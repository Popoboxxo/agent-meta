---
pipeline_stages:
  implement: 1
---

# Implementierungsplan — Stale Role Cleanup (B1 → B3 → B2)

> Status: geplant

**Spec:** `docs/specs/2026-09-13-stale-role-cleanup-design.md`

> Trace-Anker: `spec-id: SPEC-STALE-ROLE-CLEANUP-2026-09-13` (Status APPROVED, 2026-09-13).
> System-Design: `docs/specs/2026-09-13-stale-role-cleanup-system-design.md`.
> **Reihenfolge (user-mandated): B1 → B3 → B2.** B2 (IC-06/IC-07/IC-10) darf erst nach dem B1-Sicherheitsfix
> exponiert werden (F-10 / AC-24); die Task-Numerik setzt diese Ordnung erzwungen um.

**Goal:** Drei konfligierende Sub-Symptome desselben User-Erlebnisses („Rolle entfernt, Datei bleibt") beheben: (B1) den fail-open-Löschpfad durch ein provenance-basiertes, fail-closed Prädikat ersetzen, den Index immer schreiben, Skill-Wrapper für alle Provider tracken und `*.sync-backup-*` begrenzt prunen; (B3) den Managed-Block-Shrink per Regressionstest beweisen und die sechs Stale-Pfade sichtbar machen, ohne S1/S2-Opt-outs zu übersteuern; (B2) einen expliziten `preview → confirm → apply`-Pfad in der Admin-UI über den bestehenden `SyncExecutor` bereitstellen.
**Architecture:** Ein policy-freier Shared-Helper (`rule_index.py`, IC-01) besitzt die zwei sicherheitskritischen Semantiken (Provenance-Bootstrap bei fehlendem Index, Empty-Index-Write). `agent_sync.py` stellt einen **reinen** Planner `plan_agent_cleanup` als Single Source of Truth für Vorschau und echtes Cleanup bereit; Löschen ist immer backup-first. Prompt-Index (`context.py`, IC-08) nutzt denselben Helper fail-closed. B3 ist **kein** Shrink-Defekt (die Hypothese ist widerlegt): `_update_managed_html_block` ersetzt den Block bereits wholesale — bewiesen wird nur der Beweis-Gap plus Duplikat-Marker-/Stale-Pfad-Sichtbarkeit. B2 reicht die planende Traversierung als `--cleanup-preview` (seiteneffektfrei) an HTTP-Routen und ein UI-Control weiter.
**Tech Stack:** Python 3.9 (Stdlib only, `from __future__ import annotations`, `typing.Optional`/`List`; keine PEP-604-Union in neuen Modulen), pytest, Bash/DOM-Assertions über Textmuster, JavaScript inline (`docs/ui/admin-ui.html`), Markdown/YAML/JSON.

## Global Constraints

- **Reihenfolge & Abhängigkeit (bindend):** B1-Tasks (1–4) → B3/B1-Kontext (5) → B2-Tasks (6–8) → Gate (9). Kein B2-Task ist ohne die B1-Sicherheitsfixes zulässig; `Depends on:` muss die B2-Kette auf B1 zurückführen.
- **Provider-Agnostik:** Kein `if provider ==` und kein Provider-Namensliteral in neuem/geändertem Code; Unterschiede nur über Config-Keys/Capability-Flags (`provider_has_capability`, `config/ai-providers.yaml`). Die B-I-Wrapper-Fix *entfernt* den einzigen verbleibenden capability-gated Provider-Pfad (`agent_sync.py:896–897`).
- **OQ-1 (freeze):** CLI-Sync räumt weiter automatisch auf (jetzt safe); die Admin-UI verlangt **immer** `preview → confirm`.
- **OQ-2 (freeze):** Backup-Pruner aktiviert, `max_per_source = 3`, `max_age_days = 30`, **beide** Schwellen müssen überschritten sein; der neueste Backup je Quelle wird nie gelöscht.
- **OQ-3 (freeze):** Marker-lose Altdateien werden als `foreign` klassifiziert, mit `legacy_unmarked: true` in der Vorschau ausgewiesen und **nur manuell** entfernt; keine Adoption marker-loser Dateien.
- **OQ-4 (freeze):** `rules.py:521–522` und `commands.py:207–208` werden **im selben Spec** auf unbedingtes Index-Schreiben ausgerichtet (exakt derselbe Stale-Index-Bug).
- **OQ-5 (freeze):** `rule_index.py` wird **in place** erweitert; keine Modul-Extraktion, kein `managed_index.py`.
- **OQ-6 (freeze):** Duplikat-Marker → `log.warning` + Konsistenz-Finding, weiterhin nur der **erste** Block ersetzt (keine Korruption); Schreiben-vs-Refuse ist sichtbar, aber kein Abort.
- **OQ-7 (freeze):** Stale-Pfad-Sichtbarkeit = **nur Warnungen**; `context_file.auto_generate: false` (S1) und Provider-Deaktivierung (S2) werden **nie** übersteuert; **kein** `--force-context`-Escape-Hatch.
- **OQ-8 (freeze, user override):** In der UI ist ein Backup **vor** `apply` **verpflichtend**; das optionale Default wird zugunsten dieser User-Entscheidung verworfen.
- **OQ-9 (freeze):** Kein Prompt-Provenance-Marker in dieser Änderung; die fail-closed Migration des Prompt-Index (IC-08) ist **unbedingt**.
- **Backup-first / Rollback:** Jeder Cleanup-Delete schreibt zuerst ein `<name>.sync-backup-<YYYYmmdd-HHMMSS>`-Sibling; scheitert das Backup, unterbleibt der Unlink. Re-Sync-Recoverability generierter Rollen bleibt erhalten.
- **Single Source of Truth:** `plan_agent_cleanup` ist rein und speist Vorschau **und** echtes Cleanup; die Vorschau ist seiteneffektfrei (kein Index-Write, kein Unlink, kein Backup, kein Clone/Submodule).
- **Ownership-Disjunktheit:** Keine Datei wird von zwei Tasks angelegt/geändert; `context.py` und `sync_pipeline.py` liegen bewusst in je genau einer Task (siehe Task 4/5).
- **Py3.9 & Stdlib:** neue/geänderte Module `from __future__ import annotations`, keine externen Abhängigkeiten; `scripts/consistency-check.py` muss rc 0 liefern.
- **Bite-sized & TDD:** Test schreiben (fail) → implementieren → Test (pass) → Commit; kein Task ist „done" ohne beobachteten Test.
- **Kein Worktree:** Subagenten arbeiten direkt im Projektverzeichnis (`no-worktree-isolation`); Repo-Containment bleibt unangetastet.

## Interfaces

Neue und geänderte Symbole als `file:Symbol`; Signaturen sind Contracts, keine Implementierung.

| Symbol | Art | Vertrag |
|---|---|---|
| `scripts/lib/rule_index.py:ContentPredicate` | neu | `Callable[[Path, str], bool]` — `(path, file_text) -> True` gdw. Agent-Meta-Provenance. |
| `scripts/lib/rule_index.py:bootstrap_previously_managed` | geändert | `+ content_predicate: Optional[ContentPredicate] = None`; index-first, bei fehlendem Index nur Predicate-/Marker-Treffer, sonst fail-closed. |
| `scripts/lib/rule_index.py:cleanup_stale_managed_files` | geändert | `+ backup: bool = False`; schreibt Sibling vor Unlink, fail-soft je Datei, Rückgabe `list[str]` (geschriebene Backup-Pfade, `[]` bei `dry_run`/`backup=False`). |
| `scripts/lib/rule_index.py:write_managed_index` | unverändert | schreibt auch die leere Menge; no-op nur bei `dry_run`. |
| `scripts/lib/agent_sync.py:_agent_has_provenance` | neu | `(path: Path, text: str) -> bool`; erkennt `generated-from:` (Frontmatter), `<!-- agent-meta-provenance: … -->`, `# generated-from:` (TOML), sekundär `based-on:`. Rein. |
| `scripts/lib/agent_sync.py:_agent_provenance_is_external_skill` | neu | `(path, text) -> bool`; **nur** primäre Marker mit Origin-Prefix `0-external/`; `based-on:` qualifiziert nie. Rein. |
| `scripts/lib/agent_sync.py:_collect_active_skill_wrapper_filenames` | neu | `(agent_meta_root, config) -> set[str]`; `_skill_is_active` + Registry-Rollen (role default = skill name), provider-unabhängig. |
| `scripts/lib/agent_sync.py:_collect_all_registry_wrapper_filenames` | neu | `(agent_meta_root) -> set[str]`; gleiche Traversierung ohne Active-Filter; nur für `reason`-Präzedenz. |
| `scripts/lib/agent_sync.py:StaleAgentEntry` | neu | `@dataclass(frozen=True)(provider, path, reason, tracked, adopted)`. |
| `scripts/lib/agent_sync.py:plan_agent_cleanup` | neu | `(target_dir, expected_filenames, provider, wrapper_filenames, pc, project_root) -> list[StaleAgentEntry]`; PURE. |
| `scripts/lib/agent_sync.py:_cleanup_stale_agents` | geändert | `+ provider, wrapper_filenames`; nutzt Planner + `cleanup_stale_managed_files(backup=True)` + `write_managed_index` (unbedingt). |
| `scripts/lib/agent_sync.py:sync_agents_for_provider` | geändert | `:896–897` durch unbedingte IC-03-Union ersetzen. |
| `scripts/lib/generated_file_drift.py:prune_sync_backups` | neu | `(target_dir, project_root, log, dry_run, max_age_days, max_per_source) -> list[str]`. |
| `scripts/lib/sync_pipeline.py` | geändert | Prune nach der Drift-Stage je Managed-Dir; S1/S2-Sichtbarkeitswarnung. |
| `scripts/lib/rules.py` / `commands.py` | geändert | Index unbedingt schreiben (OQ-4). |
| `scripts/lib/context.py:_has_duplicate_managed_block` | neu | `(text: str) -> bool`; zählt Marker-Paare nahe `_MANAGED_BLOCK_RE`. |
| `scripts/lib/context.py:_update_managed_html_block` | geändert | Shrink-Replacement (`count=1`) unverändert; bei Duplikat `log.warning` + Konsistenz-Finding. |
| `scripts/lib/context.py:sync_prompts_for_provider` | geändert | IC-01 fail-closed Bootstrap (adopt nothing bei fehlendem Index) + `write_managed_index` unbedingt. |
| `scripts/lib/skills.py:ensure_skill_repo` / `deinit_skill_repo` | geändert | Callsite auf `not dry_run` gaten (F-04). |
| `scripts/sync.py:_handle_cleanup_preview` + `--cleanup-preview` | neu | planning-only; genau ein JSON-Objekt auf stdout; rc 0. |
| `scripts/admin-server.py:SyncExecutor.cleanup_preview` | neu | `() -> dict`; subprocess `--cleanup-preview`, JSON geparst. |
| `scripts/admin-server.py:_route_post_roles_cleanup_preview` / `_apply` | neu | POST; `_POST_EXACT_ROUTES`-Einträge. |
| `docs/ui/admin-ui.html` | geändert | `Preview cleanup`-Button, Ergebnisse-Panel, `Remove N`-Danger-Button, Zustände/409-Handling. |

## File Structure

### Neue Dateien

- Create: `tests/test_rule_index.py` — IC-01-Helper-Unit-Tests (Bootstrap, Empty-Write, Backup-on-Delete, fail-soft, Return-Typ).
- Create: `tests/test_managed_index_alignment.py` — OQ-4-Index-Write + Pipeline-Pruner-Wiring + S1/S2-Sichtbarkeit.
- Create: `tests/test_context_managed_block_shrink.py` — AC-16/AC-17-Shrink-/Duplikat-Regression.
- Create: `tests/test_context_prompt_index.py` — AC-23-Prompt-Index-fail-closed.
- Create: `tests/test_cleanup_preview_cli.py` — AC-10 seiteneffektfreie Vorschau, JSON-Schema, Fingerprint.
- Create: `tests/test_admin_cleanup_endpoint.py` — AC-11..AC-14, AC-15-Spiegel, AC-25 (Importlib-Muster aus `tests/test_admin_server.py:38–48`).

### Geänderte Dateien

- Modify: `scripts/lib/rule_index.py` — IC-01 (`ContentPredicate`, Backup, Return-Typ).
- Modify: `scripts/lib/agent_sync.py` — IC-02/IC-03/IC-04.
- Modify: `scripts/lib/generated_file_drift.py` — IC-05 Pruner.
- Modify: `scripts/lib/sync_pipeline.py` — Prune-Wiring + S1/S2-Warnung.
- Modify: `scripts/lib/rules.py`, `scripts/lib/commands.py` — OQ-4 Always-Write.
- Modify: `scripts/lib/context.py` — IC-08 + IC-09 (Duplikat, S3).
- Modify: `scripts/lib/skills.py` — F-04 `dry_run`-Gate.
- Modify: `scripts/sync.py` — IC-06 `--cleanup-preview`.
- Modify: `scripts/admin-server.py` — IC-07 Routen + `cleanup_preview`.
- Modify: `docs/ui/admin-ui.html` — IC-10 Control.
- Modify: `tests/test_agent_sync_helpers.py` — AC-01..AC-07/AC-15/AC-21/AC-22.
- Modify: `tests/test_generated_file_drift.py` — AC-09 Pruner.
- Modify: `tests/test_provider_agnostic_dispatch.py` — AC-20 Ratchet (`_TOUCHED_MODULES` erweitern).
- Modify: `docs/api/cli-reference.md`, `docs/api/admin-ui-reference.md` — Flag-/Endpoint-Doku.

### Step-Agent-Map (plan-driven `implement`)

| Step | Task | Bereich | Agent | Depends on |
|------|------|---------|-------|------------|
| 1 | Shared Managed-Index-Helper (IC-01) | B1 | senior-developer | — |
| 2 | Provenance-Cleanup + Wrapper-Tracking (IC-02/03/04) | B1 | senior-developer | 1 |
| 3 | Backup-Pruner (IC-05) | B1 | developer | 1 |
| 4 | Pipeline-Wiring, Index-Alignment, S1/S2-Sichtbarkeit | B1/B3 | developer | 1, 3 |
| 5 | context.py: Prompt-Index + Shrink-Beweis (IC-08/IC-09) | B1/B3 | developer | 1 |
| 6 | CLI `--cleanup-preview` + dry_run-Gate (IC-06/F-04) | B2 | developer | 1, 2, 3, 4 |
| 7 | Admin-Routen + UI-Control (IC-07/IC-10) | B2 | developer | 6 |
| 8 | Doku + Provider-Agnostik-Ratchet | B2 | developer | 7 |
| 9 | Vollständiges Verifikations-Gate | — | developer | 1–8 |

---

### Task 1: Shared Managed-Index-Helper (IC-01)

**Files:**
- Modify: `scripts/lib/rule_index.py`
- Test: `tests/test_rule_index.py`

**Interfaces:** (Produces / Consumes)
- Produces: `ContentPredicate`; `bootstrap_previously_managed(target_dir, index_path, glob_pattern, content_marker=None, content_predicate=None)`; `cleanup_stale_managed_files(target_dir, project_root, previously_managed, now_managed, log, dry_run, reason, backup=False) -> list[str]`; `write_managed_index` (Semantik unverändert).
- Consumes: `pathlib.Path`, `fnmatch`, `datetime`, `typing.Optional`/`Callable`; `from .io import safe_path`; `from .log import SyncLog`.

**Agent:** senior-developer
**Depends on:** —

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_rule_index.py::test_bootstrap_content_predicate_adopts_only_matching` (IC-02/IC-04), `::test_bootstrap_missing_index_never_adopts_without_predicate` (AC-03 fail-closed), `::test_bootstrap_existing_empty_index_wins_over_predicate` (AC-04), `::test_cleanup_writes_backup_before_unlink` (AC-08: Sibling mit Pre-Delete-Inhalt), `::test_cleanup_dry_run_writes_no_backup_but_reports_path` (AC-08/IC-01), `::test_cleanup_backup_failure_prevents_unlink` (IC-01 fail-soft), `::test_cleanup_returns_backup_paths` (F-11 Rückgabe-Vertrag), `::test_write_managed_index_writes_empty_file`.
- [ ] Step 2: Implementieren — `bootstrap_previously_managed` um `content_predicate` erweitern: bei vorhandenem, lesbarem Index dessen Inhalt zurückgeben (auch leer); bei fehlendem Index nur Glob-Treffer, die Predicate bzw. `content_marker` erfüllen; `OSError`/`UnicodeDecodeError` je Datei = nicht adoptieren. `cleanup_stale_managed_files` um `backup: bool = False` erweitern: vor dem Unlink `<name>.sync-backup-<ts>` schreiben (ein Timestamp je Invocation, Format wie `generated_file_drift.py:221–269`), bei Backup-Fehler `log.warning` und Unlink unterlassen; Backuppfade sammeln und `return`. Die drei bestehenden Caller (`mcp.py:378`, `external_tools.py:336`, `pipelines.py:1109`) ignorieren den Rückgabewert (F-11) — keine Return-Assertion dort ergänzen.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_rule_index.py -q` → rc 0.
- [ ] Step 4: Commit — `feat: add content-predicate bootstrap and backup to managed-index helper`.

**Acceptance:** AC-04, AC-05, AC-08, AC-23 (Helper-Seite), AC-24 (Helper-Seite).

---

### Task 2: Provenance-basiertes Cleanup + Wrapper-Tracking (IC-02/IC-03/IC-04)

**Files:**
- Modify: `scripts/lib/agent_sync.py`
- Test: `tests/test_agent_sync_helpers.py`

**Interfaces:** (Produces / Consumes)
- Produces: `_agent_has_provenance`, `_agent_provenance_is_external_skill`, `_collect_active_skill_wrapper_filenames`, `_collect_all_registry_wrapper_filenames`, `StaleAgentEntry`, `plan_agent_cleanup`; `_cleanup_stale_agents(target_dir, expected_filenames, provider, wrapper_filenames, pc, project_root, dry_run, log)`; unbedingte Wrapper-Union in `sync_agents_for_provider`.
- Consumes: IC-01-Helper (Task 1); `skills._skill_is_active`, `skills.load_external_skills_config`; `provider_has_capability` (nur für andere Gates erhalten, nicht für Wrapper); `_should_skip_role`.

**Agent:** senior-developer
**Depends on:** 1

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_agent_sync_helpers.py`: `::test_stale_managed_file_deleted_and_index_rewritten` erweitern (AC-01, DELETE-Log-Reihenfolge exakt `["agents/stale-old.md"]`), `::test_index_rewritten_when_expected_equals_previous` (AC-02), `::test_no_managed_index_prunes_only_provenance_files` (AC-03, ersetzt die fail-open-Erwartung), `::test_empty_expected_filenames_writes_empty_index` (AC-04, ersetzt `…never_rewrites…`), `::test_corrupt_index_warns_and_deletes_only_provenance` (AC-05), `::test_wrapper_tracked_for_non_capability_provider` (AC-06, parametrisiert über mindestens einen Nicht-Claude-Provider; erwartet `provider`/`reason=="skill deactivated"`), `::test_deactivated_skill_wrapper_swept_and_index_cleaned` (AC-07), `::test_reconciled_external_skill_wrapper_adopted` + `::test_markerless_and_based_only_files_are_foreign` + `::test_index_listed_phantom_deleted_with_restorable_backup` (AC-21), `::test_reason_precedence_registry_vs_role` (AC-22), `::test_foreign_file_never_deleted_backed_up_or_rewritten` (AC-15).
- [ ] Step 2: Implementieren — die vier Marker-Prädikate (IC-02) rein implementieren (Primärmarker vor `based-on:`). `_collect_active_skill_wrapper_filenames` / `_collect_all_registry_wrapper_filenames` aus derselben Quelle wie `skills.py:389–390`/`:421–422`. `plan_agent_cleanup` exakt nach den Bindungen IC-04: `previously_managed` index-first-unless-absent/unreadable; `reconcilable(f)` nur bei lesbarem Index + `is_candidate` + `f.name ∉ E` + `f.name ∉ previously_managed` + `_agent_provenance_is_external_skill`; `removable`/`foreign` wie spezifiziert; Reason-Präzedenz 1→3. `_cleanup_stale_agents` durch Planner + `cleanup_stale_managed_files(backup=True)` + unbedingtes `write_managed_index` ersetzen; DELETE-Log-Order und `"role removed from config"`-String byte-gleich zu `:804–808` halten. In `sync_agents_for_provider` `:896–897` durch `expected_filenames |= _collect_active_skill_wrapper_filenames(agent_meta_root, config)` ersetzen (kein Capability-Gate).
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_agent_sync_helpers.py -q`.
- [ ] Step 4: Commit — `feat: provenance-based fail-closed agent cleanup with skill-wrapper tracking`.

**Acceptance:** AC-01, AC-02, AC-03, AC-05, AC-06, AC-07, AC-15, AC-21, AC-22, AC-24 (agent_sync-Klausel).

---

### Task 3: Bounded `*.sync-backup-*`-Pruner (IC-05)

**Files:**
- Modify: `scripts/lib/generated_file_drift.py`
- Test: `tests/test_generated_file_drift.py`

**Interfaces:** (Produces / Consumes)
- Produces: `prune_sync_backups(target_dir, project_root, log, dry_run, max_age_days, max_per_source) -> list[str]`.
- Consumes: `_SYNC_BACKUP_PATTERN` / `_is_sync_backup_name` (`:109`, `:112–114`), Timestamp-/Namenskonvention `:240–255`.

**Agent:** developer
**Depends on:** 1

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_generated_file_drift.py`: `::test_prune_noop_in_dry_run` (AC-09), `::test_prune_never_deletes_newest_backup` (AC-09), `::test_prune_requires_both_thresholds` (AC-09: nur `age > max_age_days` **und** `> max_per_source` neuere), `::test_prune_ignores_non_backup_names` (AC-09), `::test_prune_skips_unparsable_timestamp` (AC-09 fail-safe), `::test_prune_default_policy_three_and_thirty` (OQ-2).
- [ ] Step 2: Implementieren — `prune_sync_backups` neben `_SYNC_BACKUP_PATTERN` platzieren; Kandidaten nur über `_is_sync_backup_name`; Quelle durch Abstreifen des Suffixes `.sync-backup-<YYYYmmdd-HHMMSS>`; Löschentscheidung nur wenn beide Schwellen überschritten; nie der jüngste Backup je Quelle; unparsbare Timestamps nie löschen; `OSError` je Datei via `log.debug`/`warning` und weiter; Rückgabe der geprunten projekt-relativen Posix-Pfade. Defaultbereich im Docstring dokumentieren (OQ-2), Policy-Werte als Parameter.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_generated_file_drift.py -q`.
- [ ] Step 4: Commit — `feat: add bounded sync-backup pruner`.

**Acceptance:** AC-09, AC-19 (Backup-Hälfte), OQ-2.

---

### Task 4: Pipeline-Prune-Wiring, Index-Alignment (OQ-4), S1/S2-Sichtbarkeit

**Files:**
- Modify: `scripts/lib/sync_pipeline.py`
- Modify: `scripts/lib/rules.py`
- Modify: `scripts/lib/commands.py`
- Test: `tests/test_managed_index_alignment.py`

**Interfaces:** (Produces / Consumes)
- Produces: `prune_sync_backups`-Aufruf nach der Drift-Stage je Managed-Dir; unbedingtes `write_managed_index` in `rules.py`/`commands.py`; Konsistenz-Warnungen bei S1 (`auto_generate: false`) und S2 (Provider deaktiviert).
- Consumes: `prune_sync_backups` (Task 3), `write_managed_index` (Task 1), Config-Keys `context_file`/`auto_generate`, Aktivierungsstatus.

**Agent:** developer
**Depends on:** 1, 3

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_managed_index_alignment.py::test_rules_and_commands_write_empty_index` (OQ-4: leerer Managed-Set → 0-Byte-Index nach Nicht-Dry-Run), `::test_pipeline_invokes_prune_after_drift` (AC-09, Spy auf `prune_sync_backups`), `::test_auto_generate_false_emits_warning_without_write` (AC-18/S1), `::test_deactivated_provider_emits_warning_without_write` (AC-18/S2).
- [ ] Step 2: Implementieren — `rules.py:521–522` und `commands.py:207–208` auf unbedingtes Schreiben (nur `dry_run` no-op) umstellen, via `write_managed_index`. `sync_pipeline.py`: nach der Drift-Stage je Managed-Dir `prune_sync_backups(target_dir, project_root, log, dry_run, max_age_days=30, max_per_source=3)` (OQ-2) aufrufen; S1/S2 nur als `log.warning`/Konsistenz-Finding sichtbar machen, **keinen** Schreibpfad erzwingen und keine Opt-outs übersteuern (OQ-7). S4 (`dry_run`) bleibt reines Statusfeedback.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_managed_index_alignment.py tests/test_mcp_stale_cleanup.py tests/test_rules_skill_channel.py -q` und `rtk python3 scripts/sync.py --validate`.
- [ ] Step 4: Commit — `fix: always write managed indexes and surface skipped context stages`.

**Acceptance:** AC-09, AC-18 (S1/S2), OQ-4.

---

### Task 5: `context.py` — Prompt-Index fail-closed (IC-08) + Shrink-Beweis/Duplikat/S3 (IC-09)

**Files:**
- Modify: `scripts/lib/context.py`
- Test: `tests/test_context_managed_block_shrink.py`, `tests/test_context_prompt_index.py`

**Interfaces:** (Produces / Consumes)
- Produces: `sync_prompts_for_provider` IC-01-basiert (fail-closed Bootstrap „adopt nothing", unbedingter Index-Write); `_has_duplicate_managed_block`; `_update_managed_html_block` unverändert im Shrink + Duplikat-Warnung; S3-Warnung bei `--only-variables`.
- Consumes: IC-01-Helper (Task 1); bestehende `_MANAGED_BLOCK_RE` (`:30–33`), Regex `:372–376`, Replacement `:436`, `_regenerate_static_context` (`:186–276`), `only_variables` (`:1578–1607`).

**Agent:** developer
**Depends on:** 1

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_context_managed_block_shrink.py::test_managed_block_shrinks_when_role_hint_removed` (AC-16: `A` verschwindet, `B` erscheint, Fremdinhalt byte-identisch), `::test_duplicate_marker_keeps_second_block_and_warns` (AC-17: nur erster Block ersetzt, Datei parsebar, `log.warning`/Finding), `::test_only_variables_warns_managed_block_not_refreshed` (AC-18/S3). `tests/test_context_prompt_index.py::test_absent_prompt_index_adopts_nothing` (AC-23: `orphan.md` überlebt, Index wird geschrieben), `::test_empty_expected_writes_zero_byte_index` (AC-23), `::test_present_prompt_index_deletes_stale_and_rewrites` (AC-23), `::test_prompt_fail_open_clause_gone` (AC-24 context-Klausel).
- [ ] Step 2: Implementieren — `sync_prompts_for_provider` (`:1723–1740`) auf IC-01 umstellen: `bootstrap_previously_managed` mit fail-closed Predicate (kein Adoption bei fehlendem Index), `cleanup_stale_managed_files`, `write_managed_index` unbedingt; keine Reconciliation (Prompt-Dateien tragen keinen Marker, OQ-9). `_has_duplicate_managed_block` nahe `_MANAGED_BLOCK_RE`; `_update_managed_html_block` bei Duplikat `log.warning` + Konsistenz-Finding, Replacement bei `count=1` unverändert lassen. `--only-variables`-Pfad um sichtbare Warnung ergänzen, ohne den Managed Block zu re-rendern. Das `:436`-Replacement und `_regenerate_static_context` dürfen **nicht** verändert werden (Review-Reject, siehe Spec „Corrected hypothesis").
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_context_managed_block_shrink.py tests/test_context_prompt_index.py tests/test_context_agents_md_idempotency.py -q`.
- [ ] Step 4: Commit — `feat: prove managed-block shrink and migrate prompt index fail-closed`.

**Acceptance:** AC-16, AC-17, AC-18 (S3), AC-23, AC-24 (context-Klausel).

---

### Task 6: CLI `--cleanup-preview` (IC-06) + `dry_run`-Gate (F-04)

**Files:**
- Modify: `scripts/sync.py`
- Modify: `scripts/lib/skills.py`
- Test: `tests/test_cleanup_preview_cli.py`

**Interfaces:** (Produces / Consumes)
- Produces: `--cleanup-preview` (registriert nahe `:117–118`, `_MODE_HANDLERS`-Eintrag nahe `:324–349`); `_handle_cleanup_preview` (genau ein JSON-Objekt auf stdout, rc 0/1); `CleanupPreviewLog`-Collector; `ensure_skill_repo`/`deinit_skill_repo`-Aufruf gated auf `not dry_run`.
- Consumes: IC-01..IC-05 (Tasks 1–4), `plan_agent_cleanup` (Task 2), `_resolve_sync_targets`/`_should_skip_role`, `SyncLog`.

**Agent:** developer
**Depends on:** 1, 2, 3, 4

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_cleanup_preview_cli.py::test_preview_emits_single_json_object` (AC-10: `version`, `providers[].stale/foreign/backups_to_prune`, `fingerprint`), `::test_preview_has_no_filesystem_or_network_mutation` (AC-10/F-04: Fixture mit fehlendem Skill-Repo → kein `git clone`/`submodule add`, kein Index-Write/Unlink/Backup), `::test_preview_exit_code_zero_for_nonempty_stale`, `::test_preview_fingerprint_stable_over_canonical_stale_set` (IC-06), `::test_foreign_entries_carry_legacy_unmarked` (OQ-3/AC-10).
- [ ] Step 2: Implementieren — Flag + Handler im `_MODE_HANDLERS`-Muster; planning-only Traversierung mit `dry_run=True` und `CleanupPreviewLog`, nur `plan_agent_cleanup` als Produzent; keine Writer-Stage. Genau ein JSON-Objekt nach IC-06-Schema ausgeben (`stale[].{path,reason,tracked,adopted}`, `foreign[].legacy_unmarked`, `backups_to_prune`, `fingerprint` als stabiler sha256 über den kanonisierten Stale-Set), rc 0 auch bei nicht-leerem `stale`, rc 1 nur bei internem Fehler. In `skills.py` die bedingungslosen `ensure_skill_repo`/`deinit_skill_repo`-Aufrufe (`:410–412`) auf `not dry_run` gaten. `--validate` bleibt der separate Pfad (kein Preview).
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_cleanup_preview_cli.py -q` und `rtk python3 scripts/sync.py --validate`.
- [ ] Step 4: Commit — `feat: add side-effect-free cleanup preview CLI`.

**Acceptance:** AC-10, AC-15 (CLI-Flow), AC-24 (Preview erreicht keinen fail-open-Zweig).

---

### Task 7: Admin-HTTP-Routen (IC-07) + UI-Control (IC-10)

**Files:**
- Modify: `scripts/admin-server.py`
- Modify: `docs/ui/admin-ui.html`
- Test: `tests/test_admin_cleanup_endpoint.py`

**Interfaces:** (Produces / Consumes)
- Produces: `SyncExecutor.cleanup_preview() -> dict`; `_route_post_roles_cleanup_preview` (`/api/roles/cleanup/preview`), `_route_post_roles_cleanup_apply` (`/api/roles/cleanup/apply`) in `_POST_EXACT_ROUTES`; UI-`Preview cleanup`-Button + Panel + `Remove N`-Danger-Button.
- Consumes: `SyncExecutor.run()` (`:1139–1141`, unverändert), `_read_body` (`:3044–3063`), `_send_json` (`:3014–3025`), Task 6 (`--cleanup-preview`), Backup-/Fingerprint-Semantik (Tasks 1–3).

**Agent:** developer
**Depends on:** 6

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_admin_cleanup_endpoint.py` (Importlib-Muster `tests/test_admin_server.py:38–48`): `::test_preview_route_returns_payload` (AC-11), `::test_apply_requires_confirm_true` (AC-12: 400, `run()` nicht gerufen), `::test_apply_fingerprint_mismatch_is_409` (AC-13: `run()` nicht gerufen), `::test_apply_success_returns_recomputed_stale_paths` (AC-14: `deleted == [p1.path, p2.path]`; `returncode != 0`/Timeout → 500 ohne `deleted`), `::test_foreign_never_deleted_in_preview_and_apply` (AC-15-Spiegel), `::test_ui_cleanup_control_wiring` (AC-25: Button im `btn-row`, `Remove N` nur bei `N>0`, confirm-`POST` mit `{confirm:true, fingerprint}`, 409-Re-Render ohne Button-Wedge, 400/500 markieren nichts als entfernt).
- [ ] Step 2: Implementieren — `SyncExecutor.cleanup_preview()` ruft `_run(["--cleanup-preview"])` und parst das eine JSON-Objekt; bei Subprozess-/JSON-Fehler `{"success": False, "error": "sync_preview_failed", "output": …}`. Beide Routen in `_POST_EXACT_ROUTES` (`:3382–3406`). Apply-Reihenfolge exakt: `confirm is not True` → 400 zuerst; server-seitige `cleanup_preview()`-Wiederholung und Fingerprint-Vergleich → 409; sonst `SyncExecutor.run()`; `deleted := [e.path for e in recomputed.stale]` nur bei `returncode == 0`. **OQ-8 (bindend):** `run()` erfolgt erst nach dem backup-first-Cleanup aus Task 1/2 — Backup vor Apply ist verpflichtend, kein Opt-out. `project.yaml → roles` wird **nie** mutiert. In `admin-ui.html` im Sync-View (`btn-row` `:5113–5117`) Button + Panel + Danger-Button gemäß IC-10-Zustandsmaschine (`idle → previewing → preview-shown → applying → done/error`) und 409-Re-Render; `api.post`, `toast`, `setSyncButtonsDisabled`, bestehendes Confirm-Modal nutzen.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_admin_cleanup_endpoint.py tests/test_admin_server.py -q`.
- [ ] Step 4: Commit — `feat: add admin-UI preview/confirm/apply role cleanup`.

**Acceptance:** AC-11, AC-12, AC-13, AC-14, AC-25, AC-15 (UI-Spiegel), OQ-1, OQ-8.

---

### Task 8: Doku + Provider-Agnostik-Ratchet (AC-20)

**Files:**
- Modify: `docs/api/cli-reference.md`
- Modify: `docs/api/admin-ui-reference.md`
- Modify: `tests/test_provider_agnostic_dispatch.py`

**Interfaces:** (Produces / Consumes)
- Produces: CLI-Referenz für `--cleanup-preview` (JSON-Schema, rc-Semantik, seiteneffektfrei); Admin-UI-Referenz für die zwei POST-Routen und den preview→confirm→apply-Flow; erweiterter statischer Provider-Agnostik-Scan über die geänderten Module.
- Consumes: `docs/api/cli-reference.md:11`-Tabellenformat, `docs/api/admin-ui-reference.md`, `tests/test_provider_agnostic_dispatch.py::_TOUCHED_MODULES` (`:27–43`).

**Agent:** developer
**Depends on:** 7

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_provider_agnostic_dispatch.py`: `_TOUCHED_MODULES` um `rule_index`, `generated_file_drift`, `skills` erweitern; `::test_cleanup_preview_documented` (CLI-Referenz enthält `--cleanup-preview` und den rc-0-Hinweis), `::test_admin_cleanup_routes_documented` (`docs/api/admin-ui-reference.md` nennt beide Routen und die confirm-/fingerprint-Pflicht).
- [ ] Step 2: Implementieren — CLI-Referenz-Zeile für `--cleanup-preview` im bestehenden Tabellenformat ergänzen; Admin-UI-Referenz um beide POST-Routen, Request-/Response-Schemata, 400/409/500-Semantik und den Backup-vor-Apply-Hinweis (OQ-8) erweitern. Keine Provider-Literale in den Doku-/Teständerungen.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_provider_agnostic_dispatch.py -q` und `rtk python3 scripts/sync.py --validate`.
- [ ] Step 4: Commit — `docs: document cleanup preview and extend provider-agnostic ratchet`.

**Acceptance:** AC-20.

---

### Task 9: Vollständiges Verifikations-Gate

**Files:**
- Test: `tests/test_rule_index.py`, `tests/test_agent_sync_helpers.py`, `tests/test_generated_file_drift.py`, `tests/test_managed_index_alignment.py`, `tests/test_context_managed_block_shrink.py`, `tests/test_context_prompt_index.py`, `tests/test_cleanup_preview_cli.py`, `tests/test_admin_cleanup_endpoint.py`, `tests/test_provider_agnostic_dispatch.py`

**Interfaces:** (Produces / Consumes)
- Produces: dokumentiertes, reproduzierbares Abnahme-Ergebnis; kein Produktionscode, keine neuen Dateien.
- Consumes: alle Artefakte aus Task 1–8.

**Agent:** developer
**Depends on:** 1, 2, 3, 4, 5, 6, 7, 8

**Steps:**
- [ ] Step 1: Neue/geänderte Suiten — `rtk python3 -m pytest tests/test_rule_index.py tests/test_agent_sync_helpers.py tests/test_generated_file_drift.py tests/test_managed_index_alignment.py tests/test_context_managed_block_shrink.py tests/test_context_prompt_index.py tests/test_cleanup_preview_cli.py tests/test_admin_cleanup_endpoint.py tests/test_provider_agnostic_dispatch.py -q` → rc 0.
- [ ] Step 2: Repo-weites Gate — `rtk python3 scripts/sync.py --validate` → rc 0 und `rtk python3 scripts/consistency-check.py` → rc 0.
- [ ] Step 3: Ratchets/Bestandsschutz — `rtk python3 -m pytest tests/test_mcp_stale_cleanup.py tests/test_rules_skill_channel.py tests/test_skills.py tests/test_hook_drift.py tests/test_admin_server.py tests/test_context_agents_md_idempotency.py -q` → rc 0.
- [ ] Step 4: AC-19-Rollback-Durchstich — Sibling eines per Cleanup gelöschten Files zurückbenennen (Byte-Gleichheit) und eine generierte Rolle über `project.yaml → roles` + Re-Sync deterministisch wiederherstellen.
- [ ] Step 5: Commit — `test: verify stale role cleanup end to end`.

**Acceptance:** AC-01 bis AC-25 (Abnahme-Nachweis).

---

## Acceptance-Criteria → Task-Mapping

| AC | Task(s) | | AC | Task(s) |
|----|---------|--|----|---------|
| AC-01 | 1, 2 | | AC-14 | 7 |
| AC-02 | 1, 2 | | AC-15 | 2, 6, 7 |
| AC-03 | 1, 2 | | AC-16 | 5 |
| AC-04 | 1, 2 | | AC-17 | 5 |
| AC-05 | 1, 2 | | AC-18 | 4, 5 |
| AC-06 | 2 | | AC-19 | 1, 3, 6, 9 |
| AC-07 | 2 | | AC-20 | 8 |
| AC-08 | 1, 2, 3 | | AC-21 | 2 |
| AC-09 | 3, 4 | | AC-22 | 2 |
| AC-10 | 6 | | AC-23 | 1, 5 |
| AC-11 | 7 | | AC-24 | 2, 5 |
| AC-12 | 7 | | AC-25 | 7 |
| AC-13 | 7 | | | |

## Rollback / Safety-Net

- **Backup-first:** Jeder Cleanup-Delete schreibt `<name>.sync-backup-<YYYYmmdd-HHMMSS>` mit dem Pre-Delete-Inhalt; scheitert das Backup, unterbleibt der Unlink (IC-01). Rename-back stellt Byte-Gleichheit her (AC-19).
- **Re-Sync-Idempotenz:** Ein versehentlich gelöschtes generiertes Rollenfile wird durch erneutes Aufnehmen der Rolle in `project.yaml → roles` + Sync deterministisch wiederhergestellt.
- **Dry-Run-Vorschau:** `--cleanup-preview` und die Admin-`preview`-Route sind seiteneffektfrei (kein Write/Unlink/Backup/Clone); `apply` verlangt `confirm: true` und einen frischen Fingerprint (409 bei TOCTOU).
- **Pruner fail-safe:** löscht nie den jüngsten Backup je Quelle, nie bei unparsbarem Timestamp, nie in `dry_run` (AC-09).
- **Opt-out-Erhalt:** S1/S2 werden nie übersteuert; kein `--force-context` (OQ-7).
- **Kein Worktree:** direkte Arbeit im Projektverzeichnis, Repo-Containment unangetastet.

## Self-Review

- **AC-Abdeckung:** Alle 25 Acceptance Criteria sind mindestens einer Task zugeordnet; kein AC ohne Task, keine Task ohne AC-Bezug (siehe Mapping).
- **Test je Task:** Jede Task besitzt konkrete, benannte Testfälle und ein `rtk`-Verifikationskommando mit erwartetem rc; kein Task ist ohne beobachteten Test „done".
- **Traceability:** `spec-id: SPEC-STALE-ROLE-CLEANUP-2026-09-13` ↔ `**Spec:**`-Pfad ↔ Task-ID ↔ Testname ist durchgängig; `pipeline_stages.implement` zeigt auf Step 1 (Agent `senior-developer`).
- **Reihenfolge:** B1 (1–4) → B3/B1-Kontext (5) → B2 (6–8) → Gate (9); B2 hängt über Task 6 auf Tasks 1–4 (= B1) zurück und erfüllt F-10/AC-24.
- **Interface-Vollständigkeit:** Jede Task hat nicht-leere `Produces`/`Consumes`; alle neuen Symbole sind mit Datei, Name und Signatur benannt.
- **Datei-Ownership:** Keine Datei liegt in zwei Tasks. `scripts/lib/context.py` (IC-08 aus B1 + IC-09 aus B3) und `scripts/lib/sync_pipeline.py` (IC-05-Wiring + S1/S2) sind bewusst in je **einer** Task gebündelt, um Ownership-Disjunktheit zu wahren; B3-Sichtbarkeit ist dadurch auf Task 4 (S1/S2) und Task 5 (S3/Duplikat) verteilt.
- **Rahmenbedingungen:** Provider-agnostisch (kein `if provider ==`), Stdlib-only, Py3.9-konform, Backup-first, OQ-1..OQ-9 eingefroren, kein Worktree, keine Rollen-Routen.
- **No-Placeholder:** Keine Platzhalter-Marker (`TODO`/`TBD`/Ellipse), keine leeren Interfaces; exakte Pfade, Symbole, Signaturen, Testnamen und Commit-Messages.

## Ausführungs-Handoff

- **Reihenfolge:** Task 1 → Task 9 in aufsteigender Numerik. Innerhalb B1 sind Task 2 (→1), Task 3 (→1) und Task 4 (→1,3) abhängigkeitskorrekt; Task 5 (B3) folgt nach den B1-Tasks; B2-Tasks 6–8 erst nach Task 4, Task 7 nach Task 6.
- **Task-für-Task (SDD):** Jede Task wird von einem frischen Subagenten mit frischem Kontext ausgeführt, zweistufig reviewt (Req-Treue, dann Qualität) und erst dann committet; Ledger-Checkboxen werden nach Task-Abschluss über den Writer aktualisiert.
- **Blocked-Regel:** Kann eine Task ihre Akzeptanz nicht belegen, bleibt sie offen (`- [ ]`), wird an den Orchestrator eskaliert und blockiert Nachfolger; nie stillschweigend überspringen oder umsortieren.
- **Merge-Reihenfolge:** Dieser Plan teilt `scripts/lib/sync_pipeline.py` mit der in-flight Progress-/Ledger-Spec; Shared-File-Edits koordinieren oder diese Änderung zuerst anwenden.
- **Abschluss-Gate:** `rtk python3 scripts/sync.py --validate` (rc 0), `rtk python3 scripts/consistency-check.py` (rc 0) sowie die in Task 9 genannten Suiten (rc 0).
