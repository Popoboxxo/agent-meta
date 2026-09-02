"""Regression tests for Wave 8 backup robustness (#582, #583, #586p5)."""

import json
import re
import sys
import zipfile
from pathlib import Path
from unittest import mock

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.backup import (  # noqa: E402
    _archive_name,
    _unique_archive_name,
    _zip_directory,
    create_backup,
    restore_backup,
)
from lib.log import SyncLog  # noqa: E402


# ---------------------------------------------------------------------------
# #582 -- timestamp collision
# ---------------------------------------------------------------------------

def test_archive_name_has_microsecond_precision():
    name = _archive_name()
    assert re.match(r"^agent-meta-backup_\d{8}_\d{6}_\d{6}$", name)


def test_unique_archive_name_avoids_collision(tmp_path, monkeypatch):
    fixed_name = "agent-meta-backup_20260101_120000_000000"
    monkeypatch.setattr("lib.backup._archive_name", lambda prefix="agent-meta-backup": fixed_name)
    (tmp_path / f"{fixed_name}.zip").touch()

    result = _unique_archive_name(tmp_path)
    assert result == f"{fixed_name}_2"
    assert not (tmp_path / f"{result}.zip").exists()


def test_unique_archive_name_no_collision_returns_plain_name(tmp_path):
    name = _unique_archive_name(tmp_path)
    assert not (tmp_path / f"{name}.zip").exists()


def test_create_backup_twice_in_same_process_produces_distinct_archives(tmp_path):
    project_root = tmp_path
    (project_root / ".meta-config").mkdir()
    (project_root / ".meta-config" / "project.yaml").write_text("roles: []\n", encoding="utf-8")
    log = SyncLog()

    r1 = create_backup(project_root, [], {}, {}, log, source_version="0.0.0-test")
    r2 = create_backup(project_root, [], {}, {}, log, source_version="0.0.0-test")

    assert r1["archive"] != r2["archive"]
    assert (project_root / r1["archive"]).exists()
    assert (project_root / r2["archive"]).exists()


# ---------------------------------------------------------------------------
# #583 -- restore error propagation
# ---------------------------------------------------------------------------

def test_restore_backup_config_restore_failure_propagates_to_result(tmp_path, monkeypatch):
    project_root = tmp_path
    archive_path = tmp_path / "backup.zip"
    manifest = {"providers": {}}
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr(".meta-config/project.yaml", "roles: []\n")

    def _raise_oserror(*_a, **_kw):
        raise OSError("simulated permission denied")

    monkeypatch.setattr(Path, "write_bytes", _raise_oserror)
    log = SyncLog()
    result = restore_backup(project_root, str(archive_path), provider_config={}, config={}, log=log)

    assert result["config_restored"] is False
    assert "config_restore_error" in result
    assert "OSError" in result["config_restore_error"]
    assert any("could not restore project.yaml" in e for e in log.errors)


def test_restore_backup_config_restore_success_has_no_error_field(tmp_path):
    project_root = tmp_path
    archive_path = tmp_path / "backup.zip"
    manifest = {"providers": {}}
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr(".meta-config/project.yaml", "roles: []\n")

    result = restore_backup(project_root, str(archive_path), provider_config={}, config={}, log=SyncLog())

    assert result["config_restored"] is True
    assert "config_restore_error" not in result


def test_restore_backup_provider_restore_failure_includes_error_type_and_is_logged(tmp_path):
    project_root = tmp_path
    archive_path = tmp_path / "backup.zip"
    manifest = {"providers": {"Claude": {"directory": ".claude/", "exists": True}}}
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        # Extraction matches on the *provider key* from the manifest
        # ("Claude"), not its directory value -- see restore_backup's
        # `matching` resolution.
        zf.writestr("Claude/settings.json", "{}")

    provider_config = {"Claude": {"agents_dir": ".claude/agents"}}
    log = SyncLog()

    with mock.patch("lib.backup.zipfile.ZipFile.extract", side_effect=OSError("simulated disk full")):
        result = restore_backup(
            project_root, str(archive_path), provider_config, config={}, log=log, providers=["Claude"],
        )

    prov = result["provider_results"]["Claude"]
    assert prov["restored"] is False
    assert "OSError" in prov["error"]
    assert any("failed to restore" in w for w in log.warnings)


# ---------------------------------------------------------------------------
# #586 point 5 -- backup zip creation must not touch the process CWD
# ---------------------------------------------------------------------------

def test_zip_directory_does_not_change_cwd(tmp_path, monkeypatch):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("hello", encoding="utf-8")
    (src / "sub").mkdir()
    (src / "sub" / "b.txt").write_text("world", encoding="utf-8")

    zip_path = tmp_path / "out.zip"

    def _boom(*_a, **_kw):
        raise AssertionError("os.chdir must never be called by _zip_directory")

    monkeypatch.setattr("os.chdir", _boom)
    _zip_directory(src, zip_path)

    with zipfile.ZipFile(zip_path) as zf:
        names = sorted(zf.namelist())
    assert names == ["a.txt", "sub/b.txt"]
