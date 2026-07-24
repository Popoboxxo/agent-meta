# Knowledge Engine — Phase C Design (AdminUI-Integration)

**Status:** Freigegeben (User-Entscheidung: Presets sofort mitnehmen)
**Vorgänger:** Phase A (Feature-Flag, Bundle-Scaffolding, gemerged), Phase B (7 `knowledge-*` Agenten + Routing, gemerged auf `main`)
**Quelle:** `docs/concepts/knowledge-engine-concept.md` §19 (AdminUI Integration) — korrigiert gegenüber tatsächlichem Codebase-Zustand

## Korrektur gegenüber Konzept-Dokument

Das Konzept-Dokument (§19.5) geht von einer bereits erweiterten `knowledge-engine`-Sektion in
`config/project-config.schema.json` aus (`okf.*`, `operations.*`, `migration.*`, `search.*`,
`sources-dir`, `wiki-dir`, `schema-language`). **Diese Felder existieren nicht** — Phase A hat nur
`enabled`, `domain`, `bundle-path` implementiert (`additionalProperties: false`). Gleichzeitig
referenziert `agents/1-generic/knowledge-querier.md` bereits `file-back-results` als Konfig-Toggle,
ohne dass es je geschrieben werden könnte (Schema würde es ablehnen). Phase C schließt diese Lücke:
Schema-Erweiterung ist Teil dieser Spec, nicht optional.

**Zweite Korrektur:** Der Sample-Code in §19.5 ruft `dropdownField(label, value, options, onChange)`
auf. Die tatsächliche Signatur in `docs/ui/admin-ui.html:4023` ist
`dropdownField(label, options, value, onChange, labels)` — Reihenfolge von `options` und `value`
vertauscht. Alle Dropdown-Aufrufe in dieser Spec verwenden die reale Signatur.

**Dritte Korrektur:** Zeilennummern im Konzept (`buildSidebar()` ~1348, `router.register`-Block
~7312) sind veraltet. Tatsächliche Fundstellen: `buildSidebar()` bei Zeile 1334 (Gruppe
"Project instance" endet bei Zeile 1364, letzter Eintrag `/project/advanced`), `router.register`-Block
bei Zeile 7385-7423, `routeMap` bei Zeile 7477-7513.

## Architektur

Vier Änderungsorte, keine neuen Dateien:

1. **`config/project-config.schema.json`** — `knowledge-engine`-Objekt um `sources-dir`, `wiki-dir`,
   `schema-language`, `okf`, `operations` (mit `ingest`/`query`/`lint`), `migration`, `search` erweitert.
2. **`scripts/admin-server.py`** — `"knowledge-engine"` zur `allowed`-Menge in `_write_project_section()`
   (Zeile 3296-3302) hinzugefügt.
3. **`docs/ui/admin-ui.html`** — Sidebar-Eintrag, Router-Registrierung, `routeMap`-Eintrag, neue
   View-Funktion `viewProjectKnowledgeEngine()`.
4. Kein Python-Code liest die neuen Felder zur Sync-Zeit (kein neuer `KNOWLEDGE_*`-Platzhalter) —
   die Agenten lesen `operations.query["file-back-results"]` etc. bereits heute direkt aus
   `.meta-config/project.yaml` als Laufzeit-Konvention (kein `{{PLACEHOLDER}}`). Phase C liefert nur
   die Schema-Validierung und die Editier-UI dafür.

## 1. Schema-Erweiterung

Ergänzung in `config/project-config.schema.json`, `properties["knowledge-engine"]["properties"]`
(nach `bundle-path`, vor dem schließenden `additionalProperties: false`):

```json
"sources-dir": {
  "type": "string",
  "default": "sources",
  "description": "Verzeichnis für Rohquellen (relativ zu bundle-path)."
},
"wiki-dir": {
  "type": "string",
  "default": "wiki",
  "description": "Verzeichnis für OKF-konforme Concept-Dokumente (relativ zu bundle-path)."
},
"schema-language": {
  "type": "string",
  "default": "auto",
  "description": "Sprache für generierte schema.md. 'auto' = DOCS_LANGUAGE des Projekts."
},
"okf": {
  "type": "object",
  "description": "Google OKF v0.1 Compliance-Einstellungen.",
  "properties": {
    "enforce-frontmatter": { "type": "boolean", "default": true },
    "allowed-types": { "type": "array", "items": { "type": "string" }, "default": [] },
    "auto-index": { "type": "boolean", "default": true },
    "auto-log": { "type": "boolean", "default": true }
  },
  "additionalProperties": false
},
"operations": {
  "type": "object",
  "description": "Karpathy-Workflow-Einstellungen pro Operation.",
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
              "contradictions", "stale-claims", "orphan-pages", "missing-concepts",
              "broken-links", "data-gaps", "missing-frontmatter", "index-staleness"
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
  "description": "knowledge-migrator Verhaltens-Einstellungen.",
  "properties": {
    "auto-detect-sources": { "type": "boolean", "default": false },
    "clean-duplicates": { "type": "boolean", "default": false },
    "preserve-originals": { "type": "boolean", "default": true }
  },
  "additionalProperties": false
},
"search": {
  "type": "object",
  "description": "Query-Engine-Auswahl für knowledge-querier.",
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

`preserve-originals` default bleibt `true` (Sicherheits-Constraint aus Phase B: Migration kopiert,
verschiebt nie — Default darf diesen Constraint nicht aufweichen).

## 2. `scripts/admin-server.py`

Zeile 3296-3302, `allowed`-Set um einen Eintrag erweitert:

```python
allowed = {
    "agent-prompts", "model-overrides", "memory-overrides", "permission-mode-overrides",
    "steps-overrides", "dod", "rules", "roles", "orchestrator", "viz", "admin-ui",
    "provider-tier-overrides", "project", "dod-preset", "rules-preset", "speech-mode",
    "tier-preset", "se-focus", "ai-providers", "platforms", "provider-options",
    "provider-isolation", "environments", "model-source-preference",
    "knowledge-engine",
}
```

## 3. AdminUI — Sidebar, Routing, Help-Mapping

**Sidebar** (`buildSidebar()`, Gruppe "Project instance", nach dem `/project/advanced`-Eintrag,
Zeile 1363):

```javascript
{ route: "/project/knowledge-engine", label: "Knowledge Engine", icon: "🧠" },
```

**Router-Registrierung** (nach Zeile 7403, `/project/advanced`):

```javascript
router.register("/project/knowledge-engine", viewProjectKnowledgeEngine);
```

**`routeMap`** (nach Zeile 7491, `"project/advanced"`):

```javascript
"project/knowledge-engine": "project_instance-knowledge_engine",
```

Kein zugehöriger Help-Text in `helpDocs` erforderlich — fehlt der Key, wird schlicht keine Hilfe
angezeigt (bestehendes Fallback-Verhalten, kein Fehler).

## 4. View-Funktion `viewProjectKnowledgeEngine()`

Eingefügt nach `viewProjectRulesOverrides()` (vor `viewProjectEnvironments()`), folgt dem
bestehenden Muster aus `viewProjectDodOverrides()` (Zeile 2479ff.: `loadProject()`,
`clone()`, `status`-Element, `saveProjectSection()`).

**Struktur — 6 Panels** (Preset-Selector + 5 Einstellungs-Panels, wie im Konzept §19.6 skizziert,
aber mit korrigierten Helper-Aufrufen):

```javascript
async function viewProjectKnowledgeEngine() {
  const wrap = el("div");
  wrap.appendChild(el("h1", {}, ["Project — Knowledge Engine"]));
  wrap.appendChild(el("p", { class: "muted" }, [
    "Karpathy LLM-Wiki + Google OKF v0.1 — persistentes Knowledge Wiki mit OKF-konformen " +
    "Concept-Dokumenten, automatischer Index-Pflege und 7 spezialisierten Agenten."
  ]));

  const data = await loadProject();
  const ke = (data["knowledge-engine"] && typeof data["knowledge-engine"] === "object")
    ? clone(data["knowledge-engine"])
    : {};

  if (!ke.okf || typeof ke.okf !== "object") ke.okf = {};
  if (!ke.operations || typeof ke.operations !== "object") ke.operations = {};
  if (!ke.operations.ingest || typeof ke.operations.ingest !== "object") ke.operations.ingest = {};
  if (!ke.operations.query || typeof ke.operations.query !== "object") ke.operations.query = {};
  if (!ke.operations.lint || typeof ke.operations.lint !== "object") ke.operations.lint = {};
  if (!ke.migration || typeof ke.migration !== "object") ke.migration = {};
  if (!ke.search || typeof ke.search !== "object") ke.search = {};

  const status = el("div", { class: "muted" }, ["Loaded from project.yaml."]);
  wrap.appendChild(status);

  const PRESETS = {
    research: {
      domain: "research", "bundle-path": "knowledge", "sources-dir": "sources",
      "wiki-dir": "wiki", "schema-language": "auto",
      okf: { "enforce-frontmatter": true, "allowed-types": [], "auto-index": true, "auto-log": true },
      operations: {
        ingest: { "auto-cross-reference": true, "auto-index-update": true, "batch-mode": false },
        query: { "file-back-results": true },
        lint: { schedule: "post-ingest", checks: [
          "contradictions", "stale-claims", "orphan-pages", "missing-concepts",
          "broken-links", "data-gaps", "missing-frontmatter", "index-staleness"
        ]}
      },
      migration: { "auto-detect-sources": true, "clean-duplicates": true, "preserve-originals": true },
      search: { engine: "index-only", "mcp-server": "" }
    },
    personal: {
      domain: "personal", "bundle-path": "knowledge", "sources-dir": "sources",
      "wiki-dir": "wiki", "schema-language": "auto",
      okf: { "enforce-frontmatter": true, "allowed-types": [], "auto-index": true, "auto-log": true },
      operations: {
        ingest: { "auto-cross-reference": true, "auto-index-update": true, "batch-mode": false },
        query: { "file-back-results": true },
        lint: { schedule: "on-demand", checks: [
          "orphan-pages", "missing-concepts", "broken-links", "missing-frontmatter"
        ]}
      },
      migration: { "auto-detect-sources": false, "clean-duplicates": false, "preserve-originals": true },
      search: { engine: "index-only", "mcp-server": "" }
    },
    business: {
      domain: "business", "bundle-path": "knowledge", "sources-dir": "sources",
      "wiki-dir": "wiki", "schema-language": "auto",
      okf: { "enforce-frontmatter": true, "allowed-types": [], "auto-index": true, "auto-log": true },
      operations: {
        ingest: { "auto-cross-reference": true, "auto-index-update": true, "batch-mode": true },
        query: { "file-back-results": true },
        lint: { schedule: "post-ingest", checks: [
          "contradictions", "stale-claims", "orphan-pages", "missing-concepts",
          "broken-links", "missing-frontmatter", "index-staleness"
        ]}
      },
      migration: { "auto-detect-sources": true, "clean-duplicates": true, "preserve-originals": true },
      search: { engine: "index-only", "mcp-server": "" }
    },
    book: {
      domain: "book", "bundle-path": "knowledge", "sources-dir": "sources",
      "wiki-dir": "wiki", "schema-language": "auto",
      okf: { "enforce-frontmatter": true, "allowed-types": [], "auto-index": true, "auto-log": true },
      operations: {
        ingest: { "auto-cross-reference": true, "auto-index-update": true, "batch-mode": false },
        query: { "file-back-results": false },
        lint: { schedule: "on-demand", checks: [
          "orphan-pages", "missing-concepts", "broken-links", "missing-frontmatter"
        ]}
      },
      migration: { "auto-detect-sources": false, "clean-duplicates": false, "preserve-originals": true },
      search: { engine: "index-only", "mcp-server": "" }
    },
    custom: {
      domain: "custom", "bundle-path": "knowledge", "sources-dir": "sources",
      "wiki-dir": "wiki", "schema-language": "auto",
      okf: { "enforce-frontmatter": false, "allowed-types": [], "auto-index": true, "auto-log": true },
      operations: {
        ingest: { "auto-cross-reference": true, "auto-index-update": true, "batch-mode": false },
        query: { "file-back-results": true },
        lint: { schedule: "on-demand", checks: ["broken-links", "missing-frontmatter"] }
      },
      migration: { "auto-detect-sources": false, "clean-duplicates": false, "preserve-originals": true },
      search: { engine: "index-only", "mcp-server": "" }
    }
  };

  // Panel 0: Preset-Selector
  const presetPanel = el("div", { class: "panel" });
  presetPanel.appendChild(el("h2", {}, ["⚡ Best-Practice Preset"]));
  presetPanel.appendChild(el("p", { class: "muted" }, [
    "Preset wählen, um alle Felder mit bewährten Voreinstellungen zu füllen. " +
    "Danach einzelne Werte anpassen und speichern."
  ]));
  const presetOptions = ["", "research", "personal", "business", "book", "custom"];
  const presetLabels = { "": "— Preset wählen —" };
  const presetField = dropdownField("Domänen-Preset", presetOptions, "", (value) => {
    const preset = PRESETS[value];
    if (!preset) return;
    Object.assign(ke, clone(preset));
    ke.enabled = true;
    router.navigate("/project/knowledge-engine");
  }, presetLabels);
  presetPanel.appendChild(presetField);
  wrap.appendChild(presetPanel);

  // Panel 1: General
  const generalPanel = el("div", { class: "panel" });
  generalPanel.appendChild(el("h2", {}, ["General"]));
  generalPanel.appendChild(checkboxField("enabled", ke.enabled ?? false, v => ke.enabled = v));
  generalPanel.appendChild(dropdownField("domain",
    ["research", "personal", "business", "book", "custom"],
    ke.domain ?? "research",
    v => ke.domain = v
  ));
  generalPanel.appendChild(labeledTextField("bundle-path", ke["bundle-path"] ?? "knowledge",
    v => ke["bundle-path"] = v));
  generalPanel.appendChild(labeledTextField("sources-dir", ke["sources-dir"] ?? "sources",
    v => ke["sources-dir"] = v));
  generalPanel.appendChild(labeledTextField("wiki-dir", ke["wiki-dir"] ?? "wiki",
    v => ke["wiki-dir"] = v));
  generalPanel.appendChild(labeledTextField("schema-language", ke["schema-language"] ?? "auto",
    v => ke["schema-language"] = v));
  wrap.appendChild(generalPanel);

  // Panel 2: OKF
  const okfPanel = el("div", { class: "panel" });
  okfPanel.appendChild(el("h2", {}, ["OKF (Open Knowledge Format)"]));
  okfPanel.appendChild(el("p", { class: "muted" }, [
    "Google OKF v0.1 — Frontmatter-Regeln, Concept-Type-Enforcement, Index-/Log-Automatik."
  ]));
  okfPanel.appendChild(checkboxField("enforce-frontmatter",
    ke.okf["enforce-frontmatter"] ?? true, v => ke.okf["enforce-frontmatter"] = v));
  okfPanel.appendChild(labeledTextField("allowed-types (kommagetrennt)",
    (ke.okf["allowed-types"] || []).join(", "),
    v => ke.okf["allowed-types"] = v ? v.split(",").map(s => s.trim()).filter(Boolean) : []
  ));
  okfPanel.appendChild(checkboxField("auto-index",
    ke.okf["auto-index"] ?? true, v => ke.okf["auto-index"] = v));
  okfPanel.appendChild(checkboxField("auto-log",
    ke.okf["auto-log"] ?? true, v => ke.okf["auto-log"] = v));
  wrap.appendChild(okfPanel);

  // Panel 3: Operations
  const opsPanel = el("div", { class: "panel" });
  opsPanel.appendChild(el("h2", {}, ["Operations (Karpathy Workflow)"]));

  opsPanel.appendChild(el("h3", { style: "margin-top:12px;" }, ["Ingest"]));
  opsPanel.appendChild(checkboxField("auto-cross-reference",
    ke.operations.ingest["auto-cross-reference"] ?? true,
    v => ke.operations.ingest["auto-cross-reference"] = v));
  opsPanel.appendChild(checkboxField("auto-index-update",
    ke.operations.ingest["auto-index-update"] ?? true,
    v => ke.operations.ingest["auto-index-update"] = v));
  opsPanel.appendChild(checkboxField("batch-mode",
    ke.operations.ingest["batch-mode"] ?? false,
    v => ke.operations.ingest["batch-mode"] = v));

  opsPanel.appendChild(el("h3", { style: "margin-top:12px;" }, ["Query"]));
  opsPanel.appendChild(checkboxField("file-back-results",
    ke.operations.query["file-back-results"] ?? true,
    v => ke.operations.query["file-back-results"] = v));

  opsPanel.appendChild(el("h3", { style: "margin-top:12px;" }, ["Lint"]));
  opsPanel.appendChild(dropdownField("schedule",
    ["on-demand", "post-ingest", "periodic"],
    ke.operations.lint.schedule ?? "on-demand",
    v => ke.operations.lint.schedule = v
  ));

  const ALL_LINT_CHECKS = [
    "contradictions", "stale-claims", "orphan-pages", "missing-concepts",
    "broken-links", "data-gaps", "missing-frontmatter", "index-staleness"
  ];
  const activeLintChecks = new Set(ke.operations.lint.checks || ["broken-links", "missing-frontmatter"]);
  opsPanel.appendChild(el("label", { class: "field-label", style: "margin-top:8px;" },
    ["Aktive Lint-Checks:"]));
  ALL_LINT_CHECKS.forEach(check => {
    opsPanel.appendChild(checkboxField(check, activeLintChecks.has(check), v => {
      if (v) activeLintChecks.add(check); else activeLintChecks.delete(check);
      ke.operations.lint.checks = [...activeLintChecks];
    }));
  });
  wrap.appendChild(opsPanel);

  // Panel 4: Migration
  const migPanel = el("div", { class: "panel" });
  migPanel.appendChild(el("h2", {}, ["Migration"]));
  migPanel.appendChild(el("p", { class: "muted" }, [
    "Vorhandene docs/ scannen und OKF-konform ins Wiki migrieren (knowledge-migrator)."
  ]));
  migPanel.appendChild(checkboxField("auto-detect-sources",
    ke.migration["auto-detect-sources"] ?? false, v => ke.migration["auto-detect-sources"] = v));
  migPanel.appendChild(checkboxField("clean-duplicates",
    ke.migration["clean-duplicates"] ?? false, v => ke.migration["clean-duplicates"] = v));
  migPanel.appendChild(checkboxField("preserve-originals",
    ke.migration["preserve-originals"] ?? true, v => ke.migration["preserve-originals"] = v));
  wrap.appendChild(migPanel);

  // Panel 5: Search
  const searchPanel = el("div", { class: "panel" });
  searchPanel.appendChild(el("h2", {}, ["Search"]));
  searchPanel.appendChild(dropdownField("engine",
    ["index-only", "mcp-qmd", "custom"],
    ke.search.engine ?? "index-only",
    v => ke.search.engine = v
  ));
  searchPanel.appendChild(labeledTextField("mcp-server",
    ke.search["mcp-server"] ?? "",
    v => ke.search["mcp-server"] = v));
  wrap.appendChild(searchPanel);

  // Save
  wrap.appendChild(el("div", { class: "btn-row" }, [
    el("button", { class: "btn btn-primary", onclick: async () => {
      try {
        await saveProjectSection("knowledge-engine", ke, status);
      } catch { /* toast handles error */ }
    }}, ["Save"]),
  ]));

  return wrap;
}
```

**Abweichungen gegenüber Konzept §19.5 (bewusst):**
- Kein `Dry-run`-Button — es gibt keine `runDryRun()`-Funktion, die für Knowledge-Engine-Vorschau
  ausgelegt wäre (die bestehende `runDryRun()` bei Zeile 1591 ist generischer Sync-Dry-Run, nicht
  Knowledge-Engine-spezifisch). Out of scope für Phase C; ggf. spätere Erweiterung.
- Preset-Dropdown nutzt die reale `dropdownField(label, options, value, onChange, labels)`-Signatur
  statt des im Konzept verwendeten (falschen) Aufrufs.
- Migrations-Defaults `auto-detect-sources`/`clean-duplicates` als `false` (statt `true` im
  Konzept-Fallback) — konsistent mit dem Schema-Default oben und dem Phase-B-Hard-Constraint
  "Migration startet nur nach expliziter User-Freigabe", nicht automatisch.

## Fehlerbehandlung

- Fehlt `data["knowledge-engine"]` komplett (Feature nie aktiviert) → `ke = {}`, alle Panels
  rendern mit Defaults, `enabled` Checkbox ist aus. Erstes Speichern schreibt vollständige Struktur.
- Preset-Auswahl überschreibt bestehende Werte vollständig (`Object.assign`) — kein Merge auf
  Feld-Ebene. Das ist gewolltes Verhalten (Preset = klarer Reset), wie im Konzept vorgesehen.
- Schema-Validierung (`additionalProperties: false` auf jeder Ebene) verhindert, dass unbekannte
  Felder aus einem veralteten Client-Zustand persistiert werden.

## Testing

- Schema-Test: `python scripts/sync.py --dry-run --validate` mit allen 5 Presets als
  `knowledge-engine`-Sektion in einer Test-`project.yaml` → keine Validierungsfehler.
- `admin-server.py`-Test: `PUT /api/config/project/section` mit `section: "knowledge-engine"` wird
  akzeptiert (vorher: `ValueError: section not allowed`).
- Kein Browser-/E2E-Test in dieser Spec (Out of Scope — `admin-ui.html` hat keine bestehende
  JS-Testsuite; Konsistenz mit dem restlichen Projekt, das AdminUI-Views manuell statt automatisiert
  testet).

## Out of Scope (Phase C)

- Dry-Run-Vorschau für Knowledge-Engine-Migration/-Ingest (eigene Funktion, kein bestehender Hook)
- Automatisierte Browser-Tests für die neue View (kein Präzedenzfall im Projekt)
- Phase D (`config/knowledge-presets.yaml` als eigene Datei, Export/MCP-Registry-Erweiterungen) —
  weiterhin deferred, nur bei Bedarf
