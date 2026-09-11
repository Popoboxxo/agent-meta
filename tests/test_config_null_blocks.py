"""Regression tests for issue #741: explicit null config blocks.

An explicit YAML null for a top-level key (`project: null`, `knowledge-engine:
null`, ...) used to crash downstream with
``AttributeError: 'NoneType' object has no attribute 'get'`` because
``config.get("block", {})`` returned ``None`` instead of the default.

`load_config` now normalizes at load time:
- mapping blocks become ``{}`` (so every chained ``.get()`` is safe),
- scalar/array keys are dropped (their documented "null == unset" semantics,
  e.g. ``platform.resolve_preset_name`` falling through to the platform
  cascade for a null ``dod-preset``, is preserved).
"""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.config import _build_core_variables, load_config  # noqa: E402

# Top-level mapping blocks from config/project-config.schema.json (type: object)
# plus framework blocks the schema does not declare (systems-engineering, ...).
_MAPPING_BLOCKS = [
    "project",
    "variables",
    "readme",
    "auto_commit",
    "knowledge-engine",
    "systems-engineering",
    "model-override-all",
    "model-inherit-main-chat",
    "model-overrides",
    "memory",
    "memory-overrides",
    "mcp-role-overrides",
    "permission-mode-overrides",
    "temperature-overrides",
    "tier-overrides",
    "provider-tier-overrides",
    "model-source-preference",
    "max-tokens-overrides",
    "dod",
    "release-gates",
    "conventions",
    "hooks",
    "provider-options",
    "gitignore",
    "drift-detection",
    "context_file",
    "lifecycle-triggers",
    "mcp-registry",
    "plugin-catalog",
    "cascades",
    "external-skills",
    "quality-pipelines",
    "reflection-pairs",
    "admin-ui",
    "viz",
    "delegation",
    "orchestrator",
    "analysis",
]

# Scalar/array top-level keys: an explicit null means "unset", so the key is
# dropped rather than coerced to {}.
_SCALAR_KEYS = [
    "agent-meta-version",
    "ai-provider",
    "default-provider",
    "ai-providers",
    "platforms",
    "roles",
    "tier-preset",
    "se-focus",
    "dod-preset",
    "conventions-preset",
    "debug-mode",
    "max-parallel-agents",
    "speech-mode",
    "provider-isolation",
    "allow-committed-secrets",
    "mcp-servers",
]


def _load(tmp_path: Path, body: str) -> dict:
    path = tmp_path / "project.yaml"
    path.write_text(body, encoding="utf-8")
    return load_config(path)


@pytest.mark.parametrize("key", _MAPPING_BLOCKS)
def test_null_mapping_block_normalizes_to_empty_dict(tmp_path: Path, key: str) -> None:
    config = _load(tmp_path, f"{key}: null\n")
    assert config[key] == {}


@pytest.mark.parametrize("key", _SCALAR_KEYS)
def test_null_scalar_key_is_treated_as_absent(tmp_path: Path, key: str) -> None:
    config = _load(tmp_path, f"{key}: null\n")
    assert key not in config


def test_project_null_does_not_crash_core_variable_builder(tmp_path: Path) -> None:
    """The original #741 crash: project.get() on an explicit null block."""
    config = _load(tmp_path, "project: null\n")
    assert config["project"] == {}
    assert _build_core_variables({}, config, _REPO_ROOT, None) is not None


def test_all_null_blocks_load_and_build_together(tmp_path: Path) -> None:
    body = "".join(f"{key}: null\n" for key in _MAPPING_BLOCKS + _SCALAR_KEYS)
    config = _load(tmp_path, body)
    _build_core_variables({}, config, _REPO_ROOT, None)
