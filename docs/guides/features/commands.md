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
  (Projekt-eigene Commands: .claude/commands/ im Zielprojekt — keine eigene Schicht, siehe unten)
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

| Schicht (Quelle) | Pfad | Wann |
|------------------|------|------|
| 0-external | `commands/0-external/` | Commands aus externen Skill-Repos |
| 1-generic | `commands/1-generic/` | universell, alle Projekte |
| 2-platform | `commands/2-platform/` | Plattform-Overrides (Prefix: `<platform>-`) |

Bei gleichem Namen gewinnt die spätere Schicht. Es gibt **keine** `3-project`-Prioritätsschicht:
Projekt-eigene Commands liegen direkt im `commands_dir` des Providers (Claude: `.claude/commands/`)
und werden nicht angefasst, solange sie nicht im Index stehen. **Namenskollision:** heißt eine
Projektdatei wie ein agent-meta-Command, wird sie beim Sync **ohne Backup überschrieben** und landet im Managed-Index; entfällt der Upstream-Command später, löscht der Stale-Cleanup die Datei.

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
| **Copilot** | `.github/prompts/` | `.prompt.md` | Prompt files (`/name` in Copilot Chat); `commands_ext: .prompt.md` |
| **Mammouth** | `.mammouth/commands/` | `.md` | OpenCode-Fork; `$ARGUMENTS`-Syntax identisch zu Opencode |
| **ZCode** | `.zcode/commands/` | `.md` | Workspace-Commands (`~/.zcode/commands` = User-Scope, nicht gesynct) |

**Provider ohne project-scoped Command-Oberfläche (issue #807, bewusste Capability-Entscheidung):**

| Provider | Entscheidung | Begründung |
|----------|-------------|-----------|
| **Codex** | `commands: false` | Custom prompts existieren nur user-global (`${CODEX_HOME}/prompts`, `/prompts:<name>`) und sind zugunsten von Skills deprecated; project-scoped `.codex/prompts/` ist offener Feature-Request (openai/codex #9848), nicht implementiert. Eine Repo-Sync kann daher keine Codex-Commands ausliefern. |
| **KimiCode** | `commands: false` | Slash-Commands sind built-in oder Active Skills (`/skill:<name>`); es gibt kein projekt-lokales Custom-Command-Verzeichnis. Der Command-artige Kanal ist der bereits gesyncte `.kimi-code/skills/`-Baum. |

Die Capability-Flags stehen in `config/provider-capabilities.yaml` (`commands:`),
die Zielpfade/Formate in `config/ai-providers.yaml`
(`commands_dir` / `commands_ext` / `commands_format`). `scripts/lib/commands.py`
ist rein key-getrieben — keine `if provider == "Name"`-Verzweigung.


- **Variablen-Substitution:** `{{VARIABLE}}` Platzhalter werden wie in Rules substituiert
- **Stale-Tracking** via `.agent-meta-managed` in jedem Zielverzeichnis (Continue: `.agent-meta-commands-managed`) — veraltete Commands werden gelöscht
- **Projekt-eigene Commands** (nicht im Index) werden nie angefasst, außer bei Namenskollision (dann ohne Backup überschrieben)

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
| `requires_roles` | Nein | Liste von Rollen (`requires_roles: [documenter]`). Der Command wird nur generiert, wenn alle genannten Rollen im Active Set sind (IC-18 Nr. 9); sonst entfällt er und eine früher generierte Kopie wird als Managed-File entfernt. Der Key ist eine Generator-Direktive und erscheint nicht im generierten Command. |

Command-Bodies dürfen `{{#if ROLE_<ROLLE>_ACTIVE}}…{{else}}…{{/if}}` nutzen (z. B. `add-provider`: Delegation an `meta-feedback` nur, wenn die Rolle aktiv ist).

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
# Erstellt .claude/commands/<name>.md als leeres Template (nie überschrieben, außer bei Namenskollision — siehe Schichten-Modell)
py .agent-meta/scripts/sync.py --create-command mein-command
```

Das erzeugte File liegt in `.claude/commands/mein-command.md` und wird von sync.py **nie überschrieben**
(kein Eintrag im Index), außer bei Namenskollision mit einem agent-meta-Command (Überschreiben ohne Backup, siehe Schichten-Modell).

Alternativ: Command manuell in `.claude/commands/` anlegen — ebenfalls nie überschrieben (Ausnahme: Namenskollision, Überschreiben ohne Backup).

---

## Stale-Tracking

Jedes Zielverzeichnis enthält einen Index (`.agent-meta-managed`; bei Continue: `.agent-meta-commands-managed`, Key `commands_managed_index` in `config/ai-providers.yaml`, getrennt vom Rollen-Index):

```
doc-now.md
feedback.md
commit.md
analyze-logs.md
```

- Commands die in dieser Liste stehen aber nicht mehr in den Quellen existieren → werden gelöscht
- Commands, deren `requires_roles` nicht vollständig aktiv sind → werden nicht generiert bzw. gelöscht
- Commands die **nicht** in dieser Liste stehen (projekt-eigen) → werden nie angefasst, außer bei Namenskollision (Überschreiben ohne Backup)

---

## Beispiel: doc-now.md

`commands/1-generic/doc-now.md` ist der einfachste generische Command:

```markdown
---
description: Delegate to documenter agent to update CODEBASE_OVERVIEW.md immediately
allowed-tools: ["Agent"]
argument-hint: "[area or file to focus on]"
requires_roles: [documenter]
---

Delegate to the `documenter` agent with this task:

Update `CODEBASE_OVERVIEW.md` immediately. $ARGUMENTS
```

Aufruf: `/project:doc-now src/api` → delegiert mit dem Argument `src/api` an den `documenter`-Agenten.

---

## Verfügbare Framework-Commands (nach Sync)

| Command | Beschreibung |
|---------|-------------|
| `/project:add-mcp-server` | Geführtes Aktivieren eines MCP-Servers im Projekt |
| `/project:add-project-role` | Projektspezifische Agenten-Rolle (Override oder Extension) hinzufügen |
| `/project:add-provider` | AI-Provider zum Projekt hinzufügen oder per GitHub-Issue anfragen |
| `/project:admin` | Admin-UI-Server starten oder stoppen (inkl. Viz-Dashboard und MCP-Server) |
| `/project:analysis` | AST-Abhängigkeitsanalyse — zeigt, welche scripts/lib-Module voneinander abhängen |
| `/project:analyze-logs` | Log-Dateien auf Fehler, Muster und Probleme analysieren (Severity nach RFC 5424) |
| `/project:checkpoint` | Orchestrator-Checkpoints früherer Sessions auflisten oder fortsetzen |
| `/project:commit` | Änderungen stagen und Conventional Commit mit Nachrichtenvorschlag erstellen |
| `/project:consistency-check` | Agent-Templates, Commands und Querverweise auf Konsistenz prüfen (Versionen, Anker, Platzhalter, Cross-Refs) |
| `/project:diagnose` | Health-Check des agent-meta-Setups — Versionen, generierte Dateien, Isolation, gitignore |
| `/project:doc-now` | Documenter-Agent aktualisiert CODEBASE_OVERVIEW.md sofort |
| `/project:feedback` | Bug, Feature-Wunsch oder Verbesserung als standardisiertes GitHub-Issue melden |
| `/project:merge` | PR für den aktuellen Branch erstellen und nach main mergen |
| `/project:open-docs` | docs/-Ordner oder ein Analyse-Dokument im Terminal öffnen |
| `/project:pipelines` | Zeigt alle Quality-Pipelines (aktiv/deaktiviert, Stages, Quelle) — startet keine |
| `/project:release-check` | Release-Checkliste als reinen Check-Dry-Run ausführen (kein Tag, Push oder Commit) |
| `/project:report-bug` | Bug per Feedback-Agent als standardisiertes GitHub-Issue melden |
| `/project:set-preset` | DoD-Preset oder Speech-Mode des Projekts wechseln |
| `/project:set-release-checklist` | Release-Checklisten-Modus des Projekts ändern |
| `/project:test-orchestration` | Orchestration-Dry-Run durchführen und wichtige Funktionen validieren |
| `/project:update-extensions` | Managed-Blöcke in Projekt-Extension-Dateien nach agent-meta-Upgrade aktualisieren |
| `/project:update-meta` | Alle Agenten aus aktuellen agent-meta-Templates neu syncen, ohne Versions-Upgrade |
| `/project:upgrade-meta` | agent-meta-Submodul auf neueste Version upgraden und alle Agenten neu syncen |
| `/project:what-is` | Erklärt, was ein Agent tut — Rolle, Tools und Grenzen |

Quelle der Wahrheit: `commands/1-generic/` (Tabelle spiegelt die Dateien; Namensliste durch `tests/test_commands_docs_consistency.py` geprüft).

---

## Abgrenzung zu Agenten

| | Agenten (`.claude/agents/`) | Commands (`.claude/commands/`) |
|---|---|---|
| Format | Vollständige Persona / Markdown | Kurze Instruktion / Markdown |
| Kontext | Isoliertes Context Window | Läuft im Hauptchat |
| Scope | Komplexe, mehrstufige Aufgaben | Schnelle, wiederkehrende Einzel-Aktionen |
| Aufruf | `Agent(subagent_type="...")` | `/project:<name> [args]` |
| Von agent-meta generiert | Ja (0-external / 1-generic / 2-platform) | Ja (0-external / 1-generic / 2-platform) |

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
- Liegt die Datei im Index (`.agent-meta-managed`, Continue: `.agent-meta-commands-managed`)? → Projekt-eigene Commands dürfen dort **nicht** eingetragen sein
- Heißt die Datei wie ein agent-meta-Command? → Kollision, Projektdatei wird ohne Backup überschrieben; umbenennen
- Lösung: Command aus dem Index entfernen (oder neu als projekt-eigen anlegen)
