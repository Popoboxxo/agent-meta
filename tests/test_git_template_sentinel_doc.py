"""git.md sentinel doc: no outdated provider claim, no-bypass statement present."""
from pathlib import Path

TEXT = (Path(__file__).resolve().parent.parent / "agents/1-generic/git.md").read_text(encoding="utf-8")


def test_no_outdated_provider_claim():
    assert "no provider forwards" not in TEXT


def test_sentinel_no_bypass_statement():
    assert "The sentinel only declares the role; it bypasses no protection" in TEXT


def test_mutation_gate_statement_mentions_allowlist_exemption():
    assert "blocks git mutations independent of strict mode" in TEXT
    assert "only the narrow auto-commit allowlist (add/commit, declared via its own sentinel) is exempt" in TEXT
    assert "always blocks them" not in TEXT


def test_rendered_claude_has_gh_only_exception():
    """AC-3: the exception sentence appears in the RENDERED Claude git.md only.

    The template source carries just the placeholder; the literal sentence is
    injected by the hook-agent-id provider variable (Task 1).
    """
    from tests.test_git_sentinel_gh_scope import _pc, _render_git

    rendered = _render_git(_pc("hook-agent-id"))
    assert "for Bash calls that run only `gh`" in rendered
    assert "do NOT add the sentinel line" in rendered
    # Source holds only the placeholder, never the literal exception sentence.
    assert "{{GIT_SENTINEL_SCOPE_BLOCK}}" in TEXT
    assert "do NOT add the sentinel line" not in TEXT


def test_payload_attribution_gate_is_in_the_template_source():
    """IC-7: the source carries the gate; only variant C drops the sentinel."""
    assert "{{#if GIT_PAYLOAD_ATTRIBUTION}}" in TEXT
    assert "{{else}}" in TEXT
    assert "{{/if}}" in TEXT


def test_variant_c_render_drops_sentinel_but_keeps_guard_prose():
    from tests.test_git_sentinel_gh_scope import _pc, _render_git

    rendered = _render_git(_pc("hook-agent-id", "hook-role-field"))
    assert "#agent-meta:agent=git" not in rendered
    assert "Destructive-operation, branch and" in rendered
    # The #1329 evidence line must survive every variant.
    assert "**Measured evidence only:**" in rendered
