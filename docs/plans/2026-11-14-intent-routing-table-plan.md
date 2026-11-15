---
pipeline_stages:
  implement: 3
status: DRAFT
date: 2026-11-14
base-commit: 92d41a90
trace:
  - intent-routing-table
  - issue-1161
  - issue-1244
  - issue-264
---

# Intent-Routing-Tabelle — Modernisierung (Konzept + Plan)

> Status: **DRAFT** (2026-11-14/15). Nur Analyse und Planung — nichts umgesetzt, kein Sync, kein Test, kein Issue, kein PR.
> Basis: `origin/main 92d41a90` (PR #1236 gemergt). Zeilenanker veralten; vor Ausführung Freshness-Check.
> Messdaten nicht eingecheckt, reproduzierbar per Task 0 (Messskript, tiktoken cl100k). Tokens: **tiktoken cl100k** wo so gekennzeichnet, sonst **Bytes/4 (Proxy)**.
> Klasse: **XL / Architectural** (Datenmodell in `role-defaults.yaml` + Schema, Renderer, Admin-UI, Eval, Rebaseline) → **Spec-Pflicht** (§4 ist der Spec-Kern; Umsetzung erst nach `Status: APPROVED`).
> Abgrenzung: `docs/plans/2026-11-14-agent-improvement-loop-plan.md` = Rewrite aller Rollen-Prompts (Rubrik, Blöcke, Sprache). **Hier**: Routing-Datenmodell, generierte Routing-Artefakte, Konfigurierbarkeit (project.yaml + Admin-UI), Routing-Eval. Schnittmenge = Hebel H1 (route_intent kompakt): wird **hier** spezifiziert, dort nur gemessen (§8).

## Entscheidungsstand 2026-11-15

Quelle: [Master-Roadmap §4](2026-11-15-master-roadmap.md) (Nutzerentscheidungen 2026-11-15). Plan-Status bleibt DRAFT.

- E-07: Taxonomie informativ; Routing-Spec nach Review freigegeben.
- E-23: kompaktes Zeilenformat als Default, name_index reduziert, Direct-Dispatch generiert, Lazy-Detaildatei, Minor-Bump + CHANGELOG; NICHT das globale Compact-Profil.
- E-27: Routing-Eval ja (< 1 USD).
- E-12: Rollenliste ausstehend, vor Routing-PR 2 nötig.
- E-26: Gemini = nur Gemini CLI.
- E-28 (Erweiterung): Sprach-Keys dynamisch (Eingabe und Ausgabe).

**Goal:** Eine Routing-Quelle (`role-defaults.yaml` + projektseitige Overrides) erzeugt für jeden Provider die kleinstmögliche, deterministische Routing-Oberfläche, die der Orchestrator zum korrekten Dispatch braucht; Projekte konfigurieren Intents/Trigger/Overrides in `project.yaml` und im Admin-UI mit Live-Preview und Lint; Routing-Güte wird mit einem Eval-Set gemessen.
**Architecture:** Keine neue Schicht. Datenmodell-Erweiterung in `config/role-defaults.yaml` (`routing.*`), Override-Block `routing-overrides` in `project.yaml` (Schema), ein Resolver in `scripts/lib/delegation_table.py`, zwei Render-Formen in `scripts/lib/agents.py` (kompakte Always-on-Tabelle + Lazy-Detaildatei), Admin-UI-Editor über bestehende `/api/config/project/section`-Route + neuer Read-only-Preview-Endpoint.
**Tech Stack:** Python 3.9 (stdlib + PyYAML), JSON-Schema, Vanilla-JS Admin-UI (`docs/ui/admin-ui.html`), pytest, promptfoo/`run_eval.sh` (Eval).
**Spec:** Spec-Kern in §4 dieses Dokuments (Entscheidung 15 der Roadmap: ein Dokument mit eingebettetem Spec-Abschnitt); bei Freigabe nach `docs/specs/2026-11-XX-intent-routing-table-spec.md` ausgliedern.

---

## 1. Ist-Zustand (belegt)

### 1.1 Drei Routing-Artefakte, eine Quelle

„Die Intent-Routing-Tabelle“ ist heute **drei** generierte Artefakte aus **einer** Quelle (`config/role-defaults.yaml`, 3.050 Z., 114 Rollen):

| # | Artefakt | Platzhalter / Template | Generator | Gerendert (dieses Repo) |
|---|---|---|---|---|
| A | `route_intent`-Tool-Definition (JSON, 1 Zeile) | `{{INTENT_ROUTING_TOOLS}}` — `agents/1-generic/orchestrator.md:108` | `delegation_table.get_routing_rules` (`scripts/lib/delegation_table.py:289-434`) → `agents.build_routing_tool_definition` (`:276`) → `render_routing_tool_definition` (`:514-561`) → `build_routing_tool_definitions_for_providers` (`:562`), aufgerufen `config.py:2850`; Provider-Mapping in `agent_sync.py:534-540` | `.claude/agents/orchestrator.md:214`: **31.247 B / 7.662 Tok (cl100k)** = 41 % des Orchestrator-Renders (73.403 B / 18.581 Tok) |
| B | Agent table (Name + ≤3 Keywords) | `{{AGENT_DELEGATION_TABLE}}` — `orchestrator.md:340` (nur `{{else}}`-Zweig von `CONTEXT_PROFILE_COMPACT`/`ROSTER_IN_HARNESS`, `:334-342`); Partial `templates/context/partials/agents-table.md` | `get_active_agents_data` + `exclude_name_only` (`delegation_table.py:96-105,124`), `derive_keywords` (`:20-35`); `config.py:2367-2389` | 61 Z. / 5.208 B; dasselbe Partial als „Agent Directory“ in `AGENTS.md:169` (62 Z. / 5.138 B, always-on Opencode/Gemini) |
| C | INTENT_ROUTING_TABLE (Pipeline-Zeilen + Tiers-Zeile) | `{{INTENT_ROUTING_TABLE}}` — `rules/1-generic/use-orchestrator.md:69`, **nur** im `{{#if ORCH_MODE_MAIN_CHAT}}`-Zweig (`:64-80`) | `get_intent_routing_table` (`delegation_table.py:437-505`), `config.py:2833` | in diesem Repo **leer** (mode `strict`, `.claude/rules/use-orchestrator.md` = 12 Z.); Per-Agent-Zeilen bereits 2026-08-14 gestrichen (`delegation_table.py:449-454`) |

Zusatzflächen mit Routing-Semantik: Direct-Dispatch-Tabelle (`config/direct-dispatch-section.md`, 4 feste Zeilen, `{{DIRECT_DISPATCH_SECTION}}` `orchestrator.md:60/204`), Developer-Tier-Tabelle (`orchestrator.md:133-160`), Reviewer-Routing-Matrix `config/routing/reviewers.yaml` (Pfad-Pattern → Reviewer-Set, eigener Konsument), Pipeline-Signal-Keywords (`role-defaults.yaml` ab `:2639`, 7 gerenderte Pipelines).

### 1.2 Datenmodell heute (`role-defaults.yaml`)

- Je Rolle: `workflow_tier` (required/recommended/optional), `short_desc`, `routing: {addressability, parallel, orchestrator_only, priority?, name_only_reason?}`, `routing_patterns: {keywords[], examples[] | {en:[],de:[]}}`, `handoff: {input_contracts[], output_contract}`.
- Bestand: 88 Rollen `addressability: keyword`, 13 `name_only`, 1 `excluded`; 221 Keywords, 62 Beispiele über 55 aktive Regeln; `priority` nur vereinzelt und **ohne Konsument im Prompt** (`agents.py`/`delegation_table.py:387-390`: „emitted only (the LLM resolves overlaps)“).
- Ableitungen: fehlende `addressability` → Warnung + Herleitung (`delegation_table.py:78-93`); `input_contracts` werden auf aktive Produzenten reduziert (`:350-356,382-385`).
- Sprache: Keywords „kanonisch/sprachneutral“ mit Ratchet-Allowlist `config/routing-language.yaml` (IC-29); Examples sprach-selektiert (`_select_examples`, `:229`).

### 1.3 Konfigurierbarkeit heute

| Hebel | Ort | Wirkung auf Routing |
|---|---|---|
| Rollen-Whitelist `roles:` | `project.yaml`; Schema `config/project-config.schema.json:81` | bestimmt Active-Set → Zielrollen/Regeln (`_active_role_names`, `delegation_table.py:38-68`) |
| `activation_groups` + Gates (SE, Knowledge, developer_tiers) | `role-defaults.yaml:2545`; `roles.py:131-181` | Rollen ein/aus → Zeilen ein/aus |
| `orchestrator.mode` strict/advisory/main-chat; `orchestrator.topology` | Schema `:2469-2500`; `.meta-config/project.yaml:308-324` | mode bestimmt, **welche** der drei Artefakte überhaupt rendern (C nur main-chat) |
| `context-profile: compact` (global oder je Provider) | Schema `:2830-2850`; `context_profile.py` | IC-04: route_intent-JSON → Zeilenformat `agent|flags|kw;kw|example` (`agents.py:442-512`); Golden: Routing-Block 8.435 B statt 32.834 B |
| `direct-dispatch-enabled`, `unknown-fallback.*` | Schema/UI vorhanden | Direct-Dispatch-Block, §11-Fallback |
| Provider-Capabilities `route_intent_tool` (alle 9 Provider `false`), `handoff_format` json/yaml_text_block, `roster_in_harness` | `config/provider-capabilities.yaml:124-667` | Format und Mandat (`ROUTE_INTENT_CALLABLE`) |
| **Nicht konfigurierbar**: Keywords/Examples/Addressability/Tier je Rolle aus dem Projekt, Pipelines-Signal-Keywords, Spaltenwahl/Format der Tabelle, Lazy-Auslagerung | — | fest in `role-defaults.yaml` (Framework-Datei, Submodul) |

Admin-UI: `/project/orchestrator`-View (`docs/ui/admin-ui.html:1645`, `viewProjectOrchestrator` `:7178`) schreibt nur `enabled/mode/direct-dispatch/checkpointing/native-extensions/unknown-fallback/handoff.protocol`; **keine** Routing-Daten, kein Preview.

### 1.4 Tests, Goldens, Drift

- Struktur/Determinismus: `tests/test_routing_tool_definitions.py` (676 Z.), `tests/test_delegation_table.py` (117), `tests/test_compact_matrix.py` (669, IC-04-Zeilenformat), `tests/test_routing_keywords_language_neutral.py` (Ratchet), `tests/test_no_role_routes_in_templates.py` (Routing darf nicht in Templates stehen — **Leitplanke für dieses Vorhaben**).
- Render-Identität: `tests/test_ac01_render_identity.py` + `tests/fixtures/ac01-baseline/hashes.json` (62 Commits/90 Tage), `compact-golden/orchestrator.md`, `topology-golden/*`, `slimming-golden/*` — **jede Routing-Format-Änderung = Rebaseline aller vier**.
- Budgets: `tests/test_context_budgets.py` pinnt Ist + max(256 B, 2 %, ≤4 KB) je Provider×Artefakt (`:313-320`); Compact-Targets nur ESTIMATE (`:619-627`, „Claude orchestrator ≤ 32 KB“).
- Eval: `tests/routing-llm-eval/` (B1 Routing-Katalog generiert aus Pipeline-Signal-Keywords via `scripts/gen_routing_llm_eval_catalog.py`; Rollen-Routing nur manuell/behavioral; läuft nur gegen `claude -p`/Opencode, kostenpflichtig, nicht in CI).
- Drift-Risiken: (1) Keyword-Pflege verteilt über 88 Rollen ohne Überlappungs-Lint; (2) `derive_keywords` schneidet die Frontmatter-`description` beim ersten Satz/Separator — Agent table ≠ Routing-Keywords (zwei Keyword-Quellen für dieselbe Rolle); (3) `priority` deklariert, nirgends ausgewertet; (4) `name_index` dupliziert enum + tier (12.035 B).

## 2. Orchestrierungsqualität

### 2.1 Was die Tabelle leistet

- Ablauf im Prompt (`orchestrator.md:100-117`): Pipeline-Treffer (Signal-Keywords) → Rollen-Treffer (keywords/examples) → `orchestrator_only` → Eskalations-Gate → §11 Unknown-intent (max. 1 Rückfrage, Fallback-Kette `ask-user → meta-feedback → main-chat`, `:301-309`) → Target-description-Gate (kein Best-effort-Dispatch bei Überlappung, `:117`).
- Klassifizierung S/M/L/XL: **nicht** Teil der Routing-Daten; regelbasiert in §0 (`:34-64`) und Master-Rule `spec-plan-workflow`. Die Tabelle kennt keine Größenklasse — eine `M`-Anfrage an `junior-developer` wird nicht durch Daten verhindert, nur durch Prosa (§4 Tier-Tabelle `:133-160`).
- Fan-out/Parallel: `routing.parallel` ist „rein informativ — kein Runtime-Enforcement“ (`delegation_table.py:478`); Fan-out-Mechanik capability-gated in §6 (`:202-222`).
- Topologie: Artefakt C existiert nur für `main-chat`; `primary/subagent/hybrid` ändern den Routing-Inhalt nicht, nur den Ort (Topology-Goldens). Anti-Recursion: `orchestrator` aus `target_agents` ausgeschlossen (`:349`), Singleton-Regel `:390`.
- Lazy-Skills als Ziel: **nicht vorgesehen** — `use-lazy-rules.md` (Skill-Tabelle „Wann“) ist eine zweite, unverbundene Intent-Tabelle (`context.py:3014,3140`).

### 2.2 Schwächen (routing-relevant)

| # | Befund | Beleg | Wirkung |
|---|---|---|---|
| Q1 | 55 Regeln, 221 Keywords ohne Überlappungs-Lint; Beispiel: „Audit“ (code-reviewer) vs. security-/dependency-auditor; „Review“ in concept-reviewer/code-reviewer/*-reviewer | `role-defaults.yaml` routing_patterns; Compact-Golden Z. 114-117 | Mehrdeutigkeit wird an das LLM delegiert; `priority` existiert, wird nicht gerendert/erklärt |
| Q2 | Zwei Keyword-Quellen je Rolle (routing_patterns vs. aus `description` abgeleitete Agent-table-Keywords) | `delegation_table.py:20-35` vs. `:365` | Orchestrator sieht pro Rolle zwei abweichende Trigger-Listen; Harness lädt zusätzlich die Frontmatter-`description` (Claude/Opencode: `roster_in_harness: true`) → **dreifach** |
| Q3 | Keine Größenklasse/Intent-Kategorie in den Daten | §2.1 | Spec/Plan-Gate nur prosaisch; keine Datengrundlage für „M/L/XL → erst Spec“ je Rolle |
| Q4 | `name_index` als Fallback-Kanal (`orchestrator.md:105`) trägt 57 `short_desc` — Prosa, die bei Claude/Opencode bereits im System-Prompt steht | Messung §1.1 | 12 KB/Spawn ohne Zusatznutzen bei `roster_in_harness: true` |
| Q5 | Eval misst nur Pipeline-Routing (B1 generiert); Rollen-Routing-Fälle nur manuell | `gen_routing_llm_eval_catalog.py:1-25` | Qualitätsänderungen am Rollen-Routing sind unbemessen |
| Q6 | Direct-Dispatch-Tabelle fest (4 Zeilen), nicht aus Rollen-Metadaten; Zeilen sind per `ROLE_*_ACTIVE` gegated (`templates/direct-dispatch-section.md`, `config.py:2143-2155`), `config/direct-dispatch-section.md` ist eine ungegatete Zweitkopie | Dateien | Direct-Dispatch-Fähigkeit ist kein Rollen-Attribut → Projekte können sie nicht pro Rolle setzen; Zweitkopie = Drift-Quelle |
| Q7 | #1176 (Orchestrator beendet Turn vor Hintergrund-Agenten) und #1168/#1247 (Trailer) sind **nicht** routing-bedingt | Issues | hier Nicht-Ziel; Phase D (#1176 S-Klasse, `phase-d-guards-hooks.md:47,61`) |

## 3. Token-Sparsamkeit

### 3.1 Bestand je Provider (gerendert, dieses Repo)

| Fläche | Claude | Opencode | Gemini | Messung |
|---|---|---|---|---|
| route_intent-JSON pro Orchestrator-Spawn | 31.247 B / **7.662 Tok** | ≈ identisch (json) | 32.834 B Block (json) | cl100k / wc |
| Agent table im Orchestrator | 5.208 B (~1,3k Tok Proxy) | ≈ | ≈ | wc |
| Agent Directory always-on (`AGENTS.md`) | — | 5.138 B von 16.988 B / **4.788 Tok** | dto. (geteilte Datei) | cl100k |
| Harness-Roster (Frontmatter descriptions) | 58 Rollen, 5.133 B (~1,3k Tok) always-on | dto. | Gemini `roster_in_harness: false` → Directory nötig | measurements-2026-11-14 |
| Artefakt C | 0 (strict) | 0 | 0 | — |

Anteil am Always-on (Claude, ~24,3 KB ≈ 6k Tok Proxy): Routing selbst 0 B always-on; **Hebel liegt im Spawn-Pfad** (7,7k + 1,3k Tok pro Orchestrator-Spawn, bei Checkpoint-Resume erneut).

### 3.2 Hebel und realistische Einsparung

| Hebel | Mechanik | Ersparnis (Schätzung) | Risiko |
|---|---|---|---|
| T1 Kompaktformat als Default für Provider ohne `route_intent_tool` | IC-04-Zeilenformat (`render_routing_lines`) statt JSON, unabhängig vom `context-profile` (heute gekoppelt, `agents.py:494-512`) | 31,2 KB → 8,4 KB; **≈ −5,6k Tok/Spawn (cl100k auf Golden hochgerechnet: 8.435 B ≈ 2,1k Tok)** | Format-Lesbarkeit für kleine Modelle (Opencode-Eval); Rebaseline |
| T2 `name_index` streichen, wenn `roster_in_harness: true`; sonst nur `agent` + `name_only_reason` | Capability-Flag statt Provider-Name | −12 KB JSON bzw. −1 Zeile „name-only“ bleibt | Fallback „User nennt Rolle explizit“ braucht nur Namen (enum) |
| T3 Agent table dedupe: bei `roster_in_harness: true` **nicht** rendern (heute nur bei compact, `orchestrator.md:334`) | bestehendes Gate verallgemeinern | −5,2 KB/Spawn Claude/Opencode | Gemini/Continue behalten Tabelle |
| T4 Eine Keyword-Quelle: Agent table/Directory zeigt `routing.keywords[:3]`, nicht `derive_keywords(description)` | `active_agents_table.keywords` aus `routing_patterns` | ~0 B, aber Konsistenz (Q2) | Directory-Wortlaut ändert sich (AGENTS.md-Ceiling) |
| T5 Examples auf 1 je Rolle (IC-04 `select_routing_examples` macht das schon) + Keywords ≤ 6 je Rolle (Lint) | Daten-Lint | −1…2 KB | Routing-Güte: Eval-gated |
| T6 Lazy-Detail: vollständige Regeln (`input/output_contracts`, `priority`, alle Examples) in `pipeline-details/`-ähnliche Datei `<agents_dir>/../routing-details.md`, Pointer-Zeile im Prompt | wie `PIPELINE_DETAILS_DIR` (`use-orchestrator.md:71`) | Contracts (1,5 KB) + Rest raus | Orchestrator muss bei Bedarf lesen (1 Read) |
| T7 Deterministische Reihenfolge (bereits sortiert) → Prompt-Caching-stabil; Datum/Pfade **nicht** in den Routing-Block | ist erfüllt (`sort`), Sicherung per Test | 0 B, Cache-Hit-Rate | — |

Summe realistisch (Claude, pro Orchestrator-Spawn): **≈ 73,4 KB → ≈ 45 KB (−28 KB, ≈ −7k Tok cl100k)**; mit Compact-Profil für die übrigen Blöcke zusätzlich (dort geplant im Verbesserungsschleifen-Plan, E1). Always-on Opencode/Gemini: AGENTS.md −0…5 KB je nach T3/T4 (Gemini behält Directory). Messmethode: tiktoken cl100k für Ist (oben), Zielwerte Bytes/4 → vor Umsetzung nachmessen (Task 0).

## 4. Spec-Kern: Zielkonzept „best in class“

> spec-id (vorläufig): `SPEC-INTENT-ROUTING-TABLE-2026-11-14` · Status: DRAFT · Freigabe = `Status: APPROVED` durch den Nutzer; vorher keine Implementierungs-Task aus §7 (Block B/C) ausführbar.

### 4.1 Zielbild in 5 Sätzen

1. **Eine Routing-Quelle, ein Resolver:** `role-defaults.yaml` (Framework-Default) + `project.yaml → routing-overrides` (Projekt) werden von `delegation_table.resolve_routing_model()` zu **einem** Routing-Modell gemergt, aus dem alle Artefakte (A/B/C, Direct-Dispatch, Eval-Katalog) gerendert werden.
2. **Zwei Render-Formen, capability-gated:** eine kompakte Always-on-Tabelle (Zeilenformat, ≤ 8 KB bei 57 Rollen) und eine Lazy-Detaildatei (Contracts, alle Beispiele, Priorität, Größenklasse); JSON-Tool-Definition nur noch für Provider mit `route_intent_tool: true` (heute keiner).
3. **Intent-Taxonomie statt Keyword-Suppe:** jede Rolle trägt `intents[]` aus einer festen Taxonomie (`config/routing/intents.yaml`), Trigger-Keywords ≤ 6, `size_class` (S/M/L/XL-Mindestklasse), `direct_dispatch` und `visibility` (in welcher Topologie/Mode die Zeile rendert); ein Lint erzwingt Eindeutigkeit (Überlappung nur mit `priority`).
4. **Konfigurierbar an drei Stellen:** Preset (Framework), `project.yaml` (`routing-overrides`, Schema-validiert), Admin-UI (Editor mit Lint + Live-Preview + Tokenzahl + Reset-auf-Default); alles landet im selben Override-Block.
5. **Messbar:** ein Routing-Eval-Set (`intent → erwartete Rolle/Pipeline`) wird aus dem Routing-Modell generiert (deterministische Fälle) und um manuelle Mehrdeutigkeitsfälle ergänzt; LLM-Läufe nur nach Kostenschätzung + Ja.

### 4.2 Datenmodell (Schema, Delta zu heute)

`config/role-defaults.yaml → roles.<role>.routing` (neu/erweitert; alte Keys bleiben, Migration mechanisch):

```yaml
routing:
  addressability: keyword | name_only | excluded   # unverändert
  intents: [implement, review]                       # NEU, ≥1 aus config/routing/intents.yaml, Pflicht bei keyword
  triggers: ["Bugfix", "Refactoring", "implement"]   # NEU = routing_patterns.keywords, Lint: ≤ 6, sprachneutral (IC-29)
  examples: {en: [...], de: [...]}                   # = routing_patterns.examples (verschoben, max 2 je Sprache)
  size_class: S | M | L | XL                         # NEU, Mindestklasse der Rolle (junior=S, developer=M, senior=L, concept-architect=XL)
  direct_dispatch: false                             # NEU, ersetzt die feste Direct-Dispatch-Tabelle (git/agent-meta-manager/feedback/documenter = true)
  visibility: {modes: [strict, advisory, main-chat], topologies: [primary, subagent, hybrid]}  # NEU, Default alle
  parallel, orchestrator_only, priority, name_only_reason   # unverändert; priority wird GERENDERT (Flag `p<N>`)
  requires: [tool:Bash, capability:subagent_dispatch]  # NEU optional; Zeile entfällt, wenn Provider-Capability fehlt
```

`config/routing/intents.yaml` (NEU, Framework): ~16 Intents mit 1-Zeilen-Definition und Default-`size_class` (z. B. `implement`, `fix`, `review`, `test`, `spec`, `plan`, `design`, `docs`, `git`, `meta`, `ops`, `security`, `data`, `knowledge`, `estimate`, `triage`).

`config/project-config.schema.json → routing-overrides` (NEU, Top-Level, `additionalProperties: false`):

```yaml
routing-overrides:
  format: auto | compact | json | off     # auto = capability-gated (Default)
  detail-file: true                       # Lazy-Detaildatei rendern
  table-in-orchestrator: auto | always | never   # auto = nicht bei roster_in_harness
  roles:
    developer: { triggers: ["Feature bauen"], size_class: M, priority: 2 }   # Teilmenge der routing-Keys, Deep-Merge
    intern-developer: { addressability: excluded }
  pipelines:
    bugfix: { signal_keywords: [...] }    # Override der Pipeline-Signal-Keywords
```

Merge-Regel: Projekt-Override gewinnt feldweise; Listen ersetzen (kein Append); unbekannte Rolle/Intent/Key = `SyncError routing-overrides.unknown-*` (fail-closed); Rolle nicht im Active-Set = Warnung (`routing-overrides.inactive-role`).

### 4.3 Schnittstellen

| Schnittstelle | Signatur / Vertrag | Konsumenten |
|---|---|---|
| `delegation_table.resolve_routing_model(agent_meta_root, config, *, active_set, pipelines, language, warn_sink) -> RoutingModel` | gefrorenes Dataclass: `roles: dict[str, RoleRoute]`, `pipelines`, `intents`, `source: dict[field, default|override]`; deterministisch sortiert | Renderer, Lint, Eval-Generator, Admin-Preview |
| `routing_lint.lint(model, capabilities) -> list[Finding]` (NEU `scripts/lib/routing_lint.py`) | Codes: `RL-UNKNOWN-ROLE`, `RL-UNKNOWN-INTENT`, `RL-TRIGGER-OVERLAP` (gleicher Trigger casefold in ≥2 Rollen ohne Prioritätsunterschied), `RL-MISSING-INTENT`, `RL-TRIGGER-LIMIT`, `RL-REQUIRED-INTENT-UNCOVERED` (Pflichtintents `implement`, `review`, `git` ohne aktive Rolle), `RL-CYCLE` (orchestrator_only-Eskalationskette zyklisch), `RL-DEAD-ROW` (visibility schließt alle aktiven Mode/Topologie-Kombinationen aus) | `sync.py --validate`, Admin-UI, Tests |
| `agents.render_routing(model, *, fmt: "compact"|"json", roster_in_harness: bool) -> tuple[str, str]` | `(inline_block, detail_doc)`; `compact`-Zeile: `<agent>|<flags>|<intents>|<kw;kw>|<example>`; Flags `req,rec,orch-only,name-only,dd,S..XL,p<N>`; `json` = heutiges Format minus `name_index` bei `roster_in_harness` | `config.py` (Variablen `INTENT_ROUTING_TOOLS`, `ROUTING_DETAILS_FILE`), Admin-Preview |
| Platzhalter | `{{INTENT_ROUTING_TOOLS}}` (Inhalt wechselt auf compact), `{{ROUTING_DETAILS_PATH}}` (NEU, Pointer), `{{AGENT_DELEGATION_TABLE}}` (Keywords aus `triggers[:3]`), `{{DIRECT_DISPATCH_SECTION}}` (aus `direct_dispatch: true`-Rollen generiert) | `orchestrator.md`, `use-orchestrator.md`, `agents-table.md` |
| Admin-API | `GET /api/routing/model` (effektives Modell + source), `GET /api/routing/preview?provider=<P>` (gerenderter Block + Bytes + Tok-Proxy + Lint), `POST /api/config/project/section {section:"routing-overrides"}` (bestehende Route, Section in `PROJECT_WRITABLE_SECTIONS` `admin-server.py:238` aufnehmen, Guard `_guard_routing_overrides_write` = Lint fail-closed für Fehler-Codes) | `docs/ui/admin-ui.html` |
| Eval | `scripts/gen_role_routing_eval_catalog.py` (NEU neben `gen_routing_llm_eval_catalog.py`): je Rolle 1 Fall pro Beispiel (`examples.<lang>`) → `expected: role`; Kollisionen (Trigger in ≥2 Rollen) ausgeschlossen, manuell in `catalog.manual.yaml` | `tests/routing-llm-eval/run_eval.sh` |

### 4.4 Akzeptanzkriterien

- **AC-R1** `python3 scripts/sync.py` auf einem Projekt ohne `routing-overrides` und `routing-overrides.format: json` rendert byte-identisch zu heute (Rückfallpfad; AC-01-Hashes nur für den Default-Wechsel neu gepinnt).
- **AC-R2** Default (`format: auto`, alle Provider `route_intent_tool: false`): Routing-Block im Claude-Orchestrator ≤ 9.000 B bei 57 Rollen (heute 32.834 B); Zeilen deterministisch sortiert; zwei Syncs byte-identisch.
- **AC-R3** `roster_in_harness: true` → kein `name_index`, keine Agent table im Orchestrator; `false` → Tabelle bleibt. Kein `if provider ==` (Test `test_provider_agnostic_dispatch.py` grün).
- **AC-R4** Lazy-Detaildatei `<agents_dir>/../routing-details.md` (Pfad per Provider-Config `pipeline_details_dir`-Analogon) enthält alle Felder; der Orchestrator-Prompt verweist mit genau einer Pointer-Zeile.
- **AC-R5** Lint: jede Fehlerklasse aus §4.3 hat einen Fixture-Fall; `sync.py --validate` meldet `RL-*` als Finding; Admin-`POST` mit Fehler → HTTP 400, Datei unverändert.
- **AC-R6** `routing-overrides.roles.<r>.triggers` ändert die gerenderte Zeile; `addressability: excluded` entfernt Rolle aus Zeile **und** enum; unbekannte Rolle → `SyncError`.
- **AC-R7** Direct-Dispatch-Tabelle wird aus `direct_dispatch: true` generiert und ist bei identischen Daten textgleich zu `templates/direct-dispatch-section.md` (Golden); `config/direct-dispatch-section.md` entfällt.
- **AC-R8** Eval-Katalog `catalog.roles.generated.yaml` idempotent (zweimal generieren = kein Diff); mindestens 55 Fälle; `run_eval.sh --dry-run` listet sie ohne LLM-Aufruf.
- **AC-R9** Admin-UI: Editor zeigt Default vs. Override je Feld, „Reset auf Default“ entfernt den Override-Key; Preview zeigt Bytes + Tok-Proxy (Bytes/4, gekennzeichnet) + Lint; Tastaturbedienbar, Labels verknüpft (WCAG 2.1 AA Baseline wie Audit 3 in `audit-top5-execution-plan.md`).
- **AC-R10** `tests/test_context_budgets.py`: Claude-Orchestrator-Ceiling neu gepinnt ≤ 48.000 B (Ist nach Umsetzung + Toleranz); AGENTS.md-Ceiling unverändert oder kleiner.
- **AC-R11** Python 3.9 kompatibel (`from __future__ import annotations`, keine `match`, kein `str.removeprefix` ohne Guard … stdlib + PyYAML).

### 4.5 Migration / Kompatibilität

- `role-defaults.yaml`: Skript-Migration `routing_patterns.* → routing.triggers/examples` + `intents` initial aus Pipeline-Zugehörigkeit/Tier heuristisch, dann manuell gereviewt (88 Rollen); alte Keys werden 1 Minor lang weiter gelesen (Reader akzeptiert beide, Warnung `routing.legacy-patterns`).
- Consumer-Projekte: Minor-Bump (`2.0.0-beta.9` bzw. nächste Minor), CHANGELOG „Changed: routing block compact by default; set `routing-overrides.format: json` to keep the old render“; `--check` meldet Drift einmalig, `sync.py` regeneriert.
- Rollback: `routing-overrides.format: json` + `table-in-orchestrator: always` stellt das heutige Render wieder her (AC-R1); Git-Revert des PR 2 ohne Datenverlust (Overrides bleiben gültig, werden nur ignoriert → Warnung).

## 5. Admin-UI-Konfiguration

### 5.1 Ist

- Server: `scripts/admin-server.py` (6.473 Z.), Routen-Tabellen `:3870-3927`; Token-Auth Bearer-only (`_check_token` `:3654`), Origin/Host-Check für mutierende Requests (`_check_origin` `:3686`); Schreibpfade `_route_put_config` (`:4183`, Section-Validatoren vor Write) und `_write_project_section` (`:5518`, Section-Whitelist `PROJECT_WRITABLE_SECTIONS` `:238`, Guards je Section `:5548-5551`); Schema-Lieferung `GET /api/schema/project` (`:4037`); Preview nur als `POST /api/sync/dry-run` (`:4317`, Volltext-Output) und Cleanup-Preview (`admin-ui.html:5377-5445`, Fingerprint-Confirm-Muster).
- UI: `docs/ui/admin-ui.html` (11.558 Z., Vanilla JS, Router `:11311`), Orchestrator-View `:7178` ohne Routing-Daten; Schema optional geladen (`:11295`).
- Sicherheit offen: #1271 (Stop ohne PID-Identität), #1272 (viz SSE ohne Origin) — betreffen **nicht** den Config-Schreibpfad; Audit 2/3 (`audit-top5-execution-plan.md:60-61`) liefert Security-/A11y-Befunde, auf die der neue Editor aufsetzt.

### 5.2 Soll (Editor „Routing“)

- Neue Route `/project/routing` (Nav-Eintrag neben Orchestrator): Tabelle aller Rollen (aktiv zuerst, inaktiv grau) mit Spalten Intents · Trigger (Tag-Editor, bestehendes `tagEditorField`) · Addressability · size_class · Priorität · direct_dispatch · Quelle (Default/Override-Badge) · Reset.
- Kopfzeile: `format`, `detail-file`, `table-in-orchestrator`; Pipelines-Signal-Keywords als zweiter Block.
- Rechte Spalte „Preview“: `GET /api/routing/preview?provider=` je aktivem Provider → gerenderter Block (monospace), Bytes, Tok-Proxy, Lint-Liste (Fehler blockieren Save, Warnungen nicht); Debounce 400 ms, Preview rechnet serverseitig mit demselben Renderer (kein JS-Duplikat).
- Save: `POST /api/config/project/section {section:"routing-overrides", data}` → Server-Lint fail-closed → `yaml_roundtrip` kommentarerhaltend (bestehender Pfad); danach Hinweis „Sync nötig“ (wie andere Sections; Hash-Mechanik `--check` erkennt Drift).
- Diff/Reset: Client berechnet Default-vs-Override aus `GET /api/routing/model` (`source`-Map); Reset = Key aus Override löschen, nie Default schreiben.
- Provider-Agnostik: Preview iteriert `GET /api/providers` (aktive), Format aus Capabilities; keine Provider-Namen im UI-Code außer als Datum.
- Accessibility: `<table>` mit `<th scope>`, Tag-Editor per Tastatur (Enter/Backspace), Lint-Ausgabe als `role="status"`, Kontrast nach bestehendem Theme.
- Nicht-Ziel UI: Editieren der Framework-Defaults in `role-defaults.yaml` (Submodul-Schutz).

## 6. File-Structure-Map

**Create**
- `docs/specs/2026-11-XX-intent-routing-table-spec.md` — ausgegliederter §4 (PR 1)
- `config/routing/intents.yaml` — Intent-Taxonomie (PR 2)
- `scripts/lib/routing_lint.py` — Lint-Codes `RL-*` (PR 2)
- `scripts/migrate_routing_patterns.py` — einmalige Migration `routing_patterns → routing.*` (PR 2, danach löschbar)
- `scripts/gen_role_routing_eval_catalog.py` + `tests/routing-llm-eval/catalog.roles.generated.yaml` (PR 3)
- `tests/test_routing_model.py`, `tests/test_routing_lint.py`, `tests/test_routing_render_compact_default.py`, `tests/test_routing_overrides_schema.py`, `tests/test_admin_routing_api.py`, `tests/fixtures/routing-golden/{orchestrator-claude.md, routing-details.md, direct-dispatch.md}` (PR 2/3)

**Modify**
- `config/role-defaults.yaml` — 88 Rollen `routing.*` (PR 2, mechanisch + Review)
- `config/project-config.schema.json` — `routing-overrides` (PR 2)
- `config/provider-capabilities.yaml` — nur Kommentar (Konsument `route_intent_tool` bleibt) (PR 2)
- `scripts/lib/delegation_table.py` — `resolve_routing_model`, Reader für alte+neue Keys, Direct-Dispatch aus Modell (PR 2)
- `scripts/lib/agents.py` — `render_routing` (compact default, name_index-Gate, Detaildatei), `derive_keywords` → `triggers[:3]` (PR 2)
- `scripts/lib/config.py:2143-2155, 2367-2389, 2831-2860` — Variablen `INTENT_ROUTING_TOOLS`, `ROUTING_DETAILS_PATH`, `DIRECT_DISPATCH_SECTION` (PR 2)
- `scripts/lib/agent_sync.py:534-548` — Detaildatei schreiben (Writer wie `pipeline-details`) (PR 2)
- `scripts/lib/cli_commands.py` (`_handle_validate`) — Lint-Findings (PR 2)
- `agents/1-generic/orchestrator.md:100-117, 334-342` — Prosa auf compact + Pointer, Agent-table-Gate auf `ROSTER_IN_HARNESS` (PR 2)
- `rules/1-generic/use-orchestrator.md:68-71` — Pointer auf Detaildatei (PR 2)
- `templates/context/partials/agents-table.md` — Spaltenquelle (PR 2)
- `templates/direct-dispatch-section.md` — wird generiert; Datei bleibt als Golden-Referenz bis AC-R7 (PR 2)
- `scripts/admin-server.py:238, 3870-3927, 5518-5551` — Section-Whitelist, 2 GET-Routen, Write-Guard (PR 3)
- `docs/ui/admin-ui.html:1645, 11311` — Nav + View (PR 3)
- `tests/test_context_budgets.py`, `tests/fixtures/ac01-baseline/hashes.json`, `tests/fixtures/compact-golden/`, `tests/fixtures/topology-golden/`, `tests/fixtures/slimming-golden/` — Rebaseline (PR 2)
- `CHANGELOG.md`, `VERSION`, `docs/howto/admin-ui*.md` (PR 2/3)

**Delete**
- `config/direct-dispatch-section.md` (Zweitkopie, PR 2 nach AC-R7)

## 7. Tasks (TDD)

Konvention: ein Task = ein Commit; Test zuerst (fail) → Implementierung → Suite grün. Aufwand S ≤ 1 h, M ≤ ½ Tag, L ≤ 1 Tag (Agent-Zeit). Agent-Vorschlag in Klammern.

### Block A — Spec & Messung (PR 1, Doku-Branch, kein Code)

**Task 0 Messbasis (S, `explorer`)**: Skript .tmp/routing-measure.py (nicht committen): tiktoken cl100k für `.claude/agents/orchestrator.md`, Routing-Zeile, AGENTS.md, Compact-Golden-Block; Ergebnis als Tabelle in Spec §2. AC: Zahlen aus §1.1/§3.1 reproduziert ± 2 %.
**Task 1 Spec ausgliedern (M, `concept-specifier`)**: §4 → `docs/specs/…-spec.md` mit IC-/AC-Nummern, Entscheidungen aus §11 als `DECIDED` eintragen. AC: Review (`concept-reviewer`) ohne offene Blocker; Nutzer setzt `Status: APPROVED`.
**Task 2 Intent-Taxonomie-Entwurf (M, `concept-architect`)**: Liste ~16 Intents + Zuordnung aller 88 keyword-Rollen (Tabelle in Spec-Anhang). AC: jede Rolle ≥ 1 Intent; kein Intent mit > 12 Rollen; Nutzer bestätigt (Entscheidung E3).

### Block B — Datenmodell, Renderer, Rebaseline (PR 2) — Gate: Spec APPROVED

**Task 3 Reader alt+neu (M, `tester`+`developer`)**: `test_routing_model.py::test_reads_legacy_patterns_and_new_routing_equivalently` (fail) → `resolve_routing_model()`; Warnung `routing.legacy-patterns`. AC: beide Schreibweisen → identisches Modell; bestehende `test_routing_tool_definitions.py` grün.
**Task 4 Migration role-defaults (L, `developer`, Review `prompt-engineer`)**: `migrate_routing_patterns.py` idempotent; Lauf; `intents` aus Task-2-Tabelle; Examples ≤ 2/Sprache. AC: `python3 scripts/migrate… --check` = kein Diff beim 2. Lauf; `--validate` grün; Keyword-Ratchet (`routing-language.yaml`) nicht größer.
**Task 5 Lint (M, `tester`+`developer`)**: Fixtures je `RL-*`-Code (fail) → `routing_lint.py`; Einbindung `_handle_validate`. AC: AC-R5; Ist-Repo liefert Liste der heutigen Überlappungen (Scratch), Fehler-Codes nur für echte Konflikte (Overlap ohne priority).
**Task 6 Schema + Overrides (M, `developer`)**: `test_routing_overrides_schema.py` (unbekannte Rolle/Key/Intent fail-closed; Deep-Merge; `excluded` entfernt aus enum) → Schema + Merge in `resolve_routing_model`. AC: AC-R6; `tests/test_schema_*` grün.
**Task 7 Compact-Default-Render + name_index-Gate (M, `developer`)**: Golden `routing-golden/orchestrator-claude.md` aus erwarteter Ausgabe (fail) → `render_routing`; `_render_compact_routing` entkoppeln vom `context-profile`; Gate `roster_in_harness`. AC: AC-R2, AC-R3; `format: json` = heutiger Output (AC-R1).
**Task 8 Lazy-Detaildatei (M, `developer`)**: Writer analog `pipeline-details` (`agent_sync.py`), Platzhalter `ROUTING_DETAILS_PATH`, Pointer-Zeile in `orchestrator.md` + `use-orchestrator.md`. AC: AC-R4; Datei in `generated-file-hashes.json` registriert; `--check` erkennt Drift.
**Task 9 Direct-Dispatch aus Modell (S, `developer`)**: Golden = heutige Tabelle (fail bei Generator-Abweichung) → Generator; `config/direct-dispatch-section.md` löschen. AC: AC-R7; `tests/test_direct_dispatch*` grün.
**Task 10 Agent table Quelle (S, `developer`)**: `active_agents_table.keywords = triggers[:3]`; Gate `ROSTER_IN_HARNESS` auch im full-Profil (`orchestrator.md:334`). AC: AGENTS.md Directory ≤ heutige Bytes; Gemini-Render behält Tabelle.
**Task 11 Rebaseline (M, `developer`, Freigabe Nutzer)**: `test_ac01_render_identity.py --write` nur auf sauberem Stand; compact-/topology-/slimming-Goldens regenerieren; `test_context_budgets.py` Pins neu (AC-R10); Begründung im Commit. AC: Suite grün; Delta-Tabelle (vorher/nachher je Provider×Artefakt) im PR-Text.
**Task 12 CHANGELOG/VERSION/Howto (S, `documenter`)**: Minor-Bump, Migrationshinweis, `docs/howto/routing-overrides.md` (kurz). AC: `--validate` grün; Sprachregeln (Deutsch intern, README Englisch).

### Block C — Admin-UI & Eval (PR 3) — Gate: PR 2 gemergt

**Task 13 API (M, `developer`)**: `test_admin_routing_api.py` (GET model/preview; POST section Lint-Fehler → 400, Datei unverändert; Token/Origin wie andere Routen) → Routen + Guard + Whitelist. AC: AC-R5 (Server-Teil); kein Provider-Literal.
**Task 14 UI-Editor (L, `frontend-component-engineer` oder `developer`, A11y-Review `accessibility-specialist`)**: View `/project/routing`, Tag-Editor, Preview-Panel, Reset. AC: AC-R9; manueller Smoke: Trigger ändern → Preview-Bytes ändern → Save → `sync.py --check` meldet Drift.
**Task 15 Eval-Katalog Rollen (M, `tester`)**: Generator + Idempotenz-Test + `--dry-run`-Listing. AC: AC-R8. **Kein** LLM-Lauf in diesem Task.
**Task 16 Eval-Lauf (S, Nutzer-Gate)**: Kostenschätzung (Fälle × REPEAT × Modell-Preis) in .tmp/; nur nach „Ja“: `REPEAT=1 ./run_eval.sh --provider claude`; Ergebnis als Baseline in Spec §Eval. AC: Trefferquote dokumentiert; Fehlrouten → Issues (durch Nutzer freigegeben), keine Daten-Hotfixes im selben PR.

## 8. PR-Schnitt, Rebaseline, CI-Fallen

| PR | Branch (von `origin/main`) | Inhalt | Rebaseline-Commit | Gate |
|---|---|---|---|---|
| 1 | `docs/intent-routing-spec` | Block A: Spec + Messung + Intent-Tabelle; keine generierten Dateien | keiner (kein Render-Delta) | Nutzer: `Status: APPROVED` |
| 2 | `feat/intent-routing-model` | Block B (Tasks 3-12) | **1 Commit** `chore: rebaseline ac01/compact/topology goldens and context budgets (routing compact)` als **letzter** Commit nach Task 11; vorher kein Golden anfassen | PR 1 gemergt; Phase H Task 8 abgestimmt (§9) |
| 3 | `feat/intent-routing-admin-ui` | Block C (Tasks 13-16) | ggf. 1 Commit nur `generated-file-hashes.json` (Detaildatei-Hash, falls PR 2 ihn nicht enthält) | PR 2 gemergt |

Strikt sequentiell; kein paralleler Branch auf `scripts/lib/agent_sync.py`, `config.py`, `project-config.schema.json`, `admin-ui.html` (Konfliktflächen der Config-Welle, `config-wave-overview.md:16-19`).

CI-Fallen (Checkliste je PR):
- Provider-Literale in `agents/1-generic/*` und `rules/1-generic/*` verboten → Pointer-Zeile nur mit `{{ROUTING_DETAILS_PATH}}`, nie `.claude/…` (Test `test_provider_agnostic_dispatch.py`, Skill `provider-agnostic`).
- Routing-Daten dürfen **nicht** in Templates landen (`test_no_role_routes_in_templates.py`: `Route`-Spalte, `roleA → roleB`, Dispatch-Phrasen) — der compact-Block kommt als Platzhalter-Wert, nicht als Template-Text; Direct-Dispatch-Generator muss das Partial-Format beibehalten, sonst T-ROLE-ARROW.
- Context-Ceilings: jede Render-Änderung bricht `test_context_budgets.py` → nur im Rebaseline-Commit pinnen; Toleranz max(256 B, 2 %, 4 KB).
- Tests dürfen keine gitignorierten generierten Dateien lesen (`.claude/`, `.gemini/`, `.opencode/` in `.gitignore:13-34`) → Messungen über `_make_project` + `tmp_path` wie `test_context_budgets.py:343`.
- Python 3.9 (`orchestration-test.yml:210`): kein `|`-Union zur Laufzeit ohne `from __future__ import annotations`, kein `match`, `dict | dict` vermeiden.
- Compact-Golden/AC-01-`--write` nur auf sauberem `main`-Stand mit Begründung (`test_ac01_render_identity.py:18-21`).
- `generated-file-hashes.json`: neue Detaildatei registrieren, sonst `--check` rot bzw. Drift unerkannt.
- Keyword-Ratchet `routing-language.yaml`: Migration darf die Allowlist nur verkleinern.

## 9. Überschneidungen mit Phasenplänen und Issues

| Quelle | Inhalt dort | Regel hier |
|---|---|---|
| **Phase H Block C** (`docs/superpowers/plans/2026-11-11-phase-h-context-eval.md:241-280`), #1161 Pkt 1/2 | Pkt 1 „gebaut“ (Compact-Separators, `:99`); Task 8 = Mini-Spec Pkt 2 (AGENTS.md-Directory über `roster_in_harness`/`EMIT_AGENT_ROSTER`); Task 7 Backups | **Integrieren:** Task 10 hier = Umsetzung von H-Task 8 im Orchestrator; AGENTS.md-Directory-Teil bleibt in H (Entscheidung 29). Vorschlag: Mini-Spec H-Task 8 verweist auf diese Spec statt eigener; wenn H vor PR 2 mergt, übernimmt PR 2 deren Pins. `name_index`-Streichung (T2) steht in keinem H-Task → hier. |
| **Phase H Block D** (#779/#780 Routing-Sprache) | Sprach-Normierung Keywords/Examples (Design C) | Keine Änderung der Sprachregel hier; Migration (Task 4) hält Ratchet; `examples.<lang>`-Struktur bleibt. |
| **Phase H #969** Eval-Gate (McNemar) | Per-Testfall-Schnittstelle `eval_gate.py` | Task 15/16 liefern Fälle im bestehenden Katalogformat; Gate-Statistik dort. Kostenpflichtige Läufe: nur nach Schätzung + Ja (Task 16). |
| **Phase E Config-Welle** (#1187→#1186→#1188→#1181→#1141; `config-wave-overview.md`), #1209 Template-Gating | Gleiche Konfliktdateien (`schema.json`, `config.py`, `agent_sync.py`, `admin-server.py`, `admin-ui.html`) | PR 2/3 **erst nach** Abschluss der Welle bzw. Rebase darauf; `visibility`/`requires`-Gating nutzt bestehende `{{#if}}`-Whitelist (`variables.py:570-598`) — kein neues Gating-Mechanik-Design (#1209 bleibt dort). |
| **Phase D** #1176, #1168 | BARRIER-Wartestrategie, Trailer | Nicht routing-bedingt → Nicht-Ziel; `orchestrator.md` Konfliktfläche §7 vs. §3 (disjunkt). |
| **Phase G** (Provider-Capabilities, #1171 `provider-tools.yaml`) | Capability-Tabellen | Hier nur Konsum von `route_intent_tool`/`roster_in_harness`; `requires: capability:*` liest dieselbe Datei. |
| **#1244** Session-Ceiling, Roster reduzieren | Token-Ceiling gesamt | AC-R10 pinnt nur Artefakt-Ceilings; Session-Ceiling bleibt #1244 (Phase H). Hinweis dort: Routing-Ersparnis ~7k Tok/Spawn. |
| **#1243** `topology`-Namenskollision | Rename-Entscheidung | `visibility.topologies` nutzt `orchestrator.topology`-Enum; bei Rename nachziehen (Schema-Enum referenzieren). |
| **#1257** Hook-Kernel | Hooks | keine Berührung. |
| **#1271/#1272** Admin/viz Hardening | Stop-PID, SSE-Origin | Neuer Editor nutzt nur bestehende Auth/Origin-Pfade; Audit 2/3 (`audit-top5-execution-plan.md`) vor Task 14 lesen. |
| **Verbesserungsschleifen-Plan** (`docs/plans/2026-11-14-agent-improvement-loop-plan.md`) H1/H6/E1 | route_intent kompakt, AGENTS.md Einzeiler, Compact-Profil aktivieren | **Grenze:** H1 wird **hier** spezifiziert/umgesetzt (Task 7), dort nur Messung (`:205` sieht das bereits vor); E1 (Compact-Profil) ist unabhängig und dort entschieden; H6 = Phase H Task 8. Descriptions-Lint (dort Task 2.3) ist Prompt-Thema, nicht Routing. |
| `docs/concepts/planned/orchestrator-routing-test-suite.md` | Multi-Provider-Eval-Konzept | Task 15 setzt Abschnitt 4.1 für Rollen fort; Konzept-Datei aktualisieren (Status). |

## 10. Risiken

| Risiko | Wahrscheinlichkeit | Gegenmaßnahme |
|---|---|---|
| Kompaktformat verschlechtert Routing kleiner Modelle (Opencode-Default `deepseek-…-flash`) | mittel | Eval-Baseline vor (Task 16 auf `format: json`) und nach; Rückfall `format: json` je Provider via `provider-overrides` |
| Rebaseline-Lawine (4 Golden-Sets + Budgets + Hashes) kollidiert mit Phase-E/H-Rebaselines | hoch | strikt sequentiell, Rebaseline als letzter Commit, Rebase vor Merge; Delta-Tabelle im PR |
| Intent-Taxonomie-Zuordnung von 88 Rollen ist Meinungsarbeit, blockiert PR 2 | mittel | Task 2 in PR 1 mit Nutzer-Review; `intents` zunächst **informativ** (nicht routing-entscheidend), Lint nur Pflichtfeld |
| `test_no_role_routes_in_templates.py` schlägt auf generierter Direct-Dispatch-Tabelle an | mittel | Generator liefert exakt das bisherige Partial-Format (Golden AC-R7) |
| Admin-UI-Editor wächst (11,5k-Zeilen-Datei) | mittel | eine View, keine neue Komponentenbibliothek; Preview serverseitig |
| Legacy-Reader doppelt gepflegt | niedrig | Entfernung mit nächstem Minor; Warnung ab PR 2 |
| Prompt-Caching: Detaildatei-Pfad enthält Provider-Dir → Zeile je Provider verschieden, aber stabil über Zeit | niedrig | kein Datum/Hash im Block (Test) |

## 11. Entscheidungspunkte für den Nutzer

| # | Frage | Optionen | Empfehlung |
|---|---|---|---|
| E1 | Compact-Routing als **Default** für alle Provider ohne `route_intent_tool` (Render-Änderung für alle Consumer) oder nur Opt-in über `routing-overrides.format`? | Default / Opt-in | **Default** (AC-R2); Opt-out via `format: json`. Begründung: kein Provider hat das Tool; −7k Tok/Spawn für alle. |
| E2 | `name_index` bei `roster_in_harness: true` komplett streichen oder auf `agent + name_only_reason` reduzieren? | streichen / reduzieren | **reduzieren** (eine `name-only:`-Zeile, wie IC-04); Namens-Fallback bleibt belegbar. |
| E3 | Intent-Taxonomie einführen (16 Intents, Pflichtfeld) oder nur Trigger-Lint ohne Taxonomie? | Taxonomie / nur Lint | **Taxonomie, zunächst informativ** (Flag in Zeile, Eval-Gruppierung); Routing-Entscheidung bleibt Trigger+Example. Kleinster vollständiger Schritt. |
| E4 | `size_class` je Rolle rendern und im Spec/Plan-Gate referenzieren? | ja / nein | **ja** (ein Flag `S..XL`; ersetzt die prosaische Tier-Tabelle teilweise, Daten statt Prosa). |
| E5 | Direct-Dispatch aus Rollen-Attribut generieren (löscht feste Tabelle + Zweitkopie)? | ja / später | **ja in PR 2** (S-Aufwand, beseitigt Drift-Quelle). |
| E6 | Lazy-Detaildatei einführen oder Contracts einfach weglassen? | Detaildatei / weglassen | **Detaildatei** (Contracts werden für A2A-Handoffs gebraucht; 1 Read on demand). |
| E7 | Admin-UI-Editor in PR 3 oder Routing-Overrides zunächst nur per YAML? | PR 3 / später | **PR 3** wie geplant, aber erst nach Audit 2/3 der Admin-UI (Sicherheit/A11y). |
| E8 | Eval-Lauf (Task 16) genehmigen? Kosten: ~55-60 Fälle × 1 Lauf × Haiku-Klasse (Schätzung < 1 USD; vor Lauf konkret rechnen) | ja / nein | **ja**, einmal vor und einmal nach PR 2 (Baseline-Vergleich). |
| E9 | Reihenfolge zur Phase H: diese Spec ersetzt H-Task 8 Mini-Spec (ein Dokument) oder bleibt getrennt? | ersetzen / getrennt | **ersetzen** für den Orchestrator-Teil; AGENTS.md-Directory-Teil bleibt in H. |
| E10 | Minor-Bump + CHANGELOG „Changed“ für Consumer akzeptiert (Render-Drift bei nächstem `upgrade-meta`)? | ja / nein | **ja**; `--check` zeigt Drift einmalig. |

## 12. Nicht-Ziele

- Kein Rewrite der Rollen-Prompts, keine Block-/Sprach-Normierung (Verbesserungsschleifen-Plan).
- Keine Aktivierung des Compact-**Profils** (E1 dort), keine Rollenreduktion (58 → n).
- Kein `route_intent`-Tool-Registrierung in Harnesses (bleibt capability-gated `false` bis Live-Nachweis, `provider-capabilities.yaml:57-66`).
- Keine Änderung an Pipeline-Semantik, Stage-Details, Reflection-Pairs, Reviewer-Matrix (`config/routing/reviewers.yaml`).
- Keine Hooks/Guards (#1257), kein BARRIER-/Trailer-Fix (#1176/#1168/#1247), kein Session-Token-Ceiling (#1244), kein `topology`-Rename (#1243).
- Kein Editieren von Framework-Defaults (`role-defaults.yaml`) über das Admin-UI.
- Keine Umsetzung in dieser Session: nur Analyse/Plan; kein Sync, Test, Issue, PR, Commit.
