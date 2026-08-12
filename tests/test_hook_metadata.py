"""Regression test: hook header `# matcher: ""` must parse to an empty string,
not the literal two-character string of quote marks.

Run: python -m pytest tests/test_hook_metadata.py -v
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.hooks import parse_hook_metadata


def test_quoted_empty_matcher_parses_to_empty_string():
    content = (
        "#!/bin/bash\n"
        "# hook: orchestrator-guard\n"
        '# matcher: ""\n'
        "# event: PreToolUse\n"
    )
    meta = parse_hook_metadata(content)
    assert meta.get("matcher", "") == ""


def test_unquoted_matcher_is_unaffected():
    content = (
        "#!/bin/bash\n"
        "# hook: dod-push-check\n"
        "# matcher: Bash\n"
        "# event: PreToolUse\n"
    )
    meta = parse_hook_metadata(content)
    assert meta["matcher"] == "Bash"


def test_orchestrator_guard_source_file_parses_to_empty_matcher():
    """Guards against the real header regressing back to a quoted literal."""
    path = _REPO_ROOT / "hooks" / "1-generic" / "orchestrator-guard.sh"
    meta = parse_hook_metadata(path.read_text(encoding="utf-8"))
    assert meta.get("matcher", "") == ""


def test_graphify_search_guard_metadata_parses():
    path = _REPO_ROOT / "hooks" / "0-external" / "graphify-search-guard.sh"
    meta = parse_hook_metadata(path.read_text(encoding="utf-8"))
    assert meta["hook"] == "graphify-search-guard"
    assert meta["event"] == "PreToolUse"
    assert meta["matcher"] == "Bash|Grep"
    assert meta["provider"] == "Claude"
    assert meta["enabled_by_default"] == "false"


def test_graphify_read_guard_metadata_parses():
    path = _REPO_ROOT / "hooks" / "0-external" / "graphify-read-guard.sh"
    meta = parse_hook_metadata(path.read_text(encoding="utf-8"))
    assert meta["hook"] == "graphify-read-guard"
    assert meta["event"] == "PreToolUse"
    assert meta["matcher"] == "Read|Glob"
    assert meta["provider"] == "Claude"
    assert meta["enabled_by_default"] == "false"
