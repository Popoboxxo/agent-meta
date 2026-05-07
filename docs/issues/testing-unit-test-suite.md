---
title: "[testing] Add unit test suite for scripts/lib/ modules"
labels: [testing, ci-cd, P0]
---

## Summary
The entire `scripts/lib/` directory has **zero unit tests**. This means every change is a potential regression. There is no CI validation.

## Modules Requiring Tests

| Module | Priority | Test Focus |
|--------|----------|------------|
| `scripts/lib/config.py` | P0 | Config loading, validation, variable substitution |
| `scripts/lib/agents.py` | P0 | Frontmatter injection, composition, agent resolution |
| `scripts/lib/rules.py` | P0 | Rule precedence, platform override, speech-mode sync |
| `scripts/lib/hooks.py` | P1 | Hook registration, settings.json merge, stale cleanup |
| `scripts/lib/roles.py` | P1 | Model/memory/permission resolution, tier mapping |
| `scripts/lib/skills.py` | P1 | Skill loading, commit checks, path normalization |
| `scripts/lib/extensions.py` | P2 | Managed block rendering, extension creation |

## Suggested Structure
```
scripts/
  lib/
    tests/
      __init__.py
      conftest.py              # shared fixtures
      test_config.py
      test_agents.py
      test_rules.py
      test_hooks.py
      test_roles.py
      test_skills.py
      test_extensions.py
```

## Acceptance Criteria
- [ ] `pytest` runs green for all tests
- [ ] Test coverage > 70% for P0 modules
- [ ] GitHub Actions workflow added (`.github/workflows/test.yml`)
- [ ] `README.md` updated with "How to run tests" section

## Related
- `docs/reviews/framework-provider-review-2026-05-07.md` — Finding #3
