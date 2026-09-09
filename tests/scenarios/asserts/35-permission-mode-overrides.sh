#!/bin/bash
# Scenario assert for 35-permission-mode-overrides.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (35-permission-mode-overrides): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (35-permission-mode-overrides): $*"
    exit 1
}

[ -f ".claude/agents/developer.md" ] || fail "generated file missing: .claude/agents/developer.md"
[ -f ".claude/agents/tester.md" ] || fail "generated file missing: .claude/agents/tester.md"

# developer got an explicit permission-mode-overrides entry.
grep -q "^permissionMode: acceptEdits$" .claude/agents/developer.md \
    || fail "developer.md: expected 'permissionMode: acceptEdits' from override, not found"

# tester has no override and no role-default permission_mode -> no field injected.
grep -q "^permissionMode:" .claude/agents/tester.md \
    && fail "tester.md: unexpected permissionMode field although tester has no override/default"

echo "ASSERT OK (35-permission-mode-overrides): permissionMode injected for developer only"
