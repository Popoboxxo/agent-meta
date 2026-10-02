---
pipeline_stages:
  implement: 1          # stage `implement` (plan-driven) -> step 1 (agent senior-developer, allowed_agents tier)
  validate: 18          # stage `validate` (parallel_group) -> step 18 (agent validator; tester co-runs)
  review-req: 19        # stage `review-req` (loop)         -> step 19 (agent validator)
  review-quality: 20    # stage `review-quality` (loop)     -> step 20 (agent code-reviewer)
---

# Provider-Audit Gap Closure + Opencode v2 Support — Implementation Plan

> Status: **ACTIVE** (Spec APPROVED 2026-10-01)
> Trace anchor: `spec-id: SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30`
> Review: `docs/specs/2026-09-30-provider-audit-opencode-v2-review.md` (Iteration 2: APPROVED, only minor restones)
> Design: `docs/specs/2026-09-30-provider-audit-opencode-v2-design.md` (Rev. 2)
> Evidence base: `docs/analysis/2026-09-30-provider-audit-runtime-consolidation.md`; `docs/analysis/evidence/2026-09-30-regression-tests.md`
> Plan-ledger: `plan-ledger` skill; ledger = this file (checkboxes); recovery via `scripts/lib/checkpoint.py::CheckpointStore` + `BarrierEntry.checkpoint_ref`.
> Gate note: PRE-1 is resolved — the referenced spec (`docs/specs/2026-09-30-provider-audit-opencode-v2.md`) now carries `Status: APPROVED (2026-10-01)`, so the repo's own plan check `spec_plan.py::_check_approval_markers` (spec_plan.py:464-492) finds the APPROVED marker and emits no `spec_plan_approval_marker` ERROR. The plan is ACTIVE. This gate was a convention boundary over the approval marker, never a plan defect.

**Goal:** Close the runtime-verified provider gaps (Codex TOML, Kimi model namespace, Mammouth `tools` list, Continue config validity, Copilot/Antigravity paths), add Opencode v2 as an opt-in generated surface (`surface-version: v1|v2`), and turn every silent-drop / invalid-artifact class into a sync-time, fail-loud signal (`--validate`/`--check` rc != 0) — all provider differences expressed as config data / capability flags, never as `if provider == "Name"`.
**Architecture:** One generic artifact validator (`artifact_validate.py`) feeds `agent_sync._finalize_agent_content` and two consistency modules (`consistency/artifact_contracts.py`, `consistency/model_contracts.py`). Dispatch is always on a declared config value (`mcp-config.format`, `frontmatter-mechanism`, `pipeline_notation`, `marker_id`); writer/transform code never reads a provider name or `surface-version` (H-1, ADR-10). Path changes migrate write-new -> verify -> backup-old -> remove-old, user files untouched (H-2, ADR-9).
**Tech Stack:** Python 3.9+ (Stdlib only; `from __future__ import annotations` in new modules), pytest, Bash scenario harness (`tests/scenarios/run.sh`), YAML/JSON/TOML/Markdown.

**Spec:** `docs/specs/2026-09-30-provider-audit-opencode-v2.md`

---

## Preconditions (approval gate — all RESOLVED 2026-10-01)

Every item below was a user/approval decision. All are now resolved (2026-10-01); none is open, so no implementation task is gated anymore. The referenced spec carries `Status: APPROVED (2026-10-01)`; the plan is ACTIVE (see the Amendment below for how each decision is ordered into the existing tasks).

| ID | Decision (spec ref) | Owner | Status | Effect if changed |
|---|---|---|---|---|
| PRE-1 | Spec approval: `concept-reviewer` sets `Status: APPROVED (date)` | user / `concept-reviewer` | **RESOLVED (2026-10-01) — approval granted; spec set to `Status: APPROVED (2026-10-01)`** | Blocks all tasks; would keep the plan PROVISIONAL. |
| PRE-2 | **OQ-1** Antigravity discovery: ship default-on vs. flag-gate (spec §4, AC-9) | user | **RESOLVED (2026-10-01) — flag-gated, default-off (`agent-discovery: false`)** | Task 4 `agent-discovery` default + path values + scenario 68 assert. |
| PRE-3 | **OQ-4** Opencode v2 primary entry role (`default_agent`, `primary-role` key) (spec §4, AC-5) | user | **RESOLVED (2026-10-01) — `orchestrator` as `mode: primary`** | Task 4 data key (`primary-role: orchestrator`) + Task 6 `opencode-native-v2` + scenario 69 assert. |
| PRE-4 | **OQ-5** Copilot extension `.md` vs. `.agent.md` (spec §4, AC-8) | user | **RESOLVED (2026-10-01) — `.agent.md` under `.github/agents/`** | Task 4 `agents_dir`/`agent_ext` values + scenario 67 assert. |
| PRE-5 | **OQ-7** Mammouth context file `AGENTS.md` vs. `CONTEXT.md` (spec §4) | user | **RESOLVED (2026-10-01) — `AGENTS.md`; `MAMMOUTH.md` + routing entry retired** | Task 4 `context_file` value; Task 16 regeneration/removal. |
| PRE-6 | **OQ-8** v1->v2 default flip timing / SemVer track (spec §4/§11) | user | **RESOLVED (2026-10-01) — v2 opt-in this release (`surface-version: v1` default); default flip next major** | Task 4 `surface-version` default (v1); SemVer minor bump class. |
| PRE-7 | **Scope §9**: 27-file repo drift in-scope vs. separate PR (spec §9, AC-3a/AC-3b) | user | **RESOLVED (2026-10-01) — in-scope; regenerate 27-file drift (AC-3b binding)** | Task 16/17 presence; AC-3b stays in this change on "in-scope". AC-3a is always mandatory. |

Resolved values (2026-10-01): PRE-2 flag-gated/default-off; PRE-3 `orchestrator` as `mode: primary`; PRE-4 `.agent.md` under `.github/agents/`; PRE-5 Mammouth reads `AGENTS.md`, `MAMMOUTH.md` retired; PRE-6 v1 default, v2 opt-in (minor); PRE-7 in-scope.

## Amendment 2026-10-01

> Applied by `planner`. The user's PRE-1…PRE-7 decision (2026-10-01) is pinned here and ordered into **existing** tasks; only resolved values and the ownership of the OQ-2/OQ-6/OQ-9 artifacts are recorded. The spec itself (`docs/specs/2026-09-30-provider-audit-opencode-v2.md`) is set to `Status: APPROVED (2026-10-01)` by the `concept-reviewer` in parallel — this plan references it and does not edit it. Ledger checkboxes are deliberately untouched (no task executed yet).
>
> **Follow-up amendment (2026-10-01, later pass):** the release/version-bump gap is closed by **inserting Task 15** (`release`, MAJOR bump) *before* regeneration, depending on Task 14 — the version bump runs first so that regeneration re-embeds the new `{{AGENT_META_VERSION}}` while no task writes outside its declared `Files:` set. The five tail tasks are renumbered: old Task 15 (regeneration) → **Task 16** (depends on 15), old Task 16 (commit) → **Task 17** (depends on 16), old Task 17 (validate) → **Task 18** (depends on 17), old Task 18 (review-req) → **Task 19** (depends on 18), old Task 19 (review-quality) → **Task 20** (depends on 19). Tasks 1–14 keep their numbers. Task 15 is a non-stage-target (no `pipeline_stages` slot) but is a hard dependency of Task 16, so it cannot be skipped. `agent-discovery` is named as the concrete OQ-1 key in Task 4 / Task 14 scenario 68; N7 is recorded as Accepted (spec §13.3) with no task. See the Graph Validation and Findings-Traceability re-check bullets.

### Decision → task mapping

| PRE / OQ | Decision (2026-10-01) | Ordered into |
|---|---|---|
| PRE-1 | Spec approval granted | Plan header → ACTIVE; `_check_approval_markers` clean; no task change |
| PRE-2 / OQ-1 | Antigravity discovery **flag-gated, default-off** via the concrete key `agent-discovery: false` (`config/ai-providers.yaml` §2.1) | Task 4 (`agent-discovery: false` + path values), Task 14 scenario 68 (`agent-discovery: true` fixture) |
| PRE-3 / OQ-4 | Opencode v2 primary entry **`orchestrator` as `mode: primary`** | Task 4 (`primary-role`), Task 6 (`opencode-native-v2`), Task 14 scenario 69 |
| PRE-4 / OQ-5 | Copilot **`.agent.md` under `.github/agents/`** | Task 4 (`agents_dir`, `agent_ext`), Task 14 scenario 67 |
| PRE-5 / OQ-7 | Mammouth **`AGENTS.md`**; `MAMMOUTH.md` + routing entry retired | Task 4 (`context_file`), Task 16 (regenerate/remove) |
| PRE-6 / OQ-8 | **v2 opt-in** this release; default flip next major | Task 4 (`surface-version: v1` default); SemVer minor |
| PRE-7 / §9 | 27-file drift **in-scope** (AC-3b binding) | Task 16 (regenerate), Task 17 (commit) |
| OQ-2 | Continue top-level `agents:` block in `.continue/config.yaml` is dead config — remove it and state the `cn review`-only auto-load in the generated header comment | Task 10 (`bootstrap.py` + `context.py`); Task 9 notes the `bootstrap_sequence` target; Task 14 scenario 72 |
| OQ-3 | KimiCode emits only `kimi-code/…` model IDs (exactly one prefix) | Task 4 (`model-format`/`model-catalog`), Task 7 |
| OQ-6 | Antigravity emits `model: inherit` instead of concrete tier IDs | Task 4 (`model-literal: inherit`), Task 6 |
| OQ-9 | Fix the `roles` enum at `templates/configs/CONTINUE.config-template.yaml:28` (`agent` is outside the runtime enum) | Task 9 (new file owner) |

### Ownership placements (no new task invented)

- **`templates/configs/CONTINUE.config-template.yaml` → Task 9.** Task 9 already owns the Continue notation surface and the `Continue` block of `config/delegation-syntax.yaml` (`bootstrap_sequence.target: .continue/config.yaml`), so the Continue config template is placed there. Added as `Modify:` in Task 9's `Files:` block; verified disjoint from Tasks 1–8 and 10–20 (no other task lists this path).
- **OQ-2 (dead `agents:` block) → Task 10.** Both write sites are Task 10 files: `scripts/lib/bootstrap.py::_bootstrap_config_based` writes the top-level `agents:` block (bootstrap.py:191-227) and `scripts/lib/context.py:1288` emits the `# Agents : .continue/agents/  (auto-discovered by Continue)` header comment. Task 9 keeps the `bootstrap_sequence` config target and annotates it; Task 14 (scenario 72) asserts the resulting `.continue/config.yaml`.
- **AC-12 split (2026-10-02):** the resolver half (`roles.py` precedence + `apply_model_format`) is delivered and tested by Task 7; the `model-inherit-fallback` transform half (`provider_transform.py:290-296` must route the raw value through `_resolve_tier_to_model` and emit no `model:` field when it stays a tier) is owned by Task 6, which owns that file. Precedence interpretation: the spec sentence 'a preset tiers map is a fallback' applies to the preset's GLOBAL `tiers` map; a preset's provider-specific `providers.<P>.tiers` entry remains an explicit per-provider override (pinned by a Task-7 regression test).

### Repo facts verified read-only (path / routing placement)

- **Mammouth routing entry.** The generated banner `> **AI ROUTING:** … | Mammouth -> MAMMOUTH.md | …` is produced by `scripts/lib/config.py::_build_provider_variables` (config.py:1376-1396), which groups active providers by their declared `context_file` (`config/ai-providers.yaml`). Retiring the entry is a pure data consequence of PRE-5: setting Mammouth `context_file: AGENTS.md` (Task 4) merges Mammouth into the `AGENTS.md` group, so no `Mammouth -> MAMMOUTH.md` target is emitted. **No `config.py` code change is required**, so `config.py` stays out of every `Files:` block (ownership unchanged).
- **`MAMMOUTH.md`.** `config/ai-providers.yaml` currently sets `context_file: MAMMOUTH.md` (line 372) and `context_adapter_file: MAMMOUTH.md` (line 377); Task 4 repoints both to `AGENTS.md`. No root `MAMMOUTH.md` exists in this checkout; Task 16 removes any generated `MAMMOUTH.md` (and confirms `sync.py --check` rc 0) as part of the in-scope 27-file regeneration.
- **OQ-9.** `templates/configs/CONTINUE.config-template.yaml:28` reads `roles: [chat, edit, agent]`; `agent` is outside the runtime `roles` enum (design §1.3 CO-2, F7/N11). It is declared as Continue `settings_template` at `config/ai-providers.yaml:282`.
- **OQ-3.** `config/ai-providers.yaml` KimiCode `model-tiers` currently read `kimi-k2.6`/`kimi-k2.7-code` with empty `model-aliases` (lines 576-582); Task 4 adds the `kimi-code/{model}` `model-format` + an initial `model-catalog`, and Task 7 guarantees the prefix is applied exactly once.
- **OQ-6.** No separate Antigravity entry exists in `config/ai-providers.yaml` (the Antigravity runtime is covered by the `Gemini` provider); Task 4 adds the `model-literal: inherit` data key and Task 6 makes the transform emit `inherit` verbatim instead of an injected tier ID.
- Task 7 also rebaselines `tests/test_tier_presets.py` and `tests/test_provider_toml_transform.py` (stale bare KimiCode IDs; owned by no other task, disjoint).
- Task 5 completes Task 4's ZCode/KimiCode `skills` capability data side (spec §2.1:161/§2.2:176): `config/ai-providers.yaml` gains `- skills` in both `capabilities` lists and `config/provider-capabilities.yaml` flips both `skills: false → true` (the AC-25 coupling is already satisfied by the non-null `skills_dir`). It also updates `tests/test_plugin_compact_provider_fix.py`'s now-obsolete "no lazy channel" premise — both providers now have a lazy channel via `"skills" in capabilities`. Task 4 is already committed (01b7f4c3); Task 5 completes its ZCode/KimiCode `skills` capability lines (no checkbox toggled).

## Global Constraints

- **Provider-Agnostik (project `CODE_CONVENTIONS`):** no `if provider == "…"` / `provider in (…)` in `scripts/lib/` — dispatch only on config values / capability flags. Repeated in every affected task note and guarded by AC-14 (Task 13).
- **Ordering & dependency:** config data (Task 4) before the code that consumes it; the validator core (Task 1) before integration (Task 3, Task 6); the sweep guard (Task 13) after all lib modules exist; the release bump (Task 15) after all behavior + scenario tasks (1–14) and before repo regeneration (Task 16); the regeneration commit (Task 17) last.
- **Review gate after every task (plan-ledger):** Stage 1 `review-req` (evidence vs. the task's acceptance criterion) -> Stage 2 `review-quality` (code quality / blast radius). Both loops `max_iterations: 2`; aggregate cap `task-review.max-rounds: 4`. On reaching the cap the task stays open and is reported to the human. No next task starts before both stages pass.
- **Bite-sized & TDD:** each task writes its test first (red), implements, observes green, commits. No task is done on assumed green.
- **Ownership is globally disjoint:** no file appears in two tasks' `Files:` blocks. The repo's plan check (`spec_plan.py::_check_plan_graph`, `FanoutPlan(kind="sequential")` + `check_plan_file_overlap`) treats *any* overlap between two tasks as an ERROR; parallel groups additionally require disjoint ownership. Shared-file edits are consolidated into a single owning task.
- **No worktree isolation:** never spawn with `isolation: "worktree"` (`no-worktree-isolation`). Substitutes are Ownership + Barriers + Checkpoint-ledger. Repo-containment (root + `.tmp/`) is untouched.
- **Parallel ceiling:** `max-parallel-agents: 2` (project.yaml default). Every barrier/parallel group has at most 2 tasks.
- **Fail-loud reason gate:** `artifact-validation: false` requires a non-empty `artifact-validation-reason` (L-8 / AC-24).
- **Stdlib only:** new modules (`artifact_validate.py`, `consistency/artifact_contracts.py`, `consistency/model_contracts.py`) use `from __future__ import annotations` and only the standard library; `scripts/consistency-check.py` returns rc 0 on a clean tree once PRE-1 is resolved.

## File Structure

Create:
- `config/provider-migrations.yaml` — provider-agnostic old→new path migration map (per-provider `remove` targets with an optional `requires-flag`); sole owner **Task 11**, so Task 4 keeps exclusive ownership of `config/ai-providers.yaml`.
- `scripts/lib/artifact_validate.py` — provider-agnostic `validate_toml`, `validate_frontmatter`, `validate_json_document` returning `list[Finding]`.
- `scripts/lib/consistency/artifact_contracts.py` — `check_artifact_contracts(agent_meta_root)` (Severity.ERROR) over generated artifacts.
- `scripts/lib/consistency/model_contracts.py` — model-format/prefix + `model-catalog` consistency check.
- `tests/test_artifact_contracts.py` — validator unit tests + narrow `allowed-fields` fixture + `--validate` rc 1 end.
- `tests/test_consistency_checks.py` — the two consistency modules registered and producing ERROR/SKIP as specified.
- `tests/test_sync_validation_gate.py` — `_finalize_agent_content` integration + `--check`/`--validate` exit-code policy.
- `tests/test_provider_config_contracts.py` — presence/shape of new registry keys and migrated path values.
- `tests/test_transform_contracts.py` — `tools-format: map`, `tool-name-map`, `reject-fields`, `opencode-native-v2`.
- `tests/test_model_contracts.py` — `model-format` applied once, `model-tiers` precedence, no raw tier token.
- `tests/test_pipeline_notation_config.py` — notation read from `delegation-syntax.yaml`, missing block fails loud, Copilot via registry.
- `tests/test_bootstrap_submarkers.py` — distinct sub-markers, registry-keyed cleanup, legacy-marker migration (AC-16 a/b/c).
- `tests/test_migration_paths.py` — old->new path migration, backup, user-file guard, rollback (AC-22).
- `tests/scenarios/configs/64-codex-toml-validity.project.yaml` — Codex singleton/TOML validity.
- `tests/scenarios/configs/65-kimicode-model-namespace.project.yaml` — Kimi `kimi-code/*` namespace.
- `tests/scenarios/configs/66-mammouth-tools-map.project.yaml` — Mammouth `tools-format: map`.
- `tests/scenarios/configs/67-copilot-artifact-paths.project.yaml` — Copilot corrected paths.
- `tests/scenarios/configs/68-antigravity-discovery-paths.project.yaml` — Antigravity `.agents/*` + `serverUrl`; sets `agent-discovery: true` (opt-in fixture; shipped default is `false`).
- `tests/scenarios/configs/69-opencode-v2-surface.project.yaml` — Opencode `surface-version: v2`, `mcp.servers`, `default_agent`.
- `tests/scenarios/configs/70-bootstrap-marker-convergence.project.yaml` — Gemini+ZCode distinct sub-markers.
- `tests/scenarios/configs/71-check-idempotency-all-providers.project.yaml` — fixture profile **all-9-providers** (Claude, Gemini, Opencode, Continue, Copilot, Mammouth, Codex, ZCode, KimiCode).
- `tests/scenarios/configs/72-continue-config-validity.project.yaml` — Continue Zod-valid config.
- `tests/scenarios/asserts/64-codex-toml-validity.sh` … `tests/scenarios/asserts/72-continue-config-validity.sh` — one executable assert per new scenario (cwd = temp project, `REPO_ROOT` as `$1`/env; convention `tests/scenarios/asserts/62-stale-role-cleanup.sh`).

Modify:
- `scripts/consistency-check.py` — register `check_artifact_contracts` and `check_model_contracts` in `run_checks` (next to `check_fanout_backend_contract`).
- `scripts/lib/agent_sync.py` — singleton constraint inside the body before serialization; call `artifact_validate` before `_write_agent_file`.
- `scripts/sync.py` — `--check` rc 1 on pending writes **or** ERROR findings; `--validate` rc 1 on ERROR findings.
- `scripts/lib/provider_transform.py` — `tools-format` (keep/filter/skip/remove/map), `tool-name-map`, `model-format` hook, `allowed-fields`/`reject-fields`, `frontmatter-mechanism` incl. `opencode-native-v2`; neutralise the D5 strip rule.
- `scripts/lib/roles.py` — `ai-providers.yaml model-tiers` authoritative over preset `tiers`; `model-format` applied exactly once.
- `scripts/lib/mcp_provider_config.py` — new `elif fmt == "opencode-json-v2"` nested `mcp.servers` branch (precedent `_update_zcode_json_config`) + transport/header spellings for `antigravity-mcp-json`/`kimi-json`/`codex-toml-mcp`/`continue-yaml`.
- `scripts/lib/pipelines.py` — `pipeline_notation()` reads `delegation-syntax.yaml`; missing block fails loud; `KNOWN_PROVIDERS` replaced by `providers.registered_provider_names(agent_meta_root)`.
- `scripts/lib/bootstrap.py` — expose the set of providers claiming a context file (registry-keyed cleanup input).
- `scripts/lib/context.py` — registry-keyed `_cleanup_bootstrap_block` + legacy unscoped marker discard/migration (M-6).
- `scripts/lib/sync_pipeline.py` — path-migration sequencing; pending-write computation on the final (post-cleanup) content.
- `scripts/lib/generated_file_drift.py` — backup-first managed delete + final-content diff.
- `scripts/lib/context_templates/builder.py` — Continue managed-block substitution on run 1 (run1 = fixpoint).
- `config/ai-providers.yaml` — new contract keys + migrated path values.
- `config/provider-capabilities.yaml` — `skills`, `artifact-validation`, `artifact-validation-reason`, `mcp-remote-transport`.
- `config/delegation-syntax.yaml` — per-provider `pipeline_notation` blocks.
- `config/provider-bootstrap.yaml` — `marker_id`, `context_file`, `instructions_mode`.
- `templates/configs/CONTINUE.config-template.yaml` — fix the `roles` enum at line 28 (`agent` is not a runtime role); OQ-9, owned by Task 9.
- `agents/1-generic/agent-meta-manager.md`, `agents/1-generic/agent-meta-scout.md`, `agents/1-generic/release.md` — provider-neutral body references (D5; 5 distinct refs across 3 files).
- `tests/test_provider_three_file_invariant.py` — skills + artifact-validation presence, reason gate, skills coupling.
- `tests/test_mcp_config.py` — `requestOptions.headers`, `http_headers`, `transport: sse`, `serverUrl`, v2 nesting, v1 byte shape.
- `tests/test_context_agents_md_idempotency.py` — run1 == run2 for all providers.
- `tests/test_provider_agnostic_dispatch.py` — `_TOUCHED_MODULES` replaced by a `scripts/lib/**/*.py` sweep.
- `tests/scenarios/registry.md` — one Katalog row per new scenario (64–72).
- Generated managed artifacts (~27 files under `.claude/`, `.gemini/`, `.agents/`, `.opencode/`, `.continue/`, `.github/`, `.mammouth/`, `.codex/`, `.zcode/`, `.kimi-code/` and root context files) — branch hygiene (Task 16).

## Interfaces (file:Symbol — contract)

- `scripts/lib/artifact_validate.py:validate_toml(text: str, path: str) -> list[Finding]` — parse with `tomllib`; ERROR on any parse failure.
- `scripts/lib/artifact_validate.py:validate_frontmatter(text: str, *, allowed_fields: set[str] | None, required_fields: set[str], reject_fields: set[str], path: str) -> list[Finding]` — ERROR for missing required, out-of-allow-list, or rejected keys.
- `scripts/lib/artifact_validate.py:validate_json_document(text: str, fmt: str, path: str) -> list[Finding]` — per-format key-set assertions (`opencode-json-v2` requires `mcp.servers` and no flat `mcp`; `opencode-json` requires flat `mcp`).
- `scripts/lib/consistency/artifact_contracts.py:check_artifact_contracts(agent_meta_root: Path) -> list[Finding]` — scans generated artifacts, Severity.ERROR.
- `scripts/lib/consistency/model_contracts.py:check_model_contracts(agent_meta_root: Path) -> list[Finding]` — emitted model matches `model-format` and is present in `model-catalog` when configured.
- `scripts/lib/roles.py:apply_model_format(model, provider_config, provider)` — `provider_config["model-format"].format(model=model)`, default `"{model}"`.
- `scripts/lib/roles.py:resolve_model` — `ai-providers.yaml model-tiers` wins; empty for unresolvable override-all; no raw tier token.
- `scripts/lib/mcp_provider_config.py:_write_provider_config` — dispatch on `mcp-config.format` only; new `opencode-json-v2` branch writes nested `mcp.servers`.
- `scripts/lib/pipelines.py:pipeline_notation(provider: str, config_dir: Path) -> dict` — reads `delegation-syntax.yaml`; a missing block is fail-loud.
- `scripts/lib/bootstrap.py` — exposes the inject-provider/context-file mapping consumed by `context._cleanup_bootstrap_block`.
- `scripts/lib/context.py:_cleanup_bootstrap_block` — keeps `bootstrap-begin:{marker_id}` iff the provider is active; discards the legacy unscoped pair once.

## Task Steps

Every task: write the test first (red) -> implement -> observe green -> commit with the named message. After every task the plan-ledger review (`review-req` -> `review-quality`) runs before the next task starts. Every task repeats: **Provider-Agnostik — no `if provider ==` / provider-name literal; only config keys / capability flags.**

### Task 1: Artifact validator core
**Agent:** senior-developer
**Files:** Create: `scripts/lib/artifact_validate.py`; Create: `tests/test_artifact_contracts.py`
**Interfaces:** Produces `validate_toml`, `validate_frontmatter`, `validate_json_document`; Consumes `scripts/lib/consistency/report.py::{Finding, Severity}`.
**Acceptance:** AC-13 (narrow `allowed-fields` fixture: an injected extra frontmatter key yields a `Finding`; `validate_toml` rejects malformed TOML; `validate_json_document` asserts v2 nesting).
**Verify:** `python3 -m pytest tests/test_artifact_contracts.py -q`
**Provider-Agnostik:** format is a parameter; no provider name is read.
**Depends on:** none
- [x] Step 1: Test schreiben (fail)
- [x] Step 2: implementieren
- [x] Step 3: Test (pass)
- [x] Step 4: commit — `feat: add provider-agnostic artifact validators`

### Task 2: Consistency checks (artifact + model) + registration
**Agent:** developer
**Files:** Create: `scripts/lib/consistency/artifact_contracts.py`; Create: `scripts/lib/consistency/model_contracts.py`; Modify: `scripts/consistency-check.py`; Create: `tests/test_consistency_checks.py`
**Interfaces:** Produces `check_artifact_contracts`, `check_model_contracts`, both registered in `run_checks`; Consumes `artifact_validate` (Task 1) and the `model-catalog` config key.
**Acceptance:** AC-17 (consistency side) + AC-2: `python3 scripts/consistency-check.py` returns rc 0 on the clean tree; a corrupted fixture yields an ERROR; an emitted model outside a configured `model-catalog` is fail-loud.
**Verify:** `python3 -m pytest tests/test_consistency_checks.py -q` and `python3 scripts/consistency-check.py; echo $?` -> `0`
**Provider-Agnostik:** iteration is registry/catalog-driven; no name literals.
**Depends on:** 1
- [x] Step 1: Test schreiben (fail)
- [x] Step 2: implementieren
- [x] Step 3: Test (pass)
- [x] Step 4: commit — `feat: register artifact and model consistency checks`

### Task 3: Sync-time validation wiring + exit codes
**Agent:** senior-developer
**Files:** Modify: `scripts/lib/agent_sync.py`; Modify: `scripts/sync.py`; Create: `tests/test_sync_validation_gate.py`
**Interfaces:** Produces `_finalize_agent_content` (singleton inside the body before serialization, validator called before write) and the `--check`/`--validate` rc policy; Consumes Task-1 validators.
**Acceptance:** AC-13 (sync end) + AC-3a: a scratch project with a narrowed `allowed-fields` makes `sync.py --validate` return rc 1; a normal sync stays rc 0 and logs `[WARN] artifact-contract:`.
**Verify:** `cd <scratch> && python3 <repo>/scripts/sync.py --validate; echo $?` -> `1`; `python3 -m pytest tests/test_sync_validation_gate.py -q`
**Provider-Agnostik:** findings are logged per provider from config, never from a name branch.
**Depends on:** 1
- [x] Step 1: Test schreiben (fail)
- [x] Step 2: implementieren
- [x] Step 3: Test (pass)
- [x] Step 4: commit — `feat: surface artifact findings in sync check/validate`

### Task 4: Provider registry contract data (`ai-providers.yaml`)
**Agent:** senior-developer
**Files:** Modify: `config/ai-providers.yaml`; Modify: `tests/test_provider_hooks_config.py`; Create: `tests/test_provider_config_contracts.py`
**Files rationale:** `tests/test_provider_hooks_config.py` is included because Task 4's Mammouth `context_file: AGENTS.md` change breaks `_INTENTIONAL_AGENTS_MD_SHARERS` at `tests/test_provider_hooks_config.py:142`, so that constant must be updated inside Task 4; the file is owned by no other task, so this adds no overlap.
**Interfaces:** Produces keys `agent-discovery` (bool, `config/ai-providers.yaml` §2.1), `surface-version`, `model-format`, `model-catalog`, `agent-transform.{tools-format,tool-name-map,allowed-fields,reject-fields,frontmatter-mechanism}`, `mcp-config.format` (`opencode-json`/`opencode-json-v2`/`antigravity-mcp-json`/`kimi-json`/`codex-toml-mcp`/`continue-yaml`), `primary-role`, `model-literal`, plus the migrated path values; Consumes PRE-2/PRE-3/PRE-4/PRE-5/PRE-6.
**Discovery sub-map shape (authoritative — Tasks 6/8/11 MUST consume):**
```yaml
discovery:
  agents_dir: .agents/agents
  rules_dir: .agents/rules
  skills_dir: .agents/skills
  mcp-config:
    committed-file: .agents/mcp_config.json
    format: antigravity-mcp-json
```
**Consumption contract:** path resolution (Tasks 6/11) selects `discovery.*` iff `agent-discovery: true`, else the top-level keys; MCP (Task 8) selects `discovery["mcp-config"]["format"]` iff `agent-discovery: true`, else the top-level `mcp-config.format`; dispatch on the bool + presence of `discovery`, never on the provider name.
**Full-suite note (sequencing):** Two cross-task reds are expected after Task 4 and are **not** Task-4 defects: (a) `tests/test_mcp_config.py::test_kimicode_mcp_config_reuses_claude_settings_format` stays red until Task 8 lands (KimiCode `mcp-config.format: kimi-json` vs. the old `claude-settings` assertion); (b) `tests/test_context_compact_mode.py::test_committed_agents_md_equals_configured_mode_render` stays red until Task 16 regeneration (Mammouth now shares `AGENTS.md` and adds `.mammouth/skills` to the rendered sharer line while the committed `AGENTS.md` is stale) — this is the pre-existing 27-file drift, resolved by Task 16's `sync.py` regeneration.
**Acceptance:** AC-21 (config side) + AC-25 (data side) + AC-8/AC-9 (values): every provider declares the new keys with correct types and defaults; Antigravity declares `agent-discovery: false` (bool, default `false`) gating the `.agents/*` discovery surface (AC-9, default-off); KimiCode `model-format: "kimi-code/{model}"` with an initial catalog; Mammouth `tools-format: map`; Opencode `surface-version: v1` default while `v2` selects `opencode-json-v2`; Copilot `agents_dir`/`context_file`/`rules_dir` and Gemini/Antigravity `agents_dir`/`rules_dir`/`skills_dir` carry the new paths; Antigravity carries a populated `agent-transform.tool-name-map` (G-2: `Read`→`view_file`, `Write`→`replace_file_content`, `Grep`→`grep_search`, `Bash`→`run_command`, per docs-part1 §2.1) so G-2 tool vocabulary is data, not code.
**Resolved values (Amendment 2026-10-01):** PRE-2 — Antigravity discovery gated by the concrete key **`agent-discovery: false`** in `config/ai-providers.yaml` §2.1 (bool, default `false`), gates the `.agents/*` discovery surface, present and **default-off**; PRE-3 — Opencode `primary-role: orchestrator` (`mode: primary`, consumed by Task 6); PRE-4 — Copilot `agents_dir: .github/agents` + `agent_ext: .agent.md`; PRE-5 — Mammouth `context_file: AGENTS.md` and `context_adapter_file: AGENTS.md` (no `MAMMOUTH.md` target); PRE-6 — `surface-version: v1` default (v2 opt-in); OQ-3 — KimiCode `model-format: "kimi-code/{model}"` + initial `model-catalog`; OQ-6 — Antigravity `model-literal: inherit`.
**Verify:** `python3 -m pytest tests/test_provider_config_contracts.py -q` (asserts `agent-discovery` is a bool present for Antigravity with value `false`)
**Provider-Agnostik:** values only — no code branch.
**Depends on:** none
- [x] Step 1: Test schreiben (fail)
- [x] Step 2: implementieren
- [x] Step 3: Test (pass)
- [x] Step 4: commit — `feat: add provider contract keys and migrated paths`

### Task 5: Capability flags (`provider-capabilities.yaml`)
**Agent:** developer
**Files:** Modify: `config/provider-capabilities.yaml`; Modify: `tests/test_provider_three_file_invariant.py`; Modify: `config/ai-providers.yaml`; Modify: `tests/test_plugin_compact_provider_fix.py`
**Interfaces:** Produces `skills`, `artifact-validation`, `artifact-validation-reason`, `mcp-remote-transport`; Consumes Task-4 data.
**Acceptance:** AC-15 + AC-24 + AC-25: every provider declares `skills` and `artifact-validation`; `artifact-validation: false` requires a non-empty reason; `skills: true` requires `skills` in the `ai-providers.yaml capabilities` list and a non-null `skills_dir`.
**Verify:** `python3 -m pytest tests/test_provider_three_file_invariant.py -q`
**Provider-Agnostik:** flags only; no name check.
**Depends on:** 4
- [x] Step 1: Test schreiben (fail)
- [x] Step 2: implementieren
- [x] Step 3: Test (pass)
- [x] Step 4: commit — `feat: declare skills and artifact-validation capability flags`

### Task 6: Transform format contracts
**Agent:** senior-developer
**Files:** Modify: `scripts/lib/provider_transform.py`; Create: `tests/test_transform_contracts.py`
**Interfaces:** Consumes `roles.py:apply_model_format`; `tools-format: map`; `tool-name-map`; `allowed-fields`/`reject-fields`; `frontmatter-mechanism` incl. `opencode-native-v2`; Consumes Task-1 validators and Task-4 config.
**Acceptance:** AC-6 (Mammouth `tools:` object, never a list) + AC-13 (`reject-fields` violation yields a finding). + D3/AC-12: the `model-inherit-fallback` at `provider_transform.py:290-296` resolves through `_resolve_tier_to_model` and never emits a raw tier token; covered in `tests/test_transform_contracts.py`.
**Resolved values (Amendment 2026-10-01):** OQ-6 — Antigravity emits `model: inherit` verbatim (driven by `model-literal`, no injected tier ID); PRE-3 — the `opencode-native-v2` mechanism emits the primary-role entry (`orchestrator`, `mode: primary`) from the `primary-role` data key.
**Verify:** `python3 -m pytest tests/test_transform_contracts.py -q`
**Provider-Agnostik:** every mechanism is selected by the config value; no name branch.
**Depends on:** 1, 4
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `feat: extend agent transform with format contracts`

### Task 7: Model precedence + single format application
**Agent:** developer
**Files:** Modify: `scripts/lib/roles.py`; Modify: `tests/test_tier_presets.py`; Modify: `tests/test_provider_toml_transform.py`; Create: `tests/test_model_contracts.py`
**Interfaces:** Produces `resolve_model` (ai-providers `model-tiers` wins over preset `tiers`; `model-format` applied once); Consumes Task-4 data.
**Acceptance:** AC-12 + AC-2: an active tier preset no longer shadows `ai-providers.yaml model-tiers`; emitted IDs carry exactly one `kimi-code/` prefix. (resolver half of AC-12; the transform half is Task 6).
**Resolved values (Amendment 2026-10-01):** OQ-3 — KimiCode aliases resolve only through the `kimi-code/…` namespace; the single-prefix assertion covers `kimi-code/kimi-code/*` never leaking (Task 4 data + this task's once-only application).
**Verify:** `python3 -m pytest tests/test_model_contracts.py -q`
**Provider-Agnostik:** precedence is generic; no provider name.
**Depends on:** 4
- [x] Step 1: Test schreiben (fail)
- [x] Step 2: implementieren
- [x] Step 3: Test (pass)
- [x] Step 4: commit — `fix: make provider model-tiers authoritative`

### Task 8: MCP writer format dispatch
**Agent:** senior-developer
**Files:** Modify: `scripts/lib/mcp_provider_config.py`; Modify: `tests/test_mcp_config.py`
**Interfaces:** Produces the `opencode-json-v2` branch (nested `mcp.servers`) and the transport/header spellings; Consumes Task-4 `mcp-config.format`.
**Acceptance:** AC-21 + AC-23 + AC-7 + AC-9: with `opencode-json-v2` the document contains `mcp.servers` and no flat `mcp`; with `opencode-json` the v1 flat byte shape is unchanged; Continue uses `requestOptions.headers`, Antigravity uses `serverUrl`, Codex uses `http_headers` (CX-1); the generated `.continue/config.local.yaml` carries `name`/`version` so it passes the Continue schema (AC-7); no writer branch reads `surface-version`.
**Verify:** `python3 -m pytest tests/test_mcp_config.py -q`
**Provider-Agnostik:** dispatch on the format string only (H-1 / ADR-10).
**Depends on:** 4
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `fix: dispatch mcp writers by declared format`

### Task 9: Pipeline notation from config + full registry
**Agent:** developer
**Files:** Modify: `config/delegation-syntax.yaml`; Modify: `scripts/lib/pipelines.py`; Modify: `templates/configs/CONTINUE.config-template.yaml`; Create: `tests/test_pipeline_notation_config.py`
**Interfaces:** Produces `pipeline_notation.<Provider>` blocks and `pipeline_notation(provider, config_dir)` (config-backed, fail-loud) + registry provider list; Consumes evidence D6/D7.
**Acceptance:** AC-11: every provider has a complete notation block consistent with its `delegate` phrasing; notation comes from `delegation-syntax.yaml`; a missing block fails loud (no `task()` default); Copilot resolves via `registered_provider_names`.
**Resolved values (Amendment 2026-10-01):** OQ-9 — the `roles` enum at `templates/configs/CONTINUE.config-template.yaml:28` no longer contains the out-of-enum value `agent` (fix the enum; do not restructure the template); OQ-2 — keep/annotate the Continue `bootstrap_sequence.target` (`.continue/config.yaml`), whose dead `agents:` block is removed by Task 10.
**Ownership note:** this is the sole owner of `templates/configs/CONTINUE.config-template.yaml` (placed here because Task 9 owns the Continue notation surface; disjoint from all other tasks).
**Verify:** `python3 -m pytest tests/test_pipeline_notation_config.py -q`
**Provider-Agnostik:** provider list and notation are registry/config-driven.
**Depends on:** 4
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `feat: add config-backed pipeline notation`

### Task 10: Bootstrap sub-markers + legacy migration
**Agent:** senior-developer
**Files:** Modify: `scripts/lib/bootstrap.py`; Modify: `scripts/lib/context.py`; Modify: `config/provider-bootstrap.yaml`; Create: `tests/test_bootstrap_submarkers.py`
**Interfaces:** Produces `marker_id`/`context_file`/`instructions_mode` data and registry-keyed `_cleanup_bootstrap_block`; Consumes Task-4 context files.
**Acceptance:** AC-10 + AC-16 (a/b/c): Gemini+ZCode carry one scoped pair each; inactive-provider scoped markers are removed; the legacy unscoped pair is discarded and rebuilt per provider; user notes outside markers survive.
**Resolved values (Amendment 2026-10-01):** OQ-2 — remove the dead top-level `agents:` block from the generated `.continue/config.yaml` (`bootstrap.py::_bootstrap_config_based`, bootstrap.py:191-227) and change the generated header comment (`context.py:1288`) so it states the auto-load is `cn review`-only, not a chat auto-discovery surface; `.continue/agents/*.md` keep being generated (read by `cn review`).
**Verify:** `python3 -m pytest tests/test_bootstrap_submarkers.py -q`
**Provider-Agnostik:** cleanup iterates the bootstrap registry, replacing `"Gemini" in active`.
**Depends on:** 4
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `fix: scope bootstrap markers per provider`

### Task 11: Path migration + idempotency / pending-write fix
**Agent:** senior-developer
**Files:** Modify: `scripts/lib/sync_pipeline.py`; Modify: `scripts/lib/generated_file_drift.py`; Modify: `scripts/lib/context_templates/builder.py`; Create: `config/provider-migrations.yaml`; Create: `tests/test_migration_paths.py`; Modify: `tests/test_context_agents_md_idempotency.py`
**Interfaces:** Produces the ordered migration sequence (write-new -> **verify** -> backup-old -> remove-old), backup-first managed delete, the final-content diff (wired into production, not test-only), the flag-gated `migrate_discovery_artifacts` migrator **now also running for Copilot without a flag**, and Continue run1 substitution; Consumes Task-4 path values and the `config/provider-migrations.yaml` migration map (iterated by map key; dispatch on the map + the named bool flag, never on a provider name).
**Acceptance:** AC-22 + AC-3a + AC-4 + AC-18: the new path exists, the old managed path is gone, each removed managed file has a byte-exact `.sync-backup-<ts>` sibling, user-authored files are never deleted, renaming the backup restores the file; after a clean scratch sync `--check` rc 0 and `sha256(run1)==sha256(run2)`; a managed-block edit is rc 1, an out-of-block edit rc 0. **AC-22 default-on path (review F1):** the Copilot old→new migration runs with **no flag** (`Copilot` map entry has no `requires-flag`); the Gemini entry runs **only when `agent-discovery: true`**; a **Copilot fixture** asserts old-path-gone + byte-exact `.sync-backup-<ts>` + rollback-by-rename + user-file guard, and a discovery-off fixture proves the Gemini paths are untouched. **Review F2/F3:** the `verify` step and the final-content pending diff are wired into production (`sync_pipeline.py` / `generated_file_drift.py`).
**Verify:** `python3 -m pytest tests/test_migration_paths.py tests/test_context_agents_md_idempotency.py -q`
**Shared-render convergence note (added 2026-10-01):** `tests/test_agents_md_shared_context_convergence.py` and `tests/test_context_file_modes.py` carry shared-tuple expectations that omit Mammouth and must be updated here; this is a shared-render convergence concern (Mammouth now reads `AGENTS.md`) and is assigned to Task 11 (Tests/Idempotency), not to Task 4.
**Provider-migration map (authoritative data contract — Task 11 consumes the field names; two accepted shapes):**
```yaml
# config/provider-migrations.yaml
migrations:
  Copilot:                     # default-on migration (no flag): bare-list shape
    - remove: .github/copilot/agents
      kind: dir
    - remove: .github/copilot/rules
      kind: dir
    - remove: .github/copilot/COPILOT.md
      kind: file
  Gemini:                      # flag-gated shape: a mapping with `requires-flag` + `removals`
    requires-flag: agent-discovery
    removals:
      - remove: .gemini/agents
        kind: dir
      - remove: .gemini/rules
        kind: dir
      - remove: .gemini/skills
        kind: dir
```
The migrator normalizes both shapes: a bare list = default-on; `{requires-flag, removals: [...]}` = flag-gated. (Corrected 2026-10-01 after the Task-11 review found the earlier snippet was invalid YAML.)
**Consumption contract:** the migrator iterates `migrations`; for each provider it runs only if (no `requires-flag`) OR (the named bool flag is truthy); every `remove` target is a managed artifact deleted backup-first (byte-exact `.sync-backup-<ts>`), user-authored files preserved, rollback by rename; dispatch on the map + flag name, never on the provider name. This preserves Task-4's exclusive ownership of `config/ai-providers.yaml` (the migration data lives in this new, Task-11-only file) while satisfying AC-22 / design §6.2.1 / spec §11.1 (Copilot default-on, Gemini discovery-gated).
**Depends on:** 4
**Provider-Agnostik:** migration and diff are driven by config keys; no name branch.
- [x] Step 1: Test schreiben (fail)
- [x] Step 2: implementieren
- [x] Step 3: Test (pass)
- [x] Step 4: commit — `feat: migrate artifact paths and stabilise pending writes`

### Task 12: Provider-neutral template body references (D5)
**Agent:** junior-developer
**Files:** Modify: `agents/1-generic/agent-meta-manager.md`; Modify: `agents/1-generic/agent-meta-scout.md`; Modify: `agents/1-generic/release.md`
**Interfaces:** Produces provider-neutral phrasing for the five refs (`.claude/agents`, `.claude/skills/model-override-all/SKILL.md`, `.claude/commands/evaluate-repository.md`, `.claude/hooks/pre-release-check.sh`); Consumes the placeholder scheme.
**Acceptance:** ADR-6 (spec §12): after a sync into a non-Claude scratch project, the five `.claude/`-prefixed refs no longer appear in the generated bodies of the three roles.
**Verify:** `cd <scratch> && python3 <repo>/scripts/sync.py >/dev/null && ! grep -RE '\.claude/(agents|skills/model-override-all|commands/evaluate-repository|hooks/pre-release-check)' .codex .zcode .kimi-code`
**Provider-Agnostik:** neutral wording; no provider name literal.
**Depends on:** none
- [x] Step 1: Test schreiben (fail)
- [x] Step 2: implementieren
- [x] Step 3: Test (pass)
- [x] Step 4: commit — `docs: provider-neutral template body references`

### Task 13: Provider-agnostic sweep guard
**Agent:** developer
**Files:** Modify: `tests/test_provider_agnostic_dispatch.py`
**Interfaces:** Produces a `scripts/lib/**/*.py` directory sweep replacing `_TOUCHED_MODULES`; Consumes all Task 1–11 lib modules.
**Acceptance:** AC-14 + AC-23: no `if provider ==` / provider-name literal in `scripts/lib/`; no `surface-version` comparison in `scripts/lib/`.
**Verify:** `python3 -m pytest tests/test_provider_agnostic_dispatch.py -q`
**Provider-Agnostik:** this task *is* the guard.
**Depends on:** 1, 2, 3, 6, 7, 8, 9, 10, 11
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `test: sweep scripts/lib for provider-name branches`

### Task 14: Scenarios 64–72 + asserts + registry
**Agent:** tester
**Files:** Create: `tests/scenarios/configs/64-codex-toml-validity.project.yaml`; Create: `tests/scenarios/configs/65-kimicode-model-namespace.project.yaml`; Create: `tests/scenarios/configs/66-mammouth-tools-map.project.yaml`; Create: `tests/scenarios/configs/67-copilot-artifact-paths.project.yaml`; Create: `tests/scenarios/configs/68-antigravity-discovery-paths.project.yaml`; Create: `tests/scenarios/configs/69-opencode-v2-surface.project.yaml`; Create: `tests/scenarios/configs/70-bootstrap-marker-convergence.project.yaml`; Create: `tests/scenarios/configs/71-check-idempotency-all-providers.project.yaml`; Create: `tests/scenarios/configs/72-continue-config-validity.project.yaml`; Create: `tests/scenarios/asserts/64-codex-toml-validity.sh`; Create: `tests/scenarios/asserts/65-kimicode-model-namespace.sh`; Create: `tests/scenarios/asserts/66-mammouth-tools-map.sh`; Create: `tests/scenarios/asserts/67-copilot-artifact-paths.sh`; Create: `tests/scenarios/asserts/68-antigravity-discovery-paths.sh`; Create: `tests/scenarios/asserts/69-opencode-v2-surface.sh`; Create: `tests/scenarios/asserts/70-bootstrap-marker-convergence.sh`; Create: `tests/scenarios/asserts/71-check-idempotency-all-providers.sh`; Create: `tests/scenarios/asserts/72-continue-config-validity.sh`; Modify: `tests/scenarios/registry.md`
**Interfaces:** Produces nine executable scenarios with mandatory asserts and registry rows; Consumes all implemented behavior. **Scenario 68 fixture note:** the `68-antigravity-discovery-paths.project.yaml` fixture sets `agent-discovery: true` (opt-in) to exercise the `.agents/*` discovery surface; the shipped default stays `false` (Task 4, AC-9, OQ-1) and the assert proves the flag gates the surface.
**Acceptance:** AC-19 + AC-4 + AC-5 + AC-7 + AC-8 + AC-9 + AC-22: scenarios 64–72 PASS, each with its own `asserts/<id>.sh` and Katalog row; scenario 71 ships the all-9-providers fixture proving `sha256(run1)==sha256(run2)` and `--check` rc 0; **scenario 68's fixture sets `agent-discovery: true` and its assert proves the `.agents/*` discovery surface is gated by that key (OQ-1: shipped default `false`).**
**Verify:** `bash tests/scenarios/run.sh 64 65 66 67 68 69 70 71 72`
**Provider-Agnostik:** assertions key on generated artifacts, not provider names.
**Depends on:** 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `test: add provider-audit scenarios 64-72`

### Task 15: Release + MAJOR version bump
**Agent:** release
**Files:** Modify: `VERSION`; Modify: `CHANGELOG.md`; Modify: `.meta-config/project.yaml`; Modify: `README.md` (only if it carries a version reference)
**Interfaces:** Produces the MAJOR version bump for this change (Copilot default-on path migration = MAJOR/breaking; Antigravity flag-gated and Opencode v2 opt-in = MINOR, dominated by the MAJOR) and the promoted `[Unreleased]` → new MAJOR CHANGELOG section; Consumes Tasks 1–14 (the released content) and PRE-6. It does **not** re-embed `{{AGENT_META_VERSION}}` into generated artifacts — that is Task 16.
**Acceptance:** the MAJOR bump (Copilot default-on path migration = breaking ⇒ MAJOR; Antigravity flag-gated + Opencode v2 opt-in would alone be MINOR, dominated by MAJOR) is recorded in `VERSION`, `.meta-config/project.yaml` (`agent-meta-version`) and `CHANGELOG.md` (`[Unreleased]` promoted to the new MAJOR section); version markers are updated (`grep`/read) and `git diff --stat` shows **ONLY** the four version files. This task MUST NOT run `python3 scripts/sync.py` and MUST NOT claim to re-embed the version — regeneration is Task 16.
**Verify:** version markers updated (`grep`/read) and `git diff --stat` shows only `VERSION`, `CHANGELOG.md`, `.meta-config/project.yaml` (and `README.md` if referenced)
**Provider-Agnostik:** version bookkeeping only — no provider name read; `{{AGENT_META_VERSION}}` substitution is provider-neutral and handled by the regeneration task (16).
**Depends on:** 14
- [ ] Step 1: bump `VERSION` + `.meta-config/project.yaml` (`agent-meta-version`) to the MAJOR version
- [ ] Step 2: promote `[Unreleased]` → the new MAJOR section in `CHANGELOG.md`; update any README version reference
- [ ] Step 3: verify version markers (`grep`/read) and confirm `git diff --stat` shows ONLY the four version files
- [ ] Step 4: commit — `chore(release): bump major version for provider audit`

### Task 16: Repo regeneration (27-file drift)
**Agent:** developer
**Files:** Modify: `.claude/agents/`; Modify: `.gemini/agents/`; Modify: `.agents/agents/`; Modify: `.opencode/agents/`; Modify: `.continue/agents/`; Modify: `.github/agents/`; Modify: `.mammouth/agents/`; Modify: `.codex/agents/`; Modify: `.zcode/agents/`; Modify: `.kimi-code/agents/`; Modify: `AGENTS.md`
**Interfaces:** Produces a drift-free repo checkout; Consumes all preceding tasks and PRE-7 (in-scope).
**Acceptance:** AC-3b: `sync.py --check` returns rc 0 at the repo root after regeneration and confirms the new embedded `{{AGENT_META_VERSION}}` (the MAJOR version bumped in Task 15) is present in the generated artifacts; each delta is inspected and any delta not explained by the new contracts is escalated, not committed silently.
**Resolved values (Amendment 2026-10-01):** PRE-7 — the 27-file drift is in-scope and regenerated here; PRE-5 — remove any generated root `MAMMOUTH.md` (backup-first per the migration rule) and confirm the generated `> **AI ROUTING:**` banner no longer contains a `Mammouth -> MAMMOUTH.md` entry (it merges into the `AGENTS.md` group once Task 4 sets `context_file: AGENTS.md`); the banner is regenerated by sync into every generated context file.
**Verify:** `python3 scripts/sync.py && python3 scripts/sync.py --check; echo $?` -> `0` (and the new `{{AGENT_META_VERSION}}` is embedded)
**Provider-Agnostik:** regeneration is config/template-driven.
**Depends on:** 15
- [ ] Step 1: regenerate with `python3 scripts/sync.py`
- [ ] Step 2: inspect the 27-file delta per file
- [ ] Step 3: `--check` rc 0
- [ ] Step 4: commit — `chore: regenerate drifted provider artifacts`

### Task 17: Commit regenerated artifacts
**Agent:** git
**Files:** none (commit only; Git mutation delegated to the `git` agent)
**Interfaces:** Produces the branch-hygiene commit closing AC-3b; Consumes Task-16 output.
**Acceptance:** AC-3b: the regenerated artifacts are committed on `feat/provider-audit-opencode-v2`; `git status` is clean afterwards.
**Verify:** `git status --porcelain` (empty) and `git log -1 --stat`
**Provider-Agnostik:** not applicable (commit only).
**Depends on:** 16
- [ ] Step 1: stage the regenerated artifacts
- [ ] Step 2: commit — `chore: commit regenerated provider artifacts`
- [ ] Step 3: confirm clean tree

### Task 18: Full verification gate (stage `validate`)
**Agent:** validator
**Files:** none (verification only; results recorded in this plan's ledger)
**Interfaces:** Consumes all tasks; Produces the verification verdict.
**Acceptance:** AC-17 + AC-19 + AC-20 + AC-18: `--validate` rc 0, `consistency-check.py` rc 0 (after PRE-1), full scenario catalog PASS, pytest without `tests/browser` PASS.
**Verify:** `python3 scripts/sync.py --validate; python3 scripts/consistency-check.py; TMPDIR=<scratch> bash tests/scenarios/run.sh; python3 -m pytest tests/ -q --ignore=tests/browser`
**Provider-Agnostik:** verification commands are provider-generic.
**Depends on:** 17
- [ ] Step 1: run `--validate` + `consistency-check.py`
- [ ] Step 2: run the full scenario catalog
- [ ] Step 3: run pytest without `tests/browser`
- [ ] Step 4: record results in the ledger

### Task 19: Requirement-trace review (stage `review-req`)
**Agent:** validator
**Files:** none (review only)
**Interfaces:** Produces the AC-to-task traceability verdict; Consumes Tasks 1–18.
**Acceptance:** every AC-1…AC-25 maps to at least one verified task; no AC is claimed without a green verification command; harness-dependent ACs are labelled.
**Verify:** `python3 -m pytest tests/ -q --ignore=tests/browser` plus the traceability table in this plan.
**Provider-Agnostik:** review only.
**Depends on:** 18
- [ ] Step 1: check AC coverage
- [ ] Step 2: confirm harness-dependent/STATIC labels
- [ ] Step 3: record verdict

### Task 20: Quality review (stage `review-quality`)
**Agent:** code-reviewer
**Files:** none (review only)
**Interfaces:** Produces the code-quality/blast-radius verdict; Consumes Tasks 1–19.
**Acceptance:** no provider-name branch, no provider-coupled writer path, new modules Stdlib-only, blast radius limited to the affected providers.
**Verify:** `python3 -m pytest tests/test_provider_agnostic_dispatch.py tests/test_mcp_config.py tests/test_artifact_contracts.py -q`
**Provider-Agnostik:** review only.
**Depends on:** 19
- [ ] Step 1: review blast radius
- [ ] Step 2: confirm fail-loud ergonomics
- [ ] Step 3: record verdict

## Step-to-Agent Map

This table is the `parse_plan_ref` input (numeric step, agent in column 3) and the ledger's progress view.

| # | Step | Agent | Depends on | Acceptance criteria |
|---|---|---|---|---|
| 1 | Artifact validator core | `senior-developer` | none | AC-13 |
| 2 | Consistency checks + registration | `developer` | 1 | AC-17, AC-2 |
| 3 | Sync-time validation wiring + exit codes | `senior-developer` | 1 | AC-13, AC-3a |
| 4 | Provider registry contract data | `senior-developer` | none | AC-15, AC-21, AC-25, AC-8, AC-9 (Amendment: `agent-discovery: false`, PRE-2…PRE-6, OQ-3, OQ-6 values) |
| 5 | Capability flags | `developer` | 4 | AC-15, AC-24, AC-25 |
| 6 | Transform format contracts | `senior-developer` | 1, 4 | AC-6, AC-13, D3/AC-12 |
| 7 | Model precedence + single format | `developer` | 4 | AC-12, AC-2 |
| 8 | MCP writer format dispatch | `senior-developer` | 4 | AC-21, AC-23, AC-7, AC-9 |
| 9 | Pipeline notation from config + registry | `developer` | 4 | AC-11 (Amendment: OQ-9 `CONTINUE.config-template.yaml` roles enum) |
| 10 | Bootstrap sub-markers + migration | `senior-developer` | 4 | AC-10, AC-16 (Amendment: OQ-2 Continue dead `agents:` block) |
| 11 | Path migration + idempotency | `senior-developer` | 4 | AC-22, AC-3a, AC-4, AC-18 |
| 12 | Template body references (D5) | `junior-developer` | none | ADR-6 |
| 13 | Provider-agnostic sweep guard | `developer` | 1, 2, 3, 6, 7, 8, 9, 10, 11 | AC-14, AC-23 |
| 14 | Scenarios 64–72 + asserts + registry | `tester` | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | AC-19 |
| 15 | Release + MAJOR version bump | `release` | 14 | MAJOR bump recorded in `VERSION`, `.meta-config/project.yaml`, `CHANGELOG.md`; version markers updated and `git diff --stat` shows only the four version files; no `sync.py` run |
| 16 | Repo regeneration (27-file drift) | `developer` | 15 | AC-3b; `sync.py --check` rc 0 with the new embedded `{{AGENT_META_VERSION}}` |
| 17 | Commit regenerated artifacts | `git` | 16 | AC-3b |
| 18 | Full verification gate | `validator` | 17 | AC-17, AC-18, AC-19, AC-20 |
| 19 | Requirement-trace review | `validator` | 18 | AC-1…AC-25 coverage |
| 20 | Quality review | `code-reviewer` | 19 | AC-14, AC-23 |

## Parallel Groups (ownership-disjoint only)

Each group is one `FanoutPlan(kind="parallel_group", max_parallel=2)`. Only groups with pairwise disjoint `Files:` sets are parallelized; everything else is serialized by the dependencies above. Because ownership is globally disjoint (Global Constraints), every group is conflict-free by construction.

| Group | Tasks | Files (disjoint proof) | Result |
|---|---|---|---|
| PG-1 | 1, 4 | `scripts/lib/artifact_validate.py` + `tests/test_artifact_contracts.py` vs. `config/ai-providers.yaml` + `tests/test_provider_hooks_config.py` + `tests/test_provider_config_contracts.py` | disjoint |
| PG-2 | 5, 7 | `config/provider-capabilities.yaml` + `tests/test_provider_three_file_invariant.py` vs. `scripts/lib/roles.py` + `tests/test_model_contracts.py` | disjoint |
| PG-3 | 6, 8 | `scripts/lib/provider_transform.py` + `tests/test_transform_contracts.py` vs. `scripts/lib/mcp_provider_config.py` + `tests/test_mcp_config.py` | disjoint |
| PG-4 | 9, 10 | `config/delegation-syntax.yaml` + `scripts/lib/pipelines.py` + `templates/configs/CONTINUE.config-template.yaml` + `tests/test_pipeline_notation_config.py` vs. `scripts/lib/bootstrap.py` + `scripts/lib/context.py` + `config/provider-bootstrap.yaml` + `tests/test_bootstrap_submarkers.py` | disjoint |
| PG-5 | 3, 12 | `scripts/lib/agent_sync.py` + `scripts/sync.py` + `tests/test_sync_validation_gate.py` vs. `agents/1-generic/agent-meta-manager.md` + `agents/1-generic/agent-meta-scout.md` + `agents/1-generic/release.md` | disjoint |
| PG-6 | 2, 11 | `scripts/lib/consistency/artifact_contracts.py` + `scripts/lib/consistency/model_contracts.py` + `scripts/consistency-check.py` + `tests/test_consistency_checks.py` vs. `scripts/lib/sync_pipeline.py` + `scripts/lib/generated_file_drift.py` + `scripts/lib/context_templates/builder.py` + `config/provider-migrations.yaml` + `tests/test_migration_paths.py` + `tests/test_context_agents_md_idempotency.py` | disjoint |
| PG-7 (stage `validate`) | 18 validator parallel with tester | verification only; no writes | disjoint |

**Task 15 (release) is serial, not a parallel group:** it depends on the last behavior/scenario task (`15 -> 14`) and must run **before** regeneration so the version is final when Task 16 re-embeds it; its `Files:` set (`VERSION`, `CHANGELOG.md`, `.meta-config/project.yaml`, `README.md`) is disjoint from every other task, but it is intentionally not parallelized. Task 15 is a non-stage-target (it owns no `pipeline_stages` slot) yet it is a hard dependency of Task 16 (`16 -> 15`), so it cannot be skipped.

## Graph Validation (F6)

The task graph is built from the `### Task` blocks (the repo-native parser `scripts/lib/consistency/spec_plan.py::_parse_plan_tasks`) and validated with `scripts/lib/orchestration.py::{FanoutPlan, validate_plan, check_plan_file_overlap}` (backed by `file_affinity.py::check_file_overlap`). `execute_plan` (G-08 dispatcher backend) is explicitly **out of scope** for this plan.

Replay recipe:

```bash
cd /home/hermes/repos/agent-meta
python3 - <<'PY'
from pathlib import Path
from scripts.lib.consistency.spec_plan import _parse_plan_tasks
from scripts.lib.orchestration import FanoutPlan, validate_plan, check_plan_file_overlap

plan_text = Path("docs/plans/2026-09-30-provider-audit-opencode-v2-plan.md").read_text(encoding="utf-8")
tasks = _parse_plan_tasks(plan_text)

# 1. whole-graph check exactly as the repo's spec/plan validator runs it:
graph = FanoutPlan(kind="sequential", tasks=tuple(tasks), max_parallel=len(tasks))
errors = validate_plan(graph, file_overlap=check_plan_file_overlap(graph, Path(".")))
print("whole-graph:", errors or "OK")

# 2. one FanoutPlan per parallel group (task ids per the Parallel Groups table):
for group in (("task-1", "task-4"), ("task-5", "task-7"), ("task-6", "task-8"),
              ("task-9", "task-10"), ("task-3", "task-12"), ("task-2", "task-11")):
    members = tuple(t for t in tasks if t.task_id in group)
    fanout = FanoutPlan(kind="parallel_group", tasks=members, barrier=True, max_parallel=2)
    errs = validate_plan(fanout, max_parallel=2, file_overlap=check_plan_file_overlap(fanout, Path(".")))
    print(" + ".join(group), errs or "OK")
PY
```

**Documented result (static/analytical validation performed during this read-only planning step — no runner is available in the planning phase):**
- Dependency graph (all 20 tasks): no empty plan, no duplicate `task_id`, no dangling dependency, no cycle. Every dependency edge points to a lower task number, so the graph is a strict DAG in numbering order and the Kahn peel completes with `find_dependency_errors` returning `[]`.
- Whole-graph file overlap: every task's `Files:` set is globally disjoint (Global Constraints; verified task-by-task below), so `check_plan_file_overlap` returns `{"safe": [all 20 ids], "conflict": []}` and `validate_plan` returns `[]`.
- Per-group validation: PG-1…PG-7 each have `len(tasks)=2 <= max_parallel=2` and disjoint `files_touched`; `validate_plan` returns `[]` for every group.
- `_check_plan_graph` in `spec_plan.py` uses `max_parallel=len(tasks)`, so no over-commitment is reported for the sequential whole-graph plan.
- **Amendment 2026-10-01 re-check (earlier pass):** the only ownership change is Task 9 gaining `templates/configs/CONTINUE.config-template.yaml` (OQ-9). That path appears in no other task's `Files:` block (Tasks 1–8, 10–20), so `check_plan_file_overlap` still returns `{"safe": [all 20 ids], "conflict": []}` and PG-1…PG-6 remain pairwise disjoint (PG-4 proof updated). Graph topology is unchanged: no task added, no dependency edge added, no cycle — the numbering-order DAG (every edge points to a lower task number) still holds and the Kahn peel completes. (Superseded by the release-task bullet below, which carries the 20-task re-ordered result.)
- **Release-task inserted as Task 15 (2026-10-01, re-ordered) — monotonic, disjoint:** the release/MAJOR-version-bump task now sits as **Task 15** (agent `release`, `Depends on: 14`), *before* regeneration, so the version is final when Task 16 regenerates. The five tail tasks are renumbered (regeneration 15→16, commit 16→17, validate 17→18, review-req 18→19, review-quality 19→20); Tasks 1–14 keep their numbers. Task 15 owns only `VERSION`, `CHANGELOG.md`, `.meta-config/project.yaml` and `README.md` — none of these paths appears in any other task's `Files:` block (Tasks 1–14 and 16–20), so its `Files:` set is disjoint from every other task. Every dependency edge points to a lower task number (`15 -> 14`, `16 -> 15`, `17 -> 16`, `18 -> 17`, `19 -> 18`, `20 -> 19`), so the graph is a strict DAG in numbering order, the Kahn peel completes, and `check_plan_file_overlap` returns `{"safe": [all 20 ids], "conflict": []}`. **Regeneration (Task 16) remains the sole writer of the generated artifacts**, which is why the version bump is ordered before it rather than re-embedding the version in a separate release step.
- **Findings-traceability re-check (2026-10-01, planning-only):** the complete finding inventory was mapped onto the existing tasks (see `## Findings Traceability (vollständig)`). At that pass, **no new task was required for any finding**; the only production-facing changes are two ownership-preserving amendments inside already-owned files — Task 4 (`config/ai-providers.yaml`, adds the G-2 Antigravity `tool-name-map` data) and Task 8 (`scripts/lib/mcp_provider_config.py`, adds the AC-7 `.continue/config.local.yaml` `name`/`version` + the CX-1 `http_headers` spelling). Both files remain single-owner, so `check_plan_file_overlap` still returns `{"safe": [all 20 finding-owning ids], "conflict": []}`, every dependency edge still points to a lower task number, and the Kahn peel still completes. All findings that are not mapped to a task are recorded there as **Deferred** or **Accepted** with rationale; forcing them into new tasks would either duplicate an existing file owner (forbidden by the global-disjointness constraint) or exceed the APPROVED spec scope. (Task 15 is *not* a finding closure and does not contradict this.)
- **Release-task re-check (2026-10-01):** Task 15 (release + MAJOR version bump) is a release/version-bookkeeping task, not a finding closure, and it does **not** run `sync.py` or re-embed the version — regeneration (Task 16) remains the sole writer of the generated artifacts. Task 15 adds **no file overlap** with any other task (`VERSION`, `CHANGELOG.md`, `.meta-config/project.yaml`, `README.md` are owned by no other task), so `check_plan_file_overlap` = `{"safe": [all 20 ids], "conflict": []}`; its dependency edge `15 -> 14` is monotonic (14 < 15), and the edge `16 -> 15` makes Task 15 a hard (non-skippable) prerequisite of regeneration despite owning no `pipeline_stages` slot.
- **Task-4 test-file amendment re-check (2026-10-01, later pass):** Task 4 now also modifies `tests/test_provider_hooks_config.py` (its `_INTENTIONAL_AGENTS_MD_SHARERS` constant at line 142 breaks under the Mammouth `context_file: AGENTS.md` change), alongside `config/ai-providers.yaml` and `tests/test_provider_config_contracts.py`. That path appears in **no other task's `Files:` block** (Tasks 1–3 and 5–20), so every task's `Files:` set stays globally disjoint, `check_plan_file_overlap` still returns `{"safe": [all 20 ids], "conflict": []}`, PG-1 (updated above) remains pairwise disjoint, and the graph is unchanged (no task added, no dependency edge added, no cycle; the numbering-order DAG still holds). The Task-4 discovery-sub-map shape is data in `config/ai-providers.yaml` and adds no file.
- **Task-11 migration-map amendment re-check (2026-10-01, review F1/F2/F3 pass):** Task 11 now also creates `config/provider-migrations.yaml` — the data-driven old→new path migration map (Copilot default-on, Gemini gated by `agent-discovery`), which closes AC-22 / design §6.2.1 / spec §11.1 without touching Task-4's `config/ai-providers.yaml`. The path is brand-new and appears in **no other task's `Files:` block** (Tasks 1–10 and 12–20), so every task's `Files:` set stays globally disjoint, `check_plan_file_overlap` still returns `{"safe": [all 20 ids], "conflict": []}`, PG-6 remains pairwise disjoint (proof updated above), and the graph is unchanged (no task added, no dependency edge added, no cycle; the numbering-order DAG still holds and the Kahn peel completes). Task 4 stays the exclusive owner of `config/ai-providers.yaml`; the migration map is a separate single-owner file.
- **Fail-closed caveat:** `check_file_overlap` also widens each task's file set from prompt-referenced paths and AST symbol-to-file resolution. Task titles in this plan are path-free, so the declared `files_touched` sets are the effective input. If a future edit adds a symbol/path to a title and replay surfaces a conflict, the affected tasks MUST be sequentialized before dispatch — never dispatched on a skipped check.
- Outcome: **PASS** (cycles: none, overlaps: none, over-commitment: none).

## Barriers, Ledger, Checkpoints, Recovery

- **Barrier semantics:** one barrier per task and per parallel group. A group dispatches both tasks, collects one `BarrierEntry` per task, and starts dependents only after both entries are `success`.
- **Ceiling:** `max-parallel-agents: 2` is the hard upper bound; no barrier group exceeds it.
- **Ledger = this file:** checkboxes `- [ ]` / `- [x]` are the human progress view; after every task the ledger writer `scripts/lib/plan_ledger.py --update-plan-ledger` writes the checkbox state exactly per `parse_plan_ledger` semantics (manual editing is the fallback only).
- **Checkpoints:** each entry is persisted via `scripts/lib/checkpoint.py::CheckpointStore`; `BarrierEntry.checkpoint_ref` points at the raw output under the configured checkpoint root (`progress.checkpoint-dir`; default `.meta-viz/checkpoints`). Identity comes only from the explicit `plan_id` (`checkpoint_from_barrier_entry`).
- **Recovery:** on abort, resume from the `CheckpointStore` state; the plan file's checkboxes are the readable mirror. No new ledger format is introduced.
- **Archive:** `archive.trigger: plan-complete` — archive only when all checkboxes are set AND the branch is merged (manual confirmation; target `docs/plans/archive/`).

## Verification (per task; harness-dependent ACs labelled)

| Task | Scenarios | Pytest module | Real-runtime / static |
|---|---|---|---|
| 1, 2, 3 | 64 (TOML), 69 (v2) | `tests/test_artifact_contracts.py`, `tests/test_consistency_checks.py`, `tests/test_sync_validation_gate.py` | Opencode v2 `opencode debug config` (VERIFIED parse/debug; session turn UNVERIFIABLE) |
| 4 | 65, 66, 67, 68, 69 | `tests/test_provider_config_contracts.py` | Copilot/Antigravity paths STATIC only |
| 5 | — | `tests/test_provider_three_file_invariant.py` | — |
| 6 | 66, 69 | `tests/test_transform_contracts.py` | `mammouth agent list` harness-dependent |
| 7 | 65 | `tests/test_model_contracts.py` | `kimi acp` -> `set_config_option` harness-dependent |
| 8 | 69, 72 | `tests/test_mcp_config.py` | `opencode debug config` shows `mcp.servers`; `@continuedev/config-yaml` Zod parse |
| 9 | 64, 71 | `tests/test_pipeline_notation_config.py` | — |
| 10 | 70 | `tests/test_bootstrap_submarkers.py` | — |
| 11 | 67, 68, 71, 72 | `tests/test_migration_paths.py`, `tests/test_context_agents_md_idempotency.py` | — |
| 12 | 64, 65 | grep in scratch `.codex`/`.zcode`/`.kimi-code` | — |
| 13 | — | `tests/test_provider_agnostic_dispatch.py` | — |
| 14 | 64–72 all | — | — |
| 15 | — | — | release bump only: version markers updated; `git diff --stat` shows only the four version files |
| 16, 17 | — | — | repo-root `sync.py --check` rc 0 with the new `{{AGENT_META_VERSION}}` re-embedded |
| 18, 19, 20 | full catalog | `python3 -m pytest tests/ -q --ignore=tests/browser` | `--validate` + `consistency-check.py` rc 0 |

**Harness-dependent (not CI obligations):** AC-1 `codex mcp list` (creds absent), AC-2 `kimi acp`, AC-5 `opencode debug agents`, AC-6 `mammouth agent list` — each has a CI-mandatory static equivalent (tomllib / grep / scenario assert).
**Unverifiable here (STATIC / HYPOTHESIS, out of scope):** Antigravity `agy` (SIGILL, F6) -> AC-9 ships against the in-binary STATIC contract; Copilot context injection (no authenticated runtime, F9) -> AC-8 static-path only; ZCode workspace auto-load (open P6) stays STATIC. Opencode v2 is VERIFIED at parse/debug level only; a session turn was not run (F4, I-12).
**Environment-blocked:** `tests/browser` (35 socket errors per regression report §5) is excluded from AC-20.

## Risks and Rollback

References: Spec §11.1 (path-migration table) and Design §6.2.1 (5-step sequence: write new -> verify -> backup old -> remove old -> rollback by renaming the `.sync-backup-<ts>` sibling). ADR-9: the MAJOR bump is driven by the **Copilot default-on** path migration (breaking) and ships only together with the migration table; **Antigravity is flag-gated MINOR** (nothing moves by default — its migration risk exists only when `agent-discovery: true`) and Opencode v2 is opt-in MINOR, both dominated by the Copilot MAJOR; user files are never deleted.

| Risk | Impact | Mitigation |
|---|---|---|
| v2 silent drop after a config edit | agent disappears without a signal | `allowed-fields` + `--check`/`--validate` rc != 0 (Tasks 1–3, 8) |
| Path migration deletes a user file | data loss | managed-marker-scoped writes + `.sync-backup-<ts>` + user-file guard (Task 11, AC-22) |
| `model-format` applied twice | double prefix (`kimi-code/kimi-code/*`) | applied once at emission; `model_contracts` catches it (Tasks 7, 2) |
| Bootstrap marker migration breaks an existing `AGENTS.md` | lost context | scoped replace + user-note preservation (Task 10, AC-16) |
| v1 schema used to validate v2 artifacts | false invalidity | internal `artifact_validate` only, no official v2 schema (Task 1) |
| Config-key name collision | silent override | keys added to the three-file invariant (Task 5) |
| Major bump (Copilot default-on) breaks SemVer-reactive consumers | stranded old paths | ordered migration + rollback (Task 11, §11.1); Antigravity is flag-gated MINOR, so its risk exists only when `agent-discovery: true` |
| Declarative `skills: true` diverges from generator reality | provider claims skills without artifacts | coupling rule + invariant (Task 5, AC-25) |
| 27-file drift committed unseen | unexplained deltas in branch | per-file inspection in Task 16; escalate unexplained deltas |

**Rollback principle:** never a silent move; every managed delete is preceded by a byte-exact backup sibling; restoring = rename `<file>.sync-backup-<ts>` back. Opencode v2 is opt-in (`surface-version` defaults to `v1`), so v1 projects are untouched and roll back by construction.

## Blockers and Critical Path

- **Approval gate (PRE-1…PRE-7): RESOLVED (2026-10-01).** All five decisions (OQ-1/4/5/7/8) and the §9 scope decision are resolved (see the Amendment); the spec reads `Status: APPROVED (2026-10-01)` and the plan is ACTIVE. No task remains gated on PRE-1…PRE-7.
- **27-file repo drift (spec §9) is the branch-hygiene blocker:** it is an explicit precondition (PRE-7) and an explicit task pair (Task 16 regenerate + Task 17 commit). On the in-scope decision, AC-3b (`--check` rc 0 at the repo root) is satisfied by Tasks 16/17; on the rejected scope-split, Tasks 16/17 move to the follow-up PR and only AC-3b moves with them — AC-3a (scratch-consumer `--check` rc 0, Task 11) remains mandatory in this change.
- **Critical path:** Task 1 -> Task 3 -> Task 6 -> Task 13 -> Task 14 -> Task 15 (release bump) -> Task 16 -> Task 17 -> Task 18 -> Task 19 -> Task 20 (11 nodes; Task 20 is the terminal quality-review node, Task 15 the release/version-bump node). The parallel branches (Task 4 -> Task 7 -> Task 2, Task 4 -> Task 8/9/10/11, Task 12) are shorter and join at Task 13/14.
- **Follow-ups (non-goals, not blockers):** the 85 consistency warnings and the `1.2.0-beta.2` semver-regex warning (spec §1.3/§9). The Continue template CO-2 (`templates/configs/CONTINUE.config-template.yaml:28`, Design OQ-9 / spec §1.3) is **in scope** as of the Amendment 2026-10-01 and owned by Task 9 — no longer a follow-up.
- **N7 (Opencode v2 requires a VCS root) — Accepted in spec §13.3, no plan task.** Finding N7 is recorded as `Accepted` in the spec's §13.3 decision register: the syncer cannot create a VCS root, and no approved AC requires it. Consequently the plan carries **no task** for N7 (its Findings-Traceability row reads `Accepted — spec §13.3`), preserving plan/spec consistency — the spec's acceptance and this plan's task graph agree that N7 is a documented non-action, not an open implementation item.

## Self-Review

- **Task-to-role:** every step maps to exactly one role; the `implement` stage maps to step 1 (`senior-developer`, an allowed tier); the review/validate stages map to steps 18–20; Task 15 maps to the `release` role.
- **Task-to-test:** every task has a test (pytest module or scenario assert) and an observable acceptance criterion; no criterion is "works correctly". Task 15's observable criteria are the updated version markers (`grep`/read) and `git diff --stat` showing only the four version files.
- **Ownership:** `Files:`/`Interfaces:` are complete and globally disjoint; no file is written by two tasks; shared-file edits are consolidated into one owning task. Task 15 owns `VERSION`/`CHANGELOG.md`/`.meta-config/project.yaml`/`README.md`, which no other task touches (disjointness proven in Graph Validation).
- **Traceability:** each AC-1…AC-25 is covered by at least one task (see the table below); harness-dependent ACs are labelled (AC-1/2/5/6) and STATIC areas (AC-8/9) are documented.
- **`pipeline_stages`:** maps the plan-driven stage `implement` and the review/validate stages of `concept-driven-dev`. Task 15 (release) is a non-stage-target (no `pipeline_stages` slot) but is a hard dependency of Task 16, so it cannot be skipped.
- **No placeholders:** no unresolved placeholder markers; every task names exact paths, symbols, commit messages and a verification command.
- **No worktree isolation:** explicitly forbidden; Ownership + Barriers + Checkpoint-ledger are the substitutes.

### AC-to-Task Traceability

| AC | Task(s) | AC | Task(s) |
|---|---|---|---|
| AC-1 | 4, 8, 14 | AC-14 | 13 |
| AC-2 | 4, 7, 2, 14 | AC-15 | 4, 5 |
| AC-3a | 3, 11 | AC-16 | 10 |
| AC-3b | 16, 17 | AC-17 | 2, 18 |
| AC-4 | 11, 14 | AC-18 | 11, 18 |
| AC-5 | 4, 8, 14 | AC-19 | 14, 18 |
| AC-6 | 6, 14 | AC-20 | 18 |
| AC-7 | 8, 14 | AC-21 | 4, 8 |
| AC-8 | 4, 11, 14 | AC-22 | 4, 11, 14 |
| AC-9 | 4, 8, 11, 14 | AC-23 | 8, 13 |
| AC-10 | 10, 14 | AC-24 | 5 |
| AC-11 | 9 | AC-25 | 4, 5 |
| AC-12 | 6, 7 | ADR-6 (D5) | 12 |
| AC-13 | 1, 3, 6 | | |

**Release note:** Task 15 (release + MAJOR version bump) is release bookkeeping and is not bound to an AC-1…AC-25; it is verified by the updated version markers (`grep`/read) and `git diff --stat` showing only the four version files (see the Verification table). Regeneration of the version-bearing artifacts is Task 16, verified by `sync.py --check` rc 0.

## Findings Traceability (vollständig)

> Added 2026-10-01 by `planner` (planning-only; no production code, no generated artifact, no commit). Source of truth: `docs/analysis/2026-09-30-provider-audit-generation.md` (D1–D10), `…-docs-part1.md` (CL-1/2/3, G-1…G-9, OC1-1…4, OC2-1…5, P-1…P-6), `…-docs-part2.md` (CX-1/2, ZC-1/2/3, KC-1/2, CO-1/2, MM-1…5, MM-a/MM-b), `…-runtime-consolidation.md` (H1–H10, A1–A11, N1–N20), and the eight `docs/analysis/evidence/2026-09-30-*.md` files. Every finding ID the sources actually define appears exactly once. Ledger checkboxes are untouched.
>
> **Inventory: 95 findings — 55 `Task`, 11 `Deferred`, 29 `Accepted`.** Three rows carry a split (D10, CX-2, MM-a): the primary status is `Task`, the residual (unowned fallback constant / artefact-less emission) is named in the Begründung and counted under `Deferred` semantics there.
>
> **No new finding-closure task is required.** Every finding that the APPROVED spec puts in scope is already owned by Task 1–20; the two genuine implementation gaps found (AC-7 `.continue/config.local.yaml` validity, G-2 Antigravity tool-name-map data) live inside files that already have a single owner and are therefore ownership-preserving amendments to Task 4 / Task 8 — inventing further finding tasks would violate the global-disjoint `Files:` rule. Findings outside the approved spec scope (or refuted at runtime) are recorded as `Deferred` / `Accepted` with rationale instead of being forced into tasks. (Task 15 is a deliberate release/version-bump task inserted by a later 2026-10-01 pass, not a finding closure.)

### Deliberately out / Accepted register (prompt constraint)

| Finding | Verdict | Begründung | Follow-up |
|---|---|---|---|
| D9 | Accepted (by design) | `io.py` suppresses dry-run writes when the target root is gitignored (`is_absent_gitignored_target`); the real sync is unaffected. Documented behaviour, not a defect. | Documentation note only. |
| H1 (→ OC1-2) | Accepted (refuted) | The Opencode dispatch `Bad Request` is provider-side (`opencode-go`); an `edit: deny` agent (`code-reviewer`) fails identically. No `edit`/schema defect; deliberately out. | None. |
| F6 (Antigravity `agy`) | Accepted (out of scope) | `agy` SIGILLs on the audit CPU (no `pclmul`); runtime acceptance is unverifiable. The discovery change ships against the in-binary STATIC contract. | Re-run on a `pclmul`-capable host. |

### Full table

| Finding-ID | Quelle | Severity | Status | Ort (Datei/AC/Scenario) | Begründung |
|---|---|---|---|---|---|
| D1 | generation §2 (F1/N1/N2) | MAJOR | Task 3 | Task 3 + Task 1 + Task 14 s64; AC-1/AC-13 | singleton block moved inside the body before `codex-toml` serialization; `validate_toml` guards both files. |
| D2 | generation §2 (F11) | MAJOR/MOD | Task 7 | `roles.py`; AC-12 | `ai-providers.yaml model-tiers` wins over preset `tiers`. |
| D3 | generation §2 (F11) | MAJOR | Task 6 / Task 7 | Task 6 (provider_transform.py) / Task 7 (roles.py); AC-12 | `model-inherit-fallback` resolves through the tier resolver, never a raw tier token. |
| D4 | generation §2 | MINOR | Accepted | — | Continue strips unknown keys, Mammouth collects them in `options`; tolerated by both runtimes, not in spec §1.1/§2.1. Follow-up: set `inject-memory`/`inject-permission-mode` false if a harness ever rejects. |
| D5 | generation §2 (F11) | MINOR | Task 12 | 3 templates; ADR-6 | 5 provider-neutral body refs replace `.claude/...`. |
| D6 | generation §2 (F11) | MODERATE | Task 9 | `pipelines.py`, `delegation-syntax.yaml`; AC-11 | notation read from config; missing block fail-loud (no Opencode fallback). |
| D7 | generation §2 (F11) | MODERATE | Task 9 | `pipelines.py`; AC-11 | `KNOWN_PROVIDERS` → `registered_provider_names` (Copilot present). |
| D8 | generation §2 (F10 §6/N15) | MODERATE | Task 10 | `bootstrap.py`/`context.py`; AC-10/AC-16 | registry-keyed scoped sub-markers; no forced Gemini-only cleanup. |
| D9 | generation §2 | MINOR | Accepted (by design) | — | deliberately out — see register above. |
| D10 | generation §2 | MINOR | Task 13 (residual Accepted) | `context.py:753`→T10, `pipelines.py:20/757`→T9, sweep→T13; AC-14 | no new name branch; residual fallback path constants are config-dispatched or Claude-gated and non-load-breaking. |
| CL-1 | docs-part1 §1.4 | LOW | Accepted | — | unknown Claude frontmatter ignored without error; no effect. |
| CL-2 | docs-part1 §1.4 (F5) | MED | Deferred | — | cwd-dependent relative hook command; F5 is excluded from design §1.1 objective and absent from the spec. Follow-up: `${CLAUDE_PROJECT_DIR}` (repair proven). |
| CL-3 | docs-part1 §1.4 | LOW | Accepted | — | `orchestrator` `tools`/`permissionMode` inconsistency; no load impact, separate cleanup. |
| G-1 | docs-part1 §2.4 (F6) | HIGH | Task 4 | Task 4 + Task 11 + Task 14 s68; AC-9 | `agents_dir: .agents/agents` + backup-first migration. |
| G-2 | docs-part1 §2.4 (F6) | HIGH | Task 4/6 | Task 4 (`tool-name-map`) + Task 6; docs-part1 §2.1 | Antigravity tool vocabulary supplied as data (amendment to Task 4). |
| G-3 | docs-part1 §2.4 (F6) | HIGH | Task 4/6 | Task 4 (`model-literal: inherit`) + Task 14 s68; AC-9 | OQ-6: `model: inherit` verbatim, no tier IDs. |
| G-4 | docs-part1 §2.4 | LOW | Accepted | — | defaults (`mainAgent`/`subagent` true, sandbox policy) make it non-breaking; not spec-scoped. |
| G-5 | docs-part1 §2.4 | MED | Deferred | — | `.gemini/commands/*.toml` is not an Antigravity contract; commands-surface redesign not in spec §2.5. |
| G-6 | docs-part1 §2.4 (F6) | MED | Task 4 | Task 4 + Task 14 s68; AC-9 | `skills_dir: .agents/skills`. |
| G-7 | docs-part1 §2.4 (F6) | HIGH | Task 4/8 | Task 4 (`antigravity-mcp-json`) + Task 8 (`serverUrl`) + s68; AC-9 | workspace MCP at `.agents/mcp_config.json`, remote `serverUrl`. |
| G-8 | docs-part1 §2.4 (H2) | MED | Accepted (refuted) | — | command resolves relative to the `hooks.json` directory. |
| G-9 | docs-part1 §2.4 (H3) | HYP | Accepted (verified) | — | `matcher:"*"` is documented. |
| OC1-1 | docs-part1 §3.3 | MED | Task 4/6 | Task 4 (`primary-role`) + Task 6 (`opencode-native-v2`) + s69; AC-5 | `orchestrator` as `mode: primary`, valid `default_agent`. |
| OC1-2 | docs-part1 §3.3 (H1) | HIGH | Accepted (refuted) | — | provider-side Bad Request — see register. |
| OC1-3 | docs-part1 §3.3 (H4) | LOW | Task 4/6 | Task 4 (`allowed-fields`) + Task 6; AC-13 | Opencode pass-through bucket becomes a sync-time finding. |
| OC1-4 | docs-part1 §3.3 | LOW | Accepted | — | `opencode.json` + `opencode.jsonc` merge (N20); repo hygiene only. |
| OC2-1 | docs-part1 §4.2 | HIGH | Task 6 | Task 6 (`opencode-native-v2`) + Task 4; AC-5 | native `permissions` list replaces the legacy `permission` map. |
| OC2-2 | docs-part1 §4.2 | HIGH | Task 4/8 | Task 4 (`opencode-json-v2`) + Task 8; AC-21 | nested `mcp.servers`, no flat `mcp`. |
| OC2-3 | docs-part1 §4.2 | MED | Task 4/8/1 | Task 1 (`validate_json_document`) + Task 8; AC-21 | `subagent_depth` no longer emitted for v2; v1-only keys rejected. |
| OC2-4 | docs-part1 §4.2 | LOW | Accepted | — | Markdown agents remain valid in v2 (runtime-ok); JSON `agents` not required. |
| OC2-5 | docs-part1 §4.2 | LOW | Task 4/6 | Task 4 (`allowed-fields`) + Task 6 | unknown keys (`version`/`prompt_mode`/`generated-from`) become findings. |
| P-1 | docs-part1 §5.2 | HIGH | Task 4/11/14 | Task 4 + Task 11 + s67; AC-8/AC-22 | `.github/agents/` + migration. |
| P-2 | docs-part1 §5.2 | MED | Task 4/14 | Task 4 (`agent_ext`) + s67; AC-8 | `.agent.md`. |
| P-3 | docs-part1 §5.2 | HIGH | Task 4/11/14 | Task 4 (`context_file`) + Task 11 + s67; AC-8/AC-22 | `.github/copilot-instructions.md` + migration. |
| P-4 | docs-part1 §5.2 | MED | Task 4/11/14 | Task 4 (`rules_dir`) + Task 11 + s67; AC-8/AC-22 | `.github/instructions/`. |
| P-5 | docs-part1 §5.2 | MED | Task 4/5/14 | Task 4 (`skills_dir`) + Task 5 + s67; AC-8/AC-25 | `.github/skills/`; capability coupling. |
| P-6 | docs-part1 §5.2 | MED | Deferred | — | Copilot commands/subagent under-claim; not load-affecting, no spec §2.2 contract. |
| CX-1 | docs-part2 §1.4 | MED | Task 4/8 | Task 4 (`codex-toml-mcp`) + Task 8 (`http_headers`); AC-7 neighbourhood | documented Codex header spelling; amendment names it explicitly in Task 8. |
| CX-2 | docs-part2 §6 | flag | Task 5 (emission Deferred) | Task 5; AC-15 | declaration surfaced (`skills` explicit + reason gate); Codex `.agents/skills` artefact-less emission is a Deferred follow-up. |
| ZC-1 | docs-part2 §2.4 | MED | Deferred | — | ZCode workspace auto-load is an open P6 test and an explicit spec non-goal; bootstrap workaround retained. |
| ZC-2 | docs-part2 §2.3 | flag | Deferred | — | commands under-claim; not load-affecting, not in spec §2.2. |
| ZC-3 | docs-part2 §2.3 | flag | Task 4/5 | Task 4 + Task 5; AC-15/AC-25 | ZCode `skills: true` + `capabilities: [skills]` coupling. |
| KC-1 | docs-part2 §3.3 | MED | Task 4/8 | Task 4 (`kimi-json`, `mcp-remote-transport: transport`) + Task 8 | `transport: "sse"`, not `type`. |
| KC-2 | docs-part2 §3.2 | flag | Task 4/5 | Task 4 + Task 5; AC-15/AC-25 | KimiCode `skills: true` + capabilities coupling. |
| CO-1 | docs-part2 §4.1 | MED | Task 10/14 | Task 10 + s72; AC-7 | dead top-level `agents:` block removed (OQ-2). |
| CO-2 | docs-part2 §4.3 / evidence | MED (fatal) | Task 9 | `templates/configs/CONTINUE.config-template.yaml:28`; OQ-9 | `roles` enum no longer emits invalid `agent`. |
| MM-1 | docs-part2 §5.1 | LOW | Accepted | — | `.mammouth/agents` is source-verified discovered; docs/source divergence only. |
| MM-2 | docs-part2 §5.1 (N17) | HIGH | Task 4/6/14 | Task 4 (`tools-format: map`) + Task 6 + s66; AC-6 | `tools:` object, never a list. |
| MM-3 | docs-part2 §5.2 | MED | Deferred | — | `.mammouth/settings.json` is inert; config-file target not in spec §2.1/§11.1. Follow-up: target `mammouth.json`/`opencode.json`. |
| MM-4 | docs-part2 §5.3 (A11) | MED | Task 4/16 | Task 4 (`context_file: AGENTS.md`) + Task 16; OQ-7 | retire `MAMMOUTH.md` + routing entry. |
| MM-5 | docs-part2 §5.1 (H10/A4) | MED | Deferred | — | bare model ID unresolvable (`ProviderModelNotFoundError`); the approved spec §2.1 omits a Mammouth `model-format` and the correct provider prefix is not runtime-established (only the `opencode/big-pickle` control resolves). Contingent Task 4 amendment once `mammouth provider list` confirms the prefix. |
| MM-a | docs-part2 §5.4 | flag | Task 5 (emission Deferred) | Task 5; AC-15 | Mammouth `skills` declaration surfaced; artefact-less `.mammouth/skills/` emission is a Deferred follow-up. |
| MM-b | docs-part2 §5.4 | flag | Deferred | — | Mammouth MCP under-claim; no approved MCP contract for the fork. |
| H1 | runtime §1 | REFUTED | Accepted | — | see register. |
| H2 | runtime §1 | REFUTED `[STATIC]` | Accepted | — | = G-8, resolves. |
| H3 | runtime §1 | VERIFIED `[STATIC]` | Accepted | — | = G-9, conformant. |
| H4 | runtime §1 | VERIFIED | Accepted | — | unknown keys pass through at harness layer; provider layer UNVERIFIABLE. |
| H5 | runtime §1 | REFUTED | Accepted | — | ZCode `type` is the mandatory discriminator; current output is correct. |
| H6 | runtime §1 | VERIFIED | Task 4/7 | Task 4 + Task 7; AC-2/AC-12 | `kimi-code/…` prefix exactly once + catalog. |
| H7 | runtime §1 | VERIFIED `[STATIC]` | Task 10 | Task 10; OQ-2/A6 | `cn review`-only surface; header comment corrected, dead block removed. |
| H8 | runtime §1 | REFUTED | Task 8 | Task 8; AC-7 | `requestOptions.headers`. |
| H9 | runtime §1 | VERIFIED | Deferred | — | Continue `skills` is a real runtime surface but emits 0 artefacts; under-delivery, not an error — no approved contract requires Continue skill artifacts. |
| H10 | runtime §1 | REFUTED | Deferred | — | = MM-5. |
| A1 | runtime §4 | anti-fact | Accepted | — | = H1 (refuted). |
| A2 | runtime §4 | anti-fact | Accepted | — | provider-side error, not a v1 defect. |
| A3 | runtime §4 | anti-fact | Accepted | — | = H5. |
| A4 | runtime §4 | anti-fact | Deferred | — | = MM-5 (bare alias never resolves). |
| A5 | runtime §4 | anti-fact | Task 8 | Task 8; AC-7 | = H8. |
| A6 | runtime §4 | anti-fact | Task 10 | Task 10 | = H7 header comment. |
| A7 | runtime §4 | anti-fact | Accepted | — | = H2/G-8. |
| A8 | runtime §4 | anti-fact | Task 7 | Task 7; AC-12 | D2 is generation-time precedence, not a runtime shadow. |
| A9 | runtime §4 | anti-fact | Accepted | — | `opencode debug v2` is a model catalog, not a validator; internal validator used (Task 1). |
| A10 | runtime §4 | anti-fact | Accepted | — | v2 is a separate package (`@opencode/cli`); acknowledged, v2 opt-in. |
| A11 | runtime §4 | anti-fact | Task 4/16 | Task 4 + Task 16; OQ-7 | = MM-4. |
| N1 | runtime §2 | fact | Task 3 | Task 3; AC-1 | second invalid TOML (`knowledge-curator.toml`) fixed by the singleton reordering. |
| N2 | runtime §2 | fact | Task 1 | Task 1 | `validate_toml` catches the Codex parser class. |
| N3 | runtime §2 | fact | Accepted | — | `@opencode/cli@2.0.20` installable; v2 handled as opt-in surface. |
| N4 | runtime §2 | fact | Task 4/8/1 | Task 1 + Task 8; AC-21 | `subagent_depth` silently dropped → guard. |
| N5 | runtime §2 | fact | Task 4/8 | Task 4 + Task 8; AC-21 | flat `mcp` dropped → nested `mcp.servers`. |
| N6 | runtime §2 | fact | Task 1/3/8 | Task 1 + Task 3; AC-13/AC-21 | v2 silent rejection becomes a fail-loud finding. |
| N7 | runtime §2 | fact | Accepted — spec §13.3 | — | v2 requires a VCS root; syncer cannot create it. Documented as **Accepted (out of generator scope)** in spec §13.3, so no plan task is created (plan/spec consistent). |
| N8 | runtime §2 | fact | Accepted | — | no v2 JSON schema exists; internal validator only (Task 1). |
| N9 | runtime §2 | fact | Accepted | — | `debug v2` is non-deterministic; not used as a validator. |
| N10 | runtime §2 | fact | Task 8/9 | Task 8 + Task 9; AC-7 | Continue `config.yaml`/`config.local.yaml` Zod validity. |
| N11 | runtime §2 | fact | Task 9 | Task 9; CO-2/OQ-9 | default-template `roles` enum. |
| N12 | runtime §2 | fact | Task 10 | Task 10; CO-1/OQ-2 | top-level `agents:` stripped → removed. |
| N13 | runtime §2 | fact | Task 4/11 | Task 4 + Task 11; AC-8/AC-22 | Copilot path deviations on real scratch artifacts. |
| N14 | runtime §2 | fact | Task 10/11 | Task 10 + Task 11; AC-3a/AC-18 | `--check` permanent false-positive fixed by final-content pending-write computation. |
| N15 | runtime §2 | fact | Task 10 | Task 10; AC-10/AC-16 | marker collision + Gemini-only cleanup removed. |
| N16 | runtime §2 | fact | Task 11 | Task 11; AC-4 | entry-file run1→run2 drift (Continue + ZCode) fixed. |
| N17 | runtime §2 | fact | Task 4/6 | Task 4 + Task 6 + s66; AC-6 | Mammouth `tools:` list aborts loading. |
| N18 | runtime §2 | fact | Accepted | — | KimiCode project path real; ZCode npm-installable — context facts, no action. |
| N19 | runtime §2 | fact | Accepted | — | Opencode v1 loads 65/65 deterministically — context fact. |
| N20 | runtime §2 | fact | Accepted | Task 7 (D2) | no runtime shadow; D2 is generation-time precedence (Task 7). |
| F6 | docs-part1 §2.4 / runtime §1 | out-of-scope | Accepted | — | runtime acceptance SIGILL — see register. |

### Notes on the mapping

- **Runtime-verified defects (F1–F3, F7–F11) are all owned.** F4 (Opencode v2) is added as an opt-in surface (Task 4/6/8) with the silent-drop guard (Task 1/3); F5 (Claude hook cwd, CL-2) and F6 (Antigravity runtime acceptance) are explicitly outside the design §1.1 objective and are recorded as `Deferred` / `Accepted`.
- **`Accepted` ≠ ignored:** each row states why no task is warranted (refuted at runtime, tolerated by the harness, or non-load-breaking). The three prompt-mandated deliberate-outs (D9, H1, F6) carry an explicit follow-up reference.
- **`Deferred` register (11):** CL-2, G-5, P-6, ZC-1, ZC-2, MM-3, MM-5, MM-b, H9, H10, A4. None blocks an AC; each is either outside the approved spec scope or a data-maintenance item. N7 is **not** in this register — it is recorded as `Accepted — spec §13.3` (see its row), so the plan and spec agree.
- **Amendments (ownership-preserving, no new edge):** Task 4 gains the G-2 Antigravity `tool-name-map` data; Task 8 gains the AC-7 `config.local.yaml` `name`/`version` and the CX-1 `http_headers` spelling. Both stay inside their existing single-owner files, so the graph, dependencies, parallel groups and the verification table are unchanged — see the Graph Validation (F6) re-check bullet.
- **Task 15 (release) — inserted, monotonic (added 2026-10-01):** the release/MAJOR-version-bump task is inserted as **Task 15** after the last behavior/scenario task (Task 14) and before regeneration, so the version is final when the artifacts are regenerated. It owns only `VERSION`, `CHANGELOG.md`, `.meta-config/project.yaml` and `README.md`, none of which appears in any other task's `Files:` block (disjoint from Tasks 1–14 and 16–20); its edge `15 -> 14` is monotonic and the edge `16 -> 15` makes it a non-skippable prerequisite of regeneration. The five tail tasks are renumbered (old 15→16, 16→17, 17→18, 18→19, 19→20) and `pipeline_stages` is updated to `validate: 18`, `review-req: 19`, `review-quality: 20`. Regeneration (Task 16) remains the sole writer of the generated artifacts (and the only step that re-embeds `{{AGENT_META_VERSION}}`); every dependency edge still points to a lower task number.
