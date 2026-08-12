---
name: multi-provider-three-file-invariant
description: A provider in ai-providers.yaml MUST also appear in the 3 PAL config files or it silently degrades at sync
metadata:
  type: project
---

Ein Provider, der in `config/ai-providers.yaml` definiert ist, MUSS zusätzlich in allen drei Provider-Abstraction-Layer-Configs stehen: `config/provider-capabilities.yaml`, `config/provider-bootstrap.yaml`, `config/delegation-syntax.yaml`.

**Why:** Consumer-Code (`scripts/lib/delegation_syntax.py`, `scripts/lib/bootstrap.py`) nutzt durchgehend `.get(provider, {})` mit Empty-Dict-Fallback. Fehlt ein Provider in delegation-syntax.yaml, strippt `DelegationSyntaxEngine.apply()` still ALLE `PAL_*`-Delegations-Platzhalter aus den generierten Agenten (delegate/fanout/fallback/handoff verschwinden komplett). Fehlt er in provider-capabilities.yaml, defaulten `bootstrap_required`/`subagent_dispatch`/`file_based_agents` stumm auf `false`. Keine Warnung, kein Fehler — reiner Silent-Downgrade. Genau das passierte Mammouth (gefixt in fix/provider-best-practices).

**How to apply:** Beim Hinzufügen/Ändern eines Providers immer alle vier Dateien synchron halten. Für einen "schlanken" Provider (begrenzte Fähigkeiten) ist `Copilot` das konservative Referenz-Pattern (text-basiertes `@agent`-Delegate, sequentiell, YAML-Handoff via `*handoff-yaml`-Anchor, orchestrierungsrelevante Caps auf `false`). `hooks:`-Wert aus `has_hooks:` in ai-providers.yaml ableiten (via [[tier-resolution-missing-key-silent-empty]]-artiger Logik). Kein CI-Check erzwingt diese Kopplung — rein konventionell.
