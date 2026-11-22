"""Sync pipeline writes .meta-config/auto-commit-allowlist.json (issue
#694). Real-subprocess e2e test, matching the pattern used for
generated-file-hashes.json / progress-file tests."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_sync(project_dir: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"), *extra],
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
        "authority_overrides", "custom_script", "eligible_roles", "file_count_threshold",
        "mode", "secret_scan", "triggers", "version",
    ]


# --------------------------------------------------------------------------- #
# Issue #1181 (T9): allowlist stage v2, shrink warning, dry-run read-only      #
# comparison. Real-subprocess syncs (pattern: the tests above).               #
# --------------------------------------------------------------------------- #

_AC_AUTO = "auto_commit:\n  mode: auto\n  triggers: [task-boundary]\n"
_AC_GRANT = (
    "  authority_overrides:\n"
    "    documenter:\n"
    "      authority: direct\n"
    "      acknowledge_full_shell: true\n"
)


def _write_project_yaml(tmp_path: Path, roles: str, auto_block: str = _AC_AUTO,
                        extra: str = "") -> None:
    (tmp_path / ".meta-config").mkdir(exist_ok=True)
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        "project:\n  name: t\n  prefix: t\n"
        "ai-providers: [Claude]\n"
        f"roles: {roles}\n"
        + auto_block + extra,
        encoding="utf-8",
    )


def _allowlist_path(tmp_path: Path) -> Path:
    return tmp_path / ".meta-config" / "auto-commit-allowlist.json"


def _write_previous_allowlist(tmp_path: Path, eligible: list[str], *,
                              mode: str = "off", overrides: dict | None = None) -> None:
    payload = {
        "version": 2,
        "mode": mode,
        "eligible_roles": eligible,
        "authority_overrides": overrides if overrides is not None else {},
        "triggers": ["task-boundary"],
        "file_count_threshold": 5,
        "custom_script": None,
        "secret_scan": True,
    }
    _allowlist_path(tmp_path).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def test_shrink_warning_lists_dropped_roles_with_reasons(tmp_path):
    previous_roles = [
        "accountant", "analyst", "architect", "auditor", "backend",
        "copyeditor", "data-engineer", "designer", "developer", "devops",
        "documenter", "explorer", "frontend", "git", "log-analyzer",
        "mentor", "planner", "product-manager", "reviewer", "senior-developer",
        "tester", "validator", "writer", "zookeeper",
    ]
    _write_project_yaml(
        tmp_path, "[developer, tester, git, copyeditor, documenter, planner]")
    _write_previous_allowlist(tmp_path, previous_roles)
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    line = result.stderr
    assert "auto-commit-allowlist: eligible_roles shrank 24 -> " in line
    assert "(-" in line
    assert "copyeditor (no Bash)" in line
    assert "documenter (no Bash)" in line
    assert "planner (no Bash)" in line
    assert "product-manager (role removed)" in line
    assert "… (+" in line and " more)" in line


def test_no_bash_reason_requires_role_in_roles(tmp_path):
    _write_project_yaml(tmp_path, "[developer, tester]")
    _write_previous_allowlist(tmp_path, ["product-manager", "developer"])
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "product-manager (role removed)" in result.stderr
    assert "product-manager (no Bash)" not in result.stderr


def test_shrink_warning_reports_gate_dropped(tmp_path):
    fixture = _REPO_ROOT / "tests" / "fixtures" / "active-set" / "p20" / ".meta-config" / "project.yaml"
    (tmp_path / ".meta-config").mkdir(exist_ok=True)
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        "project:\n  name: t\n  prefix: t\n"
        + fixture.read_text(encoding="utf-8") + _AC_AUTO,
        encoding="utf-8",
    )
    _write_previous_allowlist(tmp_path, ["senior-developer", "developer"])
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "senior-developer (gate-dropped)" in result.stderr


def test_shrink_warning_reports_withdrawn_grant(tmp_path):
    # D17: previous file had a grant AND the role left `roles:` (the override
    # key may still be set in config) -> "grant withdrawn", not "role removed".
    _write_project_yaml(
        tmp_path, "[developer, tester]", extra=_AC_GRANT)
    _write_previous_allowlist(
        tmp_path, ["documenter", "developer"], overrides={"documenter": "direct"})
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "documenter (grant withdrawn)" in result.stderr
    assert "documenter (role removed)" not in result.stderr


def test_removed_grant_key_while_role_listed_is_no_bash(tmp_path):
    # D17 second revocation path: only the override key is removed while the
    # role stays in `roles:` -> "no Bash", NOT "grant withdrawn".
    _write_project_yaml(tmp_path, "[developer, tester, documenter]")
    _write_previous_allowlist(
        tmp_path, ["documenter", "developer"], overrides={"documenter": "direct"})
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "documenter (no Bash)" in result.stderr
    assert "documenter (grant withdrawn)" not in result.stderr


def test_mode_change_to_off_is_reported(tmp_path):
    _write_project_yaml(tmp_path, "[developer, tester]", auto_block="")
    _write_previous_allowlist(
        tmp_path, ["developer", "documenter", "planner"], mode="auto")
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    assert (
        "auto-commit-allowlist: mode changed auto -> off; "
        "all 3 eligible role(s) dropped"
    ) in result.stderr


def test_missing_previous_allowlist_is_info(tmp_path):
    _write_project_yaml(tmp_path, "[developer, tester]")
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    assert (
        "auto-commit-allowlist: no previous allowlist — shrink check skipped"
    ) in result.stdout
    assert "auto-commit-allowlist:" not in result.stderr


def test_unreadable_previous_allowlist_is_warn(tmp_path):
    _write_project_yaml(tmp_path, "[developer, tester]")
    _allowlist_path(tmp_path).write_text("{", encoding="utf-8")
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    assert (
        "auto-commit-allowlist: previous allowlist unreadable at "
    ) in result.stderr
    assert "auto-commit-allowlist.json" in result.stderr
    assert "shrink check skipped" in result.stderr
    assert "eligible_roles shrank" not in result.stderr


@pytest.mark.parametrize("payload", ("[]", "null"))
def test_non_object_previous_allowlist_is_warn_only(tmp_path, payload):
    # Review recommendation: parseable non-object JSON must never abort sync
    # (D19), and `null` must not be mistaken for a missing file (INFO path).
    _write_project_yaml(tmp_path, "[developer, tester]")
    _allowlist_path(tmp_path).write_text(payload, encoding="utf-8")
    result = _run_sync(tmp_path, "--dry-run")
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert (
        "auto-commit-allowlist: previous allowlist unreadable at "
    ) in result.stderr
    assert "auto-commit-allowlist.json" in result.stderr
    assert "shrink check skipped" in result.stderr
    assert "no previous allowlist" not in (result.stdout + result.stderr)
    assert "eligible_roles shrank" not in result.stderr


def test_shrink_check_runs_in_dry_run_without_write(tmp_path):
    _write_project_yaml(tmp_path, "[developer, tester]")
    _write_previous_allowlist(tmp_path, ["product-manager", "developer"])
    before = _allowlist_path(tmp_path).read_bytes()
    result = _run_sync(tmp_path, "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "product-manager (role removed)" in result.stderr
    assert _allowlist_path(tmp_path).read_bytes() == before


def test_allowlist_is_written_with_version_two(tmp_path):
    _write_project_yaml(tmp_path, "[developer, tester]")
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    data = json.loads(_allowlist_path(tmp_path).read_text(encoding="utf-8"))
    assert data["version"] == 2
    assert "authority_overrides" in data
    assert data["authority_overrides"] == {}


def test_check_mode_stays_rc_zero_on_shrink(tmp_path):
    _write_project_yaml(tmp_path, "[developer, tester]")
    # Prime every generated file first so --check has zero pending drift;
    # only the WARN-only shrink comparison may still run (D19).
    assert _run_sync(tmp_path).returncode == 0
    _write_previous_allowlist(tmp_path, ["product-manager", "developer"])
    result = _run_sync(tmp_path, "--dry-run", "--check")
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "product-manager (role removed)" in result.stderr
