# Rules — Projekt-globale Regeln für alle Agenten

> Dieses Dokument beschreibt das Rules-System in agent-meta: wie Rules strukturiert,
> versioniert und per `sync.py` in Projekte synchronisiert werden.

---

## Was sind Rules?

Claude Code lädt Dateien aus `.claude/rules/` automatisch in den Kontext **jedes Agenten** —
ohne explizites Read-Tool. Ideal für Regeln die projekt-global gelten:

- Security-Policies
- Coding-Konventionen die alle Agenten kennen sollen
- Naming-Regeln, Commit-Format, Review-Checklisten
- Plattformspezifische Constraints (z.B. Sharkord-Plugin-Grenzen)

**Abgrenzung zu Extensions** (`.claude/3-project/*-ext.md`):

| | Extensions | Rules |
|---|---|---|
| Scope | Ein Agenten-Typ | **Alle Agenten** |
| Laden | Explizit per Read-Hook | **Automatisch** |
| Quelle | Projekt schreibt selbst | Alle 4 Schichten |
| Für | Detailwissen eines Agenten | Globale Policies |

---

## Vier-Schichten-Modell

```
rules/
  0-external/       ← aus externen Skill-Repos (via Git Submodule)
  1-generic/        ← universell, von agent-meta bereitgestellt
  2-platform/       ← plattformspezifisch (überschreibt 1-generic bei gleichem Namen)
  ← 3-project ist das Zielprojekt selbst: .claude/rules/ (nie von sync.py berührt)
```

**Override-Priorität (höchste zuerst für gleichnamige Dateien):**

```
2-platform  >  1-generic  >  0-external
```

Ein `sharkord-security.md` in `2-platform/` ersetzt `security.md` aus `1-generic/` im Output.

---

## Sync-Verhalten

`sync.py` kopiert Rules automatisch bei jedem normalen Sync:

| Schicht | Quelle | Output in `.claude/rules/` | Verhalten |
|---------|--------|---------------------------|-----------|
| `1-generic` | `rules/1-generic/<name>.md` | `<name>.md` | ✅ immer überschrieben |
| `2-platform` | `rules/2-platform/<platform>-<name>.md` | `<name>.md` | ✅ überschreibt generic |
| `0-external` | `rules/0-external/<name>.md` | `<name>.md` | ✅ kopiert (geringste Priorität) |
| Projekt | `.claude/rules/<name>.md` | — | ❌ **nie angefasst** |

**Stale-Cleanup:** sync.py führt Index-Dateien zur Verfolgung von generierten Rules:

- `.claude/rules/.agent-meta-managed` — für reguläre Rules aus `rules/1-generic/` und `rules/2-platform/`
- `.claude/rules/.agent-meta-managed-mcp` — für MCP-Server-Rules (automatisch aus `config/mcp-registry.yaml` generiert)
- `.claude/rules/.agent-meta-managed-tools` — für External-Tool-Rules (automatisch aus `config/external-tools-registry.yaml` generiert)

Rules die in einer dieser Indizes gelistet sind, aber nicht mehr in den agent-meta-Quellen existieren (z.B. weil ein MCP-Server deaktiviert oder ein Tool entfernt wurde), werden beim nächsten Sync **automatisch gelöscht**. Projekt-eigene Rules (nicht in den Indizes) werden niemals gelöscht.

Die getrennten Index-Dateien verhindern, dass unterschiedliche Schreiber (rules.py, mcp.py, external_tools.py) sich gegenseitig überschreiben.

---

## Naming-Konvention

### `1-generic/` und `0-external/`

```
<thema>.md          z.B. commit-conventions.md, security-baseline.md
```

### `2-platform/`

```
<platform>-<thema>.md    z.B. sharkord-plugin-constraints.md
```

sync.py strippt den Platform-Prefix beim Kopieren:
`sharkord-plugin-constraints.md` → `.claude/rules/plugin-constraints.md`

---

## Skill-Channel (`channel: skill`)

Große Rules können statt als `.claude/rules/<name>.md` zu `.claude/skills/<name>/SKILL.md` geschrieben werden — nur für Projekte mit Claude Code oder Opencode als Target-Provider (siehe `config/rules-presets.yaml` und `scripts/lib/skill_channel.py`).

**Effekt:** Claude Code lädt nur `name` + `description` im System-Prompt, den Rule-Body erst on-demand via Read-Tool. Das spart Token bei der Lazy-Load-Strategie.

**Verwendung:**

In `config/rules-presets.yaml` oder Projekt-Overrides:

```yaml
lazy:
  sync-interface:
    channel: skill
    skill-description: "Use when running sync.py..."
  architecture:
    channel: skill
    skill-description: "Use when adding agent templates..."
```

**Hintergrund:** `alwaysApply: false` hat auf Claude Code keine Wirkung (Claude Code lädt `.claude/rules/*.md` immer vollständig). `channel: skill` ist der einzige echte Lazy-Load-Kanal auf Claude Code.

**Weitere Info:** → [rules-preset-optimization.md — "Für Claude Code & Opencode"](rules-preset-optimization.md#für-claude-code--opencode-channel-skill--lazy-preset)

---

## Projekt-eigene Rules erstellen

### Manuell

Einfach eine Datei in `.claude/rules/` anlegen — sync.py fasst sie nie an.

### Via sync.py Template

```bash
py .agent-meta/scripts/sync.py --config .meta-config/project.yaml --create-rule security-policy
```

Erstellt `.claude/rules/security-policy.md` mit leerem Template.
Existiert die Datei bereits: kein Überschreiben, nur ein `[SKIP]` im Log.

---

## Rules zu agent-meta beitragen

### Neue Generic Rule (für alle Projekte)

1. `rules/1-generic/<name>.md` anlegen
2. Projekte neu syncen — Rule erscheint automatisch in `.claude/rules/`

### Neue Platform Rule (nur für eine Plattform)

1. `rules/2-platform/<platform>-<name>.md` anlegen
2. Projekte mit dieser Platform neu syncen

### Neues Format für Rule-Dateien

Rules sind plain Markdown — **kein YAML-Frontmatter** nötig.
Claude Code lädt sie as-is in den Kontext.

Empfehlung: Klare `# Überschrift` + kurze Einleitung damit Agenten den Scope sofort erkennen.

```markdown
# Commit-Konventionen

Alle Commits folgen diesem Format: `<type>(REQ-xxx): <beschreibung>`
...
```

---

## Beispiel: security-baseline.md

```markdown
# Security Baseline

## Pflicht-Checks vor jedem Commit

- Keine Secrets, API-Keys oder Passwörter in Code oder Konfigurationsdateien
- Keine `console.log` mit sensitiven Daten
- Keine `eval()` oder `new Function()` mit externen Inputs
- SQL-Queries immer parametrisiert — kein String-Concat

## OWASP Top 10 — immer im Blick

A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection ...
```

---

## Verwandte Dokumente

- [howto/features/agent-composition.md](agent-composition.md) — extends/patches System für Agenten
- [howto/features/external-skills.md](external-skills.md) — External Skills einbinden
- [CLAUDE.md](../CLAUDE.md) — Vollständige Konfigurations-Referenz
