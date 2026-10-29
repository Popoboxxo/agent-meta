---
pipeline_stages:
  implement: 5
---

# Bugfix-Welle 3 — Implementation Plan

> Status: geplant (Entwurf)
>
> **Freigabevermerk:** Die zugehörige Spec trägt `Status: Entwurf`. Dieser Plan ist **nicht ausführbar**, bis der Nutzer bzw. `concept-reviewer` die Spec auf `Status: APPROVED` setzt und diesen Plan freigibt. Der Approval-Marker wird nie vom Planer gesetzt.

**Goal:** 13 Bugs aus der Release-Linie `v2.0.0-beta.4` in vier seriell gemergten PRs beheben (Reihenfolge PR 1 → PR 2 → PR 4 → PR 3): 12 Code-Bugs (B1–B12) je mit mindestens einem vorher roten Regressionstest, B13 (#856) als Doku-Eintrag ohne Regressionstest (D8); alle Sicherheits-Hooks bleiben fail-closed; `python3 scripts/consistency-check.py` meldet 0 `handoff.output-not-consumed`; plus ein nur nach Freigabe auszuführendes Housekeeping (PR 0, Texte als Entwurf).
**Architecture:** Kein neues Subsystem. PR 1 härtet drei Bash-Hooks (`dod-push-check.sh`, `orchestrator-guard-impl.sh`, `repo-containment(-impl).sh`) an der Root-Cause; PR 2 stellt vier Schreibpfade im Hook-Deploy auf `io.write_atomic` um und härtet die `dod-push-check`-Tests; PR 4 extrahiert einen socket-freien Host-Helfer im Admin-Server und schließt Manifest-Dateien im Doctor aus; PR 3 ergänzt Daten (`role-defaults.yaml`), Variablen-Fallbacks (`config.py`) und leert den Placeholder-Ratchet.
**Tech Stack:** Bash-Hooks mit eingebettetem Python 3.9+, Python-Stdlib + PyYAML, pytest, YAML/JSON-Config, Markdown.
**Spec:** `docs/specs/2026-10-29-bugfix-wave-3-spec.md`
**Spec-ID:** `spec-id: SPEC-bugfix-wave-3` (Status Entwurf, 2026-10-29)
**Tracking:** #1033, #943, #944, #961, #951, #954, #1031, #983, #1037, #897, #1034, #856 (Stand der Issues: siehe Spec »Scope-Befund A«, Q1)

## Entry-/Exit-Kriterien (gesamt)

**Entry (vor Task 4, dem ersten Code-Task):**
1. Spec `Status: APPROVED` und dieser Plan freigegeben.
2. Q1 (Reopen vs. neue Issues) und Q6 (#945 vorziehen) und Q3 (Fix-Vertrag #943) entschieden — Entscheidungszeitpunkte siehe »Offene Fragen«.
3. `origin/main` = Ausgangsstand `043d29a4` oder neuer; Arbeitsbranch je PR durch den `git`-Agenten angelegt (Branchname je PR-Phase). Kein Code auf `main` (`.claude/rules/branch-guard.md`).

**Exit (gesamt):** PR 1, PR 2, PR 4, PR 3 gemergt (in dieser Reihenfolge, seriell); je PR die Exit-Kriterien der eigenen Phase erfüllt; `python3 -m pytest tests -q` ohne `failed`/`error` auf `main` nach dem letzten Merge; `python3 scripts/consistency-check.py` → 0 `handoff.output-not-consumed`; alle Checkboxen gesetzt (Ledger = Plan-Datei, Skill `plan-ledger`) — Task 1–3 und 34 (PR 0/0b) sind Ausnahmen: sie laufen nur nach ausdrücklicher Freigabe und blockieren keinen PR. Bedingte Tasks (10 OPTIONAL, 35, 36): werden sie nicht ausgeführt, erhalten ihre Checkboxen den Vermerk `entfällt (<Grund>)` statt eines Hakens.

## Global Constraints

- **Task-Format (maschinenlesbar):** `### Task <n>: <Titel>`; zeilenverankerte Felder `**Agent:**`, `**Depends on:**` (nur Task-Nummern dieses Plans), `**Files:**`-Block mit je einer Zeile `- Create:`/`- Modify:` mit Pfad in Backticks; `**Interfaces:**` einzeilig mit Produces/Consumes.
- **Keine Issue-Änderung und kein `gh`-Schreibaufruf durch diesen Plan-Lauf.** Alle `gh`-Befehle in PR 0/0b stehen als Text und werden **nur nach ausdrücklicher Freigabe des Nutzers** ausgeführt (D2, D6). `gh` liegt unter `/home/hermes/.local/bin/gh` (nicht im `$PATH`).
- **TDD (D4, trotz DoD-Preset `rapid-prototyping`):** Jeder Code-Task beginnt mit einem Test, der vor dem Fix nachweislich rot ist (erwartete Ausgabe im Step); dann Fix; dann grün. Der Rot-Lauf wird in der PR-Beschreibung festgehalten.
- **Fail-closed:** Kein Fix darf einen neuen Fail-open-Pfad öffnen. Hooks bleiben Convention boundary (`.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary`).
- **#954-Eskalationsregel (Spec R1):** (a) Ein roter #954-Test wird nie per `skip`/`xfail` stillgelegt. (b) Hook-Fix im selben PR 2 nur, wenn er auf eine Funktion/einen Zweig von `dod-push-check.sh` begrenzt ist und erlaubte Pushes nicht ändert; dann Version-Bump und Rebaseline in PR 2 mit Vermerk (Abweichung explizit im PR). (c) Sonst **Stopp**: Befund an den Nutzer, Folge-Issue-Entwurf, PR 2 wird ohne den betroffenen Test nicht gemergt, bis der Nutzer entscheidet (Fix in PR 2, eigener PR oder Aufteilung). Hook-Fixes sind **unbeziffert** (nicht in der Task-Zählung).
- **Rebaseline-Regel (Rest von D5):** `python tests/test_ac01_render_identity.py --write` nur auf **frischem `main`** (Branch auf aktuellen `origin/main` rebased, vorheriger PR gemergt), nie per Merge-Konfliktauflösung in `tests/fixtures/ac01-baseline/hashes.json` oder `_FIXTURE_TREES`. Begründung im Rebaseline-Log (Docstring von `tests/test_ac01_render_identity.py`); Digests in `tests/test_opencode_v2_surface.py::_FIXTURE_TREES` nachziehen; `AC01_EXCEPTIONS` nicht erweitern. Pro PR höchstens ein Rebaseline.
- **Version-Bump nach Skill `conventions`:** Agent-Templates (`agents/`): Major bei umbenannter Variable/geändertem Verhalten/neuer Pflichtsektion, Minor bei neuer optionaler Sektion/erweitertem Scope, Patch bei Textverbesserung/Klarstellung. Hook-Dateien tragen einen `# version:`-Header; die Stufenwahl folgt der **Hook-Präzedenz** im Repo, nicht der Agent-Template-Skala: Verhaltensänderung eines Hooks = Minor (Präzedenz `CHANGELOG.md` ~:604, #963: `repo-containment-impl.sh` 1.0.0 → 1.1.0 für geänderte Pfadregeln), reiner Meldungs-/Kommentartext = Patch (Plan-Entscheidung laut Spec AC-1.20, siehe Task 12). `VERSION` wird in PR 1–4 **nicht** geändert (nur in Release-PRs, vgl. `git log -- VERSION`: ausschließlich `chore: release …`). Änderungen an `rules/` oder `hooks/` erfordern anschließend `python3 scripts/sync.py` (überschreibt generierte Kopien); `config/project-config.schema.json` → Schema-Test; neues Feature/Option → Szenario-Prüfung (`tests/scenarios/registry.md`).
- Commit-Messages: Englisch, Conventional Commits mit den Typen **`feat`/`fix`/`chore`** (`.claude/rules/commit-conventions.md`; Doku-, Changelog- und Rebaseline-Commits → `chore:`, Test-Commits zu einem Bug → `fix:`), Subject ≤ 72 Zeichen (alle Subjects dieses Plans nachgezählt), Imperativ, ohne BOM; Commit durch die per `auto_commit` freigeschaltete Rolle bzw. den Orchestrator nach Secret-Scan; Push/Branch/PR/Tag nur der `git`-Agent. Dokumente Deutsch, Code-Kommentare/Logmeldungen Englisch.
- Keine `isolation: "worktree"`; Schreiben nur im Projektroot und `.tmp/` (Repo-Containment).
- Provider-agnostisch (Skill `provider-agnostic`): keine `if provider == "Name"`-Zweige in `scripts/lib`.
- Python-3.9-kompatibel in `scripts/` **und** `tests/` (CI-Matrix `['3.9', '3.12']`, `.github/workflows/orchestration-test.yml`): kein `match`, kein `X | Y` in Annotationen oder zur Laufzeit (ohne `from __future__ import annotations` wird die Annotation beim `def` ausgewertet → `TypeError` unter 3.9; stattdessen `Optional[...]`/`Union[...]`); `write_text(newline=)` erst ab 3.10 → nicht verwenden.
- Zeilennummern sind Orientierung (Stand `043d29a4`); maßgeblich sind Symbole. Jeder Task, der Zeilen zitiert, beginnt mit einem `Grep` auf das Symbol.
- Git-Lesebefehle (auch `git branch --contains`) für Rollen ohne `git`-Sentinel können vom Orchestrator-Guard false-positive geblockt werden (Vorlauf-Befund D): bei Block **stoppen**, exakten Befehl melden, über den `git`-Agenten ausführen lassen, nicht umgehen.
- Aufwand: Schätzung über `effort-estimator` (Textreferenz, wird von diesem Plan nicht berechnet).

## Ausführungsmodell

- **Merge-Reihenfolge (seriell, D3):** PR 0 (Housekeeping, nur Text/Freigabe) → **PR 1** → **PR 2** → **PR 4** → **PR 3**. Die Spec nummeriert PR 3 vor PR 4, gemergt wird PR 4 vor PR 3 (PR 3 hat den größten Rebaseline und kommt zuletzt).
- **Entwicklungs-Parallelität:** PR 2 ∥ PR 4 sind dateidisjunkt (Ownership über die `Files:`-Blöcke der Tasks 15–21 gegen 22–27 geprüft: einzige gemeinsame Datei ist `CHANGELOG.md`, Konflikt wird im jeweils späteren PR manuell aufgelöst, kein Rebaseline-Konflikt) und dürfen parallel entwickelt, aber nur seriell gemergt werden. PR 1 vor PR 2 wegen gemeinsamer Dateien `hooks/1-generic/dod-push-check.sh`, `tests/test_dod_push_check_hook.py`, `CHANGELOG.md` und Version-Bumps. PR 4 startet nach Merge von PR 1 (Spec). PR 3 startet erst nach Merge von PR 1, 2, 4.
- **Innerhalb PR 1:** `parallel_group: g1` = Tasks 5, 6, 8 (ownership-disjunkt: `dod-push-check.sh` + `test_dod_push_check_hook.py` / `orchestrator-guard-impl.sh` + `test_orchestrator_guard_hook.py` / `repo-containment.sh` + `test_repo_containment_hook.py`). Alle übrigen Tasks sequenziell.
- **DAG PR 0:** `1 → 2`, `1 → 3`; `34` nach Merge von PR 2 und PR 4 (und Freigabe).
- **DAG PR 1:** `4 → (5 ∥ 6 ∥ 8)`; `6 → 7`; `8 → 9`; `9 → 10 (OPTIONAL)`; `(7, 9) → 11`; `(5, 7, 9, 11) → 12`; `12 → 13 → 14`. Task 10 läuft, falls ausgeführt, vor Task 12 (Version-Bump, Gate in Task 12) und Task 13 (Rebaseline).
- **DAG PR 2:** `14 → 15`; `15 ∥ 16`; `16 → 17`; `(15, 17) → 18` ; `(15, 16, 17, 18) → 19 → 20 → 21`; bedingt `(17, 20) → 35 → 21` (nur bei Hook-Fix nach R1 (b), Gate in Task 21).
- **DAG PR 4:** `14 → 22 → 23`; `22 ∥ 24 ∥ 25` (disjunkt zu PR 2); `(23, 24, 25) → 26 → 27`; bedingt `26 → 36 → 27` (nur wenn AC-01 nach Task 26 rot, Gate in Task 27).
- **DAG PR 3:** `(21, 27) → 28 → 29 → 30 → 31`; `30 → 32`; `(31, 32) → 33`.
- **PR 0b:** `(21, 27) → 34` (und Freigabe): #961 nach PR 2, #856 nach PR 4.

## File Structure

**Create:**
- Create: `tests/test_deployed_guard_hooks_identity.py` — Byte-Identität `.agents/hooks/` vs. Render der Quelle (AC-2.14), Task 18
- Create: `tests/fixtures/doctor/rules-file-wrong-suffix/negative/.github/instructions/.agent-meta-managed`, `…/.github/instructions/.agent-meta-managed-mcp`, `…/.github/instructions/.agent-meta-managed-tools` — Negativ-Fixture (AC-4.7), Task 24
- Create: `tests/scenarios/configs/87-project-description-seed.project.yaml`, `tests/scenarios/asserts/87-project-description-seed.sh` — Szenario für die neue Option `project.description` (Skill `conventions`), Task 30
- Create: `.tmp/wave3-*.md` — Scratch-Messprotokolle (nicht committen), Tasks 4, 6, 13, 19, 33

**Modify (Hooks/Regeln):**
- Modify: `hooks/1-generic/dod-push-check.sh` — Dedup-Meldung (PR 1); bedingt #954-Fix (PR 2, R1)
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh`, `hooks/1-generic/orchestrator-guard.sh` — `is_fork_bomb`, Klassifikator, Header-known-gaps
- Modify: `hooks/1-generic/repo-containment.sh`, `hooks/1-generic/repo-containment-impl.sh` — Exit-Normalisierung, Detector-rc
- Modify: `rules/1-generic/branch-guard.md` — »Bekannte Grenzen« (AC-1.10)

**Modify (Code/Config):**
- Modify: `scripts/lib/hooks.py`, `scripts/lib/hook_plugins.py` — vier `write_atomic`-Aufrufstellen
- Modify: `scripts/admin-server.py` — `_effective_allowed_hosts`, `check_origin`-Meldung, `--allowed-hosts`-Hilfetext
- Modify: `scripts/lib/doctor_detectors.py` — Manifest-Ausschluss in `_glob_matches`/`_files_in`
- Modify: `config/role-defaults.yaml` — `handoff.input_contracts`
- Modify: `scripts/lib/config.py`, `scripts/lib/setup.py`, `scripts/lib/consistency/placeholders.py`, `config/project-config.schema.json`, `agents/1-generic/_reference-agent.md` — Variablen/Ratchet/Schema

**Modify (Tests/Fixtures/Doku):**
- Modify: `tests/test_dod_push_check_hook.py`, `tests/test_orchestrator_guard_hook.py`, `tests/test_repo_containment_hook.py`, `tests/test_newline_normalization.py`, `tests/test_admin_server.py`, `tests/test_doctor_runner.py`, `tests/test_consistency_checks.py`, `tests/test_config_variable_fallbacks.py`, `tests/test_build_variables_decomposition.py`, `tests/test_template_integrity_checks.py`
- Modify: `tests/fixtures/ac01-baseline/hashes.json`, `tests/test_ac01_render_identity.py`, `tests/test_opencode_v2_surface.py` — Rebaselines (PR 1, PR 3; PR 2/4 bedingt: Tasks 35, 36)
- Modify: `.agents/hooks/orchestrator-guard.sh`, `.agents/hooks/orchestrator-guard-impl.sh`, `.agents/hooks/repo-containment.sh`, `.agents/hooks/repo-containment-impl.sh`, `.meta-config/generated-file-hashes.json` — Self-Sync-Ergebnis (versioniert), Task 13
- Modify: `tests/scenarios/registry.md` — Szenario 87, Task 30
- Modify: `docs/providers/zcode.md`, `CHANGELOG.md`

## Step-Agent-Map (plan-driven implement)

| Step | Task | Agent |
|---|---|---|
| 5 | #1033 Dedup Block-Meldung | developer |
| 6 | #943 `is_fork_bomb` linear | senior-developer |
| 7 | #943 Klassifikator fail-closed | senior-developer |
| 8 | #944 Wrapper-Exit-Normalisierung | developer |
| 9 | #944 Detector-Absturz blockt | developer |
| 15 | #961 `write_atomic`-Schreibpfade | developer |
| 16 | #951 hermetische Test-Umgebung | developer |
| 22 | #897 `_effective_allowed_hosts` | developer |
| 23 | #897 Host-Header-Hinweis/Hilfetext | developer |
| 24 | #1034 Manifest-Ausschluss Doctor | developer |
| 28 | #1031 Output-Contracts verdrahten | developer |
| 29 | #983 `TECH_STACK`-Fallback, Ratchet | developer |
| 30 | #1037 `project.description`-Seed | senior-developer |

> `pipeline_stages.implement = 5` entspricht Step 5 (Task 5, Agent `developer`, in `allowed_agents` der `feature-lifecycle`-Stage `implement`: `junior-developer`, `developer`, `senior-developer`, `frontend-component-engineer`, `config/role-defaults.yaml` ~:2654-2664). Step = Task-Nummer. Auswertung: `scripts/lib/pipelines.py:parse_plan_ref`/`validate_plan_ref` (~:676-760; Frontmatter nur am Dateianfang, Tabellenzeilen `| <Zahl> | … | <agent> |`). Nicht in der Map: Tasks mit `tester`/`documenter` (nicht in `allowed_agents`) und der OPTIONALE Task 10 (Agent `developer`, nur bei Ausführung nachtragen).

---

## PR 0 — Housekeeping (nur nach ausdrücklicher Freigabe des Nutzers)

**Branch:** keiner (reine Issue-Verwaltung, kein Repo-Diff). **Entry:** ausdrückliche Freigabe des Nutzers; `gh auth status` lesend grün. **Exit:** je ausgeführtem Befehl Prüfung per `/home/hermes/.local/bin/gh issue view <N> --json state,stateReason`. **Rollback:** `/home/hermes/.local/bin/gh issue reopen <N> --comment "..."`.
**ALLE Befehle und Texte unten sind Entwürfe. Sie werden von diesem Plan weder ausgeführt noch vom Planer, Entwickler oder Tester ohne Freigabe.**

### Task 1: PR 0a — Issue-Zustand klären (Q1) und Reopen-Entwürfe
**Agent:** documenter · **Issue:** Q1, Spec »Scope-Befund A« · **AC:** — (Voraussetzung für »Closes« vs. »Refs«)
**Depends on:** —
**Gate:** nur nach ausdrücklicher Freigabe und nach Q1-Entscheidung des Nutzers (vor PR-1-Start).
**Files:**
- Modify: `docs/plans/2026-10-29-bugfix-wave-3-plan.md`
**Interfaces:** Produces Entscheidung Q1 im Plan-Vermerk und, bei Reopen, die Texte unten; Consumes Spec Befund A (zehn geschlossene Issues, acht nicht existierende Fix-Commits).
- [ ] Step 1: Lesend prüfen (kein Schreibaufruf): `/home/hermes/.local/bin/gh issue view 1033 --json state,stateReason,closedAt,comments` und analog für #943, #944, #961, #951, #954, #1031, #983, #1037, #1034; bestätigen, dass `state=CLOSED` und der Kommentar auf die Hashes `587e8684`, `c85ee04e`, `ebfa789b`, `24233481`, `26d2affa`, `63b12bde`, `af9abe9e`, `f9c33165` verweist. Hash-Existenz lesend über den `git`-Agenten prüfen: `git cat-file -e <hash>^{commit}` je Hash → erwartet: Fehler (`Not a valid object name`).
- [ ] Step 2: Q1 dem Nutzer vorlegen (Default: Reopen). Entscheidung hier vermerken: `Q1: Reopen | neue Issues` (Datum).
- [ ] Step 3 (nur bei Reopen): Befehl je Issue (Entwurf, **nicht ausführen ohne Freigabe**):
  ```
  /home/hermes/.local/bin/gh issue reopen 1033 --comment "Reopening: the closing comment (2026-10-29) cites commit <hash>, which does not exist in this repository (not on any branch of origin). On origin/main at 043d29a4 the defect is still present: <symbol and file from the spec section>. The fix is planned in PR '<branch>' (spec: docs/specs/2026-10-29-bugfix-wave-3-spec.md)."
  ```
  `<branch>` je Issue: #1033, #943, #944 → `fix/hooks-hardening-w1` (PR 1); #961, #951, #954 → `fix/hooks-py-lf-and-tests` (PR 2); #1031, #983, #1037 → `fix/config-contracts-placeholders` (PR 3); #1034 → `fix/admin-ui-network-and-doctor` (PR 4).
  Je Issue die Symbol-Angabe aus der Spec einsetzen: #1033 `hooks/1-generic/dod-push-check.sh` Block-Meldung (doppeltes `main`); #943 `is_fork_bomb` quadratisch (nur Teil (a)(m)); #944 `repo-containment.sh` Exit-Durchreichung und `repo-containment-impl.sh` `|| true`; #961 `scripts/lib/hooks.py` `create_hook` und drei Managed-Indizes ohne LF-Garantie; #951 `tests/test_dod_push_check_hook.py::_run_hook` erbt `AGENT_META_*`; #954 ausgelassene Re-Review-Checks ohne Tests; #1031 acht `handoff.output-not-consumed`-Warnungen; #983 `_UNKNOWN_TEMPLATE_RATCHET` nicht leer; #1037 `project.description` ohne Seed; #1034 `rules-file-wrong-suffix` meldet `.agent-meta-managed*`.
- [ ] Step 4 (nur bei »neue Issues«): je Issue ein Neu-Issue-Entwurf analog Task 3; PR-Beschreibungen verwenden dann die neuen Nummern.
- [ ] Step 5: Ergebnis (reopened/neu/übersprungen) im Plan vermerken. Kein Code-Commit.

### Task 2: PR 0 — Schließ-Kandidaten aus D2 (Entwürfe, nicht ausführen)
**Agent:** documenter · **Issue:** #948, #950, #952, #953, #207, #534, #865, #962, #192 · **AC:** — (D2)
**Depends on:** 1
**Gate:** nur nach ausdrücklicher Freigabe. Befund A: #948, #950, #952, #953 sind bereits **geschlossen** (COMPLETED); offen sind #207, #534, #865, #962 (und #971, siehe Task 34). #192 **bleibt offen** (Inventar: laut #959 superseded; keine Aktion, nur Vermerk).
**Files:**
- Modify: `docs/plans/2026-10-29-bugfix-wave-3-plan.md`
**Interfaces:** Produces ausführungsbereite `gh`-Befehle und englische Begründungskommentare; Consumes Issue-Inventar (Typ/Status-Verdacht), Spec D2 und Befund A.
- [ ] Step 1: Vorab lesend: `/home/hermes/.local/bin/gh issue close --help` (gültige `--reason`-Werte der installierten Version, **nicht verifiziert**: `completed|not planned`, ggf. `--duplicate-of`), und `/home/hermes/.local/bin/gh issue view <N> --json state,labels,title` für #207, #534, #865, #962.
- [ ] Step 2: Befehle (Entwürfe; Begründungen stammen aus dem Issue-Inventar und müssen vor Ausführung gegen den Issue-Text geprüft werden):
  ```
  /home/hermes/.local/bin/gh issue close 207 --reason "not planned" --comment "Closing as not planned: the issue already carries the wontfix label and the autonomous MBSE engine (SE-Runner) is not on the roadmap. Reopen if scope changes."
  /home/hermes/.local/bin/gh issue close 534 --reason "not planned" --comment "Closing: this is a research note (agent platform HACS) without an actionable scope; remaining best-practice gaps are tracked in #676. Reopen with a concrete requirement if needed."
  /home/hermes/.local/bin/gh issue close 865 --reason "not planned" --comment "Closing: the reviewed PR #839 (docs-consolidation) was closed without merge, so the review findings no longer apply to main. Reopen if the consolidation is resumed."
  /home/hermes/.local/bin/gh issue close 962 --reason "not planned" --comment "Closing as duplicate of #957 (PR template system with layered overrides and variable substitution). Tracking continues in #957."
  ```
  Für #962 prüfen, ob die installierte `gh`-Version `--reason duplicate` bzw. `--duplicate-of 957` kennt; sonst bleibt »not planned« mit Duplikat-Kommentar.
- [ ] Step 3: #948, #950, #952, #953: **kein** `close`-Befehl (bereits geschlossen). Entwurf eines Korrekturkommentars, nur falls Q1 »Reopen« und Nutzer es wünscht:
  ```
  /home/hermes/.local/bin/gh issue comment 948 --body "Note: PR #956 resolved this report; the issue was closed on 2026-10-29. [nach Bestätigung: Verified against origin/main 043d29a4.]"
  ```
  (analog #950, #952; für #953 siehe Task 3 — das Folge-Issue deckt die verbleibende Lücke.) Der Satz in `[nach Bestätigung: …]` wird nur übernommen (ohne Klammer-Markierung), nachdem der Nutzer die Verifikation bestätigt hat; sonst ersatzlos streichen (Verifikation nicht Teil dieses Plans).
- [ ] Step 4: #192 bleibt offen: kein Befehl. Vermerk im Ergebnis.
- [ ] Step 5: Kein Code-Commit.

### Task 3: PR 0 — Folge-Issue-Entwürfe (#953-Rest, Epic-Reste #943/#944, Nicht-Ziele)
**Agent:** documenter · **Issue:** #953, #943, #944 · **AC:** — (D2, D6)
**Depends on:** 1
**Gate:** nur nach ausdrücklicher Freigabe; Anlage über den Orchestrator (Skill `issue-lifecycle`). Issue-Texte Englisch.
**Files:**
- Modify: `docs/plans/2026-10-29-bugfix-wave-3-plan.md`
**Interfaces:** Produces vier Issue-Text-Entwürfe (Titel + Body) und die Anlage-Befehle; Consumes Spec D2/D6, Nicht-Ziele, Q1.
- [ ] Step 1: **Folge-Issue #953** (Entwurf):
  > **Title:** `fix: dod-push-check does not detect push.recurseSubmodules set via git config or -c`
  >
  > **Problem:** `hooks/1-generic/dod-push-check.sh` classifies pushes by command-line flags. A `push.recurseSubmodules` value that is set through repository/global git config or through `git -c push.recurseSubmodules=... push` is not recognised, so a push that recurses into submodules may bypass the protected-branch check of the submodule. Residual gap after #953 (closed 2026-10-29).
  >
  > **Repro (unverified, to be confirmed):** 1. Repo with a submodule and `git config push.recurseSubmodules on-demand`. 2. Run a push of a protected branch inside the superproject via the Bash tool. 3. Observe the hook verdict for the submodule's branch (expected: block; observed: not verified).
  >
  > **Proposal:** Cover the config/`-c` forms in the Python classifier (compare with the existing `GIT_CONFIG_PARAMETERS`/`GIT_CONFIG_COUNT` tests); fail closed when the value cannot be determined; tests per `push.default` matrix of wave 3 (AC-2.13). **References:** #953, #954, `SPEC-bugfix-wave-3`.
  
  Anlage (Entwurf): `/home/hermes/.local/bin/gh issue create --title "fix: dod-push-check does not detect push.recurseSubmodules set via git config or -c" --label bug --body-file .tmp/wave3-issue-953-followup.md`.
- [ ] Step 2: **Folge-Issues D6** (Entwürfe, je eigene Spec vor Implementierung): (a) Titel `fix: remaining items of epic #943 after wave 3`, Body: »Wave 3 delivers only item (a)(m) (`is_fork_bomb` linear, classifier fail-closed). All other items of #943 are re-scoped here; an own spec is required before implementation. Prerequisite candidate: #945 (guard test isolation, CI timeouts). Refs #943, `SPEC-bugfix-wave-3`.« (b) Titel `fix: remaining items of epic #944 after wave 3`, Body analog: delivered are SR-B-17 and the `|| true` detector crash; open: SR-B-19 (in-place flags, `cp -t DIR`) if Task 10 was not executed, plus all other #944 items. Die konkrete Item-Liste ist dem Body von #943/#944 zu entnehmen (im Plan nicht verifiziert).
- [ ] Step 3: **Folge-Issues aus den Nicht-Zielen** (nur Titel-Entwürfe, Anlage optional): (1) `fix: ~75 Path.write_text calls in scripts/ without newline= (CRLF on Windows)` (u. a. `scripts/lib/skills.py` managed index); (2) `fix: hard-coded repo identity in URL form (standalone.py REPO_URL, hermes_export.py REPO_URL, admin-server.py model-registry raw URL)`; (3) `fix: spec_plan validator classifies *-spec.md as plan (_DESIGN_RE)`; (4) `feat: _SET flags + {{#if}} for derivable variables (#425 pattern) instead of empty fallbacks`; (5) `feat: admin-server wildcard bind: detect IPv6/hostnames via getaddrinfo`; (6) `chore: #1032 Gemini/Antigravity hooks.json cwd-dependent` ist bereits ein eigenes Issue und entfällt.
- [ ] Step 4: Kein Code-Commit.

## PR 1 — `fix/hooks-hardening-w1` (Security zuerst, D3)

**Branch:** `fix/hooks-hardening-w1` (angelegt vom `git`-Agenten auf aktuellem `origin/main`).
**Entry:** Q1, Q3, Q6 entschieden; Spec APPROVED; Task 1 (falls freigegeben) erledigt, damit die PR-Beschreibung »Closes«/»Refs« kennt.
**Exit:** (1) `python3 -m pytest tests/test_dod_push_check_hook.py tests/test_orchestrator_guard_hook.py tests/test_repo_containment_hook.py tests/test_ac01_render_identity.py tests/test_opencode_v2_surface.py -q` grün; (2) `python3 scripts/sync.py --validate` Exit 0; (3) `python3 -m pytest tests -q` ohne `failed`/`error`; (4) `# version:`-Header gebumpt, `CHANGELOG.md`-Eintrag (AC-1.20); (5) genau ein Rebaseline (AC-1.21); (6) `check_stale_deployed_hooks` ohne Findings nach `python3 scripts/sync.py` (AC-1.22).
**Rollback:** `git revert` des Merge-Commits durch den `git`-Agenten (inkl. `hashes.json`, `_FIXTURE_TREES`); danach `python3 scripts/sync.py` zum Rücksetzen der lokalen/deployten Hook-Kopien; Folge: Fail-open-Verhalten von `is_fork_bomb`/Klassifikator/`|| true` ist wieder aktiv (Sicherheitsrückschritt, Nutzer informieren).
**Branch-Mutation-Hinweis:** `.claude/hooks/*` ist gitignored und lokal; Hook-Änderungen wirken im Repo erst nach `python3 scripts/sync.py`.

### Task 4: PR 1 Entry — Ausgangsmessung (AC-1.11) und Test-Mechanik klären
**Agent:** tester · **Issue:** #943 · **AC:** AC-1.11 (Vorher-Werte)
**Depends on:** —
**Files:**
- Create: `.tmp/wave3-pr1-timing-before.md`
**Interfaces:** Produces Messprotokoll (best-of-3, `time.perf_counter`) für `is_fork_bomb` Skalierung (AC-1.5, AC-1.6) und e2e-Hook (AC-1.9) **vor** dem Fix sowie die geklärte Test-Mechanik (siehe Step 2); Consumes `hooks/1-generic/orchestrator-guard-impl.sh` (Python-Block :333–:846, `is_fork_bomb` :805).
- [ ] Step 1: Symbole prüfen: `Grep` `def is_fork_bomb` und `_GIT_SCAN_RAW` in `hooks/1-generic/orchestrator-guard-impl.sh` → je ≥ 1 Treffer; `Grep` `Protected branches` in `hooks/1-generic/dod-push-check.sh` → genau 1 Treffer (:1071).
- [ ] Step 2: **Offene Mechanik (Spec: unverifiziert):** Wie isoliert der Test die in die `.sh` eingebettete Python-Funktion? Der Block steht in einem Bash-Doppelquote-String (`"$_PY" -c "…"`, :333–:846; Escaping von `\"`, `\$`, `` \` `` beachten). Vorschlag (Default): Test-Helfer `_load_is_fork_bomb()` extrahiert den Python-Quelltext zwischen `-c "` und dem schließenden `" "$PAYLOAD_CWD"`, entschärft das Bash-Escaping (`\\` → `\`, `\"` → `"`, `\$` → `$`), führt ihn per `exec` in einem Namespace aus, in dem `sys.argv`/`stdin` bedient sind, und gibt `is_fork_bomb` zurück. Falls die Extraktion nicht robust ist: Alternative (b) Skalierungs-AC nur e2e über den Hook (AC-1.9-Stil, Eingaben ≥ 20 KB), Funktionsebene nur manuell dokumentiert. Entscheidung durch den ausführenden Agenten dokumentieren (im Messprotokoll) und bei Alternative (b) an den Nutzer melden (AC-1.5/AC-1.6 ändern ihre Messebene).
- [ ] Step 3: Vorher-Messung (Altcode, Ausgabe im Protokoll): `is_fork_bomb("a"*20000 + "(){ :; }")` → erwartet ≈ 4,9 s (Spec: 4,9 s Funktionsebene, 5,16 s e2e); `"f(){ " * 60000` darf wegen 86 s **nicht** vollständig gemessen werden — Timeout-Schutz `timeout 120`; je best-of-3 mit `time.perf_counter`.
- [ ] Step 4: Kein Commit (Scratch in `.tmp/`).

### Task 5: #1033 — doppeltes `main` in der Block-Meldung (B1)
**Agent:** developer · **Issue:** #1033 · **AC:** AC-1.1, AC-1.2, AC-1.3, AC-1.4 · **parallel_group:** g1
**Depends on:** 4
**Files:**
- Modify: `hooks/1-generic/dod-push-check.sh`
- Modify: `tests/test_dod_push_check_hook.py`
**Interfaces:** Produces stderr-Text `Protected branches: <MAIN_BRANCH, main, master ohne Duplikate>. Push a feature branch and open a PR instead.` (reine Shell, Reihenfolge MAIN_BRANCH, main, master); Consumes `MAIN_BRANCH` (Env `AGENT_META_MAIN_BRANCH` > Config-Key `GIT_MAIN_BRANCH` via `read_config_var` > `main`, :221-226).
- [ ] Step 1: Tests schreiben (fail) in `tests/test_dod_push_check_hook.py`: `test_block_message_dedups_default_main` (kein Env/Config; Push auf `main` im Test-Repo → `result.stderr` enthält `Protected branches: main, master.`), `test_block_message_lists_custom_main_branch` (`AGENT_META_MAIN_BRANCH=develop`; Push auf `develop` → `Protected branches: develop, main, master.`), `test_block_message_dedups_master_main_branch` (`AGENT_META_MAIN_BRANCH=master` → `Protected branches: master, main.`), `test_block_message_lists_config_main_branch` (`variables: {GIT_MAIN_BRANCH: develop}` in `.meta-config/project.yaml` über `_run_hook_with_config` → `Protected branches: develop, main, master.`). **Helfer-Hinweis (verifiziert):** `_run_hook(cwd, command)` (:42) nimmt **kein** `env_extra`; für die Env-Fälle `_assert_outcome(..., env_extra=...)` (:390) bzw. `_run_payload(repo, payload, env_extra)` (:832) verwenden oder einen Helfer mit stderr-Rückgabe ergänzen; vorhandene Block-Fälle als Vorlage (`Grep` `Protected branches` in der Testdatei → heute 0 Treffer).
- [ ] Step 2: `python3 -m pytest tests/test_dod_push_check_hook.py -k "block_message"` → Erwartung: `2 failed, 2 passed` — rot: Default (`AssertionError: 'Protected branches: main, master.' not found in '... Protected branches: main, main, master. ...'`) und `master`-Fall (heute `master, main, master`); grün: `develop`-Env- und `develop`-Config-Fall (heute schon `develop, main, master`, Charakterisierungstests für Reihenfolge und Config-Pfad). Ergebnis je Test festhalten. (Lauf ohne `-x`, damit alle vier berichtet werden.)
- [ ] Step 3: Implementieren in `hooks/1-generic/dod-push-check.sh` an der Meldungsstelle (:1071): Liste per Shell aufbauen (`PROTECTED_LIST="$MAIN_BRANCH"`; `main` anhängen, wenn `[ "$MAIN_BRANCH" != "main" ]`; `master` anhängen, wenn `[ "$MAIN_BRANCH" != "master" ]`; Trennung `, `), `echo "Protected branches: ${PROTECTED_LIST}. Push a feature branch and open a PR instead." >&2`. Sonstiger Text unverändert; Python-Klassifikator (`PROTECTED = {"main","master",MAIN_BRANCH} - {""}` :531) nicht anfassen. Leerer `MAIN_BRANCH` (kann Config-Fehler liefern) darf keinen führenden `, ` erzeugen: leerer Wert → Liste beginnt mit `main`.
- [ ] Step 4: `python3 -m pytest tests/test_dod_push_check_hook.py -q` → alle grün (`4` neue Tests bestanden, keine Regression).
- [ ] Step 5: commit `fix: dedupe protected branch list in dod-push-check message`

### Task 6: #943(a)(m) — `is_fork_bomb` linear (B2)
**Agent:** senior-developer · **Issue:** #943 · **AC:** AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9, AC-1.10 (Block-Meldung), AC-1.11 (Nachher-Werte) · **parallel_group:** g1
**Depends on:** 4
**Files:**
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh`
- Modify: `tests/test_orchestrator_guard_hook.py`
- Modify: `.tmp/wave3-pr1-timing-before.md` (Scratch aus Task 4, Abschnitt »nachher«; **nicht committen**)
**Interfaces:** Produces `is_fork_bomb(command: str) -> bool` mit Lookbehind-Header `(?<![A-Za-z0-9_:])([A-Za-z_:][A-Za-z0-9_:]*)\s*\(\s*\)\s*\{` (keine Namenslängengrenze) und Body-Fenster `str.find('}', end, end + 1024)` — **ohne `}` im Fenster → `True` (Block)**; Exception propagiert (kein lokales `try/except`), keine Kappung der Gesamteingabe; Destructive-Block-Meldung (:873-878) um eine konditionale Hinweiszeile zur Fenstergrenze ergänzt (enthält `1024`, »unquoted `}`«, Verweis auf `branch-guard` »Bekannte Grenzen«; Klassifikator-Ausgabeformat unverändert, Spec Fix-Vertrag/R3); Consumes Q3-Default (a) aus der Spec und die Mechanik aus Task 4. Einziger Aufrufer: `destructive = is_fork_bomb(strip_quoted(command))` (:816).
- [ ] Step 1: Symbol prüfen: `Grep` `is_fork_bomb` in `hooks/1-generic/orchestrator-guard-impl.sh` → genau 2 Treffer (Definition :805, Aufruf :816) — weitere Aufrufer wären Geschwisterpfade.
- [ ] Step 2: Tests schreiben (fail) in `tests/test_orchestrator_guard_hook.py` (Mechanik aus Task 4): `test_fork_bomb_linear_on_long_identifier` (AC-1.5: n = 300 000 und 600 000, best-of-3, `t(600k)/t(300k) < 3` und `t(300k) < 1 s`), `test_fork_bomb_linear_on_repeated_headers` (AC-1.6: (i) `"f(){ " * 60000` → `True` in < 1 s; (ii) `"f(){ x} " * k` für k = 60 000/120 000, `t(120k)/t(60k) < 3` und `t(60k) < 1 s`), `test_fork_bomb_body_window_exhausted_blocks` (AC-1.7: `"f(){ " + "x"*1025` → `True`; `"f(){ " + "x"*1000 + " }"` → `False`; `"f(){ " + "x"*2000 + " f|f& }"` → `True`), `test_fork_bomb_long_name_detected` (AC-1.8: `"b"*100 + "(){ " + "b"*100 + "|" + "b"*100 + "& };"` erkannt; vorhandene `test_fork_bomb_blocked`/`test_fork_bomb_text_literal_not_blocked` unverändert), `test_fork_bomb_end_to_end_long_input_fast` (AC-1.9: 20 KB Bezeichner über den Hook, korrektes Verdikt, < 2 s), `test_fork_bomb_window_block_message_names_limit` (AC-1.10: Hook e2e mit `"f(){ " + "x"*1025` → exit 2, stderr enthält `1024`).
  **Watchdog-Pflicht (Rot-Phase ohne Hänger):** Jeder gemessene Aufruf (AC-1.5, AC-1.6 (i) **und** (ii), AC-1.9, AC-1.10) läuft in einem Subprozess mit `subprocess.run([...], timeout=5)` — für die Funktionsebene ein `sys.executable -c`-Lauf, der die per Task-4-Mechanik extrahierte Funktion lädt, best-of-3 per `time.perf_counter` misst und Verdikt + Zeiten als JSON auf stdout ausgibt; e2e der Hook-Aufruf selbst. `subprocess.TimeoutExpired` → `pytest.fail("watchdog: … exceeded 5 s")`. Derselbe Test ist vor dem Fix rot (Timeout = Fail) und nach dem Fix grün; keine gekappte Sonder-Eingabe, kein `pytest.mark` nur für die Rot-Phase.
- [ ] Step 3: Rot-Lauf: `python3 -m pytest tests/test_orchestrator_guard_hook.py -k "fork_bomb_linear or body_window or long_name or end_to_end_long or window_block_message"` (ohne `-x`) → Erwartung: `5 failed, 1 passed` — rot: `…long_identifier` (Watchdog: 300 k Bezeichner quadratisch, Altwert 20 KB = 4,9 s), `…repeated_headers` (Watchdog an (i), Altverhalten 86 s), `…body_window_exhausted_blocks` (heute `False` für 1025 `x`), `…end_to_end_long_input_fast` (Watchdog bzw. > 2 s, Altwert 5,16 s), `…window_block_message_names_limit` (heute exit 0, kein Treffer ohne `}`); grün: `…long_name_detected` (Altregex ohne Längengrenze, Charakterisierungstest). Maximale Rot-Laufzeit ≈ 4 × 5 s Watchdog.
- [ ] Step 4: Implementieren in `orchestrator-guard-impl.sh` (Python-Block): Regex auf Lookbehind-Header umstellen und den Body nicht mehr per `[^}]*` matchen, sondern: nach dem Header-Match `close = command.find('}', m.end(), m.end() + 1024)`; `close == -1` → `return True`; sonst Body = `command[m.end():close]` wie bisher prüfen (Self-Pipe-/Rekursions-Logik unverändert). Kommentare im Block aktualisieren (Fehlalarm-Grenze R3 benennen). **Kein** `try/except` um die Funktion. Destructive-Block-Meldung um die Hinweiszeile ergänzen (Englisch, z. B. `If this is a shell function whose first 1024 body characters contain no unquoted '}', it is blocked by the fork-bomb window limit (see branch-guard: known limits).`).
- [ ] Step 5: Grün: `python3 -m pytest tests/test_orchestrator_guard_hook.py -q` → alle grün; Nachher-Messung (AC-1.11) ins Protokoll `.tmp/wave3-pr1-timing-before.md` (Abschnitt »nachher«): Erwartung laut Spec-Prototyp 300/600 KB Bezeichner ≈ 2,3/4,2 ms; `"f(){ x} "` × 60k/120k ≈ 108/212 ms. Grenzen nur lockern, wenn ein Wert näher als Faktor 3 an der Grenze liegt (AC-1.11) — dann in der PR-Beschreibung begründen.
- [ ] Step 6: commit `fix: make is_fork_bomb linear and block exhausted body window`

### Task 7: #943-Geschwister — Klassifikator-Absturz fail-closed (B2)
**Agent:** senior-developer · **Issue:** #943 · **AC:** AC-1.12, AC-1.13
**Depends on:** 6
**Files:**
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh`
- Modify: `tests/test_orchestrator_guard_hook.py`
**Interfaces:** Produces Klassifikator-Aufruf ohne `|| echo "none narrow none"`: Exit-Code erfassen; rc ≠ 0 **oder** Ausgabe ≠ `<none|mutation|destructive> <narrow|broad> <none|message|file>` → stderr `ORCHESTRATOR_GUARD: command classifier failed rc=<n>, failing closed` + `exit 2` (unabhängig von Sentinel/Strict-Mode); Consumes Task 6 (`is_fork_bomb`-Contract: Exception → rc ≠ 0), Wrapper-Normalisierung `orchestrator-guard.sh:55-66`.
- [ ] Step 1: Symbole prüfen: `Grep` `none narrow none` in `hooks/1-generic/orchestrator-guard-impl.sh` → 2 Treffer (Kommentar :328, Fallback :846). Übrige `"$_PY" -c`-Aufrufe (:145, :189, :195, :265, :280, :905) sind laut Spec fail-closed/restriktiv und werden **nicht** angefasst.
- [ ] Step 2: Tests schreiben (fail): `test_classifier_crash_fails_closed` (PATH-Shim `python3` in `tmp_path`, der **nur** bei Marker `def is_fork_bomb` im `-c`-Argument mit rc 1 endet und sonst das echte Python per `exec` startet; Bash-Befehl `ls` → Exit 2, stderr enthält `command classifier failed rc=`) und `test_classifier_garbage_output_fails_closed` (Shim druckt `garbage` und rc 0 → Exit 2). Vorlage für Wrapper/Shim-Mechanik: `test_wrapper_fails_closed_on_impl_crash` (:1332).
- [ ] Step 3: `python3 -m pytest tests/test_orchestrator_guard_hook.py -k "classifier" -x` → Erwartung: `2 failed` (`assert 0 == 2` — heute Allow durch Fallback `none narrow none`).
- [ ] Step 4: Implementieren: `_GIT_SCAN_RAW=$(… 2>/dev/null)` mit `_GIT_SCAN_RC=$?`; Validierung der Ausgabe per `case`/Regex auf die drei Felder; bei Verstoß Meldung + `exit 2`. Kommentar :320-329 (»fail-open, matching the prior gates«) durch die neue Fail-closed-Aussage ersetzen (**benannte Verhaltensänderung**, Spec R2: reproduzierbarer Klassifikator-Absturz blockt jeden Bash-Aufruf, auch mit `git`-Sentinel).
- [ ] Step 5: `python3 -m pytest tests/test_orchestrator_guard_hook.py -q` → alle grün (inkl. `test_wrapper_fails_closed_on_impl_crash`).
- [ ] Step 6: commit `fix: fail closed when orchestrator guard classifier crashes`

### Task 8: #944 SR-B-17 — Wrapper-Exit-Normalisierung (B3)
**Agent:** developer · **Issue:** #944 · **AC:** AC-1.14, AC-1.15 · **parallel_group:** g1
**Depends on:** 4
**Files:**
- Modify: `hooks/1-generic/repo-containment.sh`
- Modify: `tests/test_repo_containment_hook.py`
**Interfaces:** Produces Wrapper-Verhalten: `PIPESTATUS[1]` auswerten; `0` → 0, `2` → 2, alles andere → stderr-Meldung + `exit 2`; Consumes Referenzmuster `hooks/1-generic/orchestrator-guard.sh:55-66`.
- [ ] Step 1: Symbole prüfen: `Grep` `exit \$\?` in `hooks/1-generic/repo-containment.sh` → Treffer (:46-48); Muster `PIPESTATUS` in `hooks/1-generic/orchestrator-guard.sh`.
- [ ] Step 2: Tests schreiben (fail): `test_wrapper_fails_closed_on_impl_crash` (parametrisiert rc ∈ {1, 137, 141}; Impl-Stub, der mit dem rc endet; Vorlage `tests/test_orchestrator_guard_hook.py:1332` — Aufbau wie dort prüfen, nicht kopieren ohne Anpassung an `repo-containment.sh`), Durchreich-Fälle rc 0 und rc 2 (AC-1.15).
- [ ] Step 3: `python3 -m pytest tests/test_repo_containment_hook.py -k wrapper -x` → Erwartung: `3 failed` für rc 1/137/141 (`assert 1 == 2`, heute Durchreichen), Durchreich-Fälle grün.
- [ ] Step 4: Implementieren (Muster aus `orchestrator-guard.sh`), Meldungstext `repo-containment: impl exited rc=<n>, failing closed` (Englisch).
- [ ] Step 5: `python3 -m pytest tests/test_repo_containment_hook.py -q` → alle grün.
- [ ] Step 6: commit `fix: normalize repo-containment wrapper exit to fail closed`

### Task 9: #944 `|| true` — Write-Detector-Absturz blockt (B4)
**Agent:** developer · **Issue:** #944 · **AC:** AC-1.16, AC-1.17
**Depends on:** 8
**Files:**
- Modify: `hooks/1-generic/repo-containment-impl.sh`
- Modify: `tests/test_repo_containment_hook.py`
**Interfaces:** Produces Detector-Aufruf ohne `|| true`: rc ≠ 0 → stderr `repo-containment: write detector failed rc=<n>, failing closed` + `exit 2`; rc 0 ohne Kandidaten bleibt Allow; Consumes `containment_verdict`-Auswertung (:560, :709, fail-closed im `*)`-Zweig, unverändert).
- [ ] Step 1: Symbole prüfen: `Grep` `WRITE_TARGETS=` und `\|\| true` in `hooks/1-generic/repo-containment-impl.sh` (:702); Kommentar :574-581 (»best-effort«) wird mitgeändert (**benannte Verhaltensänderung**, R2).
- [ ] Step 2: Tests schreiben (fail): `test_bash_detector_crash_fails_closed` (PATH-Shim `python3`, der **nur** beim Detector-Aufruf — Marker `INPLACE = {` im `-c`-Argument, :600 — mit rc 1 endet und sonst echtes Python `exec`t; `_PY` wird vorher schon benutzt (`resolve_realpath` :162, `read_effective_containment` :332, `containment_verdict` :484), ein generell kaputtes Python würde den Test aus falschem Grund grün machen) und `test_bash_detector_no_targets_allows` (rc 0, keine Kandidaten → Allow).
- [ ] Step 3: `python3 -m pytest tests/test_repo_containment_hook.py -k "detector" -x` → Erwartung: `test_bash_detector_crash_fails_closed` rot (`assert 0 == 2`), `…no_targets_allows` grün.
- [ ] Step 4: Implementieren: Exit-Code des Detectors erfassen, `|| true` entfernen, Block bei rc ≠ 0; Kommentar aktualisieren.
- [ ] Step 5: `python3 -m pytest tests/test_repo_containment_hook.py -q` → alle grün.
- [ ] Step 6: commit `fix: block bash calls when repo-containment detector crashes`

### Task 10: OPTIONAL — #944 SR-B-19 (In-place-Flags, `cp -t DIR`)
**Agent:** developer · **Issue:** #944 · **AC:** AC-1.18, AC-1.19 (nur falls umgesetzt)
**Depends on:** 9
**Gate:** **OPTIONAL — nicht Pflichtumfang, nicht in der 13-Bug-Zählung.** Nur starten, wenn der Nutzer es ausdrücklich verlangt (mittleres Fehlalarm-Risiko). Wird er nicht ausgeführt: Task 12 bumpt ohne SR-B-19, und die Restpunkte gehen in das D6-Folge-Issue (Task 3). Läuft er, dann vor Task 12/13.
**Files:**
- Modify: `hooks/1-generic/repo-containment-impl.sh`
- Modify: `tests/test_repo_containment_hook.py`
**Interfaces:** Produces Detector-Erweiterung im Zweig `elif cmd in INPLACE:` (~:690): gebündelte Flags (`sed -Ei`, `perl -pi`) und `cp -t DIR` liefern Kandidaten; `sed -E`/`perl -p` ohne `i` bleiben ohne Kandidat; Consumes Task 9. Vollständigkeit weiterer `-t`-Kommandos (z. B. `mv -t`, `install -t`): **unverifiziert**, vor der Implementierung per `Grep` in `INPLACE`/Detector prüfen.
- [ ] Step 1: Tests schreiben (fail): `test_bundled_inplace_flags_detected` (`sed -Ei 's/a/b/' /etc/x`, `perl -pi -e … /etc/x`, `cp -t /etc a` → Block), `test_non_inplace_flags_not_flagged` (`sed -E 's/a/b/' f`, `perl -p -e … f` → kein Kandidat), `test_cp_target_dir_detected`.
- [ ] Step 2: `python3 -m pytest tests/test_repo_containment_hook.py -k "inplace or cp_target" -x` → Erwartung: Erkennungs-Tests rot, Nicht-Fehlalarm-Test grün.
- [ ] Step 3: Implementieren (Flag-Cluster-Parsing: Flag-Bündel auf `i` prüfen; `-t DIR` als Ziel auswerten).
- [ ] Step 4: `python3 -m pytest tests/test_repo_containment_hook.py -q` → alle grün.
- [ ] Step 5: commit `feat: detect bundled in-place flags and cp -t in repo-containment`

### Task 11: Header-known-gaps und `branch-guard`-Regel nachziehen (B2)
**Agent:** documenter · **Issue:** #943 · **AC:** AC-1.10
**Depends on:** 7, 9
**Files:**
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh`
- Modify: `hooks/1-generic/orchestrator-guard.sh`
- Modify: `rules/1-generic/branch-guard.md`
**Interfaces:** Produces Text in beiden Guard-Header-»known gaps« und in »Bekannte Grenzen« von `rules/1-generic/branch-guard.md`: Funktionskörper, deren erste 1024 Zeichen kein **ungequotetes** `}` enthalten, werden hart geblockt (Fehlalarm-Klasse R3; gequotetes `"${…}"` entfernt `strip_quoted` vorher; kein Ausweg über den `git`-Sentinel); Klassifikator-Absturz blockt; Consumes Tasks 6, 7, 9 (nur Kommentar-/Dokutext, keine Logik). Gerenderte Kopien (`.claude/rules/branch-guard.md`, `.continue/rules/…`, `.github/instructions/branch-guard.instructions.md`) entstehen per Sync (Task 13).
- [ ] Step 1: Prüfung vorher: `Grep` `1024` in den drei Dateien → 0 Treffer zur Body-Fenster-Grenze.
- [ ] Step 2: Texte ergänzen; `Grep` `classifier` und `1024` je Datei → ≥ 1 Treffer (Header beider Guard-Dateien und Regel).
- [ ] Step 3: Prüfung: `python3 scripts/sync.py --validate` → Exit 0.
- [ ] Step 4: commit `chore: document fork-bomb window limit and classifier fail-closed`

### Task 12: Versions-Header und Changelog (PR 1)
**Agent:** documenter · **Issue:** #1033, #943, #944 · **AC:** AC-1.20
**Depends on:** 5, 7, 9, 11
**Gate:** falls Task 10 (OPTIONAL) ausgeführt wird: erst nach dessen Abschluss starten.
**Files:**
- Modify: `hooks/1-generic/dod-push-check.sh`
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh`
- Modify: `hooks/1-generic/orchestrator-guard.sh`
- Modify: `hooks/1-generic/repo-containment.sh`
- Modify: `hooks/1-generic/repo-containment-impl.sh`
- Modify: `CHANGELOG.md`
**Interfaces:** Produces gebumpte `# version:`-Header — **Plan-Entscheidung der Stufen** (Spec: Stufe im Plan; Ausgangsstände 2.1.5 / 1.7.0 / 3.2.0 / 1.0.0 / 1.2.0): `dod-push-check.sh` 2.1.5 → 2.1.6 (Patch, Meldungstext), `orchestrator-guard-impl.sh` 1.7.0 → 1.8.0 (Minor, neuer Fail-closed-Pfad und Fenster-Grenze), `orchestrator-guard.sh` 3.2.0 → 3.2.1 (Patch, nur Header-Kommentar), `repo-containment.sh` 1.0.0 → 1.1.0 (Minor, Exit-Normalisierung), `repo-containment-impl.sh` 1.2.0 → 1.3.0 (Minor, Detector fail-closed; bei Task 10 ebenfalls 1.3.0) — Stufen nach Hook-Präzedenz (Global Constraints, `CHANGELOG.md` ~:604); kein `VERSION`-Bump; Eintrag unter `## [Unreleased]` → `### Fixed` mit den benannten Verhaltensänderungen (Fenster-Grenze, Klassifikator-/Detector-Fail-closed, Meldung); Consumes Skill `conventions`.
- [ ] Step 1: Ausgangsstände prüfen: `Grep` `^# version:` in den fünf Dateien (Reihenfolge wie im `Files:`-Block) → `2.1.5`, `1.7.0`, `3.2.0`, `1.0.0`, `1.2.0` (verifiziert an `043d29a4`; sonst Stufen anpassen).
- [ ] Step 2: Header bumpen; `CHANGELOG.md` Eintrag (Englisch) unter `### Fixed`: z. B. `- Harden guard hooks: linear is_fork_bomb with body-window block, fail-closed command classifier, fail-closed repo-containment wrapper and write detector, deduplicated protected-branch message (#1033, #943, #944)`.
- [ ] Step 3: Prüfung: `Grep` `^# version:` → neue Werte; `python3 scripts/sync.py --validate` → Exit 0.
- [ ] Step 4: commit `chore: bump hook versions and changelog for guard hardening`

### Task 13: Rebaseline PR 1 auf frischem `main`, Self-Sync (AC-1.21, AC-1.22)
**Agent:** tester · **Issue:** #943, #944, #1033 · **AC:** AC-1.21, AC-1.22
**Depends on:** 12
**Gate:** Branch ist auf aktuellen `origin/main` rebased (durch den `git`-Agenten); **kein Rebaseline** bei Konflikten in `hashes.json`/`_FIXTURE_TREES` (stattdessen Branch neu aufsetzen).
**Files:**
- Modify: `tests/fixtures/ac01-baseline/hashes.json`
- Modify: `tests/test_ac01_render_identity.py`
- Modify: `tests/test_opencode_v2_surface.py`
- Modify: `.agents/hooks/orchestrator-guard.sh`
- Modify: `.agents/hooks/orchestrator-guard-impl.sh`
- Modify: `.agents/hooks/repo-containment.sh`
- Modify: `.agents/hooks/repo-containment-impl.sh`
- Modify: `.meta-config/generated-file-hashes.json` (nur die Einträge der geänderten Hooks/Regeln; enthält `.claude/hooks/*`-Hashes, versioniert)
**Interfaces:** Produces Manifest mit den Änderungen an Hook-Dateien (Claude + Gemini) und gerenderten `branch-guard`-Regeln (Claude/Continue/Copilot) samt abgeleiteten Manifesten/Indizes, Eintrag im Rebaseline-Log (Docstring), nachgezogene Digests in `_FIXTURE_TREES` (:5199) mit Log-Kommentar, versionierte Self-Sync-Kopien in `.agents/hooks/`; Consumes Tasks 5–12. `tests/fixtures/slimming-golden/`, `…/compact-golden/` unverändert.
- [ ] Step 1: Drift beobachten (rot): `python3 -m pytest tests/test_ac01_render_identity.py -q` → Erwartung `1 failed` mit Drift-Liste. **Erwartete Drift (abschließend):** (a) die geänderten Hooks — `Claude/.claude/hooks/{dod-push-check,orchestrator-guard,orchestrator-guard-impl,repo-containment,repo-containment-impl}.sh`, `Gemini/.agents/hooks/{orchestrator-guard,orchestrator-guard-impl,repo-containment,repo-containment-impl}.sh`; (b) die gerenderten `branch-guard`-Regeln — `Claude/.claude/rules/branch-guard.md`, `Continue/.continue/rules/branch-guard.md`, `Copilot/.github/instructions/branch-guard.instructions.md`; (c) die daraus abgeleiteten Manifeste/Indizes **genau dieser Provider** (Claude, Gemini, Continue, Copilot) — `<P>/.meta-config/generated-file-hashes.json`, `<P>/.meta-config/context-hashes.json`, betroffene `.agent-meta-managed`-Indizes (z. B. `Claude/.claude/hooks/.agent-meta-managed`, `Gemini/.agents/hooks/.agent-meta-managed`; Stand `hashes.json` :98/:148/:153 für Claude). **Stop-Kriterium:** jede Zeile außerhalb von (a)–(c) (anderer Provider wie Codex/Opencode/Mammouth/ZCode/KimiCode, nicht verwandte Dateien) ⇒ Rebaseline NICHT schreiben, Ursache klären, berichten.
- [ ] Step 2: Inhaltlich prüfen (Diff-Review, nicht blind): `git diff`-Vergleich je geänderter Datei gegen die Task-Erwartung (Kommentar-/Versions-/Logikzeilen aus Tasks 5–12); Review über den `git`-Agenten bei Guard-Block.
- [ ] Step 3: Rebaseline schreiben: `python tests/test_ac01_render_identity.py --write` → Ausgabe `wrote N hashes to …/hashes.json`. Rebaseline-Log-Eintrag im Docstring von `tests/test_ac01_render_identity.py` (Englisch): `Task 13 (wave 3, PR 1): guard hardening — changed hook files (dod-push-check, orchestrator-guard, orchestrator-guard-impl, repo-containment, repo-containment-impl) and rendered branch-guard rules. AC01_EXCEPTIONS is NOT extended.` Digests in `tests/test_opencode_v2_surface.py::_FIXTURE_TREES` nachziehen: `python3 -m pytest tests/test_opencode_v2_surface.py -k test_ac_t4_fixtures_unchanged -q` meldet je abweichendem Baum `<name>: expected <alt>, got <neu>` (verifiziert, :5221-5240) → `got`-Wert für `ac01-baseline` übernehmen; zusätzlich Log-Kommentar über `_FIXTURE_TREES` (Muster der vorhandenen Einträge, z. B. »Issue #1027 … re-pinned — N hashes …«) ergänzen: `Wave 3 PR 1 (#1033/#943/#944): ac01-baseline re-pinned — <N> hashes (guard hooks, branch-guard rules, derived manifests). Log: tests/test_ac01_render_identity.py.`
- [ ] Step 4: Diff-Nachweis: `git diff tests/fixtures/ac01-baseline/hashes.json` zeigt nur Zeilen der Klassen (a)–(c) aus Step 1; `git status --short tests/fixtures/slimming-golden tests/fixtures/compact-golden` → leere Ausgabe.
- [ ] Step 5: Self-Sync und Drift-Check (AC-1.22): `python3 scripts/sync.py`; danach je geänderter Hook `.agents/hooks/<name>` byte-identisch zum Render der Quelle (mit `{{AGENT_META_PROVIDER}}` → Provider-Name, `scripts/lib/hooks.py:526`); `check_stale_deployed_hooks` (`scripts/lib/consistency/hook_drift.py`) ohne Findings → `python3 scripts/consistency-check.py` (Ausgabe prüfen). Lokale `.claude/hooks/dod-push-check.sh` (Ist 2.1.2, gitignored) wird mit dem Sync auf 2.1.6 gebracht. **Commit-Umfang:** nur die Pfade aus dem `Files:`-Block dieses Tasks committen; jede weitere Sync-Änderung im Arbeitsbaum (`git status --short`, z. B. andere generierte Dateien) prüfen: ohne Bezug zu Tasks 5–12 → per `git checkout -- <pfad>` zurücksetzen und im Task-Ergebnis melden; mit Bezug, aber nicht im `Files:`-Block → nicht committen, Stopp und Rückfrage (Plan ergänzen).
- [ ] Step 6: Test grün: `python3 -m pytest tests/test_ac01_render_identity.py tests/test_opencode_v2_surface.py tests/test_template_slimming_equivalence.py tests/test_compact_matrix.py -q` → alle passed.
- [ ] Step 7: commit `chore: rebaseline AC-01 hashes for hook hardening`

### Task 14: Exit-Gate PR 1 und PR-Beschreibung
**Agent:** tester · **Issue:** #1033, #943, #944 · **AC:** Exit-Kriterien PR 1
**Depends on:** 13
**Files:**
- Create: `.tmp/wave3-pr1-description.md`
**Interfaces:** Produces Exit-Nachweis und PR-Text; Consumes alle PR-1-Tasks. PR/Push durch den `git`-Agenten.
- [ ] Step 1: `python3 scripts/sync.py --validate` → Exit 0 (Exit-Gate).
- [ ] Step 2: `python3 -m pytest tests -q` → ohne `failed`/`error`; Szenarien nur falls Hooks betroffen: `tests/scenarios/run.sh` → alle `PASS`.
- [ ] Step 3: PR-Beschreibung (Entwurf, Titel `fix: harden guard hooks (fork-bomb, classifier, containment)`), Closing-Keywords **je Issue einzeln** (nur die erste Nummer einer Kommaliste schließt automatisch):
  ```
  Fixes duplicated main in the dod-push-check block message, makes is_fork_bomb linear
  with a fail-closed body window, makes the orchestrator-guard classifier and the
  repo-containment wrapper/detector fail closed. Includes tests (red before fix),
  version bumps, one AC-01 rebaseline. Spec: docs/specs/2026-10-29-bugfix-wave-3-spec.md

  Closes #1033
  Refs #943 (item (a)(m) only; remainder tracked in follow-up, D6)
  Refs #944 (SR-B-17 and detector crash only; remainder tracked in follow-up, D6)
  ```
  Variante vor Q1: alle drei als `Refs` (Issues sind geschlossen, Befund A); nach Reopen (Q1) nur `Closes #1033`; #943/#944 bleiben immer `Refs` (Epic-Reste, D6). Messwerte vorher/nachher (AC-1.11) und die Rot-Läufe anhängen. Optional SR-B-19: Zeile ergänzen, falls Task 10 ausgeführt wurde.
- [ ] Step 4: Kein Code-Commit; Hand-off an `git`-Agent für Push/PR.

## PR 2 — `fix/hooks-py-lf-and-tests`

**Branch:** `fix/hooks-py-lf-and-tests` (auf frischem `main` nach Merge von PR 1).
**Entry:** PR 1 gemergt; Branch auf `origin/main` rebased.
**Exit:** (1) `python3 -m pytest tests/test_newline_normalization.py tests/test_dod_push_check_hook.py tests/test_deployed_guard_hooks_identity.py -q` grün; (2) `python3 scripts/sync.py --validate` Exit 0; (3) `python3 -m pytest tests -q` ohne `failed`/`error`; (4) `CHANGELOG.md` mit Modus-Hinweis 0600 (AC-2.2); (5) Mutations-Checks und R2S-3-Laufzeiten im PR dokumentiert (AC-2.8, AC-2.15); (6) **kein Rebaseline geplant** — erzwingt ein Hook-Fix aus der #954-Eskalationsregel (b) eine Hook-Änderung, wird Version-Bump + Rebaseline in PR 2 nach R1 nachgezogen (Abweichung explizit im PR).
**Rollback:** `git revert` des Merge-Commits; Folge: Schreibpfade nutzen wieder `Path.write_text` (CRLF unter Windows), Tests wieder nicht hermetisch; bereits erzeugte 0600-Dateien bleiben bestehen (kein Datenverlust).

### Task 15: #961-Rest — vier Schreibpfade über `write_atomic` (B5)
**Agent:** developer · **Issue:** #961 · **AC:** AC-2.1, AC-2.2 (Test), AC-2.3 · **parallel_group:** g2
**Depends on:** 14
**Files:**
- Modify: `scripts/lib/hooks.py`
- Modify: `scripts/lib/hook_plugins.py`
- Modify: `tests/test_newline_normalization.py`
**Interfaces:** Produces vier Aufrufstellen `write_atomic(path, content)` (statt `write_text`): `create_hook` (`hooks.py:708`), Managed-Index `hooks.py:635`, Release-Gates-Index `hook_plugins.py:160`, Hook-Lib-Index `hook_plugins.py:348`; Consumes `scripts/lib/io.py:write_atomic(path, content, mode="w")` (öffnet mit `newline="\n"`, bereits importiert `hooks.py:9`, `hook_plugins.py:16`; `mkstemp` → Modus 0600, **benannte Verhaltensänderung**, R4). Hook-Deploy (`write_checked`) bleibt unverändert; Geschwister `scripts/lib/skills.py:85` und ~75 weitere `write_text` sind Nicht-Ziel (Folge-Issue, Task 3).
- [ ] Step 1: Symbole prüfen: `Grep` `write_text` in `scripts/lib/hooks.py` und `scripts/lib/hook_plugins.py` → Stellen :635, :708, :160, :348; `Grep` `chmod` in `scripts/lib/hooks.py scripts/lib/hook_plugins.py scripts/lib/io.py` → 0 Treffer (kein Exec-Bit-Pfad).
- [ ] Step 2: Tests schreiben (fail) in `tests/test_newline_normalization.py`. **AC-2.1-Simulation:** `monkeypatch.setattr(pathlib.Path, "write_text", <Wrapper>)`, der vor dem Original-Aufruf `\n` → `\r\n` ersetzt (simuliert die Windows-Textmodus-Übersetzung von `Path.write_text` ohne `newline=`); `write_atomic` (öffnet per `os.fdopen(..., newline="\n")`) ist davon nicht betroffen → Altcode rot, Fix grün. Vorbild für Monkeypatch-Muster: `test_write_atomic_passes_lf_newline_to_text_mode` (:44, `os.fdopen`-Spy) und `test_settings_json_writer_writes_lf_and_skips_second_run` (:211). Tests: `test_create_hook_writes_lf`, `test_hook_managed_index_writes_lf`, `test_hook_plugin_managed_index_writes_lf`, `test_hook_lib_managed_index_writes_lf` (je: Datei enthält kein `\r`), `test_create_hook_runs_via_bash` (Scaffold über registrierte Form `bash <path>` ausführbar, Exit 0 — Ausführung ohne Exec-Bit), `test_hook_managed_indices_idempotent` (AC-2.3: zweiter Sync ohne Quelländerung → byte-identischer Inhalt der drei Indizes).
- [ ] Step 3: `python3 -m pytest tests/test_newline_normalization.py -k "create_hook or managed_index" -x` → Erwartung: `4 failed` (LF-Tests mit `Path.write_text`-Simulation: `assert b"\r" not in …`), Lauf- und Idempotenz-Test grün (Charakterisierung; unter Linux erzeugt `write_text` ohne Simulation LF). Ergebnis je Test festhalten.
- [ ] Step 4: Implementieren: die vier Stellen auf `write_atomic(...)` umstellen; keine neuen Importe nötig.
- [ ] Step 5: `python3 -m pytest tests/test_newline_normalization.py tests/test_hook_lib_sync.py tests/test_hook_drift.py tests/test_hook_metadata.py tests/test_hook_enablement_consistency.py -q` (alle an `043d29a4` vorhanden; `tests/test_hooks.py` existiert nicht) → alle grün.
- [ ] Step 6: commit `fix: write hook scaffold and managed indices with LF via write_atomic`

### Task 16: #951 — hermetische Test-Umgebung für `dod-push-check` (B6)
**Agent:** developer · **Issue:** #951 · **AC:** AC-2.4, AC-2.5, AC-2.6, AC-2.7 · **parallel_group:** g2
**Depends on:** 14
**Files:**
- Modify: `tests/test_dod_push_check_hook.py`
**Interfaces:** Produces `_clean_env(tmp: Path, extra: Optional[dict] = None) -> dict[str, str]` (`from typing import Optional`; kein `dict | None`, Py3.9-CI) (Name/Signatur Plan-Entscheidung, Spec: Name/Signatur im Plan): Reihenfolge (1) `os.environ` ohne `AGENT_META_*`, `GIT_DIR`, `GIT_WORK_TREE`, `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_*`/`GIT_CONFIG_VALUE_*`, `GIT_CONFIG_PARAMETERS`; (2) `GIT_CONFIG_GLOBAL=<tmp>/gitconfig` (bzw. `HOME=<tmp>`), `GIT_CONFIG_NOSYSTEM=1`; (3) Helfer-Defaults (`AGENT_META_TEST_COMMAND=false`, `AGENT_META_TEST_TIMEOUT=5`, wo heute gesetzt); (4) `extra` (Aufrufer-Overrides) zuletzt; alle Run-Helfer (`_run_hook` :42, `_run_hook_failing_tests` :302, `_assert_outcome` :390, Inline-Lauf ~:610, `_run_payload` :832; `_run_hook_with_config` :189 delegiert) nutzen ihn; kein Hook-Code.
- [ ] Step 1: Symbole prüfen: `Grep` `dict\(os.environ` und `def _run_` in der Testdatei; Stellen mit Overrides: `AGENT_META_MAIN_BRANCH=develop` (~:550), `PATH` (~:918).
- [ ] Step 2: Tests schreiben (fail): `test_run_helpers_ignore_caller_agent_meta_env` (AC-2.4: `monkeypatch.setenv` für `AGENT_META_MAIN_BRANCH=foo`, `AGENT_META_TEST_COMMAND=true`, `GIT_DIR=/nonexistent`, `GIT_CONFIG_PARAMETERS="'push.default=matching'"` → alle Helfer liefern dasselbe Verdikt wie ohne diese Variablen; explizite `extra`-Overrides wirken weiter), `test_main_branch_from_project_yaml` (AC-2.5: `GIT_MAIN_BRANCH: develop` → Push nach `develop` geblockt), `test_tag_branch_name_collision_main` (AC-2.6: Tag und Branch `main` → Push auf Branch `main` geblockt), `test_dash_c_other_repo` (AC-2.7: `git -C <anderes Repo> push …` mit Argument ≠ `.` → Branch des Ziel-Repos maßgeblich).
- [ ] Step 3: `python3 -m pytest tests/test_dod_push_check_hook.py -k "ignore_caller or from_project_yaml or tag_branch or dash_c_other" -x` → Erwartung: `test_run_helpers_ignore_caller_agent_meta_env` rot (geerbte Variable ändert das Verdikt, z. B. `AssertionError` auf erwartetes Verdikt); die drei Verhaltenstests sind ggf. bereits grün (reine Testlücken, kein Hook-Bug) — Ergebnis je Test festhalten; ein roter Verhaltenstest ist ein #954-/R1-Fall (Eskalationsregel).
- [ ] Step 4: Implementieren: `_clean_env` einführen, alle Helfer umstellen.
- [ ] Step 5: `python3 -m pytest tests/test_dod_push_check_hook.py -q` → alle grün; Gegenprobe mit gesetzten Caller-Variablen: `AGENT_META_MAIN_BRANCH=foo AGENT_META_TEST_COMMAND=true python3 -m pytest tests/test_dod_push_check_hook.py -q` → identisches Ergebnis.
- [ ] Step 6: commit `fix: isolate dod-push-check tests from caller environment`

### Task 17: #954 — ausgelassene Security-Re-Review-Checks (B7)
**Agent:** tester · **Issue:** #954 · **AC:** AC-2.9, AC-2.10, AC-2.11, AC-2.12, AC-2.13
**Depends on:** 16
**Files:**
- Modify: `tests/test_dod_push_check_hook.py`
- Modify: `hooks/1-generic/dod-push-check.sh` (**bedingt**, nur nach Eskalationsregel (b) — unbeziffert)
**Interfaces:** Produces Tests `test_git_config_env_injection_*` (Prozess-Env `GIT_CONFIG_COUNT`/`KEY_n`/`VALUE_n`, `GIT_CONFIG_PARAMETERS`; `include.path`/`includeIf` in der Repo-Config), `test_git_config_failure_blocks` (PATH-Shim `git`, rc 1 nur für `config --list`, sonst `exec` des echten `git`), `test_for_each_ref_failure_blocks`, `test_python3_shim_garbage_blocks`, `test_push_default_matrix` (parametrisiert über `push.default` ∈ simple/current/upstream/nothing/matching, Repo mit Submodul: geschützter Push geblockt, Feature-Push erlaubt); Consumes Task 16 (`_clean_env`). Keine Duplikate zu `GIT_CONFIG_PARAMETERS=x git push` (~:757) und `GIT_CONFIG_COUNT=1 … git p` (~:799); Abgleich mit vorhandenen #595-Tests für AC-2.12.
- [ ] Step 1: Symbole prüfen: `Grep` `git config --list -z` (:716), `for-each-ref` (:289), `CLASSIFY_BUDGET` (:236) in `hooks/1-generic/dod-push-check.sh`; `Grep` `GIT_CONFIG_PARAMETERS|GIT_CONFIG_COUNT|595` in der Testdatei (Duplikate vermeiden).
- [ ] Step 2: Tests schreiben (Erwartung: fail-closed = Block). Langsam-Test (AC-2.10 `git`-Shim mit `sleep 30` → Block mit `exceeded 20s`, ≥ 20 s) **nicht in CI**: einmalig manuell ausführen, Ergebnis im PR dokumentieren; CI-Abdeckung über vorhandenen `test_r2_3_classifier_over_budget_blocks` (~:910, `timeout`-Stub rc 124).
- [ ] Step 3: `python3 -m pytest tests/test_dod_push_check_hook.py -k "env_injection or config_failure or for_each_ref or python3_shim or push_default" -x` → je Test Ergebnis festhalten (grün/rot). Optionaler Zusatztest (Spec: als R1-Kandidat vermerkt): `read_config_var`-Fehler → `MAIN_BRANCH` fällt auf `main` zurück, ein konfigurierter `develop` wäre ungeschützt.
- [ ] Step 4: **Rot = Befund, nicht stillzulegen.** Eskalation (R1): (a) kein `skip`/`xfail`; (b) Fix im selben PR nur bei Begrenzung auf eine Funktion/einen Zweig von `dod-push-check.sh` und ohne Änderung erlaubter Pushes → Hook-Fix, `# version:` bumpen (2.1.6 → 2.1.7 Patch), **Rebaseline in PR 2** über den bedingten Task 35 nach Regel auf frischem `main` (Abweichung vom »kein Rebaseline« im PR vermerken), Changelog-Hinweis in Task 20; (c) sonst **STOPP**: Befund an den Nutzer, Folge-Issue-Entwurf (Format wie Task 3), PR 2 wird ohne den betroffenen Test nicht gemergt, bis der Nutzer entscheidet.
- [ ] Step 5: Alle neuen Tests grün (oder Stopp nach (c)): `python3 -m pytest tests/test_dod_push_check_hook.py -q`.
- [ ] Step 6: commit `fix: cover skipped dod-push-check security re-review checks`

### Task 18: AC-2.14 — Byte-Identität der versionierten Guard-Kopien
**Agent:** tester · **Issue:** #954 · **AC:** AC-2.14
**Depends on:** 15, 17
**Files:**
- Create: `tests/test_deployed_guard_hooks_identity.py`
**Interfaces:** Produces Test `test_agents_hooks_match_rendered_source` (je `orchestrator-guard.sh`, `orchestrator-guard-impl.sh`, `repo-containment.sh`, `repo-containment-impl.sh`: `.agents/hooks/<name>` byte-identisch zu `hooks/1-generic/<name>` nach Ersetzen von `{{AGENT_META_PROVIDER}}` durch den Provider-Namen — Provider = Eintrag aus `ai-providers` in `.meta-config/project.yaml`, dessen `hooks_dir` in `config/ai-providers.yaml` gleich `.agents/hooks` ist (heute `Gemini`, `config/ai-providers.yaml:157`; im Test aus beiden YAML-Dateien ermittelt, Assertion: genau ein Treffer); Vergleichsbasis Arbeitsbaum des PR-Branches, nicht `origin/main`); `dod-push-check.sh` ausgenommen (nur Claude, `.claude/` gitignored; dort gilt AC-1.22); Consumes `scripts/lib/hooks.py:526` (Render-Regel).
- [ ] Step 1: Vorab: `Grep` `agents/hooks` über `tests/` — existiert bereits ein gleichartiger Test (z. B. Hook-Drift), diese Datei nur ergänzen statt duplizieren; `Glob` `.agents/hooks/*` → vier Dateien.
- [ ] Step 2: Test schreiben; erwartet nach PR 1 grün (Sync lief in Task 13). Rot-Nachweis per Mutation: eine Kopie in `.agents/hooks/` temporär um ein Byte ändern → `1 failed`, danach zurücksetzen (nicht committen).
- [ ] Step 3: `python3 -m pytest tests/test_deployed_guard_hooks_identity.py -q` → `1 passed`.
- [ ] Step 4: commit `fix: assert deployed guard hooks match rendered sources`

### Task 19: Mutations-Checks und R2S-3-Laufzeiten (AC-2.8, AC-2.15)
**Agent:** tester · **Issue:** #951, #954 · **AC:** AC-2.8, AC-2.15
**Depends on:** 15, 16, 17, 18
**Files:**
- Create: `.tmp/wave3-pr2-mutation-report.md`
**Interfaces:** Produces Protokoll für die PR-Beschreibung: (a) AC-2.8: jeder der vier #951-Tests schlägt fehl, wenn seine Logik entfernt wird (Mutation je Test dokumentiert); (b) AC-2.15: 5-Mutations-Check der neuen #954-Tests (je Mutation: Hook-Zeile geändert → Test rot → zurückgesetzt); Laufzeiten der `test_r2_3_*`-Tests unabhängig nachgemessen (best-of-3, Referenz `docs/reviews/2026-10-11-w2-b1-dod-push-check-review-findings.md:130`); Consumes Tasks 15–18.
- [ ] Step 1: Mutationen **nur im Arbeitsbaum, nie committen**; nach jeder Mutation `git diff --stat` leer prüfen (Rücksetzen).
- [ ] Step 2: `python3 -m pytest tests/test_dod_push_check_hook.py -k "r2_3" -q --durations=10` dreimal ausführen; Werte ins Protokoll.
- [ ] Step 3: Kein Commit; Protokoll geht in die PR-Beschreibung.

### Task 20: Changelog PR 2 (Modus 0600) und gegebenenfalls Versionsbump
**Agent:** documenter · **Issue:** #961 · **AC:** AC-2.2
**Depends on:** 19
**Files:**
- Modify: `CHANGELOG.md`
**Interfaces:** Produces `### Fixed`-Eintrag (Englisch) unter `## [Unreleased]`, der ausdrücklich nennt, dass Hook-Scaffold (`--create-hook`) und Managed-Indizes mit 0600 geschrieben werden und LF-Zeilenenden unter Windows garantiert sind; Consumes Task 15; bei Hook-Fix aus Task 17 (b) zusätzlich Hinweis auf den Version-Bump.
- [ ] Step 1: Prüfung vorher: `Read` `CHANGELOG.md` Zeilen 1–10 (Konflikt mit PR-1-Eintrag auflösen, nicht überschreiben).
- [ ] Step 2: Eintrag, z. B. `- Write hook scaffold (--create-hook) and managed hook indices through write_atomic: LF line endings on Windows; files are now created with mode 0600 (#961)`.
- [ ] Step 3: `Grep` `0600` in `CHANGELOG.md` → ≥ 1 Treffer; `python3 scripts/sync.py --validate` → Exit 0.
- [ ] Step 4: commit `chore: add changelog entry for hook write path fix`

### Task 21: Exit-Gate PR 2 und PR-Beschreibung
**Agent:** tester · **Issue:** #961, #951, #954 · **AC:** Exit-Kriterien PR 2
**Depends on:** 20
**Gate:** falls Task 35 (bedingter Rebaseline) ausgeführt wird: erst nach dessen Abschluss starten.
**Files:**
- Create: `.tmp/wave3-pr2-description.md`
**Interfaces:** Produces Exit-Nachweis und PR-Text; Consumes alle PR-2-Tasks.
- [ ] Step 1: `python3 scripts/sync.py --validate` → Exit 0; `python3 -m pytest tests -q` → ohne `failed`/`error`.
- [ ] Step 2: `python3 -m pytest tests/test_ac01_render_identity.py -q` → grün (bestätigt »kein Rebaseline«); rot ⇒ Hook-Fix aus R1 war beteiligt (→ Task 35 ausführen, dann diesen Step wiederholen) oder Annahme falsch (→ Stopp, Ursache klären, berichten); im PR begründen.
- [ ] Step 3: PR-Beschreibung (Entwurf, Titel `fix: LF-safe hook writes and hermetic dod-push-check tests`), einzelne Zeilen:
  ```
  Writes hook scaffold and managed indices via write_atomic (LF, mode 0600),
  makes dod-push-check tests hermetic and adds the skipped security re-review checks.
  Mutation checks and R2S-3 timings attached. Spec: docs/specs/2026-10-29-bugfix-wave-3-spec.md

  Closes #961
  Closes #951
  Closes #954
  ```
  Variante vor Q1 (Issues geschlossen): `Refs #961`, `Refs #951`, `Refs #954`; nach Reopen: `Closes`. #961 wird laut D2 erst nach Fix **und Verifikation** geschlossen (Task 34): falls der Nutzer die Verifikation getrennt wünscht, `Refs #961`.
- [ ] Step 4: Kein Code-Commit; Hand-off an `git`-Agent.

## PR 4 — `fix/admin-ui-network-and-doctor`

**Branch:** `fix/admin-ui-network-and-doctor` (nach Merge von PR 1; parallel zu PR 2 entwickelbar, seriell nach PR 2 gemergt).
**Entry:** PR 1 gemergt; Q5 und Q7 entschieden (vor Implementierung bzw. PR-Beschreibung).
**Exit:** (1) `python3 -m pytest tests/test_admin_server.py tests/test_doctor_runner.py tests/test_doctor_fixtures.py -q` grün; (2) `python3 scripts/sync.py --validate` Exit 0; (3) `python3 -m pytest tests -q` ohne `failed`/`error`; (4) `python3 -m pytest tests/test_ac01_render_identity.py -q` grün (Annahme »rebaseline-frei«, verifiziert: `tests/fixtures/ac01-baseline/hashes.json` enthält keinen `docs/providers`-Pfad, `zcode.md` wird nicht gerendert; bei Rot bedingter Task 36 auf frischem `main`); (5) `CHANGELOG.md`-Eintrag.
**Rollback:** `git revert` des Merge-Commits; Folge: `origin not allowed` im Netzwerkmodus, Doctor-Fehlalarme wiederhergestellt, zcode-Notiz entfällt; kein Datenverlust.

### Task 22: #897 — socket-freier Helfer `_effective_allowed_hosts` (B11)
**Agent:** developer · **Issue:** #897 · **AC:** AC-4.1, AC-4.2, AC-4.3 · **parallel_group:** g3
**Depends on:** 14
**Files:**
- Modify: `scripts/admin-server.py`
- Modify: `tests/test_admin_server.py`
**Interfaces:** Produces `_effective_allowed_hosts(host, cli_hosts, cfg_hosts, resolve) -> tuple[str, ...]` (Name Vorschlag der Spec): bei `host in WILDCARD_HOSTS` werden erkannte Nicht-Loopback-Adressen dedupliziert, reihenfolgestabil angehängt, `OSError` aus `resolve` → nichts angehängt (Hinweis wie bisher); `::`-Bind ergänzt nur IPv4 und der Startup-Hinweis sagt das ausdrücklich und nennt `--allowed-hosts`/`admin-ui.allowed-hosts`; `AdminServer.__init__` (:5653) ruft den Helfer; Consumes `socket.gethostbyname_ex` (:5689, nur IPv4), `WILDCARD_HOSTS` (:201). `check_origin` (:949) unverändert.
- [ ] Step 1: Symbole prüfen: `Grep` `effective_allowed_hosts|gethostbyname_ex|WILDCARD_HOSTS` in `scripts/admin-server.py`.
- [ ] Step 2: Tests schreiben (fail): `TestEffectiveAllowedHosts` (neu): Resolver → `["10.0.0.5"]` bei Wildcard-Bind → `10.0.0.5` in den Hosts und `check_origin(origin="http://10.0.0.5:<port>", …)` wirft nicht (AC-4.1); Resolver wirft `OSError` → Hosts unverändert (AC-4.2); konkreter Bind/Loopback → keine Resolver-Adressen (AC-4.3); `::`-Bind: Hinweistext enthält den IPv4-Zusatz und `--allowed-hosts` (AC-4.3). Mechanik für den Aufruf von `AdminServer.__init__`-Hinweis (Ausgabe) ggf. über Helfer-Rückgabe; Test ohne Socket.
- [ ] Step 3: `python3 -m pytest tests/test_admin_server.py -k "EffectiveAllowedHosts" -x` → Erwartung: Collection/`AttributeError: module has no attribute '_effective_allowed_hosts'` (Admin-Server wird ggf. per `importlib` geladen — Ladeweise der Tests in `tests/test_admin_server.py` prüfen).
- [ ] Step 4: Implementieren: Helfer extrahieren, in `__init__` verwenden, Hinweis um IPv4-Zusatz ergänzen.
- [ ] Step 5: `python3 -m pytest tests/test_admin_server.py -q` → alle grün (`TestCheckOriginBindHost` :2630 unverändert in den Assertions, nur Docstring präzisieren).
- [ ] Step 6: commit `fix: allow detected local addresses on admin wildcard bind`

### Task 23: #897 — Host-Header-Hinweis, Origin-Absicherung, Hilfetext (B11)
**Agent:** developer · **Issue:** #897 · **AC:** AC-4.4, AC-4.5, AC-4.6
**Depends on:** 22
**Gate:** Q5 entschieden (Default: Hilfetext an Code anpassen, »replaces«).
**Files:**
- Modify: `scripts/admin-server.py`
- Modify: `tests/test_admin_server.py`
**Interfaces:** Produces `check_origin`-Meldung `host header not allowed` (:992) mit Hinweis auf `--allowed-hosts` und `admin-ui.allowed-hosts` (Meldungstext erweitert, Logik unverändert; ein Origin wird **nie** aus dem Host-Header abgeleitet); Hilfetext `--allowed-hosts` (:5929) von »Extends (does not replace)« auf »Replaces the default allowlist« (gemäß Q5; Code ersetzt, :5673); Consumes Task 22.
- [ ] Step 1: Tests schreiben (fail): `TestCheckOrigin::test_host_header_rejection_has_hint` (AC-4.4), `TestCheckOrigin::test_origin_never_derived_from_host_header` (AC-4.5: `Host: evil:<port>` + `Origin: http://evil:<port>` → weiterhin abgelehnt), `test_allowed_hosts_help_matches_behavior` (AC-4.6: Hilfetext und Verhalten stimmen überein — Hilfetext enthält `replace`).
- [ ] Step 2: `python3 -m pytest tests/test_admin_server.py -k "host_header_rejection or never_derived or help_matches" -x` → Erwartung: Hinweis-Test und Hilfetext-Test rot (`AssertionError`: `--allowed-hosts` nicht in der Meldung / `Extends` im Hilfetext), Origin-Test grün (Absicherung gegen Regression).
- [ ] Step 3: Implementieren (nur Meldungstext und Hilfetext; `check_origin`-Logik nicht ändern).
- [ ] Step 4: `python3 -m pytest tests/test_admin_server.py -q` → alle grün.
- [ ] Step 5: commit `fix: add allowlist hint to host header rejection and fix help text`

### Task 24: #1034 — Doctor: `.agent-meta-managed*` ausschließen (B12)
**Agent:** developer · **Issue:** #1034 · **AC:** AC-4.7, AC-4.8, AC-4.9 · **parallel_group:** g3
**Depends on:** 14
**Files:**
- Modify: `scripts/lib/doctor_detectors.py`
- Modify: `tests/test_doctor_runner.py`
- Create: `tests/fixtures/doctor/rules-file-wrong-suffix/negative/.github/instructions/.agent-meta-managed`
- Create: `tests/fixtures/doctor/rules-file-wrong-suffix/negative/.github/instructions/.agent-meta-managed-mcp`
- Create: `tests/fixtures/doctor/rules-file-wrong-suffix/negative/.github/instructions/.agent-meta-managed-tools`
**Interfaces:** Produces gemeinsame Prädikatsfunktion (Dateiname beginnt mit `.agent-meta-managed`), angewandt in `_glob_matches` (:240) und `_files_in` (:88); `config/known-issues.yaml` bleibt unverändert (Datenlösung `exclude_glob` verworfen, Spec-Abwägung); explizit per `target.path` adressierte Dateien (`target_files` :101) bleiben unberührt; Consumes `detect_path_exists` (:253).
- [ ] Step 1: Symbole prüfen: `Grep` `def _glob_matches|def _files_in|def target_files|exclude_glob` in `scripts/lib/doctor_detectors.py`; `Grep` `agent-meta-managed` in `config/known-issues.yaml scripts/lib/doctor*.py` → 0 Treffer (kein Detektor wertet Manifeste absichtlich aus).
- [ ] Step 2: Tests schreiben (fail): die drei Manifest-Dateien in `tests/fixtures/doctor/rules-file-wrong-suffix/negative/.github/instructions/` neben der vorhandenen `style.instructions.md` anlegen (Rules-Dir der Fixture; ausgeführt über `tests/test_doctor_fixtures.py::test_ac38_seed_fixture_matches_expected_finding_count`, Negativfall verlangt `findings == []`, verifiziert :245-262; die Fixture-Bäume unter `tests/fixtures/doctor/` sind **nicht** in `_FIXTURE_TREES`); `tests/test_doctor_runner.py::test_files_in_skips_managed_manifests` (AC-4.9 über `instruction-soft-cap-chars`/`_files_in`); Positiv-Fixture (falsches Suffix) meldet weiterhin (AC-4.8; vorhanden: `positive/.github/instructions/style.md`, ID `AC-38-rules-file-wrong-suffix-positive`).
- [ ] Step 3: Selektion vorab prüfen: `python3 -m pytest tests/test_doctor_fixtures.py tests/test_doctor_runner.py --collect-only -q -k "rules-file-wrong-suffix or managed_manifests"` → `3 tests collected` (Parametrisierungs-IDs `AC-38-rules-file-wrong-suffix-positive`/`-negative` mit Bindestrichen — `rules_file_wrong_suffix` würde nichts selektieren — plus `test_files_in_skips_managed_manifests`; an `043d29a4` ohne den neuen Test: `2/164 collected`, verifiziert). Dann `python3 -m pytest tests/test_doctor_fixtures.py tests/test_doctor_runner.py -k "rules-file-wrong-suffix or managed_manifests"` → Erwartung: Negativ-Fixture-Test rot (`rules-file-wrong-suffix` meldet die drei Dateien), `test_files_in_skips_managed_manifests` rot (Dateien enthalten).
- [ ] Step 4: Implementieren (ein Prädikat, in beiden Funktionen genutzt).
- [ ] Step 5: `python3 -m pytest tests/test_doctor_fixtures.py tests/test_doctor_runner.py -q` → alle grün.
- [ ] Step 6: commit `fix: exclude managed manifests from doctor file detectors`

### Task 25: #856 — zcode ZC-1 Entscheidungsnotiz (B13, kein Code-Bug)
**Agent:** documenter · **Issue:** #856 · **AC:** AC-4.11 · **parallel_group:** g3
**Depends on:** 14
**Files:**
- Modify: `docs/providers/zcode.md`
**Interfaces:** Produces Entscheidungsnotiz: ZC-1 bleibt wontfix (documented); agent-meta schreibt nicht nach `~/.zcode/agents`, weil das Repo-Containment verletzt; Verweis, dass ZC-2 mit #807 behoben ist (`config/provider-capabilities.yaml:509`); Consumes D8, bestehenden AGENTS.md-Bootstrap-Abschnitt (`docs/providers/zcode.md:61-86`). Regressionstest: keiner (D8, D4 nicht anwendbar).
- [ ] Step 1: Prüfung: `Read` `docs/providers/zcode.md` Zeilen 52 und 61–86; `Grep` `ZC-2|wontfix` in der Datei → vorab Treffer notieren.
- [ ] Step 2: Notiz ergänzen (Deutsch, interne Doku).
- [ ] Step 3: `Grep` `Repo-Containment` und `#807` in `docs/providers/zcode.md` → je ≥ 1 Treffer; `python3 scripts/sync.py --validate` → Exit 0.
- [ ] Step 4: commit `chore: record zcode ZC-1 wontfix decision`

### Task 26: Changelog PR 4
**Agent:** documenter · **Issue:** #897, #1034, #856 · **AC:** — (conventions)
**Depends on:** 23, 24, 25
**Files:**
- Modify: `CHANGELOG.md`
**Interfaces:** Produces `### Fixed`-Einträge (Englisch): wildcard-bind local addresses allowed, host-header hint, `--allowed-hosts` help text, doctor ignores `.agent-meta-managed*` manifests; `### Changed` (oder Doku-Zeile) für zcode-Notiz; Consumes Tasks 22–25. Kein Version-Bump (kein Agent-Template betroffen) und **kein `VERSION`-Bump** (`VERSION` ändert sich nur in Release-PRs, `git log -- VERSION`; gilt für PR 1–4, Q-P3 geschlossen). Merge-Konflikt mit PR 2 in `CHANGELOG.md` manuell auflösen (Append-Konflikt).
- [ ] Step 1: Eintrag schreiben; `Grep` `#897` in `CHANGELOG.md` → ≥ 1 Treffer.
- [ ] Step 2: `python3 scripts/sync.py --validate` → Exit 0.
- [ ] Step 3: commit `chore: add changelog entries for admin-ui and doctor fixes`

### Task 27: Exit-Gate PR 4, #4.10-Verifikation, PR-Beschreibung
**Agent:** tester · **Issue:** #897, #1034, #856 · **AC:** AC-4.10, Exit-Kriterien PR 4
**Depends on:** 26
**Gate:** falls Task 36 (bedingter Rebaseline) ausgeführt wird: erst nach dessen Abschluss starten.
**Files:**
- Create: `.tmp/wave3-pr4-description.md`
**Interfaces:** Produces Exit-Nachweis und PR-Text; Consumes alle PR-4-Tasks.
- [ ] Step 1: AC-4.10 (im Vorlauf **nicht** ausgeführt): echter Copilot-Sync in Wegwerfverzeichnis `.tmp/wave3-copilot/` (Config mit Provider Copilot), dann `python3 scripts/sync.py --doctor` → 0 Treffer für `.github/instructions/.agent-meta-managed`, `-mcp`, `-tools`. Exakten `--config`-Aufruf aus `tests/scenarios/` oder `docs/guides/` ableiten (nicht verifiziert); Ergebnis protokollieren.
- [ ] Step 2: `python3 scripts/sync.py --validate` → Exit 0; `python3 -m pytest tests -q` → ohne `failed`/`error`; `python3 -m pytest tests/test_ac01_render_identity.py -q` → grün.
- [ ] Step 3: PR-Beschreibung (Entwurf, Titel `fix: admin-ui wildcard bind hosts and doctor manifest false positives`), einzelne Zeilen:
  ```
  Adds detected local addresses to the admin allowlist on wildcard bind, improves the
  host-header rejection hint, fixes the --allowed-hosts help text, excludes
  .agent-meta-managed* manifests from doctor detectors and documents the zcode ZC-1
  decision. Spec: docs/specs/2026-10-29-bugfix-wave-3-spec.md

  Closes #897
  Closes #1034
  Refs #856
  ```
  #897: `Closes` nach Fix (Q4, offenes Issue). #1034: geschlossen (Befund A) → `Refs #1034` bis Q1; nach Reopen `Closes #1034`. #856: bewusst `Refs`; Schließen als Plan-Task 34 (Q7), nicht per PR.
- [ ] Step 4: Kein Code-Commit; Hand-off an `git`-Agent.

## PR 3 — `fix/config-contracts-placeholders`

**Branch:** `fix/config-contracts-placeholders` (auf frischem `main` **nach Merge von PR 1, 2, 4**).
**Entry:** PR 1, 2, 4 gemergt; Q2 entschieden (D5 formal aufheben, Default ja); Branch auf aktuellen `origin/main` rebased.
**Exit:** (1) `python3 scripts/consistency-check.py` → 0 `handoff.output-not-consumed`, keine neuen `handoff.*`-Findings; (2) `python3 -m pytest tests/test_consistency_checks.py tests/test_config_variable_fallbacks.py tests/test_build_variables_decomposition.py tests/test_template_integrity_checks.py tests/test_template_slimming_equivalence.py tests/test_build_variables_platform_cascade.py -q` grün; (3) `python3 scripts/sync.py --validate` Exit 0; (4) `python3 -m pytest tests -q` ohne `failed`/`error`; (5) genau ein Rebaseline für alle 9 Provider (AC-3.13); (6) `CHANGELOG.md`, Agent-Version `_reference-agent.md` auf `2.0.0` gebumpt; (7) Szenario `87-project-description-seed` in `tests/scenarios/registry.md` + `tests/scenarios/configs/87-project-description-seed.project.yaml`, Lauf `tests/scenarios/run.sh` → alle Szenarien `PASS`.
**Rollback:** `git revert` des Merge-Commits (inkl. `hashes.json`, `_FIXTURE_TREES`, ggf. `slimming-golden/orchestrator.md`); danach `python3 scripts/sync.py`. Folge: 8 Handoff-Warnungen und literale Platzhalter-Leaks kehren zurück; Release-Gate wieder rot.

### Task 28: #1031 — acht unkonsumierte Output-Contracts (B8)
**Agent:** developer · **Issue:** #1031 · **AC:** AC-3.1, AC-3.2, AC-3.3 (Prüfung)
**Depends on:** 21, 27
**Files:**
- Modify: `config/role-defaults.yaml`
- Modify: `tests/test_consistency_checks.py`
**Interfaces:** Produces `handoff.input_contracts` der Default-Konsumenten (erste Rolle in `target_roles`): `rag-engineer` ← `memory-architecture-v1`; `agent-meta-manager` ← `context-budget-report-v1`; `prompt-engineer` ← `redteam-findings-v1`; `sre-engineer` ← `chaos-experiment-v1`; `product-manager` ← `ux-research-findings-v1` (Handoff-Block ohne `input_contracts` vorhanden → Liste anlegen); `ai-governance-engineer` ← `privacy-assessment-v1`; `devops-engineer` ← `secret-inventory-v1` **und** `build-determinism-v1` (**neuer** Handoff-Block nur mit `input_contracts`, Präzedenz `validator` `config/role-defaults.yaml:403-408`; `handoff_contracts.py` wertet `output_contract` nur aus, wenn vorhanden); Consumes `scripts/lib/consistency/handoff_contracts.py` (Schritt 2b). Hinweis: Key heißt `target_roles`; `privacy-compliance-officer` zielt auf `app-lifecycle-governor` (Issue schreibt `lifecycle-governor`, existiert nicht) — Konsument laut Spec-Tabelle ist `ai-governance-engineer` (erste Rolle in `target_roles`; Zielreihenfolge vor Edit per `Grep` bestätigen).
- [ ] Step 1: Ist-Zustand rot belegen: `python3 scripts/consistency-check.py` → 8 × `handoff.output-not-consumed` (Ausgabe festhalten); `Grep` `target_roles` und `output_contract` in `config/role-defaults.yaml` für die 8 Produzenten, `Grep` `^  devops-engineer:` (Handoff-Struktur) und `handoff:` bei den Konsumenten.
- [ ] Step 2: Test schreiben (fail): `tests/test_consistency_checks.py::test_role_defaults_no_unconsumed_output_contracts` (prüft das **echte** `config/role-defaults.yaml`; `handoff.output-not-consumed`-Findings == 0 und jeder der 8 Contracts steht in den `input_contracts` genau des Default-Konsumenten, AC-3.2).
- [ ] Step 3: `python3 -m pytest tests/test_consistency_checks.py::test_role_defaults_no_unconsumed_output_contracts -x` → Erwartung: `1 failed` (8 Findings bzw. Contract nicht in `input_contracts`).
- [ ] Step 4: Daten ändern (YAML-Struktur der vorhandenen Blöcke übernehmen).
- [ ] Step 5: `python3 -m pytest tests/test_consistency_checks.py -q` → grün; `python3 scripts/consistency-check.py` → 0 `handoff.output-not-consumed`, keine neuen `handoff.*`.
- [ ] Step 6: Render-Auswirkung (AC-3.3, **unverifiziert**): `delegation_table.py` filtert `input_contracts` nach aktiven Produzenten → `python3 -m pytest tests/test_template_slimming_equivalence.py tests/test_compact_matrix.py -q`; falls `tests/fixtures/slimming-golden/orchestrator.md` abweicht, Änderung im Rebaseline (Task 31) mit Begründung festhalten; kein Hermes-Golden für das echte Repo (Tests nutzen synthetische Fixture).
- [ ] Step 7: commit `fix: wire eight output contracts to default consumer roles`

### Task 29: #983 — `TECH_STACK`/`AGENT_RULES`/`EXTERNAL_DOCS_LANGUAGE` (B9)
**Agent:** developer · **Issue:** #983 · **AC:** AC-3.4, AC-3.5, AC-3.6, AC-3.7
**Depends on:** 28
**Files:**
- Modify: `scripts/lib/config.py`
- Modify: `scripts/lib/consistency/placeholders.py`
- Modify: `agents/1-generic/_reference-agent.md`
- Modify: `tests/test_config_variable_fallbacks.py`
- Modify: `tests/test_template_integrity_checks.py`
**Interfaces:** Produces `"TECH_STACK": ""` in `_VARIABLE_FALLBACKS` (config.py:197) und Eintrag in `_BUILTIN_VARS` (placeholders.py:12, verlangt von :309-318); `_reference-agent.md`: `EXTERNAL_DOCS_LANGUAGE` → `DOCS_LANGUAGE`, `AGENT_RULES` aus der Liste entfernt (Default; Alternative Escape-Syntax: **unverifiziert**) mit Agent-Version-Bump **Major** `1.2.0` → `2.0.0` (Skill `conventions`, Hard Invariant 2: »renamed variable« = Major); `_UNKNOWN_TEMPLATE_RATCHET = frozenset()` (:277-279) mit angepasstem Kommentar; Consumes `agents/2-platform/sharkord-release.md:142` (deploybar).
- [ ] Step 1: Symbole/Ist prüfen: `Grep` `TECH_STACK|AGENT_RULES|EXTERNAL_DOCS_LANGUAGE` in `agents/ scripts/lib/`; `Grep` `_UNKNOWN_TEMPLATE_RATCHET` in `scripts/lib/consistency/placeholders.py`; `Grep` `_reference-agent` in `tests/test_template_slimming_equivalence.py` (`_PARSE_INPUT_MIGRATED` :327-329 — muss grün bleiben); bestehende Assertion `not _ph._is_family("TECH_STACK")` (~:126 in `tests/test_template_integrity_checks.py`) prüfen.
- [ ] Step 2: Tests schreiben (fail): `tests/test_config_variable_fallbacks.py::test_tech_stack_falls_back_to_empty` (ohne Konfig `build_variables(...)["TECH_STACK"] == ""`), `tests/test_template_integrity_checks.py::test_unknown_template_ratchet_is_empty` (`_UNKNOWN_TEMPLATE_RATCHET == frozenset()`); Render-Test AC-3.5 (Projekt mit Rolle `sharkord-release` ohne `TECH_STACK` → kein `{{TECH_STACK}}` im Output; mit gesetzter Variable deren Wert) im selben Modul wie vorhandene Render-Tests (`Glob` `tests/test_*sharkord*` prüfen).
- [ ] Step 3: `python3 -m pytest tests/test_config_variable_fallbacks.py tests/test_template_integrity_checks.py -k "tech_stack or ratchet_is_empty" -x` → Erwartung: `KeyError: 'TECH_STACK'` bzw. `assert frozenset({...}) == frozenset()` → `2–3 failed`.
- [ ] Step 4: Implementieren (config.py, placeholders.py, `_reference-agent.md` inkl. Frontmatter-Version-Bump `version: "1.2.0"` → `"2.0.0"`: umbenannte Variable `EXTERNAL_DOCS_LANGUAGE` → `DOCS_LANGUAGE` und entfernte `AGENT_RULES` = Major laut `conventions` Hard Invariant 2; `Grep` `^version:` vorher → `"1.2.0"`).
- [ ] Step 5: `python3 -m pytest tests/test_config_variable_fallbacks.py tests/test_template_integrity_checks.py tests/test_template_slimming_equivalence.py -q` → grün; `python3 scripts/consistency-check.py` → `placeholders.builder-known-set` ohne Findings für die drei Namen (AC-3.7).
- [ ] Step 6: commit `fix: add TECH_STACK fallback and empty the placeholder ratchet`

### Task 30: #1037 — `project.description` und ableitbare Variablen (B10)
**Agent:** senior-developer · **Issue:** #1037 · **AC:** AC-3.8, AC-3.9, AC-3.10, AC-3.12 (AC-3.11 in Task 33)
**Depends on:** 29
**Files:**
- Modify: `scripts/lib/config.py`
- Modify: `scripts/lib/setup.py`
- Modify: `config/project-config.schema.json`
- Modify: `tests/test_build_variables_decomposition.py`
- Modify: `tests/test_config_variable_fallbacks.py`
- Modify: `tests/scenarios/registry.md`
- Create: `tests/scenarios/configs/87-project-description-seed.project.yaml`
- Create: `tests/scenarios/asserts/87-project-description-seed.sh`
**Interfaces:** Produces `variables.setdefault("PROJECT_DESCRIPTION", project.get("description", ""))` in `_build_core_variables` (:1315, Projekt-Felder :1346-1349) **vor** der `PROJECT_GOAL`-Ableitung (:1467-1469; explizite `variables:` gewinnen); `properties.project` im Schema um `description` (string); Leer-Fallbacks `TEST_COMMANDS`, `TEST_COMMAND`, `BUILD_COMMAND`, `BUILD_COMMANDS`, `PLATFORM`, `RUNTIME`, `KEY_PATTERNS`, `ENTRY_POINT_PATTERN`, `DEV_STACK_RELOAD` in `_VARIABLE_FALLBACKS` (D7: `PLATFORM`/`RUNTIME` leer, kein Fehler) und Registrierung in `_BUILTIN_VARS`, soweit nicht vorhanden; **eine** Konstante für `"Popoboxxo/agent-meta"` (`AGENT_META_REPO`-Fallback + `setup.py` :276/:314). Konstanten-Ort ist Plan-Entscheidung: Default `scripts/lib/config.py` neben `_VARIABLE_FALLBACKS`, Voraussetzung Import-Richtung `setup.py → config.py` ohne Zyklus (Step 1 per `Grep` prüfen; bei Zyklus Stopp und Rückfrage). Nebenwirkung: `PROJECT_CONTEXT` fällt auf `PROJECT_DESCRIPTION` zurück (:1479-1480) → Render-Änderung im Rebaseline (Task 31). Standalone-Rendering (`scripts/lib/standalone.py:_standalone_variables` :261) unberührt; URL-Literale in `standalone.py`, `hermes_export.py`, `admin-server.py` sind Nicht-Ziel. Das `_SET`-Muster (config.py:1403-1412, #425) ist hier verworfen.
- [ ] Step 1: Symbole prüfen: `Grep` `Popoboxxo/agent-meta` über `scripts/` (erwartet: `setup.py` :276, :314 plus URL-Formen), `Grep` `^from|^import` in `scripts/lib/setup.py` (Import-Richtung), `Grep` `_VARIABLE_FALLBACKS|_BUILTIN_VARS` in `scripts/lib/`.
- [ ] Step 2: Tests schreiben (fail): `tests/test_build_variables_decomposition.py::test_project_description_seeds_variable` (AC-3.8: `PROJECT_DESCRIPTION == PROJECT_GOAL == PROJECT_CONTEXT == "X"`), `::test_explicit_project_description_variable_wins`, `tests/test_config_variable_fallbacks.py::test_derivable_variables_fall_back_empty` (AC-3.10: neun Variablen `""`, kein Fehler), `::test_agent_meta_repo_default` (`== "Popoboxxo/agent-meta"`); Schema-Test AC-3.9 (Validierung einer Config mit `project.description` besteht; vorhandenes Schema-Testmodul per `Glob` `tests/test_*schema*` suchen); `grep`-basierter AC-3.12-Test (genau eine Fundstelle des Literals `"Popoboxxo/agent-meta"` in `scripts/`, URL-Formen ausgenommen).
- [ ] Step 3: `python3 -m pytest tests/test_build_variables_decomposition.py tests/test_config_variable_fallbacks.py -k "description or derivable or agent_meta_repo" -x` → Erwartung: `4 failed` (`KeyError`/`assert '' == 'X'`), Schema-Test rot (`Additional properties are not allowed ('description' was unexpected)`).
- [ ] Step 4: Implementieren: Seed, Schema, Fallbacks, Konstante; `tests/test_build_variables_platform_cascade.py` darf nicht kippen (leere Fallbacks sind dort unschädlich).
- [ ] Step 5: `python3 -m pytest tests/test_build_variables_decomposition.py tests/test_config_variable_fallbacks.py tests/test_build_variables_platform_cascade.py tests/test_template_integrity_checks.py -q` → grün; `python3 scripts/consistency-check.py` → keine `placeholders.*`-Findings.
- [ ] Step 5a: Szenario für die neue `project.yaml`-Option `project.description` (Skill `conventions`: »New feature or new `project.yaml` option → scenario«): nächste freie ID vorher per `Glob` `tests/scenarios/configs/*.project.yaml` bestätigen (Stand `043d29a4`: höchste ID 86 → `87`). `tests/scenarios/configs/87-project-description-seed.project.yaml` (Provider Claude, `project: {name, prefix, description: "Seeded description"}`, **ohne** `variables.PROJECT_DESCRIPTION`); ausführbares `tests/scenarios/asserts/87-project-description-seed.sh` (Vorbild vorhandene `asserts/*.sh`: kein literales `{{PROJECT_DESCRIPTION}}` im Sync-Output, `Seeded description` erscheint im generierten Output); Zeile im Katalog von `tests/scenarios/registry.md` (Tabelle »## Katalog«, Spalten ID/Provider/Orchestrator-Mode/Feature: ID `87-project-description-seed`, Claude, strict (default), Feature »`project.description` seeds `PROJECT_DESCRIPTION`/`PROJECT_GOAL`/`PROJECT_CONTEXT` (#1037)«). Lauf: `tests/scenarios/run.sh 87` → `PASS` (vor dem Fix in Step 4: `FAIL`).
- [ ] Step 6: commit `fix: seed PROJECT_DESCRIPTION and add empty variable fallbacks`

### Task 31: Rebaseline PR 3 auf frischem `main` (alle 9 Provider, AC-3.13)
**Agent:** tester · **Issue:** #1031, #983, #1037 · **AC:** AC-3.13, AC-3.3
**Depends on:** 30
**Gate:** Branch ist auf aktuellen `origin/main` rebased; keine Konfliktauflösung in `hashes.json`/`_FIXTURE_TREES`.
**Files:**
- Modify: `tests/fixtures/ac01-baseline/hashes.json`
- Modify: `tests/test_ac01_render_identity.py`
- Modify: `tests/test_opencode_v2_surface.py`
- Modify: `tests/fixtures/slimming-golden/orchestrator.md` (**bedingt**, nur wenn Task 28 Step 6 eine Abweichung zeigt)
**Interfaces:** Produces genau ein Rebaseline für alle 9 Provider mit Begründung im Docstring-Log (u. a. `PROJECT_CONTEXT`-Seed aus `project.description`, Handoff-Verdrahtung im Orchestrator, `TECH_STACK`-Fallback); Digests in `_FIXTURE_TREES` nachgezogen; Consumes Tasks 28–30.
- [ ] Step 1: Drift beobachten: `python3 -m pytest tests/test_ac01_render_identity.py -q` → Erwartung `1 failed` mit Drift-Liste. **Erwartete Drift (abschließend):** (a) Render-Ausgaben, die aus Tasks 28–30 erklärbar sind (`PROJECT_CONTEXT`/`PROJECT_DESCRIPTION`-Seed, leere Fallbacks, `TECH_STACK`, Delegationstabelle im Orchestrator) — alle 9 Provider möglich; (b) die davon abgeleiteten `<P>/.meta-config/generated-file-hashes.json`, `<P>/.meta-config/context-hashes.json` und Managed-Indizes genau der Provider aus (a).
- [ ] Step 2: Diff-Review gegen (a)/(b) aus Step 1; Ergebnis protokollieren. **Stop-Kriterium:** jede Zeile außerhalb von (a)/(b) (z. B. Hook-Dateien, `branch-guard`-Regeln, nicht erklärbare Pfade) ⇒ Rebaseline NICHT schreiben, Ursache klären, berichten.
- [ ] Step 3: `python tests/test_ac01_render_identity.py --write` → `wrote N hashes …`; Rebaseline-Log-Eintrag im Docstring (Englisch): `Task 31 (wave 3, PR 3): config contracts and placeholders — description seeds PROJECT_DESCRIPTION/PROJECT_CONTEXT, empty fallbacks for derivable variables, TECH_STACK fallback, handoff input_contracts. AC01_EXCEPTIONS is NOT extended.`; Digests in `tests/test_opencode_v2_surface.py::_FIXTURE_TREES` nachziehen (Mechanik wie Task 13 Step 3: `got`-Digest aus `test_ac_t4_fixtures_unchanged`, ggf. auch für `slimming-golden`; Log-Kommentar über `_FIXTURE_TREES`).
- [ ] Step 4: `python3 -m pytest tests/test_ac01_render_identity.py tests/test_opencode_v2_surface.py tests/test_template_slimming_equivalence.py tests/test_compact_matrix.py -q` → alle passed.
- [ ] Step 5: commit `chore: rebaseline AC-01 hashes for config contracts and placeholders`

### Task 32: Changelog PR 3
**Agent:** documenter · **Issue:** #1031, #983, #1037 · **AC:** — (conventions)
**Depends on:** 30
**Files:**
- Modify: `CHANGELOG.md`
**Interfaces:** Produces `### Fixed`-Einträge (Englisch): eight output contracts consumed, placeholder ratchet emptied, `TECH_STACK` fallback, `project.description` seeds `PROJECT_DESCRIPTION`/`PROJECT_GOAL`/`PROJECT_CONTEXT`, empty fallbacks for nine derivable variables, `project.description` in the schema; Hinweis auf Render-Änderung (`PROJECT_CONTEXT`); Consumes Tasks 28–30.
- [ ] Step 1: Eintrag schreiben; `Grep` `#1037` in `CHANGELOG.md` → ≥ 1 Treffer.
- [ ] Step 2: `python3 scripts/sync.py --validate` → Exit 0.
- [ ] Step 3: commit `chore: add changelog entries for config contracts and placeholders`

### Task 33: Exit-Gate PR 3, 9-Provider-Verifikation, PR-Beschreibung
**Agent:** tester · **Issue:** #1031, #983, #1037 · **AC:** AC-3.11, AC-3.1, Exit-Kriterien PR 3
**Depends on:** 31, 32
**Files:**
- Create: `.tmp/wave3-pr3-description.md`
**Interfaces:** Produces Exit-Nachweis und PR-Text; Consumes alle PR-3-Tasks.
- [ ] Step 1: AC-3.11 (im Vorlauf **nicht** ausgeführt): 9-Provider-Sync mit `project: {name, description}` in einem Wegwerfprojekt unter `.tmp/wave3-nine-providers/` (Provider-Liste aus `config/ai-providers.yaml`; exakter Aufruf nach Vorbild `tests/test_ac01_render_identity.py::_make_project`, nicht verifiziert) → kein `active-set.unresolved-placeholder` für die in #1037 genannten Tokens; `python3 scripts/sync.py --doctor` ohne `unresolved-placeholder-in-output` dafür (`{{PIPELINE_DETAIL_BLOCKS}}` ausgenommen). Ergebnis protokollieren.
- [ ] Step 2: `python3 scripts/consistency-check.py` → 0 `handoff.output-not-consumed`; `python3 scripts/sync.py --validate` → Exit 0; `python3 -m pytest tests -q` → ohne `failed`/`error`; `tests/scenarios/run.sh` → alle Szenarien `PASS` (inkl. `87-project-description-seed`, Exit (7)).
- [ ] Step 3: PR-Beschreibung (Entwurf, Titel `fix: consume output contracts and fill placeholder fallbacks`), einzelne Zeilen:
  ```
  Wires the eight unconsumed output contracts, empties the placeholder ratchet,
  adds TECH_STACK and empty fallbacks for derivable variables and seeds
  PROJECT_DESCRIPTION from project.description. One AC-01 rebaseline (all 9 providers).
  Spec: docs/specs/2026-10-29-bugfix-wave-3-spec.md

  Closes #1031
  Closes #983
  Closes #1037
  ```
  Variante vor Q1 (Issues geschlossen, Befund A): `Refs #1031`, `Refs #983`, `Refs #1037`; nach Reopen: `Closes`.
- [ ] Step 4: Kein Code-Commit; Hand-off an `git`-Agent.

## PR 0b — Post-Merge-Housekeeping (nur nach ausdrücklicher Freigabe des Nutzers)

### Task 34: #961, #971, #856 nach Fix/Verifikation schließen (Entwürfe, nicht ausführen)
**Agent:** documenter · **Issue:** #961, #971, #856 · **AC:** — (D2, D8, Q7)
**Depends on:** 21, 27
**Gate:** nur nach ausdrücklicher Freigabe und nach Merge der jeweiligen PRs (#961: PR 2; #856: PR 4). #971: **Fix-/Verifikationskriterium im Spec/Brief nicht definiert** → offene Frage Q-P1; ohne Antwort bleibt #971 offen.
**Files:**
- Modify: `docs/plans/2026-10-29-bugfix-wave-3-plan.md`
**Interfaces:** Produces `gh`-Befehle (Text) und englische Begründungskommentare; Consumes Merge-Status und Verifikation.
- [ ] Step 1: Verifikation lesend (nach Merge von PR 2): `python3 -m pytest tests/test_newline_normalization.py -q` grün und Nachweis, dass `Grep` `write_text` an den vier Stellen (`hooks.py`, `hook_plugins.py`) 0 Treffer ergibt.
- [ ] Step 2: Befehle (Entwürfe):
  ```
  /home/hermes/.local/bin/gh issue close 961 --reason completed --comment "Verified on main after the merge of PR #<number>: hook scaffold (--create-hook) and the three managed hook indices are written via write_atomic with LF newlines (tests in tests/test_newline_normalization.py). Remaining write_text calls without newline= are tracked separately."
  /home/hermes/.local/bin/gh issue close 856 --reason "not planned" --comment "ZC-1 (workspace agent auto-load) stays wontfix (documented): agent-meta does not write to ~/.zcode/agents because that would violate repo containment; the AGENTS.md bootstrap is documented in docs/providers/zcode.md. ZC-2 (commands capability under-claim) was fixed in #807 (config/provider-capabilities.yaml)."
  ```
  #961 war laut Befund A bereits geschlossen: bei Q1 »Reopen« schließt `Closes #961` in der PR-Beschreibung (Task 21) das Issue automatisch und der erste Befehl entfällt. #856: Schließen des gesamten Issues gemäß Q7 (Default ja).
- [ ] Step 3: #971 (»no dangling lazy pointers; every active rule reachable via a channel«, Bug, offen): Verifikationskriterium vom Nutzer klären (Q-P1); Kommentarentwurf erst danach. Kein Befehl vorbereitet.
- [ ] Step 4: Kein Code-Commit.

## Bedingte Rebaseline-Tasks (PR 2 / PR 4)

> Laufen nur, wenn ihr Gate greift; sonst erhalten alle Checkboxen den Vermerk `entfällt (<Grund>)`. Regeln wie Task 13 (frischer `main`, keine Konfliktauflösung in `hashes.json`/`_FIXTURE_TREES`, `AC01_EXCEPTIONS` nicht erweitern, höchstens ein Rebaseline pro PR).

### Task 35: Bedingter Rebaseline PR 2 nach #954-Hook-Fix (R1 (b))
**Agent:** tester · **Issue:** #954 · **AC:** — (Spec #954 »Rebaseline«, R1 (b); PR-2-Exit (6))
**Depends on:** 17, 20
**Gate:** nur wenn Task 17 Step 4 (b) einen Fix in `hooks/1-generic/dod-push-check.sh` (inkl. `# version:` 2.1.6 → 2.1.7) committet hat; Branch durch den `git`-Agenten auf aktuellen `origin/main` rebased. Kein Hook-Fix → `entfällt (kein Hook-Fix in PR 2)`.
**Files:**
- Modify: `tests/fixtures/ac01-baseline/hashes.json`
- Modify: `tests/test_ac01_render_identity.py`
- Modify: `tests/test_opencode_v2_surface.py`
- Modify: `.meta-config/generated-file-hashes.json` (nur Eintrag `.claude/hooks/dod-push-check.sh`)
**Interfaces:** Produces ein Rebaseline für den `dod-push-check`-Fix mit Log-Eintrag und `_FIXTURE_TREES`-Digest; Consumes Task 17 (b), Task 20.
- [ ] Step 1: Drift beobachten: `python3 -m pytest tests/test_ac01_render_identity.py -q` → `1 failed`. **Erwartete Drift (abschließend):** `Claude/.claude/hooks/dod-push-check.sh` und die davon abgeleiteten Claude-Manifeste/Indizes (`Claude/.meta-config/generated-file-hashes.json`, `Claude/.meta-config/context-hashes.json`, `Claude/.claude/hooks/.agent-meta-managed`). `dod-push-check.sh` wird nur für Claude verteilt (kein `Gemini/.agents/hooks/dod-push-check.sh` in `hashes.json`, verifiziert). **Stop-Kriterium:** jede andere Zeile ⇒ nicht schreiben, Ursache klären, berichten.
- [ ] Step 2: `python tests/test_ac01_render_identity.py --write` → `wrote N hashes …`; Rebaseline-Log im Docstring (Englisch): `Task 35 (wave 3, PR 2): dod-push-check fix from the #954 escalation rule (b). AC01_EXCEPTIONS is NOT extended.`; `_FIXTURE_TREES`: `got`-Digest aus `python3 -m pytest tests/test_opencode_v2_surface.py -k test_ac_t4_fixtures_unchanged -q` übernehmen, Log-Kommentar über `_FIXTURE_TREES` ergänzen.
- [ ] Step 3: `python3 scripts/sync.py`; Commit-Umfang wie Task 13 Step 5 (nur `Files:`-Pfade; übrige Sync-Diffs prüfen, ohne Bezug zurücksetzen und melden, mit Bezug Stopp).
- [ ] Step 4: `python3 -m pytest tests/test_ac01_render_identity.py tests/test_opencode_v2_surface.py tests/test_dod_push_check_hook.py -q` → alle passed.
- [ ] Step 5: commit `chore: rebaseline AC-01 hashes for dod-push-check fix`

### Task 36: Bedingter Rebaseline PR 4 (Annahme »rebaseline-frei« widerlegt)
**Agent:** tester · **Issue:** #897, #1034, #856 · **AC:** — (PR-4-Exit (4))
**Depends on:** 26
**Gate:** nur wenn Step 1 rot ist; Branch durch den `git`-Agenten auf aktuellen `origin/main` rebased. Grün → `entfällt (AC-01 grün)`.
**Files:**
- Modify: `tests/fixtures/ac01-baseline/hashes.json`
- Modify: `tests/test_ac01_render_identity.py`
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces ein Rebaseline für PR 4 mit Log-Eintrag und `_FIXTURE_TREES`-Digest; Consumes Tasks 22–26.
- [ ] Step 1: `python3 -m pytest tests/test_ac01_render_identity.py -q` → grün ⇒ Task entfällt. Rot ⇒ Drift-Liste. **Erwartete Drift (abschließend):** nur Render-Ausgaben, die aus den `Files:`-Pfaden der Tasks 22–26 erklärbar sind (Erwartung eigentlich **keine** Drift — verifiziert: `tests/fixtures/ac01-baseline/hashes.json` enthält keinen `docs/providers`-Pfad, `zcode.md` wird nicht gerendert, `admin-server.py`/`doctor_detectors.py` erzeugen keinen Sync-Output), plus die davon abgeleiteten `<P>/.meta-config/generated-file-hashes.json`, `<P>/.meta-config/context-hashes.json` und Managed-Indizes genau dieser Provider. **Stop-Kriterium:** Hook-Dateien, Agent-Renders oder Provider ohne Bezug zu PR 4 ⇒ nicht schreiben, Ursache klären, berichten.
- [ ] Step 2: Diff-Review gegen die Ursachen aus Step 1; `python tests/test_ac01_render_identity.py --write`; Rebaseline-Log (Englisch): `Task 36 (wave 3, PR 4): <cause>. AC01_EXCEPTIONS is NOT extended.`; `_FIXTURE_TREES` wie Task 35 Step 2.
- [ ] Step 3: `python3 -m pytest tests/test_ac01_render_identity.py tests/test_opencode_v2_surface.py -q` → alle passed.
- [ ] Step 4: commit `chore: rebaseline AC-01 hashes for admin-ui and doctor fixes`

## Anhang — Traceability AC → Task → Test

| AC | Task | Test / Nachweis |
|---|---|---|
| AC-1.1 – AC-1.4 | 5 | `tests/test_dod_push_check_hook.py::test_block_message_*` (4 Tests) |
| AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | 6 | `tests/test_orchestrator_guard_hook.py::test_fork_bomb_linear_on_long_identifier`, `::test_fork_bomb_linear_on_repeated_headers`, `::test_fork_bomb_body_window_exhausted_blocks`, `::test_fork_bomb_long_name_detected`, `::test_fork_bomb_end_to_end_long_input_fast` |
| AC-1.10 | 6 (Block-Meldung), 11 (Doku) | `tests/test_orchestrator_guard_hook.py::test_fork_bomb_window_block_message_names_limit`; `Grep` `1024`/`classifier` in beiden Guard-Headern und `rules/1-generic/branch-guard.md`; `--validate` |
| AC-1.11 | 4 (vorher), 6 (nachher) | Messprotokoll `.tmp/wave3-pr1-timing-before.md`, PR-Text |
| AC-1.12, AC-1.13 | 7 | `tests/test_orchestrator_guard_hook.py::test_classifier_crash_fails_closed`, `::test_classifier_garbage_output_fails_closed` |
| AC-1.14, AC-1.15 | 8 | `tests/test_repo_containment_hook.py::test_wrapper_fails_closed_on_impl_crash` (+ Durchreich-Fälle) |
| AC-1.16, AC-1.17 | 9 | `tests/test_repo_containment_hook.py::test_bash_detector_crash_fails_closed`, `::test_bash_detector_no_targets_allows` |
| AC-1.18, AC-1.19 | 10 (OPTIONAL) | `tests/test_repo_containment_hook.py::test_bundled_inplace_flags_detected`, `::test_non_inplace_flags_not_flagged`, `::test_cp_target_dir_detected` |
| AC-1.20 | 12 | `Grep` `^# version:`, `CHANGELOG.md`-Eintrag |
| AC-1.21 | 13 | `tests/test_ac01_render_identity.py`, `tests/test_opencode_v2_surface.py` (erwartete Drift inkl. abgeleiteter Manifeste/Indizes, Task 13 Step 1) |
| AC-1.22 | 13 | `python3 scripts/sync.py` + `check_stale_deployed_hooks` (`scripts/consistency-check.py`) |
| AC-2.1, AC-2.3 | 15 | `tests/test_newline_normalization.py::test_create_hook_writes_lf`, `::test_hook_managed_index_writes_lf`, `::test_hook_plugin_managed_index_writes_lf`, `::test_hook_lib_managed_index_writes_lf`, `::test_hook_managed_indices_idempotent` |
| AC-2.2 | 15 (Test), 20 (Changelog) | `tests/test_newline_normalization.py::test_create_hook_runs_via_bash`, `Grep` `0600` in `CHANGELOG.md` |
| AC-2.4, AC-2.5, AC-2.6, AC-2.7 | 16 | `tests/test_dod_push_check_hook.py::test_run_helpers_ignore_caller_agent_meta_env`, `::test_main_branch_from_project_yaml`, `::test_tag_branch_name_collision_main`, `::test_dash_c_other_repo` |
| AC-2.8 | 19 | Mutations-Protokoll `.tmp/wave3-pr2-mutation-report.md` |
| AC-2.9, AC-2.10, AC-2.11, AC-2.12, AC-2.13 | 17 | `tests/test_dod_push_check_hook.py::test_git_config_env_injection_*`, `::test_git_config_failure_blocks`, `::test_for_each_ref_failure_blocks`, `::test_python3_shim_garbage_blocks`, `::test_push_default_matrix` (+ einmaliger manueller Langsam-Test) |
| AC-2.14 | 18 | `tests/test_deployed_guard_hooks_identity.py::test_agents_hooks_match_rendered_source` |
| AC-2.15 | 19 | 5-Mutations-Check + `--durations` der `test_r2_3_*`-Tests im Protokoll |
| AC-3.1, AC-3.2 | 28 | `tests/test_consistency_checks.py::test_role_defaults_no_unconsumed_output_contracts`, `python3 scripts/consistency-check.py` |
| AC-3.3 | 28 (Prüfung), 31 (Rebaseline) | `tests/test_template_slimming_equivalence.py`, `tests/test_compact_matrix.py` |
| AC-3.4, AC-3.5, AC-3.6, AC-3.7 | 29 | `tests/test_template_integrity_checks.py::test_unknown_template_ratchet_is_empty`, `tests/test_config_variable_fallbacks.py::test_tech_stack_falls_back_to_empty`, Render-Test `sharkord-release`, `tests/test_template_slimming_equivalence.py`, `placeholders.builder-known-set` |
| AC-3.8, AC-3.9, AC-3.10, AC-3.12 | 30 | `tests/test_build_variables_decomposition.py::test_project_description_seeds_variable`, `::test_explicit_project_description_variable_wins`, `tests/test_config_variable_fallbacks.py::test_derivable_variables_fall_back_empty`, `::test_agent_meta_repo_default`, Schema-Test, Grep-Test, Szenario `87-project-description-seed` (`tests/scenarios/run.sh`) |
| AC-3.11 | 33 | 9-Provider-Sync + `sync.py --doctor` (manuell protokolliert) |
| AC-3.13 | 31 | `tests/test_ac01_render_identity.py`, `tests/test_opencode_v2_surface.py` |
| AC-4.1, AC-4.2, AC-4.3 | 22 | `tests/test_admin_server.py::TestEffectiveAllowedHosts` |
| AC-4.4, AC-4.5, AC-4.6 | 23 | `tests/test_admin_server.py::TestCheckOrigin::test_host_header_rejection_has_hint`, `::TestCheckOrigin::test_origin_never_derived_from_host_header`, `::test_allowed_hosts_help_matches_behavior` |
| AC-4.7, AC-4.8, AC-4.9 | 24 | `tests/test_doctor_fixtures.py::test_ac38_seed_fixture_matches_expected_finding_count[AC-38-rules-file-wrong-suffix-negative]` / `[…-positive]`, `tests/test_doctor_runner.py::test_files_in_skips_managed_manifests` |
| AC-4.10 | 27 | Copilot-Sync + `sync.py --doctor` (manuell protokolliert) |
| AC-4.11 | 25 | `Grep` `Repo-Containment`/`#807` in `docs/providers/zcode.md` |

## Offene Fragen (aus der Spec übernommen, Entscheidungszeitpunkt)

| ID | Frage | Default | Entscheidung bis |
|---|---|---|---|
| Q1 | Geschlossene, aber im Code nicht behobene Issues (#1033, #943, #944, #961, #951, #954, #1031, #983, #1037, #1034): Reopen oder neue Issues? | Reopen-Kommentar-Entwurf je Issue (Task 1); bis dahin »Refs« in PRs | vor PR-1-Start, durch Nutzer |
| Q2 | D5 formal aufheben? | Ja; nur die Rebaseline-Regel bleibt | vor PR-3-Start, durch Nutzer |
| Q3 | Fix-Vertrag #943: (a) Lookbehind + Body-Fenster 1024, Fenster ohne `}` → Block; (b) Fenster ohne `}` als Body prüfen (fail-open bei Self-Pipe); (c) `{0,63}` + Eingabekappung? | (a) — fail-closed, Fehlalarm-Grenze R3 | vor PR-1-Implementierung (Task 6), durch Nutzer |
| Q4 | #897: »Closes« oder »Refs«? | »Closes #897« nach Fix | vor PR-4-Beschreibung (Task 27), durch Nutzer |
| Q5 | `--allowed-hosts`: Hilfetext an Code anpassen (»replaces«) oder Code an Hilfetext (»extends«)? | Hilfetext anpassen (keine Verhaltensänderung) | vor PR-4-Implementierung (Task 23), durch Nutzer |
| Q6 | #945 (Guard-Test-Isolation, CI-Timeouts) vor PR 1 vorziehen? | Nein — Timing-AC sind als Skalierungs-AC robust (AC-1.5/AC-1.6/AC-1.11), Spec R6 | vor PR-1-Start, durch Nutzer |
| Q7 | #856 nach PR 4 vollständig schließen (ZC-1 wontfix documented, ZC-2 fixed in #807)? | Ja, ein Schließkommentar mit beiden Verweisen (Task 34) | vor PR-4-Beschreibung (Task 27), durch Nutzer |
| Q-P1 | (Plan) Was gilt als »Fix/Verifikation« für das Schließen von #971 (D2)? In Spec/Brief nicht definiert. | #971 bleibt offen, bis der Nutzer ein Kriterium nennt | vor Task 34, durch Nutzer |
| Q-P2 | (Plan) Test-Mechanik für die in die `.sh` eingebettete Python-Funktion `is_fork_bomb` (Spec: unverifiziert): Extraktion + `exec` (Default) oder nur e2e-Messung (Alternative)? | Extraktion; bei Nicht-Robustheit Alternative und Meldung an den Nutzer | Task 4 Step 2, durch senior-developer, Meldung an Nutzer |
| Q-P3 | (Plan) Stufen der Hook-Versions-Bumps und `VERSION`-Bump für PR 1–4 | **geschlossen (2026-10-29):** Stufen nach Hook-Präzedenz (Task 12, `CHANGELOG.md` ~:604); kein `VERSION`-Bump in PR 1–4 (`VERSION` nur in Release-PRs, `git log -- VERSION`) | — |
| Q-P4 | (Plan) `pipeline_stages: implement: 5` — Stage-zu-Task-Zuordnung | **geschlossen (2026-10-29):** Frontmatter am Dateianfang + »Step-Agent-Map« (Step = Task-Nummer, Vorbild `docs/plans/2026-09-19-dynamic-routing-template-slimming-plan.md:1-4, :88-101`), geprüft mit `scripts/lib/pipelines.py:parse_plan_ref` → `stages={'implement': 5}`, Step 5 → `developer` | — |

## Self-Review

- Jeder Task mappt auf genau eine Rolle (`developer`, `senior-developer`, `tester`, `documenter`); jedes Akzeptanzkriterium ist über Testkommando, `Grep` oder Messprotokoll messbar; AC-3.11, AC-4.10 und der Langsam-Test AC-2.10 sind als manuelle Läufe ausgewiesen.
- `Files:`/`Interfaces:` vollständig; Parallelgruppen: `g1` = {Task 5, 6, 8} (PR 1; Dateien `dod-push-check.sh`+`test_dod_push_check_hook.py` / `orchestrator-guard-impl.sh`+`test_orchestrator_guard_hook.py` / `repo-containment.sh`+`test_repo_containment_hook.py` disjunkt), `g2` = {Task 15, 16} (PR 2; `hooks.py`/`hook_plugins.py`/`test_newline_normalization.py` vs. `test_dod_push_check_hook.py`), `g3` = {Task 22, 24, 25} (PR 4; `admin-server.py`+`test_admin_server.py` / `doctor_detectors.py`+Fixtures+`test_doctor_runner.py` / `zcode.md`). PR 2 (Tasks 15–21) und PR 4 (22–27) sind dateidisjunkt bis auf `CHANGELOG.md` (Task 20 / 26, sequenziell gemergt). Nachweis vor Ausführung per `scripts/lib/orchestration.py::check_plan_file_overlap` und `scripts/lib/consistency/spec_plan.py::_parse_plan_tasks`.
- `pipeline_stages` deckt die einzige `plan-driven`-Stage `implement` ab (YAML-Frontmatter am Dateianfang, »Step-Agent-Map« nur mit `allowed_agents`; `parse_plan_ref` liefert `stages={'implement': 5}` und 13 Steps, verifiziert).
- Kein Task führt `git`, `gh`-Schreibaufrufe oder Issue-Änderungen aus; alle `gh`-Befehle stehen als Entwurf in PR 0/0b.
- Traceability: jede AC-ID der Spec (AC-1.1–1.22, AC-2.1–2.15, AC-3.1–3.13, AC-4.1–4.11) steht im Anhang; AC-1.18/1.19 nur bei Ausführung des OPTIONALEN Tasks 10. Bedingte Tasks 35/36 tragen keine eigene AC (Rebaseline-Folge von R1 (b) bzw. PR-4-Exit (4)).

**Annahmen / Unsicherheiten**
1. Die Fixes aus dem Issue-Zustand (Befund A) fehlen im Code von `origin/main` (Stichprobe der Spec); wäre das falsch, entfallen die zugehörigen Tasks. Vor Task 5 gilt: `Grep`-Stichprobe wiederholen.
2. Zeilennummern driften; jeder Task verifiziert Symbole zuerst.
3. Test-Mechaniken: Q-P2 (Extraktion von `is_fork_bomb`) und die Admin-Server-Ladeweise im Test sind nicht verifiziert und stehen als Step-1/2-Prüfungen in den Tasks. Verifiziert (2026-10-29): `tests/test_doctor_fixtures.py`-Ablauf (parametrisiert, Negativfall `findings == []`) und `_FIXTURE_TREES` (`test_ac_t4_fixtures_unchanged` meldet `expected`/`got`).
4. Annahme »PR 4 rebaseline-frei« (verifiziert: `tests/fixtures/ac01-baseline/hashes.json` enthält keinen `docs/providers`-Pfad, `zcode.md` wird nicht gerendert) wird in Task 27 Step 2 bestätigt; bei Rot Task 36.
5. Einzelne `gh`-Optionswerte (`--reason`, `--duplicate-of`) der installierten Version sind unverifiziert (Task 2 Step 1).
6. **Re-Planning:** nach jedem PR-Merge Annahmen prüfen (Zeilennummern, Rebaseline-Umfang, offene Fragen) und den Plan aktualisieren, nicht einfrieren; besonders nach Task 6 (Messwerte AC-1.11), nach Task 17 (R1-Befunde) und vor PR 3 (frischer `main`).
7. Hinweis zum Validator: `scripts/lib/consistency/spec_plan.py` klassifiziert nur `*-design.md` als Spec (`_DESIGN_RE`), die Spec `…-spec.md` wird als Plan geprüft (Spec R7, nicht behoben) — mögliche Warnungen zu Plan-Pflichtsektionen bei der Spec sind erwartet und kein Fehler dieses Plans.
