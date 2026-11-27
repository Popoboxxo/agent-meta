#!/bin/bash
# hook: viz-log
# version: 1.2.0
# event: PreToolUse
# description: Automatically logs all tool calls to .meta-viz/events.jsonl for session visualization
# changelog: 1.2.0: issue #1238c2 -- delegate event construction and append logging to the deployed flat hook_gate_viz_log.py module; preserve the event schema, command preview, fail-open error handling and exit code 0
# enabled_by_default: false
#
# This hook is managed by agent-meta sync.py.
# It is ONLY copied and enabled when viz.mode is "dynamic" or "full".
# When viz.mode is "off" or "static", sync.py removes this hook automatically.

set -uo pipefail

# Not a security boundary (best-effort session-visualization logging only)
# — fails open (exit 0) if python3 is unavailable, same as before (issue
# #595 only hardens the two hooks that are actual security controls).
command -v python3 &>/dev/null || exit 0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_LIB_DIR="$SCRIPT_DIR/lib"

python3 "$HOOK_LIB_DIR/hook_gate_viz_log.py" 2>/dev/null
exit 0
