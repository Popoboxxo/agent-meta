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
