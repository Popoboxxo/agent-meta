---
spec-id: SPEC-INTENT-ROUTING-TABLE-2026-11-14
title: Intent-Routing-Tabelle — Spec (Roadmap PR 0.6 / P25)
status: APPROVED
approved: 2026-11-20
approval-basis: "Nutzergo 20.11. — E-07/E-31 Einzel-Spec-Freigaben erteilt; Spec schreiben und Status APPROVED setzen, keine neuen Entscheidungen erfinden"
revision: "1 — Ausgliederung von Plan §4 nach docs/specs/"
klasse: "M — Doku/Audit, kein Render-Delta, kein Rebaseline"
datum: 2026-11-20
issues: "#1161 #779 (#1243 Ref)"
plan: docs/plans/2026-11-14-intent-routing-table-plan.md
roadmap: docs/plans/2026-11-15-master-roadmap.md
branch: docs/intent-routing-spec
---

# Intent-Routing-Tabelle — Spec (Roadmap PR 0.6 / P25)

> Status: APPROVED (Nutzergo 2026-11-20, E-07)
> Freigabe: Nutzergo 20.11. — „Freigaben, die nur ein Ja erfordern (E-07/E-31 Einzel-Specs, 5.2 fehlende Spec, §3.8 Rebaseline-Bündelung), gelten hiermit als erteilt: Specs schreiben/Status APPROVED setzen mit Verweis auf Nutzergo 20.11., keine neuen Entscheidungen erfinden.“
> spec-id: `SPEC-INTENT-ROUTING-TABLE-2026-11-14` (vom Plan §4 vorläufig vergeben; Ausgliederung am 2026-11-20)
> Klasse: **M / Doku-Audit** — kein Render-Delta, keine generierten Dateien, kein Rebaseline (Roadmap §3.1 PR 0.6: „RB keiner“)
> Autor: `developer` (Subagent, Auftrag Roadmap PR 0.6 / P25)

Diese Spec ist die Ausgliederung des Spec-Kerns aus `docs/plans/2026-11-14-intent-routing-table-plan.md` §4
(gemäß Plan Zeile 36 und §8, PR 1) und die Freigabegrundlage für Roadmap PR 4.1
(`feat/intent-routing-model`, P26). Sie enthält **keinen Implementierungscode** und **keine neuen
Entscheidungen**: alle Zielwerte, Verträge, Codes und Zahlen stammen aus den beiden referenzierten
freigegebenen Dokumenten (siehe §7 Traceability).

## 1. Scope und Abgrenzung

### 1.1 Umfang dieses PR (Block A)

- Spec-Ausgliederung: Plan §4 → dieses Dokument, mit IC-/AC-Nummern (Plan Task 1).
- Messmethodik: tiktoken-Kalibrierung und Bytes/4-Baseline (Plan Task 0, Roadmap §2.3 W2).
- Informative Intent-Taxonomie: die 16 Intent-Keys aus Plan §4.2, E-07/E3 entsprechend **informativ**
  (Plan Task 2, Roadmap §4 E-07).
- Ausschließlich diese Markdown-Datei. **Docs-only**: kein Produktivcode, keine Templates, keine
  Config, keine generierten Dateien, kein Sync, kein Rebaseline. Es gibt daher **keine
  TDD-Code-Änderungen** und keine neuen Test-Fixtures; verifiziert wird die Ableitung per Review
  und `git diff` (eine Datei).

### 1.2 Nicht in diesem PR

- Umsetzung des Datenmodells, Renderers, Direct-Dispatch, Detaildatei und der Rebaseline: PR 2
  (P26 / Roadmap 4.1, E-23). Dessen Gate ist „Spec 0.6 APPROVED“ (Roadmap §3.5).
- Admin-UI und Eval: PR 3 (P27 / Roadmap 5.4, E-27).
- Die nicht-routing-bezogenen Nicht-Ziele aus Plan §12 (Prompt-Rewrite, globales Compact-Profil,
  `route_intent`-Tool-Registrierung, Pipeline-/Reviewer-Semantik, Hooks, #1176/#1168/#1244/#1243).
- Die vollständige Zuordnung aller 88 keyword-adressierbaren Rollen zu Intents (Plan Task 2) ist
  ein offenes Deliverable des Entwurfs und wird hier nicht erfunden (siehe §4.3).

## 2. Zielbild (aus Plan §4.1, unverändert)

1. **Eine Routing-Quelle, ein Resolver:** `role-defaults.yaml` (Framework-Default) + `project.yaml →
   routing-overrides` (Projekt) werden von `delegation_table.resolve_routing_model()` zu **einem**
   Routing-Modell gemergt; daraus werden alle Artefakte (A/B/C, Direct-Dispatch, Eval-Katalog)
   gerendert.
2. **Zwei Render-Formen, capability-gated:** kompakte Always-on-Tabelle (Zeilenformat, ≤ 8 KB bei
   57 Rollen) und Lazy-Detaildatei (Contracts, alle Beispiele, Priorität, Größenklasse);
   JSON-Tool-Definition nur bei `route_intent_tool: true` (heute kein Provider).
3. **Intent-Taxonomie statt Keyword-Suppe:** je Rolle `intents[]` aus fester Taxonomie
   (`config/routing/intents.yaml`), Trigger ≤ 6, `size_class`, `direct_dispatch`, `visibility`;
   Lint erzwingt Eindeutigkeit (Überlappung nur mit `priority`).
4. **Konfigurierbar an drei Stellen:** Preset (Framework), `project.yaml`
   (`routing-overrides`, schema-validiert), Admin-UI (Editor mit Lint, Live-Preview, Tokenzahl,
   Reset-auf-Default); alles im selben Override-Block.
5. **Messbar:** Routing-Eval-Set (`intent → erwartete Rolle/Pipeline`), generiert aus dem
   Routing-Modell plus manuelle Mehrdeutigkeitsfälle; LLM-Läufe nur nach Kostenschätzung und Ja.

## 3. Interface-Vertrag der Routing-Tabelle (Trigger/Example → Zielagent)

### 3.1 Datenmodell (Plan §4.2)

`config/role-defaults.yaml → roles.<role>.routing` (alte Keys bleiben, Migration mechanisch):

| Key | Vertrag |
|---|---|
| `addressability` | `keyword` / `name_only` / `excluded` (unverändert) |
| `intents` | **neu**, ≥ 1 aus `config/routing/intents.yaml`, Pflicht bei `keyword`; informativ (E-07) |
| `triggers` | **neu** = `routing_patterns.keywords`; Lint ≤ 6, sprachneutral (IC-29) |
| `examples` | = `routing_patterns.examples`, verschoben; max. 2 je Sprache (`en`, `de`) |
| `size_class` | **neu**, S / M / L / XL (Mindestklasse; Beispiele §4.2: junior=S, developer=M, senior=L, concept-architect=XL) |
| `direct_dispatch` | **neu**, ersetzt die feste Tabelle (§4.2: git / agent-meta-manager / feedback / documenter = true) |
| `visibility` | **neu**, `{modes: [strict, advisory, main-chat], topologies: [primary, subagent, hybrid]}`, Default alle |
| `parallel`, `orchestrator_only`, `priority`, `name_only_reason` | unverändert; `priority` wird **gerendert** (Flag `p<N>`) |
| `requires` | **neu, optional**, z. B. `[tool:Bash, capability:subagent_dispatch]`; Zeile entfällt bei fehlender Provider-Capability |

`routing-overrides` in `project.yaml` (Top-Level, `additionalProperties: false`): `format`
(`auto` | `compact` | `json` | `off`, Default `auto` = capability-gated), `detail-file`,
`table-in-orchestrator` (`auto` | `always` | `never`), `roles.<role>` (Teilmenge der routing-Keys,
Deep-Merge), `pipelines.<name>.signal_keywords`.

**Merge-Regel (§4.2):** Projekt-Override gewinnt feldweise; Listen ersetzen (kein Append);
unbekannte Rolle/Intent/Key → `SyncError routing-overrides.unknown-*` (fail-closed); Rolle nicht im
Active-Set → Warnung `routing-overrides.inactive-role`.

### 3.2 Dispatch-Semantik (Plan §2.1, unverändert)

Die Tabelle ist die Entscheidungsgrundlage des Orchestrators, nicht die
Größenklassifizierung (die bleibt regelbasiert in §0 / `spec-plan-workflow`):

1. Pipeline-Treffer (Signal-Keywords) → 2. Rollen-Treffer (`triggers` / `examples`) →
   3. `orchestrator_only` → 4. Eskalations-Gate → 5. §11 Unknown-intent-Fallback
   (max. 1 Rückfrage; Kette `ask-user → meta-feedback → main-chat`) → 6.
   Target-description-Gate (kein Best-effort-Dispatch bei Überlappung).

Invarianten: `orchestrator` ist aus `target_agents` ausgeschlossen (Anti-Recursion);
`routing.parallel` bleibt rein informativ; Fan-out ist capability-gated; Artefakt C rendert nur im
`main-chat`-Mode. Bekannte Driftquellen (Plan §1.4 Q1/Q2): Überlappungen werden heute an das LLM
delegiert (`priority` deklariert, aber nicht konsumiert) und es existieren zwei Keyword-Quellen je
Rolle; die Spec behält diese Ist-Semantik bei und macht `priority` im compact-Format sichtbar.

### 3.3 Schnittstellen (Plan §4.3, unverändert)

| Schnittstelle | Vertrag | Konsumenten |
|---|---|---|
| `delegation_table.resolve_routing_model(agent_meta_root, config, *, active_set, pipelines, language, warn_sink) -> RoutingModel` | gefrorenes Dataclass: `roles`, `pipelines`, `intents`, `source` (default/override); deterministisch sortiert | Renderer, Lint, Eval-Generator, Admin-Preview |
| `routing_lint.lint(model, capabilities) -> list[Finding]` (neu, `scripts/lib/routing_lint.py`) | Codes `RL-UNKNOWN-ROLE`, `RL-UNKNOWN-INTENT`, `RL-TRIGGER-OVERLAP`, `RL-MISSING-INTENT`, `RL-TRIGGER-LIMIT`, `RL-REQUIRED-INTENT-UNCOVERED` (implement/review/git), `RL-CYCLE`, `RL-DEAD-ROW` | `sync.py --validate`, Admin-UI, Tests |
| `agents.render_routing(model, *, fmt: "compact"|"json", roster_in_harness: bool) -> tuple[str, str]` | `(inline_block, detail_doc)`; compact-Zeile `<agent>|<flags>|<intents>|<kw;kw>|<example>`, Flags `req,rec,orch-only,name-only,dd,S..XL,p<N>`; `json` = heutiges Format minus `name_index` bei `roster_in_harness` | `config.py` (`INTENT_ROUTING_TOOLS`, `ROUTING_DETAILS_FILE`), Admin-Preview |
| Platzhalter | `{{INTENT_ROUTING_TOOLS}}` (Inhalt → compact), `{{ROUTING_DETAILS_PATH}}` (neu, Pointer), `{{AGENT_DELEGATION_TABLE}}` (Keywords aus `triggers[:3]`), `{{DIRECT_DISPATCH_SECTION}}` (aus `direct_dispatch: true` generiert) | `orchestrator.md`, `use-orchestrator.md`, `agents-table.md` |
| Admin-API | `GET /api/routing/model`, `GET /api/routing/preview?provider=<P>`, `POST /api/config/project/section {section:"routing-overrides"}` (Guard Lint fail-closed) | `docs/ui/admin-ui.html` |
| Eval | `scripts/gen_role_routing_eval_catalog.py` (neu): je Rolle 1 Fall pro `examples.<lang>` → `expected: role`; Kollisionen ausgeschlossen, manuell in `catalog.manual.yaml` | `tests/routing-llm-eval/run_eval.sh` |

**Leitplanken (Plan §8 „CI-Fallen“):** keine Provider-Literale in `agents/1-generic/*` und
`rules/1-generic/*` (Pointer nur über `{{ROUTING_DETAILS_PATH}}`); keine Routing-Daten in Templates
(`test_no_role_routes_in_templates.py`); Python 3.9-Kompatibilität; stdlib + PyYAML (ADR-1);
Determinismus (zwei Syncs byte-identisch), kein Datum/Pfad im Routing-Block.

## 4. Informative Intent-Taxonomie (E-07 / Plan §4.2, §11 E3)

### 4.1 Status der Taxonomie

E-07 (Roadmap §4): **„Taxonomie informativ; Routing-Spec nach Review freigegeben.“** E3
(Plan §11, Empfehlung = Nutzerentscheidung): **„Taxonomie, zunächst informativ“** — Flag in der
Zeile, Eval-Gruppierung; die Routing-Entscheidung bleibt Trigger + Example. Der Lint prüft nur das
Pflichtfeld (`intents` ≥ 1) und die Zugehörigkeit zum Katalog (`RL-MISSING-INTENT`,
`RL-UNKNOWN-INTENT`), nicht die intent-basierte Zielwahl. Damit ist die Taxonomie **kein**
Routing-Entscheidungsmerkmal und kein neuer Entscheidungspunkt.

### 4.2 Die 16 Intents (Plan §4.2)

`config/routing/intents.yaml` (neu, Framework) — ~16 Intents mit 1-Zeilen-Definition und
Default-`size_class`. Der Plan nennt folgende Keys (Wortlaut):

`implement`, `fix`, `review`, `test`, `spec`, `plan`, `design`, `docs`, `git`, `meta`, `ops`,
`security`, `data`, `knowledge`, `estimate`, `triage`

| Intent | Zweck (Kurzform aus dem Intent-Key / Plan-Kontext) | Explizite plan-seitige Zuordnung (§4.2) |
|---|---|---|
| `implement` | Feature-Implementierung | `developer = M`, `junior-developer = S` (Beispiele für `size_class`) |
| `fix` | Bugfix | — (Task 2) |
| `review` | Review-Auftrag | — (Task 2) |
| `test` | Test-Auftrag | — (Task 2) |
| `spec` | Spec schreiben | — (Task 2) |
| `plan` | Umsetzungsplanung | — (Task 2) |
| `design` | Konzept / Systemdesign | `concept-architect = XL` (Beispiel für `size_class`) |
| `docs` | Dokumentation | `documenter = true` (Beispiel für `direct_dispatch`) |
| `git` | Git-Operationen | `git = true` (Beispiel für `direct_dispatch`); Pflichtintent laut `RL-REQUIRED-INTENT-UNCOVERED` |
| `meta` | agent-meta-Selbstverwaltung | `agent-meta-manager = true`, `feedback = true` (Beispiele für `direct_dispatch`) |
| `ops` | Betrieb / Infrastruktur | — (Task 2) |
| `security` | Sicherheitsprüfung | — (Task 2) |
| `data` | Daten / ETL | — (Task 2) |
| `knowledge` | Knowledge-Engine | — (Task 2) |
| `estimate` | Aufwandsschätzung | — (Task 2) |
| `triage` | Issue-Triage | — (Task 2) |

Die finalen 1-Zeilen-Definitionen und Default-`size_class`-Werte werden mit
`config/routing/intents.yaml` in PR 2 erstellt; hier werden keine eigenen Werte erfunden.

### 4.3 Zuordnungsregeln (Plan Task 2, nicht hier entschieden)

Der Entwurf der vollständigen Tabelle (88 keyword-adressierbare Rollen → Intent(s)) ist Task 2
(`concept-architect`) des Block A. Seine Akzeptanzbedingungen, wie im Plan festgelegt:

- jede der 88 Rollen hat **≥ 1 Intent**;
- **kein Intent** hat **> 12 Rollen**;
- Nutzer bestätigt die Zuordnung (E3).

Der Plan stuft diese Meinungsarbeit als Risiko ein (§10) und verlangt genau deshalb die
informative Einführung: `intents` ist zunächst Pflichtfeld + Anzeige, nicht routing-entscheidend.

## 5. Token-Messung: Bytes/4-Baseline vs. tiktoken-Kalibrierung (§2.2/W2, Task 0)

### 5.1 Konflikt und Auflösung

Roadmap §2.3 **W2**: „Token-Zahlen Bytes/4 vs. tiktoken → Routing-PR 1 Task 0 (tiktoken) als erste
Messung.“ Plan-Kopfbild Zeile 18: „Messdaten nicht eingecheckt, reproduzierbar per Task 0
(Messskript, tiktoken cl100k). Tokens: **tiktoken cl100k** wo so gekennzeichnet, sonst
**Bytes/4 (Proxy)**.“ Roadmap §7 ergänzt: die Hebelzahlen stammen aus Settings-/Loop-Plan
(Bytes/4); erst Routing-PR 1 Task 0 kalibriert.

- **Baseline (Repository, stdlib):** `scripts/lib/context_report.py::count_text_stats(data: bytes)`
  liefert `tokens_est = bytes // 4` (`BYTES_PER_TOKEN = 4`); nachweisbar aufrufbar mit
  `PYTHONPATH=scripts python3 -c "from lib.context_report import count_text_stats; ..."`.
  Konsument: `scripts/lib/agent_report.py::measure_agents` (SPEC-AGENT-LOOP-BATCH0-2026-11-20,
  IC-1/IC-1b). Damit ist ein bestehender, commitierter Helper vorhanden; die Spec benennt ihn
  statt einen neuen zu erfinden.
- **Kalibrierung (dev-only, nicht commitiert):** Task 0 sieht ein Skript `.tmp/routing-measure.py`
  vor (git-ignoriert) mit `tiktoken`-Encoder `cl100k_base`. Es misst vier Schnitte:
  `.claude/agents/orchestrator.md`, die gerenderte Routing-Zeile/-Block, `AGENTS.md` und den
  Compact-Golden-Block. Ergebnis: Tabelle in dieser Spec (§5.2); AC: Zahlen aus Plan §1.1/§3.1
  reproduziert ± 2 %.

### 5.2 Referenzwerte aus dem Plan (Basis `origin/main 92d41a90`)

| Fläche | Bytes | Tokens | Maß |
|---|---|---|---|
| `route_intent`-JSON, Claude-Orchestrator | 31.247 B | 7.662 | cl100k (Plan §1.1/§3.1) |
| Gesamt-Render Claude-Orchestrator | 73.403 B | 18.581 | cl100k (Plan §1.1) |
| Agent table im Orchestrator | 5.208 B (61 Z.) | ~1,3k | Bytes/4-Proxy (Plan §3.1) |
| Agent Directory `AGENTS.md` (Opencode/Gemini) | 5.138 B (62 Z.) von 16.988 B | 4.788 | cl100k (Plan §3.1) |
| Harness-Roster (58 Rollen) | 5.133 B | ~1,3k | Bytes/4-Proxy (Plan §3.1) |
| Artefakt C (`strict`) | 0 | 0 | — (Plan §3.1) |
| Ziel: kompakter Routing-Block | 8.435 B | ~2,1k | cl100k, hochgerechnet (Plan §3.2 T1) |
| Ziel: Orchestrator-Spawn gesamt | ~45 KB (von 73,4 KB) | ≈ −7k | cl100k (Plan §3.2) |

Zeilenanker und Zahlen stammen aus dem Plan-Stand `92d41a90`; der Plan verlangt vor Ausführung
einen Freshness-Check. Diese Spec ist Docs-only und hat die Messung **nicht** erneut ausgeführt;
die Tabelle dokumentiert die planseitige Referenz, nicht einen neuen Messlauf.

### 5.3 Explizite Annahmen

- `tokens_est` ist ein Proxy (`bytes // 4`), kein Tokenizer; alle damit bezifferten Werte sind als
  solche gekennzeichnet und nicht mit cl100k-Zahlen gleichzusetzen.
- cl100k (`cl100k_base`) ist die Referenzcodierung; nur so gekennzeichnete Zahlen sind echte
  Tokenzählungen.
- Beide Verfahren rechnen auf identischen Textausschnitten desselben Renders; Vergleichbarkeit
  setzt denselben Stand und dieselben Provider-Capabilities voraus.
- `tiktoken` ist ausschließlich dev-zeitiges Messwerkzeug in `.tmp/`; **keine neue externe
  Abhängigkeit** im Produktivcode. Sync-Code bleibt stdlib + PyYAML (ADR-1). Der aktuelle
  Arbeitsstand hat `tiktoken` nicht installiert — die Methode ist dokumentiert, nicht ausgeführt.
- Toleranz für die Kalibrierung: ± 2 % gegen Plan §1.1/§3.1 (Task-0-AC).

## 6. Akzeptanzkriterien (Plan §4.4, unverändert)

Die ACs gelten für die Umsetzung in PR 2/3; diese Spec liefert die Grundlage und den Gate.

- **AC-R1** `python3 scripts/sync.py` ohne `routing-overrides` und mit
  `routing-overrides.format: json` rendert byte-identisch zu heute (Rückfallpfad).
- **AC-R2** Default (`format: auto`, alle Provider `route_intent_tool: false`): Routing-Block im
  Claude-Orchestrator ≤ 9.000 B bei 57 Rollen; Zeilen deterministisch sortiert; zwei Syncs
  byte-identisch.
- **AC-R3** `roster_in_harness: true` → kein `name_index`, keine Agent table im Orchestrator;
  `false` → Tabelle bleibt; kein `if provider ==`.
- **AC-R4** Lazy-Detaildatei `<agents_dir>/../routing-details.md` enthält alle Felder; genau eine
  Pointer-Zeile im Prompt.
- **AC-R5** Lint: jede Fehlerklasse aus §3.3 hat einen Fixture-Fall; `sync.py --validate` meldet
  `RL-*`; Admin-`POST` mit Fehler → HTTP 400, Datei unverändert.
- **AC-R6** `routing-overrides.roles.<r>.triggers` ändert die gerenderte Zeile;
  `addressability: excluded` entfernt die Rolle aus Zeile **und** Enum; unbekannte Rolle →
  `SyncError`.
- **AC-R7** Direct-Dispatch-Tabelle aus `direct_dispatch: true`, textgleich zum Golden;
  `config/direct-dispatch-section.md` entfällt.
- **AC-R8** Eval-Katalog `catalog.roles.generated.yaml` idempotent, ≥ 55 Fälle,
  `run_eval.sh --dry-run` ohne LLM-Aufruf.
- **AC-R9** Admin-UI: Default vs. Override je Feld, „Reset auf Default“, Preview mit Bytes +
  Tok-Proxy (Bytes/4, gekennzeichnet) + Lint; Tastaturbedienbar, Labels verknüpft (WCAG 2.1 AA).
- **AC-R10** `tests/test_context_budgets.py`: Claude-Orchestrator-Ceiling ≤ 48.000 B neu gepinnt;
  AGENTS.md-Ceiling unverändert oder kleiner.
- **AC-R11** Python 3.9-kompatibel, stdlib + PyYAML.

Ergänzend für Block A: Task-0-AC ± 2 % (§5.3); Task-1-AC Review ohne offene Blocker und
Nutzer setzt Status APPROVED (hier erfolgt per Nutzergo 20.11.); Task-2-AC gemäß §4.3.

## 7. Traceability (ausschließlich referenzierte Quellen)

| Quelle | Stelle | Übernommen |
|---|---|---|
| Master-Roadmap | §1, P25 | Intent-Routing PR 1, Branch `docs/intent-routing-spec`, Art D/A, Templates nein, RB keiner, Aufwand M, E-07 |
| Master-Roadmap | §3.1, PR 0.6 | Branch `docs/intent-routing-spec`; Inhalt: tiktoken-Messung, Spec, Intent-Taxonomie informativ; Issues #1161 #779; RB keiner; Gate: Spec-Freigabe nach Review (E-07) |
| Master-Roadmap | §4, E-07 | „Taxonomie informativ; Routing-Spec nach Review freigegeben“ → §4 dieser Spec, Status APPROVED |
| Master-Roadmap | §4, E-31 | „Specs/Konzepte einzeln nach Review freigeben“ → diese Spec wird einzeln freigegeben; kein Bündel mit fremden Specs |
| Master-Roadmap | §2.3, W2 | Bytes/4 vs. tiktoken → Task 0 als erste Messung → §5 |
| Intent-Routing-Plan | §4 (Spec-Kern) | Zielbild §2, Datenmodell/Schnittstellen §3, Taxonomie §4, AC-R1..R11 §6, Migration-Festlegungen bleiben im Plan |
| Intent-Routing-Plan | §8, PR 1 / §7 Block A | Block A = Spec + Messung + Intent-Tabelle; keine generierten Dateien, kein Rebaseline-Commit → §1 |
| Intent-Routing-Plan | §11 E3 / §10 Risiko | Taxonomie zunächst informativ, Lint nur Pflichtfeld; Zuordnungs-ACs → §4.3 |
| Nutzergo 20.11. | Freigabesatz | E-07/E-31-Einzel-Spec-Freigaben erteilt; Status APPROVED ohne neue Entscheidungen → Kopfzeile |

Nachgelagerte PRs (nicht Teil dieser Spec): PR 2 / P26 / Roadmap 4.1 (Gate: „Spec 0.6 APPROVED“)
und PR 3 / P27 / Roadmap 5.4.

## 8. Migration / Kompatibilität (Plan §4.5, Festlegung bleibt dort)

- `role-defaults.yaml`: mechanische Migration `routing_patterns.* → routing.triggers/examples`,
  `intents` initial heuristisch aus Pipeline-Zugehörigkeit/Tier, dann manuell gereviewt (88 Rollen);
  alte Keys werden einen Minor lang gelesen (Warnung `routing.legacy-patterns`).
- Consumer: Minor-Bump + CHANGELOG „Changed: routing block compact by default; set
  `routing-overrides.format: json` to keep the old render“; `--check` meldet Drift einmalig.
- Rollback: `routing-overrides.format: json` + `table-in-orchestrator: always` (AC-R1);
  Git-Revert von PR 2 ohne Datenverlust.
