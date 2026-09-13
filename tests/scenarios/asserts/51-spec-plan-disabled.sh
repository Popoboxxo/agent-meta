#!/bin/bash
# Scenario assert for 51-spec-plan-disabled
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (51-spec-plan-disabled): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (51-spec-plan-disabled): $*"
    exit 1
}

# (a) No gated rule is delivered, even though rules-preset: lazy would carry
#     them as skill files (channel: skill) when the workflow were active.
for rule in spec-plan-workflow brainstorming-gate writing-plans plan-ledger; do
    [ ! -e ".claude/skills/$rule/SKILL.md" ] \
        || fail "gated rule '$rule' delivered while spec-plan-workflow.enabled=false"
done

# (b) No scaffolding: configured paths stay untouched (the explicit bool wins
#     over the concept-driven preset's spec-plan-required: true).
for d in docs/specs docs/plans docs/spikes; do
    [ ! -e "$d" ] || fail "$d scaffolded while disabled"
done
[ ! -e "docs/INDEX.md" ] || fail "file-index fallback written while disabled"

# (c) Conditional flags are off: the orchestrator phase chain and the
#     use-orchestrator gate are stripped, no raw variable leaks.
[ -f ".claude/agents/orchestrator.md" ] || fail ".claude/agents/orchestrator.md missing"
grep -q 'classify → spec → approve → plan → execute' .claude/agents/orchestrator.md \
    && fail "orchestrator phase chain rendered while disabled"
[ -f ".claude/rules/use-orchestrator.md" ] || fail ".claude/rules/use-orchestrator.md missing"
grep -q 'Spec/Plan-Gate' .claude/rules/use-orchestrator.md \
    && fail "use-orchestrator spec/plan gate rendered while disabled"
if grep -Rq 'SPEC_PLAN_WORKFLOW_ENABLED' .claude/ 2>/dev/null; then
    fail "unsubstituted SPEC_PLAN_WORKFLOW_ENABLED leaked into generated output"
fi

# (d) Pipeline gate off: the dod_flag-guarded 'approve' stage is not rendered.
[ -f ".claude/pipeline-details/concept-driven-dev.md" ] \
    || fail "concept-driven-dev pipeline detail missing"
grep -q "Abnahme erforderlich vor Stage 'approve'" .claude/pipeline-details/concept-driven-dev.md \
    && fail "approval gate rendered while disabled"

echo "ASSERT OK (51-spec-plan-disabled): hard no-op confirmed"
