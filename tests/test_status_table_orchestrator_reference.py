"""orchestrator.md §7 (BARRIER protocol) must reference the mandatory
status-table block (issue #678 / #682 §5)."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ORCHESTRATOR = _REPO_ROOT / "agents" / "1-generic" / "orchestrator.md"


def test_barrier_section_references_status_table_block():
    content = _ORCHESTRATOR.read_text(encoding="utf-8")
    barrier_start = content.index("## 7. BARRIER protocol")
    barrier_end = content.index("## 8. Reflection loop")
    barrier_section = content[barrier_start:barrier_end]
    assert "{{STATUS_TABLE_BLOCK}}" in barrier_section
