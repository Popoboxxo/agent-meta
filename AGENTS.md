# agent-meta

## Projekt

**Name:** agent-meta
**Präfix:** am
**Plattform:** Python CLI (sync.py)
**Beschreibung:** Zentrales Meta-Repository für die Standardisierung und Wiederverwendung von Claude-Agenten-Rollen über alle Projekte hinweg.

> Struktur: siehe Verzeichnisstruktur im Repo (`ls`/`find`); deklarativ: `.meta-config/project.yaml` → `variables.PROJECT_STRUCTURE`.

> Runtime & Abhängigkeiten: siehe Projekt-Manifest (`pyproject.toml` / `requirements.txt` / `package.json` / `manifest.json`).

**Entry-Point:** `scripts/sync.py — Haupt-CLI für Agent-Generierung`

**Besondere Patterns:**
- Agent-Templates haben YAML-Frontmatter (name, version, description, tools)
- Platzhalter {{VARIABLE}} werden von sync.py substituiert
- Extensions (.claude/3-project/*-ext.md) werden vom Agenten zur Laufzeit gelesen
- Snippet-Dateien haben eigenes YAML-Frontmatter (snippet, version, language, runtime)


## Code-Konventionen

- Python: PEP 8, snake_case, klare Funktionsnamen
- Keine externen Python-Dependencies außer Stdlib
- Markdown-Dateien: GitHub Flavored Markdown
- YAML Frontmatter in allen Agent-Templates
- Provider-Unterschiede im Syncer-Code über Config-Keys/Capability-Flags ausdrücken, nie über `if provider == "Name"` (siehe `provider-agnostic`-Skill)


> Build: `python scripts/sync.py` · Test: `python3 scripts/sync.py --validate` · Dev: `(kein Dev-Stack)` · Reload: `(kein Dev-Stack)`

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
`agent-meta v0.101.0-beta.5` | DoD: `rapid-prototyping` | REQ-Trace: `false`



## Regeln

# Branch-Guard

Verwende Feature-Branches (`feat/`, `fix/`, `chore/`). Keine Code-Änderungen direkt auf `main` oder `master`.

## Guard-Terminologie: Convention Boundary vs. Security Boundary

Guards im System (Orchestrator-Guard, DoD-Push-Check, etc.) werden inkonsistent als
"Konventions-Tool" und als "security boundary" bezeichnet — beide Aussagen sind korrekt,
aber gegen unterschiedliche Bedrohungsmodelle:

- **Convention boundary**: fail-closed gegen AKZIDENTIELLEN Missbrauch (Tippfehler,
  vergessene Bestätigungen, naive Automatisierung). Nicht darauf ausgelegt, einen
  gezielten Bypass-Versuch zu widerstehen (siehe Lücken unten, z.B. #592).
- **Security boundary**: fail-closed gegen einen DELIBERATEN Umgehungsversuch.

Diese Definition ist die zentrale Referenz — Hook-Header und andere Doku sollen sie
verlinken (`.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary`)
statt sie ad hoc zu wiederholen.

`orchestrator-guard.sh` ist primär eine **convention boundary** (siehe Lücken unten),
mit einzelnen **security-boundary**-Eigenschaften für spezifische Fälle (z.B. das
Destructive-Gate aus #516, das auch bei gültigem `git`-Sentinel blockt). `dod-push-check.sh`
ist als **security boundary** gegen fehlendes/kaputtes `python3` fail-closed (#595).

## Bekannte Grenzen

Die technische Durchsetzung (`orchestrator-guard.sh`) erkennt Git-Mutationen über eine tokenisierte Analyse des Bash-Befehls (gemeinsamer Tokenizer für Destructive- und Mutation-Gate, Issue #551), kein vollständiger Shell-Parser. Bekannte Lücken:

1. `eval "git commit ..."` wird nicht erkannt.
2. Direkte Schreibzugriffe auf `.git/` werden nicht geprüft.
3. Andere Git-Tools (`hub`, `gh repo ...`) sind nicht erfasst.
4. Command-Substitution und Indirektion (`$(...)`, Backticks, `xargs`, `eval`) können eine Git-Mutation am Tokenizer vorbeischleusen, weil der Hook den Befehl weder ausführt noch die Shell vollständig parst (Issue #592). Ein echter Shell-Interpreter wäre unverhältnismäßig für ein Konventions-Tool.

Bewusster Trade-off, kein Bug (siehe Kommentar-Header in `.claude/hooks/orchestrator-guard.sh`) — nur relevant für Nutzer, die sich vollständig auf den Schutz statt auf die Konvention verlassen.



# Commit-Konventionen

Verwende Conventional Commits (feat, fix, chore).
Beschreibungssprache: `Englisch`
Max 72 Zeichen in erster Zeile. Imperativ.
Format: `<type>: <beschreibung>` (Bsp: `feat: ...`)



# Definition of Done (DoD)

Pflicht: Code komplett, Konventionen & Conv. Commits eingehalten, keine Regressions.



# Sprachregeln

| Kontext | Sprache |
|---|---|
| User-Kommunikation | **Deutsch** |
| User-Input | **Deutsch** |
| Externe Doku | **Englisch** |
| Interne Doku | **Deutsch** |
| Code/Commits | **Englisch** |



# MCP Hard Prohibitions

> Kurzfassung der harten Tool-Verbote aktiver MCP-Server. Vollständige Tool-Listen und
> Hinweise: pro Provider in `.gemini/skills bzw. .opencode/skills bzw. .agents/skills bzw. .zcode/skills bzw. .kimi-code/skills` — jeweils `mcp-<server>/SKILL.md` (`use-lazy-rules.md`).

- **honcho:** `delete_conclusion`, `set_config` — absolut verboten.
- **playwright:** `browser_run_code_unsafe`, `browser_evaluate`, `browser_file_upload`, `browser_handle_dialog` — absolut verboten.
- **reqogniloom:** `workspace.close`, `workspace.reactivate`, `workspace.delete`, `permissions.set_rule`, `permissions.list`, `permissions.revoke`, `permissions.check`, `admin.backup_create`, `admin.backup_list`, `admin.restore`, `audit.query`, `audit.ai_review`, `events.dlq_list`, `events.dlq_replay`, `user.create`, `user.assign_role`, `user.list`, `user.deactivate` — absolut verboten.



# No Worktree Isolation

**Anti-Pattern:** Niemals das Argument `isolation: "worktree"` beim Spawnen von Subagenten verwenden.
**Grund:** Agenten schreiben dann ihren Output in den internen Ordner `.claude/worktrees/agent-<id>/` anstatt in das eigentliche Projektverzeichnis. Das führt zu fehlgeleiteten Dateien und Datenverlust in der eigentlichen Codebase.

Alle Agenten müssen direkt im Projektverzeichnis arbeiten (Isolation deaktivieren oder weglassen). Der `.claude/` Ordner (sowie `.gemini/`, `.continue/`, `.mammouth/` etc.) ist strikt als Infrastruktur-Ordner zu betrachten und darf nicht für Arbeitskopien missbraucht werden.



# Lazy-Loaded Rules

> Nicht immer geladen — bei Bedarf per `Read` öffnen: `.gemini/skills bzw. .opencode/skills bzw. .agents/skills bzw. .zcode/skills bzw. .kimi-code/skills/<skill>/SKILL.md` (jeweils).

| Skill | Wann |
|---|---|
| sync-interface | sync.py, Templates/Rules ändern |
| admin-ui | Admin-Server/UI betreiben (Lifecycle, Token, Ports) |
| architecture | Templates/Overrides/Placeholder ändern |
| conventions | Vor Commits in agents/, config/, scripts/lib |
| submodule-protection | .agent-meta/, external/, .gitmodules |
| a2a-delegation-gates | A2A-Delegation an Subagenten |
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






## Übrige Regeln (Lazy-Load)

Nicht-Kern-Regeln werden NICHT in diesen Block eingebettet (Progressive Disclosure, #192):
sie liegen pro Provider als separate Dateien in .gemini/skills bzw. .opencode/skills bzw. .agents/skills bzw. .zcode/skills bzw. .kimi-code/skills — jeweils `<rule-name>/SKILL.md`.
Bei Bedarf mit `Read` laden; verfügbare Regeln via `ls` im jeweiligen Verzeichnis.


## Agent Directory
> Agenten (Prompts) liegen in `.gemini/agents bzw. .opencode/agents bzw. .codex/agents bzw. .zcode/agents bzw. .kimi-code/agents`.

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
| `test-executor` | Bestehende Test-Suiten ausführen — kein Test-Design, kein Code-Schreiben |
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
