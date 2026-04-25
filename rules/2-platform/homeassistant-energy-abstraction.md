# Energy Abstraction Layer

**Datei**: `/config/packages/abstraction/energy_power.yaml`

## Konzept

Physische Entitäten (Tasmota, Shelly, Zigbee) werden **NIEMALS direkt** in Dashboards oder Utility Metern verwendet — immer über Template-Sensoren mit standardisierten IDs abstrahieren.

## Architektur-Regeln

**Template Sensors:** Energy (kWh) + Power (W) pro Gerät, `| float(0)` im Template, Anker `*energy_style` / `*power_style`, neue UUIDs.

**Utility Meter:** Suffix `_energy_count`, Source = abstrahierter Sensor (nie Hardware-Entität!), Anker `*meter_config_no_reset`.

**YAML-Anker:** Definition (`&`) steht im ersten Geräte-Block. Alle neuen Geräte danach einfügen.

## Spike-Filter (wichtig!)

Manche Smart Plugs melden schwankende kWh-Werte → Utility Meter schaukelt auf. Lösung: `this.state`-Filter im Template (Energiezähler dürfen nur steigen).

Vollständige Code-Vorlage, Spike-Filter-Template, Anker-Referenz:
→ `rules/2-platform/_wf-ha-energy-template.md` (Read bei Bedarf)
