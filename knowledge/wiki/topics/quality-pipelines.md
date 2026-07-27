---
type: "Guide"
title: "Quality Pipelines"
description: "Quality Pipelines sind vordefinierte Multi-Agent-Ketten die wiederkehrende Workflows standardisieren. Statt jeden Workflow im Orchestrator hart zu codieren, werden sie zentral..."
tags: [guide]
timestamp: "2026-07-27"
resource: "../../sources/docs/guides/quality-pipelines.md"
migrated_from: "docs/guides/quality-pipelines.md"
---
# Quality Pipelines

## Konzept

Quality Pipelines sind vordefinierte Multi-Agent-Ketten die wiederkehrende Workflows
standardisieren. Statt jeden Workflow im Orchestrator hart zu codieren, werden sie
zentral in `config/role-defaults.yaml` definiert und provider-optimiert injiziert.

## Stage-Modi

| Modus | Beschreibung | Beispiel |
|-------|-------------|----------|
| `sequential` | Ein Agent nach dem anderen | branch → implement → review |
| `parallel_group` | Mehrere Agenten parallel | verifier + test-manager |
| `fanout` | Gleicher Agent, verschiedene Tasks | 3× developer für Bug A, B, C |
| `loop` | Generator/Critic-Schleife | developer ↔ code-reviewer (max 3x) |
| `conditional` | Bedingte Ausführung | termination: leaf or recurse |

## Zentrale Konfiguration

### Base-Pipelines: `config/role-defaults.yaml`
```yaml
quality_pipelines:
  standard-feature:
    description: "..."
    stages: [...]
```

### Projekt-Overrides: `.meta-config/project.yaml`
```yaml
quality-pipelines:
  overrides:
    standard-feature:
      stages:
        review:
          loop:
            max_iterations: 5
  custom-pipelines:
    my-pipeline:
      stages: [...]
```

## Provider-optimierte Injektion

Jeder Provider bekommt angepasste Notation:

| Provider | Notation | Beispiel |
|----------|----------|----------|
| Opencode | `task()` Tool-Calls | `task(subagent_type="developer", prompt="...")` |
| Claude | `background` Tool-Calls | `background(agent="developer", prompt="...")` |
| Gemini | `define_subagent` + `invoke_subagent` | `invoke_subagent("developer", "...")` |
| Continue | Sequentieller Text | `1. @developer ...` |

## SE-Kaskade als Pipeline

Die Systems-Engineering-Kaskade ist als `se-cascade` Pipeline definiert:
- L1 Requirements (Loop mit Critic)
- L2 Architecture (Loop mit Critic)
- Interface Synchronization
- Termination Decision
- Validation (Parallel Group)

## Eigene Pipelines definieren

1. Pipeline in `config/role-defaults.yaml` hinzufügen
2. Oder Projekt-spezifisch in `.meta-config/project.yaml` unter `custom-pipelines`
3. `sync.py` ausführen → Platzhalter werden generiert
4. Im Orchestrator-Template mit `{{PIPELINE_<NAME>_BLOCK}}` referenzieren