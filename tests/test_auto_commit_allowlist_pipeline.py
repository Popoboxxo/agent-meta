"""Sync pipeline writes .meta-config/auto-commit-allowlist.json (issue
#694). Real-subprocess e2e test, matching the pattern used for
generated-file-hashes.json / progress-file tests."""

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_sync(project_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py")],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )


def test_allowlist_written_when_auto_commit_enabled(tmp_path):
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        "project:\n  name: t\n  prefix: t\n"
        "ai-providers: [Claude]\n"
        "roles: [orchestrator, developer, git]\n"
        "auto_commit:\n  mode: auto\n  triggers: [task-boundary]\n",
        encoding="utf-8",
    )
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr

    allowlist_path = tmp_path / ".meta-config" / "auto-commit-allowlist.json"
    assert allowlist_path.exists()
    data = json.loads(allowlist_path.read_text(encoding="utf-8"))
    assert data["mode"] == "auto"
    assert "developer" in data["eligible_roles"]
    assert "git" not in data["eligible_roles"]


def test_allowlist_reflects_mode_off_when_unconfigured(tmp_path):
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        "project:\n  name: t\n  prefix: t\n"
        "ai-providers: [Claude]\n"
        "roles: [orchestrator, developer, git]\n",
        encoding="utf-8",
    )
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr

    allowlist_path = tmp_path / ".meta-config" / "auto-commit-allowlist.json"
    assert allowlist_path.exists()
    data = json.loads(allowlist_path.read_text(encoding="utf-8"))
    assert data["mode"] == "off"
    # eligible_roles is capability data (independent of mode); 'off' still
    # withholds actual commit authority via the guard hook's mode gate.
    assert "developer" in data["eligible_roles"]
    assert "git" not in data["eligible_roles"]
