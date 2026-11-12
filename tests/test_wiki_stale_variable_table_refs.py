from pathlib import Path

WIKI = Path(__file__).resolve().parent.parent / "knowledge" / "wiki"


def test_no_stale_variable_table_reference():
    for p in WIKI.rglob("*.md"):
        assert "Variablen-Tabelle" not in p.read_text(encoding="utf-8"), str(p)


def test_no_removed_inject_dod_reference():
    page = WIKI / "concepts" / "core-principle-pal-variables.md"
    assert "_inject_dod" not in page.read_text(encoding="utf-8")
