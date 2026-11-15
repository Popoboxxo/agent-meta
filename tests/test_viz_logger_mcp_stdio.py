"""Stdio MCP handshake of scripts/viz-logger.py must use NDJSON (#1259)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tests.timeouts import SCRIPT_TIMEOUT

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "viz-logger.py"


def _line(msg: dict) -> bytes:
    return json.dumps(msg).encode("utf-8") + b"\n"


def test_stdio_handshake_ndjson(tmp_path):
    msgs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "t", "version": "0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "log_viz_event",
                    "arguments": {"event": "start", "agent": "tester"}}},
    ]
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--mcp", "--root", str(tmp_path)],
        input=b"".join(_line(m) for m in msgs),
        capture_output=True,
        timeout=SCRIPT_TIMEOUT,
    )
    lines = [ln for ln in proc.stdout.split(b"\n") if ln.strip()]
    assert b"Content-Length" not in proc.stdout
    responses = {r["id"]: r for r in (json.loads(ln) for ln in lines)}
    assert set(responses) == {1, 2, 3}
    assert "log_viz_event" in [t["name"] for t in responses[2]["result"]["tools"]]
    assert responses[3]["result"]["isError"] is False
    log = (tmp_path / ".meta-viz" / "events.jsonl").read_text(encoding="utf-8")
    assert '"tester"' in log
