"""Regression tests for hooks/0-external/graphify-{read,search}-guard.sh
(issue #599: GRAPHIFY_BIN trusted without validation).

Background: both guards used to execute `${GRAPHIFY_BIN:-graphify}`
directly with no validation -- any process able to set GRAPHIFY_BIN in the
agent's environment could get its own arbitrary binary executed on every
Read/Glob/Bash/Grep call that fires these guards. They now resolve the
binary via hook_resolve_graphify_bin() (hooks/1-generic/lib/hook_common.sh,
covered in detail by tests/test_hook_common_lib.py) before executing it.
These tests exercise the two guard scripts end-to-end as subprocesses.

Run: python -m pytest tests/test_graphify_guard_hooks.py -v
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_READ_GUARD = _REPO_ROOT / "hooks" / "0-external" / "graphify-read-guard.sh"
_SEARCH_GUARD = _REPO_ROOT / "hooks" / "0-external" / "graphify-search-guard.sh"

_BASH = shutil.which("bash") or "bash"

pytestmark = pytest.mark.skipif(
    sys.platform not in ("win32", "linux", "darwin"), reason="requires bash"
)


def _fake_graphify(tmp_path: Path, name: str = "graphify") -> Path:
    """A fake graphify binary that echoes its subcommand and consumes stdin,
    so the guard's `exit $?` and pipe both have something real to observe."""
    p = tmp_path / name
    p.write_text(
        "#!/bin/bash\n"
        'echo "graphify-called: $1 $2"\n'
        "cat >/dev/null\n"
        "exit 0\n",
        encoding="utf-8",
    )
    p.chmod(0o700)
    return p


@pytest.mark.parametrize("guard_path,expected_subcommand", [
    (_READ_GUARD, "read"),
    (_SEARCH_GUARD, "search"),
])
def test_guard_passes_through_when_graphify_not_installed(guard_path, expected_subcommand, tmp_path):
    result = subprocess.run(
        [_BASH, str(guard_path)],
        input="{}",
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "GRAPHIFY_BIN": ""},
    )
    assert result.returncode == 0


@pytest.mark.parametrize("guard_path,expected_subcommand", [
    (_READ_GUARD, "read"),
    (_SEARCH_GUARD, "search"),
])
def test_guard_invokes_valid_graphify_on_path(guard_path, expected_subcommand, tmp_path):
    fake_bin_dir = tmp_path / "bin"
    fake_bin_dir.mkdir()
    _fake_graphify(fake_bin_dir)
    result = subprocess.run(
        [_BASH, str(guard_path)],
        input="{}",
        capture_output=True,
        text=True,
        env={"PATH": f"{fake_bin_dir}:/usr/bin:/bin"},
    )
    assert result.returncode == 0
    assert f"graphify-called: hook-guard" in result.stdout
    assert expected_subcommand in result.stdout


@pytest.mark.parametrize("guard_path", [_READ_GUARD, _SEARCH_GUARD])
def test_guard_rejects_malicious_graphify_bin_env_override(guard_path, tmp_path):
    """A GRAPHIFY_BIN pointing at an arbitrary, wrongly-named, absolute
    binary must NOT be executed -- the guard falls back to a plain PATH
    lookup of the literal name "graphify" instead (which is absent here,
    so the call passes through untouched rather than running the evil
    binary)."""
    evil = tmp_path / "evil-binary"
    evil.write_text("#!/bin/bash\necho PWNED\nexit 0\n", encoding="utf-8")
    evil.chmod(0o700)

    result = subprocess.run(
        [_BASH, str(guard_path)],
        input="{}",
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "GRAPHIFY_BIN": str(evil)},
    )
    assert "PWNED" not in result.stdout
    assert result.returncode == 0  # graphify (real name) not found -> pass through
