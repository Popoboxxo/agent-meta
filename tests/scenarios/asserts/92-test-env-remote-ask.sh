#!/bin/bash
# Scenario assert for 92-test-env-remote-ask (SPEC-TEST-ENVIRONMENTS-2026-10-31).
#
# Contract: cwd = the scenario's temp project dir (the sync output); $1 and env
# REPO_ROOT both carry the agent-meta checkout path. Exit 0 = all assertions
# hold; non-zero = first violated assertion, printed to stdout/stderr.
#
# AC-ENV-16 / AC-ENV-8 / AC-ENV-6 / AC-ENV-11: a remote HA dev target with
# remote-access ask renders the approval protocol and references the secret by
# name only; no network permission pattern is generated.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (92-test-env-remote-ask): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (92-test-env-remote-ask): $*"
    exit 1
}

ROLES="tester e2e-tester developer docker devops-engineer test-executor"

for role in $ROLES; do
    md=".claude/agents/$role.md"
    [ -f "$md" ] || fail "generated file missing: $md"

    grep -qF "APPROVAL_REQUEST: env=<name>; action=<read|deploy: action>" "$md" \
        || fail "$md: ask approval request contract missing"
    grep -qF "APPROVED: env=<name>; action=<action>" "$md" \
        || fail "$md: ask approval grant contract missing"
    grep -qF '`${HA_DEV_TOKEN}`' "$md" \
        || fail "$md: secret is not referenced by variable name"
done

# The secret value never lives in project.yaml; only the generated env script
# carries the [SECRET] marker (value injected from the shell at source time).
ENV_SH=".meta-config/env.sh"
[ -f "$ENV_SH" ] || fail "generated file missing: $ENV_SH"
grep -qF "HA_DEV_TOKEN" "$ENV_SH" || fail "$ENV_SH: HA_DEV_TOKEN entry missing"
grep -qF "[SECRET]" "$ENV_SH" || fail "$ENV_SH: [SECRET] marker missing"

# NZ8: test environments never widen the permission surface (no ssh/curl).
SETTINGS=".claude/settings.json"
[ -f "$SETTINGS" ] || fail "generated file missing: $SETTINGS"
if grep -Eq 'ssh|curl' "$SETTINGS"; then
    fail "$SETTINGS: network permission pattern (ssh/curl) generated"
fi

echo "ASSERT OK (92-test-env-remote-ask): ask protocol + secret reference, no permission widening"
