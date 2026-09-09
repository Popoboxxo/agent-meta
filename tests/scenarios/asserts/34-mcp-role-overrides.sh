#!/bin/bash
# Scenario assert for 34-mcp-role-overrides.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (34-mcp-role-overrides): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (34-mcp-role-overrides): $*"
    exit 1
}

[ -f ".claude/agents/developer.md" ] || fail "generated file missing: .claude/agents/developer.md"
[ -f ".claude/agents/git.md" ] || fail "generated file missing: .claude/agents/git.md"

# developer got an mcp-role-overrides entry for playwright -> namespaced tools bound.
grep -q "mcp__playwright__" .claude/agents/developer.md \
    || fail "developer.md: expected playwright MCP tools (mcp__playwright__*) from mcp-role-overrides, not found"

# git has no override and no playwright default -> no playwright tools leak in.
grep -q "mcp__playwright__" .claude/agents/git.md \
    && fail "git.md: playwright MCP tools present although git has no mcp-role-overrides entry"

echo "ASSERT OK (34-mcp-role-overrides): playwright tools bound to developer only"
