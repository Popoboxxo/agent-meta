# Auto-Commit Tiers (Issue #694) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let write-capable agents commit directly (not only the dedicated `git` role) under an opt-in, tiered `auto_commit` config, with a configurable set of trigger conditions and a provider-agnostic two-layer enforcement model.

**Architecture:** A new `scripts/lib/auto_commit.py` module resolves the project's `auto_commit` config into (a) a rendered prompt-instruction block injected into every write-capable `1-generic` agent template, and (b) a generated role-eligibility allowlist consumed by `orchestrator-guard-impl.sh` on the 4 hook-capable providers. Trigger *evaluation* (did tests pass, is this a task boundary) stays entirely prompt-side — the hook only ever checks *authorization* (is this sentinel + role permitted to commit right now), mirroring the existing `git`/`orchestrator` sentinel split.

**Tech Stack:** Python 3.9+ stdlib only (this repo's existing constraint), Bash + embedded Python for the hook (matches `orchestrator-guard-impl.sh`'s existing style), pytest.

**Spec:** `docs/superpowers/specs/2026-09-07-auto-commit-tiers-design.md`

## Global Constraints

- Python 3.9 floor: any `X | Y` union type hint in a new/edited `.py` file requires `from __future__ import annotations` at the top of that file (this repo's own established hazard class — hit repeatedly in earlier work this cycle).
- No external Python dependencies — stdlib only (`CLAUDE.md` Code-Konventionen).
- `{{PLACEHOLDER}}` naming is always `{{GROSS_MIT_UNTERSTRICH}}` — no lowercase/mixed case.
- Default `auto_commit.mode` is `off` — zero behavior change for any project that doesn't opt in (spec Scope section).
- `push`, `tag`, and branch management remain exclusively the `git` role's job — never touched by this plan (spec Scope section, "Explicitly out of scope").
- The destructive-operation gate in `orchestrator-guard-impl.sh` is untouched — it must keep blocking regardless of sentinel (spec "Security framing").
- Trigger *evaluation* is prompt-side only; the hook only ever checks *authorization* (spec "Trigger evaluation stays prompt-side").
- Every new/changed `1-generic` role template gets its frontmatter `version:` bumped **minor** (`x.Y.0`, patch reset to `0`) per `rules/2-platform/agent-meta-conventions.md` Hard Invariant #2 ("new optional section, expanded scope").
- New `project.yaml` config keys added in this plan must be registered in `config/project-config.schema.json` AND validated (`sync.py --validate` clean) before any task is considered done.
- Per this repo's own convention (`rules/2-platform/agent-meta-conventions.md` → Change Checklist, `tests/scenarios/registry.md`), this feature needs its own entry in `tests/scenarios/` before the plan is complete (Task 9).

---

### Task 1: `auto_commit` config schema

**Files:**
- Modify: `config/project-config.schema.json` (add `auto_commit` to `properties`)
- Modify: `templates/configs/project.yaml.example` (annotated example, same style as the existing `gitignore:`/`readme:` blocks)
- Test: `tests/test_auto_commit_schema.py` (new)

**Interfaces:**
- Consumes: nothing new.
- Produces: the `auto_commit` config shape every later task reads via `config.get("auto_commit", {})`.

- [ ] **Step 1: Write the failing test**

  Create `tests/test_auto_commit_schema.py`:

  ```python
  """auto_commit config schema (issue #694): mode enum, trigger enum, and the
  two invalid-combination rules -- triggers set without mode: auto, and
  mode: custom / triggers containing "custom" without a custom_script."""

  import json
  import sys
  from pathlib import Path

  import jsonschema
  import pytest

  _REPO_ROOT = Path(__file__).resolve().parent.parent
  _SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"


  def _schema() -> dict:
      with _SCHEMA_PATH.open(encoding="utf-8") as f:
          return json.load(f)


  def _base_config(auto_commit: dict) -> dict:
      return {
          "project": {"name": "t", "prefix": "t"},
          "ai-providers": ["Claude"],
          "roles": ["orchestrator", "developer", "git"],
          "auto_commit": auto_commit,
      }


  def test_mode_off_is_valid_minimal():
      jsonschema.validate(_base_config({"mode": "off"}), _schema())


  def test_mode_auto_with_triggers_is_valid():
      jsonschema.validate(
          _base_config({"mode": "auto", "triggers": ["task-boundary", "context-pressure"]}),
          _schema(),
      )


  def test_invalid_mode_value_rejected():
      with pytest.raises(jsonschema.ValidationError):
          jsonschema.validate(_base_config({"mode": "sometimes"}), _schema())


  def test_invalid_trigger_value_rejected():
      with pytest.raises(jsonschema.ValidationError):
          jsonschema.validate(
              _base_config({"mode": "auto", "triggers": ["whenever-i-feel-like-it"]}),
              _schema(),
          )


  def test_duplicate_triggers_rejected():
      with pytest.raises(jsonschema.ValidationError):
          jsonschema.validate(
              _base_config({"mode": "auto", "triggers": ["per-edit", "per-edit"]}),
              _schema(),
          )


  def test_file_count_threshold_must_be_positive_int():
      with pytest.raises(jsonschema.ValidationError):
          jsonschema.validate(
              _base_config({"mode": "auto", "triggers": ["file-count-threshold"], "file_count_threshold": 0}),
              _schema(),
          )
  ```

- [ ] **Step 2: Run test, verify it fails**

  ```
  python3 -m pytest tests/test_auto_commit_schema.py -q
  ```
  Expected failure: `test_mode_off_is_valid_minimal` fails with a jsonschema `ValidationError` about `additionalProperties` — `auto_commit` doesn't exist in the schema yet.

- [ ] **Step 3: Write minimal implementation**

  In `config/project-config.schema.json`, add a new top-level property (alphabetical position, next to `admin-ui`/`allow-committed-secrets`):

  ```json
  "auto_commit": {
    "type": "object",
    "description": "Issue #694: opt-in tiered commit authority for write-capable agents (not just the dedicated git role). Default: mode 'off' -- zero behavior change. 'suggest' has agents propose a commit message in their own report, never running git themselves. 'auto' commits directly when any selected trigger fires. 'custom' hands the entire commit decision to custom_script, ignoring the built-in triggers list entirely.",
    "properties": {
      "mode": {
        "type": "string",
        "enum": ["off", "suggest", "auto", "custom"],
        "default": "off",
        "description": "off = today's behavior (only the git role commits). suggest = agents propose commit messages in their report, never run git. auto = agents commit directly when a selected trigger (see 'triggers') fires. custom = custom_script alone decides, all built-in triggers ignored."
      },
      "triggers": {
        "type": "array",
        "description": "Only consulted when mode is 'auto'. Any one firing is enough to commit (OR'd). Ignored (and rejected by validation) when mode is not 'auto'.",
        "items": {
          "type": "string",
          "enum": ["task-boundary", "per-edit", "context-pressure", "file-count-threshold", "custom"]
        },
        "uniqueItems": true,
        "default": []
      },
      "file_count_threshold": {
        "type": "integer",
        "minimum": 1,
        "default": 5,
        "description": "Only read when 'file-count-threshold' is in triggers. Commit after this many files have changed since the last commit."
      },
      "custom_script": {
        "type": ["string", "null"],
        "default": null,
        "description": "Path to a project script. Exit code 0 means 'commit now'. Required when mode is 'custom', or when 'custom' appears in triggers under mode 'auto'."
      },
      "secret_scan": {
        "type": "boolean",
        "default": true,
        "description": "Run the project's existing secret scan (scripts/lib/secrets.py::scan_for_secrets) against the staged diff before any auto/custom commit. Default true; set false to skip (explicit opt-out, not a silent gap)."
      }
    },
    "additionalProperties": false
  }
  ```

  In `templates/configs/project.yaml.example`, add near the existing `gitignore:`/`readme:` annotated blocks:

  ```yaml
  # auto_commit:
  #   # mode: off (Default) -> nur die git-Rolle committet, wie bisher.
  #   #   suggest -> Agenten schlagen eine Commit-Message im eigenen Report vor,
  #   #     committen NICHT selbst.
  #   #   auto -> Agenten committen direkt, sobald ein gewaehlter Trigger feuert.
  #   #   custom -> custom_script entscheidet allein, eingebaute Trigger werden ignoriert.
  #   mode: off
  #   # triggers: nur bei mode: auto relevant, ODER-verknuepft, Mehrfachauswahl:
  #   #   task-boundary (Teilaufgabe fertig + Tests gruen), per-edit (nach jedem
  #   #   Write/Edit), context-pressure (vor Checkpoint/Context-Compaction),
  #   #   file-count-threshold (siehe file_count_threshold), custom (custom_script
  #   #   stimmt zusaetzlich mit ab).
  #   triggers: [task-boundary]
  #   file_count_threshold: 5
  #   custom_script: null
  #   secret_scan: true
  ```

- [ ] **Step 4: Run test, verify it passes**

  ```
  python3 -m pytest tests/test_auto_commit_schema.py -q
  ```

- [ ] **Step 5: Regression-check schema validation end to end**

  There is no single generic "whole schema" test file in this repo —
  per-feature schema tests live in their own file (e.g. `test_readme_schema.py`
  for the `readme` block); `tests/test_auto_commit_schema.py` from Step 1 is
  this feature's equivalent. Re-run it plus the real sync validator:

  ```
  python3 -m pytest tests/test_auto_commit_schema.py -q
  python3 scripts/sync.py --validate
  ```

- [ ] **Step 6: Commit**

  ```bash
  git add config/project-config.schema.json templates/configs/project.yaml.example tests/test_auto_commit_schema.py
  git commit -m "feat: add auto_commit config schema (#694)"
  ```

---

### Task 2: `scripts/lib/auto_commit.py` — role eligibility + allowlist shape

**Files:**
- Create: `scripts/lib/auto_commit.py`
- Test: `tests/test_auto_commit_lib.py` (new)

**Interfaces:**
- Consumes: `parse_frontmatter_file(path: Path) -> dict` (`scripts/lib/frontmatter.py`, already existing — returns a dict including a `tools` key when the frontmatter has one), `resolve_role_template_path()`-equivalent lookup (see Step 3 — this task resolves each active role's template path the same way `agent_sync.py` already does, via `config/role-defaults.yaml` + `agents/1-generic/<role>.md`, falling back to `2-platform` overrides when a platform is active).
- Produces: `is_role_eligible(role: str, agent_meta_root: Path, platform: str | None) -> bool`, `resolve_auto_commit_config(config: dict, active_roles: list[str], agent_meta_root: Path, platform: str | None = None) -> dict` (returns the exact allowlist shape from the spec: `{"version": 1, "mode": ..., "eligible_roles": [...], "triggers": [...], "secret_scan": ...}`), consumed by Task 6 (sync pipeline wiring).

- [ ] **Step 1: Write the failing test**

  Create `tests/test_auto_commit_lib.py`:

  ```python
  """scripts/lib/auto_commit.py: role-eligibility derivation and allowlist
  shape (issue #694). Eligibility is capability-derived from each role's
  OWN template frontmatter tools: list -- never a hand-maintained list."""

  from __future__ import annotations

  import sys
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

  from lib.auto_commit import is_role_eligible, resolve_auto_commit_config  # noqa: E402

  _REPO_ROOT = Path(__file__).resolve().parent.parent


  def test_developer_is_eligible():
      # agents/1-generic/developer.md tools: includes Write and Edit.
      assert is_role_eligible("developer", _REPO_ROOT) is True


  def test_git_is_not_eligible():
      # agents/1-generic/git.md tools: is Bash/Read/Glob/Grep/TodoWrite only --
      # no Edit/Write. It doesn't need this mechanism, it already has full
      # commit authority via its own dedicated sentinel.
      assert is_role_eligible("git", _REPO_ROOT) is False


  def test_explorer_is_not_eligible():
      # Read-only role -- must never become commit-eligible even if listed
      # as an active role.
      assert is_role_eligible("explorer", _REPO_ROOT) is False


  def test_resolve_config_mode_off_returns_empty_allowlist():
      result = resolve_auto_commit_config(
          config={"auto_commit": {"mode": "off"}},
          active_roles=["orchestrator", "developer", "git"],
          agent_meta_root=_REPO_ROOT,
      )
      assert result["mode"] == "off"
      assert result["eligible_roles"] == []


  def test_resolve_config_auto_mode_lists_only_eligible_active_roles():
      result = resolve_auto_commit_config(
          config={"auto_commit": {"mode": "auto", "triggers": ["task-boundary"]}},
          active_roles=["orchestrator", "developer", "git", "tester"],
          agent_meta_root=_REPO_ROOT,
      )
      assert result["mode"] == "auto"
      assert "developer" in result["eligible_roles"]
      assert "tester" in result["eligible_roles"]
      assert "git" not in result["eligible_roles"]  # already has its own path
      assert result["triggers"] == ["task-boundary"]


  def test_resolve_config_defaults_secret_scan_true():
      result = resolve_auto_commit_config(
          config={"auto_commit": {"mode": "auto", "triggers": ["per-edit"]}},
          active_roles=["developer"],
          agent_meta_root=_REPO_ROOT,
      )
      assert result["secret_scan"] is True


  def test_resolve_config_missing_auto_commit_key_defaults_to_off():
      result = resolve_auto_commit_config(
          config={},
          active_roles=["orchestrator", "developer", "git"],
          agent_meta_root=_REPO_ROOT,
      )
      assert result["mode"] == "off"
      assert result["eligible_roles"] == []
  ```

- [ ] **Step 2: Run test, verify it fails**

  ```
  python3 -m pytest tests/test_auto_commit_lib.py -q
  ```
  Expected failure: `ModuleNotFoundError: No module named 'lib.auto_commit'`.

- [ ] **Step 3: Write minimal implementation**

  Create `scripts/lib/auto_commit.py`:

  ```python
  """Issue #694: opt-in tiered commit authority for write-capable agents.

  Role eligibility is derived from each role's OWN generic template
  frontmatter `tools:` list (Edit or Write present) -- never a
  hand-maintained allowlist, so it stays correct as new roles are added.
  """

  from __future__ import annotations

  from pathlib import Path

  from .frontmatter import parse_frontmatter_file

  _ELIGIBLE_TOOLS = {"Edit", "Write"}

  ALLOWLIST_VERSION = 1


  def _template_path(role: str, agent_meta_root: Path, platform: str | None = None) -> Path | None:
      """Resolve a role's own generic template path.

      Platform overrides (agents/2-platform/<platform>-<role>.md) are not
      consulted here on purpose: eligibility must reflect the role's BASE
      tools contract, which platforms compose onto (extend), never replace
      the tools list of. If a future platform ever does replace `tools:`,
      revisit this -- out of scope for issue #694.
      """
      candidate = agent_meta_root / "agents" / "1-generic" / f"{role}.md"
      return candidate if candidate.is_file() else None


  def is_role_eligible(role: str, agent_meta_root: Path, platform: str | None = None) -> bool:
      """True if `role`'s own template declares Edit or Write in tools:."""
      path = _template_path(role, agent_meta_root, platform)
      if path is None:
          return False
      frontmatter = parse_frontmatter_file(path)
      tools = frontmatter.get("tools") or []
      return bool(_ELIGIBLE_TOOLS.intersection(tools))


  def resolve_auto_commit_config(
      config: dict,
      active_roles: list[str],
      agent_meta_root: Path,
      platform: str | None = None,
  ) -> dict:
      """Resolve project.yaml's auto_commit block into the allowlist shape
      written to .meta-config/auto-commit-allowlist.json by the sync
      pipeline (Task 6)."""
      ac_cfg = config.get("auto_commit", {}) or {}
      mode = ac_cfg.get("mode", "off")

      eligible_roles: list[str] = []
      if mode != "off":
          eligible_roles = sorted(
              role
              for role in active_roles
              if is_role_eligible(role, agent_meta_root, platform)
          )

      return {
          "version": ALLOWLIST_VERSION,
          "mode": mode,
          "eligible_roles": eligible_roles,
          "triggers": list(ac_cfg.get("triggers", [])),
          "file_count_threshold": ac_cfg.get("file_count_threshold", 5),
          "custom_script": ac_cfg.get("custom_script"),
          "secret_scan": ac_cfg.get("secret_scan", True),
      }
  ```

- [ ] **Step 4: Run test, verify it passes**

  ```
  python3 -m pytest tests/test_auto_commit_lib.py -q
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add scripts/lib/auto_commit.py tests/test_auto_commit_lib.py
  git commit -m "feat: role-eligibility resolver for auto_commit (#694)"
  ```

---

### Task 3: `render_auto_commit_block()` + the 3-registration rule

**Files:**
- Modify: `scripts/lib/auto_commit.py` (add `render_auto_commit_block()`)
- Modify: `scripts/lib/config.py:635-636` (call the renderer, set `AUTO_COMMIT_ENABLED`/`AUTO_COMMIT_BLOCK`)
- Modify: `scripts/lib/consistency/placeholders.py` (`_BUILTIN_VARS`)
- Modify: `scripts/lib/standalone.py` (fallback dicts)
- Test: `tests/test_auto_commit_block_render.py` (new)

**Interfaces:**
- Consumes: `resolve_auto_commit_config()` from Task 2.
- Produces: `render_auto_commit_block(auto_commit_resolved: dict) -> str`; `variables["AUTO_COMMIT_ENABLED"]` ("true"/"false" string, `{{#if}}`-gate) and `variables["AUTO_COMMIT_BLOCK"]` (rendered prose), consumed by Tasks 4-5.

- [ ] **Step 1: Write the failing test**

  Create `tests/test_auto_commit_block_render.py`:

  ```python
  """render_auto_commit_block (issue #694): mode-aware prose, never mentions
  push/tag/branch (git role's exclusive job), correctly reflects the
  approved non-blocking suggest-tier behavior."""

  from __future__ import annotations

  import sys
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

  from lib.auto_commit import render_auto_commit_block  # noqa: E402


  def test_off_mode_renders_empty_string():
      assert render_auto_commit_block({"mode": "off"}) == ""


  def test_suggest_mode_says_propose_not_pause():
      block = render_auto_commit_block({"mode": "suggest", "triggers": [], "secret_scan": True})
      assert "propose" in block.lower() or "vorschlag" in block.lower() or "suggest" in block.lower()
      assert "pause" not in block.lower()
      assert "wait" not in block.lower() or "do not" in block.lower()


  def test_auto_mode_lists_active_triggers():
      block = render_auto_commit_block({
          "mode": "auto",
          "triggers": ["task-boundary", "context-pressure"],
          "secret_scan": True,
      })
      assert "task-boundary" in block
      assert "context-pressure" in block
      assert "per-edit" not in block  # not selected, must not be mentioned as active


  def test_custom_mode_mentions_custom_script():
      block = render_auto_commit_block({
          "mode": "custom", "custom_script": "scripts/should-commit.sh", "secret_scan": True,
      })
      assert "scripts/should-commit.sh" in block


  def test_no_mode_ever_mentions_push_tag_or_branch():
      for mode_cfg in (
          {"mode": "suggest", "triggers": [], "secret_scan": True},
          {"mode": "auto", "triggers": ["per-edit"], "secret_scan": True},
          {"mode": "custom", "custom_script": "x.sh", "secret_scan": True},
      ):
          block = render_auto_commit_block(mode_cfg).lower()
          assert "git push" not in block
          assert "git tag" not in block
  ```

- [ ] **Step 2: Run test, verify it fails**

  ```
  python3 -m pytest tests/test_auto_commit_block_render.py -q
  ```
  Expected failure: `ImportError: cannot import name 'render_auto_commit_block'`.

- [ ] **Step 3: Write minimal implementation**

  Append to `scripts/lib/auto_commit.py`:

  ```python
  _TRIGGER_PROSE = {
      "task-boundary": "a subtask is complete AND its tests are green",
      "per-edit": "after every Write/Edit tool call",
      "context-pressure": "just before a checkpoint or context-compaction event",
      "file-count-threshold": "after {n} files have changed since the last commit",
      "custom": "the project's custom_script (see below) also votes to commit",
  }


  def render_auto_commit_block(resolved: dict) -> str:
      """Render the {{AUTO_COMMIT_BLOCK}} prose for the resolved auto_commit
      config. Empty string when mode is 'off' (nothing to render). Never
      mentions push/tag/branch -- those remain the git role's exclusive job
      (issue #694 scope)."""
      mode = resolved.get("mode", "off")
      if mode == "off":
          return ""

      secret_scan = resolved.get("secret_scan", True)
      scan_line = (
          "Before committing, run the project's secret scan against your "
          "staged changes; a finding blocks the commit -- report it and ask "
          "for manual intervention instead of committing anyway."
          if secret_scan
          else "Secret scanning is disabled for this project (secret_scan: false)."
      )

      lines = [
          "**Commit authority (issue #694):** this project has "
          f"`auto_commit.mode: {mode}` enabled for your role.",
      ]

      if mode == "suggest":
          lines.append(
              "When a configured trigger condition is met, propose a "
              "ready-to-use commit message in your own final report -- do "
              "NOT run `git commit` yourself, and do not pause execution "
              "waiting for confirmation. The user or orchestrator decides "
              "when to act on your suggestion."
          )
      elif mode == "custom":
          script = resolved.get("custom_script")
          lines.append(
              f"Commit directly whenever `{script}` exits 0 (the project's "
              "own commit-decision script has full control; no other "
              "trigger applies)."
          )
          lines.append(scan_line)
          lines.append(
              "Prefix the Bash command with `#agent-meta:agent=<your-role-"
              "name>` as its first line before `git add`/`git commit` -- "
              "required for the guard hook to authorize the commit on "
              "hook-capable providers, harmless elsewhere."
          )
      else:  # auto
          triggers = resolved.get("triggers", [])
          threshold = resolved.get("file_count_threshold", 5)
          trigger_descriptions = [
              _TRIGGER_PROSE[t].format(n=threshold) for t in triggers if t in _TRIGGER_PROSE
          ]
          lines.append(
              "Commit directly as soon as ANY of the following is true: "
              + "; ".join(trigger_descriptions) + "."
          )
          lines.append(scan_line)
          lines.append(
              "Prefix the Bash command with `#agent-meta:agent=<your-role-"
              "name>` as its first line before `git add`/`git commit` -- "
              "required for the guard hook to authorize the commit on "
              "hook-capable providers, harmless elsewhere."
          )

      lines.append(
          "This never extends to `git push`, `git tag`, or branch "
          "management -- those remain exclusively the `git` role's job."
      )
      return "\n".join(lines)
  ```

  In `scripts/lib/config.py`, right after the README block (currently ending at line 635 with the `README_SECTIONS` assignment, before the `# PROJECT_GOAL:` comment on line 636), insert:

  ```python
      # Auto-commit tiers (issue #694): AUTO_COMMIT_ENABLED gates the
      # {{#if}} block in every write-capable role's template;
      # AUTO_COMMIT_BLOCK is the mode-aware rendered prose. Only Task 2's
      # active-role list is available here as `config["roles"]` -- role
      # eligibility itself is resolved again, per-provider, by Task 6's
      # sync-pipeline stage (this variable only needs mode-level content,
      # not the per-role allowlist).
      from .auto_commit import render_auto_commit_block

      _auto_commit_cfg = config.get("auto_commit", {}) or {}
      _auto_commit_resolved = {
          "mode": _auto_commit_cfg.get("mode", "off"),
          "triggers": _auto_commit_cfg.get("triggers", []),
          "file_count_threshold": _auto_commit_cfg.get("file_count_threshold", 5),
          "custom_script": _auto_commit_cfg.get("custom_script"),
          "secret_scan": _auto_commit_cfg.get("secret_scan", True),
      }
      variables["AUTO_COMMIT_ENABLED"] = (
          "true" if _auto_commit_resolved["mode"] != "off" else "false"
      )
      variables["AUTO_COMMIT_BLOCK"] = render_auto_commit_block(_auto_commit_resolved)
  ```

  In `scripts/lib/consistency/placeholders.py`, add `"AUTO_COMMIT_ENABLED"` next to the other `_CONDITIONAL_FALSE_FLAGS`-style flags and `"AUTO_COMMIT_BLOCK"` next to the other `_BLOCK` entries in `_BUILTIN_VARS` (same list `STATUS_TABLE_BLOCK` was added to).

  In `scripts/lib/standalone.py`:
  - Add `"AUTO_COMMIT_ENABLED": "false"` to `_CONDITIONAL_FALSE_FLAGS` (line ~104) — same dict `README_WARNINGS_ENABLED` is already in; gates the `{{#if}}` block off by default for standalone rendering.
  - Add `"AUTO_COMMIT_BLOCK": ""` to `_ORCHESTRATION_FALLBACKS` (line ~78) — same dict `SE_MODE_BLOCK`/`CHECKPOINTING_BLOCK`/`QUALITY_PIPELINES_BLOCK` already use an empty-string fallback in, because (like those three, and unlike `STATUS_TABLE_BLOCK`) `AUTO_COMMIT_BLOCK` is NEVER referenced unconditionally by any template — only inside `{{#if AUTO_COMMIT_ENABLED}}` — so an empty string is the correct, harmless fallback rather than real rendered content.

- [ ] **Step 4: Run test, verify it passes**

  ```
  python3 -m pytest tests/test_auto_commit_block_render.py -q
  ```

- [ ] **Step 5: Regression-check variable-building and standalone rendering**

  ```
  python3 -m pytest tests/test_build_variables_decomposition.py tests/test_config_variable_fallbacks.py -q
  python3 scripts/sync.py --validate
  ```

- [ ] **Step 6: Commit**

  ```bash
  git add scripts/lib/auto_commit.py scripts/lib/config.py scripts/lib/consistency/placeholders.py scripts/lib/standalone.py tests/test_auto_commit_block_render.py
  git commit -m "feat: render AUTO_COMMIT_BLOCK and wire the 3-registration rule (#694)"
  ```

---

### Task 4: Wire `{{AUTO_COMMIT_BLOCK}}` into one canonical template (proof of concept)

**Files:**
- Modify: `agents/1-generic/developer.md` (version bump, append block)
- Test: `tests/test_auto_commit_developer_reference.py` (new)

**Interfaces:**
- Consumes: `{{AUTO_COMMIT_ENABLED}}` / `{{AUTO_COMMIT_BLOCK}}` from Task 3.
- Produces: the exact append pattern Task 5's bulk-rollout script replicates across the remaining 56 templates.

- [ ] **Step 1: Write the failing test**

  Create `tests/test_auto_commit_developer_reference.py`:

  ```python
  """developer.md must reference the auto_commit block, appended at end of
  file (matches the issue #506 output-guard append precedent) -- proof of
  concept before the bulk rollout in Task 5."""

  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parents[1]
  _DEVELOPER = _REPO_ROOT / "agents" / "1-generic" / "developer.md"


  def test_developer_references_auto_commit_block():
      content = _DEVELOPER.read_text(encoding="utf-8")
      assert "{{#if AUTO_COMMIT_ENABLED}}" in content
      assert "{{AUTO_COMMIT_BLOCK}}" in content
      assert "{{/if}}" in content
      # Appended at/near the end of the file, after the existing
      # <output-guard> block (issue #506 precedent) -- not spliced into the
      # middle of <workflow>/<persona>.
      assert content.rindex("{{#if AUTO_COMMIT_ENABLED}}") > content.rindex("<output-guard>")
  ```

- [ ] **Step 2: Run test, verify it fails**

  ```
  python3 -m pytest tests/test_auto_commit_developer_reference.py -q
  ```
  Expected failure: `{{#if AUTO_COMMIT_ENABLED}}` not found in content.

- [ ] **Step 3: Write minimal implementation**

  Bump `agents/1-generic/developer.md`'s frontmatter `version:` from its current value to the next minor (e.g. `"4.4.0"` → `"4.5.0"` — read the file first to confirm its exact current version before editing, per this repo's convention of never guessing a version number).

  Append at the very end of the file (after the existing `</output-guard>` closing tag, matching where issue #506's own block was appended):

  ```markdown

  {{#if AUTO_COMMIT_ENABLED}}
  {{AUTO_COMMIT_BLOCK}}
  {{/if}}
  ```

- [ ] **Step 4: Run test, verify it passes**

  ```
  python3 -m pytest tests/test_auto_commit_developer_reference.py -q
  ```

- [ ] **Step 5: Re-sync and manually verify rendering in both directions**

  ```
  python scripts/sync.py
  grep -c "AUTO_COMMIT" .claude/agents/developer.md   # expect 0 -- mode defaults to off, block renders empty and the {{#if}} strips
  ```

  Then temporarily set `auto_commit: {mode: auto, triggers: [task-boundary]}` in a throwaway copy of `.meta-config/project.yaml` (do NOT commit this test edit) and re-run `python scripts/sync.py` to confirm `.claude/agents/developer.md` now shows the rendered prose with no leftover `{{...}}`. Revert the throwaway config change and re-sync once more before continuing.

- [ ] **Step 6: Commit**

  ```bash
  git add agents/1-generic/developer.md tests/test_auto_commit_developer_reference.py
  git commit -m "feat: wire AUTO_COMMIT_BLOCK into developer.md as reference impl (#694)"
  ```

---

### Task 5: Bulk rollout to all remaining write-capable templates

**Files:**
- Create: `scripts/_migrations/2026-09-08-inject-auto-commit-block.py` (one-off migration script, not part of the runtime `scripts/lib/` package)
- Modify: 56 files under `agents/1-generic/*.md` (every template with `Edit`/`Write` in `tools:`, except `developer.md` already done in Task 4 and `_reference-agent.md` — see Step 1's rationale)
- Test: `tests/test_auto_commit_coverage.py` (new)

**Interfaces:**
- Consumes: the exact append pattern from Task 4.
- Produces: 100% coverage of write-capable `1-generic` templates, verified by the new coverage test — later tasks (hook, scenario) depend on this being complete, not partial.

- [ ] **Step 1: Write the failing test**

  Create `tests/test_auto_commit_coverage.py`:

  ```python
  """Every 1-generic template with Edit/Write in tools: must reference
  {{AUTO_COMMIT_BLOCK}} (issue #694) -- except _reference-agent.md, which is
  explicitly a didactic, non-deployable template (its own frontmatter
  description says "not intended for production delegation", it has no
  entry in config/role-defaults.yaml, and no project ever activates it as a
  role). git.md is correctly excluded too: it has no Edit/Write in tools:
  (it already has full commit authority via Bash + its own sentinel)."""

  import sys
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

  from lib.auto_commit import is_role_eligible  # noqa: E402

  _REPO_ROOT = Path(__file__).resolve().parents[1]
  _GENERIC_DIR = _REPO_ROOT / "agents" / "1-generic"
  _EXCLUDED = {"_reference-agent"}


  def _eligible_template_files():
      for path in sorted(_GENERIC_DIR.glob("*.md")):
          role = path.stem
          if role in _EXCLUDED:
              continue
          if is_role_eligible(role, _REPO_ROOT):
              yield path


  def test_every_eligible_template_references_the_block():
      missing = [
          str(p.relative_to(_REPO_ROOT))
          for p in _eligible_template_files()
          if "{{AUTO_COMMIT_BLOCK}}" not in p.read_text(encoding="utf-8")
      ]
      assert missing == [], f"templates missing the auto_commit block: {missing}"


  def test_git_template_is_not_touched():
      content = (_GENERIC_DIR / "git.md").read_text(encoding="utf-8")
      assert "AUTO_COMMIT_BLOCK" not in content


  def test_reference_agent_is_excluded_but_documented_why():
      # Confirms the exclusion is deliberate (see docstring), not an
      # oversight -- if this ever starts failing because _reference-agent.md
      # gained a role-defaults.yaml entry, re-evaluate the exclusion.
      assert "not intended for production" in (
          _GENERIC_DIR / "_reference-agent.md"
      ).read_text(encoding="utf-8").lower() or "not intended for production" in (
          _GENERIC_DIR / "_reference-agent.md"
      ).read_text(encoding="utf-8")
  ```

- [ ] **Step 2: Run test, verify it fails**

  ```
  python3 -m pytest tests/test_auto_commit_coverage.py -q
  ```
  Expected failure: `test_every_eligible_template_references_the_block` lists ~56 missing files (every eligible template except `developer.md`).

- [ ] **Step 3: Write minimal implementation**

  Create `scripts/_migrations/2026-09-08-inject-auto-commit-block.py`:

  ```python
  #!/usr/bin/env python3
  """One-off migration (issue #694): append the {{AUTO_COMMIT_BLOCK}}
  reference + a minor version bump to every 1-generic template with
  Edit/Write in tools:, except developer.md (already done, Task 4) and
  _reference-agent.md (non-deployable, see tests/test_auto_commit_coverage.py).

  Run once from the repo root: python3 scripts/_migrations/2026-09-08-inject-auto-commit-block.py
  Safe to re-run: skips any file that already contains the block.
  """

  from __future__ import annotations

  import re
  import sys
  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parents[2]
  sys.path.insert(0, str(_REPO_ROOT / "scripts"))

  from lib.auto_commit import is_role_eligible  # noqa: E402

  _GENERIC_DIR = _REPO_ROOT / "agents" / "1-generic"
  _EXCLUDED = {"_reference-agent", "developer"}

  _APPEND_BLOCK = (
      "\n\n{{#if AUTO_COMMIT_ENABLED}}\n"
      "{{AUTO_COMMIT_BLOCK}}\n"
      "{{/if}}\n"
  )

  # Matches both quoted ("4.4.0") and unquoted (2.0.1) version: values.
  _VERSION_RE = re.compile(r'^(version:\s*"?)(\d+)\.(\d+)\.(\d+)("?)\s*$', re.MULTILINE)


  def _bump_minor(content: str) -> str:
      def _replace(match: re.Match) -> str:
          prefix, major, minor, _patch, suffix = match.groups()
          return f"{prefix}{major}.{int(minor) + 1}.0{suffix}"

      new_content, count = _VERSION_RE.subn(_replace, content, count=1)
      if count != 1:
          raise ValueError("could not find a version: line to bump")
      return new_content


  def main() -> int:
      touched = []
      skipped_already_done = []
      for path in sorted(_GENERIC_DIR.glob("*.md")):
          role = path.stem
          if role in _EXCLUDED:
              continue
          if not is_role_eligible(role, _REPO_ROOT):
              continue
          content = path.read_text(encoding="utf-8")
          if "{{AUTO_COMMIT_BLOCK}}" in content:
              skipped_already_done.append(role)
              continue
          content = _bump_minor(content)
          content = content.rstrip("\n") + _APPEND_BLOCK
          path.write_text(content, encoding="utf-8")
          touched.append(role)

      print(f"Touched {len(touched)} templates: {', '.join(touched)}")
      if skipped_already_done:
          print(f"Already done, skipped: {', '.join(skipped_already_done)}")
      return 0


  if __name__ == "__main__":
      raise SystemExit(main())
  ```

  Run it:

  ```
  python3 scripts/_migrations/2026-09-08-inject-auto-commit-block.py
  ```

- [ ] **Step 4: Run test, verify it passes**

  ```
  python3 -m pytest tests/test_auto_commit_coverage.py -q
  ```

- [ ] **Step 5: Regression-check the whole template set**

  ```
  python3 scripts/consistency-check.py --changed
  python scripts/sync.py
  python3 scripts/sync.py --validate
  python3 -m pytest tests/ -o consider_namespace_packages=true -q
  ```

  If `consistency-check.py` flags any template for a malformed version bump (e.g. a file whose `version:` line didn't match the expected pattern), fix that one file's version manually and re-run — do not weaken the migration script's regex to silently accept a malformed match.

- [ ] **Step 6: Commit**

  ```bash
  git add agents/1-generic/*.md scripts/_migrations/2026-09-08-inject-auto-commit-block.py tests/test_auto_commit_coverage.py
  git commit -m "feat: append AUTO_COMMIT_BLOCK reference to all write-capable templates (#694)"
  ```

---

### Task 6: Sync-pipeline wiring — generate `.meta-config/auto-commit-allowlist.json`

**Files:**
- Modify: `scripts/lib/sync_pipeline.py` (new stage)
- Modify: `scripts/lib/cli_commands.py` (`_handle_sync`, wire the new stage in)
- Test: `tests/test_auto_commit_allowlist_pipeline.py` (new)

**Interfaces:**
- Consumes: `resolve_auto_commit_config()` from Task 2.
- Produces: `.meta-config/auto-commit-allowlist.json` on disk after every `sync.py` run, consumed by Task 7's hook change.

- [ ] **Step 1: Write the failing test**

  Create `tests/test_auto_commit_allowlist_pipeline.py`:

  ```python
  """Sync pipeline writes .meta-config/auto-commit-allowlist.json (issue
  #694). Real-subprocess e2e test, matching the pattern used for
  generated-file-hashes.json / progress-file tests."""

  import json
  import subprocess
  import sys
  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parent.parent


  def _run_sync(project_dir: Path) -> subprocess.CompletedProcess:
      return subprocess.run(
          [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py")],
          cwd=project_dir,
          capture_output=True,
          text=True,
      )


  def test_allowlist_written_when_auto_commit_enabled(tmp_path):
      (tmp_path / ".meta-config").mkdir()
      (tmp_path / ".meta-config" / "project.yaml").write_text(
          "project:\n  name: t\n  prefix: t\n"
          "ai-providers: [Claude]\n"
          "roles: [orchestrator, developer, git]\n"
          "auto_commit:\n  mode: auto\n  triggers: [task-boundary]\n",
          encoding="utf-8",
      )
      result = _run_sync(tmp_path)
      assert result.returncode == 0, result.stderr

      allowlist_path = tmp_path / ".meta-config" / "auto-commit-allowlist.json"
      assert allowlist_path.exists()
      data = json.loads(allowlist_path.read_text(encoding="utf-8"))
      assert data["mode"] == "auto"
      assert "developer" in data["eligible_roles"]
      assert "git" not in data["eligible_roles"]


  def test_allowlist_reflects_mode_off_when_unconfigured(tmp_path):
      (tmp_path / ".meta-config").mkdir()
      (tmp_path / ".meta-config" / "project.yaml").write_text(
          "project:\n  name: t\n  prefix: t\n"
          "ai-providers: [Claude]\n"
          "roles: [orchestrator, developer, git]\n",
          encoding="utf-8",
      )
      result = _run_sync(tmp_path)
      assert result.returncode == 0, result.stderr

      allowlist_path = tmp_path / ".meta-config" / "auto-commit-allowlist.json"
      assert allowlist_path.exists()
      data = json.loads(allowlist_path.read_text(encoding="utf-8"))
      assert data["mode"] == "off"
      assert data["eligible_roles"] == []
  ```

- [ ] **Step 2: Run test, verify it fails**

  ```
  python3 -m pytest tests/test_auto_commit_allowlist_pipeline.py -q
  ```
  Expected failure: `assert allowlist_path.exists()` is False.

- [ ] **Step 3: Write minimal implementation**

  In `scripts/lib/sync_pipeline.py`, add a new stage function near
  `_sync_stage_generated_file_hash_capture` (line ~722), matching its exact
  parameter convention (`agent_meta_root, project_root, config, ..., args, log`):

  ```python
  def _sync_stage_auto_commit_allowlist(agent_meta_root, project_root, config, args, log) -> None:
      """Issue #694: write .meta-config/auto-commit-allowlist.json reflecting
      the resolved auto_commit config for this sync. Runs on every sync,
      overwriting the previous allowlist in full (not merged) -- stale
      entries from a role that's no longer active must not linger. Must run
      after _sync_stage_generated_file_hash_capture (which the conventions
      skill's Change Checklist and this repo's own stage-13 comment both
      call the true last stage) so this file's own write doesn't get
      captured into that hash baseline a step too early."""
      import json

      from .auto_commit import resolve_auto_commit_config
      from .io import write_atomic

      active_roles = config.get("roles", [])
      resolved = resolve_auto_commit_config(config, active_roles, agent_meta_root)

      allowlist_path = project_root / ".meta-config" / "auto-commit-allowlist.json"
      if getattr(args, "dry_run", False):
          return
      allowlist_path.parent.mkdir(parents=True, exist_ok=True)
      write_atomic(allowlist_path, json.dumps(resolved, indent=2, sort_keys=True) + "\n")
  ```

  In `scripts/lib/cli_commands.py::_handle_sync`, add the import
  (alphabetically, alongside the other `_sync_stage_*` imports at line ~79)
  and add the call immediately AFTER the existing
  `_sync_stage_generated_file_hash_capture(...)` call (currently lines
  1038-1039), before `ctx.config = config` (line 1041):

  ```python
      _sync_stage_auto_commit_allowlist(ctx.agent_meta_root, ctx.project_root,
                                        config, ctx.args, ctx.log)
  ```

- [ ] **Step 4: Run test, verify it passes**

  ```
  python3 -m pytest tests/test_auto_commit_allowlist_pipeline.py -q
  ```

- [ ] **Step 5: Regression-check the drift-detection interaction**

  The new allowlist file must itself be covered by generated-file drift
  detection consistently (it's a generated artifact like
  `generated-file-hashes.json`, not something a user hand-edits) — or
  explicitly excluded if that's simpler. Check
  `scripts/lib/generated_file_drift.py`'s `_iter_managed_files()` scope; if
  `.meta-config/*.json` sidecars are already excluded from drift-scanning
  (as `generated-file-hashes.json` itself must be, to avoid a chicken-and-egg
  self-referential warning), no change is needed here — just confirm via:

  ```
  python3 -m pytest tests/test_generated_file_drift.py -q
  ```

- [ ] **Step 6: Commit**

  ```bash
  git add scripts/lib/sync_pipeline.py scripts/lib/cli_commands.py tests/test_auto_commit_allowlist_pipeline.py
  git commit -m "feat: write auto-commit-allowlist.json in the sync pipeline (#694)"
  ```

---

### Task 7: Hook enforcement — extend sentinel recognition in `orchestrator-guard-impl.sh`

**Files:**
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh` (version bump `1.1.0` → `1.2.0`)
- Modify: `tests/test_orchestrator_guard_hook.py` (new test cases)

**Interfaces:**
- Consumes: `.meta-config/auto-commit-allowlist.json` from Task 6 (read at hook-execution time, not sync time).
- Produces: git-mutation-gate authorization for any role in `eligible_roles`, in addition to the existing hardcoded `git`/`orchestrator`.

- [ ] **Step 1: Write the failing test**

  Append to `tests/test_orchestrator_guard_hook.py`, reusing the file's own
  `_run_hook(payload: dict)` and `_bash_payload(command: str) -> dict`
  helpers exactly as every existing test in this file does (no new
  fixtures — `cwd=tmp_path.as_posix()` with no `.meta-config/project.yaml`
  written is already the established pattern for git-mutation-gate tests,
  since a missing config file makes `STRICT` resolve to `false` and this
  gate applies independently of strict mode):

  ```python
  # `json` is already imported at module scope in this file (line 46) -- reuse it.


  def _write_allowlist(tmp_path, mode, eligible_roles):
      (tmp_path / ".meta-config").mkdir(parents=True, exist_ok=True)
      (tmp_path / ".meta-config" / "auto-commit-allowlist.json").write_text(
          json.dumps({
              "version": 1, "mode": mode, "eligible_roles": eligible_roles,
              "triggers": ["task-boundary"], "file_count_threshold": 5,
              "custom_script": None, "secret_scan": True,
          }),
          encoding="utf-8",
      )


  def test_allowlisted_role_can_commit_when_auto_commit_enabled(tmp_path):
      _write_allowlist(tmp_path, "auto", ["developer"])
      command = "#agent-meta:agent=developer\ngit add -A && git commit -m 'x'"
      result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
      assert result.returncode == 0, f"stderr={result.stderr}"


  def test_non_allowlisted_role_still_blocked(tmp_path):
      _write_allowlist(tmp_path, "auto", ["developer"])
      command = "#agent-meta:agent=tester\ngit add -A && git commit -m 'x'"
      result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
      assert result.returncode == 2, f"stderr={result.stderr}"
      assert "git" in result.stderr.lower()


  def test_missing_allowlist_file_behaves_like_mode_off(tmp_path):
      # No auto-commit-allowlist.json written at all.
      command = "#agent-meta:agent=developer\ngit add -A && git commit -m 'x'"
      result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
      assert result.returncode == 2, f"stderr={result.stderr}"  # unchanged from today


  def test_allowlist_mode_off_ignores_eligible_roles_list(tmp_path):
      # A stale allowlist from a previous sync where auto_commit was later
      # disabled again must not still authorize anyone.
      _write_allowlist(tmp_path, "off", ["developer"])
      command = "#agent-meta:agent=developer\ngit add -A && git commit -m 'x'"
      result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
      assert result.returncode == 2, f"stderr={result.stderr}"


  def test_destructive_gate_still_blocks_an_allowlisted_role(tmp_path):
      # #516's destructive-gate protections are untouched by this feature --
      # same assertion shape as test_destructive_ops_blocked_even_with_git_sentinel
      # above, substituting an allowlisted "developer" sentinel for "git".
      _write_allowlist(tmp_path, "auto", ["developer"])
      command = "#agent-meta:agent=developer\ngit push --force origin main"
      result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
      assert result.returncode == 2, f"stderr={result.stderr}"
      assert "user approval" in result.stderr


  def test_allowlisted_role_does_not_gain_orchestrator_sentinel_scope(tmp_path):
      # An allowlisted non-git/orchestrator role must only ever gain the
      # git-mutation-gate exemption (IS_GIT_SENTINEL), never the strict-mode
      # main-chat exemption (IS_ORCH_SENTINEL) -- verified with an isolated
      # fixture project (orchestrator.strict: true) as cwd: with NO agent_id
      # (a main-thread call), a plain non-mutating Bash command from an
      # allowlisted role must still be blocked by the strict-mode gate,
      # exactly like an undeclared caller.
      (tmp_path / ".meta-config").mkdir(parents=True, exist_ok=True)
      (tmp_path / ".meta-config" / "project.yaml").write_text(
          "orchestrator:\n  strict: true\n  enabled: true\n", encoding="utf-8",
      )
      _write_allowlist(tmp_path, "auto", ["developer"])
      command = "#agent-meta:agent=developer\necho test"
      result = _run_hook({**_bash_payload(command), "cwd": tmp_path.as_posix()})
      assert result.returncode == 2, f"stderr={result.stderr}"
  ```

- [ ] **Step 2: Run test, verify it fails**

  ```
  python3 -m pytest tests/test_orchestrator_guard_hook.py -k auto_commit -v
  ```
  Expected failure: `test_allowlisted_role_can_commit_when_auto_commit_enabled` fails with exit code 2 (blocked) — the hook doesn't know about the allowlist yet.

- [ ] **Step 3: Write minimal implementation**

  In `hooks/1-generic/orchestrator-guard-impl.sh`, extend the sentinel
  block (currently, per the file's own comments, at the `case "$_ROLE" in
  git|orchestrator)` line). Change:

  ```bash
  if [ "$TOOL_NAME" = "Bash" ] && [ -n "$DECLARED_AGENT" ]; then
    _ROLE=$(printf '%s' "$DECLARED_AGENT" | tr '[:upper:]' '[:lower:]')
    case "$_ROLE" in
      git|orchestrator)
        _AUDIT_LOG="$PROJECT_ROOT/.claude/hooks/.guard-audit.log"
        _AUDIT_LINE=$(printf '%s role=%s cmd=%s' \
          "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$_ROLE" \
          "$(printf '%s' "$BASH_CMD" | tr '\n\t' '  ' | head -c 200)")
        hook_audit_log_append "$_AUDIT_LOG" "$_AUDIT_LINE"
        if [ "$_ROLE" = "git" ]; then
          IS_GIT_SENTINEL=1
        else
          IS_ORCH_SENTINEL=1
        fi
        ;;
    esac
  fi
  ```

  to:

  ```bash
  if [ "$TOOL_NAME" = "Bash" ] && [ -n "$DECLARED_AGENT" ]; then
    _ROLE=$(printf '%s' "$DECLARED_AGENT" | tr '[:upper:]' '[:lower:]')
    _AUDIT_ROLE=""
    case "$_ROLE" in
      git) IS_GIT_SENTINEL=1; _AUDIT_ROLE="$_ROLE" ;;
      orchestrator) IS_ORCH_SENTINEL=1; _AUDIT_ROLE="$_ROLE" ;;
      *)
        # Issue #694: config-driven third sentinel category. Grants the
        # SAME scope as the git sentinel (git-mutation-gate exemption
        # ONLY -- never the destructive gate, never the strict-mode
        # main-chat exemption) to any role sync.py has already determined
        # is Edit/Write-capable AND that this project's auto_commit
        # config has enabled. The hook never re-derives role capability
        # itself -- it only trusts the pre-computed allowlist.
        _ALLOWLIST="$PROJECT_ROOT/.meta-config/auto-commit-allowlist.json"
        if [ -f "$_ALLOWLIST" ]; then
          _AC_MODE=$("$_PY" -c "
  import json, sys
  try:
      with open(sys.argv[1]) as f:
          data = json.load(f)
      print(data.get('mode', 'off'))
  except Exception:
      print('off')
  " "$_ALLOWLIST" 2>/dev/null)
          if [ "$_AC_MODE" != "off" ]; then
            _IS_ELIGIBLE=$("$_PY" -c "
  import json, sys
  try:
      with open(sys.argv[1]) as f:
          data = json.load(f)
      print('1' if sys.argv[2] in data.get('eligible_roles', []) else '0')
  except Exception:
      print('0')
  " "$_ALLOWLIST" "$_ROLE" 2>/dev/null)
            if [ "$_IS_ELIGIBLE" = "1" ]; then
              IS_GIT_SENTINEL=1
              _AUDIT_ROLE="$_ROLE"
            fi
          fi
        fi
        ;;
    esac
    if [ -n "$_AUDIT_ROLE" ]; then
      _AUDIT_LOG="$PROJECT_ROOT/.claude/hooks/.guard-audit.log"
      _AUDIT_LINE=$(printf '%s role=%s cmd=%s' \
        "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$_AUDIT_ROLE" \
        "$(printf '%s' "$BASH_CMD" | tr '\n\t' '  ' | head -c 200)")
      hook_audit_log_append "$_AUDIT_LOG" "$_AUDIT_LINE"
    fi
  fi
  ```

  Note the deliberate scoping: an allowlisted non-git role sets
  `IS_GIT_SENTINEL=1` (git-mutation-gate exemption only) — it never touches
  `IS_ORCH_SENTINEL`, so it can never gain the strict-mode main-chat
  exemption that only `git`/`orchestrator` have. The destructive-operation
  gate (earlier in the file) runs unconditionally regardless of either flag
  and is completely unaffected by this change.

  Bump the version comment at the top of the file:
  `# version: 1.1.0` → `# version: 1.2.0`.

- [ ] **Step 4: Run test, verify it passes**

  ```
  python3 -m pytest tests/test_orchestrator_guard_hook.py -q
  ```

- [ ] **Step 5: Re-sync so provider copies of the hook pick up the change**

  ```
  python scripts/sync.py
  python3 scripts/sync.py --validate
  ```

- [ ] **Step 6: Commit**

  ```bash
  git add hooks/1-generic/orchestrator-guard-impl.sh tests/test_orchestrator_guard_hook.py
  git commit -m "feat: hook enforcement for allowlisted auto_commit roles (#694)"
  ```

---

### Task 8: Secret-scan CLI wrapper for auto-commits

**Files:**
- Modify: `scripts/sync.py` (new `--scan-staged` flag)
- Modify: `scripts/lib/cli_commands.py` (handler)
- Test: `tests/test_scan_staged.py` (new)

**Interfaces:**
- Consumes: `scan_for_secrets(content: str, config: dict | None = None) -> list[str]` (`scripts/lib/secrets.py`, already existing).
- Produces: `sync.py --scan-staged` — exits 1 and prints findings if any staged file's diff content matches a secret pattern, exits 0 otherwise. This is what the `AUTO_COMMIT_BLOCK` prose (Task 3) instructs agents to run before an auto/custom commit.

- [ ] **Step 1: Write the failing test**

  Create `tests/test_scan_staged.py`:

  ```python
  """sync.py --scan-staged (issue #694): exposes the existing
  scan_for_secrets() to agents as a pre-commit check, without requiring a
  Python import inside a Bash instruction block."""

  import subprocess
  import sys
  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parent.parent


  def _init_repo(tmp_path):
      subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
      subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp_path, check=True)
      subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)


  def test_scan_staged_passes_on_clean_diff(tmp_path):
      _init_repo(tmp_path)
      (tmp_path / "file.py").write_text("print('hello')\n", encoding="utf-8")
      subprocess.run(["git", "add", "file.py"], cwd=tmp_path, check=True)

      result = subprocess.run(
          [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"), "--scan-staged"],
          cwd=tmp_path, capture_output=True, text=True,
      )
      assert result.returncode == 0


  def test_scan_staged_fails_on_secret_looking_content(tmp_path):
      _init_repo(tmp_path)
      (tmp_path / "config.py").write_text(
          'AWS_SECRET_ACCESS_KEY = "AKIAABCDEFGHIJKLMNOP"\n', encoding="utf-8",
      )
      subprocess.run(["git", "add", "config.py"], cwd=tmp_path, check=True)

      result = subprocess.run(
          [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"), "--scan-staged"],
          cwd=tmp_path, capture_output=True, text=True,
      )
      assert result.returncode == 1
      assert "config.py" in result.stdout or "config.py" in result.stderr
  ```

- [ ] **Step 2: Run test, verify it fails**

  ```
  python3 -m pytest tests/test_scan_staged.py -q
  ```
  Expected failure: `error: unrecognized arguments: --scan-staged`.

- [ ] **Step 3: Write minimal implementation**

  In `scripts/sync.py`'s argument parser, add:

  ```python
  parser.add_argument(
      "--scan-staged", action="store_true",
      help="Scan git-staged file contents for secrets (issue #694 pre-commit gate) and exit.",
  )
  ```

  In `scripts/lib/cli_commands.py`, add a handler function:

  ```python
  def handle_scan_staged() -> int:
      """issue #694: scan currently-staged file contents for secrets.
      Returns 0 if clean, 1 if any finding -- printed to stdout with the
      offending file path."""
      import subprocess

      from .secrets import scan_for_secrets

      result = subprocess.run(
          ["git", "diff", "--cached", "--name-only"],
          capture_output=True, text=True, check=True,
      )
      staged_files = [f for f in result.stdout.splitlines() if f.strip()]

      any_findings = False
      for rel_path in staged_files:
          path = Path(rel_path)
          if not path.is_file():
              continue  # deleted/renamed-away files have nothing to scan
          try:
              content = path.read_text(encoding="utf-8")
          except (UnicodeDecodeError, OSError):
              continue  # binary or unreadable -- not a text-secret risk this scanner covers
          findings = scan_for_secrets(content)
          if findings:
              any_findings = True
              print(f"{rel_path}: {', '.join(findings)}")

      if any_findings:
          print("Secret scan FAILED -- see findings above. Do not commit.")
          return 1
      print("Secret scan passed -- no findings in staged files.")
      return 0
  ```

  Wire it into `scripts/sync.py`'s main dispatch (near the other early-exit
  flags like `--validate`): if `args.scan_staged`, call
  `cli_commands.handle_scan_staged()` and `sys.exit()` with its return
  value, before any other sync logic runs.

- [ ] **Step 4: Run test, verify it passes**

  ```
  python3 -m pytest tests/test_scan_staged.py -q
  ```

- [ ] **Step 5: Regression-check the CLI arg surface**

  There is no single generic CLI-argument regression file in this repo
  (`tests/test_sync_test_plugin_cli.py` is the closest analog, specific to
  `--test-plugin`); `tests/test_scan_staged.py` from Step 1 is this flag's
  own coverage. Confirm the flag is registered and the full suite still
  collects cleanly:

  ```
  python3 scripts/sync.py --help | grep -A1 scan-staged
  python3 -m pytest tests/test_scan_staged.py -q
  ```

- [ ] **Step 6: Commit**

  ```bash
  git add scripts/sync.py scripts/lib/cli_commands.py tests/test_scan_staged.py
  git commit -m "feat: add sync.py --scan-staged for the auto_commit secret gate (#694)"
  ```

---

### Task 9: `tests/scenarios/` entry for auto_commit

**Files:**
- Create: `tests/scenarios/configs/18-auto-commit.project.yaml`
- Modify: `tests/scenarios/registry.md` (add the catalog row)

**Interfaces:**
- Consumes: everything from Tasks 1-7.
- Produces: a regression-tested consumer-project shape exercising `auto_commit`, per this repo's own scenario-catalog convention (`rules/2-platform/agent-meta-conventions.md` → Change Checklist).

- [ ] **Step 1: Create the scenario config**

  Create `tests/scenarios/configs/18-auto-commit.project.yaml`:

  ```yaml
  agent-meta-version: 0.101.0
  ai-providers:
  - Claude
  - Gemini
  dod-preset: standard
  platforms: []
  roles:
  - orchestrator
  - developer
  - tester
  - git
  auto_commit:
    mode: auto
    triggers: [task-boundary, context-pressure]
    secret_scan: true
  project:
    name: scenario-auto-commit
    prefix: s18
    short: scenario-autocommit
  variables:
    PROJECT_NAME: scenario-auto-commit
    PROJECT_DESCRIPTION: Auto-commit tiers test (issue #694).
    PROJECT_GOAL: Verify auto_commit config resolves eligible roles, renders AUTO_COMMIT_BLOCK, and writes the allowlist correctly.
    GIT_PLATFORM: GitHub
    GIT_REMOTE_URL: https://github.com/example/scenario-autocommit
    GIT_MAIN_BRANCH: main
  rules-preset: default
  speech-mode: full
  tier-preset: Normal
  se-focus: false
  max-parallel-agents: 2
  conventions-preset: default
  debug-mode: false
  allow-committed-secrets: false
  ```

- [ ] **Step 2: Add the registry row**

  In `tests/scenarios/registry.md`'s catalog table, add:

  ```markdown
  | `18-auto-commit` | Claude, Gemini | strict (default) | Auto-commit tiers: role eligibility, AUTO_COMMIT_BLOCK rendering, allowlist generation (#694) |
  ```

- [ ] **Step 3: Run the scenario and verify manually**

  ```
  tests/scenarios/run.sh 18
  ```

  Then manually verify (temp dir path printed by `run.sh` on failure, or
  re-run the scenario's sync manually in a scratch dir) that:
  - `.meta-config/auto-commit-allowlist.json` lists `developer` and `tester`, not `orchestrator`/`git`.
  - `.claude/agents/developer.md` and `.gemini/agents/developer.md` both show the rendered `AUTO_COMMIT_BLOCK` prose with no leftover `{{...}}`.

- [ ] **Step 4: Commit**

  ```bash
  git add tests/scenarios/configs/18-auto-commit.project.yaml tests/scenarios/registry.md
  git commit -m "test: add auto_commit scenario to the catalog (#694)"
  ```

---

### Task 10: Documentation + full validation pass

**Files:**
- Modify: `CHANGELOG.md` (append to `## [Unreleased]` → `### Added`)
- Modify: `README.md` (new subsection under Configuration, matching the existing `.gitignore Management` / `README Structure Standard` subsections' style)
- No new tests (validates the sum of Tasks 1-9).

- [ ] **Step 1: Run the full test suite**

  ```
  python3 -m pytest tests/ -o consider_namespace_packages=true -q
  ```
  Verify: 0 new failures (the pre-existing network-dependent model-discovery test and socket-blocked browser tests are known, unrelated — confirm the count matches the baseline from before this plan started, do not chase those).

- [ ] **Step 2: Run the sync validator and re-sync this repo's own generated files**

  ```
  python3 scripts/sync.py --validate
  python scripts/sync.py
  git status --short
  ```
  Verify: `--validate` reports no new errors/warnings; `git status --short` shows only the expected regenerated files plus this task's own doc edits.

- [ ] **Step 3: Write the CHANGELOG entry**

  In `CHANGELOG.md`, under `## [Unreleased]` → `### Added`, prepend:

  ```markdown
  - **Auto-commit tiers (#694)**: opt-in `auto_commit` config (`off`/`suggest`/
    `auto`/`custom`) lets write-capable agents commit directly instead of always
    delegating to the `git` role. `suggest` has agents propose a commit message
    in their own report (never blocking, never running git itself); `auto`
    commits when any of 5 selectable trigger conditions fires
    (`task-boundary`, `per-edit`, `context-pressure`, `file-count-threshold`,
    `custom`); `custom` hands the entire decision to a project script. Role
    eligibility is capability-derived (Edit/Write in a role's own template
    `tools:`, never a hand-maintained list). Enforced two ways: prompt
    instructions on all 9 providers, plus hook authorization
    (`orchestrator-guard-impl.sh` v1.2.0) on the 4 providers with PreToolUse
    hook support (Claude, Gemini, Mammouth, Codex) via a generated
    `.meta-config/auto-commit-allowlist.json`. `push`/`tag`/branch management
    remain exclusively the `git` role's job; the destructive-operation gate
    (issue #516) is completely unaffected. Optional secret scan
    (`sync.py --scan-staged`, `secret_scan: true` default) gates every
    auto/custom commit.
  ```

- [ ] **Step 4: Update README.md**

  Add a new subsection under the existing `## Configuration` section (after
  the `### Orchestrator Modes` subsection, matching that subsection's
  format): title `### Auto-Commit Tiers (issue #694)`, covering the 4 modes,
  the 5 trigger types, the capability-derived eligibility rule, and the
  explicit push/tag/branch exclusion — mirror the tone and length of the
  existing `.gitignore Management` subsection `documenter` added in the
  prior release (read it first for the exact style to match).

- [ ] **Step 5: Commit**

  ```bash
  git add CHANGELOG.md README.md
  git commit -m "docs: changelog and README entry for auto-commit tiers (#694)"
  ```

---

## Self-Review Notes

- **Spec coverage:** design-spec Layer 1 (prompt instructions, all 9 providers) → Tasks 3-5. Layer 2 (hook enforcement, 4 providers) → Tasks 6-7. Trigger types (5, selectable) → Task 3's renderer + Task 1's schema. Secret-scan gate → Task 8, wired into Task 3's rendered prose. Scenario-catalog convention → Task 9. Documentation → Task 10. Every section of the spec has a task.
- **Explicitly not built** (per spec's own "Out of scope" list): Admin-UI control surface; real hook enforcement on the 5 non-hook providers (platform limitation, not a gap); trigger-usage telemetry.
- **A capability-rule consequence worth flagging to the plan's approver, not hidden:** `orchestrator.md` itself has `Edit`/`Write` in its `tools:` list (per the capability scan run during planning) and is therefore commit-eligible under this design, even though its role is to decompose and delegate, not implement. This was an explicit, approved outcome of the "capability-derived, no role exclusions" decision during brainstorming — flagged here again because it's easy to overlook, not because it's unresolved.
- **Type/placeholder consistency:** `resolve_auto_commit_config()`'s return shape (Task 2) is used identically by Task 3 (calling code destructures the same keys), Task 6 (writes it verbatim to JSON), and Task 7's tests (constructs the same shape by hand) — no drift between the four call sites.
- **No breaking changes:** `auto_commit` defaults to `mode: off` everywhere; a project that never sets this key gets `AUTO_COMMIT_ENABLED = "false"` and an empty rendered block, so the `{{#if}}`-gated append in every one of the 57 templates renders to nothing — byte-for-byte unchanged output for every existing project.
