"""Real start/status/stop smoke of ``admin-server.py`` (#1189, AC-1, plan gate 4).

Runs the CLI as a subprocess against a throwaway project under ``.tmp`` with the
framework pin (TMPDIR/TEMP/TMP = <project>/.tmp) in the environment. Loopback
only, free port picked per test, ``--no-viz``; independent of ``socket_enabled``.
The server is always stopped in ``finally``.

Run: python -m pytest tests/test_admin_server_lifecycle_smoke.py -q
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tests.timeouts import SYNC_VALIDATE_TIMEOUT  # noqa: E402

_SCRIPT = REPO_ROOT / "scripts" / "admin-server.py"
_PID_FILE = Path(".meta-viz") / ".admin-server-pid"
_VALID_CONFIG = (
    "project:\n  name: smoke\n  prefix: sm\n"
    "repo_containment:\n  tmp-sink:\n    enabled: true\n    path: .tmp\n"
    "    system-temp-exception:\n      enabled: true\n"
    "      pytest-basetemp: true\n      toolchain-caches: false\n"
    "      reason: smoke default\n"
)


def _free_port() -> int:
    # Picked in a child interpreter: pytest-socket only guards this process,
    # so the test needs no ``socket_enabled`` marker.
    code = (
        "import socket; s = socket.socket(); s.bind(('127.0.0.1', 0)); "
        "print(s.getsockname()[1])"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=30, check=True,
    )
    return int(out.stdout.strip())


@pytest.fixture
def project():
    base = REPO_ROOT / ".tmp"
    base.mkdir(exist_ok=True)
    root = base / f"admin-smoke-{uuid.uuid4().hex[:8]}"
    (root / ".meta-config").mkdir(parents=True)
    (root / ".tmp").mkdir()
    (root / ".meta-config" / "project.yaml").write_text(_VALID_CONFIG, encoding="utf-8")
    try:
        yield root
    finally:
        # Last-resort kill so a failed assertion never leaks a server.
        pid_file = root / _PID_FILE
        if pid_file.exists():
            try:
                os.kill(int(pid_file.read_text(encoding="utf-8").strip()), signal.SIGKILL)
            except (OSError, ValueError):
                pass
        shutil.rmtree(root, ignore_errors=True)


def _cli(root: Path, command: str, port: int, temp: Path | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    for key in ("TMPDIR", "TEMP", "TMP"):
        env[key] = os.path.realpath(temp or root / ".tmp")
    return subprocess.run(
        [sys.executable, str(_SCRIPT), command, "--root", str(root),
         "--host", "127.0.0.1", "--port", str(port), "--no-viz"],
        cwd=str(REPO_ROOT), env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=SYNC_VALIDATE_TIMEOUT,
    )


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signals/process model")
def test_start_status_stop_lifecycle(project):
    port = _free_port()
    try:
        started = _cli(project, "start", port)
        assert started.returncode == 0, started.stdout + started.stderr
        assert "Traceback" not in started.stdout + started.stderr
        assert (project / _PID_FILE).exists()

        status = _cli(project, "status", port)
        assert "Admin UI" in status.stdout and "RUNNING" in status.stdout, status.stdout
    finally:
        stopped = _cli(project, "stop", port)
    assert stopped.returncode == 0, stopped.stdout + stopped.stderr
    assert not (project / _PID_FILE).exists()
    assert "STOPPED" in _cli(project, "status", port).stdout


def test_start_with_broken_config_exits_one_without_traceback(project):
    (project / ".meta-config" / "project.yaml").write_text("project: [unclosed\n", encoding="utf-8")
    port = _free_port()
    try:
        result = _cli(project, "start", port)
    finally:
        _cli(project, "stop", port)
    out = result.stdout + result.stderr
    assert result.returncode == 1, out
    assert "tmp-sink pin unavailable" in out, out
    assert "Traceback" not in out, out
    assert not (project / _PID_FILE).exists()


def test_start_fails_when_user_temp_points_into_project_root(project):
    # AK5: the system-temp-exception check must still fire for a truly broken
    # setup (user TMPDIR inside the root but not the framework sink).
    bad = project / "inroot-temp"
    bad.mkdir()
    port = _free_port()
    try:
        result = _cli(project, "start", port, temp=bad)
    finally:
        _cli(project, "stop", port)
    out = result.stdout + result.stderr
    assert result.returncode == 1, out
    assert "inside the project root" in out, out
    assert not (project / _PID_FILE).exists()
