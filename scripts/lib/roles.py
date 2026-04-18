"""Roles config loading and model/memory/permissionMode resolution."""

from pathlib import Path

from .io import _load_yaml_or_json

ROLES_CONFIG = "config/role-defaults.yaml"
_ROLES_CONFIG_LEGACY = "roles.config.yaml"
_ROLES_CONFIG_JSON = "roles.config.json"  # legacy fallback


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


def resolve_model(role: str, project_config: dict, agent_meta_root: Path) -> str:
    """Resolve the model for a role.

    Precedence (highest to lowest):
    1. Project override: project_config["model-overrides"][role]
    2. Meta default:     roles.config.yaml roles[role].model
    3. Empty string:     no model: field injected (agent inherits from parent)
    """
    project_overrides = project_config.get("model-overrides", {})
    if role in project_overrides:
        return str(project_overrides[role])
    roles_cfg = load_roles_config(agent_meta_root)
    return roles_cfg["roles"].get(role, {}).get("model", "")


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
