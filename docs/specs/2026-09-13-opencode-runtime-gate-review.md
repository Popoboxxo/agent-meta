# OpenCode Runtime Gate (Problem A) — Spec Review (independent critic)

> Reviewer: `concept-reviewer` · Date: 2026-09-13 · Branch: `feat/spec-plan-workflow`
> Target: `docs/specs/2026-09-13-opencode-runtime-gate-design.md`
> Support: `docs/specs/2026-09-13-opencode-runtime-gate-system-design.md`, `.opencode/skills/spec-plan-workflow/SKILL.md`
> **No `Status: APPROVED` marker was set. Spec remains `status: Entwurf`.**

## Verdict: CHANGES_REQUESTED

The spec is structurally complete, the design corrections D-C1 … D-C5 are
substantively right (verified against the repo), provider-agnosticism holds, and
the #747-avoidance claim is correct. It is **not** ready for the user approval
gate because the A2 permission-entry representation contradicts the existing
`opencode.json` writer and its own AC-10, the tier variables are wired to a seam
that the rule/context renderer never consumes, and the P6 gating statement
contradicts the design's `observe`-before-P6 phasing. Findings F-01 (BLOCKER) and
F-02 … F-05 (MAJOR) must be resolved by the author before approval.

## Scope reviewed

7 review dimensions + spec-plan §7.1 (Pflichtsektionen, Trace-Anker,
Approval-Marker, No-Placeholder) + the 6 task checks (template completeness,
provider-agnosticism, internal consistency, AC quality, honesty/security,
feasibility/risks).

- **Template completeness: PASS** — frontmatter (`spec-id:
  SPEC-OPENCODE-RUNTIME-GATE-2026-09-13`, title, `status: Entwurf`),
  Problem/Ziel/Nicht-Ziele, Interface Contracts (IC-01 … IC-15, each with
  `file:Symbol`, signature and error paths), Datenfluss (4 sections), numbered AC
  (AC-01 … AC-22), Offene Fragen + Risiken (OQ-1 … OQ-11, R1 … R4), Trace-Anker
  all present. No unresolved placeholders (`TODO`/`TBD`/`<…>`).
- **Trace-Anker / Approval-Marker: PASS** — anchor present in frontmatter and in
  the `## Trace-Anker` section; `status: Entwurf`; the `Status: APPROVED` string
  appears only as a statement that it is *not* set here.
- **Provider-agnosticism: PASS** — no `provider == "…"` branch; the new seams use
  `has_plugins` / `plugin_protocol` / `SUPPORTED_PLUGIN_PROTOCOLS` and
  `capabilities.runtime_gate`. `IC-13`'s exact dispatch condition is imprecise
  (F-07), but not a provider literal.
- **#747 avoidance: CONFIRMED** — `context.py::_init_provider_settings_json`
  (`:838-880`) does write only when the file is absent (`:852-855`); the existing
  isolation merge path (`isolation.py:225-256`) reads/rewrites in place. A2 adds a
  nested `permission` block, not a new root key, so the #747 avoidance is sound
  (see F-01 for the *different* merge defect).
- **#765 honesty: PASS** — child-session propagation and Main-Chat
  distinguishability are marked HYPOTHESIS / OQ-1 … OQ-4, and the tier is
  deliberately named `permission` (partial), not `hook`/`plugin`.
- **Fact-check of referenced lines: PASS** — verified `provider-capabilities.yaml:59`,
  `ai-providers.yaml:160-224/167/179/192`, `providers.py:120/305-317`,
  `isolation.py:31/54-56/125-132/232-256`, `context.py:838-880`,
  `orchestrator_strict.py:24-81`, `project-config.schema.json:2073-2203`,
  `provider_transform.py:467-515/583-591`, `provider-tools.yaml:56-59`,
  `.opencode/package.json:3`, `rules/1-generic/use-orchestrator.md:1-4`,
  `a2a-delegation-gates.md:50-55`, `tests/scenarios/registry.md:108` (ends at
  `61-hook-deploy-lf-newlines`, so `62-…` is correct), and the six AC-13 test
  names. The D-C1 … D-C5 corrections are all real defects of the system design.

## Findings

| ID | Severity | Location | Issue | Suggested change |
|----|----------|----------|-------|------------------|
| F-01 | BLOCKER | IC-09 `_opencode_runtime_gate_entries`, AC-10, AC-11, OQ-11 | **A2's write shape is incompatible with the existing `opencode.json` writer and with AC-10.** IC-09 returns `{'edit': 'deny', 'bash': 'deny'}` (permission-name → scalar), while `_sync_opencode_isolation` treats `permission.edit`/`permission.read` as glob→decision mappings and calls `.items()` unconditionally (`isolation.py:238-241`). In the common Claude+OpenCode project, A2 runs in `_sync_stage_per_provider` (stage 6) and `sync_provider_isolation` runs later in `_sync_stage_knowledge_and_isolation` (stages 8+9, `sync_pipeline.py:807`), so the isolation writer would hit a scalar string and raise. Even with a tolerant merge, replacing `permission.edit` with a scalar destroys a user's edit mapping — which contradicts AC-10 ("user `permission.edit` mapping … user entries survive"). OQ-11's recommended "namespace the managed keys per writer" cannot resolve a *shared* `opencode.json` key, and the single state file is a hard blocker: `_write_state` (`isolation.py:125-132`) overwrites the whole `{"isolation-deny": [...]}` record, so a second writer sharing that file is clobbered. | Specify the concrete merge representation (e.g. A2 adds a deny glob *inside* the `permission.edit`/`permission.bash` mapping, or uses keys disjoint from isolation's) and the exact two-writer order. Generalise `_read_state`/`_write_state` to namespaced keys (or a second state file) and name them as changed symbols. Add an explicit ownership/rollback contract that preserves a pre-existing user value at the managed key. Fix the `{'edit': 'deny'}` example, or rewrite AC-10 if scalar replacement is intended. Add the multi-provider (isolation + A2) AC that is currently missing. |
| F-02 | MAJOR | IC-04 (`agent_sync._build_provider_vars`); Datenfluss §2 | **The tier variables never reach the rule/context renderer through the stated seam.** `_build_provider_vars` (`agent_sync.py:423-472`) is called only by `sync_agents_for_provider` (`agent_sync.py:883`). Rules are rendered by `rules.py::_merged_rule_vars` (`rules.py:202-254`, called by `sync_rules`/`sync_embedded_rule_files`), and the embedded context block by `context.py::_build_managed_block`, which builds its own `local_vars = dict(variables)` (`context.py:1096-1119`). Neither calls `_build_provider_vars`, and the per-provider `provider_variables` built in `sync_pipeline.py:349/631` contains only global vars + orch-mode flags. So `GATE_ENFORCED`/`GATE_PARTIAL`/`GATE_ADVISORY` would be missing from `use-orchestrator.md`/`AGENTS.md`; with `replace_if`'s default-`"true"` (`variables.py:256`) and the `conditional_vars` guard, AC-05 fails or silently renders all three blocks. | Add the tier vars in the actual rule/context seams (`rules.py::_merged_rule_vars` and `context.py::_build_managed_block` local_vars), **or** inject the resolved tier vars into the per-provider `provider_variables` in `sync_pipeline.py` before both `sync_rules`/`sync_embedded_rule_files` and `sync_context_for_provider`. Name those files as ICs and retarget the Datenfluss arrows. |
| F-03 | MAJOR | Scope (§ Phase 1 bullet), AC-16 … AC-22 | **The "must not be implemented before P6" gate contradicts the design's `observe`-before-P6 phasing.** The design expects the plugin generator, template, managed state and drift tracking to exist and the generated plugin to run in `MODE=observe` *before* P6 (§6.2 "Bis dahin läuft das Plugin im Modus observe"; D8 "observe first"). Only the tier flip (`runtime_gate: plugin`), `MODE=enforce` and the P6 verification (AC-21) depend on P6. Gating all of AC-16 … AC-22 on P6 stalls the observe implementation and is inconsistent with the design. | Restrict the P6 gate to the tier flip + `enforce` + AC-21. Keep AC-16 … AC-20 (generation, rollback, unknown protocol, observe default, drift) implementable before P6, as the design requires. |
| F-04 | MAJOR | Scope §Phase 0 ("no dependency on an unverified provider runtime API"); OQ-3/AN-6; OQ-4/AN-3 | **The "verification-free Phase 0" claim is overstated.** A2's safety and effectiveness depend on unverified provider behaviour: AN-6 (does agent-frontmatter permission override the root deny for `orchestrator`/`git`? OQ-3) and AN-3/#765 (child-session propagation, OQ-4). The design's own §7.1 lists A2 as "abhängig von OpenCode-Permission-Precedence". If AN-6 is false, A2's root deny can block the orchestrator itself. | Narrow the claim to "no dependency on the unverified *plugin* runtime API", and state explicitly that Phase 0 ships with the open permission-precedence/child-session hypotheses, with OQ-3/OQ-4 as documented Phase-0 risks (and the fine-grained-glob fallback if verified false). |
| F-05 | MAJOR | IC-07 `GATE_ENFORCED` block; AC-05, AC-15 | **The `GATE_ENFORCED` wording is not semantically identical to the current text, although IC-07/AC-05/AC-15 require it to be.** Current (`use-orchestrator.md:1-4`): heading `# CRITICAL GATE`, sentence `… ALLES -> \`orchestrator\`. Keine Ausnahmen.` Proposed: heading `# CRITICAL GATE (runtime-enforced)` and sentence `… ALLES -> \`orchestrator\`. Runtime-Gate aktiv.` — the "Keine Ausnahmen" clause is dropped. Implementing this literally fails AC-05/AC-15. | Reproduce the current sentence verbatim in the `GATE_ENFORCED` branch (optionally keep the extended heading), or relax AC-05/AC-15 to "no weakened guarantee" and list the wording delta explicitly. |
| F-06 | MINOR | AC-02 | The two biconditionals are mutually inconsistent if a provider is both hook- and plugin-supported (precedence returns `hook`, so `runtime_gate == "plugin" iff provider_runtime_gate_supported(pc)` is false). | Qualify the plugin clause with "and not `provider_hooks_supported(pc)`". |
| F-07 | MINOR | IC-13 | "whenever the provider has an `isolation-mechanism` of the permission family" is not a concrete config key (only `opencode-permissions` exists today) and overloads cross-provider isolation as a gate-capability proxy. | Gate A2 on a dedicated, named config key (e.g. `capabilities.runtime_gate in {permission, plugin}` or `runtime-gate-mechanism`) and state it in IC-13, consistent with the provider-agnostic policy. |
| F-08 | MINOR | IC-04 (`RUNTIME_GATE_PLUGIN_MODE`); IC-12/AC-14 | The recommended project key `runtime-gate.plugin-mode` has no schema IC/AC, unlike `orchestrator.require-runtime-gate` (IC-12/AC-14). The root schema is `additionalProperties: true` (`project-config.schema.json:2297`), so the key is silently unvalidated. | Add a typed schema entry + AC for the plugin-mode key, or state explicitly that it is deferred to Phase 1 and specify its resolution now. |
| F-09 | MINOR | IC-03 `all_providers_runtime_gate_supported` | The function is defined but has no named consumer and no AC (the IC-03 → AC mapping omits it) — unverified code surface. | Add an AC/consumer, or drop the function until a project-wide guarantee needs it. |
| F-10 | MINOR | Revision table | The first row said "No review cycle has run yet" while D-C1 … D-C5 already list incorporated corrections — self-contradictory bookkeeping. | Fixed directly (see below). |
| F-11 | INFO | System design vs spec | `2026-09-13-opencode-runtime-gate-system-design.md` remains stale on D-C1 … D-C5 (single-arg `provider_runtime_gate_tier`, `orchestrator.strict.require_runtime_gate`, scenario `60`). The spec is now normative for those points. | Add a short design revision note pointing at the spec's D-C1 … D-C5 so the plan does not follow the stale design. |
| F-12 | INFO | IC-12 / Dispatching | `orchestrator.require-runtime-gate` resolves through `_resolve_effective_strict` (`orchestrator_strict.py:24-47`); IC-11 states `agent_meta_root` is "resolvable from `project_root`", which holds for the in-repo callers/tests but is not a defined dependency of that function signature. | Confirm the resolution helper (e.g. an explicit `agent_meta_root` parameter) in IC-11; low risk. |

## Direct edits made

Two MINOR editorial/traceability edits to
`docs/specs/2026-09-13-opencode-runtime-gate-design.md` (no MAJOR/BLOCKER issue was
silently redesigned):

1. Revision-table first row reworded from "(noch keine) … No review cycle has run
   yet" to a neutral "Erstfassung … D-C1 … D-C5 are pre-review corrections"
   entry, removing the self-contradiction with the five existing D-C rows.
2. Trace-Anker IC↔AC table: added the missing `AC-15` (back-compat) references to
   IC-04, IC-05 and IC-06.

All other findings are substantive (contract gaps, AC/representation conflicts,
phasing contradiction) and are left to the author.

## Confirmation

**No `Status: APPROVED` marker was set.** The spec frontmatter remains
`status: Entwurf`; approval remains a separate user gate.
