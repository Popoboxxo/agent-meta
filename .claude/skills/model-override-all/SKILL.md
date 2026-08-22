---
name: model-override-all
description: "Use when you want to blast EVERY active agent of a provider onto one model (discount promos / usage caps) — covers the reversible project.yaml model-override-all key, sync resolution priority, and how to toggle it."
---

# agent-meta — Model Override-All (reversible promo blast)

Blast **all** active agents of a single provider onto one concrete model in one
move — e.g. to exploit provider discount promotions or usage caps.

## Why this (and not per-role `model-overrides`)

`model-override-all` is a single, centralized, **reversible** switch:

- Set `model-override-all[provider] = <model>` → sync resolves *every* role of
  that provider to that model, overriding per-role / tier / preset / alias logic.
- Remove the provider key (or the whole block) → the previous per-agent settings
  resume automatically. No per-role cleanup required.

Per-role `model-overrides` is the wrong tool here: it is not reversible in one
step and must be edited role-by-role.

## Resolution priority (scripts/lib/roles.py)

`model-override-all[provider]` wins over everything else — it is checked first,
before `model-overrides`, `tier-overrides`, role-defaults, presets and aliases.
Value is resolved through `_resolve_tier_to_model`, so a tier (`nano`/`fast`/
`balanced`/`powerful`/`max`), a legacy alias (`haiku`/`sonnet`/`opus`) or a full
model ID (`claude-sonnet-4-6`) are all accepted.

## Sibling mode: model-inherit-main-chat

`model-inherit-main-chat[provider] = true` makes every role of that provider
inherit the main chat's model: sync omits the generated `model:` field entirely.
Per provider this is **hard-exclusive** with `model-override-all` — setting
both keys for the same provider aborts sync with exit code 1. Toggle it via its
own Admin-UI switch (*Project → Model Overrides*).

## project.yaml shape

```yaml
model-override-all:
  Claude: claude-sonnet-4-6
  Gemini: gemini-2.5-pro
```

Schema: `config/project-config.schema.json` → `model-override-all`
(object, provider name → string). Allowed as a project section in
`scripts/admin-server.py` (`_write_project_section` whitelist).

## Toggle workflow

1. Read current state from `.meta-config/project.yaml` (`model-override-all`).
2. Enable: merge the provider key into the block.
3. Disable: delete the provider key (or the entire block).
4. **Always re-run `sync.py`** so generated agents pick up the change:
   ```bash
   py scripts/sync.py --config .meta-config/project.yaml
   ```

## Admin-UI shortcut

*Project → Model Overrides → "Override All"* bar:
- Provider dropdown + model input + **"Alle Rollen überschreiben"** → writes
  `model-override-all[provider] = model`.
- **"Zurücksetzen"** → removes that provider key (reversible).

## Caveats

- Only affects providers with model tiers (same gate as the rest of the
  model-override UI). Mammouth / Continue are registry-only and excluded.
- Reversible by design, but a blast overrides *all* agent intent for that
  provider until cleared — confirm before enabling on a shared project.
- Branch policy still applies: changing project.yaml + re-syncing propagates to
  all pinned consumer projects → use a feature branch.
