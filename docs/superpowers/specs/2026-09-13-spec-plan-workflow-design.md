# Nativer Spec/Plan-Workflow für agent-meta — Design-Spezifikation

> **Status: Design-Gate abgeschlossen (2026-09-13); Entscheidungen eingearbeitet.**
> Implementierungsplan liegt vor unter
> `docs/superpowers/plans/2026-09-13-spec-plan-workflow.md`. Der frühere Status
> „Entwurf — nicht implementiert“ (v2) ist damit überholt; die Implementierung selbst ist
> noch nicht erfolgt. Brainstormed 2026-09-13, überarbeitet 2026-09-13 (v2/v3/v4/v5).
> Dieses Dokument definiert einen *nativen* Prozess-Workflow (Spec → Plan → Execution) auf
> Feature-Ebene, vollständig abhängig von agent-meta-Bordmitteln (Rules, Rollen, Pipelines,
> Config, Sync). Superpowers (obra/superpowers) dient **nur als Referenz-Zielbild** — es wird
> nichts extern eingebunden und nichts blind kopiert.
>
> **Hinweis zur Ablage:** Dieses Design-Doc liegt bewusst noch unter der bestehenden Konvention
> `docs/superpowers/specs/`. Es ist damit letzter Nutzer der Altkonvention und definiert in
> §5/§10 das neue, neutrale Pfadschema (`docs/specs` + `docs/plans`). Kein Widerspruch, sondern
> der Migrationsanker (siehe §10.3).

## Revision v2 — eingearbeitete Review-Punkte

Concept-Review (CHANGES_REQUESTED) + Domain-Check (MAJOR_CHANGES). In dieser Fassung behoben:

| Punkt | Korrektur |
|---|---|
| **B1** | Consistency-Aktivierung war faktisch falsch → neuer Modus `--validate-spec-plan` analog `se_validate.py`, NICHT in `run_checks()` (§1.4, §7.3) |
| **B2** | DoD-Auflösung missverstanden (`resolve_dod` iteriert `full`-Preset-Keys) → Keys in `dod-presets.yaml` in `full` + relevante Presets + `dod`-Schema (§5.3) |
| **B3** | „`enabled:false` ⇒ No-op“ war mit `dod_flag` nicht erreichbar → `effective_enabled` EINMAL zentral, in Rule-Gate UND Pipeline-Gate (§5.4) |
| **M2** | Rule-Gate nur im `lazy`-Preset reicht nicht (`collect_rule_sources` globbt alle) → intrinsisches Gate an EINEM Choke-Point (§4.2) |
| **M1** | Ledger/Ownership/Barrieren duplizierten Bestand → Andocken an `orchestration.py`/`file_affinity.py`/`checkpoint.py`/`plan-driven` (§3.1) |
| **M3** | Orchestrator darf nicht direkt an `knowledge-indexer` → Routing über `knowledge-ingestor` bzw. `planner` selbst (§6, §8) |
| **M4** | Concept-Type: `Plan` bestätigen, `Spec` ergänzen (vier Stellen) → alle vier benannt (§6) |
| **M5** | Scenario-Pflicht fehlte → Scenario-Vorschlag mit `configs/` + `asserts/` (§12) |
| **M6** | Schema-Lücken → `systems-engineering` + `spec-plan-workflow` deklarieren, `concept-driven` ergänzen, DoD-Keys ins `dod`-Schema; Rollen-Version-Bumps (§5.2, §9). *(v4: `systems-engineering`-Teil ausgelagert, F1)* |
| **M4-cr** | Plan-Template ohne `pipeline_stages` → Pflichtsektion (§7.2, §7.3) |
| **M5-cr** | Klassifikation war ungekoppelt → S/M/L/XL-Mapping ergänzt (§2.1) |
| **M6-cr** | `docs/plans` kollidiert mit Bestand → Scan-Scope + Ignore/Legacy + Archiv nach `docs/plans/archive/` (§5.1, §8, §10.3) |
| **M3-cr** | „HARD GATE“ überzeichnet → Convention-boundary deklariert + Nicht-Pipeline-Lücke (§2.1) |
| **m2-cr** | `resolve_dod` iteriert nur `full`-Preset-Keys (§5.3) |
| **m3-cr** | Absenz-Semantik für `enabled` festgelegt (§5.4) |
| **m6-cr** | Stage-ID heißt `specify` (nicht `specific`) (§9) |
| **m2-dm** | A2A-`payload` ist `additionalProperties:true`; `requires_human_approval` vs. Pipeline-Gate abgegrenzt (§2.3) |

## Revision v3 — eingearbeitete Domänen-Re-Check-Punkte

| Punkt | Korrektur |
|---|---|
| **B3-Rest** | Synthetischer `spec-plan-enabled` erreichte die Render-Pfade nicht → Injektion **in `resolve_dod()` selbst** (Single Source of Truth); übersehene Call-Site **`agent_sync.py:607`** explizit benannt (§5.4) |
| **R1/2** | Call-Site-Zahl korrigiert: **6** statt 5; `rules.py:282` als Embed-Kanal-Aufruf markiert (keine Doppelzählung) (§4.2) |
| **R2/4** | `resolve_spec_plan_enabled(..., *, dod=None)` reicht bereits aufgelöstes DoD-Dict durch; keine doppelte `resolve_dod`-Auflösung in `_build_dod_variables()` (§5.3/§5.4) |
| **R3** | `check_spec_plan_workflow(..., *, agent_meta_root=None)` + Auflösung via `resolve_agent_meta_root(project_root)` analog `checkpoint.py:274` (§7.3) |
| **R4** | Rule-Gate **fail-closed**: `collect_rule_sources(..., *, config)` verpflichtend, Gate intern berechnet; vergessener Call-Site = harter `TypeError` statt stiller Aktivierung (§4.2) |
| **R5** | `spec-plan-workflow` in `_MAPPING_BLOCKS` (`tests/test_config_null_blocks.py:27-45`) aufnehmen (§12). *(v4: Range auf `:27-66` korrigiert, F12)* |
| **Naming** | Handler-Konvention wie `se_validate.py`: `MODE = "validate-spec-plan"`, `validate_spec_plan`, `_handle_validate_spec_plan` (§1.4/§7.3) |

## Revision v4 — Entscheidungen offene Fragen (2026-09-13)

Alle 12 in v3 noch offenen Fragen (§13) sind verbindlich entschieden und in die berührten
Abschnitte eingearbeitet. Kurzformat (Details in §13):

| # | Entscheidung |
|---|---|
| **F1** | `systems-engineering`-Schema: **eigenes Folge-Issue**, nicht in diesem Vorhaben (Ausnahme von M6; §5.2/§10.2/§13) |
| **F2** | `okf.auto-index`/`auto-log`: **verdrahten** (real wirksam; steuern das Auto-Schreiben/Aktualisieren von `index.md`/`log.md`; `false` ≠ fehlende Dateien) in diesem Vorhaben (§6.2/§8/D8) |
| **F3** | Rule-Gate-Ort: Erweiterung **`config/rules-presets.yaml`** um die preset-unabhängige Top-Level-Sektion `rule-gates` (keine `config/rule-gates.yaml`) (§4.2/D6) |
| **F4** | `external-system-override`: **Info-Keys + Skip** — keine erzwungene Integration (§6.1/§6.3) |
| **F5** | `plan-complete`-Merge-Erkennung: **rein manuell**, keine Provider-Abstraktion (§8/§10.2) |
| **F6** | `orchestration.py`-Verdrahtung: **nur Graph-Validator** (`FanoutPlan`/`validate_plan`), `execute_plan` out-of-scope (§3.1/§7.3/D2) |
| **F7** | „Architectural“: **qualitatives Zusatzkriterium** unabhängig von der Dateizahl (§2.1) |
| **F8** | DoD-Flag-Namen `spec-plan-required`/`spec-plan-traceability` + synthetisch `spec-plan-enabled`: **bestätigt** (§5.3/§5.4) |
| **F9** | `variables.PROJECT_STRUCTURE`: **in diesem Vorhaben nachziehen** (`docs/specs`/`docs/plans`/`docs/spikes`) (§10.3) |
| **F10** | Spikes: **`explorer`-Spike-Modus** (read-only, Empfehlung, Wegwerf-Code) (§2.1/§2.2/§9) |
| **F11** | Archivierung: **agentbasiert** (`documenter`/`knowledge-ingestor`); Sync-Schritt bleibt Nicht-Ziel (§8) |
| **F12** | `--validate-spec-plan`: **in CI + Szenario**, **no-op bei `enabled:false`** (§7.3/§12) |

## Revision v5 — Concept-Review CHANGES_REQUESTED (2026-09-13)

Concept-Re-Review (CHANGES_REQUESTED) eingearbeitet. Details in den genannten Abschnitten:

| Punkt | Korrektur |
|---|---|
| **RVW-S1** | Falschbehauptung „`docs/specs` wird beim Sync gescaffoldet“ entfernt → `paths.specs`/`paths.spikes` (und `paths.plans`, falls fehlend) werden bei `effective_enabled=true` durch einen **neuen Sync-Scaffold-Schritt** angelegt (analog KE-Scaffolder `sync_knowledge_engine`, inkl. `.gitkeep`); `variables.PROJECT_STRUCTURE` scaffolder **nicht** (§5.1, §10.3, §12.3) |
| **RVW-S2** | F2-Semantik präzisiert: `okf.auto-index`/`auto-log` steuern das **automatische Schreiben/Aktualisieren** von `index.md`/`log.md`; `false` ⇒ keine Auto-Writes, Dateien werden vom KE-Scaffolder weiterhin angelegt und agent-driven gepflegt (`false` ≠ fehlende Dateien) (§6.2, §8) |
| **RVW-S3** | Falsche `--validate-se`-Prämisse entfernt: `--validate-spec-plan` kommt in **denselben CI-Template-Job wie der bestehende Sync-Check** (`github-actions-sync-check.yml`, real nur `sync.py --dry-run --check`); No-op bei `enabled:false`, Exit 0 (§7.3, §12.3) |
| **RVW-S4** | Scenario-ID fixiert auf **`50-spec-plan-workflow`** (höchste real vergebene ID `49-hacs-entity-naming`) (§12.3) |
| **RVW-S5** | `execute_plan` in §3.1-Tabelle als „nur Referenz; out-of-scope, F6“ markiert (§3.1) |
| **MINOR 7** | Prosa in §5.3 an die Preset-Tabelle angeglichen (alle Presets genannt); „Concept-Type `Plan` fehlt“ → „`Plan` bestätigen, `Spec` ergänzen“ (§5.3, §6.1) |
| **R3** | `SPEC_PLAN_WORKFLOW_ENABLED` (und `SPEC_PLAN_SPECS_DIR`/`SPEC_PLAN_PLANS_DIR`) werden an den drei Registrierungsstellen registriert und mindestens in `orchestrator.md` als Conditional genutzt (§10.1, §5.4) |

---

## 1. Problem, Zielbild, Nicht-Ziele, Abgrenzung zu SE (a)

### 1.1 Problem

agent-meta hat für **große** Vorhaben eine belastbare SE-Kaskade (V-Modell: Requirements/
Architektur, `systems-engineering`, aktuell `enabled:false` — `.meta-config/project.yaml:12-13`).
Für die **Feature-Ebene** fehlt dagegen ein durchgängiger, erzwingbarer Weg:

- `ideation` liefert ein Konzept, `concept-specifier`/`concept-architect` liefern eine Spec,
  `planner` liefert einen Plan — aber es gibt **keinen harten Übergang** von „Idee“ zu „Spec“
  und **keinen Zwang** von „approvte Spec“ zu „Plan“ (kein Master-Gate).
- Es existiert **keine Plan-Qualitätsnorm** (Header, File-Structure-Map, bite-sized TDD-Tasks,
  No-Placeholder, Traceability).
- Es existiert **kein Recovery-Modell** (Ledger) und keine Isolation, die mit dem
  Worktree-Verbot vereinbar ist.
- Die bestehende Doku-Konvention (`docs/superpowers/specs|plans`, `docs/plans` inkl. `archive/`,
  `docs/spikes`) ist **informell** — Pfade sind nicht konfigurierbar, nicht im Schema,
  `variables.PROJECT_STRUCTURE` listet sie nicht (`.meta-config/project.yaml:176-189`).
  `docs/plans/README.md:1-11` dokumentiert bereits eine gelebte, aber unverbindliche Konvention.

### 1.2 Zielbild

Ein **abschaltbarer, nativer Prozess** mit drei Bausteinen, ISO-agent-meta übersetzt:

| Superpowers-Baustein | agent-meta-Übersetzung |
|---|---|
| brainstorming | `ideation` + `concept-specifier/architect`, **Klassifikation** (Spike/Bounded/Architectural), **Approval-Gate**, Einzelfragen, 2–3 Optionen mit Trade-offs, Design-Doc, Self-Review, User-Review, **danach zwingend → Plan** |
| writing-plans | `planner` mit striktem Plan-Header, File-Structure-Map, bite-sized TDD-Tasks, Interfaces (consumes/produces), No-Placeholder, Self-Review |
| execution | `orchestrator`-Pipeline: **frischer Subagent pro Task** + Review, **Ledger** zur Recovery, agent-meta-konforme Isolation (kein Worktree — §3) |

### 1.3 Nicht-Ziele

- **Kein** externer Pack, **keine** externe Abhängigkeit, **kein** Vendor-Lock-in.
- **Kein** Parallel-System zu DoD/Consistency/Sync/Pipeline/Orchestrierung — Ausbau der
  Bestandsgrundideen (explizit: `orchestration.py`, `file_affinity.py`, `checkpoint.py`).
- **Keine** Implementierung durch dieses Dokument (kein Code, keine Rules/Templates/Config).
- **Keine** Massen-Umstellung bestehender `docs/superpowers/*`- oder `docs/plans/*`-Artefakte.

### 1.4 Abgrenzung zu SE (verbindlich, Entscheidung 7)

| Achse | SE-Kaskade | Spec/Plan-Workflow (neu) |
|---|---|---|
| Ebene | Requirements/Architektur (V-Modell L0–Ln) | Feature-/Change-Ebene |
| Master-Switch | `systems-engineering.enabled` (`project.yaml:12-13`) | `spec-plan-workflow.enabled` (neu) |
| Artefakte | L0–L3, ADR, VV, Traceability (`SE/`, s. `se_output`) | Spec-Doc + Plan-Doc + Ledger |
| Validierung | eigenständiger Modus `--validate-se` (`sync.py:147`, Dispatch `:282`) → `scripts/lib/se_validate.py:28 MODE`, `:31-53 validate_se_cascade(project_root, config, log)` → `scripts/lib/consistency/se_cascade.py:146` | **eigener Modus** `--validate-spec-plan` → `scripts/lib/spec_plan_validate.py` (`MODE = "validate-spec-plan"`, `validate_spec_plan(project_root, config, log)`, `_handle_validate_spec_plan`) → `scripts/lib/consistency/spec_plan.py` (Begründung §7.3) |
| Rollen | SE-eigene Rollen (`se-component-requirements`) | bestehende Concept-/Planer-/Entwickler-Rollen |

**Übergabepunkte:** SE → Feature, wenn ein Architecture Element in konkrete Feature-Specs
zerfällt (Spec referenziert die SE-Artefakt-ID). Feature → SE, wenn ein Feature als
architektur-relevant eingestuft wird (`Architectural`, §2.1): dann optional SE-Aufstieg,
aber **kein** Auto-Start der SE-Kaskade. Beide Switches bleiben unabhängig; SE bleibt
`enabled:false` unberührt.

---

## 2. Konzeptuelles Modell (b)

### 2.1 Klassifikation jeder Anfrage + Gekoppeltes Task-Size-Routing

Jede Feature-Anfrage wird **vor** jeder Implementierung klassifiziert. Die Klassifikation wird
an das **bestehende S/M/L/XL-Routing** gekoppelt (`agents/1-generic/orchestrator.md:76-85`) —
damit sind S und L nicht mehr undefiniert:

| Task-Size (orchestrator.md:78-83) | Klasse | Route | Artefakt |
|---|---|---|---|
| **S** (≤2 Dateien) | *(Workflow übersprungen)* | direkt `junior-developer` | keines |
| **M** (3–8 Dateien) | **Bounded** | `concept-specifier` → `planner` | Spec + Plan |
| **L** (9–20 Dateien) | **Bounded** (mit Review-Loop) | `concept-specifier` + `concept-reviewer` → `planner` | Spec + Plan |
| **XL** (>20 Dateien) | **Architectural** | `concept-architect` → `concept-specifier` → `planner` | Design + Spec + Plan |
| *(Recherche, keine Prod.-Änderung)* | **Spike** | `explorer` (**Spike-Modus**, F10) / `ideation` | Spike-Doc (`docs/spikes/YYYY-MM-DD-issue-<n>-<topic>-spike.md`) |

**Architectural — qualitatives Zusatzkriterium (F7, entschieden 2026-09-13):** Die Zuordnung
`XL → Architectural` ist **nicht** exklusiv an `>20 Dateien` gebunden. Eine Anfrage ist
**zusätzlich und unabhängig von der Dateizahl** als `Architectural` einzustufen, sobald eines
der folgenden Kriterien zutrifft: **öffentliche Schnittstellen/Contracts** betroffen,
**Datenmodell/Schema** betroffen oder **mehr als eine Subsystem-/Komponentengrenze**
überschritten. Damit ist Cross-Cutting-Impact klassifizierbar, ohne die Dateizahl im Voraus zu
kennen; die Dateizahl bleibt als zusätzliches Signal erhalten.

**Approval-Gate — bewusst als Convention boundary deklariert (M3-cr):** Der bestehende
Pipeline-Approval-Mechanismus rendert **nur eine Prompt-Zeile**
(`scripts/lib/pipelines.py:38-45` `_stage_requires_approval`, Rendering `:734-738`) und wirkt
**nur für Pipeline-Stages**. Er ist eine *Convention boundary* gegen akzidentellen Missbrauch,
keine *Security boundary* (Terminologie:
`.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary`).
Konsequenzen explizit:

- Der Gate greift **nur**, wenn die Anfrage über die erweiterte `concept-driven-dev`-Pipeline
  läuft. **Ad-hoc-Dispatches sowie `quick-fix` (`role-defaults.yaml:2401`) und `bugfix`
  (`:2419`) haben keine Classify-/Approve-Stage** — dort ist der Gate rein regelbasiert.
- **Gegenmaßnahme:** Die Classify-/Gate-Pflicht wird zusätzlich als Orchestrator-Regel
  verankert (`rules/1-generic/use-orchestrator.md:19` + orchestrator-Prompt), damit auch
  Nicht-Pipeline-Anfragen in die Classify-Route gezwungen werden. Das bleibt Konvention, nicht
  technische Durchsetzung — explizit kein Security-Anspruch.

Fragen werden **einzeln** gestellt (nicht als Fragenkatalog), Solutions als **2–3 Ansätze mit
Trade-offs**. Design wird abschnittsweise abgenommen (`agents/1-generic/ideation.md:47-60`).

### 2.2 Phasen und Phasen-Übergänge

```
Anfrage
  └─ classify via S/M/L/XL   (S → direkt; M/L → Bounded; XL → Architectural; offen → Spike)
        ├─ Spike  → explorer (Spike-Modus, F10: read-only, billig untersuchen,
        │            Empfehlung + Wegwerf-Code-Markierung) / ideation → Spike-Doc → STOP (kein Plan)
        └─ Bounded/Architectural
              └─ SPEC (design/spec-doc) → Self-Review → user/concept-reviewer
                    └─ [Approval-Gate: explizite Freigabe]  (Pipeline requires_approval, §2.1)
                          └─ PLAN (writing-plans) → Self-Review
                                └─ EXECUTION: Task n (frischer Subagent)
                                       → Review → Ledger/Checkpoint → Task n+1
                                              └─ Abschluss → Auto-Index → Auto-Archiv
```

Zwingend: Nach freigegebener Spec **muss** ein Plan entstehen (kein Direkteinstieg in Code).

### 2.3 Übersetzung nach agent-meta (orchestrator-first, Pipeline, A2A, Rollen)

- **Einstieg:** `orchestrator` dispatcht Phasen über die bestehende Pipeline-Mechanik
  (`config/role-defaults.yaml`, `quality_pipelines`), nicht über einen neuen Dispatcher.
- **Pipelines:** `concept-driven-dev` (`role-defaults.yaml:2475`, Stage `explore` →
  **`specify`** → `review` → `implement` → `validate`, Loop über `concept-reviewer`, max 3) und
  `feature-lifecycle` (`:2344`, `accepts_plan_ref:true` `:2354`, Stage `implement` ist
  `plan-driven` `:2375-2382`) sind die Anknüpfungspunkte. Erweiterung statt Neubau.
- **A2A (korrigiert, m2-dm):** `payload` ist im Handoff-Schema **`additionalProperties:true`**
  (`schemas/a2a-handoff.schema.json:80-89`). `spec_ref`/`task_id`/`ledger_ref` sind damit
  **ohne Schema-Erweiterung zulässig** (nur `tier_override` ist dort explizit typisiert). Zu
  unterscheiden:
  - `requires_human_approval` (`:124-128`) ist die **A2A-Ebene** (Prompt-Enforcement pro
    Handoff, „downstream agent MUST pause“).
  - Das **Pipeline-Approval-Gate** (`pipelines.py:38-45/734-738`) ist die **Pipeline-Ebene**
    (Stage-gating, eine gerenderte Zeile).
  Beide sind unabhängig und werden hier nicht vermischt.
- **Rollen:** keine neue Rolle. Erweiterung der bestehenden (`ideation`, `concept-architect`,
  `concept-specifier`, `concept-reviewer`, `planner`) + `orchestrator`-Wiring (§9).

---

## 3. Zentraler Konflikt: Worktree-Isolation vs. agent-meta (M1)

Superpowers-Execution nutzt **Worktree-Isolation** pro Task. agent-meta **verbietet** das hart:

- `rules/1-generic/no-worktree-isolation.md:1-4`: „Niemals das Argument `isolation: "worktree"`
  beim Spawnen von Subagenten verwenden“ — Agenten schreiben sonst in
  `.claude/worktrees/agent-<id>/` → fehlgeleitete Dateien und Datenverlust.
- AGENTS.md-Regel „No Worktree Isolation“ (Kernregel, nicht lazy, `rules-presets.yaml:106-108`).

### 3.1 Ersatz durch Andocken an Bestandsinfrastruktur (statt Neuerfindung)

Statt Ledger/Ownership/Barrieren neu zu bauen, werden die **vorhandenen** Grundideen genutzt:

| Bedarf | Bestandsbaustein | Andockpunkt |
|---|---|---|
| Task-Graph, Barrieren, parallel/sequential/fanout | `scripts/lib/orchestration.py` — `FanoutPlan`, `FanoutTask`, `validate_plan`, `execute_plan` (nur als Referenz; `execute_plan` out-of-scope, F6) (Modul-Doc `:1-24`) | Plan-Tasks → `FanoutTask(task_id, target_agent, prompt, files_touched, dependencies)` (`:79-97`) |
| Datei-Überlappung | `scripts/lib/file_affinity.py:173 check_file_overlap`; `scripts/lib/orchestration.py:309 check_plan_file_overlap` | Ownership-Disjunktheit prüfen vor `parallel_group` |
| Zyklus-/Deadlock-Erkennung | `orchestration.py` Dependency-Edges (`dependencies`, „cycle/deadlock detection input“ `:86-88`) | Plan-Task-Abhängigkeiten |
| Recovery/Checkpoints | `scripts/lib/checkpoint.py:263 CheckpointStore`, `save_checkpoint :349`; `BarrierEntry.checkpoint_ref` (`orchestration.py:135`, z.B. `.meta-viz/checkpoints/...`) | Task-Fortschritt an bestehende Checkpoints binden |
| Plan-Frontmatter → Stage-Mapping | `scripts/lib/pipelines.py:379 parse_plan_ref`, `:444 validate_plan_ref`, Rendering `:862 pipeline_stages` | `planner`-Template erzeugt `pipeline_stages` (Pflicht, §7.2) |
| Orchestration-Loop | `config/role-defaults.yaml` `quality_pipelines`, `plan-driven`-Stage (`:2375-2382`) | Execution-Phase |

**Härtungspunkt (explizit benannt, F6):** `scripts/lib/orchestration.py` ist derzeit **nicht
in `sync.py` verdrahtet** — nur Tests und `scripts/lib/consistency/fanout_contracts.py` nutzen
es. Genau das ist die zu härtende Grundidee: der Workflow verlangt, `FanoutPlan`/`validate_plan`
als **Plan-Validator** in den Orchestrator-Pfad (bzw. in `--validate-spec-plan`, §7.3)
einzubinden, statt daneben eine eigene Barrieren-Logik zu erfinden. **F6 (2026-09-13):** Die
Verdrahtung umfasst **nur den Graph-Validator**; `execute_plan` bleibt **out-of-scope** und
wird als eigenes Folge-Issue geführt.

**Ledger (Entscheidung D2):** Ledger = **Plan-Datei selbst** (Checkboxen + `pipeline_stages`
im Frontmatter) **plus** Recovery-Anbindung an `CheckpointStore`/`BarrierEntry.checkpoint_ref`.
Kein neues Ledger-Format; Checkbox-Zustand ist die menschliche Sicht, der Checkpoint die
maschinenlesbare Recovery-Quelle.

### 3.2 Adaption

1. **Frischer Subagent pro Task** — frischer Kontext, Task-ID + Spec-/Plan-Referenz +
   exakte Datei-Ownership.
2. **Explizite Datei-Ownership** pro Task im Plan (`Files:`-Block, vgl. realer Plan-Header
   `docs/superpowers/plans/2026-08-05-pipeline-engine-core.md:32-33`).
3. **Barrier-Gruppen über `check_file_overlap`** — nur ownership-disjunkte Tasks parallel;
   `max-parallel-agents` (`project.yaml:266`) bleibt Obergrenze.
4. **Repo-Containment** (`project.yaml:358-359`) bleibt unangetastet; Schreiben nur im
   Projektroot + `.tmp/`.

**Trade-off:** Wir verlieren die physische Worktree-Isolation. Gewonnen wird Konformität mit
Repo-Containment/Guard und Vermeidung des bekannten Datenverlust-Antipatterns. Ausgleich:
Ownership + Barrieren + Checkpoint-Ledger statt Isolation (D3, §11).

---

## 4. Native Regeln (c)

Neue Rules unter `rules/1-generic/*` als **plain Markdown ohne Pflicht-Frontmatter**
(`rules/1-generic/*` plain Markdown; Delivery `scripts/lib/rules.py`, keine Registry).

| Datei (Vorschlag) | Zweck | Trigger |
|---|---|---|
| `rules/1-generic/spec-plan-workflow.md` | **Master-Rule**: Phasen, S/M/L/XL↔Klassen-Mapping, Approval-Gate, Spec-Template, Approval-Marker, SE-Abgrenzung | jede Feature-/Change-Anfrage |
| `rules/1-generic/brainstorming-gate.md` | Klassifikation, Gate, Einzelfragen, 2–3 Optionen + Trade-offs, abschnittsweise Abnahme | vor Spec-Erstellung, Ziel/Aufwand unklar |
| `rules/1-generic/writing-plans.md` | strikter Plan-Header + `pipeline_stages`, File-Structure-Map, bite-sized TDD-Tasks, Interfaces, No-Placeholder, Self-Review | Übersetzung approvte Spec → Plan |
| `rules/1-generic/plan-ledger.md` | Execution: frischer Subagent/Task, Review, Ledger + Checkpoint-Recovery, Ownership/Barrieren, Worktree-Verbot-Adaption | bei Plan-Ausführung |

### 4.1 Geplante `rules-presets.yaml`-Einträge (`lazy`-Preset, analog SE-Rules `:162-175`)

```yaml
# in presets.lazy:
spec-plan-workflow:
  channel: skill
  skill-description: "Use when a feature-level request needs spec→plan→execution with an approval gate — classification, spec authoring, SE boundary."
brainstorming-gate:
  channel: skill
  skill-description: "Use before any feature implementation to classify Spike/Bounded/Architectural and enforce the no-implementation-without-approval gate."
writing-plans:
  channel: skill
  skill-description: "Use when turning an approved spec into a plan — required header, file-structure map, bite-sized TDD tasks, interfaces, no-placeholder self-review."
plan-ledger:
  channel: skill
  skill-description: "Use when executing a plan task-by-task — fresh subagent per task, review, ledger/checkpoint recovery, ownership/barrier isolation (no worktree)."
```

Projekt-Override weiter über `rules:`-Block (`project.yaml:346-355`).

### 4.2 Rule-Gate an EINEM Choke-Point (M2, B3)

**Problem (verifiziert):** `collect_rule_sources()` (`scripts/lib/rules.py:127-159`) globbt
**alle** `rules/1-generic/*.md` und liefert sie in **jedem** Preset aus (`default`/`minimal`/
`silent` eingeschlossen). Eine `requires-flag`-Angabe **nur im `lazy`-Preset** genügt daher
**nicht**. `collect_rule_sources` hat **6** Call-Sites:
`rules.py:282` (**zugleich der Embed-Kanal-Aufruf** aus `sync_embedded_rule_files`,
`rules.py:241-266`), `rules.py:370`, `agent_sync.py:129`, `agent_sync.py:190`,
`context.py:1133`, `sync_pipeline.py:555`. (Die Kennzeichnung von `rules.py:282` als
Embed-Kanal-Aufruf vermeidet die Doppelzählung — derselbe Call-Site, kein siebter.)

**Gewählter Mechanismus — intrinsisches Gate im Choke-Point `collect_rule_sources` (fail-closed):**

1. Neue zentrale Helper-Funktion
   `resolve_spec_plan_enabled(config, agent_meta_root, *, dod=None) -> bool` ist
   **Single Source of Truth** (§5.4).
2. `collect_rule_sources(agent_meta_root, platforms, *, config: dict)` — **`config` ist
   verpflichtend**; das Gate wird **intern** aus `resolve_spec_plan_enabled` berechnet
   (Zuordnung der gated Stems in `config/rules-presets.yaml`, F3). Ein vergessener Call-Site
   ist damit ein **harter `TypeError`** — kein Default, der gated Rules still aktiv ließe
   (**fail-closed**). Wird `config=None` explizit übergeben, werden gated Rules
   konservativ **nicht** ausgeliefert (fail-closed) statt aktiviert.
3. Die betroffenen Stems werden nicht im Preset, sondern in einer neuen **preset-unabhängigen
   Top-Level-Sektion** in `config/rules-presets.yaml` deklariert (F3 — **keine** neue Datei
   `config/rule-gates.yaml`), z. B.:
   `rule-gates: {spec-plan-workflow: {requires: spec-plan-workflow.enabled}}`, damit das Gate
   **preset-unabhängig** gilt.
4. Damit sitzt das Gate an genau einem Punkt, den **alle 6 Call-Sites** (inkl. Embed-Kanal)
   gemeinsam nutzen.

**Alternative (schwächer, nur Defense-in-Depth):** SE-Präzedenzfall mit
`{{#if SPEC_PLAN_WORKFLOW_ENABLED}}` im Rule-Body und Aufnahme der Variable in die
Conditional-Liste (`scripts/lib/variables.py:228-231`). Das entfernt zwar den Body-Inhalt,
**verhindert aber nicht** die Erzeugung der `SKILL.md`-Datei bzw. den `name`+`description`-
Eintrag im System-Prompt bei `channel: skill`. Deshalb primär die intrinsische
Source-Filterung (Punkte 2/3), die Body-Conditional nur als Defense-in-Depth.

---

## 5. Config- und Schema-Design (d)

### 5.1 Projekt-Config (`.meta-config/project.yaml`)

```yaml
spec-plan-workflow:
  # enabled bewusst OHNE Schema-Default im Top-Level-Block (Absenz-Semantik §5.4):
  # fehlt der Key, greift die DoD-Preset-Kopplung. Expliziter bool gewinnt immer.
  enabled: true
  paths:
    specs: docs/specs               # NEUTRAL Default; wird bei effective_enabled=true via Sync-Scaffold angelegt (R1)
    plans: docs/plans               # bereits vorhanden (docs/plans/README.md)
    spikes: docs/spikes             # wird bei effective_enabled=true via Sync-Scaffold angelegt (R1)
    legacy:                         # weiter LESBAR, nicht zwangs-migriert
      - docs/superpowers/specs
      - docs/superpowers/plans
  scan:
    include: ["*.md"]               # Glob-Scope (§7.3); Bestandsdateien ohne Template
    changed-files-only: true        # teuer zu validieren → Default nur geänderte
  index:
    mode: knowledge-engine          # knowledge-engine | file-index | off
    fallback-index: docs/INDEX.md   # nur für mode: file-index
  archive:
    mode: ask                       # auto | ask | off
    agent: documenter               # documenter | knowledge-ingestor (KE-Route, M3)
    trigger: plan-complete          # alle Checkboxen + gemergt
    target: docs/plans/archive      # bestehende Konvention (docs/plans/README.md:5-7)
  external-system-override:         # ersetzt KE-Indexierung durch fremdes System
    enabled: false
    system: ""
    note: ""
```

**M6-cr — Kollision mit Bestand:** `docs/plans/` existiert bereits (inkl. `archive/`, siehe
`docs/plans/README.md:1-11`), ebenso `docs/superpowers/*` und `docs/spikes/`. Der Scan-Scope ist
deshalb explizit: nur Dateien, die dem Template-Namensmuster entsprechen
(`YYYY-MM-DD-<topic>-design.md`, `YYYY-MM-DD-<topic>.md`, `*-spike.md`) **und** per
`scan.changed-files-only`/`changed_files` im aktuellen Diff liegen. Bestandsdateien ohne
Template sind **Legacy** (WARNING, nicht ERROR).

**Scaffolding (RVW-S1, präzisiert):** `paths.specs` und `paths.spikes` (sowie `paths.plans`,
falls noch nicht vorhanden) werden bei `effective_enabled=true` durch das neue Modul
`scripts/lib/spec_plan_scaffold.py` angelegt; die Call-Site liegt im Sync-Pipeline-Schritt
`scripts/lib/sync_pipeline.py:785-795` — analog dem KE-Scaffolding
(`scripts/lib/knowledge.py` `sync_knowledge_engine:100`, `_KNOWLEDGE_GITKEEP_SUBDIRS:90`,
inkl. `.gitkeep` pro Verzeichnis). Bei `effective_enabled=false` ist der Schritt ein No-op.
**Nicht** zuständig ist `variables.PROJECT_STRUCTURE` (`.meta-config/project.yaml:176-189`):
Das ist reiner Placeholder-Text für den Kontext und hat **keinen** Scaffolding-Effekt.

### 5.2 Schema-Ausschnitt `config/project-config.schema.json` (Draft-07, analog `knowledge-engine`)

```json
"spec-plan-workflow": {
  "type": "object",
  "description": "Native feature-level spec→plan→execution workflow (opt-in). No-op when effective_enabled=false.",
  "properties": {
    "enabled": { "type": "boolean" },
    "paths": {
      "type": "object",
      "properties": {
        "specs":  { "type": "string", "default": "docs/specs" },
        "plans":  { "type": "string", "default": "docs/plans" },
        "spikes": { "type": "string", "default": "docs/spikes" },
        "legacy": { "type": "array", "items": { "type": "string" },
                    "default": ["docs/superpowers/specs", "docs/superpowers/plans"] }
      },
      "additionalProperties": false
    },
    "scan": {
      "type": "object",
      "properties": {
        "include": { "type": "array", "items": { "type": "string" }, "default": ["*.md"] },
        "changed-files-only": { "type": "boolean", "default": true }
      },
      "additionalProperties": false
    },
    "index": {
      "type": "object",
      "properties": {
        "mode": { "type": "string", "enum": ["knowledge-engine", "file-index", "off"],
                  "default": "knowledge-engine" },
        "fallback-index": { "type": "string", "default": "docs/INDEX.md" }
      },
      "additionalProperties": false
    },
    "archive": {
      "type": "object",
      "properties": {
        "mode": { "type": "string", "enum": ["auto", "ask", "off"], "default": "ask" },
        "agent": { "type": "string", "enum": ["documenter", "knowledge-ingestor"],
                   "default": "documenter" },
        "trigger": { "type": "string", "enum": ["plan-complete"], "default": "plan-complete" },
        "target": { "type": "string", "default": "docs/plans/archive" }
      },
      "additionalProperties": false
    },
    "external-system-override": {
      "type": "object",
      "properties": {
        "enabled": { "type": "boolean", "default": false },
        "system":  { "type": "string",  "default": "" },
        "note":    { "type": "string",  "default": "" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

Wichtig (m3-cr): Der Block hat **kein Top-Level-`default`** und `enabled` hat **kein**
`default`. `load_config` (`scripts/lib/config.py:221-273`) injiziert keine Schema-Defaults;
`fill_defaults` (`:882-958`) materialisiert nur Top-Level-Keys **ohne Punkt** sowie `dod.*`
bei `full`/`strict` — verschachtelte `spec-plan-workflow.*`-Defaults werden also **nie**
automatisch geschrieben. Damit bleibt „explizit gesetzt“ vs. „abwesend“ unterscheidbar.

**M6 — Schema-Lücken (im selben Vorhaben zu schließen; Ausnahme `systems-engineering`, F1):**

- `systems-engineering` ist **gar nicht** deklariert; nur das Top-Level
  `additionalProperties:true` (`project-config.schema.json:2105`) toleriert es
  (belegt auch `tests/test_config_null_blocks.py:33`). → **bewusst ausgelagertes
  Out-of-Scope-Follow-up (F1, eigenes Folge-Issue)**; die Schema-Deklaration wird **nicht**
  in diesem Vorhaben nachgezogen (§10.2/§13).
- `spec-plan-workflow` explizit deklarieren (oben).
- `dod-preset`-Enum (`:575-582`) fehlt `concept-driven` (existiert real in
  `dod-presets.yaml:81-93`) → additiv ergänzen.
- Neue DoD-Keys fehlen im `dod`-Block (`additionalProperties:false`, `:635`) → dort ergänzen
  (§5.3).
- Auto-generierte Enums (`properties.roles.items.enum` aus `config/role-defaults.yaml` via
  `scripts/lib/schema.py:33`; Provider-Enums aus `config/provider-capabilities.yaml`)
  **nicht manuell** editieren.

### 5.3 DoD-Kopplung (B2, m2-cr)

**Korrektur:** `resolve_dod()` (`scripts/lib/dod.py:50-100`) iteriert die Keys des
aufgelösten `full`-Presets (`:87`) — das Fallback-Dict (`:75-84`) ist **toter Code** (nur
relevant, wenn `full` in der Datei fehlt), ebenso das ungenutzte `_DOD_FIELD_DEFAULTS`
(`scripts/lib/config.py:117-126`; `grep` findet nur die Definition). Neue Flags dürfen daher
**nicht** nur dort ergänzt werden.

Neue Keys gehören in `config/dod-presets.yaml` — in **alle** Presets der folgenden Tabelle
(`full`, `standard`, `rapid-prototyping`, `spec-optional`, `spec-driven`, `concept-driven`,
`spec-certified`), nicht nur in die werte-tragenden:

| Preset | `spec-plan-required` | `spec-plan-traceability` |
|---|---|---|
| full | false | false |
| standard | false | false |
| rapid-prototyping | false | false |
| spec-optional | false | false |
| spec-driven | true | true |
| concept-driven | true | false |
| spec-certified | true | true |

Zusätzlich: Keys in `dod.properties` im Schema (`project-config.schema.json` ab `:588`,
`additionalProperties:false` bei `:635`). `_build_dod_variables()`
(`scripts/lib/config.py:1627+`) wird um die Ableitung von `SPEC_PLAN_WORKFLOW_ENABLED` ergänzt
(§5.4). **R2/4:** Die Helper-Signatur lautet
`resolve_spec_plan_enabled(config, agent_meta_root, *, dod=None)`; `_build_dod_variables()`
reicht das bereits aufgelöste `dod_resolved` (`config.py:1647`) per `dod=` durch — **keine
zweite `resolve_dod`-Auflösung**. Präzedenz bleibt `dod > dod-preset > full`
(`dod-presets.yaml:2`).

**F8 (entschieden 2026-09-13):** Die Flag-Namen sind **final bestätigt**:
`spec-plan-required` und `spec-plan-traceability` (DoD-Preset-Keys) sowie der von
`resolve_dod()` injizierte synthetische Key `spec-plan-enabled` (`dod_flag`). Die Nomenklatur
ist konsistent zu `se-required`; keine Umbenennung.

### 5.4 `effective_enabled` — Single Source of Truth (B3/m3-cr, v3 nachgeschärft)

**Korrektur (v3, B3-Rest):** `dod_flag`-Conditionals lesen **nur** `active_dod`
(`scripts/lib/pipelines.py:728` — `active_dod.get(cond["dod_flag"], True)`; fehlt der Key,
bleibt die Stage **aktiv**). Der in `_build_dod_variables()`
(`scripts/lib/config.py:1627-1672`) injizierte synthetische Key erreicht die **realen
Render-Pfade nicht**, weil diese `resolve_dod` **frisch** aufrufen:

- `agents/1-generic/orchestrator.md:41` = `{{PIPELINE_DETAIL_BLOCKS}}`; `inject_pipeline_blocks`
  wird in `scripts/lib/agent_sync.py:608` aufgerufen — mit einem frischen
  `resolve_dod(config, agent_meta_root)` in **`agent_sync.py:607`** (diese Call-Site war in v2
  übersehen).
- `scripts/lib/sync_pipeline.py:663` übergibt ebenfalls ein frisches `resolve_dod(...)` an
  `sync_pipeline_detail_files`.

Folge: Bei `enabled:false` würden die Approve-/Spec-Stages trotzdem im Orchestrator-Prompt
erzeugt (Default `True`).

**Gewählter Mechanismus — Injektion in `resolve_dod()` selbst (single source of truth):**

```
resolve_spec_plan_enabled(config, agent_meta_root, *, dod=None) -> bool:
    block = config.get("spec-plan-workflow")
    1. isinstance(block, dict) and "enabled" in block  → bool(block["enabled"])          # explizit
    2. sonst (dod or resolve_dod(config, agent_meta_root)).get("spec-plan-required", False) # Preset
    3. sonst False

# resolve_dod() (scripts/lib/dod.py:50-100) ruft am Ende resolve_spec_plan_enabled(...)
# mit dem bereits aufgelösten Ergebnis auf und setzt:
#     resolved["spec-plan-enabled"] = effective_enabled
```

Weil `resolve_spec_plan_enabled` im selben Modul `dod.py` liegt, entsteht **kein
Import-Zyklus**. **Jeder** Aufrufer von `resolve_dod` erhält den synthetischen Key automatisch
— insbesondere die beiden übersehenen Render-Call-Sites `agent_sync.py:607` und
`sync_pipeline.py:663` sowie `sync_pipeline.py:149` und `config.py:1647`.

**Verworfene Alternative:** Wrapper `resolve_dod_with_spec_plan()` und manuelle Umstellung
aller Call-Sites — genau das war die v2-Lücke (eine vergessene Call-Site genügt). Die Injektion
in `resolve_dod` selbst ist unumgehbar und damit fail-safe.

Absenz-Semantik (m3-cr): Ein **explizit gesetztes** `enabled` (bool) gewinnt immer;
abwesender Key fällt auf die DoD-Preset-Kopplung zurück. Da weder `load_config` noch
`fill_defaults` verschachtelte Defaults injizieren (§5.2), ist „abwesend“ stabil erkennbar.

**F8 (entschieden 2026-09-13):** Der synthetische Render-Key heißt unverändert
`spec-plan-enabled` (Backing-Feld `spec-plan-required`, §5.3). Keine Umbenennung.

Einspeisung aus **einer** Berechnung:

1. **Rule-Gate:** `resolve_spec_plan_enabled` (ggf. mit durchgereichtem `dod`) → internes Gate
   in `collect_rule_sources` (§4.2).
2. **Pipeline-Gate:** Stages nutzen `condition: {dod_flag: spec-plan-enabled}` — der Key kommt
   aus `resolve_dod` und ist damit in **jedem** Render-Pfad vorhanden
   (`pipelines.py:728`). **Kein zweiter Evaluator, kein separater Wrapper.**
   `_build_dod_variables()` (`config.py:1647`) setzt zusätzlich
   `variables["SPEC_PLAN_WORKFLOW_ENABLED"]` für Agent-Templates (Registrierung in den drei
   Stellen R3, §10.1; ebenso `SPEC_PLAN_SPECS_DIR`/`SPEC_PLAN_PLANS_DIR`, §6.4) und ruft
   `resolve_dod` **nicht erneut** auf, sondern reicht `dod_resolved` per `dod=dod_resolved`
   durch (R2/4).
3. Für den Laufzeit-Fall nutzt der Orchestrator zusätzlich `payload_flag` (bestehend).

Damit steuert **eine** Helper-Funktion Rule-Delivery, Pipeline-Stages und Agent-Templates;
`enabled:false` ist sauber no-op.

---

## 6. Knowledge-Engine-Integration + Fallback (e)

Ausgangslage (verifiziert): KE aktiv (`project.yaml:14-27`); `knowledge/wiki/index.md:116-119`
Abschnitt `## Plans`, `knowledge/wiki/log.md:28-29` Einträge; `planner` schreibt bei aktiver KE
nach `knowledge/wiki/plans/<topic>.md` (`agents/1-generic/planner.md:38-41`).

### 6.1 Concept-Types `Plan` und `Spec` — vier Stellen (M4)

`Plan` **existiert bereits** in `knowledge/schema.md:34` (dort als einzige der vier Stellen);
der Concept-Type `Spec` fehlt dagegen überall. Die Absicherung von `Plan` (**bestätigen**) und
die Ergänzung von `Spec` müssen **alle vier** Stellen treffen:

| Stelle | Datei:Zeile | Änderung |
|---|---|---|
| OKF-Schema | `knowledge/schema.md:27-34` | `Plan` bestätigen, `Spec` ergänzen (additiv erlaubt laut `:43`) |
| Domain-Presets | `scripts/lib/knowledge.py:13-21 DOMAIN_CONCEPT_TYPES["internal-docs"]` | `plan`, `spec` ergänzen |
| Allowed-Types | `.meta-config/project.yaml:20-25 okf.allowed-types` | `Plan`, `Spec` ergänzen |
| Scaffolder-Ordner | `scripts/lib/knowledge.py:90-97 _KNOWLEDGE_GITKEEP_SUBDIRS` | `wiki/plans` (+ ggf. `wiki/specs`) ergänzen — sonst legt der Scaffolder sie nicht an |

**F4-Präzisierung (2026-09-13):** Diese vier Stellen sind die Voraussetzung für die
**KE-Route**. Ist `external-system-override.enabled:true` (§6.3), entfallen die KE-Schreibpfade
— die Deklarationen bleiben dennoch gültig und werden nicht übersprungen (sie sind kein
Integrationsversprechen, nur Schema-/Scaffolder-Grundlage).

### 6.2 Auto-Index/Auto-Log (M4, F2)

`okf.auto-index`/`auto-log` stehen im Schema (`project-config.schema.json:1689-1696`), werden
aber in `scripts/` **nirgends referenziert** (verifiziert). **Entscheidung F2 (2026-09-13, RVW-S2):**
Die Flags werden **in diesem Vorhaben verdrahtet** und real wirksam gemacht. Verbindliche
Semantik — bei aktiver KE **und** `index.mode: knowledge-engine` steuern sie das
**automatische Schreiben/Aktualisieren** von Einträgen in `knowledge/wiki/index.md`
(auto-index) bzw. `knowledge/wiki/log.md` (auto-log):

- **`true`** → der Workflow schreibt/aktualisiert die Einträge nach Spec-/Plan-Erstellung
  automatisch über den Rollenpfad (§6.4/§8).
- **`false`** → **keine** automatischen Schreibzugriffe; die Dateien werden vom KE-Scaffolder
  weiterhin **angelegt** und von Agenten gepflegt (`planner` bzw. `knowledge-ingestor` →
  `knowledge-indexer`). `false` bedeutet **nicht**, dass die Dateien fehlen.

Die Verzweigung ist damit auch im `true`-Fall **funktional unterscheidbar, ohne einen neuen
Sync-seitigen Writer**: Bei `true` ist der **regel-/agentenbasierte** Auto-Update-Pfad aktiv
(Orchestrator/`planner` bzw. `knowledge-ingestor`→`knowledge-indexer` schreiben/aktualisieren
die Einträge; dokumentiert in `rules/1-generic/spec-plan-workflow.md` und
`agents/1-generic/knowledge-ingestor.md`); bei `false` wird dieser Pfad übersprungen — die
Dateien bleiben gescaffoldet und werden nur auf explizite Anweisung gepflegt.

Der Zielzustand ist damit **nicht mehr** „wirkungslos“; bis zur Implementierung der
Verdrahtung ist der Bestand agent-driven.

### 6.3 Index-Modus + Fallback

| `index.mode` | Bedingung | Verhalten |
|---|---|---|
| `knowledge-engine` | `ke.enabled:true` **und** `external-system-override.enabled:false` | Spec/Plan zusätzlich als Wiki-Seiten (`Spec`/`Plan` → `topics/`/`plans/`) |
| `file-index` | KE aus **oder** Override an | Artefakte bleiben unter `paths.*`; Index in `index.fallback-index` |
| `off` | explizit | kein Index |

**Fallback explizit:** `external-system-override.enabled:true` ⇒ keine KE-Schreibpfade; nur
wenn `mode: knowledge-engine` gesetzt ist, aber KE aus/Override an, fällt der Workflow auf
`file-index` zurück (kein stiller Datenverlust).

**`external-system-override` — Info-Keys + Skip (F4, entschieden 2026-09-13):** Der Block
markiert **ausschließlich**, dass die KE-Indexierung und der Auto-Index übersprungen werden
(`enabled:true` ⇒ keine KE-Schreibpfade, `file-index`-Fallback greift). `system` und `note`
sind **reine Informationsfelder** — es gibt **keine** erzwungene Integration, keine
Konfiguration und keine Verifikation eines externen Systems. Der Workflow schreibt nicht in
das externe System und verlangt keinen Nachweis dessen.

### 6.4 Index-Pflege — Rollenvertrag (M3)

`agents/1-generic/knowledge-indexer.md:16` sagt: **„wird NUR von anderen Knowledge-Agenten
delegiert, nie direkt vom Nutzer angesprochen.“** Der Orchestrator darf daher **nicht** direkt
an `knowledge-indexer` delegieren. Entscheidung:

- **Plan (KE aktiv):** `planner` pflegt `index.md`/`log.md` **selbst** — das ist das
  bestehende Muster (`planner.md:40`) und vermeidet einen Agenten-Hop.
- **Spec (KE aktiv):** Route über `knowledge-ingestor` (der seinerseits an
  `knowledge-indexer` delegiert), weil Spec-Erzeugung nicht beim `planner` liegt.
- **Archiv/Index ausserhalb der KE:** `documenter` (kein Knowledge-Agent, direkt delegierbar).

Variablen-Basis wie bei KE: `scripts/lib/config.py:1581-1587` → analog
`SPEC_PLAN_WORKFLOW_ENABLED`, `SPEC_PLAN_SPECS_DIR`, `SPEC_PLAN_PLANS_DIR` (Registrierung der
Conditional-Variablen in den drei Stellen: §10.1/R3).

---

## 7. Spec-/Plan-Templates + Validierung (f)

### 7.1 Spec-Template (Pflichtsektionen)

```
# <Topic> — Spec
> Status: Entwurf | APPROVED (Datum)        # Approval-Marker (maschinenlesbar)
## Problem / Ziel / Nicht-Ziele
## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)
## Datenfluss
## Acceptance Criteria (nummeriert, testbar)
## Offene Fragen + Risiken
## Trace-Anker: spec-id: SPEC-<slug>        # Plan referenziert diesen Wert
```

Vorbild: `docs/superpowers/specs/2026-09-10-live-progress-channel-design.md:1-25`.

### 7.2 Plan-Template (Pflicht) — inkl. `pipeline_stages` (M4-cr)

Der real verifizierte Header (`docs/superpowers/plans/2026-08-05-pipeline-engine-core.md:1-27`)
wird normiert. **Neu verpflichtend:** das `pipeline_stages`-Frontmatter — ohne es fällt ein
templatekonformer Plan zur Laufzeit in den `fallback_agent`
(Rendering/Doku: `pipelines.py:862`, `planner.md:43-47`).

```
# <Topic> Implementation Plan
> Status: geplant | IN PROGRESS | complete
**Goal:** …            **Architecture:** …      **Tech Stack:** …
**Spec:** <pfad zur Spec>       # verpflichtend
## Global Constraints
## File Structure
- Modify/Create: <pfad> — Zweck
---
pipeline_stages:                # PFLICHT, sonst fallback_agent
  implement: 3
---
### Task <id>: <titel>
**Files:** Modify/Create + Test          # Ownership (Barrieren-Input)
**Interfaces:** Produces/Consumes
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit
```

### 7.3 Validierung — eigener Modus statt `run_checks()` (B1)

**Korrektur (faktisch):** `run_checks()` wird von `scripts/lib/cli_commands.py:171` mit
`agent_meta_root` aufgerufen; die Artefakte liegen aber im Consumer-`project_root`. Zudem gibt
`load_project_vars()` ein **Set von Variablennamen** aus dem `variables:`-Block zurück
(`scripts/lib/consistency/placeholders.py:178-186`) — keine Werte, keine Pfade. Damit sind
`SPEC_PLAN_WORKFLOW_ENABLED`/Pfade in `run_checks()` **nicht** verfügbar.

**Lösung analog SE-Vorbild (gleiche Symbol-Konvention wie `se_validate.py`):**

1. Neuer eigenständiger Modus `--validate-spec-plan` in `sync.py` (Registrierung `:147`,
   Dispatch `:282`) → Handler `scripts/lib/spec_plan_validate.py` mit denselben Symbolen wie
   `scripts/lib/se_validate.py`: `MODE = "validate-spec-plan"`,
   `validate_spec_plan(project_root, config, log) -> int`,
   `_handle_validate_spec_plan(ctx)` (analog `:28`, `:31-53`, `:98-108`).
2. Der Handler lädt die Config aus dem **Consumer-Projekt** selbst
   (`.meta-config/project.yaml` via `load_config`), weil `spec_plan.py` `project_root`
   und `config` als Argumente erhält.
3. `scripts/lib/consistency/spec_plan.py` implementiert die Checks und lädt die Config
   **selbst**, wenn kein `config` übergeben wurde (Config-Loader nötig) — dadurch ist das
   Modul auch standalone testbar.
4. **Nicht** in `run_checks()` einhängen (`scripts/consistency-check.py:138`) — das bleibt
   der agent-meta-interne Quell-Check über `agents/`, nicht der Consumer-Artefakt-Check.
5. **CI + Szenario (F12, entschieden 2026-09-13; RVW-S3):** Der Modus `--validate-spec-plan`
   wird in **denselben CI-Template-Job wie der bestehende Sync-Check** aufgenommen
   (`docs/guides/ci/github-actions-sync-check.yml`; real enthält der Job nur
   `sync.py --dry-run --check` — es gibt dort **keinen** `--validate-se`-Step, die frühere
   Formulierung „neben `--validate-se`“ war falsch) und im Scenario (§12.3) verankert. Bei
   `effective_enabled=false` ist der Modus ein **No-op** (`check_spec_plan_workflow` liefert
   früh `[]`, §10.1) — Exit-Code 0.

**`agent_meta_root` im Validator (R3):** `check_spec_plan_workflow` braucht `agent_meta_root`,
um `resolve_spec_plan_enabled`/`resolve_dod` (DoD-Presets liegen im agent-meta-Repo, **nicht**
im Consumer) korrekt auszuwerten. Auflösungspfad explizit:
`resolve_agent_meta_root(project_root)` — dasselbe Muster wie
`scripts/lib/checkpoint.py:274`; der Handler reicht das aufgelöste Root durch.

Signatur:

```python
def check_spec_plan_workflow(
    project_root: Path,
    config: dict | None = None,          # None → lädt <project_root>/.meta-config/project.yaml
    *,
    agent_meta_root: Path | None = None, # None → resolve_agent_meta_root(project_root)
    changed_files: set[str] | None = None,
) -> list[Finding]:
    """Checks: required sections (inkl. pipeline_stages), no-placeholder,
    spec↔plan↔task↔test traceability, approval markers, ledger checkbox format.
    Effective activation via resolve_spec_plan_enabled(config, agent_meta_root)."""
```

| Check | Inhalt | Severity-Logik |
|---|---|---|
| `spec_plan_required_sections` | Pflichtsektionen (§7.1/§7.2) **inkl. `pipeline_stages`** | ERROR bei `spec-plan-required` |
| `spec_plan_no_placeholder` | `TODO`, `TBD`, `...`, `<platzhalter>`, leere Interfaces | ERROR |
| `spec_plan_traceability` | `Spec:`-Referenz existiert; Task-ID ↔ Spec-Anker; Testname ↔ Task | ERROR nur bei `spec-plan-traceability:true`, sonst WARNING |
| `spec_plan_approval_marker` | `Status: APPROVED` vorhanden, bevor Plan Tasks hat | ERROR |
| `spec_plan_ledger_format` | Checkboxen + `Status:` konsistent | WARNING |
| `spec_plan_plan_graph` | **Nur Graph-Validator:** `FanoutPlan`/`validate_plan` gegen Task-`Files`/`Dependencies` (F6) | ERROR bei Zyklus/Overlap im `parallel_group` |

**F6 (entschieden 2026-09-13):** In den Validator-Pfad wird **nur der Graph-Validator**
(`FanoutPlan`/`validate_plan`) eingebunden; `execute_plan` bleibt **out-of-scope** und wird als
eigenes Folge-Issue geführt (§3.1/D2).

**Rules-Validierung (Lücke):** `consistency-check.py` scannt `rules/` **nicht**
(`collect_agent_files:106` nur `agents/`; Rules nur indirekt via
`check_changelog_mentions_new_files:205-207`). Vorschlag: `check_rule_docs(root)` +
Preset-Kreuzcheck (jede `rules-presets.yaml`-Referenz hat eine Datei und umgekehrt) als
separate Ergänzung — nicht Teil des Consumer-Modus.

---

## 8. Auto-Index + Auto-Archiv (g)

**Auto-Index (agenten-basiert, M3-konform; F2 verdrahtet):** `okf.auto-index`/`okf.auto-log`
steuern das **automatische Schreiben/Aktualisieren** von `knowledge/wiki/index.md`/`log.md`
nach Spec-/Plan-Erstellung (§6.2, F2): bei `true` aktualisiert der Workflow die Einträge über
den folgenden Rollenpfad automatisch; bei `false` gibt es **keine** automatischen
Schreibzugriffe — die Dateien werden vom KE-Scaffolder weiterhin angelegt und von Agenten
(`planner` bzw. `knowledge-ingestor` → `knowledge-indexer`) gepflegt. `false` heißt **nicht**,
dass die Dateien fehlen.

- KE aktiv + `index.mode:knowledge-engine`: Plan → `planner` pflegt `index.md`/`log.md`
  selbst; Spec → `knowledge-ingestor` (delegiert intern an `knowledge-indexer`).
- `file-index`: `planner`/`documenter` schreiben `index.fallback-index`.
- **Kein** direkter Orchestrator-Dispatch an `knowledge-indexer` (`:16`).

**Auto-Archiv:** Trigger `archive.trigger: plan-complete` = **alle Checkboxen gesetzt** und
Plan **gemergt**. Ziel ist `docs/plans/archive` (bestehende Konvention,
`docs/plans/README.md:5-7`).

- **Merge-Erkennung rein manuell (F5, entschieden 2026-09-13):** Der Orchestrator/das Team
  bestätigt den Merge-Status, bevor archiviert wird. Es gibt **keine** automatische
  Merge-Erkennung und **keine** Provider-Abstraktion (provider-agnostisch nicht nötig;
  `GIT_PLATFORM: GitHub`, `project.yaml:158`). Checkbox-Stand und Merge-Bestätigung sind die
  einzigen Trigger.
- **Agentbasiert bestätigt (F11, entschieden 2026-09-13):** Die Archivierung erfolgt durch
  einen Agenten (`archive.agent`: `documenter` Default, KE-Route `knowledge-ingestor`). Ein
  **Sync-Schritt** zur Archivierung bleibt explizit **Nicht-Ziel**.
- `auto` → `orchestrator` delegiert an `archive.agent` (`documenter` Default, KE-unabhängig;
  bei KE-Route `knowledge-ingestor`) — verschiebt Spec+Plan, loggt.
- `ask` → Rückfrage; erst nach Zustimmung archivieren.
- `off` → nichts.

---

## 9. Rollen-/Template-Änderungen + Pipeline-/Orchestrator-Wiring (h)

Bestehende Rollen erweitern, keine neuen. **Rollen-Version-Bumps verpflichtend** (Frontmatter
`version`; bei `2-platform`-Overrides zusätzlich `version` + `based-on` aktuell halten) —
siehe `rules/2-platform/agent-meta-conventions.md:60-68` und §12.

| Rolle | Änderung | Datei-Referenz |
|---|---|---|
| `ideation` | S/M/L/XL↔Klassen-Mapping + Gate-Anbindung | `agents/1-generic/ideation.md:47-73` |
| `explorer` | **Spike-Modus (F10):** expliziter Modus für billige Untersuchung — Befunde + Empfehlung berichten, Wegwerf-Code als solchen markieren, strikt read-only (keine Schreibrechte) | `agents/1-generic/explorer.md` |
| `concept-architect` | Design-Doc als Spec-Input; Trace-Anker | `agents/1-generic/concept-architect.md` |
| `concept-specifier` | Spec-Template (§7.1) + Approval-Marker + Trace-Anker | `agents/1-generic/concept-specifier.md:35-53` |
| `concept-reviewer` | Review gegen Pflichtsektionen/No-Placeholder/Approval | `agents/1-generic/concept-reviewer.md` |
| `planner` | Plan-Template (§7.2) inkl. `pipeline_stages`, `**Spec:**`, Ledger-Anbindung | `agents/1-generic/planner.md:38-51` |
| `orchestrator` | Phasen-Dispatch, Gate, frischer Subagent/Task, Checkpoint-Recovery | `agents/1-generic/orchestrator.md:39` |
| `documenter` | Archiv + Fallback-Index | Bestand |

**Pipeline-Wiring:** Erweiterung von `concept-driven-dev` (`role-defaults.yaml:2475-2516`):
optionale Stage `classify` (agent `ideation`/`explorer`) + `approve` (`requires_approval:true`,
gekoppelt an `dod_flag: spec-plan-enabled`); die bestehende Stage heißt **`specify`**
(`:2490`, nicht `specific`); danach `plan` (agent `planner`) vor `implement`.
`feature-lifecycle` (`:2344`, `plan-driven` `:2375-2382`) erhält optional `spec_ref`
(`accepts_plan_ref:true` `:2354` als Vorbild). SE-Pipeline bleibt unverändert.

---

## 10. Deaktivierbarkeit, Rückwärtskompatibilität, Migration (i)

### 10.1 Deaktivierbarkeit — alle Wirkungen no-op bei `effective_enabled=false`

| Wirkung | No-op-Mechanismus |
|---|---|
| Rules-Auslieferung | intrinsisches Gate in `collect_rule_sources` via `resolve_spec_plan_enabled` (§4.2) |
| Pipeline-Stages | `dod_flag: spec-plan-enabled`, von `resolve_dod()` selbst injiziert (erreicht jeden Render-Pfad, §5.4) |
| Agent-Templates | `{{#if SPEC_PLAN_WORKFLOW_ENABLED}}` (Registrierung R3, s. u.) |
| Consistency-Check | `check_spec_plan_workflow` → bei `effective_enabled=false` früh `return []` |
| Index/Archiv | übersprungen |
| Orchestrator | kein Gate/keine Classify-Pflicht → Bestandsverhalten |
| KE/SE | unberührt |

Seed für alle Pfade ist **eine** Helper-Funktion (§5.4) — kein doppelter Auflösungspfad.

**Registrierung der Template-Variablen (R3, verbindlich; sonst ist das Conditional wirkungslos):**
Der Mechanismus `{{#if SPEC_PLAN_WORKFLOW_ENABLED}}` greift nur, wenn die Variable den
Registrierungsstellen bekannt ist. Bei der Umsetzung sind zu registrieren:

1. `scripts/lib/variables.py` — Aufnahme in die **Conditional-Liste**
   (`strip_inactive_conditional_blocks`, `:228-233`), damit der Conditional-Block tatsächlich
   gestrippt wird.
2. `scripts/lib/consistency/placeholders.py` — `_BUILTIN_VARS` (`:11-116`) als bekannte, nicht
   zu bemängelnde Variable.
3. `scripts/lib/standalone.py` — `_CONDITIONAL_FALSE_FLAGS` (`:119`) für den
   Standalone-/Fallback-Pfad.

Mindestens in `agents/1-generic/orchestrator.md` wird die Variable als Conditional
(`{{#if SPEC_PLAN_WORKFLOW_ENABLED}}`) genutzt. Werden `SPEC_PLAN_SPECS_DIR` /
`SPEC_PLAN_PLANS_DIR` (§6.4) in Templates/Rules verwendet, werden auch sie an denselben drei
Stellen registriert. Die **Werte** setzt `_build_dod_variables()` (§5.4).

### 10.2 Rückwärtskompatibilität

- Default-Pfade neutral (`docs/specs`, `docs/plans`); `docs/plans` bereits vorhanden.
- Legacy `docs/superpowers/*` und bestehende `docs/plans/*` werden nur **gelesen**, nicht
  erzwungen (Template-Glob + changed-files-Scope, §5.1).
- Bestehende Rollen/Pipelines ohne Workflow bleiben nutzbar; neue DoD-Keys additiv.
- `plan-complete` ist **rein manuell** (F5): keine automatische Merge-Erkennung ⇒ keine
  Provider-/Plattform-Abhängigkeit, Rückwärtskompatibilität bleibt erhalten (§8).
- **`systems-engineering`-Schema (F1):** Die Deklaration wird **nicht** in diesem Vorhaben
  nachgezogen, sondern als eigenes Folge-Issue geführt. Bis dahin toleriert das Top-Level
  `additionalProperties:true` (`project-config.schema.json:2105`) den Block unverändert
  (Out-of-Scope-Follow-up, §5.2/§13).

### 10.3 Migrationspfad (optional, kein Massen-Umzug)

1. Neue Artefakte nach `paths.specs`/`paths.plans`; `paths.specs` und `paths.spikes` (sowie
   `paths.plans`, falls fehlend) werden bei `effective_enabled=true` durch den **neuen
   Sync-Scaffold-Schritt** (inkl. `.gitkeep`, analog KE-Scaffolder; **nicht** durch
   `variables.PROJECT_STRUCTURE`) angelegt — §5.1.
2. Legacy-Pfade in `paths.legacy`, nur gelesen.
3. Optionale Einzel-Migration über `documenter`/`knowledge-migrator`; Kopie statt Move
   (`preserve-originals:true`, `project.yaml:43-46`).
4. `variables.PROJECT_STRUCTURE` (`.meta-config/project.yaml:176-189`) wird **in diesem
   Vorhaben** um `docs/specs`/`docs/plans`/`docs/spikes` **ergänzt** (F9, entschieden
   2026-09-13; die Pfad-Entscheidung ist mit §5.1 gefallen — kein „nach Pfad-Entscheidung“
   mehr).

---

## 11. Trade-off-Entscheidungen

```
DECISION D1 — Verankerung
context: Spec/Plan-Workflow soll Superpowers adaptieren.
choice: Rein nativ: neue rules/1-generic/* + Erweiterung bestehender Rollen/Pipelines.
alternatives:
  - Externer Pack (obra/superpowers einbinden) → Abhängigkeit, Versions-Drift, nicht nativ.
  - Neues Parallel-System → Duplikation, Wartungslast.
consequences: Einmal definieren, überall nutzbar; Wartung im eigenen Repo.
```

```
DECISION D2 — Ledger (M1-korrigiert)
context: Recovery bei "frischer Subagent pro Task" braucht persistenten Fortschritt.
choice: Plan-Datei (Checkboxen + pipeline_stages) als menschliche Sicht + CheckpointStore/
        BarrierEntry.checkpoint_ref als maschinenlesbare Recovery-Quelle.
alternatives:
  - Eigenes Ledger-Format → dupliziert orchestration.py/checkpoint.py.
  - .meta-viz/events.jsonl → Default off (project.yaml:286-289), kein Repo-Artefakt.
  - Reiner Session-State → Recovery nach Kontextverlust unmöglich.
consequences: Bestands-Infrastruktur wird genutzt; orchestration.py wird NUR als Graph-Validator
  verdrahtet (FanoutPlan/validate_plan, F6) — execute_plan bleibt out-of-scope (Folge-Issue).
```

```
DECISION D3 — Isolation
context: Superpowers nutzt Worktree-Isolation; agent-meta verbietet sie hart.
choice: Frischer Subagent/Task + Datei-Ownership + Barrieren via check_file_overlap.
alternatives:
  - Worktree-Isolation übernehmen → verstößt gegen no-worktree-isolation.md/AGENTS.md.
  - Volle Parallelität ohne Ownership → Write-Konflikte.
consequences: Konventionskonform; weniger Parallelität bei Ownership-Überschneidung.
```

```
DECISION D4 — Master-Switch (B3/m3-cr-korrigiert)
context: Workflow muss abschaltbar sein, Presets sollen ihn aktivieren können.
choice: resolve_spec_plan_enabled: explizites bool > DoD-Preset `spec-plan-required` > false;
        EINE Ableitung, injiziert in `resolve_dod()` selbst, speist Rule-Gate UND
        synthetischen dod_flag `spec-plan-enabled` (erreicht damit jeden Render-Pfad).
alternatives:
  - Nur expliziter Switch → Presets wirkungslos.
  - Nur Preset-Kopplung → kein harter Override.
  - Paralleler zweiter Conditional-Pfad → doppelte Auflösung, Inkonsistenz.
consequences: Ein Seed für alle Wirkungen; Absenz-Semantik nötig (§5.4).
```

```
DECISION D5 — Pfade
context: Bestands-Konvention ist informell/nicht konfigurierbar.
choice: Neutral docs/specs + docs/plans; Legacy lesbar; optionale Einzel-Migration;
        Scan-Scope via Glob + changed_files.
alternatives:
  - superpowers-Pfad als Default → Namenskopplung an externes Tool.
  - Massen-Umzug → bricht Bestandslinks (docs/plans/README.md, 28+ Dateien).
consequences: Neue Artefakte sauber; Altbestand unangetastet; Template-Scope nötig.
```

```
DECISION D6 — Rules-Gating (M2-korrigiert)
context: collect_rule_sources globbt alle Rules in jedem Preset.
choice: intrinsisches, fail-closed Gate an EINEM Choke-Point (collect_rule_sources,
        verpflichtender config-Parameter) mit preset-unabhängiger Zuordnung in
        config/rules-presets.yaml (Top-Level-Sektion rule-gates, F3 — keine eigene Datei);
        Body-Conditional nur als Defense-in-Depth.
alternatives:
  - requires-flag nur im lazy-Preset → wirkungslos in default/minimal/silent.
  - Optionaler rule_gates-Parameter mit Default → vergessener Call-Site aktiviert Rules still.
  - Nur Body-Conditional → SKILL.md wird trotzdem erzeugt.
consequences: 6 Call-Sites (rules.py:282 = Embed-Kanal, keine Doppelzählung) teilen ein Gate;
  vergessener Call-Site = harter TypeError; kleiner Signatureingriff.
```

```
DECISION D7 — SE-Abgrenzung
context: SE-Kaskade existiert, neuer Workflow könnte kollidieren.
choice: Feature-Ebene getrennt; eigener Modus --validate-spec-plan; SE unverändert.
alternatives:
  - Spec/Plan in SE integrieren → vermischt V-Modell mit Feature-Tasks.
consequences: Beide Switches unabhängig; klare Artefakt-Trennung.
```

```
DECISION D8 — Index-Kopplung (F2/F4-korrigiert)
context: Auto-Indexierung soll KE nutzen, KE kann aus/ersetzt sein.
choice: mode knowledge-engine mit Fallback file-index/off + external-system-override (Info+Skip).
alternatives:
  - Unbedingte KE-Kopplung → bricht bei KE-off/externem System.
  - Kein Index → Wissen nicht auffindbar.
consequences: Fallback verhindert stillen Verlust; auto-index/auto-log werden in diesem Vorhaben
  verdrahtet (F2) und steuern das Auto-Schreiben der Index-/Log-Einträge (`false` = keine
  Auto-Writes, Dateien bleiben); external-system-override ist reine Info und erzwingt keine
  Integration (F4).
```

```
DECISION D9 — Validierungsfläche (B1-korrigiert)
context: run_checks() läuft auf agent_meta_root und kennt Consumer-Artefakte/Pfade nicht.
choice: eigenständiger Modus --validate-spec-plan analog se_validate.py; spec_plan.py lädt
        Consumer-Config selbst.
alternatives:
  - In run_checks() einhängen → falscher root, load_project_vars liefert nur Namens-Set.
consequences: CI-Gate wie SE; saubere Trennung Quell- vs. Consumer-Check.
```

```
DECISION D10 — Index-Rollenroute (M3-korrigiert)
context: knowledge-indexer darf nur von Knowledge-Agenten delegiert werden.
choice: Plan → planner pflegt selbst; Spec → knowledge-ingestor; Archiv → documenter.
alternatives:
  - Orchestrator direkt an knowledge-indexer → verletzt Rollenvertrag (:16).
consequences: KE-Route bleibt konsistent; ein Agenten-Hop bei Specs.
```

---

## 12. Test-/Verifikationsstrategie (j)

### 12.1 Betroffene bestehende Tests

| Test | Betroffenheit |
|---|---|
| `tests/test_config_null_blocks.py:27-66` | `spec-plan-workflow: null` → Mapping-Block `{}`; **`spec-plan-workflow` fehlt aktuell noch in `_MAPPING_BLOCKS` und ist dort aufzunehmen (R5)** (verifizierte Range `:27-66`), damit parametrisiert abgedeckt |
| `tests/test_pipelines.py` | neue Classify-/Approve-/Plan-Stage; `dod_flag: spec-plan-enabled` |
| `tests/test_orchestration_contract.py`, `test_barrier_runtime.py` | Gate/Phasen-Reihenfolge; `orchestration.py`-Verdrahtung; `FanoutPlan`-Nutzung als Plan-Validator |
| `tests/test_embed_rules_channel.py` | Gate in `collect_rule_sources`/`sync_embedded_rule_files` |
| `tests/test_knowledge_engine.py`, `test_knowledge_sync_integration.py` | Concept-Types an vier Stellen, KE-off-Fallback |
| `tests/test_dod_platform_cascade.py`, `test_conventions_platform_cascade.py` | neue DoD-Keys, `resolve_dod`-Keys |
| `tests/test_se_role_boundary.py` | SE-Abgrenzung intakt |
| `tests/test_frontmatter_parity.py`, `test_agents_frontmatter.py` | Rollen-Bumps ohne Frontmatter-Drift |

### 12.2 Neue Tests (beschreiben, nicht anlegen)

1. `tests/test_spec_plan_consistency.py` — `check_spec_plan_workflow`: Pflichtsektionen inkl.
   `pipeline_stages`, No-Placeholder, Traceability, Approval-Marker, `effective_enabled:false`→`[]`.
2. `tests/test_rules_activation_gate.py` — Gate an `collect_rule_sources`/Embed-Kanal entfernt
   inaktive Rules aus **allen** Presets.
3. `tests/test_spec_plan_config_schema.py` — Schema validiert Block/Defaults/
   `additionalProperties:false` + `concept-driven`-Enum. `systems-engineering` wird hier
   **nicht** getestet: Deklaration ist Out-of-Scope-Follow-up (F1).
4. `tests/test_plan_ledger.py` — Checkbox-/Status-Parsing + Checkpoint-Recovery.
5. `tests/test_spec_plan_resolve_enabled.py` — Präzedenz explizit > Preset > false;
   Absenz-Semantik.
6. `tests/test_spec_plan_validate_cli.py` — `--validate-spec-plan` gegen Consumer-root,
   Exit-Codes analog `--validate-se` (0 ohne Artefakte); **No-op bei `enabled:false`** (F12).
7. `tests/test_spec_plan_migration.py` — Legacy/Plans-Bestand gelesen, kein Auto-Move.
8. `tests/test_spec_plan_enabled_render_paths.py` — **B3-Rest:** `resolve_dod` injiziert
   `spec-plan-enabled`; bei `enabled:false` fehlen Approve-/Spec-Stages sowohl im Pfad
   `agent_sync.py:607` (`{{PIPELINE_DETAIL_BLOCKS}}`, `orchestrator.md:41`) als auch in
   `sync_pipeline.py:663`; bei explizitem `enabled:true` sind sie vorhanden.

### 12.3 Scenario-Pflicht (M5)

`rules/2-platform/agent-meta-conventions.md:69` + `tests/scenarios/registry.md:14-25`
verpflichten jede neue `project.yaml`-Option zu einem Scenario. Vorschlag:

- **ID/Name:** `50-spec-plan-workflow` (fixiert; höchste real vergebene ID ist
  `49-hacs-entity-naming`).
- `tests/scenarios/configs/50-spec-plan-workflow.project.yaml` — `spec-plan-workflow.enabled:true`
  plus `paths`/`archive`-Varianten.
- `tests/scenarios/asserts/50-spec-plan-workflow.sh` — asserted:
  (a) die durch den **neuen Sync-Scaffold-Schritt** angelegte `paths.specs`-Dir existiert
  (inkl. `.gitkeep`; **nicht** `variables.PROJECT_STRUCTURE`),
  (b) `spec-plan-workflow`-SKILL.md nur generiert wenn enabled,
  (c) `dod_flag: spec-plan-enabled` in generiertem Pipeline-Block,
  (d) KE-off-Fallback,
  (e) **`--validate-spec-plan` läuft im Scenario und ist bei `enabled:false` No-op (F12)**.
- **CI (F12/RVW-S3):** `--validate-spec-plan` wird in **denselben CI-Template-Job wie der
  bestehende Sync-Check** aufgenommen (`docs/guides/ci/github-actions-sync-check.yml`, real
  nur `sync.py --dry-run --check`; **keine** `--validate-se`-Prämisse); bei `enabled:false`
  ist der Lauf ein No-op mit Exit-Code 0.
- Katalog-Entry in `tests/scenarios/registry.md`-Tabelle; `tests/scenarios/run.sh` muss
  `PASS` liefern (DoD-Bestandteil, `registry.md:23`).

### 12.4 Rollen-/Versions-Governance (M6)

Frontmatter-`version` der geänderten Rollen bumpen; `2-platform`-Overrides falls vorhanden
`version` + `based-on` aktualisieren (`rules/2-platform/agent-meta-conventions.md:60-68`).
Verifikation: `python3 scripts/sync.py --check` (Drift) und `python3 scripts/sync.py --validate`.

---

## 13. Offene Fragen — entschieden (2026-09-13)

Alle vormals offenen Fragen sind **verbindlich entschieden** (F1–F12). Es verbleibt genau
**ein** bewusst ausgelagertes Folge-Issue (F1).

**Vorgeschichte — durch die Reviews geklärt (aus v1):**

- ✅ Validierungsort — eigener `--validate-spec-plan`-Modus (B1, §7.3). *(v1-Frage 5/11 teilweise)*
- ✅ DoD-Key-Injektion — Keys ins `full`-Preset + relevante Presets, nicht ins tote Fallback (B2).
- ✅ Rule-Gate-Ort — intrinsisch in `collect_rule_sources`, preset-unabhängig (M2).
- ✅ Ledger-Ort — Plan-Datei + `CheckpointStore`/`checkpoint_ref` (M1/D2).
- ✅ Index-Rollenroute — kein Direkt-Dispatch an `knowledge-indexer` (M3/D10).
- ✅ Concept-Type-Stellen — vier Stellen benannt (M4).
- ✅ A2A-Felder — `payload` ist `additionalProperties:true`, keine Schema-Erweiterung nötig (m2-dm).
- ✅ Absenz-Semantik — festgelegt, Defaults werden nicht materialisiert (m3-cr).

**Entscheidungen (2026-09-13):**

| # | Frage | Entscheidung | Umsetzungsort |
|---|---|---|---|
| **F1** | `systems-engineering` im Schema? | **Eigenes Folge-Issue — bewusst out-of-scope** in diesem Vorhaben. Der Block bleibt bis dahin undeklariert und wird vom Top-Level `additionalProperties:true` toleriert. | §5.2, §10.2 |
| **F2** | `okf.auto-index`/`auto-log` verdrahten? | **Ja — verdrahten** (real wirksam): steuern das automatische Schreiben/Aktualisieren von `knowledge/wiki/index.md`/`log.md` nach Spec-/Plan-Erstellung; `false` = keine Auto-Writes (Dateien werden vom KE-Scaffolder weiterhin angelegt und agent-driven gepflegt, **nicht** gelöscht). | §6.2, §8, D8 |
| **F3** | Wo liegt das Rule-Gate? | **Erweiterung `config/rules-presets.yaml`** um die preset-unabhängige Top-Level-Sektion `rule-gates` — **keine** neue Datei `config/rule-gates.yaml`. | §4.2, D6 |
| **F4** | Semantik `external-system-override`? | **Info-Keys + Skip:** markiert nur, dass KE/Auto-Index übersprungen werden. **Keine** erzwungene Integration. | §6.1, §6.3 |
| **F5** | Merge-Erkennung `plan-complete`? | **Rein manuell** — keine Auto-Erkennung, keine Provider-Abstraktion. | §8, §10.2 |
| **F6** | `orchestration.py`-Verdrahtung? | **Nur Graph-Validator** (`FanoutPlan`/`validate_plan` → Check `spec_plan_plan_graph`). `execute_plan` bleibt out-of-scope/Folge. | §3.1, §7.3, D2 |
| **F7** | „Architectural“ ohne Dateizahl? | **Qualitatives Zusatzkriterium** ergänzt: öffentliche Schnittstellen/Contracts, Datenmodell/Schema oder >1 Subsystem-/Komponentengrenze — unabhängig von der Dateizahl. | §2.1 |
| **F8** | DoD-Flag-Namen final? | **Bestätigt:** `spec-plan-required`, `spec-plan-traceability`, synthetisch `spec-plan-enabled`. Keine Umbenennung. | §5.3, §5.4 |
| **F9** | `variables.PROJECT_STRUCTURE` nachziehen? | **Ja — in diesem Vorhaben** um `docs/specs`, `docs/plans`, `docs/spikes` ergänzen. | §10.3 |
| **F10** | Spike-Ownership? | **`explorer` erweitern** um expliziten Spike-Modus (billig untersuchen, Empfehlung berichten, Wegwerf-Code markieren, read-only/keine Schreibrechte). | §2.1, §2.2, §9 |
| **F11** | Archivierung Agent vs. Sync? | **Agentbasiert bestätigt** (`documenter`/`knowledge-ingestor`). Ein Sync-Schritt bleibt **Nicht-Ziel**. | §8 |
| **F12** | `--validate-spec-plan` in CI? | **Ja — in CI + Szenario** aufnehmen; **No-op bei `enabled:false`** (Exit 0). | §7.3, §12 |

**Einziges offenes Folge-Issue:** F1 (`systems-engineering`-Schema-Deklaration). Alle übrigen
Punkte sind entschieden und in die genannten Abschnitte eingearbeitet.
