# Gemini CLI — Provider-Dokumentation

> Stand: agent-meta v0.27.x | Quelle: [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli)

> **Veraltet (teilweise):** Modellstand, `.gemini/hooks` und Kontextdatei-Angaben sind laut Studie
> `docs/analysis/2026-10-11-context-budget-provider-study.md` §3.7 nicht mehr belegt. Korrigiert
> sind nur Sub-Agenten, Rules und `context.fileName`; der Rest ist **UNVERIFIED**.

---

## Was ist Gemini CLI?

Terminal-basierter AI-Coding-Agent von Google (TypeScript, Open-Source Apache 2.0).
Vergleichbar mit Claude Code: interaktiver Chat im Terminal, liest lokale Dateien,
führt Shell-Kommandos aus, hat eingebaute Tools (Suche, Webfetch, Datei-Ops).

Kostenlos nutzbar: 60 Requests/min, 1.000/Tag mit Google-Account.

Default-Modell laut Konfiguration: **Gemini 2.5 Pro** (1M Token Context) — Modellstand **UNVERIFIED/veraltet** (Studie §3.7 nennt das Dokument veraltet).
Weitere Modell-IDs: `gemini-2.5-pro`, `gemini-2.0-flash`.

---

## Verzeichnis- und Dateistruktur

```
GEMINI.md                  ← Projekt-Kontext (analog zu CLAUDE.md)
.gemini/
  settings.json            ← Projekt-Konfiguration (Hooks, Model-Override)
  agents/                  ← Sub-Agenten (von agent-meta generiert)
    developer.md
    orchestrator.md
    ...
  commands/                ← Slash-Commands als .toml-Dateien
    doc-now.toml           → /doc-now
  hooks/                   ← Hook-Skripte (referenziert in settings.json)

~/.gemini/
  settings.json            ← User-Level-Konfiguration
  GEMINI.md                ← Globaler Kontext (alle Projekte)
```

**Hierarchisches GEMINI.md-Laden:**
Global (`~/.gemini/GEMINI.md`) → Workspace → JIT (beim Datei-Zugriff automatisch).
Unterstützt `@./path/file.md` für Modularisierung.

---

## Feature-Vergleich mit Claude Code

| Feature | Claude Code | Gemini CLI |
|---------|------------|-----------|
| Kontext-Datei | `CLAUDE.md` | `GEMINI.md` |
| Config-Verzeichnis | `.claude/` | `.gemini/` |
| Sub-Agenten | `.claude/agents/*.md` | `.gemini/agents/*.md` |
| Rules (auto-load) | `.claude/rules/` | `.gemini/rules/` |
| Slash-Commands | `.claude/commands/*.md` | `.gemini/commands/*.toml` |
| Hooks | `.claude/hooks/*.sh` + `settings.json` | `.gemini/hooks/*.sh` + `settings.json` |
| Frontmatter: model | `model:` | `model:` |
| Frontmatter: memory | `memory:` | **Nicht unterstützt** |
| Frontmatter: permissionMode | `permissionMode:` | **Nicht unterstützt** |

---

## Sub-Agenten in Gemini CLI

`.gemini/agents/*.md` sind native Subagenten der Gemini CLI. Der Loader validiert das
Frontmatter mit einem `.strict()`-Schema (erlaubt: `kind`, `name`, `description`,
`display_name`, `tools`, `mcp_servers`, `model`, `temperature`, `max_turns`,
`timeout_mins`; Tools werden validiert). Quelle: Studie
`docs/analysis/2026-10-11-context-budget-provider-study.md` §3.7 (SOURCE-DERIVED,
nicht ausgeführt).

**Offener Defekt:** unsere generierten Agenten enthalten Zusatz-Keys (`version`, `hint`,
`prompt_mode`, `generated-from`) und Claude-/Antigravity-Toolnamen — nach dem
`.strict()`-Schema würden sie abgelehnt. Das Beispiel unten zeigt den aktuell
generierten (reduzierten) Stand, nicht ein verifiziert ladbares Format:

```yaml
---
name: developer
description: "Feature-Implementierung und Bugfixes..."
model: gemini-2.5-pro   # optional
generated-from: 1-generic/developer.md@2.1.0
---
# developer
...
```

Entfernt im Vergleich zu Claude: `memory`, `permissionMode`.

---

## Rules

`.gemini/rules/` wird von **keinem** Harness gelesen (weder Gemini CLI noch Antigravity;
siehe `docs/spikes/2026-09-14-f-rulesloc-gemini-rules-channel.md` und Studie §3.7).
agent-meta generiert dennoch:

- Rule-Dateien in `.gemini/rules/` (inert, 17,880 B)
- `has_rules: true` in `config/ai-providers.yaml`

**Kontextdatei:** Gemini CLI lädt standardmäßig `GEMINI.md`. Ohne `context.fileName` in
`.gemini/settings.json` wird `AGENTS.md` ignoriert — unsere generierte `settings.json`
setzt den Key aktuell nicht, die CLI erhält daher keinen Projektkontext (Studie §3.7).

**Workaround:** Wichtige Regeln als eigene `@./`-Referenzen in GEMINI.md einbinden:

```markdown
@./.gemini/conventions.md
```

---

## Slash-Commands (.toml-Format)

Gemini Commands sind TOML-Dateien statt Markdown:

```toml
description = "Update CODEBASE_OVERVIEW.md immediately"
prompt = """
Delegate to the `documenter` agent with this task:

Update `CODEBASE_OVERVIEW.md` immediately. {{args}}
"""
```

**agent-meta transformiert automatisch** die `.md`-Quelldateien aus `commands/1-generic/`
in `.toml`-Dateien beim Sync:

- `$ARGUMENTS` → `{{args}}` (Gemini-Syntax)
- `description:`-Frontmatter → `description = "..."` in TOML
- Body → `prompt = """..."""`

---

## Hooks

Gemini CLI unterstützt 10 Lifecycle-Events:

| Event | Bedeutung |
|-------|-----------|
| `SessionStart` / `SessionEnd` | Sitzungs-Lebenszyklus |
| `BeforeAgent` / `AfterAgent` | Um Agent-Calls |
| `BeforeModel` / `AfterModel` | Um Model-Calls |
| `BeforeToolSelection` | Vor Tool-Auswahl |
| `BeforeTool` / `AfterTool` | Um einzelne Tool-Calls |
| `PreCompress` | Vor Kontext-Komprimierung |

Hook-Konfiguration in `.gemini/settings.json`:

```json
{
  "hooks": {
    "BeforeTool": [
      {
        "hooks": [{"type": "command", "command": "bash .gemini/hooks/my-hook.sh"}]
      }
    ]
  }
}
```

Kommunikation via JSON stdin/stdout (analog zu Claude Code Hooks).
Projekt-Hooks werden fingerprinted — Gemini warnt bei Änderung (Security-Feature).

agent-meta kopiert Hook-Skripte nach `.gemini/hooks/` und registriert aktivierte
Hooks in `.gemini/settings.json` (analog zu Claude Code).

---

## agent-meta Konfiguration

### Gemini aktivieren

```yaml
# .meta-config/project.yaml
ai-providers:
  - Gemini
```

Oder zusammen mit anderen Providern:

```yaml
ai-providers:
  - Claude
  - Gemini
  - Continue
```

### Modell überschreiben

```yaml
model-overrides:
  developer: gemini-2.5-pro
  git: gemini-2.0-flash
```

### Was wird generiert?

| Artefakt | Verhalten |
|----------|-----------|
| `.gemini/agents/*.md` | ✅ Überschrieben bei jedem sync, stale gelöscht |
| `GEMINI.md` (managed block) | ✅ Aktualisiert bei jedem sync |
| `GEMINI.md` (Rest) | ❌ Einmalig angelegt, dann manuell |
| `.gemini/settings.json` | ❌ Einmalig angelegt (Skeleton) |
| `.gemini/commands/*.toml` | ✅ Aus `commands/` transformiert, stale gelöscht |
| `.gemini/hooks/*.sh` | ✅ Kopiert, stale gelöscht |
| Rules | ⚠️ Generiert in `.gemini/rules/`, stale gelöscht — von keinem Harness gelesen |

---

## Bekannte Einschränkungen

1. **Rules inert** — `.gemini/rules/` wird von sync.py befüllt, aber von keinem Harness gelesen
2. **Kein persistentes Agenten-Gedächtnis** — `memory:`-Feld wird entfernt
3. **Kein permissionMode** — Berechtigungen über Google-Account gesteuert
4. **Sub-Agenten strikt validiert** — `.gemini/agents/` ist nativ, das Schema ist `.strict()`; unsere Zusatz-Keys/Toolnamen sind ein offener Defekt (Studie §3.7)
5. **TOML-Commands** — andere Syntax als Claude/Continue; `$ARGUMENTS` heißt `{{args}}`
