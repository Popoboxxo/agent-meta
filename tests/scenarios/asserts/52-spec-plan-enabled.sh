#!/bin/bash
# Scenario assert for 52-spec-plan-enabled
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (52-spec-plan-enabled): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (52-spec-plan-enabled): $*"
    exit 1
}

# (a) All four gated rules are delivered through the lazy skill channel.
for rule in spec-plan-workflow brainstorming-gate writing-plans plan-ledger; do
    [ -f ".claude/skills/$rule/SKILL.md" ] \
        || fail "gated rule '$rule' not delivered while enabled"
done

# (b) The configured spec/plan/spike paths are scaffolded with a .gitkeep.
for d in docs/specs docs/plans docs/spikes; do
    [ -d "$d" ] || fail "$d not scaffolded while enabled"
    [ -f "$d/.gitkeep" ] || fail "$d/.gitkeep missing"
done

# (c) effective spec-plan-enabled == true: orchestrator phase chain, the
#     dod_flag-guarded pipeline approval stage and the use-orchestrator gate.
grep -q 'classify → spec → approve → plan → execute' .claude/agents/orchestrator.md \
    || fail "orchestrator phase chain missing while enabled"
grep -q "Abnahme erforderlich vor Stage 'approve'" .claude/pipeline-details/concept-driven-dev.md \
    || fail "pipeline approval gate missing while enabled"
grep -q 'Spec/Plan-Gate' .claude/rules/use-orchestrator.md \
    || fail "use-orchestrator spec/plan gate missing while enabled"

# (d) KE is active and mode stays knowledge-engine: the KE index exists and no
#     file-index fallback is written.
[ -f "knowledge/wiki/index.md" ] || fail "KE index.md missing although knowledge-engine.enabled=true"
[ ! -e "docs/INDEX.md" ] || fail "file-index fallback written although KE index is authoritative"

echo "ASSERT OK (52-spec-plan-enabled): rules, scaffolding and flags active"
