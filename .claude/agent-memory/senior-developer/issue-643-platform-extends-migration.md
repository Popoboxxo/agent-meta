---
name: issue-643-platform-extends-migration
description: 2-platform full-replacement→extends+patches migration (#643); which files migratable vs skip, two composition-engine fixes required, sync-run churn gotcha
metadata:
  type: project
---

# #643: migrate 2-platform full-replacement overrides to extends+patches

**Status:** DONE (5 migrated, 8 skipped), NOT committed. Verified byte-identical.

## Classification (agents/2-platform/, 18 files: 5 hacs already-migrated + 13 full-replacement)
- **Migratable (5)** — retain base XML anchors (`<persona>`…`<constraints>`), only some sections diverge → `replace`/`append-after` patches: `agent-meta-developer`, `homeassistant-developer`, `homeassistant-documenter`, `homeassistant-log-analyzer`, `sharkord-developer`.
- **SKIP (8)** — zero shared structure with base (no XML anchors, different headings/language) → a patch list would be a full-body replacement: `sharkord-docker`, `sharkord-release`, and all 6 `agent-meta-*-expert` (claude/continue/copilot/gemini/mammouth/opencode; base `provider-expert.md` uses XML tags, overrides are hand-written `# Role:` docs).

**Why:** issue framed "12" full-replacement; actual count is 13 non-hacs (6 experts, not 5). The provider-expert group is a genuine rewrite, not composition.

**How to apply:** to migrate one, replace only diverged XML sections (compare per-section; tools/output_contract often identical → inherited). `replace` op carries the override's section text verbatim; unchanged inter-section gaps must already match base.

## Two composition-engine fixes were REQUIRED (both in scripts/lib)
1. `agent_sync._find_section_bounds` XML-anchor matching was **substring** (`open_tag in line`) → matched inline mentions like ``(see `<context>`)`` in workflow before the real section, mis-scoping `replace`. Fixed to **standalone-line** match (mirrors `config_audit._STANDALONE_TAG_RE`). Output-neutral for existing hacs (they use append-after; only end_idx matters).
2. `frontmatter._merge_frontmatter` used base-first key order (`{**base_fm,**override_fm}`) → override-only keys like `based-on` appended after `tools`, but original full-replacement declared `based-on` after `version`. Provider transform preserves source field order → byte diff. Fixed to **preserve override declared order**, then append base-only keys. Cross-repo cosmetic effect: hacs `based-on` moves to declared position on next sync (field order only, no value/body change).

**Why:** without both, `replace` on `<context>`/`<output_contract>` (sections the developer workflow references inline) produces malformed source (stray `</workflow>`, tripped by config-audit `unpaired-closing-tag`) and non-byte-identical frontmatter.

## Verification approach (reusable)
Composition-level proof is sufficient + rigorous: final per-provider output = deterministic f(post-composition content). So byte-identity ⟺ `compose_agent(base, migrated)` body == original body AND parsed frontmatter values equal. Harness in scratchpad. Confirmed end-to-end via real sync: generated `.claude/.gemini/.mammouth/agents/developer.md` had empty git diff.

**GOTCHA:** plain `python3 scripts/sync.py` regenerates README.md / CHANGELOG.md / docs/architecture/*.md (version-stamp/date refresh, was stale 0.92.0→0.101.0-beta.4) — unrelated churn. Prefer the composition harness or `--dry-run` for verification; if a full sync is run, only the task files should be staged.
