# agent-meta — Entwicklungskonventionen

## Harte Invarianten (niemals verletzen)

**1. `.claude/agents/` ist generierter Output — nie manuell bearbeiten.**
Alle Änderungen gehören in die Quell-Templates unter `agents/` oder in `.meta-config/project.yaml`.
Manuelle Edits werden beim nächsten `sync.py`-Lauf überschrieben.

**2. Agent-Versionen im Frontmatter erhöhen bei jeder inhaltlichen Änderung.**

| Änderungstyp | Bump |
|---|---|
| Umbenannte Variable, geändertes Verhalten, neue Pflichtsektion | **Major** (`X.0.0`) |
| Neue optionale Sektion, erweiterter Scope | **Minor** (`x.Y.0`) |
| Textverbesserung, Klarstellung, Config-Pfad-Fix | **Patch** (`x.y.Z`) |

Plattform-Agenten (`2-platform/`) führen zusätzlich `based-on: "1-generic/<rolle>.md@<version>"`.
Dieses Feld aktuell halten wenn die Generic-Basis geändert wird.

**3. Platzhalter immer `{{GROSS_MIT_UNTERSTRICH}}`.**
Kleinbuchstaben oder gemischte Schreibweise funktioniert nicht — der Regex in `substitute()`
erfasst nur `[A-Z0-9_]+`.

## Wenn du eine neue Agenten-Rolle hinzufügst

Pflichtschritte — alle vier, sonst ist die Rolle unvollständig:

1. `agents/1-generic/<rolle>.md` anlegen (mit Frontmatter: `name`, `version`, `description`, `hint`, `tools`)
2. Eintrag in `config/role-defaults.yaml` (model, memory, permissionMode, tier)
3. Agenten-Tabelle und Hints-Tabelle in `CLAUDE.md` ergänzen
4. `howto/setup/instantiate-project.md` und `howto/CLAUDE.project-template.md` ergänzen

## Wenn du einen neuen Platzhalter einführst

1. In `scripts/lib/config.py` → `build_variables()` oder `_inject_dod()` eintragen
2. In `CLAUDE.md` Variablen-Tabelle dokumentieren
3. In `howto/project.yaml.example` als Kommentar-Zeile ergänzen (optional aber empfohlen)

## Änderungs-Checkliste (before commit)

| Was geändert | Was prüfen |
|---|---|
| `1-generic/<rolle>.md` | version: erhöhen + betroffene Projekte syncen |
| `2-platform/<platform>-<rolle>.md` | version: und based-on: aktuell? |
| `agents/0-external/_skill-wrapper.md` | Alle aktivierten Skills neu syncen |
| `config/skills-registry.yaml` | Projekte neu syncen |
| `config/role-defaults.yaml` (neue Rolle) | Tabellen in CLAUDE.md + howto-Dateien |
| `hint:` Feld in Agent-Template | Projekte syncen (AGENT_HINTS wird neu generiert) |
| Rules oder Hooks in `rules/` / `hooks/` | Projekte syncen (werden überschrieben) |
