"""Tests for external skills management."""

from pathlib import Path

from scripts.lib.skills import _read_skills_managed_index, _write_skills_managed_index


def test_read_skills_managed_index_missing_file_returns_empty(tmp_path):
    assert _read_skills_managed_index(tmp_path / ".claude" / "skills") == set()


def test_write_then_read_skills_managed_index_roundtrip(tmp_path):
    skills_dir = tmp_path / ".claude" / "skills"
    _write_skills_managed_index(skills_dir, {"reqogniloom-change-manager", "graphify"}, dry_run=False)
    assert _read_skills_managed_index(skills_dir) == {"reqogniloom-change-manager", "graphify"}


def test_write_skills_managed_index_dry_run_does_not_write(tmp_path):
    skills_dir = tmp_path / ".claude" / "skills"
    _write_skills_managed_index(skills_dir, {"graphify"}, dry_run=True)
    assert not (skills_dir / ".agent-meta-managed").exists()


# ---------------------------------------------------------------------------
# universe= merge mode — two independent writers share the same index file
# (external-skill sync vs. rules.py's 'channel: skill' lazy-rules mechanism).
# ---------------------------------------------------------------------------

def test_write_skills_managed_index_merge_preserves_other_callers_entries(tmp_path):
    skills_dir = tmp_path / ".claude" / "skills"
    # Caller A (e.g. rules.py) writes its own entries first, full-replace mode.
    _write_skills_managed_index(skills_dir, {"sync-interface"}, dry_run=False)
    # Caller B (external-skill sync) writes in merge mode, scoped to its own
    # universe of possible skill names — must not wipe out caller A's entry.
    _write_skills_managed_index(
        skills_dir, {"graphify"}, dry_run=False, universe={"graphify", "reqogniloom-change-manager"}
    )
    assert _read_skills_managed_index(skills_dir) == {"sync-interface", "graphify"}


def test_write_skills_managed_index_merge_removes_only_stale_entries_within_universe(tmp_path):
    skills_dir = tmp_path / ".claude" / "skills"
    _write_skills_managed_index(skills_dir, {"sync-interface"}, dry_run=False)
    _write_skills_managed_index(
        skills_dir, {"graphify"}, dry_run=False, universe={"graphify", "reqogniloom-change-manager"}
    )
    # graphify is deactivated (falls out of now_managed) but "reqogniloom-
    # change-manager" was never present, and "sync-interface" belongs to a
    # different universe entirely — only graphify should ever leave.
    _write_skills_managed_index(
        skills_dir, set(), dry_run=False, universe={"graphify", "reqogniloom-change-manager"}
    )
    assert _read_skills_managed_index(skills_dir) == {"sync-interface"}


def test_write_skills_managed_index_merge_empty_result_removes_file(tmp_path):
    skills_dir = tmp_path / ".claude" / "skills"
    _write_skills_managed_index(skills_dir, {"graphify"}, dry_run=False, universe={"graphify"})
    assert (skills_dir / ".agent-meta-managed").exists()
    _write_skills_managed_index(skills_dir, set(), dry_run=False, universe={"graphify"})
    assert not (skills_dir / ".agent-meta-managed").exists()
