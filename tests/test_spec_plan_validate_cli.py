"""--validate-spec-plan exits 0 without artifacts and is a no-op when the
master switch is off (F12)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.log import SyncLog  # noqa: E402
from lib.spec_plan_validate import validate_spec_plan  # noqa: E402


def _log(tmp_path):
    return SyncLog()


def test_no_artifacts_exit_zero(tmp_path):
    code = validate_spec_plan(
        tmp_path, {"platforms": [], "spec-plan-workflow": {"enabled": True}}, _log(tmp_path),
    )
    assert code == 0


def test_enabled_false_is_noop_exit_zero(tmp_path):
    code = validate_spec_plan(
        tmp_path, {"platforms": [], "spec-plan-workflow": {"enabled": False}}, _log(tmp_path),
    )
    assert code == 0


def test_flag_registered_in_parser():
    from sync import _build_arg_parser
    args = _build_arg_parser().parse_args(["--validate-spec-plan"])
    assert args.validate_spec_plan is True


def _write_plan(tmp_path, name, text="# Legacy plan\n\nTBD\n"):
    plans = tmp_path / "docs" / "plans"
    plans.mkdir(parents=True, exist_ok=True)
    (plans / name).write_text(text, encoding="utf-8")


def test_unchanged_artifact_out_of_scope_exit_zero(tmp_path, monkeypatch):
    """`scan.changed-files-only` (default true) must exclude unchanged legacy
    artifacts even when they contain findings-causing content (§5.1/§10.2)."""
    _write_plan(tmp_path, "2020-01-01-legacy.md")
    monkeypatch.setattr("lib.spec_plan_validate._changed_files", lambda root: set())

    code = validate_spec_plan(
        tmp_path, {"platforms": [], "spec-plan-workflow": {"enabled": True}}, _log(tmp_path),
    )
    assert code == 0


def test_changed_artifact_in_scope_detects_placeholder(tmp_path, monkeypatch):
    """A changed artifact within scope is scanned and its placeholder yields
    exit 1 — proving the changed-files filter is not a blanket no-op."""
    _write_plan(tmp_path, "2020-01-01-legacy.md")
    monkeypatch.setattr(
        "lib.spec_plan_validate._changed_files",
        lambda root: {"docs/plans/2020-01-01-legacy.md"},
    )

    code = validate_spec_plan(
        tmp_path, {"platforms": [], "spec-plan-workflow": {"enabled": True}}, _log(tmp_path),
    )
    assert code == 1


_DRIFT_SPEC = (
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

_DRIFT_PLAN = (
    "# Demo Implementation Plan\n> Status: geplant\n"
    "**Goal:** demo\n**Architecture:** demo\n**Tech Stack:** demo\n"
    "**Spec:** docs/specs/2026-09-13-demo-design.md\n"
    "## Global Constraints\n- stdlib only\n"
    "## File Structure\n- Create: docs/specs/x.md\n"
    "## Trace-Anker: spec-id: SPEC-demo\n"
    "---\npipeline_stages:\n  implement: 1\n---\n"
    "### Task 1: First\n- [x] Step a\n"
)


def test_drift_finding_sets_exit_1(tmp_path, monkeypatch):
    """AC-16: a completed-checkpoint/ledger mismatch makes the gate exit 1."""
    from lib.checkpoint import Checkpoint, CheckpointStore

    specs = tmp_path / "docs" / "specs"
    plans = tmp_path / "docs" / "plans"
    specs.mkdir(parents=True, exist_ok=True)
    plans.mkdir(parents=True, exist_ok=True)
    (specs / "2026-09-13-demo-design.md").write_text(_DRIFT_SPEC, encoding="utf-8")
    (plans / "2026-09-13-demo.md").write_text(_DRIFT_PLAN, encoding="utf-8")

    store = CheckpointStore(project_root=tmp_path)
    store.save_checkpoint(
        "sess-drift",
        Checkpoint(
            task_id="task-1",
            agent="developer",
            task_description="demo",
            status="in_progress",
            plan_id="2026-09-13-demo",
        ),
    )

    monkeypatch.setattr(
        "lib.spec_plan_validate._changed_files",
        lambda root: {"docs/plans/2026-09-13-demo.md"},
    )

    code = validate_spec_plan(
        tmp_path, {"platforms": [], "spec-plan-workflow": {"enabled": True}}, _log(tmp_path),
    )
    assert code == 1
