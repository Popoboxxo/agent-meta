# Runtime Evidence — Opencode **v1** (real harness load + dispatch errors)

- **Date:** 2026-09-30 · **Repo:** `/home/hermes/repos/agent-meta` · **Branch/HEAD:** `feat/provider-audit-opencode-v2` @ `65a493ec`
- **Runtime:** `opencode --version` → **1.18.31** (npm-global `opencode-ai@1.18.31`); user config `~/.config/opencode/opencode.json` (v1 global).
- **Hypotheses source:** `2026-09-30-provider-audit-docs-part1.md` §3 (H1 = OC1-2 `edit: allow` → `Bad Request`; H4 = OC1-3 unknown-key passthrough).
- **Read-only w.r.t. repo code.** No `git`/branch/commit. Scratch outside repo: `/var/tmp/opencode-audit/opencode-v1/`.
- **Canary (paid LLM turn):** **not executed** — a local parse/debug path *and* real dispatch errors from the live runtime log resolved both hypotheses at zero cost.
- **Commands used:** `opencode --help`, `opencode debug --help`, `opencode agent --help`, `opencode agent list`, `opencode debug agent <name>`, `opencode debug config --print-logs --log-level DEBUG`, `opencode debug v2`, `opencode --pure agent list`.
- **Verdict key:** VERIFIED / REFUTED / UNVERIFIABLE.

---

## H1 — `edit: allow` frontmatter rejected by v1 as `Bad Request`? → **REFUTED**

Two layers tested separately: **(a) parse** and **(b) dispatch**.

### (a) Parse — the `edit` construct is accepted, no error
```
$ opencode debug agent developer      # .opencode/agents/developer.md has `permission: {… edit: allow}`
{ "name":"developer", "mode":"subagent",
  "options": {"version":"2.0.1","prompt_mode":"modern","generated-from":"2-platform/agent-meta-developer.md@2.0.1"},
  "tools": {"invalid":true,"…","bash":true,"read":true,"glob":true,"grep":true,"edit":true,"write":true,"task":true,"webfetch":true,"todowrite":true,"websearch":true,"skill":true} }
# exit 0 — no error, no "Bad Request"

$ opencode debug agent explorer       # .opencode/agents/explorer.md has `permission: {… edit: deny}`
{ "name":"explorer", "mode":"subagent",
  "options": {"version":"1.4.0","prompt_mode":"modern","generated-from":"1-generic/explorer.md@1.4.0"},
  "tools": {"…","edit":false,"write":false,"…} }
# exit 0 — no error
```
`debug agent` resolves the generated `permission:` **map** (42 agents `edit: allow`, 16 `edit: deny`) into an ordered
array `[{permission:"edit",pattern:"**",action:"deny"}, {permission:"edit",pattern:"*",action:"allow"}]` (global rule merged, then
agent rule). Neither the map nor `edit: allow` is a v1 schema violation — the harness parses and dispatches both.

### (b) Dispatch — `Bad Request` **does** occur, but **not** edit-specific
Real subagent dispatches recorded in the live log `~/.local/share/opencode/log/opencode.log` (same runtime/session `run=d74aac2c`,
`providerID=opencode-go modelID=deepseek-v4.1-flash`):
```
$ grep 'AI_APICallError: Bad Request' ~/.local/share/opencode/log/opencode.log
…07:42:20.883Z ERROR … agent=senior-developer mode=subagent error.error="AI_APICallError: Bad Request"
…07:42:48.903Z ERROR … agent=opencode-expert  mode=subagent error.error="AI_APICallError: Bad Request"
…08:32:04.899Z ERROR … agent=developer        mode=subagent error.error="AI_APICallError: Bad Request"
…08:34:32.761Z ERROR … agent=developer        mode=subagent error.error="AI_APICallError: Bad Request"
…08:52:51.751Z ERROR … agent=code-reviewer    mode=subagent error.error="AI_APICallError: Bad Request"
…08:53:31.840Z ERROR … agent=code-reviewer    mode=subagent error.error="AI_APICallError: Bad Request"
```
Agent `edit` values at that time (from generated frontmatter): `senior-developer=allow`, `opencode-expert=allow`,
`developer=allow`, **`code-reviewer=deny`**. The same error class also hits `edit: deny` → the failure does **not** correlate with
`edit: allow`. The identical log shows the neighbouring error classes across many agents independent of edit
(`ProviderHeaderTimeoutError`, `Upstream request failed: Endpoint is unavailable.`, `Internal Server Error`,
`Cannot connect to API`) → the `Bad Request` is a **provider-side (`opencode-go`) request rejection / unstable endpoint**, raised
*after* the v1 runtime parsed the agent and built the provider request.

**Verdict: REFUTED.** The generated `edit`/`permission` construct is neither parse-rejected nor the discriminator for the dispatch
`Bad Request`; OC1-2's "42 `edit: allow` fail, 16 `edit: deny` pass" correlation is not reproducible (an `edit: deny` agent fails too).

---

## H4 — unknown frontmatter keys ignored (passthrough) or rejected? → **VERIFIED (passthrough, not rejected)**

```
$ opencode debug agent developer
"options": {"version":"2.0.1","prompt_mode":"modern","generated-from":"2-platform/agent-meta-developer.md@2.0.1"}
$ opencode debug agent explorer
"options": {"version":"1.4.0","prompt_mode":"modern","generated-from":"1-generic/explorer.md@1.4.0"}
$ opencode debug agent orchestrator
"options": {"version":"8.2.0","prompt_mode":"modern","generated-from":"1-generic/orchestrator.md@8.2.0"}
```
`version`, `prompt_mode`, `generated-from` are collected into the documented pass-through bucket `options`, the agent resolves
(exit 0), and a `--print-logs --log-level DEBUG` run emits **no** unknown-key warning/error. Key coverage of the generated
opencode frontmatter (all 58 files): `version` 58×, `prompt_mode` ~45×, `generated-from` 58× — **`hint` 0×, `based-on` 0×**
(the opencode `agent-transform` already drops those two; the audited key list does not fully apply to this provider).

**Verdict: VERIFIED** — unknown keys are ignored/passed through to `options`, not rejected. (Whether a downstream provider rejects
those options is a provider question; the H1 log shows the `Bad Request` also on agents whose `options` are unremarkable, so no
causal link to the keys is demonstrated.)

---

## Artifact loading (v1 loads the generated agents) → **VERIFIED**

```
$ opencode agent list | grep -cE '^[a-z].* \((primary|subagent|all)\)$'
65          # = 58 generated (.opencode/agents/*.md) + 7 built-ins (build, plan, general, explore, summary, title, compaction)
$ for i in 1 2 3; do opencode agent list | grep -cE '^…$'; done   →  65 65 65
$ opencode --pure agent list | grep -cE '^…$'                     →  65   (independent of the rtk plugin)
```
- All 58 generated roles appear; none missing.
- Read-only role **`explorer`** (`edit: deny`) loads: `debug agent explorer` → `edit:false, write:false`, options passthrough.
- Edit-write role **`developer`** (`edit: allow`) loads: `debug agent developer` → `edit:true, write:true`; resolved content
  (`name`, `description`, `prompt`, `options`) matches the generated `.opencode/agents/developer.md` frontmatter verbatim.
- **Caveat (cold start):** the *first* `debug agent <name>` / `agent list` in a fresh process returned "not found" / built-ins-only
  (7) once, then was deterministic (65) on every subsequent run incl. `--pure`. Non-deterministic first-touch load, not a
  frontmatter defect.

**Verdict: VERIFIED** — v1 reliably loads the generated artifacts (steady state).

## Shadow file (`opencode.jsonc` / global / D2) → **no functional shadow found**

```
$ opencode debug config --print-logs --log-level DEBUG
… loading path=~/.config/opencode/config.json
… loading path=~/.config/opencode/opencode.json
… loading path=~/.config/opencode/opencode.jsonc
… loading path=<repo>/opencode.json
… loading path=<repo>/opencode.jsonc
… loading config from <repo>/.opencode/opencode.json      (absent)
… loading config from <repo>/.opencode/opencode.jsonc     (absent)
```
- The resolved config merges **both** `<repo>/opencode.json` (active: `subagent_depth:3`, `plugin:["rtk-for-opencode"]`,
  `permission`, `mcp`) and `<repo>/opencode.jsonc` (fully commented → contributes nothing). **No override of the generated agents.**
- No `~/.config/opencode/agent(s)/` directory exists and the global config contains no `agent` map → **no global agent shadows the
  project agents**. D2's model-tier shadowing is a generation-time concern, not a runtime file shadow here.

---

## Phase-C-relevant v1 facts
- **v1.18.31 already exposes a v2-shaped permission model:** the v1 `permission:` **map** is normalized to an ordered
  `[{permission,action,pattern}]` **array** in `debug agent`/`debug config`. v1→v2 is therefore a *config-surface* migration, not a
  separate engine here.
- **`opencode debug v2` exists on v1** and emits a v2-style catalog: `{providers:[…225…], default:Effect, small:{…}}`,
  `opencode-go` present. Output is **non-deterministic**: with `--print-logs` it returned 225 providers; a plain run returned
  `{"providers":[], "default":{"_id":"Effect","op":"OnSuccess",…}, "small":{}}` — do not treat a single capture as canonical.
- All generated agents carry `mode: subagent`; the project config has **no `default_agent`** → OC1-1 (no primary entry point) stands.
- Provider `opencode-go`/`deepseek-v4.1-flash` was **unstable** during the evidence window (timeouts, endpoint-unavailable, 5xx, 400).

## Open points
- H1's `Bad Request` root cause is provider-side and **not isolated** here (no request-body capture; provider too flaky for a clean A/B).
  A dedicated minimal canary (`run --agent developer` vs `--agent explorer`, 1 turn each) could falsify/confirm further — **not run** (cost).
- The one-off cold-start "not found" (built-ins-only first load) was not reproduced on demand; impact on real TUI startup unmeasured.
- `options` passthrough is confirmed at the harness layer only; whether any provider rejects `version`/`prompt_mode`/`generated-from`
  as model options remains **UNVERIFIABLE** without a request-body capture.
