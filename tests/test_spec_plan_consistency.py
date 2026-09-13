"""check_spec_plan_workflow: required sections incl. pipeline_stages,
no-placeholder, traceability, approval marker, ledger format, plan graph.
effective_enabled=false returns [] (no-op)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.checkpoint import Checkpoint, CheckpointStore
from lib.consistency.report import Severity
from lib.consistency.spec_plan import (
    _parse_plan_tasks,
    check_spec_plan_workflow,
    parse_task_ledgers,
)

_ENABLED = {"spec-plan-workflow": {"enabled": True}}
_DISABLED = {"spec-plan-workflow": {"enabled": False}}

_GOOD_SPEC = (
    "# Demo — Spec\n> Status: APPROVED (2026-09-13)\n"
    "## Problem\nDemo-Problem\n"
    "## Ziel\nDemo-Ziel\n"
    "## Nicht-Ziele\nDemo-Nicht-Ziel\n"
    "## Interface Contracts\n"
    "## Datenfluss\n"
    "## Acceptance Criteria\n1. AC-1\n"
    "## Offene Fragen + Risiken\n"
    "## Trace-Anker: spec-id: SPEC-demo\n"
)


def _plan(text: str) -> str:
    return (
        "# Demo Implementation Plan\n> Status: geplant\n"
        "**Goal:** demo\n**Architecture:** demo\n**Tech Stack:** demo\n"
        "**Spec:** docs/specs/2026-09-13-demo-design.md\n"
        "## Global Constraints\n- stdlib only\n"
        "## File Structure\n- Create: docs/specs/x.md\n"
        "## Trace-Anker: spec-id: SPEC-demo\n"
        "---\npipeline_stages:\n  implement: 1\n---\n"
        + text
    )


def _write(tmp_path: Path, spec: str, plan: str) -> Path:
    (tmp_path / "docs" / "specs").mkdir(parents=True)
    (tmp_path / "docs" / "plans").mkdir(parents=True)
    (tmp_path / "docs" / "specs" / "2026-09-13-demo-design.md").write_text(spec, encoding="utf-8")
    (tmp_path / "docs" / "plans" / "2026-09-13-demo.md").write_text(plan, encoding="utf-8")
    return tmp_path


def test_disabled_returns_empty(tmp_path):
    _write(tmp_path, _GOOD_SPEC, _plan("- [x] Task 1\n"))
    assert check_spec_plan_workflow(
        tmp_path, _DISABLED, agent_meta_root=REPO_ROOT,
    ) == []


def test_good_artifacts_pass(tmp_path):
    _write(tmp_path, _GOOD_SPEC, _plan("- [x] Task 1\n"))
    findings = check_spec_plan_workflow(
        tmp_path, _ENABLED, agent_meta_root=REPO_ROOT,
    )
    assert findings == []


def test_missing_pipeline_stages_is_error(tmp_path):
    plan = _plan("- [x] Task 1\n").replace(
        "pipeline_stages:\n  implement: 1\n", "",
    )
    _write(tmp_path, _GOOD_SPEC, plan)
    findings = check_spec_plan_workflow(
        tmp_path, {**_ENABLED, "dod": {"spec-plan-required": True}},
        agent_meta_root=REPO_ROOT,
    )
    checks = {f.check for f in findings}
    assert "spec_plan_required_sections" in checks
    assert any(f.severity == Severity.ERROR for f in findings)


def test_placeholder_is_error(tmp_path):
    _write(tmp_path, _GOOD_SPEC, _plan("- [ ] TBD\n"))
    findings = check_spec_plan_workflow(
        tmp_path, _ENABLED, agent_meta_root=REPO_ROOT,
    )
    assert any(f.check == "spec_plan_no_placeholder" for f in findings)


def test_plan_graph_no_false_positive_on_acyclic_plan(tmp_path):
    plan = _plan(
        "### Task 1\n**Files:** Modify: a.py\n### Task 2\n**Files:** Modify: b.py\n"
    )
    _write(tmp_path, _GOOD_SPEC, plan)
    findings = check_spec_plan_workflow(
        tmp_path, _ENABLED, agent_meta_root=REPO_ROOT,
    )
    assert not any(f.check == "spec_plan_plan_graph" and f.severity == Severity.ERROR
                   for f in findings)


def test_parse_plan_tasks_hyphen_header():
    # G-03/AC-01: hyphenated ids must yield the full id, not ``task``; the old
    # numeric ``### Task <n>`` form keeps working.
    tasks = _parse_plan_tasks(
        "### Task task-1: Hyphen\n"
        "### Task 2 \u2014 Numeric\n"
        "### Task task-3: Third\n"
    )
    assert [t.task_id for t in tasks] == ["task-1", "task-2", "task-3"]
    assert tasks[0].prompt == "Hyphen"
    assert tasks[1].prompt == "Numeric"


def test_parse_task_ledgers_counts_and_offsets(tmp_path):
    text = (
        "### Task 1: First\n"
        "- [x] Step a\n"
        "- [ ] Step b\n"
        "### Task task-2: Second\n"
        "- [x] Step c\n"
        "- [X] Step d\n"
        "### Task 3: Empty\n"
    )
    plan = tmp_path / "2026-09-13-demo.md"
    plan.write_text(text, encoding="utf-8")

    ledgers = parse_task_ledgers(plan)
    assert set(ledgers) == {"task-1", "task-2", "task-3"}

    first = ledgers["task-1"]
    assert first["total"] == 2
    assert first["checked"] == 1
    assert first["complete"] is False

    second = ledgers["task-2"]
    assert second["total"] == 2
    assert second["checked"] == 2
    assert second["complete"] is True

    # A block without checkboxes is present but never ``complete``.
    empty = ledgers["task-3"]
    assert empty["total"] == 0
    assert empty["checked"] == 0
    assert empty["complete"] is False

    # Offsets span header -> next header / end of document.
    assert text[first["start"]:first["end"]] == text[:text.index("### Task task-2")]
    assert text[first["start"]:first["end"]].startswith("### Task 1:")
    assert text[second["start"]:second["end"]].startswith("### Task task-2:")
    assert second["end"] == empty["start"]
    assert empty["end"] == len(text)

    # Missing plan file degrades to an empty ledger instead of raising.
    assert parse_task_ledgers(tmp_path / "missing.md") == {}


def test_parse_task_ledgers_normalizes_ids(tmp_path):
    plan = tmp_path / "2026-09-13-demo.md"
    plan.write_text(
        "### Task 1: Numeric\n- [x] a\n"
        "### Task task-2: Canonical\n- [ ] b\n"
        "### Task TASK-3: Upper\n- [x] c\n",
        encoding="utf-8",
    )
    ledgers = parse_task_ledgers(plan)
    assert set(ledgers) == {"task-1", "task-2", "task-3"}
    assert ledgers["task-2"]["complete"] is False
    assert ledgers["task-3"]["complete"] is True


# ---------------------------------------------------------------------------
# Ledger drift against the checkpoint store (AC-15/AC-16/AC-34, M2)
# ---------------------------------------------------------------------------

def _checkpoint(tmp_path: Path, task_id: str, status: str,
                plan_id: str = "2026-09-13-demo") -> None:
    CheckpointStore(project_root=tmp_path).save_checkpoint(
        "sess-1",
        Checkpoint(
            task_id=task_id,
            agent="developer",
            task_description="demo",
            status=status,
            plan_id=plan_id,
        ),
    )


def _drift(findings) -> list:
    return [f for f in findings if f.check == "spec_plan_ledger_drift"]


def test_drift_ledger_ahead_of_checkpoints(tmp_path):
    _write(tmp_path, _GOOD_SPEC, _plan("### Task 1: First\n- [x] Step a\n"))
    _checkpoint(tmp_path, "task-1", "in_progress")

    findings = check_spec_plan_workflow(
        tmp_path, _ENABLED, agent_meta_root=REPO_ROOT,
    )

    drift = _drift(findings)
    assert len(drift) == 1
    assert drift[0].severity == Severity.WARNING


def test_drift_checkpoint_ahead_of_ledger(tmp_path):
    _write(tmp_path, _GOOD_SPEC, _plan("### Task 1: First\n- [ ] Step a\n"))
    _checkpoint(tmp_path, "task-1", "completed")

    findings = check_spec_plan_workflow(
        tmp_path, _ENABLED, agent_meta_root=REPO_ROOT,
    )

    assert len(_drift(findings)) == 1


def test_drift_status_complete_but_ledger_open(tmp_path):
    plan = _plan("### Task 1: First\n- [ ] Step a\n").replace(
        "> Status: geplant", "> Status: complete",
    )
    _write(tmp_path, _GOOD_SPEC, plan)
    _checkpoint(tmp_path, "task-1", "in_progress")

    findings = check_spec_plan_workflow(
        tmp_path, _ENABLED, agent_meta_root=REPO_ROOT,
    )

    assert len(_drift(findings)) == 1


def test_drift_skipped_without_sessions(tmp_path):
    _write(tmp_path, _GOOD_SPEC, _plan("### Task 1: First\n- [x] Step a\n"))

    findings = check_spec_plan_workflow(
        tmp_path, _ENABLED, agent_meta_root=REPO_ROOT,
    )

    assert _drift(findings) == []


def test_drift_disabled_flag_suppresses_finding(tmp_path):
    _write(tmp_path, _GOOD_SPEC, _plan("### Task 1: First\n- [x] Step a\n"))
    _checkpoint(tmp_path, "task-1", "in_progress")
    config = {
        "spec-plan-workflow": {
            "enabled": True,
            "ledger-drift": {"enabled": False},
        },
    }

    findings = check_spec_plan_workflow(
        tmp_path, config, agent_meta_root=REPO_ROOT,
    )

    assert _drift(findings) == []


def test_drift_severity_override(tmp_path):
    _write(tmp_path, _GOOD_SPEC, _plan("### Task 1: First\n- [x] Step a\n"))
    _checkpoint(tmp_path, "task-1", "in_progress")
    config = {
        "spec-plan-workflow": {
            "enabled": True,
            "ledger-drift": {"severity": "ERROR"},
        },
    }

    findings = check_spec_plan_workflow(
        tmp_path, config, agent_meta_root=REPO_ROOT,
    )

    drift = _drift(findings)
    assert len(drift) == 1
    assert drift[0].severity == Severity.ERROR


def test_drift_is_changed_files_scoped(tmp_path):
    # AC-34 (F4): a mismatching plan that is not in changed_files stays silent,
    # the same plan being changed is drift-checked.
    _write(tmp_path, _GOOD_SPEC, _plan("### Task 1: First\n- [x] Step a\n"))
    _checkpoint(tmp_path, "task-1", "in_progress")

    out_of_scope = check_spec_plan_workflow(
        tmp_path, _ENABLED, agent_meta_root=REPO_ROOT, changed_files=set(),
    )
    assert _drift(out_of_scope) == []

    in_scope = check_spec_plan_workflow(
        tmp_path, _ENABLED, agent_meta_root=REPO_ROOT,
        changed_files={"docs/plans/2026-09-13-demo.md"},
    )
    assert len(_drift(in_scope)) == 1
