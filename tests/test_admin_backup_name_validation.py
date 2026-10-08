"""SR-D-01: the backup delete/restore HTTP handlers accept only bare archive names.

An absolute path or ``../`` traversal in ``archive_name`` must be rejected with
HTTP 400 before ``lib.backup.delete_backup``/``restore_backup`` is reached. The
``Path(archive_name)`` fallback in ``lib/backup.py`` stays untouched for the CLI.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "admin_server_backup_name_validation", REPO_ROOT / "scripts" / "admin-server.py"
)
admin_server = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(admin_server)

import lib.backup as backup_lib  # noqa: E402

BAD_REQUEST = {"error": "bad_request", "detail": "invalid archive name"}


@pytest.fixture()
def backup_mocks(monkeypatch: pytest.MonkeyPatch) -> dict[str, mock.Mock]:
    cls = admin_server.AdminRequestHandler
    monkeypatch.setattr(cls, "root", REPO_ROOT, raising=False)
    config_manager = mock.Mock()
    config_manager.read.return_value = {}
    monkeypatch.setattr(cls, "config_manager", config_manager, raising=False)
    mocks = {
        "delete": mock.Mock(return_value={"deleted": True}),
        "restore": mock.Mock(return_value={"restored": True}),
    }
    monkeypatch.setattr(backup_lib, "delete_backup", mocks["delete"])
    monkeypatch.setattr(backup_lib, "restore_backup", mocks["restore"])
    return mocks


def _make_handler(path: str = "/", body: Any = None) -> tuple[Any, dict]:
    handler = admin_server.AdminRequestHandler.__new__(admin_server.AdminRequestHandler)
    raw = json.dumps(body if body is not None else {}).encode("utf-8")
    handler.path = path
    handler.headers = {"Content-Length": str(len(raw))}
    handler.rfile = io.BytesIO(raw)
    captured: dict = {}

    def _send_json(payload, status=200, **kwargs):  # noqa: ANN001
        captured["payload"] = payload
        captured["status"] = status

    handler._send_json = _send_json
    return handler, captured


def _victim(tmp_path: Path) -> Path:
    victim = tmp_path / "outside" / "victim.txt"
    victim.parent.mkdir()
    victim.write_text("keep me", encoding="utf-8")
    return victim


def test_delete_absolute_path_rejected(tmp_path, backup_mocks):
    victim = _victim(tmp_path)
    handler, captured = _make_handler(f"/api/backups/{victim}")
    handler._dispatch_delete()
    assert captured["status"] == 400
    assert captured["payload"] == BAD_REQUEST
    assert victim.exists()
    backup_mocks["delete"].assert_not_called()


def test_delete_traversal_rejected(tmp_path, backup_mocks):
    victim = _victim(tmp_path)
    handler, captured = _make_handler("/api/backups/../../outside/victim.txt")
    handler._dispatch_delete()
    assert captured["status"] == 400
    assert captured["payload"] == BAD_REQUEST
    assert victim.exists()
    backup_mocks["delete"].assert_not_called()


def test_delete_real_backup_dir_untouched_by_absolute_name(tmp_path, monkeypatch):
    """No mocks on delete_backup: the real function must never see the path."""
    victim = _victim(tmp_path)
    cls = admin_server.AdminRequestHandler
    monkeypatch.setattr(cls, "root", tmp_path, raising=False)
    config_manager = mock.Mock()
    config_manager.read.return_value = {}
    monkeypatch.setattr(cls, "config_manager", config_manager, raising=False)
    handler, captured = _make_handler(f"/api/backups/{victim}")
    handler._dispatch_delete()
    assert captured["status"] == 400
    assert victim.exists()


@pytest.mark.parametrize("name", ["/abs/x.zip", "../x.zip", ".", "..", "a/b.zip", "x.txt"])
def test_restore_invalid_name_rejected(backup_mocks, name):
    handler, captured = _make_handler(body={"archive_name": name})
    handler._handle_restore_backup()
    assert captured["status"] == 400
    assert captured["payload"] == BAD_REQUEST
    backup_mocks["restore"].assert_not_called()


@pytest.mark.parametrize("name", ["..", "."])
def test_delete_dot_names_rejected(backup_mocks, name):
    handler, captured = _make_handler()
    handler._handle_delete_backup(name)
    assert captured["status"] == 400
    backup_mocks["delete"].assert_not_called()


def test_delete_bare_name_reaches_backend(backup_mocks):
    handler, captured = _make_handler("/api/backups/agent-meta-backup-20261007.zip")
    handler._dispatch_delete()
    assert captured["status"] == 200
    assert backup_mocks["delete"].call_args.args[1] == "agent-meta-backup-20261007.zip"


def test_restore_bare_name_reaches_backend(backup_mocks):
    handler, captured = _make_handler(
        body={"archive_name": "agent-meta-backup-20261007.zip"}
    )
    with mock.patch("lib.providers.load_providers_config", return_value={}):
        handler._handle_restore_backup()
    assert captured["status"] == 200
    assert backup_mocks["restore"].call_args.args[1] == "agent-meta-backup-20261007.zip"


def test_is_bare_backup_name():
    ok = admin_server._is_bare_backup_name
    assert ok("agent-meta-backup-20261007.zip")
    assert ok("a_b.c-d.zip")
    for bad in ("", ".", "..", "/x.zip", "../x.zip", "a/b.zip", "a\\b.zip", "x.zip\n", "x.txt"):
        assert not ok(bad), bad
