"""Regression tests for single-parse hook payload reading and role attribution.

Issues #1169 (one parse for all payload fields), #1238 (the new Python core
lives in an importable module behind a thin shell shim), #1210 (payload role
field cross-checks the sentinel) and #1250 (agent_id dependency pinned).

Run: python -m pytest tests/test_hook_single_parse.py -v
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.timeouts import SCRIPT_TIMEOUT

_REPO_ROOT = Path(__file__).resolve().parent.parent
_LIB_DIR = _REPO_ROOT / "hooks" / "1-generic" / "lib"
_MODULE_PATH = _LIB_DIR / "hook_json_many.py"
_LIB_PATH = _LIB_DIR / "hook_common.sh"
_HOOK_PATH = _REPO_ROOT / "hooks" / "1-generic" / "orchestrator-guard.sh"
_IMPL_PATH = _REPO_ROOT / "hooks" / "1-generic" / "orchestrator-guard-impl.sh"

_BASH = shutil.which("bash") or "bash"

pytestmark = pytest.mark.skipif(
    sys.platform not in ("win32", "linux", "darwin"), reason="requires bash"
)


@pytest.fixture()
def project(tmp_path):
    """A non-strict throw-away project root for real hook invocations."""
    root = tmp_path / "project"
    (root / ".meta-config").mkdir(parents=True)
    (root / ".meta-config" / "project.yaml").write_text(
        "orchestrator:\n  strict: false\n", encoding="utf-8"
    )
    return root


def _load_module():
    spec = importlib.util.spec_from_file_location("hook_json_many", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_module(payload: bytes, paths: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_MODULE_PATH), *paths],
        input=payload,
        capture_output=True,
        timeout=SCRIPT_TIMEOUT,
    )


def _fields(stdout: bytes) -> list[bytes]:
    parts = stdout.split(b"\x00")
    assert parts[-1] == b"", "fields must be NUL-terminated"
    return parts[:-1]


# --- #1238: importable, unit-testable Python core --------------------------


def test_module_is_importable():
    """#1238: the multi-field reader is a real module, not a bash heredoc."""
    module = _load_module()
    assert callable(module.read_many)


def test_read_many_matches_single_gets():
    payload = json.dumps({
        "tool_name": "Bash",
        "agent_id": "a1",
        "tool_input": {"command": "git status\nx"},
        "cwd": "/project",
    }).encode("utf-8")
    r = _run_module(payload, ["tool_name", "agent_id", "tool_input.command", "cwd"])
    assert r.returncode == 0, r.stderr
    assert _fields(r.stdout) == [b"Bash", b"a1", b"git status\nx", b"/project", b"ok"]


def test_read_many_survives_lone_surrogate():
    payload = b'{"tool_input": {"command": "git push origin main\\ud800"}}'
    r = _run_module(payload, ["tool_input.command"])
    assert r.returncode == 0, r.stderr
    assert b"git push origin main" in r.stdout


def test_read_many_invalid_json_fails_closed():
    r = _run_module(b"not json{{{", ["tool_name"])
    assert r.returncode == 1
    assert r.stdout == b""


def test_read_many_missing_and_object_values_are_empty():
    payload = json.dumps({"a": 1, "obj": {"k": "v"}, "arr": [1], "nil": None}).encode()
    r = _run_module(payload, ["missing", "obj", "arr", "nil", "a"])
    assert r.returncode == 0, r.stderr
    assert _fields(r.stdout) == [b"", b"", b"", b"", b"1", b"ok"]


def test_read_many_nul_in_value_cannot_shift_fields():
    """A NUL inside a requested value must fail the whole call, never move the
    next field into its slot (#1169 §2.4 / AC-6)."""
    payload = json.dumps({"tool_input": {"command": "a\x00/evil"}, "cwd": "/ok"}).encode()
    r = _run_module(payload, ["tool_input.command", "cwd"])
    assert r.returncode == 1
    assert r.stdout == b""


# --- #1169: thin shell shim in hook_common.sh ------------------------------


def _shim_call(payload: str, call: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_BASH, "-c", 'source "$1"\n' + call, _BASH, str(_LIB_PATH), payload],
        capture_output=True,
        cwd=str(cwd),
        env=dict(os.environ),
        timeout=SCRIPT_TIMEOUT,
    )


def test_shim_emits_nul_terminated_fields(project):
    payload = json.dumps({"tool_name": "Bash", "cwd": "/p"})
    r = _shim_call(payload, 'hook_json_get_many "$2" tool_name cwd', project)
    assert r.returncode == 0, r.stderr
    assert b"Bash\x00/p\x00ok\x00" == r.stdout


def test_shim_invalid_json_fails_without_trailer(project):
    r = _shim_call("not-json", 'hook_json_get_many "$2" tool_name', project)
    assert r.returncode == 1
    assert r.stdout == b""


# --- #1169: guard consumes the single parse --------------------------------


def _run_guard(hook: Path, payload: dict, project: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    return subprocess.run(
        [_BASH, str(hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(project),
        env=env,
        timeout=SCRIPT_TIMEOUT,
    )


def _bash_payload(command: str, project: Path) -> dict:
    return {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": project.as_posix(),
    }


def test_guard_blocks_payload_with_nul_in_command(project):
    """AC-11: a NUL in a requested field must be blocked before any command is
    evaluated — not silently stripped into a different command."""
    payload = _bash_payload("git status", project)
    payload["tool_input"]["command"] = "echo a\x00/evil"
    r = _run_guard(_HOOK_PATH, payload, project)
    assert r.returncode == 2, r.stderr
    assert "not valid JSON" in r.stderr or "NUL" in r.stderr


def test_guard_readonly_bash_unchanged(project):
    r = _run_guard(_HOOK_PATH, _bash_payload("git status", project), project)
    assert r.returncode == 0, r.stderr


def test_guard_invalid_json_still_fails_closed(project):
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    r = subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input="not-json{{{",
        capture_output=True,
        text=True,
        cwd=str(project),
        env=env,
        timeout=SCRIPT_TIMEOUT,
    )
    assert r.returncode == 2
    assert "not valid JSON" in r.stderr


# --- #1210 / #1250: payload role field vs. sentinel -----------------------


def _rendered_guard(tmp_path: Path, agent_id_cap: str, role_field_cap: str) -> Path:
    """Bake both sync-time placeholders like scripts/lib/hooks.py does."""
    hooks_dir = tmp_path / "rendered-hooks"
    (hooks_dir / "lib").mkdir(parents=True, exist_ok=True)
    shutil.copy(_HOOK_PATH, hooks_dir / _HOOK_PATH.name)
    shutil.copy(_LIB_PATH, hooks_dir / "lib" / "hook_common.sh")
    shutil.copy(_MODULE_PATH, hooks_dir / "lib" / _MODULE_PATH.name)
    impl = (_IMPL_PATH.read_text(encoding="utf-8")
            .replace("{{AGENT_META_HOOK_AGENT_ID}}", agent_id_cap)
            .replace("{{AGENT_META_HOOK_ROLE_FIELD}}", role_field_cap))
    (hooks_dir / _IMPL_PATH.name).write_text(impl, encoding="utf-8")
    return hooks_dir / _HOOK_PATH.name


def _role_payload(command: str, project: Path, role_field: str | None) -> dict:
    payload = _bash_payload(command, project)
    payload["agent_id"] = "subagent-1"
    if role_field is not None:
        payload["agent_type"] = role_field
    return payload


def test_role_mismatch_is_rejected(tmp_path, project):
    hook = _rendered_guard(tmp_path, "true", "true")
    r = _run_guard(
        hook,
        _role_payload("#agent-meta:agent=git\ngit add -- f", project, "developer"),
        project,
    )
    assert r.returncode == 2, r.stderr
    assert "role mismatch" in r.stderr


def test_role_match_keeps_git_path(tmp_path, project):
    hook = _rendered_guard(tmp_path, "true", "true")
    r = _run_guard(
        hook,
        _role_payload("#agent-meta:agent=git\ngit add -- f", project, "git"),
        project,
    )
    assert r.returncode == 0, r.stderr


def test_role_field_empty_falls_back_to_sentinel(tmp_path, project):
    hook = _rendered_guard(tmp_path, "true", "true")
    r = _run_guard(
        hook,
        _role_payload("#agent-meta:agent=git\ngit add -- f", project, None),
        project,
    )
    assert r.returncode == 0, r.stderr


def test_role_field_ignored_when_capability_off(tmp_path, project):
    hook = _rendered_guard(tmp_path, "true", "false")
    r = _run_guard(
        hook,
        _role_payload("#agent-meta:agent=git\ngit add -- f", project, "developer"),
        project,
    )
    assert r.returncode == 0, r.stderr


def test_role_field_does_not_weaken_destructive_gate(tmp_path, project):
    hook = _rendered_guard(tmp_path, "true", "true")
    r = _run_guard(
        hook,
        _role_payload("#agent-meta:agent=git\ngit reset --hard", project, "git"),
        project,
    )
    assert r.returncode == 2, r.stderr
    assert "user approval" in r.stderr


def test_main_thread_without_agent_id_unchanged(tmp_path, project):
    """#1250: the strict-mode decision still hinges on agent_id; a role field
    alone must never turn a main-thread call into a delegate."""
    hook = _rendered_guard(tmp_path, "true", "true")
    payload = _bash_payload("#agent-meta:agent=git\ngit status", project)
    payload["agent_type"] = "git"
    r = _run_guard(hook, payload, project)
    assert r.returncode == 0  # non-strict project, sentinel discarded on main thread
