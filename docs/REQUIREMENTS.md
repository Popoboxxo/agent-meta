# Anforderungen — agent-meta

> Einzige Quelle der Wahrheit für alle Anforderungen des agent-meta Frameworks.
> Format: `REQ-xxx` (dreistellig) oder thematisch präfixiert (z.B. `REQ-CMD-xx`).
> Einmal vergebene IDs dürfen nie geändert oder wiederverwendet werden.

---

## Commands-System

| ID | Anforderung | Priorität |
|----|-------------|-----------|
| REQ-CMD-01 | sync.py verwaltet Commands über ein Vier-Schichten-Modell mit den Verzeichnissen `commands/0-external/`, `commands/1-generic/` und `commands/2-platform/`. Layer-Priorität (höchste gewinnt): 2-platform überschreibt 1-generic, 0-external liefert eigenständige Commands. Bei 2-platform gilt Naming-Konvention: `<platform>-<name>.md` → Output `<name>.md`. | Must |
| REQ-CMD-02 | sync.py kopiert bei jedem normalen Sync alle aktiven Commands nach `.claude/commands/`. Dabei werden `{{VAR}}`-Platzhalter analog zu Rules substituiert. Veraltete Dateien werden über Stale-Tracking via `.claude/commands/.agent-meta-managed` erkannt und entfernt. Der Sync findet nur statt wenn `"Claude"` in den konfigurierten `ai-providers` des Projekts enthalten ist. | Must |
| REQ-CMD-03 | sync.py kopiert bei jedem normalen Sync alle aktiven Commands nach `.continue/prompts/`. Continue-Frontmatter-Felder `name` und `description` werden unverändert übernommen. Fehlt `invokable: true` im Frontmatter, fügt sync.py es automatisch hinzu. Stale-Tracking via `.continue/prompts/.agent-meta-managed`. Der Sync findet nur statt wenn `"Continue"` in den konfigurierten `ai-providers` des Projekts enthalten ist. | Must |
| REQ-CMD-04 | Die Logik für das Commands-System wird in einem neuen Modul `scripts/lib/commands.py` implementiert. Das Modul enthält mindestens `collect_command_sources()` und `sync_commands_for_provider()`. Es ist analog zu `scripts/lib/rules.py` aufgebaut und darf maximal 600 Zeilen umfassen. | Must |
| REQ-CMD-05 | Commands benötigen keine Enable/Disable-Konfiguration in `.meta-config/project.yaml`. Sie werden automatisch kopiert, sobald der zugehörige Provider (Claude oder Continue) im Projekt aktiv ist. Es ist kein Eintrag in `.claude/settings.json` erforderlich. | Must |
| REQ-CMD-06 | Claude-Commands übernehmen die Frontmatter-Felder `description`, `allowed-tools` und `argument-hint` unverändert aus der Quelldatei. Continue-Commands übernehmen `name` und `description` unverändert; sync.py ergänzt `invokable: true` automatisch, falls das Feld fehlt. Kein anderes Frontmatter-Feld wird von sync.py verändert oder entfernt. | Must |
| REQ-CMD-07 | Das Repository enthält einen generischen Claude-Slash-Command `commands/1-generic/doc-now.md`. Der Command `/doc-now` delegiert an den `documenter`-Agenten und veranlasst diesen, `CODEBASE_OVERVIEW.md` sofort zu aktualisieren. Der Command akzeptiert ein optionales `$ARGUMENTS`-Token, mit dem der Nutzer den zu dokumentierenden Bereich eingrenzen kann. | Should |
| REQ-CMD-08 | `sync.py --create-command <name>` legt eine projektspezifische Command-Datei unter `.claude/commands/<name>.md` an. Die so erstellte Datei wird von sync.py bei späteren Syncs nie überschrieben oder gelöscht. Das Verhalten ist analog zu `--create-rule <name>`. | Should |
| REQ-CMD-09 | Das Commands-System ist vollständig dokumentiert in `howto/commands.md` (Schichten-Modell, Sync-Verhalten, Frontmatter-Felder, Anleitung zum Anlegen eines projektspezifischen Commands). Zusätzlich werden `CLAUDE.md` (Verzeichnisstruktur, Sync-Verhalten-Tabelle) und `howto/instantiate-project.md` (Verweis auf Commands) aktualisiert. | Should |

---

## Framework-Features

| ID | Anforderung | Priorität |
|----|-------------|-----------|
| REQ-FW-001 | sync.py unterstützt die CLI-Flags `--config`, `--init`, `--only-variables`, `--create-ext`, `--update-ext`, `--create-rule`, `--create-hook`, `--create-command`, `--dry-run`, `--setup`, `--add-skill`. Jedes Flag löst einen klar definierten Teil-Pipeline-Schritt aus und darf unabhängig von anderen Flags kombinierbar sein (außer wo technisch ausgeschlossen). | Must |
| REQ-FW-002 | sync.py generiert Agenten für alle in `ai-providers` konfigurierten Provider (Claude, Continue, Gemini, Opencode). Die Provider-Auflösung erfolgt über `resolve_providers()` in `scripts/lib/providers.py`. Jeder Provider erhält sein natives Output-Format (z.B. `.claude/agents/`, `.continue/agents/`, `.gemini/agents/`, `.opencode/agents/`). | Must |
| REQ-FW-003 | sync.py implementiert das Vier-Schichten-Modell für Agenten-Quellen: `0-external/` (externe Skills, höchste Priorität), `1-generic/` (universell), `2-platform/` (plattformspezifisch), `3-project/` (projektspezifisch). Die Override-Reihenfolge ist: 1-generic → 2-platform → 3-project/<rolle>.md → 0-external. Eine 3-project-Override-Datei ersetzt den generierten Agenten vollständig, eine `-ext.md`-Datei wird additiv geladen. | Must |
| REQ-FW-004 | sync.py unterstützt die Composition-Syntax für 2-platform und 3-project Templates. Ein Template mit `extends:` und `patches:`-Liste wird zur Build-Zeit aufgelöst. Unterstützte Patch-Operationen sind: `append-after` (nach einem Anchor einfügen), `replace` (Section ersetzen), `delete` (Section entfernen), `append` (ans Dateiende anhängen). Das generierte Output-Dokument enthält kein `extends:`-Feld mehr. | Must |
| REQ-FW-005 | sync.py substituiert alle `{{VARIABLE}}`-Platzhalter in Templates, Rules, Hooks und Commands. Variablen werden aus `.meta-config/project.yaml` (Sektion `variables:`) gelesen und durch `build_variables()` in `scripts/lib/config.py` angereichert. Platzhalter folgen dem Muster `[A-Z0-9_]+` — kleinbuchstabige oder gemischte Namen werden nicht substituiert. | Must |
| REQ-FW-006 | sync.py verwaltet externe Skills über `config/skills-registry.yaml` (zentrale Skill-Konfiguration im Meta-Repo). Skills werden als Git-Submodule in `external/` eingebunden und erhalten ein `approved: true/false` Quality Gate. Pro Projekt können Skills via `.meta-config/skills.yaml` oder `project.yaml` aktiviert werden. Jeder aktivierte Skill generiert einen Wrapper-Agenten via `_skill-wrapper.md`. | Must |
| REQ-FW-007 | sync.py generiert und verwaltet Rules für alle aktiven Provider. Rules liegen in `rules/` und werden über `scripts/lib/rules.py` synchronisiert. Die `--create-rule <name>`-Option legt eine projektspezifische Rule an, die von sync.py nie überschrieben wird. Speech-Mode (`speech-mode` in project.yaml) wird als Rule injiziert. | Must |
| REQ-FW-008 | sync.py generiert und verwaltet Hooks für alle aktiven Provider. Hooks liegen in `hooks/` und werden über `scripts/lib/hooks.py` synchronisiert. Die `--create-hook <name>`-Option legt eine projektspezifische Hook-Datei an. Der `dod-push-check`-Hook prüft vor dem Push die Definition-of-Done-Kriterien. | Must |
| REQ-FW-009 | sync.py unterstützt das `--dry-run`-Flag, das alle Operationen simuliert ohne Dateien zu schreiben. Im Dry-Run-Modus wird ein vollständiger Sync-Log erzeugt, der alle geplanten Änderungen, Neuerstellungen und Löschungen dokumentiert. Dry-Run muss vor jedem Commit auf main ausgeführt werden. | Must |
| REQ-FW-010 | sync.py protokolliert jeden Sync-Vorgang in `sync.log`. Das Log enthält Zeitstempel, durchgeführte Operationen (Kopieren, Substituieren, Löschen), Fehlermeldungen und eine Zusammenfassung der generierten Dateien. Das Log-Modul (`scripts/lib/log.py`) bietet strukturierte Methoden für Info, Warnung und Fehler. | Must |

---

## Agenten-Templates

| ID | Anforderung | Priorität |
|----|-------------|-----------|
| REQ-AT-001 | Jedes Agent-Template in `agents/1-generic/` enthält ein YAML-Frontmatter mit den Pflichtfeldern `name`, `version`, `description`, `hint` und `tools`. Das Frontmatter wird von sync.py unverändert in den Output übernommen und dient der Provider-Konfiguration (z.B. `role-defaults.yaml` Lookup). | Must |
| REQ-AT-002 | Agent-Versionen im Frontmatter folgen semantischem Versioning: Major-Bump bei umbenannten Variablen, geändertem Verhalten oder neuen Pflichtsektionen; Minor-Bump bei neuen optionalen Sektionen oder erweitertem Scope; Patch-Bump bei Textverbesserungen, Klarstellungen oder Config-Pfad-Fixes. | Must |
| REQ-AT-003 | Plattform-Agenten in `agents/2-platform/` führen das `based-on`-Feld im Frontmatter, das auf die Generic-Basis verweist (Format: `"1-generic/<rolle>.md@<version>"`). Dieses Feld muss aktuell gehalten werden wenn die Generic-Basis geändert wird. | Must |
| REQ-AT-004 | sync.py injiziert die Definition-of-Done (DoD) basierend auf dem in `project.yaml` konfigurierten `dod-preset`. Die DoD-Presets sind in `config/dod-presets.yaml` definiert und enthalten aktivierbare Kriterien (REQ-Traceability, Tests, Codebase-Overview, Security-Audit). Die Injektion erfolgt als Handlebars-Template-Sektion im generierten Agenten. | Must |
| REQ-AT-005 | sync.py injiziert Sprachregeln basierend auf dem `speech-mode` in `project.yaml`. Unterstützte Modi sind: `full` (Default), `short`, `childish`, `caveman`, `asozial`, `submissive`. Die Sprachregel wird als Rule in den generierten Agenten übernommen und überschreibt alle anderen Stilanweisungen. | Must |
| REQ-AT-006 | Das Hints-System ermöglicht pro Agent-Rolle eine kontextspezifische `hint`-Beschreibung im Frontmatter. sync.py aggregiert alle Hints und schreibt sie in die `AGENT_HINTS`-Variable, die in `CLAUDE.md` und generierten Konfigurationsdateien referenziert wird. | Should |
| REQ-AT-007 | Agent-Templates unterstützen Workflow-Sektionen die den Agenten durch strukturierte Arbeitsabläufe leiten. Workflows sind als nummerierte Schritte oder als Entscheidungsbäume formuliert und enthalten Delegationspunkte (z.B. "Bei Anforderungsdokumenten → requirements delegieren"). | Should |
| REQ-AT-008 | Extension-Dateien (`3-project/<rolle>-ext.md`) werden vom generierten Agenten zur Laufzeit als zusätzliche Instruktion geladen. Sie enthalten kein Frontmatter und werden nicht von sync.py in den Agenten-Body eingebettet — der Agent liest sie selbstständig bei Startup. Die `--create-ext <rolle>` und `--update-ext` Flags verwalten diese Dateien. | Must |
| REQ-AT-009 | Neue Agenten-Rollen erfordern vier Pflichtschritte: (1) Template in `agents/1-generic/<rolle>.md` mit Frontmatter anlegen, (2) Eintrag in `config/role-defaults.yaml` (model, memory, permissionMode, tier), (3) Ergänzung der Agenten- und Hints-Tabellen in `CLAUDE.md`, (4) Aktualisierung von `howto/setup/instantiate-project.md` und `howto/CLAUDE.project-template.md`. | Must |
| REQ-AT-010 | Snippet-Dateien in `snippets/` enthalten eigenes YAML-Frontmatter mit den Feldern `snippet`, `version`, `language` und `runtime`. sync.py synchronisiert Snippets provider-spezifisch und substituiert Platzhalter analog zu Agent-Templates. | Should |

---

## Developer-Experience

| ID | Anforderung | Priorität |
|----|-------------|-----------|
| REQ-DX-001 | Das `howto/`-Verzeichnis enthält Anleitungen für alle Kernfunktionen: Projekt-Initialisierung (`instantiate-project.md`), Commands (`commands.md`), Rules (`rules.md`), Hooks (`hooks.md`), Extensions (`extensions.md`), MCP-Setup (`mcp-setup.md`), Agent-Visualisierung (`agent-visualization.md`), und project.yaml-Konfiguration (`project.yaml.example`). | Must |
| REQ-DX-002 | `howto/project.yaml.example` dokumentiert jede Sektion der project.yaml mit Inline-Kommentaren. Alle konfigurierbaren Variablen aus `build_variables()` sind als auskommentierte Einträge enthalten. Das Beispiel ist direkt als Vorlage kopierbar und funktioniert nach Anpassung der Projekt-spezifischen Werte. | Must |
| REQ-DX-003 | sync.py bietet das `--setup`-Flag für die initiale Gerüst-Erstellung eines neuen Meta-Repos. Es scaffolld die Standard-Verzeichnisstruktur (`agents/`, `scripts/`, `config/`, `howto/`, `docs/`), legt eine minimale `project.yaml` an und erstellt Platzhalter-Templates für die ersten Agenten-Rollen. | Should |
| REQ-DX-004 | Das Error-Handling in sync.py ist über das `SyncError`-Exception-System in `scripts/lib/io.py` zentralisiert. Jede Operation wirft typisierte Errors mit kontextuellen Informationen (Dateipfad, Operation, Ursache). Errors werden im Sync-Log protokolliert und im Dry-Run-Modus als Warnung ausgegeben. | Must |
| REQ-DX-005 | Die `CLAUDE.md`-Datei im Repository-Root dient als zentrale Referenz für alle Agenten. Sie enthält: Agenten-Tabelle mit Zuständigkeiten, Regeln (Branch-Guard, Commits, DoD, Sprachregeln), Variablen-Tabelle aller verfügbaren `{{VAR}}`-Platzhalter, Hints-Tabelle, Verzeichnisstruktur-Beschreibung und Sync-Verhalten-Tabellen. | Must |
| REQ-DX-006 | `docs/architecture/` enthält Mermaid-Diagramme die die Schichten-Architektur, Sync-Pipeline und Provider-Generierung visualisieren. Diagramme werden bei strukturellen Änderungen aktualisiert und sind in der internen Dokumentation verlinkt. | Could |
| REQ-DX-007 | Das `config/`-Verzeichnis enthält Registry- und Preset-Dateien die unabhängig von project.yaml konfigurierbar sind: `role-defaults.yaml` (Agenten-Standardkonfiguration), `dod-presets.yaml` (DoD-Vorlagen), `rules-presets.yaml` (Rule-Sammlungen), `ai-providers.yaml` (Provider-Definitionen), `mcp-registry.yaml` (MCP-Server-Registry), `skills-registry.yaml` (externe Skills). | Must |
| REQ-DX-008 | sync.py erstellt bei `--init` eine `.claude/settings.local.json` mit projektspezifischen Einstellungen. Diese Datei wird nicht von sync.py überschrieben und ermöglicht projektindividuelle Provider-Konfigurationen ohne die zentrale `project.yaml` zu ändern. | Should |
| REQ-DX-009 | Die Visualisierungsfunktion (`viz` in project.yaml) ermöglicht Agenten-Mindmaps und Session-Tracking. Events werden in `.meta-viz/events.jsonl` protokolliert. Der Viz-Server (konfigurierbar über `viz.server.port`) stellt Sessions für die Dauer von `session_timeout_min` bereit. Reports werden nach `retention_days` Tagen bereinigt. | Could |
| REQ-DX-010 | MCP-Integration: sync.py generiert MCP-Artefakte via `scripts/lib/mcp.py`. Das `mcp-registry.yaml` definiert verfügbare MCP-Server. `init_secrets_template()` erstellt eine Vorlage für Secret-Management. MCP-Konfigurationen werden provider-spezifisch in die jeweiligen Settings-Dateien geschrieben. | Should |
