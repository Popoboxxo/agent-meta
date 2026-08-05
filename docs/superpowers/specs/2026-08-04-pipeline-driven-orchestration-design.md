# Pipeline-Driven Orchestration: Config-Native Superpowers-Equivalent — Design

**Status:** Freigegeben (2026-08-05, nach Interview zur Klärung der Audit-Lücken)
**Kontext:** Ausgelöst durch Nachfragen zu PR #398 (`feat/planner-agent-and-cluster-cleanup`, `docs/superpowers/specs/2026-08-02-agent-orchestration-refinement-design.md`): der Nutzer wollte wissen, ob `planner` eine Pipeline nutzt — tut es nicht, sein 5-Schritt-Workflow ist Prosa im Agenten-Prompt. Das führte zur Entdeckung derselben Anti-Pattern in `feature.md` (hartkodierte 8-Schritt-Lifecycle-Choreografie, delegiert per `Agent`-Tool an 6 andere Rollen) und zu einem grundlegenden Architekturprinzip: **der Orchestrator ist der einzige Delegator; Pipelines sind seine einzige, deklarative Ablauf-Beschreibung — kein Agent choreografiert intern mehrere andere Agenten.**

Dieses Dokument spezifiziert die Umsetzung dieses Prinzips als vollständig konfigurationsgetriebene Erweiterung der bestehenden `quality_pipelines`-Engine (`config/role-defaults.yaml`, `scripts/lib/pipelines.py`), inklusive Admin-UI-Unterstützung, sodass neue Pipelines **ohne Code-Änderung** rein per YAML entstehen können — genau wie heute schon `standard-feature`/`quick-fix`/`bugfix`.

## Bezug zur Ursprungsspec

`docs/superpowers/specs/2026-08-02-agent-orchestration-refinement-design.md`, Entscheidung 1, verwarf direkte Superpowers-Skill-Integration ("zu viel Komplexität, Provider-Kopplung an Claude") und empfahl stattdessen: *"`planner` bekommt eigene, native, providerunabhängige Planungslogik."* Diese Spec ist die konsequente Fortsetzung dieser Empfehlung — **kein neuer Kurswechsel**, sondern die Verallgemeinerung: nicht nur `planner`, sondern jede mehrstufige Agenten-Choreografie (auch `feature`) wird nativ, providerunabhängig, deklarativ. Für Claude, das mit Superpowers bereits ein äquivalentes System hat, sind die neuen Pipelines standardmäßig **nicht** aktiv — kein Doppelbau, siehe Entscheidung 5.

## Ausgangslage — was bereits existiert

- `scripts/lib/pipelines.py`: `quality_pipelines`-Engine mit Stage-Modi `sequential`, `loop` (Generator/Critic, `max_iterations`), `parallel_group` (mehrere Agenten, verschiedene Teilaufgaben, gleichzeitig), `fanout` (ein Agent, N Instanzen), `conditional` (mit `condition`-Feld). Bereits provider-spezifische *Formatierung* (`_generate_pipeline_block` pro Provider), aber keine provider-spezifische *Aktivierung*.
- `.meta-config/project.yaml` kann Pipelines überschreiben/hinzufügen (`quality-pipelines.overrides`, `quality-pipelines.custom-pipelines`) — bereits vollständig config-getrieben, kein Code nötig für neue Pipelines heute schon (Voraussetzung für "einfach konfigurativ weitere Pipelines bauen" ist also größtenteils erfüllt; diese Spec erweitert nur die *Ausdruckskraft* der Stage-Modi).
- `agents/1-generic/feature.md`: 8-Schritt-Lifecycle (Branch→REQ→TDD→Dev→Validate→PR), `tools: [Bash, Read, Agent, TodoWrite]` — hat das `Agent`-Tool, delegiert intern an `git`, `requirements`, `tester`, `developer`, `validator`, `documenter`. Einziger generischer Agent mit echtem Multi-Agent-Delegationsrecht.
- `agents/1-generic/planner.md` (aus PR #398): 5 interne Reasoning-Schritte (Parse→Decompose→Estimate→Persist→Handoff) — **kein** Verstoß gegen das Prinzip, da `planner` selbst keine anderen Agenten per Tool-Call delegiert (Estimate-Referenz ist bewusst nur Text, kein Tool-Call). Bleibt als Ein-Agent-Rolle bestehen; nur der Estimate-Hop wird aus der Prosa in eine echte, optionale Pipeline-Stage verschoben (Entscheidung 6).
- `agents/1-generic/export-manager.md` + `.meta-config/export.yaml` (Schema-Mismatch mit dem, was `export-manager.md` erwartet — siehe Entscheidung 8) + `schemas/export-payload.schema.json`: bereits eine target-agnostische Export-Abstraktion (`markdown`, `confluence`, `jira-xray`, `notion`, `custom` via `skills-registry.yaml`), aber von keiner Rolle tatsächlich genutzt — `planner` schreibt direkt.
- `scripts/admin-server.py` + `docs/ui/admin-ui.html`: Admin-UI hat bereits eine `/pipelines`-Route mit vollem CRUD (`/api/pipelines` GET/PUT, `/api/pipelines/<name>` GET/PUT/DELETE), liest/schreibt `quality_pipelines` aus `role-defaults.yaml` direkt, mit Stage-Editor. Muss um die neuen Stage-Konzepte (Komposition, `plan-driven`) erweitert werden, sonst sind sie im Admin-UI unsichtbar/nicht editierbar.
- `config/project-config.schema.json`: JSON-Schema für IDE-Autocomplete auf `.meta-config/project.yaml` — muss bei jeder neuen Pipeline-Fähigkeit mitgezogen werden (siehe `.claude/rules/conventions.md` → "Adding a New Placeholder").

## Entscheidung 1: Pipeline-Komposition (`run_pipeline`)

Eine Stage kann eine andere Pipeline referenzieren, statt eines einzelnen Agenten:

```yaml
stages:
  - id: implement
    run_pipeline: feature-lifecycle
    # optional: Parameter-Weiterreichung an die referenzierte Pipeline
    with:
      plan_ref: "{{payload.plan_ref}}"
```

**Engine-Änderungen (`scripts/lib/pipelines.py`):**
- `validate_pipelines()`: Zyklenerkennung über den `run_pipeline`-Graphen (DFS mit Besuchs-Stack), Tiefenbegrenzung standardmäßig 4 Ebenen — pro Pipeline überschreibbar über ein optionales Feld `max_depth` (fehlt es, gilt der Default 4). Kein globaler Hard-Cap jenseits dessen; `max_depth` wird wie `agent` gegen `validate_pipelines()` geprüft (Pipeline mit `max_depth: 6`, deren tatsächliche Verschachtelung 7 erreicht, ist trotzdem ein Fehler).
- `_generate_pipeline_block()`: rendert eine referenzierte Pipeline als eingerückten Unterblock (Provider-Notation bleibt pro Format wie gehabt, nur rekursiv angewendet).
- Auflösung rein zur Sync-Zeit (Textgenerierung in den Agenten-Prompt) — keine Laufzeit-Rekursion im eigentlichen Sinn; der Orchestrator "sieht" beim Ausführen die vollständig entfaltete Stage-Liste.
- `orchestrator_roles = {"orchestrator", "feature"}` (Zeile 92, Zirkularitäts-Guard) wird auf `{"orchestrator"}` reduziert, sobald `feature` als Rolle entfällt (Entscheidung 2) — Ergänzung zur Migrationstabelle.

## Entscheidung 2: `feature.md` löst sich auf zu `feature-lifecycle`-Pipeline

Ersetzt den heutigen `feature`-Agenten durch eine Pipeline-Definition. **Klarstellung (Interview 2026-08-05):** `standard-feature` (`config/role-defaults.yaml:1386`, "Full feature lifecycle with TDD, review, and PR", `signal_keywords: [Feature implementieren, Feature bauen, neues Feature, Funktion bauen]`) ist inhaltlich bereits dieselbe Pipeline wie das hier neu beschriebene `feature-lifecycle` — kein neuer, parallel existierender Scope. Es wird **umbenannt und erweitert**, kein Alias, keine Koexistenz: `standard-feature` wird zu `feature-lifecycle`, die `signal_keywords` beider Definitionen werden vereinigt, die Stages unten ersetzen die heutigen `standard-feature`-Stages vollständig. Kein Breaking Change für Consumer-Projekte, da `standard-feature` ein intern in `role-defaults.yaml` verwalteter Default ist, keine extern versionierte Schnittstelle.

Die neue Pipeline bildet exakt ab, was `feature.md` heute in `{{#if DOD_...}}`-Blöcken hartkodiert:

```yaml
quality_pipelines:
  feature-lifecycle:
    description: Vollständiger Feature-Lifecycle mit optionalem Plan-Input, REQ, TDD, Review, PR
    signal_keywords: [Feature Lifecycle, komplexes Feature, Feature Pipeline]
    accepts_plan_ref: true          # neu — siehe Entscheidung 3
    stages:
      - id: branch
        agent: git
        task: Feature-Branch anlegen
        mode: sequential
      - id: requirement
        agent: requirements
        task: REQ-ID vergeben
        mode: conditional
        condition: { dod_flag: req-traceability }
      - id: tests
        agent: tester
        task: TDD Red Phase — Tests mit REQ-ID im Namen
        mode: conditional
        condition: { dod_flag: tests-required }
      - id: implement
        agent: developer            # Default; wird durch plan-driven überschrieben, falls payload.plan_ref gesetzt (Entscheidung 3)
        task: Implementierung
        mode: plan-driven
        plan-driven:
          fallback_agent: developer  # wenn kein Plan vorliegt
      - id: verify
        agent: tester
        task: Tests grün, keine Regression
        mode: conditional
        condition: { dod_flag: tests-required }
      - id: validate-and-document
        mode: parallel_group
        parallel_group:
          - agent: validator
            task: DoD-Check
          - agent: documenter
            task: CODEBASE_OVERVIEW aktualisieren
        condition: { dod_flag: codebase-overview }
      - id: commit
        agent: git
        task: 'Commit: feat([REQ-ID]): ... + PR'
        mode: sequential
    on_error: escalate_to_orchestrator
```

`agents/1-generic/feature.md` wird **gelöscht**. Migrationsfolgen (vollständige Liste, keine Auslassungen zulässig):

| Betroffene Stelle | Änderung |
|---|---|
| `config/role-defaults.yaml` → `roles.feature` | Eintrag entfernt (keine Rolle mehr) |
| `config/role-defaults.yaml` → `quality_pipelines.standard-feature` | durch `feature-lifecycle` ersetzt oder als Alias/Legacy-Eintrag belassen (Entscheidung offen, siehe Testing) |
| `agents/1-generic/_wf-orchestrator-reference.md` | Few-Shot-Zeile `Single Feature \| feature oder Pipeline: ...` → verweist nur noch auf die Pipeline, kein `feature`-Agent mehr als Option |
| `agents/1-generic/planner.md` | `<output_contract>` referenziert weiterhin `plan_ref` — Zielrolle ändert sich konzeptionell von "an `feature` übergeben" zu "an `feature-lifecycle`-Pipeline übergeben"; Wortlaut in Persona/Constraints prüfen |
| `.claude/rules/use-orchestrator.md`-Quelle (`rules/1-generic/use-orchestrator.md`) | "Plan Delegation"-Zeile (aus dem PR-#398-Fix-Wave) muss auf die Pipeline statt auf `feature` verweisen |
| `agents/1-generic/orchestrator.md` | dieselbe Anpassung für Opencode/Gemini-Pfad |
| `tests/test_opencode_agents.py` und alle anderen Tests, die `feature` als Rolle referenzieren | `feature` aus Rollenlisten entfernen, `feature-lifecycle`-Pipeline-Tests ergänzen |
| Intent-Tabelle (`scripts/lib/delegation_table.py`) | `feature`-Zeile entfällt automatisch (keine Rolle mehr in `role-defaults.yaml`). **Klarstellung (Interview 2026-08-05):** `delegation_table.py` wird erweitert, sodass Pipelines mit `signal_keywords` als eigene Zeilen in derselben Tabelle in `use-orchestrator.md` erscheinen (Spalte "Agent" zeigt dann `→ Pipeline: <name>` statt eines Rollennamens, Tier-Spalte bleibt leer/"pipeline") — ein Ort für alle Routing-Entscheidungen, keine separate Sektion. |
| `scripts/lib/viz.py:24,30` | Rollen-Liste und Abhängigkeitsgraph (`"feature": ["requirements", "validator", "developer", "tester", "git"]`) sind unabhängig von `role-defaults.yaml` hartkodiert für `docs/agent-graph.html`/`docs/agent-mindmap.md` — `feature`-Eintrag entfernen, sonst zeigt der generierte Graph nach der Migration eine tote Node. |
| `tests/test_opencode_agents.py:54` | `DELEGATING_ROLES = {"orchestrator", "feature", "agent-meta-manager"}` → `{"orchestrator", "agent-meta-manager"}`. |
| `docs/architecture/03-agent-roles.md` | Manuelle Doku, kein Build-Artefakt: Mermaid-Knoten `FEA[feature]` (Zeile 8) + Kanten (30-36) + Tabellen-Eintrag (43) + Sektion "feature vs. orchestrator" (72-82) entfernen/umschreiben. |
| GitHub-Issues/Docs, die `feature`-Agent referenzieren | manuell durchsuchen, nicht Teil des automatisierten Checks |

## Entscheidung 3: `mode: plan-driven`

Löst die vom Nutzer geforderte "mehrere verschiedene starke Agenten je nach Komplexität"-Anforderung — **kein neuer Ensemble-/Konsens-Mechanismus**, sondern: der Agent pro Schritt kommt zur Laufzeit aus der vom `planner` bereits vergebenen Rollen-Zuweisung (Spalte `Agent` in `planner-output-v1`), statt aus einem festen `agent:`-Feld in der YAML.

```yaml
- id: implement
  mode: plan-driven
  plan-driven:
    fallback_agent: developer   # wenn payload.plan_ref nicht gesetzt ist
    allowed_agents: [junior-developer, developer, senior-developer]  # Validierung — Plan darf keine anderen Rollen für diese Stage vergeben
```

**Auflösung:** Wenn `payload.plan_ref` gesetzt ist, liest die Stage die zu ihrer `id` passenden Plan-Zeilen (Matching über die `Agent`-Spalte gegen `allowed_agents`) und dispatcht an genau die dort genannte Rolle — `planner` hat die Komplexitätseinschätzung (junior/developer/senior) bereits beim Decompose-Schritt getroffen, keine doppelte Klassifikation nötig. Ohne `plan_ref`: `fallback_agent`.

**Fehlerfall (Interview 2026-08-05):** Ist `plan_ref` gesetzt, aber der Plan enthält keine Zeile für die aktuelle Stage-`id`, ist das **kein** stiller Fallback auf `fallback_agent` — der Orchestrator prüft das beim Dispatch der Stage (nicht die Pipeline-Engine bei der Sync-Zeit-Auflösung, da der Plan-Inhalt erst zur Laufzeit bekannt ist) und bricht mit einer expliziten Fehlermeldung ab, die den Nutzer auf die Lücke im Plan hinweist. Grund für Orchestrator statt Engine: `run_pipeline`/Stage-Auflösung passiert zur Sync-Zeit in den Prompt-Text, der tatsächliche Plan-Inhalt (welche Stage-IDs eine Zeile haben) ist aber erst zur Laufzeit bekannt — die Prüfung gehört an den Ort, der den Plan zur Laufzeit liest.

## Entscheidung 4: Neue Pipeline `concept-to-review`

Der vom Nutzer gewünschte Superpowers-äquivalente Ablauf, komplett aus bestehenden Rollen zusammengesetzt:

```yaml
quality_pipelines:
  concept-to-review:
    description: Konzept/Idee → Plan → Implementierung → Review, providerunabhängiges Superpowers-Äquivalent
    signal_keywords: [Konzept umsetzen, von Idee zu Code, vollständiger Workflow]
    providers: { default: active, exclude: [Claude] }   # Entscheidung 5
    stages:
      - id: scope
        agent: ideation
        task: Idee scopen
        mode: conditional
        condition: { payload_flag: needs_scoping }   # überspringen, wenn schon ein Konzept/REQ vorliegt
      - id: plan
        agent: planner
        task: Umsetzungsplan erzeugen
        mode: sequential
      - id: estimate
        agent: effort-estimator
        task: Aufwandsschätzung
        mode: conditional
        condition: { payload_flag: estimate_effort }   # Entscheidung 6
      - id: implement
        run_pipeline: feature-lifecycle
        mode: sequential
```

## Entscheidung 5: Provider-Aktivierung für Pipelines

Neues optionales Pipeline-Feld `providers`:

```yaml
providers:
  default: active | inactive
  include: [Provider, ...]   # nur zusammen mit default: inactive sinnvoll
  exclude: [Provider, ...]   # nur zusammen mit default: active sinnvoll
```

Fehlt das Feld: Pipeline ist überall aktiv (Rückwärtskompatibilität mit `feature-lifecycle`/`quick-fix`/`bugfix`, die das Feld nicht haben). `concept-to-review` nutzt `default: active, exclude: [Claude]` — Claude hat Superpowers bereits, kein Doppelbau (siehe Bezug zur Ursprungsspec).

**Auswertungsort (Interview 2026-08-05):** Die Filterung passiert in `scripts/lib/pipelines.py`, nicht in `sync.py` — `_generate_pipeline_block()` bekommt einen `provider`-Parameter und lässt Pipelines, für die der aufrufende Provider laut `providers`-Feld inaktiv ist, ausfallen (liefert keinen Block statt eines leeren). `sync.py` bleibt dünner Aufrufer, der `_generate_pipeline_block()` pro Provider-Lauf mit dem jeweiligen Providernamen aufruft — ein Ort für sämtliche Pipeline-Validierungs- und -Filterlogik (`available_roles`, Zyklenerkennung, `max_depth`, `providers`), konsistent mit `validate_pipelines()`.

## Entscheidung 6: Planner-Estimate wird optionale, echte Pipeline-Stage

`agents/1-generic/planner.md` wird vereinfacht: `## 3. Estimate effort` entfällt aus dem Workflow, die `**Estimated effort:**`-Zeile im `<output_contract>` wird zu `**Estimated effort:**  <nur wenn payload.estimate_effort — sonst Zeile weglassen>`. Die eigentliche Schätzung passiert als eigene, optionale Stage in `concept-to-review` (Entscheidung 4) — `planner` selbst delegiert nichts mehr, auch nicht textuell.

## Entscheidung 7: Zwischendokumente steuerbar (Pipeline-Default + Payload-Override)

Neues Stage-Feld `persist_artifact` (Default `true`, wenn nicht gesetzt — Rückwärtskompatibilität):

```yaml
- id: plan
  agent: planner
  persist_artifact: true   # Default für diese Stage
```

Laufzeit-Override: `payload.persist_artifacts: false` unterdrückt das Schreiben für den gesamten Pipeline-Lauf (z.B. wenn ein Plan nur für einen einzigen Implementierungsdurchlauf gebraucht wird und nicht dauerhaft im Repo/Wiki landen soll). Wirkt auf jede Stage, die `persist_artifact` unterstützt — Agenten-Prompts (z.B. `planner.md`) lesen `{{PERSIST_ARTIFACT_DEFAULT}}` als build-time-injizierten Default, der zur Laufzeit vom Payload-Flag überstimmt werden kann (dieselbe Zwei-Ebenen-Logik wie bei `{{DOD_...}}`-Flags heute schon).

**Registrierungsort (Interview 2026-08-05):** `{{PERSIST_ARTIFACT_DEFAULT}}` und `{{OUTPUT_TARGET_BLOCK}}` werden beide in `scripts/lib/config.py::build_variables()` registriert, analog zu den bestehenden `{{DOD_...}}`-Platzhaltern (`.claude/rules/conventions.md` → "Adding a New Placeholder" ist hier Pflichtschritt). `{{OUTPUT_TARGET_BLOCK}}` ist **kein** Platzhalter pro Artefakttyp, sondern ein generischer Mechanismus: `build_variables()` löst ihn pro produzierender Rolle anhand des in `output-targets.<artefakt-typ>` konfigurierten Eintrags auf (Artefakt-Typ ergibt sich aus der Rolle/Stage, die den Platzhalter referenziert) — eine Definition, parametrisiert über die Stage, kein Wildwuchs aus `{{OUTPUT_TARGET_BLOCK_PLAN}}`, `{{OUTPUT_TARGET_BLOCK_REQ}}` etc.

## Entscheidung 8: Output-Targets zweistufig — Build-Time-Injection statt generellem Export-Manager-Hop

**Problem:** Jedes Artefakt über `export-manager` zu routen kostet einen vollen Agenten-Hop (Kontext-Overhead) — unnötig für den Normalfall (eine Markdown-Datei oder ein einzelner MCP-Tool-Call).

**Lösung, zweistufig:**

1. **Einfache Targets** (Markdown-Datei, einzelner MCP-Call ohne Retry/Credentials-Logik): neuer Platzhalter `{{OUTPUT_TARGET_BLOCK}}`, zur Sync-Zeit aus `.meta-config/project.yaml` (neuer Block `output-targets`, siehe unten) aufgelöst und direkt in den Prompt der produzierenden Rolle injiziert — kein Extra-Agenten-Aufruf, exakt das Muster, das `planner`s duale Persistenz (Wiki vs. Flatfile) schon nutzt, nur generalisiert auf beliebige Targets inklusive Requirements-Tools.
2. **Komplexe Targets** (Confluence/Jira-Xray mit Credentials, Retry, Fallback-Kette): bleiben beim bestehenden `export-manager`-Hop — dafür ist er gebaut, der Overhead lohnt sich dort.

**Neuer Config-Block** (`.meta-config/project.yaml`):

```yaml
output-targets:
  plan:                          # Artefakt-Typ (entspricht Pipeline-Stage-Output)
    type: markdown | requirements-tool | export-manager
    # markdown:
    path: knowledge/wiki/plans/  # oder plan-<topic>.md im Root
    # requirements-tool (neu):
    mcp-server: reqogniloom      # Name aus config/mcp-registry.yaml
    mcp-tool: needs.create       # oder requirement.create
    # export-manager (für komplexe Targets, delegiert weiter):
    export-target: confluence
```

**`requirements-tool`-Target (neu):** generischer Typ für MCP-basierte Requirements-Backends (ReqFlow/ReqogniLoom, bereits per MCP in diesem Repo angebunden — `.claude/rules/mcp-reqflow.md`, `mcp-reqogniloom.md`). Die produzierende Rolle bekommt zur Sync-Zeit injiziert, *welchen* MCP-Tool-Call sie statt eines `Write` absetzen soll — kein Agenten-Hop, aber austauschbar zwischen Markdown und einem echten Requirements-Tool rein per Config-Änderung.

**Nebenfix:** `config/export.yaml` (Ist-Zustand: `architecture: {target: markdown, output_dir: ...}`) entspricht nicht dem Schema, das `export-manager.md` beschreibt (`default_target`, `targets.<name>.{enabled,format,credentials}`, `fallback.*`). **Klarstellung (Interview 2026-08-05):** Die Datei bleibt unter demselben Namen/Pfad bestehen (kein Umzug nach `.meta-config/project.yaml`), nur ihr Inhalt wird auf das `export-manager.md`-Schema migriert. Konkrete Zielform des bestehenden Eintrags:

```yaml
default_target: architecture
targets:
  architecture:
    enabled: true
    format: markdown
    output_dir: docs/adr/    # aus dem heutigen Eintrag übernommen
fallback:
  on_error: markdown
```

Alle heutigen Top-Level-Keys in `config/export.yaml` (nicht nur `architecture`) werden nach demselben Muster verlustfrei überführt — vollständige Ist-Liste vor Umsetzung gegen die tatsächliche Datei prüfen, nicht nur gegen dieses Beispiel.

**ReqFlow vs. ReqogniLoom (Interview 2026-08-05):** `config/mcp-registry.yaml` enthält aktuell nur einen Eintrag `reqogniloom:` (Zeile 164) — kein `reqflow:`. Die generierte Regel-Datei `.claude/rules/mcp-reqflow.md` ist damit Altlast aus einer früheren Config-Version, unabhängig von dieser Spec. Wird als Aufräum-Nebenfix in dieser Spec mitgezogen: `mcp-reqflow.md` wird beim nächsten `sync.py`-Lauf ohnehin nicht mehr regeneriert (kein Registry-Eintrag mehr) und kann als verwaiste Datei gelöscht werden. Kein neues Auswahlkonzept zwischen zwei Requirements-Backends nötig — `output-targets.<artefakt>.mcp-server` referenziert ausschließlich `reqogniloom`, validiert gegen `config/mcp-registry.yaml` analog zur `available_roles`-Prüfung bei Pipelines (neuer Testfall in "Testing").

## Entscheidung 9: Vollständig konfigurationsgetrieben — kein Code für neue Pipelines nötig

Explizite Anforderung: neue Pipelines (auch mit den neuen Stage-Modi `run_pipeline`/`plan-driven`) müssen sich **ausschließlich** über YAML definieren lassen, ohne `scripts/lib/pipelines.py` anzufassen — exakt wie `standard-feature`/`quick-fix`/`bugfix` heute. Konkret:

- Alle neuen Stage-Felder (`run_pipeline`, `plan-driven`, `providers`, `persist_artifact`) werden generisch in `validate_pipelines()`/`_generate_pipeline_block()` behandelt (Datenstruktur-getrieben, keine Sonderfälle pro Pipeline-Name).
- `config/project-config.schema.json` wird um alle neuen Felder erweitert (IDE-Autocomplete für `.meta-config/project.yaml` → `quality-pipelines.custom-pipelines.*`).
- Projektspezifische Pipelines bleiben über `.meta-config/project.yaml` → `quality-pipelines.custom-pipelines` möglich, exakt wie heute (keine Änderung an diesem Mechanismus nötig, nur an dem, was innerhalb einer Pipeline-Definition ausdrückbar ist).

## Entscheidung 10: Admin-UI-Unterstützung für die neuen Pipeline-Konzepte

Die bestehende `/pipelines`-Seite (`docs/ui/admin-ui.html`, `/api/pipelines`) editiert `quality_pipelines` bereits vollständig (Stage-Editor, Speichern via `PUT /api/pipelines`). Ohne UI-Erweiterung sind die neuen Stage-Modi zwar über die Rohdaten-Edit-Funktion erreichbar, aber nicht als First-Class-Konzept sichtbar:

- **Stage-Typ-Auswahl** im Editor bekommt `run_pipeline` und `plan-driven` als neue Optionen (neben `sequential`, `loop`, `parallel_group`, `fanout`, `conditional`) — jede mit eigenem Farb-Badge, konsistent mit dem bestehenden Farbschema pro Modus (bestehende Modi sind bereits farblich unterschieden, siehe `docs/ui/admin-ui.html`s Pipeline-Renderer).
- **Pipeline-Komposition sichtbar machen:** eine Stage mit `run_pipeline: X` zeigt einen expandierbaren Verweis auf Pipeline `X` (kein vollständiges Nested-Rendering nötig für v1 — ein Link/Badge "→ enthält Pipeline X" reicht, mit Klick zum Wechsel der Editor-Ansicht).
- **`providers`-Feld:** Checkbox-Liste (aktiv für: alle / bestimmte Provider) im Pipeline-Kopfbereich, analog zur bestehenden Provider-Auswahl an anderer Stelle im Admin-UI (Rollen-Aktivierung nutzt bereits ein ähnliches Muster).
- **`persist_artifact`:** Toggle pro Stage im Editor.

## Testing

- **Pipeline-Komposition:** Zyklustest (`A → run_pipeline: B → run_pipeline: A`) muss `validate_pipelines()` mit klarer Fehlermeldung abbrechen lassen; Tiefenlimit-Test (5 verschachtelte Ebenen → Fehler bei Ebene 5).
- **`mode: plan-driven`:** Test mit validem `plan_ref` (Agent-Zuweisung aus Plan wird respektiert), ohne `plan_ref` (Fallback greift), mit Plan-Zeile außerhalb `allowed_agents` (Validierungsfehler, kein stiller Fallback).
- **`feature-lifecycle`-Pipeline vs. altes `feature.md`-Verhalten:** Regressionstest — dieselben DoD-Flag-Kombinationen (REQ an/aus, Tests an/aus, CODEBASE_OVERVIEW an/aus) müssen dieselbe Stage-Aktivierung ergeben wie die alten `{{#if}}`-Blöcke in `feature.md`.
- **Provider-Aktivierung:** `concept-to-review` erscheint in generiertem Output für Opencode/Gemini, fehlt für Claude.
- **`output-targets` — `requirements-tool`:** Testprojekt mit `output-targets.plan.type: requirements-tool` → generierter `planner`-Prompt enthält den korrekten MCP-Tool-Call-Hinweis statt eines `Write`-Aufrufs.
- **`config/export.yaml`-Migration:** alte Einträge (`architecture`, `test-models`, etc.) nach der Schema-Migration weiterhin funktional (kein Datenverlust).
- **Admin-UI:** manueller Testlauf — neue Pipeline mit `run_pipeline`- und `plan-driven`-Stage über das UI anlegen, speichern, neu laden, Farb-Badges korrekt.
- **`sync.py --validate` und `consistency-check.py`** bleiben PASS über den gesamten Umbau.

## Migration von PR #398

PR #398 ist bereits gepusht (nicht gemerged). Diese Spec berührt zwei seiner Kern-Dateien erneut: `planner.md` (Entscheidung 6 vereinfacht den Workflow), `feature.md` (Entscheidung 2 löscht die Datei komplett). Empfehlung: eigener Branch von `feat/planner-agent-and-cluster-cleanup` (nicht von `main`, da `planner.md`/`feature.md` in ihrer PR-#398-Form dort noch nicht existieren) — PR #398 bleibt fokussiert und review-fähig, dieser Umbau landet als eigene, referenzierende PR obendrauf.

## Entscheidung 11: Neue `condition`-Typen `dod_flag` und `payload_flag` (Nachtrag, Interview 2026-08-05)

**Fund während der Planungsphase:** `mode: conditional` unterstützt in `scripts/lib/pipelines.py` bisher nur `condition: {type: agent_decision, agent: ...}` (einzige heutige Verwendung: `config/role-defaults.yaml:1609`, `se-termination`). Entscheidung 2 (`feature-lifecycle`) verwendet aber durchgängig `condition: {dod_flag: req-traceability}` etc., Entscheidung 4 (`concept-to-review`) verwendet `condition: {payload_flag: needs_scoping}` — beide Formen existieren im Code nicht. War weder in der ursprünglichen Spec noch im Audit-Abschnitt erfasst.

**`dod_flag` (Sync-Zeit):** Neuer `condition`-Typ neben `agent_decision`. `validate_pipelines()`/`_generate_pipeline_block()` prüfen zur Sync-Zeit, ob das benannte DOD-Preset-Flag (aus demselben `active_dod`-Dict, das `build_pipeline_variables()` bereits als Parameter erhält) aktiv ist — ist es inaktiv, wird die Stage vollständig aus dem generierten Block weggelassen (nicht nur textuell markiert), analog zum heutigen `{{#if DOD_...}}`-Verhalten in `feature.md`.

**`payload_flag` (Laufzeit):** Anders als `dod_flag` bleibt eine `payload_flag`-Stage im generierten Prompt-Text sichtbar (der Payload-Inhalt ist zur Sync-Zeit nicht bekannt) — der Orchestrator überspringt sie zur Laufzeit, wenn das benannte Flag im Payload fehlt oder `false` ist. Kein Engine-Codepfad nötig, nur eine dokumentierte Konvention im generierten Stage-Text (z.B. `**scope** — Conditional execution (payload_flag: needs_scoping):`).

Beide Typen sind Ergänzung zu Entscheidung 9 ("generisch, datengetrieben, keine Sonderfälle pro Pipeline-Name") — betreffen ausschließlich den bestehenden `conditional`-Modus, keine neuen Stage-Modi.

## Audit: Cross-Referenz-Prüfung (Ergebnis, geklärt im Interview 2026-08-05)

Nachträgliche Prüfung (2026-08-05) gegen den aktuellen Code-Stand deckte 12 Lücken auf, die die ursprüngliche Migrationstabelle (Entscheidung 2) und die übrigen Entscheidungen nicht abdeckten. Alle 12 sind mittlerweile in die jeweilige Entscheidung eingearbeitet:

| # | Lücke | Klärung | Wo eingearbeitet |
|---|---|---|---|
| 1 | `pipelines.py:92` `orchestrator_roles` hat `feature` hartkodiert | Auf `{"orchestrator"}` reduzieren | Entscheidung 1 |
| 2 | `viz.py:24,30` Agent-Graph kennt `feature` separat | Eintrag entfernen | Migrationstabelle, Entscheidung 2 |
| 3 | `test_opencode_agents.py:54` `DELEGATING_ROLES` enthält `feature` | Auf `{"orchestrator", "agent-meta-manager"}` reduzieren | Migrationstabelle, Entscheidung 2 |
| 4 | `docs/architecture/03-agent-roles.md` (manuelle Doku, Mermaid + Tabelle + Sektion) fehlte in der Migrationstabelle | Ergänzt | Migrationstabelle, Entscheidung 2 |
| 5 | `config/export.yaml`-Zielschema unklar | Datei bleibt, Inhalt migriert auf `export-manager.md`-Schema, Beispiel-Zielform dokumentiert | Entscheidung 8 |
| 6 | ReqFlow vs. ReqogniLoom Serverwahl ungeklärt | `reqflow` ist Altlast (kein Registry-Eintrag), `mcp-reqflow.md` wird gelöscht, kein Auswahlkonzept nötig | Entscheidung 8 |
| 7 | `{{PERSIST_ARTIFACT_DEFAULT}}`/`{{OUTPUT_TARGET_BLOCK}}` ohne Registrierungsort | Registrierung in `scripts/lib/config.py::build_variables()`, ein generischer Mechanismus mit Artefakt-Typ als Parameter statt eines Platzhalters pro Typ (folgt der bestehenden `{{DOD_...}}`-Konvention aus `.claude/rules/conventions.md` → "Adding a New Placeholder") | Entscheidung 7 |
| 8 | Provider-Filterlogik ohne festen Ort | In `pipelines.py::_generate_pipeline_block()` (Provider-Parameter), nicht in `sync.py` | Entscheidung 5 |
| 9 | `delegation_table.py` kennt nur Rollen, keine Pipelines | Pipelines erscheinen als eigene Zeilen in derselben Intent-Tabelle | Migrationstabelle, Entscheidung 2 |
| 10 | `standard-feature` vs. `feature-lifecycle` Koexistenz offen | Ersetzen/Umbenennen, kein Alias — `standard-feature` war inhaltlich bereits dieselbe Pipeline | Entscheidung 2 |
| 11 | `plan-driven`-Fehlerfall (Plan da, Stage-ID fehlt) ohne Ort | Orchestrator prüft beim Dispatch (Laufzeit), nicht die Pipeline-Engine (Sync-Zeit) | Entscheidung 3 |
| 12 | Tiefenlimit 4 Ebenen ohne Override | Pro Pipeline überschreibbar via `max_depth`-Feld | Entscheidung 1 |

**Zur Kenntnis, kein Blocker:** `agents/2-platform/` wurde auf `extends: "1-generic/feature` / `extends: "1-generic/planner` geprüft — keine Platform-Overrides für diese beiden Rollen gefunden, also keine verwaisten Composition-Dateien beim Löschen von `feature.md` zu erwarten.

## Out of Scope

- Vollständige Ensemble-/Judge-Panel-Stage (mehrere Agenten an *derselben* Aufgabe, dann Synthese/Abstimmung) — vom Nutzer explizit als "nicht gemeint" ausgeschlossen; `plan-driven` deckt den eigentlichen Bedarf (Komplexitätsstufen) bereits ab.
- Vollständige Ablösung von `export-manager` für komplexe Targets (Confluence/Jira-Xray) — bleibt Agenten-Hop, siehe Entscheidung 8.
- Migration bestehender Consumer-Projekte, die bereits eigene `custom-pipelines` mit altem Schema definiert haben — additive Erweiterung, keine Breaking Changes an bestehenden Feldern.
- Rückbau von Superpowers-Nutzung unter Claude — Claude behält Superpowers vollständig, die neuen Pipelines sind dort nur standardmäßig inaktiv, nicht verboten (Projekt kann sie über `providers.include` gezielt auch für Claude aktivieren, falls gewünscht).
