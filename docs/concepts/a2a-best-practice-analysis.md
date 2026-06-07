# A2A Best Practice Analysis

> Interne Analyse — Deutsch
> Datum: 2026-06-07
> Baut auf: [docs/concepts/a2a-handoff-protocol.md](a2a-handoff-protocol.md)
> Status: Konzept-Ergänzung

---

## 1. Token-Effizienz

### 1.1 Ist-Analyse: Token-Kosten des aktuellen Envelopes

Der aktuelle Envelope (`schemas/a2a-handoff.schema.json`) hat 6 Pflichtfelder + 4 optionale Felder mit deskriptiven Namen. Ein typischer vollständiger Envelope (ohne Payload-Inhalt) kostet ca. **60–80 Tokens** (je nach Tokenizer, hier Schätzung auf Basis eines GPT-4o-ähnlichen BPE-Tokenizers mit ~3,5 Zeichen/Token im JSON-Kontext):

| Feld | Lange Form | Chars | Tokens (ca.) |
|------|-----------|-------|--------------|
| `"protocol_version":"1.0.0"` | `"protocol_version":"1.0.0"` | 30 | 9 |
| `"handoff_id":"HOFF-20260607-001"` | `"handoff_id":"HOFF-20260607-001"` | 37 | 11 |
| `"source_agent":"ideation"` | `"source_agent":"ideation"` | 26 | 8 |
| `"target_agent":"requirements"` | `"target_agent":"requirements"` | 32 | 9 |
| `"schema_ref":"schemas/…json"` | (Wert ca. 50 Zeichen) | 68 | 20 |
| `"payload":{}` | (leer) | 12 | 4 |
| JSON-Struktur | `{`, `}`, `,`, `:` | 12 | 4 |
| **Summe leerer Envelope** | | **~217** | **~65** |

Bei einem nicht-leeren Payload (z.B. `ideation-output.schema.json` mit 3–5 Feldern) kommen **40–100 weitere Tokens** hinzu, je nach Umfang der übergebenen Daten. Ein realistischer Handoff liegt also bei **100–180 Tokens Overhead** (Envelope) plus Payload-Nutzdaten.

> **Faustregel:** In einer durchschnittlichen Session mit 10–20 Delegationen kostet der Envelope-Overhead **650–3.600 Tokens** — das entspricht etwa dem Kontext eines mittelgroßen Agent-Templates.

### 1.2 Minimale Envelope-Größe

Ein auf das Nötigste reduzierter Envelope (nur 6 Pflichtfelder, leeres Payload, kurze Feldnamen):

```json
{"pv":"1.0.0","hid":"HOFF-20260607-001","src":"ideation","tgt":"reqs","sch":"schemas/handoffs/ideation-output.schema.json","pl":{}}
```

| Feld | Kurze Form | Chars | Tokens (ca.) |
|------|-----------|-------|--------------|
| `"pv":"1.0.0"` | `"pv":"1.0.0"` | 13 | 5 |
| `"hid":"HOFF-20260607-001"` | `"hid":"HOFF-20260607-001"` | 28 | 9 |
| `"src":"ideation"` | `"src":"ideation"` | 18 | 6 |
| `"tgt":"reqs"` | `"tgt":"reqs"` | 12 | 5 |
| `"sch":"schemas/…json"` | (Wert unverändert) | 58 | 18 |
| `"pl":{}` | (leer) | 8 | 3 |
| JSON-Struktur | | 12 | 4 |
| **Summe minimierter Envelope** | | **~149** | **~50** |

**Ersparnis: ~15 Tokens pro leerem Envelope (~23% Reduktion).** Bei Payload-gefüllten Handoffs relativiert sich die Ersparnis auf **10–15% der Gesamtgröße**, da die Nutzdaten den größten Token-Anteil ausmachen.

### 1.3 Feldnamen: Kurz vs. Lesbar (Trade-off-Analyse)

**Die Kernfrage:** Der aktuelle Envelope ist für **menschliche Lesbarkeit** optimiert. `protocol_version`, `handoff_id`, `source_agent`, `target_agent`, `schema_ref`, `payload` — jedes Feld erklärt sich selbst. Aber die primären Konsumenten sind **LLM-Agenten**. Ein LLM versteht `"pv":"1.0.0","hid":"HOFF-…","src":"ideation","tgt":"reqs"` ebenso sicher wie die Langform, sofern das Schema einmal erklärt wurde.

| Dimension | Lange Namen | Kurze Namen |
|-----------|-------------|-------------|
| **LLM-Verständnis** | ✓ Kein Lookup nötig | ✓ Nach Schema-Einlesung gleichwertig |
| **Menschliches Debugging** | ✓ Selbsterklärend | ✗ Benötigt Schema-Referenz |
| **Token-Kosten** | ✗ 65 Tokens (leer) | ✓ 50 Tokens (leer) |
| **Payload-Feldnamen** | ✗ `preliminary_requirements` (3 Tokens) | ✓ `preq` (1 Token) |
| **Schema-Validierung** | ✓ Lesbare Fehlermeldungen | ✓ Via `title`/`description` im Schema |
| **Breaking Change** | N/A | ✗ Alle existierenden Schemas müssen migriert werden |

**Payload-Feldnamen sind der eigentliche Hebel.** Im Envelope selbst spart man pro Handoff ~15 Tokens. In den Payloads (mit 10–30 Feldern, z.B. `se-decomposition.schema.json` mit 317 Zeilen) liegt das Einsparpotenzial bei **50–150 Tokens pro Handoff**, weil semantisch reiche Feldnamen wie `preliminary_requirements`, `termination_decisions`, `architectural_rationale`, `decomposition_completeness` jeweils 2–4 Tokens kosten.

**Empfehlung: Hybrid-Ansatz**
1. **Envelope-Felder:** Beibehalten als lesbare Namen. Die Ersparnis von 15 Tokens pro Handoff rechtfertigt den Breaking Change nicht (alle existierenden Schemas, Templates, PAL-Syntax müssten umgestellt werden).
2. **Payload-Felder ab v2:** Neue Payload-Schemas erhalten kurze, maschinenoptimierte Feldnamen (2–3 Zeichen) mit aussagekräftigem `title` und `description` fürs Debugging. Beispiel:

```json
// Statt:
{"preliminary_requirements": [{"statement": "...", "priority": "mandatory"}]}

// Künftig:
{"preq": [{"st": "...", "pri": "m"}]}
// Mit Schema: {"preq": {"title": "Preliminary Requirements", "items": {"properties": {"st": {"title": "Statement"}, "pri": {"title": "Priority", "enum": ["m","d","o"]}}}}}
```

3. **Debug-Mode:** Wenn `viz.debug: true` → Schema-Titel werden in Logs/Prompts aufgelöst, sodass Debugging menschenlesbar bleibt.

### 1.4 JSON vs. kompaktere Formate

**Option A — Standard-JSON (Status Quo):**
```json
{"protocol_version":"1.0.0","handoff_id":"HOFF-20260607-001","source_agent":"ideation","target_agent":"requirements","schema_ref":"schemas/…","payload":{}}
```
→ ~65 Tokens, universal verstanden, alle Provider unterstützen es nativ.

**Option B — JSON-Array (positionsbasiert):**
```json
["1.0.0","HOFF-20260607-001","ideation","requirements","schemas/…",{}]
```
→ ~38 Tokens (41% Ersparnis). Aber: **Kein JSON Schema Draft-07 validierbar** (Arrays haben keine benannten Properties, JSON Schema validiert Arrays über `items`-Schema — das ist möglich, aber Selbstdokumentation geht verloren). Zudem für LLMs potenziell verwirrend: Position 0 = Version? Oder Position 5? Fehleranfällig.

**Option C — YAML-Text-Block (für Continue/Copilot):**
```yaml
pv: "1.0.0"
hid: "HOFF-20260607-001"
src: "ideation"
tgt: "requirements"
sch: "schemas/…"
pl: {}
```
→ ~25 Tokens (62% Ersparnis). YAML-Key-Value ohne JSON-Syntax-Overhead. Aber: **Nicht JSON-Schema-validierbar** ohne Konvertierung. Zwei Formate bedeuten doppelte Wartung.

**Empfehlung:** JSON-Objekt beibehalten. Der Gewinn durch Array- oder YAML-Formate ist real, aber die Kosten (Validierungsverlust, Format-Dualität, LLM-Verwirrung bei positionalen Arrays) überwiegen. Stattdessen: **Kurze Feldnamen in Payload-Schemas** als primäre Optimierungsstrategie.

### 1.5 Optimierungsvorschläge (Priorisiert)

| # | Optimierung | Ersparnis pro Handoff | Aufwand | Risiko | Empfehlung |
|---|-------------|----------------------|---------|--------|------------|
| 1 | Kurze Payload-Feldnamen (neue Schemas) | 50–150 Tokens | Mittel (neue Schemas) | Gering (nur neue Schemas betroffen) | **Sofort umsetzen** |
| 2 | `schema_ref` optional machen, wenn default via Route implizit | ~20 Tokens | Gering | Mittel (Default-Erkennung nötig) | Phase 2 prüfen |
| 3 | `protocol_version` nur bei Major-Änderungen übertragen (default = aktuelle Version) | ~9 Tokens | Gering | Gering (Version im Schema implizit) | Phase 2 umsetzen |
| 4 | Envelope-Feldnamen kürzen | ~15 Tokens | Hoch (Breaking Change) | Hoch (alle Schemas, Templates, PAL) | **Nicht empfohlen** — Payload-Fokus statt Envelope |
| 5 | JSON-Array-Format | ~27 Tokens | Hoch | Hoch (Validierung, LLM-Verwirrung) | **Nicht empfohlen** |
| 6 | Binäres/komprimiertes Format (MessagePack, CBOR) | 60–80% | Sehr hoch | Extrem (kein Provider-Support) | **Nicht empfohlen** |

### 1.6 Faustregeln für Token-Budget

| Szenario | Max. Envelope-Overhead | Begründung |
|----------|----------------------|------------|
| Einfacher Handoff (TaskSpec) | ≤50 Tokens | Kurzer Task, wenig Kontext |
| Komplexer Handoff (SE-Decomposition) | ≤80 Tokens | Große Payloads, Overhead fällt weniger ins Gewicht |
| Supersession-Handoff | +20 Tokens | Zusätzliche Metadaten (version, supersedes, reason) |
| Debug-Mode (viz.debug: true) | +30 Tokens | trace_context, viz_task_id, metadata |

**Zielwert Session:** Maximal 10% des Session-Token-Budgets für A2A-Overhead. Bei einer 200K-Token-Session mit 20 Handoffs → max. 1.000 Tokens pro Handoff (Envelope + Nutzdaten).

---

## 2. Schema-Strategie

### 2.1 Standardisiertes Kern-Schema (TaskSpec)

**Vorschlag:** Ein universelles Payload-Schema für 60–80% aller Handoff-Routen:

```json
{
  "t": "Implementiere Login-Flow",          // task (string, required)
  "ctx": "Bestehender Auth-Service nutzen", // context (string, optional)
  "con": ["Muss OAuth2 unterstützen"],      // constraints (string[], optional)
  "refs": ["schemas/auth-api.json"],        // references (string[], optional)
  "pri": "high",                            // priority (enum: low|medium|high|critical)
  "dep": ["HOFF-20260607-042"]             // depends_on (handoff_id[], optional)
}
```

| Route | Passt in TaskSpec? | Fehlende Felder |
|-------|-------------------|-----------------|
| `ideation → requirements` | ⚠ Teilweise | `core_idea`, `goal`, `scope_v1` (braucht Erweiterung) |
| `requirements → developer` | ✓ | — |
| `requirements → se-architect` | ⚠ | SE-spezifische REQ-IDs |
| `orchestrator → developer` | ✓ | — |
| `feature → developer` | ✓ | — |
| `feature → git` | ✓ | — |
| `log-analyzer → feedback` | ✓ | — |
| `bug-feature-analyzer → developer` | ✓ | — |
| `bug-feature-analyzer → feature` | ✓ | — |
| `ui-ux-designer → developer` | ⚠ | Design-Spezifikationen |
| `api-specialist → developer` | ⚠ | API-Contract-Daten |
| `code-reviewer → developer` | ⚠ | Review-Feedback-Struktur |
| `se-orchestrator → se-requirements` | ✗ | SE-Stakeholder-REQs |
| `se-requirements → se-architect` | ✗ | SE-Decomposition-Daten |
| `se-architect → se-critic` | ✗ | SE-Decomposition-Daten |
| `se-critic → se-architect` | ✗ | Critic-Status + Hints |
| `se-critic → se-interface-mgr` | ✗ | SE-Decomposition-Daten |
| `se-interface-mgr → se-termination` | ✗ | SE-Decomposition-Daten |
| `se-termination → se-orchestrator` | ✗ | Termination-Decisions |

### 2.2 Abdeckungsanalyse: 80/20-Regel

| Kategorie | Routen | Anteil | Ansatz |
|-----------|--------|--------|--------|
| **TaskSpec-Delegation** (dev-ähnlich) | 8 | 42% | Reines TaskSpec |
| **Erweitertes TaskSpec** (spezialisierte Worker) | 4 | 21% | TaskSpec + 1–3 domain-spezifische Felder |
| **SE-Kaskade** (hochspezialisiert) | 7 | 37% | Eigenes Payload-Schema (SE-Decomposition) |

**Erkenntnis:** 63% der Routen (12/19) können mit TaskSpec oder TaskSpec+Extensions abgedeckt werden. Die 80%-Marke wird knapp verfehlt, aber **TaskSpec + 4 Extensions deckt 84%** — eine lohnende Abstraktion.

### 2.3 Per-Agent-Erweiterungen

Statt 19 einzelner Payload-Schemas → **1 Kern-Schema + 5 Extensions:**

```
TaskSpec (Core)
├── IdeationExtension    → ideation → requirements
├── DesignExtension      → ui-ux-designer → developer
├── APIExtension         → api-specialist → developer
├── ReviewExtension      → code-reviewer → developer
└── (SE-Decomposition)   → 7 SE-Routen (existierendes Schema bleibt)
```

**Extension-Mechanismus (analog zu JSON Schema `allOf`):**
```json
{
  "allOf": [
    {"$ref": "schemas/handoffs/task-spec.schema.json"},
    {"$ref": "schemas/handoffs/ext/ideation.schema.json"}
  ]
}
```

Dieser Ansatz:
- Reduziert Schema-Anzahl von 19 auf 6 (1 Core + 4 Extensions + 1 SE)
- Ermöglicht Wiederverwendung der Basis-Validierung
- Erlaubt agent-spezifische Felder ohne Schema-Duplizierung

### 2.4 JSON Schema Draft-07 vs. Draft-2020-12

| Feature | Draft-07 | Draft-2020-12 | agent-meta Relevanz |
|---------|----------|---------------|---------------------|
| `$ref` | ✓ | ✓ | Kritisch für Schema-Komposition |
| `allOf`/`oneOf`/`anyOf` | ✓ | ✓ | Extension-Mechanismus |
| `if`/`then`/`else` | ✓ | ✓ | Bedingte Validierung (supersession) |
| `$dynamicRef` | ✗ | ✓ | Nicht benötigt |
| `unevaluatedProperties` | ✗ | ✓ | Nützlich für "closed" Schemas |
| `prefixItems` (typed arrays) | ✗ | ✓ | Nicht benötigt |
| OpenAI `strict: true` | ✓ | ✗ | OpenAI unterstützt **nur** Draft-07 |

**Empfehlung: Draft-07 beibehalten.**
- OpenAI Structured Outputs (wichtigster Konsument für Validierung) unterstützt kein Draft-2020-12
- Alle benötigten Features (`$ref`, `allOf`, `if/then/else`) sind in Draft-07 vorhanden
- Kein Migrationsgrund erkennbar

### 2.5 Empfehlung

1. **TaskSpec als Kern-Schema definieren** (`schemas/handoffs/task-spec.schema.json`)
2. **4 Extensions für spezialisierte Worker** (Ideation, Design, API, Review)
3. **SE-Decomposition behalten** wie es ist — zu komplex für generisches Schema
4. **Neue Schemas ab sofort mit kurzen Feldnamen** (2–3 Zeichen, `title` für Lesbarkeit)
5. **Schema-Versionierung einführen:** `contract`-Feld in `role-defaults.yaml` schon existent → daraus `schema_ref` im Envelope ableiten

---

## 3. Orchestrator-Integration

### 3.1 FANOUT + A2A

**Szenario:** Orchestrator erkennt 3 unabhängige Bugfixes → FANOUT(3, developer, [Fix A, Fix B, Fix C])

**A2A-Strategie:** Ein Envelope pro FANOUT-Kind.

```
orchestrator erstellt:
  Envelope-1: {hid: "HOFF-001", src: "orchestrator", tgt: "developer", trace_parent: null, ...}
  Envelope-2: {hid: "HOFF-002", src: "orchestrator", tgt: "developer", trace_parent: null, ...}
  Envelope-3: {hid: "HOFF-003", src: "orchestrator", tgt: "developer", trace_parent: null, ...}
```

**Alle drei Envelopes** teilen dasselbe `trace_context.trace_id` (Session-Trace), aber haben unterschiedliche `handoff_id` und `trace_context.span_id`. Der Orchestrator selbst hat keinen `trace_parent` (er ist Wurzel).

**Token-Impact:** 3 × ~65 Tokens = ~195 Tokens Envelope-Overhead für den FANOUT. Bei `MAX_PARALLEL_AGENTS=4` und Batching (z.B. 8 Tasks → 2 Batches à 4) sind es maximal 4 × 65 = 260 Tokens Overhead pro Batch.

### 3.2 BARRIER + A2A

**Szenario:** Nach FANOUT(3) sammelt der Orchestrator Ergebnisse via BARRIER.

**A2A-Strategie:** Die Worker-Agenten produzieren jeweils einen **Response-Envelope** (optional, nur wenn `response_handoff: true` in `role-defaults.yaml`):

```
developer₁ → orchestrator:  Envelope mit Payload = {status: "success", commit: "abc123", changes: [...]}
developer₂ → orchestrator:  Envelope mit Payload = {status: "success", commit: "def456", changes: [...]}
developer₃ → orchestrator:  Envelope mit Payload = {status: "blocked", reason: "...", needs_clarification: true}
```

**Aggregation im Orchestrator:** Der Orchestrator erhält 3 Response-Envelopes, aggregiert sie in einem **Aggregations-Handoff** an sich selbst (oder direkt an den User-Report):

```json
{
  "pv": "1.0.0",
  "hid": "HOFF-AGG-001",
  "src": "orchestrator",
  "tgt": "orchestrator",  // Self-handoff für Aggregation
  "sch": "schemas/handoffs/aggregation-result.schema.json",
  "pl": {
    "batch_id": "HOFF-001",
    "results": [
      {"handoff_id": "HOFF-001", "status": "success"},
      {"handoff_id": "HOFF-002", "status": "success"},
      {"handoff_id": "HOFF-003", "status": "blocked", "reason": "needs clarification"}
    ]
  }
}
```

### 3.3 PIPELINE + A2A

**Szenario:** `requirements → tester → developer → tester → validator → git` (Feature-Lifecycle)

**A2A-Strategie:** Verkettete Envelopes via `trace_parent`:

```
HOFF-001: orchestrator → requirements  (trace_parent: null)
HOFF-002: requirements → tester       (trace_parent: HOFF-001)
HOFF-003: tester → developer          (trace_parent: HOFF-002)
HOFF-004: developer → tester          (trace_parent: HOFF-003)
HOFF-005: tester → validator          (trace_parent: HOFF-004)
HOFF-006: validator → git             (trace_parent: HOFF-005)
```

Diese Kette ermöglicht lückenloses Tracing: Wenn HOFF-004 fehlschlägt, kann der Orchestrator die gesamte Kette bis HOFF-001 zurückverfolgen und den Fehlerkontext rekonstruieren.

### 3.4 REPEAT_UNTIL + A2A

**Szenario:** SE-Critic-Zyklus (architect → critic → architect → critic → … bis approved)

**A2A-Strategie:** Supersession-Tracking via `supersedes`:

```
HOFF-010: se-architect → se-critic (v1, decomposition initial)
  → critic rejected
HOFF-011: se-architect → se-critic (v2, supersedes: HOFF-010, reason: "missing traceability")
  → critic rejected again
HOFF-012: se-architect → se-critic (v3, supersedes: HOFF-011, reason: "added traceability links")
  → critic approved
HOFF-013: se-critic → se-interface-mgr (supersession: [HOFF-010, HOFF-011, HOFF-012])
```

Der `se-interface-mgr` erhält die vollständige Revisionshistorie im `supersession`-Feld und kann nachvollziehen, welche Änderungen in welcher Iteration vorgenommen wurden. Dies ist bereits im Envelope-Schema vorgesehen (`supersession.version`, `supersession.supersedes`).

**Abbruchbedingung:** Wenn `MAX_CRITIC_ITERATIONS` erreicht ist → `critic_status.blocked` → Eskalation an `se-orchestrator` mit `supersession`-Historie + Begründung.

### 3.5 Orchestrator als Envelope-Produzent

Der Orchestrator ist der **primäre Envelope-Produzent**. Seine Rolle im A2A-Protokoll:

| Orchestrator-Funktion | A2A-Rolle |
|-----------------------|-----------|
| Intent-Routing | Bestimmt `target_agent` + `schema_ref`/`contract` aus Routing-Tabelle |
| Task-Decomposition | Erzeugt separate Envelopes pro Sub-Task |
| FANOUT | Produziert N parallele Envelopes mit gemeinsamem `trace_id` |
| BARRIER | Konsumiert Response-Envelopes, aggregiert Ergebnisse |
| PIPELINE | Verkettet Envelopes via `trace_parent` |
| REPEAT_UNTIL | Managed Supersession-Ketten |
| Unknown Intent | Erzeugt Meta-Feedback-Envelope (nicht A2A-format, sondern Issue) |

**Konfiguration in `.meta-config/project.yaml`:**
```yaml
orchestrator:
  handoff:
    protocol: "a2a-v1"
    validate-before-delegate: true    # Envelope-Validierung vor Delegation
    supersession-tracking: true       # Supersession-Ketten aktiv
    strict-validation: false          # true = Abbruch bei invaliden Handoffs
    compact-mode: false               # true = kurze Payload-Feldnamen (Token-sparend)
```

---

## 4. Altlasten-Migration

### 4.1 Betroffene Schemas

| Schema | Zeilen | Status | Migrationsansatz |
|--------|--------|--------|------------------|
| `schemas/se-decomposition.schema.json` | 317 | Existiert, aktiv genutzt | In A2A-Envelope einbetten (als Payload, unverändert) |
| `schemas/se-orchestrator.schema.json` | 140 | Existiert, aktiv genutzt | In A2A-Envelope einbetten (als Payload, unverändert) |
| `schemas/handoffs/ideation-output.schema.json` | 91 | Existiert, aktiv genutzt | In A2A-Envelope einbetten (bereits als erstes Payload-Schema vorgesehen) |
| 16 weitere (Konzept) | — | Nur im Konzept | Direkt als A2A-Payload-Schemas anlegen |

**Keines der existierenden Schemas muss geändert werden.** Der Migrationspfad ist rein additiv: Bestehendes Schema wird als `payload` in den A2A-Envelope eingebettet. Die Feldnamen bleiben erhalten, die Validierung bleibt identisch.

### 4.2 Migrationspfad

```
Phase 1 (heute):           Agent produziert Natural-Language-Prompt
                           → downstream-Agent parst semantisch

Phase 2 (Migration):       Agent produziert A2A-Envelope {
                             payload: <existierendes Schema unverändert>
                           }
                           → downstream-Agent parst envelope.payload

Phase 3 (Optimierung):     Neue Payload-Schemas mit kurzen Feldnamen
                           → downstream-Agent validiert gegen Schema
```

**Ablauf:**
1. `schemas/a2a-handoff.schema.json` ist bereits definiert (Phase 2 abgeschlossen)
2. `schemas/handoffs/ideation-output.schema.json` ist erstes Payload-Schema
3. Bestehende SE-Schemas (`se-decomposition`, `se-orchestrator`) werden **unverändert** als Payloads verwendet
4. Neue Routen erhalten neue Payload-Schemas (mit kurzen Feldnamen wo sinnvoll)

### 4.3 Deprecation-Strategie

**Keine Breaking Changes.** Das A2A-Protokoll wird **parallel** zum bestehenden Natural-Language-Prompt-System eingeführt:

1. **Opt-in:** Agenten deklarieren in `role-defaults.yaml` ihre `handoff`-Contracts. Solange kein Contract deklariert ist, delegieren sie wie bisher per Natural-Language-Prompt.
2. **Feature-Flag:** `orchestrator.handoff.protocol: "a2a-v1"` aktiviert das Protokoll. Bei `null` → Fallback auf Natural Language.
3. **Graceful Fallback:** Wenn ein downstream-Agent keinen Envelope parsen kann → fällt auf Natural-Language-Parsing zurück (wie heute).

```yaml
# role-defaults.yaml
roles:
  ideation:
    handoff:
      enabled: true              # A2A-Handoff aktiv?
      output_contract: "ideation-output-v1"
      output_schema: "schemas/handoffs/ideation-output.schema.json"
  git:
    # Kein handoff: Abschnitt → kein A2A, Natural Language wie bisher
```

---

## 5. Viz-Debug-Integration

### 5.1 Zwei-Ebenen-Modell (Wiederholung aus a2a-handoff-protocol.md)

| Ebene | System | Zweck | Tracking-ID | Event-Typen |
|-------|--------|-------|-------------|-------------|
| **Operational Layer** | viz-Handshake | *Dass* eine Delegation stattfand | `viz_task_id` | `agent_start`, `delegate_out`, `agent_end` |
| **Data Contract Layer** | A2A-Envelope | *Was* wurde übergeben | `handoff_id` | `a2a_handoff_start`, `a2a_handoff_validated`, `a2a_handoff_delivered` |

Die lose Kopplung erfolgt via `trace_context.viz_task_id` im A2A-Envelope.

### 5.2 Debug-Mode Konfiguration

```yaml
# .meta-config/project.yaml
viz:
  debug: false          # true = A2A-Events in viz loggen
  a2a_events:           # Welche A2A-Events loggen? (nur wenn debug: true)
    handoff_start: true
    handoff_validated: true
    handoff_delivered: true
    handoff_failed: true
    supersession: true
```

**Default: `viz.debug: false`** — A2A-Events werden nicht geloggt (spart Tokens und Log-Zeilen). Nur bei aktiver Fehlersuche einschalten.

### 5.3 A2A-Event-Typen

| Event | Auslöser | Payload |
|-------|----------|---------|
| `a2a_handoff_start` | Envelope wird erstellt | `{handoff_id, source_agent, target_agent, contract}` |
| `a2a_handoff_validated` | Validierung abgeschlossen | `{handoff_id, valid: bool, errors: [...]}` |
| `a2a_handoff_delivered` | Downstream akzeptiert | `{handoff_id, status: accepted|rejected|superseded}` |
| `a2a_handoff_failed` | Validierung fehlgeschlagen | `{handoff_id, errors: [...]}` |
| `a2a_supersession` | Supersession erstellt | `{handoff_id, supersedes: handoff_id, reason}` |

**Integration in viz-logger (MCP/CLI):**
```bash
# MCP (primär):
log_viz_event --event a2a_handoff_start --task_id uuid-X \
  --caller se-orchestrator --payload '{"handoff_id":"HOFF-001","contract":"se-arch-output-v1"}'

# CLI (Fallback):
python scripts/viz-logger.py --event a2a_handoff_validated \
  --agent se-architect --provider Opencode --task_id uuid-X \
  --caller se-orchestrator \
  --payload '{"handoff_id":"HOFF-001","valid":true}'
```

### 5.4 Performance-Impact

| Modus | Zusätzliche viz-Calls pro Handoff | Token-Impact (Prompt-Injection) | Log-Zeilen |
|-------|----------------------------------|--------------------------------|------------|
| `viz.debug: false` (Default) | 0 | 0 Tokens | 0 |
| `viz.debug: true` | 3–5 | ~30 Tokens (Prompt-Block für Event-Instruktionen) | 3–5 pro Handoff |
| `viz.debug: true` + `viz.a2a_events.supersession: true` | 3–5 + Supersession | ~30 Tokens | 4–6 pro Handoff |

**Empfehlung:** Debug-Mode in Produktion deaktiviert lassen. Nur bei der Entwicklung neuer Handoff-Routen oder bei Fehlersuche in SE-Kaskaden einschalten.

---

## 6. Vergleich mit existierenden Systemen

### 6.1 W3C ANP (Agent Network Protocol)

**Status:** White Paper war zum Recherche-Zeitpunkt nicht mehr öffentlich verfügbar (URL führte zu 404).

**Relevante Konzepte (aus Sekundärquellen):**
- **Agent Discovery:** Agenten registrieren ihre Fähigkeiten in einem zentralen Verzeichnis
- **Capability Negotiation:** Agenten handeln aus, welche Protokollversion sie sprechen
- **Structured Messages:** Formale Nachrichtenformate mit Schema-Validierung

**Abgleich mit agent-meta:**
- Agent Discovery → `config/role-defaults.yaml` + `config/provider-capabilities.yaml` (statisch, nicht dynamisch)
- Capability Negotiation → `handoff_format`-Flag (`json` vs. `yaml_text_block`) pro Provider
- Structured Messages → A2A-Envelope + JSON Schema

**Fazit:** agent-meta hat die ANP-Konzepte implizit übernommen, aber in einer statisch deklarierten Form (kein dynamisches Discovery). Für den agent-meta-Use-Case (bekannte Agenten-Rollen in einem Projekt) ist statische Deklaration ausreichend und effizienter.

### 6.2 MCP (Model Context Protocol)

**Status:** Aktiver, offener Standard von Anthropik. Primär für Tool-Integration zwischen LLM und externen Diensten.

**Relevanz für agent-meta:**
- **MCP-Server als Schema-Registry:** `resolve-handoff-schema` Tool (geplant in Phase 7)
- **MCP-Server als Validator:** `validate-handoff` Tool (geplant in Phase 7)
- **MCP-Server als Capability-Discovery:** `agent-meta-handoff` Tool (geplant)

**Integrationstiefe:**
```
┌──────────────────────────────────────────┐
│              agent-meta                    │
│  ┌──────────────────────────────────────┐ │
│  │  A2A-Envelope (JSON Schema Draft-07) │ │
│  │  Payload-Schemas                     │ │
│  │  Handoff-Routen                      │ │
│  └──────────────┬───────────────────────┘ │
│                 │                          │
│  ┌──────────────▼───────────────────────┐ │
│  │  MCP-Server (viz-logger.py)          │ │
│  │  • log_viz_event (Operational)       │ │
│  │  • resolve-handoff-schema (Phase 7)  │ │
│  │  • validate-handoff (Phase 7)        │ │
│  └──────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

**Fazit:** MCP ist der natürliche Transport-Layer für Schema-Resolution und Validierung. Der existierende `viz-logger.py` MCP-Server ist bereits der Operational-Layer-Handshake. Die Erweiterung um Schema-Tools ist in Phase 7 der Roadmap vorgesehen.

### 6.3 OpenAI Structured Outputs

**Status:** Produktionsreif. JSON Schema Draft-07 mit `strict: true` Modus.

**Relevante Merkmale:**
- Garantiert 100% Schema-Adhärenz (kein "best effort")
- `strict: true` erfordert: alle Properties in `required`, kein `additionalProperties: true` auf oberster Ebene
- Pydantic/Zod SDK-Integration für Schema-Generierung
- Nur Draft-07 (nicht 2020-12)

**Abgleich mit agent-meta:**
- agent-meta nutzt JSON Schema Draft-07 (Kompatibilität gegeben)
- agent-meta's Envelope hat `"additionalProperties": false` implizit auf oberster Ebene (nur definierte Properties)
- **Unterschied:** agent-meta's Envelopes werden von LLM-Agenten **produziert** (nicht via API `response_format`), daher keine `strict: true`-Garantie, sondern **Post-hoc-Validierung**

**Fazit:** agent-meta sollte Draft-07 beibehalten (OpenAI-Kompatibilität). Der Validierungsansatz (Post-hoc statt API-native) ist dem agent-meta-Architekturmodell geschuldet (Agenten produzieren Envelopes als Teil ihres Outputs, nicht via Structured-Output-API).

### 6.4 CrewAI / AutoGen / LangGraph

| Framework | Handoff-Konzept | Format | Stärke | Schwäche |
|-----------|----------------|--------|--------|----------|
| **CrewAI** | Task-Delegation via Tool-Calls | Internes Objekt | Einfach, Python-nativ | Kein formales Schema, kein Supersession |
| **AutoGen** | Agent-Chat (Message-basiert) | Dict/JSON | Multi-Agent-Konversationen | Kein standardisiertes Format |
| **LangGraph** | State-Graph (Nodes + Edges) | Python-TypedDict | State-Management, Checkpoints | Kein standardisiertes Format |

**agent-meta's Differenzierung:**
- **Formaler als CrewAI/AutoGen:** JSON Schema + Validierung an jeder Grenze
- **Provider-agnostischer als LangGraph:** Gleiches Protokoll auf Claude, Opencode, Gemini, Continue, Copilot
- **Supersession-Tracking:** Keines der Frameworks hat ein vergleichbares Konzept
- **Token-Effizienz:** Keines der Frameworks optimiert für LLM-Token-Kosten

**Fazit:** agent-meta's A2A-Protokoll ist formaler und provider-agnostischer als die Konkurrenz. Der Preis dafür ist höhere Komplexität in der Schema-Pflege — die durch TaskSpec-Abstraktion reduziert werden kann.

---

## 7. Implementationsempfehlungen

### 7.1 Phase 1: Sofort umsetzbar (Quick Wins)

| # | Maßnahme | Aufwand | Impact | Risiko |
|---|----------|---------|--------|--------|
| 1 | **TaskSpec-Kern-Schema definieren** (`schemas/handoffs/task-spec.schema.json`) | 1 Tag | 63% Routen-Abdeckung | Gering |
| 2 | **Kurze Feldnamen für neue Payload-Schemas** (Konvention im Team etablieren) | 0 Tage (Konvention) | 50–150 Tokens/Handoff | Gering |
| 3 | **`orchestrator.handoff`-Config-Block** in `.meta-config/project.yaml` dokumentieren | 0,5 Tage | Klare Steuerung | Kein |
| 4 | **Handoff-Routen-Tabelle** im Orchestrator-Template ergänzen | 0,5 Tage | Routing-Klarheit | Gering |
| 5 | **Payload-Feldnamen-Checkliste** in `howto/` dokumentieren | 0,5 Tage | Konsistenz | Kein |

### 7.2 Phase 2: Mittelfristig (1–2 Wochen)

| # | Maßnahme | Aufwand | Impact | Risiko |
|---|----------|---------|--------|--------|
| 6 | **4 TaskSpec-Extensions implementieren** (Ideation, Design, API, Review) | 2 Tage | 84% Routen-Abdeckung | Gering |
| 7 | **`{{PAL_HANDOFF}}`-Platzhalter** in `delegation-syntax.yaml` für alle 5 Provider | 1 Tag | Provider-agnostische Syntax | Mittel |
| 8 | **Orchestrator-Integration:** FANOUT/BARRIER/PIPELINE mit A2A-Envelopes | 2 Tage | Tracking aller Delegationen | Mittel |
| 9 | **`schema_ref` implizit aus Route ableiten** (optionales Feld im Envelope) | 0,5 Tage | ~20 Tokens/Handoff Ersparnis | Gering |
| 10 | **A2A-Event-Typen** in `viz-logger.py` integrieren (hinter `viz.debug: true`) | 1 Tag | Debugging-Fähigkeit | Gering |

### 7.3 Phase 3: Langfristig (Roadmap)

| # | Maßnahme | Aufwand | Impact | Risiko |
|---|----------|---------|--------|--------|
| 11 | **MCP-Schema-Tools:** `resolve-handoff-schema`, `validate-handoff` | 2–3 Tage | Dynamische Validierung | Mittel |
| 12 | **Response-Envelopes** (Worker → Orchestrator) standardisieren | 2 Tage | Geschlossener Feedback-Loop | Mittel |
| 13 | **Token-Budget-Tracking** im Orchestrator (Session-weit) | 1 Tag | Kostenkontrolle | Gering |
| 14 | **Payload-Kompression** (MessagePack/CBOR) für >10K Token Payloads | — | Nur bei Bedarf | Hoch |
| 15 | **Handoff-Analytics-Dashboard** (viz-graph Erweiterung) | 3 Tage | Visuelles Tracking | Gering |

### 7.4 Priorisierungs-Matrix

```
                    Hoch
                     │
        6,7,8        │  1,2,3,4,5
        (Phase 2)    │  (Phase 1 — Quick Wins)
                     │
    Aufwand ─────────┼──────────→ Impact
                     │
        14,15        │  9,10,11,12,13
        (Später)     │  (Phase 2/3)
                     │
                    Gering
```

**Zusammenfassung der Kern-Empfehlungen:**

1. **Envelope-Feldnamen lang lassen** — Breaking Change lohnt nicht (15 Tokens Ersparnis vs. Migration aller Schemas)
2. **Payload-Feldnamen kurz machen** — ab sofort für neue Schemas (50–150 Tokens Ersparnis pro Handoff, kein Breaking Change)
3. **TaskSpec als universelles Kern-Schema** einführen — deckt 63% der Routen ab, mit 4 Extensions 84%
4. **Draft-07 beibehalten** — OpenAI-Kompatibilität, alle benötigten Features vorhanden
5. **Orchestrator als Envelope-Fabrik** — produziert, validiert, trackt alle Handoffs
6. **Supersession als Killer-Feature** — kein anderes Framework hat vergleichbares Revision-Tracking
7. **Debug-Mode optional** (`viz.debug: false` default) — keine Token-Kosten im Produktivbetrieb
8. **Additive Migration** — existierende Schemas unverändert einbetten, keine Breaking Changes

---

> **Nächster Schritt:** Übergabe an `requirements`-Agenten für formale REQ-Erfassung der Phase-1-Maßnahmen.
