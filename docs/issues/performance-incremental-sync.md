---
title: "[performance] Implement incremental sync using mtime checks"
labels: [performance, sync.py, P1]
---

## Summary
`sync.py` reads and writes ALL files on every run, even if source files haven't changed. For large projects this is slow.

## Current Behavior
```
[WRITE] .claude/agents/agent-meta-manager.md
[WRITE] .claude/agents/agent-meta-scout.md
[WRITE] .claude/agents/developer.md
... (all 48 agent files every time)
```

## Proposed Solution
Add `mtime` comparison before write:
```python
def _needs_update(source: Path, target: Path) -> bool:
    if not target.exists():
        return True
    return source.stat().st_mtime > target.stat().st_mtime
```

For composed agents (1-generic + 2-platform), check ALL source mtimes.

## Edge Cases
- Agent template changed but `role-defaults.yaml` didn't → must still regenerate
- Variables in config changed → must regenerate even if templates unchanged
- Platform rules changed → must regenerate affected agents

## Fix
Track a "generation fingerprint" (hash of all inputs) per file:
```python
# In .agent-meta-managed or separate fingerprint file
# agent-meta-fingerprint.json
{
  ".claude/agents/developer.md": {
    "hash": "sha256:abc123...",
    "sources": ["agents/1-generic/developer.md", "agents/2-platform/agent-meta-developer.md"]
  }
}
```

## Acceptance Criteria
- [ ] Only changed files are written on subsequent syncs
- [ ] First sync after variable change still regenerates
- [ ] `--force` flag added to override incremental behavior
- [ ] `sync.log` shows `[SKIP] (unchanged)` for skipped files

