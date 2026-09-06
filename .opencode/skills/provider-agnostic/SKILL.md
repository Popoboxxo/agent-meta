---
name: provider-agnostic
description: "Use when editing templates in agents/1-generic — covers the provider-agnostic policy."
---

# Provider-Agnostic Policy

Generische Templates in `1-generic/` müssen provider-agnostisch sein. Keine spezifischen Prompts für Claude, Gemini etc., außer als Fallback/Feature-Flag.

## Syncer-Code (scripts/)

Provider-Unterschiede werden über Capability-Flags/Config-Keys in `config/ai-providers.yaml`
(und Schwester-Registries wie `provider-capabilities.yaml`) ausgedrückt, nie über
`if provider == "Name"`-Branches im Python-Code. Ein neuer Provider muss ohne
Python-Änderung aktivierbar sein, solange er kein wirklich neues Datei-Format oder
Protokoll braucht. Das bestehende Capability-Flag-Muster (`_has_capability(pc, "...")`,
`pc.get("commands_dir", ...)`, `frontmatter_strip_fields` aus Issue #505) ist die
Referenz-Implementierung — dem folgen, keinen neuen `elif` hinzufügen.
