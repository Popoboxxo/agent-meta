"""Direct tests for the dod-push-check policy engine and reporter (MB-1).

Issue #1238c1 moved payload, config and classification into flat modules; MB-1
then moved the last decision tables (Branch-Guard verdict mapping, test-gate
state machine, result-cache key, test-result classification) into
``hook_dod_push_policy.py`` and every user-visible message into
``hook_dod_push_report.py``.  These tests pin both units directly, without a
hook process, and pin that the deployed hook still fails closed when either
module is missing.
"""
from __future__ import annotations

import ast
import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.timeouts import SCRIPT_TIMEOUT

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOKS_DIR = _REPO_ROOT / "hooks" / "1-generic"
_LIB_DIR = _HOOKS_DIR / "lib"
_HOOK_PATH = _HOOKS_DIR / "dod-push-check.sh"
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
for _path in (_SCRIPTS_DIR, _LIB_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from lib.hook_plugins import sync_hook_lib  # noqa: E402
from lib.log import SyncLog  # noqa: E402

_BASH = shutil.which("bash") or "bash"

_DISABLE_HINT = (
    "If this is intentional (release, hotfix), disable the hook temporarily:\n"
    "  Remove dod-push-check from hooks in .meta-config/project.yaml, "
    "re-sync, push, re-enable.\n"
)


def _load_module(filename: str):
    path = _LIB_DIR / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _call(module, argv, stdin: str = ""):
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = module.main(argv, stdin)
    return rc, stdout.getvalue(), stderr.getvalue()


def _policy():
    return _load_module("hook_dod_push_policy.py")


def _report():
    return _load_module("hook_dod_push_report.py")


def test_policy_module_is_pure_stdlib_only_and_py39_parseable():
    source = (_LIB_DIR / "hook_dod_push_policy.py").read_text(encoding="utf-8")
    tree = ast.parse(source, filename="hook_dod_push_policy.py",
                     feature_version=(3, 9))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    # No sys/os/json: the decisions must not read stdin, files or env.
    assert imports <= {"__future__"}
    for provider_name in ("Claude", "Gemini", "Codex", "Copilot", "OpenCode"):
        assert provider_name not in source


# --- policy engine: pure decisions ----------------------------------------

@pytest.mark.parametrize(
    "output,expected",
    [
        ("none", ("none", "")),
        ("tag", ("tag", "")),
        ("push", ("push", "")),
        ("onbranch main", ("onbranch", "main")),
        ("onbranch ", ("onbranch", "")),
        (
            "block destination 'main' of refspec 'main' is a protected branch",
            ("block", "destination 'main' of refspec 'main' is a protected branch"),
        ),
        # ${PUSH_CLASS#block } leaves a bare 'block' untouched: its first word
        # still is 'block', so it was reported as the reason before.
        ("block", ("block", "block")),
        ("", ("block", "push classification failed (fail closed)")),
        ("garbage", ("block", "push classification failed (fail closed)")),
        # A multi-line verdict never matched the former case pattern -> blocked.
        ("none\ngit push", ("block", "push classification failed (fail closed)")),
        ("block a\nb", ("block", "a\nb")),
    ],
)
def test_branch_verdict_matches_the_former_case_table(output, expected):
    assert _policy().branch_verdict(output, 0, "20") == expected


@pytest.mark.parametrize(
    "output,expected",
    [
        ("", ("block", "push classification exceeded 20s (fail closed)")),
        ("block x", ("block", "push classification exceeded 20s (fail closed)")),
        # The plain tokens were matched before rc was consulted at all.
        ("none", ("none", "")),
        ("tag", ("tag", "")),
        ("push", ("push", "")),
        ("onbranch main", ("onbranch", "main")),
    ],
)
def test_branch_verdict_budget_timeout_overrides_only_block_reasons(
    output, expected
):
    assert _policy().branch_verdict(output, 124, "20") == expected


@pytest.mark.parametrize(
    "config_file,test_cmd,expected",
    [
        ("", "", "no-config"),
        ("project.yaml", "", "no-command"),
        ("project.yaml", "pytest -q", "run"),
        ("", "pytest -q", "run"),
        ("project.yaml", " ", "run"),
    ],
)
def test_test_gate_state(config_file, test_cmd, expected):
    assert _policy().test_gate_state(config_file, test_cmd) == expected


@pytest.mark.parametrize(
    "content,head_sha,test_cmd,expected",
    [
        ("abc\npytest", "abc", "pytest", True),
        # $(cat) stripped trailing newlines; the key itself is exact.
        ("abc\npytest\n\n", "abc", "pytest", True),
        ("abc\npytest\r\n", "abc", "pytest", False),
        ("abc\npytest -q", "abc", "pytest", False),
        ("abd\npytest", "abc", "pytest", False),
        ("", "abc", "pytest", False),
        (None, "abc", "pytest", False),
        ("abc\npytest", "", "pytest", False),
    ],
)
def test_cache_matches(content, head_sha, test_cmd, expected):
    assert _policy().cache_matches(content, head_sha, test_cmd) is expected


@pytest.mark.parametrize(
    "rc,timeout_available,expected",
    [
        (0, True, "pass"),
        (0, False, "pass"),
        (1, True, "fail"),
        (1, False, "fail"),
        (124, True, "timeout"),
        # Without a timeout binary, rc 124 is the test suite's own exit code.
        (124, False, "fail"),
    ],
)
def test_test_result_verdict(rc, timeout_available, expected):
    assert _policy().test_result_verdict(rc, timeout_available) == expected


# --- reporter: messages stay byte-identical -------------------------------

def test_report_branch_allows_are_silent():
    report = _report()
    # Not a push at all: the shell exits 0 without running the test gate.
    assert _call(report, ["branch", "0", "20", "main", "main, master"], "none") == (
        3, "", ""
    )
    # A tag-only or plain push continues to the test gate.
    for verdict in ("tag", "push"):
        assert _call(
            report, ["branch", "0", "20", "main", "main, master"], verdict
        ) == (0, "", "")


def test_report_branch_onbranch_message_is_byte_exact():
    rc, out, err = _call(
        _report(), ["branch", "0", "20", "trunk", "trunk, main, master"],
        "onbranch main\n",
    )
    assert (rc, out) == (2, "")
    assert err == (
        "Branch-Guard: Push blocked — you are on 'main'.\n"
        "Create a feature branch first: git checkout -b feat/<topic>\n"
        "Direct pushes to trunk are not allowed by DoD policy.\n"
        "\n" + _DISABLE_HINT
    )


def test_report_branch_block_message_is_byte_exact():
    rc, out, err = _call(
        _report(), ["branch", "0", "20", "main", "main, master"],
        "block '--mirror' pushes many refs, destination cannot be determined",
    )
    assert (rc, out) == (2, "")
    assert err == (
        "Branch-Guard: Push blocked — '--mirror' pushes many refs, "
        "destination cannot be determined.\n"
        "Protected branches: main, master. "
        "Push a feature branch and open a PR instead.\n"
        "\n" + _DISABLE_HINT
    )


def test_report_branch_budget_message_is_byte_exact():
    rc, _, err = _call(_report(), ["branch", "124", "20", "main", "main, master"], "")
    assert rc == 2
    assert err.startswith(
        "Branch-Guard: Push blocked — push classification exceeded 20s "
        "(fail closed).\n"
    )
    assert "Protected branches: main, master. " in err


@pytest.mark.parametrize("args", [[], ["branch"], ["branch", "0", "20", "main"],
                                  ["branch", "x", "20", "main", "main, master"]])
def test_report_branch_argument_validation(args):
    assert _call(_report(), args, "none") == (1, "", "")


def test_report_gate_no_config_message_is_byte_exact():
    rc, out, err = _call(_report(), ["gate", "", "", "", "", "300", "1"])
    assert (rc, err) == (3, "")
    assert out == (
        "DoD-Check: no project config found (.meta-config/project.yaml).\n"
        "The test gate could not be evaluated. Either run from within the project,\n"
        "or export AGENT_META_TEST_COMMAND='<your-test-command>' to enable it.\n"
        "Push allowed (Branch-Guard passed, but test gate was NOT enforced).\n"
    )


def test_report_gate_no_command_message_is_byte_exact():
    rc, out, err = _call(_report(), ["gate", "project.yaml", "", "", "", "300", "1"])
    assert (rc, err) == (4, "")
    assert out == (
        "DoD-Check: TEST_COMMAND not configured — skipping test gate.\n"
        "Set variables.TEST_COMMAND in .meta-config/project.yaml or\n"
        "export AGENT_META_TEST_COMMAND='<your-test-command>' to enable.\n"
        "Push allowed (Branch-Guard passed, no test gate configured).\n"
    )


def test_report_gate_cache_hit_message_is_byte_exact(tmp_path):
    cache = tmp_path / "cache"
    cache.write_text("0123456789abcdef0123\npytest -q", encoding="utf-8")
    rc, out, err = _call(
        _report(),
        ["gate", "project.yaml", "pytest -q", str(cache),
         "0123456789abcdef0123", "300", "1"],
    )
    assert (rc, err) == (5, "")
    assert out == (
        "DoD-Check: tests already passed for commit 0123456789ab "
        "with this TEST_COMMAND (cached) — skipping re-run.\n"
        "Delete " + str(cache) + " to force a re-run.\n"
    )


def test_report_gate_run_announces_timeout_and_missing_timeout(tmp_path):
    report = _report()
    assert _call(
        report, ["gate", "project.yaml", "pytest -q", "", "", "42", "1"]
    ) == (0, "DoD-Check: Running 'pytest -q' (timeout: 42s)...\n", "")
    rc, out, err = _call(
        report, ["gate", "project.yaml", "pytest -q", "", "", "42", "0"]
    )
    assert rc == 0
    assert out == "DoD-Check: Running 'pytest -q' (timeout: 42s)...\n"
    assert err == (
        "DoD-Check: 'timeout' command not available on this system — "
        "running the test gate without a hard time limit.\n"
    )


def test_report_gate_ignores_missing_or_mismatching_cache(tmp_path):
    report = _report()
    args = ["gate", "project.yaml", "pytest -q", str(tmp_path / "absent"),
            "0123456789abcdef0123", "300", "1"]
    assert _call(report, args)[0] == 0
    mismatched = tmp_path / "cache"
    mismatched.write_text("0123456789abcdef0123\npytest", encoding="utf-8")
    args[3] = str(mismatched)
    assert _call(report, args)[0] == 0


@pytest.mark.parametrize("args", [[], ["gate"], ["gate", "c", "t", "", "", "300"]])
def test_report_gate_argument_validation(args):
    assert _call(_report(), args) == (1, "", "")


def test_report_result_pass_fail_timeout_are_byte_exact():
    report = _report()
    assert _call(report, ["result", "0", "300", "1", "pytest -q"]) == (
        0, "DoD-Check passed.\n", ""
    )
    assert _call(report, ["result", "1", "300", "1", "pytest -q"]) == (
        2, "",
        "\nDoD-Check FAILED: Tests must pass before pushing.\n"
        "Fix failing tests and retry, or disable the hook temporarily.\n",
    )
    assert _call(report, ["result", "124", "5", "1", "pytest -q"]) == (
        2, "",
        "\nDoD-Check TIMED OUT after 5s: 'pytest -q'.\n"
        "Raise the limit via variables.TEST_TIMEOUT in .meta-config/project.yaml "
        "(or AGENT_META_TEST_TIMEOUT), or fix a hanging test.\n"
        "Fix failing tests and retry, or disable the hook temporarily.\n",
    )
    # rc 124 without a timeout binary is a plain test failure.
    assert _call(report, ["result", "124", "5", "0", "pytest -q"])[1:] == (
        "", "\nDoD-Check FAILED: Tests must pass before pushing.\n"
        "Fix failing tests and retry, or disable the hook temporarily.\n",
    )


def test_report_unknown_scene_and_argument_validation():
    report = _report()
    assert _call(report, []) == (1, "", "")
    assert _call(report, ["nope"]) == (1, "", "")
    assert _call(report, ["result"]) == (1, "", "")
    assert _call(report, ["result", "x", "1", "1", "cmd"]) == (1, "", "")


def test_report_cli_reads_the_verdict_from_stdin():
    result = subprocess.run(
        [sys.executable, str(_LIB_DIR / "hook_dod_push_report.py"),
         "branch", "0", "20", "main", "main, master"],
        input=b"onbranch main\n",
        capture_output=True,
        timeout=SCRIPT_TIMEOUT,
    )
    assert result.returncode == 2
    assert result.stdout == b""
    assert b"you are on 'main'." in result.stderr


# --- deployed hook: fail closed when a new module is missing --------------

def _init_repo(root: Path, branch: str) -> Path:
    root.mkdir()
    run = lambda *args: subprocess.run(  # noqa: E731
        ["git", *args], cwd=str(root), capture_output=True, text=True,
        check=True, timeout=SCRIPT_TIMEOUT,
    )
    run("init", "-q")
    run("config", "user.email", "test@example.com")
    run("config", "user.name", "Test")
    run("checkout", "-q", "-b", branch)
    (root / "f.txt").write_text("x", encoding="utf-8")
    run("add", "f.txt")
    run("commit", "-q", "-m", "init")
    return root


def _deploy_hook(project_root: Path) -> Path:
    provider = "runtime"
    sync_hook_lib(
        _REPO_ROOT,
        project_root,
        {"platforms": []},
        SyncLog(),
        dry_run=False,
        provider=provider,
        provider_config={
            provider: {
                "hooks_dir": ".runtime/hooks",
                "has_hooks": True,
                "hook_protocol": "claude-code-json",
            }
        },
    )
    hooks = project_root / ".runtime" / "hooks"
    shutil.copy(_HOOK_PATH, hooks / "dod-push-check.sh")
    return hooks / "dod-push-check.sh"


def _run_hook(hook: Path, cwd: Path) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("AGENT_META_")}
    payload = {"tool_name": "Bash", "tool_input": {"command": "git push origin feat/x"}}
    return subprocess.run(
        [_BASH, str(hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
        timeout=SCRIPT_TIMEOUT,
    )


@pytest.mark.parametrize(
    "module",
    ["hook_dod_push_report.py", "hook_dod_push_policy.py"],
)
def test_hook_fails_closed_when_reporter_or_policy_is_missing(tmp_path, module):
    repo = _init_repo(tmp_path / "repo", "feat/x")
    hook = _deploy_hook(repo)
    target = hook.parent / "lib" / module
    target.unlink()
    target.mkdir()
    result = _run_hook(hook, repo)
    assert result.returncode == 2, result.stderr
    assert module in result.stderr
    assert "fail" in result.stderr.lower()
    assert result.stdout == ""


def test_hook_allows_the_same_push_once_both_modules_are_deployed(tmp_path):
    repo = _init_repo(tmp_path / "repo", "feat/x")
    hook = _deploy_hook(repo)
    result = _run_hook(hook, repo)
    assert result.returncode == 0, result.stderr
    assert "no project config found" in result.stdout
