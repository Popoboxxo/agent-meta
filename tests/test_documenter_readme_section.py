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


def test_section_5_documents_agent_meta_type_and_version_variable():
    """§5 must name the new badge type and its value source
    (docs/concepts/agent-meta-version-badge.md §4)."""
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "agent-meta" in content
    assert "{{AGENT_META_VERSION}}" in content


def test_section_5_documents_agent_meta_opt_in_rule():
    """The badge is rendered ONLY when `agent-meta` is listed in README_BADGES
    -- no implicit/default-on rendering (§4/§5.3)."""
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "opt-in" in content.lower()
    assert "listed in `{{README_BADGES}}`" in content


def test_section_5_documents_agent_meta_unknown_fallback():
    """Missing/empty AGENT_META_VERSION renders the literal `unknown` value
    instead of silently omitting the badge (D5/Q6)."""
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "`unknown`" in content
    assert "missing or empty" in content


def test_section_5_documents_agent_meta_shields_escaping_incl_prerelease():
    """Shields.io `-` -> `--` escaping is mandatory, including the pre-release
    case 0.101.0-beta.6 -> 0.101.0--beta.6 (M1, §4)."""
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "agent--meta" in content
    assert "v0.101.0-beta.6" in content
    assert "v0.101.0--beta.6" in content


def test_section_5_documents_agent_meta_repo_guard():
    """The link target uses AGENT_META_REPO only when it is non-empty and
    contains a `/` -- otherwise the badge is rendered without a link (m2, §4)."""
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "{{AGENT_META_REPO}}" in content
    assert "non-empty" in content
    assert "contains a `/`" in content


def test_section_5_documents_agent_meta_release_tag_link():
    """The link points at the matching release tag
    https://github.com/<repo>/releases/tag/v<version> (D1/Q2, §2.3)."""
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "releases/tag/v<version>" in content


def test_section_5_names_documenter_as_only_badge_writer():
    """Ownership B1: the documenter is the ONLY writer of the badges row, so
    no other agent may generate or patch it (§4/§5.3)."""
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "ONLY writer" in content
    assert "badges row" in content
