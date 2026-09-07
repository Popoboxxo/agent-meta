"""documenter.md §5 must reference the README standard placeholders and
template (issue #682 §3) -- regression guard against silently dropping the
additive/managed-block instruction on a future edit."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOCUMENTER = _REPO_ROOT / "agents" / "1-generic" / "documenter.md"


def test_section_5_references_readme_variables():
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "{{README_BADGES}}" in content
    assert "{{README_WARNINGS_ENABLED}}" in content
    assert "{{README_SECTIONS}}" in content


def test_section_5_references_template_and_managed_block_principle():
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "README-template.md" in content
    assert "additiv" in content.lower() or "additive" in content.lower()


def test_section_5_documents_license_and_ci_runtime_checks():
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "LICENSE" in content
    assert "CI" in content
