"""Roles config loading and model/memory/permissionMode resolution."""

from pathlib import Path

from .io import _load_yaml_or_json

ROLES_CONFIG = "config/role-defaults.yaml"
_ROLES_CONFIG_LEGACY = "roles.config.yaml"
_ROLES_CONFIG_JSON = "roles.config.json"  # legacy fallback

# Abstract tier names defined in role-defaults.yaml
_KNOWN_TIERS = {"nano", "fast", "balanced", "powerful", "max"}
# Legacy Claude aliases — resolved only when no provider context is available
_CLAUDE_ALIASES = {"haiku", "sonnet", "opus"}


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
) -> str:
    """Resolve the model ID for a role and provider.

    Precedence (highest to lowest):
    1. Provider-specific project override: project_config["model-overrides"][<provider>][role]
    2. Legacy flat project override:       project_config["model-overrides"][role]
       (treated as Claude-only when provider != Claude)
    3. Meta default from role-defaults.yaml (tier name → provider model ID)
    4. Empty string → no model: field injected (agent inherits from parent context)

    Tier resolution:
    - nano/fast/balanced/powerful/max → looked up in ai-providers.yaml model-tiers[provider]
    - haiku/sonnet/opus → legacy aliases, mapped via model-aliases or tier fallback
    - Full model IDs (claude-*, gemini-*) → passed through unchanged
    """
    pc = provider_config or {}

    # 1. Provider-specific project override
    provider_overrides = project_config.get("model-overrides", {})
    provider_specific = provider_overrides.get(provider, {})
    if isinstance(provider_specific, dict) and role in provider_specific:
        tier_or_id = str(provider_specific[role])
        return _resolve_tier_to_model(tier_or_id, provider, pc)

    # 2. Legacy flat override (only applied to Claude; for other providers skip)
    if isinstance(provider_overrides, dict) and role in provider_overrides:
        flat_value = provider_overrides[role]
        if not isinstance(flat_value, dict):
            tier_or_id = str(flat_value)
            if provider == "Claude":
                return _resolve_tier_to_model(tier_or_id, provider, pc)
            # For non-Claude providers: flat override is Claude-specific — skip it,
            # fall through to meta default so Gemini gets correct model

    # 3. Meta default from role-defaults.yaml
    roles_cfg = load_roles_config(agent_meta_root)
    tier_or_id = roles_cfg["roles"].get(role, {}).get("model", "")
    return _resolve_tier_to_model(tier_or_id, provider, pc)


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
    1. Project override: project_config["memory-overrides"][role]
    2. Meta default:     roles.config.yaml roles[role].memory
    3. Empty string:     no memory: field injected
    """
    project_overrides = project_config.get("memory-overrides", {})
    if role in project_overrides:
        return str(project_overrides[role])
    roles_cfg = load_roles_config(agent_meta_root)
    return roles_cfg["roles"].get(role, {}).get("memory", "")
