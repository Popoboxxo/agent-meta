---
pipeline_stages:
  implement: 1          # stage `implement` (plan-driven) -> step 1 (agent senior-developer, allowed_agents tier)
  review-req: 18        # stage `review-req` (loop)         -> step 18 (agent validator)
  review-quality: 19    # stage `review-quality` (loop)     -> step 19 (agent code-reviewer)
  validate: 17          # stage `validate` (parallel_group) -> step 17 (agent validator; tester co-runs)
---

# Provider-Audit Gap Closure + Opencode v2 Support — Implementation Plan

> Status: **PROVISIONAL — pending spec approval**
> Trace anchor: `spec-id: SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30`
> Review: `docs/specs/2026-09-30-provider-audit-opencode-v2-review.md` (Iteration 2: APPROVED, only minor restones)
> Design: `docs/specs/2026-09-30-provider-audit-opencode-v2-design.md` (Rev. 2)
> Evidence base: `docs/analysis/2026-09-30-provider-audit-runtime-consolidation.md`; `docs/analysis/evidence/2026-09-30-regression-tests.md`
> Plan-ledger: `plan-ledger` skill; ledger = this file (checkboxes); recovery via `scripts/lib/checkpoint.py::CheckpointStore` + `BarrierEntry.checkpoint_ref`.
> Gate note: while the referenced spec still reads `DRAFT — PENDING APPROVAL`, the repo's own plan check `spec_plan.py::_check_approval_markers` reports an ERROR by design — that is the PRE-1 approval gate, not a plan defect.

**Goal:** Close the runtime-verified provider gaps (Codex TOML, Kimi model namespace, Mammouth `tools` list, Continue config validity, Copilot/Antigravity paths), add Opencode v2 as an opt-in generated surface (`surface-version: v1|v2`), and turn every silent-drop / invalid-artifact class into a sync-time, fail-loud signal (`--validate`/`--check` rc != 0) — all provider differences expressed as config data / capability flags, never as `if provider == "Name"`.
**Architecture:** One generic artifact validator (`artifact_validate.py`) feeds `agent_sync._finalize_agent_content` and two consistency modules (`consistency/artifact_contracts.py`, `consistency/model_contracts.py`). Dispatch is always on a declared config value (`mcp-config.format`, `frontmatter-mechanism`, `pipeline_notation`, `marker_id`); writer/transform code never reads a provider name or `surface-version` (H-1, ADR-10). Path changes migrate write-new -> verify -> backup-old -> remove-old, user files untouched (H-2, ADR-9).
**Tech Stack:** Python 3.9+ (Stdlib only; `from __future__ import annotations` in new modules), pytest, Bash scenario harness (`tests/scenarios/run.sh`), YAML/JSON/TOML/Markdown.

**Spec:** `docs/specs/2026-09-30-provider-audit-opencode-v2.md`

---

## Preconditions (approval gate — MUST be resolved before Task 1)

Every item below is a user/approval decision. No implementation task may start while any item is open. The spec header still reads `DRAFT — PENDING APPROVAL`; the plan is therefore PROVISIONAL.

| ID | Decision (spec ref) | Owner | Effect if changed |
|---|---|---|---|
| PRE-1 | Spec approval: `concept-reviewer` sets `Status: APPROVED (date)` | user / `concept-reviewer` | Blocks all tasks; plan stays PROVISIONAL. |
| PRE-2 | **OQ-1** Antigravity discovery: ship default-on vs. flag-gate (spec §4, AC-9) | user | Task 4 path values + scenario 68 assert. |
| PRE-3 | **OQ-4** Opencode v2 primary entry role (`default_agent`, `primary-role` key) (spec §4, AC-5) | user | Task 4 data key + scenario 69 assert. |
| PRE-4 | **OQ-5** Copilot extension `.md` vs. `.agent.md` (spec §4, AC-8) | user | Task 4 path/naming values + scenario 67 assert. |
| PRE-5 | **OQ-7** Mammouth context file `AGENTS.md` vs. `CONTEXT.md` (spec §4) | user | Task 4 `context_file` value; `MAMMOUTH.md` stays a non-goal. |
| PRE-6 | **OQ-8** v1->v2 default flip timing / SemVer track (spec §4/§11) | user | Task 4 `surface-version` default; SemVer bump class. |
| PRE-7 | **Scope §9**: 27-file repo drift in-scope vs. separate PR (spec §9, AC-3a/AC-3b) | user | Task 15/16 presence; AC-3b stays in this change only on "in-scope". AC-3a is always mandatory. |

Recommended defaults from the spec (used as plan assumptions unless overridden): PRE-2 ship default-on; PRE-3 `orchestrator` as `primary-role`; PRE-4 emit `.md` under `.github/agents/`; PRE-5 point Mammouth at `AGENTS.md`; PRE-6 keep v1 default (v2 opt-in, minor); PRE-7 in-scope.

## Global Constraints

- **Provider-Agnostik (project `CODE_CONVENTIONS`):** no `if provider == "…"` / `provider in (…)` in `scripts/lib/` — dispatch only on config values / capability flags. Repeated in every affected task note and guarded by AC-14 (Task 13).
- **Ordering & dependency:** config data (Task 4) before the code that consumes it; the validator core (Task 1) before integration (Task 3, Task 6); the sweep guard (Task 13) after all lib modules exist; repo regeneration (Task 15) after all behavior + scenario tasks; commit (Task 16) last.
- **Review gate after every task (plan-ledger):** Stage 1 `review-req` (evidence vs. the task's acceptance criterion) -> Stage 2 `review-quality` (code quality / blast radius). Both loops `max_iterations: 2`; aggregate cap `task-review.max-rounds: 4`. On reaching the cap the task stays open and is reported to the human. No next task starts before both stages pass.
- **Bite-sized & TDD:** each task writes its test first (red), implements, observes green, commits. No task is done on assumed green.
- **Ownership is globally disjoint:** no file appears in two tasks' `Files:` blocks. The repo's plan check (`spec_plan.py::_check_plan_graph`, `FanoutPlan(kind="sequential")` + `check_plan_file_overlap`) treats *any* overlap between two tasks as an ERROR; parallel groups additionally require disjoint ownership. Shared-file edits are consolidated into a single owning task.
- **No worktree isolation:** never spawn with `isolation: "worktree"` (`no-worktree-isolation`). Substitutes are Ownership + Barriers + Checkpoint-ledger. Repo-containment (root + `.tmp/`) is untouched.
- **Parallel ceiling:** `max-parallel-agents: 2` (project.yaml default). Every barrier/parallel group has at most 2 tasks.
- **Fail-loud reason gate:** `artifact-validation: false` requires a non-empty `artifact-validation-reason` (L-8 / AC-24).
- **Stdlib only:** new modules (`artifact_validate.py`, `consistency/artifact_contracts.py`, `consistency/model_contracts.py`) use `from __future__ import annotations` and only the standard library; `scripts/consistency-check.py` returns rc 0 on a clean tree once PRE-1 is resolved.

## File Structure

Create:
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
- `tests/scenarios/configs/68-antigravity-discovery-paths.project.yaml` — Antigravity `.agents/*` + `serverUrl`.
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
- `agents/1-generic/agent-meta-manager.md`, `agents/1-generic/agent-meta-scout.md`, `agents/1-generic/release.md` — provider-neutral body references (D5; 5 distinct refs across 3 files).
- `tests/test_provider_three_file_invariant.py` — skills + artifact-validation presence, reason gate, skills coupling.
- `tests/test_mcp_config.py` — `requestOptions.headers`, `http_headers`, `transport: sse`, `serverUrl`, v2 nesting, v1 byte shape.
- `tests/test_context_agents_md_idempotency.py` — run1 == run2 for all providers.
- `tests/test_provider_agnostic_dispatch.py` — `_TOUCHED_MODULES` replaced by a `scripts/lib/**/*.py` sweep.
- `tests/scenarios/registry.md` — one Katalog row per new scenario (64–72).
- Generated managed artifacts (~27 files under `.claude/`, `.gemini/`, `.agents/`, `.opencode/`, `.continue/`, `.github/`, `.mammouth/`, `.codex/`, `.zcode/`, `.kimi-code/` and root context files) — branch hygiene (Task 15).

## Interfaces (file:Symbol — contract)

- `scripts/lib/artifact_validate.py:validate_toml(text: str, path: str) -> list[Finding]` — parse with `tomllib`; ERROR on any parse failure.
- `scripts/lib/artifact_validate.py:validate_frontmatter(text: str, *, allowed_fields: set[str] | None, required_fields: set[str], reject_fields: set[str], path: str) -> list[Finding]` — ERROR for missing required, out-of-allow-list, or rejected keys.
- `scripts/lib/artifact_validate.py:validate_json_document(text: str, fmt: str, path: str) -> list[Finding]` — per-format key-set assertions (`opencode-json-v2` requires `mcp.servers` and no flat `mcp`; `opencode-json` requires flat `mcp`).
- `scripts/lib/consistency/artifact_contracts.py:check_artifact_contracts(agent_meta_root: Path) -> list[Finding]` — scans generated artifacts, Severity.ERROR.
- `scripts/lib/consistency/model_contracts.py:check_model_contracts(agent_meta_root: Path) -> list[Finding]` — emitted model matches `model-format` and is present in `model-catalog` when configured.
- `scripts/lib/provider_transform.py:apply_model_format(model: str, provider_config: dict) -> str` — `provider_config["model-format"].format(model=model)`, default `"{model}"`.
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
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `feat: add provider-agnostic artifact validators`

### Task 2: Consistency checks (artifact + model) + registration
**Agent:** developer
**Files:** Create: `scripts/lib/consistency/artifact_contracts.py`; Create: `scripts/lib/consistency/model_contracts.py`; Modify: `scripts/consistency-check.py`; Create: `tests/test_consistency_checks.py`
**Interfaces:** Produces `check_artifact_contracts`, `check_model_contracts`, both registered in `run_checks`; Consumes `artifact_validate` (Task 1) and the `model-catalog` config key.
**Acceptance:** AC-17 (consistency side) + AC-2: `python3 scripts/consistency-check.py` returns rc 0 on the clean tree; a corrupted fixture yields an ERROR; an emitted model outside a configured `model-catalog` is fail-loud.
**Verify:** `python3 -m pytest tests/test_consistency_checks.py -q` and `python3 scripts/consistency-check.py; echo $?` -> `0`
**Provider-Agnostik:** iteration is registry/catalog-driven; no name literals.
**Depends on:** 1
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `feat: register artifact and model consistency checks`

### Task 3: Sync-time validation wiring + exit codes
**Agent:** senior-developer
**Files:** Modify: `scripts/lib/agent_sync.py`; Modify: `scripts/sync.py`; Create: `tests/test_sync_validation_gate.py`
**Interfaces:** Produces `_finalize_agent_content` (singleton inside the body before serialization, validator called before write) and the `--check`/`--validate` rc policy; Consumes Task-1 validators.
**Acceptance:** AC-13 (sync end) + AC-3a: a scratch project with a narrowed `allowed-fields` makes `sync.py --validate` return rc 1; a normal sync stays rc 0 and logs `[WARN] artifact-contract:`.
**Verify:** `cd <scratch> && python3 <repo>/scripts/sync.py --validate; echo $?` -> `1`; `python3 -m pytest tests/test_sync_validation_gate.py -q`
**Provider-Agnostik:** findings are logged per provider from config, never from a name branch.
**Depends on:** 1
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `feat: surface artifact findings in sync check/validate`

### Task 4: Provider registry contract data (`ai-providers.yaml`)
**Agent:** senior-developer
**Files:** Modify: `config/ai-providers.yaml`; Create: `tests/test_provider_config_contracts.py`
**Interfaces:** Produces keys `surface-version`, `model-format`, `model-catalog`, `agent-transform.{tools-format,tool-name-map,allowed-fields,reject-fields,frontmatter-mechanism}`, `mcp-config.format` (`opencode-json`/`opencode-json-v2`/`antigravity-mcp-json`/`kimi-json`/`codex-toml-mcp`/`continue-yaml`), `primary-role`, `model-literal`, plus the migrated path values; Consumes PRE-2/PRE-3/PRE-4/PRE-5/PRE-6.
**Acceptance:** AC-21 (config side) + AC-25 (data side) + AC-8/AC-9 (values): every provider declares the new keys with correct types and defaults; KimiCode `model-format: "kimi-code/{model}"` with an initial catalog; Mammouth `tools-format: map`; Opencode `surface-version: v1` default while `v2` selects `opencode-json-v2`; Copilot `agents_dir`/`context_file`/`rules_dir` and Gemini/Antigravity `agents_dir`/`rules_dir`/`skills_dir` carry the new paths.
**Verify:** `python3 -m pytest tests/test_provider_config_contracts.py -q`
**Provider-Agnostik:** values only — no code branch.
**Depends on:** none
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `feat: add provider contract keys and migrated paths`

### Task 5: Capability flags (`provider-capabilities.yaml`)
**Agent:** developer
**Files:** Modify: `config/provider-capabilities.yaml`; Modify: `tests/test_provider_three_file_invariant.py`
**Interfaces:** Produces `skills`, `artifact-validation`, `artifact-validation-reason`, `mcp-remote-transport`; Consumes Task-4 data.
**Acceptance:** AC-15 + AC-24 + AC-25: every provider declares `skills` and `artifact-validation`; `artifact-validation: false` requires a non-empty reason; `skills: true` requires `skills` in the `ai-providers.yaml capabilities` list and a non-null `skills_dir`.
**Verify:** `python3 -m pytest tests/test_provider_three_file_invariant.py -q`
**Provider-Agnostik:** flags only; no name check.
**Depends on:** 4
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `feat: declare skills and artifact-validation capability flags`

### Task 6: Transform format contracts
**Agent:** senior-developer
**Files:** Modify: `scripts/lib/provider_transform.py`; Create: `tests/test_transform_contracts.py`
**Interfaces:** Produces `apply_model_format`; `tools-format: map`; `tool-name-map`; `allowed-fields`/`reject-fields`; `frontmatter-mechanism` incl. `opencode-native-v2`; Consumes Task-1 validators and Task-4 config.
**Acceptance:** AC-6 (Mammouth `tools:` object, never a list) + AC-13 (`reject-fields` violation yields a finding).
**Verify:** `python3 -m pytest tests/test_transform_contracts.py -q`
**Provider-Agnostik:** every mechanism is selected by the config value; no name branch.
**Depends on:** 1, 4
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `feat: extend agent transform with format contracts`

### Task 7: Model precedence + single format application
**Agent:** developer
**Files:** Modify: `scripts/lib/roles.py`; Create: `tests/test_model_contracts.py`
**Interfaces:** Produces `resolve_model` (ai-providers `model-tiers` wins over preset `tiers`; `model-format` applied once); Consumes Task-4 data.
**Acceptance:** AC-12 + AC-2: an active tier preset no longer shadows `ai-providers.yaml model-tiers`; `model-inherit-fallback` never emits a raw tier token; emitted IDs carry exactly one `kimi-code/` prefix.
**Verify:** `python3 -m pytest tests/test_model_contracts.py -q`
**Provider-Agnostik:** precedence is generic; no provider name.
**Depends on:** 4
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `fix: make provider model-tiers authoritative`

### Task 8: MCP writer format dispatch
**Agent:** senior-developer
**Files:** Modify: `scripts/lib/mcp_provider_config.py`; Modify: `tests/test_mcp_config.py`
**Interfaces:** Produces the `opencode-json-v2` branch (nested `mcp.servers`) and the transport/header spellings; Consumes Task-4 `mcp-config.format`.
**Acceptance:** AC-21 + AC-23 + AC-7 + AC-9: with `opencode-json-v2` the document contains `mcp.servers` and no flat `mcp`; with `opencode-json` the v1 flat byte shape is unchanged; Continue uses `requestOptions.headers`, Antigravity uses `serverUrl`; no writer branch reads `surface-version`.
**Verify:** `python3 -m pytest tests/test_mcp_config.py -q`
**Provider-Agnostik:** dispatch on the format string only (H-1 / ADR-10).
**Depends on:** 4
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `fix: dispatch mcp writers by declared format`

### Task 9: Pipeline notation from config + full registry
**Agent:** developer
**Files:** Modify: `config/delegation-syntax.yaml`; Modify: `scripts/lib/pipelines.py`; Create: `tests/test_pipeline_notation_config.py`
**Interfaces:** Produces `pipeline_notation.<Provider>` blocks and `pipeline_notation(provider, config_dir)` (config-backed, fail-loud) + registry provider list; Consumes evidence D6/D7.
**Acceptance:** AC-11: every provider has a complete notation block consistent with its `delegate` phrasing; notation comes from `delegation-syntax.yaml`; a missing block fails loud (no `task()` default); Copilot resolves via `registered_provider_names`.
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
**Verify:** `python3 -m pytest tests/test_bootstrap_submarkers.py -q`
**Provider-Agnostik:** cleanup iterates the bootstrap registry, replacing `"Gemini" in active`.
**Depends on:** 4
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `fix: scope bootstrap markers per provider`

### Task 11: Path migration + idempotency / pending-write fix
**Agent:** senior-developer
**Files:** Modify: `scripts/lib/sync_pipeline.py`; Modify: `scripts/lib/generated_file_drift.py`; Modify: `scripts/lib/context_templates/builder.py`; Create: `tests/test_migration_paths.py`; Modify: `tests/test_context_agents_md_idempotency.py`
**Interfaces:** Produces the ordered migration sequence (write-new -> verify -> backup-old -> remove-old), backup-first managed delete, the final-content diff, and Continue run1 substitution; Consumes Task-4 path values.
**Acceptance:** AC-22 + AC-3a + AC-4 + AC-18: the new path exists, the old managed path is gone, each removed managed file has a byte-exact `.sync-backup-<ts>` sibling, user-authored files are never deleted, renaming the backup restores the file; after a clean scratch sync `--check` rc 0 and `sha256(run1)==sha256(run2)`; a managed-block edit is rc 1, an out-of-block edit rc 0.
**Verify:** `python3 -m pytest tests/test_migration_paths.py tests/test_context_agents_md_idempotency.py -q`
**Depends on:** 4
**Provider-Agnostik:** migration and diff are driven by config keys; no name branch.
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `feat: migrate artifact paths and stabilise pending writes`

### Task 12: Provider-neutral template body references (D5)
**Agent:** junior-developer
**Files:** Modify: `agents/1-generic/agent-meta-manager.md`; Modify: `agents/1-generic/agent-meta-scout.md`; Modify: `agents/1-generic/release.md`
**Interfaces:** Produces provider-neutral phrasing for the five refs (`.claude/agents`, `.claude/skills/model-override-all/SKILL.md`, `.claude/commands/evaluate-repository.md`, `.claude/hooks/pre-release-check.sh`); Consumes the placeholder scheme.
**Acceptance:** ADR-6 (spec §12): after a sync into a non-Claude scratch project, the five `.claude/`-prefixed refs no longer appear in the generated bodies of the three roles.
**Verify:** `cd <scratch> && python3 <repo>/scripts/sync.py >/dev/null && ! grep -RE '\.claude/(agents|skills/model-override-all|commands/evaluate-repository|hooks/pre-release-check)' .codex .zcode .kimi-code`
**Provider-Agnostik:** neutral wording; no provider name literal.
**Depends on:** none
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `docs: provider-neutral template body references`

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
**Interfaces:** Produces nine executable scenarios with mandatory asserts and registry rows; Consumes all implemented behavior.
**Acceptance:** AC-19 + AC-4 + AC-5 + AC-7 + AC-8 + AC-9 + AC-22: scenarios 64–72 PASS, each with its own `asserts/<id>.sh` and Katalog row; scenario 71 ships the all-9-providers fixture proving `sha256(run1)==sha256(run2)` and `--check` rc 0.
**Verify:** `bash tests/scenarios/run.sh 64 65 66 67 68 69 70 71 72`
**Provider-Agnostik:** assertions key on generated artifacts, not provider names.
**Depends on:** 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit — `test: add provider-audit scenarios 64-72`

### Task 15: Repo regeneration (27-file drift)
**Agent:** developer
**Files:** Modify: `.claude/agents/`; Modify: `.gemini/agents/`; Modify: `.agents/agents/`; Modify: `.opencode/agents/`; Modify: `.continue/agents/`; Modify: `.github/agents/`; Modify: `.mammouth/agents/`; Modify: `.codex/agents/`; Modify: `.zcode/agents/`; Modify: `.kimi-code/agents/`; Modify: `AGENTS.md`
**Interfaces:** Produces a drift-free repo checkout; Consumes all preceding tasks and PRE-7 (in-scope).
**Acceptance:** AC-3b: `sync.py --check` returns rc 0 at the repo root after regeneration; each delta is inspected and any delta not explained by the new contracts is escalated, not committed silently.
**Verify:** `python3 scripts/sync.py && python3 scripts/sync.py --check; echo $?` -> `0`
**Provider-Agnostik:** regeneration is config/template-driven.
**Depends on:** 14
- [ ] Step 1: regenerate with `python3 scripts/sync.py`
- [ ] Step 2: inspect the 27-file delta per file
- [ ] Step 3: `--check` rc 0
- [ ] Step 4: commit — `chore: regenerate drifted provider artifacts`

### Task 16: Commit regenerated artifacts
**Agent:** git
**Files:** none (commit only; Git mutation delegated to the `git` agent)
**Interfaces:** Produces the branch-hygiene commit closing AC-3b; Consumes Task-15 output.
**Acceptance:** AC-3b: the regenerated artifacts are committed on `feat/provider-audit-opencode-v2`; `git status` is clean afterwards.
**Verify:** `git status --porcelain` (empty) and `git log -1 --stat`
**Provider-Agnostik:** not applicable (commit only).
**Depends on:** 15
- [ ] Step 1: stage the regenerated artifacts
- [ ] Step 2: commit — `chore: commit regenerated provider artifacts`
- [ ] Step 3: confirm clean tree

### Task 17: Full verification gate (stage `validate`)
**Agent:** validator
**Files:** none (verification only; results recorded in this plan's ledger)
**Interfaces:** Consumes all tasks; Produces the verification verdict.
**Acceptance:** AC-17 + AC-19 + AC-20 + AC-18: `--validate` rc 0, `consistency-check.py` rc 0 (after PRE-1), full scenario catalog PASS, pytest without `tests/browser` PASS.
**Verify:** `python3 scripts/sync.py --validate; python3 scripts/consistency-check.py; TMPDIR=<scratch> bash tests/scenarios/run.sh; python3 -m pytest tests/ -q --ignore=tests/browser`
**Provider-Agnostik:** verification commands are provider-generic.
**Depends on:** 16
- [ ] Step 1: run `--validate` + `consistency-check.py`
- [ ] Step 2: run the full scenario catalog
- [ ] Step 3: run pytest without `tests/browser`
- [ ] Step 4: record results in the ledger

### Task 18: Requirement-trace review (stage `review-req`)
**Agent:** validator
**Files:** none (review only)
**Interfaces:** Produces the AC-to-task traceability verdict; Consumes Tasks 1–17.
**Acceptance:** every AC-1…AC-25 maps to at least one verified task; no AC is claimed without a green verification command; harness-dependent ACs are labelled.
**Verify:** `python3 -m pytest tests/ -q --ignore=tests/browser` plus the traceability table in this plan.
**Provider-Agnostik:** review only.
**Depends on:** 17
- [ ] Step 1: check AC coverage
- [ ] Step 2: confirm harness-dependent/STATIC labels
- [ ] Step 3: record verdict

### Task 19: Quality review (stage `review-quality`)
**Agent:** code-reviewer
**Files:** none (review only)
**Interfaces:** Produces the code-quality/blast-radius verdict; Consumes Tasks 1–18.
**Acceptance:** no provider-name branch, no provider-coupled writer path, new modules Stdlib-only, blast radius limited to the affected providers.
**Verify:** `python3 -m pytest tests/test_provider_agnostic_dispatch.py tests/test_mcp_config.py tests/test_artifact_contracts.py -q`
**Provider-Agnostik:** review only.
**Depends on:** 18
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
| 4 | Provider registry contract data | `senior-developer` | none | AC-15, AC-21, AC-25, AC-8, AC-9 |
| 5 | Capability flags | `developer` | 4 | AC-15, AC-24, AC-25 |
| 6 | Transform format contracts | `senior-developer` | 1, 4 | AC-6, AC-13 |
| 7 | Model precedence + single format | `developer` | 4 | AC-12, AC-2 |
| 8 | MCP writer format dispatch | `senior-developer` | 4 | AC-21, AC-23, AC-7, AC-9 |
| 9 | Pipeline notation from config + registry | `developer` | 4 | AC-11 |
| 10 | Bootstrap sub-markers + migration | `senior-developer` | 4 | AC-10, AC-16 |
| 11 | Path migration + idempotency | `senior-developer` | 4 | AC-22, AC-3a, AC-4, AC-18 |
| 12 | Template body references (D5) | `junior-developer` | none | ADR-6 |
| 13 | Provider-agnostic sweep guard | `developer` | 1, 2, 3, 6, 7, 8, 9, 10, 11 | AC-14, AC-23 |
| 14 | Scenarios 64–72 + asserts + registry | `tester` | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | AC-19 |
| 15 | Repo regeneration (27-file drift) | `developer` | 14 | AC-3b |
| 16 | Commit regenerated artifacts | `git` | 15 | AC-3b |
| 17 | Full verification gate | `validator` | 16 | AC-17, AC-18, AC-19, AC-20 |
| 18 | Requirement-trace review | `validator` | 17 | AC-1…AC-25 coverage |
| 19 | Quality review | `code-reviewer` | 18 | AC-14, AC-23 |

## Parallel Groups (ownership-disjoint only)

Each group is one `FanoutPlan(kind="parallel_group", max_parallel=2)`. Only groups with pairwise disjoint `Files:` sets are parallelized; everything else is serialized by the dependencies above. Because ownership is globally disjoint (Global Constraints), every group is conflict-free by construction.

| Group | Tasks | Files (disjoint proof) | Result |
|---|---|---|---|
| PG-1 | 1, 4 | `scripts/lib/artifact_validate.py` + `tests/test_artifact_contracts.py` vs. `config/ai-providers.yaml` + `tests/test_provider_config_contracts.py` | disjoint |
| PG-2 | 5, 7 | `config/provider-capabilities.yaml` + `tests/test_provider_three_file_invariant.py` vs. `scripts/lib/roles.py` + `tests/test_model_contracts.py` | disjoint |
| PG-3 | 6, 8 | `scripts/lib/provider_transform.py` + `tests/test_transform_contracts.py` vs. `scripts/lib/mcp_provider_config.py` + `tests/test_mcp_config.py` | disjoint |
| PG-4 | 9, 10 | `config/delegation-syntax.yaml` + `scripts/lib/pipelines.py` + `tests/test_pipeline_notation_config.py` vs. `scripts/lib/bootstrap.py` + `scripts/lib/context.py` + `config/provider-bootstrap.yaml` + `tests/test_bootstrap_submarkers.py` | disjoint |
| PG-5 | 3, 12 | `scripts/lib/agent_sync.py` + `scripts/sync.py` + `tests/test_sync_validation_gate.py` vs. `agents/1-generic/agent-meta-manager.md` + `agents/1-generic/agent-meta-scout.md` + `agents/1-generic/release.md` | disjoint |
| PG-6 | 2, 11 | `scripts/lib/consistency/artifact_contracts.py` + `scripts/lib/consistency/model_contracts.py` + `scripts/consistency-check.py` + `tests/test_consistency_checks.py` vs. `scripts/lib/sync_pipeline.py` + `scripts/lib/generated_file_drift.py` + `scripts/lib/context_templates/builder.py` + `tests/test_migration_paths.py` + `tests/test_context_agents_md_idempotency.py` | disjoint |
| PG-7 (stage `validate`) | 17 validator parallel with tester | verification only; no writes | disjoint |

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
- Dependency graph (all 19 tasks): no empty plan, no duplicate `task_id`, no dangling dependency, no cycle. Every dependency edge points to a lower task number, so the graph is a strict DAG in numbering order and the Kahn peel completes with `find_dependency_errors` returning `[]`.
- Whole-graph file overlap: every task's `Files:` set is globally disjoint (Global Constraints; verified task-by-task below), so `check_plan_file_overlap` returns `{"safe": [all 19 ids], "conflict": []}` and `validate_plan` returns `[]`.
- Per-group validation: PG-1…PG-6 each have `len(tasks)=2 <= max_parallel=2` and disjoint `files_touched`; `validate_plan` returns `[]` for every group.
- `_check_plan_graph` in `spec_plan.py` uses `max_parallel=len(tasks)`, so no over-commitment is reported for the sequential whole-graph plan.
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
| 15, 16 | — | — | repo-root `sync.py --check` rc 0 |
| 17, 18, 19 | full catalog | `python3 -m pytest tests/ -q --ignore=tests/browser` | `--validate` + `consistency-check.py` rc 0 |

**Harness-dependent (not CI obligations):** AC-1 `codex mcp list` (creds absent), AC-2 `kimi acp`, AC-5 `opencode debug agents`, AC-6 `mammouth agent list` — each has a CI-mandatory static equivalent (tomllib / grep / scenario assert).
**Unverifiable here (STATIC / HYPOTHESIS, out of scope):** Antigravity `agy` (SIGILL, F6) -> AC-9 ships against the in-binary STATIC contract; Copilot context injection (no authenticated runtime, F9) -> AC-8 static-path only; ZCode workspace auto-load (open P6) stays STATIC. Opencode v2 is VERIFIED at parse/debug level only; a session turn was not run (F4, I-12).
**Environment-blocked:** `tests/browser` (35 socket errors per regression report §5) is excluded from AC-20.

## Risks and Rollback

References: Spec §11.1 (path-migration table) and Design §6.2.1 (5-step sequence: write new -> verify -> backup old -> remove old -> rollback by renaming the `.sync-backup-<ts>` sibling). ADR-9: a major bump for Copilot/Antigravity ships only together with the migration table; user files are never deleted.

| Risk | Impact | Mitigation |
|---|---|---|
| v2 silent drop after a config edit | agent disappears without a signal | `allowed-fields` + `--check`/`--validate` rc != 0 (Tasks 1–3, 8) |
| Path migration deletes a user file | data loss | managed-marker-scoped writes + `.sync-backup-<ts>` + user-file guard (Task 11, AC-22) |
| `model-format` applied twice | double prefix (`kimi-code/kimi-code/*`) | applied once at emission; `model_contracts` catches it (Tasks 7, 2) |
| Bootstrap marker migration breaks an existing `AGENTS.md` | lost context | scoped replace + user-note preservation (Task 10, AC-16) |
| v1 schema used to validate v2 artifacts | false invalidity | internal `artifact_validate` only, no official v2 schema (Task 1) |
| Config-key name collision | silent override | keys added to the three-file invariant (Task 5) |
| Major bump breaks SemVer-reactive consumers | stranded old paths | ordered migration + rollback (Task 11, §11.1) |
| Declarative `skills: true` diverges from generator reality | provider claims skills without artifacts | coupling rule + invariant (Task 5, AC-25) |
| 27-file drift committed unseen | unexplained deltas in branch | per-file inspection in Task 15; escalate unexplained deltas |

**Rollback principle:** never a silent move; every managed delete is preceded by a byte-exact backup sibling; restoring = rename `<file>.sync-backup-<ts>` back. Opencode v2 is opt-in (`surface-version` defaults to `v1`), so v1 projects are untouched and roll back by construction.

## Blockers and Critical Path

- **Approval gate (PRE-1…PRE-7):** all five `DECISION-NEEDED` OQs (OQ-1/4/5/7/8) and the §9 scope decision block Task 1. The plan stays PROVISIONAL until `concept-reviewer` sets the spec to `APPROVED`.
- **27-file repo drift (spec §9) is the branch-hygiene blocker:** it is an explicit precondition (PRE-7) and an explicit task pair (Task 15 regenerate + Task 16 commit). On the in-scope decision, AC-3b (`--check` rc 0 at the repo root) is satisfied by Tasks 15/16; on the rejected scope-split, Tasks 15/16 move to the follow-up PR and only AC-3b moves with them — AC-3a (scratch-consumer `--check` rc 0, Task 11) remains mandatory in this change.
- **Critical path:** Task 1 -> Task 3 -> Task 6 -> Task 13 -> Task 14 -> Task 15 -> Task 16 -> Task 17 -> Task 18 -> Task 19 (10 nodes). The parallel branches (Task 4 -> Task 7 -> Task 2, Task 4 -> Task 8/9/10/11, Task 12) are shorter and join at Task 13/14.
- **Follow-ups (non-goals, not blockers):** the 85 consistency warnings, the `1.2.0-beta.2` semver-regex warning (spec §1.3/§9), and the Continue template CO-2 (`templates/configs/CONTINUE.config-template.yaml:28`, Design OQ-9 / spec §1.3).

## Self-Review

- **Task-to-role:** every step maps to exactly one role; the `implement` stage maps to step 1 (`senior-developer`, an allowed tier); the review/validate stages map to steps 17–19.
- **Task-to-test:** every task has a test (pytest module or scenario assert) and an observable acceptance criterion; no criterion is "works correctly".
- **Ownership:** `Files:`/`Interfaces:` are complete and globally disjoint; no file is written by two tasks; shared-file edits are consolidated into one owning task.
- **Traceability:** each AC-1…AC-25 is covered by at least one task (see the table below); harness-dependent ACs are labelled (AC-1/2/5/6) and STATIC areas (AC-8/9) are documented.
- **`pipeline_stages`:** maps the plan-driven stage `implement` and the review/validate stages of `concept-driven-dev`.
- **No placeholders:** no unresolved placeholder markers; every task names exact paths, symbols, commit messages and a verification command.
- **No worktree isolation:** explicitly forbidden; Ownership + Barriers + Checkpoint-ledger are the substitutes.

### AC-to-Task Traceability

| AC | Task(s) | AC | Task(s) |
|---|---|---|---|
| AC-1 | 4, 8, 14 | AC-14 | 13 |
| AC-2 | 4, 7, 2, 14 | AC-15 | 4, 5 |
| AC-3a | 3, 11 | AC-16 | 10 |
| AC-3b | 15, 16 | AC-17 | 2, 17 |
| AC-4 | 11, 14 | AC-18 | 11, 17 |
| AC-5 | 4, 8, 14 | AC-19 | 14, 17 |
| AC-6 | 6, 14 | AC-20 | 17 |
| AC-7 | 8, 14 | AC-21 | 4, 8 |
| AC-8 | 4, 11, 14 | AC-22 | 4, 11, 14 |
| AC-9 | 4, 8, 11, 14 | AC-23 | 8, 13 |
| AC-10 | 10, 14 | AC-24 | 5 |
| AC-11 | 9 | AC-25 | 4, 5 |
| AC-12 | 7 | ADR-6 (D5) | 12 |
| AC-13 | 1, 3, 6 | | |
