#!/bin/bash
# Scenario assert for 07-new-providers
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (07-new-providers): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (07-new-providers): $*"
    exit 1
}

# Expected files/directories for this scenario
[ -f "AGENTS.md" ] || fail "root provider file missing: AGENTS.md"
[ -d ".agents" ] || fail "agent directory missing for Codex: .agents"
[ -d ".zcode/agents" ] || fail "agent directory missing for ZCode: .zcode/agents"
[ -d ".kimi-code/agents" ] || fail "agent directory missing for KimiCode: .kimi-code/agents"

echo "ASSERT OK (07-new-providers): all marker files present"
