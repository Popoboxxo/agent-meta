#!/bin/bash
# Scenario assert for 39-conventions-custom-overrides.
#
# The default conventions preset renders the git issue-title format as
# '<type>: <description>'. Overriding conventions.issues.title_format must
# render the custom '[<type>] <description>' form in git.md instead.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (39-conventions-custom-overrides): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (39-conventions-custom-overrides): $*"
    exit 1
}

[ -f ".claude/agents/git.md" ] || fail "generated file missing: .claude/agents/git.md"

grep -q "Issue-Titel-Format:\*\* \`\[<type>\] <description>\`" .claude/agents/git.md \
    || fail "git.md: expected custom issue-title format '[<type>] <description>' from conventions override, not found"

# The default preset's plain '<type>: <description>' form must be gone.
grep -q "Issue-Titel-Format:\*\* \`<type>: <description>\`" .claude/agents/git.md \
    && fail "git.md: default preset issue-title format still present despite override"

echo "ASSERT OK (39-conventions-custom-overrides): custom issue-title format rendered over preset"
