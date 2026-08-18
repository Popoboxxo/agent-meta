---
name: new-block-placeholder-coupling
description: Adding a new _BLOCK placeholder to build_variables requires two easy-to-miss sibling edits (validator allowlist + standalone fallback)
metadata:
  type: project
---

A new `*_BLOCK` variable computed in `scripts/lib/config.py::build_variables()` (and referenced by a `1-generic/*.md` template) has two non-obvious sibling touchpoints beyond the CLAUDE.md/CODEBASE_OVERVIEW variable table:

1. `scripts/lib/consistency/placeholders.py` `_BUILTIN_VARS` — must list the new name, or `sync.py --validate` emits `[WRN] placeholders.unknown` for the template that references it.
2. `scripts/lib/standalone.py` `_standalone_variables()` — standalone renders ALL 1-generic roles; an unprovided placeholder degrades to a `[NAME — not available...]` safety-net note (not a crash). Provide a sensible fallback or render it, or the standalone persona silently loses content.

**Why:** discovered implementing convention-profiles (branch feat/convention-profiles) — RELEASE_VERSIONING_BLOCK/RELEASE_CHANGELOG_BLOCK/GIT_ISSUE_NAMING_BLOCK. The `conventions`-SKILL "Adding a New Placeholder" checklist only names config.py + the doc table, not these two.
**How to apply:** whenever adding any build_variables placeholder, grep `_BUILTIN_VARS` and `_ORCHESTRATION_FALLBACKS`/`_standalone_variables` and update both. See [[dual-template-tree-modern]] for the parallel 1-generic-modern gotcha.
