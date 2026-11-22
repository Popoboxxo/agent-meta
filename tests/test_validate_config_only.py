"""Tests for ``sync.py --validate-config-only``.

The flag powers the scenario harness dev profile: it keeps every
config-dependent validation but skips the repo-wide source scan, which is
identical for every scenario and is run once per checkout instead.

Run: python -m pytest tests/test_validate_config_only.py -q
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from tests.timeouts import SYNC_VALIDATE_TIMEOUT

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SYNC_PY = _REPO_ROOT / "scripts" / "sync.py"
_SCENARIO_CONFIG = (
    _REPO_ROOT / "tests" / "scenarios" / "configs" / "01-minimal-claude.project.yaml"
)


def _run(tmp_path: Path, *flags: str) -> subprocess.CompletedProcess[str]:
    config_dir = tmp_path / ".meta-config"
    config_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(_SCENARIO_CONFIG, config_dir / "project.yaml")
    env = os.environ.copy()
    env["TMPDIR"] = str(tmp_path / "tmp")
    (tmp_path / "tmp").mkdir(exist_ok=True)
    return subprocess.run(
        [sys.executable, str(_SYNC_PY), *flags],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=SYNC_VALIDATE_TIMEOUT,
    )


def test_help_documents_flag() -> None:
    result = subprocess.run(
        [sys.executable, str(_SYNC_PY), "--help"],
        capture_output=True,
        text=True,
        timeout=SYNC_VALIDATE_TIMEOUT,
    )
    assert result.returncode == 0
    assert "--validate-config-only" in result.stdout


def test_config_only_skips_source_scan_but_keeps_project_checks(tmp_path: Path) -> None:
    result = _run(tmp_path, "--validate-config-only")
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "source consistency checks skipped" in output
    # The config-only report reuses the generic report header, but the
    # source-scan report is gone: one header instead of two in full --validate.
    assert output.count("agent-meta consistency-check") == 1
    assert output.index("source consistency checks skipped") < output.index(
        "agent-meta consistency-check"
    )
    # Config-dependent findings still ran (01-minimal-claude has warnings).
    assert "warning(s) found" in output


def test_full_validate_unchanged(tmp_path: Path) -> None:
    result = _run(tmp_path, "--validate")
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "agent-meta consistency-check" in output
    assert output.count("agent-meta consistency-check") == 2
    assert "source consistency checks skipped" not in output
