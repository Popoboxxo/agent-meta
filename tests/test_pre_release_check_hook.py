"""Regression tests for hooks/1-generic/pre-release-check.sh (issue #598:
release-gates/ allowlist).

Background: the dispatcher used to run every *.sh file found in its
release-gates/ subdirectory unconditionally -- a supply-chain risk (a file
placed there accidentally, via a compromised dependency, or a malicious PR
would run automatically as part of the release process with no allowlist
or integrity check). It now only runs a gate script if its filename is
listed in one of two manifests:
  - release-gates/.agent-meta-managed  (framework-shipped built-ins)
  - release-gates/.allowed-gates       (project-owned opt-in manifest)

Since issue #603 an allowlisted gate additionally needs a valid SHA-256
checksum entry in release-gates/.sha256-checksums (fail-closed otherwise);
the _register_gate_checksum() helper below performs that standard
registration step. The dedicated issue #603 integrity tests live in
tests/test_release_gate_checksums.py.

This hook is a bash script outside the Python pytest suite, so nothing else
guards against regressions here. These tests invoke the dispatcher as a
real subprocess against a synthetic release-gates/ directory.

Run: python -m pytest tests/test_pre_release_check_hook.py -v
"""

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOK_PATH = _REPO_ROOT / "hooks" / "1-generic" / "pre-release-check.sh"

_BASH = shutil.which("bash") or "bash"

pytestmark = pytest.mark.skipif(
    sys.platform not in ("win32", "linux", "darwin"), reason="requires bash"
)

_GATE_SCRIPT = """#!/bin/bash
echo "[INFO] {name}: ran"
exit {exit_code}
"""


def _make_gate(gates_dir: Path, name: str, exit_code: int = 0) -> None:
    path = gates_dir / name
    path.write_text(_GATE_SCRIPT.format(name=name, exit_code=exit_code), encoding="utf-8")
    path.chmod(0o755)


def _register_gate_checksum(gates_dir: Path, name: str) -> None:
    """Append the gate's SHA-256 line to .sha256-checksums (issue #603 flow)."""
    digest = hashlib.sha256((gates_dir / name).read_bytes()).hexdigest()
    with (gates_dir / ".sha256-checksums").open("a", encoding="utf-8") as fh:
        fh.write(f"{digest}  {name}\n")


@pytest.fixture
def project_root(tmp_path):
    hooks_dir = tmp_path / "hooks"
    (hooks_dir / "release-gates").mkdir(parents=True)
    shutil.copy(_HOOK_PATH, hooks_dir / "pre-release-check.sh")
    return tmp_path


def _run_dispatcher(project_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_BASH, str(project_root / "hooks" / "pre-release-check.sh")],
        capture_output=True,
        text=True,
        env={"PROJECT_ROOT": str(project_root), "PATH": "/usr/bin:/bin:/usr/local/bin"},
    )


def test_unlisted_gate_is_skipped_not_run(project_root):
    gates_dir = project_root / "hooks" / "release-gates"
    _make_gate(gates_dir, "evil-dropin.sh")
    # no .agent-meta-managed, no .allowed-gates -- nothing is on the allowlist
    result = _run_dispatcher(project_root)
    assert "evil-dropin: ran" not in result.stdout
    assert "not on the release-gates allowlist" in result.stdout
    assert result.returncode == 0  # a skipped script is not a release-blocking failure


def test_managed_gate_runs_when_listed_in_agent_meta_managed(project_root):
    gates_dir = project_root / "hooks" / "release-gates"
    _make_gate(gates_dir, "built-in.sh")
    (gates_dir / ".agent-meta-managed").write_text("built-in.sh\n", encoding="utf-8")
    _register_gate_checksum(gates_dir, "built-in.sh")
    result = _run_dispatcher(project_root)
    assert "built-in.sh: ran" in result.stdout
    assert result.returncode == 0


def test_project_gate_runs_when_listed_in_allowed_gates(project_root):
    gates_dir = project_root / "hooks" / "release-gates"
    _make_gate(gates_dir, "my-custom-check.sh")
    (gates_dir / ".allowed-gates").write_text("my-custom-check.sh\n", encoding="utf-8")
    _register_gate_checksum(gates_dir, "my-custom-check.sh")
    result = _run_dispatcher(project_root)
    assert "my-custom-check.sh: ran" in result.stdout
    assert result.returncode == 0


def test_mixed_allowed_and_unallowed_gates(project_root):
    gates_dir = project_root / "hooks" / "release-gates"
    _make_gate(gates_dir, "allowed.sh")
    _make_gate(gates_dir, "not-allowed.sh")
    (gates_dir / ".agent-meta-managed").write_text("allowed.sh\n", encoding="utf-8")
    _register_gate_checksum(gates_dir, "allowed.sh")
    result = _run_dispatcher(project_root)
    assert "allowed.sh: ran" in result.stdout
    assert "not-allowed.sh: ran" not in result.stdout
    assert result.returncode == 0


def test_allowed_gate_failure_still_blocks_release(project_root):
    gates_dir = project_root / "hooks" / "release-gates"
    _make_gate(gates_dir, "failing.sh", exit_code=1)
    (gates_dir / ".agent-meta-managed").write_text("failing.sh\n", encoding="utf-8")
    _register_gate_checksum(gates_dir, "failing.sh")
    result = _run_dispatcher(project_root)
    assert result.returncode == 1
    assert "FAILED" in result.stdout


def test_allowed_gates_manifest_supports_comments_and_blank_lines(project_root):
    gates_dir = project_root / "hooks" / "release-gates"
    _make_gate(gates_dir, "commented.sh")
    (gates_dir / ".allowed-gates").write_text(
        "# my custom gates\n\ncommented.sh  # inline comment\n", encoding="utf-8"
    )
    _register_gate_checksum(gates_dir, "commented.sh")
    result = _run_dispatcher(project_root)
    assert "commented.sh: ran" in result.stdout
    assert result.returncode == 0
