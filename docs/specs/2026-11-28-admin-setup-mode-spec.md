# Admin-UI Setup-Modus — Spec
> Status: APPROVED (User-Freigabe 2026-11-28)
> Quelle: docs/plans/systemaudit-umsetzungsplan-2026-11-25.md (Phase 3, Z.121-132); docs/REQUIREMENTS.md:104-106

## Problem / Ziel / Nicht-Ziele

**Problem:** Ohne `.meta-config/project.yaml` gibt es in der Admin UI keinen Einstieg. Einziger Setup-Weg ist der interaktive CLI-Wizard.

**Ziel:**
- REQ-ADM-01: Server startet ohne `project.yaml` in einem Setup-Modus.
- REQ-ADM-02: UI-Wizard erzeugt die initiale `project.yaml` und löst die Erst-Instanziierung per `sync.py` aus.
- REQ-ADM-03: Schreibversuche auf nicht-schreibbare Sections geben 4xx. Ein fehlgeschlagener Save wird in der UI sichtbar.

**Nicht-Ziele:**
- Keine Änderung an `viz-*.py`.
- Kein neuer Auth-Mechanismus.
- Kein Ersatz des CLI-Wizards.
- Keine Optionalfelder (Sprachen, Plattformen) jenseits der Wizard-Parität.

## Ist-Inventar (verifiziert; "[nicht ausgeführt]" = nur per Code-Lektüre belegt)

| Befund | Fundstelle |
|---|---|
| Moduserkennung nur über `agents/1-generic/` (super_admin vs. project_admin), kein Setup-Zustand | `scripts/admin-server.py:1375-1382` (`detect_mode`) |
| `/api/mode` liefert `mode`, `root`, `allowed_keys`; `project_admin_available` nur im super_admin | `admin-server.py:4315-4327` |
| Server-Start liest `project.yaml` tolerant: `_load_admin_ui_config` liefert Defaults, wenn die Datei fehlt (`:610`); `ConfigManager.read` liefert `{}` (`:1502-1507`); `_read_version` hat Fallbacks (`:6792-6815`). Ein harter Abbruch im Server ist im Code nicht auffindbar. [Startverhalten nicht ausgeführt; AC-1 verifiziert es.] | `admin-server.py:599-640, 6728-6770` |
| **Eigentliche Lücke:** `/api/sync/run` startet `sync.py` ohne Flags (`:1761-1763`, `:4635`). Ohne Config greift der interaktive Wizard (`lib/cli_commands.py:681-690`). Im Subprozess mit `capture_output` und ohne TTY blockiert er oder bricht per EOF ab. | `admin-server.py:1690-1728`; `cli_commands.py:673-690` |
| `--setup` und Auto-Wizard rufen `run_setup_wizard(...)`, danach `args.init = True` | `cli_commands.py:658-690`; `sync.py:245, 365` |
| `--init` materialisiert Presets (`fill_defaults(... materialize_presets=args.init)`, #1074) | `lib/sync_pipeline.py:186-193` |
| `run_setup_wizard` (`lib/setup.py:195-407`) verknüpft `input()`-Prompts (`_ask*`, `:27-142`) mit der Config-Assembly (`:326-374`). Defaults sind unterschiedlich, Prefix-Validator `_validate_prefix` (`:177`). `_write_config` (`:428-449`) schreibt YAML mit Header und ruft `harden_admin_config_files`. Provider-Liste via `load_providers_config` (`:233`). | `scripts/lib/setup.py` |
| Whitelist `PROJECT_WRITABLE_SECTIONS` (`:239-273`); `_assert_project_sections_writable` wirft `ValueError` (`:5798-5812`), `do_PUT/do_POST` mappen auf **400** (`:4085-4086, 4111-4112`). `SecurityError` führt zu 403 (`:4081-4082`). | `admin-server.py` |
| Auth: UI-Shell public, `/api/*` token-gated, Mutationen zusätzlich `_check_origin`. Fail-closed bei non-loopback ohne Token (`:6743-6750`). | `admin-server.py:4045-4120, 6743-6765`; Skill `admin-ui` |
| UI: `init()` ruft `/api/mode` (`docs/ui/admin-ui.html:11989-12003`), kein Setup-Zweig. Sync-Button: `api.post("/api/sync/run")` (`:5357-5366`). `api.*` wirft bei `!res.ok` `APIError` (`:1001-1031`, Klasse `:1075`). Es gibt `toast(msg,"error")` (`:809`). | `docs/ui/admin-ui.html` |
| Bestehende Tests: `tests/test_admin_server.py` (u.a. Writable-Sections `:2165-2237, 3818ff`), `tests/test_admin_start_mode_896.py`, `tests/test_admin_ui_*_section.py` | `tests/` |

**ADM-03-Ist-Stand:** Das Backend liefert bereits 400 (`bad_request`) für nicht-schreibbare Sections. Das erfüllt "4xx". Offen: (1) Bei `sections` im `PUT /api/config/project` wird nur eine *geänderte* Read-only-Section abgewiesen (`:5814-5831`). (2) Es fehlt ein Test, der für alle drei Schreibpfade 4xx und unveränderte Datei belegt. (3) Es fehlt ein UI-Test, dass jeder Section-Save einen APIError sichtbar macht (Toast oder Inline). Das ist Verifikations- und Härtungsarbeit, kein Neubau.

## Entscheidungen (freigegeben)

**(a) Setup-Zustand: Server-Flag `setup_required` in `/api/mode`.**
- `/api/mode` erhält `setup_required: bool`, wahr genau dann, wenn `.meta-config/project.yaml` nicht existiert. Es ist ein berechneter Wert, kein persistierter Zustand.
- `init()` verzweigt auf diesen Wert und rendert den Wizard statt der Navigation.
- Begründung: Der Server erzwingt die Setup-Guards (Setup-Endpunkte nur, solange kein `project.yaml` existiert) und braucht den Zustand daher selbst. Ein reiner Frontend-Branch wäre umgehbar. `detect_mode` bleibt unverändert, Setup ist orthogonal zu super_admin/project_admin.

**(b) Refactor `lib/setup.py` in pure Funktionen; CLI und Server teilen sie.**
- Pure Funktion `build_setup_config(answers: dict, agent_meta_root: Path) -> dict` und `validate_setup_answers(answers: dict, agent_meta_root: Path) -> list[str]` aus `run_setup_wizard` extrahieren. Defaults und Prefix-Validator bleiben dort.
- Der CLI-Wizard sammelt per Prompt und ruft dieselben Funktionen. Das Ergebnis für identische Antworten bleibt byte-gleich (Regressionstest für `--setup`, AC-5).
- Der Server importiert diese Funktionen und `_write_config` (inkl. `harden_admin_config_files`).
- Begründung: Ein zweiter Config-Builder würde divergieren (Rollenliste, Variablen, gitignore).
- Risiko: Refactor von setup.py ist ein Verhaltensrisiko für `--setup` (siehe R-1).

**(c) Erster Sync mit festen Argumenten über `SyncExecutor.init_run()`.**
- Aufruf: `sync.py --config <abs>/.meta-config/project.yaml --init`.
- Formulardaten gehen ausschließlich in `project.yaml`; der Sync liest nur diese Datei. Nie in argv oder Env (Injektionsfläche).
- `--init` ist die Semantik des CLI-Pfads (`cli_commands.py:668, 687`) und materialisiert Presets.
- Umsetzung: neue Methode `SyncExecutor.init_run()` mit `_run(["--config", <abs>, "--init"])`.

## Interface Contracts

| Datei:Symbol | Vertrag |
|---|---|
| `scripts/lib/setup.py:build_setup_config` (neu) | `(answers: dict, agent_meta_root: Path) -> dict`. Pflicht: `name`, `prefix`, `providers`, `git_platform`. Defaults wie bisher. Kein I/O. |
| `scripts/lib/setup.py:validate_setup_answers` (neu) | `-> list[str]` (Fehlertexte, leer = ok). Nutzt `_validate_prefix`/`_validate_nonempty`, Provider gegen `load_providers_config`. |
| `scripts/lib/setup.py:run_setup_wizard` | Signatur unverändert; delegiert an die neuen Funktionen. |
| `admin-server.py:_route_get_mode` (`:4315`) | Feld `setup_required: bool` ergänzt (rückwärtskompatibel). |
| `GET /api/setup/options` (neu, token-gated) | `{providers: [..], git_platforms: [..], dod_presets: [..], defaults: {...}}`. |
| `POST /api/setup/config` (neu, token + Origin) | Body = `answers`. 200 `{success, path}`; 400 bei Validierungsfehlern (`{error:"bad_request", detail:[...]}`); **409** `{error:"already_configured"}`, wenn `project.yaml` existiert; 413 bei zu großem Body (bestehender Mechanismus). Schreibt atomar nur nach `<root>/.meta-config/project.yaml` (Pfad fest, vom Server berechnet, nie aus Body). |
| `POST /api/setup/init-sync` (neu, token + Origin) | 409, wenn `project.yaml` fehlt (kein Wizard-Start im Subprozess). Sonst `SyncExecutor.init_run()`; Antwort wie `/api/sync/run`: `{success, output, returncode}`. |
| `SyncExecutor.run` / `_run` (`:1690, 1761`) | Guard: fehlt die Config, kein Subprozess-Start; Rückgabe `{success:false, output:"project.yaml missing", returncode:-1}` (verhindert den hängenden interaktiven Wizard). |
| `_route_post_sync_run` (`:4635`) | Antwort bleibt 200 mit `success:false`; das ist bestehender Vertrag und bleibt unverändert. |
| `docs/ui/admin-ui.html:init()` (`:11989`) | Bei `setup_required` Setup-Wizard-View (Schritte: Identity, Provider, Git, optional Preset), Review, "Anlegen", "Erst-Sync starten" mit Output-Anzeige; danach Reload auf Normalbetrieb. Fehler aus `api.*` → `toast(...,"error")` plus Inline-Meldung. |
| `PROJECT_WRITABLE_SECTIONS` / `_assert_project_*` | Unverändert, Entscheidung: 400 bleibt (nicht auf 403 ändern; 4xx erfüllt REQ, bestehende Tests nutzen 400). |

## Datenfluss

1. Start ohne `project.yaml` → Server läuft (Defaults) → UI `/api/mode` meldet `setup_required: true`.
2. UI holt `/api/setup/options`, sammelt Antworten, Client-Vorvalidierung (nur Komfort).
3. `POST /api/setup/config` → `validate_setup_answers` → `build_setup_config` → `_write_config` (atomar, Rechte gehärtet) → 200.
4. `POST /api/setup/init-sync` → `sync.py --config … --init` → Output an UI; `.meta-viz/sync-status.json` wird durch `_record_run` geschrieben.
5. UI lädt `/api/mode` neu (`setup_required: false`) und zeigt die Normalansicht.

## Acceptance Criteria

Given/When/Then; Mapping auf Contracts in Klammern.

**REQ-ADM-01**
- AC-1: Given Projekt-Root ohne `.meta-config/project.yaml`, When `admin-server.py --no-viz` startet, Then Prozess läuft, `/api/health` ist 200 und `/api/mode.setup_required` ist `true`. (`_route_get_mode`)
- AC-2: Given vorhandene `project.yaml`, When `/api/mode` abgefragt wird, Then `setup_required` ist `false`; Verhalten sonst unverändert. (`_route_get_mode`)
- AC-3: Given kein `project.yaml`, When `POST /api/sync/run`, Then kein Subprozess-Start, `success:false`, kein Hängen (Timeout-frei). (`SyncExecutor._run`-Guard)

**REQ-ADM-02**
- AC-4: Given Setup-Zustand, When gültige Antworten an `POST /api/setup/config`, Then 200 und `project.yaml` existiert, ist per `lib.config.load_config` ladbar und Rechte sind owner-only. (`setup/config`)
- AC-5: Given identische Antworten, When CLI-Wizard und `build_setup_config` laufen, Then identisches Config-Dict. (Regression)
- AC-6: Given ungültiger Prefix oder unbekannter Provider, When `POST /api/setup/config`, Then 400 mit Fehlerliste und keine Datei geschrieben. (`validate_setup_answers`)
- AC-7: Given bereits existierendes `project.yaml`, When `POST /api/setup/config`, Then 409 und Datei unverändert. (`setup/config`)
- AC-8: Given frisch angelegte Config, When `POST /api/setup/init-sync`, Then `returncode==0` und generierte Agent-Dateien existieren. (`init-sync`, `init_run`)
- AC-9: Given Formularwerte mit Shell-Metazeichen, When Setup durchläuft, Then argv des Sync-Aufrufs enthält nur die festen Argumente. (`init_run`)
- AC-10: Given Setup-Zustand, When UI lädt, Then Wizard sichtbar, Normal-Navigation nicht erreichbar; nach Abschluss Normalansicht. (`init()`)

**REQ-ADM-03**
- AC-11: Given eine Section außerhalb `PROJECT_WRITABLE_SECTIONS`, When `POST /api/config/project/section`, `PUT /api/config/project` (geänderter Wert) oder interner Schreibpfad, Then Status 4xx (400) und Datei unverändert. (`_assert_project_*`)
- AC-12: Given vorhandene Read-only-Section unverändert im Full-PUT, Then 200 (GET-then-PUT bleibt möglich). (`_assert_project_update_writable`)
- AC-13: Given ein vom Server abgelehnter Save, When der Nutzer in einer Section speichert, Then UI zeigt sichtbaren Fehler (Toast und/oder Inline mit Server-`detail`), kein Erfolgs-Toast. (UI-Handler)

## Sicherheit

- Alle `/api/setup/*` sind token-gated (`_check_token`); Mutationen zusätzlich `_check_origin` (CSRF/DNS-Rebinding). Die UI-Shell bleibt public wie bisher.
- Host-Bindung unverändert: Default Loopback ohne Token; non-loopback fail-closed ohne Token (`:6743-6750`); `--mode network` erzeugt ein nicht persistiertes Token.
- Risiko im Setup-Zustand: Es existiert noch keine `admin-ui.token` in `project.yaml`. Der Setup-Modus darf daher non-loopback nur mit CLI-/Env-Token laufen; keine Lockerung.
- Setup-Endpunkte sind create-only (409 bei vorhandener Config); Zielpfad fest, nicht aus dem Body.
- Kein Token in argv, Log oder Antwort. Antworten enthalten keine Secrets.
- Subprozess nur mit festen Argumenten (AC-9). Body-Größenlimit wie bestehend.

## Teststrategie

- Python-Unit/Integration (Muster: `tests/test_admin_server.py`, `tests/test_admin_start_mode_896.py`): AC-1 bis AC-9, AC-11, AC-12 mit temporärem Root ohne `agents/1-generic`. Aufruf wie bestehend im Projekt (`python3 -m pytest` auf die genannten Dateien); AC-5 als Golden-Vergleich CLI vs. `build_setup_config`.
- UI-Tests nach bestehendem Muster `tests/test_admin_ui_*_section.py` (statische/DOM-Strukturprüfung der HTML-Datei) für AC-10 und AC-13.
- Playwright optional nur read-only (`browser_navigate`, `browser_snapshot`, `browser_take_screenshot`, `browser_click` auf Wizard-Navigation); verboten laut `mcp-guardrails.md`: `browser_run_code_unsafe`, `browser_evaluate`, `browser_file_upload`, `browser_handle_dialog`. Kein Formular-Submit gegen echte Wurzel; ein Smoke gegen temporären Root mit `--no-viz`.
- Nicht in dieser Spec: Ausführung der Tests.

## Task-Schnitt

Alle Tasks laufen **strikt SEQUENTIELL** in der Reihenfolge T1, T2, T3, T4, T5, T6. T5 läuft ausdrücklich nicht parallel zu T1-T4.

1. T1 `setup.py`-Refactor (`build_setup_config`, `validate_setup_answers`) + AC-5/AC-6-Tests. Abhängigkeit für T3.
2. T2 `/api/mode.setup_required` + `SyncExecutor`-Config-Guard + Tests AC-1 bis AC-3.
3. T3 `/api/setup/options|config|init-sync` + `SyncExecutor.init_run` + Tests AC-4, AC-7 bis AC-9 (T1, T2).
4. T4 UI-Wizard in `admin-ui.html` + Tests AC-10 (T3).
5. T5 ADM-03: Test-Abdeckung aller Schreibpfade (AC-11/12) + UI-Fehleranzeige prüfen/härten (AC-13); läuft nach T4 (gleiche Dateien `admin-server.py`/`admin-ui.html`).
6. T6 Doku: Skill `admin-ui` (Setup-Modus-Abschnitt), `docs/REQUIREMENTS.md` Status, ggf. CHANGELOG.

Aufwand: M-L (6 Tasks, ca. 6-8 Dateien plus Tests).

## Geschlossene Fragen

- OQ-1: Bricht der Server ohne `project.yaml` real ab? Durch AC-1 in T2 zu verifizieren (Code deutet auf: kein Abbruch). Umfang von REQ-ADM-01 nur bei Gegenbefund neu bewerten; dann Ursache vor T2-Abschluss lokalisieren.
- OQ-2: Setup-Zustand gilt auch im super_admin-Modus (gleiche Regel: `project.yaml` fehlt). Entschieden: ja.
- OQ-3: Wizard-Umfang: Pflichtfelder plus DoD-Preset; Rest später über die normale UI. Entschieden.
- OQ-4: Fehlercode für Read-only-Writes: 400 bleibt (kein Wechsel auf 403; bestehende Tests nutzen 400). Entschieden.

## Risiken

- R-1: Refactor `setup.py` kann `--setup` brechen; Gegenmaßnahme AC-5.
- R-2: `--init` schreibt viele Dateien (Timeout 300 s in `_run`); UI muss Laufzeit/Busy-State anzeigen.
- R-3: Race zwischen zwei Setup-Requests; atomares Schreiben und 409-Prüfung unter Lock oder `O_EXCL`-Semantik.

## Trace-Anker: spec-id: SPEC-admin-setup-mode
