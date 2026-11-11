#!/bin/bash
# Scenario assert for blocked-103-advisory-subagent.
# (issue #1190, SPEC-orchestrator-mode-topology-2026-11-09 §12.3 footnote,
#  D-OQ3, AC-29/AC-37.)
#
# Scenario 103 is `advisory x subagent` (POS-2) — the team recommendation ONLY
# after issue #1182: a `context-profile: compact` project breaks the advisory
# mode (missing `# CRITICAL GATE` section heading), so the configuration is
# BLOCKED and is never executed.
#
# `tests/scenarios/run.sh` has NO SKIP concept (a reachable scenario either
# passes or fails), therefore the scenario id lives OUTSIDE the `10*` match:
# the file is named `blocked-103-…`, which the `10`-prefix filter does not
# select. That prefix gap IS the guard (AC-29), not a skip switch.
#
# This assert therefore does not read sync output at all — it verifies that the
# documented BLOCKED preconditions still hold, so the blocker cannot silently
# disappear from the config or the catalog:
#   1. the fixture still carries `mode: advisory` + `topology: subagent` +
#      `context-profile: compact` (the #1182 trigger),
#   2. the fixture and the catalog both name #1182, the catalog row is
#      `BLOCKED (#1182)` and uses the `blocked-103-advisory-subagent` name,
#   3. the scenario name cannot be selected by the `10` prefix filter.
# It is never run by the harness; run it manually:
#   tests/scenarios/asserts/blocked-103-advisory-subagent.sh "$PWD"
# Exit 0 = the documented BLOCKED state still holds.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (blocked-103-advisory-subagent): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (blocked-103-advisory-subagent): $*"
    exit 1
}

CONFIG="$REPO_ROOT/tests/scenarios/configs/blocked-103-advisory-subagent.project.yaml"
REGISTRY="$REPO_ROOT/tests/scenarios/registry.md"
[ -f "$CONFIG" ] || fail "missing BLOCKED scenario config: $CONFIG"
[ -f "$REGISTRY" ] || fail "missing scenario catalog: $REGISTRY"

# --- 1. The #1182 trigger is still configured. -----------------------------
python3 - "$CONFIG" <<'PY' || fail "BLOCKED fixture no longer carries the #1182 precondition"
import sys
try:
    import yaml
except ImportError:
    raise SystemExit(3)
with open(sys.argv[1], encoding="utf-8") as fh:
    project = yaml.safe_load(fh) or {}
assert "Opencode" in (project.get("ai-providers") or []), project.get("ai-providers")
orch = project.get("orchestrator") or {}
assert orch.get("mode") == "advisory", f"expected mode: advisory, got {orch.get('mode')!r}"
assert orch.get("topology") == "subagent", (
    f"expected topology: subagent, got {orch.get('topology')!r}"
)
assert project.get("context-profile") == "compact", (
    "the #1182 blocker is the compact context profile, got "
    f"{project.get('context-profile')!r}"
)
PY

# --- 2. Blocker and id are documented in fixture + catalog. ----------------
grep -qF "#1182" "$CONFIG" || fail "$CONFIG must reference issue #1182"
grep -qF "BLOCKED (#1182)" "$REGISTRY" \
    || fail "$REGISTRY must mark scenario 103 as 'BLOCKED (#1182)'"
grep -qF "blocked-103-advisory-subagent" "$REGISTRY" \
    || fail "$REGISTRY must name the scenario 'blocked-103-advisory-subagent'"

# --- 3. The prefix gap keeps it out of the 10* match (guard, AC-29). -------
scenario_name="$(basename "$CONFIG" .project.yaml)"
case "$scenario_name" in
    10*) fail "the BLOCKED scenario must not start with '10' (got '$scenario_name')" ;;
esac
list10="$(bash "$REPO_ROOT/tests/scenarios/run.sh" --list 10)" \
    || fail "could not list the 10* scenario selection"
if printf '%s\n' "$list10" | grep -qF "$scenario_name"; then
    fail "'run.sh --list 10' selects $scenario_name — the prefix gap guard is broken"
fi

echo "ASSERT OK (blocked-103-advisory-subagent): BLOCKED (#1182) preconditions hold — mode: advisory + topology: subagent + context-profile: compact, blocker documented, id outside the 10* match"
