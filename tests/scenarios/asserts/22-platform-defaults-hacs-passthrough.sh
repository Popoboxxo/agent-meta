#!/bin/bash
# Scenario assert for 22-platform-defaults-hacs-passthrough.
#
# Contract (see tests/scenarios/run.sh header): cwd = the scenario's temp
# project dir (the sync output); $1 and env REPO_ROOT both carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (22-platform-defaults-hacs-passthrough): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (22-platform-defaults-hacs-passthrough): $*"
    exit 1
}

[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
grep -q "Plattform:\*\* Home Assistant Custom Component" CLAUDE.md \
    || fail "CLAUDE.md: hacs' platform default PLATFORM not rendered"
grep -q "DoD-Preset: \*\*standard\*\*" CLAUDE.md \
    || fail "CLAUDE.md: hacs' platform default dod-preset 'standard' not rendered"

[ -f ".claude/agents/tester.md" ] || fail "generated file missing: .claude/agents/tester.md"
grep -q "pytest tests/ --cov" .claude/agents/tester.md \
    || fail "tester.md: hacs' platform default TEST_COMMANDS not rendered"

echo "ASSERT OK (22-platform-defaults-hacs-passthrough): hacs platform defaults resolved unmodified"
