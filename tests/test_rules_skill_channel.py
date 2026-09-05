"""Tests for scripts/lib/rules.py's 'channel: skill' lazy-rule mechanism and
the Continue alwaysApply: false + description frontmatter (token-efficiency
review, 2026-08-14: rules-preset 'silent' turned out to be a no-op on Claude
Code — .claude/skills/<name>/SKILL.md is the only real lazy-load channel).
"""

from pathlib import Path

import pytest

from scripts.lib.log import SyncLog
from scripts.lib.rules import _build_always_apply_frontmatter, sync_rules
from scripts.lib.skill_channel import (
    first_body_line_after_h1,
    provider_supports_skill_channel,
    resolve_skill_description,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_generic_rules(agent_meta_root: Path) -> None:
    _write(
        agent_meta_root / "rules" / "1-generic" / "sync-interface.md",
        "# Sync Interface\n\n> Use when running sync.py.\n\nBody paragraph one.\n",
    )
    _write(
        agent_meta_root / "rules" / "1-generic" / "branch-guard.md",
        "# Branch Guard\n\nAlways use feature branches.\n",
    )


# ---------------------------------------------------------------------------
# first_body_line_after_h1 / resolve_skill_description
# ---------------------------------------------------------------------------

def test_first_body_line_after_h1_strips_blockquote():
    content = "# Title\n\n> A tagline.\n\nMore text.\n"
    assert first_body_line_after_h1(content) == "A tagline."


def test_first_body_line_after_h1_skips_blank_and_heading_lines():
    content = "# Title\n\n\n## Subheading\n\nActual first line.\n"
    assert first_body_line_after_h1(content) == "Actual first line."


def test_resolve_skill_description_prefers_explicit_skill_description():
    opts = {"skill-description": "Explicit description."}
    content = "# Title\n\nFallback text.\n"
    assert resolve_skill_description(opts, content) == "Explicit description."


def test_resolve_skill_description_falls_back_to_first_body_line():
    content = "# Title\n\nFallback text.\n"
    assert resolve_skill_description({}, content) == "Fallback text."


# ---------------------------------------------------------------------------
# provider_supports_skill_channel
# ---------------------------------------------------------------------------

def test_provider_supports_skill_channel_claude_with_skills_dir():
    assert provider_supports_skill_channel("Claude", {"skills_dir": ".claude/skills"}) is True


@pytest.mark.parametrize("provider", ["Gemini", "Copilot", "Mammouth", "Continue",
                                      "Codex", "ZCode", "KimiCode"])
def test_provider_supports_skill_channel_excludes_non_allowlisted(provider):
    assert provider_supports_skill_channel(provider, {"skills_dir": f".{provider.lower()}/skills"}) is False


def test_provider_supports_skill_channel_false_without_skills_dir():
    assert provider_supports_skill_channel("Claude", {}) is False


# ---------------------------------------------------------------------------
# _build_always_apply_frontmatter
# ---------------------------------------------------------------------------

def test_build_always_apply_frontmatter_adds_description():
    out = _build_always_apply_frontmatter("# Title\n\nBody.\n", "A description.")
    assert "alwaysApply: false" in out
    assert 'description: "A description."' in out
    assert out.endswith("# Title\n\nBody.\n")


def test_build_always_apply_frontmatter_no_description_when_empty():
    out = _build_always_apply_frontmatter("# Title\n\nBody.\n", "")
    assert "alwaysApply: false" in out
    assert "description:" not in out


# ---------------------------------------------------------------------------
# sync_rules() — channel: skill routing
# ---------------------------------------------------------------------------

def test_sync_rules_channel_skill_writes_skill_md_not_rules_dir(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _make_generic_rules(agent_meta_root)

    config = {"rules": {"sync-interface": {"channel": "skill", "skill-description": "Use when syncing."}}}
    provider_config = {"Claude": {"skills_dir": ".claude/skills"}}

    sync_rules(
        agent_meta_root, project_root, config, SyncLog(), dry_run=False,
        provider="Claude", provider_config=provider_config, variables={},
    )

    skill_path = project_root / ".claude" / "skills" / "sync-interface" / "SKILL.md"
    rule_path = project_root / ".claude" / "rules" / "sync-interface.md"
    assert skill_path.exists()
    assert not rule_path.exists()
    text = skill_path.read_text(encoding="utf-8")
    assert text.startswith("---\nname: sync-interface\n")
    assert 'description: "Use when syncing."' in text
    assert "# Sync Interface" in text
    assert "Body paragraph one." in text
    # Untouched rule stays a plain rules_dir file.
    assert (project_root / ".claude" / "rules" / "branch-guard.md").exists()


def test_sync_rules_channel_skill_content_preserved_verbatim(tmp_path):
    # No information loss: the full original rule body (including a
    # "Bekannte Grenzen" style section) must survive the move unchanged.
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write(
        agent_meta_root / "rules" / "1-generic" / "sync-interface.md",
        "# Sync Interface\n\n> tagline\n\nBody.\n\n## Bekannte Grenzen\n\nEdge case text.\n",
    )
    config = {"rules": {"sync-interface": {"channel": "skill"}}}
    provider_config = {"Claude": {"skills_dir": ".claude/skills"}}

    sync_rules(
        agent_meta_root, project_root, config, SyncLog(), dry_run=False,
        provider="Claude", provider_config=provider_config, variables={},
    )

    text = (project_root / ".claude" / "skills" / "sync-interface" / "SKILL.md").read_text(encoding="utf-8")
    assert "## Bekannte Grenzen" in text
    assert "Edge case text." in text


def test_sync_rules_channel_skill_ignored_for_gemini(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _make_generic_rules(agent_meta_root)

    config = {"rules": {"sync-interface": {"channel": "skill"}}}
    provider_config = {"Gemini": {"skills_dir": ".gemini/skills", "rules_dir": ".gemini/rules"}}

    sync_rules(
        agent_meta_root, project_root, config, SyncLog(), dry_run=False,
        provider="Gemini", provider_config=provider_config, variables={},
        rules_dir=".gemini/rules",
    )

    assert not (project_root / ".gemini" / "skills" / "sync-interface" / "SKILL.md").exists()
    assert (project_root / ".gemini" / "rules" / "sync-interface.md").exists()


def test_sync_rules_channel_skill_reverts_to_rules_dir_when_disabled(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _make_generic_rules(agent_meta_root)
    provider_config = {"Claude": {"skills_dir": ".claude/skills"}}

    sync_rules(
        agent_meta_root, project_root, {"rules": {"sync-interface": {"channel": "skill"}}},
        SyncLog(), dry_run=False, provider="Claude", provider_config=provider_config, variables={},
    )
    skill_path = project_root / ".claude" / "skills" / "sync-interface" / "SKILL.md"
    rule_path = project_root / ".claude" / "rules" / "sync-interface.md"
    assert skill_path.exists()
    assert not rule_path.exists()

    # Preset/override reverts to normal — old SKILL.md must be cleaned up and
    # the skill's now-empty directory removed, rule file restored.
    sync_rules(
        agent_meta_root, project_root, {}, SyncLog(), dry_run=False,
        provider="Claude", provider_config=provider_config, variables={},
    )
    assert not skill_path.exists()
    assert not skill_path.parent.exists()
    assert rule_path.exists()


def test_sync_rules_channel_skill_dry_run_does_not_write(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _make_generic_rules(agent_meta_root)
    provider_config = {"Claude": {"skills_dir": ".claude/skills"}}

    sync_rules(
        agent_meta_root, project_root, {"rules": {"sync-interface": {"channel": "skill"}}},
        SyncLog(), dry_run=True, provider="Claude", provider_config=provider_config, variables={},
    )
    assert not (project_root / ".claude" / "skills" / "sync-interface" / "SKILL.md").exists()
    assert not (project_root / ".claude" / "rules" / "sync-interface.md").exists()


def test_sync_rules_channel_skill_shares_index_with_external_skills(tmp_path):
    # Regression test: skills_dir's ".agent-meta-managed" index is shared
    # with scripts/lib/skills.py — writing a channel:skill rule must not
    # wipe out an existing external-skill entry already tracked there.
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _make_generic_rules(agent_meta_root)
    provider_config = {"Claude": {"skills_dir": ".claude/skills"}}

    index_path = project_root / ".claude" / "skills" / ".agent-meta-managed"
    _write(index_path, "graphify\n")

    sync_rules(
        agent_meta_root, project_root, {"rules": {"sync-interface": {"channel": "skill"}}},
        SyncLog(), dry_run=False, provider="Claude", provider_config=provider_config, variables={},
    )

    managed = set(index_path.read_text(encoding="utf-8").split())
    assert managed == {"graphify", "sync-interface"}
