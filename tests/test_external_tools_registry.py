"""Tests for the external dev-tool registry (scripts/lib/external_tools.py).

Mirrors tests/test_mcp_config.py: tmp_path fixtures, a real SyncLog. Covers the
3-source registry merge, activation resolution (explicit list vs.
enabled-by-default vs. explicit enabled: false override), rule-file writing via
write_checked (content + footer), the missing-hook warning, and provider-skip.
"""

from pathlib import Path

import pytest
import yaml

from scripts.lib.external_tools import (
    _tool_is_active,
    generate_external_tool_artifacts,
    load_external_tools_registry,
    resolve_active_external_tools,
    resolve_injection_path,
)
from scripts.lib.io import SyncError
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


# ---------------------------------------------------------------------------
# permitted-injections validation
# ---------------------------------------------------------------------------

def test_permitted_injections_skill_requires_name(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {
        "graphify": {
            "description": "d",
            "permitted-injections": [{"kind": "skill", "path": ".claude/skills/graphify"}],
        }
    })
    with pytest.raises(SyncError, match="requires 'name'"):
        load_external_tools_registry(agent_meta_root, {}, project_root)


def test_permitted_injections_config_requires_path(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {
        "graphify": {
            "description": "d",
            "permitted-injections": [{"kind": "config", "name": "graphify"}],
        }
    })
    with pytest.raises(SyncError, match="requires 'path'"):
        load_external_tools_registry(agent_meta_root, {}, project_root)


def test_permitted_injections_valid_entry_passes(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {
        "graphify": {
            "description": "d",
            "permitted-injections": [{"kind": "skill", "name": "graphify"}],
        }
    })
    registry = load_external_tools_registry(agent_meta_root, {}, project_root)
    assert registry["graphify"]["permitted-injections"] == [{"kind": "skill", "name": "graphify"}]


# ---------------------------------------------------------------------------
# resolve_injection_path
# ---------------------------------------------------------------------------

def test_resolve_injection_path_skill(tmp_path):
    pc = {"skills_dir": ".claude/skills"}
    entry = {"kind": "skill", "name": "graphify"}
    result = resolve_injection_path(entry, pc, tmp_path)
    assert result == (tmp_path / ".claude" / "skills" / "graphify").resolve()


def test_resolve_injection_path_config_uses_path_verbatim(tmp_path):
    pc = {}
    entry = {"kind": "config", "path": ".claude/settings.json"}
    result = resolve_injection_path(entry, pc, tmp_path)
    assert result == (tmp_path / ".claude" / "settings.json").resolve()


def test_resolve_injection_path_defaults_without_explicit_dir(tmp_path):
    pc = {}  # no hooks_dir set — must fall back to .claude/hooks
    entry = {"kind": "hook", "name": "graphify-guard.sh"}
    result = resolve_injection_path(entry, pc, tmp_path)
    assert result == (tmp_path / ".claude" / "hooks" / "graphify-guard.sh").resolve()


# ---------------------------------------------------------------------------
# _generate_tool_rule_content with permitted-injections rendering
# ---------------------------------------------------------------------------

def test_rule_content_renders_permitted_injections(tmp_path):
    from scripts.lib.external_tools import _generate_tool_rule_content
    tool_def = {
        "description": "d",
        "permitted-injections": [
            {"kind": "skill", "name": "graphify", "description": "Claude-Code-Skill"},
        ],
    }
    content = _generate_tool_rule_content(
        "graphify", tool_def, pc={"skills_dir": ".claude/skills"}, project_root=tmp_path
    )
    assert "## Erlaubte Injektionen" in content
    assert ".claude/skills/graphify" in content
    assert "Claude-Code-Skill" in content


def test_rule_content_omits_section_when_no_injections(tmp_path):
    from scripts.lib.external_tools import _generate_tool_rule_content
    content = _generate_tool_rule_content(
        "graphify", {"description": "d"}, pc={}, project_root=tmp_path
    )
    assert "## Erlaubte Injektionen" not in content


# ---------------------------------------------------------------------------
# scan_injection_drift
# ---------------------------------------------------------------------------

def test_scan_injection_drift_flags_unexplained_skill_dir(tmp_path):
    from scripts.lib.external_tools import scan_injection_drift
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {"graphify": {"description": "d", "enabled-by-default": True}})
    # No permitted-injections declared — the skill dir below is unexplained.
    skills_dir = project_root / ".claude" / "skills" / "graphify"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("x", encoding="utf-8")

    provider_config = {"Claude": {
        "skills_dir": ".claude/skills", "hooks_dir": ".claude/hooks",
        "rules_dir": ".claude/rules", "agents_dir": ".claude/agents",
    }}
    findings = scan_injection_drift(agent_meta_root, project_root, {}, provider_config)
    paths = [f["path"] for f in findings["Claude"]]
    assert ".claude/skills/graphify" in paths


def test_scan_injection_drift_clean_when_declared(tmp_path):
    from scripts.lib.external_tools import scan_injection_drift
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {"graphify": {
        "description": "d", "enabled-by-default": True,
        "permitted-injections": [{"kind": "skill", "name": "graphify"}],
    }})
    skills_dir = project_root / ".claude" / "skills" / "graphify"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("x", encoding="utf-8")

    provider_config = {"Claude": {
        "skills_dir": ".claude/skills", "hooks_dir": ".claude/hooks",
        "rules_dir": ".claude/rules", "agents_dir": ".claude/agents",
    }}
    findings = scan_injection_drift(agent_meta_root, project_root, {}, provider_config)
    assert findings["Claude"] == []


def test_scan_injection_drift_flags_loose_root_file(tmp_path):
    from scripts.lib.external_tools import scan_injection_drift
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {})
    infra_root = project_root / ".claude"
    infra_root.mkdir(parents=True)
    (infra_root / "CLAUDE.md").write_text("rogue block", encoding="utf-8")

    provider_config = {"Claude": {
        "skills_dir": ".claude/skills", "hooks_dir": ".claude/hooks",
        "rules_dir": ".claude/rules", "agents_dir": ".claude/agents",
        "settings_file": ".claude/settings.json",
        "pending_tasks_file": ".claude/pending-tasks.md",
        "extension_dir": ".claude/3-project", "snippets_dir": ".claude/snippets",
        "artifact_dir": ".claude/artifacts",
    }}
    findings = scan_injection_drift(agent_meta_root, project_root, {}, provider_config)
    paths = [f["path"] for f in findings["Claude"]]
    assert ".claude/CLAUDE.md" in paths


def test_scan_injection_drift_flags_stray_agent_file(tmp_path):
    from scripts.lib.external_tools import scan_injection_drift
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {})
    agents_dir = project_root / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "rogue-role.md").write_text("x", encoding="utf-8")
    # A real agent-meta-managed role stays unflagged.
    (agents_dir / "developer.md").write_text("x", encoding="utf-8")
    (agents_dir / ".agent-meta-managed").write_text("developer.md\n", encoding="utf-8")

    provider_config = {"Claude": {
        "skills_dir": ".claude/skills", "hooks_dir": ".claude/hooks",
        "rules_dir": ".claude/rules", "agents_dir": ".claude/agents",
    }}
    findings = scan_injection_drift(agent_meta_root, project_root, {}, provider_config)
    paths = [f["path"] for f in findings["Claude"]]
    assert ".claude/agents/rogue-role.md" in paths
    assert ".claude/agents/developer.md" not in paths
