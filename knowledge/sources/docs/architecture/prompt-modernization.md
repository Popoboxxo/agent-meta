# Architektur: Prompt-Modernisierung (Three-Mode Design)

> Status: **PoC** — Branch `feat/prompt-modernization-poc`
> Konzept: `docs/concepts/active/se-und-prompt-modernisierung.md`

---

## Übersicht

agent-meta unterstützt drei Prompt-Rendering-Modi für Agenten-Templates:

| Modus | Template-Quelle | Rendering | Ziel |
|-------|----------------|-----------|------|
| `legacy` | `agents/1-generic/` | unverändertes Markdown | Kompatibilität, alle Rollen |
| `hybrid` | `agents/1-generic/` | Markdown → auto-XML-Wrap via `wrap_sections_in_xml()` | schrittweise Migration |
| `modern` | `agents/1-generic-modern/` | natives 6-block XML | optimale LLM-Strukturierung |

---

## 6-Block XML-Format (Modern Mode)

Alle Modern-Mode-Templates verwenden genau 6 XML-Blöcke in fester Reihenfolge:

```
<persona>       Rolle, Verhalten, Singleton-Regeln
<workflow>      Schritt-für-Schritt-Prozess (nummeriert)
<context>       Projektkontext, DoD-Flags, Agenten-Tabelle, Env-Vars
<tools>         Erlaubte Tools mit Kurzbeschreibung
<output_contract> Rückgabe-Format, Tracker, Eskalation
<constraints>   Harte Regeln — zuletzt (Recency Bias)
```

**Recency Bias:** `<constraints>` steht absichtlich am Ende — LLMs befolgen letzte Instruktionen zuverlässiger.

---

## Template-Verzeichnisstruktur

```
agents/
  1-generic/              Legacy-Templates (unverändertes Markdown)
  1-generic-modern/       Modern-Mode-Templates (native XML)
    developer.md          v3.0.0
    orchestrator.md       v6.0.0
  2-platform/             Plattform-Overrides (extends: + patches:)
  3-project/              Projekt-Overrides / Extensions
```

---

## Konfiguration (project.yaml)

```yaml
agent-prompts:
  default: legacy          # Fallback für alle nicht-expliziten Rollen
  modes:
    developer: modern      # developer → 1-generic-modern/developer.md
    orchestrator: modern   # orchestrator → 1-generic-modern/orchestrator.md
```

---

## Source-Resolution (`_resolve_agent_source()`)

Beim Sync entscheidet `scripts/lib/agents.py` welches Template verwendet wird:

```
1. prompt_modes[role] == 'modern' → 1-generic-modern/<role>.md (wenn vorhanden)
2. prompt_modes['default'] == 'modern' → 1-generic-modern/<role>.md (wenn vorhanden)
3. Fallback → 1-generic/<role>.md
```

2-platform und 3-project Overrides greifen DANACH (nach der Source-Resolution):
- `extends:` / `patches:` funktionieren nur gegen Legacy-Templates (Phase 1 + 2)
- XML-Anchor-Support für Modern Templates ist Phase 2 (geplant)

---

## Pre-resolved Block-Variablen

Modern-Mode-Templates verwenden KEINE `{{#if}}`-Bedingungen. Stattdessen werden
Blöcke in `build_variables()` (config.py) pre-resolved:

| Variable | Inhalt wenn aktiv | Leer wenn |
|----------|-------------------|-----------|
| `{{DOD_REQ_BLOCK}}` | REQ-ID-Pflicht-Hinweis | req-traceability: false |
| `{{DOD_TESTS_BLOCK}}` | Test-Pflicht-Hinweis | tests-required: false |
| `{{A2A_HANDOFF_BLOCK}}` | A2A-Contract-Kurzreferenz | A2A deaktiviert |
| `{{ANTI_RECURSION_BLOCK}}` | Anti-Recursion-Regel | nie leer |

---

## TypeScript Interfaces (A2A Handoff Contracts)

Vollständige Definitionen in `snippets/prompt-modernization/a2a-handoff-block.md`:

```typescript
interface IPayload { t, ctx?, con?, refs?, pri?, dep? }
interface IEnvelope { protocol_version, handoff_id, source_agent, target_agent, schema_ref, payload }
interface IResult { status, result, artifacts?, errors? }
interface IEscalation extends IResult { escalate_reason, recommended_tier, partial_work, next_steps }
interface IBatchPayload { batch: true, payload: IPayload[] }
```

---

## Schema-Erweiterungen

`config/project-config.schema.json` (Draft-07) wurde erweitert um:

- **`agent-prompts`**: `{default: enum, modes: {role: enum}}`
- **`cascades`**: First-Class-Konzept für SE-Kaskaden (Phase 3+)
- **`$defs/cascadeDefinition`**, **`$defs/cascadeStage`**

---

## Validierungs-Tooling

```bash
# Alle Modern-Templates validieren (6-block + frontmatter)
python scripts/validate-modern-templates.py --all --strict

# Token-Vergleich legacy vs. modern
python scripts/token-counter.py --role developer
python scripts/token-counter.py --role orchestrator

# Alle Templates zählen
python scripts/token-counter.py --legacy --modern
```

---

## Phasenplan (Übersicht)

| Phase | Inhalt | Status |
|-------|--------|--------|
| 1 (PoC) | developer + orchestrator in Modern Mode, Infra-Grundlage | **in Arbeit** |
| 2 | XML-Anchor-Support für Composition, Hybrid-Mode verfeinern | geplant |
| 3 | Cascades-Runtime, SE-Kaskaden über cascades-Config | geplant |
| 4–6 | Weitere Rollen migrieren, Monitoring, GA | geplant |

Detaillierter 6-Phasen-Plan → `docs/concepts/active/se-und-prompt-modernisierung.md`

---

## Constraints (Phase 1)

- Modern-Templates sind **keine** `extends:`/`patches:`-Targets (noch kein XML-Anchor-Support)
- `1-generic-modern/` enthält **nur** provider-agnostische Templates (keine `.claude/`, `.gemini/`-Referenzen)
- `prompt_mode: modern` im Frontmatter ist **Pflicht** — Validator prüft dies
- Versionierung: Modern-Templates starten bei Major-Version ≥ 3
