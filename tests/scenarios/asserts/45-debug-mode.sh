#!/bin/bash
# Scenario assert for 45-debug-mode.
#
# With debug-mode: true, sync injects the debug-mode block (marker
# '<!-- agent-meta:debug-mode -->') into every generated agent. With the
# default false, no agent file carries it.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (45-debug-mode): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (45-debug-mode): $*"
    exit 1
}

[ -f ".claude/agents/developer.md" ] || fail "generated file missing: .claude/agents/developer.md"

grep -q "agent-meta:debug-mode" .claude/agents/developer.md \
    || fail "developer.md: expected debug-mode block marker '<!-- agent-meta:debug-mode -->', not found"

echo "ASSERT OK (45-debug-mode): debug-mode block injected into generated agent"
