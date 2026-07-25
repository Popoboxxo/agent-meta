# Architektur: Prompt-Modernisierung (XML-Struktur)

> Status: **Aktiv** (Konsolidiert in v0.70.0)

---

## Übersicht

agent-meta verwendet für alle Agenten-Templates eine hochoptimierte 6-Block-XML-Architektur. Dies ist der alleinige Standard (der frühere "Dual-Tree"-Ansatz mit Markdown-Legacy-Templates wurde vollständig aufgelöst).

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
