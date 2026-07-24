# MCP Setup — Best Practices

agent-meta verwaltet MCP-Server als First-Class-Konzept: Registry, Regel-Generierung
und sichere Secrets-Handhabung über alle Provider hinweg.

## Konzept in 30 Sekunden

```
config/mcp-registry.yaml          ← Globaler Katalog (was gibt es?)
  +
project.yaml: mcp-servers: [...]  ← Projekt-Aktivierung (was nutzt dieses Projekt?)
  oder: platforms: [homeassistant] ← Implizit via Platform-Bundle
  +
.meta-config/secrets.local.yaml   ← Echte Credentials (gitignored, einmalig befüllen)
        ↓
    sync.py
        ├─→  Regel-Dateien: mcp-<server>.md (erlaubte/verbotene Tools)
        ├─→  Provider-Configs: committed (${ENV_VAR}) + lokale (echte Werte)
        └─→  Gitignore-Einträge für alle Secrets-Dateien
```

---

## Schritt 1: MCP-Server aktivieren

### Option A — Explizit in `project.yaml`

```yaml
mcp-servers:
  - home-assistant
  - influxdb
```

### Option B — Implizit via Plattform

```yaml
platforms: [homeassistant]
# → Lädt automatisch rules/2-platform/homeassistant-mcp.yaml
# → Aktiviert: home-assistant, influxdb
```

---

## Schritt 2: Secrets befüllen

`sync.py` generiert beim ersten Sync ein Template unter `.meta-config/secrets.local.yaml`
falls die Datei noch nicht existiert. Werte einmalig eintragen:

```yaml
# .meta-config/secrets.local.yaml — NIEMALS committen (gitignored)
MCP_HA_URL: "http://192.168.1.100:8123"
MCP_HA_TOKEN: "eyJhbGciOiJIUzI1NiIsInR5..."
MCP_INFLUXDB_URL: "http://192.168.1.100:8086"
MCP_INFLUXDB_TOKEN: "mein-influxdb-token=="
MCP_INFLUXDB_ORG: "homeassistant"
MCP_INFLUXDB_BUCKET: "homeassistentbucket"
```

Template-Kopierbefehl:
```bash
cp .agent-meta/howto/configs/mcp-secrets.local-template.yaml .meta-config/secrets.local.yaml
# Datei editieren und Werte eintragen
```

---

## Schritt 3: Provider-Konfiguration

Jeder Provider hat eine committed Datei (env-var Referenzen) und eine gitignored Datei
(echte Werte). Die gitignored Datei wird durch `sync.py` im `.gitignore`-managed-Block
automatisch geschützt.

| Provider | Committed | Gitignored (Secrets) |
|---|---|---|
| Claude | `.claude/settings.json` | `.claude/settings.local.json` |
| Opencode | `opencode.json` | `.opencode/mcp.local.json` |
| Continue | `.continue/config.yaml` | `.continue/config.local.yaml` |
| Gemini | `.gemini/settings.json` | `.gemini/settings.local.json` |

Konfigurationsbeispiele für alle Provider: `rules/2-platform/_wf-ha-mcp-local.md`

---

## Schritt 4: sync.py ausführen

```bash
python .agent-meta/scripts/sync.py
```

sync.py generiert automatisch:
- `mcp-home-assistant.md` und `mcp-influxdb.md` in den Provider-Regel-Verzeichnissen
- Provider-Configs (committed + gitignored lokal) für alle aktiven Provider
- `.gitignore`-Einträge für alle Secrets-Dateien

---

## Neuen MCP-Server hinzufügen

1. Eintrag in `config/mcp-registry.yaml` anlegen (description, tools, connection, secrets)
2. Optional: In Platform-Bundle `rules/2-platform/<platform>-mcp.yaml` referenzieren
3. `sync.py` ausführen — Regel-Dateien und gitignore-Einträge werden automatisch generiert

---

## Sicherheitsregeln

### Default: Secrets niemals committen

- `secrets-file` pro Provider ist immer gitignored (automatisch via managed block)
- `.meta-config/secrets.local.yaml` ist immer gitignored
- `sync.py` bricht ab (`SyncError`) wenn ein Secret in einer committed Datei erkannt wird — kein stilles Durchlassen

### Opt-out (bewusste Ausnahme)

Nur für lokale Dev-Umgebungen ohne Außenzugriff:

```yaml
# project.yaml
allow-committed-secrets: true   # Warnung statt Abbruch bei jedem Sync
```

### Eigene Secret-Patterns ergänzen

```yaml
# project.yaml
security:
  secret-patterns:
    - name: "mein-service-token"
      regex: "mst_[a-zA-Z0-9]{32}"
```

---

## Vorhandene `.mcp.json` mit Secrets migrieren

Wenn eine `.mcp.json` mit hardcodierten Tokens existiert:

1. Prüfen ob `.mcp.json` in `.gitignore` eingetragen ist: `grep .mcp.json .gitignore`
2. Wenn nicht: **sofort** in `.gitignore` eintragen und Git-History bereinigen
3. Secrets in `.meta-config/secrets.local.yaml` verschieben
4. `.mcp.json` durch Provider-spezifische Konfiguration mit `${ENV_VAR}`-Refs ersetzen
5. `sync.py` ausführen — managed block übernimmt die Gitignore-Pflege

Token rotieren wenn unsicher ob er in Git-History gelandet ist!

---

## Referenzen

- `config/mcp-registry.yaml` — Globaler Server-Katalog
- `rules/2-platform/homeassistant-mcp.yaml` — HA-Platform-Bundle
- `rules/2-platform/_wf-ha-mcp-local.md` — Konfig-Beispiele für alle Provider
- `howto/configs/mcp-secrets.local-template.yaml` — Secrets-Template
- `howto/mcp/honcho-setup.md` — Honcho Memory-Server aktivieren
