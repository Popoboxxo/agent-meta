# Howto: Neues Projekt mit agent-meta einrichten

---

## Konzept

Agenten in `1-generic/` und `2-platform/` sind **fertige, sofort einsetzbare Rollen**.
Sie enthalten keine Projekt-Platzhalter mehr — den Projektkontext liefert die `CLAUDE.md`
des Projekts, die jeder Agent beim Start liest.

**Was du tust beim Einrichten:**
1. `CLAUDE.md` für das Projekt anlegen — vollständige Projektbeschreibung
2. Agenten-Dateien aus dem passenden Layer kopieren und nur Frontmatter anpassen
3. Für Plattform-spezifische Agenten (Docker, Release): Plattform-Layer aus `2-platform/` verwenden

---

## Schritt-für-Schritt

### Schritt 1: Projekt-Präfix festlegen

Kurzer Präfix (2–4 Zeichen). Beispiele: `vwf`, `hi`

### Schritt 2: CLAUDE.md anlegen

Nutze [CLAUDE.project-template.md](CLAUDE.project-template.md) als Basis.
Die CLAUDE.md ist die **einzige Stelle** für projektspezifische Informationen:
Tech-Stack, Architektur, Code-Konventionen, Anforderungs-Kategorien, Plattform.

### Schritt 3: `.claude/agents/` Verzeichnis anlegen

```bash
mkdir -p <projekt-root>/.claude/agents
```

### Schritt 4: Agenten kopieren

**Generische Rollen** (aus `1-generic/` — direkt verwendbar für alle Projekte):

```bash
cp agent-meta/agents/1-generic/orchestrator.md  .claude/agents/<project-name>.md
cp agent-meta/agents/1-generic/developer.md     .claude/agents/<prefix>-developer.md
cp agent-meta/agents/1-generic/tester.md        .claude/agents/<prefix>-tester.md
cp agent-meta/agents/1-generic/validator.md     .claude/agents/<prefix>-validator.md
cp agent-meta/agents/1-generic/requirements.md  .claude/agents/<prefix>-requirements.md
cp agent-meta/agents/1-generic/documenter.md    .claude/agents/<prefix>-documenter.md
```

**Plattform-Layer** (aus `2-platform/` — überschreibt den generischen Agenten):

```bash
# Sharkord-Projekte:
cp agent-meta/agents/2-platform/sharkord-release.md  .claude/agents/<prefix>-release.md
cp agent-meta/agents/2-platform/sharkord-docker.md   .claude/agents/<prefix>-docker.md

# Andere Projekte: generischen Agenten verwenden
# cp agent-meta/agents/1-generic/release.md  .claude/agents/<prefix>-release.md
# cp agent-meta/agents/1-generic/docker.md   .claude/agents/<prefix>-docker.md
```

### Schritt 5: Frontmatter in jeder kopierten Datei anpassen

Nur `name` und `description` ändern — der Rest bleibt unverändert:

```yaml
---
name: <prefix>-developer
description: "Developer-Agent für <PROJECT_NAME>."
tools: [...]
---
```

### Schritt 6: Projekt-spezifische Agenten (Ausnahmefall)

Nur wenn ein Agent **fundamental** vom Generic/Platform-Layer abweicht:
Datei in `3-project/` anlegen (oder direkt im Repo in `.claude/agents/`),
vollständig neu schreiben, auf `CLAUDE.md` als Kontext-Quelle verweisen.

---

## Agenten-Updates übernehmen

Wenn ein Agent in `1-generic/` oder `2-platform/` verbessert wurde:

```bash
# Geänderten Agenten erneut ins Projekt kopieren
cp agent-meta/agents/1-generic/developer.md .claude/agents/<prefix>-developer.md
# Frontmatter (name, description) danach wieder anpassen
```

Da der Projektkontext in der `CLAUDE.md` liegt und nicht im Agenten selbst,
ist das Update ein einfaches Überschreiben — kein Merge nötig.

---

## Checkliste: Projekt vollständig eingerichtet?

- [ ] `CLAUDE.md` im Projekt-Root — vollständige Projektbeschreibung
- [ ] `.claude/agents/<project-name>.md` (Orchestrator)
- [ ] `.claude/agents/<prefix>-developer.md`
- [ ] `.claude/agents/<prefix>-tester.md`
- [ ] `.claude/agents/<prefix>-validator.md`
- [ ] `.claude/agents/<prefix>-requirements.md`
- [ ] `.claude/agents/<prefix>-documenter.md`
- [ ] `.claude/agents/<prefix>-release.md`
- [ ] `.claude/agents/<prefix>-docker.md`
- [ ] Frontmatter (`name`, `description`) in allen Agenten angepasst
- [ ] `docs/REQUIREMENTS.md` initialisiert
- [ ] `docker-compose.dev.yml` angelegt (s. `2-platform/sharkord-docker.md` Abschnitt 5)
- [ ] `tests/docker/` mit Dockerfile.test + docker-compose.yml (falls Docker-Tests)
