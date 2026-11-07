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

from lib.config import _build_core_variables, _build_orch_variables, load_config  # noqa: E402

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
    "spec-plan-workflow",
    "conventions",
    "hooks",
    "provider-options",
    "gitignore",
    "drift-detection",
    "context_file",
    "provider-overrides",
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


def test_nested_null_unknown_fallback_is_unset(tmp_path: Path) -> None:
    """SR-A-28: `orchestrator: {unknown-fallback: null}` used to raise AttributeError."""
    # Built directly: the JSON schema rejects the nested null at load time, but
    # build_variables is also reached with programmatic configs (admin UI, tests).
    config = _load(tmp_path, "orchestrator: {}\n")
    config["orchestrator"]["unknown-fallback"] = None
    variables: dict = {}
    _build_orch_variables(variables, [], config, _REPO_ROOT)
    assert variables["UNKNOWN_FALLBACK_META_FEEDBACK"] == "true"
    assert variables["UNKNOWN_FALLBACK_ASK_USER"] == "false"


# --- #1155 F4: non-mapping blocks / string booleans / unknown hook names ----


@pytest.mark.parametrize("body,key", [
    ("viz: true\n", "viz"),
    ("hooks: true\n", "hooks"),
    ("project: [a]\n", "project"),
])
def test_non_mapping_object_block_becomes_empty_with_warning(
    tmp_path: Path, capsys, body: str, key: str,
) -> None:
    config = _load(tmp_path, body)
    assert config[key] == {}
    assert key in capsys.readouterr().err


def test_non_mapping_hook_entry_becomes_empty_with_warning(tmp_path: Path, capsys) -> None:
    config = _load(tmp_path, "hooks: {dod-push-check: true}\n")
    assert config["hooks"] == {"dod-push-check": {}}
    assert "dod-push-check" in capsys.readouterr().err


def _sync_hooks(tmp_path: Path, hooks_cfg: dict, viz_cfg=None) -> tuple:
    from lib.hooks import sync_hooks
    from lib.log import SyncLog

    log = SyncLog()
    config = {"hooks": hooks_cfg}
    if viz_cfg is not None:
        config["viz"] = viz_cfg
    sync_hooks(_REPO_ROOT, tmp_path, config, log, dry_run=False)
    settings = tmp_path / ".claude" / "settings.json"
    return log, settings.read_text(encoding="utf-8") if settings.exists() else ""


def test_string_false_does_not_enable_hook(tmp_path: Path) -> None:
    _log, settings = _sync_hooks(tmp_path, {"dod-push-check": {"enabled": "false"}})
    assert "dod-push-check" not in settings


def test_string_false_viz_enabled_does_not_activate_viz_log(tmp_path: Path) -> None:
    _log, settings = _sync_hooks(tmp_path, {}, {"enabled": "false", "mode": "full"})
    assert "viz-log" not in settings


@pytest.mark.parametrize("hooks_cfg,viz_cfg,key", [
    ({"dod-push-check": {"enabled": "true"}}, None, "hooks.dod-push-check.enabled"),
    ({}, {"enabled": "true", "mode": "full"}, "viz.enabled"),
])
def test_non_bool_enabled_warns_and_disables(
    tmp_path: Path, hooks_cfg: dict, viz_cfg, key: str,
) -> None:
    log, settings = _sync_hooks(tmp_path, hooks_cfg, viz_cfg)
    assert any(key in w and "'true'" in w for w in log.warnings)
    assert "dod-push-check" not in settings and "viz-log" not in settings


# --- B1: strict validators run before the lenient non-mapping coercion -------


@pytest.mark.parametrize("body", [
    "repo_containment: 'yes'\n",
    "model-inherit-main-chat: true\n",
    "test-environments: [a]\n",
])
def test_strict_validators_still_reject_non_mapping_blocks(tmp_path: Path, body: str) -> None:
    with pytest.raises(SystemExit) as exc:
        _load(tmp_path, body)
    assert exc.value.code == 1


def test_unknown_hook_name_warns(tmp_path: Path) -> None:
    log, _settings = _sync_hooks(tmp_path, {"dod-push-chek": {"enabled": True}})
    assert any("dod-push-chek" in w for w in log.warnings)
