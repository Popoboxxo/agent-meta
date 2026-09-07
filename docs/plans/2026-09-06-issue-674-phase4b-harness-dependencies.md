# Phase 4b Harness Dependencies & Follow-ups (Issues #264–#267, #506, #517)

| | |
|---|---|
| **Date** | 2026-09-06 |
| **Status** | Documentation — agent-meta-side Phase 4b work delivered; runtime portions recorded as harness-side dependencies |
| **Roadmap** | `docs/plans/2026-09-05-issue-674-roadmap.md` — Phase 4b "Runtime (P3)" |
| **Issues** | #517 · #506 · #266 · #264 · #265 · #267 (section order = roadmap batch order) |
| **Related** | Design spike #265: `docs/spikes/2026-09-06-issue-265-async-fanout-spike.md` — §7 is the normative harness-dependency statement for #265; §2.6 the feasibility split; §5.3 the config-vs-behavior split |

## 0. Scope boundary

agent-meta is a static file generator. It controls **templates / configs / rules / lib**
only and has **no runtime control** over LLM generation loops, provider APIs, or harness
dispatch. Everything an agent-meta artifact cannot execute at runtime is documented below
as a **harness-side dependency** together with concrete, issue-template-ready follow-up
items — never implemented here. This boundary is stated in the #265 spike header, in the
`BOUNDARY_NOTE` of `scripts/lib/file_affinity.py`, and in the module docstrings of
`scripts/lib/orchestration.py` and `scripts/lib/checkpoint.py`.

---

## 1. Issue #517 — `test-executor` agent (execution-only test runs)

### Implemented in agent-meta

- `agents/1-generic/test-executor.md` (v1.1.0): lightweight execution-only role —
  `Read` + `Bash` only; behavioral contract (run existing suites as-is, no test/code
  authoring, no architecture/context modification, no deployment tools); structured
  result capture (pass/fail/skip counts, exit codes, stdout excerpts, log paths);
  mandatory closing summary (#267). Role boundary table: test design → `tester`,
  browser E2E → `e2e-tester`, failing code → `developer`.
- `config/role-defaults.yaml`: `test-executor` role — `model: nano`, `workflow_tier:
  optional`, `parallel: true`, intent keywords (Re-Run / Fix-Verify / CI-Verify).
- Delegation guidance: `docs/guides/features/agent-delegation-map.md`.

### Harness-side dependency

- **RAM/cost behavior of parallel instances at runtime.** The template *minimizes* the
  footprint (cheapest tier, two tools, one suite per instance) and the template itself
  states that "host capacity for parallel runs remains the caller's responsibility".
  Actual memory/CPU usage, per-instance isolation and live cost savings cannot be
  verified or guaranteed from agent-meta.
- **Runtime permission compliance:** that generated `Read`+`Bash`-only frontmatter is
  actually honored (no write/edit capability offered) is provider/harness behavior.
- Parallel dispatch mechanics (how many instances actually run concurrently) are
  harness dispatch behavior.

### Follow-up items (issue-template ready)

- [ ] **Real-repo footprint validation (P6 pattern):** run 3 parallel `test-executor`
  instances on a constrained host (≤8 GB, the ReqogniLoom near-OOM scenario) and record
  RSS/peak memory + wall time vs. 3 parallel `tester` instances. Acceptance: numbers
  documented, no OOM, savings quantified.
- [ ] **Provider permission compliance check:** for every active provider, verify the
  generated `test-executor` agent offers only `Read`/`Bash` at runtime (no write/edit
  tool available to the session).
- [ ] **Adoption check:** at least one consumer project routes re-run/CI-verify loops
  to `test-executor` (observable via intent routing / session logs).

---

## 2. Issue #506 — Sync-Turn-Contract / background-process guard

### Implemented in agent-meta

- `<output-guard>` section in all 48 Bash-capable `agents/1-generic/*.md` templates
  (each minor-bumped): a started background process MUST be awaited inside the same
  turn (`docker wait`, bounded polling, synchronous foreground); the turn must NEVER
  end on a "waiting"/"started and pending" placeholder.
- `agents/1-generic/test-executor.md` §4: dedicated Sync-Turn-Contract section (#506),
  including the per-task timeout rule (`STATUS: partial` instead of a hanging caller).
- Orchestrator template §6: sync-call contract for orchestrator↔worker expectations
  (part of the `template-orchestrator` v7.13.0 consolidation).

### Harness-side dependency

- **Turn semantics are harness behavior.** Whether turn-end terminates or keeps
  background processes, and whether turn-final text truly reaches a synchronous caller
  verbatim with no post-turn re-activation, is decided by the harness runtime per
  provider. The `<output-guard>` section is prompt text — a **convention boundary**
  (fail-closed against accidental misuse, not against deliberate bypass; guard
  terminology per AGENTS.md).
- The "final tool result is the only channel" premise assumes the provider's
  synchronous-caller model; providers without one cannot benefit from the contract.

### Follow-up items (issue-template ready)

- [ ] **Per-provider sync-turn verification:** document for each active provider whether
  (a) turn-end ends background processes, (b) turn-final text reaches the synchronous
  caller verbatim. Unverified providers → the contract stays marked unverified (do not
  build on it).
- [ ] **Real-repo test of the `docker wait` pattern:** containerized long-running suite
  on 2 providers; assert the caller receives exit code + failure excerpts in the same
  turn without any post-turn polling.

---

## 3. Issue #266 — Static file-affinity analysis

### Implemented in agent-meta

- `scripts/lib/file_affinity.py` (new): deterministic task-level file-affinity
  analysis, stdlib-only. `check_file_overlap(tasks, project_root)` →
  `{"safe": [...], "conflict": [(task_a, task_b, [files]), ...]}` (deterministic,
  fail-closed); 4-step analysis: regex file references (task text + explicit
  `files` field), Python-AST top-level symbol index (names ≥6 chars), Markdown/YAML
  doc-reference pass (one normalized pass covers inline text, code fences,
  frontmatter), import-graph edges via `analysis.FileAffinityAnalyzer`. Also
  `extract_file_references()` and `format_overlap_report()` (embeds the boundary
  note). Hard overlap wins over coupling edges; conflicted ids never appear in
  `safe`.
- `BOUNDARY_NOTE` constant: the documented enforcement boundary, verbatim —
  "static analysis only — real enforcement (call before actual dispatch) is
  harness-side; agent-meta ships the analysis plus the dry-run integration in
  `tests/orchestration/dry_run/engine.py`."
- Dry-run integration: `tests/orchestration/dry_run/engine.py` sequentializes
  conflicted tasks before simulated FANOUT/PARALLEL_GROUP dispatch.
- Plan seam: `scripts/lib/orchestration.py` — `check_plan_file_overlap()` +
  `validate_plan(file_overlap=...)` consume the #266 result; conflicts mean the plan
  is rejected or the affected tasks sequentialized **before** dispatch.
- Prompt side: the orchestrator's "Parallel" line now defers to the static analysis
  instead of instructing the model to guess overlaps (#266 part of the
  template-orchestrator consolidation) — the handoff note in the `file_affinity`
  docstring ("orchestrator wording update") is thereby fulfilled.

### Harness-side dependency

- **The real enforcement point.** Calling `check_file_overlap()` before a REAL
  dispatch is harness-side (`BOUNDARY_NOTE`, `format_overlap_report` docstring):
  nothing in agent-meta runs between an orchestrator LLM's decision and the harness
  dispatch call. The dry-run engine proves the semantics; the harness must apply
  them live.

### Follow-up items (issue-template ready)

- [ ] **Harness pre-dispatch file-affinity gate:** a dispatch hook that calls
  `check_file_overlap(tasks, project_root)` before every FANOUT/PARALLEL_GROUP
  dispatch; conflicted tasks → sequentialize or reject with the
  `format_overlap_report()` output. Acceptance: a conflicted fanout in a real session
  is blocked/sequentialized, and the report (with the boundary note) reaches the
  orchestrator.
- [ ] *(agent-meta-side, optional)* Revisit the no-cache symbol-index policy only if
  consumer repos grow beyond the current "few hundred files" scale assumption
  (per-call parse is deliberate for correctness during session edits).

---

## 4. Issue #264 — Intent routing as structured tool definitions

### Implemented in agent-meta

- Generation pipeline: `scripts/lib/config.py::build_variables()` prerenders the
  per-provider `route_intent` tool definition under `_INTENT_ROUTING_TOOL_DEFS` via
  `build_routing_tool_definitions_for_providers()` (`scripts/lib/agents.py`), built
  once for the active providers; format serialization via
  `render_routing_tool_definition()` — mechanism-keyed on the `handoff_format`
  capability key (`json` / `yaml_text_block`), fail-closed on unknown keys.
- Per-provider resolution: `scripts/lib/agent_sync.py::_build_provider_vars()` maps
  `_INTENT_ROUTING_TOOL_DEFS[provider]` → `INTENT_ROUTING_TOOLS`; providers without
  `handoff_format` render `""` (fail-soft, same semantics as PAL missing-definition
  placeholders). Placeholder registered in `scripts/lib/consistency/placeholders.py`.
- Template: `template-orchestrator` §3 references the generated `route_intent`
  definition via `{{INTENT_ROUTING_TOOLS}}` — the prose routing table was removed
  (data lives in the structured definition); §4 routing policy points at
  `routing.rules` instead of duplicating keywords.

### Harness-side dependency

- **Consumption of the generated definition is provider/harness behavior.** agent-meta
  only renders the definition text (JSON or YAML block); registering it as a callable
  tool and actually routing intent calls through `route_intent` requires native
  function-calling support in the provider/harness at runtime.

### Follow-up items (issue-template ready)

- [ ] **Provider function-calling verification:** for each active provider with
  `handoff_format: json`, verify the generated definition is consumable as a tool
  (schema accepted, `route_intent` call resolves to the right agent). Acceptance: one
  live session per provider in which an intent is routed via `route_intent`.
- [ ] **Empty-§3 guard decision:** if a provider without `handoff_format` becomes
  active while intent routing is enabled, §3 renders empty. Currently never visible —
  every provider defines a `handoff_format` — but the behavior should be decided
  explicitly: sync-time warning vs. documented limitation. (Remaining point from the
  phase-4b consolidation report.)

---

## 5. Issue #265 — FANOUT/BARRIER backend contract (hard interrupt reframe)

### Implemented in agent-meta

*(the generation-time half per spike §2.6 — every step of spike §8 shipped)*

- `scripts/lib/orchestration.py` (new): plan/barrier contract module —
  `FanoutTask` / `FanoutPlan` / `BarrierEntry` / `BarrierResult`, `find_dependency_errors()`
  (empty plan, duplicate ids, dangling dependencies = deadlock, cycle detection via
  Kahn topological sort), `validate_plan()` (over-commitment vs. `max_parallel`,
  #266 file-overlap seam, `tier_override` coarse check), `check_plan_file_overlap()`,
  `execute_plan()` over the injected `Dispatcher` protocol (deterministic entry order,
  status aggregation timeout → failed → partial → success), `summarize_result()` and
  `render_barrier_result()` (#267/§7-compatible; `BARRIER_ENTRY_MARKER` as the shared
  wrapper constant). Deliberate non-goals: no HTTP/API client, no provider-CLI
  subprocess, no provider-name branch (spike §3).
- Capability flags: `fanout_mechanism` (`native-batch` / `tool-mediated` / `swarm` /
  `sequential-fallback`) + `barrier_collect` in `config/provider-capabilities.yaml`
  for all 9 providers, conservatively verified; validated getter trio
  `get_fanout_mechanism()` / `has_async_fanout()` / `get_barrier_collect()` in
  `scripts/lib/delegation_syntax.py` (mechanism-key dispatch, no `if provider ==`).
- Post-sync drift check: `scripts/lib/consistency/fanout_contracts.py::
  check_fanout_backend_contract()` — mechanism validity, mechanism/capability
  consistency, syntax coverage (async mechanisms need fanout/parallel_group syntax;
  sequential-fallback wording must not read like parallel dispatch), §7 marker drift,
  native tool surface — registered in `scripts/consistency-check.py`. Convention
  boundary: fail-closed ERROR findings, not a security boundary.
- Dry-run engine repurposed as plan validator: the hardcoded provider list
  (`engine.py`) was removed in favor of capability lookup.
- Prompt contract (capability-gated): §6 dispatch mechanics render per mechanism via
  the existing PAL placeholders (`{{#if PAL_FANOUT}}` — verified batched-dispatch /
  explicit-collect / sequential-fallback patterns; **no invented `fanout()` tool
  name**); §7 BARRIER protocol documents results-as-tool-data, the status-aware
  `||| agent=... |||` wrapper, the "exactly N tool responses" completion rule and
  partial handling (template-orchestrator consolidation).
- `config/delegation-syntax.yaml`: ZCode/Copilot fanout text aligned to
  sequential-fallback.

### Harness-side dependency

*(spike §7 is normative; §1.1/§12 provide the reasoning)*

The reframed core: **a synchronous tool call IS the hard interrupt** (spike §1.1).
agent-meta defines and validates the FANOUT/BARRIER contract; pausing LLM generation,
dispatching sub-agents, blocking until all complete, and injecting one aggregated
tool-response are harness behaviors. Two implementable bridge variants — both
harness-side, both config-driven by agent-meta:

1. **In-harness batch semantics** (no new tooling): for `fanout_mechanism:
   native-batch` providers (Claude, Opencode, Gemini), the existing "all dispatch
   calls in one response" pattern already yields turn-level barrier behavior —
   prompt contract only, no code.
2. **Barrier-tool bridge** (true async across providers): an MCP tool
   `fanout(plan) -> BarrierResult` registered via the standard `mcp-config`
   committed file. It dispatches N independent harness sessions (per-mechanism CLI
   command templates from project config — no provider branches), blocks until all
   complete (per-task + global timeout), and returns the aggregated result as the
   tool response. `scripts/lib/runtime.py::SubagentBarrierRuntime` provides the
   tested aggregation semantics for the server side; `scripts/lib/orchestration.py`
   provides plan validation and rendering.

**Never implementable by agent-meta:** intercepting arbitrary named functions in the
model's output, pausing token generation outside a tool-call boundary, spawning
harness sub-agents from outside the harness runtime (spike §7).

### Follow-up items (issue-template ready — spike §7 follow-up list)

- [ ] **Barrier-tool MCP server (bridge variant 2):** server exposing
  `fanout(plan) -> BarrierResult`; reuses `SubagentBarrierRuntime` aggregation +
  `orchestration.validate_plan` / `render_barrier_result`; per-mechanism CLI command
  templates from project config; per-task + global timeout. Acceptance: N=3 parallel
  independent harness sessions, deterministic entry order, timeout case returns
  `status: timeout`.
- [ ] **Per-mechanism CLI command templates in project config:** new
  `orchestration:` config block (command strings per mechanism, e.g.
  `claude -a {agent} "{prompt}"`) — agent-meta generates/validates the block, the
  bridge executes it (spike §5.3: config data).
- [ ] **Harness-level `wait_agent` mapping for `tool-mediated` providers (Codex):**
  map plan tasks → `spawn_agent` + `wait_agent` collect; wrap results into
  `BarrierEntry`s in task order.

---

## 6. Issue #267 — Summarization-as-a-Contract

### Implemented in agent-meta

- `scripts/lib/checkpoint.py` extension: two-level session layout —
  `<session-id>.json` (structured checkpoints, summaries) + `<session-id>/`
  directory holding the COMPLETE raw worker output per task. New API:
  `save_raw_output()` (append-only, uuid-suffixed, `_sanitize_component` filename
  hygiene), `load_raw_output()` (fail-soft), `list_raw_outputs()`. Module docstring
  states the harness boundary: the module archives bytes only — it never parses,
  filters or interprets worker content.
- `scripts/lib/orchestration.py`: `summarize_result()` (structured `SUMMARY:` marker
  first — multi-line block until a blank line or the next `KEY:`-style section —
  fallback to the first N sentences, soft 400-char cap); `execute_plan(store=...,
  session_id=...)` persists per-entry `raw_output` via `CheckpointStore.save_raw_output`
  and the entry rides on with only `checkpoint_ref` set; `render_barrier_result()`
  never renders raw output — bulk lives behind the checkpoint ref.
- Templates: orchestrator §9 "Summarization-as-a-Contract" section (compact worker
  summaries only; raw output archived under `.meta-viz/checkpoints/<session-id>/`,
  never re-requested); `test-executor` mandatory closing summary.

### Harness-side dependency

- **BARRIER parsing + raw-output stripping at runtime are harness-side** (explicit
  "Harness-Grenze" in the `checkpoint.py` module and `save_raw_output` docstrings):
  parsing worker results after the BARRIER marker and stripping raw output from the
  orchestrator context happen in the harness's tool-result handling. The
  `orchestration.py` backend supplies `summarize_result()` / `render_barrier_result()`
  — the harness must *apply* them in the live dispatch path.

### Follow-up items (issue-template ready)

- [ ] **Harness BARRIER parsing integration:** in the live dispatch path, parse tool
  results after the BARRIER marker, run `summarize_result()`, route raw output →
  `CheckpointStore.save_raw_output()`, inject only the rendered barrier block.
  Acceptance: after a real fanout the orchestrator context contains only bounded
  summaries + checkpoint refs; the full output is retrievable via
  `load_raw_output()`.
- [ ] **Live context-window validation:** measure orchestrator context before/after a
  real BARRIER with N workers (bounded summaries + refs vs. raw dumps) to verify the
  intended context protection.

---

## 7. Cross-issue dependency chain

| Enforced outcome | Depends on | Owner of the missing piece |
|---|---|---|
| **#267 enforced end-to-end** (BARRIER parsing + context stripping at runtime) | **#265 backend** — a barrier that actually collects must exist first (in-harness `native-batch` turn semantics or the barrier-tool bridge); #267's parse/strip only has something to attach to once #265's collection is real | harness |
| **#266 enforcement** (real pre-dispatch overlap check) | **harness dispatch hook** — call `check_file_overlap()` before live FANOUT/PARALLEL_GROUP dispatch (`BOUNDARY_NOTE`) | harness |
| **#264 consumption** (`route_intent` as callable tool) | **provider function-calling** — the provider/harness must register and route the generated definition (`handoff_format` gate; `json` providers only in practice) | provider/harness |
| **#506 sync-call contract** (no post-turn re-activation) | **provider turn semantics** — turn-final text must reach the synchronous caller | harness |
| **#517 parallel footprint** (cheap parallel suite runs) | **harness parallel dispatch + host capacity** — template minimizes, cannot guarantee | harness/caller |

Reading: #265 is the pivot. Its backend contract enables #267's runtime enforcement;
#266's and #264's runtime value equally hang off harness/provider surfaces that
agent-meta can only configure, not control.

## 8. Remaining consolidation observations (non-blocking, agent-meta-side)

- `standalone/agents/`: ~78 pre-rendered standalone copies are stale since the
  phase-4b template updates — refreshing them requires running
  `sync.py --render-standalone` as its own step. Housekeeping follow-up, no runtime
  impact.
- Providers without `handoff_format` → empty orchestrator §3 block (currently never
  visible; all providers define the key) → see #264 follow-up "Empty-§3 guard
  decision".
