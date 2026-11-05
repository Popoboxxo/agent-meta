"""Orchestrator topology resolution (IC-2).

SPEC-orchestrator-topology-2026-11-03 (issue #1077).

This is the ONE resolver for the ``orchestrator.topology`` position axis. It is
a leaf module: it writes nothing, resolves no orchestrator mode (``mode`` is
passed in already resolved) and never branches on a provider name. Provider
differences come exclusively from the capability data
(``topology_support`` / ``topology_degrade`` / ``topology_verified_state``).

Contract (spec IC-2):

1. Precedence: ``orchestrator.provider-overrides.<P>.topology`` >
   ``orchestrator.topology`` > derivation.
2. Unset key => derivation from ``providers.<P>.primary-role``: ``primary``
   only when the role is declared AND present in the active set; otherwise
   ``subagent``. ``hybrid`` is never derived. ``degraded_from`` stays ``None``
   and no warning is emitted (D9).
3. Fallback (B2): when ``topology_support.<axis>`` is ``False`` or
   ``topology_verified_state.<axis>`` is ``UNVERIFIED``, ``effective`` comes
   from ``topology_degrade.<axis>`` when that value is a valid topology,
   otherwise from the fail-safe ``subagent``. ``degraded_from`` is set only
   when the declared value really changed; a mechanism word
   (``"sequential-text"``) lives in ``degradation_reason`` only and is never a
   valid ``effective`` value.
4. ``effective`` is ALWAYS in ``VALID_TOPOLOGIES`` — including ``validate=False``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from .io import SyncError
from .providers import explicit_primary_role

VALID_TOPOLOGIES = frozenset({"primary", "subagent", "hybrid"})
DEFAULT_MAX_INSTANCES = 1
VERIFIED_STATES = frozenset({"VERIFIED-RUNTIME", "DOCUMENTED", "UNVERIFIED"})

_FAIL_SAFE = "subagent"


@dataclass(frozen=True)
class TopologyResolution:
    """Resolved orchestrator position.

    ``verification_state`` is the raw cell from
    ``topology_verified_state.<axis>`` (``None`` when the cell is absent).
    ``derived`` is the convenience mirror of ``source == "derived"``.
    """

    declared: Optional[str]
    effective: str
    source: str
    derived_from: Optional[str]
    degraded_from: Optional[str]
    degradation_reason: Optional[str]
    verification_state: Optional[str]

    def __post_init__(self) -> None:
        if self.effective not in VALID_TOPOLOGIES:
            raise ValueError(
                f"effective topology {self.effective!r} is not one of "
                f"{sorted(VALID_TOPOLOGIES)}"
            )

    @property
    def verified_state(self) -> Optional[str]:
        return self.verification_state

    @property
    def derived(self) -> bool:
        return self.source == "derived"


def _mapping(value: Any) -> Mapping:
    return value if isinstance(value, Mapping) else {}


def _orchestrator(config: Any) -> Mapping:
    return _mapping(_mapping(config).get("orchestrator"))


def _provider_override(config: Any, provider: str) -> Mapping:
    overrides = _orchestrator(config).get("provider-overrides")
    return _mapping(_mapping(overrides).get(provider))


def topology_explicit(config: Any, provider: Optional[str] = None) -> bool:
    """True when a topology value is explicitly declared for this scope.

    ``provider=None`` asks the project scope only. With a provider name the
    provider override also counts. The project key alone never makes a
    provider override "explicit" and vice versa (per-scope question).
    """
    if provider is not None:
        if _provider_override(config, provider).get("topology") is not None:
            return True
    return _orchestrator(config).get("topology") is not None


def _declared(config: Any, provider: str) -> tuple:
    """Return ``(declared_or_None, source)``; source is never "derived" here."""
    override_value = _provider_override(config, provider).get("topology")
    if override_value is not None:
        return str(override_value).strip(), "provider-override"
    project_value = _orchestrator(config).get("topology")
    if project_value is not None:
        return str(project_value).strip(), "project"
    return None, "derived"


def _active_roles(active_set: Any) -> frozenset:
    if active_set is None:
        return frozenset()
    roles = getattr(active_set, "roles", active_set)
    try:
        return frozenset(roles)
    except TypeError:
        return frozenset()


def _derive(provider: str, provider_config: Any, active_set: Any) -> tuple:
    """Return ``(derived_topology, derived_from)`` — never ``hybrid``."""
    role = explicit_primary_role(_mapping(provider_config), provider)
    if role and role in _active_roles(active_set):
        return "primary", f"providers.{provider}.primary-role"
    return _FAIL_SAFE, "active-set default"


def _capabilities_value(capabilities: Any, key: str, axis: str) -> Any:
    return _mapping(_mapping(capabilities).get(key)).get(axis)


def _fallback(axis: str, capabilities: Any) -> tuple:
    """Return ``(effective, reason)`` for an unsupported/unverified cell.

    The reason carries the mechanism word when ``topology_degrade`` is not a
    valid topology; the mechanism word is never returned as ``effective``.
    """
    support = _capabilities_value(capabilities, "topology_support", axis)
    state = _capabilities_value(capabilities, "topology_verified_state", axis)
    degrade = _capabilities_value(capabilities, "topology_degrade", axis)

    effective = (
        degrade
        if isinstance(degrade, str) and degrade in VALID_TOPOLOGIES
        else _FAIL_SAFE
    )
    assert effective in VALID_TOPOLOGIES  # invariant, also for validate=False

    reasons = []
    if support is False:
        reasons.append("support=false")
    if state == "UNVERIFIED":
        reasons.append("capability cell UNVERIFIED")
    reason = ", ".join(reasons)
    if degrade is not None and not (
        isinstance(degrade, str) and degrade in VALID_TOPOLOGIES
    ):
        reason = (
            f"{reason} (degrade mechanism: {degrade}; "
            f"clamped to {_FAIL_SAFE})"
        )
    return effective, reason


def _needs_fallback(axis: str, capabilities: Any) -> bool:
    support = _capabilities_value(capabilities, "topology_support", axis)
    state = _capabilities_value(capabilities, "topology_verified_state", axis)
    return support is False or state == "UNVERIFIED"


def resolve_topology(
    config: dict,
    provider: str,
    *,
    provider_config: dict,
    capabilities: dict,
    mode: str,
    active_set: Any = None,
    validate: bool = True,
) -> TopologyResolution:
    """Resolve the effective orchestrator topology for *provider*.

    ``mode`` arrives already resolved by the caller (single source:
    ``variables._resolve_orch_mode``); this module does not import it. The mode
    does not change the position resolution in v1 — the ``main-chat`` dominance
    rule is a validation/warning concern (IC-8/IC-9), not a second resolver.

    Raises ``SyncError`` for an unknown declared value when ``validate=True``.
    ``validate=False`` never raises: the unknown value fails safe to
    ``subagent`` and the invariant ``effective in VALID_TOPOLOGIES`` holds.
    """
    declared, source = _declared(config, provider)

    if source == "derived":
        derived, derived_from = _derive(provider, provider_config, active_set)
        if _needs_fallback(derived, capabilities):
            effective, reason = _fallback(derived, capabilities)
        else:
            effective, reason = derived, None
        return TopologyResolution(
            declared=None,
            effective=effective,
            source="derived",
            derived_from=derived_from,
            # D9: derivation never reports a degradation/warning, even when a
            # capability clamp adjusted the derived value.
            degraded_from=None,
            degradation_reason=reason if effective != derived else None,
            verification_state=_capabilities_value(
                capabilities, "topology_verified_state", effective
            ),
        )

    if declared not in VALID_TOPOLOGIES:
        if validate:
            raise SyncError(
                f"Invalid orchestrator topology value: {declared!r} "
                f"(provider {provider!r}). Valid values are: "
                "'primary', 'subagent', 'hybrid'. "
                "Hint: omit the key to keep the provider-derived default, or "
                "use one of the three valid values."
            )
        return TopologyResolution(
            declared=declared,
            effective=_FAIL_SAFE,
            source=source,
            derived_from=None,
            degraded_from=declared,
            degradation_reason=(
                f"unknown topology value {declared!r} "
                f"(fail-safe {_FAIL_SAFE})"
            ),
            verification_state=_capabilities_value(
                capabilities, "topology_verified_state", _FAIL_SAFE
            ),
        )

    if _needs_fallback(declared, capabilities):
        effective, reason = _fallback(declared, capabilities)
    else:
        effective, reason = declared, None

    # Coincidence is not a degradation: when the fail-safe (or a degrade value)
    # lands on the declared string, report neither degraded_from nor a reason.
    degraded_from = declared if declared != effective else None
    degradation_reason = reason if degraded_from is not None else None

    return TopologyResolution(
        declared=declared,
        effective=effective,
        source=source,
        derived_from=None,
        degraded_from=degraded_from,
        degradation_reason=degradation_reason,
        verification_state=_capabilities_value(
            capabilities, "topology_verified_state", declared
        ),
    )
