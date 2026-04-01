# agent-meta Sync-Konzept

Dieses Dokument beschreibt das Konzept zur Einbindung von `agent-meta` in konkrete
Projekte über ein versioniertes Python-Script und eine Konfigurationsdatei.

---

## Kernidee

Agenten-Dateien in einem Projekt sind **generierter Output** — kein manuell
gepflegter Inhalt. Die einzige manuelle Datei ist die `CLAUDE.md` des Projekts.

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
    1-generic/       ← universelle Agenten
    2-platform/      ← plattformspezifische Agenten
    3-project/       ← projektspezifische Overrides (selten)
  scripts/
    sync.py          ← das Sync-Script (versioniert mit agent-meta)
  howto/
    sync-concept.md  ← dieses Dokument
    CLAUDE.project-template.md
```

### Im Projekt-Repository

```
<projekt>/
  .agent-meta/               ← Git Submodule (agent-meta Repository)
  agent-meta.config.json     ← Sync-Konfiguration (manuell gepflegt, versioniert)
  CLAUDE.md                  ← bei --init generiert, danach manuell gepflegt
  .claude/
    agents/                  ← vollständig generiert, nie manuell editieren
      <project-short>.md
      <prefix>-developer.md
      <prefix>-tester.md
      ...
  sync.log                   ← Protokoll des letzten Sync-Laufs (gitignore empfohlen)
```

---

## Entscheidungen

| Thema | Entscheidung |
|-------|-------------|
| agent-meta Einbindung | **Git Submodule** unter `.agent-meta/` |
| Script-Aufruf | Immer aus agent-meta: `python .agent-meta/scripts/sync.py` |
| CLAUDE.md nach `--init` | Tabu für normale Syncs — nur `--only-variables` darf Platzhalter ersetzen |
| Fehlende Variablen | **Warning + weitermachen** — Platzhalter bleibt sichtbar, Logfile fasst alles zusammen |

---

## agent-meta.config.json

Die einzige Konfigurationsdatei die das Projekt pflegt.

```json
{
  "agent-meta-version": "1.2.0",

  "platforms": ["sharkord"],

  "project": {
    "name": "sharkord-vid-with-friends",
    "prefix": "vwf",
    "short": "vid-with-friends"
  },

  "variables": {
    "PROJECT_NAME":         "sharkord-vid-with-friends",
    "PREFIX":               "vwf",
    "PROJECT_SHORT":        "vid-with-friends",
    "PLATFORM":             "Sharkord Plugin SDK v0.0.16",
    "RUNTIME":              "Bun (NICHT Node.js)",
    "KEY_DEPENDENCIES":     "@sharkord/plugin-sdk@0.0.16, mediasoup, tRPC, React, Zod",
    "TARGET_PLATFORM":      "Sharkord Plugin SDK v0.0.16",
    "BUILD_COMMAND":        "bun run build",
    "TEST_COMMAND":         "bun test",
    "SERVICE_NAME":         "sharkord",
    "CONTAINER_NAME":       "sharkord-dev",
    "PLUGIN_DIR_NAME":      "sharkord-vid-with-friends",
    "SHARKORD_VERSION":     "v0.0.16",
    "SHARKORD_URL":         "http://localhost:3000",
    "WEB_PORT":             "3000",
    "MEDIASOUP_PORT":       "40000",
    "SHARKORD_MIN_VERSION": "0.0.7"
  }
}
```

### Felder

| Feld | Bedeutung |
|------|-----------|
| `agent-meta-version` | Welches Release von agent-meta genutzt wird — zur Dokumentation und Validierung |
| `platforms` | Liste aktiver Plattformen. Bestimmt welche `2-platform/<plattform>-*.md` einbezogen werden. Mehrere möglich: `["sharkord", "github-actions"]` |
| `project.name` | Vollständiger Projektname |
| `project.prefix` | Kurzpräfix für Agent-Dateinamen (`vwf-developer.md`) |
| `project.short` | Kurzname für den Orchestrator-Dateinamen (`vid-with-friends.md`) |
| `variables` | Alle `{{VARIABLE}}` die in Agenten-Dateien und CLAUDE.md ersetzt werden |

---

## sync.py — Verhalten

### Aufruf-Modi

```bash
# Erstmalige Einrichtung — generiert CLAUDE.md + alle Agenten
python .agent-meta/scripts/sync.py --init --config agent-meta.config.json

# Normale Aktualisierung — überschreibt Agenten, aktualisiert keine CLAUDE.md
python .agent-meta/scripts/sync.py --config agent-meta.config.json

# Nur Variablen in CLAUDE.md nachträglich befüllen (kein Agent-Sync)
python .agent-meta/scripts/sync.py --config agent-meta.config.json --only-variables

# Vorschau ohne Schreiben
python .agent-meta/scripts/sync.py --config agent-meta.config.json --dry-run

# Alle Modi erzeugen ein Logfile
# → sync.log im Projekt-Root
```

### Schreibverhalten pro Schicht

| Schicht | Verhalten |
|---------|-----------|
| `1-generic/` | **Immer überschreiben** — generierter Output |
| `2-platform/` | **Immer überschreiben** — für alle konfigurierten Plattformen |
| `3-project/` | **Überschreiben nur wenn Datei in `3-project/` existiert** |
| `CLAUDE.md` | **Nur bei `--init`** generieren — bei `--only-variables` nur `{{PLATZHALTER}}` ersetzen |

### Plattform-Erkennung

Das Script liest `platforms` aus der Config und sucht in `2-platform/` nach Dateien,
deren Dateiname mit `<plattform>-` beginnt:

```
config: "platforms": ["sharkord"]
→ 2-platform/sharkord-docker.md   → .claude/agents/vwf-docker.md
→ 2-platform/sharkord-release.md  → .claude/agents/vwf-release.md

config: "platforms": ["sharkord", "github-actions"]
→ alle sharkord-* und github-actions-* Dateien werden einbezogen
```

Existiert für eine Rolle ein Plattform-Agent, **ersetzt** er den Generic-Agenten.
Existiert kein Plattform-Agent für eine Rolle, gilt der Generic-Agent.

### Dateinamen-Mapping

Das Script baut die Ziel-Dateinamen aus Config-Werten:

| Quell-Datei | Ziel-Datei |
|-------------|------------|
| `1-generic/orchestrator.md` | `.claude/agents/<project.short>.md` |
| `1-generic/developer.md` | `.claude/agents/<prefix>-developer.md` |
| `1-generic/tester.md` | `.claude/agents/<prefix>-tester.md` |
| `1-generic/validator.md` | `.claude/agents/<prefix>-validator.md` |
| `1-generic/requirements.md` | `.claude/agents/<prefix>-requirements.md` |
| `1-generic/documenter.md` | `.claude/agents/<prefix>-documenter.md` |
| `2-platform/sharkord-release.md` | `.claude/agents/<prefix>-release.md` |
| `2-platform/sharkord-docker.md` | `.claude/agents/<prefix>-docker.md` |

Die Rolle wird aus dem Dateinamen extrahiert (nach dem Plattform-Präfix bzw. direkt):
`sharkord-release.md` → Rolle `release` → `<prefix>-release.md`

### Variablen-Befüllung

Alle `{{VARIABLE}}` in jeder Agenten-Datei werden mit Werten aus `variables` ersetzt.
Zusätzlich werden `{{PREFIX}}` und `{{PROJECT_SHORT}}` aus `project` befüllt.

**Reihenfolge:** `variables` > `project.*` > interne Script-Werte

Unbekannte Variablen (kein Wert in Config):
- Platzhalter bleibt unverändert sichtbar
- Eintrag im Logfile unter `WARNINGS`

### Frontmatter-Generierung

Das Script setzt `name` und `description` im Frontmatter jeder Agenten-Datei
korrekt für das Projekt:

```yaml
# Aus 1-generic/developer.md wird in vwf-developer.md:
---
name: vwf-developer
description: "Developer-Agent für sharkord-vid-with-friends."
tools: [...]
---
```

---

## Logfile (sync.log)

Nach jedem Lauf wird `sync.log` im Projekt-Root geschrieben (überschreibt den vorherigen).

```
=====================================
agent-meta sync — 2026-04-01 14:32:11
=====================================
Config:    agent-meta.config.json
Source:    .agent-meta/ (v1.2.0)
Mode:      sync
Platforms: sharkord

ACTIONS
-------
[INIT]   CLAUDE.md                                     (howto/CLAUDE.project-template.md)
[WRITE]  .claude/agents/vid-with-friends.md            (1-generic/orchestrator.md)
[WRITE]  .claude/agents/vwf-developer.md               (1-generic/developer.md)
[WRITE]  .claude/agents/vwf-tester.md                  (1-generic/tester.md)
[WRITE]  .claude/agents/vwf-validator.md               (1-generic/validator.md)
[WRITE]  .claude/agents/vwf-requirements.md            (1-generic/requirements.md)
[WRITE]  .claude/agents/vwf-documenter.md              (1-generic/documenter.md)
[WRITE]  .claude/agents/vwf-release.md                 (2-platform/sharkord-release.md)
[WRITE]  .claude/agents/vwf-docker.md                  (2-platform/sharkord-docker.md)
[SKIP]   .claude/agents/vwf-custom.md                  (kein 3-project/ Pendant)

WARNINGS
--------
[WARN]   Variable EXTRA_STARTUP_INFO nicht in config — Platzhalter bleibt in:
           .claude/agents/vwf-docker.md (Zeile 99)

SUMMARY
-------
9 Agenten verarbeitet  |  1 übersprungen  |  1 Warnung
Logfile: sync.log
```

---

## Update-Flow

### Neues agent-meta Release einbinden

```bash
# 1. Submodule auf neue Version bringen
cd .agent-meta && git fetch && git checkout v1.3.0 && cd ..
git add .agent-meta
git commit -m "chore: update agent-meta to v1.3.0"

# 2. Version in Config aktualisieren
# agent-meta.config.json: "agent-meta-version": "1.3.0"

# 3. Sync ausführen — alle Agenten werden neu generiert
python .agent-meta/scripts/sync.py --config agent-meta.config.json

# 4. Ergebnis prüfen + committen
git add .claude/ agent-meta.config.json sync.log
git commit -m "chore: sync agents to agent-meta v1.3.0"
```

### Neue Variable in Config ergänzen und in CLAUDE.md nachträglich einsetzen

```bash
# 1. Variable in agent-meta.config.json ergänzen
# 2. Nur Variablen in CLAUDE.md aktualisieren (kein Agenten-Sync)
python .agent-meta/scripts/sync.py --config agent-meta.config.json --only-variables
```

---

## Erstmalige Projekt-Einrichtung

```bash
# 1. agent-meta als Git Submodule einbinden
git submodule add https://github.com/<org>/agent-meta .agent-meta
git submodule update --init --recursive

# 2. Konfiguration anlegen (aus Beispiel)
cp .agent-meta/agent-meta.config.example.json agent-meta.config.json
# → Config befüllen: version, platforms, project, variables

# 3. Initiales Setup
python .agent-meta/scripts/sync.py --init --config agent-meta.config.json

# 4. Prüfen (sync.log lesen)
cat sync.log

# 5. Ergebnis committen
git add .agent-meta .claude/ CLAUDE.md agent-meta.config.json sync.log
git commit -m "chore: initialize agent-meta v1.2.0"

# 6. sync.log in .gitignore (optional — oder bewusst versionieren)
echo "sync.log" >> .gitignore
```

---

## Was NIEMALS manuell editiert wird

```
.claude/agents/*.md    ← vollständig generiert
                          Manuelle Änderungen werden beim nächsten sync überschrieben
```

**Ausnahme:** Echter projektspezifischer Override →
Datei in `agent-meta/agents/3-project/` im agent-meta Fork/Branch anlegen.

---

## Abhängigkeiten des Scripts

- Python 3.8+
- Keine externen Dependencies (nur stdlib: `json`, `pathlib`, `argparse`, `re`, `shutil`, `datetime`)
