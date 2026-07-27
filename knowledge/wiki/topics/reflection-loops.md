---
type: "Guide"
title: "Reflection-Loops — Generische Iterative Verbesserung"
description: "Ein Reflection-Loop besteht aus zwei Rollen: - Generator: Erzeugt Output (Code, Design, Tests, Anforderungen) - Critic: Bewertet den Output und gibt Korrekturhinweise"
tags: [guide]
timestamp: "2026-07-27"
resource: "../../sources/docs/guides/reflection-loops.md"
migrated_from: "docs/guides/reflection-loops.md"
---
# Reflection-Loops — Generische Iterative Verbesserung

## Konzept

Ein Reflection-Loop besteht aus zwei Rollen:
- **Generator**: Erzeugt Output (Code, Design, Tests, Anforderungen)
- **Critic**: Bewertet den Output und gibt Korrekturhinweise

Der Loop wiederholt sich bis:
- Critic den Output akzeptiert (APPROVE)
- Maximale Iterationszahl erreicht ist
- Loop als "blocked" eskaliert wird

## Konfiguration

### Zentrale Definition: `config/role-defaults.yaml`

```yaml
reflection_pairs:
  - id: dev-review-loop
    generator: developer
    critic: code-reviewer
    max_iterations: 3
    on_blocked: escalate_to_orchestrator
```

### Projekt-Overrides: `.meta-config/project.yaml`

```yaml
reflection-pairs:
  overrides:
    dev-review-loop:
      max_iterations: 5  # Projekt-spezifische Anpassung
```

## Workflow-Notation

| Notation | Bedeutung |
|----------|-----------|
| `REPEAT_UNTIL(gen, crit, n)` | Orchestrator-Operator |
| `gen [⇄ crit, max=n]` | Kurznotation in Workflows |

## Neue Pairs definieren

1. Pair in `config/role-defaults.yaml` hinzufügen
2. Generator und Critic müssen existierende Rollen sein
3. Optional: Projekt-Override in `project.yaml`
4. `sync.py` ausführen

## Platzhalter in Templates

| Platzhalter | Wird ersetzt durch |
|-------------|-------------------|
| `{{MAX_ITERATIONS}}` | max_iterations aus Pair-Konfiguration |
| `{{CRITIC_NAME}}` | Name der Critic-Rolle |
| `{{GENERATOR_NAME}}` | Name der Generator-Rolle |
| `{{PAIR_ID}}` | ID des Reflection-Pairs |
| `{{ON_BLOCKED}}` | Verhalten bei Blockade |