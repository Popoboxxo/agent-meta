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
    # issue #767: eligible_roles is direct-only (Bash + Edit/Write); the
    # orchestrator is delegate-only and must not appear.
    assert data["eligible_roles"] == ["developer"]
    assert "developer" in data["eligible_roles"]
    assert "orchestrator" not in data["eligible_roles"]
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
    assert data["eligible_roles"] == ["developer"]
    assert "developer" in data["eligible_roles"]
    assert "orchestrator" not in data["eligible_roles"]
    assert "git" not in data["eligible_roles"]


def test_allowlist_excludes_gate_dropped_role(tmp_path):
    # IC-18 no. 14 / AC-84 (spec-faithful direction): senior-developer is
    # dropped by the developer_tiers gate in the p20 fixture (no
    # junior-developer), so it must NOT keep commit authority in the allowlist
    # even though it is listed in `roles:`.
    fixture = _REPO_ROOT / "tests" / "fixtures" / "active-set" / "p20" / ".meta-config" / "project.yaml"
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        fixture.read_text(encoding="utf-8")
        + "project:\n  name: t\n  prefix: t\n"
        "auto_commit:\n  mode: auto\n  triggers: [task-boundary]\n",
        encoding="utf-8",
    )
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    data = json.loads(
        (tmp_path / ".meta-config" / "auto-commit-allowlist.json").read_text(encoding="utf-8")
    )
    assert "senior-developer" not in data["eligible_roles"]
    assert "developer" in data["eligible_roles"]
    assert sorted(data) == [
        "custom_script", "eligible_roles", "file_count_threshold",
        "mode", "secret_scan", "triggers", "version",
    ]
