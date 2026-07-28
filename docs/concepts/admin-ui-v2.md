# Admin UI v2 — Framework Defaults & Project Overrides

**Status:** Konzept  
**Version:** 0.1  
**Datum:** 2026-07-28

## Vision

Die Admin UI v2 wird zur zentralen Schaltstelle für agent-meta — sie verwaltet
**Framework-Defaults** (gelten für alle Projekte) UND zeigt **Project-Overrides**
(gelten nur für die aktuelle Projektinstanz). Jede Einstellung hat eine klare
Herkunft: Framework (agent-meta) oder Project (project.yaml).

```
┌─────────────────────────────────────────────────────┐
│  Admin UI v2                                        │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐ │
│  │ Skills   │  │ MCP      │  │ Repos & Data      │ │
│  │          │  │          │  │                   │ │
│  │ ✓ enable │  │ ✓ enable │  │ awesome-claude..  │ │
│  │ ○ disable│  │ ○ disable│  │ ○ enabled (fw)    │ │
│  │          │  │          │  │ ● active (proj)   │ │
│  └──────────┘  └──────────┘  └───────────────────┘ │
│                                                     │
│  Framework Default          Project Override        │
│  skills-registry.yaml  ←→   project.yaml            │
│  mcp-registry.yaml      →   (external-skills)       │
│  role-defaults.yaml      →   (mcp-servers)          │
│                          →   (roles)                │
└─────────────────────────────────────────────────────┘
```

## UI-Struktur

### Tabs / Sections

| Tab | Inhalt | Quelle (Framework) | Override (Project) |
|---|---|---|---|
| **Skills** | Externe Skills (enable/disable) | `skills-registry.yaml` | `project.yaml → external-skills` |
| **MCP** | MCP-Server (enable/disable) | `mcp-registry.yaml` | `project.yaml → mcp-servers` |
| **Repos** | Referenz-Repos (awesome-claude-code etc.) | `skills-registry.yaml → repos` | — (automatisch via Roles) |
| **Roles** | Agenten-Rollen (enable/disable) | `role-defaults.yaml` | `project.yaml → roles` |
| **Sync** | Live-Sync-Trigger + Log-Viewer | — | — |

### Skills-Tab

Listet alle Skills aus `skills-registry.yaml` mit:

| Feld | Quelle |
|---|---|
| Skill-Name | `skills-registry.yaml → skills.<name>` |
| Approved | `skills-registry.yaml → skills.<name>.approved` |
| Role | `skills-registry.yaml → skills.<name>.role` |
| Repo | `skills-registry.yaml → skills.<name>.repo` |
| Framework-Default | `skills-registry.yaml → skills.<name>.enabled` (neu!) |
| **Project-Override** | `project.yaml → external-skills.<name>.enabled` |
| **Effektiv** | Project-Override ?? Framework-Default |

Toggle-Logik:
```
Effektiv = project.yaml.external-skills.<name>.enabled
           ?? skills-registry.yaml.skills.<name>.enabled  (Framework-Default)
           ?? false
```

### Repos-Tab

Listet Referenz-Repos (aktuell nur `awesome-claude-code`), die keine
Skill-Einträge haben, aber von Agenten referenziert werden.

| Feld | Quelle |
|---|---|
| Repo-Name | `skills-registry.yaml → repos.<name>` |
| URL | `skills-registry.yaml → repos.<name>.repo` |
| Pinned Commit | `skills-registry.yaml → repos.<name>.pinned_commit` |
| **Framework: enabled** | `skills-registry.yaml → repos.<name>.enabled` (neu!) |
| **Project: active** | Berechnet: `agent-meta-scout ∈ roles && repo.enabled` |
| Status | `● cloned` / `○ not cloned` / `⚠ error` |

Visualisierung:
```
┌──────────────────────────────────────────────────────────┐
│ Reference Repos                                          │
│                                                          │
│  awesome-claude-code                                     │
│  ┌────────────────────────────────────────────────────┐  │
│  │ URL: github.com/hesreallyhim/awesome-claude-code   │  │
│  │ Commit: 3d8bde2 (pinned)                          │  │
│  │                                                    │  │
│  │  Framework:  [✓ enabled]  ← editierbar in UI       │  │
│  │  Project:    [● active]   ← berechnet (scout∈roles)│  │
│  │  Status:     ● cloned                               │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## Datenfluss

### Framework-Default → Project-Override → Effektiver Wert

```
skills-registry.yaml          project.yaml                 Effektiv
─────────────────────         ────────────                 ────────
skills:                       external-skills:
  foo:                          foo:
    enabled: true   ──merged──▶   enabled: false  ──────▶  false
    approved: true                                        
    role: foo-specialist                                   
```

Der effektive Wert ergibt sich aus:
1. Framework-Default (`enabled` in `skills-registry.yaml`)
2. Überschrieben durch Project-Override (`enabled` in `project.yaml → external-skills`)
3. Falls keiner gesetzt: `false` (Safety-First)

### Override-Logik im Detail

```
function effective_value(key, framework_cfg, project_cfg):
    if project_cfg has explicit key:
        return project_cfg[key]          # Projekt override
    if framework_cfg has key:
        return framework_cfg[key]         # Framework default
    return false                          # Safety
```

### Abhängigkeiten

```
awesome-claude-code enabled (fw)
    AND agent-meta-scout ∈ roles (proj)
        → Repo wird geclont

reqogniloom-change-manager enabled (fw + proj override)
    → skill wrapper agent generiert
    → Repo external/ReqogniLoom geclont
```

## Live-Sync-Integration

### Aktueller Stand

- `admin-ui.html` hat `auto-sync-on-save: true` in project.yaml
- Nach Save wird `sync.py` via `admin-server.py` ausgeführt
- Sync-Log wird in `sync.log` geschrieben

### Erweiterung v2

```
┌──────────────┐   PATCH /api/config    ┌───────────────┐
│  Admin UI    │ ──────────────────────▶ │ admin-server   │
│  (Browser)   │                         │  .py           │
└──────────────┘                         └───────┬───────┘
                                                 │
                                    ┌────────────▼───────┐
                                    │ 1. YAML schreiben   │
                                    │ 2. sync.py starten  │
                                    │ 3. Log streamen     │
                                    └────────────┬───────┘
                                                 │
                              ┌──────────────────▼──────┐
                              │ 4. Ergebnis → UI        │
                              │    ✓ 52 actions         │
                              │    ⚠ 1 warning          │
                              │    ✗ 0 errors           │
                              └─────────────────────────┘
```

### Sync-Feedback

Nach jedem Save zeigt die UI:
- Anzahl Actions / Skipped / Warnings
- Letzte 5 Log-Zeilen
- Exit-Code (0 = ok)
- Link zu vollständigem `sync.log`

## Config-Änderungen (neu in skills-registry.yaml)

```yaml
# Bisher: skills haben kein enabled-Feld → immer true wenn approved
skills:
  reqogniloom-change-manager:
    approved: true
    enabled: true          # NEU: Framework-Default
    repo: reqogniloom
    ...

# Bisher: repos haben kein enabled-Feld → hart verdrahtet
repos:
  awesome-claude-code:
    repo: https://github.com/hesreallyhim/awesome-claude-code
    enabled: true          # NEU: Framework-Default, in UI togglebar
    ...
```

## Implementierungs-Roadmap

| Phase | Was | Aufwand |
|---|---|---|
| **Phase 1** | `enabled`-Felder in YAML-Schemas + Backend-Logik | Besteht bereits (v0.90.5) |
| **Phase 2** | Admin-UI: Skills-Tab mit Framework/Project-Toggle | 1 Tag |
| **Phase 3** | Admin-UI: Repos-Tab mit Abhängigkeits-Anzeige | 0.5 Tage |
| **Phase 4** | Admin-UI: Live-Sync-Feedback (Log-Stream) | 0.5 Tage |
| **Phase 5** | Admin-UI: Role-Tab mit Tier/Model-Visualisierung | 1 Tag |

## UI-Technologie

- **Frontend:** Single HTML-File (`docs/ui/admin-ui.html`), Vanilla JS + CSS
- **Backend:** `scripts/admin-server.py` (Python stdlib, kein Flask/Django)
- **API:** REST-Endpoints unter `localhost:{admin-ui.port}`
- **Keine externen Dependencies** — bleibt stdlib-only wie der Rest von agent-meta

## Abgrenzung

- **NICHT** in Scope: Multi-Project-Management (Admin UI verwaltet immer das aktuelle Projekt)
- **NICHT** in Scope: Remote-Admin (Admin UI läuft lokal, kein Auth-Layer)
- **NICHT** in Scope: Config-Versionierung (Git übernimmt das)
