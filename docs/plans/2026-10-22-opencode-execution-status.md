# Opencode-Pläne (#1006, #1007) — Ausführungsstatus

> Status: in Arbeit · Start 2026-10-22 · Orchestrator (Singleton), Ausführung nach Skill `plan-ledger`.
>
> Pläne: `docs/plans/2026-10-22-opencode-entrypoint-1006-plan.md` (Plan A) und
> `docs/plans/2026-10-22-opencode-v2-support-plan.md` (Plan B).
> Specs: `docs/specs/2026-10-22-opencode-entrypoint-1006-spec.md` (Rev. 1.4) und
> `docs/specs/2026-10-22-opencode-v2-support-spec.md` (Rev. 1.4).

## Freigabe

- Nutzerfreigabe 2026-10-22 (Auftrag: beide Pläne vollständig abarbeiten).
- Marker `Status: APPROVED (2026-10-22)` in beiden Specs (Frontmatter `status: APPROVED`) und beiden Plänen gesetzt.
- Gate-Commit: `chore: approve opencode 1006 and 1007 specs and plans`.

## Ausführungsmodell und Abweichungen

| ID | Abweichung | Begründung |
|---|---|---|
| P-1 | Parallelgruppen (`g1`, `c0-g1`, `b-g1`) werden **sequenziell** abgearbeitet; die Ownership-Disjunktheit wird vorher geprüft und dokumentiert. | Ein einziger Working Tree, `isolation: "worktree"` ist repo-weit verboten. Zwei Branches können nicht gleichzeitig ausgecheckt sein; parallele Commits würden den Git-Index serialisieren. Die Merge-Reihenfolge bleibt exakt wie im Plan. |
| P-2 | Phase C0 läuft auf eigenem Branch, wird aber **nach** Plan A gemergt (wie im Plan gefordert). Die „parallele" Ausführung zu Plan A entfällt aus demselben Grund wie P-1. | Merge-Reihenfolge A → C0 → B → C1/C2 → C3 → D. |
| P-3 | `provider-expert` existiert in diesem Repo nicht (Agent-Tabelle); die Spike-Tasks 2 und 24 laufen über `opencode-expert`. | Nächstliegende aktive Rolle; Rollen-Zuordnung des Plans wird nicht stillschweigend erfunden. |
| P-4 | Plan-Ledger-Checkboxen werden nach jedem Task durch den Orchestrator (bzw. `documenter`) gepflegt. | `plan_ledger.py`-Writer benötigt Shell; unter Opencode-Strict ist der Direktpfad gesperrt (Spec A R-2). |

## Test- und Verifikationskommandos (je Paket und am Ende)

```
python3 -m pytest tests -q
python3 scripts/sync.py --validate
python3 scripts/sync.py --check
python3 scripts/consistency-check.py
bash tests/scenarios/run.sh
python3 -m pytest tests/test_provider_agnostic_dispatch.py tests/test_ac01_render_identity.py -q
```

## Fortschritt

| Plan | Task | Status | Commit | Tests / Evidenz |
|---|---|---|---|---|
| A | Gate (Approval-Marker) | läuft | — | — |
| A | 1 Permission-Rangfolge | offen | — | — |
| A | 2 `explicit_primary_role` | offen | — | — |
| A | 3 `mode: primary` v1/v2 | offen | — | — |
| A | 4 Serializer | offen | — | — |
| A | 5 State `default-agent` | offen | — | — |
| A | 6 `default_agent`-Merge | offen | — | — |
| A | 7 Gate-Kopplung | offen | — | — |
| A | 8 Edit-Sperre | offen | — | — |
| A | 9 Config/Hint | offen | — | — |
| A | 10 Szenario 69 | offen | — | — |
| A | 11 AC-01-Rebaseline | offen | — | — |
| A | 12 Self-Sync | offen | — | — |
| A | 13 OQ-8-Amendment A2 | offen | — | — |
| A | 14 CHANGELOG | offen | — | — |
| A | 15 Nachzügler/Verifikation | offen | — | — |
| A | 16 Folge-Issue (nach Merge) | offen | — | — |
| B | C0 1–3a, 24 | offen | — | — |
| B | B 4–12 | offen | — | — |
| B | C1/C2 13, 13a, 14–17 | offen | — | — |
| B | C3 18–19 (nur bei GO) | offen | — | — |
| B | D 20–33 (ohne 24) | offen | — | — |

## Blocker / offene Befunde

- keine (Stand Start)
