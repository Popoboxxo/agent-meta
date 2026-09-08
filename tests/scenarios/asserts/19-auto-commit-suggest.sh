#!/bin/bash
# Scenario assert for 19-auto-commit-suggest (issue #694).
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
#     frontmatter. Scenario-19 roles: orchestrator (Write), developer
#     (Write+Edit), tester (Write+Edit) -> eligible; git (Bash/Read/Glob/
#     Grep/TodoWrite) and explorer (Read/Glob/Grep/TodoWrite) -> NOT
#     eligible. -> eligible_roles = ["developer", "orchestrator", "tester"].
#   Rendering (scripts/lib/auto_commit.py::render_auto_commit_block):
#     suggest mode renders the propose-not-pause prose ("propose a
#     ready-to-use commit message ... do NOT run `git commit` yourself,
#     and do not stop and wait for confirmation") and deliberately does
#     NOT render the secret-scan line: the scan runs before auto/custom
#     commits only, and a suggest-tier agent never commits itself (the
#     scan_line append lives only in the custom and auto branches).
#     Deviation from the original scenario spec ("Secret-Scan-Zeile
#     vorhanden") -- asserted here as ABSENT to pin the designed
#     behavior; if a future change adds the scan line to suggest mode,
#     this assert fails loudly and forces a conscious scenario update.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (19-auto-commit-suggest): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (19-auto-commit-suggest): $*"
    exit 1
}

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
        print(f"ASSERT FAIL (19-auto-commit-suggest, allowlist): {msg} -- "
              f"allowlist content: {json.dumps(data, sort_keys=True)}")
        sys.exit(1)


check(data.get("mode") == "suggest", "mode must be 'suggest'")
check(data.get("eligible_roles") == ["developer", "orchestrator", "tester"],
      "eligible_roles must be exactly ['developer', 'orchestrator', 'tester'] "
      "(capability-derived; git and explorer have no Edit/Write in their own "
      "template and must be filtered out)")
check(data.get("triggers") == [], "triggers must be empty (suggest mode has no built-in triggers)")
check(data.get("secret_scan") is True, "secret_scan must be true (config value is recorded in the allowlist)")
PY

# --- 2. Rendered AUTO_COMMIT_BLOCK in developer.md (both providers) ----
# Block excerpt = header line up to the first blank line (keeps checks
# scoped to the block, away from unrelated template prose).
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

    printf '%s\n' "$block" | grep -qF "auto_commit.mode: suggest" \
        || fail "$dev: block header must name mode 'suggest'"

    # Propose-not-pause prose: agent proposes a message, never runs git.
    printf '%s\n' "$block" | grep -qF "propose a ready-to-use commit message" \
        || fail "$dev: block must contain the propose-a-commit-message prose"
    printf '%s\n' "$block" | grep -qF 'do NOT run `git commit` yourself' \
        || fail "$dev: block must forbid running git commit directly (suggest tier)"

    # No pause-wording in the block ("do not stop and wait" is fine; the
    # word "pause" must not appear).
    if printf '%s\n' "$block" | grep -qi "pause"; then
        fail "$dev: block contains forbidden 'pause' wording (suggest tier must be non-blocking)"
    fi

    # Designed behavior: suggest mode renders NO secret-scan line (the
    # scan applies to auto/custom commits only; see file header comment).
    if printf '%s\n' "$block" | grep -qi "secret scan"; then
        fail "$dev: block must NOT contain a secret-scan line in suggest mode " \
             "(scan runs before auto/custom commits only; if the framework " \
             "gained a suggest-tier scan line, update this scenario consciously)"
    fi
done

echo "ASSERT OK (19-auto-commit-suggest): allowlist shape + propose-not-pause block verified"
