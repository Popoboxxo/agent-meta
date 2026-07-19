# Rules-Preset Optimierung für platform-heavy Projekte

> Für Projekte mit vielen Platform Rules die bei jedem Request Token-Overhead erzeugen.

---

## Problem: Zu viele alwaysApply Rules

Jede Rule in `.claude/rules/` mit `alwaysApply: true` (Standard) wird in **jeden Agenten-Request** geladen — egal ob relevant. Bei Platform-heavy Projekten (Home Assistant, Sharkord) kann das schnell 3.000–8.000 Token pro Request kosten.

**Signale dass Rules zu viel Last erzeugen:**
- Platform Rules > 400 Wörter (`wc -w <datei>`)
- Rules enthalten Migration-Tabellen, Troubleshooting-Workflows oder Copy-Paste-Code-Templates
- Inhalte sind nur bei konkreter Implementierung relevant (nicht bei jedem Request)

---

## Lösung: rules-preset + gezielte alwaysApply: false

### Schritt 1 — Preset wählen

In `.meta-config/project.yaml`:

```yaml
# Empfehlung für platform-heavy Projekte
rules-preset: minimal
```

Verfügbare Presets:

| Preset | Verhalten | Wann |
|--------|-----------|------|
| `default` | Alle Rules immer aktiv | Kleine Projekte, wenige Rules |
| `minimal` | Situative Rules on-demand | Platform-heavy Projekte (empfohlen) |
| `silent` | Nur Kern-Rules immer aktiv | Rapid-Prototyping, Token-Budget kritisch |

### Schritt 2 — Große Platform Rules identifizieren

```bash
# Wort-Zahl aller Rules prüfen
wc -w .claude/rules/*.md | sort -n
```

Faustregeln:

| Wörter | Empfehlung |
|--------|------------|
| < 200 | `alwaysApply: true` — kein Problem |
| 200–400 | Prüfen ob Inhalt wirklich immer relevant |
| > 400 | `alwaysApply: false` empfohlen |
| > 800 | Lazy-Load Pattern erwägen (siehe unten) |

### Schritt 3 — Projekt-Override für einzelne Rules

```yaml
# .meta-config/project.yaml
rules-preset: minimal

rules:
  homeassistant-package-structure:
    alwaysApply: false   # ~900 Wörter, nur bei Package-Arbeit relevant
  homeassistant-energy-abstraction:
    alwaysApply: false   # ~480 Wörter, nur bei Energy-Features relevant
  homeassistant-entity-data:
    alwaysApply: false   # ~560 Wörter, situational
```

Nach sync: Diese Rules werden nur geladen wenn Claude Code sie für den aktuellen Request
als relevant erkennt (Keyword-Match im Kontext).

---

## Lazy-Load Pattern für sehr große Rules

Analog zum `_wf-*.md` Pattern bei Agenten: Kern-Rule + ausgelagertes Workflow-Dokument.

**Vorher:** Eine große Rule mit allem:
```
homeassistant-package-structure.md   ← 900 Wörter, alwaysApply: true
  → Core-Direktiven (100W) + Migration-Tabellen (400W) + Troubleshooting (400W)
```

**Nachher:** Schlanke Core-Rule + lazy-geladenes Workflow-Doc:
```
homeassistant-package-structure.md   ← ~150 Wörter, alwaysApply: true
  → Nur Kern-Direktiven + Verweis auf Workflow
_wf-ha-package-migration.md          ← ~750 Wörter, alwaysApply: false
  → Migration-Workflow, Troubleshooting (nur bei Bedarf geladen)
```

**Namens-Konvention:** `_wf-<platform>-<thema>.md` (Unterstrich-Prefix = Workflow-Datei)

**Verweis in der Core-Rule:**
```markdown
# HA Package Structure

[Kern-Direktiven hier — kurz, imperativ]

Für Migration-Workflow und Troubleshooting:
→ Lies `_wf-ha-package-migration.md` (Claude Code lädt bei Bedarf)
```

---

## Wann NICHT optimieren

- Wenn eine Rule bei wirklich jedem Task relevant ist (z.B. `commit-conventions.md`) → `alwaysApply: true` behalten
- Wenn das Projekt wenige Rules hat (< 5) → overhead vernachlässigbar
- Wenn Token-Budget keine Rolle spielt → Standard-Preset reicht

---

## Checkliste: Rules-Preset-Optimierung

- [ ] `wc -w .claude/rules/*.md` ausgeführt — Rules > 400W identifiziert
- [ ] `rules-preset: minimal` oder `silent` in project.yaml gesetzt
- [ ] Große Platform Rules auf `alwaysApply: false` gesetzt
- [ ] Sync ausgeführt: `py .agent-meta/scripts/sync.py`
- [ ] Getestet: Agenten erhalten bei typischen Requests noch die wichtigsten Rules

---

## Verwandte Dokumente

- [howto/features/rules.md](rules.md) — Rules-System Übersicht
- [config/rules-presets.yaml](../../config/rules-presets.yaml) — Preset-Definitionen
