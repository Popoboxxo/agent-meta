# Provider-Audit Gap Closure + Opencode v2 Support — Spec

> **Status: DRAFT — PENDING APPROVAL**
> **Review:** docs/specs/2026-09-30-provider-audit-opencode-v2-review.md (Iteration 1 eingearbeitet)
> **Design:** docs/specs/2026-09-30-provider-audit-opencode-v2-design.md
> **Evidence:** docs/analysis/2026-09-30-provider-audit-runtime-consolidation.md
> Trace anchor: `spec-id: SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30` (inherited verbatim from the design; the plan MUST reference this value).
>
> Classification: **XL / Architectural** (design stage exists; public config contracts and multiple subsystem boundaries are affected). Final approval marker (`Status: APPROVED (date)`) is set by `concept-reviewer`, not by this document.

---

## 0. Evidence base and traceability

Every technical statement below cites its source. IDs are used verbatim from the inputs:

| Source | IDs used here |
|---|---|
| `docs/specs/2026-09-30-provider-audit-opencode-v2-design.md` | §1–§9, `DECISION-1`…`DECISION-6`, `OQ-1`…`OQ-8`, `F1`…`F11` |
| `docs/analysis/2026-09-30-provider-audit-runtime-consolidation.md` | `H1`…`H10`, `N1`…`N20`, `A1`…`A11`, v1/v2 matrix |
| `docs/analysis/2026-09-30-provider-audit-generation.md` | `D1`…`D10` |
| `docs/analysis/2026-09-30-provider-audit-docs-part1.md` | Claude / Gemini-Antigravity / Opencode / Copilot contracts |
| `docs/analysis/2026-09-30-provider-audit-docs-part2.md` | Codex `CX-1`, ZCode `ZC-1/ZC-3`, Kimi, Continue `CO-1/CO-2`, Mammouth `MM-2/MM-4`, Copilot `P-1`…`P-6` |
| `docs/analysis/evidence/2026-09-30-regression-tests.md` | test baseline (63/63 scenarios, pytest 3127/3127 without `tests/browser`, `--check` rc=1 with 27 files) |

Verified code anchors used by the contracts (read-only, HEAD `65a493ec` on `feat/provider-audit-opencode-v2`):
`scripts/lib/provider_transform.py::transform_agent_content_for_provider` (:363), `scripts/lib/agent_sync.py::_finalize_agent_content` (:654), `scripts/lib/roles.py::resolve_model` (:326) / `_resolve_tier_to_model` (:291), `scripts/lib/pipelines.py::_PROVIDER_NOTATION` (:757) / `KNOWN_PROVIDERS` (:20), `scripts/lib/bootstrap.py` (:152–161), `scripts/lib/context.py::_cleanup_bootstrap_block` (:737) / legacy-marker regex (:759-762), `scripts/lib/mcp_provider_config.py::_write_provider_config` (:619–652, `opencode-json` branch :633–635), `scripts/lib/consistency/report.py::Finding/Severity` (:22–34), `scripts/consistency-check.py::run_checks` (:140).
Config anchors (HEAD `65a493ec`): `config/ai-providers.yaml` Copilot `agents_dir` (:317) / `context_file` (:319) / `rules_dir` (:328); Gemini `agents_dir` (:99) / `rules_dir` (:104) / `skills_dir` (:143); ZCode capabilities (:503-507) / `skills_dir` (:521); KimiCode capabilities (:554-557) / `skills_dir` (:571); `config/provider-bootstrap.yaml` Gemini (:16) / ZCode (:49).

---

## 1. Problem / Goal / Non-Goals / Scope boundaries

### 1.1 Problem

The provider audit proved that agent-meta generates artifacts which are broken, silently dropped, or placed at wrong paths in 8 of 9 real harnesses, while `sync.py` exits `0` in every case (design §1.1 point 1; generation report §1: "sync.py exited 0 with 0 errors for all 14 sync runs; none of the deviations is caught by sync-time validation"):

- Codex ships 2 invalid `.toml` files (`agent-meta-manager.toml:467`, `knowledge-curator.toml:100`) — singleton block appended after serialization (F1, N1/N2, D1).
- KimiCode emits 58 bare model IDs that its runtime does not accept (F2, H6).
- Opencode v2 silently drops `subagent_depth`, flat `mcp`, wrong-typed `permissions`/`mode` with `rc=0` and empty stderr (F4, N4–N6).
- Continue emits a Zod-invalid config (`roles:[…,"agent"]`, missing `name`/`version`, dropped SSE `headers`), and `.continue/skills/` is empty despite a declared capability (F7, N10–N12, H8/H9).
- Mammouth `tools:` as a YAML list aborts loading of the whole `.mammouth/agents/` directory (F8, N17).
- Copilot agents/rules/skills land at paths the runtime does not read (F9, N13, P-1…P-5).
- `--check` produces permanent false-positives (single-ZCode, multi-all) and entry-file drift run1→run2 (F10, N14–N16).
- Bootstrap markers collide for Gemini+ZCode (F10 §6, N15).
- Pipeline notation silently falls back to Opencode `task()` for 4 providers (D6), and `KNOWN_PROVIDERS` omits Copilot (D7).

### 1.2 Goal

1. Every generated artifact loads in its real harness **where a harness is observable**, and provider differences are expressed **only as config data / capability flags** — no `if provider == "Name"` in `scripts/lib/` (design §1.1 point 3; `CODE_CONVENTIONS`; positive precedent `provider_has_capability`, D10).
2. Every silent-drop / invalid-artifact class becomes a **sync-time signal** (warn at sync, fail under `--validate`/`--check`) (design §1.1 point 4, §4.3).
3. Add Opencode **v2** as a first-class surface next to v1 (`surface-version: v1|v2`), without duplicating templates or roles (design §4.1, DECISION-2).
4. Make `--check` drift-free in a clean tree and idempotent run1→run2 for all 9 providers (design §6.3).
5. Resolve the bootstrap marker collision with provider-scoped sub-markers (design DECISION-4, D8).

### 1.3 Non-Goals (explicit)

| Out of scope | Reason |
|---|---|
| Antigravity runtime acceptance (`agy`) | SIGILL on the audit CPU (F6); ships against in-binary STATIC contract, stays HYPOTHESIS (design §1.3). |
| Copilot runtime load proof | No authenticated Copilot runtime in the audit environment (F9 §6). |
| ZCode workspace auto-load verdict | Open P6 real-repo test (F10, `provider-capabilities.yaml` ZCode note). |
| Adding/removing providers | Registry stays at 9 providers. |
| A v2 JSON Schema | None published (`https://v2.opencode.ai/config.json` → 301/404, F4, N8). |
| Rewriting role templates wholesale | Only the four `.claude/...` body refs named in D5. |
| Fixing the 85 consistency warnings and the `1.2.0-beta.2` semver regex warning | Separate finding, non-blocking (`--validate` rc=0 tolerates warnings; regression report §4/Offene Punkte 3/4). |
| Continue `CO-2` template `roles` enum (`templates/configs/CONTINUE.config-template.yaml:28` — `roles: [chat, edit, agent]`) | Explicit follow-up ID (CO-2): the template is a user-edited starting point and is "NEVER overwritten by sync.py" (template header `:6`), so the fix belongs to the Continue naming-convention owner, not to the generator contract. The `continue-yaml` writer fixes the generated `.continue/config.yaml`/`config.local.yaml` (AC-7); the template file is tracked as a separate CO-2 follow-up (review I-13). |

### 1.4 Scope boundaries

In scope: `config/ai-providers.yaml`, `config/provider-capabilities.yaml`, `config/provider-bootstrap.yaml`, `config/delegation-syntax.yaml`; `scripts/lib/` transform/serialize/model/notation/bootstrap/MCP writers; new `scripts/lib/artifact_validate.py`; new consistency check module; template body-ref fixes for D5; new scenarios 64–72 and pytest modules (design §1.2, §7).

---

## 2. Interface Contracts

All keys below live in **config data**; no consumer branches on a provider name. Key names are provider-neutral; provider-specific facts are carried as values (design §3). All types are Python types after YAML load; `[str]` = `list[str]`, `{k: v}` = `dict[str, str]`.

### 2.1 `config/ai-providers.yaml` — per-provider keys

```yaml
providers:
  <Provider>:
    # NEW
    surface-version: "v1"                 # str; enum "v1"|"v2"; default "v1"
    model-format: "{model}"               # str; Python str.format(template, model=<resolved_id>); default "{model}"
    model-catalog:                        # list[str]; OPTIONAL; absent => check disabled (conservative, no false positives)
      - "<runtime-valid-model-id>"

    agent-transform:
      # NEW / EXTENDED
      tools-format: keep                  # enum keep|filter|skip|remove|map; default keep
      tool-name-map: {}                   # dict[str,str]; Claude tool name -> provider tool name; unknown source passes through
      allowed-fields:                     # list[str]; OPTIONAL; when set, any emitted frontmatter key outside it is a finding
        - name
        - description
      reject-fields: []                   # list[str]; default []; any emitted key here is a finding
      frontmatter-mechanism: provider-md  # enum provider-md|opencode-native|opencode-native-v2|codex-toml; default provider-md

    mcp-config:
      format: <format-enum>               # see 2.5
```

Semantics:

| Key | Semantics | Evidence |
|---|---|---|
| `surface-version` | Selects the generation surface where a product ships two generations. `v1` (default) keeps today's byte shape; `v2` selects `frontmatter-mechanism: opencode-native-v2` and `mcp-config.format: opencode-json-v2` (nested `mcp.servers`, §2.5 — the writer never branches on `surface-version`). | design §4.1; F4; DECISION-2; H-1 |
| `model-format` | Applied **exactly once** at emission to every resolved model ID. `{model}` is the only placeholder. Double application is a consistency error (`kimi-code/kimi-code/*`). | F2; H6; DECISION-5; design §8.1 |
| `model-catalog` | Exhaustive, runtime-valid ID set. Consumed only by `scripts/lib/consistency/model_contracts.py`; an emitted ID outside the catalog is a fail-loud finding. Absent = check disabled. | DECISION-5 |
| `tools-format: map` | Emits `tools: {<name>: true}` (object), never a YAML list. Required for Mammouth (list aborts loading, F8/N17). | F8; N17; D-note |
| `tool-name-map` | Maps Claude tool names to provider vocabulary (e.g. Antigravity `Read` → `view_file`). Unknown source name passes through unchanged. | docs-part1 §2.1 |
| `allowed-fields` | Frontmatter allow-list; turns Opencode v2's silent drop into a sync-time finding. | F4; N6; design §4.3 |
| `reject-fields` | Explicit deny-list; a violation is a fail-loud finding. | design §3.1 |
| `frontmatter-mechanism: provider-md` | **Explicit new default** replacing the "no block → left as generated" silent path. | design §3.1 note, `provider_transform.py:392-399` |

Concrete data values that MUST be set by this change (all values are config data, not code branches):

| Provider | Key/value | Evidence |
|---|---|---|
| KimiCode | `model-format: "kimi-code/{model}"`; `mcp-config.format: kimi-json`; `mcp-remote-transport: transport`; `skills: true` (PAL) **and** `capabilities: [..., skills]` in `ai-providers.yaml:554-557` (`skills_dir: .kimi-code/skills` at `:571`) | F2, H6, KC-1, F10/part2 flag-mismatch; M-5 |
| Mammouth | `agent-transform.tools-format: map` | F8, N17 |
| Codex | `mcp-config.format: codex-toml-mcp` (headers spelling `http_headers`) | CX-1 |
| Continue | `mcp-config.format: continue-yaml` (headers spelling `requestOptions.headers`) | F7, H8, A5 |
| Gemini/Antigravity | `mcp-config.format: antigravity-mcp-json` (remote `serverUrl`) | F6 G-7 |
| Opencode | `surface-version: v1` (default, `mcp-config.format: opencode-json`); `surface-version: v2` opt-in, which sets `mcp-config.format: opencode-json-v2` | F3, F4, DECISION-2, H-1 |
| ZCode | `skills: true` (PAL) **and** `capabilities: [..., skills]` in `ai-providers.yaml:503-507` (`skills_dir: .zcode/skills` at `:521`) | ZC-3; M-5 |

`model-tiers` / `model-aliases` precedence change (F11 D2/D3): **`ai-providers.yaml model-tiers` is authoritative**; a preset `tiers` map is a fallback behind it. `model-inherit-fallback` resolves through `_resolve_tier_to_model` and MUST never emit a raw tier token (`resolve_model` returns `""` for an unresolvable override-all; the Continue fallback at `provider_transform.py:290-296` must stop writing `roles_cfg[…]["model"]`).

### 2.2 `config/provider-capabilities.yaml` — capability flags

```yaml
capabilities:
  <Provider>:
    skills: true|false                 # bool; whether generated skills_dir artifacts are emitted
    artifact-validation: true          # bool; default true; false only with a required, non-empty reason
    artifact-validation-reason: null   # str|null; MUST be set and non-empty iff artifact-validation is false
    mcp-remote-transport: url          # enum url|transport|type; default url
```

- `skills`: add explicit `true` for ZCode and KimiCode (currently generated but undeclared — F10/part2 flag-mismatch). **Coupling rule (M-5):** the PAL flag `skills: true` is only valid together with (a) `skills` in the `ai-providers.yaml capabilities` list and (b) a non-null `skills_dir`. Artifact emission is gated on exactly these two keys (`scripts/lib/skills.py:376` reads `skills_dir`; `scripts/lib/skill_channel.py:42` gates on `skills_dir`; `scripts/lib/plugins.py:66` gates on `"skills" in pc["capabilities"]`), so the PAL flag MUST mirror them. Verified current state: ZCode has no `skills` in its capabilities list (`ai-providers.yaml:503-507`) although `skills_dir: .zcode/skills` exists (`:521`); KimiCode likewise (`:554-557`, `:571`). The three-file invariant test is extended with this coupling (below).
- `artifact-validation`: consumed by `agent_sync._finalize_agent_content`; `false` skips validation for that provider only. **Reason gate (L-8):** `artifact-validation: false` is only valid when the companion `artifact-validation-reason` is present and non-empty; the three-file invariant test fails on a missing or empty reason (closes the fail-open class named in the threat model 2(b)).
- `mcp-remote-transport`: declarative statement of how the provider discriminates remote MCP transport (`url` default; `transport` for KimiCode `transport: "sse"`; `type` where the discriminator key is `type`). Consumed by the format writer, never by a name branch (design §3.2; KC-1).
- The three-file invariant test (`tests/test_provider_three_file_invariant.py`) is extended to require `skills` and `artifact-validation` on every registered provider (design §3.2).

### 2.3 `config/delegation-syntax.yaml` — pipeline notation

Add a per-provider `pipeline_notation:` block with the exact key set currently hardcoded in `_PROVIDER_NOTATION` (`pipelines.py:757-828`):

```yaml
delegation_syntax:
  <Provider>:
    pipeline_notation:
      task_fmt: "<dispatch template>"
      mention_fmt: "<mention template>"
      loop_start: "<loop header>"
      loop_item: "<loop item template>"
      parallel_start: "<parallel header>"
      parallel_item: "<parallel item template>"
      fanout_start: "<fanout header>"
      fanout_item: "<fanout item template>"
      conditional_start: "<conditional header>"
      conditional_item: "<conditional item template>"
      sequential_start: ""
      sequential_item: "<sequential item template>"
```

- `pipelines.py` reads `pipeline_notation.<Provider>`; a missing block is a **fail-loud** finding (no `opencode` silent default — D6/F11).
- `KNOWN_PROVIDERS` is replaced by `providers.registered_provider_names(agent_meta_root)` (F11 D7: Copilot currently missing at `pipelines.py:20`).
- The rendered `task_fmt` values MUST be consistent with the existing `delegation_syntax.<Provider>.delegate` per provider (Codex `spawn_agent`, KimiCode `Agent`/`AgentSwarm`, ZCode `Agent(subagent_type=…)`, Copilot `@<agent>` sequential) — D6.

### 2.4 `config/provider-bootstrap.yaml` — marker contract

```yaml
bootstrap:
  <Provider>:
    mechanism: "api-based"
    action: "inject-bootstrap-instructions"
    marker_id: "<provider>"     # NEW str; default = provider name; scoped marker id
    context_file: null          # NEW str|null; when null, ai-providers.yaml context_file is used
    instructions_mode: "static" # optional; Gemini = generated roster, ZCode = static
```

Emitted marker pair: `<!-- agent-meta:bootstrap-begin:{marker_id} -->` … `<!-- agent-meta:bootstrap-end:{marker_id} -->` (design §3.5).

- `context._cleanup_bootstrap_block` iterates the bootstrap registry: for each provider declaring `action: inject-bootstrap-instructions`, keep its marker iff the provider is active, else remove that marker's sub-block. The literal `"Gemini" in active` (`context.py:753`) is removed (F10 §6, D8).
- `bootstrap.py` exposes the set of providers claiming a context file so the cleanup can be keyed by registry, not by literal (design §2.2).
- **Old-marker migration (M-6, D8):** the legacy unscoped pair `<!-- agent-meta:bootstrap-begin --> … <!-- agent-meta:bootstrap-end -->` (`context.py:759-762` regex, Gemini-scoped today at `:765`) is **discarded without attribution**: because two providers may have overwritten the same block, no provider can be reconstructed. On the first sync, *every* active provider with an `inject-bootstrap-instructions` action rewrites its own scoped pair; the unscoped pair is removed once. Order is deterministic (registry order of `provider-bootstrap.yaml` — Gemini at `:16`, ZCode at `:49`). No provider "inherits" the old block; a provider that would have had a block but no longer injects simply ends without one.

### 2.5 `mcp-config.format` — writer contracts

| Format | File / key | Remote transport | Headers spelling |
|---|---|---|---|
| `claude-settings` | `.mcp.json` `mcpServers` | `type: sse`, `url` | `headers` |
| `gemini-settings` | `.gemini/settings.json` `mcpServers` | `type: sse`, `url` | `headers` |
| `antigravity-mcp-json` (**new**) | `.agents/mcp_config.json` `mcpServers` | `serverUrl` | `headers` |
| `opencode-json` | `opencode.json` `mcp` (v1; **byte shape frozen** — no nesting) | `type: remote` | `headers` |
| `opencode-json-v2` (**new**) | `opencode.json` `mcp.servers` (nested) | `type: remote` | `headers` |
| `continue-yaml` | `.continue/config.yaml` `mcpServers` | `type: sse`, `url` | `requestOptions.headers` |
| `codex-toml-mcp` | `.codex/config.toml` `[mcp_servers.*]` | `url` | `http_headers` |
| `kimi-json` (**new**) / `zcode-json` | `.kimi-code/mcp.json` / `.zcode/config.json` | `transport: "sse"` (Kimi) / `type` discriminator (ZCode) | `headers` |
| `vscode-settings` | `.vscode/mcp.json` `servers` | remote `type: http` | `headers` |

The transport/header spelling is the writer's contract; the provider config only names the `format`. Dispatch on `mcp-config.format` only (design §3.4, §2.2).

**Opencode v2 dispatch rule (H-1, resolved):** the writer component is `scripts/lib/mcp_provider_config.py::_write_provider_config` (`:619-652`); its `if fmt == …` chain (`:630-651`) consumes the `opencode-json` value at `:633-635` as a **flat top-level** key: `_update_json_config(path, "mcp", …)`. The v2 target `mcp.servers` is therefore NOT produced by a `surface-version` conditional inside the writer. Instead the provider config sets `mcp-config.format: opencode-json-v2` and the writer gains a new `elif fmt == "opencode-json-v2":` branch that merges under the nested key. The byte-shape precedent already exists in the same module: `_update_zcode_json_config` (`:266-287`) writes `existing.setdefault("mcp", {})["servers"] = mcp_entries` (`:285`); the v2 branch reuses that helper or mirrors it (design DECISION-7, §3.4). Dispatch stays on the format value only; no branch reads `provider` or `surface-version`. `mcp-config.format: opencode-json` and its `:633-635` branch remain untouched; the v1 flat-`mcp` byte shape is frozen (AC-21, AC-23).

### 2.6 Function signatures (new / changed)

```python
# NEW: scripts/lib/artifact_validate.py
# Reuses scripts/lib/consistency/report.py::{Finding, Severity}.
def validate_toml(text: str, path: str) -> list[Finding]: ...
def validate_frontmatter(
    text: str, *,
    allowed_fields: set[str] | None,
    required_fields: set[str],
    reject_fields: set[str],
    path: str,
) -> list[Finding]: ...
def validate_json_document(text: str, fmt: str, path: str) -> list[Finding]: ...

# CHANGED: scripts/lib/provider_transform.py
def apply_model_format(model: str, provider_config: dict) -> str: ...
    # returns provider_config["model-format"].format(model=model); default "{model}"
def transform_agent_content_for_provider(...) -> str: ...
    # honours tools-format: map, tool-name-map, model-format,
    # allowed-fields/reject-fields, frontmatter-mechanism including opencode-native-v2

# CHANGED: scripts/lib/agent_sync.py
def _finalize_agent_content(...) -> str: ...
    # provider serialization runs LAST, after all body injections (singleton block
    # already inside the body); calls artifact_validate before _write_agent_file

# CHANGED: scripts/lib/roles.py
def resolve_model(...) -> str: ...
    # ai-providers.yaml model-tiers wins over preset tiers; model-format applied once

# CHANGED: scripts/lib/mcp_provider_config.py
def _write_provider_config(...) -> None: ...
    # dispatch on mcp-config.format; new "opencode-json-v2" branch writes the
    # nested key "mcp.servers" (precedent: _update_zcode_json_config, :266-287,
    # nested merge at :285); existing "opencode-json" branch (:633-635, flat
    # "mcp") stays byte-identical (see §2.5, H-1)

# CHANGED: scripts/lib/pipelines.py
def pipeline_notation(provider: str, config_dir: Path) -> dict: ...
    # _PROVIDER_NOTATION removed; notation read from delegation-syntax.yaml; missing => error

# NEW/CHANGED: scripts/lib/consistency/artifact_contracts.py
def check_artifact_contracts(agent_meta_root: Path) -> list[Finding]: ...
    # Severity.ERROR findings; registered in scripts/consistency-check.py::run_checks
```

---

## 3. Data flow

### 3.1 Generation path (unchanged shape, extended transform)

```
agents/{0-external,1-generic,2-platform}/<role>.md
  │  substitute placeholders (variables.py)
  ▼
provider_transform.transform_agent_content_for_provider(…)
  │   allowed-fields/reject-fields → tools-format → tool-name-map
  │   → model resolution (roles.resolve_model + apply_model_format)
  │   → strip rules → frontmatter-mechanism
  ▼
agent_toml.build_* (codex-toml) | frontmatter serialize (md providers)
  │   singleton constraint block already inside the body at this point
  ▼
artifact_validate.validate_toml | validate_frontmatter | validate_json_document
  │   → list[Finding]
  ▼
SyncLog (normal sync: [WARN] artifact-contract)  +  --validate/--check gate
  ▼
_write_agent_file(target)
```

Integration points (exact):

1. **Normal sync / `--dry-run`**: `agent_sync.py::_finalize_agent_content` (currently `:654`, called from the per-role path; singleton append is at `:752-753` today and moves before serialization). Findings are logged via `SyncLog.warning("<rel>", "artifact-contract: <message>")`; sync exit stays `0` (fail-soft, blast radius limited to the affected provider — design DECISION-3).
2. **`sync.py --check`**: `--check` already forces `dry_run=True` (`sync.py:99-105`) and reports "N file(s) out of sync". The check exit becomes `1` if `pending_writes > 0` **or** `artifact_findings_of_severity_ERROR > 0`, else `0`. This is the sole sync-time signal for Opencode v2 silent drops (design §4.3).
3. **`sync.py --validate`**: performs a full sync into the test repo and inspects `sync.log`; artifact findings are logged as `ERROR` in this mode and therefore produce a non-zero validate result. The mode is passed into `_finalize_agent_content` (or resolved from the active `SyncLog` mode) so the same validator is reused.
4. **`scripts/consistency-check.py`**: a new module `scripts/lib/consistency/artifact_contracts.py::check_artifact_contracts` is registered in `run_checks` (`consistency-check.py:140`) next to `check_fanout_backend_contract`; it validates the generated artifacts present in the agent-meta tree with `Severity.ERROR`. `--strict` remains warning-sensitive; plain `consistency-check.py` returns rc `1` only on ERROR (existing `print_report` semantics).

### 3.2 Bootstrap path (changed)

```
resolve_providers() → active providers
  │
provider-bootstrap.yaml[P].action == inject-bootstrap-instructions
  │   marker_id default = P ; context_file default = ai-providers.yaml[P].context_file
  ▼
bootstrap.write_block(context_file, "<!-- agent-meta:bootstrap-begin:<P> -->")
  │   P=Gemini → generated roster ; P=ZCode → static text  (instructions_mode)
  ▼
context._cleanup_bootstrap_block:
  for each registered P with an inject action:
     keep marker_P iff P is active ; remove marker_P sub-block otherwise
```

Two providers writing to the same context file (`AGENTS.md` for Gemini/Opencode/Codex/ZCode/KimiCode, `ai-providers.yaml:101,176,437,496,548`) now coexist as **distinct sub-blocks** (design DECISION-4, D8). Migration (M-6, deterministic, no attribution): the old unscoped pair `<!-- agent-meta:bootstrap-begin --> … <!-- agent-meta:bootstrap-end -->` (matched today at `context.py:759-762`) is removed; on the same sync every active `inject`-provider writes its own `:{marker_id}` pair in registry order (Gemini `provider-bootstrap.yaml:16`, ZCode `:49`). The old block is never handed to a single provider — the collision made the original writer unrecoverable. User notes outside managed markers are preserved (design §6.2; F10 §4).

### 3.3 `--check` / idempotency data flow

- Continue: the first sync must render the substituted `render_managed_block()` output (not the raw `{{PLACEHOLDER}}` template), so run1 is the fixpoint (design §6.3, F10 §2).
- ZCode `AGENTS.md`: the 3 internal writes per sync net to zero from run2 today; after the pending-write fix it becomes run1-stable (F10 §2, N16).
- The pending-write computation diffs the **final** (post-cleanup) content, not the intermediate states, so a net-zero sync reports clean (design §6.3, N14).

---

## 4. Decisions on OQ-1 … OQ-8

Each entry: **Recommendation**, **Rationale**, **Alternative**. `DECISION-NEEDED` marks an explicit user/approval decision that MUST NOT be taken silently by the spec.

### OQ-1 — Antigravity discovery: ship vs. flag-gate — **DECISION-NEEDED**

- **Recommendation:** Ship the discovery/path contract (`.agents/agents/`, `.agents/rules/`, `.agents/skills/`, `.agents/mcp_config.json` + `serverUrl`) as the default, because the in-binary STATIC contract is authoritative and the current `.gemini/agents/*` output is verifiably not discovered (N-fact from docs-part1 §2.1; F6). Mark Antigravity runtime acceptance HYPOTHESIS/STATIC in scenario 68 and the risk table.
- **Rationale:** Default-on gets the path right for every consumer; a flag would ship a known-wrong default. The only unknown is `agy` execution on this CPU, not the path contract.
- **Alternative:** Gate behind a per-provider opt-in flag until a pclmul-capable host runs `agy`. Cost: a second path remains wrong by default; benefit: zero risk of a wrong migration.
- **Why DECISION-NEEDED:** risk appetite for shipping against a STATIC (non-executed) contract (design §1.3, §7.4).

### OQ-2 — `.continue/agents/*.md` chat surface vs. `cn review` only

- **Recommendation:** Keep generating `.continue/agents/*.md` but **do not declare it as a chat-auto-discovery surface**; the scenario asserts only schema validity and the `cn review` read path. Add a header note in the generated file stating the auto-load is limited to `cn review` (H7/A6).
- **Rationale:** Auto-discovery is `cn review`-only (H7 `[STATIC]`); removing the files would break the one path that does read them.
- **Alternative:** Drop the surface entirely. Rejected: loses the `cn review` source and is a breaking artifact removal.

### OQ-3 — KimiCode `model-catalog` aliases

- **Recommendation:** Set `model-format: "kimi-code/{model}"` and an initial `model-catalog` equal to the formatted form of the current `model-tiers` values, i.e. `{kimi-code/kimi-k2.6, kimi-code/kimi-k2.7-code}`. The implementation task extends the catalog **only** from `kimi provider list --json` output; inventing aliases is prohibited.
- **Rationale:** The runtime expects `kimi-code/<alias>` (F2/H6); the formatted tier set is a verifiable subset; the catalog check then guards the prefix class.
- **Alternative:** Store fully-qualified IDs directly in `model-tiers`. Rejected in design DECISION-5 (leaves the bare-ID class unguarded). Vendor alias stability remains OQ-3's irreducible unknown and is documented as a data-maintenance item.

### OQ-4 — Opencode v2 entry agent (`mode: primary`) — **DECISION-NEEDED**

- **Recommendation:** Generate one primary entry agent, using the existing registry default: mark the `orchestrator` role as `mode: primary` and set `default_agent: orchestrator`; all other agents stay `mode: subagent`. Add a `primary-role` data key (default `orchestrator`) to `ai-providers.yaml` so no name is hardcoded in code.
- **Rationale:** v2 requires a valid default; setting `default_agent` to a subagent silently does nothing (N6, v1/v2 matrix). `orchestrator` is the documented entry point (AGENTS.md routing).
- **Alternative:** Keep `default_agent` unset and rely on built-in `build`. Rejected: leaves the generated surface without a primary entry and does not exercise `default_agent`.
- **Why DECISION-NEEDED:** choosing which role becomes the primary entry is a product/role decision and changes generated frontmatter semantics.

### OQ-5 — Copilot extension `.md` vs `.agent.md` — **DECISION-NEEDED**

- **Recommendation:** Emit `.md` under the corrected path `.github/agents/` (VS Code tolerant), and record the GitHub-cloud `.agent.md` requirement as a separate, opt-in convention to be decided with the naming-convention owner.
- **Rationale:** `.md` is the tolerant subset; the path fix (P-1) is orthogonal and mandatory. `.agent.md` changes the file-name contract globally and would affect stale-cleanup.
- **Alternative:** Emit `.agent.md` for GitHub cloud. Cost: breaks VS Code tolerance where documented.
- **Why DECISION-NEEDED:** file-naming convention affects all Copilot consumers (task explicitly names `.agent.md`).

### OQ-6 — Antigravity `model: inherit` vs. concrete tier IDs

- **Recommendation:** Set Antigravity `model: inherit` in `ai-providers.yaml` (data key `model-literal: inherit` or an empty `model-tiers` with `model: inject` → `inherit`), because the doc accepts only `inherit|flash|pro` and current IDs are non-contract (F6 G-3).
- **Rationale:** Removes an invalid vocabulary with the smallest change; keeps tier intent for other providers untouched.
- **Alternative:** Map tiers to `flash`/`pro`. Cost: loses per-role tiering; `inherit` is the safer default.

### OQ-7 — Mammouth context file `AGENTS.md` vs `CONTEXT.md` — **DECISION-NEEDED**

- **Recommendation:** Point Mammouth `context_file` at `AGENTS.md` (shared with the other context-file providers) and stop emitting `MAMMOUTH.md`; the binary reads `AGENTS.md`/`CLAUDE.md`/`CONTEXT.md`, but `AGENTS.md` is the cross-provider canonical (F8 MM-4, A11).
- **Rationale:** One canonical context file avoids duplicate maintenance; `MAMMOUTH.md` is proven unread.
- **Alternative:** Emit `CONTEXT.md`. Cost: a Mammouth-only fourth context file; more drift surface.
- **Why DECISION-NEEDED:** context-file topology/name is an explicit user convention decision (task names `CONTEXT.md` vs `AGENTS.md`).

### OQ-8 — v1→v2 default flip — **DECISION-NEEDED**

- **Recommendation:** Permanently opt-in for now: `surface-version: v1` default, `v2` per project. The SemVer path stays **minor while opt-in**; a default flip is scheduled only with a major release after v1 is deprecated.
- **Rationale:** Existing projects run v1.18.31 (F3); a hard flip is breaking without migration (design DECISION-2, §6.1). This refines design §6.1 (which lists the v2 surface as major) by tying the major bump to the **default flip**, not to the opt-in surface.
- **Alternative:** Flip default in a future major release. **Why DECISION-NEEDED:** product/SemVer-track decision.

---

## 5. Silent-drop handling: warn vs. fail, exit codes

The contract is a three-tier signal (design DECISION-3, §4.3; F4/N6):

| Context | Finding severity | Emitted as | Exit code |
|---|---|---|---|
| Normal `sync.py` / `--dry-run` | ERROR (validation) | `[WARN]` line `artifact-contract: <file>: <message>` in sync.log | `0` (fail-soft; one provider must not block the other eight) |
| `sync.py --check` | ERROR | `out-of-sync` / `artifact-contract` summary | `1` if drift **or** validation ERROR, else `0` |
| `sync.py --validate` / `consistency-check.py` | ERROR (mapped from Finding) | `[ERR]` report | `1` |
| `consistency-check.py --strict` | WARNING | `[WRN]` report | `1` |

- v2-specific guards (design §4.3): `allowed-fields` populated for Opencode; `validate_json_document("opencode.json", fmt)` asserts the resolved key set contains `mcp.servers` for `mcp-config.format: opencode-json-v2` / flat `mcp` for `opencode-json`, and contains **no** v1-only keys (e.g. `subagent_depth`, flat `mcp`) for `opencode-json-v2`; the presence/absence is asserted directly against the writer output (AC-21).
- Because v2's own validator is silent (`rc=0`, empty stderr — N6), `--check`/`--validate` are the only places a stale v2 artifact becomes visible.
- `artifact-validation: false` disables validation for a provider only; the three-file invariant requires the key to be present and explicit.

---

## 6. Idempotency and `--check` correctness (acceptance-relevant)

Required invariants (design §6.3, F10, N14–N16):

1. **Fixpoint after run 1**: for every scenario and every provider, `sha256(run1 file) == sha256(run2 file)`. This closes the Continue managed-block drift (`{{PLACEHOLDER}}` must be substituted on run1) and the ZCode `AGENTS.md` 3-write sequence (net-zero from run2).
2. **`--check` rc=0 in a clean tree**: immediately after a real sync, `sync.py --check` returns `0` for single-provider and multi-all projects alike. This closes the permanent false-positives (single-ZCode "2 files", multi-all "1 file", N14).
3. **Scoping preserved**: an edit inside a managed block → `--check` rc `1`; an edit outside managed blocks → rc `0` (regression-report §3/D9 scoping is correct and must not regress).
4. **Net-zero = clean**: the pending-write computation diffs the final (post-cleanup) content once, not intermediate writes.

---

## 7. Bootstrap collision (D8) — target behaviour

- Every bootstrap-writing provider emits its **own** marker pair keyed by `marker_id` (default = provider name): Gemini → `<!-- agent-meta:bootstrap-begin:Gemini -->`, ZCode → `<!-- agent-meta:bootstrap-begin:ZCode -->` (design §3.5, DECISION-4).
- Both blocks coexist in `AGENTS.md` in a Gemini+ZCode project; one provider's text is never overwritten by the other.
- In a ZCode-only project, the ZCode block is retained and no Gemini block is written; in a Gemini-only project the inverse. Cleanup is derived from the bootstrap registry, not from `"Gemini" in active` (`context.py:753`).
- The old unscoped single marker `<!-- agent-meta:bootstrap-begin -->` (no `:id`) is **discarded**, not reattributed; on first sync every active `inject`-provider writes its own scoped pair (deterministic registry order: Gemini then ZCode, `provider-bootstrap.yaml:16,49`). A project whose existing `AGENTS.md` contains only the legacy ZCode-sourced block and then syncs with Gemini+ZCode active ends with **both** `:Gemini` and `:ZCode` pairs, because the old block carries no provider identity (M-6). User notes outside managed markers are preserved (design §6.2, F10 §4).
- Non-injecting AGENTS.md providers (Opencode/Codex/KimiCode, `action: none` at `provider-bootstrap.yaml:11,44,77`) never receive a marker and never run cleanup; they are unaffected by the migration.
- Test criterion: after two clean syncs in a Gemini+ZCode project, `AGENTS.md` contains exactly one `bootstrap-begin:Gemini` and one `bootstrap-begin:ZCode` pair, `sha256(run1)==sha256(run2)`, and `--check` rc `0` (scenario 70 + `tests/test_bootstrap_submarkers.py`).

---

## 8. Acceptance Criteria (numbered, testable)

Each AC maps to at least one interface contract (§2) and states an observable result and verification command. Real-runtime commands assume the harness is installed; STATIC-only areas are explicitly labelled.

| ID | Criterion (Given/When/Then) | Verification command | Contract |
|---|---|---|---|
| AC-1 | Given a Codex sync, then all 58 generated `.codex/agents/*.toml` parse (`tomllib`) and Codex's own parser accepts the config. **Status: `tomllib` parse = CI-mandatory; `codex mcp list` = VERIFIED method, harness-dependent** (not a CI obligation — Codex creds absent in the audit env, F1/N1). | `python3 -c "import tomllib,pathlib; [tomllib.loads(p.read_text()) for p in pathlib.Path('<scratch>/.codex/agents').glob('*.toml')]"` (CI); real runtime: `CODEX_HOME=<scratch> codex mcp list` rc 0 (harness-dependent) | §2.1, §3.1; F1/N1/D1 |
| AC-2 | Given a KimiCode sync, then all 58 emitted model IDs are `kimi-code/*` and resolve as runtime aliases. **Status: `grep` prefix check = CI-mandatory; `kimi acp` = VERIFIED method, harness-dependent**. | `grep -h '^model:' <scratch>/.kimi-code/agents/*.md` all match `^model: kimi-code/` (CI); real runtime: `kimi acp` → `session/set_config_option {configId:"model"}` succeeds (harness-dependent) | §2.1; F2/H6 |
| AC-3a | Given a **scratch consumer project** after a clean real sync, then `sync.py --check` returns rc 0 (single-provider and multi-all). This measures generator correctness and is always testable, independent of the repo's own branch state. | `cd <scratch> && python3 <repo>/scripts/sync.py --check; echo $?` → `0` | §3.3, §5; F10/N14 |
| AC-3b | Given the **agent-meta repo root** after the Regenerate-Commit, then `sync.py --check` returns rc 0 (branch hygiene). Scope-dependent: only meaningful after the in-scope regeneration of the 27 drifted files; if the scope-split (§9) is chosen, AC-3a still MUST hold and AC-3b moves to the follow-up PR. | `python3 scripts/sync.py --check; echo $?` → `0` | §3.3, §9; F10/N14; ADR-8 |
| AC-4 | Given two consecutive real syncs for all 9 providers, then the second sync is byte-identical to the first (per generated file). | scenario `71-check-idempotency-all-providers` (`sha256(run1)==sha256(run2)`) | §3.3, §6; F10/N16 |
| AC-5 | Given `surface-version: v2` in a git-rooted project, then Opencode v2 loads 58/58 agents and the config retains `mcp.servers`/`default_agent`. | real runtime: `opencode debug agents` in a git root → 58 agents; `opencode debug config` shows `mcp.servers` | §2.1, §2.5, §5; F4/N5/N7 |
| AC-6 | Given a Mammouth sync, then every `tools:` frontmatter is an object, not a list. **Status: scenario assert = CI-mandatory; `mammouth agent list` = VERIFIED method, harness-dependent**. | scenario `66-mammouth-tools-map`; real runtime: `mammouth agent list` rc 0, no `Expected object … got [...]` (harness-dependent) | §2.1; F8/N17 |
| AC-7 | Given a Continue sync, then `.continue/config.yaml` passes the Zod schema, `config.local.yaml` has `name`/`version`, and SSE headers use `requestOptions.headers`. | scenario `72-continue-config-validity`; `@continuedev/config-yaml` parse → 0 fatal errors | §2.1, §2.5; F7/N10–N12/H8 |
| AC-8 | Given a Copilot sync, then artifacts exist at `.github/agents/`, `.github/instructions/`, `.github/skills/`, `.github/copilot-instructions.md`. | scenario `67-copilot-artifact-paths` | §2.5; F9/N13/P-1…P-5 |
| AC-9 | Given a Gemini/Antigravity sync, then `.agents/agents/`, `.agents/rules/`, `.agents/skills/`, `.agents/mcp_config.json` exist and remote MCP uses `serverUrl`. | scenario `68-antigravity-discovery-paths` (STATIC/HYPOTHESIS runtime) | §2.5; F6/G-7 |
| AC-10 | Given a Gemini+ZCode project, then `AGENTS.md` carries one sub-marker per provider and both rosters survive. | scenario `70-bootstrap-marker-convergence`; `tests/test_bootstrap_submarkers.py` | §2.4, §7; F10 §6/N15/D8 |
| AC-11 | Given any provider sync, then pipeline blocks use that provider's notation (no `task()` fallback). | scenario-level assertion + `tests/test_pipeline_notation_config.py`; missing `pipeline_notation` block → fail-loud | §2.3; D6/D7/F11 |
| AC-12 | Given an active tier preset, then `ai-providers.yaml model-tiers` wins and `model-inherit-fallback` never emits a raw tier token. | `tests/test_model_contracts.py` | §2.1; F11 D2/D3 |
| AC-13 | Given a `surface-version: v2` artifact with a key outside `allowed-fields`, then `--validate` returns rc 1 with an `artifact-contract` error. **Fixture mechanism (L-10):** `tests/test_artifact_contracts.py` builds a scratch `AiProviders`-config fixture whose `agent-transform.allowed-fields` is narrowed to `[name, description]` and injects an extra frontmatter key into a generated agent before calling `validate_frontmatter` (no live sync needed); the `--validate` end of the AC additionally uses a scratch project with the same narrowed allow-list. | `tests/test_artifact_contracts.py` (fixture) + `sync.py --validate` in the scratch project → rc 1 | §2.1, §5; F4/N6 |
| AC-14 | Given `scripts/lib/`, then no new `if provider == "…"` / `provider in (…)` branch is introduced. **L-7:** `tests/test_provider_agnostic_dispatch.py` MUST be extended — either replace the static `_TOUCHED_MODULES` tuple (`:27-56`) with a directory sweep over `scripts/lib/**/*.py`, or add the new modules `artifact_validate`, `consistency/artifact_contracts`, `consistency/model_contracts`, `mcp_provider_config`, `bootstrap`, `pipelines`, and `context` to the tuple. The sweep is preferred so a future module cannot bypass the guard. | `tests/test_provider_agnostic_dispatch.py` (AST/grep-based, sweep or extended list) | §2; design §1.1 |
| AC-15 | Given the provider registry, then (a) every provider declares `skills` and `artifact-validation` in `provider-capabilities.yaml`, (b) `artifact-validation: false` is accompanied by a non-empty `artifact-validation-reason`, and (c) for every provider with `skills: true`, `ai-providers.yaml` carries `skills` in its `capabilities` list AND a non-null `skills_dir` (M-5 coupling). | `tests/test_provider_three_file_invariant.py` (extended: presence + reason + skills coupling) | §2.2 |
| AC-16 | Given an existing `AGENTS.md`, then (a) user notes outside the managed block are preserved, (b) an old *scoped* marker for an inactive provider is removed while an active one survives, and (c) the **legacy unscoped** marker is discarded with no attribution (M-6): a fixture whose `AGENTS.md` contains only the ZCode-sourced legacy block, after a Gemini+ZCode sync, carries **both** a `bootstrap-begin:Gemini` and a `bootstrap-begin:ZCode` pair. | `tests/test_bootstrap_submarkers.py` (migration cases a/b/c) | §2.4, §7 |
| AC-17 | Given a clean repo, then `sync.py --validate` returns rc 0 (warnings tolerated) and `consistency-check.py` returns rc 0. | `python3 scripts/sync.py --validate; python3 scripts/consistency-check.py` | §5; regression report §3/§6 |
| AC-18 | Given a managed-block edit vs. an out-of-block edit, then `--check` returns rc 1 vs. rc 0 respectively. | scenario + regression re-check | §6; D9/F10 §3 |
| AC-19 | Given the full scenario catalog, then 63 existing + scenarios 64–72 all PASS, where each new scenario 64–72 has its own `tests/scenarios/asserts/<id>.sh` (executable, cwd = temp project dir, `REPO_ROOT` as `$1`/env — convention `tests/scenarios/asserts/62-stale-role-cleanup.sh:1-13`) and a `registry.md` row in the "Katalog" table (`registry.md:44-46`). Scenario `71-check-idempotency-all-providers` MUST ship the named fixture profile **all-9-providers** (`tests/scenarios/configs/71-check-idempotency-all-providers.project.yaml`) whose `ai-providers` list contains all nine registry keys (Claude, Gemini, Opencode, Continue, Copilot, Mammouth, Codex, ZCode, KimiCode); the existing catalog does not cover all nine in one generation, so the fixture is created by this change. | `TMPDIR=<scratch> bash tests/scenarios/run.sh` (all); `bash tests/scenarios/run.sh 64 65 66 67 68 69 70 71 72` (new IDs present) | §9, §10.1 |
| AC-20 | Given the pytest suite without the browser directory, then all tests pass. | `python3 -m pytest tests/ -q --ignore=tests/browser` | regression report §5 |
| AC-21 | Given `mcp-config.format: opencode-json-v2` (Opencode `surface-version: v2`), then the generated `opencode.json` contains a nested `mcp.servers` object and **no** flat top-level `mcp` key; given `opencode-json` (v1), the flat `mcp` key is present and the v1 byte shape is unchanged. | `tests/test_mcp_config.py` (extended) + scenario `69-opencode-v2-surface`; JSON probe asserts `"servers" in doc["mcp"]` and `"mcp"` is not a leaf server map | §2.5, §5; F4/N5; H-1 |
| AC-22 | Given a **bestandsprojekt** (existing consumer) that previously received Copilot/Antigravity artifacts at the old paths, then after one real sync: the new path exists, the old path is gone, every removed user-independent file has a byte-exact `.sync-backup-<ts>` sibling except where the file was not managed (user content is never deleted), and renaming the backup sibling restores the pre-migration file (rollback). | scenario `67-copilot-artifact-paths` / `68-antigravity-discovery-paths` migration asserts + `tests/test_migration_paths.py` (new) | §11; H-2; F9/N13/P-1…P-5 |
| AC-23 | Given the deprecated flat-`mcp` config (`mcp-config.format: opencode-json`) is not selected, then no `opencode.json` writer branch reads `surface-version`; the writer dispatch uses only the `mcp-config.format` value. | `tests/test_mcp_config.py` + `tests/test_provider_agnostic_dispatch.py` (no `surface-version` comparison in `scripts/lib/`) | §2.5, §2.6; AC-14 |
| AC-24 | Given `artifact-validation: false`, then the three-file invariant fails unless `artifact-validation-reason` is set and non-empty; given `artifact-validation: true`, no reason is required. | `tests/test_provider_three_file_invariant.py` (reason gate) | §2.2; L-8 |
| AC-25 | Given the `skills` capability, then for every provider with `skills: true` the `ai-providers.yaml` `capabilities` list contains `skills` and `skills_dir` is non-null; if either is missing the three-file invariant fails. | `tests/test_provider_three_file_invariant.py` (skills coupling) | §2.2; M-5 |

Mapping completeness: AC-1↔§2.1/§3.1, AC-2↔§2.1, AC-3a/3b/4↔§3.3/§6/§9, AC-5↔§2.1/§2.5, AC-6↔§2.1, AC-7↔§2.1/§2.5, AC-8/9↔§2.5, AC-10↔§2.4/§7, AC-11↔§2.3, AC-12↔§2.1, AC-13↔§2.1/§5, AC-14↔§2, AC-15↔§2.2, AC-16↔§2.4/§7, AC-17↔§5, AC-18↔§6, AC-19↔§9/§10.1, AC-20↔§9, AC-21↔§2.5/§5, AC-22↔§11, AC-23↔§2.5/§2.6, AC-24↔§2.2, AC-25↔§2.2. Every AC has at least one contract; no criterion is untestable.

---

## 9. Existing repo drift (`--check` rc=1, 27 files)

**Finding:** At branch HEAD `65a493ec`, `sync.py --check` reports `27 file(s) out of sync` (regression report §6). This is **pre-existing branch state**, not introduced by the test run (the tests mutate nothing — regression report "Arbeitsbaum-Mutationsverdikt" VERIFIED).

**Recommendation (in-scope):** Resolve it **within this change**. The acceptance criterion AC-3b requires `--check` rc=0 at the repo root in a clean tree; a change that fixes generation but leaves 27 drifted files cannot satisfy AC-3b (AC-3a, the scratch-consumer check, is independent of this and always holds). The implementation plan therefore ends with a real sync in the repo root and commits the regenerated artifacts, and the 27-file delta is inspected per file (expected: config/template-driven regeneration; any file whose delta is not explained by the new contracts is escalated).

**Rationale:** AC-3a (generator correctness, always testable) + AC-3b (branch hygiene, after the Regenerate-Commit) and AC-4 (run1==run2) are the core deliverables; splitting the drift into a separate PR would leave this branch failing its own AC-3b gate but must not falsify AC-3a.

**Alternative (scope-split):** Treat the 27-file drift as a separate finding/PR and move only AC-3b to that PR; AC-3a remains mandatory in this change and must be shown green on the scratch projects. Rejected unless the approval explicitly narrows scope.

**Explicitly separate:** the 85 consistency warnings (unknown placeholders `{{PARSE_INPUT_BLOCK}}`/`{{OUTPUT_GUARD_BLOCK}}`, missing CHANGELOG entries) and the `1.2.0-beta.2` semver-regex warning are **not** fixed by this spec (non-goal §1.3; `--validate` rc=0 already). They are recorded as follow-ups.

**Approval note:** the in-scope vs. scope-split choice is a PR-boundary decision that needs the approval gate (recorded as a scope decision, not an OQ).

---

## 10. Test strategy delta

### 10.1 New scenarios (`tests/scenarios/configs/`, next free IDs ≥ 64)

| ID | Provider(s) | Feature under test | Assert |
|---|---|---|---|
| 64-codex-toml-validity | Codex | singleton before serialization | every `.codex/agents/*.toml` parses with `tomllib` |
| 65-kimicode-model-namespace | KimiCode | `model-format` | every emitted model matches `kimi-code/*` |
| 66-mammouth-tools-map | Mammouth | `tools-format: map` | `tools:` is an object, not a list |
| 67-copilot-artifact-paths | Copilot | correct paths | `.github/agents/`, `.github/instructions/`, `.github/skills/`, `.github/copilot-instructions.md` |
| 68-antigravity-discovery-paths | Gemini | `.agents/*` + `serverUrl` | paths + `serverUrl` present |
| 69-opencode-v2-surface | Opencode (`surface-version: v2`) | v2 frontmatter list + `mcp.servers` + `default_agent` | no v1-only key emitted |
| 70-bootstrap-marker-convergence | Gemini + ZCode | distinct sub-markers | both markers present, one per provider |
| 71-check-idempotency-all-providers | all 9 (fixture profile **all-9-providers**: `tests/scenarios/configs/71-check-idempotency-all-providers.project.yaml` with all nine registry keys) | run1==run2 + `--check` rc 0 | byte-identity + clean check |
| 72-continue-config-validity | Continue | Zod-valid config | `roles` enum valid; `config.local.yaml` `name`/`version`; `requestOptions.headers` |

Each scenario gets an `asserts/<id>.sh` and a `registry.md` row (registry convention). The asserts file is mandatory for 64–72 (not a no-op scenario): `tests/scenarios/asserts/<id>.sh` executable, cwd = temp project dir, `REPO_ROOT` as `$1`/env (`registry.md:37-42`, reference `tests/scenarios/asserts/62-stale-role-cleanup.sh`).

### 10.2 New / extended pytest modules

| Module | Checks |
|---|---|
| `tests/test_artifact_contracts.py` (new) | `validate_toml` on all generated Codex artifacts; `validate_frontmatter` allow-list for Opencode; `validate_json_document` for v2 config |
| `tests/test_model_contracts.py` (new) | `model-format` prefix; `model-tiers` precedence over preset; no raw tier token from `model-inherit-fallback` |
| `tests/test_pipeline_notation_config.py` (new) | notation read from `delegation-syntax.yaml`; missing block fails loud; Copilot present via the registry |
| `tests/test_bootstrap_submarkers.py` (new) | distinct sub-markers; cleanup keyed by registry; Gemini+ZCode both survive; legacy unscoped marker discarded → both sub-markers written (M-6 case c); user notes preserved |
| `tests/test_context_agents_md_idempotency.py` (extend) | run1==run2 for all providers |
| `tests/test_mcp_config.py` (extend) | `requestOptions.headers`, `http_headers`, `transport: sse`, `serverUrl`; `opencode-json-v2` → nested `mcp.servers` and absent flat `mcp`; `opencode-json` v1 byte shape unchanged |
| `tests/test_migration_paths.py` (new) | Copilot/Antigravity old→new path migration: new path present, old path gone, managed files backed up, user files untouched, rollback from `.sync-backup-<ts>` restores (AC-22) |
| `tests/test_provider_three_file_invariant.py` (extend) | `skills` + `artifact-validation` declared; `artifact-validation-reason` non-empty when `artifact-validation: false`; `skills: true` ⇒ `ai-providers.yaml capabilities` contains `skills` and `skills_dir` non-null |
| `tests/test_provider_agnostic_dispatch.py` (extend) | no new provider-name branch in `scripts/lib/` — `_TOUCHED_MODULES` (`:27-56`) replaced by a `scripts/lib/**/*.py` directory sweep (preferred) or extended with the new modules (AC-14) |

### 10.3 Real-runtime vs. STATIC per provider

| Check | Harness | Status | Proof |
|---|---|---|---|
| Codex TOML parse | `codex mcp list` (scratch `CODEX_HOME`) | VERIFIED method | parseable config |
| Kimi ACP model resolution | `kimi acp` → `set_config_option` | VERIFIED method | generated alias resolves |
| Opencode v1 load | `opencode debug agent <name>` | VERIFIED | 58/58 load |
| Opencode v2 load | `opencode debug agents` (v2 binary, git root) | VERIFIED (parse/debug); **Session-Turn UNVERIFIABLE** | 58/58 parse, no silent drop; a full session turn was not run (`evidence/2026-09-30-runtime-opencode-v2.md:131-132`) |
| Claude hook cwd | `claude --settings … --debug hooks` | VERIFIED | `${CLAUDE_PROJECT_DIR}` succeeds from foreign cwd |
| Mammouth agent load | `mammouth agent list` | VERIFIED method | no schema error |
| Continue config validity | `@continuedev/config-yaml` Zod parse | VERIFIED method | 0 fatal errors |
| Antigravity discovery/hook execution | `agy` | **STATIC** (SIGILL, F6) | in-binary contract |
| Copilot context injection | authenticated Copilot | **STATIC** (no runtime, F9) | official docs |
| ZCode workspace auto-load | ZCode | **STATIC** (open P6) | capabilities note |

Browser suite (`tests/browser`, 35 errors via `pytest-socket`) remains environment-blocked and is out of this change's scope (regression report §5).

Status legend: **VERIFIED** = executed in the audit environment with observable output; **VERIFIED method, harness-dependent** = the command is the correct proof but requires an installed/authenticated harness and is therefore not a CI obligation; **STATIC** = contract read from official docs/in-binary strings, not executed; **HYPOTHESIS** = unverified. Opencode v2 is VERIFIED only at the parse/debug layer (F4, I-12).

---

## 11. Versioning and backward compatibility

- **v1 stays byte-compatible**: `surface-version` defaults to `v1`; existing MCP formats, context files and the `permission:` map shape are unchanged (F3; design §4.1, DECISION-2). A v1 project is untouched by this change.
- **v2 is opt-in** per project via `ai-providers.yaml::Opencode.surface-version: v2`; no consumer is migrated implicitly (design §6.2).
- **SemVer path** (design §6.1, refined by OQ-8):
  - Artifact corrections (Codex TOML, Kimi namespace, Mammouth `tools` map, Continue config) → **patch/minor**.
  - Path migrations (Copilot `.github/copilot/agents/` → `.github/agents/`; Antigravity `.gemini/agents/` → `.agents/agents/`) → **major for the affected provider** (generated artifact locations change; `EXTRA_DONTS: no breaking changes without major version bump`).
  - Opencode v2 surface while opt-in → **minor**; a **major** bump is reserved for a future default flip (OQ-8, DECISION-NEEDED).
- **Migration** (design §6.2; H-2): order is always **write new path → verify → remove old path (backup-first)**. User files outside managed markers are never deleted; every managed delete is preceded by a byte-exact `.sync-backup-<YYYYmmdd-HHMMSS>` sibling (existing stale-cleanup mechanism: `scripts/lib/generated_file_drift.py:255`, `docs/specs/2026-09-13-stale-role-cleanup-design.md:155,965-977`). The per-artifact table below names the config key that changes; every key lives in `ai-providers.yaml` and is dispatched as data, never by a provider-name branch. The old bootstrap marker is discarded and rewritten provider-scoped (§7); v2 is untouched for v1 projects.
- **Config compatibility**: new keys have defaults (`model-format`, `tools-format`, `reject-fields`, `artifact-validation`, `artifact-validation-reason`, `mcp-remote-transport`) so an unmodified consumer config keeps working; `surface-version` defaults to `v1`.

### 11.1 Path migration table (H-2)

Config keys are cited with their current line in `config/ai-providers.yaml` at HEAD `65a493ec`.

| Artifact class | Provider | Config key | Old path | New path | Cleanup | Backup | Rollback |
|---|---|---|---|---|---|---|---|
| Agents | Copilot | `:317 agents_dir` | `.github/copilot/agents` | `.github/agents` | stale-cleanup inside the old managed dir (managed-index/marker-scoped) | `.sync-backup-<ts>` per removed file | rename `<file>.sync-backup-<ts>` → `<file>` |
| Rules | Copilot | `:328 rules_dir` | `.github/copilot/rules` | `.github/instructions/` (`*.instructions.md`) | old rules dir emptied after new rules written | `.sync-backup-<ts>` | rename back |
| Context | Copilot | `:319 context_file` | `.github/copilot/COPILOT.md` | `.github/copilot-instructions.md` | old file removed only when no user content outside managed markers | `.sync-backup-<ts>` | rename back |
| Agents | Gemini/Antigravity | `:99 agents_dir` | `.gemini/agents` | `.agents/agents` | stale-cleanup inside the old managed dir | `.sync-backup-<ts>` | rename back |
| Rules | Gemini/Antigravity | `:104 rules_dir` | `.gemini/rules` | `.agents/rules` | old rules dir emptied after new rules written | `.sync-backup-<ts>` | rename back |
| Skills | Gemini/Antigravity | `:143 skills_dir` | `.gemini/skills` | `.agents/skills` | shared managed index in `skills_dir` | `.sync-backup-<ts>` | rename back |
| Bootstrap marker | Gemini+ZCode | n/a (context writer) | `<!-- agent-meta:bootstrap-begin -->` | `<!-- agent-meta:bootstrap-begin:{marker_id} -->` | legacy pair removed once, per-provider pair rewritten (§7, M-6) | context-file `.sync-backup-<ts>` | rename context-file backup back |

AC-22 exercises the rows above end-to-end on a bestandsprojekt.

---

## 12. ADR log (decisions recorded in this spec)

| ADR | Decision | Context | Consequences |
|---|---|---|---|
| ADR-1 | Express all provider differences as config data + a generic artifact validator (no provider subclasses, no per-provider JSON schemas). | design DECISION-1; project `CODE_CONVENTIONS`; D10 | One code path; config data is the contract; a missing key must fail loud. |
| ADR-2 | One `Opencode` provider with `surface-version: v1|v2` (v1 default) rather than a second provider entry or a hard replace. | design DECISION-2; F3/N3/A10 | Shared templates; opt-in v2; transform carries two mechanisms. |
| ADR-3 | Artifact validation: warn at sync, fail under `--validate`/`--check` (rc != 0). | design DECISION-3; F1/F4/N6 | Broken artifacts surface in CI; blast radius limited to the affected provider; every provider needs a declared contract. |
| ADR-4 | Provider-scoped bootstrap sub-markers with registry-derived cleanup. | design DECISION-4; F10 §6/N15/D8 | Both rosters coexist; precise cleanup; marker-schema migration required. |
| ADR-5 | `model-format` template + optional `model-catalog` check (no qualified-ID storage, no network fetch). | design DECISION-5; F2/H6 | Prefix declared once; wrong IDs fail in CI; catalog must be maintained per provider. |
| ADR-6 | Template-neutral `.claude/...` phrasing for the four D5 sites; existing strip rule kept as backstop. | design DECISION-6; D5 | Correct instructions in every provider; no blunt global stripping. |
| ADR-7 | Exit-code policy: sync rc 0 with WARN; `--check`/`--validate` rc 1 on ERROR. | §5; design DECISION-3 | Single silent-drop signal path; CI gate via `--check`/`--validate`. |
| ADR-8 | Resolve the 27-file repo drift within this change (regenerate + commit). | §9; regression report §6/AC-3b | `--check` rc 0 achievable at repo root; AC-3b split from AC-3a. |
| ADR-9 | Path changes migrate write-new-then-remove-old, backup-first, never a silent move; a major bump ships only together with the migration table §11.1. | H-2; design §6.2; `EXTRA_DONTS` | Bestandsprojekte converge on next sync; user files preserved; rollback by renaming the `.sync-backup-<ts>` sibling. |
| ADR-10 | Opencode v2 nesting is a distinct `mcp-config.format` value (`opencode-json-v2`), not a `surface-version` branch inside the writer. | H-1; §2.5/§2.6; design DECISION-7 | Writer dispatch stays format-only (provider-agnostic); v1 byte shape frozen; AC-21/AC-23 guard it. |

---

## 13. Open questions and risks

### 13.1 DECISION-NEEDED (blocking the approval gate)

| ID | Decision | Affected |
|---|---|---|
| OQ-1 | Ship Antigravity discovery default-on vs. flag-gated (STATIC contract) | §4, scenario 68, AC-9 |
| OQ-4 | Which role becomes the Opencode v2 primary entry (`default_agent`) | §4, AC-5 |
| OQ-5 | Copilot extension `.md` vs. `.agent.md` | §4, AC-8 |
| OQ-7 | Mammouth context file `AGENTS.md` vs. `CONTEXT.md` | §4 |
| OQ-8 | v1→v2 default flip timing and SemVer track | §11 |
| Scope | 27-file repo drift in-scope vs. separate PR | §9, AC-3a/AC-3b |

OQ-2 (Continue `.continue/agents` surface), OQ-3 (Kimi aliases), OQ-6 (Antigravity model `inherit`) are resolved by spec recommendation above with no approval dependency; OQ-3 remains a vendor-data maintenance item.

### 13.2 Risks

| Risk | Impact | Mitigation |
|---|---|---|
| v2 silent drop reintroduced after a config edit | agent disappears without a signal | allow-list validation + `--check`/`--validate` rc != 0 (§5) |
| Path migration deletes a user file | data loss | managed-marker-scoped writes + `.sync-backup-<ts>` siblings (design §6.2) |
| `model-format` applied twice | double prefix | applied once at emission; consistency check catches `kimi-code/kimi-code/*` |
| Bootstrap marker migration breaks an existing `AGENTS.md` | lost context | managed-marker-scoped replace + user-note preservation (§7, AC-16) |
| Official v1 schema used to validate v2 artifacts | false invalidity | no reliance on the official schema for v2; internal `artifact_validate` only (§5, design §4.4) |
| Config-key naming collision with an existing key | silent override | keys added to the three-file invariant + config audit (AC-15) |
| Antigravity/Copilot/ZCode stay STATIC | undetected runtime deviation | explicitly marked HYPOTHESIS/STATIC; real-runtime checks deferred (§10.3) |
| Major-Bump für Pfadänderungen (Copilot/Antigravity) bricht Bestands-Consumer | Artifact paths move under a major version; release pipelines / consumers reacting to "major" are unprepared, and an un-migrated project would leave orphaned old paths | Migrations-/Rollback-Pfad §11.1 + ADR-9: write-new-then-remove-old, backup-first, user files untouched (AC-22); majors are the declared SemVer track (§11) |
| Declarative `skills: true` diverges from generator reality (PAL vs. `ai-providers.yaml`) | a provider claims skills while no skills artifact is emitted (Copilot F9/N13 class) | coupling rule §2.2 / AC-25: `skills: true` requires `skills` in `capabilities` + non-null `skills_dir`; three-file invariant fails otherwise |

---

## 14. Self-review (spec-plan-workflow)

**Completeness**

| Required section | Present | Notes |
|---|---|---|
| Status / Design / Evidence / Trace anchor | yes | `Status: DRAFT — PENDING APPROVAL`; spec-id inherited verbatim |
| Problem / Goal / Non-Goals / Scope | yes | §1 |
| Interface Contracts (file:symbol, signature, error paths) | yes | §2.1–§2.6, exact keys/signatures |
| Data flow | yes | §3.1–§3.3 incl. `artifact_validate.py` integration |
| Acceptance Criteria (numbered, testable) | yes | §8, AC-1…AC-25 (AC-3 split into AC-3a/AC-3b) with verification commands |
| Open questions + risks | yes | §13 |
| ADR log | yes | §12, ADR-1…ADR-10 |
| Test strategy delta | yes | §10 |
| Versioning / backward compatibility | yes | §11 |
| Self-review | yes | this section |

**Logic**

- Every AC maps to at least one contract (§8 mapping line).
- Every contract key names its consumer: `surface-version`/`model-format`/`model-catalog`→transform/roles/consistency; `tools-format`→transform; `allowed-fields`/`reject-fields`→validator; `frontmatter-mechanism`→transform; `mcp-config.format`→MCP writer; `pipeline_notation`→pipelines; `marker_id`/`context_file`→bootstrap/context.
- No provider name appears in a described code path; all names are config values or test-fixture identifiers (§2, AC-14).

**No placeholders:** no `TBD`/`TODO`/`...`/empty interface. Where a value is vendor-dependent (OQ-3 aliases), an initial verified value and a clear extension rule are given instead of a placeholder.

**Traceability:** every technical claim cites F/H/N/A/D IDs or a design section (§0, inline references). The trace anchor `spec-id: SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30` is ready for the plan's `Spec:` field.

**Residual uncertainty:** OQ-1/OQ-4/OQ-5/OQ-7/OQ-8 and the §9 scope decision are `DECISION-NEEDED` and block the `Status: APPROVED` marker until resolved.

**Review iteration 1 (2026-10-01):** all findings from `docs/specs/2026-09-30-provider-audit-opencode-v2-review.md` are incorporated: H-1 (§2.5/§2.6/AC-21/AC-23, ADR-10), H-2 (§11.1/AC-22, ADR-9, risk row), M-3 (AC-3a/3b, §9), M-4 (AC-19 + scenario-71 fixture, §10.1), M-5 (§2.2 coupling, AC-15/AC-25, risk row), M-6 (§2.4/§3.2/§7, AC-16c), L-7 (AC-14/§10.2 sweep), L-8 (reason key + AC-24), L-9 (risk row), L-10 (AC-13 fixture), I-11 (AC-1/2/6 status markers), I-12 (F4/§10.3 parse-only), I-13 (CO-2 non-goal). The five `DECISION-NEEDED` OQs remain open and unchanged.

---

## Trace anchor

`spec-id: SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30`
