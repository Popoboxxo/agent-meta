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

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = _REPO_ROOT / "templates" / "configs" / "README-template.md"


def _template_text() -> str:
    return _TEMPLATE.read_text(encoding="utf-8")


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
    assert "applies ONLY to the substituted version" in content
    assert "a literal `-` becomes `--`" in content
    assert "must NOT be escaped again" in content
    assert "Raw 0.101.0-beta.6 -> escaped" in content
    assert "0.101.0--beta.6" in content
