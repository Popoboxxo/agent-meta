# Admin-UI Guide — agent-meta

> **Stand:** v0.66.0 — Phase 5 (CRUD-Endpunkte für Pipelines, Reflection Pairs, Prompt Modes + Model Mapping)
> **Frontend:** `docs/admin-ui.html` (Single-File, Vanilla JS, Zero Dependencies)
> **Backend:** `scripts/admin-server.py` (Python stdlib + PyYAML)

---

## 1. Admin-UI starten

Die Admin-UI wird via `scripts/admin-server.py` gestartet. Es gibt zwei Modi:

### Super Admin Mode

Läuft **innerhalb des agent-meta Framework-Repos** selbst. Alle Konfigurationsdateien werden editierbar.

```bash
python scripts/admin-server.py
# → http://127.0.0.1:7420
```

### Project Admin Mode

Läuft **in einem Zielprojekt** das agent-meta als Submodul (`.agent-meta/`) eingebunden hat. Nur `.meta-config/project.yaml` wird exponiert.

```bash
python .agent-meta/scripts/admin-server.py --root .
# → http://127.0.0.1:7420
```

### Sync-Integration

```bash
python scripts/sync.py --admin       # sync + Admin-UI starten
python scripts/sync.py --admin-only  # nur Admin-UI (kein sync)
```

### Flags

| Flag | Beschreibung |
|------|-------------|
| `--port 7420` | Port (Default: 7420) |
| `--host 127.0.0.1` | Loopback-Adresse |
| `--no-viz` | Ohne Viz-Dashboard/MCP-Server (leichter) |
| `--root .` | Projekt-Root (Project Admin Mode) |

> **Sicherheit:** Der Server bindet ausschließlich an Loopback-Adressen (`127.0.0.1`, `localhost`, `::1`). Die Admin-UI hat **Schreibzugriff** auf alle editierbaren Config-Dateien.

---

## 2. Seitenübersicht

Die Admin-UI bietet eine Sidebar-Navigation mit folgenden Seiten:

### 2.1 Project General

Projekt-Konfiguration: Name, Prefix, Provider, Rollen, Orchestrator-Einstellungen, tier-preset, Viz-Konfiguration.

### 2.2 Roles

Übersicht aller Rollen aus `config/role-defaults.yaml` mit Modell-Tier, Memory, Permission-Mode, Prompt-Mode-Badge und Delegationszielen.

### 2.3 Models & Pricing

Sortierbare Tabelle aller 400+ Modelle aus der Model Registry. Mit Quick-Filter-Strip nach Provider (Claude/OpenCode/GitHub/OpenAI/Google), Preis-Heatmap und Source-Badges (`[API]` / `[Overlay]` / `[Calc]`).

### 2.4 Provider Tier Mappings

Per-Provider Datalist-Filtering der Modell-Tier-Zuordnung.

### 2.5 Tier Presets

Zwei Tabs: **Resolved View** (aktuell aufgelöste Modelle) und **Edit Mappings** (direkte Modell-Inputs).

### 2.6 AI Providers

Enable/Disable pro Provider, Projekt-Tier-Override-Panel.

### 2.7 Pipelines (NEW v0.66.0)

CRUD-Oberfläche für Quality Pipelines aus `config/role-defaults.yaml` → `quality_pipelines`. Pipelines definieren Ausführungsmodi:

- `sequential`: Schritte nacheinander
- `loop`: Generator → Critic → Feedback → Generator (max N Iterationen)
- `parallel_group`: Unabhängige Agenten parallel mit BARRIER

**Endpunkte:**

| Methode | Endpunkt | Beschreibung |
|---------|----------|-------------|
| `GET` | `/api/pipelines` | Alle Pipelines lesen |
| `GET` | `/api/pipelines/{name}` | Einzelne Pipeline lesen |
| `PUT` | `/api/pipelines` | Alle Pipelines ersetzen |
| `PUT` | `/api/pipelines/{name}` | Pipeline anlegen/aktualisieren |
| `DELETE` | `/api/pipelines/{name}` | Pipeline löschen |

### 2.8 Reflection Pairs (NEW v0.66.0)

Verwaltung von Generator-Critic-Reflection-Paaren aus `config/role-defaults.yaml` → `reflection_pairs`. Jedes Pair definiert:

- `id` — Eindeutige ID (auto-generiert bei POST)
- `generator` — Generator-Rolle (z.B. `developer`)
- `critic` — Critic-Rolle (z.B. `code-reviewer`)
- `max_iterations` — Maximale Iterationen
- `enabled` — Aktiv/Inaktiv

**Endpunkte:**

| Methode | Endpunkt | Beschreibung |
|---------|----------|-------------|
| `GET` | `/api/reflection-pairs` | Liste aller Pairs |
| `GET` | `/api/reflection-pairs/{id}` | Einzelnes Pair |
| `POST` | `/api/reflection-pairs` | Neues Pair anlegen (ID auto-generiert) |
| `PUT` | `/api/reflection-pairs` | Alle Pairs ersetzen |
| `PUT` | `/api/reflection-pairs/{id}` | Pair aktualisieren |
| `DELETE` | `/api/reflection-pairs/{id}` | Pair löschen |

### 2.9 Prompt Modes (NEW v0.66.0)

Konfiguration der Prompt-Rendering-Modi pro Rolle. Liest/schreibt den `agent-prompts`-Block in `.meta-config/project.yaml`.

**Endpunkte:**

| Methode | Endpunkt | Beschreibung |
|---------|----------|-------------|
| `GET` | `/api/prompt-modes` | Aktuelle Konfiguration (`default` + `modes`) |
| `PUT` | `/api/prompt-modes` | Komplette Konfiguration ersetzen |
| `GET` | `/api/prompt-modes/roles/{role}` | Prompt-Mode einer Rolle |
| `PUT` | `/api/prompt-modes/roles/{role}` | Override setzen (`{"mode": "modern"}`) |
| `POST` | `/api/prompt-modes/roles/{role}` | Override setzen (wie PUT) |
| `DELETE` | `/api/prompt-modes/roles/{role}` | Override löschen (fällt auf `default` zurück) |

### 2.10 Model Mapping (NEW v0.66.0)

Lese-Ansicht der aufgelösten Modell-IDs pro Rolle und Provider. Die Auflösungslogik ist identisch mit der in `scripts/lib/agents.py`:

1. Prüft `project.yaml:model-overrides` (explicit override)
2. Fallback auf `role-defaults.yaml:tier` → `ai-providers.yaml:model-tiers` (role-default)
3. Fallback auf leeren String

Pro Zelle wird angezeigt:

- **Modell-ID** — die konkrete aufgelöste ID
- **Source-Badge** — `role-default`, `explicit-override`

Die Seite ist **Read-Only** — Schreib-Overrides erfolgen via:
- `/api/config/project/section` (für `model-overrides`)
- `/api/models/update` (für globale Modell-Updates)

**Endpunkt:**

| Methode | Endpunkt | Beschreibung |
|---------|----------|-------------|
| `GET` | `/api/model-mapping` | Matrix: Rolle × Provider → `{model_id, source}` |

### 2.11 Config Audit

Analysiert die aktuelle Konfiguration auf Inkonsistenzen und schlägt Korrekturen vor.

### 2.12 AI Providers Config

Super-Admin-Editor für `config/ai-providers.yaml`.

---

## 3. YAML-Formatierung

Die CRUD-Endpunkte für Pipelines und Reflection Pairs verwenden die interne Methode `_update_role_defaults_section()` in `scripts/admin-server.py`. Diese Methode arbeitet fein-granular auf Kind-Ebene:

- **Unveränderte Kinder** (einzelne Pipelines oder Reflection-Pair-Einträge) behalten ihre ursprüngliche Formatierung und Kommentare.
- **Geänderte oder neue Kinder** werden mit PyYAML neu serialisiert; deren **innere** Formatierung kann sich dabei normalisieren.
- **Kommentare und Leerzeilen außerhalb der Sektion** sowie **andere Top-Level-Sektionen** bleiben erhalten.

So bleibt das restliche `config/role-defaults.yaml` stabil, während nur das tatsächlich editierte Element neu formatiert wird.

---

## 4. Bekannte Endpunkte (Übersicht)

| Endpunkt | Methoden | Beschreibung |
|----------|----------|-------------|
| `/api/config/{key}` | GET, PUT | Generischer Config-Reader/Writer |
| `/api/config/project/section` | PUT | Partial-Update eines project.yaml-Top-Level-Keys |
| `/api/models` | GET | Model-Registry |
| `/api/models/update` | POST | Model-Crawl ausführen |
| `/api/models/exclude` | POST | Modell blacklisten |
| `/api/models/disable` | POST | Modell deaktivieren |
| `/api/models/enable` | POST | Modell aktivieren |
| `/api/pricing/update` | POST | Pricing aktualisieren |
| `/api/pricing/reset` | POST | Pricing zurücksetzen |
| `/api/ai-providers/update` | POST | AI-Provider aktualisieren |
| `/api/tier-presets/update` | POST | Tier-Presets aktualisieren |
| `/api/sync/dry-run` | POST | `sync.py --dry-run` ausführen |
| `/api/sync/run` | POST | `sync.py` ausführen |
| `/api/subserver/{name}/{action}` | POST | Viz/MCP-Server start/stop/restart |
| `/api/events` | GET | SSE-Event-Stream |
| `/api/agents/hierarchy` | GET | Rollenhierarchie |
| `/api/roles` | GET | Rollenliste |
| `/api/platforms` | GET | Plattformliste |
| `/api/providers` | GET | Providerliste |
| `/api/config-audit` | GET | Config-Audit |
| `/api/schema/project` | GET | project-config.schema.json |

---

## 5. Architektur

```
Web Browser (admin-ui.html)
       ↕ HTTP/SSE
admin-server.py (Python stdlib + PyYAML)
       ↕
Config-Manager (Backup, atomare Writes)
       ↕
File System (.meta-config/, config/)
```

**Prinzipien:**
- **Zero Dependencies** — Kein npm, kein `pip install`
- **Super Admin vs. Project Admin** — Automatische Modus-Erkennung via Dateisystem-Check (`agents/1-generic/` existiert?)
- **Backup vor Schreibzugriff** — Jeder PUT/POST/DELETE erstellt ein Backup in `config/.backup/`
- **Idempotenz** — Gleiche PUT-Requests erzeugen keine neuen Backups (Prüfung via YAML-Parse-Compare vor Write)
