"""Unit tests for the shared managed-index helper (spec IC-01).

Covers the two new safety semantics introduced by the stale-role-cleanup spec
(``SPEC-STALE-ROLE-CLEANUP-2026-09-13``):

- ``bootstrap_previously_managed``: index-first, fail-closed predicate/marker
  bootstrap when the index is absent or unreadable (AC-03/AC-04/AC-05/AC-23).
- ``cleanup_stale_managed_files(backup=True)``: backup-first delete with a
  fail-soft per-file contract and an additive ``list[str]`` return value
  (AC-08, F-11).
"""

import re
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib import rule_index as ri  # noqa: E402


class _LogRecorder:
    """Duck-typed SyncLog stand-in recording action/warning calls."""

    def __init__(self):
        self.actions = []
        self.warnings = []

    def action(self, tag, target, source):
        self.actions.append((tag, target, source))

    def warning(self, message):
        self.warnings.append(message)


@pytest.fixture()
def project_root(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    return root


def _provenance_predicate(path, text):
    return "agent-meta-provenance" in text


# --- bootstrap_previously_managed -------------------------------------------


def test_bootstrap_content_predicate_adopts_only_matching(tmp_path):
    """An absent index adopts only glob matches that pass the predicate (IC-02/IC-04)."""
    target = tmp_path / "agents"
    target.mkdir()
    index = target / ".agent-meta-managed"
    (target / "managed.md").write_text(
        "<!-- agent-meta-provenance: 0-external/foo@abc -->\n", encoding="utf-8"
    )
    (target / "foreign.md").write_text("user-authored\n", encoding="utf-8")

    adopted = ri.bootstrap_previously_managed(
        target, index, "*.md", content_predicate=_provenance_predicate
    )

    assert adopted == {"managed.md"}


def test_bootstrap_missing_index_never_adopts_without_predicate(tmp_path):
    """No index and no provenance signal is fail-closed: adopt nothing (AC-03)."""
    target = tmp_path / "agents"
    target.mkdir()
    index = target / ".agent-meta-managed"
    (target / "a.md").write_text("user a\n", encoding="utf-8")
    (target / "b.md").write_text("user b\n", encoding="utf-8")

    adopted = ri.bootstrap_previously_managed(target, index, "*.md")

    assert adopted == set()


def test_bootstrap_existing_empty_index_wins_over_predicate(tmp_path):
    """A readable-but-empty index wins over a permissive predicate (AC-04)."""
    target = tmp_path / "agents"
    target.mkdir()
    index = target / ".agent-meta-managed"
    index.write_text("", encoding="utf-8")
    (target / "managed.md").write_text("provenance\n", encoding="utf-8")

    adopted = ri.bootstrap_previously_managed(
        target, index, "*.md", content_predicate=lambda path, text: True
    )

    assert adopted == set()


def test_bootstrap_corrupt_index_falls_back_to_predicate(tmp_path):
    """An unreadable index does not propagate; predicate bootstrap stays fail-closed (AC-05)."""
    target = tmp_path / "agents"
    target.mkdir()
    index = target / ".agent-meta-managed"
    index.write_bytes(b"\xff\xfe\x00 not utf-8 \xff")
    (target / "managed.md").write_text(
        "<!-- agent-meta-provenance: 0-external/foo@abc -->\n", encoding="utf-8"
    )
    (target / "foreign.md").write_text("user-authored\n", encoding="utf-8")

    adopted = ri.bootstrap_previously_managed(
        target, index, "*.md", content_predicate=_provenance_predicate
    )

    assert adopted == {"managed.md"}


def test_bootstrap_missing_index_marker_still_adopts_matching(tmp_path):
    """Backward compatibility: the legacy content_marker path is preserved for existing callers."""
    target = tmp_path / "rules"
    target.mkdir()
    index = target / ".agent-meta-managed"
    marker = "nicht manuell bearbeiten"
    (target / "mcp-a.md").write_text(f"footer: {marker}\n", encoding="utf-8")
    (target / "mcp-b.md").write_text("handwritten\n", encoding="utf-8")

    adopted = ri.bootstrap_previously_managed(
        target, index, "mcp-*.md", content_marker=marker
    )

    assert adopted == {"mcp-a.md"}


def test_bootstrap_missing_index_false_predicate_adopts_nothing(tmp_path):
    """A caller with no provenance marker passes a false predicate -> adopt nothing (AC-23)."""
    target = tmp_path / "prompts"
    target.mkdir()
    index = target / ".agent-meta-managed"
    (target / "prompt-a.md").write_text("prompt content\n", encoding="utf-8")

    adopted = ri.bootstrap_previously_managed(
        target, index, "*.md", content_predicate=lambda path, text: False
    )

    assert adopted == set()


# --- cleanup_stale_managed_files --------------------------------------------


def test_cleanup_writes_backup_before_unlink(project_root):
    """A backup sibling with the pre-delete content exists after the unlink (AC-08)."""
    target = project_root / "agents"
    target.mkdir()
    stale = target / "x.md"
    stale.write_text("pre-delete content\n", encoding="utf-8")
    log = _LogRecorder()

    backups = ri.cleanup_stale_managed_files(
        target, project_root, {"x.md"}, set(), log,
        dry_run=False, reason="role removed from config", backup=True,
    )

    assert not stale.exists()
    assert log.actions == [("DELETE", "agents/x.md", "role removed from config")]
    assert len(backups) == 1
    backup_path = project_root / backups[0]
    assert backup_path.name.startswith("x.md.sync-backup-")
    assert backup_path.read_text(encoding="utf-8") == "pre-delete content\n"
    timestamp = backup_path.name[len("x.md.sync-backup-"):]
    assert re.fullmatch(r"\d{8}-\d{6}", timestamp)


def test_cleanup_dry_run_writes_no_backup_but_reports_path(project_root):
    """dry_run mutates nothing but still reports the would-be backup path (AC-08)."""
    target = project_root / "agents"
    target.mkdir()
    stale = target / "x.md"
    stale.write_text("pre-delete content\n", encoding="utf-8")
    log = _LogRecorder()

    backups = ri.cleanup_stale_managed_files(
        target, project_root, {"x.md"}, set(), log,
        dry_run=True, reason="role removed from config", backup=True,
    )

    assert stale.exists()
    assert stale.read_text(encoding="utf-8") == "pre-delete content\n"
    assert list(target.glob("*.sync-backup-*")) == []
    assert len(backups) == 1
    assert backups[0].startswith("agents/x.md.sync-backup-")
    timestamp = backups[0].rsplit("sync-backup-", 1)[1]
    assert re.fullmatch(r"\d{8}-\d{6}", timestamp)


def test_cleanup_backup_failure_prevents_unlink(project_root, monkeypatch):
    """A failed backup write is fail-soft: warn and leave the file in place (IC-01)."""
    target = project_root / "agents"
    target.mkdir()
    stale = target / "x.md"
    stale.write_text("pre-delete content\n", encoding="utf-8")
    log = _LogRecorder()

    real_write_text = Path.write_text

    def failing_write_text(self, *args, **kwargs):
        if ".sync-backup-" in self.name:
            raise OSError("backup device full")
        return real_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", failing_write_text)

    backups = ri.cleanup_stale_managed_files(
        target, project_root, {"x.md"}, set(), log,
        dry_run=False, reason="role removed from config", backup=True,
    )

    assert backups == []
    assert stale.exists()
    assert stale.read_text(encoding="utf-8") == "pre-delete content\n"
    assert any("backup" in warning for warning in log.warnings)


def test_cleanup_returns_backup_paths(project_root):
    """The return value is the project-relative posix backup list, [] when backup=False (F-11)."""
    target = project_root / "agents"
    target.mkdir()
    (target / "a.md").write_text("a\n", encoding="utf-8")
    (target / "b.md").write_text("b\n", encoding="utf-8")
    log = _LogRecorder()

    backups = ri.cleanup_stale_managed_files(
        target, project_root, {"a.md", "b.md"}, set(), log,
        dry_run=False, reason="role removed from config", backup=True,
    )

    assert len(backups) == 2
    assert backups[0].startswith("agents/a.md.sync-backup-")
    assert backups[1].startswith("agents/b.md.sync-backup-")
    assert all((project_root / path).exists() for path in backups)

    other = project_root / "no-backup"
    other.mkdir()
    (other / "c.md").write_text("c\n", encoding="utf-8")
    assert ri.cleanup_stale_managed_files(
        other, project_root, {"c.md"}, set(), log,
        dry_run=False, reason="role removed from config", backup=False,
    ) == []
    assert not (other / "c.md").exists()


# --- write_managed_index ----------------------------------------------------


def test_write_managed_index_writes_empty_file(project_root):
    """An empty managed set is written as a 0-byte index; dry_run is a no-op (AC-04)."""
    index = project_root / "agents" / ".agent-meta-managed"
    ri.write_managed_index(index, set(), dry_run=False)

    assert index.exists()
    assert index.read_text(encoding="utf-8") == ""

    dry_index = project_root / "agents" / ".agent-meta-managed-dry"
    ri.write_managed_index(dry_index, {"a.md"}, dry_run=True)
    assert not dry_index.exists()
