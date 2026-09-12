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
    """Missing/empty AGENT_META_VERSION -- or the non-empty sentinel
    `"unknown"`/`vunknown` returned by read_version() -- renders the literal
    label `agent-meta` + message `unknown` with the exact image URL and no `v`
    prefix, instead of silently omitting the badge (D5/Q6, F1/F10)."""
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "`unknown`" in content
    assert '"unknown"' in content
    assert "vunknown" in content
    assert "agent--meta-unknown-blue.svg" in content
    assert "label `agent-meta`" in content
    assert "message `unknown`" in content


def test_section_5_documents_agent_meta_shields_escaping_incl_prerelease():
    """Shields.io `-` -> `--` escaping is mandatory but applies ONLY to the
    badge image segment (blank version value, no `v`) FIRST; only then is a
    single literal `v` prepended:
    0.101.0-beta.6 -> 0.101.0--beta.6 -> v0.101.0--beta.6 (M1/F4)."""
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "agent--meta" in content
    assert "agent--meta-v<escaped-version>-blue.svg" in content
    assert "0.101.0-beta.6" in content
    assert "0.101.0--beta.6" in content
    assert "v0.101.0--beta.6" in content
    assert "blank version value" in content
    assert "no `vv`" in content
    assert "badge image segment ONLY" in content


def test_section_5_documents_agent_meta_sync_embedded_value():
    """The value contract is the sync-embedded `{{AGENT_META_VERSION}}`,
    refreshed by the preceding re-sync (M2) -- not a separate live read (F3)."""
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "embedded at sync time" in content
    assert "refreshed by the preceding re-sync (M2)" in content
    assert "never a separate live read" in content


def test_section_5_never_double_escapes_label():
    """The label `agent--meta` must be escaped exactly once: a double-escaped
    image URL would contain `badge/agent----meta` (M1/F4/F5)."""
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "must NOT be escaped a second time" in content
    assert "badge/agent----meta" not in content


def test_section_5_documents_agent_meta_repo_guard():
    """The link target uses AGENT_META_REPO only when it is non-empty and
    contains a `/` -- otherwise the badge is rendered without a link (m2, §4)."""
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "{{AGENT_META_REPO}}" in content
    assert "non-empty" in content
    assert "contains a `/`" in content


def test_section_5_documents_agent_meta_release_tag_link_raw_version():
    """The link points at the matching release tag with the RAW version value
    https://github.com/<repo>/releases/tag/v<version> -- Shields escaping is
    image-only, so the escaped form must NOT appear in the link (D1/Q2, §2.3)."""
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "releases/tag/v<version>" in content
    assert "releases/tag/v<escaped-version>" not in content
    assert "the **raw** version value, WITHOUT Shields escaping" in content


def test_section_5_documents_releases_page_fallback():
    """The unknown case falls back to the always-valid releases page and never
    fabricates a `vunknown` tag link (F2, §9/Q2)."""
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "always-valid releases page" in content
    assert "https://github.com/{{AGENT_META_REPO}}/releases`" in content
    assert "never fabricate a `vunknown` tag link" in content


def test_section_5_names_documenter_as_only_badge_writer():
    """Ownership B1: the documenter is the ONLY writer of the badges row, so
    no other agent may generate or patch it (§4/§5.3)."""
    content = _DOCUMENTER.read_text(encoding="utf-8")
    assert "ONLY writer" in content
    assert "badges row" in content
