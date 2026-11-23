"""Static pins for the conventions-overrides admin UI (#1204)."""

import re
from pathlib import Path

HTML = (Path(__file__).resolve().parent.parent / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")

# Consumers in the read-only render/config path (conventions.py / config.py).
KNOWN_CONSUMERS = {
    "language": "ISSUE_LANGUAGE",
    "title_format": "GIT_ISSUE_NAMING_BLOCK",
    "types": "GIT_ISSUE_NAMING_BLOCK",
    "labels.namespace": "GIT_ISSUE_NAMING_BLOCK",
    "closing_keywords": "GIT_ISSUE_NAMING_BLOCK",
}
INERT_LABELS = {"title_format", "types", "labels.namespace", "closing_keywords"}


def _conventions_overrides_view():
    start = HTML.index("async function viewProjectConventionsOverrides()")
    end = HTML.index("Views — Project Knowledge Engine")
    return HTML[start:end]


def _preset_editor_issues():
    start = HTML.index("// issues domain")
    end = HTML.index("panel.appendChild(issSec)", start) + len("panel.appendChild(issSec)")
    return HTML[start:end]


def _issue_rows(view):
    start = view.index("issues: [")
    end = view.index("];", start) + 2
    block = view[start:end]
    rows = [
        line.strip()
        for line in block.splitlines()
        if line.strip().startswith("[[\"")
    ]
    return [row.rstrip(",") for row in rows]


def _label_of(row):
    match = re.search(r'\],\s*"([^"]+)",\s*"(?:scalar|list)"', row)
    assert match is not None, f"cannot parse field row: {row}"
    return match.group(1)


def _is_covered(row):
    return _label_of(row) in KNOWN_CONSUMERS or "docOnly: true" in row


def test_language_is_overridable_in_domain_fields():
    rows = _issue_rows(_conventions_overrides_view())
    assert '[["language"], "language", "scalar"]' in rows
    assert _label_of('[["language"], "language", "scalar"],') == "language"


def test_language_is_editable_in_preset_editor():
    assert 'scalarField("language", issues, "language")' in _preset_editor_issues()


def test_inert_issue_fields_are_marked_documentation_only():
    rows = _issue_rows(_conventions_overrides_view())
    by_label = {_label_of(row): row for row in rows}
    assert INERT_LABELS.issubset(by_label), by_label
    for label in INERT_LABELS:
        assert "docOnly: true" in by_label[label], f"{label} is not marked docOnly"
        assert ", true]" in by_label[label], f"{label} lacks the functional docOnly flag"
    assert "docOnly" not in by_label["language"], "language must not be docOnly"
    assert ", true]" not in by_label["language"]


def test_documentation_badge_uses_muted_and_never_ok():
    view = _conventions_overrides_view()
    assert "documentation only" in view
    assert 'docOnly ? "muted"' in view
    assert "const badgeClass" in view
    assert 'badge ${isOverridden ? "warn" : "ok"}' not in view


def test_intro_names_git_md_help_text_and_effective_language():
    view = _conventions_overrides_view()
    start = view.index('wrap.appendChild(el("p", { class: "muted" }')
    end = view.index("]", start)
    intro = view[start:end]
    assert "git.md" in intro
    assert "help text" in intro.lower()
    assert "language" in intro
    assert "effective" in intro.lower()
    assert "#1188" not in intro


def test_every_offered_issue_field_has_consumer_or_documentation_marker():
    rows = _issue_rows(_conventions_overrides_view())
    assert rows, "no issue fields found in DOMAIN_FIELDS.issues"
    uncovered = [row for row in rows if not _is_covered(row)]
    assert not uncovered, f"fields without consumer or docOnly: {uncovered}"
    # A newly added field with neither consumer nor docOnly must fail the guard.
    assert not _is_covered('[["brand_new"], "brand_new", "scalar"],')


def test_muted_badge_class_is_defined():
    assert ".badge.muted {" in HTML


def test_save_path_is_unchanged():
    view = _conventions_overrides_view()
    assert 'await saveProjectSection("conventions-preset", activePreset, null);' in view
    assert 'await saveProjectSection("conventions", overrides, status);' in view
