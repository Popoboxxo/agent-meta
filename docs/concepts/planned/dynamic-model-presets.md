# Konzept: Dynamische Modellerfassung & Tier-Presets

**Status:** Umgesetzt  
**Ziel:** Abkehr von statischen Modell-Zuweisungen hin zu einem dynamischen, preisbewussten und skalierbaren Preset-System.

---

## 1. Matrix-Architektur der Presets

Anstatt Modelle direkt zuzuordnen, entkoppeln wir die **Rollen-Tiers** (`nano`, `fast`, `balanced`, `powerful`, `max`) von den physischen Modellen und nutzen **Presets** als Verschiebungs-Matrix.

Ein Preset definiert, wie die Rollen-Tiers auf die verfügbaren Modell-Klassen gemappt werden. Dies garantiert, dass auch in höheren Presets eine sinnvolle Kostendifferenzierung (Verdünnung) stattfindet, anstatt alles auf das teuerste Modell zu zwingen.

### Die Verschiebungs-Matrix

| Rollen-Tier (Agent) | Preset: Cheap | Preset: Normal | Preset: Advanced | Preset: Expensive | Preset: Expensive as Hell |
|---------------------|---------------|----------------|------------------|-------------------|---------------------------|
| **nano**            | `nano`        | `nano`         | `fast`           | `balanced`        | `powerful`                |
| **fast**            | `nano`        | `fast`         | `balanced`       | `powerful`        | `max`                     |
| **balanced**        | `fast`        | `balanced`     | `powerful`       | `max`             | `max`                     |
| **powerful**        | `fast`        | `powerful`     | `max`            | `max`             | `max`                     |
| **max**             | `balanced`    | `max`          | `max`            | `max`             | `max`                     |

**Erklärung der Matrix:**
- **Cheap:** Flacht die Kurve radikal ab. Selbst starke Agenten (`powerful`) bekommen nur `fast`-Modelle.
- **Normal:** Das 1:1 Mapping (Status Quo).
- **Advanced:** Shifft alles eine Stufe nach oben.
- **Expensive:** Sehr starker Shift. Selbst einfache Skripte (`fast`) laufen auf `powerful`-Modellen.
- **Expensive as Hell:** Fast alle Agenten laufen auf `powerful` oder `max`.

### SE Focus — Boolean-Modifier

SE Focus ist ein **Boolean-Modifier** (`se-focus: true/false` in `project.yaml`), kein separates Preset.

**Verhalten bei `se-focus: true`:** Alle Systems-Engineering-Rollen (`se-architect`, `se-critic`, `se-developer`, `se-integration-and-test-manager`, `se-interface-mgr`, `se-junior-developer`, `se-requirements`, `se-senior-developer`, `se-termination`, `se-test-engineer`, `se-testreviewer`, `se-validator`, `se-verifier`) werden um **eine Tier-Stufe** hochgestuft, **bevor** das Preset-Mapping angewendet wird.

**Beispiel:** Rolle `se-critic` hat Basis-Tier `balanced`. Mit `se-focus: true` → Upgrade auf `powerful`. Danach greift das Preset: Bei `Normal` bleibt `powerful` auf `powerful`. Bei `Cheap` wird `powerful` auf `fast` gemappt.

**Deprecated:** Die `(SE)`-Suffix-Syntax im Preset-Namen (`Normal (SE)`, `Advanced (SE)` etc.) wird nicht mehr unterstützt. Für Rückwärtskompatibilität wird sie bei der Auflösung erkannt und entsprechend behandelt, gilt aber als veraltet. Verwende stattdessen `tier-preset: Normal` + `se-focus: true`.

---

## 2. Auflösungs-Kette (Resolution Chain)

```
role-defaults.yaml
    └─ base_tier (z.B. "balanced")
         │
         ▼  [se-focus: true + se-* Rolle → +1 Tier]
    effective_tier
         │
         ▼  [Preset-Mapping aus config/tier-presets.yaml]
    preset_tier
         │
         ▼  [provider-tier-overrides in project.yaml]
    override_tier (optional)
         │
         ▼  _resolve_tier_to_model()
    konkretes Modell (aus config/ai-providers.yaml → model-tiers)
```

**Schritt für Schritt:**

1. **`base_tier`** — aus `config/role-defaults.yaml` für die jeweilige Rolle.
2. **SE-Upgrade** — wenn `se-focus: true` und Rolle ist eine SE-Rolle → Tier um eine Stufe erhöhen (nano→fast, fast→balanced, balanced→powerful, powerful→max, max→max).
3. **Preset-Mapping** — `config/tier-presets.yaml` wird mit dem aktiven Preset (`tier-preset`) nachgeschlagen. Der `effective_tier` wird auf den im Preset definierten Tier gemappt.
4. **`provider-tier-overrides`** — projektspezifische Overrides in `.meta-config/project.yaml` unter `provider-tier-overrides.<Provider>.<role>` überschreiben den Preset-Tier für einzelne Rollen.
5. **`_resolve_tier_to_model()`** — der resultierende Tier wird über `config/ai-providers.yaml` → `model-tiers` auf das konkrete Modell aufgelöst.

### Modell-Registry — nur für das Pricing Dashboard

`config/model-registry.json` wird **nicht** für die Tier→Modell-Auflösung verwendet. Die Registry dient ausschließlich dem **Pricing Dashboard** in der Admin UI (Kostenübersicht, Sortierung, Context-Window-Anzeige). Die eigentliche Auflösung läuft immer über `config/ai-providers.yaml`.

---

## 3. Dynamische Modell-Erfassung (Crawling)

Das System kann Modelle dynamisch erfassen und in der Registry speichern.

### 3.1 Architektur

- **Modul:** `scripts/lib/model_discovery.py` — Fetcher für Anthropic, Google Gemini API, Opencode-GO.
- **CLI:** `python scripts/sync.py --update-models` löst einen Crawl-Lauf aus.
- **Datenhaltung:** `config/model-registry.json` (generiert, nicht manuell bearbeiten).

### 3.2 Kostendarstellung

- **Metadaten:** Modell-Namen, Context-Window.
- **Pricing-Overlay:** `config/pricing-overlay.yaml` — Basispreise ($ pro 1M Input-/Output-Tokens).
- **Kostenspalte im Dashboard:** "Blended $/1M (30/70)" — Formel: `input_cost * 0.3 + output_cost * 0.7`.

---

## 4. Integration in die Admin UI

### 4.1 Dashboard "Model Discovery & Pricing"

- Sortierbare Tabelle: alle Modelle inkl. Blended-Kosten und Context-Window.
- Crawl-Button: löst `--update-models` aus und aktualisiert `model-registry.json`.

### 4.2 "Project Settings"

- **Preset Selector:** Dropdown mit den 5 Basis-Presets (Cheap / Normal / Advanced / Expensive / Expensive as Hell). SE-Variants (`(SE)`-Suffix) werden nicht mehr als eigenständige Einträge angeboten.
- **SE Focus Toggle:** Separater Boolean-Schalter für SE-Tier-Upgrade.
- **Live-Matrix-Vorschau:** Zeigt die konkreten Modelle für alle aktiven Rollen.

---

## 5. Konfigurationsreferenz

```yaml
# .meta-config/project.yaml

tier-preset: Normal          # Eines von: Cheap | Normal | Advanced | Expensive | Expensive as Hell
se-focus: true               # Optional: SE-Rollen um eine Tier-Stufe hochstufen

provider-tier-overrides:     # Optional: Einzelne Rollen gezielt übersteuern
  Claude:
    orchestrator: powerful
    junior-developer: nano
```
