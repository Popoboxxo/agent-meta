# Context Profiles — Phase 0/1 Implementation Plan

> Status: geplant

**Goal:** Phase 0 (Messen & Absichern: Voraussetzung IC-15 Nr. 26/27, Pakete 0a–0f) und Phase 1 (Kanäle & Korrektheit: Auto-Commit-Allowlist, Active-Set-Konsumenten, Provider-Kanal-Fixes) der Spec vollständig umsetzen; Phase 2/3 als Roadmap.
**Architecture:** Reine Prüf-/Mess-Module (`active_set.py`, `doctor.py`, `consistency/*`) mit IC-10-Signatur, Daten in `config/*.yaml`, ein `ActiveSet` je Sync für alle IC-18-Konsumenten, alle neuen Ausgaben nur im konfigurierten tmp-sink (IC-34).
**Tech Stack:** Python 3.9/3.11/3.12 (Stdlib + PyYAML), pytest, Bash-Szenarien (`tests/scenarios/run.sh`), Promptfoo (nur Eval, nur nach Freigabe).
**Spec:** `docs/specs/2026-10-11-context-profiles-spec.md` — `spec-id: SPEC-CONTEXT-PROFILES-2026-10-11` (Rev. 3.4, APPROVED)
**Tracking:** #977

## Global Constraints

- Task-Titel = Ziel des Tasks (ein Satz); Detailinhalt steht in der Spec unter den genannten IC-/AC-IDs.
- Provider-agnostisch: Unterschiede nur über Capability-/Config-Keys (`config/ai-providers.yaml`, `config/provider-capabilities.yaml`), nie `if provider == "Name"`; `tests/test_provider_agnostic_dispatch.py::test_no_provider_literal_usage_in_lib` bleibt grün (AC-36, AC-61).
- Python-3.9-kompatibel (`scripts/lib/consistency/python_compat.py` grün), in `scripts/lib` nur Stdlib + PyYAML; externer Tokenizer nur unter `tests/manual/`.
- TDD: jeder Task beginnt mit einem roten Test; der red-before-green-Nachweis (Testlauf vor/nach) steht in der PR-Beschreibung (AC-10, QG-8).
- AC-01 gilt für jeden Phase-0-PR: Render byte-identisch gegen das Hash-Manifest aus Task 0a.0; Golden-Rebaseline nur dort, wo die AC-01-Ausnahmeliste (i)–(v) bzw. ein Phase-1-Fix sie ausdrücklich erlaubt (IC-15 Nr. 11, IC-18 Nr. 2–8, IC-31-EN/DE-PR), jeweils mit Begründung im PR.
- Jedes Paket = eigener PR (AC-87); Phase 1: je Fix/Konsument eigener PR. PR-Beschreibung nennt Paket, ACs, DAG-Nachweis und `Closes #…` nur im abschließenden Task.
- Ausgaben/Arbeitsverzeichnisse neuer Werkzeuge nur über `resolve_output_dir`/`resolve_work_dir` (Task 0a.6); kein `.tmp`-Literal, kein `tempfile`/`/tmp`/`%TEMP%`/`TMPDIR` in neuen Modulen (AC-75, AC-94). Tests nutzen pytest-`tmp_path` (`tests/conftest.py`).
- LLM-Evals (IC-13/QG-1/QG-14) nur nach ausdrücklicher Nutzerfreigabe mit vorab angezeigter Kostenschätzung; Ablehnung ⇒ `SKIPPED-BY-USER`, Gate „nicht belegt" (IC-36).
- Version-Bumps berührter Templates und `CHANGELOG.md`-Unreleased-Eintrag je PR nach `.claude/skills/conventions/SKILL.md`; Hook-Versionen nach `check_stale_deployed_hooks` (`scripts/lib/consistency/hook_drift.py`).
- Commits: Conventional Commits (`feat`/`fix`/`chore`), Englisch, ≤ 72 Zeichen; Commit durch die per `auto_commit` freigeschaltete Rolle bzw. den Orchestrator; Push/PR/Branches nur `git`.
- Zeilenangaben der Spec sind Orientierung; maßgeblich sind Funktionsnamen (K-f).

## Ausführungsmodell

- DAG: `#963 (0a-I, 0a-II) → 0a-III (#964) → 0b → 0d → 0e`; `0c → 0e`; `0a-III → 0f`. 0c/0f laufen parallel. Phase 1 startet mit Task 1.01 (#970), sobald 0b gemergt ist.
- Merge-Reihenfolge 0c vor 0b: einzige paketübergreifende Datei-Überschneidung sind `config/active-set-references.yaml` und `scripts/lib/consistency/placeholders.py` (0c.1/0c.3 ↔ 0b.1/0b.3); 0b rebast nach dem 0c-Merge.
- Parallelität nur innerhalb eines `parallel_group` mit disjunkter Ownership laut `Files:` (Prüfung `check_plan_file_overlap`, `scripts/lib/orchestration.py`); Tasks ohne Gruppe laufen sequenziell.
- Ausführung nach Skill `plan-ledger`: frischer Subagent je Task, zweistufiges Review (req → quality), Ledger = Checkboxen dieser Datei, **kein** `isolation: "worktree"`.
- Branches je PR nach `.claude/rules/branch-guard.md` (`feat/`, `fix/`, `chore/` + Issue-Nr., z. B. `fix/963-tmp-sink-default-on`). Offene Nutzerfrage zur Session-Branch-Vorgabe `claude/adoring-keller-c12ws0`: siehe Planende.

## File Structure

- Create: `docs/plans/2026-10-11-context-profiles-plan.md` — dieser Plan (Ledger)
- Modify: `scripts/lib/gitignore.py` — `_tmp_sink_gitignore_entry` Default AN (IC-15 Nr. 26)
- Modify: `scripts/lib/repo_containment.py` — Pfad-Härtung, `tmp_sink_location_error`, `resolve_output_dir`, `resolve_work_dir` (IC-15 Nr. 27, IC-34)
- Modify: `scripts/lib/config.py` — Migrationsfehler (Nr. 27 h), `TMP_SINK_PATH`, Builder-Umstellungen (IC-18 Nr. 5–7/12/18, IC-15 Nr. 11/12/17)
- Modify: `hooks/1-generic/repo-containment-impl.sh` — Hook-Spiegel, `# version: 1.1.0`
- Modify: `scripts/lib/progress_paths.py` — `progress_path_error` mit gleichem Regelsatz
- Modify: `config/provider-capabilities.yaml`, `config/ai-providers.yaml` — IC-09-Keys, Provider-Fixes (IC-15 Nr. 2–9, 13, 16, 21–22)
- Create: `scripts/lib/context_report.py` — `measure_artifacts`, `--context-report` (IC-11)
- Modify: `scripts/measure_context.py` — nutzt `measure_artifacts`
- Modify: `scripts/sync.py` — `--context-report`, `--doctor`, `--check`-Hilfetext, IC-18 Nr. 16
- Modify: `scripts/lib/cli_commands.py` — `_handle_context_report`, `_handle_doctor`, `_SyncContext.active_set`
- Create: `config/context-anchors.yaml` — IC-12
- Create: `scripts/lib/active_set.py` — IC-17
- Create: `scripts/lib/consistency/context_budget.py` — IC-10/IC-33-Checks
- Create: `scripts/lib/consistency/active_set_refs.py` — IC-19-Checks, `routing.keyword-overlap`
- Create: `scripts/lib/consistency/provider_literals.py` — `templates.provider-literal` (IC-32)
- Modify: `scripts/lib/consistency/frontmatter.py` — `frontmatter.based-on-stale`
- Modify: `scripts/lib/consistency/placeholders.py` — `builder-known-set`, `ROLE_*_ACTIVE`, `ACTIVE_ROLES`, `TMP_SINK_PATH`
- Modify: `scripts/lib/variables.py` — Konditional-Whitelist (`ROLE_*_ACTIVE`)
- Create: `config/active-set-references.yaml` — `dispatch_phrases`, `provider_literal_allow`, `placeholder_allow`, `mention_allow`
- Create: `config/routing-language.yaml` — `keyword_allow` (IC-29)
- Modify: `scripts/lib/delegation_table.py` — Fallback-Log, IC-18 Nr. 1/4, IC-15 Nr. 15, IC-29
- Modify: `scripts/lib/sync_pipeline.py` — Check-Lauf am Sync-Ende, IC-18 Nr. 14
- Create: `config/known-issues.yaml` — IC-21-Registry
- Create: `scripts/lib/doctor.py`, `scripts/lib/doctor_detectors.py` — IC-22
- Create: `agents/1-generic/meta-doctor.md` — IC-23
- Modify: `config/role-defaults.yaml` — `meta-doctor`, IC-15 Nr. 14/15, IC-29-Daten, IC-30-Triage
- Modify: `agents/1-generic/agent-meta-manager.md` — `doctor-findings-v1`-Consumer
- Modify: `config/project-config.schema.json`, `standalone/README.md`; Create `standalone/agents/meta-doctor.md` — IC-28 Nr. 3/5
- Create: `tests/scenarios/configs/77-meta-doctor-role.project.yaml`, `tests/scenarios/asserts/77-meta-doctor-role.sh`; Modify `tests/scenarios/registry.md`
- Modify: `rules/2-platform/agent-meta-conventions.md` — IC-28-Checkliste
- Modify: `docs/api/cli-reference.md`, `docs/providers/codex.md`, `docs/providers/gemini-cli.md`, `docs/providers/kimi-code.md`, `docs/guides/setup/instantiate-project.md`, `README.md`, `CHANGELOG.md`
- Create: `docs/analysis/2026-10-11-context-tokenizer-measurement.md`, `tests/manual/measure_tokens.py` — AC-05
- Create: `scripts/gen_role_routing_eval_catalog.py`, `scripts/lib/eval_gate.py` — IC-13/IC-36
- Create: `tests/routing-llm-eval/roles/catalog.generated.yaml`, `tests/routing-llm-eval/roles/catalog.manual.yaml`, `tests/routing-llm-eval/roles/promptfooconfig.generated.yaml`, Verzeichnisse `tests/routing-llm-eval/roles/baseline/`, `tests/routing-llm-eval/roles/runs/`
- Modify: `scripts/lib/pipelines.py` — `filter_pipelines_by_active_set`, `allowed_agents`
- Modify: `scripts/lib/agent_sync.py` — Pipeline-`effective`, Agent-Name-Fix
- Modify: `agents/1-generic/orchestrator.md`, `agents/1-generic/developer.md`, `agents/1-generic/planner.md`, `templates/direct-dispatch-section.md`, `templates/context/partials/agents-table.md`, `templates/context/partials/header.md`, `rules/1-generic/security-paved-roads.md`, `rules/1-generic/threat-model.md`, `rules/1-generic/a2a-delegation-gates.md`, `rules/1-generic/use-lazy-rules.md`, betroffene `agents/1-generic/*.md`, `agents/2-platform/*.md`, `commands/**`
- Modify: `scripts/lib/commands.py`, `scripts/lib/consistency/commands.py` — `requires_roles`
- Modify: `scripts/lib/context.py`, `scripts/lib/rules.py`, `scripts/lib/skills.py`, `scripts/lib/provider_transform.py`, `scripts/lib/bootstrap.py`, `config/provider-bootstrap.yaml`, `config/delegation-syntax.yaml`, `scripts/lib/extensions.py`, `templates/managed-block.md`, `scripts/hermes_export.py`
- Create: `scripts/lib/dispatch_depth.py` — capability-getriebene Dispatch-Tiefe (`[agents] max_depth`)
- Create: `snippets/agents/closing-summary.md`, `snippets/agents/user-proxy.md` — IC-31
- Create: `agents/2-platform/agent-meta-mammouth-expert.md` — IC-15 Nr. 23
- Create (Tests Phase 0): `tests/test_ac01_render_identity.py`, `tests/fixtures/ac01-baseline/hashes.json`, `tests/test_tmp_sink_default_on.py`, `tests/test_tmp_sink_path_hardening.py`, `tests/fixtures/tmp-sink-path-corpus.json`, `tests/test_tmp_sink_path_parity.py`, `tests/test_tmp_sink_migration_error.py`, `tests/test_capability_keys_ic09.py`, `tests/test_tmp_sink_output_dirs.py`, `tests/test_context_report.py`, `tests/test_context_anchors.py`, `tests/test_context_budgets.py`, `tests/test_context_docs_corrections.py`, `tests/test_active_set.py`, `tests/fixtures/active-set/p10/.meta-config/project.yaml` (analog `p20`, `pall`, `ha`), `tests/test_context_budget_checks.py`, `tests/test_active_set_dangling.py`, `tests/test_active_set_single_source.py`, `tests/test_routing_keywords_language_neutral.py`, `tests/test_routing_keyword_overlap_check.py`, `tests/test_sync_end_checks.py`, `tests/test_template_integrity_checks.py`, `tests/test_known_issues_registry.py`, `tests/test_doctor_runner.py`, `tests/test_doctor_cli.py`, `tests/test_doctor_fixtures.py`, Fixture-Baum `tests/fixtures/doctor/` (je Seed-ID aus IC-21 ein Unterverzeichnis mit `positive/` und `negative/`), `tests/test_meta_doctor_role.py`, `tests/test_role_routing_eval_catalog.py`, `tests/test_eval_gate.py`
- Create (Tests Phase 1): je Task unter `**Files:**` genannt
- Modify (Tests): `tests/test_repo_containment_tmp_sink.py`, `tests/test_repo_containment_hook.py`, `tests/test_progress_paths.py`, `tests/test_no_role_routes_in_templates.py`, `tests/test_role_addressability_coverage.py`, `tests/test_template_slimming_equivalence.py`, `tests/fixtures/slimming-golden/orchestrator.md`, `tests/test_provider_matrix_sync.py`, `tests/test_delegation_table.py`, `tests/test_routing_tool_definitions.py`, `tests/test_routing_overlap.py`, `tests/test_developer_tiers_gate.py`, `tests/test_contract_labels.py`, `tests/test_pipelines.py`, `tests/test_auto_commit_allowlist_pipeline.py`, `tests/scenarios/asserts/76-template-auditor-role.sh`

---
pipeline_stages:
  implement: 3
---

## Phase 0

### Task 0a.0: AC-01-Harness (Render-Hash-Manifest) anlegen
Rolle: tester · Issue: #963 · PR: 0a-I · Depends: — · AC: AC-01 · Falle: Manifest auf `main` vor jeder Änderung erzeugen; Ausnahmeliste (i)–(v) als Daten im Test.
**Files:** Create `tests/test_ac01_render_identity.py`, `tests/fixtures/ac01-baseline/hashes.json`
**Interfaces:** Produces `tests/test_ac01_render_identity.py::render_matrix_hashes(fixture_root: Path) -> dict[str, str]`, `AC01_EXCEPTIONS: frozenset[str]`; Consumes Provider-Matrix-Fixtures aus `tests/test_provider_matrix_sync.py`
- [ ] Step 1: Test schreiben (fail): Meta-Test verändert eine gerenderte Datei ⇒ `test_ac01_detects_drift` muss rot sein
- [ ] Step 2: implementieren (Hash-Manifest + Diff gegen Ausnahmeliste)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_ac01_render_identity.py -q`
- [ ] Step 4: commit `chore: add AC-01 render hash manifest harness`

### Task 0a.1: tmp-sink Default AN ohne Block (IC-15 Nr. 26)
Rolle: developer · Issue: #963 · PR: 0a-I · Depends: 0a.0 · AC: AC-92, AC-01 (iv) · Falle: Aufrufstelle `sync_pipeline.py:319-324` (Claude-Gate) unverändert; bestehende „kein Block ⇒ kein Eintrag"-Pins umstellen.
**Files:** Modify `scripts/lib/gitignore.py`; Test Create `tests/test_tmp_sink_default_on.py`, Modify `tests/test_repo_containment_tmp_sink.py`
**Interfaces:** Produces `gitignore._tmp_sink_gitignore_entry(repo_containment_cfg: dict | None) -> str | None` (None ⇒ `.tmp/`); Consumes `repo_containment.default_repo_containment_block() -> dict`, `gitignore.compute_base_gitignore_entries`
- [ ] Step 1: Test schreiben (fail): `compute_base_gitignore_entries` mit `repo_containment_cfg=None` enthält `.tmp/`; `scratch/out/`; disabled/`gitignore: false` ⇒ kein Eintrag; Dry-Run schreibt nichts
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_tmp_sink_default_on.py tests/test_repo_containment_tmp_sink.py -q`
- [ ] Step 4: commit `fix: default tmp-sink gitignore entry without containment block`

### Task 0a.2: Pfad-Härtung Python (IC-15 Nr. 27 a–e, i)
Rolle: senior-developer · Issue: #963 · PR: 0a-II · Depends: 0a.1 · AC: AC-93 · Falle: Junction per `getattr(pathmod, "isjunction", None)` + Reparse-Point-Fallback (3.9); `tempfile.gettempdir()` nur in `tmp_sink_location_error`.
**Files:** Modify `scripts/lib/repo_containment.py`; Test Create `tests/test_tmp_sink_path_hardening.py`, `tests/fixtures/tmp-sink-path-corpus.json`
**Interfaces:** Produces `tmp_sink_path_error(path: Any, project_root: str | os.PathLike[str] | None = None, *, pathmod=os.path) -> str | None`, `tmp_sink_location_error(path: str, project_root: Path) -> str | None`, `_resolve_sink_dir(project_root, effective, *, pathmod=os.path) -> Path | None`, `ensure_tmp_sink(project_root, effective, dry_run: bool = False) -> Path | None`; Consumes `tests/fixtures/tmp-sink-path-corpus.json`
- [ ] Step 1: Test schreiben (fail): parametrisierte AC-93-Fälle (posixpath/ntpath), Symlink-/Junction-/Fallback-Fälle, TOCTOU-Test-Hook
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_tmp_sink_path_hardening.py -q`
- [ ] Step 4: commit `fix: harden tmp-sink path validation for posix and windows`

### Task 0a.3: Harter Migrationsfehler für unsichere Bestands-Pfade (IC-15 Nr. 27 h)
Rolle: developer · Issue: #963 · PR: 0a-II · Depends: 0a.2 · AC: AC-99, AC-01 (v)
**Files:** Modify `scripts/lib/config.py` (Validierung über `_fail`); Test Create `tests/test_tmp_sink_migration_error.py`
**Interfaces:** Produces Meldung mit Key `repo_containment.tmp-sink.path`, Grund und `Migration:`-Vorschlag über `_fail(message: str) -> None`; Consumes `tmp_sink_path_error`, `tmp_sink_location_error`
- [ ] Step 1: Test schreiben (fail): `C:\x`, `\\server\share\x`, `CON`, `.GIT`, Zwischen-Symlink ⇒ Exit ≠ 0, nichts gerendert, Meldung vollständig; Matrix-Fixtures frei davon
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_tmp_sink_migration_error.py -q`
- [ ] Step 4: commit `fix: reject unsafe tmp-sink paths with migration hint`

### Task 0a.4: Hook-Spiegel und progress_paths-Parität (IC-15 Nr. 27 f, g)
Rolle: senior-developer · Issue: #963 · PR: 0a-II · Depends: 0a.2 · AC: AC-97 · Falle: Hook importiert `repo_containment.py` nicht; ungültig ⇒ Rückfall `.tmp`, aber gleiche Entscheidung und kanonische Form.
**Files:** Modify `hooks/1-generic/repo-containment-impl.sh`, `scripts/lib/progress_paths.py`; Test Create `tests/test_tmp_sink_path_parity.py`, Modify `tests/test_repo_containment_hook.py`, `tests/test_progress_paths.py`
**Interfaces:** Produces `progress_path_error(path: object, project_root: Optional[Path] = None, *, pathmod=os.path) -> Optional[str]`, Hook `# version: 1.1.0`; Consumes `tests/fixtures/tmp-sink-path-corpus.json`, `consistency.hook_drift.check_stale_deployed_hooks`
- [ ] Step 1: Test schreiben (fail): Korpus über drei Implementierungen (Hook-Python per Subprozess) identisch; alter Hook-Stand ⇒ Drift
- [ ] Step 2: implementieren (inkl. Hook-Header-Kommentar)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_tmp_sink_path_parity.py tests/test_repo_containment_hook.py tests/test_progress_paths.py -q`
- [ ] Step 4: commit `fix: mirror tmp-sink path rules in hook and progress paths` (PR-Text: `Closes #963`)

### Task 0a.5: IC-09-Capability-Keys als reine Daten einführen
Rolle: developer · Issue: #964 · PR: 0a-III · Depends: 0a.4 · parallel_group: 0a-III-g1 · AC: AC-01, AC-36 · Falle: keine Render-Nutzung; Datenkorrekturen F-17 erst in Phase 1.
**Files:** Modify `config/provider-capabilities.yaml`; Test Create `tests/test_capability_keys_ic09.py`
**Interfaces:** Produces alle Keys der IC-09-Tabelle inkl. `surface_verified_state.context_file`, `legacy_artifacts`, `agent_config_format`; Consumes IC-09
- [ ] Step 1: Test schreiben (fail): jeder Provider hat alle Keys mit gültigem Typ/Enum
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_capability_keys_ic09.py tests/test_ac01_render_identity.py -q`
- [ ] Step 4: commit `feat: add context budget and channel capability keys`

### Task 0a.6: tmp-sink-Ausgabepfade und TMP_SINK_PATH (IC-34)
Rolle: developer · Issue: #964 · PR: 0a-III · Depends: 0a.4 · parallel_group: 0a-III-g1 · AC: AC-75 (Teil), AC-94 (Teil)
**Files:** Modify `scripts/lib/repo_containment.py`, `scripts/lib/config.py` (`build_variables`); Test Create `tests/test_tmp_sink_output_dirs.py`
**Interfaces:** Produces `resolve_output_dir(project_root: Path, config: dict, subdir: str) -> Path`, `resolve_work_dir(project_root: Path, config: dict, subdir: str, run_id: str) -> Path`, Variable `TMP_SINK_PATH`, Fehlercodes `tmp-sink.disabled` und `out-outside-tmp-sink` (Präfix je Werkzeug); Consumes `resolve_effective_repo_containment`, `_resolve_sink_dir`
- [ ] Step 1: Test schreiben (fail): `scratch/out` ⇒ `scratch/out/doctor/r1/work/`; disabled ⇒ Fehler; `--out` außerhalb per `realpath` erkannt
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_tmp_sink_output_dirs.py -q`
- [ ] Step 4: commit `feat: resolve tool output and work dirs via tmp-sink`

### Task 0a.7: `measure_artifacts` und `--context-report` bereitstellen (IC-11)
Rolle: senior-developer · Issue: #964 · PR: 0a-III · Depends: 0a.5, 0a.6 · AC: AC-04, AC-75/AC-94/AC-98 (Report) · Falle: Muster `sync.py:683-692` (Dry-Run + stdout-Umleitung vor `_build_context`).
**Files:** Create `scripts/lib/context_report.py`; Modify `scripts/sync.py`, `scripts/lib/cli_commands.py`, `scripts/measure_context.py`, `docs/api/cli-reference.md`; Test Create `tests/test_context_report.py`
**Interfaces:** Produces `measure_artifacts(project_root: Path, active_providers: Sequence[str], capabilities: Mapping[str, Mapping]) -> dict`, CLI `sync.py --context-report [--json] [--profile full|compact|both]`, `_handle_context_report(ctx: _SyncContext) -> None`; Consumes `resolve_work_dir`, IC-09-Caps
- [ ] Step 1: Test schreiben (fail): Bytes ≤ 1 % Abweichung zu unabhängiger Zählung; nur unter `scratch/out/context-report/`; `tempfile`-Monkeypatch wirft; disabled ⇒ Exit 2; Grep-Guard leer
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_context_report.py -q && python3 scripts/consistency-check.py`
- [ ] Step 4: commit `feat: add --context-report with shared measurement function`

### Task 0a.8: Anker-Registry mit Pflichtankern anlegen (IC-12)
Rolle: developer · Issue: #964 · PR: 0a-III · Depends: 0a.5 · parallel_group: 0a-III-g2 · AC: AC-06
**Files:** Create `config/context-anchors.yaml`; Test Create `tests/test_context_anchors.py`
**Interfaces:** Produces Schema `anchors.{entry-file,claude-md,orchestrator,rules-native,gate-card}.{all-profiles,compact-only}`, `gate_card_sections`, `intentional_unread`, `intentional_empty`; Consumes Provider-Matrix-Renders
- [ ] Step 1: Test schreiben (fail): Pflichtanker (CRITICAL-GATE, Singleton, Contract, MCP-Deny, Branch-Guard, Sprache, Commit) je Provider in `full`
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_context_anchors.py -q`
- [ ] Step 4: commit `feat: add context anchor registry and anchor test`

### Task 0a.9: Budgets je Provider als Obergrenzen pinnen (QG-4)
Rolle: tester · Issue: #964 · PR: 0a-III · Depends: 0a.7 · parallel_group: 0a-III-g2 · AC: AC-07
**Files:** Test Create `tests/test_context_budgets.py`
**Interfaces:** Produces `FULL_BUDGET_CEILINGS: dict[str, dict[str, int]]` (Ist-Werte Spec §2); Consumes `measure_artifacts`
- [ ] Step 1: Test schreiben (fail): künstlich vergrößertes Artefakt über Obergrenze ⇒ rot
- [ ] Step 2: implementieren (Obergrenzen eintragen)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_context_budgets.py -q`
- [ ] Step 4: commit `chore: pin per-provider context budget ceilings`

### Task 0a.10: Doku-Korrekturen und Tokenizer-Messung dokumentieren
Rolle: documenter · Issue: #964 · PR: 0a-III · Depends: 0a.7 · AC: AC-05, AC-09
**Files:** Modify `docs/providers/codex.md`, `docs/providers/gemini-cli.md`, `docs/providers/kimi-code.md`, `scripts/sync.py` (`--check`-Hilfetext), `CHANGELOG.md`; Create `docs/analysis/2026-10-11-context-tokenizer-measurement.md`, `tests/manual/measure_tokens.py`; Test Create `tests/test_context_docs_corrections.py`
**Interfaces:** Produces Hilfetext „`--check` forces dry-run" (`_normalize_check_dry_run`), Messtabelle Bytes/Token je Artefakt; Consumes `measure_artifacts`, K-a…K-c
- [ ] Step 1: Test schreiben (fail): veraltete Aussagen (`use with --dry-run`, `codex.md:118-124`, Kimi-Precedence) vorhanden; Messdoku ohne Orchestrator-/AGENTS.md-Zeile
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_context_docs_corrections.py -q`
- [ ] Step 4: commit `chore: correct context docs and record tokenizer ratios` (PR-Text: `Closes #964`)

### Task 0b.1: ActiveSet-Vertrag und Fixture-Projekte bereitstellen (IC-17)
Rolle: senior-developer · Issue: #965 · PR: 0b · Depends: 0a.10, 0c-Merge · AC: AC-43 (Teil), AC-66 (Teil) · Falle: keine zweite Gate-Logik; `"project"` nur reserviert; keine Konsumenten-Umstellung.
**Files:** Create `scripts/lib/active_set.py`, `tests/fixtures/active-set/{p10,p20,pall,ha}/.meta-config/project.yaml`; Modify `scripts/lib/cli_commands.py`, `scripts/lib/consistency/placeholders.py`, `scripts/lib/variables.py`; Test Create `tests/test_active_set.py`
**Interfaces:** Produces `GateDrop`, `ActiveSet` (IC-17), `compute_active_set(config: dict, agent_meta_root: Path, project_root: Path, *, warn_sink: list[str] | None = None) -> ActiveSet`, `active_set_variables(active: ActiveSet) -> dict[str, str]`, `_SyncContext.active_set`; Consumes `resolve_activation_gates`, `is_role_enabled`, `resolve_active_roles(require_template=True)`
- [ ] Step 1: Test schreiben (fail): p20 ⇒ `gate_dropped` `senior-developer`/`developer_tiers`; unknown-role WARN; Mengen sortiert; `ROLE_*_ACTIVE` für alle `known_roles`
- [ ] Step 2: implementieren (inkl. Eintrag `active_set_variables` in `BUILDERS`)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_active_set.py tests/test_template_integrity_checks.py -q`
- [ ] Step 4: commit `feat: add ActiveSet contract computed once per sync`

### Task 0b.2: Context-Budget-Checks als WARN ergänzen (IC-10)
Rolle: developer · Issue: #965 · PR: 0b · Depends: 0b.1 · parallel_group: 0b-g1 · AC: AC-08
**Files:** Create `scripts/lib/consistency/context_budget.py`; Test Create `tests/test_context_budget_checks.py`
**Interfaces:** Produces `check_over_hard_cap`, `check_over_soft_cap`, `check_dangling_pointer`, `check_rule_unreachable`, `check_unread_channel`, `check_marker_in_rule`, je `(project_root: Path, active_providers: Sequence[str], capabilities: Mapping[str, Mapping], active_set: ActiveSet) -> list[Finding]`; Consumes `measure_artifacts`, `config/context-anchors.yaml`
- [ ] Step 1: Test schreiben (fail): Matrix-Fixture meldet fehlende Skills (Codex/Mammouth/Gemini/Continue), 8 Gemini-lazy-Rules, ≥ 10 fehlende Lazy-Skills
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_context_budget_checks.py -q`
- [ ] Step 4: commit `feat: add context budget and reachability checks as warnings`

### Task 0b.3: Active-Set-Checks ergänzen (IC-19)
Rolle: developer · Issue: #965 · PR: 0b · Depends: 0b.1 · parallel_group: 0b-g1 · AC: AC-43 · Falle: Dispatch-Muster aus `config/delegation-syntax.yaml` + `dispatch_phrases`; fehlendes Muster ⇒ `active-set.dispatch-pattern-missing`.
**Files:** Create `scripts/lib/consistency/active_set_refs.py`; Modify `config/active-set-references.yaml` (`placeholder_allow`, `mention_allow`); Test Create `tests/test_active_set_dangling.py`
**Interfaces:** Produces `check_dangling_dispatch`, `check_dangling_mention`, `check_gate_dropped`, `check_unknown_role`, `check_unresolved_placeholder` (IC-10-Signatur); Consumes `ActiveSet`, Fixtures p10/p20/pall/ha
- [ ] Step 1: Test schreiben (fail): p10 ⇒ Dispatches an die sechs AC-43-Rollen; p20 ⇒ gate-dropped; pall ⇒ `{{EXTRA_DONTS}}`
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_active_set_dangling.py -q`
- [ ] Step 4: commit `feat: add active-set dangling and placeholder checks`

### Task 0b.4: Ratchet `active-set.raw-roles-access` einführen (QG-13 statisch)
Rolle: tester · Issue: #965 · PR: 0b · Depends: 0b.1 · parallel_group: 0b-g2 · AC: AC-84 (Start)
**Files:** Test Create `tests/test_active_set_single_source.py`
**Interfaces:** Produces `RAW_ROLES_RATCHET` (F-42: `sync_pipeline.py`, `context.py`, `sync.py`, `skills.py`, `config.py` vier Stellen) und `LEGIT_READERS` (IC-18-Liste mit Begründung); Consumes Grep auf `config["roles"]`/`config.get("roles"`
- [ ] Step 1: Test schreiben (fail): eingefügte Fundstelle in einem Fixture-Modul ⇒ rot
- [ ] Step 2: implementieren (Registry + Ausnahmeliste)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_active_set_single_source.py -q`
- [ ] Step 4: commit `chore: add raw roles access ratchet guard`

### Task 0b.5: Keyword-Overlap-Check, Keyword-Guard und Fallback-Log (IC-29 Phase 0)
Rolle: developer · Issue: #965 · PR: 0b · Depends: 0b.3 · AC: AC-63, AC-67 (Voraussetzung) · Falle: Log-Teil ändert nur `sync.log`, keinen Render (`_select_examples`).
**Files:** Modify `scripts/lib/consistency/active_set_refs.py`, `scripts/lib/delegation_table.py`; Create `config/routing-language.yaml`; Test Create `tests/test_routing_keywords_language_neutral.py`, `tests/test_routing_keyword_overlap_check.py`
**Interfaces:** Produces `check_keyword_overlap(project_root: Path, active_providers: Sequence[str], capabilities: Mapping[str, Mapping], active_set: ActiveSet) -> list[Finding]`, INFO `routing.examples-language-fallback` in `sync.log`, `keyword_allow`; Consumes `ActiveSet.routable`, `KNOWN_KEYWORD_OVERLAPS`
- [ ] Step 1: Test schreiben (fail): pall ⇒ 9 Tokens, p10 ⇒ nur aktive Paare; Umlaut-Keyword ohne Allowlist ⇒ rot; Fallback-Zeile im Log
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_routing_keywords_language_neutral.py tests/test_routing_keyword_overlap_check.py -q`
- [ ] Step 4: commit `feat: add keyword overlap check and language-neutral guard`

### Task 0b.6: Checks am Sync-Ende in sync.log ausführen
Rolle: developer · Issue: #965 · PR: 0b · Depends: 0b.2, 0b.3, 0b.5 · AC: AC-08, AC-43 · Falle: nur WARN/INFO, kein Exit-Code-Wechsel.
**Files:** Modify `scripts/lib/sync_pipeline.py`; Test Create `tests/test_sync_end_checks.py`
**Interfaces:** Produces `_sync_stage_context_checks(agent_meta_root: Path, project_root: Path, config: dict, active_set: ActiveSet, log: SyncLog) -> None`; Consumes Checks aus 0b.2/0b.3/0b.5
- [ ] Step 1: Test schreiben (fail): Sync auf p10 schreibt `active-set.dangling-dispatch` als `[WARN]` in `sync.log`, Exit 0
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_sync_end_checks.py tests/test_ac01_render_identity.py -q`
- [ ] Step 4: commit `feat: run context and active-set checks at sync end` (PR-Text: `Closes #965`)

### Task 0c.1: Template-Routing-Guard erweitern (IC-30)
Rolle: developer · Issue: #966 · PR: 0c · Depends: — · parallel_group: 0c-g1 · AC: AC-64
**Files:** Modify `tests/test_no_role_routes_in_templates.py`; Create `config/active-set-references.yaml` (`dispatch_phrases`, `provider_literal_allow`)
**Interfaces:** Produces `_SCOPE_GLOBS` + `agents/2-platform/*.md`, `rules/2-platform/*.md`; erweitertes `_HANDOFF_RE`; `ROUTE_RATCHET: frozenset[str]` (Datei:Klasse); Consumes `dispatch_phrases.de`, `dispatch_phrases.en`
- [ ] Step 1: Test schreiben (fail): Fixture-Template mit „Delegiere an `tester`" ⇒ rot; #885-Negativanker erkannt
- [ ] Step 2: implementieren (Ratchet mit Ist-Treffern)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_no_role_routes_in_templates.py -q`
- [ ] Step 4: commit `feat: extend template routing guard with ratchet registry`

### Task 0c.2: `frontmatter.based-on-stale` als WARN ergänzen
Rolle: developer · Issue: #966 · PR: 0c · Depends: — · parallel_group: 0c-g1 · AC: AC-65
**Files:** Modify `scripts/lib/consistency/frontmatter.py`; Test Create `tests/test_template_integrity_checks.py`
**Interfaces:** Produces `check_based_on_stale(agent_meta_root: Path) -> list[Finding]`; Consumes `based-on`-Pins in `agents/2-platform/*.md`
- [ ] Step 1: Test schreiben (fail): Anzahl Befunde = berechnete Abweichungen gegen die Basisdateien (kein gepinnter Wert)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_template_integrity_checks.py -k based_on -q`
- [ ] Step 4: commit `feat: warn on stale based-on pins in platform overrides`

### Task 0c.3: `placeholders.builder-known-set` als ERROR im Quell-Repo
Rolle: developer · Issue: #966 · PR: 0c · Depends: 0c.2 · AC: AC-66 · Falle: Builder-Liste erweiterbar; `active_set_variables` ergänzt 0b.1, `resolve_context_profile` Phase 2.
**Files:** Modify `scripts/lib/consistency/placeholders.py`; Test Modify `tests/test_template_integrity_checks.py`
**Interfaces:** Produces `check_builder_known_set(agent_meta_root: Path) -> list[Finding]`, `BUILDERS: list[Callable]`; Consumes `build_variables(config: dict, agent_meta_root: Path, project_root: Path | None = None) -> tuple[dict, list[str]]`
- [ ] Step 1: Test schreiben (fail): neue, nicht registrierte Builder-Variable ⇒ ERROR
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_template_integrity_checks.py -k builder -q`
- [ ] Step 4: commit `feat: derive known placeholder set from variable builders`

### Task 0c.4: `templates.provider-literal` als WARN ergänzen
Rolle: developer · Issue: #966 · PR: 0c · Depends: 0c.1 · AC: AC-64 (Teil), Voraussetzung AC-73
**Files:** Create `scripts/lib/consistency/provider_literals.py`; Test Modify `tests/test_template_integrity_checks.py`
**Interfaces:** Produces `check_provider_literal(agent_meta_root: Path) -> list[Finding]`; Consumes `config/ai-providers.yaml` (Keys, `provider_root_dirs`, `context_file`), `provider_literal_allow`
- [ ] Step 1: Test schreiben (fail): Literal außerhalb `> **Example (provider-specific):**` ⇒ Befund; innerhalb ⇒ keiner
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_template_integrity_checks.py -q`
- [ ] Step 4: commit `feat: warn on provider literals in generic templates` (PR-Text: `Closes #966`)

### Task 0d.1: Known-Issues-Registry mit Phase-0-Seeds anlegen (IC-21)
Rolle: senior-developer · Issue: #967 · PR: 0d · Depends: 0b · AC: AC-37, AC-85 (`command`), AC-78 (Quelle) · Falle: `command`-argv ohne `--dry-run`/`--deactivation-status`; keine Provider-Identitäts-Prädikate.
**Files:** Create `config/known-issues.yaml`; Test Create `tests/test_known_issues_registry.py`
**Interfaces:** Produces alle Pflicht-Seeds (IC-21 inkl. Rev.-3/3.1/3.4-Formalisierung) und Grammatik `value_key`, `pattern_from_config`, `active_role_where`, Map-Wildcard, `verified-state-by-capability`, `any_of`, `source: doctor`; Consumes IC-09-Keys
- [ ] Step 1: Test schreiben (fail): Form, IDs, Enums, Grammatik, `command`-Allowlist, Bindungen
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_known_issues_registry.py -q`
- [ ] Step 4: commit `feat: add known-issues registry with phase-0 seeds`

#### Umsetzungs-Nachzüge Phase 0d (zur Spec-Aufnahme)
Die freigegebene Spec bleibt unverändert; die Umsetzung von Task 0d.1 hat folgende Präzisierungen ergeben, die bei der nächsten Spec-Revision in IC-21 aufzunehmen sind (Validator: `scripts/lib/doctor_registry.py`, Registry-Header: `config/known-issues.yaml`).
1. **Capability-Prädikate auch auf ai-providers.yaml-Keys:** `agent_ext` und `agent-transform.allowed-fields` liegen in `config/ai-providers.yaml`; Capability-Keys lösen gegen die Vereinigung von `provider-capabilities.yaml` und den Provider-Vertragskeys auf.
2. **Bindungen:** zulässig sind `{role}`, `{key}`, `{provider}`, `{tmp_sink}`, `{agents_dir}`, `{extension_dir}`, `{agent_ext}`; `{reason}` und `{length}` nur in `message` (`{length}` = Zeichenanzahl des Variablenwerts, AC-77; nie der Wert). Bindungsreihenfolge: Wildcard-Prädikate/-Detektoren zuerst (binden `{key}`), danach `surface_has_target` als Filter je `{key}`; Mapping-Quelle `surface_target_key(surface)` in `context_budget.py` (entsteht in 0d.4).
3. **`regex`-Felder:** zusätzlich `path`, `path_template`, `default` (Ersatz bei fehlendem Config-Wert), `line_anchored`, `optional_suffix`. Der Runner setzt `re.MULTILINE` und liest Text unnormalisiert; Zeilenende-Muster müssen CRLF tolerieren (`[ \t\r]*$`).
4. **`path-exists`-Felder:** `exclude_glob`, `bind` (bindet den Glob-Stamm; `bind` erfordert `then`), `then` (je gebundenem Wert). `require_suffix_key`-Polarität: Treffer sind Dateien des Globs, deren Name den Suffix aus dem Capability-Key **nicht** trägt.
5. **`yaml-key`:** `subject: capability` liest die Capability-Matrix statt einer Projektdatei; neues Prädikat `surface_has_target: "{key}"` (muss exakt die `{key}`-Bindung sein).
6. **Wert-Dispatch in `verified-state-by-capability`:** `{<capability-key>: {<capability-wert>: <state>}}` (z. B. `context_soft_cap_chars: {4000: DOCUMENTED, 12000: UNVERIFIED}`); fehlt der Wert im Mapping, gilt das Top-Level-`verified-state` als Fallback. Test: Dispatch-Schlüssel entsprechen den tatsächlichen Capability-Werten.
7. **Config-Prädikat `default`:** `{config: <pfad>, op: ne, value: false, default: true}`; fehlender Pfad gilt als `default`.
8. **`finding-ref`:** `source: sync-log` verweist auf ein Check-Literal im Sync-Log-Producer (`delegation_table.py`); `source: doctor` erfordert eine `doctor.*`-Check-ID (Runner-eigen: `doctor.environment`, `doctor.tmp-sink-location`). Check-IDs ohne Producer (`context.declared-surface-empty`, `context.legacy-artifact-present`) stehen in `_PENDING_0D4` im Registry-Test und werden in 0d.4 entfernt.
9. **Dedupe:** `variable-unreferenced` (Key `*`) überspringt Variablen mit eigenem Seed (aktuell `CODE_QUALITY_RULES` → `dead-variable-code-quality-rules`).
10. **`schema_from_key`-Ableitung und Deckel-Lint:** das JSON-Schema wird aus dem Capability-Wert abgeleitet (Feldliste ⇒ `properties` + `additionalProperties: false`); ein Eintrag mit `verified-state: UNVERIFIED` darf nicht Severity `ERROR` deklarieren (ADR-11-Deckel, Validator-Lint). Evidenz-`date` ist ein gequoteter String.

### Task 0d.2: Doctor-Runner und Detektoren implementieren (IC-22)
Rolle: senior-developer · Issue: #967 · PR: 0d · Depends: 0d.1 · AC: AC-40, AC-41, AC-78, AC-96 · Falle: `finding-ref` importiert IC-10/IC-19-Funktionen; Sink-Prüfung nur über `tmp_sink_path_error`/`tmp_sink_location_error`; `doctor.py` ≤ 600 Zeilen.
**Files:** Create `scripts/lib/doctor.py`, `scripts/lib/doctor_detectors.py`, `scripts/lib/doctor_predicates.py` (Prädikate, Bindungen, Verified-State, `Env`), `scripts/lib/doctor_formats.py` (TOML-/JSON-Schema-Subset, `clip`, Versionsordnung); Test Create `tests/test_doctor_runner.py`
**Interfaces:** Produces `DoctorFinding`, `DoctorReport`, `load_known_issues(agent_meta_root: Path) -> tuple[list[dict], list[DoctorFinding]]`, `run_doctor(project_root: Path, agent_meta_root: Path, config: dict, *, providers: Sequence[str] | None = None) -> DoctorReport`, `print_doctor_json(report: DoctorReport) -> int`; Consumes `measure_artifacts`, `compute_active_set`, Checks aus 0b
- [ ] Step 1: Test schreiben (fail): UNVERIFIED-Deckel, Severity-Abgleich, Import-Test, Projekt-`known-issues.yaml` ignoriert, `quoted` ≤ 120 Zeichen
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_doctor_runner.py -q`
- [ ] Step 4: commit `feat: add doctor runner with registry-driven detectors`

#### Umsetzungs-Nachzüge 0d.2 (zur Spec-Aufnahme)
Die freigegebene Spec bleibt unverändert; die Umsetzung von Task 0d.2 hat folgende Präzisierungen ergeben (IC-21/IC-22).
1. **Finding-Felder:** `DoctorFinding` trägt zusätzlich `quoted` (≤ 120 Zeichen), `ref_check` (Check-ID des referenzierten Checks bei `finding-ref`), `severity_registry`; das JSON führt je Finding `severity_registry` und `severity_effective` (`severity` = effektiv) und `summary.severity[]` (`issue_id`, `provider`, `file`, `severity_registry`, `severity_effective`).
2. **Check-ID-Widerspruch:** IC-21 (`Finding.check = doctor.<id>`) und AC-41/AC-96 (Check-ID des referenzierten Checks) werden so aufgelöst: `check` bleibt `doctor.<id>`, die referenzierte Check-ID steht in `ref_check` (AC-41 vergleicht `ref_check`, AC-96 prüft `ref_check == doctor.tmp-sink-location`).
3. **`providers=`:** Schnittmenge mit den aktiven Providern (`None` = alle aktiven). Unbekannte oder nicht aktive (inkl. deaktivierte) Namen werden ignoriert und als INFO `doctor.provider-filter` gemeldet (Name in `provider`, Grund in `suggestion`).
4. **Treffer-Semantik:** ein Detektor trifft, wenn die genannte Bedingung gilt; `regex`: `found == (expect == match)`; `any_of`: Treffer nur, wenn kein Teil-Detektor trifft; fehlende Zieldatei ⇒ kein Treffer (Ausnahme `toml-key`, s. 6); fehlender Key unter `toml-key` `op: lt` zählt als Treffer (Default-Tiefe < `required_depth`); Glob ohne `/` ist relativ zum Zielverzeichnis, mit `/` relativ zur Projektwurzel; `finding-ref.match` ist eine Regex-Suche über die Meldung des referenzierten Findings.
5. **`variable-unreferenced`:** statisch über `{{…KEY…}}` in `agents`, `rules`, `templates`, `snippets`, `commands`; die IC-35-Leser-Registry existiert noch nicht und wird erst mit IC-35 berücksichtigt. Dedupe (Nachzug 9 der Phase 0d): Variablen mit eigenem Seed werden vom Wildcard-Seed übersprungen (Test vorhanden).
6. **TOML:** `tomllib` wenn vorhanden (3.11+), sonst Subset-Parser (Tabellen, gepunktete Keys, Skalare, ein-/mehrzeilige Arrays, Inline-Tables); Parser-Fehlertexte sind fest und inhaltsfrei (kein Artefakt-Rohtext in `message`/`suggestion`). Nicht parsebar ⇒ INFO `doctor.detector-unavailable`; fehlende Zieldatei ⇒ nur `skipped` (`detector-unavailable`), kein Finding.
7. **`doctor.registry-invalid`:** `severity_registry` = ERROR, effektiv WARNING (ohne `--strict`); der CLI-Handler (0d.3) leitet `--strict` (ERROR/Exit 2) aus der Check-ID `doctor.registry-invalid` ab, der Runner kennt kein `strict`.
8. **Skip-Gründe (`summary.skipped`):** `fixed-in`, `predicate` (auch bei `pattern_from_config` ohne Wert), `detector-unavailable` (fehlender Producer, z. B. `context.declared-surface-empty`/`surface_target_key` bis 0d.4, fehlende TOML-Datei, nicht allowlist-konformes argv, Sink deaktiviert bei schreibendem Befehl), `registry-invalid`. Ein fehlender Producer erzeugt kein INFO-Finding; INFO `doctor.detector-unavailable` nur bei Laufzeitursachen.
9. **`sync-log` und `command`:** der Log-Tag der Zeile (`[WARN]` ⇒ WARNING, `[INFO]` ⇒ INFO) ist die Check-Stufe des Findings. `command` hängt immer `--dry-run` an, prüft die Allowlist erneut, startet ohne Shell mit `encoding=utf-8`/`errors=replace` und `PYTHONDONTWRITEBYTECODE=1`; Treffer = Exit ≠ `expect_exit`, `quoted` = `exit N, expected M`. Bindungswerte in `message` werden von Steuerzeichen befreit und auf 120 Zeichen gekürzt.

### Task 0d.3: CLI `--doctor` mit Schreibgrenze bereitstellen
Rolle: senior-developer · Issue: #967 · PR: 0d · Depends: 0d.2 · AC: AC-39, AC-42, AC-44 (Doku), AC-75/AC-95/AC-98 (Doctor) · Falle: Dry-Run + stdout-Umleitung vor `_build_context`, danach `ctx.read_only = True`.
**Files:** Modify `scripts/sync.py`, `scripts/lib/cli_commands.py`, `docs/api/cli-reference.md`; Test Create `tests/test_doctor_cli.py`
**Interfaces:** Produces `sync.py --doctor [--json] [--strict] [--provider P] [--out FILE]`, `_handle_doctor(ctx: _SyncContext) -> None`, Exit 0/1/2, `doctor.out-outside-tmp-sink`, `doctor.tmp-sink.disabled`; Consumes `run_doctor`, `resolve_output_dir`
- [ ] Step 1: Test schreiben (fail): SHA-256-Snapshot (Projekt + agent-meta-Root, Sink `scratch/out` ausgenommen) inkl. Self-Hosting und `command`-Seed; Exit-Code-Matrix; Codex-Fixture ≥ 32,768 B ⇒ Exit 1
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_doctor_cli.py -q && python3 scripts/consistency-check.py`
- [ ] Step 4: commit `feat: add sync.py --doctor writing only to tmp-sink`

### Task 0d.4: Oberflächen-Checks ergänzen (IC-33)
Rolle: developer · Issue: #967 · PR: 0d · Depends: 0d.2 · parallel_group: 0d-g1 · AC: AC-67
**Files:** Modify `scripts/lib/consistency/context_budget.py`, `config/context-anchors.yaml` (`intentional_empty`); Test Modify `tests/test_context_budget_checks.py`
**Interfaces:** Produces `check_declared_surface_empty`, `check_legacy_artifact_present` (IC-10-Signatur, WARN); Consumes `surface_verified_state`, `legacy_artifacts`
- [ ] Step 1: Test schreiben (fail): Matrix ⇒ fehlende Skills Codex/Mammouth/Continue; Fixture mit `.mammouth/settings.json` ⇒ legacy
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_context_budget_checks.py -q`
- [ ] Step 4: commit `feat: add declared-surface and legacy-artifact checks`

#### Umsetzungs-Nachzüge 0d.3/0d.4 (zur Spec-Aufnahme)
Die freigegebene Spec bleibt unverändert; Umsetzung und Review von Task 0d.3/0d.4 haben folgende Präzisierungen ergeben (IC-22/IC-33, AC-67/AC-75).
1. **`--out` nur `<sink>/doctor/`:** `--doctor --out` akzeptiert ausschließlich Pfade unter `<sink>/doctor/` (Schreibgrenze IC-22, AC-95). Ein Pfad im Sink außerhalb von `doctor/` (z. B. `context-report/`) ist `doctor.out-outside-tmp-sink` (Exit 2); der Test deckt das ab. Der AC-75-Wortlaut „innerhalb des aufgelösten tmp-sink“ ist entsprechend auf `<sink>/doctor/` zu schärfen. Der Pfad wird vor dem Lauf geprüft (kein Laufzeitverlust bei Ablehnung); schlägt das Schreiben selbst fehl, wird der Bericht trotzdem ausgegeben und der Exit-Code ist 2 (`doctor.out-write-failed`).
2. **`intentional_empty`-Scope:** `config/context-anchors.yaml: intentional_empty` (`provider_capability: <surface>`) wirkt global über alle Provider, nicht je Provider; ein `provider:`-Schlüssel ist nicht vorgesehen. Soll eine Oberfläche nur für einen Provider leer bleiben dürfen, ist das in IC-33 nachzuziehen.
3. **Bytecode- und Flag-Regeln:** `--doctor` schreibt keine `.pyc`-Dateien: `sync.py` setzt `sys.dont_write_bytecode` vor dem ersten lib-Import (Erkennung über `sys.argv`, daher `allow_abbrev=False` am Parser, sonst umginge `--doc` die Sperre); der `command`-Detektor setzt zusätzlich `PYTHONDONTWRITEBYTECODE=1` für den Unterprozess. `--strict`, `--provider` und `--out` sind nur zusammen mit `--doctor` zulässig (sonst `parser.error`, Exit 2).
4. **AC-67 (Oberflächen-Matrix):** real belegt ist nur Codex (Skills-Oberfläche deklariert, nichts generiert); Mammouth und Continue sind fixture-basiert getestet, nicht gegen eine echte Installation.
5. **mcp/settings:** `check_declared_surface_empty` prüft MCP- und Settings-Oberflächen nur als vorhandene Datei (`is_file`), nicht auf Inhalt; die False-Positive-Policy (Datei vorhanden, aber leer/ungültig ⇒ kein Befund) ist bewusst und wird bei Bedarf über `intentional_empty` gesteuert.
6. **Nachzug 0d.1 Nr. 2 erledigt:** `surface_target_key(surface)` existiert in `context_budget.py`; der Fallback-/„lands in 0d.4“-Pfad in `doctor_predicates.py`/`doctor.py` ist entfernt (direkter Import). `declared-surface-empty` bindet den Provider aus dem Meldungspräfix `<provider>: ` (nur Namen aus dem aktiven Provider-Set) in das Finding-Feld `provider`; damit filtert `--provider` auch diese providerunabhängig deklarierten `finding-ref`-Einträge.
7. **CI-Kosten:** der Seed `sync-pending` startet `sync.py --check --dry-run` als Unterprozess; `--doctor` braucht dadurch auf dem agent-meta-Repo etwa 25–30 s (kleine Projekte ca. 7 s). Das ist in `docs/api/cli-reference.md` dokumentiert und bei der Einplanung von CI-Läufen (Matrix-Fixtures mit `--strict`) zu berücksichtigen; die Tests ersetzen den Unterprozess außer in den zwei Snapshot-Tests.

### Task 0d.5: Positiv-/Negativ-Fixtures je Seed anlegen (QG-10)
Rolle: tester · Issue: #967 · PR: 0d · Depends: 0d.3, 0d.4 · AC: AC-38, AC-76, AC-77, AC-96
**Files:** Create Fixture-Baum `tests/fixtures/doctor/` (je Pflicht-Seed-ID aus IC-21 ein Unterverzeichnis mit `positive/` und `negative/`); Test Create `tests/test_doctor_fixtures.py`
**Interfaces:** Produces Fixture-Matrix inkl. `tmp-sink-not-gitignored` (Fälle a, a', b–e), `variable-unreferenced`, `tmp-sink-outside-repo-or-system-temp`; Consumes `sync.py --doctor --json`
- [ ] Step 1: Test schreiben (fail): je Seed `positive` ≥ 1, `negative` 0 Findings der ID
- [ ] Step 2: implementieren (Fixtures)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_doctor_fixtures.py -q`
- [ ] Step 4: commit `chore: add positive and negative doctor seed fixtures` (PR-Text: `Closes #967`)

### Task 0e.1: Rolle `meta-doctor` anlegen (IC-23)
Rolle: prompt-engineer · Issue: #968 · PR: 0e · Depends: 0c, 0d · AC: AC-88, AC-95 (Rolle), AC-85 (Rolle) · Falle: nur `{{TMP_SINK_PATH}}`, kein `.tmp`; nie „strikt read-only"; `NEXT` über `ROLE_META_FEEDBACK_ACTIVE`.
**Files:** Create `agents/1-generic/meta-doctor.md`; Modify `config/role-defaults.yaml`; Test Create `tests/test_meta_doctor_role.py`
**Interfaces:** Produces Rolle `meta-doctor` (`name: template-meta-doctor`, Tools `Read, Glob, Grep, Bash, TodoWrite`), Contract `doctor-findings-v1`; Consumes `sync.py --doctor`, `TMP_SINK_PATH`
- [ ] Step 1: Test schreiben (fail): exakte argv-Allowlist, kein Write/Edit, kein `model:`, H-4-Texte, `name_only`
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_meta_doctor_role.py -q && python3 scripts/consistency-check.py`
- [ ] Step 4: commit `feat: add meta-doctor installation diagnosis role`

### Task 0e.2: `meta-doctor` nach IC-28 registrieren
Rolle: developer · Issue: #968 · PR: 0e · Depends: 0e.1 · AC: AC-01 (i)–(iii), AC-44 · Falle: `_EXPECTED_TOTAL` hier 92 → 93 (Spec-Wert 94 erst mit `meta-optimizer`); `_GOLDEN_ROLE_COUNT` bleibt 58.
**Files:** Modify `config/project-config.schema.json`, `tests/test_role_addressability_coverage.py`, `tests/fixtures/slimming-golden/orchestrator.md`, `standalone/README.md`, `tests/scenarios/registry.md`, `CHANGELOG.md`, `docs/guides/setup/instantiate-project.md`, `README.md`, `tests/fixtures/ac01-baseline/hashes.json`; Create `standalone/agents/meta-doctor.md`, `tests/scenarios/configs/77-meta-doctor-role.project.yaml`, `tests/scenarios/asserts/77-meta-doctor-role.sh` (`chmod +x`)
**Interfaces:** Produces Szenario 77, `test_name_only_roles_have_no_routing_patterns`, Golden-Rebaseline; Consumes `schema.update_roles_enum`, `sync.py --render-standalone`
- [ ] Step 1: Test schreiben (fail): Pins, Szenario 77 und AC-01-Harness melden fehlende Registrierung
- [ ] Step 2: implementieren (Sync, Export, Rebaseline mit Begründung)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_role_addressability_coverage.py tests/test_standalone_export_in_sync.py tests/test_ac01_render_identity.py -q && bash tests/scenarios/run.sh 77-meta-doctor-role`
- [ ] Step 4: commit `chore: register meta-doctor role across schema and goldens`

### Task 0e.3: `doctor-findings-v1` in `agent-meta-manager` konsumieren
Rolle: prompt-engineer · Issue: #968 · PR: 0e · Depends: 0e.1 · parallel_group: 0e-g1 · AC: AC-44
**Files:** Modify `agents/1-generic/agent-meta-manager.md` (Version-Bump); Test Modify `tests/test_meta_doctor_role.py`
**Interfaces:** Produces Consumer-Abschnitt für `doctor-findings-v1`; Consumes Contract aus 0e.1
- [ ] Step 1: Test schreiben (fail): `handoff.output-not-consumed` für `doctor-findings-v1`
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 scripts/consistency-check.py && python3 -m pytest tests/test_meta_doctor_role.py -q`
- [ ] Step 4: commit `feat: consume doctor findings in agent-meta-manager`

### Task 0e.4: IC-28-Checkliste in die Konventionen übernehmen
Rolle: documenter · Issue: #968 · PR: 0e · Depends: 0e.2 · AC: AC-44, AC-87
**Files:** Modify `rules/2-platform/agent-meta-conventions.md`; Test Create `tests/test_new_role_checklist_doc.py`
**Interfaces:** Produces Abschnitt „Neue-Rolle-Checkliste" (IC-28 Nr. 1–12); Consumes IC-28
- [ ] Step 1: Test schreiben (fail): Abschnitt mit 12 Punkten fehlt
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_new_role_checklist_doc.py -q`
- [ ] Step 4: commit `chore: add new-role checklist to agent-meta conventions` (PR-Text: `Closes #968`)

### Task 0f.1: Role-Routing-Eval-Korpus generieren (IC-13)
Rolle: tester · Issue: #969 · PR: 0f · Depends: 0a.10 · parallel_group: 0f-g1 · AC: AC-03, AC-62 (Korpus)
**Files:** Create `scripts/gen_role_routing_eval_catalog.py`, `tests/routing-llm-eval/roles/catalog.generated.yaml`, `tests/routing-llm-eval/roles/catalog.manual.yaml`, `tests/routing-llm-eval/roles/promptfooconfig.generated.yaml`; Test Create `tests/test_role_routing_eval_catalog.py`
**Interfaces:** Produces `generate_catalog(agent_meta_root: Path) -> dict`, Fallschema `{target, tier_escalation}`; Consumes `config/role-defaults.yaml`, Muster `scripts/gen_promptfoo_config.py` und `scripts/gen_routing_llm_eval_catalog.py`
- [ ] Step 1: Test schreiben (fail): jedes Keyword/Beispiel abgedeckt, ≥ 20 Rollen DE+EN, ≥ 2 Fälle je Overlap-Token, Name-only-Fälle
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_role_routing_eval_catalog.py -q`
- [ ] Step 4: commit `feat: add role routing eval catalog generator and corpus`

**Umsetzungs-Nachzüge 0f** (aus Review zu 0f.1; Spec bleibt unverändert, Spec-Nachzug offen):
- Kollisionsfälle (IC-29-Overlap-Tokens) liegen in `catalog.generated.yaml`, nicht in `catalog.manual.yaml` (Abweichung von IC-13; Spec-Nachzug).
- McNemar zurückgestellt (IC-36/Q37); bis dahin gilt das τ-Modell mit ≥ 3 Baseline-Läufen.
- Freigabewort `yes`/`ja` und Preis-Maximalalter der Kostenschätzung gemäß IC-36 in `eval_gate` (0f.2) umsetzen.
- Korpus-Hash = sha256 über die kanonische Vereinigung von `catalog.generated.yaml` und `catalog.manual.yaml` (nach `id` sortiert, kanonisches JSON); Ausgabe via `python3 scripts/gen_role_routing_eval_catalog.py --print-hash`, in Python `corpus_hash(out_dir)`.
- Sprach-Delta nur auf `pair_id`-Paaren (`language_pairs(catalog)`: gleiche Zielrolle, je ein `de`- und `en`-Fall). Englisch gerahmte DE-Keyword-Fälle sind `lang: mixed` und zählen nicht als `en`; EN-Daten in `role-defaults` fehlen bis IC-29.
- `name_only`-Rollen erhalten nur Direktadressierungs-Fälle, keine Keyword-/Beispiel-Positivfälle; Q9 (template-auditor ohne `routing_patterns`) muss VOR dem Baseline-Lauf umgesetzt sein, der Hash ändert sich dadurch erneut.
- Voraussetzung für 0f.3 (vor der Freigabeanfrage klären): `tests/routing-llm-eval/provider-claude.sh` nutzt `.claude/rules/use-orchestrator.md` (Stub) und ein festes Modell `haiku`. Zu klären: System-Prompt-Quelle (gerenderte Orchestrator-Datei des jeweiligen Profils), Profil-/Modell-Parametrisierung der Provider und ≥ 2 Modellklassen.

### Task 0f.2: Toleranzmodell und Freigabe-Wrapper implementieren (IC-36)
Rolle: developer · Issue: #969 · PR: 0f · Depends: — · parallel_group: 0f-g1 · AC: AC-86 (Freigabe)
**Files:** Create `scripts/lib/eval_gate.py`; Test Create `tests/test_eval_gate.py`
**Interfaces:** Produces `estimate_cost(cases: int, models: Sequence[str], runs: int, report: dict) -> dict`, `request_approval(estimate: dict, approval_input: str | None) -> bool`, `write_skip_record(path: Path, estimate: dict, reason: str) -> None`, `evaluate_gate(baseline: dict, candidate: dict, k: float = 2.0) -> str` (`passed|failed|not-evidenced`); Consumes `measure_artifacts`
- [ ] Step 1: Test schreiben (fail): ohne Freigabe 0 Mock-Aufrufe + Kostenausgabe; Ablehnung ⇒ `SKIPPED-BY-USER`-Datei; Gate ⇒ `not-evidenced`; Metrik-Richtungen
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_eval_gate.py -q`
- [ ] Step 4: commit `feat: add eval tolerance model and approval gate`

### Task 0f.3: Baseline `full` nach Nutzerfreigabe erheben oder Skip protokollieren
Rolle: test-executor · Issue: #969 · PR: 0f · Depends: 0f.1, 0f.2 · AC: AC-02, AC-62 (Baseline) · Falle: Kostenschätzung zeigen und auf Freigabe warten; Nein ⇒ Skip-Record committen, AC-02 nicht erfüllt, Profil `compact` blockiert.
**Files:** Create Ergebnisdateien in `tests/routing-llm-eval/roles/baseline/` (Namensschema IC-13: Datum-Modell-Profil) bzw. Skip-Record in `tests/routing-llm-eval/roles/runs/` (IC-36); Test Create `tests/test_eval_baseline_schema.py`
**Interfaces:** Produces Baseline (≥ 2 Modellklassen, ≥ 3 Läufe, σ, Korpus-Hash, Modell-IDs, Kollisions-Accuracy, Sprach-Delta) oder Skip-Record; Consumes `eval_gate.request_approval`, Katalog aus 0f.1
- [ ] Step 1: Test schreiben (fail): Schema-Test findet weder Baseline- noch Skip-Datei
- [ ] Step 2: implementieren (Lauf bzw. Skip protokollieren)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_eval_baseline_schema.py -q`
- [ ] Step 4: commit `chore: record full-profile role routing baseline` (PR-Text: `Closes #969`)

**Status 2026-10-17: SKIPPED-BY-USER.** Der Lauf (Deepseek-only, 659 Fälle × 3 Wiederholungen = 1977 Calls; Kostenschätzung 0.0000 USD laut Overlay, UNVERIFIED ohne datierte Quelle) wurde auf Nutzerentscheidung abgebrochen (~12 h Laufzeit); eine Baseline wird nicht belegt. Skip-Record: `tests/routing-llm-eval/roles/runs/2026-10-17-qg1-deepseek.json`.

Konsequenzen:
- AC-02/AC-62 bleiben nicht belegt (nur 1 statt ≥ 2 Modellklassen).
- 1.46/1.47 bleiben nur SKIPPED-fähig; ihr Depends „0f.3 (AC-62 belegt)“ bleibt offen.
- `compact` (Phase 2) bleibt unverifiziertes Opt-in ohne Verifikationsanspruch (AC-86 Profil-Teil).
- Implementiert und in PR #998 enthalten: Runner (`scripts/run_role_routing_eval.py`), Baseline-/Skip-Record-Schema, Output-Contract.

## Phase 1

Reihenfolge: 1.00 → 1.01 (#970, erster IC-18-PR) → IC-18 Nr. 15–18 (1.02–1.05) → IC-31 (1.06/1.07, vor allen Template-PRs) → IC-18 Nr. 1–12 (1.08–1.19; Nr. 2 vor IC-04) → 1.20. IC-15-Fixes (1.21–1.44) und IC-29 (1.45–1.47) laufen ab 1.01 je eigenem Branch; bei gemeinsamen Dateien gilt die `Depends`-Kette.

### Task 1.00: Fehlende Phase-1-Issues anlegen
Rolle: git · Issue: #977 · Depends: 0b · AC: AC-10 (Voraussetzung)
**Files:** Modify `docs/plans/2026-10-11-context-profiles-plan.md` (Issue-Nummern im Ledger eintragen)
**Interfaces:** Produces je ein Issue mit Verweis auf #977 und Spec-ID für IC-18 Nr. 1–12 und 15–18; IC-15 Nr. 1, 7, 10–19, 21–25; IC-29 (Sprach-Mapping, Migration, Schärfung); IC-30-Triage; IC-31 (zwei PRs); Consumes Spec §3a, §9
- [ ] Step 1: Prüfung (fail): `gh issue list -R Popoboxxo/agent-meta --search "SPEC-CONTEXT-PROFILES in:body"` liefert diese Issues nicht
- [ ] Step 2: Issues anlegen
- [ ] Step 3: Prüfung (pass): dieselbe Suche liefert alle Titel
- [ ] Step 4: commit `chore: record phase-1 issue numbers in context profiles plan`

### Task 1.01: Auto-Commit-Allowlist aus ActiveSet ableiten (IC-18 Nr. 14)
Rolle: senior-developer · Issue: #970 · Depends: 0b · AC: AC-84 (Red/Green) · Falle: Laufzeit-Leser `orchestrator-guard-impl.sh`; Ratchet-Eintrag `sync_pipeline.py` entfernen.
**Files:** Modify `scripts/lib/sync_pipeline.py` (`_sync_stage_auto_commit_allowlist`), `tests/test_active_set_single_source.py`; Test Modify `tests/test_auto_commit_allowlist_pipeline.py`
**Interfaces:** Produces `.meta-config/auto-commit-allowlist.json` ohne gate-gedroppte Rollen; Consumes `resolve_auto_commit_config(config: dict, active_roles: list[str], agent_meta_root: Path, platform: str | None = None) -> dict`, `ActiveSet.roles`
- [ ] Step 1: Test schreiben (fail): p20 mit `auto_commit` für `senior-developer` ⇒ Rolle steht in der Allowlist
- [ ] Step 2: implementieren (`sorted(active_set.roles)`)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_auto_commit_allowlist_pipeline.py tests/test_active_set_single_source.py -q`
- [ ] Step 4: commit `fix: derive auto-commit allowlist from active set` (PR-Text: `Closes #970`)

### Task 1.02: Erwartete Agent-Dateien aus ActiveSet (IC-18 Nr. 16)
Rolle: developer · Issue: aus 1.00 · Depends: 1.01 · AC: AC-45, AC-84
**Files:** Modify `scripts/sync.py`, `tests/test_active_set_single_source.py`; Test Create `tests/test_expected_agents_active_set.py`
**Interfaces:** Produces `allowed_roles` = `ActiveSet.roles`; Consumes `_SyncContext.active_set`
- [ ] Step 1: Test schreiben (fail): `--check` auf p20 meldet gate-gedroppte Rolle als erwartet
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_expected_agents_active_set.py -q`
- [ ] Step 4: commit `fix: use active set for expected agent files`

### Task 1.03: Continue-Prompts nach ActiveSet filtern (IC-18 Nr. 15)
Rolle: developer · Issue: aus 1.00 · Depends: 1.02 · AC: AC-45, AC-84
**Files:** Modify `scripts/lib/context.py` (`sync_prompts_for_continue`), `tests/test_active_set_single_source.py`; Test Create `tests/test_continue_prompts_active_set.py`
**Interfaces:** Produces Prompts nur für `ActiveSet.roles`; Consumes `ActiveSet`
- [ ] Step 1: Test schreiben (fail): p20 erzeugt Prompt für gate-gedroppte Rolle
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_continue_prompts_active_set.py -q`
- [ ] Step 4: commit `fix: filter continue prompts by active set`

### Task 1.04: Scout-Skill-Ableitung über ActiveSet (IC-18 Nr. 17)
Rolle: developer · Issue: aus 1.00 · Depends: 1.03 · AC: AC-45, AC-84
**Files:** Modify `scripts/lib/skills.py`, `tests/test_active_set_single_source.py`; Test Create `tests/test_scout_skill_active_set.py`
**Interfaces:** Produces Skill `awesome-claude-code` nur bei `ActiveSet.has("agent-meta-scout")`; Consumes `ActiveSet.has(role: str) -> bool`
- [ ] Step 1: Test schreiben (fail): gate-gedroppter Scout erzeugt den Skill
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_scout_skill_active_set.py -q`
- [ ] Step 4: commit `fix: derive scout skill from active set`

### Task 1.05: Variablen-Builder auf ActiveSet umstellen (IC-18 Nr. 18)
Rolle: senior-developer · Issue: aus 1.00 · Depends: 1.04 · AC: AC-45, AC-84
**Files:** Modify `scripts/lib/config.py` (Active-Role-Liste, `EFFORT_ESTIMATOR_ENABLED`, Konventions-Auflösung, `PROJECT_SPECIFIC_AGENTS`), `tests/test_active_set_single_source.py`; Test Create `tests/test_variable_builder_active_set.py`
**Interfaces:** Produces `EFFORT_ESTIMATOR_ENABLED` aus `ActiveSet.has("effort-estimator")`, `ACTIVE_ROLES`, `ROLE_*_ACTIVE`; Consumes `active_set_variables(active: ActiveSet) -> dict[str, str]`
- [ ] Step 1: Test schreiben (fail): gate-gedroppter `effort-estimator` ⇒ `"true"`
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_variable_builder_active_set.py tests/test_ac01_render_identity.py -q`
- [ ] Step 4: commit `fix: build role variables from active set`

### Task 1.06: Quell-Boilerplate render-neutral de-duplizieren (IC-31)
Rolle: senior-developer · Issue: aus 1.00 · Depends: 0e · AC: AC-72 · Falle: `test_contract_labels.py` auf snippet-aufgelöste Templates umstellen (#552), sonst gehen Marker verloren.
**Files:** Create `snippets/agents/closing-summary.md`, `snippets/agents/user-proxy.md`, `tests/test_template_line_duplication.py`; Modify betroffene `agents/1-generic/*.md`, `agents/2-platform/*.md`, `scripts/lib/consistency/placeholders.py`, `tests/test_contract_labels.py`
**Interfaces:** Produces `{{CLOSING_SUMMARY_BLOCK}}`, `{{USER_PROXY_BLOCK}}`, Nutzung `{{ANTI_RECURSION_BLOCK}}`; Consumes Snippet-Auflösung aus `scripts/lib/standalone.py`
- [ ] Step 1: Test schreiben (fail): Duplikations-Ratchet und Inline-Zeilen-Guard rot
- [ ] Step 2: implementieren (Version-Bumps)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_template_line_duplication.py tests/test_contract_labels.py tests/test_ac01_render_identity.py -q`
- [ ] Step 4: commit `chore: replace repeated template boilerplate with snippets`

#### Umsetzungs-Nachzüge 1.06/1.07 (zur Spec-Aufnahme)
Die freigegebene Spec bleibt unverändert; die folgenden Abweichungen sind umgesetzt und bei einer Spec-Revision zu übernehmen.
1. **Worker-Rolle (IC-31/Task 1.06):** neuer `{{WORKER_ROLE_BLOCK}}` (`snippets/agents/worker-role.md`, EN, statisch) statt `{{ANTI_RECURSION_BLOCK}}`. Grund: `ANTI_RECURSION_BLOCK` rendert deutschen, datengetriebenen Text; ein Ersatz der englischen Inline-Zeile würde den Render ändern (AC-72 verlangt byte-identisch). Beide Blöcke sind bewusst getrennt. Interfaces-Zeile 1.06 ergänzt: Produces `{{CLOSING_SUMMARY_BLOCK}}`, `{{USER_PROXY_BLOCK}}`, `{{WORKER_ROLE_BLOCK}}` (statt Nutzung `{{ANTI_RECURSION_BLOCK}}`).
2. **Zahlen (gemessen):** Worker-Role 49 identische Zeilen (nicht 24 Nutzer/58 Kopien; 8 weitere Varianten sind nicht identisch); Closing-Summary 67 (3 abweichende Varianten bleiben inline); User-Proxy 20 identische Zeilen (nicht 19).
3. **Version-Bumps (Step 2):** Ausnahme — render-neutrale Quell-Refactors erfolgen ohne Bump, weil das Frontmatter-`version:` im Render steht (ein Bump bräche AC-72/AC-01 byte-identisch). Vorschlag für Konventions-Skill, Hard Invariant 2 (Skill-Datei nicht geändert): „Bump on every content change — except purely source-level, render-neutral refactors (AC-01 harness green, rendered output byte-identical), because the frontmatter `version` is part of the render; record these in the CHANGELOG instead." Task 1.07 (Render-Änderung) bumpt dagegen (Patch).
4. **Task 1.07 Dateiliste:** `tests/fixtures/slimming-golden/orchestrator.md` blieb unverändert; tatsächlich rebaselined wurden 8 Goldens (`knowledge-*` ×7, `mammouth-expert`), außerdem AC-01 `hashes.json` (18 von 1102) und `standalone/agents/` (19 Dateien).
5. **Registrierung (IC-32):** die neuen `*_BLOCK` sind bisher manuell in `_BUILTIN_VARS` (`consistency/placeholders.py`) eingetragen; die Zuordnung Snippet→Variable liegt einmalig in `config.AGENT_BLOCK_SNIPPETS`. IC-32 soll die Menge später daraus ableiten. Präzedenz für render-neutrales Snippet-Dedup ohne Bump: Commit 5034004 (SR-C-07, escalate-card).

### Task 1.07: EN/DE-Zwilling auf EN vereinheitlichen (IC-31)
Rolle: prompt-engineer · Issue: aus 1.00 · Depends: 1.06 · AC: AC-72 (Ausnahme), AC-06
**Files:** Modify die 19 Templates mit „Pflicht-Abschluss-Summary" unter `agents/`, `tests/fixtures/slimming-golden/orchestrator.md`; Test Modify `tests/test_template_line_duplication.py`
**Interfaces:** Produces EN-Fassung über `{{CLOSING_SUMMARY_BLOCK}}`; Consumes Anker (QG-3)
- [ ] Step 1: Test schreiben (fail): Ratchet-Grenze auf Zielwert senken
- [ ] Step 2: implementieren (Golden-Rebaseline mit Begründung)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_template_line_duplication.py tests/test_context_anchors.py -q`
- [ ] Step 4: commit `chore: unify closing summary twin templates to english`

### Task 1.08: Enum, Routing und Agent-Dateien aus geteiltem ActiveSet (IC-18 Nr. 1)
Rolle: senior-developer · Issue: aus 1.00 · Depends: 1.05 · AC: AC-45 · Falle: Ergebnis unverändert (AC-01-Harness grün).
**Files:** Modify `scripts/lib/delegation_table.py`, `scripts/lib/agents.py`, `scripts/lib/agent_sync.py` (`_should_skip_role`); Test Create `tests/test_active_set_consumers_identity.py`
**Interfaces:** Produces Konsum desselben `ActiveSet`-Objekts (QG-13 dynamisch); Consumes `_SyncContext.active_set`
- [ ] Step 1: Test schreiben (fail): Identitäts-Spy zeigt Neuberechnung statt geteiltem Objekt
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_active_set_consumers_identity.py tests/test_ac01_render_identity.py -q`
- [ ] Step 4: commit `chore: pass shared active set to routing generators`

### Task 1.09: Pipeline-Validierung gegen ActiveSet (IC-18 Nr. 12, IC-15 Nr. 18)
Rolle: developer · Issue: aus 1.00 · Depends: 1.08 · AC: AC-52, AC-84 (Ende)
**Files:** Modify `scripts/lib/config.py` (Pipeline-Validierung), `scripts/lib/agent_sync.py` (`_apply_content_pipeline`), `tests/test_active_set_single_source.py`; Test Modify `tests/test_pipelines.py`
**Interfaces:** Produces ein `effective` aus `config.py`, keine Neuableitung im Renderer; Consumes `ActiveSet.roles`
- [ ] Step 1: Test schreiben (fail): p20 nennt `senior-developer` nicht; Stage mit inaktivem `dod_flag` warnt
- [ ] Step 2: implementieren (Ratchet-Registry danach leer)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_pipelines.py tests/test_active_set_single_source.py -q`
- [ ] Step 4: commit `fix: validate pipelines against active set roles`

### Task 1.10: Pipelines nach Pflicht-Stage-Rollen filtern (IC-18 Nr. 2)
Rolle: senior-developer · Issue: aus 1.00 · Depends: 1.09 · AC: AC-46 · Falle: vor IC-04 (Phase 2) mergen; veraltete `pipeline-details` über Managed-File-Cleanup entfernen.
**Files:** Modify `scripts/lib/pipelines.py`, `scripts/lib/delegation_table.py`, `scripts/lib/agent_sync.py`, `tests/fixtures/slimming-golden/orchestrator.md`; Test Create `tests/test_pipeline_active_set_filter.py`
**Interfaces:** Produces `filter_pipelines_by_active_set(effective: dict, active: ActiveSet, variables: Mapping[str, str]) -> tuple[dict, list[PipelineDrop]]`, `PipelineDrop`, WARN `active-set.pipeline-dropped` (Konsole + `sync.log`); Consumes Regel §4.4
- [ ] Step 1: Test schreiben (fail): p10 rendert Pipeline mit inaktiver Pflichtrolle in §2/§2a/`pipeline-details`/`routing.pipelines`
- [ ] Step 2: implementieren (Golden-Rebaseline mit Begründung)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_pipeline_active_set_filter.py tests/test_template_slimming_equivalence.py -q`
- [ ] Step 4: commit `feat: drop pipelines whose required roles are inactive`

#### Umsetzungs-Nachzüge 1.10/1.11 (zur Spec-Aufnahme)
Die freigegebene Spec bleibt unverändert; die folgenden Abweichungen/Entscheidungen sind umgesetzt.
1. **Default-Drop (Nutzerentscheidung, ADR-10/Q18, AC-23-Phase-1-Rebaseline):** der Pipeline-Drop gilt auch im Default (kein `roles:`-Key). Der Default hat 63 aktive Rollen; die Gates `validator` und `developer_tiers` sind aus, also fehlen `validator`, `junior-developer`, `senior-developer`. Folge: `concept-driven-dev` und `feature-lifecycle` (`validator`) sowie `refactor` (`senior-developer`) werden im Default nicht mehr gerendert; stattdessen WARN `active-set.pipeline-dropped` mit Aktivierungsweg. Rebaseline: AC-01 `hashes.json` (nur Orchestrator-Artefakte, `pipeline-details`, `generated-file-hashes.json`), Context-Budget-Pins; der Orchestrator-Golden war bereits in 1.12 als Teilmenge rebaselined.
2. **dod_flag (AC-52):** der Plan-Test-Wortlaut „Stage mit inaktivem `dod_flag` warnt“ ist falsch; laut Spec AC-52 warnt sie NICHT. Umgesetzt in 1.09 (`validate_pipelines(active_dod=...)`, geteilte Regel `_stage_dod_flag_inactive`).
3. **Zusatzparameter:** `filter_pipelines_by_active_set(effective, active, variables, *, active_dod=None, reflection_pairs=None)`. `active_dod` ist nötig, weil `root-cause-required`/`spec-plan-enabled` keine `DOD_*`-Variable haben; `reflection_pairs` löst `loop_ref` (Generator/Critic) mit Projekt-Overrides auf. Zusätzlich `format_pipeline_drop(drop, active)` für den WARN-Text. Ein leerer `allowed_agents`-Schnitt fällt auf `[fallback_agent]` zurück (der Renderer liest `[]` als „keine Restriktion“).
4. **Verdrahtung:** das gefilterte `effective` entsteht einmal in `config._build_pipeline_variables` (`PIPELINES_EFFECTIVE_KEY`); Agent-Renderer, `pipeline-details` (`sync_pipeline.py`, Test-Repo-Pfad in `cli_commands.py`), `PIPELINE_MATCH_TABLE`, `INTENT_ROUTING_TABLE` und `routing.pipelines` konsumieren es; `gen_routing_llm_eval_catalog.py` filtert mit demselben Aufruf. Veraltete `pipeline-details`-Dateien entfernt die bestehende Managed-File-Cleanup (der Aufruf läuft auch bei leerem `effective`).
5. **Szenarien:** 50, 51 und 52 (`concept-driven-dev`-Detaildatei/Approval-Gate) bekamen eine explizite `roles:`-Liste inkl. `validator`.
6. **Pflicht-Rollen:** `parallel_group`-Mitglieder und der plan-getriebene `fallback_agent` zählen als Pflicht (neben `agent` und Loop-Generator/-Critic). Signatur: `filter_pipelines_by_active_set(effective, active, variables, *, active_dod, reflection_pairs)`. Leerer `allowed_agents`-Schnitt → `[fallback_agent]`; ohne `fallback_agent` bleibt die Stage unverändert.
7. **Aktivierungsweg im Default:** expliziter `roles:`-Eintrag (die Gates `validator`/`developer_tiers` sind `roles_membership`; ohne Allowlist gibt es kein `gate_dropped`). `format_pipeline_drop` löst die Gate-Gruppe daher aus `activation_groups` + `role_patterns` auf und warnt, dass `roles:` eine Allowlist ist (alle gewünschten Rollen auflisten).
8. **Bekannter Zwischenstand:** statische Orchestrator-Prosa (Task-Größen-Routing, „complex feature → feature-lifecycle“) nennt gedroppte Pipelines bis Task 1.16 weiter. `context.py` (`build_agent_hints` ~644/646, `get_active_agents_data` ~1717) ruft `resolve_active_roles` weiter selbst auf — akzeptiertes Restrisiko bis zur Durchreichung (Follow-up), Drift-Risiko niedrig.

### Task 1.11: `allowed_agents` mit ActiveSet schneiden (IC-18 Nr. 3)
Rolle: developer · Issue: aus 1.00 · Depends: 1.10 · AC: AC-47 (Teil)
**Files:** Modify `scripts/lib/pipelines.py`; Test Modify `tests/test_pipeline_active_set_filter.py`
**Interfaces:** Produces `allowed_agents ⊆ ActiveSet.roles`; Consumes `ActiveSet.roles`
- [ ] Step 1: Test schreiben (fail): p10-`allowed_agents` enthält inaktive Rolle
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_pipeline_active_set_filter.py -q`
- [ ] Step 4: commit `fix: intersect plan-driven allowed agents with active set`

### Task 1.12: `input_contracts` nur mit aktivem Producer (IC-18 Nr. 4)
Rolle: developer · Issue: aus 1.00 · Depends: 1.11 · AC: AC-47 (Teil)
**Files:** Modify `scripts/lib/delegation_table.py` (`get_routing_rules`); Test Modify `tests/test_routing_tool_definitions.py`
**Interfaces:** Produces nur Contracts mit nicht-leerem `ActiveSet.producers[c]` (`task-spec-v1` bleibt); Consumes `ActiveSet.producers`
- [ ] Step 1: Test schreiben (fail): p10 enthält Contract ohne aktiven Producer
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_routing_tool_definitions.py -q`
- [ ] Step 4: commit `fix: keep only input contracts with an active producer`

### Task 1.13: Tier-Kette auf `DEVELOPER_TIERS_ENABLED` gaten (IC-18 Nr. 5)
Rolle: prompt-engineer · Issue: aus 1.00 · Depends: 1.12, 1.07 · AC: AC-48 · Falle: `if`-Zweig = heutiger Text byte-identisch; nur der `else`-Zweig ist neu.
**Files:** Modify `agents/1-generic/orchestrator.md`, `agents/1-generic/developer.md`, `agents/1-generic/planner.md`, `scripts/lib/config.py` (`ESCALATE_CARD_BLOCK`); Test Modify `tests/test_developer_tiers_gate.py`
**Interfaces:** Produces `{{#if DEVELOPER_TIERS_ENABLED}}`-Konditional mit Developer-only-Variante, `ROLE_CONCEPT_*_ACTIVE`-Zeilen; Consumes `variables.strip_inactive_conditional_blocks(text: str, variables: dict) -> str`
- [ ] Step 1: Test schreiben (fail): `false` ⇒ Referenzen auf `junior-developer`/`senior-developer`/`principal-developer`
- [ ] Step 2: implementieren (Version-Bumps)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_developer_tiers_gate.py -q`
- [ ] Step 4: commit `fix: gate orchestrator tier chain on developer tiers`

### Task 1.14: `ANTI_RECURSION_BLOCK` aus Daten ∩ ActiveSet (IC-18 Nr. 6)
Rolle: developer · Issue: aus 1.00 · Depends: 1.13 · AC: AC-49 (Teil)
**Files:** Modify `scripts/lib/config.py` (`ANTI_RECURSION_BLOCK`); Test Create `tests/test_anti_recursion_block.py`
**Interfaces:** Produces Rollenliste = `role-defaults` ∩ `ActiveSet.roles`; Consumes `ActiveSet`
- [ ] Step 1: Test schreiben (fail): p10-Block nennt inaktive Rolle
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_anti_recursion_block.py -q`
- [ ] Step 4: commit `fix: build anti-recursion block from active roles`

### Task 1.15: `DIRECT_DISPATCH_SECTION` je aktiver Rolle (IC-18 Nr. 7)
Rolle: developer · Issue: aus 1.00 · Depends: 1.14 · AC: AC-49 (Teil)
**Files:** Modify `templates/direct-dispatch-section.md`, `scripts/lib/config.py` (`DIRECT_DISPATCH_SECTION`); Test Create `tests/test_direct_dispatch_active_set.py`
**Interfaces:** Produces Zeilen unter `{{#if ROLE_*_ACTIVE}}`; Consumes `active_set_variables`
- [ ] Step 1: Test schreiben (fail): p10 enthält Zeile einer inaktiven Rolle
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_direct_dispatch_active_set.py -q`
- [ ] Step 4: commit `fix: render direct dispatch rows only for active roles`

### Task 1.16: Persona, §11-Fallback und SE-Prosa konditional (IC-18 Nr. 8)
Rolle: prompt-engineer · Issue: aus 1.00 · Depends: 1.15 · AC: AC-49 (Teil)
**Files:** Modify `agents/1-generic/orchestrator.md`, `tests/fixtures/slimming-golden/orchestrator.md`; Test Create `tests/test_orchestrator_active_set_prose.py`
**Interfaces:** Produces Fallback „ASK" bei inaktivem `meta-feedback`; Consumes `ROLE_META_FEEDBACK_ACTIVE`, `SE_ENABLED`
- [ ] Step 1: Test schreiben (fail): p10 ohne `meta-feedback` nennt `meta-feedback`
- [ ] Step 2: implementieren (Version-Bump, Golden-Rebaseline)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_orchestrator_active_set_prose.py -q`
- [ ] Step 4: commit `fix: condition orchestrator persona and fallback on active roles`

### Task 1.17: Commands mit `requires_roles` nur bei aktiver Rolle (IC-18 Nr. 9)
Rolle: developer · Issue: aus 1.00 · Depends: 1.16 · AC: AC-50
**Files:** Modify `scripts/lib/commands.py` (`sync_commands_for_provider`), `scripts/lib/consistency/commands.py`, betroffene Dateien unter `commands/`; Test Create `tests/test_commands_requires_roles.py`
**Interfaces:** Produces Frontmatter-Key `requires_roles` (Liste von Rollen), Managed-File-Entfernung; Consumes `ActiveSet.all_active(roles: Iterable[str]) -> bool`
- [ ] Step 1: Test schreiben (fail): Command mit inaktiver Rolle wird generiert bzw. bleibt bestehen
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_commands_requires_roles.py -q`
- [ ] Step 4: commit `feat: skip commands whose required roles are inactive`

### Task 1.18: Rules-Owner-Zeilen konditional (IC-18 Nr. 10)
Rolle: prompt-engineer · Issue: aus 1.00 · Depends: 1.17 · AC: AC-49 (Teil)
**Files:** Modify `rules/1-generic/security-paved-roads.md`, `rules/1-generic/threat-model.md`, `rules/1-generic/a2a-delegation-gates.md`; Test Create `tests/test_rules_role_ownership.py`
**Interfaces:** Produces Owner-Zeilen unter `{{#if ROLE_*_ACTIVE}}`; Consumes IC-03-Konditionale im Rules-Pfad
- [ ] Step 1: Test schreiben (fail): p10-Rule nennt inaktiven Owner
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_rules_role_ownership.py -q`
- [ ] Step 4: commit `fix: condition rule owner lines on active roles`

### Task 1.19: IC-30-Triage und Delegations-Prosa (IC-18 Nr. 11)
Rolle: prompt-engineer · Issue: aus 1.00 · Depends: 1.18 · AC: AC-71 · Falle: Zeilenmenge = IC-30-Ratchet-Registry, keine eigene Heuristik.
**Files:** Modify betroffene `agents/1-generic/*.md`, `agents/2-platform/*.md`, `config/role-defaults.yaml` (`handoff.target_roles`), `tests/test_no_role_routes_in_templates.py`
**Interfaces:** Produces Registry-Klassen A/D/E leer, B/C/F konditional, unter Allow-Marker oder in Daten; Consumes `ROUTE_RATCHET`
- [ ] Step 1: Test schreiben (fail): Ratchet-Grenze für A/D/E auf 0
- [ ] Step 2: implementieren (Version-Bumps)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_no_role_routes_in_templates.py tests/test_active_set_dangling.py -q`
- [ ] Step 4: commit `fix: triage dispatch lines in templates per active set`

### Task 1.20: `dangling-dispatch` auf ERROR heben, QG-13 vollständig
Rolle: tester · Issue: aus 1.00 · Depends: 1.19 · AC: AC-45, AC-49, AC-84 (Ende)
**Files:** Modify `scripts/lib/consistency/active_set_refs.py`, `tests/test_active_set_dangling.py`, `tests/test_active_set_single_source.py`
**Interfaces:** Produces Level ERROR für `active-set.dangling-dispatch`, `dangling-mention` außerhalb `mention_allow` = 0, leere Ratchet-Registry; Consumes Fixture-Matrix × Provider-Matrix
- [ ] Step 1: Test schreiben (fail): ERROR-Stufe und Null-Erwartung über p10/p20/pall/ha
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_active_set_dangling.py tests/test_active_set_single_source.py -q`
- [ ] Step 4: commit `fix: promote dangling dispatch check to error`

#### Umsetzungs-Nachzüge 1.13–1.20 (zur Spec-Aufnahme)
Die freigegebene Spec bleibt unverändert; die folgenden Abweichungen/Entscheidungen sind umgesetzt (PR D).
1. **Default-Render (1.13/1.14/1.16/1.19):** Der Default hat `developer_tiers`, `validator`, `se` und `knowledge` aus. Die Active-Set-Konditionale ändern daher den Default-Render (IC-18 Nr. 5/6/8 laut Plan-Global-Constraints erlaubt, Nr. 11 über AC-49/AC-71 gefordert): §4/Task-Size ohne Tier-Kette, Anti-Recursion ohne `validator`, keine SE-Prosa, keine gedroppten Pipelines in statischer Prosa, Worker-Zeilen ohne inaktive Ziele. AC-01-Rebaseline je Task (36/27/18/270 von 1075), Budget-Pins nur gesenkt. 1.15, 1.17, 1.18 und 1.20 sind im Default render-neutral.
2. **Bekannter Zwischenstand aus 1.10 Nr. 8 erledigt (1.16):** die statische Orchestrator-Prosa nennt `concept-driven-dev`, `concept-development` und `feature-lifecycle` nur noch bei `PIPELINE_<NAME>_ENABLED`.
3. **AC-48 (1.13):** der `if`-Zweig ist gegen einen Fixture-Pin (`tests/fixtures/developer-tiers/orchestrator-section4-tiers-on.md`, alle Rollen aktiv) byte-identisch — genauer: §4 ist byte-identisch, **sofern alle in §4 genannten Rollen und Pipelines aktiv sind**. Neben der Tier-Kette sind in §4 auch die Concept-Rollen (`ROLE_CONCEPT_*_ACTIVE`, IC-18 Nr. 5), `effort-estimator` (Routing-Policy Nr. 2) und `concept-driven-dev` (`PIPELINE_CONCEPT_DRIVEN_DEV_ENABLED`) konditional. Entscheidung: Routing-Policy Nr. 2 bleibt gegatet, weil AC-49 für den Orchestrator 0 `dangling-mention` außerhalb `mention_allow` verlangt; mit `DEVELOPER_TIERS_ENABLED=true` und inaktivem `effort-estimator` weicht §4 daher bewusst ab. `ESCALATE_CARD_BLOCK` (`config.py`) enthält keine Tier-Namen und blieb unverändert; gegatet sind §3 Nr. 3, §4, Task-Size-Tabelle, ESCALATE-Intake, `developer` (`RECOMMENDED_TIER`) und `planner` (Schritt-Mapping, Delegationsmuster). Das Output-Guard-Beispiel in `planner` („e.g., `senior-developer`") bleibt, weil der Golden-Normalisierungseintrag `OG-PASS-PLANNER` den Quelltext pinnt (reine Erwähnung).
4. **Datenquelle Anti-Recursion (1.14):** neuer Top-Level-Key `anti_recursion.reference_roles` in `config/role-defaults.yaml`; `load_roles_config` liefert ihn mit aus.
5. **Konditional-Engine (1.15–1.19):** ein einfaches `{{#if}}` am Zeilenende verschluckt im `false`-Fall den Zeilenumbruch; Zeilenend-Segmente nutzen daher `{{#if X}}…{{else}}{{/if}}`. `DIRECT_DISPATCH_SECTION` wird im Builder gegen das ActiveSet aufgelöst (der Wert ist für Orchestrator und `use-orchestrator`-Rule final). Standalone-Export setzt `ROLE_*_ACTIVE`/`DEVELOPER_TIERS_ENABLED`/`PIPELINE_*_ENABLED` auf `true` (alle Rollen exportiert); das behebt nebenbei den doppelten Zweig in `standalone/agents/meta-doctor.md`.
6. **Commands (1.17):** `requires_roles` ist Generator-Direktive und wird aus dem gerenderten Command entfernt (Default byte-identisch). Command-Bodies lösen zusätzlich `ROLE_*_ACTIVE`-Konditionale auf (`add-provider`, `add-project-role`). Neuer Check `commands.requires-roles-invalid` (ERROR).
7. **Rules (1.18):** `rules/1-generic/threat-model.md` existiert nicht; umgesetzt in `threat-model-4-questions.md`. Der Block-Katalog in `security-paved-roads` bleibt vollständig, nur die Eigentümer-Zelle ist konditional.
8. **IC-30-Triage (1.19):** neue Guard-Regel `D-CONDITIONAL` (Zielrolle steht im positiven Zweig ihres eigenen `{{#if ROLE_<ZIEL>_ACTIVE}}`, Block oder Inline-Segment); alle Registry-Zeilen (Klassen A–F) sind konditional, `ROUTE_RATCHET` ist leer. Zusätzlich aus IC-19 (nicht in der Guard-Registry): `bug-feature-analyzer`-Konsultationstabelle, `log-analyzer`-Delegationstabelle, `documenter`-KE-Route. 36 Patch-Bumps.
9. **1.20 teilweise:** `active-set.dangling-dispatch` ist ERROR (Sync-Ende weiter report-only, Eintrag in der sync.log-Fehlerliste), der Scan umfasst zusätzlich Rules, Commands und `pipeline-details`; Fixture-Matrix × alle Provider = 0 Dispatch, 0 Mention in Orchestrator/Pipelines/Commands (`mention_allow: '*add-project-role.*'`). **Offen:** `RAW_ROLES_RATCHET` behält drei Schnittmengen-Stellen (`_sync_stage_auto_commit_allowlist`, `sync_external_skills_for_provider`, `_build_platform_variables`). Die Spec-Form (`sorted(ActiveSet.roles)` statt Rohliste) ändert das Default-Verhalten (ohne `roles:`-Key erhielten alle berechtigten aktiven Rollen Commit-Autorität bzw. Scout-Skill/`WEB_PROJECT_ENABLED` folgen nicht mehr der Rohliste) — Nutzerentscheidung nötig (Alternative: Rohliste als sanktioniertes Feld/Helper in `active_set.py`). **`--doctor`:** der Seed `dangling-role-dispatch` (Registry ERROR) übernimmt jetzt die Check-Stufe ERROR — ein hängender Dispatch lässt `--doctor` mit Exit 1 enden. Der Scan ist daher auf von agent-meta verwaltete Dateien begrenzt: in Rules-/Commands-Verzeichnissen nur Dateien aus den Managed-Indizes (`.agent-meta-managed*`, inkl. MCP/External-Tool-Rules); eigene Commands/Rules des Projekts werden nicht gescannt (Agents-Verzeichnis und `pipeline-details` wie bisher vollständig). **QG-13 dynamisch:** `sync_commands_for_provider` und `_build_orch_variables` (ANTI_RECURSION_BLOCK/DIRECT_DISPATCH_SECTION) stehen im Identitäts-Spy (`tests/test_active_set_consumers_identity.py`); der Test-Repo-Pfad (`validate_test_repo`) berechnet ein eigenes ActiveSet (eigener Sync) und reicht es an Variablen, Agenten, Commands und Skills weiter. Verbleibende Lücke: `context.py` (`build_agent_hints`-Fallback, `get_active_agents_data`) ruft weiter `resolve_active_roles` (siehe 1.10 Nr. 8); Rules erhalten die Rollen-Flags über `variables` (aus demselben ActiveSet), nicht als Objekt.
   **Entscheidung D1 (2026-10-15):** Die Rohliste wird ein freigegebenes, dokumentiertes Feld (`RAW_ROLES`) in `scripts/lib/active_set.py` (kein Verhaltenswechsel, Auto-Commit-Default bleibt `[]`); Umsetzung als eigener PR G nach PR F. `RAW_ROLES_RATCHET` bleibt bis dahin unverändert.
10. **Version-Bumps:** `orchestrator` 8.5.0 und `developer` 4.8.0/`planner` 1.6.0 (Minor) einmal je PR in 1.13; 1.16/1.19 bumpen diese nicht erneut. `planner` bleibt Minor: Konventionen Hard Invariant 2 — das Gating ist eine konditionale Verhaltensvariante (erweiterter Geltungsbereich), keine reine Textkorrektur. Review-Nachzug: `homeassistant-developer` auf `developer.md@4.8.0` re-pinnt, `gemini-orchestrator-first` 1.0.1.
11. **Guard-Härtung (Review):** `D-CONDITIONAL` gilt nur in Dateien mit wohlgeformten Markern (`marker_problems`: balanciert, Block-Marker auf eigener Zeile nur mit Block-Markern geschlossen, Inline-Marker auf derselben Zeile geöffnet/geschlossen); Repo-weiter Balance-Test über `agents/`, `rules/`, `commands/`, `snippets/`, `templates/` (ohne `templates/context/`, eigener Renderer mit `{{#each}}`). `templates/direct-dispatch-section.md` darf nur `ROLE_*_ACTIVE`-Konditionale enthalten (Test).
12. **Bekannte kosmetische Lücken (nicht behoben):** Persona-AI-Review-Satz ist alles-oder-nichts (bei teilaktiven drei Rollen neutraler Satz); „Developer-Tier nach Größe wählen" bleibt bei inaktiven Tiers stehen; Tabellen können nur aus Kopfzeile bestehen (Direkt-Dispatch ohne aktive Zeilenrolle, Konsultationstabellen); Pfeile ohne Ziel bleiben als Grenzsatz stehen (z. B. „- No engineering review").

### Task 1.21: `shared_users` auf aktive Provider begrenzen (IC-15 Nr. 1)
Rolle: developer · Issue: aus 1.00 · Depends: 1.01 · AC: AC-10, AC-21 (Teil)
**Files:** Modify `scripts/lib/context.py` (`_build_managed_block`, `_shared_rules_file_channel`); Test Create `tests/test_shared_users_active_only.py`
**Interfaces:** Produces Pfadlisten nur aktiver Teiler; Consumes Liste aktiver Provider
- [ ] Step 1: Test schreiben (fail): Einzelprovider-AGENTS.md nennt Pfade inaktiver Teiler
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_shared_users_active_only.py -q`
- [ ] Step 4: commit `fix: limit shared context users to active providers`

### Task 1.22: Lazy-Skills für jeden Skills-Kanal schreiben (IC-15 Nr. 2, IC-33)
Rolle: senior-developer · Issue: #971 · Depends: 1.21 · AC: AC-11 (Teil) · Falle: Bedingung über `rules_read_channels` (kein nativer Rules-Kanal, aber `skills`), nie über Providernamen.
**Files:** Modify `scripts/lib/rules.py` (`sync_embedded_rule_files`), `config/ai-providers.yaml` (`skills_dir`); Test Create `tests/test_lazy_skills_channel.py`
**Interfaces:** Produces Skills unter `.agents/skills`, `.mammouth/skills`, `.continue/skills`, `.github/skills`; Consumes `rules_read_channels`, `skills_discovery_dirs`
- [ ] Step 1: Test schreiben (fail): Matrix zeigt fehlende Skills und Gemini-lazy-Verlust
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_lazy_skills_channel.py -q`
- [ ] Step 4: commit `fix: write lazy rule skills for every skills channel`

### Task 1.23: Ungelesene Verzeichnisse nicht mehr schreiben (IC-15 Nr. 9)
Rolle: developer · Issue: #971 · Depends: 1.22 · AC: AC-19
**Files:** Modify `config/ai-providers.yaml` (`rules_dir`), `scripts/lib/context.py` (`init_claude_personal`), `config/context-anchors.yaml` (`intentional_unread`); Test Create `tests/test_unread_channels_removed.py`
**Interfaces:** Produces kein `.mammouth/rules`, kein Root-`rules/` für Codex, `CLAUDE.local.md`; Consumes `check_unread_channel`
- [ ] Step 1: Test schreiben (fail): `context.unread-channel`-WARNs > 0
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_unread_channels_removed.py -q`
- [ ] Step 4: commit `fix: stop writing directories providers do not read`

### Task 1.24: Erreichbarkeits-Checks auf ERROR heben
Rolle: tester · Issue: #971 · Depends: 1.23, 1.33 · AC: AC-11, AC-12, AC-19
**Files:** Modify `scripts/lib/consistency/context_budget.py`; Test Modify `tests/test_provider_matrix_sync.py`
**Interfaces:** Produces ERROR für `context.dangling-pointer`, `context.rule-unreachable`, `context.declared-surface-empty`; Consumes 9 Provider × Rules-Presets
- [ ] Step 1: Test schreiben (fail): ERROR-Stufe und Null-Befunde
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_provider_matrix_sync.py tests/test_context_budget_checks.py -q`
- [ ] Step 4: commit `fix: promote dangling pointer and reachability to error` (PR-Text: `Closes #971`)

#### Umsetzungs-Nachzüge 1.21–1.24, 1.33 (zur Spec-Aufnahme)
Die freigegebene Spec bleibt unverändert; die folgenden Abweichungen/Entscheidungen sind umgesetzt (PR E).
1. **Embed-Entscheidung über Lese-Kanäle (1.21):** `shared_users` = aktive Teiler (+ rendernder Provider). Damit darf die Entscheidung „native Rules-Pointer statt Einbettung" nicht mehr an `has_rules` hängen — sonst verlören Einzelprovider-Projekte mit ungelesenem `rules_dir` (Codex, Mammouth, Gemini) alle eingebetteten Rules. Neu: Pointer nur, wenn jeder aktive Teiler einen nativen Rules-Kanal liest (`rules_read_channels` ∋ `native-rules-dir`/`path-scoped`); Lazy-Kanal, wenn jeder aktive Teiler `skills` liest. Helper-Modul `scripts/lib/rule_channels.py` (nicht in der Files-Liste; Fallback auf die alte `has_rules`/`skills_dir`-Semantik für Einträge ohne `rules_read_channels`). `_shares_context_with_embedded_rules` (Strategie-Wahl) bleibt katalogweit. Die committete Self-Hosting-`AGENTS.md` wurde nachgezogen (Frische-Test `test_context_compact_mode`); die Konvergenz-Tests (#638/#794) prüfen jetzt aktive Teiler bzw. ein Projekt mit allen Teilern aktiv.
2. **Kanal-Daten (1.22, nicht nur `skills_dir`):** `rules_read_channels` erhält `skills` für Opencode, ZCode, KimiCode, Mammouth (`[embedded, skills]`), Gemini und Copilot (`[skills]`) und Continue (`[native-rules-dir, skills]`). Ohne den Eintrag verlören Opencode/ZCode/Kimi (bisher `[embedded]`) ihre heutigen Lazy-Skills. Gemini schreibt nach `.gemini/skills` (nicht `.agents/skills` wie im IC-15-Nr.-2-Text: `.agents/skills` ist Codex' Verzeichnis, gemeinsame Nutzung würde wie #638 oszillieren; die Antigravity-Discovery-Oberfläche nutzt `.agents/skills` bereits über `agent-discovery`). Continue liest native Rules, erfüllt also die IC-33-Bedingung nicht; Umsetzung über die bestehende Capability `native-skill-channel` (`channel: skill` → `.continue/skills`, Studie 3.8). Copilot: `skills_dir` `.github/skills` (Pfad-Teil von AC-14 vorgezogen), `.github/copilot/skills` in `legacy_artifacts`. `sync_embedded_rule_files` läuft jetzt auch für `has_rules`-Provider; die Lazy-MCP-/Tool-Abschnitte nutzen dieselbe Bedingung (`lazy_skill_channel`).
3. **1.23:** Codex und Mammouth erhalten `has_rules: false`; neuer Daten-Key `retired_rules_dirs` räumt bestehende Verzeichnisse nur über die Managed-Indizes (`.agent-meta-managed`, `-mcp`, `-tools`) auf, fremde Dateien bleiben, das Verzeichnis entfällt nur leer, ein von einem aktiven Provider genutztes `rules_dir` wird nie angefasst. `intentional_unread` bleibt leer: `.gemini/rules` (IC-15 Nr. 8, Task 1.28) und `.github/instructions` (IC-15 Nr. 3, Task 1.29) bleiben bewusst als `context.unread-channel`-WARN sichtbar (Test-lokale Pending-Liste statt Ausnahme, die den Defekt im sync.log verstecken würde). `CLAUDE.local.md` statt `CLAUDE.personal.md`; eine vorhandene `CLAUDE.personal.md` (Nutzerinhalt) wird nicht umbenannt — keine `CLAUDE.local.md`, Sync-Warnung mit Umbenennungs-Hinweis; der Gitignore-Eintrag für die Altdatei bleibt. **Offen:** `AGENTS.personal.md` (laut Studie 4.3 für Kimi/ZCode/Gemini/Codex inert) wird weiter angelegt — eine datengetriebene Lösung braucht einen Provider-Key „liest Personal-Datei"; die Spec nennt nur das Claude-Beispiel.
4. **1.33:** Banner aus Daten (`providers.build_provider_routing`, dieselbe Funktion wie `PROVIDER_ROUTING`, aktive Provider nach Kontextdatei gruppiert, Format `> **AI ROUTING:** …`). Der Tabellenfilter ist generisch für `| Skill |`-Tabellen in Rules (`rules.filter_skill_tables`, `rules.lazy_skill_stems` spiegelt die Writer-Entscheidungen); eine Tabelle ohne existierenden Skill unterdrückt die ganze Rule (`use-lazy-rules` entfällt im Default-Preset). **Nicht umgesetzt:** unaufgelöste Platzhalter im statischen AGENTS.md-Kopf (`{{PLATFORM}}` u. a., Projekt-Metadaten-Partial) — nicht in den Plan-Produces von 1.33, Nähe zu IC-15 Nr. 19 (Task 1.39); der Klammerverweis „(`use-lazy-rules.md`)" in `mcp-guardrails` bleibt auch ohne gerenderte Lazy-Rule stehen (kosmetisch).
5. **1.24 teilweise:** Nur `context.dangling-pointer` ist ERROR (`PHASE1_PROMOTED`; Matrix 9 Provider × `default`/`minimal`/`silent`/`lazy` = 0 Befunde, AC-11). **Offen (Nutzer-/Plan-Entscheidung):** `context.rule-unreachable` bleibt WARN — einzige Restbefunde sind Copilots nicht eingebettete Rules (18 im Default, 11–13 mit `lazy`/`silent`), behoben erst durch IC-15 Nr. 3 (Task 1.29), die laut Plan von 1.24 abhängt (DAG-Widerspruch; ERROR jetzt hieße `--doctor` Exit 1 in jedem Copilot-Projekt). `context.declared-surface-empty` bleibt WARN — die Matrix zeigt nur absichtlich leere Oberflächen (Skills ohne Lazy-Rules bei allen Providern im Default, MCP-Konfig ohne aktive Server bei Claude/Copilot/Kimi, `.codex/config.toml` bis Task 1.25); `intentional_empty` wirkt nur je Oberfläche global, die Spec braucht ein Prädikat „Inhalt erwartet" oder providerbezogene Ausnahmen. `context.unread-channel` bleibt laut Spec WARN.
6. **AC-01-Rebaseline je Task:** 1.21: 6 (AGENTS.md der 6 AGENTS.md-Provider); 1.22: 4 (Copilot-`SKILLS_DIR`-Pfad); 1.23: 49 (2 × 22 Rules-Dir-Dateien entfernt, `CLAUDE.personal.md` → `CLAUDE.local.md`, Claude-`.gitignore`, 2 × `generated-file-hashes.json`; 1075 → 1031); 1.33: 18 (6 × AGENTS.md, 4 × `use-lazy-rules.md` entfernt + deren Managed-Index und `generated-file-hashes.json`; 1031 → 1027); 1.24: 0. Budget-Pins nur gesenkt (Entry-File −1.5 KB je AGENTS.md-Provider, Rules −1.0 KB, Codex/Mammouth-`rules`-Pin entfällt).

7. **Nutzerentscheidungen (2026-10-15, nach Review PR E):** `context.rule-unreachable` bleibt WARN und wird erst nach Task 1.29 (Copilot `.github/instructions`) auf ERROR gehoben (DAG 1.29 → 1.24); `context.declared-surface-empty` bleibt vorerst WARN — das Prädikat „Inhalt erwartet" (`content_expected`, ersetzt das globale `intentional_empty`) wird in PR F eingeführt, die Promotion in `PHASE1_PROMOTED` erst, wenn die 9×4-Matrix 0 Befunde zeigt; `AGENTS.personal.md` für Provider ohne Personal-Datei-Leser (Kimi/ZCode/Gemini/Codex, inert) wird in PR F datengetrieben über einen Provider-Key „liest Personal-Datei" gelöst. Datei-Korrektur: `rules_read_channels` steht in `config/provider-capabilities.yaml` (nicht `ai-providers.yaml`); `config/ai-providers.yaml` trägt `skills_dir`.

#### Wiederaufnahme-Stand PR E
Branch `feat/active-set-reachability` (Basis `d57c7ca`), nicht gepusht.
- **1.21 erledigt:** `4bac743` (+ `e7d129f` committete AGENTS.md nachgezogen).
- **1.22 erledigt:** `bd55492`.
- **1.23 erledigt:** `a86760c`. Offen: `AGENTS.personal.md` für Provider, die sie nicht lesen (Nachzug 3).
- **1.33 erledigt:** `5ea469e` (+ Unit-Test `15a9b09`). Offen: unaufgelöste Platzhalter im statischen AGENTS.md-Kopf (Nachzug 4).
- **1.24 teilweise:** `0d1da05` — nur `context.dangling-pointer` ERROR. Ausstehende Entscheidungen: `context.rule-unreachable` erst nach Task 1.29 (Copilot) auf ERROR heben (DAG-Widerspruch 1.29 → 1.24); `context.declared-surface-empty` braucht ein Prädikat „Inhalt erwartet" oder providerbezogene `intentional_empty` (Nachzug 5). Nächster Schritt: Nutzerentscheidung, dann Eintrag in `PHASE1_PROMOTED` (`scripts/lib/consistency/context_budget.py`) + Test in `tests/test_provider_matrix_sync.py` erweitern.
- Doku/Pins: `7946b9f` (Nachzüge, Budget-Pins nur gesenkt).
- **Tests (finaler Baum, vor diesem Doku-Commit):** `pytest tests/test_[a-m]*.py -n 4` 2887 passed/4 skipped; `pytest tests/test_[n-z]*.py -n 4` 2723 passed/1 skipped; `scripts/consistency-check.py` 15 WARN (alle `based-on-stale`); `sync.py --validate` 1 bekannte WARN. Neue Tests: `test_shared_users_active_only.py`, `test_lazy_skills_channel.py`, `test_unread_channels_removed.py`, `test_context_header_noise.py`, Matrix in `test_provider_matrix_sync.py`.
- **Bekannte Punkte:** die Matrix-Tests (9 Provider × 4 Presets) verlängern die Suite um mehrere Minuten; Rebaseline nur per `python tests/test_ac01_render_identity.py --write`.
- **Review (2026-10-15):** Stufe 1 (Anforderungen) und Stufe 2 (Qualität) je `APPROVED_WITH_RECOMMENDATIONS`, Rating 4/5, keine Blocker. Fix-Commit (dieser Commit): `filter_skill_tables`-Docstring + `skills_dir`-Guard-Klarstellung (`pc` vs. gemergte `caps`, Finding 5 bewusst nicht entfernt), Test nutzt `rules.provider_opts_skip`; Plan-Nachzüge. Findings 1/4/7 und die offenen AC-12/AC-19-Punkte bleiben bewusst offen bzw. gehen nach PR F.
- **CI-Drift-Gate (2026-10-15):** Der `validate`-Job generiert jetzt vor den Reachability-Checks (`CLAUDE.local.md` in den `.gitignore`-Managed-Block nachgezogen) und prüft Drift über `git status`; `.meta-config/` ist ausgenommen, weil `.meta-config/auto-commit-allowlist.json` und `.meta-config/generated-file-hashes.json` bereits auf `main` gegenüber dem Generator veralten (vom alten `--check` nicht erfasst) — Follow-up, nicht PR E.

### Task 1.25: Codex-Dispatch-Tiefe, Hard-Cap und spawn_agent-Syntax (IC-15 Nr. 4)
Rolle: senior-developer · Issue: #972 · Depends: 1.24 · AC: AC-13, AC-15 · Falle: Capture-Teil (QG-7) manuell, Ergebnis im PR; nie stilles Schreiben über dem Cap.
**Files:** Create `scripts/lib/dispatch_depth.py`; Modify `scripts/lib/context.py` (`_sync_managed_block_context`), `config/delegation-syntax.yaml`, `config/ai-providers.yaml`; Test Create `tests/test_dispatch_depth_and_hard_cap.py`
**Interfaces:** Produces `write_dispatch_depth_config(project_root: Path, pc: dict, capabilities: Mapping, dry_run: bool) -> list[str]` (`[agents] max_depth ≥ required_depth`), Sync-Abbruch `context.over-hard-cap`; Consumes `agent_config_format`, `required_depth`, `check_over_hard_cap`
- [ ] Step 1: Test schreiben (fail): `.codex/config.toml` ohne `max_depth`; 6-Provider-AGENTS.md ≥ 32,768 B wird geschrieben
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_dispatch_depth_and_hard_cap.py -q`
- [ ] Step 4: commit `fix: enforce dispatch depth config and context hard cap` (PR-Text: `Closes #972`)

### Task 1.26: Kimi-Orchestrator-Frontmatter korrigieren (IC-15 Nr. 5)
Rolle: developer · Issue: #973 · Depends: 1.20 · AC: AC-16 · Falle: Runtime-Bestätigung nur mit Kimi-Runtime, sonst UNVERIFIED im PR.
**Files:** Modify `config/ai-providers.yaml` (`agent-transform`), `scripts/lib/provider_transform.py` (`_apply_agent_transform`, `_apply_tool_name_map`); Test Create `tests/test_subagent_allowlist_frontmatter.py`
**Interfaces:** Produces `subagents:` aus aktiven delegierbaren Rollen, Tool-Mapping, `hint` → `whenToUse`; Consumes `subagent_allowlist_required`, `ActiveSet`
- [ ] Step 1: Test schreiben (fail): Orchestrator-Frontmatter ohne `subagents` bzw. mit Claude-Toolnamen
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_subagent_allowlist_frontmatter.py -q`
- [ ] Step 4: commit `fix: emit subagent allowlist and mapped tools for kimi` (PR-Text: `Closes #973`)

### Task 1.27: Mammouth-Dispatch freischalten (IC-15 Nr. 6)
Rolle: developer · Issue: #974 · Depends: 1.26 · AC: AC-17
**Files:** Modify `config/provider-capabilities.yaml` (`subagent_dispatch`), `config/ai-providers.yaml`, `scripts/lib/provider_transform.py`; Test Create `tests/test_dispatch_permissions_frontmatter.py`
**Interfaces:** Produces `mode`, kleingeschriebene `permission` inkl. `task`/`todowrite`, `subagent_depth ≥ 2`; Consumes `required_depth`
- [ ] Step 1: Test schreiben (fail): Orchestrator ohne `task`, `mode` oder Tiefe
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_dispatch_permissions_frontmatter.py -q`
- [ ] Step 4: commit `fix: enable task dispatch and depth for mammouth agents` (PR-Text: `Closes #974`)

### Task 1.28: Gemini-CLI-Kontextdatei setzen (IC-15 Nr. 8)
Rolle: developer · Issue: #975 · Depends: 1.23 · AC: AC-18
**Files:** Modify `scripts/lib/context.py` (`_adapter_settings_activation`), `config/ai-providers.yaml` (`rules_dir`); Test Create `tests/test_context_filename_settings.py`
**Interfaces:** Produces `.gemini/settings.json` mit `context.fileName`, kein `.gemini/rules`; Consumes `settings_file`
- [ ] Step 1: Test schreiben (fail): `context.fileName` fehlt, `.gemini/rules` wird geschrieben
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_context_filename_settings.py -q`
- [ ] Step 4: commit `fix: set gemini context filename and drop unread rules dir` (PR-Text: `Closes #975`)

### Task 1.29: Copilot-Rules, Agent-Name und Skills-Pfad korrigieren (IC-15 Nr. 3)
Rolle: developer · Issue: #976 · Depends: 1.24 · AC: AC-14
**Files:** Modify `scripts/lib/rules.py` (`sync_rules`), `scripts/lib/agent_sync.py` (`_finalize_agent_content`), `config/ai-providers.yaml`; Test Create `tests/test_rules_required_suffix.py`
**Interfaces:** Produces `.github/instructions/` mit Suffix `.instructions.md` und `applyTo`/`description`, Frontmatter `name: orchestrator`, `.github/skills`; Consumes `rules_required_suffix`, `agent_ext`
- [ ] Step 1: Test schreiben (fail): Datei ohne Suffix existiert; `name: orchestrator.agent`
- [ ] Step 2: implementieren (Altdateien über Managed-Cleanup)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_rules_required_suffix.py -q`
- [ ] Step 4: commit `fix: write copilot instructions with suffix and agent name` (PR-Text: `Closes #976`)

### Task 1.30: ZCode-CLI-Bootstrap entfernen (IC-15 Nr. 7) — Eintritt erst nach Q34
Rolle: developer · Issue: aus 1.00 · Depends: Q34 (Capture CLI + Desktop) · AC: AC-21
**Files:** Modify `scripts/lib/bootstrap.py`, `config/provider-bootstrap.yaml`, `config/provider-capabilities.yaml`; Test Create `tests/test_bootstrap_active_providers.py`
**Interfaces:** Produces kein CLI-Bootstrap, korrigierte Parallel-Capability, Bootstraps nur aktiver Provider; Consumes `surface_verified_state.workspace_agents_autoload`
- [ ] Step 1: Test schreiben (fail): Bootstrap-Block für CLI vorhanden
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_bootstrap_active_providers.py -q`
- [ ] Step 4: commit `fix: drop obsolete zcode cli bootstrap block`

### Task 1.31: Continue-Rule-Frontmatter und Platzhalter (IC-15 Nr. 10)
Rolle: developer · Issue: aus 1.00 · Depends: 1.03 · AC: AC-10
**Files:** Modify `scripts/lib/rules.py` (`_build_always_apply_frontmatter`), `scripts/lib/context.py` (`_sync_continue_context`); Test Create `tests/test_continue_rule_frontmatter.py`
**Interfaces:** Produces `alwaysApply`, `description`, keine unaufgelösten Platzhalter in `project-context.md`; Consumes `check_unresolved_placeholder`
- [ ] Step 1: Test schreiben (fail): fehlendes Frontmatter bzw. Platzhalter vorhanden
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_continue_rule_frontmatter.py -q`
- [ ] Step 4: commit `fix: add continue rule frontmatter and resolve placeholders`

### Task 1.32: `AGENT_DELEGATION_TABLE` als gültige Tabelle (IC-15 Nr. 11)
Rolle: developer · Issue: aus 1.00 · Depends: 1.16 · AC: AC-20
**Files:** Modify `scripts/lib/config.py` (`AGENT_DELEGATION_TABLE`), `templates/context/partials/agents-table.md`, `agents/1-generic/orchestrator.md`, `tests/fixtures/slimming-golden/orchestrator.md`; Test Modify `tests/test_delegation_table.py`
**Interfaces:** Produces eine Tabelle mit einem Header ohne Leerzeilen; Consumes `AGENT_DELEGATION_TABLE`
- [ ] Step 1: Test schreiben (fail): Markdown-Parser findet zwei Header bzw. Leerzeilen
- [ ] Step 2: implementieren (Golden-Rebaseline mit Begründung)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_delegation_table.py tests/test_template_slimming_equivalence.py -q`
- [ ] Step 4: commit `fix: render agent delegation table as one valid table`

### Task 1.33: Provider-Rauschen, Lazy-Tabelle und Banner bereinigen (IC-15 Nr. 12)
Rolle: developer · Issue: aus 1.00 · Depends: 1.22 · AC: AC-21 (Teil), AC-11
**Files:** Modify `templates/context/partials/header.md`, `rules/1-generic/use-lazy-rules.md`, `scripts/lib/config.py`; Test Create `tests/test_context_header_noise.py`
**Interfaces:** Produces ROUTING-Banner nur aktiver Provider, Lazy-Tabelle nur existierender Skills; Consumes `check_dangling_pointer`
- [ ] Step 1: Test schreiben (fail): Banner nennt inaktive Provider; Tabelle nennt fehlende Skills
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_context_header_noise.py -q`
- [ ] Step 4: commit `fix: list only active providers and existing lazy skills`

### Task 1.34: Orchestrator-Hint auf `claude --agent` korrigieren (IC-15 Nr. 13)
Rolle: developer · Issue: aus 1.00 · Depends: 1.01 · AC: AC-10
**Files:** Modify `config/ai-providers.yaml` (`orchestrator_hint`); Test Create `tests/test_orchestrator_hint_flag.py`
**Interfaces:** Produces `orchestrator_hint` mit `--agent`; Consumes Provider-Config-Loader `scripts/lib/providers.py`
- [ ] Step 1: Test schreiben (fail): Hint enthält `claude -a`
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_orchestrator_hint_flag.py -q`
- [ ] Step 4: commit `fix: use claude --agent in orchestrator hint`

### Task 1.35: `template-auditor` ohne Keyword-Regel (IC-15 Nr. 14)
Rolle: developer · Issue: aus 1.00 · Depends: 1.01 · AC: AC-22 (Teil)
**Files:** Modify `config/role-defaults.yaml` (`routing_patterns` entfernen), `tests/scenarios/asserts/76-template-auditor-role.sh` (Assert #5); Test Modify `tests/test_role_addressability_coverage.py`
**Interfaces:** Produces keine Keyword-Regel in `routing.rules`; Consumes `test_name_only_roles_have_no_routing_patterns`
- [ ] Step 1: Test schreiben (fail): name_only-Rolle mit `routing_patterns`
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_role_addressability_coverage.py -q && bash tests/scenarios/run.sh 76-template-auditor-role`
- [ ] Step 4: commit `fix: remove keyword routing from name-only template-auditor`

### Task 1.36: Keywords in einer Quelle halten (IC-15 Nr. 15)
Rolle: developer · Issue: aus 1.00 · Depends: 1.35 · AC: AC-22
**Files:** Modify `config/role-defaults.yaml`, `scripts/hermes_export.py`, `scripts/lib/delegation_table.py` (`get_routing_rules`); Test Modify `tests/test_routing_tool_definitions.py` (Gleichheitstest entfällt)
**Interfaces:** Produces nur `routing_patterns.keywords`; Consumes `get_routing_rules`
- [ ] Step 1: Test schreiben (fail): „kein Eintrag enthält `routing.intent_keywords`" ist rot
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_routing_tool_definitions.py -q`
- [ ] Step 4: commit `fix: keep routing keywords in a single source`

### Task 1.37: OpenCode-Tiefe erhalten, kein AGENTS.md-Deny (IC-15 Nr. 16)
Rolle: developer · Issue: aus 1.00 · Depends: 1.01 · AC: AC-10
**Files:** Modify `scripts/lib/context.py` (`apply_settings_surface_shape`); Test Create `tests/test_settings_depth_and_deny.py`
**Interfaces:** Produces `subagent_depth` auf v2 erhalten, kein `**/AGENTS.md`-Deny bei aktivem Leser; Consumes `required_depth`, `agents_md_visible_to_subagents`
- [ ] Step 1: Test schreiben (fail): v2-Settings ohne Tiefe; Deny vorhanden
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_settings_depth_and_deny.py -q`
- [ ] Step 4: commit `fix: keep subagent depth and agents.md access in settings`

### Task 1.38: Reflection-Overrides aus Konsumenten-Config lesen (IC-15 Nr. 17)
Rolle: developer · Issue: aus 1.00 · Depends: 1.01 · AC: AC-51
**Files:** Modify `scripts/lib/config.py` (Reflection-Overrides); Test Create `tests/test_reflection_overrides_source.py`
**Interfaces:** Produces Aufruf `apply_project_overrides(pairs, (config.get("reflection-pairs") or {}).get("overrides", {}))`; Consumes `reflection.apply_project_overrides(pairs, overrides)`
- [ ] Step 1: Test schreiben (fail): Konsument ohne Override erhält agent-meta-Wert statt `MAX_ITERATIONS=3`
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_reflection_overrides_source.py -q`
- [ ] Step 4: commit `fix: read reflection overrides from consumer config`

### Task 1.39: `--create-ext` ohne literale Platzhalter (IC-15 Nr. 19)
Rolle: developer · Issue: aus 1.00 · Depends: 1.01 · AC: AC-10
**Files:** Modify `scripts/lib/extensions.py`, `templates/managed-block.md`; Test Create `tests/test_create_ext_unresolved.py`
**Interfaces:** Produces Zeile weggelassen bzw. „nicht gesetzt"; Consumes `check_unresolved_placeholder`
- [ ] Step 1: Test schreiben (fail): erzeugte Extension enthält eine unaufgelöste Variable
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_create_ext_unresolved.py -q`
- [ ] Step 4: commit `fix: omit unresolved variables in created extensions`

### Task 1.40: Read-only-Rollen auf Sandbox `read-only` abbilden (IC-15 Nr. 21)
Rolle: developer · Issue: aus 1.00 · Depends: 1.25 · AC: AC-10
**Files:** Modify `config/ai-providers.yaml` (`sandbox_mode`), `config/provider-capabilities.yaml` (`read_only_enforcement: sandbox`), `scripts/lib/provider_transform.py`; Test Create `tests/test_read_only_sandbox.py`
**Interfaces:** Produces `sandbox_mode: read-only` für Rollen ohne `Write`/`Edit`; Consumes `read_only_enforcement`
- [ ] Step 1: Test schreiben (fail): read-only Rolle erhält `workspace-write`
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_read_only_sandbox.py -q`
- [ ] Step 4: commit `fix: map read-only roles to sandbox read-only mode`

### Task 1.41: Gemini-Commands je Oberfläche (IC-15 Nr. 22) — Eintritt erst nach Q33
Rolle: developer · Issue: aus 1.00 · Depends: Q33 · AC: AC-10, AC-67
**Files:** Modify `config/ai-providers.yaml` (Commands-Deklaration), `scripts/lib/commands.py`; Test Create `tests/test_commands_surface_state.py`
**Interfaces:** Produces Commands nur mit belegtem `surface_verified_state.commands` bzw. als Skills; Consumes `check_declared_surface_empty`
- [ ] Step 1: Test schreiben (fail): `surface-unverified`/`declared-surface-empty` meldet die Oberfläche
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_commands_surface_state.py -q`
- [ ] Step 4: commit `fix: gate gemini commands on verified surface state`

### Task 1.42: Provider-Literale aus generischen Templates entfernen (IC-15 Nr. 23)
Rolle: prompt-engineer · Issue: aus 1.00 · Depends: 1.19 · AC: AC-73 · Falle: prüfen, ob `resolve_active_roles(require_template=True)` ein `1-generic`-Template für `mammouth-expert` verlangt (Spec UNVERIFIED).
**Files:** Modify `agents/1-generic/mammouth-expert.md`, `agents/1-generic/knowledge-migrator.md`, `agents/1-generic/agent-meta-scout.md`, `agents/1-generic/prompt-governor.md`, `agents/1-generic/agent-meta-manager.md`, `scripts/lib/consistency/provider_literals.py` (ERROR); Create `agents/2-platform/agent-meta-mammouth-expert.md`; Test Modify `tests/test_template_integrity_checks.py`
**Interfaces:** Produces `templates.provider-literal` ERROR mit 0 Treffern außerhalb der Allowlist; Consumes `{{CONTEXT_FILE}}`, `provider_literal_allow`
- [ ] Step 1: Test schreiben (fail): ERROR-Stufe meldet ≥ 1 Treffer
- [ ] Step 2: implementieren (Rollen-Key und Pins bleiben; Version-Bumps)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_template_integrity_checks.py -q && python3 scripts/consistency-check.py`
- [ ] Step 4: commit `fix: move provider literals out of generic templates`

### Task 1.43: `based-on`-Pins nachziehen (IC-15 Nr. 24)
Rolle: developer · Issue: aus 1.00 · Depends: 1.42 · AC: AC-74
**Files:** Modify die 16 von `check_based_on_stale` gemeldeten `agents/2-platform/*.md`, `scripts/lib/consistency/frontmatter.py` (ERROR); Test Modify `tests/test_template_integrity_checks.py`
**Interfaces:** Produces `frontmatter.based-on-stale` ERROR mit 0 Befunden; Consumes inhaltlichen Abgleich je Override
- [ ] Step 1: Test schreiben (fail): ERROR-Stufe schlägt an
- [ ] Step 2: implementieren (Re-Pin nach Inhaltsabgleich)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_template_integrity_checks.py -q`
- [ ] Step 4: commit `fix: re-pin stale based-on versions in platform overrides`

### Task 1.44: `--deactivation-status` read-only machen (IC-15 Nr. 25, optional)
Rolle: developer · Issue: aus 1.00 · Depends: 0e · AC: AC-85 (Wiederaufnahme-Bedingung)
**Files:** Modify `scripts/lib/cli_commands.py` (Handler `--deactivation-status`), `scripts/sync.py`; Test Create `tests/test_deactivation_status_read_only.py`
**Interfaces:** Produces Handler mit `ctx.read_only = True` nach Muster `--cleanup-preview`; Consumes `_build_context`
- [ ] Step 1: Test schreiben (fail): Self-Hosting-Snapshot zeigt geänderte `sync.log`/Env-Skripte
- [ ] Step 2: implementieren (Allowlists erst danach, eigener PR)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_deactivation_status_read_only.py -q`
- [ ] Step 4: commit `fix: make --deactivation-status read-only`

### Task 1.45: Routing-Beispiele nach Projektsprache wählen (IC-29, `full`-JSON)
Rolle: developer · Issue: aus 1.00 · Depends: 0b · AC: AC-69 (`full`-Teil) · Falle: Auswahl nur über `_select_examples`, keine zweite Logik.
**Files:** Modify `scripts/lib/delegation_table.py`, `tests/test_role_addressability_coverage.py` (Mapping-Sprachabdeckung); Test Create `tests/test_routing_examples_language.py`
**Interfaces:** Produces `examples` als Liste oder Mapping Sprachwert → Beispiele; Consumes `_select_examples(examples: object, language: str) -> list[str]`, `COMMUNICATION_LANGUAGE`
- [ ] Step 1: Test schreiben (fail): DE/EN-Fixture aus gleicher Quelle, identische Keyword-Mengen, Fallback-INFO
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_routing_examples_language.py -q`
- [ ] Step 4: commit `feat: select routing examples by project language`

### Task 1.46: Deutsche Keyword-Varianten migrieren (IC-29, eval-gated)
Rolle: developer · Issue: aus 1.00 · Depends: 1.45, 0f.3 (AC-62 belegt) · AC: AC-68 · Falle: ein Eval-Lauf je PR nach Freigabe; `SKIPPED-BY-USER` ⇒ nicht mergen.
**Files:** Modify `config/role-defaults.yaml`, `config/routing-language.yaml`; Test Modify `tests/test_routing_keywords_language_neutral.py`
**Interfaces:** Produces DE-Varianten unter `examples.Deutsch`, schrumpfende `keyword_allow`; Consumes `eval_gate.evaluate_gate`
**Voraussetzung (Follow-up aus 1.45-Review F-2):** `scripts/gen_role_routing_eval_catalog.py` muss vor 1.46 mapping-fähig gemacht werden (`examples` als Mapping lesen); Sprach-Keys (`Deutsch`/`English`/…) dürfen nicht als Korpus-Tasks/Kollisionsbasis landen.
- [ ] Step 1: Test schreiben (fail): Ratchet-Grenze für `keyword_allow` senken
- [ ] Step 2: implementieren (Batch-Eval protokollieren)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_routing_keywords_language_neutral.py -q`
- [ ] Step 4: commit `chore: migrate german keyword variants to examples`

### Task 1.47: Overlap-Tokens schärfen (IC-29, eval-gated)
Rolle: developer · Issue: aus 1.00 · Depends: 1.46 · AC: AC-70 · Falle: wie 1.46; bei Skip bleibt das Token in `KNOWN_KEYWORD_OVERLAPS`.
**Files:** Modify `config/role-defaults.yaml`; Test Modify `tests/test_routing_overlap.py`
**Interfaces:** Produces geschärfte Tokens, gekürzte `KNOWN_KEYWORD_OVERLAPS`; Consumes `eval_gate.evaluate_gate`, AC-62-Fälle
- [ ] Step 1: Test schreiben (fail): `KNOWN_KEYWORD_OVERLAPS` um die geschärften Tokens kürzen
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_routing_overlap.py -q`
- [ ] Step 4: commit `chore: sharpen overlapping routing keywords`

## Roadmap Phase 2 (Profil `compact`, Config-Optimizer)

Der Detailplan folgt nach Abschluss von Phase 1 als eigene Plan-Datei unter `docs/plans/` (Name nach Schema `JJJJ-MM-TT-context-profiles-phase2-plan.md`, Datum des Phase-2-Starts).

- **Pakete:** 2a Profil-Auflösung, Konditionale, Schema (IC-01…IC-03); 2b Routing-Zeilenformat inkl. AC-69-Zeilenformat (IC-04) und Orchestrator/Entry-File/Rules/Notizen (IC-05…IC-08, C1–C7); 2c Budgets/Anker/Report `compact` (Nutzung IC-09…IC-12); 2d Optimizer-Runner, Applier, Laufzeit-Leser-Registry (IC-24, IC-25, IC-35); 2e Rolle `meta-optimizer` und `agent-meta-manager`/Orchestrator-Schritte (IC-26, IC-27, IC-28; AC-23-Ausnahmeliste, `_EXPECTED_TOTAL` → 94).
- **Abhängigkeiten:** 2d/2e nur an 0a-III (IC-34) und 0b (IC-17), unabhängig vom Eval; 2b nach Task 1.10 (IC-18 Nr. 2).
- **Gates/Eintritt:** IC-01…IC-12 erst mit belegtem AC-02 (0f.3); IC-04 nur mit belegtem AC-25 (Eval nach Freigabe); bei `SKIPPED-BY-USER` bleibt `compact` Opt-in ohne Verifikationsanspruch (AC-86 Profil-Teil, INFO `context-profile.unverified`).
- **ACs:** AC-23…AC-32, AC-54…AC-59, AC-75 (Optimizer), AC-79…AC-83, AC-86 (Profil), AC-89…AC-91, AC-94 (Optimizer), AC-98 (`--optimize-config`).

## Roadmap Phase 3 (Erweiterungen)

Der Detailplan folgt nach Abschluss von Phase 2 als eigene Plan-Datei unter `docs/plans/` (Schema `JJJJ-MM-TT-context-profiles-phase3-plan.md`).

- **Pakete:** `ultra`/Rollenprofil und `permission.task`-Trimming; `inherit-project-context`; Kimi `${agents_md}`; Admin-UI-Umschalter; Claude `paths:`; Boilerplate-De-Dup (IC-27 Phase 3, Q6); datengetriebene Delegationslisten (Q19); L2-Relokationen.
- **Abhängigkeiten:** Profil `compact` gemergt; Q6/Q19 entschieden.
- **Gates/Eintritt:** je Option Opt-in, ohne Opt-in byte-identisch (AC-35); Evals nur nach Nutzerfreigabe (AC-33, AC-60).
- **ACs:** AC-33, AC-34, AC-35, AC-60.

## Self-Review

Ergebnis (geprüft gegen Spec §8, §9, §9.1):
- Jeder AC der Phasen 0–1 hat ≥ 1 Task; jeder Task hat einen benannten Test bzw. eine Prüfung (1.00: `gh issue list`).
- Jeder Task mappt auf genau eine Rolle; `Files:`/`Interfaces:` nie leer; keine TODO/TBD/Platzhalter.
- Parallel-Gruppen ownership-disjunkt: 0a-III-g1 (0a.5 `provider-capabilities.yaml` ↔ 0a.6 `repo_containment.py`/`config.py`), 0a-III-g2 (0a.8 ↔ 0a.9), 0b-g1 (`context_budget.py` ↔ `active_set_refs.py`), 0b-g2, 0c-g1 (Test-Guard ↔ `frontmatter.py`), 0d-g1 (0d.4 allein ausführbar neben 0d.3), 0e-g1, 0f-g1 — keine Datei doppelt.
- `pipeline_stages.implement: 3` deckt die einzige `plan-driven`-Stage ab.
- Bewusst ohne eigenen Task: IC-15 Nr. 20 (Q23 entschieden: nur Seed `variable-unreferenced`, abgedeckt in 0d.1/0d.5); IC-20/AC-53 (vertagt, #958); IC-18 Nr. 13 (Phase 2).
- Abweichung von der Spec: `_EXPECTED_TOTAL` in 0e.2 auf 93 (Spec-Wert 94 setzt `meta-optimizer` voraus).
- Abweichung vom Zielumfang: Plan > 700 Zeilen, weil 81 Tasks mit Pflicht-TDD-Steps (je eigener PR laut Spec) nicht kürzer darstellbar sind.

| AC | Task | Test |
|---|---|---|
| AC-01 | 0a.0, 0e.2, alle Phase-0-PRs | `tests/test_ac01_render_identity.py` |
| AC-02, AC-62 (Baseline) | 0f.3 | `tests/test_eval_baseline_schema.py` |
| AC-03, AC-62 (Korpus) | 0f.1 | `tests/test_role_routing_eval_catalog.py` |
| AC-04, AC-75/94/98 (Report) | 0a.7 | `tests/test_context_report.py` |
| AC-05, AC-09 | 0a.10 | `tests/test_context_docs_corrections.py` |
| AC-06 | 0a.8 | `tests/test_context_anchors.py` |
| AC-07 | 0a.9 | `tests/test_context_budgets.py` |
| AC-08 | 0b.2, 0b.6 | `tests/test_context_budget_checks.py`, `tests/test_sync_end_checks.py` |
| AC-10 | alle Phase-1-Tasks | je Task-Test (red/green im PR) |
| AC-11, AC-12, AC-19 | 1.22, 1.23, 1.24, 1.33 | `tests/test_lazy_skills_channel.py`, `tests/test_unread_channels_removed.py`, `tests/test_provider_matrix_sync.py` |
| AC-13, AC-15 | 1.25 | `tests/test_dispatch_depth_and_hard_cap.py` |
| AC-14 | 1.29 | `tests/test_rules_required_suffix.py` |
| AC-16 | 1.26 | `tests/test_subagent_allowlist_frontmatter.py` |
| AC-17 | 1.27 | `tests/test_dispatch_permissions_frontmatter.py` |
| AC-18 | 1.28 | `tests/test_context_filename_settings.py` |
| AC-20 | 1.32 | `tests/test_delegation_table.py` |
| AC-21 | 1.21, 1.30, 1.33 | `tests/test_shared_users_active_only.py`, `tests/test_bootstrap_active_providers.py`, `tests/test_context_header_noise.py` |
| AC-22 | 1.35, 1.36 | `tests/test_role_addressability_coverage.py`, `tests/test_routing_tool_definitions.py` |
| AC-36, AC-61 | Global Constraints, alle Tasks | `tests/test_provider_agnostic_dispatch.py` |
| AC-37, AC-85 (`command`) | 0d.1 | `tests/test_known_issues_registry.py` |
| AC-38, AC-76, AC-77, AC-96 | 0d.5 | `tests/test_doctor_fixtures.py` |
| AC-39, AC-42, AC-75/95/98 (Doctor) | 0d.3 | `tests/test_doctor_cli.py` |
| AC-40, AC-41, AC-78 | 0d.2 | `tests/test_doctor_runner.py` |
| AC-43 | 0b.1, 0b.3 | `tests/test_active_set.py`, `tests/test_active_set_dangling.py` |
| AC-44 | 0d.3, 0e.2, 0e.3, 0e.4 | `tests/test_doctor_cli.py`, `tests/test_meta_doctor_role.py`, `tests/test_new_role_checklist_doc.py`, Szenario 77 |
| AC-45 | 1.02–1.05, 1.08, 1.20 | `tests/test_active_set_consumers_identity.py`, `tests/test_active_set_single_source.py` |
| AC-46 | 1.10 | `tests/test_pipeline_active_set_filter.py` |
| AC-47 | 1.11, 1.12 | `tests/test_pipeline_active_set_filter.py`, `tests/test_routing_tool_definitions.py` |
| AC-48 | 1.13 | `tests/test_developer_tiers_gate.py` |
| AC-49 | 1.14–1.16, 1.18–1.20 | `tests/test_active_set_dangling.py`, Task-Tests 1.14–1.18 |
| AC-50 | 1.17 | `tests/test_commands_requires_roles.py` |
| AC-51 | 1.38 | `tests/test_reflection_overrides_source.py` |
| AC-52 | 1.09 | `tests/test_pipelines.py` |
| AC-63 | 0b.5 | `tests/test_routing_keyword_overlap_check.py` |
| AC-64 | 0c.1, 0c.4 | `tests/test_no_role_routes_in_templates.py`, `tests/test_template_integrity_checks.py` |
| AC-65, AC-66 | 0c.2, 0c.3 | `tests/test_template_integrity_checks.py` |
| AC-67 | 0b.5, 0d.4, 0d.5 | `tests/test_context_budget_checks.py`, `tests/test_doctor_fixtures.py` |
| AC-68, AC-70 | 1.46, 1.47 | `tests/test_routing_keywords_language_neutral.py`, `tests/test_routing_overlap.py` |
| AC-69 (`full`) | 1.45 | `tests/test_routing_examples_language.py` |
| AC-71 | 1.19 | `tests/test_no_role_routes_in_templates.py` |
| AC-72 | 1.06, 1.07 | `tests/test_template_line_duplication.py`, `tests/test_contract_labels.py` |
| AC-73, AC-74 | 1.42, 1.43 | `tests/test_template_integrity_checks.py` |
| AC-84 | 0b.4 (Start), 1.01–1.05, 1.09, 1.20 (Ende) | `tests/test_active_set_single_source.py`, `tests/test_auto_commit_allowlist_pipeline.py` |
| AC-85 (Rolle), AC-88, AC-95 (Rolle) | 0e.1 | `tests/test_meta_doctor_role.py` |
| AC-86 (Freigabe) | 0f.2 | `tests/test_eval_gate.py` |
| AC-87 | Ausführungsmodell, je PR | PR-Beschreibung (DAG-Nachweis) |
| AC-92 | 0a.1 | `tests/test_tmp_sink_default_on.py` |
| AC-93 | 0a.2 | `tests/test_tmp_sink_path_hardening.py` |
| AC-97 | 0a.4 | `tests/test_tmp_sink_path_parity.py` |
| AC-99 | 0a.3 | `tests/test_tmp_sink_migration_error.py` |

## Offene Nutzerfragen

1. Branch-Strategie: Session-Branch `claude/adoring-keller-c12ws0` vs. Paket-/PR-Branches nach `.claude/rules/branch-guard.md` (`fix/963-…`, `feat/964-…`) — Paket-Branches vom Session-Branch abzweigen oder Session-Branch nur für diesen Plan nutzen?
2. Merge-Reihenfolge 0c vor 0b wegen gemeinsamer Dateien — einverstanden?
3. Freigabe und Budget für den Baseline-Lauf 0f.3 (Kostenschätzung wird vorher angezeigt).
