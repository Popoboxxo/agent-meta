# Provider Audit — Phase C Runtime Consolidation (Single Source of Truth)

- **Date:** 2026-09-30 · **Repo:** `/home/hermes/repos/agent-meta` · **Branch/HEAD:** `feat/provider-audit-opencode-v2` @ `65a493ec`
- **Phase:** C (consolidation; **read-only** w.r.t. repo code — no git mutation, no branch change)
- **Purpose:** collapse the Phase-0 doc audits (Part 1 + Part 2 + Generation) and the Phase-B/C runtime evidence into one
  verdict surface: the status of the **10 Phase-0 HYPOTHESES**, the newly found runtime facts, the **Opencode v1 vs v2**
  verdict matrix, and the Phase-0 assumptions that runtime **refuted**.
- **Evidence sources (sole factual basis):**
  `evidence/2026-09-30-runtime-opencode-v1.md`, `evidence/2026-09-30-runtime-opencode-v2.md`,
  `evidence/2026-09-30-runtime-codex-kimi-zcode.md`, `evidence/2026-09-30-runtime-claude-antigravity.md`,
  `evidence/2026-09-30-runtime-continue.md`, `evidence/2026-09-30-runtime-mammouth-copilot.md`,
  `evidence/2026-09-30-entry-file-verification.md`.
- **Verdict key:** `VERIFIED` (runtime/source confirms) · `REFUTED` (runtime/source contradicts) · `UNVERIFIABLE`
  (no executable path / no credentials). A `[STATIC]` suffix marks a verdict carried by an authoritative in-binary/official
  contract rather than an executed run, with the runtime layer named as UNVERIFIABLE.
- **Numbering note:** the Phase-0 reports contain exactly 10 explicit HYPOTHESIS markers: Part 1 §7 (a)–(d) = **H1–H4**,
  Part 2 §7 = **H5–H10**. The Opencode **v2** surface produced aspect-level verdicts (OC2-1…OC2-5) rather than new
  numbered hypotheses; it is kept strictly separate in §3.

---

## 1. Status matrix — the 10 Phase-0 HYPOTHESES

**Opencode v1 block (strictly separated from v2):** H1 and H4 were tested against the installed **v1.18.31** harness.

| ID | Short | Provider | Verdict | Evidence command (canonical) | Evidence file |
|---|---|---|---|---|---|
| **H1** | `edit: allow` frontmatter → dispatch `Bad Request` (OC1-2 correlation) | Opencode **v1** | **REFUTED** | `opencode debug agent developer` (exit 0) · `grep 'AI_APICallError: Bad Request' ~/.local/share/opencode/log/opencode.log` → also `agent=code-reviewer` (`edit:deny`) | `runtime-opencode-v1.md` §H1 |
| **H4** | unknown agent frontmatter keys rejected? (OC1-3) | Opencode **v1** | **VERIFIED** (passthrough) | `opencode debug agent developer` → `"options": {"version","prompt_mode","generated-from"}`; `opencode debug config --print-logs --log-level DEBUG` → no unknown-key warning | `runtime-opencode-v1.md` §H4 |

| ID | Short | Provider | Verdict | Evidence command (canonical) | Evidence file |
|---|---|---|---|---|---|
| **H2** | Antigravity hook command resolution base (G-8) | Gemini / Antigravity | **REFUTED** `[STATIC]` — it resolves | in-binary doc: *"The working directory is set to the directory containing `hooks.json`"* → `ls .agents/hooks/antigravity-json-adapter.sh` exists | `runtime-claude-antigravity.md` §2.1 |
| **H3** | Antigravity `"matcher": "*"` accepted (G-9) | Gemini / Antigravity | **VERIFIED** `[STATIC]` | in-binary matcher doc: *"`"matcher": "*"` … Matches all tools."*; `cat .agents/hooks.json` uses it | `runtime-claude-antigravity.md` §2.2 |
| **H5** | ZCode MCP `"type"` key is not contract-conformant | ZCode | **REFUTED** | installed `zcode-app-cli/vendor/zcode.cjs`: `ZVr = preprocess(ljs, discriminatedUnion("type",[…])); .strict()`; `.zcode/config.json` loads `diagnostics: []` | `runtime-codex-kimi-zcode.md` §3 |
| **H6** | KimiCode model ID needs `provider/` prefix | KimiCode | **VERIFIED** | `kimi acp` → `session/set_config_option {configId:"model", value:"kimi-k2.7-code"}` → `error -32603: Model … is not configured`; `kimi provider list --json` keys `kimi-code/…` | `runtime-codex-kimi-zcode.md` §2 |
| **H7** | `.continue/agents/*.md` is auto-discovered | Continue | **VERIFIED** `[STATIC]` (surface-dependent) | `cn` source `core/config/ConfigHandler.ts:161-179` (yaml-only chat surface) · `src/commands/review/resolveReviews.ts:57-89` (`cn review` reads `.md`) | `runtime-continue.md` §4 |
| **H8** | per-server SSE `headers:` is schema-conformant | Continue | **REFUTED** | `@continuedev/config-yaml@1.42.0` parse: `honcho (type=sse) parsedKeys=[name,url,type] headersKept=false` | `runtime-continue.md` §5 |
| **H9** | Continue `skills` surface exists | Continue | **VERIFIED** (runtime source; 0 artifacts) | `cn` `src/util/loadMarkdownSkills.ts:88-146` reads `.continue/skills/<name>/SKILL.md`; `grep skills` in config-yaml → 0; `.continue/skills/` empty | `runtime-continue.md` §6 |
| **H10** | Mammouth bare model alias resolves | Mammouth | **REFUTED** | `mammouth debug agent developer` → `"model":{"providerID":"claude-sonnet-5","modelID":""}`; `mammouth run --model claude-sonnet-5 "ping"` → `ProviderModelNotFoundError` | `runtime-mammouth-copilot.md` §2.2 |

**Tally: 5 VERIFIED / 5 REFUTED / 0 UNVERIFIABLE.** Scope caveats: H2 + H3 are `[STATIC]` only — `agy --help` SIGILLs on this
CPU (`go/sigill-fail-fast`, no `pclmul`), so their runtime layer is UNVERIFIABLE until a pclmul-capable host; H4's *harness*
passthrough is VERIFIED but whether the options reach the provider request body is UNVERIFIABLE (no request-body capture).

### 1.1 Opencode v1 sub-table (the only v1 hypotheses)

| ID | Hypothesis | Runtime observation | Verdict |
|---|---|---|---|
| H1 | 42 `edit: allow` agents are rejected with `Bad Request`, 16 `edit: deny` pass | `debug agent developer` parses both map and shorthand (exit 0); live log shows the identical `AI_APICallError: Bad Request` on `code-reviewer` (`edit:deny`) as on `developer`/`senior-developer`/`opencode-expert` (`edit:allow`) | **REFUTED** |
| H4 | Unknown keys are rejected | Keys land in the documented `options` pass-through bucket; DEBUG run emits no warning | **VERIFIED** |

### 1.2 Opencode v2 block (aspect verdicts, not hypotheses)

v2 was exercised as the real **2.0.20** binary; the OC2-1…OC2-5 doc deviations were re-checked at runtime. Full matrix in §3.
Result: the v1-shaped generated artifacts **still load** on v2 (58/58) via a legacy-compat layer, but the v2-native config
surface (`agents`, `permissions`, `default_agent`, nested `mcp.servers`) is **not** what agent-meta emits.

---

## 2. Newly found runtime facts (not present in Phase 0)

| # | Fact | Evidence |
|---|---|---|
| N1 | **Second invalid Codex TOML:** `knowledge-curator.toml` (invalid at line 100) in addition to `agent-meta-manager.toml` (line 467). Scan: `total=58 valid=56 invalid=2`; both from `SINGLETON_CONSTRAINT_BLOCK` appended after `agent-meta-manager`/`knowledge-curator` serialize; `orchestrator` excluded. | `runtime-codex-kimi-zcode.md` §1.1, §1.3 |
| N2 | Codex rejects the identical bytes through its **own** parser: `CODEX_HOME=<scratch>/invalid-home codex mcp list` → `config.toml:467:13: key with no value, expected '='`. | `runtime-codex-kimi-zcode.md` §1.2 |
| N3 | **`@opencode/cli@2.0.20` is real and installable** (`npm install --prefix … @opencode/cli@latest` rc 0 → `opencode v2.0.20`). v2 is **not** a tag of `opencode-ai` (its `next`/`beta`/`dev` are v1-lineage `0.0.0-*` snapshots) but a **separate package**. | `runtime-opencode-v2.md` §1 |
| N4 | v2 **silently drops** `"subagent_depth": 3` (absent from resolved `debug config`). | `runtime-opencode-v2.md` §2 |
| N5 | v2 **silently drops** flat `"mcp": {…}`; only nested `"mcp": {"servers": {…}}` survives. | `runtime-opencode-v2.md` §2 |
| N6 | v2 validator is **silent on rejection**: wrong-typed `permissions` map / invalid `mode`/`effect` files are dropped from the catalog with `rc=0` and **empty stderr** — a generated artifact can vanish with no sync-time signal. | `runtime-opencode-v2.md` §2.2 |
| N7 | v2 **requires a VCS/project root** for discovery: first run in a scratch dir without a git root returned `[]`; after `git init` + commit all agents loaded. | `runtime-opencode-v2.md` §1 |
| N8 | **No v2 JSON schema exists:** `https://v2.opencode.ai/config.json` → 301→404; the official `opencode.ai/config.json` is the *v1* schema and marks a v2-native config **INVALID** (`Additional properties … 'agents','permissions' were unexpected`). | `runtime-opencode-v2.md` §2, §3 |
| N9 | `opencode debug v2` on v1 is a **model/provider catalog** (`{providers:[…225…], default:Effect, small:{…}}`), **not** a v2 config validator; output is non-deterministic. | `runtime-opencode-v1.md` §Phase-C, `runtime-opencode-v2.md` §3 |
| N10 | **Continue Zod invalids:** `.continue/config.yaml` INVALID (`models[0].roles[2]="agent"` ∉ enum `chat,autocomplete,embed,rerank,edit,apply,summarize,subagent`); `.continue/config.local.yaml` INVALID (required `name`/`version` missing). | `runtime-continue.md` §3 |
| N11 | **CO-2 (new):** `templates/configs/CONTINUE.config-template.yaml:28` `roles: [chat, edit, agent]` is schema-invalid → the default Continue config does not load (fatal). | `runtime-continue.md` §3, §8 |
| N12 | **CO-1 zod-confirmed:** the 58-entry top-level `agents:` block is stripped by `configYamlSchema` → dead config. | `runtime-continue.md` §3 |
| N13 | **Copilot path deviations confirmed on real scratch artifacts** (not only declared contract): `.github/copilot/agents/*.md` vs required `.github/agents` (P-1); `COPILOT.md` vs `.github/copilot-instructions.md` (P-3); `.github/copilot/rules/*.md` vs `.github/instructions/*.instructions.md` (P-4); `.github/copilot/skills/` **empty** vs `.github/skills/<name>/SKILL.md` (P-5). `commands:false` is an underclaim (P-6). | `runtime-mammouth-copilot.md` §3, §4 |
| N14 | **`--check` permanent false-positives:** single-ZCode `rc 1` ("2 file(s) out of sync") and multi-all `rc 1` ("1 file(s) out of sync") directly after a clean sync, despite byte-stable output. | `entry-file-verification.md` §3 |
| N15 | **D8 extension / `bootstrap.py:152-161`:** Gemini + ZCode both inject the *same* marker `<!-- agent-meta:bootstrap-begin -->`; the last writer (ZCode-static) wins and the Gemini `define_subagent` roster is lost. `context.py:753` (`gemini_active = "Gemini" in active`) then deletes the ZCode-sourced block in a ZCode-only project → permanent `--check` false-positive. | `entry-file-verification.md` §6 |
| N16 | **Entry-file first-run drift:** Continue `.continue/rules/project-context.md` and ZCode `AGENTS.md` are **not** byte-idempotent on run1→run2 (ZCode: 3 internal writes per sync, net 0 from run2). | `entry-file-verification.md` §2 |
| N17 | **Mammouth MM-2 runtime-verified:** `mammouth agent list` → `Expected object | undefined, got ["Bash",…] tools`, `RC=1` — the YAML-list `tools:` aborts loading of the whole `.mammouth/agents/` dir. | `runtime-mammouth-copilot.md` §2.1 |
| N18 | KimiCode `.kimi-code/agents/*.md` is a real project-discovery path (`PROJECT_BRAND_DIRS = [".kimi-code/agents"]` from `strings kimi`); ZCode is npm-installable (`zcode-app-cli@3.14.4-30`). | `runtime-codex-kimi-zcode.md` §1, §2.1, §3.1 |
| N19 | Opencode v1 loads 65 agents (58 generated + 7 built-ins), steady-state deterministic (65/65/65, also `--pure`); one-off cold-start "not found" caveat. | `runtime-opencode-v1.md` §Artifact loading |
| N20 | No runtime global agent shadow: `opencode.json` + commented `opencode.jsonc` merge, no `~/.config/opencode/agent(s)/`. D2 is a generation-time concern, not a runtime file shadow. | `runtime-opencode-v1.md` §Shadow file |

**Phase-C verdict-matrix deltas** (feeds §3): the generated Opencode tree **runs on v2 only via the legacy-compat layer**
(map `permission`→`permissions` list, `bash`→`shell`, `task`→`subagent`), while the v2-native keys agent-meta does **not**
emit (`default_agent`, native `permissions` list, nested `mcp.servers`) are exactly the ones that survive. Meanwhile
`subagent_depth` and flat `mcp` — both generated — are the ones silently dropped.

---

## 3. Phase-C verdict matrix — Opencode v1 (1.18.31) vs v2 (2.0.20)

Runtime = v2.0.20 loading the repo's generated `.opencode/agents/*.md` (58) + generated `opencode.json`; v1 column from
`runtime-opencode-v1.md`. Transform need = what `scripts/lib/provider_transform.py` / `agent_sync.py` must still change.

| Aspect | v1 (1.18.31) | v2 (2.0.20) | Transform need for v2 |
|---|---|---|---|
| **Schema / agent frontmatter** | `permission:` **map** native; `tools` map; `mode` | `permissions:` **list** native; `tools`/`permission` are legacy; docs: *"Do not use legacy … permission, tools …"* | **YES** — emit native `permissions` list; drop `tools` (already absent in Opencode output) |
| **Discovery** | `.opencode/agents/*.md` → 58/58 (+7 built-ins) | `.opencode/agents/*.md` → 58/58; JSON `agents` key also accepted; **requires VCS/project root** | MINOR — keep Markdown; ensure a git/project root exists |
| **Permissions** | actions `read/edit/glob/grep/bash/task/todowrite/…`; map normalised to ordered `{permission,action,pattern}` array | native `{action,resource,effect}` list; `bash`→`shell`, `task`→`subagent`; `todowrite` is **not** a v2 action; map accepted via compat | **YES** — rename actions, remap/remove `todowrite`, switch to native list |
| **`default_agent`** | key documented; **absent** in generated config → no primary entry (OC1-1) | key accepted + retained; set to a `mode: subagent` → **no warning, rc 0**; documented fallback to `build` not observable via parse | **YES** — add a valid `default_agent` (or a `mode: primary` entry) |
| **`model#variant`** | no `model:` emitted (0/58); v1 also used bare IDs elsewhere | `provider/model#variant` parsed to `{id, providerID, variant}`; synthetic probe OK | **UNVERIFIABLE on generated artifacts** — agent-meta emits no `model:` for Opencode (0/58) |
| **`shell` / `subagent`** | `bash`, `task` native | `shell`, `subagent` native; `bash`/`task` mapped by compat | **YES** — rename in the transform |
| **`subagent_depth` (config)** | honoured (v1 documented) | **RUNTIME-REJECTED** — silently dropped | **YES** — replace with `subagent` permission gating |
| **flat `mcp` (config)** | v1 shape `"mcp": {name:{…}}` | **RUNTIME-REJECTED** — silently dropped; only `mcp.servers` retained | **YES** — emit nested `mcp.servers` |
| **Official schema** | `opencode.ai/config.json` valid | same v1 schema; v2-native config **INVALID**; no v2 schema (404) | Schema cannot validate v2 — validate against runtime only (and guard silent drops) |
| **Transform verdict** | generated artifacts CONFORMANT (v1 docs) | generated artifacts load only via **legacy compat**; v2-native surface unmet | **Transform to v2 IS required** and must add a silent-drop guard |

**Net:** v1→v2 is a **config-surface migration** (not a separate engine — v1.18.31 already normalises `permission` map to an
action array), but it is **not optional**: action renames (`bash`→`shell`, `task`→`subagent`), `permissions`-list form,
`default_agent`, and config-shape changes (`mcp.servers`; `subagent_depth` removal) are all needed, plus a **sync-time
detection of silently-dropped agents/config** (v2 gives no error signal).

---

## 4. Anti-facts — Phase-0 assumptions refuted by runtime

| # | Phase-0 assumption | Runtime reality | Source |
|---|---|---|---|
| A1 | `edit: allow` is the discriminator for the dispatch `Bad Request` (OC1-2: 42 fail / 16 pass) | Not reproducible: an `edit: deny` agent (`code-reviewer`) fails with the same `AI_APICallError: Bad Request`; same log shows provider-side error classes across agents | `runtime-opencode-v1.md` §H1 |
| A2 | The `Bad Request` is a v1 schema/agent defect | It is raised **after** parse+dispatch, on the provider (`opencode-go`) side; the construct parses cleanly (exit 0) | `runtime-opencode-v1.md` §H1 |
| A3 | ZCode MCP `"type"` key is undocumented / not contract-conformant (H5) | `type` is the **mandatory discriminator** (`discriminatedUnion("type",[…]); .strict()`); the generated values are schema-conformant and required | `runtime-codex-kimi-zcode.md` §3 |
| A4 | Mammouth bare model alias *might* resolve (MM-5 "HYPOTHESIS") | Bare alias never resolves; `ProviderModelNotFoundError` (`claude-sonnet-5/.`); requires `provider/model-id` | `runtime-mammouth-copilot.md` §2.2 |
| A5 | Continue SSE `headers` may be accepted via `requestOptions` (HYPOTHESIS) | Top-level `headers` is **not** in the schema and is **stripped**; correct spelling is `requestOptions.headers` | `runtime-continue.md` §5 |
| A6 | `.continue/agents/*.md` header comment "auto-discovered by Continue" (chat surface) | Chat/profile auto-discovery is **`.yaml`-only**; the `.md` auto-load exists **only** in `cn review` | `runtime-continue.md` §4 |
| A7 | Antigravity hook command points at a non-existent file under a workspace-root base (G-8) | cwd = the dir containing `hooks.json` → `.agents/hooks/antigravity-json-adapter.sh` resolves | `runtime-claude-antigravity.md` §2.1 |
| A8 | D2 model-tier shadowing is a runtime file shadow | No runtime agent/config shadow found (`opencode.json`/`.jsonc` merge, no global agent dir); D2 is a generation-time precedence issue | `runtime-opencode-v1.md` §Shadow file |
| A9 | `opencode debug v2` can act as the v2 config validator | It prints the v2 **model catalog**, not a config schema; output non-deterministic | `runtime-opencode-v1.md` §Phase-C, `runtime-opencode-v2.md` §3 |
| A10 | v2 is a dist-tag/line of `opencode-ai` | v2 is a **separate package** `@opencode/cli` (2.0.20); `opencode-ai` tags remain v1-lineage | `runtime-opencode-v2.md` §1 |
| A11 | Mammouth `settings.json` / `MAMMOUTH.md` are read by the runtime | Neither is read: loader reads `mammouth.json(c)`/`opencode.json(c)` and `AGENTS.md`/`CLAUDE.md`/`CONTEXT.md`; `MAMMOUTH.md` occurs 0× in the binary | `runtime-mammouth-copilot.md` §2.3, §2.4 |

---

## 5. Evidence index

| Evidence file | Scope |
|---|---|
| `evidence/2026-09-30-runtime-opencode-v1.md` | H1, H4, artifact loading, shadow-file, `debug v2` |
| `evidence/2026-09-30-runtime-opencode-v2.md` | install, v1↔v2 schema matrix, silent drops, config shape |
| `evidence/2026-09-30-runtime-codex-kimi-zcode.md` | D1 (2 files), H5, H6 |
| `evidence/2026-09-30-runtime-claude-antigravity.md` | CL-2, H2, H3, `AGENTS.md` vs `CLAUDE.md` |
| `evidence/2026-09-30-runtime-continue.md` | H7, H8, H9, CO-1, CO-2, bare model alias |
| `evidence/2026-09-30-runtime-mammouth-copilot.md` | H10, MM-2 runtime, MM-4, Copilot P-1…P-6 |
| `evidence/2026-09-30-entry-file-verification.md` | entry-file drift, `--check` false positives, D8 extension, harness load reality |

*Consolidation basis: 10 hypotheses (H1–H10) + 20 new runtime facts (N1–N20) + 11 anti-facts (A1–A11) + the v1/v2 matrix.*
