"""Tests for the ``--create-hook`` starter template (MB-4, audit 2026-11-25).

The generated hook must be a working, non-blocking starter that documents the
shared helper lib (``lib/hook_common.sh``) instead of the former empty
``# TODO: implement hook logic here`` stub and its inline ``python3 -c``
JSON-parsing tip. A copy-paste template is what every new project hook starts
from, so the contract is pinned here:

- the starter sources ``lib/hook_common.sh`` and shows ``hook_json_get``,
- it contains no TODO, no inline-Python one-liner, no provider-name logic,
- it renders without leaving ``%(...)`` placeholders behind,
- it is LF-only and syntactically valid bash,
- the policy decision is "allow": exit 0 for any payload, even without the lib
  (a project hook is not a security control and fails OPEN).

Run: python3 -m pytest tests/test_hook_template.py -q
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib import hooks as hooks_mod  # noqa: E402
from lib.log import SyncLog  # noqa: E402

_DOCS_REF = "docs/guides/features/hooks.md"


def _create(tmp_path: Path, name: str = "demo-guard") -> Path:
    hooks_mod.create_hook(tmp_path, name, SyncLog(), dry_run=False)
    return tmp_path / ".claude" / "hooks" / f"{name}.sh"


def test_template_documents_shared_helper_lib(tmp_path):
    """The starter points at the deployed helper lib, not a private parser."""
    content = _create(tmp_path).read_text(encoding="utf-8")

    assert 'source "$SCRIPT_DIR/lib/hook_common.sh"' in content
    assert "hook_json_get" in content
    assert "hook_json_get_many" in content
    assert _DOCS_REF in content
    # Fail-open contract must be stated for project hooks.
    assert "fails OPEN" in content


def test_template_has_no_todo_or_inline_python(tmp_path):
    """No empty stub and no ``python3 -c`` copy-paste trap."""
    content = _create(tmp_path).read_text(encoding="utf-8")

    assert "TODO" not in content
    assert "python3 -c" not in content
    # Provider names must not leak into a generic template.
    for provider in ("Claude", "Antigravity", "Gemini", "Opencode", "Mammouth"):
        assert provider not in content


def test_template_renders_without_stray_placeholders(tmp_path):
    """No ``%(...)`` placeholder survives rendering (and no ``%`` crash)."""
    rendered = hooks_mod.HOOK_TEMPLATE_SH % {
        "stem": "percent-100-check",
        "description": "Percent 100 check hook",
    }

    assert "%(" not in rendered
    assert "# hook: percent-100-check" in rendered
    assert "# description: Percent 100 check hook" in rendered


def test_created_hook_is_lf_only_and_syntactically_valid_bash(tmp_path):
    """The starter must be LF-only and parse as a bash script."""
    created = _create(tmp_path)
    raw = created.read_bytes()

    assert b"\r" not in raw
    assert raw.startswith(b"#!/bin/bash\n")

    bash = shutil.which("bash")
    if not bash:
        pytest.skip("bash not available")
    result = subprocess.run(
        [bash, "-n", str(created)], capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr


def _deploy_helper_lib(tmp_path: Path) -> None:
    """Mirror what sync_hook_lib() deploys into ``<hooks_dir>/lib/``."""
    lib_dir = tmp_path / ".claude" / "hooks" / "lib"
    lib_dir.mkdir(parents=True, exist_ok=True)
    source_lib = _REPO_ROOT / "hooks" / "1-generic" / "lib"
    for name in ("hook_common.sh", "hook_json_many.py"):
        shutil.copy2(source_lib / name, lib_dir / name)


def _run_hook(created: Path, payload: str, env: dict | None = None) -> subprocess.CompletedProcess:
    bash = shutil.which("bash")
    if not bash:
        pytest.skip("bash not available")
    return subprocess.run(
        [bash, str(created)],
        input=payload,
        capture_output=True,
        text=True,
        check=False,
        env=env or {"PATH": "/usr/bin:/bin"},
    )


@pytest.fixture
def python_path_env():
    """PATH that really resolves the interpreter ``hook_common.sh`` probes for.

    The starter's allow path only proves anything when ``hook_have_python``
    finds python3/python: with an interpreter-less PATH the script exits 0
    before reading the payload and the test would be vacuous. Without a real
    interpreter on this machine there is nothing to test, so skip instead.
    """
    for name in ("python3", "python"):
        found = shutil.which(name)
        if found:
            return {"PATH": f"{Path(found).parent}:/usr/bin:/bin"}
    pytest.skip("no python3/python on PATH — allow-policy test would be vacuous")


@pytest.mark.parametrize(
    "payload",
    [
        '{"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/x"}}',
        '{"tool_name": "Edit", "tool_input": {"file_path": "a.py"}}',
        "not json at all",
        "",
    ],
)
def test_starter_allows_every_call(tmp_path, payload, python_path_env):
    """Starter policy: allow, exit 0 — with the helper lib and a real python."""
    _deploy_helper_lib(tmp_path)
    created = _create(tmp_path)

    result = _run_hook(created, payload, env=python_path_env)

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_starter_fails_open_without_helper_lib(tmp_path):
    """A missing lib must not turn a project hook into a blocker."""
    created = _create(tmp_path)

    result = _run_hook(created, '{"tool_name": "Bash"}')

    assert result.returncode == 0, result.stderr
