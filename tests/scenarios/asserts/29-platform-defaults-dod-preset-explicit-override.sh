#!/bin/bash
# Scenario assert for 29-platform-defaults-dod-preset-explicit-override.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (29-platform-defaults-dod-preset-explicit-override): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (29-platform-defaults-dod-preset-explicit-override): $*"
    exit 1
}

[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
grep -q "DoD-Preset: \*\*rapid-prototyping\*\*" CLAUDE.md \
    || fail "CLAUDE.md: expected the explicit project.yaml dod-preset ('rapid-prototyping') to win over hacs' platform default ('standard')"

echo "ASSERT OK (29-platform-defaults-dod-preset-explicit-override): explicit project dod-preset won over the platform default"
