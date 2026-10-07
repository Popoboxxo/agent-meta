"""Regression tests for hooks/1-generic/release-gates/docker-image-scan.sh
(issue #745: scan multiple / auto-discovered Dockerfiles instead of only a
single root-level `Dockerfile`).

This hook is a bash script outside the Python pytest suite (same situation
as tests/test_pre_release_check_hook.py), so nothing else guards against
regressions here. These tests invoke the real gate script as a subprocess
against a synthetic project tree, with a stub `trivy` executable on PATH
(no real scanner/network access needed).

Run: python -m pytest tests/test_docker_image_scan_multi.py -v
"""

from __future__ import annotations

import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOK_PATH = _REPO_ROOT / "hooks" / "1-generic" / "release-gates" / "docker-image-scan.sh"

_BASH = shutil.which("bash") or "bash"

pytestmark = pytest.mark.skipif(
    sys.platform not in ("win32", "linux", "darwin"), reason="requires bash"
)

# Stub trivy: fails (exit 1) only for images whose name contains "vuln",
# mimicking a HIGH/CRITICAL finding. Mirrors the real invocation shape
# (`trivy image --severity HIGH,CRITICAL --exit-code 1 <image>`).
_TRIVY_STUB = """#!/bin/bash
image="${@: -1}"
echo "[trivy-stub] scanned $image"
if [[ "$image" == *vuln* ]]; then
  exit 1
fi
exit 0
"""


@pytest.fixture
def stub_bin(tmp_path):
    bin_dir = tmp_path / "stub-bin"
    bin_dir.mkdir()
    trivy = bin_dir / "trivy"
    trivy.write_text(_TRIVY_STUB, encoding="utf-8")
    trivy.chmod(trivy.stat().st_mode | stat.S_IEXEC)
    return bin_dir


def _run_gate(project_root: Path, stub_bin: Path, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    env = {
        "PROJECT_ROOT": str(project_root),
        "PATH": f"{stub_bin}:/usr/bin:/bin:/usr/local/bin",
        "PRE_RELEASE_GATE_ENABLED": "true",
    }
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        capture_output=True,
        text=True,
        env=env,
    )


def test_multiple_dockerfiles_auto_discovered_and_scanned(tmp_path, stub_bin):
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "Dockerfile").write_text("FROM node:20\n", encoding="utf-8")
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "Dockerfile").write_text("FROM python:3.11\n", encoding="utf-8")

    result = _run_gate(tmp_path, stub_bin)

    assert "[INFO] docker-image-scan: scanning node:20" in result.stdout
    assert "[INFO] docker-image-scan: scanning python:3.11" in result.stdout
    assert result.returncode == 0


def test_node_modules_excluded_from_auto_discovery(tmp_path, stub_bin):
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "Dockerfile").write_text("FROM python:3.11\n", encoding="utf-8")
    nested = tmp_path / "node_modules" / "some-pkg"
    nested.mkdir(parents=True)
    (nested / "Dockerfile").write_text("FROM should-not-be-scanned:1\n", encoding="utf-8")

    result = _run_gate(tmp_path, stub_bin)

    assert "python:3.11" in result.stdout
    assert "should-not-be-scanned" not in result.stdout
    assert result.returncode == 0


def test_high_critical_finding_in_any_file_fails_gate(tmp_path, stub_bin):
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "Dockerfile").write_text("FROM node:20-vuln\n", encoding="utf-8")
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "Dockerfile").write_text("FROM python:3.11\n", encoding="utf-8")

    result = _run_gate(tmp_path, stub_bin)

    assert result.returncode == 1
    assert "[FAIL]" in result.stdout
    # the clean file was still scanned despite the other file's failure
    assert "python:3.11" in result.stdout


def test_explicit_paths_env_var_overrides_auto_discovery(tmp_path, stub_bin):
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "Dockerfile").write_text("FROM node:20\n", encoding="utf-8")
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "Dockerfile").write_text("FROM python:3.11\n", encoding="utf-8")
    (tmp_path / "unused").mkdir()
    (tmp_path / "unused" / "Dockerfile").write_text("FROM should-not-be-scanned:1\n", encoding="utf-8")

    result = _run_gate(
        tmp_path,
        stub_bin,
        extra_env={"PRE_RELEASE_DOCKERFILE_PATHS": "frontend/Dockerfile:backend/Dockerfile"},
    )

    assert "node:20" in result.stdout
    assert "python:3.11" in result.stdout
    assert "should-not-be-scanned" not in result.stdout
    assert result.returncode == 0


def test_no_dockerfile_found_skips_with_exit_zero(tmp_path, stub_bin):
    result = _run_gate(tmp_path, stub_bin)

    assert "[SKIP]" in result.stdout
    assert "no Dockerfile found" in result.stdout
    assert result.returncode == 0
