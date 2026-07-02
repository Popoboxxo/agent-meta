---
name: model-id-canonical-source
description: Canonical source and format for Claude Code model IDs in this repo; fix/admin-ui-model-sync branch is partially ported, rest unmerged
metadata:
  type: project
---

Canonical Claude Code model IDs come from https://platform.claude.com/docs/en/about-claude/models/overview.md (markdown variant; docs.anthropic.com lists API-only models Claude Code rejects). Convention: 4.6+ generation = dateless dash IDs (`claude-sonnet-4-6`), pre-4.6 = dated snapshot IDs (`claude-haiku-4-5-20251001`). OpenRouter spells versions with dots (`anthropic/claude-opus-4.8`) — never valid for Claude Code frontmatter.

**Why:** Admin UI model picker fed agents invalid IDs because `config/generated/model-registry.json` only had OpenRouter/Zen IDs. Fixed in commit `dc5205b` on `feat/prompt-modernization-poc` (2026-07-02) by porting `model_discovery.py` from the unmerged branch `origin/fix/admin-ui-model-sync` plus a dot→dash dedup normalization.

**How to apply:** `fix/admin-ui-model-sync` (24 commits, base 94bc056) is still unmerged and contains further Admin-UI work (provider-baselines rename, test_admin_ui_render.py) AND an incompatible tier-presets.yaml schema (`tiers.<Provider>` + `default:`) vs. the schema on feat/prompt-modernization-poc (`tiers:` flat + `providers.<P>.tiers`). Merging it later WILL conflict in model_discovery.py, ai-providers.yaml, tier-presets.yaml — the poc branch has the newer state for these.
