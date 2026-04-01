# agent-meta — Meta-Repository für Agenten-Standards

## Zweck

Dieses Repository ist das **zentrale Meta-Repository** für die Standardisierung und
Wiederverwendung von Claude-Agenten-Rollen über alle Projekte hinweg.

---

## Kernprinzip

Die **`CLAUDE.md` eines Projekts ist die einzige Wahrheit.**

Sie beschreibt das Projekt vollständig (Ziel, Tech-Stack, Architektur, Konventionen)
und bestimmt, welche Agenten aktiv sind. Agenten lesen die `CLAUDE.md` und wissen
damit alles Projektspezifische — sie enthalten **keinen** eigenen Kontext-Block mehr.

---

## Drei-Schichten-Modell

```
1-generic/    Universell einsetzbar. Gilt für jedes Projekt ohne Anpassung.
              Wird direkt verwendet, solange kein Plattform-Layer existiert.

2-platform/   Plattformspezifisch. Überschreibt/erweitert den generischen Agenten
              für eine konkrete Plattform (z.B. Sharkord).
              Wird verwendet, wenn das Projekt auf dieser Plattform läuft.

3-project/    Projektspezifisch. Überschreibt alles darüber.
              Nur in Ausnahmefällen — wenn ein Projekt fundamental von
              Plattform- und Generic-Agent abweicht.
```

**Überschreibungs-Reihenfolge:**
```
generisch  ←  wird überschrieben durch  →  plattform  ←  wird überschrieben durch  →  projekt
```

Ein Agent existiert nur auf der niedrigsten Ebene, auf der er sich vom Generic unterscheidet.
Gibt es keinen Plattform- oder Projekt-Agenten, gilt der Generic-Agent unverändert.

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

    3-project/          ← projektspezifisch (überschreibt alles, selten!)
                           (Instanzen leben in den jeweiligen Repos)

  howto/
    instantiate-project.md       ← Schritt-für-Schritt Anleitung
    CLAUDE.project-template.md   ← Vorlage für Projekt-CLAUDE.md
    template-gap-analysis.md     ← Analyse: Lücken zwischen Generic und Projekten
```

---

## Die Rolle der CLAUDE.md im Projekt

Jedes Projekt hat eine `CLAUDE.md` im Repo-Root. Sie erfüllt drei Aufgaben:

### 1. Projekt vollständig beschreiben
- Name, Ziel, Plattform
- Tech-Stack (Runtime, Sprache, Key-Dependencies)
- Architektur (Verzeichnisstruktur, Entry-Points, Key-Patterns)
- Code-Konventionen (Sprachregeln, Namensgebung, Verbote)
- Anforderungs-Kategorien

### 2. Agenten-Konfiguration definieren
- Welche Agenten aktiv sind
- Welcher Plattform-Layer gilt
- Ob ein Projekt-Agenten-Override existiert (Ausnahmefall)

### 3. Als Basis für die Agenten dienen
Agenten lesen `CLAUDE.md` um den Projektkontext zu erhalten.
Sie enthalten **keinen eigenen Kontext-Block** — stattdessen verweisen sie auf CLAUDE.md.

Vorlage: [howto/CLAUDE.project-template.md](howto/CLAUDE.project-template.md)

---

## Agenten-Rollen-Übersicht

| Rolle | Generic | Plattform (Sharkord) | Zweck |
|-------|---------|---------------------|-------|
| `orchestrator` | `1-generic/orchestrator.md` | — | Koordination aller Sub-Agenten |
| `developer` | `1-generic/developer.md` | — | REQ-driven Implementierung |
| `tester` | `1-generic/tester.md` | — | TDD, Test-Suite, Coverage |
| `validator` | `1-generic/validator.md` | — | DoD-Check, Traceability, Code-Qualität |
| `requirements` | `1-generic/requirements.md` | — | REQ-Aufnahme, REQUIREMENTS.md |
| `documenter` | `1-generic/documenter.md` | — | Doku-Pflege, Erkenntnisse |
| `release` | `1-generic/release.md` | `2-platform/sharkord-release.md` | Versioning, Build, GitHub Release |
| `docker` | `1-generic/docker.md` | `2-platform/sharkord-docker.md` | Dev-Stack, Test-Stack, Binaries |

**Naming-Schema in Projekten:**

| Rolle | Name in `.claude/agents/` | Beispiele |
|-------|--------------------------|---------|
| Orchestrator | `<project-short>` | `vid-with-friends`, `hero-introducer` |
| Developer | `<prefix>-developer` | `vwf-developer`, `hi-developer` |
| Tester | `<prefix>-tester` | `vwf-tester`, `hi-tester` |
| Validator | `<prefix>-validator` | `vwf-validator`, `hi-validator` |
| Requirements | `<prefix>-requirements` | `vwf-requirements`, `hi-requirements` |
| Documenter | `<prefix>-documenter` | `vwf-documenter`, `hi-documenter` |
| Release | `<prefix>-release` | `vwf-release`, `hi-release` |
| Docker | `<prefix>-docker` | `vwf-docker`, `hi-docker` |

---

## Standard-Entwicklungsworkflows

Diese Workflows sind in `1-generic/orchestrator.md` definiert und gelten projektübergreifend.

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

| Repository | Präfix | Plattform | CLAUDE.md |
|-----------|--------|-----------|-----------|
| `sk_plugin` (sharkord-vid-with-friends) | `vwf` | Sharkord | `sk_plugin/CLAUDE.md` |
| `sk_hero_introduce` (sharkord-hero-introducer) | `hi` | Sharkord | `sk_hero_introduce/sharkord-hero-introducer/CLAUDE.md` |

---

## Abhängigkeiten — PFLICHTLEKTÜRE bei Änderungen

### Abhängigkeits-Karte

```
1-generic/docker.md
    └── 2-platform/sharkord-docker.md
            ├── sk_plugin/.claude/agents/vwf-docker.md
            └── sk_hero_introduce/.../.claude/agents/hi-docker.md

1-generic/release.md
    └── 2-platform/sharkord-release.md
            ├── sk_plugin/.claude/agents/vwf-release.md
            └── sk_hero_introduce/.../.claude/agents/hi-release.md

1-generic/orchestrator.md
    ├── sk_plugin/.claude/agents/vid-with-friends.md
    └── sk_hero_introduce/.../.claude/agents/hero-introducer.md

1-generic/developer.md   → sk_plugin/.claude/agents/vwf-developer.md
                         → sk_hero_introduce/.../.claude/agents/hi-developer.md

1-generic/tester.md      → sk_plugin/.claude/agents/vwf-tester.md
                         → sk_hero_introduce/.../.claude/agents/hi-tester.md

1-generic/validator.md   → sk_plugin/.claude/agents/vwf-validator.md
                         → sk_hero_introduce/.../.claude/agents/hi-validator.md

1-generic/requirements.md → sk_plugin/.claude/agents/vwf-requirements.md
                          → sk_hero_introduce/.../.claude/agents/hi-requirements.md

1-generic/documenter.md  → sk_plugin/.claude/agents/vwf-documenter.md
                         → sk_hero_introduce/.../.claude/agents/hi-documenter.md

CLAUDE.md ← diese Datei
    └── referenziert: agents/**, howto/**, alle unterstützten Projekte
```

### Regeln für Änderungen

| Wenn du änderst … | dann prüfe auch … |
|---|---|
| `1-generic/docker.md` | `2-platform/sharkord-docker.md` |
| `1-generic/release.md` | `2-platform/sharkord-release.md` |
| `1-generic/orchestrator.md` | Workflows-Abschnitt in dieser `CLAUDE.md` |
| einen beliebigen `1-generic/` Agenten | alle Instanzen in den Projekt-Repos |
| `2-platform/sharkord-docker.md` | `vwf-docker.md` + `hi-docker.md` in den Repos |
| `2-platform/sharkord-release.md` | `vwf-release.md` + `hi-release.md` in den Repos |
| `howto/instantiate-project.md` | Naming-Tabelle in dieser `CLAUDE.md` |
| `howto/CLAUDE.project-template.md` | `howto/instantiate-project.md` (Checkliste) |

### Änderungs-Kategorien

**Generische Logik verbessern** (Workflows, Konventionen, Don'ts):
→ In `1-generic/<rolle>.md` ändern → in alle Projekt-Instanzen propagieren.

**Plattformwissen aktualisieren** (neue Sharkord-Version, Pfadänderungen):
→ In `2-platform/sharkord-*.md` ändern → in Projekt-Instanzen propagieren.

**Neuen Plattform-Layer anlegen** (andere Plattform):
→ Neue Datei in `2-platform/` + Eintrag in Rollen-Übersicht + Abhängigkeits-Karte hier.

**Neue Agenten-Rolle hinzufügen**:
→ `1-generic/<rolle>.md` + Rollen-Übersicht in `CLAUDE.md` + `howto/instantiate-project.md` + `howto/CLAUDE.project-template.md` + Abhängigkeits-Karte.

---

## Neue Projekte hinzufügen

Siehe [howto/instantiate-project.md](howto/instantiate-project.md).
