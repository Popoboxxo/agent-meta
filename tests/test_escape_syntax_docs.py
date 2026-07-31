"""Regression test: the documented placeholder-escape syntax must match
scripts/lib/config.py's actual `substitute()` implementation.

Run: python -m pytest tests/test_escape_syntax_docs.py -v
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SOURCE_RULE = _REPO_ROOT / "rules" / "1-generic" / "architecture.md"


def test_architecture_doc_documents_real_escape_syntax():
    content = _SOURCE_RULE.read_text(encoding="utf-8")
    assert "{{%VAR%}}" in content, (
        "architecture.md must document the real escape token {{%VAR%}} "
        "(see scripts/lib/config.py substitute())"
    )
