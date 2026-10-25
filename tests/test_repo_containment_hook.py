"""Hook regression tests for hooks/1-generic/repo-containment.sh.

Repo-Containment ("prison mode", spec
``docs/concepts/repo-containment-prison-mode.md`` §7) confines agent WRITE
access to the project root, with an optional ``.tmp`` scratch sink as the only
sanctioned exception. The enforcement lives in a bash hook outside the Python
test suite, so these tests invoke it as a real subprocess with synthetic
PreToolUse JSON payloads and assert on the exit code (0 = allow, 2 = block),
mirroring ``tests/test_orchestrator_guard_hook.py``.

Payload shape follows ``hooks/1-generic/lib/hook_common.sh``: the hook reads
``tool_name``, ``tool_input.file_path`` / ``tool_input.command`` and ``cwd``.
The repo root is the nearest ancestor of ``cwd`` containing ``.meta-config/``,
so each test builds a ``tmp_path`` project root with a
``.meta-config/project.yaml``.

Run: python -m pytest tests/test_repo_containment_hook.py -v
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOK_PATH = _REPO_ROOT / "hooks" / "1-generic" / "repo-containment.sh"
_IMPL_PATH = _REPO_ROOT / "hooks" / "1-generic" / "repo-containment-impl.sh"

sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.tmp_paths import resolve_tmp_paths  # noqa: E402

_BASH = shutil.which("bash") or "bash"

pytestmark = pytest.mark.skipif(
    sys.platform not in ("win32", "linux", "darwin"), reason="requires bash"
)


def _write_config(root: Path, block: str) -> Path:
    """Materialize ``<root>/.meta-config/project.yaml`` with *block*."""
    meta = root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    config_path = meta / "project.yaml"
    config_path.write_text(block, encoding="utf-8")
    return config_path


def _project(tmp_path: Path, block: str | None = None) -> Path:
    """Create a project root with (optionally) a repo_containment block."""
    root = tmp_path / "project"
    root.mkdir()
    _write_config(
        root,
        block
        if block is not None
        else (
            'repo_containment:\n'
            '  enabled: true\n'
            '  tmp-sink:\n'
            '    enabled: true\n'
            '    path: ".tmp"\n'
        ),
    )
    return root


def _run_hook(payload: dict | str) -> subprocess.CompletedProcess:
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=raw,
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )


def _write_payload(path: Path, cwd: Path, tool: str = "Write") -> dict:
    return {
        "tool_name": tool,
        "tool_input": {"file_path": str(path)},
        "cwd": str(cwd),
    }


def _bash_payload(command: str, cwd: Path) -> dict:
    return {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(cwd),
    }


def _external_fixture() -> Path:
    """Create a directory outside every project root (AC-03/AC-05/AC-07).

    ``tmp_path`` is unsuitable here: its location depends on the configured
    pytest basetemp, which may itself sit inside a project root. The spec
    therefore requires ``tempfile.mkdtemp(dir=tempfile.gettempdir())`` plus an
    assertion that no ancestor carries ``.meta-config/``.
    """
    fixture = Path(tempfile.mkdtemp(dir=tempfile.gettempdir(), prefix="am-hook-ext-"))
    for ancestor in (fixture, *fixture.parents):
        assert not (ancestor / ".meta-config").is_dir(), (
            f"external fixture {fixture} is not isolated: {ancestor} has .meta-config/"
        )
    return fixture


@pytest.fixture()
def external_fixture():
    fixture = _external_fixture()
    try:
        yield fixture
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


# --- Write/Edit: path containment --------------------------------------


def test_write_inside_root_is_allowed(tmp_path):
    root = _project(tmp_path)
    result = _run_hook(_write_payload(root / "pkg" / "module.py", root))
    assert result.returncode == 0, result.stderr


def test_write_outside_root_is_blocked(tmp_path):
    root = _project(tmp_path)
    outside = root.parent / "outside.py"
    result = _run_hook(_write_payload(outside, root))
    assert result.returncode == 2
    assert "outside the repository root" in result.stderr


def test_write_into_tmp_sink_with_active_sink_is_allowed(tmp_path):
    root = _project(tmp_path)
    result = _run_hook(_write_payload(root / ".tmp" / "scratch.txt", root))
    assert result.returncode == 0, result.stderr


def test_write_into_tmp_sink_without_sink_is_blocked(tmp_path):
    root = _project(
        tmp_path,
        'repo_containment:\n'
        '  enabled: true\n'
        '  tmp-sink:\n'
        '    enabled: false\n'
        '    path: ".tmp"\n',
    )
    result = _run_hook(_write_payload(root / ".tmp" / "scratch.txt", root))
    assert result.returncode == 2
    assert "DISABLED tmp-sink" in result.stderr


def test_edit_missing_file_path_fails_closed(tmp_path):
    root = _project(tmp_path)
    payload = {"tool_name": "Edit", "tool_input": {}, "cwd": str(root)}
    result = _run_hook(payload)
    assert result.returncode == 2
    assert "no tool_input.file_path" in result.stderr


def test_read_tool_is_not_intercepted(tmp_path):
    root = _project(tmp_path)
    result = _run_hook(_write_payload(Path("/etc/passwd"), root, tool="Read"))
    assert result.returncode == 0, result.stderr


# --- enabled: false is a global opt-out --------------------------------


def test_disabled_mode_allows_even_an_outside_write(tmp_path):
    root = _project(tmp_path, "repo_containment:\n  enabled: false\n")
    result = _run_hook(_write_payload(root.parent / "outside.py", root))
    assert result.returncode == 0, result.stderr


# --- Bash: best-effort write detection ---------------------------------


def test_bash_write_pattern_outside_root_is_blocked(tmp_path):
    root = _project(tmp_path)
    result = _run_hook(
        _bash_payload(f"touch {root.parent}/evil.txt", root)
    )
    assert result.returncode == 2
    assert "outside the repository root" in result.stderr


def test_bash_redirection_outside_root_is_blocked(tmp_path):
    root = _project(tmp_path)
    result = _run_hook(
        _bash_payload(f"echo pwned > {root.parent}/evil.txt", root)
    )
    assert result.returncode == 2


def test_bash_write_inside_root_is_allowed(tmp_path):
    root = _project(tmp_path)
    result = _run_hook(_bash_payload("touch scratch.txt", root))
    assert result.returncode == 0, result.stderr


def test_bash_read_only_command_is_allowed(tmp_path):
    root = _project(tmp_path)
    result = _run_hook(_bash_payload("ls -la", root))
    assert result.returncode == 0, result.stderr


# --- Symlink escape (realpath check) -----------------------------------


@pytest.mark.skipif(os.name == "nt", reason="symlink semantics differ on Windows")
def test_symlink_escape_is_blocked(tmp_path):
    root = _project(tmp_path)
    os.symlink(root.parent, root / "escape")
    result = _run_hook(_write_payload(root / "escape" / "outside.py", root))
    assert result.returncode == 2


# --- Safe-side: empty / broken payloads never open the jail ------------


def test_empty_payload_fails_closed():
    result = _run_hook("")
    assert result.returncode == 2


def test_broken_json_payload_fails_closed():
    result = _run_hook("{not valid json")
    assert result.returncode == 2


def test_missing_config_defaults_to_containment_on(tmp_path):
    """No `.meta-config/` anywhere: the hook still blocks (F4).

    Note (Task 8): the exit 2 no longer comes from "containment ON with the
    working directory promoted to a root" — root resolution now fails closed
    with ``repo-containment.no-root``. Task 9 deliberately inverts and renames
    this test to ``test_missing_config_fails_closed`` (spec §"Bewusste
    Test-Änderung"); the assertion is unchanged on purpose.
    """
    root = tmp_path / "bare"
    root.mkdir()
    result = _run_hook(_write_payload(root.parent / "outside.py", root))
    assert result.returncode == 2


# --- Fail-closed anchor rule (Task 8) ----------------------------------


def test_cwd_outside_project_cannot_be_adopted(external_fixture):
    """AC-05: a `cwd` outside any project must never be promoted to a root.

    The regression the hook carried until Task 8: with ``cwd=/tmp`` and target
    ``/tmp/x.py`` it adopted ``$PWD``/``cwd`` as the repo root and allowed the
    write (exit 0) because the target was "inside" that fake root.
    """
    target = external_fixture / "x.py"
    result = _run_hook(_write_payload(target, external_fixture))
    assert result.returncode == 2, result.stderr
    assert "repo-containment.no-root" in result.stderr
    anchor = os.path.realpath(external_fixture)
    assert f"no project root found above {anchor}" in result.stderr
    assert f"anchor:    {anchor}" in result.stderr


def test_relative_target_with_depth_is_checked_at_real_location(tmp_path):
    """AC-33: a relative target is resolved against `cwd`, not the repo root."""
    root = _project(tmp_path)
    deep = root / "a" / "b"
    deep.mkdir(parents=True)

    inside = _run_hook(_write_payload(Path("../../x"), deep))
    assert inside.returncode == 0, inside.stderr

    outside = _run_hook(_write_payload(Path("../../../../etc/passwd"), deep))
    assert outside.returncode == 2, outside.stderr
    assert "outside the repository root" in outside.stderr


def test_hook_sink_matches_tmp_paths(tmp_path):
    """Shared contract: the hook's effective sink equals TmpPaths.absolute."""
    import yaml

    root = _project(
        tmp_path,
        'repo_containment:\n'
        '  enabled: true\n'
        '  tmp-sink:\n'
        '    enabled: true\n'
        '    path: "scratch/x"\n',
    )
    config = yaml.safe_load(
        (root / ".meta-config" / "project.yaml").read_text(encoding="utf-8")
    )
    paths = resolve_tmp_paths(root, config)
    assert paths.absolute is not None

    stderr = _outside_block_stderr(root)
    allowed = next(line for line in stderr.splitlines() if "allowed:" in line)
    assert allowed.strip().endswith(f"and under {paths.absolute}")
    assert str(paths.absolute) == os.path.realpath(root / "scratch" / "x")


# --- Safe-side: invalid tmp-sink paths fall back to ".tmp" -------------
# The inline config reader mirrors scripts/lib/repo_containment.py::
# tmp_sink_path_error — a Windows drive-letter prefix or a path that
# normalizes to the repo root itself must not become the effective sink. On a
# blocked OUTSIDE write, block_write() prints the effective sink path in
# stderr, which makes the ".tmp" fallback observable without extra plumbing.


def _outside_block_stderr(root: Path) -> str:
    result = _run_hook(_write_payload(root.parent / "outside.py", root))
    assert result.returncode == 2, result.stderr
    return result.stderr


def test_valid_custom_sink_path_is_reflected_in_stderr(tmp_path):
    """Control: a valid custom sink path IS used (proves the reader works)."""
    root = _project(
        tmp_path,
        'repo_containment:\n'
        '  enabled: true\n'
        '  tmp-sink:\n'
        '    enabled: true\n'
        '    path: "scratch/x"\n',
    )
    assert f"under {root}/scratch/x" in _outside_block_stderr(root)


def test_sink_path_dot_slash_dot_falls_back_to_default(tmp_path):
    root = _project(
        tmp_path,
        'repo_containment:\n'
        '  enabled: true\n'
        '  tmp-sink:\n'
        '    enabled: true\n'
        '    path: "./."\n',
    )
    stderr = _outside_block_stderr(root)
    assert f"under {root}/.tmp" in stderr
    assert "./." not in stderr


def test_sink_path_drive_letter_falls_back_to_default(tmp_path):
    root = _project(
        tmp_path,
        'repo_containment:\n'
        '  enabled: true\n'
        '  tmp-sink:\n'
        '    enabled: true\n'
        '    path: "C:\\\\x"\n',
    )
    stderr = _outside_block_stderr(root)
    assert f"under {root}/.tmp" in stderr
    assert "C:\\x" not in stderr


# --- Hook source health ------------------------------------------------

def test_hook_wrapper_and_impl_are_valid_bash():
    for script in (_HOOK_PATH, _IMPL_PATH):
        result = subprocess.run(
            [_BASH, "-n", str(script)], capture_output=True, text=True
        )
        assert result.returncode == 0, (script, result.stderr)


# --- issue #630: self-health wrapper carve-out ----------------------------
# repo-containment.sh (thin wrapper) syntax-checks repo-containment-impl.sh
# with `bash -n` before running it. If impl.sh is broken, the wrapper allows
# Write/Edit on EXACTLY the impl script (and the wrapper itself, mirroring
# orchestrator-guard.sh's own-directory carve-out) while every other path —
# including siblings under the same hooks directory — still fails CLOSED. The
# carve-out was narrowed from "any file under $SCRIPT_DIR" after review.


def _isolated_wrapper_with_broken_impl(tmp_path) -> Path:
    """Deploy an isolated wrapper + broken impl pair under <tmp>/.claude/hooks/.

    Mirrors the real deployment layout so "the impl script" vs. "any sibling
    under the same directory" is a meaningful distinction.
    """
    hooks_dir = tmp_path / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True)
    isolated_hook = hooks_dir / "repo-containment.sh"
    isolated_hook.write_text(_HOOK_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    broken_impl = hooks_dir / "repo-containment-impl.sh"
    # Unclosed `if` -> `bash -n` must fail (the exact trigger for the carve-out).
    broken_impl.write_text("if true; then\n", encoding="utf-8")
    return isolated_hook


def _run_isolated(hook: Path, payload: dict, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_BASH, str(hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )


def test_broken_impl_blocks_bash_calls(tmp_path):
    hook = _isolated_wrapper_with_broken_impl(tmp_path)
    result = _run_isolated(hook, _bash_payload("ls -la", tmp_path), tmp_path)
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "syntax error" in result.stderr.lower()


def test_broken_impl_allows_edit_of_impl_script_only(tmp_path):
    hook = _isolated_wrapper_with_broken_impl(tmp_path)
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(hook.parent / "repo-containment-impl.sh")},
        "cwd": str(tmp_path),
    }
    result = _run_isolated(hook, payload, tmp_path)
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"


def test_broken_impl_blocks_edit_of_sibling_under_hooks_dir(tmp_path):
    hook = _isolated_wrapper_with_broken_impl(tmp_path)
    sibling = hook.parent / "lib" / "hook_common.sh"
    sibling.parent.mkdir(parents=True, exist_ok=True)
    sibling.write_text("# sibling\n", encoding="utf-8")
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(sibling)},
        "cwd": str(tmp_path),
    }
    result = _run_isolated(hook, payload, tmp_path)
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"


def test_broken_impl_allows_edit_of_wrapper_itself(tmp_path):
    """The wrapper is exempted too, mirroring orchestrator-guard.sh."""
    hook = _isolated_wrapper_with_broken_impl(tmp_path)
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(hook)},
        "cwd": str(tmp_path),
    }
    result = _run_isolated(hook, payload, tmp_path)
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"


@pytest.mark.parametrize(
    "yaml_path",
    ['"\\\\\\\\server\\\\share\\\\x"', '"CON"', '".GIT"', '".Codex/out"', '"a:b"', '"x."'],
)
def test_unsafe_sink_path_falls_back_to_default(tmp_path, yaml_path):
    """IC-15 Nr. 27 f: the hook mirrors the hardened rules (UNC, reserved, protected)."""
    root = _project(
        tmp_path,
        'repo_containment:\n  enabled: true\n  tmp-sink:\n    enabled: true\n'
        f'    path: {yaml_path}\n',
    )
    assert f"under {root}/.tmp" in _outside_block_stderr(root)


def test_sink_path_backslash_is_canonicalized(tmp_path):
    root = _project(
        tmp_path,
        'repo_containment:\n  enabled: true\n  tmp-sink:\n    enabled: true\n'
        '    path: "scratch\\\\out"\n',
    )
    assert f"under {root}/scratch/out" in _outside_block_stderr(root)
