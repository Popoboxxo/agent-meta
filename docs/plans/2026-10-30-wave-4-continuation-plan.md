---
type: tracking-plan
status: Entwurf
date: 2026-10-30
base-commit: ec359896
trace:
  - SPEC-test-hygiene-945
  - issue-945
  - issue-1050
  - issue-1051
  - issue-971
  - issue-192
  - pr-1047
  - pr-1048
  - pr-1049
  - pr-1067
---

# Welle 4 — Fortsetzungsplan (Tracking)

> **Status: Entwurf (Fortsetzungsplan).**
>
> Dieses Dokument ist ein **Tracking-/Fortsetzungsplan**, **kein** Implementation-Plan.
> Es beschreibt je offenem Punkt den Ist-Stand, die exakt nächste Aktion und das Gate,
> an dem die Arbeit stoppt. Es enthält **bewusst kein** `pipeline_stages`-Frontmatter:
> ein Tracking-Plan treibt keine `plan-driven`-Stage — jede Stage wird erst durch den
> noch zu erstellenden, freigegebenen Item-Plan (I1) bzw. Item-Spec (I3/I4) bedient.
>
> **Kein Punkt ist freigegeben.** Kein Approval-Marker wurde gesetzt, keiner wird von
> diesem Dokument gesetzt. Jeder Punkt startet frühestens an seinem eigenen Gate
> (Spec-Approval durch den User / User-Entscheid / eigener Plan). Ausführung ohne
> freigegebene Spec verstößt gegen `spec-plan-workflow` (Spec/Plan-Gate).

**Goal:** Alle in dieser Session offen gebliebenen Punkte (Welle 4 / #945 plus drei
Folge-Issues) in einem nachvollziehbaren Fortsetzungs-Strang festhalten — je Punkt
State, Gate, Größe, Rolle und nächste konkrete Aktion.
**Architecture:** Kein Code in diesem Dokument. Reine Steuerungsebene über
`docs/specs/`, `docs/reviews/`, `docs/plans/`, GitHub-Issues.
**Tech Stack:** Markdown, pytest, GitHub Actions (YAML), Bash-Hooks.
**Spec:** `docs/specs/2026-10-30-test-hygiene-945-design.md` — Rev. 3, 1192 Zeilen,
`Status: Entwurf` (nur für I1; I3/I4/I5 haben noch **keine** Spec).
**Spec-ID:** `SPEC-test-hygiene-945` (Trace-Anker; Rev. 3 Review-Verdict APPROVED,
Spec-Status weiterhin **Entwurf**).
**Tracking:** Refs #945, #1050, #1051, #971, #192.

## Bekannter Repo-Stand (verifiziert 2026-10-30)

| Fakt | Wert |
|---|---|
| `main` | `ec359896` == `origin/main` |
| Session-Kette | `3e340690` → `a0070f78` → `3294c7e5` → `3c440c33` → `ad9bb37e` → `ec359896` |
| Branch `docs/wave4-945-spec` | Tip `9ff2b359`, **4 ahead / 13 behind** `main`, 2 Dateien / 1313 Insertions, **nicht gepusht** |
| Inhalt des Branches | Spec (`docs/specs/2026-10-30-test-hygiene-945-design.md`) + Review-Record (`docs/reviews/2026-10-30-test-hygiene-945-rev3-narrow-review.md`) — beide nur auf dem Branch, nicht auf `main` |

## Item-Übersicht

| ID | Quelle | State | Größe | Gate | Ownende Rolle | Nächste konkrete Aktion |
|---|---|---|---|---|---|---|
| **I1** | Issue #945 (`tests,ci`, OPEN) + `SPEC-test-hygiene-945` | **BLOCKED-BY-APPROVAL** | XL (P1 L 14 · P2a XL 32 · P2b XL 31 · P3 M 5 · P4 M 3 · P5 S 2 · P6 M 3 Dateien) | User setzt `Status: APPROVED` in der Spec | `planner` (Item-Plan), danach `developer`/`senior-developer`/`devops-engineer`/`tester` | User-Approval einholen; danach Item-Plan aus Rev. 3 ableiten |
| **I2** | Housekeeping zu I1 (kein Issue) | **READY** | S | keine (Doku-only), aber PR-Review | `concept-specifier` (Rev. 3.1), `git` (Rebase/Push/PR) | Rev. 3.1 schreiben, Branch auf `main` rebasen, PR aufmachen |
| **I3** | Issue #1050 (`bug,hooks`, OPEN) | **READY** | M | Spec → Approval → Plan | `concept-specifier` | Spec für #1050 schreiben (Fix-Sketch steht im Issue) |
| **I4** | Issue #1051 (`enhancement,hooks`, OPEN) | **READY** | L | Spec → Approval → Plan | `concept-specifier` | Spec für #1051 schreiben (größte Verhaltensänderung der drei) |
| **I5** | Issue #971 (`bug`, OPEN) | **BLOCKED-BY-DECISION** | unbekannt | User liefert Akzeptanzkriterium | — | User fragen: welches Kriterium definiert „kein dangling lazy pointer“? |
| **I6** | Issue #192 (`enhancement,deferred`, OPEN) | **NO ACTION** | — | — | — | Nichts. Offen lassen, nicht planen. |
| **I7** | AC2-Residual aus I1 (kein Issue) — `timeout-minutes` für `.github/workflows/scorecard.yml:jobs.analysis` | **READY** | S (1 Datei, 2 Zeilen) | keins über PR-Review hinaus | `junior-developer` (Change), `git` (PR) | `timeout-minutes: 10` in `scorecard.yml:jobs.analysis` ergänzen (Wert in einem Satz begründen) — empfohlen: in Welle-4-Phase **P5** falten |

---

## I1 — Welle 4 / Issue #945 (Test-Hygiene)

**Trace:** `SPEC-test-hygiene-945`, #945 · **State: BLOCKED-BY-APPROVAL** · Größe XL.

### Erledigt

- Spec existiert auf Branch `docs/wave4-945-spec`: `docs/specs/2026-10-30-test-hygiene-945-design.md`,
  **Rev. 3, 1192 Zeilen, `Status: Entwurf`** (Approval-Marker absichtlich nicht gesetzt).
- Drei Review-Iterationen; Rev. 3 Verdikt **APPROVED** (0 critical / 0 major,
  2 minor + 1 info). Verifikations-Review: `docs/reviews/2026-10-30-test-hygiene-945-rev3-narrow-review.md`.
- Phasen/Schnitte mit F7-Größen stehen: P1 → P2a → P2b → P3 → P4 → P5 → P6.
- Reihenfolge festgelegt: **P1 → P2a → P2b → P3 strikt**; P4 nach P1; P5/P6 unabhängig.
  Rollback-Reihenfolge bei Revert-Kaskade: **P3 → P2b → P2a → P1**.

### AC-Stand (6 ACs aus dem Issue)

| AC | Inhalt | Stand | Beleg |
|---|---|---|---|
| AC1 | Hook-Tests gegen `tmp_path`-Projekt, `.claude/hooks/.guard-audit.log` unverändert | **teilweise** | orchestrator-guard isoliert, inkl. Proof-Test (Session-Stand) |
| AC2 | `timeout-minutes` an jedem CI-Job | **nicht erfüllt — 8 von 9 Jobs** | heute verifiziert gegen `main` @ `ec359896`: 8 von 9 CI-Jobs tragen `timeout-minutes` (`orchestration-test.yml`: `changes` 5, `test` 30, `subprocess-shard` 30, `compat-311` 30, `orchestration-gate` 5; `validate.yml`: `scenarios` 30, `validate` 10, `validate-gate` 5). Die Ausnahme ist `.github/workflows/scorecard.yml:jobs.analysis` → Residual als **I7** erfasst |
| AC3 | `timeout=` an **jedem** `subprocess.run` in Tests | **offen** | Session-Messung: 203 Call-Sites / 73 Testdateien, nur wenige begrenzt (nicht heute nachgezählt) |
| AC4 | Artefakt-Tests laufen in CI, mit `sync.py` vor pytest | **unverifiziert** | heute verifiziert nur: `tests/test_artifact_contracts.py` und `tests/test_artifact_freshness_hook.py` existieren und stehen in **keiner** der sechs expliziten CI-Listen (`SUBPROCESS_SHARD_*`, `HEAVY_FIXTURE_SHARD_*`; `tests/test_provider_reactivation_artifacts.py` ist ein anderer Test). Ob ein vorheriger `sync.py`-Lauf nötig ist: **unverifiziert** |
| AC5 | Dokumentierte Entscheidung zur Multi-Python-Szenario-Suite | **unverifiziert (Doku fehlt)** | heute verifiziert: `.github/workflows/orchestration-test.yml:jobs.compat-311` ist ein gezielter 9-Datei-Job; `.github/workflows/validate.yml:jobs.scenarios` fährt die Shell-Szenarien auf 3.11, 4 Shards |
| AC6 | Playwright-CI-Pfad **oder** dokumentierte Ablehnung | **nicht erfüllt** | heute verifiziert: kein `playwright`/`browser`-Token in `.github/workflows/*` |

> **Abweichung notieren (kein AC-Blocker für die Phasen, aber AC2 bleibt offen):** Die
> Session-Notiz zu AC2 nennt „30/30/30/30/10“; die Dateien zeigen `orchestration-test.yml`
> 5/30/30/30/5 und `validate.yml` 30/10/5. **AC2 ist nicht erfüllt:** 8 von 9 CI-Jobs tragen
> `timeout-minutes`, die Ausnahme ist `.github/workflows/scorecard.yml:jobs.analysis`. Das
> Residual ist als **I7** erfasst. Zahlen gehören in Rev. 3.1 korrigiert — ebenso wie dort die
> (falsche) Aussage, AC2 sei bereits erfüllt.
>
> **Layout-Hinweis:** PR #1054 hat die Workflows nach dem Schreiben der Welle-4-Spec umgebaut
> — die Jobs `changes`, `orchestration-gate` und `validate-gate` sind neu. Job-Zahlen und
> Zeilenpositionen in Plan und Spec können den Stand **vor** #1054 widerspiegeln; maßgeblich
> ist die Job-Menge der drei Workflow-Dateien (heute: 5 + 3 + 1 = 9).

### Offen (Phasen-Inhalt, je mit F7-Größe)

- **P1 — Timeout-Vertrag + Hook-Isolation** (14 Dateien, L): `SLOW_TIMEOUT` in den
  vorhandenen `tests/timeouts.py` (dort heute nur `SYNC_TIMEOUT`,
  `SYNC_VALIDATE_TIMEOUT`, `SCRIPT_TIMEOUT`), Fixture `hook_project_root`,
  Decoy-tmp-Isolation für `test_repo_containment_hook.py` (ADR-3), Isolation-Guard-Test;
  `tests/test_orchestrator_guard_hook.py:STRICT_CASES`-Proof-Test **unangetastet**.
- **P2a — 32 Dateien, XL** und **P2b — 31 Dateien, XL**: repo-weite Timeout-Adoption;
  P2b dedupliziert sechs `RUN_TIMEOUT = 900` zu `SLOW_TIMEOUT`.
- **P3 — 5 Dateien, M**: AST-Vollständigkeits-Check `test.subprocess-timeout-missing`
  (Severity ERROR) in `sync.py --validate`, zwei enumerierte `Popen`-Allowlist-Einträge.
- **P4 — 3 Dateien, M**: CI-Digest-Step je Shard + neuer `artifacts`-Job mit
  `ARTIFACT_TESTS`-Env-Liste, `-rs`, 0-Skip-Assertion.
- **P5 — 2 Dateien, S**: AC5-Ablehnung dokumentieren.
- **P6 — 3 Dateien, M**: `browser-test.yml`, `tests/requirements-browser.txt`, `-n 0 -rs`.

### Exakt nächste Aktion

1. User setzt in `docs/specs/2026-10-30-test-hygiene-945-design.md` den Marker
   `Status: APPROVED (<Datum>)` — **nur der User**, nicht der Planner.
2. Danach leitet der `planner` den Item-Plan (Tasks/`Files:`/`Interfaces:`/`pipeline_stages`)
   aus Rev. 3 ab; P1 startet erst nach freigegebenem Plan.

### Akzeptanz-Evidenz, die zu produzieren ist

- Pro Phase: grüne, eng gefasste Testläufe (`python3 -m pytest <Slice>`) + `python3 scripts/sync.py --validate`.
- AC3: Zählbeleg „0 unbeschränkte `subprocess.run` in `tests/`“ aus dem neuen AST-Check.
- AC4: CI-Log des neuen `artifacts`-Jobs mit 0 Skips (`-rs`).
- AC6: entweder grüner `browser-test.yml`-Lauf oder der dokumentierte Ablehnungs-Eintrag.
- Vor Push: `scripts/ci-local.sh` (siehe Known Constraints), nicht die 3,4-h-Volllast.

### Betroffene Dateien/Bereiche

`tests/timeouts.py`, `tests/conftest.py`, `tests/test_repo_containment_hook.py`,
`tests/test_orchestrator_guard_hook.py`, ~70 `tests/test_*.py`,
`scripts/sync.py` + `scripts/lib/*` (neuer Check), `.github/workflows/orchestration-test.yml`,
neu `.github/workflows/browser-test.yml`, neu `tests/requirements-browser.txt`,
`tests/README.md`, `CHANGELOG.md`.

### Offene Frage im Item

- **OQ-4:** `continue-on-error: true` für den ersten `browser-test.yml`-Lauf?
  Default laut Spec: **ja, genau eine Runde, im selben PR wieder entfernt.**

---

## I2 — Pre-Approval-Housekeeping für I1 (zuerst erledigen)

**State: READY** · Größe S · Gate: keins (Doku-only), nur PR-Review. Rolle:
`concept-specifier` (Text), `git` (Rebase/Push/PR).

### Erledigt

Nichts — dieser Punkt ist vollständig offen.

### Offen

1. **Rev. 3.1** der Spec:
   - (a) `tests/README.md`-Verweise von Zeilennummern (`:104-105`) auf `file:symbol`
     umstellen. Die Datei wurde nach dem Spec-Schreiben durch PR #1054 geändert
     (Timeout-Tabelle liegt heute bei ca. Zeile 95–105, Einträge u. a. `SCRIPT_TIMEOUT`) —
     Zeilennummern sind **drift-anfällig und heute nicht neu abgeglichen**.
   - (b) drei offene Minor-Findings: die §AC3-Klammer, die nicht aufgeht; „67“ → **„66 neue
     `timeout=`-Keywords“** (eines ist bereits `timeout=timeout` über `_scan`); die siebte
     900er-Zeile (`tests/active_set_render.py`) in die Tabelle der vorbestehenden Werte.
   - (c) aus I1: **AC2-Aussage der Spec korrigieren.** Rev. 3 behauptet, AC2 sei bereits
     erfüllt — das ist falsch: 8 von 9 CI-Jobs tragen `timeout-minutes`, die Ausnahme ist
     `.github/workflows/scorecard.yml:jobs.analysis`. Rev. 3.1 muss diese Aussage ersetzen
     (Verweis auf das Residual **I7**) und die Zahlen richtigstellen (5/30/30/30/5 +
     30/10/5 statt „30/30/30/30/10“). Job-Mengen/Zeilenpositionen stammen ggf. aus dem
     Stand vor PR #1054.
2. Branch `docs/wave4-945-spec` auf `main` (`ec359896`) rebasen/mergen — er ist 13 Commits hinter.
3. Push + PR (docs-only), nach grüner CI mergen.

### Exakt nächste Aktion

`concept-specifier` schreibt Rev. 3.1 (Doku-only, kein Code), dann `git`-Rolle:
Rebase auf `ec359896` → Push → PR → Merge nach CI.

### Akzeptanz-Evidenz

- Rev. 3.1 im Spec-Changelog sichtbar; keine Zeilennummern-Referenz auf `tests/README.md` mehr.
- PR zeigt „nur Doku“-Diff; CI grün; Merge ohne `--admin`.

### Betroffene Dateien

`docs/specs/2026-10-30-test-hygiene-945-design.md` (+ ggf.
`docs/reviews/2026-10-30-test-hygiene-945-rev3-narrow-review.md` als Verweisziel).

---

## I3 — Issue #1050 (`}`-Lücke im Fork-Bomb-Scan)

**State: READY** (keine offene Entscheidung) · Größe M · Gate: Spec → Approval → Plan.
Trace: #1050 (Reihenfolge-Anker: nach `SPEC-test-hygiene-945` unabhängig).

### Erledigt

- Issue existiert (aus dem Welle-3-Entscheid Q10); Symptom dokumentiert:
  `is_fork_bomb` (`hooks/1-generic/lib/hook_common.sh:is_fork_bomb`, emittiert von
  `hook_shell_scan_py`) beendet den Funktionskörper am ersten ungequoteten `}` ohne
  Brace-Nesting → `f(){ : ${x}; f|f& };f` und `f(){ { :; }; f|f& };f` bleiben unerkannt.
- Die Lücke ist als **Punkt 5** in `rules/1-generic/branch-guard.md` (»Bekannte Grenzen«,
  heute verifiziert vorhanden) dokumentiert.

### Offen

- Spec (nicht vorhanden), Approval, Plan, Implementierung.
- Skizze im Issue: depth-matching `}` innerhalb des bestehenden 512-Zeichen-Fensters,
  fail-closed bei erschöpftem Fenster. Prototyp-Messung: 119 ms / 113 ms, linear.

### Exakt nächste Aktion

`concept-specifier` schreibt `docs/specs/<datum>-1050-fork-bomb-brace-design.md` aus dem
Issue-Sketch; danach Approval durch den User.

### Akzeptanz-Evidenz

- Beide Beispielbefehle → `True` (Block), bestehende Fork-Bomb-Tests
  (`tests/test_hook_common_lib.py`, `tests/test_orchestrator_guard_hook.py`) bleiben grün.
- Linearitätstests bleiben < 1 s.
- Der Lücken-Eintrag (Punkt 5) ist aus `rules/1-generic/branch-guard.md` entfernt.
- Genau **ein** AC-01-Rebaseline (Hook + Rule-Renders).

### Betroffene Dateien

`hooks/1-generic/lib/hook_common.sh`, `hooks/1-generic/orchestrator-guard-impl.sh` (Meldungstext),
`rules/1-generic/branch-guard.md`, Hook-Tests, `CHANGELOG.md`, AC-01-Render-Fixtures.

---

## I4 — Issue #1051 (Submodule-Push-Ziele statt Pauschalblock)

**State: READY** · Größe **L** (größte Verhaltensänderung der drei Issues) · Gate: Spec →
Approval → Plan. Trace: #1051 (Residuum von #953).

### Erledigt

- Issue existiert: der geschlossene #953-Stand liefert nur die fail-closed-Hälfte. Jedes Repo
  mit Top-Level-`.gitmodules` wird für `--recurse-submodules=on-demand|only` geblockt —
  ohne Zielprüfung, ohne Ausweg-Meldung, ohne Doku-Eintrag.
- Die vier betroffenen Tests sind heute verifiziert vorhanden:
  `tests/test_dod_push_check_hook.py::test_953_recurse_submodules_*` (4 Tests).

### Offen

- Spec, Approval, Plan, Implementierung. Vorschlag im Issue: effektives Push-Ziel jedes
  Submoduls auflösen, vorhandenen Protected-Branch-Test darauf anwenden, nur bei
  geschütztem oder unbestimmbarem Ziel blocken; fail-closed bei unlesbarer Config;
  die vier `test_953_*`-Tests aktualisieren; Rule dokumentieren; im 20-Sekunden-Budget
  des Klassifizierers bleiben.

### Exakt nächste Aktion

`concept-specifier` schreibt die Spec für #1051 — **nach** #1050 (gleiche Hook-Familie,
kleinerer Change zuerst), damit die Spec nicht gegen einen bewegten Classifier geschrieben wird.

### Akzeptanz-Evidenz

- Matrix-Beleg: Submodul mit geschütztem Ziel → Block; mit ungeschütztem Ziel → Allow;
  unlesbare Config → Block (fail-closed); Repo ohne Submodule → unverändert.
- Alle vier `test_953_*`-Tests angepasst und grün.
- Klassifizierer-Laufzeit innerhalb 20 s (Messung im PR).
- Rule-Eintrag in `rules/1-generic/branch-guard.md`, `CHANGELOG.md`-Zeile.

### Betroffene Dateien

`hooks/1-generic/orchestrator-guard-impl.sh` / `hooks/1-generic/lib/hook_common.sh`
(Classifier), `tests/test_dod_push_check_hook.py`, `rules/1-generic/branch-guard.md`,
`CHANGELOG.md`.

---

## I5 — Issue #971 (keine dangling lazy pointer)

**State: BLOCKED-BY-DECISION.**

### Erledigt

Nichts über die Issue-Existenz hinaus. Der Welle-3-Entscheid Q8 hat das Kriterium offen gelassen.

### Offen

**Es existiert kein Akzeptanzkriterium.** Ohne AC ist das Issue weder planbar noch
schließbar — jede Planung wäre erfunden.

### Exakt nächste Aktion

Der User liefert das Akzeptanzkriterium (z. B. „`sync.py --validate` meldet 0 dangling
Pointer auf einem frischen Checkout“ vs. „jeder Pointer löst auf eine existierende Datei auf“).
Erst danach: State → READY, Spec, Approval, Plan.

### Akzeptanz-Evidenz

Noch nicht definierbar (Kriterium fehlt).

### Betroffene Dateien

Unbestimmt — hängt am Kriterium.

---

## I6 — Issue #192 (Phase 2 selektives Rule-Embedding)

**State: NO ACTION.** Per Entscheid vertagt, `enhancement,deferred`.

### Exakt nächste Aktion

Nichts. Issue offen lassen, nicht planen, nicht schließen.

---

## I7 — AC2-Residual: `timeout-minutes` für `scorecard.yml:jobs.analysis`

**State: READY** · Größe **S** (1 Datei, 2 Zeilen) · Gate: keins über PR-Review hinaus.
Trace: `SPEC-test-hygiene-945` (AC2), #945. Rolle: `junior-developer` (Change), `git` (PR).

### Erledigt

Nichts — der Befund ist heute verifiziert, die Änderung fehlt.

### Ist-Stand (verifiziert gegen `main` @ `ec359896`)

| Workflow | Jobs | `timeout-minutes` |
|---|---|---|
| `.github/workflows/orchestration-test.yml` | 5 (`changes`, `test`, `subprocess-shard`, `compat-311`, `orchestration-gate`) | 5 / 30 / 30 / 30 / 5 — alle gesetzt |
| `.github/workflows/validate.yml` | 3 (`scenarios`, `validate`, `validate-gate`) | 30 / 10 / 5 — alle gesetzt |
| `.github/workflows/scorecard.yml` | 1 (`analysis`) | **fehlt** |

→ **8 von 9 Jobs sind begrenzt; einer nicht.** Es gibt genau drei Workflow-Dateien.

### Offen

- `timeout-minutes: 10` unter `.github/workflows/scorecard.yml:jobs.analysis` ergänzen
  (Wert in einem Satz begründen, z. B. Scorecard-Analyse-Laufzeit + Puffer).

### Exakt nächste Aktion

Entweder **in Welle-4-Phase P5 falten** (dort ebenfalls Docs/CI-only, 2 Dateien) —
**empfohlen**, weil es denselben PR-Review-Zuschnitt nutzt und AC2 damit im selben Strang
schließt — oder als eigenständiger Zwei-Zeilen-PR (`chore:`/`fix:`) liefern.

### Akzeptanz-Evidenz (Verifikation)

- `grep -n 'timeout-minutes' .github/workflows/*.yml` findet für **jeden** Job in allen
  drei Workflow-Dateien den Key (9 von 9), insbesondere `scorecard.yml:jobs.analysis`.
- CI-Diff zeigt nur die zwei Zeilen; keine anderen Workflow-Änderungen.

### Betroffene Dateien

`.github/workflows/scorecard.yml`.

---

## Empfohlene Reihenfolge

| # | Schritt | Begründung (eine Zeile) |
|---|---|---|
| 1 | **I2** Housekeeping (Rev. 3.1 + Rebase + PR) | Kleinster Aufwand, entsperrt I1 und verhindert, dass die Spec mit driftenden Zeilennummern und falschen Zahlen in die Approval geht. |
| 2 | **I1 / P1** | P1 legt den Timeout-Vertrag und die Hook-Isolation fest — Voraussetzung für P2a/P2b/P3 (strikte Ordnung) und für P4. |
| 3 | **Entscheid: I3 vs. I1 / P2a** | P2a ist die größte mechanische Phase (32 Dateien); #1050 ist ein klar umrissener Bugfix. Wenn Reviewer-Kapazität knapp ist, parallelisierbar — P3-AST-Check würde #1050 ohnehin nicht berühren. |
| 4 | **I1 / P2b → P3** | P3 (AST-Check in `sync.py --validate`) ist erst sinnvoll, wenn die Adoption durch ist — sonst meldet der Check sofort hunderte Findings. |
| 5 | **I4** (#1051) | Gleiche Hook-Familie wie #1050, aber größerer Change: erst nach #1050, damit der Classifier nicht zweimal umgebaut wird. |
| 6 | **I1 / P4 → P5/P6**, **I7** in P5 falten | P4 setzt P1 voraus; P5 (Doku) und P6 (`browser-test.yml`) sind unabhängig und können hinterherlaufen; I7 (AC2-Residual, 2 Zeilen) ist ebenfalls CI/Doku-only und schließt AC2 im selben Strang. |
| 7 | **I5 / I6** | Warten ausschließlich auf den User (Kriterium bzw. vertagt). |

## Geschlossen in dieser Session (Kontext — kein offener Punkt)

- **Welle 3 vollständig gemergt:** PR #1047, #1048, #1049.
- **Hook-Allowlist-Fix:** PR #1067 (Merge `ec359896`) — schließt #1055.
- **#856:** als not-planned geschlossen (Doku-Entscheid, Welle 3 R4).
- **Refspec-Reparatur (lokale Config, keine Repo-Änderung):** `remote.origin.fetch` war auf
  drei gepinnte Refs (inkl. eines gelöschten Branches) verengt; auf einen Wildcard
  zurückgesetzt. `git fetch --all --prune` funktioniert wieder. **Nur lokal, nicht versioniert.**
- **Welle-3-Folge-Issues angelegt:** #1050 (aus Q10), #1051 (Residuum #953).

## Offene Entscheidungen für den User

1. **Spec-Approval I1:** `Status: APPROVED` in `docs/specs/2026-10-30-test-hygiene-945-design.md`
   setzen (Rev. 3 Review-Verdikt: APPROVED; Marker fehlt bewusst).
2. **OQ-4:** `continue-on-error: true` für den ersten `browser-test.yml`-Lauf — Default ja,
   genau eine Runde, im selben PR entfernt. Bestätigen oder ablehnen.
3. **#971:** Akzeptanzkriterium liefern — ohne AC bleibt der Punkt BLOCKED-BY-DECISION.
4. **Programm-Zuschnitt Welle 4:** phase-by-phase (P1 → Gate → P2a → …) oder als ein
   Programm mit einem gemeinsamen Plan? Auswirkung: Anzahl der Review-/Approval-Schleifen
   und die Größe des ersten PR (P1 mit 14 Dateien ist reviewbar, P2a mit 32 nur schwer).
5. **I3-vs-P2a-Vorrang** (Empfehlung: P2a zuerst, wenn Review-Kapazität da ist; sonst #1050).

## Known Constraints (Umgebung, aus dieser Session)

- **`rtk pytest` ist in dieser Umgebung defekt** (`Failed to spawn process`) → immer
  `python3 -m pytest` verwenden.
- **Volllauf passt in keinen Tool-Call:** lokal ~6207–6575 Tests / 359–362 Dateien bei
  ~2,0 s/Test ≈ **3,4 h**; ein Tool-Call ist bei ~25 min gekappt. CI shardet:
  `.github/workflows/orchestration-test.yml` mit `pytest-split`, `-n 2 --dist loadfile`;
  **`-n auto` ist repo-weit verboten** (jeder Worker spawnt eigene `sync.py`-Kinder).
- **Lokaler CI-Runner:** PR #1054 hat `scripts/ci-local.sh` hinzugefügt und
  `tests/README.md` angefasst → für Pre-Push-Verifikation `scripts/ci-local.sh` nutzen,
  nicht den Volllauf.
- **Runner-Ausfälle:** drei begrenzte Watch-Fenster (~18 min je) gingen an einen
  GitHub-Kapazitätsstau (Jobs 19–24 min in der Queue, repo-weit). **Checks niemals per
  `--admin` umgehen** — warten und erneut beobachten.
- **`.claude/hooks/.guard-audit.log`** existiert (210 Zeilen), enthält aber **keine**
  `tool_name`-Records (nur Shell-Guard-Zeilen) → **keine** brauchbare Quelle für beobachtete
  Tool-Namen. Für AC1 nicht als Evidenz verwenden.
- **Branch-Guard:** keine Code-Änderungen auf `main`/`master`; Feature-Branches
  (`feat/`, `fix/`, `chore/`, `docs/`).
- **Kein Worktree-Isolation:** Subagenten arbeiten direkt im Projektverzeichnis.

## Trace-Anker

- Spec: `SPEC-test-hygiene-945` → `docs/specs/2026-10-30-test-hygiene-945-design.md`
- Review: `docs/reviews/2026-10-30-test-hygiene-945-rev3-narrow-review.md`
- Issues: **#945** (Welle 4, Test-Hygiene), **#1050** (`}`-Lücke), **#1051** (Submodule-Push-Ziele),
  **#971** (dangling lazy pointer, ohne AC), **#192** (vertagt)
- PRs (Kontext): **#1047**, **#1048**, **#1049** (Welle 3), **#1067** (Hook-Allowlist, schließt #1055),
  #1054 (ci-local + `tests/README.md`)
- Welle-3-Basis: `docs/plans/2026-10-29-bugfix-wave-3-plan.md`, `docs/specs/2026-10-29-bugfix-wave-3-spec.md`

## Unverifiziert (bewusst so markiert)

1. **AC1** (Hook-Isolation) — Stand stammt aus der Session, heute nicht nachgelaufen.
2. **AC3-Zählung** 203 Call-Sites / 73 Dateien — Session-Messung, heute nicht nachgezählt.
3. **AC4** — ob die Artefakt-Tests einen vorherigen `sync.py`-Lauf brauchen, ist nicht geprüft;
   verifiziert ist nur, dass sie in keiner der sechs expliziten CI-Listen stehen.
4. **AC5** — nur der Ist-Zustand der Jobs ist verifiziert, nicht die (fehlende) Entscheidungs-Doku.
5. **I1-Phasengrößen** (14/32/31/5/3/2/3 Dateien) und F7-Einstufungen — aus der Session übernommen.
6. **`tests/README.md`-Zeilen** — Lage der Timeout-Tabelle nur grob geprüft; deshalb die
   Umstellung auf `file:symbol` in I2.
7. ~~**AC2-Zahlenkonflikt** (Session-Notiz „30/30/30/30/10“ vs. Datei 5/30/30/30/5 + 30/10/5)~~
   — **verifiziert am 2026-10-30 gegen `main` @ `ec359896`:** Es gibt genau drei
   Workflow-Dateien mit 9 Jobs; 8 tragen `timeout-minutes`
   (`orchestration-test.yml`: `changes` 5, `test` 30, `subprocess-shard` 30, `compat-311` 30,
   `orchestration-gate` 5; `validate.yml`: `scenarios` 30, `validate` 10, `validate-gate` 5),
   `scorecard.yml:jobs.analysis` nicht. Die Session-Zahl „30/30/30/30/10“ ist damit obsolet;
   die AC2-Aussage „bereits erfüllt“ ist widerlegt (Residual → **I7**). Offen bleibt nur die
   Korrektur in Rev. 3.1 (I2).
