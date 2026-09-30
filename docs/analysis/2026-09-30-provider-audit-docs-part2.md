# Provider Audit — Online-Doc Contract Comparison (Part 2)

**Date (all accesses): 2026-09-30** · **Repo:** `/home/hermes/repos/agent-meta` · **Branch:** `feat/provider-audit-opencode-v2` @ `65a493ec`
**Phase:** 0 (read-only, no fixes) · **Scope:** Codex, ZCode, KimiCode, Continue, Mammouth
**Out of scope (sibling agent, Part 1):** Claude, Gemini/Antigravity, Opencode v1/v2, Copilot.

## Method & evidence provenance (important)

- The generated trees named in the task prompt (`.codex/`, `.zcode/`, `.kimi-code/`, `.mammouth/`) **do not exist in this
  repo checkout** — `ai-providers:` in `.meta-config/project.yaml` is `Claude, Opencode, Gemini` only, and `.mammouth/` is
  gitignored (`.gitignore:15`). They were therefore **regenerated into a throwaway scratch project**
  (`.tmp/provider-audit/`, `sync.py --config .tmp/provider-audit/.meta-config/project.yaml`, rc 0) with
  `ai-providers: [Codex, ZCode, KimiCode, Continue, Mammouth]`. Every "Generated" excerpt below is from that scratch run,
  which uses the identical `scripts/lib` + `config/` + `agents/` as HEAD. This is non-production scratch; no repo file
  except this report and `.tmp/` was written.
- Network: `curl -sL` OK for every URL below (HTTP 200 unless noted). No doc fact is asserted without a fetched source.
- Mammouth Code is a **fork of OpenCode** (`github.com/mammouth-ai/code`, `parent/source = anomalyco/opencode`,
  `default_branch = dev`). Its "official online documentation" is the page `info.mammouth.ai/docs/mammouth-code/` plus the
  docs/source shipped in the official repo (the product's own `packages/web/src/content/docs/*.mdx` and its TypeScript
  loaders). Where the published marketing page is silent (agents/MCP/config), the fork's own docs+source are quoted and
  labelled as such.

| Tag | Meaning |
|---|---|
| **VERIFIED** | Doc quote fetched on 2026-09-30 (or official repo source) + observable generated excerpt |
| **HYPOTHESIS** | Not resolvable from the available docs; explicitly marked, no doc fact asserted |
| **FLAG-MISMATCH** | `provider-capabilities.yaml` declares more/less than the docs support |

---

## 1. Codex (OpenAI Codex CLI)

Sources (2026-09-30): `developers.openai.com/codex/agent-configuration/subagents`, `/codex/config-file/config-reference`,
`/codex/extend/mcp`, `/codex/hooks`, `/codex/agent-configuration/agents-md`, `/codex/skills`.

### 1.1 Artifact contract (agents)

| Aspect | Documented | Generated (scratch) | Status |
|---|---|---|---|
| Dir | `~/.codex/agents/` personal, `.codex/agents/` project-scoped | `.codex/agents/*.toml` (59 + `.agent-meta-managed`) | VERIFIED CONFORMANT |
| Discovery | *"Codex loads these files as configuration layers for spawned sessions"* — no registration step | file-based, no registry | CONFORMANT |
| Required fields | *"Every standalone custom agent file must define: `name` `description` `developer_instructions`"* | `name`, `description`, `developer_instructions` present on 59/59 | CONFORMANT |
| Optional fields | *"You can also include other supported config.toml keys … such as `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, and `skills.config`."* | `model`, `sandbox_mode` used | CONFORMANT |
| Provenance | not documented / ignored | `version`/`generated-from` emitted as TOML `#` comments | CONFORMANT (comments carry no config semantics) |

Generated excerpt (`.codex/agents/developer.toml:5-10`):

```toml
name = "developer"
description = "Developer-Agent für das agent-meta Meta-Repository. …"
model = "gpt-5.3-codex-spark"
sandbox_mode = "workspace-write"
developer_instructions = """
```

### 1.2 Config / MCP contract

`.codex/config.toml` (project-scoped) is the documented MCP location: *"edit `~/.codex/config.toml` or a project-scoped
`.codex/config.toml`"*, per server `[mcp_servers.<server-name>]`. Remote (Streamable HTTP) keys are exactly:
`url`, `auth`, `bearer_token_env_var`, `http_headers`, `env_http_headers`, `http_headers_helper`.

> Doc quote: *"`http_headers` (optional): Map of header names to static values."* — `developers.openai.com/codex/extend/mcp`

Generated (`.codex/config.toml:5-21`):

```toml
[mcp_servers.honcho]
url = "${MCP_HONCHO_URL}"
bearer_token_env_var = "MCP_HONCHO_API_KEY"
[mcp_servers.honcho.headers]          # <-- `headers` is NOT a documented key
X-Honcho-User-Name = "${MCP_HONCHO_USER_NAME}"
…
[mcp_servers.reqogniloom.headers]
X-Project-ID = "${MCP_REQOGNILOOM_PROJECT_ID}"
```

→ **CX-1**: `[mcp_servers.<id>.headers]` is undocumented; the documented spelling is `http_headers`. The static
X-*-headers are silently ignored by Codex (auth-relevant for honcho/reqogniloom).

### 1.3 Context / skills / hooks / commands

- Context: *"Codex reads `AGENTS.md` files before doing any work … Codex reads `AGENTS.override.md` if it exists.
  Otherwise, Codex reads `AGENTS.md`."* → `context_file: AGENTS.md`, generated at repo root → CONFORMANT.
- Skills: *"Codex scans `.agents/skills` in every directory from your current working directory up to the repository
  [root] … `$REPO_ROOT/.agents/skills`"* → `skills_dir: .agents/skills` is documented, but the scratch run writes **0**
  skill files (`.agents/skills/` empty). See FLAG-MISMATCH CX-2.
- Hooks: contract verified (V1) but deliberately **not mirrored** (`hooks: false`, no `hook_protocol`) — consistent,
  and `.codex/hooks/` is absent in the generated output. CONFORMANT with the declared posture.
- Commands: docs expose only built-in slash commands; no documented project-level custom-command surface → `commands: false`
  is consistent (no over/under-claim found).

### 1.4 Verdict: `DEVIATION(1)`

| ID | Sev | Generated | Doc quote | URL |
|---|---|---|---|---|
| **CX-1** | MED | `.codex/config.toml:8,18` `[mcp_servers.honcho.headers]` / `[mcp_servers.reqogniloom.headers]` | *"`http_headers` (optional): Map of header names to static values."* | https://developers.openai.com/codex/extend/mcp |

---

## 2. ZCode (zcode.z.ai)

Sources (2026-09-30): `zcode.z.ai/en/docs/subagents`, `/skill`, `/mcp-services`, `/commands`, `/configuration`, `/qa`, `/hooks`.

### 2.1 Artifact contract (subagents)

Documented definition-file frontmatter (camelCase, case-sensitive): `name`/`description` (required), `model` (id or
`inherit`), `thoughtLevel` (≠ `reasoningEffort`), `color`, `tools`/`disallowedTools`, `maxTurns`, `injectAgentsMd`,
`mcpServers`. Unknown keys are *"silently ignored, with no error."*

Generated `.zcode/agents/developer.md:1-21`: `name`, `version`, `based-on`, `description`, `hint`, `prompt_mode`, `tools`
(YAML list), `generated-from`, `model: glm-5.3`. Required fields present; `version/hint/prompt_mode/based-on/generated-from`
are unknown-but-ignored; `tools` list matches the documented exhaustive built-in list (Read/Grep/Glob/Bash/Edit/Write/
WebFetch/WebSearch/TodoWrite); `model: glm-5.3` matches V9. **Frontmatter: CONFORMANT.**

> Doc quote (scope): *"**User-level only.** The current Beta manages global / user-level subagents stored under
> `~/.zcode/agents/`. Creating or editing workspace / project-level subagents from Settings is not available yet."*
> — `zcode.z.ai/en/docs/subagents`

→ **ZC-1**: agent-meta writes workspace-level `.zcode/agents/*.md`. Per the 2026-09-30 docs these are **not auto-loaded**
(user-level `~/.zcode/agents/` is the only verified auto-load; V18's P6 open item is unchanged). The generated
`AGENTS.md` bootstrap block (lines 385-403) compensates by prompt-registering them — a workaround, not a runtime contract.

### 2.2 Config / MCP contract

Documented workspace config: *"Workspace (current project only) `<project root>/.zcode/config.json` → Config key
`mcp.servers`"*. Generated `.zcode/config.json` uses `mcp.servers` ✓ and per-server `headers` (docs: *"expand Headers
(optional)"*) ✓.

> HYPOTHESIS: the per-server `"type": "sse"`/`"stdio"` key is not shown in the documented native example (which has only
> `command/args/env`); the settings panel mentions "Keep the type as stdio (SSE and HTTP … supported)". Exact key/value
> spelling unverified.

→ RUNTIME: **REFUTED (H5)** — `"type"` is not an undocumented extra key but the **mandatory discriminator**. The installed
`zcode-app-cli/vendor/zcode.cjs` defines `ZVr = preprocess(ljs, discriminatedUnion("type", [stdio, http, sse]))` with `.strict()`
on each variant; without `type` the entry fails parsing (`config_mcp_server_invalid`, server dropped). The generated
`.zcode/config.json` loads with `diagnostics: []`, and its `type: "sse"/"stdio"` values are schema-conformant. Command: inspect
`vendor/zcode.cjs`, `zcode` config load. Evidence: `docs/analysis/evidence/2026-09-30-runtime-codex-kimi-zcode.md` §3.

### 2.3 Context / skills / commands

- Context: docs `AGENTS.md` injection *"subagents inject the user-level `~/.zcode/AGENTS.md` and workspace `AGENTS.md`
  by default"* → `context_file: AGENTS.md` CONFORMANT.
- Skills: *"User-level skills … `~/.zcode/skills/<skill-name>/SKILL.md`"* + import target *"Project (current workspace
  only)"*. Generated `.zcode/skills/<name>/SKILL.md` (25, `name`+`description` frontmatter ✓). **Supported, but
  `provider-capabilities.yaml` does not declare `skills`** (FLAG-MISMATCH ZC-3).
- Commands: *"Custom commands are stored as `.md` files under `~/.zcode/commands` (workspace-level commands live in the
  project directory)."* Docs confirm a **workspace** command surface, yet `has_commands: false` / `commands: false`
  (FLAG-MISMATCH ZC-2).
- Hooks: docs `/hooks` exist but *project-level* hooks are ignored (`config_project_hooks_ignored`, V2) → `hooks: false`
  consistent.

### 2.4 Verdict: `DEVIATION(1)` + 1 HYPOTHESIS

| ID | Sev | Generated | Doc quote | URL |
|---|---|---|---|---|
| **ZC-1** | MED | `.zcode/agents/*.md` (59) + `AGENTS.md:385-403` bootstrap workaround | *"User-level only. The current Beta manages global / user-level subagents stored under `~/.zcode/agents/`. Creating or editing workspace / project-level subagents from Settings is not available yet."* | https://zcode.z.ai/en/docs/subagents |

---

## 3. KimiCode (Moonshot AI Kimi Code CLI)

Sources (2026-09-30): `moonshotai.github.io/kimi-code/en/customization/agents`, `/mcp`, `/hooks`, `/skills`.

### 3.1 Artifact contract (agents)

Docs: project level *".kimi-code/agents/"*, *"Each directory is scanned recursively for `.md` files."* Frontmatter:
`name` (optional, kebab-case, defaults to filename), `description` (**required**), `whenToUse`, `override`, `tools`
(YAML list or CSV), `disallowedTools`, `subagents`. Unknown fields ignored.

Generated `.kimi-code/agents/developer.md:1-21` → dir ✓, `description` ✓, `name` kebab-case ✓, `tools` YAML list ✓;
`version/based-on/hint/prompt_mode/generated-from` unknown-but-ignored; `model: kimi-k2.7-code` (docs: *"A specific model
id"*) → **frontmatter CONFORMANT; model-ID value = HYPOTHESIS** (no model catalog in the fetched page to confirm the exact id).

→ RUNTIME: **VERIFIED (H6).** A real ACP handshake (`kimi acp` → `session/set_config_option {configId:"model",
value:"kimi-k2.7-code"}`) returns `error -32603: Model "kimi-k2.7-code" is not configured in config.toml`; the 4 configured
aliases are all provider-qualified (`kimi-code/…`). Scan of 58 generated files: `kimi-k2.7-code` ×34, `kimi-k2.6` ×24, and
**58/58** model IDs are not configured runtime aliases. `.kimi-code/agents/*.md` itself is a real project-discovery path
(`PROJECT_BRAND_DIRS`) — the dir is fine, only the model ID is unresolvable. Evidence:
`docs/analysis/evidence/2026-09-30-runtime-codex-kimi-zcode.md` §2.

### 3.2 Context / skills

- Context: *"AGENTS.md: Projekt-Root + Subdirs auto-geladen (nearest-wins …)"* → `context_file: AGENTS.md` CONFORMANT.
- Skills: project-level `.kimi-code/skills/` is documented; directory-form `SKILL.md` requires explicit `name` +
  `description` (*"Omitting either one will cause parsing to fail."*). Generated `.kimi-code/skills/<name>/SKILL.md` (25)
  carry both → CONFORMANT. But `skills` is **not declared** in KimiCode's capabilities (FLAG-MISMATCH KC-2).

### 3.3 MCP contract — DEVIATION

Docs: *"MCP server configuration is written in `mcp.json` … Project level: `.kimi-code/mcp.json`"*, key `mcpServers` ✓.
Transport discrimination is by **field presence**, not a `type` key:

> *"Entries with a `command` field are stdio servers; entries with a `url` field and no `transport` are HTTP servers.
> For legacy SSE servers, set `transport` to `"sse"` explicitly."* — `…/customization/mcp`

Generated `.kimi-code/mcp.json:2-11`:

```json
"mcpServers": {
  "honcho": { "type": "sse", "url": "${MCP_HONCHO_URL}", "headers": {…} },
  "playwright": { "type": "stdio", "command": "npx", "args": […] }
}
```

→ **KC-1**: KimiCode has no documented `type` field; SSE must be declared as `transport: "sse"`. With `type` ignored, the
honcho/reqogniloom entries have a `url` and **no `transport`** → KimiCode classifies them as **HTTP**, not SSE. The
`/mcp/sse/` endpoint is therefore driven over the wrong transport. (`stdio` entries degrade harmlessly because `command`
is present; `headers` is documented for HTTP/SSE ✓.)

### 3.4 Hooks / commands

- Hooks: only `~/.kimi-code/config.toml [[hooks]]` (user-level) is documented; no project-level hook surface → `hooks: false`
  is consistent (no mirror). CONFORMANT with declared posture.
- Commands: no documented project-level custom-command surface on the fetched page; `commands: false` not contradicted.

### 3.5 Verdict: `DEVIATION(1)`

| ID | Sev | Generated | Doc quote | URL |
|---|---|---|---|---|
| **KC-1** | MED | `.kimi-code/mcp.json:4-6` `"type": "sse", "url": …` | *"Entries with a `command` field are stdio servers; entries with a `url` field and no `transport` are HTTP servers. For legacy SSE servers, set `transport` to `"sse"` explicitly."* | https://moonshotai.github.io/kimi-code/en/customization/mcp |

---

## 4. Continue (docs.continue.dev)

Sources (2026-09-30): `docs.continue.dev/reference`, `/customize/deep-dives/rules`, `/customize/deep-dives/mcp`,
`/customize/deep-dives/prompts`, plus official repo source (`continuedev/continue@main`):
`packages/config-yaml/src/schemas/index.ts`, `…/markdown/markdownToRule.ts`.

### 4.1 Config contract

> Doc quote: *"The top-level properties in the `config.yaml` configuration file are: `name` (required) `version`
> (required) `schema` (required) `models` `context` `rules` `prompts` `docs` `mcpServers` `data`."* — `docs.continue.dev/reference`

Official schema confirms: `configYamlSchema` = `{name, version, schema, metadata, env, requestOptions, models, context,
data, mcpServers, rules, prompts, docs}` — **no `agents` key** (`packages/config-yaml/src/schemas/index.ts:113-153`).
Generated `.continue/config.yaml:79-198` injects an `agents:` list of 58 `{name, prompt}` entries:

```yaml
# agent-meta:managed-agents-begin
agents:
  - name: accessibility-specialist
    prompt: prompts/accessibility-specialist.md
```

→ **CO-1**: `agents` is not part of `config.yaml`; the zod object strips unknown keys → the whole managed agent registry is
**dead config**. Redundant too: `.continue/agents/*.md` (59) is emitted alongside it.

- `.continue/agents/*.md` (59) frontmatter: `name`, `description`, `model`, `alwaysApply: false` (+ ignored
  `version/hint/prompt_mode/based-on/generated-from`). The parser `agentFiles.ts` (comment: *"Experimental/internal config
  format for agents"*) reads `name/description/model/tools/rules` + body; `alwaysApply` belongs to rules, not agents.
  **HYPOTHESIS**: whether `.continue/agents/` is auto-discovered is not in the public docs (docs state *"Continue Agents are
  defined using the `config.yaml` specification."*); source has `SUPPORTED_AGENT_FILES` + `.continue/agents` handling.

→ RUNTIME: **VERIFIED `[STATIC]`, surface-dependent (H7).** Source (pinned `continuedev/continue@main` `5522c6f4`): IDE chat
auto-discovery (`core/config/ConfigHandler.ts:161-179` → `getAllDotContinueDefinitionFiles(..., "agents")`) loads **`.yaml/.yml`
only**; `.continue/agents/*.md` is auto-loaded **only** by the `cn review` path (`src/commands/review/resolveReviews.ts:57-89`);
`cn` parses `.md` via `parseAgentFile` only with an explicit `--agent <path>.md` (`src/services/AgentFileService.ts:55-88`). So
the generated header comment *"auto-discovered by Continue"* is **REFUTED for the chat surface** and **VERIFIED for `cn review`**.
No live turn (no credentials). Evidence: `docs/analysis/evidence/2026-09-30-runtime-continue.md` §4.

### 4.2 Rules / MCP / prompts

- Rules: *"Rules should be `.md` files with proper YAML frontmatter"* (troubleshooting). Generated
  `.continue/rules/project-context.md` has **no frontmatter** — but `markdownToRule.ts:103-114` falls back to a
  path-derived name and `globs: undefined` → rule is always included. **Tolerated by parser → not a deviation** (LOW note:
  the docs-recommended `name` is absent; the imported core path in `loadLocalAssistants.ts` confirms `.continue/rules`).
- MCP: `mcpServers` with `type` (`sse`/`stdio`/`streamable-http`), `url`, `command`, `args`, `env` — documented in the MCP
  deep-dive. Generated `.continue/config.yaml:200-232` matches. `headers:` on the SSE entries is not listed in the
  deep-dive property list (name/type/command/args/env) → **HYPOTHESIS** (may be accepted via `requestOptions`).

→ RUNTIME: **REFUTED (H8).** `@continuedev/config-yaml@1.42.0` `packages/config-yaml/src/schemas/mcp/index.js:18-23`
(`sseOrHttpMcpServerSchema`) has keys `name,serverName,faviconUrl,sourceFile,sourceSlug,connectionTimeout,url,type,apiKey,requestOptions`
— **no top-level `headers`**; Zod strips unknown keys by default. Parse: `honcho (type=sse) parsedKeys=[name,url,type]
headersKept=false` (same for reqogniloom) → the honcho/reqogniloom auth headers are silently dropped; the correct spelling is
`requestOptions.headers`. Evidence: `docs/analysis/evidence/2026-09-30-runtime-continue.md` §5.
- Prompts: *"Prompts can be invoked with a `/` command"*, file frontmatter `name`/`description`/`invokable: true`.
  Generated `.continue/prompts/*.md` (80) carry exactly these → CONFORMANT.
- Commands: `commands_dir: .continue/prompts` (prompts = slash commands) matches the documented surface.

### 4.3 Verdict: `DEVIATION(1)` + 2 HYPOTHESES

| ID | Sev | Generated | Doc quote / source | URL |
|---|---|---|---|---|
| **CO-1** | MED | `.continue/config.yaml:81-85` top-level `agents:` list | *"The top-level properties … are: `name` … `prompts` `docs` `mcpServers` `data`."* (no `agents`); `configYamlSchema` has no `agents` key | https://docs.continue.dev/reference · https://github.com/continuedev/continue/blob/main/packages/config-yaml/src/schemas/index.ts |

---

## 5. Mammouth (Mammouth Code)

Sources (2026-09-30): `info.mammouth.ai/docs/mammouth-code/`; official repo `github.com/mammouth-ai/code` @ `dev`
(`packages/web/src/content/docs/{agents,rules,mcp-servers,skills}.mdx`, `packages/core/src/global.ts`,
`packages/opencode/src/config/{config,paths,agent,parse}.ts`, `packages/core/src/v1/config/agent.ts`).
Mammouth Code is an OpenCode fork; the docs site links to the open-source repo as the configuration reference.

### 5.1 Artifact contract (agents)

Fork docs (`.mdx`) say: *"Global: `~/.config/opencode/agents/` · Per-project: `.opencode/agents/`"*.
Fork source `ConfigPaths.directories()` traverses for **both** `.opencode` **and** `.mammouth`; `ConfigAgent.load(dir)`
globs `"{agent,agents}/**/*.md"`. So `.mammouth/agents/*.md` **is** discovered by the dev-branch build (source-verified),
even though the published docs only name `.opencode/agents/`. → MM-1 = LOW documentation/source divergence, not a break.

Fork agent schema (`packages/core/src/v1/config/agent.ts:12-41`) KNOWN keys: `name, model, variant, prompt, description,
temperature, top_p, mode, hidden, color, steps, maxSteps, options, permission, disable, tools`; unknown keys are collected
into `options`. **`tools` is typed `Record(String, Boolean)`** and the fork docs confirm it is a *map*:

> *"`tools` is deprecated. … Allows you to control which tools are available in this agent. You can enable or disable
> specific tools by setting them to `true` or `false`."* — `packages/web/src/content/docs/agents.mdx`

Generated `.mammouth/agents/developer.md:11-18`:

```yaml
tools:
- Bash
- Read
- Write
- Edit
- Glob
- Grep
- TodoWrite
model: claude-sonnet-5
```

→ **MM-2 (HIGH)**: `tools` is emitted as a **YAML string list**; the schema requires `Record<String, Boolean>`. Decode
fails (`ConfigParse.schema` **throws**, `agent.ts` `load()` has no per-item catch), which aborts agent loading for
`.mammouth/agents/` entirely — all 59 agents are affected.
→ RUNTIME: **VERIFIED (real release binary `1.18.31.1`)** — `mammouth agent list` → `Error: Configuration is invalid at
.mammouth/agents/git.md ↳ Expected object | undefined, got ["Bash",…] tools`, `RC=1`; no agent loads. Evidence:
`docs/analysis/evidence/2026-09-30-runtime-mammouth-copilot.md` §2.1.
→ **MM-5 (MED)**: fork docs: *"The model ID in your OpenCode config uses the format `provider/model-id`"* (e.g.
`anthropic/claude-sonnet-4-20250514`). Generated `model: claude-sonnet-5` has no provider prefix. (HYPOTHESIS: a bare
alias might resolve, but no fetched doc supports it.)
→ RUNTIME: **REFUTED (H10)** — bare aliases do **not** resolve: `mammouth debug agent developer` → `"model":
{"providerID":"claude-sonnet-5","modelID":""}` and `mammouth run --model claude-sonnet-5 "ping"` →
`ProviderModelNotFoundError: Model not found: claude-sonnet-5/.` (a qualified control `opencode/big-pickle` resolves). The
generated Mammouth model IDs are therefore unusable (MM-5 is real, not merely a hypothesis). Evidence:
`docs/analysis/evidence/2026-09-30-runtime-mammouth-copilot.md` §2.2.

### 5.2 Config / settings contract

Fork `ConfigPaths.files()` searches for `mammouth.jsonc`/`mammouth.json`/`opencode.jsonc`/`opencode.json` (project root,
walking up) and, inside each `.opencode`/`.mammouth` dir, loads `opencode.json(c)`/`mammouth.json(c)`. `Global.Path.config`
= `$XDG_CONFIG_HOME/mammouth` (`packages/core/src/global.ts:10-13`).

Generated `.mammouth/settings.json`:

```json
{
}
```

→ **MM-3 (MED)**: `settings.json` is **never read** by the loader; the documented project config file names are
`mammouth.json(c)` / `opencode.json(c)`. The file is inert (and empty).

### 5.3 Context contract

Fork docs `rules.mdx`: *"You can provide custom instructions to opencode by creating an `AGENTS.md` file."* Precedence:
local `AGENTS.md`/`CLAUDE.md` → `~/.config/opencode/AGENTS.md` → `~/.claude/CLAUDE.md`. **`MAMMOUTH.md` is not a
documented instruction file.**

Generated `MAMMOUTH.md` (root, `templates/configs/AGENTS.project-template.md`) duplicates the root `AGENTS.md`; the routing
banner even instructs *"Mammouth -> MAMMOUTH.md"* (`.continue/rules/project-context.md:9`).
→ **MM-4 (MED)**: Mammouth reads `AGENTS.md` (present) and ignores `MAMMOUTH.md`; the extra file is an orphan that the
routing text wrongly advertises.

### 5.4 Skills / rules / MCP / hooks / commands

| Surface | Docs (fork) | Generated | Status |
|---|---|---|---|
| skills | Agent Skills supported (`skills.mdx`, `skill` permission) | `.mammouth/skills/` exists but **0 files** | FLAG-MISMATCH MM-a (capability `skills` declared, no artifacts) |
| rules | via `AGENTS.md` / `instructions` | `.mammouth/rules/*.md` (38) — not a Mammouth concept | LOW extra-dir note (rules also embedded in `AGENTS.md`) |
| MCP | `mcp` key, `opencode.json`/`mammouth.json`, local/remote | none (`mcp-config: {}`, `mcp` absent from capabilities) | FLAG-MISMATCH MM-b (under-claim; docs support MCP) |
| hooks | plugin/hook surface exists in fork; not documented for project scope | `has_hooks:true` + `hooks_dir` but **no** `hook_protocol` → not mirrored (absent) | consistent with V-baseline |
| commands | docs have `commands.mdx` (`/…`); `commands: false` declared | none | potential under-claim (not re-verified in this pass) |

### 5.5 Verdict: `DEVIATION(5)`

| ID | Sev | Generated | Doc quote / source | URL |
|---|---|---|---|---|
| **MM-1** | LOW | `.mammouth/agents/*.md` | docs: *"Per-project: `.opencode/agents/`"*; source `ConfigPaths` accepts `.opencode` **and** `.mammouth` | https://github.com/mammouth-ai/code/blob/dev/packages/web/src/content/docs/agents.mdx · `…/packages/opencode/src/config/paths.ts:29-35` |
| **MM-2** | **HIGH** | `.mammouth/agents/developer.md:11-18` `tools:` YAML list | *"`tools` … setting them to `true` or `false`"*; `agent.ts` schema `tools: Record<String, Boolean>` | `…/packages/web/src/content/docs/agents.mdx` · `…/packages/core/src/v1/config/agent.ts:21` |
| **MM-3** | MED | `.mammouth/settings.json` `{}` | loader reads `mammouth.json(c)`/`opencode.json(c)`; `settings.json` absent | `…/packages/opencode/src/config/paths.ts:10-45` |
| **MM-4** | MED | root `MAMMOUTH.md` + routing `"Mammouth -> MAMMOUTH.md"` | *"creating an `AGENTS.md` file"*; precedence local `AGENTS.md`/`CLAUDE.md` | `…/packages/web/src/content/docs/rules.mdx:6,95-103` |
| **MM-5** | MED | `.mammouth/agents/developer.md:20` `model: claude-sonnet-5` | *"The model ID … uses the format `provider/model-id`."* | `…/packages/web/src/content/docs/agents.mdx` |

---

## 6. Capability-flag mismatches (`config/provider-capabilities.yaml` / `config/ai-providers.yaml`)

Claims **MORE** than docs/artifacts support (should be softened):

| Provider | Flag | Problem |
|---|---|---|
| Codex | `capabilities: [..., skills, ...]` | `.agents/skills` is documented and declared, but the sync writes 0 skill files (scratch: `.agents/skills/` empty). Capability without artifacts. |
| Mammouth | `capabilities: [..., skills, ...]` | same: `.mammouth/skills/` empty despite the declared capability (MM-a). |
| Mammouth | `has_hooks: true`, `hooks_dir` | no `hook_protocol`; no hook artifacts are produced — the flags describe an unmirrored surface (documented rationale, but the capability list still advertises `hooks`). |
| Continue | `capabilities: [..., skills, ...]` | no public Continue "skills" surface in the fetched docs (`Customize` = Models/MCP/Rules/Prompts); `.continue/skills/` is empty. Source has `loadMarkdownSkills.ts` → **HYPOTHESIS** (may be a real undocumented surface). |

Claims **LESS** than docs support (flags could be flipped upward):

| Provider | Flag | Docs support |
|---|---|---|
| ZCode | `commands: false` / `has_commands: false` | *"workspace-level commands live in the project directory"* — project command surface documented. |
| ZCode | `skills` not in capabilities | project-level skills documented (import target "Project"); `.zcode/skills/` already generated (25). |
| KimiCode | `skills` not in capabilities | project-level `.kimi-code/skills/` documented; already generated (25). |
| Mammouth | `mcp` absent + `mcp-config: {}` | fork documents `mcp` servers in `opencode.json`/`mammouth.json`; agent-meta generates none. |
| Codex | `hooks: false` (deliberate) | fork/docs verify the hook contract; kept false by documented `#630` policy (not a doc gap — listed for completeness). |

→ RUNTIME (H9, Continue `skills`): **VERIFIED as a real runtime surface** — `cn` `src/util/loadMarkdownSkills.ts:88-146` (and
IDE-core `core/config/markdown/loadMarkdownSkills.ts`) read `.continue/skills/<name>/SKILL.md` with frontmatter `{name,description}`
(both `min(1)`). But `skills` is **not** a `config.yaml` key (`grep skills` in `@continuedev/config-yaml@1.42.0` → 0 hits), and
agent-meta generates **0** skill artifacts (`.continue/skills/` empty) → the declared `capabilities: […, skills, …]` is
**artefactless** (under-delivery, not an error). Evidence: `docs/analysis/evidence/2026-09-30-runtime-continue.md` §6.

---

## 7. Tally

- **Verified facts** (generated excerpt + fetched doc/source): **Phase-0: 31 · Runtime-addenda: +3** (CO-2 default-template
  roles invalid; `config.local.yaml` INVALID; ZCode `type` is a mandatory discriminator).
- **Hypotheses** (explicitly marked, no doc fact asserted): **Phase-0: 6 — all RESOLVED** (3 VERIFIED / 3 REFUTED) — ZCode `type`
  key → **REFUTED** (H5); Kimi model-ID prefix → **VERIFIED** (H6); Continue `.continue/agents` auto-discovery → **VERIFIED**
  `[STATIC]` surface-dependent (H7); Continue SSE `headers` → **REFUTED** (H8); Continue `skills` surface → **VERIFIED** (H9,
  artefactless); Mammouth bare model alias → **REFUTED** (H10).
- **Doc-contract deviations:** **Phase-0: 9** (Codex 1, ZCode 1, KimiCode 1, Continue 1, Mammouth 5) **· Runtime-addenda: +2**
  (CO-2 default Continue template `roles: [chat, edit, agent]` schema-invalid; `.continue/config.local.yaml` missing required
  `name`/`version`). MM-2 re-classified from doc-derived to **runtime-verified (abort)**.
- **Capability flag mismatches:** 4 over-claims, 4 under-claims, 1 deliberate (documented) restraint.

## 8. Runtime verification (2026-09-30)

All six Phase-0 hypotheses were resolved against installed runtimes/toolchains (Codex parser, `kimi acp`, installed ZCode bundle,
`@continuedev/config-yaml@1.42.0`, `@continuedev/cli 1.5.47`, Mammouth release binary `1.18.31.1`); per-hypothesis annotations were
added inline above (§2.2, §3.1, §4.1, §4.2, §5.1, §6).

| Hypothesis | Verdict | Evidence file |
|---|---|---|
| H5 → ZCode `type` key | **REFUTED** (mandatory discriminator) | `evidence/2026-09-30-runtime-codex-kimi-zcode.md` §3 |
| H6 → Kimi model-ID prefix | **VERIFIED** (58/58 unresolvable) | `evidence/2026-09-30-runtime-codex-kimi-zcode.md` §2 |
| H7 → Continue `.continue/agents` discovery | **VERIFIED `[STATIC]`**, chat surface REFUTED | `evidence/2026-09-30-runtime-continue.md` §4 |
| H8 → Continue SSE `headers` | **REFUTED** (stripped) | `evidence/2026-09-30-runtime-continue.md` §5 |
| H9 → Continue `skills` | **VERIFIED** (runtime surface, 0 artifacts) | `evidence/2026-09-30-runtime-continue.md` §6 |
| H10 → Mammouth bare model alias | **REFUTED** | `evidence/2026-09-30-runtime-mammouth-copilot.md` §2.2 |

Additional runtime deltas: Codex D1 affects **2** files (`agent-meta-manager.toml` + `knowledge-curator.toml`); Continue
`config.yaml` / `config.local.yaml` fail Zod (new CO-2). Consolidated single source of truth:
[`2026-09-30-provider-audit-runtime-consolidation.md`](2026-09-30-provider-audit-runtime-consolidation.md).

## 8. Top recommendations (read-only, no fixes applied)

1. **MM-2 (HIGH):** emit Mammouth `tools:` as a `{tool: true}` map (or drop the field and use `permission`).
2. **MM-3/MM-4:** target `mammouth.json`/`opencode.json` and `AGENTS.md`; retire `MAMMOUTH.md` + `.mammouth/settings.json`.
3. **CX-1:** rename `[mcp_servers.<id>.headers]` → `http_headers`.
4. **KC-1:** use `transport: "sse"` (drop `type`) in `.kimi-code/mcp.json`.
5. **CO-1:** drop the `agents:` block from `.continue/config.yaml` (or move it to `prompts:` / rely on `.continue/agents/`).
6. **ZC-1:** document that `.zcode/agents/` requires the bootstrap (or emit user-level `~/.zcode/agents/`), per the Beta scope.
7. Re-align capability flags per §6.
