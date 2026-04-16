# Energy Abstraction Layer

## System-Kontext
**Datei**: `/config/packages/abstraction/energy_power.yaml`

## Konzept

Physische Entitäten (z.B. von Tasmota, Shelly, Zigbee) werden **NIEMALS direkt** in Dashboards oder Utility Metern verwendet. Stattdessen werden Template-Sensoren erstellt, die standardisierte IDs und Namen haben.

## Technik

- **YAML-Anker**: Werden genutzt (`&energy_style`, `*energy_style`) um Code zu reduzieren
  - Definition (`&`) MUSS vor Referenz (`*`) stehen
- **Utility Meter**: Greifen ausschließlich auf abstrahierte Template-Sensoren zu
- **UUIDs**: Jede Entität bekommt eine statische v4 UUID

## Architektur-Regeln für Erweiterungen

Wenn ein neuer Smart Plug hinzugefügt werden soll, befolge **strikt** dieses Muster:

### 1. Abstraktion (Template Sensors)
- Erstelle einen Sensor für **Energy (kWh)** und einen für **Power (W)**
- **Naming**: "[Raum/Gerät] [Gesamtverbrauch|Aktuelle Leistung]"
- **State**: Nutze `| float(0)` im Template zur Fehlervermeidung
- **Style**: Nutze die existierenden Anker `*energy_style` und `*power_style`
- **UUID**: Generiere zwingend neue UUIDs

### 2. Utility Meter
- Erstelle einen Zähler mit dem Suffix `_energy_count`
- **Source**: Muss der neue abstrahierte Sensor sein (nicht die Hardware-Entität!)
- **Config**: Nutze den Anker `*meter_config_no_reset`

## Spike-Filter: Monoton steigende Energy-Sensoren

### Problem
Manche Smart Plugs (z.B. Zigbee/Tasmota) melden durch Hardwarefehler **schwankende kWh-Werte** (Sägezahn-Muster). Der Energy-Wert springt z.B. zwischen 3.24 und 3.33 hin und her. Da ein `utility_meter` mit `delta_values: false` jeden Anstieg als echten Verbrauch zählt, Rückgänge aber ignoriert, **schaukelt sich der Zähler auf** — es wird Phantomverbrauch akkumuliert.

### Lösung: `this.state`-Filter
Ein Energiezähler (kWh) darf physikalisch nur steigen. Der Template-Sensor nutzt `this.state` um seinen vorherigen Wert zu referenzieren und akzeptiert nur Werte `>= old_val`:

```yaml
# --- Energy (kWh) --- SPIKE-FILTER (monoton steigend) ---
- name: "[Name] Gesamtverbrauch"
  unique_id: "[UUID]"
  state: >
    {% set new_val = states('sensor.hardware_id_energy') | float(0) %}
    {% set old_val = this.state | float(0) %}
    {# Energiezähler dürfen nur steigen — Rücksprünge = Hardwarefehler #}
    {% if new_val >= old_val %}
      {{ new_val }}
    {% else %}
      {{ old_val }}
    {% endif %}
  availability: >
    {{ has_value('sensor.hardware_id_energy') }}
  <<: *energy_style
```

### Wann anwenden?
- Wenn ein Hardware-Sensor **schwankende Totalverbrauchswerte** meldet
- Erkennbar an: Sägezahn-Muster in InfluxDB, aufschaukelnder Utility Meter
- **Nicht** anwenden bei Power-Sensoren (W) — diese dürfen schwanken

### Nach Anwendung
- **Template Reload** reicht (Developer Tools → YAML → Template Entities)
- **Utility Meter zurücksetzen**: Aufgeschaukelten Zählerstand über Developer Tools → States korrigieren

## Code-Vorlage (Copy-Paste Ready)

```yaml
# =====================================================
# NEUES GERÄT: [Gerätename]
# HARDWARE ID: [sensor.hardware_id_...]
# =====================================================
template:
  - sensor:
      # --- Energy (kWh) ---
      - name: "[Name] Gesamtverbrauch"
        unique_id: "[NEUE_UUID_V4]"
        state: >
          {{ states('sensor.hardware_id_energy') | float(0) }}
        <<: *energy_style

      # --- Power (W) ---
      - name: "[Name] Aktuelle Leistung"
        unique_id: "[NEUE_UUID_V4]"
        state: >
          {{ states('sensor.hardware_id_power') | float(0) }}
        <<: *power_style

utility_meter:
  [name]_energy_count:
    source: sensor.[slug_des_abstrahierten_sensors]
    name: "[Name] Gesamtverbrauch Count"
    unique_id: "[NEUE_UUID_V4]"
    <<: *meter_config_no_reset
```

## Vorhandene Definitionen

- Anker-Definitionen (`&`) befinden sich im ersten Geräte-Block der Datei
- Alle neuen Geräte müssen **danach** eingefügt werden oder Referenzen (`*`) nutzen
- Vorhandene Geräte: in `energy_power.yaml` nachschauen — Anker-Definitionen stehen ganz oben
