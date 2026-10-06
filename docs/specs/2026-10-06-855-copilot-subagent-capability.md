---
spec-id: SPEC-855-COPILOT-SUBAGENT-CAPABILITY-2026-10-06
title: Copilot subagent-dispatch capability correction — Mini-Spec
status: APPROVED
related-issue: "#855"
related: ["#807", "#838 audit finding P-6 (docs/analysis/2026-09-30-provider-audit-docs-part1.md)"]
---

# Copilot Subagent-Dispatch Capability Correction — Spec
> Status: APPROVED (2026-10-06)
> Trace-Anker: spec-id: SPEC-855-COPILOT-SUBAGENT-CAPABILITY-2026-10-06

## Problem / Ziel / Nicht-Ziele

**Problem.** Issue #855 claims two under-claims in the Copilot provider declaration.
Part 1 (prompt-files as slash commands) was already fixed by PR #807
(`has_commands`/`commands_dir`/`commands_ext` in `config/ai-providers.yaml`,
`commands: true` in `config/provider-capabilities.yaml`) and is **out of scope here**.
Part 2 remains open: GitHub Copilot custom agents (`.github/agents/*.agent.md`, VS
Code / GitHub docs, distinct from the older `.chatmode.md` mechanism) expose an
`agents:` frontmatter property that lists which other agents may be dispatched as
subagents (`agents: ['*']` = all, `agents: []` = none). Dispatching requires the
`agent` tool to also be listed in `tools:`; a separate `disable-model-invocation`
property (default `false`) opts an agent out of being invoked as a subagent by
others. This matches audit finding **P-6**
(`docs/analysis/2026-09-30-provider-audit-docs-part1.md:318`): `config/provider-
capabilities.yaml`'s Copilot block still declares `subagent_dispatch: false` and
`native_agent_tools: []` — a factual under-claim against a verified, GA, documented
capability, not an unresolved ambiguity.

**Ziel.** Correct the two capability keys in the Copilot block of
`config/provider-capabilities.yaml` to state the verified capability, with an
explanatory comment in the same style as the #807 `commands: true` correction, plus
one additional `special_notes` bullet naming the correct mechanism/path. No other
file changes.

**Nicht-Ziele** (explicitly out of scope — escalate separately if needed):
- **No change to `fanout_mechanism` / `parallel_execution` / `barrier_collect`.**
  The verified capability is "an `agent` tool exists that can dispatch a named
  subagent" — it says nothing about whether multiple `agent` calls in one Copilot
  turn run in parallel with a true barrier. No source in the VERIFIED CONTEXT
  confirms that, so per the project's "unverified → conservative" precedent
  (`config/provider-capabilities.yaml:20-21`, mirrored at `fanout_contracts.py`)
  `fanout_mechanism` stays `sequential-fallback`, `parallel_execution` stays
  `false`. This is also why `native_agent_tools` being non-empty here does **not**
  trigger the `fanout.tool-surface-missing` check (`fanout_contracts.py:239`) —
  that check only fires for `tool-mediated`/`swarm` mechanisms.
- **No change to `text_mentions`, `runtime_gate`, `description`, or the existing
  `special_notes` bullet.** `text_mentions: true` is already set and undisputed;
  `runtime_gate` (CRITICAL-GATE enforcement) is unaffected by a subagent-dispatch
  frontmatter property; the existing `description`/`special_notes` text ("Dateien
  in `.github/copilot/agents/` werden automatisch geladen.") repeats a **separate,
  already-tracked** path finding (audit **P-1**: real path is `.github/agents`,
  already migrated in `config/ai-providers.yaml`'s `agents_dir`/`agent_ext` per the
  PRE-4/OQ-5 comment there) — rewriting it is unrelated drift-cleanup, not this
  issue; flagged under Risiken instead of folded in here.
- **No new generated artifact, no sync.py / template logic change.**
  `DelegationSyntaxEngine.has_native_subagent_dispatch()` (`scripts/lib/
  delegation_syntax.py:590`) reads the flag but has **no caller** anywhere in
  `scripts/` today (verified via repo-wide grep) — it is pure capability-matrix
  metadata, not a generation input. The only two consumers of these two keys are
  read-only consistency checks (§ below); neither is triggered by this change in
  this repo's current configuration. Since Copilot is **not** an active provider
  in this repo's `.meta-config/project.yaml` (`ai-providers: [Claude, Opencode,
  Gemini]`), this change produces **zero** generated-artifact diff on `python
  scripts/sync.py` here.
- **No change to `config/ai-providers.yaml`, `config/provider-bootstrap.yaml`,
  `templates/configs/COPILOT.project-template.md`, `README.md`, or any other file
  still carrying the stale `.github/copilot/agents/` path (P-1).** That is a
  separate, wider documentation-drift cleanup already tracked by the 2026-09-30
  provider audit; bundling it here would turn a 1-file config correction into an
  undefined-size docs sweep. If that cleanup is wanted, it needs its own
  issue/spec.

## Interface Contracts

Single file, single block changed: `config/provider-capabilities.yaml`,
`capabilities.Copilot` (currently lines 191-215).

**Before** (lines 196, 204, 212-214):
```yaml
    subagent_dispatch: false
    ...
    native_agent_tools: []
    ...
    description: "Dateibasierte Agenten (.github/copilot/agents/). @agent Text-Mentions."
    special_notes:
      - "Dateien in .github/copilot/agents/ werden automatisch geladen."
```

**After:**
```yaml
    subagent_dispatch: true             # GitHub Copilot custom agents
                                         # (.github/agents/*.agent.md) expose an
                                         # `agents:` frontmatter property for
                                         # subagent dispatch (issue #855, audit
                                         # finding P-6, docs/analysis/2026-09-30-
                                         # provider-audit-docs-part1.md:318).
                                         # Verified against code.visualstudio.com/
                                         # docs/copilot/customization/custom-agents
                                         # and /custom-chat-modes (2026-10-06).
    ...
    native_agent_tools: ["agent"]       # the `agent` tool must also be listed in
                                         # `tools:` for `agents:` to take effect;
                                         # `disable-model-invocation` (default
                                         # false) opts an agent out of being
                                         # dispatched as a subagent by others.
    ...
    description: "Dateibasierte Agenten (.github/copilot/agents/). @agent Text-Mentions."
    special_notes:
      - "Dateien in .github/copilot/agents/ werden automatisch geladen."
      - "Subagent-Dispatch (#855): `.github/agents/*.agent.md` Frontmatter-Property
         `agents:` (Liste erlaubter Subagenten, `['*']` = alle, `[]` = keine)
         + `agent`-Tool in `tools:`. Kein verifizierter Parallel-/Barrier-Vertrag
         → fanout_mechanism bleibt sequential-fallback (Nicht-Ziel oben)."
```

No other symbol, signature, or file is touched. No Python function signature
changes — this is a data-only YAML correction.

## Datenfluss

- **Input:** the two YAML keys `capabilities.Copilot.subagent_dispatch` and
  `capabilities.Copilot.native_agent_tools` in `config/provider-capabilities.yaml`.
- **Transformation:** none (static config edit, no code path).
- **Consumers (read-only, unchanged code):**
  1. `DelegationSyntaxEngine.has_native_subagent_dispatch("Copilot")`
     (`scripts/lib/delegation_syntax.py:590-593`) — now returns `True` instead of
     `False`. No caller exists in `scripts/` today, so this is a latent/dormant
     return-value change only.
  2. `check_subagent_permission_support` (`scripts/lib/consistency/
     subagent_permissions.py:82-98`) — only emits a finding for a provider whose
     *effective* `subagent_permissions.mode` resolves to `"strict"`
     (`resolve_effective_subagent_permission_mode`). This repo's
     `.meta-config/project.yaml` has no `subagent_permissions` block for Copilot
     (confirmed via grep: no match), so the mode resolves to `"off"` and this
     check does not fire for Copilot either before or after the change.
  3. `check_fanout_backend_contract` / the `fanout.tool-surface-missing` rule
     (`scripts/lib/consistency/fanout_contracts.py:239`) — only applies to
     `mechanism in ("tool-mediated", "swarm")`. Copilot's `fanout_mechanism`
     stays `sequential-fallback` (Nicht-Ziele), so a non-empty
     `native_agent_tools` is accepted but not required; the check is a no-op for
     this provider either way.
- **Output/persistence:** the corrected YAML is the only artifact. Since Copilot
  is inactive in this repo's provider list, `python scripts/sync.py` produces no
  further generated-file diff.

## Acceptance Criteria

1. **Given** `config/provider-capabilities.yaml` is read, **when** the
   `capabilities.Copilot` block is inspected, **then**
   `subagent_dispatch is True` and `native_agent_tools == ["agent"]`.
2. **Given** the corrected file, **when**
   `DelegationSyntaxEngine().has_native_subagent_dispatch("Copilot")` is called,
   **then** it returns `True` (was `False` before).
3. **Given** the corrected file and this repo's `.meta-config/project.yaml`
   (no `subagent_permissions` override for Copilot), **when**
   `check_subagent_permission_support(...)` runs, **then** it emits **no**
   `subagent-permissions.no-dispatch-surface` finding for Copilot (mode resolves
   to `"off"`, check does not evaluate the provider's dispatch surface at all —
   same as before the change, i.e. no regression and no new finding).
4. **Given** the corrected file, **when** `check_fanout_backend_contract(...)`
   runs, **then** it still asserts `fanout_mechanism == "sequential-fallback"`
   for Copilot (`tests/test_delegation_syntax.py::_FANOUT_CAPABILITY_MATRIX`,
   `tests/test_orchestration_contract.py::test_engine_parallel_capability_is_
   capability_driven`) and emits **no** `fanout.tool-surface-missing` finding
   (that rule does not apply to `sequential-fallback`).
5. **Given** `python3 scripts/sync.py --validate` run against this repo's actual
   active-provider configuration (`[Claude, Opencode, Gemini]`), **when** it
   completes, **then** it reports the same pass/fail status as before this
   change — zero new findings, zero generated-file diff (Copilot is inactive
   here).
6. **Given** the new `special_notes` bullet, **when** read alongside the
   pre-existing (unchanged) first bullet, **then** the new bullet names the
   correct path (`.github/agents/*.agent.md`) and does not assert or imply a
   parallel/barrier dispatch contract.

## Offene Fragen + Risiken

- **Offene Frage:** should the pre-existing `.github/copilot/agents/` path drift
  in `description` (same block), `config/provider-bootstrap.yaml:64`, `config/
  ai-providers.yaml`'s own historic references, `templates/configs/
  COPILOT.project-template.md:19`, `README.md:592`, and `docs/providers/
  multi-provider.md` (audit finding **P-1**, already migrated in `ai-providers.
  yaml`'s machine-readable `agents_dir`/`agent_ext` but not in prose elsewhere)
  be cleaned up in a follow-up? **Not decided here** — recommend a separate
  issue/spec scoped to the P-1/P-2/P-3/P-4/P-5 prose-drift cleanup so it does not
  balloon this 1-file correction.
- **Risiko (low):** if a future project activates Copilot AND sets
  `subagent_permissions.mode: strict` (globally or via a Copilot
  provider-override) without also verifying a real PreToolUse-equivalent hook
  surface, `check_subagent_permission_support` will (correctly, by design) emit
  only a `subagent-permissions.no-hook-support` **WARNING** (Copilot's
  `runtime_gate` stays `advisory`) — this is existing, unchanged behavior, not a
  new risk introduced here, called out for completeness.
- **Risiko (low):** the exact VS Code/GitHub Copilot docs URLs and frontmatter
  field names for Part 2 were supplied as pre-verified context for this task
  (three independent sources per the task brief) rather than independently
  re-fetched by this spec. No embedded instructions were found in that context;
  treated as factual input, consistent with the existing audit finding P-6 this
  spec closes.

## Test Plan

- `python3 scripts/sync.py --validate` — must stay green (no new findings; see
  AC-5).
- `python -m pytest tests/test_delegation_syntax.py -k fanout` — pins
  `fanout_mechanism` unchanged for Copilot (AC-4).
- `python -m pytest tests/test_orchestration_contract.py -k parallel_capability` —
  pins `parallel_execution`/`_parallel_supported` unchanged for Copilot (AC-4).
- `python -m pytest tests/test_subagent_permissions_consistency.py` — confirms no
  new `no-dispatch-surface`/`no-hook-support` finding appears for Copilot in this
  repo's project config (AC-3).
- `python -m pytest tests/test_provider_three_file_invariant.py` — Copilot stays
  present in all three PAL files (unaffected, regression guard only).
- No new test file needed: this is a two-scalar config-value correction fully
  covered by existing parametrized tests; none of them hardcode Copilot's
  `subagent_dispatch`/`native_agent_tools` value today (verified via grep), so
  none require edits — they simply keep passing.

## Trace-Anker

spec-id: SPEC-855-COPILOT-SUBAGENT-CAPABILITY-2026-10-06
