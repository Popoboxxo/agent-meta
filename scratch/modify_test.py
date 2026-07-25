import re

with open('tests/test_knowledge_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("from scripts.lib.delegation_table import generate_agent_delegation_table, generate_intent_routing_table", "from scripts.lib.delegation_table import get_active_agents_data")
content = content.replace("table = generate_agent_delegation_table(", "table = get_active_agents_data(")
content = content.replace("assert \"knowledge-curator\" not in table", "assert \"knowledge-curator\" not in [a['name'] for a in table]")
content = content.replace("assert \"knowledge-migrator\" not in table", "assert \"knowledge-migrator\" not in [a['name'] for a in table]")
content = content.replace("assert role in table", "assert role in [a['name'] for a in table]")

with open('tests/test_knowledge_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
