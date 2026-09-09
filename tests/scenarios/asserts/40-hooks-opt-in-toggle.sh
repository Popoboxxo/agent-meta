#!/bin/bash
# Scenario assert for 40-hooks-opt-in-toggle.
#
# Two-gate hook model: scripts are always copied into .claude/hooks/, but
# registration in .claude/settings.json is per-hook opt-in. Disabling the
# default-on orchestrator-guard removes its settings.json registration;
# enabling the opt-in dod-push-check adds one.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (40-hooks-opt-in-toggle): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (40-hooks-opt-in-toggle): $*"
    exit 1
}

[ -f ".claude/settings.json" ] || fail "expected .claude/settings.json to exist"

# Opt-in hook explicitly enabled -> registered.
grep -q "dod-push-check" .claude/settings.json \
    || fail "settings.json: expected dod-push-check registration (enabled: true), not found"

# Default-on hook explicitly disabled -> NOT registered.
grep -q "orchestrator-guard" .claude/settings.json \
    && fail "settings.json: orchestrator-guard still registered despite enabled: false"

# Scripts are always synced regardless of registration.
[ -f ".claude/hooks/orchestrator-guard.sh" ] \
    || fail "hook script .claude/hooks/orchestrator-guard.sh missing (scripts must always sync)"

echo "ASSERT OK (40-hooks-opt-in-toggle): registration honours per-hook enabled flags, script still synced"
