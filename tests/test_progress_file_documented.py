"""Progress-file behavior (issue #682 §6, live-progress-channel design
2026-09-10) must be documented where a developer would look for
checkpoint/progress semantics."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_checkpointing_snippet_documents_progress_file():
    content = (_REPO_ROOT / "snippets" / "orchestrator" / "checkpointing.md").read_text(encoding="utf-8")
    assert ".meta-viz/progress/current.md" in content


def test_orchestrator_section_9_documents_progress_file():
    content = (_REPO_ROOT / "agents" / "1-generic" / "orchestrator.md").read_text(encoding="utf-8")
    section_9_start = content.index("## 9.")
    section_10_start = content.index("## 10.")
    section_9 = content[section_9_start:section_10_start]
    # Issue #743: §9 delegates the checkpointing/live-progress documentation to
    # the CHECKPOINTING_BLOCK snippet, so `orchestrator.checkpointing: false`
    # can actually suppress it. The snippet is the source of truth for the
    # documented behavior; §9 must still reference it.
    assert "{{CHECKPOINTING_BLOCK}}" in section_9
    snippet = (_REPO_ROOT / "snippets" / "orchestrator" / "checkpointing.md").read_text(encoding="utf-8")
    assert ".meta-viz/progress/current.md" in snippet
    assert "Tier-A" in snippet or "Tier A" in snippet
    assert "Tier-B" in snippet or "Tier B" in snippet


def test_orchestrator_section_7_documents_tier_a_chat_push():
    content = (_REPO_ROOT / "agents" / "1-generic" / "orchestrator.md").read_text(encoding="utf-8")
    section_7_start = content.index("## 7. BARRIER protocol")
    section_8_start = content.index("## 8. Reflection loop")
    section_7 = content[section_7_start:section_8_start]
    assert "PROGRESS_CHAT_PUSH_ENABLED" in section_7
    assert 'SendMessage(to:"main"' in section_7
