"""Checkpoint.pipeline/.stage fields (design doc 2026-09-10-live-progress-
channel-design.md, Architecture §3): optional, backward compatible."""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.checkpoint import Checkpoint  # noqa: E402


def test_pipeline_and_stage_round_trip_through_to_dict_from_dict():
    cp = Checkpoint(
        task_id="t1", agent="se-requirements", task_description="L1 REQs",
        status="in_progress", pipeline="se-cascade", stage="l1-requirements",
    )
    restored = Checkpoint.from_dict(cp.to_dict())
    assert restored.pipeline == "se-cascade"
    assert restored.stage == "l1-requirements"


def test_pipeline_and_stage_default_to_none():
    cp = Checkpoint(task_id="t1", agent="developer", task_description="x", status="pending")
    assert cp.pipeline is None
    assert cp.stage is None


def test_from_dict_without_pipeline_keys_does_not_crash():
    # Simulates a checkpoint JSON written before this field existed.
    legacy_dict = {
        "task_id": "t1", "agent": "developer", "task_description": "x",
        "status": "completed",
    }
    restored = Checkpoint.from_dict(legacy_dict)
    assert restored.pipeline is None
    assert restored.stage is None
