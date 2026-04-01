# agent-meta — Meta-Repository für Agenten-Standards

## Zweck

Dieses Repository ist das **zentrale Meta-Repository** für die Standardisierung und
Wiederverwendung von Claude-Agenten-Rollen über alle Sharkord-Projekte hinweg.

---

## Das Konzept: Templates → Plattform-Layer → Instanziierung

### Problem

In `sk_plugin` und `sk_hero_introduce` existieren nahezu identische Agenten-Rollen
(Developer, Tester, Validator, Requirements, Documenter, Orchestrator). Der einzige
Unterschied ist der **Projektkontext-Block** — Projektname, Tech-Stack, Architektur.

Das führt zu:
- doppeltem Pflegeaufwand bei Verbesserungen
- Inkonsistenzen zwischen Projekten
- Schwierigkeiten, neue Best Practices einzuführen

### Lösung: Drei-Schichten-Modell

```
Schicht 1: template-*.md          (vollständig generisch — plattformunabhängig)
Schicht 2: <plattform>-*.md       (plattformspezifisch — z.B. sharkord-docker.md)
Schicht 3: <prefix>-*.md          (Projekt-Instanz mit konkreten Werten)
```

Nicht alle Rollen brauchen alle drei Schichten. Für die meisten Rollen reicht
Schicht 1 → Schicht 3 direkt (nur Docker hat aktuell einen Plattform-Layer).

```
agent-meta/
  agents/
    1-generic/                        ← Schicht 1: plattformunabhängig
      template-orchestrator.md
      template-developer.md
      template-tester.md
      template-validator.md
      template-requirements.md
      template-documenter.md
      template-release.md
      template-docker.md
    2-platform/                       ← Schicht 2: plattformspezifisch
      sharkord-docker.md
    3-project/                        ← Schicht 3: Projekt-Instanzen (leer — leben in den Repos)

  howto/
    instantiate-project.md            ← Schritt-für-Schritt Anleitung
    CLAUDE.project-template.md        ← Vorlage für neue Projekte
    template-gap-analysis.md          ← Vergleich Templates vs. Projekte
```

---

## Wie ein Projekt die Agenten instanziiert

### 1. Projekt-CLAUDE.md anlegen

Jedes Projekt hat eine `CLAUDE.md` (im Repo-Root), die:
1. Den **Projektkontext** definiert (Name, Ziel, Tech-Stack, Architektur)
2. Die **Agenten-Rollen** mit ihrem Projektnamen benennt
3. Auf die **Templates** in `agent-meta` verweist

### 2. Projekt-Agenten anlegen (`.claude/agents/`)

Jeder Agenten-File eines Projekts besteht aus:
```markdown
---
name: <prefix>-developer
description: "..."
tools: [...]
---

## Projektkontext
<!-- PROJEKTSPEZIFISCH — hier weicht jedes Projekt ab -->
[Projektname, Tech-Stack, Architektur-Zusammenfassung, Besonderheiten]

---

<!-- AB HIER: Inhalt aus agent-meta/agents/template-developer.md -->
[Generische Rolle, Workflows, Konventionen, Don'ts]
```

Die **generischen Teile** (Workflows, Konventionen, Don'ts) kommen aus den Templates
in diesem Repository. Beim Aktualisieren eines Templates werden alle Projekte
durch Übernahme der Änderungen aktuell gehalten.

### 3. Rollen-Naming-Schema

| Schicht | Datei | Namensschema Instanz | Beispiele |
|---------|-------|---------------------|---------|
| 1 — generisch | `agents/1-generic/template-orchestrator.md` | `<project-short>` | `vid-with-friends`, `hero-introducer` |
| 1 — generisch | `agents/1-generic/template-developer.md` | `<prefix>-developer` | `vwf-developer`, `hi-developer` |
| 1 — generisch | `agents/1-generic/template-tester.md` | `<prefix>-tester` | `vwf-tester`, `hi-tester` |
| 1 — generisch | `agents/1-generic/template-validator.md` | `<prefix>-validator` | `vwf-validator`, `hi-validator` |
| 1 — generisch | `agents/1-generic/template-requirements.md` | `<prefix>-requirements` | `vwf-requirements`, `hi-requirements` |
| 1 — generisch | `agents/1-generic/template-documenter.md` | `<prefix>-documenter` | `vwf-documenter`, `hi-documenter` |
| 1 — generisch | `agents/1-generic/template-release.md` | _(Basis für Plattform-Layer)_ | — |
| 2 — Plattform | `agents/2-platform/sharkord-release.md` | `<prefix>-release` | `vwf-release`, `hi-release` |
| 1 — generisch | `agents/1-generic/template-docker.md` | _(Basis, nicht direkt instanziiert)_ | — |
| 2 — Plattform | `agents/2-platform/sharkord-docker.md` | `<prefix>-docker` | `vwf-docker`, `hi-docker` |
| 3 — Projekt | _(lebt im jeweiligen Repo)_ | s. Namensschema oben | `sk_plugin/.claude/agents/` |

---

## Standard-Entwicklungsworkflows (projektübergreifend)

Diese Workflows gelten für **alle** Sharkord-Projekte und sind in den Templates definiert.

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

---

## Standard-Qualitätskriterien (projektübergreifend)

### Definition of Done (DoD)

Eine Aufgabe ist erst abgeschlossen, wenn:
- [ ] **REQ-ID** existiert in `docs/REQUIREMENTS.md`
- [ ] **Code** implementiert die REQ vollständig
- [ ] **Test** vorhanden mit `[REQ-xxx]` im Namen
- [ ] **Tests grün** — Test-Runner bestanden
- [ ] **Code-Konventionen** eingehalten (projektspezifisch, s. CLAUDE.md des Projekts)
- [ ] **CODEBASE_OVERVIEW.md** aktualisiert
- [ ] **REQUIREMENTS.md** konsistent
- [ ] **Commit-Message** im korrekten Format

### Commit-Format (Standard)
```
<type>(REQ-xxx): <beschreibung>
```

| Type | Verwendung | REQ-ID Pflicht? |
|------|----------|----------------|
| `feat` | Neues Feature | Ja |
| `fix` | Bugfix | Ja |
| `test` | Tests hinzufügen/ändern | Ja |
| `refactor` | Refactoring | Ja |
| `chore` | Build, Dependencies, Config | Ja |
| `docs` | Dokumentation | Nein |

---

## Standard-Sprachregeln (projektübergreifend)

- `README.md` → **Englisch**
- Alle anderen Dokumente → **Deutsch**
- Code-Kommentare → **Englisch**
- Commit-Messages → **Englisch**
- Kommunikation mit dem Nutzer → **Deutsch**

---

## Unterstützte Projekte

| Repository | Präfix | CLAUDE.md |
|-----------|--------|-----------|
| `sk_plugin` (sharkord-vid-with-friends) | `vwf` | `sk_plugin/CLAUDE.md` |
| `sk_hero_introduce` (sharkord-hero-introducer) | `hi` | `sk_hero_introduce/sharkord-hero-introducer/CLAUDE.md` |

---

## Abhängigkeiten zwischen Dateien — PFLICHTLEKTÜRE bei Änderungen

> **WICHTIG:** Bevor du eine Datei in `agents/` oder `howto/` änderst, prüfe diese
> Tabelle. Jede Änderung kann mehrere abhängige Dateien betreffen.

### Abhängigkeits-Karte

```
agents/1-generic/template-docker.md
    └── agents/2-platform/sharkord-docker.md       (erbt Struktur + Prinzipien)
            ├── sk_plugin/.claude/agents/vwf-docker.md
            └── sk_hero_introduce/.../.claude/agents/hi-docker.md

agents/1-generic/template-orchestrator.md
    ├── sk_plugin/.claude/agents/vid-with-friends.md
    └── sk_hero_introduce/.../.claude/agents/hero-introducer.md

agents/1-generic/template-developer.md
    ├── sk_plugin/.claude/agents/vwf-developer.md
    └── sk_hero_introduce/.../.claude/agents/hi-developer.md

agents/1-generic/template-tester.md
    ├── sk_plugin/.claude/agents/vwf-tester.md
    └── sk_hero_introduce/.../.claude/agents/hi-tester.md

agents/1-generic/template-validator.md
    ├── sk_plugin/.claude/agents/vwf-validator.md
    └── sk_hero_introduce/.../.claude/agents/hi-validator.md

agents/1-generic/template-requirements.md
    ├── sk_plugin/.claude/agents/vwf-requirements.md
    └── sk_hero_introduce/.../.claude/agents/hi-requirements.md

agents/1-generic/template-documenter.md
    ├── sk_plugin/.claude/agents/vwf-documenter.md
    └── sk_hero_introduce/.../.claude/agents/hi-documenter.md

agents/1-generic/template-release.md
    └── agents/2-platform/sharkord-release.md      (konsolidiert vwf + hi Erfahrungen)
            ├── sk_plugin/.claude/agents/vwf-release.md
            └── sk_hero_introduce/.../.claude/agents/hi-release.md

howto/instantiate-project.md
    └── referenziert alle 1-generic/ und 2-platform/ Dateien

howto/CLAUDE.project-template.md
    └── referenziert alle 1-generic/ Dateien (Rollen-Tabelle)

CLAUDE.md  ← diese Datei
    └── referenziert: agents/**, howto/**, alle unterstützten Projekte
```

### Regeln für Änderungen

| Wenn du änderst … | dann prüfe auch … |
|---|---|
| `agents/1-generic/template-docker.md` | `agents/2-platform/sharkord-docker.md` — baut darauf auf |
| `agents/2-platform/sharkord-docker.md` | alle `*-docker.md` Instanzen in den Projekt-Repos |
| ein `agents/1-generic/template-*.md` (außer docker) | alle zugehörigen Instanzen in `sk_plugin` + `sk_hero_introduce` |
| `howto/instantiate-project.md` | `CLAUDE.md` (Rollen-Naming-Schema-Tabelle muss konsistent bleiben) |
| `howto/CLAUDE.project-template.md` | `howto/instantiate-project.md` (Checkliste) |
| Rollen-Naming-Schema | `CLAUDE.md`, `howto/instantiate-project.md`, `howto/CLAUDE.project-template.md` |
| Workflows (A–G) | `agents/1-generic/template-orchestrator.md` und `CLAUDE.md` |
| einen neuen Plattform-Layer in `agents/2-platform/` | `CLAUDE.md` (Drei-Schichten-Tabelle + Abhängigkeits-Karte hier) |

### Änderungs-Kategorien

**Generische Logik verbessern** (Workflows, Konventionen, Don'ts):
→ In `agents/1-generic/template-*.md` ändern, dann in alle Instanzen propagieren.

**Sharkord-Plattformwissen aktualisieren** (neue Image-Version, Pfadänderungen):
→ In `agents/2-platform/sharkord-docker.md` ändern, dann in `vwf-docker.md` + `hi-docker.md` propagieren.

**Projektspezifischen Kontext ändern** (Tech-Stack, Architektur, Commands):
→ Nur in der jeweiligen Instanz (`vwf-*` oder `hi-*`) im Projekt-Repo — kein Template betroffen.

**Neuen Platzhalter `{{XYZ}}` hinzufügen**:
→ `agents/1-generic/` oder `agents/2-platform/` + `howto/instantiate-project.md` (Platzhalter-Tabelle) + `howto/CLAUDE.project-template.md`.

**Neue Agenten-Rolle hinzufügen**:
→ Neues `agents/1-generic/template-*.md` + Eintrag in Rollen-Naming-Tabelle in `CLAUDE.md` + Eintrag in `howto/instantiate-project.md` + Eintrag in `howto/CLAUDE.project-template.md` + Abhängigkeits-Karte oben ergänzen.

**Neuen Plattform-Layer hinzufügen** (z.B. für eine andere Plattform als Sharkord):
→ Neue Datei in `agents/2-platform/` + Eintrag in Abhängigkeits-Karte + Eintrag in Rollen-Naming-Tabelle in `CLAUDE.md`.

---

## Neue Projekte hinzufügen

Siehe [howto/instantiate-project.md](howto/instantiate-project.md) für die
vollständige Schritt-für-Schritt Anleitung.
