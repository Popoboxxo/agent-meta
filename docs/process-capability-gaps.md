# Prozess-/Capability-Gaps — Fortschritts-, Ausführungs- und Verifikationssystem

> Stand: 2026-09-14 · Status: Read-only Analyse, keine Implementierung (Nachtrag §6.1: umgesetzter Phase-0-Status)
> Bezug: internes Spec/Plan-Workflow-Vorhaben; Coverage-Matrix `docs/spec-plan-workflow-coverage.md`
> Terminologie: „Ziel-Prozessprofil" = externes Referenz-Prozessmodell; „Referenz-Fähigkeiten";
> „Capability-Gap". Keine Externalität/Abhängigkeit wird eingeführt.

## 1. Zweck & Scope

- **Ziel:** Vergleich des eigenen Prozess-/Fortschrittssystems gegen ein externes
  Ziel-Prozessprofil; Ableitung priorisierter Capability-Gaps und einer Scope-Zuordnung.
- **Methode:** read-only. Ist-Stand am Code verifiziert (Material A), Referenz-Fähigkeiten
  neutral paraphrasiert (Material B), bereits abgebildete Mechanismen (Material C).
- **Out-of-scope:** keine Implementierung, keine REQ-Vergabe, kein Commit, keine
  Template-/Config-Änderung, kein `sync.py`-Lauf.
- **Kein Ersatz für Tests:** jede Lücken-Aussage verweist auf ein `file:symbol`; wo der
  Nachweis nur Prosa ist, wird das ausdrücklich gesagt.

## 2. Progress-System — Ist-Stand

### 2.1 Facetten-Matrix

| Facette | vorhanden | Typ | file:symbol | Testbeweis |
|---|---|---|---|---|
| Persistenter Ledger/Progress | teilweise | rule+script | `rules/1-generic/plan-ledger.md:14-23`; `scripts/lib/consistency/spec_plan.py::parse_plan_ledger:82`, `::_check_ledger_format:458`; `config/rules-presets.yaml` `rule-gates.plan-ledger` | `tests/test_plan_ledger.py::test_all_checked_is_complete`, `::test_open_checkbox_is_incomplete`, `::test_missing_status_is_none` |
| Ledger-Format | ja | script (validator) | `spec_plan.py::_check_ledger_format:458-472` (WARNING bei Checkboxen ohne `Status:`) | `tests/test_spec_plan_consistency.py::test_good_artifacts_pass` |
| Cross-Session-Recovery (JSON) | teilweise | script (Library) | `scripts/lib/checkpoint.py::CheckpointStore.save_checkpoint:349`, `load_session:406`, `get_last_checkpoint:410`, `get_completed_steps:417`, `list_sessions:428`, `delete_session:436`; Format `.meta-viz/checkpoints/<session>.json` (`:35,:282`) | `tests/test_plan_ledger.py::test_checkpoint_store_round_trip_is_recovery_source`; `tests/test_persistence_atomicity.py::test_get_last_checkpoint_returns_none_on_corrupt_file` |
| Resume-Logik | nein (nur Doku) | docs-only | `snippets/orchestrator/checkpointing.md:22-29` („on session start … Resume from step …") — kein Code-Caller | kein Auto-Resume-Test |
| Lifecycle/24h-Cleanup | nein (nur Doku) | script ungenutzt | `checkpoint.py::cleanup_old_sessions:444` (`max_age_seconds=86400`) ohne Produktions-Caller; `checkpointing.md:30` | nur `tests/test_persistence_atomicity.py::test_cleanup_old_sessions_skips_corrupt_file_without_crashing` |
| Raw-Output-Archiv | ja | script | `checkpoint.py::save_raw_output:288`, `load_raw_output:323`, `list_raw_outputs:339` | `tests/test_checkpoint_raw_output.py::test_save_raw_output_writes_under_session_directory` |
| `progress/current.md` Tier A/B | ja | script | `checkpoint.py::_PROGRESS_DIR:39`, `::_progress_tier:67`, `::_write_progress_file:378`, `::_render_progress_entry:133`, `::_trim_oldest_entries:156`, `::_progress_lock:176` | `tests/test_progress_file*.py`, `tests/test_progress_tier_resolution.py` |
| Status-Contract | ja | rule/snippet | `snippets/orchestrator/status-table.md`; eingebunden `agents/1-generic/orchestrator.md:197` (`{{STATUS_TABLE_BLOCK}}`) | `tests/test_status_table_orchestrator_reference.py` |
| BARRIER/`checkpoint_ref` | ja | script | `scripts/lib/orchestration.py::BARRIER_ENTRY_MARKER:62`, `BarrierEntry.checkpoint_ref:135`, `render_barrier_result:507`, `execute_plan:439-447` | `tests/test_orchestration_contract.py::test_render_checkpoint_ref_line`, `::test_execute_with_store_archives_raw_output_and_sets_checkpoint_ref` |
| Live-Progress-Kanal | ja (Design-Header stale) | script+rule | `checkpoint.py::_write_progress_file`; `orchestrator.md:199-201` (`PROGRESS_CHAT_PUSH_ENABLED`); Design-Header behauptet fälschlich „noch nicht implementiert" | `tests/test_progress_chat_push_variable.py`, `tests/test_progress_file_migration.py` |
| Verifikations-Gates | ja | script/test | `scripts/sync.py:156` (`--validate-spec-plan`) → `scripts/lib/spec_plan_validate.py::validate_spec_plan:73`; `consistency/spec_plan.py::check_spec_plan_workflow:96`, `::_check_approval_markers:427`, `::_check_plan_graph:475`; DoD `scripts/lib/dod.py::resolve_spec_plan_bundle:275`; `config/dod-presets.yaml:91` | `tests/test_spec_plan_validate_cli.py`, `tests/test_spec_plan_consistency.py`, `tests/test_pipelines.py::test_concept_driven_dev_spec_plan_stage_order` |
| `validator`/DoD | ja | role | `agents/1-generic/validator.md:50-55`; Pipeline-Stage `validate` (`config/role-defaults.yaml:2532-2538`) | — |
| Nebenläufigkeit/Ownership | ja | script+rule | `scripts/lib/file_affinity.py::check_file_overlap:173`; `orchestration.py::check_plan_file_overlap:309`, `::validate_plan:237`, `::find_dependency_errors:172`; `consistency/spec_plan.py::_parse_plan_tasks:510` | `tests/test_orchestration_contract.py::test_check_plan_file_overlap_*`, `tests/test_file_affinity.py` |
| No-Worktree | ja | rule | `rules/1-generic/no-worktree-isolation.md`; `plan-ledger.md:36-43` | — |
| Frischer Subagent pro Task | ja | rule | `rules/1-generic/plan-ledger.md:6-12`; `orchestrator.md:54` | — |
| Loop/`reflection_pairs` | ja | config | `config/role-defaults.yaml::reflection_pairs.concept-specify-loop:2343`, `loop_ref` in `concept-driven-dev:2513` | `tests/test_pipelines.py::test_resolve_stage_loop_concept_driven_dev_review_ratchet` |
| `execute_plan` (Task-Loop-Backend) | nein (out-of-scope) | script ohne Caller | `orchestration.py::execute_plan:372`; out-of-scope laut `consistency/spec_plan.py:14`, `plan-ledger.md:33-34` | — |

### 2.2 Kernaussage

**Haben wir ein persistentes Fortschritts-/Ledger-System über Sessions/Tasks?**
**Teilweise.** Persistenz existiert auf zwei getrennten Ebenen: (1) Plan-Datei-Checkboxen als
menschenlesbarer Ledger, validiert/geparst via `parse_plan_ledger`; (2) `CheckpointStore`-JSON
unter `.meta-viz/checkpoints/<session>.json` plus `progress/current.md`. Beide sind aber **nicht
zu einem laufenden System verdrahtet**: `execute_plan` hat keinen Produktions-Caller, der
24h-Cleanup ist nicht aufgerufen, Resume existiert nur als Snippet-Prosa. Cross-Session-Kontinuität
hängt am LLM-Orchestrator, der die Doku befolgt — nicht an erzwungener Maschinerie.

**Praktischer Beleg:** Der Live-Progress-Kanal ist implementiert
(`checkpoint.py::_write_progress_file`, `PROGRESS_CHAT_PUSH_ENABLED`), der Plan-Ledger steht
jedoch bei **0/56 Haken** — der Fortschritt lebt im Live-Kanal, nicht im Ledger.

### 2.3 Lücken gegenüber einem Recovery-Ledger-Modell

1. **Kein globales Board** — Ledger nur pro Plan-Datei (`parse_plan_ledger:82`); kein Aggregat
   über Pläne/Sessions.
2. **Kein Auto-Re-Hydrate** — `get_last_checkpoint`/`get_completed_steps`/`list_sessions`
   (`checkpoint.py:410/417/428`) ohne Aufrufer; „on session start"-Read nur Prosa
   (`checkpointing.md:22-29`).
3. **Keine stabilen Cross-Session-Task-IDs** — Plan-Tasks pro Plan auf `task-<n>` normalisiert
   (`spec_plan.py::_normalize_task_id:549`), Checkpoint-IDs zufällige UUIDs
   (`checkpoint.py::Checkpoint.__init__:218`); kein gemeinsamer Schlüssel.
4. **Checkbox-Ledger wird nie maschinell geschrieben/aktualisiert** — nur ein Reader
   (`parse_plan_ledger`), kein Writer; Ledger-Drift unbeobachtet.
5. **24h-Rotation nicht verdrahtet** — `cleanup_old_sessions:444` ungenutzt vs. Doku-Versprechen
   (`checkpointing.md:30`).
6. **`progress/current.md` ist kein Recovery-Input** — „not parsed by any code path"
   (`checkpointing.md:39`); Recovery liest nur JSON.
7. **Zwei parallele Checkpoint-Formate** — manuelles `.meta-viz/checkpoint-<ts>.json`
   (`checkpointing.md:2-16`) vs. `CheckpointStore <session>.json` (`checkpoint.py:282`); keine Brücke.
8. **Checkpoint-Persistenz nur bei Harness-Übergabe** — `save_raw_output`/`checkpoint_ref` nur wenn
   `store` UND `session_id` übergeben werden (`orchestration.py:428`); `execute_plan` nirgends
   produktiv aufgerufen.

## 3. Fähigkeits-Matrix (Ziel-Prozessprofil ↔ agent-meta)

| Aspekt | Referenz-Fähigkeit (neutral) | vorhanden? | agent-meta-Mechanismus (`file:symbol`) | Gap? |
|---|---|---|---|---|
| Klassifikation | Anfrage vor Umsetzung klassifizieren, Klasse benennen, menschliche Freigabe, Tiefe nie abwärts | ja | `rules/1-generic/brainstorming-gate.md`; `config/rules-presets.yaml` (`rule-gates.brainstorming-gate`); `agents/1-generic/orchestrator.md` Task-Size-Routing; `tests/test_frontmatter_parity.py::test_ideation_maps_task_sizes_to_classes` | Abwärts-Sperre nicht explizit (G-15) |
| Spec-Authoring/Approval | freigegebene Spec als Autorität + Voraussetzung; Self-Review + Human-Review vor Planung | ja | `rules/1-generic/spec-plan-workflow.md`; Stage `approve` (`config/role-defaults.yaml:2514`, `scripts/lib/pipelines.py::_stage_requires_approval`) | nein |
| Plan-Format | ohne Projektkontext ausführbar: Metadaten, Datei-Map, kleinste testzyklische Schritte, Interfaces, keine Platzhalter, Self-Review | ja | `rules/1-generic/writing-plans.md`; `agents/1-generic/planner.md` | nein |
| Ausführung (frischer Subagent+Review) | frischer isolierter Task-Kontext; zwei-stufiger Review (Anforderungstreue, dann Qualität); begrenzte Runden | teilweise | `rules/1-generic/plan-ledger.md:6-12`; `config/role-defaults.yaml::reflection_pairs.concept-specify-loop:2343`, `loop_ref` in `concept-driven-dev:2513` | zweiter Review-Pass + Runden-Cap nicht explizit (G-09) |
| Ledger/Recovery | Fortschritt im vorhaben-eigenen Ledger; exakt an erster offener Aufgabe fortsetzen; Datei/Versionierung schlägt Erinnerung | teilweise | `rules/1-generic/plan-ledger.md:14-23`; `scripts/lib/checkpoint.py::CheckpointStore.save_checkpoint:349`; `scripts/lib/orchestration.py::BarrierEntry.checkpoint_ref:135` | kein Auto-Re-Hydrate, read-only Ledger, keine stabilen IDs (G-01…G-08) |
| Verifikations-Gates | Erfolg nur mit frischem, vollständig ausgeführtem Nachweis; Reviews als Pflicht-Gates zwischen Tasks | teilweise | `scripts/sync.py:156` (`--validate-spec-plan`); `scripts/lib/spec_plan_validate.py::validate_spec_plan:73`; `scripts/lib/dod.py::resolve_spec_plan_bundle:275`; `agents/1-generic/validator.md:50-55` | keine Freshness-/Execution-Pflicht (G-12) |
| Ursachenanalyse/Root-Cause | Bugfix nur nach Ursachenanalyse; nach wiederholt erfolglosen Fixes Architektur hinterfragen | teilweise | `agents/1-generic/principal-developer.md:75-82` (Eskalation, kein Pflicht-Gate); `agents/1-generic/incident-responder.md` | kein Pflicht-Gate (G-10) |
| Skill-Discovery/Governance | Anleitung vor jeder Aktion prüfen/laden; Kurzbeschreibung nennt nur Auslösebedingungen; testgetrieben; Re-Injektion nach Kontextverlust | teilweise | `config/skills-registry.yaml`; `scripts/lib/rules.py::collect_rule_sources:149`, `::rule_opts_lazy_channel:263`; `scripts/lib/skill_channel.py`; `config/rules-presets.yaml` (`skill-description`) | Trigger-only-Disziplin + Re-Injektion + Test-Erzeugung nicht erzwungen (G-13) |
| Workspace-Isolation | isolierter Arbeitsbereich mit sauberer Test-Baseline; Integrationsentscheidung nur Mensch | nein (bewusste Abweichung) | `rules/1-generic/no-worktree-isolation.md`; `rules/1-generic/plan-ledger.md:36-43` (Ownership+Barrier+Checkpoint als Ersatz) | bewusste Abweichung (G-14), kein Handlungsbedarf |
| TDD-Zwang | kein Produktionscode ohne vorher beobachteten fehlschlagenden Test; Code-vor-Test wird gelöscht | teilweise | `agents/1-generic/tester.md:30` (TDD-Zyklus); `config/role-defaults.yaml:268`; `rules/1-generic/writing-plans.md:41-44` | kein durchsetzendes Gate (G-11) |

## 4. Priorisierte Gap-Liste

| ID | Gap | Warum relevant | Lösungsansatz im agent-meta-Stil | Prio | Aufwand |
|---|---|---|---|---|---|
| G-01 | Kein globales Board — Ledger nur pro Plan-Datei (`spec_plan.py::parse_plan_ledger:82`), kein Aggregat über Pläne/Sessions | Parallele Vorhaben nicht korrelierbar, kein Portfolio-Blick | Resolver-Aspect in `config/spec-plan-groups.yaml` + read-only Aggregation in `scripts/lib/consistency/` | P1 | M |
| G-02 | Kein Auto-Re-Hydrate (`checkpoint.py::get_last_checkpoint:410`, `get_completed_steps:417`, `list_sessions:428` ohne Aufrufer; Resume nur Prosa `checkpointing.md:22-29`) | Kernversprechen „nahtlos fortsetzen" trägt allein der LLM-Orchestrator | Rule-/Snippet-Pfad + expliziter Resume-Caller beim Orchestrator-Start; Config-Flag statt Provider-Branch | P0 | M |
| G-03 | Keine stabilen Cross-Session-Task-IDs — Plan `task-<n>` (`spec_plan.py::_normalize_task_id:549`), Checkpoints UUIDs (`checkpoint.py::Checkpoint.__init__:218`) | Ohne gemeinsamen Schlüssel keine verlässliche Task↔Checkpoint-Zuordnung | Task-ID-Schema im Plan-Format (Rule) + Checkpoint-Feld; Konsistenz-Check in `spec_plan.py` | P0 | S |
| G-04 | Checkbox-Ledger wird nie maschinell geschrieben — nur Reader (`parse_plan_ledger:82`), kein Writer; Drift unbeobachtet (praktisch 0/56) | Fortschritt hängt an manuellem Haken-Setzen → Ledger↔Realität divergiert | Ledger-Writer als Library-Funktion + Rule-Pflicht nach Task-Abschluss; Drift-Check in `--validate-spec-plan` | P0 | M |
| G-05 | 24h-Rotation nicht verdrahtet — `checkpoint.py::cleanup_old_sessions:444` ungenutzt vs. `checkpointing.md:30` | Checkpoint-Bloat; Doku-Versprechen unerfüllt | Config-Flag + Aufruf beim Orchestrator-Start (Rule) | P1 | S |
| G-06 | Zwei parallele Checkpoint-Formate — `checkpoint-<ts>.json` (`checkpointing.md:2-16`) vs. `CheckpointStore <session>.json` (`checkpoint.py:282`) | Uneindeutige Recovery-Quelle, doppelte Pflege | Ein Format normieren (Rule + Parser), Brücke/Migration als Resolver | P1 | S |
| G-07 | `progress/current.md` ist kein Recovery-Input (`checkpointing.md:39`) | Live-Kanal und Recovery entkoppelt | Recovery-Resolver liest `current.md` als Fallback (Library-Funktion) | P2 | S |
| G-08 | Checkpoint-Persistenz nur bei Harness-Übergabe (`orchestration.py:428`; `execute_plan` out-of-scope) | Ohne produktiven Caller entstehen keine Checkpoints | eigenes Vorhaben (Backend), nicht Spec/Plan | P1 | L |
| G-09 | Kein zweistufiger Task-Review + kein Runden-Cap (Reflection-Loops ohne explizite Abbruchgrenze) | Endlosschleifen-Risiko; Qualität erst nach Anforderungstreue | Pipeline-Stage-Kette (`role-defaults.yaml`): review-req → review-quality; `max_rounds`-Config im Reflection-Paar | P1 | M |
| G-10 | Kein Pflicht-Root-Cause-Gate vor Bugfix (`principal-developer.md:75-82` nur Eskalation) | Symptom-Fixes statt Ursache | Rule-Gate `root-cause-gate` + Pipeline-Stage-Condition | P1 | S |
| G-11 | Kein durchsetzendes TDD-Gate (`tester.md:30`, `writing-plans.md:41-44` sind Doku) | Regressionsschutz nur konventionell | Rule-Gate + DoD-Flag `tdd-required` (analog `spec-plan-required`) | P1 | M |
| G-12 | Keine Freshness-/Execution-Pflicht für Verifikationsnachweise | „erledigt" ohne frischen Lauf | DoD-/Validator-Erweiterung: Evidence-Referenz + Zeitstempel-Prüfung | P1 | M |
| G-13 | Skill-/Rule-Governance nicht erzwungen (Trigger-only-Kurzbeschreibung, Re-Injektion, testgetriebene Anleitung) | Anleitungen driften; Kontextverlust | `config/rules-presets.yaml` (`skill-description`-Pflicht) + Test; Re-Injektion via `collect_rule_sources` | P2 | M |
| G-14 | Workspace-Isolation bewusst ersetzt (Ownership+Barrier+Checkpoint) | Bewusste Abweichung, kein Worktree | keine — dokumentierte Ausnahme | P2 | — |
| G-15 | Keine explizite Sperre gegen Abwärts-Eskalation der Klassifikation | Komplexität könnte stillschweigend herabgestuft werden | Rule-Erweiterung `brainstorming-gate` + Konsistenz-Check im Score | P2 | S |

### Top-5

1. **G-02** — Auto-Re-Hydrate/Resume-Caller (Kernversprechen der Sitzungskontinuität).
2. **G-03** — stabile Cross-Session-Task-IDs (Voraussetzung für jedes Recovery).
3. **G-04** — Ledger-Writer + Drift-Check (behebt den belegten 0/56-Zustand).
4. **G-09** — zweistufiger Task-Review mit Runden-Cap (Qualität + Endlosschleifen-Schutz).
5. **G-10** — Pflicht-Root-Cause-Gate vor Bugfix (Ursache statt Symptom).

## 5. Empfehlung — Scope-Zuordnung

**A) In das bestehende Spec/Plan-Workflow-Vorhaben** (Regel-/Format-Erweiterung, kein Backend):

- **G-03** → Task-ID-Schema im Plan-Format (`rules/1-generic/writing-plans.md`,
  `consistency/spec_plan.py`).
- **G-04** → Ledger-Writer-Regel + Drift-Check in `--validate-spec-plan`.
- **G-09** → zweiter Review-Pass + `max_rounds` in den bestehenden Reflection-Loops.
- **G-15** → Abwärts-Sperre als kleine Erweiterung des `brainstorming-gate`.

**B) Eigenes Vorhaben „Ledger-/Recovery-Maschinerie"** (Backend/Verdrahtung nötig):

- **G-02**, **G-08**, **G-06**, **G-05**, **G-07**, **G-01** — in dieser Reihenfolge:
  erst Resume-Caller und produktive Checkpoint-Persistenz, dann Format-Vereinheitlichung,
  Rotation, `current.md`-Fallback und zuletzt das globale Board.

**C) Eigenes Vorhaben „Gates & Governance"**:

- **G-10** (Root-Cause-Gate), **G-11** (TDD-Gate), **G-12** (Freshness-Gate) als jeweils
  eigene, kleine Rule+DoD-Vorhaben nach dem Muster `spec-plan-required`; **G-13**
  (Skill-Governance) zuletzt, da es mehrere Config-Flächen berührt.

**D) Bewusst nicht:** **G-14** (Workspace-Isolation) — die Ablehnung ist dokumentierte
Entscheidung, kein Gap.

**Grobe Reihenfolge:** A → B (Start G-02/G-08) → C (G-10, G-12, G-11) → C (G-13).

## 6. Bewusste Ausnahmen / Out-of-Scope

- **`execute_plan`-Backend** bleibt out-of-scope (`consistency/spec_plan.py:14`,
  `plan-ledger.md:33-34`); eingebunden ist nur der Graph-Validator.
- **Worktree-Isolation bewusst verworfen** (`rules/1-generic/no-worktree-isolation.md`);
  Ersatz sind explizite Ownership + Barrieren + Checkpoint-Ledger — kein Nachbau nötig.
- **Provider-gebundene Mechanismen** (Worktrees, automatische Skill-Injektion per Session-Hook)
  werden **nicht** übertragen; Provider-Unterschiede ausschließlich über Config-Keys/
  Capability-Flags (Provider-Agnostik), nie über `if provider == …`.
- **Referenzspezifische Pack-/Vendor-Abhängigkeit** ist ausgeschlossen; keine Externalität
  oder Abhängigkeit wird eingeführt.

### 6.1 Provider-Runtime-Gate (CRITICAL GATE) — Status

Nachtrag zum umgesetzten Phase-0-Stand (SPEC-OPENCODE-RUNTIME-GATE-2026-09-13). Die
Tier-Semantik und die Verträge stehen in
[`concepts/runtime-gate-tiers.md`](concepts/runtime-gate-tiers.md); hier nur der
ehrliche Ist-Stand. Der `# CRITICAL GATE` ist nur so stark wie das Runtime des
aktiven Providers:

- **`hook`** — verifizierter PreToolUse-Hook-Vertrag; Runtime-Gate vorhanden
  (`GATE_ENFORCED`). Unverändert.
- **`permission`** — native Permission-Schicht blockiert Main-Chat-Writes über den
  bestehenden `isolation.py`-Merge-Pfad (A2-Mapping-Deny). **PARTIAL**: die
  Delegations-Provenienz ist nicht erzwungen, und die Child-Session-Propagation
  (`deriveSubagentSessionPermission`, **#765**) ist **unverifiziert**. Das ist der
  aktuelle Phase-0-Status des OpenCode-Blocks (`runtime_gate: permission` in
  `config/provider-capabilities.yaml`); kein
  „vollständig erzwungen".
- **`plugin`** — die native Plugin-Tier ist **Phase 1** und läuft nur im Modus
  `observe`; `MODE=enforce` und der Tier-Flip sind hinter die Real-Repo-Verifikation
  (P6) gesperrt. In Phase 0 deklariert kein Provider `runtime_gate: plugin`.
- **`advisory`** — rein prompt-basiert (fail-safe Default für unbekannte oder
  fehlende Konfiguration).

A2 schreibt keinen neuen Root-Key und umgeht den create-only Settings-Initializer
(**#747**); der Managed-State ist reversibel und namespaced. Insgesamt bleibt der
Gate eine **Convention boundary**, keine **security boundary** (Definition:
`.claude/rules/branch-guard.md`).

## 7. Nicht-Ziele & Nicht-Implementierung

- Keine Code-, Template-, Config- oder Test-Änderung; keine REQ-Vergabe; kein Commit;
  kein `sync.py`-Lauf.
- Dieses Dokument ist Analyse-Artefakt, **kein** Umsetzungsplan. Jede Umsetzung setzt ein
  eigenes Vorhaben mit eigener Spec/Plan-Kette voraus.
