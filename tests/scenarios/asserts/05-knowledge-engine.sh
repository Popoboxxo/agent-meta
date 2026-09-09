#!/bin/bash
# Scenario assert for 05-knowledge-engine
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (05-knowledge-engine): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (05-knowledge-engine): $*"
    exit 1
}

# Expected files/directories for this scenario
[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
[ -d ".claude/agents" ] || fail "agent directory missing for Claude: .claude/agents"
[ -d "knowledge" ] || fail "knowledge engine bundle directory missing: knowledge"
[ -f "knowledge/schema.md" ] || fail "knowledge engine schema missing"
[ -d "knowledge/wiki" ] || fail "knowledge engine wiki directory missing"

echo "ASSERT OK (05-knowledge-engine): all marker files present"
