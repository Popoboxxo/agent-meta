#!/bin/bash
# hook: dod-push-check
# version: 1.1.0
# event: PreToolUse
# matcher: Bash
# provider: Claude
# description: Blocks git push on main/master (Branch-Guard) and until tests are green (DoD enforcement)
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

# --- Branch-Guard: block push on main/master ---
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

# Resolve GIT_MAIN_BRANCH: env var > agent-meta.config.json > default "main"
MAIN_BRANCH="${AGENT_META_MAIN_BRANCH:-}"

if [ -z "$MAIN_BRANCH" ]; then
  DIR="$PWD"
  for _ in 1 2 3 4; do
    if [ -f "$DIR/agent-meta.config.json" ]; then
      MAIN_BRANCH=$(python3 -c "import json; c=json.load(open('$DIR/agent-meta.config.json')); print(c.get('variables',{}).get('GIT_MAIN_BRANCH','main'))" 2>/dev/null)
      break
    fi
    DIR="$(dirname "$DIR")"
  done
  MAIN_BRANCH="${MAIN_BRANCH:-main}"
fi

if [ "$CURRENT_BRANCH" = "$MAIN_BRANCH" ] || [ "$CURRENT_BRANCH" = "master" ]; then
  echo "Branch-Guard: Push blocked — you are on '$CURRENT_BRANCH'."
  echo "Create a feature branch first: git checkout -b feat/<topic>"
  echo "Direct pushes to $MAIN_BRANCH are not allowed by DoD policy."
  echo ""
  echo "If this is intentional (release, hotfix), disable the hook temporarily:"
  echo "  Remove dod-push-check from hooks in agent-meta.config.json, re-sync, push, re-enable."
  exit 2
fi

# --- Test-Gate: block push if tests fail ---
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
  echo "DoD-Check: TEST_COMMAND not configured — skipping test gate."
  echo "Set variables.TEST_COMMAND in agent-meta.config.json or"
  echo "export AGENT_META_TEST_COMMAND='<your-test-command>' to enable."
  echo "Push allowed (Branch-Guard passed, no test gate configured)."
  exit 0
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
