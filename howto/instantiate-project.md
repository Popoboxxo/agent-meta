# Howto: Neues Projekt mit agent-meta einrichten

---

## Konzept

Agenten werden von `sync.py` **generiert** — nie manuell kopiert oder bearbeitet.
Den Projektkontext liefert die `CLAUDE.md` des Projekts.
Projektspezifische Erweiterungen leben in `.claude/3-project/`.

---

## Ersteinrichtung

> **Tipp:** Für eine geführte Einrichtung mit einem AI-Assistenten nutze
> [howto/first-steps.md](first-steps.md) — gib die Datei deinem AI-Tool
> und sage: "Hilf mir, agent-meta einzurichten."

### Schritt 1: agent-meta als Submodul einbinden

```bash
git submodule add https://github.com/Popoboxxo/agent-meta .agent-meta
```

```bash
cd .agent-meta && git checkout v0.16.1
```

```bash
cd ..
```

```bash
git submodule update --init --recursive
```

### Schritt 2: Config anlegen und befüllen

```bash
cp .agent-meta/howto/agent-meta.config.example.json agent-meta.config.json
```

Pflichtfelder:

```json
{
  "agent-meta-version": "0.16.1",
  "ai-provider": "Claude",
  "platforms": ["sharkord"],
  "roles": ["orchestrator", "developer", "tester", "validator",
            "requirements", "documenter", "git", "release", "docker",
            "ideation", "meta-feedback", "feature", "agent-meta-manager",
            "agent-meta-scout"],
  "project": {
    "name": "sharkord-mein-plugin",
    "prefix": "mpl",
    "short": "mein-plugin"
  },
  "variables": { ... }
}
```

Fehlende Variablen → Warning in `sync.log`, Platzhalter bleibt sichtbar.

### Schritt 3: CLAUDE.md + Agenten generieren

```bash
py .agent-meta/scripts/sync.py --config agent-meta.config.json
```

Das Script erzeugt beim ersten Aufruf (nur bei `ai-provider: Claude`):
- `CLAUDE.md` — aus Template, wenn noch nicht vorhanden
- `CLAUDE.personal.md` — persönliche Präferenzen-Template (gitignored, einmalig)
- `.claude/settings.json` — Team-Permissions Skeleton (einmalig)
- `.gitignore` — fehlende Einträge werden ergänzt (bei jedem Sync)
- `.claude/agents/*.md` — alle Agenten, generisch benannt
- `CLAUDE.md` managed block — wird bei jedem sync automatisch aktualisiert
- `sync.log` mit Zusammenfassung und Warnungen

> **managed block in CLAUDE.md:** Der Abschnitt zwischen `<!-- agent-meta:managed-begin -->` und
> `<!-- agent-meta:managed-end -->` enthält die Agenten-Tabelle und wird bei **jedem normalen sync**
> automatisch aktualisiert (nur bei `ai-provider: Claude`). Alles außerhalb ist handgeschrieben und wird nie überschrieben.

### Schritt 4: sync.log prüfen

```bash
cat sync.log
```

Alle `[WARN]` zeigen fehlende Variablen. In `agent-meta.config.json` ergänzen, dann erneut syncen:

```bash
py .agent-meta/scripts/sync.py --config agent-meta.config.json
```

### Schritt 5: Committen

```bash
git add CLAUDE.md .claude/settings.json .claude/agents/ .gitignore agent-meta.config.json .gitmodules .agent-meta
git commit -m "chore: initialize agent-meta agents"
```

> `CLAUDE.personal.md` und `.claude/settings.local.json` sind gitignored — nie committen.
> Jeder Entwickler im Team erhält `CLAUDE.personal.md` beim ersten `sync` automatisch.

---

## Generierte Agent-Dateien

Alle Agenten heißen **generisch** — kein Projekt-Prefix:

| Agent-Datei | Quelle (Beispiel Sharkord) |
|-------------|---------------------------|
| `.claude/agents/orchestrator.md` | `1-generic/orchestrator.md` |
| `.claude/agents/developer.md` | `1-generic/developer.md` |
| `.claude/agents/tester.md` | `1-generic/tester.md` |
| `.claude/agents/validator.md` | `1-generic/validator.md` |
| `.claude/agents/requirements.md` | `1-generic/requirements.md` |
| `.claude/agents/documenter.md` | `1-generic/documenter.md` |
| `.claude/agents/release.md` | `2-platform/sharkord-release.md` |
| `.claude/agents/docker.md` | `2-platform/sharkord-docker.md` |
| `.claude/agents/feature.md` | `1-generic/feature.md` |
| `.claude/agents/agent-meta-manager.md` | `1-generic/agent-meta-manager.md` |
| `.claude/agents/agent-meta-scout.md` | `1-generic/agent-meta-scout.md` |

---

## Projektspezifische Anpassungen

### Einfache Werte → config.json

Kurze Texte, Kommandos, Listen: in `agent-meta.config.json` unter `variables` eintragen.
Sie werden per `{{PLATZHALTER}}` in den generierten Agenten injiziert.

Verfügbare Platzhalter:

| Platzhalter | Agent | Zweck |
|-------------|-------|-------|
| `{{PROJECT_CONTEXT}}` | alle | Projektbeschreibung |
| `{{CODE_CONVENTIONS}}` | developer | Sprachregeln |
| `{{ARCHITECTURE}}` | developer | Verzeichnisstruktur |
| `{{DEV_COMMANDS}}` | developer, orchestrator | Build/Run |
| `{{EXTRA_DONTS}}` | developer | Zusätzliche Verbote |
| `{{CODE_QUALITY_RULES}}` | validator | Linting-Regeln |
| `{{REQ_CATEGORIES}}` | requirements | Anforderungs-Kategorien |
| `{{TEST_COMMANDS}}` | tester | Test-Runner |
| `{{BUILD_COMMANDS}}` | release | Build-Schritte |

### Strukturiertes Projektwissen → Extension

Für SDK-spezifische Patterns, manuelle Workflows, domänenspezifische Regeln:

```bash
# Einzelne Extension anlegen:
py .agent-meta/scripts/sync.py --config agent-meta.config.json --create-ext developer

# Alle Extensions auf einmal anlegen:
py .agent-meta/scripts/sync.py --config agent-meta.config.json --create-ext all
```

Die Extension-Datei wird in `.claude/3-project/<prefix>-<rolle>-ext.md` erstellt mit:
- **managed block** — auto-generierter Kontext aus config-Variablen (aktualisierbar)
- **Projektbereich** — handgeschrieben, von sync.py nie angefasst

Managed block aktualisieren (z.B. nach config-Änderung):
```bash
py .agent-meta/scripts/sync.py --config agent-meta.config.json --update-ext
```

Format — einfaches Markdown, kein Frontmatter nötig:

```markdown
# Developer Extension — Sharkord Plugin SDK

## Plugin-SDK Patterns

- Alle Commands über `ctx.registerCommand()` registrieren
- Mediasoup-Zugriff nur über ctx.mediasoup, nie direkt
- ...

## Projektspezifische Don'ts

- KEIN direkter Zugriff auf window/document (kein Browser-API)
- ...
```

Der generierte Agent liest diese Datei **beim Start automatisch** (Extension-Hook).

### Kompletter Override → `.claude/3-project/<rolle>.md`

Wenn Extension nicht reicht (anderer Workflow, andere Struktur):
Datei direkt im Projekt anlegen — wird von sync.py nie berührt.

Auch Overrides unterstützen das **Composition-System** (`extends: + patches:`) —
statt einer Vollkopie können gezielt einzelne Sections ersetzt oder ergänzt werden:

```yaml
# .claude/3-project/myproject-developer.md
---
name: myproject-developer
extends: "1-generic/developer.md"
patches:
  - op: append-after
    anchor: "## Don'ts"
    content: |
      ### Projektspezifische Don'ts
      - Kein direkter DB-Zugriff außerhalb von `src/db/`
---
```

> **Vollständige Anleitung:** [howto/agent-composition.md](agent-composition.md) —
> alle Patch-Operationen (`append-after`, `replace`, `delete`, `append`), Anchor-Syntax, Beispiele.

### Externe Skills aktivieren

External Skills sind spezialisierte Agenten aus Drittrepos (z.B. 3D-Druck, CAD).

Skills werden **pro Projekt** aktiviert — in `agent-meta.config.json`:

```json
"external-skills": {
  "home-organization": { "enabled": true },
  "opengrid-openscad": { "enabled": true }
}
```

Welche Skills verfügbar (`approved: true`) sind: `cat .agent-meta/external-skills.config.json`

> **Vollständige Anleitung:** [howto/external-skills.md](external-skills.md) —
> Lifecycle, Troubleshooting, Meta-Maintainer-Workflow, Versionierung.

---

## Checkliste: Projekt vollständig eingerichtet?

- [ ] `.agent-meta/` Submodul auf gewünschter Version (`v0.16.1` oder neuer)
- [ ] `agent-meta.config.json` vollständig befüllt (inkl. `ai-provider: Claude`)
- [ ] `sync.log` ohne Warnungen
- [ ] `CLAUDE.md` vorhanden mit managed block
- [ ] `CLAUDE.md` ohne offene `{{...}}` Platzhalter
- [ ] `CLAUDE.personal.md` vorhanden (gitignored, persönlich befüllen)
- [ ] `.claude/settings.json` vorhanden und committed
- [ ] `.gitignore` enthält `CLAUDE.personal.md`, `.claude/settings.local.json`, `sync.log`
- [ ] `.claude/agents/orchestrator.md` vorhanden
- [ ] `.claude/agents/developer.md` vorhanden
- [ ] `.claude/agents/tester.md` vorhanden
- [ ] `.claude/agents/validator.md` vorhanden
- [ ] `.claude/agents/requirements.md` vorhanden
- [ ] `.claude/agents/documenter.md` vorhanden
- [ ] `.claude/agents/release.md` vorhanden
- [ ] `.claude/agents/docker.md` vorhanden
- [ ] `.claude/agents/feature.md` vorhanden
- [ ] `.claude/agents/agent-meta-manager.md` vorhanden
- [ ] `.claude/agents/agent-meta-scout.md` vorhanden
- [ ] `docs/REQUIREMENTS.md` initialisiert
