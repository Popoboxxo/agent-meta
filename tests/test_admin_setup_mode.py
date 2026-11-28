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
import urllib.error
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
        with mock.patch.object(admin_server.subprocess, "run") as m_run, \
                mock.patch.object(admin_server.subprocess, "Popen") as m_popen:
            result = executor.dry_run()
        assert result["success"] is False
        m_run.assert_not_called()
        m_popen.assert_not_called()

    def test_cleanup_preview_without_config_spawns_nothing(self, tmp_path):
        executor = admin_server.SyncExecutor(tmp_path)
        with mock.patch.object(admin_server.subprocess, "run") as m_run, \
                mock.patch.object(admin_server.subprocess, "Popen") as m_popen:
            result = executor.cleanup_preview()
        assert result["success"] is False
        assert result["error"] == "sync_preview_failed"
        m_run.assert_not_called()
        m_popen.assert_not_called()

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


# --------------------------------------------------------------------------- #
# Task 3: /api/setup/* endpoints + SyncExecutor.init_run
# --------------------------------------------------------------------------- #

_TOKEN = "setup-test-token"
_VALID = {
    "name": "demo-proj", "prefix": "dp", "providers": ["claude"],
    "git_platform": "GitHub",
}


def _first_provider() -> str:
    from lib.providers import load_providers_config
    return next(iter(load_providers_config(_REPO_ROOT)))


def _answers(**over) -> dict:
    data = dict(_VALID, providers=[_first_provider()])
    data.update(over)
    return data


def _req(port, path, body=None, *, token=None, origin=None, method=None, raw=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if origin:
        headers["Origin"] = origin
    data = raw if raw is not None else (None if body is None else json.dumps(body).encode())
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}", data=data, headers=headers,
        method=method or ("POST" if data is not None else "GET"),
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8") or "{}")


def _REPO_ROOT_COPY(tmp_path: Path) -> Path:
    """Project root without project.yaml; framework assets via ``.agent-meta`` symlink."""
    root = tmp_path / "proj"
    root.mkdir()
    (root / ".agent-meta").symlink_to(_REPO_ROOT, target_is_directory=True)
    return root


@pytest.fixture
def token_server():
    procs: list[subprocess.Popen] = []

    def _start(root: Path) -> int:
        port = _free_port()
        proc = subprocess.Popen(
            [sys.executable, str(_ADMIN_SERVER_PATH), "--root", str(root),
             "--port", str(port), "--no-viz", "--admin-token", _TOKEN],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        procs.append(proc)
        deadline = time.time() + 20
        while time.time() < deadline:
            if proc.poll() is not None:
                pytest.fail("server exited early")
            try:
                _req(port, "/api/health", token=_TOKEN)
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


def _cfg(root: Path) -> Path:
    return root / ".meta-config" / "project.yaml"


class TestSetupEndpoints:
    def test_options_requires_token_and_lists_values(self, token_server, tmp_path):
        port = token_server(_REPO_ROOT_COPY(tmp_path))
        assert _req(port, "/api/setup/options")[0] in (401, 403)
        status, body = _req(port, "/api/setup/options", token=_TOKEN)
        assert status == 200
        assert {"providers", "git_platforms", "dod_presets", "defaults"} <= set(body)
        assert "GitHub" in body["git_platforms"] and body["providers"]
        assert body["defaults"]["dod_preset"] in body["dod_presets"]

    def test_ac4_valid_answers_create_loadable_owner_only_config(self, token_server, tmp_path):
        root = _REPO_ROOT_COPY(tmp_path)
        port = token_server(root)
        status, body = _req(port, "/api/setup/config", _answers(), token=_TOKEN)
        assert status == 200, body
        assert body["success"] is True
        assert Path(body["path"]) == _cfg(root).resolve() or Path(body["path"]) == _cfg(root)
        from lib.config import load_config
        cfg = load_config(_cfg(root))
        assert cfg["project"]["name"] == "demo-proj"
        assert (_cfg(root).stat().st_mode & 0o777) == 0o600
        assert not list((root / ".meta-config").glob(".project.yaml.*.tmp"))
        _, mode = _req(port, "/api/mode", token=_TOKEN)
        assert mode["setup_required"] is False

    def test_ac6_invalid_answers_400_with_list_and_no_file(self, token_server, tmp_path):
        root = _REPO_ROOT_COPY(tmp_path)
        port = token_server(root)
        status, body = _req(port, "/api/setup/config",
                            {"name": "", "prefix": "!!", "providers": [], "git_platform": "x"},
                            token=_TOKEN)
        assert status == 400
        assert body["error"] == "bad_request"
        assert isinstance(body["detail"], list) and len(body["detail"]) >= 3
        assert not _cfg(root).exists()

    def test_non_object_body_400(self, token_server, tmp_path):
        root = _REPO_ROOT_COPY(tmp_path)
        port = token_server(root)
        status, body = _req(port, "/api/setup/config", [1, 2], token=_TOKEN)
        assert status == 400 and isinstance(body["detail"], list)
        assert not _cfg(root).exists()

    def test_ac7_existing_config_409_byte_identical(self, token_server, tmp_path):
        root = _REPO_ROOT_COPY(tmp_path)
        _cfg(root).parent.mkdir(exist_ok=True)
        _cfg(root).write_bytes(b"project:\n  name: keep\n")
        before = _cfg(root).read_bytes()
        port = token_server(root)
        status, body = _req(port, "/api/setup/config", _answers(), token=_TOKEN)
        assert status == 409 and body["error"] == "already_configured"
        assert _cfg(root).read_bytes() == before
        assert not list((root / ".meta-config").glob(".project.yaml.*.tmp"))

    def test_second_post_409(self, token_server, tmp_path):
        root = _REPO_ROOT_COPY(tmp_path)
        port = token_server(root)
        assert _req(port, "/api/setup/config", _answers(), token=_TOKEN)[0] == 200
        before = _cfg(root).read_bytes()
        assert _req(port, "/api/setup/config", _answers(name="other"), token=_TOKEN)[0] == 409
        assert _cfg(root).read_bytes() == before
        assert not list((root / ".meta-config").glob(".project.yaml.*.tmp"))

    def test_auth_and_origin(self, token_server, tmp_path):
        root = _REPO_ROOT_COPY(tmp_path)
        port = token_server(root)
        assert _req(port, "/api/setup/config", _answers())[0] in (401, 403)
        assert _req(port, "/api/setup/init-sync", {})[0] in (401, 403)
        status, _ = _req(port, "/api/setup/config", _answers(), token=_TOKEN,
                         origin="http://evil.example")
        assert status in (401, 403)
        assert not _cfg(root).exists()

    def test_target_path_not_from_body(self, token_server, tmp_path):
        root = _REPO_ROOT_COPY(tmp_path)
        port = token_server(root)
        evil = tmp_path / "evil.yaml"
        status, body = _req(port, "/api/setup/config",
                            _answers(path=str(evil), target="../x", root=str(evil)),
                            token=_TOKEN)
        assert status == 200
        assert not evil.exists()
        assert Path(body["path"]).name == "project.yaml"
        assert _cfg(root).exists()

    def test_oversized_body_413(self, token_server, tmp_path):
        root = _REPO_ROOT_COPY(tmp_path)
        port = token_server(root)
        big = b'{"name": "' + b"a" * (11 * 1024 * 1024) + b'"}'
        try:
            status, _ = _req(port, "/api/setup/config", token=_TOKEN, raw=big)
        except (urllib.error.URLError, ConnectionError, OSError):
            status = 413  # server closed the socket before the body was sent
        assert status == 413
        assert not _cfg(root).exists()

    def test_init_sync_without_config_409(self, token_server, tmp_path):
        root = _REPO_ROOT_COPY(tmp_path)
        port = token_server(root)
        status, body = _req(port, "/api/setup/init-sync", {}, token=_TOKEN)
        assert status == 409
        assert body["error"] == "setup_required"
        assert not (root / ".meta-viz" / "sync-status.json").exists()


class TestInitRun:
    def test_ac9_init_run_argv_is_fixed(self, tmp_path):
        evil = "x; rm -rf / $(id) `id` | &"
        executor = admin_server.SyncExecutor(tmp_path)
        executor.sync_script = Path(__file__)
        _cfg(tmp_path).parent.mkdir()
        _cfg(tmp_path).write_text(f"project:\n  name: '{evil}'\n", encoding="utf-8")
        fake = mock.Mock(returncode=0, stdout="ok", stderr="")
        with mock.patch.object(admin_server.subprocess, "run", return_value=fake) as m_run:
            result = executor.init_run()
        assert result["success"] is True
        cmd = m_run.call_args.args[0]
        assert cmd[1:] == [str(Path(__file__)), "--config",
                           str(tmp_path.resolve() / ".meta-config" / "project.yaml"), "--init"]
        assert m_run.call_args.kwargs.get("shell") is not True

    def test_ac9_evil_form_values_never_reach_argv(self, token_server, tmp_path):
        evil = "a; touch /tmp/pwn $(id) `id` | &"
        root = _REPO_ROOT_COPY(tmp_path)
        port = token_server(root)
        status, _ = _req(port, "/api/setup/config",
                         _answers(name=evil, short=evil, git_remote=evil,
                                  test_commands=evil, dev_commands=evil),
                         token=_TOKEN)
        assert status == 200
        assert evil in _cfg(root).read_text(encoding="utf-8")  # values did land in the file
        executor = admin_server.SyncExecutor(root)
        fake = mock.Mock(returncode=0, stdout="ok", stderr="")
        with mock.patch.object(admin_server.subprocess, "run", return_value=fake) as m_run:
            executor.init_run()
        cmd = m_run.call_args.args[0]
        assert "--init" in cmd
        assert "touch" not in " ".join(cmd) and evil not in " ".join(cmd)
        assert cmd[2:] == ["--config", str(root.resolve() / ".meta-config" / "project.yaml"), "--init"]
        assert not m_run.call_args.kwargs.get("shell")
        assert "input" not in m_run.call_args.kwargs
        env = m_run.call_args.kwargs.get("env") or {}
        assert not any(evil in str(v) for v in env.values())

    def test_publish_create_only_link_fallback(self, tmp_path):
        import errno as _errno
        tmp = tmp_path / "src.tmp"
        tmp.write_bytes(b"data: 1\n")
        target = tmp_path / "project.yaml"
        with mock.patch.object(admin_server.os, "link",
                               side_effect=OSError(_errno.EPERM, "no links")):
            admin_server._publish_create_only(tmp, target)
        assert target.read_bytes() == b"data: 1\n"
        assert (target.stat().st_mode & 0o777) == 0o600
        with mock.patch.object(admin_server.os, "link",
                               side_effect=OSError(_errno.EXDEV, "xdev")):
            with pytest.raises(FileExistsError):
                admin_server._publish_create_only(tmp, target)
        with mock.patch.object(admin_server.os, "link",
                               side_effect=OSError(_errno.EIO, "io")):
            with pytest.raises(OSError):
                admin_server._publish_create_only(tmp, tmp_path / "other.yaml")

    def test_ac8_init_sync_real_run(self, token_server, tmp_path):
        root = _REPO_ROOT_COPY(tmp_path)
        port = token_server(root)
        assert _req(port, "/api/setup/config", _answers(), token=_TOKEN)[0] == 200
        status, body = _req(port, "/api/setup/init-sync", {}, token=_TOKEN)
        assert status == 200, body
        assert body["returncode"] == 0, body["output"][-2000:]
        assert body["success"] is True
        assert (root / "CLAUDE.md").exists() or (root / ".claude" / "agents").is_dir()
