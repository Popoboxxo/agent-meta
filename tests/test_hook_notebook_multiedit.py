"""NotebookEdit / MultiEdit / PowerShell interception in both fail-closed guards.

Issue #1151 (audit F6-01, F6-13): both guards only intercepted
``Write|Edit|Bash``. ``NotebookEdit`` (target in ``tool_input.notebook_path``),
``MultiEdit`` (target in ``tool_input.file_path``) and ``PowerShell`` (command
in ``tool_input.command``, same fields as Bash) fell into the pass-through
branch, so a notebook write to ``/etc/x.ipynb`` left the repo-containment jail
and a main-thread notebook edit slipped past strict mode (probe: rc 0 in both).

Semantic assertions only: the hooks run as real subprocesses with synthetic
PreToolUse payloads; the exit code decides (0 = allow, 2 = block).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.timeouts import SCRIPT_TIMEOUT

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOKS = _REPO_ROOT / "hooks" / "1-generic"
_CONTAINMENT = _HOOKS / "repo-containment.sh"
_GUARD = _HOOKS / "orchestrator-guard.sh"
_BASH = shutil.which("bash") or "bash"

pytestmark = pytest.mark.skipif(
    sys.platform not in ("win32", "linux", "darwin"), reason="requires bash"
)


def _env() -> dict:
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    return env


def _run(hook: Path, payload: dict, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_BASH, str(hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=_env(),
        timeout=SCRIPT_TIMEOUT,
    )


@pytest.fixture()
def project(tmp_path) -> Path:
    """Containment project: active jail, active .tmp sink, strict mode off."""
    root = tmp_path / "project"
    (root / ".meta-config").mkdir(parents=True)
    (root / ".meta-config" / "project.yaml").write_text(
        "repo_containment:\n  enabled: true\n  tmp-sink:\n    enabled: true\n"
        "    path: \".tmp\"\norchestrator:\n  strict: false\n",
        encoding="utf-8",
    )
    return root


def _payload(tool: str, tool_input: dict, cwd: Path, agent_id: str = "") -> dict:
    payload = {"tool_name": tool, "tool_input": tool_input, "cwd": str(cwd)}
    if agent_id:
        payload["agent_id"] = agent_id
    return payload


# --- repo-containment ----------------------------------------------------


@pytest.mark.parametrize("tool,key", [
    ("NotebookEdit", "notebook_path"),
    ("MultiEdit", "file_path"),
])
def test_containment_blocks_outside_notebook_and_multiedit(project, tool, key):
    outside = project.parent / "x.ipynb"
    result = _run(_CONTAINMENT, _payload(tool, {key: str(outside)}, project), project)
    assert result.returncode == 2, result.stderr
    assert "outside the repository root" in result.stderr


def test_containment_blocks_notebook_in_system_dir(project):
    result = _run(_CONTAINMENT,
                  _payload("NotebookEdit", {"notebook_path": "/etc/x.ipynb"}, project),
                  project)
    assert result.returncode == 2, result.stderr


@pytest.mark.parametrize("tool,key", [
    ("NotebookEdit", "notebook_path"),
    ("MultiEdit", "file_path"),
])
def test_containment_allows_inside_notebook_and_multiedit(project, tool, key):
    inside = project / "nb" / "x.ipynb"
    result = _run(_CONTAINMENT, _payload(tool, {key: str(inside)}, project), project)
    assert result.returncode == 0, result.stderr


def test_containment_notebook_without_any_path_fails_closed(project):
    result = _run(_CONTAINMENT, _payload("NotebookEdit", {}, project), project)
    assert result.returncode == 2, result.stderr


def test_containment_treats_powershell_like_bash(project):
    outside = project.parent / "ps-evil.txt"
    blocked = _run(_CONTAINMENT,
                   _payload("PowerShell", {"command": f"echo x > {outside}"}, project),
                   project)
    assert blocked.returncode == 2, blocked.stderr
    allowed = _run(_CONTAINMENT,
                   _payload("PowerShell", {"command": "echo x > inside.txt"}, project),
                   project)
    assert allowed.returncode == 0, allowed.stderr


# --- orchestrator-guard --------------------------------------------------


@pytest.mark.parametrize("tool,tool_input", [
    ("NotebookEdit", {"notebook_path": "/etc/x.ipynb", "new_source": "x"}),
    ("MultiEdit", {"file_path": "foo.txt", "edits": []}),
    ("PowerShell", {"command": "Get-ChildItem"}),
])
def test_guard_strict_mode_blocks_main_thread_writes(hook_project_root, tool, tool_input):
    """The fixture project carries this repo's config (orchestrator.strict:
    true): a main-thread write-capable call must be blocked like Write/Bash."""
    result = _run(_GUARD, _payload(tool, tool_input, hook_project_root), hook_project_root)
    assert result.returncode == 2, result.stderr
    assert "STRICT MODE" in result.stderr


@pytest.mark.parametrize("tool,tool_input", [
    ("NotebookEdit", {"notebook_path": "x.ipynb", "new_source": "x"}),
    ("MultiEdit", {"file_path": "foo.txt", "edits": []}),
    ("PowerShell", {"command": "Get-ChildItem"}),
])
def test_guard_strict_mode_allows_dispatched_subagent(hook_project_root, tool, tool_input):
    result = _run(_GUARD, _payload(tool, tool_input, hook_project_root, "sub-1"),
                  hook_project_root)
    assert result.returncode == 0, result.stderr


def test_guard_scans_powershell_for_git_mutations(hook_project_root):
    result = _run(_GUARD,
                  _payload("PowerShell", {"command": "git push origin feature"},
                           hook_project_root, "sub-1"),
                  hook_project_root)
    assert result.returncode == 2, result.stderr
    assert "git mutations" in result.stderr
