#!/bin/bash
# Scenario assert for 54-spec-plan-external-override
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (54-spec-plan-external-override): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (54-spec-plan-external-override): $*"
    exit 1
}

# (a) external-system-override.enabled=true must skip EVERY KE write path, even
#     though knowledge-engine.enabled=true (no bundle directory at all).
[ ! -e "knowledge" ] || fail "knowledge bundle written despite external-system-override"

# (b) The file-index fallback takes over (index.mode knowledge-engine would
#     otherwise stay KE).
[ -f "docs/INDEX.md" ] || fail "file-index fallback docs/INDEX.md missing"
grep -q 'File-based index fallback' docs/INDEX.md || fail "fallback index skeleton content missing"

# (c) The workflow stays fully active: gated rules delivered.
for rule in spec-plan-workflow brainstorming-gate writing-plans plan-ledger; do
    [ -f ".claude/skills/$rule/SKILL.md" ] \
        || fail "gated rule '$rule' not delivered"
done

echo "ASSERT OK (54-spec-plan-external-override): KE writes skipped, file-index fallback active"
