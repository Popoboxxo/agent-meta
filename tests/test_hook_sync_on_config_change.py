"""Focused tests for hooks/1-generic/sync-on-config-change.sh (MB-3).

The hook used to hand the change to a lifecycle wrapper that only queued a
pending task. MB-3 (docs/plans/systemaudit-umsetzungsplan-2026-11-25.md) makes
the hook do what its name says: run the project's real ``scripts/sync.py`` for
a successful Write/Edit of ``.meta-config/project.yaml``.

Every test runs the shipped hook as a real subprocess and judges it by its
exit code plus the observable effect. ``sync.py`` itself is replaced by a stub
that records argv/cwd/guard env into a marker file, so no test touches the
repository or the network. The contract under test:

* a successful Write/Edit of the config triggers exactly one sync.py run,
  invoked cwd-independently with the absolute config path and the project root
  as cwd, in every documented agent-meta layout (`.agent-meta`,
  `external/agent-meta`, the source layout and the deployed
  `<project>/.claude/hooks` layout),
* a non-config write, a non-write tool, a failed tool result and a re-entrant
  invocation (SOC_SYNC_ON_CONFIG_CHANGE=1) trigger nothing,
* missing sync.py / missing python / a hanging or failing sync.py all fail
  OPEN: exit 0, never a blocked tool call — a non-zero child still leaves one
  stderr hint line for the operator (MB-3 review F3).

Run: python3 -m pytest tests/test_hook_sync_on_config_change.py -v
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.timeouts import SCRIPT_TIMEOUT

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOK = _REPO_ROOT / "hooks" / "1-generic" / "sync-on-config-change.sh"
_BASH = shutil.which("bash") or "bash"

pytestmark = pytest.mark.skipif(
    sys.platform not in ("linux", "darwin"), reason="requires bash"
)

_CONFIG_REL = Path(".meta-config") / "project.yaml"

#: Stub sync.py: records how it was called, then optionally hangs / exits
#: non-zero. The marker is written first so a failing child is still visible.
_STUB = """\
import os
import pathlib
import sys
import time

marker = pathlib.Path(os.environ["SOC_TEST_MARKER"])
marker.write_text(
    "cwd=" + os.getcwd() + "\\n"
    "args=" + " ".join(sys.argv[1:]) + "\\n"
    "guard=" + os.environ.get("SOC_SYNC_ON_CONFIG_CHANGE", "") + "\\n"
    "project_dir=" + os.environ.get("AM_PROJECT_DIR", "") + "\\n",
    encoding="utf-8",
)
if os.environ.get("SOC_TEST_SLEEP"):
    time.sleep(float(os.environ["SOC_TEST_SLEEP"]))
sys.exit(int(os.environ.get("SOC_TEST_EXIT") or 0))
"""

#: The operator hint the hook prints when the child did not finish cleanly
#: (MB-3 review F3: kept on purpose, the exit code stays 0).
_HINT = "sync-on-config-change: scripts/sync.py did not finish (rc="
_HINT_ADVICE = "run 'python3 scripts/sync.py' manually"


def _env(**extra: str) -> dict:
    env = dict(os.environ)
    for key in (
        "CLAUDE_PROJECT_DIR",
        "AM_PROJECT_DIR",
        "SOC_AGENT_META_ROOT",
        "SOC_SYNC_ON_CONFIG_CHANGE",
        "SOC_SYNC_TIMEOUT",
        "SOC_TEST_MARKER",
        "SOC_TEST_SLEEP",
        "SOC_TEST_EXIT",
    ):
        env.pop(key, None)
    env.update(extra)
    return env


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / ".meta-config").mkdir(parents=True)
    (root / _CONFIG_REL).write_text("name: demo-project\n", encoding="utf-8")
    return root


def _install_sync_stub(root: Path, layout: Path = Path(".agent-meta")) -> Path:
    """Place the stub in one of the documented agent-meta checkout layouts."""
    scripts = root / layout / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "sync.py").write_text(_STUB, encoding="utf-8")
    return scripts / "sync.py"


def _run(hook: Path, payload: dict, cwd: Path, env: dict):
    return subprocess.run(
        [_BASH, str(hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
        timeout=SCRIPT_TIMEOUT,
    )


def _payload(tool: str, file_path: Path, **tool_result) -> dict:
    payload: dict = {
        "tool_name": tool,
        "tool_input": {"file_path": str(file_path)},
    }
    if tool_result:
        payload["tool_result"] = tool_result
    return payload


@pytest.mark.parametrize("tool", ["Write", "Edit"])
def test_successful_config_write_runs_sync_py(tmp_path, tool):
    root = _project(tmp_path)
    _install_sync_stub(root)
    marker = tmp_path / "sync-called"

    result = _run(
        _HOOK,
        _payload(tool, root / _CONFIG_REL),
        cwd=root,
        env=_env(AM_PROJECT_DIR=str(root), SOC_TEST_MARKER=str(marker)),
    )

    assert result.returncode == 0, result.stderr
    assert marker.exists(), f"a successful {tool} of the config must run sync.py"
    recorded = marker.read_text(encoding="utf-8")
    assert f"cwd={Path(root).resolve()}" in recorded, recorded
    assert "--config" in recorded
    assert f"args=--config {root / _CONFIG_REL}" in recorded, recorded
    assert "guard=1" in recorded, "the child must carry the recursion guard"
    assert f"project_dir={root}" in recorded


def test_tool_result_failure_does_not_run_sync(tmp_path):
    root = _project(tmp_path)
    _install_sync_stub(root)
    marker = tmp_path / "sync-called"

    for tool_result in ({"exit_code": 1}, {"is_error": True}):
        result = _run(
            _HOOK,
            _payload("Write", root / _CONFIG_REL, **tool_result),
            cwd=root,
            env=_env(AM_PROJECT_DIR=str(root), SOC_TEST_MARKER=str(marker)),
        )
        assert result.returncode == 0, result.stderr
        assert not marker.exists(), f"a failed tool result must not sync: {tool_result}"


def test_non_config_write_does_not_run_sync(tmp_path):
    root = _project(tmp_path)
    _install_sync_stub(root)
    marker = tmp_path / "sync-called"

    result = _run(
        _HOOK,
        _payload("Write", root / "README.md"),
        cwd=root,
        env=_env(AM_PROJECT_DIR=str(root), SOC_TEST_MARKER=str(marker)),
    )

    assert result.returncode == 0, result.stderr
    assert not marker.exists()


def test_non_write_tool_does_not_run_sync(tmp_path):
    root = _project(tmp_path)
    _install_sync_stub(root)
    marker = tmp_path / "sync-called"

    result = _run(
        _HOOK,
        _payload("Bash", root / _CONFIG_REL),
        cwd=root,
        env=_env(AM_PROJECT_DIR=str(root), SOC_TEST_MARKER=str(marker)),
    )

    assert result.returncode == 0, result.stderr
    assert not marker.exists()


def test_recursion_guard_skips_a_reentrant_run(tmp_path):
    root = _project(tmp_path)
    _install_sync_stub(root)
    marker = tmp_path / "sync-called"

    result = _run(
        _HOOK,
        _payload("Write", root / _CONFIG_REL),
        cwd=root,
        env=_env(
            AM_PROJECT_DIR=str(root),
            SOC_TEST_MARKER=str(marker),
            SOC_SYNC_ON_CONFIG_CHANGE="1",
        ),
    )

    assert result.returncode == 0, result.stderr
    assert not marker.exists()


def test_payload_cwd_resolves_the_project_root(tmp_path):
    """No AM_PROJECT_DIR: the payload cwd chain must find the project, and the
    hook's own process cwd must not matter."""
    root = _project(tmp_path)
    _install_sync_stub(root)
    marker = tmp_path / "sync-called"
    payload = _payload("Write", root / _CONFIG_REL)
    payload["cwd"] = str(root)

    result = _run(
        _HOOK,
        payload,
        cwd=tmp_path,  # deliberately NOT the project root
        env=_env(SOC_TEST_MARKER=str(marker)),
    )

    assert result.returncode == 0, result.stderr
    assert marker.exists(), result.stderr
    assert f"cwd={Path(root).resolve()}" in marker.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "layout",
    [Path(".agent-meta"), Path("external") / "agent-meta"],
    ids=["agent-meta-submodule", "external-agent-meta"],
)
def test_submodule_layout_runs_sync_cwd_independently(tmp_path, layout):
    """F1: both documented agent-meta checkout locations are found.

    ``<project>/external/agent-meta`` used to be ignored, so a project vendoring
    agent-meta there never re-synced. The lookup must resolve relative to the
    project root, not to the hook's process cwd — the hook is run from an
    unrelated directory on purpose.
    """
    root = _project(tmp_path)
    _install_sync_stub(root, layout)
    marker = tmp_path / "sync-called"
    payload = _payload("Write", root / _CONFIG_REL)
    payload["cwd"] = str(root)

    result = _run(
        _HOOK,
        payload,
        cwd=tmp_path,  # deliberately NOT the project root
        env=_env(SOC_TEST_MARKER=str(marker)),
    )

    assert result.returncode == 0, result.stderr
    assert marker.exists(), result.stderr
    recorded = marker.read_text(encoding="utf-8")
    assert f"cwd={Path(root).resolve()}" in recorded, recorded
    assert f"args=--config {root / _CONFIG_REL}" in recorded, recorded
    assert "guard=1" in recorded
    assert f"project_dir={root}" in recorded


@pytest.mark.parametrize(
    "layout",
    [Path("hooks") / "1-generic", Path(".claude") / "hooks"],
    ids=["source-layout", "deployed-layout"],
)
def test_deploy_layout_self_hosted_tree_runs_sync(tmp_path, layout):
    """Hook deployed inside a tree that IS the project (agent-meta
    self-hosting): the sibling scripts/sync.py must be found without any env
    hint.

    Both deployment shapes are covered: the source layout ``hooks/1-generic``
    and the real deployed layout ``<project>/.claude/hooks`` (what sync.py
    writes). The hook is started from an unrelated cwd with no payload ``cwd``,
    so the project root can only come from the deployment layout itself.
    """
    tree = tmp_path / "agent-meta"
    hook_dir = tree / layout
    hook_dir.mkdir(parents=True)
    deployed = hook_dir / "sync-on-config-change.sh"
    shutil.copy(_HOOK, deployed)
    (hook_dir / "lib").symlink_to(_REPO_ROOT / "hooks" / "1-generic" / "lib")
    (tree / ".meta-config").mkdir()
    (tree / _CONFIG_REL).write_text("name: self-hosted\n", encoding="utf-8")
    (tree / "scripts").mkdir()
    (tree / "scripts" / "sync.py").write_text(_STUB, encoding="utf-8")
    marker = tmp_path / "sync-called"
    env = _env(SOC_TEST_MARKER=str(marker))

    result = _run(
        deployed,
        _payload("Edit", tree / _CONFIG_REL),
        cwd=tmp_path,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert marker.exists(), result.stderr
    recorded = marker.read_text(encoding="utf-8")
    assert f"cwd={tree.resolve()}" in recorded, recorded
    assert f"args=--config {tree / _CONFIG_REL}" in recorded, recorded
    assert "guard=1" in recorded, "the child must carry the recursion guard"
    assert f"project_dir={tree}" in recorded

    # The recursion brake is real, not just an env echo: a re-entrant
    # invocation in this same deployment must not start a second sync.
    marker.unlink()
    again = _run(
        deployed,
        _payload("Edit", tree / _CONFIG_REL),
        cwd=tmp_path,
        env=_env(SOC_TEST_MARKER=str(marker), SOC_SYNC_ON_CONFIG_CHANGE="1"),
    )
    assert again.returncode == 0, again.stderr
    assert not marker.exists(), "SOC_SYNC_ON_CONFIG_CHANGE=1 must stop a second sync"


def test_deployed_hook_uses_the_external_agent_meta_checkout(tmp_path):
    """The production combination: hook deployed at <project>/.claude/hooks,
    agent-meta vendored at <project>/external/agent-meta (F1 + deploy layout)."""
    root = _project(tmp_path)
    hook_dir = root / ".claude" / "hooks"
    hook_dir.mkdir(parents=True)
    deployed = hook_dir / "sync-on-config-change.sh"
    shutil.copy(_HOOK, deployed)
    (hook_dir / "lib").symlink_to(_REPO_ROOT / "hooks" / "1-generic" / "lib")
    _install_sync_stub(root, Path("external") / "agent-meta")
    marker = tmp_path / "sync-called"

    result = _run(
        deployed,
        _payload("Write", root / _CONFIG_REL),
        cwd=tmp_path,
        env=_env(AM_PROJECT_DIR=str(root), SOC_TEST_MARKER=str(marker)),
    )

    assert result.returncode == 0, result.stderr
    assert marker.exists(), result.stderr
    recorded = marker.read_text(encoding="utf-8")
    assert f"cwd={Path(root).resolve()}" in recorded, recorded
    assert f"args=--config {root / _CONFIG_REL}" in recorded, recorded


def test_missing_sync_py_fails_open(tmp_path):
    root = _project(tmp_path)  # no .agent-meta submodule, no sync.py anywhere
    marker = tmp_path / "sync-called"

    result = _run(
        _HOOK,
        _payload("Write", root / _CONFIG_REL),
        cwd=root,
        env=_env(AM_PROJECT_DIR=str(root), SOC_TEST_MARKER=str(marker)),
    )

    assert result.returncode == 0, result.stderr
    assert not marker.exists()


def test_missing_python_fails_open(tmp_path):
    root = _project(tmp_path)
    _install_sync_stub(root)
    marker = tmp_path / "sync-called"

    # PATH with only the utilities the hook needs BEFORE its python probe
    # (dirname for SCRIPT_DIR): no python3/python, so the hook must skip.
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    dirname = shutil.which("dirname")
    assert dirname, "test environment needs dirname"
    (bin_dir / "dirname").symlink_to(dirname)

    result = _run(
        _HOOK,
        _payload("Write", root / _CONFIG_REL),
        cwd=root,
        env=_env(
            PATH=str(bin_dir),
            AM_PROJECT_DIR=str(root),
            SOC_TEST_MARKER=str(marker),
        ),
    )

    assert result.returncode == 0, result.stderr
    assert not marker.exists()


def test_hanging_sync_py_fails_open(tmp_path):
    root = _project(tmp_path)
    _install_sync_stub(root)
    marker = tmp_path / "sync-called"

    started = time.monotonic()
    result = _run(
        _HOOK,
        _payload("Write", root / _CONFIG_REL),
        cwd=root,
        env=_env(
            AM_PROJECT_DIR=str(root),
            SOC_TEST_MARKER=str(marker),
            SOC_TEST_SLEEP="30",
            SOC_SYNC_TIMEOUT="1",
        ),
    )
    elapsed = time.monotonic() - started

    assert result.returncode == 0, result.stderr
    assert elapsed < 20, f"the hook must bound the child, took {elapsed:.1f}s"
    # F3: fail-open stays exit 0, but the operator still gets one hint line.
    assert _HINT in result.stderr, result.stderr
    assert re.search(r"did not finish \(rc=[1-9][0-9]*\)", result.stderr), result.stderr
    assert _HINT_ADVICE in result.stderr, result.stderr


def test_failing_sync_py_keeps_exit_zero_and_prints_the_hint(tmp_path):
    """F3 decision: a non-zero sync.py never blocks the write (exit 0) and
    always leaves the actionable stderr hint naming the rc."""
    root = _project(tmp_path)
    _install_sync_stub(root)
    marker = tmp_path / "sync-called"

    result = _run(
        _HOOK,
        _payload("Write", root / _CONFIG_REL),
        cwd=root,
        env=_env(
            AM_PROJECT_DIR=str(root),
            SOC_TEST_MARKER=str(marker),
            SOC_TEST_EXIT="3",
        ),
    )

    assert result.returncode == 0, result.stderr
    assert marker.exists(), "the child did run; only its exit code was non-zero"
    assert f"{_HINT}3)" in result.stderr, result.stderr
    assert _HINT_ADVICE in result.stderr, result.stderr


def test_successful_sync_py_prints_no_hint(tmp_path):
    """The hint is reserved for the failure path (no noise on a clean run)."""
    root = _project(tmp_path)
    _install_sync_stub(root)
    marker = tmp_path / "sync-called"

    result = _run(
        _HOOK,
        _payload("Write", root / _CONFIG_REL),
        cwd=root,
        env=_env(AM_PROJECT_DIR=str(root), SOC_TEST_MARKER=str(marker)),
    )

    assert result.returncode == 0, result.stderr
    assert marker.exists()
    assert _HINT not in result.stderr, result.stderr


def test_hook_runs_sync_instead_of_a_lifecycle_wrapper():
    text = _HOOK.read_text(encoding="utf-8")

    assert "# version: 1.3.0" in text
    assert "lifecycle_check" not in text, "the hook must not call the lifecycle wrapper"
    assert "scripts/sync.py" in text
    # No inline Python and no provider-name branching in the hook body.
    assert " -c \"" not in text and " -c '" not in text
