# agent-meta Sync-Konzept

Dieses Dokument beschreibt das Konzept zur Einbindung von `agent-meta` in konkrete
Projekte über ein versioniertes Python-Script und eine Konfigurationsdatei.

---

## Kernidee

Agenten-Dateien in einem Projekt sind **generierter Output** — kein manuell
gepflegter Inhalt. Den Projektkontext liefert die `CLAUDE.md` des Projekts.

```
agent-meta (Release vX.Y.Z)  +  agent-meta.config.json (im Projekt)
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
    sync.py          ← das Sync-Script (versioniert mit agent-meta)
  snippets/          ← sprachspezifische Code-Snippets
  external/          ← Git Submodule (externe Skill-Repos via --add-skill)
  external-skills.config.json   ← aktive Skill-Konfiguration
  external-skills.catalog.json  ← Katalog bekannter Skill-Repos (für agent-meta-manager)
  howto/
    sync-concept.md  ← dieses Dokument
    CLAUDE.project-template.md
```

### Im Projekt-Repository

```
<projekt>/
  .agent-meta/               ← Git Submodule (agent-meta Repository)
  agent-meta.config.json     ← Sync-Konfiguration (manuell gepflegt, versioniert)
  CLAUDE.md                  ← bei ai-provider: Claude automatisch erstellt, danach manuell gepflegt
                               ├─ managed block (auto-aktualisiert bei jedem sync)
                               └─ handgeschriebener Rest (nie überschrieben)
  .claude/
    agents/                  ← vollständig generiert, nie manuell editieren
      orchestrator.md
      developer.md
      tester.md
      feature.md
      agent-meta-manager.md
      ...
    snippets/                ← kopiert aus agent-meta/snippets/
    skills/                  ← kopiert aus external/ Submodulen
    3-project/               ← handgeschrieben, nie von sync.py überschrieben
      <prefix>-<rolle>-ext.md  ← Extension (additiv geladen)
      <rolle>.md               ← Override (ersetzt Agenten komplett)
  sync.log                   ← Protokoll des letzten Sync-Laufs (gitignore empfohlen)
```

---

## Entscheidungen

| Thema | Entscheidung |
|-------|-------------|
| agent-meta Einbindung | **Git Submodule** unter `.agent-meta/` |
| Script-Aufruf | Immer aus agent-meta: `py .agent-meta/scripts/sync.py` |
| CLAUDE.md Erstellung | Automatisch wenn `ai-provider: Claude` und Datei fehlt |
| CLAUDE.md managed block | Automatisch bei jedem sync aktualisiert (nur bei `ai-provider: Claude`) |
| Fehlende Variablen | **Warning + weitermachen** — Platzhalter bleibt sichtbar |
| Agenten-Dateinamen | **Generisch** — kein Projekt-Prefix: `developer.md`, `tester.md` |

---

## agent-meta.config.json

Die einzige Konfigurationsdatei die das Projekt pflegt.

```json
{
  "agent-meta-version": "0.14.0",

  "ai-provider": "Claude",

  "platforms": ["sharkord"],

  "roles": ["orchestrator", "developer", "tester", "validator",
            "requirements", "documenter", "git", "release", "docker",
            "ideation", "meta-feedback", "feature", "agent-meta-manager"],

  "project": {
    "name": "sharkord-vid-with-friends",
    "prefix": "vwf",
    "short": "vid-with-friends"
  },

  "variables": {
    "PROJECT_NAME":         "sharkord-vid-with-friends",
    "COMMUNICATION_LANGUAGE": "Deutsch",
    "BUILD_COMMAND":        "bun run build",
    "TEST_COMMAND":         "bun test",
    ...
  }
}
```

### Felder

| Feld | Bedeutung |
|------|-----------|
| `agent-meta-version` | Welches Release von agent-meta genutzt wird |
| `ai-provider` | AI-Provider: `"Claude"` aktiviert CLAUDE.md auto-init + managed block |
| `platforms` | Aktive Plattformen — bestimmt welche `2-platform/<plattform>-*.md` einbezogen werden |
| `roles` | Whitelist der zu generierenden Rollen — fehlt der Key, werden alle Rollen generiert |
| `project.name` | Vollständiger Projektname |
| `project.prefix` | Kurzpräfix für Extension-Dateinamen (`vwf-developer-ext.md`) |
| `project.short` | Kurzname (informativ) |
| `variables` | Alle `{{VARIABLE}}` die in Agenten und CLAUDE.md ersetzt werden |

---

## sync.py — Verhalten

### Aufruf-Modi

```bash
# Normaler Sync — generiert alle Agenten + aktualisiert CLAUDE.md managed block
py .agent-meta/scripts/sync.py --config agent-meta.config.json

# Vorschau ohne Schreiben
py .agent-meta/scripts/sync.py --config agent-meta.config.json --dry-run

# Extension erstmalig anlegen
py .agent-meta/scripts/sync.py --config agent-meta.config.json --create-ext developer
py .agent-meta/scripts/sync.py --config agent-meta.config.json --create-ext all

# Managed block in bestehenden Extensions aktualisieren
py .agent-meta/scripts/sync.py --config agent-meta.config.json --update-ext

# Externen Skill als Submodul registrieren + config-Eintrag anlegen
py .agent-meta/scripts/sync.py --add-skill <repo-url> --skill-name <name> --source <path> --role <role>
```

### Schreibverhalten pro Schicht

| Schicht | Verhalten |
|---------|-----------|
| `1-generic/` | **Immer überschreiben** — generierter Output |
| `2-platform/` | **Immer überschreiben** — für alle konfigurierten Plattformen |
| `3-project/` in Meta-Repo | **Überschreiben wenn Datei existiert** |
| `CLAUDE.md` | **Auto-erstellen** wenn `ai-provider: Claude` + nicht vorhanden |
| `CLAUDE.md` managed block | **Immer aktualisieren** bei `ai-provider: Claude` |
| `.claude/3-project/*-ext.md` | **Einmalig anlegen** via `--create-ext` — nie überschreiben |

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
| `{{AI_PROVIDER}}` | Wert aus `ai-provider` config-Feld |
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
agent-meta sync — 2026-04-05 10:00:00
============================================================
Config:    agent-meta.config.json
Source:    .agent-meta/ (v0.14.0)
Mode:      sync
Platforms: sharkord

ACTIONS
-------
[WRITE   ]  .claude/agents/orchestrator.md                 (1-generic/orchestrator.md)
[WRITE   ]  .claude/agents/developer.md                    (1-generic/developer.md)
[WRITE   ]  .claude/agents/feature.md                      (1-generic/feature.md)
[WRITE   ]  .claude/agents/agent-meta-manager.md           (1-generic/agent-meta-manager.md)
[WRITE   ]  .claude/agents/release.md                      (2-platform/sharkord-release.md)
[WRITE   ]  .claude/agents/docker.md                       (2-platform/sharkord-docker.md)
[UPDATE  ]  CLAUDE.md                                      (managed block)

SKIPPED
-------
[SKIP]   CLAUDE.md                                         (already exists)

INFO
----
[INFO]   .claude/agents/home-organization-specialist.md    (skill disabled)

WARNINGS
--------
(none)

SUMMARY
-------
7 action(s)  |  2 skipped  |  0 warning(s)
Logfile: sync.log
```

---

## Update-Flow

### Neues agent-meta Release einbinden

```bash
# 1. Submodul auf neue Version bringen
cd .agent-meta && git fetch && git checkout v0.14.0 && cd ..
git add .agent-meta

# 2. Version in Config aktualisieren
# agent-meta.config.json: "agent-meta-version": "0.14.0"

# 3. Sync ausführen — alle Agenten werden neu generiert
py .agent-meta/scripts/sync.py --config agent-meta.config.json

# 4. Ergebnis prüfen + committen
git add .claude/ agent-meta.config.json CLAUDE.md
git commit -m "chore: upgrade agent-meta to v0.14.0"
```

### Neue Variable ergänzen

```bash
# 1. Variable in agent-meta.config.json ergänzen
# 2. Sync ausführen — befüllt alle Agenten + CLAUDE.md managed block
py .agent-meta/scripts/sync.py --config agent-meta.config.json
```

---

## Was NIEMALS manuell editiert wird

```
.claude/agents/*.md    ← vollständig generiert
                          Manuelle Änderungen werden beim nächsten sync überschrieben
```

Projektspezifisches Wissen gehört in:
- **Extension** `.claude/3-project/<prefix>-<rolle>-ext.md` — additiv, nie überschrieben
- **Override** `.claude/3-project/<rolle>.md` — ersetzt Agenten komplett, nie überschrieben

---

## Abhängigkeiten des Scripts

- Python 3.8+
- Keine externen Dependencies (nur stdlib: `json`, `pathlib`, `argparse`, `re`, `shutil`, `datetime`)
