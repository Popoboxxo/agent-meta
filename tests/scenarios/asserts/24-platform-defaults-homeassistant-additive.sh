#!/bin/bash
# Scenario assert for 24-platform-defaults-homeassistant-additive.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (24-platform-defaults-homeassistant-additive): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (24-platform-defaults-homeassistant-additive): $*"
    exit 1
}

[ -f ".claude/agents/tester.md" ] || fail "generated file missing: .claude/agents/tester.md"
grep -q "hass --script check_config && pytest tests/test_automations.py" .claude/agents/tester.md \
    || fail "tester.md: expected concatenated TEST_COMMANDS ('hass --script check_config && pytest tests/test_automations.py') not found"

echo "ASSERT OK (24-platform-defaults-homeassistant-additive): platform default + project '+' override concatenated with '&&'"
