"""commit.trailers placeholders are known built-ins (no placeholders.unknown)."""
from __future__ import annotations

from pathlib import Path

from scripts.lib.consistency.placeholders import check_placeholders

ROOT = Path(__file__).resolve().parent.parent


def test_commit_trailers_placeholders_known():
    text = "{{#if COMMIT_TRAILERS_SET}}\n{{COMMIT_TRAILERS}}\n{{/if}}\n{{COMMIT_TRAILERS_SET}}\n"
    findings = check_placeholders(ROOT / "agents/1-generic/git.md", text, ROOT)
    assert [f for f in findings if f.check == "placeholders.unknown"] == []
