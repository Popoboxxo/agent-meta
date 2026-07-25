# Konzept: Modulare Context-Templates (Erweitert)

Dieses Konzept beschreibt, wie wir die Markdown-Bausteine des Frameworks aus dem Python-Code (`scripts/lib/`) extrahieren und in logische, wiederverwendbare Abschnitte zerlegen. Die Versionierung übernimmt nativ Git, sodass wir auf umständliche `v1/`-Ordner verzichten.

## 1. Verzeichnisstruktur (Flach & Modular)
Alle Inline-Strings und Templates wandern in ein klares `templates/context/`-Verzeichnis.

```text
templates/
├── context/
│   ├── partials/
│   │   ├── header.md                  # Metadaten, DoD-Preset
│   │   ├── ... (weitere Partials wie agents-table, rules-embedded, etc.)
│   │
│   ├── claude-managed.md              # Manifest für CLAUDE.md
│   ├── agents-managed.md              # Manifest für AGENTS.md (Opencode/Gemini)
│   └── extensions-managed.md          # Manifest für *-ext.md Dateien
│
├── knowledge/
│   ├── index-init.md                  # Init-Template für "Knowledge Index"
│   └── log-init.md                    # Init-Template für "Knowledge Log"
│
├── env/
│   ├── env-setup.sh                   # Template für env.sh (Shell-Skript)
│   └── env-unset.sh                   # Template für env.unset.sh
│
├── mcp/
│   ├── secrets-boilerplate.yaml       # Template für generierte mcp-secrets.yaml
│   └── mcp-docs-header.md             # Template für die MCP-Dokumentation
│
├── setup/
│   └── project-yaml-init.yaml         # Template für das Initial-Setup (--setup)
│
└── se_export/
    ├── index.md                       # Manifest für den Systems-Engineering Export Index
    ├── hierarchy.md                   # Partial für die Hierarchie
    └── interface.md                   # Partial für Interfaces
```

## 2. Umfassende Fundstellen im Code (Die "Grand Extraction")
Die tiefergehende Analyse *aller* Python-Dateien im Framework hat gezeigt, dass Inline-Strings ein systemweites Muster sind. Folgende Module werden von hardcodierten Strings befreit und auf die neue Template-Engine umgestellt:

1. **`scripts/lib/agents.py`**:
   - Baut riesige Sektionen wie `## Knowledge Engine`, `## Critical Rules` und `## Singleton-Regel: Orchestrator-Spawn` komplett als String zusammen.
2. **`scripts/lib/extensions.py` & `bootstrap.py`**:
   - Injizieren Strings wie `## Projektspezifische Erweiterungen` und `## Agent Bootstrap`.
3. **`scripts/lib/knowledge.py`**:
   - Generiert die initiale `index.md` und `log.md` Struktur (`"# Knowledge Index\n\n"`).
4. **`scripts/lib/mcp.py`**:
   - Enthält die langen Boilerplate-Kommentare für `mcp-secrets.yaml` (z.B. `"# NIEMALS committen. Diese Datei ist gitignored."`) und MCP Markdown-Docs (`"# MCP: {server_name}"`).
5. **`scripts/lib/env.py`**:
   - Baut die Bash-Skripte `env.sh` und `env.unset.sh` inklusive langer Erklär-Header zusammen.
6. **`scripts/lib/setup.py`**:
   - Generiert die initiale `project.yaml` für den User aus einem fest verdrahteten Python-String.
7. **`scripts/lib/se_export/markdown_adapter.py`**:
   - Baut die kompletten Systems-Engineering Markdown-Exporte (`# SE Export Index`, `## Hierarchy`, `# Interface: {name}`) ausschließlich über Python String-Konkatenation auf.

## 3. Strukturiertes Datenformat (Markdown + YAML Frontmatter)
Reine `.md`-Dateien sind oft zu starr, da ihnen Kontext und Meta-Informationen fehlen. Da `agent-meta` bereits exzellent mit YAML-Frontmatter umgehen kann (siehe Agent-Definitionen), nutzen wir dieses Pattern auch für die Templates!

Jedes Manifest und Partial ist eine Markdown-Datei **mit YAML Frontmatter**. So kombinieren wir die perfekte Syntax-Hervorhebung für Text mit harten, strukturierten Daten.

**Beispiel-Manifest (`agents-managed.md` für Opencode):**
```markdown
---
name: "Opencode Context Manifest"
description: "Haupt-Manifest für den AGENTS.md Build"
target_file: "AGENTS.md"
requires_capabilities: []
---
<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py. Manual changes will be overwritten. -->

{{> header }}
{{> agents-location }}
{{> agents-table }}
{{> knowledge-engine-hints }}

{{#if HAS_NATIVE_RULES}}
{{> rules-pointer }}     <!-- Falls der Provider Regeln nativ kann -->
{{else}}
{{> rules-embedded }}    <!-- Kompiliert die echten Regeln hier rein (z.B. Opencode) -->
{{/if}}

{{> footer }}
```

**Beispiel-Partial (`header.md`):**
```markdown
---
name: "Standard Header"
description: "Generiert den Metadaten-Kopfbereich (DoD, Version)"
---
Generiert von agent-meta v{{AGENT_META_VERSION}} — `{{AGENT_META_DATE}}`
DoD-Preset: **{{DOD_PRESET}}** | REQ-Traceability: {{DOD_REQ_TRACEABILITY}}
```

### A. Provider-Spezifische Manifeste vs. Agnostische Partials
Die Manifest-Dateien (mit Metadaten wie `target_file`) definieren den Aufbau pro Provider. Die ausgelagerten Partials (`header.md`, `agents-table.md`) sind dumme, wiederverwendbare Bausteine (mit eigenen Metadaten für den Syncher).

### B. ADR: Warum Markdown + Frontmatter? (Performance & DX)
**Entscheidung:** Wir nutzen Markdown mit YAML-Frontmatter anstelle nativer YAML/JSON-Dateien für textlastige Templates.
**Begründung (Performance):** Das Parsen ist *schneller* als bei reinem YAML. Python splittet den String via `split('---', 2)` in Mikrosekunden. `PyYAML` muss nur den winzigen, 5-zeiligen Header evaluieren, während der oft Hunderte Zeilen lange Body als roher String verbleibt. Reines YAML müsste jede Zeile des riesigen Bodys auf Einrückungen und Escapes prüfen.
**Begründung (DX):** Native Editoren (VS Code, Cursor) bieten für `.md`-Dateien volles Syntax-Highlighting und Autocomplete für Links. JSON erfordert mühsames Escaping (`\n`), reines YAML verliert das Markdown-Highlighting.

## 4. Konfiguration & Override-Hierarchie
Wie bei den Agenten-Definitionen greift auch bei den Templates das Schichten-Modell. Konfigurationen und Layouts können auf Projektebene überschrieben werden:

1. **Framework Defaults (agent-meta):**
   Der Basis-Satz an Templates liegt fest in `.agent-meta/templates/`.
2. **Project Settings (Override im Zielprojekt):**
   Will ein Projekt z.B. einen völlig anderen `header.md` nutzen, legt es die Datei in `.meta-config/templates/partials/header.md` ab. Der `TemplateBuilder` bevorzugt immer lokale Overrides gegenüber den Framework-Defaults.
3. **Template-Steuerung via Konfiguration:**
   In der `project.yaml` können Manifeste konfiguriert werden (z. B. `context_template: custom-managed.md`). Eine zukünftige Admin-UI kann so per Dropdown oder Toggle steuern, welches Wording oder Manifest ein Projekt verwendet.

## 5. Strategie zur extremen Verschlankung (Kompaktierung ohne Qualitätsverlust)
Das Ziel ist es, Monsterdateien wie `AGENTS.md` (aktuell ~860 Zeilen) auf ~150 Zeilen zu schrumpfen, **ohne** dass das LLM an Kontext oder Handlungsfähigkeit einbüßt. Dies erreichen wir durch aggressive, zielgerichtete Kompaktierung auf Template- und Datenebene:

### A. Verschlankung der Agenten-Tabelle
- **Problem:** Aktuell sind die Agenten-Beschreibungen oft ganze Romane (z.B. SE-Agenten).
- **Lösung:** Wir führen in der YAML-Frontmatter der Agenten ein neues Feld `short_desc` ein oder nutzen einen radikalen Kürzungsalgorithmus, der nur noch **Keywords und Core-Capabilities** rendert.
- **Beispiel (Alt):** `Accessibility-Audit: WCAG 2.1/2.2, ARIA, Keyboard-Nav, Screenreader-Guidelines, Kontrast, Focus-Management, A11y-Tree — Findings mit A/AA/AAA-Severity`
- **Beispiel (Kompakt):** `Accessibility-Audit (WCAG, ARIA, Keyboard, A11y-Tree)` -> Das LLM weiß ohnehin, was das bedeutet!

### B. Nativ kompakte Rule-Definitionen (Statt Parser-Magie)
- **Problem:** Bisher schreiben wir ausufernde Regeln mit langen Erklärungen ("Warum tun wir das?") und versuchen diese dann mühsam per Python-Parser (`_condense_rule_content`) wieder zusammenzukürzen.
- **Lösung:** Wir streichen die Parser-Magie! Stattdessen werden die **Quell-Regeln in `.agent-meta/rules/` direkt extrem kompakt formuliert**. Kein Fließtext, nur noch harte Imperative, Tabellen und Bullet-Points.
- **Ergebnis:** Der Python-Syncher muss nichts mehr "strippen". Das senkt die Fehleranfälligkeit auf null. Wenn Menschen Erklärungen brauchen, lagern wir das "Warum" in separate Doku-Dateien (z.B. in ein Wiki) aus, die dem LLM gar nicht erst übergeben werden. Die Regeln selbst sind zu 100% LLM-optimiert.

### C. Entfernung von "Human-Readability" Bloat
- Markdown-Tabellen-Padding (Spaces) wird minimiert.
- Leere Zeilen werden auf ein absolutes Minimum reduziert.
- Lange Disclaimer-Texte ("Generiert von...") wandern komprimiert in eine einzige Zeile in den Header.

## 6. Konkrete Partials & Kompressionen (Beispiele)
Um die extreme Verschlankung greifbar zu machen, hier die konkreten Entwürfe, wie die neuen Partials aussehen werden:

### Partial: `header.md`
**Bisher:** Langer Erklärungstext über Routing, Projektbeschreibung, Meta-Infos.
**Neu (Extrem komprimiert):**
```markdown
---
name: "Standard Header"
description: "Metadaten-Kopfbereich"
---
> **ROUTING:** Claude->CLAUDE.md | Opencode->AGENTS.md | Gemini->GEMINI.md
> **ENTRY:** `orchestrator`-Agent (für alle Dev-Tasks).
`agent-meta v{{AGENT_META_VERSION}}` | DoD: `{{DOD_PRESET}}` | REQ-Trace: `{{DOD_REQ_TRACEABILITY}}`
```

### Partial: `agents-location.md`
**Bisher:** Mehrzeiliger Text mit Erklärungen, wie man Agenten aufruft.
**Neu:**
```markdown
---
name: "Agent Location Hint"
---
**Agents:** `.{{PROVIDER_LOWER}}/agents/` (Invoke by name).
```

### Nativ kompakte Regel: `singleton-rule.md`
**Bisher (AGENTS.md):** 11 Zeilen mit fetten Überschriften, Bullet-Points, langer Markdown-Tabelle und Erklärungen zum Verstoß.
**Neu (Nativ gestrippt in `.agent-meta/rules/`):**
```markdown
# Singleton-Regel
`orchestrator` DARF NUR vom `main_chat` (depth=0) gestartet werden.
Worker (depth>=2) -> HARD REJECT + User-Info (Keine Exceptions).
```

### Nativ kompakte Agent-Beschreibung (In `agents-table.md`)
**Bisher:** `| accessibility-specialist | Accessibility-Audit: WCAG 2.1/2.2, ARIA, Keyboard-Nav, Screenreader-Guidelines, Kontrast, Focus-Management, A11y-Tree — Findings mit A/AA/AAA-Severity |`
**Neu (Via `short_desc`):** `| accessibility-specialist | A11y-Audit (WCAG, ARIA, Keyboard, A11y-Tree) |`

## 7. Saubere Daten-Auflösung (Pre-Resolved Data Structures)
Bisher bauen Skripte wie `delegation_table.py` aktiv Markdown-Tabellen zusammen und streuen dabei oft interne Konfigurationsbegriffe (wie Modell-Tiers `balanced`, `powerful` oder Parallelitäts-Labels `✅ (Multi-Aspekte)`) in den finalen Text, was das LLM unnötig verwirrt.

**Die Lösung: Trennung von Daten (Python) und Präsentation (Template)!**
Anstatt einen fertigen Markdown-String zu erzeugen, baut Python nur noch eine saubere, vor-aufgelöste Datenstruktur (z. B. eine Liste von Dictionaries aller *aktiven* Agenten) und übergibt diese an die Template-Engine. 

Das Template entscheidet dann, welche Spalten das LLM überhaupt sehen muss:

**Python (Daten-Layer):**
```python
# context.py übergibt saubere Daten an den Builder
variables['active_agents'] = [
    {"name": "orchestrator", "short_desc": "Einstiegspunkt für ALLE Dev-Tasks"},
    {"name": "developer", "short_desc": "Feature-Implementierung nach REQ-IDs"},
    # ...
]
```

**Template (`agents-table.md`):**
```markdown
| Agent | Zuständigkeit |
|-------|--------------|
{{#each active_agents}}
| `{{name}}` | {{short_desc}} |
{{/each}}
```

**Ergebnis:** Das System macht sich zur Laufzeit (im LLM-Prompt) keine Gedanken mehr über `balanced` oder Plattform-Flags. Alle Metadaten wurden bereits von Python bewertet, gefiltert und als extrem saubere Liste in das Template gegossen!

## 8. Die Assembly-Logik (Der "Builder")
Das riesige `context.py` und Teile von `agents.py` werden entschlackt. Wir bauen einen zentralen `TemplateBuilder` in `scripts/lib/context_templates/builder.py`.

**Ablauf beim Sync:**
1. Der Builder liest das Manifest (z. B. `agents-managed.md`) und parst das **YAML-Frontmatter**.
2. Anhand der Metadaten weiß der Builder, wie und wo die Datei gerendert werden soll.
3. Er sucht nach `{{> (.*?) }}` und lädt die entsprechenden Partials (und parst ebenfalls deren Frontmatter für Validierungen).
4. Er evaluiert die `{{#if}}`-Ausdrücke anhand der Provider-Capabilities.
5. Dynamische Inhalte werden durch den existierenden Variable-Substitutor verarbeitet.
6. Das fertige Konstrukt wird ins Zielprojekt geschrieben.

## 9. Dynamische Feature-Flags & Sauberkeits-Garantie (Purging)
Ein Kern-Feature der Template-Engine ist die strikte Einhaltung der Projekt-Konfiguration (`project.yaml`).

### A. Dynamisches Rendering (Nichts Veraltetes lesen)
Wenn ein Provider (z.B. Opencode) deaktiviert wird, darf er nirgendwo mehr erwähnt werden. Wir lösen harte Strings wie `Claude->CLAUDE.md | Opencode->AGENTS.md` durch konditionale Blöcke auf:

**Template (`header.md`):**
```markdown
> **ROUTING:**
{{#if PLATFORM_CLAUDE}} Claude->CLAUDE.md |{{/if}}
{{#if PLATFORM_OPENCODE}} Opencode->AGENTS.md |{{/if}}
{{#if PLATFORM_GEMINI}} Gemini->GEMINI.md{{/if}}
```
*Ergebnis:* Ist Opencode nicht in der Konfig, rendert das Template diesen Namen nicht. Die Dateien bleiben zu 100% konsistent zur echten Konfiguration.

### B. Clean Purging (Bereinigung nach Deaktivierung)
Das System stellt sicher, dass Deaktivierungen restlos umgesetzt werden:
1. **Verwaiste Texte verschwinden:** Da die Templates bei jedem Sync neu aus den `PLATFORM_`-Variablen generiert werden, verschwinden Provider-Verweise automatisch aus *allen* verbleibenden Dateien (z.B. aus der `CLAUDE.md`).
2. **Artefakte werden gelöscht:** Der bestehende `cleanup_legacy_files`-Mechanismus in `sync.py` wird darauf trainiert, nicht nur veraltete Agenten zu löschen, sondern die gesamte Managed-Context-Datei (z.B. `AGENTS.md`) zu entfernen, wenn die Plattform aus der `project.yaml` entfernt wurde.

## 10. Vorteile
* **Wartbarkeit:** Alle Markdown-Texte liegen endlich als echte Markdown-Dateien vor.
* **Weniger Code-Spaghetti:** Die Python-Dateien müssen keine Überschriften (`##`) und Zeilenumbrüche (`\n\n`) mehr konkatenieren. Die aufwändige `_condense_rule_content`-Funktion und hartcodierte Tabellen in `delegation_table.py` verschwinden komplett.
* **Strikte MVC-Trennung:** Python berechnet nur noch die Daten (welche Agenten sind aktiv?). Das Markdown-Template (die View) bestimmt, wie die Tabelle aussieht.
* **Provider-Spezifische Flexibilität:** Über Manifest-Dateien lässt sich der Aufbau pro Provider leicht umstrukturieren, ohne Python-Logik zu berühren.
* **Customizing:** Zielprojekte können einzelne Partials überschreiben, ohne den gesamten generierten Block zu verlieren.
* **Token-Effizienz:** Die Dateien werden winzig klein, sparen massiv Kontext-Fenster-Kosten und steigern die Attention-Spanne der LLMs.
* **Konsistenz:** Durch bedingte `{{#if}}`-Ausdrücke sehen LLMs garantiert nur Texte über Provider und Features, die auch wirklich aktiviert sind.
