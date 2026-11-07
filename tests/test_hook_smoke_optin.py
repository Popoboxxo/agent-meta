"""Behavioural smoke tests for the opt-in hooks (issue #1151, G1-7 / F6-13).

lifecycle-check, sync-on-config-change, viz-log and the action-pin-validation
release gate are ``enabled_by_default: false`` and had no behavioural test:
each one is run here once as a real subprocess against a fake project in
``tmp_path`` and judged by its exit code and its observable effect (the file
it writes or the verdict it prints). No network, no wall-clock assertions.

Run: python -m pytest tests/test_hook_smoke_optin.py -v
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
_BASH = shutil.which("bash") or "bash"

pytestmark = pytest.mark.skipif(
    sys.platform not in ("linux", "darwin"), reason="requires bash"
)


def _env(**extra: str) -> dict:
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    env.update(extra)
    return env


def _run(hook: Path, cwd: Path, payload: dict | None = None, env: dict | None = None):
    return subprocess.run(
        [_BASH, str(hook)],
        input=json.dumps(payload) if payload is not None else "",
        capture_output=True, text=True, cwd=str(cwd),
        env=env or _env(), timeout=SCRIPT_TIMEOUT,
    )


def _project(tmp_path: Path, config: dict) -> Path:
    # JSON config: lifecycle_check.py reads it without PyYAML.
    root = tmp_path / "project"
    root.mkdir()
    (root / "agent-meta.config.json").write_text(json.dumps(config), encoding="utf-8")
    return root


def test_lifecycle_check_writes_the_configured_merge_task(tmp_path):
    root = _project(tmp_path, {
        "ai-providers": ["Claude"],
        "lifecycle-triggers": {"on-merge": [{"agent": "tester", "task": "smoke-merge-task"}]},
    })
    payload = {"tool_name": "Bash", "tool_input": {"command": "git merge feature"},
               "tool_result": {"exit_code": 0}}
    failed = dict(payload, tool_result={"exit_code": 1})

    assert _run(_HOOKS / "lifecycle-check.sh", root, failed).returncode == 0
    pending = root / ".claude" / "pending-tasks.md"
    assert not pending.exists(), "a failed Bash call must not trigger lifecycle tasks"

    result = _run(_HOOKS / "lifecycle-check.sh", root, payload)
    assert result.returncode == 0, result.stderr
    assert "- [ ] **[tester]** smoke-merge-task" in pending.read_text(encoding="utf-8")


def test_sync_on_config_change_queues_a_resync_task(tmp_path):
    root = _project(tmp_path, {"ai-providers": ["Claude"]})
    hook = _HOOKS / "sync-on-config-change.sh"
    other = {"tool_name": "Write", "tool_input": {"file_path": str(root / "README.md")}}
    payload = {"tool_name": "Write",
               "tool_input": {"file_path": str(root / ".meta-config" / "project.yaml")}}

    assert _run(hook, root, other).returncode == 0
    pending = root / ".claude" / "pending-tasks.md"
    assert not pending.exists(), "only a project.yaml write may queue the re-sync"

    result = _run(hook, root, payload)
    assert result.returncode == 0, result.stderr
    assert "scripts/sync.py" in pending.read_text(encoding="utf-8")


def test_viz_log_appends_one_event_per_tool_call(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    payload = {"tool_name": "Bash", "tool_input": {"command": "ls -la"}}

    result = _run(_HOOKS / "viz-log.sh", root, payload, _env(AGENT_NAME="tester"))
    assert result.returncode == 0, result.stderr
    lines = (root / ".meta-viz" / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["tool"] == "Bash"
    assert event["agent"] == "tester"
    assert event["payload"] == {"command_preview": "ls -la"}


def test_action_pin_validation_fails_on_a_missing_upstream_ref(tmp_path):
    """A stub `gh` answers the API: 'good' refs exist, every other ref is
    missing. The gate must fail (exit 1) and name only the missing pin."""
    root = tmp_path / "project"
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text(
        "jobs:\n  a:\n    steps:\n"
        "      - uses: acme/good@v1\n"
        "      - uses: acme/gone@v9\n",
        encoding="utf-8",
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh = bin_dir / "gh"
    gh.write_text(
        '#!/bin/sh\n'
        '[ "$1" = auth ] && exit 0\n'
        'case "$2" in *acme/good/*) exit 0 ;; esac\n'
        'exit 1\n',
        encoding="utf-8",
    )
    gh.chmod(0o755)
    env = _env(PATH=f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
               PRE_RELEASE_GATE_ENABLED="true", PROJECT_ROOT=str(root))

    result = _run(_HOOKS / "release-gates" / "action-pin-validation.sh", root, env=env)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "[FAIL] action-pin-validation: acme/gone@v9" in result.stdout
    assert "acme/good" not in result.stdout
