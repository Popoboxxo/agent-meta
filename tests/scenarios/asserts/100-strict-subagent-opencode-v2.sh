#!/bin/bash
# Scenario assert for 100-strict-subagent-opencode-v2.
# (issue #1190, SPEC-orchestrator-mode-topology-2026-11-09 §3.8.3/§12.3,
#  AC-29/AC-35.)
#
# Position POS-2 — the new DEFAULT (D-OQ1): `mode: strict` +
# `orchestrator.topology: subagent` on the Opencode v2 surface.
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# `--validate` on this project (validate rc 0 is a precondition for this assert
# to run at all).
#
# Parts:
#   1. The fixture really declares the POS-2 pair (guards fixture drift).
#   2. `opencode.json` carries NO entry point and NO gate: no `default_agent`,
#      no v2 `permissions[]` list and no v1 `permission` map (§3.8.3 Nr. 2).
#   3. The emitted `orchestrator` agent is a subagent: `mode: subagent`, never
#      `mode: primary`. (The role-level write-scope lock inside the agent
#      frontmatter is a ROLE property and stays — this assert is about the
#      project-level gate document.)
#   4. Exactly ONE sync-log warning carries BOTH pinned §6.4 substrings: v2 has
#      one channel only (Sync-Log), and the cause-aware text from G7 must name
#      the resolved position — no silent suspension (§6.4 counting rule).
#   5. No `orchestrator-topology.gate-inactive` finding: on v2 the tier is
#      `plugin`, so `_gate_wanted` never fires and the finding must not exist
#      (§6.4, `consistency/topology.py:103-105`).
#   6. Prefix guard for the BLOCKED scenario: `run.sh --list 10` must select
#      this scenario plus 101/102/104 and must NOT select
#      `blocked-103-advisory-subagent` (AC-29; `run.sh` has no SKIP concept).
# Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (100-strict-subagent-opencode-v2): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (100-strict-subagent-opencode-v2): $*"
    exit 1
}

LOG_DIR=".scenario-logs"
[ -d "$LOG_DIR" ] || fail "harness log dir missing: $LOG_DIR"

[ -f "opencode.json" ] || fail "missing generated document: opencode.json"
[ -f ".opencode/agents/orchestrator.md" ] \
    || fail "POS-2 emits the role as a subagent: .opencode/agents/orchestrator.md must exist"

# --- 1. Fixture = POS-2 (strict x subagent) on the v2 project channel. -------
python3 - .meta-config/project.yaml <<'PY' || fail "fixture is not the POS-2 (strict x subagent) v2 project"
import sys
try:
    import yaml
except ImportError:
    raise SystemExit(3)
with open(sys.argv[1], encoding="utf-8") as fh:
    project = yaml.safe_load(fh) or {}
orch = project.get("orchestrator") or {}
assert orch.get("mode") == "strict", orch
assert orch.get("topology") == "subagent", orch
opts = (project.get("provider-options") or {}).get("Opencode") or {}
assert opts.get("surface-version") == "v2", opts
PY

# --- 2. No entry point, no gate in the project document. --------------------
python3 - opencode.json <<'PY' || fail "POS-2 opencode.json must carry no entry point and no gate"
import json
import sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
assert "default_agent" not in doc, (
    "POS-2 writes no entry point (AC-35): default_agent must be absent, got "
    f"{doc.get('default_agent')!r}"
)
assert not doc.get("permissions"), (
    f"POS-2 withholds the v2 permissions[] deny (AC-35), got {doc.get('permissions')!r}"
)
assert not doc.get("permission"), (
    f"the v2 surface must not carry the v1 permission map, got {doc.get('permission')!r}"
)
PY

# --- 3. The emitted agent is a subagent. ------------------------------------
python3 - .opencode/agents/orchestrator.md <<'PY' || fail "orchestrator frontmatter is not mode: subagent"
import sys
text = open(sys.argv[1], encoding="utf-8").read()
block = text.split("---", 2)[1]
fields = {}
for line in block.splitlines():
    if ":" in line and not line.startswith((" ", "-", "\t")):
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
assert fields.get("mode") == "subagent", (
    f"POS-2 requires mode: subagent, got {fields.get('mode')!r}"
)
assert "mode: primary" not in block, "POS-2 must never emit mode: primary"
PY

# --- 4. Exactly one sync-log warning, both pinned substrings on THAT line. ---
# The sync CLI renders each message twice inside one run — once in the streaming
# notice channel (`  !  …`) and once in the `WARNINGS` summary (`[WARN] …`). The
# §6.4 counting rule counts MESSAGES per channel, not rendered lines, so the
# assert normalises the transport prefixes and requires exactly one distinct
# message carrying both pinned substrings.
python3 - "$LOG_DIR/sync.log" <<'PY' || fail "the pinned v2 gate warning is not exactly one distinct sync-log message"
import re
import sys

GATE = "opencode-v2 gate (permissions deny) NOT written for provider"
CAUSE = "effective orchestrator topology is 'subagent'"
PREFIX = re.compile(r"^\s*(?:!\s*|\[(?:WARN|WARNING|INFO|HINWEIS|ERROR)\]\s*)")

messages = set()
with open(sys.argv[1], encoding="utf-8", errors="replace") as fh:
    for line in fh:
        if GATE not in line:
            continue
        messages.add(PREFIX.sub("", line).strip())

assert len(messages) == 1, (
    f"exactly one distinct gate message expected, got {len(messages)}: "
    f"{sorted(messages)}"
)
message = messages.pop()
assert CAUSE in message, (
    "the v2 gate warning must name the resolved position (G7 cause-aware text), "
    f"got: {message!r}"
)
PY
# Since #1086d stdout no longer repeats the warnings: the message streams once
# (`  !  ...`) and the WARNINGS block shrinks to `WARNINGS: N (see above)`.
stream_lines="$(grep -cE "^ +! +.*opencode-v2 gate \(permissions deny\) NOT written for provider" "$LOG_DIR/sync.log" || true)"
[ "$stream_lines" = "1" ] || fail "the v2 gate warning must stream exactly once, got $stream_lines"
if grep -qE "^\[WARN\].*opencode-v2 gate" "$LOG_DIR/sync.log"; then
    fail "the WARNINGS summary must not repeat the v2 gate warning on stdout (#1086d)"
fi
grep -qE "^WARNINGS: [1-9][0-9]* \(see above\)$" "$LOG_DIR/sync.log" || fail "the WARNINGS summary must reference the streamed warnings (WARNINGS: N (see above))"

# --- 5. No gate-inactive finding on the v2 surface (tier plugin). -----------
if grep -qF "orchestrator-topology.gate-inactive" "$LOG_DIR/validate.log"; then
    echo "----- gate-inactive hits in $LOG_DIR/validate.log -----"
    grep -nF "orchestrator-topology.gate-inactive" "$LOG_DIR/validate.log"
    fail "v2 (tier plugin) must not emit an orchestrator-topology.gate-inactive finding (§6.4)"
fi

# --- 6. Prefix guard: the BLOCKED scenario stays outside the 10* match. -----
# `env -u` drops the inherited CI shard selector: this assertion is about the
# prefix filter alone, and a shard 3/4 would otherwise show only `101-…`.
list10="$(env -u SCENARIO_SHARD -u SCENARIO_TOTAL bash "$REPO_ROOT/tests/scenarios/run.sh" --list 10)" \
    || fail "could not list the 10* scenario selection"
for expected in 100-strict-subagent-opencode-v2 101-strict-primary-opencode-v2 \
                102-main-chat-derived-primary 104-claude-strict-subagent; do
    printf '%s\n' "$list10" | grep -qxF "$expected" \
        || fail "'run.sh --list 10' must select $expected (got: $(printf '%s' "$list10" | tr '\n' ' '))"
done
if printf '%s\n' "$list10" | grep -q "blocked-103"; then
    fail "'run.sh --list 10' must NOT select blocked-103-advisory-subagent (prefix gap is the guard)"
fi

echo "ASSERT OK (100-strict-subagent-opencode-v2): POS-2 — no default_agent, no permissions[] (v2) / permission (v1), mode: subagent, exactly one cause-aware gate warning, no gate-inactive finding, blocked-103 outside the 10* match"
