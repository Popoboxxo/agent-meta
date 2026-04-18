# First Steps — agent-meta einrichten

> **Schnellstart ohne AI-Assistent:** `py .agent-meta/scripts/sync.py --setup`
> Der CLI-Wizard führt durch alle Pflichtfelder und startet danach `--init` automatisch.
>
> **Mit AI-Assistent:** Gib diese Datei deinem AI-Tool (Claude Code, Cursor, Copilot etc.)
> und sage: **"Hilf mir, agent-meta in diesem Projekt einzurichten."**
> Der Assistent liest dann diese Anleitung und führt dich interaktiv durch die Einrichtung.

---

## Für den AI-Assistenten: Deine Aufgabe

Du hilfst dem User dabei, `agent-meta` in seinem Projekt einzurichten.
Die Schritte sind unten beschrieben. Führe sie **nicht automatisch durch** —
erkläre jeden Schritt, frage nach fehlenden Werten und warte auf Bestätigung.

Die Config-Datei `.meta-config/project.yaml` ist das Herzstück — sie steuert welche
Agenten generiert werden und mit welchem Kontext. Hilf dem User, alle relevanten
Felder sinnvoll zu befüllen.

---

## Schritt 1: Submodul prüfen

Stelle sicher dass `.agent-meta/` im Projekt-Root existiert:

```bash
ls .agent-meta/
```

Wenn nicht vorhanden:

```bash
git submodule add https://github.com/Popoboxxo/agent-meta .agent-meta
```

```bash
git checkout v0.21.1-beta
```

```bash
cd ..
```

```bash
git submodule update --init --recursive
```

---

## Schritt 2: Config-Verzeichnis anlegen und Example-Config kopieren

```bash
mkdir -p .meta-config
cp .agent-meta/howto/project.yaml.example .meta-config/project.yaml
```

> **AI-Assistent:** Lies jetzt `.meta-config/project.yaml` und stelle dem User
> die folgenden Fragen, um alle Pflichtfelder zu befüllen.

---

## Schritt 3: Config befüllen — Pflichtfelder

**AI-Assistent: Stelle diese Fragen und trage die Antworten in die Config ein.**

### Projektidentität

- **`project.name`** — Vollständiger Projektname (z.B. `sharkord-mein-plugin`)
- **`project.prefix`** — Kürzel für Extension-Dateien, max 5 Zeichen (z.B. `mpl` für mein-plugin)
- **`project.short`** — Kurzname ohne Plattform-Prefix (z.B. `mein-plugin`)
- **`variables.PROJECT_NAME`** — gleich wie `project.name`
- **`variables.PROJECT_DESCRIPTION`** — Ein Satz: Was macht das Projekt?
- **`variables.PROJECT_GOAL`** — Für wen und was wird gelöst?

### Plattform & Technologie

- **`platforms`** — Welche Plattform? `["sharkord"]` oder `[]` für generisch
- **`variables.PROJECT_LANGUAGES`** — z.B. `TypeScript`, `Python`, `Go`
- **`variables.PLATFORM`** — z.B. `Sharkord Plugin SDK`, `Python CLI`
- **`variables.RUNTIME`** — z.B. `Bun (NICHT Node.js)`, `Python 3.x`

### Sprachen

- **`variables.COMMUNICATION_LANGUAGE`** — In welcher Sprache soll der Agent antworten? (Standard: `Deutsch`)
- **`variables.USER_INPUT_LANGUAGE`** — In welcher Sprache gibt der User Anweisungen? (Standard: `Deutsch`)
- **`variables.DOCS_LANGUAGE`** — Sprache für README, CHANGELOG, GitHub Issues (Standard: `Englisch`)
- **`variables.INTERNAL_DOCS_LANGUAGE`** — Sprache für interne Doku wie REQUIREMENTS.md (Standard: `Deutsch`)
- **`variables.CODE_LANGUAGE`** — Sprache für Kommentare & Commit-Messages (Standard: `Englisch`)

### Git

- **`variables.GIT_PLATFORM`** — `GitHub`, `GitLab` oder `Gitea`
- **`variables.GIT_REMOTE_URL`** — Remote-URL des Repositories
- **`variables.GIT_MAIN_BRANCH`** — Haupt-Branch (Standard: `main`)

### Commands

- **`variables.BUILD_COMMAND`** — z.B. `bun run build`
- **`variables.TEST_COMMAND`** — z.B. `bun test`
- **`variables.DEV_COMMANDS`** — Build- und Run-Kommandos für den Developer-Agenten

### Projektkontext

- **`variables.PROJECT_CONTEXT`** — Längere Beschreibung: Tech-Stack, Besonderheiten, Ziel
- **`variables.ARCHITECTURE`** — Verzeichnisstruktur und Entry-Points
- **`variables.CODE_CONVENTIONS`** — Coding-Regeln (Sprache, Namenskonventionen, Verbote)

### Externe Skills (optional)

Falls das Projekt spezialisierte externe Skill-Agenten benötigt (z.B. 3D-Druck, CAD):

**AI-Assistent:** Lies `.agent-meta/config/skills-registry.yaml` und zeige dem User
welche Skills mit `approved: true` verfügbar sind. Frage ob er welche aktivieren möchte.

Aktivierung in `.meta-config/project.yaml`:
```json
"external-skills": {
  "skill-name": { "enabled": true }
}
```

---

## Schritt 4: Rollen auswählen

Standard-Rollen (alle generisch):

```json
"roles": [
  "orchestrator", "developer", "requirements", "validator",
  "documenter", "git", "release", "ideation",
  "meta-feedback", "feature", "agent-meta-manager", "agent-meta-scout"
]
```

Für Sharkord-Projekte zusätzlich `"docker"` und `"tester"` ergänzen.

> **`agent-meta-scout`** scoutet das Claude-Ökosystem auf neue Skills, Agenten-Rollen und
> Patterns — wird nur auf explizite Anfrage aktiv, nie vom Orchestrator automatisch gestartet.

**AI-Assistent:** Frage ob alle Rollen benötigt werden oder ob einige weggelassen werden sollen.

---

## Schritt 4b: Provider wählen (optional)

Seit v0.21.0 unterstützt agent-meta mehrere AI-Provider gleichzeitig.
Standardmäßig wird nur Claude aktiviert — weitere Provider sind optional.

```json
"ai-providers": ["Claude"]
```

Mehrere Provider gleichzeitig (z.B. Claude + Continue):

```json
"ai-providers": ["Claude", "Continue"]
```

| Provider | Erzeugt | Wann sinnvoll |
|----------|---------|---------------|
| `Claude` | `.claude/agents/`, `CLAUDE.md`, Rules, Hooks | Standard — immer empfohlen |
| `Gemini` | `.gemini/agents/`, `.gemini/GEMINI.md` | Wenn Gemini CLI im Team eingesetzt wird |
| `Continue` | `.continue/agents/`, `.continue/rules/project-context.md` | Wenn Continue im Team eingesetzt wird |

> Backward-Compatible: `"ai-provider": "Claude"` (String) funktioniert weiterhin unverändert.
> Vollständige Dokumentation: [docs/providers/multi-provider.md](multi-provider.md)

**AI-Assistent:** Frage ob neben Claude noch weitere Provider (Gemini, Continue) genutzt werden sollen.

---

## Schritt 5: Dry-Run

Bevor echte Dateien geschrieben werden — prüfen ob die Config stimmt:

```bash
py .agent-meta/scripts/sync.py --config .meta-config/project.yaml --dry-run
```

**AI-Assistent:** Zeige dem User die Ausgabe. Erkläre `[WARN]`-Meldungen
(fehlende Variablen) und hilf sie zu beheben.

---

## Schritt 6: Ersten Sync ausführen

```bash
py .agent-meta/scripts/sync.py --config .meta-config/project.yaml --init
```

Das erzeugt (bei aktivem `"Claude"` Provider):
- `CLAUDE.md` — Projekt-Kontext für den AI-Assistenten
- `CLAUDE.personal.md` — Persönliche Präferenzen (gitignored)
- `.claude/settings.json` — Team-Permissions Skeleton
- `.claude/settings.local.json` — Persönliche Permissions (gitignored)
- `.claude/agents/*.md` — Alle generierten Agenten
- `.claude/rules/*.md` — Projekt-globale Regeln (auto-loaded)
- `.claude/hooks/*.sh` — Hook-Scripts (opt-in über config)
- `.gitignore` — Fehlende Einträge werden ergänzt

Zusätzlich wenn weitere Provider aktiv sind:
- `.gemini/GEMINI.md` + `.gemini/agents/*.md` — bei aktivem `"Gemini"` Provider
- `.continue/rules/project-context.md` + `.continue/agents/*.md` + `.continue/config.yaml` — bei aktivem `"Continue"` Provider

---

## Schritt 7: sync.log prüfen

```bash
cat sync.log
```

Alle `[WARN]` zeigen fehlende Variablen. In `.meta-config/project.yaml` ergänzen, dann erneut syncen:

```bash
py .agent-meta/scripts/sync.py --config .meta-config/project.yaml
```

---

## Schritt 8: Committen

```bash
git add CLAUDE.md
```

```bash
git add .claude/settings.json .claude/agents/ .gitignore
```

```bash
git add .meta-config/ .gitmodules .agent-meta
```

```bash
git commit -m "chore: initialize agent-meta agents"
```

> `CLAUDE.personal.md` und `.claude/settings.local.json` sind gitignored — nie committen.

---

## Schritt 9: CLAUDE.md vervollständigen

Öffne `CLAUDE.md` und fülle die handgeschriebenen Abschnitte aus — der managed block
(zwischen den `<!-- agent-meta:managed-begin/end -->` Kommentaren) wird automatisch
von `sync.py` befüllt und darf nicht manuell bearbeitet werden.

---

## Fertig?

Checkliste:

- [ ] `.agent-meta/` Submodul auf gewünschter Version
- [ ] `.meta-config/project.yaml` vollständig befüllt (inkl. `ai-providers`)
- [ ] Kein `agent-meta.config.yaml` mehr im Projekt-Root (ggf. via `--to-meta-config` migriert)
- [ ] `sync.log` ohne Warnungen
- [ ] `CLAUDE.md` vorhanden mit managed block (wenn `"Claude"` in `ai-providers`)
- [ ] `CLAUDE.md` ohne offene `{{...}}` Platzhalter
- [ ] `.claude/agents/orchestrator.md` vorhanden
- [ ] `.claude/agents/developer.md` vorhanden
- [ ] Bei `"Gemini"`: `.gemini/GEMINI.md` vorhanden
- [ ] Bei `"Continue"`: `.continue/rules/project-context.md` vorhanden
- [ ] Committed

**Nächster Schritt:** Starte mit dem `orchestrator`-Agenten in Claude Code:
`> Use orchestrator`
