#!/usr/bin/env bash
# Scenario assert for 59-progress-ledger
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
#
# Covers AC-28 of SPEC-PROGRESS-LEDGER-2026-09-13: the generated resume/ledger
# wiring plus the four runtime paths (execute_plan checkpoint + ledger
# close-out, the --update-plan-ledger writer, a spec_plan_ledger_drift WARNING
# for a synthetic mismatch and the --rehydrate next_task_ref resume path). All
# checks run against the temp project, never against the agent-meta checkout.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (59-progress-ledger): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (59-progress-ledger): $*"
    exit 1
}

# The DoD presets live in the agent-meta checkout (submodule in real consumer
# projects). Emulate the submodule layout so resolve_agent_meta_root() finds
# them — otherwise the concept-driven preset cannot be resolved and the drift
# check would stay a no-op.
if [ ! -e ".agent-meta" ]; then
    ln -s "$REPO_ROOT" .agent-meta
fi

# --- (a) generated wiring: the gated resume/ledger/root-cause rules exist ---
[ -f ".claude/skills/plan-ledger/SKILL.md" ] \
    || fail "gated plan-ledger rule not delivered while the workflow is enabled"
grep -q -- '--update-plan-ledger' .claude/skills/plan-ledger/SKILL.md \
    || fail "plan-ledger rule does not document the --update-plan-ledger writer"
grep -q 'CheckpointStore' .claude/skills/plan-ledger/SKILL.md \
    || fail "plan-ledger rule does not document the checkpoint path"
for rule in session-recovery root-cause-gate; do
    [ -f ".claude/rules/$rule.md" ] || [ -f ".claude/skills/$rule/SKILL.md" ] \
        || fail "gated rule '$rule' not delivered"
done
grep -q -- '--rehydrate' .claude/rules/session-recovery.md 2>/dev/null \
    || grep -q -- '--rehydrate' .claude/skills/session-recovery/SKILL.md 2>/dev/null \
    || fail "session-recovery rule does not document the --rehydrate resume path"

# --- fixtures --------------------------------------------------------------
mkdir -p docs/specs docs/plans

cat > docs/specs/2026-09-13-ledger-design.md <<'SPEC'
# Progress Ledger Demo — Spec

> Status: APPROVED (2026-09-13)

## Problem

Demo problem.

## Ziel

Demo goal.

## Nicht-Ziele

None.

## Interface Contracts

lib.plan_ledger:update_plan_ledger -> LedgerWriteResult

## Datenfluss

Plan checkboxes to checkpoints and back.

## Acceptance Criteria

1. A checkpoint is written.

## Offene Fragen

None.

## Trace-Anker: spec-id: SPEC-ledger-demo
SPEC

# Plan A: closed out by execute_plan (both tasks succeed).
cat > docs/plans/2026-09-13-ledger-demo.md <<'PLAN'
---
pipeline_stages:
  implement: 1
---

# Ledger Demo Implementation Plan

> Status: IN PROGRESS
> plan-id: ledger-demo

**Goal:** Prove execute_plan writes per-entry checkpoints and closes the ledger.
**Architecture:** Reuse the existing CheckpointStore and the plan-ledger writer.
**Tech Stack:** Python 3.9, Markdown.

**Spec:** docs/specs/2026-09-13-ledger-design.md

## Global Constraints

None.

## File Structure

- Create: tests/test_ledger_demo_task1.py — demo test

Trace anchor: SPEC-ledger-demo

### Task 1: First demo task

**Files:** Create: tests/test_ledger_demo_task1.py
**Interfaces:** Produces: demo_one()

- [ ] Step 1: implement task one
- [ ] Step 2: verify task one

### Task 2: Second demo task

**Files:** Create: tests/test_ledger_demo_task2.py
**Interfaces:** Produces: demo_two()

- [ ] Step 1: implement task two
- [ ] Step 2: verify task two
PLAN

# Plan B: synthetic ledger/checkpoint mismatch -> drift WARNING, and one open
# task (task-1) for the rehydrate next_task_ref path.
cat > docs/plans/2026-09-13-ledger-drift.md <<'PLAN'
---
pipeline_stages:
  implement: 1
---

# Ledger Drift Implementation Plan

> Status: IN PROGRESS
> plan-id: ledger-drift

**Goal:** Produce a synthetic ledger/checkpoint mismatch for the drift check.
**Architecture:** Reuse the existing CheckpointStore and the plan-ledger writer.
**Tech Stack:** Python 3.9, Markdown.

**Spec:** docs/specs/2026-09-13-ledger-design.md

## Global Constraints

None.

## File Structure

- Create: tests/test_ledger_drift_task1.py — demo test

Trace anchor: SPEC-ledger-demo

### Task 1: Ledger ahead of the checkpoints

**Files:** Create: tests/test_ledger_drift_task1.py
**Interfaces:** Produces: demo_drift()

- [x] Step 1: implement task one
- [x] Step 2: verify task one

### Task 2: Checkpoint ahead of the ledger

**Files:** Create: tests/test_ledger_drift_task2.py
**Interfaces:** Produces: demo_drift_two()

- [ ] Step 1: implement task two
- [ ] Step 2: verify task two
PLAN

# --- (b) execute_plan writes checkpoints and closes the ledger -------------
python3 - "$REPO_ROOT" <<'PYEOF' || fail "execute_plan checkpoint/ledger wiring check failed"
import sys
from pathlib import Path

repo_root = Path(sys.argv[1])
sys.path.insert(0, str(repo_root / "scripts"))

from lib.checkpoint import CheckpointStore
from lib.consistency.spec_plan import parse_plan_ledger
from lib.orchestration import BarrierEntry, FanoutPlan, FanoutTask, execute_plan


class StubDispatcher:
    def dispatch(self, tasks):
        return [
            BarrierEntry(
                task_id=task.task_id,
                agent="developer",
                status="success",
                summary="done",
            )
            for task in tasks
        ]


plan_path = Path("docs/plans/2026-09-13-ledger-demo.md")
fanout = FanoutPlan(
    kind="fanout",
    tasks=(
        FanoutTask(task_id="task-1", target_agent="developer", prompt="task one"),
        FanoutTask(task_id="task-2", target_agent="developer", prompt="task two"),
    ),
)
store = CheckpointStore(project_root=Path("."), agent_meta_root=repo_root)
result = execute_plan(
    fanout,
    StubDispatcher(),
    store=store,
    session_id="s59-exec",
    plan_id="ledger-demo",
    ledger_path=plan_path,
)
assert result.status == "success", result.status

checkpoint = store.get_checkpoint_for_task("s59-exec", "ledger-demo#task-1")
assert checkpoint is not None, "execute_plan did not write a checkpoint for task-1"
assert checkpoint.plan_id == "ledger-demo", checkpoint.plan_id
assert checkpoint.task_ref == "ledger-demo#task-1", checkpoint.task_ref

ledger = parse_plan_ledger(plan_path)
assert ledger["complete"] is True, ledger
assert ledger["status"] == "complete", ledger["status"]
plan_text = plan_path.read_text(encoding="utf-8")
assert "- [x] Step 1: implement task one" in plan_text, "task-1 checkbox not closed"
assert "- [ ] Step 1: implement task two" not in plan_text, "task-2 checkbox left open"

assert Path(".meta-viz/progress/current.md").exists(), "progress write-through missing"
PYEOF

# --- (c) --checkpoint writes the mismatch that feeds the drift warning -----
cp_out="$(python3 "$REPO_ROOT/scripts/sync.py" \
    --checkpoint --session-id s59-drift --task 2 --agent developer \
    --status completed --plan-id ledger-drift 2>&1)"
cp_rc=$?
[ "$cp_rc" = "0" ] || { echo "$cp_out"; fail "--checkpoint exited $cp_rc"; }
printf '%s\n' "$cp_out" | grep -q 'task_ref: ledger-drift#task-2' \
    || { echo "$cp_out"; fail "--checkpoint did not report task_ref ledger-drift#task-2"; }

# --- (d) synthetic mismatch emits a spec_plan_ledger_drift WARNING ---------
drift_out="$(python3 "$REPO_ROOT/scripts/sync.py" --validate-spec-plan 2>&1)"
printf '%s\n' "$drift_out" | grep -q '\[WRN\] \[spec_plan_ledger_drift\]' \
    || { echo "$drift_out"; fail "no spec_plan_ledger_drift WARNING for the synthetic mismatch"; }
printf '%s\n' "$drift_out" | grep -q 'ledger marks task(s) done without a completed checkpoint' \
    || { echo "$drift_out"; fail "drift WARNING for ledger-ahead-of-checkpoints missing"; }
printf '%s\n' "$drift_out" | grep -q 'completed checkpoint without a closed ledger task' \
    || { echo "$drift_out"; fail "drift WARNING for checkpoint-ahead-of-ledger missing"; }

# --- (e) --rehydrate returns the expected next_task_ref --------------------
rehydrate_out="$(python3 "$REPO_ROOT/scripts/sync.py" --rehydrate 2>&1)"
rh_rc=$?
[ "$rh_rc" = "0" ] || { echo "$rehydrate_out"; fail "--rehydrate exited $rh_rc"; }
printf '%s\n' "$rehydrate_out" | grep -q '## Resume context' \
    || { echo "$rehydrate_out"; fail "--rehydrate did not print a resume context"; }
printf '%s\n' "$rehydrate_out" | grep -q -- '- Plan: `ledger-drift`' \
    || { echo "$rehydrate_out"; fail "--rehydrate did not resolve the driven plan"; }
printf '%s\n' "$rehydrate_out" | grep -q -- '- Next open task: `ledger-drift#task-1`' \
    || { echo "$rehydrate_out"; fail "--rehydrate next_task_ref is not ledger-drift#task-1"; }

# --- (f) --update-plan-ledger writes the checkbox and status --------------
upd_out="$(python3 "$REPO_ROOT/scripts/sync.py" \
    --update-plan-ledger docs/plans/2026-09-13-ledger-drift.md \
    --task 1 2 --status complete 2>&1)"
upd_rc=$?
[ "$upd_rc" = "0" ] || { echo "$upd_out"; fail "--update-plan-ledger exited $upd_rc"; }

python3 - "$REPO_ROOT" <<'PYEOF' || fail "--update-plan-ledger did not close the ledger"
import sys
from pathlib import Path

repo_root = Path(sys.argv[1])
sys.path.insert(0, str(repo_root / "scripts"))

from lib.consistency.spec_plan import parse_plan_ledger, parse_task_ledgers

plan_path = Path("docs/plans/2026-09-13-ledger-drift.md")
ledger = parse_plan_ledger(plan_path)
assert ledger["complete"] is True, ledger
assert ledger["status"] == "complete", ledger["status"]
assert parse_task_ledgers(plan_path)["task-1"]["complete"] is True
assert parse_task_ledgers(plan_path)["task-2"]["complete"] is True
text = plan_path.read_text(encoding="utf-8")
assert "- [x] Step 1: implement task one" in text, "task-1 checkbox not written"
assert "- [x] Step 1: implement task two" in text, "task-2 checkbox not written"
PYEOF

echo "ASSERT OK (59-progress-ledger): checkpoint, ledger close-out, drift warning and rehydrate verified"
