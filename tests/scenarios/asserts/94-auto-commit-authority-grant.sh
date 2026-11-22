#!/bin/bash
# Scenario assert for 94-auto-commit-authority-grant (issue #1181, plan T12).
#
# Contract (see tests/scenarios/run.sh header): cwd = the scenario's temp
# project dir (the sync output); $1 and env REPO_ROOT both carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
#
# Six assertion groups, pinned against REAL generated output:
#   (a) .claude/agents/documenter.md frontmatter gains `- Bash` and the body
#       carries the grant line naming a full `Bash` grant, not a git-only one.
#   (b) .claude/agents/planner.md (notify, not granted) keeps NO Bash and NO
#       #1181 text — non-granted roles are byte-stable.
#   (c) .opencode/agents/documenter.md (hookless provider) keeps `bash: deny`
#       and sync.log carries the has_hooks=false grant WARN.
#   (d) .meta-config/auto-commit-allowlist.json has version 2 and
#       authority_overrides.documenter == "direct".
#   (e) a 2nd sync without authority_overrides and with documenter removed
#       from roles warns "documenter (grant withdrawn)" (D17, withdrawal via
#       roles:).
#   (f) a 3rd sync with the grant present but orchestrator-guard disabled
#       renders NO Bash in .claude/agents/documenter.md (N-1, fail-closed).
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (94-auto-commit-authority-grant): REPO_ROOT missing (pass as \$1 or env var)" >&2
    exit 2
fi

SYNC="python3 $REPO_ROOT/scripts/sync.py"
GRANT_SUBSTR='full `Bash` grant, not a `git`-only grant'
HOOKLESS_WARN="auto-commit-grant: documenter=direct not enforced on provider 'Opencode' (has_hooks=false); rendered as notify (issue #1181)"

fail() {
    echo "ASSERT FAIL (94-auto-commit-authority-grant): $*"
    exit 1
}

# Frontmatter-only view so tool-list checks cannot collide with prose.
frontmatter_of() {
    awk 'NR==1 && $0=="---" {fm=1; next} fm && $0=="---" {exit} fm {print}' "$1"
}
has_bash_tool() {
    printf '%s\n' "$(frontmatter_of "$1")" | grep -qE '^[[:space:]]*-[[:space:]]*Bash[[:space:]]*$'
}

# --- preconditions ----------------------------------------------------------
[ -f ".claude/agents/documenter.md" ] || fail "missing .claude/agents/documenter.md"
[ -f ".claude/agents/planner.md" ] || fail "missing .claude/agents/planner.md"
[ -f ".opencode/agents/documenter.md" ] || fail "missing .opencode/agents/documenter.md"
[ -f ".scenario-logs/sync.log" ] || fail "missing .scenario-logs/sync.log"
ALLOWLIST=".meta-config/auto-commit-allowlist.json"
[ -f "$ALLOWLIST" ] || fail "missing $ALLOWLIST"

# --- (a) Claude documenter: frontmatter Bash + grant line -------------------
has_bash_tool ".claude/agents/documenter.md" \
    || fail ".claude/agents/documenter.md frontmatter has no '- Bash' (grant not rendered)"
grep -qF "$GRANT_SUBSTR" ".claude/agents/documenter.md" \
    || fail ".claude/agents/documenter.md body missing grant line '$GRANT_SUBSTR'"

# --- (b) Claude planner: no Bash, no #1181 ----------------------------------
if has_bash_tool ".claude/agents/planner.md"; then
    fail ".claude/agents/planner.md must NOT gain '- Bash' (role not granted)"
fi
if grep -qF '#1181' ".claude/agents/planner.md"; then
    fail ".claude/agents/planner.md must NOT contain '#1181' (no grant line for non-granted role)"
fi

# --- (c) Opencode documenter: bash: deny + hookless WARN --------------------
grep -qF 'bash: deny' ".opencode/agents/documenter.md" \
    || fail ".opencode/agents/documenter.md missing 'bash: deny' (hookless provider must not render a grant)"
grep -qF "$HOOKLESS_WARN" ".scenario-logs/sync.log" \
    || fail ".scenario-logs/sync.log missing hookless-provider WARN '$HOOKLESS_WARN'"

# --- (d) allowlist: version 2 + authority_overrides -------------------------
python3 - "$ALLOWLIST" <<'PY' || exit 1
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)

if data.get("version") != 2:
    print(f"ASSERT FAIL (94, allowlist): version must be 2, got {data.get('version')!r}")
    sys.exit(1)
if data.get("authority_overrides", {}).get("documenter") != "direct":
    print("ASSERT FAIL (94, allowlist): authority_overrides.documenter must be 'direct', "
          f"got {data.get('authority_overrides')!r}")
    sys.exit(1)
PY

# --- (e) 2nd sync: no authority_overrides + documenter removed from roles ---
CFG=".meta-config/project.yaml"
cp "$CFG" ".scenario-logs/94.project.orig.yaml" \
    || fail "cannot back up $CFG"
python3 - "$CFG" <<'PY' || fail "cannot rewrite config for withdrawal sync"
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as fh:
    text = fh.read()
grant = ("  authority_overrides:\n"
         "    documenter:\n"
         "      authority: direct\n"
         "      acknowledge_full_shell: true\n")
if grant not in text:
    print("ASSERT ERROR (94): expected grant block not found in project.yaml")
    sys.exit(1)
text = text.replace(grant, "")
text = text.replace("- documenter\n", "")
with open(path, "w", encoding="utf-8") as fh:
    fh.write(text)
PY

$SYNC >".scenario-logs/sync2.out" 2>&1
sync2_rc=$?
[ "$sync2_rc" -eq 0 ] || fail "2nd (withdrawal) sync rc=$sync2_rc"
cp sync.log ".scenario-logs/sync2.log" || fail "cannot copy sync.log after 2nd sync"
grep -qF 'auto-commit-allowlist: eligible_roles shrank' ".scenario-logs/sync2.log" \
    || fail "2nd sync log missing 'auto-commit-allowlist: eligible_roles shrank'"
grep -qF 'documenter (grant withdrawn)' ".scenario-logs/sync2.log" \
    || fail "2nd sync log missing 'documenter (grant withdrawn)' (D17: roles: withdrawal)"

# --- (f) 3rd sync: restore grant, disable guard, expect no Bash ------------
cp ".scenario-logs/94.project.orig.yaml" "$CFG" \
    || fail "cannot restore original config for guard-off sync"
cat >>"$CFG" <<'YAML'
hooks:
  orchestrator-guard:
    enabled: false
YAML

$SYNC >".scenario-logs/sync3.out" 2>&1
sync3_rc=$?
[ "$sync3_rc" -eq 0 ] || fail "3rd (guard-disabled) sync rc=$sync3_rc"
cp sync.log ".scenario-logs/sync3.log" || fail "cannot copy sync.log after 3rd sync"
if has_bash_tool ".claude/agents/documenter.md"; then
    fail "guard disabled but .claude/agents/documenter.md still has '- Bash' (N-1 fail-closed)"
fi
grep -qF 'guard hook disabled: hooks.orchestrator-guard.enabled is not true' ".scenario-logs/sync3.log" \
    || fail "3rd sync log missing guard-disabled WARN"

echo "ASSERT OK (94-auto-commit-authority-grant): grant render, non-grant byte-stability, hookless deny+WARN, allowlist v2, roles: withdrawal WARN and guard-off fail-closed verified"
