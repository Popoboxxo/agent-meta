# Energy Abstraction — Spike-Filter & Code-Vorlagen

## Spike-Filter: Monoton steigende Energy-Sensoren

### Problem
Manche Smart Plugs (Zigbee/Tasmota) melden schwankende kWh-Werte (Sägezahn-Muster). Da `utility_meter` mit `delta_values: false` jeden Anstieg als Verbrauch zählt, Rückgänge aber ignoriert, **schaukelt sich der Zähler auf** (Phantomverbrauch).

### Lösung: `this.state`-Filter

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

**Wann:** Hardware-Sensor mit schwankenden Totalverbrauchswerten (Sägezahn in InfluxDB, aufschaukelnder Utility Meter).
**Nicht bei:** Power-Sensoren (W) — diese dürfen schwanken.

### Nach Anwendung
- Template Reload reicht (Developer Tools → YAML → Template Entities)
- Aufgeschaukelten Utility-Meter-Stand über Developer Tools → States korrigieren

## Code-Vorlage: Neues Gerät hinzufügen

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

## YAML-Anker

- `&energy_style` / `*energy_style` — Stil-Definitionen für Energie-Sensoren
- `&power_style` / `*power_style` — Stil-Definitionen für Leistungs-Sensoren
- `&meter_config_no_reset` / `*meter_config_no_reset` — Utility-Meter-Konfiguration
- Definition (`&`) steht im ersten Geräte-Block — alle neuen Geräte danach einfügen
