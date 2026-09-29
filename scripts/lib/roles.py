"""Roles config loading, activation resolution and model/memory/permissionMode.

Canonical role-activation resolver (SPEC ``dynamic-routing-template-slimming``,
AC A2): ``resolve_activation_gates`` reads the single default table from
``config/role-defaults.yaml::activation_groups``; ``is_role_enabled`` maps a
role to its activation group(s) via ``role_patterns``; ``resolve_active_roles``
produces Layer 1 (gates + project whitelist) and Layer 2 (∩ generatable
templates) deterministically. Provider-agnostic by construction.
"""
from __future__ import annotations

import fnmatch
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .io import _load_yaml_or_json
from .providers import provider_has_capability

if TYPE_CHECKING:
    from .log import SyncLog

ROLES_CONFIG = "config/role-defaults.yaml"
_ROLES_CONFIG_LEGACY = "roles.config.yaml"
_ROLES_CONFIG_JSON = "roles.config.json"  # legacy fallback

# Abstract tier names defined in role-defaults.yaml
_KNOWN_TIERS = {"nano", "fast", "balanced", "powerful", "max", "ultra"}
_TIER_SEQUENCE = ["nano", "fast", "balanced", "powerful", "max", "ultra"]

# Legacy Claude aliases — resolved only when no provider context is available
_CLAUDE_ALIASES = {"haiku", "sonnet", "opus"}

@lru_cache(maxsize=None)
def load_tier_presets(agent_meta_root: Path) -> dict:
    # ponytail: process-lifetime cache — file is framework config, never
    # rewritten mid-run, and every caller only reads the result (never
    # mutates it in place). Cuts ~316 redundant yaml.safe_load() calls per
    # full multi-provider render down to one per unique root (issue #553).
    presets_path = agent_meta_root / "config" / "tier-presets.yaml"
    data, _ = _load_yaml_or_json(presets_path)
    return data or {}

def _upgrade_tier(tier: str, steps: int) -> str:
    if tier not in _TIER_SEQUENCE:
        return tier
    idx = _TIER_SEQUENCE.index(tier)
    new_idx = min(len(_TIER_SEQUENCE) - 1, idx + steps)
    return _TIER_SEQUENCE[new_idx]


@lru_cache(maxsize=None)
def load_roles_config(agent_meta_root: Path) -> dict:
    """Load config/role-defaults.yaml with fallback to legacy paths.

    Cached per ``agent_meta_root`` (process lifetime): the file is read-only
    framework config within a sync run and every caller only reads the
    returned dict (this loader was re-parsed dozens of times per render,
    dominating wall time in multi-provider integration tests).

    Returns a dict with two keys: ``roles`` (unchanged, back-compatible) and
    ``activation_groups`` (the SPEC Block A single default table, empty when
    absent). Existing readers of ``["roles"]`` are unaffected.
    """
    data, _ = _load_yaml_or_json(
        agent_meta_root / ROLES_CONFIG,
        agent_meta_root / _ROLES_CONFIG_LEGACY,
        agent_meta_root / _ROLES_CONFIG_JSON,
    )
    if not data:
        return {"roles": {}, "activation_groups": {}}
    return {
        "roles": {k: v for k, v in data.get("roles", {}).items() if not k.startswith("_")},
        "activation_groups": data.get("activation_groups", {}) or {},
    }


def build_role_map(agent_meta_root: Path) -> dict[str, str]:
    """Build ROLE_MAP dynamically from roles.config.yaml.

    Returns a dict mapping role name → role name (identity mapping).
    All roles listed in roles.config.yaml are included.
    """
    roles_cfg = load_roles_config(agent_meta_root)
    return {role: role for role in roles_cfg["roles"]}


# ---------------------------------------------------------------------------
# Canonical activation resolver (SPEC dynamic-routing-template-slimming, A2)
# ---------------------------------------------------------------------------

def resolve_dotted(config: dict, path: str) -> object:
    """Resolve a dotted ``a.b.c`` path inside ``config``.

    Returns ``None`` when any segment is missing or an intermediate value is
    not a mapping — callers treat that as "not configured" and fall back to
    the group ``default``.
    """
    node: object = config
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _evaluate_config_predicate(predicate: dict, config: dict, default: bool) -> bool:
    """Evaluate a group ``config_predicate`` against the project config.

    ``kind: config_flag``      → ``bool(resolve_dotted(config, path))``;
                                 missing path → ``default``.
    ``kind: roles_membership`` → ``any``/``all`` over
                                 ``config.get("roles", [])``.
    Unknown/missing kind       → ``default``.
    """
    kind = predicate.get("kind")
    if kind == "config_flag":
        value = resolve_dotted(config, str(predicate.get("path", "")))
        return default if value is None else bool(value)
    if kind == "roles_membership":
        members = set(config.get("roles") or [])
        roles = list(predicate.get("roles") or [])
        if predicate.get("mode", "any") == "all":
            return bool(roles) and all(role in members for role in roles)
        return any(role in members for role in roles)
    return default


def resolve_activation_gates(agent_meta_root: Path, config: dict) -> dict:
    """Resolve every activation group to its effective enable state.

    Single default table: ``role-defaults.yaml::activation_groups.<group>.default``.
    The project ``config`` beats the default (explicitly set value wins).
    Deterministic (groups sorted by name), provider-agnostic — no provider
    branch anywhere.

    Returns ``{group_name: {"enabled": bool, "role_patterns": [str, ...]}}``.
    ``role_patterns`` is carried alongside ``enabled`` so the root-less
    ``is_role_enabled(role, config, gates)`` can map a role to its group
    without reloading the config file.
    """
    groups_cfg = load_roles_config(agent_meta_root).get("activation_groups", {}) or {}
    gates: dict[str, dict] = {}
    for name in sorted(groups_cfg):
        spec = groups_cfg[name] or {}
        predicate = spec.get("config_predicate") or {}
        gates[name] = {
            "enabled": _evaluate_config_predicate(
                predicate, config, bool(spec.get("default", False))
            ),
            "role_patterns": [str(p) for p in (spec.get("role_patterns") or [])],
        }
    return gates


def _role_matches_patterns(role: str, patterns: list[str]) -> bool:
    """Exact-name or glob match (``se-*``) — case-sensitive, OS-independent."""
    return any(fnmatch.fnmatchcase(role, pattern) for pattern in patterns)


def is_role_enabled(role: str, config: dict, gates: dict) -> bool:
    """Return whether ``role`` passes its activation group gate(s).

    ``True`` when ``role`` belongs to no group (via ``role_patterns``) or when
    at least one of its groups is enabled; ``False`` when the role belongs to
    group(s) and all of them are disabled. ``config`` is accepted for
    signature stability — the effective state already lives in ``gates``
    (``config_predicate`` beats ``default``).
    """
    memberships = [
        group
        for group in gates.values()
        if _role_matches_patterns(role, group.get("role_patterns") or [])
    ]
    if not memberships:
        return True
    return any(group.get("enabled", False) for group in memberships)


@lru_cache(maxsize=None)
def _cached_template_roles(agent_meta_root: str, platforms: tuple[str, ...]) -> frozenset[str]:
    """Cached generatable role set for a (root, platforms) pair."""
    from .frontmatter import collect_sources, target_filename

    root = Path(agent_meta_root)
    overrides, _ = collect_sources(root, list(platforms))
    role_map = build_role_map(root)
    return frozenset(role for role in overrides if target_filename(role, role_map))


def resolve_template_roles(agent_meta_root: Path, config: dict) -> set[str]:
    """Return the generatable role set ("Layer 2 universe").

    ``collect_sources(agent_meta_root, platforms)`` minus ``WRAPPER_TEMPLATES``
    (already excluded by ``collect_sources``) minus roles without a ROLE_MAP
    entry — matching the ``target_filename(role, role_map)`` filter of
    ``agents.build_agent_hints``/``build_agent_table``, so routing targets and
    hints/table stay congruent (RVW-27). ``frontmatter`` is imported lazily to
    keep the import graph acyclic; cached per ``(agent_meta_root, platforms)``.
    """
    platforms = tuple(str(p) for p in (config.get("platforms") or []))
    return set(_cached_template_roles(str(agent_meta_root), platforms))


def _emit_warnings(warnings: set[str], warn_sink: list[str] | None) -> None:
    """Emit deterministic (sorted, deduplicated) warnings.

    With a ``warn_sink`` the list is extended in place (deduplicated against
    already-present entries). Without one, the existing ``SyncLog`` fallback
    writes to stderr — no warning is ever swallowed.
    """
    if not warnings:
        return
    ordered = sorted(warnings)
    if warn_sink is not None:
        existing = set(warn_sink)
        warn_sink.extend(w for w in ordered if w not in existing)
        return
    from .log import SyncLog

    log = SyncLog()
    for message in ordered:
        log.warn(message)


def resolve_active_roles(
    agent_meta_root: Path,
    config: dict,
    *,
    require_template: bool = False,
    template_roles: set[str] | None = None,
    warn_sink: list[str] | None = None,
) -> list[str]:
    """Return the sorted active role set.

    Layer 1: activation gates (``resolve_activation_gates``) + optional project
    ``config["roles"]`` whitelist (AND filter). ``variables`` is deliberately
    *not* a gate source — ``config`` is the only one (RVW-14).

    ``require_template=True`` intersects with the generatable role set
    (Layer 2). ``template_roles=None`` is resolved lazily via
    ``resolve_template_roles`` (no ``ValueError`` in the default path, RVW-18);
    ``agent_meta_root`` is a mandatory parameter and there is no ValueError
    branch (RVW-28).

    ``warn_sink``: optional list sink receiving deterministically sorted,
    deduplicated warning strings:
    - ``"active role without template: <role>"``
    - ``"template without role-defaults entry: <role>"``
      (``WRAPPER_TEMPLATES`` excepted)

    Without a sink, the same messages go through ``SyncLog`` (stderr).
    """
    roles_cfg = load_roles_config(agent_meta_root)
    all_roles = roles_cfg.get("roles", {}) or {}
    gates = resolve_activation_gates(agent_meta_root, config)

    whitelist = config.get("roles")
    whitelist_set = set(whitelist) if whitelist is not None else None

    layer1 = [
        role
        for role in sorted(all_roles)
        if is_role_enabled(role, config, gates)
        and (whitelist_set is None or role in whitelist_set)
    ]

    if not require_template:
        return layer1

    if template_roles is None:
        universe = resolve_template_roles(agent_meta_root, config)
    else:
        universe = set(template_roles)

    from .frontmatter import WRAPPER_TEMPLATES

    warnings: set[str] = set()
    for role in layer1:
        if role not in universe:
            warnings.add(f"active role without template: {role}")
    for role in universe:
        if role not in all_roles and role not in WRAPPER_TEMPLATES:
            warnings.add(f"template without role-defaults entry: {role}")

    _emit_warnings(warnings, warn_sink)

    return [role for role in layer1 if role in universe]


def _resolve_tier_to_model(tier_or_alias: str, provider: str, provider_config: dict) -> str:
    """Map an abstract tier name (or legacy alias) to a provider-specific model ID.

    Resolution order:
    1. Tier name (nano/fast/balanced/powerful/max) → provider model-tiers table
    2. Legacy alias (haiku/sonnet/opus) → provider model-aliases table
    3. Full model ID (e.g. claude-sonnet-4-6) → returned as-is
    4. Empty string → returned as-is (no model field injected)
    """
    if not tier_or_alias:
        return ""

    pc = provider_config.get(provider, {})
    model_tiers = pc.get("model-tiers", {})
    model_aliases = pc.get("model-aliases", {})

    # 1. Abstract tier
    if tier_or_alias in _KNOWN_TIERS:
        resolved = model_tiers.get(tier_or_alias, "")
        return resolved  # empty = provider has no model for this tier (e.g. Continue)

    # 2. Legacy alias
    if tier_or_alias in _CLAUDE_ALIASES:
        resolved = model_aliases.get(tier_or_alias, "")
        if resolved:
            return resolved
        # If provider has no alias table (non-Claude), try treating as fast/balanced/powerful
        legacy_tier_map = {"haiku": "fast", "sonnet": "balanced", "opus": "powerful"}
        fallback_tier = legacy_tier_map.get(tier_or_alias, "balanced")
        return model_tiers.get(fallback_tier, "")

    # 3. Full model ID or unknown string — pass through
    return tier_or_alias


def resolve_model(
    role: str,
    project_config: dict,
    agent_meta_root: Path,
    provider: str = "Claude",
    provider_config: dict | None = None,
    log: Optional["SyncLog"] = None,
) -> str:
    """Resolve the model ID for a role and provider using tier presets and registry.

    Resolution order (highest to lowest):
    1. Global override: project_config["model-override-all"][provider] —
       tier/alias/model ID applied to every role of this provider.
    2. Main-chat inheritance: project_config["model-inherit-main-chat"][provider]
       truthy → return "" so inject_model_field() omits the model: field and
       the agent inherits the main-chat model at runtime.
    Stages 1 and 2 are mutually exclusive per provider; validation of that
    constraint happens in scripts/lib/config.py::_validate_config(), not here.
    3. Everything else: per-role overrides, role-defaults, tier-overrides and
       tier presets, resolved via _resolve_tier_to_model().
    """

    tier_or_id = ""
    explicit_override = False

    # --- Global per-provider "override all" (highest precedence, reversible) ---
    # If ``model-override-all[provider]`` is set (non-empty), EVERY role of that
    # provider is blasted onto this single model. Removing the key (or the whole
    # block) from project.yaml makes sync fall back to the normal per-agent
    # resolution automatically — no per-role cleanup required.
    override_all = project_config.get("model-override-all", {})
    if isinstance(override_all, dict):
        raw_all = override_all.get(provider)
        if raw_all:
            resolved_all = _resolve_tier_to_model(str(raw_all), provider, provider_config)
            if log:
                log.debug(f"{provider}/{role}", f"GLOBAL override-all for provider '{provider}' (reversible): {resolved_all}")
            return resolved_all

    # model-inherit-main-chat: the agent deliberately gets NO model: field and
    # inherits the main-chat model at runtime. Returning "" is the established
    # mechanism — inject_model_field() omits the model: field for an empty
    # resolved value. Mutually exclusive with model-override-all per provider;
    # that constraint is validated in config.py::_validate_config().
    inherit_main_chat = project_config.get("model-inherit-main-chat", {})
    if isinstance(inherit_main_chat, dict) and inherit_main_chat.get(provider):
        if log:
            log.debug(
                f"{provider}/{role}",
                f"model-inherit-main-chat active for provider '{provider}': omitting model field (inherits main-chat model)",
            )
        return ""

    provider_overrides = project_config.get("model-overrides", {})
    provider_specific = provider_overrides.get(provider, {})
    if isinstance(provider_specific, dict) and role in provider_specific:
        tier_or_id = str(provider_specific[role])
        explicit_override = True
        if log:
            log.debug(f"{provider}/{role}", f"Model explicitly overriden for provider '{provider}': {tier_or_id}")
    elif isinstance(provider_overrides, dict) and role in provider_overrides:
        flat_value = provider_overrides[role]
        if not isinstance(flat_value, dict):  # noqa: SIM102
            if provider_has_capability(
                (provider_config or {}).get(provider), "model-overrides-flat"
            ):
                tier_or_id = str(flat_value)
                explicit_override = True
                if log:
                    log.debug(f"{provider}/{role}", f"Model explicitly overriden via flat map: {tier_or_id}")

    # 2. Meta default from role-defaults.yaml
    if not tier_or_id:
        roles_cfg = load_roles_config(agent_meta_root)
        tier_or_id = roles_cfg["roles"].get(role, {}).get("model", "")
        if tier_or_id and log:
            log.debug(f"{provider}/{role}", f"Model/Tier from role-defaults: {tier_or_id}")

    # Check if role has an explicit tier override (skip when user already set explicit model-override)
    if not explicit_override:
        tier_overrides = project_config.get("tier-overrides", {})
        if role in tier_overrides:
            tier_or_id = tier_overrides[role]
            if log:
                log.debug(f"{provider}/{role}", f"Tier explicitly overridden: {tier_or_id}")

    # If it's not a known tier (e.g. a hardcoded model id), fallback to old logic
    if tier_or_id and tier_or_id not in _KNOWN_TIERS:
        resolved = _resolve_tier_to_model(tier_or_id, provider, provider_config)
        if log:
            log.debug(f"{provider}/{role}", f"Tier '{tier_or_id}' resolved directly to: {resolved}")
        return resolved

    base_tier = tier_or_id

    # 3. Apply SE Focus and Presets
    preset_name = project_config.get("tier-preset", "Normal") or "Normal"
    se_focus = bool(project_config.get("se-focus", False))
    # Backward compat: old configs may have " (SE)" suffix in tier-preset value
    if preset_name.endswith(" (SE)"):
        se_focus = True
        preset_name = preset_name.replace(" (SE)", "")
    if se_focus and role.startswith("se-"):
        base_tier = _upgrade_tier(base_tier, 1)
        if log:
            log.debug(f"{provider}/{role}", f"SE Focus applied, tier upgraded to: {base_tier}")

    # C1 fix: presets are top-level keys in tier-presets.yaml, not nested under "presets:"
    # Merge: project-local presets (project_config["tier-presets"]) override global ones.
    global_presets = load_tier_presets(agent_meta_root)
    project_presets = project_config.get("tier-presets", {}) or {}

    if isinstance(project_presets, dict) and preset_name in project_presets:
        preset_data = project_presets[preset_name] or {}
        if log:
            log.debug(f"{provider}/{role}", f"Preset '{preset_name}' resolved from project-local tier-presets")
    else:
        preset_data = global_presets.get(preset_name, {}) or {}

    # --- New format: tiers: {tier → model_id} direct ---
    if "tiers" in preset_data:
        # Provider-specific tier within preset takes priority over global tiers
        provider_preset_tiers = (preset_data.get("providers") or {}).get(provider, {}).get("tiers") or {}
        direct_model = provider_preset_tiers.get(base_tier) or preset_data["tiers"].get(base_tier, "")
        if direct_model:
            # provider-tier-overrides take priority over preset tiers
            pto = project_config.get("provider-tier-overrides", {})
            if provider in pto and base_tier in pto[provider]:
                resolved = str(pto[provider][base_tier])
                if log:
                    log.debug(f"{provider}/{role}", f"Tier '{base_tier}' explicitly overriden for provider '{provider}': {resolved}")
                return resolved
            source = f"provider '{provider}'" if provider_preset_tiers.get(base_tier) else "global fallback"
            if log:
                log.debug(f"{provider}/{role}", f"Tier '{base_tier}' resolved from preset '{preset_name}' ({source}): {direct_model}")
            return direct_model

    # --- Old format: mapping: {tier → tier} + provider model-tiers ---
    preset_matrix = preset_data.get("mapping", {}) or {}

    mapped_tier = preset_matrix.get(base_tier, base_tier)
    if log and mapped_tier != base_tier:
        log.debug(f"{provider}/{role}", f"Tier '{base_tier}' mapped to '{mapped_tier}' via preset '{preset_name}'")

    pto = project_config.get("provider-tier-overrides", {})
    if provider in pto and mapped_tier in pto[provider]:
        resolved = str(pto[provider][mapped_tier])
        if log:
            log.debug(f"{provider}/{role}", f"Tier '{mapped_tier}' explicitly overriden for provider '{provider}': {resolved}")
        return resolved

    # Resolve tier to provider-specific model ID
    resolved = _resolve_tier_to_model(mapped_tier, provider, provider_config)
    if log:
        log.debug(f"{provider}/{role}", f"Tier '{mapped_tier}' resolved to: {resolved}")
    return resolved


def resolve_permission_mode(role: str, project_config: dict, agent_meta_root: Path) -> str:
    """Resolve the permissionMode for a role.

    Precedence (highest to lowest):
    1. Project override: project_config["permission-mode-overrides"][role]
    2. Meta default:     roles.config.yaml roles[role].permission_mode
    3. Empty string:     no permissionMode: field injected
    """
    project_overrides = project_config.get("permission-mode-overrides", {})
    if role in project_overrides:
        return str(project_overrides[role])
    roles_cfg = load_roles_config(agent_meta_root)
    return roles_cfg["roles"].get(role, {}).get("permission_mode", "")


def resolve_memory(role: str, project_config: dict, agent_meta_root: Path) -> str:
    """Resolve the memory scope for a role.

    Precedence (highest to lowest):
    0. memory.enabled == False → always return "" (master kill-switch, overrides all)
    1. Project override: project_config["memory-overrides"][role]
    2. Meta default:     roles.config.yaml roles[role].memory
    3. memory.default_scope if set (global fallback for roles with no memory config)
    4. Empty string:     no memory: field injected

    Backward compatible: if "memory" block is absent, enabled defaults to True.
    """
    # 0. Master kill-switch
    memory_cfg = project_config.get("memory", {})
    if not memory_cfg.get("enabled", True):
        return ""

    # 1. Project override (role-specific)
    project_overrides = project_config.get("memory-overrides", {})
    if role in project_overrides:
        return str(project_overrides[role])

    # 2. Meta default from role-defaults.yaml
    roles_cfg = load_roles_config(agent_meta_root)
    meta_default = roles_cfg["roles"].get(role, {}).get("memory", "")
    if meta_default:
        return meta_default

    # 3. Global default_scope
    default_scope = memory_cfg.get("default_scope", "")
    if default_scope:
        return str(default_scope)

    return ""


def resolve_temperature(role: str, project_config: dict, agent_meta_root: Path) -> str:
    """Resolve the temperature for a role.

    Precedence (highest to lowest):
    1. Project override: project_config["temperature-overrides"][role]
    2. Meta default:     role-defaults.yaml roles[role].temperature
    3. Empty string:     no temperature: field injected
    """
    project_overrides = project_config.get("temperature-overrides", {})
    if role in project_overrides:
        return str(project_overrides[role])
    roles_cfg = load_roles_config(agent_meta_root)
    return roles_cfg["roles"].get(role, {}).get("temperature", "")


def resolve_max_tokens(role: str, project_config: dict, agent_meta_root: Path) -> str:
    """Resolve the max_tokens for a role.

    Precedence (highest to lowest):
    1. Project override: project_config["max-tokens-overrides"][role]
    2. Meta default:     role-defaults.yaml roles[role].max_tokens
    3. Empty string:     no max_tokens: field injected
    """
    project_overrides = project_config.get("max-tokens-overrides", {})
    if role in project_overrides:
        return str(project_overrides[role])
    roles_cfg = load_roles_config(agent_meta_root)
    return str(roles_cfg["roles"].get(role, {}).get("max_tokens", "")) or ""


def resolve_steps(role: str, project_config: dict, agent_meta_root: Path) -> str:
    """Resolve the steps limit for a role.

    Precedence (highest to lowest):
    1. Project override: project_config["steps-overrides"][role]
    2. Meta default:     roles.config.yaml roles[role].steps
    3. Empty string:     no steps: field injected
    """
    project_overrides = project_config.get("steps-overrides", {})
    if role in project_overrides:
        return str(project_overrides[role])
    roles_cfg = load_roles_config(agent_meta_root)
    return roles_cfg["roles"].get(role, {}).get("steps", "")
