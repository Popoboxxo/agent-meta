---
description: Show all quality pipelines — active/disabled status, stages, and source (default/override/custom)
allowed-tools: ["Bash"]
argument-hint: "[pipeline-name to show details]"
---

Show available quality pipelines for this project. $ARGUMENTS

## Step 1 — Load and merge pipeline configuration

Run the following Python snippet to load base pipelines and apply project overrides using the agent-meta library:

```bash
python -c "
import sys, os, io

# Fix Unicode output on Windows consoles (cp1252 cannot encode U+2192 etc.)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Resolve repo root relative to this script's location
cwd = os.getcwd()

# Add agent-meta scripts to path so we can reuse the tested library
scripts_path = os.path.join(cwd, 'scripts')
if os.path.isdir(scripts_path):
    sys.path.insert(0, scripts_path)

try:
    from lib.pipelines import load_quality_pipelines, load_pipeline_overrides, apply_overrides
    LIB_AVAILABLE = True
except ImportError:
    LIB_AVAILABLE = False

if LIB_AVAILABLE:
    base = load_quality_pipelines(cwd)
    raw_overrides = load_pipeline_overrides(os.path.join(cwd, '.meta-config', 'project.yaml'))
    pipelines = apply_overrides(base, raw_overrides)

    # Determine sources for display
    explicit_overrides = raw_overrides.get('overrides', {})
    custom_pipelines = raw_overrides.get('custom-pipelines', {})

    disabled = []
    for name, ov in explicit_overrides.items():
        if ov.get('enabled') is False:
            disabled.append(name)

    def source(name):
        if name in custom_pipelines:
            return 'custom'
        if name in explicit_overrides and explicit_overrides[name].get('enabled') is not False:
            return 'override'
        return 'default'

else:
    # Fallback: inline YAML loading without lib
    try:
        import yaml
    except ImportError:
        print('ERROR: PyYAML not available. Run: pip install pyyaml')
        sys.exit(1)

    def load_yaml(path):
        if not os.path.exists(path): return {}
        with open(path, encoding='utf-8') as f: return yaml.safe_load(f) or {}

    base = load_yaml('config/role-defaults.yaml').get('quality_pipelines', {})
    project = load_yaml('.meta-config/project.yaml').get('quality-pipelines', {})
    explicit_overrides = project.get('overrides', {})
    custom_pipelines = project.get('custom-pipelines', {})

    disabled = []
    pipelines = dict(base)
    for name, ov in explicit_overrides.items():
        if ov.get('enabled') is False:
            pipelines.pop(name, None)
            disabled.append(name)
            continue
        if name in pipelines:
            merged = dict(pipelines[name])
            base_stages = pipelines[name].get('stages', [])
            ov_stages = ov.get('stages')
            merged.update({k: v for k, v in ov.items() if k != 'stages'})
            if ov_stages is not None:
                if isinstance(ov_stages, list):
                    merged['stages'] = ov_stages
                elif isinstance(ov_stages, dict):
                    base_by_id = {s['id']: dict(s) for s in base_stages if isinstance(s, dict)}
                    for sid, sov in ov_stages.items():
                        if sid in base_by_id:
                            base_by_id[sid].update(sov if isinstance(sov, dict) else {})
                        else:
                            base_by_id[sid] = sov if isinstance(sov, dict) else {'id': sid}
                    merged['stages'] = list(base_by_id.values())
            pipelines[name] = merged
        else:
            pipelines[name] = ov
    for name, cp in custom_pipelines.items():
        pipelines[name] = cp

    def source(name):
        if name in custom_pipelines: return 'custom'
        if name in explicit_overrides and explicit_overrides[name].get('enabled') is not False: return 'override'
        return 'default'

# Display
def stage_summary(stages):
    if not isinstance(stages, list):
        return '(no stages)'
    parts = []
    for s in stages:
        if not isinstance(s, dict):
            continue
        sid = s.get('id', '?')
        agent = s.get('agent', '?')
        mode = s.get('mode', 'sequential')
        if mode == 'loop':
            loop = s.get('loop', {})
            gen = loop.get('generator', agent)
            crit = loop.get('critic', '')
            max_i = loop.get('max_iterations', '?')
            parts.append(f'{sid}(loop:{gen}/{crit},max={max_i})')
        else:
            parts.append(f'{sid}({agent})')
    return ' -> '.join(parts)

print('ACTIVE PIPELINES:')
for name, p in pipelines.items():
    stages = p.get('stages', [])
    desc = p.get('description', '')
    src = source(name)
    print(f'  [{src}] {name}: {desc}')
    print(f'    Stages: {stage_summary(stages)}')
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

If `$ARGUMENTS` is non-empty, re-run the snippet above and filter output to show only the pipeline matching that name. If not found, report "Pipeline '$ARGUMENTS' not found" and list available names.

## Step 3 — Format output as table

Present results as:

**Quality Pipelines**

| Pipeline | Status | Source | Description |
|----------|--------|--------|-------------|
| name | ACTIVE | default/override/custom | description |

Then for each ACTIVE pipeline show the stage sequence:
`stage-id(agent) -> stage-id(agent) -> ...`

For loop stages: `stage-id(loop:generator/critic, max=N)`

Disabled pipelines appear in a separate "Disabled" section.

**Tip:** Run `/pipelines <name>` for full details on a specific pipeline.

## Step 4 — If specific pipeline requested

Show full detail for the requested pipeline:
- Name, description, source (default / override / custom)
- All stages with id, agent, mode, task text
- Loop details (generator, critic, max_iterations) if mode=loop
- on_error strategy
- Whether and how it is overridden by project config
