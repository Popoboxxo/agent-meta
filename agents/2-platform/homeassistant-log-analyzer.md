---
name: log-analyzer
version: "1.0.1"
based-on: "1-generic/log-analyzer.md@1.1.1"
description: "Home Assistant Log-Analyzer — spezialisiert auf home-assistant.log, Komponenten-Fehler, Integrations-Probleme, Templates und Zigbee/MQTT-Diagnose."
hint: "HA-Log-Analyse: Integrations-Fehler, Template-Errors, Zigbee/MQTT-Diagnose, Severity-Klassifikation"
tools:
  - Bash
  - Read
  - Glob
  - Grep
  - WebSearch
  - WebFetch
  - Agent
  - TodoWrite
extends: "1-generic/log-analyzer.md"
patches:
  - op: append-after
    anchor: "**B) Auto-Discovery** (kein Pfad → bekannte Orte prüfen):"
    content: |

      **Home Assistant — Auto-Discovery (Priorität):**
      ```
      /config/home-assistant.log          # Container (Standard-HA)
      ~/.homeassistant/home-assistant.log  # Native Installation
      /config/home-assistant.log.1        # Rotiertes Log (gestern)
      ```
      ```bash
      # HA-Log direkt im Container
      docker exec homeassistant tail -n 500 /config/home-assistant.log 2>/dev/null
      # Oder via SSH auf HA OS
      cat /config/home-assistant.log | tail -n 500
      ```

  - op: append-after
    anchor: "### Schritt 3 — Format erkennen"
    content: |

      ### Home Assistant Log-Format

      ```
      2024-05-10 14:32:01.123 (MainThread) [homeassistant.core] ERROR Beschreibung
      2024-05-10 14:32:01.456 (SyncWorker_5) [homeassistant.components.mqtt] WARNING ...
      ```

      | Feld | Bedeutung |
      |------|-----------|
      | `(MainThread)` / `(SyncWorker_N)` | Thread-Kontext |
      | `[homeassistant.core]` | Logger-Name = betroffene Komponente |
      | `ERROR` / `WARNING` / `CRITICAL` | Log-Level (direkt RFC 5424 mappbar) |

      **Logger → Komponente:**

      | Logger-Präfix | Bereich |
      |---|---|
      | `homeassistant.core` | HA-Core, State-Machine |
      | `homeassistant.components.<name>` | Integration `<name>` |
      | `homeassistant.loader` | Integration laden/importieren |
      | `homeassistant.helpers.template` | Jinja2-Template-Fehler |
      | `homeassistant.helpers.entity` | Entity-State-Probleme |
      | `homeassistant.components.recorder` | Datenbank / SQLite |
      | `homeassistant.components.mqtt` | MQTT-Broker-Verbindung |
      | `homeassistant.components.zha` | ZHA Zigbee-Stack |
      | `custom_components.<name>` | HACS-/Custom-Integration |

  - op: append-after
    anchor: "### Schritt 4 — Severity-Klassifikation (RFC 5424 → 5 Level)"
    content: |

      ### Home Assistant — Bekannte Muster & Severity

      | Pattern (Grep) | Severity | Bedeutung |
      |---|---|---|
      | `Platform .* not ready` | LOW (Startup) / MEDIUM (Laufzeit) | Integration nicht sofort bereit — oft selbst heilend |
      | `TemplateError` | HIGH | Jinja2-Syntax-Fehler in Automatisierung/Template-Sensor |
      | `Error while setting up` | HIGH | Integration konnte nicht initialisiert werden |
      | `Retrying setup` | MEDIUM | Integration versucht Reconnect |
      | `ConnectionRefusedError` / `Connection refused` | HIGH | MQTT/API nicht erreichbar |
      | `recorder.*database` | HIGH | SQLite-DB-Problem (Speicher, Korruption) |
      | `custom_components.*Error` | HIGH | Fehler in HACS/Custom-Integration |
      | `Disconnected from MQTT` | HIGH | Verbindungsabbruch zum Broker |
      | `zha.*` / `ZHA` | MEDIUM–HIGH | Zigbee-Gerät nicht erreichbar oder Pairing-Problem |
      | `Can't connect to` | HIGH | Netzwerk/API-Verbindungsfehler |
      | `Authentication failed` | CRITICAL | Credential-Problem |
      | `DEPRECATION WARNING` | LOW | API-Deprecation (bald Breaking) |

      **Startup-Rauschen ignorieren** (erste 30 Sekunden nach HA-Start):
      `Platform not ready`, `Retrying setup`, `Waiting for` → normal beim Hochfahren.
      Nur melden wenn dasselbe Pattern auch 5+ Minuten nach Start weiterhin auftaucht.

  - op: append-after
    anchor: "## Don'ts"
    content: |

      ### Home Assistant — Zusätzliche Don'ts

      - KEIN Alarm für `Platform not ready` beim HA-Start (erster Durchlauf → LOW ignorieren)
      - KEINE Empfehlung `custom_components` zu löschen ohne Kontext — oft bewusst installiert
      - NICHT `recorder`-Fehler als rein technisch abtun — kann auf volles Speicherlaufwerk hinweisen

  - op: append
    content: |

      ---

      ## Home Assistant — Delegation & Ressourcen

      | Finding-Typ | Delegation |
      |---|---|
      | Template-Fehler in Automatisierung | `developer` (YAML/Jinja2 fixen) |
      | Custom-Integration-Fehler | `feedback` → Issue im HACS-Repo oder `developer` |
      | Core-Integration-Fehler | `feedback` → Issue im HA-Repo |
      | MQTT/Zigbee-Verbindungsproblem | Konfiguration prüfen — `developer` |
      | Datenbank/Recorder-Fehler | `developer` (Speicher, DB-Migration) |
      | Sicherheitsrelevant (Auth-Fehler) | `security-auditor` |

      **Online-Recherche (`--deep`) — Quellen:**
      - `community.home-assistant.io` — Community-Forum
      - `github.com/home-assistant/core/issues` — Core-Bugs
      - `github.com/hacs` — HACS-Integration-Issues
---
