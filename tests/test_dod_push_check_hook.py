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


def _clean_env(extra=None) -> dict:
    """Hermetic hook environment (issue #951): the caller's AGENT_META_*
    variables must never leak into a test run, otherwise results depend on
    the invoking shell. Extras are applied afterwards on purpose."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("AGENT_META_")}
    env.update(extra or {})
    return env


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
        env=_clean_env(),
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
    env = _clean_env({"AGENT_META_TEST_COMMAND": "false", "AGENT_META_TEST_TIMEOUT": "5"})
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
    env = _clean_env({"AGENT_META_TEST_COMMAND": "false", "AGENT_META_TEST_TIMEOUT": "5"})
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
    env = _clean_env({"AGENT_META_TEST_COMMAND": "false", "AGENT_META_TEST_TIMEOUT": "5"})
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
    env = _clean_env({"AGENT_META_TEST_COMMAND": "false", "AGENT_META_TEST_TIMEOUT": "5"})
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


# --- issues #947 / #948 / #950: false positives and xargs bypass -----------

_HEREDOC_TEXT = [
    'gh pr create --body "$(cat <<\'EOF\'\nsummary\ngit push origin main\nEOF\n)"',
    'git commit -m "$(cat <<\'EOF\'\nfix\ngit push origin main\nEOF\n)"',
    "cat <<EOF\ngit push origin main\nEOF",
]
_HEREDOC_EXECUTED = [
    "bash <<EOF\ngit push origin main\nEOF",
    "cat <<EOF | bash\ngit push origin main\nEOF",
    "echo $(bash <<EOF\ngit push origin main\nEOF\n)",
    'echo "x <<EOF"\ngit push origin main\nEOF',
    'sh -c "$(cat <<EOF\ngit push origin main\nEOF\n)"',
]


@pytest.mark.parametrize("command", _HEREDOC_TEXT)
def test_947_heredoc_text_for_text_consumer_is_not_a_push(repo_on_feature_branch, command):
    result = _run_hook(repo_on_feature_branch, command)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("command", _HEREDOC_EXECUTED)
def test_947_heredoc_fed_to_a_shell_is_still_classified(repo_on_feature_branch, command):
    result = _run_hook(repo_on_feature_branch, command)
    assert result.returncode == 2, result.stdout


def test_947_unterminated_heredoc_keeps_body_visible(repo_on_feature_branch):
    result = _run_hook(repo_on_feature_branch, "cat <<EOF\ngit push origin main\n")
    assert result.returncode == 2


@pytest.mark.parametrize("command,expected", [
    ("git push origin feat/x # main", 0),
    ("git push origin feat/x #main", 0),
    ('git push origin "#main"', 0),
    ("git push origin main # note", 2),
    # mid-word '#' is NOT a comment in bash: 'main' is still a second refspec
    ("git push origin feat#x main", 2),
])
def test_948_comment_handling(repo_on_feature_branch, command, expected):
    result = _run_hook(repo_on_feature_branch, command)
    assert result.returncode == expected, (command, result.stderr)


@pytest.mark.parametrize("command", [
    "echo main | xargs git push origin",
    "echo main | xargs -I{} git push origin {}",
    "git push origin {}",
])
def test_950_xargs_and_placeholder_pushes_fail_closed(repo_on_feature_branch, command):
    result = _run_hook(repo_on_feature_branch, command)
    assert result.returncode == 2, result.stdout


def test_950_computed_refspec_message_names_the_way_out(repo_on_feature_branch):
    result = _run_hook(repo_on_feature_branch, "git push origin $(git branch --show-current)")
    assert result.returncode == 2
    assert "HEAD" in result.stderr


# --- issue #952: cd into another repository --------------------------------

@pytest.mark.parametrize("command", [
    "cd ../other && git push",
    "cd ../other && git push origin HEAD",
    "pushd ../other; git push",
    "(cd ../other && git push)",
    "cd && git push",
])
def test_952_push_after_chdir_is_judged_as_foreign_repo(repo_on_feature_branch, command):
    result = _run_hook(repo_on_feature_branch, command)
    assert result.returncode == 2, result.stdout
    assert "another repository" in result.stderr


@pytest.mark.parametrize("command", [
    "cd . && git push origin feat/x",          # no-op cd, explicit safe ref
    "cd ../other && git push origin feat/x",   # explicit non-protected ref is safe anywhere
    "echo abcd && git push origin feat/x",     # 'cd' inside another word
])
def test_952_explicit_safe_refs_and_non_cd_words_are_not_blocked(repo_on_feature_branch, command):
    result = _run_hook(repo_on_feature_branch, command)
    assert result.returncode == 0, result.stderr


# --- issue #953 / #1051: --recurse-submodules pushes submodules too --------
#
# #953 shipped the fail-closed half: any repo with a top-level .gitmodules
# blocked. #1051 replaces that blanket block with a per-submodule destination
# check against the submodule's own push configuration; an undeterminable
# destination still fails closed and now names the way out.

def test_953_recurse_submodules_on_demand_blocked_when_repo_has_submodules(repo_on_feature_branch):
    # A .gitmodules entry whose submodule is not initialised: its push
    # configuration cannot be read, so the check must fail closed (#1051)
    # instead of silently allowing the flag through.
    (repo_on_feature_branch / ".gitmodules").write_text(
        '[submodule "s"]\n\tpath = s\n\turl = ../s\n', encoding="utf-8")
    for flag in ("on-demand", "only"):
        result = _run_hook(repo_on_feature_branch, f"git push --recurse-submodules={flag} origin feat/x")
        assert result.returncode == 2, (flag, result.stdout)
        assert "submodule 's'" in result.stderr, result.stderr
        assert "cannot be determined" in result.stderr, result.stderr


def test_953_recurse_submodules_allowed_without_submodules_or_for_check(repo_on_feature_branch):
    plain = _run_hook(repo_on_feature_branch, "git push --recurse-submodules=on-demand origin feat/x")
    assert plain.returncode == 0, plain.stderr  # no .gitmodules: flag is a no-op
    (repo_on_feature_branch / ".gitmodules").write_text("", encoding="utf-8")
    check = _run_hook(repo_on_feature_branch, "git push --recurse-submodules=check origin feat/x")
    assert check.returncode == 0, check.stderr  # check only verifies, never pushes
    no_flag = _run_hook(repo_on_feature_branch, "git push origin feat/x")
    assert no_flag.returncode == 0, no_flag.stderr


# --- issue #1033: the block message names each protected branch once -------

@pytest.mark.parametrize("main_branch,expected_list", [
    ("main", "main, master"),        # the reported case: 'main, main, master'
    ("master", "main, master"),
    ("develop", "develop, main, master"),
])
def test_1033_block_message_lists_protected_branches_once(
        repo_on_feature_branch, main_branch, expected_list):
    """The protected set is main + master + the configured main branch; the
    message must print that set de-duplicated (exit code stays 2)."""
    payload = {"tool_name": "Bash", "tool_input": {"command": "git push origin main"},
               "cwd": repo_on_feature_branch.as_posix()}
    env = _clean_env({"AGENT_META_MAIN_BRANCH": main_branch})
    result = subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(repo_on_feature_branch),
        env=env,
    )
    assert result.returncode == 2, result.stderr
    assert f"Protected branches: {expected_list}. " in result.stderr, result.stderr


# --- issue #949: one flag walk, one protected-list builder ----------------

def test_949_push_guard_helpers_live_in_the_shared_lib():
    """The flag/short-cluster walk and the protected-branch set are defined
    once (in lib/hook_common.sh) and used by both consumers — the hook must
    not carry a second copy again."""
    src = _HOOK_PATH.read_text(encoding="utf-8")
    assert "def walk_push_args" not in src          # implementation is in the lib
    assert src.count("walk_push_args(") == 2        # tag-only + destination
    assert "hook_push_arg_parser_py" in src
    assert "hook_protected_branches" in src
    assert "for k, ch in enumerate(a[1:], 1):" not in src  # old short walk
    assert '_PROTECTED_BRANCHES="main, master"' not in src  # old message list
    assert "${PROTECTED_LIST// /, }" in src


def test_949_missing_shared_helper_fails_closed(repo_on_feature_branch, tmp_path):
    """An outdated deployed lib (sync not re-run) must block, not silently
    run the guard without the shared push helpers."""
    hook_copy = tmp_path / "hooks" / "dod-push-check.sh"
    hook_copy.parent.mkdir()
    hook_copy.write_text(_HOOK_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    (hook_copy.parent / "lib").mkdir()
    (hook_copy.parent / "lib" / "hook_common.sh").write_text(
        "#!/bin/bash\nhook_json_get() { :; }\n", encoding="utf-8")
    payload = {"tool_name": "Bash", "tool_input": {"command": "git push origin feat/x"},
               "cwd": repo_on_feature_branch.as_posix()}
    result = subprocess.run(
        [_BASH, str(hook_copy)], input=json.dumps(payload),
        capture_output=True, text=True, cwd=str(repo_on_feature_branch),
        env=_clean_env({"AGENT_META_TEST_COMMAND": "false"}))
    assert result.returncode == 2, result.stderr
    assert "outdated" in result.stderr


# --- issue #951: closed test gaps (branch resolution, cwd, hermetic env) ---

def _make_repo(path: Path, branch: str) -> Path:
    """Minimal repo with one commit on `branch` and a second branch main."""
    path.mkdir(parents=True)
    run = lambda *args: subprocess.run(  # noqa: E731
        ["git", *args], cwd=str(path), capture_output=True, text=True, check=True)
    run("init", "-q")
    run("config", "user.email", "test@example.com")
    run("config", "user.name", "Test")
    run("checkout", "-q", "-b", "main")
    (path / "f.txt").write_text("x", encoding="utf-8")
    run("add", "f.txt")
    run("commit", "-q", "-m", "init")
    if branch != "main":
        run("checkout", "-q", "-b", branch)
    return path


def test_951_main_branch_from_project_yaml(tmp_path):
    """GIT_MAIN_BRANCH from .meta-config/project.yaml must protect that
    branch (previously only the AGENT_META_MAIN_BRANCH env path was tested)."""
    repo = _make_repo(tmp_path / "repo", "develop")
    (repo / ".meta-config").mkdir()
    (repo / ".meta-config" / "project.yaml").write_text(
        'variables:\n  GIT_MAIN_BRANCH: develop\n  TEST_COMMAND: "true"\n',
        encoding="utf-8")
    # bare push from the configured main branch -> current-branch guard
    result = _run_hook(repo, "git push")
    assert result.returncode == 2, result.stderr
    assert "'develop'" in result.stderr
    # destination develop from the same branch -> destination guard
    result = _run_hook(repo, "git push origin develop")
    assert result.returncode == 2, result.stderr
    assert "develop" in result.stderr


def test_951_tag_and_branch_with_the_same_name_is_not_tag_only(multi_repo):
    """With refs/tags/main and refs/heads/main both present, `origin main` is
    ambiguous — it must be judged a branch push (BLOCK), never tag-only (GATE
    in this harness, because the test gate is forced to fail)."""
    _git(multi_repo, "tag", "main")
    _assert_outcome(multi_repo, "git push origin main", BLOCK)
    _checkout(multi_repo, "main")
    _assert_outcome(multi_repo, "git push origin main", BLOCK)


def test_951_dash_c_other_repo_is_judged_as_foreign(tmp_path):
    """`-C <other>` (not `.`) must not inherit this repo's HEAD/config: a
    refspec-less or HEAD push is blocked, an explicit safe ref is allowed."""
    repo = _make_repo(tmp_path / "repo", "feat/x")
    _make_repo(tmp_path / "other", "main")
    (repo / ".meta-config").mkdir()
    (repo / ".meta-config" / "project.yaml").write_text(
        'variables:\n  TEST_COMMAND: "true"\n', encoding="utf-8")
    for command in ("git -C ../other push",
                    "git -C ../other push origin",
                    "git -C ../other push origin HEAD"):
        result = _run_hook(repo, command)
        assert result.returncode == 2, (command, result.stderr)
        assert "another repository" in result.stderr
    # an explicit protected destination is still caught by the refspec check
    result = _run_hook(repo, "git -C ../other push origin HEAD:main")
    assert result.returncode == 2, result.stderr
    assert "protected branch" in result.stderr
    result = _run_hook(repo, "git -C ../other push origin feat/x")
    assert result.returncode == 0, result.stderr
    assert "DoD-Check passed" in result.stdout


def test_951_run_hook_is_hermetic_against_caller_agent_meta_env(tmp_path, monkeypatch):
    """A caller with AGENT_META_MAIN_BRANCH/AGENT_META_TEST_COMMAND exported
    must not change the outcome: _run_hook scrubs AGENT_META_* (branch
    'develop' is mains only if the leaked MAIN_BRANCH is honoured, and the
    leaked TEST_COMMAND=false would block the test gate)."""
    repo = _make_repo(tmp_path / "repo", "develop")
    monkeypatch.setenv("AGENT_META_MAIN_BRANCH", "develop")
    monkeypatch.setenv("AGENT_META_TEST_COMMAND", "false")
    result = _run_hook(repo, "git push")
    assert result.returncode == 0, result.stderr
    assert "no project config found" in result.stdout


# --- issue #953: a real submodule setup, both value spellings --------------

@pytest.fixture
def repo_with_real_submodule(tmp_path):
    """Repo on feat/x with a real submodule (not just a .gitmodules file),
    so the recurse-submodules check sees the same top level git does."""
    sub = _make_repo(tmp_path / "sub", "main")
    repo = _make_repo(tmp_path / "repo", "feat/x")
    _git(repo, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(sub), "s")
    _git(repo, "commit", "-qm", "add submodule")
    (repo / ".meta-config").mkdir()
    (repo / ".meta-config" / "project.yaml").write_text(
        'variables:\n  TEST_COMMAND: "true"\n', encoding="utf-8")
    return repo


@pytest.mark.parametrize("command", [
    "git push --recurse-submodules=on-demand origin feat/x",
    "git push --recurse-submodules=only origin feat/x",
    # git's parse-options takes the value as the NEXT token, not only after
    # '=' -- verified against git itself; the hook must consume it the same
    # way or 'on-demand' becomes the remote and the check never runs
    "git push --recurse-submodules on-demand origin feat/x",
    "git push --recurse-submodules only origin feat/x",
])
def test_953_recurse_submodules_real_submodule_is_blocked(repo_with_real_submodule, command):
    # The fixture's submodule tracks main, so its effective push destination
    # is the protected branch 'main' (#1051). The block must name both the
    # submodule path and the destination.
    result = _run_hook(repo_with_real_submodule, command)
    assert result.returncode == 2, (command, result.stdout)
    assert "submodule 's'" in result.stderr, result.stderr
    assert "protected branch 'main'" in result.stderr, result.stderr


@pytest.mark.parametrize("command", [
    "git push --recurse-submodules=check origin feat/x",  # verifies only
    "git push --recurse-submodules=no origin feat/x",     # does not recurse
    "git push origin feat/x",
])
def test_953_recurse_submodules_non_pushing_values_allowed(repo_with_real_submodule, command):
    # check / no / absent flag are never resolved against submodule targets.
    result = _run_hook(repo_with_real_submodule, command)
    assert result.returncode == 0, (command, result.stderr)


# --- issue #1051: per-submodule push destination check ---------------------

RECURSE_UNPROTECTED = [
    "git push --recurse-submodules=on-demand origin feat/x",
    "git push --recurse-submodules on-demand origin feat/x",
    "git push --recurse-submodules=only origin feat/x",
    "git push --recurse-submodules only origin feat/x",
]


@pytest.mark.parametrize("command", RECURSE_UNPROTECTED)
def test_1051_submodule_push_to_unprotected_branch_allowed(repo_with_real_submodule, command):
    """Submodule configured to push to an unprotected branch: the recurse
    push must be allowed — the residual false positive of #953 is gone.
    Both the '=' and the space spelling are covered."""
    _git(repo_with_real_submodule / "s", "config", "remote.origin.push",
         "refs/heads/main:refs/heads/feat/sub")
    result = _run_hook(repo_with_real_submodule, command)
    assert result.returncode == 0, (command, result.stderr)


def test_1051_submodule_push_to_protected_branch_names_path_and_destination(
        repo_with_real_submodule):
    """A protected destination on the submodule's own remote blocks and the
    message names the submodule path and the destination branch."""
    _git(repo_with_real_submodule / "s", "config", "remote.origin.push",
         "refs/heads/main:refs/heads/main")
    result = _run_hook(repo_with_real_submodule,
                       "git push --recurse-submodules=on-demand origin feat/x")
    assert result.returncode == 2, result.stdout
    assert "submodule 's'" in result.stderr, result.stderr
    assert "protected branch 'main'" in result.stderr, result.stderr


def test_1051_url_push_target_still_uses_submodule_remote_config(
        repo_with_real_submodule, tmp_path):
    """When the superproject push target is a URL (not a configured remote),
    git runs a plain `git push` inside the submodule, so its branch remote's
    push config still decides the destination — a protected target must not
    slip through just because the URL is not a remote name."""
    _git(repo_with_real_submodule / "s", "config", "remote.origin.push",
         "refs/heads/main:refs/heads/main")
    url = (tmp_path / "not-a-configured-remote.git").as_posix()
    result = _run_hook(repo_with_real_submodule,
                       f"git push --recurse-submodules=on-demand {url} feat/x")
    assert result.returncode == 2, result.stdout
    assert "submodule 's'" in result.stderr, result.stderr
    assert "protected branch 'main'" in result.stderr, result.stderr


def test_1051_unreadable_submodule_config_fails_closed(repo_on_feature_branch):
    """An incomplete submodule setup (entry in .gitmodules, no repository on
    disk) must block — and the message must name the way out (#1051)."""
    (repo_on_feature_branch / ".gitmodules").write_text(
        '[submodule "s"]\n\tpath = s\n\turl = ../s\n', encoding="utf-8")
    result = _run_hook(repo_on_feature_branch,
                       "git push --recurse-submodules=on-demand origin feat/x")
    assert result.returncode == 2, result.stdout
    assert "submodule 's'" in result.stderr, result.stderr
    assert "cannot be determined" in result.stderr, result.stderr
    assert "explicitly" in result.stderr, result.stderr  # the way out


def test_1051_repo_without_gitmodules_is_unaffected(repo_on_feature_branch):
    """No .gitmodules: the flag stays a no-op, exactly as before (#953)."""
    result = _run_hook(repo_on_feature_branch,
                       "git push --recurse-submodules=on-demand origin feat/x")
    assert result.returncode == 0, result.stderr


def test_1051_several_submodules_stay_within_classifier_budget(tmp_path):
    """Six real submodules, each with its own push config: the classifier
    still finishes far below its 20 s budget (one config read per submodule,
    no repeated git invocations)."""
    repo = _make_repo(tmp_path / "repo", "feat/x")
    for i in range(6):
        sub = _make_repo(tmp_path / f"sub{i}", "main")
        _git(repo, "-c", "protocol.file.allow=always",
             "submodule", "add", "-q", str(sub), f"s{i}")
        _git(repo / f"s{i}", "config", "remote.origin.push",
             "refs/heads/main:refs/heads/feat/sub")
    _git(repo, "commit", "-qm", "add submodules")
    (repo / ".meta-config").mkdir()
    (repo / ".meta-config" / "project.yaml").write_text(
        'variables:\n  TEST_COMMAND: "true"\n', encoding="utf-8")
    start = time.monotonic()
    result = _run_hook(repo, "git push --recurse-submodules=on-demand origin feat/x")
    elapsed = time.monotonic() - start
    assert result.returncode == 0, result.stderr
    assert elapsed < 20, f"classifier took {elapsed:.1f}s (budget 20 s)"


# --- issue #954: security re-review checks that were never run -------------

def _shim_path(tmp_path: Path, name: str, body: str) -> str:
    """PATH with a wrapper binary of `name` in front of the real PATH."""
    d = tmp_path / "shim"
    d.mkdir(exist_ok=True)
    f = d / name
    f.write_text(body, encoding="utf-8")
    f.chmod(0o755)
    return f"{d}{os.pathsep}{os.environ['PATH']}"


def _failing_git(condition: str) -> str:
    """A git wrapper that exits 1 for the subcommand matched by `condition`."""
    real = shutil.which("git") or "/usr/bin/git"
    return (
        "#!/bin/sh\n"
        f'for a in "$@"; do if {condition}; then exit 1; fi; done\n'
        f'exec "{real}" "$@"\n'
    )


def test_954_garbage_python3_shim_fails_closed(multi_repo):
    """A python3 that exits 0 with garbage used to be taken as the payload:
    tool_name became 'garbage', the hook exited 0 ("not Bash") and a push to
    main went through. It must fail closed instead."""
    _checkout(multi_repo, "main")
    path = _shim_path(multi_repo.parent, "python3", "#!/bin/sh\necho garbage\n")
    result = _run_payload(multi_repo, _bash_payload("git push origin main"), {"PATH": path})
    assert result.returncode == 2, result.stderr
    assert b"does not behave" in result.stderr


def test_954_broken_python3_shim_is_reported_as_such(multi_repo):
    """M3/#954: a python3 that exits non-zero without output looked usable —
    ``hook_json_usable`` compared against its own fallback default. The hook
    still blocked, but through the R2-2 payload check with the misleading
    "command could not be read" text. The interpreter check must name it."""
    path = _shim_path(multi_repo.parent, "python3", "#!/bin/sh\nexit 1\n")
    result = _run_payload(multi_repo, _bash_payload("git push origin main"), {"PATH": path})
    assert result.returncode == 2, result.stderr
    assert b"does not behave" in result.stderr, result.stderr
    assert b"could not be read" not in result.stderr, result.stderr


def test_954_failing_git_config_fails_closed(multi_repo):
    """An unreadable `git config` may hide remote.<r>.push / push.default —
    a refspec-less push must block, not assume the default config."""
    path = _shim_path(multi_repo.parent, "git",
                      _failing_git('[ "$a" = "config" ] && [ "${*#*--list}" != "$*" ]'))
    _assert_outcome(multi_repo, "git push", BLOCK, {"PATH": path})
    _assert_outcome(multi_repo, "git push origin", BLOCK, {"PATH": path})


# B1 (blocker, review follow-up on #954): the tag-only shortcut is the FIRST
# caller of the config check, so it used to inspect the verdict *before* the
# config was read (_cfg_ok starts True and only turns False inside
# git_config()). An unreadable config was therefore read as "no push mapping"
# -> "tag" -> exit 0, while the same command with a readable
# remote.origin.push=refs/tags/v1.0.0:refs/heads/main was blocked (rc 2).
TAG_ONLY_WITH_CONFIG = [
    "git push --tags origin",
    "git push origin v1.0.0",
    "git push origin refs/tags/v1.0.0",
    "git push origin tag v1.0.0",
    "git push origin --tags && git push origin tag v1.0.0",
]


@pytest.mark.parametrize("command", TAG_ONLY_WITH_CONFIG)
def test_954_unreadable_git_config_fails_closed_for_tag_only_pushes(multi_repo, command):
    """A tag-only push must not slip past on an unreadable `git config`."""
    _checkout(multi_repo, "main")
    path = _shim_path(multi_repo.parent, "git",
                      _failing_git('[ "$a" = "config" ] && [ "${*#*--list}" != "$*" ]'))
    _assert_outcome(multi_repo, command, BLOCK, {"PATH": path})


@pytest.mark.parametrize("command", TAG_ONLY_WITH_CONFIG)
def test_954_tag_only_pushes_still_blocked_by_a_readable_tag_to_main_mapping(
        multi_repo, command):
    """The readable counterpart of the case above: the same commands are
    blocked by a tag->main mapping read from the config (no regression)."""
    _checkout(multi_repo, "main")
    _git(multi_repo, "config", "remote.origin.push",
         "refs/tags/v1.0.0:refs/heads/main")
    _assert_outcome(multi_repo, command, BLOCK)


def test_954_failing_for_each_ref_stays_fail_closed(multi_repo):
    """Without a ref snapshot every tag name looks like a missing ref, so a
    `push origin v1.0.0` must not be treated as tag-only (fail closed)."""
    _checkout(multi_repo, "main")
    path = _shim_path(multi_repo.parent, "git", _failing_git('[ "$a" = "for-each-ref" ]'))
    _assert_outcome(multi_repo, "git push origin v1.0.0", BLOCK, {"PATH": path})


def test_954_config_injection_on_the_command_line_blocks(multi_repo):
    """GIT_CONFIG_COUNT/KEY/VALUE and GIT_CONFIG_PARAMETERS are honoured by
    git itself; a push statement carrying them must not be resolved as safe."""
    _assert_outcome(
        multi_repo,
        "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=remote.origin.push "
        "GIT_CONFIG_VALUE_0=refs/heads/feat/x:refs/heads/main git push",
        BLOCK)
    _assert_outcome(
        multi_repo,
        "GIT_CONFIG_PARAMETERS=\"'remote.origin.push' 'refs/heads/*:refs/heads/*'\" "
        "git push origin",
        BLOCK)


def test_954_config_injection_from_the_environment_blocks(multi_repo):
    """Injection exported by the caller (not on the command line) is invisible
    to the token scan but is still read by the classifier's own `git config`
    — the resolved mapping must block a destination-less push."""
    _assert_outcome(
        multi_repo, "git push origin", BLOCK,
        {"GIT_CONFIG_PARAMETERS":
         "'remote.origin.push' 'refs/heads/*:refs/heads/*'"})


def test_954_include_file_from_environment_blocks(multi_repo, tmp_path):
    inc = tmp_path / "included.cfg"
    inc.write_text('[remote "origin"]\n\tpush = refs/heads/*:refs/heads/*\n',
                   encoding="utf-8")
    _assert_outcome(multi_repo, "git push origin", BLOCK,
                    {"GIT_CONFIG_GLOBAL": str(inc)})
    _assert_outcome(multi_repo, f"git -c include.path={inc} push origin", BLOCK)


DEFAULT_MODE_TABLE = [
    ([], "simple", GATE),
    ([], "current", GATE),
    ([("branch.feat/x.remote", "origin"),
      ("branch.feat/x.merge", "refs/heads/main")], "upstream", BLOCK),
    ([("branch.feat/x.remote", "origin"),
      ("branch.feat/x.merge", "refs/heads/feat/x")], "upstream", GATE),
    ([], "matching", BLOCK),
    # push.default=nothing makes git itself refuse the push; allowing it
    # cannot push anything (documented, not a gap)
    ([], "nothing", GATE),
]


@pytest.mark.parametrize("config,mode,expected", DEFAULT_MODE_TABLE)
def test_954_push_default_mode_matrix(multi_repo, config, mode, expected):
    for key, value in config:
        _git(multi_repo, "config", "--add", key, value)
    _git(multi_repo, "config", "push.default", mode)
    _assert_outcome(multi_repo, "git push", expected)


@pytest.mark.parametrize("mode,expected", [("simple", GATE), ("matching", BLOCK)])
def test_954_push_default_mode_matrix_in_submodule_repo(
        repo_with_real_submodule, mode, expected):
    _git(repo_with_real_submodule, "config", "push.default", mode)
    _assert_outcome(repo_with_real_submodule, "git push", expected)
