# agent-meta

## Projekt

**Name:** agent-meta
**Präfix:** am
**Plattform:** Python CLI (sync.py)
**Beschreibung:** Zentrales Meta-Repository für die Standardisierung und Wiederverwendung von Claude-Agenten-Rollen über alle Projekte hinweg.

> Tech-Stack, Architektur & Build-Befehle: discoverable via Repo (Manifeste, CI-Configs).

## Code-Konventionen

- Python: PEP 8, snake_case, klare Funktionsnamen
- Keine externen Python-Dependencies außer Stdlib
- Markdown-Dateien: GitHub Flavored Markdown
- YAML Frontmatter in allen Agent-Templates


## Anforderungs-Kategorien

Kategorien für `docs/REQUIREMENTS.md`:

- Framework-Features (sync.py, neue Agenten-Rollen, Variablen)
- Agenten-Templates (Workflows, Sprach-Sektionen, Versionierung)
- Entwickler-Experience (Howto, Beispiele, Doku)



<!-- agent-meta:managed-begin -->
> **ROUTING:**

 Opencode->AGENTS.md |
 Gemini->AGENTS.md
> **ENTRY:** `orchestrator`-Agent (für alle Dev-Tasks).
`agent-meta v0.101.0-beta.1` | DoD: `rapid-prototyping` | REQ-Trace: `false`


## Regeln

# A2A Anti-Re-Delegation Gates

1. Limit depth to 10, no self-handoff.
2. Short payload: `payload.t` max 300 Zeichen.
3. No Re-Delegation (payload starts with "Du bist...").
4. Singleton Orchestrator: NUR der `main_chat` darf den `orchestrator` spawnen.
5. Execution-Trace-Isolation: Worker-Output muss strukturiert sein (STATUS, RESULT, ARTIFACTS). Keine rohen Logs propagieren.

## Bekannte Grenzen

- **Tiefenlimit (Punkt 1) ist modellbasiert, keine technische Barriere.** Eine passende Implementierung existiert (`validate_envelope(max_depth=...)` in `scripts/lib/delegation_syntax.py`), wird aber im aktiven Delegationspfad nirgends aufgerufen. Die Regel verlässt sich auf Modell-Gehorsam, nicht auf Enforcement.
- **Singleton-Orchestrator (Punkt 4) wird nur über eine Selbstdeklaration der Agenten-Identität gestützt** (`#agent-meta:agent=<name>` in `.claude/hooks/orchestrator-guard.sh`), die im Hook-Quelltext selbst als "soft, self-reported convention, not a security boundary" dokumentiert ist. Jeder Agent kann sich technisch als privilegiert deklarieren. **Das ist eine bewusste Design-Grenze, kein behebbarer Bug:** kein Provider liefert im PreToolUse-Payload eine echte Agenten-Identität, der Hook kann die Behauptung also nicht verifizieren. Der Guard ist ein Konventions-Schutz gegen Versehen, kein Schutz gegen einen Agenten, der die Regel bewusst umgeht. Wer eine harte Grenze braucht, muss Git-Mutationen außerhalb des Agenten-Systems absichern (Branch-Protection, Pre-Receive-Hooks, Review-Pflicht) — zerstörerische Operationen (`push --force`, `reset --hard`, `clean -fd`, `branch -D`) bleiben deshalb ausdrücklich zustimmungspflichtig durch den Nutzer.
- **Große Ergebnisse gehören in Dateien, nicht in den Return-Channel.** Der synchrone Tool-Result-Kanal hat ein undokumentiertes Größenlimit; überlange Antworten können ohne Fehlersignal beschnitten zurückkommen (agent-meta #514). Read-only-Rollen ohne `Write` (`Plan`, `Explore`, `code-reviewer`) sind davon strukturell betroffen. Daher: Artefakte ab ~1000 Zeilen (Pläne, Konzepte, Reviews) immer von einer schreibfähigen Rolle in eine Datei schreiben lassen und nur den Pfad zurückgeben. Empfangene Ergebnisse auf Vollständigkeit prüfen (fehlender Kopf/erste Abschnitte = Truncation), nicht blind weiterverarbeiten.



# Branch-Guard

Verwende Feature-Branches (`feat/`, `fix/`, `chore/`). Keine Code-Änderungen direkt auf `main` oder `master`.

## Bekannte Grenzen

Die technische Durchsetzung (`orchestrator-guard.sh`) erkennt Git-Mutationen über eine Regex-/shlex-basierte Analyse des Bash-Befehls, kein vollständiger Shell-Parser. Bekannte Lücken: `eval "git commit ..."` wird nicht erkannt, direkte Schreibzugriffe auf `.git/` werden nicht geprüft, andere Git-Tools (`hub`, `gh repo ...`) sind nicht erfasst. Bewusster Trade-off, kein Bug (siehe Kommentar in `.claude/hooks/orchestrator-guard.sh:18-30`) — nur relevant für Nutzer, die sich vollständig auf den Schutz statt auf die Konvention verlassen.



# Commit-Konventionen

Verwende Conventional Commits (feat, fix, chore).
Beschreibungssprache: `Englisch`
Max 72 Zeichen in erster Zeile. Imperativ.
Format: `<type>: <beschreibung>` (Bsp: `feat: ...`)



# Definition of Done (DoD)

Pflicht: Code komplett, Konventionen & Conv. Commits eingehalten, keine Regressions.



# GitHub Issue Lifecycle

Issues referenzieren und am Ende mit passendem Keyword (`Fixes #123`, `Closes #123`) im PR oder Commit schließen. Kommentiere das Issue nach Fertigstellung.



# Sprachregeln

| Kontext | Sprache |
|---|---|
| User-Kommunikation | **Deutsch** |
| User-Input | **Deutsch** |
| Externe Doku | **Englisch** |
| Interne Doku | **Deutsch** |
| Code/Commits | **Englisch** |



# Lifecycle-Tasks

Beim Start prüfen: existiert `.gemini/pending-tasks.md`?
Falls ja und enthält `- [ ]`: User fragen ob delegiert werden soll.
Nach Erledigung: löschen. Datei nicht committen.



# MCP Hard Prohibitions

> Kurzfassung der harten Tool-Verbote aktiver MCP-Server. Vollständige Tool-Listen und
> Hinweise: siehe `.claude/skills/mcp-<server>/SKILL.md` (`use-lazy-rules.md`).

- **honcho:** `delete_conclusion`, `set_config` — absolut verboten.
- **playwright:** `browser_run_code_unsafe`, `browser_evaluate`, `browser_file_upload`, `browser_handle_dialog` — absolut verboten.
- **reqogniloom:** `workspace.close`, `workspace.reactivate`, `workspace.delete`, `permissions.set_rule`, `permissions.list`, `permissions.revoke`, `permissions.check`, `admin.backup_create`, `admin.backup_list`, `admin.restore`, `audit.query`, `audit.ai_review`, `events.dlq_list`, `events.dlq_replay`, `user.create`, `user.assign_role`, `user.list`, `user.deactivate` — absolut verboten.



# No Worktree Isolation

**Anti-Pattern:** Niemals das Argument `isolation: "worktree"` beim Spawnen von Subagenten verwenden.
**Grund:** Agenten schreiben dann ihren Output in den internen Ordner `.claude/worktrees/agent-<id>/` anstatt in das eigentliche Projektverzeichnis. Das führt zu fehlgeleiteten Dateien und Datenverlust in der eigentlichen Codebase.

Alle Agenten müssen direkt im Projektverzeichnis arbeiten (Isolation deaktivieren oder weglassen). Der `.claude/` Ordner (sowie `.gemini/`, `.continue/`, `.mammouth/` etc.) ist strikt als Infrastruktur-Ordner zu betrachten und darf nicht für Arbeitskopien missbraucht werden.



# Python Conventions

PEP8 einhalten. Type Hints (typing) verwenden. Docstrings für Klassen/Methoden schreiben.



# Session-Abschluss

Delegate Session-Zusammenfassung an `documenter` am Ende großer Features, um CODEBASE_OVERVIEW.md aktuell zu halten.



# Submodule-Schutzkonzept

Regeln für den Umgang mit allen Git-Submodulen (`.agent-meta/`, `external/*/`, und alle weiteren in `.gitmodules`):

- **Keine direkten Änderungen in Submodul-Verzeichnissen:** Dateien in `.agent-meta/`, `external/*/` und allen anderen Submodul-Pfaden dürfen in Konsumenten-Repositories niemals direkt editiert oder committet werden. Submodule sind separate Repositories mit eigenem Lifecycle (Build, Push, Deploy, Version-Tags). Änderungen MÜSSEN im Submodul-Repo selbst durchgeführt, committet und gepusht werden — danach aktualisiert das Parent-Repo die Pinned-Commit-Referenz.
- **Keine Mutation von `.gitmodules` / Git Staging:** `.gitmodules` darf nicht automatisch modifiziert werden und Submodule dürfen nicht automatisch via `git add` gestaged werden.
- **Kein Source-Code-Scaffolding in Konsumenten-Projekten:** In Konsumenten-Projekten wird kein Anwendungscode generiert/gerüstet; verwaltet werden ausschließlich `.meta-config/project.yaml` und die Managed Blocks.
- **Framework-Änderungen nur im agent-meta Repo:** Änderungen am agent-meta Framework müssen auf Feature-Branches im agent-meta Repository selbst durchgeführt werden.



# Lazy-Loaded Rules

> Nicht immer geladen — bei Bedarf per `Read` öffnen: `.claude/skills/<skill>/SKILL.md`.

| Skill | Wann |
|---|---|
| sync-interface | sync.py, Templates/Rules ändern |
| architecture | Templates/Overrides/Placeholder ändern |
| conventions | Vor Commits in agents/, config/, scripts/lib |
| submodule-protection | .agent-meta/, external/, .gitmodules |
| a2a-delegation-gates | A2A-Delegation an Subagenten |
| python-conventions | Python-Code |
| issue-lifecycle | GitHub-Issue |
| lifecycle-tasks | Session-Start, pending-tasks.md vorhanden |
| session-conclusion | Feature-Abschluss |
| provider-agnostic | agents/1-generic editieren |
| mcp-reqogniloom | ReqogniLoom-MCP-Tools |
| mcp-honcho | Honcho-MCP-Memory-Tools |
| mcp-playwright | Playwright-MCP-Browser-Tools |
| mcp-viz-logger | viz-logger Event-Logging |
| tool-graphify | Architektur-/Datei-Fragen mit graphify |

Harte MCP-Tool-Verbote: siehe `mcp-guardrails.md` (always-on).



# CRITICAL GATE
MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`. Keine Ausnahmen.

## Git Delegation
Git Mutationen (commit, push, add etc) -> `git` Agent. Read-only (status, log) im Main Chat ok.

Native Extensions (Skills/Hooks) erlaubt, ignorieren nicht Branch-Guard/DoD.

Anti-Recursion: Worker dürfen nicht an `orchestrator` zurück delegieren.



# agent-meta — Schichten-Architektur

Dieses Repo ist das Meta-Repository für Agenten-Standards. Jede Änderung an Templates
wirkt sich auf alle Projekte aus die dieses Submodul einbinden.

## Abhängigkeitsprinzip

Jede Änderung an einer Quelldatei propagiert in alle instanziierten Projekte
beim nächsten `sync.py`-Lauf. Daher:

- **1-generic geändert** → alle Projekte neu syncen
- **2-platform geändert** → alle Projekte auf dieser Plattform neu syncen
- **config/role-defaults.yaml geändert** → alle Projekte neu syncen
- **config/skills-registry.yaml geändert** → alle betroffenen Projekte neu syncen

Details (Schichten-Modell, Composition-Syntax, Platzhalter-Escape): `docs/architecture/01-layer-model.md`.


# agent-meta — Development Conventions

## Hard Invariants

1. `.gemini/agents bzw. .opencode/agents` is generated output — never edit manually. Make changes in `agents/` or `.meta-config/project.yaml`.
2. Bump agent version in frontmatter on every content change:
   - Major (`X.0.0`): renamed variable, changed behavior, new mandatory section
   - Minor (`x.Y.0`): new optional section, expanded scope
   - Patch (`x.y.Z`): text improvements, clarifications, config path fixes
   - Platform agents (`2-platform/`) also keep `based-on` up to date.
3. Placeholders are always `{{GROSS_MIT_UNTERSTRICH}}`. Lowercase or mixed case will not match.

Details (Naming-Konvention, Instruction-Bleed-Checkliste, Adding-New-Role/Placeholder, Change-Checklist): `.claude/skills/conventions/SKILL.md`.


# Provider-Agnostic Policy

Generische Templates in `1-generic/` müssen provider-agnostisch sein. Keine spezifischen Prompts für Claude, Gemini etc., außer als Fallback/Feature-Flag.



# agent-meta — sync.py Interface

`sync.py` ist der einzige Weg Agenten zu generieren. Nie direkt in `.gemini/agents bzw. .opencode/agents` schreiben.

Vollständige Referenz (Flags, sync.log, Modulstruktur):
→ `.agent-meta/agents/1-generic/_wf-sync-interface.md`

## Branch-Guard-Erweiterung für agent-meta

Zusätzlich zu den generischen Branch-Guard-Regeln gilt hier:

- `sync.py` ausführen → immer Branch (Sync propagiert in alle Projekte)

**Faustregel: sync.py ausführen oder >1 Datei anfassen → Branch.**

**NIE direkt auf main:** sync.py-Läufe, Template-Änderungen, Rule-Änderungen — egal wie klein.

## Warum

Direkte Commits auf main propagieren Fehler sofort in alle Projekte beim nächsten Sync.

---

Details (Smart Context Regeneration, `--check`, `context-hashes.json`, Provider-Context-Lifecycle): `.claude/skills/sync-interface/SKILL.md`.


# MCP: honcho

> Honcho local memory and context server

---

## Erlaubte Tools

- `chat`
- `get_context`
- `get_representation`
- `search`
- `list_conclusions`
- `create_conclusion`

## Verbotene Tools (ABSOLUT — keine Ausnahmen)

- `delete_conclusion`
- `set_config`

**Verbindungstyp:** `sse` — Details: `config/mcp-registry.yaml`.




# MCP: playwright

> Playwright MCP Server für Browser-Automation und E2E-Tests

---

## Erlaubte Tools

- `browser_navigate`
- `browser_navigate_back`
- `browser_snapshot`
- `browser_take_screenshot`
- `browser_click`
- `browser_type`
- `browser_hover`
- `browser_select_option`
- `browser_press_key`
- `browser_fill_form`
- `browser_wait_for`
- `browser_resize`
- `browser_tabs`
- `browser_network_requests`
- `browser_network_request`
- `browser_console_messages`

## Verbotene Tools (ABSOLUT — keine Ausnahmen)

- `browser_run_code_unsafe`
- `browser_evaluate`
- `browser_file_upload`
- `browser_handle_dialog`

**Verbindungstyp:** `stdio` — Details: `config/mcp-registry.yaml`.




# MCP: reqogniloom

> ReqogniLoom requirements-engineering platform — requirements, architecture, tests, traceability and AI-assisted derivation

---

## Erlaubte Tools

- `requirement.get`
- `requirement.query`
- `requirement.create`
- `requirement.update`
- `requirement.decompose`
- `requirement.validate`
- `requirement.derive`
- `requirement.check_consistency`
- `needs.read`
- `needs.create`
- `needs.update`
- `needs.get_traces`
- `needs.derive_requirements`
- `architecture.get`
- `architecture.query`
- `architecture.create`
- `architecture.update`
- `architecture.link`
- `architecture.decompose`
- `architecture.decompose_commit`
- `test.get`
- `test.query`
- `test.create`
- `test.update`
- `test.link`
- `test.run_create`
- `test.run_get`
- `test.run_report_results`
- `test.derive_from_requirement`
- `traceability.query`
- `traceability.suggest_links`
- `artifact.search`
- `artifact.get_tree`
- `workspace.get_context`
- `adr.read`
- `adr.create`
- `adr.update`
- `adr.delete`
- `risk.read`
- `risk.create`
- `risk.update`
- `risk.delete`
- `issue.read`
- `issue.create`
- `issue.update`
- `issue.delete`
- `glossary.read`
- `glossary.create`
- `glossary.update`
- `glossary.delete`
- `prompt_template.get`
- `ai_derivation.derive_requirements_from_need`
- `ai_derivation.suggest_architecture_for_requirement`
- `ai_derivation.decompose_requirement_next_level`

## Verbotene Tools (ABSOLUT — keine Ausnahmen)

- `workspace.close`
- `workspace.reactivate`
- `workspace.delete`
- `permissions.set_rule`
- `permissions.list`
- `permissions.revoke`
- `permissions.check`
- `admin.backup_create`
- `admin.backup_list`
- `admin.restore`
- `audit.query`
- `audit.ai_review`
- `events.dlq_list`
- `events.dlq_replay`
- `user.create`
- `user.assign_role`
- `user.list`
- `user.deactivate`

**Verbindungstyp:** `sse` — Details: `config/mcp-registry.yaml`.




# MCP: viz-logger

> agent-meta visualization event logger — tracks agent_start, delegate_out, agent_end for graph generation

---

## Erlaubte Tools

- `log_viz_event`

**Verbindungstyp:** `stdio` — Details: `config/mcp-registry.yaml`.




# External Tool: graphify

> graphify — lokal installiertes CLI-Tool. Baut das Repo als Wissensgraph auf (Community Detection, God Nodes, Query/Path/Explain). Wird NICHT von agent-meta bereitgestellt, muss lokal installiert sein.

---

Details/Registrierung: `config/external-tools-registry.yaml`.
Hook-Wrapper: `hooks/0-external/graphify-search-guard.sh`, `hooks/0-external/graphify-read-guard.sh` · Injektionen: `.gemini/skills/graphify` (skill)





## Agent Directory
> Agenten (Prompts) liegen in `.gemini/agents bzw. .opencode/agents`.

| Agent | Core Capabilities |
|-------|-------------------|
| `accessibility-specialist` | WCAG 2.1/2.2 Compliance-Audit, ARIA-Checks, Keyboard-Navigation |
| `agent-meta-manager` | agent-meta verwalten: Upgrade, Sync, Feedback |
| `agent-meta-scout` | Claude-Ökosystem scouten: neue Skills, Rollen, Rules |
| `api-specialist` | OpenAPI/Contract-First API Design, Schnittstellen-Spezifikationen |
| `bug-feature-analyzer` | Issue-Triage: Eingehende Bug-Meldungen, Feature-Requests analysieren, k |
| `claude-expert` | Absoluter Analyse-Experte für die Plattform Claude Code: Funktionsweise, Konf |
| `code-reviewer` | Clean Code Gatekeeper: Blast-Radius-Analyse, SOLID/DRY Prüfung, Code-Qualität |
| `concept-reviewer` | Konzept-Critic: reviewt Design-Docs, Konzepte auf Vollständigkeit, Logik |
| `continue-expert` | Absoluter Analyse-Experte für die Plattform Continue: Funktionsweise, Konfigu |
| `copilot-expert` | Absoluter Analyse-Experte für die Plattform GitHub Copilot: Funktionsweise, K |
| `data-engineer` | ETL/ELT-Pipelines, Schema-Migration (Datenebene), Data-Quality-Checks |
| `dependency-auditor` | Supply-Chain-Hygiene: SBOM-Analyse, Lizenz-Kompatibilität, Version-Drift und |
| `design-system-architect` | Design-System-Schema → echte Token-Artefakte, Farbharmonie, Variant-Contracts |
| `developer` | Feature-Implementierung, Bugfixes |
| `devops-engineer` | CI/CD, Infrastructure as Code, Kubernetes |
| `docker` | Dev-Stack verwalten, Test-Stack starten, Binary-Management |
| `documenter` | CODEBASE_OVERVIEW, ARCHITECTURE, README |
| `e2e-tester` | E2E-Tests, visuelle Regression, Accessibility-Audits via Playwright |
| `effort-estimator` | Schätzt Aufwände für Entwicklungsaufgaben basierend auf Task-Typ, LLM-Kali |
| `explorer` | Read-only Codebase-Recherche, Dependency, Impact-Mapping |
| `export-manager` | Target-agnostischer Output-Router: Markdown, Confluence, Jira-Xray |
| `feedback` | Projekt-Feedback standardisieren: Bugs, Features, Verbesserungen als GitHub I |
| `frontend-component-engineer` | Screen-Spec + Token-Contract → produktionsreife UI-Komponenten |
| `gemini-expert` | Absoluter Analyse-Experte für die Plattform Gemini (Antigravity): Funktionswe |
| `git` | Commits, Branches, Tags |
| `ideation` | Neue Ideen explorieren, Vision schärfen, Übergabe an requirements |
| `incident-responder` | Live-Incident-Koordination: korreliert Logs, Metriken, führt Runbook-Schri |
| `intern-developer` | Der übereifrige Praktikant |
| `junior-developer` | Triviale Code-Änderungen (≤2 Dateien, kein Architektur-Impact) |
| `knowledge-curator` | Strategische Knowledge-Engine-Steuerung: Schema-Evolution, Wiki-Strukturierun |
| `knowledge-gardener` | Kleinteilige Wiki-Pflege: Links reparieren, Tags harmonisieren, Frontmatter e |
| `knowledge-indexer` | Pflegt index.md (Content-Katalog, OKF §6), log.md (Chronologisches Event-L |
| `knowledge-ingestor` | Sources einlesen, Key Information extrahieren, Wiki-Seiten erstellen/ aktuali |
| `knowledge-linter` | Wiki-Gesundheitscheck: Widersprüche, Orphans, veraltete Claims |
| `knowledge-migrator` | Vorhandene Projektinhalte aufräumen, OKF-konform ins Knowledge Wiki migrieren |
| `knowledge-querier` | Fragen gegen das Knowledge Wiki beantworten |
| `log-analyzer` | System, Applikations-Logs analysieren: Frequency-Clustering, Severity-Kla |
| `mammouth-expert` | Absoluter Analyse-Experte für die Plattform Mammouth Code: Funktionsweise, Ko |
| `meta-feedback` | Verbesserungsvorschläge für agent-meta als GitHub Issues einreichen |
| `opencode-expert` | Absoluter Analyse-Experte für die Plattform Opencode: Funktionsweise, Konfigu |
| `orchestrator` | Einstiegspunkt für alle Entwicklungsaufgaben |
| `performance-optimizer` | Big-O Bottleneck-Identifikation, datengetriebene Performance-Optimierung |
| `planner` | Umsetzungsplanung |
| `principal-developer` | Last-Resort-Eskalationsstufe |
| `prompt-engineer` | Der ultimative Experte für Prompt-Engineering |
| `refactoring-specialist` | Systematische großflächige Code-Transformation mit Sicherheitsnetz: Strangler |
| `release` | Versioning, Changelog, Build-Artifact |
| `requirements` | Anforderungen aufnehmen, REQ-IDs vergeben, REQUIREMENTS.md pflegen |
| `senior-developer` | Komplexe Features, Architektur-Entscheidungen, schwierige Bugs |
| `technical-writer` | Externe entwickler, nutzergerichtete Doku: API-Referenzen, Getting-Starte |
| `tester` | TDD, Test-Suite ausführen, Testabdeckung sichern |
| `ui-ux-designer` | UI-Spezifikationen, Mockups, Design-Systeme erstellen |
| `validator` | Code gegen REQs prüfen, DoD-Checkliste, Traceability-Audit |


## Knowledge Engine

Aktiviert (Domäne: **personal**). Bundle: `knowledge/` — Index: `knowledge/wiki/index.md`, Schema/Workflows: `knowledge/schema.md`, immutable Sources: `knowledge/sources/` (LLM liest, modifiziert NIEMALS).

<!-- agent-meta:managed-end -->

## Eigene Notizen

Hier kannst du eigene, projektspezifische Notizen eintragen. Dieser Bereich wird von `agent-meta` nicht überschrieben!

<!-- agent-meta:bootstrap-begin -->

## Agent Bootstrap — Session-Start Pflicht

Gemini/Antigravity benötigt eine einmalige Agent-Registrierung pro Session.
Lies alle `.md`-Dateien in `.gemini/agents` und registriere jeden Agenten unter seinem Dateinamen (ohne `.md`) via `define_subagent`.
Erst danach: Bearbeite User-Anfragen (Delegation an Orchestrator etc.).

> **Ohne diese Registrierung existieren die Agenten NICHT in der Runtime**
> und der Orchestrator kann nicht delegieren.
<!-- agent-meta:bootstrap-end -->


<!-- headroom:rtk-instructions -->
# RTK (Rust Token Killer) - Token-Optimized Commands

When running shell commands, **always prefix with `rtk`**. This reduces context
usage by 60-90% with zero behavior change. If rtk has no filter for a command,
it passes through unchanged — so it is always safe to use.

## Key Commands
```bash
# Git (59-80% savings)
rtk git status          rtk git diff            rtk git log

# Files & Search (60-75% savings)
rtk ls <path>           rtk read <file>         rtk grep <pattern>
rtk find <pattern>      rtk diff <file>

# Test (90-99% savings) — shows failures only
rtk pytest tests/       rtk cargo test          rtk test <cmd>

# Build & Lint (80-90% savings) — shows errors only
rtk tsc                 rtk lint                rtk cargo build
rtk prettier --check    rtk mypy                rtk ruff check

# Analysis (70-90% savings)
rtk err <cmd>           rtk log <file>          rtk json <file>
rtk summary <cmd>       rtk deps                rtk env

# GitHub (26-87% savings)
rtk gh pr view <n>      rtk gh run list         rtk gh issue list

# Infrastructure (85% savings)
rtk docker ps           rtk kubectl get         rtk docker logs <c>

# Package managers (70-90% savings)
rtk pip list            rtk pnpm install        rtk npm run <script>
```

## Rules
- In command chains, prefix each segment: `rtk git add . && rtk git commit -m "msg"`
- For debugging, use raw command without rtk prefix
- `rtk proxy <cmd>` runs command without filtering but tracks usage
<!-- /headroom:rtk-instructions -->

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
