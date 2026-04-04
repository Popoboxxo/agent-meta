# {{PROJECT_NAME}}

> Projektbeschreibung für Claude-Agenten. Diese Datei ist die **einzige Quelle**
> für projektspezifischen Kontext — Agenten lesen sie, statt eigenen Kontext zu haben.
>
> Generiert von agent-meta v{{AGENT_META_VERSION}} — `{{AGENT_META_DATE}}`
> Plattform-Layer: {{PLATFORM_LAYER}}

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
- **Key-Dependencies:** {{KEY_DEPENDENCIES}}
- **Ziel-Plattform:** {{TARGET_PLATFORM}}

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

{{AGENT_TABLE}}
<!-- agent-meta:managed-end -->

---

## Sprachregeln

- `README.md` → **Englisch**
- Alle anderen Dokumente → **Deutsch**
- Code-Kommentare, Commit-Messages → **Englisch**
- Kommunikation mit dem Nutzer → **Deutsch**
