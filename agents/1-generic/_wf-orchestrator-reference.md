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
| Single Feature | Pipeline `feature-lifecycle`: git→req→test→dev→test→review→doc→git |
| Plan vorhanden | planner→feature-lifecycle(plan_ref=<path>) |
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

## Summarization-as-a-Contract

**Rationale (issue #267):** Each worker returns ONLY its compact summary — the
STATUS/RESULT/ARTIFACTS block. The orchestrator context is the scarce resource, so raw
output (logs, diffs, verbose tool output) is archived under
`.meta-viz/checkpoints/<session-id>/` via `CheckpointStore.save_raw_output` and comes
back as a `checkpoint_ref` pointer. Never re-request raw output into the context to
"double-check" — read the referenced file only when details are actually needed.

**Checkpoint format:** the `Full output: <checkpoint_ref>` lines are pointers into the
archived raw output — follow the reference instead of re-requesting. The
orchestrator-facing barrier entry carries the bounded 2–3 sentence `summary` plus its
`checkpoint_ref`; the full raw body stays in the archive.

**Harness enforcement (issue #265):** `scripts/lib/orchestration.py` persists
`raw_output` via `CheckpointStore.save_raw_output` and clears it from the entry
(`BarrierEntry` carries `summary` + `checkpoint_ref` only), so raw output is never
re-rendered into the orchestrator context.
