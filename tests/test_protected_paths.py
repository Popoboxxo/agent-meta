"""Protected-path containment tests for T27 / #1275a.

The deployed shell hook and the non-deployed kernel mirror must agree on
protected-path writes.  The hook remains a convention boundary; these tests
pin its observable block/allow decision, not a security guarantee.
"""
from __future__ import annotations

import ast
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.timeouts import SCRIPT_TIMEOUT

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOK_PATH = _REPO_ROOT / "hooks" / "1-generic" / "repo-containment.sh"
_IMPL_PATH = _REPO_ROOT / "hooks" / "1-generic" / "repo-containment-impl.sh"
_LIB_DIR = _REPO_ROOT / "hooks" / "1-generic" / "lib"
_BASH = shutil.which("bash") or "bash"

if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from kernel import containment, model  # noqa: E402


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    meta = root / ".meta-config"
    meta.mkdir(parents=True)
    (meta / "project.yaml").write_text(
        "repo_containment:\n"
        "  enabled: true\n"
        "  tmp-sink:\n"
        "    enabled: true\n"
        '    path: ".tmp"\n',
        encoding="utf-8",
    )
    return root


def _clean_env() -> dict:
    env = dict(os.environ)
    for name in (
        "AM_PROJECT_DIR",
        "CLAUDE_PROJECT_DIR",
        "AM_ALLOW_PROTECTED_WRITE",
        "ARTIFACT_SCRATCH_DIR",
    ):
        env.pop(name, None)
    return env


def _write_payload(path: str, root: Path, tool: str = "Write") -> dict:
    key = "notebook_path" if tool == "NotebookEdit" else "file_path"
    return {
        "tool_name": tool,
        "tool_input": {key: path},
        "cwd": str(root),
    }


def _bash_payload(command: str, root: Path) -> dict:
    return {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(root),
    }


def _run_hook(
    payload: dict,
    root: Path,
    *,
    override: str | None = None,
    project_dir: Path | None = None,
) -> subprocess.CompletedProcess:
    env = _clean_env()
    if override is not None:
        env["AM_ALLOW_PROTECTED_WRITE"] = override
    if project_dir is not None:
        env["AM_PROJECT_DIR"] = str(project_dir)
    return subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(root),
        env=env,
        timeout=SCRIPT_TIMEOUT,
    )


def _assert_protected_block(result: subprocess.CompletedProcess) -> None:
    assert result.returncode == 2, result.stderr
    assert "protected path" in result.stderr
    assert "AM_ALLOW_PROTECTED_WRITE=1" in result.stderr
    assert "not a security boundary" in result.stderr


def _gitmodules(root: Path, content: str) -> None:
    (root / ".gitmodules").write_text(content, encoding="utf-8")


@pytest.mark.parametrize("tool", ["Write", "Edit", "NotebookEdit"])
@pytest.mark.parametrize("protected", ["external/foo", ".agent-meta/foo"])
def test_write_tools_block_default_protected_paths(tmp_path, tool, protected):
    root = _project(tmp_path)
    result = _run_hook(_write_payload(protected, root, tool), root)
    _assert_protected_block(result)


@pytest.mark.parametrize("tool", ["Write", "Edit", "NotebookEdit"])
def test_write_tools_allow_docs(tmp_path, tool):
    root = _project(tmp_path)
    result = _run_hook(_write_payload("docs/foo", root, tool), root)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "printf x > external/out.txt",
        "printf x >> .agent-meta/out.txt",
        "touch external/new.txt",
        "cp source.txt external/copied.txt",
    ],
)
def test_bash_write_targets_block_default_protected_paths(tmp_path, command):
    root = _project(tmp_path)
    result = _run_hook(_bash_payload(command, root), root)
    _assert_protected_block(result)
    assert "detected in Bash command" in result.stderr


def test_without_gitmodules_only_defaults_are_protected(tmp_path):
    root = _project(tmp_path)
    allowed = _run_hook(_write_payload("vendor/lib/file.txt", root), root)
    assert allowed.returncode == 0, allowed.stderr
    _assert_protected_block(_run_hook(_write_payload("external/file.txt", root), root))


def test_all_gitmodules_paths_are_protected(tmp_path):
    root = _project(tmp_path)
    _gitmodules(
        root,
        '[submodule "foo"]\n'
        "  path = foo\n"
        "  url = https://example.invalid/foo\n"
        '# path = ignored/comment\n'
        '[submodule "shared"]\n'
        '  path="vendor/shared lib"\n'
        "  url = https://example.invalid/shared\n"
        '[submodule "unquoted"]\n'
        "  path = vendor/unquoted lib\n"
        "  url = https://example.invalid/unquoted\n",
    )
    for target in ("foo/a", "vendor/shared lib/a", "vendor/unquoted lib/a"):
        _assert_protected_block(_run_hook(_write_payload(target, root), root))
        command = "printf x > " + shlex.quote(target)
        _assert_protected_block(_run_hook(_bash_payload(command, root), root))


def test_gitmodules_prefix_collision_is_allowed(tmp_path):
    root = _project(tmp_path)
    _gitmodules(root, '[submodule "foo"]\n  path = foo\n')
    result = _run_hook(_write_payload("foobar/a", root), root)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("protected", ["externalized/a", ".agent-meta-backup/a"])
def test_default_prefix_collision_is_allowed(tmp_path, protected):
    root = _project(tmp_path)
    result = _run_hook(_write_payload(protected, root), root)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("override", ["", "0", "true", "yes"])
def test_override_requires_exact_value_one(tmp_path, override):
    root = _project(tmp_path)
    result = _run_hook(
        _write_payload("external/foo", root), root, override=override
    )
    _assert_protected_block(result)


@pytest.mark.parametrize("tool", ["Write", "Edit", "NotebookEdit"])
def test_override_allows_protected_write_tools(tmp_path, tool):
    root = _project(tmp_path)
    result = _run_hook(
        _write_payload("external/foo", root, tool), root, override="1"
    )
    assert result.returncode == 0, result.stderr


def test_override_allows_protected_bash_write(tmp_path):
    root = _project(tmp_path)
    result = _run_hook(
        _bash_payload("printf x > external/out.txt", root), root, override="1"
    )
    assert result.returncode == 0, result.stderr


def test_override_does_not_widen_the_jail_root(tmp_path):
    root = _project(tmp_path)
    outside = root.parent / "outside.txt"
    result = _run_hook(
        _write_payload(str(outside), root), root, override="1", project_dir=root
    )
    assert result.returncode == 2, result.stderr
    assert "outside the repository root" in result.stderr
    assert "protected path" not in result.stderr


@pytest.mark.skipif(os.name == "nt", reason="symlink semantics differ on Windows")
def test_override_does_not_allow_symlink_escape(tmp_path):
    root = _project(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "escape").symlink_to(outside, target_is_directory=True)
    result = _run_hook(
        _write_payload("escape/file.txt", root), root, override="1"
    )
    assert result.returncode == 2, result.stderr
    assert "outside the repository root" in result.stderr


@pytest.mark.skipif(os.name == "nt", reason="symlink semantics differ on Windows")
def test_symlink_into_protected_path_is_blocked(tmp_path):
    root = _project(tmp_path)
    (root / "external").mkdir()
    (root / "alias").symlink_to(root / "external", target_is_directory=True)
    result = _run_hook(_write_payload("alias/file.txt", root), root)
    _assert_protected_block(result)


def test_protected_path_wins_over_enabled_sink(tmp_path):
    root = _project(tmp_path)
    _gitmodules(root, '[submodule "scratch-vendor"]\n  path = .tmp/vendor\n')
    result = _run_hook(_write_payload(".tmp/vendor/file.txt", root), root)
    _assert_protected_block(result)


def test_override_does_not_disable_the_sink_rule(tmp_path):
    root = _project(tmp_path)
    config = root / ".meta-config" / "project.yaml"
    config.write_text(
        "repo_containment:\n"
        "  enabled: true\n"
        "  tmp-sink:\n"
        "    enabled: false\n"
        '    path: ".tmp"\n',
        encoding="utf-8",
    )
    _gitmodules(root, '[submodule "scratch-vendor"]\n  path = .tmp/vendor\n')
    result = _run_hook(
        _write_payload(".tmp/vendor/file.txt", root), root, override="1"
    )
    assert result.returncode == 2, result.stderr
    assert "DISABLED tmp-sink" in result.stderr


def test_unsafe_gitmodules_paths_do_not_widen_protection(tmp_path):
    root = _project(tmp_path)
    _gitmodules(
        root,
        '[submodule "escape"]\n  path = ../escape\n'
        '[submodule "root"]\n  path = .\n',
    )
    result = _run_hook(_write_payload("escape/file.txt", root), root)
    assert result.returncode == 0, result.stderr
    _assert_protected_block(_run_hook(_write_payload("external/file.txt", root), root))


def test_agent_meta_read_exception_is_unchanged(tmp_path):
    root = _project(tmp_path)
    read = _run_hook(
        {
            "tool_name": "Read",
            "tool_input": {"file_path": ".agent-meta/config.yaml"},
            "cwd": str(root),
        },
        root,
    )
    assert read.returncode == 0, read.stderr
    bash_read = _run_hook(_bash_payload("cat .agent-meta/config.yaml", root), root)
    assert bash_read.returncode == 0, bash_read.stderr
    event = model.NormEvent(
        tool_kind="read",
        path=".agent-meta/config.yaml",
        cwd=str(root),
        project_dir=str(root),
    )
    assert containment.check_containment(event) is None


@pytest.mark.parametrize(
    "path,modules,blocked",
    [
        pytest.param("external/foo", None, True, id="default-external"),
        pytest.param(".agent-meta/foo", None, True, id="default-meta"),
        pytest.param("docs/foo", None, False, id="docs"),
        pytest.param("externalized/foo", None, False, id="external-prefix"),
        pytest.param(
            "foo/a",
            '[submodule "foo"]\n  path = foo\n',
            True,
            id="gitmodule",
        ),
        pytest.param(
            "foobar/a",
            '[submodule "foo"]\n  path = foo\n',
            False,
            id="gitmodule-prefix",
        ),
    ],
)
def test_hook_and_kernel_have_the_same_path_and_redirect_decision(
    tmp_path, monkeypatch, path, modules, blocked
):
    monkeypatch.delenv("AM_ALLOW_PROTECTED_WRITE", raising=False)
    root = _project(tmp_path)
    if modules is not None:
        _gitmodules(root, modules)

    write = _run_hook(_write_payload(path, root), root)
    redirect = _run_hook(
        _bash_payload("printf x > " + shlex.quote(path), root), root
    )
    event = model.NormEvent(
        tool_kind="write", path=path, cwd=str(root), project_dir=str(root)
    )
    kernel = containment.check_containment(event)

    assert kernel is not None
    expected = "deny" if blocked else "allow"
    assert kernel.outcome == expected
    assert (write.returncode == 2) is blocked, write.stderr
    assert (redirect.returncode == 2) is blocked, redirect.stderr


@pytest.mark.parametrize(
    "path,blocked",
    [
        pytest.param("external/foo", False, id="protected-override"),
        pytest.param("../outside.txt", True, id="outside-root"),
    ],
)
def test_override_decision_matches_kernel(tmp_path, monkeypatch, path, blocked):
    monkeypatch.setenv("AM_ALLOW_PROTECTED_WRITE", "1")
    root = _project(tmp_path)
    write = _run_hook(_write_payload(path, root), root, override="1")
    redirect = _run_hook(
        _bash_payload("printf x > " + shlex.quote(path), root), root, override="1"
    )
    event = model.NormEvent(
        tool_kind="write", path=path, cwd=str(root), project_dir=str(root)
    )
    kernel = containment.check_containment(event)
    assert kernel is not None
    assert (kernel.outcome == "deny") is blocked
    assert (write.returncode == 2) is blocked, write.stderr
    assert (redirect.returncode == 2) is blocked, redirect.stderr


def test_hook_version_changelog_and_python39_static_contract():
    source = _IMPL_PATH.read_text(encoding="utf-8")
    assert "# version: 1.9.0" in source
    assert "# changelog: 1.9.0:" in source
    assert "#1275a" in source
    for path in (
        _LIB_DIR / "hook_containment_path.py",
        _LIB_DIR / "kernel" / "containment.py",
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"), feature_version=(3, 9))
        assert tree is not None
        text = path.read_text(encoding="utf-8")
        for provider_name in ("Claude", "Gemini", "Codex", "Copilot", "OpenCode"):
            assert provider_name not in text
