# Admin-UI Setup-Modus Implementation Plan
> Status: geplant

**Goal:** REQ-ADM-01..03 umsetzen: Admin UI erkennt fehlende `project.yaml` (Setup-Zustand), bietet einen Wizard für Config-Anlage und Erst-Sync, und belegt 4xx plus sichtbare Fehleranzeige bei Read-only-Writes.
**Architecture:** `lib/setup.py` in pure Funktionen (`build_setup_config`, `validate_setup_answers`) aufteilen; CLI und Server teilen sie. `/api/mode` erhält `setup_required`. Neue create-only-Endpunkte `/api/setup/options|config|init-sync`; `SyncExecutor.init_run()` mit festen argv. UI-Wizard in `admin-ui.html`. ADM-03 ist Verifikations-/Härtungsarbeit (Backend liefert bereits 400).
**Tech Stack:** Python (Stdlib + PyYAML), pytest, HTML/JS (single file), Markdown/YAML.
**Spec:** docs/specs/2026-11-28-admin-setup-mode-spec.md (spec-id: SPEC-admin-setup-mode, Status APPROVED, User-Freigabe 2026-11-28)

## Global Constraints
- Strikt SEQUENTIELL T1 -> T6, keine `parallel_group`; T5 nie parallel zu T1-T4 (gleiche Dateien `admin-server.py`/`admin-ui.html`).
- Pro Task: Implementierung (developer) -> Review (`code-reviewer`) -> Findings behoben -> Commit durch `git`-Agent; erst dann nächster Task.
- Tests nur so: `TMPDIR=/var/tmp/hermes/pytest-agent-meta rtk bypass python3 -m pytest <Dateien> --basetemp=/var/tmp/hermes/pytest-agent-meta/phase3`. Keine parallelen pytest-Läufe (gemeinsame basetemp), kein `-n`/xdist, kein Gesamt-Lauf ohne Dateiangabe.
- Scratch/temporäre Artefakte nur in `.tmp/` (Repo-Containment).
- Playwright (optional, nur read-only): `browser_navigate`, `browser_snapshot`, `browser_take_screenshot`, `browser_click`. VERBOTEN: `browser_evaluate`, `browser_run_code_unsafe`, `browser_file_upload`, `browser_handle_dialog`. Kein Form-Submit gegen echte Wurzel; Smoke nur gegen temporären Root mit `--no-viz`.
- Keine Änderung an `viz-*.py`; kein neuer Auth-Mechanismus; CLI-Wizard bleibt erhalten.
- Setup-Endpunkte token-gated, Mutationen zusätzlich `_check_origin`; Zielpfad fest `<root>/.meta-config/project.yaml`, nie aus dem Body; keine Formulardaten in argv/Env.
- Fehlercode für Read-only-Writes bleibt 400 (OQ-4); `PROJECT_WRITABLE_SECTIONS`/`_assert_project_*` unverändert.
- Generierte Dateien (`CLAUDE.md`, `AGENTS.md`, `.claude/skills/*`) nie von Hand editieren, nur Quelle ändern und `python3 scripts/sync.py` laufen lassen.
- Commits: Conventional, Englisch, <=72 Zeichen, Imperativ; Branch `feat/phase-3-admin-setup-mode`; Secret-Scan vor Commit durch Caller.
- Kein Worktree-Isolation.

## Risiken
- R-1: Refactor `setup.py` kann `--setup` brechen -> AC-5 Golden-Test in T1.
- R-2: `--init` schreibt viele Dateien (Timeout 300 s) -> UI Busy-State in T4.
- R-3: Race zwischen zwei Setup-Requests -> atomares Schreiben (`O_EXCL`/Lock) plus 409 in T3.
- OQ-1: Bricht Server ohne `project.yaml` real ab? AC-1 in T2 verifiziert; bei Gegenbefund Ursache lokalisieren und Umfang vor T2-Abschluss mit Caller neu bewerten.

## Assumptions
- Server startet ohne `project.yaml` bereits tolerant (Code-Lektüre); falls AC-1 rot ist, ändert sich T2.
- Setup-Zustand gilt auch im super_admin-Modus (OQ-2).
- Zeilennummern der Spec sind Orientierung, vor Edit per Grep gegen aktuellen Stand prüfen.

## File Structure
- Modify: scripts/lib/setup.py — `build_setup_config`, `validate_setup_answers`, `run_setup_wizard` delegiert
- Modify: scripts/admin-server.py — `_route_get_mode`, `SyncExecutor` (Guard, `init_run`), neue Setup-Routen
- Modify: docs/ui/admin-ui.html — Setup-Wizard in `init()`, Fehleranzeige-Härtung
- Create: tests/test_setup_refactor_phase3.py (T1), tests/test_admin_setup_mode.py (T2, T3, T5 Backend-Teil), tests/test_admin_ui_setup_wizard.py (T4, T5 UI-Teil)
- Modify: rules/2-platform/agent-meta-admin-ui.md (Quelle des Skills `admin-ui`), docs/REQUIREMENTS.md, ggf. CHANGELOG.md
- Generated via Sync: .claude/skills/admin-ui/SKILL.md u.a. (nie von Hand)

---
pipeline_stages:
  implement: 3
---

## Umsetzungsstand (Ledger)
- [ ] T1 setup.py-Refactor (AC-5, AC-6) — implementiert / reviewt / committed
- [ ] T2 /api/mode setup_required + Sync-Guard (AC-1..3) — implementiert / reviewt / committed
- [ ] T3 /api/setup/* + init_run (AC-4, 7, 8, 9) — implementiert / reviewt / committed
- [ ] T4 UI-Wizard (AC-10) — implementiert / reviewt / committed
- [ ] T5 ADM-03 Tests + UI-Fehleranzeige (AC-11..13) — implementiert / reviewt / committed
- [ ] T6 Doku (Skill-Quelle, REQUIREMENTS, CHANGELOG) — implementiert / reviewt / committed

### Task 1: setup.py-Refactor
**Rolle:** developer (Review: code-reviewer)
**Depends on:** —
**Files:** Modify scripts/lib/setup.py; Create tests/test_setup_refactor_phase3.py
**Interfaces:**
- Produces: `build_setup_config(answers: dict, agent_meta_root: Path) -> dict` (Pflicht `name`, `prefix`, `providers`, `git_platform`; Defaults wie bisher; kein I/O); `validate_setup_answers(answers: dict, agent_meta_root: Path) -> list[str]` (leer = ok; nutzt `_validate_prefix`/`_validate_nonempty`, Provider gegen `load_providers_config`).
- Consumes: bestehende `_ask*`, `_validate_prefix`, `load_providers_config`, `_write_config`. `run_setup_wizard`-Signatur unverändert.
**AC:** AC-5 (identische Antworten -> identisches Config-Dict aus CLI-Wizard und `build_setup_config`; Golden-Vergleich mit gepatchtem `input()`), AC-6 Unit-Teil (ungültiger Prefix oder unbekannter Provider -> nichtleere Fehlerliste, gültig -> `[]`).
- [ ] Step 1: Vor Refactor Golden-Output des CLI-Wizards (gepatchte Eingaben, temporärer Root unter `.tmp/`) im Test festschreiben; AC-6-Unit-Tests schreiben (rot, Funktionen fehlen)
- [ ] Step 2: Config-Assembly (`:326-374`) in `build_setup_config`, Validierung in `validate_setup_answers` extrahieren; `run_setup_wizard` sammelt Antworten und delegiert
- [ ] Step 3: Test (pass)
- Testbefehl: `TMPDIR=/var/tmp/hermes/pytest-agent-meta rtk bypass python3 -m pytest tests/test_setup_refactor_phase3.py --basetemp=/var/tmp/hermes/pytest-agent-meta/phase3`
- [ ] Step 4: code-reviewer-Review, Findings beheben
- [ ] Step 5: Commit `refactor: extract pure setup config builders` (git-Agent)

### Task 2: /api/mode setup_required + SyncExecutor-Config-Guard
**Rolle:** developer (Review: code-reviewer)
**Depends on:** T1
**Files:** Modify scripts/admin-server.py (`_route_get_mode` ~:4315, `SyncExecutor.run/_run` ~:1690/:1761); Create tests/test_admin_setup_mode.py
**Interfaces:**
- Produces: `/api/mode` Feld `setup_required: bool` (wahr genau wenn `<root>/.meta-config/project.yaml` fehlt; berechnet, nicht persistiert; rückwärtskompatibel); `SyncExecutor`-Guard: fehlt Config -> kein Subprozess, Rückgabe `{success:false, output:"project.yaml missing", returncode:-1}`; `_route_post_sync_run` antwortet unverändert 200.
- Consumes: bestehendes `detect_mode`, `ConfigManager`, Muster aus `tests/test_admin_start_mode_896.py`.
**AC:** AC-1 (Server startet ohne `project.yaml` mit `--no-viz`, `/api/health` 200, `setup_required: true`; klärt OQ-1), AC-2 (mit `project.yaml` `setup_required: false`, übrige Felder unverändert), AC-3 (`POST /api/sync/run` ohne Config: kein Subprozess (Popen/run gemockt, nicht aufgerufen), `success:false`, kein Hängen).
- [ ] Step 1: Tests schreiben (temporärer Root ohne `agents/1-generic`); AC-1/AC-3 prüfen Ist-Verhalten, OQ-1-Ergebnis im Review-Report festhalten
- [ ] Step 2: `setup_required` in `_route_get_mode` ergänzen; Guard in `SyncExecutor`
- [ ] Step 3: Test (pass); bestehende `tests/test_admin_start_mode_896.py` mitlaufen lassen (Regression)
- Testbefehl: `TMPDIR=/var/tmp/hermes/pytest-agent-meta rtk bypass python3 -m pytest tests/test_admin_setup_mode.py tests/test_admin_start_mode_896.py --basetemp=/var/tmp/hermes/pytest-agent-meta/phase3`
- [ ] Step 4: code-reviewer-Review, Findings beheben
- [ ] Step 5: Commit `feat: expose setup_required and guard sync without config`

### Task 3: Setup-Endpunkte + SyncExecutor.init_run
**Rolle:** developer (Review: code-reviewer, Fokus Sicherheit)
**Depends on:** T1, T2
**Files:** Modify scripts/admin-server.py (Routing GET/POST, `SyncExecutor`); Modify tests/test_admin_setup_mode.py
**Interfaces:**
- Produces: `GET /api/setup/options` -> `{providers, git_platforms, dod_presets, defaults}`; `POST /api/setup/config` (Body = answers) -> 200 `{success, path}` | 400 `{error:"bad_request", detail:[...]}` | 409 `{error:"already_configured"}` | 413 (bestehend), atomares Schreiben via `_write_config` (inkl. `harden_admin_config_files`), create-only (`O_EXCL`/Lock); `POST /api/setup/init-sync` -> 409 wenn `project.yaml` fehlt, sonst `{success, output, returncode}`; `SyncExecutor.init_run()` = `_run(["--config", <abs>/.meta-config/project.yaml, "--init"])`.
- Consumes: `build_setup_config`, `validate_setup_answers` (T1), Guard (T2), `_check_token`, `_check_origin`, `_record_run`.
**AC:** AC-4 (gültige Antworten -> 200, Datei per `lib.config.load_config` ladbar, Rechte owner-only), AC-6 (400 mit Fehlerliste, keine Datei), AC-7 (vorhandene Config -> 409, Datei byte-gleich), AC-8 (`init-sync` -> `returncode==0`, generierte Agent-Dateien existieren), AC-9 (Formularwerte mit Shell-Metazeichen -> gemocktes argv enthält nur die festen Argumente), zusätzlich: ohne Token 401/403, falscher Origin abgelehnt, Zielpfad nicht aus Body beeinflussbar.
- [ ] Step 1: Tests schreiben (rot)
- [ ] Step 2: Endpunkte und `init_run` implementieren
- [ ] Step 3: Test (pass)
- Testbefehl: `TMPDIR=/var/tmp/hermes/pytest-agent-meta rtk bypass python3 -m pytest tests/test_admin_setup_mode.py tests/test_admin_server.py --basetemp=/var/tmp/hermes/pytest-agent-meta/phase3`
- [ ] Step 4: code-reviewer-Review, Findings beheben
- [ ] Step 5: Commit `feat: add setup endpoints and init sync executor`

### Task 4: UI-Wizard
**Rolle:** developer (Review: code-reviewer)
**Depends on:** T3
**Files:** Modify docs/ui/admin-ui.html (`init()` ~:11989, Sync-Button-Muster ~:5357); Create tests/test_admin_ui_setup_wizard.py
**Interfaces:**
- Produces: Setup-View bei `setup_required` (Schritte Identity, Provider, Git, optional DoD-Preset; Review; "Anlegen"; "Erst-Sync starten" mit Output-Anzeige und Busy-State für lange Läufe, R-2); danach Reload auf Normalbetrieb; Normal-Navigation im Setup-Zustand nicht erreichbar.
- Consumes: `/api/mode`, `/api/setup/options|config|init-sync`, `api.get/post`, `toast`.
**AC:** AC-10 (statische/DOM-Strukturprüfung nach Muster `tests/test_admin_ui_*_section.py`: `init()` verzweigt auf `setup_required`, Wizard-Container und die drei Setup-API-Aufrufe vorhanden, Navigation im Setup-Zweig nicht gerendert, Reload nach Abschluss).
- [ ] Step 1: UI-Test schreiben (rot)
- [ ] Step 2: Wizard implementieren; kein `eval`/`innerHTML` mit ungeprüften Server-Strings (Escape-Helfer der Datei nutzen)
- [ ] Step 3: Test (pass)
- Testbefehl: `TMPDIR=/var/tmp/hermes/pytest-agent-meta rtk bypass python3 -m pytest tests/test_admin_ui_setup_wizard.py --basetemp=/var/tmp/hermes/pytest-agent-meta/phase3`
- [ ] Step 4: Optional Playwright-Smoke gegen temporären Root (nur erlaubte read-only Tools, siehe Global Constraints)
- [ ] Step 5: code-reviewer-Review, Findings beheben
- [ ] Step 6: Commit `feat: add setup wizard to admin ui`

### Task 5: ADM-03 Tests + UI-Fehleranzeige
**Rolle:** developer (Review: code-reviewer)
**Depends on:** T4
**Files:** Modify tests/test_admin_setup_mode.py (oder neue Datei tests/test_admin_readonly_writes_phase3.py, falls Datei zu groß); Modify tests/test_admin_ui_setup_wizard.py; Modify docs/ui/admin-ui.html nur falls Lücke gefunden; Modify scripts/admin-server.py nur bei Befund aus Step 1
**Interfaces:**
- Produces: Tests für alle Schreibpfade auf Sections außerhalb `PROJECT_WRITABLE_SECTIONS` (`POST /api/config/project/section`, `PUT /api/config/project` mit geändertem Wert, interner Schreibpfad); UI: jeder Section-Save-Fehler (`APIError`) -> `toast(...,"error")` und/oder Inline mit Server-`detail`, kein Erfolgs-Toast.
- Consumes: `_assert_project_sections_writable`, `_assert_project_update_writable`, bestehende Tests `tests/test_admin_server.py:2165-2237`.
**AC:** AC-11 (je Pfad Status 400, Datei byte-gleich), AC-12 (Full-PUT mit unveränderter Read-only-Section -> 200), AC-13 (UI-Strukturtest: Section-Save-Handler fangen `APIError`, zeigen Fehler, kein Erfolgs-Toast im Fehlerzweig; Lücken im HTML schließen).
- [ ] Step 1: Tests schreiben; Ist-Stand je Pfad dokumentieren, rote Tests -> minimale Härtung
- [ ] Step 2: Befunde beheben (nur Lücken, kein Umbau)
- [ ] Step 3: Test (pass)
- Testbefehl: `TMPDIR=/var/tmp/hermes/pytest-agent-meta rtk bypass python3 -m pytest tests/test_admin_setup_mode.py tests/test_admin_ui_setup_wizard.py tests/test_admin_server.py --basetemp=/var/tmp/hermes/pytest-agent-meta/phase3`
- [ ] Step 4: code-reviewer-Review, Findings beheben
- [ ] Step 5: Commit `test: cover read-only section writes and ui error display`

### Task 6: Doku
**Rolle:** documenter (Review: code-reviewer)
**Depends on:** T5
**Files:** Modify rules/2-platform/agent-meta-admin-ui.md (Abschnitt "Setup-Modus": Zustand, Endpunkte, Auth-Hinweis non-loopback nur mit CLI-/Env-Token); Modify docs/REQUIREMENTS.md (REQ-ADM-01..03 Status); Modify CHANGELOG.md nur falls vorhanden und im Projekt gepflegt; Generated: `.claude/skills/admin-ui/SKILL.md` und Provider-Kopien via `python3 scripts/sync.py`
**Interfaces:** Produces: aktualisierte Doku. Consumes: Ergebnisse T1-T5.
**AC:** Skill-Quelle enthält Abschnitt "Setup-Modus" mit `setup_required` und allen drei `/api/setup/*`-Endpunkten; REQUIREMENTS.md-Status der drei REQs aktualisiert; `python3 scripts/sync.py --validate` meldet keine Fehler; generierte Skill-Datei enthält den neuen Abschnitt.
- [ ] Step 1: Quelle und REQUIREMENTS editieren
- [ ] Step 2: `python3 scripts/sync.py` laufen lassen, danach `python3 scripts/sync.py --validate`
- [ ] Step 3: code-reviewer-Review, Findings beheben
- [ ] Step 4: Commit `docs: document admin setup mode`

## Self-Review
- Jeder Task mappt auf genau eine Rolle; alle AC (AC-1..13) sind auf Tasks verteilt: T1 AC-5/6, T2 AC-1..3, T3 AC-4/6/7/8/9, T4 AC-10, T5 AC-11..13.
- Keine Dateiüberlappung innerhalb einer Parallel-Gruppe, da keine Parallelgruppen existieren; Tasks strikt sequentiell.
- `pipeline_stages` deckt die Stage `implement` ab (Task 3 laut Template-Konvention als Referenz-Schrittnummer).
- Aufwand: Schätzung durch `effort-estimator` (Textreferenz, Spec nennt M-L, 6 Tasks).
- Re-Planning: nach T2 (OQ-1-Befund) und nach T3 (Sicherheitsreview) Annahmen und Reihenfolge prüfen.
