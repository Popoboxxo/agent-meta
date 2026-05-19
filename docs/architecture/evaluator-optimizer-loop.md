# Evaluator-Optimizer-Loop — Konzept

> Issue: [#163](https://github.com/Popoboxxo/agent-meta/issues/163) | Stand: 2026-05-19

## Zusammenfassung

Der Evaluator-Optimizer-Loop ist ein iterativer Qualitäts-Workflow: Developer generiert Code, Reviewer bewertet ihn gegen definierte Kriterien, Developer iteriert auf Basis des spezifischen Feedbacks — solange bis der Reviewer "approved" signalisiert oder die maximale Iterationszahl erreicht ist.

## Warum?

Aktuell prüft der Reviewer nur einmalig vor dem Merge (binäres Pass/Fail). Bei "Fail" muss der Developer raten was falsch war. Der Loop ersetzt das durch einen **informierten Verbesserungskreislauf** mit spezifischem Feedback.

## Aktivierbarkeit

### Flag in `.meta-config/project.yaml`

```yaml
evaluator-optimizer:
  enabled: false            # true = Loop aktiv
  max_iterations: 3         # 1–5, default 3
  modes:                    # In welchen Workflows greift der Loop?
    - feature
    - bugfix
    - refactor
  auto_approve: false       # true = nach N Iterationen automatisch akzeptieren
```

### Flag-Dokumentation in `config/project-config.schema.json`

```json
"evaluator_optimizer": {
  "type": "object",
  "description": "Evaluator-Optimizer quality loop: developer generates, reviewer critiques, developer iterates.",
  "properties": {
    "enabled": { "type": "boolean", "default": false },
    "max_iterations": { "type": "integer", "minimum": 1, "maximum": 5, "default": 3 },
    "modes": {
      "type": "array",
      "items": { "type": "string", "enum": ["feature", "bugfix", "refactor"] }
    },
    "auto_approve": { "type": "boolean", "default": false }
  }
}
```

### Variablen-Injektion in `scripts/lib/config.py`

```python
evaluator_optimizer_enabled = config.get("evaluator_optimizer", {}).get("enabled", False)
variables["EVALUATOR_OPTIMIZER_ENABLED"] = evaluator_optimizer_enabled
variables["EVALUATOR_OPTIMIZER_MAX_ITERATIONS"] = config.get("evaluator_optimizer", {}).get("max_iterations", 3)
variables["EVALUATOR_OPTIMIZER_MODES"] = config.get("evaluator_optimizer", {}).get("modes", [])
```

## Workflow

```
┌──────────────────────────────────────────────────────────┐
│                    Orchestrator                          │
│  prüft: EVALUATOR_OPTIMIZER_ENABLED?                     │
│  prüft: Workflow-Modus in modes-Liste?                   │
│              ↓ ja                                        │
│  delegiert an developer (Runde 1)                        │
│              ↓                                           │
│  developer erzeugt Code                                  │
│              ↓                                           │
│  reviewer bewertet → {status: "approved"|"revise", ...}  │
│              ↓ revise                ↓ approved          │
│  reviewer gibt spezifische          → Merge/Commit       │
│  Critique an developer zurück                            │
│              ↓                                           │
│  developer iteriert (Runde 2..N)                         │
│              ↓                                           │
│  reviewer bewertet erneut                                │
│              ↓                                           │
│  Loop bis approved ODER iterations == max_iterations     │
│  Bei max_iterations erreicht: Fallback-Entscheidung      │
│    - auto_approve=true → akzeptieren trotz revise        │
│    - auto_approve=false → User fragen                    │
└──────────────────────────────────────────────────────────┘
```

## Betroffene Dateien

| Datei | Änderung | Typ |
|-------|----------|-----|
| `.meta-config/project.yaml` | Neue Sektion `evaluator-optimizer:` | Config |
| `config/project-config.schema.json` | Schema-Validierung | Config |
| `scripts/lib/config.py` | `build_variables()` → neue Platzhalter | Code |
| `agents/1-generic/orchestrator.md` | Workflow-Fork: `{{#if EVALUATOR_OPTIMIZER_ENABLED}}` → Loop-Modus | Template |
| `agents/1-generic/reviewer.md` | Neue Sektion: strukturierte Critique (JSON) für Loop-Modus | Template |
| `agents/1-generic/developer.md` | Neue Sektion: Iterations-Modus (Critique lesen & anwenden) | Template |

## Reviewer: Strukturierte Critique

Der Reviewer liefert im Loop-Modus ein strukturiertes Feedback statt einem binären Pass/Fail:

```json
{
  "status": "approved" | "revise",
  "iteration": 2,
  "max_iterations": 3,
  "critique": {
    "correctness": { "status": "ok" | "issues", "details": "..." },
    "efficiency": { "status": "ok" | "issues", "details": "..." },
    "safety":     { "status": "ok" | "issues", "details": "..." },
    "style":      { "status": "ok" | "issues", "details": "..." },
    "conventions":{ "status": "ok" | "issues", "details": "..." }
  },
  "must_fix": ["concrete issue 1", "concrete issue 2"],
  "suggestions": ["nice-to-have 1", "nice-to-have 2"]
}
```

## Developer: Iterations-Modus

Im Loop-Modus bekommt der Developer zusätzlich zur ursprünglichen Task-Beschreibung:

1. Die Reviewer-Critique (obiges JSON)
2. Die Anweisung: "Iteriere auf Basis der Critique. Fixe alle `must_fix`-Punkte. Berücksichtige `suggestions` nach Ermessen. Dies ist Iteration X von Y."

Der Developer muss **nur die Critique-Punkte adressieren**, nicht die gesamte Aufgabe neu implementieren.

## Orchestrator: Workflow-Erweiterung

```
A/B/E  Neues Feature / Bugfix / Refactoring:
  0.git  1.?req  2.?test  3.dev  ──→ {{#if EVALUATOR_OPTIMIZER_ENABLED}}
                                     4.reviewer (critique)
                                     5.dev (iterate based on critique)
                                     6.reviewer (re-evaluate)
                                     ... (loop)
                                     ──→ {{/if}}
  7.?review  8.?test  9∥10.val+?doc  11.git
```

## Token-Kosten & Sicherheitsgrenzen

| Mechanismus | Wert | Begründung |
|-------------|------|------------|
| max_iterations | 3 (default) | Verhindert Endlosschleifen, begrenzt Kosten |
| auto_approve | false (default) | User hat letzte Entscheidung bei ungelösten Issues |
| modes-Whitelist | feature/bugfix/refactor | Nicht bei Trivial-Änderungen (1 Datei, 1 Zeile) |
| scope-guard | Nur bei Scope ≥ "Klein" | Triviale Änderungen triggern keinen Loop |

## Risiken

| Risiko | Mitigation |
|--------|------------|
| Token-Kosten explodieren | max_iterations=3, modes-Whitelist |
| Reviewer zu pingelig → nie approved | auto_approve-Option, User-Fallback |
| Developer ignoriert Critique | max_iterations → User-Entscheidung |
| Loop verlangsamt Entwicklung | Opt-in (default: false) |

## Implementierungs-Reihenfolge

1. **Config & Variablen** — project.yaml + schema.json + config.py (Infrastruktur)
2. **Reviewer-Template** — Critique-Sektion (kann standalone getestet werden)
3. **Developer-Template** — Iterations-Sektion
4. **Orchestrator-Template** — Workflow-Fork mit {{#if}}
5. **Dry-Run & Verifikation** — sync.py --dry-run mit/ohne Flag
