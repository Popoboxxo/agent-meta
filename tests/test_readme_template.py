"""Static contract tests for the `agent-meta` badge documentation in
`templates/configs/README-template.md`.

The template is a reference/documentation file consumed by the `documenter`
LLM agent -- it is never sync-processed and there is no renderer code. Its
badge rules (opt-in, shielding/escaping, repo guard) are therefore asserted
statically here against the template text itself; there is deliberately no
helper re-implementing the rule (a test that mirrors the logic it is supposed
to guard can stay green even when the artifact regresses).

See docs/concepts/agent-meta-version-badge.md §2.2/§4/§7.
"""

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = _REPO_ROOT / "templates" / "configs" / "README-template.md"
_PROJECT_YAML_EXAMPLE = _REPO_ROOT / "templates" / "configs" / "project.yaml.example"


def _template_text() -> str:
    return _TEMPLATE.read_text(encoding="utf-8")


def _strip_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def test_template_documents_agent_meta_as_opt_in():
    content = _template_text()
    assert "agent-meta" in content
    assert "opt-in" in content.lower()
    assert "readme.badges" in content


def test_template_contains_escaped_prerelease_example():
    """The comment must show the correctly escaped pre-release example, both
    the raw and the escaped form, plus the escaped label."""
    content = _template_text()
    assert "agent--meta" in content
    assert "0.101.0-beta.6" in content
    assert "0.101.0--beta.6" in content


def test_template_placeholder_line_uses_release_tag_link():
    content = _template_text()
    assert (
        "https://github.com/{{AGENT_META_REPO}}/releases/tag/v{{AGENT_META_VERSION}}"
        in content
    )


def test_template_documents_repo_guard_for_link_target():
    content = _template_text()
    assert "{{AGENT_META_REPO}}" in content
    assert "non-empty and contains a `/`" in content


def test_template_documents_shields_escaping_rule():
    """The documented shields.io escaping contract (raw -> escaped) must be
    present verbatim in the template artifact.

    This asserts the production artifact (the doc the `documenter` reads), not
    a helper that re-implements the replacement -- re-implementing the rule
    would be a tautology that stays green even if the template documented
    nothing. See docs/concepts/agent-meta-version-badge.md §2.2.
    """
    content = _template_text()
    assert "escaping is mandatory" in content
    assert "applies ONLY to the badge IMAGE segment" in content
    assert "The link target is NEVER escaped" in content
    assert "a literal `-` becomes `--`" in content
    assert "must NOT be escaped again" in content
    assert "Raw 0.101.0-beta.6 -> escaped" in content
    assert "0.101.0--beta.6" in content


def test_template_documents_unknown_label_message_and_image():
    """The unknown case is fully specified: label `agent-meta`, message
    `unknown`, exact image URL, no `v` prefix, sentinel included
    (D5/Q6, F1/F10)."""
    content = _template_text()
    assert "label `agent-meta`, message `unknown`" in content
    assert "agent--meta-unknown-blue.svg" in content
    assert 'sentinel `"unknown"`/`vunknown`' in content


def test_template_documents_releases_fallback():
    """Unknown values fall back to the always-valid releases page; a
    `vunknown` tag link must never be fabricated (F2, §9/Q2)."""
    content = _template_text()
    assert "always-valid link fallback" in content
    assert "https://github.com/{{AGENT_META_REPO}}/releases" in content
    assert "releases/tag/vunknown" in content


def test_template_never_double_escapes_label():
    """`agent--meta` is escaped exactly once: no `badge/agent----meta` image
    URL may appear (M1/F4/F5)."""
    content = _template_text()
    assert "must NOT be escaped again" in content
    assert "badge/agent----meta" not in content


def test_template_escaping_is_image_only_link_uses_raw_placeholder():
    """Escaping is image-only: the image segment documents the placeholder
    `<escaped-version>`, while the tag link documents the RAW `<version>`
    placeholder (F9, B1). An escaped `<escaped-version>` must never appear in
    the link target -- the real pre-release tag is `v0.101.0-beta.6`, so an
    escaped link would 404."""
    content = _template_text()
    assert "agent--meta-v<escaped-version>-blue.svg" in content
    assert "releases/tag/v<version>" in content
    assert "releases/tag/v<escaped-version>" not in content


def test_template_default_badges_do_not_include_agent_meta():
    """`agent-meta` is opt-in only: the active (non-comment) badge lines of the
    template must not contain it (D2/Q1, F5)."""
    active = _strip_html_comments(_template_text())
    badge_lines = [ln for ln in active.splitlines() if ln.strip().startswith("[![")]
    assert badge_lines, "template must contain at least one active badge line"
    assert all("agent-meta" not in ln for ln in badge_lines)


def test_project_yaml_example_default_badges_do_not_include_agent_meta():
    """The shipped config example keeps `agent-meta` opt-in: the documented
    `badges:` default never lists `agent-meta`. Asserted on the committed
    example (not the local `.meta-config/project.yaml`) so the test works even
    when the self-hosting config is absent (F5)."""
    example = _PROJECT_YAML_EXAMPLE.read_text(encoding="utf-8")
    badge_lines = [ln for ln in example.splitlines() if "badges:" in ln]
    assert badge_lines, "project.yaml.example must document readme.badges"
    assert all("agent-meta" not in ln for ln in badge_lines)
    assert any("[version, stack, license]" in ln for ln in badge_lines)
