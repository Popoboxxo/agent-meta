# Kimi Code (Moonshot AI) — Provider Documentation

> State: agent-meta v0.101.0-beta.5 | Sources: [moonshotai.github.io/kimi-code](https://moonshotai.github.io/kimi-code), [MoonshotAI/kimi-code](https://github.com/MoonshotAI/kimi-code) (npm `@moonshot-ai/kimi-code`), state 2026-09
>
> Verification provenance: V10/V11/V12/V13/V14/V15/V16 in `docs/plans/2026-09-04-verification-results.md`.

---

## What is Kimi Code?

Moonshot AI's official CLI coding agent (TypeScript, npm `@moonshot-ai/kimi-code`).

**Wrong target:** NOT the discontinued Python project `MoonshotAI/kimi-cli` — its
docs remain useful as reference only.

**Naming:** registry key **`KimiCode`** (single CamelCase token, unambiguous vs.
the existing Opencode *model aliases* `kimi`/`kimi-code`). Generated paths are
lowercase **`.kimi-code/`** — NEVER `.kimi/`, and deliberately NOT the cross-tool
`.agents/` convention that multiple tools scan (V10 warning; Kimi Code itself also
scans `.agents/` locations — agent-meta writes only `.kimi-code/` to avoid
cross-provider collisions).

---

## Directory and file structure

```
AGENTS.md                  ← Project context + managed block (shared template)
.kimi-code/
  agents/                  ← Custom sub-agents (Markdown + YAML frontmatter, auto-discovered)
    developer.md
    orchestrator.md
    ...
  mcp.json                 ← MCP config ({"mcpServers": {...}})
  skills/                  ← Skills (<name>/SKILL.md or flat <name>.md)
  snippets/                ← Snippets (generated)
  pending-tasks.md         ← Lifecycle tasks (gitignored)
  3-project/               ← Extensions read by agents at runtime

~/.kimi-code/
  AGENTS.md                ← Global context (all projects)
  agents/                  ← User-level agents
  skills/                  ← User-level skills
  mcp.json                 ← User-level MCP config
  config.toml              ← User config (incl. [[hooks]])
```

---

## Feature comparison with Claude Code

| Feature | Claude Code | Kimi Code |
|---------|------------|-----------|
| Context file | `CLAUDE.md` | `AGENTS.md` (nearest-wins subdirs, like Codex; global `~/.kimi-code/AGENTS.md`; `/init` generates it) |
| Config directory | `.claude/` | `.kimi-code/` |
| Sub-agents | `.claude/agents/*.md` | `.kimi-code/agents/*.md` (auto-discovered, no bootstrap) |
| Rules (auto-load) | `.claude/rules/` | Not configured (`has_rules: false` — unverified) |
| Slash commands | `.claude/commands/*.md` | Not generated (`has_commands: false` — unverified) |
| Hooks | `.claude/hooks/*.sh` + `settings.json` | 20 events, but **user-level `config.toml` only** — not generated (see Hooks) |
| Settings | `.claude/settings.json` | **None generated** (`has_settings: false` — `.kimi-code/local.toml` is machine-specific, see below) |
| Skills | `.claude/skills/` | `.kimi-code/skills/` (`<name>/SKILL.md` or flat `.md`) |
| MCP | `.mcp.json` | `.kimi-code/mcp.json` (`mcpServers` JSON) |

---

## Sub-agents in Kimi Code

Custom agents are **plain Markdown with a YAML frontmatter block** (V10 — the
kimi-cli YAML-spec heritage is disproven). agent-meta uses the **default transform
path** (no new `frontmatter-mechanism` value): `model: inject` per role +
`strip-fields` (`memory`, `temperature`, `top_p`, `top_k`, `stop_sequences`,
`max_output_tokens`) + `strip-claude-lines`.

Native frontmatter fields: `name` (optional, kebab-case, filename fallback),
`description` (required), `whenToUse`, `override`, `tools` (YAML list or
comma-separated string; MCP globs like `mcp__github__*`), `disallowedTools`,
`subagents` (flat allowlist). **Unknown fields are ignored** (documented for
Claude's `model` and OpenCode's `mode`) — agent-meta's injected `model` and
bookkeeping keys are tolerated; missing `name` falls back to the filename.

**Auto-discovery** (V16) — no session bootstrap needed
(`provider-bootstrap.yaml`: `file-based`, `action: none`):

```
explicit > project .kimi-code/agents/ > extra dirs (extra_agent_dirs)
        > user ~/.kimi-code/agents/ > plugin > built-in coder/explore/plan
```

Depth is natively regulated: the 3 built-ins do not dispatch further, custom
agents inherit the allowlist, deeper chains require an explicit `subagents`
frontmatter opt-in. Permission inheritance from the main agent.

---

## MCP

Kimi Code reads `{"mcpServers": {...}}` from `.kimi-code/mcp.json` (user level:
`~/.kimi-code/mcp.json`; project overrides user on name collision). agent-meta
**reuses the wire-identical `mcpServers` JSON format** of the existing
`claude-settings` branch (`format: claude-settings`, V13 — reuse beats a new
format branch).

- Transports: **stdio** (`command`/`args`/`env`/`cwd`), **HTTP** (`url`),
  **SSE** (`transport: "sse"`).
- Optional per-server keys: `headers`, `bearerTokenEnvVar`, `enabled`,
  `startupTimeoutMs`, `toolTimeoutMs`, `enabledTools`/`disabledTools`.
- **No separate secrets file** — Kimi-native env indirection via
  `bearerTokenEnvVar` + `env` map.
- Kimi shows a trust prompt for project-level MCP in untrusted folders.

---

## Hooks

Kimi Code has 20 lifecycle events (only `PreToolUse`, `Stop`, `UserPromptSubmit`
are blockable). Payload: JSON on stdin, snake_case
(`{hook_event_name, session_id, session_title, client_type: "kimi_code_cli", cwd}`
+ event-specific fields); exit 0 = allow, 2 = block (stderr = reason), otherwise
fail-open; JSON stdout `hookSpecificOutput.permissionDecision` supported.

**Configured ONLY via a `[[hooks]]` array in user-level `~/.kimi-code/config.toml`**
(fields: `event`, `matcher` (regex), `command`, `timeout` 1–600 s, default 30;
extra fields fail config load). There is **no hooks-dir mechanism** → no
project-level hook generation: agent-meta sets `has_hooks: false` and mirrors
nothing (#630 pattern).

---

## Skills

Markdown + frontmatter; directory form `<name>/SKILL.md` (recommended, scripts
alongside) or flat `<name>.md` (directory form wins). Frontmatter: `name` /
`description` (required in directory form), `type` (prompt/inline/flow),
`whenToUse`, `disableModelInvocation`, `arguments`. Placeholders: `$ARGUMENTS`,
`$0`/`$1`, `${KIMI_SKILL_DIR}`. agent-meta configures `skills_dir:
.kimi-code/skills` (Kimi additionally scans `.agents/skills/` and user-level
`~/.agents/skills/` — not written by agent-meta, see naming note above).

---

## Model tiers

Kimi K2.x, single-model resolution (no dual-model like `model.main`/`model.lite`).

| Tier | Model ID |
|------|----------|
| `nano` | `kimi-k2.6` |
| `fast` | `kimi-k2.6` |
| `balanced` | `kimi-k2.7-code` |
| `powerful` | `kimi-k2.7-code` |
| `max` | `kimi-k2.7-code` |

---

## Delegation

Two dispatch tools (V16):

- **`Agent`** — single dispatch: `prompt`, `description` (3–5 words),
  `subagent_type` (default `coder`), `resume` (mutually exclusive with
  `subagent_type`), `run_in_background`.
- **`AgentSwarm`** — uniform fan-out: `prompt_template` + `items` array
  (up to 128), aggregated report, single toolcall per response.
  → `parallel_execution: true` (documented fan-out contract).

Handoff: conservative **YAML text block** (`handoff_envelope_support: false`).
Tool whitelist (`config/provider-tools.yaml`, `kimicode`): `Read`, `Write`,
`Edit`, `Grep`, `Glob`, `Bash`, `WebSearch`, `WebFetch`, `Agent`, `AgentSwarm`,
`mcp__*`. `bash_tool_name: Bash` (exact, case-sensitive — V14);
`terminal_tool: Bash`.

**Tool-name drift (known):** template tool names `WebFetch`/`TodoWrite` differ
from the Kimi-native tools `FetchURL`/`TodoList` — they are silently mapped via
the whitelist comments today (`kimicode-silent: [TodoWrite]`).

---

## Policy surface (V15 side-finding)

Kimi Code ships a built-in policy surface — `[[permission.rules]]`
(allow/deny/ask + patterns), `dangerous_command_guard` and `[tools]`
enabled/disabled. This makes an isolation-mechanism revisit possible (today
Kimi Code takes the documented isolation skip path).

---

## agent-meta configuration

### Activate Kimi Code

```yaml
# .meta-config/project.yaml
ai-providers:
  - KimiCode
```

### What does agent-meta generate?

| Artifact | Behavior |
|----------|----------|
| `.kimi-code/agents/*.md` | Regenerated on every sync, stale files deleted |
| `AGENTS.md` (managed block) | Updated on every sync |
| `AGENTS.md` (rest) | Created once, then maintained manually |
| `.kimi-code/mcp.json` | MCP servers (reused `mcpServers` JSON format) |
| Rules / Commands / Hooks / Settings | Not generated (all `has_*: false` — see limitations) |
| `.kimi-code/snippets/`, `.kimi-code/pending-tasks.md` (gitignored), `.kimi-code/3-project/` | Standard agent-meta artifacts |

---

## Deliberate limitations

1. **`has_settings: false`** — the only documented project-level config is
   `.kimi-code/local.toml`, and it is machine-specific (`[workspace]
   additional_dir` only), "typically should not be shared", gitignored by design
   (`/add-dir` auto-creates it). No settings template is generated (V15).
2. **`KIMI_*` env-var overrides** (`KIMI_API_KEY` / `KIMI_BASE_URL` /
   `KIMI_MODEL` / `KIMI_MAX_TOKENS`) are runtime-harness concerns — **out of
   sync.py scope** (doc note only).
3. **Config precedence:** env vars / startup params > config files. The plan's
   original "project > global > startup (highest)" was corrected by V15 —
   project > global is only evidenced for `mcp.json`.
4. **No project-level hooks** — hooks are user-level `config.toml` only; no
   mirroring (#630 pattern).
5. **Tool-name drift** — template-side `WebFetch`/`TodoWrite` vs. Kimi-native
   `FetchURL`/`TodoList` (silently mapped today, see Delegation).

## Open P6 items

- Project-level hook generation — out of scope until Kimi documents a
  project-level hook surface.
- Tool-name drift `WebFetch`/`TodoWrite` vs. `FetchURL`/`TodoList` — potential
  explicit alias mapping.
