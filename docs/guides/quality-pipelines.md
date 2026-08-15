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
  feature-lifecycle:
    description: "..."
    stages: [...]
```

### Projekt-Overrides: `.meta-config/project.yaml`
```yaml
quality-pipelines:
  overrides:
    feature-lifecycle:
      stages:
        implement:
          plan-driven:
            fallback_agent: senior-developer
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

## Approval Gates (Abnahme)

Jede Stage kann optional eine explizite Nutzer-Abnahme erzwingen, bevor sie startet:

```yaml
quality_pipelines:
  feature-lifecycle:
    approval_default: false   # Pipeline-weiter Default (optional)
    stages:
    - id: implement
      mode: plan-driven
      requires_approval: true # Override pro Stage (optional)
      ...
```

- **Stage-Ebene** (`requires_approval`) überschreibt **Pipeline-Ebene** (`approval_default`).
- Fehlen beide Felder → `false` (Default, abwärtskompatibel — keine bestehende Pipeline setzt sie).
- Gilt für jeden Stage-Modus, nicht nur `plan-driven` — z.B. auch vor `commit`.
- Rendering: eine `⏸`-Zeile vor dem normalen Stage-Block, provider-unabhängig (rein instruktiv, kein Runtime-Enforcement — wie bei `Execution mode`).

Beispiel für den Planner-Anwendungsfall (Plan muss vor Ausführung abgenommen werden), als Projekt-Override in `.meta-config/project.yaml`:
```yaml
quality-pipelines:
  overrides:
    feature-lifecycle:
      stages:
        implement:
          requires_approval: true
```

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
