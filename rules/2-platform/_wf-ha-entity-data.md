# Entity-Daten Beschaffung — Workflow & Referenz

## Workflow: Datenquelle wählen

```
Szenario: User fragt nach Entitätsdaten

1. VERSUCHE: MCP GetLiveContext → ECHTZEITDATEN
   ├─ Erfolgreich: Nutze State + Attributes + Last Changed
   └─ Gescheitert → weiter zu 2.

2. FALLBACK: CSV durchsuchen nach AREA / ENTITY NAME
   ├─ CSV zeigt: alle zugeordneten Entitäten (Snapshot)
   └─ Warnung ausgeben: "CSV ist Snapshot vom [Zeitstempel]"

3. LAST RESORT: Developer-Console-Template an User übergeben
   └─ User validiert manuell
```

## Vergleich: MCP vs. CSV vs. Developer Console

| Aspekt | MCP GetLiveContext | CSV File | Developer Console |
|--------|-------------------|----------|-------------------|
| Aktualität | Live | Snapshot | Manuell |
| Status | Echtzeit State | Registry-Daten | Live, manuell |
| Verfügbarkeit | Netz erforderlich | Immer lokal | Immer lokal |
| Priorität | **#1** | #2 | #3 |

## Nutzungsregeln

**MCP nutzen:** Aktueller Zustand, Debugging, Real-time Check.
**CSV nutzen:** MCP nicht erreichbar, Übersicht aller Entitäten, Pattern-Analyse.
**Kombinieren:** MCP für State + CSV zur Bestätigung der Registry-Struktur.

## CSV-Spalten

`ENTITY ID` | `ENTITY NAME` | `DEVICE NAME` | `DEVICE ID` | `AREA` | `PLATFORM` | `INTEGRATION` | `DOMAIN` | `DEVICE AREA`

Beispiel: `light.wohnzimmer_hue;Wohnzimmer Hue;Hue Bridge;device-123;Wohnzimmer;zigbee;hue;light;Wohnzimmer`

## CSV-Anomalien

| Anomalie | Grund | Aktion |
|----------|-------|--------|
| AREA leer | Keine Area zugeordnet | MCP prüfen oder manuell zuordnen |
| DEVICE NAME leer | Orphan-Entität | Prüfen ob Integration aktiv ist |
| Doppelte ENTITY IDs | CSV-Export-Bug | MCP GetLiveContext validieren |
| PLATFORM ≠ INTEGRATION | Normalität (z.B. rest/openweathermap) | Erwartetes Verhalten |

## Developer-Console-Template (Fallback)

```jinja2
{{ states('sensor.example_entity') }}
{{ state_attr('sensor.example_entity', 'unit_of_measurement') }}
{{ states.sensor.example_entity.attributes }}
```
