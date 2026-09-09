#!/bin/bash
# Scenario assert for 09-legacy-config
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (09-legacy-config): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (09-legacy-config): $*"
    exit 1
}

# Expected files/directories for this scenario
[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
[ -d ".claude/agents" ] || fail "agent directory missing for Claude: .claude/agents"

echo "ASSERT OK (09-legacy-config): all marker files present"
