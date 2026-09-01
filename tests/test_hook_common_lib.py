"""Regression tests for hooks/1-generic/lib/hook_common.sh (issue #601 dedup,
#596 redaction, #599 GRAPHIFY_BIN validation).

This shared helper lib is sourced by other hook scripts (orchestrator-guard.sh,
dod-push-check.sh, lifecycle-check.sh, sync-on-config-change.sh, and the
graphify-*-guard.sh hooks) instead of each one duplicating the same JSON
parsing / python-resolution / credential-redaction logic. It has no test
coverage anywhere else, so these tests invoke its bash functions directly as
subprocesses.

Run: python -m pytest tests/test_hook_common_lib.py -v
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_LIB_PATH = _REPO_ROOT / "hooks" / "1-generic" / "lib" / "hook_common.sh"

_BASH = shutil.which("bash") or "bash"

pytestmark = pytest.mark.skipif(
    sys.platform not in ("win32", "linux", "darwin"), reason="requires bash"
)


def _call(func_call: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run `func_call` after sourcing hook_common.sh. `env`, if given, is
    merged on top of a copy of the current process environment (not a full
    replacement) so PATH/HOME/etc. stay intact for `command -v python3`,
    `stat`, `basename` and friends used inside the lib itself."""
    script = f'source "{_LIB_PATH}"\n{func_call}\n'
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        [_BASH, "-c", script],
        capture_output=True,
        text=True,
        env=full_env,
    )


# --- hook_have_python / hook_python_bin ----------------------------------

def test_hook_have_python_true_when_python3_present():
    r = _call("hook_have_python && echo yes || echo no")
    assert r.stdout.strip() == "yes"


def test_hook_python_bin_prefers_python3():
    r = _call("hook_python_bin")
    assert r.stdout.strip() == "python3"


# --- hook_json_get --------------------------------------------------------

def test_hook_json_get_simple_field():
    r = _call('hook_json_get \'{"tool_name": "Bash"}\' "tool_name"')
    assert r.stdout.strip() == "Bash"


def test_hook_json_get_nested_field():
    r = _call(
        'hook_json_get \'{"tool_input": {"command": "git status"}}\' "tool_input.command"'
    )
    assert r.stdout.strip() == "git status"


def test_hook_json_get_missing_field_returns_default():
    r = _call('hook_json_get \'{"a": 1}\' "tool_input.command" "fallback"')
    assert r.stdout.strip() == "fallback"


def test_hook_json_get_missing_field_returns_empty_by_default():
    r = _call('hook_json_get \'{"a": 1}\' "tool_input.command"')
    assert r.stdout.strip() == ""


def test_hook_json_get_invalid_json_returns_default_not_crash():
    r = _call('hook_json_get \'not-json{{{\' "tool_name" "safe"')
    assert r.stdout.strip() == "safe"
    assert r.returncode == 0


def test_hook_json_get_object_value_returns_default():
    """A path that resolves to an object/array (not a scalar) must not leak
    a python repr like "{'a': 1}" into a bash variable — treated as unset."""
    r = _call('hook_json_get \'{"tool_input": {"command": "x"}}\' "tool_input" "was-object"')
    assert r.stdout.strip() == "was-object"


# --- hook_redact_secrets (issue #596) -------------------------------------

@pytest.mark.parametrize("raw,must_not_contain", [
    ("git clone https://user:sup3rSecr3t@example.com/repo.git", "sup3rSecr3t"),
    ("curl -H 'Authorization: Bearer abcdef123456789'", "abcdef123456789"),
    ("curl --token ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345", "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"),
    ("export AWS_ACCESS_KEY_ID=AKIAABCDEFGHIJKLMNOP", "AKIAABCDEFGHIJKLMNOP"),
    ("password=hunter2hunter2", "hunter2hunter2"),
])
def test_hook_redact_secrets_masks_credential_shapes(raw, must_not_contain):
    r = _call(f'hook_redact_secrets "{raw}"')
    assert must_not_contain not in r.stdout, f"leaked secret in redacted output: {r.stdout!r}"


def test_hook_redact_secrets_leaves_plain_commands_untouched():
    r = _call('hook_redact_secrets "git status"')
    assert r.stdout.strip() == "git status"


# --- hook_audit_log_append (issues #596/#597) -----------------------------

def test_hook_audit_log_append_redacts_and_sets_permissions(tmp_path):
    logfile = tmp_path / "audit.log"
    r = _call(
        f'hook_audit_log_append "{logfile}" '
        '"cmd=git clone https://user:sup3rSecr3t@example.com/repo.git"'
    )
    assert r.returncode == 0
    content = logfile.read_text(encoding="utf-8")
    assert "sup3rSecr3t" not in content
    assert "***:***@" in content
    assert oct(logfile.stat().st_mode)[-3:] == "600"


def test_hook_audit_log_append_rotates_when_over_cap(tmp_path):
    logfile = tmp_path / "audit.log"
    logfile.write_text("\n".join(f"old-line-{i}" for i in range(1, 51)) + "\n", encoding="utf-8")
    r = _call(
        f'HOOK_AUDIT_LOG_MAX_LINES=50 HOOK_AUDIT_LOG_KEEP_LINES=10 '
        f'hook_audit_log_append "{logfile}" "new-line"'
    )
    assert r.returncode == 0
    lines = logfile.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 10
    assert lines[-1] == "new-line"
    assert "old-line-1" not in lines  # oldest entries truncated away


# --- hook_resolve_graphify_bin (issue #599) -------------------------------

def test_graphify_bin_env_override_rejected_relative_path():
    r = _call("hook_resolve_graphify_bin", env={"GRAPHIFY_BIN": "evil/graphify", "PATH": "/usr/bin:/bin"})
    assert r.stdout.strip() == "graphify"


def test_graphify_bin_env_override_rejected_wrong_basename(tmp_path):
    evil = tmp_path / "notgraphify"
    evil.write_text("#!/bin/bash\necho pwned\n", encoding="utf-8")
    evil.chmod(0o700)
    r = _call("hook_resolve_graphify_bin", env={"GRAPHIFY_BIN": str(evil), "PATH": "/usr/bin:/bin"})
    assert r.stdout.strip() == "graphify"


def test_graphify_bin_env_override_rejected_world_writable(tmp_path):
    evil = tmp_path / "graphify"
    evil.write_text("#!/bin/bash\necho pwned\n", encoding="utf-8")
    evil.chmod(0o777)
    r = _call("hook_resolve_graphify_bin", env={"GRAPHIFY_BIN": str(evil), "PATH": "/usr/bin:/bin"})
    assert r.stdout.strip() == "graphify"


def test_graphify_bin_env_override_accepted_when_valid(tmp_path):
    good = tmp_path / "graphify"
    good.write_text("#!/bin/bash\necho ok\n", encoding="utf-8")
    good.chmod(0o700)
    r = _call("hook_resolve_graphify_bin", env={"GRAPHIFY_BIN": str(good), "PATH": "/usr/bin:/bin"})
    assert r.stdout.strip() == str(good)
