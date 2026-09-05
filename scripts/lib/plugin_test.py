"""Active health-check for a single plugin, dispatched by origin-type. Shared by
`sync.py --test-plugin` (CLI) and admin-server `POST /api/plugins/<id>/test`
(HTTP) so both surfaces exercise one implementation. The three I/O seams
(_run_version, _mcp_initialize_handshake, _http_probe) are module-level so tests
mock them without real subprocess/network.
"""
from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import threading
import time
import urllib.request

_SECRET_RE = re.compile(r"\{\{(\w+)\}\}")
_TIMEOUT = 8


def _resolve_secrets(text: str, secrets: dict) -> str:
    return _SECRET_RE.sub(lambda m: str(secrets.get(m.group(1), m.group(0))), text)


def _read_line_with_timeout(stream, timeout: float) -> str | None:
    """Read one line from stream with bounded timeout. Returns the line,
    or None on timeout. Uses a daemon thread to avoid select() limitations
    (only works on sockets on Windows, partial-line semantics on Unix).
    The thread will unblock and exit once the stream is closed by the caller."""
    q: queue.Queue = queue.Queue(maxsize=1)

    def _reader():
        try:
            q.put(stream.readline())
        except Exception:  # noqa: BLE001
            q.put("")

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    try:
        return q.get(timeout=timeout)
    except queue.Empty:
        return None  # timed out; daemon thread left running but harmless


def _run_version(binary: str) -> tuple[bool, str]:
    try:
        out = subprocess.run([binary, "--version"], capture_output=True, text=True,
                             timeout=_TIMEOUT)  # noqa: S603
        msg = (out.stdout or out.stderr or "").strip().splitlines()
        return out.returncode == 0, (msg[0] if msg else f"{binary} present")
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def _mcp_initialize_handshake(command: str, args: list, env: dict) -> tuple[bool, str]:
    """Start the stdio MCP process, send an `initialize` request, read one line,
    terminate. Returns (ok, message). Bounded by _TIMEOUT to prevent hangs.
    Uses _read_line_with_timeout for correct timeout semantics on all platforms."""
    proc = None
    try:
        # Merge the plugin's declared vars ON TOP of the parent environment —
        # passing only `env` (which holds solely the plugin's own vars, no PATH
        # or HOME) makes every stdio plugin with an env: block fail to even
        # spawn (e.g. `npx`/`node` not found because PATH is gone).
        child_env = {**os.environ, **env} if env else None
        proc = subprocess.Popen([command, *args], stdin=subprocess.PIPE,  # noqa: S603
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                text=True, env=child_env)
        req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                          "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                     "clientInfo": {"name": "agent-meta", "version": "1"}}})
        proc.stdin.write(req + "\n")
        proc.stdin.flush()
        # Read one line with bounded timeout (works on all platforms, handles partial lines)
        line = _read_line_with_timeout(proc.stdout, _TIMEOUT)
        if line is None:
            return False, f"no response within {_TIMEOUT}s"
        return ("result" in line or "jsonrpc" in line), "initialize responded"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=_TIMEOUT)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


def _http_probe(url: str, headers: dict) -> tuple[int, str]:
    req = urllib.request.Request(url, headers=headers or {}, method="HEAD")  # noqa: S310
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:  # noqa: S310
        return resp.status, "reachable"


def _result(status: str, message: str, started: float) -> dict:
    return {"status": status, "message": message,
            "latency_ms": int((time.monotonic() - started) * 1000)}


def run_plugin_test(plugin_id: str, plugin_def: dict, secrets: dict | None = None) -> dict:
    """Test one plugin's reachability. status in {PASS, FAIL, UNKNOWN}."""
    secrets = secrets or {}
    started = time.monotonic()
    origin = plugin_def.get("origin-type")
    conn = plugin_def.get("connection", {}) or {}

    if origin == "local-binary":
        binary = plugin_def.get("binary") or plugin_id
        if shutil.which(binary) is None:
            return _result("FAIL", f"binary '{binary}' not found on PATH", started)
        ok, msg = _run_version(binary)
        return _result("PASS" if ok else "FAIL", msg, started)

    if origin in ("local-process", "repo-owned-process"):
        env = {_resolve_secrets(k, secrets): _resolve_secrets(str(v), secrets)
               for k, v in (conn.get("env") or {}).items()}
        ok, msg = _mcp_initialize_handshake(conn.get("command", ""), conn.get("args", []), env)
        return _result("PASS" if ok else "FAIL", msg, started)

    if origin == "remote-saas":
        url = _resolve_secrets(conn.get("url", ""), secrets)
        headers = {k: _resolve_secrets(str(v), secrets) for k, v in (conn.get("headers") or {}).items()}
        try:
            code, _ = _http_probe(url, headers)
        except Exception as exc:  # noqa: BLE001 - refused/timeout/etc = not reachable
            return _result("FAIL", f"not reachable: {exc}", started)
        # Endpoint reachable if it responds with any status < 500 (incl. 401 auth errors)
        reachable = code < 500
        return _result("PASS" if reachable else "FAIL", f"HTTP {code}", started)

    return _result("UNKNOWN", f"no test strategy for origin-type '{origin}'", started)
