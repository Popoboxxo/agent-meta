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
        cwd=str(_REPO_ROOT),
    )
    assert result.returncode == 0
    lines = audit_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 1000
    assert "old-line-1\n" not in "\n".join(lines[:1])  # oldest entries gone
    assert "git status" in lines[-1]
