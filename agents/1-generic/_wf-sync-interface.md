# sync.py — Vollständige Referenz

## Config-Auto-Detection

Sucht in dieser Reihenfolge (wenn `--config` weggelassen):
1. `.meta-config/project.yaml`
2. `agent-meta.config.yaml` (Legacy)
3. `agent-meta.config.json` (Legacy JSON)

## Flags

```bash
py scripts/sync.py                        # Standard-Sync
py scripts/sync.py --init                 # Ersteinrichtung (CLAUDE.md + settings.json + gitignore)
py scripts/sync.py --dry-run              # Was würde sich ändern?
py scripts/sync.py --only-variables       # Nur {{VAR}}-Platzhalter ersetzen
py scripts/sync.py --create-ext developer # Extension anlegen
py scripts/sync.py --create-ext all       # Alle Extensions anlegen
py scripts/sync.py --update-ext           # Managed blocks aktualisieren
py scripts/sync.py --create-rule <thema>  # Projekt-eigene Rule anlegen
py scripts/sync.py --add-skill <url> --skill-name <n> --source <path> --role <r>
py scripts/sync.py --fill-defaults        # Fehlende Felder in project.yaml eintragen
```

## sync.log verstehen

```
[WRITE]   .claude/agents/developer.md    ← Agent neu generiert
[COPY]    .claude/rules/branch-guard.md  ← Rule kopiert
[SKIP]    .claude/agents/docker.md       ← Rolle nicht aktiv
[UPDATE]  CLAUDE.md                      ← Managed block aktualisiert
[DELETE]  .claude/agents/old-role.md     ← Stale Agent entfernt
[WARN]    Variable FOO not in config     ← Platzhalter nicht befüllt
[INFO]    skill 'xyz' not enabled        ← Skill nicht aktiviert
```

Warnungen sofort beheben.

## Python-Modulstruktur (`scripts/lib/`)

| Modul | Zuständigkeit |
|-------|--------------|
| `agents.py` | Frontmatter parsen, Composition (extends/patches), sync_agents |
| `config.py` | load_config, build_variables, substitute(), fill_defaults |
| `context.py` | init_claude_md, sync_context, gitignore |
| `dod.py` | load_dod_presets, resolve_dod |
| `extensions.py` | create_extension, update_extensions |
| `hooks.py` | sync_hooks, create_hook |
| `io.py` | YAML/JSON-Loader |
| `log.py` | SyncLog (action/warn/skip/info) |
| `platform.py` | load_platform_config, substitute_platform |
| `providers.py` | load_providers_config, resolve_providers |
| `roles.py` | load_roles_config, build_role_map, Resolver |
| `rules.py` | sync_rules, sync_speech_mode, create_rule |
| `skills.py` | External Skills: load, check_pinned, sync, add |

`sync.py` selbst ist nur argparse + main-Dispatcher. Bei Änderungen: erst zuständiges `lib/`-Modul lesen.
