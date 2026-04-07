# Hooks — Shell-Hooks im agent-meta Layer-System

Hooks sind Shell-Skripte die Claude Code automatisch vor oder nach bestimmten Tool-Aufrufen ausführt.
Agent-meta verwaltet sie im selben Schichten-Modell wie Rules und Agents.

---

## Konzept

```
hooks/
  0-external/     ← Hooks aus externen Skill-Repos (via Git Submodule)
  1-generic/      ← universelle Hooks, gelten für alle Projekte
  2-platform/     ← plattformspezifisch (überschreibt 1-generic bei gleichem Dateinamen)
  ← 3-project: .claude/hooks/ im Zielprojekt — nie von sync.py berührt (außer managed)
```

```
hooks/1-generic/dod-push-check.sh    ← Quelldatei in agent-meta
    ↓  sync.py COPY
.claude/hooks/dod-push-check.sh       ← immer synchronisiert (wie Rules)
    ↓  settings.json registration (nur wenn enabled: true)
.claude/settings.json → hooks.PreToolUse[...]
    ↓  Claude Code führt aus bei jedem Bash-Tool-Aufruf
Skript prüft Bedingung → exit 0 (allow) oder exit 2 (block)
```

---

## Schichten-Modell

| Schicht | Pfad | Prio | Wann |
|---------|------|------|------|
| 0-external | `hooks/0-external/` | niedrig | Hooks aus externen Skill-Repos |
| 1-generic | `hooks/1-generic/` | mittel | universell, alle Projekte |
| 2-platform | `hooks/2-platform/` | hoch | Plattform-Overrides (Prefix: `<platform>-`) |
| 3-project | `.claude/hooks/` im Zielprojekt | — | Projekt-eigene Hooks (nie überschrieben) |

**Naming für 2-platform:** `<platform>-<thema>.sh` → Output: `<thema>.sh`

---

## Sync-Verhalten

`sync.py` kopiert Hook-Skripte automatisch bei jedem normalen Sync:

- **Skripte werden immer kopiert** (wie Rules) — unabhängig von `enabled`
- **Registrierung in `settings.json`** nur wenn Projekt den Hook aktiviert hat
- **Stale-Tracking** via `.claude/hooks/.agent-meta-managed` — veraltete Skripte werden gelöscht
- **Projekt-eigene Hooks** (nicht in `.agent-meta-managed`) werden nie angefasst

---

## Hook-Skript-Format

Jedes Hook-Skript beginnt mit Metadaten-Kommentaren:

```bash
#!/bin/bash
# hook: mein-hook
# version: 1.0.0
# event: PreToolUse
# matcher: Bash
# description: Kurzbeschreibung was der Hook tut
# enabled_by_default: false
```

| Feld | Werte | Bedeutung |
|------|-------|-----------|
| `hook` | `<name>` | Eindeutiger Bezeichner |
| `version` | Semver | Versionierung (unabhängig von agent-meta) |
| `event` | `PreToolUse`, `PostToolUse`, `Notification`, `Stop`, `SubagentStop` | Claude Code Hook-Event |
| `matcher` | `Bash`, `Read`, `Write`, … | Tool-Name-Filter (leer = alle Tools) |
| `description` | Text | Kurzbeschreibung |
| `enabled_by_default` | `true`/`false` | Nur Dokumentation — sync.py ignoriert dieses Feld; Opt-in via Config |

---

## Hook aktivieren (Projekt Opt-in)

In `agent-meta.config.json`:

```json
{
  "hooks": {
    "dod-push-check": { "enabled": true }
  }
}
```

Nach dem nächsten Sync ist der Hook in `.claude/settings.json` registriert:

```json
{
  "permissions": { "allow": [], "deny": [] },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "bash .claude/hooks/dod-push-check.sh" }]
      }
    ]
  }
}
```

**Two-Gate-Prinzip:** Ein Hook wird nur registriert wenn:
1. Das Skript in `hooks/1-generic/` (oder 2-platform/0-external) existiert
2. `enabled: true` in `agent-meta.config.json` gesetzt ist

Fehlt der `hooks`-Block → kein Hook wird registriert (sicheres Default).

---

## Verfügbare Hooks

| Hook | Event | Matcher | Beschreibung |
|------|-------|---------|-------------|
| `dod-push-check` | `PreToolUse` | `Bash` | Blockiert `git push` wenn Tests nicht grün sind |

---

## Projekt-eigene Hooks anlegen

```bash
# Erstellt .claude/hooks/<name>.sh aus Template (nie überschrieben)
py .agent-meta/scripts/sync.py --config agent-meta.config.json --create-hook mein-hook
```

Das erzeugte Skript liegt in `.claude/hooks/mein-hook.sh` und wird von sync.py **nie überschrieben**
(kein Eintrag in `.agent-meta-managed`).

Zum Aktivieren:
```json
"hooks": {
  "mein-hook": { "enabled": true }
}
```

---

## Hook-Laufzeit: Wie Claude Code Hooks ausführt

Claude Code führt Hooks als Shell-Befehle aus. Das Skript:
- Empfängt JSON-Kontext via **stdin**
- Gibt Feedback via **stdout/stderr** (wird Claude als Kontext angezeigt)
- **Exit 0**: Tool-Aufruf erlaubt
- **Exit 2**: Tool-Aufruf blockiert (stdout wird Claude angezeigt)
- **Anderer Exit-Code ≠ 0**: Fehler (wird geloggt)

**Stdin-Format (Claude Code):**
```json
{
  "session_id": "...",
  "transcript_path": "...",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "git push origin main"
  }
}
```

---

## dod-push-check: Konfiguration

Der `dod-push-check`-Hook liest den Test-Command aus:

1. **Umgebungsvariable** `AGENT_META_TEST_COMMAND` (höchste Priorität)
2. **`variables.TEST_COMMAND`** in `agent-meta.config.json`
3. Falls keines gesetzt: Push wird blockiert mit Hinweis zur Konfiguration

```json
{
  "variables": {
    "TEST_COMMAND": "bun test"
  },
  "hooks": {
    "dod-push-check": { "enabled": true }
  }
}
```

---

## Abgrenzung zu Rules

| | Rules (`.claude/rules/`) | Hooks (`.claude/hooks/`) |
|---|---|---|
| Format | Markdown | Shell-Skript |
| Laden | Automatisch in Agent-Kontext | Claude Code führt aus (settings.json) |
| Scope | Kontext für Agenten | Automatisierung / Enforcement |
| Aktivierung | Immer aktiv | Opt-in via `agent-meta.config.json` |
| Stale-Cleanup | `.agent-meta-managed` | `.agent-meta-managed` |

---

## Troubleshooting

**Hook wird nicht ausgeführt:**
- `enabled: true` in `agent-meta.config.json` gesetzt?
- Sync laufen lassen: `py .agent-meta/scripts/sync.py --config agent-meta.config.json`
- Eintrag in `.claude/settings.json` unter `hooks.PreToolUse` prüfen

**Hook blockiert fälschlicherweise:**
- Hook temporär deaktivieren: `"enabled": false` in Config + Sync
- Oder Skript direkt editieren: `.claude/hooks/dod-push-check.sh`

**TEST_COMMAND nicht gefunden:**
- `variables.TEST_COMMAND` in `agent-meta.config.json` setzen
- Oder `export AGENT_META_TEST_COMMAND='bun test'` in Shell-Profil
