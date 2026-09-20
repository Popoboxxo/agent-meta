"""Tests for the warning-only basetemp guard in ``tests/conftest.py``.

The guard must *warn* — never fail — when pytest's effective basetemp lives
inside the repository. Regression context: the 2026-09-19/20 disk incident.
"""
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONFTEST_PATH = Path(__file__).resolve().parent / "conftest.py"


def _load_conftest():
    """Load ``tests/conftest.py`` by path, without sys.path gymnastics."""
    spec = importlib.util.spec_from_file_location("am_tests_conftest", _CONFTEST_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_conftest()


def _fake_config(basetemp=None, recorded=None):
    """Minimal stand-in exposing only what the guard touches."""
    return SimpleNamespace(
        option=SimpleNamespace(basetemp=basetemp),
        issue_config_time_warning=lambda warning, stacklevel=1: (
            recorded.append(warning) if recorded is not None else None
        ),
    )


def test_is_within_matches_nested_and_exact_paths():
    root = Path("/a/b")
    assert guard._is_within("/a/b", root)
    assert guard._is_within("/a/b/c/d", root)
    assert not guard._is_within("/a/bc", root)
    assert not guard._is_within("/a", root)


def test_guard_detects_in_repo_basetemp():
    in_repo = guard._AGENT_META_ROOT / ".tmp" / "pytest-probe"
    assert guard.basetemp_inside_repo(_fake_config(basetemp=str(in_repo)))


def test_guard_ignores_external_basetemp():
    assert not guard.basetemp_inside_repo(_fake_config(basetemp="/var/tmp/pytest-of-x"))


def test_guard_warns_but_does_not_fail_on_in_repo_basetemp():
    in_repo = guard._AGENT_META_ROOT / ".tmp" / "pytest-probe"
    recorded = []
    guard.pytest_configure(_fake_config(basetemp=str(in_repo), recorded=recorded))
    assert len(recorded) == 1
    assert isinstance(recorded[0], Warning)
    assert "inside the repository" in str(recorded[0])


def test_guard_stays_silent_for_external_basetemp():
    recorded = []
    guard.pytest_configure(_fake_config(basetemp="/var/tmp/pytest-of-x", recorded=recorded))
    assert recorded == []


def test_guard_falls_back_to_tmpdir_env(monkeypatch):
    monkeypatch.setenv("TMPDIR", str(guard._AGENT_META_ROOT / ".tmp" / "tmproot"))
    recorded = []
    guard.pytest_configure(_fake_config(recorded=recorded))
    assert len(recorded) == 1


def test_guard_e2e_probe():
    """Trivial target for the nested pytest run below."""
    assert True


def test_guard_is_visible_and_non_fatal_in_a_real_run():
    """End-to-end: an in-repo basetemp warns visibly and still exits 0."""
    basetemp = _REPO_ROOT / ".tmp" / "pytest-guard-e2e"
    try:
        result = subprocess.run(  # noqa: PLW1510
            [
                sys.executable, "-m", "pytest",
                "tests/test_basetemp_guard.py::test_guard_e2e_probe",
                "-q", "-p", "no:cacheprovider",
                f"--basetemp={basetemp}",
            ],
            cwd=str(_REPO_ROOT), capture_output=True, text=True, timeout=300,
        )
        combined = result.stdout + result.stderr
        assert result.returncode == 0, combined
        assert "is inside the repository" in combined, combined
    finally:
        shutil.rmtree(basetemp, ignore_errors=True)
