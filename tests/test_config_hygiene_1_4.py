"""PR 1.4 non-destructive config hygiene.

Pins two things: (a) the self-hosted project config no longer carries dead
derived variables / dead knowledge-engine blocks / empty provider-option
placeholders; (b) removing those keys is behaviour-preserving because the
framework derives the same values from the authoritative source keys.

Run: python3 -m pytest tests/test_config_hygiene_1_4.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.config import build_variables  # noqa: E402

_PROJECT_CONFIG = _REPO_ROOT / ".meta-config" / "project.yaml"

_DERIVED_VARIABLES = (
    "ORCHESTRATOR_STRICT",
    "UNKNOWN_FALLBACK_META_FEEDBACK",
    "UNKNOWN_FALLBACK_MAIN_CHAT",
    "UNKNOWN_FALLBACK_ASK_USER",
    "SE_BASE_DIR",
)


def _config() -> dict:
    return yaml.safe_load(_PROJECT_CONFIG.read_text(encoding="utf-8"))


def test_derived_variable_duplicates_removed_from_project_config():
    variables = _config().get("variables", {})
    for key in _DERIVED_VARIABLES:
        assert key not in variables, f"dead duplicate variable still present: {key}"


def test_manual_derived_variable_cannot_override_authoritative_source():
    """Removing the duplicates is safe: the source key always wins."""
    config = {
        "variables": {"ORCHESTRATOR_STRICT": "false"},
        "orchestrator": {"strict": True},
    }
    variables, _ = build_variables(config, _REPO_ROOT, _REPO_ROOT)
    assert variables["ORCHESTRATOR_STRICT"] == "true"


def test_dead_knowledge_engine_migration_block_removed():
    assert "migration" not in _config().get("knowledge-engine", {})


def test_empty_provider_option_blocks_removed():
    options = _config().get("provider-options", {})
    assert all(isinstance(value, dict) and value for value in options.values())


def test_plugins_honcho_and_reqogniloom_disabled():
    plugins = _config().get("plugins", {})
    assert plugins["honcho"]["enabled"] is False
    assert plugins["reqogniloom"]["enabled"] is False


def test_disabled_plugins_absent_from_guardrail_render():
    """§3.8 caveat: disabling the plugins DOES change the guardrail render.

    The Rules hash therefore belongs in the H-only rebaseline of this PR.
    """
    from lib.mcp import (
        build_mcp_guardrails_list,
        load_mcp_registry,
        resolve_active_mcp_servers,
    )

    config = _config()
    registry = load_mcp_registry(_REPO_ROOT, config, _REPO_ROOT)
    active = resolve_active_mcp_servers(config, _REPO_ROOT, _REPO_ROOT, registry=registry)
    assert "honcho" not in active
    assert "reqogniloom" not in active
    rendered = build_mcp_guardrails_list(registry, active)
    assert "**honcho:**" not in rendered
    assert "**reqogniloom:**" not in rendered
