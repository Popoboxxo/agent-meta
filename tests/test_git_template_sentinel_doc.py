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
