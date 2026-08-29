# HACS Platform Preset Audit (Issue #534)

> **Branch:** `feat/hacs-platform-preset` · **Date:** 2026-08-29 · **Type:** Read-only audit, no code changes.
> **Scope:** Full audit of HACS platform coverage across all agent-meta layers (agents, skills, platform-config, rules/commands/hooks, tests, docs, placeholders), with an implementation spec at the end.
> **Method:** Every claim below carries `path:line` evidence. Issue #534 content (workflow, iron rules, skill requirements) was taken as the verified baseline from the task envelope.

---

## 1. Executive Summary

1. **The platform-defaults infrastructure already exists and works.** The task context assumed `config/platforms/**` was the (empty) location — the real path is `platform-configs/<platform>.defaults.yaml` at the repo root (`scripts/lib/platform.py:8,73`), and it already contains `homeassistant.defaults.yaml` and `sharkord.defaults.yaml`. HACS is the only active platform **without** a defaults file.
2. **All 5 iron-rule areas from #534 (Releases / Entities / Architecture / Flows / Privacy) are already covered** by the 5 committed HACS agent overrides — but the **7-step workflow** and the **`hacs-integration-development` skill** are **missing entirely**, and **live project references** have no mechanism in place. (Quelle: `rules/2-platform/hacs-integration-development.md` → ausgelieferter Skill: `integration-development`)
3. **Zero code changes are required.** The entire HACS preset (skill + defaults + rules) can be delivered with data/config files only: `platform-configs/hacs.defaults.yaml`, `rules/2-platform/hacs-integration-development.md`, a `rules-presets.yaml` entry, and agent patches. `sync.py`, `agents.py`, `platform.py`, `admin-server.py` need no modification.
4. **The consumer-facing Skill channel is `rules/2-platform/<platform>-<name>.md` + `channel: skill` in `config/rules-presets.yaml`** → renders to `.claude/skills/<stem>/SKILL.md` for Claude (verified end-to-end via the `conventions` and `sync-interface` skills, Section 4). Rule sources rendered this way must have **no frontmatter** (the SKILL.md frontmatter is generated).
5. **There is a testing gap:** `scripts/lib/platform.py` has no unit test at all, and no test verifies platform-gated agent/rule generation. A regression test path is proposed in Section 7.
6. **One real content discrepancy found:** `hacs-tester.md` orders E2E *before* release; #534's workflow orders the post-release Dev-Test *after* the Release-Dreiklang (that is the HACS update-path test). Both phases are legitimate but must be reconciled explicitly (Section 3.3).
7. **One doc bug found:** `docs/guides/setup/config-layout.md:100` links to `platform-config.md`, which does not exist.

---

## 2. Inventory: What Exists Today (verified state)

### 2.1 HACS agent overrides (`agents/2-platform/`, commit `2c0ed5b3`)

| File | Frontmatter `name:` | Version | `based-on` | Composition | Patch ops / anchors |
|---|---|---|---|---|---|
| `hacs-code-reviewer.md` | `code-reviewer` | 1.0.0 | `1-generic/code-reviewer.md@1.2.2` (line 4) | `extends` (line 8) | 1× `append-after` → `<persona>` (lines 9–28) |
| `hacs-developer.md` | `developer` | 1.0.0 | `1-generic/developer.md@4.0.1` (line 4) | `extends` (line 16) | 2× `append-after` → `<persona>` (17–38), `<context>` (39–84) |
| `hacs-devops-engineer.md` | `devops-engineer` | 1.0.0 | `1-generic/devops-engineer.md@1.1.3` (line 4) | `extends` (line 8) | 1× `append-after` → `<persona>` (9–19) |
| `hacs-release.md` | `release` | 1.0.0 | `1-generic/release.md@1.5.0` (line 4) | `extends` (line 8) | 1× `append-after` → `<persona>` (9–18) |
| `hacs-tester.md` | `tester` | 1.0.0 | `1-generic/tester.md@2.1.4` (line 4) | `extends` (line 8) | 1× `append-after` → `<persona>` (9–21) |

### 2.2 Home Assistant comparison agents (full-replacement style)

| File | Style | Notes |
|---|---|---|
| `homeassistant-developer.md` | Full template (no `extends`), 200 lines | Uses dotted platform placeholder `{{platform.homeassistant.influxdb_bucket}}` at line 84; references HA rules (`yaml-conventions.md`, `energy-abstraction.md`, …) at lines 111–117 |
| `homeassistant-documenter.md` | Full template, 262 lines | MkDocs-oriented; no platform placeholders |
| `homeassistant-log-analyzer.md` | Full template, 216 lines | References `github.com/hacs` as research source (line 158) |

### 2.3 Other platform assets

- `rules/2-platform/`: `homeassistant-*.md` (7 files incl. `homeassistant-mcp.yaml`), `sharkord-*.md` (2 + 2 `_wf-`), `agent-meta-*.md` (5 + `agent-meta-mcp.yaml`), `gemini-orchestrator-first.md`. **No `hacs-*.md` rule exists.**
- `platform-configs/`: `homeassistant.defaults.yaml`, `sharkord.defaults.yaml`. **No `hacs.defaults.yaml`.**
- `agents/2-platform/sharkord-developer.md`, `sharkord-release.md`: full-replacement (no `extends`); only `agent-meta-developer.md` and the 5 `hacs-*.md` files use composition (`grep -l "extends:" agents/2-platform/*.md`).
- `hooks/2-platform/` and `commands/2-platform/`: **empty** — no platform currently ships hooks or commands.

---

## 3. Layer 1 — Agent Templates vs. Issue #534

### 3.1 Frontmatter conventions observed (documenting the de-facto standard)

- Required fields in 2-platform composition files: `name` (plain role name, matching the file-stem suffix — consumed by `role_from_platform_file`, `scripts/lib/agents.py:496-501`), `version` (Semver string, quoted), `based-on` (`1-generic/<role>.md@<base-version>`), `description`, `hint`, `prompt_mode: modern`, optional `tools` list, `extends`, `patches`.
- `extends` + `patches` are **composition metadata**: stripped from the generated output frontmatter (`scripts/lib/agents.py:910-911`); composition is build-time (`agents.py:1404-1412`), the output contains the full document.
- Patch ops supported: `append`, `append-after`, `replace`, `delete` (`agents.py:882-890`); the HACS files use only `append-after` with XML anchors `<persona>` / `<context>` — this requires `prompt_mode: modern` (all 5 files set it, e.g. `hacs-developer.md:7`).
- **Language:** all HACS patch content is German (consistent with `homeassistant-*` and `sharkord-*` platform content; internal docs are German per the language rules). Code identifiers/commits stay English.
- **Placeholders used in HACS files:** none. The 5 hacs-*.md files contain zero `{{...}}` placeholders (both `{{UPPERCASE}}` and `{{platform.*}}`) — everything is static text. That is the main gap behind finding #534's "live references" requirement.
- **Instruction-bleed check (per `.claude/skills/conventions/SKILL.md:29-38`):** all patches are additive `append-after` on `<persona>`/`<context>` — the base sections' semantics are untouched, so bleed risk is low. The only cross-layer tension is `hacs-tester.md` vs. the generic tester workflow, see 3.3.

### 3.2 Gap matrix: #534 rules vs. HACS agents

| #534 area | hacs-developer | hacs-code-reviewer | hacs-release | hacs-devops | hacs-tester | Verdict |
|---|---|---|---|---|---|---|
| **Releases**: Tag alone insufficient; Tag↔manifest sync; VERSION only with migrator | ✓ lines 38, 67–69 | ✓ gate 10 (line 26) | ✓ lines 15–17 | ✓ lines 16–17 | — | **Covered** |
| **Entities**: unique_id + device_info from entity #1; unique_id never changed; platform == filename | ✓ lines 32, 70 | ✓ gates 3, 4 (lines 19–20) | — | — | — | **Covered** |
| **Architecture**: entry registry in `hass.data`, dynamic count, on-read instead of reset job | ✓ lines 30, 32, 71 | ✓ gate 9 (line 25) | — | — | partial (line 15 "on-read") | **Covered** |
| **Flows**: never validate blocking; correctable → Options; structural data written explicitly | ✓ line 31, 72 | ✓ gates 5–7 (lines 21–23) | — | — | — | **Covered** |
| **Privacy**: diagnostics without secrets; exports never to `/www`; tokens central | ✓ lines 34, 73 | ✓ gate 8 (line 24) | — | ✓ line 18 (token hygiene) | — | **Covered** |
| **Meta-file skeleton** (hacs.json / manifest.json / translations / CI) | ✓ tree lines 44–61 (incl. translations dir + validate.yml) | ✓ gates 1–2 | — | ✓ CI-from-day-1 line 15 | — | **Covered as documentation** (no skeleton generation — correct per constraint: skeletons are skill *content*) |
| **Debugging checklist "geht nicht"** (7 points) | ✓ lines 75–83 (all 7 items) | — | — | — | — | **Covered** |
| **Test trick** (pytest without HA via fake package) | — | — | — | — | ✓ line 15 | **Covered** |
| **7-step workflow** (Ist-Analyse live per API → Konzept → HA-free logic → Build → Tests green → Release-Dreiklang → only then Dev-Test & old-cleanup) | ✗ | ✗ | ✗ | ✗ | ✗ | **MISSING everywhere** |
| **`hacs-integration-development` skill** | ✗ | ✗ | ✗ | ✗ | ✗ | **MISSING** (no rule, no registry entry) |
| **Live references to both repos + both project skills** | ✗ | ✗ | ✗ | ✗ | ✗ | **MISSING** (no placeholder, no fill-in pattern) |
| **Ist-Analyse live per API** (step 1 of workflow) | ✗ | ✗ | ✗ | ✗ | ✗ | **MISSING** |
| **Old-entity cleanup** (final workflow step) | partial: checklist item 1 (`hacs-developer.md:77`) mentions generation check, but no cleanup procedure | — | — | — | — | **Partial** |

### 3.3 Which agent must get what

1. **`hacs-developer.md`** (lead agent for the workflow):
   - Add a "7-Schritte-Workflow" section (fits as third `append-after` on `<persona>` or inside the existing `<context>` patch): Ist-Analyse live per API → Konzept (name/domain rules — already present at line 36, reference it) → HA-free logic modules → Build → tests green → Release-Dreiklang → only then Dev-Test & old-cleanup. Cross-reference the skill (Section 4) instead of duplicating full text.
   - Add old-entity cleanup procedure (extend the debugging checklist item 1 at line 77 into an actionable rule).
   - Bump `1.0.0 → 1.1.0` (new optional section = Minor per `.claude/skills/conventions/SKILL.md:13`). `based-on` stays (base unchanged).
2. **`hacs-tester.md`**: reconcile ordering. Current text (lines 15–18) is correct for the *pre-release* phase (unit → E2E → release). #534 adds the *post-release* phase: the HACS-update test on the dev instance happens **after** the real release (HACS can only serve released versions) plus old-entity cleanup. Fix: rename step 3/4 to "pre-release E2E" and add step 5 "post-release: HACS-Update-Test + Alt-Cleanup" — or keep the tester as-is and put the full ordering only in the workflow skill, with a one-line cross-reference patch here. Recommended: the latter (single source of truth). Bump `1.0.0 → 1.0.1` (clarification = Patch).
3. **`hacs-code-reviewer.md`**: optionally add a gate for the workflow's structural artifacts (e.g. "translations/ + strings.json present") — **not required by #534**, leave out unless a real failure motivates it. No bump needed if untouched.
4. **`hacs-release.md`, `hacs-devops-engineer.md`**: no changes required by #534.

### 3.4 Comparison insight (hacs vs. homeassistant/sharkord)

The `homeassistant-*` and `sharkord-*` agents are full replacements; `hacs-*` uses composition. Composition is the better fit for HACS (generic base stays authoritative for workflow/conventions) and is explicitly supported (`docs/architecture/01-layer-model.md` layer model; `.claude/skills/architecture/SKILL.md:35-56`). Note the naming inconsistency in existing files: `sharkord-release.md` uses `name: sharkord-release` while `hacs-release.md` uses `name: release` — the latter is correct (the `name:` must match the resolved role for the override chain; `role_from_platform_file` keys on the *filename* prefix, `agents.py:496-501`, so this is cosmetic, but the hacs style is the cleaner convention).

---

## 4. Layer 2 — Skill Mechanics (how a consumer-facing Skill is defined and delivered)

### 4.1 There are two distinct "skill" channels

**Channel A — `channel: skill` (rules rendered as SKILL.md).** This is how agent-meta's own `.claude/skills/conventions/SKILL.md` etc. are produced:

1. **Source file:** a plain rule in `rules/1-generic/<name>.md` or `rules/2-platform/<platform>-<name>.md` (platform prefix stripped on output). **The source must have NO frontmatter** — verified: `rules/2-platform/agent-meta-conventions.md:1` starts directly with `# agent-meta — Development Conventions`. If it had frontmatter, it would be duplicated into the skill body.
2. **Registry entry:** `config/rules-presets.yaml`, preset `lazy` (lines 99–147), keyed by the rule's **output stem**:
   ```yaml
   <stem>:
     channel: skill
     skill-description: "English one-liner"
   ```
   Options are documented at `rules-presets.yaml:6-26` (`alwaysApply`, `gemini: skip`, `embed: false`, `channel: skill`, `skill-description`). `skill-description` is English per convention (line 24); fallback = first body line after H1 (`scripts/lib/skill_channel.py:67-76`).
3. **Sync path:** `sync_rules()` (`scripts/lib/rules.py:147`) → collects sources (`collect_rule_sources`, line 112) → resolves options (`resolve_rules`, line 45) → for `channel: skill` + Claude provider with `skills_dir` set, calls `write_skill_channel_rule` (`rules.py:272-278` → `skill_channel.py:86-110`).
4. **Output:** `<provider skills_dir>/<stem>/SKILL.md` with generated frontmatter `name: <stem>` + quoted `description:` (`skill_channel.py:79-83`), body = the rule source after variable + platform substitution (`rules.py:256-265`).
5. **Provider gating:** only Claude (`skill_channel.py:35 PROVIDERS = {"Claude"}`; `provider_supports_skill_channel`, lines 38–42). For providers with `has_rules: false` (e.g. Opencode — rules are embedded into AGENTS.md, `scripts/lib/context.py:500,734-742`) the rule falls back to the normal rules path/embedding. **Consequence:** a HACS skill delivered via this channel is lazy-loaded on Claude and *embedded in AGENTS.md* on Opencode — acceptable for an always-relevant platform workflow, but size matters.
6. **Stale cleanup:** shared managed index `.claude/skills/.agent-meta-managed`, scoped per-caller universe (`skill_channel.py:113-154`; `rules.py:311-322`).

**Channel B — external skills (`config/skills-registry.yaml`).** Git-repo-based packages cloned/linked into consumer projects (`scripts/lib/skills.py:13 EXTERNAL_SKILLS_CONFIG`, `skills.py:98` loader; CLI: `sync.py:147`, resolution at `sync.py:1217`). Schema (`config/skills-registry.yaml:10-90`):
- `repos:` — name → `repo` URL, `local_path` (submodule path under `external/`), `pinned_commit` (verified against the submodule), optional `enabled`.
- `skills:` — name → `approved: true|false` (meta-maintainer quality gate), `repo`, `source` (dir in repo), `entry` (e.g. `SKILL.md`), `role`, `name`, `description`, optional `additional_files`.
- Projects enable via `external-skills` in project.yaml.

**For `hacs-integration-development`, Channel A is the correct fit:** the content lives in agent-meta itself (no third-party repo), must be platform-gated (`hacs-*` prefix → only synced when `platforms: [hacs]`, `rules.py:136-142`), and should be lazy-loaded on Claude. A preset entry for a stem whose source file doesn't exist in a project's platform set is inert (not collected → no output, no error). (Quelle: `rules/2-platform/hacs-integration-development.md` → ausgelieferter Skill: `integration-development`)

### 4.2 Full trace of two existing skills

**`conventions`:** source `rules/2-platform/agent-meta-conventions.md` (68 lines, no frontmatter, uses `{{AGENTS_DIR}}` variable — substituted at sync via `rules.py:261` and `substitute()` in `config.py:1184`) → registry `config/rules-presets.yaml:109-111` (`conventions: {channel: skill, skill-description: "Use before committing changes to agents/, config/ or scripts/lib ..."}`) → output `.claude/skills/conventions/SKILL.md` (frontmatter lines 1–4 = generated `name`/`description`; body = substituted source; also embedded into `AGENTS.md` here because agent-meta itself runs provider Opencode/Claude mixed — the AGENTS.md section text matches the rule body verbatim).

**`sync-interface`:** source `rules/2-platform/agent-meta-sync-interface.md` → registry `rules-presets.yaml:100-102` → output `.claude/skills/sync-interface/SKILL.md` (same mechanics; body references `_wf-sync-interface.md` — a `_`-prefixed knowledge file, which `collect_rule_sources` deliberately skips from rule output, `rules.py:131,140`).

### 4.3 Exact schema summary

| Artifact | Location | Schema |
|---|---|---|
| Skill source rule | `rules/2-platform/hacs-<name>.md` | No frontmatter; `# H1` first line; `{{UPPERCASE}}`/`{{platform.hacs.*}}` allowed; `_`-prefix files are non-rendering knowledge files |
| Preset entry | `config/rules-presets.yaml` → `presets.lazy.<name>` | `channel: skill` + `skill-description: "<English>"` |
| Generated skill | `<skills_dir>/<name>/SKILL.md` | Frontmatter: `name: <name>`, `description: "<desc>"` — generated, never hand-written |

---

## 5. Layer 3 — Platform Defaults (`scripts/lib/platform.py::load_platform_config`)

### 5.1 Exact behavior (evidence)

- **Expected defaults path:** `<agent-meta-root>/platform-configs/<platform>.defaults.yaml` — `PLATFORM_CONFIGS_DIR = "platform-configs"` (`platform.py:8`), path built at `platform.py:73`. **Not** `config/platforms/` (the task context's assumption pointed at a nonexistent path; `config/platforms/` does not exist and nothing references it).
- **Project overrides:** `<project-root>/.claude/platform-config.yaml` (`CLAUDE_PLATFORM_CONFIG`, `platform.py:9`; loaded once for all platforms, `platform.py:63-70`).
- **YAML schema:** a single root key `platform:` → `<platform>:` → flat/nested scalar keys. Nested dicts are flattened to dot-notation keys (`_flatten_yaml_dict`, `platform.py:13-27`) → e.g. `platform.hacs.custom_components_path`.
- **Supported keys:** *anything* under `platform.<platform>.*` — the loader is schema-agnostic; it does not restrict key names. There is **no** built-in `variables/rules/commands/hooks/skills` concept in the platform config; it is purely a **placeholder-value store** for `{{platform.<platform>.<key>}}` substitution into agent and rule sources (callers: `agents.py:1457-1459`, `rules.py:264-265`; both invoked for every provider).
- **Merge semantics:** defaults first, project overrides win, per platform; all active platforms merged into one flat dict (`{**flatten(defaults), **overrides}` then `merged_flat.update(...)`, `platform.py:86,96`). Note: project overrides are *global* — if two active platforms define the same leaf key, the override file applies to both; defaults keys are namespaced by platform so they cannot collide.
- **If the defaults file is missing:** skipped silently (`platform.py:74-76`, comment: "not all platforms need one") — this is the current state for `hacs`.
- **Required-field warning:** a defaults key whose value is `""` and not overridden emits `[WARN]` ("add it to .claude/platform-config.yaml", `platform.py:89-94`). Empty string = required; non-empty = working default. This is exactly the documented contract in both existing defaults files (`platform-configs/homeassistant.defaults.yaml:16-17`, `sharkord.defaults.yaml:16-17`).
- **Unresolved `{{platform.*}}` placeholders** in sources: warning + placeholder remains (`substitute_platform`, `platform.py:119-123`).
- **PyYAML missing:** warning + empty dict (no substitution, `platform.py:51-58`).
- **Wiring in sync:** `sync.py:955-957` loads `platform_vars` for the active `platforms` list from project.yaml and logs the count; `--validate` flows through the same code via `validate_test_repo` (`sync.py:344-420`, rules sync at line ~384).

### 5.2 Do other platforms already have defaults?

Yes — exactly two: `platform-configs/homeassistant.defaults.yaml` (keys: `notify_group`, `notify_admin_group`, `debug_sensor`, `ha_url`, `influxdb_bucket`, `influxdb_org`, `influxdb_measurement_schema`, `influxdb_timezone`, `entities_csv_path`; required = `""`, lines 29–76) and `platform-configs/sharkord.defaults.yaml` (keys: `image_tag`, `min_version`, `service_name`, `host_lan_ip`; lines 20–53). Both headers document the override contract with examples — copy that header style for HACS.

### 5.3 `admin-server.py::_list_platforms` (line 3976–4000)

- Derives the platform list **purely from filename prefixes** in `agents/2-platform/*.md`: for each file stem, it finds the longest known role name (from `role-defaults.yaml` via `_list_roles`, lines 4002–4009) that the stem ends with, and takes the remaining prefix as platform (lines 3989–3997). Plus fixed entries `{"agent-meta", "generic"}` (line 3978).
- **`hacs` is already listed** (from `hacs-code-reviewer.md` etc., committed in `2c0ed5b3`). **Adding `platform-configs/hacs.defaults.yaml` does not change the list** — the function never looks at `platform-configs/`. No admin-server change needed or useful.

---

## 6. Layer 4 — Rules / Commands / Hooks: platform pattern

All three collectors implement the identical three-layer pattern with platform gating (`platforms` comes from `config.get("platforms", [])`):

| Module | Collector | Platform glob | Output name transform | Evidence |
|---|---|---|---|---|
| rules | `collect_rule_sources` | `rules/2-platform/<platform>-*.md` | strip `<platform>-` prefix; platform > generic > external for same name; `_`-files skipped | `rules.py:112-144` (platform loop 136–142, precedence doc 116–118, `_` skip 131/140) |
| commands | `collect_command_sources` | `commands/2-platform/<platform>-*.md` | same | `commands.py:15-41` (platform loop 36–41) |
| hooks | `collect_hook_sources` | `hooks/2-platform/<platform>-*.sh` | same | `hooks.py:61-88` (platform loop 83–88) |

- **A HACS platform rule belongs at `rules/2-platform/hacs-<name>.md`.** It is auto-collected **only** when the consumer's project.yaml contains `platforms: [hacs]` — for all other projects the file is dead weight in the meta repo only. No registration anywhere else is needed.
- **Fourth, separate pattern — per-platform MCP bundle:** `rules/2-platform/<platform>-mcp.yaml` is auto-loaded as MCP servers for projects on that platform (`scripts/lib/mcp.py:79-101`, "Implicit: platform bundles rules/2-platform/<platform>-mcp.yaml"). Existing examples: `homeassistant-mcp.yaml`, `agent-meta-mcp.yaml`. **Optional for HACS:** #534's "Ist-Analyse live per API" would be best served by an HA-API MCP server bundle (`hacs-mcp.yaml`), but that requires an actual MCP server to exist and is out of #534's minimum scope — record as future option, do not spec it now.
- **Commands/Hooks:** no HACS need identified from #534 (no recurring shell command or hook guard). `commands/2-platform/` and `hooks/2-platform/` are currently unused by any platform.

---

## 7. Layer 5 — Tests

### 7.1 Current state

- **Structure:** flat unit/regression tests in `tests/test_*.py`; scenario fixtures in `tests/automated/`, `tests/manual/`, `tests/orchestration/`, `tests/browser/`; deps in `tests/requirements.txt`.
- **Pytest configuration:** there is **no** `pytest.ini` / `pyproject.toml` / `setup.cfg` at the repo root (verified by `ls`). CI runs plain `python -m pytest tests/ -q` after `pip install -r tests/requirements.txt` (`.github/workflows/orchestration-test.yml:40-44`), followed by `python scripts/sync.py --validate` (line 47). `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` is mentioned only in internal reports/conclusions as a local-environment hint (e.g. `docs/conclusions/conclusions-2026-08-29.md:24`), **not** configured anywhere in CI or config files.
- **Platform-related coverage today:**
  - `tests/test_composition_engine.py:85` — end-to-end `extends`+`patches` composition (`test_compose_agent_end_to_end_extends_and_patches`).
  - `tests/test_admin_server.py:229-270` — platform override resolution in the admin UI (agent-meta vs generic), not sync.
  - **`scripts/lib/platform.py` has zero test coverage** — no test imports `load_platform_config` or `substitute_platform` (grep over `tests/*.py`: no hits).
- **`--validate` semantics:** `validate_test_repo` (`sync.py:344-420`) performs a full sync into a throwaway test repo (path from `AGENT_META_TEST_REPO` env or `test-repo.path` in project.yaml — configured at `.meta-config/project.yaml:257`), covering agents, context, rules (+skill channel), hooks, commands, snippets, external skills per provider, then fails on errors in the resulting `sync.log`. Consistency checks always run before it (`sync.py:895-924`).

### 7.2 Recommendation: `tests/test_platform_hacs_preset.py`

Model after `tests/test_sync_check_flag.py` (sys.path bootstrap, lines 8–13). Three test tiers:

1. **Unit — platform config loading:** tmp dir as `agent_meta_root` with `platform-configs/hacs.defaults.yaml`, tmp project with/without `.claude/platform-config.yaml`:
   - merged flat dict contains `platform.hacs.<key>` with default and override values;
   - empty-string default + no override → warning emitted via `SyncLog` (assert log records), matching `platform.py:89-94`;
   - missing defaults file → empty contribution, no error (`platform.py:74-76`).
2. **Unit — collection & role mapping:** `role_from_platform_file("hacs-developer.md", ["hacs"]) == "developer"` (`agents.py:496-501`); `collect_rule_sources(root, ["hacs"])` includes `("hacs-integration-development.md", ...)` with output name stripped, and does **not** include it when `platforms=["homeassistant"]` (`rules.py:136-142`).
3. **Integration — tmp-project sync (the regression the task asks for):** build a minimal consumer project (project.yaml with `platforms: [hacs]`, provider Claude with `skills_dir`), run `sync_agents_for_provider` + `sync_rules` (same call shapes as `validate_test_repo`, `sync.py:359-391`), then assert:
   - `.claude/agents/developer.md` contains the HACS persona section (composition applied, e.g. "Eiserne Regeln") and its frontmatter has **no** `extends`/`patches` keys (`agents.py:910-911`);
   - `.claude/rules/integration-development.md` exists (non-skill-channel providers) and for Claude `.claude/skills/integration-development/SKILL.md` exists with generated frontmatter (`skill_channel.py:79-83`) — **(Correction, test-verifiziert):** the audit originally claimed the un-stripped literal paths `.claude/{rules,skills}/hacs-integration-development...`; `collect_rule_sources` strips the platform prefix (`rules.py:141`) and `resolve_rules` keys on the output stem, so the engine can only ever produce the stripped-stem paths (pinned by `tests/test_platform_hacs_preset.py`, Tier 2 preset test + Tier 3 skill-path assertions);
   - `{{platform.hacs.*}}` placeholders are substituted for defined keys; a defined-as-empty required key warns; no `{{UPPERCASE}}` residue beyond the warn-list (`config.py:1221-1228`).
   Run: `python -m pytest tests/test_platform_hacs_preset.py -q` (add to the existing CI command implicitly — CI runs the whole `tests/` dir).

---

## 8. Layer 6 — Documentation touchpoints

- **Structure:** `docs/` has `architecture/01-layer-model.md … 07-se-cascade.md`, `guides/setup/` (config-layout, first-steps, instantiate-project, upgrade-guide), `plans/` (audit/report files like this one), `CODEBASE_OVERVIEW.md` (numbered top-level sections, German, "Letzte Aktualisierung" header, currently 15 sections ending with Review-Agent-Fleet).
- **`docs/architecture/01-layer-model.md`:** documents agents/rules/hooks layer flows (lines 5–47) but has **no mention of `platform-configs/` or `{{platform.*}}` substitution** — the platform-config layer is undocumented in the architecture doc. A short "Platform Config" subsection (defaults file path, override file, required-empty convention) belongs here, next to the Rules diagram (lines 17–29).
- **`docs/guides/setup/config-layout.md`:** already documents `.claude/platform-config.yaml` ("Ebene 3", lines 27, 91–100) but **links to `platform-config.md`, which does not exist** (line 100 → `docs/guides/setup/platform-config.md` missing). Either create that file during implementation or fix the link.
- **`docs/CODEBASE_OVERVIEW.md`:** add a short section (or a subsection under "3. Agent-Templates" / "4. Konfiguration") listing the HACS platform preset files; keep the "Letzte Aktualisierung" convention.
- **`docs/guides/setup/instantiate-project.md`:** mention `platforms: [hacs]` as an option and the required `.claude/platform-config.yaml` overrides (per the conventions skill's "Adding a New Agent Role" step 3 analog, `.claude/skills/conventions/SKILL.md:45`).
- **Reconciliation note (task 9):** the three skill docs match the code accurately on versioning (`06-versioning.md` diagram = conventions skill rules), composition syntax (`architecture` skill ↔ `agents.py:882-890`), and escape syntax (`architecture` skill ↔ `config.py:1202-1210`). Two gaps between docs and code: (a) the `platform-configs/` defaults layer is in code + config-layout guide but **not** in the architecture skill/doc; (b) `conventions` skill says `.claude/agents` is generated (`SKILL.md:10`) while the repo also generates `.opencode/agents` etc. (AGENTS.md wording) — pre-existing wording nit, out of scope.

---

## 9. Layer 7 — Project-specific values ("live references")

- **Mechanism inventory:** (1) `{{UPPERCASE}}` variables from project.yaml `variables` via `build_variables()` → `substitute()` (`config.py:1184-1236`); undefined variable → warn + placeholder remains (`config.py:1226-1228`); escape hatch `{{%VAR%}}` renders literal (`config.py:1202-1210`, documented in `.claude/skills/architecture/SKILL.md:68-83`). (2) `{{platform.<platform>.<key>}}` from `platform-configs/<platform>.defaults.yaml` + project `.claude/platform-config.yaml` overrides (Section 5). (3) Conditional blocks `{{#if VAR}}` stripped per provider (`agents.py:1456`).
- **Why `{{platform.hacs.*}}` is the right tool for #534's live references:** the "both repos + both project skills" values are **project-specific, not platform constants** — exactly the override use case the defaults-file contract was built for (empty string = required → sync warns until the project fills `.claude/platform-config.yaml`, `platform.py:89-94`). This gives validation + substitution everywhere (agents *and* rules) without touching `build_variables()`, the CLAUDE.md variables table, or the config schema — and it matches the established `homeassistant`/`sharkord` precedent (e.g. `rules/2-platform/homeassistant-notifications.md:7-21` uses 3 platform placeholders).
- **Rejected alternative:** `{{GROSS_MIT_UNTERSTRICH}}` project variables would require a new variable per consumer project in `build_variables()` + CLAUDE.md documentation + schema implications, and would leak HACS-specific names into the generic variable namespace. A "hier eintragen" (fill-in-at-runtime) pattern was rejected because it defeats sync-time validation and produces agents that silently ship unfilled references.
- **Caveat to document in the skill:** placeholders in the *skill rule source* are substituted at sync time; **(Correction, test-verifiziert):** the original caveat claimed a consumer who never sets the override gets a WARN and a literal `{{platform.hacs....}}` in the generated file — that is wrong for the shipped keys. Actual behavior (`platform.py:115-123`, pinned by `tests/test_platform_hacs_preset.py` Tier 1/Tier 3): a **defined but empty (required) key** is a known key and is substituted to the **empty string** (with the required-field WARN at load time, `platform.py:89-94`); a **literal placeholder** remains only for keys that are **undefined** in both defaults and overrides (`substitute_platform` warns + keeps `match.group(0)`, `platform.py:119-123`). The fallback note in the skill therefore covers the undefined-key edge case (e.g. a placeholder added to the rule without a defaults entry), while empty-string substitution is the expected state for un-overridden required keys.

---

## 10. Implementation Spec (final)

**Everything below is data/config only — no changes to `sync.py`, `scripts/lib/*.py`, `admin-server.py`, schema, or `.gitmodules`.**

### 10.1 New files

1. **`platform-configs/hacs.defaults.yaml`** — copy the header style of `sharkord.defaults.yaml:1-18`. Keys (minimal set):
   ```yaml
   platform:
     hacs:
       custom_components_path: "custom_components"   # working default
       dev_instance_url: ""      # REQUIRED — dev HA instance for post-release Dev-Test
       integration_repo_url: ""  # REQUIRED — live reference: the integration repo
       reference_repo_url: ""    # REQUIRED — live reference: second repo (e.g. home-assistant/core)
       project_skills: ""        # REQUIRED — comma-separated names of the two project skills
   ```
   (Exact key names are the implementer's choice; keep ≤ 6 keys and the required-empty convention. `domain` is intentionally **not** included — an integration repo can contain multiple domains; the skill text handles it.)
2. **`rules/2-platform/hacs-integration-development.md`** — **no frontmatter** (Section 4.1), starts with `# HACS Integration Development`. Content from #534: the 7-step workflow (incl. Ist-Analyse live per API and the post-release Dev-Test + old-entity cleanup, with the pre-/post-release distinction from Section 3.3), the meta-file skeleton as *inline example blocks* (hacs.json / manifest.json / translations / CI — content in the skill, no generator), and the live-reference block using `{{platform.hacs.*}}` placeholders with the placeholder-fallback note from Section 9. Iron rules stay in the agents (single source: reference them, don't duplicate). **(Correction, Issue #534):** this spec inverted the design — implemented is the opposite: the skill is the **single source of truth for the full iron-rules version** (with rationale/failure class), while `hacs-developer` keeps compact always-on anchors; on rule changes, reconcile **both files** (agent anchors ↔ skill tables). The inversion is covered by Issue #534 but was not annotated here — unlike the test-verified corrections above.
3. **`tests/test_platform_hacs_preset.py`** — per Section 7.2.

### 10.2 Edited files

4. **`config/rules-presets.yaml`** — add to `presets.lazy` (after line 147):
    ```yaml
    integration-development:
      channel: skill
      skill-description: "Use when developing a HACS custom integration — 7-step workflow from live Ist-Analyse to release and dev-instance verification."
    ```
   (English description per `rules-presets.yaml:24` convention.) **(Correction, test-verifiziert):** the audit originally specced the key as the un-stripped literal `hacs-integration-development`; that key can never match because `collect_rule_sources` strips the platform prefix (`rules.py:141`) and `resolve_rules` keys options on the output stem `integration-development` — the original entry was inert and would have rendered the HACS skill as a plain rule (pinned by `tests/test_platform_hacs_preset.py`, Tier 2 preset-resolution test). Key naming follows the `conventions` precedent (`rules/2-platform/agent-meta-conventions.md` → preset key `conventions`).
5. **`agents/2-platform/hacs-developer.md`** — add 7-step workflow section + old-entity cleanup (Section 3.3.1); bump `version: "1.0.0" → "1.1.0"`; `based-on` unchanged.
6. **`agents/2-platform/hacs-tester.md`** — cross-reference the workflow skill / clarify pre- vs post-release phases (Section 3.3.2); bump `1.0.0 → 1.0.1`.
7. **Docs:** `docs/architecture/01-layer-model.md` (Platform-Config subsection), `docs/guides/setup/config-layout.md` (fix or materialize the `platform-config.md` link, line 100), `docs/guides/setup/instantiate-project.md` (platforms option), `docs/CODEBASE_OVERVIEW.md` (HACS preset entry + header date).

### 10.3 Explicitly NOT done (constraint compliance)

- No skeleton *generator* anywhere — the meta-file skeleton lives as example text inside the skill (constraint: "keine Skeleton-Generierung im Meta-Repo").
- No submodule edits; no changes under `external/`, `.gitmodules`, `.agent-meta/`.
- No new `{{GROSS_MIT_UNTERSTRICH}}` placeholder → no CLAUDE.md variables-table entry needed; `{{platform.hacs.*}}` placeholders are self-documenting via the defaults-file header (established pattern, `sharkord.defaults.yaml:9-17`).
- No admin-server change — `_list_platforms` needs nothing (`admin-server.py:3976-4000`).
- No version bump of the repo VERSION file for this audit itself (no behavior change); the implementation branch carries the agent minor/patch bumps listed above.

### 10.4 Version-bump summary

| File | Change | Bump | Rationale (conventions skill) |
|---|---|---|---|
| `hacs-developer.md` | + workflow section | 1.0.0 → **1.1.1** | new optional section = Minor (+ patch fix iterations) |
| `hacs-tester.md` | clarification | 1.0.0 → **1.0.2** | text clarification = Patch (+ patch fix iteration) |
| `hacs-code-reviewer.md` / `hacs-release.md` / `hacs-devops-engineer.md` | none | — | content unchanged |
| new rule file | — | — | rules carry no version frontmatter (precedent: `sharkord-sdk.md:1-2`) |

**(Correction):** versions updated to the actually implemented state — `hacs-developer` landed at **1.1.1** and `hacs-tester` at **1.0.2** due to fix iterations during implementation (frontmatter values verified); the plan above originally targeted 1.1.0 / 1.0.1.

---

## 11. Addendum: Release-Naming-Best-Practice (Issue #534, gleicher Branch)

> **Type:** Content-Ergänzung auf dem implementierten Preset (kein Architektur-Input des Audits). Der Abschnitt ergänzt die eisernen Regeln *Releases* um Format- und Lifecycle-Details für Tags/`manifest.version`/GitHub-Releases. Quellen-Zitate Englisch (Original-Doku), Rest Deutsch (Sprachregeln interne Doku).

### 11.1 Inhalt: 6 Regeln (eiserne-Regeln-Stil: Regel | Begründung | Fehlerklasse)

| # | Regel | Leit-Fehlerklasse |
|---|---|---|
| 1 | Tag-Format Stable `vMAJOR.MINOR.PATCH`; `v`-Prefix **nur** im Tag | `v` im `manifest.version` → `Invalid version` |
| 2 | `manifest.version` = bare SemVer ohne `v`, exakt dem Tag-Suffix entsprechend | Update-Erkennung/Sortierung kaputt (AwesomeVersion, PEP-440) |
| 3 | Beta-Tags `vX.Y.Zb<N>` (z.B. `v1.3.0b0`), GitHub-Release als **pre-release** flaggen, `manifest.version` = Tag-Suffix (`v1.3.0b0` ↔ `"version": "1.3.0b0"`) | Beta ohne Flag → alle User bekommen die Beta via Update-Check |
| 4 | Promotion beta→stable = neuer Release, nie Tag mutieren; Tags/Releases immutable (nie verschieben, löschen, wiederverwenden) | Tag-Reset → User bleiben auf Alt-Stand (HACS cacht Versionen) |
| 5 | Release-Notes-Mindeststruktur: Summary + ✨ New features + 💥 Breaking changes (je mit Migration-Hinweis; Pflicht bei MAJOR wegen Migrator-Regel) + Full-Changelog-Link | User aktualisieren ohne Migrationshinweis → Setup bricht |
| 6 | SemVer-Disziplin: MAJOR = Breaking (`unique_id`-/Entity-Änderungen **immer** breaking), MINOR = Feature, PATCH = Fix; `v0.x` nicht ohne Hinweis „stabil" | Entity-Änderung als MINOR/PATCH → User verlieren Entities stillschweigend |

### 11.2 Betroffene Dateien (Implementierung)

| Datei | Änderung | Version |
|---|---|---|
| `rules/2-platform/hacs-integration-development.md` | Neuer Abschnitt „Release-Naming-Best-Practice" (6-Regeln-Tabelle + Quellen-Liste); Tag-Beispiele (`v1.2.3` / `v1.3.0b0`) im Workflow-Schritt 6 | — (Rules tragen kein Version-Frontmatter) |
| `agents/2-platform/hacs-release.md` | Always-on-Anker „Release-Naming" (4 Bullets) im bestehenden `<persona>`-Patch; `description` erweitert | 1.0.0 → **1.0.1** (Patch) |
| `agents/2-platform/hacs-developer.md` | Einzeilige Tag-Format-Ergänzung im Workflow-Schritt 6 (Release-Dreiklang) | 1.1.1 → **1.1.2** (Patch) |
| `tests/test_platform_hacs_preset.py` | Neue Tier-2b-Klasse `TestTier2ReleaseNamingBlock`: Section-Header + 6-Regeln-Tabelle, `vX.Y.Zb<N>`-Beispiele, Anker im Release-Agenten, Beispiel-Konsistenz Skill ↔ Agenten | — |
| `docs/guides/setup/instantiate-project.md` | Abschnitt „Release-Naming-Best-Practice" im HACS-Kapitel (Zusammenfassung + Quellen) | — |
| `docs/plans/hacs-platform-preset-audit.md` | Dieser Abschnitt 11 | — |

Kompositionshinweis (Instruction-Bleed-Checkliste): beide Agent-Patches sind additiv (`append-after` auf `<persona>` bzw. bestehende Liste), die Base-Sections werden nicht umdefiniert — Bleed-Risiko gering.

### 11.3 Quellen

- <https://hacs.xyz/docs/publish/start> — „If the repository uses GitHub releases, the tag name from the latest release is used to set the remote version. Just publishing tags is not enough, you need to publish releases."; `homeassistant`-Key kann HA-Betas via `b0`-Suffix erlauben.
- <https://hacs.xyz/docs/use/entities/switch> — HACS 2.0 Pre-Release-Mechanik: GitHub pre-release-Flag → Entity `switch.<repo>_pre_release` (default OFF); Beispiel-Tags `v1.0.0`, `v2.0.0b0`.
- <https://developers.home-assistant.io/docs/versioning> — HA nutzt PEP-440-Suffixe (`b<N>` für Beta); Versionsvergleiche via AwesomeVersion, nicht String-Parsing.
- <https://semver.org/#is-v123-a-semantic-version> — FAQ: `v1.2.3` ist keine Semantic Version; der `v`-Prefix ist reine Tag-Konvention.
- <https://github.com/hacs/integration/releases> — Vorbild für die Release-Notes-Struktur (What's Changed / ✨ New features / 💥 Breaking changes / Full Changelog); HACS zeigt die letzten Releases in der Update-Auswahl.
- Praxisbeispiel: `boschshc-hass` — zwei Release-Trains (Beta als Pre-Release, Promotion manuell).
