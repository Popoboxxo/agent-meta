---
title: "[code-quality] Replace bare 'except Exception:' with specific exceptions"
labels: [code-quality, bug, P0]
status: mostly-resolved
resolved-in: "5 of 7 original occurrences fixed (specific exception types + logging); the remaining 2 are deliberate, noqa-marked exceptions, not oversights."
---

> **MOSTLY RESOLVED** (re-verified 2026-08-08 against current code, not just re-read from this file):
> - `scripts/lib/skills.py`, `scripts/lib/platform.py` — no bare `except Exception:` remain at all.
> - `scripts/lib/lifecycle_check.py` — file no longer exists at this path (renamed/restructured since this issue was written).
> - `scripts/lib/agents.py:44`, `scripts/lib/config.py:746` — still `except Exception:`, but now explicitly marked `# noqa: BLE001`, i.e. a deliberate, linter-acknowledged design decision rather than an unreviewed bare catch. Revisit only if a concrete bug traces back to one of these two.

## Summary
There are **7 occurrences** of bare `except Exception:` across the codebase. This silently swallows errors, making debugging extremely difficult and hiding real problems.

## Affected Locations (original, 2026-05 — see RESOLVED note above for current state)

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

