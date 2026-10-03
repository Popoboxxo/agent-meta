# Provider Audit — Online-Doc Contract Comparison (Part 1)

**Date (all accesses): 2026-09-30** · **Repo:** `/home/hermes/repos/agent-meta` · **Branch:** `feat/provider-audit-opencode-v2` @ `65a493ec`
**Phase:** 0 (read-only, no fixes) · **Scope:** Claude, Gemini/Antigravity, Opencode (v1 **and** v2), Copilot
**Method:** fetch official docs → extract the documented contract → compare against what agent-meta actually generates in
`.claude/`, `.gemini/`, `.agents/`, `.opencode/`, `opencode.json(c)`, `.github/` and against the declarations in
`config/ai-providers.yaml` / `config/provider-capabilities.yaml`.
**Network:** `curl` OK (all URLs below returned HTTP 200 unless noted). No doc fact below is stated without a fetched source.
**Local runtime cross-check (bonus evidence, not documentation):** `opencode --version` → **1.18.31** (v1), `opencode debug agent <name>`,
`opencode debug config`, `opencode debug v2`.

## Evidence legend

| Tag | Meaning |
|---|---|
| **VERIFIED** | Doc quote fetched on 2026-09-30 + observable artifact excerpt exists in this repo |
| **HYPOTHESIS** | Not resolvable from docs (e.g. resolution base of a relative path); explicitly marked, no doc fact asserted |
| **RUNTIME** | Observation from the locally installed harness, not a doc claim |

---

## 1. Claude Code

Sources: `https://code.claude.com/docs/en/sub-agents.md`, `/settings.md`, `/hooks.md`, `/skills.md`,
`/memory.md`, `/claude-directory.md`, `/model-config.md`, `/permissions.md`, `/settings-reference.md` (index: `https://code.claude.com/docs/llms.txt`).

### 1.1 Artifact contract (agents)

| Aspect | Documented | Generated (this repo) | Status |
|---|---|---|---|
| Dir | `.claude/agents/` (project), `~/.claude/agents/` (user), managed, plugin | `.claude/agents/*.md` (58 agents) | VERIFIED CONFORMANT |
| Required frontmatter | `name`, `description` — *"Only `name` and `description` are required."* | both present on 58/58 | CONFORMANT |
| Optional fields | `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `omitClaudeMd`, `effort`, `isolation`, `color`, `initialPrompt`, `experimental` | `tools` (YAML list), `model`, `permissionMode`, `memory` used | CONFORMANT |
| Unknown fields | *"Multi-word field names use camelCase … Claude Code ignores a field it doesn't recognize without reporting an error."* | `hint` (57), `version` (58), `prompt_mode` (45), `generated-from` (58), `based-on` (7) | **DEVIATION CL-1** (ignored, no effect) |
| `tools` format | *"as a comma-separated string such as `Read, Grep, Bash` or a YAML list"* | YAML list `[Bash, Read, Write, Edit, Glob, Grep, TodoWrite, Agent]` | CONFORMANT |
| Tool names | `Read, Grep, Glob, Bash, Edit, Write, TodoWrite, Agent, …` | same names | CONFORMANT |
| Model IDs | full IDs accepted, e.g. `claude-opus-4-8`, `claude-sonnet-5`, `claude-haiku-4-5`, `claude-fable-5` | exactly these IDs from `config/ai-providers.yaml` `model-tiers` | CONFORMANT |
| `memory` | `user`/`project`/`local`; enables Read/Write/Edit + `MEMORY.md` load | `memory: project` on 27 agents; `.claude/agent-memory/<agent>/` exists | CONFORMANT |

**Adapter note (context):** Docs — *"Claude reads `AGENTS.md` only when you have no `CLAUDE.md` in your working directory or above it."*
The repo ships **both** root `CLAUDE.md` (5 966 B) and root `AGENTS.md`; `CLAUDE.md` contains **no** `@AGENTS.md` import.
Consequence (doc-derived): Claude Code loads only `CLAUDE.md`; `AGENTS.md` is invisible to Claude in this repo. (Entry/context files are
the sibling agent's surface — recorded here only because it is a doc-verified contract consequence.)

### 1.2 Settings contract

`.claude/settings.json` — shape `{permissions:{allow[],deny[]}, hooks:{PreToolUse:[{matcher?,hooks:[{type:"command",command}]}]}}`.
Docs confirm all three nesting levels and that the local file is gitignored. Deny rules `Bash(rm -rf:*)` use the documented `:*` form:
*"The `:*` suffix is an equivalent way to write a trailing wildcard, so `Bash(ls:*)` matches the same commands as `Bash(ls *)`."* → CONFORMANT.

### 1.3 Commands / hooks

* Commands: `.claude/commands/*.md` — docs: *"Command files: a Markdown file in `.claude/commands/` is the older format and still works."*
  Frontmatter used (`description`, `allowed-tools`, `argument-hint`, `$ARGUMENTS`) is within the documented set → CONFORMANT (with the
  doc's migration advice as recommendation, not a deviation).
* Hooks — see CL-2. Hook location and matcher-omission semantics are conformant (matcher omitted = *"Match all"*).

### 1.4 Verdict: `DEVIATION(3)`

| ID | Sev | Generated excerpt | Doc quote | URL |
|---|---|---|---|---|
| **CL-1** | LOW | `hint: Checks code quality…` / `prompt_mode: modern` / `version: 1.8.0` / `generated-from: …` in `.claude/agents/code-reviewer.md` | *"Only `name` and `description` are required."* … *"Claude Code ignores a field it doesn't recognize without reporting an error."* | https://code.claude.com/docs/en/sub-agents.md |
| **CL-2** | MED | `"command": "bash .claude/hooks/dod-push-check.sh"` (`.claude/settings.json`, 3 PreToolUse entries) | *"Use these placeholders to reference hook scripts relative to the project or plugin root, **regardless of the working directory when the hook runs**: `${CLAUDE_PROJECT_DIR}` …"* | https://code.claude.com/docs/en/hooks.md |
| **CL-3** | LOW | `.claude/agents/orchestrator.md`: `tools: [TodoWrite, Agent, Read, Write]` + `permissionMode: plan` | `plan` = *"Plan mode (read-only exploration)"* | https://code.claude.com/docs/en/sub-agents.md |

CL-3 is an internal inconsistency: `Write` is granted in `tools` while `permissionMode: plan` makes writes read-only. If the intent is the
"orchestrator never edits" gate, the `tools` entry is dead weight; if the intent is edit capability, the mode blocks it.

---

## 2. Gemini / Antigravity

Sources: `https://antigravity.google/docs/subagents/`, `/hooks/`, `/settings/`, `/skills/`, `/slash-commands/`, `/rules/`, `/mcp/`,
`/migration/workflows-to-skills/`, `/cli/reference/` (discovered via `https://antigravity.google/sitemap.xml`).
Note: `/docs/agents` = 404; the agent contract lives at `/docs/subagents/`.

### 2.1 Artifact contract (subagents)

Documented discovery locations (**exact doc table**):

| Location | Path |
|---|---|
| Workspace Customizations | `.agents/agents/<name>.md` or `.agents/agents/<name>/agent.md` |
| Global Customizations | `~/.gemini/config/agents/<name>.md` |
| Plugins | `plugins/<plugin_name>/agents/` |

Documented frontmatter: `name` (required), `description` (required), `tools` (string[]; **Antigravity tool names** e.g.
`view_file`, `replace_file_content`, `grep_search`, `run_command`), `mainAgent` (bool, default true), `subagent` (bool, default true),
`model` (`inherit` | `flash` | `pro`), `commandExecutionPolicy`, `mcpServers`, `skills`/`plugins`.
Doc known-issue: *"Specifying an unmapped or misspelled tool name in the tools list may cause the subagent process to hang during execution."*

Generated: `.gemini/agents/*.md` (58) with **Claude** frontmatter:

```
name: developer
version: 2.0.1
based-on: 1-generic/developer.md@4.0.2
description: 'Developer-Agent für …'
hint: Feature-Implementierung …
prompt_mode: modern
tools:
- Bash
- Read
- Write
- Edit
- Glob
- Grep
- TodoWrite
generated-from: 2-platform/agent-meta-developer.md@2.0.1
model: gemini-3.1-pro-low
```

→ Wrong directory, wrong tool vocabulary, wrong model value, and 4 non-contract fields.

### 2.2 Hooks (conformant — worth recording)

`.agents/hooks.json` exists at the documented workspace path and uses the documented name-keyed map
(`{"<hook-name>": {"PreToolUse": [{"matcher": …, "hooks": [{"type":"command","command": …}]}]}}`) → CONFORMANT (G-8 concerns the command path only).

### 2.3 MCP / settings / skills / commands

* MCP documented: global `~/.gemini/config/mcp_config.json`, workspace `.agents/mcp_config.json`, single `mcpServers` object;
  *"Remote Connection Schema: When declaring remote SSE, Streamable HTTP, or websocket-based MCP connections, you must define the
  `serverUrl` field. Legacy fields like `url` or `httpUrl` are not supported."* Generated: `.gemini/settings.json` →
  `"reqogniloom": {"type": "sse", "url": "${MCP_REQOGNILOOM_URL}/mcp/sse/" …}` (wrong file, and a now-unsupported field).
* Settings: documented config file is `~/.gemini/antigravity-cli/settings.json` (global, CLI) — `.gemini/settings.json` is the **Gemini CLI**
  product's file, not an Antigravity-documented workspace settings path.
* Skills (doc): *"Antigravity defaults to `.agents/skills`, but still maintains backward compatibility for `.agent/skills`."* Generated: `.gemini/skills/`.
* Commands: the slash-command catalog is **built-in only** (`/boost`, `/goal`, `/plan`, `/browser`, …); the customization surface is
  **skills** (`/<skill-name>`, *"Any skill located in `.agents/skills/<name>/` … can be invoked via `/<name>`"*), and legacy workflows
  (`.agents/workflows/<name>.md`) are *"deprecated and will be retired on November 1, 2026"*. Generated: `.gemini/commands/*.toml`
  (`description` + `prompt` with `{{args}}` — the **Gemini CLI** custom-command format, not an Antigravity-documented contract).

### 2.4 Verdict: `DEVIATION(8)`

| ID | Sev | Generated excerpt | Doc quote | URL |
|---|---|---|---|---|
| **G-1** | HIGH | `agents_dir: .gemini/agents` → 58 files in `.gemini/agents/` | Discovery table: workspaces read `.agents/agents/<name>.md` (`<name>/agent.md` also allowed) | https://antigravity.google/docs/subagents/ |
| **G-2** | HIGH | `tools: [Bash, Read, Write, Edit, Glob, Grep, TodoWrite]` | `tools` = *"Explicit list of tools permitted for this subagent (e.g. view_file, replace_file_content, grep_search, run_command)"*; *"an unmapped or misspelled tool name … may cause the subagent process to hang"* | https://antigravity.google/docs/subagents/ |
| **G-3** | HIGH | `model: gemini-3.1-pro-low` (22×), `gemini-3.5-flash-high` (16×), `gemini-3.1-pro-high` (9×), `gemini-3.5-flash-medium` (4×), `gemini-2.0-flash-lite-preview-02-05` (7×) | `model` … *"Model tier used when invoked (inherit, flash, or pro)"*, default `inherit` | https://antigravity.google/docs/subagents/ |
| **G-4** | LOW | no `mainAgent`, `subagent`, `commandExecutionPolicy`, `skills` | same frontmatter table (defaults `true`/`true`/`sandbox`) | https://antigravity.google/docs/subagents/ |
| **G-5** | MED | `.gemini/commands/*.toml` (23 files, `prompt = """…{{args}}…"""`) | Slash-command catalog = built-ins only; customization = skills (`/<skill-name>`); workflows deprecated 2026-11-01 | https://antigravity.google/docs/slash-commands/ · /docs/migration/workflows-to-skills/ |
| **G-6** | MED | `skills_dir: .gemini/skills` | *"Antigravity defaults to `.agents/skills`"* | https://antigravity.google/docs/skills/ |
| **G-7** | HIGH | `.gemini/settings.json` → `"mcpServers": {"reqogniloom": {"type":"sse","url":"${…}/mcp/sse/"}}` | Workspace MCP = `.agents/mcp_config.json`; *"you must define the `serverUrl` field. Legacy fields like `url` or `httpUrl` are not supported."* | https://antigravity.google/docs/mcp/ |
| **G-8** | MED | `.agents/hooks.json` → `"command": "bash ./hooks/antigravity-json-adapter.sh orchestrator-guard.sh"` | Hook example uses `"./scripts/lint.sh"` (no statement of the resolution base) | https://antigravity.google/docs/hooks/ |

**G-8 detail (HYPOTHESIS on mechanism, VERIFIED on filesystem):** the adapter file is **not** at `<repo>/hooks/antigravity-json-adapter.sh`
(root `hooks/` = `0-external`, `1-generic`, `2-platform`); it exists at `.agents/hooks/antigravity-json-adapter.sh` and
`.claude/hooks/antigravity-json-adapter.sh`. The docs do not state whether hook commands resolve relative to the workspace root or to
`.agents/`; under a workspace-root base the command therefore points at a non-existent file. **HYPOTHESIS**, needs a real-repo run.

→ RUNTIME: **REFUTED `[STATIC]` (H2) — the command resolves.** The official in-binary hooks contract (actual `agy` binary) states the
handler command runs via `sh -c` with *"The working directory … set to the directory containing `hooks.json`"* → base = `<repo>/.agents/`,
so `./hooks/antigravity-json-adapter.sh` **exists**, and the adapter resolves `orchestrator-guard.sh` relative to itself (also exists).
The "non-existent under a repo-root base" premise does not apply. Runtime layer still UNVERIFIABLE (`agy --help` SIGILLs on this CPU: no
`pclmul`). Command: `ls .agents/hooks/antigravity-json-adapter.sh`; in-binary doc quote. Evidence:
`docs/analysis/evidence/2026-09-30-runtime-claude-antigravity.md` §2.1.

**G-9 (HYPOTHESIS):** `"matcher": "*"` on `PreToolUse`. The doc states the matcher target is *"Tool name (e.g., run_command)"* and documents no
wildcard; whether `*` is accepted is unverified.

→ RUNTIME: **VERIFIED `[STATIC]` (H3).** The actual in-binary hooks doc documents *"`"matcher": "*"` or `""`: **Matches all tools.**"* and
the generated `.agents/hooks.json` uses `"matcher": "*"` on both `PreToolUse` groups → contract-conformant. Runtime layer UNVERIFIABLE
(`agy` SIGILL, no `pclmul`). Evidence: `docs/analysis/evidence/2026-09-30-runtime-claude-antigravity.md` §2.2.

---

## 3. Opencode v1

Sources (v1 site): `https://opencode.ai/docs/agents/`, `/docs/config/`, `/docs/permissions/`, and the authoritative schema
`https://opencode.ai/config.json` (also the doc's *"source of truth for available fields"*).
Local runtime: **1.18.31** (`opencode --version`) → the installed harness is v1.

### 3.1 Artifact contract

| Aspect | Documented (v1) | Generated | Status |
|---|---|---|---|
| Dir | `.opencode/agents/` | `.opencode/agents/*.md` (58) | CONFORMANT |
| Name | *"The markdown file name becomes the agent name."* | filename = role name; `name:` also present | CONFORMANT |
| Required | `description` — *"This is a required config option."* | present 58/58 | CONFORMANT |
| `mode` | `primary` \| `subagent` \| `all`; *"If no mode is specified, it defaults to all."* | `mode: subagent` on **all 58** | see OC1-1 |
| `permission` | map of documented keys; object-or-shorthand for `read, edit, glob, grep, list, bash, task, external_directory, lsp, skill`, shorthand only for `todowrite, question, webfetch, websearch, doom_loop` | `permission:` map with `read/edit/glob/grep/bash/todowrite/task/webfetch/websearch` | CONFORMANT (schema `PermissionConfig`/`PermissionRuleConfig` matches) |
| Extra keys | *"Any other options you specify in your agent configuration will be passed through directly to the provider as model options."* | `version`, `prompt_mode`, `generated-from` | see OC1-3 |

Observed key distribution: `edit: allow` **42** agents, `edit: deny` **16**; `bash` allow/deny split; 2 patterns use `task: allow`.

### 3.2 Config contract (`opencode.json`)

`subagent_depth: 3` ✔ (documented: *"control how deeply subagents can invoke other subagents … The default is 1"*),
`permission: {edit: {"**": "deny"}, bash: {"**": "deny"}}` ✔ (granular object syntax),
`mcp` flat map keyed by server name ✔ (v1 shape), `plugin: ["rtk-for-opencode"]` ✔ (string entries), `$schema` ✔.
Missing: `default_agent` (documented, and needed for a primary entry point) — see OC1-1.
`opencode.jsonc` (688 B, all keys commented out) coexists with `opencode.json` in the same directory — see OC1-4.

### 3.3 Verdict: `DEVIATION(4)`

| ID | Sev | Generated excerpt | Doc quote | URL |
|---|---|---|---|---|
| **OC1-1** | MED | `.opencode/agents/orchestrator.md`: `mode: subagent`; all 58 agents `mode: subagent`; `opencode.json` has no `default_agent` | *"The default agent must be a primary agent (not a subagent) … If the specified agent doesn't exist or is a subagent, OpenCode will fall back to `build` with a warning."* | https://opencode.ai/docs/config/ |
| **OC1-2** | HIGH | `permission: {read: allow, bash: allow, glob: allow, grep: allow, todowrite: allow, edit: allow}` (42 agents) vs `… edit: deny` (16 agents) | `allow` is a documented v1 value: *"allow — Allow all operations without approval"*; `edit` gates *"write, edit, apply_patch"* | https://opencode.ai/docs/agents/ · /docs/permissions/ |
| **OC1-3** | LOW | `.opencode/agents/developer.md`: `version: 2.0.1`, `prompt_mode: modern`, `generated-from: …` | *"Any other options you specify in your agent configuration will be passed through directly to the provider as model options."* | https://opencode.ai/docs/agents/ |
| **OC1-4** | LOW | `opencode.json` **and** `opencode.jsonc` at repo root | v2 doc (same product family): *"Use one form throughout a directory tree unless you need that behavior."* | https://v2.opencode.ai/docs/config/ |

**OC1-2 — RUNTIME cross-check (the given evidence is confirmed):**
`opencode debug agent developer` (edit: allow) resolves `tools: {"edit": true, "write": true, …}`;
`opencode debug agent code-reviewer` (edit: deny) resolves `tools: {"edit": false, "write": false, …}`.
Both keep `permission` semantics otherwise identical (bash/read/glob/grep/todowrite allow; global `edit/bash ** deny` overridden by the agent rule).
So the generated v1 contract is *valid per docs*, yet 42/58 agents are reported to fail dispatch with `Bad Request` while the 16 `edit: deny`
agents dispatch fine. That makes the correlation **RUNTIME (observed)**, while the mechanism is **HYPOTHESIS**: the request differs only by the
presence of the `write`/`edit` tools, so the most plausible cause is the configured model/provider rejecting that tool payload — not a v1
schema violation. This must be reproduced with `--print-logs` before any fix; nothing in the v1 docs makes `edit: allow` illegal.

→ RUNTIME: **REFUTED (H1).** The correlation is not reproducible: the live log
(`~/.local/share/opencode/log/opencode.log`) records the same `AI_APICallError: Bad Request` for `code-reviewer` (`edit: deny`) as for
`developer`/`senior-developer`/`opencode-expert` (`edit: allow`); the same window shows provider-side classes (`ProviderHeaderTimeoutError`,
`Endpoint is unavailable`, `Internal Server Error`) across agents. `opencode debug agent developer` parses `edit: allow` cleanly (exit 0). The
`Bad Request` is a **provider-side (`opencode-go`) rejection**, not an `edit`/schema defect. Command:
`grep 'AI_APICallError: Bad Request' ~/.local/share/opencode/log/opencode.log`. Evidence:
`docs/analysis/evidence/2026-09-30-runtime-opencode-v1.md` §H1.

**OC1-3 detail:** `opencode debug agent` shows these keys landing in `"options": {"version": …, "prompt_mode": …, "generated-from": …}` — i.e.
the *documented* pass-through bucket for provider model options. Whether the configured provider tolerates those unknown body fields is
**HYPOTHESIS**; the clean fix direction (recommendation only) is to keep agent frontmatter inside the documented field set.

→ RUNTIME: **VERIFIED (H4) — passthrough, not rejected.** `opencode debug agent developer|explorer|orchestrator` (v1.18.31) all resolve
(exit 0) with those keys in `options`; a `--print-logs --log-level DEBUG` run emits **no** unknown-key warning (`--pure` identical). Whether
a downstream provider rejects the options in the request body remains **UNVERIFIABLE** (no request-body capture). Evidence:
`docs/analysis/evidence/2026-09-30-runtime-opencode-v1.md` §H4.

---

## 4. Opencode v2

Sources (v2 site): `https://v2.opencode.ai/docs/agents/`, `/docs/config/`, `/docs/permissions/`.
Note: `https://v2.opencode.ai/config.json` → **404** (the v2 docs point to `opencode.ai/config.json`, which still describes the v1 surface —
defensive-branch loader must not assume a distinct v2 schema URL).

### 4.1 Documented v2 contract

* Locations unchanged: `.opencode/agents/<name>.md`, nested paths become IDs (`team/reviewer.md` → `team/reviewer`).
* Markdown frontmatter fields: `description`, `mode` (`primary|subagent|all`), `model` (`provider/model#variant`), `system` (body), `steps`,
  `hidden`, `color`, `disabled`, `request`, and **`permissions`** = *ordered list* of `{action, resource, effect}`.
* Config keys: **`agents`** (plural map), **`permissions`** (top-level ordered list), `default_agent`, `mcp.servers` (nested), `commands`,
  `skills`, `instructions`, `experimental.policies`.
* Hard rule: *"V1 uses different field and action names. In V2, use **permissions**, **shell**, and **subagent** instead of permission, bash, and task."*
* Hard rule: *"Do not use legacy top-level fields such as temperature, top_p, prompt, permission, tools, disable, or maxSteps in new V2 agent configuration."*
* Selection: *"Set the primary agent used when a session has not selected one: `default_agent` … The selected default must exist, be visible, and support primary use."*
* `steps` replaces `maxSteps`; `hidden` controls visibility only; v2 has no built-in `scout`.

### 4.2 Generated vs v2 — Verdict: `DEVIATION(5)`

| ID | Sev | Generated excerpt | Doc quote | URL |
|---|---|---|---|---|
| **OC2-1** | HIGH | `.opencode/agents/*.md` frontmatter `permission:` **map** (`edit: allow`, `bash: deny`, `todowrite: allow`); 4 agents use `task: allow` | *"Do not use legacy top-level fields such as … `permission` … in new V2 agent configuration."* / *"In V2, use permissions, shell, and subagent instead of permission, bash, and task."* | https://v2.opencode.ai/docs/agents/ · /docs/permissions/ |
| **OC2-2** | HIGH | `opencode.json`: `"permission": {"edit": {"**": "deny"}, "bash": {"**": "deny"}}`, flat `"mcp": {"playwright": {…}}` | *"Define ordered rules … `"permissions": [ { "action": "shell", "resource": "git push *", "effect": "ask" } ]"*; *"`"mcp": { "servers": { "playwright": {…} } }"* | https://v2.opencode.ai/docs/config/ · /docs/permissions/ |
| **OC2-3** | MED | `opencode.json`: `"subagent_depth": 3` | v2 config surface lists `default_agent`, `permissions`, `agents`, `mcp.servers`, `steps` — no `subagent_depth`; subagent launch is gated by the `subagent` permission action (*"The parent agent's subagent permissions control which agents it may launch"*) | https://v2.opencode.ai/docs/config/ · /docs/agents/ |
| **OC2-4** | LOW | JSON-defined agents absent; agents only as markdown; `agents` key unused | *"Define agents under `agents` in any OpenCode configuration file"* (markdown stays valid: *"Frontmatter accepts the same fields as an agents configuration entry."*) | https://v2.opencode.ai/docs/agents/ |
| **OC2-5** | LOW | `version`, `prompt_mode`, `generated-from` in every agent file | v2 field set = `description, mode, model, system, permissions, steps, hidden, color, disabled, request` | https://v2.opencode.ai/docs/agents/ |

**Action-name mapping required for v2:** `bash` → `shell`; `task` → `subagent`; `edit`/`read`/`glob`/`grep`/`webfetch`/`websearch`/`skill`
stay valid as v2 actions; `todowrite` is **not** a v2 action (*"`doom_loop` and `lsp` are not current V2 Core permission actions"* lists the v2
action set; `todowrite` is absent) → generated `todowrite: allow` has no v2 equivalent and would need `edit`/`read`-style re-mapping or removal. (Stated as a mapping consequence of the fetched action table.)

### 4.3 Runtime verdicts — Opencode v2 `2.0.20` (2026-09-30)

Runtime = the real `@opencode/cli` **2.0.20** binary loading the repo's generated `.opencode/agents/*.md` (58) + `opencode.json`.
The v1-shaped generated artifacts **still load** (58/58, plus 7 built-ins) via a legacy-compat layer; the v2-native surface is unmet.

| Deviation | Runtime verdict | Observation (command) |
|---|---|---|
| **OC2-1** `permission:` map / `task` | **RUNTIME-OK (compat)** — doc-nonconformant | map accepted and converted to a `permissions` **list** (`bash`→`shell`, `task`→`subagent`); `opencode debug agents` |
| **OC2-2** config `permission` map + flat `mcp` | **RUNTIME-REJECTED (silent)** | flat `mcp` absent from `opencode debug config`; only nested `mcp.servers` retained |
| **OC2-3** `subagent_depth` | **RUNTIME-REJECTED (silent drop)** | `"subagent_depth": 3` absent from resolved `debug config`; no error |
| **OC2-4** no JSON `agents` | **RUNTIME-OK (md loads)** | `.opencode/agents/` 58/58; JSON `agents` key also accepted; **requires a VCS/project root** (no git → `[]`) |
| **OC2-5** unknown keys `version`/`prompt_mode`/`generated-from` | **RUNTIME-OK (tolerated)** | native probe also accepted `mode:primary`, `model#variant`, `steps`, `hidden`, `color` unchanged |

New v2 facts: `@opencode/cli@2.0.20` is a **separate installable package** (not an `opencode-ai` tag); **no v2 JSON schema exists**
(`v2.opencode.ai/config.json` → 301→404) and the official v1 schema marks a v2-native config **INVALID**; v2's validator is **silent** —
wrong-typed `permissions` and invalid `mode`/`effect` are dropped with `rc=0` and empty stderr. Commands: `npm install @opencode/cli@latest`,
`opencode debug config`, `opencode debug agents --print-logs`, `jsonschema https://opencode.ai/config.json`. Evidence:
`docs/analysis/evidence/2026-09-30-runtime-opencode-v2.md` §1–3.

---

## 5. Copilot

Sources: `https://docs.github.com/api/article/body?pathname=/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions`
(raw article body for `https://docs.github.com/en/copilot/customizing-copilot`), `…/coding-agent/create-custom-agents`,
`https://code.visualstudio.com/docs/copilot/customization/custom-agents`, `/prompt-files`, `/agent-skills`, `/mcp-servers`.

**Important scope note:** in *this* repo Copilot is **not** an active provider (`.meta-config/project.yaml`: `ai-providers: [Claude, Opencode, Gemini]`),
and `.github/` contains **only** `workflows/` — there is **no generated `.github/copilot/` tree**. The verdict below therefore audits the
**declared contract** in `config/ai-providers.yaml` (`Copilot:` block) and `templates/configs/COPILOT.project-template.md` against the docs.
Generated-artifact verification for Copilot must be done in a project that activates it.

### 5.1 Documented contract

* Custom agents: *"Custom agent files use the `.agent.md` extension."* · Workspace: **`.github/agents`** (*"VS Code detects any .md files in the
  `.github/agents` folder of your workspace as custom agents"*); user: `~/.copilot/agents` or `~/.claude/agents`; GitHub cloud agent:
  `<repo>/.github/agents/<name>.agent.md` (*"Edit the filename (the text before `.agent.md`)"*).
  Frontmatter: `description` (**required**), `name`, `argument-hint`, `tools`, `agents`, `model`, `user-invocable`,
  `disable-model-invocation`, `target`, `mcp-servers`, `handoffs`, `hooks`.
* Repository custom instructions: *"These are specified in a `copilot-instructions.md` file in the `.github` directory of the repository."*
  Path-specific: *"one or more `NAME.instructions.md` files within or below the `.github/instructions` directory … The file name must end with `.instructions.md`"* (`applyTo` glob frontmatter). `AGENTS.md` is also supported.
* Skills: project skills live in *"`.github/skills/`, `.claude/skills/`, `.agents/skills/`"*.
* Prompt files: *"Markdown files with the `.prompt.md` extension"* in the *"`.github/prompts` folder"*; *"Skills are available as slash commands in chat, alongside prompt files"*.
* MCP: workspace `.vscode/mcp.json` (*"defines servers in a top-level `servers` object"*) or portable root `.mcp.json` (`mcpServers`).

### 5.2 Verdict: `DEVIATION(6)`

| ID | Sev | Declared (generated contract) | Doc-required | URL |
|---|---|---|---|---|
| **P-1** | HIGH | `agents_dir: .github/copilot/agents` | `.github/agents` | code.visualstudio.com/docs/copilot/customization/custom-agents |
| **P-2** | MED | `agent_ext: .md` | `.agent.md` (VS Code additionally auto-detects any `.md` inside `.github/agents`; GitHub cloud agent requires `.agent.md`) | vscode…/custom-agents · docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-custom-agents |
| **P-3** | HIGH | `context_file: .github/copilot/COPILOT.md`; config comment: *"the native path, `.github/copilot-instructions.md`, is not confirmed"* | `.github/copilot-instructions.md` **is** the documented repository-wide file (now confirmed); `AGENTS.md` also supported | docs.github.com/api/article/body?pathname=/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions |
| **P-4** | MED | `rules_dir: .github/copilot/rules` | `.github/instructions/NAME.instructions.md` (`applyTo` frontmatter) | same as P-3 |
| **P-5** | MED | `skills_dir: .github/copilot/skills` | `.github/skills/` | code.visualstudio.com/docs/copilot/customization/agent-skills |
| **P-6** | MED | `commands: false`, `subagent_dispatch: false`, `native_agent_tools: []` (`config/provider-capabilities.yaml`) | prompt files (`.github/prompts/*.prompt.md`) are a command surface (*"Skills are available as slash commands in chat, alongside prompt files"*); custom agents expose an `agents:` frontmatter property for subagents | vscode…/prompt-files · vscode…/custom-agents |

`mcp-config.committed-file: .vscode/mcp.json` with `format: vscode-settings` is **CONFORMANT** (path documented; `scripts/lib/mcp_provider_config.py`
writes the documented top-level `servers` key for that format).

---

## 6. Cross-provider summary

| Provider | Verdict | HIGH | MED | LOW | Artifacts checked in-repo |
|---|---|---|---|---|---|
| Claude | `DEVIATION(3)` | 0 | 1 | 2 | `.claude/agents/*` (58), `.claude/settings.json`, `.claude/commands/*` (22), `.claude/rules/*`, `.claude/skills/*`, `.mcp.json`, `CLAUDE.md`/`AGENTS.md` |
| Gemini / Antigravity | `DEVIATION(8)` | 4 (G-1,G-2,G-3,G-7) | 3 (G-5,G-6,G-8) | 1 (G-4) | `.gemini/agents/*` (58), `.agents/hooks.json`, `.agents/hooks/*`, `.gemini/settings.json`, `.gemini/commands/*.toml` (23), `.gemini/skills/*` |
| Opencode v1 | `DEVIATION(4)` | 1 (OC1-2) | 1 (OC1-1) | 2 | `.opencode/agents/*` (58), `opencode.json`, `opencode.jsonc`, `.opencode/commands/*` (23) |
| Opencode v2 | `DEVIATION(5)` | 2 | 1 | 2 | same as v1 (re-read against v2 contract) |
| Copilot | `DEVIATION(6)` | 2 (P-1,P-3) | 4 | 0 | declared contract only (provider inactive in this repo; no `.github/copilot/`) |

**Conformant anchors (no action, recorded so a fix does not "repair" them):**
`.claude/agents` required/optional fields & tool names, `.claude/agents` dir, Claude model IDs, Claude settings/hook nesting, matcher-less
hook groups, `:*` deny syntax, `.claude/commands` legacy format, `.claude/rules/`, `.claude/agent-memory/`;
Antigravity `.agents/hooks.json` **location + name-keyed shape**; Opencode v1 `subagent_depth`, flat `mcp`, `plugin`, granular permission
object syntax, `todowrite` (v1-only) under the v1 table; Copilot `.vscode/mcp.json` `servers` shape.

## 7. Findings count & open items

* **VERIFIED deviations:** **Phase-0: 26** (Claude 3 · Antigravity 8 · Opencode v1 4 · Opencode v2 5 · Copilot 6) **· Runtime-addenda: +6**
  (all Opencode v2 runtime: silent `subagent_depth` + flat-`mcp` drops, silent invalid-config drop, project-root discovery requirement,
  separate `@opencode/cli` package, v1-schema-only / no v2 schema).
* **HYPOTHESES:** Phase-0 **4**, all **RESOLVED** — (a) Opencode `edit: allow` `Bad Request` mechanism → **REFUTED** (H1, provider-side);
  (b) Antigravity hook command resolution base → **REFUTED** (H2, resolves `[STATIC]`); (c) `matcher: "*"` acceptance → **VERIFIED** (H3,
  `[STATIC]`); (d) unknown Opencode agent options reaching the provider body → **VERIFIED** at harness layer / **UNVERIFIABLE** at provider
  layer (H4). H2/H3 have no runtime layer (`agy` SIGILL, no `pclmul`).
* **Blockers for Phase 0 → Phase 1:** none of the deviations is a *merge blocker by itself*; the runtime-corrected K1-class item is
  **Antigravity contract drift (G-1/G-2/G-7, agents invisible/unusable — unchanged)**. OC1-2's "`edit: allow` dispatch failure" is
  **withdrawn as an `edit` bug** (H1 REFUTED); the remaining Opencode action item is the **v2 migration + silent-drop guard** (OC2-*).
* **Not covered here (sibling agents):** agent-artifact inventory for all 9 providers (a) and entry/context-file contract (b).
* **No doc fact above is asserted without a fetched source; all accesses 2026-09-30.**

## 8. Runtime verification (2026-09-30)

All four Phase-0 hypotheses were resolved against the installed harnesses v1.18.31 / `agy` binary / v2.0.20 (no paid LLM turn needed);
per-deviation runtime annotations were added inline above (G-8, G-9, OC1-2, OC1-3, §4.3). Summary:

| Hypothesis | Verdict | Evidence file |
|---|---|---|
| H1 → OC1-2 `edit: allow` | **REFUTED** | `evidence/2026-09-30-runtime-opencode-v1.md` §H1 |
| H2 → G-8 hook path | **REFUTED `[STATIC]`** | `evidence/2026-09-30-runtime-claude-antigravity.md` §2.1 |
| H3 → G-9 `matcher:"*"` | **VERIFIED `[STATIC]`** | `evidence/2026-09-30-runtime-claude-antigravity.md` §2.2 |
| H4 → OC1-3 options passthrough | **VERIFIED** (provider layer UNVERIFIABLE) | `evidence/2026-09-30-runtime-opencode-v1.md` §H4 |

Additional runtime deltas: Opencode v1 loads 58/58 generated agents (65 with built-ins), no runtime file shadow; Opencode v2 silently drops
`subagent_depth` and flat `mcp`. Consolidated single source of truth:
[`2026-09-30-provider-audit-runtime-consolidation.md`](2026-09-30-provider-audit-runtime-consolidation.md).
