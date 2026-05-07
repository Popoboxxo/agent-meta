---
title: "[security] Path Traversal in sync.py — generated paths not validated against project root"
labels: [security, sync.py, P0]
---

## Summary
`sync.py` and `agents.py` construct target file paths by concatenating user-controlled config values (`project.prefix`, role names) with fixed directory names. There is no validation that the resulting path stays within the project root.

## Risk
If a malicious or misconfigured `project.yaml` contains `prefix: "../../evil"`, sync.py will write files outside the project directory.

## Affected Code
```python
# agents.py ~line 430
target_path = target_dir / f"{prefix}-{role}.md"

# sync.py ~line 360
target_path = project_root / ".claude/rules/" / rule_name
```

## Reproduction
1. Set `project.prefix: "../../tmp/pwn"` in `.meta-config/project.yaml`
2. Run `python scripts/sync.py`
3. Observe files written to `/tmp/pwn-*.md`

## Fix
Add a `safe_path()` helper:
```python
def safe_path(base: Path, *parts: str) -> Path:
    path = base.joinpath(*parts).resolve()
    if not str(path).startswith(str(base.resolve())):
        raise ValueError(f"Path traversal detected: {path}")
    return path
```

## Acceptance Criteria
- [ ] `safe_path()` helper added to `scripts/lib/io.py`
- [ ] All file write operations in `sync.py`, `agents.py`, `rules.py`, `hooks.py` use `safe_path()`
- [ ] Unit test verifies path traversal is blocked

## Related
- `docs/reviews/framework-provider-review-2026-05-07.md` — Finding #1
