"""Regression test for the Task 6 CRITICAL security fix in
hooks/1-generic/orchestrator-guard.sh: a bare/empty `agent_name` in the
synthetic PreToolUse payload must NOT be treated as an implicit exemption
(fail-open bug). Only `agent_name` values matching `orchestrator` or the
exact literal `git` (anchored, not a substring match) are allowed through.

This hook is a bash script outside the Python pytest suite, so nothing
else guards against someone reintroducing the fail-open exemption bug.
This test invokes the hook as a real subprocess with a synthetic
PreToolUse JSON payload and asserts on its exit code.

Empirically verified setup (see docstrings below for why):
- `tool_name` must be `"Bash"` -- non-mutating tool names (or a missing
  `tool_name`) exit 0 immediately, before the AGENT_NAME check is ever
  reached.
- `cwd` points at THIS repo's own root, which has
  `orchestrator.strict: true` in `.meta-config/project.yaml`. That makes
  the hook enter the strict-mode branch immediately after the AGENT_NAME
  check, giving a direct assertion on exactly the exemption logic under
  test. `tool_input.command` can be any harmless string in this mode --
  strict mode blocks on tool_name alone, not on command content.

Run: python -m pytest tests/test_orchestrator_guard_hook.py -v
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOK_PATH = _REPO_ROOT / "hooks" / "1-generic" / "orchestrator-guard.sh"

# On Windows, plain ["bash", ...] can resolve to System32\bash.exe (the WSL
# launcher) instead of Git Bash, depending on CreateProcess search order
# (System32 is searched before PATH). The WSL launcher mishandles this
# script's CRLF line endings. Resolve the real Git Bash explicitly via PATH
# to get deterministic behavior across environments.
_BASH = shutil.which("bash") or "bash"

# (agent_name, expected_exit_code)
CASES = [
    ("", 2),  # empty agent_name must NOT be treated as an implicit exemption
    ("git", 0),  # exact literal "git" is allowed
    ("gitx", 2),  # "^git$" must be anchored, not a substring match
    ("orchestrator", 0),  # orchestrator is allowed
    ("developer", 2),  # any other agent is blocked in strict mode
]


def _run_hook(agent_name: str) -> subprocess.CompletedProcess:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "echo test"},
        # Forward slashes: the hook does raw shell string concatenation
        # (`$PROJECT_ROOT/.meta-config/project.yaml`) without normalizing
        # path separators, so a Windows-style backslash path here would
        # silently fail the `-f` existence check and short-circuit the
        # strict-mode branch under test.
        "cwd": _REPO_ROOT.as_posix(),
        "agent_name": agent_name,
    }
    return subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )


@pytest.mark.skipif(sys.platform not in ("win32", "linux", "darwin"), reason="requires bash")
@pytest.mark.parametrize("agent_name,expected_exit_code", CASES)
def test_orchestrator_guard_exit_code(agent_name, expected_exit_code):
    assert _HOOK_PATH.is_file(), f"hook script not found: {_HOOK_PATH}"

    result = _run_hook(agent_name)

    assert result.returncode == expected_exit_code, (
        f"agent_name={agent_name!r}: expected exit code {expected_exit_code}, "
        f"got {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
