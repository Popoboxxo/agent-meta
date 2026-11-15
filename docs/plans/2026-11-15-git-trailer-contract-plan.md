---
pipeline_stages:
  implement: 1
status: geplant
date: 2026-11-15
spec: docs/specs/2026-11-15-git-trailer-contract-spec.md
spec-status: APPROVED
klasse: L
branch: feat/git-trailer-contract
---

# Git-Trailer-Vertrag Implementation Plan

> Status: geplant — Spec APPROVED (User, 2026-11-15)

**Goal:** Commit-Trailer per Projekt-Config `commit.trailers` konfigurierbar machen (E-19). Rangfolge Brief > Config > Harness. Eine gemeinsame Quelle speist `git.md` (Variable `COMMIT_TRAILERS`) und den `AUTO_COMMIT_BLOCK` aller committenden/delegierenden Rollen. Admin-Sektion `commit` im selben PR.

**Architecture:** `commit.trailers` → `scripts/lib/commit_trailers.py` (`commit_violations`, `commit_warnings`, `render_commit_trailers`) → (a) `variables["COMMIT_TRAILERS"]` für `git.md`, (b) `resolved["commit_trailers"]` → `_trailer_line` in `render_auto_commit_block`. `agent_sync.py` reicht `resolved` unverändert durch; die 64+1 Rollen-Templates bleiben unberührt. Validierung in `--validate` und serverseitig im Admin-Backend (HTTP 400).

**Tech Stack:** Python 3.9 (Stdlib only), JSON-Schema (Strukturcheck ohne `jsonschema`), Markdown-Templates mit `{{#if}}`-Platzhaltern, Admin-UI als statische HTML-Datei, unittest/pytest.

**Spec:** docs/specs/2026-11-15-git-trailer-contract-spec.md

## Global Constraints

- Python 3.9-kompatibel: kein `X | Y`, kein `match`; `typing.List`/`Optional`.
- Nur Stdlib; keine neuen Dependencies.
- Kein Provider- oder Modellname in `agents/1-generic` und `scripts/lib` (`tests/test_provider_agnostic_dispatch.py`, `test_no_provider_literal_usage_in_lib`).
- Tests lesen keine gitignorierten generierten Dateien (`.claude/agents/*` u. a.); sie rendern aus Templates oder lesen versionierte Fixtures.
- Branch `feat/git-trailer-contract`; kein Amend, kein Force-Push; Push/Tag/Branch nur durch Rolle `git`.
- Commit-Trailer im Brief an `git`, wörtlich und je 1x: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` und `Claude-Session: https://claude.ai/code/session_01X59S4DW7zkWeQhy1nDRrfW`.
- Commit-Betreff Englisch, Imperativ, höchstens 72 Zeichen, Format `<type>: <beschreibung>`.
- Alle Tasks strikt sequentiell (keine Parallelgruppe); jeder Task besitzt seine Dateien exklusiv, keine Überlappung zwischen Tasks außer dem bewusst gebündelten Rebaseline-Task 9.
- Ohne `commit`-Key bleibt jede Rollen-Ausgabe außer `git.md` byte-identisch (Default = heutiges Verhalten).
- Task-IDs sind numerisch (`### Task 0` bis `### Task 10`); `Depends on:` nennt die Vorgänger-Nummer (Parser normalisiert zu `task-N`).

## File Structure

- Create: `scripts/lib/commit_trailers.py` — Validator, Warnungen, Renderer (Task 1)
- Create: `tests/test_commit_trailers.py` — Schema-Strukturcheck, C2, C3 (Task 1, 2, 3)
- Modify: `config/project-config.schema.json` — Root-Property `commit` (Task 2)
- Modify: `scripts/lib/config.py` — `COMMIT_TRAILERS`, `_VARIABLE_FALLBACKS`, `resolved["commit_trailers"]` (Task 2)
- Modify: `scripts/lib/cli_commands.py` — `_handle_validate` (Task 3)
- Modify: `agents/1-generic/git.md` — Regelerweiterung, Version 2.2.0 (Task 4)
- Modify: `tests/test_git_template_commit_trailer_rule.py` — erweiterter Test (Task 4)
- Modify: `scripts/lib/auto_commit.py` — `_TRAILER_LINES`, `_trailer_line` (Task 5)
- Modify: `tests/test_auto_commit_block_render.py` — Matrix (Task 5)
- Modify: `scripts/admin-server.py` — Whitelist, `_guard_commit_write`, Full-PUT (Task 6)
- Modify: `tests/test_admin_server.py` — Klasse `TestWriteProjectSectionFeatureBSections` (Task 6)
- Modify: `docs/ui/admin-ui.html` — `viewProjectCommit`, Route, Sidebar, `routeMap` (Task 7)
- Modify: `docs/api/admin-ui-reference.md` — Help-Block `project_instance-commit` (Task 7)
- Create: `tests/test_admin_ui_commit_section.py` — statische Asserts (Task 7)
- Modify: `CHANGELOG.md` — `### Added` unter Unreleased (Task 8)
- Modify: `scripts/lib/consistency/placeholders.py` (Task 8; `COMMIT_TRAILERS`, `COMMIT_TRAILERS_SET` in der Whitelist), `tests/test_commit_trailers_placeholder_whitelist.py` (neu); `scripts/lib/standalone.py` bereits in Task 2 (Fallbacks)
- Modify: `tests/fixtures/slimming-golden/git.md`, `tests/test_template_slimming_equivalence.py` (Docstring), `tests/fixtures/ac01-baseline/hashes.json`, `standalone/agents/git.md`, `.meta-config/generated-file-hashes.json` (Task 9)
- Unverändert: `scripts/lib/agent_sync.py`, die 64+1 Rollen-Templates, `rules/1-generic/commit-conventions.md`.

## Tasks

### Task 0: Spec und Plan committen
**Agent:** git
**Depends on:** keine
**Files:**
- Create: `docs/specs/2026-11-15-git-trailer-contract-spec.md`
- Create: `docs/plans/2026-11-15-git-trailer-contract-plan.md`

**Interfaces:** Produces: Dokumenten-Baseline auf dem Branch; Consumes: nichts.
**AC:** Voraussetzung für alle AC (Spec-Gate).
- [ ] Step 1: Branch `feat/git-trailer-contract` prüfen (nicht `main`).
- [ ] Step 2: `python3 scripts/sync.py --validate-spec-plan` ausführen; erwartet: keine Findings für Spec und Plan.
- [ ] Step 3: Beide Dateien committen. Betreff: `docs: add git trailer contract spec and plan`

### Task 1: commit_trailers.py und Tests
**Agent:** developer
**Depends on:** 0
**Files:**
- Create: `scripts/lib/commit_trailers.py`
- Create: `tests/test_commit_trailers.py`

**Interfaces:** Produces: `commit_violations(cfg: dict) -> List[str]`, `commit_warnings(cfg: dict) -> List[str]`, `render_commit_trailers(cfg: dict) -> str`; Consumes: nichts (Muster `auto_commit_violations`, `auto_commit.py:182`).
**AC:** 2, 3 (Teil: leerer Render), 12, 18 (Teil), 19.
- [ ] Step 1: Test schreiben (rot): `commit_violations` für fehlend/`None` → `[]`; Nicht-Mapping, Nicht-Liste, Regex-Verstoß (`"kein trailer"`), Nicht-String, Duplikat, unbekannter Key → Meldungen mit Präfix `commit.` laut C2; `commit_warnings` für `Co-Authored-By` ohne E-Mail (case-insensitive), keine Warnung bei Formatverstoß; `render_commit_trailers`: gültige Items mit `\n`, `""` bei fehlend/`None`/Nicht-Liste/leer, ungültige und doppelte Items verworfen, wirft nie.
- [ ] Step 2: Modul implementieren (Regex `^[A-Za-z][A-Za-z0-9-]*: \S.*$`, Python-3.9-Typen, kein Provider-Literal).
- [ ] Step 3: Verifikation: `python3 -m pytest tests/test_commit_trailers.py -q` grün.
- [ ] Step 4: Commit. Betreff: `feat: add commit trailer validator and renderer`

### Task 2: Schema und config.py
**Agent:** developer
**Depends on:** 1
**Files:**
- Modify: `config/project-config.schema.json`
- Modify: `scripts/lib/config.py`
- Modify: `tests/test_commit_trailers.py`

**Interfaces:** Produces: Root-Property `commit` (`trailers`: Array, `uniqueItems`, `pattern`, Default `[]`, `additionalProperties: false`), `variables["COMMIT_TRAILERS"]` (`setdefault`), Flag `variables["COMMIT_TRAILERS_SET"]`, `_VARIABLE_FALLBACKS["COMMIT_TRAILERS"] = ""` und `["COMMIT_TRAILERS_SET"] = "false"`, `_auto_commit_resolved["commit_trailers"]` in valid- und invalid-Zweig; Consumes: `render_commit_trailers` (Task 1).
**AC:** 3, 13, 19; C1, C3.
- [ ] Step 1: Tests ergänzen (rot): Schema-Strukturcheck (Property, `additionalProperties`, `uniqueItems`, `pattern`, Default); `_build_core_variables` mit gültigem Key → `COMMIT_TRAILERS` gesetzt und `_AUTO_COMMIT_RESOLVED["commit_trailers"]` Liste; ohne Key → `""` und `[]`; ungültiger Block → kein `COMMIT_TRAILERS`-Inhalt, `commit_trailers == []`, kein Wurf; explizites `variables.COMMIT_TRAILERS` gewinnt.
- [ ] Step 2: Schema und `config.py` implementieren (vor dem auto_commit-Block, `:1812`).
- [ ] Step 3: Verifikation: `python3 -m pytest tests/test_commit_trailers.py -q`; zusätzlich `python3 scripts/sync.py --validate` Exit 0.
- [ ] Step 4: Commit. Betreff: `feat: add commit.trailers schema and COMMIT_TRAILERS variable`

### Task 3: --validate-Einhängung
**Agent:** developer
**Depends on:** 2
**Files:**
- Modify: `scripts/lib/cli_commands.py`
- Modify: `tests/test_commit_trailers.py`

**Interfaces:** Produces: `config-audit [ERROR] commit: …` (zählt in `consistency_errors`) und `config-audit [WARN] commit: …` (ohne Zähler); Consumes: `commit_violations`, `commit_warnings` (Task 1).
**AC:** 9, 10, 11; C4.
- [ ] Step 1: Tests (rot): `_handle_validate` mit `["kein trailer"]` → Exit 1 und Meldung mit `commit.trailers[0]`; `Co-Authored-By`-Item ohne E-Mail → Warnung, Exit 0; Duplikate und unbekannter Key → Exit 1.
- [ ] Step 2: Einhängung neben dem auto_commit-Check (`:1487-1491`) implementieren; Import analog zum Bestand.
- [ ] Step 3: Verifikation: `python3 -m pytest tests/test_commit_trailers.py -q`.
- [ ] Step 4: Commit. Betreff: `feat: validate commit.trailers in sync --validate`

### Task 4: git.md 2.2.0
**Agent:** developer
**Depends on:** 3
**Files:**
- Modify: `agents/1-generic/git.md`
- Modify: `tests/test_git_template_commit_trailer_rule.py`

**Interfaces:** Produces: erweiterter Absatz `:140` (unbedingte Rangfolge, bedingter `{{#if COMMIT_TRAILERS_SET}}`-Teil mit Überschrift „Verbindliche Trailer (Projekt-Config)“) und `version: 2.2.0`; Consumes: Variablen `COMMIT_TRAILERS`, `COMMIT_TRAILERS_SET` (Task 2).
**AC:** 1, 2, 3, 4, 18, 19; C5.
- [ ] Step 1: Test erweitern (rot): Version `2.2.0`; Rangfolge im Wortlaut; Render ohne Key: `Co-Authored-By` genau 1x im Absatz, `verbatim` im selben Absatz, „Verbindliche Trailer“ fehlt; Render mit `commit.trailers` je aktivem Provider: Zeile genau 1x; Brief-gewinnt- und genau-1x-Regel (Doppel-Trailer-Risiko) im Wortlaut.
- [ ] Step 2: Absatz in `git.md` erweitern (kein zweiter Absatz, kein zweites `Co-Authored-By`-Literal im unbedingten Teil, kein Provider-/Modellname); Version anheben.
- [ ] Step 3: Verifikation: `python3 -m pytest tests/test_git_template_commit_trailer_rule.py tests/test_provider_agnostic_dispatch.py -q` grün. Golden-/Hash-Tests sind bis Task 9 erwartbar rot und werden dort rebaselined.
- [ ] Step 4: Commit. Betreff: `feat: extend git trailer rule with config precedence`

### Task 5: auto_commit.py Trailer-Zeile
**Agent:** developer
**Depends on:** 4
**Files:**
- Modify: `scripts/lib/auto_commit.py`
- Modify: `tests/test_auto_commit_block_render.py`

**Interfaces:** Produces: `_TRAILER_LINES` (Prosa je Authority) und `_trailer_line(resolved: dict, authority: str) -> str`, Einfügung unmittelbar vor `_BOM_LINE` in den drei Modus-Zweigen, Signatur von `render_auto_commit_block` unverändert; Consumes: `resolved["commit_trailers"]` (Task 2).
**AC:** 3 (Rollen-Render byte-identisch), 5, 6, 7, 8, 18, 19; C6.
- [ ] Step 1: Tests (rot): Matrix direct/delegate/notify/suggest × mit/ohne Trailer; mit Trailern: Zeilen wörtlich 1x, vor `_BOM_LINE`; `delegate` verlangt Trailer im Brief an `git` und enthält keine Anweisung zum Selbst-Commit; `notify` und `suggest` nennen die berichtete/vorgeschlagene Message; `off`, `none`, invalid (`_DISABLED_LINE`), `custom` ohne Script (`_CONFIG_ERROR_LINE`) ohne Trailer-Zeile und unverändert; Nicht-Liste in `resolved["commit_trailers"]` ignoriert; ohne Trailer: Block byte-identisch zum Stand vor der Änderung (Vergleich gegen eingebettete Referenz-Strings).
- [ ] Step 2: Implementieren; kein Provider-/Modellname.
- [ ] Step 3: Verifikation: `python3 -m pytest tests/test_auto_commit_block_render.py tests/test_provider_agnostic_dispatch.py -q` grün.
- [ ] Step 4: Commit. Betreff: `feat: add commit trailer lines to auto_commit block`

### Task 6: Admin-Backend
**Agent:** developer
**Depends on:** 5
**Files:**
- Modify: `scripts/admin-server.py`
- Modify: `tests/test_admin_server.py`

**Interfaces:** Produces: `"commit"` in `PROJECT_WRITABLE_SECTIONS` (plus Kommentar), `_guard_commit_write(self, section: str, data: Any) -> Any` (`ValueError("invalid 'commit': ...")`, Deep-Copy, Warnungen blockieren nicht), Aufruf in `_write_project_section` vor `existing[section] = data` und im Full-PUT-Pfad (`do_PUT`, Einhängestelle neben `:4240ff` beim Implementieren festlegen und im Commit-Body nennen); Consumes: `commit_violations` (Task 1, lazy Import aus `lib.commit_trailers`).
**AC:** 14, 15, 16, 19; C7.
- [ ] Step 1: Tests (rot) in `TestWriteProjectSectionFeatureBSections`: `commit` in Whitelist, `variables` bleibt gesperrt; gültiger Payload Round-Trip identisch in `project.yaml`; ungültige Payloads (Nicht-Liste, Regex-Verstoß, Duplikat, unbekannter Key) → `ValueError` mit Präfix `invalid 'commit'` und Datei unverändert; Full-PUT mit ungültigem `commit` → 400.
- [ ] Step 2: Implementieren.
- [ ] Step 3: Verifikation: `python3 -m pytest tests/test_admin_server.py -q` grün.
- [ ] Step 4: Commit. Betreff: `feat: allow validated commit section in admin backend`

### Task 7: Admin-UI und Help-Doku
**Agent:** frontend-component-engineer
**Depends on:** 6
**Files:**
- Modify: `docs/ui/admin-ui.html`
- Modify: `docs/api/admin-ui-reference.md`
- Create: `tests/test_admin_ui_commit_section.py`

**Interfaces:** Produces: `async function viewProjectCommit()`, `router.register("/project/commit", viewProjectCommit)`, Sidebar-Eintrag `route: "/project/commit"`, `routeMap`-Eintrag `"project/commit": "project_instance-commit"`, Speichern per `saveProjectSection("commit", { trailers: [...] }, status)`, Help-Block `### Commit` mit `<!-- help-id: project_instance-commit -->`, `last-updated`, `author`; Consumes: Admin-Backend-Sektion `commit` (Task 6), Muster `viewProjectGit`, `a11yField`.
**AC:** 17, 19; C8.
- [ ] Step 1: Statische Tests schreiben (rot), Muster `tests/test_admin_ui_git_section.py`: View, Route, Sidebar, `saveProjectSection("commit"`, `routeMap`, Help-Block; Hinweistext (wörtlich, keine dynamischen Werte, `Claude-Session:` nicht per Config); Help-Mappings-Checker ohne Findings.
- [ ] Step 2: View als Textarea (eine Trailer-Zeile je Zeile, leere Zeilen verwerfen) und Help-Block implementieren.
- [ ] Step 3: Verifikation: `python3 -m pytest tests/test_admin_ui_commit_section.py tests/test_admin_ui_git_section.py tests/test_admin_ui_auto_commit_section.py -q` grün; Help-Mappings-Checker (im Repo vorhandener Test) grün.
- [ ] Step 4: Commit. Betreff: `feat: add commit trailers editor to admin ui`

### Task 8: CHANGELOG und Whitelist-Prüfung
**Agent:** documenter
**Depends on:** 7
**Files:**
- Modify: `CHANGELOG.md`
- Modify: `scripts/lib/standalone.py` (nur wenn `COMMIT_TRAILERS` dort fehlt und ein Test es belegt)
- Modify: `scripts/lib/consistency/placeholders.py` (nur wenn die Variable dort geführt werden muss und ein Test es belegt)

**Interfaces:** Produces: `### Added`-Eintrag unter `## [Unreleased]`; Consumes: Ergebnisse der Tasks 1 bis 7.
**AC:** 21, 19.
- [ ] Step 1: Prüfen: `python3 scripts/sync.py --render-standalone --check` und der Placeholder-Konsistenztest; nur bei konkretem Befund `standalone.py`/`placeholders.py` anpassen (Muster `AUTO_COMMIT_BLOCK`, `standalone.py:97`, `placeholders.py:113`), sonst unverändert lassen und das im Commit-Body vermerken.
- [ ] Step 2: CHANGELOG-Eintrag: Key `commit.trailers`, Default leer = heutiges Verhalten, Trailer im auto_commit-Block aller committenden/delegierenden Rollen, Admin-Sektion `commit`, Nicht-Breaking, Hinweis auf veraltende Modellnamen in Config-Trailern.
- [ ] Step 3: Verifikation: `python3 scripts/sync.py --validate` Exit 0; CHANGELOG-Strukturtest (falls vorhanden) grün.
- [ ] Step 4: Commit. Betreff: `docs: changelog for commit.trailers contract`

### Task 9: Rebaseline-Commit
**Agent:** developer
**Depends on:** 8
**Files:**
- Modify: `tests/fixtures/slimming-golden/git.md`
- Modify: `tests/test_template_slimming_equivalence.py`
- Modify: `tests/fixtures/ac01-baseline/hashes.json`
- Modify: `standalone/agents/git.md`
- Modify: `.meta-config/generated-file-hashes.json`

**Interfaces:** Produces: konsistente Goldens/Hashes zum neuen `git.md` (Docstring-Eintrag in der Slimming-Testdatei); Consumes: finale Templates und Quellen (Tasks 1 bis 8).
**AC:** 20.
- [ ] Step 1: Arbeitsbaum muss sauber sein; roten Ausgangszustand bestätigen (`python3 -m pytest tests/test_template_slimming_equivalence.py tests/test_ac01_render_identity.py -q`).
- [ ] Step 2: `tests/fixtures/slimming-golden/git.md` per Hand-Patch (Versions-Pins plus Regel-Hunk) anpassen; Docstring-Eintrag in `tests/test_template_slimming_equivalence.py`.
- [ ] Step 3: `python3 tests/test_ac01_render_identity.py --write`; Diff-Gate: `hashes.json` darf sich ausschließlich für git-Einträge ändern, sonst Abbruch und Ursache klären.
- [ ] Step 4: `python3 scripts/sync.py --render-standalone`, danach `python3 scripts/sync.py` (aktualisiert `.meta-config/generated-file-hashes.json`).
- [ ] Step 5: `python3 -m pytest tests/test_context_budgets.py -q`; nur bei Rot die `git`-Ceilings (Ist + 2 %, min 256 B, max 4096 B) neu pinnen; weitere Rollen-Pins nur bei belegtem Befund.
- [ ] Step 6: Commit. Betreff: `chore: rebaseline git template goldens and hashes`

### Task 10: Verifikation
**Agent:** test-executor
**Depends on:** 9
**Files:**
- Modify: keine (reine Ausführung, kein Schreibzugriff)

**Interfaces:** Produces: Pass/Fail-Bericht je Kommando; Consumes: Gesamtstand der Tasks 0 bis 9.
**AC:** 1–21 (Gesamtnachweis), insbesondere 18, 19, 20.
- [ ] Step 1: Betroffene Tests: `tests/test_commit_trailers.py`, `tests/test_auto_commit_block_render.py`, `tests/test_git_template_commit_trailer_rule.py`, `tests/test_admin_server.py`, `tests/test_admin_ui_commit_section.py`, `tests/test_admin_ui_git_section.py`, `tests/test_admin_ui_auto_commit_section.py`.
- [ ] Step 2: Querschnitt: `tests/test_provider_agnostic_dispatch.py` (inkl. `test_no_provider_literal_usage_in_lib`), `tests/test_context_budgets.py`, `tests/test_ac01_render_identity.py`, die opencode-v2-surface-Tests, `tests/test_template_slimming_equivalence.py`, die release-gate-checksums-Tests, Drift-Tests.
- [ ] Step 3: CLI: `python3 scripts/sync.py --validate`, `python3 scripts/sync.py --validate-spec-plan`, `python3 scripts/sync.py --check`, `python3 scripts/sync.py --render-standalone --check`.
- [ ] Step 4: Gesamtlauf `python3 -m pytest -q` gegen Python 3.9, falls verfügbar; Ergebnis berichten.
- [ ] Step 5: Bei Rot: Befund an den Orchestrator zurückmelden (kein Selbst-Fix); bei Grün: keine Commit-Aktion.

## Trace-Anker

spec-id: SPEC-git-trailer-contract-2026-11-15

Verweise: Entscheidung E-19, Roadmap `docs/plans/2026-11-15-master-roadmap.md` P37 / PR 0.9, Issues #1168, #1247.

## Umsetzungsstand

- [ ] Task 0 Spec und Plan committen
- [ ] Task 1 commit_trailers.py und Tests
- [ ] Task 2 Schema und config.py
- [ ] Task 3 --validate-Einhängung
- [ ] Task 4 git.md 2.2.0
- [ ] Task 5 auto_commit.py Trailer-Zeile
- [ ] Task 6 Admin-Backend
- [ ] Task 7 Admin-UI und Help-Doku
- [ ] Task 8 CHANGELOG und Whitelist-Prüfung
- [ ] Task 9 Rebaseline-Commit
- [ ] Task 10 Verifikation

## Risiken

- Prompt-Konvention, kein Hard-Gate: Das Modell kann die Rangfolge ignorieren; ein Hook-Gate wäre Folgearbeit.
- Context-Budget: mit gesetzten Trailern wächst jede der 64+1 Rollen um ca. 250–400 B; Default unberührt (Task 9 Step 5 prüft).
- Kopplung an `count("Co-Authored-By") == 1` im bestehenden Test: keine zweite Literal-Nennung im unbedingten Absatz (Task 4).
- Doppel-Trailer bei `delegate` (Brief plus Config): Regel „Brief gewinnt, genau 1x je Zeile“ wird in Task 4 getestet.
- Zwischen Task 4 und Task 9 sind Golden-/Hash-Tests erwartbar rot; Zwischen-Commits sind nicht einzeln release-fähig, nur der Endstand.
- Slimming-Golden und ac01-Hashes nur auf sauberem Stand regenerieren; Diff-Gate in Task 9 Step 3.
- Full-PUT-Einhängestelle in `do_PUT` offen (Spec Offene Fragen); Mindestanforderung ist der Partial-Pfad (Task 6).
- Admin-UI ist eine reine HTML-Datei ohne Build; nur statische Tests, kein Browser-Test.
- Config-Trailer mit festem Modellnamen veralten beim Modellwechsel; im CHANGELOG und Admin-Hinweis dokumentiert (Task 7, 8).

## Self-Review

- Jeder Task mappt auf genau eine Rolle; jedes Akzeptanzkriterium ist über Kommando und AC-Nummer messbar.
- `Files:`/`Interfaces:` vollständig; alle Tasks sequentiell, keine Dateiüberlappung außer geplanter Fortschreibung von `tests/test_commit_trailers.py` (Task 1 bis 3, strikt nacheinander).
- `pipeline_stages` deckt die einzige `plan-driven`-Stage (`implement`) ab.
- Alle 21 AC abgedeckt: 1–4 (Task 4, 1, 2), 5–8 (Task 5), 9–11 (Task 3), 12 (Task 1), 13 (Task 2), 14–16 (Task 6), 17 (Task 7), 18–19 (Task 1, 4–7, 10), 20 (Task 9, 10), 21 (Task 8).
- Effort-Schätzung: `effort-estimator` (Textverweis, hier bewusst nicht berechnet).
