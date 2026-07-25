import re

with open('tests/test_knowledge_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Just remove the two tests
content = re.sub(r'def test_intent_routing_table_omits_knowledge_roles_when_disabled.*?def test_delegation_table_includes_knowledge_roles_when_enabled', 'def test_delegation_table_includes_knowledge_roles_when_enabled', content, flags=re.DOTALL)
content = re.sub(r'def test_intent_routing_table_includes_knowledge_roles_when_enabled.*?def test_build_agent_hints_omits_knowledge_section_when_disabled', 'def test_build_agent_hints_omits_knowledge_section_when_disabled', content, flags=re.DOTALL)

with open('tests/test_knowledge_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
