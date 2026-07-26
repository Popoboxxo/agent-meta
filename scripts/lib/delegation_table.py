from pathlib import Path
from .roles import load_roles_config

def get_active_agents_data(agent_meta_root: Path, config: dict, variables: dict) -> list[dict]:
    """Return a list of dictionaries with agent data.

    Reads roles from config/role-defaults.yaml and respects workflow_tier and feature flags.
    Returns: list of dicts with 'name' and 'short_desc'.
    """
    roles_cfg = load_roles_config(agent_meta_root)
    roles = roles_cfg.get("roles", {})

    roles_list = config.get("roles")
    active_roles = set(roles_list) if roles_list is not None else None

    se_enabled = variables.get("SE_ENABLED", "false") == "true"
    validator_enabled = variables.get("VALIDATOR_ENABLED", "false") == "true"
    knowledge_enabled = variables.get("KNOWLEDGE_ENGINE_ENABLED", "false") == "true"
    developer_tiers = variables.get("DEVELOPER_TIERS_ENABLED", "false") == "true"

    active_agents_data = []

    for role_name in sorted(roles.keys()):
        if role_name.startswith("se-") and not se_enabled:
            continue
        if role_name == "validator" and not validator_enabled:
            continue
        if role_name.startswith("knowledge-") and not knowledge_enabled:
            continue
        if role_name in ("junior-developer", "senior-developer", "principal-developer") and not developer_tiers:
            continue

        role_info = roles[role_name]
        tier = role_info.get("workflow_tier", "optional")

        if tier == "optional" and active_roles is not None and role_name not in active_roles:
            continue

        desc = role_info.get("short_desc", role_info.get("description", ""))
        active_agents_data.append({
            "name": role_name,
            "short_desc": desc
        })

    return active_agents_data


def get_intent_routing_table(agent_meta_root: Path, config: dict, variables: dict) -> str:
    """Generate the INTENT_ROUTING_TABLE from active roles."""
    roles_cfg = load_roles_config(agent_meta_root)
    roles = roles_cfg.get("roles", {})
    active_agents_data = get_active_agents_data(agent_meta_root, config, variables)
    active_agent_names = {agent["name"] for agent in active_agents_data}

    table_lines = [
        "| Intent / Keywords | Agent | Tier | Parallel |",
        "|-------------------|-------|------|----------|"
    ]

    has_entries = False
    for role_name in sorted(roles.keys()):
        if role_name not in active_agent_names:
            continue
        
        role_info = roles[role_name]
        routing = role_info.get("routing", {})
        intent_keywords = routing.get("intent_keywords", [])
        
        if not intent_keywords:
            continue
            
        tier = role_info.get("workflow_tier", "optional")
        parallel = "yes" if routing.get("parallel", False) else "no"
        
        keywords_str = ", ".join(intent_keywords)
        table_lines.append(f"| {keywords_str} | `{role_name}` | {tier} | {parallel} |")
        has_entries = True

    if not has_entries:
        return ""

    return "\n".join(table_lines) + "\n"
