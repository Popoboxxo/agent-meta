"""Tests for admin setup mode (Task 2): ``setup_required`` + sync guard.

AC-1: server starts without project.yaml (--no-viz), /api/health 200,
      /api/mode reports ``setup_required: true`` (resolves OQ-1).
AC-2: with project.yaml ``setup_required`` is false, other fields unchanged.
AC-3: POST /api/sync/run without config spawns no subprocess.
"""

from __future__ import annotations

import importlib.util
import json
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from unittest import mock

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_ADMIN_SERVER_PATH = _REPO_ROOT / "scripts" / "admin-server.py"
sys.path.insert(0, str(_REPO_ROOT / "scripts"))


def _load_admin_server():
    spec = importlib.util.spec_from_file_location("admin_server_setup", _ADMIN_SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["admin_server_setup"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


admin_server = _load_admin_server()


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _get(port: int, path: str) -> tuple[int, dict]:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


@pytest.fixture
def run_server():
    procs: list[subprocess.Popen] = []

    def _start(root: Path) -> int:
        port = _free_port()
        proc = subprocess.Popen(
            [sys.executable, str(_ADMIN_SERVER_PATH), "--root", str(root),
             "--port", str(port), "--no-viz"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        procs.append(proc)
        deadline = time.time() + 20
        while time.time() < deadline:
            if proc.poll() is not None:
                out = proc.stdout.read().decode("utf-8", "replace") if proc.stdout else ""
                pytest.fail(f"server exited early rc={proc.returncode}: {out}")
            try:
                _get(port, "/api/health")
                return port
            except OSError:
                time.sleep(0.2)
        pytest.fail("server did not become healthy")

    yield _start
    for proc in procs:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


class TestSetupRequiredMode:
    def test_ac1_server_starts_without_project_yaml(self, tmp_path, run_server):
        port = run_server(tmp_path)
        status, _ = _get(port, "/api/health")
        assert status == 200
        status, mode = _get(port, "/api/mode")
        assert status == 200
        assert mode["setup_required"] is True

    def test_ac2_with_project_yaml_setup_not_required(self, tmp_path, run_server):
        (tmp_path / ".meta-config").mkdir()
        (tmp_path / ".meta-config" / "project.yaml").write_text(
            "project:\n  name: demo\n", encoding="utf-8"
        )
        port = run_server(tmp_path)
        _, mode = _get(port, "/api/mode")
        assert mode["setup_required"] is False
        assert {"mode", "root", "allowed_keys"} <= set(mode)
        assert mode["root"] == str(tmp_path.resolve()) or mode["root"] == str(tmp_path)


class TestSyncExecutorGuard:
    def test_ac3_run_without_config_spawns_nothing(self, tmp_path):
        executor = admin_server.SyncExecutor(tmp_path)
        with mock.patch.object(admin_server.subprocess, "run") as m_run, \
                mock.patch.object(admin_server.subprocess, "Popen") as m_popen:
            result = executor.run()
        assert result == {"success": False, "output": "project.yaml missing", "returncode": -1}
        m_run.assert_not_called()
        m_popen.assert_not_called()

    def test_ac3_dry_run_without_config_spawns_nothing(self, tmp_path):
        executor = admin_server.SyncExecutor(tmp_path)
        with mock.patch.object(admin_server.subprocess, "run") as m_run:
            result = executor.dry_run()
        assert result["success"] is False
        m_run.assert_not_called()

    def test_ac3_post_sync_run_route_returns_200(self, tmp_path, run_server):
        port = run_server(tmp_path)
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/sync/run", data=b"{}", method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            assert resp.status == 200
            body = json.loads(resp.read().decode("utf-8"))
        assert body["success"] is False
        assert body["output"] == "project.yaml missing"

    def test_run_with_config_still_spawns(self, tmp_path):
        (tmp_path / ".meta-config").mkdir()
        (tmp_path / ".meta-config" / "project.yaml").write_text("project: {}\n", encoding="utf-8")
        executor = admin_server.SyncExecutor(tmp_path)
        executor.sync_script = Path(__file__)  # exists
        fake = mock.Mock(returncode=0, stdout="ok", stderr="")
        with mock.patch.object(admin_server.subprocess, "run", return_value=fake) as m_run:
            result = executor.run()
        m_run.assert_called_once()
        assert result["success"] is True
