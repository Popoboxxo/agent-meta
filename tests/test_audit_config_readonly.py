"""Regression test (issue #738): ``--audit-config`` is documented as
report-only but used to fall through to the common sync tail, which wrote the
four ``.meta-config/env.*`` scripts and ``sync.log`` into the project.

The mode must short-circuit before ``_run_common_tail`` and leave the project
untouched while still printing the audit report.

Run: python -m pytest tests/test_audit_config_readonly.py -q
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SYNC_PY = _REPO_ROOT / "scripts" / "sync.py"

_ENV_FILES = ("env.sh", "env.ps1", "env.unset.sh", "env.unset.ps1")

_MINIMAL_PROJECT_YAML = (
    "ai-providers: [Claude]\n"
    "dod-preset: rapid-prototyping\n"
    "roles: [developer]\n"
    "project: {name: audit-ro-test, prefix: ar, short: audit-ro}\n"
    "variables: {PROJECT_NAME: audit-ro-test}\n"
)


def _write_minimal_project(project_root: Path) -> Path:
    meta = project_root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    config = meta / "project.yaml"
    config.write_text(_MINIMAL_PROJECT_YAML, encoding="utf-8")
    return config


def _run_sync(project_root: Path, *extra: str) -> subprocess.CompletedProcess:
    config = project_root / ".meta-config" / "project.yaml"
    return subprocess.run(
        [sys.executable, str(_SYNC_PY), "--config", str(config), *extra],
        capture_output=True, text=True, cwd=str(project_root),
    )


def test_audit_config_writes_no_env_or_sync_log(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write_minimal_project(project_root)

    result = _run_sync(project_root, "--audit-config")

    assert result.returncode == 0, result.stderr
    assert "Config audit" in result.stdout, result.stdout
    assert "Traceback" not in result.stderr

    meta = project_root / ".meta-config"
    for name in _ENV_FILES:
        assert not (meta / name).exists(), f"unexpected env file: {name}"
    assert not (project_root / "sync.log").exists(), "unexpected sync.log written"


def test_audit_config_apply_still_writes_no_env_or_sync_log(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write_minimal_project(project_root)

    result = _run_sync(project_root, "--audit-config", "--apply")

    assert result.returncode == 0, result.stderr
    assert "Config audit" in result.stdout, result.stdout

    meta = project_root / ".meta-config"
    for name in _ENV_FILES:
        assert not (meta / name).exists(), f"unexpected env file: {name}"
    assert not (project_root / "sync.log").exists(), "unexpected sync.log written"
