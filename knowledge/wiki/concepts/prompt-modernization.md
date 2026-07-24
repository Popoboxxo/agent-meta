---
type: "Concept"
title: "Konzept: Prompt-Modernisierung durch Two-Mode-Prompt-Architektur"
description: "Die aktuellen Agenten-Templates in agent-meta/agents/1-generic/ sind überwiegend als narrative Markdown-Dokumente verfasst. Die systematische Evaluierung aller 55 generischen..."
tags: [concept, status:planned]
timestamp: "2026-07-10T20:58:55Z"
resource: "../../sources/docs/concepts/planned/prompt-modernization.md"
migrated_from: "docs/concepts/planned/prompt-modernization.md"
migration_note: "3 Versionen gefunden (docs/architecture/, docs/concepts/active/, docs/concepts/planned/). planned-Version gewaehlt als massgebliche Seite (umfangreichste/aktuellste, 1949 Zeilen). Andere Versionen als Sources abgelegt, keine eigenen Wiki-Seiten."
---
# Konzept: Prompt-Modernisierung durch Two-Mode-Prompt-Architektur

> Status: **Konzept-Entwurf v2.1 — überarbeitet nach Machbarkeits-Analyse** | 2026-06-29
> Ziel: Einführung einer zweigleisigen Prompt-Architektur für agent-meta — Legacy-Mode (bestehender Markdown-Fluss) und Modern-Mode (XML-/Contract-basierte Struktur) mit sanftem Hybrid-Migrationspfad.
> Bezugsdokumente: `admin-ui-concept.md`, `admin-ui-architecture.md`, `dynamic-model-presets.md`
> Quellen: `reports/prompt-optimization/00_SUMMARY.md` und alle zugehörigen Rollen-Reports

---

## 1. Executive Summary

### 1.1 Problem

Die aktuellen Agenten-Templates in `agent-meta/agents/1-generic/` sind überwiegend als narrative Markdown-Dokumente verfasst. Die systematische Evaluierung aller 55 generischen Agenten (`reports/prompt-optimization/00_SUMMARY.md`) hat wiederkehrende Anti-Patterns identifiziert:

1. **JSON Mock-Data Bloat:** A2A-Handoff-Payloads werden durch vollständige JSON-Beispiele spezifiziert (teilweise 50–90 Zeilen). Das erhöht den Token-Verbrauch und das Risiko, dass das Modell Beispieldaten in echte Outputs halluziniert.
2. **Erzählender Fließtext:** Workflows, Rollen und Verbote sind als Prosa formuliert. Das senkt die Informationsdichte und zwingt das Modell zur impliziten Inferenz.
3. **Schwache Strukturierung:** Markdown-Header (`#`, `##`) haben keine syntaktische Schließung. In langen Prompts verschwimmen Sektionen.
4. **Lost in the Middle:** Kritische Constraints (Don'ts, Anti-Recursion-Guard) sind über den gesamten Prompt verteilt. Modelle verlieren Anweisungen aus der Mitte des Kontexts.
5. **Redundanz:** Zentrale Verhaltensregeln (z. B. "Router, nicht Worker" beim Orchestrator) tauchen an mehreren Stellen auf.

### 1.2 Lösung: Two-Mode-Prompt-Architektur

Statt eines großen Big-Bang-Rewrites wird ein **zweigleisiges System** eingeführt:

| Modus | Bedeutung | Einsatz |
|-------|-----------|---------|
| **Legacy** | Bestehende Markdown-Templates unverändert | Default, Rückwärtskompatibilität |
| **Hybrid** | Legacy-Inhalt, aber automatisch in XML-Sektionen gewrappt | Sanfter Übergang, keine Template-Änderung |
| **Modern** | Native XML-Struktur + TypeScript-Contracts + Constraints am Ende | Neue/Rewrite-Agenten, höchste Token-Effizienz |

Der Modus wird **pro Rolle** in `.meta-config/project.yaml` konfiguriert. Damit können einzelne Agenten schrittweise migriert werden, während der Rest des Ökosystems stabil bleibt.

### 1.3 Erwarteter Impact

| Metrik | Hypothese | Begründung |
|--------|-----------|------------|
| Input-Token-Kostenreduktion | **15–20 %** für `developer.md` | XML-Tags ersetzen Markdown-Header-Padding; TypeScript-Interfaces ersetzen JSON-Beispiele |
| Reduzierte "Lost-in-the-Middle"-Effekte | **Deutlich reduziert** | Constraints am Ende (Recency Bias) |
| Halluzinations-Risiko | **Deutlich reduziert** | Keine ausufernden Mock-Daten; Constraints am Ende |
| Regeltreue | **Höher** | Harte Constraints werden syntaktisch abgegrenzt und wiederholt |

**Hinweis:** Time-to-First-Token (TTFT) ist keine sinnvolle Zielgröße für diese Prompt-Modernisierung, da TTFT primär von Netzwerk- und Modell-Initialisierungslatenz abhängt und nicht vom Prompt-Format. Die relevante Metrik ist die **Input-Token-Kostenreduktion**.

Die Schätzung von 15–20 % für `developer.md` basiert auf einem Vorab-Vergleich: Legacy 197 LOC vs. Modern ~150 LOC plus einer Heuristik für den XML-Tag-Overhead (siehe Abschnitt 5.8 und 10.3).

**Validierung:** Die 15–20 % sind eine **Hypothese** auf Basis von Zeilenvergleich plus Tag-Overhead-Heuristik. "Zeichenzahl / 4" ist für deutsche Templates unscharf. Die erste belastbare Messung erfolgt im PoC via `scripts/token-counter.py`. Erst danach wird die Zahl als verifiziertes Ziel verankert.

### 1.4 PoC-Empfehlung

**Empfohlener PoC-Agent: `developer`** (statt `orchestrator`).

Begründung:
- `developer.md` hat 197 Zeilen und einen klar abgegrenzten Scope.
- Der Orchestrator hat 849 Zeilen und ist das zentrale Routing-Nervensystem — ein Fehler hier blockiert das gesamte Framework.
- Der `developer` deckt alle relevanten Struktur-Elemente ab (Persona, Workflow, A2A-Handoff, Constraints, Reflection-Loop), ohne die komplexe Routing-Matrix des Orchestrators zu benötigen.
- Validierung ist einfacher: Ein Feature-Implementierungstask kann vor und nach der Modernisierung auf Token-Verbrauch und Regeltreue verglichen werden.

Der PoC soll in einem separaten Branch `feat/prompt-modernization-poc` durchgeführt werden.

---

## 2. Analyse der Report-Empfehlungen

### 2.1 Verifikationstabelle: Report-Befund → Konzept-Section

Die folgende Tabelle dokumentiert, dass alle zentralen Befunde aus `reports/prompt-optimization/00_SUMMARY.md` im Konzept adressiert werden.

| # | Report-Befund | Kategorie | Konzept-Section | Adressiert |
|---|---------------|-----------|-----------------|------------|
| 1 | Context Engineering 2026 (Paradigmenwechsel) | State of the Art | 1.2, 1.3, 4.1 | Ja |
| 2 | Struktur > Prosa | State of the Art | 4.1 (6-Block-Template), 7, 8 | Ja |
| 3 | TOON-Notation | State of the Art | 2.2, 12.2 (offener Punkt) | Ja |
| 4 | JSON Mock-Data Bloat | Befund A | 5.1, 5.7, Anhang B | Ja |
| 5 | Narrative Workflows | Befund B | 4.1, 4.2, 7, 8 | Ja |
| 6 | Markdown vs XML (schwache Strukturierung) | Befund C | 4.1, 4.4, 6.7, Anhang A | Ja |
| 7 | Lost in the Middle | Befund D | 1.3, 4.1, 4.2, 6.6, 12 | Ja |
| 8 | Framework-Verletzungen in `1-generic` | Befund E | 12, 14.2, Anhang C | Ja |
| 9 | Phase 1: Structure & Contract | Architektur | 4.1, 5, 6, 16 | Ja |
| 10 | Phase 2: Compaction (Deletion-based) | Architektur | 1.3, 5.7, 10.3 | Ja |
| 11 | Phase 3.1: TOON-Evaluierung | Architektur | 2.2, 12.2 | Ja |
| 12 | Phase 3.2: Output Shaping | Architektur | 4.2, 5.4, Anhang A | Ja |
| 13 | Phase 3.3: A2A-Rules-Zentralisierung | Architektur | 6.3, 6.6, 12, 16 | Ja |

### 2.2 State of the Art: Context Engineering 2026

Der Report identifiziert drei zentrale Trends, die das Konzept prägen:

1. **Vom Prompting zum Context Engineering:** Die wichtigste Metrik ist die Informationsdichte. "Deletion-based Compaction" (gezieltes Löschen von Füllwörtern) ist Standard.
2. **Struktur über Prosa:** XML-Tags zur Sektionierung und TypeScript-Interfaces zur Datendefinition schlagen Markdown-Header.
3. **TOON (Tabular Object-Oriented Notation):** Ein neuer Standard für große Input-Datenmengen, der JSON ersetzen kann und bis zu 60 % Struktur-Tokens spart.

**TOON-Positionierung in diesem Konzept:**
- TypeScript-Interfaces bleiben der Standard für A2A-Contracts (Output-Shaping und maschinenlesbare Verträge).
- TOON wird für Agenten mit großen reinen Input-Datenmengen (z. B. `log-analyzer`, `explorer`) in Phase 2+ evaluiert. Ein TOON-Converter würde in `scripts/lib/` als optionaler Wrapper implementiert werden, nicht als Pflicht für alle Agenten.

### 2.3 Architektur-Umbau: Drei Phasen

Der Report empfiehlt einen Umbau in drei Phasen. Dieses Konzept übersetzt sie in konkrete Bausteine:

| Report-Phase | Konzept-Umsetzung |
|--------------|-------------------|
| Phase 1: Structure & Contract | 6-Block-XML-Template (Abschnitt 4), TypeScript-Interfaces (Abschnitt 5), `_resolve_agent_source()` (Abschnitt 6.5) |
| Phase 2: Compaction | Output-Shaping (Abschnitt 4.2), Token-Counter (Abschnitt 10.4), Fülltext-Reduktion in Modern-Templates |
| Phase 3: Framework | A2A-Handoff-Block-Zentralisierung (Abschnitt 6.6), Cascaden-Schema (Abschnitt 16), TOON-Evaluierung (Abschnitt 12.2) |

---

## 3. Zwei-Modi-Architektur

### 3.1 Übersicht

```
┌─────────────────────────────────────────────────────────────────────┐
│                     agent-meta Prompt Pipeline                       │
│                                                                      │
│  agents/1-generic/<role>.md                                          │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │   Legacy Mode   │    │   Hybrid Mode   │    │   Modern Mode   │  │
│  │                 │    │                 │    │                 │  │
│  │ Markdown-Header │    │ Markdown-Header │    │ 6 XML-Blöcke    │  │
│  │ + Prosa         │    │ + XML-Sections  │    │ + TypeScript    │  │
│  │                 │    │ (wrap_sections) │    │ + Constraints   │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
│       ▲                      ▲                      ▲                │
│       │                      │                      │                │
│   Keine Änderung      Auto-Wrapper            Neue Templates         │
│   am Template         auf Legacy-Inhalt       in 1-generic-modern/   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Legacy Mode (Status Quo)

- Quelle: `agents/1-generic/<role>.md`
- Format: Markdown mit YAML-Frontmatter
- Verhalten: Unverändert zu heute
- Einsatz: Default für alle bestehenden Projekte
- Keine neuen Abhängigkeiten, kein Migrationstaufwand

### 3.3 Hybrid Mode (Sanfter Migrationspfad)

- Quelle: Weiterhin `agents/1-generic/<role>.md`
- Mechanik: `wrap_sections_in_xml()` ist **bereits implementiert** in `scripts/lib/agents.py:355` und wird über das Flag `xml-section-wrapping: enabled: true` in `.meta-config/project.yaml` aktiviert (`agents.py:941–944`).
- Ergebnis: Der Markdown-Inhalt bleibt erhalten, wird aber in `<section name="...">`-Tags eingefasst.
- **Aufwand für Hybrid-Mode: 0** — nur Config-Flag setzen, kein neuer Code nötig.
- Vorteil: Sofortige strukturelle Verbesserung ohne Rewrite
- Nachteil: Keine TypeScript-Contracts, keine echte 6-Block-Struktur

### 3.4 Modern Mode (Zielarchitektur)

- Quelle: `agents/1-generic-modern/<role>.md` (Vorschlag) oder ein neues Unterverzeichnis
- Format: Nativer XML-Block-Aufbau nach dem 6-Block-Template
- Einsatz: Für neu hinzugefügte oder vollständig rewrite-te Agenten
- Voraussetzung: Template-Autor muss XML-Struktur bewusst nutzen

### 3.5 Mode-Switch-Granularität

Die Granularität ist **pro Rolle** in `project.yaml` konfigurierbar. Das ermöglicht eine schrittweise Migration:

```yaml
agent-prompts:
  default: legacy          # globaler Default
  modes:
    developer: modern      # developer wird modernisiert
    orchestrator: hybrid   # orchestrator erstmal nur hybrid
    concept-reviewer: modern
```

Diese Konfiguration ist bewusst **außerhalb** der `variables:`-Sektion platziert, weil sie das Sync-Verhalten selbst steuert und nicht nur Text-Substitutionen auslöst.

---

## 4. XML-Struktur-Spezifikation (Modern Mode)

### 4.1 Das 6-Block-Template

Jeder Modern-Mode-Agent besteht aus genau sechs XML-Blöcken. Die Reihenfolge ist fix; `<constraints>` steht absichtlich am Ende, um den Recency Bias auszunutzen.

```xml
<persona>
  <!-- Rolle, Tonfall, Selbstverständnis -->
</persona>

<workflow>
  <!-- Schrittfolge, Routing, Entscheidungslogik -->
</workflow>

<context>
  <!-- Projektspezifischer Kontext, Variablen, Contracts -->
</context>

<tools>
  <!-- Erlaubte Tools und ihre Verwendung -->
</tools>

<output_contract>
  <!-- Erwartetes Ausgabeformat -->
</output_contract>

<constraints>
  <!-- Harte Verbote, Anti-Recursion-Guard, Don'ts -->
</constraints>
```

### 4.2 Block-Beschreibungen

| Block | Inhalt | Beispiel-Elemente |
|-------|--------|-------------------|
| `<persona>` | Kurze Rolle, Tonfall, Scope | `Du bist der Developer für {{PROJECT_NAME}}.` |
| `<workflow>` | Ablauf als nummerierte/schrittweise Anweisung | `1. Verstehe Aufgabe → 2. Implementiere → 3. Validiere` |
| `<context>` | Projekt-Kontext, A2A-Contracts, Variablen | `{{PROJECT_CONTEXT}}`, Handoff-Schema |
| `<tools>` | Tool-Liste und Regeln für deren Einsatz | `Read, Write, Edit, Bash` |
| `<output_contract>` | Struktur der Rückgabe | TypeScript-Interfaces, STATUS-Header, Output-Shaping |
| `<constraints>` | Harte Regeln am Ende | Don'ts, Anti-Recursion, HITL-Gates |

### 4.3 XML-Escaping und Frontmatter

Das YAML-Frontmatter bleibt erhalten. Der XML-Block folgt direkt nach dem Frontmatter. Innerhalb von XML müssen folgende Zeichen escaped werden:

| Zeichen | Escape |
|---------|--------|
| `<` | `&lt;` |
| `>` | `&gt;` |
| `&` | `&amp;` |

Im Regelfall enthalten die XML-Blöcke jedoch nur Markdown-Text, keine Code-Blöcke mit XML-Syntax. Code-Beispiele werden in Markdown-Code-Fences (` ``` `) eingebettet, die den XML-Parser nicht stören.

### 4.4 Unterschied Hybrid vs. Modern

**Hybrid (automatisch generiert):**

```xml
<section name="deine-zustaendigkeiten">
### 1. Feature-Implementierung
- Minimal implementieren
...
</section>
```

**Modern (manuell/autor-intendiert):**

```xml
<workflow>
1. Parse A2A-Envelope (falls vorhanden)
2. Lese REQ-ID aus `docs/REQUIREMENTS.md` (falls DOD_REQ_TRACEABILITY)
3. Implementiere minimalen Scope
4. Validiere: bestehende Tests dürfen nicht brechen
5. Gib Ergebnis im Output-Contract-Format zurück
</workflow>
```

---

## 5. TypeScript-Interface-Spezifikation

### 5.1 Grundprinzip

A2A-Handoff-Payloads werden nicht mehr durch vollständige JSON-Beispiele, sondern durch **kompakte TypeScript-Interfaces** spezifiziert. Das reduziert die Token-Anzahl deutlich, weil Klammern, Anführungszeichen und Beispielwerte entfallen.

### 5.2 Interface: `IPayload`

```typescript
/**
 * A2A-Payload — kompakte Task-Spezifikation.
 * Feldnamen sind absichtlich kurz (Compact Mode).
 */
interface IPayload {
  /** Task-Beschreibung in einem Satz, max. {{A2A_T_SIZE_LIMIT}} Zeichen */
  t: string;
  /** Kontext als strukturierter Text oder Key-Value-Block */
  ctx?: string | Record<string, unknown>;
  /** Constraints-Liste */
  con?: string[];
  /** Referenzen (Dateien, Schemas, URLs) */
  refs?: string[];
  /** Priorität: low | medium | high | critical */
  pri?: 'low' | 'medium' | 'high' | 'critical';
  /** Abhängigkeiten/Vorbedingungen */
  dep?: string[];
}
```

### 5.3 Interface: `IEnvelope`

```typescript
/**
 * A2A-Envelope — Transport-Container für jede Delegation.
 */
interface IEnvelope {
  protocol_version: '1.0.0';
  handoff_id: string;        // HOFF-YYYYMMDD-NNN
  source_agent: string;
  target_agent: string;
  schema_ref: string;        // z.B. 'task-spec-v1'
  payload: IPayload | IPayload[];
  trace_parent?: string | null;
}
```

### 5.4 Interface: `IResult`

```typescript
/**
 * Standard-Rückgabeformat aller Worker-Agenten.
 */
interface IResult {
  status: 'done' | 'partial' | 'failed' | 'escalate';
  result: string;            // 1–2 Sätze
  artifacts?: string[];      // geänderte Dateien
  errors?: string[];         // leer wenn keiner
}
```

### 5.5 Interface: `IEscalation`

```typescript
/**
 * Erweitertes Rückgabeformat bei Eskalation oder Partial-Completion.
 */
interface IEscalation extends IResult {
  status: 'escalate' | 'partial';
  escalate_reason: string;
  recommended_tier: 'junior-developer' | 'developer' | 'senior-developer' | string;
  partial_work: string;
  next_steps: string[];
}
```

### 5.6 Interface: `IBatchPayload`

```typescript
/**
 * Batch-Mode für FANOUT — mehrere Tasks an denselben Agententyp.
 */
interface IBatchPayload {
  batch: true;
  payload: Array<IPayload & { batch_task_id: string }>;
}
```

### 5.7 Vorher/Nachher-Vergleich

**Vorher (JSON-Beispiel im Prompt):**

```json
{
  "protocol_version": "1.0.0",
  "handoff_id": "HOFF-20260628-001",
  "source_agent": "orchestrator",
  "target_agent": "developer",
  "schema_ref": "task-spec-v1",
  "payload": {
    "t": "Fix login bug",
    "ctx": "User reports 401 on /api/login",
    "con": ["Do not touch auth middleware"],
    "pri": "high"
  }
}
```

**Nachher (TypeScript-Interface im Prompt):**

```typescript
interface IEnvelope {
  protocol_version: '1.0.0';
  handoff_id: string;
  source_agent: string;
  target_agent: string;
  schema_ref: 'task-spec-v1';
  payload: IPayload;
}
```

Token-Ersparnis: ca. 60–70 % für den reinen Struktur-Teil.

### 5.8 Token-Reduktions-Schätzung für `developer.md`

| Quelle | Zeilen | Bemerkung |
|--------|--------|-----------|
| Legacy `developer.md` | 197 | Markdown-Prosa mit Tabellen |
| Modern `developer.md` | ~150 | 6 XML-Blöcke, TypeScript-Interfaces |
| Rohe Zeilenreduktion | ~24 % | (197 − 150) / 197 |
| Geschätzter XML-Tag-Overhead | ~+4–9 % | `<persona>`, `</persona>` etc. |
| **Erwartete Token-Einsparung** | **15–20 %** | Konservativ geschätzt |

Die Schätzmethode ist bewusst einfach gehalten: Zeilenvergleich plus Overhead-Heuristik. Die finale Messung erfolgt mit `scripts/token-counter.py` im PoC.

---

## 6. Mode-Switch-Implementation

### 6.1 Neue Config-Section `agent-prompts`

In `.meta-config/project.yaml` wird eine neue Sektion eingeführt:

```yaml
agent-prompts:
  default: legacy          # legacy | hybrid | modern
  modes:
    developer: modern
    orchestrator: hybrid
    concept-reviewer: modern
```

### 6.2 Schema-Erweiterung

In `config/project-config.schema.json` wird ergänzt:

```json
{
  "agent-prompts": {
    "type": "object",
    "description": "Controls prompt generation mode per role.",
    "properties": {
      "default": {
        "type": "string",
        "enum": ["legacy", "hybrid", "modern"],
        "default": "legacy"
      },
      "modes": {
        "type": "object",
        "description": "Per-role prompt mode override.",
        "additionalProperties": {
          "type": "string",
          "enum": ["legacy", "hybrid", "modern"]
        }
      }
    },
    "additionalProperties": false
  }
}
```

### 6.3 Neue Variablen in `build_variables()` — Entscheidung gegen Template-Logik

**Entscheidung:** Für bedingte Inhalte im Modern Mode werden **keine** `{{#if}}`-Conditionals in die Templates eingeführt. Stattdessen wandert die Logik in `build_variables()`/`_inject_dod()`.

**Begründung:**
- `sync.py` substituiert nur Strings und kennt keine Template-Logik.
- Eine Mini-Template-Engine (`{{#if}}`, `{{#ifeq}}`) wäre ein neues Subsystem mit Parser, Scope, Escaping und Tests.
- Die bestehende `substitute()`-Funktion arbeitet mit einfachen `{{VAR}}`-Platzhaltern; eine Erweiterung würde die Wartbarkeit senken und das Risiko von Parsing-Fehlern erhöhen.
- Stattdessen werden vorab aufgelöste String-Variablen injiziert, z. B. `{{DOD_REQ_BLOCK}}`, `{{DOD_TESTS_BLOCK}}`, `{{A2A_HANDOFF_BLOCK}}`.
- Wenn ein DoD-Kriterium nicht aktiv ist, enthält die Variable einen leeren String. Damit entfällt jede Template-Logik.

```python
def build_variables(config: dict, agent_meta_root: Path) -> tuple[dict, list[str]]:
    variables = {}
    # ... bestehende Variablen ...

    # Agent-Prompt-Mode pro Rolle
    prompt_config = config.get("agent-prompts", {})
    default_mode = prompt_config.get("default", "legacy")
    per_role_modes = prompt_config.get("modes", {})

    for role in config.get("roles", []):
        mode = per_role_modes.get(role, default_mode)
        variables[f"AGENT_PROMPTS_MODE_{role.upper().replace('-', '_')}"] = mode

    # Bedingte Blöcke werden als vollständige Strings vorab gebaut
    variables["DOD_REQ_BLOCK"] = _build_dod_req_block(config)
    variables["DOD_TESTS_BLOCK"] = _build_dod_tests_block(config)
    variables["A2A_HANDOFF_BLOCK"] = _build_a2a_handoff_block(config)
    variables["ANTI_RECURSION_BLOCK"] = _build_anti_recursion_block(config)

    return variables, []
```

Diese Variablen können in Modern-Templates direkt eingesetzt werden:

```xml
<constraints>
{{ANTI_RECURSION_BLOCK}}
{{DOD_REQ_BLOCK}}
{{DOD_TESTS_BLOCK}}
</constraints>
```

**Strikt getrennte Conditional-Systeme:**
- **Legacy-Templates** verwenden `{{#if VAR}}...{{/if}}` (strip_inactive_conditional_blocks) — bleibt unverändert.
- **Modern-Templates** verwenden AUSSCHLIESSLICH vorab aufgelöste Block-Variablen wie `{{DOD_REQ_BLOCK}}`, `{{DOD_TESTS_BLOCK}}`, `{{A2A_HANDOFF_BLOCK}}`, `{{ANTI_RECURSION_BLOCK}}`. `{{#if}}`-Conditionals werden in Modern-Templates **nicht unterstützt**.

Damit bleibt `substitute()` simpel und Modern-Templates sind frei von Template-Engine-Logik.

### 6.4 Source-Layout-Vorschlag

```
agents/
├── 1-generic/               # Legacy-Templates (Status Quo)
│   ├── developer.md
│   └── orchestrator.md
├── 1-generic-modern/        # Modern-Templates (neu)
│   ├── developer.md
│   └── concept-reviewer.md
├── 2-platform/              # Plattform-Overrides
└── 3-project/               # Projekt-Extensions
```

Alternativ kann der Modern-Mode auch durch ein Flag im Frontmatter gesteuert werden (`mode: modern`). Die getrennte Verzeichnisstruktur ist jedoch vorzuziehen, weil sie:
- Klar trennt, welche Templates gewartet werden müssen
- Ein einfacheres Rollback ermöglicht
- Die Pfadlogik in `sync.py` deterministisch bleibt

### 6.5 Neue Sync-Funktion für Modern-Mode

In `scripts/lib/agents.py` wird eine neue Funktion eingeführt:

```python
def _resolve_agent_source(
    role: str,
    agent_meta_root: Path,
    prompt_mode: str,
) -> Path:
    """Resolve the source template for a role considering the prompt mode.

    Order of precedence:
    1. agents/1-generic-modern/<role>.md  (only if prompt_mode == 'modern')
    2. agents/1-generic/<role>.md         (legacy / hybrid / fallback)
    3. agents/2-platform/<platform>-<role>.md
    4. agents/3-project/<role>.md
    """
    modern_path = agent_meta_root / AGENTS_DIR / "1-generic-modern" / f"{role}.md"
    legacy_path = agent_meta_root / AGENTS_DIR / GENERIC_DIR / f"{role}.md"

    if prompt_mode == "modern" and modern_path.exists():
        return modern_path
    return legacy_path
```

**Zusätzlich anzupassen:** `collect_sources()` in `scripts/lib/agents.py` iteriert heute nur über `1-generic/`, `2-platform/`, `3-project/` und `0-external/`. Das Verzeichnis `1-generic-modern/` muss zur Discovery hinzugefügt werden, sonst werden Modern-Templates nicht erkannt und nicht generiert. Dieser Eingriff ist **Pflichtbestandteil von Phase 1, Step 2**.

### 6.6 Frontmatter-Injection und A2A-Block-Zentralisierung

Der Sync-Prozess injiziert den Prompt-Mode in das generierte Frontmatter:

```yaml
---
name: developer
version: "3.0.0"
description: "..."
hint: "..."
tools: [...]
prompt_mode: modern
---
```

Das Feld `prompt_mode` ist meta-informativ und hat keinen Einfluss auf das Laufzeitverhalten des Agenten. Es erleichtert jedoch Debugging und die Admin-UI-Darstellung.

**A2A-Handoff-Block-Zentralisierung:**
Der Report empfiehlt, die immer gleichen Anti-Recursion-Guards nicht 55× hart in den Prompts zu pflegen. Stattdessen bietet `sync.py` einen zentralen Include-Mechanismus:

- Quelle: `snippets/prompt-modernization/a2a-handoff-block.md`
- Injektion als Variable `{{A2A_HANDOFF_BLOCK}}` in den `<context>`-Block jedes Modern-Mode-Agenten
- Bei Änderungen an den A2A-Rules muss nur die Snippet-Datei gepflegt werden

### 6.7 Bedingte XML-Wrapping-Logik

Die bestehende `wrap_sections_in_xml()` wird beibehalten, aber bedingt aufgerufen:

```python
if prompt_mode in ("hybrid", "modern"):
    if prompt_mode == "hybrid":
        content = wrap_sections_in_xml(content)
    # Modern-Mode verwendet native XML-Struktur, keinen zusätzlichen Wrap
```

Für den Modern-Mode wird **kein** automatisches Wrapping angewendet, weil das Template bereits die 6-Block-Struktur enthält. Stattdessen kann eine Validierungsfunktion prüfen, ob alle sechs Blöcke vorhanden sind.

### 6.8 Composition-Patch-Constraint (Blocking)

Modern-Mode-Templates dürfen in Phase 1 und Phase 2 **KEINE** `extends:`/`patches:`-Targets sein.

**Begründung:** `compose_agent()` in `scripts/lib/agents.py` arbeitet auf Markdown-Anchors (`anchor: "## Heading"`). Modern-Mode-Templates ersetzen `## Heading` durch `<workflow>` etc. Bestehende 2-platform/3-project-Patches würden brechen.

**Lösungspfad (Phase 2+):**
- `compose_agent()` um XML-Anchor-Support erweitern: `anchor: "<workflow>"`
- Danach können 2-platform/3-project-Overrides auf Modern-Templates zugreifen.

**Betroffene Dateien heute:** `agents/2-platform/agent-meta-developer.md` nutzt `extends: "1-generic/developer.md"` mit `anchor: "## Deine Zuständigkeiten"`. Diese Datei kann erst migriert werden, wenn XML-Anchors in `compose_agent()` funktionieren.

---

## 7. Mode-Switch für Rules

### 7.1 Source-Layout

Rules erhalten ebenfalls einen Mode-Switch. Es gibt zwei konkurrierende Layouts:

| Layout | Pfad | Vorteil | Nachteil |
|--------|------|---------|----------|
| Verzeichnis-basiert | `rules/1-generic/` vs. `rules/1-generic-modern/` | Klare Trennung, einfaches Rollback | Doppelte Pflege bei parallelem Betrieb |
| Frontmatter-Flag | `rules/1-generic/a2a-delegation-gates.md` mit `mode: modern` | Weniger Dateien | Sync muss Frontmatter parsen |

**Empfehlung:** Verzeichnis-basiertes Layout für Rules, analog zu `agents/1-generic-modern/`.

### 7.2 Modern-Mode-Rule-Beispiel

Das Regelwerk `a2a-delegation-gates.md` könnte im Modern Mode als XML-Struktur formuliert werden:

```xml
<rule name="a2a-delegation-gates">
  <purpose>Anti-Re-Delegation und Struktur-Schutz für A2A-Handoffs.</purpose>
  <hard_gates>
    - source_agent == target_agent → HARD REJECT
    - delegation_depth > {{A2A_MAX_DEPTH}} → HARD REJECT
    - payload.t > {{A2A_T_SIZE_LIMIT}} Zeichen → HARD REJECT
    - payload.t startet mit "Du bist..." → HARD REJECT
  </hard_gates>
  <soft_gates>
    - >{{MAX_PARALLEL_AGENTS}} Delegationen → User informieren
    - Gleicher Agent >3× für selben Intent → Schleife vermuten
  </soft_gates>
</rule>
```

### 7.3 Pfad-Mapping pro Provider via Platzhalter

Rules werden in generierte Provider-Verzeichnisse propagiert. Die Pfad-Mapping-Logik bleibt provider-agnostisch:

```yaml
# In role-defaults.yaml oder prompt-modes.yaml
rules:
  legacy_source: "rules/1-generic/"
  modern_source: "rules/1-generic-modern/"
  target_path: "{{RULES_PATH}}/"
```

Erlaubte Platzhalter in 1-generic: `{{RULES_PATH}}`, `{{EXTENSION_DIR}}`, `{{SNIPPETS_DIR}}`. Keine konkreten Provider-Pfade wie `.claude/rules/` oder `.opencode/rules/`.

---

## 8. Mode-Switch für Prompts und Templates

### 8.1 Templates

Templates in `templates/` (z. B. `claude-md-managed.md`, `SE-STRATEGY.template.md`) erhalten optional einen Modern-Mode:

```yaml
agent-prompts:
  templates:
    default: legacy
    modes:
      se-strategy: modern
      claude-md-managed: hybrid
```

### 8.2 Snippets

Snippet-Pfade in `snippets/` können ebenfalls mit einem Mode-Flag versehen werden:

```yaml
agent-prompts:
  snippets:
    default: legacy
    modes:
      developer: modern
      tester: hybrid
```

### 8.3 Provider-Agnostik

Alle Modern-Mode-Prompts, Rules und Templates in `1-generic/` müssen provider-agnostisch bleiben. Provider-Spezifika werden in `2-platform/` oder zur Sync-Zeit durch Platzhalter ersetzt.

---

## 9. Cascaden nativ im Schema

### 9.1 Frage: Sind `quality_pipelines` aus `role-defaults.yaml` die "Cascaden"?

**Antwort:** Nein — mit einer wichtigen Einschränkung.

- `quality_pipelines` in `role-defaults.yaml` und `.meta-config/project.yaml` sind **Quality-Pipelines** für den Software-Entwicklungs-Lebenszyklus (Feature, Bugfix, Refactoring, Dokumentation, SE-Kaskade).
- Sie werden von `scripts/lib/pipelines.py` geladen, zusammengeführt, validiert und in provider-spezifische Notation übersetzt.
- Der Begriff "Cascaden" im Kontext dieses Konzepts bezeichnet ein **allgemeineres Schema-Konzept** für rekursive, bedingte und stufenweise Agenten-Ausführung. Die SE-Kaskade ist ein **spezifischer Anwendungsfall** einer solchen Cascade.

**Beziehung:** `quality_pipelines` sind eine konkrete Implementierung von Cascaden-ähnlichem Verhalten, aber sie sind **kein First-Class-Schema-Konzept**. Das `cascades`-Feature in `project-config.schema.json` würde Quality-Pipelines ergänzen, nicht ersetzen.

### 9.2 Neue `cascades`-Property in `project-config.schema.json`

```json
{
  "cascades": {
    "type": "object",
    "description": "First-class cascade definitions for recursive, conditional, multi-stage agent execution.",
    "properties": {
      "definitions": {
        "type": "object",
        "additionalProperties": {
          "$ref": "#/$defs/cascadeDefinition"
        }
      },
      "bindings": {
        "type": "object",
        "description": "Bind cascade definitions to trigger roles or intents.",
        "additionalProperties": {
          "type": "string"
        }
      }
    },
    "additionalProperties": false
  }
}
```

### 9.3 Cascade-Definition Schema

```json
{
  "$defs": {
    "cascadeDefinition": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string"
        },
        "description": {
          "type": "string"
        },
        "trigger": {
          "type": "object",
          "properties": {
            "role": {
              "type": "string"
            },
            "intent": {
              "type": "string"
            }
          }
        },
        "stages": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/cascadeStage"
          }
        },
        "on_error": {
          "type": "string",
          "enum": ["escalate", "skip", "retry", "stop"]
        }
      },
      "required": ["name", "trigger", "stages"]
    },
    "cascadeStage": {
      "type": "object",
      "properties": {
        "id": {
          "type": "string"
        },
        "agent": {
          "type": "string"
        },
        "task": {
          "type": "string"
        },
        "mode": {
          "type": "string",
          "enum": ["sequential", "parallel_group", "fanout", "loop", "conditional"]
        },
        "condition": {
          "type": "object",
          "properties": {
            "type": {
              "type": "string"
            },
            "agent": {
              "type": "string"
            },
            "expression": {
              "type": "string"
            }
          }
        },
        "next": {
          "type": "object",
          "description": "Stage routing: on_success, on_failure, on_decision.",
          "properties": {
            "on_success": {
              "type": "string"
            },
            "on_failure": {
              "type": "string"
            },
            "on_decision": {
              "type": "object",
              "additionalProperties": {
                "type": "string"
              }
            }
          }
        }
      },
      "required": ["id", "agent", "task", "mode"]
    }
  }
}
```

### 9.4 Verwendung

Cascaden werden vom Orchestrator oder von spezialisierten Cascade-Runnern interpretiert. Sie sind **kein Syncer-Feature** — `sync.py` validiert sie nur gegen das Schema und stellt sie als Variablen bereit. Die Ausführung bleibt Sache des Agenten-Runtimes.

### 9.5 Phasen-Zuordnung

- **Phase 1:** JSON-Schema-Erweiterung `cascades` in `project-config.schema.json` (siehe 9.2/9.3, Anhang D).
- **Phase 3+:** Cascade-Runtime — wie Orchestrator/Runner Cascaden interpretiert, Stages ausführt, Conditions auswertet, on_error behandelt. Dieses Konzept spezifiziert die Runtime explizit **nicht**. Sie ist Gegenstand eines Folge-Konzepts.

Bis dahin sind `cascades`-Einträge in `project.yaml` Schema-validiert, aber inaktiv (keine Ausführung).

---

## 10. Prüf-Skripte

### 10.1 Übersicht

Vier neue Skripte werden eingeführt, um den Modern-Mode zu validieren und zu überwachen:

| Skript | Zweck | Integration |
|--------|-------|-------------|
| `scripts/validate-modern-templates.py` | XML-Wohlgeformtheit, TypeScript-Interface-Syntax, Pflicht-Blöcke | `sync.py --validate` |
| `scripts/token-counter.py` | Token-Vergleich Legacy vs Modern | PoC, CI |
| `scripts/check-provider-agnostic.py` | Keine Provider-Pfade in 1-generic | `sync.py --validate` |
| `scripts/audit-prompt-mode.py` | Welche Rollen haben welchen Mode | Admin-Reporting |

### 10.2 `scripts/validate-modern-templates.py`

**Zweck:** Prüft Modern-Mode-Templates auf formale Korrektheit.

**Eingabe:**
- `--role <role>`: Einzelne Rolle prüfen
- `--all`: Alle Rollen in `agents/1-generic-modern/` prüfen
- `--schema <path>`: Pfad zum JSON Schema (optional)

**Ausgabe:**
- Liste der geprüften Dateien
- Fehler pro Datei (fehlende XML-Blöcke, schlecht geformtes XML, ungültige TypeScript-Interfaces)
- Exit-Code 0 bei Erfolg, 1 bei Fehlern

**CLI-Flags:**
```bash
python scripts/validate-modern-templates.py --role developer
python scripts/validate-modern-templates.py --all --strict
```

**Exit-Codes:**
- `0`: Alle Prüfungen bestanden
- `1`: Mindestens ein Template ungültig
- `2`: Konfigurationsfehler (z. B. unbekannte Rolle)

### 10.3 `scripts/token-counter.py`

**Zweck:** Vergleicht Token-Anzahl von Legacy- und Modern-generierten Agenten.

**Eingabe:**
- `--legacy <path>`: Pfad zur Legacy-Datei
- `--modern <path>`: Pfad zur Modern-Datei
- `--role <role>`: Automatisch `.opencode/agents/<role>.md` im Legacy- und Modern-Modus generieren und vergleichen

**Ausgabe:**
```
Role: developer
Legacy tokens:  4820
Modern tokens:  3980
Reduction:      17.4 %
```

**CLI-Flags:**
```bash
python scripts/token-counter.py --role developer
python scripts/token-counter.py --legacy .opencode/agents/developer.md --modern /tmp/developer-modern.md
```

**Exit-Codes:**
- `0`: Vergleich erfolgreich
- `1`: Datei nicht gefunden
- `2`: Reduktion unter konfiguriertem Schwellenwert (wenn `--threshold 15` gesetzt)

**Schätzmethode:**
- Zeichenzahl / 4 als grobe Token-Schätzung (Englisch/Deutsch)
- Optional: Tiktoken/Claude-Tokenizer wenn verfügbar, sonst Fallback

### 10.4 `scripts/check-provider-agnostic.py`

**Zweck:** Scannt `agents/1-generic/`, `rules/1-generic/`, `templates/` und `snippets/` auf verbotene Provider-Strings.

**Verbotene Strings (Whitelist-Ansatz):**
- `.claude/`, `.opencode/`, `.gemini/`, `.continue/`, `.github/copilot/`
- `claude -a`, `task()`, `define_subagent`, `@<role>`
- Provider-Namen in Tool-Syntax: `background(agent=...)` (außerhalb von 2-platform)

**Eingabe:**
- `--path <dir>`: Zu prüfendes Verzeichnis
- `--exclude <pattern>`: Auszuschließende Dateien

**Ausgabe:**
- Liste der Verstöße mit Datei, Zeile, gefundenem String
- Exit-Code 0 wenn sauber, 1 bei Verstößen

**CLI-Flags:**
```bash
python scripts/check-provider-agnostic.py --path agents/1-generic
python scripts/check-provider-agnostic.py --path rules/1-generic --strict
```

**Exit-Codes:**
- `0`: Keine Provider-Strings gefunden
- `1`: Verstöße gefunden

### 10.5 `scripts/audit-prompt-mode.py`

**Zweck:** Zeigt für jede aktive Rolle den aktuellen Prompt-Mode an.

**Eingabe:**
- `--config <path>`: Pfad zur `.meta-config/project.yaml`
- `--format table|json|csv`

**Ausgabe:**
```
ROLE              MODE     SOURCE
orchestrator      hybrid   project.yaml
developer         modern   project.yaml
concept-reviewer  legacy   default
```

**CLI-Flags:**
```bash
python scripts/audit-prompt-mode.py --config .meta-config/project.yaml
python scripts/audit-prompt-mode.py --format json
```

**Exit-Codes:**
- `0`: Audit erfolgreich
- `1`: Konfigurationsdatei nicht gefunden

### 10.6 Integration in `sync.py --validate`

`sync.py --validate` ruft bei aktiviertem Modern-Mode für mindestens eine Rolle automatisch auf:

1. `validate-modern-templates.py --all`
2. `check-provider-agnostic.py --path agents/1-generic --strict`
3. `audit-prompt-mode.py --format json`

---

## 11. Zentrale und projektspezifische Mode-Definition

### 11.1 Auflösungskette

Die Mode-Definition folgt einer kaskadierenden Auflösung:

```
project.yaml > role-defaults.yaml (oder prompt-modes.yaml) > hardcoded Legacy
```

| Ebene | Datei | Gilt für |
|-------|-------|----------|
| Projekt | `.meta-config/project.yaml → agent-prompts` | Einzelnes Projekt |
| Zentral | `agent-meta/config/prompt-modes.yaml` (neu) | Alle Projekte, die agent-meta syncen |
| Fallback | Hardcoded in `scripts/lib/config.py` | Legacy, wenn nichts konfiguriert |

### 11.2 Zentrale Konfiguration: `config/prompt-modes.yaml`

```yaml
# agent-meta/config/prompt-modes.yaml
# Framework-weite Defaults für Prompt-Modes.
# Wird von role-defaults.yaml oder project.yaml überschrieben.

agent-prompts:
  default: legacy
  modes:
    developer: legacy
    orchestrator: legacy

rules:
  default: legacy
  modes:
    a2a-delegation-gates: legacy

snippets:
  default: legacy
  modes: {}

templates:
  default: legacy
  modes: {}
```

### 11.3 Projektspezifische Konfiguration: `.meta-config/project.yaml`

```yaml
agent-prompts:
  default: legacy
  modes:
    developer: modern
    orchestrator: hybrid

rules:
  default: legacy
  modes:
    a2a-delegation-gates: modern

snippets:
  default: legacy
  modes:
    developer: modern

templates:
  default: legacy
  modes:
    se-strategy: modern
```

### 11.4 Hardcoded Fallback

Wenn weder `project.yaml` noch `prompt-modes.yaml` einen Mode definieren, fällt `sync.py` auf `legacy` zurück. Das garantiert Rückwärtskompatibilität für alle bestehenden Projekte.

---

## 12. Provider-Agnostik-Garantie

### 12.1 Whitelist erlaubter Pfade in `1-generic`

In allen `1-generic`-Inhalten (Agenten, Rules, Prompts, Templates, Snippets) dürfen nur folgende Platzhalter für Pfade verwendet werden:

| Platzhalter | Bedeutung |
|-------------|-----------|
| `{{EXTENSION_DIR}}` | Projekt-spezifische Extension-Dateien |
| `{{SNIPPETS_DIR}}` | Code-Snippets für Sprach-Best-Practices |
| `{{RULES_PATH}}` | Provider-spezifischer Rules-Ordner |
| `{{AGENTS_DIR}}` | Provider-spezifischer Agenten-Ordner |
| `{{ARTIFACTS_DIR}}` | Temporäre Artifact-Ablage |

### 12.2 Verbotene Strings

`scripts/check-provider-agnostic.py` scannt auf:

- Konkrete Provider-Verzeichnisse: `.claude/`, `.opencode/`, `.gemini/`, `.continue/`, `.github/copilot/`
- Provider-spezifische Tool-Syntax: `claude -a`, `task()`, `define_subagent`, `@<role>`
- Provider-Namen in imperativen Kontexten: `background(agent=...)`, `invoke_subagent(...)`

Ausnahmen:
- Dokumentation in `docs/` darf Provider-Namen nennen, wenn sie erklärend sind.
- `agents/2-platform/`, `rules/2-platform/` und Provider-spezifische Konfigurationen sind von diesem Scan ausgenommen.

### 12.3 Integration in `sync.py --validate`

Der Provider-Agnostik-Check ist Teil des Standard-Validierungslaufs:

```bash
python scripts/sync.py --validate
# → check-provider-agnostic.py --path agents/1-generic --strict
```

---

## 13. Admin-UI-Roadmap (separat vom PoC)

### 13.1 Admin-UI-Abhängigkeit

Die Admin-UI ist laut `admin-ui-concept.md` erst Phase 5 (>20 Tage entfernt). Daher werden Admin-UI-Features in diesem Konzept nur als Roadmap-Einträge geführt und sind **nicht Teil des 1-Wochen-PoC**.

### 13.2 Geplante Admin-UI-Erweiterungen

| Feature | Phase | Beschreibung |
|---------|-------|--------------|
| Prompt-Mode Matrix | Phase 4 | Sidebar-Section "Prompt Mode" mit Dropdown pro Rolle |
| Template-Editor Toggle | Phase 5 | "Edit as Markdown" vs. "Edit as XML" im Super-Admin-Bereich |
| Warnungen | Phase 4 | Fehlende Modern-Templates, unvollständige 6-Block-Struktur |
| Viz-Badge | Phase 4 | Farbcodierung pro Prompt-Mode im Agenten-Graphen |

### 13.3 PoC-Validierung ohne Admin-UI

Der PoC wird ausschließlich über Kommandozeile validiert:

```bash
python scripts/sync.py
python scripts/token-counter.py --role developer
python scripts/validate-modern-templates.py --role developer
python scripts/check-provider-agnostic.py --path agents/1-generic-modern
```

---

## 14. Viz-Feature-Änderungen

### 14.1 Agent-Hierarchy erweitern

Die Funktion `build_agent_hierarchy()` in `scripts/lib/viz.py` muss den `prompt_mode` pro Node mitführen:

```python
def build_agent_hierarchy(agent_meta_root: Path, project_root: Path, config: dict) -> dict:
    # ... bestehende Logik ...
    prompt_config = config.get("agent-prompts", {})
    default_mode = prompt_config.get("default", "legacy")
    per_role_modes = prompt_config.get("modes", {})

    for role in roles:
        nodes.append({
            "id": role,
            "label": role,
            "tier": role_tiers.get(role, "optional"),
            "prompt_mode": per_role_modes.get(role, default_mode),
            # ... weitere Felder ...
        })
```

### 14.2 Badge und Farbcodierung

In `docs/agent-graph.html` und `docs/live-dashboard.html` wird pro Node ein Badge angezeigt:

| Mode | Badge | Farbe |
|------|-------|-------|
| Legacy | L | Grau (`#868e96`) |
| Hybrid | H | Gelb (`#ffd43b`) |
| Modern | M | Grün (`#69db7c`) |

### 14.3 Neuer Event-Typ `prompt-mode-changed`

Das Viz-Event-System erhält einen neuen Event-Typ:

```json
{
  "timestamp": "2026-06-28T14:32:00Z",
  "event": "prompt-mode-changed",
  "role": "developer",
  "old_mode": "legacy",
  "new_mode": "modern",
  "source": "admin-ui"
}
```

---

## 15. Test-Strategie

### 15.1 Unit-Tests

Neue Tests unter `tests/test_prompt_modes.py`:

```python
import pytest
from pathlib import Path
from scripts.lib.config import build_variables
from scripts.lib.agents import _resolve_agent_source, wrap_sections_in_xml


def test_build_variables_injects_prompt_mode_vars():
    config = {
        "roles": ["developer", "orchestrator"],
        "agent-prompts": {
            "default": "legacy",
            "modes": {"developer": "modern"}
        }
    }
    variables, _ = build_variables(config, Path("."))
    assert variables["AGENT_PROMPTS_MODE_DEVELOPER"] == "modern"
    assert variables["AGENT_PROMPTS_MODE_ORCHESTRATOR"] == "legacy"


def test_resolve_agent_source_prefers_modern_when_configured():
    root = Path("agents")
    # Mocks setzen ...
    src = _resolve_agent_source("developer", root, "modern")
    assert "1-generic-modern" in str(src)


def test_wrap_sections_in_xml_closes_sections():
    content = "## A\nText\n## B\nMore"
    wrapped = wrap_sections_in_xml(content)
    assert "<section name=\"a\">" in wrapped
    assert "</section>" in wrapped
```

### 15.2 Integrationstests

```bash
# Standard-Sync mit Default (Legacy)
python scripts/sync.py --dry-run

# Modern-Mode für developer aktivieren
python scripts/sync.py --dry-run --mode modern --roles developer

# Validierung aller generierten Agenten
python scripts/sync.py --validate
```

### 15.3 Token-Counter-Skript

`scripts/token-counter.py` wird im PoC eingesetzt, um Legacy- und Modern-Version von `developer.md` zu vergleichen (siehe Abschnitt 10.3).

### 15.4 PoC-Validierung

Der PoC wird anhand folgender Kriterien bewertet:

| Kriterium | Messmethode | Ziel |
|-----------|-------------|------|
| Token-Reduktion | `scripts/token-counter.py --role developer` | 15–20 % |
| Regeltreue | Test-Task vor/nachher | Keine Regressions |
| Halluzinationen | Stichprobe von 10 Outputs | Keine Beispieldaten in Output |
| XML-Struktur | `scripts/validate-modern-templates.py --role developer` | Alle 6 Blöcke vorhanden |

---

## 16. Cascaden-Schema-Spezifikation

### 16.1 Ziel

Cascaden sind ein First-Class-Schema-Konzept für rekursive, bedingte und stufenweise Agenten-Ausführung. Sie ergänzen die bestehenden `quality_pipelines` und ermöglichen es, komplexe Abläufe deklarativ zu beschreiben.

### 16.2 Schema

Siehe Abschnitt 9.3 für die vollständige JSON-Schema-Definition.

### 16.3 Beispiel: SE-Kaskade als Cascade

```yaml
cascades:
  definitions:
    se-recursive-decomposition:
      name: "SE Recursive Decomposition"
      description: "Zig-Zag Requirements ↔ Architecture bis Leaf-Level"
      trigger:
        role: orchestrator
        intent: se-cascade
      stages:
        - id: l0-stakeholder
          agent: se-requirements
          task: "Stakeholder Needs → formal SN-xxx Requirements"
          mode: loop
          condition:
            type: max_iterations
            expression: "{{SE_MAX_CRITIC_ITERATIONS}}"
          next:
            on_success: l1-requirements
        - id: l1-requirements
          agent: se-requirements
          task: "L1 System Requirements (REQ-L1) from Stakeholder Needs"
          mode: loop
          next:
            on_success: l1-architecture
        - id: l1-architecture
          agent: se-architect
          task: "L1 System White-Box Decomposition (ARCH-L1)"
          mode: loop
          next:
            on_success: termination
        - id: termination
          agent: se-termination
          task: "Per-system leaf/continue decision"
          mode: conditional
          condition:
            type: agent_decision
            agent: se-termination
          next:
            on_decision:
              continue: "spawn_next_level"
              leaf: implementation
        - id: implementation
          agent: orchestrator
          task: "Route leaf components to implementation"
          mode: fanout
      on_error: escalate
```

### 16.4 Verhältnis zu `quality_pipelines`

| Aspekt | `quality_pipelines` | `cascades` |
|--------|---------------------|------------|
| Zweck | Software-Lifecycle-Pipelines | Beliebige rekursive/bedingte Abläufe |
| Schema-Status | Implementiert | Neu als First-Class-Konzept |
| Ausführung | `scripts/lib/pipelines.py` | Noch zu definieren (Cascade Runner) |
| Beispiel | `standard-feature`, `bugfix` | `se-recursive-decomposition` |

### 16.5 Sync-Integration

`sync.py` validiert `cascades` gegen `project-config.schema.json` und injiziert sie als kompakte Variablen in den Orchestrator. Die tatsächliche Ausführung obliegt dem Agenten-Runtime.

### 16.6 Runtime-Scope

Phase 1 liefert ausschließlich das Schema. Die Cascade-Runtime (Orchestrator-Interpretation, Stage-Ausführung, Condition-Evaluation, Error-Handling) ist explizit **Phase 3+** und wird in einem Folge-Konzept spezifiziert.

Bis dahin sind `cascades`-Einträge in `project.yaml` Schema-validiert, aber inaktiv (keine Ausführung).

---

## 17. Erweiterungs-Matrix

### 17.1 Mode × Komponente × Trigger

| Komponente | Legacy Mode | Hybrid Mode | Modern Mode | Trigger / Konfiguration |
|------------|-------------|-------------|-------------|-------------------------|
| Agenten-Templates | `agents/1-generic/` | `agents/1-generic/` + `wrap_sections_in_xml()` | `agents/1-generic-modern/` | `agent-prompts.modes.<role>` |
| Rules | `rules/1-generic/` | `rules/1-generic/` + Wrapper | `rules/1-generic-modern/` | `agent-prompts.rules.modes.<rule>` |
| Snippets | `snippets/` | `snippets/` | `snippets/<mode>/` | `agent-prompts.snippets.modes.<role>` |
| Templates | `templates/` | `templates/` | `templates/<mode>/` | `agent-prompts.templates.modes.<name>` |
| Cascaden | `quality_pipelines` | `quality_pipelines` | `cascades` | `cascades.definitions` |

### 17.2 Interaktionen

- **Agent Modern + Rule Legacy:** Erlaubt. Die Rule wird normal in das generierte Agenten-Dokument eingebettet.
- **Agent Legacy + Rule Modern:** Nicht empfohlen, aber technisch möglich. Die XML-Rule würde in Markdown eingebettet.
- **Agent Modern + Cascaden:** Modern-Templates erhalten Cascaden-Informationen als kompakte TypeScript-Interfaces im `<context>`-Block.
- **Hybrid + Modern gleichzeitig:** Pro Rolle nur ein Mode möglich.

---

## 18. PoC-Plan (1 Woche)

### 18.1 Entscheidung: PoC-Agent

**Gewählt: `developer`**

| Kandidat | Für | Gegen | Entscheidung |
|----------|-----|-------|--------------|
| `orchestrator` | Hoher Impact, zentrale Rolle | 849 LOC, viele Subsysteme, Fehler wirkt sich systemweit aus, schwer zu validieren | Abgelehnt |
| `developer` | Klarer Scope (197 LOC), alle Struktur-Elemente vorhanden, einfache Validierung, geringer Blast-Radius | Niedrigerer Gesamtimpact als Orchestrator | **Gewählt** |

### 18.2 Schritt-für-Schritt-Anleitung (Steps 1–6)

**Schritt 1 — Branch anlegen**

```bash
git checkout -b feat/prompt-modernization-poc
git push -u origin feat/prompt-modernization-poc
```

**Schritt 2 — Config-Section einführen**

- `config/project-config.schema.json` um `agent-prompts` erweitern
- Optional: `config/prompt-modes.yaml` als zentrale Default-Datei anlegen
- `scripts/lib/config.py` um `AGENT_PROMPTS_MODE_<ROLE>` erweitern

**Schritt 3 — Source-Layout vorbereiten**

```bash
mkdir -p agents/1-generic-modern
```

**Schritt 4 — Modern-Template für `developer` erstellen**

- `agents/1-generic-modern/developer.md` nach 6-Block-Template schreiben
- TypeScript-Interfaces für A2A-Handoff integrieren
- Constraints am Ende platzieren
- Version auf `3.0.0` setzen (Major-Bump wegen neuer Struktur)

**Schritt 5 — Sync-Logik erweitern**

- `_resolve_agent_source()` in `scripts/lib/agents.py` implementieren
- `collect_sources()` um `1-generic-modern/` als Discovery-Pfad erweitern (Pflicht — sonst keine Modern-Template-Generierung)
- Frontmatter-Injection `prompt_mode: <mode>` in das generierte Frontmatter aufnehmen

Kein zusätzliches XML-Wrapping nötig: Hybrid läuft bereits über das existierende Flag `xml-section-wrapping: enabled: true` (`agents.py:941–944`); Modern-Templates enthalten die XML-Struktur nativ.

**Schritt 6 — PoC-Projekt konfigurieren, syncen und validieren**

In `.meta-config/project.yaml`:

```yaml
agent-prompts:
  default: legacy
  modes:
    developer: modern
```

```bash
python scripts/sync.py --dry-run
python scripts/sync.py
python scripts/token-counter.py --role developer
python scripts/validate-modern-templates.py --role developer
python scripts/check-provider-agnostic.py --path agents/1-generic-modern
```

### 18.3 Definition of Done (PoC)

- [ ] `developer` wird im Modern Mode generiert
- [ ] Generierte Datei enthält alle 6 XML-Blöcke
- [ ] TypeScript-Interfaces sind syntaktisch korrekt enthalten
- [ ] Token-Reduktion 15–20 % gegenüber Legacy
- [ ] Keine funktionale Regression im Test-Task
- [ ] `sync.py --validate` erfolgreich
- [ ] Provider-Agnostik-Check bestanden

### 18.4 Phase 1 vs. Phase 2+

| Phase | Umfang | Dauer |
|-------|--------|-------|
| **Phase 1 (PoC)** | Config + Template + Sync + Token-Vergleich | 1 Woche |
| **Phase 2+** | Test-Tasks, Admin-UI-Integration, Doku, weitere Rollen | Nach PoC-Review |

Test-Tasks, Admin-UI-Integration und vollständige Dokumentation sind **nicht** Teil der 1-Wochen-Phase.

---

## 19. Migrations-Roadmap

### 19.1 Phase 1 — PoC (1 Woche)

| Task | Aufwand | Owner |
|------|---------|-------|
| `agent-prompts`-Sektion in Schema und Config einführen | 1 Tag | senior-developer |
| `AGENT_PROMPTS_MODE_<ROLE>` in `build_variables()` | 0.5 Tage | senior-developer |
| `_resolve_agent_source()` und bedingtes Wrapping | 1 Tag | senior-developer |
| Modern-Template `developer.md` erstellen | 2 Tage | senior-developer |
| Prüf-Skripte `token-counter.py` und `check-provider-agnostic.py` implementieren | 1 Tag | developer |
| Sync und Validierung | 1 Tag | senior-developer |

> **Nicht in Phase 1:** `validate-modern-templates.py` und `audit-prompt-mode.py` — verschoben in Phase 2. `rules/1-generic-modern/` — verschoben in Phase 3. Cascaden-Runtime — Phase 3+.

### 19.2 Phase 2 — Erste Rollout-Welle + Composition-Support (2.5 Wochen)

Ziel: 5–8 weitere Agenten modernisieren + Composition-Patches kompatibel machen.

Priorisierung:
- Hoher Token-Einsparung (`concept-reviewer`, `agent-meta-manager`)
- Klarem Scope (`junior-developer`, `git`, `feedback`)
- Hoher Nutzungshäufigkeit (`developer`, `code-reviewer`)

| Task | Aufwand | Owner |
|------|---------|-------|
| `compose_agent()` um XML-Anchor-Support erweitern (`anchor: "<workflow>"`) — Voraussetzung für 2-platform-Overrides auf Modern-Templates | 2 Tage | senior-developer |
| `concept-reviewer` modernisieren | 2 Tage | senior-developer |
| `agent-meta-manager` modernisieren | 2 Tage | senior-developer |
| `git`, `feedback`, `documenter` modernisieren | 2 Tage | developer |
| Integrationstests | 2 Tage | tester |
| `audit-prompt-mode.py` und Reporting | 1 Tag | developer |
| `validate-modern-templates.py` (XML-Wohlgeformtheit, 6-Block-Check) | 1 Tag | developer |

### 19.3 Phase 3 — Admin-UI, Viz, Rules-Mode-Switch & Cascade-Runtime-Konzept (2.5 Wochen)

| Task | Aufwand | Owner |
|------|---------|-------|
| Prompt-Mode Matrix im Schema-Form-Generator | 2 Tage | senior-developer |
| Viz-Badge und Farbcodierung | 1.5 Tage | developer |
| Event-Typ `prompt-mode-changed` | 1 Tag | developer |
| Template-Editor Toggle (Super-Admin) | 2 Tage | senior-developer |
| Rules-Mode-Switch (`rules/1-generic-modern/`) implementieren | 2 Tage | senior-developer |
| Cascade-Runtime-Konzept ausarbeiten (Folge-Konzept) | 3 Tage | architect / senior-developer |

### 19.4 Phase 4 — Orchestrator-Modernisierung (3 Wochen)

Der Orchestrator wird bewusst spät migriert, weil er das komplexeste Template ist:

| Task | Aufwand | Owner |
|------|---------|-------|
| SE-Mode in Extension extrahieren | 3 Tage | senior-developer |
| Routing-Matrix komprimieren | 2 Tage | senior-developer |
| Anti-Recursion/Constraints in `<constraints>`-Block | 2 Tage | senior-developer |
| TypeScript-Contracts für A2A integrieren | 2 Tage | senior-developer |
| Umfassende Integrationstests | 3 Tage | tester |
| Review und Feinschliff | 2 Tage | concept-reviewer |

### 19.5 Phase 5 — Snippets/Templates-Mode-Switch, Rollout & Cleanup (2.5 Wochen)

- Snippets-Mode-Switch (`snippets/<mode>/`) einführen
- Templates-Mode-Switch (`templates/<mode>/`) einführen
- Restliche Agenten modernisieren oder auf Hybrid setzen
- Legacy-Templates als `deprecated` markieren, falls Modern-Variante existiert
- Dokumentation aktualisieren (`CLAUDE.md`, `AGENTS.md`, `CODEBASE_OVERVIEW.md`)
- Major-Version-Bump von agent-meta (wegen neuer Default-Verhaltensmöglichkeiten)

### 19.6 Geschätzte Gesamtzeit

| Phase | Dauer |
|-------|-------|
| Phase 1 (PoC) | 1 Woche |
| Phase 2 (Rollout-Welle + Composition-Support) | 2.5 Wochen |
| Phase 3 (Admin-UI, Viz, Rules, Cascade-Runtime-Konzept) | 2.5 Wochen |
| Phase 4 (Orchestrator) | 3 Wochen |
| Phase 5 (Snippets/Templates/Rollout & Cleanup) | 2.5 Wochen |
| **Gesamt** | **~11.5 Wochen** |

---

## 20. Risiken & offene Fragen

### 20.1 Risiken

| Risiko | Impact | Wahrscheinlichkeit | Mitigation |
|--------|--------|-------------------|------------|
| XML in YAML-Frontmatter Round-Trip mit PyYAML | Hoch | Mittel | Tests für `_update_frontmatter_dict()` erweitern; XML-Blöcke nach Frontmatter platzieren |
| Extensions (3-project) sind mit Modern Mode inkompatibel | Mittel | Mittel | Extensions werden nach dem Modern-Template geladen; Composition-Patches müssen XML-Blöcke respektieren |
| Test-Repository-Workflow bricht | Hoch | Niedrig | PoC zuerst im agent-meta-Repo selbst; danach in einem Zielrepo testen |
| Provider-spezifische XML-Strukturen | Mittel | Niedrig | 1-generic-modern bleibt provider-agnostisch; Provider-Spezifika in 2-platform |
| TypeScript vs. TOON | Niedrig | Niedrig | Für A2A-Contracts bleibt TypeScript; TOON nur für große Input-Daten evaluieren |
| Hybrid-Mode wird zur Falle | Mittel | Mittel | Klare Kommunikation: Hybrid ist Übergang, nicht Endzustand; Modern-Mode für wichtige Rollen forcieren |
| `collect_sources()` kennt `1-generic-modern/` nicht — Discovery-Erweiterung in Phase 1 nötig, sonst keine Modern-Templates generiert | Hoch | Sicher (Tatsache, kein Risiko) | In Phase 1, Step 2 adressiert: `collect_sources()` um Modern-Pfad erweitern |

### 20.2 Offene Fragen

1. **Soll `1-generic-modern/` ein eigenes Verzeichnis erhalten, oder reicht ein Frontmatter-Flag?**
   - **Entschieden:** Eigenes Verzeichnis für klare Trennung, deterministischer Sync-Pfad und einfaches Rollback.

2. **Wie werden Composition-Patches (2-platform, 3-project) im Modern Mode behandelt?**
   - **Entschieden:** In Phase 1+2 sind Modern-Templates KEINE `extends:`/`patches:`-Targets (Constraint, siehe Abschnitt 6.8). In Phase 2 wird `compose_agent()` um XML-Anchor-Support (`anchor: "<workflow>"`) erweitert. Danach können 2-platform/3-project-Overrides auf Modern-Templates zugreifen.

3. **Soll der Hybrid-Mode der neue Default werden?**
   - Vorschlag: Nein — erst nach erfolgreichem PoC und Rollout-Welle diskutieren.

4. **Wie verhält sich `wrap_sections_in_xml()` zu bestehenden Code-Blöcken innerhalb von Sektionen?**
   - Antwort: Code-Fences werden nicht verändert; der Wrapper arbeitet nur auf `##`-Ebene.

5. **Soll die `prompt_mode`-Frontmatter-Variable in den generierten Agenten sichtbar sein?**
   - Vorschlag: Ja, als Meta-Information für Debugging und UI.

6. **Soll `config/prompt-modes.yaml` als separate Datei oder als Teil von `role-defaults.yaml` geführt werden?**
   - Vorschlag: Separate Datei für klare Trennung der Prompt-Mode-Defaults von Rollen-Definitionen.

---

## 21. Kompatibilitäts-Matrix

| Komponente | Legacy Mode | Hybrid Mode | Modern Mode | Hinweis |
|------------|-------------|-------------|-------------|---------|
| `agents/1-generic/*.md` | Vollständig | Quelle | Fallback | Unverändert nutzbar |
| `agents/1-generic-modern/*.md` | Nicht genutzt | Nicht genutzt | Quelle | Muss erstellt werden |
| `agents/2-platform/*.md` | Vollständig | Vollständig | Vollständig | Patches müssen Zielstruktur kennen |
| `agents/3-project/*.md` | Vollständig | Vollständig | Bedingt | Extension-Anchor muss passen |
| `scripts/lib/agents.py` | Vollständig | `wrap_sections_in_xml()` | `_resolve_agent_source()` | Erweiterungen nötig |
| `scripts/lib/config.py` | Vollständig | Variablen | Variablen | `AGENT_PROMPTS_MODE_*`, bedingte Blöcke |
| `config/project-config.schema.json` | Vollständig | Schema-Erweiterung | Schema-Erweiterung | Neue `agent-prompts`-Sektion, `cascades` |
| `.meta-config/project.yaml` | Vollständig | Optional | Optional | Default bleibt `legacy` |
| Admin-UI | Vollständig | Anzeige | Editor + Matrix | Erweiterungen in Phase 3 |
| Viz / `agent-graph.html` | Vollständig | Badge | Badge | Erweiterungen in Phase 3 |
| `sync.py --validate` | Vollständig | Vollständig | Validierung 6 Blöcke + Provider-Agnostik | Erweiterung nötig |
| A2A-Handoff Protocol | JSON-Beispiele | JSON-Beispiele | TypeScript-Interfaces | Modern Mode bevorzugt |
| Critical Rules Footer | Am Ende | Am Ende | In `<constraints>` | Mechanismus beibehalten |
| Cascaden / Quality-Pipelines | `quality_pipelines` | `quality_pipelines` | `cascades` + `quality_pipelines` | Cascaden ergänzen Pipelines |

---

## 22. Anhang A: XML-Template-Beispiel

### 22.1 Modern-Mode-Template: `developer`

```markdown
---
name: template-developer
version: "3.0.0"
description: "Implementiert Features und Bugfixes im Modern Mode mit XML-Struktur und TypeScript-Contracts."
hint: "Feature-Implementierung und Bugfixes nach REQ-IDs"
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - TodoWrite
  - Agent
prompt_mode: modern
---

<persona>
Du bist der **Developer** für {{PROJECT_NAME}} — implementierst Features und Bugfixes.
Kommunikation auf Deutsch. Code-Kommentare und Commit-Messages auf {{CODE_LANGUAGE}}.
</persona>

<workflow>
1. **Eingang prüfen:** Falls A2A-Envelope vorhanden → parse `payload.t`, `ctx`, `con`, `refs`, `pri`.
2. **REQ-Check:** {{DOD_REQ_BLOCK}}
3. **Scope erfassen:** Minimale Änderung identifizieren — nur was die Aufgabe verlangt.
4. **Implementieren:** Code-Konventionen und Sprach-Best-Practices strikt einhalten.
5. **Validieren:** Bestehende Tests dürfen nicht brechen. {{DOD_TESTS_BLOCK}}
6. **Rückgabe:** Ergebnis im `IResult`-Format (siehe `<output_contract>`).
</workflow>

<context>
**Projektkontext:**
{{PROJECT_CONTEXT}}

**Ziel:** {{PROJECT_GOAL}}
**Sprachen:** {{PROJECT_LANGUAGES}}

{{A2A_HANDOFF_BLOCK}}

**HITL:** Bei `requires_human_approval: true` VOR Ausführung fragen:
> "[payload.t]. Ausführen? (yes/no)"
</context>

<tools>
- **Read** — Dateien lesen
- **Write** — Neue Dateien erstellen
- **Edit** — Bestehende Dateien ändern
- **Bash** — Build/Test/Shell-Kommandos
- **Glob/Grep** — Code-Recherche
- **TodoWrite** — Fortschritt tracken
- **Agent** — Delegation an andere Rollen (nur wenn explizit erlaubt)
</tools>

<output_contract>
Standard-Rückgabe:
```
STATUS: done|partial|failed|escalate
RESULT: <1-Satz-Zusammenfassung>
ARTIFACTS: <geänderte Dateien, optional>
ERRORS: <leer wenn keiner>
```

Bei Eskalation:
```
STATUS: escalate
RESULT: <was abgeschlossen>
ESCALATE_REASON: <kurz>
RECOMMENDED_TIER: <junior-developer|developer|senior-developer>
PARTIAL_WORK: <was bereits erledigt>
NEXT_STEPS: <konkrete nächste Schritte>
```
</output_contract>

<constraints>
{{ANTI_RECURSION_BLOCK}}
- KEINE Default-Exports
- KEINE Secrets / API-Keys im Code
{{DOD_REQ_BLOCK}}
{{DOD_TESTS_BLOCK}}
- Bei Unklarheit User fragen, nicht raten
</constraints>
```

### 22.2 Hybrid-Mode-Ausgabe (Auszug)

Wenn `developer` auf `hybrid` gesetzt ist, würde der bestehende Legacy-Inhalt automatisch so aussehen:

```xml
<section name="deine-zustaendigkeiten">
### 1. Feature-Implementierung
- Minimal implementieren — nur was die Aufgabe verlangt
- Code-Konventionen einhalten (siehe unten)
</section>

<section name="commit-konventionen">
→ Vollständige Regeln: Globale Rule "commit-conventions.md" anwenden.
</section>
```

---

## 23. Anhang B: TypeScript-Interface-Beispiele

### 23.1 Vollständige A2A-Handoff-Definitionen

```typescript
// ============================================================
// A2A Handoff TypeScript Contracts — agent-meta Modern Mode
// ============================================================

/** Compact payload field names for FANOUT scenarios. */
interface IPayloadCompact {
  t: string;        // task
  ctx?: unknown;    // context
  con?: string[];   // constraints
  refs?: string[];  // references
  pri?: 'low' | 'medium' | 'high' | 'critical';
  dep?: string[];   // dependencies
}

/** Verbose payload field names for human-readable contexts. */
interface IPayloadVerbose {
  task: string;
  context?: unknown;
  constraints?: string[];
  references?: string[];
  priority?: 'low' | 'medium' | 'high' | 'critical';
  dependencies?: string[];
}

type IPayload = IPayloadCompact | IPayloadVerbose;

/** Envelope wrapping every delegation. */
interface IEnvelope {
  protocol_version: '1.0.0';
  handoff_id: string;
  source_agent: string;
  target_agent: string;
  schema_ref: string;
  payload: IPayload | IPayload[];
  trace_parent?: string | null;
}

/** Batch envelope for FANOUT to the same agent type. */
interface IBatchEnvelope extends Omit<IEnvelope, 'payload'> {
  batch: true;
  payload: Array<IPayloadCompact & { batch_task_id: string }>;
}

/** Standard result returned by every worker agent. */
interface IResult {
  status: 'done' | 'partial' | 'failed' | 'escalate';
  result: string;
  artifacts?: string[];
  errors?: string[];
}

/** Escalation or partial result with next-step guidance. */
interface IEscalation extends IResult {
  status: 'escalate' | 'partial';
  escalate_reason: string;
  recommended_tier: string;
  partial_work: string;
  next_steps: string[];
}

/** Lightweight artifact reference for BARRIER() aggregation. */
interface IArtifactReference {
  agent: string;
  result_key: string;
  artifact_path: string;
  summary: string;
}
```

### 23.2 Verwendung im Prompt

Im Modern-Mode-Template wird nicht das gesamte JSON-Beispiel eingebettet, sondern nur die Interfaces:

```markdown
<output_contract>
Gib Ergebnisse in diesem Format zurück:

```typescript
interface IResult {
  status: 'done' | 'partial' | 'failed' | 'escalate';
  result: string;      // 1-Satz-Zusammenfassung
  artifacts?: string[];
  errors?: string[];
}
```

Keine Einleitung, kein Fazit — nur das reine Format.
</output_contract>
```

### 23.3 Mapping zu bestehenden JSON-Schemas

| TypeScript-Interface | JSON Schema | Datei |
|----------------------|-------------|-------|
| `IEnvelope` | Envelope | `schemas/a2a-handoff.schema.json` |
| `IPayload` | Task Spec | `schemas/handoffs/task-spec.schema.json` |
| `IResult` | Dev Result | `schemas/handoffs/dev-result.schema.json` |

Die TypeScript-Interfaces dienen der **menschlichen/modellseitigen Kommunikation** im Prompt. Die JSON-Schemas bleiben die verbindliche Maschinen-Validierung. Bei Bedarf kann `sync.py` die Interfaces automatisch aus den JSON-Schemas generieren.

---

## 24. Anhang C: Rules Modern Mode Beispiel

### 24.1 `rules/1-generic-modern/a2a-delegation-gates.md`

```xml
---
name: a2a-delegation-gates
mode: modern
---

<rule>
<purpose>
Anti-Re-Delegation und Struktur-Schutz für A2A-Handoffs.
</purpose>

<hard_gates>
- source_agent == target_agent → HARD REJECT (Self-Handoff verboten)
- delegation_depth > {{A2A_MAX_DEPTH}} → HARD REJECT
- payload.t > {{A2A_T_SIZE_LIMIT}} Zeichen → HARD REJECT
- payload.t startet mit "Du bist" / "Du bist ein" / "Du bist eine" → HARD REJECT
</hard_gates>

<soft_gates>
- >{{MAX_PARALLEL_AGENTS}} Delegationen → User informieren
- Gleicher Agent >3× für selben Intent → Schleife vermuten, User informieren
- Gleicher Agent >5× gesamt → Task-Komplexität prüfen
</soft_gates>

<validation>
Prüfe VOR jedem Dispatch:
1. source_agent != target_agent
2. delegation_depth <= {{A2A_MAX_DEPTH}}
3. payload.t <= {{A2A_T_SIZE_LIMIT}} Zeichen
4. payload.t beginnt nicht mit "Du bist..."
</validation>
</rule>
```

### 24.2 Pfad-Mapping

```yaml
# In project.yaml oder prompt-modes.yaml
rules:
  source:
    legacy: "rules/1-generic/"
    modern: "rules/1-generic-modern/"
  target: "{{RULES_PATH}}/"
```

---

## 25. Anhang D: JSON-Schema-Erweiterung

### 25.1 Neue Properties `agent-prompts` und `cascades`

```json
{
  "agent-prompts": {
    "type": "object",
    "description": "Controls prompt generation mode per role, rule, snippet and template.",
    "properties": {
      "default": {
        "type": "string",
        "enum": ["legacy", "hybrid", "modern"],
        "default": "legacy"
      },
      "modes": {
        "type": "object",
        "description": "Per-role prompt mode override.",
        "additionalProperties": {
          "type": "string",
          "enum": ["legacy", "hybrid", "modern"]
        }
      },
      "rules": {
        "type": "object",
        "properties": {
          "default": { "type": "string", "enum": ["legacy", "hybrid", "modern"], "default": "legacy" },
          "modes": { "type": "object", "additionalProperties": { "type": "string", "enum": ["legacy", "hybrid", "modern"] } }
        }
      },
      "snippets": {
        "type": "object",
        "properties": {
          "default": { "type": "string", "enum": ["legacy", "hybrid", "modern"], "default": "legacy" },
          "modes": { "type": "object", "additionalProperties": { "type": "string", "enum": ["legacy", "hybrid", "modern"] } }
        }
      },
      "templates": {
        "type": "object",
        "properties": {
          "default": { "type": "string", "enum": ["legacy", "hybrid", "modern"], "default": "legacy" },
          "modes": { "type": "object", "additionalProperties": { "type": "string", "enum": ["legacy", "hybrid", "modern"] } }
        }
      }
    },
    "additionalProperties": false
  },
  "cascades": {
    "type": "object",
    "description": "First-class cascade definitions for recursive, conditional, multi-stage agent execution.",
    "properties": {
      "definitions": {
        "type": "object",
        "additionalProperties": { "$ref": "#/$defs/cascadeDefinition" }
      },
      "bindings": {
        "type": "object",
        "additionalProperties": { "type": "string" }
      }
    },
    "additionalProperties": false
  }
}
```

### 25.2 `$defs`-Ergänzung

```json
{
  "$defs": {
    "cascadeDefinition": {
      "type": "object",
      "required": ["name", "trigger", "stages"],
      "properties": {
        "name": { "type": "string" },
        "description": { "type": "string" },
        "trigger": {
          "type": "object",
          "properties": {
            "role": { "type": "string" },
            "intent": { "type": "string" }
          }
        },
        "stages": {
          "type": "array",
          "items": { "$ref": "#/$defs/cascadeStage" }
        },
        "on_error": { "type": "string", "enum": ["escalate", "skip", "retry", "stop"] }
      }
    },
    "cascadeStage": {
      "type": "object",
      "required": ["id", "agent", "task", "mode"],
      "properties": {
        "id": { "type": "string" },
        "agent": { "type": "string" },
        "task": { "type": "string" },
        "mode": { "type": "string", "enum": ["sequential", "parallel_group", "fanout", "loop", "conditional"] },
        "condition": {
          "type": "object",
          "properties": {
            "type": { "type": "string" },
            "agent": { "type": "string" },
            "expression": { "type": "string" }
          }
        },
        "next": {
          "type": "object",
          "properties": {
            "on_success": { "type": "string" },
            "on_failure": { "type": "string" },
            "on_decision": { "type": "object", "additionalProperties": { "type": "string" } }
          }
        }
      }
    }
  }
}
```

---

## DECISION

```
DECISION
context: agent-meta-Prompts sollen strukturierter und token-effizienter werden, ohne bestehende Projekte zu brechen.
choice: Einführung einer Two-Mode-Architektur (Legacy / Hybrid / Modern) mit pro-Rollen-Config in project.yaml; PoC startet mit `developer`. Template-Logik wird NICHT in `sync.py` eingeführt — stattdessen werden bedingte Blöcke als String-Variablen in `build_variables()` vorab aufgelöst. Cascaden werden als First-Class-Schema-Konzept neben `quality_pipelines` definiert. Rules, Snippets und Templates erhalten analoge Mode-Switches.
alternatives:
  - Big-Bang-Rewrite aller 55 Agenten → zu riskant, keine Rückwärtskompatibilität
  - Nur Hybrid-Mode für alle → begrenzter Impact, kein volles Potenzial
  - PoC mit `orchestrator` → zu komplex, hoher Blast-Radius, schwer zu validieren
  - Mini-Template-Engine (`{{#if}}`) in `sync.py` → neues Subsystem, Parser-Risiko, unterschätzte Wartungslast
  - Cascaden als Ersatz für `quality_pipelines` → `pipelines.py` erfüllt bereits einen spezifischen Zweck; Cascaden sollen ergänzen, nicht ersetzen
  - Sofortige Composition-Patch-Unterstützung für Modern-Templates → verschoben auf Phase 2, da `compose_agent()` heute Markdown-Anchor-basiert ist
consequences:
  + Schrittweise Migration möglich
  + Bestehende `wrap_sections_in_xml()` und `_extract_and_append_critical_footer()` werden wiederverwendet
  + Hybrid-Mode ist bereits funktional — nur Config-Flag `xml-section-wrapping: enabled: true`, kein Code-Aufwand
  + Admin-UI und Viz können Mode pro Rolle visualisieren
  + A2A-Handoff-Blocks lassen sich zentral in Snippets pflegen
  + Provider-Agnostik wird durch automatisierte Checks garantiert
  - Zusätzliche Verzeichnisstruktur `1-generic-modern/` nötig
  - `collect_sources()` muss in Phase 1 um `1-generic-modern/` erweitert werden, sonst keine Discovery
  - Modern-Templates sind in Phase 1+2 keine Composition-Targets (Constraint 6.8); `compose_agent()`-XML-Anchor-Support ist Phase-2-Task
  - Cascade-Runtime ist explizit Phase 3+, Phase 1 liefert nur das Schema
  - 15–20 % Token-Reduktion ist Hypothese, nicht Ziel — erste Messung im PoC
```

---

**Status:** Konzept-Entwurf v2.1 — überarbeitet nach Machbarkeits-Analyse
**Nächster Schritt:** Branch `feat/prompt-modernization-poc` ist angelegt; Phase 1 starten.
