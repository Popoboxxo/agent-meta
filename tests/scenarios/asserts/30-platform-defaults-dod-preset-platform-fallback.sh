#!/bin/bash
# Scenario assert for 30-platform-defaults-dod-preset-platform-fallback.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (30-platform-defaults-dod-preset-platform-fallback): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (30-platform-defaults-dod-preset-platform-fallback): $*"
    exit 1
}

[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
grep -q "DoD-Preset: \*\*standard\*\*" CLAUDE.md \
    || fail "CLAUDE.md: expected hacs' platform default dod-preset ('standard') to win, not the old implicit 'full'"
if grep -q "DoD-Preset: \*\*full\*\*" CLAUDE.md; then
    fail "CLAUDE.md: still showing the old implicit 'full' default -- platform dod-preset cascade did not apply"
fi

echo "ASSERT OK (30-platform-defaults-dod-preset-platform-fallback): platform default 'standard' won over the old implicit 'full'"
