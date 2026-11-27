"""Direct and deployment tests for the Python modules behind hook_common.sh.

Issue #1238a extracts the three executable ``cat <<'PY'`` emitters into flat,
importable modules while preserving their emitted source byte-for-byte.
"""
from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib.util
import inspect
import io
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.timeouts import SCRIPT_TIMEOUT

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.hook_plugins import sync_hook_lib  # noqa: E402
from lib.log import SyncLog  # noqa: E402

_LIB_DIR = _REPO_ROOT / "hooks" / "1-generic" / "lib"
_LIB_PATH = _LIB_DIR / "hook_common.sh"
_BASH = shutil.which("bash") or "bash"

_MODULES = {
    "hook_shell_scan_py": (
        "hook_shell_scan.py",
        "12e090a7b35e083c37bdfd87f6449aec5a4caa3b2a9227f503eb805e43ae6a3f",
    ),
    "hook_shell_resolver_py": (
        "hook_shell_resolver.py",
        "98e7f79a986cf0c8d82672f41350fb80c471fda511bb7e463483e4c6edbe2c68",
    ),
    "hook_push_arg_parser_py": (
        "hook_push_arg_parser.py",
        "9f2c67f2db64168a3c11a23d1c300dcb961679a08756de8bbb4ab7f6f09fac0f",
    ),
}


def _load_module(filename: str):
    path = _LIB_DIR / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _main_output(module, argv=None, stdin: str = "") -> bytes:
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        rc = module.main([] if argv is None else argv, stdin)
    assert rc == 0
    return stream.getvalue().encode("utf-8")


def _shell_output(lib_path: Path, function: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_BASH, "-c", 'source "$1"; "$2"', _BASH, str(lib_path), function],
        capture_output=True,
        timeout=SCRIPT_TIMEOUT,
    )


@pytest.mark.parametrize("function,module_info", _MODULES.items())
def test_module_main_contract_and_byte_identical_source(function, module_info):
    filename, expected_hash = module_info
    module = _load_module(filename)
    signature = inspect.signature(module.main)
    assert list(signature.parameters) == ["argv", "stdin"]
    assert signature.return_annotation is int

    output = _main_output(module, ["ignored"], "ignored stdin\n")
    assert hashlib.sha256(output).hexdigest() == expected_hash
    compile(output, filename, "exec")


@pytest.mark.parametrize("function,module_info", _MODULES.items())
def test_module_cli_and_shell_emitter_match(function, module_info):
    filename, expected_hash = module_info
    cli = subprocess.run(
        [sys.executable, str(_LIB_DIR / filename)],
        input=b"ignored stdin\n",
        capture_output=True,
        timeout=SCRIPT_TIMEOUT,
    )
    assert cli.returncode == 0, cli.stderr
    assert cli.stderr == b""
    assert hashlib.sha256(cli.stdout).hexdigest() == expected_hash

    shell = _shell_output(_LIB_PATH, function)
    assert shell.returncode == 0, shell.stderr
    assert shell.stderr == b""
    assert shell.stdout == cli.stdout


def test_shell_scanner_direct_logic():
    scan = _load_module("hook_shell_scan.py")
    command = "cat <<'EOF'\n:(){ :|:& };:\nEOF\ngit push --force"
    statements, cleaned = scan.split_shell_statements_and_clean(command)
    assert statements == [
        ("cat <<'EOF'", [":(){ :|:& };:"]),
        ("git push --force", []),
    ]
    assert ":(){ :|:& };:" not in cleaned
    assert scan.is_fork_bomb(":(){ :|:& };:")
    assert not scan.is_fork_bomb(scan.strip_quoted("echo ':(){ :|:& };:'"))
    assert scan.split_shell_statements_with_ops("cd /tmp && touch x") == [
        ("cd /tmp", [], "&&"),
        ("touch x", [], "\n"),
    ]
    assert scan.split_shell_statements('echo "$(git push --force)"') == [
        ('echo "$(git push --force)"', []),
        ("git push --force", []),
    ]


def test_shell_resolver_direct_logic():
    resolver = _load_module("hook_shell_resolver.py")
    assert resolver.command_start(["timeout", "5", "--", "git", "push"]) == 3
    assert resolver.command_start(["sudo", "-u", "me", "git", "push"]) == 3
    assert resolver.command_start(["X=1", "Y=2"]) == 2
    assert resolver.command_start(["case", "x", "in", "x", ")", "git", "push"]) == 5
    assert resolver.command_start(["f", "()", "{", "git", "push"]) == 3


def test_push_arg_parser_direct_logic():
    parser = _load_module("hook_push_arg_parser.py")
    assert parser.walk_push_args(
        ["-fv", "-o", "--tags", "origin", "--", "-oZ"],
        {"--push-option"},
    ) == (
        ["origin", "-oZ"],
        [
            ("-f", None, "-fv"),
            ("-v", None, "-fv"),
            ("-o", "--tags", "-o"),
        ],
    )
    assert parser.walk_push_args(
        ["--push-option=x", "--push-option", "y", "origin"],
        {"--push-option"},
    ) == (
        ["origin"],
        [
            ("--push-option", "x", "--push-option=x"),
            ("--push-option", "y", "--push-option"),
        ],
    )


@pytest.mark.parametrize("function", _MODULES)
def test_emitters_fail_closed_without_python(tmp_path, function):
    empty_path = tmp_path / "empty-path"
    empty_path.mkdir()
    env = dict(os.environ, PATH=str(empty_path))
    result = subprocess.run(
        [_BASH, "-c", 'source "$1"; "$2"', _BASH, str(_LIB_PATH), function],
        capture_output=True,
        env=env,
        timeout=SCRIPT_TIMEOUT,
    )
    assert result.returncode == 1
    assert result.stdout == b""
    assert result.stderr == b""


def _deploy_lib(project_root: Path) -> Path:
    provider = "runtime"
    provider_config = {
        provider: {
            "hooks_dir": ".runtime/hooks",
            "has_hooks": True,
            "hook_protocol": "claude-code-json",
        }
    }
    sync_hook_lib(
        _REPO_ROOT,
        project_root,
        {"platforms": []},
        SyncLog(),
        dry_run=False,
        provider=provider,
        provider_config=provider_config,
    )
    return project_root / ".runtime" / "hooks" / "lib"


def test_modules_deploy_flat_and_emitters_work_from_target_layout(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    deployed_lib = _deploy_lib(project_root)

    for filename, expected_hash in _MODULES.values():
        deployed = deployed_lib / filename
        assert deployed.is_file()
        assert deployed.parent == deployed_lib
        function = {
            "hook_shell_scan.py": "hook_shell_scan_py",
            "hook_shell_resolver.py": "hook_shell_resolver_py",
            "hook_push_arg_parser.py": "hook_push_arg_parser_py",
        }[filename]
        result = _shell_output(deployed_lib / "hook_common.sh", function)
        assert result.returncode == 0, result.stderr
        assert hashlib.sha256(result.stdout).hexdigest() == expected_hash

    managed = (deployed_lib / ".agent-meta-managed").read_text(encoding="utf-8").splitlines()
    for filename, _expected_hash in _MODULES.values():
        assert filename in managed
    assert not (deployed_lib / "kernel").exists()


def test_hook_common_inventory_and_version():
    source = _LIB_PATH.read_text(encoding="utf-8")
    assert "# version: 1.13.0" in source
    assert "v1.13.0" in source
    assert "#1238a" in source
    assert not re.search(r"(?m)^\s*cat\s+<<-?\s*(['\"])PY\1", source)
    for filename, _expected_hash in _MODULES.values():
        assert source.count("$module_dir/" + filename) == 1


@pytest.mark.parametrize("filename", [info[0] for info in _MODULES.values()])
def test_modules_are_python39_stdlib_only_and_provider_neutral(filename):
    source = (_LIB_DIR / filename).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=filename, feature_version=(3, 9))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports <= {"os", "re", "sys", "pathlib"}
    assert "provider" not in source.lower()
