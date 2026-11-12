"""system_temp_root / resolve_sink_absolute (IC-1, IC-2; #1189).

Covers AC-1189-01/02/10/11/30: the framework pin (``TMPDIR=<sink>``) is never
evidence about the system temp root. Pin cases are modelled env-based
(``TMPDIR``/``TEMP``/``TMP`` + ``tempfile.tempdir = None``); a
``gettempdir`` patch is only used for cases without env relation.

Run: python -m pytest tests/test_tmp_sink_system_temp_root.py -q
"""

from __future__ import annotations

import os
import sys
import tempfile
import threading
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import repo_containment as rc  # noqa: E402


def _pin(monkeypatch, sink: Path, keys=("TMPDIR", "TEMP", "TMP")) -> None:
    for key in ("TMPDIR", "TEMP", "TMP"):
        monkeypatch.delenv(key, raising=False)
    for key in keys:
        monkeypatch.setenv(key, str(sink))
    monkeypatch.setattr(tempfile, "tempdir", None)


@pytest.fixture
def layout(tmp_path):
    root = tmp_path / "proj"
    sink = root / ".tmp"
    sink.mkdir(parents=True)
    return root, sink


def _outside(root: Path, value: str) -> bool:
    real = os.path.realpath(value)
    return os.path.commonpath([os.path.realpath(root), real]) != os.path.realpath(root)


def test_no_sink_returns_gettempdir(layout, monkeypatch):
    root, _ = layout
    monkeypatch.setattr(tempfile, "gettempdir", lambda: "/some/where")
    assert rc.system_temp_root(root, None) == "/some/where"


def test_pin_returns_existing_dir_outside_root(layout, monkeypatch):
    root, sink = layout
    _pin(monkeypatch, sink)
    result = rc.system_temp_root(root, sink)
    assert os.path.isdir(result)
    assert _outside(root, result)
    assert os.path.realpath(result) != os.path.realpath(sink)


@pytest.mark.skipif(sys.platform == "win32", reason="TMPDIR-only pin is POSIX")
def test_tmpdir_only_pin_matches_all_keys_pin(layout, monkeypatch):
    root, sink = layout
    _pin(monkeypatch, sink)
    all_keys = rc.system_temp_root(root, sink)
    _pin(monkeypatch, sink, keys=("TMPDIR",))
    assert rc.system_temp_root(root, sink) == all_keys


def test_observed_root_not_sink_returns_unchanged(layout, monkeypatch, tmp_path):
    root, sink = layout
    other = tmp_path / "other"
    other.mkdir()
    _pin(monkeypatch, other)
    assert rc.system_temp_root(root, sink) == str(other)


def test_environ_and_tempdir_cache_unchanged(layout, monkeypatch):
    root, sink = layout
    _pin(monkeypatch, sink)
    tempfile.gettempdir()  # prime the cache before the snapshot
    env_before = dict(os.environ)
    cache_before = tempfile.tempdir
    rc.system_temp_root(root, sink)
    assert dict(os.environ) == env_before
    assert tempfile.tempdir == cache_before


def test_concurrent_calls_agree(layout, monkeypatch):
    root, sink = layout
    _pin(monkeypatch, sink)
    results = []

    def work():
        results.append(rc.system_temp_root(root, sink))

    threads = [threading.Thread(target=work) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(results) == 8 and len(set(results)) == 1


def test_sink_candidate_is_skipped(layout, monkeypatch, tmp_path):
    root, sink = layout
    outside = tmp_path / "outside"
    outside.mkdir()
    _pin(monkeypatch, sink)
    monkeypatch.setattr(
        tempfile, "_candidate_tempdir_list",
        lambda: [str(sink), str(root / "sub"), str(outside)], raising=False,
    )
    assert rc.system_temp_root(root, sink) == str(outside)


def test_no_candidate_outside_root_raises(layout, monkeypatch):
    root, sink = layout
    (root / "sub").mkdir()
    _pin(monkeypatch, sink)
    monkeypatch.setattr(
        tempfile, "_candidate_tempdir_list",
        lambda: [str(sink), str(root / "sub")], raising=False,
    )
    with pytest.raises(rc.TmpSinkError) as exc:
        rc.system_temp_root(root, sink)
    assert exc.value.code == "tmp-sink.system-temp-exception"


def test_normcase_comparison_windows(layout, monkeypatch, tmp_path):
    root, sink = layout
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(sink).upper())
    monkeypatch.setattr(
        tempfile, "_candidate_tempdir_list", lambda: [str(outside)], raising=False
    )
    monkeypatch.setattr(os.path, "normcase", lambda p: p.lower())
    monkeypatch.setattr(os.path, "realpath", lambda p, **kw: p)
    assert rc.system_temp_root(root, sink) == str(outside)


def _sink_cfg(path="scratch/out", enabled=True) -> dict:
    return {"repo_containment": {"tmp-sink": {"enabled": enabled, "path": path}}}


def test_resolve_sink_absolute_returns_realpath(tmp_path):
    got = rc.resolve_sink_absolute(tmp_path, _sink_cfg())
    assert got == Path(os.path.realpath(tmp_path / "scratch" / "out"))


def test_resolve_sink_absolute_none_when_disabled(tmp_path):
    assert rc.resolve_sink_absolute(tmp_path, _sink_cfg(enabled=False)) is None


def test_resolve_sink_absolute_none_on_invalid_path_finding(tmp_path):
    cfg = _sink_cfg(path="../escape")
    effective = rc.resolve_effective_repo_containment(cfg)
    assert any(f.code == "repo-containment.tmp-sink-path" for f in effective.findings)
    assert rc.resolve_sink_absolute(tmp_path, cfg) is None
