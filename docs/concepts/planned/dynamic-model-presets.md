# Konzept: Dynamische Modellerfassung & Tier-Presets

**Status:** Geplant  
**Ziel:** Abkehr von statischen Modell-Zuweisungen hin zu einem dynamischen, preisbewussten und skalierbaren Preset-System.

---

## 1. Matrix-Architektur der Presets (Verfeinerte Analyse)

Anstatt Modelle direkt zuzuordnen, entkoppeln wir die **Rollen-Tiers** (`nano`, `fast`, `balanced`, `powerful`, `max`) von den physischen Modellen und nutzen **Presets** als Verschiebungs-Matrix. 

Ein Preset definiert, wie die Rollen-Tiers auf die verfügbaren Modell-Klassen gemappt werden. Dies garantiert, dass auch in höheren Presets eine sinnvolle Kostendifferenzierung (Verdünnung) stattfindet, anstatt alles auf das teuerste Modell zu zwingen.

### Die Verschiebungs-Matrix

| Rollen-Tier (Agent) | Preset: Cheap | Preset: Normal | Preset: Advanced | Preset: Expensive | Preset: Expensive as Hell |
|---------------------|---------------|----------------|------------------|-------------------|---------------------------|
| **nano**            | `nano`        | `nano`         | `fast`           | `balanced`        | `powerful`                |
| **fast**            | `nano`        | `fast`         | `balanced`       | `powerful`        | `max`                     |
| **balanced**        | `fast`        | `balanced`     | `powerful`       | `max`             | `max`                     |
| **powerful**        | `fast`        | `powerful`     | `max`            | `max`             | `ultra` (Zukunft)         |
| **max**             | `balanced`    | `max`          | `max`            | `max`             | `ultra` (Zukunft)         |

**Erklärung der Matrix:**
- **Cheap:** Flacht die Kurve radikal ab. Selbst starke Agenten (`powerful`) bekommen nur `fast`-Modelle. Nur absolute `max`-Agenten bekommen ein `balanced`-Modell. Hier greift die "super billig" Regel.
- **Normal:** Das 1:1 Mapping (Status Quo).
- **Advanced:** Shifft alles eine Stufe nach oben. Der Orchestrator (`balanced`) läuft jetzt auf `powerful`, der Developer (`powerful`) auf `max`.
- **Expensive:** Sehr starker Shift. Selbst einfache Skripte (`fast`) laufen auf `powerful`-Modellen. Die Verdünnung bleibt aber erhalten (nano bekommt nicht sofort max).
- **Expensive as Hell:** Fast alle Agenten laufen auf `powerful` oder `max`. Vorbehalten für hochkomplexe, unlimitierte Phasen.

### Die "SE Focus" Varianten
Für jedes Preset existiert eine `(SE)` Variante (z.B. `Normal (SE)`).
*Logik:* Wendet das gewählte Preset regulär auf alle Agenten an, jedoch werden **alle Systems-Engineering Rollen** (`se-architect`, `se-critic`, etc.) innerhalb der Matrix künstlich um 1-2 Tiers nach oben gestuft, bevor sie durch das Preset aufgelöst werden.

---

## 2. Dynamische Modell-Erfassung (Crawling)

Das System liest die Modelle nicht mehr starr aus `ai-providers.yaml`.

### 2.1 Architektur-Erweiterung
- **Neues Modul:** `scripts/lib/model_discovery.py`
  - Fetcher für Anthropic, Google Gemini API, Opencode-GO.
- **CLI-Erweiterung (`sync.py`):**
  - Parameter: `python scripts/sync.py --update-models`
- **Datenhaltung:**
  - Automatisiert generierte Registry: `config/generated/model-registry.json`.

### 2.2 Kostenfaktor-Analyse (Cost Tracking)
- **Metadaten-Crawling:** Modell-Namen, Context-Window.
- **Pricing-Overlay:** In `config/pricing-overlay.yaml` werden Basispreise ($ pro 1M Input/Output Tokens) gepflegt, da APIs diese oft nicht mitliefern.
- **Kostenfaktor-Berechnung:** 
  `CostFactor = (InputCost * 0.3) + (OutputCost * 0.7) * 100` 
  Wird als normalisierter Score von 1-100 im System geführt.

---

## 3. Integration in die Admin UI (`admin-server.py`)

### 3.1 Neues Dashboard: "Model Discovery & Pricing"
- **Sortierbare Tabelle:** Zeigt alle dynamisch geladenen Modelle inkl. Cost Factor und Context Window.
- **Crawl-Button:** Führt einen API-Sync durch und aktualisiert `model-registry.json`.
- **Heatmap:** Visuelle Darstellung der Kostenfaktoren.

### 3.2 "Project Settings" Menü
- **Preset Selector:** Dropdown zur Auswahl des Presets (z.B. "Advanced (SE)").
- **Live-Matrix-Vorschau:** Zeigt, welche konkreten Modelle durch das gewählte Preset dem Orchestrator, Developer und Architect zugewiesen werden.

---

## 4. Machbarkeits- und Umsetzungsbewertung (Self-Evaluation)

**Bewertung: Vollumfänglich umsetzbar (High Feasibility)**

Das gesamte System kann von mir (Antigravity/Agent) vollständig und autonom in dieses Repository implementiert werden.

**Begründung der Machbarkeit:**
1. **Python / `sync.py`:** Die Entkopplung der Resolution-Logik in `scripts/lib/agents.py` und das Hinzufügen des CLI-Flags in `sync.py` ist eine gut abgegrenzte Standard-Refactoring-Aufgabe.
2. **API Clients (`model_discovery.py`):** Das Schreiben der Fetcher für die Provider ist trivial. Die Credentials liegen bereits im System und können für die Requests an die Model-Endpoints verwendet werden.
3. **Admin UI (`admin-server.py`):** Da es sich um einen lokalen Python-Webserver mit HTML/JS-Frontend handelt, können die neuen Routen (GET `/api/models`, POST `/api/models/update`) und die Frontend-Komponenten nahtlos in die bestehende Architektur eingefügt werden.
4. **Konfiguration:** Das Anlegen von `config/tier-presets.yaml` und `config/pricing-overlay.yaml` erfordert keine externen Abhängigkeiten und lässt sich sauber integrieren.

**Fazit:** Sobald der Befehl zur Umsetzung erteilt wird, kann das Feature in einem Feature-Branch (gemäß Rule `Branch-Guard`) end-to-end (Frontend + Backend + CLI) umgesetzt werden.
