# Runtime Evidence — Claude Code + Gemini/Antigravity (real harness load)

- **Date:** 2026-09-30 · **Repo:** `/home/hermes/repos/agent-meta` · **Branch/HEAD:** `feat/provider-audit-opencode-v2` (read-only, no git mutation)
- **Runtimes:** `claude` → **2.1.267** (npm-global, commit `a9e1808c`, platform linux-x64; doctor says latest applied on restart: 2.1.277) · `agy` = Antigravity/Gemini CLI (ELF x86-64, 209 MB, 2026-09-02)
- **Hypotheses source:** `2026-09-30-provider-audit-docs-part1.md` §1 (CL-2) and §2 (G-8 = H2 hook path, G-9 = H3 `matcher:"*"`, subagent-discovery table, tool vocabulary).
- **Read-only w.r.t. repo code.** No checkout/branch/commit. Scratch: `/var/tmp/opencode-audit/claude-antigravity/`.
- **Canary (paid LLM turn): NOT executed.** Real conclusions came from `claude doctor`, `--agent <name>` resolution, hook execution at session start (no model turn), and binary/loader inspection → zero cost.
- **Commands used:** `claude --version`, `claude doctor`, `claude --help`, `claude auth status`, `claude --agent <name>`, `claude --settings <file> --debug hooks` (pty via `script`), `agy --help` (fails), `file`, `strings`, plus shell/Grep/Read on the scratch dump.
- **Verdict key:** VERIFIED / REFUTED / UNVERIFIABLE / STATIC (from the actual runtime binary, not executed).

---

## 1. Claude Code 2.1.267

### 1.1 CL-2 — relative hook command resolves against the hook CWD → **VERIFIED** (fix proven)

(a) Shell-level repro of the generated command (`"command": "bash .claude/hooks/dod-push-check.sh"`):
```
$ cd /home/hermes/repos/agent-meta && bash .claude/hooks/dod-push-check.sh </dev/null ; echo $?   # 0
$ cd /tmp && bash .claude/hooks/dod-push-check.sh </dev/null ; echo $?
bash: .claude/hooks/dod-push-check.sh: Datei oder Verzeichnis nicht gefunden
127
$ cd /tmp && export CLAUDE_PROJECT_DIR=/home/hermes/repos/agent-meta
$ bash "${CLAUDE_PROJECT_DIR}/.claude/hooks/dod-push-check.sh" </dev/null ; echo $?                # 0
```

(b) Real harness execution (SessionStart hook from an external `--settings` file, no LLM turn) — the failure and the fix
side by side in one run (`runtime-probe3.json`: relative command + `${CLAUDE_PROJECT_DIR}` command):
```
[session debug] Hook SessionStart:startup (SessionStart) error:
                bash: .claude/hooks/probe-rel.sh: Datei oder Verzeichnis nicht gefunden
# same run, ${CLAUDE_PROJECT_DIR}-anchored command succeeded → ls-ok.txt lists /repo/.claude/hooks/*

[probe.log  runtime-probe2.json]  PWD=/home/hermes/repos/agent-meta
                                  CLAUDE_PROJECT_DIR=/home/hermes/repos/agent-meta
                                  (hook stdin: "cwd":"/home/hermes/repos/agent-meta", hook_event_name:"SessionStart")
[projectdir-expanded.txt]         /home/hermes/repos/agent-meta      # ${CLAUDE_PROJECT_DIR} expanded by the harness
```

**Mechanism (actual binary, 2.1.267):** the hook process is spawned with `cwd: <launchDir>` and
`env: {…, CLAUDE_PROJECT_DIR: <projectDir>}`; `${CLAUDE_PROJECT_DIR}` inside the command string is replaced by the harness.
**Scope nuance:** in a plain `cd <repo> && claude` (and even `cd <repo>/scripts && claude`) `PWD == CLAUDE_PROJECT_DIR == launch dir`;
project *settings* are read from `<cwd>/.claude/` only (no parent walk — debug: `Broken symlink … <cwd>/scripts/.claude/settings.json`),
so the generated relative path happens to resolve. The cwd-dependency bites whenever hook cwd and the settings' authoring dir diverge
(external `--settings`, forwarded/cloud hooks, worktrees) — exactly the case the docs' placeholder is meant to remove.
→ **CL-2 as a robustness deviation VERIFIED; `${CLAUDE_PROJECT_DIR}` repair VERIFIED.**

### 1.2 Hook nesting `hooks.PreToolUse[].hooks[]` → **VERIFIED accepted**

- `claude doctor` (reads cwd settings, no model call) reports under "Invalid settings" only `.mcp.json` env vars — **no hooks complaint**.
- The same three-level nesting (`hooks.SessionStart[].hooks[]`) ran for real in 1.1 → structure is accepted by the loader.

### 1.3 Agent loading `.claude/agents/*.md` + unknown frontmatter → **VERIFIED**

```
$ claude --agent __bogus__ --debug            # exit 1, no model call
--agent '__bogus__' not found. Available agents: accessibility-specialist, agent-meta-manager, …,
developer, …, orchestrator, …, validator                # 61 names incl. builtins/plugins
# comm -23 <58 repo agent files> <runtime names>  →  (empty): all 58 generated agents load by name
$ claude --agent developer --debug            # session header shows "@developer" → agent active
```
The 58 files carry non-contract frontmatter (`hint`, `version`, `prompt_mode`, `generated-from`, `based-on`) yet load with **no
warning/error**. Harness `/doctor` text (in-binary) states the contract: a file with a `name` that fails validation (e.g. missing
`description`) *never loads*; otherwise `.claude/agents/*.md` (subdirs included) + `~/.claude/agents/*.md` are the load sources.
→ CL-1 is real-but-harmless: unknown fields are ignored silently.

### 1.4 `AGENTS.md` vs `CLAUDE.md` → **VERIFIED** (`AGENTS.md` ignored)

```
$ claude --debug  →  "Loaded 13 CLAUDE.md/rules files: [Project] …/CLAUDE.md, [Project] …/.claude/rules/*.md, [AutoMem] MEMORY.md"
$ grep -c '@AGENTS.md' CLAUDE.md   # 0
```
Both root `CLAUDE.md` (5 966 B) and `AGENTS.md` (26 717 B) exist; only `CLAUDE.md` loads, and it has no `@AGENTS.md` import →
`AGENTS.md` is invisible to Claude in this repo (doc-consistent).

---

## 2. Gemini / Antigravity

**Runtime blocker:** `agy --help` → `SIGILL` (exit 132) — *"This binary was compiled with pclmul enabled, but this feature is not
available on this processor (go/sigill-fail-fast)"*; `/proc/cpuinfo` has no `pclmul`. `GODEBUG=cpu.pclmul=off` / `cpu.all=off` do not
help (GOAMD64=v3 code path). **All `agy` runtime checks are UNVERIFIABLE here.** Substituting the strongest available evidence:
the official hooks/subagent contract **embedded in the actual runtime binary** (its own docs + loader strings) + filesystem checks.

### 2.1 H2 — hook command `bash ./hooks/antigravity-json-adapter.sh …` resolvable? → **REFUTED** (it resolves) [STATIC]

In-binary hooks doc (`# Lifecycle Hooks (hooks.json)`, "Hook Handler Fields → command"):
> `command` … *"run via `sh -c` on Unix … **The working directory is set to the directory containing `hooks.json`**."*

`.agents/hooks.json` → cwd = `<repo>/.agents/` → `./hooks/antigravity-json-adapter.sh` = `<repo>/.agents/hooks/antigravity-json-adapter.sh`
(**exists**), and the adapter resolves its argument `orchestrator-guard.sh` relative to **its own** dir → `.agents/hooks/orchestrator-guard.sh`
(**exists**; adapter header lines 51–59). → the registered command resolves; G-8's "non-existent under a repo-root base" does not apply
under the documented `.agents/` base. *Runtime confirmation still pending (SIGILL).*

### 2.2 H3 — `"matcher": "*"` accepted? → **VERIFIED** [STATIC]

In-binary hooks doc (`### The Matcher`, PreToolUse/PostToolUse grouped by `matcher` regex):
> `"matcher": "*"` or `""`: **Matches all tools.** · `"run_command"` exact · `"run_command\|view_file"` alternation · `"browser_.*"` prefix.

`.agents/hooks.json` uses `"matcher": "*"` on both `PreToolUse` groups → contract-conformant. *Runtime UNVERIFIABLE (SIGILL).*

### 2.3 Subagent discovery for `.gemini/agents/*.md` → **REFUTED** (not discovered) [STATIC]

In-binary customizations doc:
> Workspace root: **`.agents/`** (or `.agent/`,`_agents/`,`_agent/`) at repo root · Global: **`~/.gemini/config/`** · Rules: `GEMINI.md`, `AGENTS.md`, `.agents/rules/*.md`.

Agent-dir literals in the binary: `{workspace}/.agents/agents/{agent_name}/` and `{workspace}/.agents/skills/{skill_name}/SKILL.md`.
There is **no** `.gemini/agents` string; workspace agent discovery is under `.agents/agents/`. The 58 generated files live in
`.gemini/agents/` (which does not exist → `ls: .agents/agents: No such file or directory`) with **Claude** tool names
(`Bash, Read, Write, Edit, Glob, Grep, TodoWrite`) whereas Antigravity subagents expect `view_file`/`replace_file_content`/`run_command`
(in-binary doc known-issue: an unmapped tool name *"may cause the subagent process to hang"*).
→ Generated Gemini agents are **not discovered** (wrong dir + wrong tool vocabulary + wrong `model` value). *Runtime UNVERIFIABLE (SIGILL).*

---

## 3. Open points

- **CL-2:** whether the repo's own `.claude/settings.json` hooks ever run with a cwd ≠ repo root in normal IDE/`--worktree`/cloud
  (forwarded-hook) usage was not exercised — only the external-`--settings` + shell cases were reproduced.
- **Antigravity H2/H3/discovery:** all three are STATIC (in-binary official contract + filesystem) because `agy` SIGILLs on this CPU
  (no `pclmul`). A re-run on a pclmul-capable host / in a real AGY IDE session is required to move them to RUNTIME.
- `claude doctor`: "Last update attempt: success → 2.1.277" while the running binary is 2.1.267 (applied on next restart).
- Raw scratch artifacts: `claude-doctor.txt`, `probe.log`, `projectdir-expanded.txt`, `probe3-debug.txt`, `agent-list.txt`,
  `session-debug.txt`, `subdir-debug.txt`, `agy-hooks-doc` region (strings offsets 475355–475464, 456920–456954, 541145).
