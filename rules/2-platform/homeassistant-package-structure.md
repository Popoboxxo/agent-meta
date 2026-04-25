# Package-Struktur & Fachliches Clustering

## Oberste Direktive: Modularisierung

Konfigurationen werden **NIEMALS** monolithisch in Root-Dateien geschrieben, sondern modular in thematische Packages aufgeteilt.

## Package-Struktur (`/config/packages/`)

```
abstraction/   # Abstraktionsschichten (energy_power.yaml)
bsm/           # Batterie-/Speicher-Management
car/           # Auto (Ladung, Fahrzeug-APIs)
fitness/       # Fitness & Gesundheits-Tracking
grid/          # Stromnetz, Spotpreise
heating/       # Heizungs-Steuerung
home/          # Kernfunktionen (climate, window_monitoring, air_quality)
home_appliances/ # Haushaltsgeräte
location/      # Präsenz, GPS, Zonen
mining/        # Krypto-Mining
report/        # Reporting & Statistiken
solar/         # Solar (dtu, solarforecast, solarmanager)
weather/       # Wetter
```

## Grundprinzipien

- **Ein Package = Eine Fachdomäne**, ein File = ein Sub-Thema
- **Keine Root-Dateien** — bleiben leer oder `!include_dir_merge_list packages/`
- **Self-Contained** — jedes Package isoliert verstehbar

## Datei-Struktur (Pflicht-Header)

```yaml
# ==============================================================================
# PACKAGE: [Domain] - [Sub-Thema]
# Beschreibung: [1-2 Sätze]
# Dependencies: [Integrationen]
# ==============================================================================
# Input Helpers → Template Sensors → Automations → Scripts → Scenes
```

## Wann neue Datei / neues Package?

Neue **Datei**: Sub-Thema neu, bestehende Datei >500 Zeilen, Sub-Thema mit 5+ Entitäten.
Neues **Package**: Neue Hauptdomäne, mind. 2–3 YAML-Dateien erwartet, unabhängig von anderen.

## Naming

| Typ | Schema | Beispiel |
|-----|--------|---------|
| Hauptfunktion | `[domain].yaml` | `climate.yaml` |
| Hardware | `[hardware].yaml` | `dtu.yaml` |
| Funktion | `[fn]_[obj].yaml` | `window_monitoring.yaml` |

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| Package nicht geladen | `Developer Tools → Check Configuration` |
| Entitäten doppelt | Root-Datei leeren |
| Reload reicht nicht | Full Restart (neue Domain hinzugefügt) |
