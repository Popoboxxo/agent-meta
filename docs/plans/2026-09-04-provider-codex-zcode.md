# Implementation Plan: New Providers "Codex" (OpenAI Codex CLI), "ZCode" (zcode.z.ai) & "Kimi Code" (Moonshot AI Kimi Code CLI)

| | |
|---|---|
| **Date** | 2026-09-04 (extended with Kimi Code, 2026-09-04) |
| **Status** | PLANNED (analysis + plan only — no implementation in this step) |
| **Scope** | Framework-level provider support in `scripts/sync.py` + config registries (three providers: Codex, ZCode, Kimi Code) |
| **Issues** | — (new work; references #505, #629, #630, #631, #625) |
| **Estimate** | 5.1 / 11.1 / 22.25 pd raw (opt/likely/pess) → **≈ 16.5 pd with 1.5× buffer**, 3–4 calendar weeks (1 dev) |

---

## 1. Executive Summary

This plan adds three new AI providers to the agent-meta sync framework:

- **Codex** (OpenAI Codex CLI): TOML-native harness — agents as `.codex/agents/*.toml`,
  project config via `config.toml` (+ `AGENTS.md` context, hooks since v0.150.0,
  MCP via `mcp_servers`). Closest to a "second Opencode" in shape, but with a
  TOML file format that requires a new `frontmatter-mechanism` transform
  (`codex-toml`) and a hand-rolled stdlib TOML serializer (no `tomli_w` in stdlib).
- **ZCode** (zcode.z.ai, official Z.ai/GLM-5.3 harness — NOT the community clones):
  an ADE (Agentic Development Environment) whose verified surface is small
  (global + workspace `AGENTS.md`, `~/.zcode/cli/config.json` with
  `model.main`/`model.lite`, Agent-Toolcalls with backgrounding instead of
  file-based agents). Everything else (agents dir, skills, hooks, MCP, commands)
  is **unverified** → ZCode follows a **verification-first, conservative-baseline**
  approach analogous to Mammouth (#630). Agent definitions are still
  **generated as files** (`.zcode/agents/*.md`, definition store) and consumed
  via a session-start bootstrap instruction in `AGENTS.md` — Gemini posture
  (5.8); dispatch remains native Agent-Toolcalls with backgrounding.
- **Kimi Code** (Moonshot AI Kimi Code CLI — npm `@moonshot-ai/kimi-code`, NOT the
  discontinued Python project `kimi-cli`): Markdown-first harness — global
  `~/.kimi/config.toml` (TOML + JSON), `AGENTS.md` context with nearest-wins
  subdir semantics (like Codex), built-in `coder`/`explore`/`plan` subagents with
  isolated contexts; lifecycle hooks (beta), MCP and skills/plugin surfaces are
  present but their contracts are unverified. Explorer-confirmed: Kimi agents are
  Markdown + YAML frontmatter → the DEFAULT transform path suffices
  (`model: inject` + strip keys — **no new `frontmatter-mechanism` branch, no
  serializer work**); the custom agent file format remains unverified, so Kimi
  follows a verification-first posture with an explicit Option-A/B/C transform
  decision (6.4) and conservative registry entries (6.3/6.5). `KIMI_*` env-var
  overrides are runtime-harness concerns, out of sync.py scope.

All three providers are added **exclusively via capability flags and config keys** —
no `if provider == "..."` branches (provider-agnostic policy). The critical
path remains P2 (Codex transform + TOML serializer); **Kimi adds no
critical-path work**. External verification (P6) starts immediately and in
parallel because its outcome can invalidate P2/P3 design decisions — for Kimi
Code especially (V10–V16).

---

## 2. Scope & Non-Goals

### In scope (this document)

- Analysis of all registration/config/code touchpoints for the three providers.
- Target design: capability matrix, config sketches, file checklists, transform
  design, delegation syntax entries.
- Phased implementation plan with effort, parallelization, migration order and
  test plan. The later implementation itself (registry entries, TOML
  serializer, transform, isolation + MCP, templates + version bumps, tests,
  docs) is scoped here but executed in the phases P1–P6 (§8).

### Non-Goals

- **No implementation in this step** — analysis + plan only. No `sync.py` runs,
  no commits, no branch work in this phase (implementation happens later on a
  `feat/` branch, see §12).
- No changes to existing providers' behavior (Claude, Opencode, Gemini,
  Continue, Mammouth, Copilot).
- No refactor of the existing hand-rolled TOML string builders
  (`_md_to_toml()` in `commands.py:60-74`, `_build_gemini_toml_rule()` in
  `isolation.py:277-302`) beyond optionally re-routing them to the new generic
  serializer — that is a separate cleanup, tracked as a follow-up candidate.
- No new placeholders without registration in the CLAUDE.md variables table
  (see §12).
- Cross-project re-sync propagation of the new providers into consumer repos
  is out of scope and **not** part of the estimate (see §9).
- ZCode desktop-app-only features (Settings → General → Memory UI etc.) —
  only what sync.py can generate/configure is targeted.
- Kimi Code `KIMI_*` env-var runtime handling (`KIMI_API_KEY`/`KIMI_BASE_URL`/
  `KIMI_MODEL`/`KIMI_MAX_TOKENS`) and other runtime-harness behavior — doc
  note only (6.6), no sync.py work.
- Kimi Code plugin marketplace and app-only features — only what sync.py can
  generate/configure is targeted; the discontinued Python project
  `MoonshotAI/kimi-cli` is not a target (wrong-target note, 6.1).

---

## 3. Current Architecture Summary

Provider support is data-driven; code contains almost no provider literals.
Key verified touchpoints (spot-checked in repo, 2026-09-04). This inventory
was re-confirmed for the Kimi Code addition (explorer spot-check, 2026-09-04):
the checklist below applies unchanged for Kimi Code; its Kimi-specific deltas
are listed in 6.2.

**Registration core (YAML registries — mandatory set):**

| Registry | Purpose |
|---|---|
| `config/ai-providers.yaml` | Per-provider block: `agents_dir`, `agent_ext`, `context_file`, `context_template`, `capabilities` list, `isolation-dirs`, `gitignore_entries`, `skills_dir`/`snippets_dir`/`pending_tasks_file`/`extension_dir`, `orchestrator_hint`, `bash_tool_name`, `model-tiers`/`model-aliases`, `agent-transform`; `hook_protocol` ONLY when the hook contract is verified (Mammouth precedent, #630). |
| `.meta-config/project.yaml` | Activation via `ai-providers: [Name]`. |
| `config/provider-capabilities.yaml` | Orchestration matrix: `subagent_dispatch`, `parallel_execution`, `file_based_agents`, `text_mentions`, `hooks`, `native_agent_tools`, `structured_handoff`, `handoff_format` (`json`\|`yaml_text_block`), `handoff_envelope_support`, `bootstrap_required`, `special_notes`. |
| `config/provider-bootstrap.yaml` | `mechanism` (`file-based`\|`api-based`\|`config-based`), `action` (`none`\|`inject-bootstrap-instructions`\|`update-config`). |
| `config/delegation-syntax.yaml` | `delegate`/`fanout`/`parallel_group`/`fallback`/`bootstrap`/`tool_preamble`/`auto_parallel`/`parallel_pattern`/`handoff`. |
| `config/provider-tools.yaml` | Tool whitelist, `<provider>-silent`, `terminal_tool` map. |
| `templates/configs/<PROVIDER>.project-template.md` | Context template; `AGENTS.project-template.md` is already shared by Gemini, Opencode, Mammouth (`ai-providers.yaml:185,358,253`). |

**Python touchpoints:**

- `scripts/lib/pipelines.py:16` — `KNOWN_PROVIDERS = ("Claude", "Opencode", "Gemini", "Continue", "Mammouth")`; validated at `pipelines.py:196-201`, cemented by `tests/test_pipelines.py:12`.
- Remaining provider literals (only relevant if the corresponding feature is needed): `commands.py` ~124 (4-way if/elif — native slash-commands only), `context.py:760` (`provider == "Continue"`), `skill_channel.py:35`, `rules.py:40/256`, `viz.py:751` (Opencode literal).
- `scripts/lib/context.py:281` — `_has_capability()`; the reference pattern for capability gating. `scripts/lib/providers.py:168` — `SUPPORTED_HOOK_PROTOCOLS = {"claude-code-json"}`; `provider_hooks_supported()` (`providers.py:171-180`) gates hook mirroring on `hook_protocol`.
- `scripts/lib/provider_transform.py:325` — `transform_agent_content_for_provider()`; `_apply_agent_transform()` (`provider_transform.py:150-323`) consumes the data-driven `agent-transform:` block (#629). Spec keys: `model` (`inject`\|`native`\|`skip`), `model-note-flat`, `model-inherit-fallback`, `inject-memory`, `inject-permission-mode`, `extra-fields`, `tools` (`skip`\|`keep`\|`filter`\|`remove`), `strip-fields`, `strip-claude-lines`, `body-note`, `body-sanitize-hr`, `frontmatter-mechanism`. Exactly one `frontmatter-mechanism` value exists today (`opencode-native`, `ai-providers.yaml:233`), dispatched via string compare at `provider_transform.py:218`. Missing `agent-transform` block → warning (`provider_transform.py:361-368`); `strip_fields` (#505) via `provider-options.frontmatter-strip-fields` or `frontmatter_strip_fields`.
- MCP: `scripts/lib/mcp_provider_config.py:384` — `_write_provider_config()` dispatch on `mcp-config: {committed-file, secrets-file, format}`; formats today: `claude-settings`, `gemini-settings`, `opencode-json`, `continue-yaml`; unknown format → warn + skip.
- Model injection: single `model:` frontmatter field via `inject_model_field()` (`frontmatter.py:344-373`); resolution `resolve_model()` (`roles.py:106-259`): `model-override-all[provider]` → `model-inherit-main-chat[provider]` → `model-overrides.<provider>[role]` → `role-defaults.yaml` → `tier-presets.yaml` (tiers + optional `providers.<name>.tiers`, `:223-239`) → provider-tier-overrides → `_resolve_tier_to_model()` (nano/fast/balanced/powerful/max/ultra; legacy aliases haiku/sonnet/opus). **Multi-model (`model.main` + `model.lite`) is not supported anywhere.**
- Isolation: `_ISOLATION_MECHANISM_HANDLERS` (`isolation.py:389-394`) — `claude-settings-deny`, `opencode-permissions`, `gemini-toml-policy`, `continue-soft-rule`; missing key → skip with log (`isolation.py:79-89`); active only with ≥2 providers and `provider-isolation` not disabled.
- Validation: `sync.py --validate` (`sync.py:1140-1209`); registry completeness check (#625) is warn-only (`sync.py:1178-1180`, `config_audit.py:511-522`) — minimal runnable set = `ai-providers.yaml` entry + `project.yaml` activation; deployed-hook drift check at `sync.py:1189-1193`.

**TOML precedent:** Gemini `commands_ext: .toml` uses the hand-rolled string
serializer `_md_to_toml()` (`commands.py:60-74`); `_build_gemini_toml_rule()`
(`isolation.py:277-302`). **No generic TOML serializer exists in `scripts/`**
and the stdlib has no `tomli_w` → a hand-rolled writer is required.

**Add-provider guidance:** the add-provider guidance identifies the MCP format
as a legitimate touchpoint and treats hooks as "no adapter concept, own
follow-up"; the `/add-provider` slash command covers only *activation* of a
known provider, not the *build-out* (see `docs/plans/archive/audit-2026-09-system-concept.md`).

---

## 4. Target Design — Codex (OpenAI Codex CLI)

### 4.1 Verified external surface (state 2026-09)

| Surface | Fact |
|---|---|
| Config | `~/.codex/config.toml` + project-level `.codex/config.toml` (TOML), profiles, "closest to cwd wins" |
| Context | `AGENTS.md` standard — repo root + subdir overrides, nearest wins; global `~/.codex/AGENTS.md` |
| Subagents | TOML files in `.codex/agents/*.toml` (fields: `name`, `description`, `sandbox_mode`, `model`, `instructions`) — GA since 2026-03; internal defaults `explorer`/`worker`/`default`; `multi_agent` feature flag |
| Hooks | 12 events since v0.150.0 (PreToolUse, PermissionRequest, PostToolUse, PreCompact, PostCompact, SessionStart, SessionEnd, UserPromptSubmit, SubagentStart, SubagentStop, Stop, Interrupt) via `hooks.json` or inline TOML — event names identical to Claude Code, **payload contract UNVERIFIED** (treat like Mammouth #630) |
| Skills | `.agents/skills/` (user → repo → directory), `SKILL.md` |
| Rules | `rules/` (`.rules` files) |
| MCP | `mcp_servers` section in `config.toml` (STDIO + HTTP) |
| Models | GPT-5.x family (`gpt-5.6` sol/terra/luna, `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.3-codex-spark`) |
| Settings | **No** `settings.json` equivalents — everything in `config.toml` |

### 4.2 Proposed capability matrix (`config/provider-capabilities.yaml`)

```yaml
  Codex:
    subagent_dispatch: true
    parallel_execution: true        # multi_agent feature flag (verify enablement)
    file_based_agents: true         # .codex/agents/*.toml auto-loaded (GA 2026-03)
    text_mentions: false
    hooks: false                    # true only AFTER hook payload contract verified
    native_agent_tools: []          # TOML agents, no dispatch tool surface known
    structured_handoff: true
    handoff_format: "json"
    handoff_envelope_support: true  # conservative start: revisit during P6
    description: "TOML-native agents (.codex/agents/*.toml), AGENTS.md context, hooks since v0.150.0 (contract unverified)."
    special_notes:
      - "Agents are TOML files with name/description/sandbox_mode/model/instructions."
      - "Hooks: 12 events, names match Claude Code — payload contract unverified (#630 pattern)."
      - "No settings.json — project config lives in .codex/config.toml."
```

Conservative-baseline comment (Mammouth style, `provider-capabilities.yaml:77-86`)
explaining every `false`/restrained value with its verification dependency.

### 4.3 Proposed `ai-providers.yaml` block (sketch)

```yaml
  Codex:
    agents_dir: .codex/agents
    agent_ext: .toml
    context_file: AGENTS.md
    context_template: templates/configs/AGENTS.project-template.md   # see 4.6
    has_rules: true
    rules_dir: rules            # .rules files; naming check in P6
    has_hooks: true
    hooks_dir: .codex/hooks     # path reserved, NOT mirrored (no hook_protocol)
    has_commands: false         # slash-command surface unverified — P6 item
    has_settings: false         # no settings.json — everything in config.toml
    capabilities: [agents, rules, hooks, snippets, skills, context-managed-block]
    skills_dir: .agents/skills  # Codex reads user → repo → directory
    snippets_dir: .codex/snippets
    pending_tasks_file: .codex/pending-tasks.md
    extension_dir: .codex/3-project
    orchestrator_hint: "- **In Codex:** Use the orchestrator agent."
    bash_tool_name: TBD         # open point, see §11
    isolation-dirs: [.codex/, AGENTS.md]
    gitignore_entries: [.codex/pending-tasks.md]
    mcp-config:
      committed-file: .codex/config.toml
      secrets-file: .codex/mcp.local.toml    # verify merge semantics in P6
      format: codex-toml-mcp
    model-tiers: {nano: gpt-5.4-mini, fast: gpt-5.4, balanced: gpt-5.3-codex-spark,
                  powerful: gpt-5.5, max: gpt-5.6}
    model-aliases: {sol: gpt-5.6-sol, terra: gpt-5.6-terra, luna: gpt-5.6-luna}
    agent-transform:
      frontmatter-mechanism: codex-toml
      model: inject
      extra-fields:            # per-agent sandbox — see 4.7 (open design point)
        sandbox_mode: workspace-write
      tools: keep
      strip-fields: [memory, temperature, top_p, top_k, stop_sequences, max_output_tokens]
      strip-claude-lines: true
```

### 4.4 File checklist (Codex)

**New files**

| File | Content |
|---|---|
| `scripts/lib/toml_writer.py` | Generic stdlib TOML serializer (shared work, §7) |
| `templates/configs/CODEX.agent-template.toml` | Reference shape of a generated `.codex/agents/*.toml` (golden-file source) |
| `docs/providers/codex.md` | Provider doc (P6) |

**Modified files**

| File | Change |
|---|---|
| `config/ai-providers.yaml` / `config/provider-capabilities.yaml` | `Codex:` block per 4.3 / row per 4.2 |
| `config/provider-bootstrap.yaml` | `Codex:` entry — `mechanism: file-based`, `action: none` (agents auto-loaded; verify in P6, else `inject-bootstrap-instructions`) |
| `config/delegation-syntax.yaml` / `config/provider-tools.yaml` | `Codex:` entry per 4.8 / tool whitelist + `Codex-silent` + `terminal_tool` (pending `bash_tool_name` verification) |
| `scripts/lib/pipelines.py` | `KNOWN_PROVIDERS` += `"Codex"` |
| `scripts/lib/provider_transform.py` | ONE new `frontmatter-mechanism` dispatch branch: `codex-toml` → TOML output (string compare, no if-provider chain) |
| `scripts/lib/mcp_provider_config.py` | ONE new format branch: `codex-toml-mcp` → `mcp_servers` array-of-tables |
| `scripts/lib/isolation.py` | possibly ONE new isolation-mechanism value (see 4.7) |
| `templates/configs/AGENTS.project-template.md` | only if a Codex-specific variant is needed (4.6) |
| `CLAUDE.md` | only if new placeholders are introduced (avoid) |

### 4.5 Transform design — `frontmatter-mechanism: codex-toml`

- New dispatch branch at `provider_transform.py:218`-style string compare:
  `codex-toml` → build TOML agent file from the sync-intermediate
  (name, description, model, instructions body, optional `sandbox_mode`).
- Mapping of existing transform keys onto Codex:
  - `model: inject` → `model = "<resolved-model>"` (single-model resolution
    via `resolve_model()`, `roles.py:106-259` — Codex needs no new model logic).
  - `extra-fields` → static extra TOML keys (e.g. `sandbox_mode`).
  - `tools` → filter/keep mapping to whatever the Codex agent TOML supports
    (verify exact tool-field name in P6).
  - `strip-claude-lines` / `strip-fields` → unchanged semantics (reuse #505
    mechanism).
- Output via the shared TOML writer (§7). `instructions` carries the Markdown
  body — escaping/`'''`-multi-line strings must round-trip through
  golden-file tests (P2, see §10).

### 4.6 Context strategy

Codex uses the `AGENTS.md` standard: repo root + subdir overrides (nearest
wins) + global `~/.codex/AGENTS.md`. **First choice: reuse the shared
`templates/configs/AGENTS.project-template.md`** (already serves Gemini,
Opencode, Mammouth) — zero template duplication. **Open point:** Codex's
subdir-override semantics can interact with agent-meta's managed blocks when
target projects ship their own subdirectory `AGENTS.md` files. Decide in
P1/P6 whether a dedicated `CODEX.project-template.md` variant (e.g. an
explicit "subdir overrides" note) is needed. Default: reuse the shared
template; a dedicated variant only on a concrete, audited conflict.

### 4.7 Hooks strategy (#630 pattern) and isolation

**Hooks** — follow the Mammouth precedent exactly (`ai-providers.yaml:354-369`,
`provider-capabilities.yaml:77-86`): `has_hooks: true` + `hooks_dir: .codex/hooks`
reserves paths (no collision with Claude's `.claude/hooks`, satisfies
path-collision tests) but **no `hook_protocol` key** → `provider_hooks_supported()`
(`providers.py:171-180`) skips hook mirroring until the Codex payload contract
is verified (event *names* match Claude Code; stdin JSON / exit-code-2
semantics unverified). Once verified: config-only addition of
`hook_protocol: claude-code-json` (or a new protocol value). The deployed-hook
drift check (`sync.py:1189-1193`) applies automatically.

**Isolation (open design point):** Codex supports per-agent `sandbox_mode`
(and `approval_policy`) directly in the agent TOML. Two options:
1. **`agent-transform.extra-fields`** (chosen default, 4.3): static per-agent
   fields — no new isolation machinery, no new mechanism value.
2. **New `isolation-mechanism` value** (e.g. `codex-sandbox-toml`) in
   `_ISOLATION_MECHANISM_HANDLERS` (`isolation.py:389-394`) only if
   provider-level *policy* (deny tools globally, analogous to
   `opencode-permissions`) is required.

Decision rule: ship option 1 in P2; add option 2 only on demand. Cross-provider
isolation triggers only with ≥2 active providers (`isolation.py:79-89`), so
Codex-only setups are unaffected either way.

### 4.8 Delegation syntax + bootstrap

- `config/delegation-syntax.yaml`: add `Codex` entry with the standard
  `delegate`/`fallback`/`handoff` keys. Conservative start mirrors Mammouth
  (text-based delegation via the shared handoff format), since
  `native_agent_tools` is empty; upgrade path if a dispatch tool surface is
  verified.
- `config/provider-bootstrap.yaml`: `mechanism: file-based`, `action: none`
  — `.codex/agents/*.toml` files are auto-loaded (GA); if P6 finds a
  registration/enablement step (e.g. `multi_agent` feature flag), switch to
  `inject-bootstrap-instructions` and document it in `special_notes`.

---

## 5. Target Design — ZCode (zcode.z.ai)

### 5.1 Verified external surface (state 2026-09)

| Surface | Fact |
|---|---|
| Harness | ADE (Agentic Development Environment), Desktop + CLI, official harness for GLM-5.3 |
| Context | `AGENTS.md` — ONLY user-global + workspace level; **no** directory-level merging, no `@import`, no child dirs; `CLAUDE.md` only as one-time migration |
| CLI config | `~/.zcode/cli/config.json` (`model.main`, `model.lite` — lite used for subagent work); project override: `zcode.json` or `.zcode/config.json` |
| Subagents | Agent-Toolcalls with backgrounding (`subagents.autoBackgroundMs`, `/tasks`, `run_in_background`) — **NOT file-based agent dirs** |
| Memory | built-in (Settings → General → Memory) |
| Everything else | agents dir, skills, hooks, MCP, commands: **UNVERIFIED** |

**Explicitly out of scope (wrong targets):** the community clones
simonyos/Z-CODE, zmccyy/ZCode--CLI--tool, kodyberry23/zcode.

### 5.2 Proposed capability matrix

```yaml
  ZCode:
    subagent_dispatch: true          # native Agent-Toolcalls (verified)
    parallel_execution: false        # backgrounding ≠ parallel subagents — verify
    file_based_agents: false         # harness does NOT auto-load agent dirs (verified);
                                     # definitions still generated as files — consumed
                                     # via bootstrap injection (Gemini posture, 5.8)
    text_mentions: false
    hooks: false                     # surface unverified
    native_agent_tools: []           # exact dispatch tool name unverified — V17
    structured_handoff: true
    handoff_format: "yaml_text_block"  # conservative until json support verified
    handoff_envelope_support: false
    bootstrap_required: true         # roster registration via AGENTS.md bootstrap
                                     # instruction (5.8 layer 2 — Gemini posture)
    description: "Official Z.ai GLM-5.3 harness (ADE). Agent-Toolcalls with backgrounding, workspace-level AGENTS.md only. Agent definitions generated as files (definition store), consumed via bootstrap injection (Gemini posture, 5.8). Surface partially unverified — verification-first."
    special_notes:
      - "AGENTS.md: user-global + workspace only — no child-dir merging, no @import."
      - "Agent definitions ARE generated as files (.zcode/agents/*.md, definition store, 5.8) — consumption via bootstrap injection, not harness auto-load (Gemini posture)."
      - "model.main for main chat, model.lite for subagent work (multi-model, see 5.4)."
      - "Verification-first: dispatch tool name (V17), skills/hooks/MCP/commands surface pending (P6)."
```

### 5.3 Proposed `ai-providers.yaml` block (sketch, minimal-first)

```yaml
  ZCode:
    agents_dir: .zcode/agents        # definition store — files ARE generated by sync.py, consumed via bootstrap, NOT auto-loaded (5.8)
    agent_ext: .md
    context_file: AGENTS.md
    context_template: templates/configs/AGENTS.project-template.md  # verify fit — P6
    has_rules: false                 # unverified
    has_hooks: false                 # unverified — no path reservation yet
    has_commands: false              # unverified
    has_settings: true
    settings_file: .zcode/config.json   # project override (alt: zcode.json — P6)
    settings_template: templates/configs/ZCODE.settings-template.json
    capabilities: [agents, settings, context-managed-block]  # agents = definition-store generation (5.8); rest grows with verification
    isolation-dirs: [.zcode/, AGENTS.md]
    bash_tool_name: TBD              # P6 verification
    gitignore_entries: [.zcode/pending-tasks.md]
    mcp-config: {}                   # empty until MCP surface verified (warn+skip today)
    skills_dir: .zcode/skills        # reserved, capability-gated
    snippets_dir: .zcode/snippets
    pending_tasks_file: .zcode/pending-tasks.md
    extension_dir: .zcode/3-project
    orchestrator_hint: "- **In ZCode:** Use the orchestrator agent."
    model-tiers: {nano: <zcode-lite-model>, fast: <zcode-lite-model>,
                  balanced: <zcode-main-model>, powerful: <zcode-main-model>, max: <zcode-main-model>}
    agent-transform:                 # required (warning otherwise) — minimal strip set
      model: skip                    # models live in config.json, not in agent files
      tools: skip
      strip-claude-lines: true
```

Key structural decision: the two-flag suppression (`file_based_agents: false`
in the orchestration matrix + `agents` capability OFF the `capabilities`
list) is only the correct posture when the harness offers **neither**
auto-load **nor** a bootstrap consumption path. ZCode explicitly chooses the
**bootstrap posture** (5.8): `file_based_agents: false` stays (verified —
nothing auto-loads), but the `agents` capability is ON — sync.py writes the
`.zcode/agents/*.md` definition store and the generated `AGENTS.md` managed
block consumes it via the bootstrap instruction. `agents_dir` therefore
points at real generated output, not a reserved path.

**File checklist (ZCode):** *New:* `templates/configs/ZCODE.settings-template.json`
(`model.main`/`model.lite` from tier resolution), `docs/providers/zcode.md` (P6).
*Modified:* the five registries (`ai-providers.yaml`, `provider-capabilities.yaml`,
`provider-bootstrap.yaml`, `delegation-syntax.yaml`, `provider-tools.yaml`),
`scripts/lib/pipelines.py` (`KNOWN_PROVIDERS`), `scripts/lib/provider_transform.py`
(minimal transform — no new dispatch branch needed; ZCode reuses existing
`strip-*` keys). No serializer, MCP or isolation changes for ZCode in the
initial pass (verification-first, 5.6).

### 5.4 Multi-model: `model.main` + `model.lite` (open design point)

The model resolution chain (`roles.py:106-259`) resolves **one** model per
role; ZCode wants two (`model.main` for main chat, `model.lite` for subagent
work). Options:

1. **Map onto existing tiers (chosen default):** `model.lite` →
   `nano`/`fast` tier, `model.main` → `balanced`/`powerful`/`max`. The
   `settings_template` for `.zcode/config.json` writes both keys from the tier
   resolution. No resolution-engine change.
2. **New capability flag** (e.g. `dual-model: {main: tier, lite: tier}`) if
   tier mapping proves too coarse or if per-role lite/main selection is
   required later. This is an engine change — defer until P6 shows the need.

Documented in `special_notes`; revisit at P2/P6 boundary.

### 5.5 Context strategy

- Workspace-level `AGENTS.md` only. The shared
  `AGENTS.project-template.md` fits the managed-block approach; the one-way
  `CLAUDE.md` migration is a ZCode-internal feature (no sync.py work).
- **Do not** model ZCode's no-subdir-merging semantics anywhere — the template
  must not instruct agents to create child `AGENTS.md` files (check template
  wording in P4).
- `settings_template` carries `model.main`/`model.lite` + any verified keys.

### 5.6 Verification-first posture

Everything beyond context/config/subagents is unverified. ZCode therefore gets
**no** hooks/skills/commands/MCP wiring in the initial implementation — the
capability list grows only when P6 verification produces facts (same
discipline as the Mammouth conservative baseline, #630). All concrete
verification tasks are listed in §11.

### 5.7 Delegation syntax + bootstrap

- `delegation-syntax.yaml`: `ZCode` entry with conservative values
  (`handoff_format: yaml_text_block`, no `auto_parallel`) — native
  Agent-Toolcalls exist, but the exact dispatch tool name (V17) and envelope
  support are unverified.
- `provider-bootstrap.yaml`: **chosen posture** — `ZCode:` entry with
  `action: inject-bootstrap-instructions` (5.8 layer 2, Gemini posture): the
  generated `AGENTS.md` managed block carries the session-start bootstrap
  instruction (read `.zcode/agents/*.md`, use as subagent roster —
  registration in the prompt, not by directory scanning). `mechanism:` leans
  `config-based` (prompt/context-driven registration; no harness scan, no
  verified registration API) — final value confirmed in P6; the chosen
  `action` is not reopened without a documented reason.

### 5.8 Agent definitions without file-based inventory (ZCode bootstrap pattern)

ZCode has verified native Agent-Toolcalls but **no file-based agent
inventory**: the harness does not auto-load an agents directory. ZCode
therefore adopts the **Gemini posture** — `config/provider-capabilities.yaml`
Gemini row: `file_based_agents: false` + `bootstrap_required: true`;
`config/provider-bootstrap.yaml` Gemini entry: `mechanism: api-based`,
`action: inject-bootstrap-instructions` (`.gemini/agents/*.md` are written by
sync.py, never auto-loaded; runtime registration via define_subagent at
session start). ZCode mirrors this posture with its verified surfaces
(AGENTS.md + file reads). Three layers:

1. **Definitions layer — sync.py writes `.zcode/agents/*.md` (definition
   store).** Agent-file generation is **re-activated** for ZCode — the §5.3
   two-flag suppression was aimed at the harness auto-load path, not at
   definition generation. sync.py generates the standard Markdown +
   frontmatter agent files through the default transform path (5.3 sketch:
   `model: skip`, `tools: skip`, `strip-claude-lines: true` — models stay in
   `config.json`, 5.4). The generated directory is the **single source of
   truth** for the roster: versioned in git, platform-shared (same generated
   agent set as every other provider, modulo the provider transform).

2. **Bootstrap layer — `provider-bootstrap.yaml` →
   `ZCode: action: inject-bootstrap-instructions`.** The generated
   `AGENTS.md` managed block carries a session-start bootstrap instruction
   (analogous to the Gemini bootstrap end block; the registry entry shape
   mirrors the Gemini entry — `instructions:` block or a dedicated
   `template_file`): the main agent reads all `.zcode/agents/*.md` at
   session start and uses them as its subagent roster — **registration
   happens in the prompt at runtime** instead of directory scanning. This is
   verified-safe for ZCode: it reads `AGENTS.md` (verified) and can read
   files (verified). Roster detail depth depends on V18 (inline personas vs.
   compact roster fallback, documented below).

3. **Dispatch layer — `delegation-syntax.yaml` → `ZCode` entry.**
   Orchestrator delegation runs as the task text of the native agent toolcall
   (persona + A2A envelope, `handoff_format: yaml_text_block` per 5.7);
   backgrounding via `subagents.autoBackgroundMs` turns the call into a
   `/tasks` job. The exact dispatch tool name is V17.

**Fallback (V18):** if ZCode's native dispatch does not accept inline
personas per call, the bootstrap block carries a **compact roster** (name +
description only) directly in the `AGENTS.md` managed block instead of file
references; full personas stay in the definition store and are read on
demand at dispatch time.

**Provider-agnostic note:** the bootstrap pattern is expressed purely via
existing config keys (`bootstrap_required`, `file_based_agents`,
`provider-bootstrap.yaml` `action`/`mechanism`, `agents` capability) — no
provider-name branches; ZCode differs from Gemini only in registry values
and the absence of a define_subagent API (prompt-level registration).

---

## 6. Target Design — Kimi Code (Moonshot AI Kimi Code CLI)

### 6.1 Verified external surface (state 2026-09)

| Surface | Fact |
|---|---|
| Harness | MoonshotAI/kimi-code (TypeScript, npm `@moonshot-ai/kimi-code`) — official successor. **Wrong target:** the discontinued Python project MoonshotAI/kimi-cli — its docs remain useful as reference only (its migration automates config/sessions) |
| Config | global `~/.kimi/config.toml` (TOML + JSON accepted); project-level config file (name/path **UNVERIFIED**, V15); precedence: project config > global > startup params (highest) |
| Context | `AGENTS.md` standard — project root + subdirs auto-loaded, nearest-wins semantics (like Codex); global `~/.kimi/AGENTS.md`; `/init` generates `AGENTS.md` |
| Subagents | built-in `coder`/`explore`/`plan` with isolated contexts; the kimi-cli predecessor used YAML agent specs (`version: 1`, `agent.extend`, `subagents` map with `path`+`description`) — successor custom agent file format **UNVERIFIED** (V10) |
| Hooks | lifecycle hooks present (beta docs) — event names/payload contract **UNVERIFIED** → #630 pattern (V11) |
| MCP | yes — `/mcp-config` (conversational), config file, ad-hoc JSON (`mcpServers` format); stdio + http; config file location/format **UNVERIFIED** (V13) |
| Skills/plugins | Agent Skills + plugin marketplace present — directory layout **UNVERIFIED** (V12) |
| Models | Kimi K2.x — `kimi-k2.6`, `kimi-k2.7-code` (opencode-go catalog); single-model resolution suffices (**no** `model.main`/`model.lite` dual-model like ZCode) |
| Env overrides | `KIMI_API_KEY` / `KIMI_BASE_URL` / `KIMI_MODEL` / `KIMI_MAX_TOKENS` override config — runtime-harness concern, **out of sync.py scope** (doc note only, 6.6) |

**Naming note:** `kimi`/`kimi-code` already exist as Opencode **model aliases**
(`ai-providers.yaml:245-246`). The new provider's registry key is therefore
`KimiCode` (single CamelCase token, consistent with the existing
`Claude`/`Opencode`/… key style and unambiguous against those aliases);
generated paths stay lowercase `.kimi/`.

### 6.2 Explorer confirmation — P1 inventory applicability

The §3 inventory was re-confirmed for Kimi Code (explorer spot-check,
2026-09-04); the same checklist mechanism applies as for Codex/ZCode.

**Carries over unchanged (same P1 checklist):**

- the five registries: `ai-providers.yaml`, `provider-capabilities.yaml`,
  `provider-bootstrap.yaml`, `delegation-syntax.yaml`, `provider-tools.yaml`;
- `KNOWN_PROVIDERS` (`pipelines.py:16`) + `tests/test_pipelines.py:12`
  (same-commit rule, 7.2);
- capability gating via `_has_capability()` (`context.py:281`) and validation
  via `sync.py --validate`.

**Structural simplification vs. Codex:** Kimi agents are **Markdown + YAML
frontmatter** → the DEFAULT transform path applies; **no new
`frontmatter-mechanism` dispatch branch is needed** — Codex's P2 critical path
(TOML serializer) does not apply to Kimi.

**New touchpoints (Kimi-specific):**

| Touchpoint | Note |
|---|---|
| Possible second `toml_writer` consumer | only if MCP/config lives in TOML — the unknown-format warn+skip at `mcp_provider_config.py:384` makes a missing format value safe by default (6.7) |
| Settings-template decision | the `settings_file`/`settings_template` pattern exists (e.g. `ai-providers.yaml:40-41`); decision deferred to P3 (6.7) |
| `KIMI_*` env-var overrides | runtime-harness concern → out of sync.py scope; doc note in `docs/providers/kimi-code.md` only |
| `.kimi/` paths | no collision with existing provider dirs (path-collision test still extended in P5) |
| Hardcoded provider lists in tests | 5 files: `tests/test_pipelines.py:12`, `tests/test_context_compact_mode.py:526` (`_ALL_PROVIDERS`), `tests/test_rules_skill_channel.py:69`, `tests/test_secrets_and_isolation.py:52`, `tests/test_provider_context_filename.py:20-28` (P5) |
| Bootstrap | **UNVERIFIED** → finalize the `provider-bootstrap.yaml` entry only after P6 verification (ZCode discipline, 5.7 / 6.8) |
| Registry-key naming | `KimiCode` key to stay unambiguous vs. the existing Opencode model aliases (6.1) |

### 6.3 Proposed capability matrix (`config/provider-capabilities.yaml`)

```yaml
  KimiCode:
    subagent_dispatch: true          # built-in coder/explore/plan agents (verified)
    parallel_execution: false        # isolated contexts, no verified parallelism contract
    file_based_agents: false         # custom agent file format UNVERIFIED (V10) — Option C posture until verified (6.4)
    text_mentions: false
    hooks: false                     # hooks present (beta) but contract unverified — #630 pattern
    native_agent_tools: []           # dispatch tool surface unverified — V16
    structured_handoff: true
    handoff_format: "yaml_text_block"  # conservative until json support verified
    handoff_envelope_support: false
    description: "Moonshot AI Kimi Code CLI. AGENTS.md context (nearest-wins subdirs, like Codex), global ~/.kimi/config.toml, built-in coder/explore/plan subagents. Custom agent format, hooks contract, MCP config location unverified — verification-first."
    special_notes:
      - "AGENTS.md: project root + subdirs auto-loaded (nearest-wins); global ~/.kimi/AGENTS.md; /init generates it."
      - "Precedence: project config > global config > startup params (highest)."
      - "KIMI_* env-var overrides are runtime-harness concerns — out of sync.py scope."
      - "Registry key KimiCode stays unambiguous vs. existing Opencode model aliases kimi/kimi-code (ai-providers.yaml:245-246)."
      - "Verification-first: custom agent format (V10), hooks (V11), skills layout (V12), MCP location (V13) pending."
```

Conservative-baseline comment (Mammouth style) explaining every `false`/restrained
value with its verification dependency.

### 6.4 Agent-transform mechanism — design decision with options

The successor's custom agent file format is UNVERIFIED (V10); the
explorer-confirmed default assumption is Markdown + YAML frontmatter. Three
options:

- **Option A — default transform path (chosen default, explorer-backed):**
  agents are Markdown + YAML frontmatter → reuse the DEFAULT transform path:
  `agent-transform` with `model: inject` + `strip-fields`/`strip-claude-lines`
  (#505/#629 mechanisms). **No new `frontmatter-mechanism` value, no dispatch
  branch, no serializer work** — golden files only (P2).
- **Option B — `kimi-yaml-spec`:** if the successor proves YAML-spec-based
  (kimi-cli heritage: `version: 1`, `agent.extend`, `subagents` map), add ONE
  new `frontmatter-mechanism` value `kimi-yaml-spec`, dispatched by string
  compare at the `provider_transform.py:218` site — same pattern as
  `opencode-native`/`codex-toml` (provider-agnostic, no if-provider chain).
- **Option C — suppression fallback (ZCode-style):** if `file_based_agents`
  stays unverified through P6, suppress agent-file generation
  provider-agnostically: `file_based_agents: false` (already the 6.3 value),
  `agents` capability OFF the `capabilities` list, `agents_dir: .kimi/agents`
  reserved so a later verification can flip one flag instead of adding a block.

**Decision rule:** P1/P2 build the cheap Option-A posture (transform config +
golden files — no critical-path work); P6 verification (V10) decides the final
posture before activation (§9): V10 confirms Markdown → stay on A and flip
`file_based_agents: true` + `agents` capability on; V10 confirms YAML-spec →
Option B; V10 inconclusive → Option C stays (zero rework, paths reserved).

### 6.5 Proposed `ai-providers.yaml` block (sketch, conservative-first)

```yaml
  KimiCode:
    agents_dir: .kimi/agents         # reserved — generation posture per 6.4 decision
    agent_ext: .md                   # Option A posture (Markdown + YAML frontmatter)
    context_file: AGENTS.md
    context_template: templates/configs/AGENTS.project-template.md   # see 6.6
    has_rules: false                 # unverified
    has_hooks: true
    hooks_dir: .kimi/hooks           # path reservation only — NO hook_protocol (#630 pattern)
    has_commands: false              # unverified
    has_settings: true               # capability `settings` added only after V15 (6.7)
    settings_file: .kimi/config.toml # project-level config name/path UNVERIFIED (V15)
    settings_template: templates/configs/KIMICODE.settings-template.toml   # P3 decision (6.7)
    capabilities: [context-managed-block]   # deliberately minimal — grows with verification
    skills_dir: .kimi/skills         # reserved, capability-gated (layout UNVERIFIED, V12)
    snippets_dir: .kimi/snippets
    pending_tasks_file: .kimi/pending-tasks.md
    extension_dir: .kimi/3-project
    orchestrator_hint: "- **In Kimi Code:** Use the orchestrator agent."
    bash_tool_name: TBD              # open point, see §11 (V14)
    isolation-dirs: [.kimi/, AGENTS.md]
    gitignore_entries: [.kimi/pending-tasks.md]
    mcp-config: {}                   # empty until MCP config location verified (6.7)
    model-tiers: {nano: kimi-k2.6, fast: kimi-k2.6,
                  balanced: kimi-k2.7-code, powerful: kimi-k2.7-code, max: kimi-k2.7-code}   # exact IDs per catalog — verify in P6
    agent-transform:                 # Option A posture — default transform path, NO new mechanism value
      model: inject
      tools: keep
      strip-fields: [memory, temperature, top_p, top_k, stop_sequences, max_output_tokens]
      strip-claude-lines: true
```

A missing `agent-transform` block triggers a warning in the transform engine
(`provider_transform.py:361-368`); the minimal block above therefore ships in
P1 regardless of the 6.4 posture, so the config stays warning-free under any
option.

### 6.6 Context strategy

- Kimi uses the `AGENTS.md` standard with **nearest-wins subdir semantics
  (like Codex)**: project root + subdirs auto-loaded + global
  `~/.kimi/AGENTS.md`; `/init` can generate the file. **First choice: reuse
  the shared `templates/configs/AGENTS.project-template.md`** → Kimi Code
  joins its consumer set (Gemini, Opencode, Mammouth today; Codex likewise
  per 4.6) — zero template duplication.
- The managed-block/subdir-override interaction flagged for Codex (4.6, V3)
  applies equally to Kimi's nearest-wins semantics — one shared wording audit
  in P4 covers both.
- Config precedence (project config > global > startup params) and `KIMI_*`
  env-var overrides are runtime-harness behavior: **no sync.py work**;
  documented in `docs/providers/kimi-code.md` (P6).

### 6.7 MCP config format, settings template, isolation (open design points)

**MCP-config format** — the MCP surface exists (`/mcp-config`, config file,
ad-hoc `mcpServers` JSON) but its config file location/format is UNVERIFIED
(V13). Options:

1. **Empty `mcp-config: {}` (chosen default, ZCode-style):**
   `_write_provider_config()` (`mcp_provider_config.py:384`) warns + skips
   unknown/missing formats — a safe no-op until verified.
2. **New format value `kimi-toml-mcp`:** if MCP lives in `~/.kimi/config.toml`,
   add ONE format branch → `kimi-toml-mcp` becomes the **second `toml_writer`
   consumer** (7.1) after `codex-toml-mcp`.
3. **Reuse an existing JSON format value:** if a separate `mcpServers`-JSON
   file proves wire-identical to an existing format, reuse it —
   provider-agnostic reuse, no new branch.

Decision rule: verify in P6, decide in the P3 follow-up loop; prefer option 3
over option 2 when wire-identical (reuse beats a new branch); option 1 is the
safe default meanwhile.

**Settings template:** the `settings_file`/`settings_template` pattern exists
(`ai-providers.yaml:40-41`). Decision deferred to P3: generate a
`KIMICODE.settings-template.toml` now vs. defer until V15 verifies the
project-level config file name/path. Default: defer — the `capabilities` list
stays minimal; the settings keys in 6.5 are placeholders pending V15.

**Isolation (open point, documented only):** no verified policy surface in
Kimi Code (no known permissions/deny config). → **no `isolation-mechanism`
value**; cross-provider isolation (≥2 active providers, `isolation.py:79-89`)
takes the documented **skip path**. Revisit only if P6 finds a policy surface.

### 6.8 Delegation syntax + bootstrap

- `config/delegation-syntax.yaml`: `KimiCode` entry with conservative values
  (`handoff_format: yaml_text_block`, no `auto_parallel`) — built-in
  `coder`/`explore`/`plan` exist, but the dispatch tool surface and envelope
  support are unverified (V16).
- `config/provider-bootstrap.yaml`: **UNVERIFIED → do not finalize before P6
  verification** (ZCode discipline, 5.7). Placeholder entry in P1; likely
  `mechanism: config-based` or `file-based` with
  `action: inject-bootstrap-instructions` if runtime registration is needed
  (V16).

---

## 7. Shared Work

### 7.1 Hand-rolled stdlib TOML serializer — `scripts/lib/toml_writer.py`

- Python stdlib ships `tomllib` (read-only); `tomli_w` is not stdlib → the
  writer must be hand-rolled (project constraint: stdlib-only).
- **Location:** `scripts/lib/toml_writer.py` (new module).
- **API (sketch):** `dumps(data: dict) -> str` with support for: nested tables,
  arrays-of-tables (`[[mcp_servers]]`), typed scalars (str/int/float/bool),
  multi-line strings for Markdown bodies (`instructions`), escaping
  (quotes, backslashes, control chars), and deterministic key order (stable
  golden files).
- **Consumers:** Codex agent transform (`codex-toml`), Codex MCP format
  (`codex-toml-mcp`), optionally Kimi MCP format (`kimi-toml-mcp` — potential
  second consumer, only if the 6.7 decision lands on option 2), optionally
  later: `commands.py:_md_to_toml()` and `isolation.py:_build_gemini_toml_rule()`
  (out of scope for this plan — follow-up cleanup candidate).
- **Risks:** TOML edge cases — escaping, arrays-of-tables, nested tables,
  multi-line string semantics. Mitigated by golden/snapshot tests + round-trip
  check against `tomllib` (stdlib parser is available for *verification* in
  tests: `tomllib.loads(toml_writer.dumps(data)) == data`).

### 7.2 `KNOWN_PROVIDERS` extension

`scripts/lib/pipelines.py:16` gains `"Codex"`, `"ZCode"` and `"KimiCode"`
(registry key per the 6.1 naming note); the tuple is validated at
`pipelines.py:196-201` and hard-coded in `tests/test_pipelines.py:12` — both
must change in the same commit (P1).

### 7.3 Capability-flag gaps identified

| Gap | Providers affected | Resolution |
|---|---|---|
| Multi-model (`model.main` + `model.lite`) | ZCode | Tier mapping (5.4 option 1); flag only if proven necessary |
| Per-agent sandbox fields (`sandbox_mode`) | Codex | `agent-transform.extra-fields` (4.7 option 1); new isolation-mechanism value only if provider-level policy needed |
| TOML output format for agents | Codex | New `frontmatter-mechanism` value `codex-toml` (one dispatch branch, string compare — same pattern as `opencode-native`) |
| TOML MCP config format | Codex | New format value `codex-toml-mcp` in `_write_provider_config()` (unknown formats already warn+skip) |
| Agent file format unverified (Markdown+frontmatter vs. kimi-cli YAML-spec heritage) | KimiCode | Option A default transform path (6.4) — no new mechanism value; `kimi-yaml-spec` dispatch branch only if V10 proves YAML-spec; Option C suppression fallback |
| MCP config in TOML vs. JSON (config location unverified) | KimiCode | Empty `mcp-config: {}` default (6.7 option 1); `kimi-toml-mcp` as second `toml_writer` consumer (option 2); reuse an existing JSON format value if wire-identical (option 3) |

---

## 8. Implementation Phases

Effort column order: **opt / likely / pess** (corrected 2026-09-04 — the
buffered total equals the middle value ×1.5; the previous header label
"opt/pess/likely" was a mislabel, the values were always opt/likely/pess).

| Phase | Content | Size | Effort (opt/likely/pess, pd) |
|---|---|---|---|
| **P1** | Registry/config: `ai-providers.yaml` blocks (Codex, ZCode, KimiCode), `provider-capabilities.yaml` rows, `provider-bootstrap.yaml` (KimiCode placeholder — finalized after P6), `delegation-syntax.yaml`, `provider-tools.yaml`, context templates, `KNOWN_PROVIDERS` += Codex/ZCode/KimiCode + `tests/test_pipelines.py:12` | S | 0.35 / 0.75 / 1.5 |
| **P2** | Agent transform + TOML serializer: `scripts/lib/toml_writer.py`, `frontmatter-mechanism: codex-toml` dispatch, ZCode minimal transform, KimiCode minimal strip-transform config + golden files (Option A posture — **no serializer work, no new dispatch branch** for Kimi) | XL | 1.6 / 3.25 / 6.5 |
| **P3** | Isolation + MCP: `codex-toml-mcp` format branch, isolation decision (4.7), ZCode settings template, KimiCode MCP format decision (6.7), KimiCode settings-template decision (V15), KimiCode isolation open point documented (skip path) | M | 0.85 / 2.0 / 4.0 |
| **P4** | Templates/overrides + version bumps (see §12), template wording audit (ZCode no-subdir note; KimiCode joining the shared `AGENTS.project-template.md` consumer set — zero duplication) | M | 0.55 / 1.1 / 2.25 |
| **P5** | Tests + `sync.py --validate` (per-phase incremental, see §10); third-provider test extension: 5 hardcoded provider-list files (6.2), `.kimi/` path-collision, KimiCode snapshots | M | 1.0 / 2.25 / 4.5 |
| **P6** | Docs + external verification (`docs/providers/codex.md`, `docs/providers/zcode.md`, `docs/providers/kimi-code.md`, verification packages from §11 incl. V10–V16) | M | 0.75 / 1.75 / 3.5 |
| **Σ raw** | | | **5.1 / 11.1 / 22.25** |
| **Σ buffered** | ×1.5 | | **≈ 16.5 pd** (opt ≈ 7.5 / pess ≈ 33) → 3–4 calendar weeks, 1 dev |

**Kimi delta (effort-estimator, medium confidence; opt/likely/pess, pd):**
P1 +0.1/0.25/0.5 · P2 +0.1/0.25/0.5 · P3 +0.1/0.5/1.0 · P4 +0.05/0.1/0.25 ·
P5 +0.25/0.75/1.5 · P6 +0.25/0.75/1.5 → **Δ Σ raw +0.85 / 2.6 / 5.25**
(prior two-provider plan: Σ raw 4.25 / 8.5 / 17 → buffered ≈ 13 pd,
2–3 calendar weeks).

**ZCode bootstrap delta (5.8):** the chosen bootstrap posture folds into the
existing P1 registry entries (`provider-bootstrap.yaml` finalization) and P4
(bootstrap-instruction wording for the generated `AGENTS.md` managed block);
ZCode agent-definition golden files extend the P2 snapshot scope marginally.
**Effort totals unchanged** (Σ raw 5.1 / 11.1 / 22.25 pd → ≈ 16.5 pd
buffered, 3–4 calendar weeks) — absorbed within the existing phase bounds.

**Risk notes (from effort-estimator):**
- P1: missing capability flags can force new flags → scope drift into P2.
- P2: critical path; TOML edge cases (escaping, arrays-of-tables, nested tables).
- P2: KimiCode agent format UNVERIFIED — an Option-B/C flip after P6 (V10) can
  rework golden files, but no serializer work is at risk.
- P3: Codex hook payload contract unverified → potential rework.
- P3: KimiCode MCP config location/format unverified → format decision may
  resolve to option 1 (no branch, no rework).
- P5: golden-file churn on serializer changes.
- P6: verification can invalidate P2/P3 decisions → re-loop; KimiCode
  verification (V10–V16) can flip the 6.4/6.7 decisions.

**Parallelization:**
- P1 + P6 (verification packages) start immediately, in parallel.
- P3 can run parallel to P2 fine-tuning.
- P4 depends on P2's output format (what a generated Codex agent looks like).
- P5 runs incrementally per phase (not as a big-bang at the end).
- P2 is the critical path — **KimiCode adds no critical-path work** (Option A:
  no serializer, no dispatch branch); its P6 verification (V10–V16) runs fully
  parallel to the Codex P2 work.
- If P6 verification completes before P2, the estimate drifts toward the
  optimistic bound.

---

## 9. Migration / Sync Order

Follows the Mammouth add-order precedent:

1. **Registry entries** (`config/ai-providers.yaml`, `provider-capabilities.yaml`,
   `provider-bootstrap.yaml`, `delegation-syntax.yaml`, `provider-tools.yaml`)
   — on a `feat/` branch.
2. **Orchestration registries finalized** + `KNOWN_PROVIDERS` extension.
3. **Templates** (`templates/configs/*`, transform, serializer, MCP format).
4. **Activation** — only after `sync.py --validate` is green: adding
   `Codex:`/`ZCode:`/`KimiCode:` to `.meta-config/project.yaml`
   `ai-providers:` and running `python scripts/sync.py` (which itself requires
   a feature branch, per repo policy).

**KimiCode activation order: last.** Its bootstrap entry is only finalized
after P6 verification (6.8, V16) and its agent-generation posture depends on
V10 (6.4) — activation happens after Codex/ZCode, or together with them once
those decisions are in.

**Cross-project propagation:** every 1-generic/config change re-syncs into all
consumer repos on their next sync run. That re-sync cost across consumer
projects is **not** part of this estimate — it is a framework-release concern
(version tags, `agent-meta-manager` upgrades), tracked separately.

**Provider-agnostic code discipline during migration:** new Python behavior
lands only as (a) one `frontmatter-mechanism` dispatch branch, (b) one MCP
format branch, (c) optionally one isolation-mechanism value — each keyed on
config values, never on provider names.

---

## 10. Test Plan

| Phase | Tests |
|---|---|
| P1 | Registry completeness asserts: `sync.py --validate` green; `KNOWN_PROVIDERS` tuple test updated (`tests/test_pipelines.py:12` — three additions); warn-only audit (#625) must not regress |
| P2 | TOML serializer unit tests (scalars, nesting, arrays-of-tables, escaping, multi-line strings) + round-trip against stdlib `tomllib`; golden/snapshot tests for generated `.codex/agents/*.toml` (at least: orchestrator, developer, one rule-heavy agent); ZCode minimal-transform snapshot; KimiCode Option-A golden files (default transform path — Markdown + YAML frontmatter) |
| P3 | MCP: `codex-toml-mcp` golden output + secrets-file split; unknown-format warn+skip unchanged; KimiCode: `mcp-config: {}` warn+skip path unchanged (6.7 option 1); isolation: `--validate` with 2 providers active (e.g. Claude+Codex) produces either no isolation or the documented mechanism — no crashes (`isolation.py:79-89` path); KimiCode isolation skip path exercised with KimiCode in a 2-provider setup |
| P4 | Context filename generation for all three new providers (`tests/test_provider_context_filename.py` pattern); managed-block integrity in generated `AGENTS.md`; version-bump audit (frontmatter versions increased, `based-on` current for 2-platform overrides) |
| P5 | Full suite incl. the five hardcoded provider-list files updated for three providers (`tests/test_pipelines.py:12`, `test_context_compact_mode.py:526` `_ALL_PROVIDERS`, `test_rules_skill_channel.py:69`, `test_secrets_and_isolation.py:52-55`, `test_provider_context_filename.py:20-28`), plus `test_provider_hooks_config.py`, `test_tier_presets.py`, `test_mcp_config.py:20`; `.kimi/` path-collision; KimiCode snapshot tests; hook drift check (`sync.py:1189-1193`) exercised with Codex and KimiCode paths reserved |
| P6 | Manual: generated output diffed against real harness expectations (Codex CLI run; ZCode ADE run; Kimi Code CLI run); docs review |

Cross-cutting: **path-collision checks** — `.codex/`, `.zcode/`, `.kimi/` must
not collide with existing provider dirs (extend
`tests/test_provider_hooks_config.py` pattern); **`sync.py --dry-run`** before
every real sync during development.

---

## 11. Open Verification Points

| # | Item | Blocks | Source |
|---|---|---|---|
| V1 | Codex hook **payload contract** (stdin format, blocking semantics, `hooks.json` vs inline TOML) | `hook_protocol` decision (P3+); until then #630 pattern | Codex docs/changelog v0.150.0+ |
| V2 | ZCode agents/skills/hooks/MCP/commands surface | ZCode capability list growth (P1/P3 scope) | zcode.z.ai/en/docs + llms.txt index at docs.z.ai |
| V3 | Codex `AGENTS.md` subdir-override/nearest-wins interaction with managed blocks | Dedicated vs shared context template (4.6) | Codex docs + real-repo test |
| V4 | Codex **bash tool name** (for `provider-tools.yaml` tool whitelist + `terminal_tool` map + `bash_tool_name`) | P1 registry entries (placeholder until verified) | Codex docs/tool catalog |
| V5 | ZCode **tool names** | `provider-tools.yaml` whitelist, delegation syntax | ZCode docs |
| V6 | ZCode project override precedence (`zcode.json` vs `.zcode/config.json`) | `settings_file` choice (5.3) | ZCode docs |
| V7 | Codex `.codex/agents/*.toml` auto-load + `multi_agent` flag enablement | bootstrap `action` (4.8), `parallel_execution` flag | Codex docs |
| V8 | Codex MCP merge semantics for `.codex/config.toml` (project-level merge; secrets-file strategy) | MCP format branch details (P3) | Codex docs |
| V9 | ZCode `model.lite` exact model IDs + whether per-role selection is required | tier mapping vs capability flag (5.4) | ZCode docs / model catalog |
| V10 | Kimi Code custom agent file format in the successor (Markdown + YAML frontmatter vs. kimi-cli YAML-spec heritage: `version: 1`, `agent.extend`, `subagents` map) | 6.4 Option A/B/C decision; `file_based_agents` flag; bootstrap posture | MoonshotAI/kimi-code docs |
| V11 | Kimi Code hooks event names + payload contract (beta docs) | `hook_protocol` decision; until then #630 pattern with `hooks_dir: .kimi/hooks` reserved | Kimi Code beta docs |
| V12 | Kimi Code skills/plugins directory layout | `skills_dir` activation, skills capability growth (P1/P3) | Kimi Code docs |
| V13 | Kimi Code MCP config file location/format + secrets split | 6.7 MCP format decision (option 1/2/3) | Kimi Code docs |
| V14 | Kimi Code bash/tool names for `provider-tools.yaml` (whitelist, `terminal_tool` map, `bash_tool_name`) | P1 registry entries (placeholder until verified) | Kimi Code docs |
| V15 | Kimi Code project-level config file name/path | `settings_file`/`settings_template` decision (6.7), `settings` capability | Kimi Code docs |
| V16 | Kimi Code subagent dispatch tool surface / bootstrap registration | `delegation-syntax.yaml` entry, `provider-bootstrap.yaml` finalization (6.8), `native_agent_tools` | Kimi Code docs |
| V17 | ZCode **exact native agent-dispatch tool name** (toolcall surface for the 5.8 dispatch layer) | `native_agent_tools` entry, `delegation-syntax.yaml` `ZCode` entry, dispatch-layer detail (5.8) | ZCode docs |
| V18 | ZCode **inline persona per agent call** — can the dispatch toolcall carry the full persona text, or only name/description? | 5.8 layer-2 detail depth: file-reference bootstrap roster vs. compact inline roster fallback (5.8) | ZCode docs |

Each item gets a dated result note in the implementation PR; V1–V2 and V10 are
the P6 kickoff deliverables; V17–V18 ride along with the V2 ZCode
verification package (5.8).

---

## 12. Constraints & Conventions

1. **Provider-agnostic (hard):** NO `if provider == "Codex"` / `== "ZCode"` /
   `== "KimiCode"` branches — capability flags/config keys only. Reference
   patterns: `_has_capability` (`context.py:281`), `frontmatter_strip_fields`
   (#505), `frontmatter-mechanism` (#629), conservative-baseline capability
   rows (#630/#631). New mechanism values are dispatched by string compare,
   never by provider identity.
2. **Version bumps:** every new/changed agent template or platform override
   bumps frontmatter version per Development Conventions (minor `x.Y.0` for
   new optional sections; `based-on` kept current for `2-platform/`).
3. **Branch policy:** all implementation on a `feat/` branch — never `main`.
   Running `sync.py` also requires a feature branch (repo rule). Conventional
   Commits (`feat: ...`, ≤72 chars, imperative, English).
4. **Stdlib-only:** no external Python deps; TOML writing is hand-rolled
   (§7.1), TOML *reading* in tests uses stdlib `tomllib`.
5. **Placeholders:** any new `{{VARIABLE}}` must be registered in the CLAUDE.md
   variables table before use — the design above deliberately introduces none.
6. **Generated output:** `.codex/`/`.zcode/`/`.kimi/` outputs are generated by
   sync.py — never edited manually in consumer repos (same invariant as
   `.claude/agents/`).
7. **Doc conventions:** docs in English where externally facing (this plan,
   `docs/providers/*`); internal docs German per language rules.

---

## 13. References

**Issues:** #505 (frontmatter strip_fields), #629 (data-driven agent-transform),
#630 (Mammouth hook-skip precedent / payload contract), #631 (capability-flag
pattern), #625 (provider-registry completeness check, warn-only).

**Kimi Code sources:**

- MoonshotAI/kimi-code — official target (GitHub repo; npm package
  `@moonshot-ai/kimi-code`, TypeScript successor)
- MoonshotAI/kimi-cli docs — reference-only (discontinued Python predecessor;
  migration automates config/sessions; YAML agent specs as heritage context)
- opencode-go model catalog (`kimi-k2.6`, `kimi-k2.7-code`)

**Key files:**

- `scripts/lib/pipelines.py:16,196-201` — `KNOWN_PROVIDERS` + validation
- `scripts/lib/provider_transform.py:150-323,325,361-368` — transform engine, dispatch, missing-block warning
- `scripts/lib/context.py:281,760` — `_has_capability`, Continue literal
- `scripts/lib/providers.py:168,171-180` — `SUPPORTED_HOOK_PROTOCOLS`, `provider_hooks_supported()`
- `scripts/lib/mcp_provider_config.py:384-405` — `_write_provider_config()` format dispatch
- `scripts/lib/isolation.py:389-394,79-89,277-302` — isolation handlers, skip path, Gemini TOML rule
- `scripts/lib/commands.py:60-74,~124` — `_md_to_toml()`, command literal branch
- `scripts/lib/frontmatter.py:344-373` — `inject_model_field()`
- `scripts/lib/roles.py:106-259` — `resolve_model()` chain
- `scripts/sync.py:1140-1209` — `--validate`; `:1189-1193` hook drift check
- `config/ai-providers.yaml` (Opencode block `:185-248` incl. `frontmatter-mechanism: opencode-native :233` and the `kimi`/`kimi-code` model aliases `:245-246` — naming constraint for the KimiCode registry key; Mammouth block `:354-421` incl. #630 hook pattern)
- `config/provider-capabilities.yaml` (row schema `:5-100`, Mammouth conservative baseline `:77-100`)
- `config/provider-bootstrap.yaml`, `config/delegation-syntax.yaml`, `config/provider-tools.yaml`
- `tests/test_pipelines.py:12` and the provider-aware test files listed in §10
- `docs/plans/archive/audit-2026-09-system-concept.md` — add-provider touchpoint audit (`/add-provider` covers activation only)
- `docs/plans/README.md` — plans lifecycle (active vs archive)
- `docs/architecture/01-layer-model.md` — layer/composition model
