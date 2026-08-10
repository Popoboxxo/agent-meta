---
type: Plan
title: "Framework-Fix: Planner-Pipeline-Integration — 3 Bugs (Ghost-Entries, plan_ref-Validierung, deklarative Kopplung)"
source: "3 Bugs: Ghost-Entry delegation_table.py, plan_ref Prompt-Text ohne Mechanismus, fehlende Planner↔Pipeline-Kopplung"
estimated_effort: "~3.5 h (reference effort-estimator: 5 discrete steps across 4 files, low-medium complexity; delegation_table.py change is trivial one-liner, pipelines.py gets new functions (~80 lines), role-defaults.yaml gets additive fields, orchestrator.md gets new workflow gate section; planner template gets minor frontmatter update for stage mapping)"
created: "2026-08-10"
status: "planned"
branch: "fix/orchestrator-delegation-reliability"
---

# Plan: Planner-Pipeline-Integration — 3 Bugs

**Source:** 3 Bugs in der planner-pipeline-Integration des agent-meta Frameworks
**Estimated effort:** ~3.5 h (reference `effort-estimator` — 5 steps, 4 files touched plus 1 template update; low-medium complexity, no provider-specific code; Step 5 adds orchestrator.md workflow gate with prompt-engineering complexity)

## Overview

Das agent-meta Framework hat eine `feature-lifecycle` Pipeline mit `plan-driven`-Stages und einen `planner`-Agenten. Drei Bugs verursachen Unzuverlässigkeit in der Orchestrator-Delegation:

1. **Ghost-Entry:** `delegation_table.py` filtert nur `optional`-Tier-Rollen aus Routing-Tabellen — `recommended`-Rollen (wie `planner`) erscheinen auch wenn nicht in `project.yaml` → `roles:` gelistet
2. **plan_ref ist toter Text:** `pipelines.py:574-589` generiert nur Prompt-Text, kein validierender Code. Kein Plan-Parsing, keine `allowed_agents`-Prüfung
3. **Keine deklarative Kopplung:** Der `planner`-Eintrag in `role-defaults.yaml` hat kein `produces:`-Feld. Die Verknüpfung `planner → feature-lifecycle` existiert nur im Orchestrator-Prompt-Freitext

**Reihenfolge:** Bug 1 → Bug 3 → Bug 2 → Step 5 (Abhängigkeiten: Bug 1 ist isoliert; Bug 3 definiert die `produces:`-Struktur die Bug 2 nutzt; Bug 2 ist der komplexeste Fix; Step 5 hängt von Bug 2 ab — die plan-driven Pipeline-Blöcke müssen korrigiert sein, bevor der Orchestrator sie korrekt referenziert)

**Scope:** Nur Framework-Schicht (`scripts/lib/`, `config/`, `agents/1-generic/`). Provider-agnostisch. Kein provider-spezifischer Code.

---

## Step-by-Step Implementation

| # | Step | Agent | Depends on | Acceptance criteria |
|---|---|---|---|---|
| 1 | **Bug 1: Fix tier filter in delegation_table.py** | `developer` | — | `sync.py` generiert keine Ghost-Entries in Routing-Tabellen für nicht-aktive `recommended`-Rollen |
| 2 | **Bug 3: Add `produces:` to planner in role-defaults.yaml** | `developer` | 1 | `planner.produces.plan.pipeline == "feature-lifecycle"` im YAML, `sync.py --validate` läuft ohne Parse-Fehler |
| 3 | **Bug 3: Add coupling consistency check in pipelines.py** | `developer` | 2 | `sync.py --validate` warnt wenn eine `plan-driven`-Pipeline keinen `produces`-deklarierenden Producer hat |
| 4 | **Bug 2: Implement plan_ref parsing, validation, and block generation** | `senior-developer` | 3 | `parse_plan_ref()` extrahiert Stage→Agent-Mappings korrekt; generierte Plan-driven-Blöcke enthalten validierende Anweisungen |
| 5 | **Orchestrator Gate: Plan-driven delegation gate in §2 + §6 präzisieren** | `senior-developer` | 4 | Orchestrator-Prompt enthält §2 plan-driven Gate (vor Intent Routing); §6 "Complex feature" referenziert Gate; `sync.py` regeneriert provider-Dateien ohne Fehler |

---

## Step 1 — Bug 1: Fix tier filter in delegation_table.py

### Datei: `scripts/lib/delegation_table.py`

#### Änderung: Zeile 39

**Ist-Zustand (L:39):**
```python
if tier == "optional" and active_roles is not None and role_name not in active_roles:
    continue
```

**Soll-Zustand:**
```python
if active_roles is not None and role_name not in active_roles:
    continue
```

#### Warum das reicht

Die Zeile 39 filtert derzeit nur Rollen mit `workflow_tier: optional` aus, wenn `project.yaml` → `roles:` explizit gesetzt ist. Rollen mit `workflow_tier: recommended` (wie `planner`, `requirements`, `tester`) erscheinen auch dann in `AGENT_DELEGATION_TABLE` und `INTENT_ROUTING_TABLE`, wenn sie nicht in `roles:` gelistet sind. Der Orchestrator routet Intents an einen nicht existierenden Agenten.

Nach dem Fix filtert die Bedingung ALLE Tiers — unabhängig von `optional`/`recommended`/`required`. Eine Rolle, die nicht in `config['roles']` ist, erscheint in keiner Routing-Tabelle.

**Betroffene Funktionen:**
- `get_active_agents_data()` (L:7-48): liefert die bereinigte Agentenliste
- `get_intent_routing_table()` (L:51-101): verwendet `get_active_agents_data()`, profitiert automatisch

#### Test-Strategie

1. **`sync.py --validate`** nach dem Fix — keine neuen Fehler
2. **Manueller Test:** `project.yaml` → `roles:` auf `[orchestrator, developer, git]` setzen, sync.py ausführen → `planner`, `requirements`, `tester` (alle `recommended`) dürfen NICHT in den generierten Routing-Tabellen erscheinen
3. **Manueller Test:** `roles:` ohne `planner` → `sync.py --validate` darf keinen Fehler wegen `feature-lifecycle` plan-driven Stage werfen (da `planner` nicht aktiv ist, sollte der Check nur warnen oder skipped werden)

#### sync.py-Propagation

- `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` — `AGENT_DELEGATION_TABLE` und `INTENT_ROUTING_TABLE` werden neu generiert
- `.opencode/agents/orchestrator.md` — Routing-Tabellen im Orchestrator-Prompt
- `.gemini/agents/orchestrator.md` — dito
- `docs/agent-mindmap.md` — Agent-Graph wird neu generiert

---

## Step 2 — Bug 3: Add `produces:` to planner in role-defaults.yaml

### Datei: `config/role-defaults.yaml`

#### Änderung: planner-Eintrag (Zeilen 180-194)

**Soll-Zustand** — `produces:`-Block zwischen `routing:` und `short_desc:` einfügen:

```yaml
  planner:
    model: balanced
    memory: ''
    workflow_tier: recommended
    description: Erzeugt konkrete, geordnete Umsetzungspläne aus Konzepten/REQs/Bugs
    routing:
      intent_keywords:
      - Plan
      - Planung
      - Schritte
      - Umsetzungsplan
      - "wie setzen wir das um"
      parallel: false
      orchestrator_only: false
    produces:
      plan:
        pipeline: feature-lifecycle
        ref_key: plan_ref
        stage: implement
    short_desc: Umsetzungsplanung
```

#### Feld-Semantik

| Feld | Bedeutung |
|------|-----------|
| `produces.plan.pipeline` | Name der Pipeline, die diesen Plan konsumiert |
| `produces.plan.ref_key` | Payload-Key, unter dem der Plan-Pfad übergeben wird |
| `produces.plan.stage` | Pipeline-Stage-ID, die den Plan ausführt |

#### Warum `produces` statt `pipeline_stages` im Agenten-Eintrag

Der `produces:`-Ansatz deklariert den **Output** des Agenten, nicht seine Rolle in einer Pipeline. Das folgt dem Dependency-Inversion-Prinzip: Die Pipeline deklariert, dass sie einen Plan akzeptiert (`plan-driven`-Stage); der Agent deklariert, dass er einen Plan produziert. Der Consistency-Check prüft die Bidirektionalität.

Diese Struktur ist zukunftssicher: Ein Agent könnte mehrere Output-Typen produzieren (`plan`, `spec`, `audit-report`), jeder mit eigener Ziel-Pipeline.

#### Test-Strategie

1. `python scripts/sync.py --validate` — YAML muss ohne Parse-Fehler laden
2. `sync.py --validate` gibt KEINE Warnung aus, da `feature-lifecycle` eine `plan-driven`-Stage hat UND `planner` jetzt `produces.plan.pipeline == "feature-lifecycle"` deklariert
3. Negativ-Test: `produces.plan.pipeline: "non-existent"` setzen → `sync.py --validate` muss warnen

#### sync.py-Propagation

- Keine direkte Propagation in generierte Dateien — `produces:` wird nur von `validate_pipelines()` gelesen
- Indirekt: Warnings/Errors in `sync.log` bei Inkonsistenz

---

## Step 3 — Bug 3: Add coupling consistency check in pipelines.py

### Datei: `scripts/lib/pipelines.py`

#### Neue Funktion: `check_plan_producer_coupling()` (nach Zeile 262, vor `generate_pipeline_match_table`)

```python
def check_plan_producer_coupling(pipelines: dict, roles_config: dict) -> list[str]:
    """Check that every pipeline with plan-driven stages has a declared producer.

    Returns a list of warning messages (non-fatal). Empty list = consistent.
    """
    warnings = []
    roles = roles_config.get("roles", {})

    # Collect plan-driven pipelines
    plan_driven_pipelines = set()
    for name, pipeline in pipelines.items():
        if not pipeline.get("enabled", True):
            continue
        for stage in pipeline.get("stages", []):
            if stage.get("mode") == "plan-driven":
                plan_driven_pipelines.add(name)

    if not plan_driven_pipelines:
        return warnings

    # Collect declared plan producers
    producers_by_pipeline: dict[str, list[str]] = {}
    for role_name, role_info in roles.items():
        produces = role_info.get("produces", {})
        plan_cfg = produces.get("plan")
        if plan_cfg and plan_cfg.get("pipeline"):
            pipeline_name = plan_cfg["pipeline"]
            producers_by_pipeline.setdefault(pipeline_name, []).append(role_name)

    # Check each plan-driven pipeline has at least one producer
    missing = plan_driven_pipelines - set(producers_by_pipeline.keys())
    for pipeline_name in sorted(missing):
        warnings.append(
            f"Pipeline '{pipeline_name}' has plan-driven stage(s) but no role "
            f"declares produces.plan.pipeline = '{pipeline_name}'. "
            f"Add a 'produces:' block to the planner role in config/role-defaults.yaml."
        )

    # Check declared producers reference existing pipelines
    for pipeline_name, producers in producers_by_pipeline.items():
        if pipeline_name not in pipelines:
            warnings.append(
                f"Role(s) {', '.join(producers)} declare produces.plan.pipeline = "
                f"'{pipeline_name}' but this pipeline does not exist."
            )
        elif pipeline_name not in plan_driven_pipelines:
            warnings.append(
                f"Role(s) {', '.join(producers)} declare produces.plan.pipeline = "
                f"'{pipeline_name}' but this pipeline has no plan-driven stages."
            )

    return warnings
```

#### Aufruf-Integration

Die Funktion muss von `sync.py` aus aufgerufen werden. In `sync.py` wird `validate_pipelines()` aufgerufen und danach `check_plan_producer_coupling()`. Die genaue Aufrufstelle ist in `scripts/sync.py` (abhängig von der aktuellen `sync.py`-Struktur). Alternativ kann die Funktion in `validate_pipelines()` selbst aufgerufen werden, wenn der `roles_config`-Parameter übergeben wird.

**Empfohlener Ansatz:** `validate_pipelines()`-Signatur erweitern:

```python
def validate_pipelines(pipelines: dict, available_roles: list, roles_config: dict | None = None) -> list[str]:
```

Am Ende von `validate_pipelines()` (nach Zeile 260, vor `return errors`):

```python
    # Check plan-producer coupling (non-fatal warnings)
    if roles_config is not None:
        coupling_warnings = check_plan_producer_coupling(pipelines, roles_config)
        errors.extend(coupling_warnings)
```

#### Test-Strategie

1. Vor dem Fix (Step 3): `sync.py --validate` sollte eine Warnung ausgeben, dass `feature-lifecycle` plan-driven Stages hat aber `planner` noch kein `produces` deklariert (dieser Test wird erst nach Step 2+3 sinnvoll, da Step 2 das `produces:`-Feld hinzufügt)
2. Nach Step 2+3: `sync.py --validate` KEINE Warnung mehr
3. Entferne `produces:` aus planner → `sync.py --validate` warnt wieder
4. Setze `produces.plan.pipeline: "non-existent"` → `sync.py --validate` warnt, dass Pipeline nicht existiert

#### sync.py-Propagation

- `sync.log` enthält ggf. Kopplungs-Warnings
- `sync.py --validate` Exit-Code bleibt 0 (Warnings sind non-fatal)

---

## Step 4 — Bug 2: Implement plan_ref parsing, validation, and block generation

### Überblick

Dieser Step enthält die komplexesten Änderungen:
- **Neue Utility-Funktion `parse_plan_ref()`** — parst eine Plan-Markdown-Datei und extrahiert Stage→Agent-Mappings
- **Neue Funktion `validate_plan_ref()`** — validiert ein Plan-File gegen Pipeline-Stage-Constraints
- **Refactored `_generate_pipeline_block` plan-driven Sektion** — ersetzt reinen Freitext durch strukturierte, validierende Anweisungen
- **Planner-Template-Update** — fügt `pipeline:`-Frontmatter-Feld in den Plan-Output ein (Stage-Mapping-Konvention)

### Datei: `scripts/lib/pipelines.py`

#### Neue Funktion 1: `parse_plan_ref()` (einfügen nach `check_plan_producer_coupling`)

```python
def parse_plan_ref(plan_path: str) -> dict:
    """Parse a plan markdown file and extract stage-to-agent mappings.

    Recognizes two sources of stage-to-agent information, in priority order:
    1. Frontmatter field `pipeline_stages:` — explicit mapping of pipeline
       stage IDs to step numbers: ``{implement: 4, verify: 5}``
    2. Steps table (markdown table with columns Step and Agent) — treated
       as fallback: step_index → agent mapping, consumer must match stage
       IDs to step indices externally.

    Returns:
        dict with keys:
        - 'stages': dict[str, int]  — {stage_id: step_number} from frontmatter
        - 'steps':  dict[int, str]  — {step_number: agent_name} from table
        - 'raw_agents': list[str]    — all agent names found in the plan
        - 'file_exists': bool
    """
    import os
    result = {
        "stages": {},
        "steps": {},
        "raw_agents": [],
        "file_exists": False,
    }

    if not os.path.exists(plan_path):
        return result

    result["file_exists"] = True

    with open(plan_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract frontmatter pipeline_stages
    fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        try:
            import yaml
            fm = yaml.safe_load(fm_match.group(1)) or {}
            ps = fm.get("pipeline_stages")
            if isinstance(ps, dict):
                result["stages"] = {str(k): int(v) for k, v in ps.items()}
        except Exception:
            pass  # Non-YAML frontmatter or parse error — ignore

    # Extract steps table
    # Table format: | # | Step | Agent | ... |
    table_pattern = re.compile(
        r'^\|\s*(\d+)\s*\|\s*.+?\|\s*`?(\w[\w-]*)`?\s*\|',
        re.MULTILINE,
    )
    for match in table_pattern.finditer(content):
        step_num = int(match.group(1))
        agent = match.group(2)
        result["steps"][step_num] = agent
        if agent not in result["raw_agents"]:
            result["raw_agents"].append(agent)

    return result
```

#### Neue Funktion 2: `validate_plan_ref()` (einfügen nach `parse_plan_ref`)

```python
def validate_plan_ref(
    plan_path: str,
    pipeline_name: str,
    stage_id: str,
    fallback_agent: str,
    allowed_agents: list[str],
) -> list[str]:
    """Validate a plan file against a pipeline's plan-driven stage constraints.

    Returns:
        list of error messages (empty = valid plan_ref for this stage).
    """
    errors = []
    plan = parse_plan_ref(plan_path)

    if not plan["file_exists"]:
        errors.append(
            f"Plan file '{plan_path}' does not exist. "
            f"Check the plan_ref path in the payload."
        )
        return errors

    # Check if plan declares stage mapping for this stage
    if plan["stages"]:
        if stage_id not in plan["stages"]:
            errors.append(
                f"Plan file '{plan_path}' has pipeline_stages frontmatter "
                f"but stage '{stage_id}' is not mapped. "
                f"Available stages: {', '.join(sorted(plan['stages'].keys()))}."
            )
            return errors
        step_num = plan["stages"][stage_id]
        agent = plan["steps"].get(step_num)
    else:
        # No explicit stage mapping — fall back to step existence check
        if not plan["steps"]:
            errors.append(
                f"Plan file '{plan_path}' contains no parsable steps table. "
                f"Expected format: | # | Step | Agent | ... |"
            )
            return errors
        # With no stage mapping, we can only validate that there IS an agent column;
        # the orchestrator must map stages to steps by convention/order
        return errors  # No hard error — orchestrator handles mapping

    if agent is None:
        errors.append(
            f"Plan stage '{stage_id}' maps to step {step_num}, "
            f"but step {step_num} has no agent assigned."
        )
        return errors

    if allowed_agents and agent not in allowed_agents:
        errors.append(
            f"Plan assigns agent '{agent}' to stage '{stage_id}', "
            f"but pipeline '{pipeline_name}' only allows: "
            f"{', '.join(allowed_agents)}. "
            f"Fallback agent '{fallback_agent}' will be used instead."
        )

    return errors
```

#### Änderung: `_generate_pipeline_block` plan-driven Sektion (Zeilen 574-589)

**Ist-Zustand (L:574-589):**
```python
        elif mode == "plan-driven":
            pd = stage.get("plan-driven", {})
            fallback = pd.get("fallback_agent", "")
            allowed = pd.get("allowed_agents", [])
            lines.append("")
            lines.append(
                f"**{stage_id}** — Plan-driven: Agent aus payload.plan_ref "
                f"(Stage-ID '{stage_id}') übernehmen."
            )
            if allowed:
                lines.append(f"  Erlaubte Rollen: {', '.join(allowed)}")
            lines.append(f"  Ohne plan_ref: fallback_agent = {fallback}")
            lines.append(
                "  Plan_ref vorhanden, aber Stage-Zeile fehlt: Fehler, kein stiller Fallback."
            )
            lines.append("")
```

**Soll-Zustand:**
```python
        elif mode == "plan-driven":
            pd = stage.get("plan-driven", {})
            fallback = pd.get("fallback_agent", "")
            allowed = pd.get("allowed_agents", [])
            lines.append("")
            lines.append(
                f"**{stage_id}** — Plan-driven: Agent aus payload.plan_ref "
                f"(Stage-ID '{stage_id}') übernehmen."
            )
            lines.append("")
            lines.append("  **Plan-Validierung (vor Delegation):**")
            lines.append(f"  1. Prüfe: payload.plan_ref-Pfad existiert → sonst fallback_agent = `{fallback}`")
            lines.append(f"  2. Prüfe: Plan-Frontmatter `pipeline_stages` enthält `{stage_id}` → sonst Fehler")
            if allowed:
                lines.append(f"  3. Prüfe: Agent in Stage `{stage_id}` ∈ {{{', '.join(allowed)}}} → sonst `{fallback}`")
            else:
                lines.append(f"  3. Keine allowed_agents-Restriktion — jeder Agent aus Plan akzeptiert")
            lines.append(f"  4. Bei allen Fehlern: `{fallback}` verwenden, Fehler in Status-Payload dokumentieren")
            lines.append("")
```

### Datei: `agents/1-generic/planner.md`

#### Änderung: Version bump + pipeline mapping im Persist-Schritt

**Zeile 3 — Version bump:**
```yaml
version: "1.0.2"
```

**Zeilen 39-41 — Persist-Schritt um `pipeline_stages`-Frontmatter erweitern:**

Der aktuelle `<workflow>` Schritt 4 (Persist) muss um die `pipeline_stages`-Konvention erweitert werden. Nach Zeile 41 (bzw. im Knowledge-Engine-aktiven Pfad) eine Mapping-Anweisung einfügen:

Der Plan spezifiziert bereits Stage→Schritt-Mappings im Frontmatter. Der `planner`-Agent muss beim Persistieren das `pipeline_stages`-Feld im Frontmatter setzen, basierend auf dem `produces.plan.stage`-Feld aus der `feature-lifecycle`-Pipeline.

**Konkrete Änderung im Persist-Abschnitt (nach Z. 41):**

Ergänze nach der Knowledge-Engine-Logik:
```
**Frontmatter-Konvention:** Wenn der Plan für eine Pipeline erstellt wird, die `plan-driven`-Stages hat (z.B. `feature-lifecycle`), muss das Frontmatter ein `pipeline_stages`-Feld enthalten:
```yaml
pipeline_stages:
  implement: 3    # Schritt 3 (Implementierung) → Stage "implement"
```
```

Diese Änderung ist ein Patch-Level-Update (neue optionale Frontmatter-Konvention, kein Breaking Change).

### Datei: `config/role-defaults.yaml` — planner-Eintrag `intent_keywords` erweitern

#### Änderung: `routing.intent_keywords` um Verbformen ergänzen

**Ist-Zustand (Zeilen 186-191):**
```yaml
      intent_keywords:
      - Plan
      - Planung
      - Schritte
      - Umsetzungsplan
      - "wie setzen wir das um"
```

**Soll-Zustand — vier neue Einträge:**
```yaml
      intent_keywords:
      - Plan
      - Planung
      - Schritte
      - Umsetzungsplan
      - "wie setzen wir das um"
      - plane                    # 1. Person Präsens
      - Plan erstellen           # Infinitiv + Verb
      - Umsetzungsplan erstellen
      - Implementierungsplan      # Variante
```

#### Warum das nötig ist

Der `orchestrator` matched Intents via Keyword-Matching gegen die `INTENT_ROUTING_TABLE`. Der aktuelle Keywords-Satz ist statisch — Substantive und eine Frage. Verbformen wie „plane“ (1. Person Präsens) und Infinitiv-Konstruktionen („Plan erstellen“) sind typische Nutzer-Eingaben, die derzeit nicht gematcht werden. Ohne diese Erweiterung würde der Orchestrator solche Intents an einen falschen oder gar keinen Agenten routen — der `planner` würde nie delegiert, selbst wenn der plan-driven Gate in §2 korrekt konfiguriert ist.

Die neuen Keywords sind **additiv** — kein existierendes Keyword wird entfernt.

#### sync.py-Propagation

- `INTENT_ROUTING_TABLE` in `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` wird mit den neuen Keywords regeneriert
- `.opencode/agents/orchestrator.md`, `.gemini/agents/orchestrator.md` — dito

#### Test-Strategie (Bug 2 gesamt)

1. **parse_plan_ref() Unit-Test:**
   - Plan ohne `pipeline_stages`-Frontmatter → `result["stages"]` ist leer, `result["steps"]` enthält Schritt→Agent-Mappings
   - Plan MIT `pipeline_stages: {implement: 4}` → `result["stages"]["implement"] == 4`
   - Nicht-existente Datei → `result["file_exists"] == False`
   - Plan mit leerer Tabelle → `result["steps"]` und `result["raw_agents"]` leer

2. **validate_plan_ref() Unit-Test:**
   - Plan existiert nicht → Fehler "does not exist"
   - Plan hat `pipeline_stages` aber `stage_id` fehlt → Fehler "stage X is not mapped"
   - Plan hat Mapping, aber Agent nicht in `allowed_agents` → Fehler mit Fallback-Hinweis
   - Plan ohne `pipeline_stages` aber mit Steps → kein Fehler (orchestrator handled mapping)
   - Alles korrekt → leere Fehlerliste

3. **Generierter Block:** `sync.py` ausführen → plan-driven Section im Orchestrator-Prompt enthält die 4-Schritt-Validierungsanweisungen (kein reiner Freitext mehr)

4. **End-to-End:** Plan mit `pipeline_stages: {implement: 3}` erstellen, `payload.plan_ref` setzen → Orchestrator-Prompt enthält validierende Anweisungen für Stage `implement`

#### sync.py-Propagation

- `parse_plan_ref()` und `validate_plan_ref()` sind reine Utility-Funktionen in `scripts/lib/pipelines.py` — keine direkte Propagation
- `_generate_pipeline_block`-Änderung propagiert in alle Orchestrator-Prompts: `.opencode/agents/orchestrator.md`, `.gemini/agents/orchestrator.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`
- Planner-Template-Update propagiert in `.opencode/agents/planner.md`, `.gemini/agents/planner.md` etc.
- Planner-Version-Bump: `AGENT_HINTS` in generierten Kontext-Dateien aktualisiert

---

## Step 5 — Orchestrator Gate: Plan-driven delegation gate in §2 + §6 präzisieren

### Überblick

Der Orchestrator hat keinen expliziten Workflow-Schritt, der ihn anweist, **vor** der Pipeline-Ausführung zu prüfen, ob ein Plan existiert. Der `feature-lifecycle`-Block enthält zwar `plan-driven`-Stages, aber der Orchestrator weiss nicht, WANN er den `planner` delegieren soll. 

Dieser Step fügt zwei Änderungen in `agents/1-generic/orchestrator.md` ein:
1. **§2 Pipeline Match Check:** Neuer „Plan-driven gate“-Abschnitt nach der Pipeline-Match-Tabelle, vor §3 Intent Routing
2. **§6 Task Decomposition:** Präzisierung der „Complex feature“-Zeile, damit der Orchestrator den Gate-Check nicht überspringt

### Datei: `agents/1-generic/orchestrator.md`

#### Änderung 1: Version bump (Frontmatter)

**Zeile 3:**
```yaml
version: "7.8.0"
```

**Bump-Begründung:** Neue Workflow-Sektion mit verbindlicher Gate-Logik — Minor-Bump. Kein Breaking Change (bestehende Workflow-Struktur bleibt erhalten, §2 wird erweitert, nicht ersetzt).

#### Änderung 2: Plan-driven Gate in §2 einfügen

**Einfügeposition:** Nach Zeile 33 (`{{PIPELINE_MATCH_TABLE}}`) und der nachfolgenden Leerzeile, vor Zeile 35 (`Signal → confirmation ...`). Momentan:

```markdown
## 2. Pipeline match check
{{PIPELINE_MATCH_TABLE}}

Signal → confirmation (NO auto-run) → pipeline or ad-hoc. Do not suggest disabled pipelines.
```

**Soll-Zustand — Plan-driven Gate einfügen:**

```markdown
## 2. Pipeline match check
{{PIPELINE_MATCH_TABLE}}

**Plan-driven gate:** Wenn die gematchte Pipeline `plan-driven`-Stages enthält
(z.B. `feature-lifecycle` → Stage `implement`), und KEIN Plan existiert:
→ delegiere ZUERST an `planner` zur Plan-Erstellung. Warte auf den Plan-Pfad
(`plan-*.md` oder Knowledge-Wiki Plan-Seite). Dann starte die Pipeline mit
`payload.plan_ref`. Ohne diesen Schritt würde die Pipeline mit dem Fallback-Agent
laufen — das ist nur für Quick-Fixes und triviale Tasks akzeptabel, NIEMALS für
Features mit >2 Dateien oder Architektur-Impact.

Signal → confirmation (NO auto-run) → pipeline or ad-hoc. Do not suggest disabled pipelines.
```

#### Änderung 3: §6 Task Decomposition — „Complex feature“ präzisieren

**Ist-Zustand (Zeile 64-66):**
```markdown
| User says | Action |
|-----------|--------|
| Single task | → target agent |
| Same tasks, independent | FANOUT(N, agent) |
| Mixed tasks | PARALLEL_GROUP |
| Complex feature | → `feature-lifecycle` pipeline |
```

**Soll-Zustand — Gate-Referenz in die Tabelle einbauen:**
```markdown
| User says | Action |
|-----------|--------|
| Single task | → target agent |
| Same tasks, independent | FANOUT(N, agent) |
| Mixed tasks | PARALLEL_GROUP |
| Complex feature | → §2 plan-driven gate prüfen, dann `feature-lifecycle` pipeline |
```

#### Warum das nötig ist

**Problem:** Der Orchestrator matched eine Pipeline (z.B. `feature-lifecycle`) über §2, aber ohne explizite Anweisung delegiert er direkt die Pipeline — die `plan-driven`-Stage würde mit dem `fallback_agent` (aktuell `developer`) laufen. Der `planner` wird nie involviert.

**Lösung:** Der Gate-Check ist ein **positiver Workflow-Schritt** (kein passiver Hinweis), der den Orchestrator zwingt, vor Pipeline-Start zu prüfen:
- Hat die gematchte Pipeline `plan-driven`-Stages?
- Existiert bereits ein Plan? Wenn nicht → `planner` delegieren
- Erst wenn ein Plan existiert → Pipeline mit `payload.plan_ref` starten

Die §6-Präzisierung stellt sicher, dass der Orchestrator den Gate-Check auch bei der Task-Decomposition nicht überspringt — die „Complex feature“-Zeile referenziert jetzt explizit §2.

#### Risiko: Prompt-Only Gate — keine technische Erzwingung

Dieser Gate-Mechanismus ist **reiner Prompt-Text** im Orchestrator-Template. Es gibt keine technische Barriere (kein Code in `sync.py` oder `pipelines.py`), die verhindert, dass der Orchestrator den Gate-Check ignoriert. Das LLM muss die Anweisung befolgen — das ist die gleiche Zuverlässigkeitsklasse wie alle anderen Orchestrator-Prompt-Anweisungen (Intent Routing, Tier Selection, Pre-Delegation Gate).

**Akzeptiertes Risiko** — konsistent mit der bestehenden Architektur, in der alle Delegationsentscheidungen prompt-basiert sind. Eine technische Erzwingung (z.B. in `pipelines.py`) würde den Scope dieses Plans sprengen und wäre ein eigenes Feature (`am-orch-gate-enforcement`).

#### Test-Strategie

1. **Template-Validierung:** `sync.py --validate` nach Änderung — kein Parse-Fehler im Orchestrator-Template
2. **Generierter Prompt enthält Gate:** `sync.py` ausführen → `.opencode/agents/orchestrator.md` enthält den „Plan-driven gate“-Block nach `PIPELINE_MATCH_TABLE`
3. **§6 enthält Gate-Referenz:** Generierter Orchestrator-Prompt → „Complex feature“-Zeile referenziert „§2 plan-driven gate prüfen“
4. **Funktionale Probe (manuell):** Task „Implementiere Feature X“ → Orchestrator matched `feature-lifecycle` → prüft ob `plan-*.md` existiert → delegiert `planner` wenn nicht → nach Plan-Erstellung: startet Pipeline mit `payload.plan_ref`
5. **Negativ-Test:** Quick-Fix (<2 Dateien, kein Architektur-Impact) → Orchestrator matched `feature-lifecycle` → `implement`-Stage läuft mit `fallback_agent` (bewusstes Verhalten — der Gate-Check erlaubt Quick-Fixes ohne Plan)

#### sync.py-Propagation

- `.opencode/agents/orchestrator.md` — Gate-Block und §6-Änderung erscheinen im generierten Prompt
- `.gemini/agents/orchestrator.md` — dito
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` — Orchestrator-Prompt-Block wird neu generiert
- Keine `scripts/lib/`-Änderungen — reine Template-Änderung

---

## Risk Analysis

| Risk | Severity | Mitigation |
|------|----------|------------|
| Bug 1: `required`-Tier-Rollen in `roles:` könnten versehentlich herausgefiltert werden | Low | `required`-Rollen (orchestrator, developer, git, feedback, log-analyzer) sollten immer in `roles:` sein — Standard-Projekt-Template enthält sie. Test mit Standard-Config bestätigt. |
| Bug 3: `validate_pipelines()`-Signaturänderung bricht bestehende Aufrufer | Low | Neuer Parameter `roles_config` ist optional (`None` default) — bestehende Aufrufe ohne `roles_config` bleiben kompatibel |
| Bug 2: `parse_plan_ref()` YAML-Parse kann fehlschlagen bei nicht-standard Frontmatter | Low | `try/except` fängt alle YAML-Fehler ab, Fallback auf Table-Only-Parsing |
| Bug 2: Planner-Template-Änderung bricht bestehende Plan-Formate | None | `pipeline_stages` ist optional im Frontmatter — alte Pläne ohne das Feld funktionieren weiter (orchestrator mapped stages per Konvention/Reihenfolge) |
| Step 5: Orchestrator ignoriert plan-driven Gate, da reiner Prompt-Text ohne technische Erzwingung | Medium | Gleiche Zuverlässigkeitsklasse wie alle anderen Orchestrator-Anweisungen (Intent Routing, Tier Selection, Pre-Delegation Gate). Gate ist prominent in §2 platziert (vor §3) und durch §6-Referenz verstärkt. LLM-Delegationsentscheidungen sind inhärent prompt-basiert — konsistent mit Architektur. Technische Erzwingung ist separates Feature (siehe Step-5-Risiko-Sektion). |

---

## Verification Checklist (nach allen Fixes)

1. [ ] `python scripts/sync.py --validate` → Exit Code 0, keine Errors
2. [ ] `python scripts/sync.py` auf Test-Projekt mit `roles: [orchestrator, developer, git]` → `planner` NICHT in Routing-Tabellen
3. [ ] `python scripts/sync.py` auf Test-Projekt mit `roles: [orchestrator, developer, git, planner]` → `planner` IN Routing-Tabellen
4. [ ] `role-defaults.yaml` → `planner.produces.plan.pipeline` = `"feature-lifecycle"` → keine Kopplungs-Warnung
5. [ ] `role-defaults.yaml` → `planner.produces` entfernt → Kopplungs-Warnung erscheint
6. [ ] Generierte plan-driven Section enthält nummerierte Validierungsschritte (kein reiner Freitext)
7. [ ] `parse_plan_ref("tests/fixtures/plan-with-stages.md")` → korrekte Stage→Step-Mappings
8. [ ] Planner-Template version auf `1.0.2` gebumpt
9. [ ] Orchestrator-Template version auf `7.8.0` gebumpt
10. [ ] Generierter Orchestrator-Prompt enthält „Plan-driven gate“-Block nach `{{PIPELINE_MATCH_TABLE}}`
11. [ ] Generierter Orchestrator-Prompt §6: „Complex feature“-Zeile referenziert „§2 plan-driven gate prüfen“
12. [ ] `config/role-defaults.yaml` planner `intent_keywords` enthält Verbformen: `plane`, `Plan erstellen`, `Umsetzungsplan erstellen`, `Implementierungsplan`
13. [ ] `sync.py --validate` nach Orchestrator-Template-Änderung → Exit Code 0, keine Parse-Fehler
14. [ ] Keine provider-spezifischen Änderungen in `scripts/lib/` oder `config/`

---

## Files Changed Summary

| Datei | Änderung | Typ |
|-------|----------|-----|
| `scripts/lib/delegation_table.py` | Zeile 39: Filter-Bedingung vereinfachen | Bugfix (1 Zeile) |
| `config/role-defaults.yaml` | planner-Eintrag: `produces:`-Block hinzufügen | Enhancement (+6 Zeilen) |
| `config/role-defaults.yaml` | planner-Eintrag: `intent_keywords` um Verbformen erweitern | Enhancement (+4 Zeilen) |
| `scripts/lib/pipelines.py` | `check_plan_producer_coupling()` — neue Funktion | Enhancement (~55 Zeilen) |
| `scripts/lib/pipelines.py` | `validate_pipelines()` — optionaler `roles_config`-Parameter | Enhancement (~3 Zeilen) |
| `scripts/lib/pipelines.py` | `parse_plan_ref()` — neue Funktion | Enhancement (~60 Zeilen) |
| `scripts/lib/pipelines.py` | `validate_plan_ref()` — neue Funktion | Enhancement (~55 Zeilen) |
| `scripts/lib/pipelines.py` | `_generate_pipeline_block` plan-driven-Sektion — refactored | Enhancement (~10 Zeilen geändert) |
| `agents/1-generic/planner.md` | Version 1.0.1 → 1.0.2; Persist-Schritt um `pipeline_stages`-Konvention ergänzt | Patch (+5 Zeilen) |
| `agents/1-generic/orchestrator.md` | Version 7.7.1 → 7.8.0; §2 plan-driven Gate einfügen; §6 „Complex feature“-Zeile präzisieren | Minor (+8 Zeilen) |
