#!/bin/bash
# Scenario assert for 18-auto-commit (issue #694).
#
# Contract (see tests/scenarios/run.sh header): cwd = the scenario's temp
# project dir (the sync output); $1 and env REPO_ROOT both carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
#
# Verified expectations -- derived from the framework code, not guessed:
#   Eligibility (scripts/lib/auto_commit.py):
#     _ELIGIBLE_TOOLS = {"Edit", "Write"}; is_role_eligible() intersects
#     this set with the role's OWN agents/1-generic/<role>.md tools:
#     frontmatter. Scenario-18 roles: orchestrator (Write) -> eligible,
#     developer (Write+Edit) -> eligible, tester (Write+Edit) -> eligible,
#     git (Bash/Read/Glob/Grep/TodoWrite) -> NOT eligible.
#     -> eligible_roles = ["developer", "orchestrator", "tester"].
#   Rendering (scripts/lib/auto_commit.py::render_auto_commit_block):
#     auto mode renders trigger prose for the CONFIGURED triggers only,
#     plus the secret-scan line and the sentinel-prefix line. The git.md
#     template has no {{AUTO_COMMIT_BLOCK}} slot at all (pinned by
#     tests/test_auto_commit_coverage.py::test_git_template_is_not_touched).
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (18-auto-commit): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (18-auto-commit): $*"
    exit 1
}

# --- Provider marker files (expected: Claude, Gemini) ----
[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
[ -d ".claude/agents" ] || fail "agent directory missing for Claude: .claude/agents"
[ -f "AGENTS.md" ] || fail "root provider file missing: AGENTS.md"
[ -d ".gemini/agents" ] || fail "agent directory missing for Gemini: .gemini/agents"

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
        print(f"ASSERT FAIL (18-auto-commit, allowlist): {msg} -- "
              f"allowlist content: {json.dumps(data, sort_keys=True)}")
        sys.exit(1)


check(data.get("mode") == "auto", "mode must be 'auto'")
check(data.get("eligible_roles") == ["developer", "orchestrator", "tester"],
      "eligible_roles must be exactly ['developer', 'orchestrator', 'tester'] "
      "(capability-derived: only roles whose own 1-generic template declares "
      "Edit/Write; git has neither)")
check(data.get("triggers") == ["task-boundary", "context-pressure"],
      "triggers must be ['task-boundary', 'context-pressure']")
check(data.get("secret_scan") is True, "secret_scan must be true")
PY

# --- 2. Rendered AUTO_COMMIT_BLOCK in developer.md (both providers) ----
# The block excerpt spans from the header line to the first blank line,
# so checks stay scoped to the block (file-level greps could collide with
# unrelated prose or PROJECT_* variable text).
block_of() {
    awk '/Commit authority \(issue #694\):/ { found = 1 }
         found { print }
         found && /^$/ { exit }' "$1"
}

for provider in .claude .gemini; do
    dev="$provider/agents/developer.md"
    [ -f "$dev" ] || fail "generated file missing: $dev"
    block="$(block_of "$dev")"
    [ -n "$block" ] || fail "$dev: AUTO_COMMIT_BLOCK not rendered (header line missing)"
    printf '%s\n' "$block" | grep -q "task-boundary" \
        || fail "$dev: rendered block does not mention trigger 'task-boundary'"
    printf '%s\n' "$block" | grep -q "context-pressure" \
        || fail "$dev: rendered block does not mention trigger 'context-pressure'"
done

# --- 3. git.md must stay block-free -------------------------------------
for provider in .claude .gemini; do
    gitfile="$provider/agents/git.md"
    [ -f "$gitfile" ] || fail "generated file missing: $gitfile"
    if grep -q "Commit authority (issue #694)" "$gitfile"; then
        fail "$gitfile: must NOT render the AUTO_COMMIT block (git role already has its own commit authority)"
    fi
done

echo "ASSERT OK (18-auto-commit): allowlist shape + rendered blocks verified"
