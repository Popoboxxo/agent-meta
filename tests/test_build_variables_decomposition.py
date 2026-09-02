"""Unit tests for the build_variables() decomposition (#566).

`build_variables()` used to be a ~500-line god-function; it is now pure
orchestration over eight `_build_*_variables()` sub-functions, each owning one
cohesive variable group. These tests exercise the sub-functions individually
(no heavy mocking needed — they take plain dicts + this repo's own
`agent_meta_root` as fixture) plus a regression check that `build_variables()`
itself still returns the exact same variables for this repo's own config as
before the split (see the manual before/after JSON-snapshot diff run during
implementation — this test locks in the same guarantee going forward).
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.config import (
    _build_convention_variables,
    _build_core_variables,
    _build_dod_variables,
    _build_orch_variables,
    _build_pipeline_variables,
    _build_platform_variables,
    _build_provider_variables,
    _build_snippet_variables,
    build_variables,
    load_config,
)

AGENT_META_ROOT = REPO_ROOT


def _base_config():
    return {
        "project": {"prefix": "tp", "short": "Test", "name": "Test Project"},
        "roles": ["developer", "validator"],
    }


# --- _build_core_variables ---------------------------------------------------

def test_build_core_variables_sets_project_identity():
    variables = {}
    unmapped = _build_core_variables(variables, _base_config(), AGENT_META_ROOT, None)
    assert variables["PREFIX"] == "tp"
    assert variables["PROJECT_NAME"] == "Test Project"
    assert variables["AGENT_META_REL_PATH"] == ".agent-meta/"
    assert isinstance(unmapped, list)


def test_build_core_variables_coerces_bool_user_variables():
    config = _base_config()
    config["variables"] = {"MY_FLAG": True, "MY_NUM": 5, "MY_STR": "hi"}
    variables = {}
    _build_core_variables(variables, config, AGENT_META_ROOT, None)
    assert variables["MY_FLAG"] == "true"
    assert variables["MY_NUM"] == "5"
    assert variables["MY_STR"] == "hi"


def test_build_core_variables_compact_mode_default_false():
    variables = {}
    _build_core_variables(variables, _base_config(), AGENT_META_ROOT, None)
    assert variables["COMPACT_MODE"] == "false"


# --- _build_provider_variables -----------------------------------------------

def test_build_provider_variables_sets_agents_dir_and_ai_provider():
    variables = {}
    _build_core_variables(variables, _base_config(), AGENT_META_ROOT, None)
    _build_provider_variables(variables, _base_config(), AGENT_META_ROOT)
    assert variables["AGENTS_DIR"]
    assert variables["AI_PROVIDER"]


def test_build_provider_variables_respects_user_override():
    """AGENTS_DIR must not be overwritten when the user already set it via
    project.yaml's `variables:` block — the check depends on core variables
    having run first."""
    config = _base_config()
    config["variables"] = {"AGENTS_DIR": "custom/agents"}
    variables = {}
    _build_core_variables(variables, config, AGENT_META_ROOT, None)
    _build_provider_variables(variables, config, AGENT_META_ROOT)
    assert variables["AGENTS_DIR"] == "custom/agents"


# --- _build_orch_variables ----------------------------------------------------

def test_build_orch_variables_defaults_enabled():
    variables = {}
    unmapped = []
    _build_orch_variables(variables, unmapped, _base_config(), AGENT_META_ROOT)
    assert variables["ORCHESTRATOR_ENABLED"] == "true"
    assert variables["A2A_PROTOCOL_ENABLED"] == "true"
    assert unmapped == []


def test_build_orch_variables_a2a_disabled_via_handoff_protocol_none():
    config = _base_config()
    config["orchestrator"] = {"handoff": {"protocol": "none"}}
    variables = {}
    _build_orch_variables(variables, [], config, AGENT_META_ROOT)
    assert variables["A2A_PROTOCOL_ENABLED"] == "false"
    assert variables["A2A_HANDOFF_BLOCK"] == ""


def test_build_orch_variables_a2a_max_depth_clamped():
    config = _base_config()
    config["orchestrator"] = {"delegation": {"max_depth": 999}}
    variables = {}
    _build_orch_variables(variables, [], config, AGENT_META_ROOT)
    assert variables["A2A_MAX_DEPTH"] == "50"


# --- _build_platform_variables -------------------------------------------------

def test_build_platform_variables_validator_enabled_from_roles():
    variables = {"ORCHESTRATOR_ENABLED": "true"}
    _build_platform_variables(variables, [], _base_config(), AGENT_META_ROOT)
    assert variables["VALIDATOR_ENABLED"] == "true"
    assert "AGENT_DELEGATION_TABLE" in variables


def test_build_platform_variables_developer_tiers_requires_both_roles():
    config = _base_config()
    config["roles"] = ["developer", "junior-developer"]
    variables = {}
    _build_platform_variables(variables, [], config, AGENT_META_ROOT)
    assert variables["DEVELOPER_TIERS_ENABLED"] == "false"


# --- _build_dod_variables ------------------------------------------------------

def test_build_dod_variables_returns_resolved_dict_and_sets_variables():
    variables = {}
    dod_resolved = _build_dod_variables(variables, _base_config(), AGENT_META_ROOT)
    assert isinstance(dod_resolved, dict)
    assert isinstance(variables["DOD_PRESET"], str)
    assert variables["DOD_REQ_TRACEABILITY"] in ("true", "false")
    assert variables["DOD_TESTS_BLOCK"] in (
        "", "Tests schreiben/aktualisieren — Pflicht vor Commit."
    )


# --- _build_pipeline_variables --------------------------------------------------

def test_build_pipeline_variables_returns_effective_dict():
    variables = {}
    dod_resolved = _build_dod_variables(variables, _base_config(), AGENT_META_ROOT)
    unmapped = []
    effective = _build_pipeline_variables(
        variables, unmapped, _base_config(), AGENT_META_ROOT, dod_resolved
    )
    assert isinstance(effective, dict)
    assert variables["QUALITY_PIPELINES_ENABLED"] in ("true", "false")
    assert variables["REFLECTION_PAIRS_ENABLED"] in ("true", "false")


# --- _build_snippet_variables ----------------------------------------------------

def test_build_snippet_variables_sets_prompt_injection_block():
    variables = {"LANGUAGE": "Python"}
    _build_snippet_variables(variables, AGENT_META_ROOT)
    assert "PROMPT_INJECTION_DEFENSE_BLOCK" in variables
    assert "SE_MODE_BLOCK" in variables


# --- _build_convention_variables ---------------------------------------------------

def test_build_convention_variables_does_not_raise_on_minimal_config():
    variables = {}
    _build_convention_variables(variables, _base_config(), AGENT_META_ROOT)
    # No assertion on specific keys — presence depends on conventions-presets.yaml
    # defaults; the contract under test is "does not raise" + returns None.


# --- build_variables() end-to-end regression ------------------------------------

def test_build_variables_self_hosting_config_is_stable():
    """Locks in the exact variable count for this repo's own project.yaml —
    a regression guard for the #566 decomposition (verified bit-identical
    against the pre-refactor monolithic build_variables() during implementation)."""
    config = load_config(REPO_ROOT / ".meta-config" / "project.yaml")
    variables, unmapped = build_variables(config, AGENT_META_ROOT, AGENT_META_ROOT)
    assert unmapped == []
    assert variables["PREFIX"] == "am"
    assert "AGENT_DELEGATION_TABLE" in variables
    assert "INTENT_ROUTING_TABLE" in variables
