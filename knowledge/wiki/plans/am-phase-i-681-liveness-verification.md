---
type: Plan
title: "Phase-I #681 — Liveness Verification (ENTSCHEIDUNGSGATE I-N7)"
source: "GitHub Issue #681; APPROVED-Konzept docs/specs/2026-11-20-phase-i-681-concept.md"
spec: "docs/specs/2026-11-20-phase-i-681-concept.md"
spec-id: "CONCEPT-PHASE-I-681-2026-11-20"
status: "geplant — BLOCKED — User-Entscheidung I-N7"
branch: "feat/wave7-phase-i-bundle"
created: "2026-11-21"
tags: [plan, liveness, phase-i, issue-681, decision-gate, blocked]
---

# Liveness Verification für langlebige Subagent-Dispatches (#681) Implementation Plan

> Status: geplant — **BLOCKED — User-Entscheidung I-N7**. Dieser Plan spezifiziert ausschließlich den I-N7-unabhängigen Teil und markiert den Rest als Entscheidungspunkt. Es wird **kein** Ablageort, **kein** Schwellwert-Modell und **keine** Zieldatei für die Liveness-Guidance gewählt.
> Bundle: W7 Phase-I-Bundle, Plan 2 von 2. Umsetzung gemeinsam mit #896 in einem PR (vom Nutzer freigegebene §3.9-Abweichung, im PR-Body zu vermerken); Pläne und Ownership bleiben getrennt.

**Feststellung vorab (Pflichtbefund):** Der Ziel-Skill `subagent-driven-development` liegt laut APPROVED-Konzept im `superpowers`-Plugin-Cache und ist **nicht im Repo verifiziert**. Die repo-internen I-N7-Optionen sind „gemeinsame Cross-Skill-Referenz" (neue Datei) und `agents/1-generic/orchestrator.md` (§2.1-shared, für dieses Bundle **verboten**). Damit existiert **keine sinnvolle repo-seitige Implementierung ohne I-N7**: schon jede Wahl eines Ablageorts wäre bereits die Entscheidung I-N7. Empfehlung: #681 im W7-Bundle als **Entscheidungspunkt** führen und die eigentliche Guidance-Umsetzung nach der User-Freigabe aus einer I-N7-Spec nachholen — nicht erfinden.

**Goal:** Die vom Issue geforderte „Liveness Verification"-Guidance (Trigger, drei Verifikationsschritte, Recovery, Beispiele, Querverlinkung) wird inhaltlich festgeschrieben; die repo-seitige Umsetzung startet erst nach der User-Entscheidung I-N7 (Ablageort + Schwellwert fest/konfigurierbar).
**Architecture:** Keine Architektur-Entscheidung vor I-N7. Der Plan enthält eine Entscheidungsvorlage mit den drei vom Konzept genannten Optionen, bewertet ausschließlich nach Ownership-/Rebaseline-Folgen — ohne Empfehlung.
**Tech Stack:** Markdown, pytest für die Content-Kriterien; keine Runtime-, keine Platform-Änderung, keine neue Abhängigkeit.
**Spec:** `docs/specs/2026-11-20-phase-i-681-concept.md` (spec-id: `CONCEPT-PHASE-I-681-2026-11-20`, status: APPROVED, Nutzergo 20.11. / E-31)

## Global Constraints

- **I-N7 nicht auflösen.** Weder Ablageort noch Schwellwert-Art (`fest 90 min` vs. `konfigurierbar`) werden hier gewählt. Die drei Optionen erscheinen ausschließlich als Entscheidungsvorlage.
- **`agents/1-generic/orchestrator.md` nicht berühren** — das ist eine I-N7-Option, eine §2.1-shared-Datei und für dieses Bundle zusätzlich verboten.
- **Bundle-1-forbidden Pfade nicht berühren:** `agents/1-generic/*.md`, `.meta-config/*`, `config/role-defaults.yaml`, `hooks/1-generic/lib/kernel/*`, `snippets/agents/closing-summary.md`, `standalone/**`, `tests/fixtures/**` sowie die Bundle-1-Testdateien.
- `#681` → `#1113`/`#1176` ist Issue-Hygiene **per Kommentar**; keine Closing-Keywords (`Closes`/`Fixes`/`Resolves`), kein Statuswechsel.
- Fachliche Abhängigkeit laut Konzept: Phase D / `#1176` („Orchestrator beendet Turn bei laufenden Workern") liegt vor der eigentlichen Umsetzung, sonst Doppelarbeit; `#1004` Teil E ist abzustimmender Querverweis. Beide sind **Voraussetzungen**, keine von diesem Plan getroffenen Entscheidungen.
- Keine Golden-Rebaseline (keine Template-/Rule-Änderung), keine Sync-Auswirkung, solange kein Ablageort gewählt ist.
- Plan/Artefakte deutsch; spätere Guidance-Datei folgt der Sprachmatrix ihres Zielorts (vom Nutzer mit I-N7 zu bestätigen).

## File Structure

- Create: `docs/specs/2026-11-21-phase-i-681-i-n7-decision.md` — APPROVED-Spec, die die zwei I-N7-Teilentscheidungen mit User-Freigabe festhält. Dies ist das Entscheidungsartefakt, **keine** Guidance-Implementierung.
- Modify: `knowledge/wiki/plans/am-phase-i-681-liveness-verification.md` — dieser Plan; Status bleibt `BLOCKED`, bis I-N7 entschieden ist.
- Create: `tests/test_liveness_guidance_681.py` — `TestIN7DecisionGate` (prüft nur, dass die Decision-Spec beide Pflichtfelder enthält, nicht welchen Wert sie haben). Die Tests für die sechs Content-AKs werden erst **nach** I-N7 gegen den dann benannten Zielpfad ergänzt.
- **Nicht spezifiziert (BLOCKED — User-Entscheidung I-N7):** Pfad, Dateiform und Rolle der Guidance-Datei; fest vs. konfigurierbarer Schwellwert; Querverlinkungs-Mechanik; Rebaseline-/Sync-Folgen; Abstimmung `#1176`/`#1004` Teil E. Ein Implementierungs-Task `681-1` wird deshalb **nicht** angelegt.
---
pipeline_stages:
  implement: 1   # Task 1 = Decision Gate; weitere Implementierungs-Stages erst nach User-Freigabe I-N7
---

### Task 681-0: ENTSCHEIDUNGSGATE I-N7 (BLOCKED — User-Entscheidung I-N7)

**Agent:** `concept-specifier` · **Depends on:** — (blocked durch User-Freigabe; fachlich vorausgesetzt: `#1176`/Phase D, Querverweis `#1004` Teil E)
**Files:** Create `docs/specs/2026-11-21-phase-i-681-i-n7-decision.md`; Test `tests/test_liveness_guidance_681.py::TestIN7DecisionGate` (Create); Modify dieser Plan (Status-Feld)
**Interfaces:**
- Produces: APPROVED-Spec mit genau zwei Pflichtfeldern: `I-N7-Ablageort` ∈ {Skill `subagent-driven-development` selbst, gemeinsame Cross-Skill-Referenz, `agents/1-generic/orchestrator.md`} und `I-N7-Schwellwert` ∈ {fest 90 min, konfigurierbar}. Beide **Werte** werden vom Nutzer gesetzt, nicht vom Planer.
- Produces: kurze Folgenabschätzung je Option (Ownership, Rebaseline-Pflicht, Erreichbarkeit des externen Skills, Abstimmbedarf `#1176`) als Entscheidungsvorlage — ohne Empfehlung, ohne Wahl.
- Consumes: Konzept §3/§4/§6 (I-N7 bewusst offen); Phase-I-Planung `docs/superpowers/plans/2026-11-11-phase-i-features-concept.md` (I-681 / I-N7).
- **Kein Output:** keine Guidance-Datei, keine `orchestrator.md`-Änderung, kein Skill-Text, keine Platform-Änderung.

- [ ] Step 1: Test schreiben (fail): `test_in7_spec_records_both_decisions` — die Decision-Spec enthält die Felder `I-N7-Ablageort` und `I-N7-Schwellwert` mit nicht-leeren Werten; gegen den aktuellen Stand (Spec fehlt) rot.
- [ ] Step 2: Entscheidung herbeiführen (**nicht** vom Planer treffen): drei I-N7-Optionen mit ihren Folgen dem Nutzer vorlegen; Nutzer wählt Ablageort + Schwellwertmodell; Werte in der Spec festhalten; Status `APPROVED` vom Nutzer setzen lassen.
- [ ] Step 3: Test (pass): `rtk pytest tests/test_liveness_guidance_681.py -k IN7DecisionGate -q` grün; `rtk grep -nE "Ablageort.*=|Schwellwert.*=" knowledge/wiki/plans/am-phase-i-681-liveness-verification.md` bestätigt, dass dieser Plan weiterhin keine Wahl enthält.
- [ ] Step 4: Commit `docs(plans): record I-N7 decision for issue 681` — ausschließlich Decision-Artefakte, **keine** Guidance-Implementierung.

**Acceptance criteria (messbar):** Decision-Spec existiert und enthält beide nicht-leeren Pflichtfelder; Test grün; dieser Plan enthält weiterhin keine Ablageort-/Schwellwert-Wahl; keine Guidance-Datei angelegt; `orchestrator.md` unverändert.

## I-N7-unabhängige Content-Spezifikation (gilt für jeden Ablageort)

Diese Anforderungen stehen unabhängig davon fest, wohin die Guidance später kommt. Sie sind die sechs Akzeptanzkriterien des APPROVED-Konzepts, ohne Pfad- und ohne Schwellwert-Aussage. Die Messbarkeit bezieht sich auf den Zielpfad, der erst durch I-N7 benannt wird.

| Nr. | I-N7-unabhängige Anforderung | Messbarkeit (nach I-N7 gegen Zielpfad) |
|---|---|---|
| C1 | Explizite Sektion „Liveness Verification" | Zieldatei enthält Überschrift `## Liveness Verification` exact match. |
| C2 | Trigger: `status: running` seit Schwellwert `T`, keine neuen Notifications seit dem letzten Tool-Round (~60 min). **Die Art von `T` (fest/konfigurierbar) ist I-N7 und bleibt offen.** | Sektion enthält eine Trigger-Regel mit genau diesen zwei Bedingungen; `T` als Symbol, nicht als festgelegter Wert. |
| C3 | Drei Verifikationsschritte in Reihenfolge: (1) Working-Tree-Timestamps (`git log --name-only -1 --format=%H`, `ls -t`); (2) projektspezifische langlebige Prozesse (`docker ps`, `docker ps -a --filter=status=exited`); (3) genau **ein** `SendMessage`-Check-in mit kurzem Tag, striktem 60-s-Timeout und One-Retry-Only-Policy. | Sektion enthält die drei Schritte numbered 1–3, die genannten Kommandos und die Tokens `60 s` sowie `one retry`. |
| C4 | Recovery bei bestätigtem Stall: `TaskStop` + frischer Dispatch; uncommitted Änderungen als **unverifizierter Kontext** übergeben und vom frischen Agenten neu verifizieren/getestet; Plan-State mit Recovery-Notiz aktualisieren. | Sektion enthält `TaskStop`, „fresh dispatch", „unverified context" und „plan state". |
| C5 | Kein-Recovery-Fall: bei nachgewiesener echter Aktivität (aktuelle Timestamps, aktive Container oder erfolgreiche Check-in-Antwort) mit Zuversicht weiterwarten. | Sektion enthält einen expliziten „keep waiting"-Zweig mit den drei Aktivitätssignalen. |
| C6 | Beispielsignale für Backend-Verifikation, Frontend-E2E, Bulk-Refactoring; Querverlinkung von Shell-Crash-Recovery und Long-Running-Task-Coordination. | Sektion nennt alle drei Task-Typen und beide verlinkten Skills namentlich. |

Diese sechs Kriterien werden zu gegebener Zeit in `tests/test_liveness_guidance_681.py` gegen den von I-N7 benannten Zielpfad umgesetzt — nicht jetzt, nicht gegen einen erfundenen Pfad.

## I-N7-abhängig — BLOCKED (bewusst nicht spezifiziert)

| Entscheidungsfeld | Warum blockiert | Was der Nutzer entscheidet |
|---|---|---|
| Ablageort | Der Ziel-Skill ist extern und nicht im Repo verifiziert; die zwei repo-internen Optionen sind Cross-Skill-Referenz oder `orchestrator.md`. Jede Pfadwahl wäre I-N7. | Eine der drei Konzept-Optionen; bei `orchestrator.md` zusätzlich außerhalb dieses Bundles zu planen (§2.1-shared + forbidden). |
| Schwellwert | Konzept lässt `fest 90 min` vs. `konfigurierbar` ausdrücklich offen. | fest oder konfigurierbar; Konfigurationsmechanismus nur bei „konfigurierbar" zu bestimmen. |
| Dateiform / Rolle der Guidance | Hängt am Ablageort (Skill-Text vs. Referenzdoku vs. Rule). | Folgt der Ablageort-Entscheidung. |
| Querverlinkungs-Mechanik | Cross-Skill-Links hängen davon ab, ob Skill oder Referenzdoku der Zielort ist. | Folgt der Ablageort-Entscheidung. |
| Rebaseline / Sync | Nur bei `orchestrator.md`-Variante (Rule → Golden-Fixtures); hier ausgeschlossen. | Bei Bedarf eigener Task außerhalb des Bundles. |
| `#1176` / `#1004` Teil E | Laut Konzept vor Umsetzung abzustimmende Abhängigkeit, keine hier getroffene Entscheidung. | Abstimmzeitpunkt und -form. |

**Konsequenz:** Es gibt nach I-N7-unabhängiger Content-Spezifikation und Decision Gate **keine weitere sinnvolle Implementierung ohne die User-Entscheidung**. `#681` wird daher im W7-Bundle als Entscheidungspunkt geführt; die Umsetzung der sechs Content-Kriterien folgt in einer separaten, aus der APPROVED-I-N7-Spec abgeleiteten Task-Folge. Einen `681-1`-Implementierungstask jetzt anzulegen hieße, I-N7 zu erfinden.

## Self-Review

| Check | Ergebnis |
|---|---|
| Sechs AKs des Konzepts abgedeckt | ✔ C1–C6 in der I-N7-unabhängigen Content-Spezifikation, messbar formuliert |
| I-N7 nicht entschieden | ✔ kein Ablageort, kein Schwellwert, keine Zieldatei gewählt; drei Optionen nur als Vorlage |
| BLOCKED-Markierung explizit | ✔ Frontmatter-Status, Header, Task 681-0 und Abschnitt „I-N7-abhängig" |
| Empfehlung „defer" ausgesprochen | ✔ Pflichtbefund + Konsequenz-Abschnitt |
| Kein Implementierung-task erfunden | ✔ nur Task 681-0 (Decision Gate); `681-1` bewusst nicht angelegt |
| `orchestrator.md` unberührt | ✔ in Global Constraints und I-N7-Tabelle als verboten markiert |
| Bundle-1-Dateien unberührt | ✔ keine forbidden Pfade in `Files:` |
| Ownership disjunkt zu #896 | ✔ #681 berührt `scripts/admin-server.py`, Doku und `tests/test_admin_start_mode_896.py` nicht |
| Jeder Task genau eine Rolle, Test, Commit, messbare AK | ✔ 1 Task (`concept-specifier`), 4 TDD-Schritte |
| `pipeline_stages` vorhanden, keine Placeholder | ✔ `implement: 1`; Pfade/Symbole/Commit benannt, offene Punkte als ausdrücklicher Entscheidungsvorbehalt (nicht als Platzhalter) markiert |
