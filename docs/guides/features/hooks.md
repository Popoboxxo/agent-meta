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

**0-external auch für externe CLI-Tool-Wrapper:** Die `0-external/`-Schicht dient nicht nur Hooks aus externen Skill-Repos (via Git Submodule), sondern auch als Heimat für maintainer-authored Shell-Wrapper um lokal installierte CLI-Dev-Tools wie `graphify`. Diese Wrapper-Skripte verhindern dass Tools zur Laufzeit generierte Dateien selbst mutieren — stattdessen registrieren sie sich über einen von Hand kuratierten Eintrag in `config/plugin-catalog.yaml`, und `sync.py` rendert deren Hook-Wiring deterministisch. Beispiel: `hooks/0-external/graphify-search-guard.sh` leitet Bash/Grep-Aufrufe an die lokale `graphify`-Binary weiter (falls installiert) oder durchlässt sie mit `exit 0` als Fallback.

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
| `hook` | `<name>` | Eindeutiger Bezeichner. **Fehlt dieses Feld, ist die Datei kein Hook, sondern ein Helper** (siehe unten) |
| `version` | Semver | Versionierung (unabhängig von agent-meta) |
| `event` | `PreToolUse`, `PostToolUse`, `Notification`, `Stop`, `SubagentStop` | Claude Code Hook-Event. `Manual` = kein Runtime-Event — wird explizit aufgerufen, nie in `settings.json` registriert |
| `matcher` | `Bash`, `Read`, `Write`, … | Tool-Name-Filter (leer = alle Tools) |
| `description` | Text | Kurzbeschreibung |
| `provider` | Provider-Name | Optional: Skript nur für diesen Provider deployen (z.B. `Claude`) |
| `hook_protocol` | Protokoll-Key | Optional: Skript nur deployen, wenn der Provider dasselbe `hook_protocol` spricht (z.B. `antigravity-hooks-json`) |
| `enabled_by_default` | `true`/`false` | Default-Aktivierungszustand. `sync.py` registriert den Hook genau dann automatisch, wenn `true`; pro Projekt überschreibbar via `hooks.<name>.enabled` |

**Helper-Skripte:** Dateien ohne `# hook:`-Header sind keine eigenständigen Hooks.
Sie werden immer mitkopiert, aber **nie registriert** — sie werden von einem
registrierten Hook aufgerufen (z.B. `orchestrator-guard-impl.sh`,
`repo-containment-impl.sh`) oder sind protokoll-spezifisch
(`antigravity-json-adapter.sh`, nur bei `hook_protocol: antigravity-hooks-json`
deployt). Ein Helper ohne Registrierung ist **kein toter Code**.

**`Manual`-Hooks:** `pre-release-check.sh` deklariert `event: Manual`. Es wird
vom `release`-Agenten explizit per `Bash` aufgerufen (siehe
`docs/RELEASE_GATES.md`) und darf **nicht** über `hooks: { pre-release-check:
{ enabled: true } }` registriert werden — `sync.py` ignoriert eine solche
Aktivierung bewusst, damit kein ungültiger `Manual`-Event-Bucket in
`settings.json` landet.

**Ausführbarkeits-Bit (issue #601):** von `sync.py` generierte Hook-Kopien in `<hooks_dir>/*.sh`
haben absichtlich **kein** `+x` (`chmod 755`) — sie werden ausschließlich über
`bash <hooks_dir>/<datei>.sh` aufgerufen (siehe `settings.json`-Eintrag unten), nie direkt
ausgeführt. Kein `chmod +x` nötig, kein Bug.

**cwd-Unabhängigkeit (issue #851):** Claude Code löst relative Kommandos gegen das Prozess-CWD auf.
Ein aus einem Unterverzeichnis gestarteter (oder ein gespawnter Subagent-)Prozess würde den Hook
sonst stillschweigend überspringen. Der Provider-Config-Key `hook-command-anchor` (Claude:
`${CLAUDE_PROJECT_DIR}`) wird deshalb jedem registrierten Kommando vorangestellt. Fehlt der Key
(z.B. Antigravity, das relativ zur `hooks.json` auflöst), bleibt die relative Form unverändert.

---

## Hook aktivieren (Projekt Opt-in)

In `.meta-config/project.yaml`:

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
        "hooks": [{ "type": "command", "command": "bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/dod-push-check.sh" }]
      }
    ]
  }
}
```

**Two-Gate-Prinzip:** Ein Hook wird nur registriert wenn:
1. Das Skript in `hooks/1-generic/` (oder 2-platform/0-external) existiert
2. `enabled: true` in `.meta-config/project.yaml` gesetzt ist

Fehlt der `hooks`-Block → kein Hook wird registriert (sicheres Default).

---

## Verfügbare Hooks

`Default` = `enabled_by_default`-Header; ein Hook ohne Registrierung ist
entweder opt-in (bewusst) oder ein Helper (kein `# hook:`-Header). Der
Consistency-Check `hooks.enabled-but-not-registered` stellt sicher, dass ein
aktivierter Hook auch tatsächlich in `settings.json` landet.

| Hook | Event | Matcher | Default | Beschreibung |
|------|-------|---------|---------|-------------|
| `orchestrator-guard` | `PreToolUse` | alle | **on** | Erzwingt die Orchestrator-Pflicht |
| `repo-containment` | `PreToolUse` | alle | **on** | Repo-Containment (Schreibzugriffe auf die Projektwurzel) |
| `dod-push-check` | `PreToolUse` | `Bash` | off | Blockiert `git push` wenn Tests nicht grün sind |
| `sync-on-config-change` | `PostToolUse` | `Write`, `Edit` | off | Triggert `sync.py`-Re-run wenn `.meta-config/project.yaml` geändert wird |
| `lifecycle-check` | `PostToolUse` | `Bash` | off | Erkennt Git-Events (Release-Tag, Merge) und triggert Lifecycle-Tasks |
| `auto-github-release` | `PostToolUse` | `Bash` | off | Erstellt GitHub-Releases nach einem Tag (opt-in, Seiteneffekte) |
| `graphify-read-guard` | `PreToolUse` | `Read`, `Glob` | off | Leitet Read/Glob an die lokale `graphify`-Binary weiter (0-external) |
| `graphify-search-guard` | `PreToolUse` | `Bash`, `Grep` | off | Leitet Bash/Grep an die lokale `graphify`-Binary weiter (0-external) |
| `viz-log` | `PreToolUse` | alle | off* | Loggt Tool-Events für das Viz-Dashboard; *auto-on bei `viz.enabled` + `mode: dynamic/full` |
| `pre-release-check` | `Manual` | — | off | Release-Gate-Dispatcher — wird explizit vom `release`-Agenten aufgerufen, **nie** registriert |

**Helper (keine eigenständigen Hooks, werden nie registriert):**
`orchestrator-guard-impl.sh`, `repo-containment-impl.sh`,
`antigravity-json-adapter.sh` (nur bei `hook_protocol: antigravity-hooks-json`),
`lib/hook_common.sh` (siehe `sync_hook_lib()`), `release-gates/*.sh`
(Plugin-Verzeichnis des `pre-release-check`-Dispatchers).

---

## Projekt-eigene Hooks anlegen

```bash
# Erstellt .claude/hooks/<name>.sh aus Template (nie überschrieben)
py .agent-meta/scripts/sync.py --create-hook mein-hook
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
- **Exit 2**: Tool-Aufruf blockiert — **nur stderr** wird Claude als Blockierungsgrund angezeigt,
  stdout wird bei Exit 2 ignoriert (issue #396/#593 — jeder Hook in diesem Repo schreibt seine
  Block-Begründung deshalb konsequent nach stderr, siehe `orchestrator-guard.sh`-Header-Kommentar)
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
2. **`variables.TEST_COMMAND`** in `.meta-config/project.yaml`
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

## sync-on-config-change: Automatische Re-Sync

Dieser Hook erkennt wenn `.meta-config/project.yaml` geändert wird und triggert automatische `sync.py`-Re-Generierung.

**Trigger:**
- Write oder Edit-Tool-Aufruf auf `.meta-config/project.yaml`
- Wird nach dem Schreiben erkannt (PostToolUse-Event)

**Aktion:**
1. Hook prüft ob `.meta-config/project.yaml` geändert wurde
2. Schreibt pending-task in `.claude/pending-tasks.md` für `agent-meta-manager`
3. `agent-meta-manager` merkt beim nächsten Start dass sync.py laufen muss
4. agent-meta-manager führt `sync.py` aus und updated alle context files

**Konfiguration:**

```yaml
hooks:
  sync-on-config-change:
    enabled: true

lifecycle-triggers:
  on-config-change:
    - agent: agent-meta-manager
      task: "Re-run sync.py to regenerate provider context files."
```

**Vorteil:** Keine manuellen `sync.py`-Aufrufe nötig — regeneration läuft vollautomatisch.

**Wann sinnvoll:** Projekte die `.meta-config/project.yaml` öfters ändern (neue Provider, neue Rollen, Konfiguration-Tuning).

---

## Abgrenzung zu Rules

| | Rules (`.claude/rules/`) | Hooks (`.claude/hooks/`) |
|---|---|---|
| Format | Markdown | Shell-Skript |
| Laden | Automatisch in Agent-Kontext | Claude Code führt aus (settings.json) |
| Scope | Kontext für Agenten | Automatisierung / Enforcement |
| Aktivierung | Immer aktiv | Opt-in via `.meta-config/project.yaml` |
| Stale-Cleanup | `.agent-meta-managed` | `.agent-meta-managed` |

---

## Troubleshooting

**Hook wird nicht ausgeführt:**
- `enabled: true` in `.meta-config/project.yaml` gesetzt?
- Sync laufen lassen: `py .agent-meta/scripts/sync.py --config .meta-config/project.yaml`
- Eintrag in `.claude/settings.json` unter `hooks.PreToolUse` prüfen

**Hook blockiert fälschlicherweise:**
- Hook temporär deaktivieren: `"enabled": false` in Config + Sync
- Oder Skript direkt editieren: `.claude/hooks/dod-push-check.sh`

**TEST_COMMAND nicht gefunden:**
- `variables.TEST_COMMAND` in `.meta-config/project.yaml` setzen
- Oder `export AGENT_META_TEST_COMMAND='bun test'` in Shell-Profil
