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
