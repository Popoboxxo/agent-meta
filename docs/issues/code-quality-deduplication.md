---
title: "[code-quality] Extract duplicated code patterns into shared helpers"
labels: [code-quality, refactoring, P2]
---

## Summary
Multiple modules duplicate the same patterns: YAML import guards, legacy config fallback loading, and memory/permission injection.

## Duplicated Patterns

### Pattern 1: `try: import yaml` (4 files)
```python
# agents.py, config.py, platform.py, lifecycle_check.py
try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False
```
**Fix:** Import from `scripts/lib/io.py` which already handles this.

### Pattern 2: Legacy Config Fallback (5 files)
```python
# agents.py, rules.py, hooks.py, skills.py, dod.py
data, _ = _load_yaml_or_json(
    agent_meta_root / "config/modern.yaml",
    agent_meta_root / "config/legacy.yaml",
    agent_meta_root / "config/legacy.json",
)
```
**Fix:** Helper `load_config_with_fallback(base_path, *names)` in `io.py`.

### Pattern 3: Memory/Permission Injection (2 locations in agents.py)
```python
# agents.py:490 and agents.py:653
memory = resolve_memory(role, config, agent_meta_root)
content = inject_memory_field(content, memory)
```
**Fix:** `inject_agent_fields(content, role, config, agent_meta_root)` helper.

## Acceptance Criteria
- [ ] `try: import yaml` removed from all files except `io.py`
- [ ] `load_config_with_fallback()` added to `io.py`
- [ ] `inject_agent_fields()` added to `agents.py`
- [ ] No functional changes — pure refactoring
- [ ] sync.py dry-run produces identical output before/after

## Related
- `docs/reviews/framework-provider-review-2026-05-07.md` — Finding #9
