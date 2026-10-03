---
spec-id: SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30
title: Provider-Audit Gap Closure + Opencode v2 Support — System Design
status: Entwurf
revision: 1
related:
  - scripts/lib/provider_transform.py
  - scripts/lib/agent_sync.py
  - scripts/lib/agent_toml.py
  - scripts/lib/roles.py
  - scripts/lib/pipelines.py
  - scripts/lib/delegation_syntax.py
  - scripts/lib/bootstrap.py
  - scripts/lib/context.py
  - scripts/lib/mcp_provider_config.py
  - scripts/lib/providers.py
  - config/ai-providers.yaml
  - config/provider-capabilities.yaml
  - config/provider-bootstrap.yaml
  - config/delegation-syntax.yaml
  - tests/scenarios/registry.md
---

# Provider-Audit Gap Closure + Opencode v2 Support — Design

> spec-id: SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30
>
> Status: **Entwurf** — this document is spec input. The approval marker
> `Status: APPROVED` is set by `concept-reviewer`, not by this document.
> Trace anchor (inherited verbatim by the spec): `spec-id: SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30`.
>
> This is a **system design** (XL / cross-cutting): it contains component
> boundaries, interface contracts, trade-off decisions and data flow —
> **no spec and no implementation code** (only exact signatures / config keys).
> It is the upstream stage input of the pipeline
> `quality_pipelines.concept-driven-dev` (stage `specify`).

### Evidence legend

- **VERIFIED** — observed in this repo or in a real harness; evidence file + section cited.
- **STATIC** — verified only against an official contract embedded in a binary/doc, not executed.
- **HYPOTHESIS** — not verified; must be resolved before a flag is flipped.
- Every technical claim below cites its evidence file. Source analyses:
  `2026-09-30-provider-audit-generation.md` (D1–D10),
  `2026-09-30-provider-audit-docs-part1.md` / `-part2.md` (contracts),
  `evidence/2026-09-30-runtime-*.md`, `evidence/2026-09-30-entry-file-verification.md`.

### Revision

| Date | Author | Change |
|---|---|---|
| 2026-09-30 | concept-architect | First version. Closes the runtime-verified provider gaps, adds Opencode v2 as a generated surface, adds sync-time artifact validation, fixes bootstrap-marker collision and `--check`/idempotency drift. |
| 2026-10-01 | concept-architect | Revision 2 (review-fix pass, iteration 1): pinned the v2 MCP format value `opencode-json-v2` + writer dispatch + DECISION-7 (H-1); added the path-migration/rollback sequence per artifact class and the major-bump justification (H-2); added the legacy bootstrap-marker migration rule (M-6); added the SemVer-break risk row (L-9); sharpened the F4 evidence qualifier (I-12); named CO-2 as follow-up OQ-9 (I-13). |
| 2026-10-01 | concept-specifier | Revision 3 (review-fix pass, iteration 2, MINOR): §3.1 `surface-version` wording aligned to DECISION-7/§3.4/AC-23 (selects the `mcp-config.format` value; the format-dispatched writer consumes it); §3.2/§7.2 mirrored to Spec §2.2/AC-24/AC-25 (`artifact-validation-reason` gate + `skills`↔`capabilities`/`skills_dir` coupling); §3.3 dropped the non-existent `action_*` notation keys. |

---

## 0. Verified fact base (input, not re-derived)

| ID | Fact | Evidence |
|---|---|---|
| F1 | Codex: 2/58 generated `.toml` invalid (`agent-meta-manager.toml:467`, `knowledge-curator.toml:100`); singleton block appended **after** TOML serialization. | `evidence/2026-09-30-runtime-codex-kimi-zcode.md` §1 |
| F2 | KimiCode: 58/58 generated bare model IDs are **not** configured runtime aliases; runtime expects `kimi-code/<alias>`. | `evidence/2026-09-30-runtime-codex-kimi-zcode.md` §2 |
| F3 | Opencode v1.18.31 loads all 58 generated agents; `edit: allow` is **not** the Bad-Request cause; unknown frontmatter keys land in `options`. | `evidence/2026-09-30-runtime-opencode-v1.md` |
| F4 | Opencode v2 (`@opencode/cli@2.0.20`, separate package) installs and loads 58/58 — **VERIFIED at parse/debug level only** (`opencode debug agents` / `debug config`); a **Session-Turn/LLM call remains UNVERIFIABLE** in the audit environment (no run/turn was executed, `evidence/2026-09-30-runtime-opencode-v2.md` §2.1 and §4 "not run"). v2 silently drops `subagent_depth` and flat `mcp`; wrong-typed `permissions`/`mode` are dropped without warning; official `https://opencode.ai/config.json` is still the v1 schema; v2 project discovery requires a VCS root. | `evidence/2026-09-30-runtime-opencode-v2.md` §1–§4 |
| F5 | Claude: relative hook commands are cwd-dependent (exit 127); `${CLAUDE_PROJECT_DIR}` fixes it in a real probe. | `evidence/2026-09-30-runtime-claude-antigravity.md` §1.1 |
| F6 | Antigravity: `matcher:"*"` doc-conformant; `.agents/hooks.json` command resolvable; `.gemini/agents/*` is **not** discovered (discovery is `{workspace}/.agents/agents/{name}/`); `agy` SIGILLs on this CPU → runtime unverifiable. | `evidence/2026-09-30-runtime-claude-antigravity.md` §2 |
| F7 | Continue: `.continue/config.yaml` Zod-invalid (`roles:[…,"agent"]`); `config.local.yaml` missing `name`/`version`; top-level `agents:` is dead config; SSE `headers` dropped (only `requestOptions.headers`); `.continue/skills/` artifactless despite a `skills` capability; `.continue/agents/*.md` auto-discovery only in `cn review`. | `evidence/2026-09-30-runtime-continue.md` |
| F8 | Mammouth: `tools:` list → `Configuration is invalid … Expected object … got [...] tools`, all agents unloadable; bare model ID → `ProviderModelNotFoundError`; `MAMMOUTH.md` is an orphan (binary reads `AGENTS.md`/`CLAUDE.md`/`CONTEXT.md`). | `evidence/2026-09-30-runtime-mammouth-copilot.md` §0–§2 |
| F9 | Copilot: agents at wrong path (`.github/copilot/agents/` vs `.github/agents/`), rules wrong path (`.github/copilot/rules/` vs `.github/instructions/`), skills empty, `COPILOT.md` never loaded. | `evidence/2026-09-30-runtime-mammouth-copilot.md` §3–§5 |
| F10 | Entry files: 7/9 single-provider byte-idempotent; Continue + ZCode drift run1→run2 (then fixpoint); `--check` permanent false-positives on single-ZCode and multi-all. Bootstrap marker collision Gemini+ZCode VERIFIED (`context.py:753`, `bootstrap.py:152-161`). | `evidence/2026-09-30-entry-file-verification.md` §2–§3, §6 |
| F11 | Generator deviations D1–D10 (singleton ordering, model-tier shadowing, Continue raw-tier fallback, Claude-only fields, `.claude/` body refs, pipeline notation fallback `task()` for 4 providers, stale `KNOWN_PROVIDERS` without Copilot, bootstrap collision, gitignored-root `--check` blind spot, provider-name literals). | `2026-09-30-provider-audit-generation.md` §2–§5 |

---

## 1. Objective and scope boundaries

### 1.1 Objective

Make every generated provider artifact load correctly in its real harness (where a harness is observable), and turn the currently **silent** failure classes into **sync-time, fail-loud signals**. Concretely:

1. Close the runtime-verified defects F1–F3, F7–F11 (invalid Codex TOML, wrong model namespace, wrong artifact paths, invalid config shapes, unloadable agent lists).
2. Add Opencode **v2** as a first-class generated surface next to v1, without duplicating templates or roles.
3. Make provider differences expressible as **config data / capability flags only** — no new `if provider == "Name"` branch (project rule, `.meta-config/project.yaml` `CODE_CONVENTIONS`; positive precedent `provider_has_capability`, D10).
4. Make "provider X rejects/drops key Z" a **declared contract** validated at sync time instead of a runtime surprise.

### 1.2 In scope

- `config/ai-providers.yaml`, `config/provider-capabilities.yaml`, `config/provider-bootstrap.yaml`, `config/delegation-syntax.yaml` data changes.
- `scripts/lib/` transform, serialization, model-resolution, notation, bootstrap and MCP-writer changes.
- New per-provider declarative contracts (model format/catalog, artifact field policy, pipeline notation, MCP transport spelling).
- New sync-time artifact validation layer + consistency checks.
- Template/body corrections for the `.claude/...` leftovers (D5).
- New scenarios and pytest modules.

### 1.3 Explicitly out of scope

| Out | Reason |
|---|---|
| Antigravity runtime acceptance | `agy` SIGILL on the audit CPU (F6) — runtime unverifiable here; discovery change ships against the in-binary STATIC contract, marked HYPOTHESIS. |
| Copilot runtime load proof | No authenticated Copilot runtime in the audit environment (F9 §6) — static-path correctness only. |
| ZCode workspace auto-load verdict | Still an open P6 real-repo test (F10, `provider-capabilities.yaml` ZCode note). |
| Adding/removing providers | Registry stays at the current 9 providers. |
| A v2 JSON Schema | None published; `https://v2.opencode.ai/config.json` → 301/404 (F4). |
| Continue template `roles` enum (CO-2) | `templates/configs/CONTINUE.config-template.yaml:28` emits `roles: [chat, edit, agent]`; `agent` is outside the runtime `roles` enum (F7/N11, `evidence/2026-09-30-runtime-continue.md` §3/§8). This is a **generator** defect, not a generated-config warning: named follow-up **CO-2**, tracked as **OQ-9** (§9) — fixing the generated `.continue/config.yaml` is in scope, fixing this user-editable template is not. |
| Rewriting role templates wholesale | Only the four `.claude/...` body refs named in D5 are touched. |

---

## 2. Components and responsibilities

### 2.1 Component map

```
config/ai-providers.yaml        [DATA]  per-provider surface: paths, agent-transform,
                                        model-tiers, model-format, model-catalog,
                                        mcp-config, surface-version
config/provider-capabilities.yaml [DATA] boolean capability flags (commands, runtime_gate,
                                        skills, fanout, …)
config/provider-bootstrap.yaml  [DATA]  bootstrap mechanism + instructions per provider
config/delegation-syntax.yaml   [DATA]  dispatch + pipeline notation per provider

scripts/lib/provider_transform.py  [TRANSFORM]  applies agent-transform policy:
                                        field policy, tools-format, tool-name-map,
                                        model-format, strip rules, body refs
scripts/lib/agent_toml.py          [SERIALIZER]  codex-toml document builder
scripts/lib/agent_sync.py          [ORCHESTRATOR] finalize order: singleton BEFORE
                                        serialization; calls artifact validator
scripts/lib/roles.py               [RESOLVER]   model precedence: provider model-tiers
                                        authoritative, then preset tiers
scripts/lib/pipelines.py           [RENDERER]   pipeline notation from delegation-syntax;
                                        provider list from providers registry
scripts/lib/delegation_syntax.py   [GETTER]     exposes pipeline notation + action names
scripts/lib/bootstrap.py           [WRITER]     provider-scoped bootstrap markers
scripts/lib/context.py             [WRITER]     bootstrap cleanup from registry (no literal)
scripts/lib/mcp_provider_config.py [WRITER]     format-keyed MCP writers
scripts/lib/artifact_validate.py   [NEW/VALIDATOR] post-serialization artifact validation
scripts/lib/consistency/*.py       [CHECKER]    sync-time drift checks
```

### 2.2 Responsibilities (one per component)

| Component | Single responsibility |
|---|---|
| `artifact_validate.py` (new) | One pure function per artifact kind: `validate_toml(text, path) -> list[Finding]`, `validate_frontmatter(text, allowed_fields, required_fields, path) -> list[Finding]`, `validate_json_document(text, fmt, path) -> list[Finding]`. Returns findings; never writes. |
| `provider_transform.py` | Apply the `agent-transform` contract to a rendered agent document. Extended to honour `tools-format: map`, `tool-name-map`, `model-format`, `allowed-fields`/`reject-fields`. |
| `agent_sync.py::_finalize_agent_content` | Order provider serialization **last**, after all body injections. |
| `roles.py` | Resolve role → model; apply `model-format`; per-provider `model-tiers` wins over preset `tiers`. |
| `pipelines.py` | Render pipeline blocks using per-provider notation read from `delegation-syntax.yaml`; iterate the provider registry (not a private tuple). |
| `bootstrap.py` | Inject the bootstrap block under a provider-scoped marker; expose the set of providers claiming a context file. |
| `context.py::_cleanup_bootstrap_block` | Remove a bootstrap sub-block when **its** provider is inactive, keyed from `provider-bootstrap.yaml`. |
| `mcp_provider_config.py` | Dispatch on `mcp-config.format` only; each format writer owns the transport/header spelling. |

### 2.3 Data flow

```
agents/{0-external,1-generic,2-platform}/<role>.md
  │  substitute placeholders (variables.py)
  ▼
provider_transform.transform_agent_content_for_provider(…)   ← reads agent-transform
  │   field policy → tools-format → tool-name-map → model-format → strip rules
  ▼
agent_toml.build_* (codex-toml)  |  frontmatter serialize (md providers)
  │   (singleton constraint already inside the body at this point)
  ▼
artifact_validate.validate_*   → Findings → SyncLog + sync_pipeline stage gate
  ▼
_write_agent_file(target)
```

Bootstrap data flow (changed):

```
resolve_providers() → active providers
  │
provider-bootstrap.yaml[P].action == inject-bootstrap-instructions
  │   marker = "<!-- agent-meta:bootstrap-begin:<P> -->"
  ▼
bootstrap.write_block(context_file, marker_P)
  │
context._cleanup_bootstrap_block: for each registered P with an
  inject action, keep its marker iff P is active; remove otherwise
```

---

## 3. Interface contracts (config keys and semantics)

All new keys live in **config data**; no consumer branches on a provider name. Key names are provider-neutral; the values carry the provider-specific facts.

### 3.1 `config/ai-providers.yaml` — new / extended per-provider keys

| Key | Type | Default | Semantics |
|---|---|---|---|
| `surface-version` | str | `"v1"` | Selects the generation surface where a product ships two generations (Opencode). In config data it selects `agent-transform.frontmatter-mechanism` (`opencode-native` / `opencode-native-v2`, §4.1) and the `mcp-config.format` value (`v1` → `opencode-json`, `v2` → `opencode-json-v2`, §3.4); the format-dispatched writer consumes that value and never branches on `surface-version` (DECISION-7, §3.4, AC-23). |
| `model-format` | str | `"{model}"` | Template applied to every resolved model ID before emission. `{model}` = resolved ID. Example value for KimiCode: `"kimi-code/{model}"`. |
| `model-catalog` | list[str] | absent | Exhaustive list of runtime-valid IDs for the provider. Consumed **only** by `consistency/model_contracts.py` — an emitted model outside the catalog is a fail-loud finding. Absent = check disabled (conservative, no false positives). |
| `agent-transform.tools-format` | enum | `keep` | `keep \| filter \| skip \| remove \| map`. `map` emits `tools: {<name>: true}` (Mammouth needs the object form — F8). |
| `agent-transform.tool-name-map` | map[str,str] | `{}` | Claude tool name → provider tool name (e.g. Antigravity `Read`→`view_file`). Unknown source name passes through unchanged. |
| `agent-transform.allowed-fields` | list[str] | absent | Frontmatter allow-list. When set, `artifact_validate` fails loud on any emitted key outside it. Turns Opencode v2's silent drop (F4) into a sync-time signal. |
| `agent-transform.reject-fields` | list[str] | `[]` | Field names that must not be emitted; violation = fail-loud finding. |
| `agent-transform.frontmatter-mechanism` | enum | `provider-md` | `provider-md \| opencode-native \| opencode-native-v2 \| codex-toml`. `provider-md` is the explicit new default replacing the "no block → left as generated" silent path (D10 note, `provider_transform.py:392-399`). |
| `mcp-config.format` | enum | — | Existing dispatch key; the writer branches on this string only (never on a provider name). Extended value set adds `opencode-json-v2` (see 3.4). For `Opencode`, `surface-version` selects which format value is written (`v1` → `opencode-json`, `v2` → `opencode-json-v2`); the value itself stays a plain format string. |

`model-tiers` / `model-aliases` semantics change (F11 D2/D3): **`ai-providers.yaml model-tiers` is authoritative**; a preset `tiers` map is a fallback behind it. `model-inherit-fallback` resolves through `_resolve_tier_to_model` and must never write a raw tier token (D3).

### 3.2 `config/provider-capabilities.yaml` — capability flags

| Key | Type | Semantics |
|---|---|---|
| `skills` | bool | Whether the provider receives generated `skills_dir` artifacts. Add explicit `true` for ZCode and KimiCode (currently generated but undeclared — F10/part2 flag-mismatch). **Coupling rule (M-5):** `skills: true` is valid only together with `skills` in the `ai-providers.yaml capabilities` list **and** a non-null `skills_dir`; artifact emission is gated on exactly these two keys (`scripts/lib/skills.py:376` reads `skills_dir`; `scripts/lib/skill_channel.py:42` gates on `skills_dir`; `scripts/lib/plugins.py:66` gates on `"skills" in pc["capabilities"]`). |
| `artifact-validation` | bool | Whether the provider's generated artifacts are passed through `artifact_validate`. Default `true`; `false` is valid only when the companion `artifact-validation-reason` is present and non-empty. |
| `artifact-validation-reason` | str\|null | Mandatory and non-empty **iff** `artifact-validation` is `false`; `null` otherwise. Closes the fail-open class named in the threat model 2(b) (L-8). |
| `mcp-remote-transport` | enum | `url` (default) \| `transport` \| `type` — declarative statement of how the provider discriminates remote MCP transport (KimiCode: `transport`; Codex: `url` + `http_headers`). Consumed by the format writer; no name branch. |

The three-file invariant test (`tests/test_provider_three_file_invariant.py`) is extended to (a) require `skills` and `artifact-validation` on every registered provider, (b) fail when `artifact-validation: false` is not accompanied by a non-empty `artifact-validation-reason` (AC-24), and (c) fail when `skills: true` is not mirrored by `skills` in the `ai-providers.yaml capabilities` list plus a non-null `skills_dir` (AC-25 coupling).

### 3.3 `config/delegation-syntax.yaml` — pipeline notation

Add a per-provider `pipeline_notation:` block with the key set currently hardcoded in `pipelines.py::_PROVIDER_NOTATION` (D6):

```
pipeline_notation:
  task_fmt: "<dispatch template>"
  mention_fmt, loop_start, loop_item, parallel_start, parallel_item,
  fanout_start, fanout_item, conditional_start, conditional_item,
  sequential_start, sequential_item
```

**No `action_*` keys.** The v2 action names (`shell`, `subagent`) are `permissions` frontmatter values (§4.1), not pipeline-notation entries. The actual `_PROVIDER_NOTATION` (`pipelines.py:757-828`) ends at `sequential_item` and contains no `action_*` key (grep `action_` under `scripts/lib/` → 0 hits), and Spec §2.3 lists exactly those 12 keys; the earlier placeholder is dropped rather than added to the spec.

`pipelines.py` reads `pipeline_notation.<Provider>`; a missing block is a **fail-loud** finding (no `opencode` silent default — D6/F11). `KNOWN_PROVIDERS` is replaced by `providers.registered_provider_names(agent_meta_root)` (F11 D7: Copilot currently missing).

### 3.4 `mcp-config.format` — writer contracts

| Format | File / key | Remote transport | Headers spelling |
|---|---|---|---|
| `claude-settings` | `.mcp.json` `mcpServers` | `type: sse`, `url` | `headers` |
| `gemini-settings` | `.gemini/settings.json` `mcpServers` | `type: sse`, `url` | `headers` |
| `antigravity-mcp-json` (**new**) | `.agents/mcp_config.json` `mcpServers` | `serverUrl` (F6 G-7) | `headers` |
| `opencode-json` | `opencode.json` flat top-level `mcp` — **v1 only, byte form unchanged** (F3, `mcp_provider_config.py:633-635`) | `type: remote` | `headers` |
| `opencode-json-v2` (**new**) | `opencode.json` nested `mcp.servers` — **v2; no flat `mcp` key** (F4 §2.2, `evidence/2026-09-30-runtime-opencode-v2.md` §2) | `type: remote` | `headers` |
| `continue-yaml` | `.continue/config.yaml` `mcpServers` | `type: sse`, `url` | **`requestOptions.headers`** (F7 H8) |
| `codex-toml-mcp` | `.codex/config.toml` `[mcp_servers.*]` | `url` | **`http_headers`** (F11 CX-1) |
| `kimi-json` (**new**) or `zcode-json` | `.kimi-code/mcp.json` / `.zcode/config.json` | **`transport: "sse"`** (F11 KC-1) | `headers` |
| `vscode-settings` | `.vscode/mcp.json` `servers` | remote `type: http` | `headers` |

The transport/header spelling is the writer's contract; the provider config only names the `format`. This keeps the code provider-agnostic.

**Dispatch rule (binding).** The v1/v2 split lives in the **format value**, not inside the v1 writer: `_write_provider_config` gains a new `elif fmt == "opencode-json-v2":` branch that writes the nested key (the existing `_update_zcode_json_config` at `mcp_provider_config.py:266-287` already implements the identical nested-`mcp.servers` pattern and is the precedent). The existing `elif fmt == "opencode-json":` branch (`mcp_provider_config.py:633-635`) stays untouched and continues to write flat `mcp`. This avoids a provider-coupled `if provider == "Opencode"` branch in the writer — the exact anti-pattern the provider-agnostic rule forbids.

**v1 compatibility rationale.** A v1 project declares `mcp-config.format: opencode-json` and keeps today's flat `mcp` byte form; nothing in this design rewrites it. Only when `surface-version: v2` is set does the Opencode entry switch to `opencode-json-v2`, so the two surfaces never share a writer branch and no v1 artifact is re-touched (§4.1, DECISION-7). `validate_json_document(text, fmt)` asserts the key shape follows from `fmt`: nested `mcp.servers` for `opencode-json-v2`, flat `mcp` for `opencode-json` (§4.3).

### 3.5 `config/provider-bootstrap.yaml` — marker contract

| Key | Type | Semantics |
|---|---|---|
| `marker_id` | str | Provider-scoped marker id, default = provider name. The emitted marker becomes `<!-- agent-meta:bootstrap-begin:{marker_id} --> … <!-- agent-meta:bootstrap-end:{marker_id} -->`. |
| `context_file` | str | Optional explicit target; when absent the provider's `ai-providers.yaml context_file` is used (removes the hardcoded `.gemini/GEMINI.md` default, F11 D10 #7). |

`context._cleanup_bootstrap_block` iterates the bootstrap registry: for each provider that declares `action: inject-bootstrap-instructions`, keep its marker iff the provider is active, else remove that marker's sub-block. The literal `"Gemini" in active` is removed (F10 §6).

**Legacy-marker migration (D8, binding).** The current writer emits an id-less pair `<!-- agent-meta:bootstrap-begin --> … <!-- agent-meta:bootstrap-end -->` (`bootstrap.py:152-153`); Gemini and ZCode both target `AGENTS.md` and both inject (`config/ai-providers.yaml:101` Gemini `context_file: AGENTS.md`; `provider-bootstrap.yaml:16-18` and `:49-56`), so the legacy marker is **not attributable** to a single writer (the collision case F10 §6). Migration therefore does **not** try to reconstruct the author:

1. **Alt-Marker verwerfen:** on the first sync, any id-less legacy pair on the target context file is removed as a whole. User notes outside the managed marker are preserved.
2. **Deterministic Neu-Schreibung:** afterwards, every provider in the bootstrap registry with `action: inject-bootstrap-instructions` writes its **own** `:{marker_id}` sub-marker, in registry declaration order (`provider-bootstrap.yaml` order: Gemini before ZCode). The id-less marker form is no longer emitted by any code path.
3. **Cleanup:** a provider's sub-block is removed iff that provider is inactive (registry-keyed, no literal provider name). A legacy id-less marker found in a later sync is treated as stale and removed by step 1.

Consequence: from state "only the ZCode legacy marker present" in a Gemini+ZCode project, the first sync yields **both** `:Gemini` and `:ZCode` sub-markers (scenario 70, §7.1).

### 3.6 Function signatures (new / changed)

```python
# scripts/lib/artifact_validate.py (NEW)
def validate_toml(text: str, path: str) -> list[Finding]: ...
def validate_frontmatter(text: str, *, allowed_fields: set[str] | None,
                         required_fields: set[str], reject_fields: set[str],
                         path: str) -> list[Finding]: ...
def validate_json_document(text: str, fmt: str, path: str) -> list[Finding]: ...

# scripts/lib/provider_transform.py (changed)
def apply_model_format(model: str, provider_config: dict) -> str: ...
# returns provider_config["model-format"].format(model=model) (default "{model}")

# scripts/lib/pipelines.py (changed)
# _PROVIDER_NOTATION removed; notation read from delegation-syntax.yaml
def pipeline_notation(provider: str, config_dir: Path) -> dict: ...

# scripts/lib/mcp_provider_config.py (changed)
# _write_provider_config dispatch (mcp_provider_config.py:619-653) gains:
#   elif fmt == "opencode-json-v2": _update_opencode_v2_json_config(path, mcp_entries, …)
# _update_json_config(path, "mcp", …)        → unchanged, v1 flat mcp
# _update_opencode_v2_json_config writes existing.setdefault("mcp", {})["servers"] = mcp_entries
# (same nested-write pattern as _update_zcode_json_config, mcp_provider_config.py:266-287)
```

---

## 4. Opencode v1 vs v2 — explicit handling

v2 is **not** a tag of `opencode-ai`; it ships as a separate package `@opencode/cli` (F4). It is a config-surface migration, not a new engine.

### 4.1 Separate targets / config switch

- **One provider name (`Opencode`), one template set, two surfaces** selected by `config/ai-providers.yaml::Opencode.surface-version` (`v1` default, `v2` opt-in per project).
- `surface-version: v2` selects:
  - `agent-transform.frontmatter-mechanism: opencode-native-v2` → emits `permissions:` as an ordered list `[{action, resource, effect}]` with v2 action names (`shell`, `subagent`), and `mode/subagent`/`hidden/color` as v2 fields.
  - `mcp-config.format: opencode-json-v2` → the MCP writer emits nested `mcp.servers` and no flat top-level `mcp` key (dispatch rule §3.4, DECISION-7).
  - Removal of `subagent_depth` from the generated `opencode.json`.
  - Emission of `default_agent` and `agents` (plural) where applicable.
- `surface-version: v1` keeps today's shape, which v1 loads 58/58 (F3). v1's runtime normalizes the `permission:` map to a list internally, so the v1 artifact is not re-touched.
- Rationale for a version key instead of two provider entries: templates and roles stay shared; the v1 compat layer accepts the v1 map, so a single source can target both without duplicating 58 agent files (trade-off §5.2).

### 4.2 Discovery-root requirement

v2 project discovery requires a VCS/project root (F4 §1: no git root → `[]`; after `git init` + commit → 58/58 loaded). The syncer **cannot** create a git repo in the consumer project. Contract: the generated `AGENTS.md`/sync log emits an advisory note when `surface-version: v2` is active and the target root has no `.git` — informational, non-blocking (same class as the existing gitignored-root note, F11 D9).

### 4.3 Silent-drop problem

v2 drops unknown/invalid keys (`subagent_depth`, flat `mcp`, wrong-typed `permissions`, invalid `mode`/`effect`) **without any warning** (F4 §2.2). The syncer addresses this with the **artifact validation layer**:

- `agent-transform.allowed-fields` is populated for Opencode; `artifact_validate.validate_frontmatter` fails loud on any key outside the allow-list.
- `validate_json_document("opencode.json", fmt)` asserts the resolved key set contains `mcp.servers` (v2) / `mcp` (v1) and does **not** contain v1-only keys when `surface-version: v2`.
- Because v2's own validator is silent, the **syncer** is the only place where a stale v2 artifact becomes visible. This is the core reason the validation layer is in scope (§5.3).

### 4.4 Official schema gap

`https://opencode.ai/config.json` is still the v1 schema and rejects a v2-native document (F4 §2, STATIC-MISMATCH). The design therefore does **not** rely on the official schema for v2; it uses the internal `artifact_validate` contract. `$schema` in the generated `opencode.json` stays pointed at the official URL (no invented schema URL).

---

## 5. Trade-off decisions

### DECISION-1 — Declarative contracts (config keys) vs. provider registry entries vs. per-provider JSON schemas

```
context: provider differences must be expressed without `if provider == "Name"`.
choice: keep a single provider registry; express every difference as config data
        (agent-transform, model-format/model-catalog, mcp-config.format,
        delegation-syntax pipeline_notation) + a generic artifact validator.
alternatives:
  - Provider subclasses / per-provider code modules → rejected: reintroduces the
    name-branch pattern the project forbids (CODE_CONVENTIONS; D10).
  - Full JSON Schema per provider → rejected: no authoritative schema exists for
    Opencode v2 or Antigravity (F4 §2, F6); vendor schemas drift silently, which
    is exactly the failure class we are closing.
consequences:
  - easier: one code path, data-only fixes, three-file invariant test enforces completeness.
  - harder: the config data becomes the contract; a missing key must fail loud, not default silently.
```

### DECISION-2 — Opencode v2 as a `surface-version` key vs. a second provider entry vs. replacing v1

```
context: v1 and v2 differ in frontmatter shape, config keys and actions, but share templates.
choice: one `Opencode` provider with `surface-version: v1|v2` (v1 default).
alternatives:
  - Second registry entry (`OpencodeV2`) → rejected: duplicates 58 agent files,
    roles, and the whole transform surface; two sources drift.
  - Replace v1 → rejected: existing projects run v1.18.31 (F3); a hard flip is a
    breaking change without migration, violating EXTRA_DONTS.
consequences:
  - easier: one template set, opt-in v2, v1 remains byte-compatible.
  - harder: the transform must carry two mechanisms; validation must understand both.
```

### DECISION-3 — Fail-loud artifact validation vs. fail-soft warning vs. no validation

```
context: Opencode v2 drops bad keys silently; Codex TOML shipped 2 invalid files
         with sync rc=0 (F1, F4). Silent corruption is the dominant risk.
choice: parse/field validation runs every sync; findings are warnings in the normal
        sync log and hard errors under `--validate`/`--check` (rc != 0).
alternatives:
  - Always hard-fail the sync → rejected: one bad provider artifact would block
    syncs for the other eight providers (blast radius too wide).
  - No validation → rejected: reproduces the exact audit failure (sync rc=0, broken artifact).
consequences:
  - easier: broken artifacts surface in CI (`--validate`) and locally (warning).
  - harder: every provider needs a declared artifact contract; validator maintenance.
```

### DECISION-4 — Bootstrap sub-markers vs. merged renderer vs. provider-attribute marker

```
context: Gemini and ZCode inject into the same AGENTS.md; last writer wins and the
         Gemini roster is lost (F10 §6, D8).
choice: provider-scoped sub-markers `<!-- agent-meta:bootstrap-begin:<Provider> -->`,
        cleanup derived from the provider-bootstrap registry.
alternatives:
  - One shared marker with a `provider="…"` attribute → rejected: attribute parsing
    on a comment is brittle; two nested pairs can be matched unambiguously.
  - A single merged renderer (one writer, all providers) → rejected: couples every
    provider's bootstrap text; a provider-specific failure would affect all.
consequences:
  - easier: both rosters coexist; cleanup is precise; removes the Gemini literal.
  - harder: marker schema change must be migrated for existing AGENTS.md files.
```

### DECISION-5 — `model-format` template + `model-catalog` check vs. storing qualified IDs vs. runtime catalog fetch

```
context: KimiCode needs `kimi-code/`-qualified IDs that are also configured aliases;
         the generator emitted bare IDs (F2, F11 H6/D2).
choice: `model-format` normalizes the prefix; `model-catalog` (optional) lets the
        consistency check fail loud on an ID outside the provider's valid set.
alternatives:
  - Store only fully-qualified IDs in model-tiers → rejected: workable but leaves the
    bare-ID class unguarded; a future template edit reintroduces it.
  - Fetch the provider's live model catalog at sync time → rejected: network + non-
    stdlib + non-deterministic; violates the offline/stdlib-only constraint.
consequences:
  - easier: prefix is declared once; wrong IDs fail in CI.
  - harder: `model-catalog` must be maintained per provider (evidence-backed values).
```

### DECISION-6 — Template-neutral `.claude/...` phrasing vs. broader strip rule

```
context: four body refs to `.claude/...` survive into all 8 non-Claude providers (D5).
choice: fix the four template sites to provider-neutral phrasing; keep the existing
        strip rule as a backstop.
alternatives:
  - Extend the strip rule to all `.claude/` body refs → rejected: would remove
    legitimate mentions (e.g. audit/analysis prose) and is a blunt global filter.
consequences:
  - easier: correct instructions in every provider; no false stripping.
  - harder: template owners must avoid provider-specific paths going forward.
```

### DECISION-7 — Opencode v2 MCP as a separate `format` value vs. `surface-version` branch inside the v1 writer

```
context: v2 writes nested `mcp.servers`; v1 writes flat `mcp`. The writer currently
         dispatches only on `mcp-config.format == "opencode-json"` (mcp_provider_config.py:633).
choice: introduce the format value `opencode-json-v2` with its own writer branch;
        `surface-version` selects the value in config data, the writer stays
        name-agnostic and branches on the format string only.
alternatives:
  - Branch on `surface-version` inside the existing v1 writer → rejected: the
    writer would have to read provider-specific state, drifting toward the
    `if provider == …` anti-pattern the project forbids (CODE_CONVENTIONS).
  - Reuse `opencode-json` and detect v2 from the document/schema → rejected: no v2
    schema exists (F4 §2, §4.4) and detection is heuristic; a format value is explicit.
consequences:
  - easier: v1 byte form is provably untouched (same branch as today); two clear
    format contracts; `validate_json_document` can assert the key per format.
  - harder: one more format enum value must be registered and tested (scenario 69).
```

---

## 6. Backward compatibility and migration

### 6.1 Versioning / SemVer

- Fixes that only correct broken artifacts (Codex TOML, KimiCode model namespace, Mammouth `tools` map, Continue config validity) are **patch/minor**.
- Path changes (Copilot `.github/copilot/agents/` → `.github/agents/`; Antigravity `.gemini/agents/` → `.agents/agents/`) and the Opencode v2 surface are **breaking for the affected provider** and require a **major version bump** (`EXTRA_DONTS: no breaking changes without major version bump`, `.meta-config/project.yaml:243`).
- **Major-bump justification vs. `EXTRA_DONTS`.** The rule is absolute: the migration path below does **not** replace the required major bump. It is the prerequisite that makes the bump *usable* — without it the major bump would silently strand old-path artifacts, which is the failure mode the rule intends to prevent. The bump is repo-wide (agent-meta release version major); the path change is only *breaking for the affected provider* (Copilot, Antigravity), which is what keeps the migration surface small.
- Defaults stay stable: Opencode `surface-version: v1`, existing MCP formats unchanged, existing context files untouched unless a provider path is explicitly migrated.

### 6.2 Existing consumer projects

| Change class | Migration |
|---|---|
| Corrected artifact content (Codex/Kimi/Mammouth/Continue) | In-place on next sync; no user action. |
| Changed artifact paths (Copilot/Antigravity) | Per-key alt→neu migration sequence (6.2.1) with backup, ordered cleanup and rollback; **not** limited to the managed agent dir. |
| Bootstrap marker schema | Legacy id-less marker discarded and rebuilt per provider on first sync (§3.5); user notes outside managed markers are preserved (F10 §4). |
| Opencode v2 | Opt-in via `surface-version`; v1 projects are untouched. |

#### 6.2.1 Path-migration sequence per artifact class

The path changes touch **three distinct config keys per provider**, and two of them (Copilot context file, Copilot rules) lie **outside** `agents_dir`. Each is migrated independently; the "new path written, old path removed inside the managed agent dir" shortcut of the previous revision is insufficient (review H-2).

| Provider | Config key | Old path (source) | New path | Managed-marker? |
|---|---|---|---|---|
| Copilot | `agents_dir` | `.github/copilot/agents` (`ai-providers.yaml:317`) | `.github/agents` | yes (agent frontmatter) |
| Copilot | `context_file` | `.github/copilot/COPILOT.md` (`ai-providers.yaml:319`) | `.github/copilot-instructions.md` | yes (managed block) |
| Copilot | `rules_dir` | `.github/copilot/rules` (`ai-providers.yaml:328`) | `.github/instructions/*.instructions.md` | yes (rule frontmatter) |
| Antigravity (provider `Gemini`) | `agents_dir` | `.gemini/agents` (`ai-providers.yaml:99`) | `.agents/agents` | yes (agent frontmatter) |
| Antigravity (provider `Gemini`) | `rules_dir` | `.gemini/rules` (`ai-providers.yaml:104`) | `.agents/rules` | yes (rule frontmatter) |
| Antigravity (provider `Gemini`) | `skills_dir` | `.gemini/skills` (`ai-providers.yaml:143`) | `.agents/skills` | yes (skill frontmatter) |

Ordered sequence, applied per artifact class on the first sync after the path change:

1. **Write new:** create the artifact at the new path through the normal managed-marker writer.
2. **Verify new:** the artifact parses/validates (`artifact_validate`, §2.2) before anything is removed.
3. **Backup old:** if the old-path artifact carries an agent-meta managed marker, write a byte-exact `.sync-backup-<YYYYmmdd-HHMMSS>` sibling of the old file (existing mechanism: `generated_file_drift.py:357-388`, `rule_index.py:122-146`). A user-authored old-path file without a managed marker is **not** backup-and-deleted — it is left in place and a warning is logged (data-loss guard).
4. **Remove old:** delete only the managed old-path artifact, and only after step 2 and step 3 succeeded. Directory cleanup removes the old provider dir only when it is empty afterwards.
5. **Rollback:** restore the step-3 backup sibling (or, for a user-authored file, it was never removed) and remove the step-1 new-path artifact; net effect = pre-sync state. Documented as a manual step (no new `sync.py` subcommand is introduced by this design).

`validate_json_document`/`validate_frontmatter` findings for the new path remain fail-loud under `--validate`/`--check`; a failed verify in step 2 aborts the removal, so the old artifact survives.

### 6.3 `--check` false-positives and idempotency drift

- **ZCode + multi-all permanent `--check` rc 1** (F10 §3): cause is that the real write nets to zero while the dry-run counts the managed-update + cleanup as two pending writes. Fix: make the pending-write computation reflect the **final** content (compute the post-cleanup content once and diff it), so a net-zero sync reports clean.
- **Continue drift run1→run2** (F10 §2): the first sync writes the template with unsubstituted `{{PLACEHOLDER}}`; the second replaces it with `render_managed_block()`. Fix: the first sync must render the substituted managed block, making run1 the fixpoint.
- **ZCode AGENTS.md 3-write sequence** (F10 §2): net byte-identical from run2; after the pending-write fix it becomes run1-stable.
- Invariant to assert in tests: for every scenario, `sha256(run1) == sha256(run2)` and `sync.py --check` after a clean sync returns rc 0.

---

## 7. Test and verification strategy

### 7.1 New scenarios (`tests/scenarios/configs/`, next free IDs ≥ 64)

| ID | Providers | Feature under test | Assert |
|---|---|---|---|
| `64-codex-toml-validity` | Codex | singleton before serialization | every `.codex/agents/*.toml` parses with `tomllib` |
| `65-kimicode-model-namespace` | KimiCode | `model-format` | every emitted model matches `kimi-code/*` |
| `66-mammouth-tools-map` | Mammouth | `tools-format: map` | `tools:` is an object, not a list |
| `67-copilot-artifact-paths` | Copilot | correct paths | `.github/agents/`, `.github/instructions/`, `.github/skills/`, `.github/copilot-instructions.md` |
| `68-antigravity-discovery-paths` | Gemini | `.agents/agents/`, `.agents/rules/`, `.agents/skills/`, `.agents/mcp_config.json` (`serverUrl`) | paths + `serverUrl` present |
| `69-opencode-v2-surface` | Opencode (`surface-version: v2`) | v2 frontmatter list + `mcp.servers` + `default_agent` | no v1-only key emitted |
| `70-bootstrap-marker-convergence` | Gemini + ZCode | distinct sub-markers | both markers present, one per provider |
| `71-check-idempotency-all-providers` | all 9 | run1==run2 + `--check` rc 0 | byte-identity + clean check |
| `72-continue-config-validity` | Continue | Zod-valid config | `roles` enum valid; `config.local.yaml` has `name`/`version`; `requestOptions.headers` |

Each scenario gets an `asserts/<id>.sh` (registry convention) and a `registry.md` row.

### 7.2 New / extended pytest modules

| Module | Checks |
|---|---|
| `tests/test_artifact_contracts.py` (new) | `validate_toml` on all generated Codex artifacts; `validate_frontmatter` allow-list for Opencode; `validate_json_document` for v2 config. |
| `tests/test_model_contracts.py` (new) | `model-format` prefix; `model-tiers` precedence over preset; no raw tier token from `model-inherit-fallback`. |
| `tests/test_pipeline_notation_config.py` (new) | notation read from `delegation-syntax.yaml`; missing block fails loud; Copilot present via the registry. |
| `tests/test_bootstrap_submarkers.py` (new) | distinct sub-markers; cleanup keyed by registry; Gemini+ZCode both survive. |
| `tests/test_context_agents_md_idempotency.py` (extend) | run1==run2 for all providers (currently F10). |
| `tests/test_mcp_config.py` (extend) | `requestOptions.headers`, `http_headers`, `transport: sse`, `serverUrl` spellings. |
| `tests/test_provider_three_file_invariant.py` (extend) | `skills` + `artifact-validation` declared; `artifact-validation-reason` present and non-empty iff validation is off (AC-24); `skills: true` coupled to the `ai-providers.yaml capabilities` list and a non-null `skills_dir` (AC-25). |

### 7.3 Real-runtime checks (must run where the harness is observable)

| Check | Harness | Status today | Expected proof |
|---|---|---|---|
| Codex TOML parse | `codex mcp list` against a scratch `CODEX_HOME` | VERIFIED method (F1 §1.2) | parseable bootstrap config |
| Kimi ACP model resolution | `kimi acp` → `session/set_config_option` | VERIFIED method (F2) | generated alias resolves |
| Opencode v1 load | `opencode debug agent <name>` | VERIFIED (F3) | 58/58 load |
| Opencode v2 load | `opencode debug agents` (v2 binary, git root) | VERIFIED (F4) | 58/58 load, no silent drop |
| Claude hook cwd | `claude --settings … --debug hooks` | VERIFIED (F5) | `${CLAUDE_PROJECT_DIR}` command succeeds from foreign cwd |
| Mammouth agent load | `mammouth agent list` | VERIFIED method (F8) | no schema error |
| Continue config validity | `@continuedev/config-yaml` Zod parse | VERIFIED method (F7) | `validateConfigYaml` → 0 fatal errors |

### 7.4 Stays STATIC (no runtime available)

| Area | Why STATIC | Source |
|---|---|---|
| Antigravity discovery/hook execution | `agy` SIGILL (F6) | in-binary contract |
| Copilot context-file injection | no authenticated Copilot runtime (F9) | official docs |
| ZCode workspace auto-load | open P6 | ZCode note (capabilities) |

---

## 8. Risks and threat model

### 8.1 Risks

| Risk | Impact | Mitigation |
|---|---|---|
| v2 silent drop reintroduced after a config edit | agent disappears from the catalog without a signal | allow-list validation + `--validate` rc != 0 (§4.3) |
| Path migration deletes a user file | data loss | managed-marker-scoped writes + `.sync-backup-<ts>` siblings + user-authored-file guard (§6.2.1) |
| Major bump for path changes breaks existing consumers (SemVer-reactive pipelines) | upgrade strands old-path artifacts / consumer tooling rejects the jump | ordered alt→neu migration sequence with backup, verification-before-removal and rollback (§6.2.1); major-bump justification vs. `EXTRA_DONTS` (§6.1); affected providers named explicitly (Copilot, Antigravity) |
| `model-format` applied twice | double prefix | `model-format` is applied once at emission; consistency check catches `kimi-code/kimi-code/*` |
| Bootstrap marker migration breaks an existing AGENTS.md | lost context | managed-marker-scoped replace + user-notes preservation (F10 §4) |
| Client-side JSON schema used for v2 artifacts | false invalidity | no reliance on the official schema for v2 (§4.4) |
| Config-key naming collides with an existing key | silent override | keys added to the three-file invariant + config audit |

### 8.2 Threat model (4 questions)

1. **What are you building?** A sync-time artifact generator for 9 harnesses, extended with a per-provider declarative contract, a sync-time artifact validator, and a generated Opencode v2 surface.
2. **What could go wrong?** (a) silent-drop regressions; (b) fail-open validation that reports clean on a broken artifact; (c) a migration that deletes user content outside managed markers; (d) reintroduction of provider-name branching; (e) wrong model IDs leaking to a runtime.
3. **Mitigations?** allow-list + parse validators that fail loud in CI (a, b); managed-marker-scoped writes + backups (c); config-key-only dispatch, enforced by a grep-based provider-agnostic test (d); `model-catalog` consistency check (e).
4. **Consequences?** Higher sync-time cost and a maintained contract per provider; three areas remain runtime-unverifiable (Antigravity, Copilot, ZCode workspace auto-load) and must stay marked HYPOTHESIS/STATIC.

---

## 9. Open questions (need a spec decision)

| ID | Question | Why it is undecidable here |
|---|---|---|
| OQ-1 | Ship Antigravity discovery changes based on the in-binary STATIC contract, or gate them behind a flag until a pclmul-capable host runs `agy`? | Runtime unverifiable on the audit CPU (F6). |
| OQ-2 | Is `.continue/agents/*.md` a supported chat-agent surface, or only a `cn review` source? | Auto-load only verified in the `cn review` path (F7 H7). |
| OQ-3 | Which KimiCode aliases are stable enough for `model-catalog` (`kimi-code/kimi-for-coding` vs `k3`)? | Runtime catalog observed once; alias stability is a vendor question (F2). |
| OQ-4 | For Opencode v2, should a `mode: primary` entry agent be generated (so `default_agent` is valid), and which role? | v2 requires a primary default; all generated agents are `subagent` (F4, F3 OC1-1). |
| OQ-5 | Copilot agent extension: `.md` (VS Code tolerant) or `.agent.md` (GitHub cloud)? | Both contracts observed; path fix is orthogonal (F9). |
| OQ-6 | Should Antigravity `model` use `inherit` instead of concrete tier IDs? | Doc accepts `inherit|flash|pro`; current IDs are non-contract (F6 G-3). |
| OQ-7 | Mammouth context file: rename to `AGENTS.md`, or emit `CONTEXT.md`? | Binary reads all three; context-file topology is shared (F8 MM-4). |
| OQ-8 | Does the v1→v2 surface flip default in a future release, or stay opt-in indefinitely? | Product decision; affects SemVer track (§6.1). |
| OQ-9 | Fix the Continue template `roles` enum (CO-2) now, or track it as a separate follow-up? | `templates/configs/CONTINUE.config-template.yaml:28` uses `roles: [chat, edit, agent]`, where `agent` is outside the runtime `roles` enum (F7/N11). It is a generator defect but orthogonal to the generated-config fix; named follow-up **CO-2** (§1.3). |
