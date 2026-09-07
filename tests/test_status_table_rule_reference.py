"""use-orchestrator.md must reference the mandatory status-table block
inside its main-chat-mode branch (issue #678 / #682 §5)."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RULE = _REPO_ROOT / "rules" / "1-generic" / "use-orchestrator.md"


def test_status_table_block_referenced_inside_main_chat_mode():
    content = _RULE.read_text(encoding="utf-8")
    main_chat_start = content.index("{{#if ORCH_MODE_MAIN_CHAT}}")
    main_chat_end = content.index("{{/if}}", main_chat_start)
    main_chat_section = content[main_chat_start:main_chat_end]
    assert "{{STATUS_TABLE_BLOCK}}" in main_chat_section
