"""Regression tests for hooks/1-generic/orchestrator-guard.sh.

Background: the hook used to read an `agent_name` field from the
PreToolUse JSON payload to exempt the `git`/`orchestrator` agents from the
strict-mode block. That field does not exist in any provider's real
PreToolUse payload (Claude Code's documented payload is
`{session_id, transcript_path, hook_event_name, tool_name, tool_input}`
only -- see docs/guides/features/hooks.md) -- the exemption never
triggered (agent-meta issue #390).

v2.0.0 replaces this with a self-declared identity: an authorized Bash
command's first line must be the exact sentinel `#agent-meta:agent=<name>`.
Write/Edit have no safe equivalent channel (a marker would corrupt file
content) and are therefore never exempted under strict mode -- this is
intentional, not a regression.

This also covers two bugs found alongside #390 while fixing it:
- the git-mutation regex matched substrings anywhere in the command
  (`merge-base`, `check-ignore`, quoted text) instead of actual git
  subcommands;
- `$CONFIG_FILE` (a Windows path, containing backslashes) used to be
  interpolated directly into a Python string literal, so Python's own
  string-escape parsing (backslash-a, backslash-R, ...) silently corrupted
  the path, `open()` raised, and strict mode resolved to 'false'
  unconditionally on Windows regardless of `project.yaml`.

This hook is a bash script outside the Python pytest suite, so nothing
else guards against regressions here. These tests invoke the hook as a
real subprocess with synthetic PreToolUse JSON payloads and assert on its
exit code.

Run: python -m pytest tests/test_orchestrator_guard_hook.py -v
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOK_PATH = _REPO_ROOT / "hooks" / "1-generic" / "orchestrator-guard.sh"

# On Windows, plain ["bash", ...] can resolve to System32\bash.exe (the WSL
# launcher) instead of Git Bash, depending on CreateProcess search order
# (System32 is searched before PATH). The WSL launcher mishandles this
# script's CRLF line endings. Resolve the real Git Bash explicitly via PATH
# to get deterministic behavior across environments.
_BASH = shutil.which("bash") or "bash"

pytestmark = pytest.mark.skipif(
    sys.platform not in ("win32", "linux", "darwin"), reason="requires bash"
)


def _run_hook(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )


def _bash_payload(command: str) -> dict:
    return {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        # Forward slashes: the hook does raw shell string concatenation
        # (`$PROJECT_ROOT/.meta-config/project.yaml`) without normalizing
        # path separators, so a Windows-style backslash path here would
        # exercise the same bug as the dedicated backslash-cwd test below.
        # Kept as .as_posix() here since these cases aren't testing that.
        "cwd": _REPO_ROOT.as_posix(),
    }


# This repo's own .meta-config/project.yaml has orchestrator.strict: true,
# which is what makes these assertions meaningful without a fixture project.
STRICT_CASES = [
    ("echo test", 2),  # no sentinel -> blocked
    ("#agent-meta:agent=git\ngit status", 0),  # exact sentinel -> exempt
    ("#agent-meta:agent=orchestrator\necho test", 0),  # exact sentinel -> exempt
    ("#agent-meta:agent=gitx\necho test", 2),  # not a recognized agent -> blocked
    (" #agent-meta:agent=git\ngit status", 0),  # surrounding whitespace is stripped before matching, still exempt
    ("echo '#agent-meta:agent=git'\ngit status", 2),  # sentinel must be the actual first line, not embedded text
    ("\n#agent-meta:agent=git\ngit status", 0),  # issue #503: leading blank line before the sentinel, still exempt
    ("\n\n#agent-meta:agent=orchestrator\necho test", 0),  # issue #503: multiple leading blank lines
]


@pytest.mark.parametrize("command,expected_exit_code", STRICT_CASES)
def test_strict_mode_sentinel_exemption(command, expected_exit_code):
    assert _HOOK_PATH.is_file(), f"hook script not found: {_HOOK_PATH}"
    result = _run_hook(_bash_payload(command))
    assert result.returncode == expected_exit_code, (
        f"command={command!r}: expected exit code {expected_exit_code}, "
        f"got {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_strict_mode_blocks_write_unconditionally():
    # Write/Edit have no safe self-declaration channel (a marker line would
    # corrupt file content) -- they must stay blocked even for otherwise
    # "trusted" content, unlike Bash which can carry a sentinel comment.
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": "foo.txt", "content": "#agent-meta:agent=git\nirrelevant"},
        "cwd": _REPO_ROOT.as_posix(),
    }
    result = _run_hook(payload)
    assert result.returncode == 2


def test_strict_mode_survives_backslash_cwd():
    # Regression for the Windows path-interpolation bug: a cwd containing
    # backslashes must not silently disable strict-mode detection.
    payload = _bash_payload("echo test")
    payload["cwd"] = str(_REPO_ROOT)  # native form; backslashes on Windows
    result = _run_hook(payload)
    assert result.returncode == 2, (
        "strict mode should still block an undeclared command with a "
        f"backslash-style cwd\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


# (command, expect_blocked) -- exercised in non-strict mode via a project
# root with no .meta-config/project.yaml, so only the git-mutation regex
# in the non-strict branch is under test, not strict-mode gating.
MUTATION_CASES = [
    ("git commit -m 'x'", True),
    ("git push origin main", True),
    ("git add .", True),
    ("git branch -d old-branch", True),
    ("git branch new-branch", True),
    ("git checkout other-branch", True),
    ("git stash pop", True),
    ("git tag -a v1.0.0 -m 'x'", True),
    ("git status", False),
    ("git branch --show-current", False),
    ("git branch -a", False),
    ("git log --oneline -5", False),
    ("git merge-base main HEAD", False),  # 'merge' substring, not the subcommand
    ("git check-ignore -v some/path", False),  # 'push'-like substring only in the binary name path
    ("gh issue create --title x --body \"mentions git push and git commit\"", False),
    ("git checkout -- some/path", True),  # discards working-tree changes -- a real mutation
    ("git stash list", False),
    # issue #508: statements() didn't split on newlines, so a multi-line
    # read-only command with no &&/;/| between the lines got flattened by
    # shlex.split() into one token stream -- the second line's tokens
    # ('git', 'status', '--short') were misread as positional args to the
    # first line's 'git branch', which looks like a branch-create mutation.
    ("git branch --show-current\ngit status --short", False),
]


def test_strict_block_reason_goes_to_stderr():
    # Issue #396: on exit 2 the harness feeds stderr back to the model and
    # ignores stdout. Emitting the guard message on stdout surfaced a bare
    # "hook error: No stderr output" -- the block worked, the reason was lost.
    result = _run_hook(_bash_payload("echo test"))
    assert result.returncode == 2
    assert "ORCHESTRATOR_GUARD" in result.stderr, (
        f"block reason must be on stderr, got stdout={result.stdout!r} "
        f"stderr={result.stderr!r}"
    )


def test_git_mutation_block_reason_goes_to_stderr(tmp_path):
    # Same contract for the non-strict git-mutation branch (issue #396).
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -m 'x'"},
        "cwd": tmp_path.as_posix(),
    }
    result = _run_hook(payload)
    assert result.returncode == 2
    assert "ORCHESTRATOR_GUARD" in result.stderr, (
        f"block reason must be on stderr, got stdout={result.stdout!r} "
        f"stderr={result.stderr!r}"
    )


@pytest.mark.parametrize("command,expect_blocked", MUTATION_CASES)
def test_git_mutation_regex_precision(command, expect_blocked, tmp_path):
    # Use a cwd with no .meta-config/project.yaml so the hook falls through
    # to the non-strict git-mutation branch under test, independent of this
    # repo's own strict-mode setting.
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": tmp_path.as_posix(),
    }
    result = _run_hook(payload)
    expected = 2 if expect_blocked else 0
    assert result.returncode == expected, (
        f"command={command!r}: expected exit {expected}, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


# --- issue #516: capability-scoped sentinel elevation -------------------

def test_git_sentinel_still_allows_plain_mutation(tmp_path):
    """Valid `git` sentinel exempts plain git mutations (existing behavior)."""
    command = "#agent-meta:agent=git\ngit add -A && git commit -m 'x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, f"stderr={result.stderr}"


def test_orchestrator_sentinel_no_longer_bypasses_git_block(tmp_path):
    """#516: `orchestrator` sentinel must NOT bypass the git-mutation block."""
    command = "#agent-meta:agent=orchestrator\ngit commit -m 'x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "git" in result.stderr.lower()


@pytest.mark.parametrize("command", [
    "#agent-meta:agent=git\ngit push --force origin main",
    "#agent-meta:agent=git\n git push -f origin main",
    "#agent-meta:agent=git\ngit reset --hard HEAD~1",
    "#agent-meta:agent=git\ngit clean -fd",
    "#agent-meta:agent=git\ngit stash drop stash@{0}",
    "#agent-meta:agent=git\ngit stash clear",
    "#agent-meta:agent=git\ngit filter-branch --tree-filter 'x' HEAD",
])
def test_destructive_ops_blocked_even_with_git_sentinel(command, tmp_path):
    """#516: destructive ops require user approval even with valid sentinel."""
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "user approval" in result.stderr


def test_non_git_agent_cannot_use_fake_sentinel_for_destructive(tmp_path):
    """The exact incident from #516: fake `general-purpose` elevation path is
    irrelevant — even claiming git, destructive ops stay blocked."""
    command = "#agent-meta:agent=git\ngit stash pop"
    # stash pop is NOT in the destructive list (only drop/clear); plain pop
    # with valid sentinel stays allowed — but a FAKE claim of an unknown
    # role gets no exemption at all:
    fake = "#agent-meta:agent=general-purpose\ngit commit -m 'x'"
    r2 = _run_hook({**_bash_payload(fake), "cwd": tmp_path.as_posix()})
    assert r2.returncode == 2


def test_elevation_attempts_are_audited(tmp_path):
    """Every sentinel elevation appends to .guard-audit.log (#516)."""
    audit_file = tmp_path / ".claude" / "hooks" / ".guard-audit.log"
    command = "#agent-meta:agent=git\ngit status"
    _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert audit_file.exists(), "audit log not created"
    content = audit_file.read_text(encoding="utf-8")
    assert "role=git" in content
    assert "git status" in content
