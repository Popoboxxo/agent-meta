# Rules-Optimierung für Token-Effizienz

> Für Projekte mit vielen Rules die bei jedem Request Token-Overhead erzeugen.
> Die Optimierungsstrategie unterscheidet sich stark zwischen Providern.

---

## Problem: Zu viele alwaysApply Rules

Jede Rule in `.claude/rules/` wird standardmäßig in **jeden Agenten-Request** geladen. Bei Platform-heavy Projekten (Home Assistant, Sharkord) kann das schnell 3.000–8.000 Token pro Request kosten.

**Signale dass Rules zu viel Last erzeugen:**
- Platform Rules > 400 Wörter (`wc -w <datei>`)
- Rules enthalten Migration-Tabellen, Troubleshooting-Workflows oder Copy-Paste-Code-Templates
- Inhalte sind nur bei konkreter Implementierung relevant (nicht bei jedem Request)

---

## Lösungen — Provider-spezifisch

### Für Claude Code & Opencode: `channel: skill` + `lazy` Preset

Claude Code lädt `.claude/rules/*.md` **immer vollständig**, unabhängig von `alwaysApply: false`. Der einzige echte Lazy-Load-Kanal ist `.claude/skills/<name>/SKILL.md`:

> **Verifiziert:** Token-Messung agent-meta selbst: 9.421 Token (alle Rules geladen) → 3.448 Token (mit `channel: skill` Preset `lazy`) = **−63 % Token-Overhead**.

**Lösung:**

```yaml
# .meta-config/project.yaml
rules-preset: lazy
```

Das ist es. sync.py schreibt große situative Rules (sync-interface, architecture, conventions, etc.) zu `.claude/skills/<name>/SKILL.md` statt `.claude/rules/<name>.md`. Claude Code lädt nur `name` + `description` im System-Prompt, den Body erst on-demand via Read.

**Welche Rules betroffen:** Siehe `config/rules-presets.yaml` `lazy` Preset — aktuell ~13 Regeln umgestellt, Kern-Rules (branch-guard, commit-conventions, language, speech-mode, use-orchestrator, dod-criteria) bleiben immer on.

**Weitere Info:** → [rules.md — Abschnitt "Skill-Channel (`channel: skill`)"](rules.md#skill-channel-channel-skill)

---

### Für Continue: `alwaysApply: false` + `minimal`/`silent` Presets

Continue UNTERSTÜTZT `alwaysApply: false` nativ — Rules landen nicht im System-Prompt, werden nur bei Keyword-Match geladen.

In `.meta-config/project.yaml`:

```yaml
# Situative Rules on-demand (guter Kompromiss)
rules-preset: minimal

# oder für maximale Einsparung
rules-preset: silent
```

**Verfügbare Presets:**

| Preset | Verhalten | Token-Einsparung |
|--------|-----------|------------------|
| `default` | Alle Rules immer aktiv | 0 % |
| `minimal` | Situative Rules on-demand | ~30–40 % (Continue) |
| `silent` | Nur Kern-Rules immer aktiv, Rest optional | ~60–70 % (Continue) |
| `lazy` | **Claude Code optimiert** — `channel: skill` statt `alwaysApply` | ~60–70 % (Claude Code) |

**Beispiel — Projekt-Override für einzelne Continue-Rules:**

```yaml
# .meta-config/project.yaml
rules-preset: minimal

rules:
  homeassistant-package-structure:
    alwaysApply: false   # ~900 Wörter, nur bei Package-Arbeit relevant
  homeassistant-energy-abstraction:
    alwaysApply: false   # ~480 Wörter, nur bei Energy-Features relevant
```

Continue lädt diese Rules dann nur bei Keyword-Match.

---

### Für andere Provider (Gemini, Copilot, Mammouth): Fallback `_wf-*.md` Pattern

Falls ein Provider weder `channel: skill` noch `alwaysApply: false` effektiv nutzt, bleibt das manuelle Aufteilen großer Rules eine Option:

**Kern-Rule + ausgelagertes Workflow-Dokument:**

```
platform-rule.md                ← ~150 Wörter, alwaysApply: true
  → Nur Kern-Direktiven + Verweis auf Workflow
_wf-platform-migration.md       ← ~750 Wörter, alwaysApply: false
  → Migration-Workflow, Troubleshooting (Lazy-Load)
```

**Namens-Konvention:** `_wf-<platform>-<thema>.md` (Unterstrich-Prefix = Workflow-Datei)

Diese Datei ist mittlerweile weitgehend durch `channel: skill` ersetzt worden (Claude Code) oder unnötig (Continue mit `alwaysApply`). Nur für exotische Provider noch relevant.

---

## Wann NICHT optimieren

- Wenn eine Rule bei wirklich jedem Task relevant ist (z.B. `commit-conventions.md`, `language.md`) → `alwaysApply: true` behalten
- Wenn das Projekt wenige Rules hat (< 5) → Overhead vernachlässigbar
- Wenn Token-Budget keine Rolle spielt → Standard-Preset reicht

---

## Checkliste: Rules-Optimierung

### Claude Code / Opencode Projekte
- [ ] `rules-preset: lazy` in `.meta-config/project.yaml` gesetzt
- [ ] Sync ausgeführt: `py .agent-meta/scripts/sync.py`
- [ ] Verifiziert: `.claude/skills/` enthält jetzt große Rules (z.B. `sync-interface/`, `architecture/`)
- [ ] Getestet: Agenten erhalten bei typischen Requests noch die wichtigsten Rules

### Continue Projekte
- [ ] `wc -w .claude/rules/*.md` ausgeführt — Rules > 400W identifiziert
- [ ] `rules-preset: minimal` oder `silent` in `.meta-config/project.yaml` gesetzt
- [ ] Sync ausgeführt: `py .agent-meta/scripts/sync.py`
- [ ] Getestet: Continue lädt große Rules nur bei Bedarf

---

## Verwandte Dokumente

- [howto/features/rules.md](rules.md) — Rules-System Übersicht
- [config/rules-presets.yaml](../../config/rules-presets.yaml) — Preset-Definitionen
