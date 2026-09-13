# Plan-Ledger und Ausführung

Verbindliches Vorgehen bei der taskweisen Ausführung eines approvten Plans.
Normativ nur bei aktiviertem Spec/Plan-Workflow.

## Frischer Subagent pro Task

- Jeder Task wird von einem **frischen Subagenten** mit frischem Kontext ausgeführt.
- Der Handoff enthält: Task-ID, Spec-/Plan-Referenz, exakte Datei-Ownership
  (`Files:`), Interfaces (`Produces`/`Consumes`) und Akzeptanzkriterium.
- Nach dem Task folgt ein **Review**, bevor der nächste Task startet. Ergebnisse
  fließen in den Ledger.

## Ledger

- Der **Ledger ist die Plan-Datei selbst**: Checkboxen (`- [ ]` / `- [x]`) sind die
  menschlich lesbare Sicht auf den Fortschritt.
- Zusätzlich wird der Task-Fortschritt an die bestehende Recovery-Infrastruktur
  gebunden: `CheckpointStore` (`scripts/lib/checkpoint.py`) über
  `barrier.checkpoint_ref` (z. B. `.meta-viz/checkpoints/...`).
- **Kein neues Ledger-Format:** Checkbox-Zustand ist die menschliche Sicht, der
  Checkpoint die maschinenlesbare Recovery-Quelle. Nach einem Abbruch wird aus dem
  Checkpoint wieder aufgesetzt.

## Ownership und Barrieren

- Datei-Ownership pro Task kommt aus dem `Files:`-Block des Plans.
- Vor paralleler Ausführung wird die Ownership-Disjunktheit mit
  `check_plan_file_overlap` (`scripts/lib/orchestration.py`, aufbauend auf
  `check_file_overlap`) geprüft. Nur **ownership-disjunkte** Tasks laufen parallel.
- Der Task-Graph stützt sich auf `FanoutPlan`/`validate_plan`; Zyklen und Overlaps
  im `parallel_group` sind Fehler.
- `max-parallel-agents` bleibt die Obergrenze der Parallelität. `execute_plan` bleibt
  out-of-scope — eingebunden wird nur der Graph-Validator.

## Worktree-Verbot (Adaption)

- **Niemals** das Argument `isolation: "worktree"` beim Spawnen von Subagenten
  verwenden (siehe `no-worktree-isolation`). Worktree-Isolation wird im Spec/Plan-
  Workflow **nicht** genutzt.
- Der Ersatz ist kein Worktree, sondern die Kombination aus **expliziter Ownership +
  Barrieren + Checkpoint-Ledger**.
- Repo-Containment bleibt unangetastet: Schreiben nur im Projektroot und in `.tmp/`.

## Archiv-Trigger

- Trigger `archive.trigger: plan-complete`: **alle Checkboxen gesetzt** UND der Plan ist
  **gemergt** (F5).
- Die Merge-Erkennung ist **rein manuell**: Der Orchestrator/das Team bestätigt den
  Merge-Status, bevor archiviert wird. Es gibt **keine** automatische Merge-Erkennung und
  **keine** Provider-Abstraktion.
- Ziel `archive.target` (Default `docs/plans/archive`, Basis `{{SPEC_PLAN_PLANS_DIR}}/archive`).
  Die bestehende Konvention des Plan-Verzeichnisses bleibt maßgeblich.
- Modus `archive.mode`:
  - `auto` → `orchestrator` delegiert an `archive.agent`; Spec + Plan verschieben, loggen.
  - `ask` → Rückfrage; erst nach Zustimmung archivieren.
  - `off` → nichts.
- `archive.agent`: `documenter` (Default, KE-unabhängig) bzw. `knowledge-ingestor` bei
  KE-Route (`index.mode: knowledge-engine`).
- Die Archivierung erfolgt **agentenbasiert** — ein **Sync-Schritt** zur Archivierung ist
  explizit **Nicht-Ziel** (F11).
