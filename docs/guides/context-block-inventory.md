# Context-Block-Inventory (Issue #540, Phase A3)

> Intern. Klassifizierung jeder Quelle des AGENTS.md/CLAUDE.md-Managed-Blocks als
> Grundlage für Phase B (Partials komprimieren). Zeilenbereiche beziehen sich auf
> AGENTS.md Stand `1538c887` (Baseline: `docs/plans/issue-540-baseline.md`).

## Klassifizierungs-Regel

Zielregel aus dem Plan: *Discoverable via ls/find/Read → raus aus dem Context-File.
Instruktion/Konvention → drin bleiben (oder lazy laden).*

| Kategorie | Bedeutung | Behandlung bei compact |
|---|---|---|
| **INSTRUKTION** | Regeln, Verbote, Gates — beeinflusst Agenten-Verhalten direkt | bleibt embedded |
| **OVERVIEW** | Architektur-Bäume, Tech-Stack, Verzeichnisse, Beschreibungen, Changelog-artige Referenzen | raus bei compact (discoverable) |
| **METADATEN** | Verbindungsdetails, Pfade, Preset-/Config-Doku | kompakt oder Pointer |

## Kompositions-Kette (wie der Block entsteht)

```
templates/configs/AGENTS.project-template.md
├── {{> project-metadata }}                     ← Z1–79 (AUSSERHALB des Managed Blocks)
└── <!-- agent-meta:managed-begin -->
    {{PROVIDER_ROUTING}}                        ← aufgelöst aus templates/context/agents-managed.md:
    ├── {{> header }}                           ← Z81–87
    ├── {{#if HAS_NATIVE_RULES}}
    │     {{> rules-pointer }}                  ← Zweig hier deaktiv
    │   {{else}}
    │     {{> rules-embedded }}                 ← Z90–758 (Loop über rules/)
    ├── {{> agents-location }}                  ← Z760–761
    ├── {{> agents-table }}                     ← Z763–871
    └── {{> knowledge-engine-hints }}           ← Z873–894
<!-- agent-meta:managed-end -->
## Eigene Notizen                               ← Z898–900 (Template-Statik, User-Bereich)
<!-- agent-meta:bootstrap-begin --> … <!-- end -->   ← Z902–1025 (eigene Region, scripts/lib/bootstrap.py)
RTK-Headroom / graphify-Sektion                 ← Z1028–1082 (Fremdinjektionen, nicht sync.py)
```

Wichtig: Obwohl Gemini `has_rules: true` hat, erzeugen **alle** AGENTS.md-Provider denselben
embedded Block (`scripts/lib/context.py` — Ping-Pong-Vermeidung beim geteilten File).
Der `rules-pointer`-Zweig ist in diesem Repo damit inaktiv.

## Inventory: Partials und injizierte Quellen

### 1. `project-metadata.md` — AGENTS.md Z1–79 (außerhalb Managed Block)

| Sektion | Zeilen | Kategorie | Begründung / Plan-Bezug |
|---|---|---|---|
| `## Projekt` (Name, Präfix, Plattform, Beschreibung) | 3–8 | METADATEN | kompakt halten; Präfix wird aktiv genutzt (Branch-Namen) |
| `## Tech-Stack` | 10–14 | OVERVIEW | discoverable (pyproject/requirements); Fix 2 |
| `## Architektur` (Baum + Entry-Point + Patterns) | 16–44 | OVERVIEW | ls/find-discoverable; Paper: Repository-Overviews nutzlos; Fix 2 |
| `## Code-Konventionen` | 47–52 | INSTRUKTION | Verhaltensregeln für Code-Beiträge (PEP 8, Stdlib-only) |
| `## Build & Development` | 55–69 | OVERVIEW | discoverable; Fix 2: nur wenn nicht ableitbar |
| `## Anforderungs-Kategorien` | 71–77 | METADATEN | Pointer auf docs/REQUIREMENTS.md genügt |

### 2. `header.md` — Z81–87

| Inhalt | Zeilen | Kategorie | Begründung |
|---|---|---|---|
| ROUTING-Zeilen (Provider→Contextfile) | 82–85 | METADATEN | bereits kompakt; Routing-Metainfo |
| ENTRY `orchestrator` | 86 | INSTRUKTION | Routing-Pflicht, 1 Zeile — erhalten |
| Version/DoD/REQ-Trace-Zeile | 87 | METADATEN | Statuszeile, kompakt |

### 3. `rules-pointer.md` — aktuell inaktiv

Einzeiler („Regeln werden nativ geladen") = INSTRUKTION. Wird nur aktiv, wenn ein
Provider AGENTS.md exklusiv mit nativen Rules nutzt; hier deaktiv (s.o.).

### 4. `rules-embedded.md` — Loop-Inhalt Z90–758

#### 4a. Generic Rules (`rules/1-generic/*.md`) — Z92–239, ~150 Zeilen

Alle 14 Dateien: **INSTRUKTION** (bleibt embedded).

| Rule-Datei | AGENTS.md-Überschrift | Kategorie |
|---|---|---|
| a2a-delegation-gates.md | # A2A Anti-Re-Delegation Gates | INSTRUKTION |
| branch-guard.md | # Branch-Guard | INSTRUKTION (**D3-Pflicht-Anchor**) |
| commit-conventions.md | # Commit-Konventionen | INSTRUKTION (**D3-Pflicht-Anchor**) |
| dod-criteria.md | # Definition of Done (DoD) | INSTRUKTION |
| issue-lifecycle.md | # GitHub Issue Lifecycle | INSTRUKTION |
| language.md | # Sprachregeln | INSTRUKTION (**D3-Pflicht-Anchor**) |
| lifecycle-tasks.md | # Lifecycle-Tasks | INSTRUKTION |
| mcp-guardrails.md | # MCP Hard Prohibitions | INSTRUKTION (**D3-Pflicht-Anchor**, Verbote) |
| no-worktree-isolation.md | # No Worktree Isolation | INSTRUKTION |
| python-conventions.md | # Python Conventions | INSTRUKTION |
| session-conclusion.md | # Session-Abschluss | INSTRUKTION |
| submodule-protection.md | # Submodule-Schutzkonzept | INSTRUKTION |
| use-lazy-rules.md | # Lazy-Loaded Rules | INSTRUKTION |
| use-orchestrator.md | # CRITICAL GATE | INSTRUKTION (**D3-Pflicht-Anchor**) |

Die „Bekannte Grenzen"-Subsektionen (z.B. A2A Z100–107, Branch-Guard Z110–117) sind
Begründungs-Prosa zu den Regeln → bei Kompromittierung kürzbar, Kernregel muss als
Anchor erhalten bleiben.

#### 4b. Platform-Rules (`rules/2-platform/agent-meta-*.md`) — Z240–397, ~158 Zeilen

| Rule-Datei | Bereich | Kategorie | Begründung |
|---|---|---|---|
| agent-meta-architecture.md (Schichten-Architektur) | 240–319 | gemischt | Schichten-Modell/Composition-Syntax/Platzhalter-Escape = OVERVIEW (Referenz-Doku); Abhängigkeitsprinzip („Änderung propagiert in alle Projekte") = INSTRUKTION |
| agent-meta-conventions.md (Development Conventions) | 321–390 | gemischt | Hard Invariants („never edit generated output", Platzhalter-Syntax) = INSTRUKTION; Naming-Konvention, Instruction-Bleed-Checkliste, Adding-New-Role/Placeholder, Change-Checklist = OVERVIEW (Change-Zeitpunkt-Referenz, lazy ladbar) |
| agent-meta-provider-agnostic.md | 392–396 | INSTRUKTION | Kurzregel, kein Kürzungsbedarf |

#### 4c. `agent-meta-sync-interface.md` — Z398–513, ~116 Zeilen

**OVERVIEW.** Interface-Flags + Feature-Changelog („Smart Context Regeneration",
Lifecycle-Diagramm). Plan-Ist: „Changelog-Charakter = Ballast". Ersatz: Pointer auf
`.claude/skills/sync-interface/SKILL.md` bzw. `_wf-sync-interface` (#192-Territorium).

#### 4d. MCP-Sektionen — generiert, Z514–730, ~217 Zeilen

Quelle: `scripts/lib/mcp.py::_generate_rule_content()` aus `config/mcp-registry.yaml`,
eingebettet über den Rules-Loop (Registry: `rules/2-platform/agent-meta-mcp.yaml`).

Server: honcho (514–549), playwright (551–602), reqogniloom (604–703), viz-logger (705–729).

| Sub-Sektion je Server | Kategorie | Begründung / Plan-Bezug |
|---|---|---|
| `## Erlaubte Tools` | INSTRUKTION | Tool-Allowlist steuert Nutzung; Fix 1.3: bleibt |
| `## Verbotene Tools (ABSOLUT)` | INSTRUKTION | Verbote = hartes Do-not; Fix 1.3: bleibt |
| `## Agent-Hinweise` (Prosa) | OVERVIEW | usage-Prosa; Fix 1.3/B3: streichen bzw. 1 Zeile |
| `## Verbindungstyp` (URL/Kommando) | METADATEN | Connection-Details gehören in secrets/mcp-registry; Pointer genügt |
| Fußzeile „Generiert von …" | METADATEN | 1 Zeile, kann entfallen |

Größter Einzelposten: reqogniloom allein ~101 Zeilen (davon ~77 Tool-Listen).

#### 4e. External Tool graphify — generiert, Z731–758, ~28 Zeilen

Quelle: `scripts/lib/external_tools.py::_generate_tool_rule_content()` aus
`config/external-tools-registry.yaml`.

| Inhalt | Kategorie |
|---|---|
| Nutzungsregeln („erst `graphify query`", Skip-Bedingungen) | INSTRUKTION (B8: prüfen/kompaktieren) |
| Hook-Wrapper- und Injektions-Pfadlisten | METADATEN (Pointer) |

### 5. `agents-location.md` — Z760–761

**METADATEN.** 2 Zeilen Pfad-Pointer („Agenten liegen in `.gemini/agents bzw. .opencode/agents`").
Kann mit dem Directory verschmolzen werden.

### 6. `agents-table.md` — Z763–871, ~112 Zeilen

**OVERVIEW.** 53 Einträge mit vollständigen Beschreibungen, jeweils durch Leerzeile
getrennt (= ~53 Leerzeilen Ballast). Fix 1.2: `name` + max. 3 Keywords statt
Full-Description; Leerzeilen-Trennung mitentfernen halbiert zusätzlich.
Routing-relevante Ausnahme: `orchestrator`-Eintrag sollte als INSTRUKTION erhalten bleiben
(ENTRY-Duplikat, kann mit header.md fusionieren).

### 7. `knowledge-engine-hints.md` — Z873–894, ~22 Zeilen

Quelle: Variable `{{KNOWLEDGE_ENGINE_HINTS}}`.

| Inhalt | Kategorie | Begründung |
|---|---|---|
| Aktivierungs-Zeile + Bundle-Pfad | METADATEN | 2 Zeilen kompakt |
| Pfad-Tabelle (schema/sources/wiki) | METADATEN | Pointer auf `knowledge/wiki/index.md` genügt |
| Knowledge-Agenten + Workflows | OVERVIEW | discoverable im Bundle/schema; B8 |

### 8. Bootstrap-Block — Z902–1025, ~124 Zeilen (eigene Managed-Region)

Quelle: `scripts/lib/bootstrap.py::generate_gemini_bootstrap_instructions()`.
Gemini-spezifisch (Antigravity `define_subagent`-Registrierung).

**OVERVIEW** — die zwei expliziten 53-fachen Agentenlisten (`.md`-Aufzählung +
`define_subagent(name=…)`-Blöcke, ~106 der ~124 Zeilen) sind discoverable via
`ls .gemini/agents/`. B6: auf Kurzform reduzieren („Lies alle .md in .gemini/agents/
und registriere sie"), der Instruktionskern (Session-Start-Pflicht, Warnhinweis)
bleibt als ~5-zeilige INSTRUKTION erhalten.

### 9. Keine agent-meta-Quellen (außerhalb Sync-Scope, zur Vollständigkeit)

| Bereich | Quelle | Kategorie |
|---|---|---|
| `## Eigene Notizen` (Z898–900) | Template-Statik, User-Bereich | — (unverändert) |
| RTK-Headroom (Z1028–1069) | Headroom/RTK-Installer (Fremdinjektion, von sync.py als Foreign Content bewahrt) | INSTRUKTION (Drittanbieter, außerhalb Scope) |
| graphify-Sektion (Z1071–1082) | graphify-Installer (permitted injection) | INSTRUKTION (Drittanbieter, außerhalb Scope) |

## Provider-Vergleich

| File | Managed-Block-Inhalt | Zeilen (gesamt) |
|---|---|---:|
| AGENTS.md (Opencode + Gemini) | header + embedded Rules + MCP/External-Tool + Directory + Knowledge Hints | 1082 |
| MAMMOUTH.md | AI ROUTING + Metadaten + kompakte Agent-Tabelle („Zuständigkeit"-Format) + Knowledge Hints; Rules nativ (has_rules: true) | 173 |
| CLAUDE.md | AI ROUTING + Metadaten + Knowledge Hints; Rules nativ über `.claude/rules/`; kein Directory, kein Bootstrap, keine MCP-Embeds | 151 |

Phase-B-Änderungen an Partials/Rules wirken auf alle drei Files; der AGENTS.md-Block ist
der einzige große Hebel (siehe Baseline: 11001 von 14954 Tokens gesamt).

## Auswertung (komprimierungspotenzial AGENTS.md, ≈-Werte)

| Kategorie | Zeilen (≈) | Anteil | Behandlung |
|---|---:|---:|---|
| INSTRUKTION (bleibt) | ~290 | 27 % | Generic-Rules, Tool-Listen, ENTRY, Code-Konventionen, Hard-Invariant-Anteile |
| OVERVIEW (raus/kompaktierbar) | ~590 | 55 % | Overviews Z1–79, sync-interface, Directory, Bootstrap-Listen, MCP-Hinweise, Referenz-Anteile Platform-Rules |
| METADATEN (Pointer/kompakt) | ~120 | 11 % | Projekt-Kopf, Verbindungen, Knowledge-Pfade, Location |
| Rest (Statik/Fremdinjektionen) | ~80 | 7 % | Eigene Notizen, Marker, RTK/graphify |

Damit ist das Plan-Soll (AGENTS.md <200 inkl. B6, <400 ohne B6) rechnerisch erreichbar,
sofern OVERVIEW-fläche konsequent auf Pointer umgestellt und das Directory gekürzt wird.
