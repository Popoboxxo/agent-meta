# Structured Output Contracts — Analyse & Design

> **Status:** Schema-Clustering implementiert (Issue #165)  
> **Branch:** `feat/structured-output-contracts`  
> **Datum:** 2026-05-20  
> **Autor:** Orchestrator (Analyse & Design)

---

## 1. Motivation

### 1.1 Problem

Agenten in agent-meta kommunizieren aktuell ausschließlich in **natürlicher Sprache**. Der Orchestrator delegiert Aufgaben an Worker (z.B. `developer`, `reviewer`, `git`) und erhält Freitext-Antworten zurück. Das führt zu drei konkreten Problemen:

1. **Token-Ineffizienz** — Jeder Agent verpackt strukturierte Daten (geänderte Dateien, Commit-SHA, Testergebnisse) in Prosa. Der Orchestrator oder nachfolgende Agenten müssen diese Informationen aus Text herauspärsen, was sowohl Token verschwendet als auch fehleranfällig ist.

2. **Fehleranfälligkeit** — Der Orchestrator muss aus Fließtext extrahieren: "Ich habe die Datei `foo.py` geändert und mit SHA `abc123` committed." Das ist nicht deterministisch und bricht bei unerwarteten Formulierungen.

3. **Keine maschinelle Validierbarkeit** — Der Orchestrator kann nicht programmatisch prüfen, ob ein Agent alle erforderlichen Output-Felder geliefert hat. Dadurch entstehen undetektierte Lücken (fehlende Test-Ergebnisse, unvollständige Diffs).

### 1.2 Inspirationsquellen

- **CrewAI:** `output_pydantic` / `output_json` — Agenten-Output wird gegen ein Pydantic-Modell validiert
- **AutoGen:** JSON-Mode für strukturierte Agenten-Kommunikation
- **LangChain:** Output-Parser mit strukturierten Schemas
- **Evaluator-Optimizer (dieses Repo):** Bereits existierendes Critique-JSON-Format (Spezialfall)
- **OpenAI Structured Outputs:** JSON-Schema-Constraint für guaranteed JSON

### 1.3 Ziel

Ein **leichtgewichtiges, optionales System** das:

- Jedem Agenten ein JSON-Schema für seinen Output zuordnet
- Im generierten Template-Text den Agenten zur strukturierten Ausgabe anweist
- Dem Orchestrator (und anderen Agenten) erlaubt, Outputs maschinell zu validieren und zu mergen
- Rückwärtskompatibel bleibt — Agenten OHNE Schema arbeiten wie bisher in Freitext

---

## 2. Ist-Zustand: Wie kommunizieren Agenten aktuell?

### 2.1 Kommunikationsmuster

```
Orchestrator → Developer:    Freitext-Task (z.B. "Implementiere Feature X in Datei Y")
Developer   → Orchestrator:  Freitext-Antwort (z.B. "Ich habe foo.py geändert, Tests laufen grün.")
Orchestrator → Git:           "Committe die Änderungen: feat: add feature X"
Git         → Orchestrator:  "Committed as abc123, pushed to origin/feat/X"
Orchestrator → Reviewer:      "Review den Branch feat/X"
Reviewer    → Orchestrator:  Review-Bericht als Markdown-Text
```

**Kein Agent liefert derzeit JSON.** Nur der Evaluator-Optimizer-Loop hat ein JSON-Critique-Format — das ist aber ein spezialisierter Sub-Workflow, kein allgemeiner Mechanismus.

### 2.2 Vorhandene Struktur: `input`/`output` in role-defaults.yaml

```yaml
developer:
  input: "Task-Beschreibung, betroffene Dateipfade, REQ-ID (falls traceability aktiv)"
  output: "Implementierter Code, ggf. Commit SHA oder Diff"
```

Diese Felder sind **reine Dokumentation** — sie haben keine automatisierte Validierung, keinen Schema-Bezug, und werden nicht in generierte Templates eingebaut.

### 2.3 Variablen-System (sync.py)

`config.py::build_variables()` erzeugt alle `{{VARIABLE}}`-Platzhalter. Aktuelle relevante Variablen: `DOD_*`, `CI_POLL_*`, `EVALUATOR_OPTIMIZER_*`, `AGENT_TABLE`, `AGENT_HINTS`.

`agents.py::sync_agents_for_provider()` injiziert per `inject_agent_fields()` die Frontmatter-Felder: `model`, `memory`, `permissionMode`, `temperature`, `maxTokens`.

### 2.4 Template-Composition

`agents_template.py` unterstützt `extends:` + `patches:` für Composition. Die `build_variables()`-Pipeline könnte um Schema-Variablen erweitert werden.

---

## 3. Design

### 3.1 JSON-Schema Definitionen — Welche Agenten brauchen welche Schemas?

Nicht jeder Agent braucht ein Output-Schema. Die Priorität richtet sich nach dem Orchestrierungs-Wert.

#### Kern-Schemas (Phase 1)

| Agent | Output-Felder | Zweck |
|-------|---------------|-------|
| `developer` | `files_changed`, `changes_summary`, `commit_sha`, `tests_passed` | Orchestrator kann Merge-Status deterministisch ermitteln |
| `git` | `commit_sha`, `branch`, `push_url`, `status` | Orchestrator weiß sofort ob Push erfolgreich |
| `tester` | `test_count`, `passed`, `failed`, `skipped`, `coverage` | Qualitäts-Gates ohne Parsing |
| `validator` | `status`, `checks_passed`, `failed_checks`, `warnings` | DoD-Check automatisiert |
| `reviewer` | `status`, `must_fix_count`, `findings`, `approval` | Review-Zusammenfassung |
| `requirements` | `req_id`, `title`, `status` | Scope-Tracking |
| `release` | `version`, `tag`, `changelog_sha`, `release_url` | Release-Traceability |

#### Optionale Schemas (Phase 2)

| Agent | Output-Felder |
|-------|---------------|
| `performance` | `bottlenecks`, `metrics`, `recommendations` |
| `security-auditor` | `issues`, `severity`, `owasp_category` |
| `ideation` | `options`, `recommended_approach`, `risks` |
| `log-analyzer` | `severity_counts`, `top_errors`, `recommendations` |

#### Spezialfall: Orchestrator

Der Orchestrator selbst hat kein Output-Schema — er aggregiert und delegiert. Sein "Output" ist die Gesamtheit der delegierten Tasks. Das ist inhärent Freitext.

### 3.2 Schema-Definitionsformat

JSON-Schema (Draft 2020-12) als separate `.schema.json`-Dateien in `config/output-schemas/`:

```
config/
  output-schemas/
    developer.schema.json
    git.schema.json
    tester.schema.json
    validator.schema.json
    reviewer.schema.json
    requirements.schema.json
    release.schema.json
```

Beispiel: `config/output-schemas/developer.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:developer:v1",
  "title": "Developer Output",
  "description": "Structured output contract for the developer agent.",
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["success", "partial", "failed"],
      "description": "Overall implementation status"
    },
    "files_changed": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "change_type"],
        "properties": {
          "path": { "type": "string", "description": "Relative file path" },
          "change_type": {
            "type": "string",
            "enum": ["created", "modified", "deleted"]
          },
          "summary": {
            "type": "string",
            "description": "Brief summary of the change (max 200 chars)"
          }
        }
      },
      "description": "List of all files changed by this implementation"
    },
    "commit_sha": {
      "type": "string",
      "pattern": "^[0-9a-f]{7,40}$",
      "description": "Full or abbreviated commit SHA (if committed)"
    },
    "tests": {
      "type": "object",
      "properties": {
        "all_passed": { "type": "boolean" },
        "count": { "type": "integer", "minimum": 0 },
        "details": { "type": "string", "description": "Optional test output link or summary" }
      },
      "required": ["all_passed"],
      "description": "Test outcome summary"
    },
    "warnings": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Non-blocking warnings"
    }
  },
  "required": ["status", "files_changed"],
  "description": "Developer implementation report"
}
```

Beispiel: `config/output-schemas/git.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:git:v1",
  "title": "Git Output",
  "description": "Structured output contract for the git agent.",
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["commit", "push", "merge", "branch", "tag", "pr"]
    },
    "status": {
      "type": "string",
      "enum": ["success", "failed", "skipped"]
    },
    "commit_sha": {
      "type": "string",
      "pattern": "^[0-9a-f]{7,40}$"
    },
    "branch": { "type": "string" },
    "target_url": {
      "type": "string",
      "format": "uri",
      "description": "PR URL, commit URL, or tag URL"
    },
    "message": {
      "type": "string",
      "description": "Human-readable result message for the orchestrator"
    }
  },
  "required": ["operation", "status"],
  "description": "Git operation result"
}
```

### 3.3 Integration in `role-defaults.yaml`

Ein neues optionales Feld `output_schema` verweist auf eine Schema-Datei:

```yaml
developer:
  model: max
  memory: ""
  temperature: 0.2
  max_tokens: 8192
  workflow_tier: required
  input: "Task-Beschreibung, betroffene Dateipfade, REQ-ID (falls traceability aktiv)"
  output: "Implementierter Code, ggf. Commit SHA oder Diff"
  output_schema: "config/output-schemas/developer.schema.json"    # NEU
  description: "Feature-Implementierung und Bugfixes"

git:
  model: fast
  memory: ""
  temperature: 0.1
  max_tokens: 2048
  workflow_tier: required
  input: "Auszuführende Git-Operation..."
  output: "Commit SHA, Branch-Name, PR-URL"
  output_schema: "config/output-schemas/git.schema.json"          # NEU
  description: "Commits, Branches, Tags, Push/Pull"
```

**Design-Entscheidung:** `output_schema` referenziert einen relativen Pfad (vom agent-meta-Root). sync.py resolvt diesen Pfad beim Generieren und injiziert die Schema-Information in das generierte Agent-Template. So bleibt die Schema-Definition zentral und versioniert.

### 3.4 Template-Text: Anweisung zur strukturierten Ausgabe

Jeder Agent, der ein `output_schema` hat, bekommt im generierten Template eine **"Structured Output"**-Sektion angehängt:

```markdown
## Structured Output Contract

Dein Output MUSS am Ende der Antwort als JSON-Block im folgenden Format stehen.
Der Orchestrator validiert diesen Block maschinell. Freitext davor ist erlaubt,
aber der JSON-Block ist die maschinell auswertbare Antwort.

```json
<output-schema-embedded-here>
```

### Regeln
1. **JSON-Block immer am ENDE der Antwort** — nach dem letzten ```` ``` ````
2. **Alle required-Felder befüllen** — Validierung schlägt sonst fehl
3. **Keine zusätzlichen Felder** außerhalb des Schemas (striktes Schema)
4. **Einvalide JSON** → Orchestrator behandelt Output als Freitext-Fallback
5. **Bei Abbruch/Fehler** → `status: "failed"` setzen und Grund in `message`-Feld
```

Diese Sektion wird per Handlebars-ähnlichem Conditional eingefügt:

```
{{#if OUTPUT_SCHEMA_EMBEDDED}}
## Structured Output Contract
...
{{/if}}
```

#### Wie das Schema in den Template-Text gelangt

Zwei Ansätze wurden evaluert:

**Ansatz A: Schema wird als JSON-String ins Frontmatter injiziert**  
`output_schema: { "type": "object", "properties": {...} }`  
→ Problem: Frontmatter wird unlesbar, YAML-JSON-Mix, Duplikation.

**Ansatz B: Schema wird als base64-kodierter JSON-Block ans Template angehängt**  
→ Problem: Nicht lesbar, schwer debuggbar.

**Ansatz C (Gewählt): Referenz + Template-Block**

Die `build_variables()`-Funktion injected zwei neue Variablen:
1. `OUTPUT_SCHEMA_<ROLE>` — das JSON-Schema als Pretty-String
2. `OUTPUT_SCHEMA_EXAMPLE_<ROLE>` — ein Beispiel-Output (dient als Prompt-Kontext)

Im Template wird dann:

```
{{#if OUTPUT_SCHEMA_DEVELOPER}}
## Structured Output Contract

Dein Output MUSS mit einem JSON-Block enden:
```json
<HIER STEHT DAS OUTPUT_SCHEMA_DEVELOPER>
```
{{/if}}
```

**Vorteil:** Keine Änderung am Frontmatter-System nötig. Die bestehende Variablen-Substitution wird genutzt.

### 3.5 Orchestrator-Validierung

Der Orchestrator (Template in `agents/1-generic/orchestrator.md`) bekommt eine neue Sektion zur Output-Validierung:

```markdown
## Structured Output Validation

Wenn ein Agent einen Output zurückliefert:

1. **Extrahiere den letzten JSON-Block** aus der Antwort (alles zwischen
   dem letzten ```json und ``` im Text)
2. **Parse JSON** — wenn fehlerhaft → Fallback auf Freitext-Interpretation
3. **Validiere gegen das Schema** des Agenten (das Schema findest du
   in der Agenten-Konfiguration)
4. **Bei Validierungsfehlern:**
   - `status: "failed"` → Aufgabe als fehlgeschlagen markieren
   - Fehlende required-Felder → Orchestrator fragt beim Agenten nach
   - Zusätzliche unbekannte Felder → ignorieren (tolerant)
5. **Extrahiere relevante Felder** für den nächsten Schritt
   (z.B. `files_changed` an `git` weiterreichen)
```

**Validierungslogik** (nicht als Code, als Prompt-Anweisung):

```
1. Suche nach ```json ... ``` Block am Ende der Antwort
2. Fehlt der Block? → Vollständigen Text als Freitext behandeln (Legacy-Fallback)
3. JSON parsen?
   → Nein: Als Freitext behandeln
   → Ja: Gegen Schema validieren
4. Schema-Validierung:
   → Bestanden: Strukturierte Felder extrahieren
   → Fehlgeschlagen: Teilweise brauchbare Felder übernehmen + Warnung
```

### 3.6 Template-Prozessor: Schema-Injection

In `config.py::build_variables()` wird eine neue Hilfsfunktion ergänzt:

```python
# Pseudocode
def _inject_output_schema_variables(variables, config, agent_meta_root):
    """Inject OUTPUT_SCHEMA_<ROLE> and OUTPUT_SCHEMA_EXAMPLE_<ROLE> variables."""
    roles_cfg = load_roles_config(agent_meta_root)
    for role, role_cfg in roles_cfg["roles"].items():
        schema_path = role_cfg.get("output_schema", "")
        if not schema_path:
            continue
        full_path = agent_meta_root / schema_path
        if not full_path.exists():
            continue
        schema = json.loads(full_path.read_text(encoding="utf-8"))
        # Inject the pretty-printed schema
        var_name = f"OUTPUT_SCHEMA_{role.upper()}"
        variables[var_name] = json.dumps(schema, indent=2)
        # Generate a minimal example
        variables[f"{var_name}_EXAMPLE"] = _generate_example(schema)
    return variables
```

### 3.7 Änderungen in Template-Dateien

#### Orchestrator-Template

Neue Sektion (nur wenn mindestens ein Agent ein Schema hat):

```
{{#if HAS_OUTPUT_SCHEMAS}}
## Structured Output Validation
...
{{/if}}
```

#### Developer/Git/Tester/etc. -Templates

Neue Sektion (per-Agent):

```
{{#if OUTPUT_SCHEMA_DEVELOPER}}
## Structured Output Contract
...
{{/if}}
```

### 3.8 Rückwärtskompatibilität

- **Ohne Schema:** Agenten arbeiten wie bisher in Freitext. Kein JSON-Block nötig.
- **Mit Schema, kein JSON:** Orchestrierung fällt auf Freitext zurück. Kein Fehler.
- **Schema vorhanden, JSON invalide:** Orchestrierung versucht Partial-Parse + Warnung.
- **Neue Felder im Output:** Werden ignoriert (tolerantes Schema).

---

## 4. Datei-Änderungsplan (für Implementierungsphase)

### 4.1 Neue Dateien — Cluster-Schema-Abdeckung (6 Cluster)

| Datei | Inhalt |
|-------|--------|
| `config/output-schemas/base.schema.json` | **Base-Schema**: Gemeinsame Felder, die ALLE Agenten erben |
| `config/output-schemas/execution-result.schema.json` | Execution-Cluster: developer, git, tester, docker, bun-ci, code-splitter, multi-repo-refactor, openscad-developer, agent-meta-manager |
| `config/output-schemas/findings-report.schema.json` | Findings-Cluster: reviewer, validator, security-auditor, performance, log-analyzer, compliance-auditor, infrastructure-check |
| `config/output-schemas/coordination-output.schema.json` | Coordination-Cluster: feature, release, requirements |
| `config/output-schemas/knowledge-output.schema.json` | Knowledge-Cluster: documenter, ideation, agent-meta-scout |
| `config/output-schemas/issue-created.schema.json` | Issue-Cluster: feedback, meta-feedback |

### 4.2 Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `config/role-defaults.yaml` | `output_schema:` Feld in ALLEN Rollen (verweist auf Cluster-Schemas) |
| `scripts/lib/config.py` | `_inject_output_schema_variables()` + Aufruf in `build_variables()` |
| `scripts/lib/agents.py` | `sync_agents_for_provider()`: neue Variable `HAS_OUTPUT_SCHEMAS` und Provider-Variable `OUTPUT_SCHEMA_<ROLE>` |
| `agents/1-generic/orchestrator.md` | Neue Sektion "Structured Output Validation" + Validierungs-Workflow |
| `agents/1-generic/developer.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/git.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/tester.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/validator.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/reviewer.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/requirements.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/release.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/feature.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/documenter.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/ideation.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/performance.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/security-auditor.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/log-analyzer.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/meta-feedback.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/feedback.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/agent-meta-manager.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/agent-meta-scout.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/docker.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/infrastructure-check.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/code-splitter.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/compliance-auditor.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/multi-repo-refactor.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/openscad-developer.md` | Neue Sektion "Structured Output Contract" (conditional) |
| `agents/1-generic/bun-ci.md` | Neue Sektion "Structured Output Contract" (conditional) |

### 4.3 Unverändert (Keep out)

| System | Begründung |
|--------|------------|
| `.claude/agents/` | Generated output — nie manuell editieren |
| `.opencode/agents/` | Generated output — nie manuell editieren |
| `scripts/sync.py` (Hauptdatei) | Keine strukturelle Änderung — nur lib/ |
| `agent-meta.config.example.yaml` | Schema-Referenzen sind role-defaults-Sache |
| `config/ai-providers.yaml` | Keine Schema-Änderung |

---

## 5. Schema-Definitionen (vollständig)

### 5.1 developer.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:developer:v1",
  "title": "Developer Output",
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["success", "partial", "failed"],
      "description": "Overall implementation status"
    },
    "files_changed": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "change_type"],
        "properties": {
          "path": { "type": "string" },
          "change_type": {
            "type": "string",
            "enum": ["created", "modified", "deleted"]
          },
          "summary": { "type": "string" }
        }
      }
    },
    "commit_sha": {
      "type": "string",
      "pattern": "^[0-9a-f]{7,40}$"
    },
    "tests": {
      "type": "object",
      "properties": {
        "all_passed": { "type": "boolean" },
        "count": { "type": "integer", "minimum": 0 }
      },
      "required": ["all_passed"]
    },
    "warnings": {
      "type": "array",
      "items": { "type": "string" }
    },
    "message": {
      "type": "string",
      "description": "Human-readable summary for the orchestrator"
    }
  },
  "required": ["status", "files_changed"]
}
```

### 5.2 git.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:git:v1",
  "title": "Git Output",
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["commit", "push", "merge", "branch", "tag", "pr", "checkout", "status"]
    },
    "status": {
      "type": "string",
      "enum": ["success", "failed", "skipped"]
    },
    "commit_sha": {
      "type": "string",
      "pattern": "^[0-9a-f]{7,40}$"
    },
    "branch": { "type": "string" },
    "base_branch": { "type": "string" },
    "target_url": { "type": "string", "format": "uri" },
    "message": { "type": "string" }
  },
  "required": ["operation", "status"]
}
```

### 5.3 tester.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:tester:v1",
  "title": "Tester Output",
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["passed", "failed", "skipped"]
    },
    "test_count": { "type": "integer", "minimum": 0 },
    "passed": { "type": "integer", "minimum": 0 },
    "failed": { "type": "integer", "minimum": 0 },
    "skipped": { "type": "integer", "minimum": 0 },
    "coverage": {
      "type": "object",
      "properties": {
        "lines": { "type": "number", "minimum": 0, "maximum": 100 },
        "branches": { "type": "number", "minimum": 0, "maximum": 100 }
      }
    },
    "failures": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "test": { "type": "string" },
          "message": { "type": "string" }
        }
      }
    },
    "message": { "type": "string" }
  },
  "required": ["status", "test_count", "passed", "failed"]
}
```

### 5.4 validator.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:validator:v1",
  "title": "Validator Output",
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["passed", "failed", "warning"]
    },
    "checks_performed": {
      "type": "array",
      "items": { "type": "string" }
    },
    "failed_checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check": { "type": "string" },
          "details": { "type": "string" }
        }
      }
    },
    "warnings": {
      "type": "array",
      "items": { "type": "string" }
    },
    "message": { "type": "string" }
  },
  "required": ["status"]
}
```

### 5.5 reviewer.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:reviewer:v1",
  "title": "Reviewer Output",
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["approved", "changes-requested", "comment"]
    },
    "must_fix_count": { "type": "integer", "minimum": 0 },
    "suggestion_count": { "type": "integer", "minimum": 0 },
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "severity": {
            "type": "string",
            "enum": ["must-fix", "suggestion", "nitpick"]
          },
          "file": { "type": "string" },
          "line": { "type": "integer" },
          "description": { "type": "string" }
        },
        "required": ["severity", "description"]
      }
    },
    "message": {
      "type": "string",
      "description": "Human-readable review summary"
    }
  },
  "required": ["status"]
}
```

---

## 6. Beispiel-Workflow (Soll-Zustand)

```
Orchestrator → Developer:
  "Implementiere die `validate_email()` Funktion in `src/utils.py`.
   Nutze das Output-Schema."

Developer → Orchestrator:
  [Freitext-Beschreibung der Implementierung]
  ```json
  {
    "status": "success",
    "files_changed": [
      { "path": "src/utils.py", "change_type": "modified",
        "summary": "Added validate_email() with regex pattern" },
      { "path": "tests/test_utils.py", "change_type": "modified",
        "summary": "Added test cases for validate_email()" }
    ],
    "commit_sha": null,
    "tests": { "all_passed": true, "count": 5 },
    "warnings": [],
    "message": "validate_email() implementiert mit 5 Tests, alle grün."
  }
  ```

Orchestrator → Git:
  "Committe die Dateien. Developer-Report:
   files_changed: src/utils.py, tests/test_utils.py
   commit_sha: null (nicht committed)"

Git → Orchestrator:
  ```json
  {
    "operation": "commit",
    "status": "success",
    "commit_sha": "a1b2c3d4e5f6",
    "branch": "feat/validate-email",
    "target_url": "https://github.com/...",
    "message": "Committed as a1b2c3d"
  }
  ```

Orchestrator → Reviewer:
  "Review den Branch feat/validate-email.
   Git-Report: commit_sha=a1b2c3d, branch=feat/validate-email"

Reviewer → Orchestrator:
  ```json
  {
    "status": "approved",
    "must_fix_count": 0,
    "suggestion_count": 1,
    "findings": [
      { "severity": "suggestion", "file": "src/utils.py", "line": 5,
        "description": "Regex könnte als Konstante ausgelagert werden" }
    ],
    "message": "Code sieht gut aus, 1 Suggestion für Konstanten-Auslagerung."
  }
  ```

Orchestrator (Reduce):
  "Alles grün: Developer success + Tests passed + Git committed + Reviewer approved.
   Nächster Schritt: Merge."
```

---

## 7. Offene Fragen / Entscheidungen für die Implementierung

| Frage | Entscheidungsvorschlag |
|-------|----------------------|
| **Q1:** Soll das Schema im Frontmatter des generierten Agenten stehen? | **Nein.** Per Template-Variable reicht. Frontmatter würde die Agent-Datei unnötig aufblähen. |
| **Q2:** Strict oder tolerant validation? | **Tolerant** — unbekannte Felder ignorieren, fehlende required-Felder warnen, dann Freitext-Fallback. |
| **Q3:** Wer validiert? Der Orchestrator oder ein Sub-Agent? | **Der Orchestrator** — inline, ohne Sub-Agent. Das ist keine Architektur-Aufgabe. |
| **Q4:** JSON-Schema-Dateien in `config/output-schemas/` oder in `schemas/`? | **`config/output-schemas/`** — konsistent mit `config/role-defaults.yaml`, `config/evaluator-criteria.yaml`. |
| **Q5:** Soll das Schema im generierten Template embedded sein oder per Referenz? | **Embedded** als Template-Variable — kein zusätzlicher I/O zur Laufzeit. |
| **Q6:** Brauchen wir einen JSON-Schema-Validator in Python (jsonschema-Lib)? | **Nicht nötig** — Validierung passiert durch den Orchestrator-Agenten (LLM-interpretiert). Die Schema-Dateien dienen als Prompt-Kontext. |

---

## 8. Nächste Schritte (Implementierungs-Phase)

### Schritt 1: Schema-Dateien anlegen
`config/output-schemas/developer.schema.json` + `git.schema.json` + `tester.schema.json` + `validator.schema.json` + `reviewer.schema.json`

### Schritt 2: role-defaults.yaml erweitern
`output_schema:` Feld in die Rollen developer, git, tester, validator, reviewer eintragen.

### Schritt 3: config.py erweitern
`_inject_output_schema_variables()` in `build_variables()` integrieren. Neue Variable `HAS_OUTPUT_SCHEMAS`.

### Schritt 4: Template-Anpassungen
- `orchestrator.md`: Neue Sektion "Structured Output Validation"
- `developer.md`, `git.md`, `tester.md`, `validator.md`, `reviewer.md`: Neue Sektion "Structured Output Contract"

### Schritt 5: Sync + Test
`python scripts/sync.py --dry-run` → generierte Dateien prüfen → Commit.

---

## 9. Vollständige Schema-Definitionen — Historisch (ersetzt durch 6 Cluster-Schemas)

> **Hinweis:** Diese individuellen Schema-Definitionen (9.1–9.24) wurden durch die 6 Cluster-Schemas ersetzt (siehe Abschnitt 11). Sie bleiben als Referenz und Design-Historie erhalten.

### 9.0 Base Schema (gemeinsame Felder, von allen geerbt)

`config/output-schemas/base.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "base.schema.json",
  "title": "Base Agent Output",
  "description": "Common fields shared by all agent output schemas.",
  "type": "object",
  "required": ["status", "message"],
  "properties": {
    "status": {
      "type": "string",
      "enum": ["success", "partial", "failure"],
      "description": "Execution status of the agent task."
    },
    "message": {
      "type": "string",
      "description": "Human-readable summary of what was done."
    },
    "warnings": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Optional warnings encountered during execution."
    },
    "errors": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Errors if status is failure or partial."
    },
    "duration_ms": {
      "type": "integer",
      "minimum": 0,
      "description": "Task duration in milliseconds."
    }
  },
  "additionalProperties": false
}
```

### 9.1 developer.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:developer:v1",
  "title": "Developer Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "status": { "$ref": "base.schema.json#/properties/status" },
    "files_changed": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "change_type"],
        "properties": {
          "path": { "type": "string", "description": "Relative file path" },
          "change_type": { "type": "string", "enum": ["created", "modified", "deleted"] },
          "summary": { "type": "string", "description": "Brief summary of the change (max 200 chars)" }
        }
      },
      "description": "List of all files changed by this implementation"
    },
    "commit_sha": {
      "type": "string",
      "pattern": "^[0-9a-f]{7,40}$",
      "description": "Full or abbreviated commit SHA (if committed)"
    },
    "tests": {
      "type": "object",
      "properties": {
        "all_passed": { "type": "boolean" },
        "count": { "type": "integer", "minimum": 0 },
        "details": { "type": "string", "description": "Optional test output link or summary" }
      },
      "required": ["all_passed"],
      "description": "Test outcome summary"
    },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status", "files_changed"]
}
```

### 9.2 git.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:git:v1",
  "title": "Git Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["commit", "push", "merge", "branch", "tag", "pr", "checkout", "status", "fetch", "rebase", "stash"]
    },
    "status": { "$ref": "base.schema.json#/properties/status" },
    "commit_sha": { "type": "string", "pattern": "^[0-9a-f]{7,40}$" },
    "branch": { "type": "string", "description": "Current or target branch name" },
    "base_branch": { "type": "string", "description": "Base branch for merge/PR" },
    "target_url": { "type": "string", "format": "uri", "description": "PR URL, commit URL, or tag URL" },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["operation", "status"]
}
```

### 9.3 tester.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:tester:v1",
  "title": "Tester Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["passed", "failed", "skipped", "error"]
    },
    "test_count": { "type": "integer", "minimum": 0 },
    "passed": { "type": "integer", "minimum": 0 },
    "failed": { "type": "integer", "minimum": 0 },
    "skipped": { "type": "integer", "minimum": 0 },
    "coverage": {
      "type": "object",
      "properties": {
        "lines": { "type": "number", "minimum": 0, "maximum": 100 },
        "branches": { "type": "number", "minimum": 0, "maximum": 100 },
        "functions": { "type": "number", "minimum": 0, "maximum": 100 }
      },
      "description": "Test coverage percentages"
    },
    "failures": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "test": { "type": "string" },
          "file": { "type": "string" },
          "line": { "type": "integer" },
          "message": { "type": "string" }
        },
        "required": ["test", "message"]
      }
    },
    "duration_ms": { "type": "integer", "minimum": 0, "description": "Total test execution time in milliseconds" },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status", "test_count", "passed", "failed"]
}
```

### 9.4 validator.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:validator:v1",
  "title": "Validator Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["passed", "failed", "warning", "skipped"]
    },
    "checks_performed": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Names of all validation checks run"
    },
    "failed_checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "check": { "type": "string" },
          "details": { "type": "string" },
          "severity": { "type": "string", "enum": ["error", "warning", "info"] }
        },
        "required": ["check", "details"]
      }
    },
    "score": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100,
      "description": "Overall validation score (percentage)"
    },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status"]
}
```

### 9.5 reviewer.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:reviewer:v1",
  "title": "Reviewer Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["approved", "changes-requested", "comment", "skipped"]
    },
    "must_fix_count": { "type": "integer", "minimum": 0 },
    "suggestion_count": { "type": "integer", "minimum": 0 },
    "nitpick_count": { "type": "integer", "minimum": 0 },
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["severity", "description"],
        "properties": {
          "severity": { "type": "string", "enum": ["must-fix", "suggestion", "nitpick", "security"] },
          "file": { "type": "string" },
          "line": { "type": "integer" },
          "description": { "type": "string" },
          "recommendation": { "type": "string" }
        }
      }
    },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status"]
}
```

### 9.6 requirements.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:requirements:v1",
  "title": "Requirements Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "action": {
      "type": "string",
      "enum": ["created", "updated", "reviewed", "traced", "deleted", "no-change"],
      "description": "What action was performed on the requirements"
    },
    "req_id": {
      "type": "string",
      "pattern": "^REQ-\\d{3,}$",
      "description": "The primary REQ-ID affected or created"
    },
    "title": { "type": "string", "description": "Requirement title" },
    "description": { "type": "string", "description": "Requirement description summary" },
    "files_affected": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Files that reference or implement this requirement"
    },
    "traceability_map": {
      "type": "object",
      "description": "Map of REQ-IDs to their implementation status",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "status": { "type": "string", "enum": ["implemented", "partial", "not-started", "blocked"] },
          "files": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["action", "status"]
}
```

### 9.7 release.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:release:v1",
  "title": "Release Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "version": { "type": "string", "pattern": "^v?\\d+\\.\\d+\\.\\d+", "description": "Semantic version" },
    "tag": { "type": "string", "description": "Git tag name" },
    "changelog_sha": { "type": "string", "pattern": "^[0-9a-f]{7,40}$", "description": "Commit SHA of changelog update" },
    "release_url": { "type": "string", "format": "uri", "description": "URL to the GitHub/GitLab release" },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "url": { "type": "string", "format": "uri" },
          "size_bytes": { "type": "integer", "minimum": 0 }
        },
        "required": ["name"]
      },
      "description": "Build artifacts included in this release"
    },
    "commits_since_last": { "type": "integer", "minimum": 0, "description": "Number of commits since last release" },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status", "version"]
}
```

### 9.8 feature.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:feature:v1",
  "title": "Feature Agent Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "steps_completed": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "step": { "type": "string", "enum": ["branch", "requirements", "tests", "dev", "review", "validate", "doc", "pr"] },
          "status": { "type": "string", "enum": ["passed", "failed", "skipped"] },
          "agent": { "type": "string", "description": "Agent that executed this step" }
        },
        "required": ["step", "status"]
      }
    },
    "req_ids": {
      "type": "array",
      "items": { "type": "string", "pattern": "^REQ-\\d{3,}$" },
      "description": "REQ-IDs covered by this feature"
    },
    "branch": { "type": "string", "description": "Feature branch name" },
    "pr_url": { "type": "string", "format": "uri", "description": "PR URL if created" },
    "summary": { "type": "string", "description": "High-level feature summary" },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status", "steps_completed"]
}
```

### 9.9 documenter.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:documenter:v1",
  "title": "Documenter Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "files_updated": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "action"],
        "properties": {
          "path": { "type": "string", "description": "Path to the documentation file" },
          "action": { "type": "string", "enum": ["created", "updated", "deleted", "unchanged"] },
          "summary": { "type": "string", "description": "Brief summary of the documentation change" }
        }
      }
    },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status"]
}
```

### 9.10 ideation.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:ideation:v1",
  "title": "Ideation Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "options": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "description"],
        "properties": {
          "name": { "type": "string", "description": "Short name for this option" },
          "description": { "type": "string", "description": "Detailed description" },
          "pros": { "type": "array", "items": { "type": "string" } },
          "cons": { "type": "array", "items": { "type": "string" } },
          "effort": { "type": "string", "enum": ["low", "medium", "high", "unknown"] }
        }
      }
    },
    "recommended_approach": {
      "type": "object",
      "properties": {
        "option": { "type": "string" },
        "rationale": { "type": "string" },
        "next_steps": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["option", "rationale"]
    },
    "risks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "risk": { "type": "string" },
          "impact": { "type": "string", "enum": ["low", "medium", "high", "critical"] },
          "mitigation": { "type": "string" }
        },
        "required": ["risk", "impact"]
      }
    },
    "follow_up": {
      "type": "string",
      "enum": ["requirements", "research", "prototype", "discussion", "none"],
      "description": "Recommended next action"
    },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status", "options", "recommended_approach"]
}
```

### 9.11 performance.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:performance:v1",
  "title": "Performance Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "bottlenecks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["location", "impact"],
        "properties": {
          "location": { "type": "string", "description": "File:line or component name" },
          "impact": { "type": "string", "enum": ["high", "medium", "low"] },
          "description": { "type": "string" },
          "current_value": { "type": "string", "description": "Current performance metric" },
          "target_value": { "type": "string", "description": "Target performance metric" }
        }
      }
    },
    "metrics": {
      "type": "object",
      "description": "Key performance metrics collected",
      "additionalProperties": { "type": ["number", "string"] }
    },
    "recommendations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["description", "expected_impact"],
        "properties": {
          "description": { "type": "string" },
          "expected_impact": { "type": "string", "enum": ["high", "medium", "low"] },
          "effort": { "type": "string", "enum": ["low", "medium", "high"] },
          "files_affected": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status"]
}
```

### 9.12 security-auditor.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:security-auditor:v1",
  "title": "Security Auditor Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "issues": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["title", "severity", "description"],
        "properties": {
          "title": { "type": "string" },
          "severity": { "type": "string", "enum": ["critical", "high", "medium", "low", "info"] },
          "description": { "type": "string" },
          "file": { "type": "string" },
          "line": { "type": "integer" },
          "owasp_category": { "type": "string", "description": "OWASP Top 10 category identifier" },
          "cwe_id": { "type": "string", "description": "CWE identifier if applicable" },
          "recommendation": { "type": "string" }
        }
      }
    },
    "severity_counts": {
      "type": "object",
      "properties": {
        "critical": { "type": "integer", "minimum": 0 },
        "high": { "type": "integer", "minimum": 0 },
        "medium": { "type": "integer", "minimum": 0 },
        "low": { "type": "integer", "minimum": 0 },
        "info": { "type": "integer", "minimum": 0 }
      }
    },
    "owasp_categories": {
      "type": "array",
      "items": { "type": "string" },
      "description": "OWASP categories that were checked"
    },
    "summary": { "type": "string", "description": "Overall security posture summary" },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status", "issues"]
}
```

### 9.13 log-analyzer.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:log-analyzer:v1",
  "title": "Log Analyzer Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "severity_counts": {
      "type": "object",
      "properties": {
        "emergency": { "type": "integer", "minimum": 0 },
        "alert": { "type": "integer", "minimum": 0 },
        "critical": { "type": "integer", "minimum": 0 },
        "error": { "type": "integer", "minimum": 0 },
        "warning": { "type": "integer", "minimum": 0 },
        "notice": { "type": "integer", "minimum": 0 },
        "info": { "type": "integer", "minimum": 0 },
        "debug": { "type": "integer", "minimum": 0 }
      }
    },
    "top_errors": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["message", "frequency"],
        "properties": {
          "message": { "type": "string", "description": "Error message pattern" },
          "frequency": { "type": "integer", "description": "Number of occurrences" },
          "first_seen": { "type": "string", "format": "date-time" },
          "last_seen": { "type": "string", "format": "date-time" },
          "source": { "type": "string" }
        }
      },
      "maxItems": 20
    },
    "root_causes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "hypothesis": { "type": "string" },
          "confidence": { "type": "string", "enum": ["high", "medium", "low"] },
          "supporting_evidence": { "type": "array", "items": { "type": "string" } }
        },
        "required": ["hypothesis", "confidence"]
      }
    },
    "recommendations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "action": { "type": "string" },
          "priority": { "type": "string", "enum": ["immediate", "high", "medium", "low"] },
          "delegate_to": { "type": "string" }
        },
        "required": ["action", "priority"]
      }
    },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status"]
}
```

### 9.14 meta-feedback.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:meta-feedback:v1",
  "title": "Meta-Feedback Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "issue_type": {
      "type": "string",
      "enum": ["bug", "feature-request", "improvement", "new-agent", "new-command", "documentation"]
    },
    "issue_title": { "type": "string", "description": "GitHub issue title" },
    "issue_body": { "type": "string", "description": "GitHub issue body (may include markdown)" },
    "issue_url": { "type": "string", "format": "uri", "description": "URL to the created GitHub issue" },
    "labels": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Labels applied to the issue"
    },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status", "issue_type", "issue_title"]
}
```

### 9.15 feedback.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:feedback:v1",
  "title": "Feedback Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "issue_type": {
      "type": "string",
      "enum": ["bug", "feature-request", "improvement", "question", "documentation"]
    },
    "issue_title": { "type": "string", "description": "GitHub issue title" },
    "issue_body": { "type": "string", "description": "GitHub issue body (may include markdown)" },
    "issue_url": { "type": "string", "format": "uri", "description": "URL to the created GitHub issue" },
    "labels": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Labels applied to the issue"
    },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status", "issue_type", "issue_title"]
}
```

### 9.16 agent-meta-manager.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:agent-meta-manager:v1",
  "title": "Agent-Meta-Manager Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "operations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["operation", "status"],
        "properties": {
          "operation": {
            "type": "string",
            "enum": ["sync", "upgrade", "create-extension", "update-extension", "check-version", "enable-skill", "disable-skill"]
          },
          "status": { "type": "string", "enum": ["success", "failed", "skipped"] },
          "details": { "type": "string" }
        }
      }
    },
    "previous_version": { "type": "string", "description": "Previous agent-meta version before upgrade" },
    "current_version": { "type": "string", "description": "Current agent-meta version after operation" },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status", "operations"]
}
```

### 9.17 agent-meta-scout.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:agent-meta-scout:v1",
  "title": "Agent-Meta-Scout Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "discoveries": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "category", "relevance"],
        "properties": {
          "name": { "type": "string", "description": "Name of the discovered item" },
          "category": {
            "type": "string",
            "enum": ["skill", "role", "pattern", "rule", "tool", "workflow", "framework"]
          },
          "relevance": { "type": "string", "enum": ["high", "medium", "low"] },
          "description": { "type": "string" },
          "source_url": { "type": "string", "format": "uri" },
          "integration_effort": { "type": "string", "enum": ["low", "medium", "high", "unknown"] }
        }
      }
    },
    "recommendations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["action", "priority"],
        "properties": {
          "action": { "type": "string" },
          "priority": { "type": "string", "enum": ["critical", "high", "medium", "low"] }
        }
      }
    },
    "confidence_score": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100,
      "description": "Overall confidence in the scouting results"
    },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status", "discoveries"]
}
```

### 9.18 docker.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:docker:v1",
  "title": "Docker Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["start", "stop", "restart", "build", "pull", "exec", "logs", "inspect", "compose", "cleanup"]
    },
    "service_name": { "type": "string", "description": "Docker Compose service or container name" },
    "container_id": { "type": "string", "description": "Container ID (short form)" },
    "ports": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "host": { "type": "integer" },
          "container": { "type": "integer" },
          "protocol": { "type": "string", "enum": ["tcp", "udp"] }
        }
      },
      "description": "Port mappings"
    },
    "image": { "type": "string", "description": "Docker image name:tag" },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status", "operation"]
}
```

### 9.19 infrastructure-check.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:infrastructure-check:v1",
  "title": "Infrastructure Check Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "status"],
        "properties": {
          "name": { "type": "string", "description": "Name of the prerequisite" },
          "status": { "type": "string", "enum": ["installed", "missing", "wrong-version", "unknown"] },
          "expected_version": { "type": "string" },
          "found_version": { "type": "string" },
          "source": { "type": "string", "description": "Which artifact requires this (hook/MCP/agent)" }
        }
      }
    },
    "missing_deps": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "install_hint"],
        "properties": {
          "name": { "type": "string" },
          "install_hint": { "type": "string", "description": "How to install this dependency" },
          "required_by": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "installed_deps": {
      "type": "array",
      "items": { "type": "string" }
    },
    "recommendations": {
      "type": "array",
      "items": { "type": "string" }
    },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status", "checks"]
}
```

### 9.20 code-splitter.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:code-splitter:v1",
  "title": "Code Splitter Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "files_split": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["source", "targets"],
        "properties": {
          "source": { "type": "string", "description": "Original monolithic file" },
          "targets": {
            "type": "array",
            "items": { "type": "string" },
            "description": "New files created from the split"
          },
          "original_lines": { "type": "integer", "minimum": 0 },
          "reason": { "type": "string", "description": "Why the split was performed" }
        }
      }
    },
    "new_files": {
      "type": "array",
      "items": { "type": "string" },
      "description": "All newly created files"
    },
    "summary": { "type": "string", "description": "High-level summary of the refactoring" },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status", "files_split"]
}
```

### 9.21 compliance-auditor.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:compliance-auditor:v1",
  "title": "Compliance Auditor Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["rule", "status"],
        "properties": {
          "rule": { "type": "string", "description": "Rule or standard being checked" },
          "status": { "type": "string", "enum": ["passed", "failed", "warning", "not-applicable"] },
          "details": { "type": "string" },
          "affected_files": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "checks_passed": { "type": "integer", "minimum": 0 },
    "checks_failed": { "type": "integer", "minimum": 0 },
    "score": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100,
      "description": "Compliance score percentage"
    },
    "violations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "rule": { "type": "string" },
          "severity": { "type": "string", "enum": ["critical", "high", "medium", "low"] },
          "description": { "type": "string" }
        },
        "required": ["rule", "severity", "description"]
      }
    },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status", "checks"]
}
```

### 9.22 multi-repo-refactor.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:multi-repo-refactor:v1",
  "title": "Multi-Repo Refactor Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "repos_affected": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["repo", "status"],
        "properties": {
          "repo": { "type": "string", "description": "Repository name or path" },
          "status": { "type": "string", "enum": ["success", "failed", "skipped", "unchanged"] },
          "files_changed": { "type": "integer", "minimum": 0 },
          "message": { "type": "string" }
        }
      }
    },
    "files_changed": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "path": { "type": "string" },
          "repo": { "type": "string" },
          "change_type": { "type": "string", "enum": ["created", "modified", "deleted"] }
        },
        "required": ["path", "repo"]
      }
    },
    "summary": { "type": "string", "description": "Cross-repo refactoring summary" },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status", "repos_affected"]
}
```

### 9.23 openscad-developer.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:openscad-developer:v1",
  "title": "OpenSCAD Developer Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "files_generated": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path"],
        "properties": {
          "path": { "type": "string", "description": "Path to the generated .scad file" },
          "stl_exported": { "type": "boolean", "description": "Whether STL was exported" },
          "stl_path": { "type": "string" }
        }
      }
    },
    "render_result": {
      "type": "string",
      "enum": ["success", "error", "warning", "not-rendered"],
      "description": "Result of the OpenSCAD render operation"
    },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status"]
}
```

### 9.24 bun-ci.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "agent-meta:output-schema:bun-ci:v1",
  "title": "Bun CI Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": {
    "build_status": {
      "type": "string",
      "enum": ["passed", "failed", "skipped", "not-run"],
      "description": "Result of the build step"
    },
    "test_results": {
      "type": "object",
      "properties": {
        "total": { "type": "integer", "minimum": 0 },
        "passed": { "type": "integer", "minimum": 0 },
        "failed": { "type": "integer", "minimum": 0 },
        "skipped": { "type": "integer", "minimum": 0 }
      },
      "required": ["total", "passed", "failed"],
      "description": "Test execution results"
    },
    "duration_ms": {
      "type": "integer",
      "minimum": 0,
      "description": "Total CI execution time in milliseconds"
    },
    "message": { "$ref": "base.schema.json#/properties/message" },
    "warnings": { "$ref": "base.schema.json#/properties/warnings" }
  },
  "required": ["status"]
}
```

---

## 10. Implementierungs-Anweisungen für developer

### 10.1 Ablauf

1. **Schema-Dateien anlegen** — 6 Cluster-Dateien in `config/output-schemas/`
2. **role-defaults.yaml erweitern** — `output_schema:` Feld in ALLEN Rollen (verweist auf Cluster-Schemas)
3. **config.py erweitern** — `_inject_output_schema_variables()` Funktion
4. **Alle Agent-Templates erweitern** — Neue Sektion "Structured Output Contract" (conditional per Cluster)
5. **Orchestrator-Template erweitern** — Neue Sektion "Structured Output Validation"
6. **sync.py --dry-run** testen

### 10.2 Schema-Datei-Erstellung (6 Cluster-Dateien)

Jede Cluster-Schema-Datei folgt diesem Muster:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "<cluster-name>.schema.json",
  "title": "<Cluster> Output",
  "allOf": [{ "$ref": "base.schema.json" }],
  "type": "object",
  "properties": { ... cluster-spezifische Felder ... },
  "required": ["status", ...]
}
```

Die vollständigen Definitionen stehen in den 6 Dateien unter `config/output-schemas/`.

### 10.3 role-defaults.yaml Änderung

Jede Rolle bekommt ein neues Feld:
```yaml
developer:
  ...
  output: "Implementierter Code, ggf. Commit SHA oder Diff"
  output_schema: "config/output-schemas/developer.schema.json"
```

Für Rollen ohne existing output-Feld: das `output_schema:`-Feld an geeigneter Stelle einfügen (nach `output:` oder nach `description:`).

### 10.4 config.py Änderung

In `build_variables()` eine neue Hilfsfunktion `_inject_output_schema_variables()`:

```python
def _inject_output_schema_variables(variables: dict, config: dict, agent_meta_root: Path) -> tuple[dict, list[str]]:
    """Inject OUTPUT_SCHEMA_<ROLE> variables and HAS_OUTPUT_SCHEMAS flag."""
    from .roles import load_roles_config
    
    roles_cfg = load_roles_config(agent_meta_root)  # role-defaults.yaml
    has_schemas = False
    warnings = []
    
    for role, role_cfg in roles_cfg.get("roles", {}).items():
        schema_path = role_cfg.get("output_schema", "")
        if not schema_path:
            continue
        full_path = agent_meta_root / schema_path
        if not full_path.exists():
            warnings.append(f"Schema file not found: {schema_path} (role: {role})")
            continue
        try:
            schema = json.loads(full_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            warnings.append(f"Schema parse error: {schema_path} — {e}")
            continue
        
        var_name = f"OUTPUT_SCHEMA_{role.upper()}"
        variables[var_name] = json.dumps(schema, indent=2)
        variables[f"{var_name}_EXAMPLE"] = _generate_example_from_schema(schema)
        has_schemas = True
    
    variables["HAS_OUTPUT_SCHEMAS"] = "true" if has_schemas else "false"
    return variables, warnings


def _generate_example_from_schema(schema: dict) -> str:
    """Generate a minimal example JSON from a schema's properties."""
    example = {"status": "success", "message": "Task completed successfully."}
    props = schema.get("properties", {})
    for key, prop in props.items():
        if key in example:
            continue
        prop_type = prop.get("type", "string")
        if prop_type == "array":
            example[key] = []
        elif prop_type == "object":
            example[key] = {}
        elif prop_type == "integer":
            example[key] = 0
        elif prop_type == "number":
            example[key] = 0.0
        elif prop_type == "boolean":
            example[key] = True
        else:
            example[key] = "<value>"
    
    # Handle allOf inheritance from base schema
    for combine in schema.get("allOf", []):
        ref = combine.get("$ref", "")
        if ref == "base.schema.json":
            example["status"] = "success"
            example["message"] = "Task completed successfully."
    
    return json.dumps(example, indent=2)
```

Diese Funktion wird in `build_variables()` aufgerufen:
```python
# Am Ende von build_variables():
schema_vars, schema_warnings = _inject_output_schema_variables(variables, config, agent_meta_root)
pre_warnings.extend(schema_warnings)
```

### 10.5 Template-Änderung (alle Agenten mit Schema)

Jeder Agent mit `output_schema` in `role-defaults.yaml` bekommt am Ende (vor der letzten Sektion, z.B. vor "## Sprache" oder "## Don'ts") diesen Conditional-Block:

```
{{#if OUTPUT_SCHEMA_<ROLE>}}
## Structured Output Contract

Dein Output MUSS am Ende der Antwort als JSON-Block im folgenden Format stehen.
Der Orchestrator validiert diesen Block maschinell. Freitext davor ist erlaubt,
aber der JSON-Block ist die maschinell auswertbare Antwort.

```json
<HIER STEHT DAS OUTPUT_SCHEMA_<ROLE>>
```

### Regeln
1. **JSON-Block immer am ENDE der Antwort** — nach dem letzten ``` ``` ```
2. **Alle required-Felder befüllen** — Validierung schlägt sonst fehl
3. **Keine zusätzlichen Felder** außerhalb des Schemas (striktes Schema)
4. **Bei Abbruch/Fehler** → `status: "failed"` setzen und Grund in `message`-Feld
{{/if}}
```

Wobei `<ROLE>` der Großbuchstaben-Name der Rolle ist (z.B. `DEVELOPER`, `GIT`, `TESTER`, etc.).

### 10.6 Orchestrator-Änderung

Der Orchestrator bekommt eine neue Sektion **"## Structured Output Validation"**:

```
{{#if HAS_OUTPUT_SCHEMAS}}
## Structured Output Validation

**RIGOROSE Validierung** — jedes Schema ist VERPFLICHTEND für den zugehörigen Agenten.

### Validierungs-Workflow

Wenn ein Agent einen Output zurückliefert:

1. **Extrahiere den letzten JSON-Block** aus der Antwort (alles zwischen
   dem letzten ```json und ``` im Text)
2. **Versuche JSON zu parsen:**
   - Erfolg: → Weiter mit Schritt 3
   - Fehler: → **SENDE ZURÜCK** mit Nachricht:
     "Dein Output enthielt keinen validen JSON-Block. Bitte wiederhole mit korrektem JSON."
3. **Validiere gegen das Schema:**
   - Prüfe ob alle `required`-Felder vorhanden sind
   - Prüfe ob `status` einen gültigen Wert hat (Enum-Prüfung)
   - Prüfe ob Feld-Typen korrekt sind (string, array, object, integer, boolean)
4. **Bei Validierungsfehlern:**
   - **SENDE ZURÜCK** an den Agenten mit konkretem Feedback:
     "Schema-Validierung fehlgeschlagen. Fehlende/inkorrekte Felder: [Liste].
      Bitte korrigiere und wiederhole."
5. **Bei erfolgreicher Validierung:**
   - Extrahiere relevante Felder für den nächsten Schritt
   - Gib die strukturierten Daten an den nächsten Agenten weiter

### Strict Mode
- **Keine Abweichung tolerieren** — fehlende Required-Felder → Retry
- **Kein Freitext-Fallback** bei vorhandenem Schema — der Agent MUSS JSON liefern
- **Max 2 Retries** pro Agent, dann Fehlschlag melden

### Validierungs-Checkliste (für Orchestrator)
- [ ] JSON-Block vorhanden?
- [ ] JSON syntaktisch korrekt?
- [ ] `status`-Feld vorhanden und gültig?
- [ ] Alle required-Felder befüllt?
- [ ] Feld-Typen korrekt?
- [ ] `status: "failed"` → Grund in `message`?
{{/if}}
```

### 10.7 agents.py Änderung

In `sync_agents_for_provider()` muss `HAS_OUTPUT_SCHEMAS` zu `provider_vars` hinzugefügt werden (von `variables` übernommen).

---

**Ende des erweiterten Design-Dokuments.**

## 11. Schema-Clustering (Reduktion von 25 auf 6)

> **Status:** Implementiert (Issue #165)  
> **Branch:** `feat/structured-output-contracts`  
> **Datum:** 2026-05-20

### 11.1 Motivation

Der ursprüngliche Ansatz mit **25 individuellen Schema-Dateien** (eine pro Agent) führte zu:

- **Hoher Wartungsaufwand** — jede Schema-Änderung musste in vielen Dateien nachgezogen werden
- **Redundanz** — ähnliche Agenten (z.B. developer, git, tester) hatten stark überlappende Felder
- **Unübersichtlichkeit** — 25 Dateien in `config/output-schemas/` schwer navigierbar

Die Lösung: **6 Cluster-Schemas** die Agenten nach ihrem Output-Verhalten gruppieren.

### 11.2 Cluster-Logik

Agenten werden nach der **Art ihres Outputs** gruppiert, nicht nach ihrer Rolle:

| Cluster | Output-Charakter | Agenten |
|---------|-----------------|---------|
| **Base** | Gemeinsame Basis-Felder | Alle (24) |
| **Execution** | Konkrete Ausführungsergebnisse (Dateien, Commits, Tests, Builds) | developer, git, tester, docker, bun-ci, code-splitter, multi-repo-refactor, openscad-developer, agent-meta-manager |
| **Findings** | Inspektions-/Prüfberichte mit Findings | reviewer, validator, security-auditor, performance, log-analyzer, compliance-auditor, infrastructure-check |
| **Coordination** | Lifecycle-Phasen und Koordinations-Events | feature, release, requirements |
| **Knowledge** | Wissensproduktion (Doku, Ideen, Discoveries) | documenter, ideation, agent-meta-scout |
| **Issue** | GitHub-Issue-Erstellung | feedback, meta-feedback |

### 11.3 Schema-Dateien

```
config/output-schemas/
├── base.schema.json              ← Basis-Felder (status, message, warnings, errors, duration_ms)
├── execution-result.schema.json  ← 9 Agenten
├── findings-report.schema.json   ← 7 Agenten
├── coordination-output.schema.json ← 3 Agenten
├── knowledge-output.schema.json  ← 3 Agenten
└── issue-created.schema.json     ← 2 Agenten
```

Jedes Cluster-Schema erbt via `allOf` von `base.schema.json` und fügt cluster-spezifische Felder hinzu.

### 11.4 5-Stufen-Einführungsplan

Statt alle 24 Agenten auf einmal umzustellen, erfolgt die Einführung in 5 Stufen:

| Stufe | Neue Cluster | Agenten | Risiko |
|-------|-------------|---------|--------|
| **1. Core** | base + execution-result + issue-created | developer, git, tester, feedback, meta-feedback | Niedrig — Core-Workflow |
| **2. Quality** | + findings-report | reviewer, validator | Niedrig — nur lesende Agenten |
| **3. Lifecycle** | + coordination-output | feature, release, requirements | Mittel — Lifecycle-Koordination |
| **4. Knowledge** | + knowledge-output | documenter, ideation, agent-meta-scout | Niedrig — dokumentierende Agenten |
| **5. Full** | execution-result + findings-report erweitert | docker, bun-ci, code-splitter, multi-repo-refactor, openscad-developer, agent-meta-manager, security-auditor, performance, log-analyzer, compliance-auditor, infrastructure-check | Mittel — spezialisierte Agenten |

**Stufe 1** deckt den häufigsten Workflow ab: Developer implementiert → Tester prüft → Git committet → Feedback erstellt Issues.

**Stufe 5** vervollständigt die Abdeckung für alle 24 Agenten.

### 11.5 Migration von 25 auf 6

Die alten 24 agent-spezifischen Schema-Dateien wurden entfernt. Die `role-defaults.yaml` referenziert nun Cluster-Schemas statt individueller Schemas:

```yaml
# Vorher (25 Dateien):
developer:
  output_schema: "config/output-schemas/developer.schema.json"

# Nachher (6 Cluster):
developer:
  output_schema: "config/output-schemas/execution-result.schema.json"
```

Die Template-Variablen `OUTPUT_SCHEMA_<ROLE>` und `OUTPUT_SCHEMA_<ROLE>_EXAMPLE` werden weiterhin pro Rolle generiert — sie zeigen jetzt auf das jeweilige Cluster-Schema statt auf ein individuelles.

### 11.6 Base-Schema Details

`base.schema.json` definiert die gemeinsamen Felder:

| Feld | Typ | Required | Beschreibung |
|------|-----|----------|-------------|
| `status` | enum: `success`, `partial`, `failure` | Ja | Ausführungsstatus |
| `message` | string | Ja | Menschlich-lesbare Zusammenfassung |
| `warnings` | string[] | Nein | Optionale Warnungen |
| `errors` | string[] | Nein | Fehler bei `failure` oder `partial` |
| `duration_ms` | integer | Nein | Ausführungsdauer in ms |

### 11.7 Cluster-Schema Details

#### execution-result.schema.json (9 Agenten)
**Required:** `operation`  
**Key Fields:** `files_changed[]`, `commit_sha`, `branch`, `tests_passed`, `tests_total`, `build_status`, `artifacts[]`, `repos_affected[]`, `breaking_changes`

#### findings-report.schema.json (7 Agenten)
**Required:** `scope`  
**Key Fields:** `findings[]`, `score`, `must_fix_count`, `dod_compliant`, `overall_risk`, `recommendations[]`, `root_causes[]`

#### coordination-output.schema.json (3 Agenten)
**Required:** `phase`  
**Key Fields:** `feature_name`, `req_id`, `version`, `bump_type`, `tag`, `steps_completed[]`, `pr_url`

#### knowledge-output.schema.json (3 Agenten)
**Required:** `topic`  
**Key Fields:** `files_updated[]`, `options[]`, `discoveries[]`, `next_steps[]`, `confidence`

#### issue-created.schema.json (2 Agenten)
**Required:** `issue_type`, `issue_title`  
**Key Fields:** `issue_url`, `issue_number`, `category`, `related_component`

---

## 12. Next Steps for Developer

Siehe Abschnitt 10 — vollständige Implementierungsanweisungen.
