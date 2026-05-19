# MCP Agent Provisioning — Architektur-Konzept

> **Erstellt:** 2026-05-17 | **Ziel:** Machbares Konzept für zentralisiertes MCP-Agent-Provisioning über alle Provider

---

## 1. Problemstellung & Ziel

### Status Quo

Das MCP-Framework von agent-meta generiert bereits:

| Artefakt | Mechanismus | Beispiel |
|----------|-------------|---------|
| Provider-Konfiguration | `mcp.py` → `settings.json` / `opencode.json` / `config.yaml` | `${MCP_HA_URL}` als Env-Ref |
| MCP-Rules | `mcp.py` → `mcp-home-assistant.md` | Tool-Allow/Block-Listen |
| Secrets-Template | `mcp.py` → `secrets.local.yaml` | `MCP_HA_URL: ""` |
| Plattform-MCP-Bundles | `rules/2-platform/<platform>-mcp.yaml` | `homeassistant-mcp.yaml` aktiviert HA+InfluxDB |

**Was fehlt:** Es gibt keine automatisch generierten **Agenten** für MCP-Server.
Plattform-Agenten wie `homeassistant-developer.md` enthalten MCP-Wissen, aber das ist manuell gepflegt und nicht aus der Registry abgeleitet.

### Ziel

Ein System, das aus **einer zentralen Registry** (`mcp-registry.yaml`) automatisch für alle Provider generiert:

1. **MCP-Server-Konfiguration** (existiert)
2. **MCP-Rules** (existiert)
3. **MCP-Agenten** (NEU) — spezialisierte Agenten, die wissen wie sie den jeweiligen MCP-Server nutzen

Dabei:
- Generische Aspekte kommen aus `1-generic/_mcp-agent.md` (Templating)
- Server-spezifische Aspekte kommen aus `mcp-registry.yaml` (Agent-Definition)
- Plattform-spezifische Aspekte kommen aus `2-platform/<platform>-mcp-agents.yaml` (Bundles)
- Der Anwender konfiguriert via `mcp-servers: [...]` in `project.yaml` eine Auswahlliste

---

## 2. Datenmodell: MCP Registry erweitert

### 2.1 Neues Feld `agent` in `mcp-registry.yaml`

```yaml
# config/mcp-registry.yaml (Auszug)
mcp-servers:

  home-assistant:
    description: "Home Assistant real-time device status, sensors, datetime and read-only data"
    category: iot
    enabled-by-default: true
    tools:
      allowed: [GetLiveContext, GetDateTime, todo_get_items]
      blocked: [HassTurnOn, HassTurnOff, HassLightSet, HassCallService, ...]
    agent-hint: |
      Primäres Tool: GetLiveContext für Echtzeit-Status.
      Schreibende Operationen sind ABSOLUT VERBOTEN.
    connection:
      type: sse
      url: "{{MCP_HA_URL}}/api/mcp_server/sse"
      headers:
        Authorization: "Bearer {{MCP_HA_TOKEN}}"
    secrets: [MCP_HA_URL, MCP_HA_TOKEN]

    # ═══════════════════ NEU ═══════════════════
    agent:
      enabled: true                          # false = kein Agent für diesen Server
      role: "mcp-home-assistant"             # Rollen-Name (muss mit mcp- beginnen)
      description: >-
        Home Assistant MCP Agent — Echtzeit-Sensor-Daten, Gerätestatus und
        Datetime-Informationen über das MCP-Protokoll abrufen und interpretieren.
      hint: "HA via MCP: Sensordaten, Gerätestatus, Echtzeit-Kontext lesen"
      tier: balanced                         # Model-Tier für diesen Agenten
      memory: ""                             # Memory-Scope (leer = kein Gedächtnis)
      tools:                                 # Tools die der Agent verwenden darf
        - Bash
        - Read
        - Glob
        - Grep
      body: |                                # Server-spezifischer Agent-Body
        ## Home Assistant MCP — Arbeitsweise

        Du bist der spezialisierte MCP-Agent für Home Assistant (HA).
        Dein Zugang erfolgt ausschließlich read-only über MCP.

        ### Primäre Werkzeuge

        | Tool | Verwendung |
        |------|-----------|
        | `GetLiveContext` | Primäres Tool — liefert Echtzeit-Status aller Geräte, Sensoren, Areas |
        | `GetDateTime` | Aktuelles Datum/Uhrzeit vom HA-Server |
        | `todo_get_items` | Todo-Listen nur lesen (Shopping-Liste, etc.) |

        ### Daten-Hierarchie

        Bei Datenabfragen immer diese Reihenfolge:
        1. **MCP GetLiveContext** — Echtzeit, aktuellster Stand
        2. **InfluxDB Flux-Query** — historische Trends (wenn verfügbar)
        3. **CSV-Export** — Entitäts-Metadaten (falls `hass_entities.csv` existiert)
        4. **YAML-Konfiguration** — statische Konfigurationswerte

        ### Typische Einsätze

        - "Welche Temperatur hat das Wohnzimmer?"
        - "Welche Geräte sind gerade an?"
        - "Wann wurde der Bewegungsmelder zuletzt ausgelöst?"
        - "Zeig mir alle Entitäten im Bereich Küche"

        ### Integration mit anderen Agenten

        - **developer**: Du lieferst Daten, der developer baut darauf Automatisierungen
        - **log-analyzer**: Bei Anomalien in Zeitreihen → delegieren
        - **orchestrator**: Wird dich für Status-Abfragen im Kontext von Tasks einsetzen

        ### {{platform.homeassistant.notify_group}} und andere Platzhalter

        Plattform-Variablen aus `platform-configs/homeassistant.defaults.yaml`
        werden bei der Generierung substituiert.

  influxdb:
    description: "InfluxDB time-series database for historical trends and analysis via Flux"
    category: database
    enabled-by-default: false
    tools:
      allowed: [query]
      blocked: [write, create_bucket, delete_bucket, update_retention, delete_measurement]
    connection:
      type: stdio
      command: npx
      args: ["-y", "influxdb-mcp-server"]
      env:
        INFLUXDB_URL: "{{MCP_INFLUXDB_URL}}"
        INFLUXDB_TOKEN: "{{MCP_INFLUXDB_TOKEN}}"
        INFLUXDB_ORG: "{{MCP_INFLUXDB_ORG}}"
        INFLUXDB_BUCKET: "{{MCP_INFLUXDB_BUCKET}}"
    secrets: [MCP_INFLUXDB_URL, MCP_INFLUXDB_TOKEN, MCP_INFLUXDB_ORG, MCP_INFLUXDB_BUCKET]

    # ═══════════════════ NEU ═══════════════════
    agent:
      enabled: true
      role: "mcp-influxdb"
      description: >-
        InfluxDB MCP Agent — historische Zeitreihendaten analysieren,
        Trends erkennen und Flux-Queries für Dashboards und Berichte erstellen.
      hint: "InfluxDB via MCP: Zeitreihen, Trends, Flux-Queries (read-only)"
      tier: balanced
      memory: ""
      tools:
        - Bash
        - Read
        - Glob
        - Grep
      body: |
        ## InfluxDB MCP — Arbeitsweise

        Du bist der spezialisierte MCP-Agent für InfluxDB.
        Dein Zugang erfolgt ausschließlich read-only über Flux-Queries.

        ### Verbindungsdaten

        - **Bucket:** `{{MCP_INFLUXDB_BUCKET}}` (aus secrets.local.yaml)
        - **Organisation:** `{{MCP_INFLUXDB_ORG}}`
        - **Measurement-Schema:** Einheiten-basiert (z.B. "W", "°C", "kWh")

        ### Flux-Query Patterns

        ```flux
        // Letzte 24h Temperatur
        from(bucket: "{{MCP_INFLUXDB_BUCKET}}")
          |> range(start: -24h)
          |> filter(fn: (r) => r._measurement == "°C")
          |> filter(fn: (r) => r.entity_id == "sensor.wohnzimmer_temp")
          |> aggregateWindow(every: 15m, fn: mean)
        ```

        ### Typische Einsätze

        - "Wie hat sich der Stromverbrauch diese Woche entwickelt?"
        - "Gab es Temperatur-Spitzen gestern Nacht?"
        - "Vergleiche den Energieverbrauch Januar vs. Februar"
        - "Welcher Sensor liefert die meisten Ausreißer?"

        ### Integration mit anderen Agenten

        - **developer**: Du lieferst Trend-Daten für Optimierungen und Schwellwerte
        - **log-analyzer**: Bei Auffälligkeiten in Zeitreihen → Übergabe der Query-Ergebnisse
        - **documenter**: Du kannst Daten für Berichte und Dashboards aufbereiten
```

### 2.2 Schema-Definition für `agent` Block

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `agent.enabled` | bool | ja | `false` = kein Agent für diesen Server generieren |
| `agent.role` | string | ja | Rollen-Name, Präfix `mcp-` + server-name |
| `agent.description` | string | ja | Agent-Beschreibung (erscheint in Agent-Tabelle) |
| `agent.hint` | string | ja | Kurzhinweis (erscheint in AGENT_HINTS) |
| `agent.tier` | string | ja | Model-Tier (nano/fast/balanced/powerful/max) |
| `agent.memory` | string | nein | Memory-Scope (`""` = kein Memory) |
| `agent.tools` | list | ja | Erlaubte Tools für diesen Agenten |
| `agent.body` | string | ja | Markdown-Body mit server-spezifischen Anweisungen |

---

## 3. Generisches MCP-Agent-Template

### 3.1 Datei: `agents/1-generic/_mcp-agent.md`

```markdown
---
name: template-mcp-agent
version: "1.0.0"
description: "MCP-Agent — generische Basis für alle MCP-Server-Agenten. Wird von sync.py pro MCP-Server instanziiert."
hint: "MCP: {{MCP_SERVER_HINT}}"
tools:
  {{MCP_SERVER_TOOLS}}
---

# MCP: {{MCP_SERVER_NAME}}

> **Generiert aus `config/mcp-registry.yaml` — nicht manuell bearbeiten.**
> Server: `{{MCP_SERVER_ROLE}}` | Kategorie: `{{MCP_SERVER_CATEGORY}}`

Du bist ein spezialisierter MCP-Agent für **{{MCP_SERVER_NAME}}**.
Dein gesamter Zugriff auf diesen Dienst erfolgt über das MCP-Protokoll.

{{MCP_SERVER_DESCRIPTION}}

---

{{MCP_SERVER_BODY}}

---

## Sicherheitsrichtlinien (ABSOLUT)

- **NUR LESENDE OPERATIONEN** — keine schreibenden, löschenden oder konfigurierenden Aktionen
- Keine Secrets, Tokens oder URLs in Antworten ausgeben
- Bei Unsicherheit: nachfragen, nicht raten
- MCP-Verbindungsfehler: melden und alternative Datenquellen vorschlagen

## Delegation

| Situation | Delegieren an |
|-----------|---------------|
| Daten zeigen Anomalien | `log-analyzer` |
| Daten sollen visualisiert werden | `documenter` |
| Implementierung auf Basis der Daten | `developer` |
| Komplexe Multi-Server-Abfrage | `orchestrator` |

## Sprache

Kommunikation mit dem Nutzer → Deutsch.
Daten, Abfragen, technische Begriffe → Englisch (Original).

---

*Generiert von agent-meta v{{AGENT_META_VERSION}} — `{{AGENT_META_DATE}}`*
```

### 3.2 Platzhalter-Übersicht

| Platzhalter | Quelle | Beispiel |
|-------------|--------|---------|
| `{{MCP_SERVER_NAME}}` | `mcp-registry.yaml` → server-key | `home-assistant` |
| `{{MCP_SERVER_ROLE}}` | `agent.role` | `mcp-home-assistant` |
| `{{MCP_SERVER_DESCRIPTION}}` | `agent.description` | `Home Assistant MCP Agent — ...` |
| `{{MCP_SERVER_HINT}}` | `agent.hint` | `HA via MCP: Sensordaten, ...` |
| `{{MCP_SERVER_CATEGORY}}` | `category` | `iot` |
| `{{MCP_SERVER_TOOLS}}` | `agent.tools` (YAML-Liste) | `- Bash\n- Read\n- ...` |
| `{{MCP_SERVER_BODY}}` | `agent.body` | Server-spezifischer Markdown |
| `{{AGENT_META_VERSION}}` | `VERSION`-Datei | `0.41.0` |
| `{{AGENT_META_DATE}}` | Heutiges Datum | `2026-05-17` |

---

## 4. Plattform-MCP-Agent-Bundles

### 4.1 Konzept

Plattformen können vordefinieren, welche MCP-Agenten automatisch aktiviert werden.
Analog zu `rules/2-platform/<platform>-mcp.yaml` für Server-Konfigurationen.

### 4.2 Datei: `agents/2-platform/<platform>-mcp-agents.yaml`

```yaml
# agents/2-platform/homeassistant-mcp-agents.yaml
platform: homeassistant

# Definiert welche MCP-Agenten für diese Plattform automatisch generiert werden.
# Referenziert Einträge aus config/mcp-registry.yaml (agent.role).
# sync.py generiert diese Agenten für alle Projekte mit platforms: [homeassistant].

mcp-agents:
  - mcp-home-assistant
  - mcp-influxdb
```

### 4.3 Plattform-Agent-Overrides

Zusätzlich kann eine Plattform Agent-Overrides definieren, die Werte aus der Registry überschreiben:

```yaml
# agents/2-platform/homeassistant-mcp-agents.yaml (erweitert)
platform: homeassistant

mcp-agents:
  - mcp-home-assistant
  - mcp-influxdb

# Plattform-spezifische Overrides für MCP-Agenten
# Überschreibt Felder aus der mcp-registry.yaml agent-Definition
agent-overrides:
  mcp-home-assistant:
    hint: "HA via MCP: Sensordaten, Gerätestatus, Echtzeit-Kontext — Home Assistant Power-User Setup"
    body: |
      ## Home Assistant MCP — Arbeitsweise

      Du arbeitest in einem **Power-User Home Assistant Setup** mit:
      - Proxmox/Unraid Virtualisierung
      - Zigbee2MQTT (nicht ZHA)
      - InfluxDB für Langzeit-Trends

      ### Daten-Hierarchie

      1. **MCP GetLiveContext** — Echtzeit
      2. **InfluxDB Flux-Query** — historisch (wenn `mcp-influxdb` Agent verfügbar)
      3. **CSV-Export** (`hass_entities.csv`) — Entitäts-Metadaten
      4. **YAML-Konfiguration** — statische Werte aus Packages

      ### Notification-Kontext

      Notification-Gruppen:
      - Standard: `{{platform.homeassistant.notify_group}}`
      - Admin: `{{platform.homeassistant.notify_admin_group}}`

      Debug-Toggle: `{{platform.homeassistant.debug_sensor}}`
```

### 4.4 Override-Semantik

Die Auflösung erfolgt in dieser Reihenfolge (später überschreibt früher):

```
mcp-registry.yaml agent.body  →  platform bundle agent-overrides.<role>.body  →  .meta-config/project.yaml mcp-agent-overrides
```

Frontmatter-Felder (`hint`, `description`, `tier`, `memory`, `tools`) werden einzeln überschrieben.
`body` wird als Ganzes ersetzt (nicht gemerged).

---

## 5. Anwender-Konfiguration

### 5.1 `project.yaml` — MCP-Agenten auswählen

```yaml
# .meta-config/project.yaml (Auszug)

# MCP-Server aktivieren (existiert bereits):
mcp-servers:
  - home-assistant
  - influxdb

# MCP-Agenten (NEU — optional):
# Leer oder nicht gesetzt = alle Agenten für aktive MCP-Server generieren
# Explizite Liste = nur diese MCP-Agenten generieren (überschreibt Auto-Generierung)
mcp-agents:
  - mcp-home-assistant
  - mcp-influxdb

# MCP-Agent-Overrides (NEU — optional):
# Projekt-spezifische Anpassungen der Agent-Definitionen
mcp-agent-overrides:
  mcp-influxdb:
    tier: powerful                      # Höhere Tier für komplexe Flux-Analysen
    memory: project                     # Session-übergreifendes Gedächtnis
    body: |
      ## InfluxDB MCP — Arbeitsweise (Projekt-spezifisch)

      Du arbeitest mit folgender Umgebung:
      - Home Assistant als primäre Datenquelle
      - Measurement-Schema: `{{platform.homeassistant.influxdb_measurement_schema}}`
      - Zeitzone: `{{platform.homeassistant.influxdb_timezone}}`

      ### Projekt-spezifische Queries

      ```flux
      // Energieverbrauch aktueller Monat
      from(bucket: "{{MCP_INFLUXDB_BUCKET}}")
        |> range(start: -30d)
        |> filter(fn: (r) => r._measurement == "kWh")
        |> filter(fn: (r) => r.entity_id == "sensor.haus_energie_total")
        |> aggregateWindow(every: 1d, fn: sum)
      ```

# Rollen (existiert bereits):
# MCP-Agenten werden automatisch in die Rollen-Tabelle aufgenommen
# sobald ihr zugehöriger MCP-Server aktiv ist.
# Kein manuelles Hinzufügen zu 'roles' nötig.
roles:
  - orchestrator
  - developer
  - # mcp-home-assistant und mcp-influxdb werden automatisch ergänzt
```

### 5.2 Verhalten

| Szenario | MCP-Agenten generiert? |
|----------|----------------------|
| `mcp-servers: [home-assistant]` + kein `mcp-agents` | Ja, alle Agenten mit `agent.enabled: true` aus der Registry |
| `mcp-servers: [home-assistant, influxdb]` + `mcp-agents: [mcp-home-assistant]` | Nur `mcp-home-assistant` |
| `mcp-servers: [home-assistant]` + `mcp-agents: []` | Keine MCP-Agenten (explizit deaktiviert) |
| Server hat `agent.enabled: false` in Registry | Agent wird nie generiert |
| Server ist nicht in `mcp-servers`, aber Plattform-Bundle aktiviert ihn | Agent wird generiert (weil Server aktiv) |

---

## 6. Generierungs-Pipeline

### 6.1 Erweiterung von `sync.py`

Neuer Schritt in der Per-Provider-Loop (nach `sync_agents_for_provider()`):

```python
# sync.py — main() per-provider loop (Auszug)

# 13a. MCP Agenten generieren (NEU — nach normalen Agenten)
sync_mcp_agents_for_provider(
    agent_meta_root, project_root, config, provider_config,
    log, args.dry_run, provider,
)
```

### 6.2 Neue Funktion in `scripts/lib/mcp.py`

```python
def generate_mcp_agents(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    provider_config: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
) -> None:
    """Generate MCP agent files from registry for all active MCP servers.

    For each active MCP server with agent.enabled == true:
      1. Load generic template from agents/1-generic/_mcp-agent.md
      2. Merge server-specific agent definition from mcp-registry.yaml
      3. Apply platform overrides from agents/2-platform/<platform>-mcp-agents.yaml
      4. Apply project overrides from .meta-config/project.yaml (mcp-agent-overrides)
      5. Substitute {{MCP_*}} placeholders
      6. Substitute {{platform.*}} placeholders
      7. Apply provider-specific frontmatter transformation
      8. Write to provider agents directory
    """
    registry = load_mcp_registry(agent_meta_root)
    if not registry:
        return

    active_servers = resolve_active_mcp_servers(config, agent_meta_root)
    if not active_servers:
        return

    # Load generic template
    generic_template_path = agent_meta_root / "agents" / "1-generic" / "_mcp-agent.md"
    if not generic_template_path.exists():
        return
    generic_template = generic_template_path.read_text(encoding="utf-8")

    # Resolve active MCP agent list
    active_agents = resolve_active_mcp_agents(config, active_servers, registry, agent_meta_root)

    pc = provider_config.get(provider, {})
    agents_dir = project_root / pc.get("agents_dir", ".claude/agents")

    for agent_role in active_agents:
        # ... generate agent file ...
```

### 6.3 `resolve_active_mcp_agents()` Logik

```python
def resolve_active_mcp_agents(
    config: dict,
    active_servers: list[str],
    registry: dict,
    agent_meta_root: Path,
) -> list[str]:
    """Determine which MCP agents to generate.

    1. Collect candidates: every active server with agent.enabled == true
    2. Platform bundles: agents/2-platform/<platform>-mcp-agents.yaml
    3. User filter: mcp-agents in project.yaml (empty = all, list = filter)
    """
    candidates: dict[str, dict] = {}

    # From active servers
    for server_name in active_servers:
        server_def = registry.get(server_name, {})
        agent_def = server_def.get("agent", {})
        if agent_def.get("enabled", False):
            candidates[agent_def["role"]] = {
                "server": server_name,
                "source": f"mcp-registry/{server_name}",
                "agent_def": agent_def,
            }

    # From platform bundles
    platform_dir = agent_meta_root / "agents" / "2-platform"
    for platform in config.get("platforms", []):
        bundle_path = platform_dir / f"{platform}-mcp-agents.yaml"
        if not bundle_path.exists():
            continue
        data, _ = _load_yaml_or_json(bundle_path)
        for agent_role in (data or {}).get("mcp-agents", []):
            if agent_role not in candidates:
                # Agent from platform bundle without server — warn
                log.warn(f"mcp-agent: '{agent_role}' in platform bundle has no active server")
                continue

    # User filter
    user_agents = config.get("mcp-agents")
    if user_agents is not None:
        # Explicit list → filter
        return [r for r in user_agents if r in candidates]
    else:
        # Auto → all candidates
        return list(candidates.keys())
```

### 6.4 Provider-spezifische Transformation

MCP-Agenten durchlaufen die gleiche Provider-Transformation wie normale Agenten:

| Provider | Frontmatter-Transformation |
|----------|---------------------------|
| **Claude** | `name`, `description`, `model`, `memory`, `permissionMode`, `tools`, `generated-from` |
| **Opencode** | `name`, `description`, `mode: subagent`, `model`, `generated-from` |
| **Gemini** | `name`, `description`, `model`, `tools`, `generated-from` |
| **Continue** | `name`, `description`, `alwaysApply: false` |

Model-Tier-Auflösung über `role-defaults.yaml`-analogen Mechanismus, aber mit dem `agent.tier` aus der Registry als Default.

---

## 7. Integration in das bestehende Agenten-Ökosystem

### 7.1 Orchestrator-Tabelle

MCP-Agenten erscheinen automatisch in der `{{AGENT_TABLE}}` des Orchestrators:

```markdown
| Agent | Zuständigkeit |
|-------|--------------|
| `orchestrator` | Einstiegspunkt für alle Entwicklungsaufgaben |
| `developer` | Feature-Implementierung und Bugfixes |
| `mcp-home-assistant` | HA via MCP: Sensordaten, Gerätestatus, Echtzeit-Kontext lesen |
| `mcp-influxdb` | InfluxDB via MCP: Zeitreihen, Trends, Flux-Queries (read-only) |
| ... | ... |
```

### 7.2 Orchestrator-MCP-Routing

Der Orchestrator erhält (via generischem Template oder Context) MCP-Routing-Regeln:

```markdown
## MCP-Routing

| Nutzer-Frage beginnt mit... | Delegieren an |
|-----------------------------|---------------|
| "Temperatur", "Status von", "Welche Geräte" | `mcp-home-assistant` |
| "Verbrauch", "Trend", "Historie", "Vergleich" | `mcp-influxdb` |
| "Fehler in", "Warum ist" (Log-bezogen) | `log-analyzer` (kann MCP-Agenten hinzuziehen) |
```

### 7.3 Plattform-Agenten nutzen MCP-Agenten

Plattform-Agenten wie `homeassistant-developer.md` können MCP-Agenten referenzieren:

```markdown
## Delegation (erweitert)

| Situation | Delegieren an |
|-----------|---------------|
| Echtzeit-Daten lesen | `mcp-home-assistant` |
| Historische Trends analysieren | `mcp-influxdb` |
| Log-Analyse | `log-analyzer` |
```

---

## 8. Beispiel-Durchlauf: HomeAssistant + InfluxDB

### 8.1 Konfiguration (Anwender-Perspektive)

```yaml
# .meta-config/project.yaml
platforms:
  - homeassistant

mcp-servers:
  - home-assistant
  - influxdb

# mcp-agents nicht gesetzt → alle Agenten automatisch

# Secrets (separate Datei)
# .meta-config/secrets.local.yaml:
# MCP_HA_URL: "http://192.168.1.100:8123"
# MCP_HA_TOKEN: "eyJ..."
# MCP_INFLUXDB_URL: "http://192.168.1.100:8086"
# MCP_INFLUXDB_TOKEN: "xyz..."
# MCP_INFLUXDB_ORG: "home"
# MCP_INFLUXDB_BUCKET: "homeassistant"
```

### 8.2 Was generiert wird

Nach `python .agent-meta/scripts/sync.py`:

```
Projekt/
├── .claude/
│   ├── agents/
│   │   ├── orchestrator.md           # Enthält MCP-Agenten in Tabelle + Routing
│   │   ├── developer.md              # Enthält Delegation an MCP-Agenten
│   │   ├── mcp-home-assistant.md     # ← NEU: Generiert aus Registry
│   │   └── mcp-influxdb.md           # ← NEU: Generiert aus Registry
│   ├── rules/
│   │   ├── mcp-home-assistant.md     # Tool-Allow/Block-Regel
│   │   └── mcp-influxdb.md           # Tool-Allow/Block-Regel
│   └── settings.json                 # mcpServers → ${ENV_VAR} Referenzen
├── .opencode/
│   ├── agents/
│   │   ├── mcp-home-assistant.md     # ← Opencode-Format
│   │   └── mcp-influxdb.md           # ← Opencode-Format
│   └── ...
├── opencode.json                     # MCP-Konfiguration (type: remote/local, enabled: true)
├── .gemini/...                       # Gemini-Format
└── .continue/...                     # Continue-Format
```

### 8.3 Generierter Agent (Beispiel: `mcp-home-assistant.md` für Claude)

```markdown
---
name: mcp-home-assistant
description: "Home Assistant MCP Agent — Echtzeit-Sensor-Daten, Gerätestatus und Datetime-Informationen über das MCP-Protokoll abrufen und interpretieren."
model: claude-sonnet-4-6
tools:
  - Bash
  - Read
  - Glob
  - Grep
generated-from: "mcp-registry/home-assistant@1.0.0"
---

# MCP: home-assistant

> **Generiert aus `config/mcp-registry.yaml` — nicht manuell bearbeiten.**
> Server: `mcp-home-assistant` | Kategorie: `iot`

Du bist ein spezialisierter MCP-Agent für **home-assistant**.
Dein gesamter Zugriff auf diesen Dienst erfolgt über das MCP-Protokoll.

Home Assistant MCP Agent — Echtzeit-Sensor-Daten, Gerätestatus und Datetime-Informationen über das MCP-Protokoll abrufen und interpretieren.

---

## Home Assistant MCP — Arbeitsweise

Du bist der spezialisierte MCP-Agent für Home Assistant (HA).
Dein Zugang erfolgt ausschließlich read-only über MCP.

### Primäre Werkzeuge

| Tool | Verwendung |
|------|-----------|
| `GetLiveContext` | Primäres Tool — liefert Echtzeit-Status aller Geräte, Sensoren, Areas |
| `GetDateTime` | Aktuelles Datum/Uhrzeit vom HA-Server |
| `todo_get_items` | Todo-Listen nur lesen (Shopping-Liste, etc.) |

[...]

---

## Sicherheitsrichtlinien (ABSOLUT)

- **NUR LESENDE OPERATIONEN** — keine schreibenden, löschenden oder konfigurierenden Aktionen
- Keine Secrets, Tokens oder URLs in Antworten ausgeben
- Bei Unsicherheit: nachfragen, nicht raten
- MCP-Verbindungsfehler: melden und alternative Datenquellen vorschlagen

[...]
```

---

## 9. Implementierungs-Roadmap

### Phase 1: Registry-Erweiterung (0.5 Tage)
- [ ] `mcp-registry.yaml`: `agent` Block für `home-assistant` und `influxdb` definieren
- [ ] Schema-Dokumentation für `agent` Block in `project-config.schema.json`

### Phase 2: Generisches Template (0.5 Tage)
- [ ] `agents/1-generic/_mcp-agent.md` erstellen mit Platzhaltern
- [ ] MCP-Platzhalter in `build_variables()` registrieren

### Phase 3: sync.py Integration (2 Tage)
- [ ] `resolve_active_mcp_agents()` in `scripts/lib/mcp.py`
- [ ] `generate_mcp_agents()` in `scripts/lib/mcp.py`
- [ ] Aufruf in `sync.py` Per-Provider-Loop
- [ ] Provider-spezifische Transformation für MCP-Agenten
- [ ] Stale-Agent-Cleanup (entfernt MCP-Agenten wenn Server deaktiviert)

### Phase 4: Plattform-Bundles (1 Tag)
- [ ] `agents/2-platform/homeassistant-mcp-agents.yaml`
- [ ] `agent-overrides` Mechanismus in der Auflösung
- [ ] Laden und Mergen der Plattform-Overrides

### Phase 5: Orchestrator-Integration (1 Tag)
- [ ] MCP-Routing-Tabelle im Orchestrator-Template
- [ ] `{{AGENT_TABLE}}` erweitert um MCP-Agenten
- [ ] Plattform-Agenten referenzieren MCP-Agenten in Delegation

### Phase 6: Projekt-Konfiguration (0.5 Tage)
- [ ] `mcp-agents` Feld in `project.yaml`
- [ ] `mcp-agent-overrides` Feld in `project.yaml`
- [ ] `--init` erweitert für MCP-Agent-Auswahl (interaktiv)

### Phase 7: Tests & Doku (1 Tag)
- [ ] `--dry-run` Szenarien mit/ohne MCP-Agenten
- [ ] Alle 4 Provider (Claude, Opencode, Gemini, Continue) verifizieren
- [ ] README / CHANGELOG aktualisieren

**Geschätzt: ~6 Arbeitstage**

---

## 10. Dateien-Übersicht (was wird neu erstellt / geändert)

### Neue Dateien

| Datei | Beschreibung |
|-------|-------------|
| `agents/1-generic/_mcp-agent.md` | Generisches MCP-Agent-Template |
| `agents/2-platform/homeassistant-mcp-agents.yaml` | HA-Plattform MCP-Agent-Bundle |

### Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `config/mcp-registry.yaml` | `agent` Block für home-assistant, influxdb |
| `scripts/lib/mcp.py` | `resolve_active_mcp_agents()`, `generate_mcp_agents()` |
| `scripts/lib/config.py` | MCP-Platzhalter in `build_variables()` |
| `scripts/sync.py` | Aufruf `generate_mcp_agents()` in Provider-Loop |
| `agents/1-generic/orchestrator.md` | MCP-Routing-Tabelle |
| `.meta-config/project.yaml` (Schema) | `mcp-agents`, `mcp-agent-overrides` Felder |
| `config/project-config.schema.json` | Schema-Validierung für neue Felder |

---

## 11. Offene Fragen / Entscheidungen

1. **MCP-Agenten in `roles` aufnehmen?** — Auto-Include wenn Server aktiv, oder manuell?
   → Auto-Include (der Server ist die Aktivierung, der Agent folgt automatisch).

2. **Mehrere MCP-Agenten pro Server?** — z.B. `mcp-ha-reader` + `mcp-ha-admin`?
   → Aktuell: 1 Agent pro Server. Erweiterbar durch `agent.variants` in Registry.

3. **MCP-Agent als Subagent des Orchestrators oder standalone?**
   → Subagent (wie alle anderen Agenten auch).

4. **Body-Komposition vs. vollständiger Ersatz?**
   → `body` aus Registry ersetzt `{{MCP_SERVER_BODY}}` komplett. Kein Merge — zu komplex.

5. **`agent-hint` aus Registry vs. `agent.hint`?**
   → `agent.hint` ist spezifisch für den Agenten. `agent-hint` bleibt für die Rule-Datei.
   Beide werden aus der Registry gelesen, aber an verschiedenen Stellen verwendet.
