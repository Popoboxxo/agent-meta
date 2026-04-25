# agent-meta — Entwicklungskonventionen

## Harte Invarianten

1. **`.claude/agents/` nie manuell bearbeiten** — nur via `sync.py`. Manuelle Edits werden überschrieben.
2. **`version:` im Frontmatter erhöhen** bei jeder inhaltlichen Änderung: Major = Verhalten/Variable, Minor = neue Sektion, Patch = Text.
3. **Platzhalter `{{GROSS_MIT_UNTERSTRICH}}`** — Regex erfasst nur `[A-Z0-9_]+`.

## Neue Agenten-Rolle

1. `agents/1-generic/<rolle>.md` (Frontmatter: `name`, `version`, `description`, `hint`, `tools`)
2. `config/role-defaults.yaml` (model, memory, permissionMode, tier)
3. Agenten-Tabelle in `CLAUDE.md` ergänzen
4. `howto/setup/instantiate-project.md` ergänzen

## Neuer Platzhalter

1. `scripts/lib/config.py` → `build_variables()` oder `_inject_dod()`
2. `CLAUDE.md` Variablen-Tabelle
