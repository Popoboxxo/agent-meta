#!/bin/bash
# Scenario assert for 56-spec-plan-preset-coupling
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (56-spec-plan-preset-coupling): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (56-spec-plan-preset-coupling): $*"
    exit 1
}

# (a) Positive: no explicit spec-plan-workflow block, but concept-driven's
#     spec-plan-required:true resolves effective_enabled=true.
for rule in spec-plan-workflow brainstorming-gate writing-plans plan-ledger; do
    [ -f ".claude/skills/$rule/SKILL.md" ] \
        || fail "gated rule '$rule' not delivered via preset coupling"
done
for d in docs/specs docs/plans docs/spikes; do
    [ -d "$d" ] || fail "$d not scaffolded via preset coupling"
done
grep -q 'classify → spec → approve → plan → execute' .claude/agents/orchestrator.md \
    || fail "orchestrator phase chain missing via preset coupling"
[ -f "docs/INDEX.md" ] || fail "file-index fallback missing (KE off)"

# (b) Counter-test: rapid-prototyping has spec-plan-required:false and there is
#     no explicit block -> the workflow stays a no-op.
neg_dir="$(mktemp -d)"
mkdir -p "$neg_dir/.meta-config"
printf '%s\n' \
    'agent-meta-version: "1.1.0"' \
    'ai-providers:' \
    '- Claude' \
    'dod-preset: rapid-prototyping' \
    'platforms: []' \
    'rules-preset: lazy' \
    'knowledge-engine:' \
    '  enabled: false' \
    > "$neg_dir/.meta-config/project.yaml"

( cd "$neg_dir" && python3 "$REPO_ROOT/scripts/sync.py" >/dev/null 2>&1 ) \
    || { rm -rf "$neg_dir"; fail "negative (rapid-prototyping) sync failed"; }

for rule in spec-plan-workflow brainstorming-gate writing-plans plan-ledger; do
    [ ! -e "$neg_dir/.claude/skills/$rule/SKILL.md" ] \
        || { rm -rf "$neg_dir"; fail "gated rule '$rule' delivered without preset coupling"; }
done
[ ! -e "$neg_dir/docs/specs" ] \
    || { rm -rf "$neg_dir"; fail "docs/specs scaffolded without preset coupling"; }
if grep -q 'classify → spec → approve → plan → execute' "$neg_dir/.claude/agents/orchestrator.md" 2>/dev/null; then
    rm -rf "$neg_dir"
    fail "orchestrator phase chain rendered without preset coupling"
fi
rm -rf "$neg_dir"

echo "ASSERT OK (56-spec-plan-preset-coupling): concept-driven on, rapid-prototyping off"
