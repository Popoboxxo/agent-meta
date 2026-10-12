"""tmp-sink path hardening (IC-15 Nr. 27 a-e, i; AC-93).

Windows behaviour is simulated through ``ntpath`` / ``pathmod`` -- no Windows
host is required.
"""
from __future__ import annotations

import json
import ntpath
import os
import posixpath
import stat
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib import repo_containment as rc  # noqa: E402
from lib.repo_containment import (  # noqa: E402
    ResolvedRepoContainment,
    canonical_tmp_sink_path,
    ensure_tmp_sink,
    tmp_sink_location_error,
    tmp_sink_path_error,
)

CORPUS = json.loads(
    (Path(__file__).parent / "fixtures" / "tmp-sink-path-corpus.json").read_text(encoding="utf-8")
)["cases"]
PATHMODS = [("posix", posixpath), ("nt", ntpath)]


@pytest.mark.parametrize("host,pathmod", PATHMODS)
@pytest.mark.parametrize("case", CORPUS, ids=[repr(c["path"]) for c in CORPUS])
def test_corpus_lexical_decision(case, host, pathmod):
    error = tmp_sink_path_error(case["path"], pathmod=pathmod)
    if case["reject"]:
        assert error, f"{case['path']!r} must be rejected on {host}"
    else:
        assert error is None, error
        assert canonical_tmp_sink_path(case["path"]) == case["canonical"]


def test_non_string_rejected():
    assert tmp_sink_path_error(5) is not None


def test_drive_letter_message_kept():
    assert "drive-letter" in tmp_sink_path_error("C:\\Users\\x")


def _sink(path: str, **kw) -> ResolvedRepoContainment:
    return ResolvedRepoContainment(enabled=True, source="default", tmp_sink_path=path, **kw)


# --- resolution with ntpath simulation ------------------------------------

def test_ntpath_case_variant_of_root_is_inside(monkeypatch):
    monkeypatch.setattr(ntpath, "realpath", lambda p: ntpath.normpath(p), raising=False)
    assert tmp_sink_path_error(".tmp", "C:\\Proj\\Repo", pathmod=ntpath) is None
    # case variant resolved by realpath is still inside (normcase compare)
    monkeypatch.setattr(
        ntpath, "realpath",
        lambda p: ntpath.normpath(p).replace("Repo", "REPO") if p.endswith(".tmp") else ntpath.normpath(p),
        raising=False,
    )
    assert tmp_sink_path_error(".tmp", "C:\\Proj\\Repo", pathmod=ntpath) is None


def test_ntpath_other_drive_is_outside(monkeypatch):
    def fake_real(p):
        n = ntpath.normpath(p)
        return "D:\\elsewhere" if n.endswith(".tmp") else n
    monkeypatch.setattr(ntpath, "realpath", fake_real, raising=False)
    err = tmp_sink_path_error(".tmp", "C:\\Proj", pathmod=ntpath)
    assert err and "escape" in err


# --- real symlinks (POSIX) -------------------------------------------------

@pytest.mark.skipif(os.name == "nt", reason="needs POSIX symlinks")
def test_symlink_sink_outside_rejected(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    out = tmp_path / "out"
    out.mkdir()
    (root / ".tmp").symlink_to(out)
    assert tmp_sink_path_error(".tmp", root) is not None


@pytest.mark.skipif(os.name == "nt", reason="needs POSIX symlinks")
def test_symlink_sink_inside_rejected(tmp_path):
    root = tmp_path / "root"
    (root / "real").mkdir(parents=True)
    (root / ".tmp").symlink_to(root / "real")
    assert tmp_sink_path_error(".tmp", root) is not None


@pytest.mark.skipif(os.name == "nt", reason="needs POSIX symlinks")
def test_intermediate_symlink_outside_rejected(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    out = tmp_path / "out"
    out.mkdir()
    (root / "scratch").symlink_to(out)
    assert tmp_sink_path_error("scratch/sub", root) is not None


@pytest.mark.skipif(os.name == "nt", reason="needs POSIX symlinks")
def test_resolve_sink_dir_rejects_intermediate_symlink(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    out = tmp_path / "out"
    out.mkdir()
    (root / "scratch").symlink_to(out)
    assert ensure_tmp_sink(root, _sink("scratch/sub")) is None
    assert not (out / "sub").exists()


def test_plain_sink_accepted_and_realpath_returned(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    sink = ensure_tmp_sink(root, _sink("scratch\\out"))
    assert sink == Path(os.path.realpath(root)) / "scratch" / "out"
    assert sink.is_dir()


# --- junction / reparse-point ----------------------------------------------

def test_junction_detected_via_isjunction(tmp_path, monkeypatch):
    root = tmp_path / "root"
    (root / "scratch").mkdir(parents=True)
    monkeypatch.setattr(
        os.path, "isjunction", lambda p: os.path.basename(p) == "scratch", raising=False
    )
    out = tmp_path / "out"
    out.mkdir()
    real = os.path.realpath
    monkeypatch.setattr(
        os.path, "realpath",
        lambda p, *a, **k: str(out / "sub") if str(p).endswith("scratch/sub") else real(p, *a, **k),
    )
    assert tmp_sink_path_error("scratch/sub", root) is not None


def test_junction_fallback_reparse_point(tmp_path, monkeypatch):
    root = tmp_path / "root"
    (root / "scratch").mkdir(parents=True)
    monkeypatch.delattr(os.path, "isjunction", raising=False)
    real_stat = os.stat

    class _Fake:
        st_file_attributes = stat.FILE_ATTRIBUTE_REPARSE_POINT if hasattr(
            stat, "FILE_ATTRIBUTE_REPARSE_POINT") else 0x400

    def fake_stat(p, *a, **k):
        if str(p).endswith("scratch"):
            return _Fake()
        return real_stat(p, *a, **k)

    monkeypatch.setattr(os, "stat", fake_stat)
    # a reparse-point as the LAST component is always refused
    assert tmp_sink_path_error("scratch", root, pathmod=posixpath) is not None


def test_no_isjunction_no_st_file_attributes_is_safe(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    monkeypatch.delattr(os.path, "isjunction", raising=False)
    assert tmp_sink_path_error("scratch", root) is None


# --- ensure_tmp_sink TOCTOU --------------------------------------------------

@pytest.mark.skipif(os.name == "nt", reason="needs POSIX symlinks")
def test_ensure_tmp_sink_toctou_creates_nothing_outside(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    out = tmp_path / "out"
    out.mkdir()

    def hook():
        (root / "scratch").symlink_to(out)

    monkeypatch.setattr(rc, "_TOCTOU_TEST_HOOK", hook)
    assert ensure_tmp_sink(root, _sink("scratch/sub")) is None
    assert list(out.iterdir()) == []


# --- tmp_sink_location_error --------------------------------------------------

def test_location_error_inside_ok(tmp_path):
    assert tmp_sink_location_error(".tmp", tmp_path) is None


def test_location_error_outside_root(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    assert tmp_sink_location_error("../x", root) is not None
    assert tmp_sink_location_error(str(tmp_path / "other"), root) is not None


def test_location_error_under_system_temp(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    other = tmp_path / "systmp"
    other.mkdir()
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(other))
    err = tmp_sink_location_error(str(other / "sink"), root)
    assert err and "temp" in err.lower()
