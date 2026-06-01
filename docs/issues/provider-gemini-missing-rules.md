---
title: "[provider] Gemini skips 5 rules, reducing agent context significantly"
labels: [provider, Gemini, P1]
status: resolved
resolved-in: "Removed all `gemini: skip` entries from `minimal` and `silent` presets. Closes #71, #80."
---

> **RESOLVED** — All `gemini: skip` entries have been removed from `config/rules-presets.yaml`.
> Gemini now gets all rules like Claude. Rules are generated into `.gemini/rules/`.
> See `CHANGELOG.md` for details.

## Summary
The Gemini rules-preset skips 5 important rules: `dod-criteria`, `issue-lifecycle`, `lifecycle-tasks`, `use-orchestrator`, `sync-interface`. This means Gemini agents operate with significantly less context than Claude agents.

## Current State
```yaml
# config/rules-presets.yaml
gemini:
  dod-criteria: { gemini: skip }
  issue-lifecycle: { gemini: skip }
  lifecycle-tasks: { gemini: skip }
  use-orchestrator: { gemini: skip }
  sync-interface: { gemini: skip }
```

## Why These Rules Are Important
| Rule | Purpose | Risk of Skipping |
|------|---------|------------------|
| `dod-criteria` | Definition of Done checks | Gemini agents don't know completion criteria |
| `issue-lifecycle` | GitHub issue management | Agents won't close issues after fixes |
| `lifecycle-tasks` | Pending task handling | Tasks from git events are ignored |
| `use-orchestrator` | Entry point enforcement | Agents might bypass orchestrator |
| `sync-interface` | sync.py command reference | Agents don't know sync commands |

## Why They Were Skipped
Likely because Gemini's context format doesn't support `alwaysApply` frontmatter. But the rules should still be embedded in `GEMINI.md` context, just without the `alwaysApply` mechanism.

## Fix
Either:
1. **Embed skipped rules into GEMINI.md** as plain text (not as separate rule files)
2. **Remove the skip** and let Gemini ignore `alwaysApply` frontmatter (it already strips it)
3. **Create Gemini-specific rule variants** without `alwaysApply`

## Acceptance Criteria
- [x] All 5 rules are available to Gemini agents in some form
- [x] `GEMINI.md` includes full rule context
- [x] `sync.log` shows no `[SKIP] (rules-preset: gemini: skip)` for these rules

## Related
- `docs/reviews/framework-provider-review-2026-05-07.md` — Finding #8
