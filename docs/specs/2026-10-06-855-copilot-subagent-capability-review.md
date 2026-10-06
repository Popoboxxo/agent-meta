---
spec-id: SPEC-855-COPILOT-SUBAGENT-CAPABILITY-2026-10-06
review-of: docs/specs/2026-10-06-855-copilot-subagent-capability.md
reviewer: concept-reviewer
date: 2026-10-06
verdict: APPROVED
---

# Spec Review — Copilot Subagent-Dispatch Capability Correction

## Scope

Independent spec-review (workflow §8, spec-review mode) of the mini-spec for issue
#855 part 2. Pinned change: two capability keys in the Copilot block of
`config/provider-capabilities.yaml` (`subagent_dispatch: false → true`,
`native_agent_tools: [] → ["agent"]`) plus an explanatory comment and one
`special_notes` bullet. Reviewer re-verified every load-bearing claim against the
live repo.

## Verification of the spec's load-bearing claims

| # | Claim | Result |
|---|-------|--------|
| 1 | `has_native_subagent_dispatch()` has no caller in the sync pipeline → zero generated diff | CONFIRMED. Repo-wide grep: definition only at `scripts/lib/delegation_syntax.py:590`; remaining hits are `docs/CODEBASE_OVERVIEW.md` (API table) and this spec. No call site in `scripts/`. Pure capability-matrix metadata. |
| 2 | `subagent_permissions.py` does not fire for Copilot | CONFIRMED (two independent reasons). `check_subagent_permission_support` loops only over `resolve_providers(...)` = `[Claude, Opencode, Gemini]` — Copilot is not active. Even if active, line 83 `continue`s unless effective mode is `strict`; `.meta-config/project.yaml` has no `subagent_permissions` block at all → resolves to `off`. No-op before and after. |
| 3 | `fanout_contracts.py:239` does not fire | CONFIRMED. The `fanout.tool-surface-missing` ERROR gates only `mechanism in ("tool-mediated","swarm")`. Copilot keeps `fanout_mechanism: sequential-fallback` (line 210), so a now-non-empty `native_agent_tools` is accepted but not required. No new finding. |
| 4 | The 4 cited tests do not hardcode Copilot's `false`/`[]` | CONFIRMED. `test_delegation_syntax.py:291` `"Copilot": ("sequential-fallback", False, False)` is the FANOUT matrix `(mechanism, parallel, barrier)` — none of which this spec changes. `test_orchestration_contract.py:742` `("Copilot", False)` is the parallel-capability flag (unchanged). `test_provider_three_file_invariant.py:88` is error-message text. `test_subagent_permissions_consistency.py` has no Copilot reference. No test asserts `subagent_dispatch`/`native_agent_tools` for Copilot → no test edits needed, all keep passing. |
| 5 | Interface-contract line cites are accurate | CONFIRMED. Copilot block spans 191-214; `subagent_dispatch` at 196, `native_agent_tools` at 204, `description` at 212, `special_notes` at 213-214. Matches the spec's "Before" exactly. |

## Findings

No critical / major findings. Mandatory spec sections (§8) all present and
substantive: Problem/Ziel/Nicht-Ziele, Interface Contracts, Datenfluss,
Acceptance Criteria, Offene Fragen + Risiken, Test Plan, Trace-Anker. Trace anchor
`spec-id: SPEC-855-COPILOT-SUBAGENT-CAPABILITY-2026-10-06` set and referenceable.
Status marker `Entwurf` consistent with frontmatter `proposed`. No unresolved
placeholders (no TODO/TBD/`<...>`/`{{...}}`) in mandatory sections.

### Dimension 7 (Consistency) — the "dispatch:yes but fanout unspecified" question

Judged NOT a risk. `subagent_dispatch` and `fanout_mechanism` are orthogonal:
the former asserts "a named subagent can be dispatched via the `agent` tool", the
latter asserts a *verified parallel + barrier* contract. Declaring
`subagent_dispatch: true` while keeping `fanout_mechanism: sequential-fallback`
is internally consistent ("dispatch is possible, serially; no verified parallel
barrier"). The "how exactly" is NOT left unspecified — the new `special_notes`
bullet names the concrete mechanism (`.github/agents/*.agent.md` + `agents:`
frontmatter + `agent` tool in `tools:` + `disable-model-invocation`). The
conservative hold on fanout keys matches the repo's documented
"unverified → conservative" precedent and is confirmed accepted by
`fanout_contracts.py` (non-empty `native_agent_tools` with `sequential-fallback`
= accepted, not required). The alternatives/trade-off (flip fanout too vs. hold)
is explicitly weighed in Nicht-Ziele with a stated reason — satisfies the
mandatory-alternatives-weighting constraint. Proportionate, correct call.

### info-1 (Risks) — intra-block path inconsistency, already tracked

After the change the Copilot block carries two different agent paths: the stale
`.github/copilot/agents/` (unchanged `description` + first `special_notes` bullet)
and the correct `.github/agents/*.agent.md` (new bullet). Mildly confusing in
isolation, but explicitly scoped out as audit finding **P-1** and acknowledged in
AC-6 + Offene Fragen with a recommendation to open a separate P-1..P-5 prose-drift
issue. No action required for this spec. Non-blocking observation only.

### Prompt-injection note

The spec itself (Risiko-2) flags that the Part-2 docs URLs/field names were
supplied as pre-verified context rather than re-fetched, and states no embedded
instructions were found. Reviewer concurs: the spec text contains no instruction-
like content directed at tooling; treated as factual data.

## Verdict

**APPROVED.**

All §8 checks green: mandatory sections complete, trace anchor present, status
marker consistent, no placeholders. Every load-bearing technical claim
(no caller, dormant consistency checks, non-hardcoding tests, zero generated
diff) independently reproduced. The scope is minimal and proportionate; the
conservative hold on fanout keys is the right, well-justified call and does not
create a misleading capability claim.

Pipeline: `quality_pipelines.concept-driven-dev` proceeds (specify → review →
**approve** → plan). No `requirements` handoff in spec-review mode.
