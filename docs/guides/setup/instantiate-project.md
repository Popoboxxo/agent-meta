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

### .claude/commands/ — Slash Commands

```
.claude/commands/
  analyze-logs.md  → /project:analyze-logs    ← von agent-meta generiert
  feedback.md      → /project:feedback        ← von agent-meta generiert
  commit.md        → /project:commit          ← von agent-meta generiert
  deploy.md        → /project:deploy          ← projekt-eigen (manuell)
```

Slash Commands laufen im **Haupt-Kontext** (kein isoliertes Context Window wie Agenten).
Geeignet für schnelle, wiederkehrende Einzel-Aktionen.

agent-meta verwaltet einen Teil der Commands automatisch (generisch und plattformspezifisch,
analog zu Agenten). Projekt-eigene Commands in `.claude/3-project/commands/` werden nie überschrieben.

> Vollständige Dokumentation: [howto/features/commands.md](../features/commands.md) — Layer-System, Frontmatter-Felder, `$ARGUMENTS`, `--create-command`, Stale-Tracking.

| `.claude/agents/` | `.claude/commands/` |
|-------------------|---------------------|
| Vollständige Persona, isolierter Kontext | Schneller Einzel-Workflow im Hauptchat |
| Für komplexe, mehrstufige Aufgaben | Für wiederkehrende Einzel-Aktionen |
| Von agent-meta generiert (1-generic / 2-platform) | Von agent-meta generiert + projekt-eigen |

Framework-Commands (immer verfügbar nach Sync): `/analyze-logs`, `/feedback`, `/commit`, `/merge`, `/doc-now`, `/diagnose`, `/upgrade-meta` u.a.

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
            "agent-meta-scout", "bug-feature-analyzer"],
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
| `.claude/agents/junior-developer.md` | `1-generic/junior-developer.md` (optional, 3-Tier-System) |
| `.claude/agents/senior-developer.md` | `1-generic/senior-developer.md` (optional, 3-Tier-System) |
| `.claude/agents/principal-developer.md` | `1-generic/principal-developer.md` (optional, Last-Resort-Eskalation über senior-developer, ultra-Tier) |
| `.claude/agents/intern-developer.md` | `1-generic/intern-developer.md` (optional, Easter-Egg/Gag-Agent — read-only, nicht für echte Arbeit) |
| `.claude/agents/tester.md` | `1-generic/tester.md` |
| `.claude/agents/e2e-tester.md` | `1-generic/e2e-tester.md` (optional, für Web-Projekte mit E2E/visueller Regression/a11y) |
| `.claude/agents/validator.md` | `1-generic/validator.md` |
| `.claude/agents/requirements.md` | `1-generic/requirements.md` |
| `.claude/agents/documenter.md` | `1-generic/documenter.md` |
| `.claude/agents/release.md` | `2-platform/sharkord-release.md` |
| `.claude/agents/docker.md` | `2-platform/sharkord-docker.md` |
| `.claude/agents/feature.md` | `1-generic/feature.md` |
| `.claude/agents/agent-meta-manager.md` | `1-generic/agent-meta-manager.md` |
| `.claude/agents/agent-meta-scout.md` | `1-generic/agent-meta-scout.md` |
| `.claude/agents/prompt-engineer.md` | `1-generic/prompt-engineer.md` |
| `.claude/agents/log-analyzer.md` | `1-generic/log-analyzer.md` (oder `2-platform/homeassistant-log-analyzer.md`) |
| `.claude/agents/feedback.md` | `1-generic/feedback.md` |
| `.claude/agents/se-requirements.md` | `1-generic/se-requirements.md` |
| `.claude/agents/se-architect.md` | `1-generic/se-architect.md` |
| `.claude/agents/se-critic.md` | `1-generic/se-critic.md` |
| `.claude/agents/concept-reviewer.md` | `1-generic/concept-reviewer.md` (optional, für concept-development Pipeline) |
| `.claude/agents/se-interface-mgr.md` | `1-generic/se-interface-mgr.md` |
| `.claude/agents/se-termination.md` | `1-generic/se-termination.md` |
| `.claude/agents/se-orchestrator.md` | `1-generic/se-orchestrator.md` |
| `.claude/agents/se-junior-developer.md` | `1-generic/se-junior-developer.md` |
| `.claude/agents/se-developer.md` | `1-generic/se-developer.md` |
| `.claude/agents/se-senior-developer.md` | `1-generic/se-senior-developer.md` |
| `.claude/agents/bug-feature-analyzer.md` | `1-generic/bug-feature-analyzer.md` |
| `.claude/agents/explorer.md` | `1-generic/explorer.md` |
| `.claude/agents/database-engineer.md` | `1-generic/database-engineer.md` (optional, Schema-Design, Migrationen, Query-Optimierung) |
| `.claude/agents/incident-responder.md` | `1-generic/incident-responder.md` (optional, Live-Incident-Koordination, RCA, Hotfix-Priorisierung) |
| `.claude/agents/dependency-auditor.md` | `1-generic/dependency-auditor.md` (optional, Supply-Chain-Hygiene, SBOM, Lizenz-Compliance) |
| `.claude/agents/sre-engineer.md` | `1-generic/sre-engineer.md` (optional, SLI/SLO, Error-Budgets, Capacity-Planning, Runbooks, Reliability-Reviews) |
| `.claude/agents/technical-writer.md` | `1-generic/technical-writer.md` (optional, externe Doku: API-Referenz, Getting-Started, SDK-Docs, Tutorials) |
| `.claude/agents/data-engineer.md` | `1-generic/data-engineer.md` (optional, ETL/ELT-Pipelines, Data-Quality, Lineage-Analyse) |
| `.claude/agents/accessibility-specialist.md` | `1-generic/accessibility-specialist.md` (optional, WCAG 2.1/2.2, ARIA-Checks, Keyboard-Navigation, Screenreader) |
| `.claude/agents/design-system-architect.md` | `1-generic/design-system-architect.md` (optional, Design-System-Schema → Token-Artefakte, Farbharmonie, Variant-Contracts) |
| `.claude/agents/frontend-component-engineer.md` | `1-generic/frontend-component-engineer.md` (optional, Screen-Spec + Token-Contract → produktionsreife UI-Komponenten) |
| `.claude/agents/refactoring-specialist.md` | `1-generic/refactoring-specialist.md` (optional, systematische Transformation, Strangler-Fig, Legacy-Modernisierung) |
| `.claude/agents/product-manager.md` | `1-generic/product-manager.md` (optional, Backlog, User-Stories, Priorisierung RICE/MoSCoW, Roadmap) |
| `.claude/agents/proofreader.md` | `1-generic/proofreader.md` (optional, Korrektorat: Rechtschreibung, Grammatik, Zeichensetzung) |
| `.claude/agents/copyeditor.md` | `1-generic/copyeditor.md` (optional, Lektorat: Stil, Satzbau, Wortwiederholungen, roter Faden, Konsistenz) |
| `.claude/agents/frontend-reviewer.md` | `1-generic/frontend-reviewer.md` (optional, Review-Agent-Fleet: Komponenten, State, SSR/Hydration, Browser-APIs) |
| `.claude/agents/backend-reviewer.md` | `1-generic/backend-reviewer.md` (optional, Review-Agent-Fleet: API-Contracts, Silent Failures, Concurrency) |
| `.claude/agents/database-reviewer.md` | `1-generic/database-reviewer.md` (optional, Review-Agent-Fleet: Migration-Safety, N+1, Injection, Transaktionen) |
| `.claude/agents/ui-reviewer.md` | `1-generic/ui-reviewer.md` (optional, Review-Agent-Fleet: Design-Token, Layout-Konsistenz, Interaction-States) |
| `.claude/agents/ai-security-guardian.md` | `1-generic/ai-security-guardian.md` (optional, KI-spezifische Sicherheitsrisiken: halluzinierte Deps, fabrizierte IAM, unsichere Defaults — komplementär zu security-auditor/dependency-auditor) |
| `.claude/agents/prompt-governor.md` | `1-generic/prompt-governor.md` (optional, Prompt-Governance: PromptBOM, Audit-Trail, Provenance, Banned-Patterns) |
| `.claude/agents/app-lifecycle-governor.md` | `1-generic/app-lifecycle-governor.md` (optional, App-Lifecycle: Ownership, SLA, Data-Classification, Deprecation-Plans) |

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

## Plattform aktivieren — Beispiel HACS

Projekte, die Home-Assistant-Custom-Components für **HACS** entwickeln, aktivieren
den HACS-Preset mit einem Eintrag in `.meta-config/project.yaml`:

```json
"platforms": ["hacs"]
```

### Was der Sync dann generiert

| Ausgangsdatei (agent-meta) | Output im Projekt |
|----------------------------|-------------------|
| `agents/2-platform/hacs-{developer,code-reviewer,devops-engineer,release,tester}.md` | Wird via `role_from_platform_file` auf die gleichnamige generische Rolle komponiert — `.claude/agents/developer.md`, `code-reviewer.md`, `devops-engineer.md`, `release.md`, `tester.md` bekommen die HACS-Persona-Abschnitte injiziert (Composition `extends` + `patches`; die Meta-Keys stehen danach nicht mehr im Output-Frontmatter). Die Dateinamen bleiben generisch. |
| `rules/2-platform/hacs-integration-development.md` | `.claude/rules/integration-development.md` bzw. als Skill (siehe unten) — **nur** wenn `hacs` in `platforms` steht. Ohne die Plattform wird die Rule nicht eingesammelt. |
| `platform-configs/hacs.defaults.yaml` | Wird eingelesen und als `{{platform.hacs.*}}`-Werte in die HACS-Agents und -Rules substituiert. |

### Skill `integration-development`

Die Rule wird zusätzlich als **Skill** ausgeliefert (Preset-Key `integration-development`
in `rules-presets.yaml` — der Plattform-Präfix `hacs-` wird beim Einsammeln gestrippt):

- **Claude:** lazy geladen als `.claude/skills/integration-development/SKILL.md`
  (generiertes Frontmatter `name`/`description`).
- **Andere Provider** (z.B. Opencode): kein Skill-Channel — die Rule fällt auf den
  normalen Rules-Pfad zurück (Opencode: eingebettet in `AGENTS.md`).

### Release-Naming-Best-Practice

Der HACS-Preset enthält einen verbindlichen Release-Naming-Block: vollständige
Referenz im Skill `integration-development` (Abschnitt „Release-Naming-Best-Practice",
eiserne-Regeln-Stil mit Begründung/Fehlerklasse) plus Always-on-Anker im generierten
`release`-Agenten. Zusammengefasst:

| Thema | Regel |
|---|---|
| Tag-Format | Stable `vMAJOR.MINOR.PATCH`, Beta `vX.Y.Zb<N>` (z.B. `v1.3.0b0`) — der `v`-Prefix gehört **nur** in den Tag |
| `manifest.version` | Bare SemVer ohne `v`, exakt dem Tag-Suffix entsprechend (`v1.2.3` ↔ `"version": "1.2.3"`, `v1.3.0b0` ↔ `"version": "1.3.0b0"`) |
| Pre-Releases | Beta-Releases im GitHub-Release als **pre-release** flaggen — sonst bekommen alle User die Beta via Update-Check (HACS 2.0: `switch.<repo>_pre_release`, default OFF) |
| Immutabilität | Tags/Releases nie verschieben, löschen oder wiederverwenden (HACS cacht Versionen); Promotion beta→stable = neuer Release, nie Tag mutieren |
| Release-Notes | Summary + ✨ New features + 💥 Breaking changes (je mit Migration-Hinweis, Pflicht bei MAJOR) + Full-Changelog-Link; optional `CHANGELOG.md` |
| SemVer-Disziplin | MAJOR = Breaking (`unique_id`-/Entity-Änderungen sind IMMER breaking), MINOR = Feature, PATCH = Fix; `v0.x` nicht ohne Hinweis als „stabil" deklarieren |

Quellen:

- <https://hacs.xyz/docs/publish/start> — „If the repository uses GitHub releases, the tag name from the latest release is used to set the remote version. Just publishing tags is not enough, you need to publish releases."
- <https://hacs.xyz/docs/use/entities/switch> — HACS 2.0 Pre-Release-Mechanik; Beispiel-Tags `v1.0.0`, `v2.0.0b0`
- <https://developers.home-assistant.io/docs/versioning> — HA nutzt PEP-440-Suffixe (`b<N>` für Betas); Versionsvergleich via AwesomeVersion
- <https://semver.org/#is-v123-a-semantic-version> — `v1.2.3` ist keine Semantic Version (`v`-Prefix ist reine Tag-Konvention)
- <https://github.com/hacs/integration/releases> — Vorbild für die Release-Notes-Struktur

### Platform-Defaults und Pflichtwerte

`platform-configs/hacs.defaults.yaml` definiert fünf Keys:

| Key | Default | Bedeutung |
|-----|---------|-----------|
| `custom_components_path` | `custom_components` | Working-Default (funktioniert out of the box) |
| `integration_repo_url` | `""` (Pflicht) | Live-Referenz: das Integrations-Repo des Projekts |
| `reference_repo_url` | `""` (Pflicht) | Live-Referenz: zweites Repo (z.B. home-assistant/core) |
| `project_skills` | `""` (Pflicht) | Komma-separiert: die beiden Projekt-Skills |
| `dev_instance_url` | `""` (Pflicht) | Dev-Home-Assistant-Instanz für Dev-Test und HACS-Update-Test |

**Override anlegen** — `.claude/platform-config.yaml` im Projekt-Root:

```yaml
platform:
  hacs:
    dev_instance_url: "http://homeassistant.local:8123"
    integration_repo_url: "https://github.com/your-org/your-integration"
    reference_repo_url: "https://github.com/home-assistant/core"
    project_skills: "hacs-integration-development,hacs-integration-review"
```

**Warn-Semantik in `sync.log`:**

- Definierter, aber leerer (Pflicht-)Key → der Key wird zum **Leerstring** substituiert
  und `[WARN]` erscheint, bis das Projekt den Wert override't.
- Undefinierter Key (nicht in Defaults, nicht im Override) → der literale
  `{{platform.hacs.*}}`-Platzhalter bleibt im Output stehen (mit Warnung).

Danach `sync.log` prüfen (Schritt 4 oben) und erneut syncen, bis die HACS-Warnungen
verschwunden sind.

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
- [ ] `.claude/agents/prompt-engineer.md` vorhanden
- [ ] `.claude/agents/log-analyzer.md` vorhanden
- [ ] `.claude/agents/feedback.md` vorhanden
- [ ] `.claude/agents/bug-feature-analyzer.md` vorhanden
- [ ] `.claude/agents/explorer.md` vorhanden
- [ ] `.claude/agents/se-requirements.md` vorhanden
- [ ] `.claude/agents/se-architect.md` vorhanden
- [ ] `.claude/agents/se-critic.md` vorhanden
- [ ] `.claude/agents/concept-reviewer.md` vorhanden (wenn concept-development Pipeline genutzt)
- [ ] `.claude/agents/se-interface-mgr.md` vorhanden
- [ ] `.claude/agents/se-termination.md` vorhanden
- [ ] `.claude/agents/se-orchestrator.md` vorhanden
- [ ] `.claude/agents/se-junior-developer.md` vorhanden
- [ ] `.claude/agents/se-developer.md` vorhanden
- [ ] `.claude/agents/se-senior-developer.md` vorhanden
- [ ] `.claude/commands/analyze-logs.md` vorhanden (nach Sync)
- [ ] `.claude/commands/feedback.md` vorhanden (nach Sync)
- [ ] Bei `"Gemini"` in `ai-providers`: `.gemini/GEMINI.md` vorhanden, `.gemini/agents/` befüllt
- [ ] Bei `"Continue"` in `ai-providers`: `.continue/rules/project-context.md` vorhanden, `.continue/agents/` befüllt
- [ ] `docs/REQUIREMENTS.md` initialisiert
