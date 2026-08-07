"""Regression tests for dynamic tier preset resolution (REQ-MOD-01).

Tests use the real config files from the repo — no mocking.
All tests target the Claude provider for deterministic model IDs.
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.roles import resolve_model

# Root of the agent-meta repo (parent of tests/)
REPO_ROOT = Path(__file__).parent.parent

# Claude model-tier expectations from config/ai-providers.yaml
CLAUDE_MODEL_POWERFUL = "claude-opus-4-8"
CLAUDE_MODEL_FAST = "claude-haiku-4-5-20251001"
CLAUDE_MODEL_MAX = "claude-fable-5"
CLAUDE_MODEL_BALANCED = "claude-sonnet-5"

# Provider config is loaded by resolve_model from ai-providers.yaml.
# We must pass it to avoid hitting disk twice; load it once here.
from scripts.lib.providers import load_providers_config

_PROVIDER_CONFIG = load_providers_config(REPO_ROOT)


def _resolve(role: str, preset: str, extra: dict | None = None) -> str:
    """Helper: resolve model for a role with a given tier-preset."""
    project_config: dict = {"tier-preset": preset}
    if extra:
        project_config.update(extra)
    return resolve_model(
        role=role,
        project_config=project_config,
        agent_meta_root=REPO_ROOT,
        provider="Claude",
        provider_config=_PROVIDER_CONFIG,
    )


# ---------------------------------------------------------------------------
# C1 — Preset matrix is applied (not always returning the same model)
# ---------------------------------------------------------------------------

def test_cheap_vs_expensive_differ() -> None:
    """Cheap and Expensive as Hell presets must produce different models for developer."""
    cheap_model = _resolve("developer", "Cheap")
    expensive_model = _resolve("developer", "Expensive as Hell")
    # developer tier=powerful → Cheap maps powerful→fast, Expensive as Hell maps powerful→max
    assert cheap_model != expensive_model, (
        f"Expected Cheap ({cheap_model!r}) != Expensive as Hell ({expensive_model!r})"
    )


# ---------------------------------------------------------------------------
# C1 — Normal preset is a 1:1 passthrough
# ---------------------------------------------------------------------------

def test_normal_is_passthrough() -> None:
    """Normal preset maps senior-developer (powerful) to the powerful model — no remapping."""
    model = _resolve("senior-developer", "Normal")
    assert model == CLAUDE_MODEL_POWERFUL, (
        f"Normal preset should pass through 'powerful' → {CLAUDE_MODEL_POWERFUL!r}, got {model!r}"
    )


# ---------------------------------------------------------------------------
# H2 — se-focus boolean upgrades SE roles, does not touch non-SE roles
# ---------------------------------------------------------------------------

def test_se_focus_upgrades_se_role() -> None:
    """se-focus: true upgrades an se-* role by 1 tier before preset mapping."""
    # se-requirements has model: balanced
    # With se-focus=true: balanced → powerful (upgraded by 1)
    # With Normal preset: powerful stays powerful
    model_with_focus = _resolve("se-requirements", "Normal", extra={"se-focus": True})
    model_without_focus = _resolve("se-requirements", "Normal")

    assert model_with_focus == CLAUDE_MODEL_POWERFUL, (
        f"SE-focused se-requirements should resolve to powerful model, got {model_with_focus!r}"
    )
    assert model_without_focus == CLAUDE_MODEL_BALANCED, (
        f"Non-SE-focused se-requirements should resolve to balanced model, got {model_without_focus!r}"
    )


def test_se_focus_does_not_upgrade_non_se_role() -> None:
    """se-focus: true must NOT affect non-se roles."""
    # developer has model: powerful
    # With se-focus=true + Normal preset: should still be powerful (no upgrade)
    model_with_focus = _resolve("senior-developer", "Normal", extra={"se-focus": True})
    model_without_focus = _resolve("senior-developer", "Normal")
    assert model_with_focus == model_without_focus, (
        f"se-focus must not change non-SE role: {model_with_focus!r} vs {model_without_focus!r}"
    )


# ---------------------------------------------------------------------------
# H2 — Backward compat: " (SE)" suffix in tier-preset value
# ---------------------------------------------------------------------------

def test_backward_compat_se_suffix() -> None:
    """tier-preset: 'Normal (SE)' behaves like Normal + se-focus: true."""
    # Via suffix
    model_suffix = _resolve("se-requirements", "Normal (SE)")
    # Via boolean flag
    model_flag = _resolve("se-requirements", "Normal", extra={"se-focus": True})

    assert model_suffix == model_flag, (
        f"'Normal (SE)' suffix must be equivalent to Normal + se-focus:true. "
        f"suffix={model_suffix!r}, flag={model_flag!r}"
    )
    # Also verify non-SE role is unchanged by the suffix
    dev_suffix = _resolve("senior-developer", "Normal (SE)")
    dev_flag = _resolve("senior-developer", "Normal", extra={"se-focus": True})
    assert dev_suffix == dev_flag, (
        f"Suffix compat must match flag for non-SE role: {dev_suffix!r} vs {dev_flag!r}"
    )


# ---------------------------------------------------------------------------
# New format: tiers: {tier → model_id} direct resolution
# ---------------------------------------------------------------------------

def _resolve_with_project_preset(
    role: str,
    preset_name: str,
    preset_tiers: dict,
    extra: dict | None = None,
) -> str:
    """Helper: resolve with an inline project-local preset using tiers: format."""
    project_config: dict = {
        "tier-preset": preset_name,
        "tier-presets": {
            preset_name: {"description": "test preset", "tiers": preset_tiers}
        },
    }
    if extra:
        project_config.update(extra)
    return resolve_model(
        role=role,
        project_config=project_config,
        agent_meta_root=REPO_ROOT,
        provider="Claude",
        provider_config=_PROVIDER_CONFIG,
    )


def test_new_format_direct_model_resolution() -> None:
    """Preset with tiers: format resolves tier directly to model id — no provider lookup."""
    # developer has model: powerful; preset tiers maps balanced only
    model = _resolve_with_project_preset(
        role="senior-developer",
        preset_name="DirectTest",
        preset_tiers={"powerful": CLAUDE_MODEL_BALANCED},
    )
    assert model == CLAUDE_MODEL_BALANCED, (
        f"New tiers: format should return model id directly, got {model!r}"
    )


def test_old_format_mapping_still_works() -> None:
    """Preset with mapping: format (old) still resolves via provider model-tiers."""
    project_config: dict = {
        "tier-preset": "LegacyPreset",
        "tier-presets": {
            "LegacyPreset": {
                "description": "legacy mapping preset",
                "mapping": {"balanced": "fast", "powerful": "fast"},
            }
        },
    }
    model = resolve_model(
        role="senior-developer",
        project_config=project_config,
        agent_meta_root=REPO_ROOT,
        provider="Claude",
        provider_config=_PROVIDER_CONFIG,
    )
    # developer has tier=powerful; mapping maps powerful→fast; fast maps to haiku
    assert model == CLAUDE_MODEL_FAST, (
        f"Old mapping: format should still work via provider model-tiers, got {model!r}"
    )


def test_provider_tier_override_beats_preset_tiers() -> None:
    """provider-tier-overrides must win over preset tiers: direct model assignment."""
    override_model = CLAUDE_MODEL_FAST  # claude-haiku — deliberately "cheap"
    model = _resolve_with_project_preset(
        role="senior-developer",
        preset_name="OverrideTest",
        preset_tiers={"powerful": CLAUDE_MODEL_MAX},  # would return max without override
        extra={"provider-tier-overrides": {"Claude": {"powerful": override_model}}},
    )
    assert model == override_model, (
        f"provider-tier-overrides must beat preset tiers: expected {override_model!r}, got {model!r}"
    )
