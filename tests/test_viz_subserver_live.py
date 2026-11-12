"""Live subprocess test for the viz sub-server controls (#317)."""
import importlib.util
import socket
import sys
import time
import urllib.request
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))


def _load_admin_server():
    spec = importlib.util.spec_from_file_location(
        "admin_server", _PROJECT_ROOT / "scripts" / "admin-server.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["admin_server"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


admin_server = _load_admin_server()
AdminRequestHandler = admin_server.AdminRequestHandler


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _loopback(url):
    # Server binds 127.0.0.1 only; pin the host so "localhost" -> ::1 is never tried.
    return url.replace("//localhost:", "//127.0.0.1:")


def _wait_http(url, timeout=15):
    url = _loopback(url)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return True
        except OSError:
            time.sleep(0.2)
    return False


@pytest.fixture
def viz_root(socket_enabled, tmp_path):
    port = _free_port()
    # viz-report.py serves docs/ui/live-dashboard.html from <root>/docs
    for name in ("scripts", "docs"):
        (tmp_path / name).symlink_to(_PROJECT_ROOT / name)
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        'agent-meta-version: "2.0.0-beta.1"\n'
        "ai-providers: [Claude]\n"
        "dod-preset: rapid-prototyping\n"
        "variables:\n  PROJECT_NAME: viz\n  PROJECT_PREFIX: vz\n"
        f"viz:\n  server:\n    port: {port}\n    timeout_sec: 60\n",
        encoding="utf-8",
    )
    yield tmp_path, port
    admin_server.VizManager(tmp_path).stop_all()


@pytest.mark.enable_socket
@pytest.mark.skipif(sys.platform == "win32", reason="symlinked scripts + POSIX signals")
def test_viz_start_restart_stop_live(viz_root):
    root, port = viz_root
    vm = admin_server.VizManager(root)
    assert vm.status()["viz"]["running"] is False
    assert vm.start_viz() is True
    st = vm.status()["viz"]
    assert st["running"] is True and st["port"] == port  # catches silent config fallback
    assert _wait_http(st["url"])
    pid1 = st["pid"]
    assert vm.restart_viz() is True
    st2 = vm.status()["viz"]
    assert st2["running"] is True and st2["pid"] != pid1
    assert _wait_http(st2["url"])
    assert vm.stop_viz() is True
    assert vm.status()["viz"]["running"] is False
    with pytest.raises(OSError):
        urllib.request.urlopen(_loopback(st2["url"]), timeout=2)


@pytest.mark.enable_socket
@pytest.mark.skipif(sys.platform == "win32", reason="symlinked scripts + POSIX signals")
def test_subserver_action_handler_and_routes(viz_root, monkeypatch):
    root, _port = viz_root
    vm = admin_server.VizManager(root)
    monkeypatch.setattr(AdminRequestHandler, "viz_manager", vm, raising=False)
    captured = {}
    handler = AdminRequestHandler.__new__(AdminRequestHandler)
    handler._send_json = lambda payload, status=200: captured.update(payload)
    handler._handle_subserver_action("viz", "start")
    assert captured["success"] is True
    assert captured["status"]["viz"]["running"] is True
    match = AdminRequestHandler._match_subserver_route
    assert match("/api/subserver/viz/restart") == ("viz", "restart")
    assert match("/api/subserver/evil/start") is None


def test_viz_dashboard_ui_wiring():
    html = (_PROJECT_ROOT / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")
    start = html.index("async function viewVizDashboard")
    body = html[start:start + 8000]
    assert 'el("iframe"' in body
    assert "lastVizUrl" in body
    assert "`/api/subserver/${name}/${action}`" in body
