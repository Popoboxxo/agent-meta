# Snippet-Pre-Flight-Audit (RVW-20)

> Status: abgeschlossen
> Trace-Anker: `spec-id: SPEC-dynamic-routing-template-slimming`
> Plan-Task: Task 2 (Snippet-Pre-Flight-Audit, RVW-20) — Ziel-AK A6
> Datum: 2026-09-19
> Branch: `feat/dynamic-routing-template-slimming`

## Zweck

Bestandsaufnahme des Route-Guard-Detektors über den Snippet-Korpus **vor** der in A6
geplanten Scope-Erweiterung auf `snippets/**/*.md` (Route-Guard lebt ausschließlich in
`config/role-defaults.yaml`; Templates, Rules **und Snippets** dürfen keine `T-*`-Konstrukte
enthalten). Der Test selbst und sein Bestands-Scope bleiben unverändert — dieser Report ist
die read-only Vorbedingung für A6.

## Methode (read-only)

- **Detektor-Quelle:** `tests/test_no_role_routes_in_templates.py`
  (`classify_line`, `boundary_lines`, `find_findings`, `load_roles`, `load_pipeline_ids`).
  Verwendet wurden exakt die Detektoren `T-ROUTE-COL`, `T-ROLE-ARROW`, `T-HANDOFF`, `T-NEXT`
  plus die Ausnahmen `D-BOUNDARY`, `D-REFERENCE`, `D-PIPELINE`, `D-NONROLE`,
  `D-ESCALATION`, `D-ORCHESTRATOR`.
- **Trockenlauf:** Das Test-Modul wurde importiert und die Modulkonstante `_SCOPE_GLOBS`
  ausschließlich **in-memory** auf `("snippets/**/*.md",)` umgestellt; anschließend
  `find_findings()` plus eine vollständige Zeilenklassifikation über alle 13 Snippets.
  Es wurden keine Dateien geschrieben außer diesem Report.
- **Datenbasis:** `config/role-defaults.yaml` → 84 Rollen, 16 Pipeline-/Pair-IDs.
- **Snippet-Korpus (13 Bestands-Dateien):**
  `snippets/developer/{browser-verification,bun-typescript,language-best-practices,pytest-python}.md`,
  `snippets/orchestrator/{a2a-protocol,checkpointing,quality-pipelines,se-mode,status-table}.md`,
  `snippets/prompt-modernization/a2a-handoff-block.md`,
  `snippets/security/prompt-injection-defense.md`,
  `snippets/tester/{bun-typescript,pytest-python}.md`.

## Ergebnis: 4 Detektor-Treffer, 0 Verstöße

Alle 4 Treffer sind durch `D-NONROLE` belegt (Pfeil verbindet **keine** zwei Rollen-Tokens).
Es gibt **0 nicht-exempte Treffer** (`uncovered_total = 0`).

| # | Datei:Zeile | Konstrukt | Match (Token A → Token B) | Ausnahme | Beleg |
|---|---|---|---|---|---|
| 1 | `snippets/orchestrator/se-mode.md:4` | `T-ROLE-ARROW` | `L0` → `L` (aus `L{{SE_MAX_DEPTH}}`) | `D-NONROLE` | Level-/Platzhalter-Tokens, keine Rollen |
| 2 | `snippets/orchestrator/se-mode.md:22` | `T-ROLE-ARROW` | `continue` → `neuer` | `D-NONROLE` | Zustandsübergang `termination`=`continue`, keine Rollen |
| 3 | `snippets/orchestrator/se-mode.md:23` | `T-ROLE-ARROW` | `leaf` → `Component` | `D-NONROLE` | Termination-Zustand → Artefakttyp, keine Rollen |
| 4 | `snippets/orchestrator/se-mode.md:41` | `T-ROLE-ARROW` | `L0` → `Ln` | `D-NONROLE` | V-Model-Level-Bereich, keine Rollen |

Keiner der beteiligten Tokens (`L0`, `L`, `Ln`, `continue`, `neuer`, `leaf`, `Component`)
ist in der Rollen-Menge aus `config/role-defaults.yaml` enthalten — `D-NONROLE` greift daher
regelkonform, nicht durch eine Scope-Lücke.

**Detektoren ohne Treffer:**

| Detektor | Treffer im Snippet-Scope |
|---|---|
| `T-ROUTE-COL` | 0 |
| `T-HANDOFF` | 0 |
| `T-NEXT` | 0 (siehe Hinweis unten) |

**T-NEXT-Hinweis:** `T-NEXT` ist im aktuellen Test ausschließlich für die Dateien in
`_WORKFLOW_FILES` aktiv. Kein Snippet ist dort gelistet, daher ist der Detektor im
Snippet-Scope strukturell inert. Eine zusätzliche Probe mit erzwungenem
`workflow_file=True` über alle 13 Snippets lieferte ebenfalls **0 Treffer** — es gibt also
auch keine latenten `NEXT: [...]`-Rollenlabels.

### Abweichung zur Spec-Vorerwartung (RVW-20)

Der Spec-Vorab-Grep erwartete zusätzlich Pfeil-Konstrukte in
`snippets/orchestrator/a2a-protocol.md` (`[task] → [agent]`). Der reale Detektor klassifiziert
diese Zeile **nicht** als `T-ROLE-ARROW`, weil die Token-Klasse
`[A-Za-z0-9_-]+` die umschließenden Klammern `[`/`]` nicht erfasst und die Lookarounds
`(?<![A-Za-z0-9_-])`/`(?![A-Za-z0-9_-])` ein Ansetzen unmittelbar vor/nach `[`/`]`
verhindern. Es entsteht dadurch **kein** ungedeckter Treffer; die Spec-Beobachtung ist
lediglich konservativer als der Detektor.

## Konsequenz

- **Keine Umschreibung erforderlich.** Die beiden in Task 2 als optional-modify gelisteten
  Dateien `snippets/orchestrator/se-mode.md` und `snippets/orchestrator/a2a-protocol.md`
  bleiben **unverändert** (`git diff` leer, `git status` sauber unter `snippets/`).
- Damit ist die in A6 geforderte Vorbedingung erfüllt: der Snippet-Korpus ist
  guard-konform, die Scope-Erweiterung kann ohne Detektor-Abschwächung erfolgen.
- **Auflage für Task 10:** die neuen Block-Snippets `snippets/agents/{parse-input,output-guard,background-process-guard}.md`
  existieren zum Audit-Zeitpunkt noch nicht. Sie müssen beim Anlegen ebenfalls frei von
  `T-*`-Konstrukten bleiben (der neue Test `tests/test_route_guard_snippets.py` deckt dies ab).

## Verifikation

| Check | Kommando | Ergebnis |
|---|---|---|
| Bestands-Scope weiter grün | `python3 -m pytest tests/test_no_role_routes_in_templates.py -q` | 10 passed |
| Snippet-Korpus unverändert | `git diff --stat -- snippets/` | leer |
| Dry-Run Snippet-Scope | in-memory `_SCOPE_GLOBS = ("snippets/**/*.md",)` | 4 Treffer, **0 uncovered** |

## Akzeptanz-Mapping (Plan Task 2)

- [x] Report enthält **0 nicht-`D-NONROLE`-belegte Treffer**.
- [x] Keine Detektoränderung; kein nicht-exempter Treffer, daher keine Snippet-Umschreibung.
- [x] Beide genannten Snippet-Dateien unverändert.
- [ ] Commit via `git`-Agent: `chore(guard): preflight snippet corpus for route guard scope`
      — offen (laut Task-Vorgabe kein Commit durch den Developer).

## Blocker

Keine. Alle Treffer liegen innerhalb der Task-2-Ownership (Snippet-Korpus); es waren keine
Änderungen außerhalb der Ownership nötig.
