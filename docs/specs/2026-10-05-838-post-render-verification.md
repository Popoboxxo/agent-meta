---
spec-id: SPEC-838-POST-RENDER-VERIFICATION-2026-10-05
title: Post-Render Verification Stage — Mini-Spec / Design Note
status: proposed
related-issue: "#838"
instances: ["#834", "#835", "#836"]
related: ["#802", "#680"]
---

# Post-Render Verification — Spec

> Status: **Entwurf** (Frontmatter `status: proposed`) — nicht freigegeben; Approval-Marker
> maschinenlesbar: erst `Status: APPROVED (Datum)` gibt frei (Approval-Gate, §7.1).
> Trace anchor: `spec-id: SPEC-838-POST-RENDER-VERIFICATION-2026-10-05`; a plan derived from this note MUST reference it.
> Provider-agnostic: dispatch on resolved config values (`has_agents`, `agents_dir`, …), never on a provider-name literal.

## 0. Phasing (binding; overall L/XL — requires a plan)

Each phase ships independently; implementation MUST NOT start before an approved plan.

- **Phase 1 (S/M) — P3 only.** `unresolved-placeholder` over the existing managed-index set, reusing `check_placeholders` + `warn_unresolved_platform_vars`; default `warn`, no new abstraction/instrumentation. Closes #834; documents the #802 gap.
- **Phase 2 (M/L) — P1 + verify set.** Pin the reference grammar/exemptions, then `path-existence` over §2.2; promote P1 to `error` only under `--validate` after clean consumer fixtures. Closes #836.
- **Phase 3 (M) — P2 (+ P4 after #680).** Needs the per-row `optional` marker (§2.5); P4 stays `warn` until #680's data lands. Closes #835.

## 1. Problem / Ziel / Nicht-Ziele

**Problem.** No stage reconciles rendered on-disk content with deployment reality (active providers/presets, existing roles/paths). Rendering can silently drift — a reference points at a never-produced path, a role is advertised in a generated directory table but has no file in an active `agents/` dir, or a placeholder survives substitution — and the broken content is then captured into the generated-file hash baseline, cementing the drift. #834/#835/#836 are one class.

**Ziel.** Close the class: one central read-only post-render verification stage validating the rendered artifacts against the resolved provider set **before** the hash baseline is captured, so drift cannot be frozen into the baseline.

**Nicht-Ziele.** Not fixing instances individually (each is a fixture). #680 is the complementary **data-side** fix — an input, not a substitute. No replacement of the generated-file drift scan. No provider-name branches; no new provider; no writer instrumentation (§2.2).

## 2. Proposed Solution

### 2.1 Stage placement + true reachability

- **Real sync** (`scripts/lib/cli_commands.py::_handle_sync`): insert `post_render_verify` between the writer stages and stage 13 `_sync_stage_generated_file_hash_capture` (`cli_commands.py:1192`; `_sync_stage_config_audit` at `:1189` is the last writer-side call).
- **`--check`:** matches no mode handler and falls through `_dispatch` (`sync.py:657-663`) into `_handle_sync` with `args.dry_run` forced on (`sync.py:99-105`); writers do not write, so a write-scoped stage would be **vacuous**. The feasible `--check`/`--validate` integration is the existing read-only artifact gate `_run_artifact_gate` (`sync.py:108-134`), which runs for both flags and reads artifacts **on disk**; Phase 1/2 extend it with P1/P3.
- **`--validate`:** `_run_consistency_checks` (`cli_commands.py:151`) is called only inside `_handle_validate` (`:1016`, call `:1032`) — **not** under `--check`; predicates may also be wired into that report.
- **#802 (accurate dependency):** verifying the *planned* render (nothing written) needs a run-scoped planned set that does not exist today and is **out of scope**; #802 is its prerequisite. Until then, `--check` verifies the already-on-disk artifacts only.

### 2.2 Inputs — the verify set (no run-scoped write set)

No `RenderWriteSet`, output plan, or run-scoped write-set abstraction exists today (`write_checked` at `io.py:414` carries no `provider`/`kind`/`optional` metadata; ~30 writers bypass it). This spec does **not** assume one. The verify set is **derived post-hoc from the rendered content on disk plus the known writer output set**:

- **File set:** `generated_file_drift._iter_managed_files` (`generated_file_drift.py:237`) — the same managed-index-derived set the hash baseline uses, walked per active provider (not a static hardcoded list; reflects current managed artifacts).
- **Metadata** is derived during the walk, never carried on write calls: `provider` = walk loop variable; `kind` = matching `dir_spec` (`agents_dir`/`rules_dir`/…/pipeline-details, capability-gated by `has_hooks`/`has_rules`/`has_commands`/`has_plugins`); `optional` = §2.5.
- **Content:** each walked file is read and parsed for referenced paths/roles/placeholders.

**Instrumentation needed? None for Phases 1–3.** Metadata is derivable from resolved config and the walk; `optional` lives in template/table data (§2.5), not in writer calls. Instrumenting writers would only enable a pre-write *planned* set for `--dry-run`/`--check`; deferred to #802.

### 2.3 Predicates

| ID | Predicate | Checks | Default severity |
|----|-----------|--------|------------------|
| P1 | path-existence | Every repo-local referenced path resolves (markdown links, backticked paths, import references). External URLs/anchors/OS paths outside the repo are out of scope. | `warn` (promote §2.4) |
| P2 | directory-table | Every role listed in a generated directory table for a capable provider has a file in that provider's `agents_dir`. **Direction: listed → must exist only.** | `error` under `--validate` |
| P3 | unresolved-placeholder | No `{{...}}` / `{{#if}}` residue survives. **Reuses** `consistency/placeholders.py::check_placeholders` (`:148`); generalizes the split diagnosis of `platform.py::warn_unresolved_platform_vars` (`:147`) from `platform_vars` to the resolved variable registry. | `warn` |
| P4 | skills | Skill references resolve against the active skill registry (#680 data-side). | `warn` until #680 |

### 2.4 Severity model + abort semantics

Per-predicate severity `off | warn | error`, read from resolved config under a `post-render-verify` map. **Mode-dependent defaults:** consumer sync (`_handle_sync`) defaults all predicates to **`warn`** — a healthy consumer sync must never abort on a false positive; framework `--validate` (full sync into the disposable test repo) defaults P1–P3 to **`error`** (fail-fast). Explicit config overrides win in both modes.

**No baseline desync.** `error` raises before stage 13, so no baseline is written for that run. Consumer sync defaults to `warn`, so healthy syncs never abort. When a predicate is *explicitly* promoted to `error` (or under `--validate`), writers have already written, but the baseline stays untouched and the next sync is idempotent (re-render → verify → stage 13); recovery is a re-run, and `--validate` targets a disposable repo. Verify-then-baseline per artifact is a Phase-2 option.

### 2.5 Suppression / expected-incomplete channel (RVW-3/RVW-8)

Legitimate capability-gated or feature-flag-filtered artifacts must produce **0 findings**. The marker lives in the **template/data**, not in the assertion scope:

- The directory-table **row datum** carries `optional_for: frozenset[str]` — provider keys for which the row is legitimately absent, sourced from resolved capability (`has_agents` false) and feature flags; the generated table emits it per row as `<!-- verify:optional providers=<comma-list> -->`.
- P2 suppresses a row **only** when the active provider key is in its `optional_for` and the provider's resolved `has_agents` is false. A capable provider with a required (unmarked) role and no file is exactly **#835** and MUST fire.
- P1/P3 validate content of present artifacts regardless of the marker (marker suppresses *absence*, not *content*).
- Not circular: `optional_for` is authored from capability/feature config, not from the render-time materialisation resolver.

## 3. Interface Contracts

- `lib/verify.py::VerifySet` — post-hoc, built by walking `_iter_managed_files` per active provider; no writer instrumentation. `iter_artifacts() -> tuple[Artifact, ...]`.
- `lib/verify.py::Artifact` — frozen dataclass: `path: Path`, `provider: str`, `kind: Literal["agent","rule","context","command","skill","hook","mcp","pipeline-details","managed-index","other"]`, `optional_for: frozenset[str] = frozenset()`. `kind` is set only by the walk (dir_spec); `managed-index` maps to P3.
- `lib/verify.py::VerifyFinding` — frozen dataclass: `predicate` (`path-existence|directory-table|unresolved-placeholder|skills`), `severity: Literal["warn","error"]`, `artifact: Path`, `message: str`, `cause: Literal["missing-from-config","substitution-not-applied","missing-path","missing-role"]`. One cause class per predicate (P1→`missing-path`, P2→`missing-role`, P3→`missing-from-config`|`substitution-not-applied`, P4→`missing-path`).
- `lib/verify.py::post_render_verify(verify_set, active_providers, config, project_root, log) -> tuple[VerifyFinding, ...]` — filesystem-read-only; raises `SyncError` iff a finding has `severity == "error"`.
- `lib/verify.py::resolve_severities(config, mode: Literal["sync","validate"]) -> dict[str, Literal["off","warn","error"]]` — implements §2.4; P3 delegates to `check_placeholders`.

## 4. Datenfluss

Resolved config + active providers/presets → writer stages → post-render walk of `_iter_managed_files` → `VerifySet` (derived `provider`/`kind`/`optional_for`) → `post_render_verify` reads each artifact + parses content → P1–P4 findings → `off` skipped / `warn` logged / `error` raises `SyncError` before hash capture → on success stage 13 captures the baseline. `--check`/`--validate`: `_run_artifact_gate` over on-disk artifacts; no writes, no baseline.

## 5. Acceptance Criteria

1. **Placement.** A real sync runs the stage after all writers and strictly before `_sync_stage_generated_file_hash_capture`; an `error` finding prevents any baseline write.
2. **Verify-set scoped.** Findings reference only artifacts in the §2.2 managed-index-derived set for active providers (the set stage 13 baselines) — not a static hardcoded list.
3. **Class reproduction.** One fixture each for #834/#835/#836 fires the matching predicate (`unresolved-placeholder` / `directory-table` / `path-existence`).
4. **Diagnostic split.** A missing-config placeholder and a not-applied substitution produce two distinct, non-merged causes.
5. **Direction.** A file present in a capable provider's `agents_dir` but absent from the table produces zero findings.
6. **Clean sync.** On the framework's consumer fixture with default severities, zero `error`.
7. **Configurable severity.** Each predicate can be `off`/`warn`/`error`; the resolved value is honoured (`off` emits nothing, `warn` never aborts).
8. **`--check` reachability (corrected).** Reachable under `--check`/`--validate` via the read-only `_run_artifact_gate` over on-disk artifacts; a planned-render gate under forced dry-run is out of scope and documented as the #802 dependency here and in #838.
9. **Invariant regression test.** Asserts invariants (finding presence/absence, causes, scope) — never exact rendered bytes or hashes.
10. **Suppression.** A row whose `optional_for` contains the active provider yields zero findings; an unmarked required role with a capable provider and no file yields a finding.

## 6. Dependencies / Relations

- **#834** — misattribution instance; P3 fixture origin. **#835 / #836** — same class (P2 / P1).
- **#802** — prerequisite for a planned-render `--check` gate; until landed, the gap is documented (AC-8). Not a blocker: on-disk verification works today.
- **#680** — complementary data-side; when its data lands, P4 can be promoted from `warn`.

## 7. Test Strategy

Fixture consumer layout under `tests/`; one sync run through `scripts/sync.py` plus a `--check`/`--validate` run; assert structured `VerifyFinding` results (predicate, cause, scope), never bytes: one regression test per instance, one clean-sync zero-error test, one suppression test.

## 8. ADR — Central stage before the hash baseline

**Context.** Drift is captured into the generated-file baseline before content is reconciled with reality; point-fixes per instance do not close the class.
**Decision.** One central read-only `post_render_verify` stage before hash capture, over the managed-index-derived verify set + resolved provider set, with mode-dependent per-predicate severity and a template-data suppression marker. No writer instrumentation.
**Consequences.** A bad render cannot be baselined; predicates are independently tunable; one extra read pass. Trade-off: the verify set is post-hoc, so it matches baseline semantics but cannot see a planned-but-unwritten render — deferred to #802.

## 9. Offene Fragen + Risiken (inkl. Threat Model)

**Offene Fragen.** (a) P1 reference syntax scope (markdown links vs. backticks vs. imports; exemptions for project-local optional user files). (b) P2 coverage (only `AGENT_TABLE` or every generated directory-style table). (c) P4 promotion after #680. (d) `--dry-run`/`--check` planned set — resolved by #802, out of scope here.

**Threat Model (4 questions).** (1) *Building:* a read-only post-render gate that reads written artifacts and can abort a sync; no network, auth, or data storage. (2) *Go wrong:* a false positive aborts a valid consumer sync (availability) and leaves a stale baseline until the next run; large/deep reference graphs slow the pass. (3) *Mitigations:* consumer-sync defaults `warn`; scope strictly to the managed-index set; bound scan depth/size; never execute/import referenced content; explicit severity overrides (`error` under `--validate` only). (4) *Consequences:* at worst broken consumer CI if a user opts into `error` with a bad predicate plus repeated drift backups; no remote-code-execution, privilege-escalation, or data-exfiltration path.

**Risiken.** False positives on consumer projects with intentional external/optional references (→ P1 default `warn` until grammar pinned); duplicate diagnostics with the existing placeholder check (→ P3 reuses it, §2.3); performance on large trees (→ scoped verify set).

## 10. Code-Anker

- `scripts/lib/cli_commands.py` — `_handle_sync` stages, stage 13 call (`:1192`); `_run_consistency_checks` (`:151`, called only `:1032` inside `_handle_validate` `:1016`).
- `scripts/sync.py` — `_run_artifact_gate` (`:108`, runs for `--check`/`--validate`); `--check` forced dry-run (`:99-105`); dispatch fallthrough (`:657-663`).
- `scripts/lib/generated_file_drift.py` — `_iter_managed_files` (`:237`).
- `scripts/lib/consistency/placeholders.py` — `check_placeholders` (`:148`).
- `scripts/lib/platform.py` — `warn_unresolved_platform_vars` split (`:147`).
- `scripts/lib/pipelines.py` — `SyncError` precedent (`:97`, `:105`).
- `scripts/lib/crossrefs.py` — optional-tier table handling (`:133-137`).
