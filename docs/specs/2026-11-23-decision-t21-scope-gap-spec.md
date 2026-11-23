---
spec-id: SPEC-T21-SCOPE-GAP-1167-2026-11-23
title: "T21-Scope-Gap (Punkt 4) — Spec"
status: APPROVED
approval: "User, 2026-11-23, Einzelentscheidung"
date: 2026-11-23
branch: fix/decision-points-bundle-20261123
anchor: 278ba54f
related_issue: "#1167"
parent_spec: SPEC-REQ-ID-FORMAT-1167-2026-11-11
---

# T21-Scope-Gap (Punkt 4) — Spec

> Status: APPROVED (User, 2026-11-23, Einzelentscheidung)

## Problem / Ziel / Nicht-Ziele

**Entscheidung (bindend, 23.11.).** Alle `REQ-xxx`-Vorkommen in `agents/` per Grep messen; den #1167-Validator auf die vollständige gemessene Liste erweitern; Goldens nachziehen. Keine Implementierung in dieser Spec.

**Problem (Beleg).** Task 21 von #1167 hat REQ-Wording nur in einer Teilmenge der Agenten gegated. `tests/test_req_id_format.py:28-35` pinnt `GATED_AGENTS` auf 6 Rollen (`validator`, `bug-feature-analyzer`, `requirements`, `se-requirements`, `se-developer`, `api-specialist`); `req_format.py:15-18,73-89` prüft als Scope nur `docs/REQUIREMENTS.md`. Die ältere Kandidatenliste der Vorprüfung nannte ~18 Zeilen/~14 Dateien — die Neumessung unten ergibt **194 Treffer in 44 Dateien**. Falsche Scope-Liste erzeugt Render-/Golden-Drift (Risiko R1).

**Ziel.** Vollständige, reproduzierbare Scope-Liste; Validator/Gating deckt genau diese Liste ab; SE-Kaskade-Domäneninhalt bleibt unangetastet; Goldens byte-identisch nachgezogen.

**Nicht-Ziele.** Keine Änderung an `REQ_ID_PATTERN` (`^REQ-[A-Z][A-Z0-9]*-\d{2,3}$`) oder an `DOD_REQ_TRACEABILITY`-Semantik; keine Änderung an SE-Kaskade-Schema-Texten; kein #1167-Closing; keine neuen Config-Keys.

## Re-Messung @ 278ba54f (eigener Grep, nicht übernommen)

Muster `REQ-` über `agents/**/*.md`, Stand Branch `fix/decision-points-bundle-20261123 @ 278ba54f`: **194 Treffer in 44 Dateien** (strenges Token-Muster `REQ-[A-Za-z0-9-]+`: 184 Treffer/43 Dateien; Differenz = Platzhalter `REQ-<AREA>-<NN>` mit `<`/`>`).

| Datei (`agents/…`) | Treffer | Klasse |
|---|---|---|
| `2-platform/sharkord-developer.md` | 3 | D |
| `2-platform/sharkord-release.md` | 2 | D |
| `2-platform/homeassistant-documenter.md` | 1 | D |
| `1-generic/validator.md` | 6 | D |
| `1-generic/requirements.md` | 8 | D |
| `1-generic/bug-feature-analyzer.md` | 3 | D |
| `1-generic/junior-developer.md` | 3 | D |
| `1-generic/senior-developer.md` | 3 | D |
| `1-generic/principal-developer.md` | 3 | D |
| `1-generic/tester.md` | 7 | D |
| `1-generic/e2e-tester.md` | 2 | D |
| `1-generic/api-specialist.md` | 2 | D |
| `1-generic/git.md` | 2 | D |
| `1-generic/orchestrator.md` | 2 | D |
| `1-generic/ui-ux-designer.md` | 4 | D |
| `1-generic/database-engineer.md` | 1 | D |
| `1-generic/devops-engineer.md` | 1 | D |
| `1-generic/refactoring-specialist.md` | 1 | D |
| `1-generic/data-engineer.md` | 1 | D |
| `1-generic/documenter.md` | 1 | D |
| `1-generic/_reference-agent.md` | 3 | D |
| `1-generic/se-developer.md` | 6 | D+S |
| `1-generic/se-junior-developer.md` | 5 | D+S |
| `1-generic/se-senior-developer.md` | 3 | D+S |
| `1-generic/se-requirements.md` | 18 | S |
| `1-generic/se-component-requirements.md` | 45 | S |
| `1-generic/se-architect.md` | 5 | S |
| `1-generic/se-critic.md` | 5 | S |
| `1-generic/se-verifier.md` | 4 | S |
| `1-generic/se-validator.md` | 3 | S |
| `1-generic/se-test-engineer.md` | 2 | S |
| `1-generic/se-testreviewer.md` | 2 | S |
| `1-generic/se-termination.md` | 6 | S |
| `1-generic/se-interface-mgr.md` | 4 | S |
| `1-generic/se-integration-and-test-manager.md` | 12 | S |
| `1-generic/ideation.md` | 2 | N |
| `1-generic/developer.md` | 2 | N |
| `1-generic/planner.md` | 2 | N |
| `1-generic/ux-researcher.md` | 1 | N |
| `1-generic/risk-based-audit-planner.md` | 1 | N |
| `1-generic/product-manager.md` | 3 | N |
| `1-generic/concept-specifier.md` | 2 | N |
| `1-generic/concept-reviewer.md` | 1 | N |
| `1-generic/concept-architect.md` | 1 | N |

Klassen: **D** = DoD-Mandat-/Traceability-Wording (Gating-Scope; 24 Dateien, davon 3 gemischt). **S** = SE-Kaskade-Domäneninhalt (`REQ-L{level}-{NNN}`, `REQ-L1-SH`, `REQ-001`, `REQ-Dateien`, `REQ-Frontmatter-*`; 14 Dateien, davon 3 gemischt) — kein DoD-Mandat. **N** = neutrale Rollenbeschreibung/-abgrenzung (9 Dateien) — kein Mandat. Summe 194 / 44.

## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)

- **IC-1 — Scope-Liste.** `tests/test_req_id_format.py::GATED_AGENTS` (aktuell 6 Rollen, `:28-35`) → ersetzen durch die vollständige **D**-Menge aus der Messung (24 Rollen, inkl. `sharkord-developer`, `sharkord-release`, `homeassistant-documenter`, `tester`, `e2e-tester`, `git`, `orchestrator`, `ui-ux-designer`, `validator`, `requirements`, `bug-feature-analyzer`, `junior-developer`, `senior-developer`, `principal-developer`, `_reference-agent`, `api-specialist`, `database-engineer`, `devops-engineer`, `refactoring-specialist`, `data-engineer`, `documenter`, `se-developer`, `se-junior-developer`, `se-senior-developer`). Signatur: modulweises `tuple[str, ...]`. Fehlerpfad: fehlende D-Datei in der Liste → AC1 rot.
- **IC-2 — Gating.** Jedes D-Mandat in `agents/1-generic/*.md` und `agents/2-platform/*.md` liegt innerhalb `{{#if DOD_REQ_TRACEABILITY}}…{{else}}…{{/if}}`; bei an erscheint `REQ-<AREA>-<NN>` (kanonisch, `\d{2,3}`), bei aus kein REQ-Mandat. Die gemessenen D-Stellen (u. a.) sind nach Funktion getrennt:
  - **REQ-Mandate (müssen gegated sein):** `validator.md:38,39`; `tester.md:40,43,44,49`; `e2e-tester.md:67`; `requirements.md:44,47`; `_reference-agent.md:174`; `sharkord-developer.md:92,96` (im Ist-Stand teils bereits im `{{#if}}`-Block, teils noch ungated — alle sind Prüfziel für AC2).
  - **Deskriptive REQ-Erwähnungen (kein Mandat, dürfen ungated bleiben):** `validator.md:4,137`; `requirements.md:4,5,102`; `e2e-tester.md:105`; `orchestrator.md:250`; `git.md:146`; `documenter.md:33`; `homeassistant-documenter.md:60`; `sharkord-developer.md:6`; `sharkord-release.md:121,124`.
  Fehlerpfad: verbliebenes ungatedes D-`REQ-xxx`-Mandat im gerenderten Text → Fehler (AC2), nachgewiesen durch den Render-Scan `tests/test_req_id_format.py::test_render_all_gated_agents_no_ungated_req_mandate` über alle 24 D-Rollen.
- **IC-3 — SE-Domäneninhalt (Schutz).** Alle **S**-Treffer bleiben unverändert und werden weder gegated noch dem Format-Check unterworfen. `REQ_L{level}`, `REQ-L1-SH`, `REQ-001-03`, `REQ-L2-AT-018` sind Domänenstrings; einEinbeziehen in `check_req_ids` würde `Severity.ERROR`-Fehlalarme erzeugen (Pattern `^REQ-[A-Z][A-Z0-9]*-\d{2,3}$` lehnt `REQ-L1-SH`/`REQ-L2-AT-018` ab). Fehlerpfad: geänderter S-Text oder S im Validator-Scope → AC3 rot.
- **IC-4 — Validator-Format.** `scripts/lib/consistency/req_format.py::REQ_ID_PATTERN` (`:32`) bleibt byte-identisch `r"^REQ-[A-Z][A-Z0-9]*-\d{2,3}$"`; `check_req_ids(...) -> List[Finding]` (`:92-96`) unverändert. Scope-Erweiterung betrifft ausschließlich die Gating-/Coverage-Liste (IC-1), nicht die Regex. Fehlerpfad: Regex gelockert → AC4 rot.
- **IC-5 — Goldens.** Rebaseline via `tests/test_rebaseline_helper.py` erlaubter Pfad-Set (`:257-265`): `tests/fixtures/slimming-golden/*.md`, `tests/fixtures/ac01-baseline/hashes.json`, `tests/fixtures/compact-golden/*.md`, `tests/fixtures/topology-golden/*`, `.meta-config/generated-file-hashes.json`, `.meta-config/context-hashes.json`, `tests/test_context_budgets.py`. Nach Gating-Änderung neu erzeugen; alte Werte sind ungültig. Fehlerpfad: Gold-Drift → AC5 rot.

## Datenfluss

Grep-Messung (`agents/**/*.md`, Muster `REQ-`, 194/44) → Klassifikation D/S/N (oben) → Scope-Liste `GATED_AGENTS` = D-Menge → Template-Gating `{{#if DOD_REQ_TRACEABILITY}}` in D-Dateien → `scripts/sync.py`-Render → `.claude/agents/` (nicht im Repo) → Rebaseline-Helper schreibt Goldens/Hashes → `python3 scripts/sync.py --validate` + `python3 -m pytest tests/test_req_id_format.py tests/test_rebaseline_helper.py -q`. S/N-Dateien bleiben außerhalb des Flusses.

## Acceptance Criteria (nummeriert, testbar)

1. **AC1 — vollständiger Scope (IC-1).** Given die gemessene 194/44-Liste, When `tests/test_req_id_format.py::GATED_AGENTS` gelesen wird, Then enthält sie exakt die 24 D-Rollen (Obermenge der alten 6) und keine S-/N-Rolle; jede D-Datei aus der Tabelle ist vertreten.
2. **AC2 — Gating korrekt (IC-2).** Given Sync mit `rapid-prototyping` (`DOD_REQ_TRACEABILITY=false`) bzw. mit Traceability an, When alle 24 D-Agenten gerendert werden, Then enthält der aus-Zustand kein ungatedes `REQ-xxx`/`REQ-<AREA>-<NN>`-Mandat und der an-Zustand das kanonische Format `REQ-<AREA>-<NN>`; Nachweis durch den Render-Scan `tests/test_req_id_format.py::test_render_all_gated_agents_no_ungated_req_mandate` (iteriert über alle `GATED_AGENTS`, prüft den gerenderten aus-Zustand auf ungatede Mandat-Strings) sowie die bestehenden `test_render_rapid_prototyping_has_no_req_mandate` und `test_render_traceability_on_shows_canonical_format` — alle grün für alle D-Rollen.
3. **AC3 — SE-Inhalt geschützt (IC-3).** Given die 14 S-Dateien, When Gating/Validator laufen, Then sind deren `REQ-`-Strings byte-identisch unverändert, `check_req_ids` meldet dafür keine `req-id.format`-Findings, und `REQ-L1-SH`/`REQ-L2-AT-018` werden nicht als gültige DoD-IDs ausgegeben.
4. **AC4 — kein Format-Regress (IC-4).** Given `REQ_ID_PATTERN == r"^REQ-[A-Z][A-Z0-9]*-\d{2,3}$"`, When `python3 -m pytest tests/test_req_id_format.py -q` und `python3 scripts/sync.py --validate` laufen, Then sind alle Tests grün, die Konstante byte-identisch, `REQ-CMD-01`/`REQ-COM-123` gültig, `REQ-1`/`REQ-COM-1234`/`REQ-L2-AT-018` ungültig, und es gibt keine neuen Findings.
5. **AC5 — Goldens byte-identisch (IC-5).** Given die nachgezogenen Goldens, When `tests/test_rebaseline_helper.py` und die Render-Identity-/Budget-Tests laufen, Then stimmen alle Golden-Dateien byte-identisch mit dem frischen Render überein und der Helper-Preflight meldet keinen unerlaubten Pfad.

Je AC ≥1 Interface Contract: AC1→IC-1, AC2→IC-2, AC3→IC-3, AC4→IC-4, AC5→IC-5.

## Offene Fragen + Risiken

**Auslegung der bindenden Nutzervorgabe (transparent dokumentiert, Entscheidung bereits getroffen).**
- **F1 — SE-Kaskade-Domäneninhalt (RESOLVED im Validator-Kontext).** Die bindende Nutzervorgabe vom 23.11. („alle `REQ-xxx`-Vorkommen in `agents/` messen, den #1167-Validator auf die vollständige Liste erweitern, Goldens nachziehen") wird hier im Kontext des **#1167-DoD-`req-traceability`-Validators** ausgelegt: „alle Agenten abdecken" meint alle Agenten, die DoD-Mandat-`REQ-IDs` tragen — die 24-Dateien-**D**-Menge (IC-1). SE-Kaskade-Domäneninhalt (`REQ-L{n}`, `REQ-L1-SH`, `REQ-001-03`, `REQ-L2-AT-018`; **S**-Klasse, 14 Dateien) und neutrale Rollenbeschreibung (**N**-Klasse, 9 Dateien) sind keine DoD-Mandate und bleiben daher außerhalb von Gating und Validierung. Technischer Grund: der kanonische `REQ_ID_PATTERN` `^REQ-[A-Z][A-Z0-9]*-\d{2,3}$` lehnt `REQ-L1-SH`/`REQ-L2-AT-018` ab; ein Einbeziehen in `check_req_ids` würde `Severity.ERROR`-Fehlalarme erzeugen und `tests/test_req_id_format.py::test_render_traceability_on_shows_canonical_format` (`:147-152`) brechen, das für alle `GATED_AGENTS` genau dieses kanonische Format erwartet. Dies ist eine transparente Auslegung der bereits getroffenen Nutzervorgabe in ihrem Validator-Kontext — keine neue Produktentscheidung und keine offene Rückfrage. Die 14 S-Dateien werden bewusst nicht gegated/validiert (Schutz von #339/#1167-Format).
- **F2 — N-Klasse.** 9 Dateien enthalten nur Rollenbeschreibung/Abgrenzung (z. B. „Do not assign REQ-IDs"). Empfehlung: unverändert lassen (kein Mandat). Keine Eskalation nötig, aber dokumentiert.

**Risiken.**
- R1: Falsche Scope-Liste → Render-/Golden-Drift. Mitigation: AC1 + AC5 gegen die Neumessung.
- R2: S-String wird versehentlich gegated → #339-Domänenbruch / Fehlalarme. Mitigation: IC-3 + AC3.
- R3: Anker-Drift — alle file:line-Belege gegen `278ba54f` gemessen; ältere Kandidatenliste war unvollständig. Mitigation: Neumessung oben ist autoritativ.
- R4: Regex-Lockerung aus Bequemlichkeit. Mitigation: IC-4 + AC4 (byte-identisch).

**ADR (Kontext / Entscheidung / Konsequenz).**
- ADR-1 (Vollständige Messung): Kontext — T21 gatede nur 6 Rollen. Entscheidung — Grep-Messung ist autoritative Scope-Quelle (194/44). Konsequenz — `GATED_AGENTS` = D-Menge (24).
- ADR-2 (Domäneninhalt-Schutz): Kontext — SE-Kaskade-`REQ-`-Strings sind keine DoD-Mandate. Entscheidung — S-Klasse bleibt unangetastet und außerhalb des Validators. Konsequenz — keine Fehlalarme, #1167-Format bleibt intakt; F1 im Validator-Kontext als RESOLVED dokumentiert (siehe Offene Fragen), keine offene Rückfrage.
- ADR-3 (Golden-Rebaseline): Kontext — Gating ändert gerenderten Text. Entscheidung — Goldens über den erlaubten Helper-Pfad neu pinnten. Konsequenz — byte-identische Render-Identity, kein Drift.

## Trace-Anker: spec-id: SPEC-T21-SCOPE-GAP-1167-2026-11-23
