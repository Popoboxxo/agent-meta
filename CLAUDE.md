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

## Drei-Schichten-Modell

```
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
1-generic  ←  überschrieben durch  →  2-platform  ←  überschrieben durch  →  3-project/<rolle>.md
```

**Extension (additiv, kein Override):**
```
generierter Agent  +  .claude/3-project/<rolle>-ext.md  =  voller Agent-Kontext
```

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

    2-platform/         ← plattformspezifisch (überschreibt 1-generic)
      sharkord-docker.md
      sharkord-release.md

    3-project/          ← projektspezifisch (im Meta-Repo als Vorlage, selten)
      developer-ext.md  ← Beispiel: Extension-Vorlage für developer
                           Overrides: <rolle>.md (ersetzt komplett)
                           Extensions: <rolle>-ext.md (additiv geladen)

  howto/
    instantiate-project.md  ← Schritt-für-Schritt Einrichtung
    upgrade-guide.md         ← Upgrade auf neue agent-meta Version
    CLAUDE.project-template.md
    sync-concept.md
    template-gap-analysis.md

  scripts/
    sync.py              ← Agent-Generator
```

---

## Agenten im Zielprojekt

### Namensgebung

Alle Agenten heißen **generisch** — kein Projekt-Prefix:

| Rolle | Datei in `.claude/agents/` | Quelle |
|-------|---------------------------|--------|
| Orchestrator | `orchestrator.md` | 1-generic |
| Developer | `developer.md` | 1-generic |
| Tester | `tester.md` | 1-generic |
| Validator | `validator.md` | 1-generic |
| Requirements | `requirements.md` | 1-generic |
| Documenter | `documenter.md` | 1-generic |
| Release | `release.md` | 1-generic oder 2-platform |
| Docker | `docker.md` | 1-generic oder 2-platform |

### Update-Verhalten bei sync

| Datei | Wird bei sync überschrieben? | Bekommt generische Updates? |
|-------|-----------------------------|-----------------------------|
| `.claude/agents/*.md` (generiert) | ✅ Ja, immer | ✅ Ja |
| `.claude/3-project/*-ext.md` (Extension) | ❌ Nein, nur einmalig kopiert | ❌ Manuell pflegen |
| `.claude/3-project/*.md` (Override, falls vorhanden) | ❌ Wird nicht generiert — liegt im Projekt | ❌ Manuell pflegen |

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
- sync.py kopiert eine Vorlage einmalig aus `3-project/<rolle>-ext.md` im Meta-Repo — danach nie wieder überschrieben
- Enthält: SDK-spezifisches Wissen, projektspezifische Don'ts, manuelle Workflows, domänenspezifische Patterns

**Extension-Hook** (in jedem generierten Agenten):
```markdown
Falls die Datei `.claude/3-project/<rolle>-ext.md` existiert:
Lies sie jetzt sofort mit dem Read-Tool und wende alle Regeln vollständig an.
```

### Override: `.claude/3-project/<rolle>.md`

- Liegt direkt im Zielprojekt (nicht von sync.py berührt)
- Wenn vorhanden im Meta-Repo unter `3-project/<rolle>.md`: wird wie 1-generic/2-platform behandelt, aber mit höchster Priorität
- Bekommt **keine automatischen Updates** — manuelle Pflege nötig
- Nur wenn Extension nicht reicht

---

## Variablen und Platzhalter

Alle `{{PLATZHALTER}}` werden via `agent-meta.config.json` befüllt.
Auto-injiziert (nicht in config nötig): `AGENT_META_VERSION`, `AGENT_META_DATE`, `AGENT_TABLE`.

| Platzhalter | Agent | Zweck |
|-------------|-------|-------|
| `{{PROJECT_CONTEXT}}` | alle | Projektbeschreibung aus CLAUDE.md |
| `{{CODE_CONVENTIONS}}` | developer | Sprachspezifische Regeln |
| `{{ARCHITECTURE}}` | developer | Verzeichnisstruktur, Entry-Points |
| `{{DEV_COMMANDS}}` | developer, orchestrator | Build/Run-Kommandos |
| `{{EXTRA_DONTS}}` | developer | Zusätzliche Verbote (kurze Liste) |
| `{{CODE_QUALITY_RULES}}` | validator | Linting-Regeln, Quality-Gates |
| `{{REQ_CATEGORIES}}` | requirements | Anforderungs-Kategorien |
| `{{TEST_COMMANDS}}` | tester | Test-Runner-Kommandos |
| `{{BUILD_COMMANDS}}` | release | Build-Schritte |

---

## Agenten-Rollen

| Rolle | Generic | Plattform (Sharkord) | Zweck |
|-------|---------|---------------------|-------|
| `orchestrator` | `1-generic/orchestrator.md` | — | Koordination |
| `developer` | `1-generic/developer.md` | — | REQ-driven Implementierung |
| `tester` | `1-generic/tester.md` | — | TDD, Test-Suite, Coverage |
| `validator` | `1-generic/validator.md` | — | DoD-Check, Traceability |
| `requirements` | `1-generic/requirements.md` | — | REQ-Aufnahme, REQUIREMENTS.md |
| `documenter` | `1-generic/documenter.md` | — | Doku-Pflege, Erkenntnisse |
| `release` | `1-generic/release.md` | `2-platform/sharkord-release.md` | Versioning, GitHub Release |
| `docker` | `1-generic/docker.md` | `2-platform/sharkord-docker.md` | Dev-Stack, Binaries |

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
```

### Workflow B: Bugfix
```
1. requirements  → Bestehende REQ-ID identifizieren
2. tester        → Reproduzierenden Test schreiben
3. developer     → Fix implementieren
4. tester        → Tests ausführen
5. validator     → Quick-Check
6. documenter    → Ggf. Doku updaten
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

(analog für tester, validator, requirements, documenter)

CLAUDE.md ← diese Datei
    └── referenziert: agents/**, howto/**, alle unterstützten Projekte
```

### Regeln für Änderungen

| Wenn du änderst … | dann prüfe auch … |
|---|---|
| `1-generic/docker.md` | `2-platform/sharkord-docker.md` |
| `1-generic/release.md` | `2-platform/sharkord-release.md` |
| `1-generic/orchestrator.md` | Workflows-Abschnitt in dieser `CLAUDE.md` |
| beliebigen `1-generic/` Agenten | Projekte neu syncen |
| `2-platform/sharkord-*.md` | Projekte neu syncen |
| `ROLE_MAP` in `sync.py` | Rollen-Übersicht hier + `howto/instantiate-project.md` |
| `howto/CLAUDE.project-template.md` | `howto/instantiate-project.md` (Checkliste) |

### Änderungs-Kategorien

**Einfaches Projektspezifikum (Kommando, Text, Liste):**
→ Variable in `agent-meta.config.json` → bestehender `{{PLATZHALTER}}`.

**Strukturiertes Projektwissen (nur dieses Projekt):**
→ `.claude/3-project/<rolle>-ext.md` im Zielprojekt schreiben.

**Plattformwissen verbessern (gilt für alle Projekte auf Plattform X):**
→ `2-platform/<plattform>-<rolle>.md` ändern → Projekte neu syncen.

**Neue Agenten-Rolle hinzufügen:**
→ `1-generic/<rolle>.md` + `ROLE_MAP` in `sync.py` + Tabellen in dieser `CLAUDE.md` + `howto/instantiate-project.md` + `howto/CLAUDE.project-template.md`.

---

## Neue Projekte hinzufügen

Siehe [howto/instantiate-project.md](howto/instantiate-project.md).

## Upgrade auf neue Version

Siehe [howto/upgrade-guide.md](howto/upgrade-guide.md).
