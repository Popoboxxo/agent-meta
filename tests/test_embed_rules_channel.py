"""Regression tests for issue #192 Phase 2: selective rule embedding.

Contracts:
  1. A rule flagged ``embed: false`` (or ``channel: skill``) leaves the shared
     managed block when EVERY provider sharing the context_file has a
     ``skills_dir`` (progressive-disclosure file channel, config-key driven —
     no provider-name branching).
  2. sync_embedded_rule_files() renders exactly those rules as separate
     ``<skills_dir>/<rule>/SKILL.md`` files for has_rules:false providers.
  3. WITHOUT the file channel (a sharer without skills_dir) the rule EMBEDS
     as fallback — a preset opt-out must never delete content a provider
     cannot load from anywhere else (issue #192 risk note: weak providers
     keep embedding; the former drop-behaviour was silent content loss).
  4. context_file.auto_generate (issue #540 Fix 3): default true; false
     leaves context files untouched (dev-written mode).
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def env():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from lib.config import build_variables, load_config
    from lib.context import _build_managed_block
    from lib.log import SyncLog
    from lib.providers import load_providers_config
    from lib.rules import sync_embedded_rule_files

    config = load_config(REPO_ROOT / ".meta-config" / "project.yaml")
    variables, _ = build_variables(config, REPO_ROOT)
    variables.setdefault("PIPELINE_DETAILS_DIR", ".opencode/pipeline-details")
    return {
        "config": config,
        "variables": variables,
        "provider_config": load_providers_config(REPO_ROOT),
        "build_block": _build_managed_block,
        "sync_files": sync_embedded_rule_files,
        "log": SyncLog(),
    }


def _no_worktree_override(env) -> dict:
    """Config copy with a project-level embed:false override (beats the lazy
    preset's channel: skill via resolve_rules precedence)."""
    config = dict(env["config"])
    config["rules"] = {"no-worktree-isolation": {"embed": False}}
    return config


def test_embed_false_rule_leaves_block_when_group_has_file_channel(env):
    config = _no_worktree_override(env)
    block = env["build_block"](
        REPO_ROOT, config, env["variables"], env["log"],
        provider="Opencode", provider_config=env["provider_config"],
        project_root=REPO_ROOT,
    )
    assert "# No Worktree Isolation" not in block  # body left the embed
    assert "## Übrige Regeln (Lazy-Load)" in block  # pointer took its place
    assert "{{SKILLS_DIR}}" not in block  # pointer placeholder fully resolved


def test_embed_false_rule_embeds_without_file_channel(env):
    # Simulate a weak sharer: ZCode without skills_dir → the whole AGENTS.md
    # group loses the file channel → the rule must EMBED, never drop.
    provider_config = {k: dict(v) for k, v in env["provider_config"].items()}
    provider_config["ZCode"] = {**provider_config["ZCode"], "skills_dir": None}
    config = _no_worktree_override(env)
    block = env["build_block"](
        REPO_ROOT, config, env["variables"], env["log"],
        provider="Opencode", provider_config=provider_config,
        project_root=REPO_ROOT,
    )
    assert "# No Worktree Isolation" in block  # fallback: embedded, not lost
    assert "## Übrige Regeln (Lazy-Load)" not in block


def test_embedded_rule_files_written_for_opencode(env, tmp_path):
    # The lazy preset routes these rules via channel: skill — for a
    # has_rules:false provider they must land as separate SKILL.md files.
    env["sync_files"](
        REPO_ROOT, tmp_path, env["config"], env["log"], dry_run=False,
        variables=env["variables"], provider="Opencode",
        provider_config=env["provider_config"],
    )
    for name in ("sync-interface", "architecture", "conventions", "admin-ui"):
        skill = tmp_path / ".opencode" / "skills" / name / "SKILL.md"
        assert skill.exists(), f"{name}: SKILL.md missing"
        assert skill.read_text(encoding="utf-8").startswith("---\n")

    # Core (always-embedded) rules must NOT be duplicated into the file
    # channel — they stay the managed block's payload.
    for name in ("branch-guard", "commit-conventions", "use-orchestrator"):
        assert not (tmp_path / ".opencode" / "skills" / name / "SKILL.md").exists()


def test_embedded_rule_files_written_for_weak_provider(env, tmp_path):
    # ZCode (has_rules: false, skills_dir: .zcode/skills) gets the same
    # separate-file treatment — config-key gating, no provider-name branch.
    env["sync_files"](
        REPO_ROOT, tmp_path, env["config"], env["log"], dry_run=False,
        variables=env["variables"], provider="ZCode",
        provider_config=env["provider_config"],
    )
    assert (tmp_path / ".zcode" / "skills" / "sync-interface" / "SKILL.md").exists()


def test_embedded_rule_files_noop_for_has_rules_provider(env, tmp_path):
    # Gemini has_rules: true — its files come from sync_rules(); this channel
    # must not double-write.
    env["sync_files"](
        REPO_ROOT, tmp_path, env["config"], env["log"], dry_run=False,
        variables=env["variables"], provider="Gemini",
        provider_config=env["provider_config"],
    )
    assert not (tmp_path / ".gemini" / "skills").exists()


def test_shared_block_identical_with_and_without_embed_false(env):
    # Issue #638 convergence must hold under the new flags: every sharer of
    # AGENTS.md renders byte-identical managed blocks.
    config = _no_worktree_override(env)
    blocks = {
        provider: env["build_block"](
            REPO_ROOT, config, env["variables"], env["log"],
            provider=provider, provider_config=env["provider_config"],
            project_root=REPO_ROOT,
        )
        for provider in ("Opencode", "Gemini", "Codex", "ZCode", "KimiCode")
    }
    assert len(set(blocks.values())) == 1


# ---------------------------------------------------------------------------
# Issue #192 Phase 2 (WP-A scope extension): MCP / external-tool sections
# ---------------------------------------------------------------------------


def test_mcp_and_tool_sections_leave_block_on_file_channel(env):
    # The lazy preset flags mcp-<server> and tool-<name> with channel: skill;
    # with the whole AGENTS.md sharer group having a skills_dir, the full
    # per-server sections leave the managed block. The embedded
    # mcp-guardrails rule keeps the hard-prohibition one-liners always-on.
    block = env["build_block"](
        REPO_ROOT, env["config"], env["variables"], env["log"],
        provider="Opencode", provider_config=env["provider_config"],
        project_root=REPO_ROOT,
    )
    for gone in ("# MCP: honcho", "# MCP: playwright", "# MCP: reqogniloom",
                 "## Erlaubte Tools", "# External Tool: graphify",
                 "Details/Registrierung: `config/external-tools-registry.yaml`."):
        assert gone not in block, f"MCP/tool section still embedded: {gone}"
    assert "# MCP Hard Prohibitions" in block
    assert "- **reqogniloom:** `workspace.close`" in block  # anchor survives
    assert "## Übrige Regeln (Lazy-Load)" in block


def test_mcp_and_tool_sections_embed_without_file_channel(env):
    # A sharer without skills_dir removes the group file channel → the
    # MCP/tool sections EMBED again (fallback, never content loss).
    provider_config = {k: dict(v) for k, v in env["provider_config"].items()}
    provider_config["ZCode"] = {**provider_config["ZCode"], "skills_dir": None}
    block = env["build_block"](
        REPO_ROOT, env["config"], env["variables"], env["log"],
        provider="Opencode", provider_config=provider_config,
        project_root=REPO_ROOT,
    )
    assert "# MCP: honcho" in block
    assert "## Erlaubte Tools" in block
    assert "# External Tool: graphify" in block
    assert "## Übrige Regeln (Lazy-Load)" not in block


def test_mcp_artifacts_written_for_opencode(env, tmp_path):
    # generate_mcp_artifacts writes the FULL per-server sections as separate
    # SKILL.md files for has_rules:false providers with a skills_dir.
    from lib.mcp import generate_mcp_artifacts

    generate_mcp_artifacts(
        REPO_ROOT, tmp_path, env["config"], env["provider_config"], env["log"],
        dry_run=False, provider="Opencode", rules_dir=None,
    )
    for server in ("honcho", "playwright", "reqogniloom", "viz-logger"):
        skill = tmp_path / ".opencode" / "skills" / f"mcp-{server}" / "SKILL.md"
        assert skill.exists(), f"mcp-{server}: SKILL.md missing"
        text = skill.read_text(encoding="utf-8")
        assert "## Verbotene Tools (ABSOLUT — keine Ausnahmen)" in text or \
            "## Erlaubte Tools" in text, f"mcp-{server}: full section lost"


def test_tool_artifacts_written_for_opencode(env, tmp_path):
    from lib.external_tools import generate_external_tool_artifacts

    generate_external_tool_artifacts(
        REPO_ROOT, tmp_path, env["config"], env["provider_config"], env["log"],
        dry_run=False, provider="Opencode", rules_dir=None,
    )
    skill = tmp_path / ".opencode" / "skills" / "tool-graphify" / "SKILL.md"
    assert skill.exists()
    assert "graphify" in skill.read_text(encoding="utf-8").lower()


def test_mcp_artifacts_unchanged_for_has_rules_provider(env, tmp_path):
    # Gemini (has_rules:true): rule files still land in its rules_dir — the
    # #192 channel must not double-write into .gemini/skills.
    from lib.mcp import generate_mcp_artifacts

    pc = env["provider_config"]["Gemini"]
    generate_mcp_artifacts(
        REPO_ROOT, tmp_path, env["config"], env["provider_config"], env["log"],
        dry_run=False, provider="Gemini", rules_dir=pc.get("rules_dir"),
    )
    assert (tmp_path / ".gemini" / "rules" / "mcp-honcho.md").exists()
    assert not (tmp_path / ".gemini" / "skills" / "mcp-honcho").exists()


# ---------------------------------------------------------------------------
# Issue #437 follow-up — skill-channel orphan sweep
# ---------------------------------------------------------------------------


def test_sweep_removes_orphaned_skill_channel_entry(env, tmp_path):
    # A stem listed in the shared index whose source vanished from ALL
    # writers (rules/mcp/tools/skills) must be swept: directory + index entry.
    # The #437 case: rules/1-generic/python-conventions.md deleted, but its
    # channel: skill copy survived because every writer cleans only within
    # its own universe and the stem left all universes.
    from lib.skill_channel import sweep_orphan_skill_channel_rules

    skills_dir = tmp_path / ".claude" / "skills"
    (skills_dir / "python-conventions").mkdir(parents=True)
    (skills_dir / "python-conventions" / "SKILL.md").write_text(
        "---\nname: python-conventions\ndescription: d\n---\nbody", encoding="utf-8"
    )
    (skills_dir / "surviving-skill").mkdir()
    (skills_dir / "surviving-skill" / "SKILL.md").write_text("x", encoding="utf-8")
    (skills_dir / ".agent-meta-managed").write_text(
        "python-conventions\nsurviving-skill\n", encoding="utf-8"
    )

    sweep_orphan_skill_channel_rules(
        tmp_path, skills_dir, {"surviving-skill"}, env["log"], False
    )

    assert not (skills_dir / "python-conventions").exists()
    assert (skills_dir / "surviving-skill" / "SKILL.md").exists()
    index = (skills_dir / ".agent-meta-managed").read_text(encoding="utf-8")
    assert "python-conventions" not in index
    assert "surviving-skill" in index


def test_sweep_drops_index_entry_without_directory(env, tmp_path):
    # Index-only orphan (file already gone manually): the entry must still
    # leave the index, and an index that becomes empty is removed entirely.
    from lib.skill_channel import sweep_orphan_skill_channel_rules

    skills_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / ".agent-meta-managed").write_text("ghost-stem\n", encoding="utf-8")

    sweep_orphan_skill_channel_rules(tmp_path, skills_dir, set(), env["log"], False)

    assert not (skills_dir / ".agent-meta-managed").exists()


def test_skill_channel_universe_covers_all_writers(env):
    # The union must contain every live writer's stems, so the sweep can only
    # remove genuinely orphaned entries.
    from lib.sync_pipeline import _skill_channel_universe

    universe = _skill_channel_universe(REPO_ROOT, env["config"], REPO_ROOT)
    assert "sync-interface" in universe        # rules/ source
    assert "mcp-honcho" in universe            # mcp-registry.yaml
    assert "tool-graphify" in universe         # external-tools-registry.yaml
    assert "reqogniloom-risk-analyst" in universe  # skills-registry.yaml


def test_orphaned_rule_is_swept_from_repo_config_skills_dir(env, tmp_path):
    # End-to-end shape of the #437 finding (Claude path): a channel: skill
    # copy of a since-deleted rule survives the per-writer cleanups (the stem
    # left their universes), and only the union sweep removes it — while the
    # live lazy rules stay.
    from lib.rules import sync_rules
    from lib.skills import (
        _read_skills_managed_index,
        _write_skills_managed_index,
    )
    from lib.skill_channel import sweep_orphan_skill_channel_rules

    skills_dir = tmp_path / ".claude" / "skills"
    pc = env["provider_config"]["Claude"]
    rules_dir = tmp_path / ".claude" / "rules"

    # Seed the orphan exactly as an older sync left it: SKILL.md + index entry.
    skills_dir.mkdir(parents=True)
    _write_skills_managed_index(skills_dir, {"python-conventions"}, False,
                                universe={"python-conventions"})

    sync_rules(
        REPO_ROOT, tmp_path, env["config"], env["log"], dry_run=False,
        variables=env["variables"], rules_dir=rules_dir,
        provider="Claude", provider_config=env["provider_config"],
    )
    # The per-writer cleanup cannot remove the orphan: its stem left the
    # rules universe, and the merge-mode index keeps unowned entries.
    assert "python-conventions" in _read_skills_managed_index(skills_dir)

    sweep_orphan_skill_channel_rules(
        tmp_path, skills_dir, _union(env), env["log"], False,
    )

    assert not (skills_dir / "python-conventions").exists()
    assert "python-conventions" not in _read_skills_managed_index(skills_dir)
    assert (skills_dir / "sync-interface" / "SKILL.md").exists()
    assert "sync-interface" in _read_skills_managed_index(skills_dir)


def _union(env):
    from lib.sync_pipeline import _skill_channel_universe

    return _skill_channel_universe(REPO_ROOT, env["config"], REPO_ROOT)


# ---------------------------------------------------------------------------
# Issue #540 Fix 3 — context_file.auto_generate
# ---------------------------------------------------------------------------


def test_auto_generate_defaults_true():
    from lib.sync_pipeline import _context_auto_generate

    assert _context_auto_generate({}) is True
    assert _context_auto_generate({"context_file": {}}) is True
    assert _context_auto_generate({"context_file": {"mode": "compact"}}) is True


def test_auto_generate_false_is_honored():
    from lib.sync_pipeline import _context_auto_generate

    assert _context_auto_generate({"context_file": {"auto_generate": False}}) is False
    # Non-dict context_file block (config typo) must fail safe to true.
    assert _context_auto_generate({"context_file": "compact"}) is True
