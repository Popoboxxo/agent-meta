#!/bin/bash
# Scenario assert for 26-platform-defaults-order-sharkord-hacs.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (26-platform-defaults-order-sharkord-hacs): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (26-platform-defaults-order-sharkord-hacs): $*"
    exit 1
}

[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
grep -q "Plattform:\*\* Home Assistant Custom Component" CLAUDE.md \
    || fail "CLAUDE.md: expected the LAST platform in the list (hacs, now swapped last) to win for PLATFORM"
if grep -q "Plattform:\*\* Sharkord Plugin SDK" CLAUDE.md; then
    fail "CLAUDE.md: sharkord's PLATFORM value leaked through despite hacs being listed later"
fi

echo "ASSERT OK (26-platform-defaults-order-sharkord-hacs): swapping the order flipped the winner, confirming order sensitivity"
