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
