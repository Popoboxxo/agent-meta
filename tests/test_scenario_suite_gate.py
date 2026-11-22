"""Tests for the built-in ``scenario-suite`` release gate.

A built-in gate is a hard release gate in every release-checklist mode: exit 1
blocks the release. Dev speed profiles must never weaken it.

Run: python -m pytest tests/test_scenario_suite_gate.py -q
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.timeouts import SCRIPT_TIMEOUT

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GATE_SOURCE = (
    _REPO_ROOT / "hooks" / "1-generic" / "release-gates" / "scenario-suite.sh"
)
_HOOK_COMMON = _REPO_ROOT / "hooks" / "1-generic" / "lib" / "hook_common.sh"

_gate_test = pytest.mark.skipif(
    sys.platform not in ("linux", "darwin"), reason="requires bash"
)


def _deploy_gate(tmp_path: Path) -> Path:
    """Lay out a minimal deployed hooks/ tree around the gate source."""
    gate_dir = tmp_path / "hooks" / "release-gates"
    lib_dir = tmp_path / "hooks" / "lib"
    gate_dir.mkdir(parents=True)
    lib_dir.mkdir(parents=True)
    shutil.copyfile(_GATE_SOURCE, gate_dir / "scenario-suite.sh")
    shutil.copyfile(_HOOK_COMMON, lib_dir / "hook_common.sh")
    return gate_dir / "scenario-suite.sh"


def _run_gate(gate: Path, project_root: Path, **env_overrides: str):
    env = os.environ.copy()
    env["PROJECT_ROOT"] = str(project_root)
    env.update(env_overrides)
    return subprocess.run(
        ["bash", str(gate)],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=SCRIPT_TIMEOUT,
    )


def test_gate_metadata_declares_manual_opt_in() -> None:
    text = _GATE_SOURCE.read_text(encoding="utf-8")
    assert "# hook: scenario-suite" in text
    assert "# event: Manual" in text
    assert "# enabled_by_default: false" in text
    assert "SCENARIO_PROFILE=release" in text


@_gate_test
def test_disabled_gate_self_skips(tmp_path: Path) -> None:
    gate = _deploy_gate(tmp_path)
    result = _run_gate(gate, tmp_path, PRE_RELEASE_GATE_ENABLED="false")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[SKIP] scenario-suite: gate disabled" in result.stdout


@_gate_test
def test_enabled_gate_skips_when_framework_is_missing(tmp_path: Path) -> None:
    gate = _deploy_gate(tmp_path)
    result = _run_gate(gate, tmp_path, PRE_RELEASE_GATE_ENABLED="true",
                       AGENT_META_ROOT="")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[SKIP] scenario-suite: no agent-meta checkout" in result.stdout


@_gate_test
def test_failing_full_suite_blocks_release_and_uses_release_profile(tmp_path: Path) -> None:
    gate = _deploy_gate(tmp_path)
    framework = tmp_path / "fw"
    (framework / "scripts").mkdir(parents=True)
    (framework / "tests" / "scenarios").mkdir(parents=True)
    (framework / "scripts" / "sync.py").write_text("# stub\n", encoding="utf-8")
    probe = tmp_path / "profile.txt"
    runner = framework / "tests" / "scenarios" / "run.sh"
    runner.write_text(
        '#!/bin/bash\nprintf "%s" "${SCENARIO_PROFILE:-unset}" > "$PROBE"\nexit 7\n',
        encoding="utf-8",
    )
    runner.chmod(0o755)

    result = _run_gate(gate, tmp_path, PRE_RELEASE_GATE_ENABLED="true",
                       AGENT_META_ROOT=str(framework), PROBE=str(probe))

    assert result.returncode == 7, result.stdout + result.stderr
    assert "[FAIL] scenario-suite: full scenario suite failed" in result.stdout
    assert probe.read_text(encoding="utf-8") == "release"
