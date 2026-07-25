#!/usr/bin/env python3
"""
agent-meta viz-logger.py
========================
Unified CLI tool, stdio MCP server, and HTTP/SSE MCP server for logging visualization events.

Usage:
  CLI mode:    python viz-logger.py --event agent_start --agent my-agent --provider opencode
  Stdio MCP:   python viz-logger.py --mcp
  HTTP MCP:    python viz-logger.py --http [port]       (default port: 9090)
"""

import argparse
import http.server
import json
import os
import queue
import sys
import threading
import time
import urllib.parse
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Try to find the project root (where .meta-viz lives).
#
# Default assumption: ``scripts/viz-logger.py`` → project root is the parent of
# ``scripts/``. This is WRONG when the script runs from a submodule checkout
# (``.agent-meta/scripts/viz-logger.py``), where ``parent.parent`` resolves to
# the submodule directory instead of the host project root. In that case the
# caller (e.g. admin-server.py's VizManager) must pass ``--root <project_root>``
# so events land in the host project's ``.meta-viz/events.jsonl``.
def _find_project_root(start_dir: Path) -> Path:
    current = start_dir.resolve()
    while current.parent != current:
        if (current / ".meta-config").is_dir() or (current / ".meta-viz").is_dir() or (current / "project.yaml").exists():
            return current
        current = current.parent
    return start_dir.parent.parent

PROJECT_ROOT = _find_project_root(Path(__file__).parent)
VIZ_DIR = PROJECT_ROOT / ".meta-viz"
EVENT_LOG = VIZ_DIR / "events.jsonl"


def _apply_project_root(root: str | Path) -> None:
    """Override the project root used for event logging.

    Recomputes the module-level ``PROJECT_ROOT``, ``VIZ_DIR`` and ``EVENT_LOG``
    so that all logging modes (CLI, stdio MCP, HTTP MCP) write to the correct
    ``.meta-viz`` directory regardless of where this script physically lives.
    """
    global PROJECT_ROOT, VIZ_DIR, EVENT_LOG
    PROJECT_ROOT = Path(root).resolve()
    VIZ_DIR = PROJECT_ROOT / ".meta-viz"
    EVENT_LOG = VIZ_DIR / "events.jsonl"


def _root_from_argv(argv: list[str]) -> str | None:
    """Extract a ``--root``/``--project-root`` value from raw argv, if present.

    Needed because ``--mcp`` and ``--http`` modes are dispatched before argparse
    runs, yet both must honour an explicit project root.
    """
    for flag in ("--root", "--project-root"):
        for i, arg in enumerate(argv):
            if arg == flag and i + 1 < len(argv):
                return argv[i + 1]
            if arg.startswith(flag + "="):
                return arg.split("=", 1)[1]
    return None


def write_event_safe(event: dict):
    """Writes an event to events.jsonl with a retry loop for Windows PermissionError."""
    event.setdefault("ts", datetime.now(timezone.utc).isoformat())
    VIZ_DIR.mkdir(parents=True, exist_ok=True)

    retries = 10
    delay = 0.1

    # Simple lockfile mechanism for cross-process synchronization
    lockfile = EVENT_LOG.with_suffix('.lock')

    for attempt in range(retries):
        try:
            # Try to acquire lock
            fd = os.open(str(lockfile), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            os.close(fd)
        except FileExistsError:
            time.sleep(delay)
            continue

        try:
            with open(EVENT_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
            return
        except PermissionError:
            # Fallback if file itself is locked by external process
            pass
        finally:
            try:
                os.remove(lockfile)
            except OSError:
                pass

        time.sleep(delay)

    # If we get here, writing failed after all retries.
    print(f"Warnung: Konnte Event nicht schreiben nach {retries} Versuchen.", file=sys.stderr)


def _build_event_from_args(args: argparse.Namespace) -> dict:
    """Build event dict from argparse Namespace."""
    event = {
        "event": args.event,
        "agent": args.agent,
        "provider": args.provider,
    }

    if args.status:
        event["status"] = args.status
    if args.target:
        event["target"] = args.target
        # Fallback for older viz-report.py that expects 'to'
        event["to"] = args.target
    if args.caller:
        event["caller"] = args.caller
        # Fallback for older viz-report.py that expects 'from'
        event["from"] = args.caller
    if args.task_id:
        event["task_id"] = args.task_id
    if args.tokens_in is not None:
        event["tokens_in"] = args.tokens_in
    if args.tokens_out is not None:
        event["tokens_out"] = args.tokens_out

    if args.payload:
        try:
            event["payload"] = json.loads(args.payload)
        except json.JSONDecodeError:
            event["payload"] = {"message": args.payload}

    return event


def _build_event_from_params(params: dict) -> dict:
    """Build event dict from MCP tool parameters."""
    event = {
        "event": params["event"],
        "agent": params["agent"],
        "provider": params.get("provider", "unknown"),
    }

    if "status" in params:
        event["status"] = params["status"]
    if "target" in params:
        event["target"] = params["target"]
        event["to"] = params["target"]
    if "caller" in params:
        event["caller"] = params["caller"]
        event["from"] = params["caller"]
    if "task_id" in params:
        event["task_id"] = params["task_id"]
    if "payload" in params:
        event["payload"] = params["payload"]
    if "tokens_in" in params:
        event["tokens_in"] = params["tokens_in"]
    if "tokens_out" in params:
        event["tokens_out"] = params["tokens_out"]

    return event


# ---------------------------------------------------------------------------
# MCP Server (stdio JSON-RPC)
# ---------------------------------------------------------------------------

MCP_SERVER_NAME = "viz-logger"
MCP_SERVER_VERSION = "1.0.0"
MCP_PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "log_viz_event",
        "description": "Log a visualization event to the events.jsonl file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event": {
                    "type": "string",
                    "description": "Event type: agent_start, delegate_out, agent_end",
                    "enum": ["agent_start", "delegate_out", "agent_end"],
                },
                "agent": {
                    "type": "string",
                    "description": "The current agent role",
                },
                "provider": {
                    "type": "string",
                    "description": "The AI provider",
                },
                "status": {
                    "type": "string",
                    "description": "Status for agent_end",
                    "enum": ["success", "error"],
                },
                "target": {
                    "type": "string",
                    "description": "Target agent role (for delegate_out and agent_end)",
                },
                "caller": {
                    "type": "string",
                    "description": "Calling agent role (for agent_start)",
                },
                "task_id": {
                    "type": "string",
                    "description": "Correlation UUID to track delegation",
                },
                "payload": {
                    "type": "object",
                    "description": "Optional JSON payload or error message",
                },
                "tokens_in": {
                    "type": "integer",
                    "description": "Optional input token count for this agent invocation",
                },
                "tokens_out": {
                    "type": "integer",
                    "description": "Optional output token count for this agent invocation",
                },
            },
            "required": ["event", "agent"],
        },
    }
]


def _send_message(msg: dict):
    """Send a JSON-RPC message to stdout with Content-Length header."""
    data = json.dumps(msg, ensure_ascii=False)
    payload = data.encode("utf-8")
    header = f"Content-Length: {len(payload)}\r\n\r\n"
    sys.stdout.buffer.write(header.encode("ascii"))
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()


def _read_message() -> dict | None:
    """Read a JSON-RPC message from stdin with Content-Length header.

    Uses os.read() on fd 0 (stdin) directly to bypass Python's
    TextIOWrapper/BufferedReader layers which cause stdin pipe issues
    when spawned by Node.js child_process on Windows.
    """
    import os

    STDIN_FD = 0
    HEADER_DELIM = b"\r\n\r\n"

    # --- Read headers byte by byte until \r\n\r\n ---
    header_bytes = b""
    while True:
        try:
            ch = os.read(STDIN_FD, 1)
        except OSError:
            return None
        if not ch:
            return None  # EOF
        header_bytes += ch
        if header_bytes.endswith(HEADER_DELIM):
            break

    header_str = header_bytes.decode("utf-8")
    headers = {}
    for line in header_str.split("\r\n"):
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

    length_raw = headers.get("content-length")
    if not length_raw:
        return None

    try:
        length = int(length_raw)
    except ValueError:
        return None

    # --- Read body with exact byte count ---
    body_bytes = b""
    while len(body_bytes) < length:
        try:
            chunk = os.read(STDIN_FD, length - len(body_bytes))
        except OSError:
            return None
        if not chunk:
            return None
        body_bytes += chunk

    try:
        return json.loads(body_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def _make_response(request_id, result=None, error=None) -> dict:
    """Build a JSON-RPC response."""
    msg = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    return msg


def _handle_initialize(request_id, params):
    """Handle the initialize method."""
    result = {
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "capabilities": {
            "tools": {},
            "logging": {},
        },
        "serverInfo": {
            "name": MCP_SERVER_NAME,
            "version": MCP_SERVER_VERSION,
        },
    }
    return _make_response(request_id, result=result)


def _handle_tools_list(request_id, params):
    """Handle the tools/list method."""
    result = {"tools": TOOLS}
    return _make_response(request_id, result=result)


def _handle_tools_call(request_id, params):
    """Handle the tools/call method."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    if tool_name != "log_viz_event":
        return _make_response(
            request_id,
            error={"code": -32601, "message": f"Tool '{tool_name}' not found"}
        )

    if "event" not in arguments or "agent" not in arguments:
        return _make_response(
            request_id,
            error={"code": -32602, "message": "Missing required parameters: event, agent"}
        )

    try:
        event = _build_event_from_params(arguments)
        write_event_safe(event)
        result = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({"success": True, "event": event}, ensure_ascii=False),
                }
            ],
            "isError": False,
        }
        return _make_response(request_id, result=result)
    except Exception as e:
        result = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({"success": False, "error": str(e)}, ensure_ascii=False),
                }
            ],
            "isError": True,
        }
        return _make_response(request_id, result=result)


def run_mcp_server():
    """Run the MCP server over stdio JSON-RPC."""
    initialized = False
    msg = None

    while True:
        try:
            msg = _read_message()
            if msg is None:
                break

            method = msg.get("method")
            request_id = msg.get("id")
            params = msg.get("params", {})

            # Handle notifications (no id)
            if method == "notifications/initialized":
                initialized = True
                continue

            if method == "initialize":
                response = _handle_initialize(request_id, params)
                _send_message(response)
                continue

            if not initialized and method is not None:
                response = _make_response(
                    request_id,
                    error={"code": -32002, "message": "Server not initialized"}
                )
                _send_message(response)
                continue

            if method == "tools/list":
                response = _handle_tools_list(request_id, params)
                _send_message(response)
            elif method == "tools/call":
                response = _handle_tools_call(request_id, params)
                _send_message(response)
            elif method is not None:
                response = _make_response(
                    request_id,
                    error={"code": -32601, "message": f"Method '{method}' not found"}
                )
                _send_message(response)
            # else: unknown message without method, ignore

        except KeyboardInterrupt:
            break
        except Exception as e:
            # Try to send error response if we have an id
            if msg and "id" in msg:
                response = _make_response(
                    msg["id"],
                    error={"code": -32603, "message": f"Internal error: {str(e)}"}
                )
                _send_message(response)
            break


# ---------------------------------------------------------------------------
# HTTP/SSE MCP Server
# ---------------------------------------------------------------------------

_sse_sessions: dict[str, "queue.Queue[dict]"] = {}
_sse_sessions_lock = threading.Lock()


class _MCPSSERequestHandler(http.server.BaseHTTPRequestHandler):
    """Handles MCP SSE transport: GET /sse (event stream) and POST /message (requests)."""

    def do_GET(self):
        if self.path.startswith("/sse"):
            self._handle_sse()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path.startswith("/message"):
            self._handle_message()
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _handle_sse(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        session_id = params.get("sessionId", [str(uuid.uuid4())])[0]

        q: queue.Queue = queue.Queue()
        with _sse_sessions_lock:
            _sse_sessions[session_id] = q

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        # Send endpoint event so client knows where to POST
        endpoint_url = f"/message?sessionId={session_id}"
        self.wfile.write(f"event: endpoint\ndata: {endpoint_url}\n\n".encode())
        self.wfile.flush()

        try:
            while True:
                try:
                    data = q.get(timeout=30)
                    payload = json.dumps(data, ensure_ascii=False)
                    self.wfile.write(f"event: message\ndata: {payload}\n\n".encode())
                    self.wfile.flush()
                except queue.Empty:
                    # Periodic keep-alive (SSE comment — ignored by client)
                    self.wfile.write(b":\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with _sse_sessions_lock:
                _sse_sessions.pop(session_id, None)

    def _handle_message(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        session_id = params.get("sessionId", [""])[0]

        with _sse_sessions_lock:
            session_queue = _sse_sessions.get(session_id)
        if session_queue is None:
            self.send_error(400, "Invalid or missing sessionId")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            msg = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_error(400, "Invalid JSON")
            return

        self.send_response(202)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        method = msg.get("method")
        request_id = msg.get("id")
        params_in = msg.get("params", {})

        if method == "initialize":
            response = _handle_initialize(request_id, params_in)
        elif method == "notifications/initialized":
            self.send_response(200)
            self.end_headers()
            return  # Notification — no response
        elif method == "tools/list":
            response = _handle_tools_list(request_id, params_in)
        elif method == "tools/call":
            response = _handle_tools_call(request_id, params_in)
        elif method is not None:
            response = _make_response(
                request_id,
                error={"code": -32601, "message": f"Method '{method}' not found"},
            )
        else:
            return  # Unknown message without method

        if response is not None:
            session_queue.put(response)

    def log_message(self, format, *args):
        pass  # Suppress default access log


def run_http_server(port: int = 9090):
    """Run the MCP server over HTTP with SSE transport."""
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), _MCPSSERequestHandler)
    print(f"viz-logger MCP HTTP server listening on http://127.0.0.1:{port}/sse")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


def main():
    # Apply an explicit project root before any mode dispatch so that CLI,
    # stdio MCP and HTTP MCP modes all log to the correct .meta-viz directory.
    root_override = _root_from_argv(sys.argv)
    if root_override:
        _apply_project_root(root_override)

    # Detect --mcp or --http before argparse so required fields are not enforced in server mode.
    if any(a == "--mcp" for a in sys.argv):
        run_mcp_server()
        return

    if any(a == "--http" for a in sys.argv):
        port = 9090
        for i, a in enumerate(sys.argv):
            if a == "--http" and i + 1 < len(sys.argv):
                try:
                    port = int(sys.argv[i + 1])
                except ValueError:
                    pass
        run_http_server(port)
        return

    parser = argparse.ArgumentParser(description="Log viz events")
    parser.add_argument("--root", "--project-root", dest="root", default=None,
                        help="Project root where .meta-viz lives (override for submodule layout)")
    parser.add_argument("--event", required=True, help="Event type: agent_start, delegate_out, agent_end, etc.")
    parser.add_argument("--agent", required=True, help="The current agent role")
    parser.add_argument("--provider", default="unknown", help="The AI provider")
    parser.add_argument("--status", help="Status (success, error) for agent_end")
    parser.add_argument("--payload", help="JSON payload or error message")
    parser.add_argument("--target", help="Target agent role (for delegate_out and agent_end)")
    parser.add_argument("--caller", help="Calling agent role (for agent_start)")
    parser.add_argument("--task_id", help="Correlation UUID to track delegation")
    parser.add_argument("--tokens_in", type=int, default=None, help="Input token count (optional)")
    parser.add_argument("--tokens_out", type=int, default=None, help="Output token count (optional)")

    args = parser.parse_args()

    event = _build_event_from_args(args)
    write_event_safe(event)


if __name__ == "__main__":
    main()
