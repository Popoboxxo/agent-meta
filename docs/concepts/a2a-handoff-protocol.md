# A2A-Handoff-Protokoll — Implementationsnahe Konzeptschärfung

> **Status:** Konzept v2.0 — Implementation-nah
> **Baut auf:** [Best-Practice-Analyse](a2a-best-practice-analysis.md) (2026-06-07)
> **Basis-Issue:** [#212](https://github.com/Popoboxxo/agent-meta/issues/212)
> **Letzte Aktualisierung:** 2026-06-07

---

## Implementierungsstatus (verifiziert 2026-06-14)

**Umgesetzt:**
- 6 Schemas (`schemas/handoffs/`, `schemas/a2a-handoff.schema.json`, SE-Schemas)
- Orchestrator als Envelope-Fabrik (`agents/1-generic/orchestrator.md` → »A2A Handoff Protocol«)
- `{{PAL_HANDOFF}}` + Provider-Matrix: JSON für Claude/Opencode/Gemini, YAML-Text-Block-Fallback für Continue/Copilot (`config/delegation-syntax.yaml`, `scripts/lib/delegation_syntax.py`)
- HITL (`human_approval_required`), Retry (`max_retries`), compact-mode, supersession-tracking (`project.yaml` → `orchestrator.handoff.*`)
- **Token-Budget-Tracking** (`orchestrator.handoff.token-budget`, Default 10% des Session-Budgets) — Offener Punkt #3 erledigt

**Offen:**
- Response-Envelopes standardisiert (Offener Punkt #2)
- MCP-Tools `resolve-handoff-schema`, `validate-handoff` (Phase 4)

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

Extensions werden via JSON Schema `allOf` mit TaskSpec kombiniert. ABER: weder TaskSpec noch Extensions verwenden `additionalProperties: false` — dies verhindert `allOf`-Kombinierbarkeit (Draft-07 Fallstrick).

```json
{
  "allOf": [
    { "$ref": "schemas/handoffs/task-spec.schema.json" },
    { "$ref": "schemas/handoffs/ext/ideation-extension.schema.json" }
  ]
}
```

Schema-Validierung für kombinierte Schemas erfolgt via `if-then` im Route-Registry-Schema — nicht via `allOf` + `additionalProperties: false`.

**Konkretes Beispiel — ideation→requirements:**

```json
{
  "protocol_version": "1.0.0",
  "handoff_id": "HOFF-20260607-005",
  "source_agent": "ideation",
  "target_agent": "requirements",
  "schema_ref": "schemas/handoffs/task-spec.schema.json",
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

**SE-Schemas verwenden `compact-mode: false` in der Build-Config** — die langen Feldnamen bleiben erhalten (kein Breaking Change für existierende SE-Infrastruktur).

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
    "supersedes": "HOFF-20260607-040",
    "history": ["HOFF-20260607-038", "HOFF-20260607-040"],
    "reason": "REQ-042 scope erweitert nach Stakeholder-Feedback",
    "timestamp": "2026-06-07T14:30:00Z"
  },
  "schema_ref": "schemas/handoffs/task-spec.schema.json",
  "payload": { "t": "...", "pri": "high" },
  "trace_parent": "HOFF-20260607-039",
  "trace_context": {
    "trace_id": "trace-abc123",
    "span_id": "span-042",
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
| `payload` | object \| array | ✓ | 2+ | Domain-spezifische Nutzdaten. Array wenn `batch: true`. |
| `schema_ref` | string (URI) | — | 10 | Optional: wenn fehlt → implizit aus `source_agent` + `target_agent` via Routing-Tabelle aufgelöst |
| `batch` | boolean | — | 2 | FANOUT-Modus: payload ist Array von Task-Objekten (default: false) |
| `retry_count` | integer | — | 2 | Anzahl bisheriger Retries (default: 0). Bei ≥ `max_retries` → Abbruch |
| `max_retries` | integer | — | 2 | Max. erlaubte Retries (default: 3). Config in project.yaml |
| `requires_human_approval` | boolean | — | 2 | HITL: downstream-Agent pausiert vor Ausführung (default: false) |
| `negotiated_format` | enum | — | 2 | Transport-Format: `json`, `yaml`, `text`, `auto` (default: `auto`) |
| `trace_parent` | HOFF | — | 2 | Parent-handoff für Delegationsbaum. Einziger Parent-Tracing-Mechanismus |
| `trace_context` | object | — | 5 | Erweitertes Tracing (trace_id, span_id, viz_task_id) |
| `supersession` | object | — | 5 | Version-Tracking über history-Kette |
| `supersession.history[]` | HOFF[] | — | 2+/Eintrag | Vollständige Revisionskette. `version = history.length + 1` |

**Token-Budget (leerer Envelope ohne Payload):**
- Mit `schema_ref` + `trace_parent`: ~64 Tokens
- Minimal (nur Pflichtfelder, schema_ref implizit): ~42 Tokens
- Mit Supersession (supersedes + history): +12 Tokens
- Mit Batch (3 Tasks): +25 Tokens

### 3.3 compact_mode — Build-Config, nicht Laufzeit-Konzept

`compact_mode` steuert ob kurze (2-3 Zeichen) oder lange Payload-Feldnamen verwendet werden. Es ist ein **Build-Zeit-Konzept** — gesteuert in `.meta-config/project.yaml`, nicht im Envelope.

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

> **Warum nicht im Envelope:** Der Envelope enthält keine Felder die zur Laufzeit zwischen `compact_mode: true` und `false` wechseln. Die Payload-Feldnamen sind Teil des Schemas das zur Build-Zeit ausgerollt wird. Ein Laufzeit-Flag würde nur verwirren — der downstream-Agent bekommt immer das Format das die Build-Config vorgibt.

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

### 4.2a Batch-Mode — N Tasks in einem Envelope

Für gleiche source/target-Paare (z.B. orchestrator→developer mit 3 Tasks) reduziert Batch-Mode
den Envelope-Overhead drastisch:

```json
{
  "protocol_version": "1.0.0",
  "handoff_id": "HOFF-BATCH-001",
  "source_agent": "orchestrator",
  "target_agent": "developer",
  "batch": true,
  "schema_ref": "schemas/handoffs/task-spec.schema.json",
  "payload": [
    {"t": "Fix Login Bug", "pri": "high", "batch_task_id": "T1"},
    {"t": "Add Logging", "pri": "medium", "batch_task_id": "T2"},
    {"t": "Refactor Auth", "pri": "low", "batch_task_id": "T3"}
  ]
}
```

**Token-Vergleich Batch vs. Einzeln (3 Tasks):**
- 3 separate Envelopes: 3 × ~60 = ~180 Tokens
- 1 Batch-Envelope: ~70 Tokens
- **Ersparnis: ~110 Tokens pro FANOUT(3)**

**Regel:** Batch nur wenn `source_agent` und `target_agent` für alle Tasks identisch sind. Unterschiedliche Ziele → separate Envelopes.

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
HOFF-020: se-architect → se-critic  (history: [], version = 0 + 1 = 1)
  → critic rejected: "missing traceability for COMP-001-03"

HOFF-021: se-architect → se-critic  (supersedes: HOFF-020, history: [HOFF-020], version = 1 + 1 = 2)
  → critic rejected: "interface type mismatch: analog_signal vs REST"

HOFF-022: se-architect → se-critic  (supersedes: HOFF-021, history: [HOFF-020, HOFF-021], version = 2 + 1 = 3)
  → critic approved ✓

HOFF-023: se-critic → se-interface-mgr
  (supersession: { supersedes: "HOFF-022", history: ["HOFF-020","HOFF-021","HOFF-022"] })
  → version = history.length + 1 = 4
```

Der `se-interface-mgr` sieht die vollständige Revisionskette und kann nachvollziehen, welche Änderungen in jeder Iteration vorgenommen wurden.

### 4.6 Orchestrator-Routing-Tabelle

Jede Route deklariert Contract + Schema:

```yaml
# In config/role-defaults.yaml (pro Route erweiterbar):
orchestrator:
  routes:
    - source: orchestrator
      target: developer
      contract: task-spec-v1
      schema: schemas/handoffs/task-spec.schema.json

    - source: ideation
      target: requirements
      contract: ideation-output-v1
      schema: schemas/handoffs/task-spec.schema.json
      extension: schemas/handoffs/ext/ideation-extension.schema.json

    - source: ui-ux-designer
      target: developer
      contract: design-spec-v1
      schema: schemas/handoffs/task-spec.schema.json
      extension: schemas/handoffs/ext/design-extension.schema.json

    - source: se-architect
      target: se-critic
      contract: se-arch-output-v1
      schema: schemas/se-decomposition.schema.json
      # Keine compact_mode-Angabe — wird aus project.yaml gelesen
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
| Einfach (TaskSpec, `t` nur) | 42 | 5 | **47** | **47** |
| Standard (TaskSpec mit ctx+con+pri) | 42 | 20 | **62** | **62** |
| Ideation (TaskSpec + IdeationExt) | 64 | 45 | **109** | **89** (compact) |
| Design (TaskSpec + DesignExt) | 64 | 55 | **119** | **94** (compact) |
| Review (TaskSpec + ReviewExt, 3 findings) | 64 | 80 | **144** | **114** (compact) |
| Batch (3 Tasks) | 70 | 30 | **100** | **85** (compact) |
| SE-Decomposition (compact-mode: false) | 64 | 180–500 | **244–564** | N/A (compact off) |
| Supersession-Handoff (+ history) | 64+12 | — | +12 | +12 |

### 7.2 Optimierungen (umgesetzt)

| # | Optimierung | Ersparnis | Status |
|---|-------------|-----------|--------|
| 1 | Kurze Payload-Feldnamen (neue Schemas) | 20–50 Tokens/Handoff | ✓ Umgesetzt (TaskSpec + Extensions) |
| 2 | `schema_ref` implizit aus Route | ~20 Tokens | ✓ Optional (im Envelope-Schema) |
| 3 | `protocol_version` default = aktuell | ~9 Tokens | ✓ Implizit, nur explizit bei Major-Change |
| 4 | `compact-mode` als Build-Config | 2 Tokens/Envelope | ✓ Aus Envelope entfernt (nur project.yaml) |
| 5 | viz.debug: false default | 30 Tokens/Handoff | ✓ In project.yaml konfiguriert |
| 6 | Batch-Mode für FANOUT | ~110 Tokens/FANOUT(3) | ✓ Neu (batch: true im Envelope) |

### 7.3 Nicht umgesetzt (begründet)

| Optimierung | Ersparnis | Grund für Ablehnung |
|-------------|-----------|-------------------|
| Envelope-Feldnamen kürzen | ~15 Tokens | Breaking Change — alle Schemas/Templates migrieren |
| JSON-Array-Format | ~27 Tokens | Kein JSON-Schema-Validierung, LLM-Verwirrung |
| Binärformat (MessagePack) | 60-80% | Kein Provider-Support |

---

## 8. Human-in-the-Loop (HITL)

### 8.1 requires_human_approval

Wenn `requires_human_approval: true` im Envelope gesetzt ist, MUSS der downstream-Agent **vor der Ausführung** pausieren und auf eine explizite User-Bestätigung warten.

```json
{
  "protocol_version": "1.0.0",
  "handoff_id": "HOFF-20260607-050",
  "source_agent": "orchestrator",
  "target_agent": "developer",
  "payload": { "t": "DELETE /api/v1/users — Batch-Löschung implementieren" },
  "requires_human_approval": true
}
```

**HITL-Flow:**
1. Orchestrator sendet Envelope mit `requires_human_approval: true`
2. Downstream-Agent empfängt, erkennt das Flag → pausiert
3. Agent zeigt Aufgabe + Kontext an: *"Soll ich folgende Aufgabe ausführen? [Task-Beschreibung]"*
4. User bestätigt → Ausführung startet
5. User lehnt ab → Agent antwortet mit `status: rejected_by_user`

**Config-Steuerung:**
```yaml
# .meta-config/project.yaml
orchestrator:
  handoff:
    human_approval_required: false   # true = globaler HITL-Modus
```

**Einsatzbereiche:**
- Kritische Änderungen (DELETE-Operationen, Schema-Migrationen)
- Unsicherheits-Flag: Orchestrator erkennt Ambiguität → setzt HITL
- Security-sensible Operationen

---

## 9. Kompatibilität mit Agent Protocol

### 9.1 Mapping-Tabelle

Das A2A-Protokoll kann auf das [Agent Protocol](https://agentprotocol.ai/) (`POST /ap/v1/agent/tasks`) gemappt werden:

| A2A-Feld | Agent Protocol Feld | Notes |
|----------|--------------------|-------|
| `handoff_id` | `task.id` | Eindeutige Task-Identität |
| `source_agent` | `task.metadata.source` | Sender-Rolle |
| `target_agent` | `task.metadata.target` | Empfänger-Rolle |
| `payload` | `input` | Domain-spezifische Nutzdaten |
| `payload.t` | `input.task` | Task-Beschreibung |
| `schema_ref` | `input.metadata.schema_ref` | Schema-Referenz |
| `trace_parent` | `task.metadata.parent_id` | Parent-Tracing |
| `trace_context.trace_id` | `task.metadata.trace_id` | Distributed Trace |
| `supersession` | `task.supersedes` + `task.history` | Version-Tracking |

### 9.2 Future: agent_protocol_bridge

Geplant: Optionaler Bridge-Modus der A2A-Envelopes transparent in Agent-Protocol-Tasks übersetzt. Ermöglicht Interop mit externen Agent-Protocol-konformen Systemen ohne Änderung der internen agent-meta-Infrastruktur.

---

## 10. Dynamisches Protocol Routing

### 10.1 negotiated_format

Der Envelope unterstützt `negotiated_format` zur Laufzeit-Aushandlung des Transport-Formats:

| Wert | Bedeutung | Einsatz |
|------|-----------|---------|
| `json` | JSON-Envelope (nativ) | Provider mit `structured_handoff: true` |
| `yaml` | YAML-Text-Block | Continue, Copilot |
| `text` | Natural-Language-Fallback | Legacy / Debugging |
| `auto` | Orchestrator wählt basierend auf Payload-Größe | Default |

### 10.2 Routing-Entscheidungen (auto-Modus)

| Payload-Größe | Format | Begründung |
|--------------|--------|-----------|
| < 1 KB | JSON | Beste LLM-Unterstützung, keine Größenprobleme |
| 1–10 KB | YAML | ~33% Token-Ersparnis vs. JSON |
| > 10 KB | Text | Vermeidet Context-Window-Überlauf, natürlichere Verarbeitung |

### 10.3 Config-Steuerung

```yaml
# .meta-config/project.yaml
orchestrator:
  handoff:
    protocol_routing: static   # static = feste Format-Wahl, dynamic = auto-Modus
```

Bei `static`: Format wird aus `config/provider-capabilities.yaml` → `handoff_format` gelesen (pro Provider).
Bei `dynamic`: Orchestrator misst Payload-Größe und wählt Format via obiger Tabelle.

---

## 11. Retry-Logik

### 11.1 retry_count / max_retries

Jeder Envelope führt `retry_count` (Anzahl bisheriger Retries) und `max_retries` (Limit):

```json
{
  "handoff_id": "HOFF-20260607-060",
  "retry_count": 2,
  "max_retries": 3,
  "payload": { "t": "Flaky-API-Integration mit Retry-Logik" }
}
```

**Retry-Flow:**
1. Orchestrator sendet Envelope mit `retry_count: 0`
2. Downstream-Agent schlägt fehl (Timeout, Validierungsfehler, etc.)
3. Orchestrator inkrementiert `retry_count` → sendet erneut (selbe `handoff_id`)
4. Wenn `retry_count >= max_retries` → **Abbruch mit Fehler-Eskalation**:
   - Orchestrator loggt Fehler
   - User wird benachrichtigt
   - Kein weiterer Retry

**Config:**
```yaml
# .meta-config/project.yaml
orchestrator:
  handoff:
    max_retries: 3   # Globaler Default, pro Envelope überschreibbar
```

---

## 12. Token Pruning für supersession.history

### 12.1 KLARSTELLUNG

`supersession.history` enthält **NUR handoff_ids** (Strings) — **NIE volle Payloads**.

| Feld | Inhalt | Token-Kosten |
|------|--------|-------------|
| `history[]` | `"HOFF-YYYYMMDD-NNN"` Strings | ~4 Tokens/Eintrag |
| Volle Payloads | **NICHT enthalten** | 0 Tokens |

**Resolution voller Payloads:** Via MCP-Tool `resolve_handoff(handoff_id)`, das den kompletten Envelope aus dem Event-Log rekonstruiert. Kein Payload-Ballast in der History-Kette.

**Beispiel — 10-Iterationen SE-Critic-Zyklus:**
- History: 10 × ~4 Tokens = ~40 Tokens
- Ohne Pruning (volle Payloads): 10 × ~200 Tokens = ~2000 Tokens
- **Ersparnis: ~1960 Tokens (98%)**

---

## 13. Implementationsfahrplan

### Phase 1 — Schema-Grundlage (JETZT)

| # | Maßnahme | Dateien | Status |
|---|----------|---------|--------|
| 1 | TaskSpec-Kern-Schema | `schemas/handoffs/task-spec.schema.json` | ✓ Erstellt |
| 2 | 4 Extensions | `schemas/handoffs/ext/*.schema.json` | ✓ Erstellt |
| 3 | Envelope-Schema (v2: -compact_mode, -version, +batch, +retry, +HITL, +negotiated_format) | `schemas/a2a-handoff.schema.json` | ✓ Angepasst |
| 4 | Konzept-Dokument überarbeiten | `docs/concepts/a2a-handoff-protocol.md` | ✓ Angepasst |
| 5 | Config-Block (handoff.max_retries, human_approval_required, protocol_routing) | `.meta-config/project.yaml` | ✓ Aktualisiert |
| 6 | provider-capabilities.yaml prüfen | `config/provider-capabilities.yaml` | ✓ structured_handoff vorhanden |

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

## 14. Offene Punkte

| # | Thema | Stand |
|---|-------|-------|
| 1 | **Schema-Validierung zur Laufzeit:** Soll der Orchestrator vor jeder Delegation gegen das Payload-Schema validieren? → **JA — `validate-before-delegate: true` in Config (MUSS).** Fallback: Agent validiert selbst. | ✓ Erledigt |
| 2 | **Response-Envelopes standardisieren:** Welche Felder muss ein Worker in seinem Response-Envelope liefern? Vorschlag: TaskSpec `t`-Feld + `status` + `commit` im Payload. | Offen |
| 3 | **Token-Budget-Tracking:** Soll der Orchestrator das Session-Token-Budget für A2A-Overhead tracken? Vorschlag: Ja, aber erst in Phase 3 — Ziel: max. 10% des Session-Budgets. | Offen |
| 4 | **Rollback bei Supersession:** Automatisches Rollback oder nur Benachrichtigung? Vorschlag: Benachrichtigung + manuelle Bestätigung durch downstream-Agent. | Offen |
| 5 | **Schema-Registry:** Zentrale Registry vs. dezentrale Dateien? Vorschlag: Dateien in `schemas/handoffs/` + MCP-Server für dynamische Resolution (Phase 4). | Offen |
| 6 | **Kompatibilität Nicht-JSON-Provider:** Gelöst via YAML-Text-Block + `negotiated_format`. File-basierte Fallback-Strategie (`.handoff.json` im `.se-cascade/`) optional. | ✓ Erledigt |
| 7 | **HITL-Integration:** Human-in-the-Loop via `requires_human_approval` umgesetzt. Config-gesteuert in project.yaml. | ✓ Erledigt |
| 8 | **Agent Protocol Bridge:** Mapping-Tabelle dokumentiert. Optionaler Bridge-Modus für Phase 4 vorgemerkt. | ✓ Dokumentiert |

---

## 15. Referenzen

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
