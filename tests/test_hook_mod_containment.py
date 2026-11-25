"""Direct, CLI and deployment tests for repo-containment Python modules.

Issue #1238b1 moves the three containment heredocs and the Bash write-target
``-c`` block into flat modules next to ``hook_common.sh``.  The hook remains
fail-closed when Python or a deployed module is unavailable (#595).
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

import pytest

from tests.timeouts import SCRIPT_TIMEOUT

_REPO_ROOT = Path(__file__).resolve().parent.parent
_LIB_DIR = _REPO_ROOT / "hooks" / "1-generic" / "lib"
_IMPL_PATH = _REPO_ROOT / "hooks" / "1-generic" / "repo-containment-impl.sh"
_HOOK_PATH = _REPO_ROOT / "hooks" / "1-generic" / "repo-containment.sh"
_BASH = shutil.which("bash") or "bash"
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from lib.hook_plugins import sync_hook_lib  # noqa: E402
from lib.log import SyncLog  # noqa: E402

_MODULES = (
    "hook_containment_config.py",
    "hook_containment_path.py",
    "hook_containment_shell.py",
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


def _values(stdout: str) -> dict:
    return dict(line.split("=", 1) for line in stdout.splitlines() if "=" in line)


def _project(tmp_path: Path, config: str = "repo_containment:\n  enabled: true\n") -> Path:
    root = tmp_path / "project"
    meta = root / ".meta-config"
    meta.mkdir(parents=True)
    (meta / "project.yaml").write_text(config, encoding="utf-8")
    return root


def _clean_env() -> dict:
    env = dict(os.environ)
    env.pop("AM_PROJECT_DIR", None)
    env.pop("CLAUDE_PROJECT_DIR", None)
    env.pop("ARTIFACT_SCRATCH_DIR", None)
    return env


def _deploy_hook(tmp_path: Path) -> Path:
    root = _project(tmp_path)
    provider = "runtime"
    sync_hook_lib(
        _REPO_ROOT,
        root,
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
    hooks = root / ".runtime" / "hooks"
    shutil.copy(_HOOK_PATH, hooks / "repo-containment.sh")
    shutil.copy(_IMPL_PATH, hooks / "repo-containment-impl.sh")
    return hooks / "repo-containment.sh"


def _run_hook(hook: Path, payload: dict, cwd: Path, env=None):
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
def test_module_main_contract_python39_and_dependencies(filename):
    module = _load_module(filename)
    signature = inspect.signature(module.main)
    assert list(signature.parameters) == ["argv", "stdin"]
    assert signature.parameters["argv"].annotation == list[str]
    assert signature.parameters["stdin"].annotation is str
    assert signature.return_annotation is int

    source = (_LIB_DIR / filename).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=filename, feature_version=(3, 9))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports <= {
        "os", "re", "sys", "json", "posixpath", "shlex", "yaml",
        "hook_shell_scan", "hook_shell_resolver",
    }
    for provider_name in ("Claude", "Gemini", "Codex", "Copilot", "OpenCode"):
        assert provider_name not in source


def test_config_defaults_and_canonical_sink(tmp_path, monkeypatch):
    monkeypatch.delenv("ARTIFACT_SCRATCH_DIR", raising=False)
    root = _project(
        tmp_path,
        'repo_containment:\n  enabled: true\n  tmp-sink:\n    enabled: true\n'
        '    path: "scratch\\\\out"\n',
    )
    rc, stdout, stderr = _call(
        _load_module("hook_containment_config.py"),
        [str(root / ".meta-config" / "project.yaml"), ""],
    )
    assert rc == 0
    assert _values(stdout) == {
        "ENABLED": "1",
        "SINK_ENABLED": "1",
        "SINK_PATH": "scratch/out",
        "SINK_REJECTED": "0",
        "SCRATCH_PATH": "scratch/out",
    }
    assert "not found" in stderr


def test_config_provider_override_and_safe_side_types(tmp_path, monkeypatch):
    monkeypatch.delenv("ARTIFACT_SCRATCH_DIR", raising=False)
    config = (
        "repo_containment:\n"
        "  enabled: false\n"
        "  provider-overrides:\n"
        "    runtime:\n"
        "      enabled: true\n"
        "    unsafe:\n"
        "      enabled: 'false'\n"
    )
    root = _project(tmp_path, config)
    module = _load_module("hook_containment_config.py")
    path = str(root / ".meta-config" / "project.yaml")
    assert _values(_call(module, [path, "runtime"])[1])["ENABLED"] == "1"
    assert _values(_call(module, [path, ""])[1])["ENABLED"] == "0"
    assert _values(_call(module, [path, "unsafe"])[1])["ENABLED"] == "1"
    assert _values(_call(module, [path, "other"])[1])["ENABLED"] == "0"


@pytest.mark.parametrize("sink", ['"./."', '"C:\\\\x"', '"../x"', '".claude/x"', '"NUL"'])
def test_config_unsafe_sink_falls_back_to_tmp(tmp_path, monkeypatch, sink):
    monkeypatch.delenv("ARTIFACT_SCRATCH_DIR", raising=False)
    root = _project(
        tmp_path,
        "repo_containment:\n  enabled: true\n  tmp-sink:\n    enabled: true\n"
        f"    path: {sink}\n",
    )
    rc, stdout, _stderr = _call(
        _load_module("hook_containment_config.py"),
        [str(root / ".meta-config" / "project.yaml"), ""],
    )
    assert rc == 0
    values = _values(stdout)
    assert values["SINK_PATH"] == ".tmp"
    assert values["SINK_REJECTED"] == "1"
    assert values["SCRATCH_PATH"] == ".tmp"


def test_config_scratch_precedence_env_then_matrix_then_legacy(tmp_path, monkeypatch):
    root = _project(
        tmp_path,
        'repo_containment:\n  enabled: true\n  tmp-sink:\n    path: "legacy"\n',
    )
    matrix = root / ".meta-config" / "artifact-locations.resolved.json"
    matrix.write_text(
        json.dumps({"classes": {"scratch": {"path": "matrix"}}}), encoding="utf-8"
    )
    module = _load_module("hook_containment_config.py")
    argv = [str(root / ".meta-config" / "project.yaml"), ""]

    monkeypatch.setenv("ARTIFACT_SCRATCH_DIR", "env-sink")
    values = _values(_call(module, argv)[1])
    assert values["SINK_PATH"] == "legacy"
    assert values["SCRATCH_PATH"] == "env-sink"

    monkeypatch.setenv("ARTIFACT_SCRATCH_DIR", "../escape")
    rc, stdout, stderr = _call(module, argv)
    assert rc == 0
    assert _values(stdout)["SCRATCH_PATH"] == "matrix"
    assert "unsafe scratch path" in stderr

    monkeypatch.delenv("ARTIFACT_SCRATCH_DIR")
    matrix.write_text(
        json.dumps({"classes": [{"name": "scratch", "path": "list-matrix"}]}),
        encoding="utf-8",
    )
    assert _values(_call(module, argv)[1])["SCRATCH_PATH"] == "list-matrix"

    matrix.write_text("{broken", encoding="utf-8")
    assert _values(_call(module, argv)[1])["SCRATCH_PATH"] == "legacy"


def test_config_unreadable_yaml_stays_enabled_and_cannot_widen_sink(tmp_path, monkeypatch):
    root = _project(tmp_path, "repo_containment:\n  enabled: false\n")
    monkeypatch.setenv("ARTIFACT_SCRATCH_DIR", "env-sink")
    module = _load_module("hook_containment_config.py")
    argv = [str(root / ".meta-config" / "project.yaml"), ""]

    monkeypatch.setitem(sys.modules, "yaml", None)
    rc, stdout, stderr = _call(module, argv)
    assert rc == 0
    assert _values(stdout) == {
        "ENABLED": "1",
        "SINK_ENABLED": "1",
        "SINK_PATH": ".tmp",
        "SINK_REJECTED": "0",
        "SCRATCH_PATH": ".tmp",
    }
    assert "PyYAML" in stderr
    assert "NOT honoured" in stderr

    monkeypatch.undo()
    monkeypatch.setenv("ARTIFACT_SCRATCH_DIR", "env-sink")
    (root / ".meta-config" / "project.yaml").write_text(": [broken", encoding="utf-8")
    rc, stdout, stderr = _call(module, argv)
    assert rc == 0
    assert _values(stdout)["ENABLED"] == "1"
    assert _values(stdout)["SCRATCH_PATH"] == ".tmp"
    assert "containment stays ENABLED" in stderr


def test_config_missing_arguments_fail_closed():
    rc, stdout, _stderr = _call(_load_module("hook_containment_config.py"), [])
    assert rc == 1
    assert stdout == ""


def test_path_inside_outside_relative_and_empty(tmp_path):
    root = _project(tmp_path)
    workdir = root / "pkg"
    workdir.mkdir()
    module = _load_module("hook_containment_path.py")

    def verdict(target, sink_enabled="1", sink_path=".tmp"):
        return _call(module, [str(root), str(workdir), sink_enabled, sink_path, target])

    assert verdict("module.py")[:2] == (0, "ALLOW\n")
    assert verdict("../module.py")[:2] == (0, "ALLOW\n")
    assert verdict("../../../etc/passwd")[:2] == (0, "BLOCK\n")
    assert verdict("")[:2] == (0, "BLOCK\n")
    assert verdict(str(root / ".tmp" / "x"))[:2] == (0, "ALLOW\n")
    assert verdict(str(root / ".tmp" / "x"), "0")[:2] == (0, "BLOCK_SINK\n")
    assert verdict(str(root / "scratch" / "x"), "0", "scratch")[:2] == (
        0, "BLOCK_SINK\n"
    )


@pytest.mark.skipif(os.name == "nt", reason="symlink semantics differ on Windows")
def test_path_symlink_escape_is_blocked(tmp_path):
    root = _project(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "escape").symlink_to(outside, target_is_directory=True)
    rc, stdout, _stderr = _call(
        _load_module("hook_containment_path.py"),
        [str(root), str(root), "1", ".tmp", "escape/x.py"],
    )
    assert (rc, stdout) == (0, "BLOCK\n")


def test_path_missing_arguments_fail_closed():
    rc, stdout, _stderr = _call(_load_module("hook_containment_path.py"), [])
    assert rc == 1
    assert stdout == ""


@pytest.mark.parametrize(
    "command,expected",
    [
        ("ls -la", []),
        ("touch /etc/target", ["/etc/target"]),
        ("echo x > notes.md", ["{root}/notes.md"]),
        ("cp source /etc/target -v", ["/etc/target"]),
        ("sed -Ei 's/a/b/' /etc/target", ["/etc/target"]),
        ("timeout 5 -- touch /etc/target", ["/etc/target"]),
        ("cd /etc && touch target", ["/etc/target"]),
        ("echo \"$(touch /etc/target)\"", ["/etc/target"]),
        ("git clone repo /etc/target", ["/etc/target"]),
        ("echo x > /dev/null", []),
        ("cd \"$DIR\" && touch target", ["\x01target"]),
        (
            "cat > notes.md <<'EOF'\n> /etc/prose\nEOF\ntouch /etc/after",
            ["{root}/notes.md", "/etc/after"],
        ),
    ],
)
def test_shell_detector_targets(tmp_path, command, expected):
    root = _project(tmp_path)
    rc, stdout, stderr = _call(
        _load_module("hook_containment_shell.py"), [str(root)], command
    )
    assert rc == 0, stderr
    assert stdout.splitlines() == [item.format(root=root) for item in expected]


def test_shell_detector_known_variables(tmp_path, monkeypatch):
    root = _project(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("AM_PROJECT_DIR", str(root))
    module = _load_module("hook_containment_shell.py")
    rc, stdout, stderr = _call(
        module, [str(root)], "touch $HOME/x ${AM_PROJECT_DIR}/y ~/z"
    )
    assert rc == 0, stderr
    assert stdout.splitlines() == [
        str(tmp_path / "home" / "x"), str(root / "y"), str(tmp_path / "home" / "z")
    ]


@pytest.mark.parametrize(
    "filename,argv,stdin",
    [
        ("hook_containment_config.py", ["missing.yaml", ""], ""),
        ("hook_containment_path.py", ["/tmp", "/tmp", "1", ".tmp", "x"], ""),
        ("hook_containment_shell.py", ["/tmp"], "touch /etc/x\n"),
    ],
)
def test_module_cli_matches_direct_call(filename, argv, stdin):
    direct = _call(_load_module(filename), argv, stdin)
    cli = subprocess.run(
        [sys.executable, str(_LIB_DIR / filename), *argv],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=SCRIPT_TIMEOUT,
    )
    assert (cli.returncode, cli.stdout, cli.stderr) == direct


def test_modules_deploy_flat_and_hook_uses_them(tmp_path):
    hook = _deploy_hook(tmp_path)
    root = hook.parent.parent.parent
    lib = hook.parent / "lib"
    for filename in _MODULES:
        deployed = lib / filename
        assert deployed.is_file()
        assert deployed.parent == lib
        assert filename in (lib / ".agent-meta-managed").read_text().splitlines()
    assert not (lib / "kernel").exists()

    allowed = _run_hook(
        hook, {"tool_name": "Write", "tool_input": {"file_path": str(root / "x.py")},
               "cwd": str(root)}, root,
    )
    assert allowed.returncode == 0, allowed.stderr
    bash = _run_hook(
        hook, {"tool_name": "Bash", "tool_input": {"command": "ls -la"},
               "cwd": str(root)}, root,
    )
    assert bash.returncode == 0, bash.stderr


@pytest.mark.parametrize(
    "filename,tool,payload",
    [
        ("hook_containment_config.py", "Write", {"file_path": "x.py"}),
        ("hook_containment_path.py", "Write", {"file_path": "x.py"}),
        ("hook_containment_shell.py", "Bash", {"command": "ls -la"}),
    ],
)
def test_missing_deployed_module_fails_closed(tmp_path, filename, tool, payload):
    hook = _deploy_hook(tmp_path)
    root = hook.parent.parent.parent
    (hook.parent / "lib" / filename).unlink()
    result = _run_hook(
        hook, {"tool_name": tool, "tool_input": payload, "cwd": str(root)}, root
    )
    assert result.returncode == 2, result.stdout
    assert "REPO_CONTAINMENT" in result.stderr


def test_missing_python_fails_closed(tmp_path):
    root = _project(tmp_path)
    empty_path = tmp_path / "empty-path"
    empty_path.mkdir()
    for utility in ("dirname", "cat", "bash", "grep", "head", "sed"):
        (empty_path / utility).symlink_to(shutil.which(utility))
    env = _clean_env()
    env["PATH"] = str(empty_path)
    result = _run_hook(
        _HOOK_PATH,
        {"tool_name": "Write", "tool_input": {"file_path": str(root / "x.py")},
         "cwd": str(root)},
        root,
        env,
    )
    assert result.returncode == 2
    assert "no python/python3 interpreter" in result.stderr
    assert "Failing closed" in result.stderr


def test_shell_inventory_version_and_inline_python_allowlist():
    source = _IMPL_PATH.read_text(encoding="utf-8")
    assert "# version: 1.9.0" in source
    assert "1.9.0" in source
    assert "#1238b1" in source
    assert not re.search(r"(?m)^\s*(?:cat\s+)?<<-?\s*(['\"])PYEOF?\1", source)
    inline = [
        line for line in source.splitlines()
        if not line.lstrip().startswith("#") and re.search(r'"\$_PY"\s+-c\s', line)
    ]
    assert inline == [
        '  "$_PY" -c \'import os, sys; print(os.path.realpath(sys.argv[1]))\' "$1" 2>/dev/null'
    ]
    for filename in _MODULES:
        assert source.count("$SCRIPT_DIR/lib/" + filename) == 1
