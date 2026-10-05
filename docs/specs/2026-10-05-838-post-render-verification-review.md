# Review — SPEC-838-POST-RENDER-VERIFICATION-2026-10-05

**Reviewed artifact:** `docs/specs/2026-10-05-838-post-render-verification.md`
**Review type:** Spec/Design review (concept-driven-dev, §7.1 spec-review mode)
**Reviewer:** concept-reviewer
**Date:** 2026-10-05
**Related issue:** #838 — instances #834 / #835 / #836 — related #802 / #680

---

## 1. Scope

Structural review of the mini-spec for the central `post_render_verify` stage:
completeness vs. the issue's acceptance criteria, logical soundness of stage
placement, feasibility of the run-scoped write set, assumptions/risks
(false positives, suppression channel, provider conditioning), threat model, and
size/phasing. The spec was **not** modified. Code paths referenced by the spec
were read to verify feasibility claims:

- `scripts/lib/cli_commands.py` (`_handle_sync`, `_handle_validate`,
  `_run_consistency_checks`, dispatch)
- `scripts/lib/sync_pipeline.py` (stages, `_sync_stage_generated_file_hash_capture`)
- `scripts/lib/generated_file_drift.py` (`capture_generated_file_hashes`,
  `_iter_managed_files`)
- `scripts/lib/io.py` (`write_checked`), `scripts/lib/context.py`,
  `scripts/lib/agent_sync.py`, `scripts/lib/platform.py`,
  `scripts/lib/pipelines.py`, `scripts/lib/agents.py`,
  `scripts/lib/consistency/placeholders.py`

**Positive:** the central-stage idea is correct; the placement between the
writers and stage 13 hash capture is sound (config-audit is read-only); the
`SyncError` precedent is real (`pipelines.py:97/105`); the split diagnosis in
`platform.py:147` exists; the problem statement (drift being frozen into the
baseline) is accurate; trace anchor and §7.1 mandatory sections are present; no
`TODO`/`TBD`/`<...>` placeholders.

---

## 2. Findings by severity

### BLOCKER

#### RVW-1 — The run-scoped write set is a hidden cross-cutting refactor; the "resolved output plan" alternative does not exist as an object.

- **Dimension:** Feasibility / Logic gap
- **Evidence:** A repository-wide search finds **no** `RenderWriteSet`, no output
  plan, and no run-scoped write-set abstraction. The nearest choke point,
  `write_checked` (`io.py:414`), is called at ~19 sites but carries **no**
  `provider` / `kind` / `optional` metadata, and roughly **30 writers bypass it**
  via direct `path.write_text()` (e.g. `context.py` has ~20 such sites). The
  late hash capture does **not** use a run-scoped set either: it derives files
  post-hoc by walking managed indices (`generated_file_drift._iter_managed_files`,
  `:237`) — a directory-derived set, not "produced by the current run", and with
  no per-artifact metadata.
- **Impact:** §2.2 presents "instrument the shared writer helpers" and "derive
  from the resolved output plan" as equally available. The second option is not
  implementable today (no plan abstraction). The first is a cross-cutting change
  through every writer module and all direct-write call sites. AC-1/AC-2/AC-3/AC-9
  all hinge on this mechanism, so the spec cannot currently be planned.
- **Suggested change:** Pick one mechanism and make it concrete before planning.
  Either (a) scope Phase 1 to the existing managed-index-derived file set
  (same semantics as hash capture, extended with `provider`/`kind`/`optional`
  during the walk), accepting that it is post-hoc, not run-scoped; or (b) commit
  to instrumentation and enumerate the exact modules/signatures to change plus an
  estimate. Do not leave both as an open "MAY". If (a), explicitly reconcile
  AC-2's "current run, not a static list" wording with the managed-index set.

### MAJOR

#### RVW-2 — AC-8 (`--check` reachability) is misattributed: `_run_consistency_checks` runs under `--validate`, not `--check`.

- **Dimension:** Consistency / Logic gap
- **Evidence:** `_run_consistency_checks` (`cli_commands.py:151`) is called only
  at `:1032`, inside `_handle_validate` (`:1016`). `_handle_validate` is bound to
  `args.validate` in the dispatch table (`sync.py:648`), not to `args.check`.
  `--check` matches no mode handler and therefore falls through `_dispatch`
  (`sync.py:657-663`) into `_handle_sync`. Consequently, inserting the stage in
  `_handle_sync` already makes it run under `--check`. But `--check` forces
  `args.dry_run = True` (`sync.py:104-105`), so writers do not write and an
  instrumented write set is empty — verification would be vacuous. This is
  precisely open question #6 leaking into AC-8.
- **Impact:** The spec states a mechanism that is factually wrong and, if
  implemented as written, verifies nothing in `--check` (or requires a planned set).
- **Suggested change:** Correct §2.1/AC-8: state that `--check` runs
  `_handle_sync` with forced dry-run; therefore the stage must operate on a
  *planned* artifact set (or be a documented no-op) in `--check`/`--dry-run`, and
  the #802 gate is the fallback for real deployment reality. Tie AC-8 to #802
  explicitly rather than to `_run_consistency_checks`.

#### RVW-3 — The suppression channel is circular vs. #835 and cannot express per-row optionality.

- **Dimension:** Logic gap / Consistency
- **Evidence:** §2.5 marks entries `optional` "by the same resolver that decides
  whether it is materialised". For #835 (directory table lists roles with 0
  materialised files), the table is produced by `build_agent_table`
  (`agents.py:182`) from `resolve_active_roles` — the same resolver. If P2
  consults that resolver's `optional` mark, #835 is suppressed and P2 never
  fires, **contradicting AC-3**. Separately, §3's `RenderedArtifact.optional` is
  per-artifact, while §2.5 requires per-*row* optionality for a directory table;
  the interface contract provides no row/entry channel.
- **Impact:** Either #835 is unreproducible (AC-3 fails) or legitimate
  feature-flag-unmaterialised rows abort consumer syncs (false positive). The
  P2/P4 contract is unimplementable as written.
- **Suggested change:** Define the boundary explicitly: which roles are
  *legitimately* absent per provider (capability/feature-flag — suppress) vs.
  the #835 defect (must fire). Add a row/entry-level optional channel to the
  interface contract (or a per-artifact variant that models a table row). State
  how #835 is distinguished from a suppressed row.

#### RVW-4 — Fail-fast defaults + unresolved P1 grammar risk aborting healthy consumer syncs, and abort-after-write desyncs the hash baseline.

- **Dimension:** Risks / Feasibility
- **Evidence:** P1/P2 default `error`; P1's reference grammar (markdown links vs
  backticks vs imports, project-local optional user-file exemptions) is explicitly
  unresolved (open question #2). Because the stage is *post*-render, writers have
  already written when it raises; aborting before
  `capture_generated_file_hashes` leaves on-disk content ahead of the baseline.
  The next run's drift scan then treats freshly generated files as manual edits
  (backups + overwrite). The spec's claim "a bad render can never be frozen into
  the baseline" is achieved only by creating a baseline/content inconsistency.
- **Impact:** High false-positive → consumer CI/tooling DoS; partial-sync state
  and repeated drift backups.
- **Suggested change:** Until the P1 grammar and exemptions are pinned, default
  P1 to `warn`; promote to `error` only after clean consumer fixtures. Define
  abort semantics: either verify-then-baseline per artifact, or explicitly
  document the desync consequence and how the next run recovers.

#### RVW-5 — No threat model (4 questions) for a consumer-facing fail-fast stage.

- **Dimension:** Risks
- **Evidence:** §9 lists generic risks but never answers the 4 questions
  (rule `threat-model-4-questions`). Brief answers as they stand:
  1. **What are you building?** A post-render gate reading written artifacts and
     aborting consumer syncs; filesystem read-only, no auth/data storage.
  2. **What could go wrong?** A false-positive predicate aborts an otherwise
     valid consumer sync (availability) and leaves a stale hash baseline;
     pathological inputs (huge/deep reference graphs) can slow the extra pass.
  3. **Mitigations?** Default risky predicates to `warn`, scope strictly to the
     write set, bound scan size/recursion, never execute referenced content.
  4. **Consequences?** Broken consumer CI, loss of trust, cascading drift
     backups. No remote code execution or data exfiltration path.
- **Suggested change:** Add a short threat-model subsection to §9 (or a
  dedicated section); at minimum record 1–4 above and cite the mitigation.

#### RVW-6 — P3 duplicates existing placeholder validation and generalizes a `{{platform.*}}`-only diagnosis.

- **Dimension:** Consistency / Completeness
- **Evidence:** `consistency/placeholders.py` already validates `{{VAR}}` against
  `_BUILTIN_VARS`; `warn_unresolved_platform_vars` (`platform.py:147`) handles the
  `{{platform.*}}` split diagnosis and takes `platform_vars`. P3 re-runs the same
  class over rendered artifacts. The spec notes duplication risk only vs. the
  *drift scan*, not vs. the existing placeholder consistency check.
- **Suggested change:** Explicitly reuse/extend the existing placeholder
  machinery, or state precisely how P3 differs, to avoid two sources of truth for
  unresolved placeholders. Confirm the split diagnosis generalizes from
  `platform_vars` to the resolved variable registry (`variables`).

### MINOR

#### RVW-7 — Approval marker vocabulary inconsistent with §7.1.

Frontmatter `status: proposed` and body `Status: **proposed**`; §7.1 expects
`Entwurf | APPROVED (Datum)`. Trace anchor (`spec-id`) is present and
well-formed; mandatory sections are all present. Suggest aligning the status
field with the §7.1 vocabulary so the approval gate is machine-checkable.

#### RVW-8 — P2 requires existence in *every* active provider, ignoring provider capability gating.

`agents.py`/`agent_sync.py` show agent surfaces are capability-gated per provider
(`agents_dir`, `has_agents`-style config, `agent_ext`). "Every active provider's
`agents/` dir" without a capability filter yields false positives. Suggest
conditioning P2 on resolved provider capability (provider-agnostic), and folding
this into the RVW-3 suppression boundary.

#### RVW-9 — Interface contract enums partially untethered from the predicates.

`RenderedArtifact.kind` includes `managed-index`; `VerifyFinding.cause` includes
`missing-artifact` (not mapped to any predicate in §2.3). Non-blocking, but pin
the enums to the predicate set to avoid dead values.

---

## 3. Size estimate + recommended phasing

**Overall: L** (approaching **XL** if the instrumented-write-set route (RVW-1b)
is chosen and completed across all writers and direct-write call sites).

Recommended split into three phases, each independently shippable:

- **Phase 1 (S/M) — P3 only.** `unresolved-placeholder` over the existing
  managed-index-derived file set (same basis as hash capture), reusing the
  existing placeholder machinery. Default `warn`. No new write-set abstraction.
  Document the #802 `--check` limitation (AC-8 fallback). This alone closes #834.
- **Phase 2 (M/L) — P1 + write-set.** Define the reference grammar and
  exemptions, then `path-existence`. Only if needed, introduce `RenderWriteSet`
  (instrumentation or managed-index extension). Promote to `error` after clean
  consumer fixtures. This closes the #836 class.
- **Phase 3 (M) — P2 (+ P4 after #680).** Requires the per-row optional resolver
  (RVW-3). Closes #835. P4 stays `warn` until #680's data lands.

AC-1's "strictly before hash capture" and AC-9's invariant tests are satisfiable
in each phase; AC-2/AC-3 are Phase 2/3 only. Do not gate Phase 1 on the full
write-set refactor.

---

## 4. Verdict

**CHANGES_REQUESTED.**

Rationale: the central-stage direction and placement are sound (no BLOCKED
condition — the design is viable once the mechanisms are pinned down). However,
the spec contains one BLOCKER (RVW-1: the write-set acquisition is an unbounded
cross-cutting refactor and the stated fallback does not exist), a factual error
in the `--check` reachability claim (RVW-2), a circular/contradictory suppression
design that makes #835 either unreproducible or a false positive (RVW-3), unsafe
`error` defaults on an unresolved P1 grammar plus an unanalyzed abort-after-write
baseline desync (RVW-4), and a missing threat model (RVW-5). These are
substantial, blocking gaps; the spec must return to the author to resolve
write-set acquisition, suppression semantics, and `--check`/dry-run behaviour
before a plan can be derived. The trace anchor is valid, so a plan derived after
the fixes can reference `SPEC-838-POST-RENDER-VERIFICATION-2026-10-05`.

**STATUS: done**
