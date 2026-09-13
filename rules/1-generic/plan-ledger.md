# Plan-Ledger und Ausführung

Verbindliches Vorgehen bei der taskweisen Ausführung eines approvten Plans.
Normativ nur bei aktiviertem Spec/Plan-Workflow.

## Frischer Subagent pro Task

- Jeder Task wird von einem **frischen Subagenten** mit frischem Kontext ausgeführt.
- Der Handoff enthält: Task-ID, Spec-/Plan-Referenz, exakte Datei-Ownership
  (`Files:`), Interfaces (`Produces`/`Consumes`) und Akzeptanzkriterium.
- Nach dem Task folgt ein **zweistufiges Review**, bevor der nächste Task startet;
  die Ergebnisse fließen in den Ledger:
  1. **Stufe 1 — Requirement-Treue** (Pipeline-Stage `review-req`, Reflection-Pair
     `task-req-review-loop`): Prüfung gegen die Akzeptanzkriterien des Tasks — **vor**
     der Qualitätsprüfung.
  2. **Stufe 2 — Qualität** (Pipeline-Stage `review-quality`, Reflection-Pair
     `task-quality-review-loop`): Code-Qualität und Blast-Radius.
- Beide Stufen laufen als Loop mit je `max_iterations: 2`. Der aggregierte Runden-Cap
  `task-review.max-rounds: 4` (Pipeline-Override in `config/role-defaults.yaml`)
  begrenzt die Gesamtzahl der Review-Runden; ist der Cap erreicht, wird **nicht** weiter
  iteriert, sondern der Stand bleibt offen und wird an den Menschen gemeldet.
- Das Routing bleibt ausschließlich deklarativ in `config/role-defaults.yaml`
  (`quality_pipelines`/`reflection_pairs`); diese Rule nennt nur Stage-/Pair-IDs.

## Ledger

- Der **Ledger ist die Plan-Datei selbst**: Checkboxen (`- [ ]` / `- [x]`) sind die
  menschlich lesbare Sicht auf den Fortschritt.
- Zusätzlich wird der Task-Fortschritt an die bestehende Recovery-Infrastruktur
  gebunden: `CheckpointStore` (`scripts/lib/checkpoint.py`) über
  `barrier.checkpoint_ref` (z. B. `.meta-viz/checkpoints/...` — illustratives
  Beispiel). Die Checkpoint-Wurzel ist über `progress.checkpoint-dir`
  konfigurierbar, der Progress-Dateipfad über `progress.dir`; `.meta-viz/checkpoints`
  bzw. `.meta-viz/progress` sind nur die Framework-Defaults (Top-Level-`progress`-Block
  in `.meta-config/project.yaml`).
- **Writer-Pflicht statt reiner Handarbeit:** Der Checkbox-Zustand wird nach jedem Task
  vom Ledger-Writer (`scripts/lib/plan_ledger.py`, Modus `--update-plan-ledger`)
  geschrieben; die manuelle Pflege ist nur der Fallback. Der geschriebene Zustand muss
  exakt der `parse_plan_ledger`-Semantik entsprechen.
- `execute_plan` (IC-06) schreibt zusätzlich pro Entry einen Checkpoint und schließt den
  Ledger über `ledger_path` ab (nur `success`-Entries; Ledger-Fehler sind fail-soft).
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
- `max-parallel-agents` bleibt die Obergrenze der Parallelität.
- `execute_plan` ist verdrahtet (IC-06): Es schreibt pro Entry einen Checkpoint
  (`checkpoint_from_barrier_entry`, Identität nur aus explizitem `plan_id`) und schließt
  über `ledger_path` den Plan-Ledger ab. **Nur** der G-08-Dispatcher-Backend
  (automatischer In-Harness-Dispatch) bleibt out-of-scope.

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
  - `auto` → Stage `archive`; `archive.agent` ist Config-Wert, ausgeführt über die Pipeline. Kein direkter Dispatch.
  - `ask` → Rückfrage; erst nach Zustimmung archivieren.
  - `off` → nichts.
- `archive.agent`: `documenter` (Default, KE-unabhängig) bzw. `knowledge-ingestor` bei
  KE-Route (`index.mode: knowledge-engine`).
- Die Archivierung erfolgt **agentenbasiert** — ein **Sync-Schritt** zur Archivierung ist
  explizit **Nicht-Ziel** (F11).

**Routing:** Ich dispatche nicht selbst. `archive.agent` ist ein Config-Wert und wird
über die Pipeline ausgeführt.
