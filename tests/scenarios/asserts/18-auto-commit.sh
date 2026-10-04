#!/bin/bash
# Scenario assert for 18-auto-commit (issue #694).
#
# Contract (see tests/scenarios/run.sh header): cwd = the scenario's temp
# project dir (the sync output); $1 and env REPO_ROOT both carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
#
# Verified expectations -- derived from the framework code, not guessed:
#   Authority/eligibility (scripts/lib/auto_commit.py, issue #767):
#     is_role_eligible() is DIRECT-only: Bash AND {Edit,Write}. Scenario-18
#     roles: developer (Bash+Write+Edit) -> direct -> eligible, tester
#     (Bash+Write+Edit) -> direct -> eligible, orchestrator (Agent+Write,
#     NO Bash) -> delegate -> NOT eligible, git (Bash/Read/Glob/Grep/
#     TodoWrite, no Edit/Write) -> none -> NOT eligible.
#     -> eligible_roles = ["developer", "tester"].
#   Rendering (scripts/lib/auto_commit.py::render_auto_commit_block):
#     auto mode renders per-authority prose: developer (direct) -> "Commit
#     directly as soon as ANY ..." + secret-scan + sentinel-prefix line;
#     orchestrator (delegate) -> "delegate the commit to the `git` agent"
#     at each trigger boundary; documenter (notify) -> changed files + a
#     ready-to-use message for the caller/orchestrator. delegate and notify
#     both forward the secret-scan requirement (F1, issue #767). Asserted for
#     Claude, Gemini AND Opencode -- the root-cause provider (orchestrator has
#     permission.bash: deny there). The git.md template has no
#     {{AUTO_COMMIT_BLOCK}} slot at all (pinned by
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

# --- Provider marker files (expected: Claude, Gemini, Opencode) ----
[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
[ -d ".claude/agents" ] || fail "agent directory missing for Claude: .claude/agents"
[ -f "AGENTS.md" ] || fail "root provider file missing: AGENTS.md"
[ -d ".gemini/agents" ] || fail "agent directory missing for Gemini: .gemini/agents"
# Opencode is the ROOT-CAUSE provider for issue #767 (orchestrator has
# permission.bash: deny there) -- its rendered agents must be asserted too.
[ -d ".opencode/agents" ] || fail "agent directory missing for Opencode: .opencode/agents"

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
check(data.get("eligible_roles") == ["developer", "tester"],
      "eligible_roles must be exactly ['developer', 'tester'] "
      "(direct-only: Bash AND Edit/Write; orchestrator has Write but no Bash, "
      "git has Bash but no Edit/Write)")
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

for provider in .claude .gemini .opencode; do
    dev="$provider/agents/developer.md"
    [ -f "$dev" ] || fail "generated file missing: $dev"
    block="$(block_of "$dev")"
    [ -n "$block" ] || fail "$dev: AUTO_COMMIT_BLOCK not rendered (header line missing)"
    printf '%s\n' "$block" | grep -q "task-boundary" \
        || fail "$dev: rendered block does not mention trigger 'task-boundary'"
    printf '%s\n' "$block" | grep -q "context-pressure" \
        || fail "$dev: rendered block does not mention trigger 'context-pressure'"
done

# --- 2b. orchestrator.md renders the DELEGATE block (issue #767) --------
for provider in .claude .gemini .opencode; do
    orch="$provider/agents/orchestrator.md"
    [ -f "$orch" ] || fail "generated file missing: $orch"
    block="$(block_of "$orch")"
    [ -n "$block" ] || fail "$orch: delegate AUTO_COMMIT_BLOCK not rendered"
    printf '%s\n' "$block" | grep -qF "delegate the commit to the \`git\` agent" \
        || fail "$orch: delegate block must delegate the commit to the git agent"
    printf '%s\n' "$block" | grep -qF "trigger boundary" \
        || fail "$orch: delegate block must name the trigger boundary"
    printf '%s\n' "$block" | grep -qi "secret scan" \
        || fail "$orch: delegate block must forward the secret-scan requirement"
    if printf '%s\n' "$block" | grep -qF "Commit directly"; then
        fail "$orch: delegate block must NOT tell the orchestrator to commit directly"
    fi
done

# --- 2c. documenter.md renders the NOTIFY block (issue #767) ------------
# Notify is the third write capability: no git, hand the file list + message
# to the caller. Asserted for every provider, incl. the root-cause Opencode.
for provider in .claude .gemini .opencode; do
    doc="$provider/agents/documenter.md"
    [ -f "$doc" ] || fail "generated file missing: $doc"
    block="$(block_of "$doc")"
    [ -n "$block" ] || fail "$doc: notify AUTO_COMMIT_BLOCK not rendered"
    printf '%s\n' "$block" | grep -qF "ready-to-use Conventional-Commits message" \
        || fail "$doc: notify block must carry a ready-to-use commit message"
    printf '%s\n' "$block" | grep -qF "caller/orchestrator" \
        || fail "$doc: notify block must route the commit to the caller/orchestrator"
    printf '%s\n' "$block" | grep -qi "secret scan" \
        || fail "$doc: notify block must forward the secret-scan requirement"
    if printf '%s\n' "$block" | grep -qF "Commit directly"; then
        fail "$doc: notify block must NOT tell the documenter to commit directly"
    fi
    if printf '%s\n' "$block" | grep -qi "delegate the commit"; then
        fail "$doc: notify block must NOT contain a delegation instruction"
    fi
done

# --- 3. git.md must stay block-free -------------------------------------
for provider in .claude .gemini .opencode; do
    gitfile="$provider/agents/git.md"
    [ -f "$gitfile" ] || fail "generated file missing: $gitfile"
    if grep -q "Commit authority (issue #694)" "$gitfile"; then
        fail "$gitfile: must NOT render the AUTO_COMMIT block (git role already has its own commit authority)"
    fi
done

echo "ASSERT OK (18-auto-commit): allowlist shape + rendered blocks verified"
