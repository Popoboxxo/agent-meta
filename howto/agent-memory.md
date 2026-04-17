# Agent Memory — Persistentes Agenten-Gedächtnis

> Dieses Dokument beschreibt das Memory-System für Sub-Agenten in Claude Code und wie
> agent-meta es konfiguriert und injiziert.

---

## Was ist Agent Memory?

Claude Code unterstützt das `memory:`-Feld im Agenten-Frontmatter. Wenn gesetzt, bekommt
der Agent ein **persistentes Verzeichnis das über Sessions hinweg erhalten bleibt**.

Der Agent nutzt dieses Verzeichnis um Wissen aufzubauen:
- Codebase-Patterns die er wiederholt beobachtet
- Erkenntnisse aus vergangenen Audit-Läufen
- Projektspezifische Konventionen die er gelernt hat
- Bekannte Stolperfallen und wiederkehrende Probleme

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
`.claude/agent-memory/validator/MEMORY.md` und aktualisiere es mit neuen Erkenntnissen.
Halte MEMORY.md unter 150 Zeilen — lagere Details in separate Themen-Dateien aus.
```

---

## Die drei Scopes im Vergleich

| Scope | Speicherort | Git-Status | Wann verwenden |
|-------|------------|------------|----------------|
| `project` | `.claude/agent-memory/<name>/` | ✅ committed | Projekt-Wissen das das ganze Team teilen soll. Validator-Findings, REQ-Muster, Architektur-Entscheidungen. |
| `local` | `.claude/agent-memory-local/<name>/` | ❌ gitignored | Projekt-Wissen das nur lokal relevant ist. Scout-History, persönliche Notizen, WIP-Erkenntnisse. |
| `user` | `~/.claude/agent-memory/<name>/` | ❌ nur lokal | Wissen das projektübergreifend gilt. Allgemeine Code-Patterns, persönliche Präferenzen. |

**Empfehlung:** `project` ist der sinnvolle Default für die meisten Agenten in einem Team-Kontext.
`local` für Agenten die interne Scouting-Ergebnisse sammeln (z.B. `agent-meta-scout`).

---

## Konfiguration in agent-meta

### Meta-Defaults (`roles.config.yaml`)

Der Meta-Maintainer definiert empfohlene Memory-Scopes in `roles.config.yaml`:

```json
{
  "roles": {
    "validator": {
      "memory": "project",
      "model": "sonnet",
      "description": "..."
    },
    "git": {
      "memory": "",
      "model": "haiku",
      "description": "..."
    }
  }
}
```

Leerer String `""` = kein `memory:`-Feld im generierten Agenten.

### Projekt-Overrides (`agent-meta.config.yaml`)

Projekte können einzelne Rollen überschreiben:

```json
{
  "memory-overrides": {
    "validator": "local",
    "developer": "project"
  }
}
```

### Precedence

```
memory-overrides in agent-meta.config.yaml   (höchste Priorität)
        ↓
roles.config.yaml memory-Default
        ↓
kein memory:-Feld (Agent hat kein Gedächtnis)
```

### Was sync.py macht

`sync.py` injiziert `memory:` direkt nach dem `model:`-Feld (oder nach `name:` wenn kein Modell):

```yaml
# Generiertes .claude/agents/validator.md
---
name: validator
model: sonnet
memory: project        ← von sync.py injiziert
version: "1.3.0"
description: "..."
generated-from: "1-generic/validator.md@1.3.0"
---
```

Im `sync.log` erscheint:
```
[INFO]   .claude/agents/validator.md   (memory: project (from meta default))
[INFO]   .claude/agents/documenter.md  (memory: project (from meta default))
[INFO]   .claude/agents/validator.md   (memory: local (from project override))
```

---

## Meta-Defaults (Stand v0.16.4)

| Rolle | Scope | Was akkumuliert wird |
|-------|-------|---------------------|
| `validator` | `project` | REQ-Muster, Traceability-Lücken, bekannte Code-Probleme |
| `documenter` | `project` | Architektur-Entscheidungen, Doku-Konventionen, Erkenntnisse |
| `requirements` | `project` | REQ-Kategorien, bekannte Anforderungs-Muster, Stakeholder-Präferenzen |
| `security-auditor` | `project` | Findings aus vorherigen Audits, bekannte Risikobereiche |
| `agent-meta-scout` | `local` | Bewertete Repos, entdeckte Kandidaten (nicht in git — Scout-History ist persönlich) |
| alle anderen | *(leer)* | Kein persistentes Gedächtnis |

---

## Memory-Datei-Struktur empfehlen

Ein gut gepflegtes `MEMORY.md` für den `validator`:

```markdown
# Validator Memory — <Projektname>

## Bekannte REQ-Muster
- REQ-IDs folgen Format `REQ-NNN` (dreistellig, nullpadded)
- Alle REQs in `docs/REQUIREMENTS.md`, Kategorie-Header mit `###`

## Wiederkehrende Probleme
- `src/db/` hat häufig fehlende REQ-Referenzen in Tests
- `any`-Types werden vom Linter regelmäßig bemängelt

## Traceability-Lücken (bekannt)
- REQ-042: Test existiert, aber `[REQ-042]` fehlt im Test-Namen
- REQ-018: Noch kein Test vorhanden (bewusst aufgeschoben bis v2)

## Letzte Audit-Ergebnisse
- 2026-04-06: Vollständiger Audit — 3 Lücken gefunden, 2 geschlossen
```

**Regeln für gutes Memory:**
- Index-Datei unter 150 Zeilen halten (200 Zeilen werden geladen, Puffer lassen)
- Details in separate Dateien auslagern: `traceability-gaps.md`, `known-issues.md`
- Timestamps bei Einträgen — Memory veraltet sonst unbemerkt
- Nur nicht-offensichtliche Dinge speichern — was aus dem Code ersichtlich ist, gehört nicht ins Memory

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

```json
"memory-overrides": {
  "validator": ""
}
```

Damit wird kein `memory:`-Feld injiziert — der Validator läuft ohne Gedächtnis.

---

## Verwandte Dokumente

- [howto/agent-composition.md](agent-composition.md) — extends/patches System
- [howto/external-skills.md](external-skills.md) — External Skills einbinden
- [CLAUDE.md](../CLAUDE.md) — Vollständige Konfigurations-Referenz (`model-overrides`, `memory-overrides`)
