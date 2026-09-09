#!/bin/bash
# Scenario assert for 27-platform-defaults-additive-three-platforms.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (27-platform-defaults-additive-three-platforms): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (27-platform-defaults-additive-three-platforms): $*"
    exit 1
}

[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
grep -q "Python, ruff, mypy --strict; TypeScript, ESLint, Prettier" CLAUDE.md \
    || fail "CLAUDE.md: expected CODE_CONVENTIONS concatenation (hacs; sharkord, in list order, '; '-joined) not found"

echo "ASSERT OK (27-platform-defaults-additive-three-platforms): additive field concatenated only the 2 of 3 platforms that set it, in list order"
