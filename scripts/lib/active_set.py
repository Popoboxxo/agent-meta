"""Active-set contract (IC-17): the single, per-sync computed role set.

Delegates to the canonical resolvers in ``roles.py`` (``resolve_activation_gates``,
``is_role_enabled``, ``resolve_active_roles``) -- there is deliberately no second
gate logic here. Additionally detects allowlist entries that a gate silently
dropped (``gate_dropped``) and unknown allowlist entries.

``"project"`` is a reserved ``sources`` value only (project-specific roles are
deferred, Q16); ``known_roles`` equals the ``role-defaults`` roles for now.
All collections are sorted/frozen so serialization is byte-stable.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional

from .variables import _resolve_orch_mode
from .roles import (
    _emit_warnings,
    is_role_enabled,
    load_roles_config,
    resolve_activation_gates,
    resolve_active_roles,
    _role_matches_patterns,
)


@dataclass(frozen=True)
class GateDrop:
    role: str
    group: str    # activation_groups key, e.g. "developer_tiers"
    reason: str   # e.g. "requires all of [junior-developer, senior-developer]"


@dataclass(frozen=True)
class ActiveSet:
    roles: frozenset
    routable: frozenset
    known_roles: frozenset
    sources: Mapping[str, str]            # role -> framework | platform | project
    gates: Mapping[str, bool]             # activation group -> enabled
    gate_dropped: tuple                   # tuple[GateDrop, ...], sorted
    missing_template: tuple               # tuple[str, ...], sorted
    producers: Mapping[str, frozenset]    # output_contract id -> active roles

    def has(self, role: str) -> bool:
        return role in self.roles

    def all_active(self, roles: Iterable[str]) -> bool:
        return all(role in self.roles for role in roles)


def _gate_reason(spec: dict) -> str:
    predicate = (spec or {}).get("config_predicate") or {}
    kind = predicate.get("kind")
    if kind == "roles_membership":
        mode = "all" if predicate.get("mode", "any") == "all" else "any"
        members = ", ".join(str(r) for r in predicate.get("roles") or [])
        return f"requires {mode} of [{members}]"
    if kind == "config_flag":
        return f"requires {predicate.get('path', '')} to be enabled"
    return "group disabled by default"


def _detect_gate_drops(roles_cfg: dict, config: dict, gates: dict,
                       known: frozenset) -> list:
    allowlist = config.get("roles")
    if not allowlist:
        return []
    groups_cfg = roles_cfg.get("activation_groups", {}) or {}
    drops = []
    for role in sorted(set(allowlist) & known):
        if is_role_enabled(role, config, gates):
            continue
        for name in sorted(gates):
            if (not gates[name].get("enabled")
                    and _role_matches_patterns(role, gates[name].get("role_patterns") or [])):
                drops.append(GateDrop(role, name, _gate_reason(groups_cfg.get(name) or {})))
                break
    return sorted(drops, key=lambda d: (d.role, d.group))


def compute_active_set(
    config: dict,
    agent_meta_root: Path,
    project_root: Path,
    *,
    warn_sink: Optional[list] = None,
) -> ActiveSet:
    """Compute the ActiveSet once per sync (``project_root`` reserved for Q16)."""
    from .frontmatter import PLATFORM_DIR, collect_sources

    roles_cfg = load_roles_config(agent_meta_root)
    role_defs = roles_cfg.get("roles", {}) or {}
    known = frozenset(role_defs)
    gates = resolve_activation_gates(agent_meta_root, config)

    layer1 = resolve_active_roles(agent_meta_root, config, require_template=False)
    active = resolve_active_roles(
        agent_meta_root, config, require_template=True, warn_sink=warn_sink
    )
    missing_template = tuple(sorted(set(layer1) - set(active)))

    drops = _detect_gate_drops(roles_cfg, config, gates, known)
    unknown = sorted(set(config.get("roles") or []) - known)
    warnings = {f"active-set.unknown-role: '{r}' is not defined in role-defaults" for r in unknown}
    warnings |= {
        f"active-set.gate-dropped: '{d.role}' dropped by group '{d.group}' ({d.reason})"
        for d in drops
    }
    _emit_warnings(warnings, warn_sink)

    overrides, _ = collect_sources(agent_meta_root, list(config.get("platforms") or []))
    sources = {
        role: "platform" if role in overrides and overrides[role].parent.name == PLATFORM_DIR
        else "framework"
        for role in sorted(known)
    }

    # Main-chat skip: in orchestrator.mode "main-chat" the orchestrator is not
    # a dispatch target (same rule as config.py strict-permission scan).
    main_chat = _resolve_orch_mode(config.get("orchestrator") or {}) == "main-chat"
    routable = frozenset(
        role for role in active
        if ((role_defs.get(role) or {}).get("routing") or {}).get("addressability") != "excluded"
        and not (main_chat and role == "orchestrator")
    )

    producers: dict = {}
    for role in active:
        contract = ((role_defs.get(role) or {}).get("handoff") or {}).get("output_contract")
        if contract:
            producers.setdefault(str(contract), set()).add(role)

    return ActiveSet(
        roles=frozenset(active),
        routable=routable,
        known_roles=known,
        sources=sources,
        gates={name: bool(gates[name]["enabled"]) for name in sorted(gates)},
        gate_dropped=tuple(drops),
        missing_template=missing_template,
        producers={k: frozenset(v) for k, v in sorted(producers.items())},
    )


def active_set_variables(active: ActiveSet) -> dict:
    """Template variables derived from the ActiveSet (all values are strings)."""
    variables = {
        "ACTIVE_ROLES": ",".join(sorted(active.roles)),
        "PROJECT_SPECIFIC_AGENTS": "",
    }
    for role in sorted(active.known_roles):
        key = "ROLE_%s_ACTIVE" % role.upper().replace("-", "_")
        variables[key] = "true" if role in active.roles else "false"
    return variables
