#!/bin/bash
# hook: scenario-suite
# version: 1.0.0
# event: Manual
# description: Pre-release gate — runs the full agent-meta scenario catalog (all configs, full --validate, all content assertions) and blocks the release on any FAIL.
# enabled_by_default: false

# --- Gate contract (see docs/RELEASE_GATES.md) ---
# Run standalone (`bash release-gates/scenario-suite.sh`) or via the
# release-gates/ dispatcher (pre-release-check.sh). Exit 0 = pass or
# self-skip (disabled, or prerequisites missing). Exit non-zero = fail,
# blocks the release.

set -u

PROJECT_ROOT="${PROJECT_ROOT:-$PWD}"
cd "$PROJECT_ROOT" || exit 1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/hook_common.sh" 2>/dev/null || exit 0

GATE_NAME="scenario-suite"

# Baked at sync-time from the release-gates.scenario-suite.enabled setting
# > dod-preset default > this header's enabled_by_default. The `:=` form keeps
# an explicit one-off `PRE_RELEASE_GATE_ENABLED=false` override working.
: "${PRE_RELEASE_GATE_ENABLED:=true}"
hook_gate_check_enabled "$GATE_NAME" || exit 0

# Framework sources: consumer submodule layout first, then the framework
# checkout itself (agent-meta releases from its own repo).
FRAMEWORK_ROOT=""
for candidate in "${AGENT_META_ROOT:-}" "$PROJECT_ROOT/.agent-meta" "$PROJECT_ROOT"; do
    if [ -n "$candidate" ] && [ -f "$candidate/scripts/sync.py" ] \
       && [ -f "$candidate/tests/scenarios/run.sh" ]; then
        FRAMEWORK_ROOT="$candidate"
        break
    fi
done
if [ -z "$FRAMEWORK_ROOT" ]; then
    echo "[SKIP] $GATE_NAME: no agent-meta checkout with tests/scenarios/run.sh found (set AGENT_META_ROOT or use the .agent-meta submodule)"
    exit 0
fi

RUNNER="$FRAMEWORK_ROOT/tests/scenarios/run.sh"
echo "[INFO] $GATE_NAME: full scenario suite from $FRAMEWORK_ROOT (SCENARIO_PROFILE=release)"

# Release decisions always use the full profile: all scenarios, dry-run,
# full --validate and every content assertion. No dev shortcuts here.
SCENARIO_PROFILE=release bash "$RUNNER"
rc=$?
if [ "$rc" -eq 0 ]; then
    echo "[INFO] $GATE_NAME: full scenario suite passed"
    exit 0
fi

echo "[FAIL] $GATE_NAME: full scenario suite failed (runner exit $rc); release blocked"
exit "$rc"
