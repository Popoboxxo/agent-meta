# Entity-Daten Beschaffung & Analyse

## Datenquellen-Hierarchie

1. **MCP `GetLiveContext`** — Echtzeit, immer bevorzugen
2. **`{{platform.homeassistant.entities_csv_path}}`** — Snapshot mit Metadaten (ENTITY ID, NAME, DEVICE, AREA, PLATFORM, INTEGRATION, DOMAIN)
3. **Developer Console Template** — Fallback, manuell durch User

## Workflow

MCP verfügbar → `GetLiveContext`. Nicht erreichbar → CSV mit Snapshot-Warnung. Beides nicht → Console-Template an User.

## Nutzungsregeln

- **MCP**: Aktueller Zustand, Debugging, Real-time Check
- **CSV**: Übersicht aller Entitäten, Pattern-Analyse, MCP nicht verfügbar
- **Kombinieren**: MCP für State + CSV zur Bestätigung der Registry-Struktur

Vollständige Workflow-Referenz (CSV-Spalten, Anomalien-Tabelle, Templates):
→ `rules/2-platform/_wf-ha-entity-data.md` (Read bei Bedarf)
