# YAML Code-Konventionen & Versionierung

## Standardisierter YAML-Header

Jeder YAML-Block MUSS folgenden Kommentar-Header besitzen:

```yaml
# [Pfad/Dateiname, falls bekannt]
# ------------------------------------------------------------------------------
# [MODUL NAME] [VERSION Vx.y]
# Architect: HA Expert 2.0
# Changelog:
#   - Vx.y: [Kurze Beschreibung der technischen Änderung]
#   - Vx.y: [Weiterer Punkt]
# ------------------------------------------------------------------------------
```

## Versions-Logik

- Nutze einen **Namenszusatz (Postfix)** zur Darstellung der Versionen
- Erhöhe **y (Minor)** bei Bugfixes oder kleinen Anpassungen (V1.1 → V1.2)
- Erhöhe **x (Major)** bei Architekturwechseln oder Breaking Changes
- **Ziel**: User muss sofort erkennen, wer spricht und was sich geändert hat

## KRITISCHE ID-REGEL: Immutable vs. Mutable

### Immutable IDs (NIEMALS Versionsnummern!)

- `unique_id`
- `entity_id`
- `automation id`

Diese sind **statische System-Slugs** und dürfen NIEMALS eine Versionsnummer, ein Datum oder dynamische Werte enthalten!

**VERBOTEN**: `unique_id: binary_sensor_rain_fusion_state_v1`
**VERBOTEN**: `id: "notify_rain_started_fusion_v1"`
**VERBOTEN**: `entity_id: automation.washing_machine_logic_v1`

**KORREKT**: `id: "notify_rain_started_fusion"` (stabil, immer!)

### Mutable Metadata (Versionsnummern erlaubt)

Nur `alias` oder `friendly_name` dürfen Versionsnummern enthalten:

**KORREKT**: `friendly_name: "Fenster Snooze [V3.3]"` (Fürs UI)
**KORREKT**: `alias: "Waschmaschine Logik [V2.1]"`

**Validation**: Vor Code-Ausgabe prüfen: Enthält ein Feld mit 'id' im Key eine Zahl am Ende? → **Löschen!**

## Dokumentation & Code-Kommentare

**REGEL**: Verwende immer vorhandene Code/Kommentare weiter bzw. verbessere sie im Zweifelsfall.
**WICHTIG**: Generierter Code darf **niemals weniger Kommentare** beinhalten als Input-Code!
