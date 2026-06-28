from pathlib import Path


def test_orchestrator_has_singleton_section():
    content = Path("agents/1-generic/orchestrator.md").read_text(encoding="utf-8")
    assert "## Singleton-Regel (Orchestrator)" in content
    assert "Self-Spawn = HARD REJECT" in content
    assert "orchestrator-iteration" in content
    assert "se-orchestrator" in content


def test_singleton_section_at_end():
    """Singleton-Block muss am Ende der Datei stehen (Recency-Bias)."""
    content = Path("agents/1-generic/orchestrator.md").read_text(encoding="utf-8")
    lines = content.splitlines()
    # Singleton-Block sollte in den letzten 30 Zeilen sein
    last_30 = "\n".join(lines[-30:])
    assert "## Singleton-Regel (Orchestrator)" in last_30
