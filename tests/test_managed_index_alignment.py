"""Task 4 (stale-role-cleanup): pipeline prune wiring, OQ-4 index alignment
and S1/S2 stale-path visibility.

Covers:
- OQ-4 / IC-08: ``rules.py`` and ``commands.py`` always write their own
  ``.agent-meta-managed`` index (including the empty set) after cleanup.
- AC-09 / IC-05: the sync pipeline invokes ``prune_sync_backups`` after the
  drift stage, per managed directory, with the frozen OQ-2 policy (3/30).
- AC-18 / IC-09 / OQ-7: S1 (``context_file.auto_generate: false``) and S2
  (provider deactivated) are surfaced as warnings only — no write, and the
  opt-outs are never overridden.

The prune/visibility tests load ``scripts.lib.sync_pipeline`` after putting
``scripts`` on ``sys.path`` (it imports sibling ``lib.*`` modules absolutely,
mirroring ``tests/test_generated_file_drift_pipeline_wiring.py``).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from scripts.lib.log import SyncLog


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# --- OQ-4 / IC-08: unconditional managed-index write -----------------------


def test_rules_write_empty_index_and_clean_stale_entry(tmp_path: Path) -> None:
    """OQ-4: an empty managed set still yields a 0-byte index (the stale
    entry is deleted, not merely unlisted)."""
    from scripts.lib.rules import sync_rules

    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write(agent_meta_root, "rules/1-generic/dummy.md", "# Dummy\n")
    rules_dir = project_root / ".claude" / "rules"
    _write(project_root, ".claude/rules/stale.md", "old\n")
    (rules_dir / ".agent-meta-managed").write_text("stale.md\n", encoding="utf-8")

    # The only source is skipped for this provider -> now_managed stays empty.
    config = {"platforms": [], "rules": {"dummy": {"claude": "skip"}}}
    provider_config = {"Claude": {"skills_dir": ".claude/skills", "rules_dir": ".claude/rules"}}

    sync_rules(
        agent_meta_root, project_root, config, SyncLog(), dry_run=False,
        provider="Claude", provider_config=provider_config, variables={},
    )

    index_path = rules_dir / ".agent-meta-managed"
    assert index_path.read_bytes() == b""
    assert not (rules_dir / "stale.md").exists()


def test_commands_write_empty_index_and_clean_stale_entry(tmp_path: Path) -> None:
    """OQ-4: with no command sources at all, commands.py still writes the
    empty index and sweeps the stale entry it previously tracked."""
    from scripts.lib.commands import sync_commands_for_provider

    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write(
        agent_meta_root, "config/provider-capabilities.yaml",
        "capabilities:\n  Claude:\n    commands: true\n",
    )
    commands_dir = project_root / ".claude" / "commands"
    _write(project_root, ".claude/commands/stale.md", "old\n")
    (commands_dir / ".agent-meta-managed").write_text("stale.md\n", encoding="utf-8")

    provider_config = {"Claude": {"commands_dir": ".claude/commands"}}
    sync_commands_for_provider(
        agent_meta_root, project_root, {}, SyncLog(), dry_run=False,
        provider="Claude", provider_config=provider_config,
    )

    index_path = commands_dir / ".agent-meta-managed"
    assert index_path.read_bytes() == b""
    assert not (commands_dir / "stale.md").exists()


# --- AC-09 / IC-05: prune wiring after the drift stage ---------------------


def test_pipeline_invokes_prune_after_drift(tmp_path: Path, monkeypatch) -> None:
    """AC-09: the drift stage prunes every managed dir with the frozen OQ-2
    policy, after the drift scan, in the same stage."""
    import scripts.lib.sync_pipeline as sync_pipeline

    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "edited by hand")
    (project_root / ".claude" / "agents" / ".agent-meta-managed").write_text(
        "developer.md\n", encoding="utf-8",
    )
    provider_config = {
        "Claude": {"agents_dir": ".claude/agents", "skills_dir": ".claude/skills"},
    }
    calls: list[tuple] = []

    def _spy(target_dir, prj_root, log, dry_run, max_age_days, max_per_source):
        calls.append((Path(target_dir), Path(prj_root), dry_run, max_age_days, max_per_source))
        return []

    monkeypatch.setattr(sync_pipeline, "prune_sync_backups", _spy)

    sync_pipeline._sync_stage_generated_file_drift_scan(
        tmp_path / "agent-meta", project_root, {}, provider_config,
        argparse.Namespace(dry_run=False), SyncLog(),
    )

    pruned_dirs = {call[0] for call in calls}
    assert project_root / ".claude" / "agents" in pruned_dirs, calls
    assert all(
        call[2] is False and call[3] == 30 and call[4] == 3 for call in calls
    ), calls


# --- AC-18 / IC-09: S1 / S2 visibility (warnings only) ---------------------


def test_auto_generate_false_emits_warning_without_write(tmp_path: Path) -> None:
    """AC-18/S1: ``auto_generate: false`` is never overridden; the skip is
    surfaced as a warning and the context file is not touched."""
    import scripts.lib.sync_pipeline as sync_pipeline

    project_root = tmp_path / "project"
    context_file = project_root / ".claude" / "CLAUDE.md"
    context_file.parent.mkdir(parents=True, exist_ok=True)
    context_file.write_text("ORIGINAL", encoding="utf-8")
    provider_config = {"Claude": {"context_file": "CLAUDE.md"}}
    log = SyncLog()

    sync_pipeline._sync_stage_contexts(
        tmp_path / "agent-meta", project_root,
        {"context_file": {"auto_generate": False}},
        provider_config, ["Claude"], {},
        argparse.Namespace(dry_run=False), log,
    )

    assert context_file.read_text(encoding="utf-8") == "ORIGINAL"
    assert any(
        "auto_generate" in warning and "S1" in warning for warning in log.warnings
    ), log.warnings


def test_deactivated_provider_emits_warning_without_write(tmp_path: Path) -> None:
    """AC-18/S2: a deactivated provider is skipped (no context write) and the
    skip is surfaced as a warning, never as a forced refresh."""
    import scripts.lib.sync_pipeline as sync_pipeline

    project_root = tmp_path / "project"
    provider_config = {"Claude": {"context_file": "CLAUDE.md"}}
    config = {
        "provider-deactivation": {
            "enabled": True, "mode": "selective", "providers": ["Claude"],
        },
    }
    log = SyncLog()

    sync_pipeline._sync_stage_contexts(
        tmp_path / "agent-meta", project_root, config,
        provider_config, ["Claude"], {},
        argparse.Namespace(dry_run=False), log,
    )

    assert not (project_root / ".claude" / "CLAUDE.md").exists()
    assert any(
        "deactivated" in warning and "S2" in warning for warning in log.warnings
    ), log.warnings
