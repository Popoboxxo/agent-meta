"""Raw-output storage API tests for CheckpointStore (issue #267).

Summarization-as-a-Contract: the worker's structured summary travels back
as the return value, while the COMPLETE raw output is archived under
``.meta-viz/checkpoints/<session-id>/``. These tests cover the archiving
API (save / load / list), filename sanitization and append-only behavior.

Boundary note (issue #265): parsing worker results after the BARRIER
marker is harness-side (``scripts/lib/orchestration.py``) — deliberately
NOT covered here; checkpoint.py archives bytes only.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.checkpoint import CheckpointStore  # noqa: E402


def _store(tmp_path: Path) -> CheckpointStore:
    return CheckpointStore(project_root=tmp_path)


def test_save_raw_output_writes_under_session_directory(tmp_path):
    store = _store(tmp_path)
    path = store.save_raw_output("sess1", "task-1", "developer", "raw output")
    assert path.exists()
    assert path.parent == store.checkpoint_dir / "sess1"
    assert path.suffix == ".txt"


def test_save_and_load_roundtrip_exact_content(tmp_path):
    store = _store(tmp_path)
    raw = "line1\nüñïcödé & special chars ✓\n\nlast line\n"
    path = store.save_raw_output("sess1", "task-1", "developer", raw)
    filename = path.name
    assert store.load_raw_output("sess1", filename) == raw


def test_save_raw_output_sanitizes_path_traversal_and_separators(tmp_path):
    store = _store(tmp_path)
    path = store.save_raw_output(
        "sess1", "../../evil", "agent/with:weird chars", "content"
    )
    # File must stay inside the session directory — no escape, no new dirs.
    assert path.parent == store.checkpoint_dir / "sess1"
    assert path.exists()
    assert ".." not in path.name
    assert "/" not in path.name.replace(path.suffix, "", 1).replace(
        str(path.parent) + "/", ""
    )


def test_save_raw_output_is_append_only_no_silent_overwrite(tmp_path):
    store = _store(tmp_path)
    first = store.save_raw_output("sess1", "task-1", "developer", "first run")
    second = store.save_raw_output("sess1", "task-1", "developer", "second run")
    assert first != second
    assert first.exists() and second.exists()
    assert store.load_raw_output("sess1", first.name) == "first run"
    assert store.load_raw_output("sess1", second.name) == "second run"


def test_load_raw_output_missing_file_returns_none(tmp_path):
    store = _store(tmp_path)
    assert store.load_raw_output("nope", "missing.txt") is None
    store.save_raw_output("sess1", "t", "agent", "content")
    assert store.load_raw_output("sess1", "does-not-exist.txt") is None


def test_load_raw_output_unreadable_file_returns_none(tmp_path):
    store = _store(tmp_path)
    session_dir = store.checkpoint_dir / "sess1"
    session_dir.mkdir(parents=True)
    broken = session_dir / "broken.txt"
    # A directory where a file is expected makes read_text() raise OSError.
    broken.mkdir()
    assert store.load_raw_output("sess1", "broken.txt") is None


def test_list_raw_outputs_lists_session_files_sorted(tmp_path):
    store = _store(tmp_path)
    assert store.list_raw_outputs("empty") == []
    paths = [
        store.save_raw_output("sess1", "t1", "agent-a", "one"),
        store.save_raw_output("sess1", "t2", "agent-b", "two"),
    ]
    listed = store.list_raw_outputs("sess1")
    assert listed == sorted(paths)
    assert len(listed) == 2
    assert all(p.exists() for p in listed)


def test_raw_output_dir_does_not_break_session_json_views(tmp_path):
    store = _store(tmp_path)
    store.save_raw_output("sess1", "t1", "developer", "raw")
    # Session JSON layer is unaffected: no file, no entries.
    assert store.load_session("sess1") is None
    assert store.get_last_checkpoint("sess1") is None
    assert store.get_completed_steps("sess1") == []
    # list_sessions still reports only JSON session files.
    assert store.list_sessions() == []
