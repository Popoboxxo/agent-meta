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


# ---------------------------------------------------------------------------
# Capability flags (SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30, §2.2)
# ---------------------------------------------------------------------------
# AC-15: every registered provider declares `skills`, `artifact-validation`
#        and the `mcp-remote-transport` discriminator in
#        config/provider-capabilities.yaml.
# AC-24: `artifact-validation: false` is valid only with a non-empty
#        `artifact-validation-reason`.
# AC-25: `skills: true` must mirror the ai-providers.yaml machine flags — the
#        `capabilities` list contains `skills` and `skills_dir` is non-null.

_MCP_REMOTE_TRANSPORTS = ("url", "transport", "type")


def _capability_entries() -> dict:
    data = _load_yaml(_REPO_ROOT / "config" / "provider-capabilities.yaml") or {}
    return data.get("capabilities") or {}


def _ai_provider_entries() -> dict:
    data = _load_yaml(_REPO_ROOT / "config" / "ai-providers.yaml") or {}
    return data.get("providers") or {}


def _capability_flag_findings(
    provider: str, pal_entry: dict, ai_entry: dict
) -> list:
    """Pure validator for one provider's §2.2 capability contract.

    Returns human-readable findings; an empty list means the provider's flags
    are consistent. Kept pure so the AC-24 reason gate stays covered even
    though no live provider currently opts out of artifact validation."""
    findings: list = []
    pal_entry = pal_entry or {}
    ai_entry = ai_entry or {}

    for flag in ("skills", "artifact-validation"):
        if flag not in pal_entry:
            findings.append(f"{provider}: missing '{flag}' (AC-15)")
        elif not isinstance(pal_entry[flag], bool):
            findings.append(
                f"{provider}: '{flag}' must be a bool, got "
                f"{type(pal_entry[flag]).__name__} (AC-15)"
            )

    transport = pal_entry.get("mcp-remote-transport")
    if transport not in _MCP_REMOTE_TRANSPORTS:
        findings.append(
            f"{provider}: 'mcp-remote-transport' must be one of "
            f"{_MCP_REMOTE_TRANSPORTS}, got {transport!r} (§2.2)"
        )

    # AC-24 reason gate (fail-closed: `false` is only valid with a reason).
    if pal_entry.get("artifact-validation") is False:
        reason = pal_entry.get("artifact-validation-reason")
        if not (isinstance(reason, str) and reason.strip()):
            findings.append(
                f"{provider}: 'artifact-validation: false' requires a "
                "non-empty 'artifact-validation-reason' (AC-24)"
            )

    # AC-25 coupling to the ai-providers.yaml machine flags.
    if pal_entry.get("skills") is True:
        capabilities = ai_entry.get("capabilities") or []
        if "skills" not in capabilities:
            findings.append(
                f"{provider}: 'skills: true' but 'skills' is absent from the "
                "ai-providers.yaml capabilities list (AC-25)"
            )
        if not ai_entry.get("skills_dir"):
            findings.append(
                f"{provider}: 'skills: true' but ai-providers.yaml has no "
                "'skills_dir' (AC-25)"
            )
    return findings


@pytest.mark.parametrize("provider", _registered_providers())
def test_provider_capability_flags_are_consistent(provider):
    """[AC-15/AC-24/AC-25] Every registered provider declares the §2.2 flags
    and keeps `skills` coupled to the ai-providers machine flags."""
    findings = _capability_flag_findings(
        provider,
        _capability_entries().get(provider),
        _ai_provider_entries().get(provider),
    )
    assert not findings, "\n".join(findings)


def test_artifact_validation_false_without_reason_is_rejected():
    """[AC-24] Synthetic gate: `false` without a reason must fail, so the
    invariant cannot pass vacuously while no provider opts out."""
    findings = _capability_flag_findings(
        "Synthetic",
        {
            "skills": False,
            "artifact-validation": False,
            "mcp-remote-transport": "url",
        },
        {},
    )
    assert any("artifact-validation-reason" in f for f in findings), findings


def test_artifact_validation_false_with_blank_reason_is_rejected():
    """[AC-24] A whitespace-only reason does not legitimise the opt-out."""
    findings = _capability_flag_findings(
        "Synthetic",
        {
            "skills": False,
            "artifact-validation": False,
            "artifact-validation-reason": "   ",
            "mcp-remote-transport": "url",
        },
        {},
    )
    assert any("artifact-validation-reason" in f for f in findings), findings


def test_artifact_validation_false_with_reason_is_accepted():
    """[AC-24] A non-empty reason legitimises the opt-out."""
    findings = _capability_flag_findings(
        "Synthetic",
        {
            "skills": False,
            "artifact-validation": False,
            "artifact-validation-reason": "provider emits non-validatable TOML",
            "mcp-remote-transport": "url",
        },
        {},
    )
    assert findings == []


def test_skills_true_without_ai_provider_coupling_is_rejected():
    """[AC-25] `skills: true` without the ai-providers `skills` capability and
    a `skills_dir` is rejected."""
    findings = _capability_flag_findings(
        "Synthetic",
        {"skills": True, "artifact-validation": True, "mcp-remote-transport": "url"},
        {"capabilities": ["agents"], "skills_dir": None},
    )
    assert any("capabilities list" in f for f in findings), findings
    assert any("skills_dir" in f for f in findings), findings


def test_skills_true_with_ai_provider_coupling_is_accepted():
    """[AC-25] The coupling is satisfied by both machine flags together."""
    findings = _capability_flag_findings(
        "Synthetic",
        {"skills": True, "artifact-validation": True, "mcp-remote-transport": "url"},
        {"capabilities": ["agents", "skills"], "skills_dir": ".synthetic/skills"},
    )
    assert findings == []
