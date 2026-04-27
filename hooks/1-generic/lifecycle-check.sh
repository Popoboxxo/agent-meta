#!/bin/bash
# hook: lifecycle-check
# version: 1.0.0
# event: PostToolUse
# matcher: Bash
# provider: Claude
# description: Detects git lifecycle events (tag push, merge, version bump) and writes pending tasks to .claude/pending-tasks.md
# enabled_by_default: false

# Claude Code passes hook context as JSON on stdin.
# PostToolUse hooks receive the tool result — exit code is ignored.

INPUT=$(cat)

# python3 required for JSON parsing
command -v python3 &>/dev/null || exit 0

TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)
EXIT_CODE=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); r=d.get('tool_result',{}); print(r.get('exit_code','0') if isinstance(r,dict) else '0')" 2>/dev/null)

# Only intercept successful Bash tool calls
[ "$TOOL_NAME" = "Bash" ] || exit 0
[ "$EXIT_CODE" = "0" ] || exit 0

# Locate lifecycle_check.py (relative to this hook's location or via AGENT_META_ROOT)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIFECYCLE_PY="$(dirname "$(dirname "$SCRIPT_DIR")")/scripts/lifecycle_check.py"

# Fallback: search for .agent-meta submodule from cwd
if [ ! -f "$LIFECYCLE_PY" ]; then
  LIFECYCLE_PY="$PWD/.agent-meta/scripts/lifecycle_check.py"
fi

[ -f "$LIFECYCLE_PY" ] || exit 0

# ---------------------------------------------------------------------------
# Detect lifecycle event from the git command that just ran
# ---------------------------------------------------------------------------

EVENT=""

# on-release: git push with a tag (git push origin v1.2.3 or git push --tags)
if echo "$COMMAND" | grep -qE 'git push' && \
   echo "$COMMAND" | grep -qE '(--tags?|v[0-9]+\.[0-9]+\.[0-9]+)'; then
  EVENT="on-release"

# on-version-bump-*: commit message contains "bump version to X.Y.Z" or "chore: bump"
elif echo "$COMMAND" | grep -qE 'git commit'; then
  COMMIT_MSG=$(echo "$COMMAND" | grep -oP '(?<=-m ["\x27]).*(?=["\x27])' | head -1)
  if echo "$COMMIT_MSG" | grep -qiE 'bump.*version|version.*bump|chore.*bump'; then
    # Detect patch/minor/major from version numbers in commit message
    # Heuristic: look for X.Y.Z pattern
    VERSION=$(echo "$COMMIT_MSG" | grep -oP '\d+\.\d+\.\d+' | head -1)
    if [ -n "$VERSION" ]; then
      PATCH=$(echo "$VERSION" | cut -d. -f3)
      MINOR=$(echo "$VERSION" | cut -d. -f2)
      MAJOR=$(echo "$VERSION" | cut -d. -f1)
      # Check if previous tag exists to determine bump type
      PREV_TAG=$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1)
      if [ -n "$PREV_TAG" ]; then
        PREV_MAJOR=$(echo "$PREV_TAG" | cut -d. -f1)
        PREV_MINOR=$(echo "$PREV_TAG" | cut -d. -f2)
        if [ "$MAJOR" != "$PREV_MAJOR" ]; then
          EVENT="on-version-bump-major"
        elif [ "$MINOR" != "$PREV_MINOR" ]; then
          EVENT="on-version-bump-minor"
        else
          EVENT="on-version-bump-patch"
        fi
      else
        EVENT="on-version-bump-patch"
      fi
    fi
  fi

# on-merge: git merge command or commit on main after a branch
elif echo "$COMMAND" | grep -qE 'git merge|gh pr merge'; then
  EVENT="on-merge"

# on-commit: any successful git commit (broad catch — only fires if configured)
elif echo "$COMMAND" | grep -qE 'git commit'; then
  EVENT="on-commit"
fi

[ -n "$EVENT" ] || exit 0

# Fire the lifecycle check
python3 "$LIFECYCLE_PY" "$EVENT"

exit 0
