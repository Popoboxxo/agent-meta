"""Tool output/work dirs resolved via the tmp-sink (IC-34, AC-75/AC-94 part).

Run: python -m pytest tests/test_tmp_sink_output_dirs.py -q
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import repo_containment as rc  # noqa: E402
from lib.config import build_variables  # noqa: E402
from lib.tmp_paths import (  # noqa: E402
    SystemTempException,
    TmpPaths,
    resolve_pytest_basetemp,
    resolve_tmp_paths,
    tmp_env,
    tmp_sink_env_pin_block,
)


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


# ---------------------------------------------------------------------------
# Central tmp-paths resolver (Task 1: AC-12, AC-15 edge, AC-16, AC-23, AC-24,
# AC-35, AC-36)
# ---------------------------------------------------------------------------

def _exception_cfg(
    *,
    enabled: bool = True,
    pytest_basetemp: bool = True,
    reason: str | None = "unit-test reason",
    toolchain_caches: bool | None = None,
    sink_enabled: bool = True,
    path: str = ".tmp",
) -> dict:
    """Config with an explicit ``system-temp-exception`` block."""
    exception: dict = {"enabled": enabled, "pytest-basetemp": pytest_basetemp}
    if reason is not None:
        exception["reason"] = reason
    if toolchain_caches is not None:
        exception["toolchain-caches"] = toolchain_caches
    return {
        "repo_containment": {
            "tmp-sink": {
                "enabled": sink_enabled,
                "path": path,
                "system-temp-exception": exception,
            }
        }
    }


def _system_temp_outside_project(tmp_path: Path) -> Path:
    """A temp root that is provably not inside ``tmp_path``."""
    return tmp_path.parent / "system-temp-root"


def test_system_temp_exception_defaults(tmp_path):
    """Q1: projects without the key keep the enabled pytest exception."""
    paths = resolve_tmp_paths(tmp_path, {})
    assert paths.system_temp_exception == SystemTempException(
        enabled=True,
        reason=paths.system_temp_exception.reason,
        pytest_basetemp=True,
        toolchain_cache=False,
    )
    assert paths.system_temp_exception.reason.strip()


def test_resolver_does_not_raise_when_sink_disabled(tmp_path):
    """AC-23: a disabled sink is a valid state, not an error."""
    paths = resolve_tmp_paths(tmp_path, _cfg(enabled=False))

    assert paths.enabled is False
    assert paths.relative == "scratch/out"
    assert paths.absolute is None
    assert paths.env == {}
    assert paths.pytest_basetemp


def test_resolver_still_validates_path_when_sink_disabled(tmp_path):
    """IC-03: a broken path stays a config error even when disabled."""
    with pytest.raises(rc.TmpSinkError) as exc:
        resolve_tmp_paths(tmp_path, _cfg(path="../escape", enabled=False))
    assert exc.value.code == "tmp-sink.invalid-path"


def test_writers_still_raise_when_sink_disabled(tmp_path):
    """AC-24: write/consumer APIs keep raising ``tmp-sink.disabled``."""
    cfg = _cfg(enabled=False)
    paths = resolve_tmp_paths(tmp_path, cfg)  # must not raise

    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_output_dir(tmp_path, cfg, "doctor")
    assert exc.value.code == "tmp-sink.disabled"

    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_work_dir(tmp_path, cfg, "doctor", "r1")
    assert exc.value.code == "tmp-sink.disabled"

    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_out_path(tmp_path, cfg, "scratch/out/x.json")
    assert exc.value.code == "tmp-sink.disabled"

    with pytest.raises(rc.TmpSinkError) as exc:
        tmp_env(paths)
    assert exc.value.code == "tmp-sink.disabled"

    with pytest.raises(rc.TmpSinkError) as exc:
        tmp_sink_env_pin_block(paths)
    assert exc.value.code == "tmp-sink.disabled"

    with pytest.raises(rc.TmpSinkError) as exc:
        rc.resolve_output_dir(tmp_path, cfg, "doctor", tool="doctor")
    assert exc.value.code == "doctor.tmp-sink.disabled"


def test_tmp_env_pins_absolute_sink(tmp_path):
    """AC-12: all three keys are absolute, existing and inside the root."""
    paths = resolve_tmp_paths(tmp_path, _cfg())
    env = tmp_env(paths)
    root_real = os.path.realpath(tmp_path)

    for key in ("TMPDIR", "TEMP", "TMP"):
        value = env[key]
        assert os.path.isabs(value)
        assert Path(value).is_dir()
        assert os.path.commonpath([root_real, os.path.realpath(value)]) == root_real
        assert value == str(paths.absolute)

    assert set(("TMPDIR", "TEMP", "TMP")) <= set(env)
    assert all(os.path.isabs(env[key]) for key in ("TMPDIR", "TEMP", "TMP"))
    # TmpPaths.env carries the same absolute pin (IC-06).
    assert [paths.env[key] for key in ("TMPDIR", "TEMP", "TMP")] == [
        str(paths.absolute)
    ] * 3


def test_tmp_env_preserves_base_env(tmp_path):
    paths = resolve_tmp_paths(tmp_path, _cfg())
    base = {"PATH": "/usr/bin", "TMPDIR": "/elsewhere"}
    env = tmp_env(paths, base)
    assert env["PATH"] == "/usr/bin"
    assert env["TMPDIR"] == str(paths.absolute)
    assert base["TMPDIR"] == "/elsewhere"  # base is not mutated


def test_relative_and_absolute_sink_variables(tmp_path):
    """AC-16 (resolver half): ``relative`` stays relative, ``absolute`` absolute."""
    paths = resolve_tmp_paths(tmp_path, {})
    assert paths.relative == ".tmp"
    assert not os.path.isabs(paths.relative)
    assert paths.absolute == Path(os.path.realpath(tmp_path / ".tmp"))
    assert os.path.isabs(str(paths.absolute))
    assert os.path.realpath(paths.absolute) == str(paths.absolute)
    assert paths.enabled is True


def test_env_pin_block_is_absolute(tmp_path):
    """AC-35: the block pins all three vars to the absolute sink."""
    paths = resolve_tmp_paths(tmp_path, _cfg())
    block = tmp_sink_env_pin_block(paths)

    assert f"TMPDIR={paths.relative}" not in block
    assert f"TMPDIR='{paths.relative}'" not in block

    probe = block + "\nprintf '%s\\n%s\\n%s\\n' \"$TMPDIR\" \"$TEMP\" \"$TMP\"\n"
    result = subprocess.run(
        ["sh", "-c", probe],
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 0, result.stderr
    values = result.stdout.splitlines()
    assert values == [str(paths.absolute)] * 3
    assert all(os.path.isabs(value) for value in values)
    assert all(Path(value).is_dir() for value in values)


def test_env_pin_block_refuses_missing_directory(tmp_path):
    """AC-36: a dead sink path is not exported; the repair hint is printed."""
    paths = resolve_tmp_paths(tmp_path, _cfg())
    block = tmp_sink_env_pin_block(paths)
    shutil.rmtree(paths.absolute)
    assert not paths.absolute.exists()

    probe = block + "\nprintf '%s\\n%s\\n%s\\n' \"$TMPDIR\" \"$TEMP\" \"$TMP\"\n"
    result = subprocess.run(
        ["sh", "-c", probe],
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin",
            "TMPDIR": "/keep",
            "TEMP": "/keep",
            "TMP": "/keep",
        },
    )
    assert result.returncode == 0
    assert result.stdout.splitlines() == ["/keep", "/keep", "/keep"]
    assert "python scripts/sync.py" in result.stderr


def test_pytest_basetemp_uses_system_temp_when_exception_active(tmp_path, monkeypatch):
    """IC-04: active exception ⇒ platform temp root, no ``/tmp`` literal."""
    system_temp = _system_temp_outside_project(tmp_path)
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(system_temp))

    paths = resolve_tmp_paths(tmp_path, _exception_cfg())

    assert os.path.isabs(paths.pytest_basetemp)
    assert paths.pytest_basetemp.startswith(str(system_temp) + os.sep)
    assert paths.pytest_basetemp.endswith(os.sep + "pytest-agent-meta")
    assert '"' not in paths.pytest_basetemp
    assert str(tmp_path) not in paths.pytest_basetemp


def test_pytest_basetemp_falls_back_to_sink_without_exception(tmp_path):
    """IC-04: without the exception the basetemp lives under the sink."""
    paths = resolve_tmp_paths(
        tmp_path, _exception_cfg(enabled=False, pytest_basetemp=False, reason=None)
    )
    assert paths.pytest_basetemp == str(paths.absolute / "pytest")


def test_pytest_basetemp_rejects_temp_root_inside_project(tmp_path, monkeypatch):
    """AC-15 edge: a temp root inside the project makes the exception useless."""
    inside = tmp_path / "system-temp"
    inside.mkdir()
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(inside))

    with pytest.raises(rc.TmpSinkError) as exc:
        resolve_tmp_paths(tmp_path, _exception_cfg())
    assert exc.value.code == "tmp-sink.system-temp-exception"


def test_pytest_basetemp_rejects_quote_in_value(tmp_path, monkeypatch):
    """IC-04: a ``"`` would break ``--basetemp="<path>"``."""
    system_temp = _system_temp_outside_project(tmp_path)
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(system_temp))
    monkeypatch.setenv("USER", 'we"ird')
    monkeypatch.setenv("USERNAME", 'we"ird')
    paths = TmpPaths(
        relative=".tmp",
        absolute=tmp_path / ".tmp",
        enabled=True,
        system_temp_exception=SystemTempException(),
        pytest_basetemp="",
        env={},
    )
    with pytest.raises(rc.TmpSinkError) as exc:
        resolve_pytest_basetemp(tmp_path, paths)
    assert exc.value.code == "tmp-sink.system-temp-exception"


def test_toolchain_cache_requires_enabled_exception(tmp_path):
    """AC-38 (resolver half): an opt-in without the exception is a config error."""
    with pytest.raises(rc.TmpSinkError) as exc:
        resolve_tmp_paths(
            tmp_path,
            _exception_cfg(enabled=False, pytest_basetemp=False, toolchain_caches=True),
        )
    assert exc.value.code == "tmp-sink.system-temp-exception"


def test_disabled_sink_without_pytest_exception_has_no_basetemp(tmp_path):
    """IC-04: a disabled sink must never silently become the basetemp location."""
    with pytest.raises(rc.TmpSinkError) as exc:
        resolve_tmp_paths(
            tmp_path,
            _exception_cfg(
                enabled=False,
                pytest_basetemp=False,
                reason=None,
                sink_enabled=False,
            ),
        )
    assert exc.value.code == "tmp-sink.system-temp-exception"
