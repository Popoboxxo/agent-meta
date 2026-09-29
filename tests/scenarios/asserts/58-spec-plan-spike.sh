#!/bin/bash
# Scenario assert for 58-spec-plan-spike
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (58-spec-plan-spike): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (58-spec-plan-spike): $*"
    exit 1
}

# (a) The gated master rule documents the Spike classification alongside the
#     Bounded/Architectural classes.
master=".claude/skills/spec-plan-workflow/SKILL.md"
[ -f "$master" ] || fail "gated master rule missing"
grep -q 'Spike' "$master" || fail "master rule does not document the Spike class"
grep -q 'Bounded' "$master" || fail "master rule does not document the Bounded class"
grep -q 'Architectural' "$master" || fail "master rule does not document the Architectural class"

# (b) The generated explorer carries the read-only Spike mode with its
#     disposable-code marker and spike-doc path.
explorer=".claude/agents/explorer.md"
[ -f "$explorer" ] || fail "explorer agent missing"
grep -q 'Spike-Modus' "$explorer" || fail "explorer spike mode missing"
grep -q 'SPIKE-CODE — nicht mergen' "$explorer" || fail "explorer disposable-code marker missing"
grep -q 'docs/spikes/YYYY-MM-DD-issue-<n>-<topic>-spike.md' "$explorer" \
    || fail "explorer spike-doc path missing"
grep -qi 'read-only' "$explorer" || fail "explorer spike mode read-only constraint missing"

# (c) The spec->plan chain is wired: planner mandates pipeline_stages, the
#     specifier carries the trace anchor.
grep -q 'pipeline_stages' .claude/agents/planner.md || fail "planner pipeline_stages mandate missing"
grep -q 'Trace-Anker' .claude/agents/concept-specifier.md || fail "concept-specifier trace anchor missing"

echo "ASSERT OK (58-spec-plan-spike): spike route and explorer spike mode visible"
