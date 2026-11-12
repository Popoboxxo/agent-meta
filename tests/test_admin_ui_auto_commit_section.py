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


def test_triggers_use_checkbox_group_not_tag_editor():
    view = _auto_commit_view()
    assert 'tagEditorField(\n    "Triggers"' not in view and 'tagEditorField("Triggers"' not in view
    assert "checkboxGroupField(" in view
    assert "function checkboxGroupField(" in HTML


def test_threshold_is_conditional_on_file_count_trigger():
    view = _auto_commit_view()
    assert "file-count-threshold" in view and "thresholdField.style.display" in view
