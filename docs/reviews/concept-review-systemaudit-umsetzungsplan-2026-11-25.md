# Concept Review — Systemaudit-Umsetzungsplan

**Reviewed artifact:** `docs/plans/systemaudit-umsetzungsplan-2026-11-25.md`  
**Branch:** `feat/provider-agnostic-sync-hooks-wave-5`  
**Review date:** 2026-11-25  
**Reviewer role:** `concept-reviewer`

---

## Scope

Review of the freshly created implementation plan derived from a system audit of agent-meta. Focus areas requested:

1. Coverage of critical audit findings
2. Realism and sequencing of phases/tasks
3. P1/P2/P3 prioritization
4. Missing dependencies/risks
5. Integration of open issues (#1359, #783, #676, #779, #681, #679, #778, #548, #330/#329) and requirements (REQ-CMD, REQ-SE, REQ-ADM, REQ-CTX)
6. Language/style clarity

---

## Findings

### Major

| # | Severity | Dimension | Description | Improvement suggestion |
|---|----------|-----------|-------------|------------------------|
| F1 | major | Feasibility / Completeness | **Phase 1 scope overload.** Phase 1 is framed as "make the branch mergeable", yet it bundles hook refactoring with the full implementation of Commands-System (REQ-CMD-01..10), Admin-UI setup mode (REQ-ADM-01..03), and SE-Pipeline persistence/role-separation (REQ-SE-01..13). These are multi-day feature epics, not merge-blocker tasks. | Restrict Phase 1 to branch-relevant fixes (hook quality, `sync.py --validate`, `opencode.json` cleanup). Spin out REQUIREMENTS work into separate feature branches/epics with their own specs. |
| F2 | major | Logic / Consistency | **Merge-blockers and open Must-Requirements are conflated.** Section 2 lists hook problems (genuine merge blockers) alongside unimplemented Must-Requirements (Commands, SE, Admin-UI). The plan then treats all of them as P1, blurring the line between "what blocks this branch" and "what blocks the product". | Split section 2 into two distinct tables: "Branch merge blockers" and "Open Must-Requirements from REQUIREMENTS.md". Assign separate phases/owners. |
| F3 | major | Risks / Feasibility | **Phase 4 is a scope-creep bucket.** It contains eight parallel improvement items (#779, #676, #681, #783, #679, #778, REQ-CTX-01, plus implicit post-upgrade cleanup follow-up) without sub-division or exit criteria. The plan itself acknowledges this risk but does not mitigate it structurally. | Break Phase 4 into sub-phases or streams (e.g., routing, HACS, liveness, merge-policy, context notes) with per-stream goals and ordering constraints. |
| F4 | major | Feasibility | **No effort estimates or timeline.** High-risk items (e.g., `dod-push-check.sh` SRP refactor across many consumer projects, SE persistence protocol) are not sized, making the plan unverifiable for scheduling. | Add T-shirt-size estimates and rough time boxes per phase, especially for Phase 1 and Phase 2. |

### Minor

| # | Severity | Dimension | Description | Improvement suggestion |
|---|----------|-----------|-------------|------------------------|
| F5 | minor | Completeness | **Other Must/Should requirements from `docs/REQUIREMENTS.md` are not addressed.** REQ-MOD-01..07 (dynamic model presets), REQ-SYNC-01..02 (backup/audit), and REQ-GEN-01 (deprecated template handling) are present in REQUIREMENTS.md but absent from the plan (except REQ-MOD as a status inconsistency in 2.10). | Either explicitly mark them as out-of-scope with rationale or add them to the appropriate phase. |
| F6 | minor | Completeness | **No acceptance/exit criteria per phase.** Phases list activities but not "done-when" conditions, which weakens the Definition of Done. | Add 2–3 concrete exit criteria to each phase (e.g., "`sync.py --validate` green", "PR approved and merged", "scenario tests added"). |
| F7 | minor | Consistency / Language | **Terminology inconsistencies.** "Uncommittete Änderung" is not standard German/English project terminology; "Rating C" and "Wave 5" are used without context. | Use "Uncommitted change" or "Nicht committete Änderung"; add one-sentence explanations for "Wave 5" and "Rating C" or link to the source review. |
| F8 | minor | Risks | **Missing dependency on test infrastructure.** The plan relies on `tests/scenarios/asserts/` and new unit tests but does not state whether the test harness is ready or who owns it. | Add a dependency/risk line for test-harness readiness and owner. |

### Info

| # | Severity | Dimension | Description |
|---|----------|-----------|-------------|
| I1 | info | Completeness | The risk section (§7) is comprehensive and correctly identifies blast-radius, scope-creep, and knowledge-gap risks. |
| I2 | info | Completeness | Open issues and requirements are explicitly referenced; coverage is traceable. |
| I3 | info | Consistency | Tabular structure is clear and consistent across P1/P2/P3 sections. |

---

## Verdict

**CHANGES_REQUESTED**

The plan is a solid, well-structured inventory of audit findings and open work. It correctly identifies the critical issues and references the right requirements/issues. However, it mixes branch merge-blockers with multi-day feature epics in Phase 1, creates a scope-creep-heavy Phase 4, and lacks effort estimates and per-phase exit criteria. Before execution, the plan should be reorganized so that Phase 1 is strictly branch-merge-focused, REQUIREMENTS are handled in separate epics, and every phase has measurable done-criteria.

---

## Recommended next step

Route back to the author for reorganization. After revision, re-review the phase boundaries and acceptance criteria before the orchestrator advances the plan into `quality_pipelines.concept-driven-dev`.
