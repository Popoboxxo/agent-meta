# Howto: Neues Projekt mit agent-meta einrichten

---

## Konzept

Agenten in `1-generic/` und `2-platform/` sind **fertige, sofort einsetzbare Rollen**.
Sie werden vom `sync.py`-Script **automatisch generiert** — nicht manuell kopiert.

Den Projektkontext liefert die `CLAUDE.md` des Projekts, die jeder Agent beim Start liest.
Die Agenten-Dateien in `.claude/agents/` sind **generierter Output** und werden nie manuell bearbeitet.

---

## Ersteinrichtung (neues Projekt)

### Schritt 1: agent-meta als Submodul einbinden

```bash
git submodule add https://github.com/Popoboxxo/agent-meta .agent-meta
cd .agent-meta && git checkout v0.1.0 && cd ..
```

### Schritt 2: Config-Datei anlegen und befüllen

```bash
cp .agent-meta/agent-meta.config.example.json agent-meta.config.json
```

Pflichtfelder in `agent-meta.config.json`:

```json
{
  "agent-meta-version": "0.1.0",
  "platforms": ["sharkord"],
  "project": {
    "name": "sharkord-mein-plugin",
    "prefix": "mp",
    "short": "mein-plugin"
  },
  "variables": { ... }
}
```

Alle `{{PLATZHALTER}}` die in `CLAUDE.md` und Agenten vorkommen, müssen im `variables`-Block
stehen. Fehlende Variablen → Warning in `sync.log`, Platzhalter bleibt sichtbar.

### Schritt 3: CLAUDE.md + Agenten generieren

```bash
py .agent-meta/scripts/sync.py --config agent-meta.config.json --init
```

Das Script:
- Erzeugt `CLAUDE.md` aus `howto/CLAUDE.project-template.md` (nur wenn noch nicht vorhanden)
- Erzeugt alle `.claude/agents/*.md` aus der Drei-Schichten-Hierarchie
- Schreibt `sync.log` mit Zusammenfassung und Warnungen

### Schritt 4: sync.log prüfen

```bash
cat sync.log
```

Alle Warnungen (`[WARN]`) zeigen fehlende Variablen. In `agent-meta.config.json` ergänzen,
dann erneut syncen:

```bash
py .agent-meta/scripts/sync.py --config agent-meta.config.json
```

### Schritt 5: Alles committen

```bash
git add CLAUDE.md .claude/agents/ agent-meta.config.json .gitmodules .agent-meta
git commit -m "chore: initialize agent-meta agents"
```

---

## CLAUDE.md nach Erstanlage befüllen

Nach `--init` enthält `CLAUDE.md` noch offene Platzhalter (wenn nicht alle in der Config stehen).
Diese manuell befüllen, dann `--only-variables` laufen lassen:

```bash
# Nach manuellem Bearbeiten der CLAUDE.md:
py .agent-meta/scripts/sync.py --config agent-meta.config.json --only-variables
```

---

## Agenten-Updates übernehmen (neue agent-meta Version)

```bash
# 1. Submodul auf neue Version ziehen
cd .agent-meta && git checkout v0.2.0 && cd ..

# 2. Versionsnummer in agent-meta.config.json aktualisieren
#    "agent-meta-version": "0.2.0"

# 3. Agenten neu generieren
py .agent-meta/scripts/sync.py --config agent-meta.config.json

# 4. sync.log prüfen (neue Platzhalter?)
cat sync.log

# 5. Committen
git add .claude/agents/ .agent-meta agent-meta.config.json
git commit -m "chore: upgrade agent-meta to v0.2.0"
```

Da der Projektkontext in `CLAUDE.md` liegt und nicht in den Agenten,
ist das Update ein einfaches Überschreiben — kein Merge nötig.

---

## Projektspezifische Erweiterungen

Generische Agenten haben dedizierte Erweiterungspunkte via `{{PLATZHALTER}}`.
Damit lassen sich plattform- oder projektspezifische Inhalte **hinzufügen,
ohne den gesamten Agenten zu überschreiben**:

| Platzhalter | Agent | Zweck |
|-------------|-------|-------|
| `{{PROJECT_CONTEXT}}` | alle | Projektbeschreibung aus CLAUDE.md |
| `{{CODE_CONVENTIONS}}` | developer | Sprachspezifische Code-Regeln |
| `{{ARCHITECTURE}}` | developer | Verzeichnisstruktur, Entry-Points |
| `{{DEV_COMMANDS}}` | developer | Build/Run-Kommandos |
| `{{EXTRA_DONTS}}` | developer | Projektspezifische Verbote |
| `{{EXTRA_ORCHESTRATOR_KNOWLEDGE}}` | orchestrator | Zusätzliche Workflows, Delegation-Regeln |
| `{{EXTRA_TESTER_KNOWLEDGE}}` | tester | Manuelle E2E-Workflows, Test-Besonderheiten |
| `{{EXTRA_DOCUMENTER_KNOWLEDGE}}` | documenter | Doku-Besonderheiten des Projekts |
| `{{EXTRA_REQ_KNOWLEDGE}}` | requirements | Domänenspezifische Anforderungs-Regeln |
| `{{CODE_QUALITY_RULES}}` | validator | Linting-Regeln, Quality-Gates |
| `{{REQ_CATEGORIES}}` | requirements | Anforderungs-Kategorien |
| `{{TEST_COMMANDS}}` | tester | Test-Runner-Kommandos |
| `{{BUILD_COMMANDS}}` | release | Build-Schritte |

→ Alle Werte in `agent-meta.config.json` unter `variables` eintragen.

Nur wenn ein Agent **fundamental** von Generic/Platform abweicht (sehr selten):
Datei unter `3-project/<rolle>.md` anlegen — überschreibt alles.

---

## Checkliste: Projekt vollständig eingerichtet?

- [ ] `.agent-meta/` Submodul auf gewünschter Version
- [ ] `agent-meta.config.json` vollständig befüllt (alle Variablen)
- [ ] `sync.log` ohne Warnungen
- [ ] `CLAUDE.md` im Projekt-Root — vollständige Projektbeschreibung, keine offenen `{{...}}`
- [ ] `.claude/agents/<project-short>.md` (Orchestrator)
- [ ] `.claude/agents/<prefix>-developer.md`
- [ ] `.claude/agents/<prefix>-tester.md`
- [ ] `.claude/agents/<prefix>-validator.md`
- [ ] `.claude/agents/<prefix>-requirements.md`
- [ ] `.claude/agents/<prefix>-documenter.md`
- [ ] `.claude/agents/<prefix>-release.md`
- [ ] `.claude/agents/<prefix>-docker.md`
- [ ] `docs/REQUIREMENTS.md` initialisiert
