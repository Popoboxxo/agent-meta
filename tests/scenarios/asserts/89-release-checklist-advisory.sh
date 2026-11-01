#!/bin/bash
# Scenario assert for 89-release-checklist-advisory (SPEC-RELEASE-CHECKLIST-2026-10-31).
#
# Contract: cwd = the scenario's temp project dir (the sync output); $1 and env
# REPO_ROOT both carry the agent-meta checkout path. Exit 0 = all assertions
# hold; non-zero = first violated assertion, printed to stdout/stderr.
#
# AC-REL-6/9/11/21-23: advisory renders the full checklist contract (mode
# marker, approval protocol, dry-check marker) plus agent, script and step
# items. The rendered block must not leave a template placeholder behind.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (89-release-checklist-advisory): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (89-release-checklist-advisory): $*"
    exit 1
}

RELEASE_MD=".claude/agents/release.md"
[ -f "$RELEASE_MD" ] || fail "generated file missing: $RELEASE_MD"

# 1. Contract phrases of the rendered checklist block.
for phrase in "CHECKLIST_MODE" "APPROVAL_REQUEST" "APPROVED:" "n/a (nicht ausgeführt)"; do
    grep -qF "$phrase" "$RELEASE_MD" \
        || fail "$RELEASE_MD: checklist contract phrase missing: $phrase"
done

# 2. Every project item reaches the rendered table (agent, script, step).
for item_id in changelog-unreleased schema-valid docker-image-pushed; do
    grep -qF "$item_id" "$RELEASE_MD" \
        || fail "$RELEASE_MD: project checklist item missing: $item_id"
done

# 3. The script item renders its command, the step item its applies-when text.
grep -qF '`python3 scripts/sync.py --validate`' "$RELEASE_MD" \
    || fail "$RELEASE_MD: script item command not rendered"
grep -qF "the project ships a docker image" "$RELEASE_MD" \
    || fail "$RELEASE_MD: step item applies-when text not rendered"

# 4. No unresolved placeholder survives in the rendered agent.
if grep -q "{{" "$RELEASE_MD"; then
    fail "$RELEASE_MD: unresolved '{{' placeholder in generated output"
fi

echo "ASSERT OK (89-release-checklist-advisory): advisory contract + items rendered"
