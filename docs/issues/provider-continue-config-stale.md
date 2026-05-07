---
title: "[provider] Continue provider config.yaml never updates after first sync"
labels: [provider, Continue, bug, P1]
---

## Summary
The Continue provider's `config.yaml` is created once and then skipped on subsequent syncs with `[SKIP] .continue/config.yaml (already exists - not overwritten)`. This means configuration updates (new agents, rules, models) are never propagated to Continue.

## Affected Code
```python
# scripts/lib/context.py ~line 420
if target_path.exists():
    log.skip(..., "already exists - not overwritten")
    continue
```

## Impact
- Continue users don't get agent updates
- Rules never update in Continue context
- New agents are invisible to Continue

## Fix Options

### Option A: Managed Block for Continue Config
Wrap Continue config in managed blocks like `CLAUDE.md`:
```yaml
# agent-meta:managed-begin
# agent-meta:managed-end
```

### Option B: Overwrite Flag
Add provider option:
```yaml
provider-options:
  Continue:
    overwrite-config: true
```

### Option C: Separate Config Parts
Split into `config.yaml` (user-owned) and `config.agent-meta.yaml` (generated), with include.

## Acceptance Criteria
- [ ] Continue config updates on subsequent syncs
- [ ] User customizations in `config.yaml` are preserved
- [ ] Documented in `docs/providers/continue.md`

## Related
- `docs/reviews/framework-provider-review-2026-05-07.md` — Finding #6
