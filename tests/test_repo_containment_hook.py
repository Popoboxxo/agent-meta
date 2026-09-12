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
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOK_PATH = _REPO_ROOT / "hooks" / "1-generic" / "repo-containment.sh"
_IMPL_PATH = _REPO_ROOT / "hooks" / "1-generic" / "repo-containment-impl.sh"

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
    """No `.meta-config/` anywhere: the hook resolves to ENABLED (F4)."""
    root = tmp_path / "bare"
    root.mkdir()
    result = _run_hook(_write_payload(root.parent / "outside.py", root))
    assert result.returncode == 2


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
