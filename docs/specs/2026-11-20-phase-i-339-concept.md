---
doc_type: concept
status: APPROVED
doc_id: CONCEPT-339-PHASE-I-2026-11-20
title: "Phase-I-Konzept — SE-Kaskaden-Standardisierung / Rest-Arbeit (#339)"
issue: 339
date: 2026-11-20
author_agent: developer
size: M
approved_date: 2026-11-20
approved_by: "Nutzergo 2026-11-20 (E-31, Re-Approval Phase-I-Start)"
roadmap_ref: "PR 0.7 / P33 / Phase I"
traceability: ["#339", "P33", "E-31", "Entscheidung 30", "Entscheidung 54"]
supersedes_concept: docs/concepts/archive/2026-06-se-cascade-optimization-339.md
---

> Status: APPROVED (Nutzergo 2026-11-20, E-31 — Re-Approval Phase-I-Start)

# Phase-I-Konzept — SE-Kaskaden-Standardisierung / Rest-Arbeit (#339)

> **Re-Approval:** Mit Nutzergo vom 2026-11-20 ist das Re-Approval für #339 erteilt
> (E-31: „#339 Re-Approval bei Phase-I-Start", Roadmap §4/§6). Status `APPROVED`
> durch User-Freigabe — nicht durch Self-Approve und nicht durch den Reviewer.
> **Keine neuen Entscheidungen:** Dieses Dokument führt ausschließlich die bereits
> freigegebenen Inhalte aus Issue #339, Roadmap PR 0.7 / P33 / E-31 und der
> approbierten Spec `docs/specs/2026-10-07-339-se-housekeeper-standardization.md`
> (inkl. Review, `verdict: APPROVED`) zusammen. Es werden keine neuen Design-,
> Produkt- oder scope-Entscheidungen getroffen.

---

## 1. Problemstellung

Issue #339 („[meta-feedback] SE-Kaskade: Standardisierungsbedarf bei ADRs,
REQ-Feldern, Strategie-Dokumenten und L2-Decomposition-Konventionen") dokumentiert
sechs Befunde aus einer realen SE-Kaskaden-Durchführung (L0 → L1 → L2 → V&V) im
ReqFlow-POC:

| Befund | Inhalt (Issue #339) | Priorität (Issue) |
|--------|---------------------|-------------------|
| B1 | ADRs ohne Standard (Verzeichnis, Namensschema, Frontmatter, Lifecycle, Review-Zuständigkeit, L1/L2-Verknüpfung) | HOCH |
| B2 | Neue REQ-Felder ohne Standardisierung (`implementation_state`, `review_state`, `test_status`, `open_adrs` — uneinheitliche Werte, kein Frontmatter-Schema) | HOCH |
| B3 | Strategie-Dokumente ohne Standard / Taxonomie; Versionsnummern im Dateinamen | MITTEL |
| B4 | L2-Dokumente enthalten Decomposition, Reviews und Traceability inline statt in dedizierten Artefakten | HOCH |
| B5 | Fehlende Review-Iteration-Konvention (kein Protokoll, keine ID, kein formaler Abschluss) | MITTEL |
| B6 | Fehlende Implementierungs-Rückkopplung (Bottom-Up, Suspect-Mark, ADR-Impact) | MITTEL |

**Korrigierter Ist-Zustand (aus der approbierten Spec, §0):** Die ursprüngliche
Auftragsprämisse „`se-housekeeper` ist die ausstehende Arbeit mit 5 selbst zu
implementierenden Prüfblöcken HK-1..HK-5" trifft nicht mehr zu. HK-1..HK-5 sind
bereits als deterministischer, getesteter, read-only Python-Gate umgesetzt:

| HK | Prüflogik | CLI |
|----|-----------|-----|
| HK-1 Dateinamen/Taxonomie | `check_taxonomy` (`+_vN`-Verbot) | `sync.py --validate-se` |
| HK-2 L2-Trennregel | `check_l2_separation` | dito |
| HK-3 ADR-Verlinkung | `check_open_adrs` + `check_adr_conventions` | dito |
| HK-4 Review-Protokoll | `check_review_conventions` + Coverage | dito |
| HK-5 Frontmatter-Schema | `check_req_frontmatter` (`REQ_ENUMS`) | dito |

B1, B2, B4 und B5 sind damit **code-complete**. B3 ist **partial** (flache Taxonomie
erzwungen, verschachtelte Zellen-Struktur nicht). B6 ist **nicht implementiert** und
außerhalb des HK-/B1–B5-Scopes. Die Rest-Arbeit ist klein (Aufwand **M**, nicht L).

---

## 2. Scope

### In Scope (Phase-I-Konzept / spätere Rest-Arbeit)

- Re-Approval der bereits `APPROVED`en Spec gemäß Entscheidung 30 / E-31 — das erste
  und einzige Phase-I-Gate für #339 (Nutzergo 2026-11-20).
- Bekräftigung der aus der Spec übernommenen Entscheidungen DECISION-1 bis DECISION-5
  (dünner Wrapper statt LLM-Re-Implementierung; `REQ_ENUMS` statt `jsonschema`;
  read-only; kein neuer Runner; additive `check_cell_structure`).
- Die eine substanzielle Validierungslücke B3 (verschachtelte Zellen-Struktur,
  `check_cell_structure`) als Rest-Arbeit R1 festschreiben — unverändert aus Spec §5.
- Anpassung des REQ-ID-Formats an Entscheidung 54: strikt `REQ-<BEREICH>-<NN>`;
  das in #339 verwendete `REQ-L2-AT-018` wird bei der Neufreigabe angepasst (der
  #1167-Validator in Phase H lehnt das alte Format ab).
- Traceability auf #339 / P33 / PR 0.7 / E-31 / Entscheidung 30 / Entscheidung 54.

### Out of Scope

- Re-Implementierung von HK-1..HK-5 (bereits erledigt, Single Source ist der Gate).
- B6 Bottom-Up-Rückkopplung, viz-Logger-Events, Admin-UI (Spec §1 Nicht-Ziele; R3).
- Migrations-Script `migrate-se-frontmatter.py` (eigene Phase, hier nur referenziert).
- Auto-Fix / schreibende Operationen (DECISION-3: read-only-Garantie).
- Neuer Runner / CLI-Einstieg (DECISION-4: `sync.py --validate-se` bleibt kanonisch).
- OQ-12 (rekursive `sub_components`-Schematiefe) — laut Spec §4 einzige echte
  offene User-Entscheidung, außerhalb des HK-Scopes; hier **bewusst nicht entschieden**
  (keine neuen Entscheidungen gemäß Nutzergo).
- Änderungen an Master-Roadmap, Worker-Control-/Batch0-Dateien, archivierten Plänen
  oder anderen Roadmap-Paketen.
- **Keine Implementierung in diesem PR** (siehe §6).

---

## 3. Ansatz mit Alternativen / Trade-offs

Alle Alternativen und Verdikte stammen aus der approbierten Spec §3/§4 und werden
hier unverändert wiedergegeben — keine neuen Abwägungen.

| Entscheidung | Wahl (approbiert) | Verworfene Alternative | Trade-off |
|--------------|-------------------|------------------------|-----------|
| DECISION-1 | `se-housekeeper` — falls überhaupt — nur als dünner read-only Wrapper (Gate aufrufen, Findings eskalieren). Bau erst bei bestätigtem Eskalationsbedarf; sonst genügt `--validate-se` in CI. | Voller LLM-Agent mit eigener Prüflogik (dupliziert deterministischen Code, nicht-deterministisch, Token-Kosten, schlechter für CI). Agent ganz weglassen ist zulässiger Default. | Einfacher: kein Code-Duplikat, CI-Gate bleibt Single Source. Härter: Findings-Routing bleibt manuell, bis der Wrapper gebaut wird. |
| DECISION-2 | Enum-/Pflichtschlüssel-Prüfung in Python-Konstanten `REQ_ENUMS`, kein `jsonschema`-Load. | `jsonschema`-Bibliothek (nicht Stdlib; von den Repo-Konventionen verboten). | Dependency-frei und bereits getestet; Vokabular-Duplikat Schema ↔ `REQ_ENUMS` muss synchron gehalten werden (kleiner, stabiler Enum-Satz). |
| DECISION-3 | Read-only, 0 Auto-Fixes — für Gate und Agent. | `--fix`-Flag für triviale Renames (erhöht Blast-Radius, bricht read-only-Garantie). | CI-sicher; Fixes manuell / über Eskalation / Migrations-Script. |
| DECISION-4 | Kein neuer Runner; `sync.py --validate-se` ist kanonischer Einstieg. | `scripts/se-housekeeper.py` (Duplikat des bestehenden CLI-Modus). | Ein Einstiegspunkt, keine Nachteile. |
| DECISION-5 | Additive Funktion `check_cell_structure()` in `se_cascade.py` (ERROR bei fehlendem Postfix, WARNING bei fehlendem `.se-state.yaml`). Nur bauen, wenn Nested-Struktur tatsächlich genutzt wird. | Nested-Struktur hart verpflichtend ab sofort (verfrüht: `docs/se/**` ist leer; Flat bleibt gültiger Default, OQ-11). | Inkrementell, kleiner Diff; bis zur Adoption keine Postfix-Durchsetzung — akzeptabel. |

**Phasen-Plan der Rest-Arbeit (unverändert aus Spec §5):**

- **R1** — `check_cell_structure()` + Einhängen + Tests (Aufwand S, keine Abhängigkeit). Empfehlung: zuerst.
- **R2 (optional)** — dünner `se-housekeeper`-Wrapper-Agent + Rollen-Registrierung + Conditional-Injection (Aufwand M, hängt an R1). Nur bei bestätigtem Eskalationsbedarf.
- **R3 (separat, nicht B1–B5)** — Migrations-Script, B6, viz-Events (je eigenes Issue).

---

## 4. Akzeptanzkriterien

Unverändert aus der approbierten Spec §6 (AC-1 bis AC-5). Sie gelten für die
spätere Implementierung, nicht für diesen Docs-only-PR.

- **AC-1 (R1):** `check_cell_structure` meldet für ein Fixture mit (a) Ordner ohne
  `System`/`Component`-Postfix ERROR, (b) Zelle ohne `.se-state.yaml` WARNING,
  (c) Datei mit `_iter-N`-Suffix KEIN Finding. Positiv- und Negativfall in
  `test_se_validate.py`.
- **AC-2 (R1):** `sync.py --validate-se` auf flachem `docs/se` ohne Nested-Zellen
  bleibt unverändert grün (Backward-Compat, keine False Positives).
- **AC-3 (R2, falls gebaut):** `se-housekeeper` ruft `--validate-se`, re-implementiert
  0 Checks (Template-Review: kein Regex/Enum im Prompt), eskaliert jeden der 5
  HK-Typen an die korrekte Rolle, schreibt 0 Dateien.
- **AC-4 (R2):** Sync mit `SE_ENABLED=false` erzeugt byte-identischen Output wie vor
  R2 (Zero-Overhead; Injektion nur bei `SE_ENABLED=true`).
- **AC-5:** `python3 -m pytest -q tests/test_se_validate.py` grün.

---

## 5. Risiken / Annahmen

Unverändert aus der approbierten Spec §7/§9:

| Risiko | W | I | Mitigation |
|--------|---|---|------------|
| R2 baut doch Logik nach → Code-Duplikat | mittel | hoch | AC-3 Template-Review: Agent darf nur `--validate-se` aufrufen, keine Checks. |
| `check_cell_structure` erzeugt False Positives auf flachen Repos | mittel | mittel | AC-2; Funktion greift nur innerhalb `L1/`/`L2/`-Zellen, nicht auf flacher Ebene. |
| Enum-Duplikat (Schema ↔ `REQ_ENUMS`) driftet | niedrig | niedrig | Kleiner, stabiler Enum-Satz; optional vergleichender Test. |
| Scope-Creep nach B6/viz/Admin-UI | mittel | mittel | §2 Nicht-Ziele + R3 als separate Issues abgegrenzt. |

**Annahmen:**

- `scripts/lib/consistency/se_cascade.py` und `sync.py --validate-se` bleiben die
  Single Source der HK-Prüfung (Spec §0, durch Review verifiziert).
- `docs/se/**` ist im Repo noch leer (Dogfood-Ziel, OQ-5) — daher ist R1 additiv
  und R2 nur bedingt nötig.
- Der Re-Approval-Prozess läuft über den User (Nutzergo 2026-11-20), nicht über
  einen Reviewer-/Self-Approve (Entscheidung 30, E-31).

---

## 6. Umsetzung — späterer PR (Welle 7)

Dieses Dokument ist **Docs-only**. Es enthält keine Implementierung, kein TDD,
keine Code-Änderungen und keine Rebaseline — die ACs in §4 beschreiben den
Soll-Zustand für eine spätere Umsetzung, nicht für diesen PR.

Die Implementierung erfolgt in einem **eigenen späteren PR** in Welle 7 (W7)
der Roadmap (§3.9: „Je Issue eigener Plan + PR nach APPROVED-Concept aus 0.7
(#896, #339 nach Re-Approval, …)"), entsprechend Entscheidung 53 des
Phase-I-Konzept-Fahrplans (eigene J-Phase je Issue mit eigenem Plan und PR).
Dieser PR hier liefert ausschließlich das freigegebene Konzept.

---

## 7. Traceability

| Referenz | Bezug |
|----------|-------|
| Issue #339 | Ursprung der 6 Befunde B1–B6; Konzept-Phase abgeschlossen (Kommentar 2026-06-28); Spec `APPROVED` |
| Roadmap PR 0.7 | `docs/phase-i-<issue>` je Issue; Rang 1–3 zuerst (#896, **#339**, #681) |
| Roadmap P33 | Phase-I-Konzept-PRs; „#339 Re-Approval bei Phase-I-Start" |
| E-31 | „Specs/Konzepte einzeln nach Review, Reihenfolge P33; #339 Re-Approval bei Phase-I-Start" — Re-Approval erteilt per Nutzergo 2026-11-20 |
| Entscheidung 30 | User-Re-Approval der Spec als erstes Gate; Reviewer-Approval ist keine User-Freigabe |
| Entscheidung 54 | REQ-Format strikt `REQ-<BEREICH>-<NN>`; `REQ-L2-AT-018` wird bei Neufreigabe angepasst |
| `docs/specs/2026-10-07-339-se-housekeeper-standardization.md` | Normative Spec (status: APPROVED), Quelle für DECISION-1..5, AC-1..5, R1/R2/R3 |
| `docs/specs/2026-10-07-339-se-housekeeper-standardization-review.md` | Review, `verdict: APPROVED` |
| `docs/concepts/archive/2026-06-se-cascade-optimization-339.md` | Archiviertes Ursprungskonzept (Konzept-Entwurf v1.2) |
| `docs/superpowers/plans/2026-11-11-phase-i-features-concept.md` | Phase-I-Fahrplan (Block I-339, Decision 30/53/54) |
| Roadmap §3.9 (Welle 7) | Umsetzung in späterem PR nach APPROVED-Concept |
