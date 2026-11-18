"""Hook regression tests for hooks/1-generic/artifact-path-guard.sh (T16, #1186).

The artifact-path-guard is a *routing convention*, not a security boundary.
It reads ``<root>/.meta-config/artifact-locations.resolved.json`` (Stage 14c,
T15) and routes a Write/Edit target by path:

    marker -> unmanaged[] -> legacy[] -> class path -> managed tree -> root

* rc 0 = allow / warn, rc 2 = block (only in strict mode for misroutes;
  ``legacy[]`` targets always block once the hook is enabled),
* missing/corrupt data file fails open (one warning line, rc 0),
* directory markers are never blocked.

The hook is a bash script outside the Python suite, so these tests invoke it
as a real subprocess with synthetic PreToolUse payloads.  Run:

    python -m pytest tests/test_artifact_path_guard_hook.py -v
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

from tests.timeouts import SCRIPT_TIMEOUT

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.hooks import parse_hook_metadata  # noqa: E402

_HOOK_PATH = _REPO_ROOT / "hooks" / "1-generic" / "artifact-path-guard.sh"

_BASH = shutil.which("bash") or "bash"

pytestmark = pytest.mark.skipif(
    sys.platform not in ("win32", "linux", "darwin"), reason="requires bash"
)

# Minimal resolved-matrix fixture.  ``docs`` is the managed tree (shared by
# reviews/spikes/adr/plans); ``spikes`` deliberately points at ``docs/spikes-2``
# so a write to ``docs/spikes/`` is a misroute.  ``project-docs`` is a file-set
# class (null path, files listed in ``patterns``).
_CLASSES = [
    {"name": "reviews", "path": "docs/reviews", "mode": "files", "patterns": []},
    {"name": "spikes", "path": "docs/spikes-2", "mode": "files", "patterns": []},
    {"name": "adr", "path": "docs/adr", "mode": "files", "patterns": []},
    {"name": "plans", "path": "docs/plans", "mode": "files", "patterns": []},
    {"name": "scratch", "path": ".tmp", "mode": "files", "patterns": []},
    {
        "name": "project-docs",
        "path": None,
        "mode": "files",
        "patterns": [
            "docs/ARCHITECTURE.md",
            "docs/CODEBASE_OVERVIEW.md",
            "docs/REQUIREMENTS.md",
            "docs/issue-labels.md",
        ],
    },
]
# D3: the legacy ADR pattern only matches the OLD flat naming, which sits
# *inside* the current class path docs/adr -> legacy must win over class path.
_LEGACY = [
    "docs/plans/audit-*.md",
    "docs/adr/[0-9][0-9][0-9][0-9]-*.md",
    "docs/conclusions/**",
]
_UNMANAGED = ["docs/api/**", ".meta-config/issue-labels-state.json"]


@pytest.fixture
def project():
    """An isolated project root (external fixture, cf. repo-containment tests)."""
    root = Path(tempfile.mkdtemp(prefix="am-path-guard-", dir=tempfile.gettempdir()))
    yield root
    shutil.rmtree(root, ignore_errors=True)


def _write_data(
    root: Path,
    *,
    strict: bool = False,
    classes=None,
    legacy=None,
    unmanaged=None,
    root_value=None,
    corrupt: bool = False,
) -> Path:
    """Materialize <root>/.meta-config/artifact-locations.resolved.json."""
    meta = root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    target = meta / "artifact-locations.resolved.json"
    if corrupt:
        target.write_text("{ this is not valid json ", encoding="utf-8")
        return target
    payload = {
        "schema_version": "1",
        "enabled": True,
        "strict": strict,
        "root": str(root_value if root_value is not None else root),
        "preset": "default",
        "classes": _CLASSES if classes is None else classes,
        "legacy": _LEGACY if legacy is None else legacy,
        "unmanaged": _UNMANAGED if unmanaged is None else unmanaged,
        "baseline": {"generated_at": "2026-11-17T00:00:00Z", "legacy_files": []},
    }
    target.write_text(json.dumps(payload), encoding="utf-8")
    return target


def _run(
    root: Path,
    target: str,
    *,
    strict: bool = False,
    tool: str = "Write",
    write_data: bool = True,
    **data_kwargs,
) -> subprocess.CompletedProcess:
    """Run the hook as a real subprocess against a synthetic PreToolUse payload."""
    if write_data:
        _write_data(root, strict=strict, **data_kwargs)
    payload = {
        "tool_name": tool,
        "tool_input": {"file_path": target},
        "cwd": str(root),
    }
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(root)
    return subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(root),
        env=env,
        timeout=SCRIPT_TIMEOUT,
    )


def _combined(result: subprocess.CompletedProcess) -> str:
    return result.stdout + result.stderr


# ---------------------------------------------------------------------------
# 1. Opt-in header (#4.5 / RVW-1186-01)
# ---------------------------------------------------------------------------
def test_header_is_opt_in():
    meta = parse_hook_metadata(_HOOK_PATH.read_text(encoding="utf-8"))
    assert meta.get("enabled_by_default") == "false"
    assert meta.get("event") == "PreToolUse"
    assert meta.get("matcher", "") == ""


# ---------------------------------------------------------------------------
# 2. Class path -> allow
# ---------------------------------------------------------------------------
def test_allow_target_in_class_path(project):
    result = _run(project, "docs/reviews/x.md")
    assert result.returncode == 0
    assert _combined(result).strip() == ""


# ---------------------------------------------------------------------------
# 3. Misroute in managed tree -> warn (rc 0)
# ---------------------------------------------------------------------------
def test_warn_target_in_managed_tree_outside_class(project):
    result = _run(project, "docs/spikes/x.md")  # spikes.path = docs/spikes-2
    assert result.returncode == 0
    assert "artifact-path-guard" in _combined(result).lower()
    assert "docs/spikes-2" in _combined(result)  # expected path named


# ---------------------------------------------------------------------------
# 4. Same misroute with strict -> block (rc 2), message names expected path
# ---------------------------------------------------------------------------
def test_block_same_case_with_strict(project):
    result = _run(project, "docs/spikes/x.md", strict=True)
    assert result.returncode == 2
    assert "docs/spikes-2" in _combined(result)


# ---------------------------------------------------------------------------
# 5. legacy[] target blocks in BOTH modes (AC-09)
# ---------------------------------------------------------------------------
def test_block_legacy_target_in_both_modes(project):
    for strict in (False, True):
        result = _run(project, "docs/plans/audit-x.md", strict=strict)
        assert result.returncode == 2, strict
        assert "legacy" in _combined(result).lower()


# ---------------------------------------------------------------------------
# 6. D3: legacy pattern inside class path wins (0002 vs ADR-002)
# ---------------------------------------------------------------------------
def test_legacy_pattern_wins_over_class_path(project):
    blocked = _run(project, "docs/adr/0002-neu.md")  # matches legacy glob
    assert blocked.returncode == 2
    allowed = _run(project, "docs/adr/ADR-002_neu.md")  # canonical name
    assert allowed.returncode == 0
    assert _combined(allowed).strip() == ""


# ---------------------------------------------------------------------------
# 7. Markers never blocked, in both modes
# ---------------------------------------------------------------------------
def test_marker_files_are_never_blocked(project):
    for strict in (False, True):
        for marker in (".gitkeep", ".gitignore", ".keep"):
            result = _run(project, f"docs/conclusions/{marker}", strict=strict)
            assert result.returncode == 0, (strict, marker)
            assert _combined(result).strip() == ""


# ---------------------------------------------------------------------------
# 8. src/ and tests/ are untouched (not managed trees)
# ---------------------------------------------------------------------------
def test_allow_src_and_tests_untouched(project):
    for target in ("src/app.py", "tests/test_x.py"):
        result = _run(project, target, strict=True)
        assert result.returncode == 0, target
        assert _combined(result).strip() == ""


# ---------------------------------------------------------------------------
# 9. project-docs file-set: declared file allowed, undeclared sibling not
# ---------------------------------------------------------------------------
def test_project_docs_file_is_allowed(project):
    for strict in (False, True):
        ok = _run(project, "docs/issue-labels.md", strict=strict)
        assert ok.returncode == 0, strict
        assert _combined(ok).strip() == ""

        undeclared = _run(project, "docs/labels.md", strict=strict)
        if strict:
            assert undeclared.returncode == 2
        else:
            assert undeclared.returncode == 0
            assert "artifact-path-guard" in _combined(undeclared).lower()


# ---------------------------------------------------------------------------
# 10. unmanaged[] allowed in both modes (D-8)
# ---------------------------------------------------------------------------
def test_unmanaged_target_is_allowed(project):
    for strict in (False, True):
        for target in ("docs/api/x.md", ".meta-config/issue-labels-state.json"):
            result = _run(project, target, strict=strict)
            assert result.returncode == 0, (strict, target)
            assert _combined(result).strip() == ""


# ---------------------------------------------------------------------------
# 11. Root files are outside managed trees -> allow
# ---------------------------------------------------------------------------
def test_allow_target_outside_managed_trees(project):
    result = _run(project, "README.md", strict=True)
    assert result.returncode == 0
    assert _combined(result).strip() == ""


# ---------------------------------------------------------------------------
# 12. Fail-open: missing data file
# ---------------------------------------------------------------------------
def test_fail_open_on_missing_datafile(project):
    result = _run(project, "docs/reviews/x.md", write_data=False)
    assert result.returncode == 0
    lines = [line for line in _combined(result).splitlines() if line.strip()]
    assert len(lines) == 1
    assert "fail-open" in lines[0].lower()


# ---------------------------------------------------------------------------
# 13. Fail-open: corrupt data file
# ---------------------------------------------------------------------------
def test_fail_open_on_corrupt_json(project):
    result = _run(project, "docs/reviews/x.md", corrupt=True)
    assert result.returncode == 0
    lines = [line for line in _combined(result).splitlines() if line.strip()]
    assert len(lines) == 1
    assert "fail-open" in lines[0].lower()


# ---------------------------------------------------------------------------
# 14. Shared helpers are used, not duplicated (#1151)
# ---------------------------------------------------------------------------
def test_uses_shared_helpers():
    source = _HOOK_PATH.read_text(encoding="utf-8")
    assert "lib/hook_common.sh" in source
    assert "hook_json_get" in source
    assert "hook_known_tool_name" in source
    # Definitions live only in hook_common.sh, never in the consumer.
    assert "hook_json_get()" not in source
    assert "hook_known_tool_name()" not in source


# ---------------------------------------------------------------------------
# 15. Targets outside the project root are not this hook's job
# ---------------------------------------------------------------------------
def test_outside_project_root_is_not_this_hooks_job(project):
    result = _run(project, "/etc/passwd", strict=True)
    assert result.returncode == 0
    assert _combined(result).strip() == ""


# ---------------------------------------------------------------------------
# 16. No content/extension checks: .txt and .md route identically
# ---------------------------------------------------------------------------
def test_no_content_or_extension_checks(project):
    # Same routing decision for a misroute, regardless of extension.
    md = _run(project, "docs/spikes/x.md")
    txt = _run(project, "docs/spikes/x.txt")
    assert md.returncode == txt.returncode
    assert ("docs/spikes-2" in _combined(md)) == ("docs/spikes-2" in _combined(txt))
    # And for an allowed class-path target.
    md_ok = _run(project, "docs/reviews/x.md")
    txt_ok = _run(project, "docs/reviews/x.txt")
    assert md_ok.returncode == txt_ok.returncode == 0
