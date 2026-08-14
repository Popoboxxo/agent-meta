"""Regression tests for hooks/1-generic/dod-push-check.sh.

Background: the hook's Branch-Guard blocks any `git push` while the current
branch is main/master, to prevent accidental direct pushes bypassing PR
review. It used to apply that check uniformly, so a release's `git push
origin vX.Y.Z` tag push -- which touches no branch ref at all, and is
normally run right after the release PR merge while sitting on main -- was
blocked identically to an actual direct push of main's commit history. This
adds a tag-only-push detection (`--tags`, `push <remote> tag <name>`,
`push <remote> <ref>` where <ref> resolves to an existing tag and not an
existing branch) that skips the Branch-Guard for genuine tag pushes while
leaving it fully in effect for anything that could touch a branch.

This hook is a bash script outside the Python pytest suite, so nothing else
guards against regressions here. These tests invoke the hook as a real
subprocess against an isolated temp git repo (branch renamed to "main",
with one commit and one tag) and assert on its exit code.

Run: python -m pytest tests/test_dod_push_check_hook.py -v
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOK_PATH = _REPO_ROOT / "hooks" / "1-generic" / "dod-push-check.sh"

_BASH = shutil.which("bash") or "bash"

pytestmark = pytest.mark.skipif(
    sys.platform not in ("win32", "linux", "darwin"), reason="requires bash"
)


def _run_hook(cwd: Path, command: str) -> subprocess.CompletedProcess:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": cwd.as_posix(),
    }
    return subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )


@pytest.fixture
def repo_on_main(tmp_path):
    """An isolated git repo, on a branch literally named 'main', with a
    commit and a tag 'v1.0.0' pointing at it -- and a branch 'other-branch'
    pointing at the same commit, so tag-vs-branch name resolution is
    exercised against real refs rather than assumed to work."""
    repo = tmp_path / "repo"
    repo.mkdir()
    run = lambda *args: subprocess.run(  # noqa: E731
        ["git", *args], cwd=str(repo), capture_output=True, text=True, check=True
    )
    run("init", "-q")
    run("config", "user.email", "test@example.com")
    run("config", "user.name", "Test")
    run("checkout", "-q", "-b", "main")
    (repo / "f.txt").write_text("x", encoding="utf-8")
    run("add", "f.txt")
    run("commit", "-q", "-m", "init")
    run("tag", "-a", "v1.0.0", "-m", "v1.0.0")
    run("branch", "other-branch")
    return repo


BLOCKED_ON_MAIN = [
    "git push",
    "git push origin",
    "git push origin main",
    "git push origin HEAD",
    # a branch ref, not a tag -- must NOT be misclassified as a tag push
    "git push origin other-branch",
]

ALLOWED_TAG_PUSHES = [
    "git push origin v1.0.0",
    "git push -u origin v1.0.0",
    "git push origin refs/tags/v1.0.0",
    "git push origin --tags",
    "git push --tags origin",
    "git push origin tag v1.0.0",
]


@pytest.mark.parametrize("command", BLOCKED_ON_MAIN)
def test_non_tag_push_still_blocked_on_main(repo_on_main, command):
    result = _run_hook(repo_on_main, command)
    assert result.returncode == 2, (
        f"command={command!r} should still be blocked on main\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.parametrize("command", ALLOWED_TAG_PUSHES)
def test_tag_only_push_allowed_on_main(repo_on_main, command):
    result = _run_hook(repo_on_main, command)
    assert result.returncode == 0, (
        f"command={command!r} is a tag-only push and must not be blocked "
        f"by the Branch-Guard\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_push_of_nonexistent_ref_falls_back_to_branch_guard(repo_on_main):
    # A ref that resolves to neither a tag nor a branch (typo, or a ref
    # that doesn't exist locally yet) must not be treated as tag-safe --
    # fail closed, keep the Branch-Guard active.
    result = _run_hook(repo_on_main, "git push origin does-not-exist")
    assert result.returncode == 2
