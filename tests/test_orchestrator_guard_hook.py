"""Regression tests for hooks/1-generic/orchestrator-guard.sh.

Background: the hook used to read an `agent_name` field from the
PreToolUse JSON payload to exempt the `git`/`orchestrator` agents from the
strict-mode block. That field does not exist in any provider's real
PreToolUse payload (Claude Code's documented payload at the time was
`{session_id, transcript_path, hook_event_name, tool_name, tool_input}`
only -- see docs/guides/features/hooks.md) -- the exemption never
triggered (agent-meta issue #390).

v2.0.0 replaced this with a self-declared identity: an authorized Bash
command's first line must be the exact sentinel `#agent-meta:agent=<name>`.
Write/Edit had no safe equivalent channel (a marker would corrupt file
content) and were therefore never exempted under strict mode -- which
turned out to make delegated implementation infeasible under strict mode
entirely (issue #683): a properly orchestrator-dispatched implementer
subagent needs Write/Edit to do its job, and got blocked identically to
the main thread.

Issue #683's fix uses Claude Code's `agent_id` common input field instead
(added to the PreToolUse payload since #390 was fixed, harness-set, "present
only when the hook fires inside a subagent call" --
https://code.claude.com/docs/en/hooks.md): the strict-mode main-chat block
now applies only when `agent_id` is absent. The sentinel convention still
exists for ROLE identification (git vs. orchestrator) on the git-mutation
gate, which `agent_id` alone doesn't provide.

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
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOK_PATH = _REPO_ROOT / "hooks" / "1-generic" / "orchestrator-guard.sh"
_IMPL_PATH = _REPO_ROOT / "hooks" / "1-generic" / "orchestrator-guard-impl.sh"

# The hook reads project.yaml and appends to <root>/.claude/hooks/.guard-audit.log
# relative to the project it runs in. Running it against the real checkout
# polluted that gitignored log with test lines on every local run (#945);
# every test now runs against a throw-away copy of the real project config.
# The root comes from the shared `hook_project_root` fixture (tests/conftest.py)
# and is bound below, so importing this module has no filesystem side effect.
# `Optional[Path]` rather than `Path | None`: this module has no
# `from __future__ import annotations` and must stay Python 3.9 compatible.
_PROJECT_ROOT: Optional[Path] = None

# On Windows, plain ["bash", ...] can resolve to System32\bash.exe (the WSL
# launcher) instead of Git Bash, depending on CreateProcess search order
# (System32 is searched before PATH). The WSL launcher mishandles this
# script's CRLF line endings. Resolve the real Git Bash explicitly via PATH
# to get deterministic behavior across environments.
_BASH = shutil.which("bash") or "bash"

pytestmark = pytest.mark.skipif(
    sys.platform not in ("win32", "linux", "darwin"), reason="requires bash"
)


@pytest.fixture(scope="module", autouse=True)
def _bind_project_root(hook_project_root):
    """Bind the shared project fixture to the module global for this module."""
    global _PROJECT_ROOT
    _PROJECT_ROOT = hook_project_root
    yield
    _PROJECT_ROOT = None


def _clean_env() -> dict:
    # SR-B-11: the hook prefers $CLAUDE_PROJECT_DIR over the payload cwd. A
    # value inherited from a surrounding Claude Code session would silently
    # retarget every tmp_path fixture at that project (and its audit log),
    # so tests never inherit it -- tests that need it set it explicitly.
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    return env


def _run_hook(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(_PROJECT_ROOT),
        env=_clean_env(),
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
        "cwd": _PROJECT_ROOT.as_posix(),
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


def test_strict_mode_blocks_write_for_main_thread():
    # A main-thread Write call (no agent_id -- issue #683) has no safe
    # self-declaration channel (a marker line would corrupt file content)
    # -- it must stay blocked even for otherwise "trusted" content, unlike
    # Bash which can carry a sentinel comment.
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": "foo.txt", "content": "#agent-meta:agent=git\nirrelevant"},
        "cwd": _PROJECT_ROOT.as_posix(),
    }
    result = _run_hook(payload)
    assert result.returncode == 2


def test_strict_mode_allows_write_for_dispatched_subagent():
    # Issue #683: a dispatched subagent's Write call carries a non-empty
    # agent_id (Claude Code common input field, harness-set -- see
    # https://code.claude.com/docs/en/hooks.md). Before this fix, strict
    # mode blocked this unconditionally for every caller, making delegated
    # implementation (Subagent-Driven Development, Executing Plans, etc.)
    # infeasible the moment a task needed to write a file.
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": "foo.txt", "content": "irrelevant"},
        "cwd": _PROJECT_ROOT.as_posix(),
        "agent_id": "subagent-123",
    }
    result = _run_hook(payload)
    assert result.returncode == 0


def test_strict_mode_allows_edit_for_dispatched_subagent():
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": "foo.txt", "old_string": "a", "new_string": "b"},
        "cwd": _PROJECT_ROOT.as_posix(),
        "agent_id": "subagent-123",
    }
    result = _run_hook(payload)
    assert result.returncode == 0


def test_strict_mode_allows_readonly_bash_for_dispatched_subagent():
    # Issue #683 point 2: a dispatched subagent (e.g. agent-meta-manager)
    # was blocked on every Bash call, including plain read-only `git
    # status`, since it had no reason to self-declare via the sentinel.
    payload = _bash_payload("git status")
    payload["agent_id"] = "subagent-123"
    result = _run_hook(payload)
    assert result.returncode == 0


def test_strict_mode_still_blocks_git_mutation_for_dispatched_subagent_without_sentinel():
    # Issue #683 fix must NOT weaken the git-mutation gate: agent_id says
    # "this is some subagent", not "this is the git agent". A dispatched
    # subagent still needs the `git` sentinel to run a git mutation --
    # falls through to the same non-strict-mode mutation check.
    payload = _bash_payload("git commit -m 'x'")
    payload["agent_id"] = "subagent-123"
    result = _run_hook(payload)
    assert result.returncode == 2


def test_strict_mode_dispatched_subagent_with_git_sentinel_can_mutate():
    payload = _bash_payload("#agent-meta:agent=git\ngit commit -m 'x'")
    payload["agent_id"] = "subagent-123"
    result = _run_hook(payload)
    assert result.returncode == 0


def test_strict_mode_survives_backslash_cwd():
    # Regression for the Windows path-interpolation bug: a cwd containing
    # backslashes must not silently disable strict-mode detection.
    payload = _bash_payload("echo test")
    payload["cwd"] = str(_PROJECT_ROOT)  # native form; backslashes on Windows
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


# --- issue #542: newline-aware destructive patterns ----------------------

# Multi-line commands whose LATER lines merely mention push/--force/-f etc.
# as TEXT must not trip the destructive gate (issue #542): the old character
# classes ([^|;&]*, \s+) crossed line boundaries, so a keyword on one line
# and a flag on a later line were read as one destructive git invocation.
# Each case pairs a keyword with its flag on DIFFERENT lines -- same-line
# text mentions remain a documented limitation (best-effort keyword gate).
DESTRUCTIVE_TEXT_FALSE_POSITIVES = [
    "git status\necho \"ready to push\"\necho \"reminder: never use --force on shared branches\"",
    # heredoc-style echo: keyword and flag on separate body lines
    "git status\ncat <<'EOF'\nplan: push the feature branch\nnote: avoid --force on main\nEOF",
    "git status\necho \"will reset soon\"\necho \"then go --hard on cleanup\"",
    "git status\necho \"clean up the mess\"\necho \"flag -f means force\"",
    "git status\ncat <<'EOF'\ntodo: stash\ndrop obsolete patches\nEOF",
    "git status\necho see checkout docs\n-- .",
    "git status\necho restore notes\n.",
]


@pytest.mark.parametrize("command", DESTRUCTIVE_TEXT_FALSE_POSITIVES)
def test_destructive_gate_ignores_text_across_lines(command, tmp_path):
    """#542: destructive patterns must not match across line boundaries."""
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, (
        f"command={command!r}: text mention on a later line must not trip the "
        f"destructive gate\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.parametrize("command", [
    "git push --force origin main",
    # real destructive op as the second line of a multi-line command must
    # still be caught (newline scoping must not weaken detection)
    "git status\ngit push --force origin main",
])
def test_real_force_push_still_blocked_in_multiline(command, tmp_path):
    """#542: detection of real destructive ops survives newline scoping."""
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "user approval" in result.stderr


# --- issue #590: '+'-refspec force push (token-aware) --------------------

@pytest.mark.parametrize("command", [
    "#agent-meta:agent=git\ngit push origin +main",
    "#agent-meta:agent=git\ngit push origin +refs/heads/main:main",
])
def test_plus_refspec_push_is_destructive(command, tmp_path):
    """#590: a leading '+' on the refspec forces a non-fast-forward push, the
    same effect as --force, and must be blocked even with a git sentinel."""
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "user approval" in result.stderr


@pytest.mark.parametrize("command", [
    "#agent-meta:agent=git\ngit push origin main",
    # a ':' refspec without a leading '+' is a normal fast-forward push
    "#agent-meta:agent=git\ngit push origin HEAD:main",
])
def test_plain_push_is_not_destructive(command, tmp_path):
    """#590 counter-check: a push without a leading '+' on the refspec is a
    plain mutation (git sentinel exempts it), not a destructive op."""
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, f"stderr={result.stderr}"


def test_plus_in_non_git_text_arg_not_blocked(tmp_path):
    """#590 counter-check: a '+' inside a non-git command's quoted text
    argument must not be read as a refspec (#602 tokenization)."""
    command = 'gh issue create --title x --body "push origin +main please"'
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, f"stderr={result.stderr}"


# --- issue #591: `-c key=val` consumption + core.pager/editor RCE ---------

def test_config_pager_rce_is_destructive(tmp_path):
    """#591: `-c core.pager=<cmd>` executes an arbitrary shell command; it is
    blocked even with a git sentinel."""
    command = "#agent-meta:agent=git\ngit -c core.pager=touch\\ pwned push"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "user approval" in result.stderr


@pytest.mark.parametrize("command", [
    "#agent-meta:agent=git\ngit -c core.pager= status",
    "#agent-meta:agent=git\ngit -c core.editor= status",
])
def test_config_pager_editor_flagged_even_readonly(command, tmp_path):
    """#591: core.pager / core.editor are inherently suspicious regardless of
    the subcommand (even a read-only `status`)."""
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"


def test_config_value_does_not_hide_subcommand(tmp_path):
    """#591: `-c key=val` must be consumed together with its value token so the
    real subcommand (here `commit`) is still detected as a mutation. Before the
    fix the skip-loop stopped at `user.name=x` and never inspected `commit`."""
    command = "git -c user.name=x commit -m y"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "git" in result.stderr.lower()


def test_config_commit_is_mutation_not_destructive(tmp_path):
    """#591 counter-check: `-c user.name=x commit` is a plain mutation, so a
    valid git sentinel exempts it (it is not destructive)."""
    command = "#agent-meta:agent=git\ngit -c user.name=x commit -m y"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, f"stderr={result.stderr}"


def test_harmless_config_status_not_blocked(tmp_path):
    """#591 counter-check: `-c color.ui=false status` is read-only despite the
    `-c` option and must not be blocked."""
    command = "git -c color.ui=false status"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, f"stderr={result.stderr}"


# --- issue #602: tokenized destructive gate (no raw-string substring) -----

@pytest.mark.parametrize("command", [
    'gh issue create --title x --body "git push --force on main"',
    'echo "reset --hard"',
    'echo "git clean -fd is dangerous"',
    'echo "git filter-branch rewrites history"',
])
def test_git_keywords_in_text_args_not_destructive(command, tmp_path):
    """#602: destructive keywords inside a non-git command's quoted text
    argument must not trip the destructive gate (raw-substring false positive)."""
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, (
        f"command={command!r}: keyword in a text argument must not be treated "
        f"as a git invocation\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_real_force_push_still_blocked(tmp_path):
    """#602 counter-check: a genuine `git push --force` is still destructive."""
    command = "git push --force origin main"
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


# --- issue #551 F1: --config-env / --attr-source subcommand hiding --------

@pytest.mark.parametrize("command", [
    "#agent-meta:agent=git\ngit --config-env x=Y push --force origin main",
    "#agent-meta:agent=git\ngit --attr-source tree push --force origin main",
])
def test_global_opt_value_does_not_hide_force_push(command, tmp_path):
    """#551: --config-env (git>=2.31) / --attr-source (git>=2.40) take a
    separate value token in space-form; if not consumed WITH their value the
    value masks the real 'push' subcommand, and the force push bypasses the
    destructive gate (same class as the original '-c' bug #591). Must stay
    blocked even with a valid git sentinel."""
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "user approval" in result.stderr


@pytest.mark.parametrize("command", [
    "git --config-env x=Y commit -m y",
    "git --attr-source tree commit -m y",
])
def test_global_opt_value_does_not_hide_mutation(command, tmp_path):
    """#551 control: the real 'commit' subcommand behind a --config-env /
    --attr-source value token is still detected as a plain mutation."""
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "git" in result.stderr.lower()


def test_config_env_rce_key_is_destructive(tmp_path):
    """#551: '--config-env core.pager=ENV' carries the same RCE key surface as
    '-c core.pager='; the KEY is extracted from NAME=ENVVAR and flagged
    destructive regardless of the (read-only) subcommand."""
    command = "#agent-meta:agent=git\ngit --config-env core.pager=EVIL status"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "user approval" in result.stderr


# --- issue #551 F2: mirror / delete push destroys remote refs ------------

@pytest.mark.parametrize("command", [
    "#agent-meta:agent=git\ngit push --mirror origin",
    "#agent-meta:agent=git\ngit push --delete origin old-branch",
    "#agent-meta:agent=git\ngit push -d origin old-branch",
])
def test_ref_deleting_push_is_destructive(command, tmp_path):
    """#551: --mirror / --delete / -d delete remote refs (irreversible loss);
    they stay blocked even with a valid git sentinel, like force push (#590)."""
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "user approval" in result.stderr


def test_plain_push_still_not_ref_deleting(tmp_path):
    """#551 F2 counter-check: a normal push (no --mirror/--delete/-d) with a
    git sentinel stays exempt — F2 must not over-block."""
    command = "#agent-meta:agent=git\ngit push origin main"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, f"stderr={result.stderr}"


# --- issue #551 F3: extended RCE config keys -----------------------------

@pytest.mark.parametrize("command", [
    "#agent-meta:agent=git\ngit -c core.sshCommand=EVIL fetch",
    "#agent-meta:agent=git\ngit -c core.hooksPath=/tmp/evil status",
    "#agent-meta:agent=git\ngit -c credential.helper=EVIL status",
    "#agent-meta:agent=git\ngit -c sequence.editor=EVIL status",
    "#agent-meta:agent=git\ngit -c alias.x=EVIL status",
])
def test_extended_rce_config_keys_are_destructive(command, tmp_path):
    """#551: sshCommand / hooksPath / credential.helper / sequence.editor /
    alias.* are RCE vectors and must be flagged destructive regardless of the
    (even read-only) subcommand, matched case-insensitively."""
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "user approval" in result.stderr


# --- issue #595: fail CLOSED (not open) when python3/python is unavailable

def test_fails_closed_without_python(tmp_path):
    """Hiding python3/python from PATH must BLOCK the action (exit 2 with a
    clear stderr reason) instead of silently allowing it through -- the
    opposite of the pre-#595 behavior (`[ -z "$_PY" ] && exit 0`)."""
    minimal_bin = tmp_path / "minimal-bin"
    minimal_bin.mkdir()
    for tool in ("bash", "cat", "dirname", "mkdir", "date", "printf", "tr",
                 "head", "sed", "grep", "basename", "sh", "mv", "wc", "tail",
                 "chmod"):
        found = shutil.which(tool)
        if found:
            (minimal_bin / tool).symlink_to(found)

    payload = _bash_payload("git status")
    payload["cwd"] = tmp_path.as_posix()
    result = subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env={"PATH": str(minimal_bin)},
    )
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "python" in result.stderr.lower()


def test_fails_closed_without_lib_common(tmp_path):
    """A deployment where hooks/lib/hook_common.sh is missing (e.g. a stale
    hooks dir not re-synced since #601) must also fail closed, not silently
    behave as if strict/destructive checks passed."""
    isolated_hook = tmp_path / "orchestrator-guard.sh"
    isolated_hook.write_text(_HOOK_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    # The impl script must be present (issue #630 self-health wrapper split)
    # so this test actually reaches hook_common.sh sourcing inside impl,
    # instead of failing earlier on a missing impl script.
    isolated_impl = tmp_path / "orchestrator-guard-impl.sh"
    isolated_impl.write_text(_IMPL_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    # No lib/ subdirectory next to it -- `source $SCRIPT_DIR/lib/hook_common.sh` must fail.
    payload = _bash_payload("git status")
    payload["cwd"] = tmp_path.as_posix()
    result = subprocess.run(
        [_BASH, str(isolated_hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "hook_common.sh" in result.stderr


# --- issue #630: self-health wrapper carve-out ----------------------------
# orchestrator-guard.sh (thin wrapper) syntax-checks orchestrator-guard-
# impl.sh with `bash -n` before running it. If impl.sh is broken (e.g. an
# unresolved merge-conflict marker), a narrow carve-out allows Write/Edit on
# paths under the wrapper's own directory (so it can be repaired) while
# every other call still fails closed.

def _isolated_wrapper_with_broken_impl(tmp_path) -> Path:
    """Deploy an isolated wrapper+broken-impl pair under <tmp_path>/.claude/hooks/,
    mirroring the real deployment layout (hooks nested under the project root)
    so "under the wrapper's own directory" vs. "elsewhere in the project" is a
    meaningful distinction, not just any sibling of tmp_path itself."""
    hooks_dir = tmp_path / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True)
    isolated_hook = hooks_dir / "orchestrator-guard.sh"
    isolated_hook.write_text(_HOOK_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    broken_impl = hooks_dir / "orchestrator-guard-impl.sh"
    broken_impl.write_text(
        "#!/bin/bash\n<<<<<<< HEAD\necho broken\n=======\necho conflict\n>>>>>>> branch\n",
        encoding="utf-8",
    )
    return isolated_hook


def test_broken_impl_blocks_bash_calls(tmp_path):
    isolated_hook = _isolated_wrapper_with_broken_impl(tmp_path)
    payload = _bash_payload("git status")
    payload["cwd"] = tmp_path.as_posix()
    result = subprocess.run(
        [_BASH, str(isolated_hook)], input=json.dumps(payload),
        capture_output=True, text=True, cwd=str(tmp_path),
    )
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "syntax error" in result.stderr.lower()


def test_broken_impl_allows_edit_under_own_hooks_dir(tmp_path):
    isolated_hook = _isolated_wrapper_with_broken_impl(tmp_path)
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(isolated_hook.parent / "orchestrator-guard-impl.sh")},
        "cwd": tmp_path.as_posix(),
    }
    result = subprocess.run(
        [_BASH, str(isolated_hook)], input=json.dumps(payload),
        capture_output=True, text=True, cwd=str(tmp_path),
    )
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"


def test_broken_impl_still_blocks_edit_outside_hooks_dir(tmp_path):
    isolated_hook = _isolated_wrapper_with_broken_impl(tmp_path)
    # A project file OUTSIDE .claude/hooks/ (sibling of it, not nested under
    # it) -- must stay blocked even while the impl script is broken.
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(tmp_path / "some-file.py")},
        "cwd": tmp_path.as_posix(),
    }
    result = subprocess.run(
        [_BASH, str(isolated_hook)], input=json.dumps(payload),
        capture_output=True, text=True, cwd=str(tmp_path),
    )
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"


def test_missing_impl_fails_closed(tmp_path):
    isolated_hook = tmp_path / "orchestrator-guard.sh"
    isolated_hook.write_text(_HOOK_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    # No orchestrator-guard-impl.sh at all.
    result = subprocess.run(
        [_BASH, str(isolated_hook)], input=json.dumps(_bash_payload("git status")),
        capture_output=True, text=True, cwd=str(tmp_path),
    )
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "impl script" in result.stderr.lower()


def test_valid_impl_still_enforces_normally():
    """Sanity check: with a syntactically valid impl.sh (the real one), the
    wrapper's `bash -n` pre-check passes and normal enforcement is unaffected
    -- guards against the wrapper accidentally short-circuiting the happy
    path."""
    result = _run_hook(_bash_payload("echo test"))
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"


# --- issue #596: audit log redacts credentials + tightens permissions -----

def test_audit_log_redacts_credentials_in_command(tmp_path):
    command = "#agent-meta:agent=git\ngit clone https://user:sup3rSecr3t@example.com/repo.git"
    _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    audit_file = tmp_path / ".claude" / "hooks" / ".guard-audit.log"
    content = audit_file.read_text(encoding="utf-8")
    assert "sup3rSecr3t" not in content
    assert "***:***@" in content


def test_audit_log_permissions_are_owner_only(tmp_path):
    command = "#agent-meta:agent=git\ngit status"
    _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    audit_file = tmp_path / ".claude" / "hooks" / ".guard-audit.log"
    assert oct(audit_file.stat().st_mode)[-3:] == "600"


# --- issue #597: audit log rotation ---------------------------------------

def test_audit_log_rotates_when_over_cap(tmp_path):
    audit_dir = tmp_path / ".claude" / "hooks"
    audit_dir.mkdir(parents=True)
    audit_file = audit_dir / ".guard-audit.log"
    audit_file.write_text(
        "\n".join(f"old-line-{i}" for i in range(1, 2600)) + "\n", encoding="utf-8"
    )
    command = "#agent-meta:agent=git\ngit status"
    result = subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps({**_bash_payload(command), "cwd": tmp_path.as_posix()}),
        capture_output=True,
        text=True,
        cwd=str(_PROJECT_ROOT),
        env=_clean_env(),
    )
    assert result.returncode == 0
    lines = audit_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 1000
    assert "old-line-1\n" not in "\n".join(lines[:1])  # oldest entries gone
    assert "git status" in lines[-1]


# --- issue #694: config-driven auto_commit allowlist sentinel ------------
# `json` is already imported at module scope in this file (line 46) -- reuse it.


def _write_allowlist(tmp_path, mode, eligible_roles):
    (tmp_path / ".meta-config").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".meta-config" / "auto-commit-allowlist.json").write_text(
        json.dumps({
            "version": 1, "mode": mode, "eligible_roles": eligible_roles,
            "triggers": ["task-boundary"], "file_count_threshold": 5,
            "custom_script": None, "secret_scan": True,
        }),
        encoding="utf-8",
    )


def test_allowlisted_role_can_commit_when_auto_commit_enabled(tmp_path):
    _write_allowlist(tmp_path, "auto", ["developer"])
    command = "#agent-meta:agent=developer\ngit add -A && git commit -m 'x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, f"stderr={result.stderr}"


def test_auto_commit_non_allowlisted_role_still_blocked(tmp_path):
    _write_allowlist(tmp_path, "auto", ["developer"])
    command = "#agent-meta:agent=tester\ngit add -A && git commit -m 'x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "git" in result.stderr.lower()


def test_auto_commit_missing_allowlist_file_behaves_like_mode_off(tmp_path):
    # No auto-commit-allowlist.json written at all.
    command = "#agent-meta:agent=developer\ngit add -A && git commit -m 'x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"  # unchanged from today


def test_auto_commit_mode_off_ignores_eligible_roles_list(tmp_path):
    # A stale allowlist from a previous sync where auto_commit was later
    # disabled again must not still authorize anyone.
    _write_allowlist(tmp_path, "off", ["developer"])
    command = "#agent-meta:agent=developer\ngit add -A && git commit -m 'x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"


def test_auto_commit_suggest_mode_ignores_eligible_roles_list(tmp_path):
    # eligible_roles now reflects capability in every mode (bugfix); the
    # guard hook must still withhold authority for 'suggest' -- only
    # 'auto'/'custom' grant it.
    _write_allowlist(tmp_path, "suggest", ["developer"])
    command = "#agent-meta:agent=developer\ngit add -A && git commit -m 'x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"


def test_auto_commit_destructive_gate_still_blocks_an_allowlisted_role(tmp_path):
    # #516's destructive-gate protections are untouched by this feature --
    # same assertion shape as test_destructive_ops_blocked_even_with_git_sentinel
    # above, substituting an allowlisted "developer" sentinel for "git".
    _write_allowlist(tmp_path, "auto", ["developer"])
    command = "#agent-meta:agent=developer\ngit push --force origin main"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "user approval" in result.stderr


def test_auto_commit_allowlisted_role_does_not_gain_orchestrator_sentinel_scope(tmp_path):
    # An allowlisted non-git/orchestrator role must only ever gain the
    # git-mutation-gate exemption (IS_GIT_SENTINEL), never the strict-mode
    # main-chat exemption (IS_ORCH_SENTINEL) -- verified with an isolated
    # fixture project (orchestrator.strict: true) as cwd: with NO agent_id
    # (a main-thread call), a plain non-mutating Bash command from an
    # allowlisted role must still be blocked by the strict-mode gate,
    # exactly like an undeclared caller.
    (tmp_path / ".meta-config").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        "orchestrator:\n  strict: true\n  enabled: true\n", encoding="utf-8",
    )
    _write_allowlist(tmp_path, "auto", ["developer"])
    command = "#agent-meta:agent=developer\necho test"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"


# --- issue #694 follow-up: allowlist sentinel is add/commit-scoped only ---
# The allowlist sentinel authorizes staging + committing, nothing else. Every
# other git mutation in the same command must still be blocked, so an
# auto-committing role can never publish or rewrite refs behind the `git`
# role's back (README: "auto_commit only ever authorizes `git commit`").

@pytest.mark.parametrize("mutation", [
    "git push origin main",
    "git add -A && git commit -m 'x' && git push",
    "git rm foo.txt",
    "git tag v1.0.0",
    "git merge feature",
    "git checkout other-branch",
    "git stash pop",
    # --amend rewrites the previous commit instead of adding one; it can
    # destroy work an earlier (possibly git-role) commit already recorded.
    "git commit --amend -m 'x'",
])
def test_allowlist_sentinel_blocks_non_addcommit_mutations(tmp_path, mutation):
    _write_allowlist(tmp_path, "auto", ["developer"])
    command = f"#agent-meta:agent=developer\n{mutation}"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "git mutations are forbidden" in result.stderr.lower()


def test_git_sentinel_keeps_full_mutation_scope(tmp_path):
    # Narrowing the allowlist sentinel must not narrow the real `git` role.
    _write_allowlist(tmp_path, "auto", ["developer"])
    command = "#agent-meta:agent=git\ngit push origin main"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, f"stderr={result.stderr}"


# --- issue #842: reject a leading UTF-8 BOM in the commit subject ---------
# A BOM (EF BB BF) in front of the subject breaks Conventional-Commit
# tooling and line-based hooks: the subject must start at byte 0 with the
# type. The gate lives between the tokenizer and the strict-mode sentinel
# exit, so neither a `git` sentinel nor strict mode can bypass it. Only a
# BOM at the very START of a -m/--message value or -F/--file file counts;
# a BOM used as a zero-width space mid-subject must not false-positive.

_BOM = "\ufeff"


def test_leading_bom_via_message_flag_blocked_with_git_sentinel(tmp_path):
    command = f"#agent-meta:agent=git\ngit commit -m '{_BOM}feat: x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "BOM" in result.stderr


def test_leading_bom_blocked_before_strict_mode_sentinel(tmp_path):
    # Issue #842: the BOM gate must fire even when the caller would otherwise
    # take the strict-mode sentinel's `exit 0` shortcut (cwd = repo root with
    # orchestrator.strict: true, valid `git` sentinel). If the gate were
    # placed after that early exit this command would exit 0 instead.
    command = f"#agent-meta:agent=git\ngit commit -m '{_BOM}feat: x'"
    result = _run_hook({**_bash_payload(command), "cwd": _PROJECT_ROOT.as_posix()})
    assert result.returncode == 2, (
        f"BOM must be rejected before the strict-mode sentinel exit 0\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "BOM" in result.stderr


def test_leading_bom_via_message_equals_form_blocked(tmp_path):
    command = f"#agent-meta:agent=git\ngit commit --message='{_BOM}feat: x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "BOM" in result.stderr


def test_leading_bom_not_blocked_for_non_bash_tool(tmp_path):
    # Defense-in-depth: the gate is scoped to Bash, like every other gate.
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": "foo.txt", "old_string": "a", "new_string": "b"},
        "cwd": tmp_path.as_posix(),
    }
    result = _run_hook(payload)
    assert result.returncode == 0, f"stderr={result.stderr}"


def test_leading_bom_via_file_flag_blocked(tmp_path):
    msg = tmp_path / "msg.txt"
    msg.write_bytes(b"\xef\xbb\xbffeat: x\n")
    command = f"#agent-meta:agent=git\ngit commit -F {msg.as_posix()}"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "BOM" in result.stderr


def test_leading_bom_via_relative_file_flag_resolved_against_cwd(tmp_path):
    # -F with a relative path is resolved against the payload cwd
    # (PROJECT_ROOT), not the process cwd.
    (tmp_path / "msg.txt").write_bytes(b"\xef\xbb\xbffeat: x\n")
    command = "#agent-meta:agent=git\ngit commit -F msg.txt"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "BOM" in result.stderr


def test_leading_bom_via_file_equals_form_blocked(tmp_path):
    msg = tmp_path / "msg.txt"
    msg.write_bytes(b"\xef\xbb\xbffeat: x\n")
    command = f"#agent-meta:agent=git\ngit commit --file={msg.as_posix()}"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "BOM" in result.stderr


def test_clean_message_not_blocked(tmp_path):
    command = "#agent-meta:agent=git\ngit commit -m 'feat: x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, f"stderr={result.stderr}"
    assert result.stderr == ""


def test_clean_file_not_blocked(tmp_path):
    msg = tmp_path / "msg.txt"
    msg.write_bytes(b"feat: x\n")
    command = f"#agent-meta:agent=git\ngit commit -F {msg.as_posix()}"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, f"stderr={result.stderr}"


def test_missing_file_flag_not_bom_blocked(tmp_path):
    # A missing -F file has no bytes to inspect -> no BOM signal; the guard
    # must leave it to git (which will report the missing file itself).
    missing = tmp_path / "does-not-exist.txt"
    command = f"#agent-meta:agent=git\ngit commit -F {missing.as_posix()}"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, f"stderr={result.stderr}"


def test_bom_not_at_message_start_not_blocked(tmp_path):
    # A BOM used as a zero-width space inside the subject/body is not a
    # leading BOM and must not false-positive.
    command = f"#agent-meta:agent=git\ngit commit -m 'feat: mention {_BOM} here'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, (
        f"a BOM mid-message must not be rejected\nstderr: {result.stderr}"
    )


def test_bom_in_non_commit_subcommand_not_blocked(tmp_path):
    # Only `commit` can carry a message/BOM; a BOM-shaped argument to another
    # subcommand must not trip the gate.
    command = f"#agent-meta:agent=git\ngit branch {_BOM}weird-name"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, f"stderr={result.stderr}"


# --- issue #842 follow-ups: ANSI-C quoting (G1) + short-option clusters (G2)


def test_leading_bom_via_ansi_c_unicode_escape_blocked(tmp_path):
    # G1: `git commit -m $'\uFEFFfeat: x'` -- the shell expands ANSI-C quoting
    # to a real BOM BEFORE git sees it, so git receives a BOM subject. shlex
    # strips the single quotes and leaves a leading '$' + the escape text, so
    # the raw prefix check alone missed it.
    command = "#agent-meta:agent=git\ngit commit -m $'\\uFEFFfeat: x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "BOM" in result.stderr


def test_leading_bom_via_ansi_c_hex_escape_blocked(tmp_path):
    # G1: the byte-explicit ANSI-C spelling $'\xEF\xBB\xBF...'.
    command = "#agent-meta:agent=git\ngit commit -m $'\\xEF\\xBB\\xBFfeat: x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "BOM" in result.stderr


def test_leading_bom_via_short_option_cluster_blocked(tmp_path):
    # G2: `git commit -am '<BOM>feat: x'` -- the message option is the last
    # character of a combined short-option cluster, the value is the next token.
    command = f"#agent-meta:agent=git\ngit commit -am '{_BOM}feat: x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "BOM" in result.stderr


def test_leading_bom_via_short_option_cluster_ansi_c_blocked(tmp_path):
    # G1 + G2 combined: cluster option with an ANSI-C quoted BOM value.
    command = "#agent-meta:agent=git\ngit commit -am $'\\uFEFFfeat: x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "BOM" in result.stderr


def test_leading_bom_via_glued_short_message_blocked(tmp_path):
    # G2: value glued to the short option (`-m<msg>`).
    command = f"#agent-meta:agent=git\ngit commit -m'{_BOM}feat: x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "BOM" in result.stderr


def test_leading_bom_via_glued_cluster_message_blocked(tmp_path):
    # G2: value glued to the cluster's trailing message option (`-am<msg>`).
    command = f"#agent-meta:agent=git\ngit commit -am'{_BOM}feat: x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "BOM" in result.stderr


def test_leading_bom_via_cluster_file_option_blocked(tmp_path):
    # G2 for -F: `git commit -aF <file>` and glued `-aF<file>`.
    msg = tmp_path / "msg.txt"
    msg.write_bytes(b"\xef\xbb\xbffeat: x\n")
    command = f"#agent-meta:agent=git\ngit commit -aF {msg.as_posix()}"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "BOM" in result.stderr
    glued = f"#agent-meta:agent=git\ngit commit -aF{msg.as_posix()}"
    result = _run_hook({**_bash_payload(glued), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"


def test_dollar_prefixed_message_is_not_false_positive(tmp_path):
    # Guard (G1): a normal message that merely STARTS with a literal '$' has no
    # backslash after it, so it is not ANSI-C quoting and must be allowed.
    for msg in ("$5 cost", "$HOME/x"):
        command = f"#agent-meta:agent=git\ngit commit -m '{msg}'"
        result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
        assert result.returncode == 0, (
            f"msg={msg!r} must not be treated as a leading BOM; stderr={result.stderr}"
        )


def test_ansi_c_quoted_message_without_bom_is_not_false_positive(tmp_path):
    # Guard (G1): ANSI-C quoting that does NOT start with a BOM must pass.
    command = "#agent-meta:agent=git\ngit commit -m $'feat: x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, f"stderr={result.stderr}"


# --- issue #694 follow-up: bare '&' is a statement separator -------------
# statements() used to split only on '&&'/'||'/';'/'|'/newline, so
# "git add x & git push" was ONE statement -- and since the token loop
# breaks after the first `git` it finds per statement, the second
# invocation was never classified at all. That silently bypassed both the
# mutation gate and the add/commit-only narrowing of the allowlist
# sentinel above.


def test_bare_ampersand_second_git_is_still_classified(tmp_path):
    # Without any sentinel this used to exit 0 (full bypass of the mutation
    # gate) because `git push` hid behind the leading `git status`.
    command = "git status & git push origin main"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"


def test_bare_ampersand_addcommit_still_allowed_for_allowlisted_role(tmp_path):
    # Both halves are add/commit, so the command stays inside the sentinel's
    # narrow scope -- splitting on '&' must not over-block this.
    _write_allowlist(tmp_path, "auto", ["developer"])
    command = "#agent-meta:agent=developer\ngit add -A & git commit -m 'x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, f"stderr={result.stderr}"


def test_bare_ampersand_cannot_smuggle_push_past_allowlist_sentinel(tmp_path):
    # The actual bypass: `git push` after a bare '&' escaped the add/commit
    # narrowing that test_allowlist_sentinel_blocks_non_addcommit_mutations
    # enforces for the '&&' form.
    _write_allowlist(tmp_path, "auto", ["developer"])
    command = "#agent-meta:agent=developer\ngit add -A & git push origin main"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "git mutations are forbidden" in result.stderr.lower()


def test_double_ampersand_addcommit_unchanged_by_bare_ampersand_split(tmp_path):
    # Regression guard for the alternation order: '&&' must keep matching as
    # one operator. If '&' were listed first it would split '&&' into two
    # empty statements and this previously-passing case would change behavior.
    _write_allowlist(tmp_path, "auto", ["developer"])
    command = "#agent-meta:agent=developer\ngit add -A && git commit -m 'x'"
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, f"stderr={result.stderr}"


# --- issue #809: destructive gate covers filesystem destruction ----------
# Before #809 the destructive gate only classified `git <subcommand>`
# invocations, so `rm -rf /` and `rm -rf /etc` passed through with rc=0.
# These tests drive the real hook subprocess in a NON-strict cwd (no
# project.yaml) so only the destructive/mutation gates decide the exit code,
# matching the harness the audit used.

FS_DESTRUCTIVE_CASES = [
    "rm -rf /",
    "rm -rf /etc",
    "rm -rf /*",
    "rm -rf /usr",
    "rm -rf ~",
    "rm -rf $HOME",
    "rm -rf ${HOME}",
    "rm -rf .",
    "rm -rf ..",
    "rm -rf *",
    "sudo rm -rf /etc",
    "rm -r /",
    "echo hi && rm -rf /etc",
]


@pytest.mark.parametrize("command", FS_DESTRUCTIVE_CASES)
def test_fs_destruction_blocked_without_sentinel(command, tmp_path):
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, (
        f"command={command!r} must be blocked\nstderr={result.stderr}"
    )
    assert "user approval" in result.stderr


@pytest.mark.parametrize("command", [
    "#agent-meta:agent=git\nrm -rf /etc",
    "#agent-meta:agent=orchestrator\nrm -rf /etc",
])
def test_fs_destruction_blocked_even_with_sentinel(command, tmp_path):
    # The destructive gate is capability-independent: no sentinel bypasses it.
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "user approval" in result.stderr


FS_BENIGN_CASES = [
    "rm -rf .tmp/build",
    "rm -rf .tmp/foo/bar",
    "rm -rf node_modules",
    "rm -rf ./dist",
    "rm -rf /tmp/my-scratch",
    "rm -rf /var/tmp/app-cache",
    "rm -rf ~/project/build",
    "rm file.txt",
]


@pytest.mark.parametrize("command", FS_BENIGN_CASES)
def test_benign_rm_not_blocked(command, tmp_path):
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, (
        f"command={command!r} must stay allowed\nstderr={result.stderr}"
    )


@pytest.mark.parametrize("command", [
    ":(){ :|:& };:",
    "bomb(){ bomb|bomb& };bomb",
])
def test_fork_bomb_blocked(command, tmp_path):
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "user approval" in result.stderr


@pytest.mark.parametrize("command", [
    "echo ':(){ :|:& };:'",
    'echo "bomb(){ bomb|bomb& };bomb"',
])
def test_fork_bomb_text_literal_not_blocked(command, tmp_path):
    # Same quoted-text scoping as the git gates (#602): a fork-bomb-shaped
    # STRING argument must not trip the gate.
    result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
    assert result.returncode == 0, f"stderr={result.stderr}"


# --- SR-B-10: strict-mode detection fails closed on unreadable config ------
# Each case builds a throwaway tmp_path project (never the real repo) so no
# test here writes into the real .claude/hooks/.guard-audit.log.


def _strict_project(tmp_path, project_yaml: str):
    (tmp_path / ".meta-config").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".meta-config" / "project.yaml").write_text(project_yaml, encoding="utf-8")


def _run_hook_in(tmp_path, payload: dict, hide_yaml: bool) -> subprocess.CompletedProcess:
    env = _clean_env()
    if hide_yaml:
        # A fake yaml.py earlier on sys.path makes `import yaml` raise
        # ImportError -- simulates a hook interpreter without PyYAML.
        shadow = tmp_path / "no-yaml"
        shadow.mkdir(exist_ok=True)
        (shadow / "yaml.py").write_text("raise ImportError('PyYAML hidden by test')\n", encoding="utf-8")
        env["PYTHONPATH"] = str(shadow)
    return subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps({**payload, "cwd": tmp_path.as_posix()}),
        capture_output=True, text=True, cwd=str(tmp_path), env=env,
    )


_MAIN_THREAD_WRITE = {"tool_name": "Write", "tool_input": {"file_path": "foo.txt", "content": "x"}}


@pytest.mark.parametrize("project_yaml", [
    "orchestrator:\n  mode: strict\n",
    "orchestrator:\n  enabled: true\n  strict: true\n",
    "orchestrator:\n  provider-overrides:\n    claude:\n      mode: strict\n",
])
def test_strict_mode_blocks_without_pyyaml(tmp_path, project_yaml):
    _strict_project(tmp_path, project_yaml)
    result = _run_hook_in(tmp_path, _MAIN_THREAD_WRITE, hide_yaml=True)
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "STRICT MODE" in result.stderr
    assert "PyYAML" in result.stderr


@pytest.mark.parametrize("project_yaml", [
    "orchestrator:\n  mode: default\n",
    "orchestrator:\n  enabled: true\n  strict: false\n",
    "project:\n  name: x\n",
])
def test_non_strict_project_without_pyyaml_allows(tmp_path, project_yaml):
    _strict_project(tmp_path, project_yaml)
    result = _run_hook_in(tmp_path, _MAIN_THREAD_WRITE, hide_yaml=True)
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"


def test_ambiguous_orchestrator_block_without_pyyaml_fails_closed(tmp_path):
    # Flow-style mapping can't be judged by a line scan -> conservative block.
    _strict_project(tmp_path, "orchestrator: {mode: strict}\n")
    result = _run_hook_in(tmp_path, _MAIN_THREAD_WRITE, hide_yaml=True)
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"


def test_malformed_strict_config_fails_closed(tmp_path):
    pytest.importorskip("yaml")
    _strict_project(tmp_path, "orchestrator:\n  mode: strict\n  bad: [unclosed\n")
    result = _run_hook_in(tmp_path, _MAIN_THREAD_WRITE, hide_yaml=False)
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "STRICT MODE" in result.stderr


def test_strict_project_with_pyyaml_still_blocks(tmp_path):
    pytest.importorskip("yaml")
    _strict_project(tmp_path, "orchestrator:\n  mode: strict\n")
    result = _run_hook_in(tmp_path, _MAIN_THREAD_WRITE, hide_yaml=False)
    assert result.returncode == 2
    assert "PyYAML" not in result.stderr


def test_non_strict_project_with_pyyaml_allows(tmp_path):
    pytest.importorskip("yaml")
    _strict_project(tmp_path, "orchestrator:\n  enabled: true\n  strict: false\n")
    result = _run_hook_in(tmp_path, _MAIN_THREAD_WRITE, hide_yaml=False)
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"


# --- SR-B-08: wrapper maps impl exit status to {0, 2} -----------------------
# Claude Code only blocks on exit 2; any other non-zero status is a
# non-blocking error and the tool call proceeds. An impl crash (unbound
# variable rc 1, SIGKILL 137, SIGPIPE 141) must therefore fail CLOSED.

def _wrapper_with_stub_impl(tmp_path, impl_body: str) -> Path:
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    wrapper = hooks_dir / "orchestrator-guard.sh"
    wrapper.write_text(_HOOK_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    (hooks_dir / "orchestrator-guard-impl.sh").write_text(
        "#!/bin/bash\ncat >/dev/null\n" + impl_body + "\n", encoding="utf-8",
    )
    return wrapper


@pytest.mark.parametrize("impl_body,crash_rc", [
    ("set -u\necho \"$UNBOUND_VAR_SR_B_08\"", 1),
    ("kill -KILL $$", 137),
    ("kill -PIPE $$", 141),
    ("exit 3", 3),
])
def test_wrapper_fails_closed_on_impl_crash(tmp_path, impl_body, crash_rc):
    wrapper = _wrapper_with_stub_impl(tmp_path, impl_body)
    result = subprocess.run(
        [_BASH, str(wrapper)], input=json.dumps(_bash_payload("echo hi")),
        capture_output=True, text=True, cwd=str(tmp_path), env=_clean_env(),
    )
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert f"impl crashed rc={crash_rc}" in result.stderr
    assert "failing closed" in result.stderr


@pytest.mark.parametrize("impl_rc", [0, 2])
def test_wrapper_passes_through_allow_and_block(tmp_path, impl_rc):
    wrapper = _wrapper_with_stub_impl(tmp_path, f"exit {impl_rc}")
    result = subprocess.run(
        [_BASH, str(wrapper)], input=json.dumps(_bash_payload("echo hi")),
        capture_output=True, text=True, cwd=str(tmp_path), env=_clean_env(),
    )
    assert result.returncode == impl_rc, f"stderr={result.stderr!r}"
    assert "impl crashed" not in result.stderr


# --- SR-B-11: project root resolution (walk-up / $CLAUDE_PROJECT_DIR) --------

def _strict_tree(tmp_path) -> Path:
    proj = tmp_path / "proj"
    sub = proj / "sub" / "dir"
    sub.mkdir(parents=True)
    _strict_project(proj, "orchestrator:\n  mode: strict\n")
    return proj


def _run_with(payload: dict, cwd: Path, extra_env=None) -> subprocess.CompletedProcess:
    env = _clean_env()
    env.update(extra_env or {})
    return subprocess.run(
        [_BASH, str(_HOOK_PATH)], input=json.dumps({**payload, "cwd": cwd.as_posix()}),
        capture_output=True, text=True, cwd=str(cwd), env=env,
    )


def test_strict_mode_found_from_subdirectory(tmp_path):
    proj = _strict_tree(tmp_path)
    result = _run_with(_MAIN_THREAD_WRITE, proj / "sub" / "dir")
    assert result.returncode == 2, f"stderr={result.stderr!r}"
    assert "STRICT MODE" in result.stderr


def test_strict_mode_found_via_claude_project_dir(tmp_path):
    proj = _strict_tree(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    result = _run_with(_MAIN_THREAD_WRITE, elsewhere, {"CLAUDE_PROJECT_DIR": str(proj)})
    assert result.returncode == 2, f"stderr={result.stderr!r}"


@pytest.mark.parametrize("bogus", ["", "/nonexistent/sr-b-11", "<no-meta>"])
def test_unusable_claude_project_dir_falls_back_to_walk_up(tmp_path, bogus):
    proj = _strict_tree(tmp_path)
    if bogus == "<no-meta>":
        bogus = str(tmp_path)  # exists, but has no .meta-config/
    result = _run_with(_MAIN_THREAD_WRITE, proj / "sub", {"CLAUDE_PROJECT_DIR": bogus})
    assert result.returncode == 2, f"stderr={result.stderr!r}"


def test_non_project_cwd_without_meta_config_stays_non_strict(tmp_path):
    plain = tmp_path / "plain" / "a"
    plain.mkdir(parents=True)
    result = _run_with(_MAIN_THREAD_WRITE, plain)
    assert result.returncode == 0, f"stderr={result.stderr!r}"


def test_allowlist_found_from_subdirectory(tmp_path):
    proj = tmp_path / "proj"
    (proj / "src").mkdir(parents=True)
    _write_allowlist(proj, "auto", ["developer"])
    payload = _bash_payload("#agent-meta:agent=developer\ngit commit -m 'x'")
    result = _run_with(payload, proj / "src")
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    # Audit line lands in the project root, not in the subdirectory.
    assert (proj / ".claude" / "hooks" / ".guard-audit.log").is_file()
    assert not (proj / "src" / ".claude").exists()


def test_relative_bom_file_still_resolved_against_cwd(tmp_path):
    proj = tmp_path / "proj"
    sub = proj / "sub"
    sub.mkdir(parents=True)
    (proj / ".meta-config").mkdir()
    (sub / "msg.txt").write_bytes(b"\xef\xbb\xbffeat: x\n")
    payload = _bash_payload("#agent-meta:agent=git\ngit commit -F msg.txt")
    result = _run_with(payload, sub)
    assert result.returncode == 2, f"stderr={result.stderr!r}"
    assert "BOM" in result.stderr


# --- SR-B-12: ref-loss commands are destructive (even with git sentinel) -----

SR_B_12_DESTRUCTIVE = [
    "git push origin :main",
    "git push origin +:main",
    "git push origin :refs/heads/x",
    "git push --prune origin",
    "git checkout .",
    "git checkout -f main",
    "git checkout --force main",
    "git update-ref -d refs/heads/main",
    "git update-ref --delete refs/heads/main",
    "git reflog expire --expire=now --all",
    "git reflog delete HEAD@{1}",
    "git stash -q drop",
    "git stash --quiet clear",
    # switch is checkout's modern alias -- same force semantics.
    "git switch -f main",
    "git switch --discard-changes main",
]


@pytest.mark.parametrize("sentinel", ["", "#agent-meta:agent=git\n"])
@pytest.mark.parametrize("command", SR_B_12_DESTRUCTIVE)
def test_ref_loss_commands_are_destructive(tmp_path, command, sentinel):
    result = _run_with(_bash_payload(sentinel + command), tmp_path)
    assert result.returncode == 2, f"stderr={result.stderr!r}"
    assert "user approval" in result.stderr


# --- SR-B-13: history-changing subcommands are mutations ---------------------

SR_B_13_MUTATIONS = [
    "git pull",
    "git switch main",
    "git cherry-pick abc123",
    "git revert HEAD",
    "git am x.patch",
    "git update-ref refs/heads/x HEAD",
    "git worktree add ../wt main",
    "git stash -q pop",
]


@pytest.mark.parametrize("command", SR_B_13_MUTATIONS)
def test_new_mutations_blocked_without_sentinel(tmp_path, command):
    result = _run_with(_bash_payload(command), tmp_path)
    assert result.returncode == 2, f"stderr={result.stderr!r}"
    assert "Direct git mutations" in result.stderr


@pytest.mark.parametrize("command", SR_B_13_MUTATIONS)
def test_new_mutations_allowed_with_git_sentinel(tmp_path, command):
    result = _run_with(_bash_payload("#agent-meta:agent=git\n" + command), tmp_path)
    assert result.returncode == 0, f"stderr={result.stderr!r}"


@pytest.mark.parametrize("command", SR_B_13_MUTATIONS)
def test_new_mutations_outside_allowlist_scope(tmp_path, command):
    _write_allowlist(tmp_path, "auto", ["developer"])
    result = _run_with(_bash_payload("#agent-meta:agent=developer\n" + command), tmp_path)
    assert result.returncode == 2, f"stderr={result.stderr!r}"


# Negative controls: must stay allowed WITHOUT any sentinel (read-only) ...
SR_B_READ_ONLY = [
    "git status",
    "git log --oneline -5",
    "git diff HEAD",
    "git show HEAD",
    "git branch --show-current",
    "git remote -v",
    "git ls-remote origin",
    "git fetch origin",
    "git reflog",
    "git reflog show --all",
    "git stash list",
    "git worktree list",
]
# ... and must stay allowed WITH the git sentinel (not destructive).
SR_B_BENIGN_WITH_SENTINEL = SR_B_READ_ONLY + [
    "git checkout -b x",
    "git checkout main",
    "git checkout -- path/file.txt",
    "git stash",
    "git stash push -m drop",
    "git stash pop",
    "git push origin main:main",
    "git push origin HEAD:main",
    "git push --tags",
    "git push origin :",
    "git update-ref refs/heads/x HEAD",
    "git pull --rebase",
    "git switch -c feature",
    "git stash -- drop",  # pathspec 'drop' after '--', a stash push
    "git worktree add ../wt main",
]


@pytest.mark.parametrize("command", SR_B_READ_ONLY)
def test_read_only_git_stays_allowed(tmp_path, command):
    result = _run_with(_bash_payload(command), tmp_path)
    assert result.returncode == 0, f"stderr={result.stderr!r}"


@pytest.mark.parametrize("command", SR_B_BENIGN_WITH_SENTINEL)
def test_benign_git_with_sentinel_stays_allowed(tmp_path, command):
    result = _run_with(_bash_payload("#agent-meta:agent=git\n" + command), tmp_path)
    assert result.returncode == 0, f"stderr={result.stderr!r}"


@pytest.mark.parametrize("raw", ["not json", '{"tool_name": "Bash", ', "[1, 2"])
def test_unparseable_payload_fails_closed(raw):
    """SR-B-09: a non-empty payload that is not valid JSON must block (exit 2)."""
    result = subprocess.run(
        [_BASH, str(_HOOK_PATH)], input=raw, capture_output=True, text=True,
        cwd=str(_PROJECT_ROOT), env=_clean_env(),
    )
    assert result.returncode == 2, result.stderr
    assert "not valid JSON" in result.stderr


def test_empty_payload_fails_closed():
    """Review finding M2: an empty payload is not a documented PreToolUse
    event -- it used to exit 0 here ("no tool name -> allow"). The guard
    cannot evaluate a call whose payload never arrived, so it fails closed
    like repo-containment-impl.sh always did.

    CONFLICT NOTE: this replaces the former test_empty_payload_is_still_a_noop
    (asserted returncode 0), which pinned exactly the fail-open M2 names.
    """
    result = subprocess.run(
        [_BASH, str(_HOOK_PATH)], input="", capture_output=True, text=True,
        cwd=str(_PROJECT_ROOT), env=_clean_env(),
    )
    assert result.returncode == 2, result.stderr
    assert "empty PreToolUse payload" in result.stderr


# --- review finding M2: payload/tool_name fail-closed ----------------------

def _garbage_python_env(tmp_path) -> dict:
    """Environment whose `python3` is a shim that EXITS 0 printing junk --
    the M2 fail-open trigger. The rest of PATH stays intact so bash/cat/
    dirname/... still work inside the hook."""
    shim_dir = tmp_path / "garbage-python"
    shim_dir.mkdir()
    shim = shim_dir / "python3"
    shim.write_text("#!/bin/sh\necho garbage\n", encoding="utf-8")
    shim.chmod(0o755)
    env = _clean_env()
    env["PATH"] = f"{shim_dir}{os.pathsep}{env.get('PATH', '')}"
    return env


def _tool_payload(tool, **extra) -> dict:
    payload = {"tool_name": tool, "tool_input": {}, "cwd": _PROJECT_ROOT.as_posix()}
    payload.update(extra)
    return payload


def test_garbage_python_interpreter_fails_closed(tmp_path):
    """M2: `python3` on PATH that exits 0 printing junk made tool_name
    'garbage', which matched `*) exit 0` -- the destructive git push below
    went through. The shared hook_json_usable() gate must block it instead."""
    env = _garbage_python_env(tmp_path)
    payload = _bash_payload("git push --force origin main")
    payload["cwd"] = _PROJECT_ROOT.as_posix()
    result = subprocess.run(
        [_BASH, str(_HOOK_PATH)], input=json.dumps(payload),
        capture_output=True, text=True, cwd=str(_PROJECT_ROOT), env=env,
    )
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "does not behave like a Python interpreter" in result.stderr


@pytest.mark.parametrize("tool", ["Frobnicate", "bash", "run_command"])
def test_unknown_tool_name_fails_closed(tool):
    """M2: an unrecognized tool_name used to hit `*) exit 0` (allow)."""
    result = _run_hook(_tool_payload(tool))
    assert result.returncode == 2, result.stderr
    assert f"unknown tool_name '{tool}'" in result.stderr


@pytest.mark.parametrize("payload", [
    {"tool_input": {}},                    # missing
    {"tool_name": None, "tool_input": {}}, # null
    {"tool_name": ["Bash"], "tool_input": {}},  # array
    {"tool_name": {"name": "Bash"}, "tool_input": {}},  # object
])
def test_missing_or_non_scalar_tool_name_fails_closed(payload):
    """hook_json_get reports null/object/array as "missing"; all of them, and
    an absent key, are unclassifiable payloads and must block (M2)."""
    result = _run_hook({**payload, "cwd": _PROJECT_ROOT.as_posix()})
    assert result.returncode == 2, result.stderr
    assert "no usable tool_name" in result.stderr


@pytest.mark.parametrize("tool", [
    "Read", "Glob", "Grep", "WebFetch", "WebSearch", "TodoWrite", "Task",
    "Skill", "mcp__playwright__browser_navigate",
])
def test_known_non_mutating_tools_stay_allowed(tool):
    """M2 must not over-block: every known non-mutating tool keeps passing
    through untouched (this project's config has orchestrator.strict: true,
    so the pass-through is proven under strict mode too)."""
    result = _run_hook(_tool_payload(tool))
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"


def test_outdated_helper_lib_fails_closed(tmp_path):
    """A deployed lib/hook_common.sh from before hook_known_tool_name existed
    (sync.py not re-run) must block with a clear message instead of failing
    obscurely on the missing function."""
    hooks_dir = tmp_path / "hooks"
    (hooks_dir / "lib").mkdir(parents=True)
    (hooks_dir / "orchestrator-guard.sh").write_text(
        _HOOK_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    (hooks_dir / "orchestrator-guard-impl.sh").write_text(
        _IMPL_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    # Pre-M2 lib surface: no hook_known_tool_name.
    (hooks_dir / "lib" / "hook_common.sh").write_text(
        "#!/bin/bash\n"
        "hook_have_python() { command -v python3 >/dev/null 2>&1; }\n"
        "hook_python_bin() { printf '%s' python3; }\n"
        "hook_json_get() { printf '%s' \"${3:-}\"; }\n"
        "hook_json_usable() { return 0; }\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [_BASH, str(hooks_dir / "orchestrator-guard.sh")],
        input=json.dumps(_bash_payload("git status")),
        capture_output=True, text=True, cwd=str(tmp_path), env=_clean_env(),
    )
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "outdated" in result.stderr
    assert "hook_common.sh" in result.stderr


# --- issue #943: residual guard gaps (W2-B2b) ------------------------------
# Each case pins one sub-finding from the security review: (a) quadratic
# fork-bomb regex, (b) subshell grouping, (c) backslash-newline continuation,
# (d) whole-tree pathspecs, (e) gc immediate pruning, (f) update-ref --stdin
# deletes, (g) worktree remove --force, (h) force-create/delete branch,
# (i) false positives, (j) quoted operators / heredoc text, (k) lone-surrogate
# payload and classifier failure, (l) submodule walk-up, (m) documented gaps,
# (n) test isolation from the real audit log.

_SENTINEL = "#agent-meta:agent=git\n"


def test_fork_bomb_scan_does_not_hang_on_a_300kb_command(tmp_path):
    """(a) The old regex was quadratic (20 KB ~ 5 s -> hook timeout = allow).
    The pure-Python 100 ms bound is pinned in test_hook_common_lib.py; here we
    prove the whole hook still returns promptly for a 300 KB command."""
    command = "echo " + "a" * 300_000
    started = time.perf_counter()
    result = _run_with(_bash_payload(command), tmp_path)
    elapsed = time.perf_counter() - started
    assert result.returncode == 0, result.stderr
    assert elapsed < 5.0, f"300 KB command took {elapsed:.1f}s (quadratic scan?)"


def test_fork_bomb_window_block_names_scan_limits(tmp_path):
    """AC-A.7 (#943 follow-up): a body without an unquoted '}' in its first 512
    characters is blocked fail-closed (wave 3, PR A). The block message must
    name that limit, so a long inline function body is not mistaken for an
    arbitrary refusal. The command carries no digits, so 'first 512' can only
    come from the message."""
    result = _run_with(_bash_payload("f(){ " + "x" * 520 + " f|f& };f"), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "user approval" in result.stderr
    assert "first 512" in result.stderr, f"stderr={result.stderr!r}"


def test_subshell_parentheses_do_not_hide_a_destructive_push(tmp_path):
    """(b) shlex.split('(git push)') produced the token '(git', so the
    invocation was invisible."""
    result = _run_with(_bash_payload(_SENTINEL + "(git push --force origin main)"), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "user approval" in result.stderr


def test_backslash_newline_continuation_keeps_force_flag(tmp_path):
    """(c) Splitting at '\\n' made 'git push \\<newline> --force' two
    statements; the force flag was never attributed to the push."""
    command = _SENTINEL + "git push \\\n--force origin main"
    result = _run_with(_bash_payload(command), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "user approval" in result.stderr


@pytest.mark.parametrize("command", [
    "git checkout HEAD -- ./",
    "git checkout -- '*'",
    "git checkout :/",
    "git restore :/",
    "git restore .",
    "git restore --source HEAD -- *",
])
def test_whole_tree_pathspecs_are_destructive(tmp_path, command):
    """(d) './', '*', ':/' and 'HEAD -- ./' wipe the whole working tree, but
    only the literal '.' was recognised."""
    result = _run_with(_bash_payload(_SENTINEL + command), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "user approval" in result.stderr


@pytest.mark.parametrize("command", [
    "git checkout -- path/file.txt",
    "git restore path/file.txt",
])
def test_single_path_restore_stays_a_plain_mutation(tmp_path, command):
    """(d) counter-check: restoring one path is not a whole-tree wipe."""
    result = _run_with(_bash_payload(_SENTINEL + command), tmp_path)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("command", [
    "git gc --prune=now",
    "git -c gc.reflogExpire=now gc --prune=now",
    "git -c gc.pruneExpire=now gc",
    "git --config-env gc.reflogExpire=EXPIRY gc",
])
def test_immediate_gc_pruning_is_destructive(tmp_path, command):
    """(e) 'gc --prune=now' (and a gc.*Expire=now config) deletes unreachable
    objects immediately; neither was classified."""
    result = _run_with(_bash_payload(_SENTINEL + command), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "user approval" in result.stderr


def test_gc_without_immediate_expiry_is_not_destructive(tmp_path):
    """(e) counter-check: a plain gc / '=never' expiry is not destructive."""
    result = _run_with(_bash_payload(_SENTINEL + "git -c gc.reflogExpire=never gc"), tmp_path)
    assert result.returncode == 0, result.stderr


def test_update_ref_stdin_delete_line_is_destructive(tmp_path):
    """(f) 'update-ref --stdin' with delete lines was invisible."""
    command = _SENTINEL + "git update-ref --stdin <<EOF\ndelete refs/heads/main\nEOF"
    result = _run_with(_bash_payload(command), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "user approval" in result.stderr


def test_update_ref_stdin_without_delete_stays_a_mutation(tmp_path):
    """(f) counter-check: an inspectable create-only stdin is a plain
    mutation (allowed with the git sentinel)."""
    command = _SENTINEL + "git update-ref --stdin <<EOF\ncreate refs/heads/x HEAD\nEOF"
    result = _run_with(_bash_payload(command), tmp_path)
    assert result.returncode == 0, result.stderr


def test_update_ref_stdin_from_a_pipe_fails_closed(tmp_path):
    """(f) the pipe body is not visible to the hook -> unclassifiable, so it
    must be treated as destructive rather than allowed."""
    result = _run_with(_bash_payload(_SENTINEL + "printf 'delete refs/heads/x\\n' | git update-ref --stdin"), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "user approval" in result.stderr


@pytest.mark.parametrize("command", [
    "git worktree remove -f ../wt",
    "git worktree remove --force ../wt",
])
def test_worktree_remove_force_is_destructive(tmp_path, command):
    """(g) force-removing a worktree discards local modifications."""
    result = _run_with(_bash_payload(_SENTINEL + command), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "user approval" in result.stderr


def test_worktree_remove_without_force_stays_a_mutation(tmp_path):
    """(g) counter-check: without --force git refuses a dirty worktree."""
    result = _run_with(_bash_payload(_SENTINEL + "git worktree remove ../wt"), tmp_path)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("command", [
    "git checkout -B main",
    "git switch -C main",
    "git branch -f main HEAD",
    "git branch -D old",
])
def test_force_create_and_delete_branch_are_destructive(tmp_path, command):
    """(h) '-B'/'-C'/'-f'/'-D' reset or delete a branch tip."""
    result = _run_with(_bash_payload(_SENTINEL + command), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "user approval" in result.stderr


@pytest.mark.parametrize("command", [
    "git checkout -b x",
    "git switch -c x",
    "git branch -d old",
])
def test_plain_branch_create_and_merged_delete_stay_mutations(tmp_path, command):
    """(h) counter-check: lowercase -b/-c create and -d only deletes a merged
    branch; those remain plain mutations (allowed with the sentinel)."""
    result = _run_with(_bash_payload(_SENTINEL + command), tmp_path)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("command", [
    "git checkout -bfoo",              # '-b foo' -- 'f' is part of the value
    "man git pull",                    # git is an argument to man
    "git am --show-current-patch",     # read-only
    "git cherry-pick --abort",         # recovery action
    "git switch -",                    # previous-branch shorthand
])
def test_over_blocked_git_commands_are_allowed_with_sentinel(tmp_path, command):
    """(i) these were false positives. The real `git` role must be able to run
    them; the mutation gate itself is unchanged (see the counter-checks)."""
    result = _run_with(_bash_payload(_SENTINEL + command), tmp_path)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("command", [
    'echo "a; git push --force b"',
    "cat <<'EOF'\nplan: git push --force\nEOF",
    "echo 'reset; --hard'",
])
def test_operators_and_heredoc_text_are_not_commands(tmp_path, command):
    """(j) quoted operators and heredoc bodies were split into fake commands,
    tripping the destructive gate."""
    result = _run_with(_bash_payload(command), tmp_path)
    assert result.returncode == 0, result.stderr


def test_command_after_heredoc_terminator_is_still_scanned(tmp_path):
    """(j)/#944 SR-B-16: skipping the body must not stop scanning after it."""
    command = "cat <<'EOF'\nprose only\nEOF\ngit push --force origin main"
    result = _run_with(_bash_payload(command), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "user approval" in result.stderr


def test_lone_surrogate_payload_is_classified_not_dropped(tmp_path):
    """(k) a lone-surrogate escape used to crash the classifier, which then
    fell back to 'none' (allow). The destructive push must block."""
    payload = _bash_payload("git push --force " + chr(0xD800) + " origin main")
    payload["cwd"] = tmp_path.as_posix()
    result = subprocess.run(
        [_BASH, str(_HOOK_PATH)], input=json.dumps(payload).encode(),
        capture_output=True, cwd=str(tmp_path), env=_clean_env(),
    )
    assert result.returncode == 2, result.stderr[:200]
    assert b"user approval" in result.stderr


def test_lone_surrogate_benign_command_is_allowed(tmp_path):
    """(k) counter-check: the surrogate-safe read must not block a harmless
    command just because it contains an undecodable byte."""
    payload = _bash_payload("git status " + chr(0xD800))
    payload["cwd"] = tmp_path.as_posix()
    result = subprocess.run(
        [_BASH, str(_HOOK_PATH)], input=json.dumps(payload).encode(),
        capture_output=True, cwd=str(tmp_path), env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr[:200]


def _classifier_python_shim(tmp_path, body: str) -> dict:
    """PATH whose python3 is the real interpreter EXCEPT for the classifier
    script (recognised by the MUTATING marker)."""
    shim_dir = tmp_path / "classifier-shim"
    shim_dir.mkdir()
    real = shutil.which("python3") or "python3"
    shim = shim_dir / "python3"
    shim.write_text(
        "#!/bin/sh\n"
        'case "${2:-}" in\n'
        "  *MUTATING*) " + body + " ;;\n"
        "esac\n"
        'exec "' + real + '" "$@"\n',
        encoding="utf-8",
    )
    shim.chmod(0o755)
    env = _clean_env()
    env["PATH"] = f"{shim_dir}{os.pathsep}{env.get('PATH', '')}"
    return env


def test_classifier_crash_fails_closed(tmp_path):
    """(k) the old '|| echo none narrow none' allowed the call whenever the
    classifier died. A crash must block."""
    env = _classifier_python_shim(tmp_path, "exit 1")
    result = subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(_bash_payload("git status")),
        capture_output=True, text=True, cwd=str(tmp_path), env=env,
    )
    assert result.returncode == 2, result.stderr
    assert "classifier exited rc=1" in result.stderr


def test_classifier_garbage_output_fails_closed(tmp_path):
    """(k) exit 0 with output that is not '<category> <scope> <bom>' is also
    unevaluable and must block."""
    env = _classifier_python_shim(tmp_path, "printf 'garbage\\n'; exit 0")
    result = subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(_bash_payload("git status")),
        capture_output=True, text=True, cwd=str(tmp_path), env=env,
    )
    assert result.returncode == 2, result.stderr
    assert "malformed output" in result.stderr


def _meta_project(path: Path, orchestrator_block: str) -> Path:
    (path / ".meta-config").mkdir(parents=True, exist_ok=True)
    (path / ".meta-config" / "project.yaml").write_text(orchestrator_block, encoding="utf-8")
    return path


def test_submodule_meta_config_is_skipped_when_an_enclosing_project_exists(tmp_path):
    """(l) a nested agent-meta checkout carries its own .meta-config/ (strict
    here). A session inside it belongs to the enclosing (non-strict) project,
    so an ordinary Write must not be strict-blocked."""
    outer = _meta_project(tmp_path / "outer", "orchestrator:\n  mode: default\n")
    sub = _meta_project(outer / ".agent-meta", "orchestrator:\n  mode: strict\n")
    deep = sub / "hooks" / "x"
    deep.mkdir(parents=True)
    result = _run_with(_MAIN_THREAD_WRITE, deep)
    assert result.returncode == 0, result.stderr


def test_submodule_meta_config_is_the_fallback_when_nothing_encloses_it(tmp_path):
    """(l) a session opened only inside the submodule still resolves to it."""
    sub = _meta_project(tmp_path / ".agent-meta", "orchestrator:\n  mode: strict\n")
    result = _run_with(_MAIN_THREAD_WRITE, sub)
    assert result.returncode == 2, result.stderr
    assert "STRICT MODE" in result.stderr


def test_header_lists_known_gaps():
    """(m) the remaining gaps are documented in the implementation header."""
    header = _IMPL_PATH.read_text(encoding="utf-8").split("\nINPUT=$(cat)", 1)[0]
    assert "Known gaps" in header
    for gap in ("command substitution", "heredoc body", "bash -c"):
        assert gap in header, f"header does not document {gap!r}"


def test_strict_cases_never_write_the_repo_audit_log():
    """(n) STRICT_CASES used to append to the real .claude/hooks/
    .guard-audit.log (#945 / W2-E2). They run against a temp project now."""
    real_log = _REPO_ROOT / ".claude" / "hooks" / ".guard-audit.log"
    before = real_log.read_bytes() if real_log.exists() else None
    result = _run_hook(_bash_payload("#agent-meta:agent=git\ngit status"))
    assert result.returncode == 0, result.stderr
    after = real_log.read_bytes() if real_log.exists() else None
    assert after == before


def test_fork_bomb_text_in_a_heredoc_body_is_not_a_bomb(tmp_path):
    """(j) a heredoc body is prose; a fork-bomb example in documentation must
    not trip the destructive gate."""
    command = "cat <<'EOF'\n:(){ :|:& };:\nEOF"
    result = _run_with(_bash_payload(command), tmp_path)
    assert result.returncode == 0, result.stderr


def test_commented_out_fork_bomb_is_not_a_bomb(tmp_path):
    """(j) a commented-out command is not code (the sentinel line already
    relies on this)."""
    command = "# :(){ :|:& };:\necho hi"
    result = _run_with(_bash_payload(command), tmp_path)
    assert result.returncode == 0, result.stderr


# --- review findings F1-F4: splitter / command-word regressions ----------
# Wave-6 made the shared scanner quote/heredoc-aware and introduced
# command_start(). Both are right, but they dropped four blocking paths that
# HEAD still caught (F1-F4). These pin each one end to end.


@pytest.mark.parametrize("command", [
    "echo $'it\\'s'; git push --force origin main",
    "echo $'it\\'s'; rm -rf /",
])
def test_f1_ansi_c_quoting_does_not_swallow_a_later_command(tmp_path, command):
    """F1: $'it\\'s' desynced the quote state, so the whole rest of the line
    (force push / recursive rm) became invisible. The destructive gate must
    still block even with the git sentinel."""
    result = _run_with(_bash_payload(_SENTINEL + command), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "user approval" in result.stderr


@pytest.mark.parametrize("command", [
    "cat <<$X\nX\ngit push --force origin main",
    "cat <<${X}\nX\ngit push --force origin main",
    "cat <<`X`\nX\ngit push --force origin main",
    'cat <<"$X"\nX\ngit push --force origin main',
])
def test_f2_dynamic_heredoc_delimiter_does_not_hide_the_body(tmp_path, command):
    """F2: a delimiter the scanner cannot resolve must not suppress an
    unknown amount of following input (fail closed)."""
    result = _run_with(_bash_payload(_SENTINEL + command), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "user approval" in result.stderr


@pytest.mark.parametrize("command", [
    "timeout 30 git push --force origin main",
    "flock /tmp/l git push --force origin main",
    "setsid git push --force origin main",
    "watch git push --force origin main",
    "strace git push --force origin main",
    "chroot /x git push --force origin main",
    "busybox git push --force origin main",
    "case x in x) git push --force;; esac",
    "f(){ git push --force; }; f",
    "function f { git push --force; }; f",
])
def test_f3_wrappers_case_arms_and_function_bodies_are_classified(tmp_path, command):
    """F3: command_start() only inspected the first word per statement, so a
    wrapper, a `case` arm or an inline function body hid the real command."""
    result = _run_with(_bash_payload(_SENTINEL + command), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "user approval" in result.stderr


@pytest.mark.parametrize("command", [
    "timeout 30 git commit -m x",
    "flock /tmp/l git commit -m x",
])
def test_f3_wrapped_mutation_still_hits_the_mutation_gate(tmp_path, command):
    """F3 second half: without a git sentinel a wrapped `git commit` was not
    even seen as a mutation."""
    result = _run_with(_bash_payload(command), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "Direct git mutations are forbidden" in result.stderr


@pytest.mark.parametrize("command", [
    "timeout 30 man git pull",
    "timeout 30 echo git push --force origin main",
    "timeout 30 git status",
])
def test_f3_wrappers_do_not_reintroduce_the_argument_false_positive(tmp_path, command):
    """F3 counter-check: unwrapping must not degrade to 'any token named
    git'. A git ARGUMENT behind a wrapper stays ordinary text."""
    result = _run_with(_bash_payload(_SENTINEL + command), tmp_path)
    assert result.returncode == 0, result.stderr


def test_f4_trailing_comment_is_not_an_executable_fork_bomb(tmp_path):
    """F4: a bomb-shaped trailing comment reached the fork-bomb scan while the
    statement stream already dropped it. `git status` is benign."""
    result = _run_with(_bash_payload("git status # :(){ :|:& };:"), tmp_path)
    assert result.returncode == 0, result.stderr


def test_f4_a_real_fork_bomb_is_still_destructive(tmp_path):
    """F4 counter-check: cutting comments must not disarm the fork-bomb gate."""
    result = _run_with(_bash_payload(":(){ :|:& };:"), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "user approval" in result.stderr


# --- review findings F-NEW-1/F-NEW-2: regressions from the F3 fix ----------
# The F3 fix taught command_start() to unwrap a wrapper's positional prefix
# and to skip `case`/function prefixes, but it (1) stopped at a `--`
# end-of-options marker that follows such a prefix, and (2) did not recognise
# `in` when the shared splitter put `case WORD` and `in PATTERN)` onto
# different statements. Both reopened the destructive and mutation gates.
# These pin the general shape (marker transparent on every path; `case ... in`
# across statements) plus the wrapper option-arity bug that hid commands
# behind flag-like options (`setsid --wait`, `ionice -t`).

_F_NEW_1_DESTRUCTIVE = [
    # '--' after the wrapper's positional prefix (DURATION / FILE / ROOT)
    "timeout 5 -- git push --force origin main",
    "flock -w 5 /tmp/l -- git push --force origin main",
    "chroot /x -- git push --force origin main",
    # '--' directly before the command word / after wrapper options
    "timeout -- 5 git push --force origin main",
    "env -- git push --force origin main",
    "timeout 5 -- -- git push --force origin main",
    # wrapper chains with the marker in different positions
    "timeout 5 flock /tmp/l -- git push --force origin main",
    "sudo env X=1 timeout 5 -- git push --force origin main",
    "sudo -- env X=1 timeout 5 -- git push --force origin main",
    "chroot --userspec=u:g /x -- git push --force origin main",
    # flag-like wrapper options must not swallow the wrapped command word
    "setsid --wait git push --force origin main",
    "setsid -w git push --force origin main",
    "setsid -f git push --force origin main",
    "ionice -t git push --force origin main",
    "ionice -u 1000 git push --force origin main",
    "ionice -P 1 git push --force origin main",
]


@pytest.mark.parametrize("command", _F_NEW_1_DESTRUCTIVE)
def test_f_new_1_dash_marker_does_not_hide_a_force_push(tmp_path, command):
    """F-NEW-1: `--` at command position is transparent, so the wrapped force
    push is still destructive even with a valid git sentinel."""
    result = _run_with(_bash_payload(_SENTINEL + command), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "user approval" in result.stderr


@pytest.mark.parametrize("command", [
    "timeout 5 -- git commit -m x",
    "flock /tmp/l -- git commit -m x",
    "chroot /x -- git commit -m x",
])
def test_f_new_1_dash_marker_does_not_hide_a_mutation(tmp_path, command):
    """F-NEW-1 second half: a wrapped `git commit` behind `--` must still hit
    the mutation gate without a sentinel."""
    result = _run_with(_bash_payload(command), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "Direct git mutations are forbidden" in result.stderr


@pytest.mark.parametrize("command", [
    "man git pull",
    "timeout 30 man git pull",
    "timeout 30 -- man git pull",
    "git status",
    "timeout 30 -- git status",
    "echo git push --force",
    "timeout 30 -- echo git push --force origin main",
])
def test_f_new_1_dash_marker_keeps_git_as_an_argument(tmp_path, command):
    """F-NEW-1 counter-check: a transparent `--` must not turn a git ARGUMENT
    (`man git pull`, `echo git push`) into a git invocation."""
    result = _run_with(_bash_payload(command), tmp_path)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("command", [
    "timeout 5 -- git commit -m x",
    "timeout 5 -- git push origin main",
])
def test_f_new_1_dash_marker_keeps_allowed_mutations_allowed(tmp_path, command):
    """F-NEW-1 counter-check: the marker must not make a plain mutation
    (add/commit or a non-destructive push) newly blocked for the git role."""
    result = _run_with(_bash_payload(_SENTINEL + command), tmp_path)
    assert result.returncode == 0, result.stderr


_F_NEW_2_CASE_SPLIT = [
    # the regression: `case x` and `in x) ...` are separate statements
    "case x\nin x) git push --force;; esac",
    "case x\nin\nx) git push --force;;\nesac",
    # alternation across a newline
    "case $x\nin\n  a|b)\n    git push --force\n    ;;\nesac",
    # extglob / bracket pattern terminators are `)` runs, not a single ')'
    "case x\nin @(a|b)) git push --force;; esac",
    "case x\nin\n  @(a|b))\n    git push --force\n    ;;\nesac",
    "case x\nin [)]) git push --force;; esac",
    # nested function body inside a split case arm
    "case x\nin\n  x)\n    f(){ git push --force; }; f\n    ;;\nesac",
]


@pytest.mark.parametrize("command", _F_NEW_2_CASE_SPLIT)
def test_f_new_2_split_case_arm_is_classified(tmp_path, command):
    """F-NEW-2: `in` is a reserved word, so a `case` whose `in PATTERN)` lands
    on a later statement is still unwrapped to the arm's command list."""
    result = _run_with(_bash_payload(_SENTINEL + command), tmp_path)
    assert result.returncode == 2, result.stderr
    assert "user approval" in result.stderr


def test_f_new_2_split_case_arm_hits_the_mutation_gate(tmp_path):
    """F-NEW-2 second half: without a sentinel the split arm's `git commit`
    must be a mutation, not the literal command word `in`."""
    result = _run_with(
        _bash_payload("case x\nin x) git commit -m x;; esac"), tmp_path
    )
    assert result.returncode == 2, result.stderr
    assert "Direct git mutations are forbidden" in result.stderr


@pytest.mark.parametrize("command", [
    "case x in x) git status;; esac",
    "case x\nin x) git status;; esac",
    "case x\nin\n  @(a|b))\n    git status\n    ;;\nesac",
])
def test_f_new_2_split_case_arm_keeps_read_only_allowed(tmp_path, command):
    """F-NEW-2 counter-check: unwrapping a split case arm must not block a
    read-only command in that arm."""
    result = _run_with(_bash_payload(command), tmp_path)
    assert result.returncode == 0, result.stderr


def test_header_names_the_exact_residual_gaps():
    """F-DOC-1: the old header claimed a case pattern could never hide the
    command list after its ')', which was false for the split `case`/`in`
    shape. The header must now name the structural interpreter/wrapper gaps
    explicitly instead of implying completeness."""
    header = _IMPL_PATH.read_text(encoding="utf-8").split("\nINPUT=$(cat)", 1)[0]
    for gap in ("eval", "bash -c", "env -S", "UNKNOWN wrapper"):
        assert gap in header, f"header does not name {gap!r}"
    assert "never hide the command list" not in header, (
        "F-DOC-1: the disproven 'never hide' claim is still in the header"
    )
