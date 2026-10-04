#!/bin/bash
# Scenario assert for 73-continue-prompts-one-sync (issue #802).
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# --validate, so the tree is the run1 output of a config with Continue
# `provider-options.Continue.generate-prompts: true`.
#
# Proves: `sync.py --check` exits rc 0 straight after that FIRST real sync —
# the generated `.continue/prompts/*.md` were previously logged as an
# unconditional WRITE even when byte-identical, so --check reported permanent
# drift until a second sync. This assert fails if a second sync is required.
#
# Exit 0 = assertion holds.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (73-continue-prompts-one-sync): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (73-continue-prompts-one-sync): $*"
    exit 1
}

# Sanity: the feature under test actually produced prompt files.
prompts_count="$(find .continue/prompts -maxdepth 1 -type f -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
[ "$prompts_count" -ge 1 ] || fail "no .continue/prompts/*.md generated (generate-prompts not effective?)"

# The one-sync convergence assertion: --check must be clean NOW, before any
# second sync could mask non-idempotent writers.
check_rc=0
python3 "$REPO_ROOT/scripts/sync.py" --check > check.log 2>&1 || check_rc=$?
[ "$check_rc" -eq 0 ] || {
    cat check.log
    fail "sync.py --check rc=$check_rc after ONE sync (expected one-sync convergence, issue #802)"
}

echo "ASSERT OK (73-continue-prompts-one-sync): --check rc 0 after ONE sync ($prompts_count prompt file(s))"
