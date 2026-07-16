---
name: tier-resolution-missing-key-silent-empty
description: sync.py resolve_model returns empty string (no model field) if a tier key is absent from the active preset — add new tiers to ALL presets
metadata:
  type: project
---

`scripts/lib/roles.py::resolve_model` silently returns `""` (no `model:` field injected → agent falls back to provider default) when a role's tier is not present in the active preset's `tiers:` block.

**Why:** The new-format path (`if "tiers" in preset_data`) only returns when `direct_model` is truthy; a missing key makes it fall through to the old-format `mapping` path, then `_resolve_tier_to_model(tier, ...)` looks the tier up in the provider's `model-tiers` table (a different table, usually undefined for a new tier) → returns `""`. No error, no warning.

**How to apply:** When adding a new abstract tier (e.g. the `ultra` tier added above `max`), it must be added to EVERY preset in `config/tier-presets.yaml` — both the top-level `tiers:` block AND every provider block (`providers.<Provider>.tiers`). `_KNOWN_TIERS`/`_TIER_SEQUENCE` in roles.py already list `nano/fast/balanced/powerful/max/ultra`. Verify resolution per preset×provider with a direct `resolve_model` call — validation does NOT catch a missing tier key.
