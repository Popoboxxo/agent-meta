#!/usr/bin/env python3
"""
agent-meta viz-logger.py
========================
Unified CLI tool and (future) MCP server for logging visualization events.
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

def main():
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
            
    write_event_safe(event)

if __name__ == "__main__":
    main()
