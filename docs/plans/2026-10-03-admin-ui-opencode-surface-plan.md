---
spec-id: SPEC-ADMIN-UI-OPENCODE-SURFACE-AMENDMENT-2026-10-03
parent-spec-id: SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30
pipeline_stages:
  implement: 1          # stage `implement` -> Task 1 (senior-developer; T2–T5 are implement fanout siblings)
  validate: 6           # stage `validate` -> Task 6 (runtime verification; tester/validator)
---

# Admin-UI + Project-Level `surface-version` Gap Closure — Implementation Plan

> Status: **geplant** (amendment APPROVED 2026-10-03)
> **Trace anchors:** `spec-id: SPEC-ADMIN-UI-OPENCODE-SURFACE-AMENDMENT-2026-10-03`; `parent-spec-id: SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30`
> **Spec:** `docs/specs/2026-10-03-admin-ui-opencode-surface-amendment.md`
> **Parent plan/rule:** `docs/plans/2026-09-30-provider-audit-opencode-v2-plan.md`; plan conventions per `writing-plans` skill (`pipeline_stages` mandatory).

**Goal:** Close G1–G5: let a consumer opt into Opencode `surface-version: v2` via `.meta-config/project.yaml → provider-options.Opencode.surface-version` without touching the framework registry, validate it server-side, expose the resolved `active-surface`, and render it as a `<select>` + badge in the Admin UI — v1 staying byte-frozen.
**Architecture:** One override step in the resolver (`load_providers_config(root, project_config)`) feeds generation and every check via the §8 MUST-THREAD call sites; dispatch stays data-driven on resolved `mcp-config.format` / `frontmatter-mechanism` (no provider-name literal). Server reads the same registry the resolver reads; UI reads `surface-formats` keys and the dedicated `GET /api/ai-providers` badge.
**Tech Stack:** Python 3.9+ (Stdlib only), pytest; JSON Schema (`jsonschema`); Bash scenario harness; Playwright browser harness (`tests/browser/`); YAML/JSON/HTML.

**Spec:** `docs/specs/2026-10-03-admin-ui-opencode-surface-amendment.md`

## Global Constraints

- **Provider-agnostic:** no `if provider == "Name"` / provider-name literal anywhere; iterate `provider-options` data (D1) and dispatch on resolved config values only.
- **v1 byte-freeze:** `project_config=None` and a project without the key are strict no-ops; `tests/test_surface_version_selection.py` and the v1 scenario output stay byte-identical (R1/D5).
- **MUST-THREAD list is binding:** only the §8.2 MUST-THREAD sites (call sites 1–8) get `project_config`; SURFACE-IRRELEVANT sites keep the one-arg call.
- **Reserved key:** `active-surface` is read-only, is never persisted, and is stripped by both registry write handlers (R3/REV-R1).
- **No new dependency, no new endpoint:** only existing ai-providers endpoints are extended; comments-stripping on save is OUT-OF-SCOPE (R7).
- **Branch:** `feat/provider-audit-opencode-v2` (PR #845); no merge/force-push.

## File Structure

- Modify `scripts/lib/providers.py` — `_SURFACE_OVERRIDE_KEYS`, `_apply_project_surface_overrides`, `load_providers_config(root, project_config=None)`, `_surface_version_warnings`.
- Modify `scripts/lib/sync_pipeline.py` — pass `config` (call site 1).
- Modify `scripts/lib/agent_sync.py` — pass `config` + emit REV-R5 WARNING finding (call site 2).
- Modify `scripts/lib/consistency/artifact_contracts.py` — `project_config` param (call site 3).
- Modify `scripts/lib/consistency/model_contracts.py` — `project_config` param (call site 4).
- Modify `scripts/consistency-check.py` — load project config once, pass to call sites 3/4.
- Modify `scripts/sync.py` — cleanup preview passes `config` (call site 5).
- Modify `scripts/lib/cli_commands.py` — test-repo + activate/deactivate pass `config` (call sites 6–8).
- Modify `config/project-config.schema.json` — `surface-version`/`agent-discovery` in the 5 modeled provider blocks.
- Modify `scripts/admin-server.py` — `_validate_surface_versions`, reserved-key strip, `active-surface`, project-channel validation.
- Modify `docs/ui/admin-ui.html` — `inferSchema` enum + opts forwarding, `viewAIProviders` badge, `viewProjectProviders` select/checkbox.
- Modify `tests/test_surface_version_selection.py`, `tests/test_provider_options_schema.py`, `tests/test_admin_server.py`, `tests/test_admin_ui_plugins_section.py`, `tests/scenarios/configs/69-opencode-v2-surface.project.yaml`, `tests/scenarios/asserts/69-opencode-v2-surface.sh`.
- Create `tests/test_surface_version_consistency.py`, `tests/browser/test_admin_ui_opencode_surface.py`.
- `VERSION` / `package.json` — touched only if T7 triggers (not required; see T7).

## Task Steps

Every task: write/extend the test first (red) → implement → observe green → commit with the named message. Provider-agnostic rule applies to every task. Owned test files are exclusive (no `Files:` overlap).

### Task 1: Resolver project-override + must-thread call sites
**Agent:** senior-developer
**Files:** Modify `scripts/lib/providers.py`; Modify `scripts/lib/sync_pipeline.py`; Modify `scripts/lib/agent_sync.py`; Modify `scripts/lib/consistency/artifact_contracts.py`; Modify `scripts/lib/consistency/model_contracts.py`; Modify `scripts/consistency-check.py`; Modify `scripts/sync.py`; Modify `scripts/lib/cli_commands.py`; Modify `tests/test_surface_version_selection.py`
**Interfaces:**
- Produces `_SURFACE_OVERRIDE_KEYS: tuple[str, ...] = ("surface-version", "agent-discovery")` and `_apply_project_surface_overrides(provider_config: dict, project_config: dict | None) -> dict` (allow-list copy; non-dict/malformed → no-op).
- Produces `load_providers_config(agent_meta_root: Path, project_config: dict | None = None) -> dict` (override before `_apply_surface_format_selection` / `_apply_surface_mechanism_selection`).
- Produces `_surface_version_warnings(provider_config: dict) -> list[str]` (REV-R5: non-default `surface-version` without `surface-formats`).
- Produces signature `check_artifact_contracts(agent_meta_root: Path, project_config: dict | None = None)`, `check_model_contracts(agent_meta_root: Path, project_config: dict | None = None)`; `collect_artifact_findings` passes `config` + appends the `_surface_version_warnings` WARNING findings.
- Produces call-site threading at `sync_pipeline.py:155`, `agent_sync.py:728`, `consistency/artifact_contracts.py:89`, `consistency/model_contracts.py:95`, `consistency-check.py:195-196`, `sync.py:571`, `cli_commands.py:220/806/841`.
- Consumes `resolve_frontmatter_strip_fields` fail-safe pattern; `lib.io.load_yaml_file` for the `consistency-check` project load.
**Acceptance:** AC-A1: with `provider-options.Opencode.surface-version: v2` the resolver returns `mcp-config.format == "opencode-json-v2"` AND `agent-transform.frontmatter-mechanism == "opencode-native-v2"`; absent key / `project_config=None` → `opencode-json` / `opencode-native` byte-identical; `agent-discovery` copied; non-dict `provider-options` no-op; unknown value ignored; a generic `FutureProvider` proves no name literal. AC-A3 (threading): generation-resolved == check-resolved `provider_config`; a non-default `surface-version` without `surface-formats` yields a WARNING finding.
**Verify:** `python3 -m pytest tests/test_surface_version_selection.py -q`; `python3 scripts/sync.py --check; echo $?` → `0`
**Depends on:** none — **parallel_group:** P1
- [ ] Step 1: extend `tests/test_surface_version_selection.py` with override/byte-identity/`FutureProvider` cases (fail)
- [ ] Step 2: implement `_SURFACE_OVERRIDE_KEYS`, `_apply_project_surface_overrides`, extend `load_providers_config`
- [ ] Step 3: add `_surface_version_warnings` + thread the 8 MUST-THREAD call sites (AC-A3)
- [ ] Step 4: `python3 -m pytest tests/test_surface_version_selection.py -q` (green); commit — `feat: resolve project provider-options surface overrides`

### Task 2: Project schema opening
**Agent:** developer
**Files:** Modify `config/project-config.schema.json`; Modify `tests/test_provider_options_schema.py`
**Interfaces:**
- Produces properties `surface-version: {"type":"string"}` and `agent-discovery: {"type":"boolean"}` inside the `additionalProperties:false` blocks Claude/Gemini/Continue/Opencode/Mammouth (spec §3.3). No `enum` in the schema.
- Consumes the existing `_MODELLED_PROVIDERS` fixture list.
**Acceptance:** AC-A1 (schema precondition): both keys accepted in all 5 modeled blocks; absence valid; unknown key still rejected (`additionalProperties:false`); non-string/non-bool rejected.
**Verify:** `python3 -m pytest tests/test_provider_options_schema.py -q`
**Depends on:** none — **parallel_group:** P1
- [ ] Step 1: extend `tests/test_provider_options_schema.py` (new keys accepted; bogus still rejected) (fail)
- [ ] Step 2: add the two additive properties to every modeled block
- [ ] Step 3: `python3 -m pytest tests/test_provider_options_schema.py -q` (green); commit — `feat: accept surface-version and agent-discovery in project provider-options`

### Task 3: Server validation, reserved-key strip, active-surface, project channel
**Agent:** senior-developer
**Files:** Modify `scripts/admin-server.py`; Modify `tests/test_admin_server.py`
**Interfaces:**
- Produces `_validate_surface_versions(providers: dict, *, allow_no_formats: bool = False) -> None` — raises `ValueError` → HTTP 400; no provider-name literal; no `{v1,v2}` acceptance fallback (REV-R5).
- Produces reserved-key strip in `_route_put_config` (`key == "ai-providers"`, shallow copy) and `_handle_post_ai_providers_update` before `yaml.dump`.
- Produces project validation in `_route_put_config("project")` and `_write_project_section` when `section == "provider-options"` (REV-R4).
- Produces `_handle_get_ai_providers` payload `{"providers": <registry>, "active-surface": {<P>: {"version","format","mechanism"}}}` computed via `load_providers_config(agent_meta_root, project_config)`.
- Consumes Task-1 `load_providers_config(root, project_config)`.
**Acceptance:** AC-A4: `PUT /api/config/ai-providers` and `POST /api/ai-providers/update` with `surface-version: "v3"` → HTTP 400 + JSON `{"error":...}`, file unchanged; `"v2"` → 200 persisted; project write (`PUT /api/config/project` and `PUT /api/config/project/section` `section:"provider-options"`) with an unresolvable value → 400, no write; a provider with `surface-version: v2` but no `surface-formats` → 400 (REV-R5). AC-A5: `GET /api/ai-providers` → `active-surface.Opencode == {"version":"v2","format":"opencode-json-v2","mechanism":"opencode-native-v2"}`; an injected `active-surface` is stripped and never persisted.
**Verify:** `python3 -m pytest tests/test_admin_server.py -q`
**Depends on:** 1 — **parallel_group:** P2
- [ ] Step 1: extend `tests/test_admin_server.py` (400/strip/active-surface/project-channel; no-write assertions)
- [ ] Step 2: implement `_validate_surface_versions` + strip + project-channel validation
- [ ] Step 3: extend `_handle_get_ai_providers` with the computed read-only `active-surface`
- [ ] Step 4: `python3 -m pytest tests/test_admin_server.py -q` (green); commit — `feat: validate and expose provider surface in admin server`

### Task 4: Admin UI enum `<select>`, active-surface badge, project provider-options
**Agent:** developer
**Files:** Modify `docs/ui/admin-ui.html`; Modify `tests/test_admin_ui_plugins_section.py`; Create `tests/browser/test_admin_ui_opencode_surface.py`
**Interfaces:**
- Produces `inferSchema(obj, opts)`: `opts.enumFields` emits `{type:"string", enum:[...]}` and `opts` is forwarded through nested recursion (REV-R7, `:2043`).
- Produces `viewAIProviders` (`:1959`): editable object from `/api/config/ai-providers`; badge from `const activeSurface = (await api.get("/api/ai-providers").catch(()=>({})))["active-surface"] || {}`; `delete` `active-surface` before save; options = `Object.keys(conf["mcp-config"]?.["surface-formats"] || {})`, fallback `["v1"]`.
- Produces `viewProjectProviders` (`:6503`): per-provider `surface-version` `<select>` + `agent-discovery` checkbox writing into `providerOptions[provName]` (excluded from the generic `renderDictEditor`); help text extended.
- Consumes Task-3 `GET /api/ai-providers` → `active-surface`; `mcp-config.surface-formats` keys.
**Acceptance:** AC-A6: surface-version renders as `<select>` with `v1`/`v2` (not free text) and an active-surface badge is shown; a provider without `surface-formats` offers `[v1]` only; the project Providers view exposes a `surface-version` `<select>` that persists `provider-options.<Provider>.surface-version` on Save.
**Verify:** `python3 -m pytest tests/test_admin_ui_plugins_section.py -q`; `pytest tests/browser/test_admin_ui_opencode_surface.py -q`
**Depends on:** 1 (surface-formats data); consumes the §3.2 endpoint contract fixed by Task 3 — **parallel_group:** P2
- [ ] Step 1: add static assertions + browser test (select/badge/options-fallback/nested opts) (fail)
- [ ] Step 2: implement `inferSchema` enumFields + nested `opts` forwarding
- [ ] Step 3: implement `viewAIProviders` badge + `viewProjectProviders` select/checkbox + help text
- [ ] Step 4: `python3 -m pytest tests/test_admin_ui_plugins_section.py -q` (green); commit — `feat: render provider surface as select with active-surface badge`

### Task 5: Cross-layer consistency test + scenario 69 extension
**Agent:** tester
**Files:** Create `tests/test_surface_version_consistency.py`; Modify `tests/scenarios/configs/69-opencode-v2-surface.project.yaml`; Modify `tests/scenarios/asserts/69-opencode-v2-surface.sh`
**Interfaces:**
- Produces `tests/test_surface_version_consistency.py`: generation-resolved == check-resolved `provider_config` for a v2 project (R2); non-default `surface-version` without `surface-formats` → WARNING finding (REV-R5).
- Consumes Task 1 `load_providers_config(root, project_config)` / `_surface_version_warnings`; consolidates the resolver-override, admin-endpoint and UI assertions by importing/running their suites (`test_surface_version_selection.py`, `test_admin_server.py`, UI tests) as one gate.
- Modifies scenario 69 config to consume the **project channel** `provider-options.Opencode.surface-version` (replacing the throwaway registry flip) and its assert to prove project.yaml → resolver → sync → v1/v2 artifact + `--check` rc 0.
**Acceptance:** AC-A2 + AC-A3 end-to-end: v2 project.yaml emits the v2 shape/mechanism; v1/unset byte-identical; `--check` rc 0 on a consistent v2 tree; a v1 tree under a v2 project yields a mismatch finding.
**Verify:** `python3 -m pytest tests/test_surface_version_consistency.py -q`; `bash tests/scenarios/run.sh 69`
**Depends on:** 1, 2, 3, 4 — **parallel_group:** P3
- [ ] Step 1: write `tests/test_surface_version_consistency.py` (fail)
- [ ] Step 2: switch scenario 69 to the project channel + extend the assert (v1/v2 + `--check`)
- [ ] Step 3: `python3 -m pytest tests/test_surface_version_consistency.py -q` + `bash tests/scenarios/run.sh 69` (green)
- [ ] Step 4: commit — `test: cover project surface override consistency and scenario 69`

### Task 6: Runtime verification Opencode v1.18.31 + v2.0.20
**Agent:** tester
**Files:** none in-repo (scratch only under `/var/tmp/`; no committed artifact)
**Interfaces:** Consumes the v1/v2 artifacts produced by Task 5's scenario in a `/var/tmp` scratch project; Produces a verification record in the task report (not committed).
**Acceptance:** AC-A2 (runtime-readable): the v2 `opencode.json` (nested `mcp.servers`, `default_agent`, no `subagent_depth`) loads under Opencode `v2.0.20`; the frozen v1 flat `opencode.json` loads under Opencode `v1.18.31`; both generate rc 0 and `--validate` rc 0; v1 output byte-identical to the pre-change baseline.
**Verify:** `mkdir -p /var/tmp/am-opencode-surface && cd /var/tmp/am-opencode-surface && python3 <repo>/scripts/sync.py && opencode --version` (v1.18.31 on the v1 tree, v2.0.20 on the v2 tree); record both exits.
**Depends on:** 5 — **pipeline stage:** `validate`
- [ ] Step 1: materialize a v1 and a v2 scratch project under `/var/tmp/`
- [ ] Step 2: run sync + `--validate` on both; load each with its matching Opencode version
- [ ] Step 3: assert v1 byte-freeze and v2 nested shape; record results
- [ ] Step 4: report (no commit; verification-only)

## Release / Version Bump (T7) — **Not required**

- **Decision:** T7 does **not** trigger. The `conventions` skill's version-bump invariant (#2) applies to `agents/**` content changes; this amendment changes no agent template. The SemVer **minor** for v2-opt-in is already owned by the parent plan (Task 15, `VERSION`/`package.json`/`CHANGELOG.md`); `VERSION` stays `2.0.0`.
- **If later triggered** (scope grows to include an `agents/**` change): add a `release` task owning `VERSION`, `package.json` (and the parent plan's `CHANGELOG.md`) — disjoint from every task here; no such step exists under the approved scope.

## Findings Traceability (AC-A1…AC-A6)

| AC | Criterion (short) | Task(s) | Test |
|----|-------------------|---------|------|
| AC-A1 | project override v2 resolves format+mechanism; absent → v1 byte-identical; schema accepts keys | T1 (resolver), T2 (schema) | `tests/test_surface_version_selection.py`, `tests/test_provider_options_schema.py` |
| AC-A2 | real sync emits v2 shape/mechanism; v1 byte-frozen; runtime-readable | T1 (threading), T5 (scenario), T6 (runtime) | `tests/test_surface_version_consistency.py`, scenario 69, T6 record |
| AC-A3 | check paths resolve same config; mismatch is fail-loud (no silent divergence) | T1 (MUST-THREAD), T5 | `tests/test_surface_version_consistency.py`, `sync.py --check` |
| AC-A4 | server + project write reject unresolvable value with 400; valid persists | T3 | `tests/test_admin_server.py` |
| AC-A5 | `GET /api/ai-providers` exposes `active-surface`; reserved key never persisted | T3 | `tests/test_admin_server.py` |
| AC-A6 | UI `<select>` + badge (registry) and project provider-options select persists | T4 | `tests/test_admin_ui_plugins_section.py`, `tests/browser/test_admin_ui_opencode_surface.py` |

## Graph Validation

- **Parse:** tasks are built from the `### Task` blocks via `scripts/lib/consistency/spec_plan.py::_parse_plan_tasks`; validated with `scripts/lib/orchestration.py::{FanoutPlan, validate_plan, check_plan_file_overlap}`.
- **Ownership (pairwise disjoint in every parallel group):** P1 = {T1, T2}; P2 = {T3, T4}; P3 = {T5}. `Files:` sets are pairwise disjoint by construction (production files split resolver/schema/server/UI; test files split per owner). The only cross-task test *invocations* (T5 running T1/T3/T4 suites) are read-only, not writes. So `check_plan_file_overlap` returns `{"safe": [task-1…task-6], "conflict": []}` and `validate_plan` returns `[]` for the whole graph and for each group (`max_parallel=2`, `len(tasks)=2 ≤ 2`).
- **No dependency cycle:** every edge points to a lower id — `3→1`, `4→1`, `5→1,2,3,4`, `6→5`; T1 and T2 have no incoming edge. Kahn peel completes; no dangling dependency; no duplicate `task_id`.
- **`pipeline_stages` coverage:** `implement → 1`; `validate → 6`. T2–T5 are implement-stage fanout siblings covered by T1's `implement` slot; T7 is a documented non-required decision (no stage slot, no task).
- **Replay:** `python3 - <<'PY'` (parse plan → `FanoutPlan(kind="sequential", …)` whole-graph + one `FanoutPlan(kind="parallel_group", barrier=True, max_parallel=2)` per P1/P2/P3); expect `[]`. Runner not executed at planning time (static analysis only) — replay is the Task-5 gate.

## Self-Review

- **AC coverage:** every AC-A1…AC-A6 maps to ≥1 task with a concrete test (table above). No AC is task-less.
- **Role mapping:** each task maps to exactly one existing role (`senior-developer`, `developer`, `tester`).
- **`Files:`/`Interfaces:`:** complete (exact paths, symbols, signatures); test files exclusively owned; no placeholders.
- **TDD:** each task writes/extends its test first (red → implement → green → commit); T5 adds the cross-layer/scenario gate; T6 is runtime-only.
- **Boundary:** this plan implements nothing; execution is the user's/orchestrator's decision (`payload.plan_ref` = this file).
