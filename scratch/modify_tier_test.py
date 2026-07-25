import re

with open('tests/test_tier_presets.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace developer with senior-developer where it matters
content = content.replace('_resolve("developer", "Normal")', '_resolve("senior-developer", "Normal")')
content = content.replace('maps developer (powerful)', 'maps senior-developer (powerful)')
content = content.replace('role="developer",', 'role="senior-developer",')

with open('tests/test_tier_presets.py', 'w', encoding='utf-8') as f:
    f.write(content)
