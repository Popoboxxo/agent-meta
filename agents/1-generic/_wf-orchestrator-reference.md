# Orchestrator — Referenz (Lazy-Load)

> Auslagerung aus `orchestrator.md` zur Token-Reduktion. Der Orchestrator liest
> diese Datei **nur bei Bedarf** — nicht Teil des Standard-Kontexts.
>
> Pfad im Zielprojekt: `.agent-meta/agents/1-generic/_wf-orchestrator-reference.md`
>
> `_`-Präfix → wird von `sync.py` nicht als Agent generiert (Konvention wie
> `_wf-sync-interface.md`).

## Few-Shot Patterns

| Pattern | Vorgehen |
|---------|----------|
| Single Feature | `feature` oder Pipeline: git→req→test→dev→test→review→doc→git |
| Plan vorhanden | planner→feature(plan_ref=<path>) |
| Multi-Bug Fix | FANOUT(N, developer) → BARRIER → git |
| Mixed Tasks | PARALLEL_GROUP(dev, tester) → BARRIER → review → git |
| Refactoring | explorer→dev→tester→review→git |
| Analysis + Design | PARALLEL_GROUP(explorer, ideation) → BARRIER |
| Unknown Intent | Klärende Frage → Fallback |

## Delegation Failure Recovery

| Fehler | Reaktion |
|--------|----------|
| Permission/Unavailable | User informieren, Alternativen nennen |
| Timeout | Max. 1 Retry, dann User |
| Out-of-scope | Intent neu klassifizieren |
| Multi-Failure | Sequentiell, User informieren |
| Ambiguous | 1x Retry, dann User |
| Partial | User entscheiden lassen |

Nach 2 Fehlern für selben Intent → User um Klärung bitten.
