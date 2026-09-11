"""End-to-end: a real `python scripts/sync.py` run detects a manual edit
made between two syncs, warns about it, and a subsequent sync with the
edited path allowlisted produces no warning."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SYNC_PY = _REPO_ROOT / "scripts" / "sync.py"


def _run_sync(project_root: Path, *extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SYNC_PY), "--config", str(project_root / ".meta-config" / "project.yaml"), *extra_args],
        capture_output=True, text=True, cwd=str(project_root),
    )


def _write_minimal_project_yaml(project_root: Path) -> None:
    meta = project_root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "project.yaml").write_text(
        "ai-providers: [Claude]\n"
        "dod-preset: rapid-prototyping\n"
        "roles: [developer]\n"
        "project: {name: e2e-drift-test, prefix: e2e, short: e2e-drift}\n"
        "variables: {PROJECT_NAME: e2e-drift-test}\n",
        encoding="utf-8",
    )


def test_manual_edit_produces_warning_on_next_sync(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write_minimal_project_yaml(project_root)

    first = _run_sync(project_root)
    assert first.returncode == 0, first.stderr

    developer_md = project_root / ".claude" / "agents" / "developer.md"
    assert developer_md.is_file()
    developer_md.write_text(developer_md.read_text(encoding="utf-8") + "\n<!-- hand edit -->\n", encoding="utf-8")

    second = _run_sync(project_root)
    assert "generated-file-drift" in second.stderr, second.stderr
    assert ".claude/agents/developer.md" in second.stderr


def test_allowlisted_edit_produces_no_warning(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write_minimal_project_yaml(project_root)
    _run_sync(project_root)

    developer_md = project_root / ".claude" / "agents" / "developer.md"
    developer_md.write_text(developer_md.read_text(encoding="utf-8") + "\n<!-- hand edit -->\n", encoding="utf-8")

    meta = project_root / ".meta-config"
    (meta / "drift-allowlist.yaml").write_text(
        "allow-edits:\n  - .claude/agents/developer.md\n", encoding="utf-8",
    )

    second = _run_sync(project_root)
    assert "generated-file-drift" not in second.stderr, second.stderr


def test_manual_edit_creates_backup_with_pre_overwrite_content(tmp_path: Path) -> None:
    """Issue #734: the sync that overwrites a drifted file first drops a
    `.sync-backup-<ts>` sibling holding exactly the hand-edited content."""
    project_root = tmp_path / "project"
    _write_minimal_project_yaml(project_root)

    first = _run_sync(project_root)
    assert first.returncode == 0, first.stderr

    developer_md = project_root / ".claude" / "agents" / "developer.md"
    edited = developer_md.read_text(encoding="utf-8") + "\n<!-- hand edit -->\n"
    developer_md.write_text(edited, encoding="utf-8")

    second = _run_sync(project_root)
    assert second.returncode == 0, second.stderr

    backups = list((project_root / ".claude" / "agents").glob("developer.md.sync-backup-*"))
    assert len(backups) == 1, second.stderr
    assert backups[0].read_text(encoding="utf-8") == edited


def test_no_drift_creates_no_backup(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write_minimal_project_yaml(project_root)

    assert _run_sync(project_root).returncode == 0
    second = _run_sync(project_root)
    assert second.returncode == 0, second.stderr

    assert list((project_root / ".claude" / "agents").glob("*.sync-backup-*")) == []


def test_dry_run_warns_about_drift_but_writes_no_backup(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write_minimal_project_yaml(project_root)
    _run_sync(project_root)

    developer_md = project_root / ".claude" / "agents" / "developer.md"
    developer_md.write_text(
        developer_md.read_text(encoding="utf-8") + "\n<!-- hand edit -->\n", encoding="utf-8",
    )

    dry = _run_sync(project_root, "--dry-run")
    assert dry.returncode == 0, dry.stderr
    assert "generated-file-drift" in dry.stderr, dry.stderr
    assert list(project_root.rglob("*.sync-backup-*")) == []

