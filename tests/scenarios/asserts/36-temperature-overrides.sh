#!/bin/bash
# Scenario assert for 36-temperature-overrides.
#
# Temperature is only materialised into the Opencode-native agent frontmatter
# (Claude's Markdown frontmatter carries no temperature field), so this
# scenario runs an Opencode provider and asserts against .opencode/agents/.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (36-temperature-overrides): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (36-temperature-overrides): $*"
    exit 1
}

[ -f ".opencode/agents/developer.md" ] || fail "generated file missing: .opencode/agents/developer.md"
[ -f ".opencode/agents/git.md" ] || fail "generated file missing: .opencode/agents/git.md"

# developer got an explicit temperature-overrides value.
grep -q "^temperature: 0.33$" .opencode/agents/developer.md \
    || fail "developer.md: expected 'temperature: 0.33' from override, not found"

# git has no override and no role-default temperature -> no field.
grep -q "^temperature:" .opencode/agents/git.md \
    && fail "git.md: unexpected temperature field although git has no override/default"

echo "ASSERT OK (36-temperature-overrides): temperature 0.33 rendered for developer only"
