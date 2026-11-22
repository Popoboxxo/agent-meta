---
spec-id: SPEC-EVIDENCE-DISCIPLINE-1014-2026-11-11
title: "Evidence Discipline (#1014) — Spec (Issue #1014, Phase H Task 0)"
status: APPROVED
date: 2026-11-22
approval: "Nutzergo 22.11 — Spezifikation auf Basis des freigegebenen Phasenplans 2026-11-11-phase-h-context-eval.md nachgetragen, keine neue Entscheidung"
issues: "#1014"
plan: docs/superpowers/plans/2026-11-11-phase-h-context-eval.md
plan_task: 0
concept: docs/concepts/evidence-discipline-1014.md
branch: chore/phase-h-bundle
ist_anchor: "4d3d21f5 (Re-Messung 2026-11-22; #778-Konzept 87564958, Plan-Review origin/main 9aa0e0c0)"
klasse: "XL — Gate-Artefakt; Umsetzung in vier Folgeplaenen gemaess Entscheidung 52 (H2)"
---

# Evidence Discipline (#1014) — Spec

> Status: APPROVED (Nutzergo 22.11 — Spezifikation auf Basis des freigegebenen Phasenplans `2026-11-11-phase-h-context-eval.md` nachgetragen, keine neue Entscheidung)
> Datum: 2026-11-22 | Ist-Anker: Arbeitsstand `chore/phase-h-bundle @ 4d3d21f5` (Historic: `#778`-Konzept `87564958`, Plan-Review `origin/main 9aa0e0c0`) | Plan: `docs/superpowers/plans/2026-11-11-phase-h-context-eval.md` Task 0 (Z. 325–332) | Konzept: `docs/concepts/evidence-discipline-1014.md`
> Issue: #1014 (XL, Gate Task 0). Diese Spec wurde nachgetragen; Implementierung entsteht ausschliesslich in vier Folgeplaenen (H2, Entscheidung 52 / O-H8). **Keine kostenpflichtigen Laeufe ohne Kostenschaetzung und ausdrueckliches User-Ja** (Plan Z. 91).

## Problem / Ziel / Nicht-Ziele

**Problem.** #1014 verlangt eine querschnittliche Evidence-Discipline ueber generische Rollen-Templates (Plan-Scope Z. 30: 34 Rollen, 8 Muster, 4 PRs). Der freigegebene Phasenplan macht Konzept und Spec zum H1-Gate (Z. 70) und verweist die Umsetzung in Folgeplaene. Die Issue-Datei `.tmp/issues/1014.md` ist im Checkout nicht vorhanden (Glob `**/*1014*`: 0 Treffer), ebenso `UEBERGREIFENDE-MUSTER.md` (Plan Z. 328, Z. 471). Damit sind Rollenlisten je Muster und der genaue Issue-Wortlaut nicht verifizierbar.

**Ziel.** Diese Spec legt die verbindlichen Schnittstellen, den Datenfluss und testbare Akzeptanzkriterien fuer die vier Folgeplaene fest: Step 1 (P5+P7), Step 2 (P1), Step 3 (P3+P4), Step 4 (P2+P6+P8) — je ein Folgeplan, nicht Teil des Phasenplans, laut Entscheidung 52 in H2. Sie uebernimmt die Dedupe-Regel gegen expandierten Text, die Dateilisten und Pruefkommandos aus Plan Z. 328–329, die Golden-Fixture-Regel aus Z. 93 und die Kostenregel aus Z. 91.

**Nicht-Ziele.**
- Keine Template-, Config-, Hook-, Test- oder Generator-Aenderung in diesem Gate; kein Implementierungsplan und kein Code.
- Keine Erfindung von Rollenlisten, Muster-Namen, Satztexten, Versionsnummern, Kostenwerten oder Zielzahlen. Fehlende Issue-Werte sind "to be determined in the follow-up plan".
- Kein automatisierter LLM-/Agent-/Eval-Lauf; kein Kostenwert wird genannt.
- Keine Schliessung von #1014, keine REQ-ID, keine Wiederholung oder Aenderung der #778-Dispositionen, keine erneute Oeffnung von PR #1013, keine Closing-Keywords (Z. 89).

## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)

Die Contracts beschreiben die Oberflaechen, die die Folgeplaene **verwenden**; diese Spec aendert keine davon. `(Datei:Symbol, Signatur, Fehlerpfad)`.

- **IC-0 — Gate-Artefakte.** `docs/concepts/evidence-discipline-1014.md` und `docs/specs/2026-11-11-evidence-discipline-1014-spec.md` : `Status: APPROVED` (maschinenlesbar) + `spec-id:` im Spec-Kopf und im Trace-Anker. Signatur: zwei vorhandene Markdown-Dateien; Spec-Kopf `status: APPROVED`. Fehlerpfad: fehlt der APPROVED-Marker, darf kein Plan und keine Implementierung entstehen (Plan Z. 39, Z. 87).
- **IC-1 — Generator-Frischepruefung.** `scripts/gen_promptfoo_config.py:main` — `main(argv: list[str]) -> int`; `--check`: „exit 1 if it would change" (`:21`), Flag-Auswertung `:93`. Erfolg: Exit 0 bei unveraendertem Output. Fehlerpfad: Exit 1 = Drift; der betroffene Folgeplan ist blockiert, bis die generierte Konfiguration nachgefuehrt ist.
- **IC-2 — Verhaltens-Eval-Katalog.** `tests/routing-llm-eval/catalog.behavior.yaml:cases` (`:15`) — Liste von Cases mit `id`, `role`, `prompt`, `category` sowie `expected_any` (Regex-Liste), `expected_all` (Literal-Liste), `forbidden` (Literal-Liste); Feldbedeutung `:1-10`. Auswertung in `tests/routing-llm-eval/run_eval.sh` (`:10`), Wiederholung via `REPEAT=1`. Fehlerpfad: ungueltiges Feld oder nicht ladbarer Case = Eval nicht auswertbar. Judge-basierte `llm-rubric`-Asserts sind bewusst **nicht** Teil dieser Datei (`:12-14`); ihre Einfuehrung waere eine neue Entscheidung.
- **IC-3 — Rollen-Templates.** `agents/1-generic/<role>.md` : YAML-Frontmatter mit `name`, `version`, `description`, `tools` (Projektkonvention, `AGENTS.md`). Signatur der Aenderung: eine Evidence-Aussage im Template-Body + erhoehte Frontmatter-`version:` je betroffener Rolle; konkrete Rollen, Zielversionen und Hoehe des Bumps sind "to be determined in the follow-up plan" (gemaess den registrierten Konventionen der `conventions`-Skill; keine neue Versionsregel in dieser Spec). Fehlerpfad: `tests/test_agents_frontmatter.py` rot = Blocker.
- **IC-4 — Golden-Fixture-Freeze.** `tests/fixtures/slimming-golden/` : eingefrorene gerenderte Rollen-Dateien. Signatur: Freeze-Point „after Block A (commit `62876f49`), before Block B" (`README.md:16-20`), aktiver Satz `_GOLDEN_ROLE_COUNT` = 58 (`README.md:36-41`), B2-Gate in `tests/test_template_slimming_equivalence.py`, Rebaseline nur mit dokumentiertem Grund und Diff-Manifest-Eintrag (`README.md:90-94`). Fehlerpfad: Rebaseline ohne Manifest-Eintrag entwertet das B2-Gate (Plan Z. 93).
- **IC-5 — Substitutions-Expansion.** `scripts/lib/config.py:variables["PROMPT_INJECTION_DEFENSE_BLOCK"]` (`:3435-3437`) — Aufbau aus `snippets/security/prompt-injection-defense.md` (`:3433-3436`), leerer String bei fehlender Datei (`:3436`); Registrierung in `scripts/lib/consistency/placeholders.py:130`; Dokumentation `docs/guides/features/sync-concept.md:287`. Fehlerpfad: fehlendes Snippet → leere Variable → Dedupe-False-Negative; Pruefung daher am expandierten Text.
- **IC-6 — Dedupe-Pruefflaeche.** Expandierter Agenten-Text (Sync-/Render-Pfad), nicht Template-Rohtext. Signatur: fuer jeden Muster-Satz gilt „bereits vorhanden", wenn er im expandierten Text einer Rolle vorkommt — u. a. nach Inlining von `{{PROMPT_INJECTION_DEFENSE_BLOCK}}` (Belege: `agents/1-generic/concept-specifier.md:125`, `concept-reviewer.md:164`, `ideation.md:176`, `security-auditor.md:230`; expandiert z. B. `standalone/agents/concept-specifier.md:112`). Fehlerpfad: reiner `grep` ueber `agents/1-generic/` sieht den Block nicht und ist unzulaessig.
- **IC-7 — Test-Einstiegspunkte.** `python3 -m pytest <datei> -q` fuer `tests/test_agents_frontmatter.py`, `tests/test_agent_eval_framework.py`, `tests/test_contract_labels.py`, `tests/test_context_compact_mode.py` (alle vier im Checkout vorhanden). Fehlerpfad: jeder rote Test blockiert den betroffenen Folgeplan.
- **IC-8 — Sync-Validierung.** `python3 scripts/sync.py --validate` (Plan Z. 88; `AGENTS.md`). Erfolg: Exit 0. Fehlerpfad: Exit ungleich 0 = Blocker.
- **IC-9 — Kosten-Gate.** `scripts/run_role_routing_eval.py:eval_gate.run_with_approval` (Aufrufstelle `:1096`; Definition `scripts/lib/eval_gate.py:269`; Plan Z. 98 nennt `:1021` als historischen `9aa0e0c0`-Anker) und `--estimate-only`-Pfad (Z. 91). Signatur: erst Schätzung, dann Anzeige, dann ausschliesslich nach ausdruecklichem User-Ja Ausfuehrung. Fehlerpfad: ohne Schätzung **oder** ohne User-Ja darf kein LLM-/Agent-/Eval-Lauf starten; das Kriterium bleibt dann unverifiziert (nicht „bestanden"). Die Anwendung auf #1014-Eval-Cases wird hier spezifiziert, nicht implementiert.

## Datenfluss

1. **Gate-Kette (dieses Artefakt):** Phasenplan Task 0 (Z. 325–332) → Konzept (`docs/concepts/evidence-discipline-1014.md`, #778-Hintergrund) → diese Spec (`Status: APPROVED`) → vier Folgeplaene in H2 (Entscheidung 52). Ohne APPROVED endet die Kette (IC-0).
2. **Folgeplan-Aenderungsfluss:** Issue-ACs und Rollenliste je Muster (soweit verfuegbar; sonst "to be determined in the follow-up plan") → Auswahl der `agents/1-generic/<role>.md` (IC-3) → Dedupe gegen expandierten Text (IC-5, IC-6) → Version-Bump (IC-3) → Case in `tests/routing-llm-eval/catalog.behavior.yaml` (IC-2) → `gen_promptfoo_config.py --check` (IC-1) → Golden-Rebaseline nur betroffener eingefrorener Rollen mit Manifest (IC-4) → vier pytest-Dateien (IC-7) → `sync.py --validate` (IC-8) → Review.
3. **COSTLY-Zweig (nur AC-10/AC-11):** Kriterium „eval case fails when the sentence is removed" → `--estimate-only` → Kostenschaetzung anzeigen → User-Ja → LLM-Laeufe ueber `run_eval.sh` (IC-9, IC-2) → Ergebnis entscheidet ueber die Gueltigkeit des Eval-Cases. Ohne User-Ja: kein Lauf, kein Ergebnis, kein Statuswechsel.

## Acceptance Criteria (nummeriert, testbar)

Jedes Kriterium ist in Given/When/Then-Form und nennt mindestens einen Interface Contract.

1. **AC-01 (Gate-Artefakte, IC-0).** Given der freigegebene Phasenplan Task 0, When beide Artefakte im Checkout gelesen werden, Then existieren `docs/concepts/evidence-discipline-1014.md` und `docs/specs/2026-11-11-evidence-discipline-1014-spec.md`, und die Spec trägt `Status: APPROVED` sowie einen identischen `spec-id:` im Kopf und im Trace-Anker.
2. **AC-02 (Folgeplan-Struktur, IC-0).** Given die APPROVED Spec, When die Planungsphase fortgesetzt wird, Then existieren genau vier Folgeplaene, einen je Sequenzschritt: Step 1 = P5+P7, Step 2 = P1, Step 3 = P3+P4, Step 4 = P2+P6+P8; alle sind gemaess Entscheidung 52 / O-H8 in H2 eingeplant und nicht Teil des Phasenplans.
3. **AC-03 (Rollenlisten, IC-0, IC-3).** Given `UEBERGREIFENDE-MUSTER.md` nicht im Repo liegt, When ein Folgeplan seine Rollenliste je Muster dokumentiert, Then ist sie entweder gegen eine vorhandene Quelle belegt oder ausdruecklich als "to be determined in the follow-up plan" gefuehrt; diese Spec enthält keine erfundene Rollenliste und keine erfundene Muster-Bezeichnung.
4. **AC-04 (Dedupe, IC-5, IC-6).** Given ein Muster-Satz soll in eine Rolle eingefuegt werden, When der Dedupe-Check nach dem Inlining von `{{PROMPT_INJECTION_DEFENSE_BLOCK}}` auf dem expandierten Text laeuft, Then enthaelt keine behandelte Rolle denselben Satz doppelt; ein reiner Rohtext-`grep` wird als Nachweis nicht akzeptiert.
5. **AC-05 (Dateiliste und Version-Bumps, IC-3, IC-7).** Given ein Folgeplan benennt seine Rollen, When `agents/1-generic/<role>.md` geaendert wird, Then ist die Frontmatter-`version:` genau dieser Rollen erhoeht, und `python3 -m pytest tests/test_agents_frontmatter.py -q` ist gruen.
6. **AC-06 (Eval-Katalog, IC-2).** Given ein Verhaltens-Eval-Case wird fuer ein Muster ergaenzt oder angepasst, When `tests/routing-llm-eval/catalog.behavior.yaml` gelesen wird, Then deklariert der Case die dokumentierten Felder (`id`, `role`, `prompt`, `category` sowie verwendete `expected_any`/`expected_all`/`forbidden`) gueltig, und es wird kein `llm-rubric`-Assert eingefuehrt.
7. **AC-07 (Generator-Frische, IC-1).** Given Aenderungen am Eval-Katalog, When `python3 scripts/gen_promptfoo_config.py --check` ausgefuehrt wird, Then ist der Exit-Code 0 und die generierte Konfiguration unveraendert; bei Exit 1 ist der Folgeplan blockiert.
8. **AC-08 (Golden-Rebaseline, IC-4).** Given eine Template-Aenderung veraendert das gerenderte Output einer Rolle mit Golden in `tests/fixtures/slimming-golden/`, When die Fixture angepasst wird, Then geschieht dies ausschliesslich fuer die vom Folgeplan betroffenen eingefrorenen Rollen, mit dokumentiertem Grund und Diff-Manifest-Eintrag; der uebrige eingefrorene Satz (inkl. `_GOLDEN_ROLE_COUNT` = 58) bleibt unangetastet, und `tests/test_template_slimming_equivalence.py` bleibt gruen.
9. **AC-09 (Tests und Validierung, IC-7, IC-8).** Given die Aenderungen eines Folgeplans sind fertig, When `python3 -m pytest tests/test_agents_frontmatter.py tests/test_agent_eval_framework.py tests/test_contract_labels.py tests/test_context_compact_mode.py -q` und anschliessend `python3 scripts/sync.py --validate` laufen, Then sind alle vier Testdateien gruen und `--validate` endet mit Exit 0.
10. **AC-10 (COSTLY — keine Ausfuehrung ohne Freigabe, IC-9).** Given das Kriterium „eval case fails when the sentence is removed" erfordert LLM-Laeufe, When weder Kostenschaetzung noch ausdrueckliches User-Ja vorliegen, Then wird kein LLM-/Agent-/Eval-Lauf gestartet und das Kriterium bleibt als „unverifiziert — Kosten-Gate offen" dokumentiert; ein stiller Lauf ist ein Verstoss gegen Plan Z. 91.
11. **AC-11 (COSTLY — bedingte Ausfuehrung, IC-9, IC-2).** Given die Kostenschaetzung wurde angezeigt und der User hat ausdruecklich zugestimmt, When der Eval-Lauf ueber `tests/routing-llm-eval/run_eval.sh` mit `REPEAT=1` erfolgt, Then schlaegt genau der Eval-Case fehl, dessen Evidence-Satz aus der betroffenen Rolle entfernt wurde, waehrend der unveraenderte Fall besteht; ohne diese Bedingungen ist AC-11 nicht ausfuehrbar und darf nicht als bestanden markiert werden.
12. **AC-12 (PR-Schnitt, IC-0).** Given die vier Folgeplaene sind umgesetzt, When ihre PRs und Commit-Texte erstellt werden, Then liegen sie im Nachfolge-PR H2 der Phase H (Entscheidung 52, O-H8 beantwortet), enthalten nicht `Closes`/`Fixes`/`Resolves`, und #1014 bleibt in diesem Gate offen (P1–P8 querschnittlich offen bis zum Lauf der Folgeplaene, Plan Z. 331).

## Offene Fragen + Risiken

**Offene Fragen (keine Entscheidung, an main chat / Folgeplaene):**

- **OQ-1 (Rollenlisten, Muster-Namen):** `UEBERGREIFENDE-MUSTER.md` fehlt (Plan Z. 328, Z. 471); die Zuordnung der 34 Rollen auf P1..P8 und die inhaltliche Bezeichnung der Muster sind nicht verifizierbar. "to be determined in the follow-up plan".
- **OQ-2 (Issue-Wortlaut):** AC-Liste, P1..P8-Sequenz und alle harte Zahlen stammen nur aus Plan Z. 327–329; `.tmp/issues/1014.md` (`:78`, `:133`) ist nicht im Checkout. "to be determined in the follow-up plan".
- **OQ-3 (Kosten):** Umfang und Preis der LLM-Laeufe fuer AC-11 sind nicht beziffert; Kostenschaetzung und User-Ja stehen aus. Kein Wert wird hier genannt.
- **OQ-4 (#1013-Abgrenzung):** Der Merge-Status ist belegt (Roadmap Z. 77; Spec `2026-10-22-opencode-v2-support-spec.md:16`), die Dateiebene der Abgrenzung ist lokal nicht messbar. "to be determined in the follow-up plan".

**Risiken und Gegenmassnahmen:**

- **R1 — Dedupe-False-Negative:** Pruefung nur am Template-Rohtext uebersieht expandierte Substitutionsbloecke (IC-5). Gegenmassnahme: AC-04 verlangt expandierten Text.
- **R2 — Golden-Drift / B2-Gate-Verlust:** Unbegruendetes Neu-Einfrieren verschiebt das B2-Ziel (Plan Z. 93, `README.md:16-20,90-94`). Gegenmassnahme: AC-08 mit Manifestpflicht und reduziertem Scope.
- **R3 — Unautorisierte Kosten:** LLM-Laeufe ohne Freigabe verletzen Plan Z. 91. Gegenmassnahme: AC-10 als hartes Gate vor AC-11; IC-9 mit `--estimate-only` und User-Ja.
- **R4 — Veraltete Anker:** Plan-Anker `9aa0e0c0` und #778-Messstand `87564958` sind historisch. Gegenmassnahme: Re-Messung gegen `4d3d21f5`; Tabelle unten.

**Re-Messung — korrigierte bzw. als nicht verifizierbar markierte Plan-Anker:**

| Plan-Anker | Lokaler Befund (`4d3d21f5`) | Behandlung in dieser Spec |
|---|---|---|
| `.tmp/issues/1014.md:78` (Kriterium „eval case fails when the sentence is removed") | Datei nicht im Checkout; Glob `**/*1014*`: 0 Treffer | Nur aus Plan Z. 329 uebernommen; AC-10/AC-11 mit Kosten-Gate; Wortlaut offen (OQ-2) |
| `.tmp/issues/1014.md:133` („One PR per step") | Datei nicht im Checkout | Nicht benoetigt: durch Entscheidung 52 / O-H8 (Z. 142) ersetzt; AC-12 |
| `UEBERGREIFENDE-MUSTER.md` (Z. 328, Z. 471) | Nicht im Repo; Glob: 0 Treffer | Rollenlisten/Muster-Namen offen (OQ-1, AC-03) |
| `{{PROMPT_INJECTION_DEFENSE_BLOCK}}` (Z. 328) | Verifiziert: `scripts/lib/config.py:3426-3437`, `scripts/lib/consistency/placeholders.py:130`, `snippets/security/prompt-injection-defense.md`, `docs/guides/features/sync-concept.md:287` | IC-5/IC-6, AC-04 |
| `tests/fixtures/slimming-golden/` (Z. 329, Z. 93) | Verifiziert: `README.md:16-20,36-41,90-94`; B2-Gate `tests/test_template_slimming_equivalence.py` | IC-4, AC-08 |
| `python3 scripts/gen_promptfoo_config.py --check` (Z. 329) | Verifiziert: `:21` („exit 1 if it would change"), `:92-93` | IC-1, AC-07 |
| Vier Test-Dateien (Z. 329) | Verifiziert: `tests/test_agents_frontmatter.py`, `tests/test_agent_eval_framework.py`, `tests/test_contract_labels.py`, `tests/test_context_compact_mode.py` je 1 Treffer | IC-7, AC-09 |
| `tests/routing-llm-eval/catalog.behavior.yaml` (Z. 329) | Verifiziert: `:1-15` (Felder, `REPEAT=1`, kein Judge-Assert) | IC-2, AC-06, AC-11 |
| `eval_gate.run_with_approval` (Plan Z. 98: `:1021`) | Historischer `9aa0e0c0`-Anker; aktuell Aufruf `scripts/run_role_routing_eval.py:1096`, Definition `scripts/lib/eval_gate.py:269` | IC-9 auf `:1096` korrigiert; AC-10/AC-11 unveraendert |
| Plan-Review `9aa0e0c0` / #778 `87564958` | Historisch; HEAD `4d3d21f5` | Kopf/Frontmatter weist Re-Messstand aus |

**Abdeckungs-Checkliste (Self-Review):**

- [x] Pflichtsektionen vorhanden: Problem/Ziel/Nicht-Ziele, Interface Contracts, Datenfluss, Acceptance Criteria, Offene Fragen + Risiken, Trace-Anker.
- [x] IC-0..IC-9 vollstaendig mit Datei:Symbol, Signatur und Fehlerpfad; kein `TBD`, kein `TODO`, keine leere Schnittstelle.
- [x] AC-01..AC-12 nummeriert, Given/When/Then, testbar und je mindestens einem IC zugeordnet.
- [x] Vier Sequenzschritte mit P5+P7 / P1 / P3+P4 / P2+P6+P8 und je einem Folgeplan in H2 abgebildet (Entscheidung 52, O-H8).
- [x] Dateiliste `agents/1-generic/<role>.md` + `tests/routing-llm-eval/catalog.behavior.yaml`, Version-Bumps und Golden-Rebaseline nur fuer eingefrorene Rollen enthalten.
- [x] LLM-Eval-Kriterium als **COSTLY** mit User-Gate (`--estimate-only` → Kostenschaetzung → User-Ja) dokumentiert; kein Automatismus, keine Kostenzahl.
- [x] Kein Implementierungsplan, kein Code, keine Rollenliste, keine erfundene Zahl, keine REQ-ID, keine Closing-Keywords.
- [x] #778-Konzept gelesen und als Hintergrund uebernommen; keine neue Entscheidung.
- [x] Freigabe-Marker im Kopf und im Frontmatter mit Nutzer-go 22.11 und „keine neue Entscheidung".

## Trace-Anker: spec-id: SPEC-EVIDENCE-DISCIPLINE-1014-2026-11-11
