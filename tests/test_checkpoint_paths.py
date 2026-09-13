"""CheckpointStore path injection, ``from_config`` and default compatibility.

Covers AC-07, AC-08 and AC-15 of ``SPEC-PROGRESS-PATHS-CONFIG-2026-09-13``:
the default constructor stays byte-identical to the historical ``.meta-viz``
layout, the resolved directories are honoured when injected, and the
defense-in-depth confinements of IC-03 keep holding for custom directories.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import checkpoint as checkpoint_module  # noqa: E402
from lib.checkpoint import (  # noqa: E402
    Checkpoint,
    CheckpointStore,
    _render_progress_markdown,
)
from lib.progress_paths import (  # noqa: E402
    DEFAULT_CHECKPOINT_DIR,
    DEFAULT_PROGRESS_DIR,
)


def _cp(task_id="t1", agent="developer", description="do x", status="completed"):
    return Checkpoint(
        task_id=task_id,
        agent=agent,
        task_description=description,
        status=status,
        status_summary="On track.",
    )


def test_default_constructor_is_byte_identical(tmp_path):
    store = CheckpointStore(project_root=tmp_path)
    store.save_checkpoint("sess1", _cp())

    session_json = tmp_path / ".meta-viz" / "checkpoints" / "sess1.json"
    progress_file = tmp_path / ".meta-viz" / "progress" / "current.md"
    assert session_json.exists()
    assert progress_file.exists()

    session = store.load_session("sess1")
    assert session is not None
    # The progress bytes are exactly the pre-change rendering.
    assert progress_file.read_text(encoding="utf-8") == _render_progress_markdown(session)


def test_two_argument_constructor_backward_compatible(tmp_path):
    store = CheckpointStore(tmp_path, None)

    assert store.checkpoint_dir == tmp_path / DEFAULT_CHECKPOINT_DIR
    assert store.progress_dir == tmp_path / DEFAULT_PROGRESS_DIR
    store.save_checkpoint("sess2", _cp())
    assert (tmp_path / ".meta-viz" / "checkpoints" / "sess2.json").exists()


def test_from_config_honours_both_overrides(tmp_path):
    store = CheckpointStore.from_config(
        tmp_path,
        {"progress": {"dir": ".run/progress", "checkpoint-dir": ".run/checkpoints"}},
    )
    assert store.progress_dir == tmp_path / ".run" / "progress"
    assert store.checkpoint_dir == tmp_path / ".run" / "checkpoints"

    store.save_checkpoint("sess3", _cp())

    assert (tmp_path / ".run" / "checkpoints" / "sess3.json").exists()
    assert (tmp_path / ".run" / "progress" / "current.md").exists()
    assert not (tmp_path / ".meta-viz").exists()


def test_write_progress_file_confined_to_progress_dir(tmp_path):
    progress_dir = tmp_path / "custom-progress"
    progress_dir.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("untouched", encoding="utf-8")
    # A symlinked current.md resolves outside the progress dir; the guard must
    # refuse the write instead of following it.
    (progress_dir / "current.md").symlink_to(outside)

    store = CheckpointStore(project_root=tmp_path, progress_dir=progress_dir)
    store.save_checkpoint("sess4", _cp())

    assert outside.read_text(encoding="utf-8") == "untouched"
    assert (progress_dir / "current.md").is_symlink()


def test_custom_checkpoint_dir_keeps_session_confinement(tmp_path):
    custom = tmp_path / "cps"
    store = CheckpointStore(project_root=tmp_path, checkpoint_dir=custom)

    with pytest.raises(ValueError):
        store._session_file("../evil")
    assert store._session_file("ok") == (custom / "ok.json").resolve()


def test_module_aliases_point_to_new_defaults():
    assert checkpoint_module.CHECKPOINT_DIR == DEFAULT_CHECKPOINT_DIR
    assert checkpoint_module._PROGRESS_DIR == DEFAULT_PROGRESS_DIR
    assert checkpoint_module.CHECKPOINT_DIR == ".meta-viz/checkpoints"
    assert checkpoint_module._PROGRESS_DIR == ".meta-viz/progress"
