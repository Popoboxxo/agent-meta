"""Progress-file behavior (issue #682 §6) must be documented where a
developer would look for checkpoint/progress semantics."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_checkpointing_snippet_documents_progress_file():
    content = (_REPO_ROOT / "snippets" / "orchestrator" / "checkpointing.md").read_text(encoding="utf-8")
    assert ".claude/progress/current.md" in content


def test_orchestrator_section_9_documents_progress_file():
    content = (_REPO_ROOT / "agents" / "1-generic" / "orchestrator.md").read_text(encoding="utf-8")
    section_9_start = content.index("## 9. Context guard & checkpointing")
    section_10_start = content.index("## 10. Delegation failure recovery")
    section_9 = content[section_9_start:section_10_start]
    assert ".claude/progress/current.md" in section_9
