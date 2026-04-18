# Gemini CLI — Provider-Dokumentation

> Stand: agent-meta v0.27.x | Quelle: [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli)

---

## Was ist Gemini CLI?

Terminal-basierter AI-Coding-Agent von Google (TypeScript, Open-Source Apache 2.0).
Vergleichbar mit Claude Code: interaktiver Chat im Terminal, liest lokale Dateien,
führt Shell-Kommandos aus, hat eingebaute Tools (Suche, Webfetch, Datei-Ops).

Kostenlos nutzbar: 60 Requests/min, 1.000/Tag mit Google-Account.

Default-Modell: **Gemini 2.5 Pro** (1M Token Context).
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
| Rules (auto-load) | `.claude/rules/` | **Nicht vorhanden** (alles in GEMINI.md) |
| Slash-Commands | `.claude/commands/*.md` | `.gemini/commands/*.toml` |
| Hooks | `.claude/hooks/*.sh` + `settings.json` | `.gemini/hooks/*.sh` + `settings.json` |
| Frontmatter: model | `model:` | `model:` |
| Frontmatter: memory | `memory:` | **Nicht unterstützt** |
| Frontmatter: permissionMode | `permissionMode:` | **Nicht unterstützt** |

---

## Sub-Agenten in Gemini CLI

Gemini CLI hat kein natives Sub-Agenten-System wie Claude Codes `.claude/agents/`.
Die Community diskutiert dies (Issue #1471), aber es ist kein offizielles Feature.

**agent-meta generiert trotzdem `.gemini/agents/*.md`** — der Markdown-Body ist
identisch mit Claude, aber das Frontmatter ist reduziert:

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

Gemini CLI hat **kein `.gemini/rules/`-Verzeichnis**. Regeln werden direkt in
`GEMINI.md` eingebettet. agent-meta generiert deshalb:

- Keine separaten Rule-Dateien für Gemini
- `has_rules: false` in `config/ai-providers.yaml`

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
| Rules | ❌ Nicht vorhanden (kein `.gemini/rules/`) |

---

## Bekannte Einschränkungen

1. **Kein Rules-System** — Regeln nur über GEMINI.md einbindbar
2. **Kein persistentes Agenten-Gedächtnis** — `memory:`-Feld wird entfernt
3. **Kein permissionMode** — Berechtigungen über Google-Account gesteuert
4. **Sub-Agenten inoffiziell** — Gemini kennt `.gemini/agents/` nicht nativ; die Dateien sind für zukünftige Kompatibilität vorbereitet
5. **TOML-Commands** — andere Syntax als Claude/Continue; `$ARGUMENTS` heißt `{{args}}`
