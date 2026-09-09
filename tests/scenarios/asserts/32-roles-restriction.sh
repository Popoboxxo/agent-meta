#!/bin/bash
# Scenario assert for 32-roles-restriction.
#
# Contract (see tests/scenarios/run.sh header): cwd = the scenario's temp
# project dir (the sync output); $1 and env REPO_ROOT both carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (32-roles-restriction): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (32-roles-restriction): $*"
    exit 1
}

[ -f ".claude/agents/developer.md" ] || fail "whitelisted role missing: .claude/agents/developer.md"
[ -f ".claude/agents/tester.md" ] || fail "whitelisted role missing: .claude/agents/tester.md"

# A standard role NOT in the whitelist must not be generated.
[ ! -f ".claude/agents/code-reviewer.md" ] \
    || fail "non-whitelisted role code-reviewer.md was generated despite roles: [developer, tester]"
[ ! -f ".claude/agents/orchestrator.md" ] \
    || fail "non-whitelisted role orchestrator.md was generated despite roles: [developer, tester]"

echo "ASSERT OK (32-roles-restriction): only whitelisted roles (developer, tester) generated"
