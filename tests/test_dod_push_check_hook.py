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
import os
import shutil
import subprocess
import sys
import time
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


# --- issue #593: block-reason messages must go to stderr, not stdout ------

def test_branch_guard_block_reason_goes_to_stderr(repo_on_main):
    result = _run_hook(repo_on_main, "git push")
    assert result.returncode == 2
    assert "Branch-Guard" in result.stderr
    assert "Branch-Guard" not in result.stdout


# --- issue #595: fail CLOSED (not open) when python3 is unavailable -------

def test_fails_closed_without_python3(repo_on_main, tmp_path):
    """Manipulating PATH to hide python3 must BLOCK the push (exit 2, with
    a clear stderr reason), not silently allow it through -- the opposite
    of the pre-#595 behavior (`command -v python3 || exit 0`)."""
    minimal_bin = tmp_path / "minimal-bin"
    minimal_bin.mkdir()
    for tool in ("bash", "cat", "dirname", "mkdir", "date", "printf", "tr",
                 "head", "sed", "grep", "basename", "sh", "mv", "wc", "tail",
                 "chmod", "git"):
        found = shutil.which(tool)
        if found:
            (minimal_bin / tool).symlink_to(found)

    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "git push"},
        "cwd": repo_on_main.as_posix(),
    }
    env = {"PATH": str(minimal_bin)}
    result = subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(repo_on_main),
        env=env,
    )
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "python3" in result.stderr.lower()


# --- issue #594: SHA-keyed result cache + timeout --------------------------

@pytest.fixture
def repo_on_feature_branch(tmp_path):
    """A repo on a non-main feature branch (so the Branch-Guard never
    triggers), with a committed .meta-config/project.yaml the hook can
    discover via its upward directory walk."""
    repo = tmp_path / "repo"
    repo.mkdir()
    run = lambda *args: subprocess.run(  # noqa: E731
        ["git", *args], cwd=str(repo), capture_output=True, text=True, check=True
    )
    run("init", "-q")
    run("config", "user.email", "test@example.com")
    run("config", "user.name", "Test")
    run("checkout", "-q", "-b", "feat/x")
    (repo / "f.txt").write_text("x", encoding="utf-8")
    run("add", "f.txt")
    run("commit", "-q", "-m", "init")
    return repo


def _run_hook_with_config(repo: Path, command: str, project_yaml: str) -> subprocess.CompletedProcess:
    (repo / ".meta-config").mkdir(exist_ok=True)
    (repo / ".meta-config" / "project.yaml").write_text(project_yaml, encoding="utf-8")
    return _run_hook(repo, command)


def test_second_push_of_same_commit_hits_cache(repo_on_feature_branch):
    project_yaml = "variables:\n  TEST_COMMAND: \"echo running && exit 0\"\n"
    first = _run_hook_with_config(repo_on_feature_branch, "git push origin feat/x", project_yaml)
    assert first.returncode == 0, f"stdout={first.stdout!r} stderr={first.stderr!r}"
    assert "running" in first.stdout

    second = _run_hook(repo_on_feature_branch, "git push origin feat/x")
    assert second.returncode == 0
    assert "cached" in second.stdout.lower()
    assert "running" not in second.stdout  # test command was NOT re-run


def test_cache_invalidated_by_new_commit(repo_on_feature_branch):
    project_yaml = "variables:\n  TEST_COMMAND: \"echo running && exit 0\"\n"
    first = _run_hook_with_config(repo_on_feature_branch, "git push origin feat/x", project_yaml)
    assert first.returncode == 0

    subprocess.run(["git", "commit", "--allow-empty", "-q", "-m", "second"],
                    cwd=str(repo_on_feature_branch), capture_output=True, text=True, check=True)
    second = _run_hook(repo_on_feature_branch, "git push origin feat/x")
    assert second.returncode == 0
    assert "cached" not in second.stdout.lower()
    assert "running" in second.stdout  # test command WAS re-run for the new commit


def test_hanging_test_command_is_killed_by_timeout(repo_on_feature_branch):
    project_yaml = (
        "variables:\n"
        "  TEST_COMMAND: \"sleep 5\"\n"
        "  TEST_TIMEOUT: \"1\"\n"
    )
    result = _run_hook_with_config(repo_on_feature_branch, "git push origin feat/x", project_yaml)
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "TIMED OUT" in result.stderr


def test_failing_command_blocked_even_if_piped_through_success(repo_on_feature_branch):
    """A failing TEST_COMMAND must still block the push even if piped through
    a filter (e.g. rtk) that itself exits 0 — regression test for #753."""
    # A pipeline where the first part fails (exit 1) but the last part exits 0.
    # Before the fix: pipefail not propagated, so exit code 0 is captured.
    # After the fix: pipefail is set via "set -uo pipefail;", so exit code 1
    # from the first command in the pipeline is captured and the push is blocked.
    project_yaml = "variables:\n  TEST_COMMAND: \"false | cat\"\n"
    result = _run_hook_with_config(repo_on_feature_branch, "git push origin feat/x", project_yaml)
    assert result.returncode == 2, (
        f"A failing command piped through something exiting 0 must still block the push "
        f"(regression for #753)\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "FAILED" in result.stderr


# --- SR-B-01: tag-only detection must not leak across refs/statements -----
#
# The hook used to flag the WHOLE command as tag-only as soon as '--tags'
# appeared anywhere after the first 'push' token, skipping the Branch-Guard
# even when the same command also pushed main. With
# AGENT_META_TEST_COMMAND=false a skipped Branch-Guard surfaces as
# "DoD-Check FAILED" instead of the "Branch-Guard" block message.

TAGS_BYPASS_ATTEMPTS = [
    "git push origin main --tags",
    "git push origin tag v1.0.0 main",
    "git push origin --tags ; git push origin main",
    "git push --tags && git push origin main",
    # --follow-tags pushes the current branch too -- never tag-only
    "git push --follow-tags",
    "git push origin --follow-tags",
    # tag-looking refspec whose destination is a branch
    "git push origin refs/tags/v1.0.0:refs/heads/main",
    # SR-B-01 round 2: --no-tags negates an earlier --tags (last one wins)
    "git push origin --tags --no-tags",
    "git push origin --tags --no-tag",
    # space-form value option swallows the following '--tags'
    "git push origin -o --tags",
    "git push origin --push-option --tags",
    # line continuation joins both lines into ONE statement with a branch ref
    "git push --tags \\\norigin main",
    # unresolvable 'git ... push' statement must fail closed, not be dropped
    "git push --tags ; sudo -u git git push origin main",
    "git push --tags ; env -u git git push origin main",
    # --attr-source takes a separate value (issue #551 option set)
    "git push --tags ; git --attr-source HEAD push origin main",
    # unparseable quoting fails closed instead of falling back to str.split
    'git push origin --tags "main',
    # quoted ';' splits a real push into an unparseable fragment whose git
    # token is quoted — the old str.split fallback dropped it as non-git
    'git push --tags; g"i"t push origin main "x;y"',
    # unknown push flags (e.g. --recurse-submodules) are never tag-only
    "git push --recurse-submodules=on-demand origin --tags",
]

PURE_TAG_PUSHES = [
    "git push origin --tags",
    "git push origin tag v1.0.0",
    "git push origin refs/tags/v1.0.0",
    "git push origin --tags && git push origin tag v1.0.0",
    # redirects must not be misclassified as refs (release-flow regression)
    "git push origin --tags 2>&1",
    "git push origin tag v1.0.0 2>&1 | tail -5",
    "git push origin --tags >/dev/null",
    "git push origin --tags > /dev/null 2>&1",
    # last --tags/--no-tags occurrence wins
    "git push origin --no-tags --tags",
]


def _run_hook_failing_tests(cwd: Path, command: str) -> subprocess.CompletedProcess:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": cwd.as_posix(),
    }
    env = dict(os.environ, AGENT_META_TEST_COMMAND="false", AGENT_META_TEST_TIMEOUT="5")
    return subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
    )


@pytest.mark.parametrize("command", TAGS_BYPASS_ATTEMPTS)
def test_mixed_tag_and_branch_push_hits_branch_guard(repo_on_main, command):
    result = _run_hook_failing_tests(repo_on_main, command)
    assert result.returncode == 2
    assert "Branch-Guard: Push blocked" in result.stderr, (
        f"command={command!r} must not be treated as tag-only\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "DoD-Check FAILED" not in result.stderr


@pytest.mark.parametrize("command", PURE_TAG_PUSHES)
def test_pure_tag_push_skips_branch_guard(repo_on_main, command):
    result = _run_hook_failing_tests(repo_on_main, command)
    assert "Branch-Guard" not in result.stderr, (
        f"command={command!r} is tag-only and must skip the Branch-Guard\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "DoD-Check FAILED" in result.stderr


# --- W2-B1: push recognition by command word + destination Branch-Guard ----
#
# Outcomes with AGENT_META_TEST_COMMAND=false:
#   BLOCK -> rc 2, "Branch-Guard: Push blocked" (test gate never reached)
#   GATE  -> recognised push, Branch-Guard passed, test gate ran ("DoD-Check FAILED")
#   NONE  -> not a push at all: rc 0, neither guard nor test gate ran
# Nothing is ever pushed: the hook only inspects the command text.

BLOCK, GATE, NONE = "block", "gate", "none"


@pytest.fixture
def multi_repo(tmp_path):
    """Repo with branches main + feat/x (both on one commit), tag v1.0.0 and
    a dummy remote 'origin' (never contacted). Starts on feat/x."""
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
    run("remote", "add", "origin", str(tmp_path / "does-not-exist.git"))
    run("checkout", "-q", "-b", "feat/x")
    return repo


def _checkout(repo: Path, where: str) -> None:
    args = ["checkout", "-q", "--detach"] if where == "detached" else ["checkout", "-q", where]
    subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True, check=True)


def _outcome(result: subprocess.CompletedProcess) -> str:
    if "classifier error" in result.stderr:  # fail-closed crash, not a decision
        return f"classifier crash: {result.stderr!r}"
    if result.returncode == 2 and "Branch-Guard: Push blocked" in result.stderr:
        return BLOCK
    if result.returncode == 2 and "DoD-Check FAILED" in result.stderr:
        return GATE
    if result.returncode == 0 and "DoD-Check" not in result.stdout + result.stderr:
        return NONE
    return f"unexpected rc={result.returncode} stdout={result.stdout!r} stderr={result.stderr!r}"


def _assert_outcome(repo: Path, command: str, expected: str, env_extra=None) -> None:
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": repo.as_posix()}
    env = dict(os.environ, AGENT_META_TEST_COMMAND="false", AGENT_META_TEST_TIMEOUT="5")
    env.pop("AGENT_META_MAIN_BRANCH", None)
    env.update(env_extra or {})
    result = subprocess.run([_BASH, str(_HOOK_PATH)], input=json.dumps(payload),
                            capture_output=True, text=True, cwd=str(repo), env=env)
    assert _outcome(result) == expected, f"command={command[:200]!r}: {_outcome(result)}"


def _padding(size_kb: int) -> str:
    line = "# " + "x" * 78 + "\n"
    return line * (size_kb * 1024 // len(line))


# SR-B-21: printf | grep -q under pipefail let a padded push through (SIGPIPE).
@pytest.mark.parametrize("size_kb", [70, 300])
def test_large_multiline_push_still_blocked(multi_repo, size_kb):
    _checkout(multi_repo, "main")
    _assert_outcome(multi_repo, "git push origin main\n" + _padding(size_kb), BLOCK)


@pytest.mark.parametrize("size_kb", [70, 300])
def test_large_multiline_push_to_main_blocked_from_feature(multi_repo, size_kb):
    _assert_outcome(multi_repo, "git push origin HEAD:main\n" + _padding(size_kb), BLOCK)


@pytest.mark.parametrize("size_kb", [70, 300])
def test_large_multiline_non_push_allowed_quickly(multi_repo, size_kb):
    _checkout(multi_repo, "main")
    start = time.monotonic()
    _assert_outcome(multi_repo, "git status\n" + _padding(size_kb), NONE)
    assert time.monotonic() - start < 10


# SR-B-03: git invoked with global options / wrappers / subshells.
B03_FORMS = [
    "git -C . push origin {ref}",
    "git --no-pager push origin {ref}",
    "git -c push.default=simple push origin {ref}",
    "/usr/bin/git push origin {ref}",
    "command git push origin {ref}",
    "env VAR=1 git push origin {ref}",
    "VAR=1 git push origin {ref}",
    "sudo git push origin {ref}",
    "timeout 60 git push origin {ref}",
    "(git push origin {ref})",
    "echo hi; (cd . && git push origin {ref})",
    "git\tpush origin {ref}",
    "git  push   origin {ref}",
    "git pu''sh origin {ref}",
]


@pytest.mark.parametrize("form", B03_FORMS)
def test_global_option_push_blocked_on_main(multi_repo, form):
    _checkout(multi_repo, "main")
    _assert_outcome(multi_repo, form.format(ref="main"), BLOCK)


@pytest.mark.parametrize("form", B03_FORMS)
def test_global_option_push_to_main_blocked_from_feature(multi_repo, form):
    _assert_outcome(multi_repo, form.format(ref="main"), BLOCK)


@pytest.mark.parametrize("form", B03_FORMS)
def test_global_option_push_from_feature_runs_test_gate(multi_repo, form):
    _assert_outcome(multi_repo, form.format(ref="feat/x"), GATE)


# SR-B-04: text that merely contains "git push" is not a push.
B04_BENIGN = [
    'grep -rn "git push" docs/',
    "grep -rn git push docs",
    "echo git push",
    'echo "git push origin main"',
    "printf '%s\\n' git push origin main",
    'gh pr create --title t --body "then run git push origin main later"',
    "git stash push -m wip",
    "docker push example/image:latest",
]


@pytest.mark.parametrize("command", B04_BENIGN)
def test_benign_text_is_not_a_push_on_main(multi_repo, command):
    _checkout(multi_repo, "main")
    _assert_outcome(multi_repo, command, NONE)


@pytest.mark.parametrize("command", B04_BENIGN)
def test_benign_text_is_not_a_push_on_feature(multi_repo, command):
    _assert_outcome(multi_repo, command, NONE)


# SR-B-02: Branch-Guard checks destination refs, not only the current branch.
B02_TABLE = [
    # from a feature branch
    ("feat/x", "git push origin HEAD:main", BLOCK),
    ("feat/x", "git push origin feat/x:main", BLOCK),
    ("feat/x", "git push origin +feat/x:main", BLOCK),
    ("feat/x", "git push origin feat/x:refs/heads/main", BLOCK),
    ("feat/x", "git push origin HEAD:master", BLOCK),
    ("feat/x", "git push origin :main", BLOCK),
    ("feat/x", "git push origin --delete main", BLOCK),
    ("feat/x", "git push origin main", BLOCK),
    ("feat/x", "git push origin refs/heads/main", BLOCK),
    ("feat/x", "git push origin origin/main", BLOCK),
    ("feat/x", "git push --force-with-lease=main origin HEAD:main", BLOCK),
    ("feat/x", "git push --force-with-lease=main origin feat/x", BLOCK),
    ("feat/x", "git push --all", BLOCK),
    ("feat/x", "git push origin --all", BLOCK),
    ("feat/x", "git push --mirror origin", BLOCK),
    ("feat/x", "git push origin --branches", BLOCK),
    ("feat/x", "git push origin 'refs/heads/*:refs/heads/*'", BLOCK),
    ("feat/x", "git push origin :", BLOCK),
    ("feat/x", "git push --mirr origin", BLOCK),  # unique abbreviation of --mirror
    ("feat/x", "git push origin feat/x && git push origin HEAD:main", BLOCK),
    ("feat/x", "echo $(git push origin main)", BLOCK),
    ("feat/x", "git push origin >(cat) main", BLOCK),
    # destination computed at run time cannot be checked -> fail closed
    ("feat/x", "git push -u origin $(git branch --show-current)", BLOCK),
    ("feat/x", 'git push origin "$BRANCH"', BLOCK),
    ("feat/x", "git push origin feat/x", GATE),
    ("feat/x", "git push -u origin feat/x", GATE),
    ("feat/x", "git push --set-upstream origin feat/x", GATE),
    ("feat/x", "git push", GATE),
    ("feat/x", "git push origin", GATE),
    ("feat/x", "git push origin HEAD", GATE),
    ("feat/x", "git push --force origin feat/x", GATE),
    ("feat/x", "git push origin feat/x:feat/y", GATE),
    ("feat/x", "git push origin v1.0.0", GATE),
    ("feat/x", "git push origin --tags", GATE),
    # detached HEAD
    ("detached", "git push", BLOCK),
    ("detached", "git push origin", BLOCK),
    ("detached", "git push origin HEAD", BLOCK),
    ("detached", "git push origin HEAD:main", BLOCK),
    ("detached", "git push origin HEAD:feat/x", GATE),
    ("detached", "git push origin v1.0.0", GATE),
    # on main: the current-branch rule is kept
    ("main", "git push origin main:feat/x", BLOCK),
    ("main", "git push origin feat/x", BLOCK),
    ("main", "git push origin v1.0.0", GATE),
]


@pytest.mark.parametrize("where,command,expected", B02_TABLE)
def test_branch_guard_destination_table(multi_repo, where, command, expected):
    if where != "feat/x":
        _checkout(multi_repo, where)
    _assert_outcome(multi_repo, command, expected)


@pytest.mark.parametrize("command,expected", [
    ("git push origin HEAD:develop", BLOCK),
    ("git push origin HEAD:main", BLOCK),
    ("git push origin HEAD:master", BLOCK),
    ("git push origin feat/x", GATE),
])
def test_custom_main_branch_is_protected_destination(multi_repo, command, expected):
    _assert_outcome(multi_repo, command, expected, {"AGENT_META_MAIN_BRANCH": "develop"})


# --- W2-B1 round 2 ----------------------------------------------------------

def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True, check=True)


# F1: git resolves a destination not starting with 'refs/' via its DWIM rules
# (refs/%s, refs/tags/%s, refs/heads/%s, refs/remotes/%s): 'heads/main' is
# refs/heads/main on the remote.
F1_SPELLINGS = ["heads/main", "refs/heads/main", "remotes/origin/main",
                "refs/remotes/origin/main", "origin/main", "heads/master"]
F1_FORMS = [
    "git push origin HEAD:{s}",
    "git push origin +HEAD:{s}",
    "git push origin feat/x:{s}",
    "git push origin :{s}",
    "git push origin --delete {s}",
    "git push -d origin {s}",
    "git push --force-with-lease={s} origin HEAD:{s}",
    "git push --force-with-lease={s}:abc123 origin +HEAD:{s}",
    "git push origin {s}",
]
F1_TABLE = [(where, form.format(s=s), BLOCK)
            for s in F1_SPELLINGS for form in F1_FORMS
            for where in ("feat/x", "detached", "main")]
F1_TABLE += [
    # a tag named 'main' / a branch merely containing 'main' stays unprotected
    ("feat/x", "git push origin feat/x:refs/tags/main", GATE),
    ("feat/x", "git push origin feat/x:tags/main", GATE),
    ("feat/x", "git push origin --delete tags/main", GATE),
    ("feat/x", "git push origin HEAD:heads/feat/y", GATE),
    ("feat/x", "git push origin HEAD:refs/heads/feat/main", GATE),
    ("detached", "git push origin HEAD:heads/feat/y", GATE),
]


@pytest.mark.parametrize("where,command,expected", F1_TABLE)
def test_f1_dwim_destination_spellings(multi_repo, where, command, expected):
    if where != "feat/x":
        _checkout(multi_repo, where)
    _assert_outcome(multi_repo, command, expected)


# F2: a failing here-string (temp file cannot be written: /tmp full, ulimit -f)
# must never let a push through — neither via the pre-filter nor via the
# classifier input (empty classifier output = block).
@pytest.mark.parametrize("trap", ["", "trap '' XFSZ; "])
@pytest.mark.parametrize("where,first_line", [
    ("feat/x", "git push origin main"),
    ("feat/x", "git push origin HEAD:main"),
    ("main", "git push"),
])
def test_f2_here_string_failure_fails_closed(multi_repo, trap, where, first_line):
    if where != "feat/x":
        _checkout(multi_repo, where)
    command = first_line + "\n" + "\n".join(["echo " + "a" * 74] * 2000)  # ~160 KB
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    env = dict(os.environ, AGENT_META_TEST_COMMAND="false", AGENT_META_TEST_TIMEOUT="5")
    env.pop("AGENT_META_MAIN_BRANCH", None)
    result = subprocess.run(
        [_BASH, "-c", f'ulimit -f 64; {trap}exec "$0" "$1"', _BASH, str(_HOOK_PATH)],
        input=json.dumps(payload), capture_output=True, text=True,
        cwd=str(multi_repo), env=env)
    assert result.returncode == 2, f"rc={result.returncode} stderr={result.stderr[-300:]!r}"
    assert "Branch-Guard: Push blocked" in result.stderr


def test_f2_one_megabyte_non_push_is_fast(multi_repo):
    command = "git status\n" + _padding(1024)
    start = time.monotonic()
    _assert_outcome(multi_repo, command, NONE)
    assert time.monotonic() - start < 5


# QF1: a quoted separator before the refspec must not hide the destination.
QF1_TABLE = [
    ('git push -o "ci.variable=A;B" origin HEAD:main', BLOCK),
    ('git push -o "x|y" origin HEAD:main', BLOCK),
    ('git push -o "x&y" origin HEAD:main', BLOCK),
    ('git push -o "x&&y" origin feat/x:main', BLOCK),
    ("git push -o 'x;y' origin HEAD:main", BLOCK),
    ('git push -o "a\nb" origin HEAD:main', BLOCK),
    ('git -c "x.y=a;b" push origin HEAD:main', BLOCK),
    ('sudo -u "a;b" git push origin HEAD:main', BLOCK),
    # a statement that only parses after a quote was appended: fail closed
    ('git push -o "x|y" origin feat/x', BLOCK),
    # multi-line commit / PR text stays unaffected
    ('git commit -m "fix: push check\n\nexplain the push path; and | more\n"', NONE),
    ('gh pr create --title "push fix" --body "line one;\nline two | x\n"', NONE),
    ('git commit -m "a; push b"', NONE),
    ('git commit -m "a; b" && git push origin feat/x', GATE),
]


@pytest.mark.parametrize("command,expected", QF1_TABLE)
def test_qf1_quoted_separator_before_refspec(multi_repo, command, expected):
    _assert_outcome(multi_repo, command, expected)


# QF5: man/less/more/ack can execute commands (man -P, ack --pager).
@pytest.mark.parametrize("where", ["feat/x", "main"])
@pytest.mark.parametrize("command", [
    "man -P 'git push origin main' git",
    "man --pager='git push origin main' git",
    "man -P git-push git",
    "MANPAGER='git push origin main' man git",
    "ack --pager='git push origin main' x",
    "less 'git push origin main'",
])
def test_qf5_exec_capable_pagers_are_not_text(multi_repo, where, command):
    if where != "feat/x":
        _checkout(multi_repo, where)
    _assert_outcome(multi_repo, command, BLOCK)


@pytest.mark.parametrize("command", ["man git-push", "man git push", "less push.log"])
def test_qf5_reading_docs_is_not_a_push(multi_repo, command):
    _checkout(multi_repo, "main")
    _assert_outcome(multi_repo, command, NONE)


# A2: tag-only detection must not spawn one git process per ref.
def test_a2_many_tag_pushes_are_fast(multi_repo):
    _checkout(multi_repo, "main")
    start = time.monotonic()
    _assert_outcome(multi_repo, "git push origin v1.0.0\n" * 5000, GATE)
    assert time.monotonic() - start < 10


# A5: quoting/expansion forms bash resolves to a git push.
A5_FORMS = [
    "git $'push' origin main",
    'git $"push" origin main',
    "$'git' push origin main",
    "g$'i't push origin main",
    "git $'\\x70ush' origin main",
    "$'\\x67it' $'\\x70ush' origin main",
    "git pu$'s'h origin main",
    "git {push,} origin main",
    "{git,} push origin main",
    "git $(echo push) origin main",
    "$(which git) push origin main",
    "sudo $GIT push origin main",
    "git-push origin main",
    "/usr/lib/git-core/git-push origin main",
    "sudo git-push origin main",
]


@pytest.mark.parametrize("where", ["feat/x", "main"])
@pytest.mark.parametrize("command", A5_FORMS)
def test_a5_expanded_push_forms_blocked(multi_repo, where, command):
    if where != "feat/x":
        _checkout(multi_repo, where)
    _assert_outcome(multi_repo, command, BLOCK)


@pytest.mark.parametrize("command,expected", [
    ("git push origin {feat/x,main}", BLOCK),
    ("git push origin ma?n", BLOCK),
    ("git push -o $'a\\';b' origin HEAD:main", BLOCK),
    ("git-push origin feat/x", GATE),
])
def test_a5_expanded_refs_from_feature(multi_repo, command, expected):
    _assert_outcome(multi_repo, command, expected)


# A4: another repository (-C/--git-dir/--work-tree/GIT_DIR) cannot be judged
# by the cwd repo's HEAD.
@pytest.mark.parametrize("command,expected", [
    ("git -C . push", BLOCK),
    ("git -C . push origin", BLOCK),
    ("git -C . push origin HEAD", BLOCK),
    ("git --git-dir=.git push", BLOCK),
    ("git --git-dir .git push origin", BLOCK),
    ("git --work-tree . push origin HEAD", BLOCK),
    ("GIT_DIR=.git git push", BLOCK),
    ("env GIT_DIR=.git git push origin HEAD", BLOCK),
    ("git -C . push origin feat/x", GATE),
    ("git -C . push origin HEAD:feat/x", GATE),
])
def test_a4_other_repository_push(multi_repo, command, expected):
    _assert_outcome(multi_repo, command, expected)


# A3: a refspec-less / destination-less push resolves its destination through
# config (push.default, branch.<n>.merge, remote.<r>.push).
A3_TABLE = [
    ([("branch.feat/x.remote", "origin"), ("branch.feat/x.merge", "refs/heads/main")],
     [("git push", BLOCK), ("git push origin", BLOCK), ("git push origin feat/x", GATE),
      ("git push origin HEAD", GATE)]),
    ([("branch.feat/x.remote", "origin"), ("branch.feat/x.merge", "refs/heads/feat/x")],
     [("git push", GATE), ("git push origin", GATE)]),
    ([("push.default", "matching")], [("git push", BLOCK), ("git push origin feat/x", GATE)]),
    ([("remote.origin.push", "refs/heads/feat/x:refs/heads/main")],
     [("git push", BLOCK), ("git push origin", BLOCK), ("git push origin feat/x", BLOCK),
      ("git push origin HEAD", BLOCK), ("git push origin HEAD:feat/y", GATE)]),
    ([("remote.origin.push", "refs/heads/*:refs/heads/*")],
     [("git push", BLOCK), ("git push origin feat/x", BLOCK)]),
    ([("remote.origin.push", "refs/heads/feat/x:refs/heads/feat/x")],
     [("git push", GATE), ("git push origin feat/x", GATE)]),
    ([], [("git -c push.default=upstream push", BLOCK),
          ("git -c remote.origin.push=HEAD:main push origin feat/x", BLOCK),
          ("git -c include.path=/x push", BLOCK),
          ("GIT_CONFIG_PARAMETERS=x git push", BLOCK),
          ("git -c core.quotepath=off push", GATE),
          ("git -c core.quotepath=off push origin feat/x", GATE)]),
]


@pytest.mark.parametrize("config,rows", A3_TABLE)
def test_a3_push_destination_from_config(multi_repo, config, rows):
    for key, value in config:
        _git(multi_repo, "config", "--add", key, value)
    for command, expected in rows:
        _assert_outcome(multi_repo, command, expected)


def test_a3_tag_push_mapped_onto_main_is_not_tag_only(multi_repo):
    _checkout(multi_repo, "main")
    _git(multi_repo, "config", "remote.origin.push", "refs/tags/v1.0.0:refs/heads/main")
    _assert_outcome(multi_repo, "git push origin v1.0.0", BLOCK)


# R2-1: git subcommands/config that run another command must not hide a push
# (`git submodule foreach git push ...` was blocked by v2.0.3).
R2_1_BLOCKED = [
    "git submodule foreach git push origin main",
    "git submodule foreach --recursive git push origin HEAD:main",
    "git bisect run git push origin main",
    "git submodule foreach 'git push origin main'",
    "git rebase --exec 'git push origin main' HEAD~0",
    "git rebase -x 'git push origin main' HEAD",
    "git filter-branch --tree-filter 'git push origin main' HEAD",
    "git difftool -x 'git push origin main' HEAD",
    "git -c core.pager='git push origin main' log -1",
    "git -c core.sshCommand='sh -c \"git push origin main\"' fetch",
    "git -c core.editor='git push origin main' commit",
    "git -c sequence.editor='git push origin main' rebase -i HEAD",
    "git config alias.x '!git push origin main'",
    "git -c alias.p='!git push origin main' p",
    "git -c alias.x='!sh -c \"git push origin main\"' x",
    "git -c alias.p=push p origin main",
    "git -c ALIAS.p=push P origin HEAD:main",
    "git -c alias.p=push -c alias.q=p q origin main",
    "git --config-env=alias.p=PV p origin main",
    "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=alias.p GIT_CONFIG_VALUE_0=push git p origin main",
    "git -c core.sshCommand=ssh push origin feat/x",
    "git -c core.pager=cat push origin feat/x",
    "rg --pre 'git push origin main' x",
    "rg --pre=x push",
    "ack --pager=x push",
]


@pytest.mark.parametrize("where", ["feat/x", "main", "detached"])
@pytest.mark.parametrize("command", R2_1_BLOCKED)
def test_r2_1_command_running_subcommands_blocked(multi_repo, where, command):
    if where != "feat/x":
        _checkout(multi_repo, where)
    _assert_outcome(multi_repo, command, BLOCK)


@pytest.mark.parametrize("command,expected", [
    ("git -c alias.p=push p origin feat/x", GATE),
    ("git -c alias.p=push p origin HEAD:main", BLOCK),
    ('git commit -m "then git push origin main"', NONE),
    ('git tag -a v2 -m "git push origin main"', NONE),
    ('git log --grep "git push"', NONE),
    ("git stash push -m wip", NONE),
    ('rg "git push" docs', NONE),
    ("rg -n push scripts", NONE),
    ("git submodule foreach git status && git push origin feat/x", GATE),
])
def test_r2_1_resolved_aliases_and_text(multi_repo, command, expected):
    _assert_outcome(multi_repo, command, expected)


# R2-2: a payload the JSON helper cannot hand over must not open the gate.
def _run_payload(repo: Path, payload: bytes, env_extra=None) -> subprocess.CompletedProcess:
    env = dict(os.environ, AGENT_META_TEST_COMMAND="false", AGENT_META_TEST_TIMEOUT="5")
    env.pop("AGENT_META_MAIN_BRANCH", None)
    env.update(env_extra or {})
    return subprocess.run([_BASH, str(_HOOK_PATH)], input=payload, capture_output=True,
                          cwd=str(repo), env=env)


def _bash_payload(command: str) -> bytes:
    return json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}).encode()


@pytest.mark.parametrize("locale", ["C", "C.UTF-8", "de_DE.UTF-8"])
@pytest.mark.parametrize("command", [
    "git push origin main\ud800",
    "git push origin main\udcff",
    "echo \udcff; git push origin main",
    "git push origin main # \udfff",
])
def test_r2_2_lone_surrogate_does_not_skip_guard(multi_repo, locale, command):
    _checkout(multi_repo, "main")
    result = _run_payload(multi_repo, _bash_payload(command), {"LC_ALL": locale, "LANG": locale})
    assert result.returncode == 2, (locale, command, result.stderr[-300:])


@pytest.mark.parametrize("payload", [
    b'{"tool_name": "Bash", "tool_input": {"command": "git push origin main \xff\xfe"}}',
    b'{"tool_name": "Bash", "tool_input": {"command": "git push origin main\\u0000"}}',
    b'{"tool_name": "Bash", "tool_input": {"command": ["git", "push", "origin", "main"]}}',
    b'{"tool_name": "Bash", "tool_input": {"command": "git push origin main"',
    b'not json at all: git push origin main',
])
def test_r2_2_unextractable_bash_command_blocked(multi_repo, payload):
    _checkout(multi_repo, "main")
    for locale in ("C", "de_DE.UTF-8"):
        result = _run_payload(multi_repo, payload, {"LC_ALL": locale, "LANG": locale})
        assert result.returncode == 2, (locale, payload, result.stderr[-300:])


@pytest.mark.parametrize("payload", [
    b'{"tool_name": "Read", "tool_input": {"file_path": "x"}}',
    b'{"tool_name": "Write", "tool_input": {"file_path": "x", "content": "git push"}}',
    b'{"tool_name": "Bash", "tool_input": {"command": ""}}',
])
def test_r2_2_empty_command_for_non_bash_or_empty_bash_allowed(multi_repo, payload):
    _checkout(multi_repo, "main")
    result = _run_payload(multi_repo, payload)
    assert result.returncode == 0, (payload, result.stderr[-300:])


# R2-3: classifier time must stay linear; a hook timeout would fail open.
@pytest.mark.parametrize("command", [
    "git push origin main " + "a" * (1 << 20),
    "$" * (1 << 20) + " git push origin main",
    "\\" * (1 << 20) + " git push origin main",
    "git push origin main " + "a" * (2 << 20),
    "$" * (2 << 20) + "push origin main",
    "git push origin '{" + "," * (1 << 20) + "' main",
    "git rebase -x '" + "git " * (1 << 18) + "' HEAD; git push origin main",
], ids=["ident-1M", "dollar-1M", "backslash-1M", "ident-2M", "dollar-2M", "commas-1M",
        "git-words-1M"])
def test_r2_3_huge_push_commands_block_in_time(multi_repo, command):
    start = time.monotonic()
    _assert_outcome(multi_repo, command, BLOCK)
    assert time.monotonic() - start < 25


@pytest.mark.parametrize("command,expected", [
    ("git push origin feat/x\n" * 10000, GATE),
    ("echo " + "$(" * 50000 + "\ngit push origin main", BLOCK),
    ("git push origin main " + "a" * (300 << 10), BLOCK),
], ids=["10k-pushes", "50k-nested", "ident-300K"])
def test_r2_3_many_statements_and_nesting_fast(multi_repo, command, expected):
    start = time.monotonic()
    _assert_outcome(multi_repo, command, expected)
    assert time.monotonic() - start < 10


def test_r2_3_classifier_over_budget_blocks(multi_repo, tmp_path):
    # `timeout` killing the classifier (rc 124, no output) must block.
    stub = tmp_path / "stub"
    stub.mkdir()
    (stub / "timeout").write_text("#!/bin/sh\nexit 124\n", encoding="utf-8")
    (stub / "timeout").chmod(0o755)
    payload = _bash_payload("git push origin feat/x")
    result = _run_payload(multi_repo, payload,
                          {"PATH": f"{stub}{os.pathsep}{os.environ['PATH']}"})
    assert result.returncode == 2
    assert b"exceeded 20s" in result.stderr


def test_r2_3_normal_push_stays_fast(multi_repo):
    start = time.monotonic()
    _assert_outcome(multi_repo, "git push origin HEAD:main", BLOCK)
    assert time.monotonic() - start < 2


# R2-4: backslash-newline inside the word 'push' (bash joins the lines).
@pytest.mark.parametrize("command", [
    "git pu\\\nsh origin main",
    "git p\\\nu\\\ns\\\nh origin main",
])
def test_r2_4_line_continuation_inside_push(multi_repo, command):
    _checkout(multi_repo, "main")
    _assert_outcome(multi_repo, command, BLOCK)
