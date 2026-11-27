"""Direct, CLI and deployment tests for the dod-push-check Python modules.

Issue #1238c1 moves payload-state, config reading and push classification out of
Bash heredocs into flat modules next to ``hook_common.sh``.  The deployed hook
must keep its exit codes and remain fail-closed without Python or a module.
"""
from __future__ import annotations

import ast
import contextlib
import importlib.util
import inspect
import io
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import get_type_hints

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
# CLI modules: each is invoked from the hook through one deployed path
# literal (see test_hook_has_no_extracted_inline_python_and_has_version_changelog).
_MODULES = (
    "hook_dod_push_payload.py",
    "hook_dod_push_config.py",
    "hook_dod_push_classify.py",
    "hook_dod_push_report.py",
)
# Library module: imported by the reporter, verified by the hook's fail-closed
# preflight and tested directly (issue #1238c1 MB-1).
_POLICY_MODULE = "hook_dod_push_policy.py"


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


def _clean_env(extra=None) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("AGENT_META_")}
    env.update(extra or {})
    return env


def _init_repo(root: Path, branch: str = "main") -> Path:
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
    run("tag", "-a", "v1.0.0", "-m", "v1.0.0")
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


def _run_hook(hook: Path, cwd: Path, command: str, env=None):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    return subprocess.run(
        [_BASH, str(hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=_clean_env() if env is None else env,
        timeout=SCRIPT_TIMEOUT,
    )


@pytest.mark.parametrize("filename", _MODULES)
def test_module_contract_python39_stdlib_and_provider_neutral(filename):
    module = _load_module(filename)
    signature = inspect.signature(module.main)
    assert list(signature.parameters) == ["argv", "stdin"]
    hints = get_type_hints(module.main)
    assert hints["argv"] == list[str]
    assert hints["stdin"] is str
    assert hints["return"] is int

    source = (_LIB_DIR / filename).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=filename, feature_version=(3, 9))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports <= {
        "__future__", "collections", "json", "os", "re", "shlex",
        "subprocess", "sys", "yaml", "hook_push_arg_parser", "hook_shell_scan",
        "hook_dod_push_policy",
    }
    for provider_name in ("Claude", "Gemini", "Codex", "Copilot", "OpenCode"):
        assert provider_name not in source
    assert not re.search(
        r"ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY",
        source,
    )


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"tool_name": "Bash", "tool_input": {"command": ""}}, "empty\n"),
        ({"tool_name": "Bash", "tool_input": {}}, "empty\n"),
        ({"tool_name": "Bash", "tool_input": {"command": None}}, "empty\n"),
        ({"tool_name": "", "tool_input": {"command": ""}}, "empty\n"),
        ({"tool_name": "Read", "tool_input": {"command": "text"}}, "empty\n"),
        ({"tool_name": "Bash", "tool_input": {"command": "git push"}}, "unreadable\n"),
        ({"tool_name": "", "tool_input": {"command": "git push"}}, "unreadable\n"),
        ({"tool_name": "Bash", "tool_input": {"command": 0}}, "unreadable\n"),
        ({"tool_name": "Bash", "tool_input": {"command": []}}, "unreadable\n"),
        ([], "unreadable\n"),
    ],
)
def test_payload_state_classification(payload, expected):
    module = _load_module("hook_dod_push_payload.py")
    assert _call(module, [], json.dumps(payload)) == (0, expected, "")


@pytest.mark.parametrize("payload", ["", "{broken", "null"])
def test_payload_state_malformed_json_fails_closed(payload):
    module = _load_module("hook_dod_push_payload.py")
    assert _call(module, [], payload) == (0, "unreadable\n", "")


def test_payload_state_cli_and_argument_validation():
    module = _load_module("hook_dod_push_payload.py")
    assert _call(module, ["unexpected"], "{}") == (1, "", "")
    result = subprocess.run(
        [sys.executable, str(_LIB_DIR / (module.__name__ + ".py"))],
        input=b'{"tool_name":"Bash","tool_input":{"command":""}}',
        capture_output=True,
        timeout=SCRIPT_TIMEOUT,
    )
    assert (result.returncode, result.stdout, result.stderr) == (0, b"empty\n", b"")


def test_config_reader_json_and_yaml(tmp_path, monkeypatch):
    module = _load_module("hook_dod_push_config.py")
    json_path = tmp_path / "agent-meta.config.json"
    json_path.write_text(
        json.dumps({"variables": {"GIT_MAIN_BRANCH": "release", "TEST_COMMAND": "pytest -q"}}),
        encoding="utf-8",
    )
    assert _call(module, [str(json_path), "GIT_MAIN_BRANCH"]) == (0, "release\n", "")
    assert _call(module, [str(json_path), "TEST_COMMAND"]) == (0, "pytest -q\n", "")

    yaml_path = tmp_path / "project.yaml"
    yaml_path.write_text(
        'variables:\n  GIT_MAIN_BRANCH: "trunk"\n  TEST_COMMAND: "pytest -q"\n',
        encoding="utf-8",
    )
    assert _call(module, [str(yaml_path), "GIT_MAIN_BRANCH"])[1] == "trunk\n"

    monkeypatch.setitem(sys.modules, "yaml", None)
    assert _call(module, [str(yaml_path), "GIT_MAIN_BRANCH"]) == (0, "trunk\n", "")
    assert _call(module, [str(yaml_path), "TEST_COMMAND"]) == (0, "pytest -q\n", "")


@pytest.mark.parametrize("content", ["", "{broken", "variables: []\n", "other:\n  X: y\n"])
def test_config_reader_unreadable_or_missing_values_are_empty(tmp_path, content):
    module = _load_module("hook_dod_push_config.py")
    path = tmp_path / "project.yaml"
    path.write_text(content, encoding="utf-8")
    assert _call(module, [str(path), "GIT_MAIN_BRANCH"]) == (0, "\n", "")
    assert _call(module, [str(tmp_path / "missing.yaml"), "GIT_MAIN_BRANCH"]) == (0, "\n", "")


def test_config_reader_cli_and_argument_validation(tmp_path):
    module = _load_module("hook_dod_push_config.py")
    assert _call(module, []) == (1, "", "")
    assert _call(module, ["only-one"]) == (1, "", "")
    path = tmp_path / "agent-meta.config.json"
    path.write_text('{"variables":{"TEST_COMMAND":"pytest"}}', encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(_LIB_DIR / (module.__name__ + ".py")), str(path), "TEST_COMMAND"],
        capture_output=True,
        timeout=SCRIPT_TIMEOUT,
    )
    assert (result.returncode, result.stdout, result.stderr) == (0, b"pytest\n", b"")


@pytest.mark.parametrize(
    "command,main_branch,current_branch,protected,expected",
    [
        ("git status", "main", "main", "main master", "none\n"),
        ('echo "git push origin main"', "main", "main", "main master", "none\n"),
        ("git push", "main", "main", "main master", "onbranch main\n"),
        ("git push", "main", "master", "main master", "onbranch master\n"),
        ("git push", "trunk", "trunk", "main master trunk", "onbranch trunk\n"),
        ("git push", "trunk", "trunk", "", "push\n"),
        ("git push origin feat/x", "main", "feat/x", "main master", "push\n"),
        (
            "git push origin main", "main", "feat/x", "main master",
            "block destination 'main' of refspec 'main' is a protected branch\n",
        ),
        (
            "git push origin HEAD:main", "main", "feat/x", "main master",
            "block destination 'main' of refspec 'HEAD:main' is a protected branch\n",
        ),
        (
            "git push --mirror", "main", "feat/x", "main master",
            "block '--mirror' pushes many refs, destination cannot be determined\n",
        ),
        (
            'git push origin "main', "main", "feat/x", "main master",
            "block git push statement with a quote spanning a command separator\n",
        ),
    ],
)
def test_push_classifier_branch_and_destination_rules(
    tmp_path, monkeypatch, command, main_branch, current_branch, protected, expected
):
    repo = _init_repo(tmp_path / "repo", current_branch)
    monkeypatch.chdir(repo)
    module = _load_module("hook_dod_push_classify.py")
    assert _call(module, [main_branch, current_branch, protected], command) == (
        0, expected, ""
    )


@pytest.mark.parametrize(
    "command,expected",
    [
        ("git push origin v1.0.0", "tag\n"),
        ("git push origin refs/tags/v1.0.0", "tag\n"),
        ("git push origin --tags", "tag\n"),
        (
            "git push origin v1.0.0:refs/heads/main",
            "block destination 'refs/heads/main' of refspec 'v1.0.0:refs/heads/main' is a protected branch\n",
        ),
    ],
)
def test_push_classifier_tag_only_rules(tmp_path, monkeypatch, command, expected):
    repo = _init_repo(tmp_path / "repo", "feat/x")
    monkeypatch.chdir(repo)
    module = _load_module("hook_dod_push_classify.py")
    assert _call(module, ["main", "feat/x", "main master"], command) == (0, expected, "")


def test_push_classifier_reuses_shared_modules_and_closes_on_error(monkeypatch):
    import hook_push_arg_parser
    import hook_shell_scan

    module = _load_module("hook_dod_push_classify.py")
    assert module.walk_push_args is hook_push_arg_parser.walk_push_args
    assert module.command_substitutions is hook_shell_scan.command_substitutions
    assert _call(module, [], "git push") == (1, "", "")

    def broken(_command):
        raise ValueError("boom")

    monkeypatch.setattr(module, "classify", broken)
    assert _call(module, ["main", "feat/x", "main master"], "git push") == (
        0, "block classifier error (ValueError)\n", ""
    )


def test_push_classifier_cli_reads_stdin(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "repo", "main")
    monkeypatch.chdir(repo)
    result = subprocess.run(
        [
            sys.executable,
            str(_LIB_DIR / "hook_dod_push_classify.py"),
            "main", "main", "main master",
        ],
        input=b"git push\n",
        capture_output=True,
        timeout=SCRIPT_TIMEOUT,
    )
    assert (result.returncode, result.stdout, result.stderr) == (0, b"onbranch main\n", b"")


def test_modules_deploy_flat_and_hook_uses_target_layout(tmp_path):
    repo = _init_repo(tmp_path / "repo", "main")
    hook = _deploy_hook(repo)
    deployed_lib = hook.parent / "lib"
    for filename in (*_MODULES, _POLICY_MODULE):
        deployed = deployed_lib / filename
        assert deployed.is_file()
        assert deployed.parent == deployed_lib
        assert filename in (deployed_lib / ".agent-meta-managed").read_text().splitlines()
    assert not (deployed_lib / "kernel").exists()

    blocked = _run_hook(hook, repo, "git push origin main")
    assert blocked.returncode == 2
    assert "Branch-Guard" in blocked.stderr
    allowed = _run_hook(hook, repo, "git push origin v1.0.0")
    assert allowed.returncode == 0


def test_hook_fails_closed_when_deployed_module_is_missing(tmp_path):
    repo = _init_repo(tmp_path / "repo", "feat/x")
    hook = _deploy_hook(repo)
    module = hook.parent / "lib" / "hook_dod_push_config.py"
    module.unlink()
    module.mkdir()
    result = _run_hook(hook, repo, "git push origin feat/x")
    assert result.returncode == 2
    assert "module" in result.stderr.lower()
    assert "Branch-Guard" not in result.stdout


def test_hook_fails_closed_without_python3(tmp_path):
    repo = _init_repo(tmp_path / "repo", "main")
    hook = _deploy_hook(repo)
    minimal_bin = tmp_path / "minimal-bin"
    minimal_bin.mkdir()
    for tool in ("bash", "cat", "dirname", "mkdir", "printf", "git"):
        found = shutil.which(tool)
        if found:
            (minimal_bin / tool).symlink_to(found)
    result = _run_hook(hook, repo, "git push", {"PATH": str(minimal_bin)})
    assert result.returncode == 2
    assert "python3" in result.stderr.lower()


def test_hook_classifier_budget_timeout_blocks(tmp_path):
    repo = _init_repo(tmp_path / "repo", "feat/x")
    hook = _deploy_hook(repo)
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    timeout = fake_bin / "timeout"
    timeout.write_text("#!/bin/sh\nexit 124\n", encoding="utf-8")
    timeout.chmod(0o755)
    env = _clean_env({"PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", "")})
    result = _run_hook(hook, repo, "git push origin feat/x", env)
    assert result.returncode == 2
    assert "exceeded 20s" in result.stderr


def test_hook_has_no_extracted_inline_python_and_has_version_changelog():
    source = _HOOK_PATH.read_text(encoding="utf-8")
    assert "# version: 2.7.0" in source
    assert "v2.7.0" in source
    assert "#1238c1" in source
    assert not re.search(r"python3\s+-c\b", source)
    assert not re.search(r"<<-?\s*(['\"])PY\1", source)
    assert not re.search(r"hook_push_arg_parser_py\s*;\s*hook_shell_scan_py", source)
    for filename in _MODULES:
        assert source.count("$SCRIPT_DIR/lib/" + filename) == 1
