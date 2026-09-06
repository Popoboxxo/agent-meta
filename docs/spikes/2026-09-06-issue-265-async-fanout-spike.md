# Design Spike — Issue #265: Hard Backend Interrupt for FANOUT/PARALLEL_GROUP

| | |
|---|---|
| **REQ** | #265 (Roadmap Phase 4b "Runtime (P3)" — highest complexity, spike required before implementation) |
| **Status** | Design spike, analytical only — no code changes |
| **Date** | 2026-09-06 |
| **Related** | #266 (file-affinity static analysis), #267 (BARRIER result summarization), #346 (tier override), #592 (guard gaps — terminology precedent) |
| **Scope boundary** | agent-meta controls **templates / configs / rules / lib** only. It is a static file generator with **no runtime control** over LLM generation or provider APIs. Harness-side portions are documented as a dependency/follow-up, never implemented here. |

---

## 1. Problem statement

The orchestrator prompt defines `FANOUT`, `PARALLEL_GROUP`, and `BARRIER` as orchestration
patterns, but nothing enforces them at the execution layer. The LLM is expected to
self-enforce waiting — without a hard mechanism it can hallucinate sub-agent completion
and fabricate results (the "Parallel Illusion", external audit 2026-05-29).

The issue demands a backend that (a) halts LLM generation on a FANOUT/PARALLEL_GROUP
tool-call, (b) dispatches all sub-agents asynchronously via the provider's native parallel
API, (c) collects results at a **true BARRIER**, and (d) injects them as a single
tool-response.

### 1.1 The one structural fact that decides everything

A "hard interrupt" of an LLM generation loop can only be executed by the component that
owns that loop — the **harness** (Claude Code, Opencode, Antigravity, Codex, …). agent-meta
ships no process that sits between the model's token stream and tool dispatch. However,
the tool-call protocol itself already provides the halt for free:

> **A synchronous tool call IS a hard interrupt.** A model cannot continue generating past
> a tool call before the tool result arrives. If `fanout(plan)` exists as a real tool whose
> return value is the aggregated result of all N sub-agents, then the BARRIER is enforced
> by construction: the model never sees a moment where results could be fabricated — they
> arrive as tool data, not generated text.

This reframing splits the issue cleanly:

- agent-meta owns the **contract** (plan/result schemas, prompt syntax, capability flags,
  validators, plan-static analysis) — all generation-time.
- The harness owns the **barrier tool** implementation (dispatch + blocking collect +
  single tool-response) — documented dependency.

### 1.2 What already exists today (asset inventory)

| Asset | Location | State | Relevance for #265 |
|---|---|---|---|
| Barrier runtime (thread pool, per-task + global timeout, exception capture, deterministic order) | `scripts/lib/runtime.py` (`SubagentBarrierRuntime`) | Implemented, unit-tested (`tests/test_barrier_runtime.py`: parallel, exception, timeout cases), **dormant** (no production caller) | Seed for `orchestration.py`'s dispatch seam semantics |
| FANOUT/PARALLEL_GROUP prompt syntax | `config/delegation-syntax.yaml` (`PAL_FANOUT`, `PAL_PARALLEL_GROUP`, `PAL_PARALLEL_PATTERN`) via `scripts/lib/delegation_syntax.py` | Active, per-provider | Issue text points at `agents.py:95-100` — **stale**: FANOUT text now lives here, not in agents.py |
| Pipeline fanout renderers | `scripts/lib/pipelines.py` `_PROVIDER_NOTATION` (lowercase provider-keyed dict) | Active | Second FANOUT-text generation point; must stay in sync with new contract |
| Capability matrix | `config/provider-capabilities.yaml` (`subagent_dispatch`, `parallel_execution`, `native_agent_tools`, `handoff_format`, …) | Active | Extension point for new flags |
| Mechanism-key pattern | `config/ai-providers.yaml` (`isolation-mechanism`, `agent-transform.frontmatter-mechanism`, `hook_protocol`, `mcp-config.format`) + dispatch tables (`isolation.py`, `hooks.py`, `mcp_provider_config.py`) | Established reference pattern | The provider-agnostic adapter strategy follows exactly this pattern |
| A2A envelope with batch FANOUT | `schemas/a2a-handoff.schema.json` (`batch: true` → payload array with per-entry `task_id`) | Active, schema-validated | Fanout envelope contract already schema-ready |
| Dry-run simulation engine | `tests/orchestration/dry_run/engine.py` (`OrchestratorDryRun`, `DispatchPlan`, `validate_syntax`) | Simulation only | Repurpose target → plan validator. **Contains a provider-agnostic-policy violation**: hardcoded `provider in ["Claude", "Opencode", "Gemini"]` (engine.py:165, 340) |
| Checkpoint store | `scripts/lib/checkpoint.py` (`CheckpointStore`, session files, append-only) | Active | #267 synergy: full raw worker output storage |
| File dependency analysis | `scripts/lib/analysis.py` (`FileAffinityAnalyzer.get_file_dependencies`, `find_shared_files`) | Active | Reuse base for #266's `check_file_overlap` (module does **not** exist yet) |
| Consistency-check suite | `scripts/consistency-check.py` + `scripts/lib/consistency/*` (check functions → `list[Finding]`) | Active | Registration point for post-sync FANOUT-contract validation |
| Orchestrator prompt contract | `agents/1-generic/orchestrator.md` §6 (delegation table), §7 (BARRIER protocol with `\|\|\| agent=<name> result_key=<key> \|\|\|` wrapper) | Active | Update target: text-pattern → tool-call contract (capability-gated) |

**Provider reality check** (from `delegation-syntax.yaml` + `provider-capabilities.yaml`):
the semantics of "FANOUT" already differ per provider today — Opencode: all `task()` calls
in one response run in parallel and the turn completes only when all finish ("BARRIER:
Automatisch" is already documented in its `parallel_pattern`); Claude: foreground multi-call
parallelism + `run_in_background` with manual wait; Codex: `spawn_agent` + explicit
`wait_agent` collect; KimiCode: `AgentSwarm` = one tool call with aggregated report
(barrier by construction); Continue/Copilot/Mammouth: no native parallelism → sequential
fallback. This heterogeneity is exactly what capability flags must express — not `if
provider ==` branches.

---

## 2. Decomposition — agent-meta-side vs. harness-side

Per item from the issue, with feasibility verdict and reason.

### 2.1 `scripts/lib/orchestration.py` — new module

| Sub-item | Feasible for agent-meta? | Reasoning |
|---|---|---|
| Plan/result **data structures** (`FanoutTask`, `FanoutPlan`, `BarrierEntry`, `BarrierResult`) | ✅ Machbar | Pure data + validation, stdlib only, testable. Generation-time contract. |
| **Static plan validation** (cycles, deadlocks, over-commitment, file overlap) | ✅ Machbar | Operates on the plan, not on live agents. Consumes #266 output as input. |
| **BARRIER result format + renderer** (`render_barrier_result` → orchestrator §7-compatible block) | ✅ Machbar | Deterministic formatting of data. Backward-compatible with the existing `\|\|\| agent=… result_key=… \|\|\|` wrapper. |
| **Summarization contract** (#267: exit-summary extraction, raw output → checkpoint routing) | ✅ Machbar | `CheckpointStore` exists; extraction is string processing. |
| **Dispatch seam** (`execute_plan(plan, dispatcher)` with injected `Dispatcher` protocol) | ✅ Machbar (as seam) | agent-meta ships the orchestration semantics over an injected callable; `SubagentBarrierRuntime` already implements barrier/timeout aggregation over callables. Testable with stub dispatchers. |
| `execute_fanout()` / `execute_parallel_group()` with **real async dispatch** | ❌ Nicht machbar (agent-meta) | No process inside agent-meta runs while an orchestrator LLM generates; nobody here can halt it or dispatch harness subagents (`Agent`/`task` are harness-runtime tools, not provider-API endpoints). Feasible only inside the harness or a barrier-tool bridge (§7/§12). Keep the two issue-named functions as thin wrappers over `execute_plan` for naming continuity. |
| "Dispatch via the **provider's native parallel execution API**" | ❌ Nicht machbar (as stated) | Category error in the issue text: sub-agents are **harness** constructs, not provider-API resources. A raw provider API can run parallel *LLM requests*, but not harness sub-agents with agent-meta role files, tool access, or hooks. The bridge variant (§7, option B) dispatches **independent harness sessions** via configured CLI commands — that is a harness-side behavior driven by agent-meta config. |

### 2.2 Provider adapters (`scripts/lib/providers/` as proposed)

| Sub-item | Feasible? | Reasoning |
|---|---|---|
| Per-provider Python adapter modules + `if provider ==` selection | ❌ Nicht machbar / unidiomatic | Directly violates the provider-agnostic policy (`provider-agnostic` SKILL.md, `architecture` SKILL.md): no new provider without Python changes; the repo's established pattern is **mechanism keys in config + small dispatch tables** (`isolation-mechanism`, `hook_protocol`, `frontmatter-mechanism`). |
| Config-driven mechanism model (`fanout-mechanism` key + validation table) | ✅ Machbar | Follows `hook_protocol` precedent exactly: config names the mechanism, Python validates known keys and gates generation on them. See §7. |

### 2.3 Post-sync validation in generation

| Sub-item | Feasible? | Reasoning |
|---|---|---|
| Detect FANOUT/PARALLEL_GROUP patterns in generated orchestrator ↔ verify corresponding backend/capability contract exists | ✅ Machbar | New consistency check (e.g. `scripts/lib/consistency/fanout_contracts.py`) returning `list[Finding]`, registered in `scripts/consistency-check.py` (same pattern as `check_handoff_contracts`, `check_orchestrator_strict_hook_support`). Fail-closed on drift: e.g. provider advertises `parallel_execution: true` but has no `fanout-mechanism` mapping or no fanout syntax in `delegation-syntax.yaml`. Note file drift: the issue names `agents.py` — today the FANOUT-text generation points are `config/delegation-syntax.yaml` (PAL) and `pipelines.py::_PROVIDER_NOTATION`; the check must cover all three surfaces. |

### 2.4 Dry-run engine → plan validator

| Sub-item | Feasible? | Reasoning |
|---|---|---|
| Cycle / deadlock / over-commitment detection | ✅ Machbar | `DispatchPlan` + `SubTask.dependencies` already model the dependency graph; over-commitment batching exists partially (`validate_syntax`). Cycle detection is a topological sort — stdlib. |
| Fix hardcoded provider list | ✅ Machbar (required) | Replace `provider in ["Claude", "Opencode", "Gemini"]` with `DelegationSyntaxEngine.get_capabilities(provider)["parallel_execution"]` — kills the existing policy violation as part of the repurpose. |
| Placement | ✅ Machbar | Validator core moves to `scripts/lib/orchestration.py` (`validate_plan`); `engine.py` keeps simulation/fixture role and delegates. Rationale: production consistency checks must not import from `tests/` (layering smell). Alternative — keep everything in `engine.py` — rejected for exactly that reason. |

### 2.5 `orchestrator.md` → `fanout()` / `parallel_group()` tool-call syntax

| Sub-item | Feasible? | Reasoning |
|---|---|---|
| Replace text-pattern FANOUT with explicit tool-call instruction | ✅ Machbar — **capability-gated** | Only emit `fanout(<envelope>)` tool-call syntax where a mechanism actually provides that tool (`fanout-mechanism: tool-mediated-*`). For `automatic` providers the honest contract stays "all dispatch calls in one response; the turn's return IS the barrier" (already true for Opencode). For sequential-only providers the fallback text stays. Emitting a `fanout()` tool name that no harness knows would be *worse* than today's text patterns — fictional tools invite fabrication, the exact problem #265 wants to kill. Implemented via PAL placeholders + `{{#if}}` conditionals; no provider names in `1-generic/`. |
| BARRIER protocol §7 result format update | ✅ Machbar | Keep `\|\|\| agent=<name> result_key=<key> \|\|\|` wrapper (backward compatible), add status/summary/checkpoint_ref fields per §6 of this doc. |

### 2.6 Summary verdict

Every item decomposes into a **machbar generation-time half** (contract, validation,
prompt, config) and a **nicht-machbar runtime half** (halt, dispatch, collect, inject) —
the latter is a documented harness dependency (§12), consistent with the task's stated
user boundary.

---

## 3. API sketch — `scripts/lib/orchestration.py`

Data structures and functions agent-meta can own as generated/validated contract. All
stdlib-only, PEP 8, type-hinted, docstring level as shown.

```python
"""Orchestration plan, barrier contract, and dispatch seam (issue #265).

agent-meta owns PLAN + CONTRACT + VALIDATION. Live sub-agent dispatch stays a
harness concern, injected via the ``Dispatcher`` protocol — the framework never
calls a provider API itself (see docs/spikes/2026-09-06-issue-265-async-fanout-spike.md
§7 and the harness-dependency section).

Usage:
    from scripts.lib.orchestration import FanoutPlan, validate_plan, execute_plan

    plan = FanoutPlan(kind="fanout", tasks=(...))
    errors = validate_plan(plan, max_parallel=4, file_overlap=check_file_overlap)
    if errors: ...                      # fail fast before any dispatch
    result = execute_plan(plan, dispatcher=my_harness_dispatcher)
    print(render_barrier_result(result))
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Literal, Protocol


# ---------------------------------------------------------------------------
# Plan structures (generation-time contract — what the orchestrator issues)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FanoutTask:
    """One sub-agent dispatch inside a fanout/parallel-group plan.

    files_touched feeds the #266 static overlap check; handoff carries the
    A2A envelope fragment (schemas/a2a-handoff.schema.json — with batch:true
    the same fields live in each payload array entry).
    """
    task_id: str                        # local to the plan (A2A batch task_id)
    target_agent: str
    prompt: str
    files_touched: tuple[str, ...] = ()      # #266 input
    tier_override: str | None = None         # issue #346 semantics, pre-validated
    handoff: dict | None = None              # full A2A envelope (optional)


@dataclass(frozen=True)
class FanoutPlan:
    """A validated-in-advance dispatch plan for FANOUT or PARALLEL_GROUP."""
    kind: Literal["fanout", "parallel_group", "sequential"]
    tasks: tuple[FanoutTask, ...]
    barrier: bool = True                    # False = fire-and-forget (explicitly discouraged)
    max_parallel: int = 2                   # mirrors project.yaml max-parallel-agents


# ---------------------------------------------------------------------------
# Barrier result structures (#267-compatible contract)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BarrierEntry:
    """One task's outcome at the barrier — the ONLY thing the orchestrator sees.

    summary carries the 2-3 sentence exit summary (#267 Summarization-as-a-Contract);
    checkpoint_ref points at the full raw output in .meta-viz/checkpoints/<session>.json.
    """
    task_id: str
    agent: str
    status: Literal["success", "failed", "timeout"]
    summary: str
    checkpoint_ref: str | None = None       # e.g. ".meta-viz/checkpoints/orch-...json#checkpoints[N]"
    overlap_warnings: tuple[str, ...] = ()  # #266 conflicts observed during execution
    duration_s: float = 0.0


@dataclass(frozen=True)
class BarrierResult:
    """Aggregated barrier outcome — injected to the orchestrator as ONE tool-response."""
    plan_id: str
    status: Literal["success", "partial", "failed", "timeout"]
    entries: tuple[BarrierEntry, ...]
    total_duration_s: float = 0.0


# ---------------------------------------------------------------------------
# Dispatch seam — the ONLY place the harness plugs in
# ---------------------------------------------------------------------------

class Dispatcher(Protocol):
    """Harness-side async dispatch adapter (see §7 / §12).

    Implementations: stub (tests/dry-run), SubagentBarrierRuntime-based
    subprocess bridge (future MCP barrier tool), in-harness native batch.
    Must return entries in task order — barrier semantics are deterministic.
    """
    def dispatch(self, tasks: Sequence[FanoutTask]) -> Sequence[BarrierEntry]: ...


def validate_plan(
    plan: FanoutPlan,
    *,
    max_parallel: int = 2,
    file_overlap: Callable[[Sequence[FanoutTask]], list[str]] | None = None,
) -> list[str]:
    """Static plan validation — no agents, no I/O. Returns error strings (empty = valid).

    Checks (in order):
    1. Empty plan / duplicate task_ids.
    2. Cycle detection over FanoutTask handoff dependency edges (topological sort).
    3. Over-commitment: len(tasks) > max_parallel without explicit barrier batching
       (mirrors project.yaml max-parallel-agents, HITL rule FANOUT>N requires confirmation).
    4. File overlap via the injected #266 callable (None = check unavailable → skipped,
       never a silent pass-through claim of safety).
    5. tier_override present without a valid tier name (coarse check; full guardrails
       remain in delegation_syntax.resolve_tier_override — no duplicated policy).
    """


def execute_plan(
    plan: FanoutPlan,
    dispatcher: Dispatcher,
    *,
    store: CheckpointStore | None = None,
    session_id: str | None = None,
) -> BarrierResult:
    """Execute a plan through the injected dispatcher with BARRIER semantics.

    Reuses runtime.SubagentBarrierRuntime for aggregation when the dispatcher
    runs Python callables (subprocess bridge); passes through deterministic
    ordering, per-task/global timeouts, and status aggregation
    (all success → success; any failed → failed; any timeout → timeout;
    mixed without failure → partial). When `store` is given, raw outputs are
    persisted per session (#267) and only checkpoint refs ride in entries.
    """


def summarize_result(raw_output: str, *, max_sentences: int = 3) -> str:
    """Extract the worker exit summary (#267). Structured marker first
    (worker templates: 'SUMMARY:' block), fallback: first N sentences."""


def render_barrier_result(result: BarrierResult) -> str:
    """Render as the single orchestrator-facing tool-response text block,
    backward-compatible with orchestrator.md §7:

        ||| agent=<name> result_key=<task_id> status=<status> |||
        <summary>
        Full output: <checkpoint_ref>

    …plus a closing '[N] agents completed' line. Pure formatting — no I/O.
    """
```

Not in scope for this module (deliberate): any HTTP/API client, any `subprocess` of a
provider CLI (bridge concern, §12), any provider-name branch.

---

## 4. BARRIER result format — #267/#266 compatibility

```json
{
  "plan_id": "FANOUT-20260906-001",
  "kind": "fanout",
  "status": "partial",
  "entries": [
    {
      "task_id": "t1",
      "agent": "developer",
      "status": "success",
      "summary": "Fixed race in cache.py eviction; tests added; next: review.",
      "checkpoint_ref": ".meta-viz/checkpoints/orch-1757-abc.json#checkpoints[4]",
      "overlap_warnings": []
    }
  ],
  "total_duration_s": 182.4
}
```

- **#267**: every `entry.summary` is bounded prose; raw diffs/logs live behind
  `checkpoint_ref` (CheckpointStore session file). The orchestrator prompt points at
  `.meta-viz/checkpoints/` for detail — context window protected.
- **#266**: `validate_plan(plan, file_overlap=check_file_overlap)` consumes the future
  `file_affinity.check_file_overlap(tasks)` return shape (`{safe: [], conflict: […]}` →
  projected here as a flat `list[str]` of conflict descriptions; adapter stays in #266's
  module). Conflicts → plan rejected or affected tasks sequentialized *before* dispatch —
  static, not LLM-guessed.
- **A2A**: with `batch: true`, one envelope carries the whole plan; each result entry
  maps back via `task_id`. `render_barrier_result` keeps the §7 human-readable wrapper so
  existing tracker/tooling output stays parseable.

---

## 5. Provider adapter strategy — capability flags, not branches

### 5.1 Principle (matches `hook_protocol` / `isolation-mechanism` precedent)

Config **names a mechanism**; Python code contains a **dispatch/validation table over
mechanism keys** and gates generation on flags. Adding a provider that reuses an existing
mechanism requires zero Python changes. Code may validate `mechanism ∈ known_mechanisms`
— it must never branch on the provider *name*.

### 5.2 New capability keys — `config/provider-capabilities.yaml`

```yaml
capabilities:
  <Provider>:
    # existing keys stay…
    fanout_mechanism: <key|null>   # null ⇒ provider must not receive FANOUT patterns at all
    barrier_collect: <automatic | tool-mediated | none>
```

Mechanism keys (initial set, all observable in today's syntax table):

| `fanout_mechanism` | Semantics | Current providers matching |
|---|---|---|
| `native-batch` | All dispatch tool-calls in one response; harness runs them in parallel; turn returns when all complete — BARRIER is turn semantics, no extra tool | Opencode, Claude (foreground), Gemini |
| `tool-mediated` | Explicit collect step: results gathered via a named harness tool (`wait_agent`-style) or a barrier tool | Codex (`wait_agent`) |
| `swarm` | One tool call fans out N items and returns an aggregated report — barrier by construction | KimiCode (`AgentSwarm`) |
| `sequential-fallback` | No native parallelism — FANOUT renders as sequential list | Continue, Copilot, Mammouth, ZCode (`parallel_execution: false`) |

### 5.3 Split: config data structure vs. harness behavior

| Concern | Where it lives | Nature |
|---|---|---|
| Which mechanism a provider speaks | `provider-capabilities.yaml` (`fanout_mechanism`, `barrier_collect`) | **Config data** |
| Per-provider prompt syntax text | `delegation-syntax.yaml` (`fanout`, `parallel_group`, `parallel_pattern`) | **Config data** |
| Known-mechanism validation + generation gating + `DelegationSyntaxEngine.has_async_fanout()` / `get_fanout_mechanism()` getters | `scripts/lib/delegation_syntax.py` (+ new small table in `orchestration.py`) | **agent-meta code** (mechanism-keyed, provider-name-free) |
| Actually pausing generation / parallel dispatch / blocking collect / tool-response injection | Harness (or future barrier-tool bridge) | **Harness behavior** — out of repo scope, §12 |
| Bridge CLI command templates (option B, §12) | Project config (`orchestration:` block) — command strings per mechanism, e.g. `claude -a {agent} "{prompt}"` | **Config data** (agent-meta generates/validates the block; the bridge executes it) |

### 5.4 Consequence for the existing violation

`tests/orchestration/dry_run/engine.py` hardcoded provider list and `pipelines.py`
`_PROVIDER_NOTATION`'s lowercase provider-keyed dict are the two places where provider
differences currently live in code. The engine violation is fixed by the repurpose
(capability lookup). `_PROVIDER_NOTATION` is a data-dict-in-code — acceptable short-term,
flagged as optional follow-up: migrate notation strings into `delegation-syntax.yaml`
(same PAL pattern) so both FANOUT-text surfaces share one config source.

---

## 6. Post-sync validation design

New check `check_fanout_backend_contract(agent_meta_root, project_root, config) ->
list[Finding]` in `scripts/lib/consistency/fanout_contracts.py`, registered in
`scripts/consistency-check.py` (pattern: `check_handoff_contracts`).

Checks (fail-closed as errors, not warnings — this is a **convention boundary** per the
guard-terminologie, not a security boundary):

1. For every provider active in the project with `parallel_execution: true`:
   `fanout_mechanism` set and ∈ known mechanisms; `fanout`/`parallel_group` syntax
   defined in `delegation-syntax.yaml`; `barrier_collect` consistent with mechanism.
2. For every provider with `parallel_execution: false`: rendered orchestrator contains
   **no** parallel-dispatch instruction beyond the sequential fallback (scan generated
   output for the provider's `fanout` syntax keys).
3. Generated orchestrator output: no leftover `{{PAL_FANOUT}}` / `{{PAL_PARALLEL_GROUP}}`
   placeholders (already warned by the PAL engine; here elevated to a Finding when the
   mechanism is non-null).
4. `orchestrator.md` §7 result wrapper references match the format emitted by
   `render_barrier_result` (marker string kept in one shared constant).
5. When `fanout_mechanism: tool-mediated` → the referenced tool appears in
   `native_agent_tools` (or the project's barrier-tool MCP config, §12).

Acceptance: deliberately broken fixture (mechanism removed while `parallel_execution:
true`) produces an error-Finding; clean sync passes; suite runtime unaffected otherwise.

---

## 7. Harness dependency / follow-up (copy-paste ready)

> **Harness dependency — hard backend interrupt (Issue #265, Roadmap Phase 4b)**
>
> agent-meta defines and validates the FANOUT/BARRIER **contract** (plan/result schemas,
> capability flags, prompt syntax, plan validator, post-sync checks). It cannot execute
> it: pausing LLM generation, dispatching sub-agents, blocking until all complete, and
> injecting one aggregated tool-response are **harness** behaviors.
>
> **Two implementable bridge variants (both harness-side, both config-driven by
> agent-meta):**
>
> 1. **In-harness batch semantics** (no new tooling): for `fanout_mechanism:
>    native-batch` providers, the existing "all dispatch calls in one response" pattern
>    already yields turn-level barrier behavior (documented for Opencode). No code needed;
>    prompt contract only.
> 2. **Barrier-tool bridge** (true async across providers): an MCP tool
>    `fanout(plan) -> BarrierResult` registered via the standard `mcp-config`
>    committed-file. The tool server dispatches N **independent harness sessions**
>    (per-mechanism CLI command templates from project config — no provider branches),
>    blocks until all complete (per-task + global timeout), and returns the aggregated
>    result as the tool response. The synchronous tool return **is** the barrier — the
>    model cannot fabricate results past a tool call. `scripts/lib/runtime.py`
>    (`SubagentBarrierRuntime`) already provides the tested aggregation semantics for the
>    server side; `scripts/lib/orchestration.py` provides plan validation and rendering.
>
> **Not implementable by agent-meta, ever:** intercepting arbitrary named functions in
> the model's output, pausing token generation outside a tool-call boundary, spawning
> harness sub-agents from outside the harness runtime.
>
> **Follow-up issues to file when the contract lands:** barrier-tool MCP server (variant
> 2), per-mechanism CLI command templates in project config, harness-level `wait_agent`
> mapping for `tool-mediated` providers.

---

## 8. Recommended implementation order (agent-meta-side)

Each step is independently shippable; none requires the harness bridge to exist.

| # | Step | Files | Acceptance criteria |
|---|---|---|---|
| 1 | Capability flags + getters | `config/provider-capabilities.yaml`, `scripts/lib/delegation_syntax.py` (+tests) | `has_async_fanout(provider)` / `get_fanout_mechanism(provider)` / `get_barrier_collect(provider)` return per-provider values; all 9 current providers (Claude, Opencode, Gemini, Continue, Copilot, Mammouth, Codex, ZCode, KimiCode) mapped; mechanism-key validation raises on unknown key; no `if provider ==`; sequential-only providers map to `sequential-fallback` |
| 2 | `orchestration.py` data + contract module | `scripts/lib/orchestration.py` (new), `tests/test_orchestration_contract.py` (new) | `FanoutTask`/`FanoutPlan`/`BarrierEntry`/`BarrierResult` + `validate_plan` (cycles, over-commitment, duplicate ids) + `execute_plan` over stub dispatcher (success/failed/timeout/partial aggregation — cases mirroring `test_barrier_runtime.py`) + `render_barrier_result` (§7-compatible output); no I/O, no provider names |
| 3 | Plan-validator repurpose | `scripts/lib/orchestration.py`, `tests/orchestration/dry_run/engine.py` (+tests) | Hardcoded provider list removed → capability lookup; `validate_plan` rejects cyclic dependency fixture and over-max-parallel fixture; `engine.py` delegates validation (no logic duplication); #266 `file_overlap` hook parameter exists (callable optional) |
| 4 | Post-sync consistency check | `scripts/lib/consistency/fanout_contracts.py` (new), `scripts/consistency-check.py` (+fixture test) | Broken-fixture produces error-Finding (mechanism missing while `parallel_execution: true`; leftover PAL placeholders); clean repo passes; check runs in default suite |
| 5 | Prompt contract update | `agents/1-generic/orchestrator.md` §6/§7, `config/delegation-syntax.yaml`, (+version bump per conventions) | Generated orchestrator per provider matches capability matrix: `native-batch` → batched-dispatch text (today's wording kept), `tool-mediated` → explicit collect-step text, `swarm` → swarm text, `sequential-fallback` → unchanged fallback; **no `fanout()` tool-name emitted unless `tool-mediated` mechanism configures it**; §7 wrapper keeps `\|\|\| agent=… result_key=… \|\|\|` (backward compatible → no breaking change); `tests/test_delegation_syntax.py` updated |
| 6 | #267 synergy hooks | `scripts/lib/orchestration.py`, `scripts/lib/checkpoint.py` (optional `store_raw_output` helper) | `execute_plan(store=…)` writes raw outputs to CheckpointStore and returns `checkpoint_ref` per entry; `summarize_result` extracts bounded summary; unit-tested |

Order rationale: flags first (everything gates on them), contract module before validator
(validator imports it), prompt last (emits only what earlier steps guarantee), #267 hooks
last (pure extension of step 2 structures).

---

## 9. Risk list

| Risk | Assessment | Mitigation |
|---|---|---|
| Prompt-only enforcement remains a convention boundary for `native-batch` providers — the LLM could still *claim* partial results before the turn ends | Accepted, documented | Guard-terminologie framing; #267 summaries + artifact pattern reduce impact; `tool-mediated`/`swarm` mechanisms eliminate it entirely where available |
| Fictional `fanout()` tool name if emitted without a real tool | High — worse than status quo | Capability gating is mandatory (step 5 acceptance criterion); consistency check (step 4) fails on drift |
| Drift between three FANOUT-text surfaces (`delegation-syntax.yaml`, `pipelines.py`, orchestrator template) | Medium | Post-sync check covers generated output; optional follow-up: migrate `_PROVIDER_NOTATION` strings into config |
| Partial barrier semantics (sub-agent fails mid-fanout) | Medium — needs explicit contract | `BarrierResult.status` aggregation defined in `execute_plan` docstring (success/partial/failed/timeout); orchestrator §7 rule "contradictions → main_chat" unchanged |
| Token cost of N-result BARRIER envelope | Medium | #267 summaries (bounded), checkpoint refs for bulk; artifact pattern >200 lines stays |
| Breaking change to downstream projects via orchestrator prompt changes | Low — format kept backward compatible | §7 wrapper preserved; template minor version bump + changelog per conventions skill; no major bump required |
| Bridge (variant 2) loses in-session context — dispatching independent sessions cannot share the orchestrator's conversation | Real limitation, not a bug | Documented in §7: variant 1 for in-session work, variant 2 for coarse-grained independent tasks; A2A envelopes carry full context per task by design |
| Scope creep into #266/#267 territory | Medium | This spike only defines seams (`file_overlap` param, `summary`/`checkpoint_ref` fields); #266/#267 fill them in their own issues |

---

## 10. Decision block

```
DECISION
context: Issue #265 demands a hard backend interrupt for FANOUT/PARALLEL_GROUP; agent-meta
  is a static generator with no runtime control over LLM loops or provider APIs.
choice: Implement #265 as contract + plan + validation (generation-time): orchestration.py
  data/validator/dispatch-seam module reusing the dormant SubagentBarrierRuntime, capability
  flags (fanout_mechanism / barrier_collect) instead of provider adapters, post-sync
  consistency check, capability-gated prompt contract; reframe "hard interrupt" as a
  synchronous barrier tool whose return value IS the barrier — harness-side, documented
  as dependency with two bridge variants (in-harness batch semantics; MCP barrier-tool
  bridge dispatching independent sessions).
alternatives:
  - Full in-repo execution engine with per-provider Python adapters — rejected: violates
    provider-agnostic policy; agent-meta cannot halt LLM generation; new provider would
    require Python changes.
  - Status quo (prompt-only BARRIER) — rejected: Parallel Illusion persists; issue is
    roadmap-mandated.
  - Keep plan validator in tests/orchestration/dry_run/engine.py only — rejected:
    production consistency checks must not import from tests/.
consequences: Easier — provider onboarding without Python changes; #266/#267 get defined
  seams; drift becomes CI-detectable. Harder — real async execution now explicitly depends
  on harness follow-ups; two config files gain new keys; three FANOUT-text surfaces must
  stay consistent (check-enforced).
```
