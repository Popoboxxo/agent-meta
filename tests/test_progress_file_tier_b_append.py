"""Tier-B append + rotation for the progress file (design doc
2026-09-10-live-progress-channel-design.md, Architecture §1)."""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib import checkpoint as checkpoint_lib  # noqa: E402
from lib.checkpoint import Checkpoint, CheckpointStore  # noqa: E402


def _tier_b_store(tmp_path: Path) -> CheckpointStore:
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        "ai-providers: [Opencode]\n", encoding="utf-8"
    )
    return CheckpointStore(project_root=tmp_path, agent_meta_root=_REPO_ROOT)


def test_tier_b_appends_both_checkpoints(tmp_path):
    store = _tier_b_store(tmp_path)
    store.save_checkpoint(
        "sess1", Checkpoint(task_id="t1", agent="developer", task_description="first", status="completed")
    )
    store.save_checkpoint(
        "sess1", Checkpoint(task_id="t2", agent="tester", task_description="second", status="in_progress")
    )
    content = (tmp_path / ".meta-viz" / "progress" / "current.md").read_text(encoding="utf-8")
    assert "first" in content
    assert "second" in content
    assert content.count("| Agent | Task | Status | Pipeline/Stage |") == 2


def test_tier_b_rotates_on_new_session(tmp_path):
    store = _tier_b_store(tmp_path)
    store.save_checkpoint(
        "sessA", Checkpoint(task_id="t1", agent="developer", task_description="session-a-entry", status="completed")
    )
    store.save_checkpoint(
        "sessB", Checkpoint(task_id="t1", agent="developer", task_description="session-b-entry", status="completed")
    )
    content = (tmp_path / ".meta-viz" / "progress" / "current.md").read_text(encoding="utf-8")
    assert "session-a-entry" not in content
    assert "session-b-entry" in content


def test_tier_b_trims_oldest_entries_over_byte_budget(tmp_path, monkeypatch):
    monkeypatch.setattr(checkpoint_lib, "_PROGRESS_MAX_BYTES", 500)
    store = _tier_b_store(tmp_path)
    for i in range(20):
        store.save_checkpoint(
            "sess1", Checkpoint(task_id=f"t{i}", agent="developer", task_description=f"entry-{i}", status="in_progress")
        )
    content = (tmp_path / ".meta-viz" / "progress" / "current.md").read_text(encoding="utf-8")
    assert len(content.encode("utf-8")) <= 500
    assert "entry-19" in content
    assert "entry-0" not in content
