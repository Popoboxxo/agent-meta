# Stale Role Cleanup — Spec Re-Review (independent critic)

> Reviewer: `concept-reviewer` · Date: 2026-09-14 · Branch: `feat/spec-plan-workflow`
> Target: `docs/specs/2026-09-13-stale-role-cleanup-design.md` (Rev 0.2)
> Prior review: `docs/specs/2026-09-13-stale-role-cleanup-review.md` (F-01…F-11)
> Support: `docs/specs/2026-09-13-stale-role-cleanup-system-design.md`
> **No `Status: APPROVED` marker was set or written. Target remains `status: Entwurf`.**

## Verdict: APPROVED-FOR-USER-APPROVAL

All F-01…F-11 are independently verified as resolved. The F-01 reconciliation branch is
correctly bounded and fail-closed for genuinely foreign/user-authored files. Two new
**minor** contract gaps remain (non-blocking; recommended before implementation). No new
`Status: APPROVED` marker. The user's explicit approval gate is still the next step.

## Per-finding resolution

| F-id | Resolved? | Evidence (independently re-verified against working tree) |
|---|---|---|
| F-01 | YES | IC-04 adds `reconcilable(f)` gated on `index_readable ∧ is_candidate ∧ name∉E ∧ name∉previously_managed ∧ _agent_provenance_is_external_skill`. Predicate bound to **primary** markers with origin `0-external/` (skills.py:500 `generated_from=f"0-external/{skill_name}@{commit}"`); `based-on:` explicitly excluded (IC-02:319–321). R7 + Nicht-Ziele document the widened-but-bounded surface; backup-first. AC-21 covers both adopt and `based-on`-only survival. |
| F-02 | YES | `plan_agent_cleanup` now takes `provider: str` + `wrapper_filenames: set[str]` (IC-04:383–390); `StaleAgentEntry` gains `provider/tracked/adopted`; reason precedence defined entry-level (IC-04:458–465). Verified `_collect_all_registry_wrapper_filenames` is registry-wide (active+inactive). AC-06/AC-22 assert provider + precedence. |
| F-03 | YES | `deleted` explicitly defined as the recomputed preview's stale paths, not parsed stdout (IC-07:646–670); R8 documents divergence. AC-14 asserts exact equality and the no-`deleted`-on-500 case. |
| F-04 | YES | IC-06:567–578 requires a planning-only traversal, gates `ensure_skill_repo`/`deinit_skill_repo` on `not dry_run`. Verified today: `ensure_skill_repo` is called unconditionally at skills.py:410–412 and performs `git submodule add`/`clone` (skills.py:212–301); it ignores `dry_run`. AC-10 amended to assert no fs/network mutation incl. no clone/submodule-add. |
| F-05 | YES (migration) / deferred residual | IC-08 (697–705) migrates `sync_prompts_for_provider` to IC-01 fail-closed bootstrap + unconditional index write. Verified the identical fail-open at context.py:1733 and conditional write at :1739. Prompt frontmatter (context.py:1707–1714) emits no provenance marker → intentionally recorded as OQ-9 + Nicht-Ziel. |
| F-06 | YES | AC-02 (`test_index_rewritten_when_expected_equals_previous`, non-empty) and AC-04 (`test_empty_expected_filenames_writes_empty_index`, 0-byte) are distinct fixtures/tests; existing tests confirmed at test_agent_sync_helpers.py:288 and :249. |
| F-07 | YES | AC-15 narrowed to the real trust anchors and explicitly carves out the index-listed case (909–919); AC-21 adds the index-listed phantom deletion + backup-restore test. |
| F-08 | YES | `legacy_unmarked` present in IC-06 foreign schema (547, 558–562) and AC-10 (887–888), semantics gated on OQ-3. |
| F-09 | YES | New IC-10 (739–773) + AC-25 (977–982): element roles, states, confirm dialog, preview→confirm→apply ordering. |
| F-10 | YES | IC-07 ordering constraint (672–675) + AC-24 static guard; Datenfluss note (829). |
| F-11 | YES | IC-01 backward-compat note (257–262). Verified all three callers ignore the return value (mcp.py:378, external_tools.py:336, pipelines.py:1109) and that adding `backup: bool = False` last is call-compatible. |

## Reconciliation branch safety (check 2 / R7)

- Marker-less file → `_agent_provenance_is_external_skill` false → `foreign`, never touched.
- `based-on:`-only file → excluded by IC-02 → `foreign`, survives (AC-21).
- Primary marker with non-`0-external/` origin (e.g. `1-generic/…`) → not reconcilable → `foreign`.
- Branch requires a **readable** index; absent/unreadable index falls back to the provenance
  bootstrap, never to "delete all". Index-empty is handled explicitly (matrix 476–481).
- Residual widening: a hand-authored file that embeds a literal `0-external/` primary
  provenance would be swept — **explicitly documented as R7** with backup-first + logging +
  and the rejected safer alternative recorded. Bounded and acknowledged; not fail-open.
- Reconciliation is not applied when the index is absent/corrupt (bootstrap already admits
  provenance files) — no double-widening.

## New findings (non-blocking)

| ID | Severity | Dimension | Finding | Suggestion |
|---|---|---|---|---|
| N-01 | MINOR | Consistency | IC-06 preview JSON emits `backups_to_prune` (547), but IC-05 states `prune_sync_backups` "Never runs when `dry_run` is true (returns `[]`…)" (510) and Datenfluss (a) invokes it only in the non-dry-run branch (795). `--cleanup-preview` runs `dry_run=True`, so no specified pure contract can populate the field; no AC asserts it. | Either define a dry-run-capable pure candidate computation (return would-be pruned paths; delete only when not dry_run) or drop `backups_to_prune` from the IC-06 contract. |
| N-02 | MINOR | Completeness | IC-07's `cleanup_preview()` contract says only "parse the single JSON object on stdout into a dict" (595–599), yet the HTTP response flattens IC-06's `providers[]` into top-level `stale`/`foreign` and annotates each entry with `provider` (609–613). The flatten/annotate mapping is unspecified, and AC-11 mocks `cleanup_preview()`, so it is untested. Relatedly, IC-04's `plan_agent_cleanup` returns only stale entries — no contract produces the `foreign` list AC-10 requires. | Specify the flatten/annotate step (or have IC-06 emit flat lists), contract the foreign-list producer, and add one AC that feeds the real IC-06 stdout shape through parse/mapping. |

Observation (pre-existing, already documented → not a new finding): on the absent/corrupt-index
path `_agent_has_provenance` accepts `based-on:` (IC-02), so a user-authored file carrying only
`based-on:` is adopted and deletable; R2's stated "primary markers take precedence" does not by
itself prevent this. The reconciliation branch (index-readable) correctly excludes it. Low
likelihood; flagged for awareness only.

## Confirmations

- **No approval marker:** frontmatter line 4 is `status: Entwurf`; the only occurrence of
  `Status: APPROVED` is the descriptive template sentence at line 15. Nothing written/edited.
- The reviewed spec and the prior review file were **not** modified.
- No implementation or plan was produced. Pure editorial fixes were permitted but none were
  warranted (N-01/N-02 are semantic, not editorial).
