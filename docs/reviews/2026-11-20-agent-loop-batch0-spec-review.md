# Concept-/Spec-Review — Agent-Verbesserungsschleife Batch 0

- Reviewed artifact: `docs/specs/2026-11-20-agent-improvement-loop-batch0-spec.md` (spec-id `SPEC-AGENT-LOOP-BATCH0-2026-11-20`, IC-1..8, AC-1..12, OQ-1..4, ADR-1..3)
- Approval basis: `docs/plans/2026-11-15-master-roadmap.md:3` APPROVED 2026-11-19; P28 `:59`, PR 6.0 `:221`, E-29 `:297`, rebaseline NONE
- Evidence source: `docs/plans/2026-11-14-agent-improvement-loop-plan.md` (DRAFT, stale, base `3dc03f95`)
- This review targets the FINAL on-disk spec version (authoritative).

## Scope

Resolve OQ-1..4 (CONFIRM_CONSERVATIVE vs ESCALATE), sanity-check ADR-1..3 and the conventions-SKILL path for hidden new decisions, and verify spec-mandatory sections / trace anchor / approval marker / no-placeholder.

### Mandatory-section check (spec-plan-workflow §8)
- Pflichtsektionen: Problem/Ziel/Nicht-Ziele (:20-48), Interface Contracts (:50-102), Datenfluss (:104-128), Acceptance Criteria (:130-145), Offene Fragen + Risiken (:147-160) — all present. PASS
- Trace-Anker: `spec-id: SPEC-AGENT-LOOP-BATCH0-2026-11-20` (:2, :196). PASS with caveat (see Finding minor-1).
- Approval-Marker: `Status: APPROVED (User, 2026-11-19 ... — E-29; Spec nachgereicht ...)` (:4, :16) — consistent with "nachgereicht auf Basis des approbierten Master-Plans", no new decision. PASS
- No-Placeholder: no TODO/TBD/`<...>`/`{{...}}` in mandatory sections; unresolved items are explicitly labelled OQ-1..4 with "do not invent" guidance. PASS

## Findings by severity

### major-1 — Ceiling unit error in IC-5 / AC-7 (Dimension: Consistency / Logic)
- IC-5 (:82) and the data-flow line (:119) specify `bytes <= 19500 * 1024` (= 19,968,000 B ≈ 19 MB). §5 of the detail plan (:120) and §1.3 (:67) use **decimal KB** (24,317 B = "24,3 KB"). The documented "Always-on Claude ≤ 19,5 KB" is therefore **19,500 B**, not 19,968,000 B — off by 1024×.
- Effect: with a realistic session-sum (~24,317 B) the comparison is always true → `XPASS(strict)` → the test fails on day 1 instead of `xfail`. Functional defect.
- Improvement: replace with `bytes <= 19500` (or `19.5 * 1000`), cite §5 as source, keep `xfail(strict)`. This is a mechanical correction derivable from §5 — no new decision. Required before APPROVED.

### minor-1 — Trace-anchor claim not literally true (Dimension: Consistency)
- :198 states "Plan referenziert diesen Wert (Master :221 / Detail :208-214)". The master roadmap and the detail plan do NOT contain the new spec-id string; the detail plan still uses the placeholder path `2026-11-XX-agent-improvement-loop-spec.md` (:37, :192).
- Improvement: record the spec-id/path in the plan's `trace:` block or soften the wording to "referenzierbar über Pfad". No effect on implementation.

### minor-2 — R1 lint content check not actually specified (Dimension: Logic gap)
- IC-6 (:88) claims R1 checks `description` length AND "enthält 'when to use'+Abgrenzung", but labels the mechanism "(Lint Länge)"; AC-8 (:141) only tests length (161..200 chars). Semantic content cannot be verified by a length check.
- Improvement: either add a keyword/phrase check or narrow the R1 description to length-only. Not blocking.

### info — ADR sanity check / conventions-SKILL path
- ADR-1 (bytes/4 proxy) traces to detailplan :19; ADR-2 (xfail(strict) until hard in Batch 11) traces to §9.3 AC-L2 :185, E7 :238, E-29 :297, P31; ADR-3 (rubric non-strict start) traces to Task 1.3 :212. All three **describe documented decisions — none invents a new one**.
- IC-8 path `.claude/skills/conventions/SKILL.md` exists on disk (frontmatter `name: conventions`) — path correct, **no escalation**.
- No hidden new decisions found beyond OQ-1..4 and the major-1 defect.

## OQ resolution table

| OQ | Decision | Evidence | Implementer instruction |
|----|----------|----------|-------------------------|
| OQ-1 §5-Zielwert-Mapping | CONFIRM_CONSERVATIVE | Detailplan §5 :108-120 documents Hebel H1–H7 and Gesamtziele with explicit values + artifact names (:120); master :221/PR 6.0 + E-29 :297 approve "Ziele hart" without enumerating values; spec :150 already prescribes "documented constants + source citation, no invented values"; xfail(strict) defers binding to Batch 11 (:228-229, P31) | Parametrize ONLY the five explicitly-stated §5 Gesamtziele as source-cited constants: Orchestrator-Render ≤28 KB → role "orchestrator" × provider; Roster ≤300 KB → per-provider total; Ø Worker −35 % → worker average; Always-on ≤19,5 KB → Claude always-on (= OQ-3); AGENTS.md ≤12 KB → DO NOT parametrize (H6/P30 out of scope, spec :41). Do NOT map H1–H7 levers as separate targets (sub-artifacts/mechanisms, several out of Batch-0 scope). Keep xfail(strict); re-confirm exact binding at Batch 11. |
| OQ-2 JSON-Top-Level-Einbettung | CONFIRM_CONSERVATIVE | Documented shape contract `{provider:{role:{bytes,lines,tokens_approx}}}` (detailplan :210; IC-1 :56; AC-1 :134); a `"providers"` wrapper changes that contract; IC-1b/IC-3 (:59, :70) already choose the reserved key | Keep `"session-sum"` as a top-level reserved sibling key next to provider keys. Do NOT add a `"providers"` wrapper. `measure_agents()` still returns the pure provider mapping (AC-1); only `run_agent_report`/CLI adds the sibling key. |
| OQ-3 Session-Summe-Ceiling | CONFIRM_CONSERVATIVE (+ required correction) | §5 :120 names exactly one always-on goal "24,3 KB → ≤ 19,5 KB"; §1.3 :67 derives 24,3 KB = entry 5.358 + rules 8.117 + agent/skill/command descriptions 5.133+3.568+2.141 B; decimal-KB convention. No second session-sum value exists. | Use §5's 19,5 KB = **19,500 B** (decimal) as the single ceiling; aggregate session_sum from entry-file + rules + all always-on descriptions so the baseline matches §1.3 (currently unmet → xfail(strict)); do not invent a separate value or a *1.01 variant. **Fix major-1**: `19500 * 1024` → `19500`. |
| OQ-4 Rollenquelle | CONFIRM_CONSERVATIVE | Task 1.1 :210 explicitly "Lauf gegen `.claude/agents` liefert 58 Zeilen" → measurement = rendered 58; §9.3 AC-L3 :186 "Lint ... für alle 99 Rollen" + §9.1 :176 + §10 :200 → lint = source templates 99. Two different tools, not a contradiction. | Measurement CLI + baseline → rendered `.claude/agents/*.md` (58, :210). Rubric lint → source `agents/1-generic/*.md` (99, :186/:176). Keep `agents_dir`/`agent_ext` configurable via `mappings` (IC-1) so both stay supported. |

## ESCALATE list for main chat

**Empty.** All four OQs resolve to CONFIRM_CONSERVATIVE using documented evidence within the existing approval. No genuine new decision requires user escalation.

- conventions-SKILL path: **NO ESCALATE** — `.claude/skills/conventions/SKILL.md` exists and is verified.
- The only open item is the mechanical ceiling-unit correction (major-1), derivable from §5 — not an escalation.
- (Out of scope, for awareness only: the exact final per-role target binding will be finalized at Batch 11 / P31, a separate PR.)

## Verdict + rationale

**CHANGES_REQUESTED** — one major finding: the ceiling comparison in IC-5/AC-7 is off by 1024× (`19500 * 1024` vs documented 19,500 B) and would fail immediately via `XPASS(strict)`. All four OQs are resolved conservatively within approval; once major-1 is corrected to `bytes <= 19500`, the spec is APPROVED and Batch 0 can proceed. No escalation to main chat needed.

Counts: critical 0 · major 1 · minor 2 · info 1.

Commit note (trigger boundary — review artifact only; caller runs secret scan before commit, no push/tag/branch):
`docs: add Batch 0 spec review with OQ-1..4 resolution`
