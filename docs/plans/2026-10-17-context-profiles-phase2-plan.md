# Context Profiles — Phase 2 Implementation Plan (Profil `compact`, Config-Optimizer)

> Status: APPROVED
>
> **Freigabevermerk:** Nutzerfreigabe 2026-10-18 (Auftrag ‚Phase 2 komplett umsetzen‘); Entscheidungen zu den offenen Fragen siehe `## Offene Nutzerfragen` unten.
>
> **Fortschritt (2026-10-20):** 2a.1–2a.8, 2b.1–2b.6, 2c.1–2c.4, 2d.1–2d.7, 2e.1–2e.6 umgesetzt und committet (siehe docs/plans/2026-10-18-context-profiles-phase2-status.md); offen: 2f.1–2f.3 (gated).

**Goal:** Phase 2 der Spec vollständig umsetzen — Profil `compact` (IC-01…IC-12, C1–C7) sowie Config-Optimizer, Applier und Rolle `meta-optimizer` (IC-24…IC-28, IC-35) — ausschließlich als Opt-in ohne Default-Änderung; die nachweisabhängigen Verifikationsschritte (AC-02/AC-25) sind als eigene Gate-Tasks (Paket 2f) ausgewiesen und heute nicht startbar.
**Architecture:** Neue Auflösungsschicht `context_profile.py` über der bestehenden `COMPACT_MODE`-Ableitung (`config.py:1394-1407`); Profil-Konditionale nur in Resolution/Templates, der Active-Set-Filter (IC-17/IC-18) bleibt orthogonal; Per-Provider-Profile über einen Provider-Injection-Seam analog `_INTENT_ROUTING_TOOL_DEFS`/`shared_runtime_gate_vars`; Optimizer als reines Stdlib-Modul mit Sentinel-Render im tmp-sink, Remove-only-Applier und Laufzeit-Leser-Registry als Daten.
**Tech Stack:** Python 3.9/3.11/3.12 (Stdlib + PyYAML), pytest, Bash-Szenarien (`tests/scenarios/run.sh`), Promptfoo (nur Eval, nur nach Freigabe).
**Spec:** `docs/specs/2026-10-11-context-profiles-spec.md`
**Spec-ID:** `spec-id: SPEC-CONTEXT-PROFILES-2026-10-11` (Rev. 3.4, APPROVED; maßgeblich IC-01…IC-12, IC-24…IC-28, IC-34…IC-36)
**Vorgängerplan:** `docs/plans/2026-10-11-context-profiles-plan.md` (Phasen 0/1; gemergt bis #997, Task 1.45)
**Tracking:** #977

## Global Constraints

- Task-Titel = Ziel des Tasks (ein Satz); Detailinhalt steht in der Spec unter den genannten IC-/AC-IDs.
- **Task-Format (maschinenlesbar, B-F-01):** `### Task <n>: <Paket-Koordinate> — <Titel>`; zeilenverankerte Felder `**Agent:** <rolle>`, `**Depends on:** <Maschinen-IDs dieses Plans>` (Bereichs-Depends explizit aufgelistet; keine Fremdzahlen in der Zeile — externe/Phase-1-Abhängigkeiten stehen in `**Voraussetzung:**`, das nicht geparst wird); `Files:`-Block mit je einer Zeile `- Create:`/`- Modify:` mit Pfad in Backticks (jeder Pfad mit eigenem Präfix, da der Parser sonst nur den ersten Pfad einer Sammelzeile sieht). Nachweis über `spec_plan._parse_plan_tasks`/`validate_plan`/`check_plan_file_overlap` im Self-Review.
- Provider-agnostisch: Unterschiede nur über Capability-/Config-Keys, nie `if provider == "Name"`; `tests/test_provider_agnostic_dispatch.py::test_no_provider_literal_usage_in_lib` bleibt grün (AC-36, AC-61).
- Python-3.9-kompatibel (`scripts/lib/consistency/python_compat.py` grün); in `scripts/lib` nur Stdlib + PyYAML; externer Tokenizer nur unter `tests/manual/`.
- **Byte-Stabilität (AC-35 sinngemäß, AC-01/AC-23):** Ohne Opt-in (Key `context-profile` fehlt oder ist `full`) bleibt jeder Render byte-identisch zu den Phase-1-Goldens; `compact` ändert den Render ausschließlich bei aktivem Opt-in (Einzel-Provider bzw. geteilte Datei → `full` + WARN, ADR-5). Golden-/Hash-Rebaselines (`tests/fixtures/slimming-golden/`, `tests/fixtures/ac01-baseline/hashes.json`) nur für die AC-23-Ausnahmeliste (Artefakte der Rolle `meta-optimizer` in 2e.2; IC-05-Konditionale/Version-Bump in 2b.2; Template-Änderungen an `agent-meta-manager`/`orchestrator` aus IC-27 in 2e.4/2e.5) — jeweils mit Begründung im PR **und** im Rebaseline-Log (`tests/test_ac01_render_identity.py`).
- **Gate-Doktrin (IC-36):** 0f.3 wurde am 2026-10-17 vom Nutzer abgelehnt (`SKIPPED-BY-USER`) ⇒ AC-02 ist **nicht belegt**; AC-25 kann ohne Baseline nicht belegt werden. Daher: IC-01…IC-12 werden ohne Verifikationsanspruch als Opt-in ausgeliefert (Spur A); ein Sync mit `context-profile: compact` ohne belegtes AC-25 schreibt INFO `context-profile.unverified` in `sync.log`; kein Default wechselt auf `compact`; Doku/CHANGELOG/Report behaupten keine Verifikation (AC-86). LLM-Evals nur nach ausdrücklicher Nutzerfreigabe mit vorab angezeigter Kostenschätzung.
- **Optimizer-Regeln (ADR-14/ADR-17/ADR-18):** `--accept` ist Pflicht; nur Entfernungen sind anwendbar (Remove-only, L0); Applier rechnet neu und vertraut keinen Hunks; keine Zieldateien; Credential-Keys vollständig ausgeschlossen (IC-35); Vorschau `preview.json` ist Pflicht vor der Anwendung (`--preview`-Bindung); `approval_source: relayed`.
- **tmp-sink/Arbeitsverzeichnisse (IC-34):** alle neuen Ausgaben über `resolve_output_dir`/`resolve_work_dir`; kein `.tmp`-Literal, kein `tempfile`/`/tmp`/`%TEMP%`/`TMPDIR` in `scripts/lib/{meta_optimizer,context_report}*.py` (AC-75, AC-94); Sink deaktiviert ⇒ definierte Abbrüche (AC-98); Sink-Artefakte des Optimizers Modus `0600` (`permissions.restrict_owner_only`, AC-89).
- TDD: jeder Task beginnt mit einem roten Test; der red-before-green-Nachweis (Testlauf vor/nach) steht in der PR-Beschreibung (AC-10 sinngemäß, QG-8).
- Jedes Paket (2a…2f) ist ein eigener PR; die Tasks eines Pakets laufen sequenziell bzw. in den deklarierten `parallel_group`s. PR-Beschreibung nennt Paket, ACs und DAG-Nachweis. `Closes #977` wird nicht verwendet, solange Phase 3 offen ist; Paket-PRs verweisen lediglich auf #977. Branches nach `.claude/rules/branch-guard.md` (`feat/977-…`, `fix/977-…`).
- Version-Bumps berührter Templates und `CHANGELOG.md`-Unreleased-Eintrag je PR nach `.claude/skills/conventions/SKILL.md`; jede renderrelevante Template-Änderung — ausdrücklich 2b.2 (IC-05, Orchestrator-Template) sowie 2e.4/2e.5 (IC-27) — schließt **Minor-Bump und AC-01-Rebaseline** (`tests/fixtures/ac01-baseline/hashes.json`, `tests/fixtures/slimming-golden/orchestrator.md`) samt Rebaseline-Log-Eintrag verpflichtend ein; Rollen-Neuanlage `meta-optimizer` vollständig nach IC-28 / `rules/2-platform/agent-meta-conventions.md` (Abschnitt „Neue-Rolle-Checkliste“).
- Commits: Conventional Commits (`feat`/`fix`/`chore`), Englisch, ≤ 72 Zeichen; Commit durch die per `auto_commit` freigeschaltete Rolle bzw. den Orchestrator; Push/Branches/PR nur `git`.
- Zeilenangaben der Spec sind Orientierung; maßgeblich sind Funktionsnamen.

## Gate-Modell: zwei Spuren (AC-02/AC-25)

**Faktenlage (2026-10-17):** Der Baseline-Lauf 0f.3 (Role-Routing-Eval `full`) wurde vom Nutzer abgelehnt; ein versionierter Skip-Record existiert noch **nicht** (Task 2.00 holt das nach). AC-02 ist damit nicht belegt, AC-25 (Vergleich `compact` gegen Baseline) kann ohne Baseline nicht belegt werden. Die Spec-Ersetzung (Rev. 3, W-10) und IC-36 Folge 2 erlauben dafür: IC-01…IC-12 bleiben Opt-in ohne Verifikationsanspruch; IC-04 wird nicht **als verifiziert** gemergt, sondern bleibt hinter `context-profile: compact` mit „unverifiziert“-Hinweis.

| Spur | Inhalt | Tasks | Bedingung |
|---|---|---|---|
| **A — unverifikations-sicher (jetzt ausliefern)** | Profil-Auflösung/Schema/Konditionale, Render-Verdichtung, Budgets/Anker/Report, Optimizer + Rolle — alles Opt-in bzw. read-only; Defaults unangetastet; `context-profile.unverified`-INFO aktiv | 2.00, 2a.1–2a.8, 2b.1–2b.6, 2c.1–2c.4, 2d.1–2d.7, 2e.1–2e.6 | kein AC-02 nötig; keine Verifikationsbehauptung; kein Default-Wechsel |
| **B — nachweisabhängig (heute nicht startbar)** | Baseline-Nachversuch (AC-02), `compact`-Eval (AC-25), Verifikations-Abschluss (INFO-Absenz, Doku-Claim, AC-26-Claim) | 2f.1 (Gate: Nutzerfreigabe, Kostenschätzung zuerst), 2f.2 (Gate: AC-02 belegt), 2f.3 (Gate: AC-25 belegt) | Start erst nach erfülltem Gate; Tasks ändern Spur-A-Code nur in der Evidenz-Auswertung und in Doku-Claims |

**Regeln für Spur A:**
1. `context-profile: compact` ist jederzeit wieder abwählbar; ohne Key ist die Ausgabe byte-identisch (AC-35 sinngemäß).
2. Tasks, die einen AC „belegen“ wollen (AC-24 gilt deterministisch als belegbar; AC-25/AC-26-Claims nicht), dürfen nur die deterministische Teilmenge behaupten.
3. Kein PR der Spur A nennt `compact` „verifiziert“, „validiert“ oder „empfohlen“; die Kern-Aussage lautet „Opt-in, unverifiziert“ (IC-36 Nr. 3).
4. Task 2b.1 (IC-04-Zeilenformat) wird als Opt-in gemergt, nicht „as verified“; die Entscheidung „ganz zurückhalten bis AC-25“ ist offene Nutzerfrage 1. Bei Wahl der konservativen Variante wird 2b.1 auf einem Branch fertiggestellt und erst nach 2f.2 gemergt; 2b.2–2c werden als gestackte Branches auf dem 2b.1-Branch-Stand gebaut (Rebase-Kette, s. Ausführungsmodell „Konservative Variante“). Der 2f.2-Lauf rendert den **Kandidaten-Build des Branch-Stack-Heads** (Branch-Stand statt Merge — 2f.2 braucht den Branch-Inhalt, nicht den Merge, daher keine Zirkularität); ebenso verweisen die 2c.3-Matrix und der `--check`-Nachweis auf diesen Kandidaten-Build. Kein Task wird dadurch blockiert.

## Ausführungsmodell

- DAG (Spur A): `2.00 → (2a.1 ↔ 2a.2 = 2a-g1) → 2a.3 → (2a.4 ∥ 2a.5 ∥ 2a.6 = 2a-g2) → 2a.7 → 2a.8 (Zusatz, hängt an 2a.2)`; `2a.3 → (2b.1 ∥ 2b.2 = 2b-g1) → 2b.3 → 2b.4 → 2b.5 → 2b.6`; `2b.3…2b.5 → (2c.1 ∥ 2c.2 = 2c-g1) → 2c.3 → 2c.4`; `2d.1 → 2d.2 → 2d.3 → 2d.4 → 2d.5 → 2d.6 → 2d.7` (eigenes Modul; Ausführung unabhängig vom Eval möglich, **Merge erst nach 2c** — geteilte Dateien siehe Merge-Reihenfolge); `(2d.2, 2d.3) → 2e.1 → (2e.2; 2e.3 → 2e.4 → 2e.5) → 2e.6`. Maßgebliche Kantenliste ist das maschinenlesbare `**Depends on:**` je Task; die Paket-Koordinaten (2a.1 … 2f.3) stehen in den Task-Titeln.
- DAG (Spur B): `2f.1 → 2f.2 → 2f.3`; 2f.2 setzt die gemergten Pakete 2a–2c voraus **oder** rendert in der konservativen Variante aus dem Head des 2b.1-Branch-Stacks inkl. 2b.2–2c (der Eval braucht echte `compact`-Artefakte).
- **Eval-Unabhängigkeit:** 2d/2e hängen nur an 0a-III (IC-34, #981) und 0b (IC-17, #984) — beide gemergt — und dürfen unabhängig vom Eval beginnen (Spec §9, Rev.-3-Zusatzregel); sie teilen jedoch Dateien mit 2b/2c (s. u.) und werden deshalb sequenziell gemergt.
- **2b-Voraussetzung:** Task 1.10 (IC-18 Nr. 2, Pipelines-Filter) ist mit #992 gemergt; das Zeilenformat basiert damit auf der gefilterten Pipeline-Menge.
- Parallelität nur innerhalb eines `parallel_group` mit disjunkter Ownership laut `Files:` (maschinenlesbar über die `Files:`-Blöcke; Prüfung `check_plan_file_overlap`, `scripts/lib/orchestration.py:320`, auf dem `FanoutPlan` dieses Plans; `validate_plan` meldet Zyklen/Overlaps); Tasks ohne Gruppe laufen sequenziell.
- **Merge-/Ausführungsreihenfolge (paketübergreifende Überschneidungen dokumentiert, Muster Phase-1-Plan):** *Innerhalb der Pakete:* 2a vor 2b (Variablen/Konditionale); 2d vor 2e (CLI + Proposal-Format existieren); 2e.2 vor 2e.3–2e.5 (Rollen-Registrierung, `role-defaults`-Eintrag); 2e.4 vor 2e.5 (gemeinsame Rebaseline-Dateien `tests/fixtures/slimming-golden/`, `tests/fixtures/ac01-baseline/hashes.json`). *Paketübergreifend* wird sequenziell gemergt: **2a → 2b → 2c → 2d → 2e** (kein Paket startet vor dem Merge seines Vorgängers, sofern eine der folgenden Überschneidungen existiert; Ausnahme ist allein die konservative Variante, in der 2b.1 bis nach 2f.2 offenbleibt und 2b.2–2c als gestackte Kette darauf laufen — Start-Reihenfolge unverändert, Merge von 2b.1 zuletzt). *Bekannte Überschneidungen:* `CHANGELOG.md` (2a.7, 2b.6, 2c.4, 2d.2, 2d.3, 2e.6 — je Paket sequenziell), `docs/api/cli-reference.md` (2a.7, 2c.4, 2d.2, 2d.3, 2e.6), `scripts/lib/cli_commands.py` (2c.2, 2d.2, 2d.3), `tests/test_context_profile_docs.py` (2a.7, 2b.6, 2c.4), `scripts/lib/agent_sync.py` (2a.3/2b.1), `scripts/lib/context.py` (2a.6/2b.3/2b.4/2b.5 — über `Depends on:` bereits sequenziell), `README.md` (2c.4/2e.2/2e.6/2f.3), `config/project-config.schema.json` (2a.2/2e.2), `tests/test_context_budget_checks.py` (2a.4/2c.3), `scripts/lib/context_profile_gate.py` + `tests/test_context_profile_gate.py` (2a.5/2f.3), `tests/test_eval_baseline_schema.py` (2.00/2f.1/2f.2), Rebaseline-Dateien `tests/fixtures/ac01-baseline/hashes.json` + `tests/test_ac01_render_identity.py` (2b.2/2e.2/2e.4/2e.5), `agents/1-generic/orchestrator.md` + `tests/fixtures/slimming-golden/orchestrator.md` (2b.2/2e.2/2e.5), `agents/1-generic/agent-meta-manager.md` + `tests/fixtures/slimming-golden/agent-meta-manager.md` (2e.2/2e.4).
- **Konservative Variante (offene Nutzerfrage 1: 2b.1-Hold-back, Stacked-PR-Kette):** 2b.1 wird auf `feat/977-2b1-…` fertiggestellt, der PR bleibt bis nach belegtem AC-25 offen. 2b.2–2b.6 und 2c.1–2c.4 bauen als **gestackte Branches** auf dem jeweiligen Vorgänger-Head auf (jeder PR nennt seinen Basis-Branch; nach jedem Basis-Merge wird die Kette per Rebase auf den neuen Basis-Head gezogen) und laufen nicht gegen `main`. 2f.2 rendert den **Kandidaten-Build des Stack-Heads** (Branch-Stand statt Merge — keine Zirkularität); die 2c.3-Matrix und der `--check`-Nachweis (Task 18, Step 5) laufen ebenfalls gegen diesen Kandidaten-Build. Merge erst nach bestandenem 2f.2 in Kettenreihenfolge (2b.1 zuerst); scheitert 2f.2, bleibt 2b.1 ungemergt und die Kette wird nicht freigegeben. 2a, 2d und 2e sind nicht Teil der Kette; ihre Ausführung bleibt unabhängig, der Merge folgt weiterhin der Paketreihenfolge (2a → 2b → 2c → 2d → 2e).
- Ausführung nach Skill `plan-ledger`: frischer Subagent je Task, zweistufiges Review (req → quality), Ledger = Checkboxen dieser Datei, **kein** `isolation: "worktree"`.
- Issue-Spalte referenziert das Tracking-Issue #977; die Ableitung eigener Paket-Issues ist offene Nutzerfrage 3.

## File Structure

**Neu (Code/Config):**
- Create: `scripts/lib/context_profile.py` — Auflösung `ResolvedContextProfile`, Shared-File-Regel (IC-02)
- Create: `scripts/lib/context_profile_gate.py` — Eval-Evidenz-Auswertung und `context-profile.unverified`-INFO (IC-36, AC-86)
- Create: `config/runtime-config-readers.yaml` — Laufzeit-Leser-Registry inkl. `credentials` (IC-35)
- Create: `scripts/lib/meta_optimizer.py` — Kandidaten, Fan-out, Beweis, Applier, Vorschau (IC-24, IC-25)
- Create: `templates/context/partials/gate-card.md`, `templates/context/partials/agents-list-compact.md` — Entry-File-`compact` (IC-06)
- Create: `agents/1-generic/meta-optimizer.md` — Rolle (IC-26)
- Create: `standalone/agents/meta-optimizer.md` — Standalone-Export (IC-28 Nr. 5)
- Create: `tests/scenarios/configs/78-meta-optimizer-role.project.yaml`, `tests/scenarios/asserts/78-meta-optimizer-role.sh` — Szenario 78 (chmod +x)
- Create: `tests/routing-llm-eval/roles/runs/2026-10-17-baseline-full.json` — Skip-Record 0f.3 (Task 2.00)
- Create (Tests): `tests/test_context_profile.py`, `tests/test_context_profile_schema.py`, `tests/test_context_profile_shared_file.py`, `tests/test_context_profile_gate.py`, `tests/test_routing_lines_compact.py`, `tests/test_orchestrator_compact_sections.py`, `tests/test_gate_card_compact.py`, `tests/test_compact_rule_channels.py`, `tests/test_compact_matrix.py`, `tests/test_runtime_config_readers.py`, `tests/test_meta_optimizer_runner.py`, `tests/test_meta_optimizer_applier.py`, `tests/test_meta_optimizer_fanout.py`, `tests/test_meta_optimizer_refill.py`, `tests/test_meta_optimizer_inactive_scope.py`, `tests/test_meta_optimizer_marks.py`, `tests/test_meta_optimizer_credentials.py`, `tests/test_meta_optimizer_role.py`, `tests/test_eval_baseline_schema.py`, Fixture-Baum `tests/fixtures/meta-optimizer/`, `tests/fixtures/compact-golden/` (QG-5: `orchestrator.md` in 2b.2, `agents-managed.md` in 2b.3)

**Modify (Code/Config):**
- Modify: `config/project-config.schema.json` — Top-Level `context-profile`, Top-Level `provider-overrides.<P>.context-profile` (IC-01)
- Modify: `templates/configs/project.yaml.example` — auskommentiertes Beispiel (IC-01)
- Modify: `scripts/lib/config.py` — `COMPACT_MODE` aus aufgelöstem Profil, Provider-Prerender `_PROVIDER_CONTEXT_PROFILE_VARS`, Profil-Logzeile, Optimizer-CLI-Verdrahtung (IC-02, IC-24, AC-30)
- Modify: `scripts/lib/agent_sync.py` — Provider-Injection `_PROVIDER_CONTEXT_PROFILE_VARS` (2a.3, AC-30), Provider-Zweig `INTENT_ROUTING_TOOLS` (IC-04)
- Modify: `scripts/lib/variables.py` — Konditional-Whitelist `CONTEXT_PROFILE_COMPACT` (IC-03)
- Modify: `scripts/lib/consistency/placeholders.py` — Built-ins `CONTEXT_PROFILE`, `CONTEXT_PROFILE_COMPACT` (IC-02)
- Modify: `scripts/lib/consistency/context_budget.py` — Promotion `context-profile.marker-in-rule` in `PHASE1_PROMOTED` (Check `check_marker_in_rule` existiert; IC-03/IC-10)
- Modify: `scripts/lib/sync_pipeline.py` — Drain der Gate-INFO in `sync.log` (IC-36, Muster `_ROUTING_INFO`)
- Modify: `scripts/lib/context.py` — Shared-File-Downgrade, Gate-Card/Agents-List-Wiring, `_COMPACT_PLATFORM_RULES`-Erweiterung, CLAUDE.md-Notizen, Managed-Block-Injection (IC-05…IC-08, AC-30)
- Modify: `scripts/lib/agents.py` — `render_routing_lines`, `select_routing_examples`, `compact`-Zweig der Tool-Definition (IC-04)
- Modify: `scripts/lib/delegation_table.py` — Wiederverwendung `_select_examples`/`get_routing_rules` (IC-04, AC-69)
- Modify: `scripts/lib/standalone.py` — `_CONDITIONAL_FALSE_FLAGS`-Eintrag `CONTEXT_PROFILE_COMPACT: "false"` (2b.2; für `meta-optimizer` nur, falls die Rolle Konditionale enthält — 2e.1 prüft)
- Modify: `scripts/lib/doctor_detectors.py` — `detect_variable_unreferenced` zählt registrierte Laufzeit-Leser als Nutzung (IC-35)
- Modify: `templates/context/agents-managed.md`, `templates/context/claude-managed.md` — Profil-Konditionale (IC-06, IC-08)
- Modify: `config/context-anchors.yaml` — `compact-only`-Anker, Gate-Card-Sektionen (IC-12)
- Modify: `scripts/lib/context_report.py`, `scripts/lib/cli_commands.py` — `--profile compact|both` real rendern (IC-11)
- Modify: `scripts/sync.py` — `--optimize-config`, `--apply-config-patch` (IC-24)
- Modify: `scripts/lib/yaml_roundtrip.py` — nur falls Signatur/Export fehlt (Wiederverwendung `analyze_roundtrip`, `_count_comments`) (IC-25)
- Modify: `agents/1-generic/orchestrator.md` — Profil-Konditionale §2a/§9/Tabelle; IC-27-Vorschau-Pflicht (IC-05, IC-27)
- Modify: `agents/1-generic/agent-meta-manager.md` — Optimizer-Schritte, `config-patch-proposal-v1`-Consumer (IC-27)
- Modify: `config/role-defaults.yaml` — Rollen-Eintrag `meta-optimizer`, `input_contracts` (IC-26, IC-27)
- Modify: `agents/1-generic/meta-doctor.md` — nur falls Gate-Wortlaut referenziert wird (keine Pflichtänderung; sonst unberührt)

**Modify (Meta/Doku/Tests):**
- Modify: `tests/test_role_addressability_coverage.py` — `_EXPECTED_TOTAL` 93 → 94, Verteilung, sortierte Liste (IC-28 Nr. 4)
- Modify: `tests/test_ac01_render_identity.py`, `tests/fixtures/ac01-baseline/hashes.json` — AC-23-Ausnahmeliste + Rebaseline (2b.2, 2e.2, 2e.4, 2e.5)
- Modify: `tests/fixtures/slimming-golden/orchestrator.md`, `tests/fixtures/slimming-golden/agent-meta-manager.md` — Rebaseline (2b.2, 2e.4, 2e.5)
- Modify: `tests/test_context_anchors.py`, `tests/test_context_budgets.py`, `tests/test_context_report.py`, `tests/test_context_budget_checks.py`, `tests/test_provider_matrix_sync.py`, `tests/test_routing_tool_definitions.py`, `tests/test_role_routing_eval_catalog.py`, `tests/test_doctor_fixtures.py`, `tests/test_standalone_export_in_sync.py`, `tests/scenarios/registry.md`
- Modify: `docs/api/cli-reference.md` — `--optimize-config`, `--apply-config-patch`, `--profile compact|both`, Unverified-Hinweis
- Modify: `docs/guides/setup/instantiate-project.md`, `README.md`, `docs/guides/context-block-inventory.md`, `rules/2-platform/agent-meta-conventions.md` (Praxis-Hinweise `meta-optimizer`), `CHANGELOG.md`
- Modify: `.meta-config/project.yaml` — nur optional Rollen-Self-Hosting (offene Nutzerfrage 5)

---
pipeline_stages:
  implement: 3
---

## Vorbedingung (Gate-Zustand)

### Task 1: 2.00 — Skip-Record des Baseline-Laufs 0f.3 versionieren
**Agent:** tester · **Issue:** #977 · **PR:** 2.00 · **AC:** AC-02 (Zustand), AC-62 (Baseline-Teil), AC-86 (Skip-Datei) · **Gate:** —
**Depends on:** —
> **Hinweis (2026-10-18):** Ein `SKIPPED-BY-USER`-Record existiert bereits unter `tests/routing-llm-eval/roles/runs/2026-10-17-qg1-deepseek.json`; `tests/test_eval_baseline_schema.py` ist grün. Die Task-Steps bleiben bewusst **ungetickt** (Dateiname weicht vom Plan-Soll `2026-10-17-baseline-full.json` ab) — Vorbedingung faktisch erfüllt, siehe Statusdoku §3.
**Falle:** `SKIPPED-BY-USER` ist die belegte Faktenlage von 2026-10-17 — Record per `eval_gate.write_skip_record` erzeugen, nicht per Hand schreiben; `estimate_cost`-Bezugsgrößen fixieren und im Record festhalten: `cases` = Fallzahl aus `tests/routing-llm-eval/roles/catalog.generated.yaml`, `models` = ≥ 2 namentlich benannte Modellklassen, `runs` = 3 je Metrik, Preisquelle/-datum über `max_age_days` ausgewiesen.
**Files:**
- Create: `tests/routing-llm-eval/roles/runs/2026-10-17-baseline-full.json`
- Create: `tests/test_eval_baseline_schema.py`
- Modify: `tests/routing-llm-eval/README.md`
**Interfaces:** Produces Skip-Record-Schema-Test (entweder gültige Baseline-Datei unter `tests/routing-llm-eval/roles/baseline/` **oder** gültiger `SKIPPED-BY-USER`-Record in `runs/`), Record `{status, date, estimate, reason}`; Consumes `eval_gate.write_skip_record(path: Path, estimate: dict, reason: str, *, today: Optional[str] = None) -> None`, `eval_gate.estimate_cost(cases: int, models: Sequence[str], runs: int, report: dict, *, task_tokens_per_case, max_age_days, today)`, `eval_gate.SKIP_RECORD_DIR`
- [ ] Step 1: Test schreiben (fail): weder Baseline noch Skip-Record vorhanden ⇒ `test_baseline_or_skip_record_exists` rot
- [ ] Step 2: implementieren (Record aus der abgelehnten Freigabe erzeugen — mit den fixierten `estimate_cost`-Bezugsgrößen; README-Absatz „Gate-Status Phase 2“)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_eval_baseline_schema.py tests/test_eval_gate.py -q`
- [ ] Step 4: commit `chore: record skipped user approval for full routing baseline`

## Paket 2a — Profil-Auflösung, Konditionale, Schema (IC-01…IC-03)

### Task 2: 2a.1 — Profil-Auflösung mit Präzedenz und Shared-File-Regel bereitstellen
**Agent:** senior-developer · **Issue:** #977 · **PR:** 2a · **parallel_group:** 2a-g1 · **AC:** AC-29, AC-30 (Auflösungs-Teil) · **Gate:** —
**Depends on:** 1
**Falle:** Präzedenz explizit > `provider-overrides.<P>` > `context-profile` > Default je Einzel-Einstellung; `compact` impliziert `context_file.mode: compact` nur, wenn `mode` nicht explizit gesetzt ist; keine Provider-Literale (rein datengetrieben); `sources` führt `explicit` für explizit gesetzte Einzelwerte.
**Files:**
- Create: `scripts/lib/context_profile.py`
- Create: `tests/test_context_profile.py`
**Interfaces:** Produces `ResolvedContextProfile(provider, profile, context_file_mode, rules_preset, sources)`, `resolve_context_profile(config: dict, provider: str) -> ResolvedContextProfile`, `resolve_shared_file_profile(profiles: Iterable[ResolvedContextProfile]) -> Literal["full", "compact"]` (mindestens ein Teiler `full` ⇒ `full`), `context_profile_provider_variables(config: dict, provider: str) -> dict[str, str]` (`CONTEXT_PROFILE`/`CONTEXT_PROFILE_COMPACT` für die Provider-Injection in 2a.3), `context_profile_variables(config: dict, provider: str, shared_users: Iterable[str]) -> dict[str, str]` (Shared-File-Wrapper: wendet `resolve_shared_file_profile` über `shared_users ∪ {provider}` an und delegiert an `context_profile_provider_variables`; Managed-Block-Injection in 2a.6); Consumes `config.get("context-profile")`, `config.get("provider-overrides")`, `config.get("context_file", {}).get("mode")`, `config.get("rules-preset", "default")`
- [x] Step 1: Test schreiben (fail): Präzedenzmatrix (explizit/override/global/default), `compact`⇒`mode=compact`, explizites `mode: full` gewinnt (`sources["context_file_mode"]=="explicit"`), Shared-File-Regel, unbekannter Wert ⇒ `ValueError`
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_context_profile.py -q`
- [x] Step 4: commit `feat: add context profile resolution with precedence`

### Task 3: 2a.2 — Schema und Validierungsfehler für `context-profile` ergänzen
**Agent:** developer · **Issue:** #977 · **PR:** 2a · **parallel_group:** 2a-g1 · **AC:** AC-01 (kein Render), AC-30 (Schema-Teil) · **Gate:** —
**Depends on:** 1
**Falle:** neuer **Top-Level** `provider-overrides`-Block (je Provider nur `context-profile`, Eintrag `additionalProperties: false`); Default wird nicht persistiert; `--validate` bricht mit `context-profile.invalid` inkl. erlaubter Werte ab; die neue Top-Level-Objektkopie in `tests/test_config_null_blocks.py::_MAPPING_BLOCKS` aufnehmen (`_normalize_null_blocks` ist schema-getrieben, `config.py` bleibt unberührt).
**Files:**
- Modify: `config/project-config.schema.json`
- Modify: `templates/configs/project.yaml.example`
- Modify: `tests/test_config_null_blocks.py`
- Create: `tests/test_context_profile_schema.py`
**Interfaces:** Produces Schema-Keys `context-profile` (enum `full|compact`) und `provider-overrides.<P>.context-profile`, Fehlerpfad `context-profile.invalid`; Consumes IC-01, `scripts/lib/config_audit*.py`
- [x] Step 1: Test schreiben (fail): ungültiger Wert ⇒ Validierungsfehler mit erlaubten Werten; `provider-overrides: null` wird wie ein fehlender Block behandelt; gültiger Eintrag kollidiert nicht mit den bestehenden verschachtelten `provider-overrides`-Blöcken
- [x] Step 2: implementieren (inkl. Beispiel im Schema-Example und `_MAPPING_BLOCKS`-Eintrag)
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_context_profile_schema.py tests/test_config_null_blocks.py -q`
- [x] Step 4: commit `feat: add context-profile schema keys and validation error`

### Task 4: 2a.3 — `CONTEXT_PROFILE`/`COMPACT_MODE` an die Auflösung hängen und loggen
**Agent:** senior-developer · **Issue:** #977 · **PR:** 2a · **AC:** AC-23 (byte-stabil ohne Key), AC-29 (Log `source=explicit`), AC-30 (Provider-Injection) · **Gate:** —
**Depends on:** 2, 3
**Falle:** `COMPACT_MODE` bleibt außerhalb der Whitelist-Erweiterung unverändert (Verhalten #540); Core-Werte sind nur der **Fallback** (`full`/`false`) — die **Provider-Injection** ist der Single-Source-Seam für `provider-overrides.<P>.context-profile`: Prerender `variables["_PROVIDER_CONTEXT_PROFILE_VARS"] = {p: context_profile_provider_variables(config, p)}` über die aktiven Provider in `build_variables` (Muster `_INTENT_ROUTING_TOOL_DEFS`, `config.py:2213-2219`) und Merge in `agent_sync._build_provider_vars` (`agent_sync.py:516-523`); Ableitung liegt nach der Nutzer-Variablen-Schleife (`config.py:1394-1407`) und gewinnt weiterhin gegen stale `variables.COMPACT_MODE`/`variables.CONTEXT_PROFILE`; Logzeile je aktivem Provider `context-profile: <P> profile=… mode=… preset=… (sources: …)`.
**Files:**
- Modify: `scripts/lib/config.py`
- Modify: `scripts/lib/agent_sync.py`
- Modify: `scripts/lib/variables.py`
- Modify: `scripts/lib/consistency/placeholders.py`
- Modify: `tests/test_context_profile.py`
- Modify: `tests/test_build_variables_decomposition.py`
**Interfaces:** Produces Variablen `CONTEXT_PROFILE` (`full|compact`) und `CONTEXT_PROFILE_COMPACT` (`true|false`) als provider-injizierte Werte (`_PROVIDER_CONTEXT_PROFILE_VARS` → `_build_provider_vars`) mit Core-Fallback `full`/`false`; Whitelist-Eintrag `CONTEXT_PROFILE_COMPACT` in `strip_inactive_conditional_blocks` (`variables.py:283ff`); Consumes `resolve_context_profile`, `ResolvedContextProfile.sources`
- [x] Step 1: Test schreiben (fail): ohne Key bleiben alle Phase-1-Renders des Profil-Pfads unverändert (`COMPACT_MODE=false`, `CONTEXT_PROFILE=full`); `context-profile: compact` ⇒ `CONTEXT_PROFILE_COMPACT=true`; explizites `context_file.mode: full` ⇒ `source=explicit`; `provider-overrides.<P>.context-profile: compact` ⇒ nur P rendert `compact`, alle übrigen Provider `full`/`false` (AC-30 „wirkt nur auf P“); Whitelist erkennt das Flag im Rules-Pfad
- [x] Step 2: implementieren (Core-Fallback + Provider-Prerender + Merge in `_build_provider_vars`)
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_context_profile.py tests/test_ac01_render_identity.py tests/test_build_variables_decomposition.py -q`
- [x] Step 4: commit `feat: derive context profile variables from resolved profile`

### Task 5: 2a.4 — `context-profile.marker-in-rule` auf Spec-Severity ERROR promovieren
**Agent:** developer · **Issue:** #977 · **PR:** 2a · **parallel_group:** 2a-g2 · **AC:** AC-32 · **Gate:** —
**Depends on:** 4
**Falle:** kein neuer/doppelter Check — `context_budget.check_marker_in_rule` existiert (Phase 0, WARN; `context_budget.py:456`) und ist in `_sync_stage_context_checks` registriert (`sync_pipeline.py:1648`); `SPEC_SEVERITY` führt den Check bereits als ERROR, die Promotion ist der Ein-Zeilen-Eintrag in `PHASE1_PROMOTED` (`context_budget.py:71`); `context.declared-surface-empty` bleibt bewusst WARN (Begründung `context_budget.py:62-70`); Quell-Rules unter `rules/` dürfen `{{#if CONTEXT_PROFILE_COMPACT}}` nie enthalten (der native Rules-Pfad strippt keine Profil-Konditionale); native Rules bleiben in `full` und `compact` byte-identisch, soweit IC-07 sie nicht betrifft.
**Files:**
- Modify: `scripts/lib/consistency/context_budget.py`
- Modify: `tests/test_context_budget_checks.py`
**Interfaces:** Produces `PHASE1_PROMOTED` inkl. `context-profile.marker-in-rule` (effektive Severity ERROR via `SPEC_SEVERITY`/`EMITTED_SEVERITY`); Consumes bestehendes `check_marker_in_rule(project_root: Path, active_providers: Sequence[str], capabilities: Mapping[str, Mapping], active_set) -> list[Finding]`, Quell-Rules `rules/1-generic/*.md`, `rules/2-platform/*.md`
- [x] Step 1: Test schreiben (fail): bestehender Fixture-Test wird von WARN- auf ERROR-Erwartung umgestellt (Fixture-Rule mit Marker ⇒ ERROR mit Datei/Hinweis); reale Regelmenge ohne Marker ⇒ 0 Befunde
- [x] Step 2: implementieren (Promotion in `PHASE1_PROMOTED`)
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_context_budget_checks.py -q && python3 scripts/consistency-check.py`
- [x] Step 4: commit `feat: promote context-profile marker check to error`

### Task 6: 2a.5 — INFO `context-profile.unverified` bei fehlendem AC-25-Beleg ausgeben
**Agent:** developer · **Issue:** #977 · **PR:** 2a · **parallel_group:** 2a-g2 · **AC:** AC-86 (Profil-Teil) · **Gate:** —
**Depends on:** 4, 1
**Falle:** Evidenz wird ausschließlich aus dem agent-meta-Root gelesen (`tests/routing-llm-eval/roles/{baseline,runs}`) und über `eval_gate.evaluate_gate` bewertet; kein Default wechselt auf `compact`; mit belegtem AC-25 darf die INFO nicht erscheinen (heute erscheint sie).
**Files:**
- Create: `scripts/lib/context_profile_gate.py`
- Modify: `scripts/lib/sync_pipeline.py`
- Create: `tests/test_context_profile_gate.py`
**Interfaces:** Produces `scripts/lib/context_profile_gate.py` mit `context_profile_gate_state(agent_meta_root: Path) -> Literal["evidenced", "not-evidenced"]`, `context_profile_info_lines(resolved: Sequence[ResolvedContextProfile], agent_meta_root: Path) -> list[str]` (INFO `context-profile.unverified` je Provider mit Profil `compact` ohne Beleg); Consumes `eval_gate.evaluate_gate`, `eval_gate.SKIP_RECORD_DIR`, Muster `variables["_ROUTING_INFO"]` → `_sync_stage_context_checks`
- [x] Step 1: Test schreiben (fail): Meta-Repo ohne Baseline (heutiger Zustand) + Fixture mit `compact` ⇒ INFO-Zeile in `sync.log`; Fixture mit gültiger Baseline-/Beleg-Datei ⇒ keine INFO; Default ohne Key ⇒ keine INFO
- [x] Step 2: implementieren (Drain in `sync_pipeline.py`)
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_context_profile_gate.py tests/test_sync_end_checks.py -q`
- [x] Step 4: commit `feat: log unverified context profile gate state`

### Task 7: 2a.6 — Shared-File-Downgrade als WARN melden und Datei `full` rendern
**Agent:** senior-developer · **Issue:** #977 · **PR:** 2a · **parallel_group:** 2a-g2 · **AC:** AC-30 · **Gate:** —
**Depends on:** 4
**Falle:** geteilte AGENTS.md-Gruppe: mindestens ein Teiler `full` ⇒ Datei `full`; WARN `context-profile.shared-file-downgrade` genau einmal je Datei; `shared_users`-Menge stammt aus `context.py::_build_managed_block` (aktive Sharer), keine zweite Liste; Managed-Block-Injection je Provider über `local_vars.update(context_profile_variables(config, provider, shared_users))` (Shared-File-Wrapper um `context_profile_provider_variables` aus 2a.1; Muster `shared_runtime_gate_vars`, `context.py:1953-1964`); `provider-overrides.<P>` gilt nur für P — sobald P in einer geteilten Datei rendert, entscheidet `resolve_shared_file_profile` über alle aktiven Sharer.
**Files:**
- Modify: `scripts/lib/context.py`
- Modify: `scripts/lib/context_profile.py`
- Create: `tests/test_context_profile_shared_file.py`
**Interfaces:** Produces WARN `context-profile.shared-file-downgrade`, Managed-Block-Injection (`CONTEXT_PROFILE`/`CONTEXT_PROFILE_COMPACT` in `local_vars` je Provider via `context_profile_variables(config, provider, shared_users)` — Shared-File-Wrapper um 2a.1s `context_profile_provider_variables`, Shared-File-Regel über alle aktiven Sharer); Consumes `resolve_context_profile`, `resolve_shared_file_profile`, `context_profile_variables`, `provider_channel_caps`
- [x] Step 1: Test schreiben (fail): Fixture mit geteilter Datei, ein Provider `compact`, einer `full` ⇒ Render `full`, genau eine WARN mit Datei und Providern; `provider-overrides.<P>: compact` auf geteilter Datei ⇒ Downgrade auf `full` + WARN (AC-30)
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_context_profile_shared_file.py tests/test_provider_matrix_sync.py -q`
- [x] Step 4: commit `feat: downgrade shared context files to full profile with warning`

### Task 8: 2a.7 — Doku und CHANGELOG für Paket 2a aktualisieren
**Agent:** documenter · **Issue:** #977 · **PR:** 2a · **AC:** AC-29 (Doku), AC-86 (Unverified-Hinweis) · **Gate:** —
**Depends on:** 2, 3, 4, 5, 6, 7
**Falle:** keine Verifikationsbehauptung; `docs/api/cli-reference.md` nennt den Unverified-Zustand ausdrücklich.
**Files:**
- Modify: `docs/api/cli-reference.md`
- Modify: `CHANGELOG.md`
- Create: `tests/test_context_profile_docs.py`
**Interfaces:** Produces Doku-Abschnitt „`context-profile` (Opt-in, unverifiziert)“, CHANGELOG-Unreleased-Eintrag; Consumes 2a.1–2a.6
- [x] Step 1: Test schreiben (fail): Doku-Abschnitt und CHANGELOG-Eintrag fehlen
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_context_profile_docs.py -q && python3 scripts/consistency-check.py`
- [x] Step 4: commit `docs: document opt-in context profile resolution`

### Task 9: 2a.8 — `context-profile` in der Admin-UI exponieren
- [x] Zusatz (2026-10-18): 2a.8 — Admin-UI-Exposition (Nutzerauftrag; #730-Fehlerklasse vermeiden)
**Agent:** developer · **Issue:** #977 · **PR:** 2a · **AC:** AC-86 (Profil) · **Gate:** —
**Depends on:** 3
**Falle:** `context-profile` ist ein Top-Level-Key (`full`/`compact`), kein Objekt wie `context_file`; die UI schreibt ihn als eigene Sektion `["context-profile", contextProfile]` über den vorhandenen PUT-Route — kein neuer Endpoint, keine neue Route; Default `full` bei fehlendem/fremdem Wert (AC-35); Help-Text nennt Opt-in/UNVERIFIED bis AC-25 und AC-35, keine Verifikationsbehauptung; Whitelist `PROJECT_WRITABLE_SECTIONS` (bei `context_file`) ergänzen, sonst HTTP 400 beim Speichern.
**Files:**
- Modify: `scripts/admin-server.py`
- Modify: `docs/ui/admin-ui.html`
- Create: `tests/test_context_profile_admin.py`
- Modify: `tests/test_admin_server.py`
**Interfaces:** Produces Admin-UI-Dropdown „Context profile“ (`full`/`compact`, Default `full`) und writable Sektion `context-profile`; Consumes `context-profile`-Key (2a.2), `provider-overrides.<P>.context-profile`, Muster `context_file`-Panel und Topology-Admin-Test
- [x] Step 1: Test schreiben (fail): statische UI-Asserts (Default-Zeile, Dropdown, Save-Payload, Help-Marker) + `"context-profile" in PROJECT_WRITABLE_SECTIONS` und PUT-Akzeptanz
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_context_profile_admin.py tests/test_admin_ui_git_section.py tests/test_context_topology_admin.py -q`
- [x] Step 4: commit `feat: expose the context profile switch in the admin ui`

## Paket 2b — Routing-Zeilenformat und Render-Verdichtung (IC-04…IC-08, C1–C7)

### Task 10: 2b.1 — Routing-Zeilenformat für `compact` implementieren
**Agent:** senior-developer · **Issue:** #977 · **PR:** 2b · **parallel_group:** 2b-g1 · **AC:** AC-31, AC-69 (Zeilenformat-Teil), AC-27 (Teil) · **Gate:** — (Opt-in-Merge; „as verified“ erst 2f.3 — offene Nutzerfrage 1)
**Depends on:** 4
**Voraussetzung:** Task 1.10 der Phase 1 (IC-18 Nr. 2, Pipelines-Filter) ist mit #992 gemergt — nicht Teil dieses Plans.
**Falle:** aktiv nur bei `CONTEXT_PROFILE_COMPACT=true` **und** `ROUTE_INTENT_CALLABLE=false`; sonst bleiben `json`/`yaml_text_block` byte-identisch; Keyword mit `;` oder `|` ⇒ `SyncError` mit Rolle und Keyword; Beispiele über `delegation_table._select_examples` (Projektsprache), Keywords kanonisch; Zeilen sortiert nach Agentenname; `tool{}` nur bei `ROUTE_INTENT_CALLABLE=true`; **kein** Compact-Zweig für `PIPELINE_MATCH_TABLE` — die §2-Pipeline-Tabelle bleibt in `compact` verbatim (C2-Vorrang; die IC-04-„Single-Source“-Klausel ist als bewusste Abweichung dokumentiert und erst nach 2f-Eval revidierbar, s. Self-Review). **Konservative Variante:** Der PR bleibt bis nach belegtem AC-25 offen; 2b.2–2c bauen als gestackte Kette darauf auf (s. Ausführungsmodell).
**Files:**
- Modify: `scripts/lib/agents.py`
- Modify: `scripts/lib/delegation_table.py`
- Modify: `scripts/lib/agent_sync.py`
- Create: `tests/test_routing_lines_compact.py`
- Modify: `tests/test_routing_tool_definitions.py`
**Interfaces:** Produces `render_routing_lines(rules: list[dict], pipelines: list[dict], name_only: list[dict]) -> str`, `select_routing_examples(rule: dict) -> list[str]`, `compact`-Zweig in `render_routing_tool_definition`/`build_routing_tool_definitions_for_providers`, Zeilenform `<agent>|<flags>|<kw1>;<kw2>|<example>[/<example>]`, Pipeline-Zeile `pipeline:<name>|<signal_keywords>`, Name-only-Zeile `name-only: <agent> (<reason>); …`; Consumes `get_routing_rules`, `_select_examples(examples, language)`
- [x] Step 1: Test schreiben (fail): Zeilen sortiert; Flags `req`/`rec`/`orch-only`/`name-only` nur bei Nicht-Default; leere Flags ⇒ `||`; alle Keywords enthalten; Beispiele sprachgewählt (DE-Fixture/EN-Fixture, identische Keyword-Menge); `;` im Keyword ⇒ `SyncError`; `full`-Pfad byte-identisch
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_routing_lines_compact.py tests/test_routing_tool_definitions.py tests/test_ac01_render_identity.py -q`
- [x] Step 4: commit `feat: render compact routing lines for opt-in profile`

### Task 11: 2b.2 — Orchestrator-§2a/§9/Agent-Tabelle per Profil-Konditional verdichten
**Agent:** prompt-engineer · **Issue:** #977 · **PR:** 2b · **parallel_group:** 2b-g1 · **AC:** AC-24 (C1/C2-Teil), AC-23 (IC-05-Template-Teil) · **Gate:** —
**Depends on:** 4
**Falle:** `{{else}}`-Zweig ist der unveränderte heutige Text (byte-stabil in `full`); Active-Set-Konditionale (IC-18 Nr. 4–8) gelten in beiden Zweigen unabhängig; §1/§2/§4/§5/§6/§7/§11 verbatim; Version-Bump (Minor) + `based-on`-Prüfung der Plattform-Varianten; **Standalone-Export:** `CONTEXT_PROFILE_COMPACT: "false"` in `standalone._CONDITIONAL_FALSE_FLAGS` (`standalone.py:121`) ergänzen, sonst leakt das Konditional in den Standalone-Render; **Rebaseline Pflicht (A-F-1):** der Minor-Bump ändert den gerenderten Orchestrator (Frontmatter-Version im Golden) ⇒ `tests/fixtures/slimming-golden/orchestrator.md` + `tests/fixtures/ac01-baseline/hashes.json` neu einfrieren **und** Rebaseline-Log in `tests/test_ac01_render_identity.py` ergänzen (Begründung im PR); **QG-5:** neues `compact`-Golden.
**Files:**
- Modify: `agents/1-generic/orchestrator.md`
- Modify: `scripts/lib/standalone.py`
- Modify: `tests/fixtures/slimming-golden/orchestrator.md`
- Modify: `tests/fixtures/ac01-baseline/hashes.json`
- Modify: `tests/test_ac01_render_identity.py`
- Create: `tests/test_orchestrator_compact_sections.py`
- Create: `tests/fixtures/compact-golden/orchestrator.md`
**Interfaces:** Produces Profil-Konditionale in §2a (Pointer auf `{{PIPELINE_DETAILS_DIR}}/<pipeline>.md`), §9 (Schwellen verbatim, Prosa → Pointer `_wf-orchestrator-reference.md`), Agent-Tabelle (entfällt bei `roster_in_harness: true`, sonst Namensliste); Standalone-Flag `CONTEXT_PROFILE_COMPACT`; `compact`-Golden (QG-5); Consumes `CONTEXT_PROFILE_COMPACT`
- [x] Step 1: Test schreiben (fail): `full`-Render byte-identisch (Golden), `compact`-Render ohne Tabellen-Overhead, Anker (Singleton/Contract) vorhanden, `compact`-Golden fehlt
- [x] Step 2: implementieren (Version-Bump; Standalone-Flag; Rebaseline mit Begründung + Log-Eintrag; compact-Golden erzeugen)
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_orchestrator_compact_sections.py tests/test_template_slimming_equivalence.py tests/test_ac01_render_identity.py tests/test_standalone_export_in_sync.py -q`
- [x] Step 4: commit `feat: compact orchestrator sections behind context profile`

### Task 12: 2b.3 — Gate-Card und kompakte Agentenliste im Entry-File bereitstellen
**Agent:** senior-developer · **Issue:** #977 · **PR:** 2b · **AC:** AC-24 (C3-Teil), AC-26 (Entry-File-Ziele) · **Gate:** —
**Depends on:** 10, 11, 7
**Voraussetzung:** In der konservativen Variante (offene Nutzerfrage 1) bleibt 2b.1 ungemergt — 2b.3 baut dann als gestackter Branch auf dem 2b.1-Branch-Stand auf (Rebase-Kette, s. Ausführungsmodell „Konservative Variante“; kein Ausführungsblocker).
**Falle:** Gate-Texte werden per Section-Extraktion aus den Quell-Rules geholt (keine Kopie); Quellen `config/context-anchors.yaml::gate_card_sections`; fehlende Sektion ⇒ `SyncError`; Pointer nur auf existierende Pfade (IC-10 `context.dangling-pointer`); Entry-File ≥ `context_hard_cap_bytes` ⇒ `SyncError` `context.over-hard-cap` (nie still schreiben); **QG-5:** neues `compact`-Golden für das Entry-File.
**Files:**
- Create: `templates/context/partials/gate-card.md`
- Create: `templates/context/partials/agents-list-compact.md`
- Modify: `templates/context/agents-managed.md`
- Modify: `scripts/lib/context.py`
- Create: `tests/test_gate_card_compact.py`
- Create: `tests/fixtures/compact-golden/agents-managed.md`
**Interfaces:** Produces Verdichtungszweig `CONTEXT_PROFILE_COMPACT` in `agents-managed.md` (`gate-card`/`agents-list-compact` statt `rules-embedded`/`agents-table`), `build_gate_card(...) -> str`, Hard-Cap-Guard; `compact`-Golden (QG-5); Consumes `config/context-anchors.yaml`, `_build_managed_block`, `get_active_agents_data`
- [x] Step 1: Test schreiben (fail): Gate-Card enthält CRITICAL GATE, Git Delegation, Branch-Guard-Kern, Commit-Konventionen, Sprachregeln, Singleton, MCP-Deny-Header; fehlende Sektion ⇒ `SyncError`; Agentenliste ohne Leerzeilen; `full` byte-identisch; `compact`-Golden fehlt
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_gate_card_compact.py tests/test_provider_matrix_sync.py -q`
- [x] Step 4: commit `feat: add compact gate card and agent list to entry files`

### Task 13: 2b.4 — REFERENCE-Anteile generischer Rules in den Skills-Kanal verlagern
**Agent:** senior-developer · **Issue:** #977 · **PR:** 2b · **AC:** AC-24 (C5-Teil), AC-32 (IC-07-Klausel) · **Gate:** —
**Depends on:** 12
**Falle:** Klassifikation erweitert `_COMPACT_PLATFORM_RULES` (`context.py:1784`) um `a2a-delegation-gates`, `branch-guard`, `submodule-protection`, `security-paved-roads` nach `docs/guides/context-block-inventory.md`; INSTRUKTION-Kerne bleiben embedded; ohne Skills-Kanal bleibt der Volltext embedded (Invariante §4.3); `lazy` nur, wenn für jeden Teiler über einen gelesenen Kanal erreichbar, sonst embed + WARN; keine zweite Schreiblogik — bestehender Phase-1-Skill-Writer.
**Files:**
- Modify: `scripts/lib/context.py`
- Create: `tests/test_compact_rule_channels.py`
**Interfaces:** Produces erweiterte `_COMPACT_PLATFORM_RULES`-Tabelle, Reachability-Fallback-WARN, Nutzung von `rule_channels.reads_rule_skills`/`lazy_skill_channel`; Consumes `collect_rule_sources`, `resolve_rules`, `lazy_skill_stems`, `docs/guides/context-block-inventory.md`
- [x] Step 1: Test schreiben (fail): Fixture-Provider mit Skills-Kanal ⇒ REFERENCE-Teile als `<skills_dir>/<rule>/SKILL.md`, INSTRUKTION-Kerne embedded; Provider ohne Kanal ⇒ Volltext + keine Datei; `context.rule-unreachable` bleibt 0
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_compact_rule_channels.py tests/test_lazy_skills_channel.py tests/test_context_budget_checks.py -q`
- [x] Step 4: commit `feat: lazy-load reference rule sections in compact profile`

### Task 14: 2b.5 — CLAUDE.md-Notizen im `compact`-Profil als HTML-Kommentare rendern
**Agent:** developer · **Issue:** #977 · **PR:** 2b · **AC:** AC-24 (C6-Teil) · **Gate:** —
**Depends on:** 13
**Falle:** nur für Dateien, deren alleiniger Leser Capability `strips_html_comments: true` hat (Claude); nie in geteilten Dateien; `full` byte-identisch.
**Files:**
- Modify: `templates/context/claude-managed.md`
- Modify: `scripts/lib/context.py`
- Modify: `tests/test_gate_card_compact.py`
**Interfaces:** Produces Notiz-Block als `<!-- … -->` im `compact`-Zweig der Claude-Datei; Consumes `merged_caps(provider, …)`, `strips_html_comments`
- [x] Step 1: Test schreiben (fail): Claude-Fixture `compact` ⇒ Notizen als Kommentar; geteilte Datei oder Fremd-Provider ⇒ unverändert sichtbar/aus
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_gate_card_compact.py tests/test_context_docs_corrections.py -q`
- [x] Step 4: commit `feat: render claude notes as html comments in compact profile`

### Task 15: 2b.6 — CHANGELOG und Klassifikations-Doku für Paket 2b pflegen
**Agent:** documenter · **Issue:** #977 · **PR:** 2b · **AC:** AC-24 (Doku), AC-86 (Unverified-Hinweis) · **Gate:** —
**Depends on:** 10, 11, 12, 13, 14
**Falle:** `compact` bleibt „Opt-in, unverifiziert“; Klassifikationstabelle in `docs/guides/context-block-inventory.md` muss die vier neuen REFERENCE-Regeln führen.
**Files:**
- Modify: `CHANGELOG.md`
- Modify: `docs/guides/context-block-inventory.md`
- Modify: `tests/test_context_profile_docs.py`
**Interfaces:** Produces Klassifikationseinträge (REFERENCE-Anteile der vier Regeln, INSTRUKTION-Kerne) + CHANGELOG; Consumes 2b.4
- [x] Step 1: Test schreiben (fail): Klassifikationstabelle ohne die REFERENCE-Anteile der vier Regeln ⇒ rot
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_context_profile_docs.py -q && python3 scripts/consistency-check.py`
- [x] Step 4: commit `docs: record compact render classification`

## Paket 2c — Budgets, Anker und Report für `compact` (IC-09…IC-12)

### Task 16: 2c.1 — Pflicht-Anker für `compact` in der Anker-Registry hinterlegen
**Agent:** tester · **Issue:** #977 · **PR:** 2c · **parallel_group:** 2c-g1 · **AC:** AC-24 (QG-3), AC-06 (compact-Teil) · **Gate:** —
**Depends on:** 12, 14
**Falle:** `compact-only`-Listen je Artefakt-Kind füllen (Gate-Card-Anker inkl. MCP-Deny-Tokens, erstmals MCP-active Fixture); Anker sind wörtlich, Änderungen brechen den Test bewusst.
**Files:**
- Modify: `config/context-anchors.yaml`
- Modify: `tests/test_context_anchors.py`
- Create: `tests/fixtures/mcp-active/.meta-config/project.yaml`
**Interfaces:** Produces `compact-only`-Ankerlisten + Testlauf je Provider × Profil; Consumes `measure_artifacts`-Renders der Matrix
- [x] Step 1: Test schreiben (fail): `compact`-Renders ohne Gate-Card-Anker ⇒ rot
- [x] Step 2: implementieren (Ankerlisten aus 2b.3/2b.4/2b.5)
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_context_anchors.py -q`
- [x] Step 4: commit `chore: pin compact profile anchors in the registry`

### Task 17: 2c.2 — `--context-report --profile compact|both` real rendern und Ziele pinnen
**Agent:** senior-developer · **Issue:** #977 · **PR:** 2c · **parallel_group:** 2c-g1 · **AC:** AC-26, AC-11 (Δ) · **Gate:** —
**Depends on:** 14
**Falle:** kein stdout-only-Modus; Rendern in ein Arbeitsverzeichnis via `resolve_work_dir`; `--profile compact` injiziert `context-profile: compact` in die Temp-Kopie, nicht in die Projekt-Config; Zielwerte **nicht** als Lib-Konstante in `context_report.py` führen, sondern als Test-/Config-Daten: QG-4-Pins in `tests/test_context_budgets.py` plus Caps als Config-Keys (C7); Ziele als Schätzwerte markieren (Spec §11), nie still anpassen.
**Files:**
- Modify: `scripts/lib/context_report.py`
- Modify: `scripts/lib/cli_commands.py`
- Modify: `tests/test_context_report.py`
- Modify: `tests/test_context_budgets.py`
**Interfaces:** Produces `--profile compact|both` mit echtem `compact`-Render, Report-Δ `full` vs. `compact`, Zielwerte als Daten (`tests/test_context_budgets.py`, Caps als Config-Keys); Consumes `resolve_context_profile`, `resolve_work_dir`, `measure_artifacts`
- [x] Step 1: Test schreiben (fail): `--profile compact` misst `compact`-Artefakte (Claude-Orchestrator ≤ 32 KB, AGENTS.md Einzel ≤ 8 KB, Multi ≤ 12 KB und < 32,768 B, Gemini ≤ 9 KB, Continue ≤ 2 KB, Copilot ≤ 4,000 Zeichen); künstliche Vergrößerung ⇒ rot; Projekt-Config unverändert (Hash-Snapshot)
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_context_report.py tests/test_context_budgets.py -q`
- [x] Step 4: commit `feat: report and pin compact profile budgets`

### Task 18: 2c.3 — Provider-Matrix 9×2, Idempotenz und `compact`-Checks absichern
**Agent:** tester · **Issue:** #977 · **PR:** 2c · **AC:** AC-24 (QG-2), AC-27, AC-28 · **Gate:** —
**Depends on:** 16, 17, 13
**Voraussetzung:** In der konservativen Variante (2b.1-Hold-back, offene Nutzerfrage 1) laufen Matrix und `--check`-Nachweis gegen den Kandidaten-Build des 2b.1-Branch-Stacks (s. Ausführungsmodell); `Depends on:` bleibt unverändert.
**Falle:** Multi-Provider-Kombinationen mit Shared-File-Downgrade einschließen; `--check` ist nach `compact`-Sync grün (zweimaliger Sync byte-identisch); `context.dangling-pointer`/`context.rule-unreachable` laufen für `compact` auf ihrer Phase-1-Stufe (ERROR) — Fixtures müssen matrixweit 0 Befunde liefern; **QG-2-Vollset explizit:** Mengengleichheit `full` ↔ `compact` für Rollen, Keywords, Pipeline-Signal-Keywords, Flags (`required`/`recommended`/`orchestrator_only`), Name-only-Liste + Gründe; die IC-04-Beispielregel ist verifiziert; jeder in `compact` entfernte Abschnitt (§2a, §9-Begründung, Contracts, `short_desc`) ist über einen existierenden Pointer erreichbar (Pfad existiert, Abschnitt dort vorhanden).
**Files:**
- Create: `tests/test_compact_matrix.py`
- Modify: `tests/test_provider_matrix_sync.py`
- Modify: `tests/test_context_budget_checks.py`
**Interfaces:** Produces Matrix-Lauf 9 Provider × 2 Profile + Shared-File-Kombinationen, Informationserhaltungs-Prüfung nach QG-2-Vollset, Idempotenz-Check; Consumes 2b/2c.1/2c.2-Artefakte
- [x] Step 1: Test schreiben (fail): `compact`-Matrix ohne Vollständigkeit ⇒ rot (fehlende Kombination/Idempotenzverletzung/QG-2-Mengendifferenz)
- [x] Step 2: implementieren (Fixtures/Wiederholungssync)
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_compact_matrix.py tests/test_provider_matrix_sync.py tests/test_context_budget_checks.py -q`
- [x] Step 4: commit `test: cover compact profile across the provider matrix`
- [x] Step 5: Nachweis `sync.py --check` nach `compact`-Sync (Ausgabe im PR protokollieren)

### Task 19: 2c.4 — Doku und CHANGELOG für das `compact`-Profil veröffentlichen
**Agent:** documenter · **Issue:** #977 · **PR:** 2c · **AC:** AC-26 (Doku), AC-86 · **Gate:** —
**Depends on:** 18
**Falle:** Ziele als Schätzungen kennzeichnen; keine Aussage zu AC-25; `--profile compact|both` in `docs/api/cli-reference.md` von „reserved for Phase 2“ auf den realen Stand heben.
**Files:**
- Modify: `docs/api/cli-reference.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `tests/test_context_profile_docs.py`
**Interfaces:** Produces Doku „Profil `compact` (Opt-in, unverifiziert)“ mit Zielwerten und Unverified-Hinweis; Consumes 2c.1–2c.3
- [x] Step 1: Test schreiben (fail): cli-reference sagt noch „reserved for Phase 2“; README ohne Profil-Abschnitt
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_context_profile_docs.py tests/test_context_report.py -q && python3 scripts/consistency-check.py`
- [x] Step 4: commit `docs: publish opt-in compact profile`

## Paket 2d — Config-Optimizer, Applier, Laufzeit-Leser (IC-24, IC-25, IC-35)

### Task 20: 2d.1 — Laufzeit-Leser-Registry mit Credential-Markierung anlegen
**Agent:** developer · **Issue:** #977 · **PR:** 2d · **AC:** AC-81 (Registry-Teil), AC-89 (Credential-Muster) · **Gate:** —
**Depends on:** —
**Voraussetzung:** 0a-III (IC-34, #981) und 0b (IC-17, #984) sind gemergt — nicht Teil dieses Plans.
**Falle:** Evidenz-Pfade am Code verifizieren (Hook-/Server-Zeilen); Vollständigkeits-Ratchet über `hooks/**/*.sh` **und** `scripts/*.py` mit begründeter Ausnahmeliste (Start-Klassifikation Spec Rev. 3.1: `admin-server.py`, `consistency-check.py`, `gen_routing_llm_eval_catalog.py`, `lifecycle_check.py`, `migrate-config.py`, `migrate-plugin-registry.py`, `se-export.py`, `sync.py`, `viz-logger.py`, `viz-report.py`); Ausnahmeliste darf nur schrumpfen; `credentials.name_patterns` segmentgenau (`max-tokens-overrides` darf nicht treffen); `release-gates` ist kein Eintrag; **Doctor-Konsument (IC-35):** `detect_variable_unreferenced` (`doctor_detectors.py`) zählt registrierte Laufzeit-Leser (Pfad/Key der Registry) als Nutzung, sonst meldet der Doctor Laufzeit-Konsumenten fälschlich als unreferenziert.
**Files:**
- Create: `config/runtime-config-readers.yaml`
- Create: `tests/test_runtime_config_readers.py`
- Modify: `scripts/lib/doctor_detectors.py`
- Modify: `tests/test_doctor_fixtures.py`
**Interfaces:** Produces Registry `{registry-version, readers[], credentials{name_patterns, keys, value_scan}}` (Seed F-43 inkl. `admin-ui`, `viz`, `lifecycle-triggers`, `variables.TEST_COMMAND`/`TEST_TIMEOUT`/`GIT_MAIN_BRANCH`, `repo_containment`, `orchestrator`), Ratchet-Test, Doctor-Wiring (Laufzeit-Leser zählen als Nutzung); Consumes `secrets.scan_for_secrets(content: str, config: dict | None = None) -> list[str]`, `permissions.restrict_owner_only`, `doctor_detectors.detect_variable_unreferenced`
- [x] Step 1: Test schreiben (fail): jeder `evidence`-Pfad existiert und nennt den Key/`project.yaml`; neuer unregistrierter `.sh`-/`scripts/*.py`-Leser ⇒ rot; Positiv-/Negativliste der Muster (`admin-ui.token` trifft, `max-tokens-overrides` nicht); Doctor-Fixture: Variable, die nur über einen registrierten Laufzeit-Leser konsumiert wird ⇒ kein `doctor.variable-unreferenced`-Befund
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_runtime_config_readers.py tests/test_doctor_fixtures.py -q`
- [x] Step 4: commit `feat: add runtime config reader registry with credentials`

### Task 21: 2d.2 — Optimizer-Runner mit Kandidaten, Fan-out und L0-Beweis bereitstellen
**Agent:** senior-developer · **Issue:** #977 · **PR:** 2d · **AC:** AC-54, AC-55 (Beweis-Teil inkl. L0-Vergleichsmenge), AC-57 (Hinweis-Klassifikation, `--include-semantic`), AC-58, AC-75/AC-94/AC-98 (Optimizer-Teil), AC-89 (Runner-Teil), AC-91 (Proposal-Felder) · **Gate:** —
**Depends on:** 20
**Falle:** Sentinel-Render in `<tmp-sink>/meta-optimizer/<ts>/work/` via `resolve_work_dir` (nie Systemtemp); Konditional-Variablen nicht umschließen (`occurrences: null`, `conditional: true`); Credential-Pfade ohne Kandidat/Hinweis/FanOutEntry/Wert in `rationale`; Universe-Prüfung für `no-effect` (`variables.*` nur ohne Template-Referenz oder builder-überschrieben); `--fill-defaults` in derselben Invocation ⇒ `meta-optimizer.lossy-flag` (Exit 2); Sink deaktiviert ⇒ `tmp-sink.disabled` (Exit 2); Projekt-/Framework-Hash-Snapshot belegt „schreibt nur in den Sink“; **L0-Vergleichsmenge (AC-55 Rev. 3):** `.meta-config/auto-commit-allowlist.json` liegt heute **nicht** in der Vergleichsmenge (`generated_file_drift.py` walkt nur Provider-Verzeichnisse; `_sync_stage_auto_commit_allowlist` schreibt bewusst **nach** der Hash-Capture, `sync_pipeline.py:1571-1579`) ⇒ in die L0-Vergleichsmenge von `prove(...)` aufnehmen und testen; **semantische Arten** (`duplicate-value`, `relocate-*`, `semantic-merge`) erscheinen nur mit `--include-semantic` (AC-57). **Weitere `.meta-config/*.json` (§13, „Planer prüft“):** `generated-file-hashes.json` und `context-hashes.json` werden wie `.meta-config/auto-commit-allowlist.json` in die L0-Vergleichsmenge **aufgenommen** (beide sind render-abgeleitete Sidecars; ein wirkungsfreier Kandidat darf sie nicht ändern) und in `proof.json` als Vergleichsdateien gelistet.
**Files:**
- Create: `scripts/lib/meta_optimizer.py`
- Modify: `scripts/sync.py`
- Modify: `scripts/lib/cli_commands.py`
- Modify: `docs/api/cli-reference.md`
- Modify: `CHANGELOG.md`
- Create: `tests/test_meta_optimizer_runner.py`
- Create: `tests/test_meta_optimizer_fanout.py`
- Create: `tests/fixtures/meta-optimizer/`
**Interfaces:** Produces `CandidateKind`, `Candidate(id, kind, yaml_path, scope, marks, approval_level, warnings, deterministic, applicable, proof_level_required, yaml_bytes_saved, injected_bytes_saved_est, rationale, hunks)`, `FanOutEntry(variable, value_bytes, occurrences, files, injected_bytes, per_provider)`, `OptimizerProposal(project_yaml_sha256, agent_meta_version, generator_options, candidates, fan_out, diff)`, `collect_candidates(project_root: Path, agent_meta_root: Path, config: dict, config_text: str, active: ActiveSet) -> OptimizerProposal`, `prove(...) -> ProofReport` (L0 + Bisektion, `scope_note`, Vergleichsmenge inkl. `.meta-config/{auto-commit-allowlist,generated-file-hashes,context-hashes}.json`), `advance_l0(…)`; CLI `sync.py --optimize-config [--json] [--include-semantic] [--out <dir>]` mit `proposal.json`/`proposal.diff`/`proof.json`; Consumes `resolve_work_dir`, `resolve_output_dir`, `eval_gate`-freier Lauf, `yaml_roundtrip.analyze_roundtrip`, Laufzeit-Registry aus 2d.1
- [x] Step 1: Test schreiben (fail): selbst-gehostete Config ⇒ `no-effect` für `variables.ORCHESTRATOR_STRICT`, `variables.UNKNOWN_FALLBACK_*`, `variables.SE_BASE_DIR`, `CODE_QUALITY_RULES` als `dead-variable-content-loss`; Fan-out exakt gegen unabhängige Sentinel-Zählung; `tempfile.*`-Monkeypatch wirft; Hash-Snapshot außerhalb des Sinks leer; absichtlich wirksame Variable ⇒ `meta-optimizer.proof-failed` ohne Schreiben; Prüfschritt L0-Vergleichsmenge: `.meta-config/auto-commit-allowlist.json`, `.meta-config/generated-file-hashes.json` und `.meta-config/context-hashes.json` werden vor/nach dem Beweis verglichen (Hash gleich) und in `proof.json` als Vergleichsdateien gelistet; ohne `--include-semantic` erscheinen keine `deterministic: false`-Kandidaten, mit Flag erscheinen sie (`duplicate-value` als `info-only`)
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_meta_optimizer_runner.py tests/test_meta_optimizer_fanout.py -q && python3 scripts/consistency-check.py`
- [x] Step 4: commit `feat: add config optimizer runner with fan-out and proof`

### Task 22: 2d.3 — Applier mit Vorschau, Neuberechnung und Remove-only einführen
**Agent:** senior-developer · **Issue:** #977 · **PR:** 2d · **AC:** AC-55 (Anwendung), AC-56, AC-80, AC-90 (Applier-Teil), AC-91 (Anwendbarkeit: `version-mismatch`, `rejected: not-applicable`), AC-57 (`rejected: not-applicable`), AC-75/AC-94 (Applier-Teil), AC-89 (Redaktion/Mode) · **Gate:** —
**Depends on:** 21
**Falle:** `--accept` Pflicht; ohne `--preview` und ohne `--dry-run` ⇒ Exit 2; Neuberechnung + Remove-only (`after_yaml` Zeilen-Teilfolge) + Hunk-Abgleich (redigierte Formen); TOCTOU-Recheck vor `os.replace`; Temp-Datei `<sink>/meta-optimizer/<ts>/project.yaml.new`, cross-device ⇒ Exit 1 `meta-optimizer.cross-device`; `project.yaml.bak` nur mit redigierten Credential-Werten, `applied.json.approval_source` ausschließlich `relayed`, `backup_redacted_keys` nur Namen; Hinweis-ID in `--accept` ⇒ `rejected: not-applicable`; `--accept-runtime` für `confirm-runtime`; alle Sink-Dateien `0600`; **`version-mismatch` (AC-91):** weicht `proposal.json.agent_meta_version` von der laufenden Framework-Version ab ⇒ Exit 1, nichts wird geschrieben.
**Files:**
- Modify: `scripts/lib/meta_optimizer.py`
- Modify: `scripts/sync.py`
- Modify: `scripts/lib/cli_commands.py`
- Modify: `docs/api/cli-reference.md`
- Modify: `CHANGELOG.md`
- Create: `tests/test_meta_optimizer_applier.py`
**Interfaces:** Produces `apply_config_patch(project_root: Path, agent_meta_root: Path, proposal_path: Path, accept_ids: Sequence[str], *, accept_runtime_ids: Sequence[str] = (), preview_path: Path | None = None, dry_run: bool) -> ApplyReport`, `ApplyReport(applied_ids, rejected, preview_sha256, project_yaml_sha256_before/after, backup_redacted_keys, log_path)`, CLI `sync.py --apply-config-patch <proposal.json> --accept <id>… [--accept-runtime <id>…] [--dry-run] [--preview <preview.json>]`; Consumes `collect_candidates`, `prove`, `yaml_roundtrip.analyze_roundtrip`, `_count_comments`, `restrict_owner_only`
- [x] Step 1: Test schreiben (fail): (a) ohne `--accept` Exit 2; (b) manipulierte `proposal.json` ⇒ `hunk-mismatch`/`not-remove-only`, Datei unverändert; (c) nicht reproduzierbare ID ⇒ `not-reproducible`; (d) `preview.json`-Mismatch ⇒ `preview-mismatch`; (e) TOCTOU-Hook ⇒ `stale-proposal`; (f) `applied.json`-Felder inkl. `approval_source == "relayed"`; (g) Kommentare/Reihenfolge via `analyze_roundtrip` erhalten (`expected_comment_loss` aus `_count_comments` der entfernten Zeilen); (h) Fixture mit abweichender `agent_meta_version` ⇒ Exit 1 `version-mismatch`, nichts geschrieben (AC-91); (i) Hinweis-ID in `--accept` ⇒ `rejected: not-applicable`, keine Dateiänderung (AC-57/AC-91); (j) `tempfile.*`-Monkeypatch läuft für `--apply-config-patch` durch (AC-94), Sink-Protokoll und Backup liegen unter `<sink>/meta-optimizer/<ts>/` (AC-75)
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_meta_optimizer_applier.py tests/test_meta_optimizer_runner.py -q`
- [x] Step 4: commit `feat: add remove-only config patch applier with preview binding`

### Task 23: 2d.4 — `fill_defaults`-Wechselwirkung als `info-only` abbilden
**Agent:** developer · **Issue:** #977 · **PR:** 2d · **AC:** AC-82 · **Gate:** —
**Depends on:** 22
**Falle:** `refill_keys` aus **denselben** Funktionen berechnen, die `fill_defaults` nutzt (`config_field_defaults()`, Schema-Top-Level-Defaults, Sonderblöcke `repo_containment`/`project.short`/`dod`), keine Kopie; für diese Keys nie ein Entfernungs-Hunk, nur `info-only` mit Mark `refilled-by-defaults` und Pflichttext; `structural-simplify` erzeugt nie einen Hunk.
**Files:**
- Modify: `scripts/lib/meta_optimizer.py`
- Create: `tests/test_meta_optimizer_refill.py`
**Interfaces:** Produces `refill_keys(agent_meta_root: Path, config: dict) -> set[str]`, Mark `refilled-by-defaults`, Pflichttext; Consumes `config.config_field_defaults(agent_meta_root: Path) -> dict`, `config.fill_defaults`
- [x] Step 1: Test schreiben (fail): Key aus `refill_keys` ⇒ kein Hunk, `applicable: false`, Mark + Text; Anwenden aller akzeptierbaren Kandidaten, dann regulärer Sync ⇒ `project.yaml` byte-gleich
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_meta_optimizer_refill.py -q`
- [x] Step 4: commit `feat: mark refilled defaults as non-removable hints`

### Task 24: 2d.5 — `inactive-scope`-Kandidaten mit Reaktivierungs-Warnung ausweisen
**Agent:** developer · **Issue:** #977 · **PR:** 2d · **AC:** AC-83 · **Gate:** —
**Depends on:** 23
**Falle:** Abgrenzung zu `no-effect`: nur im aktuellen Active Set wirkungslos ⇒ `inactive-scope` (nicht `no-effect`), `deterministic: false`, Mark `reactivation-loss-warning` mit Pflichttext „Bei späterer Reaktivierung …“; Fixture p10-artig (`tests/fixtures/active-set/p10`); nach Anwendung + Re-Sync mit aktivierter Rolle erscheint `active-set.unresolved-placeholder` bzw. der Framework-Default, wie in der Warnung angekündigt.
**Files:**
- Modify: `scripts/lib/meta_optimizer.py`
- Create: `tests/test_meta_optimizer_inactive_scope.py`
**Interfaces:** Produces Kandidatenart `inactive-scope`, Pflichttext, Test-Fixture-Kopplung an `tests/fixtures/active-set/p10`; Consumes `ActiveSet`, `resolve_active_roles`, `_VARIABLE_FALLBACKS`
- [x] Step 1: Test schreiben (fail): `variables.TEST_COMMANDS` bei inaktivem `tester` ⇒ `inactive-scope` mit Warnung, kein `no-effect`
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_meta_optimizer_inactive_scope.py -q`
- [x] Step 4: commit `feat: classify inactive-scope candidates with reactivation warning`

### Task 25: 2d.6 — Laufzeit-Leser als `confirm-runtime` markieren
**Agent:** developer · **Issue:** #977 · **PR:** 2d · **AC:** AC-81 · **Gate:** —
**Depends on:** 24
**Falle:** Mark `runtime-reader` + `approval_level: confirm-runtime` + Pflichttext mit Leser-Namen aus der Registry; ohne `--accept-runtime` ⇒ `rejected: needs-runtime-confirmation`; Credential-Keys haben Vorrang und erscheinen nicht; kein Ausschluss (Nutzerentscheidung), nur Markierung.
**Files:**
- Modify: `scripts/lib/meta_optimizer.py`
- Create: `tests/test_meta_optimizer_marks.py`
**Interfaces:** Produces Mark `runtime-reader`, `approval_level: confirm-runtime`, Ablehnungsgrund `needs-runtime-confirmation`; Consumes `config/runtime-config-readers.yaml`
- [x] Step 1: Test schreiben (fail): Kandidat für `repo_containment`, `orchestrator.*` oder `variables.TEST_COMMAND` ⇒ Mark + Text; Anwendung nur mit `--accept-runtime`
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_meta_optimizer_marks.py tests/test_runtime_config_readers.py -q`
- [x] Step 4: commit `feat: require runtime confirmation for runtime-reader keys`

### Task 26: 2d.7 — Credential-Ausschluss und Sink-Härtung end-to-end absichern
**Agent:** tester · **Issue:** #977 · **PR:** 2d · **AC:** AC-89 · **Gate:** —
**Depends on:** 22, 25
**Falle:** Fixture mit `admin-ui.token` (Testwert ≥ 20 Zeichen), `admin-ui.token-file`, `variables.API_TOKEN` und einem `scan_for_secrets`-Treffer; Testwert darf in **keiner** Datei unter `<tmp-sink>/meta-optimizer/` als Byte-Folge vorkommen; Redaktionsmarker im Diff-Kontext; Modus `0600` (POSIX, sonst Skip); `max-tokens-overrides` Negativfall.
**Files:**
- Create: `tests/test_meta_optimizer_credentials.py`
- Create: `tests/fixtures/meta-optimizer/credentials/.meta-config/project.yaml`
**Interfaces:** Produces E2E-Beweis für Redaktion/Modus/`backup_redacted_keys`; Consumes `sync.py --optimize-config`, `--apply-config-patch --dry-run`, `secrets.scan_for_secrets`
- [x] Step 1: Test schreiben (fail): Fixture ohne Redaktion ⇒ rot
- [x] Step 2: Fixtures/Implementierungslücken schließen (nur im 2d-Modul)
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_meta_optimizer_credentials.py -q`
- [x] Step 4: commit `test: prove credential exclusion in optimizer sink artifacts`

## Paket 2e — Rolle `meta-optimizer` und Freigabe-Workflow (IC-26, IC-27, IC-28)

### Task 27: 2e.1 — Rolle `meta-optimizer` als read-only Proposal-Rolle anlegen
**Agent:** prompt-engineer · **Issue:** #977 · **PR:** 2e · **AC:** AC-79, AC-59 (Rollen-Teil), AC-91 (Berichts-Teil) · **Gate:** —
**Depends on:** 21, 22
**Falle:** `tools: [Read, Glob, Grep, TodoWrite]` — kein Bash/Write/Edit/Agent; Output-Contract mit `ARTIFACTS: none`; `warnings` wörtlich, Hinweise als „nicht anwendbar — manuelle Nutzeränderung bzw. Framework-Issue“; keine Credential-Werte zitieren; `name_only` ohne `routing_patterns`; H-4-Texte (`description`, `short_desc`, `name_only_reason`) ausformuliert; ausführender Schritt liegt bei `agent-meta-manager` (IC-27); **Standalone-Check (A-F-2):** Quelle auf Konditionale prüfen — enthält sie `{{#if …}}`, fehlende Einträge in `standalone._CONDITIONAL_FALSE_FLAGS` ergänzen (sonst keine Änderung; Ergebnis im PR notieren).
**Files:**
- Create: `agents/1-generic/meta-optimizer.md`
- Modify: `config/role-defaults.yaml`
- Create: `tests/test_meta_optimizer_role.py`
**Interfaces:** Produces Rolle `meta-optimizer` (`name: template-meta-optimizer`, `version: "1.0.0"`, `prompt_mode: modern`), `role-defaults`-Eintrag (`model: balanced`, `workflow_tier: optional`, `name_only`, `orchestrator_only: true`, Handoff `input_contracts: [task-spec-v1]`, `output_contract: config-patch-proposal-v1`, `target_roles: [agent-meta-manager]`), Contract-Marker `PROPOSALS`/`PROOF`; Consumes `sync.py --optimize-config`-Proposal-Felder (2d.2), IC-26-Wortlaut
- [x] Step 1: Test schreiben (fail): exakte Tool-Menge, kein `model:` in der Quelle, Contract-Marker, keine Schreib-/Ausführungsanweisung, Hinweis-Kennzeichnung
- [x] Step 2: implementieren (inkl. Standalone-Konditional-Check)
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_meta_optimizer_role.py -q && python3 scripts/consistency-check.py`
- [x] Step 4: commit `feat: add read-only meta-optimizer proposal role`

### Task 28: 2e.2 — `meta-optimizer` nach IC-28 registrieren und Goldens rebaselinen
**Agent:** developer · **Issue:** #977 · **PR:** 2e · **AC:** AC-23 (Ausnahmeliste (i)–(iii)), AC-59 (Registrierung) · **Gate:** —
**Depends on:** 27
**Falle:** `_EXPECTED_TOTAL` 93 → 94, Verteilung `{"keyword": 88, "name_only": 5, "excluded": 1}`, sortierte Liste in `test_name_only_roles_have_reason` (`intern-developer`, `meta-doctor`, `meta-optimizer`, `principal-developer`, `template-auditor`); `_GOLDEN_ROLE_COUNT` bleibt 58; `_EXPECTED_GROUPS` unverändert (`tests/test_role_activation_schema.py`; Q17: keine Gruppe); Golden-/`hashes.json`-Rebaseline mit Begründung; AC-01/AC-23-Ausnahmeliste rollenspezifisch erweitern (**nie pauschal**); **`AC01_EXCEPTIONS`-Pattern:** `.*/meta-optimizer\.[a-z]+$` fasst `meta-optimizer.agent.md` nicht (Punkt im Suffix) ⇒ auf `.*/meta-optimizer\.(md|toml|agent\.md)$` erweitern (Muster `meta-doctor`).
**Files:**
- Modify: `config/project-config.schema.json`
- Modify: `tests/test_role_addressability_coverage.py`
- Modify: `tests/fixtures/slimming-golden/orchestrator.md`
- Modify: `tests/fixtures/slimming-golden/agent-meta-manager.md`
- Modify: `tests/test_ac01_render_identity.py`
- Modify: `tests/fixtures/ac01-baseline/hashes.json`
- Modify: `tests/scenarios/registry.md`
- Modify: `standalone/README.md`
- Modify: `docs/guides/setup/instantiate-project.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Create: `standalone/agents/meta-optimizer.md`
- Create: `tests/scenarios/configs/78-meta-optimizer-role.project.yaml`
- Create: `tests/scenarios/asserts/78-meta-optimizer-role.sh`
**Interfaces:** Produces Szenario 78, Schema-Rollen-Enum (regeneriert), Golden-Rebaseline mit Rebaseline-Log, erweitertes `AC01_EXCEPTIONS`-Pattern; Consumes `schema.update_roles_enum`, `sync.py --render-standalone`, `tests/scenarios/run.sh` (`chmod +x`)
- [x] Step 1: Test schreiben (fail): Pins, Szenario 78 und AC-01-Harness melden fehlende Registrierung; `meta-optimizer.agent.md`-Pattern-Fixture (Copilot) fehlt
- [x] Step 2: implementieren (Sync, Export, Rebaseline mit Begründung, Pattern-Erweiterung)
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_role_addressability_coverage.py tests/test_standalone_export_in_sync.py tests/test_ac01_render_identity.py -q && bash tests/scenarios/run.sh 78-meta-optimizer-role`
- [x] Step 4: commit `chore: register meta-optimizer role across schema and goldens`

### Task 29: 2e.3 — Contract `config-patch-proposal-v1` verdrahten
**Agent:** prompt-engineer · **Issue:** #977 · **PR:** 2e · **AC:** AC-59 (Consumer) · **Gate:** —
**Depends on:** 27
**Falle:** `agent-meta-manager` muss den Contract in `handoff.input_contracts` führen, sonst `handoff.output-not-consumed`; `config-patch-proposal-v1` bleibt Phase-2-Contract (nicht 0e); Schema-Ablage nach bestehendem Muster unter `schemas/handoffs/`.
**Files:**
- Modify: `config/role-defaults.yaml`
- Create: `schemas/handoffs/config-patch-proposal.schema.json`
- Modify: `tests/test_meta_optimizer_role.py`
**Interfaces:** Produces Consumer-Eintrag + Handoff-Schema; Consumes `consistency/handoff_contracts.check_handoff_contracts(agent_meta_root: Path) -> list[Finding]`
- [x] Step 1: Test schreiben (fail): `handoff.output-not-consumed` für `config-patch-proposal-v1`
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `python3 scripts/consistency-check.py && python3 -m pytest tests/test_meta_optimizer_role.py -q`
- [x] Step 4: commit `feat: wire config-patch-proposal contract into the manager`

### Task 30: 2e.4 — `agent-meta-manager`-Workflow um Analyse, Vorschau und Anwendung ergänzen
**Agent:** prompt-engineer · **Issue:** #977 · **PR:** 2e · **AC:** AC-59, AC-90 (Manager-Schritte), AC-91 (Manager-Teil) · **Gate:** —
**Depends on:** 29
**Falle:** drei Schritte (1) `sync.py --optimize-config --json --out {{TMP_SINK_PATH}}/meta-optimizer/<ts>/` ausführen und Pfad zurückgeben, (2) Vorschau `--dry-run` erzeugen, (3) Anwendung nur `--preview <preview.json>` nach wörtlich weitergeleiteter Nutzerantwort; `project.yaml` nie per `Edit`; kein `--fill-defaults`; Version-Bump + Golden-Rebaseline.
**Files:**
- Modify: `agents/1-generic/agent-meta-manager.md`
- Modify: `tests/fixtures/slimming-golden/agent-meta-manager.md`
- Modify: `tests/fixtures/ac01-baseline/hashes.json`
- Modify: `tests/test_ac01_render_identity.py`
- Modify: `tests/test_meta_optimizer_role.py`
**Interfaces:** Produces Abschnitt „Optimizer-Vorschläge anwenden (Advisory Mode)“ mit den drei Schritten und der „nur wörtlich weitergeleitete IDs“-Regel; Consumes `config-patch-proposal-v1`, 2d.3-CLI
- [x] Step 1: Test schreiben (fail): Manager ohne die drei Schritte/Schritt-Verben ⇒ rot; `handoff.output-not-consumed` bleibt grün
- [x] Step 2: implementieren (Version-Bump `1.24.z → 1.25.0`)
- [x] Step 3: Test (pass): `python3 scripts/consistency-check.py && python3 -m pytest tests/test_meta_optimizer_role.py tests/test_ac01_render_identity.py -q`
- [x] Step 4: commit `feat: add optimizer apply workflow to agent-meta-manager`

### Task 31: 2e.5 — Orchestrator zur Vorschau-Pflicht verpflichten
**Agent:** prompt-engineer · **Issue:** #977 · **PR:** 2e · **AC:** AC-90 (Orchestrator-Teil), AC-23 (IC-27-Template-Teil) · **Gate:** —
**Depends on:** 30
**Falle:** `preview.json` muss dem Nutzer über `main_chat` gezeigt werden, bevor eine Anwendung veranlasst wird; keine Ergänzung von IDs, die nicht wörtlich in der weitergeleiteten Nutzerantwort stehen; kein Bash für Orchestrator/`meta-optimizer`; Version-Bump + Rebaseline (`tests/fixtures/slimming-golden/orchestrator.md`, `tests/fixtures/ac01-baseline/hashes.json`, Rebaseline-Log in `tests/test_ac01_render_identity.py`).
**Files:**
- Modify: `agents/1-generic/orchestrator.md`
- Modify: `tests/fixtures/slimming-golden/orchestrator.md`
- Modify: `tests/fixtures/ac01-baseline/hashes.json`
- Modify: `tests/test_ac01_render_identity.py`
- Modify: `tests/test_meta_optimizer_role.py`
**Interfaces:** Produces Pflichtabsatz „Vorschau zeigen (`preview.json`) → Bestätigung einholen → Manager mit `--preview` beauftragen“; Consumes `orchestrator.md:20`-Kanalregel
- [x] Step 1: Test schreiben (fail): Orchestrator ohne Vorschau-Pflicht ⇒ rot
- [x] Step 2: implementieren (Version-Bump Minor)
- [x] Step 3: Test (pass): `python3 -m pytest tests/test_meta_optimizer_role.py tests/test_orchestrator_compact_sections.py tests/test_ac01_render_identity.py -q`
- [x] Step 4: commit `feat: require optimizer preview approval in orchestrator`

### Task 32: 2e.6 — Szenario-78-Asserts, CLI-Doku und Konventions-Praxis abschließen
**Agent:** documenter · **Issue:** #977 · **PR:** 2e · **AC:** AC-59 (Doku/Szenario), AC-79/AC-91 (Asserts) · **Gate:** —
**Depends on:** 28, 31
**Falle:** Asserts prüfen je Provider generiert, kein Bash/Write/Edit/Agent, OpenCode `edit: deny`, kein `model:` in der Quelle, Platzhalter aufgelöst, keine Keyword-Regel in `routing.rules`, jede `warnings`-Zeile wörtlich, `ARTIFACTS: none`; `docs/api/cli-reference.md` dokumentiert beide Optimizer-Flags inkl. Exit-Codes; Praxis-Hinweise in `agent-meta-conventions.md` ergänzen.
**Files:**
- Modify: `tests/scenarios/asserts/78-meta-optimizer-role.sh` (chmod +x)
- Modify: `tests/scenarios/registry.md`
- Modify: `docs/api/cli-reference.md`
- Modify: `docs/guides/setup/instantiate-project.md`
- Modify: `README.md`
- Modify: `rules/2-platform/agent-meta-conventions.md`
- Modify: `CHANGELOG.md`
- Modify: `tests/test_meta_optimizer_role.py`
**Interfaces:** Produces vollständige Szenario-78-Asserts + Doku; Consumes 2e.1–2e.5
- [x] Step 1: Test schreiben (fail): Asserts fehlen oder bestehen das Szenario nicht
- [x] Step 2: implementieren
- [x] Step 3: Test (pass): `bash tests/scenarios/run.sh 78-meta-optimizer-role && python3 -m pytest tests/test_meta_optimizer_role.py tests/test_new_role_checklist_doc.py -q`
- [x] Step 4: commit `docs: complete meta-optimizer scenario, cli docs and checklist`

## Paket 2f — Nachweis (Gate-Spur B): Baseline und `compact`-Eval (AC-02, AC-25, AC-86)

> **Start nur nach Gate:** Diese Tasks werden ohne erfülltes Gate nicht begonnen (keine Vorbereitung von Läufen „auf Vorrat“). Vor jedem Lauf: Kostenschätzung anzeigen (`eval_gate.format_estimate`), ausdrückliche Nutzerfreigabe einholen; Ablehnung ⇒ `SKIPPED-BY-USER`-Record (Muster Task 2.00) und Gate bleibt „nicht belegt“.

> **Status 2026-10-20:** SKIPPED-BY-USER — Claude in der Laufumgebung nicht authentifiziert (nur 1 Modellklasse, AC-02 verlangt ≥ 2). Kein Lauf gestartet; Skip-Record `tests/routing-llm-eval/roles/runs/2026-10-20-qg1-phase2.json`. Steps bleiben ungetickt.

### Task 33: 2f.1 — Role-Routing-Baseline (`full`) mit ≥ 2 Modellklassen nachversuchen
**Agent:** test-executor · **Issue:** #977 · **PR:** 2f-I · **AC:** AC-02 (inkl. Reproduktionslauf), AC-62 (Baseline-Teil) · **Gate:** Nutzerfreigabe (Kostenschätzung zuerst)
**Depends on:** —
**Falle:** ≥ 2 Modellklassen × ≥ 3 Läufe je Metrik, σ je Metrik, Korpus-Hash, Modell-IDs und Parameter in der Baseline-Datei; **AC-02 umfasst den Reproduktionslauf:** ein zweiter Lauf mit identischer Config reproduziert jede Metrik innerhalb der dokumentierten Streuung (σ) — als `repro`-Abschnitt der Baseline-Datei nachweisen (gleiche Config, Modell-IDs, Parameter); Abbruch ohne Freigabe ⇒ `SKIPPED-BY-USER` (neuer Record, Task 2.00 aktualisieren).
**Files:**
- Create: `tests/routing-llm-eval/roles/baseline/<date>-<model>-full.json`
- Modify: `tests/test_eval_baseline_schema.py`
**Interfaces:** Produces Baseline-Dateien nach IC-13-Namensschema (inkl. Kollisions-Accuracy, Sprach-Delta und `repro`-Abschnitt), Gate-Status `evidenced`; Consumes `eval_gate.estimate_cost`, `eval_gate.run_with_approval`, `gen_role_routing_eval_catalog.py`, `tests/routing-llm-eval/roles/catalog.*`
- [ ] Step 1: Test schreiben (fail): Baseline-Schema (Klassen, ≥ 3 Läufe, σ, Korpus-Hash, Modell-IDs, `repro`-Abschnitt) fehlt
- [ ] Step 2: Läufe nach Freigabe ausführen (Baseline + Reproduktionslauf; oder Skip-Record aktualisieren)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_eval_baseline_schema.py tests/test_eval_gate.py -q`
- [ ] Step 4: commit `chore: record full profile routing baseline`

### Task 34: 2f.2 — `compact`-Eval gegen die Baseline fahren (AC-25)
**Agent:** test-executor · **Issue:** #977 · **PR:** 2f-II · **AC:** AC-25 · **Gate:** AC-02 belegt (2f.1) **und** 2a–2c gemergt **oder** konservative Variante: Kandidaten-Build aus dem 2b.1-Branch (offene Nutzerfrage 1 — der Eval rendert echte `compact`-Artefakte; kein Zirkularitätsproblem)
**Depends on:** 33
**Falle:** je Metrik Richtung und Toleranz aus IC-36 (`τ = max(1 pp, k·σ)`, k = 2), gepaarte Fälle nach Möglichkeit; Batch je PR; Ergebnisdateien versioniert; Verschlechterung ⇒ Gate „nicht bestanden“, keine Merge-Freigabe für „as verified“.
**Files:**
- Create: `tests/routing-llm-eval/roles/baseline/<date>-<model>-compact.json` (bzw. Ergebnisdateien)
- Modify: `tests/test_eval_baseline_schema.py`
**Interfaces:** Produces `evaluate_gate(baseline, candidate)`-Ergebnis (`passed|failed|not-evidenced`) je Modellklasse/Metrik, versionierte Ergebnisdateien; Consumes `eval_gate.evaluate_gate`, `eval_gate.METRIC_DIRECTIONS`, 2b-/2c-Artefakte
- [ ] Step 1: Test schreiben (fail): Ergebnis-/Gate-Datei fehlt oder Schema unvollständig
- [ ] Step 2: Lauf nach Freigabe ausführen (oder Skip-Record)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_eval_gate.py tests/test_eval_baseline_schema.py -q`
- [ ] Step 4: commit `chore: evaluate compact profile routing against baseline`

### Task 35: 2f.3 — Verifikationsanspruch und INFO-Absenz nach belegtem AC-25 herstellen
**Agent:** senior-developer · **Issue:** #977 · **PR:** 2f-III · **AC:** AC-25 (Abschluss), AC-86 (Profil-Teil), AC-26 (Claim) · **Gate:** AC-25 belegt (2f.2)
**Depends on:** 34
**Falle:** nur bei belegtem AC-25 verschwindet die INFO `context-profile.unverified`; kein Default wechselt auf `compact` (Test bleibt bestehen); Doku/CHANGELOG dürfen erst jetzt Verifikation nennen; `compact` bleibt Opt-in.
**Files:**
- Modify: `scripts/lib/context_profile_gate.py` (Evidenz-Auswertung)
- Modify: `docs/api/cli-reference.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `tests/test_context_profile_gate.py`
- Modify: `tests/test_context_profile_docs.py`
**Interfaces:** Produces Zustandswechsel `not-evidenced → evidenced` (keine INFO bei `compact`), Doku-Claim; Consumes `eval_gate.evaluate_gate`, Ergebnisdateien 2f.2
- [ ] Step 1: Test schreiben (fail): Fixture mit belegtem AC-25 ⇒ INFO darf nicht erscheinen (heute erscheint sie)
- [ ] Step 2: implementieren (nur Evidenz-Auswertung + Doku)
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_context_profile_gate.py tests/test_context_profile_docs.py -q`
- [ ] Step 4: commit `feat: recognize evidenced compact eval in profile gate`

## Self-Review

Ergebnis (geprüft gegen Spec §8, §9, §9.1, IC-01…IC-12, IC-24…IC-28, IC-34…IC-36):

- Jeder Task hat genau eine Rolle (`**Agent:**`), benannte Tests, ein nicht-leeres `Files:`- und `Interfaces:`-Feld (Produces/Consumes mit Datei + Symbol); keine unerledigten Arbeitsmarker, keine leeren Felder. Konsumierte, bereits vorhandene ICs ohne eigenen Task: IC-09 (Capability-Keys), IC-10 (Check-Signatur/Checks in `consistency/context_budget.py`/`active_set_refs.py`), IC-12 (Anker-Registry), IC-17 (ActiveSet), IC-18 Nr. 2 (Pipeline-Filter, #992) — Phase-2-Tasks konsumieren sie nur.
- **Maschinenlesbarkeit (B-F-01-Nachweis, am 2026-10-18 gegen diese Datei ausgeführt):** `spec_plan._parse_plan_tasks` ⇒ **35 Tasks, 35 mit `Files:`-Ownership, 32 mit `Depends on:`-Kanten** (ohne Vorbedingung: Task 1/2.00, 20/2d.1, 33/2f.1); `validate_plan(FanoutPlan(kind="sequential", max_parallel=35))` ⇒ **0 Fehler** (keine Deadlocks/Zyklen/Over-Commitment); `check_plan_file_overlap` ⇒ `{"safe": 2, "conflict": 195}` — die 195 Meldungen sind Import-/Doku-Kopplungen über sequenzielle Kanten (bekanntes #266-Verhalten; `_check_plan_graph` prüft File-Overlap für sequenzielle Pläne bewusst nicht, #848), **innerhalb der vier `parallel_group`s: 0 Konflikte** (2a-g1: safe=2, 2a-g2 inkl. 2a.6: safe=3, 2b-g1: safe=2, 2c-g1: safe=2; je `conflict=0` — pairwise disjunkt laut deklariertem `Files:`).
- Jeder AC der Phase 2 hat ≥ 1 Task (Tabelle unten; am 2026-10-18 aus den `**AC:**`-Feldern der Task-Header regeneriert, inkl. 2a.7/AC-29, 2a.8/AC-86, 2a.2/AC-01, 2d.3/AC-57 und der AC-91/AC-98-Angleichung); AC-02/AC-25 sind explizit als Gate-Tasks (2f) ausgewiesen und heute nicht startbar.
- Gate-Spuren: Spur A (ohne AC-02 auslieferbar, Opt-in, kein Verifikationsanspruch) = 2.00, 2a.\*, 2b.\*, 2c.\*, 2d.\*, 2e.\*; Spur B (belegtes AC-02/AC-25 nötig) = 2f.1–2f.3. Der `context-profile.unverified`-INFO (2a.5) ist Teil von Spur A und verschwindet erst in 2f.3; IC-04 (2b.1) wird als Opt-in gemergt, nicht „as verified“ (offene Nutzerfrage 1; konservative Variante nutzt den Kandidaten-Build des 2b.1-Branch-Stacks in 2f.2 und 2c.3).
- Byte-Stabilität: kein Task der Spur A ändert den Default-/`full`-Render ohne Rebaseline-Eintrag in der AC-23-Ausnahmeliste (2b.2/2e.2/2e.4/2e.5 mit Minor-Bump, Golden + `hashes.json` + Rebaseline-Log); `compact` ist überall hinter `CONTEXT_PROFILE_COMPACT` bzw. den Key `context-profile` gegated.
- Parallel-Gruppen ownership-disjunkt (Prüfung `check_plan_file_overlap`, `scripts/lib/orchestration.py:320`, auf diesem Plan): 2a-g1 (2a.1 `context_profile.py`/`test_context_profile.py` ↔ 2a.2 Schema/Example/`test_context_profile_schema.py`), 2a-g2 (2a.4 `context_budget.py`/`test_context_budget_checks.py` ∥ 2a.5 `context_profile_gate.py`/`sync_pipeline.py`/`test_context_profile_gate.py` ∥ 2a.6 `context.py`/`context_profile.py`/`test_context_profile_shared_file.py`), 2b-g1 (2b.1 `agents.py`/`delegation_table.py`/`agent_sync.py` ↔ 2b.2 `orchestrator.md`/`standalone.py`/`test_orchestrator_compact_sections.py`), 2c-g1 (2c.1 `context-anchors.yaml`/`test_context_anchors.py` ↔ 2c.2 `context_report.py`/`cli_commands.py`/`test_context_budget*`) — keine Datei doppelt.
- `pipeline_stages.implement: 3` deckt die einzige `plan-driven`-Stage ab.
- Bewusst ohne eigenen Task: IC-27 Phase-3-Teile (Boilerplate-De-Dup), `permission.task`-Trimming, `ultra`/IC-16 (Phase 3); AC-57-`relocate-*`-Umsetzung (nur Hinweis, ADR-18); **C4 (Bootstrap-Blöcke: nur aktive Provider, ZCode-Entfall/Gemini-Discovery „nach Verifikation“)** — die aktive-Provider-Bedingung ist Phase-1-Fix (IC-18), die verifikationsabhängigen Teile liegen außerhalb des Phase-2-Gates (Roadmap).
- Bewusste Abweichung (IC-04-„Single-Source“-Klausel zur §2-Pipeline-Tabelle): **C2-Vorrang** — §1/§2/§4/§5/§6/§7/§11 bleiben in `compact` verbatim, d. h. `PIPELINE_MATCH_TABLE` erhält in 2b.1 keinen Compact-Zweig; die IC-04-Klausel („die §2-Pipeline-Tabelle verweist darauf“) ist laut Spec „revidierbar per Eval“ und wird erst nach belegtem AC-25 (2f) per Spec-Revision eingeführt.
- Dokumentierte Abweichung (QG-11-Testdateiname): QG-11 nennt `tests/test_meta_optimizer.py`; dieser Plan splittet bewusst in `tests/test_meta_optimizer_{runner,applier,fanout,refill,inactive_scope,marks,credentials}.py` (600-Zeilen-Modulbudget, Task-Ownership); die QG-11-Prüfungen (a)–(n) sind vollständig auf die Splitdateien verteilt (u. a. (m) `rejected: not-applicable` in 2d.3, (n) `version-mismatch` in 2d.3).
- Bewusste Abweichung von der Spec-Zeile „Reihenfolge-Regel: Phase 2 beginnt erst, wenn AC-02 erfüllt ist“: umgesetzt nach der ersetzenden Rev.-3-Regel (§9, W-10) — Optimizer unabhängig, Profil Opt-in ohne Verifikationsanspruch.
- Offene Punkte für den Nutzer: siehe unten.

| AC | Task | Test |
|---|---|---|
| AC-01, AC-23, AC-35 (Byte-Stabilität, Ausnahmeliste; AC-35 sinngemäß) | Global Constraints; feldführend: 2a.2 (AC-01), 2a.3/2b.2/2e.2/2e.5 (AC-23) | `tests/test_ac01_render_identity.py`, `tests/test_template_slimming_equivalence.py`, `tests/fixtures/compact-golden/` (QG-5) |
| AC-02 (inkl. Reproduktionslauf) | 2.00, 2f.1 | `tests/test_eval_baseline_schema.py` |
| AC-06 (compact) | 2c.1 | `tests/test_context_anchors.py` |
| AC-11 (Δ; Phase-1-AC auf `compact` angewandt) | 2c.2 | `tests/test_context_report.py` |
| AC-24 | 2b.2–2b.6, 2c.1, 2c.3 | `tests/test_orchestrator_compact_sections.py`, `tests/test_gate_card_compact.py`, `tests/test_compact_rule_channels.py`, `tests/test_compact_matrix.py` |
| AC-25 | 2f.2, 2f.3 | `tests/test_eval_gate.py`, Ergebnisdateien `tests/routing-llm-eval/roles/` |
| AC-26 | 2b.3, 2c.2, 2c.4, 2f.3 | `tests/test_context_budgets.py`, `tests/test_context_report.py` |
| AC-27 | 2b.1, 2c.3 | `tests/test_compact_matrix.py`, `tests/test_provider_matrix_sync.py` |
| AC-28 | 2c.3 | `tests/test_compact_matrix.py` (Idempotenz-Check) |
| AC-29 | 2a.1, 2a.3, 2a.7 | `tests/test_context_profile.py`, `tests/test_context_profile_docs.py` |
| AC-30 | 2a.1, 2a.2, 2a.3, 2a.6 | `tests/test_context_profile.py`, `tests/test_context_profile_schema.py`, `tests/test_context_profile_shared_file.py` |
| AC-31 | 2b.1 | `tests/test_routing_lines_compact.py` |
| AC-32 | 2a.4, 2b.4 | `tests/test_context_budget_checks.py`, `tests/test_compact_rule_channels.py` |
| AC-54 | 2d.2 | `tests/test_meta_optimizer_runner.py` |
| AC-55 (inkl. L0-Vergleichsmenge `.meta-config/*.json`) | 2d.2, 2d.3 | `tests/test_meta_optimizer_runner.py`, `tests/test_meta_optimizer_applier.py` |
| AC-56 | 2d.3 | `tests/test_meta_optimizer_applier.py` |
| AC-57 (inkl. `--include-semantic`-Gating: 2d.2; `rejected: not-applicable`: 2d.3) | 2d.2, 2d.3 | `tests/test_meta_optimizer_runner.py`, `tests/test_meta_optimizer_applier.py` |
| AC-58 | 2d.2 | `tests/test_meta_optimizer_fanout.py` |
| AC-59 | 2e.1–2e.4, 2e.6 | `tests/test_meta_optimizer_role.py`, `tests/test_role_addressability_coverage.py`, Szenario 78 |
| AC-62 (Baseline) | 2.00, 2f.1 | `tests/test_eval_baseline_schema.py` |
| AC-69 (Zeilenformat) | 2b.1 | `tests/test_routing_lines_compact.py` |
| AC-75 (Optimizer) | 2d.2, 2d.3 | `tests/test_meta_optimizer_runner.py`, `tests/test_meta_optimizer_applier.py`, `tests/test_tmp_sink_output_dirs.py` |
| AC-79 | 2e.1, 2e.6 | `tests/test_meta_optimizer_role.py`, Szenario 78 |
| AC-80 | 2d.3 | `tests/test_meta_optimizer_applier.py` |
| AC-81 | 2d.1, 2d.6 | `tests/test_runtime_config_readers.py`, `tests/test_meta_optimizer_marks.py` |
| AC-82 | 2d.4 | `tests/test_meta_optimizer_refill.py` |
| AC-83 | 2d.5 | `tests/test_meta_optimizer_inactive_scope.py` |
| AC-86 (Profil) | 2.00, 2a.5, 2a.7, 2a.8, 2b.6, 2c.4, 2f.3 | `tests/test_context_profile_gate.py`, `tests/test_context_profile_docs.py`, `tests/test_context_profile_admin.py` |
| AC-89 | 2d.1, 2d.2, 2d.3, 2d.7 | `tests/test_runtime_config_readers.py`, `tests/test_meta_optimizer_runner.py`, `tests/test_meta_optimizer_applier.py`, `tests/test_meta_optimizer_credentials.py` |
| AC-90 | 2d.3, 2e.4, 2e.5 | `tests/test_meta_optimizer_applier.py`, `tests/test_meta_optimizer_role.py`, Szenario 78 |
| AC-91 (inkl. `version-mismatch`/`rejected: not-applicable`: 2d.3) | 2d.2, 2d.3, 2e.1, 2e.4, 2e.6 | `tests/test_meta_optimizer_runner.py`, `tests/test_meta_optimizer_applier.py`, `tests/test_meta_optimizer_role.py`, Szenario 78 |
| AC-94 (Optimizer) | 2d.2, 2d.3 | `tests/test_meta_optimizer_runner.py`, `tests/test_meta_optimizer_applier.py` (tempfile-Monkeypatch), AC-94-Guard |
| AC-98 (Optimizer; Spec-Scope `--context-report`/`--optimize-config`) | 2d.2 | `tests/test_meta_optimizer_runner.py` |
| AC-36/AC-61 | Global Constraints, alle Tasks | `tests/test_provider_agnostic_dispatch.py` |

> IC-09 (Capability-Keys) und IC-10 (Check-Signatur) sind Phase-0/1-Bestand; die Phase-2-Tasks konsumieren sie, erzeugen sie nicht neu (siehe erster Self-Review-Punkt).

## Offene Nutzerfragen

1. **IC-04-Merge (2b.1):** Plan-Default ist der Opt-in-Merge hinter `context-profile: compact` mit `context-profile.unverified`-Hinweis (Rev.-3-Regel). Konservative Alternative: 2b.1 fertigstellen, aber erst nach belegtem AC-25 (2f.2) mergen; 2b.2–2c laufen dann als Stacked-PR-Kette auf dem 2b.1-Branch (Rebase nach jedem Basis-Merge, s. Ausführungsmodell „Konservative Variante“). Auflösung der Reihenfolge: der 2f.2-Lauf und die 2c.3-Matrix rendern gegen den **Kandidaten-Build des Branch-Stack-Heads** (Branch-Stand statt Merge) — damit weder zirkulär noch blockierend für 2a/2d/2e. Welche Variante gilt?
   **Entscheidung (2026-10-18):** 2b.1 wird als **Opt-in** gemergt (nicht „as verified“); der Verifikationsanspruch („as verified“) entsteht erst nach 2f.3. Die konservative Stacked-PR-Variante wird verworfen; 2b.2–2c laufen regulär nach Paket-Merge-Reihenfolge.
2. **AC-02/AC-25-Nachweis:** Soll ein späterer Baseline-Versuch (2f.1) mit ≥ 2 Modellklassen und ≥ 3 Läufen je Metrik plus Reproduktionslauf (AC-02) eingeplant werden (mit Kostenschätzung und separater Nutzerfreigabe)? Falls ja: Zielmodellklassen und grober Zeitpunkt (z. B. nach Paket 2c)?
   **Entscheidung (2026-10-18):** Ein späterer Baseline-Versuch mit **≥ 2 Modellklassen** bleibt als Gate 2f.1 vorgesehen, wird aber heute **nicht** gestartet (Status: SKIPPED); er braucht eine eigene, separate Nutzerfreigabe inkl. vorab angezeigter Kostenschätzung.
3. **Paket-Issues:** Alle Tasks referenzieren Tracking #977. Sollen je Paket eigene Issues (#977-Ableger, Muster Phase 1: #963…#970) angelegt werden, oder bleibt #977 das alleinige Issue?
   **Entscheidung (2026-10-18):** Keine separaten Paket-Issues; **#977 bleibt das Dach**. Ableger-Issues werden nur auf ausdrücklichen Zuruf angelegt.
4. **Selbst-Hosting (IC-28 Nr. 9):** Soll `meta-optimizer` (und nachträglich `meta-doctor`) in `.meta-config/project.yaml roles:` aufgenommen werden (optionaler Checklistenpunkt, ändert `generated-file-hashes.json`), oder bleibt self-hosting unverändert?
   **Entscheidung (2026-10-18):** `meta-optimizer` wird **nicht** in das Self-Hosting-`roles:` aufgenommen (nur für Fixtures/Tests); self-hosting bleibt unverändert.
5. **Unverified-Doku-Tonalität:** Der Plan hält `compact` strikt neutral („Opt-in, unverifiziert“). Soll README/`cli-reference` zusätzlich den Grund (fehlende Baseline/AC-02) nennen und den geplanten Nachweis (2f) referenzieren, oder nur den Status ohne Begründung?
   **Entscheidung (2026-10-18):** README/`cli-reference` nennen den Status **mit Begründung** (fehlende Baseline/AC-02, geplanter Nachweis in Paket 2f); keine Verifikationsbehauptung (IC-36 Nr. 3).
