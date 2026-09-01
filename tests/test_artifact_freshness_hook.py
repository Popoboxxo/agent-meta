"""Regression tests for hooks/1-generic/release-gates/artifact-freshness.sh
(issue #600: unreliable mtime-based freshness check).

Background: the gate used to compare filesystem mtimes to decide whether a
generated artifact is stale relative to its source. In CI or on a fresh
`git clone`/checkout, many tools set uniform mtimes for all checked-out
files, making mtime comparisons unreliable -- a source file "touched" only
at the filesystem level (no real content/commit change) could wrongly
appear newer than its already-fresh generated artifact. The gate now
prefers `git log`-derived commit timestamps for both source AND generated
artifacts, falling back to filesystem mtime only for paths git has no
history for (e.g. untracked/gitignored build output).

This hook is a bash script outside the Python pytest suite, so nothing else
guards against regressions here. These tests invoke the gate as a real
subprocess against an isolated git repo.

Run: python -m pytest tests/test_artifact_freshness_hook.py -v
"""

import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOK_PATH = _REPO_ROOT / "hooks" / "1-generic" / "release-gates" / "artifact-freshness.sh"

_BASH = shutil.which("bash") or "bash"

pytestmark = pytest.mark.skipif(
    sys.platform not in ("win32", "linux", "darwin"), reason="requires bash"
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True, check=True)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q")
    _git(r, "config", "user.email", "test@example.com")
    _git(r, "config", "user.name", "Test")
    return r


def _run_gate(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        capture_output=True,
        text=True,
        cwd=str(repo),
        env={"PROJECT_ROOT": str(repo), "PRE_RELEASE_GATE_ENABLED": "true",
             "PATH": "/usr/bin:/bin:/usr/local/bin"},
    )


def _write_config(repo: Path) -> None:
    (repo / ".agent-meta").mkdir(exist_ok=True)
    (repo / ".agent-meta" / "generated-artifacts.yaml").write_text(
        "artifacts:\n  - source: source.txt\n    generated: generated.txt\n",
        encoding="utf-8",
    )


def test_fresh_artifact_committed_together_passes(repo):
    (repo / "source.txt").write_text("v1", encoding="utf-8")
    (repo / "generated.txt").write_text("gen v1", encoding="utf-8")
    _write_config(repo)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "v1")

    result = _run_gate(repo)
    assert result.returncode == 0, result.stdout
    assert "[FAIL]" not in result.stdout


def test_filesystem_only_mtime_touch_does_not_cause_false_fail(repo):
    """issue #600's core regression case: bumping a source file's mtime at
    the filesystem level ONLY (no new commit, no real content change) must
    NOT make an already-fresh, already-committed artifact look stale."""
    (repo / "source.txt").write_text("v1", encoding="utf-8")
    (repo / "generated.txt").write_text("gen v1", encoding="utf-8")
    _write_config(repo)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "v1")

    # Simulate a checkout tool setting a much newer mtime with no git change.
    future = time.time() + 10_000
    import os
    os.utime(repo / "source.txt", (future, future))

    result = _run_gate(repo)
    assert result.returncode == 0, result.stdout
    assert "[FAIL]" not in result.stdout


def test_real_source_change_after_generated_fails(repo):
    (repo / "source.txt").write_text("v1", encoding="utf-8")
    (repo / "generated.txt").write_text("gen v1", encoding="utf-8")
    _write_config(repo)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "v1")

    time.sleep(1.1)  # ensure a distinct git commit second-resolution timestamp
    (repo / "source.txt").write_text("v2", encoding="utf-8")
    _git(repo, "add", "source.txt")
    _git(repo, "commit", "-q", "-m", "v2 source change")

    result = _run_gate(repo)
    assert result.returncode == 1, result.stdout
    assert "[FAIL]" in result.stdout
    assert "generated.txt" in result.stdout


def test_untracked_generated_artifact_falls_back_to_filesystem_mtime(repo):
    """A generated artifact git has no history for at all (e.g. gitignored
    build output) must still be checked via its filesystem mtime, not
    unconditionally reported as missing just because git_mtime() is None."""
    (repo / "source.txt").write_text("v1", encoding="utf-8")
    _write_config(repo)
    _git(repo, "add", "source.txt", ".agent-meta")
    _git(repo, "commit", "-q", "-m", "v1")

    # generated.txt is written to disk AFTER the commit and never committed
    # (simulates a gitignored build artifact) -- newer filesystem mtime than
    # source.txt's commit timestamp, so must be considered fresh.
    time.sleep(0.05)
    (repo / "generated.txt").write_text("gen v1", encoding="utf-8")

    result = _run_gate(repo)
    assert result.returncode == 0, result.stdout
    assert "[FAIL]" not in result.stdout
