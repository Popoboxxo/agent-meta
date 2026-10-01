# Amendment Step-1 Review — Provider-Audit Gap Closure + Opencode v2

> Reviewer: `concept-reviewer`
> Subject: the just-applied Step-1 amendment to
> `docs/specs/2026-09-30-provider-audit-opencode-v2.md` and
> `docs/plans/2026-09-30-provider-audit-opencode-v2-plan.md`
> Trace anchor: `spec-id: SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30`
> **VERDICT: CHANGES_REQUESTED**

## Method and limitation

The review is based on the **on-disk content** of the two documents (spec 689 lines,
plan 723 lines) plus supporting repo anchors. No shell/`git` tool is available to this
reviewer, so the pre-amendment baseline could **not** be diffed against HEAD; checks
that depend on "unchanged since the last revision" are verified for *internal*
consistency and monotonicity only (noted per check).

## Scope

The amendment closes three gaps:
1. `agent-discovery` (bool, default `false`) as the concrete provider-neutral OQ-1 key (§2.1/§4, AC-9, §11/§11.1).
2. SemVer policy correction (Copilot default-on = MAJOR; Antigravity flag-gated + Opencode v2 opt-in = MINOR) with a release/bump task in the plan.
3. N7 (Opencode v2 needs a VCS root) recorded as Accepted in spec §13, no new AC/task.

## Per-check results

### Check 1 — Key name identical; no provider literal in a code path — PASS
- `agent-discovery` is spelled identically in spec (§2.1 line 117; semantics line 141; values line 159; §4 lines 357–358; AC-9 line 465; §11 lines 563/567; §11.1 lines 578–580/585; §13.1 line 617) and plan (lines 34, 54, 109, 202, 204–205, 338–339, 434). No variant (`agent_discovery`/`agentDiscovery`) exists.
- The key is described as provider-neutral; the provider fact stays a *value* on the provider entry (spec line 141). No `if provider == "Name"` path is described for it; the plan keeps it in `config/ai-providers.yaml` (Task 4) and consumes it via data. PASS.

### Check 2 — SemVer logic sound; §11.1 gating correct — PASS (with one wording inconsistency, MINOR-1)
- Spec §11 (lines 561–565): artifact corrections patch/minor; **Copilot default-on → MAJOR** (line 562, explicitly "with no opt-in"); **Antigravity flag-gated → MINOR** (line 563, future flip would be major); Opencode v2 opt-in → minor (line 564); required bump = **MAJOR** (line 565). Internally consistent.
- §11.1 (lines 575–580): the three Copilot rows are **not** gated; the three Gemini/Antigravity rows are annotated "(gated by `agent-discovery`)", reconfirmed line 585. Correct: Copilot default-on, Antigravity opt-in.
- Plan Task 20 acceptance (line 415) reproduces the same rationale ("Copilot default-on … ⇒ MAJOR; Antigravity flag-gated + Opencode v2 opt-in would alone be MINOR, dominated by MAJOR"). Consistent with §11.
- **Inconsistency:** spec §13.2 risk row line 641 still says "Major-Bump für Pfadänderungen **(Copilot/Antigravity)**", and plan §Risks line 546 repeats "a major bump for Copilot/Antigravity" — contradicting §11 (Antigravity is flag-gated MINOR and, by default, moves nothing). See MINOR-1.

### Check 3 — N7 marked Accepted with rationale + AC-5 cross-reference — PASS (plan label inconsistent, MINOR-3)
- Spec §13.3 (lines 644–648): table "Accepted (out of generator scope)"; N7 disposition is "**Accepted (out of generator scope).** … runtime precondition … AC-5 already scopes the v2 verification to a git-rooted project … **No new AC and no new task** are added." Cross-reference "AC-5 (§8); §10.3", evidence `runtime-consolidation.md:71`. Clear and complete.
- No dangling task/AC: the plan creates no N7 task (Task 20 is release bookkeeping, explicitly not a finding closure). Space is clean.
- **Inconsistency:** the plan's Findings Traceability still labels N7 **"Deferred"** (line 701) and lists it in the "Deferred register (12)" (line 721), while the spec labels it **Accepted**; the plan does add reconciliation prose. See MINOR-3.

### Check 4 — Plan integrity — FAIL (MAJOR-1)
- Highest-numbered node: **yes**, Task 20 (lines 411–423) is the terminal task.
- Depends on 19: **yes** (line 418), single monotonic edge `20 -> 19`.
- Declared `Files:` set disjoint from Tasks 1–19: **yes on paper** — `VERSION`, `CHANGELOG.md`, `.meta-config/project.yaml`, `README.md` (line 413) appear in no Task 1–19 `Files:` block (verified against the whole plan).
- Tasks 1–19 numbering/titles/dependencies unchanged: **not independently verifiable** (no VCS baseline available). Internally self-consistent: the Step-to-Agent Map (lines 431–450) matches the task headings and the dependency edges are monotonic.
- **Defect:** Task 20's *operations* contradict its declared ownership. Interfaces line 414 and Acceptance line 415 and Step 3 (line 421) require `python3 scripts/sync.py` to "re-embed the new `{{AGENT_META_VERSION}}` in generated artifacts". Those version-bearing artifacts include `AGENTS.md` and generated agent files owned by **Task 15** (line 350), because `{{AGENT_META_VERSION}}` is substituted into context headers and agent bodies (`scripts/lib/context.py:471`, `scripts/lib/standalone.py:188/249`, `templates/context/partials/header.md:9`, `agents/1-generic/agent-meta-scout.md:80`, `agent-meta-manager.md:420`). The Graph-Validation claim `{"safe":[all 20], "conflict":[]}` / "no file overlap" (lines 505, 507) is therefore unsound for the actual writes, and Global Constraints line 84 ("no file appears in two tasks' `Files:` blocks") is breached in effect. See MAJOR-1.

### Check 5 — No contradiction with Resolved-decisions / AC list / §14 — PARTIAL
- Resolved decisions: OQ-1 (line 19) and OQ-8 (line 26) match the amended §2.1/§11. OK.
- AC list: AC-9 (line 465) correctly builds on `agent-discovery`; AC-5 (line 461) cross-refs N7. **AC-22 (line 478) still states unconditionally** that after one sync the "Copilot/Antigravity" new path exists and old is gone — false for Antigravity at the default `agent-discovery: false`. See MINOR-2.
- §14 self-review: line 664 claims the ADR log is "ADR-1…ADR-10" while §12 holds ADR-1…ADR-15. See MINOR-4 (possibly pre-existing; not attributable to Step 1 with certainty).
- Plan Global Constraints line 81 "commit (Task 16) last" is stale after appending Task 20. See MINOR-4.

### Check 6 — Findings — see below.

## Findings

### MAJOR-1 — Task 20's declared ownership is incomplete (regenerated version artifacts escape its `Files:` set)
- **Dimension:** Consistency / Feasibility (plan integrity, ownership).
- **Evidence:** plan line 413 (Files: only `VERSION`, `CHANGELOG.md`, `.meta-config/project.yaml`, `README.md`) vs. lines 414–415 and 419–423 (Task 20 re-runs `sync.py` and "re-embeds the new `{{AGENT_META_VERSION}}` in generated artifacts"); Task 15 line 350 owns `AGENTS.md` + the generated agent dirs; version embedding proven by `scripts/lib/context.py:471`, `scripts/lib/standalone.py:188/249`, `templates/context/partials/header.md:9`, `agents/1-generic/agent-meta-scout.md:80`.
- **Consequence:** after Task 15/16 have regenerated and committed the artifacts, Task 20's release sync re-writes `AGENTS.md` and version-bearing generated agent files **outside its declared set**; the release commit then contains files owned by Task 15/16. The graph-validation/re-check statements (lines 505, 507) assert an overlap result that does not hold for the operations.
- **Fix:** reconcile ownership. Either (a) let Task 20 explicitly declare the version-bearing regenerated paths (`AGENTS.md`, the generated agent/context dirs) and remove those paths from Task 15's ownership / make Task 20 the single regenerator of version-bearing files; or (b) drop the re-sync/re-embed from Task 20 and assign it to a dedicated task whose `Files:` set covers the outputs. In either case update the Graph-Validation bullets so the disjointness claim matches the actual writes.

### MINOR-1 — §13.2 risk row and plan §Risks still group the MAJOR under "Copilot/Antigravity"
- **Dimension:** Consistency (SemVer).
- **Evidence:** spec line 641 ("Major-Bump für Pfadänderungen (Copilot/Antigravity) … an un-migrated project would leave orphaned old paths"); plan line 546 ("a major bump for Copilot/Antigravity"). §11 lines 562–563 say only Copilot is MAJOR/default-on; Antigravity is MINOR and default-off (nothing moves by default).
- **Fix:** attribute the MAJOR to Copilot only; split the row (Copilot = default-on MAJOR; Antigravity = flag-gated MINOR, risk only when `agent-discovery: true`).

### MINOR-2 — AC-22 states Antigravity migration unconditionally
- **Dimension:** Consistency (AC list vs. new gating).
- **Evidence:** spec line 478 ("previously received Copilot/Antigravity artifacts … after one real sync: the new path exists, the old path is gone") vs. §2.1 line 141 and §11.1 line 585 (Antigravity `.agents/*` only with `agent-discovery: true`).
- **Fix:** qualify the Antigravity half of AC-22 with "with `agent-discovery: true`" (scenario 68 already sets the flag).

### MINOR-3 — Plan labels N7 "Deferred" while spec §13.3 marks it "Accepted"
- **Dimension:** Consistency (plan/spec classification).
- **Evidence:** plan line 701 ("Deferred (spec §13: Accepted, no task)"), plan line 721 (N7 in the "Deferred register (12)"); spec §13.3 line 648 ("Accepted (out of generator scope)").
- **Fix:** set the plan row's Status to "Accepted — spec §13.3" (and drop N7 from the Deferred register count), or add an explicit one-line note that the plan uses "Deferred" = "Accepted-not-tasked".

### MINOR-4 — Stale cross-references introduced/left by the amendment
- **Dimension:** Consistency.
- **Evidence:** plan line 81 "commit (Task 16) last" (now false; Task 20 also commits); spec §14 line 664 "ADR-1…ADR-10" vs §12 ADR-1…ADR-15 (may predate Step 1).
- **Fix:** reword line 81 to "…; release/version bump (Task 20) last"; update the self-review ADR range.

### INFO-1 — Task 20 is not referenced by any `pipeline_stages` target
- Plan lines 2–7 map only `implement:1`, `validate:17`, `review-req:18`, `review-quality:19`; line 723 documents this as intentional. Recommend confirming the runner executes graph-reachable tasks that are not a stage target, so the MAJOR bump cannot be skipped.

## Verdict

**CHANGES_REQUESTED.** The three intended gaps are substantively closed — the key is
named consistently (Check 1), the SemVer policy is correct and the §11.1 gating is
right (Check 2), N7 is Accepted with rationale + AC-5 cross-reference (Check 3), and
the terminal Task 20 is correctly numbered/dependent (Check 4, partial). However,
**MAJOR-1** (Task 20's operational writes to Task 15-owned, version-bearing artifacts
are undeclared, making the plan's ownership/graph validation unsound) must be resolved
before the plan is dispatched. The remaining MINOR findings are wording/classification
fixes.

---

## Iteration 2 — Re-Review after the CHANGES_REQUESTED fixes (2026-10-01)

> Reviewer: `concept-reviewer`. Subject: the uncommitted Step-1 rework of the spec and
> plan. Method: on-disk re-read of both documents; no shell/`git` available (same
> limitation as Iteration 1 — baseline checks are internal-consistency only).
> **VERDICT: APPROVED** (0 critical, 0 major, 0 minor, 1 info).

### CN-1 — MAJOR-1 (ownership / regeneration) — **PASS**
- **Task 15 (release) no longer runs sync / re-embeds.** Plan:351 ("It does **not**
  re-embed `{{AGENT_META_VERSION}}` … that is Task 16"), plan:352 ("This task MUST NOT
  run `python3 scripts/sync.py` and MUST NOT claim to re-embed the version —
  regeneration is Task 16"), plan:354, Step 3 plan:358.
- **Regeneration is now Task 16 and is the sole writer of generated artifacts,
  including `AGENTS.md` and version-bearing files.** Plan:363 lists all ten `*/agents/`
  dirs **+ `AGENTS.md`**; plan:365 acceptance re-embeds the Task-15 MAJOR version and
  asserts `--check` rc 0; plan:367 runs `sync.py`. Plan:504/506/722 state explicitly
  that "Regeneration (Task 16) remains the sole writer of the generated artifacts".
- **Task 15 `Files:` = {`VERSION`, `CHANGELOG.md`, `.meta-config/project.yaml`,
  `README.md`} (plan:350).** Grep confirms these paths appear in **no** other task's
  `Files:` block, so the set is disjoint.
- **Graph-overlap claim is sound.** `check_plan_file_overlap` widens each set with
  `extract_file_references(task.prompt)` + `resolve_symbol_files(task.prompt)`
  (`file_affinity.py:205-214`), and `_parse_plan_tasks` sets `prompt` = the task
  **title only** (`spec_plan.py:552/564/578`); declared `files_touched` come from the
  `Modify:`/`Create:` markers (`spec_plan.py:567`). All 20 titles are path-free, so
  Task 15's body mention of `python3 scripts/sync.py` does **not** widen its set and
  creates no false conflict with Task 3 (`scripts/sync.py`). The `{"safe":[all 20],
  "conflict":[]}` claim (plan:504/506) holds for the effective input. **PASS.**

### CN-2 — MINOR-1 (SemVer attribution: Copilot MAJOR / Antigravity gated MINOR) — **PASS**
- Spec §13.2 now has two separate rows: "Major-Bump für die default-on
  Copilot-Pfadänderung" (spec:641) and "Flag-gated Antigravity-`.agents/*`-Migration
  (MINOR)" with "risk materialises **only with `agent-discovery: true`**" (spec:642).
- Plan §Risks: intro plan:545 (MAJOR driven by Copilot default-on; "Antigravity is
  flag-gated MINOR — nothing moves by default") and risk row plan:555. Consistent with
  §11:562–563. **PASS.**

### CN-3 — MINOR-2 (AC-22 Antigravity half gated) — **PASS**
- Spec:478 now reads "… Copilot artifacts at the old paths (default-on) and, with
  `agent-discovery: true` …, Antigravity artifacts at the old paths, then after one real
  sync (**the Antigravity half only with `agent-discovery: true`**; the default `false`
  leaves the Antigravity `.gemini/*` paths unchanged)"; the verification column scopes
  67 default-on / 68 flag-on. §10.2 line 531 mirrors the gating. **PASS.**

### CN-4 — MINOR-3 (N7 label / Deferred count) — **PASS**
- Plan:700 Status = "Accepted — spec §13.3"; plan:720 "Deferred register **(11)**" with
  "N7 is **not** in this register — it is recorded as `Accepted — spec §13.3`";
  plan:567 prose; inventory plan:604 "11 `Deferred`". Spec §13.3 (spec:649) Accepted.
  Consistent. **PASS.**

### CN-5 — MINOR-4 (stale cross-references / ADR range) — **PASS**
- Plan:81 now reads "…release bump (Task 15) after all behavior + scenario tasks (1–14)
  and before repo regeneration (Task 16); the regeneration commit (Task 17) last." No
  stale "commit (Task 16) last".
- Spec §14 (spec:665) = "§12, ADR-1…ADR-15", matching §12 ADR-1…15 (spec:593–607).
  **PASS.**

### CN-6 — INFO-1 (non-stage-target release task on the critical path) — **PASS**
- Plan:565 critical path now reads "… Task 14 -> Task 15 (release bump) -> Task 16 ->
  Task 17 -> …"; plan:465/575/722 state Task 15 is a non-stage-target but a hard
  prerequisite of Task 16. Note present. **PASS.**

### Renumber integrity — **PASS**
- Tasks 1–20 present exactly once (`^### Task`: plan:160,173,186,199,213,226,240,254,
  267,282,296,309,322,335,348,361,375,387,400,412).
- All `Depends on` edges point to a lower task number (monotonic, no dangling/cycle):
  2←1, 3←1, 5←4, 6←1,4, 7←4, 8←4, 9←4, 10←4, 11←4, **15←14, 16←15, 17←16, 18←17,
  19←18, 20←19**; 1/4/12 are roots.
- `pipeline_stages` (plan:3–6) `validate:18`, `review-req:19`, `review-quality:20` map
  to Task 18/19/20 ("Full verification gate", "Requirement-trace review", "Quality
  review"); Step-to-Agent Map rows 15–20 (plan:444–449) match the headings. **PASS.**

### New finding
- **INFO-2 (new, non-blocking) — Task 16's `Files:` enumeration may be narrower than
  the stated drift scope.** Plan:140 describes the drift as "~27 files under `.claude/`,
  `.gemini/`, `.agents/`, `.opencode/`, `.continue/`, `.github/`, `.mammouth/`,
  `.codex/`, `.zcode/`, `.kimi-code/` and root context files", whereas Task 16's
  `Files:` (plan:363) lists only the ten `*/agents/` subdirs + `AGENTS.md`. If the 27
  drifted files include non-agent generated artifacts (rules/skills/commands/MCP
  configs), Task 16 writes outside its declared set. This is **pre-existing** (old
  Task 15 carried the identical declaration) and does **not** break the overlap result
  (`{"safe":[…], "conflict":[]}` still holds, because no other task owns those paths),
  hence non-blocking. Fix: at dispatch, confirm the 27 files are confined to `*/agents/`
  + `AGENTS.md`, or broaden Task 16's `Files:` to the full generated-managed set.
  Cannot be confirmed from here (no shell/`git`; the evidence file does not enumerate
  the 27 paths).

### Verdict
**APPROVED.** The MAJOR-1 ownership defect is resolved structurally (release no longer
writes generated artifacts; regeneration is the single writer and owns `AGENTS.md` +
the version-bearing agent dirs); the graph-overlap claim is sound for the effective
`files_touched` input. All four MINOR findings are closed, renumbering/topology and
`pipeline_stages` are consistent, and the only residual item (INFO-2) is a non-blocking
dispatch-time ownership confirmation.
