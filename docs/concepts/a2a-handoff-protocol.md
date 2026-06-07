# A2A-Handoff-Protokoll — Implementationsnahe Konzeptschärfung

> **Status:** Konzept v2.0 — Implementation-nah
> **Baut auf:** [Best-Practice-Analyse](a2a-best-practice-analysis.md) (2026-06-07)
> **Basis-Issue:** [#212](https://github.com/Popoboxxo/agent-meta/issues/212)
> **Letzte Aktualisierung:** 2026-06-07

---

## 1. Architektur-Entscheidung: A2A als EINZIGES Schema-Austauschformat

### 1.1 Prinzip

**A2A-Envelopes sind das einzige Format für Agent-zu-Agent-Daten.** Natural-Language-Prompts zwischen Agenten werden vollständig durch strukturierte Envelopes ersetzt. Einzige Ausnahme: Continue/Copilot (`structured_handoff: false`) erhalten einen YAML-Text-Block statt JSON — aber das ist ein Transport-Format, kein anderes Konzept.

| Format | Status | Verwendung |
|--------|--------|------------|
| Natural-Language-Prompt | **Deprecated** | Wird nicht mehr für Agent-zu-Agent-Übergaben genutzt |
| A2A-Envelope (JSON) | **Einziges Format** | Alle Provider mit `structured_handoff: true` |
| YAML-Text-Block | **Transport-Fallback** | Continue/Copilot (kein natives JSON-Tool-Call) |
| SE-Schemas (se-decomposition, se-orchestrator) | **Eingebettet** | Nur noch als `payload` im Envelope |

### 1.2 Einbettungs-Muster für existierende Schemas

Bestehende Schemas werden **unverändert** als Payload in den Envelope eingebettet:

```json
{
  "protocol_version": "1.0.0",
  "handoff_id": "HOFF-20260607-001",
  "source_agent": "se-architect",
  "target_agent": "se-critic",
  "schema_ref": "schemas/se-decomposition.schema.json",
  "payload": {
    "feature_id": "REQ-L1-SH-001",
    "stakeholder_requirement": "...",
    "l1_system": { "blackbox": "...", "whitebox": ["..."] },
    "sub_components": [
      { "id": "COMP-001-01", "name": "...", "domain": "hardware", "black_box_requirement": "..." }
    ],
    "architectural_rationale": "..."
  },
  "trace_parent": "HOFF-20260607-000"
}
```

**Regel:** Kein existierendes Schema wird geändert. Neue Schemas (TaskSpec + Extensions) erhalten **kurze Feldnamen** (2–3 Zeichen).

---

## 2. Schema-Strategie: 1 Core + 4 Extensions + 1 SE

### 2.1 Übersicht

```
Schemas (6 total):
├── task-spec.schema.json              ← Core: 60-80% aller Delegationen
├── ext/ideation-extension.schema.json ← ideation → requirements
├── ext/design-extension.schema.json   ← ui-ux-designer → developer
├── ext/api-extension.schema.json      ← api-specialist → developer
├── ext/review-extension.schema.json   ← code-reviewer → developer
└── se-decomposition.schema.json       ← SE-Kaskade (7 Routen, existierend)
```

### 2.2 TaskSpec — Universelles Kern-Schema

```json
{
  "t": "Implementiere Login-Flow mit OAuth2",
  "ctx": "Bestehender Auth-Service unter /internal/auth nutzen",
  "con": ["Muss OAuth2 mit PKCE unterstützen", "Keine neuen Dependencies"],
  "refs": ["schemas/auth-api.json", "docs/architecture.md#auth-flow"],
  "pri": "high",
  "dep": ["HOFF-20260607-042"]
}
```

| Feld | Key | Typ | Tokens (ca.) | Pflicht |
|------|-----|-----|-------------|---------|
| Task | `t` | string | 1 | ✓ |
| Context | `ctx` | string | 1 | — |
| Constraints | `con` | string[] | 2 | — |
| References | `refs` | string[] | 2 | — |
| Priority | `pri` | enum | 1 | — |
| Depends on | `dep` | HOFF[] | 2 | — |

**Token-Vergleich (leeres Payload, nur Envelope + TaskSpec):**
- Mit langen Feldnamen: ~130 Tokens
- Mit kurzen Feldnamen: ~90 Tokens
- **Ersparnis: ~40 Tokens pro TaskSpec-Handoff (~31%)**

### 2.3 Extension-Mechanismus

Extensions werden via JSON Schema `allOf` mit TaskSpec kombiniert:

```json
{
  "allOf": [
    { "$ref": "schemas/handoffs/task-spec.schema.json" },
    { "$ref": "schemas/handoffs/ext/ideation-extension.schema.json" }
  ]
}
```

**Konkretes Beispiel — ideation→requirements:**

```json
{
  "protocol_version": "1.0.0",
  "handoff_id": "HOFF-20260607-005",
  "source_agent": "ideation",
  "target_agent": "requirements",
  "schema_ref": "schemas/handoffs/task-spec.schema.json",
  "compact_mode": true,
  "payload": {
    "t": "Dark-Mode-Toggle für Settings-Page entwickeln",
    "ctx": "Bestehende Theme-Infrastruktur nutzen",
    "pri": "medium",
    "ci": "Nutzer soll zwischen Light/Dark/System-Mode wechseln können",
    "g": "Nutzer mit visuellen Präferenzen können das UI anpassen → höhere UX-Zufriedenheit",
    "sv1": {
      "ins": ["Toggle-Button in Settings", "Light/Dark/System drei Modi", "Persistenz via localStorage"],
      "oos": ["Automatische Tageszeit-Erkennung", "Theme-Editor"]
    },
    "oq": ["Wie verhalten sich Drittanbieter-Widgets im Dark Mode?"],
    "ref": ["https://m3.material.io/theme"]
  }
}
```

### 2.4 DesignExtension — ui-ux-designer→developer

```json
{
  "protocol_version": "1.0.0",
  "handoff_id": "HOFF-20260607-010",
  "source_agent": "ui-ux-designer",
  "target_agent": "developer",
  "schema_ref": "schemas/handoffs/task-spec.schema.json",
  "compact_mode": true,
  "payload": {
    "t": "Settings-Page mit Theme-Toggle implementieren",
    "ds": {
      "cm": [
        {
          "nm": "ThemeToggle",
          "tp": "button",
          "st": ["default", "hover", "active", "focus"],
          "ac": "role=switch, aria-checked, Tab-index 0"
        }
      ],
      "th": {
        "co": { "primary": "#6750A4", "surface": "#FFFBFE", "error": "#BA1A1A" },
        "ty": { "h1": "32/40/700", "body": "14/20/400" },
        "sp": { "xs": "4", "sm": "8", "md": "16", "lg": "24", "xl": "32" }
      }
    }
  }
}
```

### 2.5 APIExtension — api-specialist→developer

```json
{
  "protocol_version": "1.0.0",
  "handoff_id": "HOFF-20260607-013",
  "source_agent": "api-specialist",
  "target_agent": "developer",
  "schema_ref": "schemas/handoffs/task-spec.schema.json",
  "compact_mode": true,
  "payload": {
    "t": "User-Preferences-Endpunkt implementieren",
    "ct": {
      "ep": [
        {
          "mt": "PATCH",
          "pt": "/api/v1/users/{id}/preferences",
          "sm": "Update user theme preference",
          "rq": {
            "bd": { "theme": { "type": "string", "enum": ["light", "dark", "system"] } },
            "ph": { "id": { "type": "string", "format": "uuid" } }
          },
          "rs": {
            "200": { "desc": "Updated", "bd": { "theme": "string", "updated_at": "string" } },
            "404": { "desc": "User not found" }
          },
          "au": true,
          "sc": ["user:write"]
        }
      ]
    },
    "vr": "v1",
    "gw": "/api/v1"
  }
}
```

### 2.6 ReviewExtension — code-reviewer→developer

```json
{
  "protocol_version": "1.0.0",
  "handoff_id": "HOFF-20260607-018",
  "source_agent": "code-reviewer",
  "target_agent": "developer",
  "schema_ref": "schemas/handoffs/task-spec.schema.json",
  "compact_mode": true,
  "payload": {
    "t": "ThemeToggle-Komponente überarbeiten — Review-Findings",
    "rd": {
      "v": "changes_requested",
      "fl": [
        {
          "fp": "src/components/ThemeToggle.tsx",
          "ln": 42,
          "sv": "error",
          "ct": "clean_code",
          "msg": "useEffect dependencies incomplete — missing 'theme' in dependency array",
          "sg": "Add theme to dependency array: useEffect(() => {...}, [theme, systemPrefers])"
        },
        {
          "fp": "src/components/ThemeToggle.tsx",
          "ln": 15,
          "sv": "warning",
          "ct": "naming",
          "msg": "Variable 't' too short for component-level scope",
          "sg": "Rename to 'currentTheme'"
        }
      ],
      "br": {
        "pf": ["src/components/ThemeToggle.tsx", "src/hooks/useTheme.ts"],
        "rl": "medium",
        "tn": "Unit test for ThemeToggle with all three theme values"
      }
    }
  }
}
```

### 2.7 SE-Decomposition als Payload (existierendes Schema, unverändert)

Die SE-Kaskade nutzt weiterhin `se-decomposition.schema.json` — eingebettet als `payload`:

```json
{
  "protocol_version": "1.0.0",
  "handoff_id": "HOFF-20260607-025",
  "source_agent": "se-architect",
  "target_agent": "se-critic",
  "schema_ref": "schemas/se-decomposition.schema.json",
  "compact_mode": false,
  "payload": {
    "feature_id": "REQ-L1-SH-001",
    "stakeholder_requirement": "...",
    "l1_system": { "blackbox": "...", "whitebox": ["..."] },
    "sub_components": [
      { "id": "COMP-001-01", "name": "...", "domain": "software", "black_box_requirement": "..." }
    ],
    "internal_interfaces": [
      { "source_id": "COMP-001-01", "target_id": "COMP-001-02", "interface_type": "REST", "data_payload": "..." }
    ],
    "architectural_rationale": "...",
    "decomposition_completeness": "..."
  },
  "trace_parent": "HOFF-20260607-024"
}
```

**SE-Schemas sind `compact_mode: false`** — die langen Feldnamen bleiben erhalten (kein Breaking Change für existierende SE-Infrastruktur).

---

## 3. Envelope-Schema (angepasst)

### 3.1 Struktur

```json
{
  "protocol_version": "1.0.0",
  "handoff_id": "HOFF-20260607-042",
  "source_agent": "orchestrator",
  "target_agent": "developer",
  "supersession": {
    "version": 3,
    "supersedes": "HOFF-20260607-040",
    "history": ["HOFF-20260607-038", "HOFF-20260607-040"],
    "reason": "REQ-042 scope erweitert nach Stakeholder-Feedback",
    "timestamp": "2026-06-07T14:30:00Z"
  },
  "schema_ref": "schemas/handoffs/task-spec.schema.json",
  "compact_mode": true,
  "payload": { "t": "...", "pri": "high" },
  "trace_parent": "HOFF-20260607-039",
  "trace_context": {
    "trace_id": "trace-abc123",
    "span_id": "span-042",
    "parent_span_id": "span-039",
    "viz_task_id": "uuid-x-y-z"
  }
}
```

### 3.2 Feld-Referenz

| Feld | Typ | Pflicht | Token (ca.) | Beschreibung |
|------|-----|---------|-------------|-------------|
| `protocol_version` | string (SemVer) | ✓ | 4 | Nur bei Major-Änderungen explizit gesetzt. Default = aktuelle Version. |
| `handoff_id` | HOFF-YYYYMMDD-NNN | ✓ | 4 | Globally unique. Format: HOFF-{date}-{seq} |
| `source_agent` | string | ✓ | 3 | Rolle des sendenden Agenten |
| `target_agent` | string | ✓ | 3 | Rolle des empfangenden Agenten |
| `schema_ref` | string (URI) | — | 10 | Optional: aus Route implizit ableitbar |
| `compact_mode` | boolean | — | 2 | true = kurze Payload-Namen (default: false) |
| `payload` | object | ✓ | 2+ | Domain-spezifische Nutzdaten |
| `trace_parent` | HOFF | — | 2 | Parent-handoff für Delegationsbaum |
| `trace_context` | object | — | 5 | Erweitertes Tracing |
| `supersession` | object | — | 5 | Version-Tracking |
| `supersession.history[]` | HOFF[] | — | 2+/Eintrag | Vollständige Revisionskette |

**Token-Budget (leerer Envelope ohne Payload):**
- Mit `schema_ref` + `compact_mode` + `trace_parent`: ~60 Tokens
- Minimal (nur Pflichtfelder, schema_ref implizit): ~40 Tokens
- Mit Supersession (version + supersedes): +15 Tokens

### 3.3 compact_mode — Steuerung kurzer Feldnamen

| compact_mode | Payload-Feldnamen | Anwendung |
|-------------|-------------------|-----------|
| `false` (default) | Lesbare lange Namen | SE-Schemas, Debugging |
| `true` | Kurze Namen (2-3 Zeichen) | TaskSpec, Extensions |

**Konfiguration in `.meta-config/project.yaml`:**
```yaml
orchestrator:
  handoff:
    compact-mode: false   # true = Token-sparend im Produktivbetrieb
```

---

## 4. Orchestrator-Integration

### 4.1 Orchestrator als Envelope-Fabrik

Der Orchestrator ist der **primäre Envelope-Produzent**. Jede Delegation wird als A2A-Envelope verpackt:

```
User-Request → Orchestrator analysiert Intent
                 │
                 ├─→ Routing-Tabelle bestimmt target_agent + contract
                 ├─→ payload aus User-Request + Kontext extrahiert
                 ├─→ Envelope erstellt (handoff_id, source, target, schema_ref, payload)
                 ├─→ (optional) Viz-Validierung vor Delegation
                 └─→ Delegation via PAL-Dispatch (JSON oder YAML)
```

### 4.2 FANOUT — N parallele Envelopes

**Szenario:** Orchestrator erkennt 3 unabhängige Sub-Tasks → FANOUT an 3 developer:

```
Envelope-1: { hid: "HOFF-001", src: "orchestrator", tgt: "developer",
              trace_context: { trace_id: "tr-abc", span_id: "sp-1" },
              payload: { "t": "Fix Login NullPointer" } }

Envelope-2: { hid: "HOFF-002", src: "orchestrator", tgt: "developer",
              trace_context: { trace_id: "tr-abc", span_id: "sp-2" },
              payload: { "t": "Add CSRF protection" } }

Envelope-3: { hid: "HOFF-003", src: "orchestrator", tgt: "developer",
              trace_context: { trace_id: "tr-abc", span_id: "sp-3" },
              payload: { "t": "Update error messages" } }
```

**Token-Impact FANOUT:** N × ~60 Tokens Envelope-Overhead. Bei MAX_PARALLEL_AGENTS=4: 240 Tokens pro Batch.

### 4.3 BARRIER — Response-Envelopes aggregieren

Nach FANOUT sammelt der Orchestrator die Ergebnisse. Worker produzieren Response-Envelopes:

```json
{
  "protocol_version": "1.0.0",
  "handoff_id": "HOFF-RESP-001",
  "source_agent": "developer",
  "target_agent": "orchestrator",
  "schema_ref": "schemas/handoffs/task-spec.schema.json",
  "payload": {
    "t": "Fix Login NullPointer abgeschlossen",
    "ctx": "commit: abc123, 3 files changed, tests green"
  },
  "trace_parent": "HOFF-001"
}
```

**Aggregation im Orchestrator:**

```json
{
  "handoff_id": "HOFF-AGG-001",
  "source_agent": "orchestrator",
  "target_agent": "orchestrator",
  "payload": {
    "batch_id": "HOFF-001",
    "results": [
      { "hid": "HOFF-001", "status": "success", "commit": "abc123" },
      { "hid": "HOFF-002", "status": "success", "commit": "def456" },
      { "hid": "HOFF-003", "status": "blocked", "reason": "needs clarification" }
    ]
  }
}
```

### 4.4 PIPELINE — Verkettung via trace_parent

**Szenario:** Feature-Lifecycle: `requirements → tester → developer → tester → validator → git`

```
HOFF-010: orchestrator → requirements  (trace_parent: null)
HOFF-011: requirements → tester       (trace_parent: HOFF-010)
HOFF-012: tester → developer          (trace_parent: HOFF-011)
HOFF-013: developer → tester          (trace_parent: HOFF-012)
HOFF-014: tester → validator          (trace_parent: HOFF-013)
HOFF-015: validator → git             (trace_parent: HOFF-014)
```

Fehlschlag in HOFF-013 → Chain-of-custody bis HOFF-010 zurückverfolgbar.

### 4.5 REPEAT_UNTIL — Supersession-Kette

**Szenario:** SE-Critic-Zyklus (max. 3 Iterationen):

```
HOFF-020: se-architect → se-critic  (v1, decomposition initial)
  → critic rejected: "missing traceability for COMP-001-03"

HOFF-021: se-architect → se-critic  (v2, supersedes: HOFF-020, history: [HOFF-020])
  → critic rejected: "interface type mismatch: analog_signal vs REST"

HOFF-022: se-architect → se-critic  (v3, supersedes: HOFF-021, history: [HOFF-020, HOFF-021])
  → critic approved ✓

HOFF-023: se-critic → se-interface-mgr
  (supersession: { version: 3, supersedes: "HOFF-022", history: ["HOFF-020","HOFF-021","HOFF-022"] })
```

Der `se-interface-mgr` sieht die vollständige Revisionskette und kann nachvollziehen, welche Änderungen in jeder Iteration vorgenommen wurden.

### 4.6 Orchestrator-Routing-Tabelle

Jede Route deklariert Contract + Schema + compact_mode:

```yaml
# In config/role-defaults.yaml (pro Route erweiterbar):
orchestrator:
  routes:
    - source: orchestrator
      target: developer
      contract: task-spec-v1
      schema: schemas/handoffs/task-spec.schema.json
      compact_mode: true

    - source: ideation
      target: requirements
      contract: ideation-output-v1
      schema: schemas/handoffs/task-spec.schema.json
      extension: schemas/handoffs/ext/ideation-extension.schema.json
      compact_mode: true

    - source: ui-ux-designer
      target: developer
      contract: design-spec-v1
      schema: schemas/handoffs/task-spec.schema.json
      extension: schemas/handoffs/ext/design-extension.schema.json
      compact_mode: true

    - source: se-architect
      target: se-critic
      contract: se-arch-output-v1
      schema: schemas/se-decomposition.schema.json
      compact_mode: false   # Lange Feldnamen erhalten
```

---

## 5. Provider-Matrix: Transport-Format

### 5.1 structured_handoff vs. YAML-Fallback

| Provider | structured_handoff | handoff_format | A2A-Envelope-Transport |
|----------|-------------------|----------------|------------------------|
| **Claude** | `true` | `json` | JSON im Task-Tool-Prompt |
| **Opencode** | `true` | `json` | JSON im task()-Prompt |
| **Gemini** | `true` | `json` | JSON im define_subagent-Prompt |
| **Continue** | `false` | `yaml_text_block` | YAML-Block im Prompt-Text |
| **Copilot** | `false` | `yaml_text_block` | YAML-Block im Prompt-Text |

### 5.2 YAML-Text-Block (Continue/Copilot)

```yaml
---
a2a_handoff:
  protocol_version: "1.0.0"
  handoff_id: "HOFF-20260607-001"
  source_agent: "orchestrator"
  target_agent: "developer"
  schema_ref: "schemas/handoffs/task-spec.schema.json"
  compact_mode: true
  trace_parent: "HOFF-20260607-000"
  payload:
    t: "Implementiere Login-Flow"
    ctx: "Bestehenden Auth-Service nutzen"
    pri: "high"
---
@developer Bearbeite diesen strukturierten Handoff.
```

**Token-Vergleich YAML vs. JSON (gleicher Inhalt):**
- JSON: ~90 Tokens
- YAML: ~60 Tokens
- **Ersparnis: ~33% für Continue/Copilot**

---

## 6. viz-Debug als separates Konzept

### 6.1 Zwei-Ebenen-Modell

| Ebene | System | Zweck | ID | Default |
|-------|--------|-------|-----|---------|
| **Operational Layer** | viz-Handshake | *Dass* eine Delegation stattfand | `viz_task_id` | Aktiv (nur basic Events) |
| **Data Contract Layer** | A2A-Envelope | *Was* wurde übergeben | `handoff_id` | Immer (Datenformat) |
| **Debug-Ebene** | A2A viz-Events | *Wie* wurde validiert/delivered | `viz_task_id` | **AUS** (`viz.debug: false`) |

### 6.2 Lose Kopplung via trace_context.viz_task_id

```json
{
  "trace_context": {
    "trace_id": "trace-session-42",
    "span_id": "span-007",
    "viz_task_id": "uuid-orchestrator-delegation-001"
  }
}
```

Das `viz_task_id`-Feld ist die einzige Kopplung zwischen beiden Systemen. Es ist optional — der A2A-Envelope funktioniert vollständig ohne viz, und viz funktioniert ohne A2A.

### 6.3 Debug-Mode Konfiguration

```yaml
# .meta-config/project.yaml
viz:
  debug: false           # true = A2A-Events werden geloggt
  a2a_events:
    handoff_start: true
    handoff_validated: true
    handoff_delivered: true
    handoff_failed: true
    supersession: true
```

### 6.4 Token-Kosten viz-Debug

| Modus | Zusätzliche viz-Calls | Token-Impact | Log-Zeilen |
|-------|----------------------|--------------|------------|
| `viz.debug: false` | 0 | **0 Tokens** | 0 |
| `viz.debug: true` | 3–5 pro Handoff | ~30 Tokens (Prompt-Block) | 3–5 |

**Default ist `false`** — Null-Token-Kosten im Produktivbetrieb.

### 6.5 A2A-Event-Typen

| Event | Wann | Payload |
|-------|------|---------|
| `a2a_handoff_start` | Envelope erstellt | `{handoff_id, source_agent, target_agent, contract}` |
| `a2a_handoff_validated` | Validierung abgeschlossen | `{handoff_id, valid: bool, errors: [...]}` |
| `a2a_handoff_delivered` | Downstream akzeptiert | `{handoff_id, status: accepted\|rejected\|superseded}` |
| `a2a_handoff_failed` | Validierung fehlgeschlagen | `{handoff_id, errors: [...]}` |
| `a2a_supersession` | Supersession erstellt | `{handoff_id, supersedes, reason}` |

---

## 7. Token-Budget & Optimierungen

### 7.1 Token-Tabelle pro Handoff-Typ

| Handoff-Typ | Envelope | Payload | Total | Mit compact_mode |
|-------------|----------|---------|-------|-----------------|
| Einfach (TaskSpec, `t` nur) | 40 | 5 | **45** | **45** |
| Standard (TaskSpec mit ctx+con+pri) | 40 | 20 | **60** | **60** |
| Ideation (TaskSpec + IdeationExt) | 60 | 45 | **105** | **85** (compact) |
| Design (TaskSpec + DesignExt) | 60 | 55 | **115** | **90** (compact) |
| Review (TaskSpec + ReviewExt, 3 findings) | 60 | 80 | **140** | **110** (compact) |
| SE-Decomposition (compact_mode: false) | 60 | 180–500 | **240–560** | N/A (compact off) |
| Supersession-Handoff (+ history) | 60+15 | — | +15 | +15 |

### 7.2 Optimierungen (umgesetzt)

| # | Optimierung | Ersparnis | Status |
|---|-------------|-----------|--------|
| 1 | Kurze Payload-Feldnamen (neue Schemas) | 20–50 Tokens/Handoff | ✓ Umgesetzt (TaskSpec + Extensions) |
| 2 | `schema_ref` implizit aus Route | ~20 Tokens | ✓ Optional (im Envelope-Schema) |
| 3 | `protocol_version` default = aktuell | ~9 Tokens | ✓ Implizit, nur explizit bei Major-Change |
| 4 | `compact_mode`-Flag | 0 (schaltet #1 an/aus) | ✓ Im Envelope-Schema |
| 5 | viz.debug: false default | 30 Tokens/Handoff | ✓ In project.yaml konfiguriert |

### 7.3 Nicht umgesetzt (begründet)

| Optimierung | Ersparnis | Grund für Ablehnung |
|-------------|-----------|-------------------|
| Envelope-Feldnamen kürzen | ~15 Tokens | Breaking Change — alle Schemas/Templates migrieren |
| JSON-Array-Format | ~27 Tokens | Kein JSON-Schema-Validierung, LLM-Verwirrung |
| Binärformat (MessagePack) | 60-80% | Kein Provider-Support |

---

## 8. Implementationsfahrplan

### Phase 1 — Schema-Grundlage (JETZT)

| # | Maßnahme | Dateien | Status |
|---|----------|---------|--------|
| 1 | TaskSpec-Kern-Schema | `schemas/handoffs/task-spec.schema.json` | ✓ Erstellt |
| 2 | 4 Extensions | `schemas/handoffs/ext/*.schema.json` | ✓ Erstellt |
| 3 | Envelope um compact_mode + history[] | `schemas/a2a-handoff.schema.json` | ✓ Angepasst |
| 4 | Konzept-Dokument überarbeiten | `docs/concepts/a2a-handoff-protocol.md` | ✓ Dieses Dokument |
| 5 | Config-Block in project.yaml | `.meta-config/project.yaml` | → Nächster Schritt |
| 6 | CODEBASE_OVERVIEW + SE-Cascade | `docs/CODEBASE_OVERVIEW.md`, `docs/architecture/07-se-cascade.md` | → Nächster Schritt |

### Phase 2 — Transport & Provider (1–2 Wochen)

| # | Maßnahme | Dateien |
|---|----------|---------|
| 7 | `{{PAL_HANDOFF}}`-Platzhalter | `config/delegation-syntax.yaml`, `scripts/lib/delegation_syntax.py` |
| 8 | Provider-Capability-Flags | `config/provider-capabilities.yaml` |
| 9 | YAML-Text-Block für Continue/Copilot | `config/delegation-syntax.yaml` (Continue/Copilot Sektionen) |

### Phase 3 — Orchestrator & Agenten (2–3 Wochen)

| # | Maßnahme | Dateien |
|---|----------|---------|
| 10 | Orchestrator Envelope-Fabrik | `agents/1-generic/orchestrator.md` |
| 11 | Handoff-Routing-Tabelle | `config/role-defaults.yaml` (routes-Sektion) |
| 12 | Agent-Updates (ideation, feature, developer) | `agents/1-generic/ideation.md`, `feature.md`, `developer.md` |
| 13 | SE-Agenten (Envelope-basierte Handoffs) | `agents/1-generic/se-*.md` |
| 14 | Validator: validate_handoff | `agents/1-generic/validator.md` |

### Phase 4 — MCP & Tooling (3–4 Wochen)

| # | Maßnahme | Dateien |
|---|----------|---------|
| 15 | MCP-Tools: resolve-handoff-schema, validate-handoff | `scripts/viz-logger.py` (erweitern) |
| 16 | A2A-Events in viz-logger (hinter debug-Flag) | `scripts/viz-logger.py`, `scripts/lib/viz.py` |
| 17 | Supersession-Tracking im Orchestrator | `agents/1-generic/orchestrator.md`, `scripts/lib/` |

---

## 9. Offene Punkte

| # | Thema | Stand |
|---|-------|-------|
| 1 | **Schema-Validierung zur Laufzeit:** Soll der Orchestrator vor jeder Delegation gegen das Payload-Schema validieren? Vorschlag: Ja — `validate-before-delegate: true` in Config. Fallback: Agent validiert selbst. |
| 2 | **Response-Envelopes standardisieren:** Welche Felder muss ein Worker in seinem Response-Envelope liefern? Vorschlag: TaskSpec `t`-Feld + `status` + `commit` im Payload. |
| 3 | **Token-Budget-Tracking:** Soll der Orchestrator das Session-Token-Budget für A2A-Overhead tracken? Vorschlag: Ja, aber erst in Phase 3 — Ziel: max. 10% des Session-Budgets. |
| 4 | **Rollback bei Supersession:** Automatisches Rollback oder nur Benachrichtigung? Vorschlag: Benachrichtigung + manuelle Bestätigung durch downstream-Agent. |
| 5 | **Schema-Registry:** Zentrale Registry vs. dezentrale Dateien? Vorschlag: Dateien in `schemas/handoffs/` + MCP-Server für dynamische Resolution (Phase 4). |
| 6 | **Kompatibilität Nicht-JSON-Provider:** Gelöst via YAML-Text-Block. File-basierte Fallback-Strategie (`.handoff.json` im `.se-cascade/`) optional. |

---

## 10. Referenzen

| Quelle | Link/Pfad |
|--------|-----------|
| Best-Practice-Analyse | `docs/concepts/a2a-best-practice-analysis.md` |
| Envelope-Schema | `schemas/a2a-handoff.schema.json` |
| TaskSpec-Schema | `schemas/handoffs/task-spec.schema.json` |
| Extensions | `schemas/handoffs/ext/*.schema.json` |
| SE-Decomposition | `schemas/se-decomposition.schema.json` |
| SE-Orchestrator | `schemas/se-orchestrator.schema.json` |
| Ideation-Output (exist.) | `schemas/handoffs/ideation-output.schema.json` |
| Orchestrator-First Architecture | `docs/concepts/orchestrator-first-architecture.md` |
| SE-Kaskade | `docs/architecture/07-se-cascade.md` |
| CODEBASE_OVERVIEW | `docs/CODEBASE_OVERVIEW.md` |
| project.yaml Config | `.meta-config/project.yaml` |
| Viz-Architektur | `docs/viz-architecture.md` |
| PAL (Delegation Syntax) | `config/delegation-syntax.yaml` |
