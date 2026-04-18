# agent-meta — sync.py Interface

`sync.py` ist der einzige Weg Agenten zu generieren. Nie direkt in `.claude/agents/` schreiben.

## Config-Auto-Detection

Wenn `--config` weggelassen wird, sucht sync.py in dieser Reihenfolge:

1. `.meta-config/project.yaml` (Standard: Zielprojekt + Meta-Repo Self-Hosting ← dieses Repo)
2. `agent-meta.config.yaml` (Legacy)
3. `agent-meta.config.json` (Legacy JSON)

## Wichtige Flags

```bash
# Standard-Sync (Agenten + Rules + Hooks regenerieren)
py scripts/sync.py

# Erstmalig: CLAUDE.md + settings.json + gitignore anlegen
py scripts/sync.py --init

# Vor echten Änderungen: was würde sich ändern?
py scripts/sync.py --dry-run

# Nur {{%VAR%}}-Platzhalter in bestehender CLAUDE.md ersetzen
py scripts/sync.py --only-variables

# Extension für eine Rolle anlegen (einmalig)
py scripts/sync.py --create-ext developer
py scripts/sync.py --create-ext all

# Managed block in allen bestehenden Extensions aktualisieren
py scripts/sync.py --update-ext

# Neue projekt-eigene Rule anlegen (nie überschrieben)
py scripts/sync.py --create-rule mein-thema

# Neuen External Skill registrieren (Meta-Maintainer)
py scripts/sync.py --add-skill <repo-url> --skill-name <name> --source <path> --role <role>

# Config-Defaults in project.yaml eintragen (fehlende Felder)
py scripts/sync.py --fill-defaults
```

## sync.log verstehen

```
[WRITE]   .claude/agents/developer.md   (1-generic/developer.md)      ← Agent neu generiert
[COPY]    .claude/rules/branch-guard.md  (rules/1-generic/branch-guard.md) ← Rule kopiert
[SKIP]    .claude/agents/docker.md       (not in roles list)           ← Rolle nicht aktiv
[UPDATE]  CLAUDE.md                      (managed block)               ← Managed block aktualisiert
[DELETE]  .claude/agents/old-role.md     (role removed from config)    ← Stale Agent entfernt
[WARN]    Variable FOO not in config                                   ← Platzhalter nicht befüllt
[INFO]    skill 'xyz' not enabled                                      ← Skill nicht aktiviert
```

**Warnungen sofort beheben** — sie bedeuten entweder fehlende Variablen in
`.meta-config/project.yaml` oder veraltete Submodul-Stände.

## Python-Modulstruktur (`scripts/lib/`)

Jedes Modul ≤ 600 Zeilen — LLM-lesbar in einem Read-Aufruf.

| Modul | Zuständigkeit |
|-------|--------------|
| `agents.py` | Frontmatter parsen, Composition (extends/patches), sync_agents |
| `config.py` | load_config, build_variables, substitute(), fill_defaults |
| `context.py` | init_claude_md, sync_context, gitignore |
| `dod.py` | load_dod_presets, resolve_dod |
| `extensions.py` | create_extension, update_extensions |
| `hooks.py` | sync_hooks, create_hook |
| `io.py` | YAML/JSON-Loader (_load_yaml_or_json) |
| `log.py` | SyncLog (action/warn/skip/info) |
| `platform.py` | load_platform_config, substitute_platform |
| `providers.py` | load_providers_config, resolve_providers |
| `roles.py` | load_roles_config, build_role_map, Resolver |
| `rules.py` | sync_rules (inkl. substitute), sync_speech_mode, create_rule |
| `skills.py` | External Skills: load, check_pinned, sync, add |

**Bei Änderungen am sync-Verhalten:** Erst das zuständige `lib/`-Modul lesen,
dann gezielt ändern. `sync.py` selbst ist nur argparse + main-Dispatcher.
