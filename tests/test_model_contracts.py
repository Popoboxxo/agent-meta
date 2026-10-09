"""Task 7 — model precedence + single ``model-format`` application (AC-12, AC-2).

Contracts pinned here (all provider-agnostic, config-driven — no provider-name
branch):

* ``config/ai-providers.yaml`` ``model-tiers`` is authoritative: an active
  (global) tier preset must not shadow it. A preset's own provider-specific
  ``providers.<P>.tiers`` entry still wins (explicit active-preset mapping),
  as does a project-local preset — only the preset's *global* Claude-centric
  fallback curve yields to the provider registry.
* ``model-format`` is applied **exactly once** at resolution. A value that
  already carries the template's literal prefix is returned unchanged, so
  ``kimi-code/kimi-code/*`` can never leak (idempotent application).
* ``resolve_model`` never returns a raw tier token (``nano``/``fast``/...):
  a tier routes through ``_resolve_tier_to_model`` once and an unresolvable
  tier yields ``""`` (so no ``model:`` field is injected) — the resolver-side
  half of the ``model-inherit-fallback`` contract.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.lib.providers import load_providers_config
from scripts.lib.roles import _KNOWN_TIERS, load_roles_config, resolve_model

REPO_ROOT = Path(__file__).resolve().parents[1]

_PROVIDER_CONFIG = load_providers_config(REPO_ROOT)
_ROLES = sorted(load_roles_config(REPO_ROOT)["roles"])

KIMICODE_FORMATTED_BALANCED = "kimi-code/kimi-k2.7-code"


def _resolve(provider: str, role: str, config: dict | None = None) -> str:
    """Resolve a role's model with the Normal preset (config override optional)."""
    project_config: dict = {"tier-preset": "Normal"}
    if config:
        project_config.update(config)
    return resolve_model(
        role=role,
        project_config=project_config,
        agent_meta_root=REPO_ROOT,
        provider=provider,
        provider_config=_PROVIDER_CONFIG,
    )


def _global_normal_preset() -> dict:
    with (REPO_ROOT / "config" / "tier-presets.yaml").open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)["Normal"]


# --------------------------------------------------------------------------
# model-tiers precedence over the active preset
# --------------------------------------------------------------------------


# Synthetic precedence fixture: the two precedence tests below must not depend
# on the real tier-presets.yaml / ai-providers.yaml values (a registry-faithful
# global fallback legitimately equals Mammouth's model-tiers).
_SENTINEL_PRESET_FALLBACK = "sentinel-preset-global-powerful"
_SENTINEL_REGISTRY_TIER = "sentinel-registry-powerful"
_SENTINEL_OTHER_PROVIDER_TIER = "sentinel-opencode-preset-powerful"


def _synthetic_precedence(monkeypatch: pytest.MonkeyPatch) -> tuple[dict, dict]:
    """Install a synthetic global ``Normal`` preset; return
    ``(preset, provider_config)``.

    The preset has a SENTINEL global ``tiers.powerful`` fallback and a
    provider-specific entry for a *different* provider only (Opencode), so
    Mammouth has no preset entry. The provider config keeps Mammouth's real
    ``model-format`` but carries a distinct SENTINEL ``model-tiers.powerful``,
    so the values differ by construction.
    """
    preset = {
        "description": "synthetic precedence fixture",
        "tiers": {"powerful": _SENTINEL_PRESET_FALLBACK},
        "providers": {
            "Opencode": {"tiers": {"powerful": _SENTINEL_OTHER_PROVIDER_TIER}}
        },
    }
    monkeypatch.setattr(
        "scripts.lib.roles.load_tier_presets", lambda _root: {"Normal": preset}
    )
    mammouth = dict(_PROVIDER_CONFIG["Mammouth"])
    mammouth["model-tiers"] = {"powerful": _SENTINEL_REGISTRY_TIER}
    return preset, {"Mammouth": mammouth}


def _resolve_synthetic(provider_config: dict) -> str:
    """Resolve Mammouth/senior-developer (tier ``powerful``) with the synthetic
    config as the active *global* Normal preset."""
    return resolve_model(
        role="senior-developer",
        project_config={"tier-preset": "Normal"},
        agent_meta_root=REPO_ROOT,
        provider="Mammouth",
        provider_config=provider_config,
    )


def test_ai_providers_model_tiers_beat_active_preset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-12: the global preset's Claude-centric ``tiers`` fallback must
    not shadow the provider's own ``model-tiers`` table.

    Mammouth has a registry catalog but no ``Normal.providers.Mammouth`` entry,
    so before the fix the global ``tiers.powerful`` leaked; the registry tier
    must win. Runs on a synthetic preset/provider config
    (``_synthetic_precedence``), independent of the real config values.
    """
    preset, provider_config = _synthetic_precedence(monkeypatch)
    registry_tier = provider_config["Mammouth"]["model-tiers"]["powerful"]
    preset_fallback = preset["tiers"]["powerful"]
    assert registry_tier != preset_fallback, (
        "fixture sanity: the registry tier and the preset fallback must differ "
        f"(both are {registry_tier!r})"
    )

    resolved = _resolve_synthetic(provider_config)
    assert resolved == f"mammouth/{registry_tier}", (
        "ai-providers.yaml model-tiers must win over the preset global fallback: "
        f"expected {registry_tier!r} (formatted), got {resolved!r}"
    )


def test_registry_less_provider_still_uses_preset_fallback() -> None:
    """A provider with an empty ``model-tiers`` catalog keeps the historical
    preset-global fallback (only a real registry entry is authoritative)."""
    continue_tiers = _PROVIDER_CONFIG["Continue"]["model-tiers"]
    assert not continue_tiers, "fixture sanity: Continue must have an empty catalog"
    resolved = _resolve("Continue", "senior-developer")
    assert resolved == _global_normal_preset()["tiers"]["powerful"]


def test_preset_provider_specific_tiers_are_explicit_override() -> None:
    """Orchestrator decision (Task 7): a preset's provider-specific
    ``providers.<P>.tiers`` entry is an explicit per-provider override and is
    NOT shadowed by the registry's ``model-tiers`` table.

    The spec sentence "a preset ``tiers`` map is a fallback behind it" is read
    as applying to the preset's *global* ``tiers`` map only; a provider-specific
    entry stays an explicit override. Opencode has a
    ``Normal.providers.Opencode.tiers.powerful`` entry, so the preset value must
    win over ``ai-providers.yaml``'s Opencode ``model-tiers.powerful``.
    """
    preset = _global_normal_preset()
    preset_tier = preset["providers"]["Opencode"]["tiers"]["powerful"]
    registry_tier = _PROVIDER_CONFIG["Opencode"]["model-tiers"]["powerful"]
    assert preset_tier != registry_tier, (
        "fixture sanity: the preset provider-specific tier and the registry tier "
        f"must differ (both are {preset_tier!r})"
    )

    resolved = _resolve("Opencode", "senior-developer")
    assert resolved == preset_tier, (
        "a preset's provider-specific tiers entry is an explicit override and "
        f"must win: expected {preset_tier!r}, got {resolved!r}"
    )


def test_provider_without_preset_entry_falls_back_to_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A provider that has a registry ``model-tiers`` value but NO preset
    provider-specific entry resolves from the registry, not from the preset's
    global fallback (Mammouth, made explicit here). Runs on a synthetic
    preset/provider config (``_synthetic_precedence``)."""
    preset, provider_config = _synthetic_precedence(monkeypatch)
    assert "Mammouth" not in (preset.get("providers") or {}), (
        "fixture sanity: Mammouth must have no preset provider-specific entry"
    )
    registry_tier = provider_config["Mammouth"]["model-tiers"]["powerful"]
    preset_fallback = preset["tiers"]["powerful"]
    assert registry_tier != preset_fallback, (
        "fixture sanity: the registry tier and the preset global fallback must "
        f"differ (both are {registry_tier!r})"
    )

    resolved = _resolve_synthetic(provider_config)
    assert resolved == f"mammouth/{registry_tier}", (
        "without a preset provider-specific entry the registry model-tiers must "
        f"win: expected {registry_tier!r} (formatted), got {resolved!r}"
    )


# --------------------------------------------------------------------------
# model-format applied exactly once
# --------------------------------------------------------------------------


def test_project_local_preset_overrides_same_named_global_preset() -> None:
    """A project-local preset shadows a same-named global preset.

    ``Normal`` ships in ``config/tier-presets.yaml``; when a project redefines
    ``tier-presets.Normal`` inline, the project definition must be used — the
    global preset must not win just because the name matches.
    """
    global_powerful = _global_normal_preset()["tiers"]["powerful"]
    local_powerful = "claude-sonnet-4-6"
    assert local_powerful != global_powerful, (
        "fixture sanity: the project-local tier and the global preset tier must "
        f"differ (both are {local_powerful!r})"
    )

    config = {
        "tier-presets": {
            "Normal": {
                "description": "project-local override",
                "tiers": {"powerful": local_powerful},
            }
        }
    }
    resolved = _resolve("Claude", "senior-developer", config)
    assert resolved == local_powerful, (
        "a project-local preset must shadow the same-named global preset: "
        f"expected {local_powerful!r}, got {resolved!r}"
    )


def test_project_local_preset_tiers_beat_ai_providers_model_tiers() -> None:
    """A2 carve-out (spec amendment): a project-local preset's own ``tiers``
    map beats the provider registry's ``model-tiers`` table, as an explicitly
    approved EXCEPTION to AC-12's generic-preset direction.

    Authority: ``docs/specs/2026-09-30-provider-audit-opencode-v2.md``
    §Amendments A2 (project-local preset precedence carve-out); implementation
    of record: ``roles.py::resolve_model`` ``is_project_local_preset`` branch
    (:512-517). This direction is NOT an AC-12 conformance claim — AC-12 pins
    the generic (global) preset case, where ``ai-providers.yaml model-tiers``
    wins.

    Mammouth has a registry ``model-tiers.powerful`` (= claude-opus-5); the
    project-local value must not be shadowed by it.
    """
    registry_tier = _PROVIDER_CONFIG["Mammouth"]["model-tiers"]["powerful"]
    local_powerful = "claude-sonnet-4-6"
    assert local_powerful != registry_tier, (
        "fixture sanity: the project-local tier and the registry tier must "
        f"differ (both are {local_powerful!r})"
    )

    config = {
        "tier-presets": {
            "Normal": {
                "description": "project-local override",
                "tiers": {"powerful": local_powerful},
            }
        }
    }
    resolved = _resolve("Mammouth", "senior-developer", config)
    assert resolved == f"mammouth/{local_powerful}", (
        "a project-local preset's tiers map must beat ai-providers.yaml "
        f"model-tiers: expected {local_powerful!r} (formatted), got {resolved!r}"
    )


def test_kimicode_emits_single_prefix() -> None:
    """AC-2: every resolved KimiCode ID carries exactly one ``kimi-code/``
    prefix and the formatted ID is a declared catalog member."""
    resolved = _resolve("KimiCode", "orchestrator")
    assert resolved.startswith("kimi-code/"), (
        f"KimiCode IDs must be namespaced, got {resolved!r}"
    )
    assert "kimi-code/kimi-code/" not in resolved, (
        f"model-format must be applied exactly once, got doubled prefix {resolved!r}"
    )
    assert resolved.count("kimi-code/") == 1, (
        f"exactly one prefix expected, got {resolved!r}"
    )
    catalog = _PROVIDER_CONFIG["KimiCode"]["model-catalog"]
    assert resolved in catalog, (
        f"{resolved!r} is not in the declared model-catalog {catalog!r}"
    )


def test_mammouth_emits_single_prefix() -> None:
    """#852: every resolved Mammouth ID carries exactly one ``mammouth/``
    prefix (idempotent model-format, no doubled prefix)."""
    resolved = _resolve("Mammouth", "orchestrator")
    assert resolved.startswith("mammouth/"), (
        f"Mammouth IDs must be namespaced, got {resolved!r}"
    )
    assert "mammouth/mammouth/" not in resolved, (
        f"model-format must be applied exactly once, got doubled prefix {resolved!r}"
    )
    assert resolved.count("mammouth/") == 1, (
        f"exactly one prefix expected, got {resolved!r}"
    )


def test_kimicode_bare_override_gets_single_prefix() -> None:
    """A bare model override is normalised through ``model-format`` once."""
    config = {"model-overrides": {"KimiCode": {"developer": "kimi-k2.6"}}}
    resolved = _resolve("KimiCode", "developer", config)
    assert resolved == "kimi-code/kimi-k2.6"


def test_kimicode_prefixed_override_is_not_doubled() -> None:
    """An already-formatted ID passes through unchanged (idempotent), so the
    template can never produce ``kimi-code/kimi-code/*``."""
    config = {"model-overrides": {"KimiCode": {"developer": "kimi-code/kimi-k2.6"}}}
    resolved = _resolve("KimiCode", "developer", config)
    assert resolved == "kimi-code/kimi-k2.6"


def test_default_model_format_is_a_noop() -> None:
    """Providers with the default ``{model}`` template are byte-unchanged.

    ``senior-developer`` is a role *default*, so it resolves through the active
    preset's provider-specific Claude table (``providers.Claude.tiers.powerful``
    wins over the ai-providers ``model-tiers`` catalog -- see the module
    docstring). The two sources may differ; the expected value is therefore the
    preset's provider-specific entry, i.e. the value this role actually gets.
    """
    resolved = _resolve("Claude", "senior-developer")
    assert resolved == _global_normal_preset()["providers"]["Claude"]["tiers"]["powerful"]
    assert "/" not in resolved


# --------------------------------------------------------------------------
# resolve_model never emits a raw tier token
# --------------------------------------------------------------------------


def test_unresolvable_override_all_yields_empty_not_raw_tier() -> None:
    """AC-12/D3 (resolver half): Continue has no catalog, so an override-all
    tier cannot resolve — ``resolve_model`` returns ``""`` (no raw token)."""
    config = {"model-override-all": {"Continue": "balanced"}}
    for role in _ROLES:
        resolved = resolve_model(
            role=role,
            project_config=config,
            agent_meta_root=REPO_ROOT,
            provider="Continue",
            provider_config=_PROVIDER_CONFIG,
        )
        assert resolved == "", (
            f"{role}: unresolvable override-all must yield '', got {resolved!r}"
        )


def test_raw_tier_override_is_resolved_not_emitted() -> None:
    """A tier-valued ``provider-tier-overrides`` entry routes through the tier
    resolver and never leaks the raw token."""
    config = {"provider-tier-overrides": {"Claude": {"balanced": "fast"}}}
    resolved = _resolve("Claude", "developer", config)
    assert resolved not in _KNOWN_TIERS, (
        f"a raw tier token must never be emitted, got {resolved!r}"
    )
    assert resolved == _PROVIDER_CONFIG["Claude"]["model-tiers"]["fast"]


@pytest.mark.parametrize("provider", sorted(_PROVIDER_CONFIG))
def test_no_registered_provider_resolves_to_a_raw_tier(provider: str) -> None:
    """Sweep every registered provider: no role may resolve to a bare tier."""
    for role in _ROLES:
        resolved = _resolve(provider, role)
        assert resolved not in _KNOWN_TIERS, (
            f"{provider}/{role}: raw tier token leaked: {resolved!r}"
        )
