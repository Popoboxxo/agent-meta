"""Regression tests for the composition/patch engine (scripts/lib/agents.py).

Run: python -m pytest tests/test_composition_engine.py -v
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.agents import _find_section_bounds, apply_patch
from lib.consistency.frontmatter import _check_patch_anchors
from lib.log import SyncLog


SECTION_WITH_CODE_BLOCK = """## Build & Development

```bash
# Build
python scripts/sync.py

# Tests
python scripts/sync.py --validate
```

## Next Section

Some other content.
"""


def test_find_section_bounds_skips_hash_comments_in_fenced_code_block():
    lines = SECTION_WITH_CODE_BLOCK.splitlines(keepends=True)
    bounds = _find_section_bounds(lines, "## Build & Development")
    assert bounds is not None
    start, end = bounds
    # The section must extend up to (not into) "## Next Section", i.e. it must
    # include the full fenced code block including its "# Build" / "# Tests" comments.
    section_text = "".join(lines[start:end])
    assert "python scripts/sync.py --validate" in section_text
    assert "## Next Section" not in section_text


def test_patch_replace_does_not_truncate_at_code_block_comment():
    log = SyncLog()
    patch = {
        "op": "replace",
        "anchor": "## Build & Development",
        "content": "## Build & Development\n\nReplaced entirely.\n",
    }
    result = apply_patch(SECTION_WITH_CODE_BLOCK, patch, log, "test-source")
    assert "Replaced entirely." in result
    # Old code-block remnants must be fully gone, not just the heading.
    assert "python scripts/sync.py --validate" not in result
    assert "## Next Section" in result


def test_validator_rejects_anchor_that_is_only_a_substring(tmp_path):
    base_path = tmp_path / "agents" / "1-generic" / "example.md"
    base_path.parent.mkdir(parents=True)
    base_path.write_text("## Configuration\n\nSome text.\n", encoding="utf-8")

    patches = [{"op": "replace", "anchor": "## Config", "content": "## Config\n\nNew.\n"}]
    findings = _check_patch_anchors(
        patches, "1-generic/example.md", "some/override.md", tmp_path,
    )
    check_ids = [f.check for f in findings]
    assert "frontmatter.patch-anchor-not-found" in check_ids


def test_patch_replace_preserves_base_file_crlf_line_endings():
    base = "## Section\r\n\r\nOld content.\r\n\r\n## Next\r\n\r\nOther.\r\n"
    patch = {"op": "replace", "anchor": "## Section", "content": "## Section\n\nNew content.\n"}
    log = SyncLog()
    result = apply_patch(base, patch, log, "test-source")
    # Every line in the result must end with \r\n, matching the CRLF base file.
    for line in result.splitlines(keepends=True):
        if line.strip("\r\n"):
            assert line.endswith("\r\n"), f"expected CRLF line ending, got {line!r}"
