"""run_plugin_test dispatches per origin-type. All process/HTTP calls are
mocked — no real network, no real subprocess (pattern: test_auto_github_release_hook).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import lib.plugin_test as pt  # noqa: E402
from lib.plugin_test import run_plugin_test  # noqa: E402


def test_local_binary_pass(monkeypatch):
    monkeypatch.setattr(pt.shutil, "which", lambda n: "/usr/bin/graphify")
    monkeypatch.setattr(pt, "_run_version", lambda binary: (True, "graphify 1.2.3"))
    res = run_plugin_test("graphify", {"origin-type": "local-binary", "binary": "graphify"})
    assert res["status"] == "PASS"
    assert "1.2.3" in res["message"]
    assert isinstance(res["latency_ms"], int)


def test_local_binary_missing(monkeypatch):
    monkeypatch.setattr(pt.shutil, "which", lambda n: None)
    res = run_plugin_test("graphify", {"origin-type": "local-binary", "binary": "graphify"})
    assert res["status"] == "FAIL"
    assert "not found" in res["message"].lower()


def test_local_process_handshake(monkeypatch):
    monkeypatch.setattr(pt, "_mcp_initialize_handshake",
                        lambda cmd, args, env: (True, "initialize ok"))
    pdef = {"origin-type": "local-process",
            "connection": {"type": "stdio", "command": "npx", "args": ["-y", "x"]}}
    res = run_plugin_test("influxdb", pdef)
    assert res["status"] == "PASS"


def test_remote_saas_reachable(monkeypatch):
    monkeypatch.setattr(pt, "_http_probe", lambda url, headers: (200, "OK"))
    pdef = {"origin-type": "remote-saas",
            "connection": {"type": "sse", "url": "https://x/mcp",
                           "headers": {"Authorization": "Bearer {{TOK}}"}}}
    res = run_plugin_test("honcho", pdef, secrets={"TOK": "secret"})
    assert res["status"] == "PASS"


def test_remote_saas_401_is_reachable(monkeypatch):
    monkeypatch.setattr(pt, "_http_probe", lambda url, headers: (401, "Unauthorized"))
    pdef = {"origin-type": "remote-saas", "connection": {"type": "sse", "url": "https://x/mcp"}}
    res = run_plugin_test("honcho", pdef)
    assert res["status"] == "PASS"  # 401 still means the endpoint answered


def test_remote_saas_refused(monkeypatch):
    def _boom(url, headers):
        raise ConnectionRefusedError("refused")
    monkeypatch.setattr(pt, "_http_probe", _boom)
    pdef = {"origin-type": "remote-saas", "connection": {"type": "sse", "url": "https://x/mcp"}}
    res = run_plugin_test("honcho", pdef)
    assert res["status"] == "FAIL"


def test_local_process_timeout(monkeypatch):
    """Verify readline timeout is bounded by select.select()."""
    # Mock select to simulate timeout (no stdout readable), and mock Popen
    # to avoid actual subprocess
    class MockStdin:
        def write(self, s):
            pass
        def flush(self):
            pass
    class MockProc:
        def __init__(self):
            self.stdin = MockStdin()
            self.stdout = None
        def poll(self):
            return None
        def terminate(self):
            pass
        def wait(self, timeout=None):
            pass
        def kill(self):
            pass
    monkeypatch.setattr(pt.select, "select", lambda r, w, x, t: ([], [], []))
    monkeypatch.setattr(pt.subprocess, "Popen", lambda *a, **kw: MockProc())
    pdef = {"origin-type": "local-process",
            "connection": {"type": "stdio", "command": "sleep", "args": ["10"]}}
    res = run_plugin_test("hung", pdef)
    assert res["status"] == "FAIL"
    assert "no response" in res["message"].lower()


def test_unknown_origin_type():
    res = run_plugin_test("mystery", {"origin-type": "quantum"})
    assert res["status"] == "UNKNOWN"
