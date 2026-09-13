"""IC-11 ``--checkpoint`` production writer (AC-33, M1, M3).

The standing production trigger writes one checkpoint through the existing
``CheckpointStore`` without any dispatcher (G-08) dependency. These tests pin
the three contract points of Task 10:

* explicit plan identity only (F1/AC-33) -- ``--plan-id`` or ``--plan``, else
  ``plan_id is None`` and ``task_ref is None``;
* task-id normalization *before* the ref is built (M1) -- ``--task 3`` yields
  ``<plan-id>#task-3``, never ``<plan-id>#3``;
* manual required-argument validation (M3) -- a missing argument or a store
  ``OSError`` exits ``1`` and writes nothing.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib import checkpoint_record
from lib.checkpoint import Checkpoint, CheckpointStore
from lib.checkpoint_record import (
    ALLOWED_STATUSES,
    MODE,
    _handle_checkpoint,
    record_checkpoint,
)
from lib.log import SyncLog

PLAN_NAME = "2026-09-13-demo.md"

PLAN = (
    "> plan-id: p-from-file\n"
    "\n"
    "# Demo Plan\n"
    "\n"
    "- [ ] Step 1\n"
)


def _plan(tmp_path: Path, *, name: str = PLAN_NAME, text: str = PLAN) -> Path:
    path = tmp_path / "docs" / "plans" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _ctx(tmp_path: Path, **overrides):
    """A handler context with all ``--checkpoint`` arguments filled."""
    values = {
        "checkpoint": True,
        "session_id": "S",
        "task": ["task-1"],
        "agent": "developer",
        "status": "completed",
        "plan": None,
        "plan_id": None,
        "description": None,
        "summary": None,
        "next_step": None,
    }
    values.update(overrides)
    args = SimpleNamespace(**values)
    return SimpleNamespace(
        args=args,
        project_root=tmp_path,
        config={},
        log=MagicMock(),
    )


def _last_checkpoint(tmp_path: Path, session_id: str = "S") -> dict:
    session = CheckpointStore(project_root=tmp_path).load_session(session_id)
    assert session is not None, "session must exist after a successful write"
    return session["checkpoints"][-1]


# --- AC-33: explicit identity ------------------------------------------------


def test_record_with_plan_id_sets_ref(tmp_path):
    code = record_checkpoint(
        tmp_path,
        {},
        SyncLog(),
        session_id="S",
        task_id="task-1",
        agent="developer",
        status="completed",
        plan_id="p",
    )

    assert code == 0
    checkpoint = _last_checkpoint(tmp_path)
    assert checkpoint["plan_id"] == "p"
    assert checkpoint["task_ref"] == "p#task-1"
    assert checkpoint["status"] == "completed"


def test_handler_with_plan_id_sets_ref(tmp_path):
    ctx = _ctx(tmp_path, plan_id="p", task=["task-1"])

    with pytest.raises(SystemExit) as exc:
        _handle_checkpoint(ctx)

    assert exc.value.code == 0
    assert ctx.mode == MODE
    checkpoint = _last_checkpoint(tmp_path)
    assert checkpoint["plan_id"] == "p"
    assert checkpoint["task_ref"] == "p#task-1"


def test_record_with_plan_path_derives_id(tmp_path):
    plan = _plan(tmp_path)
    ctx = _ctx(tmp_path, task=["task-2"], plan=str(plan.relative_to(tmp_path)))

    with pytest.raises(SystemExit) as exc:
        _handle_checkpoint(ctx)

    assert exc.value.code == 0
    checkpoint = _last_checkpoint(tmp_path)
    assert checkpoint["plan_id"] == "p-from-file"
    assert checkpoint["task_ref"] == "p-from-file#task-2"


def test_plan_id_wins_over_plan_path(tmp_path):
    plan = _plan(tmp_path)
    ctx = _ctx(tmp_path, task=["task-2"], plan=str(plan), plan_id="explicit")

    with pytest.raises(SystemExit):
        _handle_checkpoint(ctx)

    assert _last_checkpoint(tmp_path)["plan_id"] == "explicit"


def test_record_without_plan_is_null_identity(tmp_path):
    ctx = _ctx(tmp_path, task=["task-3"])

    with pytest.raises(SystemExit) as exc:
        _handle_checkpoint(ctx)

    assert exc.value.code == 0
    checkpoint = _last_checkpoint(tmp_path)
    assert checkpoint["plan_id"] is None
    assert checkpoint["task_ref"] is None


# --- M1: normalization before the ref ---------------------------------------


def test_task_id_normalized_before_ref(tmp_path):
    ctx = _ctx(tmp_path, task=["3"], plan_id="p")

    with pytest.raises(SystemExit) as exc:
        _handle_checkpoint(ctx)

    assert exc.value.code == 0
    checkpoint = _last_checkpoint(tmp_path)
    assert checkpoint["task_id"] == "task-3"
    assert checkpoint["task_ref"] == "p#task-3"


def test_task_id_normalized_without_plan(tmp_path):
    code = record_checkpoint(
        tmp_path,
        {},
        SyncLog(),
        session_id="S",
        task_id="7",
        agent="developer",
        status="in_progress",
    )

    assert code == 0
    checkpoint = _last_checkpoint(tmp_path)
    assert checkpoint["task_id"] == "task-7"
    assert checkpoint["task_ref"] is None


# --- M3: manual validation, exit 1, no write ---------------------------------


@pytest.mark.parametrize("missing", ["session_id", "task", "agent", "status"])
def test_missing_required_arg_exits_1_without_write(tmp_path, missing):
    overrides = {missing: None}
    ctx = _ctx(tmp_path, **overrides)

    with pytest.raises(SystemExit) as exc:
        _handle_checkpoint(ctx)

    assert exc.value.code == 1
    assert not (tmp_path / ".meta-viz").exists()
    assert CheckpointStore(project_root=tmp_path).load_session("S") is None


def test_invalid_status_exits_1_without_write(tmp_path):
    ctx = _ctx(tmp_path, status="bogus")

    with pytest.raises(SystemExit) as exc:
        _handle_checkpoint(ctx)

    assert exc.value.code == 1
    assert not (tmp_path / ".meta-viz").exists()
    assert "completed" in " ".join(ALLOWED_STATUSES)


def test_store_oserror_exits_1(tmp_path, monkeypatch):
    class _BoomStore:
        def __init__(self, *args, **kwargs):
            pass

        @classmethod
        def from_config(cls, *args, **kwargs):
            return cls()

        def save_checkpoint(self, *args, **kwargs):
            raise OSError("boom")

    monkeypatch.setattr(checkpoint_record, "CheckpointStore", _BoomStore)

    code = record_checkpoint(
        tmp_path,
        {},
        SyncLog(),
        session_id="S",
        task_id="task-1",
        agent="developer",
        status="completed",
        plan_id="p",
    )

    assert code == 1


def test_handler_store_oserror_exits_1(tmp_path, monkeypatch):
    class _BoomStore:
        def __init__(self, *args, **kwargs):
            pass

        @classmethod
        def from_config(cls, *args, **kwargs):
            return cls()

        def save_checkpoint(self, *args, **kwargs):
            raise OSError("boom")

    monkeypatch.setattr(checkpoint_record, "CheckpointStore", _BoomStore)

    with pytest.raises(SystemExit) as exc:
        _handle_checkpoint(_ctx(tmp_path, plan_id="p"))

    assert exc.value.code == 1


# --- IC-11 path-traversal containment ----------------------------------------


def test_traversal_session_id_exits_1_and_writes_nothing(tmp_path):
    """``--session-id ../../../escape`` must never write outside the root."""
    ctx = _ctx(tmp_path, session_id="../../../escape", plan_id="p")

    with pytest.raises(SystemExit) as exc:
        _handle_checkpoint(ctx)

    assert exc.value.code == 1
    assert not (tmp_path / ".meta-viz").exists()
    assert not (tmp_path.parent / "escape.json").exists()


@pytest.mark.parametrize("session_id", ["..", "a/b", "..\\..\\win", "a..b"])
def test_store_rejects_unsafe_session_id(tmp_path, session_id):
    """Defense-in-depth: the store itself refuses an unsafe session id."""
    store = CheckpointStore(project_root=tmp_path)
    checkpoint = Checkpoint(
        task_id="task-1",
        agent="developer",
        task_description="d",
        status="completed",
    )

    with pytest.raises(ValueError):
        store.save_checkpoint(session_id, checkpoint)


def test_store_rejects_absolute_session_id(tmp_path):
    store = CheckpointStore(project_root=tmp_path)

    with pytest.raises(ValueError):
        store._session_file(str(tmp_path / "absolute-escape"))


def test_legit_session_id_still_accepted(tmp_path):
    """The containment guard must not reject legitimate UUID/date session ids."""
    store = CheckpointStore(project_root=tmp_path)
    checkpoint = Checkpoint(
        task_id="task-1",
        agent="developer",
        task_description="d",
        status="completed",
    )

    store.save_checkpoint("orch-2026-09-13-abcd1234", checkpoint)

    assert store.load_session("orch-2026-09-13-abcd1234") is not None


# --- CLI wiring --------------------------------------------------------------


def test_flag_registered_in_parser():
    from sync import _build_arg_parser

    args = _build_arg_parser().parse_args([
        "--checkpoint",
        "--session-id", "S",
        "--task", "task-1",
        "--agent", "developer",
        "--status", "completed",
        "--plan-id", "p",
    ])

    assert args.checkpoint is True
    assert args.session_id == "S"
    assert args.task == ["task-1"]
    assert args.agent == "developer"
    assert args.status == "completed"
    assert args.plan_id == "p"


def test_optional_text_flags_reach_the_checkpoint(tmp_path):
    ctx = _ctx(
        tmp_path,
        task=["task-1"],
        plan_id="p",
        description="do the thing",
        summary="all good",
        next_step="continue",
    )

    with pytest.raises(SystemExit):
        _handle_checkpoint(ctx)

    checkpoint = _last_checkpoint(tmp_path)
    assert checkpoint["task_description"] == "do the thing"
    assert checkpoint["status_summary"] == "all good"
    assert checkpoint["next_step"] == "continue"
