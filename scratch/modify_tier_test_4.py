
with open('tests/test_tier_presets.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('_resolve("developer", "Normal (SE)")', '_resolve("senior-developer", "Normal (SE)")')

with open('tests/test_tier_presets.py', 'w', encoding='utf-8') as f:
    f.write(content)
