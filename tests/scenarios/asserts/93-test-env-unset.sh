#!/bin/bash
# Scenario assert for 93-test-env-unset (SPEC-TEST-ENVIRONMENTS-2026-10-31).
#
# Contract: cwd = the scenario's temp project dir (the sync output); $1 and env
# REPO_ROOT both carry the agent-meta checkout path. Exit 0 = all assertions
# hold; non-zero = first violated assertion, printed to stdout/stderr.
#
# AC-ENV-16 / AC-ENV-1: without a test-environments block the six gated role
# templates stay byte-clean -- no block, no placeholder residue, no protocol.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (93-test-env-unset): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (93-test-env-unset): $*"
    exit 1
}

ROLES="tester e2e-tester developer docker devops-engineer test-executor"

for role in $ROLES; do
    md=".claude/agents/$role.md"
    [ -f "$md" ] || fail "generated file missing: $md"

    if grep -qF "Test environments" "$md"; then
        fail "$md: test environment block rendered despite an unconfigured project"
    fi
    if grep -qF "TEST_ENVIRONMENT" "$md"; then
        fail "$md: TEST_ENVIRONMENT placeholder residue"
    fi
    if grep -qF "{{TEST_ENV" "$md"; then
        fail "$md: unresolved {{TEST_ENV placeholder"
    fi
done

approval_count="$(grep -hF "APPROVAL_REQUEST" .claude/agents/tester.md .claude/agents/e2e-tester.md \
    .claude/agents/developer.md .claude/agents/docker.md .claude/agents/devops-engineer.md \
    .claude/agents/test-executor.md | wc -l | tr -d ' ')"
[ "$approval_count" = "0" ] \
    || fail "approval protocol rendered $approval_count time(s) despite an unconfigured project"

echo "ASSERT OK (93-test-env-unset): unconfigured project stays byte-clean"
