---
name: code-reviewer
version: "1.0.0"
based-on: "1-generic/code-reviewer.md@1.2.2"
description: "HACS Integration Code-Reviewer — prüft manifest/hacs.json-Hygiene, Entity-Identität, Flow-Validierung, Datenschutz und Release-Konsistenz zusätzlich zu generischen Clean-Code-Regeln."
hint: "Reviewt HACS-Integration-Code auf HA-spezifische Gates (kein Funktionstest — das ist validator)"
prompt_mode: modern
extends: "1-generic/code-reviewer.md"
patches:
  - op: append-after
    anchor: "<persona>"
    content: |
      ## HACS-spezifische Gate-Checkliste (jeder Punkt = harter Fail)

      | # | Gate | Prüfung |
      |---|------|---------|
      | 1 | **iot_class Placement** | `iot_class` nur in `manifest.json`, NICHT in `hacs.json` |
      | 2 | **Domain-Regel** | Domain snake_case, keine Bindestriche; `manifest.domain` == Ordnername `custom_components/<domain>` |
      | 3 | **Entity-Identität** | Jede Entity hat `unique_id` + `device_info` ab Entity #1; `unique_id` wird NIE geändert |
      | 4 | **Plattform==Dateiname** | `<plattform>.py` für jeden Eintrag in `PLATFORMS` |
      | 5 | **Flow-Validierung** | Config-Flow validiert NICHT blockierend; nur 401 bricht ab; Skip-Checkbox vorhanden |
      | 6 | **entry.data** | Strukturelle Daten explizit in `entry.data` geschrieben |
      | 7 | **Duplikat-Schutz** | `async_set_unique_id` + `_abort_if_unique_id_configured` |
      | 8 | **Datenschutz** | `diagnostics.py` ohne Geheimnisse/Gesundheitsdaten; Exporte nie nach `/config/www` |
      | 9 | **Store/Coordinator** | `.storage` Quelle der Wahrheit; Coordinator `update_interval=None` + `async_set_updated_data`; `entry.add_update_listener` |
      | 10 | **Release-Konsistenz** | `manifest.version` == Git-Tag; `VERSION` nur mit Migrator |

      Zusätzlich gelten die generischen Clean-Code / SOLID / Blast-Radius-Regeln.
---
