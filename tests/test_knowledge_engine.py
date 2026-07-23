"""Tests for scripts/lib/knowledge.py — Knowledge Engine Phase A scaffolding helpers."""
from pathlib import Path
import json

import pytest

from scripts.lib.knowledge import (
    DOMAIN_CONCEPT_TYPES,
    generate_schema,
    generate_initial_index,
    generate_initial_log,
)
from scripts.lib.delegation_table import generate_agent_delegation_table, generate_intent_routing_table

_AGENT_META_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# DOMAIN_CONCEPT_TYPES
# ---------------------------------------------------------------------------

def test_domain_concept_types_has_all_five_domains():
    assert set(DOMAIN_CONCEPT_TYPES.keys()) == {
        "research", "personal", "business", "book", "custom",
    }


def test_domain_concept_types_values_are_nonempty_lists():
    for domain, types in DOMAIN_CONCEPT_TYPES.items():
        assert isinstance(types, list)
        assert len(types) >= 1
        for t in types:
            assert isinstance(t, str)


# ---------------------------------------------------------------------------
# generate_schema() — one case per domain
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("domain", ["research", "personal", "business", "book", "custom"])
def test_generate_schema_renders_domain_and_concept_types(domain):
    rendered = generate_schema(domain, "my-bundle", _AGENT_META_ROOT)
    assert domain in rendered
    for concept_type in DOMAIN_CONCEPT_TYPES[domain]:
        assert f"- {concept_type}" in rendered
    assert "{{KNOWLEDGE_DOMAIN}}" not in rendered
    assert "{{KNOWLEDGE_CONCEPT_TYPES}}" not in rendered
    assert "my-bundle" in rendered
    assert "{{KNOWLEDGE_BUNDLE_PATH}}" not in rendered


def test_generate_schema_unknown_domain_raises_value_error():
    with pytest.raises(ValueError, match="Unknown knowledge-engine domain"):
        generate_schema("nonexistent-domain", "knowledge", _AGENT_META_ROOT)


# ---------------------------------------------------------------------------
# generate_initial_index() / generate_initial_log()
# ---------------------------------------------------------------------------

def test_generate_initial_index_has_expected_sections():
    content = generate_initial_index()
    assert "# Knowledge Index" in content
    assert "## Concepts" in content
    assert "## Entities" in content
    assert "## Topics" in content


def test_generate_initial_log_has_expected_sections():
    content = generate_initial_log()
    assert "# Knowledge Log" in content
    assert "## Format" in content
    assert "## Entries" in content


# ---------------------------------------------------------------------------
# _is_role_enabled() — knowledge- prefix branch
# ---------------------------------------------------------------------------

from scripts.lib.agents import _is_role_enabled


def test_knowledge_role_enabled_when_config_true():
    config = {"knowledge-engine": {"enabled": True}}
    assert _is_role_enabled("knowledge-curator", config) is True


def test_knowledge_role_disabled_when_config_false():
    config = {"knowledge-engine": {"enabled": False}}
    assert _is_role_enabled("knowledge-curator", config) is False


def test_knowledge_role_disabled_when_config_missing():
    assert _is_role_enabled("knowledge-curator", {}) is False


def test_knowledge_role_disabled_when_block_present_but_empty():
    assert _is_role_enabled("knowledge-curator", {"knowledge-engine": {}}) is False


def test_se_role_still_defaults_to_enabled_unaffected():
    """Regression: existing se- behavior must not change."""
    assert _is_role_enabled("se-architect", {}) is True


def test_non_prefixed_role_always_enabled():
    """Regression: roles without se-/knowledge- prefix are unaffected."""
    assert _is_role_enabled("developer", {"knowledge-engine": {"enabled": False}}) is True


# ---------------------------------------------------------------------------
# build_variables() — KNOWLEDGE_* injection
# ---------------------------------------------------------------------------

from scripts.lib.config import build_variables

_TEST_REPO_ROOT = Path(__file__).resolve().parent.parent


def _minimal_config(**overrides) -> dict:
    config = {
        "project": {"name": "test-proj", "prefix": "tp", "short": "test-proj"},
        "ai-providers": ["Claude"],
    }
    config.update(overrides)
    return config


def test_build_variables_knowledge_defaults_when_block_absent():
    variables, _ = build_variables(_minimal_config(), _AGENT_META_ROOT)
    assert variables["KNOWLEDGE_ENGINE_ENABLED"] == "false"
    assert variables["KNOWLEDGE_DOMAIN"] == "research"
    assert variables["KNOWLEDGE_BUNDLE_PATH"] == "knowledge"


def test_build_variables_knowledge_enabled_true():
    config = _minimal_config(**{
        "knowledge-engine": {"enabled": True, "domain": "personal", "bundle-path": "kb"},
    })
    variables, _ = build_variables(config, _AGENT_META_ROOT)
    assert variables["KNOWLEDGE_ENGINE_ENABLED"] == "true"
    assert variables["KNOWLEDGE_DOMAIN"] == "personal"
    assert variables["KNOWLEDGE_BUNDLE_PATH"] == "kb"


# ---------------------------------------------------------------------------
# config/project-config.schema.json — knowledge-engine property
# ---------------------------------------------------------------------------

def test_schema_has_knowledge_engine_property():
    schema_path = _AGENT_META_ROOT / "config" / "project-config.schema.json"
    with schema_path.open(encoding="utf-8") as f:
        schema = json.load(f)
    ke_schema = schema["properties"]["knowledge-engine"]
    assert ke_schema["type"] == "object"
    assert ke_schema["properties"]["enabled"]["type"] == "boolean"
    assert ke_schema["properties"]["enabled"]["default"] is False
    assert set(ke_schema["properties"]["domain"]["enum"]) == set(DOMAIN_CONCEPT_TYPES.keys())
    assert ke_schema["properties"]["bundle-path"]["type"] == "string"


def test_self_hosting_project_yaml_has_knowledge_engine_block():
    import yaml
    project_yaml_path = _AGENT_META_ROOT / ".meta-config" / "project.yaml"
    with project_yaml_path.open(encoding="utf-8") as f:
        project_config = yaml.safe_load(f)
    assert project_config["knowledge-engine"]["enabled"] is False
    assert project_config["knowledge-engine"]["domain"] in DOMAIN_CONCEPT_TYPES


def test_build_variables_knowledge_derived_paths():
    config = _minimal_config(**{
        "knowledge-engine": {"enabled": True, "domain": "research", "bundle-path": "kb"},
    })
    variables, _ = build_variables(config, _AGENT_META_ROOT)
    assert variables["KNOWLEDGE_SCHEMA_PATH"] == "kb/schema.md"
    assert variables["KNOWLEDGE_WIKI_DIR"] == "kb/wiki"
    assert variables["KNOWLEDGE_SOURCES_DIR"] == "kb/sources"


def test_build_variables_knowledge_derived_paths_default_bundle():
    variables, _ = build_variables(_minimal_config(), _AGENT_META_ROOT)
    assert variables["KNOWLEDGE_SCHEMA_PATH"] == "knowledge/schema.md"
    assert variables["KNOWLEDGE_WIKI_DIR"] == "knowledge/wiki"
    assert variables["KNOWLEDGE_SOURCES_DIR"] == "knowledge/sources"


# ---------------------------------------------------------------------------
# config/role-defaults.yaml — 7 knowledge-* roles
# ---------------------------------------------------------------------------

from scripts.lib.roles import load_roles_config


def test_role_defaults_has_seven_knowledge_roles():
    roles_cfg = load_roles_config(_AGENT_META_ROOT)
    roles = roles_cfg["roles"]
    expected = {
        "knowledge-curator", "knowledge-ingestor", "knowledge-querier",
        "knowledge-linter", "knowledge-indexer", "knowledge-gardener", "knowledge-migrator",
    }
    assert expected.issubset(roles.keys())
    for name in expected:
        assert roles[name]["group"] == "knowledge"
        assert roles[name]["workflow_tier"] == "optional"
        assert "conditional" not in roles[name]


def test_knowledge_indexer_has_no_intent_keywords():
    roles_cfg = load_roles_config(_AGENT_META_ROOT)
    routing = roles_cfg["roles"]["knowledge-indexer"]["routing"]
    assert "intent_keywords" not in routing
    assert routing["orchestrator_only"] is True


def test_knowledge_roles_pass_schema_validation():
    import subprocess
    result = subprocess.run(
        ["python", str(_AGENT_META_ROOT / "scripts" / "sync.py"), "--dry-run", "--validate"],
        cwd=_AGENT_META_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# delegation_table.py — knowledge-* gating in routing tables
# ---------------------------------------------------------------------------

def test_delegation_table_omits_knowledge_roles_when_disabled():
    variables = {"SE_ENABLED": "false", "VALIDATOR_ENABLED": "false", "KNOWLEDGE_ENGINE_ENABLED": "false"}
    table = generate_agent_delegation_table(_AGENT_META_ROOT, {}, variables)
    assert "knowledge-curator" not in table
    assert "knowledge-migrator" not in table


def test_intent_routing_table_omits_knowledge_roles_when_disabled():
    variables = {
        "SE_ENABLED": "false", "VALIDATOR_ENABLED": "false",
        "DEVELOPER_TIERS_ENABLED": "false", "EFFORT_ESTIMATOR_ENABLED": "false",
        "DOD_TESTS_REQUIRED": "false", "WEB_PROJECT_ENABLED": "false",
        "KNOWLEDGE_ENGINE_ENABLED": "false",
    }
    table = generate_intent_routing_table(_AGENT_META_ROOT, {}, variables)
    assert "knowledge-curator" not in table
    assert "knowledge-migrator" not in table


def test_delegation_table_includes_knowledge_roles_when_enabled():
    variables = {"SE_ENABLED": "false", "VALIDATOR_ENABLED": "false", "KNOWLEDGE_ENGINE_ENABLED": "true"}
    table = generate_agent_delegation_table(_AGENT_META_ROOT, {}, variables)
    for role in ["knowledge-curator", "knowledge-ingestor", "knowledge-querier",
                 "knowledge-linter", "knowledge-indexer", "knowledge-gardener", "knowledge-migrator"]:
        assert role in table


def test_intent_routing_table_includes_knowledge_roles_when_enabled():
    variables = {
        "SE_ENABLED": "false", "VALIDATOR_ENABLED": "false",
        "DEVELOPER_TIERS_ENABLED": "false", "EFFORT_ESTIMATOR_ENABLED": "false",
        "DOD_TESTS_REQUIRED": "false", "WEB_PROJECT_ENABLED": "false",
        "KNOWLEDGE_ENGINE_ENABLED": "true",
    }
    table = generate_intent_routing_table(_AGENT_META_ROOT, {}, variables)
    # knowledge-indexer has no intent_keywords -> excluded from intent routing table (routing.get() check)
    for role in ["knowledge-curator", "knowledge-ingestor", "knowledge-querier",
                 "knowledge-linter", "knowledge-gardener", "knowledge-migrator"]:
        assert f"`{role}`" in table
