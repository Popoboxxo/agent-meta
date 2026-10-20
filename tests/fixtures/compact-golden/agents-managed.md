<!-- agent-meta:managed-begin -->
> **AI ROUTING:** Claude -> CLAUDE.md | Opencode, Gemini -> AGENTS.md
> **ENTRY:** `orchestrator`-Agent (für alle Dev-Tasks).
`agent-meta v2.0.0-beta.1` | DoD: `rapid-prototyping` | REQ-Trace: `false`

# CRITICAL GATE (runtime-partially enforced)
MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`.
Provider-native Permissions block Main-Chat-Writes; Delegations-Provenienz ist
NICHT erzwungen (Prompt + Permission-Layer).

**Spec/Plan-Gate (Convention boundary):** Auch Nicht-Pipeline-Anfragen (Ad-hoc-Dispatch, `quick-fix`, `bugfix`) erst über die Classify-Route (`S`/`M`/`L`/`XL`) führen — kein Direkteinstieg in die Implementierung ohne freigegebene Spec/Plan (`Status: APPROVED`). Details: Master-Rule `spec-plan-workflow`.

## Git Delegation
Commit ist für die per `auto_commit`-Tier freigeschaltete Rolle erlaubt (Details im Commit-Authority-Block der jeweiligen Rolle). Push, Tag und Branch-Management bleiben ausschließlich Aufgabe des `git` Agenten. Read-only (status, log) im Main Chat ok.

Native Extensions (Skills/Hooks) erlaubt, ignorieren nicht Branch-Guard/DoD.
Skill-getriebene Sub-Agent-Loops (z.B. generische Harness-Skills wie `subagent-driven-development`) sind KEINE dritte Ausnahme von der Orchestrator-Pflicht: ein Skill darf einen bereits vom `orchestrator` gestarteten Loop ausführen, aber niemals selbst zum Einstiegspunkt für einen neuen Dev-Task werden. Einzige Ausnahmen bleiben User-Override.

Anti-Recursion: Worker dürfen nicht an `orchestrator` zurück delegieren.

# Branch-Guard

Verwende Feature-Branches (`feat/`, `fix/`, `chore/`). Keine Code-Änderungen direkt auf `main` oder `master`.

# Commit-Konventionen

Verwende Conventional Commits (feat, fix, chore).
Beschreibungssprache: `Englisch`
Max 72 Zeichen in erster Zeile. Imperativ.
Format: `<type>: <beschreibung>` (Bsp: `feat: ...`)

# Sprachregeln

| Kontext | Sprache |
|---|---|
| User-Kommunikation | **Deutsch** |
| User-Input | **Deutsch** |
| Externe Doku | **Englisch** |
| Interne Doku | **Deutsch** |
| Code/Commits | **Englisch** |

## Enforced Gates (aktiv prüfen — HARD REJECT)

1. **No Self-Handoff / No Re-Delegation:** Ein `payload`, der mit "Du bist..." beginnt, ist ein Re-Delegations-/Spec-Dump-Versuch → HARD REJECT.
2. **Orchestrator-Singleton:** NUR `main_chat` darf den `orchestrator` spawnen. Worker → `orchestrator` → HARD REJECT (siehe `singleton-orchestrator-architecture.md`).
3. **Execution-Trace-Isolation:** Worker-Output muss strukturiert sein (STATUS, RESULT, ARTIFACTS). Keine rohen Logs propagieren.

# MCP Hard Prohibitions

> Kurzfassung der harten Tool-Verbote aktiver MCP-Server. Vollständige Tool-Listen und
> Hinweise: pro Provider in `.gemini/skills bzw. .opencode/skills` — jeweils `mcp-<server>/SKILL.md` (`use-lazy-rules.md`).

- **honcho:** `delete_conclusion`, `set_config` — absolut verboten.
- **playwright:** `browser_run_code_unsafe`, `browser_evaluate`, `browser_file_upload`, `browser_handle_dialog` — absolut verboten.
- **reqogniloom:** `workspace.close`, `workspace.reactivate`, `workspace.delete`, `permissions.set_rule`, `permissions.list`, `permissions.revoke`, `permissions.check`, `admin.backup_create`, `admin.backup_list`, `admin.restore`, `audit.query`, `audit.ai_review`, `events.dlq_list`, `events.dlq_replay`, `user.create`, `user.assign_role`, `user.list`, `user.deactivate` — absolut verboten.



## Agent Directory
> Agenten (Prompts) liegen in `.gemini/agents bzw. .opencode/agents`.

- `accessibility-specialist`: WCAG 2.1/2.2 Compliance-Audit, ARIA-Checks, Keyboard-Navigation, Screenreader...
- `agent-meta-manager`: agent-meta verwalten: Upgrade, Sync, Feedback, projektspezifische Agenten anl...
- `agent-meta-scout`: Claude-Ökosystem scouten: neue Skills, Rollen, Rules und Patterns entdecken
- `api-specialist`: OpenAPI/Contract-First API Design, Schnittstellen-Spezifikationen.
- `app-lifecycle-governor`: App-Lifecycle-Governance: Ownership, SLA, Data-Classification, Deprecation
- `bug-feature-analyzer`: Issue-Triage: Eingehende Bug-Meldungen und Feature-Requests analysieren und k...
- `claude-expert`: Absoluter Analyse-Experte für die Plattform Claude Code: Funktionsweise, Konf...
- `code-reviewer`: Clean Code Gatekeeper: Blast-Radius-Analyse, SOLID/DRY Prüfung, Code-Qualität...
- `concept-architect`: Systemdesign für komplexe Änderungen: Komponenten, Schnittstellen, Trade-offs
- `concept-reviewer`: Konzept-Critic: reviewt Design-Docs und Konzepte auf Vollständigkeit, Logik, ...
- `concept-specifier`: Technische Spezifikationen aus Anforderungen und Codebase-Kontext — implementiert nicht
- `continue-expert`: Absoluter Analyse-Experte für die Plattform Continue: Funktionsweise, Konfigu...
- `copilot-expert`: Absoluter Analyse-Experte für die Plattform GitHub Copilot: Funktionsweise, K...
- `data-engineer`: ETL/ELT-Pipelines, Schema-Migration (Datenebene), Data-Quality-Checks, Lineag...
- `dependency-auditor`: Supply-Chain-Hygiene: SBOM-Analyse, Lizenz-Kompatibilität, Version-Drift und ...
- `design-system-architect`: Design-System-Schema → echte Token-Artefakte, Farbharmonie, Variant-Contracts.
- `developer`: Feature-Implementierung und Bugfixes
- `devops-engineer`: CI/CD, Infrastructure as Code, Kubernetes, Observability.
- `docker`: Dev-Stack verwalten, Test-Stack starten, Binary-Management, Dockerfiles erste...
- `documenter`: CODEBASE_OVERVIEW, ARCHITECTURE, README, Erkenntnisse pflegen
- `e2e-tester`: E2E-Tests, visuelle Regression und Accessibility-Audits via Playwright
- `effort-estimator`: Schätzt Aufwände für Entwicklungsaufgaben basierend auf Task-Typ und LLM-Kali...
- `explorer`: Read-only Codebase-Recherche, Dependency- und Impact-Mapping, Datei- und Symb...
- `export-manager`: Target-agnostischer Output-Router: Markdown, Confluence, Jira-Xray, Notion.
- `feedback`: Projekt-Feedback standardisieren: Bugs, Features, Verbesserungen als GitHub I...
- `frontend-component-engineer`: Screen-Spec + Token-Contract → produktionsreife UI-Komponenten.
- `gemini-expert`: Absoluter Analyse-Experte für die Plattform Gemini (Antigravity): Funktionswe...
- `git`: Commits, Branches, Tags, Push/Pull und alle Git-Operationen
- `ideation`: Neue Ideen explorieren, Vision schärfen, Übergabe an requirements
- `incident-responder`: Live-Incident-Koordination: korreliert Logs und Metriken, führt Runbook-Schri...
- `intern-developer`: [EASTER EGG / GAG] Der übereifrige Praktikant
- `junior-developer`: Triviale Code-Änderungen (≤2 Dateien, kein Architektur-Impact)
- `knowledge-curator`: Strategische Knowledge-Engine-Steuerung: Schema-Evolution, Wiki-Strukturierun...
- `knowledge-gardener`: Kleinteilige Wiki-Pflege: Links reparieren, Tags harmonisieren, Frontmatter e...
- `knowledge-indexer`: Pflegt index.md (Content-Katalog, OKF §6) und log.md (Chronologisches Event-L...
- `knowledge-ingestor`: Sources einlesen, Key Information extrahieren, Wiki-Seiten erstellen/ aktuali...
- `knowledge-linter`: Wiki-Gesundheitscheck: Widersprüche, Orphans, veraltete Claims, kaputte Links...
- `knowledge-migrator`: Vorhandene Projektinhalte aufräumen und OKF-konform ins Knowledge Wiki migrieren
- `knowledge-querier`: Fragen gegen das Knowledge Wiki beantworten
- `log-analyzer`: System- und Applikations-Logs analysieren: Frequency-Clustering, Severity-Kla...
- `mammouth-expert`: Absoluter Analyse-Experte für die Plattform Mammouth Code: Funktionsweise, Ko...
- `meta-feedback`: Verbesserungsvorschläge für agent-meta als GitHub Issues einreichen
- `opencode-expert`: Absoluter Analyse-Experte für die Plattform Opencode: Funktionsweise, Konfigu...
- `orchestrator`: Einstiegspunkt für alle Entwicklungsaufgaben
- `performance-optimizer`: Big-O Bottleneck-Identifikation und datengetriebene Performance-Optimierung.
- `planner`: Umsetzungsplanung
- `principal-developer`: Last-Resort-Eskalationsstufe
- `product-manager`: Strategisches Produkt-Management: Backlog, User-Stories, Sprint-Planung, Prio...
- `prompt-engineer`: Der ultimative Experte für Prompt-Engineering
- `refactoring-specialist`: Systematische großflächige Code-Transformation mit Sicherheitsnetz: Strangler...
- `release`: Versioning, Changelog, Build-Artifact, GitHub Release erstellen
- `requirements`: Anforderungen aufnehmen, REQ-IDs vergeben, REQUIREMENTS.md pflegen
- `senior-developer`: Komplexe Features, Architektur-Entscheidungen, schwierige Bugs, Cross-Cutting...
- `technical-writer`: Externe entwickler- und nutzergerichtete Doku: API-Referenzen, Getting-Starte...
- `test-executor`: Bestehende Test-Suiten ausführen — kein Test-Design, kein Code-Schreiben
- `tester`: TDD, Test-Suite ausführen, Testabdeckung sichern
- `ui-ux-designer`: UI-Spezifikationen, Mockups und Design-Systeme erstellen.
- `validator`: Code gegen REQs prüfen, DoD-Checkliste, Traceability-Audit



## Knowledge Engine

Aktiviert (Domäne: **internal-docs**). Bundle: `knowledge/` — Index: `knowledge/wiki/index.md`, Schema/Workflows: `knowledge/schema.md`, immutable Sources: `knowledge/sources/` (LLM liest, modifiziert NIEMALS).

<!-- agent-meta:managed-end -->
