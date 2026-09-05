"""Active health-check for a single plugin, dispatched by origin-type. Shared by
`sync.py --test-plugin` (CLI) and admin-server `POST /api/plugins/<id>/test`
(HTTP) so both surfaces exercise one implementation. The three I/O seams
(_run_version, _mcp_initialize_handshake, _http_probe) are module-level so tests
mock them without real subprocess/network.
"""
from __future__ import annotations

import json
import re
import select
import shutil
import subprocess
import time
import urllib.request

_SECRET_RE = re.compile(r"\{\{(\w+)\}\}")
_TIMEOUT = 8


def _resolve_secrets(text: str, secrets: dict) -> str:
    return _SECRET_RE.sub(lambda m: str(secrets.get(m.group(1), m.group(0))), text)


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
    terminate. Returns (ok, message). Bounded by _TIMEOUT to prevent hangs."""
    proc = None
    try:
        proc = subprocess.Popen([command, *args], stdin=subprocess.PIPE,  # noqa: S603
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                text=True, env=env or None)
        req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                          "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                     "clientInfo": {"name": "agent-meta", "version": "1"}}})
        proc.stdin.write(req + "\n")
        proc.stdin.flush()
        # Wait with timeout for stdout to be ready, prevent indefinite hang
        readable, _, _ = select.select([proc.stdout], [], [], _TIMEOUT)
        if not readable:
            return False, f"no response within {_TIMEOUT}s"
        line = proc.stdout.readline()
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
