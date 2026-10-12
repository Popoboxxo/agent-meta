"""Tool output/work dirs resolved via the tmp-sink (IC-34, AC-75/AC-94 part).

Run: python -m pytest tests/test_tmp_sink_output_dirs.py -q
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import repo_containment as rc  # noqa: E402
from lib.config import build_variables  # noqa: E402


def _cfg(path: str = "scratch/out", enabled: bool = True) -> dict:
    return {"repo_containment": {"tmp-sink": {"enabled": enabled, "path": path}}}


def test_output_dir_uses_configured_sink(tmp_path):
    out = rc.resolve_output_dir(tmp_path, _cfg(), "doctor")
    assert out == Path(os.path.realpath(tmp_path / "scratch" / "out" / "doctor"))


def test_work_dir_is_run_id_based(tmp_path):
    work = rc.resolve_work_dir(tmp_path, _cfg(), "doctor", "r1")
    assert work == Path(os.path.realpath(tmp_path / "scratch/out/doctor/r1/work"))


def test_default_config_uses_dot_tmp(tmp_path):
    out = rc.resolve_output_dir(tmp_path, {}, "context-report")
    assert out == Path(os.path.realpath(tmp_path / ".tmp" / "context-report"))


def test_disabled_sink_raises_tmp_sink_disabled(tmp_path):
    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_output_dir(tmp_path, _cfg(enabled=False), "doctor")
    assert exc.value.code == "tmp-sink.disabled"
    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_work_dir(tmp_path, _cfg(enabled=False), "doctor", "r1")
    assert exc.value.code == "tmp-sink.disabled"
    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_output_dir(tmp_path, _cfg(enabled=False), "doctor", tool="doctor")
    assert exc.value.code == "doctor.tmp-sink.disabled"


@pytest.mark.parametrize("subdir", ["", "..", "a/../..", "/abs", "a\\..\\x", "C:x"])
def test_bad_subdir_or_run_id_rejected(tmp_path, subdir):
    with pytest.raises(rc.TmpSinkError):
        rc.resolve_output_dir(tmp_path, _cfg(), subdir)
    with pytest.raises(rc.TmpSinkError):
        rc.resolve_work_dir(tmp_path, _cfg(), "doctor", subdir)


def test_unsafe_sink_path_rejected(tmp_path):
    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_output_dir(tmp_path, _cfg("../escape"), "doctor")
    assert exc.value.code == "tmp-sink.invalid-path"


def test_out_inside_sink_accepted(tmp_path):
    target = tmp_path / "scratch" / "out" / "doctor" / "r.json"
    got = rc.resolve_out_path(tmp_path, _cfg(), str(target), tool="doctor")
    assert got == Path(os.path.realpath(target))
    rel = rc.resolve_out_path(tmp_path, _cfg(), "scratch/out/x.json", tool="doctor")
    assert rel == Path(os.path.realpath(tmp_path / "scratch/out/x.json"))


@pytest.mark.parametrize("out", ["elsewhere/x.json", "scratch/out/../x.json", "/etc/x"])
def test_out_outside_sink_rejected(tmp_path, out):
    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_out_path(tmp_path, _cfg(), out, tool="optimize-config")
    assert exc.value.code == "optimize-config.out-outside-tmp-sink"


def test_out_symlink_escape_detected_by_realpath(tmp_path):
    (tmp_path / "scratch" / "out").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "scratch" / "out" / "lnk").symlink_to(outside)
    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_out_path(tmp_path, _cfg(), "scratch/out/lnk/x.json", tool="doctor")
    assert exc.value.code == "doctor.out-outside-tmp-sink"


def test_out_with_disabled_sink(tmp_path):
    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_out_path(tmp_path, _cfg(enabled=False), "x.json", tool="doctor")
    assert exc.value.code == "doctor.tmp-sink.disabled"


def test_no_system_temp_used(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("system temp used")

    for name in ("mkdtemp", "gettempdir", "mkstemp", "TemporaryDirectory"):
        monkeypatch.setattr(tempfile, name, boom)
    rc.resolve_work_dir(tmp_path, _cfg(), "context-report", "r1")
    rc.resolve_out_path(tmp_path, _cfg(), "scratch/out/a.json", tool="doctor")


def test_tmp_sink_path_variable(tmp_path):
    variables, _ = build_variables({"repo_containment": {"tmp-sink": {"path": "scratch/out"}}},
                                   REPO_ROOT, tmp_path)
    assert variables["TMP_SINK_PATH"] == "scratch/out"
    variables, _ = build_variables({}, REPO_ROOT, tmp_path)
    assert variables["TMP_SINK_PATH"] == ".tmp"


def test_symlink_subdir_escape_rejected(tmp_path):
    (tmp_path / "scratch" / "out").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "scratch" / "out" / "doctor").symlink_to(outside)
    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_output_dir(tmp_path, _cfg(), "doctor")
    assert exc.value.code == "tmp-sink.invalid-segment"
    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_work_dir(tmp_path, _cfg(), "doctor", "r1")
    assert exc.value.code == "tmp-sink.invalid-segment"
    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_output_dir(tmp_path, _cfg(), "doctor/deeper", tool="doctor")
    assert exc.value.code == "doctor.tmp-sink.invalid-segment"


def test_symlink_inside_sink_still_allowed(tmp_path):
    (tmp_path / "scratch" / "out" / "real").mkdir(parents=True)
    (tmp_path / "scratch" / "out" / "alias").symlink_to(tmp_path / "scratch" / "out" / "real")
    got = rc.resolve_output_dir(tmp_path, _cfg(), "alias")
    assert got == Path(os.path.realpath(tmp_path / "scratch/out")) / "alias"


def test_symlinked_run_id_escape_rejected(tmp_path):
    base = tmp_path / "scratch" / "out" / "doctor"
    base.mkdir(parents=True)
    (tmp_path / "outside").mkdir()
    (base / "r1").symlink_to(tmp_path / "outside")
    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_work_dir(tmp_path, _cfg(), "doctor", "r1")
    assert exc.value.code == "tmp-sink.invalid-segment"


def test_out_equal_to_sink_rejected(tmp_path):
    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_out_path(tmp_path, _cfg(), "scratch/out", tool="doctor")
    assert exc.value.code == "doctor.out-outside-tmp-sink"


def test_invalid_path_and_segment_carry_tool_prefix(tmp_path):
    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_output_dir(tmp_path, _cfg("../escape"), "doctor", tool="doctor")
    assert exc.value.code == "doctor.tmp-sink.invalid-path"
    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_output_dir(tmp_path, _cfg(), "..", tool="doctor")
    assert exc.value.code == "doctor.tmp-sink.invalid-segment"
