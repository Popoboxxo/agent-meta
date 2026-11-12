# Checkpoint-Tracking (#1000) — Spec
> Status: DRAFT
> Datum: 2026-11-12 | Ist-Anker: Worktree `fix/phase-c-sync-config` | Plan: `docs/superpowers/plans/2026-11-11-phase-c-sync-config.md` (Task 0b, Task 13) | Schwester-Spec: `docs/specs/2026-11-11-phase-c-sync-config-spec.md`
> Issue: #1000 "design: plan/handoff checkpoints live in gitignored .meta-viz/ — references dangle in fresh clones"

## Problem

**Problem.** Der Checkpoint-/Progress-Store schreibt standardmäßig nach `.meta-viz/` (`scripts/lib/progress_paths.py:34-35`). Der verwaltete `.gitignore`-Block schließt `.meta-viz/` aus (in diesem Repo `.gitignore:54`; belegt: `git check-ignore -v .meta-viz/checkpoints` -> `.gitignore:54:.meta-viz/`, rc 0, auch ohne existierendes Verzeichnis). Ein Plan/Handoff, der einen Checkpoint dort zitiert, zeigt in einem frischen Clone oder auf einem anderen Branch ins Leere. Weder Tooling noch Doku warnen davor (Issue "Problem").

## Ziel

**Ziel.** Option B (Durchsetzungsboden) + Option C (Prozessregel) gemäß Entscheidungen 8, 43, 55:
- B1: `resolve_progress_paths` meldet ein Finding, wenn das Checkpoint-/Progress-Verzeichnis gitignoriert ist.
- B2: `--validate-spec-plan` meldet zitierte Checkpoint-Pfade, die fehlen oder gitignoriert sind.
- C: `snippets/orchestrator/checkpointing.md` trennt ephemer/clone-lokal von getrackt und legt die Prozessregel "Umsetzungsstand im selben PR" fest.

## Nicht-Ziele

**Nicht-Ziele.**
- Option A (getrackter Checkpoint-Ort) ist nicht Teil dieser Runde.
- Kein Exit-Code-Wechsel bei B1 (Warnung); `--validate` bleibt Exit 0.
- Keine Umstellung des Defaults `DEFAULT_CHECKPOINT_DIR`/`DEFAULT_PROGRESS_DIR` und kein neuer Unterdrückungs-Key für Findings (Entscheidung 55).
- Keine Änderung am Schreibpfad von `CheckpointStore` (kein Blockieren des Schreibens).
- Kein `git ls-files`-Check auf "tracked" (siehe Risiken R2).
- Keine Closing-Keywords in Commit/PR-Texten (Entscheidung 38e).

## Issue-Wortlaut der Optionen (Quelle: Issue #1000, Abschnitt "Proposed behavior — options"; keine Kommentare am Issue)

- **A:** "Track referenced checkpoints. Checkpoints/status that plans or handoffs reference must live at a *tracked* location — e.g. alongside the plan in `docs/plans/`, in `.meta-config/`, or a dedicated tracked `checkpoints/` directory. Keep `.meta-viz/` for ephemeral runtime artifacts only."
- **B:** "Warn/fail when the target is untracked. If `.meta-viz/` must stay gitignored, agent-meta tooling should (a) warn or fail when a checkpoint is written into a gitignored directory, and (b) validate plan/handoff checkpoint paths before they are cited, failing on non-existent or untracked targets."
- **C:** "Process rule. The "Umsetzungsstand"/status must be committed in the **same PR** as the phase it documents (not in a separate open branch), so resume references are stable on `main`."
- Empfehlung des Issues: "Adopt **B as the enforcement floor** and **C as the process rule**" mit "B ... implementable in the existing path-resolution layer: extend `scripts/lib/progress_paths.py` (and the `--checkpoint`/plan-path validation) with a gitignore/`git ls-files` check that emits a finding (or exits non-zero)"; "Optionally **A** for artifacts that are explicitly part of a plan's handoff contract."
- Issue-DoR (Akzeptanzkriterien): (1) Warnung oder Non-Zero-Exit bei Schreiben in gitignoriertes Verzeichnis bzw. Zitat eines untracked/fehlenden Checkpoint-Pfads, Oberfläche im PR benannt; (2) `checkpointing.md` benennt ephemer/clone-lokal vs. tracked und wie ein Plan Resume-State referenziert; (3) mindestens ein Regressionstest für untracked/missing; (4) Prozessregel C dort dokumentiert, wo Plan-Status geschrieben wird.

**Abgleich mit Plan/Entscheidung 8, 43, 55.** "B+C" entspricht exakt der Issue-Empfehlung. Zwei Feinunterschiede, beide innerhalb der Empfehlung:
- Das Issue nennt "gitignore/`git ls-files` check"; diese Spec wählt `git check-ignore` (bestehender Helfer, siehe Contracts) statt `git ls-files` (R2).
- Option C nennt das Issue "same PR" für den "Umsetzungsstand"-Abschnitt von Plänen; der Plan-Auftrag setzt C als Absatz in `checkpointing.md` + Planvorlage-Hinweis um (DoR 4: "where plan status is written").

## Ist-Zustand (am Code belegt)

- `scripts/lib/progress_paths.py:49` `class ProgressPathFinding` (Felder `level: str`, `code: str`, `message: str`); `:180` `resolve_progress_paths(project_root: Path, config: Optional[dict] = None) -> ResolvedProgressPaths` (:180-237); Leaf-Modul, importiert `from .io import SyncError, _load_yaml_or_json` (:31). `progress`-Block kennt nur `dir` und `checkpoint-dir` (:41-43).
- `scripts/lib/checkpoint.py:338` Parameter `checkpoint_dir`, :367 Default-Zuweisung `self.project_root / DEFAULT_CHECKPOINT_DIR`; `:388` ist der einzige Aufrufer von `resolve_progress_paths` und verwirft die Findings. Kein `check-ignore` in `checkpoint.py`/`progress_paths.py`.
- `scripts/lib/io.py:543` `run_git_check_ignore(target: str, cwd: str, *flags: str) -> "subprocess.CompletedProcess | None"`: `None` bei Git-Aufruf-Fehler; rc 0 = ignoriert, 1 = nicht ignoriert, >1 = Git-Fehler (gemessen: rc 128 außerhalb eines Repos). `io.py` importiert nur Stdlib, kein Import-Zyklus mit `progress_paths.py`.
- `--validate` sammelt Findings als `lib.consistency.report.Finding(severity, check, file, message, suggestion="")` in `_strict_findings` (`scripts/lib/cli_commands.py` um :1500-1510, `check_temp_literals`-Block) und druckt sie über `print_report`; WARNING-Familien dort ändern den Exit-Code nicht (Vorbild: temp-literals, ADR-06).
- `scripts/lib/spec_plan_validate.py:73` `validate_spec_plan(project_root, config, log) -> int` ruft `check_spec_plan_workflow` (`scripts/lib/consistency/spec_plan.py:153`) und liefert Exit 1 bei jedem Finding.
- `snippets/orchestrator/checkpointing.md:2` nennt `.meta-viz/checkpoint-<timestamp>.json`, :28-31 `.meta-viz/checkpoints/<session>.json` als Resume-Quelle, ohne ephemer/tracked-Hinweis.

## Gewählte Lösung

B+C wie oben; A nicht in dieser Runde. Entscheidung 55: agent-meta selbst behält `.meta-viz/` als Default. Auf diesem Repo erscheint `progress.checkpoint-dir-ignored` daher bei `--validate` dauerhaft; das ist **dokumentiert hingenommen** (Warnung, Exit 0, kein Unterdrückungs-Key). Wer die Warnung loswerden will, setzt `progress.checkpoint-dir` auf einen nicht ignorierten Pfad (bestehender Key).

## Interface Contracts

### IC-1 — `progress_paths.py`: Finding `progress.checkpoint-dir-ignored`

- Signatur unverändert: `resolve_progress_paths(project_root: Path, config: Optional[dict] = None) -> ResolvedProgressPaths`; `ProgressPathFinding(level: str, code: str, message: str)` unverändert.
- Neu (privat): `_gitignore_findings(root: Path, checkpoint_rel: str, progress_rel: str) -> list` in `progress_paths.py`; nutzt `from .io import run_git_check_ignore` (Erweiterung des bestehenden Imports :31).
- Verhalten: für `checkpoint_rel` und `progress_rel` je `run_git_check_ignore(rel, str(root))`. Ergebnis `None` oder `returncode not in (0, 1)` -> **übersprungen**, kein Finding, keine Exception (Entscheidung 43, fail-soft). `returncode == 0` -> `ProgressPathFinding("warning", code, message)`.
- Codes: `progress.checkpoint-dir-ignored` (Checkpoint-Verzeichnis) und `progress.progress-dir-ignored` (Progress-Verzeichnis). Die Message nennt den relativen Pfad und den Hinweis, dass Referenzen darauf in frischen Clones ins Leere zeigen, sowie den Opt-out-Key `progress.checkpoint-dir` bzw. `progress.dir`.
- Aufruf: am Ende von `resolve_progress_paths`, nach Berechnung von `*_rel`; Findings werden an `findings` angehängt. Fehlerpfade: keine neuen; die Funktion bleibt "never raises, never exits".

### IC-2 — Ausgabefläche der Warnung (`--validate`)

- Neu: `scripts/lib/consistency/checkpoint_tracking.py`, Funktion `check_checkpoint_dir_ignored(project_root: Path, config: dict) -> list[Finding]`: ruft `resolve_progress_paths(project_root, config)`, mappt jedes Finding mit Code `progress.checkpoint-dir-ignored`/`progress.progress-dir-ignored` auf `Finding(Severity.WARNING, <code>, file=".meta-config/project.yaml", message=<message>)`.
- Einhängen: in `_handle_validate` (`scripts/lib/cli_commands.py`) neben `check_temp_literals` in `_strict_findings`. Warnung ändert den Exit-Code nicht (wie temp-literals).
- Der Schreibpfad (`CheckpointStore.from_config`, `checkpoint.py:388`) verwirft die Findings weiterhin; kein neuer Log-Kanal dort.

### IC-3 — `--validate-spec-plan`: zitierte Checkpoint-Pfade

- Neu, in derselben Datei `checkpoint_tracking.py`: `check_checkpoint_references(project_root: Path, plan_files: Iterable[Path]) -> list[Finding]`.
- Erkennung: Token in Plan-Dateien, das `checkpoint` enthält und auf `.json` endet (Regex `[^\s`'"()<>]*checkpoint[^\s`'"()<>]*\.json`); Platzhalter-Tokens mit `<` oder `{{` werden nicht gematcht.
- Prüfung je Referenz (relativ zu `project_root`): (a) Datei existiert nicht -> `Finding(Severity.ERROR, "checkpoint.reference-missing", file=<plan>, ...)`; (b) existiert, aber `run_git_check_ignore(ref, str(project_root)).returncode == 0` -> `Finding(Severity.ERROR, "checkpoint.reference-ignored", ...)`. `suggestion` verweist auf Option C / `checkpointing.md`.
- Fail-soft (Entscheidung 43): `run_git_check_ignore` liefert `None` oder rc nicht in (0, 1) -> gesamte Referenzprüfung für diese Runde übersprungen, kein Finding.
- Einhängen: `validate_spec_plan` (`scripts/lib/spec_plan_validate.py:73`) hängt die Findings an die von `check_spec_plan_workflow` gelieferten an; Exit 1 bei Finding folgt aus der bestehenden Logik. Die Plan-Datei-Menge ist dieselbe, die `check_spec_plan_workflow` scannt (Aufzählungs-Helfer bei Implementierung zu lokalisieren, nicht verifiziert).

### IC-4 — `snippets/orchestrator/checkpointing.md`

- Ergänzung (Snippet-Version im Frontmatter erhöhen, falls vorhanden): Absatz "Persistence scope" mit (1) `.meta-viz/**` ist ephemer/clone-lokal und gitignoriert; (2) ein Plan/Handoff zitiert Resume-State nur über einen getrackten Pfad (z.B. Abschnitt "Umsetzungsstand" im Plan selbst) oder setzt `progress.checkpoint-dir` auf einen getrackten Ort; (3) Prozessregel C: Umsetzungsstand wird im **selben PR** wie die dokumentierte Phase committet, nicht in einem separaten offenen Branch; (4) Hinweis auf Warnung `progress.checkpoint-dir-ignored` und `--validate-spec-plan`.
- Planvorlage-Hinweis: ein Satz mit Verweis auf Regel C an der Stelle, die den Plan-"Umsetzungsstand" beschreibt (Ablage bei Implementierung zu lokalisieren: `rules/1-generic/spec-plan-workflow.md` Plan-Template; nicht verifiziert).

## Datenfluss

1. `--validate`: `_handle_validate` -> `check_checkpoint_dir_ignored(project_root, config)` -> `resolve_progress_paths` -> `run_git_check_ignore(<rel>, root)` -> rc 0 -> `ProgressPathFinding(warning)` -> `Finding(WARNING)` -> `print_report`, Exit-Code unberührt.
2. `--validate-spec-plan`: `validate_spec_plan` -> Plan-Dateien -> `check_checkpoint_references` -> pro Referenz Existenz- und `check-ignore`-Prüfung -> `Finding(ERROR)` -> Report, Exit 1.
3. Kein Git-Repo / Git fehlt: `run_git_check_ignore` -> `None` oder rc 128 -> Prüfung übersprungen, nichts geloggt, Exit-Code unberührt.

## Acceptance Criteria

- AC-1000-1: Given tmp-Git-Repo mit `.gitignore` `.meta-viz/` und ohne `progress`-Block, When `resolve_progress_paths(root)`, Then enthält `findings` ein Finding mit `code == "progress.checkpoint-dir-ignored"` und `level == "warning"`.
- AC-1000-2: Given dasselbe Repo mit `progress: {checkpoint-dir: docs/checkpoints}` (nicht ignoriert), Then kein `progress.checkpoint-dir-ignored`-Finding.
- AC-1000-3: Given tmp-Verzeichnis ohne `.git`, When `resolve_progress_paths(root)`, Then keine Exception, kein `*-dir-ignored`-Finding, kein Eintrag in `log.errors`/`log.warnings` (Entscheidung 43).
- AC-1000-4: Given Git nicht ausführbar (`run_git_check_ignore` liefert `None`, per Monkeypatch), Then wie AC-1000-3.
- AC-1000-5: Given tmp-Repo mit ignoriertem Default, When `python3 scripts/sync.py --validate` dort läuft, Then erscheint eine Zeile mit `progress.checkpoint-dir-ignored` und der Exit-Code ist unverändert 0.
- AC-1000-6: Given `plan.md`, die `.meta-viz/checkpoint-x.json` zitiert (Datei fehlt oder ignoriert), When `--validate-spec-plan`, Then Finding `checkpoint.reference-missing` bzw. `checkpoint.reference-ignored` und Exit 1.
- AC-1000-7: Given `plan.md`, die einen existierenden, nicht ignorierten Checkpoint-Pfad zitiert, Then kein Finding aus `check_checkpoint_references`.
- AC-1000-8: Given tmp-Verzeichnis ohne `.git` und `plan.md` mit zitiertem Checkpoint-Pfad, Then kein Finding aus `check_checkpoint_references`, keine Exception.
- AC-1000-9: `checkpointing.md` enthält die Begriffe "ephemeral" und "tracked", die Prozessregel "same PR" und den Verweis auf `progress.checkpoint-dir-ignored`; nach `python3 scripts/sync.py --dry-run` ist der Text in den generierten Orchestrator-Dateien (falls Checkpointing aktiv) sichtbar.
- AC-1000-10: Auf diesem Repo (`.gitignore:54`, kein `progress`-Block): `python3 scripts/sync.py --validate` meldet die Warnung `progress.checkpoint-dir-ignored` und endet mit Exit 0 (dokumentiert hingenommen, Entscheidung 55).
- AC-1000-11: `scripts/lib/progress_paths.py` und `scripts/lib/consistency/checkpoint_tracking.py` bleiben je <= 600 Zeilen und enthalten kein `print()`; `python3 -m pytest tests/test_checkpoint_tracking.py -q` und bestehende Checkpoint-/Progress-Tests bleiben grün.

Anzahl AC: 11. DoR-Zuordnung: Issue-1 -> AC-1000-1, -5, -6; Issue-2 -> AC-1000-9; Issue-3 -> AC-1000-1, -6 (Regressionstests in `tests/test_checkpoint_tracking.py`); Issue-4 -> AC-1000-9.

## Offene Fragen + Risiken

**Offene Fragen:** keine (Teilfrage `progress.checkpoint-dir` durch Entscheidung 55 beantwortet; Ausgabefläche in IC-2/IC-3 festgelegt).

**Risiken.**
- R1: Die Warnung `progress.checkpoint-dir-ignored` erscheint dauerhaft auf agent-meta selbst und in jedem Konsumentenprojekt mit Default-`.gitignore`-Block; hingenommen (Entscheidungen 8, 43, 55). Konsumenten können `progress.checkpoint-dir` umsetzen.
- R2: `git check-ignore` erkennt nur "ignoriert", nicht "untracked, aber nicht ignoriert". Ein neu erzeugter, nie committeter Checkpoint außerhalb einer Ignore-Regel wird von IC-3 nicht gemeldet. Mitigation später über `git ls-files --error-unmatch`; bewusst nicht in dieser Runde (kein Helfer vorhanden, Zusatzfläche).
- R3: Regex-Erkennung in IC-3 kann Prosa-Erwähnungen von Checkpoint-Dateien (z.B. in Doku-Beispielen) als Referenz werten und ERROR melden. Mitigation: Platzhalter mit `<`/`{{` ausgenommen; Beschränkung auf Plan-Dateien.
- R4: `check-ignore` je Verzeichnis ist ein Subprozess (Timeout 5 s in `io.py:543`); `resolve_progress_paths` läuft bei jedem `CheckpointStore.from_config`. Mitigation: Prüfung nur in `--validate` auswerten (Findings in `checkpoint.py:388` werden verworfen), Mehrkosten zwei Prozessstarts je Store-Konstruktion; bei Messung als Problem Prüfung in IC-2 verlagern.

## Entscheidungsverweise

8 (B+C), 43 (fail-soft ohne Git-Repo), 55 (Default `.meta-viz/` bleibt, Warnung hingenommen), 17 (ein Commit für Task 13), 38e (keine Closing-Keywords).

## Trace-Anker: spec-id: SPEC-1000-CHECKPOINT-TRACKING-2026-11-11
