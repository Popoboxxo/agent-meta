#!/bin/bash
# Scenario assert for 10-model-tiers
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (10-model-tiers): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (10-model-tiers): $*"
    exit 1
}

# Expected files/directories for this scenario
[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
[ -d ".claude/agents" ] || fail "agent directory missing for Claude: .claude/agents"
[ -f "AGENTS.md" ] || fail "root provider file missing: AGENTS.md"
[ -d ".gemini/agents" ] || fail "agent directory missing for Gemini: .gemini/agents"

echo "ASSERT OK (10-model-tiers): all marker files present"
