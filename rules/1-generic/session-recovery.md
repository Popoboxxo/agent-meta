# Session-Recovery (Resume-Vorrang)

Verbindliches Vorgehen beim Session-Start, sobald der Spec/Plan-Workflow aktiviert ist
(`spec-plan-workflow.enabled`). Diese Rule wird nur ausgeliefert, wenn der Workflow aktiv
ist (Rule-Gate `session-recovery`, `requires: spec-plan-workflow.enabled`).

## Resume vor neuer Plan-Arbeit

- **Vor** jeder neuen Plan-Arbeit liest der Session-Start einen Resume-Kontext. Dafür wird
  ausschließlich der read-only rehydrate-Modus verwendet:
  `python3 scripts/sync.py --rehydrate` (`scripts/lib/rehydrate.py::rehydrate`).
- Der read-only Lauf schreibt **keine** Dateien. Er ermittelt den neuesten nicht
  abgeschlossenen Stand über `scripts/lib/recovery.py::find_resumable_session` und rendert
  ihn über `build_resume_context` / `render_resume_context`.
- Gibt es **keine** offene Session, wird das explizit als "no unfinished session" gemeldet;
  die Plan-Arbeit beginnt dann normal.
- Das Verhalten ist über `spec-plan-workflow.recovery.rehydrate` steuerbar; nur ein
  explizites `false` deaktiviert den Resume-Pfad.

## Autoritative Quelle

- Autoritative maschinelle Recovery-Quelle ist der `CheckpointStore`
  (`scripts/lib/checkpoint.py`) mit seinen Session-Dateien unter
  `.meta-viz/checkpoints/<session>.json`.
- Das manuelle Legacy-Format `.meta-viz/checkpoint-<ts>.json` bleibt **lesbar**
  (Abwärtskompatibilität), wird von der Runtime aber **nicht** geschrieben und **nicht**
  automatisch gelöscht.
- Es wird kein neues Ledger-/Recovery-Format eingeführt: Die Plan-Checkboxen bleiben die
  menschliche Sicht, der Checkpoint die maschinenlesbare Quelle.

## Offener Task: fortsetzen, nicht umsortieren

- Liegt ein offener Task vor, wird genau dort fortgesetzt, wohin `next_task_ref` zeigt.
- Der offene Task wird **nie stillschweigend übersprungen und nie umsortiert**.
- Ist `next_task_ref` nicht eindeutig auflösbar, wird die Session nicht fortgesetzt,
  sondern der unklare Stand bleibt offen und wird an den Menschen gemeldet (fail-closed).
- Der Resume-Kontext ändert nur den Wiedereinstieg, nie den Plan selbst.

## Abgrenzung

- Der Resume-Vorrang ist eine **Convention boundary**, keine Security boundary
  (Terminologie:
  `branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary`).
- Recovery ist read-only; Schreibzugriffe auf Store und Ledger liegen allein bei den
  dafür vorgesehenen Writer-Modi (`--checkpoint`, `--update-plan-ledger`).
