# SE Metrics Reporting — Design (Issue #330)

> Issue: #330 — Metrik-Reporting für die SE-Kaskade
> Relevante REQs: REQ-SE-01, REQ-SE-02, REQ-SE-03, REQ-SE-04, REQ-SE-05 (Persistenzbasis, `docs/REQUIREMENTS.md:41-45`)
> Status: **DESIGN-DOKUMENT** — implementierungsreif, aber die Umsetzung bleibt durch die
> Do-Not-Implement-Klausel des Issues gesperrt („Do NOT implement yet; concept phase: metrics data
> model and collection strategy needed"). Dieses Dokument liefert genau das: Datenmodell (§4) und
> Sammel-Strategie (§5); die Implementierung startet erst nach expliziter Freigabe auf #330.

---

## 1. Ziel und Scope

Die SE-Kaskade erzeugt heute zwar persistierte Artefakte, aber keine maschinenlesbaren,
aggregierbaren Prozess- und Qualitätskennzahlen. Dies Design definiert:

1. **Metrik-Definitionen** — Requirements Volatility Index (RVI), Test-/V&V-Abdeckung,
   Traceability-Gaps, Budget-/Prozessmetriken (§3).
2. **Datenmodell** — `schemas/se-metrics.schema.json` + append-only `.se-metrics.jsonl` (§4).
3. **Sammel-Strategie** — Runner-seitige Collection ohne Pflichtänderungen an Agent-Outputs (§5).
4. **Export/Dashboard-Konzept** — `metrics.md` als generiertes MD-Artefakt (§6).
5. **Schwellwert-Konfiguration** — `project.yaml`-Keys mit Gate-Wirkung warn/reject (§7–8).

Nicht im Scope: Budget-**Enforcement** (Abbruch-Logik gehört zu #207/Runner — hier wird nur
**berichtet**), Baseline-/CR-Mechanik (#329, eigenes Design — hier wird nur verdrahtet), Admin-UI-
Implementierung (nur Konzept §6.2).

---

## 2. Datenquellen (alle bestehend, ohne neuen Zwang an Agenten)

| Quelle | Inhalt | Referenz |
|---|---|---|
| Persistierte SE-Artefakte (`docs/se/<projektname>/`) | REQ/ARCH/IF/Termination/Validation-Dateien mit Frontmatter `step, agent, iteration, status, timestamp, schema_version` | REQ-SE-01/02 (`docs/REQUIREMENTS.md:41-42`), Schritt-Tabelle `docs/se-cascade/se-resume-session.md:36-46` |
| `.se-state.yaml` | `budget_consumed {cells, tokens, estimated_eur}`, `last_completed_step`, `current_level/current_node` | REQ-SE-03, `schemas/se-state.schema.json:69-86`; Beispiel `se-resume-session.md:93-113` |
| Review-Protokolle + Critic-Endreports | `reviews/REVIEW_<YYYY-MM-DD>_<scope>.md` (RVW-IDs, Status `open|response|closed`) + `reports/{FolderName}/*_critic_report.md` (mit `iteration_history`) = implizite Rejections-Zählung (Datei-Analyse, kein neues Feld) | Taxonomie `rules/1-generic/se-cascade-artifact-taxonomy.md` (#334), Protokoll-Lifecycle `rules/1-generic/se-cascade-review-lifecycle.md` |
| Validation-Outputs | `validation/L{n}_<Node>_Validation.md` + `_TestPlan.md` (se-validator / se-verifier / se-integration-and-test-manager) | `se-resume-session.md:45-46`; `parallel_group`-Stufe `quality_pipelines.se-cascade` → Stage `validation` in `config/role-defaults.yaml` |
| Traceability-Matrix + Interface-Registry | Parent-Child-Bezüge, IF-Registry-Tabelle | `docs/se-cascade/se-workflow.md:164-174` |
| Developer-Results (`dev-result-v1`) | `status`, `artifacts`, `interfaces_implemented`, `test_coverage` | `docs/architecture/07-se-cascade.md:95-99` |
| run-cascade-Session-Meta (Phase-1-Runner) | `current_stage`, `completed_stages`, Session-Layout `.se-cascade/<session>/` | `scripts/run-cascade.py:104-106,128-139` |
| Baseline/CR-Artefakte (falls #329 aktiv) | `baseline-manifest*.yaml`, `changes/CR-*.md`, `cr-registry.md` | `docs/se-cascade/se-baseline-change-control-design.md` §§3, 5, 7 |

Prinzip: **Jede** Metrik ist aus bestehenden Artefakten ableitbar (deterministisch, stdlib-Parser).
Artefakt-Locations folgen der Artefakt-Taxonomie (`rules/1-generic/se-cascade-artifact-taxonomy.md`,
Issue #334, umgesetzt in `agents/1-generic/se-architect.md`/`se-critic.md`): kanonische Final-Namen
ohne Suffix, Review-Protokolle unter `reviews/`, Critic-Endreports unter `reports/{FolderName}/` —
Metriken sampeln an diesen kanonischen Orten, **nicht** an `.iter`/`.final`-Suffix-Dateien (die
REQ-SE-02-Suffix-Dateien im wörtlichen Sinn existieren nicht mehr). Keine Metrik erfordert ein
neues Pflichtfeld in Agent-Outputs — Agent-Prompts und -Schemas
(`schemas/se-requirements.schema.json`, `se-critic.schema.json`, `se-decomposition.schema.json`)
bleiben unverändert.

---

## 3. Metrik-Definitionen

### 3.1 Requirements Volatility Index (RVI)

**Definition (mit #329-Baseline):**

```
RVI(L, fenster) = |REQ-L{L}, die nach erstmaliger Critic-Approval geändert/neu/gestrichen wurden|
                  / |REQ-L{L} total (Stand Ende des Fensters)|
```

- Einheit: Anteil in [0.0, 1.0], pro Zerlegungsebene L und optional pro Node.
- „Nach Approval geändert" = Statement-Body-Diff eines REQ-Blocks über Baseline-Versionen hinweg
  (CR-Historie aus `changes/CR-*.md` + Manifest-`last_cr`, `se-baseline-change-control-design.md` §7)
  ODER Neuaufnahme/Streichung zwischen Baseline v(n-1) und v(n).
- Diff-Granularität: REQ-Block (ID-Anker), nicht ganze Datei — ein REQ-Umbau in derselben Datei
  zählt nur für die betroffenen REQ-IDs.

**Definition (Pre-Baseline-Proxy, ohne #329):**

```
RVI-Proxy(L) = |REQ mit Body-Diff zwischen erster Approval und Final-Stand| / |REQ total|
```

- Nutzt die Review-Protokoll-Serie (REQ-SE-02, Taxonomie #334): erster Critic-Approval
  (RVW-Protokoll `closed` / REQ-Frontmatter `review_iteration: 1`) vs. aktueller Final-Stand.
  Body-Hash je REQ-Block über die **Git-History des kanonischen REQ-Dateinamens**
  (`L{n}_{Node}_Requirements.md` — Versionierung via Git, nicht via Datei-Suffixe);
  Differenz = volatile REQ.
- Bewusster Charakter: **Trendmetrik, kein Absolutwert** — der Proxy misst Volatilität innerhalb
  der Critic-Schleife, nicht über Projektgrenzen. Schwellwerte (§7) gelten für beide Varianten,
  mit dem Hinweis „Proxy" im Report.

### 3.2 Test- und V&V-Abdeckungsmetriken

| Metrik | Definition | Quelle |
|---|---|---|
| **AC-Coverage je Leaf** | \|implementierte Test-Referenzen in `dev-result-v1.test_coverage`\| / \|`acceptance_criteria` in `task-spec-v1`\| | `docs/architecture/07-se-cascade.md:89-99` (beide Felder existieren im Vertrag) |
| **Leaf-Validationsquote** | \|Leafs mit persistiertem Validation-Ergebnis\| / \|Software-Leafs gesamt\| | `validation/`-Verzeichnis (Pfade `se-resume-session.md:45-46`) |
| **V&V-Completeness** | 3/3-Stufencheck: se-validator (User-Journeys) · se-verifier (Multi-Level) · se-integration-and-test-manager (Testplan) je Ebene erledigt | `parallel_group`-Stufe, `quality_pipelines.se-cascade` → Stage `validation` in `config/role-defaults.yaml` |
| **Defekt-Dichte je Zelle** | Critic-Rejections / Zelle (`iteration_history` im Critic-Endreport bzw. `review_iteration` im REQ/ARCH-Frontmatter) | Analyse der Critic-Endreports (`reports/{FolderName}/`) bzw. Frontmatter-`review_state` (Taxonomie #334) |
| **Eskalationsquote** | `blocked`-Eskalationen / Critic-Runs | Critic-Verdicts (Eskalationspfad `docs/architecture/07-se-cascade.md:289-292`) |

### 3.3 Traceability-Gap-Report

Fünf deterministische Gap-Klassen, alle aus Artefakt-Parsen ableitbar:

| Gap-Klasse | Regel | Quelle |
|---|---|---|
| **G1 Orphan-REQ** | REQ-L{n} ohne ARCH-Bezug (keine Sub-Komponente referenziert sie) | `requirements/` ∩ `architecture/`-Rationale/Sub-Components |
| **G2 Waisen-ARCH-Element** | Sub-Komponente ohne Parent-REQ-Bezug | `architecture/` ∩ Parent-REQ-Liste |
| **G3 Hängendes Interface** | IF in der Interface-Registry ohne Consumer ODER ohne Provider | `interfaces/`-Registry-Tabelle (`se-workflow.md:171`) |
| **G4 Unimplementiertes Software-Leaf** | `domain: software` + Termination `leaf`, aber kein `dev-result-v1` | `termination/`-Decisions ∩ `implementation/`-Outputs |
| **G5 Unvalidiertes Leaf** | Implementiertes Leaf ohne Validation-Ergebnis | `implementation/` ∩ `validation/` |

Output: je Ebene eine Gap-Tabelle (human) + strukturiert im JSONL (maschinenlesbar). Gaps sind
**Zählmetrik + Liste** (die Liste ist der eigentlich wertvolle Teil — die Zählung steuert nur das
Gate §8).

### 3.4 Budget- und Prozessmetriken

| Metrik | Definition | Quelle |
|---|---|---|
| **Zellennutzung** | `budget_consumed.cells / SE_MAX_CELLS` | `.se-state.yaml` vs. `se_variables` → `SE_MAX_CELLS` (`config/role-defaults.yaml`) |
| **Tiefennutzung** | `current_level-Numerik / SE_MAX_DEPTH` | `.se-state.yaml` vs. `se_variables` → `SE_MAX_DEPTH` (MIN/MAX-Band) |
| **Critic-Loop-Auslastung** | max. beobachtete Iterationen / `SE_MAX_CRITIC_ITERATIONS` | Critic-Endreports (`iteration_history`, `reports/{FolderName}/`) vs. `se_variables` → `SE_MAX_CRITIC_ITERATIONS` |
| **Budget-Auslastung** | `budget_consumed.estimated_eur / cost_limit_eur` | `se_variables` → `cost_limit_eur` |
| **Budget-Forecast** | linearer Ausbauprognose: EUR pro abgeschlossener Stufe × Stufen bis `SE_MAX_DEPTH` | `.se-state.yaml`-Serie über Zeitstempel (REQ-SE-01-`timestamp`) |
| **Stage-Durchlauf** | `completed_stages`-Länge + `current_stage` je Session | `scripts/run-cascade.py:128-139` (Phase-1-Runner) |

Hinweis: `estimated_eur` bleibt eine **Schätzung** (Token-Modellpreise driften); der Forecast ist
eine Orientierung, kein Zusagen-Metriken-Konstrukt.

---

## 4. Datenmodell

### 4.1 `schemas/se-metrics.schema.json` (Vorschlag)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SE Metrics Event",
  "description": "Ein Event pro abgeschlossenem SE-Stufenschritt; append-only JSONL.",
  "type": "object",
  "required": ["ts", "session_id", "stage_id", "agent", "status"],
  "properties": {
    "ts":            { "type": "string", "format": "date-time" },
    "session_id":    { "type": "string" },
    "pipeline":      { "type": "string", "description": "Pipeline-ID (default: se-cascade-Variante)" },
    "level":         { "type": "string", "pattern": "^L[0-9]+$" },
    "node":          { "type": "string" },
    "stage_id":      { "type": "string" },
    "agent":         { "type": "string" },
    "iteration":     { "type": "integer", "minimum": 1 },
    "status":        { "type": "string", "enum": ["approved", "rejected", "done", "partial", "blocked"] },
    "rvi":           { "type": "object",
                       "description": "RVI je Ebene; key=L{n}; value-Objekt mit ratio + proxy-Flag",
                       "additionalProperties": { "type": "object",
                         "properties": { "ratio": { "type": "number" }, "proxy": { "type": "boolean" } } } },
    "coverage":      { "type": "object",
                       "properties": {
                         "leaves_total":            { "type": "integer" },
                         "leaves_with_tests":       { "type": "integer" },
                         "ac_coverage_ratio":       { "type": "number" },
                         "vv_completeness":         { "type": "integer", "minimum": 0, "maximum": 3 } } },
    "gaps":          { "type": "object",
                       "properties": {
                         "g1_orphan_req":   { "type": "array", "items": { "type": "string" } },
                         "g2_orphan_arch":  { "type": "array", "items": { "type": "string" } },
                         "g3_hanging_if":   { "type": "array", "items": { "type": "string" } },
                         "g4_unimpl_leaf":  { "type": "array", "items": { "type": "string" } },
                         "g5_unvalidated_leaf": { "type": "array", "items": { "type": "string" } } } },
    "budget":        { "type": "object",
                       "properties": {
                         "cells":          { "type": "integer" },
                         "tokens":         { "type": "integer" },
                         "estimated_eur":  { "type": "number" } } }
  }
}
```

### 4.2 Speicher: `.se-metrics.jsonl`

- Pfad: `docs/se/<projektname>/.se-metrics.jsonl` (Punkt-Datei analog `.se-state.yaml` —
  Arbeitszustand, kein Lieferartefakt).
- **Append-only, eine JSON-Zeile pro Stufen-Abschluss.** Append pro Zeile ist atomar genug
  (kurze Zeilen, single write) und resistent gegen Crash-Mitten (letzte Teilzeile wird beim
  Lesen verworfen, vorherige Zeilen bleiben gültig).
- Resume-kompatibel: nach Token-Loss liest der Collector die bestehende JSONL und setzt fort
  (verträglich mit REQ-SE-03-Resume-Algorithmus).

---

## 5. Sammel-Strategie

### 5.1 Prinzip: Runner-seitige Collection, keine Agent-Selbstauskunftspflicht

- **Der Collector ist deterministischer Code** (stdlib: `json`, `hashlib`, `pathlib`) und läuft im
  Koordinator-Kontext — Hauptschritt `orchestrator` (SE-Mode) bzw. künftig der Runner aus #207.
  Der Collector hat denselben Platz wie der Freeze aus #329: kein neuer Agent, keine neue
  LLM-Stufe.
- Agent-Outputs bleiben unverändert Pflicht. **Optionale additive Erweiterung erlaubt:** Agenten
  DÜRFEN in ihr Frontmatter einen `metrics:`-Block schreiben (z. B. `test_coverage`-Zähler direkt
  beim Developer); der Collector nutzt ihn, falls vorhanden, sonst leitet er ab. Kein
  Breaking-Change, kein Schema-Zwang.

### 5.2 Collection-Points

| # | Punkt | Aktion |
|---|---|---|
| 1 | Nach jedem Stage-Completion (REQ-SE-01-Write) | Append eines Events (§4) mit dem Status/Frontmatter des gerade abgeschlossenen Schritts |
| 2 | Nach Critic-Loop-Abschluss | Append mit Iterations-/Eskalationszählung (§3.2 Defekt-Dichte) |
| 3 | Nach V&V-`parallel_group` | Append mit V&V-Completeness + Leaf-Validationsquote |
| 4 | SE-Ende (Traceability-Matrix) | Append mit Gap-Report + RVI + Budget-Summe → Triggert Export (§6) |
| 5 | Session-Resume | JSONL-Line-Replay: bestehende Events einlesen, `budget_consumed` und Zähler fortsetzen |

### 5.3 Verhältnis zu #329 und #207

- **#329 (Baseline):** Freeze-Vorbereitung fordert `gaps == 0` (alle 5 Klassen leer) als Freeze-Prüfung
  (§8-Gate-Wirkung); RVI erhält exakte Werte erst mit CR-Historie, vorher läuft der Proxy (§3.1).
- **#207 (Runner):** Budget-**Zählung** (cells/tokens/EUR pflegen) bleibt Runner-Aufgabe; der
  Metrics-Collector **konsumiert** `budget_consumed` nur. Keine doppelte Buchhaltung: ein
  Schreiber (Runner/Coordinator), ein Leser (Collector).
- **#652-Status:** die Pipeline ist deaktiviert (`.meta-config/project.yaml` →
  `quality-pipelines.overrides.se-cascade.enabled: false`,
  `docs/architecture/07-se-cascade.md:7-10`) — die Metrics-Funktion erbt denselben Override:
  `enabled: false` der Pipeline ⇒ keine Collection (keine side-effect-Dateien neben einer
  deaktivierten Pipeline).

---

## 6. Export- und Dashboard-Konzept

### 6.1 Phase 1: `metrics.md` (generiertes MD-Artefakt)

- Pfad: `docs/se/<projektname>/metrics.md`; **immer** aus der JSONL regeneriert, nie handeditiert
  (generiert-Charakter analog Managed-Blöcken — Regenerate = idempotenter Voll-Rebuild).
- Inhalt: (1) RVI-Trend je Ebene (Tabelle + Mermaid-Trend), (2) Coverage-Tabelle je Leaf,
  (3) Gap-Report-Tabellen (5 Klassen, mit Pfadlisten), (4) Budget-Tabelle (Ist/Soll-Grenzen,
  Forecast), (5) Stage-Durchlauf-Tabelle je Session.
- Format folgt dem MD-Adapter-Muster (default-Adapter, `docs/se-cascade/se-mcp-adapters.md:14-21`) —
  Mermaid-Bausteine wie in den se-cascade-Doku-Dateien (`se-workflow.md:31-50`,
  `docs/architecture/07-se-cascade.md:27-67`).
- Idempotenz-AK: zweimalige Regeneration aus identischer JSONL = byte-identisches `metrics.md`.

### 6.2 Phase 2 (Konzept, bewusst nicht Teil der Implementierung): Admin-UI-Page

- Muster-Schablonen existieren: Sidebar + `router.register` (`docs/ui/admin-ui.html:9793-9812`),
  iframe-Embed-Page als Vorlage (`viewVizDashboard`, `admin-ui.html:8071`), Config-Sektion
  via `_write_project_section`-Allowed-Set (`scripts/admin-server.py:4603-4631`).
- Ein Seeding im Admin-UI wäre: read-only Render der JSONL-Aggregate (keine Config-Writes nötig).
  **Diese Phase ist hier nur skizziert** — die Implementierung braucht ein eigenes, separates
  Task mit den UI-Tests-Konventionen aus `tests/browser/` (inkl. pytest_socket-Constraint,
  siehe Phase-4d-Follow-ups §5).

---

## 7. Schwellwert-Konfiguration (project.yaml)

Ablageort: `se_variables`-Block in `config/role-defaults.yaml` (Defaults), Override via
`variables` in `.meta-config/project.yaml` — identisches Muster wie der #329-Entwurf (§8 dort).

```yaml
# se_variables (config/role-defaults.yaml) — Neuvorschläge:
SE_METRICS_ENABLED: false        # false = keine Collection, keine Dateien, keine Warnungen
SE_METRICS_FILE: ".se-metrics.jsonl"   # relativ zu docs/se/<projektname>/
SE_RVI_WARN: 0.20                # RVI > warn  → SyncLog-Warnung + Report-Marker
SE_RVI_REJECT: 0.50              # RVI > reject → Stage-Auf-Ebene-Nicht-Fortsetzung (§8)
SE_COVERAGE_MIN: 0.80            # AC-Coverage je Leaf (§3.2); Leaf-Fails → Gap G5-naher Befund
SE_TRACE_GAPS_MAX: 0             # max. offene Gaps (Summe G1–G5) vor Baseline-Freeze (§8)
SE_BUDGET_WARN_EUR: null         # null = 0.8 * cost_limit_eur (aus `se_variables` → `cost_limit_eur`)
```

Regeln:

- `SE_METRICS_ENABLED: false` (Default) = **byte-identisches Verhalten** (keine Dateien, keine
  Pipeline-Deltas). Aktivierung ist ein expliziter Projekt-Opt-in — konsistent mit dem
  deaktivierten SE-Cascade-Status (#652).
- Neue Platzhalter in `scripts/lib/consistency/placeholders.py` registrieren (SE-Liste dort:
  Zeilen 86–87) — Implementierungshinweis.
- `SE_TRACE_GAPS_MAX: 0` ist der harte Kopplungspunkt an #329: ein Freeze mit offenen Gaps
  ist ein Prozessfehler (nicht blockiert durch dieses Design allein, sondern durch die
  Freeze-Vorprüfung im #329-Fluss, die diese Zahl konsumiert).

---

## 8. Gate-Wirkung (warn vs. reject)

| Schwelle | Wirkung | Mechanik |
|---|---|---|
| `SE_RVI_WARN`, `SE_BUDGET_WARN_EUR` | **warn** — Pipeline läuft weiter | SyncLog-Warnung + Marker in `metrics.md` |
| `SE_RVI_REJECT` | **reject auf Ebene** — Ebene wird nicht als abgeschlossen gemeldet | Eskalation an Parent-Zelle/`orchestrator` — dasselbe Muster wie Critic-`blocked` (`docs/architecture/07-se-cascade.md:289-292`); das Reject-Event selbst wird geloggt (§4-Event `status: rejected`) |
| `SE_COVERAGE_MIN` | **reject auf Leaf-Ebene** — Leaf gilt nicht als done | Leaf verlässt nicht den Implementation-Loop (`max_iterations: 2`, `quality_pipelines.se-cascade` → Stage `implementation` in `config/role-defaults.yaml`) |
| `SE_TRACE_GAPS_MAX` | **block vor Freeze** — Prüfung im #329-Freeze-Ablauf | Freeze wird nicht ausgelöst, bis Gaps leer sind |

Auch bei Reject gilt: **Der Collector blockiert nichts selbst** — er berechnet und meldet; die
Blockier-Entscheidung fällt im Koordinator/Runner (dieselbe Trennung wie bei #329: Gate ist
Prozessregel, Collector ist Messinstrument).

---

## 9. Implementierungs-Akzeptanzkriterien (für die spätere Freigabe)

- [ ] RVI (beide Varianten), Coverage, Gaps, Budget — je mit deterministischem Test-Fixture
      (minimaler `docs/se/`-Baum in `tmp_path`, Fixture-Pattern analog `tests/test_se_persistence.py`).
- [ ] `.se-metrics.jsonl` append-only; Line-Replay über Resume hinweg korrekt (Crash-Mitte verwirft
      nur die letzte Teilzeile).
- [ ] `metrics.md` aus JSONL regenerierbar, idempotent (zweimal erzeugen = byte-identisch).
- [ ] `SE_METRICS_ENABLED: false` → keine Dateien, keine Warnungen, kein Pipeline-Delta (byte-identisch).
- [ ] Schema-Validation jedes Events gegen `schemas/se-metrics.schema.json` (invalides Event →
      fail-closed Abbruch mit Pfad-Meldung).
- [ ] Gates greifen exakt wie §8 (warn/reject/block) — positiv- und negativ-getestet; der Collector
      selbst hat keinen Block-Codepfad.
- [ ] Keine externen Abhängigkeiten (stdlib only); keine Änderung an `se-*`-Agent-Schemas.
- [ ] Neue SE-Variablen in `placeholders.py` registriert; `sync.py --validate` grün.

## 10. Grenzen

- Metriken sind **Beobachtung, kein Beweis**: RVI misst Statement-Volatilität, nicht fachliche
  Richtigkeit; AC-Coverage misst Referenzen, nicht Testqualität.
- RVI-Proxy (ohne #329) ist eine Annäherung mit systematischer Unschärfe (innerhalb-Critic-Schleife,
  keine projektübergreifende Historie) — im Report immer als `proxy: true` markiert.
- `estimated_eur` erbt die Preisdrift der Token-Preise; Forecast linear-nähernd.
- Convention boundary: Schwellwerte/Gates schützen gegen Prozessdrift, nicht gegen gezielte
  Manipulation der JSONL (Terminologie per AGENTS.md).
