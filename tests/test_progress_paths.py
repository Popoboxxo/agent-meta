"""Unit tests for the configurable progress / checkpoint path resolver.

Covers AC-01..AC-06, AC-11 and AC-12 of
``SPEC-PROGRESS-PATHS-CONFIG-2026-09-13``: default resolution, full and partial
project overrides, invalid-type and traversal fallbacks (findings instead of
exceptions), best-effort config loading, provider-agnosticism and the Python
3.9 syntax floor.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.progress_paths import (  # noqa: E402
    DEFAULT_CHECKPOINT_DIR,
    DEFAULT_PROGRESS_DIR,
    SOURCE_DEFAULT,
    SOURCE_PROJECT,
    SOURCE_SAFE_FALLBACK,
    resolve_progress_paths,
)

_MODULE_PATH = REPO_ROOT / "scripts" / "lib" / "progress_paths.py"


def _provider_names():
    try:
        import yaml
    except ImportError:  # pragma: no cover - PyYAML is a runtime dependency
        return set()
    data = yaml.safe_load(
        (REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8")
    )
    return set((data.get("providers") or {}).keys())


def _annotations(tree):
    nodes = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            all_args = list(getattr(args, "posonlyargs", [])) + list(args.args) + list(args.kwonlyargs)
            if args.vararg is not None:
                all_args.append(args.vararg)
            if args.kwarg is not None:
                all_args.append(args.kwarg)
            nodes.extend(arg.annotation for arg in all_args if arg.annotation is not None)
            if node.returns is not None:
                nodes.append(node.returns)
        elif isinstance(node, ast.AnnAssign) and node.annotation is not None:
            nodes.append(node.annotation)
    return nodes


def _has_pep604_union(tree):
    return any(
        isinstance(inner, ast.BinOp) and isinstance(inner.op, ast.BitOr)
        for ann in _annotations(tree)
        for inner in ast.walk(ann)
    )


def test_default_resolution(tmp_path):
    resolved = resolve_progress_paths(tmp_path, {})

    assert resolved.progress_rel == ".meta-viz/progress"
    assert resolved.checkpoint_rel == ".meta-viz/checkpoints"
    assert resolved.progress_rel == DEFAULT_PROGRESS_DIR
    assert resolved.checkpoint_rel == DEFAULT_CHECKPOINT_DIR
    assert resolved.progress_source == SOURCE_DEFAULT
    assert resolved.checkpoint_source == SOURCE_DEFAULT
    assert resolved.progress_dir.is_absolute()
    assert resolved.checkpoint_dir.is_absolute()
    # Both absolute paths resolve under the project root.
    resolved.progress_dir.relative_to(tmp_path)
    resolved.checkpoint_dir.relative_to(tmp_path)
    assert resolved.findings == ()


def test_progress_dir_override(tmp_path):
    resolved = resolve_progress_paths(tmp_path, {"progress": {"dir": ".run/progress"}})

    assert resolved.progress_rel == ".run/progress"
    assert resolved.progress_source == SOURCE_PROJECT
    assert resolved.progress_dir == tmp_path / ".run" / "progress"
    assert resolved.checkpoint_rel == DEFAULT_CHECKPOINT_DIR
    assert resolved.checkpoint_source == SOURCE_DEFAULT
    assert resolved.findings == ()


def test_checkpoint_dir_override(tmp_path):
    resolved = resolve_progress_paths(
        tmp_path, {"progress": {"checkpoint-dir": ".run/checkpoints"}}
    )

    assert resolved.checkpoint_rel == ".run/checkpoints"
    assert resolved.checkpoint_source == SOURCE_PROJECT
    assert resolved.checkpoint_dir == tmp_path / ".run" / "checkpoints"
    assert resolved.progress_rel == DEFAULT_PROGRESS_DIR
    assert resolved.progress_source == SOURCE_DEFAULT
    assert resolved.findings == ()


def test_partial_override_is_independent(tmp_path):
    resolved = resolve_progress_paths(tmp_path, {"progress": {"dir": ".run/progress"}})

    assert resolved.progress_source == SOURCE_PROJECT
    assert resolved.checkpoint_source == SOURCE_DEFAULT


@pytest.mark.parametrize(
    "key,value,expected_code",
    [
        ("dir", 1, "progress.dir-type"),
        ("dir", [".run"], "progress.dir-type"),
        ("dir", {"path": ".run"}, "progress.dir-type"),
        ("checkpoint-dir", 1, "progress.checkpoint-dir-type"),
        ("checkpoint-dir", [".run"], "progress.checkpoint-dir-type"),
    ],
)
def test_non_string_type_falls_back_with_finding(tmp_path, key, value, expected_code):
    resolved = resolve_progress_paths(tmp_path, {"progress": {key: value}})

    if key == "dir":
        assert resolved.progress_rel == DEFAULT_PROGRESS_DIR
        assert resolved.progress_source == SOURCE_SAFE_FALLBACK
    else:
        assert resolved.checkpoint_rel == DEFAULT_CHECKPOINT_DIR
        assert resolved.checkpoint_source == SOURCE_SAFE_FALLBACK
    codes = [f.code for f in resolved.findings]
    assert codes == [expected_code]


@pytest.mark.parametrize("value", ["", "   ", "\t"])
def test_empty_or_whitespace_resolves_to_default_without_finding(tmp_path, value):
    resolved = resolve_progress_paths(tmp_path, {"progress": {"dir": value}})

    assert resolved.progress_rel == DEFAULT_PROGRESS_DIR
    assert resolved.progress_source == SOURCE_DEFAULT
    assert resolved.findings == ()


def test_progress_block_not_mapping_falls_back(tmp_path):
    resolved = resolve_progress_paths(tmp_path, {"progress": ["not", "a", "mapping"]})

    assert resolved.progress_rel == DEFAULT_PROGRESS_DIR
    assert resolved.checkpoint_rel == DEFAULT_CHECKPOINT_DIR
    assert resolved.progress_source == SOURCE_SAFE_FALLBACK
    assert resolved.checkpoint_source == SOURCE_SAFE_FALLBACK
    assert [f.code for f in resolved.findings] == ["progress.not-mapping"]


@pytest.mark.parametrize(
    "value",
    [
        "/abs/path",
        "C:/drive/path",
        ".",
        "..",
        "a/../..",
        "x/../../escape",
    ],
)
def test_traversal_values_rejected(tmp_path, value):
    resolved = resolve_progress_paths(tmp_path, {"progress": {"dir": value}})

    assert resolved.progress_rel == DEFAULT_PROGRESS_DIR
    assert resolved.progress_source == SOURCE_SAFE_FALLBACK
    assert resolved.checkpoint_source == SOURCE_DEFAULT
    codes = [f.code for f in resolved.findings]
    assert len(codes) == 1, codes
    assert codes[0] in {
        "progress.dir-traversal",
        "progress.dir-invalid",
    }, codes
    # No resolved absolute path may lie outside the project root.
    resolved.progress_dir.relative_to(tmp_path)
    resolved.checkpoint_dir.relative_to(tmp_path)


def test_config_none_best_effort_load(tmp_path):
    config_dir = tmp_path / ".meta-config"
    config_dir.mkdir(parents=True)
    (config_dir / "project.yaml").write_text(
        "progress:\n"
        "  dir: .run/progress\n"
        "  checkpoint-dir: .run/checkpoints\n",
        encoding="utf-8",
    )

    resolved = resolve_progress_paths(tmp_path)

    assert resolved.progress_rel == ".run/progress"
    assert resolved.checkpoint_rel == ".run/checkpoints"
    assert resolved.progress_source == SOURCE_PROJECT
    assert resolved.checkpoint_source == SOURCE_PROJECT
    assert resolved.findings == ()


def test_unreadable_or_non_mapping_config_never_raises(tmp_path):
    # A non-mapping caller config is treated like an absent block.
    resolved = resolve_progress_paths(tmp_path, ["not", "a", "mapping"])
    assert resolved.progress_rel == DEFAULT_PROGRESS_DIR
    assert resolved.findings == ()

    # A config file whose top level is not a mapping is caught, not raised.
    config_dir = tmp_path / ".meta-config"
    config_dir.mkdir(parents=True)
    (config_dir / "project.yaml").write_text("- a\n- b\n", encoding="utf-8")
    loaded = resolve_progress_paths(tmp_path)
    assert loaded.progress_rel == DEFAULT_PROGRESS_DIR
    assert loaded.findings == ()

    # No config file at all is equally harmless.
    other = tmp_path / "empty"
    other.mkdir()
    missing = resolve_progress_paths(other)
    assert missing.checkpoint_rel == DEFAULT_CHECKPOINT_DIR
    assert missing.findings == ()


def _provider_equality_branches(tree):
    """AST scan for ``provider == '<Name>'`` dispatch branches.

    Mirrors ``tests/test_progress_ledger_conventions.py``: only real ``Compare``
    nodes are inspected, so docstrings/comments that discuss the anti-pattern do
    not false-positive.
    """
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if not any(isinstance(op, (ast.Eq, ast.NotEq)) for op in node.ops):
            continue
        operands = [node.left, *node.comparators]
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
            offenders.append(node.lineno)
    return offenders


def test_no_provider_literals_and_py39_syntax():
    source = _MODULE_PATH.read_text(encoding="utf-8")
    assert "from __future__ import annotations" in source

    tree = ast.parse(source, filename=str(_MODULE_PATH))
    assert not _has_pep604_union(tree), "PEP-604 union annotation in progress_paths"
    assert _provider_equality_branches(tree) == [], "provider equality branch in progress_paths"

    names = _provider_names()
    if names:
        literals = sorted({
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value in names
        })
        assert literals == [], "provider literal(s) in progress_paths: {0}".format(literals)
