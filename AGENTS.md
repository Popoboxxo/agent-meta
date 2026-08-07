# agent-meta

## Projekt

**Name:** agent-meta
**Präfix:** am
**Plattform:** Python CLI (sync.py)
**Beschreibung:** Zentrales Meta-Repository für die Standardisierung und Wiederverwendung von Claude-Agenten-Rollen über alle Projekte hinweg.

## Tech-Stack

- **Runtime:** Python 3.x
- **Sprache:** Python 3, Markdown, YAML
- **Key-Dependencies:** - Python: `>=3.8`

## Architektur

```
agents/
  0-external/       # Wrapper-Template für externe Skills
  1-generic/        # Universelle Agent-Templates
  2-platform/       # Plattform-Overrides (z.B. sharkord, homeassistant, agent-meta)
scripts/
  sync.py           # Agent-Generator
  admin-server.py   # Lokaler Admin-UI developer/)
external/           # Git Submodule (externe Skill-Repos)
docs/guides/        # Anleitungen und Beispiel-Config
docs/ui/            # UI Assets
  architecture/     # Architektur-Diagramme (Mermaid)
  admin-ui.html     # Admin-UI Frontend
tests/              # Test-Suite (automated, manual, orchestration)

```

**Entry-Point:**
```
scripts/sync.py — Haupt-CLI für Agent-Generierung
```

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


## Build & Development

```bash
# Build
python scripts/sync.py

# Tests
python scripts/sync.py --validate

# Dev-Stack starten
(kein Dev-Stack)

# Nach Änderungen neu laden
(kein Dev-Stack)
```

## Anforderungs-Kategorien

Kategorien für `docs/REQUIREMENTS.md`:

- Framework-Features (sync.py, neue Agenten-Rollen, Variablen)
- Agenten-Templates (Workflows, Sprach-Sektionen, Versionierung)
- Entwickler-Experience (Howto, Beispiele, Doku)



<!-- agent-meta:managed-begin -->
> **ROUTING:**


 Gemini->AGENTS.md
> **ENTRY:** `orchestrator`-Agent (für alle Dev-Tasks).
`agent-meta v0.92.0` | DoD: `rapid-prototyping` | REQ-Trace: `false`


## Regeln

# Branch-Guard

Verwende Feature-Branches (`feat/`, `fix/`, `chore/`). Keine Code-Änderungen direkt auf `main` oder `master`.

## Bekannte Grenzen

Die technische Durchsetzung (`orchestrator-guard.sh`) erkennt Git-Mutationen über eine Regex-/shlex-basierte Analyse des Bash-Befehls, kein vollständiger Shell-Parser. Bekannte Lücken: `eval "git commit ..."` wird nicht erkannt, direkte Schreibzugriffe auf `.git/` werden nicht geprüft, andere Git-Tools (`hub`, `gh repo ...`) sind nicht erfasst. Bewusster Trade-off, kein Bug (siehe Kommentar in `.claude/hooks/orchestrator-guard.sh:18-30`) — nur relevant für Nutzer, die sich vollständig auf den Schutz statt auf die Konvention verlassen.



# Commit-Konventionen

Verwende Conventional Commits (feat, fix, chore).
Beschreibungssprache: `Englisch`
Max 72 Zeichen in erster Zeile. Imperativ.
Format: `<type>: <beschreibung>` (Bsp: `feat: ...`)



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



# CRITICAL GATE
MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`. Keine Ausnahmen.

## Git Delegation
Git Mutationen (commit, push, add etc) -> `git` Agent. Read-only (status, log) im Main Chat ok.

Native Extensions (Skills/Hooks) erlaubt, ignorieren nicht Branch-Guard/DoD.

Anti-Recursion: Worker dürfen nicht an `orchestrator` zurück delegieren.



# agent-meta — Schichten-Architektur

Dieses Repo ist das Meta-Repository für Agenten-Standards. Jede Änderung an Templates
wirkt sich auf alle Projekte aus die dieses Submodul einbinden.

## Schichten-Modell

```
0-external/   Externe Skill-Agenten aus Drittrepos (via Git Submodule).
              Höchste Priorität. Konfiguriert in config/skills-registry.yaml.
              approved: true/false — Meta-Maintainer Quality Gate.

1-generic/    Universell. Gilt für jedes Projekt. Wird immer generiert,
              solange kein Override in 2-platform oder 3-project existiert.

2-platform/   Plattformspezifisch. Überschreibt den Generic-Agent für alle
              Projekte auf dieser Plattform.
              Modi: Full-replacement (kein extends:) oder Composition (extends: + patches:)

3-project/    Projektspezifisch.
              - <rolle>.md      → Override: ersetzt generierten Agent komplett
              - <rolle>-ext.md  → Extension: additiv geladen vom generierten Agent
```

**Override-Reihenfolge:**
```
1-generic  →  2-platform  →  3-project/<rolle>.md  →  0-external (eigenständige Rollen)
```

## Composition-Syntax (2-platform und 3-project)

```yaml
extends: "1-generic/<rolle>.md"
patches:
  - op: append-after        # nach Section einfügen
    anchor: "## Section"
    content: |
      ## Neue Section ...
  - op: replace             # Section vollständig ersetzen
    anchor: "## Section"
    content: |
      ## Section ...
  - op: delete              # Section entfernen
    anchor: "## Section"
  - op: append              # ans Dateiende anhängen
    content: |
      ## Anhang ...
```

Composition wird zur Build-Zeit aufgelöst — das generierte `.gemini/agents bzw. .opencode/agents/<rolle>.md`
enthält das vollständige Dokument. Kein `extends:` im Output.

## Abhängigkeitsprinzip

Jede Änderung an einer Quelldatei propagiert in alle instanziierten Projekte
beim nächsten `sync.py`-Lauf. Daher:

- **1-generic geändert** → alle Projekte neu syncen
- **2-platform geändert** → alle Projekte auf dieser Plattform neu syncen
- **config/role-defaults.yaml geändert** → alle Projekte neu syncen
- **config/skills-registry.yaml geändert** → alle betroffenen Projekte neu syncen

## Platzhalter-Escape

Für Dokumentation in Templates: Ein Platzhalter kann escaped werden, indem sein
Variablenname zusätzlich in Prozentzeichen eingeschlossen wird, direkt innerhalb
der doppelten geschweiften Klammern (Reihenfolge: zwei öffnende geschweifte
Klammern, Prozentzeichen, VARIABLENNAME, Prozentzeichen, zwei schließende
geschweifte Klammern). `sync.py` erkennt diese Schreibweise, entfernt beim
Rendern die beiden Prozentzeichen wieder und lässt den reinen Platzhalter
unverändert und unsubstituiert im generierten Output stehen — so kann ein
Platzhalter-Beispiel literal in Doku-Templates erscheinen, ohne selbst ersetzt
zu werden. Exakte Implementierung: `scripts/lib/config.py::substitute()`.

**Hinweis für Doku-Autoren:** Der escapte Token selbst darf hier in dieser
Quelldatei nicht als roher, verarbeitbarer Text auftauchen — jedes Vorkommen
würde von `substitute()` beim nächsten Sync genauso entschärft wie ein echter
Platzhalter, wodurch die Doku ihr eigenes Beispiel unsichtbar macht.



# agent-meta — Development Conventions

## Hard Invariants

1. `.gemini/agents bzw. .opencode/agents` is generated output — never edit manually. Make changes in `agents/` or `.meta-config/project.yaml`.
2. Bump agent version in frontmatter on every content change:
   - Major (`X.0.0`): renamed variable, changed behavior, new mandatory section
   - Minor (`x.Y.0`): new optional section, expanded scope
   - Patch (`x.y.Z`): text improvements, clarifications, config path fixes
   - Platform agents (`2-platform/`) also keep `based-on` up to date.
3. Placeholders are always `{{GROSS_MIT_UNTERSTRICH}}`. Lowercase or mixed case will not match.

## Naming-Konvention (Frontmatter `name:`)

Generische Templates in `agents/1-generic/` verwenden `name: template-<rolle>`. Ausnahme:
SE-Rollen (`se-*.md`) verwenden `name: se-<rolle>` ohne `template-`-Präfix — bewusste
Abweichung, um SE-Cascade-spezifische Rollen visuell von generischen Rollen zu
unterscheiden (Audit #412). Keine funktionale Abhängigkeit vom Präfix — reine Konvention,
nirgends in `scripts/lib/` oder den Consistency-Checks geprüft. Neue Rollen außerhalb der
SE-Kaskade folgen der Standardkonvention; weitere Ausnahmen sollten hier dokumentiert werden.

## Composition-Risiko: Instruction Bleed

Bei `extends + patches` in `2-platform/` und `3-project/` gilt:

**Instruction Bleed:** Text-Level-Composition kann Behavioral-Logic ungewollt zwischen Schichten übertragen — ein `append-after` an einer Section, die in einer anderen Schicht semantisch umdefiniert wurde, produziert widersprüchliche Instruktionen im generierten Agent.

**Prüfpunkte vor einem Patch-Commit:**
- Überschreibt der Patch eine Section, die in der übergeordneten Schicht eine andere Semantik trägt?
- Erzeugt `append-after` doppelte oder widersprüchliche Regelaussagen?
- Ist der Override vollständig (replace) oder additiv (append-after)? Additiv = höheres Bleed-Risiko.

> Empirische Grundlage: Instruction Bleed Paper (arXiv:2606.26356) belegt Cross-Module-Interference bei Text-Level-Composition als häufige Fehlerquelle.

## Adding a New Agent Role

Manual (required):
1. Create `agents/1-generic/<role>.md` with frontmatter: `name`, `version`, `description`, `hint`, `tools`
2. Add entry in `config/role-defaults.yaml`
3. Update `howto/setup/instantiate-project.md`

Auto-generated by `sync.py` (never edit manually):
- `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.continue/config.yaml`
- `.*/agents/*.md`
- `docs/agent-graph.html`, `docs/agent-mindmap.md`
- `.*/rules/conventions.md`
- `config/project-config.schema.json` roles enum

Only `1-generic/<role>.md`, `config/role-defaults.yaml`, and `howto/setup/instantiate-project.md` are maintained manually.

## Adding a New Placeholder

1. Add to `scripts/lib/config.py` → `build_variables()` or `_inject_dod()`
2. Document in `CLAUDE.md` variables table
3. Add to `howto/project.yaml.example` (optional)

## Change Checklist (before commit)

| Changed | Check |
|---|---|
| `1-generic/<role>.md` | bump version; sync affected projects |
| `2-platform/<platform>-<role>.md` | `version` and `based-on` current? |
| `agents/0-external/_skill-wrapper.md` | re-sync all enabled skills |
| `config/skills-registry.yaml` | re-sync projects |
| `config/role-defaults.yaml` (new role) | update CLAUDE.md + howto files |
| `config/project-config.schema.json` | test IDE autocomplete / jsonschema |
| `hint:` in agent template | sync projects (regenerates `AGENT_HINTS`) |
| `rules/` or `hooks/` | sync projects (overwrites generated copies) |



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

## Neue Funktionen: Smart Context Regeneration

### --check Flag (CI-Mode)

```bash
python .agent-meta/scripts/sync.py --check
python .agent-meta/scripts/sync.py --dry-run --check
```

**Verhalten:**
- Exit Code `0` wenn provider context files (CLAUDE.md, AGENTS.md, GEMINI.md, etc.) aktuell sind
- Exit Code `1` wenn Dateien regeneriert werden müssten
- Keine Dateien geschrieben (pure Status-Abfrage)

**Einsatz in CI:** Blockiert PRs wenn `.meta-config/project.yaml` verändert wurde und context files noch nicht neu generiert wurden.

**Vorteil:** Verhindert Drift zwischen Konfiguration und generiertem Projektkontext — besonders wichtig bei Multi-Provider-Setups.

### context-hashes.json (Drift-Erkennung)

Neuer Sidecar-Datei: `.meta-config/context-hashes.json`

```json
{
  "version": 1,
  "hashes": {
    "claude": "sha256:abc123...",
    "gemini": "sha256:def456...",
    "continue": "sha256:ghi789..."
  }
}
```

**Zweck:** Speichert Hashes der generierten statischen Header, um zu erkennen ob der User die Datei manuell bearbeitet hat (Drift).

**Verhalten:**
- Wird bei jedem Sync aktualisiert
- Bei Drift → Backup erstellt (`.CLAUDE.md.sync-backup-<timestamp>`) mit Warnung
- User kann Backup reviewen und Änderungen manuell merge

**WICHTIG: Mit Git committen** — ermöglicht Drift-Erkennung über Rechner und CI hinweg.

**Nicht gitignoren.**

### sync-on-config-change Hook (Automatische Re-Sync)

Neuer Hook in `hooks/1-generic/sync-on-config-change.sh`

**Trigger:** PostToolUse — reagiert auf Write/Edit-Operationen die `.meta-config/project.yaml` verändern

**Aktion:** 
- Erkennt wenn Projekt-Config geändert wurde (z.B. neue Provider hinzugefügt, Rolle aktiviert)
- Schreibt Lifecycle-Task für `agent-meta-manager` in `.claude/pending-tasks.md`
- `agent-meta-manager` merkt beim nächsten Start dass sync.py erneut laufen muss

**Konfiguration in project.yaml:**

```yaml
lifecycle-triggers:
  on-config-change:
    - agent: agent-meta-manager
      task: "Re-run sync.py — project.yaml has changed."

hooks:
  sync-on-config-change:
    enabled: true
```

**Vorteil:** Keine manuellen Sync-Aufrufe nötig wenn Konfiguration sich ändert — vollautomatische Reconciliation.

---

## Zusammenfassung: Provider Context Lifecycle

```
Developer ändert .meta-config/project.yaml
        ↓
sync-on-config-change Hook erkennt änderung
        ↓
lifecycle_check.py schreibt pending-task für agent-meta-manager
        ↓
agent-meta-manager führt sync.py aus
        ↓
sync.py vergleicht context-hashes.json mit aktuellen Hashes
        ↓
Drift erkannt? → Backup + Regeneration
Kein Drift? → Stille Aktualisierung der managed blocks
        ↓
.meta-config/context-hashes.json aktualisiert
```



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

## Agent-Hinweise

Honcho bietet persistentes Cross-Session-Memory. Verwende diese Tools immer, wenn du Informationen über frühere Interaktionen, Architektur-Entscheidungen oder Nutzer-Präferenzen über Sessions hinweg benötigst oder speichern musst.
get_context: Wann nutzen? Um den aktuellen Sitzungskontext zu Beginn der Aufgabe zu laden. search: Wann nutzen? Bei Recherchen zu vergangenem Code oder historischen Entscheidungen. create_conclusion: Wann nutzen? Nach Abschluss eines komplexen Tasks, um Learnings für zukünftige Sessions dauerhaft zu speichern. list_conclusions: Wann nutzen? Um bestehende Learnings vor einer Implementierung abzurufen. chat: Wann nutzen? Für direkte Konversation mit dem Honcho-Backend bei Unklarheiten im Kontext. get_representation: Wann nutzen? Um auf personalisierte Nutzer-Einstellungen zuzugreifen.
Destruktive Tools (delete_conclusion, set_config) sind gesperrt.

## Verbindungstyp

- Typ: `sse`
- URL: `{{MCP_HONCHO_URL}}` — Wert aus `secrets.local.yaml`

---

*Generiert von agent-meta aus `config/mcp-registry.yaml` — nicht manuell bearbeiten.*



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

## Agent-Hinweise

Browser-Automation für E2E-Flows, visuelle Regression und Accessibility-Audits.
browser_navigate: zur Ziel-URL navigieren.
browser_snapshot: Accessibility-Baum der Seite erfassen (Basis für a11y-Audit und stabile Selektoren).
browser_click/browser_type/browser_fill_form: User-Interaktionen im Flow simulieren.
browser_take_screenshot: visuelle Regression via Screenshot-Vergleich.
browser_network_requests/browser_console_messages: Netzwerk und Konsole inspizieren.
Arbiträre Code-Ausführung (browser_run_code_unsafe, browser_evaluate) ist gesperrt.

## Verbindungstyp

- Typ: `stdio`
- Kommando: `npx @playwright/mcp@latest`

---

*Generiert von agent-meta aus `config/mcp-registry.yaml` — nicht manuell bearbeiten.*



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

## Agent-Hinweise

ReqogniLoom ist die Single-Source-of-Truth für Requirements, Architektur und Test-Traceability. Verwende es immer, wenn du Features validieren oder Architekturentscheidungen nachvollziehen musst.
requirement.query/get: Wann nutzen? Zu Beginn jeder Aufgabe, um Anforderungen und deren Kontext zu verstehen. requirement.create/update/decompose/derive: Wann nutzen? Während der Planungsphase, um große Features in überprüfbare Requirements zu zerlegen. architecture.*, test.*: Wann nutzen? Beim Systemdesign (Architecture) und TDD-Prozess (Tests) zur Verknüpfung mit Code. traceability.query/suggest_links: Wann nutzen? Beim Code-Review oder Validator-Gate, um die REQ-Abdeckung zu validieren. artifact.search/get_tree: Wann nutzen? Für tiefgreifende Recherchen über den gesamten Artefakt-Baum. ai_derivation.*: Wann nutzen? Wenn du komplexe, abstrakte Requirements systematisch in technische Sub-Tasks aufschlüsseln musst.
Schreibende Tools erfordern Editor- oder Admin-Rolle. Administrative/destruktive Namespaces (admin.*, user.*, etc.) sind aus Sicherheitsgründen hart blockiert.

## Verbindungstyp

- Typ: `sse`
- URL: `{{MCP_REQOGNILOOM_URL}}/mcp/sse/` — Wert aus `secrets.local.yaml`

---

*Generiert von agent-meta aus `config/mcp-registry.yaml` — nicht manuell bearbeiten.*



# MCP: viz-logger

> agent-meta visualization event logger — tracks agent_start, delegate_out, agent_end for graph generation

---

## Erlaubte Tools

- `log_viz_event`

## Agent-Hinweise

Nutze log_viz_event um Agenten-Starts, Delegationen und Beendigungen zu protokollieren.
Parameter: event (agent_start|delegate_out|agent_end), agent, provider, status, target, caller, task_id, payload.

## Verbindungstyp

- Typ: `stdio`
- Kommando: `python scripts/viz-logger.py --mcp`

---

*Generiert von agent-meta aus `config/mcp-registry.yaml` — nicht manuell bearbeiten.*





## Agent Directory
> ⚠️ **ACHTUNG:** Agenten (Prompts) liegen in `.gemini/agents bzw. .opencode/agents`.

| Agent | Core Capabilities |
|-------|-------------------|

| `accessibility-specialist` | WCAG 2.1/2.2 Compliance-Audit, ARIA-Checks, Keyboard-Navigation, Screenreader... |

| `agent-meta-manager` | agent-meta verwalten: Upgrade, Sync, Feedback, projektspezifische Agenten anl... |

| `agent-meta-scout` | Claude-Ökosystem scouten: neue Skills, Rollen, Rules und Patterns entdecken |

| `api-specialist` | OpenAPI/Contract-First API Design, Schnittstellen-Spezifikationen. |

| `bug-feature-analyzer` | Issue-Triage: Eingehende Bug-Meldungen und Feature-Requests analysieren und k... |

| `claude-expert` | Absoluter Analyse-Experte für die Plattform Claude Code: Funktionsweise, Konf... |

| `code-reviewer` | Clean Code Gatekeeper: Blast-Radius-Analyse, SOLID/DRY Prüfung, Code-Qualität... |

| `concept-reviewer` | Konzept-Critic: reviewt Design-Docs und Konzepte auf Vollständigkeit, Logik, ... |

| `continue-expert` | Absoluter Analyse-Experte für die Plattform Continue: Funktionsweise, Konfigu... |

| `copilot-expert` | Absoluter Analyse-Experte für die Plattform GitHub Copilot: Funktionsweise, K... |

| `data-engineer` | ETL/ELT-Pipelines, Schema-Migration (Datenebene), Data-Quality-Checks, Lineag... |

| `dependency-auditor` | Supply-Chain-Hygiene: SBOM-Analyse, Lizenz-Kompatibilität, Version-Drift und ... |

| `developer` | Feature-Implementierung und Bugfixes |

| `devops-engineer` | CI/CD, Infrastructure as Code, Kubernetes, Observability. |

| `docker` | Dev-Stack verwalten, Test-Stack starten, Binary-Management, Dockerfiles erste... |

| `documenter` | CODEBASE_OVERVIEW, ARCHITECTURE, README, Erkenntnisse pflegen |

| `e2e-tester` | E2E-Tests, visuelle Regression und Accessibility-Audits via Playwright |

| `effort-estimator` | Schätzt Aufwände für Entwicklungsaufgaben basierend auf Task-Typ und LLM-Kali... |

| `explorer` | Read-only Codebase-Recherche, Dependency- und Impact-Mapping, Datei- und Symb... |

| `export-manager` | Target-agnostischer Output-Router: Markdown, Confluence, Jira-Xray, Notion. |

| `feedback` | Projekt-Feedback standardisieren: Bugs, Features, Verbesserungen als GitHub I... |

| `gemini-expert` | Absoluter Analyse-Experte für die Plattform Gemini (Antigravity): Funktionswe... |

| `git` | Commits, Branches, Tags, Push/Pull und alle Git-Operationen |

| `ideation` | Neue Ideen explorieren, Vision schärfen, Übergabe an requirements |

| `incident-responder` | Live-Incident-Koordination: korreliert Logs und Metriken, führt Runbook-Schri... |

| `intern-developer` | [EASTER EGG / GAG] Der übereifrige Praktikant |

| `junior-developer` | Triviale Code-Änderungen (≤2 Dateien, kein Architektur-Impact) |

| `knowledge-curator` | Strategische Knowledge-Engine-Steuerung: Schema-Evolution, Wiki-Strukturierun... |

| `knowledge-gardener` | Kleinteilige Wiki-Pflege: Links reparieren, Tags harmonisieren, Frontmatter e... |

| `knowledge-indexer` | Pflegt index.md (Content-Katalog, OKF §6) und log.md (Chronologisches Event-L... |

| `knowledge-ingestor` | Sources einlesen, Key Information extrahieren, Wiki-Seiten erstellen/ aktuali... |

| `knowledge-linter` | Wiki-Gesundheitscheck: Widersprüche, Orphans, veraltete Claims, kaputte Links... |

| `knowledge-migrator` | Vorhandene Projektinhalte aufräumen und OKF-konform ins Knowledge Wiki migrieren |

| `knowledge-querier` | Fragen gegen das Knowledge Wiki beantworten |

| `log-analyzer` | System- und Applikations-Logs analysieren: Frequency-Clustering, Severity-Kla... |

| `mammouth-expert` | Absoluter Analyse-Experte für die Plattform Mammouth Code: Funktionsweise, Ko... |

| `meta-feedback` | Verbesserungsvorschläge für agent-meta als GitHub Issues einreichen |

| `opencode-expert` | Absoluter Analyse-Experte für die Plattform Opencode: Funktionsweise, Konfigu... |

| `orchestrator` | Einstiegspunkt für alle Entwicklungsaufgaben |

| `performance-optimizer` | Big-O Bottleneck-Identifikation und datengetriebene Performance-Optimierung. |

| `planner` | Umsetzungsplanung |

| `principal-developer` | Last-Resort-Eskalationsstufe |

| `prompt-engineer` | Der ultimative Experte für Prompt-Engineering |

| `refactoring-specialist` | Systematische großflächige Code-Transformation mit Sicherheitsnetz: Strangler... |

| `release` | Versioning, Changelog, Build-Artifact, GitHub Release erstellen |

| `requirements` | Anforderungen aufnehmen, REQ-IDs vergeben, REQUIREMENTS.md pflegen |

| `senior-developer` | Komplexe Features, Architektur-Entscheidungen, schwierige Bugs, Cross-Cutting... |

| `technical-writer` | Externe entwickler- und nutzergerichtete Doku: API-Referenzen, Getting-Starte... |

| `tester` | TDD, Test-Suite ausführen, Testabdeckung sichern |

| `ui-ux-designer` | UI-Spezifikationen, Mockups und Design-Systeme erstellen. |

| `validator` | Code gegen REQs prüfen, DoD-Checkliste, Traceability-Audit |


## Knowledge Engine

Die Knowledge Engine ist aktiviert. Domäne: **personal**.

**Bundle-Pfad:** `knowledge/`
| Pfad | Zweck |
|------|-------|
| `knowledge/schema.md` | Steuerungsdokument — Konventionen, Concept Types, Workflows |
| `knowledge/sources/` | Immutable Raw Sources — LLM liest, modifiziert NIEMALS |
| `knowledge/wiki/` | OKF Knowledge Bundle — LLM-owned, strukturiertes Wiki |
| `knowledge/wiki/index.md` | Content-Katalog aller Wiki-Seiten (OKF §6) |
| `knowledge/wiki/log.md` | Chronologisches Event-Log (OKF §7) |

### Knowledge-Agenten
- **Schema-Owner:** `knowledge-curator` verwaltet `knowledge/schema.md` und Concept-Type-Konventionen

### Knowledge-Workflows
- **Ingest:** Source in `knowledge/sources/` ablegen → `knowledge-ingestor` verarbeitet → Wiki aktualisiert
- **Query:** Frage stellen → `knowledge-querier` durchsucht Index → synthetisiert Antwort
- **Lint:** `knowledge-linter` prüft Wiki-Gesundheit (Widersprüche, Orphans, OKF-Compliance)
- **Migration:** `knowledge-migrator` räumt vorhandene Inhalte auf und migriert ins OKF-Format
- **Gardening:** `knowledge-gardener` pflegt Links, Tags, Typos, Timestamps

<!-- agent-meta:managed-end -->

## Eigene Notizen

Hier kannst du eigene, projektspezifische Notizen eintragen. Dieser Bereich wird von `agent-meta` nicht überschrieben!

<!-- agent-meta:bootstrap-begin -->

## Agent Bootstrap — Session-Start Pflicht

Gemini/Antigravity benötigt eine einmalige Agent-Registrierung pro Session.
**Führe folgende Schritte zu Beginn JEDER Session aus:**

1. Lies alle Agenten-Dateien aus `.gemini/agents/`:
   - `accessibility-specialist.md` → registriere als `accessibility-specialist`
   - `agent-meta-manager.md` → registriere als `agent-meta-manager`
   - `agent-meta-scout.md` → registriere als `agent-meta-scout`
   - `api-specialist.md` → registriere als `api-specialist`
   - `bug-feature-analyzer.md` → registriere als `bug-feature-analyzer`
   - `claude-expert.md` → registriere als `claude-expert`
   - `code-reviewer.md` → registriere als `code-reviewer`
   - `concept-reviewer.md` → registriere als `concept-reviewer`
   - `continue-expert.md` → registriere als `continue-expert`
   - `copilot-expert.md` → registriere als `copilot-expert`
   - `data-engineer.md` → registriere als `data-engineer`
   - `dependency-auditor.md` → registriere als `dependency-auditor`
   - `developer.md` → registriere als `developer`
   - `devops-engineer.md` → registriere als `devops-engineer`
   - `docker.md` → registriere als `docker`
   - `documenter.md` → registriere als `documenter`
   - `e2e-tester.md` → registriere als `e2e-tester`
   - `effort-estimator.md` → registriere als `effort-estimator`
   - `explorer.md` → registriere als `explorer`
   - `export-manager.md` → registriere als `export-manager`
   - `feedback.md` → registriere als `feedback`
   - `gemini-expert.md` → registriere als `gemini-expert`
   - `git.md` → registriere als `git`
   - `ideation.md` → registriere als `ideation`
   - `incident-responder.md` → registriere als `incident-responder`
   - `intern-developer.md` → registriere als `intern-developer`
   - `junior-developer.md` → registriere als `junior-developer`
   - `knowledge-curator.md` → registriere als `knowledge-curator`
   - `knowledge-gardener.md` → registriere als `knowledge-gardener`
   - `knowledge-indexer.md` → registriere als `knowledge-indexer`
   - `knowledge-ingestor.md` → registriere als `knowledge-ingestor`
   - `knowledge-linter.md` → registriere als `knowledge-linter`
   - `knowledge-migrator.md` → registriere als `knowledge-migrator`
   - `knowledge-querier.md` → registriere als `knowledge-querier`
   - `log-analyzer.md` → registriere als `log-analyzer`
   - `mammouth-expert.md` → registriere als `mammouth-expert`
   - `meta-feedback.md` → registriere als `meta-feedback`
   - `opencode-expert.md` → registriere als `opencode-expert`
   - `orchestrator.md` → registriere als `orchestrator`
   - `performance-optimizer.md` → registriere als `performance-optimizer`
   - `planner.md` → registriere als `planner`
   - `principal-developer.md` → registriere als `principal-developer`
   - `prompt-engineer.md` → registriere als `prompt-engineer`
   - `refactoring-specialist.md` → registriere als `refactoring-specialist`
   - `release.md` → registriere als `release`
   - `requirements.md` → registriere als `requirements`
   - `senior-developer.md` → registriere als `senior-developer`
   - `technical-writer.md` → registriere als `technical-writer`
   - `tester.md` → registriere als `tester`
   - `ui-ux-designer.md` → registriere als `ui-ux-designer`
   - `validator.md` → registriere als `validator`

2. Registriere jeden Agenten via define_subagent API-Call:
   ```
   define_subagent(name="accessibility-specialist", ...)
   define_subagent(name="agent-meta-manager", ...)
   define_subagent(name="agent-meta-scout", ...)
   define_subagent(name="api-specialist", ...)
   define_subagent(name="bug-feature-analyzer", ...)
   define_subagent(name="claude-expert", ...)
   define_subagent(name="code-reviewer", ...)
   define_subagent(name="concept-reviewer", ...)
   define_subagent(name="continue-expert", ...)
   define_subagent(name="copilot-expert", ...)
   define_subagent(name="data-engineer", ...)
   define_subagent(name="dependency-auditor", ...)
   define_subagent(name="developer", ...)
   define_subagent(name="devops-engineer", ...)
   define_subagent(name="docker", ...)
   define_subagent(name="documenter", ...)
   define_subagent(name="e2e-tester", ...)
   define_subagent(name="effort-estimator", ...)
   define_subagent(name="explorer", ...)
   define_subagent(name="export-manager", ...)
   define_subagent(name="feedback", ...)
   define_subagent(name="gemini-expert", ...)
   define_subagent(name="git", ...)
   define_subagent(name="ideation", ...)
   define_subagent(name="incident-responder", ...)
   define_subagent(name="intern-developer", ...)
   define_subagent(name="junior-developer", ...)
   define_subagent(name="knowledge-curator", ...)
   define_subagent(name="knowledge-gardener", ...)
   define_subagent(name="knowledge-indexer", ...)
   define_subagent(name="knowledge-ingestor", ...)
   define_subagent(name="knowledge-linter", ...)
   define_subagent(name="knowledge-migrator", ...)
   define_subagent(name="knowledge-querier", ...)
   define_subagent(name="log-analyzer", ...)
   define_subagent(name="mammouth-expert", ...)
   define_subagent(name="meta-feedback", ...)
   define_subagent(name="opencode-expert", ...)
   define_subagent(name="orchestrator", ...)
   define_subagent(name="performance-optimizer", ...)
   define_subagent(name="planner", ...)
   define_subagent(name="principal-developer", ...)
   define_subagent(name="prompt-engineer", ...)
   define_subagent(name="refactoring-specialist", ...)
   define_subagent(name="release", ...)
   define_subagent(name="requirements", ...)
   define_subagent(name="senior-developer", ...)
   define_subagent(name="technical-writer", ...)
   define_subagent(name="tester", ...)
   define_subagent(name="ui-ux-designer", ...)
   define_subagent(name="validator", ...)
   ```

3. Erst danach: Bearbeite User-Anfragen (Delegation an Orchestrator etc.)

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
