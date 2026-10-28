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
from __future__ import annotations

import os
import shlex
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


@pytest.mark.parametrize("locale", ["C", "C.UTF-8", "de_DE.UTF-8"])
@pytest.mark.parametrize("escape", ["\\ud800", "\\udcff", "\\udfff"])
def test_hook_json_get_lone_surrogate_is_not_dropped(locale, escape):
    """A lone surrogate made print() raise under a UTF-8 locale and the field
    came back empty -- a present, non-empty field must never read as ""
    (W2-B1 R2-2)."""
    payload = '{"tool_input": {"command": "git push origin main' + escape + '"}}'
    r = subprocess.run(
        [_BASH, "-c", f'source "{_LIB_PATH}"\nhook_json_get "$1" tool_input.command', _BASH, payload],
        capture_output=True, env=dict(os.environ, LC_ALL=locale))
    assert r.stdout.startswith(b"git push origin main"), (locale, r.stdout, r.stderr)


@pytest.mark.parametrize("locale", ["C", "de_DE.UTF-8"])
def test_hook_json_get_invalid_utf8_input_is_not_dropped(locale):
    script = (f'source "{_LIB_PATH}"\n'
              'IN=$(printf \'{"tool_input": {"command": "git push \\377"}}\')\n'
              'hook_json_get "$IN" tool_input.command\n')
    r = subprocess.run([_BASH, "-c", script], capture_output=True,
                       env=dict(os.environ, LC_ALL=locale))
    assert r.stdout.startswith(b"git push "), (locale, r.stdout, r.stderr)


# --- hook_json_usable (issue #954) ---------------------------------------

def _python_shim(tmp_path: Path, body: str) -> str:
    """A PATH whose first python3 is `body` (the shim dir only, so a second
    real interpreter cannot rescue the probe)."""
    d = tmp_path / "shim"
    d.mkdir(exist_ok=True)
    f = d / "python3"
    f.write_text(body, encoding="utf-8")
    f.chmod(0o755)
    return str(d)


def test_hook_json_usable_true_with_a_real_interpreter():
    r = _call("hook_json_usable && echo usable || echo unusable")
    assert r.stdout.strip() == "usable", r.stderr


def test_hook_json_usable_rejects_an_interpreter_that_exits_non_zero(tmp_path):
    """M3/#954: the probe default used to be the sentinel itself, so an
    interpreter that exits 1 without output fell back to the default and
    looked usable. The sentinel must come from the payload, never a fallback."""
    path = _python_shim(tmp_path, "#!/bin/sh\nexit 1\n")
    r = _call("hook_json_usable && echo usable || echo unusable", {"PATH": path})
    assert r.stdout.strip() == "unusable", (r.stdout, r.stderr)


def test_hook_json_usable_rejects_an_interpreter_that_prints_garbage(tmp_path):
    path = _python_shim(tmp_path, "#!/bin/sh\necho garbage\n")
    r = _call("hook_json_usable && echo usable || echo unusable", {"PATH": path})
    assert r.stdout.strip() == "unusable", (r.stdout, r.stderr)


def test_hook_json_usable_rejects_a_missing_interpreter(tmp_path):
    empty = tmp_path / "empty-path"
    empty.mkdir()
    r = _call("hook_json_usable && echo usable || echo unusable", {"PATH": str(empty)})
    assert r.stdout.strip() == "unusable", (r.stdout, r.stderr)


def test_hook_json_usable_probe_default_is_distinct_from_the_sentinel():
    """The fallback default must not be the sentinel value the comparison
    looks for (that equality was the M3 bug)."""
    lib = _LIB_PATH.read_text(encoding="utf-8")
    assert "'hook-json-bad'" in lib
    r = _call("hook_json_get '{}' '__hook_json_probe__' 'hook-json-bad'")
    assert r.stdout.strip() == "hook-json-bad"


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


# --- issue #949: shared push-guard helpers --------------------------------

def test_hook_protected_branches_dedupes_main_and_master():
    """One definition for the classifier's set and the block message (#949):
    main/master must never appear twice (#1033) and the configured main
    branch stays first when it is a different branch."""
    assert _call("hook_protected_branches main").stdout.strip() == "main master"
    assert _call("hook_protected_branches master").stdout.strip() == "main master"
    assert _call("hook_protected_branches develop").stdout.strip() == "develop main master"
    assert _call("hook_protected_branches").stdout.strip() == "main master"
    assert _call('hook_protected_branches ""').stdout.strip() == "main master"


def _walk(args, opts_with_value=""):
    """Run the emitted walk_push_args() (issue #949) on a JSON arg list and
    return (pos, opts) as JSON-decoded Python objects."""
    import json as _json

    script = (
        'hook_push_arg_parser_py > /dev/null\n'  # must exist and emit source
        "{ hook_push_arg_parser_py; cat <<'PY'\n"
        "import json, sys\n"
        "print(json.dumps(walk_push_args(json.loads(sys.argv[1]), set(sys.argv[2].split(',')))))\n"
        "PY\n"
        "} | python3 - " + f"'{_json.dumps(args)}' '{opts_with_value}'\n"
    )
    r = _call(script)
    assert r.returncode == 0, r.stderr
    return tuple(_json.loads(r.stdout))


def test_push_arg_parser_emits_python_source():
    r = _call("hook_push_arg_parser_py | python3 -c 'import sys; compile(sys.stdin.read(), \"p\", \"exec\")'")
    assert r.returncode == 0, r.stderr


def test_push_arg_parser_positionals_after_double_dash():
    pos, opts = _walk(["-f", "origin", "--", "main", "-oZ"])
    assert pos == ["origin", "main", "-oZ"]
    assert opts == [["-f", None, "-f"]]


def test_push_arg_parser_long_value_forms():
    pos, opts = _walk(["--push-option=x", "--push-option", "y", "origin"],
                      "--push-option")
    assert pos == ["origin"]
    assert opts == [["--push-option", "x", "--push-option=x"],
                    ["--push-option", "y", "--push-option"]]


def test_push_arg_parser_short_clusters_and_o_value():
    pos, opts = _walk(["-fv", "-o", "--tags", "origin", "-fo", "y"], "--push-option")
    assert pos == ["origin"]
    assert opts == [["-f", None, "-fv"], ["-v", None, "-fv"],
                    ["-o", "--tags", "-o"], ["-f", None, "-fo"], ["-o", "y", "-fo"]]


# --- hook_known_tool_name (review finding M2, #954 follow-up) -------------

def _known(name: str) -> str:
    return _call(
        f"hook_known_tool_name {shlex.quote(name)} && echo known || echo unknown"
    ).stdout.strip()


@pytest.mark.parametrize("name", [
    "Bash", "Write", "Edit", "Read", "Glob", "Grep", "TodoWrite", "Task",
    "WebFetch", "WebSearch", "NotebookEdit", "MultiEdit", "Skill",
    "mcp__playwright__browser_navigate", "mcp__reqogniloom__workspace_get",
])
def test_hook_known_tool_name_accepts_known_tools(name):
    """The shared allow-list both security guards consult (M2): every name
    either guard can receive from the claude-code-json contract, plus the
    open-ended MCP namespace, must stay allowed."""
    assert _known(name) == "known"


@pytest.mark.parametrize("name", [
    "",            # missing tool_name (or unparseable payload)
    "garbage",     # what a broken python3 shim used to return as tool_name
    "bash",        # raw provider-native spelling, not the hook contract
    "write",
    "run_command",     # Antigravity native name: the adapter normalizes it
    "write_to_file",
    "123",         # JSON number -> "123"
    "True",        # JSON true
    "mcp__",       # namespace without server/tool
])
def test_hook_known_tool_name_rejects_unknown_or_non_canonical(name):
    """Anything not on the list fails closed: unknown means unclassifiable,
    so both guards block it instead of matching their `*) exit 0` branch."""
    assert _known(name) == "unknown"
