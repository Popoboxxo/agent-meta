# Governance Quick-Wins (README-Standard, .gitignore-Hardening, Orchestrator-Status, Progress-System) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Codify four independent governance quick-wins from issue #682 (sections 3-6) — a README template standard, a context-file gitignore bugfix plus a safer setup-wizard default, a mandatory orchestrator status table, and a human-readable progress file — without touching sections 1/2 (out of scope, missing from the issue) or section 7 (Fleet-Server, separate plan).

**Architecture:** All four changes are additive to the existing sync.py template-substitution pipeline (`scripts/lib/config.py:build_variables()`, `scripts/lib/consistency/placeholders.py`, `scripts/lib/standalone.py`) and to two library modules (`scripts/lib/gitignore.py`, `scripts/lib/setup.py`, `scripts/lib/checkpoint.py`). No new top-level modules, no new external dependencies, no schema-breaking changes.

**Tech Stack:** Python 3.9-floor stdlib (`from __future__ import annotations` everywhere touched), PyYAML (already a soft dependency via `scripts/lib/setup.py`), Markdown/YAML templates, pytest.

**Spec:** https://github.com/Popoboxxo/agent-meta/issues/682 — sections 3 (README-Standard), 4 (.gitignore-Default), 5 (Orchestrator-Status-Tabelle / issue #678), 6 (Progress-System, Option A). Sections 1/2/7 are explicitly out of scope for this plan.

## Global Constraints

- Every touched `scripts/lib/*.py` file keeps `from __future__ import annotations` at the top — no bare `X | Y` union annotations without it (Python 3.9 floor, enforced by `scripts/lib/consistency/python_compat.py`, CI matrix 3.9/3.11/3.12).
- Placeholders are always `{{UPPER_SNAKE_CASE}}` — never lowercase (hard invariant, `.claude/skills/conventions/SKILL.md`).
- Every new placeholder consumed by `agents/1-generic/*.md` needs THREE registrations to avoid drift: (1) `scripts/lib/config.py` → `build_variables()`, (2) `scripts/lib/consistency/placeholders.py` → `_BUILTIN_VARS`, (3) `scripts/lib/standalone.py` → the matching fallback dict (`_IDENTITY_FALLBACKS` for plain-text values, `_ORCHESTRATION_FALLBACKS` for `_BLOCK` values referenced unconditionally, `_CONDITIONAL_FALSE_FLAGS` for anything gating a `{{#if}}`) — `standalone.py` only renders `agents/1-generic/*.md`, never `rules/1-generic/*.md`.
- `agents/1-generic/<role>.md` frontmatter `version:` MUST be bumped on every content change (minor bump = new optional/expanded section, per `.claude/skills/conventions/SKILL.md`). `rules/1-generic/*.md` files have no frontmatter/version — none to bump there.
- `.claude/agents/*.md` (and the other provider dirs) are **generated output** — never hand-edit them. After editing a generic template, run `python scripts/sync.py` and diff the regenerated output to verify.
- No breaking changes: every new `project.yaml` key is optional with a default that reproduces today's behavior exactly (`readme:` block, `gitignore.custom_entries` additions are opt-in via wizard prompt, not silent).
- Test runner: full suite needs the namespace-packages flag or ~30 `scripts.lib` collection errors appear: `python3 -m pytest tests/ -o consider_namespace_packages=true -q`. Individual new test files can be run directly with plain `python3 -m pytest tests/test_x.py -q`.
- Validate template consistency after every template edit: `python3 scripts/sync.py --validate`.
- Not implemented (explicitly out of scope per the issue's own recommendation, do not build these): CLAUDE.md/AGENTS.md ignorability change (4.2, rejected — breaks the framework's single-source-of-truth premise), `gitignore.generated` default flip to `true` (4.4, rejected — breaks CI/team reproducibility), a CI-status badge in the README default set (only available as an opt-in list value, never emitted unless CI config is actually detected at runtime by the documenter agent).

---

### Task 1: `readme` config block in the project schema

**Files:**
- Modify: `config/project-config.schema.json:794-807` (insert new `"readme"` property between the closing `}` of `"drift-detection"` and the `"context_file"` property)
- Modify: `templates/configs/project.yaml.example` (append a commented example block near the existing `gitignore:` example, around line 74)
- Test: `tests/test_readme_schema.py` (new)

**Interfaces:**
- Consumes: nothing (pure schema addition).
- Produces: the `readme` object shape `{badges: string[], warnings: bool, sections: string[]}` that Task 2 (`build_variables`) reads via `config.get("readme", {})`.

- [ ] Step 1: Write the failing test

  Create `tests/test_readme_schema.py`:

  ```python
  """Schema validation for the `readme` project.yaml block (issue #682 §3)."""

  import json
  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parent.parent
  _SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"


  def _load_schema() -> dict:
      with _SCHEMA_PATH.open(encoding="utf-8") as f:
          return json.load(f)


  def test_schema_is_valid_json():
      _load_schema()  # raises json.JSONDecodeError on malformed schema


  def test_readme_block_defined_with_expected_defaults():
      schema = _load_schema()
      readme = schema["properties"]["readme"]
      assert readme["type"] == "object"
      badges = readme["properties"]["badges"]
      assert badges["type"] == "array"
      assert badges["default"] == ["version", "stack", "license"]
      warnings = readme["properties"]["warnings"]
      assert warnings["type"] == "boolean"
      assert warnings["default"] is False
      sections = readme["properties"]["sections"]
      assert sections["type"] == "array"
      assert sections["default"] == ["description", "badges", "setup", "structure"]


  def test_readme_block_rejects_unknown_keys():
      schema = _load_schema()
      assert schema["properties"]["readme"]["additionalProperties"] is False
  ```

- [ ] Step 2: Run test, verify it fails

  ```
  python3 -m pytest tests/test_readme_schema.py -q
  ```
  Expected failure: `KeyError: 'readme'` (property does not exist yet).

- [ ] Step 3: Write minimal implementation

  In `config/project-config.schema.json`, insert immediately after the `"drift-detection"` property's closing `},` (currently line 805, right before `"context_file": {` at line 807):

  ```json
    "readme": {
      "type": "object",
      "description": "README.md structure standard (issue #682): badges shown, optional warning callout, section selection. Consumed by the `documenter` agent when maintaining README.md — additive only, never overwrites hand-written content.",
      "properties": {
        "badges": {
          "type": "array",
          "description": "Badge set for the README badges row. 'license' is only ever rendered when a LICENSE file actually exists; 'ci' is only ever rendered when a CI config is actually detected -- both checked at documentation time, never assumed.",
          "items": {
            "type": "string",
            "enum": ["version", "stack", "license", "ci"]
          },
          "default": ["version", "stack", "license"]
        },
        "warnings": {
          "type": "boolean",
          "description": "Whether the README may include a [!WARNING]/[!IMPORTANT] callout. Default off -- most projects are not experiments.",
          "default": false
        },
        "sections": {
          "type": "array",
          "description": "Required README sections, in order.",
          "items": {
            "type": "string",
            "enum": ["description", "badges", "setup", "structure"]
          },
          "default": ["description", "badges", "setup", "structure"]
        }
      },
      "additionalProperties": false
    },
  ```

- [ ] Step 4: Run test, verify it passes

  ```
  python3 -m pytest tests/test_readme_schema.py -q
  ```

- [ ] Step 5: Document the example block

  In `templates/configs/project.yaml.example`, after the existing commented `gitignore:` example block (ends around line 74, right before the `# Secrets in committeten Dateien erlauben` comment), add:

  ```yaml
  #
  # readme:
  #   # badges: Badge-Set für die README-Badges-Zeile. "license" wird nur gerendert
  #   #   wenn eine LICENSE-Datei existiert, "ci" nur wenn eine CI-Config erkennbar ist.
  #   badges: [version, stack, license]
  #   # warnings: false (Default) → kein [!WARNING]-Callout erzwungen.
  #   warnings: false
  #   # sections: Pflicht-Abschnitte in Reihenfolge.
  #   sections: [description, badges, setup, structure]
  ```

- [ ] Step 6: Commit

  ```
  git add config/project-config.schema.json templates/configs/project.yaml.example tests/test_readme_schema.py
  git commit -m "feat: add readme config block to project schema (#682)"
  ```

---

### Task 2: `README_BADGES`/`README_WARNINGS_ENABLED`/`README_SECTIONS` placeholders

**Files:**
- Modify: `scripts/lib/config.py` (new code inside `_build_core_variables`, after the `REQ_CATEGORIES` fallback block, i.e. after line 621 and before line 622's `PROJECT_GOAL` fallback — exact insertion point verified by the anchor text in Step 3 below)
- Modify: `scripts/lib/consistency/placeholders.py:11-103` (`_BUILTIN_VARS` frozenset)
- Modify: `scripts/lib/standalone.py:54-71` (`_IDENTITY_FALLBACKS`) and `:95-126` (`_CONDITIONAL_FALSE_FLAGS`)
- Test: `tests/test_readme_variables.py` (new)

**Interfaces:**
- Consumes: `config.get("readme", {})` dict from Task 1's schema shape; `_BUILTIN_VARS` frozenset and both standalone fallback dicts (module-level, imported directly).
- Produces: `variables["README_BADGES"]` (comma-joined string, e.g. `"version, stack, license"`), `variables["README_WARNINGS_ENABLED"]` (`"true"`/`"false"` string for `{{#if}}`), `variables["README_SECTIONS"]` (comma-joined string) — consumed by Task 4 (`documenter.md` §5).

- [ ] Step 1: Write the failing test

  Create `tests/test_readme_variables.py`:

  ```python
  """build_variables() coverage for the readme.* config block (issue #682 §3)."""

  from pathlib import Path

  from scripts.lib.config import build_variables

  _REPO_ROOT = Path(__file__).resolve().parents[1]


  def test_readme_variables_default_when_block_absent():
      variables, _ = build_variables({}, _REPO_ROOT)
      assert variables["README_BADGES"] == "version, stack, license"
      assert variables["README_WARNINGS_ENABLED"] == "false"
      assert variables["README_SECTIONS"] == "description, badges, setup, structure"


  def test_readme_variables_reflect_explicit_config():
      config = {
          "readme": {
              "badges": ["version", "ci"],
              "warnings": True,
              "sections": ["description", "setup"],
          }
      }
      variables, _ = build_variables(config, _REPO_ROOT)
      assert variables["README_BADGES"] == "version, ci"
      assert variables["README_WARNINGS_ENABLED"] == "true"
      assert variables["README_SECTIONS"] == "description, setup"
  ```

- [ ] Step 2: Run test, verify it fails

  ```
  python3 -m pytest tests/test_readme_variables.py -q
  ```
  Expected failure: `KeyError: 'README_BADGES'`.

- [ ] Step 3: Write minimal implementation

  In `scripts/lib/config.py`, inside `_build_core_variables`, insert right after the existing block that ends with (line 621):

  ```python
      if not variables.get("REQ_CATEGORIES"):
          variables["REQ_CATEGORIES"] = variables.get("REQ_CATEGORIES_LIST") or (
              "- Kernfunktionalität\n- Lifecycle\n- Nichtfunktionale Anforderungen"
          )
  ```

  the new block:

  ```python
      # README structure standard (issue #682 §3): comma-joined strings for
      # inline use in documenter.md prose (not a {{#if}}-gated block, so no
      # standalone.py _ORCHESTRATION_FALLBACKS entry needed -- these three go
      # into _IDENTITY_FALLBACKS/_CONDITIONAL_FALSE_FLAGS instead, see there).
      _readme_cfg = config.get("readme", {})
      variables["README_BADGES"] = ", ".join(
          _readme_cfg.get("badges", ["version", "stack", "license"])
      )
      variables["README_WARNINGS_ENABLED"] = (
          "true" if _readme_cfg.get("warnings", False) else "false"
      )
      variables["README_SECTIONS"] = ", ".join(
          _readme_cfg.get("sections", ["description", "badges", "setup", "structure"])
      )
  ```

  In `scripts/lib/consistency/placeholders.py`, inside `_BUILTIN_VARS`, add a new line right after the `"AGENT_TABLE", "AGENT_HINTS",` entry (line 18):

  ```python
      # README structure standard (issue #682 §3)
      "README_BADGES", "README_WARNINGS_ENABLED", "README_SECTIONS",
  ```

  In `scripts/lib/standalone.py`, `README_BADGES`/`README_SECTIONS` are plain informational text (like `PROJECT_LANGUAGES`) — add to `_IDENTITY_FALLBACKS` (after the `"EXTRA_DONTS": "",` line, ~line 70):

  ```python
      "README_BADGES": "version, stack, license",
      "README_SECTIONS": "description, badges, setup, structure",
  ```

  `README_WARNINGS_ENABLED` gates a `{{#if}}` in Task 4's documenter.md rewrite — add to `_CONDITIONAL_FALSE_FLAGS` (after the `"TESTER_SNIPPETS_PATH_SET": "false",` line, ~line 108):

  ```python
      "README_WARNINGS_ENABLED": "false",
  ```

- [ ] Step 4: Run test, verify it passes

  ```
  python3 -m pytest tests/test_readme_variables.py -q
  ```

- [ ] Step 5: Regression-check placeholder + standalone consistency

  ```
  python3 -m pytest tests/test_config_variable_fallbacks.py -q
  python3 scripts/sync.py --validate
  ```

- [ ] Step 6: Commit

  ```
  git add scripts/lib/config.py scripts/lib/consistency/placeholders.py scripts/lib/standalone.py tests/test_readme_variables.py
  git commit -m "feat: build README_BADGES/README_WARNINGS_ENABLED/README_SECTIONS variables (#682)"
  ```

---

### Task 3: `templates/configs/README-template.md`

**Files:**
- Create: `templates/configs/README-template.md`
- Test: none (static reference document, not sync-processed — see note below)

**Interfaces:**
- Consumes: nothing programmatically. This file is a **manually-read reference** for the `documenter` agent (Read tool), the same way `templates/direct-dispatch-section.md` is a raw partial — it is NOT passed through `build_variables()`/`substitute()`. Its `{{PLACEHOLDER}}` tokens are written in the project's real placeholder syntax so the `documenter` agent (an LLM) can resolve them itself by reading the target project's actual `.meta-config/project.yaml` and generated `CLAUDE.md`/`AGENTS.md` — mirrors how `documenter.md` already tells the agent to write README.md "ALWAYS in `{{DOCS_LANGUAGE}}`" without any code ever substituting that value into the target project's README.md.
- Produces: the section skeleton referenced by Task 4's rewritten `documenter.md` §5.

- [ ] Step 1: Create the file

  ```markdown
  <!--
  Reference template for README.md — read by the `documenter` agent, never
  sync-processed. Placeholders below are resolved by the documenter agent
  itself from the target project's .meta-config/project.yaml and generated
  context file (CLAUDE.md/AGENTS.md), not by sync.py.

  Managed-block principle (same as .gitignore, issue #682 §3/§4): this
  template lists the REQUIRED sections. The documenter agent adds only the
  sections that are missing from an existing README.md -- it never
  overwrites hand-written prose in a section that already exists.
  -->

  # {{PROJECT_NAME}}

  > {{PROJECT_SHORT}} — one-line description.

  <!--
  Badges row — only emit a badge if it is actually true, never a
  placeholder that resolves to a broken image:
  - version: always safe (project's own version, e.g. from VERSION file or package manifest)
  - stack:   always safe (primary language/runtime, e.g. from PROJECT_LANGUAGES)
  - license: ONLY if a `LICENSE` file exists in the project root
  - ci:      ONLY if a recognizable CI config exists (.github/workflows/*.yml,
             .gitlab-ci.yml, .circleci/config.yml, ...) -- not part of the
             default badge set, opt-in only (readme.badges: [..., ci])
  -->
  [![Version](https://img.shields.io/badge/version-{{VERSION}}-blue.svg)]()
  [![Stack](https://img.shields.io/badge/stack-{{PROJECT_LANGUAGES}}-green.svg)]()
  <!-- [![License](https://img.shields.io/badge/license-{{LICENSE_NAME}}-gray.svg)]() -- only if LICENSE file exists -->

  <!--
  Optional warning/important callout -- only if readme.warnings: true in
  project.yaml. Omit entirely otherwise, do not render an empty callout.
  -->
  <!--
  > [!WARNING]
  > ## {{WARNING_TITLE}}
  > {{WARNING_BODY}}
  -->

  ## Setup / Quickstart

  ```bash
  {{DEV_COMMANDS}}
  {{TEST_COMMANDS}}
  ```

  ## Structure

  See [`docs/CODEBASE_OVERVIEW.md`](docs/CODEBASE_OVERVIEW.md) / [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full module layout. <!-- only link the file(s) that actually exist -->
  ```

- [ ] Step 2: Verify the file is syntactically valid Markdown (no code-execution check needed for a static doc)

  ```
  python3 -c "from pathlib import Path; Path('templates/configs/README-template.md').read_text(encoding='utf-8')"
  ```

- [ ] Step 3: Commit

  ```
  git add templates/configs/README-template.md
  git commit -m "feat: add README-template.md reference for documenter agent (#682)"
  ```

---

### Task 4: `documenter.md` §5 rewrite (README standard)

**Files:**
- Modify: `agents/1-generic/documenter.md:3` (version bump) and `:43-45` (§5 body)
- Test: `tests/test_documenter_readme_section.py` (new)

**Interfaces:**
- Consumes: `{{README_BADGES}}`, `{{README_WARNINGS_ENABLED}}`, `{{README_SECTIONS}}` from Task 2; `templates/configs/README-template.md` from Task 3 (referenced by path in prose, read by the agent at runtime — not embedded).
- Produces: updated agent instructions consumed only by the LLM at runtime (no downstream code interface).

- [ ] Step 1: Write the failing test

  Create `tests/test_documenter_readme_section.py`:

  ```python
  """documenter.md §5 must reference the README standard placeholders and
  template (issue #682 §3) -- regression guard against silently dropping the
  additive/managed-block instruction on a future edit."""

  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parents[1]
  _DOCUMENTER = _REPO_ROOT / "agents" / "1-generic" / "documenter.md"


  def test_section_5_references_readme_variables():
      content = _DOCUMENTER.read_text(encoding="utf-8")
      assert "{{README_BADGES}}" in content
      assert "{{README_WARNINGS_ENABLED}}" in content
      assert "{{README_SECTIONS}}" in content


  def test_section_5_references_template_and_managed_block_principle():
      content = _DOCUMENTER.read_text(encoding="utf-8")
      assert "README-template.md" in content
      assert "additiv" in content.lower() or "additive" in content.lower()


  def test_section_5_documents_license_and_ci_runtime_checks():
      content = _DOCUMENTER.read_text(encoding="utf-8")
      assert "LICENSE" in content
      assert "CI" in content
  ```

- [ ] Step 2: Run test, verify it fails

  ```
  python3 -m pytest tests/test_documenter_readme_section.py -q
  ```
  Expected failure: `assert "{{README_BADGES}}" in content` fails (§5 is still the one-liner).

- [ ] Step 3: Write minimal implementation

  Bump the frontmatter version in `agents/1-generic/documenter.md:3`:

  ```yaml
  version: "1.7.0"
  ```

  Replace §5 (lines 43-45):

  ```markdown
  ## 5. README.md maintenance

  README ALWAYS written in **{{DOCS_LANGUAGE}}**.
  ```

  with:

  ```markdown
  ## 5. README.md maintenance

  README ALWAYS written in **{{DOCS_LANGUAGE}}**.

  **Required sections** (default order: {{README_SECTIONS}}) — additive only: an
  existing, hand-written README.md is NEVER overwritten wholesale, only missing
  required sections get added (same managed-block principle as `.gitignore`).

  1. **Title + one-line description.**
  2. **Badges row** — set from `readme.badges` (default: {{README_BADGES}}). Runtime checks before rendering, never assume:
     - `license` → only include if a `LICENSE` file exists in the project root.
     - `ci` → only include if a recognizable CI config exists (`.github/workflows/*.yml`, `.gitlab-ci.yml`, `.circleci/config.yml`, ...).
     - `version`/`stack` → always safe to include.
     A broken or misleading badge (e.g. a license badge with no LICENSE file) is a defect, not an acceptable shortcut.
  3. **Warning/Important callout** — ONLY when `readme.warnings` is enabled ({{README_WARNINGS_ENABLED}}). Never force a callout on a project that isn't flagged as one.
  4. **Setup/Quickstart** — from `{{DEV_COMMANDS}}`/`{{TEST_COMMANDS}}`.
  5. **Structure reference** — link `docs/CODEBASE_OVERVIEW.md`/`docs/ARCHITECTURE.md` only if the file actually exists; never fabricate the link.

  Reference skeleton: `templates/configs/README-template.md` (structure guide, not a byte-for-byte template — do not paste its HTML comments into the real README.md).
  ```

- [ ] Step 4: Run test, verify it passes

  ```
  python3 -m pytest tests/test_documenter_readme_section.py -q
  ```

- [ ] Step 5: Re-sync agent-meta's own generated files and validate

  ```
  python scripts/sync.py
  python3 scripts/sync.py --validate
  ```

- [ ] Step 6: Commit

  ```
  git add agents/1-generic/documenter.md tests/test_documenter_readme_section.py
  git commit -m "feat: codify README structure standard in documenter.md §5 (#682)"
  ```

---

### Task 5: `.gitignore` context-file protection bugfix

**Files:**
- Modify: `scripts/lib/gitignore.py:198-209` (the `settings` category loop inside `compute_base_gitignore_entries`)
- Test: `tests/test_gitignore_context_file_protection.py` (new)

**Interfaces:**
- Consumes: `provider_config: dict` parameter already passed into `compute_base_gitignore_entries` (no signature change).
- Produces: same return type (`list[str]`) — behavior is byte-identical for the real `config/ai-providers.yaml` (Claude's `context_file` is `"CLAUDE.md"` there too), only diverges if Claude's own `context_file` config value were ever changed.

- [ ] Step 1: Write the failing test

  Create `tests/test_gitignore_context_file_protection.py`:

  ```python
  """Context-file protection must follow Claude's own configured context_file,
  not a hardcoded "CLAUDE.md" literal (issue #682 §4 bugfix).

  The protection scope itself is unchanged by design: only Claude's context
  file is hard-exempted from the `settings` category (AGENTS.md/MAMMOUTH.md
  for other providers still follow the category default, as documented in
  the schema). The bug was the hardcoded literal, not the exemption's scope.
  """

  import sys
  from pathlib import Path

  import yaml

  _REPO_ROOT = Path(__file__).resolve().parent.parent
  _SCRIPTS_DIR = _REPO_ROOT / "scripts"
  if str(_SCRIPTS_DIR) not in sys.path:
      sys.path.insert(0, str(_SCRIPTS_DIR))

  from lib.gitignore import compute_base_gitignore_entries  # noqa: E402

  _PROVIDERS_CONFIG = _REPO_ROOT / "config" / "ai-providers.yaml"


  def _load_provider_config() -> dict:
      with _PROVIDERS_CONFIG.open(encoding="utf-8") as f:
          return yaml.safe_load(f)["providers"]


  def test_real_config_claude_md_still_protected_settings_true():
      # Regression: default real config -- unchanged behavior.
      provider_config = _load_provider_config()
      entries = compute_base_gitignore_entries(
          ["Claude", "Gemini"], provider_config, {"settings": True}
      )
      assert "CLAUDE.md" not in entries
      assert "AGENTS.md" in entries  # Gemini's context file: unaffected, by design

  def test_protection_follows_claudes_configured_context_file_not_literal():
      # Simulated non-default Claude context_file -- protection must track it.
      provider_config = {
          "Claude": {"context_file": "CLAUDE_CUSTOM.md", "gitignore_entries": []},
          "Gemini": {"context_file": "AGENTS.md"},
      }
      entries = compute_base_gitignore_entries(
          ["Claude", "Gemini"], provider_config, {"settings": True}
      )
      assert "CLAUDE_CUSTOM.md" not in entries
      assert "AGENTS.md" in entries


  def test_settings_false_still_keeps_both_context_files_out_default():
      provider_config = _load_provider_config()
      entries = compute_base_gitignore_entries(
          ["Claude", "Gemini"], provider_config, {"settings": False}
      )
      assert "CLAUDE.md" not in entries
      assert "AGENTS.md" not in entries
  ```

- [ ] Step 2: Run test, verify it fails

  ```
  python3 -m pytest tests/test_gitignore_context_file_protection.py -q
  ```
  Expected failure: `test_protection_follows_claudes_configured_context_file_not_literal` fails — `"CLAUDE_CUSTOM.md" in entries` because the current code compares against the literal `"CLAUDE.md"`, not `"CLAUDE_CUSTOM.md"`.

- [ ] Step 3: Write minimal implementation

  In `scripts/lib/gitignore.py`, current code (lines 198-209):

  ```python
      # Category "settings" (default false): committed settings/context files.
      # Top-level context files (CLAUDE.md never, AGENTS.md/MAMMOUTH.md via the
      # settings category) keep their per-category behavior in toggle mode.
      cat_set = gitignore_cfg.get("settings", False)
      for _prov in providers:
          _pc = provider_config.get(_prov, {})
          _sf = _pc.get("settings_file")
          if _sf and _keep(_sf, cat_set):
              entries.append(_sf)
          _ctx = _pc.get("context_file")
          if _ctx and _ctx != "CLAUDE.md" and _keep(_ctx, cat_set):
              entries.append(_ctx)
  ```

  becomes:

  ```python
      # Category "settings" (default false): committed settings/context files.
      # Top-level context files (Claude's own context file never, other
      # providers' context files -- AGENTS.md/MAMMOUTH.md -- via the settings
      # category) keep their per-category behavior in toggle mode.
      #
      # Issue #682 §4 bugfix: the exemption used to compare against the
      # literal string "CLAUDE.md" for every provider's context file, which
      # only worked because Claude's context_file happens to equal that
      # literal today. Resolving it from Claude's own provider config instead
      # decouples the exemption from the hardcoded string (provider-agnostic
      # policy, .claude/rules/*) without changing today's behavior at all.
      cat_set = gitignore_cfg.get("settings", False)
      _claude_context_file = provider_config.get("Claude", {}).get("context_file", "CLAUDE.md")
      for _prov in providers:
          _pc = provider_config.get(_prov, {})
          _sf = _pc.get("settings_file")
          if _sf and _keep(_sf, cat_set):
              entries.append(_sf)
          _ctx = _pc.get("context_file")
          if _ctx and _ctx != _claude_context_file and _keep(_ctx, cat_set):
              entries.append(_ctx)
  ```

- [ ] Step 4: Run test, verify it passes

  ```
  python3 -m pytest tests/test_gitignore_context_file_protection.py -q
  ```

- [ ] Step 5: Regression-check the existing gitignore test suite (pins the historical behavior for the real config — must stay green since Claude's real `context_file` is still `"CLAUDE.md"`)

  ```
  python3 -m pytest tests/test_gitignore_provider_dirs.py -q
  ```

- [ ] Step 6: Commit

  ```
  git add scripts/lib/gitignore.py tests/test_gitignore_context_file_protection.py
  git commit -m "fix: resolve protected context file from Claude's own config, not a literal (#682)"
  ```

---

### Task 6: Setup-wizard secret-pattern question

**Files:**
- Modify: `scripts/lib/setup.py:218-222` (end of the "3. Git Configuration" section) and `:287-299` (config assembly)
- Test: `tests/test_setup_wizard_secrets_prompt.py` (new)

**Interfaces:**
- Consumes: `_ask_choice()` helper (already defined, `scripts/lib/setup.py:62`).
- Produces: `config["gitignore"]["custom_entries"]` list, consumed downstream by `scripts/lib/gitignore.py:compute_base_gitignore_entries()`'s existing `custom_entries` handling (Task 5's neighbor code, line 211-213 — untouched, already generic).

- [ ] Step 1: Write the failing test

  Create `tests/test_setup_wizard_secrets_prompt.py`:

  ```python
  """Setup wizard must offer (not silently default) typical secret-pattern
  .gitignore entries (issue #682 §4.3)."""

  import sys
  from pathlib import Path
  from unittest.mock import patch

  _REPO_ROOT = Path(__file__).resolve().parent.parent
  _SCRIPTS_DIR = _REPO_ROOT / "scripts"
  if str(_SCRIPTS_DIR) not in sys.path:
      sys.path.insert(0, str(_SCRIPTS_DIR))

  from lib.setup import run_setup_wizard  # noqa: E402

  _EXPECTED_SECRET_PATTERNS = [".env*", "*.pem", "*.key", "credentials*.json", "secret*.y*ml"]


  def _run_wizard(tmp_path, answers):
      """Run the wizard with a scripted sequence of `input()` answers."""
      with patch("lib.setup._QUESTIONARY_AVAILABLE", False), \
           patch("sys.stdin.isatty", return_value=True), \
           patch("builtins.input", side_effect=answers):
          return run_setup_wizard(
              agent_meta_root=_REPO_ROOT,
              project_root=tmp_path,
              target_config=tmp_path / "project.yaml",
              dry_run=True,
          )

  def test_accepting_recommended_default_adds_secret_patterns(tmp_path):
      # name, prefix, short, providers(list->empty=default), git platform,
      # remote, branch, secrets-question(yes/default), optional-config(no)
      answers = ["my-proj", "mp", "", "", "", "", "", "", "no"]
      config = _run_wizard(tmp_path, answers)
      assert config.get("gitignore", {}).get("custom_entries") == _EXPECTED_SECRET_PATTERNS


  def test_declining_leaves_gitignore_block_absent(tmp_path):
      answers = ["my-proj", "mp", "", "", "", "", "", "no", "no"]
      config = _run_wizard(tmp_path, answers)
      assert "gitignore" not in config
  ```

- [ ] Step 2: Run test, verify it fails

  ```
  python3 -m pytest tests/test_setup_wizard_secrets_prompt.py -q
  ```
  Expected failure: extra/missing `input()` call mismatch or `config.get("gitignore", {})` empty (the question does not exist yet) — adjust the exact `answers` list length once Step 3 fixes the prompt count (documented here so the test author isn't surprised: the wizard's `_ask`/`_ask_choice` fallback path consumes exactly one `input()` per call when `questionary` is unavailable).

- [ ] Step 3: Write minimal implementation

  In `scripts/lib/setup.py`, after line 222 (`git_branch = _ask("Main Branch", default="main")`), insert:

  ```python

      print("\n  INFO: Protects against accidentally committed secrets in your own code")
      print("  (not just framework files) -- .gitignore only affects untracked files;")
      print("  already-committed secrets still need rotation + history rewrite.")
      ignore_secrets = _ask_choice(
          "Automatically .gitignore typical secret patterns "
          "(.env*, *.pem, *.key, credentials*.json, secret*.y*ml)?",
          ["yes", "no"],
          default="yes",
      )
  ```

  In the config-assembly section, after line 301 (`if platforms:\n        config["platforms"] = platforms`), insert:

  ```python
      if ignore_secrets == "yes":
          config["gitignore"] = {
              "custom_entries": [
                  ".env*", "*.pem", "*.key", "credentials*.json", "secret*.y*ml",
              ]
          }
  ```

- [ ] Step 4: Run test, verify it passes

  ```
  python3 -m pytest tests/test_setup_wizard_secrets_prompt.py -q
  ```

- [ ] Step 5: Regression-check the wizard still runs end-to-end in dry-run mode manually

  ```
  echo -e "test-proj\ntp\n\n\n\n\n\nno\nno" | python3 scripts/sync.py --setup --dry-run
  ```
  Verify the printed config preview shows no traceback and (when the secrets question is answered "yes" by adjusting the echo sequence) includes the `gitignore.custom_entries` list.

- [ ] Step 6: Commit

  ```
  git add scripts/lib/setup.py tests/test_setup_wizard_secrets_prompt.py
  git commit -m "feat: offer secret-pattern gitignore defaults in setup wizard (#682)"
  ```

---

### Task 7: `snippets/orchestrator/status-table.md`

**Files:**
- Create: `snippets/orchestrator/status-table.md`
- Test: covered by Task 8's variable-loading test (this task is pure content, no logic to unit-test in isolation).

**Interfaces:**
- Consumes: nothing (static content, no `{{VAR}}` placeholders inside — deliberately, since `_build_snippet_variables()` does a raw `read_text()` without a second substitution pass over the loaded block, see Task 8).
- Produces: raw Markdown text loaded verbatim into `variables["STATUS_TABLE_BLOCK"]` by Task 8.

- [ ] Step 1: Create the file

  ```markdown
  ## Status-Tabelle (Pflicht, Issue #678)

  Nach jedem Abschluss eines Batch-Mitglieds (FANOUT/PARALLEL_GROUP) und spätestens
  bei jedem BARRIER-Punkt eine kompakte Status-Tabelle ausgeben — nicht erst am Ende
  der gesamten Pipeline/Session.

  | Agent | Task | Status |
  |-------|------|--------|
  | `<agent>` | `<Ein-Satz-Task>` | `pending` \| `in_progress` \| `done` \| `failed` |

  - Eine Zeile pro Batch-Mitglied, in Dispatch-Reihenfolge.
  - `Status` wird bei jedem eingehenden Tool-Ergebnis aktualisiert, nicht erst am Ende gesammelt.
  - Ersetzt NICHT die BARRIER-Zusammenfassung — sie ist der sichtbare Zwischenstand
    während des laufenden Batches, kein Duplikat.
  ```

- [ ] Step 2: Verify readable as plain text (no placeholder leaks planned, but confirm no accidental `{{...}}` crept in)

  ```
  grep -c '{{' snippets/orchestrator/status-table.md
  ```
  Expected output: `0`.

- [ ] Step 3: Commit

  Commit together with Task 8 (the file is inert until wired into `build_variables()`).

---

### Task 8: Wire `STATUS_TABLE_BLOCK` into `build_variables()`

**Files:**
- Modify: `scripts/lib/config.py:1093-1104` (the orchestrator-snippet loading loop inside `_build_snippet_variables`)
- Modify: `scripts/lib/consistency/placeholders.py` (`_BUILTIN_VARS`, next to the other `_BLOCK` entries at line 75)
- Modify: `scripts/lib/standalone.py:76-81` (`_ORCHESTRATION_FALLBACKS`)
- Test: `tests/test_status_table_block.py` (new)

**Interfaces:**
- Consumes: `snippets/orchestrator/status-table.md` from Task 7.
- Produces: `variables["STATUS_TABLE_BLOCK"]` — consumed by Task 9 (`rules/1-generic/use-orchestrator.md`) and Task 10 (`agents/1-generic/orchestrator.md`).

- [ ] Step 1: Write the failing test

  Create `tests/test_status_table_block.py`:

  ```python
  """STATUS_TABLE_BLOCK must be loaded from snippets/orchestrator/status-table.md
  and be non-empty in every render (issue #678 / #682 §5) -- it is a mandatory
  rule, never gated behind a {{#if}} feature flag."""

  from pathlib import Path

  from scripts.lib.config import build_variables

  _REPO_ROOT = Path(__file__).resolve().parents[1]


  def test_status_table_block_loaded_and_non_empty():
      variables, _ = build_variables({}, _REPO_ROOT)
      assert "STATUS_TABLE_BLOCK" in variables
      assert "Status-Tabelle" in variables["STATUS_TABLE_BLOCK"]
      assert "Agent | Task | Status" in variables["STATUS_TABLE_BLOCK"]
  ```

- [ ] Step 2: Run test, verify it fails

  ```
  python3 -m pytest tests/test_status_table_block.py -q
  ```
  Expected failure: `KeyError: 'STATUS_TABLE_BLOCK'`.

- [ ] Step 3: Write minimal implementation

  In `scripts/lib/config.py`, extend the tuple in `_build_snippet_variables` (lines 1096-1101):

  ```python
      for _snippet_name, _var_stem in (
          ("se-mode", "SE_MODE"),
          ("a2a-protocol", "A2A_PROTOCOL"),
          ("checkpointing", "CHECKPOINTING"),
          ("quality-pipelines", "QUALITY_PIPELINES"),
          ("status-table", "STATUS_TABLE"),
      ):
  ```

  In `scripts/lib/consistency/placeholders.py`, extend the `_BLOCK` comment group (line 75):

  ```python
      "SE_MODE_BLOCK", "A2A_PROTOCOL_BLOCK", "CHECKPOINTING_BLOCK", "QUALITY_PIPELINES_BLOCK",
      "STATUS_TABLE_BLOCK",
  ```

  In `scripts/lib/standalone.py`, `STATUS_TABLE_BLOCK` will be referenced unconditionally (no `{{#if}}` wrapper, see Task 9/10) inside `agents/1-generic/orchestrator.md`, which IS rendered standalone — add to `_ORCHESTRATION_FALLBACKS` (line 76-81):

  ```python
  _ORCHESTRATION_FALLBACKS: dict[str, str] = {
      "A2A_HANDOFF_BLOCK": "",
      "ANTI_RECURSION_BLOCK": "",
      "DOD_REQ_BLOCK": "",
      "DOD_TESTS_BLOCK": "",
      # STATUS_TABLE_BLOCK (issue #682 §5): unlike SE_MODE_BLOCK/CHECKPOINTING_BLOCK/
      # QUALITY_PIPELINES_BLOCK (built but not yet referenced by any template --
      # pre-existing gap, out of scope here), this one IS referenced unconditionally
      # in orchestrator.md §7 -- standalone rendering needs the real snippet text,
      # not an empty string, since it's a mandatory rule the reader must see.
      "STATUS_TABLE_BLOCK": (Path(__file__).resolve().parents[2] / "snippets" / "orchestrator" / "status-table.md").read_text(encoding="utf-8")
      if (Path(__file__).resolve().parents[2] / "snippets" / "orchestrator" / "status-table.md").exists() else "",
  }
  ```

  Check `scripts/lib/standalone.py`'s existing imports at the top of the file for `Path` (already imported, since `_IDENTITY_FALLBACKS`/other code uses `Path` throughout the module) — no new import needed.

- [ ] Step 4: Run test, verify it passes

  ```
  python3 -m pytest tests/test_status_table_block.py -q
  ```

- [ ] Step 5: Regression-check standalone rendering + placeholder consistency

  ```
  python3 -m pytest tests/test_build_variables_decomposition.py -q
  python3 scripts/sync.py --validate
  ```

- [ ] Step 6: Commit

  ```
  git add snippets/orchestrator/status-table.md scripts/lib/config.py scripts/lib/consistency/placeholders.py scripts/lib/standalone.py tests/test_status_table_block.py
  git commit -m "feat: load STATUS_TABLE_BLOCK snippet for mandatory batch status reporting (#678)"
  ```

---

### Task 9: Reference `{{STATUS_TABLE_BLOCK}}` in `rules/1-generic/use-orchestrator.md`

**Files:**
- Modify: `rules/1-generic/use-orchestrator.md:21-26` (inside the `{{#if ORCH_MODE_MAIN_CHAT}}` block, between "A2A Delegation" and "Plan Delegation")
- Test: `tests/test_status_table_rule_reference.py` (new)

**Interfaces:**
- Consumes: `{{STATUS_TABLE_BLOCK}}` from Task 8.
- Produces: rendered `.claude/rules/use-orchestrator.md` (via `python scripts/sync.py`) containing the status-table rule for the main-chat-as-orchestrator mode — this repo's own primary orchestrator mode per its `project.yaml` (`ORCH_MODE_MAIN_CHAT`).

- [ ] Step 1: Write the failing test

  Create `tests/test_status_table_rule_reference.py`:

  ```python
  """use-orchestrator.md must reference the mandatory status-table block
  inside its main-chat-mode branch (issue #678 / #682 §5)."""

  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parents[1]
  _RULE = _REPO_ROOT / "rules" / "1-generic" / "use-orchestrator.md"


  def test_status_table_block_referenced_inside_main_chat_mode():
      content = _RULE.read_text(encoding="utf-8")
      main_chat_start = content.index("{{#if ORCH_MODE_MAIN_CHAT}}")
      main_chat_end = content.index("{{/if}}", main_chat_start)
      main_chat_section = content[main_chat_start:main_chat_end]
      assert "{{STATUS_TABLE_BLOCK}}" in main_chat_section
  ```

- [ ] Step 2: Run test, verify it fails

  ```
  python3 -m pytest tests/test_status_table_rule_reference.py -q
  ```
  Expected failure: `assert "{{STATUS_TABLE_BLOCK}}" in main_chat_section` is False.

- [ ] Step 3: Write minimal implementation

  In `rules/1-generic/use-orchestrator.md`, current lines 21-26:

  ```markdown
  ## A2A Delegation
  {{A2A_HANDOFF_BLOCK}}

  ## Plan Delegation
  Plan vorhanden (`plan-*.md` oder Knowledge-Wiki Plan-Seite) -> Pipeline `feature-lifecycle` mit `payload.plan_ref`, statt neuen Lifecycle blind zu starten.
  {{/if}}
  ```

  becomes:

  ```markdown
  ## A2A Delegation
  {{A2A_HANDOFF_BLOCK}}

  {{STATUS_TABLE_BLOCK}}

  ## Plan Delegation
  Plan vorhanden (`plan-*.md` oder Knowledge-Wiki Plan-Seite) -> Pipeline `feature-lifecycle` mit `payload.plan_ref`, statt neuen Lifecycle blind zu starten.
  {{/if}}
  ```

- [ ] Step 4: Run test, verify it passes

  ```
  python3 -m pytest tests/test_status_table_rule_reference.py -q
  ```

- [ ] Step 5: Re-sync and manually confirm the rendered rule

  ```
  python scripts/sync.py
  grep -A3 "Status-Tabelle" .claude/rules/use-orchestrator.md
  ```
  Expected: the status-table section renders with no leftover `{{...}}` placeholder.

- [ ] Step 6: Commit

  ```
  git add rules/1-generic/use-orchestrator.md tests/test_status_table_rule_reference.py
  git commit -m "feat: mandate status-table reporting in main-chat orchestrator mode (#678)"
  ```

---

### Task 10: Reference `{{STATUS_TABLE_BLOCK}}` in `agents/1-generic/orchestrator.md`

**Files:**
- Modify: `agents/1-generic/orchestrator.md:3` (version bump) and `:149-158` (§7 BARRIER protocol)
- Test: `tests/test_status_table_orchestrator_reference.py` (new)

**Interfaces:**
- Consumes: `{{STATUS_TABLE_BLOCK}}` from Task 8.
- Produces: rendered orchestrator subagent template for the advisory/strict modes (the "seltener Fall eines aktiven Orchestrator-Subagenten" per the issue).

- [ ] Step 1: Write the failing test

  Create `tests/test_status_table_orchestrator_reference.py`:

  ```python
  """orchestrator.md §7 (BARRIER protocol) must reference the mandatory
  status-table block (issue #678 / #682 §5)."""

  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parents[1]
  _ORCHESTRATOR = _REPO_ROOT / "agents" / "1-generic" / "orchestrator.md"


  def test_barrier_section_references_status_table_block():
      content = _ORCHESTRATOR.read_text(encoding="utf-8")
      barrier_start = content.index("## 7. BARRIER protocol")
      barrier_end = content.index("## 8. Reflection loop")
      barrier_section = content[barrier_start:barrier_end]
      assert "{{STATUS_TABLE_BLOCK}}" in barrier_section
  ```

- [ ] Step 2: Run test, verify it fails

  ```
  python3 -m pytest tests/test_status_table_orchestrator_reference.py -q
  ```
  Expected failure: assertion fails (placeholder not present yet).

- [ ] Step 3: Write minimal implementation

  Bump the frontmatter version in `agents/1-generic/orchestrator.md:3`:

  ```yaml
  version: "7.15.0"
  ```

  In §7 (current lines 149-158):

  ```markdown
  ## 7. BARRIER protocol
  BARRIER() actively collects ALL results. Results arrive as TOOL DATA — never fabricate a result, never paraphrase an outcome that has not arrived. "Wait" does not mean pause — it means process results as they arrive.

  1. Capture each tool response as it arrives
  2. Wrap it verbatim: `||| agent=<name> result_key=<key> status=<status> |||` (wrapper emitted by `scripts/lib/orchestration.py:render_barrier_result`; `status ∈ success | failed | timeout`)
  3. "[N] agents completed" only after exactly N tool responses — the count is derived, never assumed
  4. Partial results (`status: partial | failed | timeout`): re-dispatch only the failed tasks (§10) — never merge failed entries into a success narrative; contradictions → `main_chat`, do not auto-merge
  5. `Full output: <checkpoint_ref>` lines are pointers into the archived raw output (§9) — follow the reference instead of re-requesting raw output

  Artifact pattern for output >200 lines: subagent writes to an artifact directory (`<handoff_id>-<type>.md`), returns only the reference.
  ```

  becomes (inserting the block reference right after point 5, before the artifact-pattern paragraph):

  ```markdown
  ## 7. BARRIER protocol
  BARRIER() actively collects ALL results. Results arrive as TOOL DATA — never fabricate a result, never paraphrase an outcome that has not arrived. "Wait" does not mean pause — it means process results as they arrive.

  1. Capture each tool response as it arrives
  2. Wrap it verbatim: `||| agent=<name> result_key=<key> status=<status> |||` (wrapper emitted by `scripts/lib/orchestration.py:render_barrier_result`; `status ∈ success | failed | timeout`)
  3. "[N] agents completed" only after exactly N tool responses — the count is derived, never assumed
  4. Partial results (`status: partial | failed | timeout`): re-dispatch only the failed tasks (§10) — never merge failed entries into a success narrative; contradictions → `main_chat`, do not auto-merge
  5. `Full output: <checkpoint_ref>` lines are pointers into the archived raw output (§9) — follow the reference instead of re-requesting raw output

  {{STATUS_TABLE_BLOCK}}

  Artifact pattern for output >200 lines: subagent writes to an artifact directory (`<handoff_id>-<type>.md`), returns only the reference.
  ```

- [ ] Step 4: Run test, verify it passes

  ```
  python3 -m pytest tests/test_status_table_orchestrator_reference.py -q
  ```

- [ ] Step 5: Re-sync and validate

  ```
  python scripts/sync.py
  python3 scripts/sync.py --validate
  ```

- [ ] Step 6: Commit

  ```
  git add agents/1-generic/orchestrator.md tests/test_status_table_orchestrator_reference.py
  git commit -m "feat: mandate status-table reporting in orchestrator subagent BARRIER protocol (#678)"
  ```

---

### Task 11: `Checkpoint.status_summary` field

**Files:**
- Modify: `scripts/lib/checkpoint.py:48-94` (`Checkpoint.__init__`, `to_dict`, `from_dict`)
- Test: `tests/test_checkpoint_status_summary.py` (new)

**Interfaces:**
- Consumes: nothing new (optional constructor kwarg, backward compatible — `from_dict` on old JSON without the key must not crash).
- Produces: `Checkpoint.status_summary: str | None`, consumed by Task 12's progress-markdown renderer.

- [ ] Step 1: Write the failing test

  Create `tests/test_checkpoint_status_summary.py`:

  ```python
  """Checkpoint.status_summary field (issue #682 §6, Option A).

  Optional, backward compatible: existing checkpoint JSON without the key
  must still load (old sessions predate this field).
  """

  import sys
  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(_REPO_ROOT / "scripts"))

  from lib.checkpoint import Checkpoint  # noqa: E402


  def test_status_summary_round_trips_through_to_dict_from_dict():
      cp = Checkpoint(
          task_id="t1", agent="developer", task_description="implement X",
          status="completed", status_summary="developer: done. tester: pending.",
      )
      restored = Checkpoint.from_dict(cp.to_dict())
      assert restored.status_summary == "developer: done. tester: pending."


  def test_status_summary_defaults_to_none():
      cp = Checkpoint(task_id="t1", agent="developer", task_description="x", status="pending")
      assert cp.status_summary is None
      assert cp.to_dict()["status_summary"] is None


  def test_from_dict_without_status_summary_key_does_not_crash():
      # Simulates a checkpoint JSON written before this field existed.
      legacy_dict = {
          "task_id": "t1", "agent": "developer", "task_description": "x",
          "status": "completed",
      }
      restored = Checkpoint.from_dict(legacy_dict)
      assert restored.status_summary is None
  ```

- [ ] Step 2: Run test, verify it fails

  ```
  python3 -m pytest tests/test_checkpoint_status_summary.py -q
  ```
  Expected failure: `TypeError: __init__() got an unexpected keyword argument 'status_summary'`.

- [ ] Step 3: Write minimal implementation

  In `scripts/lib/checkpoint.py`, `Checkpoint.__init__` (lines 51-68):

  ```python
      def __init__(
          self,
          task_id: str,
          agent: str,
          task_description: str,
          status: str,  # "pending", "in_progress", "completed", "failed"
          result: str | None = None,
          next_step: str | None = None,
          status_summary: str | None = None,
          timestamp: float | None = None,
      ):
          self.id = str(uuid.uuid4())
          self.task_id = task_id
          self.agent = agent
          self.task_description = task_description
          self.status = status
          self.result = result
          self.next_step = next_step
          self.status_summary = status_summary
          self.timestamp = timestamp or time.time()
  ```

  `to_dict` (lines 70-80):

  ```python
      def to_dict(self) -> dict:
          return {
              "id": self.id,
              "task_id": self.task_id,
              "agent": self.agent,
              "task_description": self.task_description,
              "status": self.status,
              "result": self.result,
              "next_step": self.next_step,
              "status_summary": self.status_summary,
              "timestamp": self.timestamp,
          }
  ```

  `from_dict` (lines 82-94):

  ```python
      @classmethod
      def from_dict(cls, data: dict) -> "Checkpoint":
          cp = cls(
              task_id=data["task_id"],
              agent=data["agent"],
              task_description=data["task_description"],
              status=data["status"],
              result=data.get("result"),
              next_step=data.get("next_step"),
              status_summary=data.get("status_summary"),
              timestamp=data.get("timestamp"),
          )
          cp.id = data.get("id", cp.id)
          return cp
  ```

- [ ] Step 4: Run test, verify it passes

  ```
  python3 -m pytest tests/test_checkpoint_status_summary.py -q
  ```

- [ ] Step 5: Regression-check the existing checkpoint suite

  ```
  python3 -m pytest tests/test_checkpoint_raw_output.py -q
  ```

- [ ] Step 6: Commit

  ```
  git add scripts/lib/checkpoint.py tests/test_checkpoint_status_summary.py
  git commit -m "feat: add optional status_summary field to Checkpoint (#682)"
  ```

---

### Task 12: `.claude/progress/current.md` write-through on every checkpoint save

**Files:**
- Modify: `scripts/lib/checkpoint.py` (new `_render_progress_markdown()` module function + `CheckpointStore.save_checkpoint()` extension, around lines 175-196)
- Test: `tests/test_progress_file.py` (new)

**Interfaces:**
- Consumes: `session_data: dict` (the same dict `save_checkpoint()` already assembles and passes to `save_json_document()`) and `Checkpoint.status_summary` from Task 11.
- Produces: `<project_root>/.claude/progress/current.md`, overwritten (not historized) on every `save_checkpoint()` call. Reuses `write_atomic` (already imported in `checkpoint.py:25`).

- [ ] Step 1: Write the failing test

  Create `tests/test_progress_file.py`:

  ```python
  """.claude/progress/current.md write-through on every checkpoint save
  (issue #682 §6, Option A) -- human-readable progress snapshot, overwritten
  each time, not historized. Reuses the same table format as the orchestrator
  status-table snippet (issue #678) so the text can be copy-pasted between
  the two surfaces."""

  import sys
  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(_REPO_ROOT / "scripts"))

  from lib.checkpoint import Checkpoint, CheckpointStore  # noqa: E402


  def _store(tmp_path: Path) -> CheckpointStore:
      return CheckpointStore(project_root=tmp_path)


  def test_save_checkpoint_writes_progress_file(tmp_path):
      store = _store(tmp_path)
      cp = Checkpoint(
          task_id="t1", agent="developer", task_description="implement X",
          status="completed", status_summary="On track.",
      )
      store.save_checkpoint("sess1", cp)
      progress_path = tmp_path / ".claude" / "progress" / "current.md"
      assert progress_path.exists()
      content = progress_path.read_text(encoding="utf-8")
      assert "developer" in content
      assert "implement X" in content
      assert "completed" in content
      assert "On track." in content


  def test_progress_file_is_overwritten_not_appended(tmp_path):
      store = _store(tmp_path)
      store.save_checkpoint(
          "sess1", Checkpoint(task_id="t1", agent="developer", task_description="first", status="completed")
      )
      store.save_checkpoint(
          "sess1", Checkpoint(task_id="t2", agent="tester", task_description="second", status="in_progress")
      )
      content = (tmp_path / ".claude" / "progress" / "current.md").read_text(encoding="utf-8")
      # Both checkpoints of the session appear (cumulative table), but the
      # file itself was overwritten (single write_atomic call), not appended to.
      assert "first" in content
      assert "second" in content
      assert content.count("| Agent | Task | Status |") == 1


  def test_progress_file_survives_corrupt_existing_session_json(tmp_path):
      store = _store(tmp_path)
      # Simulate a corrupt session file (#576 fail-soft contract) -- must not
      # crash the progress write either.
      store.checkpoint_dir.mkdir(parents=True)
      (store.checkpoint_dir / "sess1.json").write_text("{not valid json", encoding="utf-8")
      store.save_checkpoint(
          "sess1", Checkpoint(task_id="t1", agent="developer", task_description="x", status="pending")
      )
      assert (tmp_path / ".claude" / "progress" / "current.md").exists()
  ```

- [ ] Step 2: Run test, verify it fails

  ```
  python3 -m pytest tests/test_progress_file.py -q
  ```
  Expected failure: `assert progress_path.exists()` is False.

- [ ] Step 3: Write minimal implementation

  In `scripts/lib/checkpoint.py`, add a module-level helper right before the `CheckpointStore` class (before line 97):

  ```python
  _PROGRESS_DIR = ".claude/progress"


  def _render_progress_markdown(session_data: dict) -> str:
      """Render a session's checkpoints as the same status-table format used
      by the orchestrator's mandatory status-table rule (issue #678) --
      human-readable progress snapshot, not the resume-machinery JSON.
      """
      session_id = session_data.get("session_id", "unknown")
      checkpoints = session_data.get("checkpoints", [])
      lines = [f"# Progress — session `{session_id}`", ""]
      latest_summary = next(
          (cp.get("status_summary") for cp in reversed(checkpoints) if cp.get("status_summary")),
          None,
      )
      if latest_summary:
          lines.append(latest_summary)
          lines.append("")
      lines.append("| Agent | Task | Status |")
      lines.append("|-------|------|--------|")
      for cp in checkpoints:
          agent = cp.get("agent", "?")
          task = cp.get("task_description", "?")
          status = cp.get("status", "?")
          lines.append(f"| `{agent}` | {task} | `{status}` |")
      lines.append("")
      return "\n".join(lines)
  ```

  Extend `CheckpointStore.save_checkpoint()` (current lines 175-196):

  ```python
      def save_checkpoint(self, session_id: str, checkpoint: Checkpoint) -> None:
          """Append checkpoint to session file.

          A corrupt existing session file (#576) is treated as an empty one —
          the new checkpoint still gets saved instead of crashing the whole
          orchestration on a single damaged file.

          Issue #682 §6: also overwrites .claude/progress/current.md with a
          human-readable snapshot of the same session data -- non-historized,
          for a human glancing at the repo, not for resume logic.
          """
          self._ensure_dir()
          path = self._session_file(session_id)

          existing = load_json_document(path, default={})
          checkpoints = existing.get("checkpoints", []) if isinstance(existing, dict) else []

          checkpoints.append(checkpoint.to_dict())

          session_data = {
              "session_id": session_id,
              "created_at": checkpoints[0].get("timestamp", time.time()) if checkpoints else time.time(),
              "updated_at": time.time(),
              "checkpoints": checkpoints,
          }
          save_json_document(path, session_data)
          self._write_progress_file(session_data)

      def _write_progress_file(self, session_data: dict) -> None:
          """Overwrite .claude/progress/current.md -- see _render_progress_markdown."""
          progress_path = self.project_root / _PROGRESS_DIR / "current.md"
          progress_path.parent.mkdir(parents=True, exist_ok=True)
          write_atomic(progress_path, _render_progress_markdown(session_data))
  ```

- [ ] Step 4: Run test, verify it passes

  ```
  python3 -m pytest tests/test_progress_file.py -q
  ```

- [ ] Step 5: Regression-check the full checkpoint module

  ```
  python3 -m pytest tests/test_checkpoint_raw_output.py tests/test_checkpoint_status_summary.py tests/test_progress_file.py -q
  ```

- [ ] Step 6: Commit

  ```
  git add scripts/lib/checkpoint.py tests/test_progress_file.py
  git commit -m "feat: write .claude/progress/current.md on every checkpoint save (#682)"
  ```

---

### Task 13: Document the progress file in the checkpointing snippet + orchestrator.md §9

**Files:**
- Modify: `snippets/orchestrator/checkpointing.md` (append a short note)
- Modify: `agents/1-generic/orchestrator.md:165-169` (§9, already version-bumped in Task 10 — no second bump needed here)
- Test: `tests/test_progress_file_documented.py` (new)

**Interfaces:**
- Consumes: nothing new.
- Produces: updated LLM-facing instructions only (the orchestrator agent still writes its own `checkpoint-<timestamp>.json` by hand per the existing textual convention documented in §9 — see the note below on why this stays text-only, not `CheckpointStore`-mediated).

**Note on the two coexisting checkpoint mechanisms (read before editing):** `orchestrator.md` §9 describes two different things under one heading: (a) a manually-LLM-written `.meta-viz/checkpoint-<timestamp>.json` file (the orchestrator agent itself uses its Write tool, following the textual format spec — no Python code produces this file), and (b) the harness-side `CheckpointStore.save_raw_output`/`save_checkpoint` API from `scripts/lib/checkpoint.py` (Task 11/12's target), used for raw-output archiving under `.meta-viz/checkpoints/<session-id>/`. This task only documents (b)'s new progress-file behavior — it does NOT change the orchestrator agent's own manual (a)-style checkpoint-writing instructions, since that would be a larger, out-of-scope behavioral change to how the LLM self-checkpoints.

- [ ] Step 1: Write the failing test

  Create `tests/test_progress_file_documented.py`:

  ```python
  """Progress-file behavior (issue #682 §6) must be documented where a
  developer would look for checkpoint/progress semantics."""

  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parents[1]


  def test_checkpointing_snippet_documents_progress_file():
      content = (_REPO_ROOT / "snippets" / "orchestrator" / "checkpointing.md").read_text(encoding="utf-8")
      assert ".claude/progress/current.md" in content


  def test_orchestrator_section_9_documents_progress_file():
      content = (_REPO_ROOT / "agents" / "1-generic" / "orchestrator.md").read_text(encoding="utf-8")
      section_9_start = content.index("## 9. Context guard & checkpointing")
      section_10_start = content.index("## 10. Delegation failure recovery")
      section_9 = content[section_9_start:section_10_start]
      assert ".claude/progress/current.md" in section_9
  ```

- [ ] Step 2: Run test, verify it fails

  ```
  python3 -m pytest tests/test_progress_file_documented.py -q
  ```
  Expected failure: both assertions fail (string not present yet).

- [ ] Step 3: Write minimal implementation

  In `snippets/orchestrator/checkpointing.md`, append right before the closing `{{/if}}`:

  ```markdown

  **Progress-Datei (issue #682 §6):** Bei jedem `CheckpointStore.save_checkpoint()`-Aufruf
  wird zusätzlich `.claude/progress/current.md` überschrieben (nicht historisiert) — ein
  menschenlesbarer Snapshot im selben `Agent | Task | Status`-Format wie die
  Status-Tabelle (§5-Regel). Für Resume-Logik weiterhin die JSON-Checkpoints verwenden,
  `current.md` ist nur für den schnellen menschlichen Blick in den Fortschritt gedacht.
  ```

  In `agents/1-generic/orchestrator.md` §9 (current lines 165-169), append one sentence after the existing "Summarization-as-a-Contract" paragraph (after line 169):

  ```markdown

  **Progress file (issue #682 §6):** every `CheckpointStore.save_checkpoint()` call also overwrites `.claude/progress/current.md` (non-historized) with a human-readable `Agent | Task | Status` snapshot — same format as the mandatory status table (§7). Resume logic still reads the JSON checkpoints; `current.md` is for a human glancing at the repo, not parsed by any code path.
  ```

- [ ] Step 4: Run test, verify it passes

  ```
  python3 -m pytest tests/test_progress_file_documented.py -q
  ```

- [ ] Step 5: Re-sync and validate

  ```
  python scripts/sync.py
  python3 scripts/sync.py --validate
  ```

- [ ] Step 6: Commit

  ```
  git add snippets/orchestrator/checkpointing.md agents/1-generic/orchestrator.md tests/test_progress_file_documented.py
  git commit -m "docs: document .claude/progress/current.md write-through in checkpointing docs (#682)"
  ```

---

### Task 14: Full validation pass + CHANGELOG entry

**Files:**
- Modify: `CHANGELOG.md` (append to the `## [Unreleased]` → `### Added` section)
- No new tests (this task validates the sum of Tasks 1-13).

**Interfaces:**
- Consumes: everything built in Tasks 1-13.
- Produces: a green full test suite, a clean `--validate` pass, and a changelog entry — the definition of done for this plan.

- [ ] Step 1: Run the full test suite

  ```
  python3 -m pytest tests/ -o consider_namespace_packages=true -q
  ```
  Verify: 0 failures, and specifically that no pre-existing test regressed (`tests/test_gitignore_provider_dirs.py`, `tests/test_checkpoint_raw_output.py`, `tests/test_config_variable_fallbacks.py`, `tests/test_build_variables_decomposition.py` all still green).

- [ ] Step 2: Run the sync validator and a full re-sync of this repo's own generated files

  ```
  python3 scripts/sync.py --validate
  python scripts/sync.py
  git status --short
  ```
  Verify: `--validate` reports no new errors/warnings; `git status --short` shows only the expected regenerated files under `.claude/`, `.gemini/`, etc. plus this plan's source edits — no unexpected drift.

- [ ] Step 3: Manually exercise the four features end-to-end

  - README standard: `python3 -c "from scripts.lib.config import build_variables; from pathlib import Path; v,_ = build_variables({'readme': {'badges': ['version','ci'], 'warnings': True}}, Path('.')); print(v['README_BADGES'], v['README_WARNINGS_ENABLED'])"` → prints `version, ci true`.
  - .gitignore bugfix: `python3 -m pytest tests/test_gitignore_context_file_protection.py tests/test_gitignore_provider_dirs.py -q`.
  - Setup wizard: `python3 -m pytest tests/test_setup_wizard_secrets_prompt.py -q`.
  - Status table + progress file: `grep -A5 "Status-Tabelle" .claude/rules/use-orchestrator.md .claude/agents/orchestrator.md` shows the rendered block in both generated files with no leftover `{{...}}`.

- [ ] Step 4: Write the CHANGELOG entry

  In `CHANGELOG.md`, under `## [Unreleased]` → `### Added`, prepend:

  ```markdown
  - **Governance quick-wins (#682)**: README structure standard (`readme.badges`/
    `readme.warnings`/`readme.sections` in `project.yaml`, new
    `templates/configs/README-template.md`, additive `documenter.md` §5 rewrite —
    same managed-block, non-overwriting principle as `.gitignore`); `.gitignore`
    context-file protection now resolves Claude's protected context file from its
    own provider config instead of a hardcoded `"CLAUDE.md"` literal; `sync.py
    --setup` offers (not silently defaults) typical secret-pattern `.gitignore`
    entries (`.env*`, `*.pem`, `*.key`, `credentials*.json`, `secret*.y*ml`);
    mandatory orchestrator status-table reporting after every batch member and
    BARRIER point (issue #678, new `snippets/orchestrator/status-table.md`,
    `{{STATUS_TABLE_BLOCK}}` in both `use-orchestrator.md` and `orchestrator.md`);
    `CheckpointStore.save_checkpoint()` now also overwrites
    `.claude/progress/current.md` with a human-readable, non-historized
    `Agent | Task | Status` snapshot.
  ```

- [ ] Step 5: Commit

  ```
  git add CHANGELOG.md
  git commit -m "docs: changelog entry for governance quick-wins (#682)"
  ```

---

## Self-Review Notes

- **Spec coverage:** §3 (README) → Tasks 1-4. §4 (.gitignore) → Tasks 5-6. §5 (status table) → Tasks 7-10. §6 (progress system) → Tasks 11-13. Task 14 closes the loop for all four.
- **Explicitly not built** (per the issue's own recommendation, documented in Global Constraints): CLAUDE.md/AGENTS.md ignorability change, `gitignore.generated` default flip, CI badge as a default (only opt-in + runtime-detected).
- **Pre-existing gap found during research, deliberately left alone:** `SE_MODE_BLOCK`/`CHECKPOINTING_BLOCK`/`QUALITY_PIPELINES_BLOCK` are built by `_build_snippet_variables()` but not referenced by any current template — an existing gap unrelated to this plan. `STATUS_TABLE_BLOCK` (Task 8) is deliberately wired to real references (Tasks 9-10) so it doesn't join that orphaned set.
- **Type/placeholder consistency:** every new `{{VAR}}` (`README_BADGES`, `README_WARNINGS_ENABLED`, `README_SECTIONS`, `STATUS_TABLE_BLOCK`) has all three required registrations (build_variables, placeholders `_BUILTIN_VARS`, standalone fallback) — cross-checked task by task above.
- **No breaking changes:** every new schema key defaults to today's exact behavior; the gitignore bugfix is behavior-neutral for the real `config/ai-providers.yaml`; the setup-wizard question defaults to "yes" but is asked, not silently applied.
