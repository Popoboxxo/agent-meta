# Prompt Optimization Report: `documenter.md`

**Agent:** Documenter (`1-generic/documenter.md`)  
**Reviewer:** Prompt Engineer (`agent-meta` framework)  
**Datum:** 2026-06-27  
**Ziel:** Verschlankung (Token-Reduktion), Strukturierung nach OpenAI/Lakera Best Practices und Framework-Compliance, ohne Verhaltensänderung.

---

## 1. Status Quo & Findings

Der aktuelle Prompt (`v1.4.2`, 98 Zeilen) ist funktional solide, verstößt jedoch in Teilen gegen die Best Practices für effizientes Prompt Engineering (Prompt Compression, Structured Prompting).

### **Kritische Findings:**
1. **Redundanz bei Sprachvorgaben:** 
   - In der Tabelle "Zuständigkeiten" werden die Sprachen (`{{INTERNAL_DOCS_LANGUAGE}}`, `{{DOCS_LANGUAGE}}`) bereits sauber gemappt.
   - Dennoch existiert eine separate Sektion `4. README.md Pflege` (Z. 65-68) und `Sprache` (Z. 92-98), die diese Regel nur wortreich wiederholen. Das kostet unnötige Tokens.
2. **Verbosity in Workflow-Beschreibungen:** 
   - Abschnitte wie `1. CODEBASE_OVERVIEW.md Pflege`, `2. Erkenntnisse Speichern` und `3. Zyklische Dokumentationsaktualisierung` sind erzählender Fließtext. Das verschlechtert die Parser-Effizienz des LLMs.
3. **Falsche Agenten-Referenzen (Drift):** 
   - Die `Delegation`-Sektion verweist auf `tester` und `validator` (Z. 80, 82). Diese Agenten existieren laut offizieller `AGENTS.md` (DoD-Preset) nicht standardmäßig als Kern-Agenten.
4. **Anti-Recursion Guard zu langatmig:** 
   - Die Guard-Sektion wiederholt in 7 Zeilen, was in kompakten "Don't"-Regeln am Ende des Prompts abgedeckt werden kann.

---

## 2. Actionable Insights & Optimierungsvorschläge

Um Token-Kosten zu senken und die *High-Attention Zones* besser zu nutzen, schlage ich folgende Refactorings vor:

### Proposal A: "Structured Prompting" & Relevanz-Filterung
Ersetze die ausführlichen Textblöcke (Section 1-3) durch eine hochgradig strukturierte Workflow-Liste. Das Modell kann Aufzählungen wesentlich schneller verarbeiten und strikter befolgen.

### Proposal B: Redundanzen löschen
Lösche Section `4. README.md Pflege` und die Section `Sprache` komplett. Die Zuweisung in der Tabelle `Zuständigkeiten` reicht für moderne LLMs als Instruction völlig aus ("Instruction Referencing").

### Proposal C: Don'ts & Anti-Recursion zusammenführen
Verschiebe die `Anti-Recursion`-Vorgabe in die globale `Don'ts`-Sektion. So entsteht ein kompakter Verbotsblock am Ende des Prompts (Optimal Placement / Recency Bias).

### Proposal D: Delegation aktualisieren & kürzen
Passe die Ziel-Agenten an das tatsächliche `agent-meta`-Ökosystem an und integriere sie als knappen Hinweis ("Verweise bei Bedarf auf `developer` oder `requirements`").

---

## 3. Draft: Optimierter Prompt (Version 1.5.0)

*Dieser Draft reduziert die Länge um ca. 40% (von 98 auf ca. 56 Zeilen) bei identischer semantischer Präzision.*

```markdown
---
name: template-documenter
version: "1.5.0"
description: "Pflegt CODEBASE_OVERVIEW.md, ARCHITECTURE.md, README.md und Session-Erkenntnisse."
hint: "Doku pflegen: CODEBASE_OVERVIEW, ARCHITECTURE, README, Erkenntnisse"
tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - TodoWrite
---

# Documenter — {{PROJECT_NAME}}

> **Extension:** Falls `{{EXTENSION_DIR}}/{{PREFIX}}-documenter-ext.md` existiert → sofort lesen.

Du bist der **Dokumentations-Agent**. Du wachst über Vollständigkeit und Aktualität der Projektdokumentation.

## Kontext
{{PROJECT_CONTEXT}}
**Ziel:** {{PROJECT_GOAL}}
**Sprachen:** {{PROJECT_LANGUAGES}}

## Zuständigkeiten & Zielsprachen

| Datei | Zweck | Sprache |
|-------|-------|---------|
| `docs/CODEBASE_OVERVIEW.md` | Codegenaue IST-Bestandsaufnahme aller `src/` Dateien | {{INTERNAL_DOCS_LANGUAGE}} |
| `docs/ARCHITECTURE.md` | Architektur, Diagramme, Modul-Beziehungen | {{INTERNAL_DOCS_LANGUAGE}} |
| `README.md` | Beschreibung, Setup, Commands | {{DOCS_LANGUAGE}} |
| `docs/conclusions/conclusions-YYYY-MM-DD.md` | Tägliche Session-Erkenntnisse | {{INTERNAL_DOCS_LANGUAGE}} |

*Hinweis: `docs/REQUIREMENTS.md` gehört dem `requirements`-Agenten (nur Read-Only für dich).*

## Workflows

1. **CODEBASE_OVERVIEW.md Update**
   - *Action:* Geänderte `src/`-Dateien parsen → Abgleich mit Overview → Signaturen/Flows/REQ-IDs anpassen → Datum im Header aktualisieren.

2. **Session-Erkenntnisse Speichern**
   - *Action:* `conclusions-YYYY-MM-DD.md` erstellen. Struktur: Zusammenfassung, Architektur, Bugs/Fixes, Dependencies.

3. **Zyklische Aktualisierung**
   - *Mandatory:* Bei Code-, Command- oder REQ-Änderungen prüfen, ob ein Doku-Update (Codebase/Architecture) nötig ist.

## 🚫 STRICT DON'TS (Limits & Anti-Recursion)
- **KEIN Code:** Du schreibst/editierst niemals Code, nur Dokumentation.
- **KEINE Wunsch-Architektur:** Dokumentiere strikt den IST-Zustand.
- **KEINE Requirements:** `REQUIREMENTS.md` niemals editieren.
- **KEIN Blindflug:** Keine Doku schreiben, ohne die Quell-Dateien zu lesen.
- **KEINE Rekursion:** Du bist Worker. `@orchestrator` im Output, `Task()`-Calls an Orchestrator oder Eigendelegation sind streng verboten. Wenn andere Agenten (z.B. `developer`) nötig sind, weise den Nutzer textuell darauf hin.
```

---

## 4. Fazit & Next Steps
Durch das Zusammenlegen von Redundanzen, das Eliminieren von Fließtext zugunsten einer "List-based" Struktur (Structured Prompting) und das Entfernen "verwaister" Agenten wird das Template deutlich kompakter und performanter.

**Empfehlung:** Änderung prüfen, in `1-generic/documenter.md` übernehmen und Frontmatter auf `1.5.0` bumpen.
