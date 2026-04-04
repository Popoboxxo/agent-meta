# agent-meta — Meta-Repository für Agenten-Standards

## Zweck

Dieses Repository ist das **zentrale Meta-Repository** für die Standardisierung und
Wiederverwendung von Claude-Agenten-Rollen über alle Projekte hinweg.

---

## Kernprinzipien

**1. `CLAUDE.md` des Projekts ist die einzige Wahrheit.**
Sie beschreibt das Projekt vollständig (Ziel, Tech-Stack, Architektur, Konventionen).
Agenten lesen sie beim Start — sie enthalten keinen eigenen Kontext-Block.

**2. `.claude/agents/` ist generierter Output — nie manuell bearbeiten.**
Dateien werden von `sync.py` erzeugt und bei jedem Sync überschrieben.
Änderungen gehören in `agent-meta.config.json` (Variablen) oder die Agent-Quelldateien.

**3. Agenten haben generische Namen — kein Prefix.**
Ein Projekt pro Workspace. Die Agenten heißen `developer.md`, `tester.md` etc.
Kein `vwf-developer.md` oder `hi-tester.md` mehr.

**4. Projektspezifische Erweiterungen gehören in `.claude/3-project/`.**
Nicht in die generierten Agenten, nicht als Config-Variable.
Der generierte Agent liest die Erweiterungsdatei selbst zur Laufzeit.

---

## Schichten-Modell

```
0-external/   Externe Skill-Agenten aus Drittrepos (via Git Submodule).
              Höchste Priorität. Konfiguriert in external-skills.config.json.
              enabled: true/false — binäre Aktivierung pro Skill.

1-generic/    Universell. Gilt für jedes Projekt. Wird immer generiert,
              solange kein Override in 2-platform oder 3-project existiert.

2-platform/   Plattformspezifisch. Überschreibt den Generic-Agent für alle
              Projekte auf dieser Plattform (z.B. alle Sharkord-Plugins).

3-project/    Projektspezifisch. Zwei Arten:
              - <rolle>.md      → Override: ersetzt den generierten Agenten komplett
              - <rolle>-ext.md  → Extension: wird vom generierten Agenten additiv geladen
```

**Override-Reihenfolge (für generierte Agenten):**
```
1-generic  →  2-platform  →  3-project/<rolle>.md  →  0-external (eigenständige Rollen)
```

**Extension (additiv, kein Override):**
```
generierter Agent  +  .claude/3-project/<rolle>-ext.md  =  voller Agent-Kontext
```
Extension-Dateien leben **ausschließlich im Zielprojekt** — sie werden von sync.py
nie berührt. Erstellen, bearbeiten und versionieren liegt vollständig beim Projekt.

---

## Verzeichnisstruktur

```
agent-meta/
  agents/
    1-generic/          ← universell, plattformunabhängig
      orchestrator.md
      developer.md
      tester.md
      validator.md
      requirements.md
      documenter.md
      release.md
      docker.md
      git.md

    2-platform/         ← plattformspezifisch (überschreibt 1-generic)
      sharkord-docker.md
      sharkord-release.md

    3-project/          ← projektspezifisch (im Meta-Repo als Vorlage, selten)
      developer-ext.md  ← Beispiel: Extension-Vorlage für developer
                           Overrides: <rolle>.md (ersetzt komplett)
                           Extensions: <rolle>-ext.md (additiv geladen)

    0-external/         ← Wrapper-Template für externe Skill-Agenten
      _skill-wrapper.md ← generisches Template (einmalig, nie manuell bearbeiten)

  external/             ← Git Submodule (externe Skill-Repos, via --add-skill)
    <repo-name>/        ← gepinnter Commit, enthält SKILL.md + Referenzdokumente

  external-skills.config.json  ← Zentrale Skill-Konfiguration (Modell A)
  external-skills.catalog.json ← Katalog bekannter/empfohlener Skill-Repos (für agent-meta-manager)

  howto/
    instantiate-project.md  ← Schritt-für-Schritt Einrichtung
    upgrade-guide.md         ← Upgrade auf neue agent-meta Version
    CLAUDE.project-template.md
    sync-concept.md
    template-gap-analysis.md

  snippets/
    tester/
      bun-typescript.md    ← Sprachspezifische Test-Snippets für TypeScript/Bun
      pytest-python.md     ← Sprachspezifische Test-Snippets für Python/pytest
    developer/
      bun-typescript.md    ← Code-Patterns & Best Practices für TypeScript/Bun
      pytest-python.md     ← Code-Patterns & Best Practices für Python

  scripts/
    sync.py              ← Agent-Generator
```

---

## Agenten im Zielprojekt

### Generierte Agenten (Self-Hosting)

<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on every sync. -->
<!-- Manual changes here will be overwritten. -->

Generiert von agent-meta v0.14.0 — `2026-04-04`

> **Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben.

| Agent | Zuständigkeit |
|-------|--------------|
| `agent-meta-manager` | agent-meta verwalten: Upgrade, Sync, Feedback, projektspezifische Agenten anlegen |
| `developer` | Feature-Implementierung und Bugfixes nach REQ-IDs |
| `documenter` | Doku pflegen: CODEBASE_OVERVIEW, ARCHITECTURE, README, Erkenntnisse |
| `feature` | Neues Feature end-to-end durchführen: Branch → REQ → TDD → Dev → Validate → PR |
| `git` | Commits, Branches, Tags, Push/Pull und alle Git-Operationen |
| `ideation` | Neue Ideen explorieren, Vision schärfen, Übergabe an requirements |
| `meta-feedback` | Verbesserungsvorschläge für agent-meta als GitHub Issues einreichen |
| `orchestrator` | Einstiegspunkt für alle Entwicklungsaufgaben — koordiniert alle anderen Agenten |
| `release` | Versioning, Changelog, Build-Artifact, GitHub Release erstellen |
| `requirements` | Anforderungen aufnehmen, REQ-IDs vergeben, REQUIREMENTS.md pflegen |
| `validator` | Code gegen REQs prüfen, DoD-Checkliste, Traceability-Audit |
<!-- agent-meta:managed-end -->

### Update-Verhalten bei sync

| Datei | Wird bei sync überschrieben? | Bekommt generische Updates? |
|-------|-----------------------------|-----------------------------|
| `.claude/agents/*.md` (generiert) | ✅ Ja, immer | ✅ Ja |
| `CLAUDE.md` — managed block | ✅ Ja, managed block wird aktualisiert | ✅ Ja (AGENT_HINTS + Version) |
| `CLAUDE.md` — Rest | ❌ Nein, handgeschrieben | ❌ Manuell pflegen |
| `.claude/3-project/*-ext.md` (Extension) | ❌ Nein, nur einmalig kopiert | ❌ Manuell pflegen |
| `.claude/3-project/*.md` (Override, falls vorhanden) | ❌ Wird nicht generiert — liegt im Projekt | ❌ Manuell pflegen |

**CLAUDE.md managed block** — eingeleitet durch `<!-- agent-meta:managed-begin -->`:
- Wird von `sync.py` bei **jedem normalen sync** automatisch aktualisiert
- Enthält: Agenten-Hints-Tabelle (`AGENT_HINTS`) mit Orchestrator-Einstiegspunkt + agent-meta Version + Datum
- Manuelle Änderungen innerhalb des Blocks werden überschrieben
- Kein managed block in `CLAUDE.md` → sync gibt `[WARN]` aus mit Hinweis zum manuellen Einfügen
- `--init` erstellt `CLAUDE.md` aus Template inkl. managed block (nur wenn nicht vorhanden)

---

## Projektspezifische Anpassungen

### Entscheidungsbaum

```
Was brauche ich?
│
├─ Einfacher Wert (Kommando, kurzer Text, Liste)?
│   → Variable in agent-meta.config.json
│   → Wird per {{PLATZHALTER}} in den Agenten injiziert
│   → Beispiele: BUILD_COMMAND, CODE_CONVENTIONS, REQ_CATEGORIES
│
├─ Strukturiertes Zusatzwissen (SDK-Patterns, E2E-Workflow, Plattform-Regeln)?
│  Gilt es für ALLE Projekte auf einer Plattform?
│   → Ja → 2-platform/<plattform>-<rolle>.md (neuer/erweiterter Agent)
│   → Nein (nur dieses Projekt) → .claude/3-project/<rolle>-ext.md  ← EXTENSION
│
└─ Fundamentaler Unterschied — anderer Workflow, andere Struktur, anderes Tooling?
    → .claude/3-project/<rolle>.md  ← OVERRIDE (selten, gut begründen)
```

### Extension: `.claude/3-project/<rolle>-ext.md`

- Handgeschriebene Markdown-Datei im Zielprojekt
- Wird vom generierten Agenten **beim Start automatisch gelesen** (Extension-Hook)
- Liegt im Zielprojekt unter `.claude/3-project/<prefix>-<rolle>-ext.md`
- Wird via `--create-ext <rolle>` (oder `--create-ext all`) erstellt
- Enthält einen **managed block** (`<!-- agent-meta:managed-begin/end -->`) mit auto-generiertem Kontext aus config-Variablen — aktualisierbar via `--update-ext`
- Darunter: handgeschriebener Projektbereich — von sync.py **nie angefasst**
- Das Meta-Repo stellt **keine** Extension-Vorlagen bereit — alles Projektdomäne

**Extension-Hook** (in jedem generierten Agenten):
```markdown
Falls die Datei `.claude/3-project/<prefix>-<rolle>-ext.md` existiert:
Lies sie jetzt sofort mit dem Read-Tool und wende alle Regeln vollständig an.
```

**sync.py Extension-Kommandos:**
```bash
# Extension erstmalig anlegen (managed block + leerer Projektbereich)
py .agent-meta/scripts/sync.py --config agent-meta.config.json --create-ext developer
py .agent-meta/scripts/sync.py --config agent-meta.config.json --create-ext all

# Managed block in allen bestehenden Extensions aktualisieren
py .agent-meta/scripts/sync.py --config agent-meta.config.json --update-ext
```

### Override: `.claude/3-project/<rolle>.md`

- Liegt direkt im Zielprojekt (nicht von sync.py berührt)
- Wenn vorhanden im Meta-Repo unter `3-project/<rolle>.md`: wird wie 1-generic/2-platform behandelt, aber mit höchster Priorität
- Bekommt **keine automatischen Updates** — manuelle Pflege nötig
- Nur wenn Extension nicht reicht

---

## Config-Felder

### `ai-provider` — AI Provider (optional, empfohlen)

```json
"ai-provider": "Claude"
```

Steuert provider-spezifisches Verhalten von `sync.py`:

| Wert | Verhalten |
|------|-----------|
| `"Claude"` | `CLAUDE.md` wird automatisch erstellt (wenn nicht vorhanden) + managed block bei jedem sync aktualisiert |
| Anderer Wert / fehlt | Kein `CLAUDE.md`-Handling — weder Erstellen noch Update |

Verfügbare Werte: `Claude`, `GitHub` (weitere folgen bei Bedarf)

---

### `roles` — Agenten-Whitelist (optional)

```json
"roles": ["orchestrator", "developer", "tester", ...]
```

Fehlt der Key → alle Rollen aus `1-generic/` + aktiven `2-platform/`-Overrides werden generiert (Rückwärtskompatibel).
Ist der Key vorhanden → nur die gelisteten Rollen werden generiert. Alle anderen werden mit `[SKIP]` im Log übersprungen.

Verfügbare Rollen: `orchestrator`, `feature`, `developer`, `tester`, `validator`, `requirements`, `ideation`, `documenter`, `release`, `docker`, `meta-feedback`, `git`, `agent-meta-manager`

---

## Variablen und Platzhalter

Alle `{{PLATZHALTER}}` werden via `agent-meta.config.json` befüllt.
Auto-injiziert (nicht in config nötig): `AGENT_META_VERSION`, `AGENT_META_DATE`, `AGENT_TABLE`, `AGENT_HINTS`, `AI_PROVIDER`.

### Generische Variablen (alle Projekte)

| Platzhalter | Agent | Zweck |
|-------------|-------|-------|
| `{{PROJECT_CONTEXT}}` | alle | Projektbeschreibung |
| `{{PROJECT_GOAL}}` | alle | Primäres Ziel des Projekts (für wen, was wird gelöst) |
| `{{PROJECT_LANGUAGES}}` | alle | Verwendete Programmiersprachen |
| `{{COMMUNICATION_LANGUAGE}}` | alle | Sprache für Nutzer-Kommunikation — Agent-Output (z.B. `Englisch`) |
| `{{USER_INPUT_LANGUAGE}}` | alle | Sprache der Nutzer-Eingaben — Agent-Input (z.B. `Deutsch`) |
| `{{DOCS_LANGUAGE}}` | alle | Sprache für externe Doku: README, CHANGELOG, Release Notes, GitHub Issues |
| `{{INTERNAL_DOCS_LANGUAGE}}` | alle | Sprache für interne Doku: CODEBASE_OVERVIEW, ARCHITECTURE, REQUIREMENTS, conclusions |
| `{{CODE_LANGUAGE}}` | alle | Sprache für code-nahe Artefakte: Kommentare, Commit-Messages, Test-Beschreibungen |
| `{{AGENT_META_REPO}}` | meta-feedback | GitHub-Repo für Issues (z.B. `owner/agent-meta`) |
| `{{GIT_PLATFORM}}` | git | Plattform: `GitHub`, `GitLab` oder `Gitea` |
| `{{GIT_REMOTE_URL}}` | git | Remote-URL des Repositories |
| `{{GIT_MAIN_BRANCH}}` | git | Haupt-Branch (z.B. `main` oder `master`) |
| `{{CODE_CONVENTIONS}}` | developer | Sprachspezifische Regeln |
| `{{ARCHITECTURE}}` | developer | Verzeichnisstruktur, Entry-Points |
| `{{DEV_COMMANDS}}` | developer, orchestrator | Build/Run-Kommandos |
| `{{EXTRA_DONTS}}` | developer | Zusätzliche Verbote (kurze Liste) |
| `{{CODE_QUALITY_RULES}}` | validator | Linting-Regeln, Quality-Gates |
| `{{REQ_CATEGORIES}}` | requirements | Anforderungs-Kategorien |
| `{{TEST_COMMANDS}}` | tester | Test-Runner-Kommandos |
| `{{TESTER_SNIPPETS_PATH}}` | tester | Pfad zur Snippet-Datei (relativ zu `snippets/`) |
| `{{DEVELOPER_SNIPPETS_PATH}}` | developer | Pfad zur Snippet-Datei (relativ zu `snippets/`) |
| `{{BUILD_COMMANDS}}` | release | Build-Schritte |

### Infrastruktur-Variablen — generisch (Docker, Ports)

| Platzhalter | Zweck | Format |
|-------------|-------|--------|
| `{{SYSTEM_DEPENDENCIES}}` | Kern-Abhängigkeiten mit konkreten Versionen | Markdown-Liste |
| `{{SYSTEM_URLS}}` | Relevante System-URLs (Web-UI, APIs, Signaling) | Markdown-Liste |
| `{{PRIMARY_PORT}}` | Haupt-Port der Anwendung | Einzelwert |
| `{{EXTRA_PORTS}}` | Weitere benötigte Ports neben `PRIMARY_PORT` | Markdown-Liste |
| `{{SERVICE_NAME}}` | Compose-Service-Name | Einzelwert |
| `{{CONTAINER_NAME}}` | Docker-Container-Name | Einzelwert |

### Plattform-Variablen — nur bei `"platforms": ["sharkord"]`

| Platzhalter | Zweck | Format |
|-------------|-------|--------|
| `{{PRIMARY_IMAGE_TAG}}` | Docker-Image-Tag des Sharkord-Kernsystems | Einzelwert |
| `{{PLUGIN_DIR_NAME}}` | Plugin-Verzeichnisname = `package.json` `name` | Einzelwert |

### Projektspezifische Variablen — individuelle Werte pro Projekt

| Platzhalter | Zweck | Format |
|-------------|-------|--------|
| `{{BUILD_OUTPUT}}` | Beschreibung der Build-Artefakte | Text |
| `{{ARTIFACT_ZIP_CMD}}` | Befehl zum Erstellen des ZIP-Artifacts | Shell-Befehl |
| `{{ARTIFACT_TAR_CMD}}` | Befehl zum Erstellen des TAR-Artifacts | Shell-Befehl |
| `{{GH_ASSETS}}` | Pfade der GitHub-Release-Assets | Leerzeichen-getrennt |
| `{{BUILD_SYSTEM_NOTES}}` | Hinweise zum Build-System | Text |
| `{{VERSION_DIST_BEHAVIOUR}}` | Wie landet die Version im Dist? | Text |

---

## Snippets

Sprachspezifische Code-Beispiele, die Agenten zur Laufzeit lesen — sprachunabhängige Templates
können so plattformspezifische Syntax einbinden, ohne sie im Agent-Template hart zu kodieren.

### Konzept

```
agent-meta/snippets/<rolle>/<sprache-runtime>.md   ← versionierte Quelldateien
    ↓  sync.py COPY
.claude/snippets/<rolle>/<sprache-runtime>.md       ← im Zielprojekt (generiert)
    ↓  Read-Tool zur Laufzeit
Agent nutzt sprachspezifische Syntax
```

### Frontmatter

Jede Snippet-Datei enthält YAML-Frontmatter:

```yaml
---
snippet: <rolle>-syntax          # Eindeutiger Bezeichner
version: "1.0.0"                 # Semver — erhöhen bei inhaltlichen Änderungen
language: "TypeScript"           # Programmiersprache
runtime: "Bun"                   # Runtime / Test-Framework
---
```

### Verfügbare Snippets

| Datei | Rolle | Sprache / Runtime | Version |
|-------|-------|-------------------|---------|
| `snippets/tester/bun-typescript.md` | tester | TypeScript / Bun | 1.0.0 |
| `snippets/tester/pytest-python.md` | tester | Python / pytest | 1.0.0 |
| `snippets/developer/bun-typescript.md` | developer | TypeScript / Bun | 1.0.0 |
| `snippets/developer/pytest-python.md` | developer | Python / pytest | 1.0.0 |

### Snippet hinzufügen

1. Neue Datei in `snippets/<rolle>/` anlegen (mit Frontmatter)
2. Variable `<ROLLE>_SNIPPETS_PATH` in `agent-meta.config.json` des Projekts setzen
3. `sync.py` kopiert die Datei automatisch nach `.claude/snippets/`
4. Agent-Template enthält Read-Instruktion: `Lies .claude/snippets/{{<ROLLE>_SNIPPETS_PATH}}`

### Versionierung

- Snippet-Version ist unabhängig von Agent- und Repo-Version
- `sync.py` loggt die Version beim COPY: `snippets/tester/bun-typescript.md@1.0.0`
- Bei inhaltlichen Änderungen: Patch oder Minor erhöhen

---

## External Skills (0-external Layer)

Domänenspezifische Agenten aus Drittrepos — hochspezialisiertes Wissen das nicht in generischen
Agenten gehört (z.B. 3D-Druck-Systeme, CAD-Workflows, spezifische Plattform-Expertise).

### Konzept

```
external/<repo>/path/to/SKILL.md    ← Quelldatei im Submodule (gepinnter Commit)
    ↓  sync.py substituiert SKILL_CONTENT in _skill-wrapper.md
.claude/agents/<role>.md            ← generierter Wrapper-Agent im Zielprojekt
.claude/skills/<skill-name>/        ← kopierte Skill-Dateien (für lazy Read-Zugriff)
```

### Konfiguration: `external-skills.config.json`

Liegt **zentral in agent-meta** (Modell A) — ein Eintrag pro Skill:

```json
{
  "submodules": {
    "my-skills-repo": {
      "repo": "https://github.com/owner/my-skills-repo",
      "local_path": "external/my-skills-repo"
    }
  },
  "skills": {
    "my-skill": {
      "enabled": true,
      "submodule": "my-skills-repo",
      "source": "path/within/repo",
      "entry": "SKILL.md",
      "role": "my-specialist",
      "name": "My Specialist",
      "description": "Kurzbeschreibung der Spezialisierung.",
      "additional_files": ["reference.md"]
    }
  }
}
```

- **`enabled: true/false`** — binäre Aktivierung ohne Eintrag zu löschen
- **`entry`** — Abstraktion über die Einstiegsdatei (egal wie sie im Fremdrepo heißt)
- **`additional_files`** — weitere Dokumente, die der Agent lazy per Read-Tool laden kann

### Skill hinzufügen

```bash
# Einmalig: Submodule registrieren + Config-Eintrag anlegen
python .agent-meta/scripts/sync.py \
  --add-skill https://github.com/owner/skill-repo \
  --skill-name my-skill \
  --source path/within/repo \
  --role my-specialist

# Danach normaler Sync generiert den Wrapper-Agenten
python .agent-meta/scripts/sync.py --config agent-meta.config.json
```

### Wrapper-Agent

`_skill-wrapper.md` ist das **einzige Template** für alle External Skills:
- Header + Scope-Hinweis werden von agent-meta beigesteuert
- `{{SKILL_CONTENT}}` wird mit dem vollständigen Inhalt der `entry`-Datei substituiert
  (Frontmatter des Skill-Dokuments wird dabei entfernt)
- `additional_files` bleiben als `.claude/skills/<skill>/` für lazy Read-Zugriff

### Versionierung

`sync.py` loggt beim Generieren den Submodule-Commit-Hash:
`0-external/my-skill@a3f9c12`

Um einen Skill auf einen neuen Stand zu bringen:
```bash
cd external/my-skills-repo && git pull
cd ../.. && git add external/my-skills-repo
git commit -m "chore: update my-skills-repo submodule"
python .agent-meta/scripts/sync.py --config agent-meta.config.json
```

---

## Standard-Entwicklungsworkflows

Definiert in `1-generic/orchestrator.md`, gelten projektübergreifend.

### Workflow A: Neues Feature
```
1. requirements  → Anforderung formulieren, REQ-ID vergeben
2. tester        → Tests ZUERST schreiben (TDD Red Phase)
3. developer     → Implementierung (TDD Green Phase)
4. tester        → Tests ausführen, Regressions prüfen
5. validator     → Code gegen REQ validieren, DoD-Check
6. documenter    → CODEBASE_OVERVIEW + Erkenntnisse updaten
7. git           → Commit + Push
```

### Workflow B: Bugfix
```
1. requirements  → Bestehende REQ-ID identifizieren
2. tester        → Reproduzierenden Test schreiben
3. developer     → Fix implementieren
4. tester        → Tests ausführen
5. validator     → Quick-Check
6. documenter    → Ggf. Doku updaten
7. git           → Commit + Push
```

### Workflow C: Validierung / Audit
```
1. validator     → Traceability-Audit (REQ → Code → Test)
2. validator     → Code-Qualitäts-Scan
3. validator     → Vollständiger Bericht
```

### Workflow D: Erkenntnisse speichern
```
1. documenter    → Tages-Erkenntnisse in docs/conclusions/ speichern
```

### Workflow E: Refactoring
```
1. requirements  → Betroffene REQ-IDs identifizieren
2. developer     → Refactoring durchführen
3. tester        → Alle betroffenen Tests ausführen
4. validator     → Sicherstellen, dass kein Verhalten sich ändert
5. documenter    → Signaturen/Flows in CODEBASE_OVERVIEW updaten
6. git           → Commit + Push
```

### Workflow F: Testsystem starten
```
1. docker        → Dev-Stack bauen + starten, Startup-Display ausgeben
```

### Workflow G: Neue Docker-Konfiguration
```
1. docker        → Anforderungen klären, Dockerfile + Compose erstellen
2. tester        → Test-Stack validieren
```

### Workflow H: Neue Idee / Vision erkunden
```
1. ideation      → Idee explorieren, Fragen stellen, Scope schärfen
2. ideation      → Übergabe an requirements (wenn Idee reif)
3. requirements  → Anforderungen formal aufnehmen, REQ-IDs vergeben
```

---

## Standard-Qualitätskriterien

### Definition of Done (DoD)

- [ ] **REQ-ID** existiert in `docs/REQUIREMENTS.md`
- [ ] **Code** implementiert die REQ vollständig
- [ ] **Test** vorhanden mit `[REQ-xxx]` im Namen
- [ ] **Tests grün**
- [ ] **Code-Konventionen** eingehalten (s. CLAUDE.md des Projekts)
- [ ] **CODEBASE_OVERVIEW.md** aktualisiert
- [ ] **REQUIREMENTS.md** konsistent
- [ ] **Commit-Message** im korrekten Format

### Commit-Format
```
<type>(REQ-xxx): <beschreibung>
```

| Type | REQ-ID Pflicht? |
|------|----------------|
| `feat`, `fix`, `test`, `refactor`, `chore` | Ja |
| `docs` | Nein |

### Sprachregeln
- `README.md` → **Englisch**
- Alle anderen Dokumente → **Deutsch**
- Code-Kommentare, Commit-Messages → **Englisch**
- Kommunikation mit dem Nutzer → **Deutsch**

---

## Unterstützte Projekte

| Repository | Plattform | CLAUDE.md |
|-----------|-----------|-----------|
| `sk_plugin` (sharkord-vid-with-friends) | Sharkord | `sk_plugin/CLAUDE.md` |
| `sk_hero_introduce` (sharkord-hero-introducer) | Sharkord | `sk_hero_introduce/sharkord-hero-introducer/CLAUDE.md` |

---

## Abhängigkeits-Karte — PFLICHTLEKTÜRE bei Änderungen

```
1-generic/docker.md
    └── 2-platform/sharkord-docker.md
            ├── sk_plugin/.claude/agents/docker.md
            └── sk_hero_introduce/.../.claude/agents/docker.md

1-generic/release.md
    └── 2-platform/sharkord-release.md
            ├── sk_plugin/.claude/agents/release.md
            └── sk_hero_introduce/.../.claude/agents/release.md

1-generic/orchestrator.md  → sk_plugin/.claude/agents/orchestrator.md
                           → sk_hero_introduce/.../.claude/agents/orchestrator.md

1-generic/developer.md     → sk_plugin/.claude/agents/developer.md
                           → sk_hero_introduce/.../.claude/agents/developer.md

(analog für tester, validator, requirements, ideation, documenter, meta-feedback, git, agent-meta-manager, feature)

0-external/_skill-wrapper.md
    └── external-skills.config.json (enabled skills)
            └── .claude/agents/<role>.md (generiert)
            └── .claude/skills/<skill-name>/ (kopiert)

CLAUDE.md ← diese Datei
    └── referenziert: agents/**, howto/**, alle unterstützten Projekte

ARCHITECTURE.md ← grafische Übersicht (Mermaid)
    └── wird bei jedem Major Release aktualisiert
```

### Regeln für Änderungen

| Wenn du änderst … | dann prüfe auch … |
|---|---|
| `1-generic/docker.md` | `2-platform/sharkord-docker.md` |
| `1-generic/release.md` | `2-platform/sharkord-release.md` |
| `1-generic/orchestrator.md` | Workflows-Abschnitt in dieser `CLAUDE.md` |
| beliebigen `1-generic/` Agenten | Version in Template erhöhen + Projekte neu syncen |
| `2-platform/sharkord-*.md` | Version in Template erhöhen + `based-on` aktuell halten + Projekte neu syncen |
| `agents/0-external/_skill-wrapper.md` | Alle aktivierten Skills neu syncen |
| `external-skills.config.json` | Projekte neu syncen |
| `ROLE_MAP` in `sync.py` | Rollen-Übersicht hier + `howto/instantiate-project.md` |
| `hint:` Feld in einem Agenten-Template | Projekte neu syncen (AGENT_HINTS wird neu generiert) |
| `howto/CLAUDE.project-template.md` | `howto/instantiate-project.md` (Checkliste) |

### Änderungs-Kategorien

**Einfaches Projektspezifikum (Kommando, Text, Liste):**
→ Variable in `agent-meta.config.json` → bestehender `{{PLATZHALTER}}`.

**Strukturiertes Projektwissen (nur dieses Projekt):**
→ `.claude/3-project/<rolle>-ext.md` im Zielprojekt schreiben.

**Plattformwissen verbessern (gilt für alle Projekte auf Plattform X):**
→ `2-platform/<plattform>-<rolle>.md` ändern → Projekte neu syncen.

**Neuen External Skill einbinden:**
→ `--add-skill` ausführen → `external-skills.config.json` prüfen → Projekte neu syncen.

**Neue Agenten-Rolle hinzufügen:**
→ `1-generic/<rolle>.md` + `ROLE_MAP` in `sync.py` + Tabellen in dieser `CLAUDE.md` + `howto/instantiate-project.md` + `howto/CLAUDE.project-template.md`.

---

## Agent-Versionierung

Jeder Agent-Template-Datei trägt eine eigene `version:` im Frontmatter.
Plattform-Agenten dokumentieren zusätzlich ihre Generic-Basis via `based-on:`.
Generierte Dateien erhalten automatisch `generated-from:` (gesetzt von `sync.py`).

### Frontmatter-Übersicht

| Feld | 1-generic | 2-platform | generiert in `.claude/agents/` |
|------|-----------|------------|-------------------------------|
| `version` | ✅ manuell pflegen | ✅ manuell pflegen | erhalten aus Template |
| `hint` | ✅ manuell pflegen | ✅ manuell pflegen | erhalten aus Template — erscheint in `AGENT_HINTS` in `CLAUDE.md` |
| `based-on` | — | ✅ `<generic>@<version>` | erhalten aus Template |
| `generated-from` | — | — | ✅ automatisch von sync.py |

### Wann Version erhöhen?

| Änderungstyp | Version |
|---|---|
| Umbenannte Variable, geändertes Verhalten, neue Pflichtsektion | **Major** (`X.0.0`) |
| Neue optionale Sektion, erweiterter Scope | **Minor** (`x.Y.0`) |
| Textverbesserung, Klarstellung | **Patch** (`x.y.Z`) |

Agenten-Versionen sind **unabhängig** von der Repository-Version in `VERSION`.
Nur geänderte Agenten bekommen eine neue Versionsnummer.

Wenn eine `1-generic`-Datei versioniert wird und ein `2-platform`-Agent darauf basiert:
→ `based-on` im Plattform-Agenten auf neue Generic-Version aktualisieren.

Siehe [howto/agent-versioning.md](howto/agent-versioning.md) für Details.

---

## Neue Projekte hinzufügen

Siehe [howto/instantiate-project.md](howto/instantiate-project.md).

## Upgrade auf neue Version

Siehe [howto/upgrade-guide.md](howto/upgrade-guide.md).

---

## Release-Prozess (agent-meta selbst)

Releases folgen [Semantic Versioning](https://semver.org/):
- **Patch** (`x.y.Z`) — Bugfixes, Doku, kleine Verbesserungen ohne Breaking Changes
- **Minor** (`x.Y.0`) — Neue Features, neue Agenten-Rollen, neue Platzhalter (rückwärtskompatibel)
- **Major** (`X.0.0`) — Breaking Changes (Umbenennungen, entfernte Variablen, geändertes Verhalten)

### Schritt-für-Schritt

```
1. Agenten-Versionen prüfen und erhöhen:
   - Welche Agent-Dateien wurden inhaltlich geändert?
   - Für jede geänderte Datei: version: im Frontmatter erhöhen (Patch/Minor/Major)
   - Bei 2-platform Agenten: based-on prüfen — zeigt es noch auf die richtige
     Generic-Version? Ggf. aktualisieren.
   - Bei Unsicherheit: Nutzer fragen welche Agenten-Version gesetzt werden soll

2. Änderungen committen (alle Agenten, Scripts, Doku)

3. CHANGELOG.md aktualisieren:
   - Neue Version [x.y.z] — <Datum> oben einfügen
   - Breaking Changes, Added, Changed, Removed dokumentieren
   - Geänderte Agenten-Versionen im "Changed"-Abschnitt nennen

4. VERSION aktualisieren:
   - Inhalt auf neue Versionsnummer setzen (z.B. 0.10.2)

5. README.md aktualisieren:
   - "Current version:" Badge/Zeile auf neue Version setzen
   - Quick-Start-Beispiel (`git checkout v<x.y.z>`) auf neue Version setzen

6. Bei MAJOR Release: ARCHITECTURE.md aktualisieren:
   - Version in der Überschrift anpassen
   - Neue Agenten-Rollen, Schichten oder Submodule in die Diagramme einpflegen
   - Bei Minor/Patch nur wenn sich Architektur strukturell ändert

7. Commit: git add VERSION CHANGELOG.md README.md [ARCHITECTURE.md]
           git commit -m "chore: bump version to x.y.z"

8. Tag setzen und pushen:
   git tag vx.y.z
   git push origin main
   git push origin vx.y.z
```

### Wichtig

- **Agenten-Versionen zuerst** — vor dem Release-Commit prüfen, ob alle geänderten
  Agent-Dateien eine aktualisierte `version:` im Frontmatter haben
- Bei Unsicherheit über Agenten-Version oder Release-Tag: **Nutzer fragen**
- README.md muss **vor dem Tag-Commit** die neue Version zeigen
- CHANGELOG.md muss vollständig sein **bevor** der Tag gesetzt wird
- Der Tag zeigt immer auf den Version-Bump-Commit — nie auf einen vorherigen Commit
