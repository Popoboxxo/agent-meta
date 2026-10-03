# Provider Audit — AGENT-Artifact Generation (9 Providers)

- **Date:** 2026-09-30
- **Branch / HEAD:** `feat/provider-audit-opencode-v2` @ `65a493ec`
- **Auditor:** `code-reviewer` (Phase 0, read-only w.r.t. production code)
- **Scope:** AGENT artifacts only — agents dir/extension, `agent-transform`, model/tier resolution, Claude-only leftovers, stale-role cleanup + roles whitelist, Codex/ZCode/KimiCode specifics, provider-agnostic sweep, multi-provider collisions. Entry/context files → sibling audit (`2026-09-30-provider-audit-docs-part1.md`).
- **Method:** scratch consumer projects under `.tmp/gen-audit/gen/<Provider>/` (single provider each) + `.tmp/gen-audit/gen/Multi/` (all 9). Per provider: `--dry-run` + one **real** sync in the scratch root, then artifact inspection. Repo root was never synced non-dry-run.
- **Inputs read:** `config/ai-providers.yaml`, `config/provider-capabilities.yaml`, `config/provider-tools.yaml`, `config/provider-bootstrap.yaml`, `config/tier-presets.yaml`, `config/delegation-syntax.yaml`, `config/role-defaults.yaml`, `scripts/lib/{providers,provider_transform,agent_sync,agents,roles,frontmatter,agent_toml,pipelines,io,context,gitignore,bootstrap,isolation,external_tools_drift}.py`, `tests/scenarios/registry.md`, `docs/plans/2026-09-04-verification-results.md`.
- **Ratings:** every finding below is **VERIFIED** by execution unless marked `HYPOTHESIS`.

Artifact inventory: 61 agent files per provider × 9 = **549 generated agent artifacts** (Codex `.toml`, all others `.md`), plus `.agent-meta-managed` index in each agent dir.

---

## 1. Result matrix

| Provider | Verdict | Short |
|---|---|---|
| Claude | OK | baseline: `model`/`memory`/`permissionMode`/`tools` injected as configured; `_KNOWN_TIERS` all resolve |
| Gemini | DEVIATION(1) | body `.claude/...` refs survive the non-Claude transform (D5) |
| Opencode | DEVIATION(1) | body `.claude/...` refs (D5); `opencode-native` frontmatter correct (`mode: subagent`, `permission` map, no `tools`) |
| Continue | DEVIATION(4) | model shadowing → Claude IDs (D2); raw tier token via `model-inherit-fallback` (D3); Claude-only `memory`/`permissionMode` (D4); body refs (D5) |
| Copilot | DEVIATION(3) | no `model:` (config `agent-transform` has no `model:` key, D2-note); body refs (D5); wrong pipeline notation (D6); registry omission (D7) |
| Mammouth | DEVIATION(2) | own `model-tiers` shadowed by preset global fallback (D2); body refs (D5) |
| Codex | DEVIATION(3) | **invalid TOML artifact** (D1); body refs (D5); wrong pipeline notation `task()` vs `spawn_agent` (D6) |
| ZCode | DEVIATION(2) | body refs (D5); wrong pipeline notation (D6); `model: inject` + per-role `model:` works (V9 ✓) |
| KimiCode | DEVIATION(2) | body refs (D5); wrong pipeline notation `task()` vs `Agent`/`AgentSwarm` (D6) |

Global (not provider-scoped): **D8** multi-provider bootstrap collision (Multi only), **D9** dry-run/`--check` blind spot under a gitignored consumer root, **D10** hardcoded provider-name/path leftovers in `scripts/lib`.

`sync.py` exited `0` with **0 errors/tracebacks** for all 14 sync runs (9 single + Multi + Inherit + Overrides + ContEmpty + Stale). None of the deviations below is caught by sync-time validation.

---

## 2. Deviations

### D1 — Codex `agent-meta-manager.toml` is invalid TOML (MAJOR)

**Evidence (verbatim, `Codex/.codex/agents/agent-meta-manager.toml:461-467`):**

```
461: '</output-guard>'
462: ''
463: '"""'
464: ''
465: '## Singleton-Regel: Orchestrator-Spawn (auto-generated)'
466: ''
467: '**NIEMALS** `task(subagent_type="orchestrator", ...)` oder `Agent(subagent_type="orchestrator", ...)` aufrufen.'
```

`tomllib.loads(...)` → `TOMLDecodeError: Invalid statement (at line 467, column 1)`. In Phase 0 it was the **only** one of 61 Codex files that fails to parse; the other 60 parse to exactly `{name, description, model, sandbox_mode, developer_instructions}` (verified).

→ RUNTIME (2026-09-30): **extended to 2 invalid files, not 1.** A real scratch sync (58 `.toml`, identical `scripts/lib` + `config/` + `agents/` as HEAD) yields `total=58 valid=56 invalid=2` — `agent-meta-manager.toml` (line 467) **and** `knowledge-curator.toml` (line 100), both with the `## Singleton-Regel` block after the closing `"""`. Codex's own Rust TOML parser rejects the identical bytes: `CODEX_HOME=<scratch>/invalid-home codex mcp list` → `config.toml:467:13: key with no value, expected '='` (control file parses fine). Evidence: `docs/analysis/evidence/2026-09-30-runtime-codex-kimi-zcode.md` §1.1–1.3, command `python3 -c "import tomllib,pathlib; tomllib.loads(...)"` over `<scratch>/.codex/agents/`.

**Root cause (code, `scripts/lib/agent_sync.py`):** `_finalize_agent_content` calls
`transform_agent_content_for_provider(...)` at **line 681** (which via `frontmatter-mechanism: codex-toml` builds the *complete* TOML document ending in `"""`), then appends the singleton constraint **after** serialization at **lines 752-753**:

```python
if role != "orchestrator" and not role.endswith("-iteration") and can_spawn:
    content = content.rstrip() + SINGLETON_CONSTRAINT_BLOCK
```

For YAML-frontmatter providers appending to the body is valid; for `codex-toml` it lands *outside* `developer_instructions`. `agent-meta-manager` is the only non-orchestrator role with a spawn-capable `tools` entry (`_tools_can_spawn`, agent_sync.py:52), so only it is corrupted. `orchestrator.toml` parses because the singleton text is part of the template body, not appended.

→ RUNTIME: **two roles are corrupted, not one** — `knowledge-curator` (`tools: [Read, Write, Agent, TodoWrite]`) is spawn-capable too; the earlier analysis named only `agent-meta-manager`. See the D1 runtime note above.

**Not covered by tests:** `tests/test_provider_toml_transform.py:85-113` calls the pure transform `_transform(...)` and asserts `lines[-1] == '"""'` — it never runs `_finalize_agent_content`, and no test asserts `tomllib` parseability of the *finalized* Codex file. No post-serialization TOML validation exists in the pipeline (`tomllib` is only referenced in `agent_toml.py` docstring and `mcp_provider_config.py` comment).

**Impact:** Codex cannot load `agent-meta-manager.toml` (config-layer parse error); the role is unavailable in Codex projects.
**Recommended follow-up (no fix in Phase 0):** move the singleton block injection *before* the provider serialization (or fold it into the body builder for `codex-toml`), and add a fail-soft `tomllib` round-trip check after `codex-toml` serialization.

### D2 — Per-provider `model-tiers` are shadowed by the active tier-preset (MAJOR for Continue, MODERATE for Mammouth)

**Observed generated `model:` distributions (`logs/models.txt`):**

```
Claude      claude-sonnet-5(30) claude-haiku-4-5-20251001(19) claude-opus-4-8(12)
Continue    claude-sonnet-5(30) claude-haiku-4-5-20251001(19) claude-opus-4-8(12)   <- identical to Claude
Mammouth    claude-sonnet-5(30) claude-haiku-4-5-20251001(19) claude-opus-4-8(12)
```

`config/ai-providers.yaml` declares Continue `model-tiers: {}` (line 297) and Mammouth
`powerful: claude-opus-5`, `max: claude-fable-5-1` (lines 414-415). Generated Mammouth
`security-auditor` (tier `powerful`) has **`model: claude-opus-4-8`** — the configured
`claude-opus-5` is never emitted. Continue — a non-Claude harness — receives Claude model IDs.

**Root cause (code, `scripts/lib/roles.py:446-461`):**

```python
if "tiers" in preset_data:
    provider_preset_tiers = (preset_data.get("providers") or {}).get(provider, {}).get("tiers") or {}
    direct_model = provider_preset_tiers.get(base_tier) or preset_data["tiers"].get(base_tier, "")
    if direct_model:
        ...
        return direct_model
```

With the default `tier-preset: Normal`, `preset_data["tiers"]` exists for every tier
(`config/tier-presets.yaml:33-38`, all Claude IDs), so `model-tiers` from
`config/ai-providers.yaml` (used only by `_resolve_tier_to_model`, roles.py:291-323) is
reached only when the preset has *no* `tiers` map. `tier-presets.yaml` defines
`providers.<P>.tiers` for Claude/Gemini/Opencode/Codex/ZCode/KimiCode but **not** for
Continue/Copilot/Mammouth → those silently inherit the global Claude tier map.

**Impact:** two sources of truth for per-provider models; `ai-providers.yaml model-tiers`
(and its per-provider intent) is not authoritative whenever any preset is active (i.e. always).
**HYPOTHESIS (unverified):** whether Continue resolves a bare `claude-sonnet-5` (its model field
normally is `provider/model`) — needs a real-repo Continue check before treating as breakage.
→ RUNTIME: **VERIFIED (schema accepts the bare ID) / semantic resolution UNVERIFIABLE.** `@continuedev/config-yaml@1.42.0`
`parseAgentFile("---\nname: x\nmodel: claude-sonnet-5\n---")` → `model="claude-sonnet-5"`, no Zod error
(`agentFileSchema.model = z.string().optional()` — no provider-prefix validation). Whether the `cn` path resolves it
(`AgentFileService.doInitialize → loadModelFromHub`) is UNVERIFIABLE without hub/auth. Evidence:
`docs/analysis/evidence/2026-09-30-runtime-continue.md` §7.
**Recommended follow-up:** either add the three missing providers to every preset, or make the
preset `tiers` map a fallback *behind* `provider_config.model-tiers` (explicit provider mapping wins).

### D3 — Continue `model-inherit-fallback` injects a raw tier token (MAJOR)

**Reproduction:** Continue scratch + `model-override-all: {Continue: balanced}` → generated
frontmatters contain literal tier names, not model IDs:

```
{'balanced': 30, 'powerful': 12, 'fast': 15, 'nano': 4}     # `^model:` values
```

and the sync log confirms the empty resolution:

```
[DEBUG]  Continue/accessibility-specialist  GLOBAL override-all for provider 'Continue' (reversible):
```

**Root cause (code):** `resolve_model` returns `""` for an override-all that cannot be resolved
for the provider (roles.py:356-363 → `_resolve_tier_to_model` finds `model_tiers == {}`). The
Continue-only fallback in `provider_transform.py:290-296` then writes the **unresolved role default**:

```python
if spec.get('model-inherit-fallback'):
    inherit_active = bool((config.get('model-inherit-main-chat') or {}).get(provider))
    if not model and not inherit_active:
        raw = roles_cfg["roles"].get(role, {}).get("model", "")   # e.g. "balanced"
        if raw:
            model = raw
```

`config/role-defaults.yaml` stores **tier names** (`developer: model: balanced`), not model IDs.
`inject_model_field(content, "balanced")` therefore writes `model: balanced`.
**Impact:** any project using `model-override-all` (or a path that empties model resolution) with
Continue gets 61 unresolvable `model:` values. **Recommended follow-up:** resolve the fallback
through `_resolve_tier_to_model` (or drop the fallback when no provider mapping exists).

### D4 — Continue/Mammouth inject Claude-only frontmatter fields (MINOR)

`config/ai-providers.yaml` sets `inject-memory: true` / `inject-permission-mode: true` for
Continue (lines 309-310) and `inject-permission-mode: true` for Mammouth (line 424). Generated
artifacts therefore carry Claude semantics, e.g. Continue `agent-meta-scout.md`:

```yaml
name: agent-meta-scout
...
model: claude-haiku-4-5-20251001
memory: local
alwaysApply: false
---
```

Counts: Continue 35×`memory` + 13×`permissionMode`; Mammouth 13×`permissionMode`; `temperature` 0
everywhere (correctly stripped). Claude/Template bookkeeping fields `version`/`prompt_mode`/
`hint` are present in all providers. **Recommended follow-up:** confirm whether Continue/Mammouth
tolerate these keys; if not, set both flags `false` for them (capability-driven, no code change).

### D5 — Body-level `.claude/...` leftovers in all 8 non-Claude providers (MINOR)

`_strip_claude_specific_lines` (provider_transform.py:642-656) removes only lines that start with
`> **Extension:**` **and** contain `.claude/3-project/`. After placeholder substitution the extension
line carries the provider-local path (`.gemini/3-project/...`), so the rule never fires; other
`.claude/...` references are never touched. Each non-Claude provider still contains these 5 distinct
refs (one file each):

| Ref | File (all providers) |
|---|---|
| `.claude/agents`, `.claude/agents/` | `agent-meta-manager` |
| `.claude/skills/model-override-all/SKILL.md` | `agent-meta-manager` |
| `.claude/commands/evaluate-repository.md` | `agent-meta-scout` |
| `.claude/hooks/pre-release-check.sh` | `release` |

**Impact:** misleading instructions in foreign harnesses (e.g. `release` pointing at a `.claude/hooks`
script that does not exist in a Codex/ZCode/Kimi project). **Recommended follow-up:** template-side
provider-neutral phrasing (or extend the strip rule to all `.claude/` body refs).

### D6 — Pipeline notation silently falls back to Opencode for 4 providers (MODERATE)

**Evidence (verbatim generated excerpt, `Codex/.codex/agents/orchestrator.toml` body, and identically
in KimiCode/ZCode/Copilot `orchestrator`):**

```
### `feature-lifecycle`
Execution mode: parallel_group

1. task(subagent_type="git", prompt="Feature-Branch anlegen") → warten bis abgeschlossen
```

**Code:** `scripts/lib/pipelines.py:757-828` hardcodes `_PROVIDER_NOTATION` for only
`opencode`, `claude`, `mammouth`, `gemini`, `continue`; line 852:
`fmt = _PROVIDER_NOTATION.get(provider_key, _PROVIDER_NOTATION["opencode"])`.

The config-key alternative **already exists and is complete**:
`config/delegation-syntax.yaml` defines all 9 providers — Codex `spawn_agent`/`wait_agent`
(lines 134-143), KimiCode `Agent`/`AgentSwarm` (163-175), Copilot `@<agent>` (104-113),
ZCode `Agent(subagent_type=...)` (152-161). The same generated Codex artifact therefore mixes
correct delegation-syntax(`spawn_agent`) with wrong pipeline-syntax(`task(...)`).
**Impact:** wrong dispatch instructions for Codex/KimiCode/Copilot/ZCode (e.g. `task()` is not a
Codex tool; Copilot has no tool-call dispatch at all). **Recommended follow-up:** source
`_PROVIDER_NOTATION` from `delegation_syntax.<Provider>` or add the four providers + fail-loud on
unknown provider instead of a silent Opencode default.

### D7 — `pipelines.py::KNOWN_PROVIDERS` is a stale duplicate registry (MODERATE)

`scripts/lib/pipelines.py:20`:

```python
KNOWN_PROVIDERS = ("Claude", "Opencode", "Gemini", "Continue", "Mammouth", "Codex", "ZCode", "KimiCode")
```

**Copilot is missing** (the registry has 9 providers at HEAD). Consequences: (a) validation at
`pipelines.py:302` rejects a pipeline that lists `Copilot` under `providers.include/exclude`;
(b) `generate_pipeline_variables` (line 664) never builds a `Copilot` block. The authoritative
registry is `load_providers_config()` / `resolve_providers()` (providers.py:48/180).
**Recommended follow-up:** derive `KNOWN_PROVIDERS` from the provider registry, or fail loud on drift.

### D8 — Multi-provider bootstrap block collision: Gemini overwritten by ZCode (MODERATE, Multi only)

`config/ai-providers.yaml` gives `context_file: AGENTS.md` to Gemini, Opencode, Codex, ZCode and
KimiCode (lines 101, 176, 437, 496, 548). `config/provider-bootstrap.yaml` marks **Gemini**
(generated roster) and **ZCode** (static text) as `mechanism: api-based` /
`action: inject-bootstrap-instructions` → both write the same managed marker
`<!-- agent-meta:bootstrap-begin -->` into the same `AGENTS.md`.

**Evidence:**
- Single-provider: Gemini `AGENTS.md` contains the generated roster (`Lies alle Agenten-Dateien aus .gemini/agents/`); ZCode `AGENTS.md` contains the static text.
- `Multi/AGENTS.md`: exactly **one** bootstrap block, and it is the **ZCode** static text
  (`ZCode lädt Workspace-Level .zcode/agents/ NICHT automatisch …`). The Gemini
  `define_subagent` roster is gone; `define_subagent` occurs only inside ZCode's negative
  statement (`es gibt KEINE define_subagent-API`).
- Overlap analysis confirms `AGENTS.md` is the only shared configured path besides `.meta-viz`
  (`logs/overlap.txt`).

**Impact:** in a Gemini+ZCode project, one provider's session bootstrap is silently lost
(last writer wins). **Recommended follow-up:** merge per-provider bootstrap sub-blocks under
distinct markers, or use one bootstrap writer keyed by provider with a deduplicated render.

→ RUNTIME (2026-09-30): **VERIFIED and extended.** (a) The shared marker is injected at `scripts/lib/bootstrap.py:152-161`
(`config/provider-bootstrap.yaml:16-27` Gemini, `:49-75` ZCode both target `<!-- agent-meta:bootstrap-begin -->`); in a
multi-all project two real writes occur in one sync (`write1` = Gemini roster, `write2` = ZCode-static), net text = ZCode only,
Gemini `define_subagent` roster lost. (b) `context.py:753` (`gemini_active = "Gemini" in active`) plus
`_cleanup_bootstrap_block` (`:737-776`) delete the ZCode-sourced block in a **ZCode-only** project, so `--check` **oscillates
permanently** with no byte drift: single-ZCode `rc 1` ("2 file(s) out of sync"), multi-all `rc 1` ("1 file(s) out of sync").
Evidence: `docs/analysis/evidence/2026-09-30-entry-file-verification.md` §3, §6 (write-instrumented real sync).

### D9 — `--dry-run`/`--check` blind spot when the consumer root is gitignored (MINOR, by design)

**Evidence:** all single-provider dry-runs report 0 agent writes and 61 skips per provider:

```
[SKIP] .gemini/agents/developer.md   (absent (target root gitignored))
```

`io.py:414-468` + `io.py:594-606` deliberately suppress dry-run writes when
`git check-ignore` confirms the target dir is ignored (`is_absent_gitignored_target`); the real
run is unaffected. My scratch roots live under the repo's gitignored `.tmp/`, which triggered this.
**Impact:** a CI `--check` executed inside a gitignored subtree would report "clean" despite
pending agent writes. Not a defect for normal consumer repos, but worth documenting.

→ RUNTIME (2026-09-30): a second, opposite `--check` issue is broader than the gitignored-root blind spot — **permanent
false-positives** in single-ZCode (`rc 1`, "2 file(s) out of sync") and multi-all (`rc 1`, "1 file(s) out of sync") with
byte-stable output (D8/collision). Scoping itself is correct: an in-managed-block edit → `rc 1`, an out-of-block edit → `rc 0`.
Evidence: `docs/analysis/evidence/2026-09-30-entry-file-verification.md` §3.

### D10 — Provider-agnostic sweep: remaining provider-name / hardcoded-path sites (MINOR)

`scripts/lib` contains **no** live `if provider == "Name"` / `provider in (...)` conditional —
grep matches 11 hits, all of them comments/docstrings. Real non-config sites:

| # | File:line | Finding | Config-key alternative |
|---|---|---|---|
| 1 | `context.py:753` | `gemini_active = "Gemini" in active` in `_cleanup_bootstrap_block` | Look up providers whose `provider-bootstrap.yaml` mechanism targets this context file (also covers ZCode — see HYPOTHESIS below) |
| 2 | `pipelines.py:20` | `KNOWN_PROVIDERS` tuple (8, no Copilot, duplicated registry) | `load_providers_config()` / `resolve_providers()` |
| 3 | `pipelines.py:757-828` + `:852` | `_PROVIDER_NOTATION` (5 keys) + silent `opencode` default | `config/delegation-syntax.yaml` (`delegation_syntax.<Provider>`) |
| 4 | `config.py:811` | `inherit.get("Claude")` flat-override validation | `provider_has_capability(pc, "model-overrides-flat")` |
| 5 | `gitignore.py:156`, `:176` | `if "Claude" not in providers` / `provider_config.get("Claude", {})` | capability flag (documented intentional: managed-block path is Claude-gated) |
| 6 | `external_tools_drift.py:153-157` | `_INFRA_ROOT_FALLBACK_DIRS = {"hooks_dir": {"Claude": …}, "commands_dir": {"Claude": …, "Continue": ".continue/prompts"}}` | provider_config keys (already primary path) |
| 7 | `bootstrap.py:136`, `:191`, `:237` | literals `.gemini/GEMINI.md`, `.continue/config.yaml`, `.gemini/agents` | `pc["context_file"]`, `pc["settings_file"]`, `pc["agents_dir"]` |
| 8 | `context.py:2084-2133` | Continue-specific prompt generator hardcodes `"Continue"` | `provider-options.<P>.generate-prompts` (already read) + capability dispatch |
| 9 | `providers.py:67` | embedded fallback provider registry contains only `Claude` | fail-loud or full fallback |
| 10 | `commands.py:17`, `rules.py:38`, `mcp.py:44`, `external_tools.py:58,70-72`, `extensions.py:10` | hardcoded `.claude/...` default path constants | provider_config keys (fallback use only) |

**Correctly config-dispatched (positive findings):** `isolation.py:101-102` (`isolation-mechanism`
+ handler table `:581`), `mcp_provider_config.py:648` (`mcp-config.format`), `runtime_gate.py:94`
(protocol-keyed plugin template), `agent_toml.py` (`codex-toml` mechanism, zero provider names),
`provider_transform.py:389` (`agent-transform` block, no if/elif chain), `agent_sync.py:700`
(`provider_has_capability` for MCP tools). `provider_has_capability` is referenced in 7 sites
across `providers.py`, `roles.py`, `agent_sync.py`.

**HYPOTHESIS (unverified):** `context.py:753` treats the shared bootstrap marker as Gemini-only
while ZCode writes the same marker. In a ZCode-only project the block is re-injected after the
cleanup (observed: block present), so no loss was reproducible; the scenario
"deactivate Gemini, keep ZCode, block removed afterwards" was not run in a real repo.
→ RUNTIME: **VERIFIED (extended).** The marker collision is real (`scripts/lib/bootstrap.py:152-161`); in a ZCode-only project
`context.py:753` deletes the ZCode-sourced block and `--check` never converges (permanent `rc 1`); in multi-all the Gemini
`define_subagent` roster is lost to the ZCode text (last writer wins). See D8 runtime note and
`docs/analysis/evidence/2026-09-30-entry-file-verification.md` §3, §6.

---

## 3. Check-by-check verification

| # | Check | Result |
|---|---|---|
| 1 | agents dir + `agent_ext` match config | **PASS** — `.claude/.gemini/.opencode/.continue` + `.github/copilot` + `.mammouth` + `.zcode` + `.kimi-code` all `*.md`; **Codex `*.toml`** (`ext_ok=True` for all 9) |
| 2 | `agent-transform` honoured | **PASS with notes** — `model: inject` (8/9) / `opencode-native` / `codex-toml`; `tools` keep/filter/skip/remove each observed; `strip-fields` effective (`temperature`=0 everywhere, `reference_standards` stripped from all frontmatters, body prose retained); `strip-claude-lines` partly ineffective (D5); `model-note-flat` log-only; extra-fields present — Codex `sandbox_mode = "workspace-write"`, Continue `alwaysApply: false`; Gemini `body-note: gemini-registration` present and points at configured `AGENTS.md` |
| 3 | Model tiers/aliases + overrides + inherit | **PASS with D2/D3** — `tier-overrides {developer: max}` → preset Normal max `claude-opus-4-8`; `model-overrides {tester: sonnet}` → alias `claude-sonnet-4-6`; `model-inherit-main-chat {Gemini: true}` → all 61 Gemini agents have **no** `model:` (correct); no unresolved/empty tier in the default run; D2/D3 under override paths |
| 4 | No Claude-only leftovers | **PARTIAL** — `temperature`: 0 everywhere ✓; `memory`/`permissionMode`: Continue 35/13, Mammouth 0/13, Claude 35/13 (intentional per config, D4); body `.claude/` refs remain (D5) |
| 5 | Stale cleanup + roles whitelist | **PASS** — `roles: [developer, tester]` → 59 tracked stale files DELETEd **with byte-exact `.sync-backup-<ts>` siblings** (59 backups; `copyeditor.md` backup == pre-delete original), index rewritten to exactly `developer.md`/`tester.md`; foreign unmarked `foreign-notes.md` and provenance-marked-but-untracked `custom-role.md` survived **byte-identical** |
| 6 | Codex/ZCode/KimiCode specifics | **PASS with D1** — Codex 60/61 parse to exactly `{name, description, model, sandbox_mode, developer_instructions}`, no `instructions` key; ZCode all 61 carry per-role `model:` (`glm-5.3` ×42, `glm-5.3-flash` ×19) → `model: inject` is correct, V9 "`model: skip` would be wrong" confirmed; KimiCode all 61 plain Markdown + YAML frontmatter with required `description` (V10 Option A) |
| 7 | Provider-agnostic sweep | **PASS with notes** — 0 live `if provider ==` branches; see D6/D7/D10 |

---

## 4. Verified facts about newer-provider artifacts

- **Codex:** `developer_instructions` is the body field and is always emitted last; header comments carry `generated-from`/`version` (no bookkeeping keys in the document). `sandbox_mode` extra-field present in 60/61.
- **ZCode:** per-role `model:` frontmatter present in all 61 files (V9). `tools: skip` keeps Claude tool names (`Bash, Read, Write, Edit, Glob, Grep, TodoWrite`).
- **KimiCode:** `tools: keep` retains the template list including `TodoWrite` (in `kimicode-silent`) and `Agent`; `version`/`prompt_mode`/`hint` are emitted as unknown-but-ignored fields per V10.
- **Opencode:** `mode: subagent`, `model:`, and a derived `permission:` map (deny list applied: read-only roles get `bash: deny`/`edit: deny`, `git` gets `edit: deny`); no deprecated `tools:` key.

---

## 5. Recommendations (no fixes applied — Phase 0)

1. **D1 (blocker-class):** inject the singleton constraint *inside* the body before provider serialization for `codex-toml`; add a `tomllib.loads` fail-soft assertion for every generated Codex agent.
2. **D2/D3:** make `provider_config.model-tiers` authoritative over preset `tiers`, or extend every preset to all 9 providers; resolve the Continue `model-inherit-fallback` through the tier resolver; decide Continue's intended `model:` semantics (inherit vs Claude IDs).
3. **D6/D7:** derive pipeline notation + provider list from `config/delegation-syntax.yaml` / the provider registry; fail loud instead of defaulting to Opencode.
4. **D8:** give Gemini and ZCode distinct bootstrap sub-markers in `AGENTS.md` (or a merged writer).
5. **D4/D5:** decide provider-by-provider whether `memory`/`permissionMode` and `.claude/...` body refs are acceptable; if not, config flags + template phrasing.
6. **D9/D10:** document the gitignored-root dry-run semantics; port the remaining provider-name literals to capability/config keys (table in D10).

---

## 6. Runtime verification (2026-09-30)

Phase-corrected counts (Phase-0 number kept for traceability):

**Phase-0: 10 deviations (D1–D10) · Runtime-addenda: +2** (D1 second file, D8 extension incl. `bootstrap.py:152-161` +
`--check` oscillation). Additionally **2 Phase-0 HYPOTHESES resolved**: D2's Continue bare-model = schema-accepted /
resolution UNVERIFIABLE; D10's bootstrap-marker hypothesis = VERIFIED (extended).

Delta findings (all commands in `docs/analysis/evidence/`):

| Ref | Delta | Evidence |
|---|---|---|
| D1 | **2** invalid Codex TOMLs, not 1: `agent-meta-manager.toml` (467) + `knowledge-curator.toml` (100); Codex's own parser rejects the identical bytes. | `runtime-codex-kimi-zcode.md` §1 |
| D8 | Shared marker injected at `bootstrap.py:152-161`; multi-all loses the Gemini roster; ZCode-only `--check` `rc 1` permanent (no byte drift). | `entry-file-verification.md` §3, §6 |
| D9 | `--check` permanent false-positives in single-ZCode / multi-all; managed-block scoping itself correct. | `entry-file-verification.md` §3 |
| D2 | Continue bare model ID accepted by schema; hub resolution UNVERIFIABLE. | `runtime-continue.md` §7 |
| D10 | Bootstrap-marker hypothesis VERIFIED (extended). | `entry-file-verification.md` §6 |
| new | Opencode v1 exonerates `edit: allow` (provider-side `Bad Request`); v1 loads 58/58 generated agents; no runtime file shadow. | `runtime-opencode-v1.md` |
| new | Opencode v2 `2.0.20` installable (separate package); silently drops `subagent_depth` + flat `mcp`; v2-native config invalid against the v1 schema. | `runtime-opencode-v2.md` |

Consolidated verdict surface: [`2026-09-30-provider-audit-runtime-consolidation.md`](2026-09-30-provider-audit-runtime-consolidation.md).

---

*Evidence archive (scratch, not part of the repo): `.tmp/gen-audit/gen/logs/` — `*.dry.log`, `*.real.log`, `analyze.txt`, `models.txt`, `codex_keys.txt`, `stale_check.txt`, `overlap.txt`, `pipeline_notation.txt`, `notation_ctx.txt`, `bootstrap_check.txt`, `multi_agents_md.txt`, `overrides_inherit.txt`, `cont_empty2.txt`.*
