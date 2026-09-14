"""Tests for scripts/lib/generated_file_drift.py.

Detects when a sync.py-generated file (anything tracked via
.agent-meta-managed) was manually edited since the last sync, via a
content-hash sidecar store. Warn-only -- write behavior is unaffected.
Spec: docs/superpowers/specs/2026-09-07-generated-file-drift-detection-design.md
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.generated_file_drift import (
    _hashes_path,
    _load_allowlist_patterns,
    _load_hashes,
    _save_hashes,
    is_allowlisted,
    is_drift_detection_enabled,
)


def test_hashes_path_is_meta_config_generated_file_hashes_json(tmp_path: Path) -> None:
    assert _hashes_path(tmp_path) == tmp_path / ".meta-config" / "generated-file-hashes.json"


def test_load_hashes_returns_empty_dict_when_file_absent(tmp_path: Path) -> None:
    assert _load_hashes(tmp_path) == {}


def test_save_then_load_hashes_round_trips(tmp_path: Path) -> None:
    _save_hashes(tmp_path, {".claude/agents/developer.md": "abc123"}, dry_run=False)
    assert _load_hashes(tmp_path) == {".claude/agents/developer.md": "abc123"}


def test_save_hashes_is_noop_in_dry_run(tmp_path: Path) -> None:
    _save_hashes(tmp_path, {"x": "y"}, dry_run=True)
    assert not _hashes_path(tmp_path).exists()


def test_load_hashes_returns_empty_dict_on_malformed_json(tmp_path: Path) -> None:
    path = _hashes_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("not json", encoding="utf-8")
    assert _load_hashes(tmp_path) == {}


def test_load_allowlist_patterns_returns_empty_list_when_file_absent(tmp_path: Path) -> None:
    assert _load_allowlist_patterns(tmp_path) == []


def test_load_allowlist_patterns_reads_yaml_list(tmp_path: Path) -> None:
    meta = tmp_path / ".meta-config"
    meta.mkdir()
    (meta / "drift-allowlist.yaml").write_text(
        "allow-edits:\n  - .claude/commands/my-cmd.md\n  - .opencode/rules/*.md\n",
        encoding="utf-8",
    )
    assert _load_allowlist_patterns(tmp_path) == [
        ".claude/commands/my-cmd.md", ".opencode/rules/*.md",
    ]


def test_is_allowlisted_matches_exact_path() -> None:
    assert is_allowlisted(".claude/commands/my-cmd.md", [".claude/commands/my-cmd.md"])


def test_is_allowlisted_matches_glob() -> None:
    assert is_allowlisted(".opencode/rules/foo.md", [".opencode/rules/*.md"])


def test_is_allowlisted_false_when_no_pattern_matches() -> None:
    assert not is_allowlisted(".claude/agents/developer.md", [".claude/commands/*.md"])


def test_is_allowlisted_false_for_empty_patterns() -> None:
    assert not is_allowlisted(".claude/agents/developer.md", [])


def test_is_drift_detection_enabled_defaults_true_when_key_absent() -> None:
    assert is_drift_detection_enabled({}) is True


def test_is_drift_detection_enabled_false_when_explicitly_disabled() -> None:
    assert is_drift_detection_enabled({"drift-detection": {"enabled": False}}) is False


def test_is_drift_detection_enabled_true_when_explicitly_enabled() -> None:
    assert is_drift_detection_enabled({"drift-detection": {"enabled": True}}) is True


from scripts.lib.generated_file_drift import scan_generated_file_drift


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _managed_index(root: Path, dir_rel: str, *names: str) -> None:
    index_path = root / dir_rel / ".agent-meta-managed"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("\n".join(names) + "\n", encoding="utf-8")


def _provider_config() -> dict:
    return {"Claude": {
        "agents_dir": ".claude/agents", "skills_dir": ".claude/skills",
        "hooks_dir": ".claude/hooks", "rules_dir": ".claude/rules",
        "commands_dir": ".claude/commands",
        "has_hooks": True, "has_rules": True, "has_commands": True,
    }}


def test_scan_flags_agent_file_whose_content_changed_since_last_hash(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "edited by hand")
    _managed_index(project_root, ".claude/agents", "developer.md")
    from scripts.lib.generated_file_drift import content_hash
    _save_hashes(project_root, {".claude/agents/developer.md": content_hash("original content")}, dry_run=False)

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    paths = [f["path"] for f in findings]
    assert ".claude/agents/developer.md" in paths


def test_scan_does_not_flag_file_with_no_stored_hash_yet(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "brand new")
    _managed_index(project_root, ".claude/agents", "developer.md")

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    assert findings == []


def test_scan_does_not_flag_unchanged_file(tmp_path: Path) -> None:
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "same content")
    _managed_index(project_root, ".claude/agents", "developer.md")
    _save_hashes(project_root, {".claude/agents/developer.md": content_hash("same content")}, dry_run=False)

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    assert findings == []


def test_scan_respects_allowlist(tmp_path: Path) -> None:
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".claude/commands/my-cmd.md", "edited by hand")
    _managed_index(project_root, ".claude/commands", "my-cmd.md")
    _save_hashes(project_root, {".claude/commands/my-cmd.md": content_hash("original")}, dry_run=False)
    meta = project_root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "drift-allowlist.yaml").write_text(
        "allow-edits:\n  - .claude/commands/*.md\n", encoding="utf-8",
    )

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    assert findings == []


def test_scan_covers_rules_dir_hooks_dir_and_pipeline_details(tmp_path: Path) -> None:
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".claude/rules/branch-guard.md", "edited")
    _managed_index(project_root, ".claude/rules", "branch-guard.md")
    _write(project_root, ".claude/hooks/dod-push-check.sh", "edited")
    _managed_index(project_root, ".claude/hooks", "dod-push-check.sh")
    _write(project_root, ".claude/pipeline-details/bugfix.md", "edited")
    _managed_index(project_root, ".claude/pipeline-details", "bugfix.md")
    _save_hashes(project_root, {
        ".claude/rules/branch-guard.md": content_hash("orig"),
        ".claude/hooks/dod-push-check.sh": content_hash("orig"),
        ".claude/pipeline-details/bugfix.md": content_hash("orig"),
    }, dry_run=False)

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    paths = {f["path"] for f in findings}
    assert paths == {
        ".claude/rules/branch-guard.md",
        ".claude/hooks/dod-push-check.sh",
        ".claude/pipeline-details/bugfix.md",
    }


def test_scan_covers_nested_managed_subdirs(tmp_path: Path) -> None:
    """hooks/lib/ and hooks/release-gates/ carry their OWN .agent-meta-managed
    index (issue #558) -- must be recursed into, not just the top-level hooks/."""
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".claude/hooks/lib/hook_common.sh", "edited")
    _managed_index(project_root, ".claude/hooks/lib", "hook_common.sh")
    _managed_index(project_root, ".claude/hooks")  # empty top-level index
    _save_hashes(project_root, {".claude/hooks/lib/hook_common.sh": content_hash("orig")}, dry_run=False)

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    paths = {f["path"] for f in findings}
    assert ".claude/hooks/lib/hook_common.sh" in paths


def test_scan_covers_skill_subdirectory_files(tmp_path: Path) -> None:
    """The skills_dir .agent-meta-managed index lists DIRECTORY names, not
    file names (e.g. "a2a-delegation-gates", a subdir containing SKILL.md)
    -- unlike every other managed dir, whose index lists file names
    directly. Must still be picked up and hashed/compared."""
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".claude/skills/a2a-delegation-gates/SKILL.md", "edited by hand")
    _managed_index(project_root, ".claude/skills", "a2a-delegation-gates")
    _save_hashes(project_root, {
        ".claude/skills/a2a-delegation-gates/SKILL.md": content_hash("original content"),
    }, dry_run=False)

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    paths = {f["path"] for f in findings}
    assert ".claude/skills/a2a-delegation-gates/SKILL.md" in paths


def test_scan_unions_rules_sidecar_indexes(tmp_path: Path) -> None:
    """rules/ has THREE index files (.agent-meta-managed, -mcp, -tools) for
    three different writers -- all three contribute managed filenames."""
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".claude/rules/mcp-honcho.md", "edited")
    (project_root / ".claude" / "rules").mkdir(parents=True, exist_ok=True)
    (project_root / ".claude" / "rules" / ".agent-meta-managed").write_text("", encoding="utf-8")
    (project_root / ".claude" / "rules" / ".agent-meta-managed-mcp").write_text("mcp-honcho.md\n", encoding="utf-8")
    _save_hashes(project_root, {".claude/rules/mcp-honcho.md": content_hash("orig")}, dry_run=False)

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    paths = {f["path"] for f in findings}
    assert ".claude/rules/mcp-honcho.md" in paths


def test_scan_only_covers_active_providers(tmp_path: Path) -> None:
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".gemini/agents/developer.md", "edited")
    _managed_index(project_root, ".gemini/agents", "developer.md")
    _save_hashes(project_root, {".gemini/agents/developer.md": content_hash("orig")}, dry_run=False)

    provider_config = {
        "Claude": _provider_config()["Claude"],
        "Gemini": {"agents_dir": ".gemini/agents", "skills_dir": ".gemini/skills"},
    }
    # config has no "ai-providers" key -> resolve_providers() defaults to
    # ["Claude"] only (see scripts/lib/providers.py) -- Gemini is not active.
    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, provider_config)
    assert findings == []


def test_scan_covers_context_adapter_in_per_provider_mode(tmp_path: Path) -> None:
    """AC-17: a generated context adapter is tracked for drift."""
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, "CLAUDE.md", "edited by hand")
    _save_hashes(project_root, {"CLAUDE.md": content_hash("original")}, dry_run=False)

    config = {"context_file": {"topology": "per-provider", "core_file": "AGENTS.md"}}
    provider_config = {
        "Claude": {
            **_provider_config()["Claude"],
            "context_adapter": True,
            "context_adapter_file": "CLAUDE.md",
        }
    }

    findings = scan_generated_file_drift(
        tmp_path / "agent-meta", project_root, config, provider_config
    )
    assert [f["path"] for f in findings] == ["CLAUDE.md"]


def test_scan_ignores_context_adapter_in_unified_mode(tmp_path: Path) -> None:
    """The default ``unified`` topology never opts adapters into the baseline."""
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, "CLAUDE.md", "edited by hand")
    _save_hashes(project_root, {"CLAUDE.md": content_hash("original")}, dry_run=False)

    config = {"context_file": {"topology": "unified", "core_file": "AGENTS.md"}}
    provider_config = {
        "Claude": {
            **_provider_config()["Claude"],
            "context_adapter": True,
            "context_adapter_file": "CLAUDE.md",
        }
    }

    findings = scan_generated_file_drift(
        tmp_path / "agent-meta", project_root, config, provider_config
    )
    assert findings == []


from scripts.lib.generated_file_drift import capture_generated_file_hashes, content_hash


def test_capture_writes_hash_for_every_managed_file(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "fresh content")
    _managed_index(project_root, ".claude/agents", "developer.md")

    capture_generated_file_hashes(tmp_path / "agent-meta", project_root, {}, _provider_config(), dry_run=False)

    assert _load_hashes(project_root) == {
        ".claude/agents/developer.md": content_hash("fresh content"),
    }


def test_capture_skips_sync_backup_siblings(tmp_path: Path) -> None:
    """`.sync-backup-<ts>` siblings must never enter the tracked hash baseline.

    They are ephemeral safety copies listed alongside generated files in a
    managed dir. Pinning them in the baseline would make the next sync report
    their (correct) removal as drift forever.
    """
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "fresh content")
    _write(
        project_root,
        ".claude/agents/developer.md.sync-backup-20260912-170235",
        "old content",
    )
    _managed_index(
        project_root,
        ".claude/agents",
        "developer.md",
        "developer.md.sync-backup-20260912-170235",
    )

    capture_generated_file_hashes(tmp_path / "agent-meta", project_root, {}, _provider_config(), dry_run=False)

    hashes = _load_hashes(project_root)
    assert ".claude/agents/developer.md" in hashes
    assert not any(".sync-backup-" in rel for rel in hashes)


def test_capture_skips_sync_backup_inside_managed_skill_dir(tmp_path: Path) -> None:
    """The skills dir index lists directory names; its rglob must skip backups."""
    project_root = tmp_path / "project"
    _write(project_root, ".claude/skills/a2a-delegation-gates/SKILL.md", "fresh content")
    _write(
        project_root,
        ".claude/skills/a2a-delegation-gates/SKILL.md.sync-backup-20260912-170235",
        "old content",
    )
    _managed_index(project_root, ".claude/skills", "a2a-delegation-gates")

    capture_generated_file_hashes(tmp_path / "agent-meta", project_root, {}, _provider_config(), dry_run=False)

    hashes = _load_hashes(project_root)
    assert ".claude/skills/a2a-delegation-gates/SKILL.md" in hashes
    assert not any(".sync-backup-" in rel for rel in hashes)


def test_capture_is_noop_in_dry_run(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "fresh content")
    _managed_index(project_root, ".claude/agents", "developer.md")

    capture_generated_file_hashes(tmp_path / "agent-meta", project_root, {}, _provider_config(), dry_run=True)

    assert _load_hashes(project_root) == {}


def test_capture_then_scan_round_trip_finds_no_drift(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "content v1")
    _managed_index(project_root, ".claude/agents", "developer.md")

    capture_generated_file_hashes(tmp_path / "agent-meta", project_root, {}, _provider_config(), dry_run=False)
    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())

    assert findings == []


def test_capture_overwrites_stale_hash_for_regenerated_content(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "content v1")
    _managed_index(project_root, ".claude/agents", "developer.md")
    _save_hashes(project_root, {".claude/agents/developer.md": content_hash("stale")}, dry_run=False)

    capture_generated_file_hashes(tmp_path / "agent-meta", project_root, {}, _provider_config(), dry_run=False)

    assert _load_hashes(project_root) == {
        ".claude/agents/developer.md": content_hash("content v1"),
    }


from scripts.lib.generated_file_drift import backup_drifted_files


def _backup_siblings(project_root: Path, rel: str) -> list[Path]:
    path = project_root / rel
    return sorted(path.parent.glob(f"{path.name}.sync-backup-*"))


def test_backup_writes_sibling_with_drifted_content(tmp_path: Path) -> None:
    """Issue #734: a drifted file gets a `.sync-backup-<ts>` sibling holding
    exactly the pre-overwrite content."""
    from scripts.lib.log import SyncLog
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "edited by hand")
    findings = [{"path": ".claude/agents/developer.md", "provider": "Claude"}]

    backups = backup_drifted_files(findings, project_root, SyncLog(), dry_run=False)

    assert len(backups) == 1
    assert backups[0].startswith(".claude/agents/developer.md.sync-backup-")
    siblings = _backup_siblings(project_root, ".claude/agents/developer.md")
    assert len(siblings) == 1
    assert siblings[0].read_text(encoding="utf-8") == "edited by hand"


def test_backup_uses_one_timestamp_across_all_findings(tmp_path: Path) -> None:
    from scripts.lib.log import SyncLog
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/a.md", "A")
    _write(project_root, ".claude/agents/b.md", "B")
    findings = [
        {"path": ".claude/agents/a.md", "provider": "Claude"},
        {"path": ".claude/agents/b.md", "provider": "Claude"},
    ]

    backups = backup_drifted_files(findings, project_root, SyncLog(), dry_run=False)

    timestamps = {name.rsplit(".sync-backup-", 1)[1] for name in backups}
    assert len(timestamps) == 1
    assert len(backups) == 2


def test_backup_writes_nothing_without_findings(tmp_path: Path) -> None:
    """No drift -> the scan yields no findings -> no backup sibling."""
    from scripts.lib.log import SyncLog
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "unchanged")
    _managed_index(project_root, ".claude/agents", "developer.md")
    from scripts.lib.generated_file_drift import content_hash
    _save_hashes(project_root, {
        ".claude/agents/developer.md": content_hash("unchanged"),
    }, dry_run=False)

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    assert findings == []
    assert backup_drifted_files(findings, project_root, SyncLog(), dry_run=False) == []
    assert list(project_root.rglob("*.sync-backup-*")) == []


def test_backup_writes_nothing_in_dry_run(tmp_path: Path) -> None:
    from scripts.lib.log import SyncLog
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "edited by hand")
    findings = [{"path": ".claude/agents/developer.md", "provider": "Claude"}]

    backups = backup_drifted_files(findings, project_root, SyncLog(), dry_run=True)

    assert list(project_root.rglob("*.sync-backup-*")) == []
    # dry-run still reports where a backup would have been written
    assert backups and backups[0].startswith(".claude/agents/developer.md.sync-backup-")


def test_backup_is_fail_soft_when_target_is_missing(tmp_path: Path) -> None:
    from scripts.lib.log import SyncLog
    project_root = tmp_path / "project"

    backups = backup_drifted_files(
        [{"path": ".claude/agents/gone.md", "provider": "Claude"}],
        project_root, SyncLog(), dry_run=False,
    )

    assert backups == []


from datetime import datetime, timedelta

from scripts.lib.generated_file_drift import prune_sync_backups


def _stamp(days_ago: int) -> str:
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y%m%d-%H%M%S")


def _write_backup(project_root: Path, rel: str, stamp: str) -> Path:
    path = project_root / f"{rel}.sync-backup-{stamp}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("old content", encoding="utf-8")
    return path


def _backup_count(target_dir: Path) -> int:
    return len([p for p in target_dir.iterdir() if p.is_file() and ".sync-backup-" in p.name])


def test_prune_noop_in_dry_run(tmp_path: Path) -> None:
    """AC-09: in dry_run nothing is pruned and no filesystem mutation occurs."""
    from scripts.lib.log import SyncLog
    project_root = tmp_path / "project"
    target_dir = project_root / ".claude" / "agents"
    for days in (100, 90, 80, 70, 60, 50):
        _write_backup(project_root, ".claude/agents/a.md", _stamp(days))

    pruned = prune_sync_backups(
        target_dir, project_root, SyncLog(), dry_run=True,
        max_age_days=30, max_per_source=3,
    )

    assert pruned == []
    assert _backup_count(target_dir) == 6


def test_prune_never_deletes_newest_backup(tmp_path: Path) -> None:
    """AC-09: the most recent backup of a source is never pruned."""
    from scripts.lib.log import SyncLog
    project_root = tmp_path / "project"
    target_dir = project_root / ".claude" / "agents"
    for days in (100, 90, 80, 70, 60, 50):
        _write_backup(project_root, ".claude/agents/a.md", _stamp(days))
    newest = _write_backup(project_root, ".claude/agents/a.md", _stamp(0))

    pruned = prune_sync_backups(
        target_dir, project_root, SyncLog(), dry_run=False,
        max_age_days=30, max_per_source=3,
    )

    assert newest.exists()
    assert newest.name not in {Path(p).name for p in pruned}
    assert pruned  # older, over-threshold backups are still pruned


def test_prune_requires_both_thresholds(tmp_path: Path) -> None:
    """AC-09: prune only when age > max_age_days AND > max_per_source newer exist."""
    from scripts.lib.log import SyncLog
    project_root = tmp_path / "project"
    target_dir = project_root / ".claude" / "agents"

    # (a) Age threshold NOT exceeded: many recent backups survive.
    for days in (1, 2, 3, 4, 5, 6):
        _write_backup(project_root, ".claude/agents/recent.md", _stamp(days))

    # (b) Count threshold NOT exceeded: fewer than (> max_per_source) newer backups.
    _write_backup(project_root, ".claude/agents/few.md", _stamp(100))
    _write_backup(project_root, ".claude/agents/few.md", _stamp(90))

    # (c) Both thresholds exceeded for the oldest of five old siblings.
    many_stamps = [_stamp(days) for days in (100, 90, 80, 70, 60)]
    for stamp in many_stamps:
        _write_backup(project_root, ".claude/agents/many.md", stamp)

    # (d) Age boundary: exactly 30 days old is not > 30, 31 days is.
    boundary_stamps = [_stamp(days) for days in (31, 30, 29, 28, 27, 26)]
    for stamp in boundary_stamps:
        _write_backup(project_root, ".claude/agents/boundary.md", stamp)

    pruned = prune_sync_backups(
        target_dir, project_root, SyncLog(), dry_run=False,
        max_age_days=30, max_per_source=3,
    )

    pruned_names = {Path(p).name for p in pruned}
    assert pruned_names == {
        f"many.md.sync-backup-{many_stamps[0]}",
        f"boundary.md.sync-backup-{boundary_stamps[0]}",
    }
    assert _backup_count(target_dir) == 6 + 2 + 5 + 6 - 2


def test_prune_ignores_non_backup_names(tmp_path: Path) -> None:
    """AC-09: no name other than `*.sync-backup-*` is ever a candidate."""
    from scripts.lib.log import SyncLog
    project_root = tmp_path / "project"
    target_dir = project_root / ".claude" / "agents"
    _write(project_root, ".claude/agents/a.md", "generated")
    _write(project_root, ".claude/agents/notes.txt", "notes")
    _write(project_root, ".claude/agents/config.yaml", "key: value")

    pruned = prune_sync_backups(
        target_dir, project_root, SyncLog(), dry_run=False,
        max_age_days=30, max_per_source=3,
    )

    assert pruned == []
    assert (target_dir / "a.md").exists()
    assert (target_dir / "notes.txt").exists()
    assert (target_dir / "config.yaml").exists()


def test_prune_skips_unparsable_timestamp(tmp_path: Path) -> None:
    """AC-09: a `*.sync-backup-*` name with an unparsable timestamp is never pruned."""
    from scripts.lib.log import SyncLog
    project_root = tmp_path / "project"
    target_dir = project_root / ".claude" / "agents"
    # Force the count threshold: the unparsable sibling shares the source with
    # six old, parsable backups.
    for days in (100, 90, 80, 70, 60, 50):
        _write_backup(project_root, ".claude/agents/a.md", _stamp(days))
    unparsable = _write_backup(project_root, ".claude/agents/a.md", "not-a-timestamp")
    orphan = _write_backup(project_root, ".claude/agents/b.md", "garbage")

    pruned = prune_sync_backups(
        target_dir, project_root, SyncLog(), dry_run=False,
        max_age_days=30, max_per_source=3,
    )

    assert unparsable.exists()
    assert orphan.exists()
    assert unparsable.name not in {Path(p).name for p in pruned}
    assert orphan.name not in {Path(p).name for p in pruned}


def test_prune_default_policy_three_and_thirty(tmp_path: Path) -> None:
    """OQ-2: with max_per_source=3 and max_age_days=30 the newest four survive."""
    from scripts.lib.log import SyncLog
    project_root = tmp_path / "project"
    target_dir = project_root / ".claude" / "agents"
    stamps = {days: _stamp(days) for days in (100, 90, 80, 70, 60, 50, 1)}
    for stamp in stamps.values():
        _write_backup(project_root, ".claude/agents/a.md", stamp)

    pruned = prune_sync_backups(
        target_dir, project_root, SyncLog(), dry_run=False,
        max_age_days=30, max_per_source=3,
    )

    assert {Path(p).name for p in pruned} == {
        f"a.md.sync-backup-{stamps[100]}",
        f"a.md.sync-backup-{stamps[90]}",
        f"a.md.sync-backup-{stamps[80]}",
    }
    remaining = {p.name for p in target_dir.iterdir()}
    assert remaining == {
        f"a.md.sync-backup-{stamps[70]}",
        f"a.md.sync-backup-{stamps[60]}",
        f"a.md.sync-backup-{stamps[50]}",
        f"a.md.sync-backup-{stamps[1]}",
    }


def test_prune_fail_soft_when_dir_missing(tmp_path: Path) -> None:
    from scripts.lib.log import SyncLog
    project_root = tmp_path / "project"
    project_root.mkdir()

    pruned = prune_sync_backups(
        project_root / ".claude" / "agents", project_root, SyncLog(), dry_run=False,
        max_age_days=30, max_per_source=3,
    )

    assert pruned == []

