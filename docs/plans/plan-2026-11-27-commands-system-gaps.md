# Commands-System Restlücken Implementation Plan
> Status: geplant

**Goal:** REQ-CMD-01..10, Code, Doku und Tests konsistent machen (Phase-2-Exit).
**Architecture:** Hard-Error-Guard in `sync_commands_for_provider` (IC-3), `.gitkeep`-Layer-Marker, neue Test-Dateien, REQ-/Doku-Angleich (ADR-1=B, ADR-2=B), Szenario 107. Keine neue öffentliche Schnittstelle.
**Tech Stack:** Python (Stdlib + PyYAML), pytest, bash-Szenarien, Markdown/YAML.
**Spec:** docs/specs/2026-11-27-commands-system-gaps-spec.md (spec-id: SPEC-COMMANDS-SYSTEM-GAPS-2026-11-27, Status APPROVED)

## Global Constraints
- Testbefehl-Schema: `python3 -m pytest <Dateien> --basetemp=/var/tmp/hermes/pytest-agent-meta/phase2` — keine parallelen Läufe (gemeinsame basetemp).
- Strikt sequenziell; keine Provider-Namenslogik im Code/Test-Annahmen (Config iterieren).
- `CLAUDE.md`/`AGENTS.md` nie von Hand editieren — nur Template + `python3 scripts/sync.py`.
- Commits: Conventional, Englisch, <=72 Zeichen, Imperativ; Branch `feat/phase-2-commands-system`; Commit-Ausführung durch Caller (secret scan vor Commit).
- Knowledge-Bundle-Kopien (`knowledge/wiki/topics/commands.md`, `knowledge/sources/...`) NICHT in diesem Plan editieren (R-3).
- Kein Worktree-Isolation; Schreiben nur im Projektroot/`.tmp/`.

## Risiken
- R-3: Knowledge-Bundle-Kopien tragen weiter den alten Doku-Widerspruch bis zum separaten Ingest (Follow-up, `knowledge-ingestor`); Doku-Konsistenztest darf `knowledge/` NICHT prüfen.
- R-4: Szenario-ID 107 — aktuell frei (höchste vorhandene 106; Configs/Asserts geprüft); vor Task 9 erneut gegen `git fetch`/offene Branches prüfen.
- R-2: Leer-Ordner mit `.gitkeep` — `--validate` in Task 13 muss grün sein.
- R-5: Existenz `documenter`-Agent (REQ-07) nicht geprüft; Szenario 107 setzt ihn aktiv voraus.
- IC-3 Hard-Error: Real-Config hat stets 1-generic-Quellen (AC-5.4), Szenario 71 als Regression.

## File Structure
- Create: docs/plans/plan-2026-11-27-commands-system-gaps.md (dieser Plan, Task 0)
- Modify: scripts/lib/commands.py — Guard `if not sources: return` entfällt (IC-3)
- Create: commands/0-external/.gitkeep, commands/2-platform/.gitkeep — Layer-Marker (IC-4)
- Create: tests/test_commands_hard_error.py (IC-6), tests/test_commands_layers.py (IC-5), tests/test_commands_create_command.py (IC-7), tests/test_commands_gate_consistency.py (IC-8), tests/test_commands_continue_stale.py (IC-9), tests/test_commands_docs_consistency.py (OF-4)
- Modify: tests/test_commands_requires_roles.py — Assertion "andere Felder unverändert" (AC-2.2)
- Modify: docs/REQUIREMENTS.md — REQ-CMD-03, REQ-CMD-06 (IC-1, IC-2)
- Create: tests/scenarios/configs/107-commands-system.project.yaml, tests/scenarios/asserts/107-commands-system.sh; Modify: tests/scenarios/registry.md
- Modify: templates/configs/CLAUDE.project-template.md, docs/guides/features/commands.md, docs/guides/setup/instantiate-project.md
- Generated via Sync: CLAUDE.md, AGENTS.md (nie von Hand)

---
pipeline_stages:
  implement: 3
---

### Task 0: Spec + Plan committen
**Rolle:** git/orchestrator (Commit durch Caller)
**Files:** Create/Add: docs/specs/2026-11-27-commands-system-gaps-spec.md, docs/plans/plan-2026-11-27-commands-system-gaps.md
**Interfaces:** Produces: versionierte Spec + Plan. Consumes: —
**AC:** beide Dateien getrackt, Spec `Status: APPROVED`.
- [ ] Step 1: beide Dateien stagen
- [ ] Step 2: commit `docs: add commands-system gaps spec and plan`
- Testbefehl: entfällt (Doku)

### Task 1: REQ-10 Hard-Error (Tests zuerst, dann Code)
**Rolle:** developer
**Files:** Create tests/test_commands_hard_error.py; Modify scripts/lib/commands.py (Z. 244-256)
**Interfaces:** Produces: `sync_commands_for_provider` wirft `SyncError` ("commands_dir") bei commands-Support + fehlendem/leerem `commands_dir` unabhängig von Quellenmenge. Consumes: `provider_commands_supported` (providers.py:850), `SyncLog`, `SyncError`.
**AC:** AC-5.1, AC-5.2, AC-5.3, AC-5.4 (Regression via Szenario 71 in Task 13)
- [ ] Step 1: Test schreiben (5.1 leere Quellen -> SyncError; 5.2 nichtleere Quellen -> SyncError; 5.3 `commands: false` -> genau 1 INFO "not supported", keine Dateien); 5.1 muss fehlschlagen
- [ ] Step 2: Guard `if not sources: return` entfernen, Fehlerprüfung vor Quellenprüfung
- [ ] Step 3: Test (pass)
- Testbefehl: `python3 -m pytest tests/test_commands_hard_error.py --basetemp=/var/tmp/hermes/pytest-agent-meta/phase2`
- [ ] Step 4: commit `fix: raise SyncError for commands without commands_dir`

### Task 2: REQ-01 Layer-Marker und Layer-Tests
**Rolle:** developer
**Files:** Create commands/0-external/.gitkeep, commands/2-platform/.gitkeep, tests/test_commands_layers.py
**Interfaces:** Produces: Layer-Ordner + Tests. Consumes: `collect_command_sources(agent_meta_root: Path, platforms: list[str]) -> list[tuple[Path, str]]`.
**AC:** AC-4.1 (real_root, `[]`: kein `.gitkeep`-Eintrag; Ordner existieren), AC-4.2 (Priorität 2>1>0, Fallbacks), AC-4.3 (Plattform q ausgeschlossen, Präfix-Strip `p-deploy.md`->`deploy.md`)
- [ ] Step 1: Test schreiben (Existenztest 4.1 schlägt fehl)
- [ ] Step 2: leere `.gitkeep` anlegen (keine README.md)
- [ ] Step 3: Test (pass)
- Testbefehl: `python3 -m pytest tests/test_commands_layers.py --basetemp=/var/tmp/hermes/pytest-agent-meta/phase2`
- [ ] Step 4: commit `test: cover commands layers and add layer markers`

### Task 3: REQ-08 create_command
**Rolle:** tester
**Files:** Create tests/test_commands_create_command.py (kein Code-Change erwartet; bei Fehlschlag Befund melden)
**Interfaces:** Consumes: `create_command(project_root, name, log, dry_run)` (commands.py:334), normaler Claude-Sync. Produces: Tests.
**AC:** AC-8.1 (existierende Datei byte-identisch, SKIP-Log), AC-8.2 (Anlage, `foo`/`foo.md`->`foo.md`, nicht im Managed-Index), AC-8.3 (Folge-Sync löscht Datei nicht), AC-8.4 (dry_run -> keine Datei)
- [ ] Step 1: Tests schreiben
- [ ] Step 2: laufen lassen; bei Rot Defekt an developer melden (Code-Fix nur dann)
- [ ] Step 3: Test (pass)
- Testbefehl: `python3 -m pytest tests/test_commands_create_command.py --basetemp=/var/tmp/hermes/pytest-agent-meta/phase2`
- [ ] Step 4: commit `test: cover create-command skip, suffix and dry-run`

### Task 4: Gate-Konsistenz (Lücke 7)
**Rolle:** tester
**Files:** Create tests/test_commands_gate_consistency.py
**Interfaces:** Consumes: `config/ai-providers.yaml:has_commands`, `config/provider-capabilities.yaml:commands`, `load_provider_capabilities`, `provider_commands_supported`, `COMMAND_FORMAT_TRANSFORMS`. Produces: Konsistenztest ohne Provider-Namen (iteriert Config).
**AC:** AC-7.1 (Fehlermeldung nennt Provider + beide Werte), AC-7.2 (`has_commands: true` => `commands_dir` nicht leer, `commands_format` in Transforms)
- [ ] Step 1: Test schreiben
- [ ] Step 2: bei Rot Config-Drift melden/beheben (Config-Fix = developer)
- [ ] Step 3: Test (pass)
- Testbefehl: `python3 -m pytest tests/test_commands_gate_consistency.py --basetemp=/var/tmp/hermes/pytest-agent-meta/phase2`
- [ ] Step 4: commit `test: assert commands gate consistency across provider configs`

### Task 5: Continue-Stale (AC-1.2, AC-1.3) und requires_roles-Feldtest (AC-2.2)
**Rolle:** tester
**Files:** Create tests/test_commands_continue_stale.py; Modify tests/test_commands_requires_roles.py
**Interfaces:** Consumes: Continue-Provider-Konfig (`commands_managed_index: .agent-meta-commands-managed`), `cleanup_stale_managed_files`, `sync_prompts_for_continue`-Index `.agent-meta-managed`. Produces: Tests.
**AC:** AC-1.2 (zwei Syncs; beide Indizes disjunkt; Command-Entfernung löscht kein Rollen-Prompt), AC-1.3 (entferntes Command -> Datei gelöscht, Index aktualisiert), AC-2.2 (`description`, `allowed-tools`, `argument-hint` byte-identisch, `requires_roles` fehlt)
- [ ] Step 1: Tests schreiben
- [ ] Step 2: bei Rot Befund an developer
- [ ] Step 3: Test (pass)
- Testbefehl: `python3 -m pytest tests/test_commands_continue_stale.py tests/test_commands_requires_roles.py --basetemp=/var/tmp/hermes/pytest-agent-meta/phase2`
- [ ] Step 4: commit `test: cover continue commands stale cleanup and index split`

### Task 6: REQ-Texte (REQ-CMD-03 / REQ-CMD-06)
**Rolle:** requirements
**Files:** Modify docs/REQUIREMENTS.md (Z. ~13-22)
**Interfaces:** Produces: IC-1 (Index `.continue/prompts/.agent-meta-commands-managed`, Begründung eigener Index neben Rollen-Prompt-Index), IC-2 (REQ-CMD-06 Ausnahme `requires_roles` + `{{VAR}}`-Substitution).
**AC:** AC-1.1 (REQ-CMD-03 nennt `.agent-meta-commands-managed`), AC-2.1 (REQ-CMD-06 enthält Ausnahmeklausel). Prüfung: `grep -n "agent-meta-commands-managed\|requires_roles" docs/REQUIREMENTS.md` zeigt beide.
- [ ] Step 1: Doku-Konsistenztest-Erwartung notieren (wird in Task 8 gebündelt)
- [ ] Step 2: Texte anpassen
- [ ] Step 3: Grep-Prüfung
- [ ] Step 4: commit `docs: align REQ-CMD-03 and REQ-CMD-06 with generator behavior`

### Task 7: Szenario 107
**Rolle:** tester
**Files:** Create tests/scenarios/configs/107-commands-system.project.yaml, tests/scenarios/asserts/107-commands-system.sh; Modify tests/scenarios/registry.md (Katalogzeile)
**Interfaces:** Produces: Szenario 107. Consumes: Assert-Contract wie `07-new-providers.sh` (cwd = Temp-Projekt, `REPO_ROOT` als `$1`/Env, `fail()`-Muster), `tests/scenarios/run.sh`.
**AC:** AC-6.1 (`tests/scenarios/run.sh 107` PASS: Claude+Continue+Opencode markdown, Gemini toml, Codex/KimiCode ohne Commands-Dir, `doc-now.md` ohne `requires_roles`, `.continue/prompts/.agent-meta-commands-managed` vorhanden, zweiter Sync idempotent; AC-3.1 CLAUDE.md/AGENTS.md-Grep erst in Task 12), AC-6.2 (Katalogzeile mit ID/Providern/Feature; dev- und release-Profil PASS)
- [ ] Step 1: ID-Kollision prüfen (`Glob tests/scenarios/*/107-*`, registry.md, offene Branches); bei Kollision nächste freie ID und Plan anpassen
- [ ] Step 2: Config + Assert + Registry anlegen (Assert zuerst, Lauf rot)
- [ ] Step 3: `tests/scenarios/run.sh 107` (dev und release) PASS
- [ ] Step 4: commit `test: add scenario 107 for commands system`
- Testbefehl: `bash tests/scenarios/run.sh 107` (kein pytest)

### Task 8: Doku-Konsistenztest (OF-4, rot)
**Rolle:** tester
**Files:** Create tests/test_commands_docs_consistency.py
**Interfaces:** Consumes: `docs/guides/features/commands.md`, `docs/guides/setup/instantiate-project.md`, `commands/1-generic/*.md`, `docs/REQUIREMENTS.md`. Produces: Tests, die Guides prüfen (nicht `knowledge/`).
**AC:** AC-1.1 (konsistenter Continue-Index-Name in Guide + REQ), AC-3.2 (jedes `.agent-meta-managed` im Continue-Kontext nennt Ausnahme `.agent-meta-commands-managed`), AC-3.3 (`3-project/commands` kommt in Doku nicht vor), AC-3.4 (Guide-Tabelle deckt alle `commands/1-generic/*.md` ab)
- [ ] Step 1: Tests schreiben; erwartet rot für 3.2/3.3/3.4
- [ ] Step 2: (Fix in Task 10/11)
- [ ] Step 3: Test läuft rot (Beleg), kein Commit bis Task 11 grün — Task 8 wird mit Task 11 gemeinsam committet
- Testbefehl: `python3 -m pytest tests/test_commands_docs_consistency.py --basetemp=/var/tmp/hermes/pytest-agent-meta/phase2`

### Task 9: Template CLAUDE.project-template.md (AC-3.1)
**Rolle:** documenter
**Files:** Modify templates/configs/CLAUDE.project-template.md
**Interfaces:** Produces: Commands-Abschnitt (Struktur `commands/0-external|1-generic|2-platform`, Sync-Verhalten-Tabelle je `commands_dir`). Consumes: Spec IC-11, `config/ai-providers.yaml`.
**AC:** AC-3.1 Template enthält Abschnitt; Grep `commands/2-platform` im Template trifft. CLAUDE.md/AGENTS.md erst via Sync in Task 13.
- [ ] Step 1: Doku-Test ergänzen falls Template-Check gewünscht (Task 8 erweitern)
- [ ] Step 2: Abschnitt schreiben
- [ ] Step 3: Grep-Prüfung
- [ ] Step 4: commit `docs: add commands section to CLAUDE project template`

### Task 10: Guide commands.md
**Rolle:** documenter
**Files:** Modify docs/guides/features/commands.md (Z. 15, 35, 69, 70, 143, 181-192, 222-223)
**Interfaces:** Produces: widerspruchsfreier Guide; Command-Tabelle mit allen 1-generic-Commands (24).
**AC:** AC-3.2, AC-3.4 (Test aus Task 8 für commands.md grün)
- [ ] Step 1: Test Task 8 rot bestätigen
- [ ] Step 2: Guide anpassen
- [ ] Step 3: `python3 -m pytest tests/test_commands_docs_consistency.py --basetemp=/var/tmp/hermes/pytest-agent-meta/phase2` (Teil grün)
- [ ] Step 4: commit nach Task 11 (gemeinsam)

### Task 11: instantiate-project.md + Doku-Test grün
**Rolle:** documenter
**Files:** Modify docs/guides/setup/instantiate-project.md (Z. 67); Commit-Umfang: tests/test_commands_docs_consistency.py, docs/guides/features/commands.md, docs/guides/setup/instantiate-project.md
**Interfaces:** Produces: Verweis `.claude/commands/` statt `.claude/3-project/commands/`.
**AC:** AC-3.3; kompletter Doku-Test grün.
- [ ] Step 1: Doku anpassen
- [ ] Step 2: Test (pass)
- Testbefehl: `python3 -m pytest tests/test_commands_docs_consistency.py --basetemp=/var/tmp/hermes/pytest-agent-meta/phase2`
- [ ] Step 3: commit `docs: fix commands guide inconsistencies and add doc test`

### Task 12: Gesamtlauf Commands-Tests
**Rolle:** tester
**Files:** keine (nur Lauf)
**AC:** alle neuen/erweiterten Tests grün.
- [ ] Step 1: `python3 -m pytest tests/test_commands_hard_error.py tests/test_commands_layers.py tests/test_commands_create_command.py tests/test_commands_gate_consistency.py tests/test_commands_continue_stale.py tests/test_commands_requires_roles.py tests/test_commands_docs_consistency.py --basetemp=/var/tmp/hermes/pytest-agent-meta/phase2`
- [ ] Step 2: Fehler an developer; kein Commit

### Task 13: Sync/Validate + generierte CLAUDE.md/AGENTS.md
**Rolle:** developer
**Files:** Modify (generiert): CLAUDE.md, AGENTS.md ggf. weitere Sync-Outputs (Hashes/Baselines nur wenn Sync sie ändert — Baseline-Änderung melden, nicht blind akzeptieren)
**Interfaces:** Consumes: Template aus Task 9, `scripts/sync.py`.
**AC:** `python3 scripts/sync.py` rc 0; `python3 scripts/sync.py --validate` rc 0; CLAUDE.md und AGENTS.md enthalten Commands-Abschnitt (AC-3.1, Grep); `bash tests/scenarios/run.sh 71` und `107` PASS (AC-5.4); `git diff` zeigt keinen Handedit außerhalb Sync.
- [ ] Step 1: `python3 scripts/sync.py`
- [ ] Step 2: `python3 scripts/sync.py --validate`
- [ ] Step 3: Szenarien 71, 107 und Gesamtlauf aus Task 12
- [ ] Step 4: commit `chore: regenerate CLAUDE.md and AGENTS.md via sync`

## Self-Review
- AC-Abdeckung: 1.1 T6/T8; 1.2/1.3 T5; 2.1 T6; 2.2 T5; 2.3 entfällt (ADR-2=B); 3.1 T9/T13; 3.2/3.4 T8/T10; 3.3 T8/T11; 4.1-4.3 T2; 5.1-5.3 T1; 5.4 T13; 6.1/6.2 T7; 7.1/7.2 T4; 8.1-8.4 T3.
- IC-Abdeckung: IC-1/2 T6; IC-3 T1; IC-4/5 T2; IC-6 T1; IC-7 T3; IC-8 T4; IC-9 T5; IC-10 T7; IC-11 T9-T11.
- Je Task eine Rolle, Testbefehl und Dateiliste; keine parallelen Läufe, keine Dateiüberlappung (commands.md T10, instantiate-project.md T11, docs-Test T8->T11 sequenziell).
- Offen: T8/T10 Commit gebündelt in T11 (Test-rot-Zwischenstand soll nicht committet werden).
- Knowledge-Bundle-Kopien (R-3): bewusst außerhalb des Plans; Follow-up Ingest.
- Effort: Schätzung durch `effort-estimator` (Textverweis, nicht berechnet).
