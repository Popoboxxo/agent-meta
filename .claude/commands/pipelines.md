---
description: Show all quality pipelines — active/disabled status, stages, and source (default/override/custom)
allowed-tools: ["Read", "Bash"]
argument-hint: "[pipeline-name to show details]"
---

Show available quality pipelines for this project. $ARGUMENTS

## Step 1 — Load pipeline configuration

Read both sources:
1. `config/role-defaults.yaml` → `quality_pipelines:` section (base pipelines)
2. `.meta-config/project.yaml` → `quality-pipelines:` section (overrides + custom-pipelines)

Parse them with Python (use Bash tool):
```bash
python -c "
import yaml, os, sys

def load_yaml(path):
    if not os.path.exists(path): return {}
    with open(path, encoding='utf-8') as f: return yaml.safe_load(f) or {}

base = load_yaml('config/role-defaults.yaml').get('quality_pipelines', {})
project = load_yaml('.meta-config/project.yaml').get('quality-pipelines', {})

overrides = project.get('overrides', {})
custom = project.get('custom-pipelines', {})

# Build effective pipeline list
result = dict(base)
disabled = []
for name, ov in overrides.items():
    if ov.get('enabled') is False:
        result.pop(name, None)
        disabled.append(name)
    elif name in result:
        result[name] = {**result[name], **ov}
    else:
        result[name] = ov
for name, cp in custom.items():
    result[name] = cp

# Determine source for each
def source(name):
    if name in custom: return 'custom'
    if name in overrides and overrides[name].get('enabled') is not False: return 'override'
    return 'default'

print('ACTIVE:')
for name, p in result.items():
    stages = p.get('stages', [])
    stage_seq = ' → '.join(s.get('id','?') + '(' + s.get('agent','?') + ')' for s in stages)
    desc = p.get('description', '')
    src = source(name)
    print(f'  [{src}] {name}: {desc}')
    print(f'    Stages: {stage_seq}')
    on_err = p.get('on_error', '')
    if on_err: print(f'    on_error: {on_err}')

if disabled:
    print()
    print('DISABLED (by project override):')
    for name in disabled:
        print(f'  - {name}')
"
```

## Step 2 — Filter by argument (if provided)

If $ARGUMENTS is non-empty, filter to show only the pipeline matching that name. If not found, report "Pipeline '$ARGUMENTS' not found" and list available names.

## Step 3 — Display

Format the output as a compact table for overview, with details below:

**Quality Pipelines — Project: [project name from .meta-config/project.yaml]**

| Pipeline | Status | Source | Description |
|----------|--------|--------|-------------|
| standard-feature | ACTIVE | default | Full feature lifecycle... |
| quick-fix | ACTIVE | default | Schneller Bugfix... |
| ... | ... | ... | ... |

Then for each ACTIVE pipeline, show stage sequence:
`[stage-id (agent, mode)] → [stage-id (agent, mode)] → ...`

If a pipeline is disabled, show it in a "Disabled" section at the bottom.

**Tip:** Run `/pipelines <name>` for full details on a specific pipeline.

## Step 4 — If specific pipeline requested

Show full detail:
- Name, description, source
- All stages with id, agent, mode, task text
- Loop details (generator, critic, max_iterations) if mode=loop
- on_error strategy
- Whether it's overridden by project config and how
