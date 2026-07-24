# Konzept: agent-meta Admin-UI — Config Surface & Workflow Editor

> Status: **Konzept-Entwurf v1.0** | 2026-06-14
> Ziel: Browser-basierte Oberfläche zur visuellen Konfiguration von agent-meta — Super Admin für das Framework-Repo, Project View für Zielrepos.

---

## 1. Vision & Zielsetzung

### Problem

Die agent-meta-Konfiguration lebt in `.meta-config/project.yaml` (264 Zeilen, ~70 Variablen, 27 Rollen, Orchestrator-Einstellungen, Viz, Quality-Pipelines, Lifecycle-Trigger) sowie in `config/role-defaults.yaml` (576 Zeilen, ~40 Rollen, Handoff-Contracts, Reflection-Pairs, 6 Pipelines), `config/ai-providers.yaml` (174 Zeilen, 5 Provider, Model-Tier-Mappings), `config/skills-registry.yaml`, `config/mcp-registry.yaml`, `config/dod-presets.yaml`, `config/rules-presets.yaml` — summiert knapp **2000 Zeilen YAML/JSON** über ein Dutzend Dateien.

Jede Änderung erfordert:
1. YAML-Syntax-Kenntnis (Schema wird nur via sync.py validiert — Fehler erst beim Sync sichtbar)
2. Wissen über Wechselwirkungen (Model-Override für Opencode + Role-Default + AI-Provider-Tier)
3. Navigation zwischen 6+ Config-Dateien
4. Manuelles Testen via `sync.py --dry-run`

### Lösung

Eine **Single-Page Web-Application** (eine HTML-Datei, kein Build-Schritt, keine externen Dependencies), die via Python-stdlib-HTTP-Server ausgeliefert wird und alle Konfigurationsoberflächen in einem einheitlichen UI bündelt — mit zwei Modi:

| Modus | Kontext | Sichtbare Konfiguration |
|-------|---------|------------------------|
| **Super Admin** | agent-meta Framework-Repo (`agents/1-generic/` existiert) | Alles: role-defaults, ai-providers, skills-registry, mcp-registry, dod-presets, rules-presets, project.yaml, Schema |
| **Project Admin** | Zielrepo (Submodul eingebunden) | Nur `project.yaml`, `extensions/`, `export.yaml`, `platform-configs/` |

### Kernprinzipien

1. **Zero Dependencies** — Kein npm, kein pip install. Python-stdlib-Backend + einzelne HTML-Datei.
2. **Schema-gesteuert** — Jedes Formular wird aus `project-config.schema.json` bzw. `role-defaults.yaml` generiert. Kein hartkodiertes UI.
3. **Realtime Validation** — JSON Schema wird clientseitig repliziert (AJV oder handgerollt), Validierung vor dem Speichern.
4. **Sync-Integration** — Änderungen triggern automatischen `sync.py --dry-run`; Erfolg zeigt Diff-Preview, Fehler zeigt Validation-Errors inline.
5. **Multi-Provider Aware** — Jede Provider-spezifische Einstellung (Model-Overrides, Provider-Options) in eigenen Tabs.

---

## 2. Best-Practice Analyse

### 2.1 Referenz-Implementierungen

| Tool | Domäne | Relevante Patterns |
|------|--------|--------------------|
| **Portainer** | Docker-Admin | Role-based views (admin vs user), YAML-Editor mit Schema-Validierung, Service-Stacks per Drag-n-Drop |
| **n8n** | Workflow-Automation | Drag-n-Drop-Node-Editor, Canvas-basierte Pipeline-Visualisierung, Credential-Management |
| **Swagger Editor** | OpenAPI | Split-Pane YAML-Editor mit Live-Preview, Schema-gesteuerte Formulare, Inline-Validation |
| **Grafana** | Observability | Dashboard-Template-Variablen, Provider-Plugin-Architektur, Panel-Drag-n-Drop |
| **VS Code Settings UI** | IDE-Konfiguration | Schema-gesteuerte Formulare aus JSON Schema, Enum-Dropdowns, Nested-Object-Editor |
| **Directus** | Headless CMS | Auto-generated Admin aus Datenmodell, Role/Permission-Matrix, Field-Level-Validation |

### 2.2 Abgeleitete Patterns für agent-meta

| Pattern | Quelle | Anwendung |
|---------|--------|-----------|
| **Schema-Driven Forms** | VS Code, Swagger | Aus `project-config.schema.json` werden alle Formularfelder generiert — kein UI-Code für neue Config-Keys |
| **Split-Pane Editor** | Swagger Editor | Links YAML-Rohdaten, rechts formularbasierte Ansicht — bidirektional synchronisiert |
| **Node-Graph Editor** | n8n, Node-RED | Agenten als Nodes, Delegation als Kanten, Pipelines als Subgraphen |
| **Provider-Tabs** | Portainer (Environments) | Claude / Opencode / Gemini / Continue als horizontale Tabs für Provider-spezifische Settings |
| **Admin/User Mode Detection** | Portainer | Dateisystem-Check (`agents/1-generic/` existiert → Super Admin) |
| **Dry-Run Preview** | Terraform Plan | Vor jedem Save: `sync.py --dry-run` → Diff als farbige Side-by-Side-Ansicht |
| **Inline Validation** | Swagger | JSON Schema wird clientseitig validiert; Fehler erscheinen direkt unter dem betroffenen Feld |

### 2.3 Anti-Patterns (bewusst vermieden)

| Anti-Pattern | Warum vermieden |
|-------------|-----------------|
| React/Vue SPA mit Build-Step | Verletzt Zero-Dependencies-Prinzip. Build-Output müsste committed werden. |
| Externe CSS-Frameworks (Bootstrap, Tailwind CDN) | Offline-Fähigkeit verloren. CSS wird inline/minimal gehalten. |
| Datenbank-Backend | agent-meta hat kein DB-Backend. State = YAML-Dateien im Git. |
| REST-API mit Framework (Flask/FastAPI) | Verletzt stdlib-only. `http.server` + manuelles Routing reicht. |
| OAuth/Auth-System | Lokales Tool auf `localhost` — kein Auth-Layer nötig. Super-Admin-Mode ist bereits durch Dateisystem-Präsenz geschützt. |

---

## 3. Architektur-Überblick

```
┌──────────────────────────────────────────────────────────────────┐
│                        BROWSER (Single Page)                      │
│  ┌─────────────────────────┐  ┌────────────────────────────────┐ │
│  │   Navigation Sidebar    │  │   Content Area (Router)         │ │
│  │                         │  │                                 │ │
│  │  📋 Project Config      │  │  ┌───────────────────────────┐  │ │
│  │  🧩 Roles & Agents      │  │  │ Form / Editor             │  │ │
│  │  🔀 Delegation Graph    │──┤  │ (schema-driven,           │  │ │
│  │  🔄 Quality Pipelines   │  │  │  tabbed per provider)     │  │ │
│  │  🏗️ Model Tiers         │  │  └───────────────────────────┘  │ │
│  │  🎯 Provider Settings   │  │                                 │ │
│  │  🧠 Memory & Permissions│  │  ┌───────────────────────────┐  │ │
│  │  🪝 Hooks & Lifecycle   │  │  │ Diff Preview              │  │ │
│  │  📊 Viz & Reporting     │  │  │ (sync.py --dry-run output)│  │ │
│  │  📝 Variables           │  │  └───────────────────────────┘  │ │
│  │  ─────────────────────  │  │                                 │ │
│  │  [SUPER ADMIN ONLY]     │  │  ┌───────────────────────────┐  │ │
│  │  ⚙️ Role Defaults       │  │  │ Validation Panel          │  │ │
│  │  🏭 Provider Registry   │  │  │ (schema errors inline)    │  │ │
│  │  🧩 Skills Registry     │  │  └───────────────────────────┘  │ │
│  │  🔌 MCP Registry        │  │                                 │ │
│  │  📐 DoD Presets         │  └────────────────────────────────┘ │
│  │  📏 Rules Presets       │                                      │
│  │  🏷️ Delegation Syntax   │                                      │
│  └─────────────────────────┘                                      │
└──────────────────────────────────────────────────────────────────┘
         │ HTTP/SSE                                ▲
         ▼                                         │
┌─────────────────────────────────────────────────────────────┐
│              PYTHON STDLIB HTTP SERVER (:8766)               │
│                                                              │
│  GET  /                    → admin-ui.html (static)          │
│  GET  /api/mode            → {mode: "super_admin"|"project"} │
│  GET  /api/config          → YAML/JSON config files          │
│  PUT  /api/config/<file>   → Write config + validate         │
│  POST /api/sync/dry-run    → sync.py --dry-run output (SSE)  │
│  POST /api/sync/run        → sync.py output (SSE)            │
│  GET  /api/schema/<file>   → JSON Schema for client-side val │
│  GET  /api/agents/hierarchy→ Agent tree for graph editor     │
│  GET  /api/events          → .meta-viz/events.jsonl (SSE)    │
│                                                              │
│  Filesystem Operations:                                      │
│  - Read/Write .meta-config/project.yaml                      │
│  - Read/Write .agent-meta/config/*.yaml (super admin only)   │
│  - Execute scripts/sync.py --dry-run                         │
│  - Tail .meta-viz/events.jsonl                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Modus-Detektion

```python
def detect_mode(project_root: Path) -> str:
    """Erkennt ob wir im agent-meta Framework-Repo oder Zielrepo sind."""
    # Prüfkette (erste zutreffende Regel gewinnt):
    indicators = [
        (project_root / "agents" / "1-generic").is_dir(),
        (project_root / ".agent-meta" / "agents" / "1-generic").is_dir(),
        (project_root / ".agent-meta").is_dir(),      # Submodul-Prüfung
    ]
    if indicators[0] or indicators[1]:
        return "super_admin"
    elif indicators[2]:
        return "project"
    return "project"  # Fallback
```

**Super Admin View** aktiviert zusätzliche Sidebar-Einträge und API-Endpoints für:
- `config/role-defaults.yaml`
- `config/ai-providers.yaml`
- `config/skills-registry.yaml`
- `config/mcp-registry.yaml`
- `config/dod-presets.yaml`
- `config/rules-presets.yaml`
- `config/delegation-syntax.yaml`
- `config/project-config.schema.json`
- `agents/1-generic/` (Template-Editor)
- `agents/2-platform/` (Plattform-Override-Editor)

**Project View** zeigt ausschließlich:
- `.meta-config/project.yaml` (alle Sektionen)
- `.meta-config/export.yaml`
- Extension-Dateien (`3-project/`)
- Platform-Configs (`platform-configs/`)

---

## 5. Super Admin View — Vollständige Funktionsübersicht

### 5.1 Role Defaults Editor (`role-defaults.yaml`)

**Tabellen-Editor** für alle ~40 Rollen:

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| Role | Text (readonly) | Rollen-ID (z.B. `orchestrator`) |
| Model | Dropdown (tier) | nano / fast / balanced / powerful / max |
| Memory | Dropdown | (leer) / project / local / user |
| Permission Mode | Dropdown | default / acceptEdits / bypassPermissions / plan |
| Tier | Dropdown | required / recommended / optional |
| Description | Textarea | Einzeilige Beschreibung |

**Detail-Panel pro Rolle (Modal/Expander):**
- Handoff-Contracts (Input-Contracts, Output-Contract, Input/Output-Schemas)
- Target-Roles (für Delegation)
- Timeout-Sekunden
- Validate-Handoff-Flag
- Workflow-Tier

**Aktionen:**
- Rolle hinzufügen (neue Zeile)
- Rolle deaktivieren (nicht löschen — nur ausblenden)
- Bulk-Edit: Alle Model-Tiers auf "balanced" setzen

### 5.2 AI Providers Editor (`ai-providers.yaml`)

**Accordion pro Provider** (Claude, Opencode, Gemini, Continue, Copilot):

| Feldgruppe | Felder |
|-----------|--------|
| Directory Paths | agents_dir, agent_ext, context_file, rules_dir, hooks_dir, commands_dir |
| Model Tiers | nano → Modell-ID, fast → ID, balanced → ID, powerful → ID, max → ID |
| Model Aliases | haiku → ID, sonnet → ID, opus → ID, fable → ID |
| MCP Config | committed-file, secrets-file, format |
| Isolation | isolation-dirs (Multi-Select) |
| Gitignore | gitignore_entries (Tag-Editor) |

### 5.3 Skills Registry (`skills-registry.yaml`)

**Tabelle** aller externen Skills:

| Spalte | Typ |
|--------|-----|
| Name | Text |
| Repo URL | Text |
| Commit (pinned) | Text |
| Approved | Toggle |
| Enabled-by-default | Toggle |

**Detail-Panel:**
- Per-Skill-Konfiguration (YAML-Editor)
- Tool-Whitelist / Blacklist

### 5.4 MCP Registry (`mcp-registry.yaml`)

**Tabelle** aller MCP-Server:

| Spalte | Typ |
|--------|-----|
| Server-ID | Text |
| Display-Name | Text |
| Transport | Dropdown (stdio / sse / streamable-http) |
| Command / URL | Text |
| Enabled-by-default | Toggle |

**Detail-Panel:**
- Tool-Whitelist (allowedTools → Tag-Editor)
- Tool-Blacklist (blockedTools → Tag-Editor)
- Environment-Variablen

### 5.5 DoD Presets (`dod-presets.yaml`)

**Matrix-Editor:**

| Preset | req-traceability | tests-required | codebase-overview | security-audit |
|--------|-----------------|----------------|-------------------|----------------|
| full | ✓ | ✓ | ✓ | ✓ |
| standard | ✓ | ✓ | — | — |
| rapid-prototyping | — | — | — | — |

### 5.6 Delegation Syntax (`delegation-syntax.yaml`)

**Provider-Matrix** mit Code-Editor pro Zelle:

| PAL Variable | Claude | Opencode | Gemini | Continue |
|-------------|--------|----------|--------|----------|
| `{{PAL_DELEGATE}}` | `@<role>` | Task-Tool | `@<role>` | `/invoke` |
| `{{PAL_FANOUT}}` | `run_in_background` | Parallel Tasks | `@all:` | ... |
| `{{PAL_PARALLEL_GROUP}}` | ... | ... | ... | ... |

### 5.7 Agent Template Editor (`agents/1-generic/`)

**Split-Pane:**
- Links: Markdown-Quelltext mit YAML-Frontmatter-Syntax-Highlighting
- Rechts: Live-Preview (gerendert)

**Frontmatter-Formular:**
- Name, Version, Description, Hint, Tools (Tag-Editor)
- Model, Memory, PermissionMode (wenn hartkodiert)

**Platzhalter-Prüfung:**
- Liste aller `{{VARIABLE}}` im Template
- Abgleich mit `build_variables()` — fehlende Variablen warnen

### 5.8 Schema Editor (`project-config.schema.json`)

**JSON-Editor** (kein Formular — Roh-JSON mit Validierung):
- Syntax-Highlighting
- Schema-Validierung (gegen JSON Schema Draft-07 Meta-Schema)
- `additionalProperties`-Checker: Neue Felder im Schema müssen in `build_variables()` registriert sein

---

## 6. Project View — Vollständige Funktionsübersicht

### 6.1 Project Identity

- **Name** (Text, required)
- **Prefix** (Text, required, max 5 Zeichen)
- **Short** (Text, required)

### 6.2 AI Providers

**Checkbox-Gruppe:** Claude ☑ Opencode ☑ Gemini ☐ Continue ☐ Copilot ☐

### 6.3 Platforms

**Tag-Editor** — Plattform-Namen als Tags (z.B. `agent-meta`, `homeassistant`, `sharkord`)

### 6.4 Roles — Drag-n-Drop Workflow Editor ★

Siehe Abschnitt 7.

### 6.5 DoD Preset & Overrides

**Dropdown:** full / standard / rapid-prototyping

**Override-Checkboxen (nur sichtbar wenn abweichend vom Preset):**
- req-traceability
- tests-required
- codebase-overview
- security-audit

### 6.6 Model Overrides — Provider-Tab-Matrix

```
[Claude] [Opencode] [Gemini] [Continue]

Role           │ Model
───────────────┼────────────────────
orchestrator   │ [balanced      ▾]
developer      │ [powerful      ▾]   ← Override (blau hinterlegt)
senior-dev     │ [max           ▾]
git            │ [fast          ▾]
...
```

- Dropdown-Optionen aus `ai-providers.yaml` model-tiers + model-aliases + direkte Modell-IDs
- Override-Indikator: Blaue Schrift = vom Default abweichend
- Reset-Button pro Zeile (zurück auf Default)

### 6.7 Memory & Permission Overrides

**Memory-Matrix:** Role × Scope (project / local / user / leer)

**Permission-Matrix:** Role × Mode (default / acceptEdits / bypassPermissions / plan)
- Visualisiert als Icon-Matrix (🔓 = bypassPermissions, 👁️ = plan, ✏️ = acceptEdits)

### 6.8 Variables Editor

**Zweispaltig:**
- Links: Variablen-Name (readonly, alphabetisch)
- Rechts: Wert (Text / Textarea / Dropdown je nach Typ)

**Typ-Erkennung:**
- Enum-Werte → Dropdown (z.B. `GIT_PLATFORM`: GitHub/GitLab/Gitea)
- Lange Strings → Textarea (z.B. `PROJECT_CONTEXT`, `EXTRA_DONTS`)
- Kurze Strings → Input
- Booleans → Toggle

**Platzhalter-Vorschau:**
- Zeigt wo `{{VARIABLE}}` in Templates verwendet wird (Read-Only-Liste)

### 6.9 Orchestrator Settings

| Feld | Typ | Default |
|------|-----|---------|
| enabled | Toggle | true |
| strict | Toggle | true |
| direct-dispatch-enabled | Toggle | true |
| handoff.protocol | Dropdown | a2a-v1 |
| handoff.validate-before-delegate | Toggle | true |
| handoff.supersession-tracking | Toggle | true |
| handoff.strict-validation | Toggle | false |
| handoff.compact-mode | Toggle | false |
| handoff.max_retries | Number (1-10) | 3 |
| handoff.human_approval_required | Toggle | false |
| handoff.protocol_routing | Dropdown | static/dynamic |
| unknown-fallback.meta-feedback | Toggle | true |
| unknown-fallback.main-chat | Toggle | true |
| unknown-fallback.ask-user | Toggle | false |

### 6.10 Viz Settings

| Feld | Typ |
|------|-----|
| enabled | Toggle |
| mode | Dropdown (off / static / dynamic / full) |
| event_log | Text (Pfad) |
| report.retention_days | Number |
| report.session_timeout_min | Number |
| debug | Toggle |
| a2a_events.* | 5× Toggle |
| server.port | Number |
| server.timeout_sec | Number |

### 6.11 Hooks

**Checkbox-Liste** aller verfügbaren Hooks:
- dod-push-check ☑
- orchestrator-guard ☑
- lifecycle-check ☐
- viz-log ☐

Nur aktivierte Hooks werden in `.claude/settings.json` registriert.

### 6.12 Lifecycle Triggers

**Event-basierte Konfiguration:**
- on-commit → Liste von Agent+Task
- on-merge → Liste
- on-release → Liste
- on-version-bump-* → Listen

**UI:** Pro Event ein Block mit "Add Agent-Task"-Button. Jeder Eintrag:
- Agent-Dropdown (alle verfügbaren Rollen)
- Task-Textarea
- Delete-Button

### 6.13 Speech Mode

**Dropdown mit Live-Vorschau:**
- full / short / childish / caveman / asozial / submissive / business / bullshit-bingo / linkedin
- Jede Option zeigt einen Beispiel-Satz im entsprechenden Stil

### 6.14 Quality Pipelines

**Pipeline-Editor** (Drag-n-Drop):

Pipelines (standard-feature, quick-fix, bugfix, concept-development) als Akkordeons.
Jede Stage als horizontale Kette von Blöcken:
```
[branch: git] → [implement: developer] → [review: loop(dev↔reviewer)] → [commit: git]
```

- Stage per Drag-n-Drop umsortieren
- Stage-Typ wählen: sequential / parallel_group / fanout / loop / conditional
- Agent pro Stage aus Dropdown
- Task-Beschreibung pro Stage
- Loop-Parameter (generator, critic, max_iterations)
- Parallel-Group: Sub-Stages hinzufügen

### 6.15 Export Settings

- Export-Typ (markdown / confluence / jira-xray / notion)
- Output-Verzeichnis
- Target-Mapping (Agent → Ziel)

### 6.16 External Skills

**Tabelle** aus `skills-registry.yaml` (read-only: approved-Flag aus Registry + enabled-Toggle aus Projekt)

### 6.17 Gitignore Settings

- local (Toggle)
- generated (Toggle)
- settings (Toggle)

### 6.18 Provider Options

**Tabs pro Provider:**
- Continue: generate-prompts, prompt-mode
- Andere: (leer / future)

### 6.19 Miscellaneous

- debug-mode (Toggle)
- max-parallel-agents (Number 1-5)
- provider-isolation (nur "disabled" als Option)
- allow-committed-secrets (Toggle)
- outcome-caching (Toggle + ttl_seconds + max_entries + invalidation)
- rules-preset (Dropdown: default / minimal / silent)

---

## 7. Drag-n-Drop Workflow Editor ★

### 7.1 Konzept

Der Workflow-Editor ersetzt die reine Rollen-Checkbox-Liste durch eine visuelle, interaktive Oberfläche, die drei Modi vereint:

| Modus | Ansicht | Zweck |
|-------|---------|-------|
| **Rollen-Auswahl** | Kachel-Grid | Welche Agenten sind im Projekt aktiv? |
| **Delegations-Graph** | Node-Edge-Canvas | Wer delegiert an wen? |
| **Pipeline-Builder** | Swimlane-Diagramm | Qualitäts-Pipelines visuell konfigurieren |

### 7.2 Rollen-Auswahl (Kachel-Grid)

```
┌─────────────────────────────────────────────────────────────┐
│  Verfügbare Rollen (40)         │  Aktive Rollen (27)        │
│                                 │                            │
│  ┌──────────┐ ┌──────────┐     │  ┌──────────┐ ┌──────────┐ │
│  │ tester   │ │ validator│     │  │orchestr..│ │developer │ │
│  │  🔵 rec  │ │  🔵 rec  │     │  │  🔴 req  │ │  🔴 req  │ │
│  └──────────┘ └──────────┘     │  └──────────┘ └──────────┘ │
│  ┌──────────┐ ┌──────────┐     │  ┌──────────┐ ┌──────────┐ │
│  │ security │ │ docker   │ →→→  │  │ git      │ │documenter│ │
│  │  ⚪ opt  │ │  ⚪ opt  │ drag │  │  🔴 req  │ │  🔵 rec  │ │
│  └──────────┘ └──────────┘     │  └──────────┘ └──────────┘ │
│  ...                            │  ...                       │
└─────────────────────────────────────────────────────────────┘
```

- Linke Spalte: Alle bekannten Rollen (aus `role-defaults.yaml`), gruppiert nach Tier
- Rechte Spalte: Aktive Rollen (aus `project.yaml → roles`)
- Drag von links nach rechts = aktivieren
- Drag von rechts nach links = deaktivieren
- Kachel-Farbe = Workflow-Tier (rot/blau/grau)
- Klick auf Kachel = Detail-Popup (Model, Memory, Permission)

### 7.3 Delegations-Graph (Canvas)

```
                   ┌──────────┐
                   │ orchestra│
                   │   tor    │
                   └────┬─────┘
          ┌─────────────┼─────────────┐
          │             │             │
     ┌────▼────┐   ┌────▼────┐   ┌───▼────┐
     │developer│   │  git    │   │feature │
     └────┬────┘   └─────────┘   └───┬────┘
          │                          │
     ┌────▼────┐              ┌──────▼──────┐
     │ tester  │              │ requirements│
     └─────────┘              └─────────────┘
```

**Interaktionen:**
- Nodes aus der Seitenleiste auf den Canvas ziehen → neue Agent-Node
- Von Node-Ausgang (rechter Rand) zu Node-Eingang (linker Rand) ziehen → Delegations-Kante
- Kante anklicken → Delegations-Typ wählen (direct / fanout / conditional)
- Node doppelklicken → Model/Memory/Permission-Override im Side-Panel
- Rechtsklick auf Node → "Als Root setzen" (für Sub-Workflows)
- Canvas zoomt/pant (Mausrad / Drag)

**Validierung in Echtzeit:**
- Zirkuläre Delegation → rote Kante + Warnung
- Orchestrator nicht aktiv → Warn-Badge
- Pflicht-Rollen (Tier=required) nicht aktiv → Warn-Badge

**Export:**
- Graph → `roles:` Array in `project.yaml`
- Graph → `_DELEGATION_MAP` in `scripts/lib/viz.py` (Super Admin)

### 7.4 Pipeline-Builder (Swimlane)

```
standard-feature
┌──────────────────────────────────────────────────────────────────┐
│  git          │  developer     │  [loop]        │  git           │
│  ┌──────────┐ │  ┌───────────┐ │  ┌──────────┐  │  ┌──────────┐  │
│  │ branch   │→│  │ implement │→│  │ review   │→ │  │ commit   │  │
│  │ Feature- │ │  │ Feature   │ │  │ dev ↔    │  │  │ Commit + │  │
│  │ Branch   │ │  │ implement.│ │  │ reviewer  │  │  │ Push + PR│  │
│  │ anlegen  │ │  │           │ │  │ max_iter:3│  │  │           │  │
│  └──────────┘ │  └───────────┘ │  └──────────┘  │  └──────────┘  │
└──────────────────────────────────────────────────────────────────┘
                                    on_error: escalate_to_orchestrator
```

- Stages als horizontale Blöcke
- Stage per Drag-n-Drop umsortieren
- Stage-Typ: `sequential` (Standard), `parallel_group` (mehrere Agenten parallel), `fanout` (verteilen), `loop` (Generator↔Critic), `conditional`
- Neue Stage: "+" Button zwischen bestehenden Stages
- Stage-Konfiguration im rechten Side-Panel

---

## 8. Technische Umsetzung

### 8.1 Backend: `scripts/admin-server.py`

```python
#!/usr/bin/env python3
"""agent-meta Admin UI Server — stdlib-only HTTP server for config management."""
# Zero dependencies beyond Python 3.8+ stdlib:
# - http.server (HTTP)
# - json (serialization)
# - yaml (PyYAML — EINZIGE externe Dependency, bereits im Projekt via sync.py)
# - subprocess (sync.py execution)
# - pathlib (file operations)
# - json (schema validation — client-seitig, Server validiert nur via sync.py)

from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json, yaml, subprocess, re, threading
```

**Routing-Tabelle:**

| Methode | Pfad | Handler | Super Admin? |
|--------|------|---------|-------------|
| GET | `/` | Serve `admin-ui.html` | Beide |
| GET | `/api/mode` | Detect mode JSON | Beide |
| GET | `/api/config/project` | Read `project.yaml` as JSON | Beide |
| PUT | `/api/config/project` | Write `project.yaml` from JSON | Beide |
| GET | `/api/config/export` | Read `export.yaml` as JSON | Beide |
| PUT | `/api/config/export` | Write `export.yaml` | Beide |
| GET | `/api/config/role-defaults` | Read `role-defaults.yaml` | SA |
| PUT | `/api/config/role-defaults` | Write `role-defaults.yaml` | SA |
| GET | `/api/config/ai-providers` | Read `ai-providers.yaml` | SA |
| PUT | `/api/config/ai-providers` | Write `ai-providers.yaml` | SA |
| GET | `/api/config/skills-registry` | Read `skills-registry.yaml` | SA |
| PUT | `/api/config/skills-registry` | Write `skills-registry.yaml` | SA |
| GET | `/api/config/mcp-registry` | Read `mcp-registry.yaml` | SA |
| PUT | `/api/config/mcp-registry` | Write `mcp-registry.yaml` | SA |
| GET | `/api/config/dod-presets` | Read `dod-presets.yaml` | SA |
| PUT | `/api/config/dod-presets` | Write `dod-presets.yaml` | SA |
| GET | `/api/config/rules-presets` | Read `rules-presets.yaml` | SA |
| GET | `/api/config/delegation-syntax` | Read `delegation-syntax.yaml` | SA |
| PUT | `/api/config/delegation-syntax` | Write `delegation-syntax.yaml` | SA |
| GET | `/api/schema/project` | Serve `project-config.schema.json` | Beide |
| GET | `/api/agents/hierarchy` | Build agent tree + delegations | Beide |
| GET | `/api/agents/template/{role}` | Read agent template markdown | SA |
| PUT | `/api/agents/template/{role}` | Write agent template markdown | SA |
| POST | `/api/sync/dry-run` | Execute `sync.py --dry-run`, return diff | Beide |
| POST | `/api/sync/run` | Execute `sync.py`, return output (SSE) | Beide |
| GET | `/api/events` | Stream `.meta-viz/events.jsonl` (SSE) | Beide |
| GET | `/api/extensions` | List `.opencode/3-project/*.md` | Beide |
| GET | `/api/extensions/{name}` | Read extension file | Beide |
| PUT | `/api/extensions/{name}` | Write extension file | Beide |

### 8.2 Frontend-Architektur

**Technologie-Stack (Zero-Dependencies):**
- Vanilla JS (ES2020+, kein Transpiler)
- CSS Custom Properties + CSS Grid/Flexbox (kein Framework)
- Fetch API (kein axios)
- Custom Element-basierte Komponenten (Web Components, kein Framework)
- HTML5 Drag-and-Drop API (keine Library)
- Canvas API für den Delegations-Graphen (2D Canvas, kein SVG/Cytoscape für MVP)
- `contenteditable` / `textarea` für Editoren

**Dateistruktur (alles in einer HTML-Datei):**
```
admin-ui.html
├── <style> (css custom properties, grid layout, dark theme)
├── <script type="module">
│   ├── StateManager        — event-bus, dirty-tracking, undo-stack
│   ├── Router              — hash-based (#/roles, #/pipelines, ...)
│   ├── API                 — fetch wrapper, SSE parser
│   ├── SchemaValidator     — client-side JSON Schema validation
│   ├── DiffRenderer        — side-by-side diff from sync.py --dry-run
│   └── Components (Custom Elements):
│       ├── <admin-sidebar>       — Navigation mit Mode-Indikator
│       ├── <config-form>         — Schema-gesteuertes Formular
│       ├── <model-override-grid> — Provider-Tab-Matrix
│       ├── <role-grid>           — Drag-n-Drop Kachel-Grid
│       ├── <delegation-canvas>   — Canvas-basierter Node-Editor
│       ├── <pipeline-editor>     — Swimlane-Diagramm-Editor
│       ├── <yaml-editor>         — Split-Pane Text/Form
│       ├── <diff-viewer>         — Side-by-Side Diff
│       ├── <validation-panel>    — Inline-Error-Liste
│       ├── <toast-notification>  — Transiente Statusmeldungen
│       └── <confirm-dialog>      — Modaler Bestätigungsdialog
└── </script>
```

### 8.3 Client-Side JSON Schema Validation

```javascript
class SchemaValidator {
    /**
     * Validiert einen Wert gegen einen JSON Schema (Draft-07 subset).
     * Kein vollständiger Validator — deckt die in project-config.schema.json
     * verwendeten Keywords ab: type, enum, pattern, minimum, maximum,
     * required, properties, additionalProperties, items, anyOf, oneOf.
     */
    validate(value, schema, path = '') {
        const errors = [];
        // type check
        if (schema.type === 'object' && typeof value !== 'object') { ... }
        // required
        if (schema.required) { ... }
        // enum
        if (schema.enum && !schema.enum.includes(value)) { ... }
        // pattern
        if (schema.pattern && !new RegExp(schema.pattern).test(value)) { ... }
        // nested object
        if (schema.properties) {
            for (const [key, propSchema] of Object.entries(schema.properties)) {
                this.validate(value[key], propSchema, `${path}.${key}`);
            }
        }
        return errors;
    }
}
```

### 8.4 Canvas-basierter Delegations-Graph

```javascript
class DelegationCanvas {
    /**
     * Rendert Agenten als Nodes und Delegationen als gerichtete Kanten
     * auf einem HTML5 Canvas-Element.
     *
     * Features:
     * - Drag-n-Drop Nodes aus der Sidebar
     * - Kanten durch Ziehen von Node-Output zu Node-Input
     * - Zoom/Pan (Mausrad, Drag auf leerer Fläche)
     * - Auto-Layout (einfache hierarchische Anordnung)
     * - Zirkuläre Abhängigkeitserkennung
     */
    constructor(canvas) {
        this.nodes = new Map();   // role → {x, y, w, h, color, tier, model, ...}
        this.edges = [];          // {from, to, type}
        this.selected = null;
        this.dragging = null;
    }

    // ... rendering, hit-testing, drag handlers
}
```

### 8.5 YAML ↔ JSON Konvertierung

Der Server sendet/empfängt JSON (einfacher für Web-UI), konvertiert aber transparent zu/von YAML auf dem Filesystem.

```python
def yaml_to_json(yaml_path: Path) -> dict:
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def json_to_yaml(yaml_path: Path, data: dict) -> None:
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
```

**Wichtig:** Kommentare in YAML gehen bei Round-Trip verloren. Lösung:
- Nur tatsächlich geänderte Keys schreiben
- Vor dem Schreiben Original-YAML parsen und Kommentar-Blöcke vor nicht-geänderten Keys erhalten
- Alternative: `ruamel.yaml` für Comment-Preserving (wäre zweite externe Dependency — Abwägung)

---

## 9. Integration in sync.py

### 9.1 CLI-Erweiterung

```bash
# Server starten
python scripts/sync.py --admin
python scripts/sync.py --admin --port 8766

# Nur UI starten (kein Sync)
python scripts/sync.py --admin-only

# Server im Hintergrund
python scripts/sync.py --admin --daemon
```

### 9.2 Hook-Registrierung

Der Admin-Server registriert sich selbst als Hook — Änderungen über die UI lösen automatisch einen Sync aus:

```yaml
# .meta-config/project.yaml (vom Admin-Server auto-gesetzt)
admin-ui:
  enabled: true
  port: 8766
  auto-sync-on-save: true   # sync.py --dry-run nach jedem Save
  watch-config: true         # Dateisystem-Watcher für externe Änderungen
```

### 9.3 Config-Schreibschutz

Sync.py prüft beim Start ob der Admin-Server läuft — wenn ja, wird vor jedem Sync ein Lock-File geprüft um Race-Conditions zu vermeiden:

```python
# In sync.py main()
admin_lock = project_root / ".meta-config" / ".admin-lock"
if admin_lock.exists():
    print("  i  Admin UI is active — config writes are managed by the UI")
    print("  i  Run 'python scripts/sync.py --admin-stop' to release the lock")
```

---

## 10. Dark Theme Design System

```css
:root {
    --bg-primary: #0f0f23;
    --bg-secondary: #1a1a2e;
    --bg-tertiary: #16213e;
    --bg-input: #0d1b2a;
    --text-primary: #eaeaea;
    --text-secondary: #a0a0b0;
    --text-muted: #6c6c80;
    --border: #2a2a4a;
    --border-focus: #4dabf7;
    --accent: #4dabf7;
    --accent-hover: #74c0fc;
    --success: #69db7c;
    --warning: #ffd43b;
    --error: #ff6b6b;
    --tier-required: #e03131;
    --tier-recommended: #1971c2;
    --tier-optional: #868e96;
    --provider-claude: #d97706;
    --provider-opencode: #6366f1;
    --provider-gemini: #4285f4;
    --provider-continue: #10b981;
    --font-mono: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace;
    --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --radius: 8px;
    --radius-sm: 4px;
    --transition: 150ms ease;
}
```

---

## 11. MVP Scope & Implementierungs-Roadmap

### Phase 1 — Static Config Viewer (READ-ONLY)

| Feature | Aufwand | Prio |
|---------|---------|------|
| `scripts/admin-server.py` (HTTP-Server, stdlib) | 2 Tage | P0 |
| `admin-ui.html` Grundgerüst (Sidebar, Routing, Dark Theme) | 1 Tag | P0 |
| GET `/api/config/*` Endpoints | 1 Tag | P0 |
| Schema-Driven Form Generator (read-only) | 2 Tage | P0 |
| Provider-Tab-Matrix (Model Overrides) | 1 Tag | P1 |
| Mode-Detection (Super Admin vs Project) | 0.5 Tage | P0 |

### Phase 2 — Edit & Validate

| Feature | Aufwand | Prio |
|---------|---------|------|
| PUT `/api/config/*` Endpoints mit Backup | 1 Tag | P0 |
| Client-Side JSON Schema Validator | 2 Tage | P0 |
| Inline-Validation-Panel | 1 Tag | P1 |
| Undo-Stack (letzte 10 Änderungen) | 1 Tag | P2 |
| Diff-Preview via `sync.py --dry-run` | 1 Tag | P0 |
| Toast-Notifications (Saved, Error, Synced) | 0.5 Tage | P1 |

### Phase 3 — Drag-n-Drop Role Editor

| Feature | Aufwand | Prio |
|---------|---------|------|
| Role-Kachel-Grid (Drag zwischen aktiv/inaktiv) | 2 Tage | P1 |
| Delegation-Canvas (Node-Graph, Grundlayout) | 3 Tage | P1 |
| Canvas-Kanten-Editor (Drag Node → Node) | 2 Tage | P1 |
| Zirkuläre Delegationserkennung | 1 Tag | P2 |
| Graph → `roles:` Array Export | 0.5 Tage | P1 |

### Phase 4 — Pipeline Builder

| Feature | Aufwand | Prio |
|---------|---------|------|
| Swimlane-Layout (horizontale Stage-Kette) | 3 Tage | P2 |
| Stage-Typen (sequential, parallel, loop, conditional) | 2 Tage | P2 |
| Pipeline → YAML Export | 1 Tag | P2 |

### Phase 5 — Super Admin Extensions

| Feature | Aufwand | Prio |
|---------|---------|------|
| Role-Defaults Tabellen-Editor | 2 Tage | P1 |
| AI-Providers Accordion-Editor | 1 Tag | P1 |
| Skills-Registry Tabellen-Editor | 1 Tag | P2 |
| MCP-Registry Tabellen-Editor | 1 Tag | P2 |
| Agent-Template Split-Pane Editor | 2 Tage | P2 |
| Delegation-Syntax Matrix-Editor | 1 Tag | P2 |

### Phase 6 — Live-Sync & Watcher

| Feature | Aufwand | Prio |
|---------|---------|------|
| Dateisystem-Watcher (polling, stdlib) | 1 Tag | P2 |
| Auto-Sync-on-Save | 0.5 Tage | P2 |
| Live-Dashboard Embed (aus bestehendem viz) | 1 Tag | P2 |
| SSE-Event-Stream für Echtzeit-Feedback | 1 Tag | P2 |

**Geschätzte Gesamtzeit: 35–40 Personentage für alle Phasen.**
**MVP (Phase 1+2): ~12 Tage — lesender + schreibender Config-Editor mit Validierung.**

---

## 12. Risiken & Offene Fragen

| Risiko | Impact | Mitigation |
|--------|--------|------------|
| YAML-Kommentar-Verlust bei Round-Trip | Mittel | `ruamel.yaml` evaluieren oder Kommentar-Blöcke manuell erhalten |
| `sync.py --dry-run` langsam bei vielen Providern | Niedrig | Caching der nicht-geänderten Provider |
| Canvas-Drag-n-Drop komplex (Touch, Accessability) | Mittel | Fallback auf Formular-Ansicht; Canvas erst ab Phase 3 |
| Race-Condition: Admin-Server + manuelles Edit | Niedrig | `.admin-lock` + Polling auf Dateiänderungen |
| Browser-Kompatibilität (Custom Elements, ES Modules) | Niedrig | Ziel: Chromium-basiert (Edge, Chrome). Firefox/WebKit später. |
| Schema-Änderungen brechen die UI | Mittel | Schema-Versionierung + Feature-Flags im Frontend |
| Multi-Repo-Szenario (Submodul in mehreren Projekten) | Hoch | **Noch offen.** Soll der Admin-Server pro Submodul-Instanz laufen? |

### Offene Fragen

1. **Submodul-Workflow:** Wenn agent-meta als Submodul in 5 Projekten eingebunden ist, läuft der Admin-Server dann im agent-meta-Repo selbst oder pro Projekt? Im Submodul ist `project.yaml` im Zielrepo, `role-defaults.yaml` im Submodul.
   - **Vorschlag:** Server läuft im Zielrepo. Super-Admin-Funktionen werden deaktiviert (Submodul ist read-only bis auf `project.yaml`-Overrides). Echter Super-Admin-Zugriff nur im agent-meta-Repo selbst.

2. **Multi-User:** Was passiert wenn zwei Tabs den Admin-Server offen haben?
   - **Vorschlag:** SSE-broadcast bei Config-Änderungen. Zweiter Tab zeigt "Config wurde extern geändert — neu laden?" Toast.

3. **Diff-Granularität:** `sync.py --dry-run` zeigt Datei-Änderungen. Reicht das oder brauchen wir Key-Level-Diffs für YAML?
   - **Vorschlag:** Key-Level-Diff als Nice-to-Have (Phase 3). Datei-Level reicht für MVP.

4. **Persistenz von UI-State:** Soll die Navigation/Sidebar-Collapse/Tab-Auswahl gespeichert werden?
   - **Vorschlag:** `localStorage` — kein Server-Roundtrip nötig.

5. **`ruamel.yaml` als Dependency:** Akzeptabel für Comment-Preserving oder bleibt es bei PyYAML?
   - **Vorschlag:** PyYAML für MVP. `ruamel.yaml` evaluieren wenn Kommentar-Verlust zum Problem wird.

---

## 13. Abgrenzung zu bestehenden Systemen

| System | Was es tut | Abgrenzung zum Admin-UI |
|--------|-----------|------------------------|
| `scripts/viz.py` | Statische Agenten-Mindmap generieren | Admin-UI nutzt viz.py für Agent-Hierarchie-Daten, ersetzt es nicht |
| `scripts/viz-logger.py` | Event-Logging (MCP/CLI/HTTP) | Admin-UI kann Events streamen (GET /api/events), ersetzt Logger nicht |
| `scripts/viz-report.py` | Reports & Live-Watch | Admin-UI kann Reports embedden, ersetzt sie nicht |
| `docs/live-dashboard.html` | Echtzeit-Agent-Graph mit Cytoscape.js | Wird im Admin-UI als eingebettetes Panel nutzbar sein (Phase 6) |
| `sync.py` | Agent-Generierung | Admin-UI ist ein Frontend für sync.py — triggert, zeigt Output, ersetzt nicht |
| CLI-Commands (`viz-toggle.md`, etc.) | Einzelne Konfigurations-Kommandos | Admin-UI bündelt alle Commands in einer Oberfläche |
