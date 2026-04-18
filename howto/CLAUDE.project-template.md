# {{PROJECT_NAME}}

> Projektbeschreibung für Claude-Agenten. Diese Datei ist die **einzige Quelle**
> für projektspezifischen Kontext — Agenten lesen sie, statt eigenen Kontext zu haben.
>
> Generiert von agent-meta v{{AGENT_META_VERSION}} — `{{AGENT_META_DATE}}`
>
> **Längenempfehlung:** 200–500 Zeilen optimal. Über 500 Zeilen → Detailwissen in
> `docs/ARCHITECTURE.md`, `docs/API.md` o.ä. auslagern und manuell verlinken.
> Agent-spezifisches Wissen → `.claude/3-project/<rolle>-ext.md` (Extension).
>
> **CLAUDE.md Hierarchie (Claude Code lädt in dieser Reihenfolge):**
> 1. `~/.claude/CLAUDE.md` — global, alle Projekte (~50 Zeilen max, persönliche Präferenzen)
> 2. `<projekt>/CLAUDE.md` — diese Datei, projektspezifisch (von agent-meta verwaltet)
> 3. `<ordner>/CLAUDE.md` — optional in Unterordnern (z.B. `src/backend/CLAUDE.md`)

---

## Projekt

**Name:** {{PROJECT_NAME}}
**Präfix:** {{PREFIX}}
**Plattform:** {{PLATFORM}}
**Beschreibung:** {{PROJECT_DESCRIPTION}}

---

## Tech-Stack

- **Runtime:** {{RUNTIME}}
- **Sprache:** {{LANGUAGE}}
- **Key-Dependencies:** {{SYSTEM_DEPENDENCIES}}

---

## Architektur

```
{{PROJECT_STRUCTURE}}
```

**Entry-Point:**
```
{{ENTRY_POINT_PATTERN}}
```

**Besondere Patterns:**
{{KEY_PATTERNS}}

---

## Code-Konventionen

{{CODE_CONVENTIONS}}

---

## Build & Development

```bash
# Build
{{BUILD_COMMAND}}

# Tests
{{TEST_COMMAND}}

# Dev-Stack starten
{{DEV_STACK_START}}

# Nach Änderungen neu laden
{{DEV_STACK_RELOAD}}
```

---

## Anforderungs-Kategorien

Kategorien für `docs/REQUIREMENTS.md`:

{{REQ_CATEGORIES_LIST}}

---

## Agenten-Konfiguration

<!-- agent-meta:managed-begin -->
<!-- Dieser Block wird von sync.py bei jedem sync automatisch aktualisiert. -->
<!-- Manuelle Änderungen hier werden überschrieben. -->

Generiert von agent-meta v{{AGENT_META_VERSION}} — `{{AGENT_META_DATE}}`

{{AGENT_HINTS}}
<!-- agent-meta:managed-end -->

---

## Sprachregeln

<!-- Die globale Rule .claude/rules/language.md (generiert von sync.py) deckt den Kern ab. -->
<!-- Hier nur projektspezifische Abweichungen eintragen — sonst leer lassen. -->

- `README.md` → **Englisch**
- Alle anderen Dokumente → **Deutsch**
- Code-Kommentare, Commit-Messages → **Englisch**
- Kommunikation mit dem Nutzer → **Deutsch**
