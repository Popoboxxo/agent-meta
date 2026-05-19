# Evaluator-Optimizer-Loop — Generisches Konzept

> Issue: [#163](https://github.com/Popoboxxo/agent-meta/issues/163) | Stand: 2026-05-19

## Zusammenfassung

Der Evaluator-Optimizer-Loop ist ein iterativer Qualitäts-Workflow zwischen **beliebigen Agenten-Paaren**: ein Generator-Agent erzeugt Output, ein Evaluator-Agent bewertet ihn gegen konfigurierbare Kriterien, der Generator iteriert auf Basis des spezifischen Feedbacks — solange bis der Evaluator "approved" signalisiert oder die maximale Iterationszahl erreicht ist.

**Nicht nur Developer↔Reviewer.** Jedes Agenten-Paar mit Generator-Evaluator-Beziehung kann konfiguriert werden.

## Warum generisch?

| Starr (Developer↔Reviewer) | Generisch (Pairs) |
|---|---|
| Nur Code-Qualität | Jede Output-Art prüfbar |
| Ein Kriterien-Set | Kriterien pro Paar definierbar |
| Immer 3 Iterationen | Iterationen pro Paar |
| Immer gleicher Evaluator | Evaluator pro Paar wählbar |
| Nicht erweiterbar | Neue Paare per Config |

## Konfiguration

### `pairs` in `.meta-config/project.yaml`

```yaml
evaluator-optimizer:
  enabled: false                     # Master-Schalter
  auto_approve: false                # Global: nach max_iterations automatisch akzeptieren?

  pairs:
    # ── Code-Qualität ──
    - generator: developer
      evaluator: reviewer
      max_iterations: 3
      modes: [feature, bugfix, refactor]
      criteria:
        - correctness
        - efficiency
        - safety
        - style
        - conventions

    # ── Anforderungs-Qualität ──
    - generator: requirements
      evaluator: reviewer
      max_iterations: 2
      modes: [feature]
      criteria:
        - completeness
        - clarity
        - traceability
        - consistency

    # ── Dokumentations-Qualität ──
    - generator: documenter
      evaluator: reviewer
      max_iterations: 2
      modes: [feature, refactor]
      criteria:
        - completeness
        - clarity
        - structure
        - language

    # ── Test-Qualität ──
    - generator: tester
      evaluator: validator
      max_iterations: 2
      modes: [feature, bugfix]
      criteria:
        - coverage
        - correctness
        - edge_cases
```

### Schema in `config/project-config.schema.json`

```json
"evaluator_optimizer": {
  "type": "object",
  "description": "Generator-Evaluator quality loops. Any agent pair can be configured.",
  "properties": {
    "enabled": { "type": "boolean", "default": false },
    "auto_approve": { "type": "boolean", "default": false },
    "pairs": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["generator", "evaluator"],
        "properties": {
          "generator": { "type": "string", "description": "Agent that produces output" },
          "evaluator": { "type": "string", "description": "Agent that evaluates output" },
          "max_iterations": { "type": "integer", "minimum": 1, "maximum": 5, "default": 3 },
          "modes": {
            "type": "array",
            "items": { "type": "string", "enum": ["feature", "bugfix", "refactor"] }
          },
          "criteria": {
            "type": "array",
            "items": { "type": "string" }
          }
        }
      }
    }
  }
}
```

### Variablen-Injektion in `scripts/lib/config.py`

```python
eo_config = config.get("evaluator_optimizer", {})
variables["EVALUATOR_OPTIMIZER_ENABLED"] = eo_config.get("enabled", False)
variables["EVALUATOR_OPTIMIZER_AUTO_APPROVE"] = eo_config.get("auto_approve", False)

# Pairs als strukturierte Variable für Template-Iteration
pairs = eo_config.get("pairs", [])
# Beispiel-Generierung:
# EVALUATOR_OPTIMIZER_PAIRS = "developer|reviewer|3|feature,refactor|correctness,efficiency,safety..."
# Oder als YAML-ähnlicher Block den das Template parsen kann

# Für jedes Paar: EVALUATOR_OPTIMIZER_PAIR_0_GENERATOR = "developer" usw.
for i, pair in enumerate(pairs):
    for key in ["generator", "evaluator", "max_iterations", "modes", "criteria"]:
        val = pair.get(key, "")
        if isinstance(val, list):
            val = ",".join(val)
        variables[f"EVALUATOR_OPTIMIZER_PAIR_{i}_{key.upper()}"] = val
variables["EVALUATOR_OPTIMIZER_PAIR_COUNT"] = len(pairs)
```

## Workflow (generisch)

```
┌──────────────────────────────────────────────────────────┐
│                    Orchestrator                          │
│  prüft: EVALUATOR_OPTIMIZER_ENABLED?                     │
│              ↓ ja                                        │
│  prüft: Aktueller Workflow-Modus (feature/bugfix/...)    │
│  findet: Alle Paare deren modes passen                   │
│              ↓                                           │
│  Für jedes passende Paar:                                │
│    delegiert an <generator> (Runde 1)                    │
│              ↓                                           │
│    <generator> erzeugt Output                            │
│              ↓                                           │
│    delegiert an <evaluator> mit Kriterien                │
│              ↓                                           │
│    <evaluator> bewertet → {status, critique, must_fix}   │
│              ↓ revise                ↓ approved          │
│    <evaluator> gibt spezifische    → nächster Schritt    │
│    Critique an <generator> zurück                        │
│              ↓                                           │
│    <generator> iteriert (Runde 2..N)                     │
│              ↓                                           │
│    Loop bis approved ODER iterations == max_iterations   │
│    Bei max_iterations erreicht:                          │
│      auto_approve=true → akzeptieren                     │
│      auto_approve=false → User fragen                    │
└──────────────────────────────────────────────────────────┘
```

## Evaluator: Generische Critique-Struktur

Jeder Evaluator liefert ein einheitliches Critique-Format — die `criteria`-Keys aus der Config werden zu den Bewertungsfeldern:

```json
{
  "pair": "developer→reviewer",
  "status": "approved" | "revise",
  "iteration": 2,
  "max_iterations": 3,
  "criteria_evaluated": ["correctness", "efficiency", "safety", "style", "conventions"],
  "critique": {
    "correctness":  { "status": "ok" | "issues", "details": "..." },
    "efficiency":   { "status": "ok" | "issues", "details": "..." },
    "safety":       { "status": "ok" | "issues", "details": "..." },
    "style":        { "status": "ok" | "issues", "details": "..." },
    "conventions":  { "status": "ok" | "issues", "details": "..." }
  },
  "must_fix": ["concrete issue 1", "concrete issue 2"],
  "suggestions": ["nice-to-have 1"]
}
```

Die `criteria`-Keys sind **frei definierbar** pro Pair — der Evaluator richtet seine Bewertung danach aus.

## Generator: Generischer Iterations-Modus

Jeder Generator-Agent bekommt im Loop-Modus:

1. Die ursprüngliche Task-Beschreibung
2. Die Evaluator-Critique (obiges JSON)
3. Die Anweisung: "Iteriere auf Basis der Critique. Fixe alle `must_fix`-Punkte. Berücksichtige `suggestions` nach Ermessen. Dies ist Iteration X von Y."

Der Generator muss **nur die Critique-Punkte adressieren**, nicht die gesamte Aufgabe neu implementieren.

## Orchestrator: Workflow-Fork

```
A/B/E  Feature / Bugfix / Refactoring:
  0.git  1.?req  2.?test  3.<generator>
    ──→ {{#if EVALUATOR_OPTIMIZER_ENABLED}}
          Für jedes Paar dessen modes passen:
            evaluator (critique) → generator (iterate) → evaluator → ... → approved|fallback
        {{/if}}
  4.?review  5.?test  6∥7.val+?doc  8.git
```

Der Orchestrator iteriert über alle konfigurierten Pairs, filtert nach `modes`, und führt für jedes passende Pair den Loop durch.

## Betroffene Dateien

| Datei | Änderung | Typ |
|-------|----------|-----|
| `.meta-config/project.yaml` | Neue Sektion `evaluator-optimizer:` mit `pairs` | Config |
| `config/project-config.schema.json` | Schema für pairs-Array | Config |
| `scripts/lib/config.py` | `build_variables()` → Pair-Variablen generieren | Code |
| `agents/1-generic/orchestrator.md` | Workflow-Fork: Pair-Iteration + Loop | Template |
| `agents/1-generic/reviewer.md` | Neue Sektion: generische Critique (criteria-gesteuert) | Template |
| `agents/1-generic/developer.md` | Neue Sektion: Iterations-Modus (Critique anwenden) | Template |
| `agents/1-generic/validator.md` | Neue Sektion: Critique-Modus für Evaluator-Rolle | Template |
| `agents/1-generic/documenter.md` | Iterations-Modus (wenn als generator konfiguriert) | Template |
| `agents/1-generic/requirements.md` | Iterations-Modus (wenn als generator konfiguriert) | Template |
| `agents/1-generic/tester.md` | Iterations-Modus (wenn als generator konfiguriert) | Template |
| `howto/project.yaml.example` | Beispiel-Konfiguration dokumentieren | Doku |

## Sinnvolle vorkonfigurierte Pairs

| Generator | Evaluator | Sinn | Kriterien |
|-----------|-----------|------|-----------|
| `developer` | `reviewer` | Code-Qualität | correctness, efficiency, safety, style, conventions |
| `requirements` | `reviewer` | Anforderungs-Qualität | completeness, clarity, traceability, consistency |
| `documenter` | `reviewer` | Dokumentations-Qualität | completeness, clarity, structure, language |
| `tester` | `validator` | Test-Qualität | coverage, correctness, edge_cases |
| `developer` | `security-auditor` | Security im Code | owasp_top10, secret_leaks, dependency_vulns |
| `release` | `validator` | Release-Qualität | changelog_complete, version_consistent, artifacts_valid |

## Token-Kosten & Sicherheitsgrenzen

| Mechanismus | Wert | Begründung |
|-------------|------|------------|
| max_iterations pro Pair | 2–3 (default) | Pro Pair konfigurierbar |
| auto_approve | false (default) | User hat letzte Entscheidung |
| modes-Whitelist pro Pair | feature/bugfix/refactor | Nicht bei Trivial-Änderungen |
| scope-guard | Nur bei Scope ≥ "Klein" | Triviale Änderungen triggern keinen Loop |
| Max-Pairs pro Workflow | ≤3 parallel | Token-Kosten kontrollieren |

## Risiken

| Risiko | Mitigation |
|--------|------------|
| Zu viele Pairs → Token-Kosten explodieren | Max 3 Pairs pro Workflow, modes-Whitelist |
| Evaluator zu pingelig → nie approved | auto_approve, User-Fallback |
| Generator ignoriert Critique | max_iterations → User-Entscheidung |
| Neue Agenten haben keinen Iterations-Modus | Nur Agenten mit Iterations-Sektion sind als Generator nutzbar |
| Zirkuläre Pairs (A→B, B→A) | Schema-Validierung verhindert A==B im selben Pair |

## Implementierungs-Reihenfolge

1. **Config & Schema** — project.yaml + schema.json (Pairs-konfigurierbar)
2. **config.py** — Pair-Variablen-Injektion
3. **Reviewer + Validator** — Generische Critique-Sektion (criteria-gesteuert)
4. **Developer** — Iterations-Sektion (Prototyp)
5. **Weitere Generatoren** — documenter, requirements, tester
6. **Orchestrator** — Pair-Iteration + Loop-Fork
7. **Dry-Run & Verifikation** — sync.py mit/ohne Flag, alle Pairs
8. **howto/project.yaml.example** — Dokumentation für Endnutzer
