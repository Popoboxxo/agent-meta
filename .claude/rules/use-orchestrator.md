# Main-Chat Mode
Main Chat ist Router + Worker. Kein Orchestrator-Subagent. Du bist der Orchestrator!

## Intent Routing
> Parallel ist rein informativ — kein Runtime-Enforcement, nur CI-Konsistenzcheck bei required/recommended-Tier-Abdeckung.

**Tiers** (nicht gelistet = optional): recommended: `bug-feature-analyzer`, `code-reviewer`, `documenter`, `planner`, `requirements`, `tester`, `validator` | required: `developer`, `feedback`, `git`, `log-analyzer`, `orchestrator`

| Intent / Keywords | Agent | Tier | Parallel |
|-------------------|-------|------|----------|
| Bug fixen, Bug beheben, Fehler beheben | → Pipeline: `bugfix` | pipeline | no |
| Konzept, Design-Doc, Architektur-Recherche, Trade-offs | → Pipeline: `concept-development` | pipeline | no |
| concept-driven-dev, Konzept-Pipeline, gegen Spezifikation implementieren, spec-first | → Pipeline: `concept-driven-dev` | pipeline | no |
| Dokumentation, README, Docs, Doku | → Pipeline: `docs-update` | pipeline | no |
| Feature implementieren, Feature bauen, neues Feature, Funktion bauen, Feature Lifecycle, komplexes Feature, Feature Pipeline | → Pipeline: `feature-lifecycle` | pipeline | no |
| Bug fixen, Bug beheben, Triage, schneller Fix, Hotfix | → Pipeline: `quick-fix` | pipeline | no |
| Refactoring, aufräumen, Cleanup, Code verbessern | → Pipeline: `refactor` | pipeline | no |


Volle Stage-Details (Agent/Modus je Stage, Loop/Fallback/Approval-Gate) einer gematchten Pipeline bei Bedarf: `Read .claude/pipeline-details/<pipeline-name>.md`.

## A2A Delegation
A2A-Envelopes nur für Routen mit schema-gebundenem Contract (role-defaults.yaml handoff.input_schema/output_schema zeigt auf eine echte Datei) — sonst normales Klartext-Delegationsformat: IPayload (t, ctx, con, refs, pri, dep), IEnvelope (protocol_version, handoff_id, source_agent, target_agent, schema_ref, payload). payload.t ≤ 300 Zeichen.

## Status-Tabelle (Pflicht, Issue #678)

Nach jedem Abschluss eines Batch-Mitglieds (FANOUT/PARALLEL_GROUP) und spätestens
bei jedem BARRIER-Punkt eine kompakte Status-Tabelle ausgeben — nicht erst am Ende
der gesamten Pipeline/Session.

| Agent | Task | Status |
|-------|------|--------|
| `<agent>` | `<Ein-Satz-Task>` | `pending` \| `in_progress` \| `done` \| `failed` |

- Eine Zeile pro Batch-Mitglied, in Dispatch-Reihenfolge.
- `Status` wird bei jedem eingehenden Tool-Ergebnis aktualisiert, nicht erst am Ende gesammelt.
- Ersetzt NICHT die BARRIER-Zusammenfassung — sie ist der sichtbare Zwischenstand
  während des laufenden Batches, kein Duplikat.


## Plan Delegation
Plan vorhanden (`plan-*.md` oder Knowledge-Wiki Plan-Seite) -> Pipeline `feature-lifecycle` mit `payload.plan_ref`, statt neuen Lifecycle blind zu starten.

## Git Delegation
Git Mutationen (commit, push, add etc) -> `git` Agent. Read-only (status, log) im Main Chat ok.
Ausnahme auf User-Wunsch erlaubt.

Native Extensions (Skills/Hooks) erlaubt, ignorieren nicht Branch-Guard/DoD.

