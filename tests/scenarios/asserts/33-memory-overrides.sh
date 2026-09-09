#!/bin/bash
# Scenario assert for 33-memory-overrides.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (33-memory-overrides): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (33-memory-overrides): $*"
    exit 1
}

[ -f ".claude/agents/developer.md" ] || fail "generated file missing: .claude/agents/developer.md"
[ -f ".claude/agents/tester.md" ] || fail "generated file missing: .claude/agents/tester.md"

# developer has an explicit memory-overrides entry -> 'local'
grep -q "^memory: local$" .claude/agents/developer.md \
    || fail "developer.md: expected 'memory: local' (from memory-overrides), not found"

# tester has no override and no role-default -> falls back to memory.default_scope 'project'
grep -q "^memory: project$" .claude/agents/tester.md \
    || fail "tester.md: expected 'memory: project' (from memory.default_scope), not found"

echo "ASSERT OK (33-memory-overrides): per-role override wins, others fall back to global default_scope"
