
with open('tests/test_tier_presets.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('CLAUDE_MODEL_BALANCED = "claude-sonnet-4-6"', 'CLAUDE_MODEL_BALANCED = "claude-sonnet-5"')

with open('tests/test_tier_presets.py', 'w', encoding='utf-8') as f:
    f.write(content)
