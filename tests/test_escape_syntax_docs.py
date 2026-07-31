"""Regression test: the documented placeholder-escape syntax must match
scripts/lib/config.py's actual `substitute()` implementation, and must
survive being rendered by sync.py without being silently mangled.

Background (Task 8 self-referential bug): the escape mechanism works by
finding the literal raw token `{{%VAR%}}` in SOURCE text and stripping the
`%` signs when rendering, emitting `{{VAR}}` in the output. That means any
attempt to *document* the escape mechanism by embedding a literal, raw
`{{%VAR%}}`-shaped token directly in this rule file is self-defeating: the
very rule file is itself processed by `substitute()` when sync.py generates
`.claude/rules/architecture.md` (and the other provider copies), so the raw
token gets silently stripped down to `{{VAR}}` in the rendered output ---
making the rendered doc claim the escape token IS `{{VAR}}`, which is wrong
and exactly the original bug Task 8 was supposed to fix.

This test therefore checks two things:
1. The source doc does NOT contain a raw, processable `{{%...%}}`-shaped
   token (which would trigger the self-referential stripping bug again).
2. The source doc still accurately points readers to the real mechanism
   (mentions `substitute()` / `config.py`), so the documentation has real
   content instead of just being scrubbed of the bug.

Run: python -m pytest tests/test_escape_syntax_docs.py -v
"""

import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SOURCE_RULE = _REPO_ROOT / "rules" / "2-platform" / "agent-meta-architecture.md"

sys.path.insert(0, str(_REPO_ROOT / "scripts"))


def _extract_section(content: str, heading: str) -> str:
    """Extract a '## <heading>' section's body up to the next '## ' heading."""
    pattern = rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    assert match, f"Section '## {heading}' not found in {content[:80]!r}..."
    return match.group(1)


def test_source_doc_does_not_contain_raw_escape_token():
    """The raw {{%VAR%}} token must never appear as literal, processable text
    in the source rule file -- substitute() would silently strip the '%'
    signs on every sync.py run, making the rendered doc claim the wrong
    escape syntax (byte-identical to the original bug)."""
    content = _SOURCE_RULE.read_text(encoding="utf-8")
    section = _extract_section(content, "Platzhalter-Escape")
    assert "{{%" not in section, (
        "architecture.md's Platzhalter-Escape section must not contain a raw "
        "'{{%' sequence -- sync.py's substitute() strips the surrounding "
        "'%' signs on every render, so any literal '{{%VAR%}}'-shaped token "
        "here is guaranteed to render as the (wrong) bare '{{VAR}}' token in "
        "all deployed rule copies (.claude/rules/architecture.md etc.), "
        "silently reintroducing the original Task 8 bug."
    )


def test_source_doc_points_to_real_implementation():
    """The section must still accurately describe the real mechanism by
    referencing the actual implementation, so it isn't just scrubbed of the
    bug without conveying correct information."""
    content = _SOURCE_RULE.read_text(encoding="utf-8")
    section = _extract_section(content, "Platzhalter-Escape")
    assert "substitute()" in section or "config.py" in section, (
        "architecture.md's Platzhalter-Escape section must reference "
        "scripts/lib/config.py's substitute() so readers can find the exact "
        "implementation of the escape mechanism."
    )


def test_rendered_copy_survives_sync_unchanged_in_meaning():
    """End-to-end: render the section through the real substitute() function
    (as sync.py would) and confirm the rendered text still does not read as
    if a bare '{{VAR}}' token alone is presented as *the* escape syntax, and
    still doesn't contain a raw '{{%' sequence (which would prove the
    stripping bug fired during render)."""
    from lib.config import SyncLog, substitute  # type: ignore

    content = _SOURCE_RULE.read_text(encoding="utf-8")
    section = _extract_section(content, "Platzhalter-Escape")

    log = SyncLog()
    rendered = substitute(section, {}, "test:architecture.md", log)

    assert "{{%" not in rendered, (
        "Rendered Platzhalter-Escape section must not contain a raw '{{%' "
        "sequence -- its presence would mean an unescaped self-referential "
        "token survived (or was reintroduced) into the source."
    )
    # The old, wrong claim was exactly this literal sentence shape: a bare
    # '{{VAR}}' presented directly as *the* escape token via an arrow.
    old_wrong_claim = re.compile(r"\{\{VAR\}\}\s*.*rendert als\s*.*\{\{VAR\}\}")
    assert not old_wrong_claim.search(rendered), (
        "Rendered section must not read as the original broken claim "
        "('{{VAR}} -> rendert als {{VAR}}') -- that described the escape "
        "token as identical to an unescaped placeholder, which is wrong."
    )
