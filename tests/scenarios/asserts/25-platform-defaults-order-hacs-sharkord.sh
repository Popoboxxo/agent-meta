#!/bin/bash
# Scenario assert for 25-platform-defaults-order-hacs-sharkord.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (25-platform-defaults-order-hacs-sharkord): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (25-platform-defaults-order-hacs-sharkord): $*"
    exit 1
}

[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
grep -q "Plattform:\*\* Sharkord Plugin SDK" CLAUDE.md \
    || fail "CLAUDE.md: expected the LAST platform in the list (sharkord) to win for PLATFORM"
if grep -q "Plattform:\*\* Home Assistant Custom Component" CLAUDE.md; then
    fail "CLAUDE.md: hacs' PLATFORM value leaked through despite sharkord being listed later"
fi

echo "ASSERT OK (25-platform-defaults-order-hacs-sharkord): last-platform-wins confirmed for [hacs, sharkord]"
