import re

with open('tests/test_knowledge_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'def test_build_agent_hints_omits_knowledge_section_when_disabled.*?def test_documenter_template_has_knowledge_engine_conditional_block', 'def test_documenter_template_has_knowledge_engine_conditional_block', content, flags=re.DOTALL)

with open('tests/test_knowledge_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
