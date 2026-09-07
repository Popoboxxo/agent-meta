"""Checkpoint.status_summary field (issue #682 §6, Option A).

Optional, backward compatible: existing checkpoint JSON without the key
must still load (old sessions predate this field).
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.checkpoint import Checkpoint  # noqa: E402


def test_status_summary_round_trips_through_to_dict_from_dict():
    cp = Checkpoint(
        task_id="t1", agent="developer", task_description="implement X",
        status="completed", status_summary="developer: done. tester: pending.",
    )
    restored = Checkpoint.from_dict(cp.to_dict())
    assert restored.status_summary == "developer: done. tester: pending."


def test_status_summary_defaults_to_none():
    cp = Checkpoint(task_id="t1", agent="developer", task_description="x", status="pending")
    assert cp.status_summary is None
    assert cp.to_dict()["status_summary"] is None


def test_from_dict_without_status_summary_key_does_not_crash():
    # Simulates a checkpoint JSON written before this field existed.
    legacy_dict = {
        "task_id": "t1", "agent": "developer", "task_description": "x",
        "status": "completed",
    }
    restored = Checkpoint.from_dict(legacy_dict)
    assert restored.status_summary is None
