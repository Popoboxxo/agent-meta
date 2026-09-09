#!/bin/bash
# Scenario assert for 23-platform-defaults-sharkord-explicit-override.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (23-platform-defaults-sharkord-explicit-override): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (23-platform-defaults-sharkord-explicit-override): $*"
    exit 1
}

[ -f ".claude/agents/tester.md" ] || fail "generated file missing: .claude/agents/tester.md"
grep -q "custom-sharkord-test-cmd" .claude/agents/tester.md \
    || fail "tester.md: explicit project TEST_COMMANDS not rendered"
if grep -q "docker compose run --rm test" .claude/agents/tester.md; then
    fail "tester.md: sharkord's platform-default TEST_COMMANDS leaked through despite an explicit project override"
fi

echo "ASSERT OK (23-platform-defaults-sharkord-explicit-override): explicit override replaced the platform default completely"
