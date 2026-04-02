# Howto: Neues Projekt mit agent-meta einrichten

---

## Konzept

Agenten werden von `sync.py` **generiert** — nie manuell kopiert oder bearbeitet.
Den Projektkontext liefert die `CLAUDE.md` des Projekts.
Projektspezifische Erweiterungen leben in `.claude/3-project/`.

---

## Ersteinrichtung

### Schritt 1: agent-meta als Submodul einbinden

```bash
git submodule add https://github.com/Popoboxxo/agent-meta .agent-meta
cd .agent-meta && git checkout v0.1.0 && cd ..
```

### Schritt 2: Config anlegen und befüllen

```bash
cp .agent-meta/agent-meta.config.example.json agent-meta.config.json
```

Pflichtfelder:

```json
{
  "agent-meta-version": "0.1.0",
  "platforms": ["sharkord"],
  "project": {
    "name": "sharkord-mein-plugin",
    "short": "mein-plugin"
  },
  "variables": { ... }
}
```

Fehlende Variablen → Warning in `sync.log`, Platzhalter bleibt sichtbar.

### Schritt 3: CLAUDE.md + Agenten generieren

```bash
py .agent-meta/scripts/sync.py --config agent-meta.config.json --init
```

Das Script erzeugt:
- `CLAUDE.md` aus Template (nur wenn noch nicht vorhanden)
- `.claude/agents/*.md` — alle Agenten, generisch benannt
- `sync.log` mit Zusammenfassung und Warnungen

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
git add CLAUDE.md .claude/ agent-meta.config.json .gitmodules .agent-meta
git commit -m "chore: initialize agent-meta agents"
```

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
mkdir -p .claude/3-project
# Datei selbst erstellen und befüllen:
# .claude/3-project/developer-ext.md
```

sync.py berührt `.claude/3-project/` nie — die Extension-Dateien werden vollständig
vom Entwickler erstellt, gepflegt und versioniert. Falls im Meta-Repo eine Vorlage
unter `agents/3-project/developer-ext.md` existiert, wird sie im `sync.log` als
Hinweis erwähnt.

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

---

## Checkliste: Projekt vollständig eingerichtet?

- [ ] `.agent-meta/` Submodul auf gewünschter Version
- [ ] `agent-meta.config.json` vollständig befüllt
- [ ] `sync.log` ohne Warnungen
- [ ] `CLAUDE.md` ohne offene `{{...}}` Platzhalter
- [ ] `.claude/agents/orchestrator.md` vorhanden
- [ ] `.claude/agents/developer.md` vorhanden
- [ ] `.claude/agents/tester.md` vorhanden
- [ ] `.claude/agents/validator.md` vorhanden
- [ ] `.claude/agents/requirements.md` vorhanden
- [ ] `.claude/agents/documenter.md` vorhanden
- [ ] `.claude/agents/release.md` vorhanden
- [ ] `.claude/agents/docker.md` vorhanden
- [ ] `docs/REQUIREMENTS.md` initialisiert
