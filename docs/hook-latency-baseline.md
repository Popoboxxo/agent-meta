# Hook latency baseline (#1169)

Measurement date: 2026-11-20. Tool: `python3 scripts/bench_hooks.py --runs 5 --json`
(Task 6). Spawn counts come from a PATH shim that counts `python3`/`python`
invocations; timings are diagnostic only and are never asserted in CI (#1116).

## Before the single-parse refactor

The pre-refactor count is **static**, from the approved spec
`docs/specs/2026-11-11-hook-single-parse-spec.md` §1.1 (measured at worktree
`wt-phase-d1`, 2026-11-13): 9 Python starts on the guard's Bash path — probe,
JSON validation, four field reads, sentinel parse, git scan, strict config.
Issue #1169 additionally records audit measurements of ~0.35 s for the
orchestrator-guard Bash path (means of 5 runs, 2026-11-06).

## After (this branch)

| Payload | median_ms | p95_ms | python_spawns |
|---|---:|---:|---:|
| `bash-simple` | 316.5 | 452.8 | **5** |
| `read-simple` | 233.2 | 249.3 | 2 |

`bash-simple` now starts **5** interpreters instead of the statically counted
9 (−4), reaching the spec's plan value of ≤ 5. The remaining starts are the
JSON probe, the one multi-field parse, the sentinel regex, the git scan and the
strict-config read; they are deliberately separate programs (spec §1.3).

Latency figures were taken on the development machine under load; they are
context for the spawn reduction, not a performance regression gate.
