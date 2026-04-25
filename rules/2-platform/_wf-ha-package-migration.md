# HA Package — Migration & Troubleshooting

## Workflow: Neues Package erstellen

### Schritt 1: Domänen-Analyse
- Eng mit bestehender Domain → existierendes Package erweitern
- Eigenständige Domain mit Wachstumspotenzial → neues Package

### Schritt 2: Datei-Struktur

```yaml
# ==============================================================================
# PACKAGE: [Domain] - [Sub-Thema]
# Beschreibung: [1-2 Sätze]
# Dependencies: [Integrationen]
# Autor: HA Expert 2.0
# Version: V1.0
# ==============================================================================
```

### Schritt 3: Entitäten gruppieren

1. Input Helpers (Booleans, Numbers, Selects, Datetimes)
2. Template Sensors/Binary Sensors
3. Automations
4. Scripts
5. Scenes (optional)

### Schritt 4: Integration in `configuration.yaml`

```yaml
homeassistant:
  packages: !include_dir_named packages
```

## Migration: Root-Dateien zu Packages

| Root-Datei | Ziel-Package |
|------------|--------------|
| `sensor.yaml` (Energie) | `packages/abstraction/energy_power.yaml` |
| `sensor.yaml` (Solar) | `packages/solar/solarforecast.yaml` |
| `automation.yaml` (Klima) | `packages/home/climate.yaml` |
| `automation.yaml` (Auto) | `packages/car/charging.yaml` |
| `script.yaml` (Notifications) | `packages/home/notifications.yaml` |

### Migrations-Schritte

1. Fachliche Domäne identifizieren
2. Existierende Package-Datei prüfen
3. Bei Bedarf neue Datei mit Header anlegen
4. Entität inkl. aller Kommentare verschieben
5. Header mit Version V1.0 ergänzen
6. YAML validieren: `ha core check` oder Developer Tools
7. Nach Reload/Restart testen

**WICHTIG:** `unique_id` und `entity_id` bleiben exakt gleich. Keine Funktionsänderungen während Migration.

## Versionierung von Packages

- **V1.0** Erstanlage
- **V1.x** kleinere Erweiterungen
- **V2.0** strukturelle Änderungen (Split in Sub-Dateien)

```yaml
# Version: V1.3
# Changelog:
#   - V1.3: battery_threshold_alerts hinzugefügt
#   - V1.0: Initiale Erstellung
```

## Troubleshooting

| Problem | Ursache | Lösung |
|---------|---------|--------|
| Package nicht geladen | YAML-Syntax-Fehler | `Developer Tools → Check Configuration` |
| Entitäten doppelt | In Root-Datei UND Package | Root-Datei leeren |
| Anker-Fehler | `&` nach `*` definiert | Anker VOR erste Nutzung verschieben |
| Reload reicht nicht | Neue Domain hinzugefügt | **Full Restart** |

### Debugging

1. `Settings → System → Logs` nach Package-Namen filtern
2. Developer Tools → YAML → Check Configuration
3. Package temporär auskommentieren, schrittweise aktivieren
4. `Developer Tools → States` — Entität vorhanden?
