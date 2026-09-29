# OpenCode Runtime Gate (Problem A) — Spec Re-Review (iteration 2)

> Reviewer: `concept-reviewer` · Date: 2026-09-14
> Target: `docs/specs/2026-09-13-opencode-runtime-gate-design.md`
> Prior review: `docs/specs/2026-09-13-opencode-runtime-gate-review.md` (F-01 … F-12)
> Support: `docs/specs/2026-09-13-opencode-runtime-gate-system-design.md`
> **No `Status: APPROVED` marker was set. Spec remains `status: Entwurf`.**

## Verdict: APPROVED-FOR-USER-APPROVAL

All twelve prior findings are independently resolved against the code, not
merely by the author's summary. No new BLOCKER/MAJOR finding. The spec is ready
for the explicit user approval gate; approval itself remains a separate user
step and was deliberately not set here.

## Per-finding resolution (independently verified)

| ID | Resolved? | Evidence |
|----|-----------|----------|
| F-01 (BLOCKER) | YES | Current writers confirmed defective: `isolation.py:111` `_read_state` returns only `data.get("isolation-deny", [])`; `:125-132` `_write_state` overwrites the whole `{"isolation-deny": …}` record; `:238-241` calls `.items()` unconditionally on `permission.read`/`edit` (raises on scalar). Spec now fixes all three: mapping-form deny `{"**":"deny"}` disjoint from `_dir_to_glob` output (`**/file`, `dir/**`) (IC-09 :444-451); `_read_state`/`_write_state` namespaced (`isolation-deny`, `runtime-gate-deny`) with read-modify-write preserving siblings (:415-422); scalar tolerance via `_permission_mapping` (:424-426, :452-458); ownership/rollback (:459-467); writer order stage 6 → stages 8+9 (:468-475); AC-10 repaired (:818-830); AC-23 added (:867-878); OQ-11 resolved (:974-987). Backward-compatible signatures keep existing positional callers working. |
| F-02 (MAJOR) | YES | Verified the codebase: `agent_sync._build_provider_vars` is called only from `sync_agents_for_provider` (`agent_sync.py:423,883`); neither renderer consumes it. `rules.py:254` returns `{**variables, **provider_vars}`; `context.py:1096` starts from `dict(variables)`, and `_sync_opencode_context` passes `variables` straight to `_build_managed_block` (`context.py:585-588`). IC-04 now injects via `provider_variables.update(runtime_gate_vars(...))` at `_sync_stage_contexts` before `sync_context_for_provider` (`sync_pipeline.py:349-360`) and at `_sync_stage_per_provider` before `sync_rules`/`sync_embedded_rule_files` (`:631-692`). Datenfluss §2 retargeted. Propagation is real. |
| F-03 (MAJOR) | YES | P6 gate narrowed (Scope :35-44; Phase-1 header :882-884; Datenfluss §3 :726-733). Only tier flip + `MODE=enforce` + AC-21 gated; AC-16…AC-20, AC-22 implementable in observe mode. |
| F-04 (MAJOR) | YES | Phase-0 claim narrowed to the *plugin* runtime API (:25-34); AN-6/OQ-3 and AN-3/OQ-4 documented as Phase-0 risks with the fine-glob fallback. |
| F-05 (MAJOR) | YES | IC-07 `GATE_ENFORCED` now verbatim `# CRITICAL GATE` + `… ALLES -> \`orchestrator\`. Keine Ausnahmen.` (:335-337), byte-identical to `rules/1-generic/use-orchestrator.md:2-3`; AC-05/AC-15 assert it. |
| F-06 (MINOR) | YES | AC-02 plugin clause qualified `and not provider_hooks_supported(pc)` (:765-768). |
| F-07 (MINOR) | YES | IC-13 dispatch pinned to `provider_runtime_gate_tier(pc, caps) == "permission"` (:557-565); `isolation-mechanism` explicitly not used. |
| F-08 (MINOR) | YES | IC-16 typed root key (`enum: [observe, enforce]`, `additionalProperties: false`, :608-620) + AC-24 (:926-933); root `additionalProperties: true` at `project-config.schema.json:2297` confirmed. |
| F-09 (MINOR) | YES | `all_providers_runtime_gate_supported` dropped, rationale + future mirror named (IC-03 :252-256); no residual reference in the spec. |
| F-10 (MINOR) | YES | Revision-table row reworded, no self-contradiction (already fixed in R1). |
| F-11 (INFO) | YES | System-design `### Revision` note added pointing at spec D-C1…D-C5 (`…-system-design.md:27-32`). |
| F-12 (INFO) | YES | `agent_meta_root` is an explicit parameter of the two new isolation symbols (IC-09 :428-442) and of `check_orchestrator_strict_hook_support(...)` with caller `consistency-check.py:266-267` named (IC-11 :520-524). |

## New findings

None (no BLOCKER/MAJOR). The fix introduced no contradiction, no unresolved
placeholder, and no provider-name branch: `load_provider_capabilities` returns
the per-provider capability block (`providers.py:120-134`), matching the
`capabilities.runtime_gate` lookup, and IC-13 keys off the resolver output plus
`has_plugins`, never a provider literal.

## Direct edits

None — no pure-editorial defect was found. The concept was not modified.

## Approval-marker confirmation

- Frontmatter `status: Entwurf` intact (`…-design.md:4`).
- No `Status: APPROVED` marker exists. The only occurrence of that string states
  that it is *not* set by the document (`:13`).
- The `## Trace-Anker` section and `spec-id: SPEC-OPENCODE-RUNTIME-GATE-2026-09-13`
  are present and intact.
