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

P3 adds the orthogonal multiplicity axis (D5/D6): ``resolve_orchestrator_instances``
returns ``(effective_count, clamp_reason_or_None)`` for a provider and
``compose_instance_session_id`` namespaces state as ``<base>__<id>``. At N=1 the
identity is ``None`` and the composition is the unchanged base id.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from .io import SyncError
from .providers import explicit_primary_role

VALID_TOPOLOGIES = frozenset({"primary", "subagent", "hybrid"})
DEFAULT_MAX_INSTANCES = 1
MAX_INSTANCES = 8
VERIFIED_STATES = frozenset({"VERIFIED-RUNTIME", "DOCUMENTED", "UNVERIFIED"})

#: Instance-identity grammar (D6, IC-10): ``[a-z0-9][a-z0-9._-]{0,39}``.
#: The same grammar is used by the guard sentinel (IC-9), the A2A envelope
#: (IC-10) and the state namespace composed below.
ORCHESTRATOR_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,39}")

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


# --- P3: multi-instance identity and resolution ----------------------------
#
# Logical identity model: ``orchestrator#<scope-id>``.
#
# The main chat derives ``<scope-id>`` deterministically from the scope it is
# working on (plan id / task ref, branch name, PR number), normalizes it to
# ``[a-z0-9][a-z0-9._-]{0,39}`` and passes it in the A2A envelope. The dispatch
# target itself stays the plain role name ``orchestrator`` — no ``#`` suffix in
# file names or ``subagent_type``. At N=1 the id is ``None`` and the state
# paths are byte-identical to today.
#
# Missing id at N>1 is a prompt HARD-REJECT plus a guard audit ``id=unset``.
# Duplicate ids / overlapping scopes are a HARD ERROR at spawn time; this is
# the prompt contract (G2), not a runtime registry — P3 deliberately ships no
# registry, so there is nothing here that could silently last-wins.


def is_valid_orchestrator_id(value: Any) -> bool:
    """True when *value* is a safe orchestrator instance id.

    Grammar ``[a-z0-9][a-z0-9._-]{0,39}`` (1..40 chars, lowercase). ``..`` is
    rejected explicitly even though it matches the raw character grammar,
    because the id is later used as a path component (``<base>__<id>.json``).
    """
    if not isinstance(value, str) or ".." in value:
        return False
    return ORCHESTRATOR_ID_RE.fullmatch(value) is not None


def compose_instance_session_id(
    base_session_id: str, instance_id: Optional[str]
) -> str:
    """Compose the state namespace for one orchestrator instance (D6, IC-2).

    * ``instance_id is None`` => *base_session_id* is returned **unchanged**.
      This is the N=1 identity: no suffix, no validation, no rewrite, so the
      existing checkpoint/progress paths stay byte-identical (AC-10).
    * otherwise => ``<base>__<id>``. The id must match
      :data:`ORCHESTRATOR_ID_RE` and the composed id must pass
      ``checkpoint.validate_session_id`` (no path separators, no ``..``, no
      absolute path). Violations raise ``ValueError``.

    The checkpoint import is lazy on purpose: ``checkpoint`` imports this leaf
    module, a module-level import would close the cycle (plan K-3).
    """
    if instance_id is None:
        return base_session_id

    if not is_valid_orchestrator_id(instance_id):
        raise ValueError(
            f"invalid orchestrator instance id {instance_id!r}: expected "
            "[a-z0-9][a-z0-9._-]{0,39} (1..40 chars, no '..')"
        )

    composed = f"{base_session_id}__{instance_id}"
    from .checkpoint import validate_session_id  # lazy: avoid import cycle

    validate_session_id(composed)
    return composed


def _raw_instance_count(
    orch: Mapping, provider: str, *, validate: bool
) -> tuple:
    """Return ``(count, reason)``; ``count`` is 1 on every fail-closed path."""
    if "max-instances" not in orch:
        return DEFAULT_MAX_INSTANCES, None
    value = orch.get("max-instances")
    if isinstance(value, bool) or not isinstance(value, int):
        reason = (
            "orchestrator.max-instances must be an integer between 1 and "
            f"{MAX_INSTANCES} (got {value!r})"
        )
    elif not 1 <= value <= MAX_INSTANCES:
        reason = (
            "orchestrator.max-instances must be between 1 and "
            f"{MAX_INSTANCES} (got {value})"
        )
    else:
        return value, None

    if validate:
        raise SyncError(
            f"{reason} (provider {provider!r}). "
            "Hint: use 1 for the single-orchestrator default."
        )
    return DEFAULT_MAX_INSTANCES, f"{reason} (fail-safe 1)"


def resolve_orchestrator_instances(
    config: dict,
    provider: str,
    topology: TopologyResolution,
    *,
    capabilities: dict,
    validate: bool = True,
) -> tuple:
    """Resolve the effective orchestrator instance count (P3, IC-2).

    Returns ``(effective_count, clamp_reason_or_None)``.

    Rules (D5, AC-8, AC-9):

    * ``max-instances`` unset => 1 (today's behaviour). Same-scope
      contradictions are hard ``SyncError``s when ``validate=True``; with
      ``validate=False`` they fail closed to 1 with a reason (consistency
      checker channel).
    * ``singleton`` present (key existence, never truthiness) + N>1 =>
      ``SyncError``; ``singleton: false`` => ``SyncError`` with the
      "use max-instances" hint; ``singleton`` present + N=1 is redundant but
      valid (the INFO finding belongs to the consistency check).
    * Explicit project ``topology: primary`` + N>1 in the same scope =>
      ``SyncError``. A *provider-scoped* ``primary`` with a global N>1 is the
      cross-scope case: clamped to 1 with a reason, never an error.
    * A *derived* primary is not a same-scope declaration (K-1); the count is
      then governed by the capability cells only.
    * N>1 requires ``orchestrator_instances.multiple is True`` and
      ``topology_verified_state.multiple`` not ``UNVERIFIED``; otherwise the
      count clamps to 1 with a reason.
    """
    orch = _orchestrator(config)

    count, invalid_reason = _raw_instance_count(
        orch, provider, validate=validate
    )
    if invalid_reason is not None:
        return count, invalid_reason

    singleton_declared = "singleton" in orch
    if singleton_declared:
        singleton_value = orch.get("singleton")
        if singleton_value is not True:
            if singleton_value is False:
                message = (
                    "orchestrator.singleton: false is not supported "
                    "(use max-instances)"
                )
            else:
                message = (
                    "orchestrator.singleton must be true when present "
                    f"(got {singleton_value!r}); 'false' is not supported "
                    "(use max-instances)"
                )
            if validate:
                raise SyncError(message)
            return DEFAULT_MAX_INSTANCES, f"{message} (fail-safe 1)"
        if count > DEFAULT_MAX_INSTANCES:
            message = (
                "orchestrator.singleton conflicts with "
                "orchestrator.max-instances"
            )
            if validate:
                raise SyncError(
                    f"{message} (provider {provider!r}). singleton means "
                    "exactly one orchestrator; remove the alias or set "
                    "max-instances: 1."
                )
            return DEFAULT_MAX_INSTANCES, f"{message} (fail-safe 1)"
        # Redundant alias: explicitly one instance, nothing to clamp.
        return DEFAULT_MAX_INSTANCES, None

    project_topology = orch.get("topology")
    if (
        project_topology is not None
        and str(project_topology).strip() == "primary"
        and count > DEFAULT_MAX_INSTANCES
    ):
        message = (
            "orchestrator.topology: primary conflicts with "
            "orchestrator.max-instances"
        )
        if validate:
            raise SyncError(
                f"{message} (provider {provider!r}). primary is a single "
                "entry-point orchestrator; set max-instances: 1 or leave the "
                "topology unset."
            )
        return DEFAULT_MAX_INSTANCES, f"{message} (fail-safe 1)"

    if (
        count > DEFAULT_MAX_INSTANCES
        and topology.source == "provider-override"
        and topology.declared == "primary"
        and topology.effective == "primary"
    ):
        return DEFAULT_MAX_INSTANCES, (
            f"provider-overrides.{provider}.topology: primary clamps global "
            f"max-instances {count} to 1 (cross-scope; WARNING rule AC-9)"
        )

    if count > DEFAULT_MAX_INSTANCES:
        multiple = _capabilities_value(
            capabilities, "orchestrator_instances", "multiple"
        )
        state = _capabilities_value(
            capabilities, "topology_verified_state", "multiple"
        )
        reasons = []
        if multiple is not True:
            reasons.append("orchestrator_instances.multiple is not true")
        if state not in ("VERIFIED-RUNTIME", "DOCUMENTED"):
            reasons.append(
                "topology_verified_state.multiple is "
                f"{state or 'absent'} (UNVERIFIED)"
            )
        if reasons:
            return DEFAULT_MAX_INSTANCES, (
                f"max-instances {count} clamped to 1: " + ", ".join(reasons)
            )

    return count, None
