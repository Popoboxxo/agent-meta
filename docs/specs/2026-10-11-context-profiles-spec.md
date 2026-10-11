---
spec-id: SPEC-CONTEXT-PROFILES-2026-10-11
title: Context Profiles (full/compact) — token-effiziente Kontextartefakte für alle 9 Provider
status: DRAFT
related-spec: SPEC-CONTEXT-FILE-MODES-2026-09-13
builds-on: SPEC-844-COMPRESS-ROOT-CONTEXT-2026-10-06, docs/plans/issue-540-baseline.md, docs/guides/context-block-inventory.md
source-study: docs/analysis/2026-10-11-context-budget-provider-study.md
---

# Context Profiles (full/compact) — Spec

> Status: Entwurf (**DRAFT**, 2026-10-11). Der Approval-Marker (`Status: APPROVED`) wird
> ausschließlich vom Nutzer bzw. `concept-reviewer` gesetzt, nie vom Autor. Diese Datei definiert
> Interface-Contracts und Akzeptanzkriterien; sie enthält keine Implementierung und keinen Plan.
> Trace-Anker: `spec-id: SPEC-CONTEXT-PROFILES-2026-10-11`.
>
> Evidenz: alle Zahlen stammen aus `docs/analysis/2026-10-11-context-budget-provider-study.md`
> (im Folgenden „Studie"). Bytes; Tokens ≈ Bytes/4 (grob, siehe Studie §1). Zielwerte in §11 sind
> **Schätzungen/Ziele**, keine Messungen. Nicht verifizierte Aussagen tragen `UNVERIFIED`.
>
> Provider-agnostisch ist Pflicht: Provider-Unterschiede ausschließlich über Config-Keys und
> Capability-Flags (`config/ai-providers.yaml`, `config/provider-capabilities.yaml`), nie über
> `if provider == "Name"` (Skill `provider-agnostic`).

## 0. Korrekturen früherer Aussagen

| # | Frühere Aussage | Korrektur (Studie §9) |
|---|---|---|
| K-a | Orchestrator §12 Few-shot ist 8.5 KB inline | §12 ist ein 3-Zeilen-Pointer von 188 B (Ziel `_wf-orchestrator-reference.md`, 1,355 B). Die frühere Messaussage war falsch; §12 ist kein Kompaktierungshebel. |
| K-b | Die Orchestrator-Datei (90.7 KB) kostet in jedem Turn | Sie kostet pro Orchestrator-Aufruf; in **jedem** Turn nur, wenn der Orchestrator Main-Thread-Agent ist (Claude `--agent orchestrator`, Kimi `--agent`, OpenCode/Mammouth primary). |
| K-c | „AGENTS.md ist bei Claude der Haupt-Bloat" | Falsch: CLAUDE.md ist 2.5 KB, und Claude ignoriert AGENTS.md, wenn CLAUDE.md existiert. Die Claude-Last liegt bei `.claude/rules` (17.9 KB), Harness-Roster (≈ 16.5 KB) und ggf. Orchestrator. |

## 1. Problem / Ziel / Nicht-Ziele

### 1.1 Problem

- Generierte Kontextartefakte sind groß und enthalten viel Struktur-Rauschen: Der Orchestrator
  (90,691 B) besteht zu 62.6 % aus der Routing-Payload (55,170 B pretty JSON), deren `tool{}`-Schema
  bei allen 9 Providern tot ist und in der jede Rolle 4× vorkommt.
- Das bestehende `compact` (#540) wirkt in Konsumentenprojekten kaum: CLAUDE.md −59 B, Orchestrator
  −62 B, AGENTS.md −11.7 %.
- Mehrere Provider lesen generierte Kanäle gar nicht (Codex Root-`rules/`, `.mammouth/rules`,
  `.gemini/rules`, `.github/instructions/*.md`), Lazy-Pointer zeigen ins Leere, und im Gemini-`lazy`-Preset
  gehen 8 Rules verloren. Ein Multi-Provider-AGENTS.md (34,035 B) wird von Codex still bei 32,768 B
  abgeschnitten.
- Es gibt keinen Role-Routing-Eval. Jede Kompaktierung des Routings ist heute qualitativ unbeweisbar.

### 1.2 Ziel

1. Eine Profil-Achse `context-profile: full | compact` steuert **alle** Verdichtungsmaßnahmen
   (Entry-File, Rules, Orchestrator, Bootstraps) gebündelt; Default `full`, byte-identisch zum Ist.
2. „Kein Qualitätsverlust" ist **beweisbar**: Eval-Baseline vor jeder Kompaktierung (QG-1),
   deterministische Informationserhaltung (QG-2), Anker-Registry (QG-3), Budgets in CI (QG-4).
3. Jede aktive Rule ist für jeden aktiven Provider über einen Kanal erreichbar, den der Provider
   wirklich liest; kein generierter Pointer zeigt ins Leere.
4. Harte Provider-Limits (Codex 32 KiB) werden nie überschritten; weiche Limits werden gemeldet.
5. Korrektheitsfehler je Provider (Studie §3) werden als unabhängige Bugfixes vor dem Profil behoben.

### 1.3 Nicht-Ziele

- Kein Ändern des Rollenumfangs im Profil `compact` (Rollen-Teilmengen sind Phase 3, `ultra`/Rollenprofil).
- Keine Änderung der Semantik von `context_file.mode` und `context_file.topology` (SPEC-CONTEXT-FILE-MODES-2026-09-13).
- Kein neuer Template-Dialekt; keine Laufzeit-Komponente beim Provider (alles Sync-Zeit).
- Keine Umformulierung von INSTRUKTION-Inhalten (Klassifikation aus `docs/guides/context-block-inventory.md` gilt).
- Kein callable `route_intent`-Tool (bleibt `ROUTE_INTENT_CALLABLE=false`; Schema bleibt für künftige Provider erhalten, Q11).

## 2. Ist-Zustand (gemessen)

Messbasis: Scratch-Projekte `.tmp/ctx-study`, 62 aktive Rollen (Studie §1).

| Artefakt | Provider | Größe | Quelle |
|---|---|---:|---|
| Orchestrator | Claude | 90,691 B (2,472 Z.) | Studie §2.1 |
| davon §3 Routing | Claude | 56,756 B (62.6 %) | Studie §2.1 |
| Routing-Payload pretty JSON / YAML | alle | 55,170 / 40,564 B | Studie §2.2 |
| Agent-Tabelle in `<context>` | alle | 5,781 B | Studie §2.3 |
| CLAUDE.md | Claude | 2,509 B | Studie §3.1 |
| `.claude/rules` (19) | Claude | 17,880–18,297 B | Studie §3.1 |
| Main-Thread-Set Default / `lazy` | Claude | ≈ 38.8 KB / ≈ 31.2 KB | Studie §3.1 |
| AGENTS.md full / compact / lazy | Codex/OpenCode/Kimi | 25,560–25,632 / 22,571–22,643 / 16,745–16,813 B | Studie §2.6 |
| AGENTS.md full / compact | Gemini | 33,037 / 23,032 B | Studie §2.6 |
| AGENTS.md Multi-Provider full / compact | 6 AGENTS.md-Provider | 34,035 / 24,030 B | Studie §2.6 |
| Main-Turn | Codex / OpenCode / Mammouth | ≈ 82.9 / ≈ 70 / ≈ 70 KB | Studie §3.2–3.4 (Runtime) |
| Orchestrator-Child | Codex / OpenCode | 143 KB / 146 KB | Studie §3.2–3.3 (Runtime) |
| Always-on Rules | Continue | 18,591 B | Studie §3.8 |
| copilot-instructions.md | Copilot | 9,247 B | Studie §3.9 |
| Generierter AGENTS.md-Anteil | Kimi / ZCode | ≈ 42 / ≈ 43 KB | Studie §3.5–3.6 |

## 3. Befunde

Severity: **kritisch** (Funktions-/Inhaltsverlust) · **hoch** (falsches Verhalten oder großer Token-Hebel) · **mittel** · **niedrig**.

| ID | Befund | Evidenz | Severity | Phase |
|---|---|---|---|---|
| F-01 | Routing-Payload dominiert den Orchestrator: 55,170 B pretty, Whitespace ≈ 19–21 %, `tool{}`-Schema (2,780 B) tot, weil `ROUTE_INTENT_CALLABLE=false` bei allen 9 Providern | Studie §2.1, §2.2; `agents.py:235-415`, `agent_sync.py:512,519` | hoch | 2 |
| F-02 | Routing-Daten redundant/fehlerhaft: jede Rolle 4× im Orchestrator; `input_contracts`/`output_contract`/`parallel`/`short_desc` fürs Routing unnötig; 55 von 76 Beispielen ohne neues Signal; Keywords doppelt in `role-defaults.yaml` (87 von 92 identisch); `template-auditor` name_only mit Keyword-Regel, Szenario-Assert 76 widersprüchlich | Studie §2.2 | mittel | 1 (Daten), 2 (Render) |
| F-03 | Kein Role-Routing-LLM-Eval; `tests/routing-llm-eval` prüft nur Pipeline-Routing | Studie §2.4 | hoch | 0 |
| F-04 | Codex schneidet AGENTS.md bei 32,768 B still ab (Modell erhielt exakt 32,769 B, Ende `define_subagent(nam`); Multi-Provider full = 34,035 B; kein Cap-Check | Studie §3.2 (Runtime) | kritisch | 1 |
| F-05 | `shared_users` aus dem ganzen Katalog statt aus aktiven Providern → Einzelprovider-Projekte embedden Rules, Pfadlisten aller 6 mit „ bzw. " verbunden, Lazy-Kanal blockiert | `context.py:1599-1625`, `317-336`, `1776-1799` | hoch | 1 |
| F-06 | Hängende Lazy-Pointer: keine Skills für Codex (`.agents/skills`), Mammouth (`.mammouth/skills`), Gemini, Continue; Gemini-`lazy` verliert 8 Rules vollständig; Lazy-Tabelle nennt ≥ 10 agent-meta-interne Skills | Studie §4.4; `rules.py:305`; `context.py:1615-1617` | kritisch | 1 |
| F-07 | Generierte, aber ungelesene Kanäle: Codex Root-`rules/` + `.rules` (18,380 B), `.mammouth/rules` (18,387 B), `.gemini/rules` (17,880 B), `.github/instructions/*.md` (17,988 B), `CLAUDE.personal.md`/`AGENTS.personal.md` | Studie §4.3 | hoch | 1 |
| F-08 | Gemini CLI erhält keinen Projektkontext (kein `context.fileName`); Agent-Frontmatter verletzt strict-Schema (SOURCE-DERIVED); Bootstrap fordert Lesen von 590,365 B | Studie §3.7 | kritisch | 1 |
| F-09 | Codex-Orchestrator-Child ohne Multi-Agent-Tools (keine `.codex/config.toml`, `max_depth`); dokumentierte `spawn_agent`-Parameter falsch | Studie §3.2 (Runtime) | kritisch | 1 |
| F-10 | Kimi-Orchestrator kann nicht dispatchen (kein `subagents:`, `TodoWrite` statt `TodoList`, kein AgentSwarm, `hint`≠`whenToUse`); Worker sehen AGENTS.md nie; Gate nur beratend | Studie §3.5 | kritisch | 1 (+3: D-1) |
| F-11 | Mammouth: kein `mode` (alle 62 im Tab-Zyklus), Claude-Toolnamen inert → Orchestrator ohne `task`; Capability `subagent_dispatch:false` falsch; kein `subagent_depth`; Delegationssyntax gemischt | Studie §3.4 (Runtime) | hoch | 1 |
| F-12 | ZCode: Bootstrap-Block für die CLI obsolet (Agenten werden automatisch geladen) und weist Lesen von 562,718 B (≈ 140k tok) an; Parallelität untertrieben; AGENTS.md in jeden Subagenten | Studie §3.6 | hoch | 1 |
| F-13 | Copilot: Rules nie gelesen (Suffix `.instructions.md` fehlt), Agent-Name `orchestrator.agent` (`agent_sync.py:892`), Skills-Pfad falsch, Review liest nur 4,000 Zeichen; Kontextdatei zu 9,007 von 9,247 B Header + Agententabelle | Studie §3.9 | hoch | 1 |
| F-14 | Continue: 18,591 B Rules ohne Frontmatter immer aktiv (≈ 28 % des 16,384-Token-Template-Fensters); `lazy` No-op; Kontextdatei mit unaufgelösten Platzhaltern; Orchestrator im Chat unerreichbar | Studie §3.8 | mittel | 1 (+2) |
| F-15 | `AGENT_DELEGATION_TABLE`: doppelter Header, Leerzeilen zwischen Zeilen (ungültige Tabelle), Tier/Parallel nie gefüllt; Agent Directory (5,836–5,870 B) dupliziert das Harness-Roster | Studie §2.3, §2.6; `config.py:1694-1710` | mittel | 1 (Fix), 2 (Profil) |
| F-16 | Entry-File-Rauschen: eingebettete Rules 64 % der AGENTS.md; Claude-Hook-Referenzprosa (Branch-Guard Terminologie 1,193 B + Grenzen 1,785 B, A2A-Grenzen 2,718 B) bei allen; 7 unaufgelöste Platzhalter (929 B); falsches ROUTING-Banner; Provider-Listen-Boilerplate | Studie §2.6 | mittel | 1 (Fehler), 2 (Dichte) |
| F-17 | Fehlerhafte Capability-/Doku-Daten: `claude -a` (`ai-providers.yaml:97`), Kimi nearest-wins (`provider-capabilities.yaml:358`), ZCode `parallel_execution:false`, Mammouth `subagent_dispatch:false`, Gemini `.gemini/agents` nur für Antigravity zutreffend, Copilot-Altpfade, `docs/providers/codex.md:118-124`, `docs/providers/gemini-cli.md` veraltet; OpenCode v2 verwirft `subagent_depth`; `**/AGENTS.md`-Deny im Multi-Provider-`opencode.json` | Studie §3 | mittel | 0 (Doku), 1 (Daten) |
| F-18 | Keine Mess-/Budget-Werkzeuge: `context_size.py` prüft nur Zeilen der Kontextdatei, keine Agentendateien, keine Provider-Caps, kein Token-Report, keine Anker-Registry | Studie §2.4 | mittel | 0 |

## 4. Konzept

### 4.1 Achsen

| Key | Achse | Werte | Default | Persistiert |
|---|---|---|---|---|
| `context-profile` (**neu**, Top-Level `project.yaml`) | Bündel aller Verdichtungsmaßnahmen | `full` \| `compact` | `full` | nein (fehlender Key ⇒ `full`, Ausgabe byte-identisch) |
| `provider-overrides.<Provider>.context-profile` (**neu**) | Profil je Provider | wie oben | erbt global | nein |
| `context_file.mode` (bestehend) | Dichte des Entry-File-Managed-Blocks | `full` \| `compact` | `full` | unverändert |
| `context_file.topology` (bestehend) | Dateitopologie | `unified` \| `per-provider` | `unified` | unverändert |
| `roles:` (bestehend) | Rollen-Allowlist | Liste | alle | unverändert (Phase-3-Hebel) |

**Präzedenz** (je Einzel-Einstellung): explizit gesetzte Untereinstellung (`context_file.mode`,
`rules-preset`, …) > `provider-overrides.<P>.context-profile` > `context-profile` > Default.
`compact` impliziert `context_file.mode: compact`, sofern `context_file.mode` nicht explizit gesetzt ist.
Aufgelöste Werte werden je Provider in `sync.log` protokolliert.

**Shared-File-Regel:** Teilen sich Provider mit unterschiedlichem Profil eine Datei (AGENTS.md-Gruppe),
gilt für diese Datei das Profil `full`, wenn mindestens ein Teiler `full` hat (sichere Seite), und
`sync.log` meldet `context-profile.shared-file-downgrade` (WARN). Entscheidung ist Q12-abhängig.

### 4.2 Inhalt Profil `compact` (C1–C7)

| ID | Gegenstand | `full` | `compact` |
|---|---|---|---|
| C1 | Routing im Orchestrator §3 | JSON/YAML wie heute, byte-stabil | Zeilenformat B (IC-04), wenn `ROUTE_INTENT_CALLABLE=false`; Prosa per Profil-Konditional angepasst |
| C2 | Orchestrator-Abschnitte | wie heute | §2a → Pointer auf `PIPELINE_DETAILS_DIR`-Dateien; §9 → Kern + Pointer; Agent-Tabelle in `<context>` entfällt bei `roster_in_harness: true`, sonst Namensliste; §1, §2, §4, §5, §6/Direkter Dispatch, §7 Barrier, §11 **verbatim** |
| C3 | Entry-File AGENTS.md-Gruppe | wie heute | Gate-Card (≤ ~3 KB) + Pointer nur auf existierende Pfade + kompakte Agentenliste (entfällt bei `roster_in_harness`); Ziel ≤ ~8 KB Einzelprovider; harter Cap in Multi-Provider (< 32,768 B inkl. Bootstraps) |
| C4 | Bootstrap-Blöcke | wie heute (nach Phase-1-Fixes) | nur für aktive Provider, wo möglich nicht in der geteilten Datei; ZCode-Bootstrap entfällt nach Verifikation; Gemini-Bootstrap durch native statische Discovery (`.agents/agents`/`.gemini/agents`) ersetzt, wo verifiziert |
| C5 | Rules | wie heute (nach Phase-1-Fixes) | REFERENCE-Anteile lazy; INSTRUKTION-Kerne embedded; Claude `paths:`; Continue `alwaysApply:false`+`description`; Copilot `*.instructions.md`+`applyTo` |
| C6 | CLAUDE.md | wie heute | Maintainer-/Provenienz-Notizen als Block-HTML-Kommentare (nur in CLAUDE.md) |
| C7 | Budgets | Ist-Werte als Obergrenzen | Zielwerte; Caps als Config-Keys |

Gate-Card-Inhalt (verbatim aus den Quell-Rules): CRITICAL GATE, Git Delegation, Branch-Guard-Kern,
Commit-Konventionen, Sprachregeln, Singleton-Regel, MCP-Deny-Listen.

### 4.3 Reachability-Invariante

Für jedes Paar (aktiver Provider P, aktive Rule R) existiert mindestens ein Kanal
`c ∈ rules_read_channels(P)`, über den R (bzw. deren INSTRUKTION-Kern + Referenz-Skill) an P geliefert wird;
jeder in einem generierten Artefakt genannte Pfad/Skill existiert nach dem Sync. Verletzung = Befund
`context.rule-unreachable` bzw. `context.dangling-pointer` (Phase 0 WARN, ab Phase 1 ERROR).

## 5. Interface-Contracts

### IC-01 Konfiguration und Schema
- `config/project-config.schema.json`: Top-Level `context-profile` (`enum: [full, compact]`, Default wird
  nicht persistiert); unter dem bestehenden `provider-overrides`-Muster je Provider `context-profile`
  (gleiche Enum, `additionalProperties: false` wie beim bestehenden `context_file.provider-overrides`).
  Phase 3 erweitert die Enum um `ultra` (IC-16).
- `templates/configs/project.yaml.example`: auskommentiertes Beispiel.
- Fehlerpfad: unbekannter Wert → `--validate`-Fehler `context-profile.invalid` mit erlaubten Werten; Sync bricht ab.

### IC-02 Profil-Auflösung `scripts/lib/context_profile.py` (neu)
```python
@dataclass(frozen=True)
class ResolvedContextProfile:
    provider: str
    profile: Literal["full", "compact"]
    context_file_mode: Literal["full", "compact"]
    rules_preset: str
    sources: dict[str, Literal["explicit", "provider-override", "profile", "default"]]

def resolve_context_profile(config: dict, provider: str) -> ResolvedContextProfile
def resolve_shared_file_profile(profiles: Iterable[ResolvedContextProfile]) -> Literal["full", "compact"]
```
- Einhängepunkt: `COMPACT_MODE`-Ableitung in `scripts/lib/config.py` (Bereich `:1382-1395`) liest
  `context_file_mode` aus dem aufgelösten Profil; explizites `context_file.mode` gewinnt (Präzedenz §4.1).
- Neue Variablen `CONTEXT_PROFILE` (`full`|`compact`) und `CONTEXT_PROFILE_COMPACT` (`true`|`false`);
  Registrierung als Built-ins in `scripts/lib/consistency/placeholders.py`.
- Logging: eine Zeile je Provider `context-profile: <P> profile=<…> mode=<…> preset=<…> (sources: …)`.

### IC-03 Konditional-Mechanismus
- `CONTEXT_PROFILE_COMPACT` wird in die Whitelist von `strip_inactive_conditional_blocks` (`config.py`)
  aufgenommen. Weil dieselbe Funktion im nativen Rules-Pfad (`rules.py`) läuft, gilt:
  Quell-Rules unter `rules/` dürfen `{{#if CONTEXT_PROFILE_COMPACT}}` **nicht** enthalten.
  Neuer Consistency-Check `context-profile.marker-in-rule` (ERROR). Rule-Kompaktierung läuft
  ausschließlich über die bestehende `compact_embedded_rule()`-Transform (`context.py:1562-1585`) und IC-07.
- `COMPACT_MODE` bleibt unverändert außerhalb der Whitelist (Verhalten #540 unverändert).

### IC-04 Routing-Zeilenformat `scripts/lib/agents.py`
```python
def render_routing_lines(
    rules: list[dict], pipelines: list[dict], name_only: list[dict]
) -> str
def select_routing_examples(rule: dict) -> list[str]
```
- Aktiv nur, wenn `CONTEXT_PROFILE_COMPACT` und `ROUTE_INTENT_CALLABLE=false`; sonst bestehender Pfad
  (`json` | `yaml_text_block`) unverändert. Bei `ROUTE_INTENT_CALLABLE=true` bleibt `tool{}` erhalten.
- Zeile je Keyword-Regel: `<agent>|<flags>|<kw1>;<kw2>;…|<example>[ / <example>…]`.
  - Keyword-Trenner `;` (Keywords können Kommas enthalten). Enthält ein Keyword `;` oder `|` → `SyncError`
    mit Rolle und Keyword.
  - `flags` nur bei Nicht-Default, kommasepariert, Reihenfolge fest: `req` (tier required), `rec`
    (tier recommended), `orch-only`, `name-only`; leer ⇒ `||`.
  - **Alle** Keywords bleiben.
  - `select_routing_examples`: erstes Beispiel plus jedes weitere, das **keines** der eigenen Keywords der
    Rolle enthält (Vergleich case-insensitiv, Teilstring); Reihenfolge wie in der Quelle.
- Pipelines: eine Zeile je Pipeline `pipeline:<name>|<alle signal_keywords mit ;>`. Single-Source: im
  `compact`-Profil bleibt nur die Zeilenform in §3; die §2-Pipeline-Tabelle verweist darauf (revidierbar per Eval).
- Name-only: genau eine Zeile `name-only: <agent> (<reason>); …` mit allen `name_only`-Rollen und Gründen.
- Entfällt im `compact`-Profil: `parallel`, `input_contracts`, `output_contract` (Pointer-Satz: „Contracts
  stehen in der Agentendatei bzw. `role-defaults.yaml`"), `short_desc`, `addressability` (abgeleitet),
  `tool{}` (solange `ROUTE_INTENT_CALLABLE=false`).
- Zeilen sortiert nach Agentenname (Byte-Stabilität).

### IC-05 Orchestrator-Template `agents/1-generic/orchestrator.md`
- §2a, §9, Agent-Tabelle in `<context>` und §3-Prosa erhalten `{{#if CONTEXT_PROFILE_COMPACT}}…{{else}}…{{/if}}`.
  Der `{{else}}`-Zweig ist der **unveränderte** heutige Text (`full` byte-stabil).
- §2a compact: Satz + Pointer `{{PIPELINE_DETAILS_DIR}}/<pipeline>.md` (bestehende Dateien).
- §9 compact: Schwellen und Pflichtaktionen verbatim, Begründungsprosa → Pointer `_wf-orchestrator-reference.md`.
- Agent-Tabelle compact: entfällt, wenn Capability `roster_in_harness: true`; sonst kommaseparierte Namensliste.
- Version-Bump gemäß `rules/2-platform/agent-meta-conventions.md`; abgeleitete Plattform-Varianten (`based-on`) prüfen.

### IC-06 Entry-File AGENTS.md-Gruppe
- Neue Partials `templates/context/partials/gate-card.md` und `templates/context/partials/agents-list-compact.md`;
  `templates/context/agents-managed.md` wählt per `CONTEXT_PROFILE_COMPACT` zwischen `rules-embedded`/`agents-table`
  und `gate-card`/`agents-list-compact`.
- `gate-card.md` bezieht die Gate-Texte per Section-Extraktion aus den Quell-Rules (keine Kopie im Partial);
  Quelle der Abschnittsnamen: `config/context-anchors.yaml` (`gate_card_sections`, IC-12). Fehlender Abschnitt → `SyncError`.
- Pointer nur auf Pfade/Skills, die nach dem Sync existieren (IC-10 `context.dangling-pointer`).
- `agents-list-compact.md`: eine Zeile je Agent `- <name>: <Kurzbeschreibung>` ohne Leerzeilen; entfällt, wenn
  alle Teiler `roster_in_harness: true` haben.
- Fehlerpfad: Ergebnis ≥ `context_hard_cap_bytes` eines Lesers → `SyncError` `context.over-hard-cap` (nie still schreiben).

### IC-07 Rules-Kanäle und REFERENCE-Klasse
- Sektionsklassifikation erweitert die bestehende Tabelle `_COMPACT_PLATFORM_RULES` (`context.py:1521`)
  um generische Rules mit REFERENCE-Anteilen: `a2a-delegation-gates` (lange Teile), `branch-guard`
  („Bekannte Grenzen", „Guard-Terminologie"), `submodule-protection`, `security-paved-roads` (Detail).
  INSTRUKTION-Kerne bleiben embedded (Klassifikation `docs/guides/context-block-inventory.md`).
- Entfernte REFERENCE-Teile werden für jeden aktiven Provider mit Skills-Kanal als Skill geschrieben
  (Phase-1-Fix IC-15 Nr. 2); ohne Skills-Kanal bleibt der Volltext embedded (Invariante §4.3).
- `lazy`-Semantik: eine Rule darf aus dem Embed nur entfernt werden, wenn sie für jeden Teiler über einen
  gelesenen Kanal erreichbar ist; sonst Fallback auf embed + WARN.
- Kanal-Metadaten je Provider via Capability `rules_read_channels` (IC-09): Claude `paths:`-Frontmatter für
  code-gebundene Rules (Phase 3); Continue `alwaysApply: false` + `description`; Copilot
  `.github/instructions/<rule>.instructions.md` + `applyTo`/`description`.

### IC-08 CLAUDE.md-Notizen
- Maintainer-/Provenienz-Notizen des Managed-Blocks werden im `compact`-Profil als Block-HTML-Kommentare
  gerendert (Claude entfernt sie vor der Injektion, Studie §3.1). Gilt nur für Dateien, deren alleiniger Leser
  Capability `strips_html_comments: true` hat (Claude); nie in geteilten Dateien, da andere Provider, die
  CLAUDE.md lesen, sich anders verhalten können.

### IC-09 Provider-Budgets und Capabilities (Config, keine Literale)
Neue Keys in `config/provider-capabilities.yaml` (bzw. `config/ai-providers.yaml`, je nach bestehendem Ort verwandter Keys):

| Key | Typ | Beispielwerte (Studie) |
|---|---|---|
| `context_hard_cap_bytes` | int\|null | Codex 32768; ZCode 100 KiB |
| `context_soft_cap_bytes` | int\|null | Kimi 32768 (Warnung) |
| `context_soft_cap_chars` | int\|null | Copilot 4000 (Review, je Instruktionsdatei); Antigravity 12000 (**UNVERIFIED**) |
| `context_soft_cap_lines` | int\|null | Claude 200 (CLAUDE.md) |
| `roster_in_harness` | bool | true: Claude, Codex, OpenCode, Mammouth, Kimi, ZCode |
| `agents_md_visible_to_subagents` | bool | true: Codex (Child erhält AGENTS.md), OpenCode, ZCode; false: Kimi |
| `rules_read_channels` | geordnete Liste aus `embedded`\|`native-rules-dir`\|`skills`\|`path-scoped` | z. B. Codex `[embedded, skills]` |
| `skills_discovery_dirs` | Liste | Codex `[.agents/skills]`; Mammouth `[.mammouth/skills]`; Copilot `[.github/skills, .claude/skills, .agents/skills]` |
| `main_agent_selectable` | bool | true: Claude, Kimi, OpenCode; false: ZCode |
| `agents_md_precedence` | `concatenate`\|`nearest` | Codex/Kimi `concatenate`; ZCode `nearest` |
| `required_depth` | int | 2 (Orchestrator → Worker) |
| `strips_html_comments` | bool | Claude true |

Datenkorrekturen (F-17): ZCode Parallelität, Kimi `agents_md_precedence`, Mammouth `subagent_dispatch`,
Gemini `.gemini/agents` nur Antigravity, Copilot-Pfade, Claude `orchestrator_hint` `--agent`.
Code liest ausschließlich diese Keys; Guard `test_no_provider_literal_usage_in_lib` bleibt grün.

### IC-10 Consistency-Checks `scripts/lib/consistency/context_budget.py` (neu)

| Check-ID | Level | Bedingung |
|---|---|---|
| `context.over-hard-cap` | ERROR | Artefakt (inkl. Bootstrap-Regionen) ≥ `context_hard_cap_bytes` eines Lesers |
| `context.over-soft-cap` | WARN | über `context_soft_cap_*` |
| `context.dangling-pointer` | Phase 0 WARN, ab Phase 1 ERROR | in generiertem Artefakt genannter Pfad/Skill existiert nicht |
| `context.rule-unreachable` | Phase 0 WARN, ab Phase 1 ERROR | Invariante §4.3 verletzt |
| `context.unread-channel` | WARN | generiertes Verzeichnis ∉ `rules_read_channels`/Discovery des Providers (Ausnahmen in `config/context-anchors.yaml: intentional_unread`); Entfernung in Phase 1 |
| `context.token-report` | INFO | Report-Zeile je Provider (Quelle IC-11) |
| `context-profile.marker-in-rule` | ERROR | IC-03 |

### IC-11 CLI `--context-report`
- `sync.py --context-report [--json] [--profile full|compact|both]`: je aktivem Provider Entry-File, Rules
  (je Kanal), Orchestrator, geschätztes Harness-Roster, Always-loaded-Set, Caps, Δ `full` vs `compact`.
  Read-only; rendert in ein Temp-Verzeichnis unter `.tmp/`, schreibt nichts ins Projekt. Exit 0; Exit 1 nur bei
  `context.over-hard-cap`.
- JSON-Schema: `{provider: {artifact: {bytes, lines, tokens_est, tokens_real?, cap, cap_kind}}}`.
- `scripts/measure_context.py --project <path>` nutzt dieselbe Messfunktion (keine Doppelimplementierung).
- `tokens_real` optional, sobald in Phase 0 ein Tokenizer festgelegt ist. Stdlib-Pflicht: externer Tokenizer
  nur in `tests/`/manuell, nicht in `scripts/lib`.

### IC-12 Anker-Registry `config/context-anchors.yaml` (neu)
```yaml
anchors:
  <artifact-kind>:            # entry-file | claude-md | orchestrator | rules-native | gate-card
    all-profiles: [<string>…]
    compact-only: [<string>…]
gate_card_sections: [<rule-stem>#<heading>…]
intentional_unread: [<path-glob>…]
```
Pflichtanker mindestens: CRITICAL-GATE-Satz, Singleton-Regel, `STATUS`/`RESULT`/`ARTIFACTS`-Contract,
MCP-Deny-Tokens (`delete_conclusion`, `set_config`, `browser_run_code_unsafe`, `workspace.delete`, …),
Branch-Guard „keine Code-Änderungen auf main", Sprachregel, Commit-Konventionen.
Test `tests/test_context_anchors.py` prüft je Provider × Profil.

### IC-13 Role-Routing-Eval (QG-1)
- Generator `scripts/gen_role_routing_eval_catalog.py` (neu) → `tests/routing-llm-eval/roles/catalog.generated.yaml`;
  kuratiert `tests/routing-llm-eval/roles/catalog.manual.yaml`; Promptfoo-Config nach dem Muster
  `scripts/gen_promptfoo_config.py`.
- Korpus: jedes Keyword und jedes Beispiel aus `role-defaults` (positiv); kuratierte Paraphrasen für ≥ 20 Rollen;
  Negative/Mehrdeutige/Kollisionen (Studie §2.2 Kollisionstabelle); Name-only-Dispatch-Fälle.
- Erwartete Ausgabe je Fall: `{target: <agent> | pipeline:<name> | ASK, tier_escalation?: bool}`.
- System-Prompt der Eval = gerenderte Orchestrator-Datei des jeweiligen Profils (keine Kurzfassung).
- ≥ 2 Modellklassen (klein/schnell + balanced; optional ein Nicht-Anthropic-Modell).
- Metriken: Top-1-Accuracy, Ambiguität→Rückfrage-Rate, Wrong-Pipeline-Rate, Tier-/orch-only-Eskalation.
- Ergebnisablage: `tests/routing-llm-eval/roles/baseline/<date>-<model>-<profile>.json` (versioniert, mit Modell-IDs und Parametern).
- Läuft manuell/CI-nightly (benötigt LLM); nicht Teil des Default-CI.

### IC-14 Runtime-Capture-Harness (QG-7)
`tests/manual/context-capture/` (neu, manuell): Mock-LLM-Server + Runner-Skripte aus der Studie; Assertions je
Runtime: AGENTS.md nicht abgeschnitten, Skills gelistet, Rules erreicht, Orchestrator-Child hat Dispatch-Tools.
Ausgabe als JSON-Report unter `.tmp/`. Abgedeckte Runtimes zunächst: OpenCode, Codex, Mammouth (wie Studie).

### IC-15 Phase-1-Korrekturen (je eigener Issue/PR, eigener Red/Green-Test — QG-8)

| Nr. | Fix | Ort (Zeilen aus der Studie; sonst UNVERIFIED) | Befund |
|---|---|---|---|
| 1 | `shared_users` auf **aktive** Provider begrenzen; Pfadlisten nur aktiver Teiler | `context.py:1599-1625`, `317-336`, `1776-1799` | F-05 |
| 2 | Lazy-Skills für jeden aktiven Provider mit Skills-Dir schreiben (Codex `.agents/skills`, Mammouth `.mammouth/skills`, Gemini/Antigravity `.agents/skills`, Continue `.continue/skills`, Copilot `.github/skills`) — behebt hängende Pointer und den Gemini-Inhaltsverlust | `rules.py:305`, `context.py:1615-1617` | F-06 |
| 3 | Copilot: Rules als `*.instructions.md` + `applyTo`/`description`; Agent-Name-Bug; Skills-Pfad | `agent_sync.py:892`; Copilot-Pfade in Capabilities | F-13 |
| 4 | Codex: `.codex/config.toml` mit `[agents] max_depth` ≥ `required_depth`; Hard-Cap-Check (32 KiB); `spawn_agent`-Parameter (`agent_type`, `message`, `items`, `fork_context`) in der Delegationssyntax | Ort der Delegationssyntax-Config UNVERIFIED | F-04, F-09 |
| 5 | Kimi: Frontmatter `subagents:`-Allowlist, Tool-Mapping (`Agent`, `AgentSwarm`, `TodoList`), `hint` → `whenToUse` | Kimi-Agent-Transform (Ort UNVERIFIED) | F-10 |
| 6 | Mammouth: `mode`, kleingeschriebene `permission` inkl. `task`/`todowrite`, `subagent_depth`, Capability + Delegationssyntax | `provider-capabilities.yaml:231-247` | F-11 |
| 7 | ZCode: obsoleten Bootstrap für die CLI entfernen; Parallel-Capability korrigieren | `scripts/lib/bootstrap.py` | F-12 |
| 8 | Gemini: `context.fileName` bzw. `GEMINI.md` für Gemini CLI; strict-schema-sichere Agent-Frontmatter (erst zur Laufzeit verifizieren, Q3); kein `.gemini/rules` mehr | Settings-/Agent-Transform (Ort UNVERIFIED) | F-08, F-07 |
| 9 | Ungelesene Verzeichnisse stoppen/verlagern: `.mammouth/rules`, Root-`rules/` für Codex, Personal-Dateien nur, wenn der Provider sie liest (`CLAUDE.local.md` statt `CLAUDE.personal.md`) | Rules-/Context-Writer | F-07 |
| 10 | Continue: Rule-Frontmatter (`alwaysApply`, `description`); unaufgelöste Platzhalter in `project-context.md` | Continue-Rules-Writer (Ort UNVERIFIED) | F-14 |
| 11 | `AGENT_DELEGATION_TABLE`: ein Header, keine Leerzeilen (ändert `full` bewusst ⇒ Golden-Rebaseline) | `config.py:1694-1710`, `agents-table.md`, `orchestrator.md:266-267` | F-15 |
| 12 | Provider-Listen-Rauschen, tote Skill-Tabelle (nur existierende Skills), unaufgelöste Platzhalter, ROUTING-Banner nur für aktive Provider | Partials `header.md`, Lazy-Tabelle | F-16 |
| 13 | `claude -a` → `claude --agent` | `ai-providers.yaml:97` | F-17 |
| 14 | `template-auditor`: name_only ohne Keyword-Regel **oder** §3-Text anpassen (Q9); Szenario 76 korrigieren | `role-defaults.yaml`, `tests/scenarios/asserts/76-template-auditor-role.sh:63-76` | F-02 |
| 15 | Keyword-Single-Source in `role-defaults.yaml` (`routing.intent_keywords` vs. `routing_patterns.keywords`) | `tests/test_routing_tool_definitions.py:47-64`, `scripts/hermes_export.py:270` | F-02 |
| 16 | OpenCode: `subagent_depth` auf v2 erhalten oder Tiefe anders setzen; kein `**/AGENTS.md`-Deny, wenn OpenCode aktiv | `context.py:1340-1371` (`:1367`) | F-17 |

### IC-16 Phase-3-Erweiterungspunkte (Default aus, eval-gated)
- Profil `ultra` / Rollenprofil: kuratierte Rollenteilmengen über die bestehende `roles:`-Allowlist; verkleinert
  Routing, Roster (≈ 16.5 KB für 62 Rollen; 63 Rollen kosten 16–19 KB pro Main-Turn in den `task`/`spawn_agent`-
  Beschreibungen von Codex/OpenCode/Mammouth) und Directory proportional; zusätzlich OpenCode/Mammouth
  `permission.task`-Deny/hidden.
- Rollen-Key `inherit-project-context: bool` (Default true) → Claude `omitClaudeMd`, ZCode `injectAgentsMd`.
- Kimi: Gate-Card in Worker-Bodies via `${agents_md}` (D-1) oder Plugin-`systemPrompt`.
- Admin-UI: Profil-Umschalter + Report-Ansicht. Claude `paths:`-Scoping. `permission.task`-Trimming.

## 6. Datenfluss

```
project.yaml (context-profile, provider-overrides.<P>.context-profile, context_file.*, rules-preset, roles)
        │
        ▼ resolve_context_profile (IC-02) ── sync.log: aufgelöste Werte je Provider
        │
        ├─► build_variables: CONTEXT_PROFILE, CONTEXT_PROFILE_COMPACT, COMPACT_MODE (abgeleitet)
        │
        ├─► Orchestrator-Render ── C1 render_routing_lines (IC-04) | JSON/YAML (full)
        │                       └─ C2 Konditionale §2a/§9/<context> (IC-05)
        ├─► Entry-File ── shared_users = aktive Provider (IC-15/1)
        │               └─ gate-card | rules-embedded, agents-list-compact | agents-table (IC-06)
        ├─► Rules ── Kanal je rules_read_channels (IC-07/IC-09) ── Skills je skills_discovery_dirs
        ├─► Bootstraps ── nur aktive Provider (C4)
        │
        ▼ write_checked (byte-stabil, sortiert, keine Zeitstempel in dynamischer Position)
        │
        ▼ Consistency (IC-10): Caps, Dangling, Reachability, Unread, Anker (IC-12)
        │
        ▼ --context-report (IC-11) ──► CI-Budgets (QG-4)
                                  └─► Role-Routing-Eval nightly (IC-13) / Capture manuell (IC-14)
```

## 7. Qualitätssicherung

| QG | Prüfung | Art | Läuft |
|---|---|---|---|
| QG-1 | Role-Routing-Eval (IC-13); Baseline `full` **vor** jeder Kompaktierung; Akzeptanz: `compact` ≥ `full` − 1.0 Prozentpunkt je Metrik und je Modellklasse, plus absolute Schwellen aus der Baseline kalibriert | LLM | manuell / CI-nightly |
| QG-2 | Informationserhaltung `full` ↔ `compact`: Mengen gleich für Rollen, Keywords, Pipeline-Signal-Keywords, Flags (required/recommended/orchestrator_only), Name-only-Liste + Gründe; Beispielregel aus IC-04 verifiziert | deterministisch | jede CI |
| QG-3 | Anker-Registry (IC-12) je Provider × Profil × Artefaktart | deterministisch | jede CI |
| QG-4 | Budgets je Provider + Profil: `full` = Ist-Werte als Obergrenzen (Regressionsschutz), `compact` = Zielwerte (§11/AC-26); gemessen mit `--context-report` | deterministisch | jede CI |
| QG-5 | Goldens: `full` byte-stabil (`tests/fixtures/slimming-golden/orchestrator.md` nur bei bewussten Bugfixes, z. B. IC-15/11, aktualisiert); neue `compact`-Goldens | deterministisch | jede CI |
| QG-6 | `tests/test_provider_matrix_sync.py` erweitert auf Profil × 9 Provider (+ Multi-Provider-Kombinationen): wohlgeformte Artefakte, Caps, keine hängenden Pointer, Rule-Erreichbarkeit, Idempotenz | deterministisch | jede CI |
| QG-7 | Runtime-Capture (IC-14) | Runtime | manuell |
| QG-8 | Je Phase-1-Fix ein Test, rot vor dem Fix, grün danach | deterministisch | jede CI |

Test-Churn (Format-Pins):

| Test | `full` | `compact` |
|---|---|---|
| `tests/test_orchestrator_name_dispatch.py:61-111` (parst JSON/YAML) | unberührt | format-gepinnt → Zeilenparser-Variante nötig |
| `tests/test_routing_tool_definitions.py` | unberührt (außer IC-15/15) | format-gepinnt |
| `tests/test_routing_name_index.py` | unberührt | format-gepinnt |
| `tests/test_developer_tiers_gate.py:44-65` | unberührt | format-gepinnt (Flags `req`/`rec`) |
| `tests/test_template_slimming_equivalence.py:1233-1283` (Golden) | Rebaseline nur IC-15/11 | eigenes Golden |
| `tests/test_delegation_table.py` | ändert sich durch IC-15/11 | betroffen (Tabelle entfällt/Liste) |
| `test_context_compact_mode.py:246-268` | unberührt | Schwellen neu |
| `tests/test_routing_overlap.py`, `tests/test_role_addressability_coverage.py` | unberührt (Datenebene) | unberührt |
| `scripts/lib/consistency/placeholders.py:111-119` | neue Built-ins | neue Built-ins |

## 8. Akzeptanzkriterien

### Phase 0 — Messen & Absichern (keine Verhaltensänderung)
1. **AC-01** Ohne `context-profile`-Key ist die Sync-Ausgabe aller Provider-Matrix-Projekte byte-identisch zum Stand vor dem Feature (Vorher/Nachher-Diff leer).
2. **AC-02** Die Role-Routing-Baseline (`full`) liegt für ≥ 2 Modellklassen unter `tests/routing-llm-eval/roles/baseline/` vor; ein zweiter Lauf mit gleicher Config reproduziert jede Metrik innerhalb der in der Baseline-Datei dokumentierten Streuung.
3. **AC-03** Der Eval-Korpus enthält jedes Keyword und jedes Beispiel aus `role-defaults`, Paraphrasen für ≥ 20 Rollen, alle Kollisionsfälle aus Studie §2.2 und Name-only-Fälle (Test zählt die Fälle gegen `role-defaults`).
4. **AC-04** `sync.py --context-report --json` existiert; seine Byte-Werte weichen je Artefakt um ≤ 1 % von einer unabhängigen Messung (Byte-Zählung auf dem gerenderten Artefakt) ab.
5. **AC-05** Die Messung mit echtem Tokenizer für Orchestrator und AGENTS.md (Ist, beide Profile, sobald vorhanden) ist dokumentiert, inkl. Verhältnis Bytes/Token je Artefakt.
6. **AC-06** `config/context-anchors.yaml` existiert; `tests/test_context_anchors.py` ist für `full` über alle 9 Provider grün.
7. **AC-07** CI prüft Budgets je Provider mit den Ist-Werten (§2) als Obergrenzen; eine künstliche Vergrößerung eines Artefakts über die Obergrenze lässt den Test fehlschlagen.
8. **AC-08** `context.dangling-pointer` und `context.rule-unreachable` melden (als WARN) mindestens die bekannten Defekte: fehlende Skills für Codex/Mammouth/Gemini/Continue, die 8 verlorenen Gemini-`lazy`-Rules, ≥ 10 nicht existente Skills der Lazy-Tabelle.
9. **AC-09** Die Doku-Korrekturen K-a…K-c sowie `docs/providers/codex.md:118-124`, `docs/providers/gemini-cli.md` und die Kimi-Precedence-Aussage sind korrigiert.

### Phase 1 — Kanäle & Korrektheit (je Fix eigener Issue/PR)
10. **AC-10** Jeder Fix aus IC-15 hat einen eigenen Test, der vor dem Fix rot und danach grün ist (Nachweis im PR).
11. **AC-11** Über alle 9 Provider × Rules-Presets: null `context.dangling-pointer`-Befunde (Check ist ERROR).
12. **AC-12** Jede aktive Rule ist für jeden aktiven Provider über einen gelesenen Kanal erreichbar (null `context.rule-unreachable`; Check ist ERROR).
13. **AC-13** Codex: Multi-Provider-AGENTS.md (6 AGENTS.md-Provider) ist < 32,768 B, oder der Sync bricht mit `context.over-hard-cap` ab; nie stilles Schreiben über dem Cap.
14. **AC-14** Copilot: Rules liegen als `.github/instructions/<rule>.instructions.md` mit `applyTo` bzw. `description`; `.github/instructions/*.md` ohne Suffix existieren nicht mehr; der Agent heißt `orchestrator` (Frontmatter `name`); Skills unter `.github/skills`.
15. **AC-15** Codex: `.codex/config.toml` enthält `[agents] max_depth` ≥ 2; der Capture-Harness (QG-7) zeigt Multi-Agent-Tools im Orchestrator-Child.
16. **AC-16** Kimi: Orchestrator-Frontmatter enthält `subagents:` mit allen aktiven delegierbaren Rollen, Tools ausschließlich mit Kimi-Namen (`Agent`, `AgentSwarm`, `TodoList`, …), `whenToUse` aus `hint`; Frontmatter-Test grün. Runtime-Bestätigung per Capture, sofern eine Kimi-Runtime verfügbar ist; sonst im PR als UNVERIFIED vermerkt.
17. **AC-17** Mammouth: Orchestrator-Agent hat `task` in seiner Tool-/Permission-Menge, `mode` ist gesetzt, `subagent_depth` ≥ 2; Capability `subagent_dispatch` ist `true`.
18. **AC-18** Gemini CLI: `.gemini/settings.json` setzt `context.fileName` (oder `GEMINI.md` wird erzeugt) — Settings-Test grün; `.gemini/rules` wird nicht mehr geschrieben.
19. **AC-19** Kein generiertes Verzeichnis liegt außerhalb der Lese-Kanäle seines Providers, außer es ist in `intentional_unread` mit Begründung gelistet (sonst null `context.unread-channel`-WARNs).
20. **AC-20** `AGENT_DELEGATION_TABLE` ist eine gültige Markdown-Tabelle (ein Header, keine Leerzeilen); Golden-Rebaseline im selben PR mit Begründung.
21. **AC-21** ZCode-AGENTS.md enthält keinen Bootstrap-Block mehr (CLI); Parallel-Capability korrigiert; eine Multi-Provider-Datei enthält Bootstraps nur aktiver Provider.
22. **AC-22** `role-defaults.yaml` speichert Keywords einmal; der `template-auditor`-Widerspruch ist aufgelöst und Szenario 76 konsistent mit dem Render.

### Phase 2 — Profil `compact`
23. **AC-23** Mit `context-profile: full` (oder ohne Key) ist die Ausgabe byte-identisch zu den Phase-1-Goldens.
24. **AC-24** Mit `context-profile: compact` sind QG-2 (Informationserhaltung) und QG-3 (Anker) für alle 9 Provider grün.
25. **AC-25** Role-Routing-Eval: `compact` ≥ Baseline − 1.0 Prozentpunkt je Metrik und je Modellklasse; Ergebnisdateien versioniert.
26. **AC-26** Größenziele `compact` (gemessen mit `--context-report` am 62-Rollen-Matrixprojekt der Studie): Claude-Orchestrator ≤ 32 KB; AGENTS.md Einzelprovider ≤ 8 KB; AGENTS.md Multi-Provider ≤ 12 KB und < 32,768 B; Gemini-AGENTS.md ≤ 9 KB; Continue Always-on-Rules ≤ 2 KB; Copilot-Instruktionsdatei ≤ 4,000 Zeichen. Die Ziele sind Schätzungen (§11): wird ein Ziel bei erfüllten AC-24/AC-25 verfehlt, wird der Wert per Spec-Revision mit Begründung angepasst — nie stillschweigend im Test.
27. **AC-27** Provider-Matrix 9 Provider × 2 Profile (+ Multi-Provider-Kombinationen) grün (QG-6).
28. **AC-28** `sync.py --check` ist nach einem `compact`-Sync grün (idempotent); zweimaliger Sync erzeugt byte-identische Dateien.
29. **AC-29** Explizites `context_file.mode: full` bei `context-profile: compact` ergibt Entry-File-Dichte `full`; `sync.log` zeigt `source=explicit`.
30. **AC-30** `provider-overrides.<P>.context-profile` wirkt nur auf P; ein Shared-File-Konflikt erzeugt `context-profile.shared-file-downgrade` (WARN) und rendert die geteilte Datei `full`.
31. **AC-31** Routing-Zeilenformat: ein Keyword mit `;` oder `|` in `role-defaults` → `SyncError` mit Rolle und Keyword; Zeilen sind nach Agentenname sortiert; `tool{}` fehlt bei `ROUTE_INTENT_CALLABLE=false` und ist bei `true` vorhanden.
32. **AC-32** `context-profile.marker-in-rule` schlägt an, wenn eine Quelldatei unter `rules/` `CONTEXT_PROFILE_COMPACT` enthält; native Rules sind in `full` und `compact` byte-identisch, soweit IC-07 sie nicht betrifft.

### Phase 3 — Erweiterungen (je nach Umsetzung)
33. **AC-33** `ultra`/Rollenprofil: Routing, Roster und Directory enthalten genau die Rollen der Allowlist; Eval auf der Teilmenge ≥ Baseline − 1.0 Prozentpunkt für die enthaltenen Rollen.
34. **AC-34** `inherit-project-context: false` setzt Claude `omitClaudeMd: true` bzw. ZCode `injectAgentsMd: false`; Default unverändert; Capture bestätigt den Wegfall des Projektkontexts im Subagenten.
35. **AC-35** Für jede Phase-3-Option gilt AC-01 sinngemäß: ohne Opt-in byte-identische Ausgabe.

Quer:
36. **AC-36** Kein Provider-Literal im neuen Code (`test_no_provider_literal_usage_in_lib` grün); Python-3.9-kompatibel, nur Stdlib + PyYAML in `scripts/lib`.

## 9. Phasen

| Phase | Name | Inhalt | ACs | Verhaltensänderung |
|---|---|---|---|---|
| 0 | Messen & Absichern | Role-Routing-Eval + Baseline, Tokenizer-Messung, `--context-report`, Anker-Registry, Budgets als Obergrenzen, Dangling/Reachability als WARN, Doku-Korrekturen | AC-01…AC-09 | keine |
| 1 | Kanäle & Korrektheit | IC-15 Nr. 1–16, je eigener Issue/PR; Goldens wo nötig aktualisiert | AC-10…AC-22 | Bugfixes (auch in `full`) |
| 2 | Profil `compact` | IC-01…IC-12, C1–C7 | AC-23…AC-32 | nur mit Opt-in |
| 3 | Erweiterungen | IC-16: `ultra`/Rollenprofil, Vererbungs-Flags, Kimi `${agents_md}`/Plugin-`systemPrompt`, Admin-UI, Claude `paths:`, `permission.task` | AC-33…AC-35 | nur mit Opt-in |

Reihenfolge-Regel: Phase 2 beginnt erst, wenn AC-02 (Baseline) erfüllt ist; IC-04 wird nicht gemergt, bevor AC-25 nachgewiesen ist. AC-36 gilt in allen Phasen.

## 10. ADRs (Kurzform)

| ADR | Kontext | Entscheidung | Konsequenzen |
|---|---|---|---|
| ADR-1 Profil statt Einzelschalter | Verdichtung verteilt auf `context_file.mode`, `rules-preset`, Bootstrap-`compact` | eine Bündelachse `context-profile`; Einzelschalter bleiben und gewinnen | einfache Nutzung; Präzedenzlogik nötig (IC-02) |
| ADR-2 Format B mit `;` | Stichprobe: B kleinstes Format (7,975 B vs. A 8,991 B, C 8,936 B) | Zeilenformat B, `;`-Trenner, Flags nur bei Nicht-Default | JSON-Parser-Tests für `compact` anpassen; Format-Risiko → QG-1 |
| ADR-3 Alle Keywords, kuratierte Beispiele | 55 von 76 Beispielen ohne neues Signal; Tool-Use-Evidenz spricht für Beispiele | alle Keywords + erstes Beispiel + signaltragende Beispiele | deterministisch, prüfbar (QG-2) |
| ADR-4 Bugfixes vor Profil | viele Defekte wirken auch in `full` | Phase 1 vor Phase 2, eigene PRs | `full`-Ausgabe ändert sich in Phase 1 bewusst |
| ADR-5 Shared File fällt auf `full` | geteilte AGENTS.md, gemischte Profile | sichere Seite + WARN | Opt-in pro Provider bei geteilter Datei wirkungslos (Q12) |

## 11. Erwartete Wirkung (ZIELE/Schätzungen, keine Messung; Tokens ≈ Bytes/4)

| Artefakt | Ist | Ziel `compact` | Herleitung |
|---|---:|---:|---|
| Claude-Orchestrator | 90.7 KB | ≈ 32 KB (≈ −65 %) | Routing 55.2 → ≈ 8.8 (60 Regeln; ≈ 11.7 bei 88), §2a 6.2 → ≈ 0.4, §9 3.6 → ≈ 1.2, Agent-Tabelle 5.8 → ≈ 1.5 |
| Claude als Main (Orchestrator + Main-Set) | ≈ 129 KB | ≈ 63 KB | Summe |
| Claude Default-Main-Set | 38.8 KB | ≈ 31 KB (`lazy`), mit `paths:` weniger | Studie §3.1 |
| AGENTS.md Einzelprovider | 25.6 KB | ≈ 8 KB (≈ 2k tok, −70 %) | Gate-Card + Pointer + Liste |
| AGENTS.md Multi-Provider | 34.0 KB | ≈ 9–12 KB, < 32 KiB | dto. + Bootstraps nur aktiv |
| Gemini-AGENTS.md | 33.0 KB | ≈ 9 KB | |
| Continue Always-on-Rules | 18.6 KB | ≈ 2 KB | `alwaysApply:false` |
| Copilot-Instruktionsdatei | 9.2 KB | ≤ 4 KB, Rules ladbar | Review-Limit |
| Kimi/ZCode generierter Anteil | ≈ 42–43 KB | ≈ 25 KB; ZCode ohne 140k-Token-Bootstrap-Read | |
| OpenCode/Mammouth/Codex Main-Turn | 70–83 KB | ≈ 52–65 KB | Roster 16–26 KB bleibt → nächster Hebel Rollenprofile/`permission.task` |

Zusätzliche Wirkung durch Byte-Stabilität: Prompt-Cache-Treffer (Cache-Read 0.1×, Studie §5) — nicht quantifiziert.

## 12. Offene Fragen und Risiken

| # | Frage | Auflösung |
|---|---|---|
| Q1 | Routing-Qualität des Zeilenformats auf kleinen Modellen | QG-1/AC-25 |
| Q2 | Sprache der Tabelle (Keywords/Beispiele deutsch vs. englisch; Beispiele 96 % deutsch) | Eval-Variante mit englischem Korpus in Phase 0; Entscheidung datenbasiert |
| Q3 | Gemini-CLI strict-Frontmatter-Schema zur Laufzeit | Lauf/Capture vor IC-15/8 |
| Q4 | Antigravity 12,000-Zeichen-Cap und Status `define_subagent` | Runtime-Test; bis dahin UNVERIFIED, Soft-Cap nur WARN |
| Q5 / D-1 | Brauchen Kimi-Worker Rules (sehen AGENTS.md nie)? Gate-Card via `${agents_md}`? | Phase 3, Eval + Nutzerentscheidung; `compact` macht es billig |
| Q6 | Erhalten Claude-Subagenten `.claude/rules`? | Capture/Doku; beeinflusst `paths:`-Scoping |
| Q7 | Erhält ein Mammouth-Primary-Orchestrator mit unserer Datei `task`? | Capture nach IC-15/6 |
| Q8 | Erreichbarkeitspolitik Continue-Orchestrator (nur `cn --agent`) | Nutzerentscheidung: dokumentieren vs. Prompt-Weg |
| Q9 | `template-auditor`: Regel löschen oder §3-Text ändern | Nutzerentscheidung in IC-15/14 |
| Q10 | OpenCode v2 `subagent_depth` | Verifikation gegen v2-Schema |
| Q11 | Künftige Provider mit callable `route_intent` | Schema-Pfad bleibt (IC-04) |
| Q12 | Eine Gate-Card für die geteilte Datei = kleinster gemeinsamer Nenner (beratende Runtimes) | Review; ggf. `per-provider`-Topologie |
| Q13 | `lazy`-only-REFERENCE-Rules aus dem Embed löschen oder Digest behalten | Eval + Anker; Vorschlag: Digest-Satz + Pointer |
| Q14 | Byte-Stabilität für Prompt-Caching (keine Zeitstempel in dynamischer Position) | Audit der Header (`Generiert von … — <Datum>`) in Phase 0 |

| # | Risiko | Gegenmaßnahme |
|---|---|---|
| R1 | Prompt-Format-Sensitivität (arXiv 2411.10541) | QG-1, Baseline zuerst, ≥ 2 Modellklassen |
| R2 | Gate-Kompression auf beratenden Providern (Kimi) schwächt Durchsetzung | Gate-Card verbatim, Anker QG-3, Hooks wo verfügbar |
| R3 | Geteilte AGENTS.md-Gruppe: ein Profil für alle | ADR-5, Q12 |
| R4 | Test-Churn (Goldens, Format-Pins) | Tabelle §7; `full` unberührt außer IC-15/11 |
| R5 | Studie mit 62 Rollen; Projekte mit 88 Keyword-Rollen sind größer | Hochrechnung §11 (× 1.47); Budgets je Projekt via Report |
| R6 | Fremdinjektionen (RTK/graphify) in AGENTS.md außerhalb Scope können Caps sprengen | `context.over-hard-cap` misst die ganze Datei |

## 13. Nicht verifiziert

| Aussage | Status |
|---|---|
| Gemini CLI lehnt alle 62 Agenten wegen strict-Schema ab | UNVERIFIED (SOURCE-DERIVED) |
| Antigravity 12,000-Zeichen-Cap | UNVERIFIED (Drittquelle) |
| ZCode Desktop lädt Agenten automatisch; Tiefenlimit | UNVERIFIED |
| Claude-Subagenten erhalten `.claude/rules` | UNVERIFIED |
| Mammouth-Primary-Orchestrator erhält `task` | UNVERIFIED |
| Copilot kann ohne `tools:`/`agents:` nicht delegieren | UNVERIFIED (Schlussfolgerung) |
| Continue `$ARGUMENTS`-Substitution | UNVERIFIED |
| Code-Orte der Kimi-/Gemini-/Continue-Transforms und der Delegationssyntax-Config (IC-15 Nr. 4, 5, 8, 10) | UNVERIFIED (Planer verifiziert) |
| Alle Token-Zahlen | Schätzung Bytes/4 bis AC-05 |
| Zielgrößen §11 / AC-26 | Schätzung |
| Übertragbarkeit IFScale/RAG-MCP auf unsere Modelle | UNVERIFIED |

## 14. Revisionen

| Datum | Änderung |
|---|---|
| 2026-10-11 | Erstentwurf (DRAFT) auf Basis der Studie `docs/analysis/2026-10-11-context-budget-provider-study.md` |

## Trace-Anker

`spec-id: SPEC-CONTEXT-PROFILES-2026-10-11`
