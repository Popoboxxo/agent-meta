"""AC-29 / AC-30 conventions ratchet for the progress/ledger modules.

This guard binds two cross-cutting conventions of the progress/ledger system to
the *real* modules (not to a fixture), so a regression turns the suite red:

* **AC-29 (Python 3.9 portability):** every new or changed progress/ledger
  module parses under the Python 3.9 grammar (``ast.parse(..., feature_version=
  (3, 9))``). Every new module additionally declares
  ``from __future__ import annotations`` (postponed evaluation) and contains no
  PEP-604 union annotation (``X | Y``) -- that syntax is 3.10+ at runtime even
  though the 3.9 grammar accepts the expression.
* **AC-30 (provider agnosticism):** the new/changed modules contain no
  ``provider == "<Name>"`` dispatch branch and the new modules contain no
  provider-name literal. The detector mirrors
  ``tests/test_provider_agnostic_dispatch.py``: an AST scan of ``Compare``
  nodes (``Eq``/``NotEq``) so comments and docstrings -- which may legitimately
  discuss the anti-pattern -- never false-positive.

Stdlib only (plus PyYAML, already a runtime dependency).
"""
from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path
from typing import List, Set, Tuple

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_ROOT = _REPO_ROOT / "scripts"
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))

# Modules created by the progress/ledger work (spec "Neue Dateien").
_NEW_MODULES: Tuple[str, ...] = (
    "plan_identity",
    "recovery",
    "rehydrate",
    "plan_ledger",
    "checkpoint_record",
    "plan_closeout",
    "consistency/ledger_drift",
)

# Existing modules touched by the progress/ledger wiring (spec "Geänderte Dateien").
_CHANGED_MODULES: Tuple[str, ...] = (
    "checkpoint",
    "orchestration",
    "consistency/spec_plan",
    "pipelines",
    "dod",
    "rules",
    "sync",
)

_ALL_MODULES: Tuple[str, ...] = _NEW_MODULES + _CHANGED_MODULES

_PY39 = (3, 9)


def _module_path(module: str) -> Path:
    """Resolve a module name to its source file (``sync`` lives one level up)."""
    if module == "sync":
        return _SCRIPTS_ROOT / "sync.py"
    return _SCRIPTS_ROOT / "lib" / f"{module}.py"


def _source(module: str) -> str:
    return _module_path(module).read_text(encoding="utf-8")


def _provider_names() -> Set[str]:
    """Registered provider names from ``config/ai-providers.yaml``."""
    data = yaml.safe_load((_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))
    return set((data.get("providers") or {}).keys())


def _has_future_annotations(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            if any(alias.name == "annotations" for alias in node.names):
                return True
    return False


def _annotation_expressions(tree: ast.AST) -> List[ast.expr]:
    """Every annotation expression in ``tree`` (functions + ``AnnAssign``)."""
    annotations: List[ast.expr] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            all_args = list(getattr(args, "posonlyargs", [])) + list(args.args) + list(args.kwonlyargs)
            if args.vararg is not None:
                all_args.append(args.vararg)
            if args.kwarg is not None:
                all_args.append(args.kwarg)
            annotations.extend(arg.annotation for arg in all_args if arg.annotation is not None)
            if node.returns is not None:
                annotations.append(node.returns)
        elif isinstance(node, ast.AnnAssign) and node.annotation is not None:
            annotations.append(node.annotation)
    return annotations


def _is_pep604_union(node: ast.expr) -> bool:
    """True when the annotation contains a ``X | Y`` (``ast.BitOr``) expression."""
    return any(
        isinstance(inner, ast.BinOp) and isinstance(inner.op, ast.BitOr)
        for inner in ast.walk(node)
    )


def _pep604_offenders_in(source: str, label: str) -> List[str]:
    tree = ast.parse(source, filename=label)
    return [
        "{0}:{1}: {2}".format(label, node.lineno, ast.unparse(node))
        for node in _annotation_expressions(tree)
        if _is_pep604_union(node)
    ]


def _provider_equality_offenders_in(source: str, names: Set[str], label: str) -> List[str]:
    """AST scan for provider dispatch branches (mirrors the existing guard)."""
    tree = ast.parse(source, filename=label)
    offenders: List[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if not any(isinstance(op, (ast.Eq, ast.NotEq)) for op in node.ops):
            continue
        operands = [node.left, *node.comparators]
        literals = sorted({
            operand.value
            for operand in operands
            if isinstance(operand, ast.Constant)
            and isinstance(operand.value, str)
            and operand.value in names
        })
        if literals:
            offenders.append(
                "{0}:{1}: provider-name literal comparison {2!r}".format(label, node.lineno, literals)
            )
        provider_operand = any(
            (isinstance(operand, ast.Name) and "provider" in operand.id.lower())
            or (isinstance(operand, ast.Attribute) and "provider" in operand.attr.lower())
            for operand in operands
        )
        string_operand = any(
            isinstance(operand, ast.Constant) and isinstance(operand.value, str)
            for operand in operands
        )
        if provider_operand and string_operand:
            offenders.append(
                "{0}:{1}: `provider == '<str>'` dispatch branch".format(label, node.lineno)
            )
    return offenders


def _provider_literal_offenders_in(source: str, names: Set[str], label: str) -> List[str]:
    """String constants that are exactly a registered provider name in code."""
    tree = ast.parse(source, filename=label)
    return [
        "{0}:{1}: provider literal {2!r}".format(label, node.lineno, node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value in names
    ]


# ---------------------------------------------------------------------------
# AC-29 / AC-30 canonical guards (require the two node ids from the plan)
# ---------------------------------------------------------------------------


def test_new_modules_import_and_no_pep604():
    """Parse all modules under 3.9, import the new ones, forbid PEP-604."""
    syntax_offenders: List[str] = []
    for module in _ALL_MODULES:
        label = str(_module_path(module))
        try:
            ast.parse(_source(module), filename=label, feature_version=_PY39)
        except SyntaxError as exc:
            syntax_offenders.append("{0}:{1}: {2}".format(module, exc.lineno, exc.msg))
    assert not syntax_offenders, (
        "progress/ledger module is not parseable under the Python 3.9 grammar:\n"
        + "\n".join(syntax_offenders)
    )

    import_offenders: List[str] = []
    for module in _NEW_MODULES:
        try:
            importlib.import_module("lib." + module.replace("/", "."))
        except Exception as exc:  # pragma: no cover - failure path only
            import_offenders.append("{0}: {1}: {2}".format(module, type(exc).__name__, exc))
    assert not import_offenders, "new progress/ledger module failed to import:\n" + "\n".join(import_offenders)

    future_offenders = [
        module
        for module in _NEW_MODULES
        if not _has_future_annotations(ast.parse(_source(module), filename=str(_module_path(module))))
    ]
    assert not future_offenders, (
        "new module must use postponed evaluation (`from __future__ import annotations`):\n"
        + "\n".join(future_offenders)
    )

    pep604_offenders: List[str] = []
    for module in _NEW_MODULES:
        pep604_offenders.extend(_pep604_offenders_in(_source(module), str(_module_path(module))))
    assert not pep604_offenders, (
        "PEP-604 (`X | Y`) annotation in a module that must import under Python 3.9:\n"
        + "\n".join(pep604_offenders)
    )


def test_no_provider_literals_in_new_modules():
    """No provider literal and no provider equality branch in the new modules."""
    names = _provider_names()
    offenders: List[str] = []
    for module in _NEW_MODULES:
        label = str(_module_path(module))
        source = _source(module)
        offenders.extend(_provider_equality_offenders_in(source, names, label))
        offenders.extend(_provider_literal_offenders_in(source, names, label))
    assert not offenders, (
        "provider-specific dispatch/literal reintroduced -- express provider "
        "differences through capability flags / config keys instead:\n" + "\n".join(offenders)
    )


def test_no_provider_equality_dispatch_in_changed_modules():
    """The changed modules must not contain a ``provider == "<Name>"`` branch."""
    names = _provider_names()
    offenders: List[str] = []
    for module in _CHANGED_MODULES:
        offenders.extend(
            _provider_equality_offenders_in(_source(module), names, str(_module_path(module)))
        )
    assert not offenders, (
        "literal provider-name equality branch in a changed progress/ledger module:\n"
        + "\n".join(offenders)
    )


# ---------------------------------------------------------------------------
# Granular, per-module variants (better failure locality)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module", _ALL_MODULES)
def test_module_parses_under_python39(module):
    ast.parse(_source(module), filename=str(_module_path(module)), feature_version=_PY39)


@pytest.mark.parametrize("module", _NEW_MODULES)
def test_new_module_declares_future_annotations(module):
    tree = ast.parse(_source(module), filename=str(_module_path(module)))
    assert _has_future_annotations(tree), (
        "{0} must declare `from __future__ import annotations`".format(module)
    )


@pytest.mark.parametrize("module", _NEW_MODULES)
def test_new_module_has_no_pep604_union(module):
    offenders = _pep604_offenders_in(_source(module), str(_module_path(module)))
    assert not offenders, "\n".join(offenders)


@pytest.mark.parametrize("module", _NEW_MODULES)
def test_new_module_has_no_provider_equality_branch(module):
    offenders = _provider_equality_offenders_in(
        _source(module), _provider_names(), str(_module_path(module))
    )
    assert not offenders, "\n".join(offenders)


# ---------------------------------------------------------------------------
# Self-check: the guard must actually go red on a violation
# ---------------------------------------------------------------------------


def test_detector_flags_synthetic_violations():
    pep604_source = "def f(x: int | None) -> str | None:\n    return None\n"
    assert _pep604_offenders_in(pep604_source, "<pep604>"), (
        "PEP-604 detector must flag `int | None`"
    )

    provider_source = 'def f(provider):\n    if provider == "Claude":\n        return 1\n'
    assert _provider_equality_offenders_in(provider_source, {"Claude"}, "<provider>"), (
        "provider detector must flag `provider == 'Claude'`"
    )

    literal_source = 'NAME = "Opencode"\n'
    assert _provider_literal_offenders_in(literal_source, {"Opencode"}, "<literal>"), (
        "provider literal detector must flag a bare provider-name string"
    )

    clean_source = "from __future__ import annotations\n\ndef f(x: int) -> int:\n    return x\n"
    assert not _provider_equality_offenders_in(clean_source, {"Claude"}, "<clean>")
    assert not _pep604_offenders_in(clean_source, "<clean>")
