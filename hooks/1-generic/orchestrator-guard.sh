#!/bin/bash
# hook: orchestrator-guard
# version: 1.0.0
# event: PreToolUse
# matcher: ""
# description: Block non-orchestrator write/edit/bash calls when orchestrator.strict=true
# enabled_by_default: true

# This hook is always active (enabled_by_default: true).
# It self-checks whether orchestrator.strict mode is enabled in project.yaml.
# If strict mode is off, the hook exits 0 immediately and imposes no overhead.
#
# Only mutating tools (Write, Edit, Bash) are intercepted.
# Research tools (read, glob, grep) are never blocked.
#
# Exit codes: 0 = allow, 2 = block (stdout shown as error context).

INPUT=$(cat)

# Try python first, then python3
_PY=""
if command -v python >/dev/null 2>&1; then
  _PY="python"
elif command -v python3 >/dev/null 2>&1; then
  _PY="python3"
fi

if [ -z "$_PY" ]; then
  # No Python available — cannot parse JSON/YAML; allow through to avoid breakage
  exit 0
fi

TOOL_NAME=$(echo "$INPUT" | $_PY -c "import json,sys; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")

# If no tool name: startup or other events — allow through
if [ -z "$TOOL_NAME" ]; then
  exit 0
fi

# Only block mutating tools
case "$TOOL_NAME" in
  Write|Edit|Bash) ;;
  *) exit 0 ;;
esac

# Check if we are inside the orchestrator agent (not the main chat)
AGENT_NAME=$(echo "$INPUT" | $_PY -c "import json,sys; print(json.load(sys.stdin).get('agent_name',''))" 2>/dev/null || echo "")

if echo "$AGENT_NAME" | grep -qi "orchestrator"; then
  exit 0
fi

# Determine project root
PROJECT_ROOT=$(echo "$INPUT" | $_PY -c "import json,sys; print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null || echo "")
if [ -z "$PROJECT_ROOT" ]; then
  PROJECT_ROOT="$PWD"
fi

# Check if strict mode is enabled in project.yaml
CONFIG_FILE="$PROJECT_ROOT/.meta-config/project.yaml"
if [ -f "$CONFIG_FILE" ]; then
  STRICT=$("$_PY" -c "
import yaml, sys
try:
    with open('$CONFIG_FILE') as f:
        c = yaml.safe_load(f) or {}
    orch = c.get('orchestrator', {})
    strict = orch.get('strict', False)
    enabled = orch.get('enabled', True)
    print('true' if strict and enabled else 'false')
except Exception:
    print('false')
" 2>/dev/null)

  if [ "$STRICT" = "true" ]; then
    echo "ORCHESTRATOR_GUARD: STRICT MODE is active. Direct $TOOL_NAME calls in the main chat are blocked."
    echo "Delegate this task to the orchestrator agent."
    exit 2
  fi
fi

exit 0
