"""Tests for scripts/lib/knowledge.py — Knowledge Engine Phase A scaffolding helpers."""
import json
from pathlib import Path

import pytest

from scripts.lib.delegation_table import get_active_agents_data
from scripts.lib.knowledge import (
    DOMAIN_CONCEPT_TYPES,
    generate_initial_index,
    generate_initial_log,
    generate_schema,
)

_AGENT_META_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# DOMAIN_CONCEPT_TYPES
# ---------------------------------------------------------------------------

def test_domain_concept_types_has_all_domains():
    assert set(DOMAIN_CONCEPT_TYPES.keys()) == {
        "research", "personal", "business", "book", "internal-docs", "technical", "custom",
    }


def test_domain_concept_types_values_are_nonempty_lists():
    for types in DOMAIN_CONCEPT_TYPES.values():
        assert isinstance(types, list)
        assert len(types) >= 1
        for t in types:
            assert isinstance(t, str)


# ---------------------------------------------------------------------------
# generate_schema() — one case per domain
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("domain", ["research", "personal", "business", "book", "internal-docs", "custom"])
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

from scripts.lib.frontmatter import _is_role_enabled


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
    assert project_config["knowledge-engine"]["enabled"] is True
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


def test_knowledge_indexer_has_intent_keywords():
    roles_cfg = load_roles_config(_AGENT_META_ROOT)
    routing = roles_cfg["roles"]["knowledge-indexer"]["routing"]
    assert "intent_keywords" in routing
    assert "Index aktualisieren" in routing["intent_keywords"]
    assert routing["orchestrator_only"] is True


def test_knowledge_roles_pass_schema_validation():
    import sys
    import subprocess
    result = subprocess.run(  # noqa: PLW1510
        [sys.executable, str(_AGENT_META_ROOT / "scripts" / "sync.py"), "--dry-run", "--validate"],
        cwd=_AGENT_META_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# delegation_table.py — knowledge-* gating in routing tables
# ---------------------------------------------------------------------------

def test_delegation_table_omits_knowledge_roles_when_disabled():
    variables = {"SE_ENABLED": "false", "VALIDATOR_ENABLED": "false", "KNOWLEDGE_ENGINE_ENABLED": "false"}
    table = get_active_agents_data(_AGENT_META_ROOT, {}, variables)
    assert "knowledge-curator" not in [a['name'] for a in table]
    assert "knowledge-migrator" not in [a['name'] for a in table]


def test_delegation_table_includes_knowledge_roles_when_enabled():
    variables = {"SE_ENABLED": "false", "VALIDATOR_ENABLED": "false", "KNOWLEDGE_ENGINE_ENABLED": "true"}
    table = get_active_agents_data(_AGENT_META_ROOT, {}, variables)
    for role in ["knowledge-curator", "knowledge-ingestor", "knowledge-querier",
                 "knowledge-linter", "knowledge-indexer", "knowledge-gardener", "knowledge-migrator"]:
        assert role in [a['name'] for a in table]


def test_documenter_template_has_knowledge_engine_conditional_block():
    content = (_AGENT_META_ROOT / "agents" / "1-generic" / "documenter.md").read_text(encoding="utf-8")
    assert "{{#if KNOWLEDGE_ENGINE_ENABLED}}" in content
    assert "## Knowledge Engine Dokumentation" in content
    assert "{{KNOWLEDGE_SCHEMA_PATH}}" in content
    assert "NICHT bearbeiten — gehört dem knowledge-curator" in content


def test_knowledge_curator_template_exists_and_has_required_frontmatter():
    path = _AGENT_META_ROOT / "agents" / "1-generic" / "knowledge-curator.md"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---\nname: template-knowledge-curator")
    assert "tools:" in content
    assert "- Read" in content
    assert "- Write" in content
    assert "- Agent" in content
    assert "- TodoWrite" in content
    assert "{{KNOWLEDGE_SCHEMA_PATH}}" in content
    assert "{{#if KNOWLEDGE_ENGINE_ENABLED}}" in content


def test_knowledge_ingestor_template_exists_and_documents_okf_frontmatter():
    path = _AGENT_META_ROOT / "agents" / "1-generic" / "knowledge-ingestor.md"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---\nname: template-knowledge-ingestor")
    assert "type: <Entity|Concept|Topic|Source Summary" in content
    assert "10-15 Dateien" in content
    assert "knowledge-indexer" in content


def test_knowledge_querier_template_exists_and_forbids_rewriting_pages():
    path = _AGENT_META_ROOT / "agents" / "1-generic" / "knowledge-querier.md"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---\nname: template-knowledge-querier")
    assert "Index-First" in content
    assert "schreibt KEINE bestehenden Wiki-Seiten um" in content or "KEINE bestehenden Wiki-Seiten" in content


def test_knowledge_linter_template_exists_and_has_ten_checks():
    path = _AGENT_META_ROOT / "agents" / "1-generic" / "knowledge-linter.md"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---\nname: template-knowledge-linter")
    for check in [
        "Widersprüche", "Veraltete Claims", "Orphan-Seiten", "Fehlende Concepts",
        "Kaputte Cross-References", "Datenlücken", "Fehlendes `type`-Frontmatter",
        "Fehlende recommended Frontmatter", "veraltet", "Inkonsistenzen",
    ]:
        assert check in content, f"missing check reference: {check}"


def test_knowledge_indexer_template_exists_and_documents_log_format():
    path = _AGENT_META_ROOT / "agents" / "1-generic" / "knowledge-indexer.md"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---\nname: template-knowledge-indexer")
    assert "## \\[YYYY-MM-DD\\]" in content or "## [YYYY-MM-DD]" in content
    assert "Append-only" in content


def test_knowledge_gardener_template_exists_and_forbids_content_changes():
    path = _AGENT_META_ROOT / "agents" / "1-generic" / "knowledge-gardener.md"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---\nname: template-knowledge-gardener")
    assert "KEINE inhaltliche Substanz" in content or "keine inhaltliche Substanz" in content
    assert "Tag-Harmonisierung" in content


def test_knowledge_migrator_template_exists_and_has_hard_constraints():
    path = _AGENT_META_ROOT / "agents" / "1-generic" / "knowledge-migrator.md"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---\nname: template-knowledge-migrator")
    for protected in [
        "docs/CODEBASE_OVERVIEW.md", "docs/REQUIREMENTS.md",
        "CLAUDE.md", "AGENTS.md", ".claude/", ".gemini/", ".opencode/",
        "VERSION", "LICENSE", "CHANGELOG.md",
    ]:
        assert protected in content, f"missing protected-file reference: {protected}"
    assert "NIEMALS migrieren" in content or "NIEMALS anfassen" in content
    assert "kopiert immer, verschiebt nie" in content or "KOPIERE (nicht verschiebe" in content
    assert "expliziten Freigabe" in content or "expliziter Freigabe" in content or "User-Freigabe" in content


# ---------------------------------------------------------------------------
# Full self-hosting integration — sync.py end-to-end with knowledge-engine on
# ---------------------------------------------------------------------------

def test_schema_knowledge_engine_has_phase_c_properties():
    import json
    from pathlib import Path
    schema_path = Path(__file__).parent.parent / "config" / "project-config.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    ke_props = schema["properties"]["knowledge-engine"]["properties"]
    for field in ("sources-dir", "wiki-dir", "schema-language", "okf", "operations", "migration", "search"):
        assert field in ke_props, f"missing knowledge-engine.{field}"
    assert ke_props["okf"]["additionalProperties"] is False
    assert ke_props["operations"]["additionalProperties"] is False
    assert ke_props["operations"]["properties"]["ingest"]["additionalProperties"] is False
    assert ke_props["operations"]["properties"]["query"]["additionalProperties"] is False
    assert ke_props["operations"]["properties"]["lint"]["additionalProperties"] is False
    assert ke_props["migration"]["additionalProperties"] is False
    assert ke_props["migration"]["properties"]["preserve-originals"]["default"] is True
    assert ke_props["migration"]["properties"]["auto-detect-sources"]["default"] is False
    assert ke_props["migration"]["properties"]["clean-duplicates"]["default"] is False
    assert ke_props["search"]["additionalProperties"] is False


def test_self_hosting_sync_with_knowledge_engine_enabled(tmp_path):
    import shutil
    import subprocess

    import yaml

    # Copy the whole repo into a temp dir so we don't mutate the real working tree.
    dest = tmp_path / "agent-meta-copy"
    shutil.copytree(
        _AGENT_META_ROOT, dest,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".superpowers", "external"),
    )

    project_yaml_path = dest / ".meta-config" / "project.yaml"
    with project_yaml_path.open(encoding="utf-8") as f:
        project_config = yaml.safe_load(f)
    project_config["knowledge-engine"]["enabled"] = True
    with project_yaml_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(project_config, f, allow_unicode=True, sort_keys=False)

    # No importable top-level entry point exists in scripts/sync.py (main() reads
    # sys.argv via argparse) — run the real CLI as a subprocess, per the fallback
    # described in the task brief.
    import sys
    result = subprocess.run(  # noqa: PLW1510
        [sys.executable, str(dest / "scripts" / "sync.py")],
        cwd=dest, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    claude_md = (dest / "CLAUDE.md").read_text(encoding="utf-8")
    assert "## Knowledge Engine" in claude_md
    for role in ["knowledge-curator", "knowledge-ingestor", "knowledge-querier",
                 "knowledge-linter", "knowledge-gardener", "knowledge-migrator"]:
        assert f"`{role}`" in claude_md

    for role in ["knowledge-curator", "knowledge-ingestor", "knowledge-querier",
                 "knowledge-linter", "knowledge-indexer", "knowledge-gardener", "knowledge-migrator"]:
        assert (dest / ".claude" / "agents" / f"{role}.md").exists(), f"{role} not generated"


# ---------------------------------------------------------------------------
# admin-server.py — allowed section set includes knowledge-engine
# ---------------------------------------------------------------------------

def test_admin_server_allows_knowledge_engine_section_write():
    import ast
    from pathlib import Path
    source = Path(__file__).parent.parent / "scripts" / "admin-server.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_write_project_section":
            found = "knowledge-engine" in ast.dump(node)
            break
    assert found, "'knowledge-engine' not found in _write_project_section's allowed set"


# ---------------------------------------------------------------------------
# admin-ui.html — routing for /project/knowledge-engine
# ---------------------------------------------------------------------------

def test_admin_ui_has_knowledge_engine_route():
    from pathlib import Path
    html = (Path(__file__).parent.parent / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")
    assert '{ route: "/project/knowledge-engine", label: "Knowledge Engine", icon: "🧠" }' in html
    assert 'router.register("/project/knowledge-engine", viewProjectKnowledgeEngine);' in html


# ---------------------------------------------------------------------------
# admin-ui.html — viewProjectKnowledgeEngine() view function (Task 4)
# ---------------------------------------------------------------------------

def test_admin_ui_has_view_project_knowledge_engine_function():
    from pathlib import Path
    html = (Path(__file__).parent.parent / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")
    assert "async function viewProjectKnowledgeEngine()" in html
    assert 'const PRESETS = {' in html
    for preset_name in ("research", "personal", "business", "book", "internal-docs", "custom"):
        assert f'{preset_name}: {{' in html or f'"{preset_name}": {{' in html
    assert 'saveProjectSection("knowledge-engine", ke, status)' in html
    assert '"project/knowledge-engine": "project_instance-knowledge_engine",' in html
