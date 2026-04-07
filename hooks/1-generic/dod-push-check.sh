#!/bin/bash
# hook: dod-push-check
# version: 1.0.0
# event: PreToolUse
# matcher: Bash
# description: Blocks git push until tests are green (DoD enforcement)
# enabled_by_default: false

# Claude Code passes hook context as JSON on stdin.
# Exit 0 = allow, exit 2 = block (stdout shown to Claude as context).

INPUT=$(cat)

# python3 required for JSON parsing
command -v python3 &>/dev/null || exit 0

TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

# Only intercept Bash tool calls
[ "$TOOL_NAME" = "Bash" ] || exit 0

# Only intercept commands that contain git push
echo "$COMMAND" | grep -qE '(^|[;&|[:space:]])git push' || exit 0

# Resolve TEST_COMMAND: env var > agent-meta.config.json
TEST_CMD="${AGENT_META_TEST_COMMAND:-}"

if [ -z "$TEST_CMD" ]; then
  DIR="$PWD"
  for _ in 1 2 3 4; do
    if [ -f "$DIR/agent-meta.config.json" ]; then
      TEST_CMD=$(python3 -c "import json; c=json.load(open('$DIR/agent-meta.config.json')); print(c.get('variables',{}).get('TEST_COMMAND',''))" 2>/dev/null)
      break
    fi
    DIR="$(dirname "$DIR")"
  done
fi

if [ -z "$TEST_CMD" ]; then
  echo "DoD-Check: TEST_COMMAND not configured."
  echo "Set variables.TEST_COMMAND in agent-meta.config.json or"
  echo "export AGENT_META_TEST_COMMAND='<your-test-command>'."
  echo "Push blocked. Fix config or disable dod-push-check in agent-meta.config.json."
  exit 2
fi

echo "DoD-Check: Running '$TEST_CMD'..."
if ! eval "$TEST_CMD" 2>&1; then
  echo ""
  echo "DoD-Check FAILED: Tests must pass before pushing."
  echo "Fix failing tests and retry, or disable the hook temporarily."
  exit 2
fi

echo "DoD-Check passed."
exit 0
