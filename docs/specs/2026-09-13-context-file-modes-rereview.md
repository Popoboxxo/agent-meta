# Context-File Modes — Spec Re-Review (independent critic, iteration 2)

> Reviewer: `concept-reviewer` · Date: 2026-09-14 · Branch: `feat/spec-plan-workflow`
> Target: `docs/specs/2026-09-13-context-file-modes-design.md`
> Prior review: `docs/specs/2026-09-13-context-file-modes-review.md` (F-01 … F-10)
> Support: `docs/specs/2026-09-13-context-file-modes-system-design.md` (authoritative design)
> **No `Status: APPROVED` marker was set. The spec remains `status: Entwurf`.**
> Method: independent re-verification of every claimed resolution against the real
> repository (code + config + tests read at the revision on this branch). The design's
> own assertions were not treated as evidence.

## Verdict: APPROVED-FOR-USER-APPROVAL

All four MAJOR findings (F-01 … F-04) and all six MINOR findings (F-05, F-07 … F-10;
F-06 was fixed editorially in the prior round) are **resolved and independently
confirmed against the code**. The Phase-0 determinism guarantee is now correctly
scoped, the adapter render switch is on the real dispatch seam (not the legacy-cleanup
resolver), the Phase-0/1/2 gating is clean, AC-06 still guarantees `--check` rc 0, and
the newly added AC-25/AC-26 are testable and mapped. One **MINOR, non-blocking** new
finding (N-01) is reported below; it does not affect the Phase-0 fix or the shipped
guarantee. The spec is ready for the user approval gate.

## Per-finding resolution (verified against code)

| F-id | Sev. | Resolved? | Evidence (spec + independent code check) |
|------|------|-----------|------------------------------------------|
| F-01 | MAJOR | **YES** | Scoped-guarantee option (a) implemented consistently: IC-03 "Neutralisation scope" (`design.md:289-299`) + "Determinism definition (scoped)" (`:305-314`), Ziel §2 (`:148-152`), AC-07 (`:669-679`), new AC-25 (`:692-703`), R7 (`:986-993`), OQ-13 `[User approval]` (`:953-963`). The three non-neutralised inputs are named and match the code exactly: `context.py:1131` (`ORCHESTRATOR_INVOCATION_HINT`), `:1133-1136` (`ORCH_MODE_*`), `:1141` (`REPO_CONTAINMENT_*`) — verified by reading `scripts/lib/context.py:1118-1141`. Internal consistency with AC-06 confirmed: this repo has **no** divergent non-gate override (`.meta-config/project.yaml:304-317` has `orchestrator.mode: strict`, **no** `provider-overrides`; no `repo_containment` provider override), so the narrow guarantee suffices for rc 0. (One precision caveat → N-01.) |
| F-02 | MAJOR | **YES** | IC-08 is explicitly narrowed to legacy cleanup (`design.md:413-434`: "This function is not on the render path"), and IC-09 now owns the render switch (`:436-479`: "Target selection (this is the render switch, F-02)"), naming the readers `_sync_opencode_context` (`context.py:553`, reads `pc["context_file"]` `:566`) and `_sync_managed_block_context` (`:483`, reads `pc.get("context_file")` `:496`). Independently verified: `resolve_context_filename` is imported at `sync_pipeline.py:98` and called **only** at `:445`/`:455` inside `_sync_stage_legacy_cleanup` (repo-wide grep); no render path calls it. AC-13 (`:734-746`) is bound to the file the dispatch actually writes. |
| F-03 | MAJOR | **YES** | AC-06 (`:658-668`) reduced to the AC-05 unit repeated dry-run + committed-`AGENTS.md` `--check` rc0; the scenario assertion is explicitly excluded and moved to AC-21 (`:818-827`, Phase 2). AC-17 (`:772-780`) no longer depends on IC-13/AC-24: "The size-guard counting of adapters is **not** part of this Phase-1 criterion — it belongs to Phase 2 (IC-13/AC-24, F-03)." Phase-0 list (`:61-62`) = AC-01…AC-09 + AC-25; no Phase-0 AC references scenario 63 or the size guard. |
| F-04 | MAJOR | **YES** | IC-09 "Claude carrier (F-04)" (`design.md:481-491`) now states Claude is `context-managed-block` (`config/ai-providers.yaml:24`, verified), that `templates/context/claude-managed.md` has no `GATE_*` (verified: only `{{PROVIDER_ROUTING}}`/`{{AGENT_HINTS}}`), that the hook wording lives in `.claude/rules/use-orchestrator.md:1` (verified `# CRITICAL GATE`), rendered by `sync_rules` (`sync_pipeline.py:782`) with vars injected at `:748` (both verified). AC-14 (`:747-760`) observable changed to "the Claude provider surface contains the verbatim hook wording", not the `CLAUDE.md` managed block. |
| F-05 | MINOR | **YES** | IC-02 (`design.md:232-245`, `:251-256`) uses `provider_config.get(u, {})` and `(capabilities_config or {}).get(u)`; non-dict → `{}` → `advisory`, never raises. AC-02 (`:624-631`) asserts the same. |
| F-07 | MINOR | **YES** | Refreshed and verified: `_sync_stage_contexts` `:328-378` with loop `:345-377` (`sync_pipeline.py`, verified), `cli_commands.py` print `:1218` / exit `:1219` (verified), rules seam `sync_pipeline.py:748` added to the impact table (`design.md:867`) and consumed by `sync_rules` `:782` / `sync_embedded_rule_files` `:796` (verified). |
| F-08 | MINOR | **YES** | AC-13 (`design.md:734-746`) is scoped to the resolved adapter set (Claude→`CLAUDE.md`, Gemini→`GEMINI.md`, rest direct readers) and explicitly does **not** assert the Antigravity dual-reader; that sub-case lives entirely in OQ-3 (`:911-918`). |
| F-09 | MINOR | **YES** | `context_mode` no longer appears in IC-02: `design.md:257-258` ("`context_mode` is **not** declared here — it is a Phase-1 symbol, declared solely in IC-05 (F-09)"); sole declaration in IC-05 (`:325-339`). |
| F-10 | MINOR | **YES** | IC-07 adds `context_adapter_settings` (`design.md:392`, `:398-402`); IC-09 names the provider-native settings write, capability/`settings_file`-gated (Gemini `context.fileName` in `.gemini/settings.json`) (`:465-471`); new AC-26 observes activation or default-context-file semantics (`:787-797`). |
| F-06 | MINOR | **YES (prior round)** | Required headings intact: `## Ziel` (`:144`) and `## Nicht-Ziele` (`:161`) satisfy `REQUIRED_SPEC_SECTIONS` (`scripts/lib/consistency/spec_plan.py:31-35`). |

No MAJOR finding was silently redesigned; the resolution rows in the spec
(`design.md:82-95`) match the actual text.

## Checks (task items 1–6)

1. **F-01 narrowed guarantee internally consistent — PASS (with N-01).** The scoped
   wording is repeated consistently in IC-03, Ziel, Datenfluss §1 (`:572-575`), AC-07,
   AC-25, R7 and OQ-13. The remaining divergence sources it names (`ORCH_MODE_*`,
   `REPO_CONTAINMENT_*`) are real: `use-orchestrator.md:1` consumes `ORCH_MODE_STRICT`,
   `repo-containment.md:3-4` consumes `REPO_CONTAINMENT_ENABLED`/`REPO_CONTAINMENT_BLOCK`
   (verified). `orchestrator_hint` is the exception → N-01.
2. **AC-06 still guarantees `--check` rc 0 for Phase-0 — PASS.** The criterion
   (`design.md:658-668`) still requires `sys.exit(0)` with the committed canonicalised
   `AGENTS.md`; `cli_commands.py:1209-1219` confirms rc0 on zero actions. Only the test
   *location* changed (scenario removed); the guarantee was not weakened.
3. **Phase-0 vs Phase-1/2 gating clean — PASS.** Audit of every Phase-0 AC
   (AC-01…AC-09, AC-25): none references a deferred artifact. AC-09's conditional
   mention of `consistency/context_mode` ("is added if that module exists") creates no
   dependency. AC-25 only uses the new Phase-0 test module.
4. **New ACs testable and mapped — PASS (N-01 caveat).** AC-25 and AC-26 each name a
   concrete test and are listed in their phase scopes (`:61-62`, `:67-68`). AC-26's
   real-repo verification task is explicit and appropriately Phase-1.
5. **`status: Entwurf` intact; no `Status: APPROVED` — PASS.** Frontmatter `:4` is
   `status: Entwurf`. The string `Status: APPROVED` appears only in explanatory prose
   (`:14`, `:1001`); neither matches the approval-marker regex
   (`spec_plan.py:70-72`). No approval marker was written by this review.
6. **No unresolved placeholders — PASS.** No `TODO`/`TBD`/`<platzhalter>`/standalone
   `...` line/empty `Interfaces:` (`spec_plan.py:73-82`). `{{...}}` occurrences are
   quoted template placeholders inside interface contracts, not spec placeholders.

## New findings (iteration 2)

| ID | Severity | Location | Issue | Suggested change |
|----|----------|----------|-------|------------------|
| N-01 | MINOR (non-blocking) | IC-03 `neutralisation scope` (`design.md:294`), Datenfluss §1 `:573`, AC-07 `:677`, AC-25 `:697`, R7 `:989`, OQ-13 `:955` | **`orchestrator_hint` is listed as a divergence source although `ORCHESTRATOR_INVOCATION_HINT` has no consumer.** `local_vars["ORCHESTRATOR_INVOCATION_HINT"] = pc.get("orchestrator_hint", "")` (`context.py:1131`) is set, and Opencode/Gemini carry different `orchestrator_hint` values (`ai-providers.yaml:138` vs. `:212`), but a repo-wide search finds **no** `{{ORCHESTRATOR_INVOCATION_HINT}}` in any rule/template (`rules/`, `templates/`, `agents/`); it is only *assigned* (`context.py:1131`, `rules.py:227/249`). A differing `orchestrator_hint` therefore cannot make the two shared renders differ, so AC-25's "… or a differing `orchestrator_hint` … then the renders differ" is not satisfiable for that input and R7/OQ-13 over-state the limitation. Direction is conservative (documenting more limitation than exists), so the Phase-0 fix and AC-06 are unaffected. | Drop `orchestrator_hint` from the divergence enumerations (IC-03/Datenfluss/AC-07/AC-25/R7/OQ-13), or annotate it as a currently-unrendered/reserved variable that does not itself cause divergence. Keep `ORCH_MODE_*` and `REPO_CONTAINMENT_*`, which are consumed. |

No other new contradiction, gap or placeholder was found. AC-25 saying the remaining
non-gate inputs are "the sole remaining provider-scoped inputs" remains a readable
(i.e. currently unused) variable set; AC-25/AC-26 stay testable once N-01 is trimmed.

## Direct edits

None. No editorial issue required a change; the spec was left untouched.

## Confirmations

- **No `Status: APPROVED` marker was set.** `docs/specs/2026-09-13-context-file-modes-design.md`
  remains `status: Entwurf`; approval remains a separate user gate. This review wrote
  only this report file.
- Scope respected: no implementation, no plan, no code, no REQ-IDs; no handoff to
  `requirements` (spec-review mode). On user approval the orchestrator would advance
  `quality_pipelines.concept-driven-dev` (`specify → review → approve → plan`).
