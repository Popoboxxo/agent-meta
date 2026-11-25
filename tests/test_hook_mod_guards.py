"""Direct, CLI and deployment tests for the extracted guard-hook modules.

Issue #1238b2 moves the artifact-path classifier, the orchestrator git/destructive
classifier and the orchestrator identity/config readers into flat modules next to
``hook_common.sh``.  The security guard remains fail-closed when Python or a
deployed module is unavailable; the artifact routing convention keeps its
existing fail-open contract.
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
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
for _path in (_SCRIPTS_DIR, _LIB_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from lib.hook_plugins import sync_hook_lib  # noqa: E402
from lib.log import SyncLog  # noqa: E402

_BASH = shutil.which("bash") or "bash"
_MODULES = (
    "hook_guard_artifact.py",
    "hook_guard_scan.py",
    "hook_guard_policy.py",
)
_ORCHESTRATOR_MODULES = ("hook_guard_policy.py", "hook_guard_scan.py")
_INLINE_PY_ALLOWLIST = {}


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


def _write_matrix(root: Path, *, strict: bool = False, corrupt: bool = False) -> Path:
    meta = root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    path = meta / "artifact-locations.resolved.json"
    if corrupt:
        path.write_text("{broken", encoding="utf-8")
        return path
    path.write_text(
        json.dumps(
            {
                "strict": strict,
                "classes": [
                    {"name": "reviews", "path": "docs/reviews"},
                    {"name": "spikes", "path": "docs/spikes-2"},
                    {"name": "adr", "path": "docs/adr"},
                    {
                        "name": "project-docs",
                        "path": None,
                        "patterns": ["docs/ARCHITECTURE.md"],
                    },
                ],
                "legacy": ["docs/adr/[0-9][0-9][0-9][0-9]-*.md"],
                "unmanaged": ["docs/api/**"],
            }
        ),
        encoding="utf-8",
    )
    return path


def _artifact_verdict(root: Path, target: str, *, strict: bool = False):
    data = _write_matrix(root, strict=strict)
    return _call(
        _load_module("hook_guard_artifact.py"),
        [str(data), target, str(root), ".gitkeep .gitignore .keep"],
    )


def _write_allowlist(root: Path, data: dict) -> Path:
    meta = root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    path = meta / "auto-commit-allowlist.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _clean_env() -> dict:
    env = dict(os.environ)
    env.pop("AM_PROJECT_DIR", None)
    env.pop("CLAUDE_PROJECT_DIR", None)
    return env


def _deploy_lib(project_root: Path) -> Path:
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
    return project_root / ".runtime" / "hooks" / "lib"


def _deployed_orchestrator(project_root: Path) -> Path:
    lib = _deploy_lib(project_root)
    hooks = lib.parent
    shutil.copy(_HOOKS_DIR / "orchestrator-guard.sh", hooks)
    impl = (_HOOKS_DIR / "orchestrator-guard-impl.sh").read_text(encoding="utf-8")
    impl = impl.replace("{{AGENT_META_HOOK_AGENT_ID}}", "false")
    impl = impl.replace("{{AGENT_META_HOOK_ROLE_FIELD}}", "false")
    impl = impl.replace("{{AGENT_META_PROVIDER}}", "runtime")
    (hooks / "orchestrator-guard-impl.sh").write_text(impl, encoding="utf-8")
    return hooks / "orchestrator-guard.sh"


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
        "__future__", "fnmatch", "json", "os", "re", "shlex", "sys",
        "yaml", "hook_shell_scan",
    }
    for provider_name in ("Claude", "Gemini", "Codex", "Copilot", "OpenCode"):
        assert provider_name not in source


@pytest.mark.parametrize(
    "target,strict,expected",
    [
        ("docs/reviews/x.md", False, "ALLOW\n"),
        ("docs/ARCHITECTURE.md", True, "ALLOW\n"),
        ("docs/api/x.md", True, "ALLOW\n"),
        ("docs/conclusions/.gitkeep", True, "ALLOW\n"),
        ("README.md", True, "ALLOW\n"),
        ("../outside.md", True, "ALLOW\n"),
        ("docs/adr/0002-new.md", False, "BLOCK:"),
        ("docs/spikes/x.md", False, "WARN:"),
        ("docs/spikes/x.md", True, "BLOCK:"),
    ],
)
def test_artifact_classifier_core_routing(tmp_path, target, strict, expected):
    rc, stdout, stderr = _artifact_verdict(tmp_path, target, strict=strict)
    assert rc == 0
    assert stderr == ""
    assert stdout.startswith(expected)


def test_artifact_classifier_absolute_outside_and_corrupt_fail_open(tmp_path):
    outside = tmp_path.parent / "outside-artifact-target.md"
    rc, stdout, stderr = _artifact_verdict(tmp_path, str(outside), strict=True)
    assert (rc, stdout, stderr) == (0, "ALLOW\n", "")

    data = _write_matrix(tmp_path, corrupt=True)
    rc, stdout, stderr = _call(
        _load_module("hook_guard_artifact.py"),
        [str(data), "docs/spikes/x.md", str(tmp_path), ".gitkeep"],
    )
    assert rc == 0
    assert stdout.startswith("FAIL:artifact-path-guard: WARN:")
    assert "fail-open" in stdout
    assert stderr == ""


def test_artifact_classifier_missing_arguments_fail_closed():
    rc, stdout, _stderr = _call(_load_module("hook_guard_artifact.py"), [])
    assert rc == 1
    assert stdout == ""


@pytest.mark.parametrize(
    "command,expected",
    [
        ("git status", "none narrow none 1 0\n"),
        ("git commit -m x", "mutation narrow none 1 0\n"),
        ("git push origin main", "mutation broad none 1 0\n"),
        ("git push --force origin main", "destructive broad none 1 0\n"),
        ("git branch -D old", "destructive broad none 1 1\n"),
        ("git branch -D -f old", "destructive broad none 1 0\n"),
        ("git branch -D old; git reset --hard", "destructive broad none 1 0\n"),
        ("git add -A && echo ok", "mutation narrow none 0 0\n"),
        ("rm -rf /etc", "destructive narrow none 1 0\n"),
        (":(){ :|:& };:", "destructive forkbomb none 1 0\n"),
        ('echo "git push --force"', "none narrow none 0 0\n"),
        (
            "git update-ref --stdin <<EOF\ndelete refs/heads/main\nEOF",
            "destructive broad none 1 0\n",
        ),
        (
            "printf 'delete refs/heads/x\\n' | git update-ref --stdin",
            "destructive broad none 0 0\n",
        ),
    ],
)
def test_git_scan_core_classification(command, expected):
    rc, stdout, stderr = _call(
        _load_module("hook_guard_scan.py"), ["/work/project"], command
    )
    assert (rc, stdout, stderr) == (0, expected, "")


def test_git_scan_bom_and_relative_file_resolution(tmp_path):
    module = _load_module("hook_guard_scan.py")
    command = "git commit -m '\ufefffeat: x'"
    assert _call(module, [str(tmp_path)], command)[1] == (
        "mutation narrow message 1 0\n"
    )

    message = tmp_path / "message.txt"
    message.write_bytes(b"\xef\xbb\xbffeat: x\n")
    assert _call(module, [str(tmp_path)], "git commit -F message.txt")[1] == (
        "mutation narrow file 1 0\n"
    )
    message.write_bytes(b"feat: x\n")
    assert _call(module, [str(tmp_path)], "git commit -F message.txt")[1] == (
        "mutation narrow none 1 0\n"
    )


def test_git_scan_missing_arguments_fail_closed():
    rc, stdout, _stderr = _call(_load_module("hook_guard_scan.py"), [], "git status")
    assert rc == 1
    assert stdout == ""


@pytest.mark.parametrize(
    "command,expected",
    [
        ("#agent-meta:agent=git\ngit status", "git|\n"),
        ("\n  #agent-meta:agent=orchestrator id=scope-a  \necho x", "orchestrator|scope-a\n"),
        ("#agent-meta:agent=orchestrator id=..\necho x", "\n"),
        ("#agent-meta:agent=orchestrator id=Scope-A\necho x", "\n"),
        ("echo '#agent-meta:agent=git'\ngit status", "\n"),
    ],
)
def test_policy_sentinel_parser(command, expected):
    assert _call(_load_module("hook_guard_policy.py"), ["sentinel"], command) == (
        0, expected, ""
    )


def test_policy_allowlist_readers_fail_to_no_grant(tmp_path):
    module = _load_module("hook_guard_policy.py")
    path = _write_allowlist(
        tmp_path,
        {
            "mode": "auto",
            "eligible_roles": ["developer"],
            "authority_overrides": {"documenter": "direct"},
        },
    )
    assert _call(module, ["allowlist-mode", str(path)])[1] == "auto\n"
    assert _call(module, ["allowlist-eligible", str(path), "developer"])[1] == "1\n"
    assert _call(module, ["allowlist-eligible", str(path), "tester"])[1] == "0\n"
    assert _call(module, ["allowlist-grant", str(path), "documenter"])[1] == "1\n"
    assert _call(module, ["allowlist-grant", str(path), "developer"])[1] == "0\n"

    path.write_text("{broken", encoding="utf-8")
    assert _call(module, ["allowlist-mode", str(path)])[1] == "off\n"
    assert _call(module, ["allowlist-eligible", str(path), "developer"])[1] == "0\n"
    assert _call(module, ["allowlist-grant", str(path), "documenter"])[1] == "0\n"


def test_policy_strict_reader_provider_override_and_safe_fallback(tmp_path, monkeypatch):
    module = _load_module("hook_guard_policy.py")
    config = tmp_path / "project.yaml"
    config.write_text(
        "orchestrator:\n"
        "  mode: default\n"
        "  provider-overrides:\n"
        "    runtime:\n"
        "      mode: strict\n",
        encoding="utf-8",
    )
    assert _call(module, ["strict", str(config), "runtime"])[1] == "true\n"
    assert _call(module, ["strict", str(config), "other"])[1] == "false\n"

    config.write_text("orchestrator:\n  mode: strict\n", encoding="utf-8")
    monkeypatch.setitem(sys.modules, "yaml", None)
    rc, stdout, stderr = _call(module, ["strict", str(config), "runtime"])
    assert rc == 0
    assert stdout == "true\n"
    assert "PyYAML" in stderr
    assert "STRICT=true" in stderr

    config.write_text("orchestrator: {mode: strict}\n", encoding="utf-8")
    rc, stdout, _stderr = _call(module, ["strict", str(config), "runtime"])
    assert rc == 0
    assert stdout == "true\n"


def test_policy_ask_enabled_and_json_redaction(tmp_path, monkeypatch):
    module = _load_module("hook_guard_policy.py")
    config = tmp_path / "project.yaml"
    config.write_text(
        "orchestrator:\n  destructive-ask:\n    enabled: true\n", encoding="utf-8"
    )
    assert _call(module, ["ask-enabled", str(config)])[1] == "1\n"
    config.write_text("orchestrator:\n  destructive-ask: false\n", encoding="utf-8")
    assert _call(module, ["ask-enabled", str(config)])[1] == "0\n"
    monkeypatch.setitem(sys.modules, "yaml", None)
    assert _call(module, ["ask-enabled", str(config)])[1] == "0\n"

    rc, stdout, stderr = _call(
        module, ["ask-json", "git push --delete origin token=top-secret"]
    )
    assert rc == 0
    assert stderr == ""
    output = json.loads(stdout)
    assert output["hookSpecificOutput"]["permissionDecision"] == "ask"
    assert "top-secret" not in stdout
    assert "token=<redacted>" in stdout


@pytest.mark.parametrize("argv", [[], ["unknown"], ["strict"], ["allowlist-mode"]])
def test_policy_invalid_invocation_fails_closed(argv):
    rc, stdout, _stderr = _call(_load_module("hook_guard_policy.py"), argv, "")
    assert rc == 1
    assert stdout == ""


def test_modules_deploy_flat_and_artifact_hook_uses_deployed_module(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    deployed_lib = _deploy_lib(project)
    for filename in _MODULES:
        deployed = deployed_lib / filename
        assert deployed.is_file()
        assert deployed.parent == deployed_lib
        assert filename in (
            deployed_lib / ".agent-meta-managed"
        ).read_text(encoding="utf-8").splitlines()
    assert not (deployed_lib / "kernel").exists()

    hook = deployed_lib.parent / "artifact-path-guard.sh"
    shutil.copy(_HOOKS_DIR / "artifact-path-guard.sh", hook)
    _write_matrix(project, strict=True)
    result = _run_hook(
        hook,
        {"tool_name": "Write", "tool_input": {"file_path": "docs/spikes/x.md"}, "cwd": str(project)},
        project,
    )
    assert result.returncode == 2, result.stderr
    assert "docs/spikes-2" in result.stderr


def test_deployed_orchestrator_uses_modules_and_keeps_exit_codes(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    hook = _deployed_orchestrator(project)
    allowed = _run_hook(
        hook,
        {"tool_name": "Bash", "tool_input": {"command": "git status"}, "cwd": str(project)},
        project,
    )
    assert allowed.returncode == 0, allowed.stderr
    blocked = _run_hook(
        hook,
        {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}, "cwd": str(project)},
        project,
    )
    assert blocked.returncode == 2, blocked.stderr
    assert "Direct git mutations" in blocked.stderr


@pytest.mark.parametrize("filename", _ORCHESTRATOR_MODULES)
def test_orchestrator_missing_deployed_module_fails_closed(tmp_path, filename):
    project = tmp_path / "project"
    project.mkdir()
    hook = _deployed_orchestrator(project)
    (hook.parent / "lib" / filename).unlink()
    result = _run_hook(
        hook,
        {"tool_name": "Bash", "tool_input": {"command": "git status"}, "cwd": str(project)},
        project,
    )
    assert result.returncode == 2, result.stderr
    assert filename in result.stderr
    assert "Failing closed" in result.stderr


def test_orchestrator_without_python_still_fails_closed(tmp_path):
    minimal_bin = tmp_path / "bin"
    minimal_bin.mkdir()
    for tool in ("bash", "cat", "dirname", "mkdir", "date", "printf", "tr", "head"):
        found = shutil.which(tool)
        if found:
            (minimal_bin / tool).symlink_to(found)
    result = subprocess.run(
        [_BASH, str(_HOOKS_DIR / "orchestrator-guard.sh")],
        input=json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": "git status"}, "cwd": str(tmp_path)}
        ),
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env={"PATH": str(minimal_bin)},
        timeout=SCRIPT_TIMEOUT,
    )
    assert result.returncode == 2
    assert "python" in result.stderr.lower()


def test_guard_hook_inventory_versions_and_empty_allowlist():
    artifact = (_HOOKS_DIR / "artifact-path-guard.sh").read_text(encoding="utf-8")
    orchestrator = (_HOOKS_DIR / "orchestrator-guard-impl.sh").read_text(encoding="utf-8")
    assert "# version: 1.2.0" in artifact
    assert "# version: 1.17.0" in orchestrator
    assert "#1238b2" in artifact
    assert "#1238b2" in orchestrator

    inline_py = re.compile(
        r"""<<-?\s*["']?PY(EOF)?["']?|(?:\bpython3?\b|["']?\$_PY["']?)\s+-(?:\s|c\s)"""
    )
    found = {}
    for name, source in (
        ("artifact-path-guard.sh", artifact),
        ("orchestrator-guard-impl.sh", orchestrator),
    ):
        for lineno, line in enumerate(source.splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if inline_py.search(line):
                found[f"{name}:{lineno}"] = line.strip()
    assert found == _INLINE_PY_ALLOWLIST
