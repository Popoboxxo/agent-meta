---
description: Show all quality pipelines — active/disabled status, stages, and source (default/override/custom)
allowed-tools: ["Bash"]
argument-hint: "[pipeline-name to show details]"
---

Show available quality pipelines for this project. $ARGUMENTS

Run this Python snippet from `scripts/lib/pipelines.py`:

```bash
python - <<'PY'
import os, sys
sys.path.insert(0, 'scripts')
from lib.pipelines import load_quality_pipelines, load_pipeline_overrides, apply_overrides
root = os.getcwd()
pipelines = apply_overrides(load_quality_pipelines(root), load_pipeline_overrides(os.path.join(root, '.meta-config', 'project.yaml')))
for n, p in pipelines.items():
    print(f"{n}: {' -> '.join(s.get('id', '?') for s in p.get('stages', []))}")
PY
```

If $ARGUMENTS is provided, filter to the matching pipeline. Present results as:

| Pipeline | Status | Source | Description |
|----------|--------|--------|-------------|
| name | ACTIVE | default/override/custom | description |

List disabled pipelines separately.
