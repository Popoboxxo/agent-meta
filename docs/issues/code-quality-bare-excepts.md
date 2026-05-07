---
title: "[code-quality] Replace bare 'except Exception:' with specific exceptions"
labels: [code-quality, bug, P0]
---

## Summary
There are **7 occurrences** of bare `except Exception:` across the codebase. This silently swallows errors, making debugging extremely difficult and hiding real problems.

## Affected Locations

| File | Line | Context |
|------|------|---------|
| `scripts/lib/agents.py` | 205 | YAML parsing in `_wf_load_file` |
| `scripts/lib/agents.py` | 325 | PyYAML composition loading |
| `scripts/lib/config.py` | 218 | Schema loading fallback |
| `scripts/lib/skills.py` | 73 | Git subprocess call |
| `scripts/lib/platform.py` | 69 | YAML loading in platform config |
| `scripts/lib/lifecycle_check.py` | 138 | YAML loading |
| `scripts/lib/hooks.py` | 124 | *(already specific: JSONDecodeError + OSError)* |

## Example (Bad)
```python
try:
    data = _yaml.safe_load(f)
except Exception:
    pass
```

## Example (Good)
```python
try:
    data = _yaml.safe_load(f)
except (yaml.YAMLError, ImportError) as e:
    log.warn(f"YAML parse error in {path}: {e}")
```

## Acceptance Criteria
- [ ] All bare `except Exception:` replaced with specific exception types
- [ ] Each catch block logs the exception (not silently swallows)
- [ ] `scripts/lib/hooks.py:124` verified as already correct
- [ ] Regression test added to prevent new bare excepts

## Related
- `docs/reviews/framework-provider-review-2026-05-07.md` — Finding #2
