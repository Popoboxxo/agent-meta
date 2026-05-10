---
description: Toggle visualization mode and trigger sync
allowed-tools: ["Bash"]
argument-hint: "[off | static | dynamic | full]"
---

Toggle the visualization mode in `.meta-config/project.yaml` and run a sync.

**Usage:**
- No arguments → cycles through modes: off → static → dynamic → full → off
- Argument provided → sets the specified mode directly

```bash
python -c "
import sys, subprocess, re

MODES = ['off', 'static', 'dynamic', 'full']
config_path = '.meta-config/project.yaml'

try:
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
except FileNotFoundError:
    print(f'  !  Config not found: {config_path}', file=sys.stderr)
    sys.exit(1)

# Determine current mode
current = 'off'
if 'viz:' in content:
    m = re.search(r'mode:\s*\"([^\"]+)\"', content)
    if m:
        current = m.group(1)
    elif 'enabled: true' in content.split('viz:')[1].split('\n')[0] if 'viz:' in content else False:
        current = 'static'  # legacy: enabled without mode

if len(sys.argv) > 1 and sys.argv[1]:
    target = sys.argv[1]
    if target not in MODES:
        print(f'  !  Unknown mode: {target}. Valid: {', '.join(MODES)}', file=sys.stderr)
        sys.exit(1)
else:
    # Cycle to next mode
    idx = MODES.index(current) if current in MODES else 0
    target = MODES[(idx + 1) % len(MODES)]

# Update or insert viz block
viz_block = f'''viz:
  enabled: {str(target != 'off').lower()}
  mode: \"{target}\"
  event_log: \".meta-viz/events.jsonl\"
  report:
    retention_days: 7
    session_timeout_min: 5'''

if 'viz:' in content:
    # Replace existing viz block (from 'viz:' to next top-level key or end)
    pattern = r'(viz:.*?)(?=\n\n[^#\s]|\Z)'
    content = re.sub(pattern, viz_block, content, count=1, flags=re.DOTALL)
else:
    # Append before last newline or at end
    content = content.rstrip() + '\n\n' + viz_block + '\n'

with open(config_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'  i  viz mode: {current} -> {target}')
" $ARGUMENTS

# Run sync
echo "  i  Running sync..."
python .agent-meta/scripts/sync.py
