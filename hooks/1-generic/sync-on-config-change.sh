#!/bin/bash
# hook: sync-on-config-change
# version: 1.0.0
# event: PostToolUse
# matcher: Write|Edit
# provider: Claude
# description: Trigger sync pending-task when .meta-config/project.yaml changes
# enabled_by_default: false

# Claude Code passes hook context as JSON on stdin.
# PostToolUse hooks receive the tool result — exit code is ignored.

# python3 required for JSON parsing
command -v python3 &>/dev/null || exit 0

read -r -d '' _PARSE_HOOK_INPUT <<'PYEOF'
import json, sys
d = json.load(sys.stdin)
ti = d.get('tool_input', {}) or {}
print(d.get('tool_name', ''))
print(ti.get('file_path', ''))
PYEOF

_parsed=$(python3 -c "$_PARSE_HOOK_INPUT" 2>/dev/null)
TOOL_NAME=$(printf '%s' "$_parsed" | sed -n '1p')
FILE_PATH=$(printf '%s' "$_parsed" | sed -n '2p')

# Only intercept file-writing tools
[ "$TOOL_NAME" = "Write" ] || [ "$TOOL_NAME" = "Edit" ] || exit 0

# Only fire when the edited file is the project config
echo "$FILE_PATH" | grep -qE '\.meta-config/project\.yaml$' || exit 0

# Locate lifecycle_check.py (relative to this hook's location or via .agent-meta submodule)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIFECYCLE_PY="$(dirname "$(dirname "$SCRIPT_DIR")")/scripts/lifecycle_check.py"

# Fallback: search for .agent-meta submodule from cwd
if [ ! -f "$LIFECYCLE_PY" ]; then
  LIFECYCLE_PY="$PWD/.agent-meta/scripts/lifecycle_check.py"
fi

[ -f "$LIFECYCLE_PY" ] || exit 0

# Graceful skip if sync.py is not available alongside lifecycle_check.py
SYNC_PY="$(dirname "$LIFECYCLE_PY")/sync.py"
[ -f "$SYNC_PY" ] || exit 0

# Fire the lifecycle check
python3 "$LIFECYCLE_PY" on-config-change

exit 0
