# External-Tool Injection Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `config/external-tools-registry.yaml` declare, per tool, a provider-agnostic whitelist (`permitted-injections`) of skills/hooks/rules/config paths a locally-installed tool (e.g. graphify) is allowed to self-install — default-deny everything else — and surface both the whitelist and any drift (undeclared foreign artifacts) directly in the loaded agent context and the Admin UI.

**Architecture:** Extends `scripts/lib/external_tools.py` (no new module). Reuses the codebase's existing `.agent-meta-managed` index-file convention (already used by `sync_rules`, `sync_hooks`, `sync_agents_for_provider`) as the "what did agent-meta itself put here" ground truth, adds the same convention to `sync_external_skills_for_provider` (currently missing it), and diffs actual directory listings against (managed-index ∪ permitted-injections) once per sync run. Drift is reported via `log.warning` (sync.log) and, only when non-empty, a generated `.claude/rules/external-tools-drift.md` (loaded context) — mirrors the existing "Bekannte Grenzen" transparency pattern already used in `branch-guard.md` / `a2a-delegation-gates.md`.

**Tech Stack:** Python 3 stdlib only (no new deps), existing `pytest` suite, vanilla-JS Admin UI (`docs/ui/admin-ui.html`), Python `http.server`-based `scripts/admin-server.py`.

**Spec:** `docs/superpowers/specs/2026-08-13-external-tool-injection-governance-design.md`

## Global Constraints

- Default-deny: nothing is permitted unless declared in a tool's `permitted-injections`. No hardcoded exception list — `.claude/agents/`, `CLAUDE.md` etc. are protected purely because nothing legitimately declares permission for them.
- Warn only. Never block, never modify/delete drifted files, never change `sync.py --check` exit code.
- `kind ∈ {skill, hook, rule}` requires `name` (provider-relative, resolved via `pc.get("<kind>s_dir"/"hooks_dir"/"rules_dir", ...)`); `kind ∈ {config, other}` requires an explicit `path` (relative to `project_root`). Mixing (`name` with `config`, `path` with `skill`) is a `SyncError`.
- `external-tools-drift.md` is only ever written when findings exist; capped at 10 entries + `"… N weitere, siehe sync.log"`; deleted if a later sync finds no drift.
- No new Python dependencies. No new top-level module — everything lives in `scripts/lib/external_tools.py` plus the one small addition to `scripts/lib/skills.py`.

---

## File Structure

| File | Change |
|---|---|
| `config/project-config.schema.json` | Add `permitted-injections` under `external-tools-registry.patternProperties.*.properties` |
| `config/external-tools-registry.yaml` | Add `permitted-injections` to the `graphify` entry |
| `scripts/lib/external_tools.py` | `_validate_permitted_injections`, `resolve_injection_path`, extend `_generate_tool_rule_content`, new `scan_injection_drift`, new `render_injection_drift_artifacts` |
| `scripts/lib/skills.py` | Add `.agent-meta-managed` index write/read to `sync_external_skills_for_provider` (mirrors existing pattern in `rules.py`/`hooks.py`/`agents.py`) |
| `scripts/sync.py` | Call `scan_injection_drift` + `render_injection_drift_artifacts` once after the provider loop |
| `scripts/admin-server.py` | New `GET /api/external-tools/drift` route + `_compute_injection_drift` helper |
| `docs/ui/admin-ui.html` | Drift warning banner + `permitted-injections` row-editor in `viewProjectExternalToolsOverrides` |
| `tests/test_external_tools_registry.py` | New tests for all of the above |

---

### Task 1: Schema — `permitted-injections` field + validation + graphify entry

**Files:**
- Modify: `config/project-config.schema.json` (`external-tools-registry.patternProperties.*.properties`)
- Modify: `config/external-tools-registry.yaml`
- Modify: `scripts/lib/external_tools.py` (add `SyncError` import, new `_validate_permitted_injections`)
- Test: `tests/test_external_tools_registry.py`

**Interfaces:**
- Produces: `_validate_permitted_injections(tool_name: str, entries: list[dict]) -> None` — raises `SyncError` on malformed entries. Called from `load_external_tools_registry` right before it returns.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_external_tools_registry.py
import pytest
from scripts.lib.io import SyncError

def test_permitted_injections_skill_requires_name(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {
        "graphify": {
            "description": "d",
            "permitted-injections": [{"kind": "skill", "path": ".claude/skills/graphify"}],
        }
    })
    with pytest.raises(SyncError, match="requires 'name'"):
        load_external_tools_registry(agent_meta_root, {}, project_root)


def test_permitted_injections_config_requires_path(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {
        "graphify": {
            "description": "d",
            "permitted-injections": [{"kind": "config", "name": "graphify"}],
        }
    })
    with pytest.raises(SyncError, match="requires 'path'"):
        load_external_tools_registry(agent_meta_root, {}, project_root)


def test_permitted_injections_valid_entry_passes(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {
        "graphify": {
            "description": "d",
            "permitted-injections": [{"kind": "skill", "name": "graphify"}],
        }
    })
    registry = load_external_tools_registry(agent_meta_root, {}, project_root)
    assert registry["graphify"]["permitted-injections"] == [{"kind": "skill", "name": "graphify"}]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_external_tools_registry.py -k permitted_injections -v`
Expected: FAIL — `load_external_tools_registry` does not validate `permitted-injections` yet (first two tests fail because no `SyncError` is raised; third passes trivially since nothing rejects it, which is fine).

- [ ] **Step 3: Implement `_validate_permitted_injections` and wire it in**

In `scripts/lib/external_tools.py`, change the import line:

```python
from .io import SyncError, _load_yaml_or_json, safe_path, write_checked
```

Add near the top (after `_deep_merge`, before `load_external_tools_registry`):

```python
_INJECTION_KINDS_NAME = {"skill", "hook", "rule"}
_INJECTION_KINDS_PATH = {"config", "other"}


def _validate_permitted_injections(tool_name: str, entries) -> None:
    """Validate a tool's ``permitted-injections`` list.

    kind in {skill, hook, rule} requires 'name' (provider-relative);
    kind in {config, other} requires an explicit 'path'. Mixing either
    field with the wrong kind group is a SyncError.
    """
    if not isinstance(entries, list):
        raise SyncError(
            f"external-tools-registry: '{tool_name}'.permitted-injections must be a list"
        )
    for entry in entries:
        if not isinstance(entry, dict):
            raise SyncError(
                f"external-tools-registry: '{tool_name}'.permitted-injections entries must be objects"
            )
        kind = entry.get("kind")
        if kind not in _INJECTION_KINDS_NAME | _INJECTION_KINDS_PATH:
            raise SyncError(
                f"external-tools-registry: '{tool_name}'.permitted-injections has invalid "
                f"kind '{kind}' (expected one of skill, hook, rule, config, other)"
            )
        if kind in _INJECTION_KINDS_NAME:
            if not entry.get("name"):
                raise SyncError(
                    f"external-tools-registry: '{tool_name}'.permitted-injections entry "
                    f"with kind '{kind}' requires 'name'"
                )
            if entry.get("path"):
                raise SyncError(
                    f"external-tools-registry: '{tool_name}'.permitted-injections entry "
                    f"with kind '{kind}' must not set 'path' (use 'name')"
                )
        else:
            if not entry.get("path"):
                raise SyncError(
                    f"external-tools-registry: '{tool_name}'.permitted-injections entry "
                    f"with kind '{kind}' requires 'path'"
                )
            if entry.get("name"):
                raise SyncError(
                    f"external-tools-registry: '{tool_name}'.permitted-injections entry "
                    f"with kind '{kind}' must not set 'name' (use 'path')"
                )
```

At the end of `load_external_tools_registry`, right before `return registry`:

```python
    for tool_name, tool_def in registry.items():
        if isinstance(tool_def, dict) and "permitted-injections" in tool_def:
            _validate_permitted_injections(tool_name, tool_def["permitted-injections"])

    return registry
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_external_tools_registry.py -k permitted_injections -v`
Expected: PASS (all three)

- [ ] **Step 5: Extend the JSON schema**

In `config/project-config.schema.json`, inside `external-tools-registry.patternProperties.^[a-zA-Z0-9_-]+$.properties`, add a sibling to the existing `hooks` property:

```json
"permitted-injections": {
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "kind": { "type": "string", "enum": ["skill", "hook", "rule", "config", "other"] },
      "name": { "type": "string" },
      "path": { "type": "string" },
      "description": { "type": "string" }
    },
    "required": ["kind"],
    "additionalProperties": false
  }
}
```

Run: `python3 -c "import json; json.load(open('config/project-config.schema.json'))"` — must not raise (valid JSON).

- [ ] **Step 6: Add the graphify entry to the framework registry**

In `config/external-tools-registry.yaml`, inside the `graphify:` block (after `hooks:`), add:

```yaml
    permitted-injections:
      - kind: skill
        name: graphify
        description: "Claude-Code-Skill (SKILL.md + references), vom graphify-Installer selbst verwaltet"
```

- [ ] **Step 7: Commit**

```bash
git add config/project-config.schema.json config/external-tools-registry.yaml scripts/lib/external_tools.py tests/test_external_tools_registry.py
git commit -m "feat: add permitted-injections schema to external-tools-registry"
```

---

### Task 2: Path resolution — `resolve_injection_path`

**Files:**
- Modify: `scripts/lib/external_tools.py`
- Test: `tests/test_external_tools_registry.py`

**Interfaces:**
- Consumes: `pc: dict` (single provider's entry from `provider_config`, e.g. `provider_config["Claude"]`), `entry: dict` (one validated `permitted-injections` item), `project_root: Path`.
- Produces: `resolve_injection_path(entry: dict, pc: dict, project_root: Path) -> Path` — absolute, resolved path. Used by Task 3 (rendering) and Task 5 (drift scan).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_external_tools_registry.py
from scripts.lib.external_tools import resolve_injection_path

def test_resolve_injection_path_skill(tmp_path):
    pc = {"skills_dir": ".claude/skills"}
    entry = {"kind": "skill", "name": "graphify"}
    result = resolve_injection_path(entry, pc, tmp_path)
    assert result == (tmp_path / ".claude" / "skills" / "graphify").resolve()


def test_resolve_injection_path_config_uses_path_verbatim(tmp_path):
    pc = {}
    entry = {"kind": "config", "path": ".claude/settings.json"}
    result = resolve_injection_path(entry, pc, tmp_path)
    assert result == (tmp_path / ".claude" / "settings.json").resolve()


def test_resolve_injection_path_defaults_without_explicit_dir(tmp_path):
    pc = {}  # no hooks_dir set — must fall back to .claude/hooks
    entry = {"kind": "hook", "name": "graphify-guard.sh"}
    result = resolve_injection_path(entry, pc, tmp_path)
    assert result == (tmp_path / ".claude" / "hooks" / "graphify-guard.sh").resolve()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_external_tools_registry.py -k resolve_injection_path -v`
Expected: FAIL with `ImportError: cannot import name 'resolve_injection_path'`

- [ ] **Step 3: Implement `resolve_injection_path`**

In `scripts/lib/external_tools.py`, add (after `_validate_permitted_injections`):

```python
_INJECTION_DIR_KEYS = {
    "skill": ("skills_dir", ".claude/skills"),
    "hook": ("hooks_dir", ".claude/hooks"),
    "rule": ("rules_dir", ".claude/rules"),
}


def resolve_injection_path(entry: dict, pc: dict, project_root: Path) -> Path:
    """Resolve one permitted-injections entry to an absolute path.

    kind in {skill, hook, rule}: <pc[<kind>s_dir]>/<name>
    kind in {config, other}: <project_root>/<path>, verbatim.
    """
    kind = entry["kind"]
    if kind in _INJECTION_DIR_KEYS:
        dir_key, default_dir = _INJECTION_DIR_KEYS[kind]
        base = project_root / pc.get(dir_key, default_dir)
        return (base / entry["name"]).resolve()
    return (project_root / entry["path"]).resolve()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_external_tools_registry.py -k resolve_injection_path -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/external_tools.py tests/test_external_tools_registry.py
git commit -m "feat: resolve permitted-injections entries to provider paths"
```

---

### Task 3: Rule rendering — "## Erlaubte Injektionen"

**Files:**
- Modify: `scripts/lib/external_tools.py` (`_generate_tool_rule_content`)
- Test: `tests/test_external_tools_registry.py`

**Interfaces:**
- Consumes: `resolve_injection_path` (Task 2). `_generate_tool_rule_content` gains a `pc: dict` and `project_root: Path` parameter to resolve paths for rendering — both already available at its one call site in `generate_external_tool_artifacts`.

- [ ] **Step 1: Write the failing test**

```python
def test_rule_content_renders_permitted_injections(tmp_path):
    from scripts.lib.external_tools import _generate_tool_rule_content
    tool_def = {
        "description": "d",
        "permitted-injections": [
            {"kind": "skill", "name": "graphify", "description": "Claude-Code-Skill"},
        ],
    }
    content = _generate_tool_rule_content(
        "graphify", tool_def, pc={"skills_dir": ".claude/skills"}, project_root=tmp_path
    )
    assert "## Erlaubte Injektionen" in content
    assert ".claude/skills/graphify" in content
    assert "Claude-Code-Skill" in content


def test_rule_content_omits_section_when_no_injections(tmp_path):
    from scripts.lib.external_tools import _generate_tool_rule_content
    content = _generate_tool_rule_content(
        "graphify", {"description": "d"}, pc={}, project_root=tmp_path
    )
    assert "## Erlaubte Injektionen" not in content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_external_tools_registry.py -k rule_content_renders -v`
Expected: FAIL — `_generate_tool_rule_content` does not accept `pc`/`project_root` yet (`TypeError`).

- [ ] **Step 3: Update `_generate_tool_rule_content` and its one call site**

In `scripts/lib/external_tools.py`, change the signature and body:

```python
def _generate_tool_rule_content(name: str, tool_def: dict, pc: dict, project_root: Path) -> str:
    """Build Markdown rule content for one external tool from its registry def."""
    lines: list[str] = []

    desc = (tool_def.get("description") or name).strip()
    lines += [f"# External Tool: {name}", "", f"> {desc}", "", "---", ""]

    body = (tool_def.get("rule-content") or "").strip()
    if body:
        lines += [body, ""]

    hooks = tool_def.get("hooks", [])
    if isinstance(hooks, list) and hooks:
        lines += ["## Hook-Wrapper", ""]
        lines += [f"- `{EXTERNAL_HOOKS_DIR}/{stem}.sh`" for stem in hooks]
        lines.append("")

    injections = tool_def.get("permitted-injections", [])
    if isinstance(injections, list) and injections:
        lines += ["## Erlaubte Injektionen", ""]
        for entry in injections:
            resolved = resolve_injection_path(entry, pc, project_root)
            rel = resolved.relative_to(project_root.resolve()) if resolved.is_relative_to(project_root.resolve()) else resolved
            desc_suffix = f" — {entry['description']}" if entry.get("description") else ""
            lines.append(f"- `{rel}` ({entry['kind']}){desc_suffix}")
        lines.append("")

    lines += [
        "---",
        "",
        "*Generiert von agent-meta aus `config/external-tools-registry.yaml` — "
        "nicht manuell bearbeiten.*",
    ]
    return "\n".join(lines) + "\n"
```

Update the one call site inside `generate_external_tool_artifacts` (same file, in the `for tool_name in active_tools:` loop under "Rule file generation"):

```python
        content = _generate_tool_rule_content(tool_name, tool_def, pc, project_root)
```

(`pc` and `project_root` are already local variables in `generate_external_tool_artifacts` at that point.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_external_tools_registry.py -v`
Expected: PASS (all tests in the file, including the pre-existing ones — confirms the signature change didn't break the one call site)

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/external_tools.py tests/test_external_tools_registry.py
git commit -m "feat: render permitted-injections in generated tool rule files"
```

---

### Task 4: `.agent-meta-managed` index for `skills_dir`

**Files:**
- Modify: `scripts/lib/skills.py` (new helpers + `sync_external_skills_for_provider`)
- Test: `tests/test_skills.py` (new file — no existing test currently covers `skills.py`; confirmed via `grep -rl "sync_external_skills_for_provider" tests/*.py` returning nothing)

**Interfaces:**
- Produces: `_read_skills_managed_index(skills_dir: Path) -> set[str]`, `_write_skills_managed_index(skills_dir: Path, now_managed: set[str], dry_run: bool) -> None` — two small pure-ish helpers, same format/semantics as the existing `<rules_dir>/.agent-meta-managed` (`rules.py:182-247`) and `<hooks_dir>/.agent-meta-managed` (`hooks.py:228-329`) but factored out standalone so they're testable without needing a full skill-repo fixture (unlike `sync_external_skills_for_provider`, which requires a submodule checkout, a wrapper template and a registered role — out of scope to fabricate here). Consumed by Task 5.

- [ ] **Step 1: Write the failing tests for the two standalone helpers**

```python
# tests/test_skills.py
from pathlib import Path

from scripts.lib.skills import _read_skills_managed_index, _write_skills_managed_index


def test_read_skills_managed_index_missing_file_returns_empty(tmp_path):
    assert _read_skills_managed_index(tmp_path / ".claude" / "skills") == set()


def test_write_then_read_skills_managed_index_roundtrip(tmp_path):
    skills_dir = tmp_path / ".claude" / "skills"
    _write_skills_managed_index(skills_dir, {"reqogniloom-change-manager", "graphify"}, dry_run=False)
    assert _read_skills_managed_index(skills_dir) == {"reqogniloom-change-manager", "graphify"}


def test_write_skills_managed_index_dry_run_does_not_write(tmp_path):
    skills_dir = tmp_path / ".claude" / "skills"
    _write_skills_managed_index(skills_dir, {"graphify"}, dry_run=True)
    assert not (skills_dir / ".agent-meta-managed").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_skills.py -v`
Expected: FAIL with `ImportError: cannot import name '_read_skills_managed_index'`

- [ ] **Step 3: Implement the two helpers**

In `scripts/lib/skills.py`, add (near `_normalize_project_skills`, top of file):

```python
def _read_skills_managed_index(skills_dir: Path) -> set[str]:
    managed_index_path = skills_dir / ".agent-meta-managed"
    if not managed_index_path.exists():
        return set()
    return {
        line.strip()
        for line in managed_index_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def _write_skills_managed_index(skills_dir: Path, now_managed: set[str], dry_run: bool) -> None:
    if dry_run or not now_managed:
        return
    managed_index_path = skills_dir / ".agent-meta-managed"
    managed_index_path.parent.mkdir(parents=True, exist_ok=True)
    managed_index_path.write_text("\n".join(sorted(now_managed)) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_skills.py -v`
Expected: PASS (all three)

- [ ] **Step 5: Wire the helpers into `sync_external_skills_for_provider`**

In `scripts/lib/skills.py`, inside `sync_external_skills_for_provider` (starts at line 280), add right after `skills_dir = project_root / skills_dir_rel` (line 306):

```python
    now_managed: set[str] = set()
```

Inside the `for skill_name, skill_cfg in skills.items():` loop, right after the `if not _skill_is_active(...): ... continue` block (i.e. once we know the skill IS active — immediately after line 361), add:

```python
        now_managed.add(skill_name)
```

After the `for skill_name, skill_cfg in skills.items():` loop ends (same indentation level as the `for` statement itself), add:

```python
    _write_skills_managed_index(skills_dir, now_managed, dry_run)
```

Do not add stale-removal logic here (unlike `rules.py`/`hooks.py`) — `sync_external_skills_for_provider` already `shutil.rmtree`s a skill's directory the moment it becomes inactive (existing code, lines 358-360), so the index never needs separate pruning; it's simply rewritten from `now_managed` on every run that has at least one active skill.

- [ ] **Step 6: Integration smoke test against this repo's real skills**

This repo already has real, active external-skills (e.g. `reqogniloom-change-manager` from `config/skills-registry.yaml`) — use them instead of a fabricated fixture:

Run: `python3 scripts/sync.py --dry-run 2>&1 | grep -i "skill\|drift"`
Expected: no traceback; no new errors. (`--dry-run` skips the actual `.agent-meta-managed` write per `_write_skills_managed_index`'s `dry_run` guard, so this only proves the call path doesn't crash — Step 7 confirms the on-disk effect.)

Run (non-dry-run, safe — this repo's own `.claude/skills/` is regenerated content): `python3 scripts/sync.py 2>&1 | tail -20 && cat .claude/skills/.agent-meta-managed`
Expected: file exists, contains one line per currently-active external skill (e.g. `reqogniloom-change-manager` if enabled in this repo's `.meta-config/project.yaml`).

- [ ] **Step 7: Run full test suite to check no regression**

Run: `python3 -m pytest tests/ -q`
Expected: all pass

- [ ] **Step 8: Commit**

```bash
git add scripts/lib/skills.py tests/test_skills.py
git commit -m "feat: track skills_dir contents in .agent-meta-managed index"
```

---

### Task 5: `scan_injection_drift` — the core scan function

**Files:**
- Modify: `scripts/lib/external_tools.py`
- Test: `tests/test_external_tools_registry.py`

**Interfaces:**
- Consumes: `resolve_active_external_tools`, `resolve_injection_path`, `load_external_tools_registry` (all existing/Task 2), `resolve_active_mcp_servers` from `scripts.lib.mcp` (existing), `is_provider_active` from `scripts.lib.config` (existing — already used in `sync.py`).
- Produces: `scan_injection_drift(agent_meta_root: Path, project_root: Path, config: dict, provider_config: dict) -> dict[str, list[dict]]` — maps provider name → list of `{"path": str (relative to project_root), "kind": str, "tool": str | None}`. Pure — no writes, no `log` param, no `dry_run` param. Consumed by Task 6 (rendering) and Task 8 (Admin UI endpoint).

- [ ] **Step 1: Write the failing test**

```python
def test_scan_injection_drift_flags_unexplained_skill_dir(tmp_path):
    from scripts.lib.external_tools import scan_injection_drift
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {"graphify": {"description": "d", "enabled-by-default": True}})
    # No permitted-injections declared — the skill dir below is unexplained.
    skills_dir = project_root / ".claude" / "skills" / "graphify"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("x", encoding="utf-8")

    provider_config = {"Claude": {
        "skills_dir": ".claude/skills", "hooks_dir": ".claude/hooks",
        "rules_dir": ".claude/rules", "agents_dir": ".claude/agents",
    }}
    findings = scan_injection_drift(agent_meta_root, project_root, {}, provider_config)
    paths = [f["path"] for f in findings["Claude"]]
    assert ".claude/skills/graphify" in paths


def test_scan_injection_drift_clean_when_declared(tmp_path):
    from scripts.lib.external_tools import scan_injection_drift
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {"graphify": {
        "description": "d", "enabled-by-default": True,
        "permitted-injections": [{"kind": "skill", "name": "graphify"}],
    }})
    skills_dir = project_root / ".claude" / "skills" / "graphify"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("x", encoding="utf-8")

    provider_config = {"Claude": {
        "skills_dir": ".claude/skills", "hooks_dir": ".claude/hooks",
        "rules_dir": ".claude/rules", "agents_dir": ".claude/agents",
    }}
    findings = scan_injection_drift(agent_meta_root, project_root, {}, provider_config)
    assert findings["Claude"] == []


def test_scan_injection_drift_flags_loose_root_file(tmp_path):
    from scripts.lib.external_tools import scan_injection_drift
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {})
    infra_root = project_root / ".claude"
    infra_root.mkdir(parents=True)
    (infra_root / "CLAUDE.md").write_text("rogue block", encoding="utf-8")

    provider_config = {"Claude": {
        "skills_dir": ".claude/skills", "hooks_dir": ".claude/hooks",
        "rules_dir": ".claude/rules", "agents_dir": ".claude/agents",
        "settings_file": ".claude/settings.json",
        "pending_tasks_file": ".claude/pending-tasks.md",
        "extension_dir": ".claude/3-project", "snippets_dir": ".claude/snippets",
        "artifact_dir": ".claude/artifacts",
    }}
    findings = scan_injection_drift(agent_meta_root, project_root, {}, provider_config)
    paths = [f["path"] for f in findings["Claude"]]
    assert ".claude/CLAUDE.md" in paths


def test_scan_injection_drift_flags_stray_agent_file(tmp_path):
    from scripts.lib.external_tools import scan_injection_drift
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_framework_registry(agent_meta_root, {})
    agents_dir = project_root / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "rogue-role.md").write_text("x", encoding="utf-8")
    # A real agent-meta-managed role stays unflagged.
    (agents_dir / "developer.md").write_text("x", encoding="utf-8")
    (agents_dir / ".agent-meta-managed").write_text("developer.md\n", encoding="utf-8")

    provider_config = {"Claude": {
        "skills_dir": ".claude/skills", "hooks_dir": ".claude/hooks",
        "rules_dir": ".claude/rules", "agents_dir": ".claude/agents",
    }}
    findings = scan_injection_drift(agent_meta_root, project_root, {}, provider_config)
    paths = [f["path"] for f in findings["Claude"]]
    assert ".claude/agents/rogue-role.md" in paths
    assert ".claude/agents/developer.md" not in paths
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_external_tools_registry.py -k scan_injection_drift -v`
Expected: FAIL with `ImportError: cannot import name 'scan_injection_drift'`

- [ ] **Step 3: Implement `scan_injection_drift`**

In `scripts/lib/external_tools.py`, add:

```python
def _read_managed_index(dir_path: Path) -> set[str]:
    index_path = dir_path / ".agent-meta-managed"
    if not index_path.exists():
        return set()
    return {
        line.strip() for line in index_path.read_text(encoding="utf-8").splitlines() if line.strip()
    }


# Top-level entries under a provider's infra root that agent-meta itself may
# place there, independent of the four managed subdirs. Keyed by the
# provider_config field that names each one; a field absent from `pc` is
# skipped (not every provider has every capability).
_INFRA_ROOT_KNOWN_KEYS = [
    "agents_dir", "hooks_dir", "rules_dir", "skills_dir", "snippets_dir",
    "extension_dir", "artifact_dir", "checkpoint_dir", "settings_file",
    "pending_tasks_file",
]


def scan_injection_drift(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    provider_config: dict,
) -> dict[str, list[dict]]:
    """Find files/dirs under each active provider's infra root that neither
    agent-meta itself manages (per-directory .agent-meta-managed indexes) nor
    any active external tool's permitted-injections declares. Pure — no writes.
    """
    from .deactivation import is_provider_active
    from .mcp import resolve_active_mcp_servers

    registry = load_external_tools_registry(agent_meta_root, config, project_root)
    active_tools = resolve_active_external_tools(config, agent_meta_root, project_root)
    active_mcp = set(resolve_active_mcp_servers(config, agent_meta_root, project_root))

    findings_by_provider: dict[str, list[dict]] = {}

    for provider, pc in provider_config.items():
        if not is_provider_active(config, provider):
            continue

        # Permitted set, resolved to absolute paths, keyed by dir-kind.
        permitted_by_kind: dict[str, set[Path]] = {"skill": set(), "hook": set(), "rule": set()}
        permitted_root_extra: set[Path] = set()  # kind: config/other
        for tool_name in active_tools:
            for entry in registry.get(tool_name, {}).get("permitted-injections", []):
                resolved = resolve_injection_path(entry, pc, project_root)
                if entry["kind"] in permitted_by_kind:
                    permitted_by_kind[entry["kind"]].add(resolved)
                else:
                    permitted_root_extra.add(resolved)

        provider_findings: list[dict] = []

        # --- managed subdirs: skill / hook / rule (declarable kinds) ---
        dir_specs = [
            ("skill", pc.get("skills_dir", ".claude/skills")),
            ("hook", pc.get("hooks_dir", ".claude/hooks")),
            ("rule", pc.get("rules_dir", ".claude/rules")),
        ]
        for kind, dir_rel in dir_specs:
            dir_path = project_root / dir_rel
            if not dir_path.is_dir():
                continue
            managed = _read_managed_index(dir_path)
            if kind == "rule":
                managed |= {f"{TOOL_RULE_PREFIX}{t}.md" for t in active_tools}
                managed |= {f"mcp-{s}.md" for s in active_mcp}
            for child in sorted(dir_path.iterdir()):
                if child.name == ".agent-meta-managed":
                    continue
                if child.name in managed:
                    continue
                if child.resolve() in permitted_by_kind[kind]:
                    continue
                provider_findings.append({
                    "path": str(child.relative_to(project_root)),
                    "kind": kind,
                    "tool": None,
                })

        # --- agents_dir: no declarable permitted-injections kind exists for
        # it (per spec — agent files are never legitimately tool-installed).
        # Only an explicit kind: config/other entry (permitted_root_extra)
        # can excuse a finding here; the existing .agent-meta-managed index
        # (agents.py:1498) still excuses agent-meta's own generated roles.
        agents_dir_path = project_root / pc.get("agents_dir", ".claude/agents")
        if agents_dir_path.is_dir():
            managed = _read_managed_index(agents_dir_path)
            for child in sorted(agents_dir_path.iterdir()):
                if child.name == ".agent-meta-managed":
                    continue
                if child.name in managed:
                    continue
                if child.resolve() in permitted_root_extra:
                    continue
                provider_findings.append({
                    "path": str(child.relative_to(project_root)),
                    "kind": "other",
                    "tool": None,
                })

        # --- infra root: loose files/dirs beside the four managed subdirs ---
        # Determined from the provider's own infra root (parent of skills_dir,
        # e.g. ".claude" for Claude) rather than a hardcoded ".claude" literal,
        # so Gemini/.gemini, Opencode/.opencode etc. are covered the same way.
        skills_dir_rel = pc.get("skills_dir")
        if skills_dir_rel:
            infra_root = (project_root / skills_dir_rel).parent
            if infra_root.is_dir() and infra_root != project_root:
                known_names = set()
                for key in _INFRA_ROOT_KNOWN_KEYS:
                    val = pc.get(key)
                    if val:
                        known_names.add(Path(val).name)
                known_names.add("settings.local.json")
                for child in sorted(infra_root.iterdir()):
                    if child.name in known_names:
                        continue
                    if child.resolve() in permitted_root_extra:
                        continue
                    provider_findings.append({
                        "path": str(child.relative_to(project_root)),
                        "kind": "other",
                        "tool": None,
                    })

        findings_by_provider[provider] = provider_findings

    return findings_by_provider
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_external_tools_registry.py -k scan_injection_drift -v`
Expected: PASS

- [ ] **Step 5: Run the full external-tools test file to check no regressions**

Run: `python3 -m pytest tests/test_external_tools_registry.py -v`
Expected: PASS (all)

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/external_tools.py tests/test_external_tools_registry.py
git commit -m "feat: add scan_injection_drift for external-tool governance"
```

---

### Task 6: `render_injection_drift_artifacts` — sparse drift file

**Files:**
- Modify: `scripts/lib/external_tools.py`
- Test: `tests/test_external_tools_registry.py`

**Interfaces:**
- Consumes: `scan_injection_drift` output (Task 5).
- Produces: `render_injection_drift_artifacts(findings_by_provider: dict[str, list[dict]], project_root: Path, provider_config: dict, log: SyncLog, dry_run: bool) -> None`. Writes/deletes `<rules_dir>/external-tools-drift.md` per provider with `has_rules`.

- [ ] **Step 1: Write the failing test**

```python
def test_render_drift_artifacts_writes_capped_file(tmp_path):
    from scripts.lib.external_tools import render_injection_drift_artifacts
    project_root = tmp_path / "project"
    (project_root / ".claude" / "rules").mkdir(parents=True)
    findings = {"Claude": [
        {"path": f".claude/skills/rogue-{i}", "kind": "skill", "tool": None} for i in range(12)
    ]}
    provider_config = {"Claude": {"has_rules": True, "rules_dir": ".claude/rules"}}
    log = SyncLog()
    render_injection_drift_artifacts(findings, project_root, provider_config, log, dry_run=False)

    out = project_root / ".claude" / "rules" / "external-tools-drift.md"
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert text.count("rogue-") == 10
    assert "2 weitere, siehe sync.log" in text


def test_render_drift_artifacts_removes_stale_file_when_clean(tmp_path):
    from scripts.lib.external_tools import render_injection_drift_artifacts
    project_root = tmp_path / "project"
    rules_dir = project_root / ".claude" / "rules"
    rules_dir.mkdir(parents=True)
    stale = rules_dir / "external-tools-drift.md"
    stale.write_text("old drift", encoding="utf-8")

    provider_config = {"Claude": {"has_rules": True, "rules_dir": ".claude/rules"}}
    log = SyncLog()
    render_injection_drift_artifacts({"Claude": []}, project_root, provider_config, log, dry_run=False)
    assert not stale.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_external_tools_registry.py -k render_drift_artifacts -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `render_injection_drift_artifacts`**

In `scripts/lib/external_tools.py`, add:

```python
DRIFT_FILENAME = "external-tools-drift.md"
_DRIFT_CAP = 10


def _generate_drift_content(findings: list[dict]) -> str:
    lines = [
        "# External-Tool Injection Drift", "",
        "> Automatisch erkannt von `check_injection_drift` — Fremd-Artefakte, die keinem "
        "aktiven Tool in `config/external-tools-registry.yaml` als `permitted-injections` "
        "deklariert sind. Nur Warnung, kein automatisches Eingreifen.",
        "", "---", "",
    ]
    shown = findings[:_DRIFT_CAP]
    for f in shown:
        tool_label = f["tool"] or "keinem registrierten Tool zugeordnet"
        lines.append(f"- `{f['path']}` ({f['kind']}) — {tool_label}")
    remaining = len(findings) - len(shown)
    if remaining > 0:
        lines.append(f"- … {remaining} weitere, siehe sync.log")
    lines.append("")
    return "\n".join(lines) + "\n"


def render_injection_drift_artifacts(
    findings_by_provider: dict[str, list[dict]],
    project_root: Path,
    provider_config: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    for provider, findings in findings_by_provider.items():
        pc = provider_config.get(provider, {})
        if not pc.get("has_rules"):
            continue
        rules_dir = project_root / pc.get("rules_dir", DEFAULT_RULES_DIR)
        target_path = rules_dir / DRIFT_FILENAME

        if not findings:
            if target_path.exists() and not dry_run:
                target_path.unlink()
                log.action("DELETE", str(target_path.relative_to(project_root)), "no drift found")
            continue

        for f in findings:
            log.warning(
                f"external-tools: undeclared artifact '{f['path']}' ({f['kind']}) for provider "
                f"'{provider}' — not covered by any active tool's permitted-injections"
            )

        content = _generate_drift_content(findings)
        rel_out = str(target_path.relative_to(project_root))
        if write_checked(target_path, content, log, "external-tools-drift", dry_run=dry_run):
            log.action("WRITE", rel_out, "external-tools-drift")
        else:
            log.skip(rel_out, "unchanged")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_external_tools_registry.py -k render_drift_artifacts -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/external_tools.py tests/test_external_tools_registry.py
git commit -m "feat: render sparse external-tools-drift.md when drift is found"
```

---

### Task 7: Wire into `sync.py`

**Files:**
- Modify: `scripts/sync.py`
- Test: manual (`--dry-run`), no new automated test (covered by Task 5/6 unit tests + Task 11 integration test)

**Interfaces:**
- Consumes: `scan_injection_drift`, `render_injection_drift_artifacts` (Tasks 5-6).

- [ ] **Step 1: Update the import**

In `scripts/sync.py`, change line 97:

```python
from lib.external_tools import generate_external_tool_artifacts
```
to:
```python
from lib.external_tools import (
    generate_external_tool_artifacts,
    render_injection_drift_artifacts,
    scan_injection_drift,
)
```

- [ ] **Step 2: Call the scan + render once, after the provider loop**

In `scripts/sync.py`, right after the `for provider in providers:` loop ends (immediately before the existing `# Knowledge Engine — Phase A scaffolding` comment at line 1140), add:

```python
        # External-tool injection governance: once per sync run (not per
        # provider) — diffs each active provider's managed dirs against
        # permitted-injections, warns on anything undeclared.
        try:
            drift = scan_injection_drift(agent_meta_root, project_root, config, provider_config)
            render_injection_drift_artifacts(drift, project_root, provider_config, log, args.dry_run)
        except SyncError as exc:
            print(f"\n  !!  External-tool injection drift scan aborted: {exc}", file=sys.stderr)
            sys.exit(1)
```

- [ ] **Step 3: Manual smoke test**

Run: `python3 scripts/sync.py --dry-run --validate 2>&1 | tail -30`
Expected: no traceback; sync completes as before (this repo's own `.claude/skills/graphify/` should now resolve cleanly once Task 1's registry entry is in place — no new drift warning for it; `.claude/CLAUDE.md` and `.claude/settings.json.graphify-bak` SHOULD now appear as warnings, confirming the feature catches the real incident it was built for).

- [ ] **Step 4: Run the full test suite**

Run: `python3 -m pytest tests/ -x -q`
Expected: all pass (353+ pre-existing + new tests from Tasks 1-6)

- [ ] **Step 5: Commit**

```bash
git add scripts/sync.py
git commit -m "feat: wire injection-drift scan into sync.py"
```

---

### Task 8: Admin UI — `GET /api/external-tools/drift`

**Files:**
- Modify: `scripts/admin-server.py`

**Interfaces:**
- Produces: `_compute_injection_drift(self) -> dict` instance method, route `GET /api/external-tools/drift` → `{"findings": {<provider>: [...]}}`.

- [ ] **Step 1: Add the route**

In `scripts/admin-server.py`, inside `_dispatch_get`, add a new branch right after the existing `if path == "/api/consistency-check":` block (around the section shown earlier):

```python
        if path == "/api/external-tools/drift":
            return self._send_json(self._compute_injection_drift())
```

- [ ] **Step 2: Implement the helper**

Add a new method on the same handler class as `_run_consistency_check` (`scripts/admin-server.py:3662`) — place it near the existing deactivation-status handlers at line ~3810, which already establish the exact `project_config`/`provider_config` loading pattern to reuse verbatim:

```python
    def _compute_injection_drift(self) -> dict:
        from lib.external_tools import scan_injection_drift
        from lib.providers import load_providers_config

        root = self.__class__.root
        project_config = self.__class__.config_manager.read("project")
        provider_config = load_providers_config(root)
        findings = scan_injection_drift(root, root, project_config, provider_config)
        return {"findings": findings}
```

This mirrors the exact pattern already used at `scripts/admin-server.py:3810-3814` (`from lib.providers import load_providers_config` / `config_manager.read("project")` / `load_providers_config(root)`) — same imports, same two calls, so `_compute_injection_drift` sees the same effective config (project.yaml overrides included) as every other Admin UI endpoint.

- [ ] **Step 3: Manual smoke test**

Start the admin server (`python3 scripts/admin-server.py` or via the existing `/admin` skill), then:
Run: `curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:<port>/api/external-tools/drift | python3 -m json.tool`
Expected: valid JSON with a `findings` object keyed by provider name (empty lists once Task 1's graphify entry is committed and no other drift exists in this repo, besides the known `.claude/CLAUDE.md` / `settings.json.graphify-bak` pair).

- [ ] **Step 4: Commit**

```bash
git add scripts/admin-server.py
git commit -m "feat: add GET /api/external-tools/drift endpoint"
```

---

### Task 9: Admin UI — drift banner + `permitted-injections` editor

**Files:**
- Modify: `docs/ui/admin-ui.html` (`viewProjectExternalToolsOverrides`, ~line 2785)

**Interfaces:**
- Consumes: `GET /api/external-tools/drift` (Task 8), existing `el(...)` DOM helper, existing `tagEditor(...)` helper (used for `hooks`/`provider-skip` at lines 2925-2941), existing `renderOverridePanel(...)` (used by `renderToolPanel`).

- [ ] **Step 1: Add the drift banner**

In `viewProjectExternalToolsOverrides` (`docs/ui/admin-ui.html:2785`), right after the existing `wrap.appendChild(el("p", ...))` help-text line (2788), add:

This file has no full-width "banner/callout" component (confirmed via `grep -n "banner-warning\|class=\"banner" docs/ui/admin-ui.html` → no matches) — only an inline `badge warn` style (`docs/ui/admin-ui.html:3716`, `#0d9488`-family colors used for the framework badge at line 2264). Follow the file's dominant convention of inline `style:` attributes rather than inventing a new CSS class:

```js
  try {
    const driftResp = await api.get("/api/external-tools/drift");
    const allFindings = Object.values(driftResp.findings || {}).flat();
    if (allFindings.length > 0) {
      const banner = el("div", {
        style: "margin-bottom:var(--space-4); padding:var(--space-3); border:1px solid #b45309; "
             + "border-radius:4px; background:rgba(180,83,9,0.1);",
      });
      banner.appendChild(el("strong", {}, [`${allFindings.length} undeklarierte Artefakte gefunden`]));
      const list = el("ul", { style: "margin:var(--space-2) 0 0 0; padding-left: 20px;" });
      allFindings.slice(0, 10).forEach((f) => {
        list.appendChild(el("li", {}, [`${f.path} (${f.kind}) — ${f.tool || "kein Tool zugeordnet"}`]));
      });
      banner.appendChild(list);
      wrap.appendChild(banner);
    }
  } catch (err) {
    // Non-fatal — drift banner is a convenience, not a blocker for the panel.
  }
```

- [ ] **Step 2: Add the `permitted-injections` editor to `buildEdit`**

In `renderToolPanel`'s `buildEdit` callback (`docs/ui/admin-ui.html:2891-2942`), after the existing `wrapSkip` block (ends at line 2941), add:

```js
        const wrapInjections = el("div", { style: "margin-top: var(--space-2);" });
        wrapInjections.appendChild(el("label", {}, ["Permitted Injections (skills/hooks/rules a tool may self-install)"]));
        const injectionsList = el("div", {});
        const renderInjectionRows = () => {
          injectionsList.innerHTML = "";
          const items = merged["permitted-injections"] || [];
          items.forEach((item, idx) => {
            const row = el("div", { style: "display:flex; gap:var(--space-1); margin-bottom:var(--space-1);" });
            const kindSel = el("select", { class: "form-control" });
            ["skill", "hook", "rule", "config", "other"].forEach((k) => {
              const opt = el("option", { value: k }, [k]);
              if (item.kind === k) opt.selected = true;
              kindSel.appendChild(opt);
            });
            kindSel.onchange = (e) => { const ov = setupEditState(); ov["permitted-injections"][idx].kind = e.target.value; markDirty(); };
            const isPathKind = item.kind === "config" || item.kind === "other";
            const valInput = el("input", { class: "form-control", placeholder: isPathKind ? "path" : "name", value: isPathKind ? (item.path || "") : (item.name || "") });
            valInput.oninput = (e) => {
              const ov = setupEditState();
              const field = (ov["permitted-injections"][idx].kind === "config" || ov["permitted-injections"][idx].kind === "other") ? "path" : "name";
              ov["permitted-injections"][idx][field] = e.target.value;
              markDirty();
            };
            const descInput = el("input", { class: "form-control", placeholder: "description", value: item.description || "" });
            descInput.oninput = (e) => { const ov = setupEditState(); ov["permitted-injections"][idx].description = e.target.value; markDirty(); };
            const removeBtn = el("button", { class: "btn btn-sm" }, ["✕"]);
            removeBtn.onclick = () => { const ov = setupEditState(); ov["permitted-injections"].splice(idx, 1); markDirty(); renderInjectionRows(); };
            row.appendChild(kindSel); row.appendChild(valInput); row.appendChild(descInput); row.appendChild(removeBtn);
            injectionsList.appendChild(row);
          });
        };
        renderInjectionRows();
        wrapInjections.appendChild(injectionsList);
        const addInjectionBtn = el("button", { class: "btn btn-sm" }, ["+ Add Permitted Injection"]);
        addInjectionBtn.onclick = () => {
          const ov = setupEditState();
          ov["permitted-injections"] = ov["permitted-injections"] || [];
          ov["permitted-injections"].push({ kind: "skill", name: "" });
          markDirty();
          renderInjectionRows();
        };
        wrapInjections.appendChild(addInjectionBtn);
        isEditing.appendChild(wrapInjections);
```

- [ ] **Step 3: Add read-only rendering to `buildReadonly`**

In the same function's `buildReadonly` callback (`docs/ui/admin-ui.html:2870-2890`), after the existing `provider-skip` block, add:

```js
        if (merged["permitted-injections"] && merged["permitted-injections"].length > 0) {
            isReadonly.appendChild(el("div", { style: "margin-top:var(--space-2);" }, ["Permitted injections:"]));
            isReadonly.appendChild(renderBadgeList(merged["permitted-injections"].map(
              (i) => `${i.kind}: ${i.name || i.path}`
            )));
        }
```

- [ ] **Step 4: Manual smoke test**

Start the admin UI (`/admin` skill), navigate to Project → External Tools, confirm: the graphify panel shows its `permitted-injections` badge (`skill: graphify`) read-only and editable; adding/removing a row marks the page dirty and survives Save (`PUT /api/config/project/section` with `section: "external-tools-registry"`); the drift banner appears if `.claude/CLAUDE.md`/`settings.json.graphify-bak` are still present in this repo at test time.

- [ ] **Step 5: Commit**

```bash
git add docs/ui/admin-ui.html
git commit -m "feat: add permitted-injections editor and drift banner to Admin UI"
```

---

### Task 10: Full regression pass + spec cross-check

**Files:** none (verification only)

- [ ] **Step 1: Run the complete test suite**

Run: `python3 -m pytest tests/ -q`
Expected: all tests pass, including every test added in Tasks 1-6.

- [ ] **Step 2: Run sync validation**

Run: `python3 scripts/sync.py --dry-run --validate`
Expected: exits 0, no unexpected warnings beyond the two known graphify-legacy findings (`.claude/CLAUDE.md`, `.claude/settings.json.graphify-bak`) — those are expected per the spec's "Migration: graphify" section (cleanup is explicitly out of scope for this plan).

- [ ] **Step 3: Cross-check against the spec's task list**

Re-read `docs/superpowers/specs/2026-08-13-external-tool-injection-governance-design.md` section by section; confirm each of Schema, Pfadauflösung, Drift-Erkennung, Sichtbarkeit im Kontext, sync.py-Integrationspunkt, Admin-UI, Migration: graphify has a corresponding completed task above. Note in the PR description (Task 11) if anything in "Out of Scope" was intentionally left undone (all three items should remain undone: automatic cleanup, content-level drift, honcho entry).

- [ ] **Step 4: Commit** (only if Step 3 surfaced fixes; otherwise skip)

---

### Task 11: PR

**Files:** none (git/GitHub only — delegate to the `git` agent per this repo's branch-guard rule, not run directly)

- [ ] **Step 1: Push the branch and open a PR**

Delegate to the `git` agent: push `feat/external-tools-registry`, open (or update, since PR #490 already exists on this branch) a PR describing the `permitted-injections` governance addition, linking `docs/superpowers/specs/2026-08-13-external-tool-injection-governance-design.md` and this plan file, and noting explicitly that `.claude/CLAUDE.md` / `.claude/settings.json.graphify-bak` cleanup is a deliberate follow-up, not included here.
