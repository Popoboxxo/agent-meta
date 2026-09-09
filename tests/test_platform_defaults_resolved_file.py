"""Task 6 (platform-project-defaults feature): .meta-config/
platform-defaults.resolved.yaml is written by every non-dry-run sync.py
run and registered in .meta-config/generated-file-hashes.json.

Runs the real sync.py as a subprocess against a synthetic project dir --
same mechanics as tests/scenarios/run.sh, kept as a pytest test here so it
also runs under a plain `pytest tests/` invocation.
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]

_MINIMAL_PROJECT_YAML = """
agent-meta-version: 0.101.0
ai-providers: [Claude]
platforms: [hacs]
roles: [orchestrator, developer, git]
project:
  name: platform-defaults-test
  prefix: pdt
  short: platform-defaults-test
"""


def test_resolved_file_written_and_registered(tmp_path):
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(_MINIMAL_PROJECT_YAML, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py")],
        cwd=str(tmp_path), capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    resolved_path = tmp_path / ".meta-config" / "platform-defaults.resolved.yaml"
    assert resolved_path.is_file()
    resolved = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
    assert resolved["dod-preset"] == "standard"
    assert resolved["variables"]["TEST_COMMANDS"] == "pytest tests/ --cov"

    hashes_path = tmp_path / ".meta-config" / "generated-file-hashes.json"
    assert hashes_path.is_file()
    hashes = json.loads(hashes_path.read_text(encoding="utf-8"))
    assert ".meta-config/platform-defaults.resolved.yaml" in hashes["hashes"]


def test_resolved_file_not_written_in_dry_run(tmp_path):
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(_MINIMAL_PROJECT_YAML, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"), "--dry-run"],
        cwd=str(tmp_path), capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / ".meta-config" / "platform-defaults.resolved.yaml").exists()
