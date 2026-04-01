# {{PROJECT_NAME}}

> Projektbeschreibung für Claude-Agenten. Diese Datei ist die **einzige Quelle**
> für projektspezifischen Kontext — Agenten lesen sie, statt eigenen Kontext zu haben.

---

## Projekt

**Name:** {{PROJECT_NAME}}
**Präfix:** {{PREFIX}}
**Plattform:** {{PLATFORM}}  <!-- z.B. Sharkord Plugin SDK v0.0.16 -->
**Beschreibung:** {{PROJECT_DESCRIPTION}}

---

## Tech-Stack

- **Runtime:** {{RUNTIME}}  <!-- z.B. Bun (NICHT Node.js) -->
- **Sprache:** TypeScript (ES6+, strict)
- **Key-Dependencies:** {{KEY_DEPENDENCIES}}
- **Ziel-Plattform:** {{TARGET_PLATFORM}}

---

## Architektur

```
{{PROJECT_STRUCTURE}}
```

**Entry-Point:**
```typescript
{{ENTRY_POINT_PATTERN}}
```

**Besondere Patterns:**
{{KEY_PATTERNS}}

---

## Code-Konventionen

### TypeScript
- **ES6+** — kein CommonJS, kein `require()`
- **`const` / `let`** — NIEMALS `var`
- **Kein `any`** — `unknown` + Type Guards verwenden
- **Named Exports only** — KEINE Default-Exports
- {{EXTRA_TS_RULES}}

### Dateibenennung
- kebab-case: `module-name.ts`
- Tests: `<module>.test.ts`

### Fehlerbehandlung
{{ERROR_HANDLING_PATTERN}}

---

## Build & Development

```bash
# Build
{{BUILD_COMMAND}}

# Tests
{{TEST_COMMAND}}

# Dev-Stack starten
docker compose -f docker-compose.dev.yml up

# Nach Änderungen
{{BUILD_COMMAND}}
docker compose -f docker-compose.dev.yml restart {{SERVICE_NAME}}
```

---

## Anforderungs-Kategorien

Kategorien für `docs/REQUIREMENTS.md`:

{{REQ_CATEGORIES_LIST}}

---

## Agenten-Konfiguration

**Plattform-Layer:** {{PLATFORM_LAYER}}
<!-- z.B. "Sharkord" → verwendet 2-platform/sharkord-docker.md + sharkord-release.md -->

| Rolle | Datei in `.claude/agents/` | Basis |
|-------|---------------------------|-------|
| Orchestrator | `{{PROJECT_SHORT}}.md` | `1-generic/orchestrator.md` |
| Developer | `{{PREFIX}}-developer.md` | `1-generic/developer.md` |
| Tester | `{{PREFIX}}-tester.md` | `1-generic/tester.md` |
| Validator | `{{PREFIX}}-validator.md` | `1-generic/validator.md` |
| Requirements | `{{PREFIX}}-requirements.md` | `1-generic/requirements.md` |
| Documenter | `{{PREFIX}}-documenter.md` | `1-generic/documenter.md` |
| Release | `{{PREFIX}}-release.md` | `2-platform/sharkord-release.md` |
| Docker | `{{PREFIX}}-docker.md` | `2-platform/sharkord-docker.md` |

---

## Sprachregeln

- `README.md` → **Englisch**
- Alle anderen Dokumente → **Deutsch**
- Code-Kommentare, Commit-Messages → **Englisch**
- Kommunikation mit dem Nutzer → **Deutsch**
