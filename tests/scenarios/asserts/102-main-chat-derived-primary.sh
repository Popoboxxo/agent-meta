#!/bin/bash
# Scenario assert for 102-main-chat-derived-primary.
# (issue #1190, SPEC-orchestrator-mode-topology-2026-11-09 §3.8.3, D-Q1/§6.2,
#  AC-29/AC-34.)
#
# Position POS-1 — `orchestrator.mode: main-chat` with an UNSET `topology` key.
# The registry's `providers.Opencode.primary-role: orchestrator` nevertheless
# derives `primary`, which is inert in main-chat and must be reported exactly
# once (`orchestrator-topology.main-chat-derived-primary`, WARNING).
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path.
#
# Parts:
#   1. The fixture is POS-1 and really omits the topology key (guards fixture
#      drift — an explicit key would turn the case into the hard validator ERROR).
#   2. No orchestrator role is emitted: `.opencode/agents/orchestrator.md` absent,
#      no `default_agent` and no gate (neither `permissions[]` nor `permission`)
#      in `opencode.json` (AC-34).
#   3. The sync log records the derivation source (`derived from
#      providers.Opencode.primary-role`) — the precondition of the D-Q1 finding.
#   4. EXACTLY ONE `orchestrator-topology.main-chat-derived-primary` WARNING, no
#      ERROR (AC-29/D-Q1).
#      CHANNEL NOTE (deviation, reported with this task): `sync.py --validate`
#      runs `check_orchestrator_topology` against the AGENT-META root only
#      (`cli_commands._run_consistency_checks(agent_meta_root)`, the framework's
#      own `.meta-config/project.yaml`), so a scratch project's D-Q1 finding can
#      never appear in `.scenario-logs/validate.log`. This assert therefore calls
#      the very same checker (`lib.consistency.topology`) on THIS project — the
#      channel the spec names in §6.2 (`consistency/topology.py`).
#   5. `--validate` rc 0 (the harness already gates on it; re-asserted here).
# Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (102-main-chat-derived-primary): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (102-main-chat-derived-primary): $*"
    exit 1
}

LOG_DIR=".scenario-logs"
[ -d "$LOG_DIR" ] || fail "harness log dir missing: $LOG_DIR"

[ -f "opencode.json" ] || fail "missing generated document: opencode.json"

# --- 1. Fixture = POS-1 (main-chat, topology deliberately unset). -----------
python3 - .meta-config/project.yaml <<'PY' || fail "fixture is not the POS-1 (main-chat, topology unset) project"
import sys
try:
    import yaml
except ImportError:
    raise SystemExit(3)
with open(sys.argv[1], encoding="utf-8") as fh:
    project = yaml.safe_load(fh) or {}
orch = project.get("orchestrator") or {}
assert orch.get("mode") == "main-chat", orch
assert "topology" not in orch, (
    "the D-Q1 case needs an UNSET topology key (an explicit one is a hard "
    f"validator ERROR), got {orch!r}"
)
PY

# --- 2. POS-1 emits no role and no entry point/gate. -----------------------
if [ -e ".opencode/agents/orchestrator.md" ]; then
    fail "POS-1 must not emit the orchestrator role (AC-34): .opencode/agents/orchestrator.md exists"
fi
python3 - opencode.json <<'PY' || fail "POS-1 opencode.json must carry no entry point and no gate"
import json
import sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
assert "default_agent" not in doc, (
    "POS-1 writes no default_agent (AC-34), got "
    f"{doc.get('default_agent')!r}"
)
assert not doc.get("permissions"), (
    f"POS-1 writes no v2 permissions[] triples, got {doc.get('permissions')!r}"
)
assert not doc.get("permission"), (
    f"POS-1 writes no v1 permission map, got {doc.get('permission')!r}"
)
PY

# --- 3. The derivation actually happened (precondition of the D-Q1 check). --
grep -qF "derived from providers.Opencode.primary-role" "$LOG_DIR/sync.log" || {
    echo "----- topology lines in $LOG_DIR/sync.log -----"
    grep -n "topology" "$LOG_DIR/sync.log" || echo "(none)"
    fail "POS-1 expects the unset topology to DERIVE primary from providers.Opencode.primary-role"
}

# --- 4. Exactly one derived-primary WARNING, no ERROR (D-Q1, §6.2). -------
python3 - "$REPO_ROOT" <<'PY' || fail "the D-Q1 consistency channel did not report exactly one derived-primary warning"
import sys
sys.path.insert(0, sys.argv[1] + "/scripts")
from pathlib import Path
from types import SimpleNamespace

from lib.consistency.report import Severity
from lib.consistency.topology import check_orchestrator_topology
from lib.io import load_yaml_file
from lib.providers import load_provider_capabilities, load_providers_config
from lib.roles import load_roles_config

repo = Path(sys.argv[1]).resolve()
root = Path.cwd()
config = load_yaml_file(
    root / ".meta-config" / "project.yaml", on_error="default", default={}
)
known = frozenset(load_roles_config(repo).get("roles", {}))
active_set = SimpleNamespace(
    roles=frozenset(config.get("roles") or ()), known_roles=known
)
findings = check_orchestrator_topology(
    root,
    config,
    provider_config=load_providers_config(repo, config),
    capabilities=load_provider_capabilities(repo),
    providers=["Opencode"],
    active_set=active_set,
)
derived = [
    f for f in findings if f.check == "orchestrator-topology.main-chat-derived-primary"
]
assert len(derived) == 1, (
    "exactly one derived-primary finding expected, got "
    f"{[(f.severity.name, f.check) for f in findings]}"
)
assert derived[0].severity == Severity.WARNING, derived[0].severity
errors = [f for f in findings if f.severity == Severity.ERROR]
assert not errors, [(f.check, f.message) for f in errors]
PY

# --- 5. `--validate` rc 0, as recorded by the harness. ---------------------
validate_rc="$(cat "$LOG_DIR/validate.rc" 2>/dev/null || echo missing)"
[ "$validate_rc" = "0" ] || fail "sync.py --validate must exit 0 (recorded rc: $validate_rc)"

echo "ASSERT OK (102-main-chat-derived-primary): POS-1 — no orchestrator role, no default_agent, no gate, derivation to primary reported as exactly one warning (consistency channel), --validate rc 0"
