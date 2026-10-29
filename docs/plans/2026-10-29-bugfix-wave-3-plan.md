---
pipeline_stages:
  implement: 1
---

# Bugfix-Welle 3 (Rest-Welle) — Implementation Plan

> Status: geplant (Entwurf), Revision 3.2 (2026-10-29)
>
> **Freigabevermerk:** Die zugehörige Spec trägt `Status: Entwurf`. Dieser Plan ist **nicht ausführbar**, bis der Nutzer bzw. `concept-reviewer` die Spec auf `Status: APPROVED` setzt und diesen Plan freigibt. Der Approval-Marker wird nie vom Planer gesetzt.

**Goal:** Die vier nach PR #1038 verbliebenen Restpunkte der Welle 3 in zwei PRs schließen: PR A lässt den Fork-Bomb-Scanner Namen exakt prüfen und an der Body-Grenze fail-closed sein und dokumentiert die `}`-Lücke (R1, #943-Rest, Q3 (b)/Q10, mit genau einem AC-01-Rebaseline); PR B schreibt die drei Managed-Indizes über `write_atomic` (R2, #961-Rest), ergänzt den Host-Header-Hinweis und korrigiert die `--allowed-hosts`-Doku (R3, #897-Rest) und dokumentiert zcode ZC-1 als wontfix (R4, #856) — ohne Rebaseline.
**Architecture:** Kein neues Subsystem. PR A ändert nur die emittierte Python-Funktion `is_fork_bomb` in `hooks/1-generic/lib/hook_common.sh`, eine Meldungszeile in `orchestrator-guard-impl.sh` und einen Punkt in »Bekannte Grenzen« von `rules/1-generic/branch-guard.md`; PR B tauscht drei `Path.write_text`-Aufrufe gegen das vorhandene `io.write_atomic`, erweitert zwei Hinweistexte und korrigiert Hilfe-/Doku-/Schema-Texte.
**Tech Stack:** Bash-Hooks mit eingebettetem Python 3.9+, Python-Stdlib, pytest, Markdown.
**Spec:** `docs/specs/2026-10-29-bugfix-wave-3-spec.md`
**Spec-ID:** `spec-id: SPEC-bugfix-wave-3` (Status Entwurf, Revision 3.2, 2026-10-29)
**Tracking:** Refs #943 (R1), Refs #961 (R2), Refs #897 (R3), #856 (R4; Schließen durch den User)

## Änderungslog des Plans

- **Rev. 2 (2026-10-29):** Plan auf Rest-Welle umgebaut. Entfallen: PR 0/0a/0b (Tasks 1–3, 34), PR 1 (Tasks 4–14), PR 2 (15–21), PR 4 (22–27), PR 3 (28–33), bedingte Rebaselines (35, 36) — deren Code-Scope ist mit PR #1038 auf `main` (Verifikationsnachweis: Spec »Stand nach PR #1038«). Task-IDs neu ab 1; AC-IDs neu (AC-A.n, AC-B.n).
- **Rev. 3 (2026-10-29):** Review-Findings P-1…P-8 und Spec Rev. 3 eingearbeitet; Task-Nummern unverändert. Task 1 auf Q3-Default (b) (Rot-Zählung `4 failed, 8 passed`, alle fünf Tests parametrisiert, `{`-Kette im Linearitätstest); Task 2 Grenzphrase `first 512`; Task 3 mit AC-A.10 (`rules/1-generic/branch-guard.md`) und `# changelog:` nur bei `hook_common.sh`; Task 4 Patch je Eintrag statt `--write`, Drift 13 Einträge; Task 6 mit zwei Charakterisierungstests (`3 failed, 2 passed`); Task 7 inkl. `config/project-config.schema.json` und Abschluss-Grep. Neu Q10 und Folge-Issue-Entwurf im Status-Abschnitt.
- **Rev. 3.1 (2026-10-29):** Minor-Findings eingearbeitet: Drift-Zahlen `13 + k` (Task 4), `_MAX_FUNC_NAME`-Grep-Bereich (Task 1), AC-A.10 ≥ 1 Treffer, AC-01-Lauf aus Task 6 Step 5 entfernt (in Task 10 Step 1 enthalten), CR-Byte-Formulierung, Wildcard-Phrasen-Hinweis (Task 7), Folge-Issue-Hinweis im Status.
- **Rev. 3.2 (2026-10-29):** User-Entscheidungen Q3/Q5/Q9/Q10 (vom User bestätigt): Q3 = (b), Q5 = Doku an Code (»Replaces«, Code unverändert), Q9 = »Refs«, Q10 = (ii) Folge-Issue durch User + »Bekannte Grenzen«. Gates in Entry, Task 1, Task 7 entschärft (Varianten bleiben Alternativen, nicht blockierend); Q-Tabelle aktualisiert.

## Status — ehemaliger PR 0 (Housekeeping, kein Agent-Task)

- Issue-Änderungen führt **kein** Agent aus. Stand (gh lesend, 2026-10-29): #948, #950, #952, #953, #1033, #943, #944, #961, #951, #954, #1031, #983, #1037, #1034, #1036, #897 CLOSED; #1035 NOT_PLANNED.
- #207, #534, #865, #962: offen — der User schließt sie selbst per `! gh issue close <N> …`.
- #953-Folge-Issue: legt der User an, Body `.tmp/issue-953-followup.md` (vorhanden).
- #856: OPEN — nach Merge von PR B schließt der User mit dem Kommentar-Entwurf aus Task 10 (Spec Q6).
- #971: offen, Kriterium fehlt (Spec Q8). #192: bleibt offen.
- **Hinweis (möglicher Folge-Issue, nicht Scope):** Der Index bleibt stale, nachdem alle Einträge entfernt wurden; nur Text, keine Änderung in dieser Welle.
- **Q10-Folge-Issue (`}`-Lücke):** legt der User an (Q10 = (ii), vom User bestätigt 2026-10-29); kein Agent führt `gh issue create` aus. Text-Entwurf (Englisch), nicht ausgeführt:

  > **Title:** `fix: fork-bomb scan ends a function body at the first '}'`
  >
  > **Problem.** `is_fork_bomb` in `hooks/1-generic/lib/hook_common.sh` (emitted by `hook_shell_scan_py`) takes the function body to end at the first unquoted `}` after `{` (`command.find('}', j + 1, j + 1 + _MAX_FUNC_BODY)`), without brace nesting. A fork bomb whose body contains a `}` before the self-call is not detected and passes the destructive gate of `orchestrator-guard-impl.sh` (allow instead of block).
  >
  > **Evidence (2026-10-29, Python 3.13, function level after `strip_quoted`, `origin/main` `3e340690`).** `f(){ : ${x}; f|f& };f` → `False`; `f(){ { :; }; f|f& };f` → `False`. Both stay `False` with the wave-3 PR A contract (exact name scan, body fail-closed at 512 characters, SPEC-bugfix-wave-3 Q3 (b)). Documented as a known gap in `rules/1-generic/branch-guard.md` ("Bekannte Grenzen", wave 3 PR A, AC-A.10).
  >
  > **Proposal.** End the body at the depth-matching `}` inside the existing 512-character window (count `{`/`}`), fail closed when the window is exhausted. A scratch prototype on top of the PR A contract detects both examples, keeps all wave-3 cases unchanged and stays linear (`"f(){ x} " * 60000` 119 ms, 600 000-character name 113 ms). False positives from an unquoted `{` in a long body: not measured.
  >
  > **Acceptance.** Both examples → `True`; existing fork-bomb tests in `tests/test_hook_common_lib.py` / `tests/test_orchestrator_guard_hook.py` stay green; linearity tests stay < 1 s; the gap entry in `rules/1-generic/branch-guard.md` is removed; one AC-01 rebaseline (hook + rule renders).
  >
  > Refs #943.

## Entry-/Exit-Kriterien (gesamt)

**Entry (vor Task 1 bzw. Task 6):**
1. Spec `Status: APPROVED` und dieser Plan freigegeben.
2. Vor PR A: Q4 (#945) und Q7 (`function NAME`-Form) entschieden bzw. Default akzeptiert; Q3 (b), Q10 (ii), Q5 und Q9 sind vom User bestätigt (2026-10-29).
3. `origin/main` = `3e340690` oder neuer; Arbeitsbranch je PR durch den `git`-Agenten angelegt. Kein Code auf `main` (`.claude/rules/branch-guard.md`).

**Exit (gesamt):** PR A und PR B gemergt (A vor B); je PR die eigenen Exit-Kriterien erfüllt; `python3 -m pytest tests -q` ohne `failed`/`error` auf `main` nach dem zweiten Merge; alle Checkboxen gesetzt (Ledger = Plan-Datei, Skill `plan-ledger`).

## Global Constraints

- **Task-Format (maschinenlesbar):** `### Task <n>: <Titel>`; Felder `**Agent:**`, `**Depends on:**` (nur Task-Nummern dieses Plans oder `—`), `**Files:**`-Block mit je einer Zeile `- Create:`/`- Modify:` (Pfad in Backticks), `**Interfaces:**` einzeilig mit Produces/Consumes.
- **Kein `gh`-Schreibaufruf, keine Issue-Änderung, keine Git-Mutation durch ausführende Agenten.** Git-Lesebefehle (`git status`, `git diff`, `git log`, `git diff --stat` in Task 4) sind erlaubt; blockt der Orchestrator-Guard einen Lesebefehl false-positive (z. B. `git branch -a --contains`), stoppen, exakten Befehl melden und über den `git`-Agenten ausführen lassen. Branch/Push/PR/Rebase/Revert/Zurücksetzen nur über den `git`-Agenten; Commits durch die per `auto_commit` freigeschaltete Rolle nach Secret-Scan.
- **TDD (D4):** Jeder Code-Task beginnt mit Tests, die vor dem Fix nachweislich rot sind (erwartete Zählung im Step); ausdrücklich als Charakterisierung markierte Fälle sind vorher und nachher grün und werden im PR so ausgewiesen. Läufe mit mehreren erwarteten Fails **ohne** `-x`. Rot-Lauf im PR festhalten.
- **Fail-closed:** Kein Fix öffnet einen neuen Fail-open-Pfad. Hooks bleiben Convention boundary (`.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary`).
- **Rebaseline-Regel (Rest von D5):** Rebaseline nur auf einem auf aktuellen `origin/main` rebasten Branch (durch den `git`-Agenten), höchstens **einmal** pro PR, nie per Konfliktauflösung in `tests/fixtures/ac01-baseline/hashes.json` oder `_FIXTURE_TREES`. **Kein `--write`** (`tests/test_ac01_render_identity.py` Docstring :12-13 erlaubt es nur auf sauberem, unverändertem `main`): Patch je Eintrag, jeder neue Digest unabhängig mit dem Harness-eigenen `_hash_file` aus den gerenderten Bytes berechnet, Zahl der unberührten Zeilen im Log (Präzedenz Docstring :363, :399, :439). `AC01_EXCEPTIONS` nicht erweitern. Nur PR A hat einen Rebaseline.
- **Version-Bump nach Skill `conventions` (`.claude/skills/conventions/SKILL.md`) mit Hook-Präzedenz:** Hook-Dateien tragen `# version:`; `# changelog:` nur ergänzen, wo die Datei bereits einen Header-Changelog hat (`hook_common.sh` ja, :5; `orchestrator-guard-impl.sh` nein — keinen anlegen). Regeldateien unter `rules/` haben keine Versionszeile. Verhaltensänderung eines Hooks = Minor (Präzedenz `CHANGELOG.md` [Unreleased]: `hook_common.sh` 1.4.0, `repo-containment-impl.sh` 1.5.0), reiner Meldungs-/Kommentartext = Patch. `VERSION` wird **nicht** geändert (nur Release-PRs, `git log -- VERSION`: ausschließlich `chore: release …`). Nach Änderung an `hooks/` → `python3 scripts/sync.py` (Self-Sync).
- **Commits:** Englisch, Conventional Commits nur `feat`/`fix`/`chore` (`.claude/rules/commit-conventions.md`), Subject ≤ 72 Zeichen (alle unten nachgezählt), Imperativ, ohne BOM. Dokumente Deutsch; `docs/providers/zcode.md` und `docs/howto/admin-ui-remote-access.md` sind englisch und bleiben englisch.
- **Python 3.9-kompatibel in `scripts/` und `tests/`:** kein `X | Y` in neuen Annotationen (stattdessen `Optional[...]`/`Union[...]`, auch in Testhelfern), kein `match`, kein `write_text(newline=)`.
- Keine `isolation: "worktree"`; Schreiben nur im Projektroot und `.tmp/` (Repo-Containment).
- Provider-agnostisch: keine `if provider == "Name"`-Zweige in `scripts/lib`.
- Zeilennummern sind Orientierung (Stand `3e340690`); jeder Task, der Zeilen zitiert, beginnt mit einem `Grep` auf das Symbol.

## Ausführungsmodell

- **PR-Schnitt:** PR A `fix/fork-bomb-window-gap` = R1 inkl. AC-A.10 (einziger Hook- und Regel-Eingriff → einziger Rebaseline + Self-Sync; isolierter Revert). PR B `fix/index-lf-admin-hint-zcode-doc` = R2 + R3 + R4 (Python/Doku/Schema, kein gerenderter Output, kein Rebaseline).
- **Parallelität:** PR A (Tasks 1–5) und PR B (Tasks 6–10) sind dateidisjunkt bis auf `CHANGELOG.md` (Task 3 / Task 9) → parallel entwickelbar. Merge seriell: **PR A zuerst** (D3, Security), dann PR B auf frischem `main`; `CHANGELOG.md`-Append-Konflikt im PR B manuell lösen (kein Rebaseline-Konflikt, PR B berührt `hashes.json`/`_FIXTURE_TREES` nicht).
- **DAG PR A:** `1 → 2 → 3 → 4 → 5`.
- **DAG PR B:** `parallel_group: gB` = Tasks 6, 7, 8 (ownership-disjunkt: `hooks.py`+`hook_plugins.py`+`test_newline_normalization.py` / `admin-server.py`+`test_admin_server.py`+How-to+`project-config.schema.json` / `zcode.md`); `(6, 7, 8) → 9 → 10`.

## File Structure

**Modify (PR A):**
- Modify: `hooks/1-generic/lib/hook_common.sh` — `is_fork_bomb` Name exakt + Body fail-closed, Header-Kommentar, `# version:`/`# changelog:` (Tasks 1, 3)
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh` — Grenzen-Zeile im Destructive-Gate, `# version:` (Tasks 2, 3)
- Modify: `tests/test_hook_common_lib.py`, `tests/test_orchestrator_guard_hook.py` — Regressionstests (Tasks 1, 2)
- Modify: `rules/1-generic/branch-guard.md` — »Bekannte Grenzen« um die `}`-Lücke (Task 3, AC-A.10)
- Modify: `CHANGELOG.md` (Task 3)
- Modify: `tests/fixtures/ac01-baseline/hashes.json`, `tests/test_ac01_render_identity.py`, `tests/test_opencode_v2_surface.py` — Rebaseline (Task 4)
- Modify: `.agents/hooks/lib/hook_common.sh`, `.agents/hooks/orchestrator-guard-impl.sh`, `.meta-config/generated-file-hashes.json` — Self-Sync (Task 4)

**Modify (PR B):**
- Modify: `scripts/lib/hooks.py`, `scripts/lib/hook_plugins.py`, `tests/test_newline_normalization.py` (Task 6)
- Modify: `scripts/admin-server.py`, `tests/test_admin_server.py`, `docs/howto/admin-ui-remote-access.md`, `config/project-config.schema.json` (Task 7)
- Modify: `docs/providers/zcode.md` (Task 8)
- Modify: `CHANGELOG.md` (Task 9)

**Create (Scratch, nicht committen):**
- Create: `.tmp/wave3-prA-description.md` (Task 5), `.tmp/wave3-prB-description.md`, `.tmp/wave3-issue-856-close.md` (Task 10)

## Step-Agent-Map (plan-driven implement)

| Step | Task | Agent |
|---|---|---|
| 1 | R1 `is_fork_bomb` Name exakt, Body fail-closed | senior-developer |
| 2 | R1 Grenzen-Zeile im Destructive-Gate | developer |
| 3 | PR A Versionen, Changelog, »Bekannte Grenzen« | junior-developer |
| 4 | PR A Rebaseline und Self-Sync | developer |
| 5 | PR A Exit-Gate und PR-Text | developer |
| 6 | R2 Managed-Indizes über `write_atomic` | developer |
| 7 | R3 Host-Header-Hinweis, Hilfetext, How-to | developer |
| 8 | R4 zcode ZC-1 Notiz | junior-developer |
| 9 | PR B Changelog | junior-developer |
| 10 | PR B Exit-Gate, PR-Text, #856-Kommentar-Entwurf | developer |

> `pipeline_stages.implement = 1` → Step 1 (Task 1, `senior-developer`). Step = Task-Nummer. Alle Agents aus `allowed_agents` der Stage `implement` (`junior-developer`, `developer`, `senior-developer`, `frontend-component-engineer`). Auswertung: `scripts/lib/pipelines.py:parse_plan_ref`/`validate_plan_ref` (Frontmatter nur am Dateianfang).

---

## PR A — `fix/fork-bomb-window-gap` (R1)

**Branch:** `fix/fork-bomb-window-gap` (vom `git`-Agenten auf aktuellem `origin/main` angelegt).
**Entry:** Spec APPROVED; Q3 (b) und Q10 (ii) vom User bestätigt (2026-10-29); Q4, Q7 mit Default.
**Exit:** (1) `python3 -m pytest tests/test_hook_common_lib.py tests/test_orchestrator_guard_hook.py tests/test_ac01_render_identity.py tests/test_opencode_v2_surface.py -q` grün; (2) `python3 scripts/sync.py --validate` Exit 0; (3) `python3 -m pytest tests -q` ohne `failed`/`error`; (4) Versionen + `CHANGELOG.md` (AC-A.8) und »Bekannte Grenzen« (AC-A.10); (5) genau ein Rebaseline (AC-A.9); (6) `python3 scripts/consistency-check.py` ohne `hooks.stale-deployed-version`.
**Rollback:** `git revert` des Merge-Commits durch den `git`-Agenten (nimmt `hashes.json`/`_FIXTURE_TREES`/`.agents/hooks/*`/Regeltext mit); danach `python3 scripts/sync.py` für die lokalen `.claude/hooks/`- und Regel-Kopien. Folge: Fork-Bomben mit Namen > 64 bzw. Body > 512 passieren wieder (fail-open, Nutzer informieren).

### Task 1: R1 — `is_fork_bomb` Name exakt, Body-Grenze fail-closed
**Agent:** senior-developer · **Issue:** Refs #943 · **AC:** AC-A.1, AC-A.2, AC-A.3, AC-A.4, AC-A.5, AC-A.6
**Depends on:** —
**Gate:** Q3 (b) und Q10 (ii) vom User bestätigt (2026-10-29) — nicht blockierend. Vertrag unten gilt. Alternative (nur bei späterer Änderung der Entscheidung) Q3 (a): Varianten-AC der Spec (`"a"*65 + "(){ :; }"` und n = 20 000/300 000 → `1`, Test heißt `test_fork_bomb_fails_closed_on_long_function_name`, `_MAX_FUNC_NAME` bleibt, Rot-Zählung `7 failed, 5 passed`). Jede Abweichung von der bestätigten Entscheidung (a/c/i) → Stopp, Spec-/Plan-Revision; die Varianten-AC für (a) liegen vorbereitet in der Spec.
**Files:**
- Modify: `hooks/1-generic/lib/hook_common.sh`
- Modify: `tests/test_hook_common_lib.py`
**Interfaces:** Produces `is_fork_bomb(command: str) -> bool`: Rückwärts-Scan des Namens unbegrenzt (`_MAX_FUNC_NAME` entfällt), Name wird wie bisher per `_body_calls_itself_piped` geprüft; kein `}` in `command[j+1 : j+1+_MAX_FUNC_BODY]` (512) → `True`; Body endet weiter am ersten `}` (Q10, dokumentiert in Task 3); linear, keine Exception-Unterdrückung; Consumes `hook_shell_scan_py` (:431), einziger Aufrufer `orchestrator-guard-impl.sh:1157`.
- [ ] Step 1: Blast-Radius prüfen: `Grep` `is_fork_bomb` in `hooks/` und `scripts/` → genau Definition `hooks/1-generic/lib/hook_common.sh` (~:722) und Aufruf `hooks/1-generic/orchestrator-guard-impl.sh` (~:1157); `Grep` `hook_shell_scan_py` → Konsumenten `orchestrator-guard-impl.sh`, `repo-containment-impl.sh` (ruft `is_fork_bomb` nicht); `Grep` `_MAX_FUNC_NAME` in `hooks/`, `scripts/`, `tests/`, `.agents/` → nur `hook_common.sh` (:437, :743, :746) und die gerenderte Kopie `.agents/hooks/lib/hook_common.sh`; Treffer in `docs/` (Spec/Plan) und `.claude/` (gitignorte Deploy-Kopien) sind erwartet und ignorierbar. Weitere Treffer in den vier Pfaden = Geschwisterpfad → Stopp und melden.
- [ ] Step 2: Testhelfer `_scan` (`tests/test_hook_common_lib.py` ~:378) um `timeout: Optional[float] = None` erweitern (an `subprocess.run` durchreichen; `from typing import Optional`). Alle fünf Tests per `@pytest.mark.parametrize("expr,expected", [...], ids=[...])`; Eingaben im Subprozess per Ausdruck erzeugen (`expr` als Quelltext, nicht als Literal einbetten). Tests schreiben (fail):
  - `test_fork_bomb_scans_long_function_name_exactly`: `"b"*70 + "(){ " + "b"*70 + "|" + "b"*70 + "& };" + "b"*70` → `1`; `"a"*65 + "(){ :; }"` → `0`.
  - `test_fork_bomb_function_name_at_limit_is_scanned`: `"a"*64 + "(){ :; }"` → `0`; `"b"*64 + "(){ " + "b"*64 + "|" + "b"*64 + "& };"` → `1`; `"a"*100 + "()"` → `0`.
  - `test_fork_bomb_fails_closed_on_exhausted_body_window`: `"f(){ " + "x"*520 + " f|f& };f"`, `"f(){ " + "x"*980 + " f|f& };f"` → `1`.
  - `test_fork_bomb_closed_body_within_window_is_scanned`: `"f(){ " + "x"*500 + " }"`, `"f(){ x} " * 60000` → `0`.
  - `test_fork_bomb_scan_stays_linear_on_long_header_names`: `"a"*20000 + "(){ :; }"` → `0`, `"a"*300000 + "(){ :; }"` → `0`, `{`-Kette `"f(){ " * 60000` → `1`; Messung `time.perf_counter` im Subprozess, `_scan(…, timeout=5)`, `subprocess.TimeoutExpired` → `pytest.fail("watchdog …")`, Grenze `< 1000` ms je Fall.
- [ ] Step 3: Rot-Lauf (ohne `-x`): `python3 -m pytest tests/test_hook_common_lib.py -k "long_function_name_exactly or name_at_limit or exhausted_body_window or closed_body_within_window or linear_on_long_header_names" -q` → Erwartung `4 failed, 8 passed`. Rot: Bombe mit Namen 70, Body 520, Body 980, `{`-Kette. Grün (Charakterisierung): harmloser 65er, 3× Grenzfall 64/ohne `{`, 2× geschlossener Body, 2× langer harmloser Name (Werte am 2026-10-29 gegen `3e340690` an der emittierten Funktion gemessen, Py 3.13). Abweichung → Stopp, neu messen.
- [ ] Step 4: Implementieren in `hook_shell_scan_py`: im Rückwärts-Scan Abbruch `if e - s > _MAX_FUNC_NAME: break` und `len(name) > _MAX_FUNC_NAME` entfernen, Konstante `_MAX_FUNC_NAME` streichen; bei `close < 0` → `return True` statt `continue`. Header-Kommentar (~:426-430) auf: Name unbegrenzt (linear, weil sich die Rückwärts-Scans zweier `()`-Paare nie überdecken), Body fail-closed ohne ungequotetes `}` in den ersten 512 Zeichen (Fehlalarm-Klasse Spec RK-1), Body endet am ersten ungequoteten `}` ohne Verschachtelung (bekannte Lücke, Spec Q10). Kein `try/except`.
- [ ] Step 5: Grün: `python3 -m pytest tests/test_hook_common_lib.py tests/test_orchestrator_guard_hook.py -q` → alle passed (inkl. AC-A.6-Liste der Spec). Messwerte der Laufzeittests notieren (PR-Text, Task 5).
- [ ] Step 6: commit `fix: scan fork-bomb names exactly and fail closed on body limit` (63 Zeichen)

### Task 2: R1 — Grenzen-Zeile im Destructive-Gate
**Agent:** developer · **Issue:** Refs #943 · **AC:** AC-A.7
**Depends on:** 1
**Files:**
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh`
- Modify: `tests/test_orchestrator_guard_hook.py`
**Interfaces:** Produces eine zusätzliche stderr-Zeile im Destructive-Gate (nach `Detected command: …`), Englisch, konditional, mit der Grenzphrase `first 512` und »unquoted '}'« (Variante (a): zusätzlich `over 64 characters`); Klassifikator-Ausgabe unverändert; Consumes Task 1.
- [ ] Step 1: `Grep` `destructive operation requires explicit user approval` in `hooks/1-generic/orchestrator-guard-impl.sh` → genau 1 Treffer (~:1255).
- [ ] Step 2: Test schreiben (fail): `test_fork_bomb_window_block_names_scan_limits` — `_run_with(_bash_payload("f(){ " + "x"*520 + " f|f& };f"), tmp_path)` (Muster `test_fork_bomb_scan_does_not_hang_on_a_300kb_command`, ~:1681) → `returncode == 2`, stderr enthält `user approval` und `first 512`.
- [ ] Step 3: `python3 -m pytest tests/test_orchestrator_guard_hook.py -k window_block_names_scan_limits -q` → `1 failed` (exit 2 bereits durch Task 1, `first 512` fehlt in stderr).
- [ ] Step 4: Zeile ergänzen, z. B. `echo "If this is a shell function: a body without an unquoted '}' in its first 512 characters is blocked by the fork-bomb scan (fail closed)." >&2`.
- [ ] Step 5: `python3 -m pytest tests/test_orchestrator_guard_hook.py -q` → alle passed.
- [ ] Step 6: commit `fix: name fork-bomb scan limits in destructive block message` (60 Zeichen)

### Task 3: PR A — Versionen, Changelog und »Bekannte Grenzen«
**Agent:** junior-developer · **Issue:** Refs #943 · **AC:** AC-A.8, AC-A.10
**Depends on:** 2
**Files:**
- Modify: `hooks/1-generic/lib/hook_common.sh`
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh`
- Modify: `rules/1-generic/branch-guard.md`
- Modify: `CHANGELOG.md`
**Interfaces:** Produces `hook_common.sh` `# version: 1.5.0` (Minor) mit vorangestelltem `v1.5.0: …` in der vorhandenen `# changelog:`-Zeile, `orchestrator-guard-impl.sh` `# version: 1.9.3` (Patch, **ohne** `# changelog:` — die Datei hat keinen Header-Changelog); neuer Punkt 5 in »Bekannte Lücken« von `rules/1-generic/branch-guard.md`; `CHANGELOG.md` [Unreleased] `### Fixed`-Eintrag; Consumes Tasks 1–2, Skill `conventions`.
- [ ] Step 1: `Grep` `^# version:` in beiden Hook-Dateien → `1.4.0` bzw. `1.9.2` (sonst Stufen neu ableiten und melden); `Grep` `^# changelog:` → genau 1 Treffer in `hook_common.sh` (:5), 0 in `orchestrator-guard-impl.sh`.
- [ ] Step 2: Header bumpen; nur in `hook_common.sh` den Changelog-Eintrag vorn ergänzen (Format der vorhandenen Einträge).
- [ ] Step 3: `rules/1-generic/branch-guard.md`, Liste »Bekannte Lücken« (nach Punkt 4, ~:32), Deutsch: `5. Der Fork-Bomb-Scan des Destructive-Gates beendet den Funktionskörper am ersten ungequoteten `}` (keine Verschachtelung): Bomben mit `${…}` oder `{ …; }` vor dem Selbstaufruf (z. B. `f(){ : ${x}; f|f& };f`) werden nicht erkannt. Ein Funktionskörper ohne ungequotetes `}` in den ersten 512 Zeichen wird dagegen geblockt (fail-closed, mögliche Fehlalarme). Fix: Folge-Issue.` (Nummer des Folge-Issues nachtragen, sobald der User es angelegt hat; sonst ohne Nummer.) `Grep` `ersten ungequoteten` → ≥ 1 Treffer (AC-A.10).
- [ ] Step 4: `CHANGELOG.md` (Englisch), z. B. `- **`hook_common.sh` 1.5.0 / `orchestrator-guard-impl.sh` 1.9.3 (#943 follow-up)**: the fork-bomb scan checks function names of any length exactly and fails closed when a body has no unquoted `}` in its first 512 characters (blocks instead of being skipped); the destructive block message names the limit. Known gap, documented in `rules/1-generic/branch-guard.md`: the body still ends at the first `}` (no nesting).` Fehlalarm-Klasse (lange Inline-Funktionskörper) ausdrücklich nennen.
- [ ] Step 5: `Grep` `^# version:` → `1.5.0` / `1.9.3`; `python3 scripts/sync.py --validate` → Exit 0.
- [ ] Step 6: commit `chore: bump hook versions and document fork-bomb scan gap` (57 Zeichen)

### Task 4: PR A — Rebaseline auf frischem `main` und Self-Sync
**Agent:** developer · **Issue:** Refs #943 · **AC:** AC-A.9
**Depends on:** 3
**Gate:** Branch durch den `git`-Agenten auf aktuellen `origin/main` rebased; bei Konflikt in `hashes.json`/`_FIXTURE_TREES` **kein** Rebaseline (Branch neu aufsetzen lassen).
**Files:**
- Modify: `tests/fixtures/ac01-baseline/hashes.json`
- Modify: `tests/test_ac01_render_identity.py`
- Modify: `tests/test_opencode_v2_surface.py`
- Modify: `.agents/hooks/lib/hook_common.sh`
- Modify: `.agents/hooks/orchestrator-guard-impl.sh`
- Modify: `.meta-config/generated-file-hashes.json`
**Interfaces:** Produces neu gepinntes AC-01-Manifest (`13 + k` Einträge, k ∈ {0, 6}), Rebaseline-Log-Eintrag, neuer `ac01-baseline`-Digest in `_FIXTURE_TREES`, versionierte Self-Sync-Kopien; Consumes Tasks 1–3.
- [ ] Step 1: Drift beobachten: `python3 -m pytest tests/test_ac01_render_identity.py -q` → `1 failed` mit Drift-Liste. **Erwartet (abschließend, `13 + k` von 1085, k ∈ {0, 6}):** 4 Hook-Renders `Claude/.claude/hooks/lib/hook_common.sh`, `Gemini/.agents/hooks/lib/hook_common.sh`, `Claude/.claude/hooks/orchestrator-guard-impl.sh`, `Gemini/.agents/hooks/orchestrator-guard-impl.sh`; 9 Regel-Renders `Claude/.claude/rules/branch-guard.md`, `Continue/.continue/rules/branch-guard.md`, `Copilot/.github/instructions/branch-guard.instructions.md`, `Codex/AGENTS.md`, `Gemini/AGENTS.md`, `KimiCode/AGENTS.md`, `Mammouth/AGENTS.md`, `Opencode/AGENTS.md`, `ZCode/AGENTS.md`. Zulässig zusätzlich nur `<Provider>/.meta-config/context-hashes.json` dieser sechs `AGENTS.md`-Provider (k = 6, nicht erwartet, Spec AC-A.9; falls vorhanden im Log benennen und die Zahlen unten als `13 + k` ansetzen). `<Provider>/.meta-config/generated-file-hashes.json` driftet nicht (`_hash_file` hasht nur die Schlüssel). **Stop-Kriterium:** jede andere Zeile ⇒ nicht schreiben, Ursache klären, melden.
- [ ] Step 2: **Kein `--write`.** Gerenderte Matrix in `.tmp/` (`render_matrix_hashes` aus dem Harness) bzw. die Drift-Liste aus Step 1; jeden neuen Digest unabhängig mit `_hash_file` aus den gerenderten Bytes berechnen und in `hashes.json` **je Eintrag** ersetzen (`13 + k` Einzeilen-Ersetzungen, `1087 - (13 + k)` der 1087 Zeilen unberührt; k = 0: 1074). Rebaseline-Log im Docstring (Englisch, Muster :363/:399/:439): `Wave 3 rest (PR A, #943 follow-up; hook_common.sh 1.4.0 -> 1.5.0, orchestrator-guard-impl.sh 1.9.2 -> 1.9.3, branch-guard rule known-gap entry): 13 + k of 1085 hashes moved (k = 0 or 6, fill in measured value); 0 added/removed -- 4 hook renders (Claude + Gemini) and 9 branch-guard rule renders (Claude/Continue/Copilot rule files, AGENTS.md of Codex/Gemini/KimiCode/Mammouth/Opencode/ZCode), alt -> neu je Eintrag (8 Hex-Zeichen). Patched per entry (13 + k single-line replacements, 1087 - (13 + k) of the 1087 lines untouched; k = 0: 13 and 1074) -- not via --write -- after independently recomputing each digest with _hash_file. AC01_EXCEPTIONS is NOT extended.` Digest: `python3 -m pytest tests/test_opencode_v2_surface.py -k test_ac_t4_fixtures_unchanged -q` meldet `ac01-baseline: expected <alt>, got <neu>` → `got` nach unabhängiger Neuberechnung aus den Fixture-Bytes übernehmen; Log-Kommentar über `_FIXTURE_TREES` (Muster ~:5280-5296) ergänzen.
- [ ] Step 3: Diff-Nachweis (Git-Lesebefehl): `git diff --stat tests/fixtures/ac01-baseline/hashes.json` → `13 + k insertions(+), 13 + k deletions(-)` (k = 0: 13/13), Zeilen = Liste aus Step 1; `tests/fixtures/slimming-golden`, `tests/fixtures/compact-golden` unverändert (enthalten den Regelabschnitt nicht).
- [ ] Step 4: Self-Sync: `python3 scripts/sync.py`; danach `.agents/hooks/lib/hook_common.sh` und `.agents/hooks/orchestrator-guard-impl.sh` tragen 1.5.0 / 1.9.3; `.meta-config/generated-file-hashes.json` ändert die Werte der betroffenen Hook-/Regel-Kopien (u. a. `.claude/rules/branch-guard.md`, ~:103); `AGENTS.md` des Repos bleibt unverändert (nur Compact-Zeiger, ~:57); `python3 scripts/consistency-check.py` ohne `hooks.stale-deployed-version`. Nur Pfade aus `Files:` committen; weitere Sync-Diffs (`git status --short`) ohne Bezug zu Tasks 1–3 über den `git`-Agenten zurücksetzen lassen und melden; mit Bezug, aber nicht in `Files:` → Stopp, Plan ergänzen.
- [ ] Step 5: `python3 -m pytest tests/test_ac01_render_identity.py tests/test_opencode_v2_surface.py tests/test_template_slimming_equivalence.py tests/test_compact_matrix.py -q` → alle passed.
- [ ] Step 6: commit `chore: rebaseline AC-01 hashes for fork-bomb scan limits` (56 Zeichen)

### Task 5: PR A — Exit-Gate und PR-Beschreibung
**Agent:** developer · **Issue:** Refs #943 · **AC:** Exit-Kriterien PR A
**Depends on:** 4
**Files:**
- Create: `.tmp/wave3-prA-description.md`
**Interfaces:** Produces Exit-Nachweis und PR-Text (Entwurf); Consumes Tasks 1–4. Push/PR durch den `git`-Agenten.
- [ ] Step 1: `python3 scripts/sync.py --validate` → Exit 0; `python3 -m pytest tests -q` → ohne `failed`/`error`.
- [ ] Step 2: PR-Text (Titel `fix: fail closed at fork-bomb scan limits`), Inhalt: Problem (Messwerte Spec R1), Vertrag (Q3-Entscheidung), Fehlalarm-Klasse, dokumentierte `}`-Lücke (Q10, Verweis auf das Folge-Issue des Users, falls angelegt), Rot-/Grün-Läufe, Laufzeitwerte aus Task 1 Step 5, Rebaseline-Umfang. Zeile `Refs #943` (geschlossen, Q9; kein `Closes`).
- [ ] Step 3: Kein Commit; Hand-off an den `git`-Agenten.

## PR B — `fix/index-lf-admin-hint-zcode-doc` (R2, R3, R4)

**Branch:** `fix/index-lf-admin-hint-zcode-doc` (vom `git`-Agenten angelegt; Entwicklung parallel zu PR A, Merge nach PR A auf frischem `main`).
**Entry:** Spec APPROVED; Q5 vom User bestätigt (2026-10-29); Q6 vor Task 10 entschieden.
**Exit:** (1) `python3 -m pytest tests/test_newline_normalization.py tests/test_hook_lib_sync.py tests/test_release_gate_checksums.py tests/test_admin_server.py -q` grün; (2) `python3 scripts/sync.py --validate` Exit 0; (3) `python3 -m pytest tests -q` ohne `failed`/`error`; (4) `python3 -m pytest tests/test_ac01_render_identity.py -q` grün **ohne** Rebaseline (AC-B.4; bei Rot: Stopp, Ursache melden — kein Rebaseline in PR B ohne Plan-Revision); (5) `CHANGELOG.md`-Einträge inkl. Modus 0600.
**Rollback:** `git revert` des Merge-Commits durch den `git`-Agenten. Folge: Indizes wieder per `write_text` (CRLF unter Windows), Host-Meldung ohne Hinweis, Doku wieder falsch; bereits mit 0600 geschriebene Indizes bleiben (kein Datenverlust).

### Task 6: R2 — Managed-Indizes über `write_atomic`
**Agent:** developer · **Issue:** Refs #961 · **AC:** AC-B.1, AC-B.2, AC-B.3, AC-B.4 · **parallel_group:** gB
**Depends on:** —
**Files:**
- Modify: `scripts/lib/hooks.py`
- Modify: `scripts/lib/hook_plugins.py`
- Modify: `tests/test_newline_normalization.py`
**Interfaces:** Produces `sync_hooks`, `sync_release_gates`, `sync_hook_lib` schreiben `.agent-meta-managed` über `write_atomic(path, content)` (LF, Modus 0600), Bedingungen (`not dry_run`, #630-Leerindex) unverändert; Consumes `scripts/lib/io.py:write_atomic` (bereits importiert, `hooks.py:9`, `hook_plugins.py:16`).
- [ ] Step 1: `Grep` `\.write_text\(` in `scripts/lib/hooks.py` und `scripts/lib/hook_plugins.py` → genau 3 Treffer (`hooks.py` ~:635, `hook_plugins.py` ~:160, ~:348).
- [ ] Step 2: Tests schreiben nach Muster `test_create_hook_writes_lf_through_write_atomic` / `test_create_hook_dry_run_writes_nothing` (Spy auf `write_atomic` im jeweiligen Modul per `monkeypatch.setattr`, ~:246-288). Aufruf-Vorlagen: `tests/test_antigravity_hooks_registration.py` (~:85-92, `sync_hooks`/`sync_hook_lib` mit echtem `agent_meta_root` und `load_providers_config`), `tests/test_release_gate_checksums.py` bzw. `tests/test_hook_lib_sync.py` (`sync_release_gates`, Dry-Run-Vorbild `test_dry_run_makes_no_filesystem_changes` :82). Annotationen Py3.9-kompatibel (`Optional[...]`).
  - Vorher rot: `test_hook_managed_index_writes_lf_through_write_atomic` (`hooks_mod.sync_hooks`), `test_release_gate_managed_index_writes_lf_through_write_atomic` (`hook_plugins.sync_release_gates`), `test_hook_lib_managed_index_writes_lf_through_write_atomic` (`hook_plugins.sync_hook_lib`); je Assertion: Spy-Aufrufliste **enthält** den Pfad `<…>/.agent-meta-managed` (weitere Aufrufe zulässig), Index-Bytes enthalten kein CR-Byte (13) (AC-B.1).
  - Charakterisierung, vorher **und** nachher grün (AC-B.3): `test_hook_managed_index_dry_run_writes_nothing` (`sync_hooks(…, dry_run=True)` → `.agent-meta-managed` existiert nicht, Spy-Liste ohne Index-Pfad); `test_hook_managed_index_rewritten_empty_after_revocation` (Lauf 1 mit echter Provider-Config für `Claude` → Index nicht leer; Lauf 2 mit Kopie dieser Config ohne `hook_protocol`, Gate `provider_hooks_supported` `hooks.py:~486` → Index existiert, `read_bytes() == b""`).
- [ ] Step 3: Rot-Lauf (ohne `-x`): `python3 -m pytest tests/test_newline_normalization.py -k "managed_index" -q` → `3 failed, 2 passed` (rot: Index-Pfad fehlt in der Spy-Liste, weil `write_text` schreibt; grün: die zwei Charakterisierungstests — im PR so vermerken). Abweichung bei den Charakterisierungstests → Stopp, Vorbedingung klären.
- [ ] Step 4: Die drei Aufrufe durch `write_atomic(managed_index_path, <gleicher Inhalt>)` ersetzen; vorhandene `mkdir`-Aufrufe dürfen bleiben.
- [ ] Step 5: Grün: `python3 -m pytest tests/test_newline_normalization.py tests/test_hook_lib_sync.py tests/test_release_gate_checksums.py tests/test_antigravity_hooks_registration.py -q` → alle passed (inkl. `5 passed` für `-k managed_index`); `Grep` `\.write_text\(` in beiden Modulen → 0 Treffer (AC-B.2).
- [ ] Step 6: commit `fix: write hook managed indices through write_atomic` (52 Zeichen)

### Task 7: R3 — Host-Header-Hinweis, Hilfetext, How-to und Schema
**Agent:** developer · **Issue:** Refs #897 · **AC:** AC-B.5, AC-B.6, AC-B.7 · **parallel_group:** gB
**Depends on:** —
**Gate:** Q5 vom User bestätigt (Doku an Code, 2026-10-29) — nicht blockierend. Bei einer späteren Änderung auf »Code an Hilfetext angleichen« Stopp und Plan-Revision (Verhaltensänderung, socket-freier Helfer nötig).
**Files:**
- Modify: `scripts/admin-server.py`
- Modify: `tests/test_admin_server.py`
- Modify: `docs/howto/admin-ui-remote-access.md`
- Modify: `config/project-config.schema.json`
**Interfaces:** Produces `SecurityError`-Text `host header not allowed: '<host>' -- … --allowed-hosts <host> … admin-ui.allowed-hosts … include loopback names if needed` (Logik unverändert); Wildcard-Startup-Hinweis mit demselben Zusatz; `--allowed-hosts`-Hilfetext »Allowed origin hosts … Replaces the default loopback set …«; How-to (:62, :157, :166, :216-224) und Schema-`description` von `admin-ui.allowed-hosts` konsistent; Consumes `AuthService.check_origin` (statisch, ~:948), Wildcard-Hinweis in `AdminServer.__init__` (~:5694), `main()`-Parser (~:5926).
- [ ] Step 1: `Grep -i` `host header not allowed|does not replace|extends the default|\*\*Extends\*\*|Additional allowed|host:port origins|writes from other machines` in `scripts/admin-server.py`, `docs/howto/admin-ui-remote-access.md`, `config/project-config.schema.json` → Treffer notieren (erwartet: admin-server ~:992, ~:5694, ~:5927, ~:5929; How-to ~:62, ~:166; Schema ~:1927).
- [ ] Step 2: Tests schreiben (fail) in `TestCheckOrigin` (`tests/test_admin_server.py` ~:768): `test_host_header_rejection_names_allowlist_hint` (`AuthService.check_origin(origin=None, host="evil.example:7420", allowed_hosts=DEFAULT_ALLOWED_HOSTS, bind_host="127.0.0.1", bind_port=7420)` → `SecurityError`, Text enthält `host header not allowed`, `--allowed-hosts`, `admin-ui.allowed-hosts`, `loopback names`), `test_allowed_hosts_help_states_replace_semantics` (`subprocess.run([sys.executable, <admin-server-Pfad>, "--help"], timeout=30)` → Exit 0, normalisierter Text (Whitespace zusammengezogen) enthält `Replaces`, weder `does not replace` noch `Additional allowed`; zusätzlich `json.load` von `config/project-config.schema.json` → `properties.admin-ui.properties.allowed-hosts.description` enthält `Replaces`, weder `Extends` noch `host:port`). Kein separater Schema-Test (Schema nicht in `hashes.json`, nicht gerendert, Spec R3).
- [ ] Step 3: Rot-Lauf (ohne `-x`): `python3 -m pytest tests/test_admin_server.py -k "allowlist_hint or replace_semantics" -q` → `2 failed`.
- [ ] Step 4: Implementieren (Englisch):
  - Host-Meldung um den Hinweis ergänzen (Wortlaut der Origin-Meldung ~:982-986 wiederverwenden) plus `; include loopback names if needed`; Wildcard-Hinweis (~:5694-5695) ebenso ergänzen.
  - Hilfetext z. B. `"Allowed origin hosts for CORS/DNS-rebinding protection. Default: 127.0.0.1 localhost ::1. Replaces the default loopback set: include loopback names if needed."`
  - How-to :62 (Tabellenzeile ohne »Additional«/»**Extends**«), :166 (»replaces the default loopback set«), YAML-Block :157 (Kommentar oder Liste mit Loopback-Namen, Text `loopback names`), Beispiel :216-224 (Satz: the list replaces the loopback default, include loopback names if needed).
  - Schema `admin-ui.allowed-hosts.description`, z. B. `"Hostnames/IPs (without port; the server port is appended) allowed for CORS / DNS-rebinding protection. Replaces the default loopback set; include loopback names if needed. Use when binding to a specific network interface."`; JSON gültig (`python3 -c "import json; json.load(open('config/project-config.schema.json'))"`).
- [ ] Step 5: Grün: `python3 -m pytest tests/test_admin_server.py -q` → alle passed, darunter unverändert `TestCheckOrigin::test_dns_rebinding_forged_host_rejected_even_with_matching_origin` und `TestCheckOriginBindHost` (AC-B.6). Abschluss-Grep (AC-B.7; die Phrase `loopback names` muss je in einem zusammenhängenden String-Literal stehen — der Wildcard-Hinweis ist ein mehrzeiliger f-String, ein Zeilenumbruch mitten in der Phrase würde den Grep ≥ 3 verfehlen): `Grep -i` `\*\*Extends\*\*|extends the default|Additional allowed` in `scripts/admin-server.py`, `docs/howto/admin-ui-remote-access.md`, `config/project-config.schema.json` → **0 Treffer**; `Grep` `does not replace` in denselben Dateien → 0; `Grep` `loopback names` → admin-server ≥ 3, How-to ≥ 2. `python3 scripts/sync.py --validate` → Exit 0.
- [ ] Step 6: commit `fix: hint on host header rejection and fix allowed-hosts help` (61 Zeichen)

### Task 8: R4 — zcode ZC-1 Entscheidungsnotiz
**Agent:** junior-developer · **Issue:** Refs #856 (Schließen durch User, Q6) · **AC:** AC-B.8 · **parallel_group:** gB
**Depends on:** —
**Files:**
- Modify: `docs/providers/zcode.md`
**Interfaces:** Produces Punkt 6 in »Deliberate limitations« (Englisch): ZC-1 (workspace agent auto-load) stays wontfix (documented); agent-meta does not write to `~/.zcode/agents` because that is outside the project root and would violate repo containment; the AGENTS.md bootstrap (section »Agents as definition store + bootstrap«) is the supported path; ZC-2 (commands capability under-claim) was fixed in #807; Consumes D8, `docs/providers/zcode.md:61-86`, `:207-216`. Regressionstest: keiner (D8).
- [ ] Step 1: `Read` `docs/providers/zcode.md` Zeilen 61–86 und 205–224; `Grep` `ZC-1|wontfix` → 0 Treffer (Ausgangsstand).
- [ ] Step 2: Punkt 6 ergänzen (Stil der Punkte 1–5).
- [ ] Step 3: `Grep` `ZC-1`, `wontfix`, `repo containment`, `~/.zcode/agents`, `#807` → je ≥ 1 Treffer; `python3 scripts/sync.py --validate` → Exit 0.
- [ ] Step 4: commit `chore: record zcode ZC-1 wontfix decision` (41 Zeichen)

### Task 9: PR B — Changelog
**Agent:** junior-developer · **Issue:** Refs #961, Refs #897, Refs #856 (Schließen durch User, Q6) · **AC:** AC-B.3 (Changelog-Teil)
**Depends on:** 6, 7, 8
**Files:**
- Modify: `CHANGELOG.md`
**Interfaces:** Produces `### Fixed`-Einträge (Englisch) unter [Unreleased]: managed hook indices via `write_atomic` (LF; files now created with mode 0600 instead of the umask default), host-header rejection and wildcard hints (include loopback names), `--allowed-hosts` help/how-to/schema description state replace semantics (schema: hosts, not host:port); zcode ZC-1 note; Consumes Tasks 6–8. Kein Versions-Bump (keine Hook-/Agent-Datei), kein `VERSION`-Bump.
- [ ] Step 1: Einträge schreiben; `Grep` `0600` und `#897` in `CHANGELOG.md` → neue Treffer im [Unreleased]-Block.
- [ ] Step 2: `python3 scripts/sync.py --validate` → Exit 0.
- [ ] Step 3: commit `chore: add changelog entries for index LF and admin hint` (56 Zeichen)

### Task 10: PR B — Exit-Gate, PR-Text, #856-Kommentar-Entwurf
**Agent:** developer · **Issue:** Refs #961, Refs #897, Refs #856 (Schließen durch User, Q6) · **AC:** AC-B.4, AC-B.9, Exit-Kriterien PR B
**Depends on:** 9
**Files:**
- Create: `.tmp/wave3-prB-description.md`
- Create: `.tmp/wave3-issue-856-close.md`
**Interfaces:** Produces Exit-Nachweis, PR-Text und den #856-Schließkommentar als Handoff-Text an den User; Consumes Tasks 6–9. Push/PR durch den `git`-Agenten; Issue-Schließung nur durch den User.
- [ ] Step 1: `python3 scripts/sync.py --validate` → Exit 0; `python3 -m pytest tests -q` → ohne `failed`/`error`; `python3 -m pytest tests/test_ac01_render_identity.py -q` → grün ohne Rebaseline (AC-B.4).
- [ ] Step 2: PR-Text (Titel `fix: LF managed indices, admin host hint, zcode ZC-1 note`), je Issue eine Zeile: `Refs #961`, `Refs #897` (beide geschlossen, Q9), `Refs #856` (Schließen durch den User, Q6). Modus-0600-Hinweis aufnehmen.
- [ ] Step 3: Kommentar-Entwurf in `.tmp/wave3-issue-856-close.md` (Englisch), zur Ausführung durch den User nach Merge, z. B. `! /home/hermes/.local/bin/gh issue close 856 --reason "not planned" --comment "ZC-1 (workspace agent auto-load) stays wontfix (documented): agent-meta does not write to ~/.zcode/agents because that would violate repo containment; the AGENTS.md bootstrap is documented in docs/providers/zcode.md (Deliberate limitations). ZC-2 (commands capability under-claim) was fixed in #807."` Gültige `--reason`-Werte der installierten `gh`-Version: unverifiziert (User prüft mit `gh issue close --help`).
- [ ] Step 4: Kein Commit; Hand-off an den `git`-Agenten (PR) und an den User (#856).

## Anhang — Traceability AC → Task → Test

| AC | Task | Test / Nachweis |
|---|---|---|
| AC-A.1 | 1 | `tests/test_hook_common_lib.py::test_fork_bomb_scans_long_function_name_exactly` (Variante (a): `::test_fork_bomb_fails_closed_on_long_function_name`) |
| AC-A.2 | 1 | `tests/test_hook_common_lib.py::test_fork_bomb_function_name_at_limit_is_scanned` (Charakterisierung) |
| AC-A.3 | 1 | `tests/test_hook_common_lib.py::test_fork_bomb_fails_closed_on_exhausted_body_window` |
| AC-A.4 | 1 | `tests/test_hook_common_lib.py::test_fork_bomb_closed_body_within_window_is_scanned` (Charakterisierung) |
| AC-A.5 | 1 | `tests/test_hook_common_lib.py::test_fork_bomb_scan_stays_linear_on_long_header_names` (n = 20 000/300 000 Charakterisierung, `{`-Kette rot) |
| AC-A.6 | 1 | vorhandene Fork-Bomb-Tests in `tests/test_hook_common_lib.py` und `tests/test_orchestrator_guard_hook.py` (Liste Spec AC-A.6) |
| AC-A.7 | 2 | `tests/test_orchestrator_guard_hook.py::test_fork_bomb_window_block_names_scan_limits` |
| AC-A.8 | 3 | `Grep` `^# version:` (1.5.0 / 1.9.3), `^# changelog:` nur in `hook_common.sh`, `CHANGELOG.md`-Eintrag, `VERSION` unverändert |
| AC-A.9 | 4 | `tests/test_ac01_render_identity.py`, `tests/test_opencode_v2_surface.py`, `git diff --stat` (13 + k / 13 + k), `python3 scripts/consistency-check.py` |
| AC-A.10 | 3 | `Grep` `ersten ungequoteten` in `rules/1-generic/branch-guard.md` → ≥ 1; Render-Drift in AC-A.9 |
| AC-B.1 | 6 | `tests/test_newline_normalization.py::test_hook_managed_index_writes_lf_through_write_atomic`, `::test_release_gate_managed_index_writes_lf_through_write_atomic`, `::test_hook_lib_managed_index_writes_lf_through_write_atomic` |
| AC-B.2 | 6 | `Grep` `\.write_text\(` in `scripts/lib/hooks.py`, `scripts/lib/hook_plugins.py` → 0 |
| AC-B.3 | 6, 9 | `tests/test_newline_normalization.py::test_hook_managed_index_dry_run_writes_nothing`, `::test_hook_managed_index_rewritten_empty_after_revocation` (neu, Charakterisierung, vor dem Fix grün); vorhanden `tests/test_hook_lib_sync.py::test_dry_run_makes_no_filesystem_changes`, `tests/test_newline_normalization.py::test_create_hook_dry_run_writes_nothing`; `Grep` `0600` in `CHANGELOG.md` (Task 9) |
| AC-B.4 | 6, 10 | `tests/test_ac01_render_identity.py` grün ohne Rebaseline |
| AC-B.5 | 7 | `tests/test_admin_server.py::TestCheckOrigin::test_host_header_rejection_names_allowlist_hint` |
| AC-B.6 | 7 | `tests/test_admin_server.py::TestCheckOrigin::test_dns_rebinding_forged_host_rejected_even_with_matching_origin`, `::TestCheckOriginBindHost` |
| AC-B.7 | 7 | `tests/test_admin_server.py::TestCheckOrigin::test_allowed_hosts_help_states_replace_semantics` (Hilfetext + Schema-Beschreibung), Abschluss-Grep Task 7 Step 5 (`**Extends**`/`extends the default`/`Additional allowed`/`does not replace` → 0; `loopback names` ≥ 3 / ≥ 2) |
| AC-B.8 | 8 | `Grep` `ZC-1`/`wontfix`/`repo containment`/`~/.zcode/agents`/`#807` in `docs/providers/zcode.md` |
| AC-B.9 | 10 | `.tmp/wave3-issue-856-close.md` (Handoff an den User) |

## Offene Fragen (aus der Spec, mit Entscheidungszeitpunkt)

| ID | Frage | Default / Entscheidung | Entscheidung bis |
|---|---|---|---|
| Q1 | Reopen vs. neue Issues (Rev. 1) | gegenstandslos | — |
| Q2 | D5 formal aufheben (Rev. 1) | gegenstandslos | — |
| Q3 | R1-Vertrag (a) fail-closed an beiden Grenzen / (b) Name exakt + Body fail-closed / (c) belassen; Fenster 512 oder 1024 | **GESCHLOSSEN – vom User bestätigt, 2026-10-29: (b)**, 512 | — (entschieden) |
| Q4 | #945 vor PR A vorziehen? | Nein | vor PR-A-Start, durch User |
| Q5 | `--allowed-hosts`: Doku an Code oder Code an Doku? | **GESCHLOSSEN – vom User bestätigt, 2026-10-29:** Doku an Code (»Replaces«), Code unverändert | — (entschieden) |
| Q6 | #856 nach PR B schließen? | Ja, durch den User (Entwurf Task 10) | vor Task 10, durch User |
| Q7 | `function NAME { … }`-Form in R1 aufnehmen? | Nein, Folge-Issue durch den User | vor Task 1, durch User |
| Q8 | Kriterium für #971 | bleibt offen | offen, durch User |
| Q9 | Geschlossene Bezugs-Issues (#943, #961, #897): »Refs« oder Reopen? | **GESCHLOSSEN – vom User bestätigt, 2026-10-29:** »Refs« statt »Closes« (#943, #961, #897) | — (entschieden) |
| Q10 | `}`-Lücke: (ii) dokumentieren + Folge-Issue oder (i) in PR A mitschließen? | **GESCHLOSSEN – vom User bestätigt, 2026-10-29: (ii)** — Folge-Issue durch den User (Entwurf im Status-Abschnitt) plus Eintrag in »Bekannte Grenzen« (AC-A.10/Task 3 Pflicht) | — (entschieden) |

## Annahmen und Self-Review

**Annahmen (explizit):**
1. `origin/main` `3e340690` enthält den in der Spec belegten Stand; Testläufe der vorhandenen Tests wurden für diese Revision **nicht** ausgeführt (nur Existenz geprüft) — Task 1 Step 5 und Task 6 Step 5 sind die ersten Läufe.
2. Die Rot-Zählung in Task 1 Step 3 (`4 failed, 8 passed`; Variante (a): `7 failed, 5 passed`) beruht auf einer Messung der emittierten Funktion gegen `3e340690` (2026-10-29, Py 3.13, alle 12 Fälle einzeln); bei anderem Stand neu messen. Task 6 Step 3 (`3 failed, 2 passed`) ist aus dem Code abgeleitet (`write_text`-Pfad, `not dry_run`-Bedingung, #630-Leerindex), nicht gemessen.
3. AC-01 hasht nur Inhalte (`tests/test_ac01_render_identity.py:540`) → PR B ohne Rebaseline; die Index-Inhalte bleiben auf Linux byte-identisch; das Schema wird nicht gerendert (Matrix-Render 2026-10-29).
4. `<Provider>/.meta-config/generated-file-hashes.json` driftet im AC-01-Fixture nicht (`_hash_file` :526-531 hasht nur die Schlüssel; Wave-6-Logs :388-447). `context-hashes.json` der sechs `AGENTS.md`-Provider: nicht erwartet (statischer Header), in Task 4 gemessen.
5. `python3 scripts/admin-server.py --help` endet ohne Seiteneffekt mit Exit 0 (geprüft 2026-10-29).
6. `check_stale_deployed_hooks` prüft `lib/` nicht (gelesen `scripts/lib/consistency/hook_drift.py:29-86`); deshalb wird `orchestrator-guard-impl.sh` mitgebumpt (Spec RK-2).
7. Re-Planning: nach dem Merge von PR A Zeilennummern, `CHANGELOG.md`-Stand und Q-Entscheidungen für PR B prüfen.

**Self-Review:**
- 10 Tasks, je ein Agent aus `allowed_agents`; jeder Task in der Step-Agent-Map; `pipeline_stages.implement = 1`; Task-Nummern gegenüber Rev. 2 unverändert.
- Jede AC-ID der Spec (AC-A.1–A.10, AC-B.1–B.9) steht im Traceability-Anhang.
- `Files:`-Blöcke: PR A und PR B überschneiden sich nur in `CHANGELOG.md` (Task 3 / Task 9, unterschiedliche PRs, seriell gemergt); `gB` = {6, 7, 8} disjunkt. Prüfung vor Ausführung per `scripts/lib/orchestration.py::check_plan_file_overlap`.
- Kein Task führt Git-Mutationen, `gh`-Schreibaufrufe oder Issue-Änderungen aus; `gh`-Befehle stehen nur als User-Handoff-Entwürfe (Task 10, Q10-Folge-Issue im Status-Abschnitt).
- Validator-Hinweis: `scripts/lib/consistency/spec_plan.py` stuft nur `*-design.md` als Spec ein; Warnungen zur Spec-Datei sind erwartet (Spec RK-6).
