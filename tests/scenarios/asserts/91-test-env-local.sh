#!/bin/bash
# Scenario assert for 91-test-env-local (SPEC-TEST-ENVIRONMENTS-2026-10-31).
#
# Contract: cwd = the scenario's temp project dir (the sync output); $1 and env
# REPO_ROOT both carry the agent-meta checkout path. Exit 0 = all assertions
# hold; non-zero = first violated assertion, printed to stdout/stderr.
#
# AC-ENV-16 / AC-ENV-7: a local-only target renders the "## Test environments"
# table into every gated role, but the remote approval protocol never appears.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (91-test-env-local): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (91-test-env-local): $*"
    exit 1
}

ROLES="tester e2e-tester developer docker devops-engineer test-executor"

for role in $ROLES; do
    md=".claude/agents/$role.md"
    [ -f "$md" ] || fail "generated file missing: $md"

    grep -qF "## Test environments" "$md" \
        || fail "$md: test environment block missing"
    grep -qF "| sharkord-local | local |" "$md" \
        || fail "$md: local-only target row missing"

    if grep -qF "APPROVAL_REQUEST: env=" "$md"; then
        fail "$md: remote approval protocol rendered for a local-only target"
    fi
done

echo "ASSERT OK (91-test-env-local): local target rendered, no remote approval protocol"
