---
type: "Guide"
title: "Agent Memory — Persistentes Agenten-Gedächtnis"
description: "Claude Code unterstützt das memory:-Feld im Agenten-Frontmatter. Wenn gesetzt, bekommt der Agent ein persistentes Verzeichnis das über Sessions hinweg erhalten bleibt."
tags: [guide, feature]
timestamp: "2026-07-27"
resource: "../../sources/docs/guides/features/agent-memory.md"
migrated_from: "docs/guides/features/agent-memory.md"
---
# Agent Memory — Persistentes Agenten-Gedächtnis

> Dieses Dokument beschreibt das Memory-System für Sub-Agenten in Claude Code und wie
> agent-meta es konfiguriert und injiziert.
>
> **Stand:** v0.34.0

---

## Was ist Agent Memory?

Claude Code unterstützt das `memory:`-Feld im Agenten-Frontmatter. Wenn gesetzt, bekommt
der Agent ein **persistentes Verzeichnis das über Sessions hinweg erhalten bleibt**.

Der Agent nutzt dieses Verzeichnis um Wissen aufzubauen:
- Codebase-Patterns die er wiederholt beobachtet
- Erkenntnisse aus vergangenen Audit-Läufen
- Projektspezifische Konventionen die er gelernt hat
- Bekannte Stolperfallen und wiederkehrende Probleme
- Session-Zusammenfassungen und Architektur-Entscheidungen

**Wo wird es gespeichert?**

```
.claude/agent-memory/<agent-name>/     ← scope: project (in git)
  MEMORY.md                            ← Index-Datei (erste 200 Zeilen werden geladen)
  <thema>.md                           ← Detail-Dateien (auf Anfrage laden)

.claude/agent-memory-local/<name>/    ← scope: local (gitignored)
~/.claude/agent-memory/<name>/        ← scope: user (maschinenlokal)
```

---

## Wie funktioniert es technisch?

### Session-Start

Beim Start einer Session mit einem Memory-fähigen Agenten:
1. Claude Code lädt die **ersten 200 Zeilen oder 25 KB** von `MEMORY.md` automatisch in den Kontext
2. Der Agent kann Detail-Dateien via `Read`-Tool nachladen
3. `Read`, `Write` und `Edit` werden dem Agenten **automatisch zugeschaltet** — auch wenn sie nicht in `tools:` stehen

### Session-Ende

Am Ende empfiehlt es sich, den Agenten explizit anzuweisen sein Gedächtnis zu aktualisieren:

```markdown
## Memory-Pflege

Nach Abschluss deiner Aufgabe: Lies dein Gedächtnis unter
`.claude/agent-memory/<agent-name>/MEMORY.md` und aktualisiere es mit neuen Erkenntnissen.
Halte MEMORY.md unter 150 Zeilen — lagere Details in separate Themen-Dateien aus.
```

---

## Die drei Scopes im Vergleich

| Scope | Speicherort | Git-Status | Wann verwenden |
|-------|------------|------------|----------------|
| `project` | `.claude/agent-memory/<name>/` | ✅ committed | Projekt-Wissen das das ganze Team teilen soll. Dokumenter-Erkenntnisse, REQ-Muster, Architektur-Entscheidungen. |
| `local` | `.claude/agent-memory-local/<name>/` | ❌ gitignored | Projekt-Wissen das nur lokal relevant ist. Scout-History, persönliche Notizen, WIP-Erkenntnisse. |
| `user` | `~/.claude/agent-memory/<name>/` | ❌ nur lokal | Wissen das projektübergreifend gilt. Allgemeine Code-Patterns, persönliche Präferenzen. |

**Empfehlung:** `project` ist der sinnvolle Default für die meisten Agenten in einem Team-Kontext.
`local` für Agenten die interne Scouting-Ergebnisse sammeln (z.B. `agent-meta-scout`).

---

## Konfiguration in agent-meta

### Meta-Defaults (`config/role-defaults.yaml`)

Der Meta-Maintainer definiert empfohlene Memory-Scopes in `config/role-defaults.yaml`:

```yaml
roles:
  requirements:
    memory: project
    # ...
  documenter:
    memory: project
    # ...
  agent-meta-scout:
    memory: local
    # ...
```

Leerer String `""` = kein `memory:`-Feld im generierten Agenten.

### Projekt-Overrides (`.meta-config/project.yaml`)

Projekte können einzelne Rollen überschreiben:

```yaml
memory-overrides:
  documenter: local
  developer: project
```

### Precedence

```
memory-overrides in .meta-config/project.yaml   (höchste Priorität)
        ↓
config/role-defaults.yaml memory-Default
        ↓
kein memory:-Feld (Agent hat kein Gedächtnis)
```

### Was sync.py macht

`sync.py` injiziert `memory:` direkt nach dem `model:`-Feld (oder nach `name:` wenn kein Modell):

```yaml
# Generiertes .claude/agents/documenter.md
---
name: documenter
model: claude-sonnet-4-6
memory: project        ← von sync.py injiziert
version: "2.1.0"
description: "..."
generated-from: "1-generic/documenter.md@2.1.0"
---
```

Im `sync.log` erscheint:
```
[INFO]   .claude/agents/documenter.md  (memory: project (from meta default))
[INFO]   .claude/agents/agent-meta-scout.md   (memory: local (from meta default))
[INFO]   .claude/agents/developer.md   (memory: project (from project override))
```

---

## Aktuelle Meta-Defaults (Stand v0.34.0)

| Rolle | Scope | Was akkumuliert wird |
|-------|-------|---------------------|
| `requirements` | `project` | REQ-Kategorien, bekannte Anforderungs-Muster, Stakeholder-Präferenzen |
| `documenter` | `project` | Architektur-Entscheidungen, Doku-Konventionen, Session-Erkenntnisse |
| `security-auditor` | `project` | Findings aus vorherigen Audits, bekannte Risikobereiche |
| `agent-meta-scout` | `local` | Bewertete Repos, entdeckte Kandidaten (Scout-History ist persönlich) |
| `openscad-developer` | `local` | OpenSCAD-Parameter-Sets, Render-Einstellungen |
| alle anderen | *(leer)* | Kein persistentes Gedächtnis |

---

## Memory-Datei-Struktur empfehlen

Ein gut gepflegtes `MEMORY.md` für den `documenter`:

```markdown
# Documenter Memory — <Projektname>

## Architektur-Entscheidungen
- 2026-05-07: Layer-Modell eingeführt (1-generic → 2-platform → 3-project)
- 2026-05-01: Opencode-Provider hinzugefügt

## Doku-Konventionen
- README.md: deutsche Sprache, englische Code-Kommentare
- CHANGELOG.md: Conventional Commits, deutsche Überschriften

## Bekannte Stolperfallen
- `sync.py` darf nie direkt auf main ausgeführt werden (Branch-Guard)
- `.claude/agents/` ist generierter Output — nie manuell bearbeiten

## Letzte Session-Erkenntnisse
- 2026-05-07: Speech-Mode `submissive` hinzugefügt, Schema + Doku aktualisiert
```

**Regeln für gutes Memory:**
- Index-Datei unter 150 Zeilen halten (200 Zeilen werden geladen, Puffer lassen)
- Details in separate Dateien auslagern: `architecture-decisions.md`, `known-issues.md`
- Timestamps bei Einträgen — Memory veraltet sonst unbemerkt
- Nur nicht-offensichtliche Dinge speichern — was aus dem Code ersichtlich ist, gehört nicht ins Memory
- Nach größeren Refactorings: Memory auf veraltete Einträge prüfen

---

## .gitignore-Einträge

`sync.py` sorgt dafür dass lokale Memory-Verzeichnisse in `.gitignore` eingetragen sind:

```
# agent-meta managed
.claude/agent-memory-local/
```

`project`-Memory (`.claude/agent-memory/`) wird **bewusst nicht** gitignored —
es soll committed und geteilt werden.

---

## Deaktivieren für einzelne Rollen

Im Projekt einfach `""` in `memory-overrides` setzen:

```yaml
memory-overrides:
  documenter: ""
```

Damit wird kein `memory:`-Feld injiziert — der Documenter läuft ohne Gedächtnis.

---

## Troubleshooting

### Memory wird nicht geladen
- Prüfen ob `memory:` im generierten Agenten-Frontmatter steht
- Prüfen ob `.claude/agent-memory/<name>/MEMORY.md` existiert
- Claude Code Neustart erforderlich nach Memory-Datei-Änderungen

### Memory ist zu groß
- Index-Datei auf 150 Zeilen reduzieren
- Details in separate Dateien auslagern
- Veraltete Einträge entfernen

### Falsche Scope-Konfiguration
- `sync.log` prüfen — dort steht die Quelle des Memory-Werts
- `memory-overrides` in `.meta-config/project.yaml` haben höchste Priorität

---

## Verwandte Dokumente

- [howto/features/agent-composition.md](agent-composition.md) — extends/patches System
- [howto/features/external-skills.md](external-skills.md) — External Skills einbinden
- [CLAUDE.md](../../../CLAUDE.md) — Vollständige Konfigurations-Referenz (`model-overrides`, `memory-overrides`)
- [config/role-defaults.yaml](../../../config/role-defaults.yaml) — Aktuelle Memory-Defaults pro Rolle