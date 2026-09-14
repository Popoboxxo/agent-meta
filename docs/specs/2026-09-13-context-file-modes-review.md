# Context-File Modes (unified / per-provider) — Spec Review (independent critic)

> Reviewer: `concept-reviewer` · Date: 2026-09-14 · Branch: `feat/spec-plan-workflow`
> Target: `docs/specs/2026-09-13-context-file-modes-design.md`
> Support: `docs/specs/2026-09-13-context-file-modes-system-design.md` (authoritative design), `docs/specs/2026-09-13-opencode-runtime-gate-design.md` (related), `.opencode/skills/spec-plan-workflow/SKILL.md`
> **No `Status: APPROVED` marker was set. The spec remains `status: Entwurf`.**
> Method: independent critic against the real repository (code + config + tests read at
> the revision on this branch), not against the design's own assertions.

## Verdict: CHANGES_REQUESTED

The spec is structurally complete, provider-agnostic, and the Phase-0 mechanism
it describes (**weakest active sharer** replaces the per-provider `GATE_*` in
`_build_managed_block`) genuinely and deterministically fixes the `AGENTS.md`
double-write **for this repository**: no provider-scoped override exists here, so
the two sharer renders become byte-identical and `sync.py --check` converges once
the regenerated file is committed. The interface-contract symbols and the
`Berührter Phase-0-Code` impact table are largely accurate.

It is **not** ready for the user approval gate because:

1. the Phase-0 determinism guarantee is stated unconditionally although IC-03
   neutralises **only** `GATE_*` — other per-sharer variables (`ORCH_MODE_*`,
   `REPO_CONTAINMENT_*`) still diverge and can re-introduce the same rc1 (F-01);
2. the `per-provider` adapter filename switch is wired to a seam that does not
   drive the render (`resolve_context_filename` is used only by legacy cleanup)
   (F-02);
3. Phase-0/Phase-1 acceptance criteria reference Phase-2 artifacts that do not
   exist at that stage (F-03);
4. AC-14's Claude-adapter gate-wording contract contradicts the actual Claude
   render path (F-04).

F-01 … F-04 (MAJOR) must be resolved by the author before approval. F-05 … F-10
are MINOR; F-06 was fixed editorially (see *Direct edits*). No BLOCKER: the
Phase-0 core is sound and nothing in the approach is unsound.

## Scope reviewed

7 dimensions (Completeness, Logic gaps, Unchecked assumptions, Missing
alternatives, Risks, Feasibility, Consistency) + spec-plan §7.1 (Pflichtsektionen,
Trace-Anker, Approval-Marker, No-Placeholder) + the 8 task checks (template
completeness, provider-agnosticism, Phase-0 fix correctness, backward
compatibility, `per-provider` feasibility, AC quality, impact correctness,
honesty/risks).

### Check results (verdict per check)

| # | Check | Result |
|---|-------|--------|
| 1 | Template completeness / frontmatter / Trace / Approval | **PASS w/ F-06** — `spec-id: SPEC-CONTEXT-FILE-MODES-2026-09-13`, title, `status: Entwurf`, `related-spec`, Problem, Ziel, Nicht-Ziele, Interface Contracts (IC-01…IC-13, each `file:Symbol` + signature + error paths), Datenfluss (2 flows), 24 numbered ACs, Offene Fragen + Risiken (OQ-1…OQ-12, R1…R6), Trace-Anker present. No `TODO`/`TBD`/`<platzhalter>`/empty-`Interfaces:` (verified against `scripts/lib/consistency/spec_plan.py:73-82`). F-06: `## Nicht-Ziele` was not a literal required heading; fixed editorially. |
| 2 | Provider-agnosticism | **PASS** — no `if provider == "…"` in any new/changed contract; IC-03/IC-05/IC-07/IC-08/IC-09 are key/capability-driven. `runtime_gate` + `isolation` already in `tests/test_provider_agnostic_dispatch.py:27-51` (`:49`,`:50`), as AC-09 claims. |
| 3 | Phase-0 fix correctness | **PASS for this repo, overclaim in general (F-01)** — verified: `sync_pipeline.py:373-375` injects per-provider `runtime_gate_vars`; `_build_managed_block` (`context.py:1066`) computes `shared_users` at `:1091-1098`, `local_vars = dict(variables)` at `:1118`, rule substitution at `:1235`; `.providers` cycle-free (existing local import `:1171`); `resolve_providers` (`providers.py:175`) → active `{Opencode, Gemini}` → weakest `permission`; second sharer observes equality and hits `log.skip` (`context.py:627`); `--check` maps any action to `sys.exit(1)` (`cli_commands.py:1209-1217`). One UPDATE until the canonicalised `AGENTS.md` is committed (AC-06 correctly states this). |
| 4 | Backward compatibility | **PASS with caveat** — single-provider / same-tier shared groups take the `len(active_shared_users) > 1` guard and are untouched; genuinely different-tier shared groups change content once (documented). Caveat = F-01's un-scoped determinism claim. |
| 5 | `per-provider` feasibility | **FAIL (F-02, F-04, F-08, F-10)** — topology (opencode, KimiCode, ZCode, Antigravity runtime on `AGENTS.md`; Claude `CLAUDE.md`; Gemini `GEMINI.md`) matches the stated verified facts, but IC-08's filename switch does not reach the render path, AC-14's Claude contract is infeasible as written, the Gemini dual-reader cannot be expressed with single per-provider keys, and the `context.fileName` write is unspecified. |
| 6 | AC quality | **FAIL (F-03)** — ACs are testable and named, but AC-06 (Phase 0) and AC-17 (Phase 1) depend on Phase-2 artifacts (scenario 63 / IC-13 size guard). |
| 7 | Impact section correctness | **PASS w/ F-07** — the `Berührter Phase-0-Code` table is substantively correct (`provider_runtime_gate_tier`, `RUNTIME_GATE_TIERS`, `runtime_gate_vars` contract, `sync_pipeline` seam, `isolation.py`, `orchestrator_strict.py` all correctly classified); the committed-behaviour list is honest. F-07: minor line drift and the rules seam (`sync_pipeline.py:748`). |
| 8 | Honesty / risks | **PASS** — Convention-boundary framing explicit; Phase-1/2 adapters labelled HYPOTHESIS with real-repo verification gating; OQs carry recommended defaults; OQ-2…OQ-5 correctly flagged `[User approval]`; R1…R6 honest (incl. R3 residual no-op render and R4 active-set determinism). |

## Findings

| ID | Severity | Location | Issue | Suggested change |
|----|----------|----------|-------|------------------|
| F-01 | MAJOR | IC-03; Datenfluss §1; AC-07; Ziel §2 | **The "one deterministic render" invariant neutralises only `GATE_*`.** `_build_managed_block` still derives three provider-scoped values from the *currently rendering* provider: `local_vars["ORCHESTRATOR_INVOCATION_HINT"] = pc.get("orchestrator_hint","")` (`context.py:1131`), `_orch_mode_flags(_resolve_orch_mode(orch_config, provider_override))` (`:1134-1136`) and `repo_containment_variables(config, provider)` (`:1141`). The embedded `use-orchestrator.md` consumes `ORCH_MODE_*` and the `REPO_CONTAINMENT_*` flags are rendered into the block. If a project sets `orchestrator.provider-overrides.<P>.mode` (or a provider-scoped repo-containment override) differently for two active sharers, the two renders still differ, the second write overwrites the first, and `sync.py --check` returns rc1 again. The spec's own "Determinism definition" ("within a fixed active set the render is stable") is therefore false in that configuration. In this repo no such overrides exist, so the immediate blocker is fixed — but the guarantee as written is not general. | Either (a) scope the invariant and AC-07 explicitly: "deterministic **when the active sharers differ only in gate tier**", and add it as a named risk/OQ; or (b) extend the IC-03 shared override to also neutralise every other provider-scoped input in the shared block (e.g. resolve `ORCH_MODE_*` / `REPO_CONTAINMENT_*` over the active sharer union, or document why those fields must be provider-invariant in a shared file). Add an AC that two active sharers with divergent `orchestrator.provider-overrides` still render byte-identically (or assert the documented limitation). |
| F-02 | MAJOR | IC-08 ("adapter rule"); AC-13; Datenfluss §2; design §5.3 IC-08 | **The adapter filename switch is attached to a seam that does not drive the render.** `providers.resolve_context_filename` is called only from `_sync_stage_legacy_cleanup` (`sync_pipeline.py:445,455`). The actual context render reads the raw key directly: `_sync_opencode_context` uses `pc["context_file"]` (`context.py:566`) and `_sync_managed_block_context` uses `pc.get("context_file")` (`:496`). A change inside `resolve_context_filename` therefore cannot make Gemini render `GEMINI.md`; it only changes which file the legacy-cleanup stage considers "active". AC-13's "when the effective filenames are resolved ... Gemini to `GEMINI.md`" then only exercises a function that is not on the render path, so the test can pass while `per-provider` still writes the wrong file. | Retarget the adapter rule: name the concrete switch in the dispatch (`context.py::sync_context_for_provider` / `_sync_opencode_context`, IC-09) that selects core vs. `context_adapter_file` in mode `per-provider`; explicitly state that IC-08's change only affects `_sync_stage_legacy_cleanup` (orphan protection) and cannot by itself deliver the render. Adjust AC-13 so it asserts the file actually written by sync, not only the resolver return value. |
| F-03 | MAJOR | AC-06 (Phase 0) vs AC-21 (Phase 2); AC-17 (Phase 1) vs IC-13/AC-24 (Phase 2) | **Phase-gating violation: earlier-phase ACs depend on later-phase artifacts.** AC-06 names `tests/scenarios/asserts/63-context-file-modes.sh` as its test, but that assert script, its config and its registry entry are created only by AC-21, which the spec explicitly defers to Phase 2 ("gated/deferred from Phase 0"). Likewise AC-17 (Phase 1) requires the adapter to be "counted by `check_context_file_size` (IC-13)", while IC-13/AC-24 are Phase 2. A Phase-0 sign-off cannot be gated on an artifact that must not exist yet. | Split AC-06: keep the Phase-0 assertion as the unit-level repeated dry-run (AC-05 / `test_repeated_sync_never_reports_pending_agents_md_change` with real `GATE_*` vars) plus the committed-`AGENTS.md` `--check` rc0; move the scenario-63 assertion to AC-21 only. Move the size-guard counting of adapters out of AC-17 into AC-24, leaving AC-17 to managed-index + drift + hash. |
| F-04 | MAJOR | IC-09; AC-14; design §5.1/§5.3 | **The Claude adapter cannot carry the embedded `hook` gate block as AC-14 specifies.** AC-14 requires "the Claude adapter carries the `hook` tier block (`GATE_ENFORCED`, verbatim `# CRITICAL GATE` wording per SPEC-OPENCODE-RUNTIME-GATE F-05/IC-07)". But Claude is a `context-managed-block` provider (capabilities list `config/ai-providers.yaml:74-86`; no `context-embedded-rules`), and its managed block is built from `templates/context/claude-managed.md`, which contains only `{{PROVIDER_ROUTING}}`/`{{AGENT_HINTS}}` — no embedded rules, no `GATE_*` conditionals. In the committed architecture the hook wording for Claude lives in the **native rules file** `.claude/rules/use-orchestrator.md` (verified: line 1 `# CRITICAL GATE`), rendered by `sync_rules` with `GATE_*` from `_sync_stage_per_provider` (`sync_pipeline.py:748`). The spec's IC-09 "adapter = managed block with `runtime_gate_vars` of THIS provider" is therefore not how Claude's gate wording is produced. | State what the Claude adapter actually is and where its hook wording comes from. Either (a) redefine the Claude adapter's carrier as CLAUDE.md→`@AGENTS.md` import **plus** the existing native `.claude/rules/use-orchestrator.md` (rendered at `hook`), or (b) route the adapter render through the embedded-rules path so the block itself carries the `GATE_ENFORCED` wording. Name the changed symbol and adjust AC-14's observable ("the Claude provider surface contains the verbatim hook wording", not "the CLAUDE.md adapter file carries it"). |
| F-05 | MINOR | IC-02 `shared_runtime_gate_vars`; AC-02 | **Fail-safe contract contradicts the pseudocode.** The docstring/error path and AC-02 require an unknown/missing provider entry to count as `advisory` and the function never to raise, but the signature sketch evaluates `provider_runtime_gate_tier(provider_config[u], …)` — a `KeyError` for a provider absent from `provider_config`. | Specify `provider_config.get(u, {})` and `(capabilities_config or {}).get(u)` in the contract (as the design's fail-safe prose already implies) and state that a non-dict entry degrades to `advisory`. |
| F-06 | MINOR | `## Ziel / Nicht-Ziele` heading | **Required-section literal missing.** `REQUIRED_SPEC_SECTIONS` (`scripts/lib/consistency/spec_plan.py:31-34`) matches the literal headings `## Ziel` and `## Nicht-Ziele`; the spec used the combined heading `## Ziel / Nicht-Ziele`, so `## Nicht-Ziele` was absent and the consistency check would emit a required-section finding. | **Fixed editorially** (see *Direct edits*): split into `## Ziel` + `## Nicht-Ziele`. |
| F-07 | MINOR | IC-04/IC-09, Problem §, Impact table | **Line-number drift in otherwise-correct references.** Examples: Problem § cites `sync_pipeline._sync_stage_contexts` as `:328-378` while the design cites `:345-377` (the per-provider loop is `:345-377`); AC-06 cites `cli_commands.py:1219` for the "up to date" print (print is `:1218`, `sys.exit(0)` `:1219`); the Impact table lists only the context seam `:373-375` and omits the rules injection seam `sync_pipeline.py:748` (design §11 cites `:747-748`). Symbols are correct; only the numbers drift. | Refresh the line numbers or drop them where the symbol is unambiguous. Add the `:748` rules seam to the Impact table (`sync_rules`/`sync_embedded_rule_files` per-provider artefact) so the "Phase-0 untouched" claim covers both injection points. |
| F-08 | MINOR | AC-13 vs OQ-3 | **Gemini dual-reader is asserted as resolvable, not only as an open question.** AC-13 says Gemini "resolves to `GEMINI.md`" **and** that "the Antigravity agent-runtime stays a direct reader of `context.core_file`". Both behaviours belong to the **single** registered provider `Gemini` (`config/ai-providers.yaml:89`), whose IC-07 keys are per-provider: one entry cannot simultaneously be `context_adapter: true` (→ `GEMINI.md`) and a direct core reader. | Keep AC-13 to the resolved adapter set (`Claude`→`CLAUDE.md`, `Gemini`→`GEMINI.md`, the rest direct readers of the core) and move the Antigravity-runtime sub-case entirely into OQ-3 as the HYPOTHESIS/go-no-go it already is; do not assert both outcomes in one AC. |
| F-09 | MINOR | IC-02 vs IC-05 | **Phase tagging: `context_mode` is declared inside IC-02 (labelled "additive + internal refactor; Phase 0")** although it is a Phase-1 symbol (restated as IC-05). An implementer reading the Phase-0 section could wire it early. | Remove the `context_mode` sketch from IC-02 (or mark it clearly as "declared here for completeness — Phase 1") and keep the contract solely in IC-05. |
| F-10 | MINOR | IC-07 / IC-09 (Gemini) | **The config surface that makes Gemini select `GEMINI.md` is unspecified.** The design lists Gemini's adapter as "`@`-import + `context.fileName` (string or list) in `.gemini/settings.json`", but no spec IC names that write; IC-07 declares only `context_adapter_file`/`context_adapter_import`. Without `context.fileName`, the adapter file may never be read. | Either name the `.gemini/settings.json` `context.fileName` write as part of IC-09 (provider-native settings update, capability-gated), or state explicitly that `GEMINI.md` is Gemini's default context file so no settings change is required — and make it an AC observation for the Phase-1 real-repo check. |

### Confirmations (positive, verified against the repo)

- **Trace anchor / Approval marker: PASS.** `spec-id: SPEC-CONTEXT-FILE-MODES-2026-09-13` in frontmatter and `## Trace-Anker`; identical to the source design's anchor; `related-spec: SPEC-OPENCODE-RUNTIME-GATE-2026-09-13` exists (`docs/specs/2026-09-13-opencode-runtime-gate-design.md:2`). `status: Entwurf`; `Status: APPROVED` appears only as a statement that it is not set here. **No APPROVED marker was set by this review.**
- **Phase-0 symbol facts: PASS.** `runtime_gate.RUNTIME_GATE_TIERS` (`:35`), `providers.provider_runtime_gate_tier` (`:357-386`), `providers.runtime_gate_vars` (`:389-423`), `resolve_providers` (`:175`), `resolve_context_filename` (`:254-289`), `SUPPORTED_PLUGIN_PROTOCOLS` (`:312`), `provider_hooks_supported` (`:315`), `context._build_managed_block` (`:1066`), `shared_users` (`:1091-1098`), `sync_context_for_provider` (`:818-857`), `_shares_context_with_embedded_rules` (`:791-815`), `_sync_opencode_context` (`:553`), `context.py:622-627` write/skip, `cli_commands.py:1209-1217`, `sync.py:99` — all confirmed at the cited symbols.
- **Weakest-tier correctness for this repo: CONFIRMED.** Active set `{Claude, Opencode, Gemini}` (`.meta-config/project.yaml:6-9`); `AGENTS.md` sharers active = `{Opencode(permission), Gemini(hook)}` → `permission`; configured-but-inactive Codex/ZCode/KimiCode correctly excluded (AC-04). Opencode's `has_rules:false` forces `has_native_rules=False` for the whole shared group, so both sharers use the embedded-rules render and are governed by the override. `AGENTS.md:208` carries the current `hook` render — the one-time content change AC-06 requires.
- **Provider-agnostic AST guard: CONFIRMED.** `tests/test_provider_agnostic_dispatch.py` `_TOUCHED_MODULES` already contains `context`, `providers`, `sync_pipeline`, `rule_index`, `generated_file_drift`, `runtime_gate` (`:49`), `isolation` (`:50`).
- **Supporting line references: mostly CONFIRMED.** `config/project-config.schema.json` `context_file` `:885-916`, `required` `:2315`, root `additionalProperties` `:2318`; `rule_index.py` `:45/110/180`; `context.py` `_save_context_hashes` `:68`, `_record_static_hash` `:80`; `consistency/context_size.py:44` and iteration `:91+`; `consistency-check.py:43/197/202`; `admin-server.py:230-249/4792/4827`; `variables.py:235`; `placeholders.py:84-85`; scenario registry ends at `62-stale-role-cleanup` (`tests/scenarios/registry.md:109`).
- **Alternatives / risks / honesty: PASS.** "Do nothing" (last-writer-wins) and in-file conditional selection are explicitly rejected with reasons (NeurIPS 2024 SAD); HYPOTHESIS items are labelled and gated behind real-repo verification; OQ-2…OQ-5 carry `[User approval]`; OQ-1, OQ-6…OQ-12 carry recommended defaults. Convention- (not security-)boundary framing is explicit.

## Direct edits

| File | Change | Rationale |
|------|--------|-----------|
| `docs/specs/2026-09-13-context-file-modes-design.md` | `## Ziel / Nicht-Ziele` → `## Ziel` (redundant `**Ziel**` label removed) and the `**Nicht-Ziele**` label → `## Nicht-Ziele` | Pure template/traceability fix (F-06): satisfies the literal `REQUIRED_SPEC_SECTIONS` (`## Ziel`, `## Nicht-Ziele`) checked by `scripts/lib/consistency/spec_plan.py`. Section content unchanged. |

No MAJOR/BLOCKER finding was silently redesigned; all MAJOR findings are listed
above and left to the author.

## Confirmations

- **No `Status: APPROVED` marker was set.** `docs/specs/2026-09-13-context-file-modes-design.md`
  remains `status: Entwurf`; the document body states the marker is set by the
  user gate, not here.
- Scope respected: no implementation, no plan, no REQ-ID, no code; only the
  review report and the one editorial heading fix were written.
- No handoff to `requirements` (spec-review mode): on `APPROVED` the orchestrator
  would advance `quality_pipelines.concept-driven-dev` (`specify → review →
  approve → plan`); that does not apply here.
