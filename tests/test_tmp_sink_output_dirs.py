"""Tool output/work dirs resolved via the tmp-sink (IC-34, AC-75/AC-94 part).

Run: python -m pytest tests/test_tmp_sink_output_dirs.py -q
"""

from __future__ import annotations

import ast
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import context_report as cr  # noqa: E402
from lib import meta_optimizer as mo  # noqa: E402
from lib import repo_containment as rc  # noqa: E402
from lib.config import build_variables, load_config  # noqa: E402
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
    # Resolution/provisioning are separate since Task 2: tmp_env creates the
    # sink (AC-12), the resolver itself stays write-free for dry-run safety.
    tmp_env(paths)
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
    tmp_env(paths)  # provision (AC-12), then simulate the moved repo below
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


# ---------------------------------------------------------------------------
# Suite commands rendered literal-free (Task 3: AC-13, AC-34)
# ---------------------------------------------------------------------------

def _repo_variables() -> dict:
    """Render the variables of this repository's real project config."""
    config = load_config(REPO_ROOT / ".meta-config" / "project.yaml")
    variables, _warnings = build_variables(config, REPO_ROOT, REPO_ROOT)
    return variables


def _basetemp_args(rendered: str) -> list[str]:
    """Every ``--basetemp=...`` argv element of a rendered shell command."""
    return [arg for arg in shlex.split(rendered) if arg.startswith("--basetemp=")]


def test_test_commands_have_no_system_temp_literal():
    """AC-13: the repo's suite commands carry no system-temp literal.

    The resolved basetemp is the single sanctioned temp path, so it is masked
    before the literal check — on POSIX the platform temp root *is* ``/tmp``.
    """
    variables = _repo_variables()
    basetemp = variables["PYTEST_BASETEMP"]
    assert os.path.isabs(basetemp)

    for key in ("TEST_COMMANDS", "CODE_QUALITY_RULES"):
        rendered = variables[key]
        command_text = rendered.replace(basetemp, "<PYTEST_BASETEMP>")

        assert "/tmp" not in command_text, key
        assert "%TEMP%" not in command_text, key
        assert "C:\\Temp" not in command_text, key
        assert "$USER" not in command_text, key

        # Shell-quoted and exactly one argument (AC-13/AC-34).
        assert '--basetemp="' in rendered, key
        args = _basetemp_args(rendered)
        assert len(args) == 1, (key, args)
        assert args[0] == f"--basetemp={basetemp}", key


def test_basetemp_with_spaces_is_single_argument(tmp_path, monkeypatch):
    """AC-34: a system temp root containing a space stays one argument."""
    spaced_root = tmp_path.parent / "system temp root"
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(spaced_root))

    variables = _repo_variables()
    basetemp = variables["PYTEST_BASETEMP"]
    assert " " in basetemp
    assert basetemp.startswith(str(spaced_root))

    for key in ("TEST_COMMANDS", "CODE_QUALITY_RULES"):
        rendered = variables[key]
        assert '--basetemp="' in rendered, key
        args = _basetemp_args(rendered)
        assert len(args) == 1, (key, args)
        assert args[0] == f"--basetemp={basetemp}", key


# ---------------------------------------------------------------------------
# Framework subprocess env pin (Task 10: IC-18/IC-34, AC-11 groundwork)
# ---------------------------------------------------------------------------

def _capture_subprocess_env(monkeypatch, module) -> list[dict]:
    """Capture the ``env`` of every ``subprocess.run`` call in *module*."""
    captured: list[dict] = []

    def fake_run(argv, **kwargs):
        captured.append(dict(kwargs.get("env") or {}))
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    return captured


def _assert_pin_matches_tmp_paths(env: dict, paths: TmpPaths) -> None:
    """All three keys are absolute and identical to ``TmpPaths.env`` (AC-12)."""
    for key in ("TMPDIR", "TEMP", "TMP"):
        assert env[key] == paths.env[key]
        assert os.path.isabs(env[key])
        assert Path(env[key]).is_dir()


def test_context_report_passes_absolute_tmp_env(tmp_path, monkeypatch):
    """IC-34: the render subprocesses receive the absolute ``TmpPaths.env`` pin.

    Red before Task 10: ``render_into_work_dir`` built its env with
    ``work_dir_env(work_dir)`` and knew no ``paths`` argument.
    """
    project_root = tmp_path / "project"
    config_path = project_root / ".meta-config" / "project.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("variables:\n  PROJECT_NAME: demo\n", encoding="utf-8")
    paths = resolve_tmp_paths(project_root, {})
    work_dir = project_root / ".tmp" / "context-report" / "run-1" / "work"

    captured = _capture_subprocess_env(monkeypatch, cr)
    cr.render_into_work_dir(REPO_ROOT, config_path, work_dir, paths=paths)

    assert captured, "no subprocess was started"
    for env in captured:
        _assert_pin_matches_tmp_paths(env, paths)
        assert env["TMPDIR"] != str(work_dir)


def test_meta_optimizer_render_pins_sink_env(tmp_path, monkeypatch):
    """IC-34: the optimizer render helper pins the absolute sink env.

    Red before Task 10: ``_render_into`` called ``work_dir_env(work_dir)``.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    paths = resolve_tmp_paths(project_root, {})
    work_dir = paths.absolute / "meta-optimizer" / "run-1" / "work"

    captured = _capture_subprocess_env(monkeypatch, mo)
    mo._render_into(REPO_ROOT, "variables:\n  A: b\n", work_dir, paths)

    assert captured, "no subprocess was started"
    for env in captured:
        _assert_pin_matches_tmp_paths(env, paths)
        assert env["TMPDIR"] != str(work_dir)


def _work_dir_env_call_sites() -> dict[Path, list[int]]:
    """Every ``scripts/**`` file that *calls* ``work_dir_env`` and the lines."""
    call_sites: dict[Path, list[int]] = {}
    for source in sorted((REPO_ROOT / "scripts").rglob("*.py")):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        lines = [
            node.lineno
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Name) and node.func.id == "work_dir_env")
                or (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "work_dir_env"
                )
            )
        ]
        if lines:
            call_sites[source.relative_to(REPO_ROOT)] = lines
    return call_sites


def test_work_dir_env_is_only_called_from_tmp_paths():
    """IC-18: ``work_dir_env`` is reachable only through ``tmp_env``."""
    call_sites = _work_dir_env_call_sites()
    only = Path("scripts/lib/tmp_paths.py")

    assert set(call_sites) == {only}, {
        str(path): lines for path, lines in call_sites.items()
    }
    assert call_sites[only], "tmp_env must delegate to work_dir_env"


def test_framework_render_modules_call_tmp_env():
    """The two Task-10 call sites go through ``tmp_env``, not ``work_dir_env``."""
    for relative in ("scripts/lib/context_report.py", "scripts/lib/meta_optimizer.py"):
        tree = ast.parse((REPO_ROOT / relative).read_text(encoding="utf-8"))
        called = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert "tmp_env" in called, relative
