#!/bin/bash
# Scenario assert for 42-external-skills-gitignore.
#
# The .gitignore skill entry is pure config (approved + enabled +
# gitignore: true) and is emitted independently of whether the skill repo
# is cloned, so this assertion is deterministic and offline.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (42-external-skills-gitignore): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (42-external-skills-gitignore): $*"
    exit 1
}

[ -f ".gitignore" ] || fail "expected .gitignore to exist"

grep -q "\.claude/skills/reqogniloom-change-manager/" .gitignore \
    || fail ".gitignore: expected managed entry '.claude/skills/reqogniloom-change-manager/', not found"

echo "ASSERT OK (42-external-skills-gitignore): approved+enabled skill dir added to .gitignore"
