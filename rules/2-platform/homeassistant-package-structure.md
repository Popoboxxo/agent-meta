# Package-Struktur & Fachliches Clustering

## Oberste Direktive: Modularisierung

Das Home Assistant Repository folgt einer **strikten fachlichen Clusterung** durch das Package-System. Konfigurationen werden **NIEMALS** monolithisch in einzelne Root-Dateien (wie `sensor.yaml`, `automation.yaml`) geschrieben, sondern modular in thematische Packages aufgeteilt.

## Aktuelle Package-Struktur

Das `/config/packages/` Verzeichnis ist nach **Fachdomänen** organisiert:

```
packages/
├── abstraction/        # Abstraktionsschichten (z.B. energy_power.yaml)
├── bsm/                # Batterie-/Speicher-Management (battery_control.yaml)
├── car/                # Auto-bezogene Integrationen (Ladung, Fahrzeug-APIs)
├── fitness/            # Fitness & Gesundheits-Tracking
├── grid/               # Stromnetz, Spotpreise
├── heating/            # Heizungs-Steuerung
├── home/               # Haus-Kernfunktionen (climate.yaml, window_monitoring.yaml, air_quality.yaml)
├── home_appliances/    # Haushaltsgeräte (Waschmaschine, Trockner, Geschirrspüler)
├── location/           # Präsenz, GPS, Zonen
├── mining/             # Krypto-Mining Überwachung
├── report/             # Reporting & Statistiken
├── solar/              # Solar-Erzeugung (dtu.yaml, solarforecast.yaml, solarmanager.yaml)
└── weather/            # Wetter-Daten & Vorhersagen
```

## Package-Philosophie

### Grundprinzipien
1. **Ein Package = Eine Fachdomäne**: Jedes Package behandelt einen abgeschlossenen Themenbereich
2. **Ein File = Ein Sub-Thema**: Innerhalb eines Packages wird nach Sub-Themen aufgeteilt
3. **Keine Root-Dateien**: Root-Dateien (z.B. `sensor.yaml`) bleiben leer oder enthalten nur `!include_dir_merge_list packages/`
4. **Self-Contained**: Jedes Package ist in sich geschlossen und kann isoliert verstanden werden

### Beispiel-Aufbau eines Packages

**Datei**: `/config/packages/home/climate.yaml`
```yaml
# ==============================================================================
# PACKAGE: Home Climate Management
# Beschreibung: Zentrale Klima-Steuerung für alle Räume inkl. Circadian Rhythm
# ==============================================================================

# --- Input Helpers ---
input_boolean:
input_number:

# --- Template Sensors ---
template:
  - sensor:
  - binary_sensor:

# --- Automations ---
automation:
  - alias: "Climate Scheduler [V1.0]"
    id: climate_scheduler

# --- Scripts ---
script:
  climate_emergency_heat:
```

## Regeln für Package-Erweiterung

### Wann eine neue Datei anlegen?
- Ein neues Sub-Thema hinzukommt (z.B. `packages/solar/battery_management.yaml`)
- Eine bestehende Datei über **500 Zeilen** wächst → Split in logische Sub-Dateien
- Ein Sub-Thema mindestens **5+ Entitäten** (Sensoren, Automations, Scripts) umfasst

**KEINE** neue Datei für:
- Einzelne Sensoren oder Automations → In existierende Datei integrieren
- Temporäre Experimente → In `packages/home/experimental.yaml` (falls vorhanden)

### Wann ein neues Package anlegen?
- Eine neue **Hauptdomäne** entsteht (z.B. `packages/garden/` für Gartenbewässerung)
- Mindestens **2-3 YAML-Dateien** für das Thema erwartet werden
- Das Thema **unabhängig** von anderen Domains ist

### Naming Conventions für Package-Dateien

| Typ | Beispiel | Schema |
|-----|----------|--------|
| **Hauptfunktion** | `climate.yaml` | `[domain].yaml` |
| **Spezifische Hardware** | `dtu.yaml` | `[hardware_name].yaml` |
| **Funktions-Gruppe** | `window_monitoring.yaml` | `[function]_[object].yaml` |
| **Abstraktion** | `energy_power.yaml` | `[category]_[subcategory].yaml` |

## Workflow: Neues Package erstellen

### Schritt 1: Domänen-Analyse
Frage: Zu welcher Hauptdomäne gehört die neue Funktionalität?
- Wenn eng mit bestehender Domain verbunden → Existierendes Package
- Wenn eigenständige Domain mit Wachstumspotenzial → Neues Package

### Schritt 2: Datei-Struktur planen
```yaml
# ==============================================================================
# PACKAGE: [Domain] - [Sub-Thema]
# Beschreibung: [1-2 Sätze zur Funktion]
# Dependencies: [Liste von Integrationen, z.B. "Zigbee2MQTT, Shelly"]
# Autor: HA Expert 2.0
# Version: V1.0
# ==============================================================================
```

### Schritt 3: Entitäten gruppieren
Struktur innerhalb der Datei:
1. **Input Helpers** (Booleans, Numbers, Selects, Datetimes)
2. **Template Sensors/Binary Sensors** (Berechnete Werte)
3. **Automations** (Logik & Trigger)
4. **Scripts** (Wiederverwendbare Aktionen)
5. **Scenes** (Optional, falls relevant)

### Schritt 4: Integration in `configuration.yaml`
```yaml
homeassistant:
  packages: !include_dir_named packages
```

## Migration: Root-Dateien zu Packages

### Typische Migrationspfade

| Root-Datei | Ziel-Package | Beispiel |
|------------|--------------|----------|
| `sensor.yaml` (Energie) | `packages/abstraction/energy_power.yaml` | Energie-Sensoren |
| `sensor.yaml` (Solar) | `packages/solar/solarforecast.yaml` | Solar-Prognosen |
| `automation.yaml` (Klima) | `packages/home/climate.yaml` | Klima-Automations |
| `automation.yaml` (Auto) | `packages/car/charging.yaml` | Lade-Logik (EV-Charging) |
| `script.yaml` (Benachrichtigungen) | `packages/home/notifications.yaml` | Notification-Scripts |

### Migrations-Workflow

1. **Identifiziere** die Entität und ihre fachliche Domäne
2. **Prüfe** ob bereits eine passende Package-Datei existiert
3. **Erstelle** bei Bedarf eine neue Package-Datei mit Header
4. **Verschiebe** die Entität inkl. aller Kommentare
5. **Ergänze** den Code-Header mit Version V1.0
6. **Validiere** YAML-Syntax mit `ha core check` oder Developer Tools
7. **Teste** die Entität nach Reload/Restart

**WICHTIG**: Bei Verschiebung von Entitäten:
- `unique_id` und `entity_id` bleiben **EXAKT** gleich
- Nur `alias` oder `friendly_name` werden mit `[V1.0]` ergänzt
- Keine Funktionalitäts-Änderungen während Migration

## Best Practices für Package-Wartung

### Code-Organisation innerhalb einer Package-Datei

```yaml
# 1. Header (IMMER am Anfang)
# ==============================================================================
# PACKAGE: [Name]
# ==============================================================================

# 2. Configuration (Optional)
homeassistant:
  customize:

# 3. Input Helpers
input_boolean:
input_number:
input_select:
input_datetime:

# 4. Template Sensoren (Berechnet)
template:
  - sensor:
  - binary_sensor:

# 5. Automations (Logik)
automation:

# 6. Scripts (Wiederverwendbar)
script:

# 7. Scenes (Optional)
scene:
```

### Dokumentations-Standard

Jede Package-Datei MUSS enthalten:
1. **Header-Block** mit Beschreibung
2. **Dependencies** (welche Integrationen werden benötigt?)
3. **Inline-Kommentare** bei komplexen Logiken
4. **Changelog** bei Updates (im Header)

### Versionierung von Packages

- **V1.0** bei Erstanlage
- **V1.x** bei kleineren Erweiterungen innerhalb der Datei
- **V2.0** bei strukturellen Änderungen (z.B. Split in mehrere Sub-Dateien)

```yaml
# Version: V1.3
# Changelog:
#   - V1.3: Hinzufügen von battery_threshold_alerts
#   - V1.2: Neue Sensoren integriert
#   - V1.1: Fehlerbehebung bei Template-Syntax
#   - V1.0: Initiale Erstellung
```

## Troubleshooting: Package-Loading-Probleme

### Häufige Fehler

| Problem | Ursache | Lösung |
|---------|---------|--------|
| Package wird nicht geladen | YAML-Syntax-Fehler | `Developer Tools → Check Configuration` |
| Entitäten doppelt | In Root-Datei UND Package | Root-Datei leeren |
| Anker-Fehler | Anker-Definition (`&`) nach Referenz (`*`) | Anker VOR erste Nutzung verschieben |
| Reload funktioniert nicht | Neue Domain hinzugefügt | **Full Restart** notwendig |

### Debugging-Workflow
1. **Check Logs**: `Settings → System → Logs` nach Package-Namen filtern
2. **Validate YAML**: Developer Tools → YAML → Check Configuration
3. **Incremental Test**: Package temporär auskommentieren, schrittweise aktivieren
4. **Entity Registry**: `Developer Tools → States` → Prüfe ob Entität existiert
