# Stale Role Cleanup — Spec Review (independent critic)

> Reviewer: `concept-reviewer` · Date: 2026-09-13 · Branch: `feat/spec-plan-workflow`
> Target: `docs/specs/2026-09-13-stale-role-cleanup-design.md`
> Support: `docs/specs/2026-09-13-stale-role-cleanup-system-design.md`, `.opencode/skills/spec-plan-workflow/SKILL.md`
> **No `Status: APPROVED` marker was set. Spec remains `status: Entwurf`.**

## Verdict: CHANGES_REQUESTED

The spec is structurally complete, the corrected B-III hypothesis is right, and the
safety/fail-closed direction is sound. It is **not** release-ready because several
interface contracts are incomplete or contradict the stated remediation goal, and one
data-loss fail-open remains outside its scope. Findings F-01 … F-05 are MAJOR.

## Scope reviewed

7 review dimensions + spec-plan §7.1 (Pflichtsektionen, Trace-Anker, Approval-Marker,
No-Placeholder) + the 6 task checks (template completeness, corrected hypothesis, safety
model, Admin-UI contract, rollback, AC quality/provider-agnosticism).

Template completeness: **PASS** — frontmatter (`spec-id: SPEC-STALE-ROLE-CLEANUP-2026-09-13`,
title, `status: Entwurf`), Problem/Ziel/Nicht-Ziele, Interface Contracts (IC-01..IC-09),
Datenfluss (a/b/c), numbered ACs (AC-01..AC-20), Offene Fragen (OQ-1..OQ-8) + Risiken
(R1..R6), Trace-Anker all present. No unresolved placeholders in required sections.

Corrected hypothesis: **PASS** — the spec explicitly states the managed block already
shrinks in the normal path (`context.py:436`) and scopes six residual paths S1–S6
(`auto_generate:false`, provider disabled, `--only-variables`, `dry_run`, duplicate marker,
injected foreign content). It explicitly rejects any "fix the shrink" regression. No
regression to the user's original (partly wrong) hypothesis.

Provider-agnosticism: **PASS** — no `if provider ==` in the design; AC-20 asserts a static
scan; IC-03 removes the only capability-gated provider branch. `external-skill-agent-files`
is confirmed declared only by Claude (`config/ai-providers.yaml:35`).

Admin auth/CSRF: **no new gap** — `do_POST` applies `_check_token()` + `_check_origin()`
server-wide (`admin-server.py:3257–3260`); routes added to `_POST_EXACT_ROUTES` inherit
both automatically. Preview→confirm→apply ordering is specified and correct.

## Findings

| ID | Severity | Location | Issue | Suggested change |
|----|----------|----------|-------|------------------|
| F-01 | MAJOR | IC-04 delete predicate; Problem B-I §3; AC-06 | **Existing stale non-Claude skill wrappers are not remediated.** When a readable index exists, `previously_managed` = index contents only, so an untracked wrapper written by `skills.py` (no capability gate, `skills.py:374–378/424/490/525–527`) is classified `foreign` and never deleted. The fix tracks wrappers only *going forward*; wrappers already stale/deactivated before the first post-fix sync (exactly the user's complaint, Problem B-I §3) survive forever. | Add an explicit reconciliation/adoption branch for provenance-carrying, unexpected candidates when the index is readable, or document the residual and add a distinct preview category + user-approved manual removal. Must decide. |
| F-02 | MAJOR | IC-04 `plan_agent_cleanup` signature; IC-06 JSON | **The planner cannot populate its own output.** Signature `(target_dir, expected_filenames, pc, project_root)` carries no `provider` name, so `StaleAgentEntry.provider` (IC-06 groups by provider) cannot be filled; and it never receives the active-wrapper filename set, so `reason="skill deactivated"` cannot be distinguished from `"role removed from config"`. `pc` in `ai-providers.yaml` has no provider-name key. | Pass `provider: str` and the wrapper filename set (or a `name → reason/origin` map) into `plan_agent_cleanup`; specify reason precedence. |
| F-03 | MAJOR | IC-07 apply response; AC-14 | **`deleted:[...]` derivation is unspecified.** `SyncExecutor.run()` returns only `{success, output, returncode, command}` (`admin-server.py:1076–1106`); the spec never states how the `deleted` list in the apply response is produced, yet AC-14 asserts it. | Define `deleted` as the recomputed preview's stale paths (explicitly), or parse a machine-readable sync summary; make it testable. |
| F-04 | MAJOR | IC-06; Datenfluss (b) | **Preview is not guaranteed mutation-free.** It "runs the sync pipeline with `dry_run=True`", but `SyncExecutor.dry_run()` documents that agent-meta's `--dry-run` "still touches some artefacts" (`admin-server.py:1133–1137`), and `skills.ensure_skill_repo` is called unconditionally (`skills.py:410–412`) and can `git submodule add`/`git clone`. A read-only preview endpoint can mutate the repo. | Route preview through a side-effect-free path (like `--validate`) or explicitly constrain/verify the stages executed; amend AC-10 to assert no filesystem/network mutation, not just "no index/unlink/backup". |
| F-05 | MAJOR | Ziel #1/#2; IC-08 ownership table | **Residual fail-open delete contradicts the stated goal.** `context.py::sync_prompts_for_provider` (`:1723–1740`) still has the identical `if not managed_index.exists() or name in previously_managed` fail-open at `:1733` and the conditional index write at `:1739`. Ziel #1 says "exactly one implementation" and Ziel #2 "replace the fail-open no-index delete"; the prompts index is neither migrated nor listed as out of scope. | Migrate this instance through IC-01 + `_agent_has_provenance`-equivalent predicate in the same change, or explicitly list it (and its data-loss risk) as out of scope with an OQ/risk entry. |
| F-06 | MINOR | AC-02 / AC-04 | Both ACs edit the same test `test_empty_expected_filenames_never_rewrites_index` (one "extend", one "replace"), and AC-02's "index stays empty" is only valid when `expected_filenames == set()` — making AC-02 ≈ AC-04. | Disambiguate AC-02: fix `expected_filenames={"developer.md"}` → nothing deleted, index rewritten to `developer.md\n`; or drop it as a duplicate and align test references. |
| F-07 | MINOR | AC-15; IC-04 predicate | AC-15 claims "a user-authored file is **never** deleted", but the tested class is narrower ("neither listed in a readable index nor carries a provenance marker"). An index-listed phantom name later authored by the user is deleted with no provenance check. | Require `_agent_has_provenance` (or an equivalent) for index-tracked deletes, or narrow AC-15's wording and add a test for the index-listed case. |
| F-08 | MINOR | OQ-3 vs IC-06/AC-10 | OQ-3's recommended default introduces a `legacy_unmarked` flag, but IC-06's JSON schema and AC-10 omit it — inconsistency if the default is approved. | Add `legacy_unmarked` to the preview schema (pending approval) or state explicitly that IC-06 intentionally defers it. |
| F-09 | MINOR | Interface Contracts / Datenfluss (b)(c) | The Admin-UI control referenced by design C4 ("+ `admin-ui.html` control") has no interface contract — only the HTTP routes are specified. | Add a short IC for the UI control (element, states, confirm dialog) or state UI markup is out of scope. |
| F-10 | MINOR | IC-07 ordering constraint | "B-I must ship before B-II" is stated but has no AC/verification hook; it can be silently violated. | Add an AC or plan-gate note referencing the ordering constraint. |
| F-11 | INFO | IC-01 `cleanup_stale_managed_files` | Return type changes `None → list[str]`; existing callers (`mcp.py:382`, `external_tools.py:340`, `pipelines.py:1113`) ignore the result — safe, but not stated. | Add one sentence confirming backward compatibility. |

## Direct edits made

**None.** All identified defects are substantive (AC correctness/schema, contract
incompleteness, scope/residual-risk) rather than pure editorial or traceability issues;
fixing them would silently redesign the spec, which is outside the reviewer mandate.

## Confirmations

- No `Status: APPROVED` (or any approval marker) was written. The spec still reads
  `status: Entwurf`; approval remains the separate user gate.
- The reviewed spec file was **not** modified.
- No implementation or plan was produced.
