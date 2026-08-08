---
title: "[documentation] Add API documentation for scripts/lib/ modules"
labels: [documentation, P2]
---

## Summary
The `scripts/lib/` modules are undocumented except for inline docstrings. There is no high-level API reference for contributors or users who want to extend agent-meta.

## Missing Documentation

| Module | Purpose | Audience |
|--------|---------|----------|
| `scripts/lib/config.py` | Config loading, validation, variable substitution | Contributors |
| `scripts/lib/agents.py` | Agent file generation, composition, frontmatter | Contributors |
| `scripts/lib/rules.py` | Rule collection, precedence, speech-mode | Contributors |
| `scripts/lib/hooks.py` | Hook script sync, settings.json merge | Contributors |
| `scripts/lib/roles.py` | Model/memory/permission resolution | Contributors |
| `scripts/lib/skills.py` | External skill loading, submodule checks | Contributors |
| `scripts/lib/context.py` | Provider-specific context generation | Contributors |
| `scripts/lib/extensions.py` | Managed block rendering | Contributors |

## Proposed Structure
```
docs/
  architecture/
    sync-flow.md          # already exists
    api-reference.md      # NEW: module-by-module API docs
    provider-matrix.md    # NEW: feature comparison table
```

## Acceptance Criteria
- [ ] `docs/architecture/api-reference.md` created with all public functions
- [ ] `docs/architecture/provider-matrix.md` created with feature comparison
- [ ] Each function documented with: signature, parameters, return value, example
- [ ] Cross-references to `howto/` guides where applicable

