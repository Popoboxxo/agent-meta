import re

with open('scripts/lib/context.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the call to _build_opencode_managed_block
content = content.replace(
    "_build_opencode_managed_block(",
    "_build_managed_block("
)

start_idx = content.find("def _condense_rule_content(")
if start_idx == -1:
    print("Could not find _condense_rule_content")

end_idx = content.find("def init_claude_personal(", start_idx)
if end_idx == -1:
    print("Could not find init_claude_personal")

new_functions = '''def _build_managed_block(
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    provider: str,
    provider_config: dict | None = None,
) -> str:
    from .context_templates.builder import TemplateBuilder
    from .delegation_table import get_active_agents_data
    from .rules import collect_rule_sources, resolve_rules
    
    pc = (provider_config or {}).get(provider, {})
    has_native_rules = pc.get("has_rules", False)
    
    provider_dirs = {
        "Claude": ".claude/agents",
        "Opencode": ".opencode/agents",
        "Gemini": ".gemini/agents",
        "Continue": ".continue/agents",
        "Copilot": ".github/copilot/agents",
        "Mammouth": ".mammouth/agents",
    }
    
    local_vars = dict(variables)
    local_vars["AGENTS_DIR"] = provider_dirs.get(provider, ".local/agents")
    local_vars["HAS_NATIVE_RULES"] = has_native_rules
    local_vars[f"PLATFORM_{provider.upper()}"] = True
    
    local_vars["active_agents"] = get_active_agents_data(agent_meta_root, config, local_vars)
    
    if not has_native_rules:
        rule_options = resolve_rules(config, agent_meta_root)
        platforms = config.get("platforms", [])
        rule_sources = collect_rule_sources(agent_meta_root, platforms)
        
        embedded_rules = []
        for src_path, _ in rule_sources:
            rule_stem = src_path.stem
            opts = rule_options.get(rule_stem, {})
            prov_opt = opts.get(provider.lower())
            if prov_opt == "skip" or prov_opt is False:
                continue
            if opts.get("embed") is False:
                continue
                
            rule_content = src_path.read_text(encoding="utf-8")
            embedded_rules.append({"content": rule_content})
            
        local_vars["embedded_rules"] = embedded_rules

    builder = TemplateBuilder(agent_meta_root / "templates" / "context")
    return builder.build("agents-managed", local_vars)

'''

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_functions + content[end_idx:]
    with open('scripts/lib/context.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced successfully.")
else:
    print("Replacement failed.")
