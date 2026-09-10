""".meta-viz/progress/current.md write-through on every checkpoint save
(issue #682 §6, Option A; path made provider-neutral by the live-progress-
channel design, 2026-09-10) -- human-readable progress snapshot, overwritten
each time on Tier-A providers, not historized. Reuses the same table format
as the orchestrator status-table snippet (issue #678) so the text can be
copy-pasted between the two surfaces."""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.checkpoint import Checkpoint, CheckpointStore  # noqa: E402


def _store(tmp_path: Path) -> CheckpointStore:
    return CheckpointStore(project_root=tmp_path)


def test_save_checkpoint_writes_progress_file(tmp_path):
    store = _store(tmp_path)
    cp = Checkpoint(
        task_id="t1", agent="developer", task_description="implement X",
        status="completed", status_summary="On track.",
    )
    store.save_checkpoint("sess1", cp)
    progress_path = tmp_path / ".meta-viz" / "progress" / "current.md"
    assert progress_path.exists()
    content = progress_path.read_text(encoding="utf-8")
    assert "developer" in content
    assert "implement X" in content
    assert "completed" in content
    assert "On track." in content


def test_progress_file_is_overwritten_not_appended(tmp_path):
    store = _store(tmp_path)
    store.save_checkpoint(
        "sess1", Checkpoint(task_id="t1", agent="developer", task_description="first", status="completed")
    )
    store.save_checkpoint(
        "sess1", Checkpoint(task_id="t2", agent="tester", task_description="second", status="in_progress")
    )
    content = (tmp_path / ".meta-viz" / "progress" / "current.md").read_text(encoding="utf-8")
    # Both checkpoints of the session appear (cumulative table), but the
    # file itself was overwritten (single write_atomic call), not appended to.
    # Default tier (no .meta-config/project.yaml present) resolves to
    # Tier A -- see Task 5 -- so overwrite semantics stay the pre-existing
    # default for this bare-tmp_path fixture shape.
    assert "first" in content
    assert "second" in content
    assert content.count("| Agent | Task | Status |") == 1


def test_progress_file_survives_corrupt_existing_session_json(tmp_path):
    store = _store(tmp_path)
    # Simulate a corrupt session file (#576 fail-soft contract) -- must not
    # crash the progress write either.
    store.checkpoint_dir.mkdir(parents=True)
    (store.checkpoint_dir / "sess1.json").write_text("{not valid json", encoding="utf-8")
    store.save_checkpoint(
        "sess1", Checkpoint(task_id="t1", agent="developer", task_description="x", status="pending")
    )
    assert (tmp_path / ".meta-viz" / "progress" / "current.md").exists()
