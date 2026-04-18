# agent-meta Sync-Konzept

Dieses Dokument beschreibt das Konzept zur Einbindung von `agent-meta` in konkrete
Projekte über ein versioniertes Python-Script und eine Konfigurationsdatei.

---

## Kernidee

Agenten-Dateien in einem Projekt sind **generierter Output** — kein manuell
gepflegter Inhalt. Den Projektkontext liefert die `CLAUDE.md` des Projekts.

```
agent-meta (Release vX.Y.Z)  +  .meta-config/project.yaml (im Projekt)
    = .claude/agents/*.md (generiert, nie manuell editieren)
```

---

## Beteiligte Dateien

### Im `agent-meta` Repository

```
agent-meta/
  agents/
    0-external/      ← Wrapper-Template für externe Skill-Agenten
    1-generic/       ← universelle Agenten
    2-platform/      ← plattformspezifische Agenten
    3-project/       ← projektspezifische Overrides (selten)
  scripts/
    sync.py          ← CLI-Entrypoint (argparse + main, ~260 Zeilen)
    lib/             ← Logik-Module (je ≤600 Zeilen)
  templates/         ← managed-block Templates (Extension, CLAUDE.md)
  config/            ← Framework-Konfiguration (nie manuell bearbeiten)
    project.yaml               ← Meta-Repo Selbst-Konfiguration
    role-defaults.yaml         ← Rollen-Defaults: model, memory, permissionMode
    dod-presets.yaml           ← DoD-Qualitätsprofile
    ai-providers.yaml          ← Provider-Konfiguration (Claude, Gemini, Continue)
    skills-registry.yaml       ← Skill-Registry: repos + skills (approved-Gate)
    project-config.schema.json ← JSON Schema für .meta-config/project.yaml
  snippets/          ← sprachspezifische Code-Snippets
  external/          ← Git Submodule (externe Skill-Repos via --add-skill)
  howto/
    sync-concept.md  ← dieses Dokument
    CLAUDE.project-template.md
```

### Im Projekt-Repository

```
<projekt>/
  .agent-meta/               ← Git Submodule (agent-meta Repository)
  .meta-config/project.yaml     ← Sync-Konfiguration (manuell gepflegt, versioniert)
  CLAUDE.md                  ← bei "Claude" in ai-providers automatisch erstellt, danach manuell gepflegt
                               ├─ managed block (auto-aktualisiert bei jedem sync)
                               └─ handgeschriebener Rest (nie überschrieben)
  CLAUDE.personal.md         ← persönliche Präferenzen (gitignored, nie committen)
  .claude/                   ← Claude Code (immer wenn "Claude" in ai-providers)
    settings.json            ← Team-Permissions (committed ins Repo)
    settings.local.json      ← persönliche Permissions (gitignored, nie committen)
    agents/                  ← vollständig generiert, nie manuell editieren
      orchestrator.md
      developer.md
      tester.md
      feature.md
      agent-meta-manager.md
      ...
    snippets/                ← kopiert aus agent-meta/snippets/
    skills/                  ← kopiert aus external/ Submodulen
    rules/                   ← auto-loaded in alle Agenten + Hauptchat
      *.md                     ← von agent-meta verwaltet (sync.py, mit Variablensubstitution)
      meine-regel.md           ← projekt-eigen (nie von sync.py berührt)
    hooks/                   ← kopiert aus agent-meta/hooks/ + in settings.json registriert
    commands/                ← Custom Slash Commands (/project:<name>), manuell angelegt
      deploy.md                ← → /project:deploy (läuft im Hauptkontext, kein isolierter Context)
    3-project/               ← handgeschrieben, nie von sync.py überschrieben
      <prefix>-<rolle>-ext.md  ← Extension (additiv geladen)
      <rolle>.md               ← Override (ersetzt Agenten komplett)
  .gemini/                   ← Gemini CLI (nur wenn "Gemini" in ai-providers)
    GEMINI.md                ← Kontext-Datei mit managed block
    agents/                  ← generierte Agenten (kein permissionMode/memory)
    settings.json            ← Skeleton (einmalig angelegt)
  .continue/                 ← Continue (nur wenn "Continue" in ai-providers)
    rules/
      project-context.md     ← Projekt-Kontext als Rule (alwaysApply: true, managed block)
    agents/                  ← Custom Agents (alwaysApply: false, explizit aufgerufen)
    config.yaml              ← Skeleton (einmalig angelegt, nie überschrieben)
  sync.log                   ← Protokoll des letzten Sync-Laufs (gitignore empfohlen)
```

### Team vs. Persönlich

| Datei | Committed? | Angelegt von | Zweck |
|-------|------------|--------------|-------|
| `CLAUDE.md` | Ja | sync.py (einmalig) | Projektregeln für alle |
| `CLAUDE.personal.md` | Nein (gitignored) | sync.py (einmalig) | Persönliche Präferenzen |
| `.claude/settings.json` | Ja | sync.py (einmalig Skeleton + Hooks-Merge) | Team-Permissions + Hooks |
| `.claude/settings.local.json` | Nein (gitignored) | sync.py (einmalig) | Persönliche Permissions |

`CLAUDE.personal.md` wird einmalig aus `howto/CLAUDE.personal-template.md` kopiert und danach nie wieder von sync.py angefasst. Jeder Entwickler füllt sie für sich aus.

---

## Abgrenzung: rules/ vs. 3-project/ vs. commands/

| Mechanismus | Scope | Laden | Quelle | Von sync.py verwaltet |
|-------------|-------|-------|--------|----------------------|
| `.claude/rules/*.md` | **Alle** Agenten + Hauptchat | Automatisch | agent-meta + Projekt | Ja (agent-meta-Rules) / Nein (projekt-eigene) |
| `.claude/3-project/*-ext.md` | **Ein** Agenten-Typ | Explizit per Read-Hook | Projekt | Nein |
| `.claude/commands/*.md` | Hauptchat (kein isolierter Kontext) | Als Slash-Command `/project:<name>` | Projekt | Nein |

**Wann was:**
- Regel gilt für alle Agenten und Hauptchat → `.claude/rules/`
- Zusatzwissen für einen spezifischen Agenten → `.claude/3-project/<rolle>-ext.md`
- Wiederkehrender Einzel-Workflow im Hauptchat → `.claude/commands/`

---

## Entscheidungen

| Thema | Entscheidung |
|-------|-------------|
| agent-meta Einbindung | **Git Submodule** unter `.agent-meta/` |
| Script-Aufruf | Immer aus agent-meta: `py .agent-meta/scripts/sync.py` |
| CLAUDE.md Erstellung | Automatisch wenn `"Claude"` in `ai-providers` und Datei fehlt |
| CLAUDE.md managed block | Automatisch bei jedem sync aktualisiert (nur wenn `"Claude"` in `ai-providers`) |
| Fehlende Variablen | **Warning + weitermachen** — Platzhalter bleibt sichtbar |
| Agenten-Dateinamen | **Generisch** — kein Projekt-Prefix: `developer.md`, `tester.md` |

---

## .meta-config/project.yaml

Die einzige Konfigurationsdatei die das Projekt pflegt.

```yaml
# .meta-config/project.yaml
agent-meta-version: "0.26.0"

ai-providers:
  - Claude

platforms:
  - sharkord

roles:
  - orchestrator
  - developer
  - tester
  - validator
  - requirements
  - documenter
  - git
  - release
  - docker
  - ideation
  - meta-feedback
  - feature
  - agent-meta-manager
  - agent-meta-scout

project:
  name: sharkord-vid-with-friends
  prefix: vwf
  short: vid-with-friends

variables:
  PROJECT_NAME: sharkord-vid-with-friends
  COMMUNICATION_LANGUAGE: Deutsch
  BUILD_COMMAND: bun run build
  TEST_COMMAND: bun test
  # ... weitere Variablen
```

### Felder

| Feld | Bedeutung |
|------|-----------|
| *(optional)* | Schema-Validierung via `.agent-meta/config/project-config.schema.json` kann in der IDE eingebunden werden |
| `agent-meta-version` | Welches Release von agent-meta genutzt wird |
| `ai-providers` | Array der aktiven Provider: `["Claude"]`, `["Claude", "Gemini", "Continue"]` etc. |
| `ai-provider` | Legacy (String) — weiterhin unterstützt; `"Claude"` aktiviert CLAUDE.md auto-init, managed block, settings.json + .gitignore |
| `platforms` | Aktive Plattformen — bestimmt welche `2-platform/<plattform>-*.md` einbezogen werden |
| `roles` | Whitelist der zu generierenden Rollen — fehlt der Key, werden alle Rollen generiert |
| `project.name` | Vollständiger Projektname |
| `project.prefix` | Kurzpräfix für Extension-Dateinamen (`vwf-developer-ext.md`) |
| `project.short` | Kurzname (informativ) |
| `model-overrides` | Modell pro Rolle überschreiben (z.B. `"git": "haiku"`) |
| `permission-mode-overrides` | permissionMode pro Rolle überschreiben (z.B. `"validator": "default"`) |
| `memory-overrides` | Memory-Scope pro Rolle überschreiben (z.B. `"validator": "local"`) |
| `hooks` | Hooks aktivieren — `"dod-push-check": { "enabled": true }` |
| `external-skills` | Externe Skills aktivieren — `"my-skill": { "enabled": true }` |
| `variables` | Alle `{{VARIABLE}}` die in Agenten und CLAUDE.md ersetzt werden |

---

## sync.py — Verhalten

### Aufruf-Modi

```bash
# Normaler Sync — generiert Agenten, Rules, Hooks, aktualisiert CLAUDE.md managed block
py .agent-meta/scripts/sync.py 

# Erst-Einrichtung — erzeugt auch CLAUDE.md, settings.json, settings.local.json, .gitignore
py .agent-meta/scripts/sync.py --init

# Vorschau ohne Schreiben
py .agent-meta/scripts/sync.py --dry-run

# Extension erstmalig anlegen
py .agent-meta/scripts/sync.py --create-ext developer
py .agent-meta/scripts/sync.py --create-ext all

# Managed block in bestehenden Extensions aktualisieren
py .agent-meta/scripts/sync.py --update-ext

# Projekt-eigene Rule anlegen (nie von sync.py überschrieben)
py .agent-meta/scripts/sync.py --create-rule security-policy

# Projekt-eigenen Hook anlegen (Vorlage)
py .agent-meta/scripts/sync.py --create-hook my-hook

# Externen Skill als Submodul registrieren + config-Eintrag anlegen
py .agent-meta/scripts/sync.py --add-skill <repo-url> --skill-name <name> --source <path> --role <role>
```

### Schreibverhalten pro Schicht / Datei

| Datei / Schicht | Verhalten | Wann |
|-----------------|-----------|------|
| `.claude/agents/*.md` | **Immer überschreiben** + veraltete löschen | Jeder Sync (wenn "Claude" aktiv) |
| `.claude/rules/*.md` (verwaltet) | **Immer überschreiben** + stale löschen | Jeder Sync (wenn "Claude" aktiv) |
| `.claude/hooks/*.sh` (verwaltet) | **Immer überschreiben** + stale löschen | Jeder Sync (wenn "Claude" aktiv) |
| `.claude/settings.json` (Hooks) | **Hooks mergen** — managed Hooks aktualisieren | Jeder Sync (wenn "Claude" aktiv) |
| `CLAUDE.md` managed block | **Immer aktualisieren** | Jeder Sync (wenn "Claude" aktiv) |
| `.gemini/agents/*.md` | **Immer überschreiben** + veraltete löschen | Jeder Sync (wenn "Gemini" aktiv) |
| `.gemini/GEMINI.md` managed block | **Immer aktualisieren** | Jeder Sync (wenn "Gemini" aktiv) |
| `.continue/agents/*.md` | **Immer überschreiben** + veraltete löschen | Jeder Sync (wenn "Continue" aktiv) |
| `.continue/rules/project-context.md` managed block | **Immer aktualisieren** | Jeder Sync (wenn "Continue" aktiv) |
| `.gitignore` | **Fehlende Einträge ergänzen** | Jeder Sync |
| `CLAUDE.md` | **Einmalig anlegen** aus Template | Einmalig, wenn nicht vorhanden |
| `CLAUDE.personal.md` | **Einmalig anlegen** aus Template | Einmalig, wenn nicht vorhanden |
| `.claude/settings.json` (Skeleton) | **Einmalig anlegen** | Einmalig, wenn nicht vorhanden |
| `.claude/settings.local.json` | **Einmalig anlegen** (Skeleton, gitignored) | Einmalig, wenn nicht vorhanden |
| `.gemini/GEMINI.md` | **Einmalig anlegen** aus Template | Einmalig, wenn nicht vorhanden |
| `.gemini/settings.json` | **Einmalig anlegen** (Skeleton) | Einmalig, wenn nicht vorhanden |
| `.continue/rules/project-context.md` | **Einmalig anlegen** aus Template | Einmalig, wenn nicht vorhanden |
| `.continue/config.yaml` | **Einmalig anlegen** (Skeleton) | Einmalig, wenn nicht vorhanden |
| `.claude/3-project/*-ext.md` | **Einmalig anlegen** via `--create-ext` | Manuell angefordert |
| `.claude/rules/*.md` (projekt-eigen) | **Nie anfassen** — nicht in `.agent-meta-managed` | — |
| `sync.log` | Überschreiben | Jeder Lauf |

> Einmalige Aktionen für Claude (CLAUDE.md, settings.json, CLAUDE.personal.md) sind nur aktiv wenn `"Claude"` in `ai-providers` steht.
> Für Gemini und Continue: Kontext-Datei + Settings werden beim ersten sync ohne `--init` angelegt.

### CLAUDE.md managed block

Beim normalen Sync wird der Block zwischen
`<!-- agent-meta:managed-begin -->` und `<!-- agent-meta:managed-end -->` immer aktualisiert:
- Enthält die aktuelle Agenten-Hints-Tabelle (`AGENT_HINTS`)
- Zeigt Version + Datum des letzten Syncs
- Fehlt der Block: `[WARN]` im Log mit Hinweis zum manuellen Einfügen

### Variablen-Befüllung

Alle `{{VARIABLE}}` in jeder Agenten-Datei werden mit Werten aus `variables` ersetzt.

**Auto-injiziert** (nicht in config nötig):

| Variable | Inhalt |
|----------|--------|
| `{{AGENT_META_VERSION}}` | Version aus `VERSION`-Datei |
| `{{AGENT_META_DATE}}` | Aktuelles Datum |
| `{{AGENT_HINTS}}` | Agenten-Tabelle aus `hint`-Feldern der Templates |
| `{{AI_PROVIDER}}` | Aktive Provider aus `ai-providers` (kommagetrennt) |
| `{{PREFIX}}` | Aus `project.prefix` |

Unbekannte Variablen (kein Wert in Config):
- Platzhalter bleibt unverändert sichtbar
- Eintrag im Logfile unter `WARNINGS`

Escape-Syntax: `{{%VAR%}}` → rendert als `{{VAR}}` ohne Substitution (für Dokumentation).

---

## Logfile (sync.log)

Nach jedem Lauf wird `sync.log` im Projekt-Root geschrieben (überschreibt den vorherigen).

```
============================================================
agent-meta sync — 2026-04-07 10:00:00
============================================================
Config:    .meta-config/project.yaml
Source:    .agent-meta/ (v0.21.1-beta)
Mode:      sync
Platforms: sharkord

ACTIONS
-------
[PROVIDER] Claude
[WRITE   ]  .claude/agents/orchestrator.md                 (1-generic/orchestrator.md)
[WRITE   ]  .claude/agents/developer.md                    (1-generic/developer.md)
[WRITE   ]  .claude/agents/feature.md                      (1-generic/feature.md)
[WRITE   ]  .claude/agents/agent-meta-manager.md           (1-generic/agent-meta-manager.md)
[WRITE   ]  .claude/agents/release.md                      (2-platform/sharkord-release.md)
[WRITE   ]  .claude/agents/docker.md                       (2-platform/sharkord-docker.md)
[COPY    ]  .claude/rules/issue-lifecycle.md               (rules/1-generic/issue-lifecycle.md)
[COPY    ]  .claude/hooks/dod-push-check.sh                (hooks/1-generic/dod-push-check.sh)
[UPDATE  ]  CLAUDE.md                                      (managed block)

[PROVIDER] Continue
[WRITE   ]  .continue/agents/orchestrator.md               (1-generic/orchestrator.md)
[WRITE   ]  .continue/agents/developer.md                  (1-generic/developer.md)
[UPDATE  ]  .continue/rules/project-context.md             (managed block)

SKIPPED
-------
[SKIP]   CLAUDE.md                                         (already exists)
[SKIP]   .claude/settings.local.json                       (already exists)

INFO
----
[INFO]   .claude/agents/home-organization-specialist.md    (skill disabled)
[INFO]   dod-push-check hook                               (not enabled in config)

WARNINGS
--------
(none)

SUMMARY
-------
12 action(s)  |  2 skipped  |  0 warning(s)
Logfile: sync.log
```

> **Multi-Provider Dokumentation:** [howto/multi-provider.md](multi-provider.md) — vollständige Beschreibung
> aller Provider (Claude, Gemini, Continue), Frontmatter-Unterschiede, Stale-Tracking, Troubleshooting.

---

## Update-Flow

### Neues agent-meta Release einbinden

```bash
# 1. Submodul auf neue Version bringen
cd .agent-meta && git fetch && git checkout v0.21.1-beta && cd ..
git add .agent-meta

# 2. Version in Config aktualisieren
# .meta-config/project.yaml: "agent-meta-version": "0.21.1-beta"

# 3. Sync ausführen — alle Agenten, Rules und Hooks werden neu generiert
py .agent-meta/scripts/sync.py 

# 4. Ergebnis prüfen + committen
git add .claude/ .gemini/ .continue/ .meta-config/project.yaml CLAUDE.md
git commit -m "chore: upgrade agent-meta to v0.21.1-beta"
```

### Neue Variable ergänzen

```bash
# 1. Variable in .meta-config/project.yaml ergänzen
# 2. Sync ausführen — befüllt alle Agenten + CLAUDE.md managed block
py .agent-meta/scripts/sync.py 
```

---

## Stale Agent Cleanup

Wenn eine Rolle aus `config['roles']` entfernt wird, löscht sync.py die zugehörige Datei beim nächsten Sync automatisch:

```
[DELETE  ]  .claude/agents/docker.md    (role removed from config)
```

Das gilt für alle generisch generierten Agenten. **Externe Skill-Agenten** (`.claude/agents/<role>.md` aus `0-external/`) werden nicht gelöscht — sie werden nur über `enabled: false` in `config/skills-registry.yaml` deaktiviert.

---

## Was NIEMALS manuell editiert wird

```
.claude/agents/*.md    ← vollständig generiert
                          Manuelle Änderungen werden beim nächsten sync überschrieben
                          Nicht mehr benötigte Dateien werden automatisch gelöscht
```

Projektspezifisches Wissen gehört in:
- **Extension** `.claude/3-project/<prefix>-<rolle>-ext.md` — additiv, nie überschrieben
- **Override** `.claude/3-project/<rolle>.md` — ersetzt Agenten komplett, nie überschrieben

---

## Abhängigkeiten des Scripts

- Python 3.8+
- Pflicht: nur stdlib (`json`, `pathlib`, `argparse`, `re`, `shutil`, `datetime`)
- Optional: `jsonschema` — wenn installiert, wird `.meta-config/project.yaml` gegen `config/project-config.schema.json` validiert
