# Prompt-Modernisierung — Konzept (Aktiv)

**Status:** Aktiv — Phase 1 implementiert  
**Erstellt:** 2026-06-30  
**Branch:** feat/prompt-modernization-poc

## Problemstellung

Agent-Prompts in `1-generic/` wachsen unkontrolliert. Orchestrator-Template: ~8500 Tokens.
Keine strukturelle Einschränkung verhindert Copy-Paste-Inflation.
Fehlende Semantik: gleichwertige Abschnitte sind nicht maschinenlesbar unterscheidbar.

## Lösung: Drei-Modus-Architektur

| Modus | Template | Tokens | Eingesetzt ab |
|-------|----------|--------|---------------|
| `legacy` | `1-generic/<rolle>.md` | beliebig | v0.1 |
| `hybrid` | `1-generic/<rolle>.md` + Auto-XML-Wrap | ~gleich | geplant |
| `modern` | `1-generic-modern/<rolle>.md` | optimiert | v0.65 |

## 6-Block-XML-Struktur (Modern Mode)

Pflicht-Reihenfolge (Recency-Bias-optimiert):

```xml
<persona>   — Wer der Agent ist
<workflow>  — Wie der Agent vorgeht
<context>   — Was er wissen muss
<tools>     — Welche Tools er hat
<output_contract> — Was er liefern muss
<constraints>     — Was er nicht tun darf (zuletzt = höchste Gewichtung)
```

## Konfiguration

In `.meta-config/project.yaml`:

```yaml
agent-prompts:
  default: legacy          # legacy | hybrid | modern
  modes:
    orchestrator: modern   # Pro-Rolle-Override
    developer: modern
```

## Implementierte Artefakte (Phase 1)

- `agents/1-generic-modern/orchestrator.md` — v6.0.0, −61% Tokens vs. Legacy
- `agents/1-generic-modern/developer.md` — v3.0.0, −37% Tokens vs. Legacy
- `snippets/prompt-modernization/a2a-handoff-block.md` — TypeScript-Interfaces
- `scripts/validate-modern-templates.py` — 6-Block-Validator
- `scripts/token-counter.py` — Tokens-Vergleich Legacy vs. Modern
- `config/project-config.schema.json` — `agent-prompts` + `cascades` Properties
- `config/prompt-modes.yaml` — Framework-Defaults
- `scripts/lib/agents.py` — `_resolve_agent_source()`, `MODERN_DIR`
- `scripts/lib/log.py` — `[modern]`-Annotation im Sync-Log
- `scripts/admin-server.py` — `/api/prompt-modes` Endpoint, `prompt_mode` in Hierarchy
- `docs/admin-ui.html` — Badges + `/project/prompt-modes` Seite
- `docs/architecture/prompt-modernization.md` — Architektur-Dokumentation

## Offene Punkte (Phase 2+)

- XML-Anchor-Support: Composition (`extends:` + `patches:`) gegen Modern-Templates
- `consistency-check.py`: `prompt_mode` Frontmatter-vs-Config-Abgleich
- `hybrid`-Modus: `wrap_sections_in_xml()` in `sync.py` implementieren
- Mehr Rollen modernisieren: `senior-developer`, `git`, `feature`
- CI-Integration: `validate-modern-templates.py --strict` im Pre-Commit

## Metriken

| Rolle | Legacy | Modern | Einsparung |
|-------|--------|--------|------------|
| orchestrator | ~8558 Tokens | ~3315 Tokens | −61% |
| developer | ~1384 Tokens | ~867 Tokens | −37% |
