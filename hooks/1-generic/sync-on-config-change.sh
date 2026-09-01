#!/bin/bash
# hook: sync-on-config-change
# version: 1.1.0
# event: PostToolUse
# matcher: Write|Edit
# provider: Claude
# description: Trigger sync pending-task when .meta-config/project.yaml changes
# enabled_by_default: false

set -uo pipefail

# Claude Code passes hook context as JSON on stdin.
# PostToolUse hooks receive the tool result — exit code is ignored.
#
# Not a security boundary (informational automation only) — fails OPEN
# (exit 0) if the shared helper lib or python3/python is unavailable,
# same as before (issue #595 only hardens the two hooks that are actual
# security controls: orchestrator-guard.sh and dod-push-check.sh).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/hook_common.sh" 2>/dev/null || exit 0
hook_have_python || exit 0

INPUT=$(cat)
TOOL_NAME=$(hook_json_get "$INPUT" "tool_name")
FILE_PATH=$(hook_json_get "$INPUT" "tool_input.file_path")

# Only intercept file-writing tools
[ "$TOOL_NAME" = "Write" ] || [ "$TOOL_NAME" = "Edit" ] || exit 0

# Only fire when the edited file is the project config
printf '%s' "$FILE_PATH" | grep -qE '\.meta-config/project\.yaml$' || exit 0

# Locate lifecycle_check.py (relative to this hook's location, SCRIPT_DIR
# already resolved above, or via .agent-meta submodule)
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
