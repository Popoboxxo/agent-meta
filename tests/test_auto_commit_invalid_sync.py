"""#1142: invalid auto_commit warns, keeps the sync going (rc 0) and never rewrites the allowlist."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_FIX = Path(__file__).resolve().parent / "fixtures" / "active-set" / "p10"
_SYNC = _ROOT / "scripts" / "sync.py"

_VARIANTS = {
    "off-with-triggers": "auto_commit:\n  mode: off\n  triggers: [task-boundary]\n",
    "custom-without-script": "auto_commit:\n  mode: custom\n",
}


def _project(tmp_path: Path, block: str) -> Path:
    project = tmp_path / "proj"
    (project / ".meta-config").mkdir(parents=True)
    shutil.copy(_FIX / ".meta-config" / "project.yaml", project / ".meta-config" / "project.yaml")
    with open(project / ".meta-config" / "project.yaml", "a", encoding="utf-8") as fh:
        fh.write(block)
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    return project


def _sync(project: Path, *flags: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SYNC), "--config", str(project / ".meta-config" / "project.yaml"), *flags],
        cwd=project, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)


@pytest.mark.parametrize("block", list(_VARIANTS.values()), ids=list(_VARIANTS))
def test_invalid_auto_commit_writes_no_allowlist(tmp_path, block):
    project = _project(tmp_path, block)
    result = _sync(project, "--init")
    assert result.returncode == 0, result.stderr
    assert not (project / ".meta-config" / "auto-commit-allowlist.json").exists()
    assert "auto_commit is invalid" in result.stdout + result.stderr


def test_invalid_auto_commit_keeps_stale_allowlist(tmp_path):
    project = _project(tmp_path, _VARIANTS["off-with-triggers"])
    stale = project / ".meta-config" / "auto-commit-allowlist.json"
    stale.write_bytes(b'{"stale": true}\n')
    result = _sync(project, "--init")
    assert result.returncode == 0, result.stderr
    assert stale.read_bytes() == b'{"stale": true}\n'


def test_validate_reports_error_summary(tmp_path):
    project = _project(tmp_path, _VARIANTS["off-with-triggers"])
    _sync(project, "--init")
    result = _sync(project, "--validate")
    assert result.returncode == 1
    assert "config-audit [ERROR] auto_commit" in result.stdout + result.stderr
