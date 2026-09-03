---
type: "Architecture"
title: "Architektur: Prompt-Modernisierung (XML-Struktur)"
description: "agent-meta verwendet für alle Agenten-Templates eine hochoptimierte 6-Block-XML-Architektur. Dies ist der alleinige Standard (der frühere Dual-Tree-Ansatz mit Markdown-Legacy-Templates wurde vollständig aufgelöst)."
tags: [architecture, "status:active"]
timestamp: "2026-09-03"
resource: "../../sources/docs/architecture/prompt-modernization.md"
migrated_from: "docs/architecture/prompt-modernization.md"
migration_note: "Re-Ingest 2026-09-03 (Issue #651): Neue Seite — spiegelt den tatsächlich umgesetzten, konsolidierten Ein-Standard-Zustand (docs/architecture/) wider, im Gegensatz zum historischen Legacy/Hybrid/Modern-Planungskonzept in concepts/prompt-modernization.md (dort als SUPERSEDED markiert)."
---
# Architektur: Prompt-Modernisierung (XML-Struktur)

> [Back to Architecture Overview](../../../ARCHITECTURE.md)

> Status: **Aktiv** (Konsolidiert in v0.70.0)
>
> Historisches Planungskonzept (Legacy/Hybrid/Modern-Dreiklang, nie so gebaut):
> [`concepts/prompt-modernization.md`](prompt-modernization.md)

---

## Übersicht

agent-meta verwendet für alle Agenten-Templates eine hochoptimierte 6-Block-XML-Architektur. Dies ist der alleinige Standard (der frühere "Dual-Tree"-Ansatz mit Markdown-Legacy-Templates wurde vollständig aufgelöst).

> **Ausnahme (Audit-Fund 2026-09-03):** Die ~13 `se-*.md`-Rollen der SE-Kaskade (siehe
> `architecture-se-cascade.md`, aktuell deaktiviert) nutzen weiterhin klassisches
> Markdown+Prosa statt XML — bislang nicht als bewusste Ausnahme in dieser Seite dokumentiert.

---

## 6-Block XML-Format

Alle Agenten-Templates (`agents/1-generic/*.md`) verwenden exakt 6 XML-Blöcke in fester Reihenfolge:

```xml
<persona>       Rolle, Verhalten, Singleton-Regeln
<workflow>      Schritt-für-Schritt-Prozess (nummeriert)
<context>       Projektkontext, DoD-Flags, Agenten-Tabelle, Env-Vars
<tools>         Erlaubte Tools mit Kurzbeschreibung
<output_contract> Rückgabe-Format, Tracker, Eskalation
<constraints>   Harte Regeln — zuletzt (Recency Bias)
```

**Recency Bias:** `<constraints>` steht absichtlich am Ende — modernste LLMs (Claude 3.5, Gemini 1.5, GPT-4o) befolgen letzte Instruktionen in langen Prompts am zuverlässigsten.

---

## Pre-resolved Block-Variablen

Um die Template-Größe zu minimieren und unnötige Tokens zu sparen, werden dynamische Blöcke im Backend (`scripts/lib/config.py`) "pre-resolved":

| Variable | Inhalt wenn aktiv | Leer wenn |
|----------|-------------------|-----------|
| `{{DOD_REQ_BLOCK}}` | REQ-ID-Pflicht-Hinweis | req-traceability: false |
| `{{DOD_TESTS_BLOCK}}` | Test-Pflicht-Hinweis | tests-required: false |
| `{{A2A_HANDOFF_BLOCK}}` | A2A-Contract-Kurzreferenz | A2A deaktiviert |
| `{{ANTI_RECURSION_BLOCK}}` | Anti-Recursion-Regel | nie leer |

---

## TypeScript Interfaces (A2A Handoff Contracts)

Das A2A-Protokoll basiert auf strikten JSON-Typ-Definitionen:

```typescript
interface IPayload { t, ctx?, con?, refs?, pri?, dep? }
interface IEnvelope { protocol_version, handoff_id, source_agent, target_agent, schema_ref, payload }
interface IResult { status, result, artifacts?, errors? }
interface IEscalation extends IResult { escalate_reason, recommended_tier, partial_work, next_steps }
interface IBatchPayload { batch: true, payload: IPayload[] }
```

---

## Validierung

Die XML-Struktur der Agenten wird automatisch bei jedem Run von `sync.py --validate` durch den Consistency-Check (`scripts/consistency-check.py`) sichergestellt.
