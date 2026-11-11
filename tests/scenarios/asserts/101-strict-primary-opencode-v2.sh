#!/bin/bash
# Scenario assert for 101-strict-primary-opencode-v2.
# (issue #1190, SPEC-orchestrator-mode-topology-2026-11-09 §3.8.3/§12.3,
#  AC-29/AC-33.)
#
# Position POS-3 — the ONLY position with an entry point: `mode: strict` +
# declared `orchestrator.topology: primary` on the Opencode v2 surface.
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# `--validate`; this assert re-reads the recorded rc and pins the artifacts.
#
# Parts:
#   1. The fixture really declares the POS-3 pair (guards fixture drift).
#   2. `opencode.json` carries `default_agent: orchestrator` AND exactly the two
#      managed deny triples `{edit,**,deny}` + `{shell,**,deny}` — and no v1
#      `permission` map (§3.8.3 Nr. 3, §12.3 row `strict x primary`).
#   3. The emitted `orchestrator` agent is the entry point: `mode: primary`.
#   4. No suspension warning: POS-3 activates the gate, so neither the v2
#      `NOT written` text nor `orchestrator-topology.gate-inactive` may appear.
#   5. `--validate` rc 0 (the harness already gates on it; re-asserted here so
#      the scenario documents the rc explicitly).
# Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (101-strict-primary-opencode-v2): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (101-strict-primary-opencode-v2): $*"
    exit 1
}

LOG_DIR=".scenario-logs"
[ -d "$LOG_DIR" ] || fail "harness log dir missing: $LOG_DIR"

[ -f "opencode.json" ] || fail "missing generated document: opencode.json"
[ -f ".opencode/agents/orchestrator.md" ] \
    || fail "POS-3 must emit the orchestrator agent: .opencode/agents/orchestrator.md"

# --- 1. Fixture = POS-3 (strict x primary) on the v2 project channel. -------
python3 - .meta-config/project.yaml <<'PY' || fail "fixture is not the POS-3 (strict x primary) v2 project"
import sys
try:
    import yaml
except ImportError:
    raise SystemExit(3)
with open(sys.argv[1], encoding="utf-8") as fh:
    project = yaml.safe_load(fh) or {}
orch = project.get("orchestrator") or {}
assert orch.get("mode") == "strict", orch
assert orch.get("topology") == "primary", orch
opts = (project.get("provider-options") or {}).get("Opencode") or {}
assert opts.get("surface-version") == "v2", opts
PY

# --- 2. Entry point + exactly the two managed deny triples. -----------------
python3 - opencode.json <<'PY' || fail "POS-3 opencode.json contract violated"
import json
import sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
assert doc.get("default_agent") == "orchestrator", (
    f"POS-3 requires default_agent == 'orchestrator', got {doc.get('default_agent')!r}"
)
assert "permission" not in doc, (
    "a v2 document must not carry the v1 permission map"
)
triples = {
    (entry.get("action"), entry.get("resource"), entry.get("effect"))
    for entry in doc.get("permissions") or ()
}
expected = {("edit", "**", "deny"), ("shell", "**", "deny")}
assert triples == expected, (
    f"POS-3 writes exactly the two managed deny triples, got {sorted(triples)}"
)
PY

# --- 3. The emitted agent is the session entry point. ----------------------
python3 - .opencode/agents/orchestrator.md <<'PY' || fail "orchestrator frontmatter is not mode: primary"
import sys
text = open(sys.argv[1], encoding="utf-8").read()
block = text.split("---", 2)[1]
fields = {}
for line in block.splitlines():
    if ":" in line and not line.startswith((" ", "-", "\t")):
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
assert fields.get("mode") == "primary", (
    f"POS-3 requires mode: primary, got {fields.get('mode')!r}"
)
assert "mode: subagent" not in block, "POS-3 must never emit mode: subagent"
PY

# --- 4. No gate-suspension warning on POS-3 (the gate IS active). ----------
if grep -qF "opencode-v2 gate (permissions deny) NOT written for provider" "$LOG_DIR/sync.log"; then
    echo "----- suspension hits in $LOG_DIR/sync.log -----"
    grep -nF "NOT written for provider" "$LOG_DIR/sync.log"
    fail "POS-3 activates the gate: no 'NOT written' warning may appear"
fi
if grep -qF "orchestrator-topology.gate-inactive" "$LOG_DIR/sync.log" "$LOG_DIR/validate.log"; then
    fail "POS-3 must not report a suspended gate (gate-inactive) in any channel"
fi

# --- 5. `--validate` rc 0, as recorded by the harness. ---------------------
validate_rc="$(cat "$LOG_DIR/validate.rc" 2>/dev/null || echo missing)"
[ "$validate_rc" = "0" ] || fail "sync.py --validate must exit 0 (recorded rc: $validate_rc)"

echo "ASSERT OK (101-strict-primary-opencode-v2): POS-3 — default_agent orchestrator, mode: primary, exactly the two managed deny triples, no suspension warning, --validate rc 0"
