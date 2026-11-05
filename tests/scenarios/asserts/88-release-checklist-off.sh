#!/bin/bash
# Scenario assert for 88-release-checklist-off (SPEC-RELEASE-CHECKLIST-2026-10-31).
#
# Contract: cwd = the scenario's temp project dir (the sync output); $1 and env
# REPO_ROOT both carry the agent-meta checkout path. Exit 0 = all assertions
# hold; non-zero = first violated assertion, printed to stdout/stderr.
#
# AC-REL-1: `mode: off` must be a hard no-op -- release.md carries no
# CHECKLIST_MODE / RELEASE_CHECKLIST residue and is byte-identical to the
# release.md generated from the same config WITHOUT the release-checklist block.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (88-release-checklist-off): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (88-release-checklist-off): $*"
    exit 1
}

RELEASE_MD=".claude/agents/release.md"
[ -f "$RELEASE_MD" ] || fail "generated file missing: $RELEASE_MD"

# 1. No checklist block leaks into the generated release agent.
if grep -q "CHECKLIST_MODE" "$RELEASE_MD"; then
    fail "$RELEASE_MD: CHECKLIST_MODE rendered despite mode: off"
fi
if grep -q "RELEASE_CHECKLIST" "$RELEASE_MD"; then
    fail "$RELEASE_MD: RELEASE_CHECKLIST residue despite mode: off"
fi

# 2. Second sync of the same config WITHOUT the release-checklist block must
#    produce a byte-identical release.md (block absence == mode off).
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
mkdir -p "$tmp_dir/.meta-config"
awk '
    /^release-checklist:/ { skip = 1; next }
    skip && /^[^[:space:]]/ { skip = 0 }
    !skip { print }
' .meta-config/project.yaml > "$tmp_dir/.meta-config/project.yaml"

if grep -q "^release-checklist:" "$tmp_dir/.meta-config/project.yaml"; then
    fail "failed to strip the release-checklist block from the reference config"
fi

( cd "$tmp_dir" && python3 "$REPO_ROOT/scripts/sync.py" >sync.log 2>&1 )
rc=$?
[ "$rc" = "0" ] || fail "reference sync (without the block) failed with rc=$rc"

[ -f "$tmp_dir/$RELEASE_MD" ] || fail "reference sync produced no $RELEASE_MD"
cmp -s "$RELEASE_MD" "$tmp_dir/$RELEASE_MD" \
    || fail "$RELEASE_MD differs between mode: off and an absent release-checklist block"

echo "ASSERT OK (88-release-checklist-off): mode off is a byte-identical no-op"
