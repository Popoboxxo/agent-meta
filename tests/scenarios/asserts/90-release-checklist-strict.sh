#!/bin/bash
# Scenario assert for 90-release-checklist-strict (SPEC-RELEASE-CHECKLIST-2026-10-31).
#
# Contract: cwd = the scenario's temp project dir (the sync output); $1 and env
# REPO_ROOT both carry the agent-meta checkout path. Exit 0 = all assertions
# hold; non-zero = first violated assertion, printed to stdout/stderr.
#
# AC-REL-7/8/24/25: strict renders the boundary wording and the
# required_failed -> STATUS failed mapping, and lists the project item.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (90-release-checklist-strict): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (90-release-checklist-strict): $*"
    exit 1
}

RELEASE_MD=".claude/agents/release.md"
[ -f "$RELEASE_MD" ] || fail "generated file missing: $RELEASE_MD"

# 1. Strict is a prompt/convention boundary -- never a security guarantee.
grep -qF "Prompt-/Konventions-Boundary" "$RELEASE_MD" \
    || fail "$RELEASE_MD: strict boundary wording missing"

# 2. Strict maps a failing required item to STATUS: failed.
grep -qF "required_failed" "$RELEASE_MD" \
    || fail "$RELEASE_MD: required_failed summary marker missing"
grep -qF "STATUS: failed" "$RELEASE_MD" \
    || fail "$RELEASE_MD: STATUS: failed mapping missing"

# 3. The project item is listed.
grep -qF "docker-image-pushed" "$RELEASE_MD" \
    || fail "$RELEASE_MD: project checklist item missing: docker-image-pushed"

echo "ASSERT OK (90-release-checklist-strict): strict boundary + failure mapping rendered"
