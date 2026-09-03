"""Consistency check: PEP 604 ``X | Y`` union syntax vs. Python 3.9 support.

Python 3.9 (the floor per ``pyproject.toml``/CI matrix) evaluates annotations
at import time unless ``from __future__ import annotations`` is present --
``X | Y`` union syntax (PEP 604) only works without that import on Python
3.10+. This bug class hit ``scripts/lib/`` twice in one campaign (#628, #637):
a new module was written and tested locally on Python 3.13, where the
missing future-import goes unnoticed, and only failed in CI's 3.9 matrix
job. This check closes that gap preventively (#646).
"""

from __future__ import annotations

import ast
from pathlib import Path

from .report import Finding, Severity


def check_py39_union_syntax(root: Path) -> list[Finding]:
    """Flag ``scripts/lib/*.py`` modules using ``X | Y`` annotations without the future import.

    AST-based (stdlib ``ast``, no new dependency): collects every annotation
    node (function args, return type, variable annotations) and looks for an
    ``ast.BinOp`` with ``ast.BitOr`` inside it -- that is PEP 604 union
    syntax. Plain runtime ``|`` usage (e.g. dict-merge, bitwise-or in normal
    expressions) is untouched since only annotation subtrees are walked.
    """
    findings: list[Finding] = []
    lib_dir = root / "scripts" / "lib"
    if not lib_dir.is_dir():
        return findings

    for path in sorted(lib_dir.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
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
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
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
