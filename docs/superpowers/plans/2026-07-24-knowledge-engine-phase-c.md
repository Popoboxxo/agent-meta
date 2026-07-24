# Knowledge Engine Phase C (AdminUI Integration) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/project/knowledge-engine` AdminUI page that lets a user configure the Knowledge Engine bundle (schema-language, OKF rules, ingest/query/lint operations, migration safety flags, search engine) via 6 panels and 5 domain presets, backed by a schema extension and a `admin-server.py` write-allowlist entry.

**Architecture:** Four independent layers, each additive and backward-compatible: (1) JSON Schema extension in `config/project-config.schema.json` adds new optional `knowledge-engine` sub-fields with `additionalProperties: false` at every level; (2) `scripts/admin-server.py::_write_project_section()` gets `"knowledge-engine"` added to its `allowed` set so the AdminUI can PUT this section; (3) `docs/ui/admin-ui.html` gets three routing insertion points (sidebar entry, `router.register`, help `routeMap`); (4) a new `viewProjectKnowledgeEngine()` function renders the 6 panels, following the existing `viewProjectDodOverrides()` pattern (`loadProject()` / `clone()` / `saveProjectSection()` / status element / re-render-on-change).

**Tech Stack:** Python 3 (stdlib only) for schema + admin-server; vanilla JS (no framework, `el()` DOM helper, existing `dropdownField`/`checkboxField`/`labeledTextField` helpers) for the AdminUI view; pytest for tests.

## Global Constraints

- Placeholders are always `{{GROSS_MIT_UNTERSTRICH}}` — not applicable to this plan (no template changes).
- `additionalProperties: false` must be set at every new object level in the schema (`okf`, `operations`, `operations.ingest`, `operations.query`, `operations.lint`, `migration`, `search`) — matches existing `knowledge-engine` block convention.
- Migration safety invariant (carried from Phase B, hard constraint): `migration.preserve-originals` defaults to `true`; `migration.auto-detect-sources` and `migration.clean-duplicates` default to `false`. Migration must never auto-start or auto-delete — this plan only adds config toggles, it does not touch the `knowledge-migrator` agent's behavior.
- No Dry-run button for this view (no existing Knowledge-Engine-specific `runDryRun()` hook — out of scope, per spec).
- No new automated browser/E2E test (no precedent for automated AdminUI view tests in this project — per spec).
- Commit message format: Conventional Commits (`feat:`, `test:`, `docs:`), English, imperative, ≤72 chars first line, no REQ-ID (req-traceability is disabled for this project).
- Branch: `feat/knowledge-engine-phase-c` (already created, spec already committed as `fe676d7`). All tasks commit directly onto this branch.

---

### Task 1: JSON Schema extension for `knowledge-engine`

**Files:**
- Modify: `config/project-config.schema.json` (the `knowledge-engine.properties` object, currently ending after `bundle-path` around line 851-853 per the design spec; the exact insertion point is directly after the existing `bundle-path` property definition and before the object's closing `},\n"additionalProperties": false`)
- Test: `tests/test_knowledge_engine.py`

**Interfaces:**
- Produces: schema properties `sources-dir`, `wiki-dir`, `schema-language`, `okf`, `operations`, `migration`, `search` under `knowledge-engine.properties` — consumed by Task 2 (admin-server allowlist, no schema dependency) and Task 4 (AdminUI panels read/write these exact field names).

- [ ] **Step 1: Write the failing schema-validation test**

Add to `tests/test_knowledge_engine.py`:

```python
def test_schema_knowledge_engine_has_phase_c_properties():
    import json
    from pathlib import Path
    schema_path = Path(__file__).parent.parent / "config" / "project-config.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    ke_props = schema["properties"]["knowledge-engine"]["properties"]
    for field in ("sources-dir", "wiki-dir", "schema-language", "okf", "operations", "migration", "search"):
        assert field in ke_props, f"missing knowledge-engine.{field}"
    assert ke_props["okf"]["additionalProperties"] is False
    assert ke_props["operations"]["additionalProperties"] is False
    assert ke_props["operations"]["properties"]["ingest"]["additionalProperties"] is False
    assert ke_props["operations"]["properties"]["query"]["additionalProperties"] is False
    assert ke_props["operations"]["properties"]["lint"]["additionalProperties"] is False
    assert ke_props["migration"]["additionalProperties"] is False
    assert ke_props["migration"]["properties"]["preserve-originals"]["default"] is True
    assert ke_props["migration"]["properties"]["auto-detect-sources"]["default"] is False
    assert ke_props["migration"]["properties"]["clean-duplicates"]["default"] is False
    assert ke_props["search"]["additionalProperties"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_knowledge_engine.py::test_schema_knowledge_engine_has_phase_c_properties -v`
Expected: FAIL with `KeyError: 'sources-dir'` (or similar — the fields don't exist yet).

- [ ] **Step 3: Add the schema properties**

Open `config/project-config.schema.json`. Locate the `"knowledge-engine"` object (search for `"knowledge-engine": {`). Inside its `"properties"` object, after the existing `"bundle-path"` property definition, insert the following properties (comma-separated, before the object's own closing brace):

```json
        "sources-dir": {
          "type": "string",
          "default": "sources",
          "description": "Relative path (inside the bundle) where raw source documents live before ingestion."
        },
        "wiki-dir": {
          "type": "string",
          "default": "wiki",
          "description": "Relative path (inside the bundle) where curated wiki pages are written."
        },
        "schema-language": {
          "type": "string",
          "default": "auto",
          "description": "Language used for schema.md and generated wiki page headers ('auto' = follow project language rules)."
        },
        "okf": {
          "type": "object",
          "description": "Open Knowledge Format enforcement rules for ingested/curated pages.",
          "properties": {
            "enforce-frontmatter": { "type": "boolean", "default": true },
            "allowed-types": {
              "type": "array",
              "items": { "type": "string" },
              "default": []
            },
            "auto-index": { "type": "boolean", "default": true },
            "auto-log": { "type": "boolean", "default": true }
          },
          "additionalProperties": false
        },
        "operations": {
          "type": "object",
          "description": "Behavior toggles for the ingest, query and lint pipelines.",
          "properties": {
            "ingest": {
              "type": "object",
              "properties": {
                "auto-cross-reference": { "type": "boolean", "default": true },
                "auto-index-update": { "type": "boolean", "default": true },
                "batch-mode": { "type": "boolean", "default": false }
              },
              "additionalProperties": false
            },
            "query": {
              "type": "object",
              "properties": {
                "file-back-results": { "type": "boolean", "default": true }
              },
              "additionalProperties": false
            },
            "lint": {
              "type": "object",
              "properties": {
                "schedule": {
                  "type": "string",
                  "enum": ["on-demand", "post-ingest", "periodic"],
                  "default": "on-demand"
                },
                "checks": {
                  "type": "array",
                  "items": {
                    "type": "string",
                    "enum": [
                      "broken-links",
                      "missing-frontmatter",
                      "orphaned-pages",
                      "duplicate-concepts",
                      "stale-index",
                      "inconsistent-naming",
                      "missing-citations",
                      "unresolved-todos"
                    ]
                  },
                  "default": ["broken-links", "missing-frontmatter"]
                }
              },
              "additionalProperties": false
            }
          },
          "additionalProperties": false
        },
        "migration": {
          "type": "object",
          "description": "Safety toggles for the knowledge-migrator agent. Migration copies, never moves.",
          "properties": {
            "auto-detect-sources": { "type": "boolean", "default": false },
            "clean-duplicates": { "type": "boolean", "default": false },
            "preserve-originals": { "type": "boolean", "default": true }
          },
          "additionalProperties": false
        },
        "search": {
          "type": "object",
          "properties": {
            "engine": {
              "type": "string",
              "enum": ["index-only", "mcp-qmd", "custom"],
              "default": "index-only"
            },
            "mcp-server": { "type": "string", "default": "" }
          },
          "additionalProperties": false
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_knowledge_engine.py::test_schema_knowledge_engine_has_phase_c_properties -v`
Expected: PASS

- [ ] **Step 5: Validate the schema is still well-formed JSON and passes sync's own validation**

Run: `python scripts/sync.py --dry-run --validate`
Expected: exits 0, no schema errors reported.

- [ ] **Step 6: Commit**

```bash
git add config/project-config.schema.json tests/test_knowledge_engine.py
git commit -m "feat: extend knowledge-engine schema for Phase C AdminUI fields"
```

---

### Task 2: `admin-server.py` — allow `knowledge-engine` section writes

**Files:**
- Modify: `scripts/admin-server.py:3296-3302` (the `allowed` set inside `_write_project_section()`)
- Test: `tests/test_knowledge_engine.py`

**Interfaces:**
- Consumes: nothing new (uses existing `_write_project_section()` mechanics).
- Produces: PUT `/api/config/project/section` with `{"section": "knowledge-engine", "data": {...}}` now succeeds instead of raising `ValueError("section not allowed: knowledge-engine")`. Task 4's `saveProjectSection("knowledge-engine", ke, status)` call depends on this.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_knowledge_engine.py` (uses the existing `AdminHandler`/`ConfigManager` test fixtures already present in this file for other section-write tests — check the top of the file for the fixture name and reuse it; if the file has no HTTP-level fixture yet, test the allowed-set directly via source inspection):

```python
def test_admin_server_allows_knowledge_engine_section_write():
    import ast
    from pathlib import Path
    source = Path(__file__).parent.parent / "scripts" / "admin-server.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_write_project_section":
            found = "knowledge-engine" in ast.dump(node)
            break
    assert found, "'knowledge-engine' not found in _write_project_section's allowed set"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_knowledge_engine.py::test_admin_server_allows_knowledge_engine_section_write -v`
Expected: FAIL (`assert False`).

- [ ] **Step 3: Add `"knowledge-engine"` to the allowed set**

In `scripts/admin-server.py`, locate the `allowed = { ... }` set inside `_write_project_section()` (around line 3296). Add `"knowledge-engine"` as a new entry, e.g. after `"environments"`:

```python
        allowed = {
            "agent-prompts", "model-overrides", "memory-overrides", "permission-mode-overrides",
            "steps-overrides", "dod", "rules", "roles", "orchestrator", "viz", "admin-ui",
            "provider-tier-overrides", "project", "dod-preset", "rules-preset", "speech-mode",
            "tier-preset", "se-focus", "ai-providers", "platforms", "provider-options",
            "provider-isolation", "environments", "model-source-preference", "knowledge-engine",
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_knowledge_engine.py::test_admin_server_allows_knowledge_engine_section_write -v`
Expected: PASS

- [ ] **Step 5: Run the full existing admin-server test module to check no regression**

Run: `pytest tests/test_knowledge_engine.py -v`
Expected: all tests PASS (including Task 1's new test).

- [ ] **Step 6: Commit**

```bash
git add scripts/admin-server.py tests/test_knowledge_engine.py
git commit -m "feat: allow knowledge-engine section writes in admin-server"
```

---

### Task 3: AdminUI routing — sidebar, router, help map

**Files:**
- Modify: `docs/ui/admin-ui.html` at three locations:
  - Sidebar `groups` array, "Project instance" group (currently ends at line 1363 with the `/project/advanced` entry)
  - `router.register(...)` block (currently ends at line 7403 with `/project/advanced`, before the backward-compat block)
  - `routeMap` object inside the help-system IIFE (currently ends at line 7491 with `"project/advanced"`)

**Interfaces:**
- Consumes: `viewProjectKnowledgeEngine` — the function Task 4 defines. This task's `router.register` line references that name; if Task 4 has not run yet, the page will 404 at runtime until Task 4 lands (acceptable — both tasks land on the same branch before merge; no intermediate deploy).
- Produces: route `/project/knowledge-engine` resolvable via sidebar click and direct navigation.

- [ ] **Step 1: Write the failing test (static HTML structure check)**

Add to `tests/test_knowledge_engine.py`:

```python
def test_admin_ui_has_knowledge_engine_route():
    from pathlib import Path
    html = (Path(__file__).parent.parent / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")
    assert '{ route: "/project/knowledge-engine", label: "Knowledge Engine", icon: "🧠" }' in html
    assert 'router.register("/project/knowledge-engine", viewProjectKnowledgeEngine);' in html
    assert '"project/knowledge-engine": "project_instance-knowledge_engine",' in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_knowledge_engine.py::test_admin_ui_has_knowledge_engine_route -v`
Expected: FAIL (assertion errors — none of the three strings exist yet).

- [ ] **Step 3: Add the sidebar entry**

In `docs/ui/admin-ui.html`, in the `buildSidebar()` function, inside the `"Project instance"` group's `items` array, add a new line immediately after the `/project/advanced` entry (currently the last entry in that array, ends with `},` on the line containing `label: "Advanced (raw YAML)"`):

```javascript
        { route: "/project/advanced",  label: "Advanced (raw YAML)", icon: "⌨" },
        { route: "/project/knowledge-engine", label: "Knowledge Engine", icon: "🧠" },
```

- [ ] **Step 4: Add the router registration**

In the same file, in the `init()` function's routes block, add a new line immediately after the `/project/advanced` registration (currently `router.register("/project/advanced", viewProjectAdvanced);`, right before the `// Backward-compat` comment):

```javascript
  router.register("/project/advanced",        viewProjectAdvanced);
  router.register("/project/knowledge-engine", viewProjectKnowledgeEngine);
  // Backward-compat: keep the old route pointing at the raw editor.
```

- [ ] **Step 5: Add the help routeMap entry**

In the same file, inside the help-system IIFE's `routeMap` object, add a new line immediately after the `"project/advanced"` entry:

```javascript
    "project/advanced": "project_instance-advanced",
    "project/knowledge-engine": "project_instance-knowledge_engine",
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_knowledge_engine.py::test_admin_ui_has_knowledge_engine_route -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add docs/ui/admin-ui.html tests/test_knowledge_engine.py
git commit -m "feat: register knowledge-engine route in AdminUI"
```

---

### Task 4: `viewProjectKnowledgeEngine()` — the 6-panel view function

**Files:**
- Modify: `docs/ui/admin-ui.html` — insert a new function after `viewProjectRulesOverrides()` and before `viewProjectEnvironments()` (locate `viewProjectRulesOverrides` — starts at line 2590 per Task 3's grep context — find its closing `}` and the start of the next `/* ... Views — ... */` comment block or `async function viewProjectEnvironments()`, and insert between them)
- Test: `tests/test_knowledge_engine.py`

**Interfaces:**
- Consumes: `el()`, `clone()`, `loadProject()`, `saveProjectSection(key, value, statusEl)`, `dropdownField(label, options, value, onChange, labels)`, `checkboxField(label, value, onChange)`, `labeledTextField(label, value, onInput, help)` — all already defined earlier in `admin-ui.html` (confirmed at lines 739, 3970, 3976, 4023, 4041, 3997 respectively).
- Produces: `viewProjectKnowledgeEngine` — the function name Task 3's `router.register` call references (must match exactly, case-sensitive).

- [ ] **Step 1: Write the failing test**

Add to `tests/test_knowledge_engine.py`:

```python
def test_admin_ui_has_view_project_knowledge_engine_function():
    from pathlib import Path
    html = (Path(__file__).parent.parent / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")
    assert "async function viewProjectKnowledgeEngine()" in html
    assert 'const PRESETS = {' in html
    for preset_name in ("research", "personal", "business", "book", "internal-docs", "custom"):
        assert f'{preset_name}: {{' in html or f'"{preset_name}": {{' in html
    assert 'saveProjectSection("knowledge-engine", ke, status)' in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_knowledge_engine.py::test_admin_ui_has_view_project_knowledge_engine_function -v`
Expected: FAIL (function doesn't exist yet).

- [ ] **Step 3: Insert the `viewProjectKnowledgeEngine()` function**

Insert this complete function into `docs/ui/admin-ui.html`, right after `viewProjectRulesOverrides()`'s closing `}` (before the next view function or section comment):

```javascript
/* =========================================================================
 * Views — Project Knowledge Engine
 * ========================================================================= */
const KNOWLEDGE_ALL_LINT_CHECKS = [
  "broken-links", "missing-frontmatter", "orphaned-pages", "duplicate-concepts",
  "stale-index", "inconsistent-naming", "missing-citations", "unresolved-todos",
];

const KNOWLEDGE_PRESETS = {
  research: {
    domain: "research", "bundle-path": "knowledge", "sources-dir": "sources", "wiki-dir": "wiki",
    "schema-language": "auto",
    okf: { "enforce-frontmatter": true, "allowed-types": ["paper", "note", "citation"], "auto-index": true, "auto-log": true },
    operations: {
      ingest: { "auto-cross-reference": true, "auto-index-update": true, "batch-mode": true },
      query: { "file-back-results": true },
      lint: { schedule: "post-ingest", checks: ["broken-links", "missing-frontmatter", "missing-citations", "duplicate-concepts"] },
    },
    migration: { "auto-detect-sources": false, "clean-duplicates": false, "preserve-originals": true },
    search: { engine: "index-only", "mcp-server": "" },
  },
  personal: {
    domain: "personal", "bundle-path": "knowledge", "sources-dir": "sources", "wiki-dir": "wiki",
    "schema-language": "auto",
    okf: { "enforce-frontmatter": true, "allowed-types": ["note", "journal"], "auto-index": true, "auto-log": true },
    operations: {
      ingest: { "auto-cross-reference": false, "auto-index-update": true, "batch-mode": false },
      query: { "file-back-results": true },
      lint: { schedule: "on-demand", checks: ["broken-links", "missing-frontmatter"] },
    },
    migration: { "auto-detect-sources": false, "clean-duplicates": false, "preserve-originals": true },
    search: { engine: "index-only", "mcp-server": "" },
  },
  business: {
    domain: "business", "bundle-path": "knowledge", "sources-dir": "sources", "wiki-dir": "wiki",
    "schema-language": "auto",
    okf: { "enforce-frontmatter": true, "allowed-types": ["process", "decision", "policy"], "auto-index": true, "auto-log": true },
    operations: {
      ingest: { "auto-cross-reference": true, "auto-index-update": true, "batch-mode": false },
      query: { "file-back-results": true },
      lint: { schedule: "periodic", checks: ["broken-links", "missing-frontmatter", "stale-index", "orphaned-pages"] },
    },
    migration: { "auto-detect-sources": false, "clean-duplicates": false, "preserve-originals": true },
    search: { engine: "index-only", "mcp-server": "" },
  },
  book: {
    domain: "book", "bundle-path": "knowledge", "sources-dir": "sources", "wiki-dir": "wiki",
    "schema-language": "auto",
    okf: { "enforce-frontmatter": true, "allowed-types": ["chapter", "character", "worldbuilding"], "auto-index": true, "auto-log": true },
    operations: {
      ingest: { "auto-cross-reference": true, "auto-index-update": true, "batch-mode": false },
      query: { "file-back-results": true },
      lint: { schedule: "on-demand", checks: ["broken-links", "missing-frontmatter", "inconsistent-naming"] },
    },
    migration: { "auto-detect-sources": false, "clean-duplicates": false, "preserve-originals": true },
    search: { engine: "index-only", "mcp-server": "" },
  },
  custom: {
    domain: "custom", "bundle-path": "knowledge", "sources-dir": "sources", "wiki-dir": "wiki",
    "schema-language": "auto",
    okf: { "enforce-frontmatter": true, "allowed-types": [], "auto-index": true, "auto-log": true },
    operations: {
      ingest: { "auto-cross-reference": true, "auto-index-update": true, "batch-mode": false },
      query: { "file-back-results": true },
      lint: { schedule: "on-demand", checks: ["broken-links", "missing-frontmatter"] },
    },
    migration: { "auto-detect-sources": false, "clean-duplicates": false, "preserve-originals": true },
    search: { engine: "index-only", "mcp-server": "" },
  },
};
const PRESETS = KNOWLEDGE_PRESETS;

async function viewProjectKnowledgeEngine() {
  const wrap = el("div");
  wrap.appendChild(el("h1", {}, ["Project — Knowledge Engine"]));
  wrap.appendChild(el("p", { class: "muted" }, [
    "Configure the opt-in Knowledge Engine bundle: schema, OKF frontmatter rules, ingest/query/lint behavior, migration safety and search.",
  ]));

  const data = await loadProject();
  const ke = (data["knowledge-engine"] && typeof data["knowledge-engine"] === "object") ? clone(data["knowledge-engine"]) : {};
  ke.okf = (ke.okf && typeof ke.okf === "object") ? ke.okf : {};
  ke.operations = (ke.operations && typeof ke.operations === "object") ? ke.operations : {};
  ke.operations.ingest = (ke.operations.ingest && typeof ke.operations.ingest === "object") ? ke.operations.ingest : {};
  ke.operations.query = (ke.operations.query && typeof ke.operations.query === "object") ? ke.operations.query : {};
  ke.operations.lint = (ke.operations.lint && typeof ke.operations.lint === "object") ? ke.operations.lint : {};
  ke.migration = (ke.migration && typeof ke.migration === "object") ? ke.migration : {};
  ke.search = (ke.search && typeof ke.search === "object") ? ke.search : {};

  const status = el("div", { class: "muted" });
  const contentWrap = el("div");

  const render = () => {
    contentWrap.replaceChildren();

    // Panel 0 — Preset Selector
    const presetPanel = el("div", { class: "panel" });
    presetPanel.appendChild(el("h2", {}, ["Domain Preset"]));
    presetPanel.appendChild(dropdownField(
      "Apply preset",
      ["", "research", "personal", "business", "book", "internal-docs", "custom"],
      "",
      (val) => {
        if (!val) return;
        const preset = KNOWLEDGE_PRESETS[val];
        if (!preset) return;
        Object.assign(ke, clone(preset));
        ke.enabled = true;
        router.navigate("/project/knowledge-engine");
      },
      { "": "(select to apply — overwrites all fields below)" },
    ));
    contentWrap.appendChild(presetPanel);

    // Panel 1 — General
    const generalPanel = el("div", { class: "panel" });
    generalPanel.appendChild(el("h2", {}, ["General"]));
    generalPanel.appendChild(checkboxField("Enabled", !!ke.enabled, (v) => { ke.enabled = v; render(); }));
    generalPanel.appendChild(dropdownField(
      "Domain",
      ["research", "personal", "business", "book", "internal-docs", "custom"],
      ke.domain || "custom",
      (v) => { ke.domain = v; },
    ));
    generalPanel.appendChild(labeledTextField("Bundle path", ke["bundle-path"] || "knowledge", (v) => { ke["bundle-path"] = v; }));
    generalPanel.appendChild(labeledTextField("Sources dir", ke["sources-dir"] || "sources", (v) => { ke["sources-dir"] = v; }));
    generalPanel.appendChild(labeledTextField("Wiki dir", ke["wiki-dir"] || "wiki", (v) => { ke["wiki-dir"] = v; }));
    generalPanel.appendChild(labeledTextField("Schema language", ke["schema-language"] || "auto", (v) => { ke["schema-language"] = v; }));
    contentWrap.appendChild(generalPanel);

    // Panel 2 — OKF
    const okfPanel = el("div", { class: "panel" });
    okfPanel.appendChild(el("h2", {}, ["OKF (Open Knowledge Format)"]));
    okfPanel.appendChild(checkboxField("Enforce frontmatter", ke.okf["enforce-frontmatter"] !== false, (v) => { ke.okf["enforce-frontmatter"] = v; }));
    okfPanel.appendChild(checkboxField("Auto-index", ke.okf["auto-index"] !== false, (v) => { ke.okf["auto-index"] = v; }));
    okfPanel.appendChild(checkboxField("Auto-log", ke.okf["auto-log"] !== false, (v) => { ke.okf["auto-log"] = v; }));
    okfPanel.appendChild(labeledTextField(
      "Allowed types (comma-separated)",
      (ke.okf["allowed-types"] || []).join(", "),
      (v) => { ke.okf["allowed-types"] = v.split(",").map(s => s.trim()).filter(Boolean); },
      "Leave empty to allow any concept type.",
    ));
    contentWrap.appendChild(okfPanel);

    // Panel 3 — Operations
    const opsPanel = el("div", { class: "panel" });
    opsPanel.appendChild(el("h2", {}, ["Operations"]));

    opsPanel.appendChild(el("h3", {}, ["Ingest"]));
    opsPanel.appendChild(checkboxField("Auto cross-reference", ke.operations.ingest["auto-cross-reference"] !== false, (v) => { ke.operations.ingest["auto-cross-reference"] = v; }));
    opsPanel.appendChild(checkboxField("Auto index update", ke.operations.ingest["auto-index-update"] !== false, (v) => { ke.operations.ingest["auto-index-update"] = v; }));
    opsPanel.appendChild(checkboxField("Batch mode", !!ke.operations.ingest["batch-mode"], (v) => { ke.operations.ingest["batch-mode"] = v; }));

    opsPanel.appendChild(el("h3", {}, ["Query"]));
    opsPanel.appendChild(checkboxField("File-back results", ke.operations.query["file-back-results"] !== false, (v) => { ke.operations.query["file-back-results"] = v; }));

    opsPanel.appendChild(el("h3", {}, ["Lint"]));
    opsPanel.appendChild(dropdownField(
      "Schedule",
      ["on-demand", "post-ingest", "periodic"],
      ke.operations.lint.schedule || "on-demand",
      (v) => { ke.operations.lint.schedule = v; },
    ));
    const lintChecks = new Set(ke.operations.lint.checks || ["broken-links", "missing-frontmatter"]);
    const checksWrap = el("div");
    for (const check of KNOWLEDGE_ALL_LINT_CHECKS) {
      checksWrap.appendChild(checkboxField(check, lintChecks.has(check), (v) => {
        if (v) { lintChecks.add(check); } else { lintChecks.delete(check); }
        ke.operations.lint.checks = [...lintChecks];
      }));
    }
    opsPanel.appendChild(checksWrap);
    contentWrap.appendChild(opsPanel);

    // Panel 4 — Migration
    const migrationPanel = el("div", { class: "panel" });
    migrationPanel.appendChild(el("h2", {}, ["Migration"]));
    migrationPanel.appendChild(el("p", { class: "muted" }, ["Migration always copies, never moves. These toggles do not start a migration by themselves."]));
    migrationPanel.appendChild(checkboxField("Auto-detect sources", !!ke.migration["auto-detect-sources"], (v) => { ke.migration["auto-detect-sources"] = v; }));
    migrationPanel.appendChild(checkboxField("Clean duplicates", !!ke.migration["clean-duplicates"], (v) => { ke.migration["clean-duplicates"] = v; }));
    migrationPanel.appendChild(checkboxField("Preserve originals", ke.migration["preserve-originals"] !== false, (v) => { ke.migration["preserve-originals"] = v; }));
    contentWrap.appendChild(migrationPanel);

    // Panel 5 — Search
    const searchPanel = el("div", { class: "panel" });
    searchPanel.appendChild(el("h2", {}, ["Search"]));
    searchPanel.appendChild(dropdownField(
      "Engine",
      ["index-only", "mcp-qmd", "custom"],
      ke.search.engine || "index-only",
      (v) => { ke.search.engine = v; render(); },
    ));
    if (ke.search.engine !== "index-only") {
      searchPanel.appendChild(labeledTextField("MCP server", ke.search["mcp-server"] || "", (v) => { ke.search["mcp-server"] = v; }));
    }
    contentWrap.appendChild(searchPanel);
  };
  render();

  wrap.appendChild(status);
  wrap.appendChild(contentWrap);

  wrap.appendChild(el("div", { class: "btn-row" }, [
    el("button", { class: "btn btn-primary", onclick: async () => {
      try {
        await saveProjectSection("knowledge-engine", ke, status);
      } catch { /* toast shown */ }
    } }, ["Save"]),
  ]));
  return wrap;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_knowledge_engine.py::test_admin_ui_has_view_project_knowledge_engine_function -v`
Expected: PASS

- [ ] **Step 5: Run the full test file to check no regressions across Tasks 1-4**

Run: `pytest tests/test_knowledge_engine.py -v`
Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add docs/ui/admin-ui.html tests/test_knowledge_engine.py
git commit -m "feat: add Knowledge Engine AdminUI view with 5 domain presets"
```

---

### Task 5: Full-suite regression check and schema preset validation

**Files:**
- None modified — verification-only task.

**Interfaces:**
- Consumes: everything from Tasks 1-4.
- Produces: confidence that the whole branch's test suite and `sync.py --validate` pass together before the final code review.

- [ ] **Step 1: Run the full project test suite**

Run: `pytest tests/ -v`
Expected: all tests PASS, no regressions in unrelated test modules.

- [ ] **Step 2: Run schema validation against a project.yaml containing each of the 6 presets**

Create a temporary test project.yaml (or extend an existing fixture in `tests/`) with `knowledge-engine` set to each preset's full field set in turn, and run:

Run: `python scripts/sync.py --dry-run --validate`
Expected: exits 0 for all 6 presets, no schema violations.

If this requires a throwaway fixture file, create it under the test's own tmp_path (pytest `tmp_path` fixture) rather than a committed file — no new fixture file should be added to the repo for this verification step.

- [ ] **Step 3: Commit (only if Step 1/2 uncovered fixes)**

If no changes were needed, skip this commit — this task is verification-only.

```bash
git add -A
git commit -m "test: verify knowledge-engine phase c schema and admin-server integration"
```
