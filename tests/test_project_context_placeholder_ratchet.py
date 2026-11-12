"""Ratchet against duplicate {{PROJECT_CONTEXT}} placeholders in generic templates (#1197).

Per file: one "**Project context:**" block line (counted) plus prose references.
Known duplicates (block / prose): ui-ux-designer.md 72 / 77,105;
bug-feature-analyzer.md 76 / 40; knowledge-curator.md 22 / 55;
knowledge-migrator.md 26 / 38. The real fix is #1187 T9.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# Shrink-only ratchet. #1187 T9 wraps prose sites in {{#if}} and keeps the token,
# so counts stay 3/2/2/2; lower an entry only when a token is removed.
_KNOWN_DUPLICATES = {
    "ui-ux-designer.md": 3,
    "bug-feature-analyzer.md": 2,
    "knowledge-curator.md": 2,
    "knowledge-migrator.md": 2,
}


def test_project_context_placeholder_count_ratchet():
    for f in sorted((REPO_ROOT / "agents" / "1-generic").glob("*.md")):
        n = f.read_text(encoding="utf-8").count("{{PROJECT_CONTEXT}}")
        limit = _KNOWN_DUPLICATES.get(f.name, 1)
        assert n <= limit, f"{f.name}: {n} > {limit} (new duplicate placeholder)"
        assert limit == 1 or n == limit, f"{f.name}: lower the ratchet to {n}"
