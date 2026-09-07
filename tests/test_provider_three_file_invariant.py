"""Regression guard (issue #492, Suggestion 1): every provider registered in
config/ai-providers.yaml ("providers" section) MUST also be present in ALL
THREE PAL (Provider Abstraction Layer) config files:

    config/provider-capabilities.yaml  -> "capabilities" section
    config/provider-bootstrap.yaml     -> "bootstrap" section
    config/delegation-syntax.yaml      -> "delegation_syntax" section

Consumers read these with a silent empty-dict fallback:
  - scripts/lib/delegation_syntax.py:
      .get("delegation_syntax", {}).get(provider, {})
      .get("capabilities", {}).get(provider, {})
  - scripts/lib/bootstrap.py:
      .get("bootstrap", {}).get(provider, {})

A provider missing from one file is therefore a SILENT DOWNGRADE, not an
error: DelegationSyntaxEngine.apply() strips ALL PAL_* delegation
placeholders from the generated agents (delegate/fanout/fallback/handoff
vanish) and bootstrap_required/subagent_dispatch/file_based_agents silently
default to false. Exactly this happened to Mammouth (fixed in
fix/provider-best-practices). Previously no gate enforced the coupling —
this test is that gate, parametrized over the live registry so a newly
onboarded provider is automatically covered.

Run: python -m pytest tests/test_provider_three_file_invariant.py -v
"""

from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent

# (relative config path, section key) — mirrors the exact lookup the PAL
# consumers perform (delegation_syntax.py / bootstrap.py).
_PAL_FILES = (
    ("config/provider-capabilities.yaml", "capabilities"),
    ("config/provider-bootstrap.yaml", "bootstrap"),
    ("config/delegation-syntax.yaml", "delegation_syntax"),
)


def _load_yaml(rel_path: Path) -> dict:
    with rel_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _registered_providers() -> list:
    """Provider keys from config/ai-providers.yaml, sorted for stable IDs."""
    data = _load_yaml(_REPO_ROOT / "config" / "ai-providers.yaml") or {}
    return sorted((data.get("providers") or {}).keys())


def test_issue_492_provider_registry_is_nonempty_and_contains_claude():
    """[issue-492] Vacuous-pass guard: the sweep below parametrizes over the
    provider registry — if the section were renamed or emptied, pytest would
    collect zero cases and the three-file invariant would hold vacuously.
    Pin the registry contract instead."""
    providers = _registered_providers()
    assert providers, (
        "config/ai-providers.yaml has no 'providers' entries — the "
        "three-file sweep would collect zero cases (vacuous pass)"
    )
    assert "Claude" in providers, (
        "Claude is the reference provider every PAL config has always "
        "contained — its absence signals a registry rename"
    )


@pytest.mark.parametrize("provider", _registered_providers())
def test_issue_492_provider_registered_in_all_three_pal_configs(provider):
    """[issue-492] The provider must appear under the SAME key in every PAL
    config section its consumers read with .get(provider, {}) — a missing
    entry means generated agents silently lose delegation (PAL_* placeholders
    stripped) and capability defaults flip to false, with no warning."""
    for rel_path, section in _PAL_FILES:
        data = _load_yaml(_REPO_ROOT / rel_path) or {}
        registry = data.get(section)
        assert isinstance(registry, dict), (
            f"{rel_path}: section '{section}' missing or not a mapping — "
            "consumers would fall back to {} for every provider"
        )
        assert provider in registry, (
            f"'{provider}' is registered in config/ai-providers.yaml but "
            f"missing from {rel_path} section '{section}' — silent downgrade "
            "(PAL_* delegation placeholders stripped / capability defaults "
            "false). Add the provider to all three PAL files; Copilot is the "
            "conservative reference pattern."
        )
