# agent-meta Sync-Konzept

Dieses Dokument beschreibt das Konzept zur Einbindung von `agent-meta` in konkrete
Projekte über ein versioniertes Python-Script und eine Konfigurationsdatei.

---

## Kernidee

Agenten-Dateien in einem Projekt sind **generierter Output** — kein manuell
gepflegter Inhalt. Die einzige manuelle Datei ist die `CLAUDE.md` des Projekts.

```
agent-meta (Release vX.Y.Z)
    + agent-meta.config.json (im Projekt)
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
  agent-meta.config.json   ← Sync-Konfiguration (manuell gepflegt, versioniert)
  CLAUDE.md                ← beim --init generiert, danach manuell gepflegt
  .claude/
    agents/                ← vollständig generiert, nie manuell editieren
      <project-short>.md
      <prefix>-developer.md
      <prefix>-tester.md
      ...
```

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
    "PROJECT_NAME":        "sharkord-vid-with-friends",
    "PREFIX":              "vwf",
    "PROJECT_SHORT":       "vid-with-friends",
    "PLATFORM":            "Sharkord Plugin SDK v0.0.16",
    "RUNTIME":             "Bun (NICHT Node.js)",
    "KEY_DEPENDENCIES":    "@sharkord/plugin-sdk@0.0.16, mediasoup, tRPC, React, Zod",
    "TARGET_PLATFORM":     "Sharkord Plugin SDK v0.0.16",
    "BUILD_COMMAND":       "bun run build",
    "TEST_COMMAND":        "bun test",
    "SERVICE_NAME":        "sharkord",
    "CONTAINER_NAME":      "sharkord-dev",
    "PLUGIN_DIR_NAME":     "sharkord-vid-with-friends",
    "SHARKORD_VERSION":    "v0.0.16",
    "SHARKORD_URL":        "http://localhost:3000",
    "WEB_PORT":            "3000",
    "MEDIASOUP_PORT":      "40000",
    "SHARKORD_MIN_VERSION": "0.0.7"
  }
}
```

### Felder

| Feld | Bedeutung |
|------|-----------|
| `agent-meta-version` | Welches Release von `agent-meta` genutzt wird |
| `platforms` | Liste aktiver Plattformen — bestimmt welche `2-platform/` Agenten einbezogen werden. Mehrere möglich: `["sharkord", "github-actions"]` |
| `project.name` | Vollständiger Projektname |
| `project.prefix` | Kurzpräfix für Agent-Dateinamen |
| `project.short` | Kurzname für den Orchestrator-Dateinamen |
| `variables` | Alle `{{PLATZHALTER}}` die in Agenten-Dateien und `CLAUDE.md` ersetzt werden |

---

## sync.py — Verhalten

### Aufruf-Modi

```bash
# Erstmalige Einrichtung — generiert CLAUDE.md + alle Agenten
python sync.py --init --config agent-meta.config.json

# Normale Aktualisierung — überschreibt Agenten, befüllt Variablen in CLAUDE.md
python sync.py --config agent-meta.config.json

# Vorschau ohne Schreiben
python sync.py --config agent-meta.config.json --dry-run

# Bestimmtes agent-meta Release verwenden (überschreibt config-Version)
python sync.py --config agent-meta.config.json --version 1.3.0
```

### Schreibverhalten pro Schicht

| Schicht | Verhalten |
|---------|-----------|
| `1-generic/` | **Immer überschreiben** — generierter Output, nie manuell editieren |
| `2-platform/` | **Immer überschreiben** — für alle in `platforms` konfigurierten Plattformen |
| `3-project/` | **Nur überschreiben wenn Datei in `3-project/` existiert** — ein projektspezifischer Override wird ersetzt, wenn agent-meta eine neuere Version hat |
| `CLAUDE.md` | **Nur bei `--init`** — danach nie mehr angefasst |

### Plattform-Erkennung

Das Script liest `platforms` aus der Config und sucht in `2-platform/` nach Dateien,
deren Präfix mit einem der konfigurierten Plattform-Namen übereinstimmt:

```
config: "platforms": ["sharkord"]
→ verwendet:  2-platform/sharkord-docker.md
              2-platform/sharkord-release.md
              (alle Dateien mit Präfix "sharkord-")

config: "platforms": ["sharkord", "github-actions"]
→ verwendet:  2-platform/sharkord-docker.md
              2-platform/sharkord-release.md
              2-platform/github-actions-ci.md
              (alle Dateien beider Präfixe)
```

Wenn für eine Rolle ein Plattform-Agent existiert, **ersetzt** er den Generic-Agenten
für diese Rolle. Wenn nicht, wird der Generic-Agent verwendet.

### Variablen-Befüllung

Das Script ersetzt alle `{{VARIABLE}}` Vorkommen in jeder Agenten-Datei
mit den Werten aus `variables` in der Config.

Bei `--init` zusätzlich in `CLAUDE.md` (einmalig).

Unbekannte Variablen (kein Wert in Config) → **Warning**, Platzhalter bleibt stehen.

### Ausgabe

```
agent-meta sync v1.2.0
Config:   agent-meta.config.json
Source:   agent-meta v1.2.0
Platform: sharkord

[INIT]      CLAUDE.md                              (erstellt)

[WRITE]     .claude/agents/vid-with-friends.md     (1-generic/orchestrator.md)
[WRITE]     .claude/agents/vwf-developer.md        (1-generic/developer.md)
[WRITE]     .claude/agents/vwf-tester.md           (1-generic/tester.md)
[WRITE]     .claude/agents/vwf-validator.md        (1-generic/validator.md)
[WRITE]     .claude/agents/vwf-requirements.md     (1-generic/requirements.md)
[WRITE]     .claude/agents/vwf-documenter.md       (1-generic/documenter.md)
[WRITE]     .claude/agents/vwf-release.md          (2-platform/sharkord-release.md)
[WRITE]     .claude/agents/vwf-docker.md           (2-platform/sharkord-docker.md)

[WARN]      Variable EXTRA_STARTUP_INFO nicht in config — Platzhalter bleibt

8 Agenten geschrieben. 1 Warnung.
```

---

## Update-Flow

### Neues agent-meta Release einbinden

1. `agent-meta-version` in `agent-meta.config.json` auf neue Version setzen
2. Script erneut ausführen — alle Agenten werden überschrieben
3. `CLAUDE.md` bleibt unverändert (manuell gepflegt)

```bash
# agent-meta.config.json: "agent-meta-version": "1.3.0"
python sync.py --config agent-meta.config.json
```

### Neues Plattform-Modul einbinden

1. Plattform-Name zu `platforms` in Config hinzufügen
2. Neue Variablen in `variables` ergänzen
3. Script ausführen — neue Plattform-Agenten werden hinzugefügt

### Variable nachträglich befüllen

Nur Variablen in `CLAUDE.md` aktualisieren (ohne Agenten neu zu schreiben):

```bash
python sync.py --config agent-meta.config.json --only-variables
```

---

## Was NIEMALS manuell editiert wird

```
.claude/agents/*.md    ← vollständig generiert
                          Änderungen werden beim nächsten sync überschrieben
```

**Ausnahme:** Wenn ein echter projektspezifischer Override nötig ist →
Datei in `agent-meta/agents/3-project/` anlegen, nicht direkt in `.claude/agents/`.

---

## Versionierung

Das Script `sync.py` ist Teil des `agent-meta` Repositories und wird mit ihm
zusammen getaggt und released. Ein Projekt pinnt seine Version über:

```json
{ "agent-meta-version": "1.2.0" }
```

und kann damit jederzeit reproduzierbar regenerieren — auch auf einer alten Version.

---

## Abhängigkeiten des Scripts

- Python 3.8+
- Keine externen Dependencies (nur stdlib: `json`, `pathlib`, `argparse`, `re`, `shutil`)
- Optionaler Parameter `--agent-meta-path` falls agent-meta nicht als Git-Submodule
  oder benachbartes Verzeichnis liegt

---

## Empfohlene Projekt-Einrichtung

```bash
# 1. agent-meta als Git-Submodule einbinden (empfohlen)
git submodule add https://github.com/<org>/agent-meta .agent-meta
git submodule update --init

# 2. Konfiguration anlegen
cp .agent-meta/howto/CLAUDE.project-template.md agent-meta.config.json
# → Config befüllen

# 3. Initiales Setup
python .agent-meta/scripts/sync.py --init --config agent-meta.config.json

# 4. Generierte Dateien committen
git add .claude/ CLAUDE.md agent-meta.config.json
git commit -m "chore: initialize agent-meta v1.2.0"
```

---

## Offene Entscheidungen (Feedback erbeten)

1. **Submodule vs. lokale Kopie vs. Download:**
   Soll agent-meta als Git-Submodule, als lokale Kopie im Repo, oder
   durch das Script automatisch heruntergeladen werden?

2. **Wo liegt sync.py beim Aufruf:**
   Im agent-meta Verzeichnis (`.agent-meta/scripts/sync.py`) oder
   soll es ins Projekt-Root kopiert werden?

3. **Variablen in CLAUDE.md beim Update:**
   Bei `sync --only-variables` — soll das Script Variablen in der
   bestehenden `CLAUDE.md` nachträglich ersetzen können, auch wenn
   sie manuell erweitert wurde? Oder ist `CLAUDE.md` nach `--init` tabu?

4. **Fehlende Variablen:**
   Warning und weitermachen, oder Fehler und abbrechen?
