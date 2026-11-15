from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = (ROOT / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")
REF = (ROOT / "docs" / "api" / "admin-ui-reference.md").read_text(encoding="utf-8")


def _view():
    start = HTML.index("async function viewProjectCommit()")
    end = HTML.index("/* --------------------------- Release Checklist")
    return HTML[start:end]


def test_route_sidebar_and_help_wired():
    assert 'router.register("/project/commit"' in HTML and "viewProjectCommit);" in HTML
    assert 'route: "/project/commit"' in HTML
    assert '"project/commit": "project_instance-commit"' in HTML
    assert "<!-- help-id: project_instance-commit -->" in REF


def test_view_saves_commit_section_via_textarea():
    view = _view()
    assert 'el("textarea"' in view and 'saveProjectSection("commit"' in view
    assert "out.trailers = lines" in view and "clone(cm)" in view


def test_view_is_accessible():
    view = _view()
    assert "a11yField(" in view and 'role: "status"' in view and '"aria-live": "polite"' in view
