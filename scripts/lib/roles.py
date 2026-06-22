"""Roles config loading and model/memory/permissionMode resolution."""

from pathlib import Path
from typing import TYPE_CHECKING

from .io import _load_yaml_or_json

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

def load_tier_presets(agent_meta_root: Path) -> dict:
    presets_path = agent_meta_root / "config" / "tier-presets.yaml"
    data, _ = _load_yaml_or_json(presets_path)
    return data or {}

def _upgrade_tier(tier: str, steps: int) -> str:
    if tier not in _TIER_SEQUENCE:
        return tier
    idx = _TIER_SEQUENCE.index(tier)
    new_idx = min(len(_TIER_SEQUENCE) - 1, idx + steps)
    return _TIER_SEQUENCE[new_idx]


def load_roles_config(agent_meta_root: Path) -> dict:
    """Load config/role-defaults.yaml with fallback to legacy paths."""
    data, _ = _load_yaml_or_json(
        agent_meta_root / ROLES_CONFIG,
        agent_meta_root / _ROLES_CONFIG_LEGACY,
        agent_meta_root / _ROLES_CONFIG_JSON,
    )
    if not data:
        return {"roles": {}}
    return {"roles": {k: v for k, v in data.get("roles", {}).items() if not k.startswith("_")}}


def build_role_map(agent_meta_root: Path) -> dict[str, str]:
    """Build ROLE_MAP dynamically from roles.config.yaml.

    Returns a dict mapping role name → role name (identity mapping).
    All roles listed in roles.config.yaml are included.
    """
    roles_cfg = load_roles_config(agent_meta_root)
    return {role: role for role in roles_cfg["roles"]}


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
    log: "SyncLog" | None = None,
) -> str:
    """Resolve the model ID for a role and provider using tier presets and registry."""
    pc = provider_config or {}

    tier_or_id = ""
    explicit_override = False

    # 1. Provider-specific project override
    provider_overrides = project_config.get("model-overrides", {})
    provider_specific = provider_overrides.get(provider, {})
    if isinstance(provider_specific, dict) and role in provider_specific:
        tier_or_id = str(provider_specific[role])
        explicit_override = True
        if log:
            log.debug(f"{provider}/{role}", f"Model explicitly overriden for provider '{provider}': {tier_or_id}")
    elif isinstance(provider_overrides, dict) and role in provider_overrides:
        flat_value = provider_overrides[role]
        if not isinstance(flat_value, dict):
            if provider == "Claude":
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
        resolved = _resolve_tier_to_model(tier_or_id, provider, pc)
        if log:
            log.debug(f"{provider}/{role}", f"Tier '{tier_or_id}' resolved directly to: {resolved}")
        return resolved

    base_tier = tier_or_id

    # 3. Apply SE Focus and Presets
    preset_name = project_config.get("tier-preset", "Normal")
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
        preset_matrix = project_presets[preset_name].get("mapping", {}) or {}
        if log:
            log.debug(f"{provider}/{role}", f"Preset '{preset_name}' resolved from project-local tier-presets")
    elif preset_name in global_presets:
        preset_matrix = global_presets.get(preset_name, {}).get("mapping", {}) or {}
    else:
        preset_matrix = {}

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
    resolved = _resolve_tier_to_model(mapped_tier, provider, pc)
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
