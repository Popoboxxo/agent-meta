"""STATUS_TABLE_BLOCK must be loaded from snippets/orchestrator/status-table.md
and be non-empty in every render (issue #678 / #682 §5) -- it is a mandatory
rule, never gated behind a {{#if}} feature flag."""

from pathlib import Path

from scripts.lib.config import build_variables

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_status_table_block_loaded_and_non_empty():
    variables, _ = build_variables({}, _REPO_ROOT)
    assert "STATUS_TABLE_BLOCK" in variables
    assert "Status-Tabelle" in variables["STATUS_TABLE_BLOCK"]
    assert "Agent | Task | Status" in variables["STATUS_TABLE_BLOCK"]
