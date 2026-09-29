"""IC-03 read-only recovery resolver (AC-17/18/19 + M4).

Covers the merge of the legacy hand-written checkpoint format with the
``CheckpointStore`` session format, the resumable-session selection and the
resume-context construction/rendering. The resolver must be read-only, must
never raise for content problems and must resolve the plans directory from
``spec-plan-workflow.paths.plans`` (M4), never from a hard-coded path.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.checkpoint import CheckpointStore
from lib.plan_identity import make_task_ref
from lib.recovery import (
    REHYDRATE_CONFIG_PATH,
    RecoverySource,
    ResumeContext,
    build_resume_context,
    find_resumable_session,
    load_legacy_checkpoints,
    load_store_sources,
    render_resume_context,
    resolve_recovery_sources,
)

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

COMPLETE_PLAN = (
    "# Demo plan\n\n"
    "> plan-id: p\n"
    "> Status: complete\n\n"
    "### Task 1: First\n"
    "- [x] done\n"
)

# Same derived plan id, different ledger -- a hard-coded ``docs/plans`` lookup
# would pick this one up and report the wrong ``next_task_ref`` (M4).
DECOY_PLAN = (
    "# Decoy plan\n\n"
    "> plan-id: p\n"
    "> Status: in-progress\n\n"
    "### Task 1: First\n"
    "- [x] done\n\n"
    "### Task 2: Second\n"
    "- [x] done\n\n"
    "### Task 3: Third\n"
    "- [ ] open\n"
)


def _store(tmp_path: Path) -> CheckpointStore:
    return CheckpointStore(project_root=tmp_path)


def _write_plan(tmp_path: Path, rel: str = "docs/plans/2026-09-13-demo.md",
                text: str = PLAN) -> Path:
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _write_config(tmp_path: Path, text: str) -> None:
    cfg = tmp_path / ".meta-config"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "project.yaml").write_text(text, encoding="utf-8")


def _write_legacy(
    tmp_path: Path,
    session_id: str,
    *,
    filename: str = "checkpoint-20260913-100000.json",
    created_at=None,
    completed=None,
    pending=None,
) -> Path:
    viz = tmp_path / ".meta-viz"
    viz.mkdir(parents=True, exist_ok=True)
    data = {
        "session_id": session_id,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "task_summary": "Overall task",
        "completed_steps": completed if completed is not None else [],
        "pending_steps": pending if pending is not None else [],
        "context": "intermediate results",
        "unknown_key": "ignored",
    }
    path = viz / filename
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _write_store_session(
    tmp_path: Path,
    session_id: str,
    entries,
    *,
    plan_id="p",
    updated_at=None,
) -> CheckpointStore:
    """Write a raw store session with full control over ``updated_at``."""
    ts = time.time() if updated_at is None else updated_at
    checkpoints = []
    for index, (task_id, status) in enumerate(entries):
        checkpoints.append({
            "id": "{}-{}".format(session_id, index),
            "task_id": task_id,
            "agent": "developer",
            "task_description": "task " + task_id,
            "status": status,
            "result": None,
            "next_step": None,
            "status_summary": None,
            "pipeline": None,
            "stage": None,
            "timestamp": ts + index,
            "plan_id": plan_id,
            "task_ref": make_task_ref(plan_id, task_id),
        })
    data = {
        "session_id": session_id,
        "created_at": ts,
        "updated_at": ts,
        "checkpoints": checkpoints,
    }
    store = _store(tmp_path)
    store.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    (store.checkpoint_dir / (session_id + ".json")).write_text(
        json.dumps(data), encoding="utf-8"
    )
    return store


# ---------------------------------------------------------------------------
# AC-17 -- legacy source + store precedence
# ---------------------------------------------------------------------------


def test_legacy_checkpoint_source(tmp_path):
    _write_legacy(
        tmp_path,
        "sess-legacy",
        completed=[{"step": 1, "agent": "developer", "result_key": "k",
                    "status": "done"}],
        pending=[{"step": 2, "agent": "developer", "task": "next"},
                 {"step": 3, "task_ref": "p#task-3", "task": "later"}],
    )

    sources = resolve_recovery_sources(tmp_path)

    assert len(sources) == 1
    source = sources[0]
    assert isinstance(source, RecoverySource)
    assert source.source_format == "legacy"
    assert source.session_id == "sess-legacy"
    assert source.plan_id is None
    assert source.completed_task_refs == ("step:1",)
    # Pending steps without a task id become ``step:<n>``; explicit refs win.
    assert source.pending_task_refs == ("step:2", "p#task-3")


def test_store_wins_on_duplicate_session_id(tmp_path):
    _write_legacy(tmp_path, "dup")
    _write_store_session(tmp_path, "dup", [("task-1", "running")], plan_id=None)

    sources = resolve_recovery_sources(tmp_path)

    duplicates = [s for s in sources if s.session_id == "dup"]
    assert len(sources) == 1
    assert len(duplicates) == 1
    assert duplicates[0].source_format == "store"


def test_malformed_legacy_is_skipped(tmp_path):
    viz = tmp_path / ".meta-viz"
    viz.mkdir(parents=True, exist_ok=True)
    (viz / "checkpoint-broken.json").write_text("{not json", encoding="utf-8")
    _write_legacy(tmp_path, "sess-ok")

    sources = resolve_recovery_sources(tmp_path)

    assert [s.session_id for s in sources] == ["sess-ok"]


# ---------------------------------------------------------------------------
# AC-18 -- resumable selection
# ---------------------------------------------------------------------------


def test_find_resumable_skips_completed(tmp_path):
    _write_plan(tmp_path, text=COMPLETE_PLAN)
    _write_store_session(tmp_path, "sess-done", [("task-1", "completed")])

    assert find_resumable_session(tmp_path) is None


def test_find_resumable_newest_first(tmp_path):
    now = time.time()
    _write_store_session(
        tmp_path, "sess-old", [("task-1", "running")],
        plan_id=None, updated_at=now - 100,
    )
    _write_store_session(
        tmp_path, "sess-new", [("task-1", "running")],
        plan_id=None, updated_at=now - 10,
    )

    resumable = find_resumable_session(tmp_path)

    assert resumable is not None
    assert resumable.session_id == "sess-new"


# ---------------------------------------------------------------------------
# AC-19 -- resume context + rendering
# ---------------------------------------------------------------------------


def test_build_resume_context_next_task_ref(tmp_path):
    _write_plan(tmp_path)
    store = _write_store_session(tmp_path, "sess-1", [("task-1", "completed")])

    context = build_resume_context(tmp_path, "sess-1", store=store)

    assert isinstance(context, ResumeContext)
    assert context.session_id == "sess-1"
    assert context.plan_id == "p"
    assert context.source_format == "store"
    assert context.completed_task_refs == ("p#task-1",)
    # First ledger task absent from the completed refs.
    assert context.next_task_ref == "p#task-2"
    assert context.plan_path == "docs/plans/2026-09-13-demo.md"
    assert context.drift == ()


def test_build_resume_context_unknown_session_returns_none(tmp_path):
    assert build_resume_context(tmp_path, "does-not-exist") is None


def test_render_contains_session_and_no_role_name(tmp_path):
    _write_plan(tmp_path)
    store = _write_store_session(tmp_path, "sess-77", [("task-1", "completed")])
    context = build_resume_context(tmp_path, "sess-77", store=store)

    text = render_resume_context(context)

    assert "sess-77" in text
    assert "p#task-2" in text
    lowered = text.lower()
    for role in ("developer", "orchestrator", "validator", "code-reviewer",
                 "senior-developer", "tester"):
        assert role not in lowered


# ---------------------------------------------------------------------------
# M4 -- plans directory comes from the project config
# ---------------------------------------------------------------------------


def test_build_resume_context_uses_configured_plans_dir(tmp_path):
    _write_config(
        tmp_path,
        "spec-plan-workflow:\n"
        "  paths:\n"
        "    plans: custom/plans\n",
    )
    _write_plan(tmp_path, rel="custom/plans/2026-09-13-demo.md", text=PLAN)
    # Hard-coded ``docs/plans`` must not win.
    _write_plan(tmp_path, rel="docs/plans/2026-09-13-demo.md", text=DECOY_PLAN)
    store = _write_store_session(tmp_path, "sess-m4", [("task-1", "completed")])

    context = build_resume_context(tmp_path, "sess-m4", store=store)

    assert context.plan_path == "custom/plans/2026-09-13-demo.md"
    assert context.next_task_ref == "p#task-2"


def test_rehydrate_config_path_constant():
    assert REHYDRATE_CONFIG_PATH == "spec-plan-workflow.recovery.rehydrate"
