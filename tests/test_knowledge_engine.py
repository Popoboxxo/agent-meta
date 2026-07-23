"""Tests for scripts/lib/knowledge.py — Knowledge Engine Phase A scaffolding helpers."""
from pathlib import Path

import pytest

from scripts.lib.knowledge import (
    DOMAIN_CONCEPT_TYPES,
    generate_schema,
    generate_initial_index,
    generate_initial_log,
)

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
