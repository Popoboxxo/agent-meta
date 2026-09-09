#!/bin/bash
# Scenario assert for 13-status-table
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (13-status-table): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (13-status-table): $*"
    exit 1
}

# Expected files/directories for this scenario
[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
[ -d ".claude/agents" ] || fail "agent directory missing for Claude: .claude/agents"
[ -f "AGENTS.md" ] || fail "root provider file missing: AGENTS.md"
[ -d ".gemini/agents" ] || fail "agent directory missing for Gemini: .gemini/agents"
[ -d ".opencode/agents" ] || fail "agent directory missing for Opencode: .opencode/agents"

echo "ASSERT OK (13-status-table): all marker files present"
