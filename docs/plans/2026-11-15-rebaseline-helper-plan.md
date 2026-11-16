---
pipeline_stages:
  implement: 1
status: geplant
date: 2026-11-15
spec: docs/specs/2026-11-15-rebaseline-helper-spec.md
spec-status: APPROVED (User, 2026-11-16)
klasse: M
branch: feat/rebaseline-helper
---

# Rebaseline-Helper Implementation Plan

> Status: geplant — Spec APPROVED (User, 2026-11-16, E-10); Umsetzung erst nach P3 (#1246, Linux-Basetemp-Stabilität; kein allgemeiner Render-Determinismus, Spec OF-4); Entscheidungen 1-7 der Spec sind getroffen.

**Goal:** Ein Befehl (`scripts/rebaseline.py`) führt AC-01-Manifest, Standalone-Render, `sync.py`, topology-a2a-Fixtures, AC-T4-Digests und Ceiling-Messung in fester Reihenfolge aus, erzwingt ein Diff-Gate, schreibt ein Reason-Log und berichtet vorab/nachher die betroffenen Pins (Issue #1237, #1115).

**Architecture:** Dünner Entrypoint `scripts/rebaseline.py` (argparse, `main()`), Logik in `scripts/lib/rebaseline.py` (Pin-Registry als Daten, Schritt-Runner mit Snapshot/Rollback, Gate, Report, Log). Subprozess-Aufrufe über eine injizierbare Runner-Funktion (testbar ohne echten Sync). Root aus dem Helper-Ort, jeder `sync.py`-Aufruf mit explizitem `--config`.

**Tech Stack:** Python 3.9 (Stdlib only), pytest, JSON-Lines-Log.

**Spec:** docs/specs/2026-11-15-rebaseline-helper-spec.md

## Global Constraints

- Python 3.9-kompatibel: kein `X | Y`, kein `match`; `typing.List`/`Optional`.
- Nur Stdlib; keine neuen Dependencies.
- `scripts/lib/rebaseline.py` ≤ 600 Zeilen; bei Überschreiten Pin-Registry nach `scripts/lib/rebaseline_pins.py`.
- Kein `print()` in `lib/`; Ausgabe über Rückgabewerte/`SyncLog`; `print()` nur im Entrypoint.
- Kein Provider-/Modellname im Code (`tests/test_provider_agnostic_dispatch.py`).
- Keine Render-Wirkung des Helper-Codes: kein Template-/Rule-/Config-Edit, daher keine Rebaseline durch diesen PR (Roadmap P4); Ausnahme Skill-Verweis, falls dessen Quelle ein Template ist (Task 10, OF-7).
- Scratch/Snapshot im Tmp-Sink (`resolve_tmp_paths`, `.tmp/`), nicht unter Systemtemp (Repo-Containment).
- PR-Text: `Refs #1237` (kein Closing-Keyword; #1237 Empf. 2 bleibt offen, Spec OF-4).
- Tests rendern nicht den vollen Matrix-Sync; Runner/Registry werden gemockt, es gibt keinen automatisierten Integrationstest; der einzige echte `--check-only`-Lauf ist manuell (Task 8 Step 2 und Task 11 Step 2).
- Branch `feat/rebaseline-helper`; kein Amend, kein Force-Push; Push/Tag/Branch nur durch Rolle `git`.
- Commit-Betreff Englisch, Imperativ, ≤ 72 Zeichen, Format `<type>: <beschreibung>`.
- Alle Tasks strikt sequentiell; Task-IDs numerisch; `Depends on:` nennt die Vorgängernummer.
- Fixture-Verzeichnis `tests/fixtures/ac01-baseline/` bleibt frei von Zusatzdateien (AC-T4-Digest über `rglob`).

## File Structure

- Create: `scripts/lib/rebaseline.py` — Gate, Snapshot/Rollback, Schritt-Runner, Report, Log (Tasks 1-7)
- Create: `scripts/rebaseline.py` — Entrypoint (Task 8)
- Create: `tests/test_rebaseline_helper.py` — Unit-Tests je Task (Tasks 1-9)
- NICHT in diesem PR: `.meta-config/rebaseline-log.jsonl` — Laufzeit-Artefakt, entsteht erst beim ersten echten Schreiblauf (Task 10 Step 2, falls der Helper dort genutzt wird); kein Create-Eintrag dieses PR (Spec Entscheidung 2)
- Modify: `howto/` (passender Eintrag) — Task 10; Doku-Verweis im `conventions`-Skill nur nach Quellverifikation (OF-7)
- Modify: `CHANGELOG.md` — Task 10
- Task 7 liegt in `scripts/lib/rebaseline.py` (bzw. `rebaseline_pipeline.py`)

## Tasks

### Task 0: Spec freigeben und committen (Gate: P3 #1246 gemerged, Reihenfolge P3 -> P4)
> Gate-Stand: P3 = PR #1291 ist GEMERGT (Merge-Commit 84e849ed) → Gate P3 erfüllt. Spec-Gate erfüllt: Spec APPROVED (User, 2026-11-16). #1291 ändert `tests/fixtures/topology-golden/schema-property-paths.json` (reine Pfadliste, hash-neutral laut Analyse); Roadmap P3 „RB keiner“ bleibt konsistent. Zusätzlich: OF-1/5/6 sind entschieden (Nutzer, 2026-11-16); verbleibend offen: OF-8 (vor Task 0; Akzeptanz von `DRAFT`/`APPROVED` durch `--validate-spec-plan` ist UNBELEGT), OF-9 (vor Task 11), OF-2/3/4/7 nicht blockierend.
**Agent:** documenter
**Depends on:** keine
**Files:**
- Modify: `docs/specs/2026-11-15-rebaseline-helper-spec.md`
- Modify: `docs/plans/2026-11-15-rebaseline-helper-plan.md`

**Interfaces:** Produces: Spec `Status: APPROVED (User, 2026-11-16)`, Entscheidungen 1-7 stehen bereits in der Spec; Consumes: Nutzerentscheidung E-10.
**AC:** Gate vor allen Folge-Tasks.
- [ ] Step 1: Prüfen, dass P3 (#1246) gemerged ist; Spec-Freigabe durch den Nutzer einholen.
- [ ] Step 2: Status auf APPROVED setzen; `python3 scripts/sync.py --validate-spec-plan --config <abs>/.meta-config/project.yaml` grün.
- [ ] Step 3: Commit `docs: add rebaseline helper spec and plan`.

### Task 1: Root-Auflösung und Runner
**Agent:** developer
**Depends on:** 0
**Files:**
- Create: `scripts/lib/rebaseline.py`
- Create: `tests/test_rebaseline_helper.py`

**Interfaces:** Produces: `resolve_root(script_file, override=None) -> Path`, `build_sync_cmd(root, *extra) -> List[str]` (immer `--config <root>/.meta-config/project.yaml`), `run_step(cmd, root, runner=subprocess.run)` (immer `cwd=root`, `sys.executable`); Fehlerpfad: fehlende Config → `RebaselineError` (Exit 2). Consumes: nichts.
**AC:** 7, 8.
- [ ] Step 1: Rote Tests: `resolve_root` ignoriert `cwd` (monkeypatch `os.chdir`), `build_sync_cmd` enthält `--config`, `run_step` setzt `cwd`, fehlende Config wirft.
- [ ] Step 2: Minimale Implementierung bis grün: `python3 -m pytest tests/test_rebaseline_helper.py -q`.
- [ ] Step 3: Commit `feat: add rebaseline root resolution and runner`.

### Task 2: Snapshot und Rollback
**Agent:** developer
**Depends on:** 1
**Files:**
- Modify: `scripts/lib/rebaseline.py`
- Modify: `tests/test_rebaseline_helper.py`

**Interfaces:** Produces: `Snapshot.take(root, paths)`, `Snapshot.restore()` (byte-genau, löscht neu entstandene Dateien, kein Git-Schreibzugriff). Consumes: Task 1.
**AC:** 6, 15.
- [ ] Step 1: Rote Tests: Änderung/Neuanlage/Löschung wird exakt zurückgesetzt; Dateien außerhalb der Pfadliste bleiben unberührt.
- [ ] Step 2: Implementierung bis grün.
- [ ] Step 3: Commit `feat: add rebaseline snapshot and rollback`.

### Task 3: Diff-Gate
**Agent:** developer
**Depends on:** 2
**Files:**
- Modify: `scripts/lib/rebaseline.py`
- Modify: `tests/test_rebaseline_helper.py`

**Interfaces:** Produces: `CLASS_ALLOWLIST` (Daten), `derive_expected_stems(changed_sources) -> Set[str]`, `check_gate(changed_files, changed_keys, expect, expect_key, stems) -> List[str]` (Liste der Verletzungen; leer = ok). Quellen ohne Stem-Abbildung erlauben keine Schlüssel (fail-closed). Consumes: Task 2.
**AC:** 4, 6.
- [ ] Step 1: Rote Tests: erlaubter Stem passiert, fremder Schlüssel verletzt, `--expect-key`-Glob erlaubt, `config/**`-Quelle ohne Expect → Verletzung, Klassen-Allowlist ok.
- [ ] Step 2: Implementierung bis grün.
- [ ] Step 3: Commit `feat: add rebaseline diff gate`.

### Task 4: Pin-Registry und Detektoren
**Agent:** developer
**Depends on:** 3
**Files:**
- Modify: `scripts/lib/rebaseline.py` (oder Create: `scripts/lib/rebaseline_pins.py` bei > 600 Zeilen)
- Modify: `tests/test_rebaseline_helper.py`

**Interfaces:** Produces: `PinSpec(klass, paths, detector, action)`, `PINS` (AC, AC-T4, SG, CG, TG, H1, H2, SA, CE), `impact_report(root, runner) -> List[PinStatus]` (`ok|betroffen|n/a`). Consumes: Task 1, Task 3.
**AC:** 2, 3, 13.
- [ ] Step 1: Rote Tests: Registry enthält alle 9 Klassen (TG: a2a `auto`, Schema-Pfade `report-only`) und die Fixtures `compact-golden/agents-managed.md`, `topology-golden/schema-property-paths.json`; gemockter Runner liefert `betroffen` bei rotem Detektor.
- [ ] Step 2: Implementierung bis grün; AC-T4-Detektor ruft `_fixture_tree_sha256` aus dem bestehenden Testmodul via `importlib`.
- [ ] Step 3: Commit `feat: add rebaseline pin registry and impact report`.

### Task 5: Schritte ac01, standalone, sync, topology, digests
**Agent:** developer
**Depends on:** 4
**Files:**
- Modify: `scripts/lib/rebaseline.py`
- Modify: `tests/test_rebaseline_helper.py`

**Interfaces:** Produces: `step_ac01`, `step_standalone`, `step_sync`, `step_topology` (a2a-Fixtures per Render, Aktion auto), `step_digests`, `STEP_ORDER = ("ac01","standalone","sync","topology","digests","ceilings")`; `step_ac01` schreibt nur abweichende Schlüssel im Format `indent=1, sort_keys=True` plus `"\n"`; `step_digests` ersetzt automatisch nur die `_FIXTURE_TREES`-Zeile (in der Gate-Allowlist). Consumes: Task 1-4.
**AC:** 4, 5, 9, 10, 18, 19, 20.
- [ ] Step 1: Rote Tests: Reihenfolge der aufgezeichneten Runner-Aufrufe, Schlüssel-Patch lässt andere Zeilen unberührt, Preflight bricht nur bei veränderten Artefakten (uncommittete Quellen erlaubt); `--base`-Fallback auf lokales `main` mit Warnung, Idempotenz (zweiter Lauf 0 Änderungen) mit gemocktem Render.
- [ ] Step 2: Implementierung bis grün.
- [ ] Step 3: Commit `feat: add rebaseline write steps`.

### Task 6: Ceiling-Report, Log, Exit-Codes
**Agent:** developer
**Depends on:** 5
**Files:**
- Modify: `scripts/lib/rebaseline.py`
- Modify: `tests/test_rebaseline_helper.py`

**Interfaces:** Produces: `ceiling_repin_block(report, ist_full, ist_compact) -> str` (nur Ausgabe, keine Dateiänderung), `append_log(root, entry)` (nur bei Änderungen), `EXIT_*`-Konstanten (0-6; 6 = Rest-Drift, entschieden, Spec OF-1). Consumes: Task 5, `scripts/lib/context_report.py:130` (`measure_artifacts`).
**AC:** 11, 12, 14.
- [ ] Step 1: Rote Tests: Block nennt Provider/Artefakt/alt/neu; Toleranz-Datei hashgleich; Log-Zeile valide und nur bei Änderung; `--json`-Felder.
- [ ] Step 2: Implementierung bis grün.
- [ ] Step 3: Commit `feat: add rebaseline ceiling report and log`.

### Task 7: run_pipeline, Verify und Idempotenzlauf
**Agent:** developer
**Depends on:** 6
**Files:**
- Modify: `scripts/lib/rebaseline.py` (bei > 600 Zeilen: `scripts/lib/rebaseline_pipeline.py`)
- Modify: `tests/test_rebaseline_helper.py`

**Interfaces:** Produces: `run_pipeline(root, options, runner=subprocess.run) -> PipelineResult` (Preflight inkl. Dirty-Baseline → Schritte in `STEP_ORDER` → Rollback bei Exit 3/4 → zweiter Check-only-Durchlauf (Idempotenz, Rest-Drift → Exit 6, entschieden, Spec OF-1) → `verify(root, runner)` (gezielte `pytest -q`-Aufrufe aus der Registry, rot → Exit 5; `--skip-verify` übersprungen) → Log nur bei Änderungen), `verify(root, runner) -> List[PinStatus]`, Step-Runner mit Subprozess-Fehlerbehandlung (Exit ≠ 0 → Exit 4 + Rollback). Scratch/Snapshot im Tmp-Sink (`resolve_tmp_paths`), nicht Systemtemp. Consumes: Task 1-6.
**AC:** 5, 13, 15, 21, 22.
- [ ] Step 1: Rote Tests mit gemocktem Runner: Preflight (AC 10: dateiweise, `test_opencode_v2_surface.py` zeilenweise nur für `_FIXTURE_TREES`; Quell-/Hand-Golden-Dirty blockiert nicht); Reihenfolge Preflight→Schritte→Idempotenzlauf→Verify→Log; Rest-Drift → Exit 6 mit weiterlaufendem Verify/Log (`idempotency: failed`); Subprozess-Fehler → Exit 4 + Rollback; Gate-Verletzung → Exit 3 + Rollback; instabiler Render im zweiten Durchlauf → Exit 6; roter Pin-Test → Exit 5 mit Log `verify: failed`; Check-only schreibt nichts.
- [ ] Step 2: Implementierung bis grün.
- [ ] Step 3: Commit `feat: add rebaseline pipeline, verify and idempotency run`.

### Task 8: Entrypoint und CLI
**Agent:** developer
**Depends on:** 7
**Files:**
- Create: `scripts/rebaseline.py`
- Modify: `tests/test_rebaseline_helper.py`

**Interfaces:** Produces: `main(argv) -> int` mit Flags der Spec C2, Exit-Codes C3 (0-6). Consumes: Task 1-7 (`run_pipeline`).
**AC:** 1, 2, 3, 8, 14.
- [ ] Step 1: Rote Tests (Subprozess nur für `--help`/Fehlerpfade): ohne `--reason` Exit 2; `--check-only` Exit 0/1 per gemocktem Pipeline-Runner; unbekannter Step Exit 2.
- [ ] Step 2: Implementierung bis grün; manuell `python3 scripts/rebaseline.py --check-only --root <worktree>` einmal ausführen und Report beobachten.
- [ ] Step 3: Commit `feat: add rebaseline entrypoint`.

### Task 9: Strukturtests und Provider-Agnostik
**Agent:** tester
**Depends on:** 8
**Files:**
- Modify: `tests/test_rebaseline_helper.py`

**Interfaces:** Produces: Meta-Tests (Zeilenzahl ≤ 600, kein `print()` in `lib/rebaseline.py`, keine Provider-Literale, Stdlib-Imports; transitives PyYAML über Testmodul-Import unter ADR 0001 erlaubt). Hinweis: `tests/test_provider_agnostic_dispatch.py` scannt nur `scripts/lib/**` — `scripts/rebaseline.py` per eigenem Meta-Test abdecken. Consumes: Task 8.
**AC:** 16.
- [ ] Step 1: Tests schreiben und gegen `python3 -m pytest tests/test_rebaseline_helper.py tests/test_provider_agnostic_dispatch.py -q` laufen lassen.
- [ ] Step 2: Commit `test: add rebaseline structure checks`.

### Task 10: Doku, Skill-Verweis, CHANGELOG
**Agent:** documenter
**Depends on:** 9
**Files:**
- Modify: `howto/` (neuer oder bestehender Eintrag zu Rebaseline)
- Modify: `CHANGELOG.md`
- Modify: Quelle des `conventions`-Skills (Verweis auf den Befehl)

**Interfaces:** Produces: Doku zu Flags, Exit-Codes, Gate, Log-Ort; Consumes: Spec Abschnitte C2-C6. Hinweis: die Quelle des `conventions`-Skills ist UNBELEGT (`.claude/skills/conventions/SKILL.md` ist generiert; `agents/1-generic/skills/conventions/SKILL.md` existiert nicht; Glob/Grep waren nicht lauffähig). Ein Edit an einer Template-Quelle hat Render-Wirkung → Rebaseline nötig und Henne-Ei (Helper noch nicht gemergt). Deshalb Step 0: Quelle per Read verifizieren; Default laut Spec OF-7: Verweis nur in `howto/`/Docs, Skill-Edit erst im Folge-PR mit dem fertigen Helper.
**AC:** 17.
- [ ] Step 1: Dokumente schreiben; Platzhalter-/Docs-Tests laufen: `python3 scripts/sync.py --validate --config <abs>/.meta-config/project.yaml`.
- [ ] Step 2: Falls Skill-Quelle editiert: den neuen Helper selbst für die Rebaseline benutzen (erster Anwender), Ergebnis im Report belegen.
- [ ] Step 3: Commit `docs: document rebaseline helper`.

### Task 11: Verifikation
**Agent:** test-executor
**Depends on:** 10
**Files:**
- Modify: keine (reine Ausführung)

**Interfaces:** Produces: Pass/Fail je Kommando; Consumes: Gesamtstand 0-10.
**AC:** 1-22.
- [ ] Step 0: Vorab klären: bestehende Sync-Drift (22 Dateien out of sync laut #1291-Bericht, TMPDIR-unabhängig, nicht gegen HEAD verglichen) per frischem `python3 scripts/sync.py --check --config <abs>/.meta-config/project.yaml` auf main bestimmen; sonst ist Step 2 (Exit 0) nicht erreichbar.
- [ ] Step 1: `python3 -m pytest tests/test_rebaseline_helper.py tests/test_provider_agnostic_dispatch.py -q`.
- [ ] Step 2: `python3 scripts/rebaseline.py --check-only` auf sauberem, drift-freiem Stand: Exit 0 (Linux; Plattformgrenze siehe Spec).
- [ ] Step 3: `python3 scripts/sync.py --validate --config <abs>/.meta-config/project.yaml` und `--validate-spec-plan`.
- [ ] Step 4: Bei Rot Befund melden (kein Selbst-Fix); bei Grün keine Commit-Aktion.

## Trace-Anker

spec-id: SPEC-rebaseline-helper-2026-11-15

Verweise: Entscheidung E-10, Roadmap `docs/plans/2026-11-15-master-roadmap.md` P4 / PR 1.3, Issues #1237, #1115.

## Umsetzungsstand

- [ ] Task 0 Spec freigeben und committen
- [ ] Task 1 Root-Auflösung und Runner
- [ ] Task 2 Snapshot und Rollback
- [ ] Task 3 Diff-Gate
- [ ] Task 4 Pin-Registry und Detektoren
- [ ] Task 5 Schritte ac01, standalone, sync, topology, digests
- [ ] Task 6 Ceiling-Report, Log, Exit-Codes
- [ ] Task 7 run_pipeline, Verify und Idempotenzlauf
- [ ] Task 8 Entrypoint und CLI
- [ ] Task 9 Strukturtests und Provider-Agnostik
- [ ] Task 10 Doku, Skill-Verweis, CHANGELOG
- [ ] Task 11 Verifikation

## Risiken

- Spec ist APPROVED (User, 2026-11-16); Task 0 bleibt Gate (OF-8 vor Task 0 offen; P3/#1291 gemergt), kein Code davor.
- Skill-Verweis (Task 10) kann eine Template-Änderung mit Rebaseline sein; sonst entsteht die Henne-Ei-Situation, den Helper vor seiner Fertigstellung zu brauchen.
- `importlib`-Kopplung an `tests/test_ac01_render_identity.py` (Modul-Seiteneffekte); Fallback: Funktionen nach `scripts/lib/` extrahieren.
- Matrix-Render ist langsam; Render-Ergebnis zwischen Schritt 2 und Idempotenzlauf wiederverwenden.
- Pseudo-Drift durch Umgebung kann den Idempotenztest stören; #1246/PR #1291 löst nur den Linux-TMPDIR-Basetemp, #1237 Empf. 2 hat keinen Owner (Spec OF-4).
- Bestehende Sync-Drift (22 Dateien laut #1291-Bericht) bedroht Task 11 Step 2; Klärung vor Task 11.
- `importlib`-Kopplung zusätzlich an `tests/test_opencode_v2_surface.py` (>5500 Zeilen); PyYAML transitiv (ADR 0001).

## Self-Review

- Jeder Task mappt auf genau eine Rolle; jedes Akzeptanzkriterium der Spec (1-22) ist über Task und AC-Nummer abgedeckt: 7, 8 (Task 1), 1, 2, 3 (Task 8; 8 zusätzlich Task 1), 4 (Task 3, 5), 5 (Task 5, 7), 6 (Task 2, 3), 9-10, 18-20 (Task 5), 11-12, 14 (Task 6), 13 (Task 4, 7), 15 (Task 2, 7), 21-22 (Task 7), 16 (Task 9), 17 (Task 10).- `Files:`/`Interfaces:` vollständig; alle Tasks sequentiell, gemeinsame Dateien (`scripts/lib/rebaseline.py`, `tests/test_rebaseline_helper.py`) werden strikt nacheinander fortgeschrieben.
- `pipeline_stages` deckt die einzige `plan-driven`-Stage (`implement`) ab.
- Spec-Entscheidungen 1-7 sind in Tasks 1, 3, 4, 5, 6, 7 abgebildet; AC 18-20 in Task 5; P3-Reihenfolge in Task 0.
- OF-1/5/6 entschieden (Nutzer, 2026-11-16): Exit 6 bei Rest-Drift, Verzicht auf Log-Kommentar, Scratch bei deaktiviertem Sink → Exit 2. Verbleibend offen: OF-2/3/4/7 (nicht blockierend; Plan folgt vorläufig den Empfehlungen: importlib, eigenes Script), OF-8 vor Task 0, OF-9 vor Task 11.
- Effort-Schätzung: `effort-estimator` (Textverweis, hier bewusst nicht berechnet).
