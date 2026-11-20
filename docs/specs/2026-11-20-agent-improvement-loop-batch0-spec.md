---
spec-id: SPEC-AGENT-LOOP-BATCH0-2026-11-20
title: Agent-Verbesserungsschleife Batch 0 — Mess-CLI, Rubrik-Lint, Ratsche, Sektionsschema
status: APPROVED
plan: docs/plans/2026-11-15-master-roadmap.md (P28 :59, PR 6.0 :221, E-29 :297)
detail: docs/plans/2026-11-14-agent-improvement-loop-plan.md (Batch 0 :208-214, DRAFT, Base 3dc03f95)
branch: chore/agent-loop-batch-0
base: 3cb97fb7
date: 2026-11-20
autor: concept-specifier (Subagent via Orchestrator)
issues: "#1244 (Ceiling-Test-Teil), #885-Ersatz (Loop-Rubrik)"
---

# Agent-Verbesserungsschleife Batch 0 — Spec

> Status: APPROVED (User, 2026-11-19 Roadmap approved — E-29; Nutzer-Go 2026-11-20 „Ja Go! Weiter geht es!"; Spec nachgereicht auf Basis des approbierten Master-Plans, keine neue Entscheidung; Beleg: docs/reviews/2026-11-20-agent-loop-batch0-spec-review.md — OQ-1..4 CONFIRM_CONSERVATIVE, ESCALATE leer, MAJOR 19500*1024→19500 korrigiert)
> Klasse: **M**. Keine Rebaseline (Master :221 RB = „keiner"). Kein Code, keine Syncs, keine Tests in dieser Spec.
> Freigabe-Gate greift nach Detailplan :209 erst **vor Batch 1**, nicht vor Batch 0.

## Problem / Ziel / Nicht-Ziele

### Problem
Der Master-Plan (PR 6.0) verlangt für die Verbesserungsschleife eine reproduzierbare Mess- und Absicherungs-Infrastruktur, die am Stand `3cb97fb7` fehlt (Precheck `.tmp/loop-batch0-precheck.md`: beide 6.0-Issues `NOT_STARTED`):

- Keine per-Rolle × Provider-Messung: `scripts/measure_context.py` kennt nur `target`, `--project`, `--json` (verifiziert `:196-228`), kein `--per-agent`; `scripts/lib/context_report.py` misst nur Artefakte pro Provider (`:130-186`), nicht Rollen.
- Keine Ratsche: `tests/test_context_budgets.py:306-326` friert Ist-Werte (`_IST_FULL`) mit 2 % Toleranz ein, **keine Ratsche nach unten, keine Session-Summe** (Detailplan :70).
- Kein Rubrik-Lint: `tests/test_template_rubric_lint.py` existiert nicht; Rubrik R1/R2/R4/R5/R9/R11 (Detailplan §4 :94-106) ist noch nicht prüfbar.
- Kein dokumentiertes Sektionsschema: `docs/guides/features/agent-composition.md` beschreibt nur `extends`/`patches`, keine kanonischen Worker-Sektionen; `conventions`-Skill (`.claude/skills/conventions/SKILL.md`, verifiziert) kennt keinen Sektionsschema-Check.

### Ziel (Goal)
Batch-0-Infrastruktur anlegen, damit die Batches 1–11 messbar und rückfallfest ablaufen:

1. **Mess-CLI** liefert JSON `{provider:{role:{bytes,lines,tokens_approx}}}` plus Session-Summe (Task 1.1).
2. **Ratschen-Test** verhindert Wachstum > 1 % und hält die §5-Zielwerte als `xfail(strict)` (Task 1.4, deckt #1244 Pkt 1).
3. **Rubrik-Lint** prüft R1/R2/R4/R5/R9/R11, startet `xfail(strict=False)` mit Allowlist (Task 1.3).
4. **Sektionsschema** ist in Doku + `conventions`-Skill dokumentiert (Task 1.5).
5. Diese Spec (Task 0.1) existiert mit Status APPROVED; Review/Re-Approval vor Batch 1.

### Nicht-Ziele / Non-Scope
- Kein Entfernen/Reduzieren von Rollen, kein `config/role-defaults.yaml`-Roster-Enum — Roster-Teil #1244 = P6/2.2 + E-12 (Master :37, :95, :280, :350).
- Keine `agents/**`-Rewrites (Batch 2–10), keine Snippet-/Block-Kürzung (Batch 1), keine `templates/context/**`-Änderung (H6/P30).
- Kein Rebaseline (Generated-File-Hashes, AC-01, Goldens, Ceilings), kein Sync, kein Render.
- Kein `xfail`→hart-Umschalten, kein Zielwert-Erreichen — das ist Batch 11 (Detailplan :228-229).
- Keine kostenpflichtigen Claude-Evals (E-29), kein globales Compact-Profil (E-29/W1), keine Prompt-Sprach-Änderung (E-29 → Batch 1/2+).
- Kein spec-approval Gate für Batch 0 selbst (Gate erst vor Batch 1, :209).

### Betroffene Subsysteme
`scripts/` (Mess-CLI), `tests/` (Ratschen-Test, Rubrik-Lint), `docs/guides/` + `.claude/skills/` (Doku). Strikt disjunkt zu `agents/**`, `config/role-defaults.yaml`, `templates/context/**`, Hooks, Admin-UI.

## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)

Verifikationsstand: alle Signaturen unten gegen Checkout `3cb97fb7` geprüft; `lib.context_report.count_text_stats(data: bytes) -> dict` liefert `{bytes, lines, tokens_est}`, `tokens_est = len(data)//4` (`:77-84`); `measure_artifacts(project_root, active_providers, capabilities) -> dict` (`:130-186`). Neue Contracts extended, forken keine-existing Konvention.

### IC-1 — `scripts/lib/agent_report.py` (neu)
- `measure_agents(project_root: Path, providers: Sequence[str], mappings: Mapping[str, Mapping]) -> dict`
  - Liefert exakt `{"<provider>": {"<role>": {"bytes": int, "lines": int, "tokens_approx": int}}, ...}`; `tokens_approx` = `count_text_stats(...)["tokens_est"]` (Bytes/4, kein tiktoken — Detailplan :19).
  - Rollenquellen: `.claude/agents/*.md` (gegerendert) bzw. `agents/1-generic/*.md` (Quelle) — Auswahl per `mappings[provider]["agents_dir"]` + `agent_ext`; Summary-Schluessel `session-sum` (siehe IC-1b).
  - Fehlerpfad: fehlendes `agents_dir` → leeres Mapping für diesen Provider, kein Crash; kein Provider mit Rollen → `ValueError("no agent roles found")` (von CLI zu Exit 1).
- `session_sum(report: Mapping) -> dict` — IC-1b: liefert `{"bytes": int, "lines": int, "tokens_approx": int}` als Summe aus `entry-file` + `rules` + `descriptions` (Detailplan :210; AC-L1 „always-on + Spawn"). Der Session-Summe-Wert wird unter dem Reserveschluessel `"session-sum"` im Top-Level-JSON abgelegt (nicht als Provider). Exakter Ses-sions-Summe-Ceiling-Wert → OFFENE FRAGE OQ-3.
- `render_agent_table(report: Mapping) -> str` — ASCII-Tabelle `Provider | Role | Bytes | Lines | Tokens (~)` + TOTAL-Zeile + `SESSION-SUM`-Zeile; nutzt `lib.context_report.render_table`-Konvention (`:220-233`).
- Kein provider-spezifisches `if provider == ...` (AGENTS.md: provider-agnostisch); Provider nur über `mappings`/Capabilities.

### IC-2 — `scripts/measure_context.py` (modify): Flag `--per-agent`
- `parse_args(argv: list[str] | None = None) -> argparse.Namespace` (`:196-228`): neues Flag `--per-agent` (`action="store_true"`), Namespace erhält Attribut `per_agent: bool`. Bestehende Attribute `target`, `project`, `json` bleiben unverändert (Rückwärtskompatibilität).
- `main(argv=None) -> int` (`:257-282`): bei `args.per_agent` Disposition zu IC-3 statt `collect_measurements`; `--per-agent` ohne `--project` → `print("error: --per-agent requires --project", file=sys.stderr)`, Exit 2.
- Fehlerpfade: kein Projekt-Config → Exit 1 (wie `run_project_report`, `:240-243`); keine Rollen → Exit 1; `--json` → `json.dumps(..., indent=2)` (konsistent `:253`).

### IC-3 — `scripts/measure_context.py:run_agent_report(project: Path, as_json: bool) -> int` (neu)
- Analoge zu `run_project_report` (`:231-254`): `lib.config.load_config` → `lib.providers.{load_provider_capabilities, load_providers_config, resolve_providers}` → `lib.context_report.merge_provider_mappings` → `agent_report.measure_agents` → `agent_report.session_sum`.
- Ausgabe: `json.dumps({"providers": <IC-1-Mapping>, "session-sum": <IC-1b>}, indent=2)` bei `--json`, sonst `render_agent_table`. Hinweis: JSON-SHAPE-Kontrakt ist `{provider:{role:{bytes,lines,tokens_approx}}}` + Session-Summe; die Einbettung unter `"providers"` ist Implementierungsdetail der CLI, das Test `tests/test_agent_report.py` muss die rolle-Mapping-Struktur direkt prüfen. Endgültige Top-Level-Einbettung → OFFENE FRAGE OQ-2.

### IC-4 — `tests/test_agent_report.py` (neu)
- `test_json_shape()`: Given `measure_agents` auf Test-Fixture-Verzeichnis mit ≥2 Rollen × ≥2 Providern; When Aufruf; Then Mapping hat Provider-Keys, jeder Provider hat Rollen-Keys, jede Rolle hat genau `{"bytes","lines","tokens_approx"}`, alle `int`, `tokens_approx == bytes//4`.
- `test_session_sum_contains_components()`: Given Fixture; When `session_sum`; Then Summe = entry-file + rules + descriptions (Byte-Genauigkeit), Struktur `{bytes,lines,tokens_approx}`.
- `test_cli_per_agent_flag()`: Given `parse_args(["--per-agent","--project",p,"--json"])`; When `main`; Then `per_agent is True`, Exit 0, JSON parsebar mit Rollen-Mapping + `session-sum`.
- `test_no_per_agent_without_project()`: Given `parse_args(["--per-agent"])`; When `main`; Then Exit 2, stderr enthält `requires --project`.

### IC-5 — `tests/test_agent_budget_ratchet.py` (neu; #1244 Pkt 1)
- Konstante `NO_GROWTH_TOLERANCE = 0.01` (Detailplan E7 :238, 1 %; **unterschiedlich** zu `test_context_budgets.py` 2 % Toleranz — keine Änderung dort).
- `test_no_artifact_grows()`: Given Baseline-JSON `.tmp/plans/scratch/baseline-batch-0.json` (Detailplan :126/:222) mit `bytes` je Rolle/Provider; When aktuelle Messung; Then kein `current > baseline * 1.01`, sonst `AssertionError` mit Rolle/Provider/Delta.
- `test_target_values_are_xfail_strict()`: Given §5-Zielwerte (Detailplan :108-120) als parametrisierte `pytest.param(..., marks=pytest.mark.xfail(strict=True, reason="target §5 not yet reached"))`; When Messung; Then `xfail` bis Ziel erreicht, `XPASS(strict)` → Testfehler (zwingt Batch 11 zum Entfernen des Marks). **Welche§5-Zielwerte auf welche Rolle/Provider-artefakte abgebildet werden, ist OFFENE FRAGE OQ-1 — keine Werte erfinden.**
- `test_session_sum_ceiling()`: Given Session-Summe aus IC-1b; When Vergleich mit §5-Gesamtziel „Always-on Claude ≤ 19,5 KB" (Detailplan :120); Then `bytes <= 19500` (als `xfail(strict)`, bis erreicht; Quelle §5 (19,5 KB decimal)). Exakter Wert/Scope der Ceiling → OFFENE FRAGE OQ-3.
- Fehlerpfad: fehlende Baseline-Datei → `pytest.skip("baseline-batch-0.json missing — run Task 1.1 first")` (nicht still passing).

### IC-6 — `tests/test_template_rubric_lint.py` (neu; #885-Ersatz)
- Konstante `RULES = ("R1","R2","R4","R5","R9","R11")` (Detailplan :212); `ALLOWLIST: dict[str, set[str]]` (regel → Rollenmenge), initial alle 99 Rollen je Regel (siehe IC-6 Startstatus).
- `lint_role(role_path: Path, rule_id: str) -> list[str]`: liefert Verstöße; leere Liste = grün. Prüfungen exakt nach Detailplan §4 :94-106:
  - R1: Frontmatter `description` ≤ 160 Zeichen (Lint Länge).
  - R2: Sektion `Boundaries` vorhanden, `Does not`-Liste ≤ 5, Eskalationsziel genannt (Lint Sektion).
  - R4: genau 1 Output-Contract-Sektion mit kanonischem Namen (§9.2), Schema ≤ 25 Zeilen (Lint Sektionsname).
  - R5: `Don'ts` ≤ 7 Punkte, keine Begründungsprosa (Lint Punktzahl).
  - R9: kein `Issue #\d+` im Body (Provenienz nur `<!-- -->`/CHANGELOG), Tabellen/Listen statt Prosa (Lint Regex).
  - R11: DE-Markerquote < 5 %, kanonische Sektionsnamen nach §9.2 (Lint DE-Marker).
- Startstatus: jede Regel × Rolle als `pytest.param(..., marks=pytest.mark.xfail(strict=False, reason="Batch-0 allowlist, tighten per batch"))`; `strict=False` erlaubt XPASS ohne Fehler (Detailplan :212). Fehlerpfad: Rolle ohne `description` → R1-Verstoß (nicht Crash).

### IC-7 — `docs/guides/features/agent-composition.md` (modify)
- Neue Sektion „Standard-Sektionsschema (Worker)": kanonische Namen (EN) `Purpose`, `Boundaries`, `Parse input`, `Workflow`, `Output contract`, `Don'ts`, `Escalation`, `Project context`, `Language` in Reihenfolge `frontmatter → > Extension → <persona> → <workflow> → <rules> → <context> → Blöcke` (Detailplan §9.2 :179-181).
- Migrationsliste alt→neu: `Sprache→Language`, `Projektkontext→Project context`, `Return`/`JSON Output Schema`/`Output contract`-Varianten→`Output contract` (Detailplan :75, :181).
- Hinweis: `patches`-Anker in `2-platform/**` bei Umbenennung nachziehen (bestehender Anker-Hinweis `:170-183`, `:307-311`).

### IC-8 — `.claude/skills/conventions/SKILL.md` (modify)
- Ergänzung: Sektionsschema-Pflicht (kanonische Namen, Reihenfolge = Cache-Präfix stabil→variabel) im Abschnitt „Adding a New Agent Role" / neue Checkliste; Verweis auf Rubrik R1/R2/R4/R5/R9/R11 und IC-7. Keine Änderung an Version-Bump-Regeln (`:11-15`) oder Instruction-Bleed-Prüfpunkten (`:27-38`).

## Datenfluss

```
Task 1.1: .claude/agents/*.md (gerendert)  OR  agents/1-generic/*.md (Quelle)
   └─ measure_agents(project_root, providers, mappings)   [IC-1]
        ├─ lib.context_report.count_text_stats → {bytes, lines, tokens_est}
        └─ tokens_est → tokens_approx (Bytes/4 Proxy)
   └─ {provider:{role:{bytes,lines,tokens_approx}}}  +  session_sum() [IC-1b]
   └─ scripts/measure_context.py --per-agent --project P [--json]  [IC-2/IC-3]
        ├─ table → stdout (render_agent_table, TOTAL + SESSION-SUM)
        └─ json  → stdout (kein Datei-Schreiben; Baseline separat in .tmp/plans/scratch/)

Task 1.4: Baseline-JSON (.tmp/plans/scratch/baseline-batch-0.json, von Task 1.1 erzeugt)
   └─ test_no_artifact_grows: current vs baseline*1.01 → Fail bei Wachstum [IC-5]
   └─ test_target_values_are_xfail_strict: current vs §5-Ziele → xfail(strict)
   └─ test_session_sum_ceiling: session-sum vs 19,5 KB → xfail(strict)  (#1244 Pkt 1)

Task 1.3: agents/1-generic/*.md + 2-platform/*.md
   └─ lint_role(path, rule) → findings pro R1/R2/R4/R5/R9/R11  [IC-6]
   └─ xfail(strict=False) + ALLOWLIST → grün/XPASS (Batch-für-Batch verschärft)

Task 1.5: IC-7 + IC-8 (Doku, kein Runtime-Effekt)
```

Persistenz: keine. Mess-Summen werden als Baseline-JSON in `.tmp/` zwischengespeichert (nicht eingecheckt); alle übigen Ausgaben gehen nach stdout. Keine Rebaseline-Orte berührt.

## Acceptance Criteria (nummeriert, testbar)

Jede AC nennt ihren Interface Contract (IC-n) und ist Given/When/Then formuliert.

- **AC-1 (IC-1):** Given ein Fixture-Verzeichnis mit Rollen für ≥2 Provider; When `measure_agents(...)`; Then entspricht das Ergebnis exakt `{provider:{role:{bytes:int,lines:int,tokens_approx:int}}}`, `tokens_approx == bytes//4`, ohne weitere Keys pro Rolle.
- **AC-2 (IC-1b):** Given dasselbe Fixture; When `session_sum(report)`; Then ist das Ergebnis `{bytes,lines,tokens_approx}`, deren `bytes` der Summe von `entry-file`+`rules`+`descriptions` entspricht, und liegt unter Reserveschluessel `"session-sum"` im Top-Level-JSON.
- **AC-3 (IC-2, IC-3):** Given `python3 scripts/measure_context.py --per-agent --project <P> --json`; When Ausfuehrung; Then Exit 0, parsebares JSON mit Rollen-Mapping + `session-sum`, und die Tabelle (ohne `--json`) enthält eine `TOTAL`- und eine `SESSION-SUM`-Zeile.
- **AC-4 (IC-2):** Given `python3 scripts/measure_context.py --per-agent` ohne `--project`; When Ausfuehrung; Then Exit 2 und stderr `error: --per-agent requires --project`.
- **AC-5 (IC-5, #1244):** Given Baseline-JSON mit Wert `B` für Rolle R/Provider P und aktuellem Wert `B*1.02`; When `test_no_artifact_grows`; Then `AssertionError` mit R/P/Delta. Bei `B*1.005` → kein Fehler.
- **AC-6 (IC-5):** Given §5-Zielwert noch nicht erreicht; When `pytest tests/test_agent_budget_ratchet.py`; Then `xfail` (nicht Fail). Bei erreichem Ziel → `XPASS(strict)` = Fehler (Marker muss entfernt werden). (Zielwert-Mapping gemäß OQ-1.)
- **AC-7 (IC-5):** Given Session-Summe > 19,5 KB; When `test_session_sum_ceiling`; Then `xfail(strict)`; bei ≤ 19,5 KB → `XPASS(strict)` = Fehler. (Wert/Scope gemäß OQ-3.)
- **AC-8 (IC-6):** Given eine Rolle mit `description` ∈ 161..200 Zeichen; When `lint_role(path,"R1")`; Then enthält die Ergebnisliste einen R1-Verstoß. Analog: R2 ohne `Boundaries`, R4 mit 2 Output-Sektionen, R5 mit 8 Don'ts, R9 mit `Issue #123`, R11 mit >5 % DE-Markern → je ≥1 Verstoß.
- **AC-9 (IC-6):** Given der Initialzustand mit `ALLOWLIST` = alle Rollen und `strict=False`; When `pytest tests/test_template_rubric_lint.py`; Then alle Params `xfail`/`XPASS` ohne Fehlschlag;(`strict=False`), keine echte Regression blockiert den Batch-0-Lauf.
- **AC-10 (IC-5):** Given fehlende `.tmp/plans/scratch/baseline-batch-0.json`; When Ratschen-Test läuft; Then `pytest.skip` mit Hinweis auf Task 1.1 — kein stilles Bestehen.
- **AC-11 (IC-7, IC-8):** Given die Dokumentation nach Änderung; When Sektionsschema gelesen wird; Then enthält `agent-composition.md` alle 9 kanonischen Namen + Reihenfolge + Migrationsliste + `patches`-Hinweis, und der `conventions`-Skill verweist auf Schema und Rubrik-IDs.
- **AC-12 (IC-1, IC-2):** Given Provider-Konfiguration mit `agents_dir`/`agent_ext` pro Provider; When Messung; Then keine `if provider == ...`-Verzweigung im Messpfad; Provider-Verhalten ausschließlich über `mappings` gesteuert.

## Offene Fragen + Risiken

### Offene Fragen (do NOT invent — escalation an concept-reviewer/User)
- **OQ-1 (§5-Zielwert-Mapping):** Detailplan §5 :108-120 nennt Hebel-Ziele (H1 ≤8 KB, H2 ≤20 KB, H3 ~35 KB, H4 −30 %, H5 ≤4 KB, H6 ≤12 KB) und Gesamtziele (Roster −45 %/≤300 KB, Orchestrator −60 %/≤28 KB, Ø Worker −35 %, Always-on −20 %/≤19,5 KB, AGENTS.md ≤12 KB). Welcher dieser Werte auf welche konkrete Kombination aus Rolle × Provider-artefakt im `xfail(strict)`-Test angewendet wird, ist im DRAFT-Plan nicht eindeutig spezifiziert. Bis zur Klarstellung: Werte nur als parametrisierte Konstanten mit Quellenvermerk §5 verwenden, keine eigenen Zielwerte erfinden.
- **OQ-2 (JSON-Top-Level-Einbettung):** Der Message-Contract lautet `{provider:{role:{...}}}` + Session-Summe; ob `"session-sum"` als Top-Level-Reserveschluessel neben den Providern oder unter separatem `"providers"`-Key liegt, ist im Plan nicht festgelegt. IC-1/IC-3 waehlen Reserveschluessel; final mit Review abstimmen.
- **OQ-3 (Session-Summe-Ceiling-Wert):** #1244 Pkt 1 verlangt einen Ceiling, der Plan nennt als einziges Gesamtziel „Always-on Claude ≤ 19,5 KB" (:120). Ob der Ceiling auf genau diesem Wert, auf `19,5 KB * 1,01` oder auf einem separat zu definierenden Session-Summe-Wert basieren soll → offen. Kein Wert erfinden.
- **OQ-4 (Rollenquelle):** Messung gegen gerenderte `.claude/agents/*.md` (58 Rollen, :210) oder gegen Quell-Templates `agents/1-generic/*.md` (99 Rollen, :212 für Lint)? AC-1/IC-1 erlauben beide ueber `agents_dir`; finale Wahl beeinflusst die Zeilenzahl (58 vs 99) und die Baseline. Mit Review klären.

### Risiken
- **Stale Base:** Detailplan ist DRAFT auf `3dc03f95`; Zeilenanker/Dateipfade können gegen `3cb97fb7` veraltet sein. Vor Implementierung Freshness-Check (Measure-CLI-Funktionen und `conventions`-Skill wurden in dieser Spec gegen Checkout geprüft).
- **Zielwert-Drift:** Ohne OQ-1-Klärung drohen erfundene Zielwerte → Review-Blocker. Deshalb xfail-Marks mit Quellenvermerk.
- **Toleranz-Verwechslung:** Neue Ratsche 1 % (E7) vs. bestehende Ceilings 2 % (`test_context_budgets.py`); nicht verwechseln, keine Änderung an `test_context_budgets.py`.
- **Roster-Grenze:** Jede Beruehrung von `config/role-defaults.yaml` oder `agents/**` wuerde E-12/P6-Rebaseline ausloesen — strikt vermeiden.
- **Eval-/Sprach-Gate:** E-29 (Englisch, Issue-Nummern raus, keine Claude-Evals, kein globales Compact) ist fuer Batch 0 nur Dokumentations-/Rubrik-Grundlage, keine Template-Aenderung.

### ADRs (adr.github.io — Context / Decision / Consequences)
- **ADR-1 — Tokens als Bytes/4-Proxy:** Context: kein tiktoken in Stdlib, Plan :19 kennzeichnet Tokens ueberall als Proxy. Decision: `tokens_approx = bytes//4` ueber `count_text_stats`. Consequences: DE/JSON unterschaetzt;Kalibrierung optional Task 1.2, keine Genauigkeitsgarantie.
- **ADR-2 — Ratsche als xfail(strict) statt harter Grenze jetzt:** Context: E-29 „Ziele hart", aber §5-Ziele noch nicht erreicht (Detailplan AC-L2). Decision: `xfail(strict)` bis erreicht, dann Batch 11 hart; kein Artefakt wachsen lasen ist dagegen ab Task 1.4 hart (1 %). Consequences: XPASS zwingt Marker-Entfernung; verhindert "stillschweigend weiches" Ziel.
- **ADR-3 — Rubrik-Lint startet nicht-strikt:** Context: 99 Rollen entsprechen §9.2 noch nicht (580 H2-Varianten, :75). Decision: `xfail(strict=False)` + Allowlist, Verschärfung je Batch. Consequences: kein sofortiger Rotzustand; Disziplin muss ueber Batch-Fortschritt erfolgen.

## Self-Review / Coverage Checklist

| Pflicht | Erfuellt |
|---|---|
| Header + Status-Marker exakt wie vorgegeben | ja |
| Problem / Ziel / Nicht-Ziele + Goal + Scope/Non-Scope | ja |
| Interface Contracts: Datei:Symbol, Signatur, Fehlerpfade (IC-1..IC-8) | ja |
| Exakter JSON-Shape + Ratchet/Rubric-Contracts | ja (IC-1/IC-5/IC-6) |
| Datenfluss (Input→Transformation→Output→Persistenz) | ja |
| File Structure mit `Files:`-Ownership | siehe unten |
| Acceptance Criteria nummeriert, Given/When/Then, IC-zugeordnet (AC-1..AC-12) | ja |
| Offene Fragen + Risiken (OQ-1..OQ-4) | ja |
| ADRs (Context/Decision/Consequences) | ja (ADR-1..3) |
| Keine Platzhalter / keine erfundenen Zielwerte | ja (OQ-1/3 markiert) |
| Keine Rebaseline / kein Code / kein Sync in dieser Spec | ja |
| Jede AC mappt auf ≥1 IC | ja |

### File Structure (`Files:` Ownership; Detailplan :192-204, :208-214)
- Create `scripts/lib/agent_report.py` — IC-1 (Task 1.1)
- Modify `scripts/measure_context.py` — IC-2/IC-3 (Task 1.1): `--per-agent`
- Create `tests/test_agent_report.py` — IC-4 (Task 1.1)
- Create `tests/test_agent_budget_ratchet.py` — IC-5 (Task 1.4, #1244)
- Create `tests/test_template_rubric_lint.py` — IC-6 (Task 1.3, #885-Ersatz)
- Modify `docs/guides/features/agent-composition.md` — IC-7 (Task 1.5)
- Modify `.claude/skills/conventions/SKILL.md` — IC-8 (Task 1.5)
- Create `.tmp/plans/scratch/baseline-batch-0.json` — Laufzeit-Artefakt (Task 1.1, nicht eingecheckt)

Nicht angefasst: `tests/test_context_budgets.py`, `agents/**`, `config/role-defaults.yaml`, `templates/context/**`, Rebaseline-Dateien.

## Trace-Anker: spec-id: SPEC-AGENT-LOOP-BATCH0-2026-11-20

Referenzierbar über Pfad (Master :221 / Detail :208-214); der Plan nennt den spec-id-String nicht wörtlich, verweist aber über den Pfad `2026-11-XX-agent-improvement-loop-spec.md`. Approval-Marker: `Status: APPROVED (User, 2026-11-19 ...)` — keine neue Entscheidung, Spec nachgereicht auf Basis des approbierten Master-Plans.
