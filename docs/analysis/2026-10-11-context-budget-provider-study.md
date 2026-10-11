---
title: Context-Budget-Studie — was die 9 Provider tatsächlich laden und was es kostet
date: 2026-10-11
status: FINAL (Evidenzbasis, keine Spezifikation)
consumed-by: SPEC-CONTEXT-PROFILES-2026-10-11 (docs/specs/2026-10-11-context-profiles-spec.md)
related-spec: SPEC-CONTEXT-FILE-MODES-2026-09-13
builds-on: docs/plans/issue-540-baseline.md, docs/guides/context-block-inventory.md
---

# Context-Budget-Studie (9 Provider)

> Zweck: belastbare Evidenzbasis für die Spec `SPEC-CONTEXT-PROFILES-2026-10-11`. Diese Datei
> enthält Messungen, Quellenlage und Konfidenz — keine Designentscheidungen.
>
> **Konfidenz-Kennzeichnung:** `VERIFIED-RUNTIME` = an einer laufenden Runtime gegen einen
> Mock-LLM-Server gemessen (tatsächlich gesendete Request-Bytes). `VERIFIED-SOURCE` = aus
> Quellcode/Repo-Doku des Providers abgeleitet, nicht ausgeführt. `VERIFIED-DOCS` = offizielle Doku.
> `UNVERIFIED` = Drittquelle, Schlussfolgerung oder nicht prüfbar. Wo nichts angegeben ist,
> handelt es sich um eine Messung an den generierten Dateien (Bytes auf Platte).

## 1. Methodik

| Aspekt | Vorgehen |
|---|---|
| Messobjekt | Scratch-Projekte unter `.tmp/ctx-study` (je Provider und Kombination), generiert mit `sync.py` |
| Rollenbasis | **62 aktive Rollen** (die vollständige `role-defaults` hat 92; 60 davon geroutet) |
| Einheit | Bytes; Tokens ≈ Bytes/4 (grob). Whitespace tokenisiert billiger, daher ist die Token-Ersparnis durch JSON-Minify **kleiner** als die Byte-Ersparnis. Eine echte Tokenizer-Messung ist Phase-0-Aufgabe der Spec. |
| Runtime-Capture | opencode 1.19.0, codex-cli 0.162.1, Mammouth Code 1.18.31.1 — jeweils auf einen lokalen Mock-LLM-Server gerichtet, der die Request-Bodies mitschneidet (= Bytes, die wirklich an das Modell gehen) |
| Quellcode-Lektüre | Kimi Code: Repo `MoonshotAI/kimi-code@c9f01f07`; ZCode: `zai-org/ZCode@aac47556` + npm `zcode-app-cli@3.14.5-34` |
| Doku + Quellen | Claude Code, Gemini CLI/Antigravity, Continue, Copilot: offizielle Doku und Quellcode, soweit erreichbar |
| Grenze | Viele offizielle Doku-Sites waren über den Proxy gesperrt (HTTP 403). Betroffen u. a. Kimi-Doku, `docs.continue.dev`, `docs.github.com`, Antigravity-Doku. Ersatz: Repo-Markdown, Snippets, Audit-Zitate — entsprechend gekennzeichnet. |

## 2. Querschnitt: Größen der generierten Artefakte

### 2.1 Orchestrator (Claude-Render, 90,691 B, 2,472 Zeilen)

Quelle: Template `agents/1-generic/orchestrator.md` (24,349 B, Version 8.4.1); der Rest entsteht durch Substitution.

| Abschnitt | Bytes | Anteil |
|---|---:|---:|
| §3 Intent-Routing (`{{INTENT_ROUTING_TOOLS}}`-Payload + Prosa) | 56,756 | 62.6 % |
| `<context>` (inkl. Agent-Tabelle 5,781) | 6,772 | 7.5 % |
| §2a Pipeline-Stage-Detail | 6,178 | 6.8 % |
| Direkter Dispatch | 3,925 | 4.3 % |
| §4 Tier-Auswahl | 3,716 | 4.1 % |
| §9 Context-Guard / Checkpointing | 3,646 | 4.0 % |
| Status-Tabelle | 1,271 | 1.4 % |
| Singleton-Regel | 1,262 | 1.4 % |
| §12 Few-shot | 188 | 0.2 % |

§12 ist **nur ein 3-Zeilen-Pointer (188 B)** auf `_wf-orchestrator-reference.md` (1,355 B) — keine 8.5 KB inline (frühere Messaussage falsch, siehe §9).

Weitere große Agenten: `agent-meta-manager` 24,010 B; `security-auditor` 16,992 B; `control-framework-assessor` 13,906 B. Alle 62 Agentendateien: 577,850 B.

Duplizierte Boilerplate über die 62 Agentendateien ≈ 22,124 redundante Bytes: `background-process-guard` 342 B × 33 = 10,944 B; A2A-Envelope-Hinweis × 9 in zwei Varianten ≈ 5.7 KB.

### 2.2 Routing-Payload (§3, `{{INTENT_ROUTING_TOOLS}}`)

Pretty-JSON 55,170 B; YAML-Rendering 40,564 B (für Continue/Copilot/Mammouth/ZCode/KimiCode gemäß `handoff_format`).

| Teil | pretty | compact JSON | Bemerkung |
|---|---:|---:|---|
| `routing.rules` (60 Einträge) | 27,925 | 20,649 | Keyword-/Beispiel-Regeln |
| `routing.name_index` (61 Einträge) | 15,746 | 13,183 | Felder `agent`, `short_desc` (4,556 B, deutsch, 23 von 61 manuell mit „..." gekürzt), `tier`, `orchestrator_only`, `addressability`, `name_only_reason` (nur bei 2 Einträgen nicht leer: `intern-developer`, `template-auditor`) |
| `routing.pipelines` (7 Einträge) | 1,326 | – | |
| `tool{}`-Schema | 2,780 | – | davon `enum` 1,292 — **tot**, weil `route_intent_tool: false` für alle 9 Provider (`ROUTE_INTENT_CALLABLE=false`); der Prompt sagt selbst „kein natives route_intent-Tool registriert … Erfinde keinen Tool-Aufruf" |
| `routing` gesamt | – | 34,774 | |

Whitespace/Einrückung ≈ 19–21 % der Payload.

Bytes je Feld in `routing.rules`:

| Feld | Bytes | Beobachtung |
|---|---:|---|
| `keywords` | 4,743 | 300 Keywords |
| `examples` | 4,528 | 76 Beispiele; 47 Regeln mit 1, 10 mit 2, 3 mit 3; 55 von 76 enthalten ein eigenes Keyword der Rolle (kein neues Signal), 21 bringen Signal; 73 von 76 deutsch |
| `input_contracts` | 1,911 | wird von `consistency/handoff_contracts.py` aus `role-defaults.yaml` genutzt, nicht aus der Orchestrator-Datei; fürs Routing nicht nötig |
| `agent` | 1,028 | |
| `output_contract` | 740 | wie `input_contracts` |
| `tier` | 618 | 50 optional, 6 recommended, 4 required |
| `orchestrator_only` | 298 | |
| `parallel` | 263 | „rein informativ", nicht durchgesetzt |

Redundanz: Jede Rolle steht **4×** im Orchestrator (Enum, Rules, `name_index`, Agent-Tabelle) plus im Harness-Roster.

Keyword-Überlappung: nur 6 geteilte Keywords (`accessibility`, `a11y`, `audit`, `refactoring`, `design`, `post-mortem`), max. 33 % Überlappung, dokumentiert in `tests/test_routing_overlap.py`. Rolle-vs-Pipeline-Kollisionen:

| Rolle | Pipeline | Kollision |
|---|---|---|
| `bug-feature-analyzer` | `quick-fix` | „Triage" |
| `developer`, `refactoring-specialist` | `refactor` | „Refactoring" |
| `documenter` | `docs-update` | 4 geteilte Keywords |
| `ideation` | `concept-development` | „Konzept" |
| `incident-responder` | `quick-fix` | „Hotfix" |
| – | `bugfix` / `quick-fix` | Pipeline-vs-Pipeline |

Datenduplikat in der Quelle: `role-defaults.yaml` speichert Keywords doppelt (`routing.intent_keywords` und `routing_patterns.keywords`), identisch für 87 von 92 Rollen; festgenagelt durch `tests/test_routing_tool_definitions.py:47-64`, gelesen von `scripts/hermes_export.py:270`.

Datendefekt: `template-auditor` ist `name_only`, hat aber trotzdem eine Keyword-Regel (4 Keywords, `orchestrator_only`) — Widerspruch zum §3-Text „Rollen mit addressability: name_only tragen keine Keyword-/Beispiel-Regel". `tests/scenarios/asserts/76-template-auditor-role.sh:63-76` parst das Enum per Regex und schlägt fehl, wenn `template-auditor` darin steht — der Render enthält es (Assert veraltet/widersprüchlich; wird nicht ausgeführt).

### 2.3 Agent-Delegationstabelle (`AGENT_DELEGATION_TABLE`, 5,781 B)

Erzeugt in `config.py:1694-1710`, Partial `templates/context/partials/agents-table.md`. Defekte:
- doppelter verschachtelter Header: `| Agent | Responsibility | Tier | Parallel |` aus `orchestrator.md:266-267` **plus** der eigene Header des Partials `| Agent | Core Capabilities |`;
- im Nicht-compact-Modus Leerzeilen zwischen den Zeilen (ungültige Markdown-Tabelle; 66–68 Leerzeilen);
- Spalten Tier/Parallel werden nie gefüllt.

`COMPACT_MODE` entfernt nur diese Leerzeilen (~62 B).

### 2.4 Generierungspfad und maschinelle Parser

| Stelle | Rolle |
|---|---|
| `config.py:2066-2117` `build_variables` | Variablenaufbau |
| `delegation_table.py:164-299` `get_routing_rules` | Regeldaten |
| `agents.py:235-415` `build_routing_tool_definition` / Render (`json` \| `yaml_text_block`) | Payload |
| `agent_sync.py:474-528` `_build_provider_vars` | `ROUTE_INTENT_CALLABLE` (:512), `INTENT_ROUTING_TOOLS` (:519) |
| `delegation_syntax.py:600-609` | Delegationssyntax |
| `scripts/lib/consistency/placeholders.py:111-119` | Platzhalter-Registry |

Kein Runtime-Konsument parst das JSON außer dem LLM. Maschinelle Parser/Pins (Test-Churn-relevant):

| Test | Was gepinnt ist |
|---|---|
| `tests/test_orchestrator_name_dispatch.py:61-111` | parst JSON/YAML je `handoff_format`; `name_index` nicht leer, sortiert, `intern-developer` name_only |
| `tests/test_routing_tool_definitions.py` (570 Zeilen) | Tool-Definition, Keyword-Duplikat (:47-64) |
| `tests/test_routing_name_index.py` | `name_index` |
| `tests/test_developer_tiers_gate.py:44-65` | Tier-Felder |
| `tests/test_routing_overlap.py` | Keyword-Überlappung |
| `tests/test_role_addressability_coverage.py` | 92 Rollen: 88 keyword, 3 name_only, 1 excluded |
| `tests/test_delegation_table.py` | Delegationstabelle |
| `test_context_compact_mode.py:246-268` | compact-Verhalten |
| `tests/test_template_slimming_equivalence.py:1233-1283` | Golden `tests/fixtures/slimming-golden/orchestrator.md` (87,873 B), nur Claude, 58 Rollen; Konvention: Golden zusammen mit Template-Änderungen aktualisieren |

`{{#if VAR}}` wirkt nur für eine Whitelist von Variablennamen in `strip_inactive_conditional_blocks` (`config.py`); `COMPACT_MODE` ist **nicht** darin. Dieselbe Funktion läuft im nativen Rules-Pfad (`rules.py`) — eine Whitelist-Erweiterung darf native Rules nicht komprimieren (vgl. `docs/plans/issue-540-baseline.md`, Abschnitt „Mechanismus").

Es gibt **keinen Role-Routing-LLM-Eval**: `tests/routing-llm-eval` + `scripts/gen_routing_llm_eval_catalog.py` / `gen_promptfoo_config.py` testen nur **Pipeline**-Routing (exakter Ein-Wort-Match).

`scripts/lib/consistency/context_size.py` warnt, wenn eine Kontextdatei `context_file.max_lines` überschreitet (Default 250; dieses Repo: `compact`, 250, `oversize_acknowledged`); Agentendateien werden **nicht** geprüft.

### 2.5 Gerenderte Routing-Varianten (Stichprobe 6 Rollen; Größen für alle 60 Regeln)

| Format | keywords + 1. Beispiel | alle Beispiele | nur keywords |
|---|---:|---:|---:|
| A — Markdown-Tabelle | 8,991 | 10,278 | 6,006 |
| B — Einzeiler `agent\|flags\|keywords\|example` | 7,975 | 9,262 | 4,990 |
| C — gruppiert nach erfundenen Lanes | 8,936 | – | 5,531 |
| Ist: compact-JSON `routing` | 34,774 | | |
| Ist: pretty Payload | 55,170 | | |

B + Pipelines (606 B für 7) + Name-only-Zeile (210 B) ≈ 8.8 KB (−84 % der Payload; §3-Anteil am Orchestrator fiele von 62.6 % auf ≈ 9.7 %). Hochrechnung auf 88 Keyword-Rollen (× 1.47): B ≈ 11.7 KB, A ≈ 13.2 KB (Schätzung).

Beispielzeilen B:
```
developer|req|Bugfix,Refactoring,Implementierung,Code schreiben|Implementiere das Feature X.
template-auditor|orch-only,name-only|Agenten-Audit,...|Prüfe ob ...
```

### 2.6 Entry-File der AGENTS.md-Gruppe (Gemini, Opencode, Mammouth, Codex, ZCode, KimiCode)

Generierungsdefekte (Code):
- `context.py:1599-1625` baut `shared_users` aus dem **gesamten Katalog**, nicht aus aktiven Providern → ein Einzelprovider-Projekt Codex/Mammouth embedded Rules, weil Opencode/ZCode/KimiCode `has_rules:false` haben.
- `_shared()` verbindet Pfadlisten aller 6 mit „ bzw. " (4 Zeilen, 804 B, ~520 B entfernbar).
- Lazy-Kanal nur, wenn **jeder** Katalog-Teiler `skills_dir` hat (`context.py:317-336`, `1776-1799`).
- `compact_embedded_rule`: `context.py:1562-1585`, `1735-1752`, `1811-1817`.

| Variante | AGENTS.md Bytes | Bemerkung |
|---|---:|---|
| Codex/Opencode/Kimi full | 25,560–25,632 (503–504 Z., ~6.4k tok) | identisch ± 8 B |
| … compact | 22,571–22,643 | −11.7 % |
| … lazy | 16,745–16,813 | −34 % |
| ZCode | +914 | Bootstrap-Block L505–523 |
| Gemini full / compact / lazy | 33,037 / 23,032 / 24,230 | |
| Multi-Provider (6 AGENTS.md-Provider) full / compact | 34,035 (> 32,768) / 24,030 | |

Zusammensetzung (`codex_full`): Kopf/Projekt 1,148 B; eingebettete Rules `## Regeln` 16,486 B (64 %); Lazy-Tabelle + Gate + Git-Delegation + Agent Directory 7,805 B.

| Größte Sektionen | Bytes | Befund |
|---|---:|---|
| Agent Directory | 5,836–5,870 | 66–68 Leerzeilen; Provider-Listen-Boilerplate 172 B; dupliziert das Harness-Roster |
| A2A-Regel | 6,805 | davon „Bekannte Grenzen" 2,718 |
| Branch-Guard | 3,104 | davon Guard-Terminologie 1,193 + Bekannte Grenzen 1,785 — beschreiben einen Claude-Hook, anderswo irrelevant |
| security-paved-roads | 1,355 | |
| submodule-protection | 1,188 | |
| Lazy-Loaded-Rules-Tabelle | 1,118–1,120 | listet ≥ 10 von 15 agent-meta-internen Skills, die in Konsumentenprojekten nicht existieren (sync-interface, admin-ui, architecture, conventions, provider-agnostic, mcp-×4, tool-graphify) |
| Gemini-Bootstrap | 7,509–7,552 | compact 493 B |
| ZCode-Bootstrap | 871–913 | |
| Projektkopf | 929 | 7 unaufgelöste `{{...}}`-Platzhalter |
| ROUTING-Banner | 115 | `Opencode->AGENTS.md \| Gemini->AGENTS.md` — für die anderen falsch |

Zusätzlich: Verweise auf `.claude/hooks` / `.claude/rules` in Rules, die bei Nicht-Claude-Providern ins Leere zeigen.

Bestehendes #540-compact-Ergebnis in den Scratch-Projekten: CLAUDE.md −2.4 %, AGENTS.md −11.7 %. Die früheren Repo-Messungen (−34 % / −47 %, `docs/plans/issue-540-baseline.md`) bezogen sich auf die größeren eigenen Dateien dieses Repos — kein Widerspruch, andere Messbasis. Die Klassifikation INSTRUKTION/OVERVIEW/METADATEN aus `docs/guides/context-block-inventory.md` bleibt gültig.

## 3. Provider-Faktenblätter

### 3.1 Claude Code

| Punkt | Befund |
|---|---|
| Artefakte | `CLAUDE.md` 2,509 B (627 tok); `.claude/rules` 19 Dateien 17,880–18,297 B (ohne `paths:` → alle beim Start geladen); `.claude/agents` 62 Dateien 577,850 B; Orchestrator 90,691 B |
| Größte Rules | a2a-delegation-gates 6,795; branch-guard 3,103; security-paved-roads 1,352; submodule-protection 1,185; use-lazy-rules 1,011 |
| Ladeverhalten (VERIFIED-DOCS, https://code.claude.com/docs/en/memory) | CLAUDE.md-Ziel < 200 Zeilen; Imports reduzieren den Kontext **nicht** (beim Start geladen, 4 Hops); Block-HTML-Kommentare werden vor der Injektion entfernt; Rules ohne `paths:` beim Start, pfadgebundene bei passendem Read/Write/Edit; CLAUDE.md überlebt `/compact`; als User-Message nach dem System-Prompt; Auto-Memory lädt die ersten 200 Zeilen/25 KB; nur `CLAUDE.local.md` wird automatisch geladen; AGENTS.md wird ignoriert, wenn CLAUDE.md existiert; CLAUDE.md ist Kontext, keine erzwungene Konfiguration — harte Regeln über Hooks |
| Subagenten (VERIFIED-DOCS, https://code.claude.com/docs/en/sub-agents) | laden die CLAUDE.md-Hierarchie außer Explore/Plan, sofern nicht `omitClaudeMd: true` (ignoriert, wenn der Agent als Main läuft); Warnung bei kombinierten Beschreibungen > 15,000 Tokens; Verschachtelungstiefe Default 3; ob `.claude/rules` Subagenten erreichen: **UNVERIFIED** |
| Skills | nur Beschreibungen im Kontext (Cap 1,536 Zeichen, Listing-Budget 1 % des Fensters), SKILL.md < 500 Zeilen |
| Always-loaded (Main-Thread, Default) | ≈ 38.8 KB (~9.7k tok): CLAUDE.md 2.5 + Rules 17.9 + Agent-Roster ≈ 16.5 (davon Beschreibungen 12,144 B ≈ 3.3k tok) + Command-Beschreibungen ≈ 2.0 |
| … mit rules-preset `lazy` | ≈ 31.2 KB (Rules 8.8 + 8 SKILL.md-Frontmatter 1.3) |
| Orchestrator-Rolle | Subagent; mit `claude --agent orchestrator` Main-Thread → +90.7 KB System-Prompt **jeden Turn** (ersetzt den Default-System-Prompt; CLAUDE.md lädt weiterhin) |
| Inerte Kanäle | `CLAUDE.personal.md` (nur `CLAUDE.local.md` wird geladen) |
| Abweichungen | `orchestrator_hint` `claude -a orchestrator` (`ai-providers.yaml:97`) falsch — es gibt kein `-a`, korrekt `--agent`; #540-compact spart nur 59 B an CLAUDE.md und 62 B am Orchestrator |

### 3.2 Codex (codex-cli 0.162.1, VERIFIED-RUNTIME wo angegeben)

| Punkt | Befund |
|---|---|
| Artefakte | AGENTS.md 25,560–25,632 B (Einzelprovider full); Root `rules/*.md` + `.rules` 18,380 B; Orchestrator-Developer-Instructions 92,103 B |
| Ladeverhalten (VERIFIED-DOCS, https://developers.openai.com/codex/guides/agents-md; VERIFIED-SOURCE `codex-rs/core/src/agents_md.rs:142-178`) | AGENTS.md von Root → cwd konkateniert; `AGENTS.override.md` bevorzugt; Fallback-Dateinamen; `project_doc_max_bytes` Default 32768 |
| Truncation (VERIFIED-RUNTIME) | stilles Abschneiden mitten in der Zeile: bei der 34,035-B-Multi-Datei erhielt das Modell exakt 32,769 B, endend auf `define_subagent(nam`; nur `tracing::warn` |
| Main-Turn (VERIFIED-RUNTIME) | ≈ 82.9 KB: Basis-Prompt 17,119 B; AGENTS.md-User-Message 26,181; Tools 37,204 (davon `spawn_agent` 26,125 mit Rollenliste 19,026 für 64 Rollen); Skills-Liste 2,337 |
| Orchestrator-Child (VERIFIED-RUNTIME) | 92,103 B developer_instructions + 17,119 Basis + AGENTS.md 26,181 = 143 KB; **keine Multi-Agent-Tools** bei Default-Config (Aufruf abgelehnt „unsupported call"); mit `[agents] max_depth = 2` vorhanden (172.6 KB) — wir generieren keine `.codex/config.toml` |
| Inerte Kanäle | Root `rules/*.md` und `.rules` werden **nicht** geladen (`.rules` sind Starlark-Exec-Policy) → 18,380 B tote Dateien; Aussage in `docs/providers/codex.md:118-124` falsch |
| Skills | Lazy-Pointer auf `.agents/skills`, aber keine geschrieben (`rules.py:305` `if pc.get("has_rules"): return`; `context.py:1615-1617`). Nach manuellem Kopieren von 8 Skills listete Codex sie (12 Einträge, 3,941 B) → Discovery funktioniert (VERIFIED-RUNTIME) |
| Abweichungen | `spawn_agent`-Parameter real `agent_type`/`message`/`items`/`fork_context` — wir dokumentieren `agent=`/`task=` |

### 3.3 OpenCode (1.19.0, VERIFIED-RUNTIME)

| Punkt | Befund |
|---|---|
| Main `build`-Request | ≈ 70 KB (≈ 17.5k tok): System 35,353 B (inkl. AGENTS.md 25.6 KB als „Instructions from: AGENTS.md" + Basis ~8.9 KB); Tools 34,670 B, davon `task`-Beschreibung 16,348 B = Roster mit 63 Agenten |
| Orchestrator-Subagent | 116,890 B System + 29,360 Tools = 146 KB ≈ 36.6k tok |
| Developer-Subagent | 52.7 KB |
| Vererbung | AGENTS.md wird in **jeden** Subagenten injiziert; Agent-Body ersetzt den OpenCode-Basis-Prompt |
| Rules (VERIFIED-DOCS, https://opencode.ai/docs/rules) | `instructions`-Globs/Pfade sind immer aktiv (nicht lazy/pfadgebunden); Doku empfiehlt Lazy über `@file`-Referenzen + explizite Read-Anweisung |
| Skills | `.opencode/skills`, `.claude/skills`, `.agents/skills` (Namens-Regex, Beschreibung ≤ 1024) |
| Hebel | `permission.task`-Deny-Globs entfernen Agenten aus dem `task`-Roster |
| Tiefe | `subagent_depth` Default 1; unser Template setzt 3 (Orchestrator → Worker braucht ≥ 2), die v2-Surface verwirft es (`context.py:1340-1371`, `1367`) |
| Abweichungen | `primary-role: orchestrator` wirkt nur auf v2 (v1 emittiert `mode: subagent`); unbekannte Frontmatter-Keys (`version`, `prompt_mode`, `generated-from`, `hint`, `name`) werden als Optionen an den Modell-Provider durchgereicht; im Multi-Provider-Projekt erhält `opencode.json` ein Permission-Deny für `**/AGENTS.md` (Codex-Isolation-Dirs) → OpenCode-Agenten können AGENTS.md nicht lesen |

### 3.4 Mammouth Code (1.18.31.1, OpenCode-Fork, VERIFIED-RUNTIME)

| Punkt | Befund |
|---|---|
| Kontextdatei | liest AGENTS.md (Loader-Liste im Binary: AGENTS.md … CLAUDE.md, CONTEXT.md; null `MAMMOUTH.md`-Strings); AGENTS.md 25,568 B, identisch zu Codex |
| Config | `mammouth.jsonc/json` oder `opencode.jsonc/json`; scannt `.mammouth/` oder `.opencode/` nach `agent(s)/command(s)/skill(s)/mode(s)`; `mammouth.json` 604 B (Kommentare) |
| Inerte Kanäle | `.mammouth/rules/` (18,387 B) wird **nicht** gelesen (VERIFIED-RUNTIME) |
| Skills | `.mammouth/skills` wird entdeckt (8 manuell kopierte Lazy-Skills gelistet), aber wir schreiben keine (0 Dateien; Pointer hängen) |
| Agenten | 62 Agenten alle Modus `all` (kein `mode` emittiert) → alle im Tab-Zyklus; unsere Claude-Tool-Keys (`Agent`, `TodoWrite`, `Read` …) werden zu inerten Permission-Keys (OpenCode nutzt `task`/`todowrite`/`read` klein) → Orchestrator-Subagent (101,781 B System, 8 Tools, kein `task`) kann nicht delegieren |
| Dispatch | natives `task`-Tool existiert (der `build`-Agent dispatchte den Orchestrator) → `provider-capabilities.yaml:231-247` `subagent_dispatch:false` untertreibt |
| Main-Request | ≈ 70 KB |
| Abweichungen | kein `subagent_depth`; `delegation-syntax.yaml` mischt `background(agent=…)`-Pipeline-Notation mit `@agent`; kein `docs/providers/mammouth.md` |

### 3.5 Kimi Code (VERIFIED-SOURCE, Repo `MoonshotAI/kimi-code@c9f01f07`; offizielle Doku gesperrt)

| Punkt | Befund |
|---|---|
| Ladeverhalten | konkateniert `$KIMI_CODE_HOME/AGENTS.md`, `~/.agents/AGENTS.md` und für jedes Verzeichnis Git-Root → cwd `.kimi-code/AGENTS.md`, dann `AGENTS.md`; **nicht** nearest-wins (unsere `provider-capabilities.yaml:358` sagt nearest-wins) |
| Grenzen | keine Truncation; Warnung über 32 KiB (`AGENTS_MD_RECOMMENDED_MAX_BYTES`; `context.ts:8,185-191`) |
| Autorität | Injektion in den System-Prompt als nicht privilegierte „project-supplied reference data" in einem Code-Fence → das Gate ist nur beratend |
| Kanäle | keine `@`-Imports, kein Rules-Verzeichnis; Skills `.kimi-code/skills` / `.agents/skills` (SKILL.md, per Beschreibung auto-aufgerufen, ≤ 3 Ebenen) |
| Subagenten | Markdown + Frontmatter (`name`, `description`, `whenToUse`, `tools`-Allowlist [unbekannte Namen gewarnt], `disallowedTools`, `subagents`-Allowlist; Default delegierbar = nur coder/explore/plan); Agent-Body ist der **gesamte** System-Prompt (kein AGENTS.md/Skills, außer `${agents_md}`/`${skills}`/`${base_prompt}`) → unsere Worker sehen AGENTS.md nie; `kimi --agent <name>` / `--agent-file` macht einen Agenten zum Main; AgentSwarm 2..128 Items, muss einziger Tool-Call sein |
| BREAKING | generierter Orchestrator (75,747 B) hat Tools `[TodoWrite, Agent, Read, Write]` ohne `subagents:`-Allowlist → kann als gespawnter Subagent nicht an unsere Rollen dispatchen; kein AgentSwarm, obwohl §fanout es behauptet; `TodoWrite` ungültig (Kimi: `TodoList`); `hint` nicht auf `whenToUse` gemappt |
| Größen | Roster ≈ 16.5 KB in der Agent-Tool-Beschreibung; generierter Anteil ≈ 42 KB (~10.5k tok) full / ≈ 34 KB lazy |
| Fenster | `kimi-code/k3` 1,048,576; andere 262,144 |
| Stärkerer Kanal (Option) | Plugin-`systemPrompt` (privilegiert, ≤ 32 KB/Feld, 64 KB gesamt) |
| Inert | `AGENTS.personal.md` (generiert 1.2–1.3 KB) |

### 3.6 ZCode (VERIFIED-SOURCE, `zai-org/ZCode@aac47556` + `zcode-app-cli@3.14.5-34`)

| Punkt | Befund |
|---|---|
| Ladeverhalten | genau `~/.zcode/AGENTS.md` + nächstgelegene AGENTS.md beim Aufstieg von cwd (eine Workspace-Datei), je bei 100 KiB abgeschnitten |
| Autorität | Injektion als meta_user `# agentsMd` mit „IMPORTANT: These instructions OVERRIDE any default behavior and you MUST follow them" (hoch) |
| Vererbung | AGENTS.md auch in Subagenten, außer Profil `injectAgentsMd:false` → jeder Spawn zahlt ≈ 26 KB erneut |
| Agenten-Discovery | CLI lädt `~/.zcode/agents` und `<cwd>/.zcode/agents` beim Bootstrap automatisch (`subagents.ts:47-56`) — widerspricht `bootstrap_required:true` und dem AGENTS.md-Bootstrap-Block, der das Modell alle 62 Agentendateien lesen lässt (562,718 B ≈ 140k tok ≈ 70 % des GLM-5.3-200k-Fensters). Block für die CLI obsolet (Desktop: **UNVERIFIED**), 913 B |
| Parallelität | `Agent`-Tool `concurrentSafe:true`, Prompt fordert Batching von Agent-Calls → unser `parallel_execution:false` / Sequential-Fallback / „der Reihe nach" untertreibt |
| Main-Agent | kein Main-Agent-Flag (Orchestrator nur als Subagent); verschachtelter Agent möglich, Tiefenlimit **UNVERIFIED** |
| Skills | `.zcode/skills` / `.agents/skills`, Listing-Budget 20,000 Zeichen / 250 je Beschreibung |
| Größen | Roster ≈ 16.5 KB; Orchestrator 75,782 B; generierter AGENTS.md-Anteil ≈ 43 KB (~10.7k tok) |
| Sonstiges | Projekt-Hooks jetzt „pending workspace trust"; `AGENTS.personal.md` inert |

### 3.7 Gemini CLI / Antigravity (VERIFIED-SOURCE; Antigravity: statische In-Binary-Evidenz, Doku gesperrt)

| Punkt | Befund |
|---|---|
| Gemini-CLI-Kontext (VERIFIED-DOCS, https://geminicli.com/docs/cli/gemini-md) | Default-Kontextdatei `GEMINI.md` (andere via `context.fileName`), hierarchisch, konkateniert, bei jedem Prompt gesendet, `@`-Imports |
| Defekt | unser `.gemini/settings.json` hat kein `context.fileName` → Gemini CLI erhält **keinen** Projektkontext (AGENTS.md ignoriert) |
| Agenten | `.gemini/agents/*.md` sind native Subagenten, aber Loader-Schema `.strict()` (erlaubt: `kind`, `name`, `description`, `display_name`, `tools`, `mcp_servers`, `model`, `temperature`, `max_turns`, `timeout_mins`; Tools validiert) → unsere Zusatz-Keys (`version`, `hint`, `prompt_mode`, `generated-from`) und Claude-/Antigravity-Toolnamen ließen alle 62 scheitern (SOURCE-DERIVED, nicht ausgeführt); kein `define_subagent` in der CLI |
| Skills | `.gemini/skills` / `.agents/skills` (`.agents` gewinnt), `activate_skill` |
| Antigravity | liest `GEMINI.md`, `AGENTS.md`, `.agents/rules/*.md`, Agenten in `.agents/agents`, Skills `.agents/skills`; 12,000-Zeichen-Cap pro Rule-Datei von Drittquelle berichtet (**UNVERIFIED**) — unser AGENTS.md 33,037 / 23,032 B |
| Inert | `.gemini/rules` (17,880 B) von keinem der beiden Harnesses gelesen (deckt sich mit `docs/spikes/2026-09-14-f-rulesloc-gemini-rules-channel.md`); `AGENTS.personal.md` |
| Inhaltsverlust | Preset `lazy` entfernt 8 Rules (a2a-delegation-gates, issue-lifecycle, lifecycle-tasks, 3 × se-cascade, session-conclusion, submodule-protection) still aus AGENTS.md und schreibt **keine** Skills → nirgends erreichbar |
| Bootstrap | weist das Modell an, `define_subagent` / alle Agentendateien zu lesen (590,365 B ≈ 147k tok) |
| Orchestrator | 90,557 B, Tools `[TodoWrite, view_file, replace_file_content]`, kein Dispatch-Tool |
| Doku | `docs/providers/gemini-cli.md` veraltet (Gemini 2.5, GEMINI.md, `.gemini/hooks`) |

### 3.8 Continue (Repo-mdx; `docs.continue.dev` gesperrt)

| Punkt | Befund |
|---|---|
| Kontextdatei | `.continue/rules/project-context.md` nur 621 B, unaufgelöste `{{PLATFORM}}`, `{{BUILD_COMMAND}}` |
| Rules | 19+1 Rules, 18,591 B ohne Frontmatter → `alwaysApply` undefiniert → in jedem Agent/Chat/Edit-Request (≈ 4.6k tok ≈ 28 % des 16,384-Token-Kontexts des lokalen Template-Modells); unterstützt `alwaysApply:false` + `description` (model-decision) oder `globs` |
| Lazy | Preset `lazy` ist für Continue ein No-op (`channel: skill`); `.continue/skills/<n>/SKILL.md` ist reale Runtime-Fläche (H9), 0 generiert |
| Agenten | `.continue/agents/*.md` nur von `cn review` / `cn --agent`, nicht im Chat geladen → Orchestrator im Chat faktisch unerreichbar; Prompts nur bei `provider-options.Continue.generate-prompts: true` (Default aus) |
| Abweichungen | Agent-Frontmatter mit Claude-Feldern (`model claude-sonnet-5-5`, `permissionMode`, `alwaysApply`); Prompts tragen `allowed-tools`, `$ARGUMENTS` (Substitution **UNVERIFIED**), fehlendes `name` |

### 3.9 GitHub Copilot (`docs.github.com` gesperrt → Snippets + Audit-Zitate)

| Punkt | Befund |
|---|---|
| Kontextdatei | `.github/copilot-instructions.md` 9,247 B, davon 9,007 B Header + 62-Zeilen-Agententabelle, **keine** Rules |
| Code Review | liest nur die ersten 4,000 Zeichen jeder Instruktionsdatei |
| Inert | `.github/instructions/*.md` (19 Rules, 17,988 B) werden **nie** gelesen — Pflichtsuffix ist `.instructions.md` (+ `applyTo`/`description`-Frontmatter) |
| Bug | Agent `name: orchestrator.agent` (`agent_sync.py:892` `Path(filename).stem` auf `orchestrator.agent.md`) → `@orchestrator` passt nicht |
| Dispatch | kein `tools:`/`agents:` (Transform entfernt Tools) → keine Subagenten-Delegation (Schlussfolgerung, **UNVERIFIED**) |
| Skills | Pfad `.github/copilot/skills` falsch (dokumentiert `.github/skills`, außerdem `.claude/skills`, `.agents/skills`) |
| Richtwert | GitHub-Empfehlung ~1,000 Zeilen pro Datei |
| OK | Prompts `.github/prompts/*.prompt.md` |
| Veraltet | `.github/copilot/agents/`-Text in Bootstrap/Capabilities |

## 4. Querschnittstabellen

### 4.1 Always-loaded-Menge je Provider (aus den Messungen abgeleitet)

| Provider | Kontextdatei(en) im Main-Turn | Rules-Kanal real | Roster im Harness | Orchestrator als Main möglich |
|---|---|---|---|---|
| Claude | CLAUDE.md 2.5 KB + `.claude/rules` 17.9 KB | native Rules (alle beim Start) | ja (≈ 16.5 KB) | ja (`--agent`) |
| Codex | AGENTS.md 26.2 KB | embedded (Root-`rules/` inert) | ja (`spawn_agent` 26.1 KB) | UNVERIFIED (als Child nur mit `max_depth` dispatch-fähig) |
| OpenCode | AGENTS.md 25.6 KB (+ in jeden Subagenten) | embedded / `instructions` | ja (`task` 16.3 KB) | ja (primary, v2) |
| Mammouth | AGENTS.md 25.6 KB | embedded (`.mammouth/rules` inert) | ja | UNVERIFIED (Q7 der Spec) |
| Kimi | AGENTS.md, generierter Anteil ≈ 42 KB | embedded | ja (≈ 16.5 KB) | ja (`kimi --agent`) |
| ZCode | AGENTS.md, generierter Anteil ≈ 43 KB (+ in Subagenten) | embedded | ja (≈ 16.5 KB) | nein (kein Main-Agent-Flag) |
| Gemini CLI | **nichts** (kein `context.fileName`) | keiner | – | nein |
| Continue | project-context.md 0.6 KB + 18.6 KB Rules | native Rules (alle immer) | – | nur `cn --agent` |
| Copilot | copilot-instructions.md 9.2 KB | **keiner** (Suffix falsch) | – | UNVERIFIED |

### 4.2 Harte/weiche Größengrenzen

| Provider | Grenze | Art | Konfidenz |
|---|---|---|---|
| Codex | 32,768 B (`project_doc_max_bytes`) | hart, stilles Abschneiden | VERIFIED-RUNTIME |
| Kimi | 32 KiB | Warnung | VERIFIED-SOURCE |
| ZCode | 100 KiB je Datei | hart | VERIFIED-SOURCE |
| Claude | < 200 Zeilen CLAUDE.md; Beschreibungen > 15,000 Tokens Warnung | weich | VERIFIED-DOCS |
| Copilot | 4,000 Zeichen (Code Review); ~1,000 Zeilen Richtwert | hart (Review) / weich | Audit-Zitat (Doku gesperrt) |
| Antigravity | 12,000 Zeichen je Rule-Datei | ? | UNVERIFIED |
| Continue | Fenster des lokalen Template-Modells 16,384 Tokens | Budget | Messung am Template |

### 4.3 Kanäle, die generiert, aber nicht gelesen werden

| Provider | Verzeichnis/Datei | Bytes | Konfidenz |
|---|---|---:|---|
| Codex | Root `rules/*.md`, `.rules` | 18,380 | VERIFIED-RUNTIME |
| Mammouth | `.mammouth/rules/` | 18,387 | VERIFIED-RUNTIME |
| Gemini/Antigravity | `.gemini/rules` | 17,880 | VERIFIED-SOURCE + Spike |
| Copilot | `.github/instructions/*.md` | 17,988 | Doku-Snippet (Site gesperrt) |
| Claude | `CLAUDE.personal.md` | 1.2–1.3 KB | VERIFIED-DOCS |
| Kimi/ZCode/Gemini/Codex | `AGENTS.personal.md` | 1.2–1.3 KB | VERIFIED-SOURCE/-DOCS |
| Gemini CLI | AGENTS.md (ohne `context.fileName`) | 33,037 | VERIFIED-SOURCE |

### 4.4 Hängende Pointer / Inhaltsverlust

| Provider | Pointer | Ziel | Status |
|---|---|---|---|
| Codex | Lazy-Skills | `.agents/skills` | 0 Dateien |
| Mammouth | Lazy-Skills | `.mammouth/skills` | 0 Dateien |
| Gemini | Preset `lazy` | 8 Rules | weder embedded noch als Skill → Verlust |
| Continue | Preset `lazy` | Skills | No-op |
| alle AGENTS.md | Lazy-Rules-Tabelle | ≥ 10 agent-meta-interne Skills | existieren im Konsumentenprojekt nicht |
| Nicht-Claude | Verweise auf `.claude/hooks`, `.claude/rules` | Claude-Pfade | irrelevant / nicht vorhanden |

## 5. Best-Practice-Recherche

| Quelle | Kernaussage | Relevanz |
|---|---|---|
| [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | kleinste Menge hoch-signalhaltiger Tokens; „right altitude"; kanonische Beispiele statt Edge-Case-Listen; Just-in-time-Retrieval; Context Rot; Compaction; Sub-Agenten | Leitprinzip für Profil `compact` |
| [Anthropic — Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) | wenige, durchdachte Tools; concise vs. detailed (~1/3 Tokens); eval-getriebene Iteration; Tool-Beschreibungen zählen | Routing-Tabelle + Eval-Pflicht |
| [Anthropic — Advanced tool use](https://www.anthropic.com/engineering/advanced-tool-use) | Tool-Definitions-Overhead (z. B. 58 Tools ≈ 55K Tokens); Tool Search −85 % Tokens; MCP-Eval Opus 4 49 %→74 %, Opus 4.5 79.5 %→88.1 %; `defer_loading`; 1–5 Beispiele pro Tool 72 %→90 % | Roster-Kosten; Beispiele behalten, aber kuratiert |
| [Anthropic — Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) | Subagenten-Brief = Ziel, Ausgabeformat, Tools, Grenzen; Scaling-Effort-Regeln; Multi-Agent ≈ 15× Tokens; Lead-Kontext klein halten (externer Speicher) | Orchestrator klein halten |
| [Claude Code Memory](https://code.claude.com/docs/en/memory), [Sub-agents](https://code.claude.com/docs/en/sub-agents) | siehe §3.1 | Claude-Hebel (`paths:`, HTML-Kommentare, `omitClaudeMd`) |
| [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) / [best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Metadaten ~100 Tokens/Skill; Body < 5k Tokens / < 500 Zeilen; Referenzen eine Ebene tief; evaluation-driven; „Claude is already very smart" | Lazy-Skills als Rule-Kanal |
| [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) | Cache-Read 0.1× (0.05× Opus 5.5/Sonnet 5.5); 5-min-TTL; Präfix-Reihenfolge tools → system → messages; exakter Match → generierte Dateien byte-stabil halten, stabile Inhalte zuerst | Byte-Stabilität als Anforderung |
| [Chroma — Context Rot](https://trychroma.com/research/context-rot) | Qualität sinkt mit Kontextlänge | Begründung für Verkleinerung |
| [Format-Studie arXiv 2411.10541](https://arxiv.org/abs/2411.10541) | Prompt-Format verändert Ergebnisse, kleinere Modelle stärker; keine Head-to-Head-Token-Studie gefunden | Formatwechsel braucht **eigenen** Eval |
| IFScale / Instruction-Density-Forschung | bestes Frontier-Modell ≈ 68 % bei 500 Instruktionen; neuere Modelle besser | nur Richtung (Übertragbarkeit UNVERIFIED) |
| [Codex AGENTS.md-Guide](https://developers.openai.com/codex/guides/agents-md) | 32 KiB Default, `project_doc_max_bytes` | harter Cap |
| GitHub Copilot Custom Instructions | ~1,000 Zeilen; `applyTo`; `.instructions.md` | Suffix-Fix (Doku-Site gesperrt; Snippets) |
| [Gemini CLI GEMINI.md](https://geminicli.com/docs/cli/gemini-md) | siehe §3.7 | `context.fileName` |
| [OpenCode Rules](https://opencode.ai/docs/rules) | siehe §3.3 | Lazy via `@file` |
| Tool-Count-Degradation (RAG-MCP 13.6 %→43.1 %) | Sekundärquellen | **UNVERIFIED-Qualität**, nur Richtung |

Konsequenzen für das Design (Ableitung, keine Messung): (1) Routing-Signal (Keywords, signaltragende Beispiele) behalten, Struktur-Rauschen (Whitespace, Duplikate, tote Schemas) streichen; (2) Referenzprosa per Just-in-time-Kanal (Skills, Pointer) statt immer-an; (3) jede Formatänderung per eigenem Eval absichern; (4) Ausgaben byte-stabil halten.

## 6. Konnte nicht verifiziert werden

| # | Punkt | Grund |
|---|---|---|
| U-01 | Ob `.claude/rules` Claude-Subagenten erreichen | Doku uneindeutig, kein Capture |
| U-02 | Gemini CLI strict-Schema-Verhalten zur Laufzeit (alle 62 Agenten scheitern) | nur Quellcode, nicht ausgeführt |
| U-03 | Antigravity 12,000-Zeichen-Cap, Status `define_subagent` | Drittquelle, Doku gesperrt |
| U-04 | ZCode Desktop lädt Agenten ebenfalls automatisch; Tiefenlimit verschachtelter Agenten | nur CLI-Quelle |
| U-05 | Mammouth: Orchestrator als Primary erhält `task` mit unserer Datei | nicht getestet |
| U-06 | Copilot kann ohne `tools:`/`agents:` nicht delegieren | Schlussfolgerung |
| U-07 | Continue `$ARGUMENTS`-Substitution in Prompts | Doku gesperrt |
| U-08 | Kimi-Verhalten laut offizieller Doku (nur Repo gelesen) | Doku gesperrt |
| U-09 | Copilot-4,000-Zeichen-Grenze und `.instructions.md` | `docs.github.com` gesperrt, Audit-Zitate |
| U-10 | Token-Zahlen | Bytes/4-Näherung; echter Tokenizer fehlt |
| U-11 | IFScale-/RAG-MCP-Zahlen auf unsere Modelle übertragbar | Sekundärquellen |
| U-12 | Codex: Orchestrator als Main-Agent wählbar | nicht untersucht |

## 7. Reproduktion

- Scratch-Projekte: `.tmp/ctx-study` (nicht versioniert); je Provider ein `project.yaml` mit 62 Rollen und dem jeweiligen Preset (`full`, `compact`, `lazy`).
- Capture: lokaler Mock-LLM-Server, der Request-Bodies auf Platte schreibt; Runtime per Base-URL-Override darauf gerichtet. Die Spec überführt diese Skripte nach `tests/manual/context-capture/` (QG-7).
- Größen: Byte-Zählung auf generierte Dateien bzw. Request-Bodies; Abschnittsgrößen über Überschriften-Splits.

## 8. Rückverweise

- Bestehende Kompaktierung (#540) und Klassifikation: `docs/plans/issue-540-baseline.md`, `docs/guides/context-block-inventory.md`.
- Topologie-Achse: `SPEC-CONTEXT-FILE-MODES-2026-09-13`.
- Ableitende Spec: `docs/specs/2026-10-11-context-profiles-spec.md` (Befunde F-01..F-18).

## 9. Korrekturen früherer Aussagen

| # | Frühere Aussage | Korrektur |
|---|---|---|
| K-a | Orchestrator §12 Few-shot sei 8.5 KB inline | §12 ist ein 3-Zeilen-Pointer von 188 B auf `_wf-orchestrator-reference.md` (1,355 B); die frühere Messaussage war falsch |
| K-b | Die Orchestrator-Datei (90.7 KB) werde in jedem Turn bezahlt | Bezahlt pro Orchestrator-Aufruf; in **jedem** Turn nur, wenn er Main-Thread-Agent ist (Claude `--agent orchestrator`, Kimi `--agent`, OpenCode/Mammouth primary) |
| K-c | „AGENTS.md ist der Haupt-Bloat bei Claude" | falsch: CLAUDE.md ist 2.5 KB; Claude ignoriert AGENTS.md, wenn CLAUDE.md existiert; Claude-Last liegt bei Rules (17.9 KB), Roster (≈ 16.5 KB) und ggf. Orchestrator |
