#!/bin/bash
# Scenario assert for 55-spec-plan-ke-off-fallback
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (55-spec-plan-ke-off-fallback): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (55-spec-plan-ke-off-fallback): $*"
    exit 1
}

# (a) KE off => no knowledge bundle is scaffolded.
[ ! -e "knowledge" ] || fail "knowledge bundle created although knowledge-engine.enabled=false"

# (b) Declared index.mode knowledge-engine degrades to the file-index fallback.
[ -f "docs/INDEX.md" ] || fail "file-index fallback docs/INDEX.md missing"
grep -q 'File-based index fallback' docs/INDEX.md || fail "fallback index skeleton content missing"

# (c) Workflow active while the KE is off: gated rules + scaffolds.
for rule in spec-plan-workflow brainstorming-gate writing-plans plan-ledger; do
    [ -f ".claude/skills/$rule/SKILL.md" ] || fail "gated rule '$rule' not delivered"
done
for d in docs/specs docs/plans docs/spikes; do
    [ -d "$d" ] || fail "$d not scaffolded"
done

echo "ASSERT OK (55-spec-plan-ke-off-fallback): KE off degrades to file-index"
