# Intent-Routing Eval — Baseline (separate artefact, P27 / Task 16)

---
status: DRAFT — NOT RUN
date: 2026-11-21
decision: "Nutzergo 21.11., Entscheidung 6: Eval-Baseline als SEPARATES Artefakt, keine Revision der APPROVED-Spec"
spec: docs/specs/2026-11-20-intent-routing-spec.md
plan: docs/plans/2026-11-14-intent-routing-table-plan.md (Block C, Task 16)
cost_estimate: .tmp/p27-task16-cost-estimate-2026-11-21.md
---

## Zweck

Dieses Dokument ist der vorgesehene Ablageort für die Ergebnisse des
kostenpflichtigen Routing-Eval-Laufs (Plan Task 16). Es ist bewusst **getrennt**
von der freigegebenen Spec `docs/specs/2026-11-20-intent-routing-spec.md`
(Entscheidung 6, 21.11.) — die APPROVED-Spec wird nicht verändert.

## Stand

- **Kein Eval-Lauf ausgeführt.** Kein LLM-Aufruf, keine Gemini-Probe.
- Kostenschätzung und exakter Befehl liegen in
  `.tmp/p27-task16-cost-estimate-2026-11-21.md`.
- Freigabe: **offen** — Entscheidung 7 verlangt Kostenschätzung + ausdrückliches
  „Ja" des Nutzers vor dem Lauf.

## Messaufbau (vorgesehen)

| Feld | Wert |
|---|---|
| Katalog (Entscheidung 1) | `tests/routing-llm-eval/roles/catalog.generated.yaml` (altes `roles/`-Layout, 613 Fälle) |
| Trocken-Listing (Entscheidung 5) | `python3 tests/routing-llm-eval/list_cases.py …` — kein `--dry-run` in `run_eval.sh` |
| Kollisionsprüfung | Generator-Report: 9 Overlap-Tokens, 45 Kollisionsfälle (siehe unten) |
| Provider | `claude` (Haiku-Klasse), `REPEAT=1`; kein Gemini (5.1/#860 blockiert) |
| Befehl | `cd tests/routing-llm-eval && REPEAT=1 ./run_eval.sh --provider claude` |
| Kosten | ≈ $0.21 (142 Fälle, Ist-Befehl) bzw. ≈ $0.92 (613 Fälle, Obergrenze) — E-27: < 1 USD |

## Kollisionsprüfung (Entscheidung 2, bereits ausgeführt)

Der Generator liest jetzt `routing.triggers` (P26) als Primärquelle mit
`routing_patterns`-Fallback. `--report-collisions` meldet **9 Overlap-Tokens**
mit **45 Kollisionsfällen** (je Token: ein `ASK`-Fall plus je ein
disambiguuierter Fall pro Rolle). Tokens: `a11y`, `accessibility`,
`architektur`, `audit`, `design`, `post-mortem`, `refactoring`, `schema`,
`se leaf` — exakte Liste per
`python3 scripts/gen_role_routing_eval_catalog.py --report-collisions`.

Der Katalog bleibt byte-identisch (Generator `--check` = up to date), daher
ist kein Rebaseline nötig.

## Ergebnis-Tabelle (nach Freigabe zu füllen)

| Metrik | Wert | Beleg |
|---|---|---|
| Fälle / Läufe | — | — |
| Trefferquote (exakt) | — | — |
| Fehlrouten | — | — |
| Flaky-Fälle | — | — |

Fehlrouten werden nach Nutzerfreigabe als Issues erfasst — keine
Daten-Hotfixes im selben Change (Plan Task 16).
