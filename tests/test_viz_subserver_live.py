"""Live subprocess test for the viz sub-server controls (#317)."""
import importlib.util
import json
import socket
import sys
import threading
import time
import urllib.error
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
def viz_root(request, tmp_path):
    # socket_enabled only exists with pytest-socket (not installed in CI)
    try:
        request.getfixturevalue("socket_enabled")
    except pytest.FixtureLookupError:
        pass
    port = _free_port()
    mcp_port = _free_port()
    # viz-report.py serves docs/ui/live-dashboard.html from <root>/docs
    for name in ("scripts", "docs"):
        (tmp_path / name).symlink_to(_PROJECT_ROOT / name)
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        'agent-meta-version: "2.0.0-beta.1"\n'
        "ai-providers: [Claude]\n"
        "dod-preset: rapid-prototyping\n"
        "variables:\n  PROJECT_NAME: viz\n  PROJECT_PREFIX: vz\n"
        f"viz:\n  server:\n    port: {port}\n    timeout_sec: 60\n"
        f"  mcp:\n    port: {mcp_port}\n",
        encoding="utf-8",
    )
    yield tmp_path, port, mcp_port
    admin_server.VizManager(tmp_path).stop_all()


@pytest.mark.enable_socket
@pytest.mark.skipif(sys.platform == "win32", reason="symlinked scripts + POSIX signals")
def test_viz_start_restart_stop_live(viz_root):
    root, port, _mcp = viz_root
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
    root, _port, _mcp = viz_root
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


def _post(base, path):
    req = urllib.request.Request(base + path, data=b"{}", method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, json.loads(r.read())


@pytest.mark.enable_socket
@pytest.mark.skipif(sys.platform == "win32", reason="symlinked scripts + POSIX signals")
def test_subserver_http_post_viz_and_mcp(viz_root):
    """Real POST /api/subserver/{viz|mcp}/{start|restart|stop} on a live admin server (#317)."""
    root, _vp, _mp = viz_root
    srv = admin_server.AdminServer(root, host="127.0.0.1", port=_free_port(), enable_viz=False)
    t = threading.Thread(target=srv.httpd.serve_forever, daemon=True)
    t.start()
    base = f"http://127.0.0.1:{srv.port}"
    try:
        for name in ("viz", "mcp"):
            status, body = _post(base, f"/api/subserver/{name}/start")
            assert status == 200 and body["success"] is True, body
            st = body["status"][name]
            assert st["running"] is True
            assert _wait_http(st["url"]) if name == "viz" else True
            pid1 = st["pid"]
            _, body = _post(base, f"/api/subserver/{name}/restart")
            assert body["status"][name]["running"] is True
            assert body["status"][name]["pid"] != pid1
            _, body = _post(base, f"/api/subserver/{name}/stop")
            assert body["success"] is True and body["status"][name]["running"] is False
        with pytest.raises(urllib.error.HTTPError) as exc:
            _post(base, "/api/subserver/evil/start")
        assert exc.value.code == 404
    finally:
        srv.httpd.shutdown()
        srv.httpd.server_close()
        t.join(5)


@pytest.mark.enable_socket
@pytest.mark.skipif(sys.platform == "win32", reason="symlinked scripts + POSIX signals")
def test_viz_dashboard_browser_iframe_follows_state(viz_root):
    """Chromium E2E: iframe appears on Start, vanishes on Stop, reloads on Restart (#317)."""
    sync_api = pytest.importorskip("playwright.sync_api")
    root, _vp, _mp = viz_root
    srv = admin_server.AdminServer(root, host="127.0.0.1", port=_free_port(), enable_viz=False)
    t = threading.Thread(target=srv.httpd.serve_forever, daemon=True)
    t.start()
    try:
        with sync_api.sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception as exc:  # noqa: BLE001 - browser binary not installed
                pytest.skip(f"chromium unavailable: {exc}")
            try:
                page = browser.new_page()
                page.goto(f"http://127.0.0.1:{srv.port}/#/viz-dashboard")
                page.wait_for_selector("text=Subserver controls")
                assert page.locator("iframe").count() == 0
                viz_row = page.locator(".flex-row", has_text="Viz dashboard").first
                viz_row.get_by_role("button", name="Start", exact=True).click()
                page.wait_for_selector("iframe", timeout=20000)
                src = page.locator("iframe").get_attribute("src")
                assert str(srv_viz_port(root)) in src
                pid1 = admin_server.VizManager(root).status()["viz"]["pid"]
                viz_row.get_by_role("button", name="Restart", exact=True).click()
                page.wait_for_function(
                    "!document.querySelector('button[disabled]')", timeout=20000)
                assert admin_server.VizManager(root).status()["viz"]["pid"] != pid1
                assert page.locator("iframe").count() == 1
                viz_row.get_by_role("button", name="Stop", exact=True).click()
                page.wait_for_selector("iframe", state="detached", timeout=20000)
                assert "not running" in page.inner_text("body")
            finally:
                browser.close()
    finally:
        srv.httpd.shutdown()
        srv.httpd.server_close()
        t.join(5)


def srv_viz_port(root):
    return admin_server.VizManager(root).status()["viz"]["port"]
