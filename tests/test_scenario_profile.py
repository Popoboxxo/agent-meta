"""Tests for the scenario harness dev/release profiles.

Dev must be a pure speed profile: same catalog, same asserts, same PASS/FAIL
semantics, but the repo-wide consistency scan runs once and the redundant
dry-run pass can be skipped. Release stays byte-for-byte on the historical
three-pass behaviour.

Run: python -m pytest tests/test_scenario_profile.py -q
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from tests.timeouts import SLOW_TIMEOUT

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RUNNER = _REPO_ROOT / "tests" / "scenarios" / "run.sh"
_SCENARIO = "01-minimal-claude"


def _harness_env(tmp_path: Path) -> tuple[dict[str, str], Path]:
    """PATH-shim 'python3' that records every script argument."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    calls = tmp_path / "calls.log"
    wrapper = bin_dir / "python3"
    wrapper.write_text(
        '#!/bin/bash\nprintf "%s\\n" "$*" >> "$CALL_LOG"\nexec "$REAL_PY" "$@"\n',
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    (tmp_path / "tmp").mkdir(exist_ok=True)

    env = os.environ.copy()
    env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]
    env["REAL_PY"] = sys.executable
    env["CALL_LOG"] = str(calls)
    env["TMPDIR"] = str(tmp_path / "tmp")
    return env, calls


def _run(tmp_path: Path, **overrides: str) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    env, calls = _harness_env(tmp_path)
    env.update(overrides)
    result = subprocess.run(
        ["bash", str(_RUNNER), _SCENARIO],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=SLOW_TIMEOUT,
    )
    return result, calls.read_text(encoding="utf-8").splitlines() if calls.exists() else []


def test_invalid_profile_fails_fast() -> None:
    env = os.environ.copy()
    env["SCENARIO_PROFILE"] = "bogus"
    result = subprocess.run(
        ["bash", str(_RUNNER), "--list"],
        cwd=_REPO_ROOT, env=env, capture_output=True, text=True, timeout=SLOW_TIMEOUT,
    )
    assert result.returncode == 2
    assert "SCENARIO_PROFILE must be 'release' or 'dev'" in result.stderr


def test_both_profiles_select_the_same_catalog() -> None:
    def names(profile: str) -> list[str]:
        env = os.environ.copy()
        env["SCENARIO_PROFILE"] = profile
        result = subprocess.run(
            ["bash", str(_RUNNER), "--list"],
            cwd=_REPO_ROOT, env=env, capture_output=True, text=True, timeout=SLOW_TIMEOUT,
        )
        assert result.returncode == 0, result.stderr
        return result.stdout.splitlines()

    assert names("dev") == names("release")


def test_dev_profile_uses_config_only_validation(tmp_path: Path) -> None:
    result, calls = _run(
        tmp_path, SCENARIO_PROFILE="dev", SCENARIO_SKIP_SOURCE_CHECK="1"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Profile: dev" in result.stdout
    assert "PASS  " + _SCENARIO in result.stdout
    assert any(line.endswith(" --validate-config-only") for line in calls), calls
    assert not any(line.endswith(" --validate") for line in calls), calls
    assert not any(" --dry-run" in line for line in calls), calls
    assert not any("consistency-check.py" in line for line in calls), calls


def test_release_profile_keeps_all_three_passes(tmp_path: Path) -> None:
    result, calls = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Profile: release" in result.stdout
    assert any(" --dry-run" in line for line in calls), calls
    assert any(line.endswith(" --validate") for line in calls), calls
    assert not any(" --validate-config-only" in line for line in calls), calls
