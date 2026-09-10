"""Rollout/migration regression (spec 2026-09-10-live-progress-channel-design.md,
Rollout/Migration section): an existing .claude/progress/current.md from before
the provider-neutral path fix must survive a checkpoint save untouched, and
.gitignore must already cover the new path without a dedicated entry."""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.checkpoint import Checkpoint, CheckpointStore  # noqa: E402


def test_legacy_claude_progress_file_is_left_untouched(tmp_path):
    legacy_dir = tmp_path / ".claude" / "progress"
    legacy_dir.mkdir(parents=True)
    legacy_path = legacy_dir / "current.md"
    legacy_path.write_text("# stale pre-migration snapshot\n", encoding="utf-8")

    store = CheckpointStore(project_root=tmp_path)
    store.save_checkpoint(
        "sess1", Checkpoint(task_id="t1", agent="developer", task_description="x", status="completed")
    )

    assert legacy_path.read_text(encoding="utf-8") == "# stale pre-migration snapshot\n"
    assert (tmp_path / ".meta-viz" / "progress" / "current.md").exists()


def test_gitignore_already_covers_meta_viz_progress_without_a_new_entry():
    gitignore = (_REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    lines = [l.strip() for l in gitignore.splitlines()]
    assert ".meta-viz/" in lines, (
        "the existing generic .meta-viz/ entry must keep covering "
        ".meta-viz/progress/ -- if this line is ever narrowed, a "
        "dedicated .meta-viz/progress/ entry must be added at the same time"
    )
