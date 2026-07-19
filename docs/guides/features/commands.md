# Commands — Slash Commands im agent-meta Layer-System

Commands sind Markdown-Dateien die Claude Code (und andere Plattformen) als aufrufbare
Slash-Commands bereitstellen. Agent-meta verwaltet sie im selben Schichten-Modell wie Rules und Agents.

---

## Konzept

```
commands/
  0-external/     ← Commands aus externen Skill-Repos (via Git Submodule)
  1-generic/      ← universelle Commands, gelten für alle Projekte
  2-platform/     ← plattformspezifisch (überschreibt 1-generic bei gleichem Dateinamen)
  ← 3-project: .claude/commands/ im Zielprojekt — nie von sync.py berührt (außer managed)
```

```
commands/1-generic/doc-now.md    ← Quelldatei in agent-meta
    ↓  sync.py COPY + Variablen-Substitution
.claude/commands/doc-now.md       ← immer synchronisiert
    ↓  Claude Code registriert automatisch als Slash Command
/project:doc-now [args]           ← im Hauptchat aufrufbar
```

---

## Schichten-Modell

| Schicht | Pfad | Prio | Wann |
|---------|------|------|------|
| 0-external | `commands/0-external/` | niedrig | Commands aus externen Skill-Repos |
| 1-generic | `commands/1-generic/` | mittel | universell, alle Projekte |
| 2-platform | `commands/2-platform/` | hoch | Plattform-Overrides (Prefix: `<platform>-`) |
| 3-project | `.claude/commands/` im Zielprojekt | — | Projekt-eigene Commands (nie überschrieben) |

**Naming für 2-platform:** `<platform>-<thema>.md` → Output: `<thema>.md`

---

## Sync-Verhalten je Provider

`sync.py` kopiert Command-Dateien automatisch bei jedem normalen Sync:

| Provider | Zielverzeichnis | Format | Besonderheiten |
|----------|----------------|--------|---------------|
| **Claude** | `.claude/commands/` | `.md` | As-is, keine Konvertierung |
| **Continue** | `.continue/prompts/` | `.md` | `invokable: true` wird in Frontmatter injiziert |
| **Gemini** | `.gemini/commands/` | `.toml` | Automatisch aus `.md` konvertiert; `$ARGUMENTS` → `{{args}}` |
| **Opencode** | `.opencode/commands/` | `.md` | As-is, `$ARGUMENTS`-Syntax identisch zu Claude |

- **Variablen-Substitution:** `{{VARIABLE}}` Platzhalter werden wie in Rules substituiert
- **Stale-Tracking** via `.agent-meta-managed` in jedem Zielverzeichnis — veraltete Commands werden gelöscht
- **Projekt-eigene Commands** (nicht in `.agent-meta-managed`) werden nie angefasst

---

## Command-Format (Frontmatter)

### Claude / Opencode

```markdown
---
description: Short description shown in the slash command picker
allowed-tools: ["Agent", "Bash", "Read"]
argument-hint: "[optional argument description]"
---

Command body here. Use $ARGUMENTS to receive optional user input.
```

| Feld | Pflicht | Bedeutung |
|------|---------|-----------|
| `description` | Ja | Kurzbeschreibung im Command-Picker |
| `allowed-tools` | Nein | Werkzeuge die dieser Command nutzen darf |
| `argument-hint` | Nein | Platzhalter-Hinweis für Argumente |

### Continue

Continue-Commands nutzen dasselbe Format — `sync.py` injiziert automatisch `invokable: true`:

```markdown
---
name: doc-now
description: Update CODEBASE_OVERVIEW.md immediately
invokable: true   ← wird automatisch eingefügt
---
```

---

## $ARGUMENTS-Token

`$ARGUMENTS` ist ein spezieller Platzhalter im Command-Body:

```markdown
Delegate to the `documenter` agent with this task:

Update `CODEBASE_OVERVIEW.md` immediately. $ARGUMENTS
```

- Claude ersetzt `$ARGUMENTS` durch alles was der User nach dem Command-Namen eingibt
- Bei Gemini wird `$ARGUMENTS` automatisch in `{{args}}` konvertiert
- Kein Argument übergeben → `$ARGUMENTS` wird leer (kein Fehler)

---

## Projektspezifische Commands anlegen

```bash
# Erstellt .claude/commands/<name>.md als leeres Template (nie überschrieben)
py .agent-meta/scripts/sync.py --create-command mein-command
```

Das erzeugte File liegt in `.claude/commands/mein-command.md` und wird von sync.py **nie überschrieben**
(kein Eintrag in `.agent-meta-managed`).

Alternativ: Command manuell in `.claude/commands/` anlegen — ebenfalls nie überschrieben.

---

## Stale-Tracking

Jedes Zielverzeichnis enthält eine `.agent-meta-managed` Datei (bei Continue: `.agent-meta-commands-managed`):

```
doc-now.md
feedback.md
commit.md
analyze-logs.md
```

- Commands die in dieser Liste stehen aber nicht mehr in den Quellen existieren → werden gelöscht
- Commands die **nicht** in dieser Liste stehen (projekt-eigen) → werden nie angefasst

---

## Beispiel: doc-now.md

`commands/1-generic/doc-now.md` ist der einfachste generische Command:

```markdown
---
description: Delegate to documenter agent to update CODEBASE_OVERVIEW.md immediately
allowed-tools: ["Agent"]
argument-hint: "[area or file to focus on]"
---

Delegate to the `documenter` agent with this task:

Update `CODEBASE_OVERVIEW.md` immediately. $ARGUMENTS
```

Aufruf: `/project:doc-now src/api` → delegiert mit dem Argument `src/api` an den `documenter`-Agenten.

---

## Verfügbare Framework-Commands (nach Sync)

| Command | Beschreibung |
|---------|-------------|
| `/project:doc-now` | CODEBASE_OVERVIEW sofort aktualisieren |
| `/project:feedback` | Bug oder Feature als GitHub Issue einreichen |
| `/project:commit` | Commit mit Conventional-Commits-Format erstellen |
| `/project:merge` | Feature-Branch mergen |
| `/project:analyze-logs` | Log-Dateien analysieren |
| `/project:diagnose` | Codebase-Problem diagnostizieren |
| `/project:upgrade-meta` | agent-meta auf neue Version upgraden |
| `/project:report-bug` | Bug-Report erstellen |
| `/project:set-preset` | DoD-Preset wechseln |
| `/project:pipelines` | Quality-Pipeline starten |

Vollständige Liste: `commands/1-generic/` Verzeichnis.

---

## Abgrenzung zu Agenten

| | Agenten (`.claude/agents/`) | Commands (`.claude/commands/`) |
|---|---|---|
| Format | Vollständige Persona / Markdown | Kurze Instruktion / Markdown |
| Kontext | Isoliertes Context Window | Läuft im Hauptchat |
| Scope | Komplexe, mehrstufige Aufgaben | Schnelle, wiederkehrende Einzel-Aktionen |
| Aufruf | `Agent(subagent_type="...")` | `/project:<name> [args]` |
| Von agent-meta generiert | Ja (1-generic / 2-platform) | Ja (1-generic / 2-platform) |

---

## Troubleshooting

**Command erscheint nicht im Picker:**
- Sync laufen lassen: `py .agent-meta/scripts/sync.py --config .meta-config/project.yaml`
- Datei in `.claude/commands/` vorhanden?
- Frontmatter korrekt (YAML valide, `description` gesetzt)?

**$ARGUMENTS wird nicht ersetzt:**
- Claude ersetzt `$ARGUMENTS` automatisch — keine manuelle Konfiguration nötig
- Bei Gemini: `{{args}}` prüfen (automatisch konvertiert)

**Command wird bei Sync gelöscht:**
- Liegt die Datei in `.agent-meta-managed`? → Projekt-eigene Commands dürfen dort **nicht** eingetragen sein
- Lösung: Command aus `.agent-meta-managed` entfernen (oder neu als projekt-eigen anlegen)
