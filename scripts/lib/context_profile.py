"""Context-profile resolution (SPEC-CONTEXT-PROFILES-2026-10-11, IC-01/IC-02).

The profile bundles the context-density measures behind a single opt-in axis
``context-profile`` (``full`` | ``compact``). Resolution is per provider so a
``provider-overrides.<P>.context-profile`` entry can scope ``compact`` to a
single provider without touching the default.

Precedence (spec §4.1, per single setting):

    explicit sub-setting (``context_file.mode``) >
    ``provider-overrides.<P>.context-profile`` >
    ``context-profile`` >
    default

``compact`` implies ``context_file.mode: compact`` only when the mode is not
explicitly set. With no opt-in key every resolved value is the ``full``/``false``
fallback, so renders stay byte-identical to the Phase-1 goldens (AC-01/AC-23).

This module is pure data resolution: no provider literals, no I/O, no render
effect (the provider-injection seam lives in ``config.py`` / ``agent_sync.py``).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Literal, Mapping

ProfileValue = Literal["full", "compact"]
SourceValue = Literal["explicit", "provider-override", "profile", "default"]

_VALID_PROFILES = ("full", "compact")
_VALID_MODES = ("full", "compact")


@dataclass(frozen=True)
class ResolvedContextProfile:
    """Effective context profile for one provider.

    Attributes:
        provider: Provider the resolution is scoped to.
        profile: Effective profile axis value (``full`` | ``compact``).
        context_file_mode: Effective entry-file density; follows the profile
            unless ``context_file.mode`` was explicitly set.
        rules_preset: Effective ``rules-preset`` (global setting, default
            ``default``).
        sources: Provenance per setting (``profile``, ``context_file_mode``,
            ``rules_preset``) — one of ``explicit``/``provider-override``/
            ``profile``/``default``.
    """

    provider: str
    profile: ProfileValue
    context_file_mode: ProfileValue
    rules_preset: str
    sources: Dict[str, SourceValue]


def _validate_profile(value: object, where: str) -> ProfileValue:
    if value not in _VALID_PROFILES:
        raise ValueError(
            f"invalid {where}: {value!r} (expected one of: "
            f"{', '.join(_VALID_PROFILES)})"
        )
    return value  # type: ignore[return-value]


def _override_profile(config: Mapping, provider: str) -> ProfileValue | None:
    """Return the per-provider profile value, or ``None`` when not set.

    A non-mapping block, a missing provider entry or a ``None`` value is treated
    as "not set" (inherit), mirroring the null-block convention (issue #741).
    """
    overrides = config.get("provider-overrides")
    if not isinstance(overrides, Mapping):
        return None
    entry = overrides.get(provider)
    if not isinstance(entry, Mapping):
        return None
    value = entry.get("context-profile")
    if value is None:
        return None
    return _validate_profile(value, f"provider-overrides.{provider}.context-profile")


def resolve_context_profile(config: dict, provider: str) -> ResolvedContextProfile:
    """Resolve the effective context profile for ``provider``.

    Raises:
        ValueError: when ``context-profile`` (global or per provider override)
            carries a value outside the ``full``/``compact`` enum.
    """
    override_profile = _override_profile(config, provider)
    global_profile = config.get("context-profile")

    if override_profile is not None:
        profile: ProfileValue = override_profile
        profile_source: SourceValue = "provider-override"
    elif global_profile is not None:
        profile = _validate_profile(global_profile, "context-profile")
        profile_source = "profile"
    else:
        profile = "full"
        profile_source = "default"

    explicit_mode: ProfileValue | None = None
    context_file = config.get("context_file")
    if isinstance(context_file, Mapping) and context_file.get("mode") in _VALID_MODES:
        explicit_mode = context_file.get("mode")  # type: ignore[assignment]

    if explicit_mode is not None:
        context_file_mode: ProfileValue = explicit_mode
        mode_source: SourceValue = "explicit"
    else:
        context_file_mode = profile
        mode_source = profile_source

    preset_key_present = config.get("rules-preset") is not None
    rules_preset = config.get("rules-preset") or "default"

    sources: Dict[str, SourceValue] = {
        "profile": profile_source,
        "context_file_mode": mode_source,
        "rules_preset": "explicit" if preset_key_present else "default",
    }

    return ResolvedContextProfile(
        provider=provider,
        profile=profile,
        context_file_mode=context_file_mode,
        rules_preset=str(rules_preset),
        sources=sources,
    )


def resolve_shared_file_profile(
    profiles: Iterable[ResolvedContextProfile],
) -> ProfileValue:
    """Downgrade a shared context file to ``full`` if any sharer is ``full``.

    Safe side (ADR-5/Q12): one ``full`` sharer forces ``full`` for the whole
    shared file. An empty iteration is also ``full`` (nothing to compress).
    """
    seen = False
    for resolved in profiles:
        seen = True
        if resolved.profile == "full":
            return "full"
    return "compact" if seen else "full"


def _variables_for(profile: ProfileValue) -> Dict[str, str]:
    return {
        "CONTEXT_PROFILE": profile,
        "CONTEXT_PROFILE_COMPACT": "true" if profile == "compact" else "false",
    }


def context_profile_provider_variables(config: dict, provider: str) -> Dict[str, str]:
    """Return ``CONTEXT_PROFILE``/``CONTEXT_PROFILE_COMPACT`` for ``provider``."""
    resolved = resolve_context_profile(config, provider)
    return _variables_for(resolved.profile)


def context_profile_variables(
    config: dict,
    provider: str,
    shared_users: Iterable[str],
) -> Dict[str, str]:
    """Shared-file wrapper around :func:`context_profile_provider_variables`.

    Applies :func:`resolve_shared_file_profile` across ``shared_users ∪
    {provider}`` so a shared file renders ``full`` as soon as one sharer is
    ``full``; otherwise the per-provider values are returned unchanged.
    """
    users = set(shared_users) | {provider}
    profiles = [resolve_context_profile(config, user) for user in sorted(users)]
    if resolve_shared_file_profile(profiles) == "full":
        return _variables_for("full")
    return context_profile_provider_variables(config, provider)
