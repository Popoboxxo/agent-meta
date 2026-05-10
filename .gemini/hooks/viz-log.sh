#!/bin/bash
# hook: viz-log
# version: 1.0.0
# event: PreToolUse
# description: Automatically logs all tool calls to .meta-viz/events.jsonl for session visualization
# enabled_by_default: false
#
# This hook is managed by agent-meta sync.py.
# It is ONLY copied and enabled when viz.mode is "dynamic" or "full".
# When viz.mode is "off" or "static", sync.py removes this hook automatically.

command -v python3 &>/dev/null || exit 0

read -r -d '' _VIZ_LOG <<'PYEOF'
import json, sys, os
from datetime import datetime, timezone

try:
    d = json.load(sys.stdin)
    tool_name = d.get('tool_name', 'unknown')
    tool_input = d.get('tool_input', {})
    
    # Try to extract agent name from working directory or env
    agent_name = os.environ.get('AGENT_NAME', 'system')
    provider = os.environ.get('AGENT_PROVIDER', 'unknown')
    
    # Build minimal event
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "tool_call",
        "agent": agent_name,
        "tool": tool_name,
        "provider": provider,
    }
    
    # Add command snippet if Bash tool
    if tool_name == "Bash" and isinstance(tool_input, dict):
        cmd = tool_input.get("command", "")
        if cmd:
            event["payload"] = {"command_preview": cmd[:120]}
    
    viz_dir = ".meta-viz"
    os.makedirs(viz_dir, exist_ok=True)
    
    with open(f"{viz_dir}/events.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
except Exception:
    pass
PYEOF

python3 -c "$_VIZ_LOG" 2>/dev/null
exit 0
