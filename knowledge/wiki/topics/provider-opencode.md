---
type: "Guide"
title: "opencode — Provider-Dokumentation"
description: "Terminal-basierter AI-Coding-Agent von SST (Open Source, MIT). Vergleichbar mit Claude Code: interaktiver Chat im Terminal, Datei-Operationen, Shell-Integration, 75+..."
tags: [guide, provider]
timestamp: "2026-07-27"
resource: "../../sources/docs/providers/opencode.md"
migrated_from: "docs/providers/opencode.md"
---
# opencode — Provider-Dokumentation

> Stand: agent-meta v0.33.x | Quelle: [sst/opencode](https://github.com/sst/opencode)

---

## Was ist opencode?

Terminal-basierter AI-Coding-Agent von SST (Open Source, MIT).
Vergleichbar mit Claude Code: interaktiver Chat im Terminal, Datei-Operationen, Shell-Integration,
75+ AI-Provider via AI SDK.

Kontext-Datei: **`AGENTS.md`** (analog zu `CLAUDE.md`). Wird via `/init` generiert und ins Git committed.
Unterstützt Legacy: opencode liest auch `CLAUDE.md` direkt — bestehende Projekte bekommen
den Kontext automatisch, ohne explizite opencode-Konfiguration.

---

## Verzeichnis- und Dateistruktur

```
AGENTS.md                  ← Projekt-Kontext + eingebettete Regeln (analog zu CLAUDE.md)
opencode.json              ← Projekt-Konfiguration (JSONC)
.opencode/
  agents/                  ← Sub-Agenten (von agent-meta generiert)
    developer.md
    orchestrator.md
    ...
  commands/                ← Slash-Commands als .md-Dateien (von agent-meta generiert)
    doc-now.md             → /doc-now

~/.config/opencode/
  opencode.json            ← User-Level-Konfiguration
  AGENTS.md                ← Globaler Kontext (alle Projekte)
  agents/                  ← User-eigene Agenten
  commands/                ← User-eigene Commands
```

---

## Feature-Vergleich mit Claude Code

| Feature | Claude Code | opencode |
|---------|------------|---------|
| Kontext-Datei | `CLAUDE.md` | `AGENTS.md` (liest auch `CLAUDE.md`) |
| Config-Verzeichnis | `.claude/` | `.opencode/` |
| Sub-Agenten | `.claude/agents/*.md` | `.opencode/agents/*.md` |
| Rules (auto-load) | `.claude/rules/` | **Nicht vorhanden** — in `AGENTS.md` eingebettet |
| Slash-Commands | `.claude/commands/*.md` | `.opencode/commands/*.md` (gleiches Format) |
| Hooks | `.claude/hooks/*.sh` + `settings.json` | **Nicht vorhanden** (noch Feature-Request) |
| Frontmatter: `description` | `description:` | `description:` |
| Frontmatter: `mode` | — | `mode: primary \| subagent \| all` |
| Frontmatter: `model` | `model: claude-sonnet-4-6` | `model: anthropic/claude-sonnet-4-6` |
| Frontmatter: `memory` | `memory:` | **Nicht unterstützt** |
| Frontmatter: `permissionMode` | `permissionMode:` | **Nicht unterstützt** |

---

## Sub-Agenten in opencode

Markdown-Dateien in `.opencode/agents/` — Dateiname = Agent-ID.

**agent-meta schreibt natives opencode-Frontmatter:**

```yaml
---
description: "Feature-Implementierung und Bugfixes..."
mode: subagent
model: anthropic/claude-sonnet-4-6
generated-from: "1-generic/developer.md@2.1.0"
---
# developer
...
```

`mode: subagent` ist Standard für alle agent-meta Agenten — sie werden explizit delegiert,
nicht als Haupt-Agent gestartet.

---

## Rules

opencode hat **kein `.opencode/rules/`-Verzeichnis**. Regeln werden direkt in `AGENTS.md`
eingebettet. agent-meta generiert deshalb:

- Keine separaten Rule-Dateien für opencode
- `has_rules: false` in `config/ai-providers.yaml`
- Alle aktiven Rules werden im managed block von `AGENTS.md` eingebettet
- Speech-Mode-Rule wird ebenfalls eingebettet (wenn konfiguriert)

**Rule überspringen:** `opencode: skip` in `config/rules-presets.yaml` oder project.yaml:

```yaml
rules:
  lifecycle-tasks:
    opencode: skip
```

---

## Slash-Commands

opencode Commands sind `.md`-Dateien — **gleiches Format wie Claude Code**:
- Gleiches `$ARGUMENTS` für Argumente
- Gleiche `description:` + Body-Struktur
- Kein Transformationsschritt nötig

opencode scannt `.opencode/commands/` automatisch — kein Eintrag in `opencode.json` nötig.

Optionale Frontmatter-Felder für opencode Commands:

```yaml
---
description: Update CODEBASE_OVERVIEW.md immediately
agent: documenter    # opencode wählt diesen Agenten automatisch
model: anthropic/claude-sonnet-4-6
subtask: true        # erzwingt Subagent-Ausführung
---
```

---

## Model-Tiers

opencode Model-IDs folgen dem AI-SDK-Format: `provider/model-id`.

| Tier | Modell-ID |
|------|-----------|
| `nano` | `anthropic/claude-haiku-4-5-20251001` |
| `fast` | `anthropic/claude-haiku-4-5-20251001` |
| `balanced` | `anthropic/claude-sonnet-4-6` |
| `powerful` | `anthropic/claude-opus-4-7` |
| `max` | `anthropic/claude-opus-4-7` |

opencode unterstützt 75+ Provider — Tier-Mapping auf andere Provider via `model-overrides`
in `project.yaml`:

```yaml
model-overrides:
  Opencode:
    developer: openai/gpt-4o
    git: google/gemini-2.5-flash
```

---

## agent-meta Konfiguration

### Opencode aktivieren

```yaml
# .meta-config/project.yaml
ai-providers:
  - Opencode
```

Oder zusammen mit anderen Providern:

```yaml
ai-providers:
  - Claude
  - Opencode
```

### Was wird generiert?

| Artefakt | Verhalten |
|----------|-----------|
| `.opencode/agents/*.md` | Überschrieben bei jedem sync, stale gelöscht |
| `AGENTS.md` (managed block) | Aktualisiert bei jedem sync (agent hints + eingebettete rules) |
| `AGENTS.md` (Rest) | Einmalig angelegt, dann manuell gepflegt |
| `opencode.json` | Einmalig als Skeleton angelegt, danach manuell |
| `.opencode/commands/*.md` | Aus `commands/` kopiert, stale gelöscht |
| Rules | In `AGENTS.md` eingebettet (kein eigenes Verzeichnis) |
| Hooks | Nicht vorhanden (kein natives Hook-System) |

---

## Bekannte Einschränkungen

1. **Kein Rules-System** — Regeln nur über `AGENTS.md` einbindbar; agent-meta bettet sie ein
2. **Kein persistentes Agenten-Gedächtnis** — `memory:`-Feld wird entfernt
3. **Kein permissionMode** — Berechtigungen nicht in Frontmatter steuerbar
4. **Kein Hook-System** — opencode hat noch keinen nativen Lifecycle-Hook-Mechanismus
5. **Legacy-Kompatibilität:** opencode liest auch `CLAUDE.md` — bestehende Claude-Projekte
   funktionieren ohne dedizierte opencode-Konfiguration