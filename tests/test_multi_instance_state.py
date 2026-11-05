"""State namespaces for multi-instance orchestrators (P3, AC-10).

SPEC-orchestrator-topology-2026-11-03, Task 5. ``CheckpointStore`` composes
the session id through ``topology.compose_instance_session_id``:

* ``orchestrator_id=None`` (N=1, the default) is the byte-identical historic
  layout ``<checkpoint-dir>/<base>.json`` + ``<progress-dir>/current.md``.
* an instance id namespaces the checkpoint as ``<base>__<id>.json`` and writes
  ``progress-<id>.md`` instead of ``current.md``.

``progress-<id>.md`` is **human-only**: no code consumer reads it.
``current.md`` stays the single machine-read progress file (root session only).
The raw-output directory follows the same composition as the session file.

Run: python3 -m pytest tests/test_multi_instance_state.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.checkpoint import (  # noqa: E402
    Checkpoint,
    CheckpointStore,
    _render_progress_markdown,
    validate_session_id,
)


def _cp(task_id="t1", agent="developer", description="do x", status="completed"):
    return Checkpoint(
        task_id=task_id,
        agent=agent,
        task_description=description,
        status=status,
        status_summary="On track.",
    )


def test_default_store_keeps_the_historic_layout_byte_identically(tmp_path):
    store = CheckpointStore(project_root=tmp_path)
    store.save_checkpoint("sess1", _cp())

    checkpoint_dir = tmp_path / ".meta-viz" / "checkpoints"
    progress_dir = tmp_path / ".meta-viz" / "progress"
    session_json = checkpoint_dir / "sess1.json"
    progress_file = progress_dir / "current.md"

    assert session_json.exists()
    assert progress_file.exists()
    assert progress_file.read_text(encoding="utf-8") == _render_progress_markdown(
        store.load_session("sess1")
    )
    # No instance namespace leaked into N=1 (no ``__`` suffix, no new files).
    assert [p.name for p in checkpoint_dir.iterdir()] == ["sess1.json"]
    assert [p.name for p in progress_dir.iterdir() if p.suffix == ".md"] == [
        "current.md"
    ]


def test_instance_store_namespaces_checkpoint_and_progress(tmp_path):
    store = CheckpointStore(project_root=tmp_path, orchestrator_id="scope-a")
    store.save_checkpoint("sess1", _cp())

    checkpoint_dir = tmp_path / ".meta-viz" / "checkpoints"
    progress_dir = tmp_path / ".meta-viz" / "progress"

    assert (checkpoint_dir / "sess1__scope-a.json").exists()
    assert not (checkpoint_dir / "sess1.json").exists()
    assert (progress_dir / "progress-scope-a.md").exists()
    # ``current.md`` is the root session's machine-read file; the instance
    # store never writes it (and no consumer reads progress-<id>.md).
    assert not (progress_dir / "current.md").exists()


def test_session_file_stays_confined_to_the_checkpoint_dir(tmp_path):
    custom = tmp_path / "cps"
    store = CheckpointStore(
        project_root=tmp_path, checkpoint_dir=custom, orchestrator_id="scope-a"
    )
    assert store._session_file("ok") == (custom / "ok__scope-a.json").resolve()

    with pytest.raises(ValueError):
        store._session_file("../evil")


def test_raw_output_directory_uses_the_same_composition(tmp_path):
    custom = tmp_path / "cps"
    store = CheckpointStore(
        project_root=tmp_path, checkpoint_dir=custom, orchestrator_id="scope-a"
    )
    path = store.save_raw_output("sess1", "t1", "developer", "raw bytes")

    assert path.parent == custom / "sess1__scope-a"
    assert path.read_text(encoding="utf-8") == "raw bytes"
    assert store.list_raw_outputs("sess1") == [path]


def test_validate_session_id_accepts_the_composition():
    validate_session_id("base__scope-a")
    validate_session_id("base__pr-42")


def test_from_config_carries_the_orchestrator_id(tmp_path):
    store = CheckpointStore.from_config(
        tmp_path, None, orchestrator_id="scope-a"
    )
    assert store.orchestrator_id == "scope-a"
    store.save_checkpoint("sess2", _cp())

    assert (
        tmp_path / ".meta-viz" / "checkpoints" / "sess2__scope-a.json"
    ).exists()
    assert (tmp_path / ".meta-viz" / "progress" / "progress-scope-a.md").exists()


def test_invalid_orchestrator_id_fails_closed(tmp_path):
    with pytest.raises(ValueError):
        CheckpointStore(project_root=tmp_path, orchestrator_id="../evil")
