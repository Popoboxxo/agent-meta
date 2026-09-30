"""Ledger parsing: checkbox/status view is the human-readable ledger; the
CheckpointStore is the machine-readable recovery source (D2)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.checkpoint import Checkpoint, CheckpointStore  # noqa: E402
from lib.consistency.spec_plan import (  # noqa: E402
    REQUIRED_PLAN_SECTIONS,
    REQUIRED_SPEC_SECTIONS,
    parse_plan_ledger,
)


def _plan(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "2026-09-13-demo.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_all_checked_is_complete(tmp_path):
    ledger = parse_plan_ledger(_plan(
        tmp_path,
        "# Demo Implementation Plan\n> Status: IN PROGRESS\n"
        "- [x] a\n- [x] b\n",
    ))
    assert ledger["checkboxes"] == 2
    assert ledger["checked"] == 2
    assert ledger["complete"] is True
    assert ledger["status"] == "IN PROGRESS"


def test_open_checkbox_is_incomplete(tmp_path):
    ledger = parse_plan_ledger(_plan(
        tmp_path,
        "# Demo Implementation Plan\n> Status: geplant\n- [x] a\n- [ ] b\n",
    ))
    assert ledger["checkboxes"] == 2
    assert ledger["checked"] == 1
    assert ledger["complete"] is False


def test_missing_status_is_none(tmp_path):
    ledger = parse_plan_ledger(_plan(tmp_path, "# Demo\n- [ ] a\n"))
    assert ledger["status"] is None
    assert ledger["complete"] is False


def test_required_sections_include_pipeline_stages():
    assert "pipeline_stages" in " ".join(REQUIRED_PLAN_SECTIONS)
    assert REQUIRED_SPEC_SECTIONS


def test_checkpoint_store_round_trip_is_recovery_source(tmp_path):
    store = CheckpointStore(project_root=tmp_path)
    store.save_checkpoint(
        "sess1",
        Checkpoint(task_id="task-3", agent="developer",
                   task_description="impl", status="completed"),
    )
    last = store.get_last_checkpoint("sess1")
    assert last is not None
    assert last.task_id == "task-3"
    assert [c.task_id for c in store.get_completed_steps("sess1")] == ["task-3"]
