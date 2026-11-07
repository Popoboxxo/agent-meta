"""Regression tests for Wave 8 persistence robustness (#573, #576, #580).

Covers:
- #573 `io.write_atomic()` — crash/interrupt mid-write must never corrupt
  the target file (temp file + os.replace()).
- #576 `checkpoint.py` — a corrupt session JSON file must not crash
  `load_session` / `get_last_checkpoint` / `cleanup_old_sessions` /
  `save_checkpoint`.
- #580 `cache.py` — `read()` must be side-effect-free (no write), and
  concurrent reads must never corrupt the cache file.
"""

import concurrent.futures
import json
import os
import sys
import threading
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib import cache  # noqa: E402
from lib.checkpoint import Checkpoint, CheckpointStore  # noqa: E402
from lib.io import write_atomic  # noqa: E402


# ---------------------------------------------------------------------------
# #573 -- write_atomic
# ---------------------------------------------------------------------------

def test_write_atomic_roundtrip(tmp_path):
    path = tmp_path / "sub" / "state.json"
    write_atomic(path, '{"a": 1}')
    assert path.read_text(encoding="utf-8") == '{"a": 1}'


def test_write_atomic_leaves_original_untouched_on_crash(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    write_atomic(path, "original-content")

    def _boom(*_a, **_kw):
        raise OSError("simulated crash mid-write")

    monkeypatch.setattr(os, "fsync", _boom)
    with pytest.raises(OSError):
        write_atomic(path, "corrupted-content-should-never-land")

    assert path.read_text(encoding="utf-8") == "original-content"
    # no leftover temp file
    leftovers = [p for p in tmp_path.iterdir() if p.name != "state.json"]
    assert leftovers == []


def test_write_atomic_leaves_original_untouched_on_replace_failure(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    write_atomic(path, "original-content")

    def _boom(*_a, **_kw):
        raise OSError("simulated interrupt before rename")

    monkeypatch.setattr(os, "replace", _boom)
    with pytest.raises(OSError):
        write_atomic(path, "corrupted-content")

    assert path.read_text(encoding="utf-8") == "original-content"
    leftovers = [p for p in tmp_path.iterdir() if p.name != "state.json"]
    assert leftovers == []


def test_write_atomic_creates_parent_dirs(tmp_path):
    path = tmp_path / "a" / "b" / "c.json"
    write_atomic(path, "x")
    assert path.read_text(encoding="utf-8") == "x"


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits only")
def test_write_atomic_preserves_existing_mode(tmp_path):
    """#1155 F6: rewriting an 0755 hook must not drop it to mkstemp's 0600."""
    path = tmp_path / "hook.sh"
    path.write_text("old\n", encoding="utf-8")
    os.chmod(path, 0o755)
    write_atomic(path, "new\n")
    assert path.stat().st_mode & 0o777 == 0o755


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits only")
def test_write_atomic_new_file_follows_umask(tmp_path):
    old = os.umask(0o027)
    try:
        write_atomic(tmp_path / "new.txt", "x")
    finally:
        os.umask(old)
    assert (tmp_path / "new.txt").stat().st_mode & 0o777 == 0o640


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits only")
def test_write_atomic_private_is_owner_only(tmp_path):
    path = tmp_path / "secret.env"
    path.write_text("old\n", encoding="utf-8")
    os.chmod(path, 0o644)
    write_atomic(path, "TOKEN=x\n", private=True)
    assert path.stat().st_mode & 0o777 == 0o600
    write_atomic(tmp_path / "fresh.env", "TOKEN=x\n", private=True)
    assert (tmp_path / "fresh.env").stat().st_mode & 0o777 == 0o600


# ---------------------------------------------------------------------------
# #576 -- checkpoint.py tolerates corrupt session files
# ---------------------------------------------------------------------------

def _make_store(tmp_path) -> CheckpointStore:
    return CheckpointStore(project_root=tmp_path)


def test_load_session_returns_none_on_corrupt_file(tmp_path):
    store = _make_store(tmp_path)
    store.checkpoint_dir.mkdir(parents=True)
    (store.checkpoint_dir / "broken.json").write_text("{not json", encoding="utf-8")
    assert store.load_session("broken") is None


def test_get_last_checkpoint_returns_none_on_corrupt_file(tmp_path):
    store = _make_store(tmp_path)
    store.checkpoint_dir.mkdir(parents=True)
    (store.checkpoint_dir / "broken.json").write_text("{not json", encoding="utf-8")
    assert store.get_last_checkpoint("broken") is None


def test_save_checkpoint_recovers_from_corrupt_existing_file(tmp_path):
    store = _make_store(tmp_path)
    store.checkpoint_dir.mkdir(parents=True)
    (store.checkpoint_dir / "sess.json").write_text("{not json", encoding="utf-8")

    store.save_checkpoint("sess", Checkpoint("t1", "developer", "do thing", "completed"))

    session = store.load_session("sess")
    assert session is not None
    assert len(session["checkpoints"]) == 1


def test_cleanup_old_sessions_skips_corrupt_file_without_crashing(tmp_path):
    store = _make_store(tmp_path)
    store.save_checkpoint("good", Checkpoint("t1", "developer", "do thing", "completed"))
    store.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    (store.checkpoint_dir / "broken.json").write_text("{not json", encoding="utf-8")

    deleted = store.cleanup_old_sessions(max_age_seconds=-1)

    # "good" is older than -1 seconds -> deleted; "broken" cannot be parsed
    # for its age -> skipped (not deleted, not crashed).
    assert deleted == 1
    assert (store.checkpoint_dir / "broken.json").exists()


# ---------------------------------------------------------------------------
# #580 -- cache.read() is side-effect-free / no races under concurrency
# ---------------------------------------------------------------------------

def test_read_does_not_modify_cache_file(tmp_path):
    cache_path = str(tmp_path / "cache.json")
    cache.write(cache_path, "k1", {"r": 1})
    before = Path(cache_path).read_text(encoding="utf-8")

    for _ in range(5):
        cache.read(cache_path, "k1")

    after = Path(cache_path).read_text(encoding="utf-8")
    assert before == after


def test_read_does_not_change_mtime(tmp_path):
    cache_path = str(tmp_path / "cache.json")
    cache.write(cache_path, "k1", {"r": 1})
    mtime_before = Path(cache_path).stat().st_mtime_ns

    cache.read(cache_path, "k1")

    assert Path(cache_path).stat().st_mtime_ns == mtime_before


def test_concurrent_reads_never_corrupt_cache_file(tmp_path):
    cache_path = str(tmp_path / "cache.json")
    for i in range(20):
        cache.write(cache_path, f"k{i}", {"r": i})

    errors = []

    def _hammer_read():
        try:
            for i in range(50):
                cache.read(cache_path, f"k{i % 20}")
        except Exception as e:  # noqa: BLE001 -- test must capture any failure
            errors.append(e)

    threads = [threading.Thread(target=_hammer_read) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    # File must still be valid, parseable JSON with all entries intact.
    data = json.loads(Path(cache_path).read_text(encoding="utf-8"))
    assert len(data["entries"]) == 20


def test_record_hit_is_batched_into_next_write(tmp_path):
    cache_path = str(tmp_path / "cache.json")
    cache.write(cache_path, "k1", {"r": 1})

    def _hammer_hits():
        for _ in range(25):
            cache.record_hit(cache_path)

    threads = [threading.Thread(target=_hammer_hits) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Stats query (read-only) sees the pending hits without draining them.
    stats_before = cache.cache_stats(cache_path)
    assert stats_before["hits"] == 100

    # A write() call drains the journal into the persisted counter.
    cache.write(cache_path, "k2", {"r": 2})
    stats_after = cache.cache_stats(cache_path)
    assert stats_after["hits"] == 100
    assert not Path(str(cache_path) + ".hits").exists()


def test_read_returns_none_on_corrupt_cache_file(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text("{not json", encoding="utf-8")
    assert cache.read(str(path), "k1") is None


def test_write_self_heals_corrupt_cache_file(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text("{not json", encoding="utf-8")
    cache.write(str(path), "k1", {"r": 1})
    assert cache.read(str(path), "k1") == {"r": 1}


def test_concurrent_writes_do_not_crash(tmp_path):
    # write() still does a read-modify-write (unlike read()) -- concurrent
    # writers may overwrite each other's entries (best-effort, no locking
    # requested by #580), but the file must always stay valid JSON.
    cache_path = str(tmp_path / "cache.json")

    def _hammer_write(n):
        for i in range(10):
            cache.write(cache_path, f"t{n}-{i}", {"r": i})

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(_hammer_write, range(8)))

    data = json.loads(Path(cache_path).read_text(encoding="utf-8"))
    assert isinstance(data["entries"], dict)


# ---------------------------------------------------------------------------
# #1155 F7 -- project.yaml writers go through write_atomic
# ---------------------------------------------------------------------------

def _crash_fsync(monkeypatch):
    def _boom(*_a, **_kw):
        raise OSError("simulated crash mid-write")
    monkeypatch.setattr(os, "fsync", _boom)


@pytest.mark.parametrize("full_dump", [False, True])
def test_project_yaml_comment_writer_is_atomic(tmp_path, monkeypatch, full_dump):
    from lib import config as config_mod
    from lib import yaml_patch

    path = tmp_path / "project.yaml"
    original = "# keep\r\nproject:\r\n  name: t\r\n"
    path.write_bytes(original.encode("utf-8"))
    if full_dump:
        monkeypatch.setattr(yaml_patch, "patch_top_level", lambda *a, **k: None)
    _crash_fsync(monkeypatch)
    with pytest.raises(OSError):
        config_mod._write_yaml_with_comments(
            path, {"project": {"name": "t"}, "roles": ["x"]}, [("roles", "d")])
    assert path.read_bytes().decode("utf-8") == original
    assert [p.name for p in tmp_path.iterdir()] == ["project.yaml"]


def test_version_bookkeeping_write_is_atomic(tmp_path, monkeypatch):
    from lib.log import SyncLog
    from lib.sync_pipeline import sync_version_bookkeeping

    path = tmp_path / "project.yaml"
    path.write_text('agent-meta-version: "0.0.1"\n', encoding="utf-8")
    _crash_fsync(monkeypatch)
    with pytest.raises(OSError):
        sync_version_bookkeeping(_REPO_ROOT, tmp_path, path,
                                 {"agent-meta-version": "0.0.1"}, SyncLog(), False)
    assert path.read_text(encoding="utf-8") == 'agent-meta-version: "0.0.1"\n'


# --- #1155 A3: project.yaml writers keep the (token-bearing) file 0600 -------


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")
def test_audit_apply_writes_project_yaml_owner_only(tmp_path):
    from lib.config_audit_apply import apply_audit
    from lib.config_audit_types import AuditReport

    cfg = tmp_path / "project.yaml"
    cfg.write_text("roles:\n  - old-role\n", encoding="utf-8")
    os.chmod(cfg, 0o644)
    report = AuditReport()
    report.add("deprecated_roles", "warning", "old-role", "msg")
    assert apply_audit(report, cfg) == 1
    assert (os.stat(cfg).st_mode & 0o777) == 0o600


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")
def test_deactivation_writes_project_yaml_owner_only(tmp_path):
    from lib.deactivation import update_deactivation_config
    from lib.log import SyncLog

    cfg = tmp_path / "project.yaml"
    cfg.write_text("project: {}\n", encoding="utf-8")
    os.chmod(cfg, 0o644)
    update_deactivation_config(cfg, {}, ["Gemini"], {}, SyncLog())
    assert (os.stat(cfg).st_mode & 0o777) == 0o600
