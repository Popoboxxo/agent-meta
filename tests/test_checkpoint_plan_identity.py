"""IC-02: plan identity on checkpoints (AC-04/05/06).

Covers the backward-compatible checkpoint schema extension
(``plan_id``/``task_ref``) and the two query helpers
``CheckpointStore.get_checkpoint_for_task`` / ``find_sessions_for_plan``.

Existing checkpoint JSON without the new keys must keep loading; the four
hard-required fields stay enforced. Identity is explicit, never random.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.checkpoint import Checkpoint, CheckpointStore
from lib.plan_identity import make_task_ref


def _store(tmp_path: Path) -> CheckpointStore:
    return CheckpointStore(project_root=tmp_path)


def _legacy_data() -> dict:
    """A checkpoint JSON exactly as written before the schema extension."""
    return {
        "id": "legacy-id",
        "task_id": "task-3",
        "agent": "developer",
        "task_description": "desc",
        "status": "completed",
        "result": "done",
        "next_step": None,
        "status_summary": "summary",
        "pipeline": "concept-driven-dev",
        "stage": "implement",
        "timestamp": 1700000000.0,
    }


def _write_session(store: CheckpointStore, session_id: str, *, plan_id, updated_at, task_id="task-1"):
    """Write a raw session JSON with full control over ``updated_at``."""
    store.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "session_id": session_id,
        "created_at": updated_at,
        "updated_at": updated_at,
        "checkpoints": [
            {
                **_legacy_data(),
                "id": "id-" + session_id,
                "task_id": task_id,
                "timestamp": updated_at,
                "plan_id": plan_id,
                "task_ref": make_task_ref(plan_id, task_id),
            }
        ],
    }
    (store.checkpoint_dir / f"{session_id}.json").write_text(
        json.dumps(data), encoding="utf-8"
    )
    return data


# --- AC-04: legacy JSON keeps loading -------------------------------------


def test_from_dict_legacy_without_new_keys():
    cp = Checkpoint.from_dict(_legacy_data())

    assert cp.plan_id is None
    assert cp.task_ref is None
    assert cp.task_id == "task-3"
    assert cp.agent == "developer"
    assert cp.status == "completed"


def test_from_dict_requires_four_hard_fields():
    for missing in ("task_id", "agent", "task_description", "status"):
        data = _legacy_data()
        del data[missing]
        with pytest.raises(KeyError):
            Checkpoint.from_dict(data)


def test_from_dict_backfills_task_ref():
    data = _legacy_data()
    data["plan_id"] = "p"
    cp = Checkpoint.from_dict(data)
    assert cp.plan_id == "p"
    assert cp.task_ref == "p#task-3"

    data["task_ref"] = "explicit-ref"
    assert Checkpoint.from_dict(data).task_ref == "explicit-ref"


def test_round_trip_serializes_plan_fields():
    cp = Checkpoint(
        task_id="task-3",
        agent="developer",
        task_description="desc",
        status="completed",
        plan_id="p",
        task_ref="p#task-3",
    )
    payload = cp.to_dict()
    assert payload["plan_id"] == "p"
    assert payload["task_ref"] == "p#task-3"

    restored = Checkpoint.from_dict(payload)
    assert restored.plan_id == "p"
    assert restored.task_ref == "p#task-3"


# --- AC-05: get_checkpoint_for_task / find_sessions_for_plan --------------


def test_get_checkpoint_for_task_hit_miss_and_backcompat(tmp_path):
    store = _store(tmp_path)

    # Stored WITHOUT task_ref (only plan_id) -> back-compat reconstruction.
    store.save_checkpoint(
        "sess1",
        Checkpoint(
            task_id="task-3",
            agent="developer",
            task_description="desc",
            status="completed",
            plan_id="p",
        ),
    )
    # Stored WITH explicit task_ref.
    store.save_checkpoint(
        "sess1",
        Checkpoint(
            task_id="task-4",
            agent="developer",
            task_description="desc2",
            status="failed",
            plan_id="p",
            task_ref="p#task-4",
        ),
    )

    hit = store.get_checkpoint_for_task("sess1", "p#task-3")
    assert hit is not None
    assert hit.task_id == "task-3"

    hit = store.get_checkpoint_for_task("sess1", "p#task-4")
    assert hit is not None
    assert hit.task_id == "task-4"
    assert hit.status == "failed"

    assert store.get_checkpoint_for_task("sess1", "p#task-99") is None
    assert store.get_checkpoint_for_task("unknown-session", "p#task-3") is None


def test_get_checkpoint_for_task_returns_most_recent_match(tmp_path):
    store = _store(tmp_path)
    for status in ("in_progress", "completed"):
        store.save_checkpoint(
            "sess1",
            Checkpoint(
                task_id="task-3",
                agent="developer",
                task_description="desc",
                status=status,
                plan_id="p",
            ),
        )

    latest = store.get_checkpoint_for_task("sess1", "p#task-3")
    assert latest is not None
    assert latest.status == "completed"


def test_find_sessions_for_plan_hit_miss_and_ordering(tmp_path):
    store = _store(tmp_path)
    _write_session(store, "s-old", plan_id="p", updated_at=100.0)
    _write_session(store, "s-new", plan_id="p", updated_at=200.0)
    _write_session(store, "s-other", plan_id="q", updated_at=300.0)

    assert store.find_sessions_for_plan("p") == ["s-new", "s-old"]
    assert store.find_sessions_for_plan("q") == ["s-other"]
    assert store.find_sessions_for_plan("unknown") == []
    assert store.find_sessions_for_plan("") == []


# --- AC-06: corrupt files are skipped, never raised -----------------------


def test_find_sessions_for_plan_skips_corrupt_file(tmp_path):
    store = _store(tmp_path)
    _write_session(store, "sess-valid", plan_id="p", updated_at=100.0)
    _write_session(store, "sess-other", plan_id="q", updated_at=100.0)

    store.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    (store.checkpoint_dir / "sess-corrupt.json").write_text(
        "{not valid json", encoding="utf-8"
    )

    assert store.find_sessions_for_plan("p") == ["sess-valid"]
    assert store.find_sessions_for_plan("unknown") == []


# --- AC-06: entry-level corruption is fail-soft, never raised --------------


def test_get_checkpoint_for_task_fail_soft_on_corrupt_entries(tmp_path):
    store = _store(tmp_path)
    store.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "session_id": "sess-bad",
        "created_at": 10.0,
        "updated_at": 10.0,
        "checkpoints": [
            "not-a-dict",
            {
                "agent": "developer",
                "task_description": "missing task_id",
                "status": "completed",
                "plan_id": "p",
            },
            {
                "task_id": "task-3",
                "agent": "developer",
                "task_description": "ok",
                "status": "completed",
                "plan_id": "p",
                "task_ref": "p#task-3",
            },
        ],
    }
    (store.checkpoint_dir / "sess-bad.json").write_text(
        json.dumps(data), encoding="utf-8"
    )

    hit = store.get_checkpoint_for_task("sess-bad", "p#task-3")
    assert hit is not None
    assert hit.task_id == "task-3"
    assert store.get_checkpoint_for_task("sess-bad", "p#task-99") is None


def test_find_sessions_for_plan_fail_soft_on_corrupt_entries(tmp_path):
    store = _store(tmp_path)
    _write_session(store, "sess-good", plan_id="p", updated_at=100.0)
    store.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    bad = {
        "session_id": "sess-bad",
        "created_at": 50.0,
        "updated_at": 50.0,
        "checkpoints": [
            "not-a-dict",
            {"agent": "developer", "status": "completed"},
        ],
    }
    (store.checkpoint_dir / "sess-bad.json").write_text(
        json.dumps(bad), encoding="utf-8"
    )

    assert store.find_sessions_for_plan("p") == ["sess-good"]


def _write_raw_session(store: CheckpointStore, session_id: str, checkpoints: list):
    """Write a session JSON with fully controlled (possibly corrupt) entries."""
    store.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "session_id": session_id,
        "created_at": 10.0,
        "updated_at": 10.0,
        "checkpoints": checkpoints,
    }
    (store.checkpoint_dir / f"{session_id}.json").write_text(
        json.dumps(data), encoding="utf-8"
    )
    return data


def test_get_completed_steps_fail_soft_on_corrupt_entries(tmp_path):
    """MINOR-A: a corrupt entry must not crash get_completed_steps; the valid
    completed entry stays visible (reachable from the ledger drift check)."""
    store = _store(tmp_path)
    _write_raw_session(store, "sess-bad", [
        "not-a-dict",
        {"agent": "developer", "task_description": "missing task_id",
         "status": "completed"},
        {**_legacy_data(), "task_id": "task-ok", "id": "id-ok"},
    ])

    steps = store.get_completed_steps("sess-bad")
    assert [cp.task_id for cp in steps] == ["task-ok"]


def test_get_last_checkpoint_fail_soft_on_corrupt_entries(tmp_path):
    """MINOR-A: a corrupt newest entry is skipped; the most recent *valid*
    checkpoint is returned instead of raising."""
    store = _store(tmp_path)
    _write_raw_session(store, "sess-bad", [
        {**_legacy_data(), "task_id": "task-ok", "id": "id-ok"},
        "not-a-dict",
        {"agent": "developer", "status": "completed"},  # missing task_id
    ])

    latest = store.get_last_checkpoint("sess-bad")
    assert latest is not None
    assert latest.task_id == "task-ok"


def test_completed_steps_and_last_checkpoint_fail_soft_on_malformed_container(tmp_path):
    """MINOR-A: a non-list ``checkpoints`` value is fail-soft, too."""
    store = _store(tmp_path)
    store.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    (store.checkpoint_dir / "sess-not-list.json").write_text(
        json.dumps({"session_id": "sess-not-list", "checkpoints": "nope"}),
        encoding="utf-8",
    )

    assert store.get_completed_steps("sess-not-list") == []
    assert store.get_last_checkpoint("sess-not-list") is None
