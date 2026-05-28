#!/usr/bin/env python3
"""
agent-meta viz-logger.py
========================
Unified CLI tool and MCP server for logging visualization events.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Try to find the project root (where .meta-viz lives)
# Assuming scripts/viz-logger.py, project root is parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIZ_DIR = PROJECT_ROOT / ".meta-viz"
EVENT_LOG = VIZ_DIR / "events.jsonl"


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
    """Read a JSON-RPC message from stdin with Content-Length header."""
    headers = {}
    while True:
        line = sys.stdin.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            break
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

    length = headers.get("content-length")
    if not length:
        return None

    try:
        length = int(length)
    except ValueError:
        return None

    data = sys.stdin.buffer.read(length)
    if not data:
        return None

    try:
        return json.loads(data.decode("utf-8"))
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


def main():
    # Detect --mcp before argparse so required fields are not enforced in server mode.
    if any(a == "--mcp" for a in sys.argv):
        run_mcp_server()
        return

    parser = argparse.ArgumentParser(description="Log viz events")
    parser.add_argument("--event", required=True, help="Event type: agent_start, delegate_out, agent_end, etc.")
    parser.add_argument("--agent", required=True, help="The current agent role")
    parser.add_argument("--provider", default="unknown", help="The AI provider")
    parser.add_argument("--status", help="Status (success, error) for agent_end")
    parser.add_argument("--payload", help="JSON payload or error message")
    parser.add_argument("--target", help="Target agent role (for delegate_out and agent_end)")
    parser.add_argument("--caller", help="Calling agent role (for agent_start)")
    parser.add_argument("--task_id", help="Correlation UUID to track delegation")

    args = parser.parse_args()

    event = _build_event_from_args(args)
    write_event_safe(event)


if __name__ == "__main__":
    main()
