# Konzept: Evidence Discipline (#1014) — Muster, Dedupe und Abgrenzung

> Status: APPROVED (Nutzergo 22.11 — Konzept auf Basis des freigegebenen Phasenplans `2026-11-11-phase-h-context-eval.md` (Task 0, Z. 325–332) nachgetragen, keine neue Entscheidung)

- **Autoritative Basis:** `docs/superpowers/plans/2026-11-11-phase-h-context-eval.md` — Task 0 (Z. 325–332), Scope-Zeile Z. 30 (`#1014 | XL | 34 Rollen, 8 Muster, 4 PRs`), Gate-Eintrag Z. 70 (`0 | #1014 | H1 (Gate-Task) | Concept/Spec-Freigabe; ohne APPROVED nach H2; #1014-Folgeplaene (Umsetzung) fallen unter Entscheidung 52`), Global Constraints Z. 91 (keine kostenpflichtigen Laeufe), Entscheidung 52 Z. 135, O-H8 Z. 142, Offene Punkte Z. 471 und Z. 478.
- **Issue-Quelle — Plan-only:** Die im Plan zitierte Issue-Datei `.tmp/issues/1014.md` (Z. 329 verweist auf `:78`, Z. 142 auf `:133`) ist im lokalen Checkout **nicht vorhanden**. Geprueft mit Glob über `.tmp/**/1014*` und repoweit `**/*1014*`: 0 Treffer. Alle P1..P8-Bezeichnungen, Rollenlisten, konkreten Saetze, Versionsziele und numerischen Werte in diesem Konzept stammen daher ausschliesslich aus dem Plan. Issue-spezifische Werte, die der Plan nicht nennt, sind ausdruecklich **"to be determined in the follow-up plan"** und werden hier nicht geraten.
- **Messstand:** Branch `chore/phase-h-bundle`, HEAD `4d3d21f5` (aus `.git/refs/heads/chore/phase-h-bundle` und `.git/logs/HEAD` gelesen). Alle file:line-Belege unten sind gegen diesen Stand neu gemessen. Abweichende Historic-Anker werden nicht vermischt: das Schwesterkonzept `docs/concepts/cross-cutting-findings-778.md` wurde bei `87564958` gemessen, der Plan-Review bei `origin/main 9aa0e0c0`.
- **Gemeinsamer Hintergrund:** `docs/concepts/cross-cutting-findings-778.md` (APPROVED, Nutzer-go 22.11) wurde vollstaendig gelesen und als Hintergrund uebernommen. #1014 setzt die Linie von #778 fort (Plan Z. 327); dieses Konzept wiederholt weder dessen Dispositionen F-1..F-6 noch traegt es neue Entscheidungen bei.
- **Geltung:** Konzept und zugehoerige Spec sind Gate-Artefakte (H1). Umsetzung entsteht ausschliesslich in Folgeplaenen, die nach Entscheidung 52 in den Nachfolge-PR H2 der Phase H fallen (Z. 70, Z. 135, Z. 142). #1014 wird hier nicht geschlossen; P1–P8 bleiben bis zum Lauf der Folgeplaene querschnittlich offen (Z. 331).

## 1. Problem / Ziel / Nicht-Ziele

**Problem.** Issue #1014 verlangt eine querschnittliche Evidence-Discipline ueber die generischen Rollen-Templates: acht Muster (P1–P8) sollen in den betroffenen Rollen konsistent, nachweisbar und ohne Duplikate verankert werden. Der freigegebene Phasenplan macht die Freigabe von Konzept und Spec zum H1-Gate und verweist die eigentliche Umsetzung in Folgeplaene. Zwei Voraussetzungen sind lokal nicht erfuellbar: die vom Issue genannte Quelldatei `UEBERGREIFENDE-MUSTER.md` liegt nicht im Repo (Plan Z. 328, Z. 471), und die Issue-Datei selbst liegt nicht im Checkout. Damit sind Rollenliste je Muster und der genaue Issue-Wortlaut nicht verifizierbar.

**Ziel.**
- Die drei vom Plan vorgegebenen Konzept-Schritte (Z. 328) festschreiben: Rollenliste je Muster als offene, im Folgeplan zu fuellende Groesse; Dedupe-Regel gegen den **expandierten** Text; Abgrenzung zum gemergten PR #1013.
- Die Sequenz Step 1–Step 4 mit der Plan-Zuordnung der Muster auf je einen Folgeplan dokumentieren, ohne die Folgeplaene selbst zu schreiben.
- Die Kostenregel fuer das Kriterium „eval case fails when the sentence is removed" als COSTLY/User-Gate verankern (Z. 329 i. V. m. Z. 91).
- Die PR-Schnittsregel (Entscheidung 52 / O-H8, Z. 70, Z. 135, Z. 142) als verbindlich uebernehmen.

**Nicht-Ziele.**
- Keine Template-, Config-, Hook-, Test- oder Generator-Aenderung; keine Umsetzung in Phase H (Z. 327, Z. 331).
- Keine Folgeplaene, kein Implementierungsplan, kein Code — die vier Folgeplaene entstehen erst nach dieser Freigabe und laufen in H2 (Entscheidung 52).
- Keine Erfindung von Rollenlisten, Muster-Namen, Satztexten, Versionsnummern, Kostenwerten oder Zielzahlen. Wo der Plan schweigt: "to be determined in the follow-up plan".
- Keine Schliessung von #1014, keine REQ-ID-Vergabe, keine Wiederholung der #778-Dispositionen, keine erneute Oeffnung von #1013.
- Keine Closing-Keywords in Commit-/PR-Texten (Z. 89).

**Betroffene Subsysteme (nur als spaetere Aenderungsziele der Folgeplaene, nicht hier):** `agents/1-generic/<rolle>.md` (Template-Frontmatter inkl. `version:`), `tests/routing-llm-eval/catalog.behavior.yaml`, `tests/fixtures/slimming-golden/` (eingefrorene Golden-Fixtures), `scripts/gen_promptfoo_config.py` (`--check`), `snippets/security/prompt-injection-defense.md` und `scripts/lib/config.py` (Expandierung von Substitutionsbloecken).

## 2. Muster und Rollen (P1–P8) — Stand und Grenze

Der Plan nennt acht Muster und 34 Rollen als Scope (Z. 30), sowie vier Sequenzschritte mit folgender Muster-Zuordnung (Z. 327):

| Sequenzschritt | Muster laut Plan | Folgeplan | PR-Einordnung |
|---|---|---|---|
| Step 1 | P5 + P7 | separater Folgeplan | H2 (Entscheidung 52) |
| Step 2 | P1 | separater Folgeplan | H2 (Entscheidung 52) |
| Step 3 | P3 + P4 | separater Folgeplan | H2 (Entscheidung 52) |
| Step 4 | P2 + P6 + P8 | separater Folgeplan | H2 (Entscheidung 52) |

**Nicht aus dem Plan ableitbar und daher offen:**
- Die inhaltliche Bezeichnung und der normative Satztext von P1..P8. Quelle waere `UEBERGREIFENDE-MUSTER.md`; diese Datei ist nicht im Repo (Glob `**/UEBERGREIFENDE-MUSTER.md`: 0 Treffer; vgl. Plan Z. 328, Z. 471). **to be determined in the follow-up plan.**
- Die Rollenliste je Muster. Der Plan nennt nur die Gesamtzahl 34 (Z. 30), keine Zuordnung. **to be determined in the follow-up plan.**
- Die „79-Rollen-Review-Grundlage" ist laut Plan Z. 471 ebenfalls nicht pruefbar; sie wird hier nicht als Beleg verwendet.
- Die Formulierung „4 PRs" in Z. 30 stammt aus dem Issue-Vorschlag (ein PR je Sequenzschritt, vgl. Z. 142: `.tmp/issues/1014.md:133` „One PR per step"). Sie ist durch Entscheidung 52 / O-H8 ueberschrieben: die Folgeplaene laufen im Nachfolge-PR H2, nicht „one PR per step". Diese Zuordnung ist eine bereits getroffene Entscheidung, keine neue.

## 3. Dedupe-Check gegen den expandierten Text

Der Plan verlangt in Step 1 einen Dedupe-Check „gegen expandierten Text (Substitutionsbloecke wie `{{PROMPT_INJECTION_DEFENSE_BLOCK}}`)" (Z. 328). Die Regel wird wie folgt verankert:

- **Regel:** Ein Muster-Satz gilt als bereits vorhanden, wenn er im **gerenderten/expandierten** Agenten-Text vorkommt — nicht nur, wenn er im Template-Quelltext steht. Ein Satz darf nicht durch Einfuegen in ein Template dupliziert werden, das denselben Satz ueber einen Substitutionsblock bereits erhaelt.
- **Beleg der Substitutionskette (neu gemessen):**
  - `scripts/lib/config.py:3426-3437` — Kommentar und Aufbau von `variables["PROMPT_INJECTION_DEFENSE_BLOCK"]`; Quelle ist `snippets/security/prompt-injection-defense.md` (`:3433-3436`), Rueckgabe leer bei fehlender Datei (`:3436`).
  - `snippets/security/prompt-injection-defense.md` — vorhanden (Glob: 1 Treffer).
  - `scripts/lib/consistency/placeholders.py:130` — der Platzhalter ist registriert.
  - `docs/guides/features/sync-concept.md:287` — dokumentierte Bedeutung: kanonischer Hinweis aus `snippets/security/prompt-injection-defense.md`.
  - `agents/1-generic/*.md` — der Platzhalter erscheint in vielen Rollen (z. B. `concept-specifier.md:125`, `concept-reviewer.md:164`, `ideation.md:176`, `security-auditor.md:230`); die expandierte Form liegt in `standalone/agents/*.md` (z. B. `concept-specifier.md:112`).
- **Konsequenz fuer die Folgeplaene:** Der Dedupe-Check muss nach dem Expandieren ansetzen (Sync-/Render-Pfad oder gleichwertige Expansion). Ein reiner `grep` ueber `agents/1-generic/` ist unzureichend, weil er den eingefuegten Block nicht sieht. Das konkrete Pruefverfahren wird im jeweiligen Folgeplan festgelegt.
- **Keine neue Entscheidung:** Es wird kein neues Platzhalter-System, kein neues Snippet und keine Aenderung an `scripts/lib/config.py` beschlossen; die Kette wird nur als Evidenz fuer die Pruefregel zitiert.

## 4. Abgrenzung zu PR #1013 (gemergt)

- Der Plan nennt die Abgrenzung zu PR #1013 ausdruecklich als Konzept-Schritt (Z. 328: „Abgrenzung zu PR #1013 (gemergt)"). Der Merge-Status ist unabhaengig belegt: `docs/superpowers/plans/2026-11-10-backlog-roadmap.md:77` (`XL; PR #1013 gemergt; P1-P8 querschnittlich nicht`) und `docs/specs/2026-10-22-opencode-v2-support-spec.md:16` (Liste der MERGED-PRs inkl. `#1013`).
- **Abgrenzungsregel:** #1014 behandelt ausschliesslich die noch offenen P1–P8. Inhalte, die mit PR #1013 gemergt wurden, werden nicht erneut entschieden, nicht rueckgaengig gemacht und nicht als offen gefuehrt. Ein Folgeplan darf #1013-Artefakte nur lesen, nicht als Aenderungsziel aufnehmen.
- **Grenze der Pruefbarkeit:** Welche Dateien/Zeilen #1013 im Einzelnen beruehrt hat, ist aus dem lokalen Checkout nicht ermittelbar (Issue-/PR-Daten nicht vorhanden). Die konkrete Abgrenzungsliste je Muster ist **to be determined in the follow-up plan**; an dieser Stelle wird keine Dateiliste erfunden.

## 5. Umsetzungsgrenze und Trace

- Plan-Task 0 (Z. 327–332): Konzept, dann Spec; Freigabe durch `Status: APPROVED`; danach separater Folgeplan je Sequenzschritt. Akzeptanz: beide Artefakte vorhanden, Spec-Zeile `Status: APPROVED` (Z. 331).
- Plan-Task 14 (Z. 317–323): dies ist der gemeinsame Hintergrund; das #778-Konzept bleibt unverändert.
- Entscheidung 52 (Z. 53–55, Z. 70, Z. 135) und O-H8 (Z. 142): die vier Folgeplaene laufen in Phase H / H2, nicht in einem eigenen PR je Schritt. Damit ist O-H8 beantwortet; hier wird nichts neu entschieden.
- Global Constraints Z. 89 (keine Closing-Keywords), Z. 91 (keine kostenpflichtigen Laeufe ohne Kostenschaetzung und User-Ja), Z. 93 (Golden-/Hash-Fixtures nur mit dokumentiertem Grund neu pinnen).
- ADR-Bezug: Es werden keine neuen ADRs angelegt. Die hier angewendeten Entscheidungen (PR-Schnitt, Kosten-Gate, Golden-Freeze-Regel) sind im freigegebenen Phasenplan bzw. in der Gated-Spec `docs/specs/2026-09-19-dynamic-routing-template-slimming.md` (AC B2) als Entscheidungsprotokoll festgehalten.

## 6. Offene Punkte (keine Entscheidung)

- **D-1014-1 (Rollenlisten und Muster-Namen):** `UEBERGREIFENDE-MUSTER.md` fehlt; die Rollenliste je Muster und die P1..P8-Bezeichnungen sind nicht verifizierbar. Der jeweilige Folgeplan beschafft die Quelle oder benennt sie als nicht verfuegbar. Kein Ort und keine Liste wird hier festgelegt.
- **D-1014-2 (Issue-Wortlaut):** Die AC-Liste und die P1..P8-Sequenz sind nur aus dem Plan bekannt (Z. 327, Z. 329). Der genaue Issue-Text (`.tmp/issues/1014.md:78`, `:133`) ist nicht im Checkout. Issue-spezifische Werte bleiben "to be determined in the follow-up plan".
- **D-1014-3 (Kosten des Eval-Kriteriums):** Das Kriterium „eval case fails when the sentence is removed" erfordert LLM-Laeufe. Kostenschaetzung und User-Ja stehen aus; der Ablauf ist in der Spec als COSTLY/User-Gate beschrieben. Keine Zahl wird genannt.
- **D-1014-4 (Abgrenzungsdetail #1013):** Die Dateiebene der Abgrenzung ist lokal nicht messbar; der Folgeplan fuehrt sie nach.

## 7. Abdeckungs-Checkliste

- [x] Drei Plan-Schritte aus Task 0 Step 1 (Z. 328) vollstaendig aufgenommen: Rollenliste (offen), Dedupe-Check (expandierter Text), Abgrenzung #1013.
- [x] Sequenz Step 1–Step 4 mit der Plan-Zuordnung P5+P7 / P1 / P3+P4 / P2+P6+P8 und je einem Folgeplan in H2 dokumentiert.
- [x] #778-Konzept gelesen, als Hintergrund uebernommen, nicht veraendert.
- [x] Keine Rollenliste, kein Muster-Name, keine Zahl, kein Preis, keine Version erfunden; offene Werte als "to be determined in the follow-up plan" markiert.
- [x] LLM-Eval-Kriterium als COSTLY/User-Gate gekennzeichnet (Spec-Uebergabe).
- [x] Keine neue Entscheidung, keine Umsetzung, kein Implementierungsplan, keine REQ-ID, keine Closing-Keywords.
- [x] Freigabe-Marker im Kopf exakt mit Nutzer-go 22.11 und „keine neue Entscheidung".
- [x] Re-Messung: Anker gegen `4d3d21f5` gemessen; nicht verfuegbare Plan-Anker (`.tmp/issues/1014.md`, `UEBERGREIFENDE-MUSTER.md`) als nicht verifizierbar gekennzeichnet, nicht uebernommen.
