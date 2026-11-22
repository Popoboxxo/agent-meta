---
spec-id: SPEC-CONTEXT-TOKEN-1161-2026-11-11
title: Kontext-Token-Reduktion (#1161 Punkt 2) — Full-Profil-Agentverzeichnis nur ohne eigene Agent-Liste
status: APPROVED
plan: docs/superpowers/plans/2026-11-11-phase-h-context-eval.md (Task 8, Entscheidung 29, Abweichung 15)
builds-on: SPEC-CONTEXT-PROFILES-2026-10-11
related-spec: SPEC-HOOK-SINGLE-PARSE-2026-11-11 (Punkt 5 / hook_json_get_many, Phase D, separat)
---

# Kontext-Token-Reduktion (#1161 Punkt 2) — Spec

> Status: APPROVED (Nutzergo 22.11 — Spezifikation auf Basis des freigegebenen Phasenplans 2026-11-11-phase-h-context-eval.md nachgetragen, keine neue Entscheidung)
> Basis: Workstream A (Phase H), Branch `chore/phase-h-bundle` @ `87564958`. Der Plan maß seine Anker 2026-11-11 gegen `9aa0e0c0`; diese Spec misst alle file:line-Anker erneut gegen `87564958` (Drift siehe Risiko R1).
> Gate: Diese Spec ist das Freigabe-Gate für Task 10b. Ohne obige `Status: APPROVED`-Zeile ist Task 10b nicht ausführbar (Plan Task 8, Akzeptanz).

## Problem / Ziel / Nicht-Ziele

**Problem.** Im Default-Profil `full` rendert `templates/context/agents-managed.md` die Agent-Tabelle (`{{> agents-table }}`) unbedingt — auch für Provider, deren Harness eine eigene Agent-Liste bereitstellt (`roster_in_harness: true`). Das dupliziert das Agent-Verzeichnis in der Kontextdatei und erzeugt unnötige Tokens (Issue #1161 Punkt 2). Im Compact-Profil ist dieselbe Roster bereits über `EMIT_AGENT_ROSTER` gated; im Full-Profil fehlt dieses Gate.

**Ziel.** Den Full-Profil-Zweig an dieselbe vorhandene Variable `EMIT_AGENT_ROSTER` hängen, sodass das Agent-Verzeichnis nur für Provider ohne eigene Agent-Liste in die Kontextdatei rendert (Entscheidung 29 / D-H2). Kein neues Flag, kein Provider-Namens-Branching, kein Eingriff in `scripts/lib/context.py`.

**Scope.** Nur `templates/context/agents-managed.md` (Full-Zweig) sowie die davon abhängigen Fixtures (`tests/fixtures/ac01-baseline/hashes.json`, `tests/test_context_budgets.py`) in der umsetzenden Task 10b. Keine Änderung an `config/provider-capabilities.yaml`, `scripts/lib/context.py`, Hooks oder Provider-Configs.

**Nicht-Ziele.**
- #1161 Punkt 5 (`hook_json_get_many`, Fail-closed, bash 3.2, Spawn-Zahl): Owner ist Phase D, spezifiziert in `docs/specs/2026-11-11-hook-single-parse-spec.md` (`spec-id: SPEC-HOOK-SINGLE-PARSE-2026-11-11`, APPROVED 2026-11-15) und dort gemergt. Hier nur Querverweis, keine Neuspezifikation. H-Task 10 (Rest-Hooks) und Task 9 (Abnahme) bleiben unberührt.
- Keine Änderung an `scripts/lib/context.py`: `EMIT_AGENT_ROSTER` wird bereits unbedingt berechnet (Abweichung von der Annahme im C-1086i-Plan, die einen Eingriff vermutet hatte; siehe Plan Abhängigkeitstabelle).
- Kein neues Capability-Flag: `roster_in_harness` existiert bereits (Abweichung 15, O-H1 erledigt).
- Keine Änderung der Toleranzkonstanten in `tests/test_context_budgets.py` (`TOLERANCE_MIN_BYTES = 256`, `TOLERANCE_RATIO = 0.02`, `TOLERANCE_MAX_BYTES = 4096`, Zeilen 46-48).
- Kein Eingriff in `config/ai-providers.yaml` oder `.meta-config/project.yaml` (Entscheidung 56: G vor H; H ändert diese Dateien nicht).
- Keine kostenpflichtigen Läufe (Entscheidung 11). Keine Closing-Keywords in Commit-/PR-Texten (Entscheidung 38e); `(#1161)` ist reiner Verweis.

## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)

Alle Anker gegen `87564958` nachgemessen. Python 3.9-kompatibel, provider-agnostisch (Provider-Unterschiede ausschließlich über den Config-Key `roster_in_harness`, kein `if provider == "Name"`).

### IC-1 — Template-Änderung (einzige Verhaltensänderung)

- Datei: `templates/context/agents-managed.md:20-21` (Anker unverändert gegenüber Plan).
- Ist (Stand `87564958`):
  ```
  {{#if CONTEXT_PROFILE_COMPACT}}{{#if EMIT_AGENT_ROSTER}}{{> agents-list-compact }}
  {{/if}}{{else}}{{> agents-table }}{{/if}}
  ```
  Der Compact-Zweig ist an `EMIT_AGENT_ROSTER` gebunden; der Full-Zweig (`{{else}}`) rendert `{{> agents-table }}` unbedingt.
- Soll: Full-Zweig ebenfalls an `EMIT_AGENT_ROSTER` binden, z. B.:
  ```
  {{#if CONTEXT_PROFILE_COMPACT}}{{#if EMIT_AGENT_ROSTER}}{{> agents-list-compact }}
  {{/if}}{{else}}{{#if EMIT_AGENT_ROSTER}}{{> agents-table }}{{/if}}{{/if}}
  ```
  Semantik: `EMIT_AGENT_ROSTER = "false"` → kein Agent-Verzeichnis im Full-Profil; `"true"` → unverändertes Rendering. Der Compact-Zweig bleibt byte-identisch.
- Partial `templates/context/partials/agents-table.md:5-8` (Markdown-Tabelle über `active_agents_table`) wird nicht geändert; `templates/context/partials/agents-list-compact.md:5-6` nicht geändert.
- Fehlerpfade: keine neuen. Fehlt `EMIT_AGENT_ROSTER` im Render-Kontext, greift der heutige Template-Fallback; die unbedingte Erzeugung der Variable ist in IC-2 belegt.

### IC-2 — `EMIT_AGENT_ROSTER` (bestehend, keine Änderung)

- `scripts/lib/context.py:2860-2871` (Plan: `:2777-2786`, Anker driftet): `local_vars["EMIT_AGENT_ROSTER"] = "true" if resolve_shared_emit_roster({user: (_roster_caps.get(user) or {}).get("roster_in_harness") is True for user in _roster_users}) else "false"`. Die Variable wird unbedingt je Render berechnet; eine Änderung ist nicht nötig.
- `scripts/lib/context_profile.py:150-168`, Signatur `resolve_shared_emit_roster(roster_by_provider: Mapping[str, bool]) -> bool`: Safe-Side-Regel — `True` (Roster emitieren), sobald mindestens ein Sharer `roster_in_harness=false` ist; `False`, wenn alle Sharer `true` sind; leere Mapping → `True` (dokumentiert in `:159-163`).
- Semantik laut Kommentar `context.py:2855-2859`: `EMIT_AGENT_ROSTER` ist das *Emit*-Prädikat (`"true"` = Liste bleibt, `"false"` = Harness owns the roster) und bewusst **nicht** das invertierte `ROSTER_IN_HARNESS`-Literal des Orchestrator-Templates.
- Config-Quelle: `config/provider-capabilities.yaml`, Key `roster_in_harness`. Kein Provider-Name im Code-Pfad.

### IC-3 — Betroffene Provider (Evidenztabelle, Abweichung 15)

`roster_in_harness` in `config/provider-capabilities.yaml` (Stand `87564958`; Plan-Anker in Klammern, alle driftet). Provider-Identitäten und Werte unverändert gegenüber dem Plan:

| Provider | Sektion | `roster_in_harness` | Flag-Zeile (Plan) | EMIT bei Einzelanbieter |
|---|---|---|---|---|
| Claude | :129 | true | :159 (:140) | false |
| Opencode | :189 | true | :220 (:199) | false |
| Mammouth | :452 | true | :481 (:452) | false |
| Codex | :526 | true | :557 (:526) | false |
| ZCode | :601 | true | :632 (:599) | false |
| KimiCode | :672 | true | :702 (:667) | false |
| Gemini | :249 | false | :279 (:256) | true |
| Continue | :318 | false | :347 (:322) | true |
| Copilot | :381 | false | :410 (:383) | true |

- Der Full-Render ändert sich nur dort, wo `EMIT_AGENT_ROSTER = "false"` gilt, also für die sechs `true`-Provider (bei Einzelanbieter-Kontextdateien). Für die drei `false`-Provider bleibt das Rendering identisch.
- Geteilte Kontextdateien (Safe-Side): für die gemeinsame `AGENTS.md` der sechs Sharer (`tests/test_context_budgets.py:628`, `_AGENTS_MD_PROVIDERS`) gilt `EMIT = true`, sofern einer der aktiven Sharer `roster_in_harness=false` hat (z. B. Gemini) — dann bleibt die Tabelle auch im Full-Profil erhalten. Die Messung je Provider entscheidet (AC-3); es wird keine konkrete Byte-Änderung angenommen.

### IC-4 — Re-Pin-Flächen (Task 10b, nicht Gegenstand dieser Spec-Änderung selbst)

- `tests/fixtures/ac01-baseline/hashes.json`: Kontextdateien sind gepinnt — `Claude/CLAUDE.md` (:164), `Codex/AGENTS.md` (:265), `Gemini/AGENTS.md` (:706), `KimiCode/AGENTS.md` (:806), `Mammouth/AGENTS.md` (:931), `Opencode/AGENTS.md` (:1059), `ZCode/AGENTS.md` (:1187). Nur Einträge neu pinnen, deren gerendertes Artefakt messbar abweicht, mit dokumentiertem Grund (Globale Constraint Plan Z. 93: kein Neu-Einfrieren, um einen roten Test zu löschen).
- `tests/test_context_budgets.py`: `_IST_FULL` (:306; Plan :300), `_IST_COMPACT` (:609; Plan :583), `FULL_BUDGET_CEILINGS` (:323-326), `COMPACT_BUDGET_CEILINGS` (:621-624), `_ceiling(ist)` (:319-320). Re-Pin-Plan in AC-5; Toleranzkonstanten (:46-48) bleiben unverändert.
- Messpunkt: `scripts/lib/context_report.py:130`, `measure_artifacts(project_root, active_providers, capabilities) -> dict` mit den Artefakten `entry-file`, `rules`, `orchestrator`, `harness-roster` (nur bei `roster_in_harness`) und `always-loaded` (`context_report.py:144-147, 156-183`). Der Helper `scripts/measure_context_repin.py` entsteht in Task 6 und ist hier nur Konsument.

## Datenfluss

`config/provider-capabilities.yaml::roster_in_harness` → `load_provider_capabilities` (`context.py:2860`) → `resolve_shared_emit_roster` (`context_profile.py:150`, Safe-Side über `shared_users`, `context.py:2861-2871`) → `local_vars["EMIT_AGENT_ROSTER"]` → `templates/context/agents-managed.md:20-21` (Full-Zweig, neu gated) → gerenderte Kontextdatei (`CLAUDE.md` / `AGENTS.md`) → `measure_artifacts` (`context_report.py:130`) → Pins in `tests/test_context_budgets.py` und `tests/fixtures/ac01-baseline/hashes.json`. Neue Warnungen oder Fehlerpfade entstehen nicht.

## Acceptance Criteria (nummeriert, testbar)

Der Plan nennt keine numerischen Byte-Ziele für diese Änderung → alle Größenangaben sind "zu messen" (Vorher/Nachher-Messung auf Basis `87564958`, Plan Task 8 Step 1). Given/When/Then verkürzt.

- **AC-1** (IC-1): Given ein Projekt mit `roster_in_harness: true` und `context-profile: full`, When der Sync die Kontextdatei rendert, Then enthält das gerenderte Artefakt keine `Agent | Core Capabilities`-Tabelle (Partial `agents-table.md`) mehr. Bei `roster_in_harness: false` ist die Tabelle weiterhin vorhanden.
- **AC-2** (IC-1, Compact-Parität): Given `context-profile: compact`, When gerendert wird, Then ist der Output byte-identisch zum Stand vor dieser Änderung (Compact-Zweig unverändert; `EMIT_AGENT_ROSTER` steuert `agents-list-compact` wie heute).
- **AC-3** (IC-2/IC-3, Render-Größe je Provider): Given `measure_artifacts` vor und nach der Änderung für jeden der neun Provider im Full-Profil, When die Werte verglichen werden, Then ist `entry-file` (und damit `always-loaded`) für jeden Provider mit `EMIT_AGENT_ROSTER = "false"` kleiner oder gleich dem Vorher-Wert und für Provider mit `EMIT = "true"` unverändert. Die konkreten Delta-Werte sind **zu messen** und in der PR-Notiz je Provider zu dokumentieren; ein im Plan festgelegtes Ziel existiert nicht.
- **AC-4** (IC-2, Safe-Side): Given eine geteilte Kontextdatei mit mindestens einem aktiven Sharer mit `roster_in_harness: false`, When `resolve_shared_emit_roster` mit dieser Sharer-Menge läuft, Then ist das Ergebnis `True` und die Full-Tabelle bleibt erhalten. Given alle Sharer `true`, Then `False` und die Tabelle entfällt.
- **AC-5** (IC-4, Re-Pin): Given die gemessenen Abweichungen aus AC-3, When Task 10b die Fixtures aktualisiert, Then sind nur tatsächlich abweichende Einträge in `hashes.json` und in `_IST_FULL`/`_IST_COMPACT` neu gepinnt, jeweils mit dokumentiertem Grund; `python3 -m pytest tests/test_context_budgets.py tests/test_ac01_render_identity.py -q` ist grün; `TOLERANCE_*` (:46-48) bleibt unverändert.
- **AC-6** (Gate): Given diese Spec-Datei, When geprüft wird, Then enthält sie die Zeile `Status: APPROVED` (Approval-Marker oben) und `python3 scripts/sync.py --validate` meldet gegenüber dem Ausgangsstand keinen neuen Fehler. Ohne die Zeile ist Task 10b nicht ausführbar (Plan Task 8 Akzeptanz).
- **AC-7** (Punkt-5-Abgrenzung): Given diese Spec, When nach `hook_json_get_many` gesucht wird, Then enthält sie keinen Interface-Vertrag dafür; der Vertrag liegt in `docs/specs/2026-11-11-hook-single-parse-spec.md` (`SPEC-HOOK-SINGLE-PARSE-2026-11-11`), ist dort APPROVED und gemergt. Kein doppelter H-Commit.

## Offene Fragen + Risiken

**Offene Fragen (fachlich): keine.** Flag-Name, Provider-Liste, Änderungsort und Safe-Side-Regel sind im Plan und im Code belegt (Abweichung 15, O-H1 erledigt, Entscheidung 29). Es wurde keine Entscheidung über den Plan hinaus getroffen.

**Plan-Ambiguitäten (bekannt, nicht neu entschieden).**
- *Identifikator:* Der Plan nennt für Task 8 keinen `spec-id`-Wert. Der hier verwendete Wert `SPEC-CONTEXT-TOKEN-1161-2026-11-11` folgt der Konvention der Schwester-Specs (`SPEC-CONTEXT-PROFILES-2026-10-11`, `SPEC-PHASE-C-SYNC-CONFIG-2026-11-11`); er ist ein Identifikator, keine technische Entscheidung.
- *Task-8-Step-1-Messungen:* Der Plan fordert zusätzlich einen Tokenproxy von `rules/1-generic/branch-guard.md` (Punkt 3-Rest) und den `name_index`-Anteil (`agents.py:364`). Dies ist Bestandsaufnahme/Evidenzhinweis, kein Vertragsgegenstand von Punkt 2; diese Spec übernimmt es als Hinweis (Risiko R2), ohne Anforderungen daraus abzuleiten.
- *Reihenfolge:* Task 10b läuft laut Entscheidung 56 erst nach G-Merge. Diese Spec (Task 8) ist davon unberührt und steht als Gate bereit; die Umsetzung folgt der Plan-Reihenfolge.

**Risiken.**
- **R1 (Anker-Drift):** Alle Plan-Anker (Basis `9aa0e0c0`) wurden gegen `87564958` neu gemessen und weichen teils deutlich ab: `context.py` Roster-Block `:2777-2786` → `:2860-2871`; `_IST_FULL` `:300` → `:306`; `_IST_COMPACT` `:583` → `:609`; Capability-Flags `:140/:199/:256/:322/:383/:452/:526/:599/:667` → `:159/:220/:279/:347/:410/:481/:557/:632/:702`. Nach Phase C/D/G erneut messen (Roadmap §4 Freshness-Check).
- **R2 (Punkt 3/Punkt 1 nicht verifiziert):** Der Plan vermerkt selbst, dass `name_index`-Duplikate und die Token-Zahlen des Issues nicht nachgemessen wurden; Task 8 Step 1 fordert eine Messung unter `.tmp/` (nicht committen). Diese Spec enthält bewusst keine Zahl dafür.
- **R3 (Golden-Drift):** Das Entfernen der Agent-Tabelle verändert gerenderte Kontextdateien → ac01-Hashes und Budget-Pins müssen mit Grund neu gesetzt werden (AC-5); ein Löschen des roten Tests ohne Messung ist unzulässig (Globale Constraint Z. 93).
- **R4 (Geteilte Datei):** Die Safe-Side-Regel kann den Effekt auf gemeinsamen `AGENTS.md`-Dateien neutralisieren; AC-3/AC-4 verlangen deshalb Messung je Provider statt einer pauschalen Annahme.

**ADR (Kontext / Entscheidung / Konsequenz).**
- **ADR-1 (Gate-Ort):** Kontext — Compact-Zweig gated die Roster bereits, Full-Zweig nicht; `EMIT_AGENT_ROSTER` wird unbedingt berechnet. Entscheidung — nur den Full-Zweig von `agents-managed.md:20-21` an die vorhandene Variable hängen, `context.py` nicht anfassen (Entscheidung 29). Konsequenz — minimale Render-Änderung, kein API-Wechsel, Re-Pin nur in Fixtures.
- **ADR-2 (Kein neues Flag):** Kontext — O-H1/Abweichung 15 belegen `roster_in_harness` im Code. Entscheidung — vorhandenes Flag und vorhandene Variable nutzen, kein Provider-Namens-Branching. Konsequenz — provider-agnostisch, kein Eingriff in `config/provider-capabilities.yaml`.
- **ADR-3 (Punkt 5 außer Scope):** Kontext — `hook_json_get_many` ist Phase D, APPROVED und gemergt. Entscheidung — nur verlinken (`SPEC-HOOK-SINGLE-PARSE-2026-11-11`), nicht neu spezifizieren. Konsequenz — kein Duplicate, H-Task 10 bleibt unabhängig.

**Entscheidungsverweise.** 11 (keine kostenpflichtigen Läufe); 28 (Punkt 5 → Phase D); 29 / D-H2 (Full-Zweig an `roster_in_harness`); 38e (keine Closing-Keywords); 52 (H1/H2-Schnitt); 56 / O-H7 (G vor H, betrifft nur Task 10b); O-H1 (Flag vorhanden).

## Trace-Anker: spec-id: SPEC-CONTEXT-TOKEN-1161-2026-11-11
