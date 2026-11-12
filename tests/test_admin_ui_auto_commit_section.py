from pathlib import Path

HTML = (Path(__file__).resolve().parent.parent / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")


def _auto_commit_view():
    start = HTML.index("async function viewProjectAutoCommit()")
    end = HTML.index("/* --------------------------- Release Checklist")
    return HTML[start:end]


def test_save_clones_loaded_object_instead_of_rebuilding():
    view = _auto_commit_view()
    assert "const out = { mode }" not in view
    assert "const out = clone(ac)" in view


def test_save_drops_mode_specific_fields_outside_auto():
    view = _auto_commit_view()
    assert "delete out.triggers" in view
    assert "delete out.file_count_threshold" in view
