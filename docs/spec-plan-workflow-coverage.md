# Spec/Plan-Workflow — Coverage-Matrix

> **Stand:** 2026-09-13
> **Bezug:** Design-Addendum `docs/superpowers/specs/2026-09-13-spec-plan-workflow-design.md`
> (§D.4, §E) · Umsetzungsplan `docs/superpowers/plans/2026-09-13-spec-plan-workflow.md`
> (Task 24) · Seed `config/spec-plan-groups.yaml`.

## 1. Zweck & Scope

Diese Matrix verbindet jeden **Prozess-Aspekt** des nativen Spec/Plan-Workflows mit dem
konkreten **agent-meta-Mechanismus**, der ihn trägt — plus Fundstelle (`file:symbol`),
Consumer, Test-Nachweis und Status. Sie ist ein **Abdeckungs- und Drift-Nachweis** und
**kein Ersatz für Tests**: Jede Zeile verweist auf mindestens einen realen Test, der den
Mechanismus beobachtet. Ändert sich ein Mechanismus, muss die zugehörige Zeile mitziehen
(Pflege-Regel, §6).

Scope: alle Aspekte des Seed-Gruppen-Configs `config/spec-plan-groups.yaml` (Gruppe
`plan-mode`), die Routing-/Gate-/Scaffold-/DoD- und KE-Kopplung des Workflows sowie die
Gating-Regeln und der Route-Guard. **Nicht** Scope: die Prosa-Konzeption selbst (die liegt
in der Design-Spec) und die SE-Kaskade (eigener, unabhängiger Prozess).

## 2. Legende

Mechanismustypen (`Typ`-Spalte):

| Typ | Bedeutung |
|---|---|
| `rule` | Verbindliche Prozess-Regel (`rules/1-generic/*.md`), ausgeliefert über `collect_rule_sources` und das Rule-Gate. |
| `pipeline` | Deklarative Stage-/Gate-Definition in `quality_pipelines` bzw. deren Rendering/Validierung. |
| `reflection-pair` | Wiederverwendbares Generator/Critic-Loop-Paar in `reflection_pairs`, referenziert per `loop_ref`. |
| `role` | Agenten-Rolle, die einen Workflow-Schritt trägt (kein neues Rollen-Artefakt). |
| `resolver` | Ein-Seed-Ableitung (`resolve_spec_plan_bundle`) für alle Plan-Modus-Aspekte. |
| `config` | Deklarativer Config/Schema-Schalter, der den Aspekt steuert. |
| `test` | Ausführbarer Guard, der Drift/Regel-Verstöße detected (kein Laufzeit-Mechanismus). |

`Status`-Werte: `umgesetzt` (Mechanismus + Test vorhanden), `umgesetzt (config-gekoppelt)`
(Aspekt hängt zusätzlich an KE-Config), `offen` (bewusst nicht Teil dieses Vorhabens).

## 3. Matrix

| Prozess-Aspekt | Typ | agent-meta-Mechanismus | Fundstelle (file:symbol) | Consumer | Nachweis (Test) | Status |
|---|---|---|---|---|---|---|
| Klassifikation Spike/Bounded/Architectural (S/M/L/XL) | `rule` | `brainstorming-gate` — Regel-Gate | `rules/1-generic/brainstorming-gate.md`; `config/rules-presets.yaml:198` (`rule-gates.brainstorming-gate`) | `scripts/lib/rules.py::collect_rule_sources` | `tests/test_rules_activation_gate.py::test_rule_gates_section_declares_all_new_stems`; `tests/test_frontmatter_parity.py::test_ideation_maps_task_sizes_to_classes` | umgesetzt |
| Spec-Authoring (Pflicht-Template) | `rule` | `spec-plan-workflow` Master-Rule | `rules/1-generic/spec-plan-workflow.md` (Abschnitt `Spec-Template`); `config/rules-presets.yaml:196` (`rule-gates.spec-plan-workflow`) | `scripts/lib/rules.py::collect_rule_sources` | `tests/test_rules_activation_gate.py::test_gate_delivers_rule_when_enabled`; `tests/test_frontmatter_parity.py::test_concept_specifier_uses_spec_template_sections` | umgesetzt |
| Approval-Gate (`Status: APPROVED`) | `pipeline` | `requires_approval`-Stage `approve` in `concept-driven-dev` | `config/role-defaults.yaml:2514` (`quality_pipelines.concept-driven-dev.approve`); `scripts/lib/pipelines.py::_stage_requires_approval` | `scripts/lib/pipelines.py::_generate_pipeline_block` | `tests/test_pipelines.py::test_concept_driven_dev_spec_plan_stage_order`; `tests/test_pipelines.py::test_concept_driven_dev_spec_plan_hidden_when_disabled` | umgesetzt |
| Plan-Authoring | `rule` | `writing-plans` — Pflicht-Header + `pipeline_stages` | `rules/1-generic/writing-plans.md`; `config/rules-presets.yaml:200` (`rule-gates.writing-plans`) | `scripts/lib/rules.py::collect_rule_sources`; `scripts/lib/pipelines.py::parse_plan_ref` | `tests/test_rules_activation_gate.py::test_new_rule_files_exist`; `tests/test_pipelines.py::test_planner_template_mentions_pipeline_stages_mandate` | umgesetzt |
| Ausführung / Ledger | `rule` | `plan-ledger` — frischer Subagent + Checkbox-Ledger | `rules/1-generic/plan-ledger.md`; `config/rules-presets.yaml:202` (`rule-gates.plan-ledger`) | `scripts/lib/rules.py::collect_rule_sources`; `scripts/lib/consistency/spec_plan.py::parse_plan_ledger` | `tests/test_rules_activation_gate.py::test_rule_gates_section_declares_all_new_stems`; `tests/test_plan_ledger.py::test_all_checked_is_complete` | umgesetzt |
| Recovery / Checkpoint | `rule` | `CheckpointStore` über `barrier.checkpoint_ref` | `scripts/lib/checkpoint.py::CheckpointStore.save_checkpoint`; `rules/1-generic/plan-ledger.md` (Abschnitt `Ledger`) | `scripts/lib/orchestration.py::FanoutTask.checkpoint_ref` | `tests/test_plan_ledger.py::test_checkpoint_store_round_trip_is_recovery_source` | umgesetzt |
| Archiv (plan-complete) | `config` | `spec-plan-workflow.archive.*` (mode/agent/trigger/target) | `config/project-config.schema.json:1822` (archive-Block); `rules/1-generic/plan-ledger.md` (Abschnitt `Archiv-Trigger`) | `agents/1-generic/orchestrator.md` (Agenten-Pfad, kein Sync-Schritt) | `tests/test_spec_plan_config_schema.py::test_spec_plan_workflow_block_valid` | umgesetzt |
| Index + Fallback-Index | `config` | `spec-plan-workflow.index.mode` → `file-index`-Fallback | `scripts/lib/spec_plan_scaffold.py::resolve_index_mode` | `scripts/lib/spec_plan_scaffold.py::scaffold_spec_plan_dirs` | `tests/test_spec_plan_scaffold.py::test_index_mode_defaults_to_knowledge_engine`; `tests/test_spec_plan_scaffold.py::test_ke_off_forces_file_index` | umgesetzt |
| KE-Concept-Types (`plan`, `spec`) | `config` | `DOMAIN_CONCEPT_TYPES` (`internal-docs`) | `scripts/lib/knowledge.py::DOMAIN_CONCEPT_TYPES` (`plan`, `spec`) | `scripts/lib/knowledge.py::generate_schema` | `tests/test_knowledge_engine.py::test_domain_concept_types_has_all_domains`; `tests/test_knowledge_engine.py::test_generate_schema_renders_domain_and_concept_types` | umgesetzt |
| Regel-Gating (`rules-channel`) | `config` | `rule-gate` — fail-closed auf `spec-plan-workflow.enabled` | `config/spec-plan-groups.yaml#plan-mode.aspects.rules-channel`; `scripts/lib/rules.py::_rule_gate_satisfied` | `scripts/lib/rules.py::collect_rule_sources` | `tests/test_rules_activation_gate.py::test_gate_removes_rule_when_disabled_in_every_preset`; `tests/test_spec_plan_group_consistency.py::test_consumer_ratchet` | umgesetzt |
| Pipeline-Gating (`pipeline-gating`) | `pipeline` | `pipeline-stage-condition` (`dod_flag: spec-plan-enabled`) | `config/spec-plan-groups.yaml#plan-mode.aspects.pipeline-gating`; `config/role-defaults.yaml:2480` (`quality_pipelines.concept-driven-dev`); `scripts/lib/pipelines.py::_generate_pipeline_block` | `scripts/lib/pipelines.py::inject_pipeline_blocks` | `tests/test_pipelines.py::test_concept_driven_dev_spec_plan_hidden_when_disabled`; `tests/test_spec_plan_group_consistency.py::test_consumer_ratchet` | umgesetzt |
| Scaffold (neutrale Pfade) | `config` | `sync-scaffold` — legt `docs/specs` / `docs/plans` / `docs/spikes` + `.gitkeep` an | `config/spec-plan-groups.yaml#plan-mode.aspects.scaffold`; `scripts/lib/spec_plan_scaffold.py::scaffold_spec_plan_dirs` | Sync-Pipeline (`scripts/lib/sync_pipeline.py`) | `tests/test_spec_plan_scaffold.py::test_enabled_scaffolds_all_paths`; `tests/test_spec_plan_group_consistency.py::test_consumer_ratchet` | umgesetzt |
| DoD-Kopplung (`spec-plan-required`/`-traceability`) | `config` | DoD-Flags + Preset `concept-driven` | `config/dod-presets.yaml:91` (Preset `concept-driven`); `scripts/lib/dod.py::resolve_dod` | `scripts/lib/dod.py::resolve_spec_plan_bundle` | `tests/test_spec_plan_config_schema.py::test_concept_driven_preset_requires_spec_plan`; `tests/test_spec_plan_config_schema.py::test_dod_preset_enum_includes_concept_driven` | umgesetzt |
| Template-Conditional (`template-conditional`) | `config` | `SPEC_PLAN_WORKFLOW_ENABLED` + `{{#if}}`-Block | `config/spec-plan-groups.yaml#plan-mode.aspects.template-conditional`; `scripts/lib/config.py::_build_dod_variables` | `scripts/lib/variables.py::strip_inactive_conditional_blocks` | `tests/test_spec_plan_conditional_flag.py::test_conditional_true_keeps_block`; `tests/test_spec_plan_group_consistency.py::test_consumer_ratchet` | umgesetzt |
| Consistency-Noop (`consistency-noop`) | `config` | `validator-noop` — leere Findings bei Seed `false` | `config/spec-plan-groups.yaml#plan-mode.aspects.consistency-noop`; `scripts/lib/consistency/spec_plan.py::check_spec_plan_workflow` | `scripts/lib/spec_plan_validate.py::validate_spec_plan` | `tests/test_spec_plan_consistency.py::test_disabled_returns_empty`; `tests/test_spec_plan_group_consistency.py::test_consumer_ratchet` | umgesetzt |
| KE-Auto-Index (`ke-auto-index`) | `config` | `knowledge-engine-auto-write` — `index.md`-Auto-Write | `config/spec-plan-groups.yaml#plan-mode.aspects.ke-auto-index`; `scripts/lib/knowledge.py::sync_knowledge_engine` (`okf.auto-index`) | `agents/1-generic/knowledge-ingestor.md` | `tests/test_spec_plan_group_consistency.py::test_seed_matrix`; `tests/test_knowledge_engine.py::test_auto_flags_true_keep_scaffolded_files_without_agent_driven_note` | umgesetzt (config-gekoppelt) |
| KE-Auto-Log (`ke-auto-log`) | `config` | `knowledge-engine-auto-write` — `log.md`-Auto-Write | `config/spec-plan-groups.yaml#plan-mode.aspects.ke-auto-log`; `scripts/lib/knowledge.py::sync_knowledge_engine` (`okf.auto-log`) | `agents/1-generic/planner.md` | `tests/test_spec_plan_group_consistency.py::test_seed_matrix`; `tests/test_knowledge_engine.py::test_auto_flags_false_keep_scaffolded_files` | umgesetzt (config-gekoppelt) |
| DoD-Traceability (`dod-traceability`) | `config` | `dod-flag` — `resolve_spec_plan_bundle` liefert `seed and dod.spec-plan-traceability` | `config/spec-plan-groups.yaml#plan-mode.aspects.dod-traceability`; `scripts/lib/consistency/spec_plan.py::check_spec_plan_workflow` liest `bundle["dod-traceability"]` | `scripts/lib/consistency/spec_plan.py::check_spec_plan_workflow` | `tests/test_spec_plan_config_schema.py::test_full_preset_defines_both_keys`; `tests/test_spec_plan_group_consistency.py::test_consumer_ratchet`; `tests/test_spec_plan_group_consistency.py::test_dod_traceability_aspect_follows_resolved_flag` | umgesetzt |
| Review-Loop (`reflection_pairs.concept-specify-loop`) | `reflection-pair` | `loop_ref` → `resolve_stage_loop` | `config/role-defaults.yaml:2343` (`reflection_pairs.concept-specify-loop`); `scripts/lib/reflection.py::resolve_stage_loop` | `scripts/lib/pipelines.py::_generate_pipeline_block` | `tests/test_pipelines.py::test_resolve_stage_loop_concept_driven_dev_review_ratchet`; `tests/test_pipelines.py::test_loop_ref_renders_resolved_generator_critic_and_max_iterations` | umgesetzt |
| Pipeline `concept-driven-dev` | `pipeline` | `quality_pipelines.concept-driven-dev` (explore → classify → specify → review → approve → plan → implement → validate) | `config/role-defaults.yaml:2480` | `scripts/lib/pipelines.py::load_quality_pipelines`; `scripts/lib/pipelines.py::inject_pipeline_blocks` | `tests/test_pipelines.py::test_concept_driven_dev_spec_plan_stage_order` | umgesetzt |
| Pipeline `concept-development` (Spike) | `pipeline` | `quality_pipelines.concept-development` (Recherche-Pfad, kein Plan) | `config/role-defaults.yaml:2454` | `scripts/lib/pipelines.py::load_quality_pipelines` | `tests/test_frontmatter_parity.py::test_ideation_maps_task_sizes_to_classes`; `tests/test_agents_frontmatter.py::test_explorer_documents_spike_mode` | umgesetzt |
| Gruppierung / Bundle-Seed (`enabled`) | `resolver` | `resolve_spec_plan_bundle` — ein Seed, alle Aspekte | `config/spec-plan-groups.yaml#plan-mode.seed`; `scripts/lib/dod.py::resolve_spec_plan_bundle` | `scripts/lib/dod.py::resolve_spec_plan_enabled`; `scripts/lib/dod.py::resolve_dod` | `tests/test_spec_plan_resolve_enabled.py::test_wrapper_matches_bundle_enabled`; `tests/test_spec_plan_group_consistency.py::test_seed_sources_and_default_declared` | umgesetzt |
| `--validate-spec-plan` (CLI-Gate) | `test` | Standalone-, read-only Validator-Modus | `scripts/sync.py:156` (Argument); `scripts/lib/spec_plan_validate.py::validate_spec_plan` | CLI / CI | `tests/test_spec_plan_validate_cli.py::test_flag_registered_in_parser`; `tests/test_spec_plan_validate_cli.py::test_changed_artifact_in_scope_detects_placeholder` | umgesetzt |
| Routing-Single-Source / Route-Guard | `test` | `no-role-routes`-Guard — Routing nur in `config/role-defaults.yaml` | `tests/test_no_role_routes_in_templates.py::find_findings` | CI / pytest | `tests/test_no_role_routes_in_templates.py::test_no_uncovered_role_routes_in_templates`; `tests/test_no_role_routes_in_templates.py::test_next_role_labels_absent_in_spec_plan_workflow_scope` | umgesetzt |
| Naming / Pfade (`spec-plan-workflow.paths`) | `config` | Neutrale Defaults `docs/specs` / `docs/plans` / `docs/spikes`, kein Legacy-Schema-Default | `scripts/lib/spec_plan_scaffold.py::DEFAULT_SPECS_DIR`; `config/project-config.schema.json:1822` | `scripts/lib/spec_plan_scaffold.py::scaffold_spec_plan_dirs` | `tests/test_spec_plan_config_schema.py::test_spec_plan_workflow_defaults_contain_no_legacy_path`; `tests/test_spec_plan_config_schema.py::test_project_structure_lists_spec_plan_paths` | umgesetzt |

### 3.1 Aspekt-Abdeckung von `config/spec-plan-groups.yaml`

Alle deklarierten Aspekte besitzen genau eine Matrixzeile:

| Aspect-ID | Matrixzeile |
|---|---|
| `rules-channel` | Regel-Gating (`rules-channel`) |
| `pipeline-gating` | Pipeline-Gating (`pipeline-gating`) |
| `scaffold` | Scaffold (neutrale Pfade) |
| `template-conditional` | Template-Conditional (`template-conditional`) |
| `consistency-noop` | Consistency-Noop (`consistency-noop`) |
| `ke-auto-index` | KE-Auto-Index (`ke-auto-index`) |
| `ke-auto-log` | KE-Auto-Log (`ke-auto-log`) |
| `dod-traceability` | DoD-Traceability (`dod-traceability`) |

Der Seed selbst (`enabled`) ist über die Zeile „Gruppierung / Bundle-Seed“ abgedeckt.

## 4. Bewusste Ausnahmen

Diese Nennungen bleiben bestehen und sind **kein** Prozess-Routing und **kein** Bezug des
Spec/Plan-Workflows.

**(a) `native-extensions`-Whitelist-Beispiel (bewusste Ausnahme, §D.4).**
Einzige erlaubte Nennung eines realen externen Plugin-Namens ist das Whitelist-Beispiel in
`docs/superpowers/plans/2026-07-23-native-extensions-whitelist.md:152`
(`native-extensions.whitelist: ["<externer Plugin-Name>", "code-simplifier"]`). Es ist ein
Dokumentations-Beispiel für die generische Whitelist-Property und wird **nicht** gepurged.
Der reale Fremd-Name ist hier absichtlich nicht ausgeschrieben; maßgeblich ist die
Fundstelle `…native-extensions-whitelist.md:152`.

**(b) `docs/superpowers/*`-Pfade bleiben read-only.**
Die Pfad-Wurzeln `docs/superpowers/specs` und `docs/superpowers/plans` sind **Pfade**, kein
Prosa-Name, und bleiben in diesem Schritt unverändert (der Pfad-Purge ist ein späterer
Task, §D.1). Legacy-Artefakte werden nicht verschoben; der Scan-Scope bleibt unverändert.
Der Route-/Purge-Guard darf Vorkommen innerhalb von Repo-Pfad-Tokens nicht flaggen.

**(c) `.meta-config/project.yaml` expliziter Legacy-Pointer bleibt.**
`.meta-config/project.yaml:63-65` deklariert `spec-plan-workflow.paths.legacy` explizit
(Projekt-Config, **kein** Schema-Default). Diese Deklaration bleibt bestehen; der
Schema-Default des Feldes ist dagegen leer (`[]`) — abgesichert durch
`tests/test_spec_plan_config_schema.py::test_spec_plan_workflow_defaults_contain_no_legacy_path`.

**(d) `D-ORCHESTRATOR` — Orchestrator-Routing ist erlaubt (H1, Decision A).**
`agents/1-generic/orchestrator.md` ist die **eine** dokumentierte Ausnahme vom
Routing-Verbot: der Orchestrator ist der Router, seine Task-Size-Routing-Tabelle
(`:112-121`), das Routing-Gate (`§0`) und das Tier-/Eskalations-Routing sind
beabsichtigt. Der Route-Guard `tests/test_no_role_routes_in_templates.py` gewährt
deshalb für genau diese Datei die `D-ORCHESTRATOR`-Regel (datei-weit, analog §A.4
im Design). Die frühere zeilenweite `D-ESCALATION`-Ausnahme ist auf eine enge,
rollen-gebundene Regel reduziert (`principal-developer`-Ziel + Eskalations-Policy).
Die `→ delegiere ZUERST an \`planner\``-Plan-driven-Gate-Zeile des Orchestrators
bleibt damit gültig.

## 5. Lücken / Follow-ups

- **F1 (`systems-engineering`-Schema):** Der `systems-engineering`-Block bleibt undeklariert
  und wird vom Top-Level-`additionalProperties: true`
  (`config/project-config.schema.json:2105`) toleriert. Die Deklaration ist bewusst
  **nicht** Teil dieses Vorhabens; bis dahin ändert sich nichts. Keine Matrixzeile, da kein
  Spec/Plan-Workflow-Mechanismus. Die Issue-Erstellung ist separat (nicht Teil des Plans).
- **R6-3 (`loop_ref` additiv):** `bugfix`/`concept-development` bleiben vorerst bei inline
  `loop:`; eine Migration ist **nicht** Teil dieses Vorhabens. Die neue Pair-Zeile deckt nur
  `concept-specify-loop` ab.
- **R6-2 (Route-Guard heuristisch):** Der Guard ist eine Regex-/Scope-Heuristik, keine
  vollständige Sprach-Analyse (Convention boundary, analog `orchestrator-guard.sh`).
  Seit M1 matcht `T-ROLE-ARROW` Rollen-Tokens mit **optionalen** Backticks (nur wenn beide
  Seiten Rollen sind), `T-HANDOFF` zusätzlich `hand back to` und deutsche Artikel
  (`den|dem|einen`). `D-PIPELINE` ist konstrukt- statt zeilenweit, `D-ESCALATION` ist eng
  rollen-gebunden, und `D-ORCHESTRATOR` ist die dokumentierte Orchestrator-Ausnahme (§4d).
  Ein negativer Anker (`test_canonical_offender_lines_are_flagged`) verhindert, dass eine
  spätere Aufweichung der D-*-Regeln den Guard still abschaltet.

## 6. Pflege-Regel

1. Ein **neuer Prozess-Aspekt** des Spec/Plan-Workflows benötigt in diesem Dokument eine
   **neue Matrixzeile** mit realer `file:symbol`-Fundstelle, Consumer und mindestens einem
   Test — plus einen neuen Aspekt in `config/spec-plan-groups.yaml`.
2. Ein neuer Aspekt ohne Matrixzeile und ohne Test gilt als **nicht abgedeckt**; der
   Consumer-Ratchet `tests/test_spec_plan_group_consistency.py::test_consumer_ratchet` und
   der Route-Guard `tests/test_no_role_routes_in_templates.py` sind die zugehörigen Guards.
3. Änderungen an Mechanismus, `file:symbol` oder Testpfad ziehen die betroffene Zeile
   sofort mit (keine veralteten Symbole).
4. Die Design-Spec (§E) verweist für den Umsetzungsstand auf dieses Dokument; die Matrix
   referenziert umgekehrt die Spec (§D.4/§E) und ist damit die gepflegte
   Coverage-Sicht.
