---
pipeline_stages:
  implement: 1
status: DRAFT
date: 2026-11-14
base-commit: 3dc03f95
trace:
  - agent-improvement-loop
  - issue-1161
  - issue-1244
  - issue-1237
  - issue-1255
---

# Agent-Verbesserungsschleife (alle Rollen) — Analyse und Implementation Plan

> Status: **DRAFT** (2026-11-14). Nur Analyse und Planung — nichts umgesetzt, kein Sync, kein Test, kein Issue, kein PR.
> Basis: `origin/main 3dc03f95`. Zeilenanker veralten; vor Ausführung Freshness-Check.
> Messdaten nicht eingecheckt, reproduzierbar per `python3 scripts/measure_context.py`. Tokens = Bytes/4 (Proxy, **kein tiktoken**), überall so gekennzeichnet.
> Klasse: **L** (99 generische + 18 Plattform-Templates, Sync-Code, Tests, Baselines) → Spec-Pflicht, siehe §9.

## Entscheidungsstand 2026-11-15

Quelle: [Master-Roadmap §4](2026-11-15-master-roadmap.md) (Nutzerentscheidungen 2026-11-15). Plan-Status bleibt DRAFT.

- E-13 (Abweichung): DoD-Preset bleibt rapid-prototyping.
- E-14 (Abweichung): Knowledge Engine bleibt AN.
- E-15 (Abweichung): keine Rules-Kürzung (max_depth bleibt 10, use-lazy-rules bleibt); globales Compact-Profil wird NICHT aktiviert (E-29).
- E-12: Rollenliste (58 -> ~30) ausstehend, wartet auf Nutzerfreigabe; Umfang der Schleife hängt davon ab.
- E-29: Prompt-Sprache Englisch; Issue-Nummern raus; Ziele/Ratsche hart; Claude-Evals nein.
- E-16: Sprach-Matrix wie empfohlen.
- E-10: #1237-Helper-Mini-Spec wird zuerst geschrieben.

**Goal:** Alle Agenten von agent-meta nach einer Rubrik vereinheitlichen, korrigieren, sprachlich normieren und den Kontextverbrauch drastisch senken — gemessen, in Batches, mit Verhaltens-Guardrails; Nebeneffekt: kleinere generierte CLAUDE.md/AGENTS.md.
**Architecture:** Keine neuen Schichten. Hebel in dieser Reihenfolge: (1) Sync-Render (route_intent-JSON, Blöcke, Profile), (2) Template-Rewrite je Rolle nach Rubrik, (3) Lazy-Verlagerung (Skills/Snippets/Extensions), (4) Baselines/Tests. Provider-Unterschiede nur über Capability-Flags.
**Tech Stack:** Python 3.9 (stdlib + PyYAML), Markdown-Templates, pytest, promptfoo (Eval).
**Spec:** `docs/specs/2026-11-XX-agent-improvement-loop-spec.md` — **zu erstellen, Status DRAFT** (§9 enthält den Spec-Kern).

---

## 1. Ist-Analyse: Inventar und Größen

### 1.1 Templates (Quelle)
- 120 Template-Dateien: 101 `agents/1-generic` (99 Rollen + `_README.md` + `_wf-orchestrator-reference.md`), 18 `agents/2-platform`, 1 `agents/0-external/_skill-wrapper.md`.
- Summe **17.973 Zeilen / 874.640 B / ~218,7k Tok**; Median 7.153 B (~1,8k Tok).
- Rangliste Top-10 (B / ~Tok): orchestrator 32.121/8,0k · agent-meta-manager 30.728/7,7k · se-component-requirements 16.645/4,2k · security-auditor 16.438/4,1k · documenter 13.345/3,3k · se-integration-and-test-manager 12.854/3,2k · control-framework-assessor 12.820/3,2k · se-verifier 10.853/2,7k · code-reviewer 10.823/2,7k · homeassistant-documenter (2-platform) 10.464/2,6k.
- Cluster: se-* 14 Dateien 132.884 B (15 % aller Template-Bytes); agent-meta-* 9/59.121; knowledge-* 7/32.665; Provider-Experts 1 Basis + 6 Plattform-Overrides.
- Wiederverwendung existiert: 23 Snippets (20.568 B), 118 Platzhalter, `{{*_BLOCK}}`-Blöcke (WORKER_ROLE 50×, CLOSING_SUMMARY 87×, AUTO_COMMIT 65×, OUTPUT_GUARD 60×, PARSE_INPUT 39×), 10/18 Plattform-Overrides via `extends`+`patches`.

### 1.2 Gerenderte Größen (dieses Repo, 58 aktive Rollen)
| Artefakt | Claude | Opencode | Gemini |
|---|---|---|---|
| Roster gesamt (58 Dateien) | 552.763 B (~138k Tok) | 550.551 | 564.101 |
| orchestrator | 73.403 B (~18,4k) | 73.253 | 73.208 |
| developer | 13.282 (~3,3k) | 13.238 | 13.510 |
| git | 10.176 (~2,5k) | 10.278 | 10.390 |
| tester | 8.060 (~2,0k) | 8.087 | 8.289 |
| code-reviewer | 11.522 (~2,9k) | 11.461 | 11.700 |
| documenter | 15.174 (~3,8k) | 15.179 | 15.380 |

- Orchestrator rendert auf **2,3× Template**. Treiber: `## 3. Intent routing` = **32.834 B** (route_intent-JSON in einer Zeile, 58 Enum-Werte + Regeln + `name_index`; `scripts/lib/agents.py:540`), Few-shot 8.078, Pipeline-stage-detail 7.217, Direkter Dispatch 4.424, Context guard 3.962, Spec/Plan-Dispatch 3.724, Tier selection 3.716. Deckt sich mit #1161 (dort ~11,4k Tok tiktoken für das JSON).
- Compact-Profil (`context-profile: compact`, `agents.py:373,497-512`) rendert den Orchestrator bereits auf **34.792 B** (`tests/test_context_budgets.py:584`) — opt-in, hier nicht aktiv.
- Wiederholte Blöcke im Claude-Roster: Background-Process Guard in 33/58 Dateien = **37.241 B**; Reflection loop 12/58 = 15.658 B; Parse input 13.774 B; Provenance 7.865 B; Escalation Card 6.693 B; Worker-role/A2A je in 44 Dateien.
- 58 `.claude/agents/*.sync-backup-*` (Rauschen im Agent-Verzeichnis; #1161 Pkt 4, Phase H Task 7).

### 1.3 Always-on-Anteil
- Claude: CLAUDE.md 5.358 B + 10 Rules 8.117 B = **13.475 B (~3,4k Tok)**; dazu System-Prompt-Anteile: 58 Agent-Descriptions 5.133 B (~1,3k), 25 Skill-Descriptions 3.568 B (~0,9k), 24 Command-Descriptions 2.141 B (~0,5k) → **~24,3 KB ≈ 6,1k Tok je Nachricht und je Subagent-Spawn**.
- Memory 2026-08-14 (tiktoken): 11,8k Tok bei 22 Rules; Rules seither auf 10 reduziert — Hebel „Rules → Skills“ ist bereits teilweise gezogen. `rules-preset` auf Claude wirkungslos (Memory, gemessen) — kein Hebel.
- Opencode/Gemini: AGENTS.md **16.988 B (~4,2k Tok)**; Sektionen: Agent Directory 5.139, Regeln 4.815 (eingebettet), graphify 1.174, Git Delegation 1.031. Compact-Ziel lt. Test: single ≤ 8 KB, multi ≤ 12 KB, Gemini ≤ 9 KB (`test_context_budgets.py` COMPACT_BUDGET_TARGETS).
- Ceilings (`test_context_budgets.py:301-309`, full): Claude orchestrator 72.183, rules 18.208, always-loaded 705.665 (= entry + rules + Roster-Summe; Roster zählt als „Schätzung“, `context_report.py:146-147` — für Claude überschätzt, da nur Descriptions always-on sind). Ceilings sind eingefrorene Ist-Werte + 2 % Toleranz, **keine Ratsche nach unten** (#1237).

## 2. Ist-Analyse: Qualität und Konsistenz

- **Frontmatter:** name/version/description/hint/tools in allen 99 Rollen; `prompt_mode: modern` nur in 77 (22 fehlen → implizites Default?), `reference_standards` in 51 (8.832 B, landet im Render? — unverifiziert). Descriptions Ø 206 Zeichen (max 469) → System-Prompt-Kosten; Ziel ≤ 160.
- **Sektionsstruktur:** 580 verschiedene H2-Überschriften in 99 Rollen — kein Schema. Gleiche Konzepte unter verschiedenen Namen: `Project context` 14 / `Projektkontext` 9, `Language` 10 / `Sprache` 10, `Output schema|Output contract|JSON Output Schema|Return|Output` 5 Varianten, `Step Persistence` 2 Varianten, `A2A Handoff` 3 Varianten.
- **Boilerplate:** Dubletten auf Zeilenebene gering (4 Muster, 4.404 B) weil Blöcke zentral sind — aber die Blöcke selbst sind groß und werden in jeden Worker gerendert (§1.2). Orchestrator-Template trägt eigene Kopien (Singleton-Regel 1.364 B zusätzlich zu `use-orchestrator.md`).
- **Widersprüche/Veraltetes (Stichproben, nicht vollständig):** 74 „Issue #N“-Nennungen (20 Nummern) in Prompts — Provenienz für Menschen, Rauschen fürs Modell; Persona-Opener 89× „You are the“ vs 11× „Du bist der“; `## Sprache` in 20 Rollen, in 79 fehlt eine Sprachsektion ganz (Verhalten uneinheitlich). 5 von 39 repo-relativen Pfadreferenzen im Repo nicht vorhanden (`config/auto-commit-allowlist.json`, `config/env.sh`, `config/project.yaml`, `docs/ARCHITECTURE.md`, `docs/conclusions/…`) — vermutlich zielprojekt-relativ, einzeln zu prüfen.
- **Provider-Literale in 1-generic:** 14 Dateien (se-termination 13, agent-meta-manager 5, agent-meta-scout 4, release 3) — Gegenstand von #1255 (strip-claude-lines kaschiert).
- **Tool-Minimalprinzip:** Ø 4,3 Tools; 27 Rollen ≥ 7; Max 9 (senior-/principal-developer, agent-meta-manager). Review-Rollen mit Write/Edit (code-reviewer, validator, app-lifecycle-governor — „read-only“ laut Description, aber Write/Edit in tools).
- **Instruction-Bleed:** nur Checkliste (`.claude/skills/conventions/SKILL.md:27-38`), kein Test. 10 Plattform-Overrides mit `patches` (4× auf developer) sind das Risiko-Fenster.
- **Drift/Rebaseline-Aufwand:** 5 Mechanismen (generated-file-hashes, context-hashes, external_tools_drift, standalone, AC-01+golden+ceilings) — `generated-file-hashes.json` 95 Commits/90 Tage, ac01-baseline 62, compact-golden 17 (#1237). Golden-Fixtures 79 Dateien / 1,2 MB. **Jede Template-Änderung = bis zu 4 Rebaseline-Orte** → ohne #1237 ist eine Schleife über 99 Rollen prozessual teuer (≈ 1 Rebaseline-Commit je PR, Pflicht).

## 3. Ist-Analyse: Sprache

- Regelwerk (`CLAUDE.md` Sprachregeln, `.claude/rules/language.md`): README EN, übrige Doku DE, Code/Commits EN, Nutzerkommunikation DE. **Agent-Prompts sind nicht geregelt.**
- Ist: 86 Rollen EN-dominant, 11 DE-dominant (6 knowledge-*, se-architect, se-component-requirements, se-critic, se-integration-and-test-manager, template-auditor), 4 gemischt (ideation, knowledge-indexer, mammouth-expert, se-requirements). DE+gemischt = 105.777 B (~26,4k Tok). Überschriften gemischt auch in EN-Rollen (orchestrator: „Direkter Dispatch“, „Singleton-Regel“, „Status-Tabelle“).
- Empfehlung: **Prompt-Sprache Englisch, knapp, imperativ**; Nutzer-/Doku-Sprache ausschließlich über vorhandene Platzhalter (`{{COMMUNICATION_LANGUAGE}}` 18×, `{{INTERNAL_DOCS_LANGUAGE}}` 41×, `{{DOCS_LANGUAGE}}` 14×, `{{CODE_LANGUAGE}}` 39×). Begründung: Modelle folgen englischen Instruktionen am robustesten; deutscher Text kostet beim selben Inhalt **schätzungsweise 20–40 % mehr Tokens** (ESTIMATE, tokenizer-abhängig, hier nicht gemessen — Messung in Task 1.2). Kosten je Token providerabhängig, nicht verifiziert.
- Konfliktfreiheit: `speech-mode.md` und `language.md` regeln Ausgabe an den Nutzer, nicht die Prompt-Sprache → kein Konflikt; eine Zeile in `language.md` („Agent-Prompts: Englisch“) schließt die Lücke. Phase H Block D (#779/#780 Routing-Sprache, DE/EN-Keywords) bleibt dort.
- Migrationsaufwand: 15 Templates übersetzen/kürzen (~26k Tok Quelle), Einheiten in den Batches 5 und 6 (§6.3); Golden/AC-01 der SE-/Knowledge-Rollen rebaselinen.

## 4. Best-in-class-Rubrik (Soll je Rolle)

| # | Kriterium | Prüfbar durch |
|---|---|---|
| R1 | Zweck + Trigger in ≤ 2 Sätzen; `description` ≤ 160 Zeichen, enthält „when to use“ und Abgrenzung | Lint (Länge), Review |
| R2 | Grenzen: „Does not …“-Liste (max 5), Eskalationsziel genannt | Lint (Sektion vorhanden) |
| R3 | Tool-Minimalprinzip: nur Tools, die im Workflow vorkommen; Read-only-Rollen ohne Write/Edit | Test: Tool ↔ Workflow-Erwähnung |
| R4 | Ausgabeformat: genau 1 Output-Contract-Sektion (Standardname), Schema als Tabelle/JSON ≤ 25 Zeilen | Lint (Sektionsname) |
| R5 | Anti-Patterns: `Don'ts` ≤ 7 Punkte, keine Begründungsprosa | Lint (Punktzahl) |
| R6 | Progressive Disclosure: Kerntext ≤ 1,5k Tok Render (Worker) / ≤ 7k (orchestrator); Details in Skills/Snippets/Extensions, referenziert | Budget-Test je Rolle |
| R7 | Wiederverwendung statt Kopie: Blöcke nur per Platzhalter; keine Zeile ≥ 80 Zeichen in ≥ 3 Rollen | Dubletten-Test |
| R8 | Bedingte Sektionen per Capability-Flag/`{{#if}}`, keine Provider-Literale | `test_provider_agnostic_dispatch.py`, Literal-Test |
| R9 | Kompaktform: Tabellen/Listen statt Prosa; keine Issue-Nummern im Prompt (Provenienz → Kommentar `<!-- -->` oder CHANGELOG) | Lint (`Issue #`-Regex) |
| R10 | Prompt-Caching-freundlich: stabiler Präfix (Frontmatter, Persona, Blöcke) vor variablen Teilen (Projektkontext, Datum) | Render-Reihenfolge-Test |
| R11 | Sprache: Prompt EN; Sprach-Platzhalter für Nutzer/Doku; einheitliche Standard-Sektionsnamen (Schema §9.2) | Lint (DE-Markerquote < 5 %) |
| R12 | Eval: je Rolle ≥ 1 Verhaltens-Case in `tests/routing-llm-eval/catalog.behavior.yaml` | Katalog-Hygiene-Test (existiert) |

## 5. Hebel und Einsparpotenzial (Schätzung, Bytes/4)

| Hebel | Ist | Ziel | Einsparung | Art |
|---|---|---|---|---|
| H1 route_intent-JSON kompakt (Namensliste + Signal-Keywords statt Volltext-Enum/Descriptions/`name_index`), für alle Provider ohne `route_intent`-Tool | 32.834 B | ≤ 8 KB | ~25 KB / ~6k Tok je Orchestrator-Spawn | Sync-Code (#1161 Pkt 2, Phase H Task 8) |
| H2 Orchestrator-Template: Few-shot auf 3 Beispiele, Pipeline-stage-detail als Tabelle, Singleton/Direkter Dispatch auf Rule verweisen | 40,5 KB Rest | ≤ 20 KB | ~20 KB / ~5k Tok | Template |
| H3 Worker-Blöcke kürzen: BG-Guard 1.884 → ≤ 500 B, Parse input 2.395 → ≤ 900, Reflection loop, Provenance, Escalation Card je −50 % | ~81 KB im Roster | ~35 KB | ~46 KB Roster; je Worker-Spawn ~1–1,5k Tok | Snippets |
| H4 Rollen-Rewrite nach Rubrik (Prosa → Tabellen, Don'ts kürzen, Issue-Nummern raus, Sprach-Normierung) | 874 KB Templates | −30 % | ~260 KB Templates / ~65k Tok; Roster ~−150 KB | Template, batchweise |
| H5 Descriptions ≤ 160 Zeichen | 5.133 B (58) | ≤ 4 KB | ~0,3k Tok always-on je Nachricht | Template |
| H6 AGENTS.md: Agent Directory als Einzeiler je Rolle, Regeln nur Pointer | 16.988 B | ≤ 12 KB (Compact-Target) | ~1,2k Tok always-on (Opencode/Gemini) | templates/context (Phase H/#1244) |
| H7 Backups aus `.claude/agents` prunen | 58 Dateien | 0 | Verzeichnis-Rauschen | Phase H Task 7 |

- Gesamtziel: **Roster −45 % (553 KB → ≤ 300 KB), Orchestrator-Render −60 % (73 KB → ≤ 28 KB), Ø Worker-Render −35 %, Always-on Claude −20 % (24,3 KB → ≤ 19,5 KB), AGENTS.md ≤ 12 KB.** Begründung der Zielwerte: H1–H3 sind mechanisch (gemessene Blockgrößen); H4 ist konservativ gegen Literatur (Prosa→Tabelle typ. 30–50 %), untere Grenze gewählt; Compact-Profil beweist 34,8 KB für den Orchestrator bereits heute.
- Nullkosten-Sofortmaßnahme (Entscheidung E1): `context-profile: compact` im Zielprojekt aktivieren → Orchestrator 73 → ~35 KB ohne Codeänderung.

## 6. Schleifen-Design

### 6.1 Zyklus je Batch
1. **Messen:** `python3 scripts/measure_context.py` + neuer Report `--per-agent --provider <P>` (Task 1.1) → Tabelle Rolle × Provider (Bytes, ~Tok), Baseline-Datei .tmp/plans/scratch/baseline-<batch>.json.
2. **Ranken:** Sortierung nach Render-Bytes × Spawn-Häufigkeit (orchestrator, developer-Tier, git, tester, code-reviewer, documenter zuerst).
3. **Rewrite:** je Rolle nach Rubrik §4 durch `prompt-engineer` (Entwurf) → `developer` (Template/Snippet/Sync) ; Blöcke zuerst, dann Rollen.
4. **Verifikation:** `tests/test_context_budgets.py` (Ceilings, neu: Zielwerte als Ratsche), `test_provider_agnostic_dispatch.py` + Literal-Test, Lint §4 (Task 1.3), `tests/routing-llm-eval` Smoke (lokal, Opencode-Provider, kostenfrei) — **kostenpflichtige Claude-Evals nur nach Kosten-Gate E5**.
5. **Rebaseline:** ein Commit je PR (AC-01, Golden, Ceilings, generated-file-hashes) — bis #1237 den Helper liefert (Phase H Task 6 Re-Pin-Helper #1115 nutzen).
6. **Report:** Vorher/Nachher je Rolle in .tmp/plans/scratch/loop-report.md + PR-Beschreibung; Prozentziel je Rolle ≥ 25 %, sonst Begründung.

### 6.2 Guardrails
- A/B-Eval: Verhaltens-Cases je Batch vor/nach (Opencode lokal; Claude nur mit E5). Abbruch des Batches bei Regression > 1 Case.
- Review-Pflicht: `prompt-engineer` reviewt jeden Rewrite (Rubrik-Checkliste), `code-reviewer` den Sync-Code.
- Rollback: ein PR je Batch, Revert = `git revert <merge>` + Rebaseline-Commit; Golden-Fixtures machen jeden Revert deterministisch.
- Keine Semantikänderung ohne Begründungszeile in der PR („behaviour-preserving“ vs. „intended change“).

### 6.3 Takt / PR-Schnitt (Batch = 4–6 Rollen, je 1 PR)
| Batch | Inhalt | Aufwand |
|---|---|---|
| 0 | Mess-CLI, Lint, Ratschen-Test, Sektions-Schema (Infrastruktur) | M |
| 1 | Sync: route_intent kompakt (H1), Block-Kürzung (H3), Descriptions-Lint (H5) | M |
| 2 | orchestrator, developer, junior-developer, senior-developer, principal-developer | L |
| 3 | git, tester, test-executor, code-reviewer, validator, documenter | M |
| 4 | planner, requirements, concept-architect, concept-specifier, concept-reviewer, ideation | M |
| 5 | se-* (14; DE→EN) in 3 PRs | L |
| 6 | knowledge-* (7; DE→EN), template-auditor | M |
| 7 | security-/ai-/audit-Cluster (security-auditor, control-framework-assessor, red-team-agent, secrets-manager, ai-*) | M |
| 8 | agent-meta-manager, agent-meta-scout, meta-doctor, provider-expert + 6 Plattform-Overrides, release, feedback | M |
| 9 | Rest 1-generic (ca. 35 Rollen in 6–7 PRs) | L |
| 10 | 2-platform (hacs/homeassistant/sharkord) + 0-external, AGENTS.md/CLAUDE.md-Templates (H6) | M |
| 11 | Abschluss: Ratschen-Ziele verschärfen, Doku, Memory-Notiz | S |

## 7. Überschneidungen (integrieren, nicht doppelt planen)
- **#1161 / Phase H Block C** (`docs/superpowers/plans/2026-11-11-phase-h-context-eval.md:241-280`): route_intent-JSON (Pkt 2, Mini-Spec Task 8), Backups (Task 7), branch-guard-Detail. → H1 und H7 werden **dort** umgesetzt; dieser Plan setzt sie als Vorbedingung von Batch 2 voraus und liefert nur die Messung/Zielwerte.
- **Phase H Block A** (#969 Eval-Gate McNemar, Task 1–5): Verhaltens-A/B dieses Plans nutzt dessen Per-Testfall-Schnittstelle; bis dahin nur Smoke.
- **Phase H Block D** (#779/#780 Routing-Sprache): Sprach-Normierung der Routing-Keywords bleibt dort; §3 hier betrifft nur Prompt-Prosa.
- **#1244** (Session-Ceiling, Roster-Reduktion): Task 1.1/1.4 liefern die Token-Summe je Session als Test; Roster-Verkleinerung (aktive Rollen) ist Entscheidung E3.
- **#1237** (Rebaseline vereinheitlichen): harte Abhängigkeit für den Takt — ohne Helper +1 Rebaseline-Commit je PR, akzeptiert (E4).
- **#1255** (strip-claude-lines → agnostische Templates): Literal-Bereinigung der 14 Dateien gehört in die jeweiligen Batches; der Strip-Abbau selbst bleibt #1255/Phase G.
- **Phase E (#1186-Kette)**: Pfad-Literale in Templates werden durch Artifact-Locations-Variablen ersetzt — Rewrite-Batches dürfen keine neuen Pfad-Literale einführen; Rollen mit Pfadausgaben (reviews/audits) erst nach Phase-E-Merge oder mit Platzhalter-Vorgriff.
- **Phase D** (#1210 Sentinel-Rollenbindung, #1181 Commit-Authority): Commit-Authority-Blocktexte nicht in Batches anfassen, bis D gemergt.
- `docs/plans/2026-11-14-bugfix-batch-3-plan.md` und `…-audit-top5-execution-plan.md`: keine Überschneidung (Laufzeit-Bugs bzw. Audits; nur Reihenfolge: Bugfix-Batch 3 vor Batch 0, weil TMPDIR-Determinismus die Rebaseline berührt).

## 8. Global Constraints
- Nur über `orchestrator`; Feature-Branches `chore/agent-loop-batch-<n>`; Merge nur durch den Nutzer.
- Provider-Unterschiede nur per Capability-Flag; keine `if provider == …`.
- Jede Template-Änderung: Version-Bump (Skill `conventions`), Rebaseline in **einem** eigenen Commit je PR.
- Kein Worktree-Isolation; Schreiben nur im Repo + .tmp/.
- Kostenpflichtige Eval-Läufe: nur nach Kostenschätzung + explizitem Ja (E5).

## 9. Spec-Kern (für die zu erstellende Spec, Status DRAFT)

### 9.1 Scope / Non-Goals
- In Scope: 99 generische Rollen, 18 Plattform-Overrides, Snippets/Blöcke, Render-Pfad route_intent, Mess-/Lint-Tests, `templates/context/*`.
- Nicht in Scope: Rollen entfernen (E3 separat), Hooks, Admin-UI, Pipeline-Semantik, Provider-Mechanismen (#1255/Phase G).

### 9.2 Standard-Sektionsschema (Worker; Reihenfolge = Cache-Präfix stabil → variabel)
`frontmatter` → `> Extension` → `<persona>` (Purpose, Boundaries, Does-not) → `<workflow>` (Parse input, Steps, Output contract) → `<rules>` (Don'ts, Escalation) → `<context>` (Project context, Language) → Blöcke (Closing summary, Auto-commit, Output guard).
Kanonische Namen (EN): `Purpose`, `Boundaries`, `Parse input`, `Workflow`, `Output contract`, `Don'ts`, `Escalation`, `Project context`, `Language`. Alte Namen (`Sprache`, `Projektkontext`, `Return`, `JSON Output Schema` …) werden migriert; `patches`-Anker in 2-platform entsprechend angepasst.

### 9.3 Akzeptanzkriterien (Spec-Level)
- AC-L1: Mess-Report je Rolle × Provider existiert als CLI und Test; Summen je Session (always-on + Spawn) in Bytes und ~Tok.
- AC-L2: Ratschen-Test: kein Artefakt wächst; Zielwerte §5 als `xfail(strict)` bis erreicht, dann hart.
- AC-L3: Lint R1/R2/R4/R5/R9/R11 grün für alle 99 Rollen.
- AC-L4: Kein Provider-Literal in 1-generic außerhalb der Allowlist von `provider_literals.py`.
- AC-L5: Verhaltens-Eval: je Batch keine Regression (Smoke lokal; McNemar mit Phase H Block A).
- AC-L6: AC-01-Render-Identität und Golden nach jedem Batch rebaselined; `--validate` grün.

## 10. File Structure
- Create: `docs/specs/2026-11-XX-agent-improvement-loop-spec.md` — Spec (§9).
- Create: `scripts/lib/agent_report.py` — Per-Rolle/Provider-Messung (nutzt `context_report.measure_artifacts`, `count_text_stats`).
- Modify: `scripts/measure_context.py` — Flag `--per-agent` (Tabelle + JSON).
- Create: `tests/test_agent_budget_ratchet.py` — Ratsche je Rolle × Provider, Zielwerte §5.
- Create: `tests/test_template_rubric_lint.py` — R1/R2/R4/R5/R9/R11.
- Modify: `tests/test_context_budgets.py` — Re-Pins je Batch (über Phase-H-Helper #1115).
- Modify: `scripts/lib/agents.py:373-545` — kompakte Routing-Zeilen für alle Provider ohne `route_intent`-Tool (**nur falls Phase H Task 8 es nicht liefert**).
- Modify: `snippets/agents/*.md` (background-process-guard, parse-input, escalate-card, closing-summary, output-guard) — Kürzung.
- Modify: `agents/1-generic/*.md` (99) + `agents/2-platform/*.md` (18) — batchweise.
- Modify: `templates/context/agents-managed.md`, `partials/agents-table.md`, `partials/rules-embedded.md` — AGENTS.md-Kompaktierung.
- Modify: `.claude/rules/language.md` (Quelle: `templates/…` bzw. `config/`, Pfad bei Ausführung verifizieren) — Zeile „Agent-Prompts: Englisch“.
- Modify: `docs/guides/features/agent-composition.md`, `.claude/skills/conventions/SKILL.md` — Sektionsschema, Rubrik.
- Modify: `tests/fixtures/{compact,slimming,topology}-golden/**`, `tests/fixtures/ac01-baseline/hashes.json`, `.meta-config/generated-file-hashes.json`, `.meta-config/context-hashes.json` — Rebaseline je Batch.

## 11. Tasks

### Batch 0 — Infrastruktur (M)
**Task 0.1 Spec schreiben + Freigabe-Gate** — Files: Create Spec. AC: Status DRAFT → Review durch `concept-reviewer` → User-APPROVED, bevor Batch 1 startet.
**Task 1.1 Mess-CLI je Rolle × Provider** — Files: Create `scripts/lib/agent_report.py`, Modify `scripts/measure_context.py`, Create `tests/test_agent_report.py`. Steps: Test (fail) für JSON-Shape `{provider:{role:{bytes,lines,tokens_approx}}}` → implementieren → Test (pass) → commit. AC: Lauf gegen `.claude/agents` liefert 58 Zeilen, Summenzeile, Session-Summe (entry + rules + descriptions).
**Task 1.2 Tokenizer-Stichprobe (optional, lokal)** — Files: Create .tmp/plans/scratch/tokenizer-probe.md. AC: Bytes/4 vs. echter Tokenizer für 5 Rollen (EN) + 3 Rollen (DE) dokumentiert; Faktor DE/EN belegt oder als ESTIMATE belassen. Kein Netz/keine Kosten; nur wenn `tiktoken` lokal verfügbar.
**Task 1.3 Rubrik-Lint** — Files: Create `tests/test_template_rubric_lint.py`. AC: prüft R1 (description ≤ 160), R2 (Boundaries-Sektion), R4 (genau 1 Output-Sektion kanonisch), R5 (Don'ts ≤ 7), R9 (kein `Issue #\d+` im Body), R11 (DE-Markerquote); startet als `xfail(strict=False)` je Rolle mit Allowlist, wird je Batch verschärft.
**Task 1.4 Ratschen-Test** — Files: Create `tests/test_agent_budget_ratchet.py`. AC: liest Baseline-JSON, failt bei Wachstum > 1 %, Zielwerte §5 als `xfail(strict)`; Session-Summe-Ceiling (deckt #1244 Pkt 1).
**Task 1.5 Sektionsschema dokumentieren** — Files: Modify `docs/guides/features/agent-composition.md`, `conventions`-Skill. AC: kanonische Namen §9.2, Migrationsliste alt→neu, Hinweis auf `patches`-Anker.

### Batch 1 — Sync/Blöcke (M)
**Task 2.1 route_intent kompakt** — Gate: Phase H Task 8 (Mini-Spec #1161 Pkt 2). Wenn dort umgesetzt → nur Messung. Sonst: Modify `scripts/lib/agents.py` — Name + ≤ 5 Signal-Keywords je Rolle, kein `name_index`, keine Description-Dubletten; Capability-gesteuert. AC: Claude-Orchestrator ≤ 40 KB; AC-01 für Provider mit `route_intent`-Tool unverändert.
**Task 2.2 Block-Kürzung** — Files: Modify 5 Snippets. AC: BG-Guard ≤ 500 B, Parse input ≤ 900 B, Escalation Card ≤ 1.200 B, Closing summary ≤ 300 B; Semantik erhalten (Review `prompt-engineer`); Golden rebaselined.
**Task 2.3 Descriptions ≤ 160** — Files: 1-generic Frontmatter (nur `description`). AC: Lint R1 grün; Routing-Eval-Katalog (`gen_role_routing_eval_catalog.py`) regeneriert, Smoke grün.

### Batch 2–10 — Rollen-Rewrite (Schema je Batch, 4–6 Rollen)
**Task n.1 Baseline messen** (Task 1.1) → .tmp/plans/scratch/baseline-batch-<n>.json.
**Task n.2 Rewrite je Rolle** — `prompt-engineer` Entwurf nach §4/§9.2, `developer` übernimmt; Version-Bump; DE→EN wo nötig; Issue-Nummern in `<!-- provenance -->`-Kommentar; Tools auf Workflow-Nutzung reduziert (R3).
**Task n.3 Plattform-Overrides** — `patches`-Anker nachziehen; Instruction-Bleed-Checkliste abhaken; Render-Diff lesen.
**Task n.4 Verifikation** — `--validate`, Budgets/Ratsche, Lint, Literal-Test, Eval-Smoke (lokal). AC: je Rolle ≥ 25 % Render-Reduktion oder Begründung; keine Eval-Regression.
**Task n.5 Rebaseline + Report** — ein Commit; Vorher/Nachher in PR.

### Batch 11 — Abschluss (S)
**Task 12.1** Zielwerte §5 hart machen (`xfail` entfernen). **Task 12.2** Memory-/Doku-Notiz; `AGENTS.md`/`CLAUDE.md`-Beispiel im README aktualisieren (EN).

## 12. Entscheidungspunkte (einzeln, mit Empfehlung)
- **E1 Compact-Profil sofort für dieses Repo aktivieren?** Empfehlung: **Ja** (Orchestrator 73 → ~35 KB, null Code; Phase-2-Status lt. `2026-10-18-context-profiles-phase2-status.md` nicht evaluiert, daher Smoke nach Aktivierung).
- **E2 Prompt-Sprache Englisch für alle Rollen (15 Templates übersetzen)?** Empfehlung: **Ja**; Nutzer-/Doku-Sprache bleibt über Platzhalter Deutsch.
- **E3 Aktive Rollen im Repo reduzieren (58 → ~30, Memory-Hebel „50→12“)?** Empfehlung: **Separat entscheiden** (nicht Teil der Schleife; betrifft `roles:` in `.meta-config/project.yaml:91`, Routing-Katalog).
- **E4 Takt ohne #1237-Helper starten (+1 Rebaseline-Commit je PR)?** Empfehlung: **Ja**, Phase-H-Task 6 (Re-Pin-Helper) als Mindest-Vorbedingung.
- **E5 Kosten-Gate Claude-Evals:** Verhaltens-A/B gegen Claude-API nur nach Kostenschätzung (Cases × Rollen × 2 Varianten × Ø Prompt-Tok) und explizitem Ja; Default: **Nein**, nur lokaler Opencode-Smoke.
- **E6 Issue-Nummern aus Prompts entfernen (Provenienz nur noch als HTML-Kommentar)?** Empfehlung: **Ja** (R9).
- **E7 Zielwerte §5 verbindlich (Ratsche hart in Batch 11)?** Empfehlung: **Ja**, mit Toleranz 1 %.
- **E8 Reihenfolge: Bugfix-Batch 3 (TMPDIR-Determinismus) vor Batch 0?** Empfehlung: **Ja**.

## 13. Risiken
- Verhaltensdrift durch Kürzung (Blöcke tragen Guard-Semantik) → Review-Pflicht, Eval-Smoke, Revert je Batch.
- Rebaseline-Lawine (4 Orte/PR) → ein Commit, Helper aus Phase H; Konflikte mit parallelen Phase-D/E-PRs → Batch-Reihenfolge §7.
- `patches`-Anker brechen beim Umbenennen von Sektionen → Task n.3, `--validate`, Golden.
- Bytes/4 unterschätzt DE-Text und JSON → Task 1.2 kalibriert; Zielwerte in Bytes formuliert.
- Prompt-Caching-Vorteil nicht messbar ohne Provider-Telemetrie → als Designprinzip (R10), nicht als Metrik.
- Routing-Qualität sinkt durch kürzere Descriptions → Routing-Eval-Katalog je Batch regenerieren und laufen lassen (lokal).

## 14. Rollback
- Je Batch ein Merge-Commit → `git revert -m 1 <merge>` + ein Rebaseline-Commit; Golden/AC-01 garantieren Byte-Identität zum Vorzustand.
- Compact-Profil (E1) per Config-Key zurücknehmbar.

## 15. Aufwand
- Batch 0: M · Batch 1: M · Batch 2: L · Batch 3–4: M · Batch 5: L · Batch 6–8: M · Batch 9: L · Batch 10: M · Batch 11: S. Gesamt: **L/XL**, ~20 PRs.

## 16. Nicht verifiziert / Lücken
- Tokens überall Bytes/4; tiktoken-Werte nur aus Memory 2026-08 (veraltet) und #1161.
- Ob `reference_standards` und `hint` in den Render/System-Prompt gelangen — nicht geprüft.
- „Tote“ Pfadreferenzen (5) nicht einzeln gegen Zielprojekt-Semantik geprüft.
- Widersprüche zwischen Rollen nur stichprobenhaft (Headings/Opener/Tools), kein vollständiger Semantik-Abgleich.
- Prompt-Caching-Verhalten der Provider nicht gemessen.
- Phase-H-Plan ist DRAFT; Task-Nummern dort können sich ändern.

## Self-Review
- Header, Status DRAFT, File-Structure-Map, Tasks mit AC, Risiken, Rollback, Aufwand, Entscheidungen einzeln, Kosten-Gate, Spec-Abschnitt: vorhanden.
- Keine Platzhalter außer Spec-Datum (`XX`, absichtlich bis Erstellung).
