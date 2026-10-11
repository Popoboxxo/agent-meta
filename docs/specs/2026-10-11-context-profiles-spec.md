---
spec-id: SPEC-CONTEXT-PROFILES-2026-10-11
title: Context Profiles (full/compact) — token-effiziente Kontextartefakte für alle 9 Provider
status: DRAFT
revision: 2
related-spec: SPEC-CONTEXT-FILE-MODES-2026-09-13
builds-on: SPEC-844-COMPRESS-ROOT-CONTEXT-2026-10-06, docs/plans/issue-540-baseline.md, docs/guides/context-block-inventory.md
source-study: docs/analysis/2026-10-11-context-budget-provider-study.md
scope-rev2: Active-Set-Filter (dynamisches Routing/Dispatch), Installations-Doctor (install-doctor), project.yaml-Optimizer (config-optimizer)
---

# Context Profiles (full/compact) — Spec

> Status: Entwurf (**DRAFT**, 2026-10-11, Revision 2). Der Approval-Marker (`Status: APPROVED`) wird
> ausschließlich vom Nutzer bzw. `concept-reviewer` gesetzt, nie vom Autor. Diese Datei definiert
> Interface-Contracts und Akzeptanzkriterien; sie enthält keine Implementierung und keinen Plan.
> Trace-Anker: `spec-id: SPEC-CONTEXT-PROFILES-2026-10-11`.
>
> Evidenz: alle Zahlen stammen aus `docs/analysis/2026-10-11-context-budget-provider-study.md`
> (im Folgenden „Studie"); Revision 2 zusätzlich aus Studie §10 (Nachtrag: Doctor-Inventar,
> Active-Set-/Dangling-Experiment, Variablen-Fan-out; Scratch `.tmp/ctx-study/dyn/`, nicht versioniert).
> Bytes; Tokens ≈ Bytes/4 (grob, siehe Studie §1). Zielwerte in §11 sind
> **Schätzungen/Ziele**, keine Messungen. Nicht verifizierte Aussagen tragen `UNVERIFIED`.
>
> Provider-agnostisch ist Pflicht: Provider-Unterschiede ausschließlich über Config-Keys und
> Capability-Flags (`config/ai-providers.yaml`, `config/provider-capabilities.yaml`), nie über
> `if provider == "Name"` (Skill `provider-agnostic`).
>
> **Revision 2 (Überblick):** drei Nutzeranforderungen ergänzt — **R1** Installations-Doctor
> (Registry `config/known-issues.yaml` + Runner `sync.py --doctor` + read-only Rolle `install-doctor`),
> **R2** Active-Set-Filter (ein berechneter Vertrag für alle dispatch-bezogenen Generatoren,
> Dangling-Reference-Invariante), **R3** project.yaml-Optimizer (Runner `sync.py --optimize-config`,
> deterministischer Applier, read-only Rolle `config-optimizer`). Neue IDs: F-19…F-33, IC-17…IC-28,
> AC-37…AC-61, QG-9…QG-13, Q15…Q27, ADR-6…ADR-11, R7…R11. Bestehende IDs unverändert.

## 0. Korrekturen früherer Aussagen

| # | Frühere Aussage | Korrektur (Studie §9) |
|---|---|---|
| K-a | Orchestrator §12 Few-shot ist 8.5 KB inline | §12 ist ein 3-Zeilen-Pointer von 188 B (Ziel `_wf-orchestrator-reference.md`, 1,355 B). Die frühere Messaussage war falsch; §12 ist kein Kompaktierungshebel. |
| K-b | Die Orchestrator-Datei (90.7 KB) kostet in jedem Turn | Sie kostet pro Orchestrator-Aufruf; in **jedem** Turn nur, wenn der Orchestrator Main-Thread-Agent ist (Claude `--agent orchestrator`, Kimi `--agent`, OpenCode/Mammouth primary). |
| K-c | „AGENTS.md ist bei Claude der Haupt-Bloat" | Falsch: CLAUDE.md ist 2.5 KB, und Claude ignoriert AGENTS.md, wenn CLAUDE.md existiert. Die Claude-Last liegt bei `.claude/rules` (17.9 KB), Harness-Roster (≈ 16.5 KB) und ggf. Orchestrator. |
| K-d (Rev. 2) | IC-03: `strip_inactive_conditional_blocks` liegt in `config.py` | Die Funktion liegt in `scripts/lib/variables.py:284`; die Whitelist der konditionalen Variablen steht dort in `:298-306`. `DEVELOPER_TIERS_ENABLED` und `VALIDATOR_ENABLED` sind bereits whitelisted, werden aber von keinem Template genutzt (F-24). |
| K-e (Rev. 2) | „Alle Rollen" (kein `roles:`-Key) = 92 Agenten | Ohne `roles:` sind `validator` und die Developer-Tiers per Gate **aus** (`roles_membership`-Prädikate sehen eine leere Liste); „alles" = 62 Agenten (Studie §10.2). |

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
- (Rev. 2) Es gibt **keinen projektseitigen Doctor**: `consistency-check.py`, `--validate` und
  `measure_context.py` laufen gegen den agent-meta-Root, nicht gegen die instanziierte Installation.
  Die bekannten Provider-Defekte (Caps, hängende Pointer, ungelesene Kanäle, Suffix-/Name-Bugs,
  strict-Schema, Dispatch-Tiefe) werden im Konsumentenprojekt von keinem Werkzeug erkannt (F-19).
- (Rev. 2) Nur Routing-Enum, `routing.rules`, `name_index`, Agent-Tabelle und Agent-Dateien folgen der
  aktiven Rollenmenge. Pipelines, Tier-Kette, `input_contracts`, statische Dispatch-Sektionen,
  Commands und Rules nicht: Im 10-Rollen-Projekt enthalten die generierten Dateien ≈ 117 hängende
  Rollenreferenzen, davon ≈ 38 `background(agent="X")` an nicht existente Agenten (F-21, F-22).
- (Rev. 2) `project.yaml`-Variablen werden voll in viele Agenten injiziert (`PROJECT_CONTEXT` ×56 ≈ 20.5 KB);
  manche Variablen sind wirkungslos (vom Builder überschrieben, gleich dem Default, unbenutzt) oder
  gehen still verloren (`CODE_QUALITY_RULES`). Es gibt kein verlustfreies, kommentar-erhaltendes
  Werkzeug, um das zu bereinigen (F-28, F-31).

### 1.2 Ziel

1. Eine Profil-Achse `context-profile: full | compact` steuert **alle** Verdichtungsmaßnahmen
   (Entry-File, Rules, Orchestrator, Bootstraps) gebündelt; Default `full`, byte-identisch zum Ist.
2. „Kein Qualitätsverlust" ist **beweisbar**: Eval-Baseline vor jeder Kompaktierung (QG-1),
   deterministische Informationserhaltung (QG-2), Anker-Registry (QG-3), Budgets in CI (QG-4).
3. Jede aktive Rule ist für jeden aktiven Provider über einen Kanal erreichbar, den der Provider
   wirklich liest; kein generierter Pointer zeigt ins Leere.
4. Harte Provider-Limits (Codex 32 KiB) werden nie überschritten; weiche Limits werden gemeldet.
5. Korrektheitsfehler je Provider (Studie §3) werden als unabhängige Bugfixes vor dem Profil behoben.
6. (Rev. 2) **Active-Set-Filter:** Ein einziger berechneter Vertrag `ActiveSet` (Default + Plattform +
   Projekt, nach Gates) wird von **allen** Generatoren konsumiert, die Rollen nennen; kein generiertes
   Artefakt weist an, an eine inaktive Rolle zu delegieren (Dangling-Reference-Invariante §4.4).
7. (Rev. 2) **Installations-Doctor:** Eine versionierte Known-Issues-Registry und ein deterministischer,
   read-only Runner (`sync.py --doctor`) prüfen die instanziierte Installation auf bekannte Probleme;
   eine read-only Rolle `install-doctor` interpretiert die Befunde und übergibt Fixes an `agent-meta-manager`.
8. (Rev. 2) **Config-Optimizer:** Ein read-only Runner (`sync.py --optimize-config`) und eine read-only
   Rolle `config-optimizer` schlagen verlustfreie, beweisgestützte Verkleinerungen der Projekt-YAML vor
   (Unified Diff); die Anwendung erfolgt ausschließlich über einen deterministischen Applier mit
   Roundtrip-Guard.

### 1.3 Nicht-Ziele

- Kein Ändern des Rollenumfangs im Profil `compact` (Rollen-Teilmengen sind Phase 3, `ultra`/Rollenprofil).
- Keine Änderung der Semantik von `context_file.mode` und `context_file.topology` (SPEC-CONTEXT-FILE-MODES-2026-09-13).
- Kein neuer Template-Dialekt; keine Laufzeit-Komponente beim Provider (alles Sync-Zeit).
  (Rev. 2: Der Active-Set-Filter nutzt ausschließlich den bestehenden `{{#if VAR}}`-Mechanismus mit neuen
  berechneten Variablen, IC-17.)
- Keine Umformulierung von INSTRUKTION-Inhalten (Klassifikation aus `docs/guides/context-block-inventory.md` gilt).
- Kein callable `route_intent`-Tool (bleibt `ROUTE_INTENT_CALLABLE=false`; Schema bleibt für künftige Provider erhalten, Q11).
- (Rev. 2) Der Doctor repariert nichts und führt keinen Sync aus; er schreibt nichts außerhalb von `.tmp/`.
- (Rev. 2) Der Doctor-Runner enthält kein LLM; LLM-Interpretation liegt ausschließlich in der Rolle `install-doctor`.
- (Rev. 2) Der Optimizer ändert keine Framework-Templates und keine `config/*.yaml` des Frameworks;
  er bearbeitet nur Projekt-Dateien (`.meta-config/project.yaml`, Extension-/Doku-Ziele bei Relokation).
- (Rev. 2) Keine semantische Zusammenführung von Variablen ohne ausdrückliche Freigabe je Kandidat.
- (Rev. 2) Keine Boilerplate-De-Dup in Phase 0–2 (abhängig von Q6, Phase 3, IC-27 nicht betroffen).

## 2. Ist-Zustand (gemessen)

Messbasis: Scratch-Projekte `.tmp/ctx-study`, 62 aktive Rollen (Studie §1). Rev.-2-Zeilen: Scratch
`.tmp/ctx-study/dyn` (Projekte `p10`, `p20`, `pall`, `pha`, `pproj`, `s_repo`, `s_all`; nur Provider Claude; Studie §10).

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
| (Rev. 2) Orchestrator 10 / 20 / 62 Rollen | Claude | 41,059 / 49,155 / 90,694 B | Studie §10.2 |
| (Rev. 2) §3 Routing 10 / 20 / 62 Rollen | Claude | 12,020 / 19,277 / 56,756 B (≈ 4.3 KB fix + ≈ 860 B je routbarer Rolle) | Studie §10.2 |
| (Rev. 2) §2a / `routing.pipelines` (konstant, rollenunabhängig) | Claude | 6,179 / 1,326 B | Studie §10.2 |
| (Rev. 2) `pipeline-details/*.md` | Claude | ≈ 8.0 KB (dupliziert §2a) | Studie §10.4 |
| (Rev. 2) Hängende Rollenreferenzen p10 / p20 / pall | Claude | 117 / 82 / 80 (Untergrenze, heuristischer Scanner) | Studie §10.2 |
| (Rev. 2) Boilerplate-Blöcke in Agenten p10 / pall | Claude | 6.6 KB (5.9 %) / 50.3 KB (8.7 %) | Studie §10.4 |
| (Rev. 2) Injizierte project.yaml-Variablen (Repo-Werte, 58 Agenten) | Claude | ≈ 36.1 KB, davon `PROJECT_CONTEXT` 20,496 B (×56) | Studie §10.3 |

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
| F-19 | Kein projektseitiger Doctor: `consistency-check.py` (`--root` = agent-meta), `--validate` (`_run_consistency_checks(agent_meta_root)`, `cli_commands.py:1029`) und `measure_context.py` (`REPO_ROOT`, `:22,226`) prüfen nicht die Konsumenten-Installation; Issue-Klassen Caps, hängende Pointer, ungelesene Kanäle, Suffix/Pfad, Dispatch-Fähigkeit, strict-Schema werden heute höchstens fragmentarisch erkannt; Verifikationsstatus von Capabilities steht nur in YAML-Kommentaren (`provider-capabilities.yaml:253-262`) | Studie §10.1 | hoch | 0 |
| F-20 | Rollen-Onboarding unvollständig: Commit 507bbb5 (`template-auditor`) ohne `instantiate-project.md`/README-Rollentabelle; `output_contract: audit-findings-v1` ohne Konsument; Standalone-Export erst nachgezogen (1ff89be); keine dokumentierte Neue-Rolle-Checkliste | Studie §10.1; `git show 507bbb5` | mittel | 0 |
| F-21 | Active-Set nur teilweise angewendet: gefiltert sind Enum, `routing.rules`, `name_index`, Agent-Tabelle, `AGENT_HINTS`, Agent-Dateien; **nicht** gefiltert: §2/§2a/`pipeline-details`/`routing.pipelines`/`PIPELINE_MATCH_TABLE` (`pipelines.py:729-738, 851-883, 905-1103, 1123-1197`; `delegation_table.py:280-292, 355-363`), plan-driven `allowed_agents` (Kommentar `pipelines.py:497-500` vs. Render `:1093-1094`), `routing.rules[].input_contracts` (`delegation_table.py:251-254`), §4 Tier-Kette/Task-Size-Tabelle (`orchestrator.md:111-144`), `ANTI_RECURSION_BLOCK` (`config.py:1609-1612`), `DIRECT_DISPATCH_SECTION` (`config.py:1517-1523`), Persona-Zeile und §11-Fallback `meta-feedback` (`orchestrator.md:22,26,238`), SE-Prosa bei SE aus (`orchestrator.md:255`), Slash-Commands (`commands.py:20,100-175`), Rules (`security-paved-roads`, `threat-model`, `a2a-delegation-gates`), „Delegation (reference only)"-Prosa in 34 Templates | Studie §10.2 | hoch | 1 |
| F-22 | Hängende Rollenreferenzen: p10 117 (Pipeline-Stage 38, Tier-Kette 25, Prosa 40, Tabellen 12, Routing-Prosa 2), davon ≈ 38 `background(agent="X")`; am häufigsten `senior-developer` 17, `validator` 14; zusätzlich 26 von 34 `input_contracts` mit inaktivem Producer, 6 von 7 Pipelines nicht ausführbar | Studie §10.2 (heuristischer Scanner, Untergrenze) | kritisch | 0 (Check), 1 (Fix) |
| F-23 | Pipeline-Validierung gegen falsche Menge: `available_roles = set(config["roles"])` bzw. alle 92 Rollen (`config.py:1852-1857`) statt gegateter Aktivmenge → gate-gedroppte Rollen still (p20: `senior-developer`; pall: 0 Pipeline-Warnungen trotz `validator`-/Tier-Referenzen); Agent-Renderer leitet `effective` separat ab (`agent_sync.py:666-668`, ohne se-focus-Filter/Validierung); False Positive `quick-fix`/`root-cause` trotz dod_flag aus | Studie §10.2; `config.py:1843-1872` (verifiziert) | hoch | 1 |
| F-24 | Tote Gate-Variablen: `DEVELOPER_TIERS_ENABLED`, `VALIDATOR_ENABLED`, `EFFORT_ESTIMATOR_ENABLED` berechnet (`config.py:1679,1685,1688`) und in `variables.py:298` whitelisted, aber von keinem Template genutzt; §4 (≈ 3.7 KB, 25 Tier-Referenzen) statisch; Tier-Kette auch in `developer.md:129`, `ESCALATE_CARD_BLOCK`, Planner | Studie §10.2; `variables.py:298` (verifiziert) | mittel | 1 |
| F-25 | Projekt-spezifische Rollen nicht unterstützt: Sync liest nie die Konsumenten-`.claude/3-project/<role>.md` (`collect_sources` nur `<agent_meta_root>/agents/3-project`, `frontmatter.py:662-670`); `PROJECT_SPECIFIC_AGENTS` hart `""` (`config.py:1712-1714`); Rolle fehlt in Enum/Routing/Tabelle, `audit-config` meldet ERROR; Doku (`commands/1-generic/add-project-role.md`, agent-meta-manager §8) verspricht anderes | Studie §10.2 (Projekt `pproj`) | hoch | 1 |
| F-26 | Reflection-Overrides-Leak: `load_project_overrides(str(agent_meta_root / ".meta-config" / "project.yaml"))` (`config.py:1817-1821`) liest agent-metas eigene getrackte Config → Konsument ohne `reflection-pairs` erhält `MAX_ITERATIONS=5` | Studie §10.2; `config.py:1817-1821`, `reflection.py:43-55` (verifiziert) | hoch | 1 |
| F-27 | Unaufgelöste `{{VAR}}` in generierten Dateien (pall: 17× `{{EXTRA_DONTS}}`, 6× `{{AGENT_META_REPO}}`, 5× `{{TEST_COMMANDS}}` …); `--create-ext` schreibt bei fehlenden Werten literal `{{PLATFORM}}` (`templates/managed-block.md`); nur `sync.log`-WARN (`variables.py:458`), kein Check auf dem Output | Studie §10.2, §10.3 | mittel | 0 (Check), 1 (Fix) |
| F-28 | Variablen-Fan-out und tote Inhalte: `PROJECT_CONTEXT` ×56 (20,496 B; 82 Template-Refs), `PROJECT_GOAL` ×32, `EXTRA_DONTS` ×17, `ARCHITECTURE` ×13, `CODE_CONVENTIONS` ×7, `DEV_COMMANDS` ×10; `CODE_QUALITY_RULES` von keinem Template genutzt (Inhalt geht still verloren); vom Builder überschriebene Variablen (`ORCHESTRATOR_STRICT`, `UNKNOWN_FALLBACK_*` via `config.py:1493,1583-1586`; `SE_BASE_DIR` via `:1660`); Werte gleich Default (`SE_*`); Duplikate (`BUILD_COMMAND`/`BUILD_COMMANDS`, `TEST_COMMAND`/`TEST_COMMANDS`, `LANGUAGE`/`PROJECT_LANGUAGES`, `ARCHITECTURE`/`PROJECT_STRUCTURE`) | Studie §10.3 | mittel | 2 |
| F-29 | Boilerplate-Blöcke pro Agent: `OUTPUT_GUARD_BLOCK` 399 B ×31, `BACKGROUND_PROCESS_GUARD` 368 B ×32 (in Quell-Templates inline; Variable ungenutzt), `PROMPT_INJECTION_DEFENSE_BLOCK` 443 B ×18, `PARSE_INPUT_BLOCK` 129 B ×30, `A2A_HANDOFF_BLOCK` 348 B ×11 → ≈ 50.3 KB bei 62 Agenten | Studie §10.4 | mittel | 3 |
| F-30 | Interne Orchestrator-Duplikate: Rolle in Enum, Rules, `name_index` und Agent-Tabelle; §2a (6.2 KB) dupliziert `pipeline-details/*.md` (8.0 KB) | Studie §10.2, §10.4 | mittel | 2 (C2) |
| F-31 | Kein verlustfreier project.yaml-Rewriter: `--fill-defaults` lädt per PyYAML und dumpt neu (`config.py:1072-1101`) → bestehende Nutzerkommentare gehen verloren; `yaml_roundtrip.analyze_roundtrip` existiert, wird nur vom Admin-Server genutzt | Studie §10.3; `yaml_roundtrip.py:164-181` (verifiziert) | mittel | 2 |
| F-32 | Read-only-Durchsetzung neuer Rollen provider-abhängig: Bash erlaubt überall Schreiben; Codex alle Agenten `sandbox_mode: workspace-write` (`ai-providers.yaml:668`); Copilot/Continue ohne Tool-Durchsetzung; OpenCode `edit: deny` | Studie §10.1 (Config gelesen, Runtime UNVERIFIED) | mittel | 0 (Doku/Known-Issue), 1 (Codex-Fix) |
| F-33 | Schema-Validierung der project.yaml nur, wenn `jsonschema` installiert ist, und nur als Warnung (`config.py:381-417`); `requirements.txt` und CI installieren nur PyYAML | Studie §10.1 | niedrig | 0 (Known-Issue) |

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

Der Active-Set-Filter (§4.4) ist **keine** Profil-Option: er gilt in `full` und `compact` gleichermaßen
(Korrektheit, ADR-4/ADR-7).

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

### 4.4 Active-Set-Filter und Dangling-Reference-Invariante (Rev. 2, R2)

**Prinzip:** Es gibt genau **einen** berechneten Active-Set-Vertrag pro Sync (`ActiveSet`, IC-17). Er
umfasst Framework-Default-Rollen, Plattform-Rollen und projekt-spezifische Rollen (IC-20), nach
Allowlist (`roles:`), Aktivierungs-Gates und Template-Verfügbarkeit (Layer 2). Jeder Generator, der eine
Rolle nennt oder an sie delegiert, konsumiert ausschließlich dieses Objekt; direkter Zugriff auf
`config["roles"]` oder `role-defaults.yaml::roles` zur Bestimmung der „verfügbaren" Rollen ist in
Generatoren verboten (Guard-Test QG-13).

**Filterklassen** (Details IC-18):

| Klasse | Regel |
|---|---|
| Rollenlisten (Enum, Tabellen, `allowed_agents`, Anti-Recursion, Direct-Dispatch) | Schnittmenge mit `ActiveSet.roles` |
| Pipelines | Pipeline wird gerendert, wenn alle **Pflicht**-Stage-Rollen (inkl. Reflection-Loop-Generator/-Critic) aktiv sind; inaktive `optional`-Stages und Stages mit inaktivem `dod_flag` entfallen; sonst wird die Pipeline vollständig entfernt (`PIPELINE_<NAME>_ENABLED=false`, kein §2-/§2a-Eintrag, keine `pipeline-details`-Datei, kein `routing.pipelines`-Eintrag) und als `active-set.pipeline-dropped` (INFO) protokolliert (ADR-10, Q18) |
| Handoff-Contracts | `input_contracts` bleiben nur, wenn eine aktive Rolle (inkl. `orchestrator`) den Contract als `output_contract` produziert |
| Statische Prosa mit Dispatch-Anweisung | Konditional über berechnete Flags `ROLE_<UPPER_SNAKE>_ACTIVE` bzw. bestehende Gruppen-Flags (`DEVELOPER_TIERS_ENABLED`, `VALIDATOR_ENABLED`, `SE_ENABLED`) |
| Commands | Command mit `requires_roles` wird nur generiert, wenn alle genannten Rollen aktiv sind |
| Rein informative Erwähnung (kein Dispatch) | bleibt; wird gezählt (`active-set.dangling-mention`, INFO) |

**Dangling-Reference-Invariante:** Kein generiertes Artefakt enthält eine **Dispatch-Anweisung** an eine
Rolle `r ∈ KnownRoles \ ActiveSet.roles`. Dispatch-Anweisung = Treffer eines der aus
`config/delegation-syntax.yaml` abgeleiteten Muster (z. B. `background(agent="r")`, `agent="r"`,
`subagent_type="r"`, PAL-Syntax des Providers) sowie Tabellenzeilen der Dispatch-Tabellen (IC-19).
Verletzung = `active-set.dangling-dispatch` (Phase 0 WARN, ab Phase 1 ERROR).
`KnownRoles` = `role-defaults.yaml::roles` ∪ projekt-spezifische Rollen.

**Zusatzwarnungen:** gate-gedroppte Allowlist-Einträge (`active-set.gate-dropped`, z. B. `senior-developer`
ohne `junior-developer`) und unaufgelöste `{{VAR}}` im Output (`active-set.unresolved-placeholder`).

### 4.5 Installations-Doctor (Rev. 2, R1)

Drei Schichten, klar getrennt (ADR-6):

| Schicht | Artefakt | Art | Schreibt |
|---|---|---|---|
| Wissen | `config/known-issues.yaml` (IC-21) | versionierte Registry bekannter Probleme mit Evidenz und Verifikationsstatus | — |
| Prüfung | `scripts/lib/doctor.py` + `sync.py --doctor [--json] [--strict]` (IC-22) | deterministisch, read-only, gegen die **Projekt**-Installation | nichts (ggf. `.tmp/`) |
| Interpretation | Rolle `install-doctor` (IC-23) | LLM, read-only; dedupliziert, priorisiert, formuliert Fixes | nichts |

Fixes führt ausschließlich `agent-meta-manager` (Projekt-Config) bzw. ein Framework-Issue/PR aus
(`fix-owner`). Bestehende Checks (IC-10 `context.*`, IC-19 `active-set.*`, `hooks.*`, `artifact-contract`,
`handoff.*`) werden über `detector.kind: finding-ref` **wiederverwendet**, nie dupliziert.
Severity-Regel: `verified-state: UNVERIFIED` ⇒ effektive Severity ≤ WARNING (ADR-11).

### 4.6 Config-Optimizer (Rev. 2, R3)

| Schicht | Artefakt | Art |
|---|---|---|
| Analyse + Beweis | `scripts/lib/config_optimizer.py` + `sync.py --optimize-config [--json]` (IC-24, IC-25) | deterministisch, read-only; Kandidaten, Fan-out-Report, Unified Diff, Beweisbericht unter `.tmp/config-optimizer/` |
| Anwendung | `sync.py --apply-config-patch <proposal.json> [--accept <id>…]` (IC-24) | deterministischer Applier, zeilenbasiert, Roundtrip-Guard, Re-Beweis vor dem Schreiben |
| Interpretation | Rolle `config-optimizer` (IC-26) | LLM, read-only; präsentiert Vorschläge, formuliert semantische Kandidaten (nicht-deterministisch, nur mit Freigabe) |

Beweisstufen L0–L3 (IC-25): L0 Byte-Gleichheit aller Artefakte; L1 Placeholder-/Token-Multiset/Anker;
L2 Relokation erreichbar; L3 semantisch (Freigabe je Kandidat). Wichtig: **L0-Kandidaten verkleinern nur
die YAML, nicht die Injektion** (per Definition byte-gleich); Injektions-Einsparung entsteht nur durch
L2/L3 (Relokation in `-ext.md`/Doku hinter Pointer, Zusammenführung). Das wird im Report getrennt ausgewiesen.

Verboten: `--fill-defaults` (kommentar-verlustbehaftet, F-31), `yaml.dump` der gesamten Datei, ruamel
(nur Stdlib + PyYAML).

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
- `CONTEXT_PROFILE_COMPACT` wird in die Whitelist von `strip_inactive_conditional_blocks`
  (`scripts/lib/variables.py:284`, Whitelist `:298-306`; Korrektur K-d) aufgenommen. Weil dieselbe Funktion im nativen Rules-Pfad (`rules.py`) läuft, gilt:
  Quell-Rules unter `rules/` dürfen `{{#if CONTEXT_PROFILE_COMPACT}}` **nicht** enthalten.
  Neuer Consistency-Check `context-profile.marker-in-rule` (ERROR). Rule-Kompaktierung läuft
  ausschließlich über die bestehende `compact_embedded_rule()`-Transform (`context.py:1562-1585`) und IC-07.
- `COMPACT_MODE` bleibt unverändert außerhalb der Whitelist (Verhalten #540 unverändert).
- (Rev. 2) Zusätzlich whitelisted: alle Variablen mit Präfix `ROLE_` und Suffix `_ACTIVE` (IC-17).
  Diese **dürfen** in Quell-Rules verwendet werden (Rollen-Konditionale sollen auch im Rules-Pfad wirken).

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
  (Rev. 2: `pipelines` = nach IC-18 gefilterte Pipelines.)
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
- (Rev. 2) Die Active-Set-Konditionale (IC-18 Nr. 4–8) sind von den Profil-Konditionalen unabhängig und
  gelten in beiden Zweigen.

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
| (Rev. 2) `rules_required_suffix` | string\|null | Copilot `.instructions.md` (**UNVERIFIED**) |
| (Rev. 2) `subagent_allowlist_required` | bool | Kimi true (SOURCE-DERIVED) |
| (Rev. 2) `read_only_enforcement` | `tools`\|`permission-map`\|`sandbox`\|`none` | OpenCode `permission-map`; Copilot/Continue `none`; Codex `none` bis IC-15 Nr. 21 (Config gelesen, Runtime UNVERIFIED) |

Datenkorrekturen (F-17): ZCode Parallelität, Kimi `agents_md_precedence`, Mammouth `subagent_dispatch`,
Gemini `.gemini/agents` nur Antigravity, Copilot-Pfade, Claude `orchestrator_hint` `--agent`.
Code liest ausschließlich diese Keys; Guard `test_no_provider_literal_usage_in_lib` bleibt grün.
(Rev. 2) Die Keys (nur Daten, keine Render-Änderung) werden in **Phase 0** eingeführt, weil der Doctor
(IC-21/IC-22) sie als Prädikate und Limits braucht; ihre Nutzung im Render bleibt Phase 1/2.

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

(Rev. 2) Signaturvorgabe, damit Doctor und Sync dieselben Funktionen nutzen (ADR-6): jeder Check ist eine
reine Funktion `check_<name>(project_root: Path, active_providers: Sequence[str], capabilities: Mapping[str, Mapping], active_set: ActiveSet) -> list[Finding]`;
kein Zugriff auf `agent_meta_root` als Prüfgegenstand. `consistency-check.py` (agent-meta-Root) ruft sie
nur für Fixture-Projekte auf.

### IC-11 CLI `--context-report`
- `sync.py --context-report [--json] [--profile full|compact|both]`: je aktivem Provider Entry-File, Rules
  (je Kanal), Orchestrator, geschätztes Harness-Roster, Always-loaded-Set, Caps, Δ `full` vs `compact`.
  Read-only; rendert in ein Temp-Verzeichnis unter `.tmp/`, schreibt nichts ins Projekt. Exit 0; Exit 1 nur bei
  `context.over-hard-cap`.
- JSON-Schema: `{provider: {artifact: {bytes, lines, tokens_est, tokens_real?, cap, cap_kind}}}`.
- `scripts/measure_context.py --project <path>` nutzt dieselbe Messfunktion (keine Doppelimplementierung).
- `tokens_real` optional, sobald in Phase 0 ein Tokenizer festgelegt ist. Stdlib-Pflicht: externer Tokenizer
  nur in `tests/`/manuell, nicht in `scripts/lib`.
- (Rev. 2) Die Messfunktion `measure_artifacts(project_root, active_providers, capabilities) -> dict` ist
  öffentlich und wird vom Doctor-Detektor `file-size` (IC-22) wiederverwendet.

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
(Rev. 2) Die Anker sind zugleich Prüfgröße der Optimizer-Beweisstufe L1 (IC-25).

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
- (Rev. 2) Zusätzliche Eval-Variante „Teilmenge": System-Prompt aus einem 10-Rollen-Projekt (p10-artig)
  vor/nach Active-Set-Filter; Metrik zusätzlich „Dispatch an inaktive Rolle" (Ziel nach Phase 1: 0).

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
| 17 (Rev. 2) | Reflection-Overrides aus der **Konsumenten**-Config: `apply_project_overrides(_refl_pairs, (config.get("reflection-pairs") or {}).get("overrides", {}))` statt `load_project_overrides(agent_meta_root/...)` | `config.py:1817-1821`; `reflection.py:43-55` | F-26 |
| 18 (Rev. 2) | Pipeline-Validierung gegen `ActiveSet.roles` statt `config["roles"]`/alle Rollen; ein einziges `effective` (Agent-Renderer `agent_sync.py:666-668` konsumiert das Ergebnis aus `config.py`, keine Neuableitung); kein Warn-False-Positive für Stages mit inaktivem `dod_flag` | `config.py:1852-1857`; `agent_sync.py:666-668`; `pipelines.py:434-435` | F-23 |
| 19 (Rev. 2) | `--create-ext`/Managed-Block: unaufgelöste Variablen nicht literal schreiben (Zeile weglassen bzw. „nicht gesetzt") | `templates/managed-block.md`; `extensions.py:49-146` | F-27 |
| 20 (Rev. 2) | `CODE_QUALITY_RULES`: entweder in ein Template (Code-Konventionen der Kontextdatei) einbinden **oder** im Schema als deprecated markieren + Doctor-Regel; Entscheidung Q23 | `config/project-config.schema.json`; Kontext-Template (Ort UNVERIFIED) | F-28 |
| 21 (Rev. 2) | Codex: read-only Rollen (`tools` ohne `Write`/`Edit`) erhalten `sandbox_mode: read-only` über Capability `read_only_enforcement: sandbox` statt pauschal `workspace-write` | `ai-providers.yaml:668`; Codex-Agent-Transform (Ort UNVERIFIED) | F-32 |

### IC-16 Phase-3-Erweiterungspunkte (Default aus, eval-gated)
- Profil `ultra` / Rollenprofil: kuratierte Rollenteilmengen über die bestehende `roles:`-Allowlist; verkleinert
  Routing, Roster (≈ 16.5 KB für 62 Rollen; 63 Rollen kosten 16–19 KB pro Main-Turn in den `task`/`spawn_agent`-
  Beschreibungen von Codex/OpenCode/Mammouth) und Directory proportional; zusätzlich OpenCode/Mammouth
  `permission.task`-Deny/hidden.
- Rollen-Key `inherit-project-context: bool` (Default true) → Claude `omitClaudeMd`, ZCode `injectAgentsMd`.
- Kimi: Gate-Card in Worker-Bodies via `${agents_md}` (D-1) oder Plugin-`systemPrompt`.
- Admin-UI: Profil-Umschalter + Report-Ansicht. Claude `paths:`-Scoping. `permission.task`-Trimming.
- (Rev. 2) Zentrale Boilerplate-De-Dup (IC-28-unabhängig, siehe IC-27 Abschnitt „Phase 3").

### IC-17 Active-Set-Vertrag `scripts/lib/active_set.py` (neu, Rev. 2)
```python
@dataclass(frozen=True)
class GateDrop:
    role: str
    group: str            # activation_groups-Key, z. B. "developer_tiers"
    reason: str           # z. B. "requires all of [junior-developer, senior-developer]"

@dataclass(frozen=True)
class ActiveSet:
    roles: frozenset[str]                      # Layer 2 (Allowlist ∧ Gates ∧ Template) ∪ projekt-spezifische Rollen
    routable: frozenset[str]                   # roles ohne addressability "excluded" und ohne Main-Chat-Skip
    known_roles: frozenset[str]                # role-defaults ∪ projekt-spezifische Rollen
    sources: Mapping[str, Literal["framework", "platform", "project"]]
    gates: Mapping[str, bool]                  # Aktivierungsgruppe → aktiv
    gate_dropped: tuple[GateDrop, ...]         # in roles: gelistet, durch Gate entfernt (sortiert)
    missing_template: tuple[str, ...]          # aktiv laut Layer 1, ohne Template (sortiert)
    producers: Mapping[str, frozenset[str]]    # contract-id → aktive Rollen mit diesem output_contract

    def has(self, role: str) -> bool
    def all_active(self, roles: Iterable[str]) -> bool

def compute_active_set(
    config: dict, agent_meta_root: Path, project_root: Path, *, warn_sink: list[str] | None = None
) -> ActiveSet

def active_set_variables(active: ActiveSet) -> dict[str, str]
```
- Implementierung delegiert an `resolve_activation_gates`, `is_role_enabled`, `resolve_active_roles(require_template=True)`
  (`roles.py:129-288`) — keine zweite Gate-Logik. Erweiterung: Erkennung `gate_dropped` (Allowlist-Eintrag,
  den `is_role_enabled` verwirft) und projekt-spezifische Rollen (IC-20).
- Wird **einmal** pro Sync berechnet und an alle Konsumenten (IC-18) übergeben; Ablage im Sync-Kontext.
- `active_set_variables` liefert: `ACTIVE_ROLES` (kommasepariert, sortiert), für **jede** Rolle aus `known_roles`
  `ROLE_<UPPER_SNAKE>_ACTIVE` = `"true"|"false"` (Bindestrich → Unterstrich, z. B. `ROLE_SENIOR_DEVELOPER_ACTIVE`),
  `PROJECT_SPECIFIC_AGENTS` (ersetzt den hart kodierten Leerstring, `config.py:1712-1714`).
- Registrierung: `ROLE_*_ACTIVE` als Muster-Built-in in `scripts/lib/consistency/placeholders.py`;
  Whitelist in `variables.py` (IC-03).
- Fehlerpfade: unbekannter Allowlist-Eintrag (weder `role-defaults` noch Projektrolle) → `active-set.unknown-role`
  (WARN); gate-gedroppter Eintrag → `active-set.gate-dropped` (WARN, mit Gruppe und Grund); beides in `sync.log`.
- Byte-Stabilität: alle Mengen sortiert serialisiert.

### IC-18 Active-Set-Konsumenten (Filter-Matrix, Rev. 2)

| Nr. | Konsument | Ort (aus Studie §10.2; sonst UNVERIFIED) | Filterregel | Phase |
|---|---|---|---|---|
| 1 | Enum, `routing.rules`, `name_index`, Agent-Tabelle, `AGENT_HINTS`, Agent-Dateien | `delegation_table.py:83-299`; `agents.py:104-321`; `agent_sync.py:530-598` | auf `ActiveSet` umstellen (Ergebnis unverändert) | 1 |
| 2 | Pipelines §2 (`PIPELINE_MATCH_TABLE`), §2a, `pipeline-details/*.md`, `routing.pipelines`, Pipeline-Zeilen `INTENT_ROUTING_TABLE` | `pipelines.py:729-738, 851-883, 905-1103, 1123-1197`; `delegation_table.py:280-292, 355-363`; `agent_sync.py:661-675` | neue Funktion `filter_pipelines_by_active_set(effective: dict, active: ActiveSet, variables: Mapping[str, str]) -> tuple[dict, list[PipelineDrop]]` (`pipelines.py`); Regel §4.4; nicht mehr gerenderte `pipeline-details`-Dateien werden über die bestehende Managed-File-Cleanup entfernt | 1 |
| 3 | Plan-driven `allowed_agents` | `pipelines.py:497-500` vs. `:1093-1094` | Schnittmenge mit `ActiveSet.roles` (wie Kommentar versprochen) | 1 |
| 4 | `routing.rules[].input_contracts` | `delegation_table.py:251-254` | nur Contracts mit `ActiveSet.producers[c] ≠ ∅` (`task-spec-v1` wird von `orchestrator` produziert, bleibt daher) | 1 |
| 5 | §4 Tier-Kette, Task-Size-Tabelle, ESCALATE-Intake | `orchestrator.md:111-144`; `developer.md:129`; `ESCALATE_CARD_BLOCK`; Planner | `{{#if DEVELOPER_TIERS_ENABLED}}…{{else}}<developer-only-Variante>{{/if}}`; Concept-Rollen über `ROLE_CONCEPT_*_ACTIVE`; `{{else}}`-Zweig wird neu geschrieben, der `if`-Zweig ist der unveränderte heutige Text | 1 |
| 6 | `ANTI_RECURSION_BLOCK` | `config.py:1609-1612` | Rollenliste aus Daten (`role-defaults`) ∩ `ActiveSet` statt String-Literal | 1 |
| 7 | `DIRECT_DISPATCH_SECTION` | `config.py:1517-1523`; `templates/direct-dispatch-section.md` | Zeilen je Rolle per `ROLE_*_ACTIVE` | 1 |
| 8 | Persona-Zeile, §11-Fallback `meta-feedback`, SE-Prosa | `orchestrator.md:22,26,238,255` | `ROLE_*_ACTIVE` bzw. `SE_ENABLED`; Fallback bei inaktivem `meta-feedback`: Rückfrage an den Nutzer (ASK) | 1 |
| 9 | Slash-Commands | `commands.py:20,100-175` | neuer optionaler Frontmatter-Key `requires_roles: [<role>…]` in `commands/**`; Command nur generieren, wenn `ActiveSet.all_active(requires_roles)`; consistency-check `commands.*` akzeptiert den Key (Q26) | 1 |
| 10 | Rules mit Rollen-Ownership (`security-paved-roads`, `threat-model`, `a2a-delegation-gates`) | `rules/1-generic/*.md` | Owner-Zeilen per `ROLE_*_ACTIVE` (im Rules-Pfad erlaubt, IC-03) | 1 |
| 11 | „Delegation (reference only)"-Prosa (34 Templates) | `agents/1-generic/*.md` | Phase 1: nur Zeilen mit Dispatch-Anweisung konditional; reine Erwähnungen bleiben (INFO-Zählung); Phase 3: datengetrieben (Q19) | 1 / 3 |
| 12 | Pipeline-Validierung | `config.py:1852-1857` | gegen `ActiveSet.roles` (IC-15 Nr. 18) | 1 |
| 13 | Config-Optimizer „unbenutzt"-Analyse | IC-24 | Fan-out nur über Artefakte aktiver Rollen × aktiver Provider | 2 |

`PipelineDrop` = `@dataclass(frozen=True) class PipelineDrop: pipeline: str; missing_roles: tuple[str, ...]; dropped_stages: tuple[str, ...]`.
Version-Bumps aller berührten Templates gemäß `agent-meta-conventions.md`.

### IC-19 Active-Set-Checks `scripts/lib/consistency/active_set_refs.py` (neu, Rev. 2)

| Check-ID | Level | Bedingung |
|---|---|---|
| `active-set.dangling-dispatch` | Phase 0 WARN, ab Phase 1 ERROR | Dispatch-Muster (abgeleitet aus `config/delegation-syntax.yaml` je aktivem Provider + Dispatch-Tabellenzeilen) nennt `r ∈ known_roles \ roles` |
| `active-set.dangling-mention` | INFO | Rollenname aus `known_roles \ roles` als reine Erwähnung (Backticks/Prosa); Zählung je Datei |
| `active-set.gate-dropped` | WARN | `ActiveSet.gate_dropped` nicht leer |
| `active-set.unknown-role` | WARN | Allowlist-Eintrag ∉ `known_roles` |
| `active-set.pipeline-dropped` | INFO | IC-18 Nr. 2 |
| `active-set.unresolved-placeholder` | WARN | Regex `\{\{[A-Z][A-Z0-9_]*\}\}` im generierten Output; Allowlist `config/active-set-references.yaml: placeholder_allow` (z. B. dokumentierte `{{%VAR%}}`-Escapes) |
| `active-set.raw-roles-access` | ERROR (nur Quell-Repo) | Generator-Modul liest `config["roles"]`/`config.get("roles")` außerhalb `active_set.py`/`roles.py` (statischer Guard, QG-13) |

- Signatur wie IC-10: `check_<name>(project_root, active_providers, capabilities, active_set) -> list[Finding]`.
- Läuft am Sync-Ende (`sync.log`), im Doctor (via `finding-ref`) und in Tests auf Fixture-Projekten.
- Neue Datei `config/active-set-references.yaml`: `placeholder_allow: [<literal>…]`, `mention_allow: [<path-glob>…]`
  (Dateien, in denen Erwähnungen inaktiver Rollen gewollt sind, z. B. Doku-Beispiele).
- Fehlerpfad: Muster-Ableitung aus `delegation-syntax.yaml` schlägt für einen aktiven Provider fehl →
  `active-set.dispatch-pattern-missing` (WARN), Check für diesen Provider übersprungen (nie still).

### IC-20 Projekt-spezifische Rollen (Rev. 2)
Entscheidung Q16 (Empfehlung: implementieren). Vertrag bei Implementierung:
- Quelle: Projekt-Dateien `<project_root>/.meta-config/agents/<role>.md` (provider-neutral; Empfehlung) mit
  Frontmatter wie Framework-Templates (`name`, `version`, `description`, `tools`); Rollen-Metadaten
  (`routing`, `handoff`, `model`, `short_desc`) in `project.yaml: project-roles: {<role>: {…}}` mit
  `role-defaults`-Struktur. Legacy: `<extension_dir>/<role>.md` (ohne `-ext`) wird gelesen und mit
  `active-set.project-role-legacy-path` (WARN) gemeldet.
- `collect_sources` (`frontmatter.py:638-670`) erhält zusätzlich `project_root`; Projektrolle mit gleichem Namen
  wie eine Framework-Rolle = Override (bestehende Semantik von `agents/3-project`), neue Namen = Ergänzung.
- Schema: `roles:`-Enum akzeptiert zusätzlich Keys aus `project-roles` (Validierung im Sync, da die Enum generiert ist).
- Projektrolle ohne `project-roles`-Eintrag → `active-set.project-role-metadata-missing` (ERROR, Sync bricht ab).
- `config_audit` meldet Projektrollen nicht mehr als `roles_without_template`.
- Alternative (Q16 = dokumentieren): `commands/1-generic/add-project-role.md` und agent-meta-manager §8 korrigieren;
  Doctor-Regel `project-role-not-generated` (IC-21) bleibt dauerhaft.

### IC-21 Known-Issues-Registry `config/known-issues.yaml` (neu, Rev. 2)
Format (Schema als Kopfkommentar, Stil wie `config/provider-migrations.yaml:1-30`; validiert durch Tests):
```yaml
registry-version: 1
issues:
  - id: <kebab-case, eindeutig, stabil>        # Finding.check = "doctor.<id>"
    title: <eine Zeile>
    applies_to:                                 # UND-verknüpft; leer = immer
      - {capability: <key-pfad>, op: present|absent|eq|ne|truthy|falsy|in|gt|lt, value: <any>}
      - {config: <project.yaml-dotted-pfad>, op: <wie oben>, value: <any>}
      - {active_role: <role>, op: truthy|falsy}
    target:
      artifact: context_file|rules_dir|agents_dir|skills_dir|commands_dir|hooks_config_file|project_config|sync_log|<ai-providers-key>
      role: <optional>
      path: <optional, relativ zum Projekt>
    detector:
      kind: file-size|regex|path-exists|yaml-key|toml-key|json-schema|command|finding-ref
      # kind-spezifische Felder, siehe unten
    severity: ERROR|WARNING|INFO
    verified-state: VERIFIED-RUNTIME|VERIFIED-SOURCE|SOURCE-DERIVED|DOCUMENTED|UNVERIFIED
    evidence: {kind: runtime|source|docs|third-party, ref: <url oder repo-pfad:zeile>, date: YYYY-MM-DD}
    fix-hint: <ein Satz; nie automatisch angewendet>
    fix-owner: agent-meta-manager|framework-issue|project-config
    introduced-in: <agent-meta-version|null>
    fixed-in: <agent-meta-version|null>         # Runner überspringt, wenn VERSION ≥ fixed-in
```
Detektor-Felder:

| kind | Felder | Semantik |
|---|---|---|
| `file-size` | `unit: bytes\|chars\|lines`, `op: ">"\|">="`, `limit` **oder** `limit_key` (Capability-Key) | Messung über `measure_artifacts` (IC-11) |
| `regex` | `pattern`, `expect: match\|no-match`, `allow: [<literal>…]`, `scope: frontmatter\|body\|all` | zeilenweise, `re.MULTILINE` |
| `path-exists` | `path`\|`glob`\|`path_template`, `expect: present\|absent`, optional `require_suffix_key` | `path_template` darf Capture-Gruppen eines vorangehenden `regex` nutzen (`then:`) |
| `yaml-key` | `key` (dotted), `frontmatter: bool`, `op`, `value` | PyYAML `safe_load` |
| `toml-key` | `key` (dotted), `op`, `value` | Stdlib-Subset-Parser (Q21); nicht parsebar → `doctor.detector-unavailable` (INFO) |
| `json-schema` | `schema` **oder** `schema_from_key`; unterstützte Keywords: `type`, `required`, `properties`, `additionalProperties: false`, `enum` | Stdlib-Subset-Validator (Q22); unbekanntes Keyword → Registry-Test schlägt fehl |
| `command` | `argv: [sync.py-Unterbefehl…]`, `expect_exit`, `timeout_s` | nur Allowlist `--check`, `--context-report --json`, `--deactivation-status`, `--cleanup-preview`; kein Shell; sonst Registry-Test-Fehler |
| `finding-ref` | `check: <check-id oder glob>`, `source: context-budget\|active-set\|consistency\|hooks\|sync-log`, optional `match` | übernimmt Findings der referenzierten Funktion; keine Neuimplementierung |

Regeln:
- **Provider-agnostisch:** Prädikate nur über Capability-/Config-Keys; Prädikate auf Provider-Identität
  (`name`, Provider-Display-Name als `value` bei `eq`) sind verboten (Registry-Test).
- **Severity-Deckel:** `verified-state: UNVERIFIED` ⇒ effektive Severity `min(severity, WARNING)`.
- **Fail-soft-Loader:** ungültiger Eintrag → `doctor.registry-invalid` (ERROR, Exit 2 im `--strict`, sonst
  Eintrag übersprungen und gemeldet); nie Absturz.

Seed-Einträge (Phase 0; `verified-state` aus Studie, nichts darüber hinaus):

| id | Prädikat (Kurz) | Detektor | Severity | verified-state |
|---|---|---|---|---|
| `context-hard-cap-truncation` | `context_hard_cap_bytes` present | `file-size` bytes `>` `limit_key` | ERROR | VERIFIED-RUNTIME (Codex, Studie §3.2) |
| `context-soft-cap-bytes` | `context_soft_cap_bytes` present | `file-size` bytes | WARNING | VERIFIED-SOURCE (Kimi, Studie §3.5) |
| `instruction-soft-cap-chars` | `context_soft_cap_chars` present | `file-size` chars | WARNING | UNVERIFIED (Copilot 4,000; Antigravity 12,000) |
| `context-soft-cap-lines` | `context_soft_cap_lines` present | `file-size` lines | WARNING | DOCUMENTED (Claude 200) |
| `dangling-pointer` | — | `finding-ref` `context.dangling-pointer` | ERROR | VERIFIED-RUNTIME (Studie §4.4) |
| `rule-unreachable` | — | `finding-ref` `context.rule-unreachable` | ERROR | VERIFIED-RUNTIME |
| `unread-channel` | — | `finding-ref` `context.unread-channel` | WARNING | gemischt; je Provider aus Studie §4.3 |
| `rules-file-wrong-suffix` | `rules_required_suffix` present | `path-exists` mit `require_suffix_key` | WARNING | UNVERIFIED |
| `orchestrator-missing-subagent-allowlist` | `subagent_allowlist_required` eq true | `yaml-key` frontmatter `subagents` absent (Rolle `orchestrator`) | ERROR | SOURCE-DERIVED |
| `agent-name-suffix` | `agent_ext` present | `regex` Frontmatter `name:` endet auf Dateiendung (`orchestrator.agent`) | WARNING | VERIFIED-SOURCE (`agent_sync.py:892`) |
| `agent-frontmatter-strict-schema` | `agent-transform.allowed-fields` present | `json-schema` `schema_from_key` | WARNING | SOURCE-DERIVED |
| `dispatch-depth-missing` | `required_depth` present ∧ Provider mit TOML-Agentenkonfig (Capability-Key, Q21) | `toml-key` `agents.max_depth` ≥ `required_depth` | ERROR | VERIFIED-RUNTIME (Codex, Studie §3.2) |
| `dangling-role-dispatch` | — | `finding-ref` `active-set.dangling-dispatch` | ERROR | VERIFIED-SOURCE (Studie §10.2, statisch) |
| `gate-dropped-allowlist-role` | — | `finding-ref` `active-set.gate-dropped` | WARNING | VERIFIED-SOURCE |
| `unresolved-placeholder-in-output` | — | `finding-ref` `active-set.unresolved-placeholder` | WARNING | VERIFIED-SOURCE |
| `dead-variable-code-quality-rules` | `config` `variables.CODE_QUALITY_RULES` present | `regex` no-match des Werts in Artefakten | WARNING | VERIFIED-SOURCE (Studie §10.3) |
| `project-role-not-generated` | — | `path-exists` `<extension_dir>/<role>.md` present ∧ `agents_dir/<role>` absent | WARNING | VERIFIED-SOURCE (bis IC-20) |
| `hooks-not-registered` | — | `finding-ref` `hooks.enabled-but-not-registered` | ERROR | VERIFIED-SOURCE |
| `sync-pending` | — | `command` `--check`, `expect_exit: 0` | WARNING | VERIFIED-SOURCE |
| `read-only-not-enforced` | `read_only_enforcement` eq `none` ∧ aktive Rolle ohne Write/Edit | `yaml-key` | INFO | UNVERIFIED (Runtime) |
| `schema-validation-skipped` | — `finding-ref` `doctor.environment` | INFO | VERIFIED-SOURCE (`config.py:381-417`) |

`agent_ext` ist ein bestehender Key laut Studie §10.1 (Artefakt-Contract); exakter Key-Name UNVERIFIED (Planer prüft).
Je Eintrag Fixtures `tests/fixtures/doctor/<id>/{positive,negative}/` (QG-10).

### IC-22 Doctor-Runner `scripts/lib/doctor.py` + CLI `sync.py --doctor` (neu, Rev. 2)
```python
@dataclass
class DoctorFinding(Finding):          # erweitert scripts/lib/consistency/report.py:Finding
    issue_id: str = ""
    provider: str = ""                 # leer = providerübergreifend
    verified_state: str = ""
    evidence: str = ""
    fix_owner: str = ""

@dataclass(frozen=True)
class DoctorReport:
    findings: tuple[DoctorFinding, ...]
    skipped: tuple[tuple[str, str], ...]      # (issue_id, Grund: fixed-in|predicate|detector-unavailable)
    registry_version: int
    agent_meta_version: str

def load_known_issues(agent_meta_root: Path) -> tuple[list[dict], list[DoctorFinding]]
def run_doctor(project_root: Path, agent_meta_root: Path, config: dict, *, providers: Sequence[str] | None = None) -> DoctorReport
def print_doctor_json(report: DoctorReport) -> int
```
- CLI: `sync.py --doctor [--json] [--strict] [--provider <P>…]`. Handler `_handle_doctor` setzt `ctx.read_only = True`
  (Muster `--audit-config`, `cli_commands.py:658`); ruft weder Writer noch `update_roles_enum`.
- Eingaben: generierte Artefakte, `sync.log` (`[WARN]`-Zeilen unter `WARNINGS`, `log.py:52-66`),
  `.meta-config/generated-file-hashes.json`, `.meta-config/context-hashes.json`, `VERSION`/`agent-meta-version`,
  Hook-Registrierungsdateien, `ActiveSet` (IC-17), Capabilities (IC-09).
- Ablauf: Registry laden → je aktivem Provider Prädikate auswerten → Detektor ausführen → Severity-Deckel →
  sortieren (severity, issue_id, provider, file) → Ausgabe.
- JSON: `{"findings":[{severity, check, file, message, suggestion, issue_id, provider, verified_state, evidence, fix_owner}], "summary":{total, errors, warnings, infos, registry_version, agent_meta_version, skipped:[{issue_id, reason}]}}`
  (Obermenge von `print_json_report`, `report.py:78-99`).
- Exit: 0 keine ERROR (ohne `--strict`), 1 ≥ 1 ERROR (bzw. ≥ 1 WARNING mit `--strict`), 2 interner Fehler.
- Doku: `docs/api/cli-reference.md` (sonst ERROR `docs.cli_reference`, `consistency/docs.py`).
- Größe `doctor.py` ≤ 600 Zeilen (Konvention); Detektoren ggf. in `scripts/lib/doctor_detectors.py`.

### IC-23 Rolle `install-doctor` (neu, Rev. 2)
- Rollen-Key `install-doctor`; Datei `agents/1-generic/install-doctor.md`; Frontmatter `name: template-install-doctor`
  (Präfix-Konvention `agent-meta-conventions.md:15`, Präzedenz `template-template-auditor`), `version: "1.0.0"`,
  **kein** `model:`, `prompt_mode: modern`, `tools: [Read, Glob, Grep, Bash, TodoWrite]`, `description`, `hint`,
  `reference_standards`.
- Namensbegründung (Q15): „install" benennt den Prüfgegenstand (instanziierte Installation), „doctor" die
  etablierte Diagnose-Metapher (`--doctor`). `template-doctor` wird verworfen: der Rollen-Key würde mit dem
  Frontmatter-Präfix zu `template-template-doctor` und suggeriert eine Prüfung der Framework-Templates, die
  `template-auditor` bereits abdeckt.
- Body: Extension-Pointer, `{{PROJECT_CONTEXT}}`, Workflow: (1) `sync.py --doctor --json`, (2) bei Bedarf
  `--check`, `--context-report --json`; (3) Findings deduplizieren (gleiche Ursache über Provider), nach
  `fix-owner` gruppieren, UNVERIFIED-Vorbehalt ausweisen; (4) keine Reparatur.
- Bash-Allowlist im Prompt: nur `sync.py --doctor|--check|--context-report|--deactivation-status|--cleanup-preview`,
  `git status|log|diff` read-only. Read-only-Durchsetzung ist providerabhängig (F-32) — Prompt-Ebene + Known-Issue.
- Output-Contract:
  ```
  STATUS: done|partial|failed
  RESULT: <1-2 Sätze>
  ARTIFACTS: <Pfade, z. B. .tmp/doctor/<ts>.json oder none>
  FINDINGS: D-nn | ERROR|WARNING|INFO | <issue_id|check> | <file[:line]> | <provider|all> | <verified-state>
            Befund: … / Beleg: … / Fix: … (fix-owner)
  GATES: doctor=<exit>, check=<exit|skipped>
  NEXT: agent-meta-manager (project-config) | {{#if ROLE_META_FEEDBACK_ACTIVE}}meta-feedback{{else}}Nutzer: Framework-Issue{{/if}} (framework-issue) | none
  ```
- `<constraints>`: `{{PROMPT_INJECTION_DEFENSE_BLOCK}}`, `{{OUTPUT_GUARD_BLOCK}}`; Worker-Rolle, nie an `orchestrator` delegieren.
- `role-defaults.yaml`: `model: fast`, `memory: ''`, `workflow_tier: optional`, `description`, `short_desc`,
  `routing: {addressability: name_only, name_only_reason: <Text>, parallel: false, orchestrator_only: true}`,
  **kein** `routing_patterns`, `handoff: {input_contracts: [task-spec-v1], output_contract: doctor-findings-v1, target_roles: [agent-meta-manager]}`.

### IC-24 Config-Optimizer-Runner `scripts/lib/config_optimizer.py` + CLI (neu, Rev. 2)
```python
CandidateKind = Literal[
    "no-effect",                 # Entfernen ist byte-gleich (umfasst: vom Builder überschrieben, gleich Default, unbenutzt in aktiven Artefakten)
    "dead-variable-content-loss",# no-effect, aber substanzieller Inhalt (> threshold) → Relokation statt Löschung
    "duplicate-value",           # gleicher Wert unter zwei Keys
    "relocate-to-ext",           # rollen-spezifischer Inhalt → <prefix>-<role>-ext.md
    "relocate-to-doc",           # hoher Fan-out → Doku-Datei + Pointer
    "semantic-merge",            # inhaltliche Zusammenführung
]

@dataclass(frozen=True)
class Candidate:
    id: str                      # stabil, z. B. "OPT-no-effect:variables.ORCHESTRATOR_STRICT"
    kind: CandidateKind
    yaml_path: str
    deterministic: bool          # True nur für no-effect
    proof_level_required: Literal["L0", "L1", "L2", "L3"]
    yaml_bytes_saved: int
    injected_bytes_saved_est: int   # Σ über aktive Provider-Artefakte; 0 bei L0 per Definition
    rationale: str
    hunks: tuple[str, ...]       # Unified-Diff-Hunks (project.yaml und ggf. Zieldatei)

@dataclass(frozen=True)
class FanOutEntry:
    variable: str
    value_bytes: int
    occurrences: int
    files: int
    injected_bytes: int
    per_provider: Mapping[str, int]

@dataclass(frozen=True)
class OptimizerProposal:
    project_yaml_sha256: str
    agent_meta_version: str
    candidates: tuple[Candidate, ...]
    fan_out: tuple[FanOutEntry, ...]
    diff: str                    # vollständiger Unified Diff aller deterministischen Kandidaten

def collect_candidates(project_root: Path, agent_meta_root: Path, config: dict, config_text: str, active: ActiveSet) -> OptimizerProposal
def apply_config_patch(project_root: Path, agent_meta_root: Path, proposal: OptimizerProposal, accept_ids: Sequence[str], *, dry_run: bool) -> "ProofReport"
```
- CLI Analyse: `sync.py --optimize-config [--json] [--include-semantic] [--out <dir>]`; read-only bis auf
  `<dir>` (Default `.tmp/config-optimizer/<YYYYMMDD-HHMMSS>/` mit `proposal.json`, `proposal.diff`, `proof.json`).
  Exit 0 (auch mit Kandidaten), 2 interner Fehler.
- CLI Anwendung: `sync.py --apply-config-patch <proposal.json> [--accept <id>…] [--dry-run]`; schreibt
  `.meta-config/project.yaml` (und bei Relokation Zieldateien) **nur**, wenn IC-25 für alle angenommenen
  Kandidaten bestanden ist; atomar (Temp-Datei + Replace). Ohne `--accept` werden nur `deterministic`-Kandidaten
  angewendet; `semantic-merge`/`relocate-*` nur mit expliziter `--accept <id>`.
- Algorithmus Kandidatensuche:
  1. Sentinel-Render: jeder Textwert unter `variables:` wird mit `QZ<NAME>QZ…ZQ<NAME>ZQ` umschlossen; ein Render aller
     aktiven Provider in `.tmp/` → `FanOutEntry` je Variable (Technik Studie §10.3).
  2. `occurrences == 0` → `no-effect`-Kandidat; ist der Wert länger als `content_loss_threshold_bytes`
     (Default 200, Konstante) → stattdessen `dead-variable-content-loss`.
  3. Wert gleich Framework-Fallback/Default (`_VARIABLE_FALLBACKS`, `role-defaults.yaml::se_variables`, Schema-Defaults) → `no-effect`-Kandidat (Beweis via L0).
  4. Builder-eigene Variablen (unbedingt nach der Nutzer-Schleife gesetzt, z. B. `config.py:1493,1583-1586,1660`) → `no-effect`.
  5. Gemeinsame L0-Verifikation aller `no-effect`-Kandidaten (ein Render ohne alle); bei Abweichung Bisektion bis
     zur Einzelursache; nicht bestätigte Kandidaten entfallen.
  6. `duplicate-value`, `relocate-*`, `semantic-merge`: nur mit `--include-semantic`; `injected_bytes_saved_est` aus Fan-out.
- Diff: `difflib.unified_diff`, `n=3`, Labels `a/.meta-config/project.yaml`/`b/.meta-config/project.yaml`, LF.
  Zeilenbasiert: ein Kandidat entfernt genau die Zeilen des Keys inkl. Block-Scalar-Fortsetzungszeilen und
  direkt zugehöriger Inline-Kommentare; vorangestellte eigenständige Kommentarzeilen bleiben (Q24).
- Fehlerpfade: `project.yaml`-Hash ≠ `project_yaml_sha256` → `config-optimizer.stale-proposal` (Exit 1, kein Schreiben);
  Beweis fehlgeschlagen → `config-optimizer.proof-failed` (Exit 1, kein Schreiben, `proof.json` mit Gründen);
  `--fill-defaults` in derselben Invocation → Abbruch `config-optimizer.lossy-flag` (Exit 2).
- Nur Stdlib + PyYAML; Python-3.9-kompatibel.

### IC-25 Verlustfreiheits-Beweis (neu, Rev. 2)
```python
@dataclass(frozen=True)
class ProofReport:
    level_reached: Literal["none", "L0", "L1", "L2", "L3"]
    files_compared: int
    byte_equal_files: int
    changed_files: tuple[str, ...]
    placeholder_sets_equal: bool
    unresolved_placeholders_before: int
    unresolved_placeholders_after: int
    token_multiset_equal: bool          # nur geänderte Dateien
    anchors_ok: bool                    # IC-12
    relocation_reachable: bool | None   # L2
    roundtrip: "RoundTripReport"        # scripts/lib/yaml_roundtrip.py:analyze_roundtrip
    expected_comment_loss: int
    ok: bool
    reasons: tuple[str, ...]

def prove(before_render: Path, after_render: Path, before_yaml: str, after_yaml: str, level: str, *, relocations: Sequence["Relocation"] = ()) -> ProofReport
```

| Stufe | Bedingung (alle aktiven Provider, alle generierten Artefakte) | Für |
|---|---|---|
| L0 | jede Datei byte-gleich; Dateimenge gleich | `no-effect` |
| L1 | Placeholder-Mengen gleich; unaufgelöste Platzhalter nicht mehr; Multiset aus Identifiern (`[A-Za-z_][\w./-]+`), Zahlen/Versionen, Pfaden, Backtick-Spans, Code-Fence-Kommandos, URLs je geänderter Datei gleich; Anker (IC-12) vorhanden | `duplicate-value` (Minimum) |
| L2 | L1 auf allen nicht betroffenen Dateien; jedes entfernte Token-Multiset ist in der Zieldatei enthalten; jeder betroffene Agent enthält einen Pointer auf die Zieldatei (`path-exists`) | `relocate-*` |
| L3 | L1-Prüfungen als Minimum + ausdrückliche Annahme je Kandidat-ID; im Report `deterministic: false` | `semantic-merge` |

- Roundtrip-Guard: `analyze_roundtrip(before_yaml, after_yaml)`; bestanden ⇔ `order_changed == False` **und**
  `lost_comments == expected_comment_loss`, wobei `expected_comment_loss` = Anzahl Kommentare auf den entfernten Zeilen
  (aus den Hunks berechnet). `assert_roundtrip_preserved(..., allow_lossy=True)` wird nicht verwendet.
- Renders laufen über denselben Codepfad wie `--check` in Temp-Projekte unter `.tmp/`; keine Schreibzugriffe auf
  das Projekt oder den agent-meta-Root (insbesondere kein `update_roles_enum`).

### IC-26 Rolle `config-optimizer` (neu, Rev. 2)
- Rollen-Key `config-optimizer`; Datei `agents/1-generic/config-optimizer.md`; `name: template-config-optimizer`,
  `version: "1.0.0"`, **kein** `model:`, `prompt_mode: modern`, `tools: [Read, Glob, Grep, Bash, TodoWrite]`.
- Namensbegründung (Q15): Gegenstand ist die Projekt-Config (nicht der Kontext an sich); Suffix `-optimizer`
  folgt `performance-optimizer`. Verworfen: `context-optimizer` (verwechselbar mit dem Profil `compact`).
- Workflow: (1) `sync.py --optimize-config --json` (optional `--include-semantic`); (2) deterministische Kandidaten
  als Unified Diff zeigen, getrennt: YAML-Einsparung vs. Injektions-Einsparung; (3) semantische Kandidaten mit
  Begründung, Risiko und `NON-DETERMINISTIC`-Kennzeichnung; (4) nie selbst schreiben.
- Bash-Allowlist: `sync.py --optimize-config`, `--context-report --json`, `--doctor --json`, `git status|diff` read-only.
- Output-Contract:
  ```
  STATUS: done|partial|failed
  RESULT: <1-2 Sätze>
  ARTIFACTS: .tmp/config-optimizer/<ts>/proposal.json, proposal.diff, proof.json
  PROPOSALS: OPT-id | kind | deterministic | proof-level | yaml-Δbytes | injected-Δbytes(est)
  PROOF: <level_reached, byte_equal_files/files_compared, roundtrip ok/nok>
  NEXT: agent-meta-manager → sync.py --apply-config-patch <proposal.json> [--accept <ids>] (nach Nutzerfreigabe) | none
  ```
- `role-defaults.yaml`: `model: balanced`, `memory: ''`, `workflow_tier: optional`,
  `routing: {addressability: name_only, name_only_reason: <Text>, parallel: false, orchestrator_only: true}`,
  **kein** `routing_patterns`, `handoff: {input_contracts: [task-spec-v1], output_contract: config-patch-proposal-v1, target_roles: [agent-meta-manager]}`.

### IC-27 Handoff-Contracts und `agent-meta-manager` (Rev. 2)
- Neue Contracts `doctor-findings-v1`, `config-patch-proposal-v1`; Schemas unter `schemas/handoffs/` nach bestehendem Muster
  (Ort der bestehenden Handoff-Schemas laut Studie §10.1; exakte Dateinamen UNVERIFIED).
- `agent-meta-manager`: `handoff.input_contracts` += beide Contracts (sonst `handoff.output-not-consumed`,
  `handoff_contracts.py:95-110`); neuer Abschnitt „Doctor-/Optimizer-Vorschläge anwenden": nur nach
  ausdrücklicher Nutzerbestätigung (Advisory Mode, `agent-meta-manager.md:30`), Anwendung **ausschließlich**
  über `sync.py --apply-config-patch`, nie per `Edit` auf `project.yaml` und nie mit `--fill-defaults`.
  Version-Bump `agent-meta-manager`.
- Optional (Q17-unabhängig): `template-auditor`-Contract `audit-findings-v1` erhält denselben Konsumenten (F-20).
- **Phase 3 (Boilerplate-De-Dup, F-29):** `OUTPUT_GUARD_BLOCK`, `BACKGROUND_PROCESS_GUARD`, `PROMPT_INJECTION_DEFENSE_BLOCK`,
  `PARSE_INPUT_BLOCK` als je eine Rule/ein referenziertes Snippet statt Inline-Kopie — nur, wenn Q6 (erhalten
  Subagenten Rules?) je Provider positiv beantwortet ist; sonst bleibt Inline. Opt-in, eval-gated (QG-1), Anker (QG-3).

### IC-28 Neue-Rolle-Checkliste (gilt für `install-doctor` und `config-optimizer`, Rev. 2)
Abgeleitet aus Commit 507bbb5 (+ 1ff89be). Je Rolle vollständig, sonst kein Merge:

| # | Schritt | Prüfung |
|---|---|---|
| 1 | Template `agents/1-generic/<role>.md`: `name: template-<role>`, `version: "1.0.0"`, **kein** `model:`, Tools nur `Read, Glob, Grep, Bash, TodoWrite`, `prompt_mode: modern`, Extension-Pointer, `{{PROJECT_CONTEXT}}`, Output-Contract, `{{PROMPT_INJECTION_DEFENSE_BLOCK}}`, `{{OUTPUT_GUARD_BLOCK}}`; alle Platzhalter in `consistency/placeholders.py` bekannt; jedes `{{#if X}}` mit Eintrag in `standalone.py` (`_CONDITIONAL_FALSE_FLAGS`/`_IDENTITY_FALLBACKS`, `:54,107-119`) | `consistency-check` grün; Szenario |
| 2 | `config/role-defaults.yaml`-Eintrag: `routing.addressability: name_only` + `name_only_reason`, `orchestrator_only: true`, **kein** `routing_patterns`, Handoff gemäß IC-23/IC-26; `target_roles` nur mit Consumer-Contract in `agent-meta-manager` (IC-27) | `crossrefs.*`, `handoff.*` grün; neuer Test `test_name_only_roles_have_no_routing_patterns` (QG-12) |
| 3 | Schema-Rollen-Enum (`config/project-config.schema.json`) per Sync regeneriert (`schema.py:22-40`, `update_roles_enum`) und committet | Diff enthält beide Rollen |
| 4 | Gepinnte Tests: `tests/test_role_addressability_coverage.py` `_EXPECTED_TOTAL` 92 → **94**, Verteilung `{"keyword": 88, "name_only": 5, "excluded": 1}`, sortierte Liste `["config-optimizer", "install-doctor", "intern-developer", "principal-developer", "template-auditor"]`; `_GOLDEN_ROLE_COUNT` (`test_template_slimming_equivalence.py:84`) unverändert; `_EXPECTED_GROUPS` (`test_role_activation_schema.py:21`) nur bei neuer Aktivierungsgruppe (Q17) | pytest grün |
| 5 | Standalone-Export regeneriert (`sync.py --render-standalone`), `standalone/agents/<role>.md` + `standalone/README.md` committet | `tests/test_standalone_export_in_sync.py` grün |
| 6 | Szenarien **77** (`install-doctor`) und **78** (`config-optimizer`): Zeile in `tests/scenarios/registry.md`, `configs/7x-<role>.project.yaml`, `asserts/7x-<role>.sh` **mit `chmod +x`** (`run.sh:75` prüft `-x`); Asserts: generiert je Provider, kein Write/Edit/Agent, OpenCode `edit: deny`, kein `model:` in der Quelle, Platzhalter aufgelöst, Contract-Marker vorhanden, **keine** Keyword-Regel für die Rolle in `routing.rules` (statt Enum-Ausschluss wie Szenario-76-Assert #5) | `tests/scenarios/run.sh` grün in CI |
| 7 | `CHANGELOG.md` Unreleased-Eintrag | `crossrefs.changelog-missing-entry` grün |
| 8 | Doku: `docs/guides/setup/instantiate-project.md` (Rollenliste), README-Rollentabelle (Englisch), `docs/api/cli-reference.md` für `--doctor`, `--optimize-config`, `--apply-config-patch` | `docs.cli_reference` grün |
| 9 | Optional Self-Hosting: Rollen in `.meta-config/project.yaml roles:` + Re-Sync (aktualisiert `generated-file-hashes.json`) | `--check` grün |
| 10 | Aktivierungsgruppe: optional (Q17; Empfehlung keine) | ggf. `_EXPECTED_GROUPS` + Schema |
| 11 | Provider-agnostisch: keine `if provider == "Name"`, nur Capability-Keys | `test_no_provider_literal_usage_in_lib` grün |
| 12 | Version-Bumps berührter Templates (`agent-meta-manager`, `orchestrator` bei Delegationsänderung) | `frontmatter.version-bump` grün |

Diese Checkliste wird zusätzlich als Abschnitt in `rules/2-platform/agent-meta-conventions.md` (bzw. Skill
`conventions`) übernommen, damit sie für künftige Rollen gilt (F-20).

## 6. Datenfluss

```
project.yaml (context-profile, provider-overrides.<P>.context-profile, context_file.*, rules-preset, roles,
              project-roles, reflection-pairs, variables)
        │
        ▼ compute_active_set (IC-17) ── sync.log: gate-dropped / unknown-role / project-role-*
        │        └─► ActiveSet (einmal je Sync; einzige Quelle für alle Rollen-Konsumenten)
        │
        ▼ resolve_context_profile (IC-02) ── sync.log: aufgelöste Werte je Provider
        │
        ├─► build_variables: CONTEXT_PROFILE, CONTEXT_PROFILE_COMPACT, COMPACT_MODE (abgeleitet),
        │                    ACTIVE_ROLES, ROLE_*_ACTIVE, PROJECT_SPECIFIC_AGENTS (IC-17),
        │                    MAX_ITERATIONS aus Konsumenten-reflection-pairs (IC-15/17)
        │
        ├─► Pipelines ── apply_overrides → filter_pipelines_by_active_set (IC-18/2) → validate (gegen ActiveSet)
        │              └─ ein einziges `effective` für §2, §2a, pipeline-details, routing.pipelines
        ├─► Orchestrator-Render ── C1 render_routing_lines (IC-04) | JSON/YAML (full)
        │                       ├─ C2 Konditionale §2a/§9/<context> (IC-05)
        │                       └─ Active-Set-Konditionale §4/Anti-Recursion/Direct-Dispatch/Persona (IC-18)
        ├─► Entry-File ── shared_users = aktive Provider (IC-15/1)
        │               └─ gate-card | rules-embedded, agents-list-compact | agents-table (IC-06)
        ├─► Rules ── Kanal je rules_read_channels (IC-07/IC-09) ── Skills je skills_discovery_dirs; ROLE_*_ACTIVE-Konditionale
        ├─► Commands ── requires_roles ⊆ ActiveSet (IC-18/9)
        ├─► Bootstraps ── nur aktive Provider (C4)
        │
        ▼ write_checked (byte-stabil, sortiert, keine Zeitstempel in dynamischer Position)
        │
        ▼ Consistency (IC-10, IC-19): Caps, Dangling-Pointer, Reachability, Unread, Anker (IC-12),
        │                            Dangling-Dispatch, Unresolved-Placeholder
        │
        ▼ --context-report (IC-11) ──► CI-Budgets (QG-4)
                                  └─► Role-Routing-Eval nightly (IC-13) / Capture manuell (IC-14)

Installation (read-only):
  known-issues.yaml (IC-21) + Capabilities (IC-09) + ActiveSet
        └─► sync.py --doctor (IC-22) ── finding-ref → IC-10 / IC-19 / hooks.* ── Detektoren
               └─► JSON-Report ─► install-doctor (IC-23) ─► doctor-findings-v1 ─► agent-meta-manager / Framework-Issue

Projekt-Config (Vorschlag → Beweis → Anwendung):
  project.yaml + ActiveSet ─► sync.py --optimize-config (IC-24): Sentinel-Render → Fan-out → Kandidaten → L0-Verifikation
        └─► .tmp/config-optimizer/<ts>/{proposal.json, proposal.diff, proof.json}
               └─► config-optimizer (IC-26) ─► config-patch-proposal-v1 ─► Nutzerfreigabe
                      └─► agent-meta-manager: sync.py --apply-config-patch (IC-24/IC-25: Re-Beweis + Roundtrip-Guard) ─► project.yaml
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
| QG-9 (Rev. 2) | Dangling-Reference-Test `tests/test_active_set_dangling.py`: Fixture-Projekte p10-artig (10 Rollen), p20-artig (`senior-developer` ohne `junior-developer`), alle Rollen, Plattform `homeassistant`; je Provider der Matrix: null `active-set.dangling-dispatch` (ab Phase 1), `gate-dropped` gemeldet, keine unaufgelösten Platzhalter außerhalb der Allowlist | deterministisch | jede CI |
| QG-10 (Rev. 2) | Doctor-Registry-Test `tests/test_known_issues_registry.py` (Form, eindeutige IDs, Enums, Severity-Deckel, keine Provider-Identitäts-Prädikate, nur unterstützte Detektor-Arten/Keywords, `command` nur Allowlist) + `tests/test_doctor_fixtures.py`: je Eintrag `positive/` ⇒ ≥ 1 Finding mit `check == doctor.<id>` bzw. referenzierter Check-ID, `negative/` ⇒ 0; Read-only-Test (Hash-Snapshot von Projekt- und agent-meta-Baum vor/nach `--doctor` gleich) | deterministisch | jede CI |
| QG-11 (Rev. 2) | Optimizer-Lossless-Test `tests/test_config_optimizer.py`: (a) überschriebene/Default-gleiche/unbenutzte Variable ⇒ L0 bestanden; (b) wirksame Variable fälschlich als Kandidat injiziert ⇒ L0 schlägt fehl, Kandidat verworfen; (c) Kommentare erhalten außer auf entfernten Zeilen (exakte Zahl), Key-Reihenfolge erhalten; (d) veralteter Vorschlag ⇒ Exit 1 ohne Schreiben; (e) semantischer Kandidat ohne `--accept` ⇒ nicht angewendet; (f) Fan-out-Zahlen = unabhängige Sentinel-Zählung | deterministisch | jede CI |
| QG-12 (Rev. 2) | Neue-Rolle-Konformität (IC-28): Pins in `test_role_addressability_coverage.py`, `test_name_only_roles_have_no_routing_patterns`, Szenarien 77/78, Standalone-Export | deterministisch | jede CI |
| QG-13 (Rev. 2) | Active-Set-Single-Source: Guard-Test `tests/test_active_set_single_source.py` (statisch: kein `config["roles"]`/`config.get("roles")` in Generator-Modulen außerhalb `active_set.py`/`roles.py`; dynamisch: alle IC-18-Konsumenten erhalten dasselbe `ActiveSet`-Objekt) | deterministisch | jede CI |

Test-Churn (Format-Pins):

| Test | `full` | `compact` |
|---|---|---|
| `tests/test_orchestrator_name_dispatch.py:61-111` (parst JSON/YAML) | unberührt | format-gepinnt → Zeilenparser-Variante nötig |
| `tests/test_routing_tool_definitions.py` | unberührt (außer IC-15/15; Rev. 2: `input_contracts`-Filter IC-18/4) | format-gepinnt |
| `tests/test_routing_name_index.py` | unberührt | format-gepinnt |
| `tests/test_developer_tiers_gate.py:44-65` | unberührt (Rev. 2: §4-Konditional IC-18/5 prüfen) | format-gepinnt (Flags `req`/`rec`) |
| `tests/test_template_slimming_equivalence.py:1233-1283` (Golden) | Rebaseline nur IC-15/11 (Rev. 2: zusätzlich Active-Set-Filter IC-18/2–8, eigener PR je Konsument) | eigenes Golden |
| `tests/test_delegation_table.py` | ändert sich durch IC-15/11 | betroffen (Tabelle entfällt/Liste) |
| `test_context_compact_mode.py:246-268` | unberührt | Schwellen neu |
| `tests/test_routing_overlap.py`, `tests/test_role_addressability_coverage.py` | unberührt (Datenebene; Rev. 2: Pins 94/5, IC-28) | unberührt |
| `scripts/lib/consistency/placeholders.py:111-119` | neue Built-ins (Rev. 2: `ROLE_*_ACTIVE`, `ACTIVE_ROLES`) | neue Built-ins |
| (Rev. 2) `tests/scenarios/asserts/76-template-auditor-role.sh:63-76` | Assert #5 ersetzen (IC-15/14) | — |
| (Rev. 2) Pipeline-bezogene Tests (`tests/test_*pipeline*.py`, exakte Liste UNVERIFIED) | Fixtures mit inaktiven Stage-Rollen ändern Erwartung (Pipeline gedroppt) | — |

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

### Rev. 2 — Phase 0 (Doctor, Checks als WARN; keine Render-Änderung)
37. **AC-37** `config/known-issues.yaml` existiert mit mindestens allen Seed-IDs aus IC-21; `tests/test_known_issues_registry.py` ist grün (Form, eindeutige IDs, Enums, keine Provider-Identitäts-Prädikate, nur unterstützte Detektor-Arten/JSON-Schema-Keywords, `command` nur Allowlist).
38. **AC-38** Für jeden Registry-Eintrag existieren `tests/fixtures/doctor/<id>/positive/` und `.../negative/`; `sync.py --doctor --json` liefert auf `positive` ≥ 1 Finding mit der erwarteten Check-ID und auf `negative` 0 Findings dieser ID.
39. **AC-39** `sync.py --doctor` ist read-only: SHA-256-Snapshot aller Dateien unter Projekt-Root (ohne `.tmp/`) und agent-meta-Root ist vor und nach dem Lauf identisch; Exit 0 ohne ERROR, 1 mit ERROR, 1 mit WARNING nur bei `--strict`, 2 bei internem Fehler (je ein Test); JSON enthält `summary.registry_version` und `summary.skipped`.
40. **AC-40** Ein Eintrag mit `severity: ERROR` und `verified-state: UNVERIFIED` erscheint als WARNING; ein Lauf, der nur solche Befunde hat, endet mit Exit 0.
41. **AC-41** Für `finding-ref`-Einträge stimmen Check-ID und Anzahl der Doctor-Findings mit dem direkten Aufruf der referenzierten Check-Funktion (IC-10/IC-19) auf derselben Fixture überein; `doctor.py` enthält keine eigene Implementierung dieser Checks (Import-Test).
42. **AC-42** Auf einem Codex-Multi-Provider-Fixture mit AGENTS.md ≥ 32,768 B meldet `--doctor` `doctor.context-hard-cap-truncation` (ERROR) und endet mit Exit 1.
43. **AC-43** `active-set.*`-Checks (IC-19) laufen als WARN: im p10-artigen Fixture meldet `active-set.dangling-dispatch` mindestens Dispatches an `senior-developer`, `validator`, `bug-feature-analyzer`, `concept-specifier`, `concept-reviewer`, `ideation`; im p20-artigen Fixture meldet `active-set.gate-dropped` `senior-developer` mit Gruppe `developer_tiers`; im Alle-Rollen-Fixture meldet `active-set.unresolved-placeholder` u. a. `{{EXTRA_DONTS}}`.
44. **AC-44** `docs/api/cli-reference.md` dokumentiert `--doctor` (`docs.cli_reference` grün); `install-doctor` erfüllt IC-28 vollständig (QG-12 grün, Szenario 77 grün).

### Rev. 2 — Phase 1 (Active-Set-Filter; ändert `full` bewusst, je Konsument eigener PR)
45. **AC-45** Alle IC-18-Konsumenten erhalten dasselbe `ActiveSet`; QG-13 grün (kein Rohzugriff auf `config["roles"]` in Generatoren).
46. **AC-46** Im p10-artigen Fixture werden nur Pipelines gerendert, deren Pflicht-Stage-Rollen aktiv sind — konsistent in §2, §2a, `pipeline-details/`, `routing.pipelines`, `PIPELINE_MATCH_TABLE`; jede entfernte Pipeline erscheint als `active-set.pipeline-dropped` in `sync.log`; keine veraltete `pipeline-details`-Datei bleibt nach Re-Sync bestehen.
47. **AC-47** `allowed_agents` ⊆ `ActiveSet.roles`; jeder `input_contracts`-Eintrag in `routing.rules` hat einen aktiven Producer.
48. **AC-48** Mit `DEVELOPER_TIERS_ENABLED=false` enthält der Orchestrator keine Referenz auf `junior-developer`, `senior-developer`, `principal-developer`; mit `true` ist §4 byte-identisch zum Stand vor der Änderung.
49. **AC-49** Über die Fixture-Matrix (p10-, p20-, Alle-Rollen-, `homeassistant`-artig) × Provider-Matrix: null `active-set.dangling-dispatch` (Check ist ERROR); `active-set.dangling-mention` wird gezählt und liegt außerhalb `mention_allow` bei 0 für Orchestrator, Pipelines und Commands.
50. **AC-50** Ein Command mit `requires_roles`, dessen Rolle inaktiv ist, wird nicht generiert; ein zuvor generierter wird als Managed-File entfernt.
51. **AC-51** Ein Konsumentenprojekt ohne `reflection-pairs` erhält `MAX_ITERATIONS=3` unabhängig von agent-metas eigener `.meta-config/project.yaml`; mit Projekt-Override gilt der Projektwert (IC-15 Nr. 17).
52. **AC-52** Pipeline-Validierungswarnungen werden gegen `ActiveSet.roles` berechnet: das p20-artige Fixture nennt `senior-developer`; Stages mit inaktivem `dod_flag` erzeugen keine Warnung (IC-15 Nr. 18).
53. **AC-53** Projekt-spezifische Rollen (bei Q16 = implementieren): eine Rolle aus `.meta-config/agents/<role>.md` + `project-roles` erscheint als Agent-Datei, im Enum, `name_index`, in `routing.rules` (sofern `keyword`), in der Agent-Tabelle und in `PROJECT_SPECIFIC_AGENTS`; `--audit-config` meldet keinen ERROR. (Bei Q16 = dokumentieren: Doku korrigiert und Doctor-Regel `project-role-not-generated` mit Fixture grün.)

### Rev. 2 — Phase 2 (Config-Optimizer)
54. **AC-54** `sync.py --optimize-config --json` schreibt ausschließlich unter `.tmp/config-optimizer/`; auf der selbst-gehosteten `.meta-config/project.yaml` enthält der Vorschlag mindestens `no-effect`-Kandidaten für `variables.ORCHESTRATOR_STRICT`, `variables.UNKNOWN_FALLBACK_*` und `variables.SE_BASE_DIR` sowie `CODE_QUALITY_RULES` als `dead-variable-content-loss` (nicht als Löschung).
55. **AC-55** Anwenden aller deterministischen Kandidaten ergibt für alle aktiven Provider byte-identische generierte Artefakte (L0); ein Test mit einer absichtlich wirksamen Variable als Kandidat führt zu `config-optimizer.proof-failed` ohne Schreiben.
56. **AC-56** `--apply-config-patch` erhält alle Kommentare außer denen auf entfernten Zeilen (exakte Anzahl laut Hunks) und die Reihenfolge aller verbleibenden Keys (`analyze_roundtrip`); kein `yaml.dump` der Gesamtdatei; veralteter Vorschlag (Hash-Mismatch) ⇒ Exit 1 ohne Schreiben.
57. **AC-57** Semantische Kandidaten (`duplicate-value`, `relocate-*`, `semantic-merge`) tragen `deterministic: false`, erscheinen nur mit `--include-semantic` und werden nur mit `--accept <id>` angewendet; `relocate-*` besteht L2 (Token in Zieldatei, Pointer in jedem betroffenen Agenten).
58. **AC-58** Der Fan-out-Report (`fan_out`) nennt je Variable Vorkommen, Dateien, injizierte Bytes je Provider; die Werte stimmen exakt mit einer unabhängigen Sentinel-Zählung auf derselben Fixture überein.
59. **AC-59** `config-optimizer` erfüllt IC-28 vollständig (QG-12 grün, Szenario 78 grün); `agent-meta-manager` konsumiert `config-patch-proposal-v1` und `doctor-findings-v1` (kein `handoff.output-not-consumed`); `docs/api/cli-reference.md` dokumentiert `--optimize-config` und `--apply-config-patch`.

### Rev. 2 — Phase 3 und Quer
60. **AC-60** Boilerplate-De-Dup (IC-27, Phase 3) nur als Opt-in und nur für Provider mit positiv beantworteter Q6; Eval ≥ Baseline − 1.0 Prozentpunkt; Anker (QG-3) grün; ohne Opt-in byte-identisch (AC-35 sinngemäß).
61. **AC-61** Neue Module (`active_set.py`, `doctor.py`, `config_optimizer.py`, Checks) enthalten keine Provider-Literale; Registry-Prädikate sind ausschließlich Capability-/Config-/Rollen-Prädikate; `test_no_provider_literal_usage_in_lib` grün.

## 9. Phasen

| Phase | Name | Inhalt | ACs | Verhaltensänderung |
|---|---|---|---|---|
| 0 | Messen & Absichern | Role-Routing-Eval + Baseline, Tokenizer-Messung, `--context-report`, Anker-Registry, Budgets als Obergrenzen, Dangling/Reachability als WARN, Doku-Korrekturen; **(Rev. 2)** IC-09-Keys (nur Daten), IC-17 `ActiveSet` (berechnet, noch ohne Konsumenten-Umstellung), IC-19-Checks als WARN, IC-21 Registry, IC-22 `--doctor`, IC-23 `install-doctor`, IC-28 Checkliste in Konventionen | AC-01…AC-09, AC-37…AC-44 | keine (nur neue read-only Werkzeuge, neue `sync.log`-WARNs) |
| 1 | Kanäle & Korrektheit | IC-15 Nr. 1–21, je eigener Issue/PR; Goldens wo nötig aktualisiert; **(Rev. 2)** IC-18 Active-Set-Konsumenten (je Konsument eigener PR, Reihenfolge = Rangliste §11.1), IC-19 `dangling-dispatch` → ERROR, IC-20 projekt-spezifische Rollen (Q16) | AC-10…AC-22, AC-45…AC-53 | Bugfixes (auch in `full`) |
| 2 | Profil `compact` | IC-01…IC-12, C1–C7 (IC-09-Keys liegen bereits seit Phase 0 vor); **(Rev. 2)** IC-24…IC-27 Config-Optimizer + Applier + `config-optimizer`-Rolle (unabhängig vom Profil, parallel möglich) | AC-23…AC-32, AC-54…AC-59 | nur mit Opt-in (Profil) bzw. nur auf Anforderung (Optimizer) |
| 3 | Erweiterungen | IC-16: `ultra`/Rollenprofil, Vererbungs-Flags, Kimi `${agents_md}`/Plugin-`systemPrompt`, Admin-UI, Claude `paths:`, `permission.task`; **(Rev. 2)** Boilerplate-De-Dup (IC-27), datengetriebene „Delegation (reference only)"-Listen (Q19), L2-Relokationen hoher Fan-out-Variablen | AC-33…AC-35, AC-60 | nur mit Opt-in |

Reihenfolge-Regel: Phase 2 beginnt erst, wenn AC-02 (Baseline) erfüllt ist; IC-04 wird nicht gemergt, bevor AC-25 nachgewiesen ist. AC-36 und AC-61 gelten in allen Phasen.
(Rev. 2) Zusatzregeln: IC-18 Nr. 2 (Pipelines) wird vor IC-04 gemergt, damit das Zeilenformat bereits auf der
gefilterten Pipeline-Menge basiert. Der Config-Optimizer (Phase 2) setzt IC-17 (Phase 0) voraus, nicht das Profil.
Die IC-19-Check-Stufe wechselt erst auf ERROR, wenn AC-49 auf der vollständigen Fixture-Matrix grün ist.

## 10. ADRs (Kurzform)

| ADR | Kontext | Entscheidung | Konsequenzen |
|---|---|---|---|
| ADR-1 Profil statt Einzelschalter | Verdichtung verteilt auf `context_file.mode`, `rules-preset`, Bootstrap-`compact` | eine Bündelachse `context-profile`; Einzelschalter bleiben und gewinnen | einfache Nutzung; Präzedenzlogik nötig (IC-02) |
| ADR-2 Format B mit `;` | Stichprobe: B kleinstes Format (7,975 B vs. A 8,991 B, C 8,936 B) | Zeilenformat B, `;`-Trenner, Flags nur bei Nicht-Default | JSON-Parser-Tests für `compact` anpassen; Format-Risiko → QG-1 |
| ADR-3 Alle Keywords, kuratierte Beispiele | 55 von 76 Beispielen ohne neues Signal; Tool-Use-Evidenz spricht für Beispiele | alle Keywords + erstes Beispiel + signaltragende Beispiele | deterministisch, prüfbar (QG-2) |
| ADR-4 Bugfixes vor Profil | viele Defekte wirken auch in `full` | Phase 1 vor Phase 2, eigene PRs | `full`-Ausgabe ändert sich in Phase 1 bewusst |
| ADR-5 Shared File fällt auf `full` | geteilte AGENTS.md, gemischte Profile | sichere Seite + WARN | Opt-in pro Provider bei geteilter Datei wirkungslos (Q12) |
| ADR-6 Doctor = Registry + Runner + Rolle; Checks als Bibliothek | IC-10/IC-11 planen bereits Cap-, Pointer-, Kanal-Checks; ohne Abgrenzung entstünden zwei Implementierungen | Checks sind reine Funktionen über `project_root` (IC-10/IC-19); Sync-Ende, `--doctor` und Tests rufen dieselben Funktionen; die Registry fügt nur Metadaten (Evidenz, Verifikationsstatus, Fix-Owner) und eigene Detektoren für nicht abgedeckte Klassen hinzu (`finding-ref`) | keine Doppelimplementierung; Doctor hängt zeitlich an IC-10/IC-19 (beide Phase 0) |
| ADR-7 Ein Active-Set-Vertrag | Rollenfilter heute verteilt (allowlist, gates, template, teils roh `config["roles"]`) → Drift, stille Gate-Drops | `ActiveSet` einmal je Sync; alle Generatoren konsumieren es; Rohzugriff per Guard-Test verboten | Konsistenz; einmaliger Umbau vieler Generatoren; `full`-Ausgabe ändert sich (Phase 1) |
| ADR-8 Optimizer schlägt vor, Applier beweist | Nutzer-YAML enthält Kommentare; `--fill-defaults` verliert sie; LLM-Edits sind unbeweisbar | Vorschlag als Unified Diff; Anwendung nur über `--apply-config-patch` mit Re-Beweis (IC-25) und Roundtrip-Guard; semantische Kandidaten nur mit Freigabe je ID | beweisbare Verlustfreiheit; zusätzlicher CLI-Befehl; `agent-meta-manager` editiert `project.yaml` dafür nicht direkt |
| ADR-9 Neue Rollen name_only, orchestrator_only, ohne `routing_patterns` | Präzedenz `template-auditor` hat `routing_patterns` trotz name_only → Keyword-Regel, Szenario-76-Widerspruch | beide neuen Rollen ohne `routing_patterns`; Invarianten-Test für alle name_only-Rollen (wirkt nach IC-15 Nr. 14 auch für `template-auditor`) | kein versehentliches Auslösen durch Routine-Aufgaben; Aufruf nur explizit per Name |
| ADR-10 Pipeline-Drop statt Ersatzrolle | Pipelines mit inaktiver Pflicht-Rolle sind heute nicht ausführbar, werden aber gerendert | Pipeline entfällt vollständig (+ INFO); keine implizite Ersatzrolle | keine hängenden Dispatches; Funktionsumfang sichtbar kleiner; Ersatzrollen später explizit per Daten (Q18) |
| ADR-11 Severity-Deckel für UNVERIFIED | Provider-Fakten teils nur aus Drittquellen; falsche ERRORs würden CI blockieren | `verified-state: UNVERIFIED` ⇒ ≤ WARNING; Hochstufung nur mit Evidenz-Update | weniger False-Positive-Blocker; echte Fehler ggf. zunächst nur als WARNING |

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

(Rev. 2) Wirkung des Active-Set-Filters und des Optimizers (gilt in `full`; Schätzungen):

| Artefakt / Größe | Ist | Ziel | Herleitung |
|---|---:|---:|---|
| Orchestrator 10-Rollen-Projekt (Claude, `full`) | 41.1 KB | ≈ 30–34 KB | §2a/§2 nur ausführbare Pipelines (p10: 1 von 7 voll ausführbar; §2a 6.2 KB konstant → anteilig), §4 Tier-Kette ≈ 3.7 KB, `input_contracts` ≈ 0.7 KB |
| `pipeline-details/*.md` 10-Rollen-Projekt | ≈ 8.0 KB | anteilig nur ausführbare Pipelines | IC-18 Nr. 2 |
| Dispatch-Anweisungen an inaktive Rollen | p10 ≈ 38 (Dispatch) / 117 (alle Referenzen) | 0 Dispatch; Erwähnungen gezählt | Invariante §4.4 |
| Gate-gedroppte Allowlist-Rollen gemeldet | 0 | 100 % (WARN) | IC-17 |
| Boilerplate in Agenten (pall) | 50.3 KB | ≈ 5–10 KB (Phase 3, nur bei Q6 positiv; UNVERIFIED) | IC-27 |
| project.yaml (Self-Hosting), L0-Kandidaten | — | YAML kleiner, **injizierte Bytes unverändert** (per Definition) | IC-25 |
| `PROJECT_CONTEXT` (×56, 20.5 KB injiziert) via L2-Relokation | 20.5 KB | ≈ 3–4 KB (Pointer-Satz ≈ 60 B × 56) | Studie §10.3; nur mit Freigabe, eval-gated |
| `EXTRA_DONTS` (×17), `ARCHITECTURE` (×13), `DEV_COMMANDS` (×10) | 3.2 / 2.5 / 0.6 KB (Repo-Werte) | proportional zum Wert; bei 1-KB-Werten 17.5 / 13.6 / 10.5 KB Hebel | Studie §10.3 |

### 11.1 Wo weiter optimieren (Rangliste, Rev. 2)

Priorisiert nach Wirkung × Korrektheitsrisiko; jede Zeile verweist auf den Spec-Ort.

| Rang | Maßnahme | Wirkung (Schätzung) | Spec-Ort | Phase |
|---|---|---|---|---|
| 1 | Pipelines nach Stage-Verfügbarkeit gegen gegatete Aktivmenge filtern; `allowed_agents` filtern | entfernt den Großteil der hängenden Dispatches; bis ≈ 6 KB §2a + 5–8 KB `pipeline-details` in kleinen Projekten | IC-18 Nr. 2–3, IC-15 Nr. 18, ADR-10 | 1 |
| 2 | §4 Tier-Kette/Task-Size-Tabelle auf `DEVELOPER_TIERS_ENABLED` gaten | ≈ 3.7 KB; −25 Tier-Referenzen | IC-18 Nr. 5 | 1 |
| 3 | `input_contracts` auf aktive Producer filtern | ≈ 0.7 KB (p10); weniger Rauschen | IC-18 Nr. 4 | 1 |
| 4 | Interne Orchestrator-Duplikate entfernen (Agent-Tabelle vs. `name_index`; §2a vs. `pipeline-details`) + kaputte Tabellen-Partial reparieren | ≈ 860 B + 94 B je Rolle; §2a ≈ 6 KB in `compact` | C2/IC-05, IC-15 Nr. 11 | 1 (Fix), 2 (Profil) |
| 5 | Dispatch-bezogene statische Sektionen bedingt auf Aktivmenge (`ANTI_RECURSION_BLOCK`, `DIRECT_DISPATCH_SECTION`, Persona, §11-Fallback, SE-Prosa) | Korrektheit; klein in Bytes | IC-18 Nr. 6–8 | 1 |
| 6 | Rollenbewusste Commands und Rules | Korrektheit; Commands nur bei aktiver Zielrolle | IC-18 Nr. 9–10 | 1 |
| 7 | Zentrale Boilerplate-De-Dup | ≈ 50 KB bei 62 Agenten (pro Agent-Aufruf 0.4–1.4 KB) | IC-27 (Phase 3), Q6 | 3 |
| 8 | project.yaml-Fan-out-Hebel (`PROJECT_CONTEXT`, `PROJECT_GOAL`, `EXTRA_DONTS`, `ARCHITECTURE`, `DEV_COMMANDS`; Relokation in `-ext.md`/Doku) | bis ≈ 17 KB je Sync allein `PROJECT_CONTEXT` (Repo-Werte) | IC-24…IC-26 | 2 (Werkzeug), 3 (Relokation) |
| 9 | Reflection-Overrides-Quelle fixen | Korrektheit (`MAX_ITERATIONS`) | IC-15 Nr. 17 | 1 |
| 10 | Projekt-spezifische Rollen implementieren oder Doku korrigieren | Funktion (heute nicht nutzbar) | IC-20, Q16 | 1 |
| 11 | Warnung bei gate-gedroppten Allowlist-Einträgen und übrig gebliebenen `{{VAR}}` | Sichtbarkeit | IC-17, IC-19 | 0 |

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
| Q15 (Rev. 2) | Rollennamen `install-doctor` / `config-optimizer` | **Empfehlung:** annehmen (Begründung IC-23/IC-26); Frontmatter `template-install-doctor` / `template-config-optimizer` gemäß Präfix-Konvention; Nutzerentscheidung vor Phase 0 |
| Q16 (Rev. 2) | Projekt-spezifische Rollen implementieren oder als nicht unterstützt dokumentieren; Quellpfad | **Empfehlung:** implementieren mit provider-neutralem Pfad `.meta-config/agents/<role>.md` + `project-roles:`; Legacy-Pfad lesen mit WARN (IC-20) |
| Q17 (Rev. 2) | Aktivierungsgruppe für die neuen Rollen (z. B. `diagnostics`, Default aus) | **Empfehlung:** keine Gruppe (wie `template-auditor`; kein `_EXPECTED_GROUPS`-Churn); Mehrkosten in Projekten ohne Allowlist ≈ 2 × (≈ 266 B Roster + ≈ 260 B `name_index` + ≈ 94 B Tabelle) ≈ 1.2 KB (Schätzung); Projekte steuern über `roles:` |
| Q18 (Rev. 2) | Pipeline mit inaktiver Pflicht-Rolle: droppen vs. Stage überspringen vs. Ersatzrolle (z. B. `senior-developer` → `developer`) | **Empfehlung:** droppen (ADR-10); optionaler Daten-Key `fallback_role` je Stage in einer späteren Revision, nur mit Eval |
| Q19 (Rev. 2) | „Delegation (reference only)"-Prosa in 34 Templates | **Empfehlung:** Phase 1 nur Zeilen mit Dispatch-Anweisung konditional; Phase 3 datengetrieben (Liste in `role-defaults`, gefiltert gerendert) |
| Q20 (Rev. 2) | Doctor in CI: nur WARN-Report oder `--strict` als Gate | **Empfehlung:** Default ohne `--strict`; `--strict` nur für Matrix-Fixtures in der agent-meta-CI |
| Q21 (Rev. 2) | `toml-key`-Detektor unter Python 3.9 (kein `tomllib`) | **Empfehlung:** Stdlib-Subset-Parser (`[table]`, `key = int|string|bool`); nicht parsebar ⇒ INFO `doctor.detector-unavailable`; Capability-Key für „Provider nutzt TOML-Agentenkonfig" statt Provider-Name |
| Q22 (Rev. 2) | `json-schema`-Detektor ohne `jsonschema` | **Empfehlung:** Subset-Validator (IC-21-Tabelle); kein neues Dependency |
| Q23 (Rev. 2) | `CODE_QUALITY_RULES`: in Template einbinden oder deprecaten | **Empfehlung:** in die Code-Konventionen der Kontextdatei einbinden (Inhalt war vom Nutzer gewollt); bis dahin Doctor-WARN |
| Q24 (Rev. 2) | Kommentar-Zuordnung beim zeilenbasierten Entfernen (eigenständige Kommentarzeilen direkt über einem entfernten Key) | **Empfehlung:** erhalten (konservativ); Nutzer kann sie per semantischem Kandidaten entfernen |
| Q25 (Rev. 2) | `PROJECT_CONTEXT`-Pointer-Hebel automatisch im Profil `compact`? | **Empfehlung:** nein; nur Optimizer-Vorschlag (L2) mit Freigabe + Eval, weil Projektkontext in jedem Agenten Routing-/Qualitätsrelevanz haben kann |
| Q26 (Rev. 2) | Frontmatter-Key `requires_roles` für Commands (Name; Akzeptanz durch `commands.*`-Checks) | **Empfehlung:** `requires_roles` (Liste, optional); `consistency/commands`-Check um den Key erweitern |
| Q27 (Rev. 2) | Read-only-Durchsetzung neuer Rollen auf Providern ohne Tool-/Sandbox-Durchsetzung | **Empfehlung:** Prompt-Ebene + Known-Issue `read-only-not-enforced` (INFO); Codex-Fix IC-15 Nr. 21 |

| # | Risiko | Gegenmaßnahme |
|---|---|---|
| R1 | Prompt-Format-Sensitivität (arXiv 2411.10541) | QG-1, Baseline zuerst, ≥ 2 Modellklassen |
| R2 | Gate-Kompression auf beratenden Providern (Kimi) schwächt Durchsetzung | Gate-Card verbatim, Anker QG-3, Hooks wo verfügbar |
| R3 | Geteilte AGENTS.md-Gruppe: ein Profil für alle | ADR-5, Q12 |
| R4 | Test-Churn (Goldens, Format-Pins) | Tabelle §7; `full` unberührt außer IC-15/11 |
| R5 | Studie mit 62 Rollen; Projekte mit 88 Keyword-Rollen sind größer | Hochrechnung §11 (× 1.47); Budgets je Projekt via Report |
| R6 | Fremdinjektionen (RTK/graphify) in AGENTS.md außerhalb Scope können Caps sprengen | `context.over-hard-cap` misst die ganze Datei |
| R7 (Rev. 2) | Active-Set-Filter ändert `full` breit (Goldens, viele Templates) | ein PR je IC-18-Konsument in Ranglistenfolge; Goldens mit Begründung; `if`-Zweige = unveränderter Text |
| R8 (Rev. 2) | Heuristische Detektoren (Regex) erzeugen False Positives/Negatives | Positiv-/Negativ-Fixtures je Eintrag (QG-10); Severity-Deckel (ADR-11); Allowlists |
| R9 (Rev. 2) | Optimizer-Renderkosten (viele Renders über alle Provider) | ein Sentinel-Render + eine gemeinsame L0-Verifikation; Bisektion nur bei Abweichung |
| R10 (Rev. 2) | Umgehung des Appliers durch direkte LLM-Edits an `project.yaml` | Vertrag in `agent-meta-manager` (IC-27); Doctor-Regel möglich (Hash-Vergleich gegen letzten angewendeten Vorschlag, spätere Revision) |
| R11 (Rev. 2) | Über-Filterung entfernt nützliche Hinweise (z. B. „Rolle X existiert, ist aber nicht aktiv") | Erwähnungen bleiben (INFO); nur Dispatch-Anweisungen werden entfernt |

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
| (Rev. 2) Dangling-Zahlen (117/82/80) | Untergrenze; heuristischer Scanner, nur Provider Claude; Slash-Listen und deutsche Prosa unterzählt |
| (Rev. 2) Ob Claude zur Laufzeit tatsächlich an einen nicht existenten Agenten zu dispatchen versucht | UNVERIFIED (nur statische Analyse) |
| (Rev. 2) Ob Szenario-76-Assert #5 zur Laufzeit fehlschlägt | UNVERIFIED (kein Sync ausgeführt; Regex nimmt das erste `"enum": [`) |
| (Rev. 2) Copilot 4,000 Zeichen und `.instructions.md`-Pflicht | UNVERIFIED (Doku gesperrt) |
| (Rev. 2) Read-only-Durchsetzung auf Kimi, ZCode, Mammouth zur Laufzeit | UNVERIFIED (nur Config gelesen) |
| (Rev. 2) Exakter Key-Name `agent_ext` und Ort der Handoff-Schemas | UNVERIFIED (Planer prüft) |
| (Rev. 2) Ob CI `jsonschema` installiert | nicht in `requirements.txt`, Workflow installiert nur PyYAML — Schluss: Validierung übersprungen (Quelle Studie §10.1, nicht im CI-Log geprüft) |
| (Rev. 2) Variablen-Fan-out auf Providern ≠ Claude; Block-Variablen nach PAL-Transformation | UNVERIFIED |
| (Rev. 2) SE-/Knowledge-aktivierte Varianten des Active-Set-Experiments; Plattformen hacs/sharkord | nicht untersucht |
| (Rev. 2) Wirkung der Boilerplate-De-Dup auf Regelbefolgung | UNVERIFIED (Eval nötig, Q6) |
| (Rev. 2) Ziele §11 (Rev.-2-Tabelle) | Schätzung |

## 14. Revisionen

| Datum | Änderung |
|---|---|
| 2026-10-11 | Erstentwurf (DRAFT) auf Basis der Studie `docs/analysis/2026-10-11-context-budget-provider-study.md` |
| 2026-10-11 | Revision 2 (DRAFT): Nutzeranforderungen R1 (Installations-Doctor), R2 (Active-Set-Filter/dynamisches Routing), R3 (project.yaml-Optimizer) ergänzt — neue Befunde F-19…F-33, Konzept §4.4–§4.6, IC-17…IC-28 (u. a. `ActiveSet`, `known-issues.yaml`, `--doctor`, `install-doctor`, `--optimize-config`/`--apply-config-patch`, `config-optimizer`, Neue-Rolle-Checkliste), IC-15 Nr. 17–21, IC-09 drei Keys, QG-9…QG-13, AC-37…AC-61, ADR-6…ADR-11, Q15…Q27, R7…R11, §11 Rev.-2-Wirkung + Rangliste §11.1, Phasen §9 angepasst (IC-09-Keys nach Phase 0); Korrekturen K-d (Ort `strip_inactive_conditional_blocks`) und K-e („alle Rollen" = 62); Studie §10 (Nachtrag) ergänzt. Bestehende IDs unverändert. |

## Trace-Anker

`spec-id: SPEC-CONTEXT-PROFILES-2026-10-11`
