import re

with open('scripts/lib/config.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the imports
content = content.replace(
    "from .delegation_table import (\n        generate_agent_delegation_table,\n        generate_intent_routing_table,\n    )",
    "from .delegation_table import get_active_agents_data\n    from .context_templates.builder import TemplateBuilder\n"
)

# Replace AGENT_DELEGATION_TABLE assignment
# Since TemplateBuilder takes a template name, we'll build agents-table
content = re.sub(
    r'variables\["AGENT_DELEGATION_TABLE"\] = generate_agent_delegation_table\(agent_meta_root, config, variables\)',
    'variables["active_agents"] = get_active_agents_data(agent_meta_root, config, variables)\n    variables["AGENT_DELEGATION_TABLE"] = TemplateBuilder(agent_meta_root / "templates" / "context").resolve_partials("{{> agents-table }}").replace("{{> agents-table }}", "").strip()',
    content
)

# Wait, `resolve_partials` will just return the content of agents-table.md, then we need to resolve loops.
# Let's write a small inline render in config.py
replacement = '''
    variables["active_agents"] = get_active_agents_data(agent_meta_root, config, variables)
    _tb = TemplateBuilder(agent_meta_root / "templates" / "context")
    _table_tpl = _tb.resolve_partials("{{> agents-table }}")
    variables["AGENT_DELEGATION_TABLE"] = _tb.resolve_loops(_table_tpl, variables).strip()
'''
content = re.sub(
    r'variables\["AGENT_DELEGATION_TABLE"\] = .*',
    replacement,
    content
)

# Also delete INTENT_ROUTING_TABLE assignment if I delete generate_intent_routing_table
content = re.sub(
    r'variables\["INTENT_ROUTING_TABLE"\] = generate_intent_routing_table\(agent_meta_root, config, variables\)',
    'variables["INTENT_ROUTING_TABLE"] = ""',
    content
)

with open('scripts/lib/config.py', 'w', encoding='utf-8') as f:
    f.write(content)
