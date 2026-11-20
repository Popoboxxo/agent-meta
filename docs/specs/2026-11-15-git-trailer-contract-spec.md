# Git-Trailer-Vertrag — Spec
> Status: APPROVED (User, 2026-11-15, mit Änderungen: auto_commit-Rollen und Admin-UI im selben PR)
> **ARCHIV-PRÜFUNG 2026-11-20 (teilweise umgesetzt):** Spec APPROVED; zugehöriger Plan nur teilumgesetzt → Spec nicht als DONE markieren.
> Datum: 2026-11-15 | Entscheidung: E-19 | Roadmap: `docs/plans/2026-11-15-master-roadmap.md` P37 / PR 0.9 | Issues: #1168, #1247 | Design: `.tmp/plans/2026-11-15-git-trailer-contract-design.md`
> Klasse: L (siehe Abschnitt Klassifikation)

## Änderungen gegenüber der Vorversion (DRAFT)

- Freigabe mit Änderungen: Nicht-Ziele „kein auto_commit-Block“ und „keine Admin-UI-Whitelist“ entfallen; beides ist jetzt Teil dieses PR (C7, C8).
- Klasse M → L (Dateizahl, öffentliches Schema).
- Entscheidungen 1–5 sind getroffen (Abschnitt Offene Fragen).
- Basis unverändert: origin/main 6853d0f8, `agents/1-generic/git.md` Version `2.1.5`, Trailer-Regel `:140` (#1168), Test `tests/test_git_template_commit_trailer_rule.py`.

## Klassifikation

- Klasse **L**: ca. 20 Dateien (Quelle 6, Template 1, Admin 3, Doku 2, Tests 6, Rebaseline-Artefakte 4; Zählung siehe File-Structure-Map).
- F7-Kriterium: neues öffentliches Config-Schema (`commit.trailers`) plus neuer Admin-Schreibpfad → mindestens M; Dateizahl > 8 → L.
- Kein XL: kein neues Subsystem, kein Architekturschnitt.

## Problem

- Der git-Agent setzt die Harness-Attribution (Modellname Haiku) statt des im Brief verlangten Trailers (Modellname Sonnet). Regel `agents/1-generic/git.md:140` deckt nur den Brief ab.
- Keine Projekt-Config-Quelle: ohne Brief-Trailer entscheidet die Harness.
- Keine ausdrückliche Rangfolge Brief > Config > Harness.
- Nur `Co-Authored-By` ist adressiert; andere Trailer-Tokens sind ungeregelt.
- Committende und delegierende Rollen (Block `AUTO_COMMIT_BLOCK`, 64 generische Templates plus 1 Plattform-Template) kennen keinen Trailer-Vertrag; der git-Agent erreicht nur, was der Delegierende im Brief nennt.
- Kein `commit`-Objekt in `config/project-config.schema.json`; Admin-UI kann nichts dergleichen schreiben.

## Ziel

- Commit-Trailer sind konfigurierbar (E-19) als Liste `commit.trailers`.
- Rangfolge: expliziter Brief des Auftraggebers > Projekt-Config `commit.trailers` > Harness-Attribution; Harness nur ohne Brief UND ohne Config.
- Trailer wörtlich und genau 1x je Zeile; nie Modellnamen aus dem Session-Kontext ableiten.
- EINE gemeinsame Quelle: `commit.trailers` → `scripts/lib/commit_trailers.py` → (a) Variable `COMMIT_TRAILERS` für `git.md`, (b) Trailer-Zeile im `AUTO_COMMIT_BLOCK` über `render_auto_commit_block` in `scripts/lib/auto_commit.py`. Keine Textduplikate in Templates.
- Admin-UI-Whitelist `commit` und Editor-Seite im selben PR; serverseitige Validierung.

## Nicht-Ziele

- Kein Hook-/Guard-Gate für Trailer (Prompt-Konvention).
- Keine dynamischen Trailer (Session-ID): `Claude-Session:` nicht per Config (Entscheidung 5).
- Keine Änderung an `rules/1-generic/commit-conventions.md`.
- Keine Template-Edits in den 64+1 Rollen-Templates (Block wird über die bestehende Platzhalter-Kette `{{AUTO_COMMIT_BLOCK}}` erweitert).
- Kein Provider- oder Modellname im Code oder in `agents/1-generic` (`tests/test_provider_agnostic_dispatch.py`, `test_no_provider_literal_usage_in_lib`).

## Belege (verifiziert in W, origin/main 6853d0f8)

- `scripts/lib/auto_commit.py`: `render_auto_commit_block(resolved: dict, authority: str = AUTHORITY_DIRECT) -> str` (`:340`); Konstanten `AUTHORITY_DIRECT|DELEGATE|NOTIFY|NONE` (`:35-38`), `_BOM_LINE` (`:46`), `_PUSH_BOUNDARY_LINE` (`:52`), `INVALID_CONFIG_MARKER` (`:68`), `_DISABLED_LINE`. Rückgabe `""` bei `mode == "off"` oder `authority == none`; ungültiger Block → `_DISABLED_LINE`; `custom` ohne Script → `_CONFIG_ERROR_LINE` (früher Return). Zeilenfolge am Ende: Modus-spezifische Zeilen, `_BOM_LINE`, `_PUSH_BOUNDARY_LINE`.
- Modi je Authority: `direct` committet selbst (Sentinel-Zeile), `delegate` übergibt an Agent `git` mit „changed files and a ready-to-use Conventional-Commits message“, `notify` liefert Dateien + Message im Report (Aufrufer committet), `none` leer. `suggest` ist authority-agnostisch (nur Vorschlag im Report).
- `scripts/lib/config.py:1812-1861` (`_build_core_variables`): baut `_auto_commit_resolved` (Keys `mode`, `triggers`, `file_count_threshold`, `custom_script`, `secret_scan`), setzt `AUTO_COMMIT_ENABLED`, `AUTO_COMMIT_BLOCK` (Default-Authority direct) und `_AUTO_COMMIT_RESOLVED`.
- `scripts/lib/agent_sync.py:92-123` `_apply_role_auto_commit_overrides(merged_vars, role, agent_meta_root, variables)`: liest `variables["_AUTO_COMMIT_RESOLVED"]`, ruft `render_auto_commit_block(resolved, role_commit_authority(role, root))` je Rolle; Aufruf `:1570`. Reicht `resolved` unverändert durch → **keine Änderung nötig**, wenn `resolved` den Key `commit_trailers` trägt.
- Einhängung im Template: `{{#if AUTO_COMMIT_ENABLED}}` / `{{AUTO_COMMIT_BLOCK}}` / `{{/if}}` (z. B. `developer.md:171-173`). Templates mit dem Block: 64 Dateien in `agents/1-generic/` (u. a. developer, senior-developer, junior-developer, principal-developer, release, orchestrator, planner, documenter, tester, concept-specifier, concept-architect, concept-reviewer, ideation, requirements, alle `se-*`, alle `knowledge-*`, devops-engineer, docker, sre-engineer, technical-writer u. a.) plus `agents/2-platform/agent-meta-mammouth-expert.md`. `git.md` selbst enthält den Block nicht. Platzhalter-Whitelist: `scripts/lib/consistency/placeholders.py:113`; Standalone-Fallback `scripts/lib/standalone.py:97` (`"AUTO_COMMIT_BLOCK": ""`).
- `scripts/admin-server.py:238-263` `PROJECT_WRITABLE_SECTIONS` (frozenset); `:256` enthält `"subagent_permissions", "git", "auto_commit"`. Choke point `_assert_project_sections_writable` (`:5483`), Schreibpfad `_write_project_section` (`:5518`) mit Guards `_guard_*` (`:5547-5550`); Muster mit Validierung: `_guard_release_checklist_write` (`:5555`, wirft `ValueError` → HTTP 400 vor jedem Disk-Write).
- Admin-UI-Datei ist `docs/ui/admin-ui.html` (nicht `scripts/`): `viewProjectGit` (`:7591`), `viewProjectAutoCommit` (`:7677`), Speichern über `saveProjectSection("git"|"auto_commit", out, status)` (`:5978`), Helfer `a11yField` (`:6010`), `textInputEl` (`:7496`), Route-Registrierung `router.register(...)`, Sidebar-Eintrag `route: "/project/git"`, `routeMap` (`:11432-11433`: `"project/git": "project_instance-git"`), Hilfe-Blöcke in `docs/api/admin-ui-reference.md:175-185` (`<!-- help-id: project_instance-git -->`).
- Admin-Tests: `tests/test_admin_server.py:2118` `TestWriteProjectSectionFeatureBSections` (Round-Trip, Whitelist, `variables` bleibt gesperrt); `tests/test_admin_ui_git_section.py` und `tests/test_admin_ui_auto_commit_section.py` (statische Asserts auf `docs/ui/admin-ui.html` und `docs/api/admin-ui-reference.md`).

## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)

Python 3.9-kompatibel (`typing.List`/`Optional`, kein `X | Y`, kein `match`), nur Stdlib, provider-agnostisch.

### C1 — Schema `commit.trailers`

- Datei: `config/project-config.schema.json`, neues Root-Property `commit` (Root `additionalProperties: true` bleibt), Muster der Properties `git` und `auto_commit`.
- Vertrag: `commit` = Objekt, `additionalProperties: false`, einziges Property `trailers`: Array von Strings, `uniqueItems: true`, je Item `pattern` `^[A-Za-z][A-Za-z0-9-]*: \S.*$`, Default `[]`.
- Fehlerpfade: `commit` kein Objekt, `trailers` kein Array, Item ohne Form `Token: Wert`, Duplikat, unbekannter Key unter `commit` → Schema-Fehler.

### C2 — Validator und Warnungen

- Datei: `scripts/lib/commit_trailers.py` (neu).
- `def commit_violations(cfg: dict) -> List[str]` (Muster `auto_commit_violations`, `auto_commit.py:182`): fehlender oder `None`-Block → `[]`. Meldungen beginnen mit `commit.`:
  - `"commit must be a mapping"`
  - `"commit.trailers must be a list"`
  - `"commit.trailers[i] must match 'Token: value'"` (Nicht-String oder Regex-Verstoß)
  - `"commit.trailers contains duplicate value(s): ..."`
  - `"commit has unknown key(s): ..."`
- `def commit_warnings(cfg: dict) -> List[str]`: je Item mit Token `Co-Authored-By` (case-insensitive) ohne E-Mail (ein At-Zeichen zwischen öffnender und schließender spitzer Klammer im Wert) → `"commit.trailers[i] Co-Authored-By should include an email address"`. Formatverstoß-Items werden hier übersprungen. Wirft nie.
- `def render_commit_trailers(cfg: dict) -> str`: gültige Items (Regex wie C1) mit `\n` verbunden; `""` bei fehlendem/`None`/ungültigem Block, Nicht-Liste, leerer Liste; ungültige Items und Duplikate verworfen (Fehler meldet `commit_violations`). Wirft nie.
- Parameter heißt `cfg` (Gesamt-Projekt-Config; Block `cfg.get("commit")`).

### C3 — Variablen `COMMIT_TRAILERS`, `COMMIT_TRAILERS_SET` und `resolved["commit_trailers"]`

- `scripts/lib/config.py` `_build_core_variables` (neben dem `_git_cfg`-Block und vor dem auto_commit-Block `:1812`):
  - `variables["COMMIT_TRAILERS"] = render_commit_trailers(config)`; `setdefault`-Semantik wie `GIT_*` (explizites `variables.COMMIT_TRAILERS` gewinnt); zusätzlich Flag `variables["COMMIT_TRAILERS_SET"] = "true"|"false"` (`<VAR>_SET`-Konvention: `{{#if}}` wertet nur whitelistete true-Flags).
  - `_auto_commit_resolved["commit_trailers"] = render_commit_trailers(config).split("\n")` bzw. `[]` bei leerem String — in BEIDEN Zweigen (valid/invalid) gesetzt, im invalid-Zweig `[]`.
- `_VARIABLE_FALLBACKS["COMMIT_TRAILERS"] = ""` und `_VARIABLE_FALLBACKS["COMMIT_TRAILERS_SET"] = "false"` (`config.py`) sowie beide Einträge im standalone-Fallback-Dict `scripts/lib/standalone.py` (Muster `:97`), sonst Unknown-Placeholder-Fehler (`variables.py:200-206`); beide Einträge in der Platzhalter-Whitelist `scripts/lib/consistency/placeholders.py` (sonst `placeholders.unknown`).
- Fehlerpfade: kein Wurf; Fehlerausgabe ausschließlich über C2/C4.

### C4 — Validate-Einhängung

- `scripts/lib/cli_commands.py` `_handle_validate`, neben dem auto_commit-Check (`:1487-1491`): `commit_violations` → `log.warning("config-audit [ERROR] commit: …")`, `consistency_errors += 1`; `commit_warnings` → `log.warning("config-audit [WARN] commit: …")` ohne Zähler.
- `sync.py --validate`: Fehler → Exit 1, Warnung → Exit 0. Plain sync bleibt Exit 0 (ungültige Items verworfen).

### C5 — Regel in `git.md`

- `agents/1-generic/git.md`, bestehender Absatz `:140` („Commit trailers (issue #1168)“) wird erweitert, kein zweiter Absatz; `version` `2.1.5` → `2.2.0`.
- Unbedingt: Rangfolge Brief > Projekt-Config `commit.trailers` > Harness-Attribution; Harness nur ohne Brief UND ohne Config; Brief-Trailer verbatim (1:1), genau 1x je Zeile; Brief gewinnt bei Konflikt; nichts ermittelbar → keine Trailer-Zeile (nicht raten). Das Literal `Co-Authored-By` bleibt im Render ohne Key genau 1x im Absatz (`tests/test_git_template_commit_trailer_rule.py`).
- Bedingt: `{{#if COMMIT_TRAILERS_SET}}` … `{{COMMIT_TRAILERS}}` … `{{/if}}` im selben Absatz, Überschrift „Verbindliche Trailer (Projekt-Config)“, Zeilen unverändert übernehmen.

### C6 — Block-Erweiterung `render_auto_commit_block`

- Datei/Symbol: `scripts/lib/auto_commit.py` — neue Konstante `_TRAILER_LINES` (Prosa je Authority) und kleine Hilfsfunktion `def _trailer_line(resolved: dict, authority: str) -> str` (leer wenn `resolved.get("commit_trailers")` leer/fehlt). Signatur von `render_auto_commit_block` unverändert.
- Einfügeposition: unmittelbar vor `_BOM_LINE` (`lines.append(_trailer_line(...))` nur wenn nicht leer), also nach Scan-/Sentinel-Zeilen in allen drei Modus-Zweigen. Nicht erreicht bei `off`, `authority none`, invalid (`_DISABLED_LINE`) und `custom` ohne Script (früher Return) — gewollt.
- Text je Authority (provider-agnostisch, kein Modell-/Providername; Trailer-Zeilen werden als eingerückter/Backtick-Block angehängt, wörtlich aus der Liste):
  - `direct` (und `mode: custom`/`auto` direct): „End your own commit message with these trailer lines, copied verbatim, each exactly once“ + Zeilen. Gilt für die eigene Commit-Message.
  - `delegate`: „Put these trailer lines verbatim into the brief you hand to the `git` agent (it copies a brief trailer 1:1, each exactly once)“ + Zeilen. Der Trailer steht im Brief an git, nicht in einer eigenen Commit-Message.
  - `notify`: „Include these trailer lines verbatim at the end of the ready-to-use commit message in your report“ + Zeilen.
  - `suggest` (authority-agnostisch): wie `notify` („in the proposed commit message“).
- Ohne `commit.trailers`: `_trailer_line` liefert `""` → Block byte-identisch zu heute.
- Fehlerpfade: unbekannte Authority bleibt fail-closed (`""`); Nicht-Liste in `resolved["commit_trailers"]` → ignoriert (kein Wurf).

### C7 — Admin-Backend

- `scripts/admin-server.py`:
  - `PROJECT_WRITABLE_SECTIONS` (`:256`): `"commit"` ergänzen; Kommentar-Zeile ergänzen.
  - Neue Methode `def _guard_commit_write(self, section: str, data: Any) -> Any` (Muster `_guard_release_checklist_write`): für `section != "commit"` → `data` unverändert; sonst Deep-Copy, `commit_violations({"commit": payload})` (Import lazy aus `lib.commit_trailers`); Fehler → `ValueError("invalid 'commit': " + "; ".join(errors))` (HTTP 400, vor Disk-Write). Rückgabe normalisierte Kopie. Warnungen blockieren nicht.
  - Aufruf in `_write_project_section` (`:5547-5550`) vor `existing[section] = data`; zusätzlich im Full-PUT-Pfad (`do_PUT`, neben den Guards `:4240ff`) für Key `commit`.

### C8 — Admin-UI

- `docs/ui/admin-ui.html`: neue View `async function viewProjectCommit()` (Muster `viewProjectGit`), `router.register("/project/commit", viewProjectCommit)`, Sidebar-Eintrag `route: "/project/commit"`, `routeMap`-Eintrag `"project/commit": "project_instance-commit"`. Editor: ein mehrzeiliges Textfeld (`el("textarea")` in `a11yField`), eine Trailer-Zeile je Zeile; beim Speichern leere Zeilen verwerfen und `saveProjectSection("commit", { trailers: [...] }, status)`; Server-Fehler (HTTP 400) werden von `saveProjectSection` als Toast/Status angezeigt. Hinweistext: Trailer wörtlich, ohne dynamische Werte, `Claude-Session:` nicht über Config.
- `docs/api/admin-ui-reference.md`: Hilfe-Block `### Commit` mit `<!-- help-id: project_instance-commit -->`, `last-updated`, `author` (Muster `:175-185`).

### C9 — Tests, CHANGELOG, Rebaseline

- Erweitern: `tests/test_git_template_commit_trailer_rule.py` (ohne Key unverändert grün; mit `commit.trailers` Zeile genau 1x im Block; Rangfolge im Wortlaut); `tests/test_auto_commit_block_render.py` (Matrix direct/delegate/notify/suggest × mit/ohne Trailer; off/none/invalid/custom-ohne-Script ohne Trailer); `tests/test_admin_server.py` (Klasse `TestWriteProjectSectionFeatureBSections`: `commit` Round-Trip, Whitelist, ungültiger Payload → `ValueError`, Datei unverändert); `tests/test_admin_ui_git_section.py`-Muster als neue Datei `tests/test_admin_ui_commit_section.py` (View, Route, Sidebar, `saveProjectSection("commit"`, `routeMap`, Help-Block).
- Neu: `tests/test_commit_trailers.py` (C1 Schema per `jsonschema`-freiem Strukturcheck, C2, C3).
- `CHANGELOG.md`: `### Added` unter `## [Unreleased]`: Key `commit.trailers`, Default leer = heutiges Verhalten, Trailer im auto_commit-Block aller committenden/delegierenden Rollen, Admin-Sektion `commit`; Nicht-Breaking.
- Rebaseline in EINEM Commit: `tests/fixtures/slimming-golden/git.md` per Hand-Patch (Versions-Pins + Regel-Hunk) mit Docstring-Eintrag in `tests/test_template_slimming_equivalence.py`; `tests/fixtures/ac01-baseline/hashes.json` (`python3 tests/test_ac01_render_identity.py --write`, nur die git-Einträge dürfen sich ändern, da Default ohne Key rollenseitig byte-identisch); `standalone/agents/git.md` (`python3 scripts/sync.py --render-standalone`); `.meta-config/generated-file-hashes.json` (`python3 scripts/sync.py`). Weitere Rollen-Goldens ändern sich nur, wenn ein Golden-Test mit gesetztem `commit.trailers` rendert — im Default nicht; bei Rot nur betroffene Einträge neu pinnen.
- `tests/test_context_budgets.py`: Default-Render unverändert außer `git.md`; Zuwachs mit gesetzten Trailern ca. 250–400 B je Rolle mit Block (nicht Teil der Default-Budgets). Nach Änderung laufen lassen; Ceilings (Ist + 2 %, min 256 B, max 4096 B) nur für `git`-Einträge neu pinnen.

## File-Structure-Map

- Quelle (6): `config/project-config.schema.json`, `scripts/lib/commit_trailers.py` (neu), `scripts/lib/config.py`, `scripts/lib/auto_commit.py`, `scripts/lib/cli_commands.py`, `scripts/lib/standalone.py`.
- Template (1): `agents/1-generic/git.md`.
- Admin (3): `scripts/admin-server.py`, `docs/ui/admin-ui.html`, `docs/api/admin-ui-reference.md`.
- Doku (1): `CHANGELOG.md`.
- Tests (6): `tests/test_commit_trailers.py` (neu), `tests/test_admin_ui_commit_section.py` (neu), erweitert: `test_git_template_commit_trailer_rule.py`, `test_auto_commit_block_render.py`, `test_admin_server.py`, `test_template_slimming_equivalence.py` (Docstring).
- Rebaseline (4): `tests/fixtures/slimming-golden/git.md`, `tests/fixtures/ac01-baseline/hashes.json`, `standalone/agents/git.md`, `.meta-config/generated-file-hashes.json`.
- Unverändert: `scripts/lib/agent_sync.py` (reicht `resolved` durch), die 64+1 Rollen-Templates.

## Datenfluss

- Eingabe: `.meta-config/project.yaml` → `commit.trailers` (Liste von Strings); Schreibweg alternativ Admin-UI → `POST` Section `commit` → `_guard_commit_write` → `project.yaml`.
- Validierung: `_handle_validate` → `commit_violations` (Fehler) / `commit_warnings` (Warnung); Admin-Backend → `commit_violations` (Fehler = HTTP 400).
- Transformation: `_build_core_variables` → `render_commit_trailers` → (a) `variables["COMMIT_TRAILERS"]`, (b) `_AUTO_COMMIT_RESOLVED["commit_trailers"]`.
- Render (a): `sync.py` substituiert `COMMIT_TRAILERS` in `git.md` je aktivem Provider.
- Render (b): `_apply_role_auto_commit_overrides` → `render_auto_commit_block(resolved, authority)` → Trailer-Zeile je Authority in `{{AUTO_COMMIT_BLOCK}}` jeder Rolle mit Block.
- Ausgabe: `.claude/agents/*.md` u. a. (gitignoriert), `standalone/agents/git.md` (versioniert).
- Laufzeit: `direct` → Trailer in eigener Commit-Message; `delegate` → Trailer im Brief an `git`; `notify`/`suggest` → Trailer in der berichteten Message; `git` → Rangfolge Brief > Config > Harness; Ergebnis im Commit-Footer.
- Persistenz: nur `project.yaml`.

## Acceptance Criteria

1. Given `agents/1-generic/git.md`, When gelesen, Then enthält der erweiterte Absatz (`:140`) die Rangfolge Brief > Projekt-Config `commit.trailers` > Harness-Attribution unbedingt; Version `2.2.0` (C5, C9).
2. Given der Render ohne `commit`-Key, When gezählt, Then kommt `Co-Authored-By` genau 1x im Absatz vor und `verbatim` steht im selben Absatz; der bestehende Test bleibt grün (C5, C9).
3. Given `project.yaml` ohne `commit`-Key, When `render_commit_trailers` aufgerufen, Then `""`; der `git.md`-Render enthält „Verbindliche Trailer“ nicht; der Render von `developer`, `release`, `orchestrator` ist byte-identisch zum Stand vor der Änderung (C2, C3, C5, C6).
4. Given `commit.trailers` mit einer gültigen Zeile, When `git.md` für jeden aktiven Provider gerendert wird, Then enthält jede Ausgabe genau diese Zeile 1x im Block (C3, C5).
5. Given `commit.trailers` gesetzt und `auto_commit.mode: auto` mit Rolle `direct` (Bash + Edit/Write), When gerendert, Then enthält der Block die Direct-Trailer-Zeile mit den Trailern wörtlich, jeweils 1x, vor der BOM-Zeile (C6).
6. Given Rolle `delegate` (Edit/Write, kein Bash, Agent/Task), When gerendert, Then verlangt der Block die Trailer im Brief an `git` und enthält keine Anweisung, selbst zu committen (C6).
7. Given Rolle `notify`, oder `mode: suggest` für beliebige Authority, When gerendert, Then stehen die Trailer in der berichteten/vorgeschlagenen Message (C6).
8. Given `mode: off`, Authority `none`, ungültiger `auto_commit`-Block oder `mode: custom` ohne Script, When gerendert, Then enthält der Block keine Trailer-Zeile und die bisherige Ausgabe (`""`, `_DISABLED_LINE`, `_CONFIG_ERROR_LINE`) bleibt unverändert (C6).
9. Given `commit.trailers: ["kein trailer"]`, When `sync.py --validate`, Then Exit 1 und Meldung mit Präfix `commit.trailers[0]` (C2, C4).
10. Given ein `Co-Authored-By`-Item ohne E-Mail, When `--validate`, Then Warnung `[WARN] commit:`, Exit 0 (C2, C4).
11. Given doppelte Items oder unbekannter Key unter `commit`, When `--validate`, Then Exit 1 mit passender Meldung (C1, C2).
12. Given `commit: null` oder fehlender Block, When `commit_violations`/`commit_warnings`, Then `[]` (C2).
13. Given ein ungültiger `commit`-Block, When Plain-Sync, Then Exit 0, keine Trailer-Zeile im Block und kein `COMMIT_TRAILERS` (C3).
14. Given `PROJECT_WRITABLE_SECTIONS`, When geprüft, Then enthält die Menge `commit`; `variables` bleibt gesperrt (C7).
15. Given gültiger Payload für Section `commit` an `_write_project_section`, When geschrieben, Then Round-Trip identisch in `project.yaml` (C7).
16. Given ungültiger Payload (Nicht-Liste, Regex-Verstoß, Duplikat, unbekannter Key), When `_write_project_section`, Then `ValueError` mit Präfix `invalid 'commit'` und `project.yaml` unverändert (C7).
17. Given `docs/ui/admin-ui.html` und `docs/api/admin-ui-reference.md`, When statisch geprüft, Then existieren `viewProjectCommit`, Route-Registrierung, Sidebar-Eintrag, `saveProjectSection("commit"`, `routeMap`-Eintrag und Help-Block `project_instance-commit`; der Help-Mappings-Checker meldet keine Findings (C8).
18. Given `tests/test_provider_agnostic_dispatch.py`, When ausgeführt, Then grün; kein Provider-/Modellname in `scripts/lib/commit_trailers.py`, `scripts/lib/auto_commit.py` oder `agents/1-generic` (C2, C5, C6).
19. Given Python 3.9, When `tests/test_commit_trailers.py`, `tests/test_auto_commit_block_render.py`, `tests/test_git_template_commit_trailer_rule.py` und die Admin-Tests laufen, Then grün (C9).
20. Given der Rebaseline-Commit, When ac01-, Slimming-, Drift-, Release-Checksum- und Context-Budget-Tests laufen, Then grün; `standalone/agents/git.md` entspricht dem Render; ac01-Hashes ändern sich nur für git (C9).
21. Given `CHANGELOG.md`, When gelesen, Then dokumentiert `### Added` unter Unreleased `commit.trailers`, Default (leer = heutiges Verhalten), die Block-Erweiterung, die Admin-Sektion und Nicht-Breaking (C9).

## Offene Fragen

Entschieden (Nutzerfreigabe 2026-11-15):
- Entscheidung 1: Liste von Trailern (`commit.trailers`), keine Einzelfelder.
- Entscheidung 2: auto_commit-Block der committenden/delegierenden Rollen bekommt den Trailer-Vertrag direkt in diesem PR; eine gemeinsame Quelle in `render_auto_commit_block`.
- Entscheidung 3: Formatverstoß = Fehler, fehlende E-Mail bei `Co-Authored-By` = Warnung.
- Entscheidung 4: Admin-UI-Whitelist `commit` sofort in diesem PR, serverseitig validiert, Backend-Test.
- Entscheidung 5: `Claude-Session:` nicht per Config.

Offen (nicht blockierend):
- Full-PUT-Pfad `do_PUT`: genaue Einhängestelle der `commit`-Prüfung beim Implementieren festlegen (neben `:4240ff`); Mindestanforderung ist der Partial-Pfad.
- Editor-Widget: Textarea (eine Zeile je Trailer) ist vorgegeben; ein Listen-Editor ist Folgearbeit.

## Risiken

- Prompt-Konvention, kein Hard-Gate: Modell kann die Rangfolge ignorieren; Hook-Gate wäre Folgearbeit.
- Context-Budget: mit gesetzten Trailern wächst jede der 64+1 Rollen um ca. 250–400 B; Default unberührt. Projekte mit Trailern prüfen ihr Budget selbst.
- Config-Trailer mit festem Modellnamen veralten bei Modellwechsel; im CHANGELOG und Admin-Hinweis dokumentieren.
- Doppelt-Trailer: `delegate` bringt Trailer im Brief, `git` hängt zusätzlich Config-Trailer an — Regel C5 (Brief gewinnt, genau 1x je Zeile) verhindert Duplikate; im Test abdecken.
- Kopplung an `count("Co-Authored-By") == 1` im bestehenden Test; keine zweite Literal-Nennung im unbedingten Absatz.
- Slimming-Golden/ac01-Hashes nur auf sauberem Stand regenerieren.
- Admin-UI: reine HTML-Datei ohne Build; nur statische Tests, kein Browser-Test.

## Trace-Anker

spec-id: SPEC-git-trailer-contract-2026-11-15
