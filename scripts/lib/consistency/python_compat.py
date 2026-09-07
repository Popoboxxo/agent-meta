"""Consistency checks: Python-3.9-floor syntax hazards (CI matrix: 3.9/3.11/3.12).

Two independent hazard classes, both bitten agent-meta repeatedly because
new code is written and tested locally on a much newer interpreter (3.12+),
where neither hazard is visible, and only fails in CI's older matrix jobs:

1. PEP 604 ``X | Y`` union syntax in an annotation without
   ``from __future__ import annotations`` -- Python 3.9 evaluates
   annotations at import time, and the ``|`` union operator only works
   without that import on 3.10+. Hit ``scripts/lib/`` twice in one
   campaign (#628, #637); closed for ``scripts/lib/`` in #646, and hit
   ``tests/`` on top of that (issue #674 roadmap review) -- this module
   now scans both trees.
2. A literal backslash inside an f-string's ``{...}`` expression part
   (e.g. ``f"{r'C:\\x'}"``) -- PEP 701 (Python 3.12) relaxed the f-string
   grammar to allow this; 3.9 and 3.11 still raise a SyntaxError at parse
   time, which fails pytest at collection (whole matrix job red) rather
   than at a single test. The interpreter running THIS check may itself
   be 3.12+ (where the pattern parses fine), so detection can't rely on
   ``ast.parse`` raising -- it inspects each f-string expression's
   original source text via ``ast.get_source_segment`` instead.
"""

from __future__ import annotations

import ast
from pathlib import Path

from .report import Finding, Severity

# Both hazards apply everywhere the CI matrix actually runs pytest against
# Python 3.9: scripts/lib (the framework) and tests/ (its test suite).
# vendored submodules (external/) are excluded -- foreign code, foreign floor.
_SCAN_DIRS = (("scripts", "lib"), ("tests",))


def _iter_py_files(root: Path):
    for parts in _SCAN_DIRS:
        scan_dir = root.joinpath(*parts)
        if not scan_dir.is_dir():
            continue
        for path in sorted(scan_dir.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            yield path


def check_py39_union_syntax(root: Path) -> list[Finding]:
    """Flag modules using ``X | Y`` annotations without the future import.

    AST-based (stdlib ``ast``, no new dependency): collects every annotation
    node (function args, return type, variable annotations) and looks for an
    ``ast.BinOp`` with ``ast.BitOr`` inside it -- that is PEP 604 union
    syntax. Plain runtime ``|`` usage (e.g. dict-merge, bitwise-or in normal
    expressions) is untouched since only annotation subtrees are walked.
    """
    findings: list[Finding] = []
    for path in _iter_py_files(root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError):
            continue

        if not _has_union_annotation(tree) or _has_future_annotations_import(tree):
            continue

        findings.append(Finding(
            Severity.ERROR,
            "python.py39-union-syntax",
            str(path.relative_to(root)),
            "Uses `X | Y` union syntax in an annotation without "
            "`from __future__ import annotations` -- breaks on Python 3.9 "
            "(PEP 604 union operator needs 3.10+ at runtime).",
            "Add `from __future__ import annotations` as the first statement "
            "(after the module docstring, if any).",
        ))
    return findings


def check_fstring_backslash_hazard(root: Path) -> list[Finding]:
    """Flag f-strings with a literal backslash inside a ``{...}`` expression.

    Python < 3.12 raises ``SyntaxError: f-string expression part cannot
    include a backslash`` for this -- even for a backslash buried inside a
    nested raw-string literal (``f"{r'C:\\x'}"``). Detection walks every
    ``ast.JoinedStr``/``ast.FormattedValue`` pair and checks the ORIGINAL
    source text of each expression (via ``ast.get_source_segment``) for a
    backslash, since the AST itself parses fine under a 3.12+ interpreter
    regardless of the target floor.
    """
    findings: list[Finding] = []
    for path in _iter_py_files(root):
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            # On Python < 3.12 this exact hazard IS a SyntaxError -- the
            # interpreter running this check may itself be pre-3.12 (CI's
            # 3.9/3.11 matrix jobs), in which case ast.parse() never
            # produces a tree to inspect at all. CPython's message for
            # this specific case ("f-string expression part cannot
            # include a backslash") is stable across 3.9-3.11; treat a
            # match as a direct hit instead of silently skipping the file
            # (any other SyntaxError is out of this check's scope).
            if exc.msg and "backslash" in exc.msg and "f-string" in exc.msg:
                findings.append(Finding(
                    Severity.ERROR,
                    "python.fstring-backslash-expr",
                    str(path.relative_to(root)),
                    f"f-string expression at line {exc.lineno} contains a "
                    "backslash -- SyntaxError on Python < 3.12 (PEP 701 "
                    "relaxed this in 3.12; CI's 3.9/3.11 matrix jobs fail "
                    "at collection, not just one test).",
                    "Assign the backslash-containing value to a variable "
                    "first, then reference the variable in the f-string "
                    "(e.g. `x = r'C:\\\\x'; f'{x}'`).",
                ))
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.JoinedStr):
                continue
            for value in node.values:
                if not isinstance(value, ast.FormattedValue):
                    continue
                segment = ast.get_source_segment(source, value.value)
                if segment and "\\" in segment:
                    findings.append(Finding(
                        Severity.ERROR,
                        "python.fstring-backslash-expr",
                        str(path.relative_to(root)),
                        f"f-string expression at line {value.lineno} contains "
                        "a backslash -- SyntaxError on Python < 3.12 (PEP 701 "
                        "relaxed this in 3.12; CI's 3.9/3.11 matrix jobs fail "
                        "at collection, not just one test).",
                        "Assign the backslash-containing value to a variable "
                        "first, then reference the variable in the f-string "
                        "(e.g. `x = r'C:\\\\x'; f'{x}'`).",
                    ))
    return findings


def _has_future_annotations_import(tree: ast.Module) -> bool:
    """Mirror Python's own rule: the future-import must directly follow the docstring."""
    body = tree.body
    idx = 1 if _is_docstring(body[0] if body else None) else 0
    if idx >= len(body):
        return False
    node = body[idx]
    return (
        isinstance(node, ast.ImportFrom)
        and node.module == "__future__"
        and any(alias.name == "annotations" for alias in node.names)
    )


def _is_docstring(node: ast.stmt | None) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _has_union_annotation(tree: ast.Module) -> bool:
    annotations: list[ast.expr] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns is not None:
                annotations.append(node.returns)
            args = node.args
            for a in (*args.posonlyargs, *args.args, *args.kwonlyargs):
                if a.annotation is not None:
                    annotations.append(a.annotation)
            for extra in (args.vararg, args.kwarg):
                if extra is not None and extra.annotation is not None:
                    annotations.append(extra.annotation)
        elif isinstance(node, ast.AnnAssign) and node.annotation is not None:
            annotations.append(node.annotation)

    return any(
        isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.BitOr)
        for ann in annotations
        for sub in ast.walk(ann)
    )
