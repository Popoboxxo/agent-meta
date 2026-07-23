# Native Extensions Whitelist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing `orchestrator.native-extensions` config block with a `whitelist` property that restricts native Skill/Plugin execution to a named allow-list, wire it through variable injection, the generated rule text, and the Admin UI.

**Architecture:** Reuses the established zero-overhead config-flag → `build_variables()` → `{{#if}}`-templated rule pattern already used for `NATIVE_EXTENSIONS_ENABLED`, `CHECKPOINTING_ENABLED`, etc. No new subsystem, no new config file — one new schema property, two new template variables, one nested `{{#if}}` block, one Admin UI field.

**Tech Stack:** Python 3 (`scripts/lib/config.py`), JSON Schema (`config/project-config.schema.json`), Markdown/Mustache-style templates (`rules/1-generic/use-orchestrator.md`), vanilla JS/DOM (`docs/ui/admin-ui.html`), pytest.

## Global Constraints

- Whitelist semantics (Option B), must appear **verbatim** in schema description, rendered rule text, and Admin UI helptext: "Ist die Whitelist nicht leer, sind ausschließlich die dort gelisteten Skills/Plugins erlaubt — alles andere wird automatisch gesperrt, unabhängig vom generellen Erlaubt-Statement."
- Config path is `orchestrator.native-extensions.whitelist` (nested under the existing block) — **not** a new top-level `native-extensions:` key.
- Default `whitelist: []` (empty) — zero-overhead / no behavior change for projects that don't set it, matching every other conditional flag in this repo.
- `enabled: false` still takes precedence: whitelist is never rendered if `native-extensions.enabled` is `false` (the outer `{{#if NATIVE_EXTENSIONS_ENABLED}}` block already encloses it).
- No technical sandboxing/enforcement — this is a generated behavioral rule the agent follows, like every other rule in this repo. Do not attempt to build a runtime blocker.
- Placeholders in schema/templates use `{{GROSS_MIT_UNTERSTRICH}}` — n/a here since no new `{{VAR}}` substitution placeholders are introduced beyond the two new template variables already named below.

---

### Task 1: Schema — `whitelist` property

**Files:**
- Modify: `config/project-config.schema.json:970-981` (existing `orchestrator.native-extensions` object)
- Test: `tests/test_native_extensions_whitelist.py` (new file)

**Interfaces:**
- Consumes: nothing (pure schema data).
- Produces: `orchestrator.native-extensions.whitelist` becomes a documented, IDE-autocompletable array property. Task 2 reads this via `config.get("orchestrator", {}).get("native-extensions", {}).get("whitelist", [])`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_native_extensions_whitelist.py`:

```python
"""Tests for the orchestrator.native-extensions.whitelist config path."""
from pathlib import Path
import json

import pytest

_AGENT_META_ROOT = Path(__file__).resolve().parent.parent


def test_schema_has_native_extensions_whitelist_property():
    schema_path = _AGENT_META_ROOT / "config" / "project-config.schema.json"
    with schema_path.open(encoding="utf-8") as f:
        schema = json.load(f)
    ne_schema = schema["properties"]["orchestrator"]["properties"]["native-extensions"]
    wl_schema = ne_schema["properties"]["whitelist"]
    assert wl_schema["type"] == "array"
    assert wl_schema["items"]["type"] == "string"
    assert wl_schema["default"] == []
    assert wl_schema["uniqueItems"] is True
    assert "Ist die Whitelist nicht leer" in wl_schema["description"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_native_extensions_whitelist.py -v`
Expected: FAIL — `KeyError: 'whitelist'`

- [ ] **Step 3: Edit the schema**

Edit `config/project-config.schema.json`, replacing lines 970-981 (the full `"native-extensions": { ... }` block) with:

```json
        "native-extensions": {
          "type": "object",
          "description": "Exempt platform-native extension mechanisms (Skills, Plugins, Lifecycle-Hooks) from the STRICT-mode orchestrator gate. When enabled, platform-triggered flows are not treated as a delegation bypass. Default: true.",
          "properties": {
            "enabled": {
              "type": "boolean",
              "default": true,
              "description": "Allow native extension mechanisms to run without going through the orchestrator gate. Branch-guard, commit-conventions and DoD still apply to resulting code changes. Default: true."
            },
            "whitelist": {
              "type": "array",
              "items": { "type": "string" },
              "default": [],
              "uniqueItems": true,
              "description": "Whitelist of allowed native Skill/Plugin identifiers. Ist die Whitelist nicht leer, sind ausschließlich die dort gelisteten Skills/Plugins erlaubt — alles andere wird automatisch gesperrt, unabhängig vom generellen Erlaubt-Statement. Empty (default) = no filter."
            }
          },
          "additionalProperties": false
        },
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_native_extensions_whitelist.py -v`
Expected: PASS

- [ ] **Step 5: Validate schema consistency**

Run: `python scripts/sync.py --dry-run --validate`
Expected: exit code `0` — additive change, no breaking schema errors.

- [ ] **Step 6: Commit**

```bash
git add config/project-config.schema.json tests/test_native_extensions_whitelist.py
git commit -m "feat: add whitelist property to orchestrator.native-extensions schema"
```

---

### Task 2: Variable injection in `build_variables()`

**Files:**
- Modify: `scripts/lib/config.py:466-471` (existing `NATIVE_EXTENSIONS_ENABLED` block)
- Modify: `scripts/lib/config.py:688` (`conditional_vars` set in `strip_inactive_conditional_blocks()`)
- Test: `tests/test_native_extensions_whitelist.py` (append)

**Interfaces:**
- Consumes: `orch_config = config.get("orchestrator", {})` (already resolved earlier in `build_variables()`, same variable used to build `NATIVE_EXTENSIONS_ENABLED`).
- Produces: `variables["NATIVE_EXTENSIONS_WHITELIST_ACTIVE"]` (`"true"`/`"false"`, drives the nested `{{#if}}` in Task 3) and `variables["NATIVE_EXTENSIONS_WHITELIST_TABLE"]` (Markdown bullet list, one `- \`<entry>\`` line per whitelist item, `""` when inactive — consumed by `{{NATIVE_EXTENSIONS_WHITELIST_TABLE}}` in Task 3).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_native_extensions_whitelist.py`:

```python
from scripts.lib.config import build_variables


def _minimal_config(**overrides) -> dict:
    config = {
        "project": {"name": "test-proj", "prefix": "tp", "short": "test-proj"},
        "ai-providers": ["Claude"],
    }
    config.update(overrides)
    return config


def test_build_variables_whitelist_inactive_when_absent():
    variables, _ = build_variables(_minimal_config(), _AGENT_META_ROOT)
    assert variables["NATIVE_EXTENSIONS_WHITELIST_ACTIVE"] == "false"
    assert variables["NATIVE_EXTENSIONS_WHITELIST_TABLE"] == ""


def test_build_variables_whitelist_inactive_when_empty_list():
    config = _minimal_config(orchestrator={"native-extensions": {"enabled": True, "whitelist": []}})
    variables, _ = build_variables(config, _AGENT_META_ROOT)
    assert variables["NATIVE_EXTENSIONS_WHITELIST_ACTIVE"] == "false"
    assert variables["NATIVE_EXTENSIONS_WHITELIST_TABLE"] == ""


def test_build_variables_whitelist_active_with_entries():
    config = _minimal_config(orchestrator={
        "native-extensions": {"enabled": True, "whitelist": ["superpowers", "code-simplifier"]},
    })
    variables, _ = build_variables(config, _AGENT_META_ROOT)
    assert variables["NATIVE_EXTENSIONS_WHITELIST_ACTIVE"] == "true"
    assert variables["NATIVE_EXTENSIONS_WHITELIST_TABLE"] == "- `superpowers`\n- `code-simplifier`"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_native_extensions_whitelist.py -v -k whitelist`
Expected: FAIL — `KeyError: 'NATIVE_EXTENSIONS_WHITELIST_ACTIVE'` (or similar — the key does not exist yet).

- [ ] **Step 3: Implement variable injection**

Edit `scripts/lib/config.py`, directly after line 471 (`variables["NATIVE_EXTENSIONS_ENABLED"] = "true" if _native_ext_enabled else "false"`), insert:

```python
    _native_ext_whitelist = _native_ext_cfg.get("whitelist", []) if isinstance(_native_ext_cfg, dict) else []
    variables["NATIVE_EXTENSIONS_WHITELIST_ACTIVE"] = "true" if _native_ext_whitelist else "false"
    variables["NATIVE_EXTENSIONS_WHITELIST_TABLE"] = (
        "\n".join(f"- `{s}`" for s in _native_ext_whitelist) if _native_ext_whitelist else ""
    )
```

- [ ] **Step 4: Register the new variable as a conditional block driver**

Edit `scripts/lib/config.py:688`, adding `"NATIVE_EXTENSIONS_WHITELIST_ACTIVE"` to the existing tuple:

```python
    conditional_vars.update({k for k in variables if k in ("ORCHESTRATOR_ENABLED", "ORCHESTRATOR_STRICT", "DIRECT_DISPATCH_ENABLED", "UNKNOWN_FALLBACK_ASK_USER", "UNKNOWN_FALLBACK_META_FEEDBACK", "UNKNOWN_FALLBACK_MAIN_CHAT", "A2A_PROTOCOL_ENABLED", "ORCHESTRATOR_OUTCOME_CACHING", "CHECKPOINTING_ENABLED", "NATIVE_EXTENSIONS_ENABLED", "NATIVE_EXTENSIONS_WHITELIST_ACTIVE", "ANALYSIS_ENABLED", "FILE_BASED_AGENTS")})
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_native_extensions_whitelist.py -v`
Expected: all tests PASS (schema test from Task 1 + the three new tests).

- [ ] **Step 6: Run full existing test suite (regression check)**

Run: `python -m pytest tests/ -v --ignore=tests/browser --ignore=tests/manual --ignore=tests/automated`
Expected: no new failures beyond any pre-existing ones (compare failure count/names against a run before this task's changes if any pre-existing failures are present).

- [ ] **Step 7: Commit**

```bash
git add scripts/lib/config.py tests/test_native_extensions_whitelist.py
git commit -m "feat: inject NATIVE_EXTENSIONS_WHITELIST_* variables in build_variables"
```

---

### Task 3: Rule template — nested whitelist block

**Files:**
- Modify: `rules/1-generic/use-orchestrator.md:79-83` (existing `{{#if NATIVE_EXTENSIONS_ENABLED}}` block)
- Test: `tests/test_native_extensions_whitelist.py` (append)

**Interfaces:**
- Consumes: `NATIVE_EXTENSIONS_ENABLED`, `NATIVE_EXTENSIONS_WHITELIST_ACTIVE`, `NATIVE_EXTENSIONS_WHITELIST_TABLE` (all produced by Task 2's `build_variables()`), rendered via `strip_inactive_conditional_blocks()` and `substitute()` in `scripts/lib/config.py` (existing, unmodified functions — nested `{{#if}}` blocks are already supported, resolved inner-to-outer across repeated passes; see `scripts/lib/config.py:680,694-770`).
- Produces: the final rendered rule text propagated into every provider's rule directory (`.claude/rules/use-orchestrator.md`, `.gemini/rules/use-orchestrator.md`, etc.) on the next `sync.py` run.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_native_extensions_whitelist.py`:

```python
from scripts.lib.config import strip_inactive_conditional_blocks


_RULE_SNIPPET = """{{#if NATIVE_EXTENSIONS_ENABLED}}
## Native Provider-Erweiterungen

Native Erweiterungsmechanismen erlaubt.

{{#if NATIVE_EXTENSIONS_WHITELIST_ACTIVE}}
**Whitelist aktiv:** Ist die Whitelist nicht leer, sind ausschließlich die dort gelisteten Skills/Plugins erlaubt — alles andere wird automatisch gesperrt, unabhängig vom generellen Erlaubt-Statement.

Erlaubte Skills/Plugins:
{{NATIVE_EXTENSIONS_WHITELIST_TABLE}}
{{/if}}
{{/if}}
{{#unless NATIVE_EXTENSIONS_ENABLED}}
## Native Provider-Erweiterungen — deaktiviert
{{/unless}}
"""


def test_rule_template_renders_whitelist_block_when_active():
    variables = {
        "NATIVE_EXTENSIONS_ENABLED": "true",
        "NATIVE_EXTENSIONS_WHITELIST_ACTIVE": "true",
        "NATIVE_EXTENSIONS_WHITELIST_TABLE": "- `superpowers`",
    }
    result = strip_inactive_conditional_blocks(_RULE_SNIPPET, variables)
    assert "Ist die Whitelist nicht leer" in result
    assert "- `superpowers`" in result
    assert "deaktiviert" not in result


def test_rule_template_omits_whitelist_block_when_inactive():
    variables = {
        "NATIVE_EXTENSIONS_ENABLED": "true",
        "NATIVE_EXTENSIONS_WHITELIST_ACTIVE": "false",
        "NATIVE_EXTENSIONS_WHITELIST_TABLE": "",
    }
    result = strip_inactive_conditional_blocks(_RULE_SNIPPET, variables)
    assert "Whitelist aktiv" not in result
    assert "Native Provider-Erweiterungen" in result
    assert "deaktiviert" not in result


def test_rule_template_omits_whitelist_block_when_native_extensions_disabled():
    variables = {
        "NATIVE_EXTENSIONS_ENABLED": "false",
        "NATIVE_EXTENSIONS_WHITELIST_ACTIVE": "true",
        "NATIVE_EXTENSIONS_WHITELIST_TABLE": "- `superpowers`",
    }
    result = strip_inactive_conditional_blocks(_RULE_SNIPPET, variables)
    assert "Whitelist aktiv" not in result
    assert "deaktiviert" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_native_extensions_whitelist.py -v -k rule_template`
Expected: FAIL on `test_rule_template_renders_whitelist_block_when_active` and `test_rule_template_omits_whitelist_block_when_inactive` — the nested `{{#if NATIVE_EXTENSIONS_WHITELIST_ACTIVE}}` marker text (`{{#if ...}}`, `{{/if}}`) leaks into the output as literal text instead of being resolved, because `NATIVE_EXTENSIONS_WHITELIST_ACTIVE` is not yet in `conditional_vars` at the time this test's own fixture builds `variables` directly (this test calls `strip_inactive_conditional_blocks` directly, so it exercises the function itself — it should already pass once Task 2's `conditional_vars` change is in place, since `conditional_vars` is derived from `variables.keys()` filtered by the hardcoded name tuple inside the function, not from an external registry). If it fails, confirm the exact failure mode matches "raw `{{#if}}` marker text present in output" before proceeding.

- [ ] **Step 3: Edit the rule template**

Edit `rules/1-generic/use-orchestrator.md`, replacing lines 79-83:

```
{{#if NATIVE_EXTENSIONS_ENABLED}}
## Native Provider-Erweiterungen

Native Erweiterungsmechanismen der Plattform — Skills, Plugins, Lifecycle-Hooks — werden von diesem Gate NICHT blockiert. Sie laufen im Rahmen des eigenen Invocation-Flows der Plattform (z.B. ein SessionStart-Hook, der eine Skill lädt) und zählen nicht als `task`-Call oder `edit`/`write`-Aktion im Sinne dieser Regel. Folge ihren Anweisungen gemäß Plattform-Konvention. Das hebt Branch-Guard, Commit-Konventionen und DoD-Criteria NICHT auf — die gelten weiterhin für jede daraus resultierende Code-Änderung.
{{/if}}
```

with:

```
{{#if NATIVE_EXTENSIONS_ENABLED}}
## Native Provider-Erweiterungen

Native Erweiterungsmechanismen der Plattform — Skills, Plugins, Lifecycle-Hooks — werden von diesem Gate NICHT blockiert. Sie laufen im Rahmen des eigenen Invocation-Flows der Plattform (z.B. ein SessionStart-Hook, der eine Skill lädt) und zählen nicht als `task`-Call oder `edit`/`write`-Aktion im Sinne dieser Regel. Folge ihren Anweisungen gemäß Plattform-Konvention. Das hebt Branch-Guard, Commit-Konventionen und DoD-Criteria NICHT auf — die gelten weiterhin für jede daraus resultierende Code-Änderung.

{{#if NATIVE_EXTENSIONS_WHITELIST_ACTIVE}}
**Whitelist aktiv:** Ist die Whitelist nicht leer, sind ausschließlich die dort gelisteten Skills/Plugins erlaubt — alles andere wird automatisch gesperrt, unabhängig vom generellen Erlaubt-Statement.

Erlaubte Skills/Plugins:
{{NATIVE_EXTENSIONS_WHITELIST_TABLE}}
{{/if}}
{{/if}}
```

Do not modify the adjacent `{{#unless NATIVE_EXTENSIONS_ENABLED}}` block (lines 84-88 before this edit) — it is unaffected by this task.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_native_extensions_whitelist.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Regenerate propagated rule copies**

Run: `python scripts/sync.py --dry-run`
Expected: exit code `0`; log shows `use-orchestrator.md` scheduled for update in each active provider's rules directory (`.claude/rules/`, `.gemini/rules/`, `.mammouth/rules/`, `AGENTS.md`-embedded copy) since the template content changed. No `knowledge-engine` regression (unrelated feature, should remain `[SKIP]`).

Run: `python scripts/sync.py`
Expected: exit code `0`; the propagated `use-orchestrator.md` copies now contain the same content as `rules/1-generic/use-orchestrator.md` (no whitelist section rendered, since agent-meta's own `.meta-config/project.yaml` does not set `orchestrator.native-extensions.whitelist`).

- [ ] **Step 6: Run full existing test suite (regression check)**

Run: `python -m pytest tests/ -v --ignore=tests/browser --ignore=tests/manual --ignore=tests/automated`
Expected: no new failures.

- [ ] **Step 7: Commit**

```bash
git add rules/1-generic/use-orchestrator.md tests/test_native_extensions_whitelist.py .claude/rules/use-orchestrator.md .gemini/rules/use-orchestrator.md .mammouth/rules/use-orchestrator.md .continue/rules/use-orchestrator.md AGENTS.md
git commit -m "feat: render native-extensions whitelist block in orchestrator rule"
```

(Adjust the propagated-file list in the `git add` to whatever `git status` actually shows changed after the `sync.py` run in Step 5 — only stage files that `sync.py` itself modified, do not use `git add -A`.)

---

### Task 4: Admin UI — whitelist editor

**Files:**
- Modify: `docs/ui/admin-ui.html` — new standalone helper function near `checkboxField` (currently `docs/ui/admin-ui.html:4041-4051`)
- Modify: `docs/ui/admin-ui.html:4557` (inside `viewProjectOrchestrator()`, directly after the existing `checkboxField("checkpointing", ...)` line)

**Interfaces:**
- Consumes: `orch["native-extensions"]` (object, may be absent — same `orch` variable already in scope in `viewProjectOrchestrator()`, loaded from `project.yaml` via `loadProject()`).
- Produces: on save, `orch["native-extensions"] = { enabled, whitelist }` is included in the object passed to the existing `saveProjectSection("orchestrator", orch, status)` call (`docs/ui/admin-ui.html:4755`) — no new REST endpoint, no new save path.

- [ ] **Step 1: Add a standalone tag-editor helper function**

Edit `docs/ui/admin-ui.html`, directly after the existing `checkboxField` function (after line 4051), insert:

```javascript
function tagEditorField(label, values, onChange, helpText) {
  const field = el("div", { class: "field" });
  field.appendChild(el("label", { class: "field-label" }, [label]));
  const wrap = el("div", { class: "tag-editor flex-row", style: "gap:6px; flex-wrap:wrap;" });
  const tags = Array.isArray(values) ? [...values] : [];
  const refresh = () => {
    wrap.innerHTML = "";
    tags.forEach((t, i) => {
      const tag = el("span", { class: "badge" }, [String(t)]);
      const rm = el("button", { class: "btn btn-ghost", style: "padding:0 6px; font-size:11px;", title: "remove" }, ["×"]);
      rm.addEventListener("click", () => { tags.splice(i, 1); onChange([...tags]); refresh(); });
      tag.appendChild(rm);
      wrap.appendChild(tag);
    });
    const inp = el("input", { type: "text", placeholder: "add…", style: "max-width:160px;" });
    inp.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" && inp.value.trim()) {
        ev.preventDefault();
        tags.push(inp.value.trim()); onChange([...tags]); inp.value = ""; refresh();
      }
    });
    wrap.appendChild(inp);
  };
  refresh();
  field.appendChild(wrap);
  if (helpText) field.appendChild(el("div", { class: "field-help" }, [helpText]));
  return field;
}
```

- [ ] **Step 2: Wire the whitelist editor into the Orchestrator panel**

Edit `docs/ui/admin-ui.html`, directly after line 4557 (`genPanel.appendChild(checkboxField("checkpointing", orch.checkpointing, v => { orch.checkpointing = v; }));`, before `wrap.appendChild(genPanel);`), insert:

```javascript
  // ── Native Extensions ────────────────────────────────────────────────────
  const nativeExt = (orch["native-extensions"] && typeof orch["native-extensions"] === "object") ? orch["native-extensions"] : {};
  const nePanel = el("div", { class: "panel" });
  nePanel.appendChild(el("h2", {}, ["Native Extensions"]));
  nePanel.appendChild(checkboxField("enabled", nativeExt.enabled !== false, v => { nativeExt.enabled = v; orch["native-extensions"] = nativeExt; }));
  nePanel.appendChild(tagEditorField(
    "whitelist",
    nativeExt.whitelist,
    v => { nativeExt.whitelist = v; orch["native-extensions"] = nativeExt; },
    "Ist die Whitelist nicht leer, sind ausschließlich die dort gelisteten Skills/Plugins erlaubt — alles andere wird automatisch gesperrt, unabhängig vom generellen Erlaubt-Statement. Leer = kein Filter."
  ));
  wrap.appendChild(nePanel);
```

- [ ] **Step 3: Manual smoke test**

Run: `python scripts/admin-server.py --no-viz --port 7420 --root .`

Open `http://localhost:7420/project/orchestrator` in a browser. Confirm:
- A "Native Extensions" panel appears below the existing "General" panel, with an `enabled` toggle (checked by default) and a `whitelist` tag editor.
- Typing a value (e.g. `superpowers`) and pressing Enter adds it as a removable badge.
- Clicking the `×` on a badge removes it.
- The helptext below the whitelist field shows the Option-B sentence verbatim.
- Saving the Orchestrator page (existing save button, calls `saveProjectSection("orchestrator", orch, status)`) writes `orchestrator.native-extensions.whitelist` into `.meta-config/project.yaml` with the entered values — verify by reading the file after save.

Stop the server (`Ctrl+C`) after verifying. Report the outcome in the task report; this step cannot be scripted as a pytest assertion since it is a live-server DOM/UX check.

- [ ] **Step 4: Commit**

```bash
git add docs/ui/admin-ui.html
git commit -m "feat: add native-extensions whitelist editor to Admin UI"
```

---

### Task 5: Framework-default documentation

**Files:**
- Modify: `templates/configs/project.yaml.example`
- Modify: `docs/guides/project.yaml.example` (mirror copy — confirm with `diff templates/configs/project.yaml.example docs/guides/project.yaml.example` whether these two files are kept identical in this repo; if they diverge in other sections, only mirror this specific addition, matching the file's existing local conventions)

**Interfaces:**
- Consumes: nothing (documentation only).
- Produces: a commented-out example block new users can uncomment, showing the recommended framework-default shape of `orchestrator.native-extensions`.

- [ ] **Step 1: Locate the orchestrator section in the example file**

Run: `grep -n "orchestrator" templates/configs/project.yaml.example`

Find the existing `orchestrator:` block (or its absence — if no `orchestrator:` block exists yet in the example file, add a new one at the end of the file rather than interleaving with unrelated sections).

- [ ] **Step 2: Add the commented example**

Append (or insert into the existing `orchestrator:` section, matching its indentation) a commented block:

```yaml
# orchestrator:
#   native-extensions:
#     enabled: true          # allow platform-native Skills/Plugins (default: true)
#     whitelist: []          # empty = no filter. Non-empty = allow-only:
#                            # only listed Skills/Plugins may run, everything else is blocked
#                            # regardless of `enabled`. Example: ["superpowers", "code-simplifier"]
```

- [ ] **Step 3: Verify the file still parses as valid YAML once uncommented**

Run a scratch check: copy the uncommented block into a throwaway `.yaml` file and run `python -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]))" <scratch-file>` to confirm no indentation errors. Delete the scratch file afterward.

- [ ] **Step 4: Commit**

```bash
git add templates/configs/project.yaml.example docs/guides/project.yaml.example
git commit -m "docs: document native-extensions whitelist in project.yaml example"
```

---

## Final Verification

- [ ] **Run the complete new + existing test suite**

Run: `python -m pytest tests/test_native_extensions_whitelist.py tests/ -v --ignore=tests/browser --ignore=tests/manual --ignore=tests/automated`
Expected: 0 new failures (compare against the pre-existing failure baseline noted during Task 2, Step 6, if any exist).

- [ ] **Confirm zero-overhead for a project without the whitelist**

Run: `python -m pytest tests/test_native_extensions_whitelist.py -k "inactive_when_absent" -v`
Expected: PASS — confirms no behavior change for the (majority) case of projects that never set `orchestrator.native-extensions.whitelist`.

- [ ] **Full sync validation on agent-meta itself**

Run: `python scripts/sync.py --dry-run --validate`
Expected: exit code `0`.

Run: `python scripts/sync.py --check`
Expected: exit code `0` — confirms generated context files (CLAUDE.md, AGENTS.md, GEMINI.md, etc.) are up to date after Task 3's `sync.py` run and no further regeneration is pending.
