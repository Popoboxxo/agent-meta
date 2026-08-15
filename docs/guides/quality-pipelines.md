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

## Stage-Detail-Sichtbarkeit: Full-Inline vs. Lean-Reference

Der gerenderte Stage-Detail-Block (`_generate_pipeline_block`) erreicht Agenten auf zwei Wegen, je nach Orchestrator-Modus:

| Modus | Mechanismus | Wo | Token-Kosten |
|---|---|---|---|
| `strict`/`advisory` (dedizierter `orchestrator`-Subagent) | `{{PIPELINE_DETAIL_BLOCKS}}` — alle aktiven Pipelines voll inline | `agents/1-generic/orchestrator.md` | einmalig beim Subagent-Spawn, nicht immer-on |
| `main-chat` (kein Orchestrator-Subagent) | `{{PIPELINE_DETAILS_DIR}}` — ein Zeiger pro Sync, volle Details in separaten Dateien | `rules/1-generic/use-orchestrator.md` (immer geladen) | eine Zeile always-on, volle Details nur per `Read` bei Bedarf |

Für `main-chat` schreibt `sync_pipeline_detail_files()` (`scripts/lib/pipelines.py`) bei jedem Sync eine `<pipeline-name>.md`-Datei pro aktiver Pipeline nach `<PIPELINE_DETAILS_DIR>/` (Default: Geschwisterverzeichnis von `agents_dir`, z.B. `.claude/pipeline-details/`) — inklusive Stale-Cleanup über einen `.agent-meta-managed`-Index (gleiches Muster wie `mcp.py`/`external_tools.py`, siehe `scripts/lib/rule_index.py`). `main_chat` liest die passende Datei erst, wenn eine Pipeline tatsächlich gematcht wurde — die immer geladene `use-orchestrator.md` wächst dadurch nur um einen fixen Hinweis-Satz, unabhängig von der Anzahl der Pipelines.

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
4. Wird automatisch über `{{PIPELINE_DETAIL_BLOCKS}}` in `agents/1-generic/orchestrator.md` gerendert
   (aggregiert alle aktiven Pipelines) — für eine einzelne Pipeline gezielt: `{{PIPELINE_<NAME>_BLOCK}}`
