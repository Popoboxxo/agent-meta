#!/bin/bash
# Scenario assert for 20-auto-commit-custom (issue #694).
#
# Contract (see tests/scenarios/run.sh header): cwd = the scenario's temp
# project dir (the sync output); $1 and env REPO_ROOT both carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
#
# Verified expectations -- derived from the framework code, not guessed:
#   Authority/eligibility (scripts/lib/auto_commit.py, issue #767):
#     is_role_eligible() is DIRECT-only: Bash AND {Edit,Write}. Scenario-20
#     roles: developer (Bash+Write+Edit) -> direct -> eligible, orchestrator
#     (Agent+Write, no Bash) -> delegate -> NOT eligible, git (Bash, no
#     Edit/Write) -> none -> NOT eligible. -> eligible_roles = ["developer"].
#   Rendering (scripts/lib/auto_commit.py::render_auto_commit_block):
#     custom mode renders per-authority prose. developer (direct): "Commit
#     directly whenever `<script>` exits 0", the secret-scan line and the
#     sentinel-prefix line, and NO trigger prose (built-in triggers are
#     ignored entirely in custom mode). orchestrator (delegate): "delegate
#     the commit to the `git` agent" when `<script>` exits 0.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (20-auto-commit-custom): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (20-auto-commit-custom): $*"
    exit 1
}

# --- Provider marker files (expected: Claude only) ----
[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
[ -d ".claude/agents" ] || fail "agent directory missing for Claude: .claude/agents"

ALLOWLIST=".meta-config/auto-commit-allowlist.json"
[ -f "$ALLOWLIST" ] || fail "allowlist file missing: $ALLOWLIST"

# --- 1. Allowlist shape (python3 for JSON parsing; jq-free) ------------
python3 - "$ALLOWLIST" <<'PY' || exit 1
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)


def check(cond: bool, msg: str) -> None:
    if not cond:
        print(f"ASSERT FAIL (20-auto-commit-custom, allowlist): {msg} -- "
              f"allowlist content: {json.dumps(data, sort_keys=True)}")
        sys.exit(1)


check(data.get("mode") == "custom", "mode must be 'custom'")
check(data.get("custom_script") == "scripts/should-commit.sh",
      "custom_script must be 'scripts/should-commit.sh'")
check(data.get("eligible_roles") == ["developer"],
      "eligible_roles must be exactly ['developer'] "
      "(direct-only: Bash AND Edit/Write; orchestrator is delegate-only, "
      "git has no Edit/Write)")
check(data.get("triggers") == [], "triggers must be empty (built-in triggers are ignored in custom mode)")
check(data.get("secret_scan") is True, "secret_scan must be true")
PY

# --- 2. Rendered AUTO_COMMIT_BLOCK in developer.md (Claude only) -------
# Block excerpt = header line up to the first blank line (keeps checks
# scoped to the block, away from unrelated template prose).
block_of() {
    awk '/Commit authority \(issue #694\):/ { found = 1 }
         found { print }
         found && /^$/ { exit }' "$1"
}

dev=".claude/agents/developer.md"
[ -f "$dev" ] || fail "generated file missing: $dev"
block="$(block_of "$dev")"
[ -n "$block" ] || fail "$dev: AUTO_COMMIT_BLOCK not rendered (header line missing)"

printf '%s\n' "$block" | grep -qF "auto_commit.mode: custom" \
    || fail "$dev: block header must name mode 'custom'"

# The custom_script contract: the script path must be named verbatim.
printf '%s\n' "$block" | grep -qF "scripts/should-commit.sh" \
    || fail "$dev: block must mention custom_script 'scripts/should-commit.sh'"

# Sentinel-prefix instruction (guard-hook authorization).
printf '%s\n' "$block" | grep -qF "#agent-meta:agent=" \
    || fail "$dev: block must contain the '#agent-meta:agent=<role>' sentinel-prefix instruction"

# Secret scan applies in custom mode (the agent commits itself).
printf '%s\n' "$block" | grep -qi "secret scan" \
    || fail "$dev: block must contain the secret-scan line in custom mode"

# NO trigger prose: no built-in trigger name may appear in the block.
if printf '%s\n' "$block" \
    | grep -Eq "task-boundary|per-edit|context-pressure|file-count-threshold"
then
    fail "$dev: block must NOT contain trigger prose (custom_script alone decides)"
fi

# --- 3. orchestrator.md (delegate) gets custom delegate prose -----------
orch=".claude/agents/orchestrator.md"
[ -f "$orch" ] || fail "generated file missing: $orch"
orch_block="$(block_of "$orch")"
[ -n "$orch_block" ] || fail "$orch: delegate AUTO_COMMIT_BLOCK not rendered"
printf '%s\n' "$orch_block" | grep -qF "scripts/should-commit.sh" \
    || fail "$orch: delegate block must name the custom_script"
printf '%s\n' "$orch_block" | grep -qF "delegate the commit to the \`git\` agent" \
    || fail "$orch: delegate block must delegate the commit to the git agent"
if printf '%s\n' "$orch_block" | grep -qF "Commit directly"; then
    fail "$orch: delegate block must NOT tell the orchestrator to commit directly"
fi

echo "ASSERT OK (20-auto-commit-custom): allowlist shape + custom-script block verified"
