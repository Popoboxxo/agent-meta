# Entity-Daten Beschaffung & Analyse

## Datenquellen-Hierarchie

1. **Primary Source (Echtzeit)**: MCP `GetLiveContext` Tool
   - Liefert Echtzeit-Kontext über den aktuellen Zustand von Geräten, Sensoren und Areas
   - **IMMER bevorzugt**, wenn MCP verfügbar ist

2. **Secondary Source (Snapshot)**: `{{platform.homeassistant.entities_csv_path}}` aus dem Entity-Analyzer-Tool
   - Enthält alle vorhandenen Entitäten mit Metadaten:
     - `ENTITY ID`, `ENTITY NAME`, `DEVICE NAME`, `DEVICE ID`, `AREA`
     - `PLATFORM`, `INTEGRATION`, `DOMAIN`, `DEVICE AREA`
   - Wird regelmäßig per Automation aktualisiert
   - Nutze CSV für **Vergleiche & Pattern-Analyse** und umfassende Übersichten

3. **Developer Console Template (Fallback)**: Manuelle Validierung durch User
   - Wenn MCP nicht erreichbar ist
   - Begrenzte Daten-Sicht, aber keine Abhängigkeiten

## Workflow: Entity-Daten Beschaffung

```
Szenario:
- User fragt: "Welche Sensoren sind im Wohnzimmer?"

Ablauf:
1. VERSUCHE: MCP GetLiveContext → ECHTZEITDATEN
   ├─ Wenn erfolgreich: Nutze diese Daten + alle Attribute
   └─ Gib Details zu State, Attributes, Last Changed aus

2. FALLBACK: CSV durchsuchen nach "wohnzimmer" in AREA oder ENTITY NAME
   ├─ CSV zeigt: Alle zugeordneten Entitäten (Snapshot)
   └─ Gib Warnung aus: "CSV ist ein Snapshot vom [Zeitstempel]"

3. LAST RESORT: Template für Entwicklerconsole geben
   ├─ User muss manuell validieren
   └─ Kombiniert Precision + Autarkie
```

## Vergleich: MCP vs. CSV vs. Developer Console

| Aspekt | MCP (GetLiveContext) | CSV File | Developer Console |
|--------|----------------------|----------|-------------------|
| **Aktualität** | Live | Snapshot | Manuell |
| **Status** | Echtzeit State | Registry-Daten | Live, manuell |
| **Attribute** | Kontextabhängig | Teilweise | Manuell |
| **Verfügbarkeit** | Netz erforderlich | Immer lokal | Immer lokal |
| **Priorität** | **#1 Primary** | #2 Secondary | #3 Fallback |

## Nutzungsregeln

**CSV nutzen, wenn:**
- MCP ist nicht erreichbar ODER
- User möchte umfassende **Übersicht aller Entitäten** (nicht einzelne prüfen) ODER
- Pattern-Analyse über viele Entitäten (z.B. "Welche Integrationen nutzen wir?")

**MCP nutzen, wenn:**
- User fragt nach **aktuellem Zustand** eines Geräts/Sensors/Bereichs ODER
- User hat Doubt über aktuelle Daten (Real-time Check erforderlich) ODER
- Debugging: Aktueller State als erster Schritt vor einer bedingten Aktion

**Kombinieren:**
- MCP für aktuellen State + CSV zur Validierung der Registry-Struktur
- CSV für Überblick + MCP für Detailfragen zu spezifischen Entities

## CSV-Struktur & Interpretation

**Beispiel-Zeile:**
```
light.wohnzimmer_hue;Wohnzimmer Hue;Hue Bridge;device-123;Wohnzimmer;zigbee;hue;light;Wohnzimmer
```

**Spalten-Bedeutung:**
- `ENTITY ID`: Eindeutige System-ID (immer stabil)
- `ENTITY NAME`: Freundlicher Name (kann sich ändern)
- `DEVICE NAME`: Hardware-Name (z.B. "Hue Bridge")
- `DEVICE ID`: Eindeutige Geräte-ID
- `AREA`: **Räumliche Zuordnung** (KANN LEER SEIN)
- `PLATFORM`: Wo kommen die Daten her (z.B. "zigbee", "mqtt", "rest")
- `INTEGRATION`: Integration-Name (z.B. "hue", "mqtt", "template")
- `DOMAIN`: Entity-Type (z.B. "light", "sensor", "switch")
- `DEVICE AREA`: Area vom Device (Fallback wenn Entity-Area leer)

## Häufige CSV-Anomalien & Interpretation

| Anomalie | Grund | Aktion |
|----------|-------|--------|
| **AREA ist leer** | Entity/Device hat keine Area zugeordnet | MCP nutzen um zu prüfen, oder manuell zuordnen |
| **DEVICE NAME leer** | Entität ist "Orphan" (gehört zu keinem Device) | Prüfe ob Integration noch aktiv ist |
| **Doppelte ENTITY IDs** | CSV-Export-Bug oder mehrere Quellen | MCP `GetLiveContext` zur Validierung |
| **PLATFORM vs INTEGRATION verschieden** | Normalität (z.B. Platform=rest, Integration=openweathermap) | Erwartetes Verhalten |

## Beispiel-Template für Entwicklerconsole (Fallback)

```jinja2
{# Wenn MCP nicht verfügbar - User manuell validieren #}

{# Aktuelle State + Attribute #}
{{ states('sensor.example_entity') }}
{{ state_attr('sensor.example_entity', 'unit_of_measurement') }}
{{ states.sensor.example_entity.attributes }}

{# Entity-Registry Infos (zeigt, ob Entität aktiviert ist) #}
{# Copyable Template für Developer Tools → Templates #}
```
