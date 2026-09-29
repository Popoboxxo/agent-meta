"""IC-04 read-only ``--rehydrate`` CLI mode (AC-20).

``--rehydrate`` prints the resume context for the newest unfinished session and
writes nothing. "Nothing to resume" is informational: the mode returns exit
code ``0`` and prints an explicit note, it is never a failure.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.checkpoint import Checkpoint, CheckpointStore
from lib.log import SyncLog
from lib.rehydrate import MODE, _handle_rehydrate, rehydrate

PLAN = (
    "# Demo plan\n\n"
    "> plan-id: p\n"
    "> Status: in-progress\n\n"
    "### Task 1: First\n"
    "- [x] done\n\n"
    "### Task 2: Second\n"
    "- [ ] open\n\n"
    "### Task 3: Third\n"
    "- [ ] open\n"
)


def _write_plan(project_root: Path) -> Path:
    path = project_root / "docs" / "plans" / "2026-09-13-demo.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(PLAN, encoding="utf-8")
    return path


def _session_with_open_task(project_root: Path) -> CheckpointStore:
    """A store session whose newest checkpoint is still unfinished (task-2)."""
    _write_plan(project_root)
    store = CheckpointStore(project_root=project_root)
    store.save_checkpoint("sess-1", Checkpoint(
        task_id="task-1", agent="developer", task_description="first",
        status="completed", plan_id="p",
    ))
    store.save_checkpoint("sess-1", Checkpoint(
        task_id="task-2", agent="developer", task_description="second",
        status="in_progress", plan_id="p",
    ))
    return store


def _snapshot(root: Path) -> set:
    """Identity of every file under ``root`` (path, size, mtime)."""
    return {
        (p.relative_to(root).as_posix(), p.stat().st_size, p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }


def test_no_unfinished_session_exit_0_with_note(tmp_path, capsys):
    code = rehydrate(tmp_path, {}, SyncLog())
    out = capsys.readouterr().out
    assert code == 0
    assert "no unfinished session" in out.lower()


def test_resumable_session_prints_context_exit_0(tmp_path, capsys):
    _session_with_open_task(tmp_path)
    code = rehydrate(tmp_path, {}, SyncLog())
    out = capsys.readouterr().out
    assert code == 0
    assert "sess-1" in out
    assert "p#task-2" in out


def test_rehydrate_disabled_prints_and_exit_0(tmp_path, capsys):
    _session_with_open_task(tmp_path)
    config = {"spec-plan-workflow": {"recovery": {"rehydrate": False}}}
    code = rehydrate(tmp_path, config, SyncLog())
    out = capsys.readouterr().out
    assert code == 0
    assert "rehydrate disabled" in out.lower()


def test_rehydrate_writes_no_file(tmp_path):
    _session_with_open_task(tmp_path)
    before = _snapshot(tmp_path)
    rehydrate(tmp_path, {}, SyncLog())
    assert _snapshot(tmp_path) == before


def test_flag_registered_in_parser():
    from sync import _build_arg_parser
    args = _build_arg_parser().parse_args(["--rehydrate"])
    assert args.rehydrate is True


def test_handler_sets_mode_and_exits_zero(tmp_path, capsys):
    class _Ctx:
        pass

    ctx = _Ctx()
    ctx.project_root = tmp_path
    ctx.config = {}
    ctx.log = SyncLog()
    ctx.mode = None
    ctx.read_only = False

    try:
        _handle_rehydrate(ctx)
    except SystemExit as exc:
        code = exc.code
    else:  # pragma: no cover - the handler must exit directly
        raise AssertionError("_handle_rehydrate must call sys.exit")

    assert code == 0
    assert ctx.mode == MODE
    assert ctx.read_only is True
