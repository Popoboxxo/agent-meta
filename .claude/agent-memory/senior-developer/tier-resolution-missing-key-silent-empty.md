---
name: tier-resolution-missing-key-silent-empty
description: sync.py resolve_model returns empty string (no model field) if a tier key is absent from the active preset — add new tiers to ALL presets
metadata:
  type: project
---

`scripts/lib/roles.py::resolve_model` silently returns `""` (no `model:` field injected → agent falls back to provider default) when a role's tier is not present in the active preset's `tiers:` block.

**Why:** The new-format path (`if "tiers" in preset_data`) only returns when `direct_model` is truthy; a missing key makes it fall through to the old-format `mapping` path, then `_resolve_tier_to_model(tier, ...)` looks the tier up in the provider's `model-tiers` table (a different table, usually undefined for a new tier) → returns `""`. No error, no warning.

**How to apply:** When adding a new abstract tier (e.g. the `ultra` tier added above `max`), it must be added to EVERY preset in `config/tier-presets.yaml` — both the top-level `tiers:` block AND every provider block (`providers.<Provider>.tiers`). `_KNOWN_TIERS`/`_TIER_SEQUENCE` in roles.py already list `nano/fast/balanced/powerful/max/ultra`. Verify resolution per preset×provider with a direct `resolve_model` call — validation does NOT catch a missing tier key.

**Additional hardcoded tier lists to keep in sync (found 2026-07-21, fix/agents-md-footer-regen):** A new tier must ALSO be added to (1) `docs/ui/admin-ui.html` const `TIERS` (~line 6704, drives both Resolved + Edit tabs of the `#/tier-presets` view via `viewTierPresets`; missing `ultra` hid the repaired ultra rows) and (2) `config/ai-providers.yaml` `providers.<P>.model-tiers` (the per-provider baseline = "Normal" preset's generic tiers; feeds `/api/providers` → `#/project/provider-tier-overrides`). Also: tier-presets.yaml providers blocks only listed Claude/Gemini/Opencode — Mammouth was entirely absent, so the admin-ui fell back to preset.tiers (Claude values). Canonical Mammouth model IDs (deepseek-v4-flash/deepseek-v4-pro/kimi-k2.6/glm-5.2) live only in ai-providers.yaml Mammouth model-tiers; not in generated/model-registry.json (which has only opencode-go/-prefixed IDs). Admin-server endpoints are pure live-read pass-throughs (no tier whitelist), but the server is a long-running process — restart `python scripts/admin-server.py` after config edits to clear any stale startup state.
