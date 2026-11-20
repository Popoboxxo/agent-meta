---
spec-id: CONCEPT-PHASE-I-681-2026-11-20
title: "Phase-I-Konzept #681 — Liveness Verification für langlebige Subagent-Dispatches"
issue: 681
roadmap-pr: "0.7"
package: P33
rank: 3
status: APPROVED
approved-by: "Nutzergo 2026-11-20 (E-31)"
date: 2026-11-20
kind: concept
implementation: "später — Welle 7 (Roadmap §3.9)"
---

# Phase-I-Konzept #681 — Liveness Verification für langlebige Subagent-Dispatches

> Status: APPROVED (Nutzergo 2026-11-20, E-31)
> Freigabe: Nutzer-go 2026-11-20 für E-31-Einzel-Specs („Specs schreiben/Status APPROVED setzen mit Verweis auf Nutzergo 20.11., keine neuen Entscheidungen erfinden"). Der Approval-Marker wird vom Nutzer gesetzt, nicht vom Autor.
> Herkunft: ausschließlich Issue #681 und die freigegebene Master-Roadmap (PR 0.7, P33, E-31, §3.1, §3.9, §6) sowie die daraus dokumentierte Phase-I-Planung (Entscheidung I-N7, Abhängigkeit #1176/#1004-Teil-E). **Keine neuen Entscheidungen.**
> Dieses Dokument ist ein **Konzept**, kein Implementierungsplan und keine Spec mit Code.

## 1. Problemstellung (aus Issue #681)

Die Guidance des `subagent-driven-development`-Skills zum Warten auf dispatchte Subagenten
bietet gutes Pacing, unterscheidet aber nicht explizit zwischen einem **noch arbeitenden**
langen Task und einem **still hängenden** Agenten. Für den Koordinator sehen beide identisch
aus: gemeldeter `status: running`, keine neuen Notifications.

Beleg aus dem Issue: Bei einem 29-Task-SDD-Lauf in `ai-native-reqflow-POC` stallte ein
Implementer-Task (Task 29, „One diff world — Milestone M5") nach 3 Stunden legitimer
Arbeit (14 Dateien geändert, Tests teilweise vorbereitet). Der Status blieb `running`;
`ListAgents`/`TaskStatus` zeigten keinen Fehler. Erkannt wurde der Stall nur durch aktive
Prüfung konkreter externer Signale statt dem vertrauten Status:

1. **Git-Working-Tree-Timestamps** — 2+ Stunden keine Dateiänderung, inkonsistent mit behaupteter Aktivität.
2. **Docker-Container-Lifecycle** — erwartete langlebige Test-/Build-Container fehlten und waren nicht kürzlich beendet.
3. **Ein `SendMessage`-Liveness-Check-in** wurde von der Tooling angenommen („queued for delivery at its next tool round"), blieb aber ohne Antwort und ohne weitere Aktivität → bestätigter Stall.

Recovery erforderte: `TaskStop` des hängenden Agenten, Dispatch eines frischen Implementers,
Übergabe der uncommitted Änderungen als **unverifizierten Ausgangspunkt** (nicht vertrauen;
neu verifizieren).

**Root-Cause-Hinweis (Issue):** Warum der Agent keine Tool-Calls mehr produzierte, wurde nicht
bestimmt; möglicherweise ein separates Claude-Code-Plattform-Problem. Der Issue betrifft den
**SDD-Koordinator-Workflow**, nicht die Plattform selbst.

## 2. Ziel / Soll-Zustand (aus Issue #681)

Die `subagent-driven-development`-Guidance (oder eine gemeinsame Cross-Skill-Referenz)
erhält einen expliziten Abschnitt **„Liveness Verification"** für Dispatches jenseits einer
Schwelle (Issue-Vorschlag: ~90 Minuten):

- **Trigger:** Agent `status: running` seit 90+ Minuten, keine neuen Notifications seit dem letzten Tool-Round (~60 Minuten).
- **Verifikationsschritte (in Reihenfolge):**
  1. Working-Tree-Timestamps prüfen (z. B. `git log --name-only -1 --format=%H`, `ls -t` auf Source-Verzeichnissen) → bei 2+ Stunden ohne Änderung weiter zu Schritt 2.
  2. Projektspezifische langlebige Prozesse prüfen (z. B. `docker ps`, `docker ps -a --filter=status=exited`) → bei fehlenden erwarteten Containern weiter zu Schritt 3.
  3. **Ein** Liveness-Check-in via `SendMessage` mit kurzem Tag (z. B. `@agent Still here?`), striktem Timeout (60 s) und One-Retry-Only-Policy → ohne Antwort/Aktivität weiter zum Stopp.
- **Recovery:** Bei bestätigtem Stall `TaskStop` + frischer Dispatch; die uncommitted Änderungen des hängenden Agenten werden als **Kontext, nicht als vertrauenswürdige Arbeit** übergeben und vom frischen Agenten neu verifiziert/getestet; Plan-State mit Recovery-Notiz aktualisieren.
- **Kein-Recovery-Fall:** Bei nachgewiesener echter Aktivität (aktuelle Timestamps, aktive Container oder erfolgreiche Check-in-Antwort) mit Zuversicht weiterwarten.

Die Guidance soll konkrete Beispiele für gängige Task-Typen enthalten (Backend-Verifikation,
Frontend-E2E, Bulk-Refactoring) und von verwandten Skills querverlinkt werden (Shell-Crash-
Recovery, Long-Running-Task-Coordination).

## 3. Scope

### In Scope (Konzept-Ebene)

- Problem und Soll-Zustand der Liveness-Verification aus Issue #681 als Konzept festhalten.
- Trigger-Bedingung, die drei Verifikationsschritte, Recovery und Kein-Recovery-Fall als
  vom Issue vorgeschlagene Guidance beschreiben.
- Die sechs Akzeptanzkriterien des Issues als Soll-Zustand der späteren Umsetzung übernehmen.
- Querverweise auf #1004 (Teil E) und #1176 gemäß Roadmap/Phase-I-Planung als **abzustimmende**
  Abhängigkeiten dokumentieren.
- Offene Entscheidung **I-N7** (Ablageort, Schwellwert fest/konfigurierbar) als bewusst offen
  markieren und der späteren Spec mit User-Freigabe überlassen.
- Traceability auf #681 / P33 / PR 0.7 / E-31 / §6.

### Out of Scope (explizit)

- **Implementierung / Code-Änderungen** — erfolgt später in Welle 7 (§3.9), eigener Plan + PR.
- **Entscheidung I-N7** (Ablageort der Guidance; Schwellwert 90 min fest oder konfigurierbar)
  — durch die spätere Spec mit User-Freigabe zu entscheiden; hier **bewusst nicht entschieden**.
- **Keine Golden-Rebaseline** — PR 0.7 ist laut Roadmap §3.1 RB-frei; dieses Dokument ist
  reine Doku und rendert keine Agenten-/Rule-Templates.
- **Keine TDD-Code-Arbeit, keine Tests** — docs-only.
- Kein Schließen/Kommentieren von #681, #1113 oder #1176; keine Änderung an Issue-/PR-Status.
  Die Beziehung „#681 → #1113/#1176" ist laut Roadmap §6 **Issue-Hygiene per Kommentar**
  und hier ausdrücklich *nicht* als Merge/Close zu verstehen. Keine Closing-Keywords
  (`Closes`/`Fixes`/`Resolves`) in Commit- oder PR-Texten.
- Keine Änderung an Master-Roadmap, Worker-Control-Dateien, Batch0-Dateien, archivierten
  Plänen oder anderen Roadmap-Paketen.
- Keine neuen Entscheidungen über Issue #681 + freigegebene Roadmap hinaus.

## 4. Vorgeschlagener Ansatz mit Alternativen / Trade-offs

### Ansatz A — Expliziter Abschnitt „Liveness Verification" (issue-konform, empfohlen)

Die `subagent-driven-development`-Guidance erhält den im Issue beschriebenen Abschnitt mit
Trigger (90+ min), den drei Verifikationsschritten, Recovery und Kein-Recovery-Fall,
ergänzt um konkrete Beispiele und Querverlinkung verwandter Skills. Der genaue **Ablageort**
(Skill selbst vs. gemeinsame Cross-Skill-Referenz vs. frameworkspezifische
`orchestrator.md`-Regeln) und die Frage, ob der Schwellwert **fest 90 min oder
konfigurierbar** ist, bleiben der offenen Entscheidung **I-N7** vorbehalten.

- **Vorteile:** direkte Abhilfe gegen den identifizierten stillen Stall; orientiert sich
  vollständig an den Issue-AKs; keine Platform-Änderung nötig.
- **Nachteile:** braucht Abstimmung mit #1176/#1004-Teil-E, sonst Doppelarbeit in
  `orchestrator.md`; der externe Skill liegt nicht im Repo und muss vor der Umsetzung gegen
  den realen Skill-Text verifiziert werden.

### Ansatz B — Status quo (nur Pacing-Guidance, kein Liveness-Prozedere)

Keine Änderung; der Koordinator vertraut weiterhin dem gemeldeten Status.

- **Vorteile:** kein Aufwand.
- **Nachteile:** der beschriebene Stall bleibt unerkannt („waiting forever"); die sechs
  Issue-AKs werden nicht erfüllt. → verworfen.

### Ansatz C — Nur frameworkspezifische Orchestrator-Regel statt Skill-Guidance

Die Liveness-Guidance ausschließlich in `agents/1-generic/orchestrator.md` (bzw. abgeleitete
Plattform-Overrides) verankern, nicht im `subagent-driven-development`-Skill.

- **Vorteile:** im Repo versionierbar und via `sync.py` ausrollbar; nahe an #1176
  (Worker-Control, Turn-Ende bei laufenden Workern).
- **Nachteile:** der Issue adressiert primär den SDD-Skill; eine reine Framework-Regel
  erreicht die SDD-Nutzung nicht, solange der externe Skill nicht querverlinkt ist.
- **Status:** **nicht entschieden** — dieser Ablageort ist Teil von I-N7 und wird in der
  späteren Spec mit User-Freigabe festgelegt. Das Konzept trifft hier keine Wahl.

### Trade-off Schwellwert

Der Issue schlägt ~90 Minuten vor. Ob dieser Wert **fest** oder **konfigurierbar** sein soll,
ist ausdrücklich Teil von I-N7 und bleibt offen — keine Festlegung in diesem Konzept.

## 5. Akzeptanzkriterien (aus Issue #681, Konzept-Ebene)

- [ ] `subagent-driven-development` enthält eine explizite „Liveness Verification"-Sektion.
- [ ] Die Guidance enthält eine Trigger-Bedingung (~90 min Schwelle, keine recenten Notifications).
- [ ] Sie enthält konkrete Verifikationsschritte (Working-Tree-Timestamps, projektspezifische
      Prozesse, Check-in-Nachrichten-Protokoll mit 60 s Timeout / One-Retry-Only).
- [ ] Sie enthält ein Recovery-Verfahren (Stopp + frischer Dispatch + uncommitted Änderungen
      als unverifizierten Kontext).
- [ ] Sie enthält Beispielsignale für gängige Task-Typen (Backend-Verifikation, Frontend-E2E,
      Bulk-Refactoring).
- [ ] Querverlinkung von verwandten Skills (Shell-Crash-Recovery, Long-Running-Task-Coordination).

Diese AKs beschreiben den **Soll-Zustand der späteren Umsetzung**; ihre Erfüllung wird in der
späteren Spec / W7 geprüft und ist nicht Gegenstand dieses Doku-PRs. Die konkrete Ausgestaltung
(Ablageort, fest/konfigurierbarer Schwellwert) bleibt I-N7 vorbehalten.

## 6. Risiken / Annahmen

- **Annahme:** Der Ziel-Skill `subagent-driven-development` ist ein Harness-Skill aus dem
  `superpowers`-Plugin-Cache und **nicht im Repo verifiziert** (so die Phase-I-Planung). Der
  aktuelle Skill-Text muss vor der Umsetzung gegen die reale Installation geprüft werden.
- **Offene Entscheidung I-N7:** Ablageort der Liveness-Guidance und fest vs. konfigurierbarer
  Schwellwert sind bewusst unentschieden; die spätere Spec klärt sie mit User-Freigabe.
- **Abhängigkeit:** Phase D / #1176 („Orchestrator beendet Turn bei laufenden Workern") liegt
  vor der Umsetzung, sonst entsteht Doppelarbeit in `orchestrator.md` (dokumentierte
  Roadmap-Abhängigkeit). Inhaltlich eng verwandt: #1004 Teil E (Orchestrator-Abschluss,
  wait vs. resume). Beide sind **abzustimmende Querverweise**, keine von diesem Konzept
  getroffenen Entscheidungen.
- **Annahme:** Die in Issue #681 genannten Tools (`TaskStop`, `SendMessage`, `TaskStatus`,
  `ListAgents`) sind Bestandteil der Worker-Control-Mechanik; die zugehörige
  `#1176`-Arbeit gated Worker-Control über `{{#if WORKER_CONTROL_ENABLED}}` und
  `worker_control_tools` je Provider. Die spätere Spec hat dies gegen den dann aktuellen
  Code abzugleichen — hier keine neue Aussage.
- **Root-Cause offen:** Die Ursache des Hängens wurde laut Issue nicht bestimmt und ist
  möglicherweise ein separates Plattform-Problem → nicht Teil dieses Scopes.
- **Keine Rebaseline / kein Render-Diff:** reine Markdown-Änderung ohne Template-/Rule-Änderung.
- **Issue-Hygiene:** #681 → #1113/#1176 ist eine per-Kommentar-Zuordnung (Roadmap §6);
  hier keine Statusänderung, kein Close, keine Closing-Keywords.

## 7. Traceability

| Artefakt | Bezug |
|---|---|
| Issue #681 | Quelle für Problemstellung, Signale, Verifikationsschritte, Recovery, AKs und Root-Cause-Hinweis |
| Master-Roadmap §3.1, PR 0.7 | `docs/phase-i-<issue>`, P33, Rang 1–3 zuerst (#896, #339, #681), RB-frei |
| Master-Roadmap §1, P33 | Phase-I-Konzept-PRs; Reihenfolge P33; je S–M |
| Master-Roadmap §4, E-31 | Specs/Konzepte einzeln nach Review, Reihenfolge P33; Freigabe hiermit erteilt (Nutzergo 20.11.) |
| Master-Roadmap §3.9 | Welle 7: Phase-I-Umsetzungen, je Issue eigener Plan + PR **nach** APPROVED-Concept aus 0.7 |
| Master-Roadmap §6 | Issue-Hygiene: „#681 → #1113/#1176" per Kommentar — hier keine Statusänderung, kein Close |
| Phase-I-Planung (Fahrplan, Rang 3) | Aufwand S-M; Ziel-Skill nicht im Repo verifiziert; Querverweis #1004-Teil-E / #1176; Abhängigkeit #1176 vor Umsetzung |
| Entscheidung I-N7 | Offen: Ablageort der Guidance, Schwellwert 90 min fest/konfigurierbar → spätere Spec mit User-Freigabe |
| Nutzer-go 2026-11-20 (E-31) | Approval für dieses Konzept; keine neuen Entscheidungen |

## 8. Umsetzung — späterer PR (Welle 7)

Dieser PR liefert **nur** das Konzept (`docs/specs/2026-11-20-phase-i-681-concept.md`).
Die Implementierung folgt in einem eigenen PR in **Welle 7 (Roadmap §3.9)**: je Issue eigener
Plan + PR nach diesem APPROVED-Concept. Dort wird I-N7 (Ablageort, Schwellwert) durch eine
Spec mit User-Freigabe entschieden und die AKs umgesetzt und geprüft; vorher greift die
Abhängigkeit zu Phase D / #1176.

**Docs-only:** kein TDD-Code, keine Tests, keine Rebaseline. Bewusst kein Self-Approve — der
Status-Marker `APPROVED` stützt sich auf den Nutzergo 20.11. (E-31).

## 9. Bestätigung — keine neuen Entscheidungen

Alle Aussagen dieses Konzepts stammen aus Issue #681 und der freigegebenen Roadmap
(PR 0.7 / P33 / E-31, §3.1, §3.9, §6) sowie der dokumentierten Phase-I-Planung
(Rang 3, I-N7, Abhängigkeit #1176/#1004-Teil-E). I-N7 bleibt ausdrücklich offen und wird
nicht hier entschieden. Es wurden **keine neuen Entscheidungen erfunden**, keine Issue-/PR-
Status geändert und keine weiteren Roadmap-Pakete berührt.
