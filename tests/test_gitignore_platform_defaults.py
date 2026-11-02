"""Tests for the generated platform-defaults snapshot in the managed .gitignore
block (#1073).

`.meta-config/platform-defaults.resolved.yaml` is a pure snapshot without a CI
contract, so the managed block must ignore it unconditionally -- on the
dedicated-context (exact) path and on the additive non-dedicated path alike.
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import pytest

from lib.generated_file_drift import PLATFORM_DEFAULTS_RESOLVED_REL
from lib.gitignore import (
    FRAMEWORK_GENERATED_ENTRIES,
    compute_base_gitignore_entries,
    framework_baseline_entries,
)

_PC = {"Claude": {"has_dedicated_context_file": True, "agents_dir": ".claude/agents",
                  "gitignore_entries": [".claude/settings.local.json"]}}


def test_constant_matches_drift_module():
    # Pinned instead of imported from lib.gitignore to avoid a cycle risk; the
    # drift scanner and the gitignore writer must agree on the same path.
    assert FRAMEWORK_GENERATED_ENTRIES == (PLATFORM_DEFAULTS_RESOLVED_REL,)


@pytest.mark.parametrize("cfg", [{}, {"generated": True}, {"ignore-provider-dirs": True},
                                 {"ignore-provider-dirs": True, "generated": True}])
def test_platform_defaults_snapshot_in_base_entries(cfg):
    entries = compute_base_gitignore_entries(["Claude"], _PC, cfg)
    assert PLATFORM_DEFAULTS_RESOLVED_REL in entries


def test_non_dedicated_framework_baseline_contains_snapshot():
    assert framework_baseline_entries() == [
        "sync.log", "*.sync-backup-*", PLATFORM_DEFAULTS_RESOLVED_REL]


def test_git_check_ignore_matches_entry(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text(
        PLATFORM_DEFAULTS_RESOLVED_REL + "\n", encoding="utf-8")
    r = subprocess.run(
        ["git", "check-ignore", "-q", PLATFORM_DEFAULTS_RESOLVED_REL], cwd=tmp_path)
    assert r.returncode == 0
