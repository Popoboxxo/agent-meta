# Opencode-Pläne (#1006, #1007) — Ausführungsstatus

> Status: Plan A abgeschlossen (Tasks 1–15), Task 16 nach Merge offen · Start 2026-10-22 · Orchestrator (Singleton), Ausführung nach Skill `plan-ledger`.
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
| A | Gate (Approval-Marker) | done | `1b40143e` | Approval-Marker in beiden Specs und beiden Plänen |
| A | 1 Permission-Rangfolge | done | `7ae1bbb1` | Verdikt `CONFIRMED_BY_DOC` (Doku-Delegation + Binary-Belege, Pfad-Semantik lokal belegt) — Gate für Task 8 erfüllt |
| A | 2 `explicit_primary_role` | done | `60171d9e` | `tests/test_explicit_primary_role.py` 7 passed |
| A | 3 `mode: primary` v1/v2 | done | `35078885` | `test_transform_contracts.py` (v1/v2-Promotion) grün; Mammouth bleibt ohne `primary-role` Subagent |
| A | 4 Serializer | done | `62916e9c` | Charakterisierung `test_agents_frontmatter.py` grün (keine Serializer-Änderung nötig) |
| A | 5 State `default-agent` | done | `bfc11d2f` | `tests/test_opencode_runtime_gate.py` 14 passed (9 + 5) |
| A | 6 `default_agent`-Merge | done | `94ef7b86` | 10 neue Tests (24 in der Datei); Idempotenz, Rollback und Nutzerwert-Schutz belegt |
| A | 7 Gate-Kopplung | done | `75148fd0` | `tests/test_runtime_gate_wiring.py` 12 passed; Gate-Deny nur mit explizitem Einstiegspunkt |
| A | 8 Edit-Sperre | done | `b5ec0e4d` | `tests/test_opencode_primary_edit_lock.py` 8 passed (AC-11, Scoped-Deny) |
| A | 9 Config/Hint | done | `caf73143` | `tests/test_orchestrator_hint_flag.py` grün; `primary-role`-Kommentar + Hint ohne `@orchestrator` |
| A | 10 Szenario 69 | done | `e91736fd` | Szenario `69-opencode-v2-surface` PASS (v1: `default_agent` + `mode: primary`) |
| A | 11 AC-01-Rebaseline | done | `357dd389` | 2 changed + 1 added (nur `Opencode/…`); `slimming-golden/`/`compact-golden/` unverändert |
| A | 12 Self-Sync | done | `e5d5d038` | `--validate` rc 0, zweiter Lauf idempotent; P-5: `.opencode/` ist gitignored → nur `opencode.json` + Hash-Manifest committet |
| A | 13 OQ-8-Amendment A2 | done | `209d8175` | Amendment A2 + Querverweise in drei Specs; `--validate` rc 0 |
| A | 14 CHANGELOG | done | `262ce72a` | `### Fixed` unter `## [Unreleased]`, kein Version-Bump |
| A | 15 Nachzügler/Verifikation | done | `88517839` | 6251 passed / 24 skipped / 0 failed, 78/78 Szenarien PASS, `--validate`/`--check` rc 0, AC-01 5 passed, provider-agnostisch 71 passed, Mammouth-Diff 0 |
| A | 16 Folge-Issue (nach Merge) | offen | — | startet erst nach dem Merge von Plan A (Gate in Task 16); blockiert den PR-Hand-off nicht |
| B | C0 1–3a, 24 | offen | — | — |
| B | B 4–12 | offen | — | — |
| B | C1/C2 13, 13a, 14–17 | offen | — | — |
| B | C3 18–19 (nur bei GO) | offen | — | — |
| B | D 20–33 (ohne 24) | offen | — | — |

## Blocker / offene Befunde

Keine offenen Blocker für Plan A. Akzeptierte Review-Abweichungen (Tasks 1–15):

- **P-5 — `.opencode/` ist gitignored:** Task 12 hat deshalb nur `opencode.json` und das
  Hash-Manifest committet (`e5d5d038`); die generierten Agent-Dateien unter `.opencode/` sind nicht
  versioniert. Der Einstiegspunkt ist über `opencode.json` (`default_agent`) und den
  Manifest-Eintrag belegt; die Agent-Datei wird bei jedem Sync neu erzeugt.
- **D-2 — Hint-Formulierung:** Der `orchestrator_hint` wurde sinngemäß statt wörtlich umgesetzt
  (Default-Agent wird benannt, `@orchestrator` entfällt). Der Test prüft auf `Default` und die
  Abwesenheit von `@orchestrator`, nicht auf den exakten Satz.
- **D-3 — AC-01-Drift-Lauf 2:** Der zweite Drift-Lauf verfehlte die Erwartung „exakt 3 Zeilen“
  (Zähl-/Reihenfolgeabweichung der Drift-Liste). Die inhaltliche Diff-Prüfung bestätigte exakt
  2 geänderte + 1 hinzugefügter Hash; die Rebaseline wurde daher nicht blind geschrieben, sondern
  nach Diff-Review (`357dd389`).

**Review-Verdikte:** Task 1 trägt `CONFIRMED_BY_DOC` (Gate für Task 8 damit erfüllt), Task 4 ist
als Charakterisierung grün. Die Reviews der Tasks 2–15 meldeten keine blockierenden Befunde; die
Doku-Befunde RVW-A1-1 (Ledger), RVW-A2-7 (Statusdokument), RVW-A1-3 (`Verdikt:`-Gate),
RVW-A1-4 („v1 byte-frozen“-Kommentar) und RVW-A1-6 (Spec weiter „Entwurf“) sind mit diesem
Doku-Update erledigt. Restrisiko R-1/R-2 (Rangfolge ohne End-to-End-Probe, Pfad-Semantik) bleibt
als markierte Unsicherheit im Evidenzdokument bestehen.
