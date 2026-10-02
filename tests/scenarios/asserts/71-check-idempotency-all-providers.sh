#!/bin/bash
# Scenario assert for 71-check-idempotency-all-providers
# (design §6.3, AC-19: run1==run2 + `sync.py --check` rc 0 for all 9 providers).
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# --validate, so the tree is the run1 output. This scenario proves:
#   1. a further sync leaves every generated artifact byte-identical
#      (run1 == run2), and
#   2. `sync.py --check` on the converged tree exits rc 0.
# Volatile log files written by sync itself and the harness log dir are excluded
# from the content hash — they are diagnostics, not generated artifacts.
# Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (71-check-idempotency-all-providers): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (71-check-idempotency-all-providers): $*"
    exit 1
}

# Deterministic content hash of the generated tree (path + bytes), skipping the
# volatile diagnostics that a run rewrites but that are not generated provider
# artifacts: the sync/harness logs and the external-tools drift *reports*
# (`external-tools-drift.md`, the scanner's own warning artifact; it appears on
# the second run because the isolation state files created by the first run are
# only then visible to the scanner). Provider agent/rule/skill/hook artifacts
# are all covered.
tree_hash() {
    find . -type f \
        -not -path './.scenario-logs/*' \
        -not -name '*.log' \
        -not -name 'external-tools-drift.md' \
        -not -name '*.sync-backup-*' \
        -print0 | sort -z | xargs -0 -r sha256sum | sha256sum | cut -d' ' -f1
}

run1_hash="$(tree_hash)"
[ -n "$run1_hash" ] || fail "could not hash the generated tree"

run2_rc=0
python3 "$REPO_ROOT/scripts/sync.py" > run2.log 2>&1 || run2_rc=$?
[ "$run2_rc" -eq 0 ] || { cat run2.log; fail "second sync rc=$run2_rc"; }

run2_hash="$(tree_hash)"
[ "$run1_hash" = "$run2_hash" ] \
    || fail "generated tree changed between sync runs ($run1_hash != $run2_hash)"

check_rc=0
python3 "$REPO_ROOT/scripts/sync.py" --check > check.log 2>&1 || check_rc=$?
[ "$check_rc" -eq 0 ] || { cat check.log; fail "sync.py --check rc=$check_rc (expected clean tree)"; }

echo "ASSERT OK (71-check-idempotency-all-providers): tree byte-identical across syncs ($run1_hash); --check rc 0"
