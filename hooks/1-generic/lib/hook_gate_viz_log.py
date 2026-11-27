#!/usr/bin/env python3
"""Best-effort tool-call event logger for the deployed viz-log hook.

Issue #1238c2: importable replacement for the former inline Python heredoc.
Malformed payloads and logging failures remain fail-open.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone


def main(argv: list[str], stdin: str) -> int:
    """Append one visualization event and always return 0."""
    del argv
    try:
        data = json.loads(stdin)
        tool_name = data.get("tool_name", "unknown")
        tool_input = data.get("tool_input", {})

        # Try to extract agent name from working directory or env.
        agent_name = os.environ.get("AGENT_NAME", "system")
        provider = os.environ.get("AGENT_PROVIDER", "unknown")

        # Build minimal event.
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": "tool_call",
            "agent": agent_name,
            "tool": tool_name,
            "provider": provider,
        }

        # Add command snippet if Bash tool.
        if tool_name == "Bash" and isinstance(tool_input, dict):
            command = tool_input.get("command", "")
            if command:
                event["payload"] = {"command_preview": command[:120]}

        viz_dir = ".meta-viz"
        os.makedirs(viz_dir, exist_ok=True)

        with open(f"{viz_dir}/events.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin.read()))
