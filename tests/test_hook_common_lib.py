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
from typing import Optional

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
#
# There is NO automated consistency check against the harness's actual tool
# list, and none can exist: the list is maintained by hand (the audit log
# contains no `tool_name` records, verified). A new built-in therefore has to
# be added here deliberately, together with its accept case below.

def _known(name: str) -> str:
    return _call(
        f"hook_known_tool_name {shlex.quote(name)} && echo known || echo unknown"
    ).stdout.strip()


@pytest.mark.parametrize("name", [
    "Bash", "Write", "Edit", "Read", "Glob", "Grep", "TodoWrite", "Task",
    "WebFetch", "WebSearch", "NotebookEdit", "MultiEdit", "Skill",
    "mcp__playwright__browser_navigate", "mcp__reqogniloom__workspace_get",
    "Agent", "SendMessage",
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
    "EnterWorktree",   # creates a directory: forbidden by no-worktree-isolation
    "ExitWorktree",
])
def test_hook_known_tool_name_rejects_unknown_or_non_canonical(name):
    """Anything not on the list fails closed: unknown means unclassifiable,
    so both guards block it instead of matching their `*) exit 0` branch."""
    assert _known(name) == "unknown"


# --- hook_is_meta_submodule_dir (issue #943 (l)) --------------------------

@pytest.mark.parametrize("path", [
    "/home/u/project/.agent-meta",
    "/home/u/project/.agent-meta/",
    "/home/u/project/external/agent-meta",
    "/home/u/project/external/agent-meta/",
])
def test_hook_is_meta_submodule_dir_accepts_nested_meta_checkouts(path):
    """A nested agent-meta checkout carries its own .meta-config/ and must not
    win the project-root walk-up over the enclosing project."""
    assert _call(f"hook_is_meta_submodule_dir {shlex.quote(path)} && echo yes || echo no"
                 ).stdout.strip() == "yes"


@pytest.mark.parametrize("path", [
    "", "/home/u/project", "/home/u/project/external/other",
    "/home/u/agent-meta", "/home/u/project/.agent-meta-copy",
])
def test_hook_is_meta_submodule_dir_rejects_everything_else(path):
    assert _call(f"hook_is_meta_submodule_dir {shlex.quote(path)} && echo yes || echo no"
                 ).stdout.strip() == "no"


# --- hook_shell_scan_py (issues #943 (a)/(c)/(j), #944 SR-B-16) -----------

def _shell_scan_source() -> str:
    r = _call("hook_shell_scan_py")
    assert r.returncode == 0, r.stderr
    assert "def split_shell_statements" in r.stdout
    return r.stdout


def _scan(code: str, timeout: Optional[float] = None) -> subprocess.CompletedProcess:
    """Run `code` with the emitted scanner definitions in scope."""
    return subprocess.run(
        [sys.executable, "-c", _shell_scan_source() + "\n" + code],
        capture_output=True, text=True, timeout=timeout,
    )


def _fork_bomb_verdict(expr: str) -> subprocess.CompletedProcess:
    """Classify the command built by the Python expression `expr`.

    The command is built INSIDE the child process (as source text) so a
    multi-hundred-KB input never travels through the command line.
    """
    return _scan(f"print(int(is_fork_bomb({expr})))")


def test_shell_scan_py_emits_compilable_source():
    r = subprocess.run(
        [sys.executable, "-c",
         "import sys; compile(sys.stdin.read(), 'p', 'exec')"],
        input=_shell_scan_source(), capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr


@pytest.mark.parametrize("command,expected", [
    # An operator inside quotes is text, not a statement separator (#943 (j)).
    ('echo "a; git push --force b"', [('echo "a; git push --force b"', [])]),
    # A heredoc body is prose and is attached to the opening statement
    # (#944 SR-B-16); a real command after the terminator still appears.
    ("cat <<'EOF'\nfoo; git push --force\nEOF",
     [("cat <<'EOF'", ["foo; git push --force"])]),
    ("cat <<'EOF'\nfoo\nEOF\ngit push --force",
     [("cat <<'EOF'", ["foo"]), ("git push --force", [])]),
    # Backslash-newline joins the physical lines (#943 (c)).
    ("git push \\\n--force origin main", [("git push --force origin main", [])]),
    # A comment is not code (the sentinel line disappears; the next line stays).
    ("#agent-meta:agent=git\ngit commit -m x", [("git commit -m x", [])]),
    # Parentheses stay part of the statement; tokens_of splits them later.
    ("(git push --force)", [("(git push --force)", [])]),
    # Operators inside a command substitution do not split the outer command.
    ('echo "$(git push --force)"', [('echo "$(git push --force)"', [])]),
])
def test_split_shell_statements_semantics(command, expected):
    r = _scan(
        "import json, sys\n"
        f"print(json.dumps(split_shell_statements({command!r})))\n"
    )
    assert r.returncode == 0, r.stderr
    assert [tuple(x) for x in eval(r.stdout)] == expected  # noqa: S307 - test data


def test_fork_bomb_detection_is_linear_on_a_300kb_identifier():
    """Issue #943 (a): the old regex was quadratic on long identifier chains
    (20 KB ~ 5 s), so the hook timeout silently disabled the gate. The shared
    scanner must classify 300 KB well under the 100 ms acceptance bound."""
    r = _scan(
        "import time\n"
        "command = 'echo ' + 'a' * 300000\n"
        "start = time.perf_counter()\n"
        "result = is_fork_bomb(command)\n"
        "elapsed_ms = (time.perf_counter() - start) * 1000\n"
        "print(int(result), elapsed_ms)\n"
    )
    assert r.returncode == 0, r.stderr
    result, elapsed_ms = r.stdout.split()
    assert result == "0"
    assert float(elapsed_ms) < 100.0, f"fork-bomb scan took {elapsed_ms} ms"


@pytest.mark.parametrize("command", [
    ":(){ :|:& };:",
    "bomb(){ bomb|bomb& };bomb",
    "bomb ( ) { bomb | bomb & }",
])
def test_fork_bomb_detector_matches_real_bombs(command):
    r = _scan(f"print(int(is_fork_bomb({command!r})))")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "1"


def test_fork_bomb_detector_ignores_a_quoted_string_argument():
    r = _scan("print(int(is_fork_bomb(strip_quoted('echo \\\":(){ :|:& };:\\\"'))))")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "0"


@pytest.mark.parametrize("expr,expected", [
    # AC-A.1: a name longer than the old 64-character cap is scanned exactly,
    # so this bomb is detected instead of being dropped as "no match".
    ('"b"*70 + "(){ " + "b"*70 + "|" + "b"*70 + "& };" + "b"*70', 1),
    # ... while a long name with a harmless body stays a non-bomb.
    ('"a"*65 + "(){ :; }"', 0),
], ids=["bomb-with-70-char-name", "harmless-65-char-name"])
def test_fork_bomb_scans_long_function_name_exactly(expr, expected):
    r = _fork_bomb_verdict(expr)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == str(expected)


@pytest.mark.parametrize("expr,expected", [
    # AC-A.2 (characterisation): at and below the old cap nothing changes.
    ('"a"*64 + "(){ :; }"', 0),
    ('"b"*64 + "(){ " + "b"*64 + "|" + "b"*64 + "& };"', 1),
    # An identifier followed by "()" but no body is not a bomb.
    ('"a"*100 + "()"', 0),
], ids=["harmless-64-char-name", "bomb-with-64-char-name", "no-body"])
def test_fork_bomb_function_name_at_limit_is_scanned(expr, expected):
    r = _fork_bomb_verdict(expr)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == str(expected)


@pytest.mark.parametrize("expr,expected", [
    # AC-A.3: no unquoted '}' inside the 512-character body window -> fail
    # closed (block) instead of skipping the header (fail open).
    ('"f(){ " + "x"*520 + " f|f& };f"', 1),
    ('"f(){ " + "x"*980 + " f|f& };f"', 1),
], ids=["bomb-body-past-window", "bomb-body-far-past-window"])
def test_fork_bomb_fails_closed_on_exhausted_body_window(expr, expected):
    r = _fork_bomb_verdict(expr)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == str(expected)


@pytest.mark.parametrize("expr,expected", [
    # AC-A.4 (characterisation): a body closed inside the window is still
    # classified by content, not by the window rule.
    ('"f(){ " + "x"*500 + " }"', 0),
    ('"f(){ x} " * 60000', 0),
], ids=["closed-body-at-window-edge", "many-closed-bodies"])
def test_fork_bomb_closed_body_within_window_is_scanned(expr, expected):
    r = _fork_bomb_verdict(expr)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == str(expected)


@pytest.mark.parametrize("expr,expected", [
    # Issue #1050: the body ends at the DEPTH-MATCHING '}' inside the
    # 512-character window, so a brace or '${...}' before the self-call no
    # longer hides the bomb behind the first '}'.
    ('"f(){ : ${x}; f|f& };f"', 1),
    ('"f(){ { :; }; f|f& };f"', 1),
    # ... while nested braces/expansions without a self-call stay clean.
    ('"f(){ { :; }; };f"', 0),
    ('"f(){ : ${x}; }"', 0),
    # An exhausted window still fails closed (block) under the depth scan,
    # even when the preceding '${...}' is balanced.
    ('"f(){ ${x}; " + "x"*520 + " f|f& };f"', 1),
], ids=["bomb-after-expansion", "bomb-after-nested-braces",
        "nested-braces-no-call", "expansion-no-call",
        "nested-body-past-window"])
def test_fork_bomb_ends_body_at_depth_matching_brace(expr, expected):
    r = _fork_bomb_verdict(expr)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == str(expected)


@pytest.mark.parametrize("expr,expected", [
    # AC-A.5: the unlimited backward name scan stays linear (one scan per
    # '()' pair, they never overlap), so a 300 KB header is not a timeout.
    ('"a"*20000 + "(){ :; }"', 0),
    ('"a"*300000 + "(){ :; }"', 0),
    # A header with no closing '}' in the body window fails closed.
    ('"f(){ " * 60000', 1),
], ids=["20k-char-name", "300k-char-name", "brace-chain"])
def test_fork_bomb_scan_stays_linear_on_long_header_names(expr, expected):
    code = (
        "import time\n"
        f"command = {expr}\n"
        "start = time.perf_counter()\n"
        "result = is_fork_bomb(command)\n"
        "elapsed_ms = (time.perf_counter() - start) * 1000\n"
        "print(int(result), elapsed_ms)\n"
    )
    try:
        r = _scan(code, timeout=5)
    except subprocess.TimeoutExpired:
        pytest.fail("watchdog: the fork-bomb scan did not finish within 5 s")
    assert r.returncode == 0, r.stderr
    result, elapsed_ms = r.stdout.split()
    assert result == str(expected)
    assert float(elapsed_ms) < 1000.0, (
        f"fork-bomb scan of the {expr!r} command took {elapsed_ms} ms"
    )


def test_split_shell_statements_and_clean_drops_bodies_keeps_terminator():
    """The cleaned stream keeps operators (so a fork bomb stays one line) but
    drops heredoc bodies (#943 (j), #944 SR-B-16)."""
    r = _scan(
        "import json\n"
        "stmts, cleaned = split_shell_statements_and_clean("
        "\"cat <<'EOF'\\n:(){ :|:& };:\\nEOF\\ngit push --force\")\n"
        "print(json.dumps([stmts, cleaned]))\n"
    )
    assert r.returncode == 0, r.stderr
    statements, cleaned = eval(r.stdout)  # noqa: S307 - test data
    assert [tuple(x) for x in statements] == [
        ("cat <<'EOF'", [":(){ :|:& };:"]),
        ("git push --force", []),
    ]
    assert "git push --force" in cleaned
    assert ":(){ :|:& }:" not in cleaned


def test_heredoc_with_escaped_delimiter_is_skipped():
    r = _scan(
        "import json\n"
        "print(json.dumps(split_shell_statements('cat <<\\\\EOF\\n> /etc/x\\nEOF\\nls')))\n"
    )
    assert r.returncode == 0, r.stderr
    assert eval(r.stdout) == [["cat <<\\EOF", ["> /etc/x"]], ["ls", []]]  # noqa: S307


# --- review findings F1/F2/F4: splitter fidelity -------------------------


def test_ansi_c_quoting_does_not_desync_the_splitter():
    """F1: inside $'...' a backslash escapes the next character, so the \\'
    does NOT close the string. The old scanner treated $'it\\'s' as a plain
    quoted span, never closed it, and swallowed every later statement (a
    force push became invisible)."""
    r = _scan(
        "import json\n"
        "print(json.dumps(split_shell_statements("
        "\"echo $'it\\\\'s'; git push --force origin main\")))\n"
    )
    assert r.returncode == 0, r.stderr
    assert eval(r.stdout) == [  # noqa: S307 - test data
        ["echo $'it\\'s'", []],
        ["git push --force origin main", []],
    ]


def test_locale_quoting_keeps_the_split_boundary():
    """F1: $"..." (locale translation) quotes like "...", so an operator
    inside it is text while the following statement is still split off."""
    r = _scan(
        "import json\n"
        "print(json.dumps(split_shell_statements("
        "'echo $\"a; b\"; git push --force')))\n"
    )
    assert r.returncode == 0, r.stderr
    assert eval(r.stdout) == [  # noqa: S307 - test data
        ['echo $"a; b"', []],
        ["git push --force", []],
    ]


def test_dynamic_heredoc_delimiter_does_not_swallow_the_body():
    """F2: a delimiter word carrying '$' or a backtick is not tracked, so the
    body stays in the statement stream instead of hiding everything after it
    (fail closed; see the deliberate divergence documented in the scanner)."""
    commands = [
        "cat <<$X\nX\ngit push --force origin main",
        "cat <<${X}\nX\ngit push --force origin main",
        "cat <<`X`\nX\ngit push --force origin main",
        'cat <<"$X"\nX\ngit push --force origin main',
    ]
    for command in commands:
        r = _scan(
            "import json\n"
            f"print(json.dumps(split_shell_statements({command!r})))\n"
        )
        assert r.returncode == 0, r.stderr
        statements = [tuple(x) for x in eval(r.stdout)]  # noqa: S307 - test data
        assert statements[-1] == ("git push --force origin main", []), command
        # The opening statement has no attached (suppressed) body.
        assert statements[0][1] == [], command


def test_trailing_comment_is_cut_from_cleaned_code_too():
    """F4: the statement stream already dropped comments; the cleaned code
    handed to the fork-bomb scan kept a trailing one, so a bomb-shaped
    COMMENT was classified as destructive code."""
    r = _scan(
        "import json\n"
        "stmts, cleaned = split_shell_statements_and_clean("
        "'git status # :(){ :|:& };:')\n"
        "print(json.dumps([stmts, cleaned, int(is_fork_bomb(strip_quoted(cleaned)))]))\n"
    )
    assert r.returncode == 0, r.stderr
    statements, cleaned, bomb = eval(r.stdout)  # noqa: S307 - test data
    assert [tuple(x) for x in statements] == [("git status", [])]
    assert cleaned.strip() == "git status"
    assert bomb == 0


# --- hook_shell_resolver_py (containment/guard parity, v1.4.0) ------------

def _resolver_source() -> str:
    r = _call("hook_shell_scan_py; hook_shell_resolver_py")
    assert r.returncode == 0, r.stderr
    assert "def command_start" in r.stdout
    return r.stdout


def _resolve(command: str) -> list[tuple[str, list[str]]]:
    """Run the shared splitter + resolver over *command* and return one
    (command word, args) pair per statement that has a command word.

    The tokenizer lives with the caller by design, so this mirrors what both
    hooks do: punctuation-aware shlex, then command_start().
    """
    code = (
        "import json, os, re, shlex, sys\n"
        "def tokens_of(stmt):\n"
        "    lex = shlex.shlex(stmt, posix=True, punctuation_chars='()')\n"
        "    lex.whitespace_split = True\n"
        "    lex.commenters = ''\n"
        "    return list(lex)\n"
        "out = []\n"
        f"for stmt, _b in split_shell_statements({command!r}):\n"
        "    toks = tokens_of(stmt)\n"
        "    if not toks:\n"
        "        continue\n"
        "    i = command_start(toks)\n"
        "    if i >= len(toks):\n"
        "        continue\n"
        "    out.append((os.path.basename(toks[i]), toks[i + 1:]))\n"
        "print(json.dumps(out))\n"
    )
    r = subprocess.run(
        [sys.executable, "-c", _resolver_source() + "\n" + code],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    return [(word, args) for word, args in eval(r.stdout)]  # noqa: S307 - test data


def test_shell_resolver_py_emits_compilable_source():
    source = _resolver_source()
    r = subprocess.run(
        [sys.executable, "-c",
         "import sys; compile(sys.stdin.read(), 'p', 'exec')"],
        input=source, capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr


@pytest.mark.parametrize("command,expected", [
    # Wrapper grammar: positional prefix, then the wrapped command.
    ("timeout 5 git push", [("git", ["push"])]),
    ("flock -w 5 /tmp/l git push", [("git", ["push"])]),
    ("chroot /x git push", [("git", ["push"])]),
    ("env X=1 git push", [("git", ["push"])]),
    ("sudo -u me git push", [("git", ["push"])]),
    ("setsid --wait git push", [("git", ["push"])]),
    # A '--' at command position is transparent, before or after the
    # wrapper's own options/positional prefix.
    ("timeout 5 -- git push", [("git", ["push"])]),
    ("timeout --signal=KILL 5 -- git push", [("git", ["push"])]),
    ("flock -w 5 /tmp/l -- git push", [("git", ["push"])]),
    ("chroot /x -- git push", [("git", ["push"])]),
    ("env -u HOME -- git push", [("git", ["push"])]),
    # case arm, one-line and split across statements.
    ("case x in x) git push ;; esac", [("git", ["push"])]),
    ("case x\nin x) git push\nesac", [("git", ["push"])]),
    # Function bodies, groups, subshells, if/for/while bodies. The splitter
    # cuts the surrounding syntax into its own statements, so the pair is
    # asserted as present rather than as the only result.
    ("f() { git push; }", [("git", ["push"])]),
    ("function f { git push; }", [("git", ["push"])]),
    ("{ git push; }", [("git", ["push"])]),
    ("if true; then git push; fi", [("git", ["push"])]),
    ("for f in a; do git push; done", [("git", ["push"])]),
    ("while true; do git push; break; done", [("git", ["push"])]),
    # A command word that is merely an ARGUMENT stays an argument.
    ("echo git push", [("echo", ["git", "push"])]),
    ("man git pull", [("man", ["git", "pull"])]),
])
def test_command_start_resolves_the_real_command_word(command, expected):
    """One shared walk for both guards: wrappers (with positional arity),
    transparent '--', case arms, function bodies, grouping and if/for/while
    bodies. The containment detector used a wrapper-name-only loop and missed
    every compound shape (rc 0 on an outside write)."""
    resolved = _resolve(command)
    for pair in expected:
        assert pair in resolved, resolved


@pytest.mark.parametrize("command", ["X=1", "A=1 B=2"])
def test_command_start_skips_pure_assignment_statements(command):
    """A statement with no command word returns len(tokens), so the caller
    skips it instead of treating the assignment as a command."""
    code = (
        "import os, re, shlex\n"
        "def tokens_of(stmt):\n"
        "    lex = shlex.shlex(stmt, posix=True, punctuation_chars='()')\n"
        "    lex.whitespace_split = True\n"
        "    lex.commenters = ''\n"
        "    return list(lex)\n"
        f"stmt = split_shell_statements({command!r})[0][0]\n"
        "toks = tokens_of(stmt)\n"
        "print(json.dumps(command_start(toks) == len(toks)))\n"
    )
    r = subprocess.run(
        [sys.executable, "-c",
         "import json\n" + _resolver_source() + "\n" + code],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "true"


def test_subshell_closing_paren_stays_in_args_but_not_as_command():
    """( git push ) -> the command is git; the trailing ')' is an argument
    token. A containment detector must therefore read the command word, not
    args[0]."""
    assert _resolve("( git push )")[0] == ("git", ["push", ")"])
