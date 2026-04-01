# {{PROJECT_NAME}} — Projekt-CLAUDE.md

> Diese Datei ist die `CLAUDE.md` für das Projekt {{PROJECT_NAME}}.
> Sie instanziiert die Agenten-Rollen aus `agent-meta` mit projektspezifischem Kontext.

---

## Projektübersicht

**Name:** {{PROJECT_NAME}}
**Präfix:** {{PREFIX}}
**Beschreibung:** {{PROJECT_DESCRIPTION}}

**Tech-Stack:**
- Runtime: {{RUNTIME}} (z.B. Bun, Node.js)
- Sprache: TypeScript (ES6+, strict)
- Ziel-Plattform: {{TARGET_PLATFORM}} (z.B. Sharkord Plugin SDK v0.0.16)
- Besondere Dependencies: {{KEY_DEPENDENCIES}}

---

## Agenten-Rollen

Die Agenten dieses Projekts sind in `.claude/agents/` definiert und basieren
auf den Templates aus [agent-meta](../agent-meta/agents/).

| Agent | Datei | Zuständigkeit |
|-------|-------|--------------|
| Orchestrator | `.claude/agents/{{PROJECT_SHORT}}.md` | Koordination aller Sub-Agenten |
| Developer | `.claude/agents/{{PREFIX}}-developer.md` | Feature-Implementierung nach REQ-IDs |
| Tester | `.claude/agents/{{PREFIX}}-tester.md` | TDD, Test-Suite, Coverage |
| Validator | `.claude/agents/{{PREFIX}}-validator.md` | DoD-Check, Traceability, Code-Qualität |
| Requirements | `.claude/agents/{{PREFIX}}-requirements.md` | REQ-Aufnahme, REQUIREMENTS.md |
| Documenter | `.claude/agents/{{PREFIX}}-documenter.md` | Doku-Pflege, Erkenntnisse |
| Release | `.claude/agents/{{PREFIX}}-release.md` | Versioning, Build, GitHub Release |

---

## Projektspezifische Code-Konventionen

<!-- Hier die spezifischen Regeln für dieses Projekt eintragen -->

### TypeScript
- **ES6+** — kein CommonJS, kein `require()`
- **`const` / `let`** — NIEMALS `var`
- **Kein `any`** — verwende `unknown` und Type Guards
- **Named Exports only** — KEINE Default-Exports
- {{EXTRA_TS_RULES}}

### Dateibenennung
- kebab-case: `module-name.ts`
- Tests: `<module>.test.ts`

---

## Projektspezifische Architektur

```
{{PROJECT_STRUCTURE}}
```

**Entry-Point Pattern:**
```typescript
{{ENTRY_POINT_PATTERN}}
```

---

## Development Environment

### Build
```bash
{{BUILD_COMMAND}}
```

### Tests ausführen
```bash
{{TEST_COMMAND}}
```

### Docker / Dev-Stack
```bash
{{DEV_STACK_COMMANDS}}
```

---

## Anforderungs-Kategorien

<!-- Kategorien für REQUIREMENTS.md dieses Projekts -->
{{REQ_CATEGORIES_LIST}}

---

## Standard-Workflows

Alle Workflows sind in den Agenten-Templates definiert und gelten unverändert.
Projektspezifische Abweichungen werden hier dokumentiert:

{{WORKFLOW_OVERRIDES}}

---

## Sprache

- `README.md` → **Englisch**
- Alle anderen Dokumente → Deutsch
- Code-Kommentare → Englisch
- Commit-Messages → Englisch
- Kommunikation mit dem Nutzer → Deutsch

---

## Verweis auf agent-meta

Dieses Projekt verwendet die standardisierten Agenten-Rollen aus:
`c:\Repositorys\MetaAgent\agent-meta`

Bei Verbesserungen an der generischen Logik: Änderungen ins Template eintragen
und dann in alle betroffenen Projekte übernehmen.
