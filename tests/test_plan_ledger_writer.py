"""Plan ledger writer -- round-trip against ``parse_plan_ledger``.

Covers AC-07..AC-10 of the progress/ledger system design
(``SPEC-PROGRESS-LEDGER-2026-09-13``, IC-05): checkbox toggling per task block,
untouched neighbours, parser ``complete`` guarantee, first ``Status:`` write,
missing-plan and unknown-task error behaviour, no-op write avoidance and the
handler's exit codes.
"""
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import plan_ledger  # noqa: E402
from lib.consistency.spec_plan import parse_plan_ledger  # noqa: E402
from lib.plan_ledger import (  # noqa: E402
    MODE,
    handle_update_plan_ledger,
    set_plan_status,
    update_plan_ledger,
)

PLAN_NAME = "2026-09-13-demo.md"

PLAN = (
    "# Demo Implementation Plan\n"
    "> Status: geplant\n"
    "\n"
    "### Task 1: First\n"
    "- [ ] a\n"
    "- [ ] b\n"
    "\n"
    "### Task 2: Second\n"
    "- [ ] c\n"
    "\n"
)


def _plan(tmp_path: Path, text: str = PLAN) -> Path:
    path = tmp_path / PLAN_NAME
    path.write_text(text, encoding="utf-8")
    return path


def _ctx(tmp_path: Path, *, plan=None, tasks=None, status=None, open_=False,
         dry_run=False, project_root=None):
    args = SimpleNamespace(
        update_plan_ledger=plan,
        task=tasks,
        status=status,
        open=open_,
        dry_run=dry_run,
    )
    return SimpleNamespace(args=args,
                           project_root=project_root or tmp_path,
                           log=MagicMock())


# ---------------------------------------------------------------------------
# AC-07 -- toggle one task on
# ---------------------------------------------------------------------------

def test_toggle_task_on_matches_parser(tmp_path, monkeypatch):
    path = _plan(tmp_path)
    writes = []
    real_write_atomic = plan_ledger.write_atomic

    def spy(target, content, *args, **kwargs):
        writes.append(content)
        return real_write_atomic(target, content, *args, **kwargs)

    monkeypatch.setattr(plan_ledger, "write_atomic", spy)

    result = update_plan_ledger(path, {"task-1": True})

    assert result.ok is True
    assert result.reason is None
    assert result.tasks_updated == ("task-1",)
    assert result.checkboxes_toggled == 2
    assert result.unmatched == ()

    ledger = parse_plan_ledger(path)
    assert ledger["checkboxes"] == 3
    assert ledger["checked"] == 2
    assert ledger["complete"] is False

    # Other task untouched.
    assert "- [ ] c" in path.read_text(encoding="utf-8")

    # Atomic single write and disk content equals the built document.
    assert len(writes) == 1
    assert writes[0] == path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# AC-08 -- toggle one task off, neighbours untouched
# ---------------------------------------------------------------------------

def test_toggle_task_off_and_others_untouched(tmp_path):
    text = (
        "# Demo\n> Status: complete\n"
        "### Task 1: A\n- [x] a\n"
        "### Task 2: B\n- [x] b\n- [x] c\n"
        "### Task 3: C\n- [x] d\n"
    )
    path = _plan(tmp_path, text)

    result = update_plan_ledger(path, {"task-2": False})

    assert result.checkboxes_toggled == 2
    assert result.tasks_updated == ("task-2",)

    written = path.read_text(encoding="utf-8")
    assert "- [ ] b" in written
    assert "- [ ] c" in written
    assert "- [x] a" in written
    assert "- [x] d" in written
    assert parse_plan_ledger(path)["complete"] is False


# ---------------------------------------------------------------------------
# AC-09 -- all closed => parser complete; status read back
# ---------------------------------------------------------------------------

def test_all_closed_parser_complete_true(tmp_path):
    path = _plan(tmp_path)

    update_plan_ledger(path, {"task-1": True, "task-2": True})
    result = set_plan_status(path, "complete")

    assert result.ok is True
    ledger = parse_plan_ledger(path)
    assert ledger["checkboxes"] == 3
    assert ledger["checked"] == 3
    assert ledger["complete"] is True
    assert ledger["status"] == "complete"


def test_status_written_and_read_back(tmp_path):
    path = _plan(tmp_path, "# Demo Implementation Plan\n")

    result = set_plan_status(path, "IN PROGRESS")

    assert result.ok is True
    assert result.status == "IN PROGRESS"
    assert result.tasks_updated == ()
    text = path.read_text(encoding="utf-8")
    assert text.startswith("# Demo Implementation Plan\n> Status: IN PROGRESS")
    assert parse_plan_ledger(path)["status"] == "IN PROGRESS"


def test_status_replaces_only_first_existing_line(tmp_path):
    path = _plan(tmp_path, "# Demo\n> Status: geplant\n> Status: other\n")

    set_plan_status(path, "complete")

    text = path.read_text(encoding="utf-8")
    assert "> Status: complete" in text
    assert "> Status: other" in text
    assert text.count("Status:") == 2
    assert parse_plan_ledger(path)["status"] == "complete"


# ---------------------------------------------------------------------------
# AC-10 -- missing plan and unknown task
# ---------------------------------------------------------------------------

def test_missing_plan_reason_plan_not_found(tmp_path):
    path = tmp_path / "does-not-exist.md"

    result = update_plan_ledger(path, {"task-1": True})

    assert result.ok is False
    assert result.reason == "plan-not-found"
    assert result.checkboxes_toggled == 0
    assert not path.exists()


def test_unknown_task_in_unmatched_others_written(tmp_path):
    path = _plan(tmp_path)

    result = update_plan_ledger(path, {"task-1": True, "task-99": True})

    assert result.ok is True
    assert result.unmatched == ("task-99",)
    assert result.tasks_updated == ("task-1",)
    assert result.checkboxes_toggled == 2
    assert parse_plan_ledger(path)["checked"] == 2


# ---------------------------------------------------------------------------
# No-op and dry-run write avoidance
# ---------------------------------------------------------------------------

def test_no_change_no_write(tmp_path, monkeypatch):
    path = _plan(tmp_path, "# Demo\n> Status: complete\n### Task 1: A\n- [x] a\n")
    before = path.read_text(encoding="utf-8")
    calls = []
    monkeypatch.setattr(plan_ledger, "write_atomic",
                        lambda *args, **kwargs: calls.append(args))

    result = update_plan_ledger(path, {"task-1": True})

    assert calls == []
    assert path.read_text(encoding="utf-8") == before
    assert result.ok is True
    assert result.checkboxes_toggled == 0
    assert result.tasks_updated == ()


def test_dry_run_reports_but_does_not_write(tmp_path):
    path = _plan(tmp_path)
    before = path.read_text(encoding="utf-8")

    result = update_plan_ledger(path, {"task-1": True}, status="IN PROGRESS",
                                dry_run=True)

    assert result.dry_run is True
    assert result.ok is True
    assert result.checkboxes_toggled == 2
    assert result.status == "IN PROGRESS"
    assert path.read_text(encoding="utf-8") == before


# ---------------------------------------------------------------------------
# CLI handler (M3: manual validation => exit code 1)
# ---------------------------------------------------------------------------

def test_handler_marks_task_and_exits_0(tmp_path):
    path = _plan(tmp_path)

    with pytest.raises(SystemExit) as exc:
        handle_update_plan_ledger(
            _ctx(tmp_path, plan=PLAN_NAME, tasks=["1"])
        )

    assert exc.value.code == 0
    assert parse_plan_ledger(path)["checked"] == 2


def test_handler_sets_mode(tmp_path):
    _plan(tmp_path)
    ctx = _ctx(tmp_path, plan=PLAN_NAME, tasks=["1"])

    with pytest.raises(SystemExit):
        handle_update_plan_ledger(ctx)

    assert ctx.mode == MODE


def test_handler_missing_plan_arg_exits_1(tmp_path):
    with pytest.raises(SystemExit) as exc:
        handle_update_plan_ledger(_ctx(tmp_path, plan=None, tasks=["1"]))
    assert exc.value.code == 1


def test_handler_without_action_exits_1(tmp_path):
    with pytest.raises(SystemExit) as exc:
        handle_update_plan_ledger(_ctx(tmp_path, plan=PLAN_NAME))
    assert exc.value.code == 1


def test_handler_unknown_task_exits_1(tmp_path):
    _plan(tmp_path)
    with pytest.raises(SystemExit) as exc:
        handle_update_plan_ledger(
            _ctx(tmp_path, plan=PLAN_NAME, tasks=["99"])
        )
    assert exc.value.code == 1


def test_handler_open_resets_checkboxes(tmp_path):
    path = _plan(tmp_path, "# Demo\n### Task 1: A\n- [x] a\n")

    with pytest.raises(SystemExit) as exc:
        handle_update_plan_ledger(
            _ctx(tmp_path, plan=PLAN_NAME, tasks=["1"], open_=True)
        )

    assert exc.value.code == 0
    assert "- [ ] a" in path.read_text(encoding="utf-8")


def test_handler_rejects_path_outside_project_root(tmp_path):
    outside = tmp_path.parent / "outside-plan.md"
    outside.write_text("# Outside\n- [ ] a\n", encoding="utf-8")
    project_root = tmp_path / "project"
    project_root.mkdir()

    with pytest.raises(SystemExit) as exc:
        handle_update_plan_ledger(
            _ctx(project_root, plan=str(outside), tasks=["1"],
                 project_root=project_root)
        )

    assert exc.value.code == 1
    assert "- [ ] a" in outside.read_text(encoding="utf-8")
