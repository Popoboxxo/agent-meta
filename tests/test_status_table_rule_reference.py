"""use-orchestrator.md must reference the mandatory status-table block
inside its main-chat-mode branch (issue #678 / #682 §5)."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RULE = _REPO_ROOT / "rules" / "1-generic" / "use-orchestrator.md"


def test_status_table_block_referenced_inside_main_chat_mode():
    content = _RULE.read_text(encoding="utf-8")
    main_chat_start = content.index("{{#if ORCH_MODE_MAIN_CHAT}}")
    # Walk to the matching {{/if}}, accounting for nested {{#if ...}} blocks
    # (e.g. ROUTING_DETAILS_ENABLED) added inside main-chat mode.
    depth = 0
    main_chat_end = None
    pos = main_chat_start + len("{{#if ORCH_MODE_MAIN_CHAT}}")
    while True:
        nxt_if = content.find("{{#if ", pos)
        nxt_end = content.find("{{/if}}", pos)
        if nxt_end == -1:
            raise AssertionError("unterminated ORCH_MODE_MAIN_CHAT block")
        if nxt_if != -1 and nxt_if < nxt_end:
            depth += 1
            pos = nxt_if + len("{{#if ")
        else:
            if depth == 0:
                main_chat_end = nxt_end
                break
            depth -= 1
            pos = nxt_end + len("{{/if}}")
    main_chat_section = content[main_chat_start:main_chat_end]
    assert "{{STATUS_TABLE_BLOCK}}" in main_chat_section
