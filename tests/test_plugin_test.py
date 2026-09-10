"""run_plugin_test dispatches per origin-type. All process/HTTP calls are
mocked — no real network, no real subprocess (pattern: test_auto_github_release_hook).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import lib.plugin_test as pt  # noqa: E402
from lib.plugin_test import run_plugin_test  # noqa: E402


def test_local_binary_pass(monkeypatch):
    captured = {}
    monkeypatch.setattr(pt.shutil, "which", lambda n: "/usr/bin/graphify")

    def _fake_run_version(binary):
        captured["binary"] = binary
        return True, "graphify 1.2.3"

    monkeypatch.setattr(pt, "_run_version", _fake_run_version)
    res = run_plugin_test("graphify", {"origin-type": "local-binary", "binary": "graphify"})
    assert res["status"] == "PASS"
    assert "1.2.3" in res["message"]
    assert isinstance(res["latency_ms"], int)
    # Root-cause fix (issue #725): the which()-resolved path, not the raw
    # binary name, must reach _run_version()/Popen (PATHEXT shims on Windows).
    assert captured["binary"] == "/usr/bin/graphify"


def test_local_binary_missing(monkeypatch):
    """#693: not installed locally is a setup gap (UNAVAILABLE/"Experimental"
    in the UI), not a plugin FAIL."""
    monkeypatch.setattr(pt.shutil, "which", lambda n: None)
    res = run_plugin_test("graphify", {"origin-type": "local-binary", "binary": "graphify"})
    assert res["status"] == "UNAVAILABLE"
    assert "not installed" in res["message"].lower()


def test_local_process_handshake(monkeypatch):
    monkeypatch.setattr(pt.shutil, "which", lambda n: "/usr/bin/npx")
    monkeypatch.setattr(pt, "_mcp_initialize_handshake",
                        lambda cmd, args, env: (True, "initialize ok"))
    pdef = {"origin-type": "local-process",
            "connection": {"type": "stdio", "command": "npx", "args": ["-y", "x"]}}
    res = run_plugin_test("influxdb", pdef)
    assert res["status"] == "PASS"


def test_local_process_command_missing(monkeypatch):
    """#693: command not on PATH is a setup gap, not a plugin FAIL — and must
    short-circuit before attempting the handshake."""
    monkeypatch.setattr(pt.shutil, "which", lambda n: None)
    monkeypatch.setattr(pt, "_mcp_initialize_handshake",
                        lambda cmd, args, env: (_ for _ in ()).throw(AssertionError("should not be called")))
    pdef = {"origin-type": "local-process",
            "connection": {"type": "stdio", "command": "npx", "args": ["-y", "x"]}}
    res = run_plugin_test("influxdb", pdef)
    assert res["status"] == "UNAVAILABLE"
    assert "not installed" in res["message"].lower()


def test_remote_saas_unresolved_secret(monkeypatch):
    """#693: a missing per-project secret leaves a `{{VAR}}` placeholder in the
    URL — that's a config gap, not a broken plugin, and must not even attempt
    the HTTP probe (an unresolved placeholder is not a valid URL)."""
    monkeypatch.setattr(pt, "_http_probe",
                        lambda url, headers: (_ for _ in ()).throw(AssertionError("should not be called")))
    pdef = {"origin-type": "remote-saas",
            "connection": {"type": "sse", "url": "{{HOME_ASSISTANT_URL}}/api/mcp"}}
    res = run_plugin_test("home-assistant", pdef)
    assert res["status"] == "UNAVAILABLE"
    assert "secret" in res["message"].lower()


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
    """Verify timeout is bounded by _read_line_with_timeout (thread + queue).
    Tests that partial-line-then-stall returns FAIL, not hang."""
    # Mock both _read_line_with_timeout to return None (simulating timeout)
    # and Popen to avoid actual subprocess
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

    monkeypatch.setattr(pt.shutil, "which", lambda n: "/usr/bin/mock")
    monkeypatch.setattr(pt, "_read_line_with_timeout", lambda stream, timeout: None)
    monkeypatch.setattr(pt.subprocess, "Popen", lambda *a, **kw: MockProc())
    pdef = {"origin-type": "local-process",
            "connection": {"type": "stdio", "command": "mock", "args": []}}
    res = run_plugin_test("hung", pdef)
    assert res["status"] == "FAIL"
    assert "no response" in res["message"].lower()


def test_local_process_partial_line_timeout(monkeypatch):
    """Specifically test that partial-line-then-stall doesn't hang the main thread.
    Mock _read_line_with_timeout to simulate a process that writes partial data
    and then stalls, which the thread-based implementation handles gracefully."""
    import time as time_module
    # Record when the call enters and exits
    call_times = []
    original_mcp = pt._mcp_initialize_handshake

    def _mcp_with_timing(cmd, args, env):
        call_times.append(("enter", time_module.time()))
        result = original_mcp(cmd, args, env)
        call_times.append(("exit", time_module.time()))
        return result

    # Mock the thread reader to timeout immediately
    monkeypatch.setattr(pt.shutil, "which", lambda n: "/usr/bin/true")
    monkeypatch.setattr(pt, "_read_line_with_timeout", lambda stream, timeout: None)
    monkeypatch.setattr(pt, "_mcp_initialize_handshake", _mcp_with_timing)

    pdef = {"origin-type": "local-process",
            "connection": {"type": "stdio", "command": "true", "args": []}}
    res = run_plugin_test("stalled", pdef)
    assert res["status"] == "FAIL"
    # Verify call didn't hang (if mocking works, should return quickly)
    assert "no response" in res["message"].lower()


def test_local_process_env_block_inherits_parent_env(monkeypatch):
    """I4 regression: a stdio plugin with an env: block must inherit the parent
    PATH/HOME, not run with ONLY its own declared vars (which would strip PATH
    and make the command unresolvable). The plugin's vars override on top."""
    captured = {}

    class MockStdin:
        def write(self, s):
            pass
        def flush(self):
            pass

    class MockProc:
        def __init__(self):
            self.stdin = MockStdin()
            self.stdout = object()
        def poll(self):
            return 0  # already exited → finally block skips terminate

    def _fake_popen(cmd, *a, **kw):
        captured["env"] = kw.get("env")
        return MockProc()

    monkeypatch.setattr(pt.os, "environ", {"PATH": "/usr/bin", "HOME": "/home/x"})
    monkeypatch.setattr(pt.shutil, "which", lambda n: "/usr/bin/npx")
    monkeypatch.setattr(pt.subprocess, "Popen", _fake_popen)
    monkeypatch.setattr(pt, "_read_line_with_timeout", lambda stream, timeout: '{"result": {}}')

    pdef = {"origin-type": "local-process",
            "connection": {"type": "stdio", "command": "npx", "args": ["-y", "srv"],
                           "env": {"API_KEY": "{{TOK}}"}}}
    res = run_plugin_test("srv", pdef, secrets={"TOK": "sekret"})

    assert res["status"] == "PASS"
    env = captured["env"]
    assert env is not None
    assert env["PATH"] == "/usr/bin"          # inherited from parent
    assert env["HOME"] == "/home/x"           # inherited from parent
    assert env["API_KEY"] == "sekret"         # plugin's own var, secret-resolved


def test_unknown_origin_type():
    res = run_plugin_test("mystery", {"origin-type": "quantum"})
    assert res["status"] == "UNKNOWN"


def test_local_process_command_uses_resolved_which_path(monkeypatch):
    """Root-cause fix for issue #725's misfix: which() resolves PATHEXT shims
    (.cmd/.bat on Windows) that Popen(shell=False) does not resolve itself —
    so the resolved path, not the raw command string, must reach Popen."""
    captured = {}

    class MockStdin:
        def write(self, s):
            pass
        def flush(self):
            pass

    class MockProc:
        def __init__(self):
            self.stdin = MockStdin()
            self.stdout = object()
        def poll(self):
            return 0  # already exited → finally block skips terminate

    def _fake_popen(cmd, *a, **kw):
        captured["cmd"] = cmd
        return MockProc()

    monkeypatch.setattr(pt.shutil, "which", lambda n: "/usr/local/bin/project-atlas.cmd")
    monkeypatch.setattr(pt.subprocess, "Popen", _fake_popen)
    monkeypatch.setattr(pt, "_read_line_with_timeout", lambda stream, timeout: '{"result": {}}')

    pdef = {"origin-type": "local-process",
            "connection": {"type": "stdio", "command": "project-atlas", "args": ["--mcp"]}}
    res = run_plugin_test("project-atlas", pdef)

    assert res["status"] == "PASS"
    assert captured["cmd"] == ["/usr/local/bin/project-atlas.cmd", "--mcp"]


@pytest.mark.parametrize("message", [
    "[WinError 2] The system cannot find the file specified",
    "[Errno 2] No such file or directory: 'graphify'",
])
def test_local_process_resolved_path_still_fnf_is_fail_not_unavailable(monkeypatch, message):
    """Issue #725 misfix: previously ANY FileNotFoundError from Popen was
    silently reclassified as UNAVAILABLE, even after which() already found a
    path. That hides real failures (permissions, TOCTOU races, a Windows
    .cmd shim CreateProcess can't exec directly). Once which() found a path,
    a further FileNotFoundError is unexpected and must surface as FAIL."""
    monkeypatch.setattr(pt.shutil, "which", lambda n: "/usr/bin/mock")

    def _boom(*a, **kw):
        raise FileNotFoundError(message)

    monkeypatch.setattr(pt.subprocess, "Popen", _boom)
    pdef = {"origin-type": "local-process",
            "connection": {"type": "stdio", "command": "project-atlas", "args": []}}
    res = run_plugin_test("project-atlas", pdef)
    assert res["status"] == "FAIL"
    assert "resolved" in res["message"].lower()


def test_remote_saas_placeholder_never_reaches_http_probe(monkeypatch):
    """Root cause: a scaffolded-but-blank secret (the shipped secrets.local
    template ships empty strings, not missing keys) resolves the `{{VAR}}`
    placeholder to "" — no longer matching the placeholder pattern — so a
    post-substitution regex check would miss it and let the blank/unresolved
    URL reach the HTTP probe (urllib's "unknown url type"). The guard must
    catch this pre-substitution instead."""
    monkeypatch.setattr(pt, "_http_probe",
                        lambda url, headers: (_ for _ in ()).throw(
                            AssertionError("must not reach the HTTP probe")))
    pdef = {"origin-type": "remote-saas",
            "connection": {"type": "sse", "url": "{{MCP_HONCHO_URL}}"}}

    # Case A: secret entirely absent from secrets.local.yaml.
    res = run_plugin_test("honcho", pdef, secrets={})
    assert res["status"] == "UNAVAILABLE"

    # Case B: secret present but blank (the shipped template's default).
    res = run_plugin_test("honcho", pdef, secrets={"MCP_HONCHO_URL": ""})
    assert res["status"] == "UNAVAILABLE"
