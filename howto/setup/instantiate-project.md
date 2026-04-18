# Howto: Neues Projekt mit agent-meta einrichten

---

## Konzept

Agenten werden von `sync.py` **generiert** — nie manuell kopiert oder bearbeitet.
Den Projektkontext liefert die `CLAUDE.md` des Projekts.
Projektspezifische Erweiterungen leben in `.claude/3-project/`.

### CLAUDE.md Hierarchie

Claude Code lädt Kontext-Dateien in dieser Reihenfolge (alle werden zusammengeführt):

```
~/.claude/CLAUDE.md          ← global, alle Projekte (~50 Zeilen max)
<projekt>/CLAUDE.md          ← projektspezifisch — von agent-meta verwaltet
<ordner>/CLAUDE.md           ← optional in Unterordnern (z.B. src/backend/CLAUDE.md)
```

| Ebene | Inhalt | Wer pflegt es |
|-------|--------|---------------|
| Global (`~/.claude/CLAUDE.md`) | Persönliche Präferenzen, eigene Verbote, persönliche Kommunikationsstil | Du — manuell, einmalig |
| Projekt (`CLAUDE.md`) | Tech-Stack, Commands, Architektur, DoD, Agenten-Hints | agent-meta (managed block) + Du (manuell) |
| Ordner (`<ordner>/CLAUDE.md`) | Subsystem-spezifische Regeln (z.B. nur für `src/backend/`) | Du — manuell, bei Bedarf |

**Empfehlung für die globale CLAUDE.md:** Persönliche Präferenzen die für *alle* Projekte gelten —
kein projektspezifisches Wissen. Maximal ~50 Zeilen.

**Ordner-level CLAUDE.md:** Sinnvoll wenn ein Unterordner eigene Konventionen hat die im
Hauptkontext zu viel Platz wäre. Wird von agent-meta nicht berührt.

### .claude/rules/ — modulare Regeln

```
.claude/rules/
  branch-guard.md       ← von agent-meta generiert (sync.py)
  commit-conventions.md ← von agent-meta generiert
  language.md           ← von agent-meta generiert (mit substituierten Variablen)
  dod-criteria.md       ← von agent-meta generiert
  meine-regel.md        ← projekt-eigen (nie von sync.py berührt)
```

Regeln in `.claude/rules/` werden von Claude Code **automatisch** in jeden Agenten-Kontext
und den Hauptchat geladen — kein `Read`-Tool nötig. agent-meta-verwaltete Rules werden bei
jedem Sync aktualisiert; projekt-eigene Rules werden nie überschrieben.

Projekt-eigene Rule anlegen:
```bash
py .agent-meta/scripts/sync.py --create-rule meine-regel
```

### .claude/commands/ — Custom Slash Commands

```
.claude/commands/
  deploy.md      → /project:deploy
  review.md      → /project:review
```

Slash Commands laufen im **Haupt-Kontext** (kein isoliertes Context Window wie Agenten).
Geeignet für schnelle, wiederkehrende Einzel-Aktionen. agent-meta verwaltet commands/ nicht —
du legst diese Dateien manuell an.

| `.claude/agents/` | `.claude/commands/` |
|-------------------|---------------------|
| Vollständige Persona, isolierter Kontext | Schneller Einzel-Workflow im Hauptchat |
| Für komplexe, mehrstufige Aufgaben | Für wiederkehrende Einzel-Aktionen |
| Von agent-meta generiert und verwaltet | Manuell angelegt, nie von sync.py berührt |

---

## Ersteinrichtung

> **Tipp — Setup-Wizard:** Statt manueller Config-Erstellung:
> ```bash
> py .agent-meta/scripts/sync.py --setup
> ```
> Der Wizard führt Schritt für Schritt durch alle Pflichtfelder,
> generiert `.meta-config/project.yaml` und startet danach automatisch `--init`.
>
> Alternativ: [howto/setup/first-steps.md](first-steps.md) für AI-assistierte Einrichtung.

### Schritt 1: agent-meta als Submodul einbinden

```bash
git submodule add https://github.com/Popoboxxo/agent-meta .agent-meta
```

```bash
cd .agent-meta && git checkout v0.21.1-beta
```

```bash
cd ..
```

```bash
git submodule update --init --recursive
```

### Schritt 2: Config anlegen und befüllen

```bash
mkdir -p .meta-config
cp .agent-meta/howto/agent-meta.config.example.json .meta-config/project.yaml
```

Pflichtfelder:

```json
{
  "$schema": ".agent-meta/agent-meta.schema.json",
  "agent-meta-version": "0.21.1-beta",
  "ai-providers": ["Claude"],
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
py .agent-meta/scripts/sync.py --config .meta-config/project.yaml
```

Das Script erzeugt beim ersten Aufruf (bei aktivem `"Claude"` in `ai-providers`):
- `CLAUDE.md` — aus Template, wenn noch nicht vorhanden
- `CLAUDE.personal.md` — persönliche Präferenzen-Template (gitignored, einmalig)
- `.claude/settings.json` — Team-Permissions Skeleton (einmalig, Hooks werden bei jedem sync gemergt)
- `.claude/settings.local.json` — persönliches Skeleton (gitignored, einmalig)
- `.gitignore` — fehlende Einträge werden ergänzt (bei jedem Sync)
- `.claude/agents/*.md` — alle Agenten, generisch benannt
- `.claude/rules/*.md` — Projekt-globale Regeln aus agent-meta (bei jedem Sync aktualisiert)
- `.claude/hooks/*.sh` — Hook-Scripts aus agent-meta (bei jedem Sync aktualisiert)
- `CLAUDE.md` managed block — wird bei jedem sync automatisch aktualisiert
- `sync.log` mit Zusammenfassung und Warnungen

Zusätzlich bei weiteren Providern (ohne `--init` nötig — beim ersten normalen sync):
- `.gemini/GEMINI.md` + `.gemini/agents/*.md` — bei aktivem `"Gemini"` Provider
- `.continue/rules/project-context.md` + `.continue/agents/*.md` + `.continue/config.yaml` — bei aktivem `"Continue"` Provider

> **managed block in CLAUDE.md:** Der Abschnitt zwischen `<!-- agent-meta:managed-begin -->` und
> `<!-- agent-meta:managed-end -->` enthält die Agenten-Tabelle und wird bei **jedem normalen sync**
> automatisch aktualisiert (nur wenn `"Claude"` in `ai-providers`). Alles außerhalb ist handgeschrieben und wird nie überschrieben.

### Schritt 4: sync.log prüfen

```bash
cat sync.log
```

Alle `[WARN]` zeigen fehlende Variablen. In `.meta-config/project.yaml` ergänzen, dann erneut syncen:

```bash
py .agent-meta/scripts/sync.py --config .meta-config/project.yaml
```

### Schritt 5: Committen

```bash
git add CLAUDE.md .claude/settings.json .claude/agents/ .gitignore .meta-config/project.yaml .gitmodules .agent-meta
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

## Multi-Provider

Seit v0.21.0 kann `sync.py` gleichzeitig Agenten-Dateien für mehrere AI-Provider erzeugen.
Konfiguration in `.meta-config/project.yaml`:

```json
"ai-providers": ["Claude", "Continue"]
```

| Provider | Agents-Verzeichnis | Kontext-Datei |
|----------|--------------------|---------------|
| `Claude` | `.claude/agents/` | `CLAUDE.md` |
| `Gemini` | `.gemini/agents/` | `.gemini/GEMINI.md` |
| `Continue` | `.continue/agents/` | `.continue/rules/project-context.md` |

Das Legacy-Feld `"ai-provider": "Claude"` (String) wird weiterhin unterstützt — kein Breaking Change.

> **Vollständige Dokumentation:** [docs/providers/multi-provider.md](multi-provider.md) — Provider-Details,
> Frontmatter-Unterschiede, Sync-Verhalten, Continue Best Practices, Troubleshooting.

---

## Projektspezifische Anpassungen

### Einfache Werte → config.json

Kurze Texte, Kommandos, Listen: in `.meta-config/project.yaml` unter `variables` eintragen.
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
py .agent-meta/scripts/sync.py --config .meta-config/project.yaml --create-ext developer

# Alle Extensions auf einmal anlegen:
py .agent-meta/scripts/sync.py --config .meta-config/project.yaml --create-ext all
```

Die Extension-Datei wird in `.claude/3-project/<prefix>-<rolle>-ext.md` erstellt mit:
- **managed block** — auto-generierter Kontext aus config-Variablen (aktualisierbar)
- **Projektbereich** — handgeschrieben, von sync.py nie angefasst

Managed block aktualisieren (z.B. nach config-Änderung):
```bash
py .agent-meta/scripts/sync.py --config .meta-config/project.yaml --update-ext
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

> **Vollständige Anleitung:** [howto/features/agent-composition.md](agent-composition.md) —
> alle Patch-Operationen (`append-after`, `replace`, `delete`, `append`), Anchor-Syntax, Beispiele.

### Externe Skills aktivieren

External Skills sind spezialisierte Agenten aus Drittrepos (z.B. 3D-Druck, CAD).

Skills werden **pro Projekt** aktiviert — in `.meta-config/project.yaml`:

```json
"external-skills": {
  "home-organization": { "enabled": true },
  "opengrid-openscad": { "enabled": true }
}
```

Welche Skills verfügbar (`approved: true`) sind: `cat .agent-meta/external-skills.config.yaml`

> **Vollständige Anleitung:** [howto/features/external-skills.md](external-skills.md) —
> Lifecycle, Troubleshooting, Meta-Maintainer-Workflow, Versionierung.

---

## CLAUDE.md iterativ verbessern

agent-meta ist **kein "einmal einrichten und vergessen"** — CLAUDE.md wird mit jedem
Claude-Fehler besser. Der `agent-meta-manager` begleitet diesen Prozess aktiv.

### Sofort nach einem Claude-Fehler

```
1. Starte den agent-meta-manager
2. Beschreibe den Fehler: "Claude hat X gemacht obwohl er Y hätte tun sollen"
3. Der Manager liest CLAUDE.md, formuliert eine präzise Regel und ergänzt sie
4. Verifizierung: "Was steht in deiner CLAUDE.md über [Thema]?"
```

### Alle 2–3 Wochen: Review-Runde

```bash
# agent-meta-manager starten und sagen:
"Führe eine CLAUDE.md Review-Runde durch"
```

Der Manager führt durch strukturierte Fragen:
- Welche Fehler hat Claude wiederholt?
- Welche Regeln sind veraltet oder redundant?
- Welche häufigen Aufgaben fehlen noch in der Doku?
- Ist die CLAUDE.md noch kompakt genug? (Empfehlung: 200–500 Zeilen)

### Qualitätsprinzip

| Gut | Schlecht |
|-----|---------|
| `KEIN any` | `Vermeide any wenn möglich` |
| `Tests in src/__tests__/` | `Tests sinnvoll ablegen` |
| Kurze Imperativsätze | Ausführliche Erklärungen |

Vollständige Anleitung: `agent-meta-manager` → Abschnitt "CLAUDE.md Review & Verbesserung".

---

## Checkliste: Projekt vollständig eingerichtet?

- [ ] `.agent-meta/` Submodul auf gewünschter Version (`v0.21.1-beta` oder neuer)
- [ ] `.meta-config/project.yaml` vollständig befüllt (inkl. `ai-providers`)
- [ ] `sync.log` ohne Warnungen
- [ ] `CLAUDE.md` vorhanden mit managed block
- [ ] `CLAUDE.md` ohne offene `{{...}}` Platzhalter
- [ ] `CLAUDE.personal.md` vorhanden (gitignored, persönlich befüllen)
- [ ] `.claude/settings.json` vorhanden und committed
- [ ] `.claude/settings.local.json` vorhanden (gitignored)
- [ ] `.claude/rules/` vorhanden mit `issue-lifecycle.md`
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
- [ ] Bei `"Gemini"` in `ai-providers`: `.gemini/GEMINI.md` vorhanden, `.gemini/agents/` befüllt
- [ ] Bei `"Continue"` in `ai-providers`: `.continue/rules/project-context.md` vorhanden, `.continue/agents/` befüllt
- [ ] `docs/REQUIREMENTS.md` initialisiert
