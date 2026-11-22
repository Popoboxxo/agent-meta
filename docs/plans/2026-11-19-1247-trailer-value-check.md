---
pipeline_stages:
  implement: 1
status: APPROVED
date: 2026-11-19
spec: docs/plans/2026-11-19-1247-trailer-value-check.md
spec-status: APPROVED
klasse: M
branch: fix/1247-1168-trailer-contract
---

# #1247 Commit-Trailer gegen konfigurierten Wert prüfen — Spec und Plan

> Status: APPROVED — Freigabe durch den User am 2026-11-19. Code freigegeben.
> Datum: 2026-11-19 | Issues: #1247, #1168 | Baut auf: `docs/specs/2026-11-15-git-trailer-contract-spec.md` (APPROVED, PR #1282) | Klasse: M
> Hinweis zur Quellenlage: Die Issue-Texte #1247/#1168 waren in dieser Session nicht lesbar (kein `gh`-Zugriff für den Planner). Issue-Texte #1247/#1168 vor Freigabe gegen Entwurf prüfen (lesend durch git/feedback-Rolle).
> Bis zur Freigabe: kein `sync.py`-Lauf, keine Rebaseline; die Working-Tree-Änderung in `rules/1-generic/commit-conventions.md` bleibt uncommitted.

## Klassifikation

- Klasse **M** (Bounded): 3 Quellen, 2 Tests im Kern plus CHANGELOG, Alt-Spec-Änderung und Rule-/Pin-Pass (Task 5).
- F7-Hinweis: kein neues Config-Schema (`commit.trailers` besteht), kein neues Subsystem. Berührt wird eine öffentliche Schnittstelle (CLI-Flag `--check-commit-msg`) und eine Nicht-Ziel-Aussage einer APPROVED-Spec; Einstufung M gilt, weil additiv und opt-in. Default (a): M bestätigt.

## Spec

### Problem

- #1247: Der Trailer-Vertrag (E-19) ist reine Prompt-Konvention. Ob ein echter Commit die konfigurierten Trailer wörtlich trägt, prüft nichts. Beleg #1168: die Harness-Attribution (falscher Modellname) landete im Commit, obwohl Brief/Config einen anderen Wert verlangten.
- Nutzerentscheidung (relayed): Wert-Check wird gewollt: „Commit-Trailer gegen konfigurierten Wert prüfen“.

### Konflikt mit der APPROVED-Spec

- Alt-Spec `2026-11-15-git-trailer-contract-spec.md`, Nicht-Ziele: „Kein Hook-/Guard-Gate für Trailer (Prompt-Konvention).“ und Risiko „Hook-Gate wäre Folgearbeit“.
- Gewählter Entwurf: **opt-in CLI-Check** (kein Eingriff in `orchestrator-guard-impl.sh`); bleibt ein Gate, sobald ein Projekt ihn als `commit-msg`-Hook verdrahtet.
- **Spec-Änderung (Amendment der Alt-Spec, Default d; Task 4):** Nicht-Ziel ersetzen durch: „Kein Gate im PreToolUse-Orchestrator-Guard (`hooks/1-generic/orchestrator-guard-impl.sh` unverändert). Eine opt-in Prüfung per `sync.py --check-commit-msg <datei>` (Spec `2026-11-19-1247-trailer-value-check`) ist zulässig; sie ist Convention boundary.“ Risiko-Zeile „Hook-Gate wäre Folgearbeit“ um Verweis ergänzen. Alt-Spec bleibt `APPROVED`; Eintrag unter „Änderungen“ mit Datum.
- **Bereits im Working Tree (uncommitted):** Override-Vermerk in der Alt-Spec (Nicht-Ziel „Keine Änderung an `rules/1-generic/commit-conventions.md`“ aufgehoben per User-Entscheidung 2026-11-19) und Trailer-Zeile am Dateiende von `rules/1-generic/commit-conventions.md`. Deren Rolle in diesem Plan: Task 4 (Amendment ergänzt/konsolidiert) und Task 5 (Pin-Pass).

### Ziel

- Eine reine Funktion prüft, ob der Footer einer Commit-Message jeden konfigurierten Trailer (`commit.trailers`) wörtlich und genau 1x enthält.
- Aufruf über `sync.py --check-commit-msg <datei>`, nutzbar als Git-`commit-msg`-Hook (manuell verdrahtet), als Selbst-Check der `git`-Rolle oder in CI.
- Exit-Vertrag: 0 = ok / nichts zu prüfen / nur Warnungen, 1 = Verstoß (Token fehlt oder doppelt), 2 = Prüffehler (fail-closed).
- Rule-Zeile: `rules/1-generic/commit-conventions.md` nennt die Trailer-Konvention (Vorrang: expliziter Auftrag > Projekt-Config > Harness-Attribution).

### Nicht-Ziele

- Kein Eingriff in `hooks/1-generic/orchestrator-guard-impl.sh` oder andere Hooks; keine neue Hook-Registrierung.
- Keine automatische Installation eines Git-`commit-msg`-Hooks durch sync.py (Default c).
- Kein Rewriting/Autofix der Message; nur Befund.
- Keine dynamischen Trailer (`Claude-Session:`), keine Provider-/Modellnamen im Code.
- Keine Änderung an Agent-Templates, `render_auto_commit_block`, Schema oder Admin-UI. (Die Rule-Datei ist Ausnahme: Task 5.)

### Entwurfswahl (kleinste Lösung)

| Option | Aufwand | Bewertung |
|---|---|---|
| A: Funktion in `commit_trailers.py` + CLI-Flag | 3 Quellen | **gewählt**: kein Hook-Eingriff, Stdlib, testbar |
| B: Prüfung in `orchestrator-guard-impl.sh` (neben BOM-Gate #842) | Hook + Python-Scan + Config-Zugriff im Hook | verworfen: Hook per ac01-Hash und Registrierungs-Invariante gepinnt, kennt `project.yaml` nicht, widerspricht Alt-Spec-Nicht-Ziel frontal |
| C: nur Doku/Prompt | 0 Code | erfüllt die Nutzerentscheidung nicht |

### Interface Contracts

Python 3.9-kompatibel, nur Stdlib, provider-agnostisch.

**C1 — `scripts/lib/commit_trailers.py`**

- `def check_commit_message(message: str, cfg: dict) -> Tuple[List[str], List[str]]` — liefert `(errors, warnings)`; wirft nie.
  - Soll-Trailer = `render_commit_trailers(cfg).split("\n")`; leer → `([], [])`.
  - Footer = letzter Absatz nach Entfernen von Kommentarzeilen (`#`-Zeilen) und Trailing-Whitespace; `\r\n` normalisiert; führendes BOM → Error `"commit message starts with a UTF-8 BOM"` (Dopplung zu #842 bewusst).
  - Je Soll-Trailer, wörtlicher Vergleich (Token-Schreibweise exakt wie konfiguriert):
    - Token fehlt im Footer komplett → Error `"commit trailer missing: <zeile>"`.
    - Genau diese Zeile >1x → Error `"commit trailer duplicated: <zeile>"`.
    - Token kommt im Footer nur mit **anderem Wert** vor → **Warnung** `"commit trailer token '<Token>' has a different value (brief override?)"`, kein Error (Brief > Config laut Alt-Spec; Nutzerentscheidung 3).
  - Message ohne Footer-Absatz (Einzeiler) → Error „missing“ je Soll-Trailer.
- Kein `format_findings`: Ausgabe über `log` im Handler.

**C2 — `scripts/lib/cli_commands.py`**

- `def _handle_check_commit_msg(ctx) -> None` (Muster `_handle_validate_spec_plan`, `spec_plan_validate.py:139`): liest Datei `ctx.args.check_commit_msg` (`-` = stdin), Config `ctx.config`; ruft `check_commit_message`; `log.warning("commit-msg [ERROR] …")` / `[WARN] …`; `sys.exit(1)` nur bei Errors, sonst `sys.exit(0)` (Warnungen mit Hinweis, Exit 0). Datei nicht lesbar/nicht UTF-8 → `log.error`, `sys.exit(2)`. Schreibt keine Dateien, kein Sync-Tail.

**C3 — `scripts/sync.py`**

- `parser.add_argument("--check-commit-msg", metavar="FILE", help=…)` neben `--validate-spec-plan` (`:375`); Dispatch-Eintrag `(lambda a: a.check_commit_msg is not None, _handle_check_commit_msg)` neben `:839`; Import aus `lib.cli_commands`.

**Exit-Vertrag**

| Fall | Exit | Ausgabe |
|---|---|---|
| Kein `commit.trailers` konfiguriert (fail-open) | 0 | nichts |
| Ungültiger `commit`-Block | 0 | Hinweis `use sync.py --validate` |
| Alle Trailer je 1x wörtlich | 0 | nichts |
| Token vorhanden, Wert weicht ab | 0 | `[WARN]` mit Hinweis (Brief-Override?) |
| Token fehlt / Trailer doppelt / BOM | 1 | `[ERROR]` |
| Prüffehler (Datei, Parse) | 2 (fail-closed) | `log.error` |

- Einstufung: **Convention boundary**; `--no-verify`, Amend nach dem Hook und `-F`-Umgehung bleiben möglich.

### Datenfluss

- Eingabe: Message-Datei (Git übergibt `.git/COMMIT_EDITMSG`) + `commit.trailers` aus `project.yaml`.
- Verarbeitung: `check_commit_message` → `(errors, warnings)`.
- Ausgabe: Log-Zeilen und Exit-Code. Persistenz: keine.

### Acceptance Criteria

1. Given `commit.trailers` leer/fehlend, When `check_commit_message(<beliebig>, cfg)`, Then `([], [])`; CLI Exit 0.
2. Given Footer mit allen konfigurierten Trailern je 1x wörtlich, When geprüft, Then keine Errors/Warnings, Exit 0.
3. Given Message, in der ein konfigurierter Token im Footer fehlt, When geprüft, Then Error `commit trailer missing: <zeile>` und Exit 1.
4. Given Trailer doppelt im Footer, When geprüft, Then Error `commit trailer duplicated` und Exit 1.
5. Given gleicher Token mit anderem Wert (z. B. falscher Modellname), When geprüft, Then **Warnung** `different value`, kein Error für diesen Trailer, Exit 0 mit Hinweis auf stderr/Log.
6. Given Trailer steht im Body statt im letzten Absatz (Token nicht im Footer), When geprüft, Then Error missing, Exit 1.
7. Given Message beginnt mit UTF-8 BOM, When geprüft, Then Error BOM, Exit 1.
8. Given nicht lesbare Datei, When CLI, Then Exit 2.
9. Given `--check-commit-msg -` mit stdin, When CLI, Then wie Datei.
10. Given Stand nach Task 4 (vor Task 5), When `python3 scripts/sync.py --validate`, Then Exit 0; `git diff --stat` (gegen Stand vor Task 1, ohne die bereits vorhandene Working-Tree-Änderung an Rule/Alt-Spec) zeigt keine Änderung an `hooks/`, `agents/`, `tests/fixtures/`, `standalone/`, `.meta-config/generated-file-hashes.json`.
11. Given `tests/test_provider_agnostic_dispatch.py`, When ausgeführt, Then grün (kein Provider-/Modellname in `scripts/lib/commit_trailers.py`).
12. Given Python 3.9, When `tests/test_commit_trailers.py`, `tests/test_commit_msg_check_cli.py` laufen, Then grün.
13. Given Task 5 abgeschlossen, When `python3 -m pytest tests -q`, Then grün (inkl. der 6 gelisteten Pin-Tests und AC-T4) und `git diff --stat` enthält ausschließlich die in Task 5 gelisteten Dateien.
14. Given #1168, When geschlossen, Then AK2-Beleg liegt vor (siehe Hinweis #1168; kein Task in diesem Plan).

### Entscheidungen / Defaults

Entscheidungen des Users (relayed):

1. Option C: die Rule `rules/1-generic/commit-conventions.md` wird **Task 5** dieses Plans; **ein** Pin-Pass (sync + Rebaseline) deckt Rule und Check-Change ab. Bis `Status: APPROVED`: kein `sync.py`, keine Rebaseline, Rule-Änderung bleibt uncommitted.
2. Gleicher Token mit abweichendem Wert = **WARNUNG** (Exit 0 mit Hinweis), kein Error. Fehlender Token = Error (Exit 1).
3. #1168 wird separat jetzt über AK2-Beleg geschlossen (Commits `bb8f3b1e` / `ae282297`); der frühere Beleg-Task entfällt (Hinweis unten).

Defaults (zur Bestätigung):

- (a) Klasse M.
- (c) Kein automatisch installierter `commit-msg`-Hook; manuelle Verdrahtung/CI.
- (d) Änderung der Alt-Spec per Amendment (keine neue ablösende Spec).
- (e) AK2-Beleg durch die `git`-Rolle.
- (f) Beleg-Commit auf dem Feature-Branch.

Fragen an den User beim Freigeben:

1. Klasse M (Default a) bestätigen?
2. Kein auto-installierter `commit-msg`-Hook (Default c) bestätigen?
3. Amendment der Alt-Spec statt neuer Spec (Default d) bestätigen?
4. AK2-Evidenz durch die `git`-Rolle (Default e) bestätigen?
5. Evidenz-Commit auf dem Feature-Branch (Default f) bestätigen?
6. Zusätzlich: ausdrückliches OK für den Pin-Pass in Task 5 (`python3 scripts/sync.py`, Rebaseline AC-01-Hashes, Compact-Golden, AC-T4-Digest)?

### Hinweis #1168

- #1168 wird separat per AK2-Beleg geschlossen (Commits `bb8f3b1e`, `ae282297`). Kein Task in diesem Plan; nach Abschluss nur Verweis im PR/Issue. Optional: Check aus diesem Change gegen eine reale Commit-Message laufen lassen und im Issue vermerken.

### Risiken

- **Gepinnte Dateien — Hooks nicht berührt:** `hooks/1-generic/orchestrator-guard-impl.sh` und `.agents/hooks/orchestrator-guard-impl.sh` bleiben unverändert (Pins: `tests/fixtures/ac01-baseline/hashes.json`, `tests/test_ac01_render_identity.py`, `tests/test_orchestrator_guard_hook.py`, `tests/test_hook_registration_invariant.py`, `tests/test_opencode_v2_surface.py`, …).
- **Rule-Änderung bricht Pins (Task 5):** Die Rule-Zeile verändert gerenderte Artefakte (`CLAUDE.md`-/`AGENTS.md`-Managed-Block, Compact-Golden). Erwartet brechende Tests (genau 6):
  1. `tests/test_compact_rule_channels.py::test_no_opt_in_render_is_byte_identical_to_the_committed_block`
  2. `tests/test_gate_card_compact.py::test_full_and_no_key_render_byte_identical`
  3. `tests/test_gate_card_compact.py::test_compact_render_matches_compact_golden`
  4. `tests/test_context_compact_mode.py::test_committed_agents_md_equals_configured_mode_render`
  5. `tests/test_ac01_render_identity.py::test_ac01_render_identical_to_manifest`
  6. `tests/test_ac01_render_identity.py::test_ac01_detects_drift`
- **STOP-and-ask:** bricht ein **anderer** Pin als diese 6 (oder AC-T4 liefert nicht genau die erwartete Digest-Änderung), Task 5 sofort stoppen und beim User rückfragen; nicht rebaselinen.
- Reine Python-Änderungen in `scripts/lib/` (Tasks 1–2) verändern keine Goldens. Flag-/CLI-Referenz-Pins (z. B. `tests/test_cli_smoke_multi_provider.py`) in Task 2 per Testlauf feststellen; Rebaseline nur mit User-OK.
- Context-Budget: `tests/test_context_budgets.py` nach Task 5 zur Kontrolle laufen lassen.
- Prompt-Konvention bleibt zusätzlich bestehen; Check ist Netz, kein Ersatz.
- Python-3.9-Bug-Klasse: keine `X | Y`-Annotationen in neuem Code.
- Issue-Texte unverifiziert: Issue-Texte #1247/#1168 vor Freigabe gegen Entwurf prüfen (lesend durch git/feedback-Rolle).

### Trace-Anker

spec-id: SPEC-1247-trailer-value-check-2026-11-19

## Plan

**Goal:** Konfigurierte Commit-Trailer gegen eine echte Commit-Message prüfen (#1247) und die Rule-Zeile samt einmaligem Pin-Pass einbringen.
**Architecture:** reine Funktion `check_commit_message` in `scripts/lib/commit_trailers.py`; neues CLI-Flag in `sync.py` + Handler in `cli_commands.py`; kein Hook-/Template-Eingriff; Rule-Zeile + Pin-Pass als letzter Task.
**Tech Stack:** Python 3.9 (Stdlib), pytest.
**Spec:** docs/plans/2026-11-19-1247-trailer-value-check.md (Abschnitt Spec, Status DRAFT; Plan erst nach `Status: APPROVED` ausführbar)

## Global Constraints

- Ausführung erst nach Freigabe durch den User; bis dahin kein Code, kein `sync.py`, keine Rebaseline.
- Python 3.9, nur Stdlib, kein Provider-/Modellname in `scripts/lib`.
- Branch `fix/1247-1168-trailer-contract`; kein Amend, kein Force-Push; Push/Tag nur Rolle `git`.
- Keine Änderung an Hooks, Agent-Templates, Fixtures, `standalone/`, `generated-file-hashes.json` **vor Task 5**; Rebaseline nur in Task 5 und nur mit ausdrücklichem User-OK.
- Alle Tasks sequentiell; Dateien je Task disjunkt; Pin-Pass (Task 5) ist letzter Task und läuft genau einmal.
- Commit-Betreff Englisch, Imperativ, ≤72 Zeichen; Trailer laut Brief wörtlich 1x.

## File Structure

- Modify: `scripts/lib/commit_trailers.py` — `check_commit_message` (Task 1)
- Modify: `tests/test_commit_trailers.py` — Unit-Tests (Task 1)
- Modify: `scripts/lib/cli_commands.py` — `_handle_check_commit_msg` (Task 2)
- Modify: `scripts/sync.py` — Flag + Dispatch (Task 2)
- Create: `tests/test_commit_msg_check_cli.py` — CLI-Tests (Task 2)
- Modify: `CHANGELOG.md` — `### Added` (Task 3)
- Modify: `docs/specs/2026-11-15-git-trailer-contract-spec.md` — Amendment (Task 4)
- Modify: `rules/1-generic/commit-conventions.md` — Trailer-Zeile (Task 5; bereits im Working Tree)
- Regenerate (Task 5): `CLAUDE.md`, `AGENTS.md` und weitere per `python3 scripts/sync.py` erzeugte Artefakte; `tests/fixtures/ac01-baseline/hashes.json` (per-Eintrag), `tests/fixtures/compact-golden/agents-managed.md`; Docstring-Log in `tests/test_ac01_render_identity.py` und `tests/test_gate_card_compact.py`; Digest-Pin in `tests/test_opencode_v2_surface.py`

---
pipeline_stages:
  implement: 1
---

## Tasks

### Task 1: check_commit_message
**Agent:** developer
**Depends on:** keine
**Files:**
- Modify: `scripts/lib/commit_trailers.py`
- Modify: `tests/test_commit_trailers.py`

**Interfaces:** Produces: `check_commit_message(message: str, cfg: dict) -> Tuple[List[str], List[str]]`; Consumes: `render_commit_trailers`.
**AC:** 1–7, 11, 12 (Teil).
- [ ] Step 1: Tests schreiben (rot): AC 1–7 inkl. CRLF, Kommentarzeilen, Einzeiler, BOM; Token mit anderem Wert → Warnung ohne Error.
- [ ] Step 2: Funktion implementieren (Footer = letzter Absatz; wörtlicher Zeilenvergleich).
- [ ] Step 3: `python3 -m pytest tests/test_commit_trailers.py tests/test_provider_agnostic_dispatch.py -q` grün.
- [ ] Step 4: Commit `feat: add commit message trailer check`

### Task 2: CLI --check-commit-msg
**Agent:** developer
**Depends on:** 1
**Files:**
- Modify: `scripts/lib/cli_commands.py`
- Modify: `scripts/sync.py`
- Create: `tests/test_commit_msg_check_cli.py`

**Interfaces:** Produces: `_handle_check_commit_msg(ctx)`, Flag `--check-commit-msg FILE` (`-` = stdin), Exit 0/1/2; Consumes: `check_commit_message` (Task 1).
**AC:** 1, 5, 8, 9, 10, 12.
- [ ] Step 1: CLI-Tests (rot): ok → 0, Token fehlt → 1, abweichender Wert → 0 mit `[WARN]`, nicht lesbar → 2, stdin, kein Trailer konfiguriert → 0.
- [ ] Step 2: Handler und Flag/Dispatch implementieren.
- [ ] Step 3: `python3 -m pytest tests/test_commit_msg_check_cli.py tests/test_cli_smoke_multi_provider.py -q` und `python3 scripts/sync.py --validate` Exit 0. Pins/Flag-Listen-Tests, die rot werden, melden statt rebaselinen.
- [ ] Step 4: Commit `feat: add sync --check-commit-msg trailer gate`

### Task 3: CHANGELOG
**Agent:** documenter
**Depends on:** 2
**Files:**
- Modify: `CHANGELOG.md`

**Interfaces:** Produces: `### Added` unter `## [Unreleased]`; Consumes: Tasks 1–2.
**AC:** Nachvollziehbarkeit (Flag, Exit-Codes inkl. Warnung bei abweichendem Wert, Convention boundary, Default = no-op, Nicht-Breaking; Rule-Zeile erwähnen).
- [ ] Step 1: Eintrag schreiben.
- [ ] Step 2: `python3 scripts/sync.py --validate` Exit 0.
- [ ] Step 3: Commit `docs: changelog for --check-commit-msg`

### Task 4: Alt-Spec-Amendment
**Agent:** concept-specifier
**Depends on:** 3
**Files:**
- Modify: `docs/specs/2026-11-15-git-trailer-contract-spec.md`

**Interfaces:** Produces: ersetztes Nicht-Ziel + Risiko-Verweis + Änderungs-Eintrag mit Datum (bestehender Rule-Override-Vermerk bleibt, wird konsolidiert); Consumes: Abschnitt „Konflikt mit der APPROVED-Spec“.
**AC:** `python3 scripts/sync.py --validate-spec-plan` ohne neue Findings; `Status: APPROVED` der Alt-Spec unverändert.
- [ ] Step 1: Amendment einarbeiten (Default d).
- [ ] Step 2: `python3 scripts/sync.py --validate-spec-plan` ohne Findings.
- [ ] Step 3: Commit `docs: amend trailer spec for commit msg check`

### Task 5: Rule-Zeile + einmaliger Pin-Pass (LETZTER Task)
**Agent:** developer
**Depends on:** 4
**Files:**
- Modify: `rules/1-generic/commit-conventions.md` (Rule-Text liegt bereits im Working Tree; hier committen)
- Regenerate: per `python3 scripts/sync.py` erzeugte Artefakte (`CLAUDE.md`, `AGENTS.md`, weitere Provider-Rule-Kopien)
- Modify: `tests/fixtures/ac01-baseline/hashes.json` (**nur betroffene Einträge**, per-Eintrag-Rebaseline nach Präzedenz im Docstring von `tests/test_ac01_render_identity.py`, Eintrag #1300) + Docstring-Log-Eintrag
- Modify: `tests/fixtures/compact-golden/agents-managed.md` + Rebaseline-Log in `tests/test_gate_card_compact.py` (Docstring erlaubt Regenerierung „only for a justified rebaseline, documented below“: Compact-Profil über `_render` rendern, Fixture schreiben, Log-Eintrag ergänzen)
- Modify: Digest-Pin AC-T4 in `tests/test_opencode_v2_surface.py`

**Interfaces:** Produces: committete Rule-Zeile, regenerierte Artefakte, rebaselinierte Pins; Consumes: Tasks 1–4.
**AC:** 13.
- [ ] Step 0: **Voraussetzung:** Plan `Status: APPROVED` und ausdrückliches User-OK für `sync.py` + Rebaseline. Fehlt eines → Task nicht starten.
- [ ] Step 1: Baseline: `python3 -m pytest tests -q`; erwartet rot ist nur die Menge der 6 Tests (siehe Risiken), sofern Rule-Änderung im Working Tree und Artefakte noch nicht regeneriert. Weicht die Menge ab → STOP und beim User rückfragen.
- [ ] Step 2: Einmaliger Lauf `python3 scripts/sync.py` (ohne weitere Flags). Heilt `test_compact_rule_channels::test_no_opt_in_render_is_byte_identical_to_the_committed_block` und `test_context_compact_mode::test_committed_agents_md_equals_configured_mode_render`.
- [ ] Step 3: Compact-Golden regenerieren (Docstring-Anleitung in `tests/test_gate_card_compact.py`) und Rebaseline-Log-Eintrag ergänzen → heilt `test_gate_card_compact::test_full_and_no_key_render_byte_identical` und `::test_compact_render_matches_compact_golden`.
- [ ] Step 4: AC-01-Hashes per-Eintrag rebaselinen (nur Einträge, deren Render sich durch die Rule-Zeile geändert hat; Präzedenz #1300), Log-Eintrag im Docstring → heilt `test_ac01_render_identical_to_manifest` und `::test_ac01_detects_drift`.
- [ ] Step 5: AC-T4-Digest in `tests/test_opencode_v2_surface.py` neu pinnen (nur falls rot/abweichend).
- [ ] Step 6: `python3 -m pytest tests -q` komplett grün; `git diff --stat` zeigt nur die oben gelisteten Dateien. Bricht ein **anderer** Pin → STOP, melden, nicht rebaselinen.
- [ ] Step 7: Commit `chore: add commit trailer rule line and rebaseline pins`

## Risiken

- Siehe Spec-Abschnitt Risiken. Task 5 hängt an Freigabe und explizitem Pin-OK; Pin-Pass läuft genau einmal am Ende.
- Re-Planning: nach Task 2 prüfen, ob Annahmen (kein Pin auf Flag-Liste, kein Hook-Eingriff) halten; vor Task 5 prüfen, ob sich die Menge brechender Pins seit diesem Entwurf geändert hat (z. B. durch gemergte PRs auf `main`).

## Self-Review

- Jeder Task mappt auf genau eine Rolle; AC messbar (Exit-Code, Meldungstext, Diff-Stat, Testliste).
- Dateien je Task disjunkt, alle Tasks sequentiell; Pin-Pass nur in Task 5.
- `pipeline_stages` deckt `implement` ab.
- Aufwand: `effort-estimator` (Textverweis, nicht berechnet).
- Status DRAFT: `Status: APPROVED` darf nur der User setzen.
