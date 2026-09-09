#!/bin/bash
# Scenario assert for 43-tier-overrides.
#
# tester's role-default tier is 'fast' (-> claude-haiku). tier-overrides lifts
# it to 'powerful' (-> claude-opus). developer has no override and keeps its
# own default tier, proving the override is role-scoped.
#
# (Replaces the originally-planned 'backup:' scenario: backup config only
# drives the --backup CLI path and produces no footprint during a normal
# sync, so it is not observable via this scenario harness — see registry.md.)
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (43-tier-overrides): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (43-tier-overrides): $*"
    exit 1
}

[ -f ".claude/agents/tester.md" ] || fail "generated file missing: .claude/agents/tester.md"
[ -f ".claude/agents/developer.md" ] || fail "generated file missing: .claude/agents/developer.md"

# tester lifted to the 'powerful' tier -> claude-opus model id.
grep -q "^model: claude-opus" .claude/agents/tester.md \
    || fail "tester.md: expected a claude-opus model from tier-overrides (powerful), not found"

# developer keeps its own default tier -> not the opus/powerful model.
grep -q "^model: claude-opus" .claude/agents/developer.md \
    && fail "developer.md: got a claude-opus model although it has no tier-override"

echo "ASSERT OK (43-tier-overrides): tier override applied to tester only"
