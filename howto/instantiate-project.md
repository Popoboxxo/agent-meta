# Howto: Neues Projekt mit agent-meta instanziieren

Diese Anleitung beschreibt, wie ein neues Sharkord-Plugin-Projekt die
standardisierten Agenten-Rollen aus `agent-meta` übernimmt.

---

## Konzept: Was bedeutet "instanziieren"?

Die Templates in `agent-meta/agents/1-generic/` sind **generische Rollen-Definitionen**,
Plattform-Layer liegen in `agent-meta/agents/2-platform/`.
Sie enthalten überall dort Platzhalter (`{{...}}`), wo projektspezifische
Informationen eingetragen werden müssen.

Beim Instanziieren:
1. Du kopierst das Template
2. Du ersetzt alle `{{PLATZHALTER}}` mit dem projektspezifischen Inhalt
3. Du legst die fertige Datei in `.claude/agents/` des Projekts ab

**Änderungen an der generischen Logik** (Workflows, Don'ts, Konventionen) werden
im Template in `agent-meta` gepflegt und dann in alle Projekte übernommen.

**Änderungen am Projektkontext** (Tech-Stack, Architektur, Commands) werden nur
im jeweiligen Projekt-Agenten gepflegt.

---

## Schritt-für-Schritt

### Schritt 1: Projekt-Präfix festlegen

Wähle einen kurzen Präfix (2–4 Zeichen) für dein Projekt.
Beispiele: `vwf` (vid-with-friends), `hi` (hero-introducer)

### Schritt 2: Verzeichnis anlegen

```bash
mkdir -p <projekt-root>/.claude/agents
```

### Schritt 3: Templates kopieren und instanziieren

**Schicht 1 — generische Rollen** (aus `agents/1-generic/`):

```bash
cp agent-meta/agents/1-generic/template-orchestrator.md .claude/agents/<project-name>.md
cp agent-meta/agents/1-generic/template-developer.md    .claude/agents/<prefix>-developer.md
cp agent-meta/agents/1-generic/template-tester.md       .claude/agents/<prefix>-tester.md
cp agent-meta/agents/1-generic/template-validator.md    .claude/agents/<prefix>-validator.md
cp agent-meta/agents/1-generic/template-requirements.md .claude/agents/<prefix>-requirements.md
cp agent-meta/agents/1-generic/template-documenter.md   .claude/agents/<prefix>-documenter.md
# Release: Sharkord-Projekte verwenden den Plattform-Layer direkt
cp agent-meta/agents/2-platform/sharkord-release.md      .claude/agents/<prefix>-release.md
# Nicht-Sharkord-Projekte: generisches Template verwenden
# cp agent-meta/agents/1-generic/template-release.md     .claude/agents/<prefix>-release.md
```

**Schicht 2 — Plattform-Layer** (aus `agents/2-platform/`):

```bash
# Sharkord-Projekte: Plattform-Layer als Docker-Basis verwenden
cp agent-meta/agents/2-platform/sharkord-docker.md      .claude/agents/<prefix>-docker.md

# Nicht-Sharkord-Projekte: generisches Template direkt verwenden
# cp agent-meta/agents/1-generic/template-docker.md     .claude/agents/<prefix>-docker.md
```

### Schritt 4: Platzhalter ersetzen

In jeder kopierten Datei:

| Platzhalter | Ersetzen durch |
|-------------|---------------|
| `{{PROJECT_NAME}}` | Vollständiger Projektname, z.B. `sharkord-vid-with-friends` |
| `{{PREFIX}}` | Kurzer Präfix, z.B. `vwf` |
| `{{PROJECT_CONTEXT}}` | Projektbeschreibung + Tech-Stack + besondere Hinweise |
| `{{CODE_CONVENTIONS}}` | Sprachspezifische Konventionen (TypeScript-Regeln, etc.) |
| `{{ARCHITECTURE}}` | Verzeichnisstruktur + Key-Patterns des Projekts |
| `{{DEV_COMMANDS}}` | Build- und Docker-Kommandos |
| `{{TEST_COMMANDS}}` | Test-Runner-Kommandos |
| `{{BUILD_COMMANDS}}` | Release-Build-Kommandos |
| `{{REQ_CATEGORIES}}` | Anforderungs-Kategorien des Projekts |
| `{{CODE_QUALITY_RULES}}` | Automatisierbare Code-Qualitäts-Checks |
| `{{EXTRA_DONTS}}` | Weitere projektspezifische Don'ts |
| `{{DOCKER_STACKS_OVERVIEW}}` | Tabelle der verfügbaren Docker-Stacks |
| `{{BUILD_COMMAND}}` | Bau-Befehl vor Docker-Start (z.B. `bun run build`) |
| `{{CONTAINER_NAME}}` | Docker-Container-Name (z.B. `sharkord-dev`) |
| `{{SHARKORD_SERVICE_NAME}}` | Service-Name in Compose (z.B. `sharkord`) |
| `{{SHARKORD_URL}}` | URL der lokalen Sharkord-Instanz (z.B. `http://localhost:3000`) |
| `{{SHARKORD_IMAGE}}` | Docker-Image mit Tag (z.B. `sharkord/sharkord:v0.0.16`) |
| `{{PLUGIN_DIR_NAME}}` | Verzeichnisname des Plugins (z.B. `sharkord-vid-with-friends`) |
| `{{EXTRA_STARTUP_INFO}}` | Zusätzliche Infos in Startup-Box (z.B. Debug-Cache-Pfad) |
| `{{APT_PACKAGES}}` | Apt-Pakete für Dockerfile.dev (z.B. `ffmpeg`) |
| `{{BINARY_NAME}}` / `{{BINARY_URL}}` | Externe Binary für Init-Container |

### Schritt 5: CLAUDE.md des Projekts anlegen

Nutze die Vorlage [CLAUDE.project-template.md](CLAUDE.project-template.md) als
Basis für die `CLAUDE.md` im Projekt-Root.

### Schritt 6: Frontmatter anpassen

In jeder Agenten-Datei den `name`-Eintrag im Frontmatter korrigieren:

```yaml
---
name: <prefix>-developer   # ← anpassen
description: "Developer-Agent für <PROJECT_NAME>."
tools: [...]
---
```

---

## Template-Updates übernehmen

Wenn ein Template in `agent-meta` verbessert wurde:

1. Vergleiche das neue Template mit der instanziierten Version im Projekt
2. Übernehme die generischen Änderungen (außerhalb der `{{...}}`-Blöcke)
3. Lasse den projektspezifischen Kontext unberührt

**Empfehlung:** Halte die projektspezifischen Blöcke klar voneinander getrennt
durch Kommentar-Marker wie `<!-- PROJEKTSPEZIFISCH -->` und
`<!-- AB HIER: GENERISCH aus agent-meta -->`.

---

## Checkliste: Projekt vollständig instanziiert?

- [ ] `.claude/agents/<project-name>.md` (Orchestrator)
- [ ] `.claude/agents/<prefix>-developer.md`
- [ ] `.claude/agents/<prefix>-tester.md`
- [ ] `.claude/agents/<prefix>-validator.md`
- [ ] `.claude/agents/<prefix>-requirements.md`
- [ ] `.claude/agents/<prefix>-documenter.md`
- [ ] `.claude/agents/<prefix>-release.md`
- [ ] `.claude/agents/<prefix>-docker.md`
- [ ] Alle `{{PLATZHALTER}}` ersetzt
- [ ] `CLAUDE.md` im Projekt-Root angelegt
- [ ] `docs/REQUIREMENTS.md` initialisiert
- [ ] `docker-compose.dev.yml` erstellt (aus template-docker Abschnitt 5)
- [ ] `tests/docker/` Verzeichnis mit Dockerfile.test + docker-compose.yml (falls Tests via Docker)
