"""Tests for the external dev-tool registry (scripts/lib/external_tools.py).

Mirrors tests/test_mcp_config.py: tmp_path fixtures, a real SyncLog. Covers the
3-source registry merge, activation resolution (explicit list vs.
enabled-by-default vs. explicit enabled: false override), rule-file writing via
write_checked (content + footer), the missing-hook warning, and provider-skip.
"""

from pathlib import Path

import yaml

from scripts.lib.external_tools import (
    _tool_is_active,
    generate_external_tool_artifacts,
    load_external_tools_registry,
    resolve_active_external_tools,
)
from scripts.lib.log import SyncLog


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_framework_registry(agent_meta_root: Path, tools: dict) -> None:
    _write(
        agent_meta_root / "config" / "external-tools-registry.yaml",
        yaml.dump({"version": "1.0.0", "external-tools": tools}),
    )


# ---------------------------------------------------------------------------
# Registry loading / merge
# ---------------------------------------------------------------------------

def test_load_registry_merges_three_sources(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"

    _write_framework_registry(agent_meta_root, {
        "graphify": {
            "description": "framework desc",
            "enabled-by-default": False,
            "rule-content": "framework body",
        }
    })
    # Project-level registry file overrides the description.
    _write(
        project_root / ".meta-config" / "external-tools-registry.yaml",
        yaml.dump({"external-tools": {"graphify": {"description": "project-file desc"}}}),
    )
    # Inline project.yaml override wins over both for enabled-by-default.
    config = {"external-tools-registry": {"graphify": {"enabled-by-default": True}}}

    registry = load_external_tools_registry(agent_meta_root, config, project_root)

    assert registry["graphify"]["description"] == "project-file desc"
    assert registry["graphify"]["enabled-by-default"] is True
    # Untouched key survives the deep-merge.
    assert registry["graphify"]["rule-content"] == "framework body"


def test_load_registry_empty_when_missing(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    assert load_external_tools_registry(agent_meta_root) == {}


# ---------------------------------------------------------------------------
# _tool_is_active precedence
# ---------------------------------------------------------------------------

def test_tool_is_active_explicit_enable_wins_over_default_false():
    assert _tool_is_active(
        "graphify",
        {"enabled-by-default": False},
        {"graphify": {"enabled": True}},
    ) is True


def test_tool_is_active_explicit_disable_wins_over_default_true():
    assert _tool_is_active(
        "graphify",
        {"enabled-by-default": True},
        {"graphify": {"enabled": False}},
    ) is False


def test_tool_is_active_falls_back_to_default():
    assert _tool_is_active("graphify", {"enabled-by-default": True}, {}) is True
    assert _tool_is_active("graphify", {"enabled-by-default": False}, {}) is False


def test_tool_is_active_defaults_false_when_no_flag():
    assert _tool_is_active("graphify", {}, {}) is False


# ---------------------------------------------------------------------------
# resolve_active_external_tools
# ---------------------------------------------------------------------------

def test_resolve_explicit_flat_list_activates_default_off_tool(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    _write_framework_registry(agent_meta_root, {
        "graphify": {"enabled-by-default": False, "rule-content": "x"},
    })
    config = {"external-tools": ["graphify"]}
    assert resolve_active_external_tools(config, agent_meta_root) == ["graphify"]


def test_resolve_enabled_by_default_without_explicit_list(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    _write_framework_registry(agent_meta_root, {
        "always-on": {"enabled-by-default": True, "rule-content": "x"},
        "opt-in": {"enabled-by-default": False, "rule-content": "y"},
    })
    assert resolve_active_external_tools({}, agent_meta_root) == ["always-on"]


def test_resolve_explicit_disable_overrides_default_on(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    _write_framework_registry(agent_meta_root, {
        "always-on": {"enabled-by-default": True, "rule-content": "x"},
    })
    config = {"external-tools": {"always-on": {"enabled": False}}}
    assert resolve_active_external_tools(config, agent_meta_root) == []


def test_resolve_skips_tool_absent_from_registry(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    _write_framework_registry(agent_meta_root, {
        "graphify": {"enabled-by-default": False, "rule-content": "x"},
    })
    config = {"external-tools": ["graphify", "ghost-tool"]}
    assert resolve_active_external_tools(config, agent_meta_root) == ["graphify"]


# ---------------------------------------------------------------------------
# generate_external_tool_artifacts — rule file writing
# ---------------------------------------------------------------------------

def test_generate_writes_rule_file_with_content_and_footer(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {
        "graphify": {
            "description": "graphify desc",
            "enabled-by-default": False,
            "rule-content": "## graphify\nUse the graphify CLI.",
        },
    })
    config = {"external-tools": ["graphify"]}
    provider_config = {"Claude": {"has_rules": True}}
    log = SyncLog()

    generate_external_tool_artifacts(
        agent_meta_root, project_root, config, provider_config, log,
        dry_run=False, provider="Claude",
    )

    rule_path = project_root / ".claude" / "rules" / "tool-graphify.md"
    assert rule_path.exists()
    text = rule_path.read_text(encoding="utf-8")
    assert "# External Tool: graphify" in text
    assert "> graphify desc" in text
    assert "## graphify" in text
    assert "Use the graphify CLI." in text
    assert (
        "*Generiert von agent-meta aus `config/external-tools-registry.yaml` — "
        "nicht manuell bearbeiten.*"
    ) in text


def test_generate_is_idempotent_second_run_skips(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {
        "graphify": {"enabled-by-default": True, "rule-content": "body"},
    })
    provider_config = {"Claude": {"has_rules": True}}

    generate_external_tool_artifacts(
        agent_meta_root, project_root, {}, provider_config, SyncLog(),
        dry_run=False, provider="Claude",
    )
    log2 = SyncLog()
    generate_external_tool_artifacts(
        agent_meta_root, project_root, {}, provider_config, log2,
        dry_run=False, provider="Claude",
    )
    assert any("unchanged" in s for s in log2.skipped)


def test_generate_warns_on_missing_declared_hook(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {
        "graphify": {
            "enabled-by-default": True,
            "rule-content": "body",
            "hooks": ["graphify-search-guard"],  # no .sh file created
        },
    })
    provider_config = {"Claude": {"has_rules": True}}
    log = SyncLog()

    generate_external_tool_artifacts(
        agent_meta_root, project_root, {}, provider_config, log,
        dry_run=False, provider="Claude",
    )
    assert any("graphify-search-guard" in w and "not found" in w for w in log.warnings)


def test_generate_no_warning_when_declared_hook_present(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {
        "graphify": {
            "enabled-by-default": True,
            "rule-content": "body",
            "hooks": ["graphify-search-guard"],
        },
    })
    _write(agent_meta_root / "hooks" / "0-external" / "graphify-search-guard.sh", "#!/bin/bash\nexit 0\n")
    provider_config = {"Claude": {"has_rules": True}}
    log = SyncLog()

    generate_external_tool_artifacts(
        agent_meta_root, project_root, {}, provider_config, log,
        dry_run=False, provider="Claude",
    )
    assert not any("not found" in w for w in log.warnings)


def test_generate_provider_skip_excludes_provider(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {
        "graphify": {
            "enabled-by-default": True,
            "rule-content": "body",
            "provider-skip": ["Claude"],
        },
    })
    provider_config = {"Claude": {"has_rules": True}}
    log = SyncLog()

    generate_external_tool_artifacts(
        agent_meta_root, project_root, {}, provider_config, log,
        dry_run=False, provider="Claude",
    )
    assert not (project_root / ".claude" / "rules" / "tool-graphify.md").exists()


def test_generate_skips_rule_file_for_provider_without_rules(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {
        "graphify": {"enabled-by-default": True, "rule-content": "body"},
    })
    # has_rules: False (e.g. Opencode) — rule content is embedded elsewhere.
    provider_config = {"Opencode": {"has_rules": False}}
    log = SyncLog()

    generate_external_tool_artifacts(
        agent_meta_root, project_root, {}, provider_config, log,
        dry_run=False, provider="Opencode",
    )
    assert not (project_root / ".claude" / "rules" / "tool-graphify.md").exists()
