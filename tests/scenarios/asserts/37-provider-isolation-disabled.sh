#!/bin/bash
# Scenario assert for 37-provider-isolation-disabled.
#
# With two active providers and NO provider-isolation key, sync writes a
# cross-provider deny (e.g. '.gemini/**') into .claude/settings.json. Setting
# provider-isolation: disabled must suppress exactly that managed deny entry.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (37-provider-isolation-disabled): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (37-provider-isolation-disabled): $*"
    exit 1
}

[ -f ".claude/settings.json" ] || fail "expected .claude/settings.json to exist"

# The cross-provider isolation glob for the OTHER active provider (.gemini)
# must be absent from the deny list when isolation is disabled.
grep -q "\.gemini/\*\*" .claude/settings.json \
    && fail "settings.json: '.gemini/**' deny present although provider-isolation is disabled"

echo "ASSERT OK (37-provider-isolation-disabled): no cross-provider deny entry generated"
