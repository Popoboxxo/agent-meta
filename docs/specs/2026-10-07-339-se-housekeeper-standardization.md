---
status: APPROVED
spec-id: SPEC-339-SE-HOUSEKEEPER-2026-10-07
title: "SE-Kaskaden-Standardisierung — se-housekeeper & Rest-Arbeit (#339)"
issue: 339
date: 2026-10-07
author_agent: concept-architect
supersedes_concept: docs/concepts/archive/2026-06-se-cascade-optimization-339.md
size: M
approved_date: 2026-10-07
approved_by: concept-reviewer
---

# SE-Kaskaden-Standardisierung — se-housekeeper & Rest-Arbeit — Design

> spec-id: SPEC-339-SE-HOUSEKEEPER-2026-10-07
> Basiert auf: freigegebenes Konzept `docs/concepts/archive/2026-06-se-cascade-optimization-339.md`
> (Commit `03db437c`), normative Referenz `knowledge/wiki/concepts/se-cascade-optimization-339.md`.

---

## 0. Kernbefund (Ist-Zustand korrigiert die Auftrags-Prämisse)

Die Annahme „`se-housekeeper` ist die zentrale ausstehende Arbeit mit 5 selbst zu
implementierenden Prüf-Blöcken HK-1..HK-5" **trifft nicht mehr zu.** Die komplette
HK-1..HK-5-Prüflogik existiert bereits als deterministischer, getesteter Python-Gate:

| Konzept-Block (HK) | Implementiert in `scripts/lib/consistency/se_cascade.py` | CLI |
|--------------------|----------------------------------------------------------|-----|
| HK-1 Dateinamen/Taxonomie | `check_taxonomy` (+ `_vN`-Suffix-Verbot) | `sync.py --validate-se` |
| HK-2 L2-Trennregel | `check_l2_separation` (H2-Whitelist + Arch-Term-Heuristik) | dito |
| HK-3 ADR-Verlinkung | `check_open_adrs` + `check_adr_conventions` (+ 5 Sub-Checks) | dito |
| HK-4 Review-Protokoll | `check_review_conventions` + `_check_review_coverage` | dito |
| HK-5 Frontmatter-Schema | `check_req_frontmatter` (Enums + Pflichtschlüssel + optionale Felder) | dito |

Der Gate ist read-only (`lib/se_validate.py`: „must never write files"), CI-fähig
(Exit 1 bei Findings), getestet (`tests/test_se_validate.py`, positiv+negativ je Check)
und registriert (`sync.py:187,649`). `has_se_artifacts()` überspringt Projekte ohne
`docs/se`-Artefakte graceful (Exit 0).

**Konsequenz für diese Spec:** Die eigentliche Rest-Arbeit ist klein und die
zentrale Design-Entscheidung lautet: *Keinen LLM-Agenten bauen, der deterministische
Regex-/Enum-Checks nachbaut.* Siehe DECISION-1.

### Präziser B1–B5-Status

| Befund | Schema | Prüflogik (Code) | Verdikt |
|--------|--------|------------------|---------|
| **B1** ADR-Standard | `schemas/se-adr.schema.json` ✅ | `check_adr_conventions` + Duplikat-, ID-, superseded_by-, affected_reqs-Checks ✅; Skill `.claude/skills/se-cascade-adr-standard/SKILL.md` ✅ | **code-complete** (Validierung). Lifecycle-*Transitionen* (proposed→accepted) sind Workflow, nicht Validierung — nicht automatisiert, nicht erforderlich. |
| **B2** REQ-Frontmatter | `schemas/se-requirements.schema.json` ✅ | `check_req_frontmatter` + `_check_optional_req_fields` ✅ | **code-complete.** Validierung via Python-Enum-Konstanten (`REQ_ENUMS`), NICHT via `jsonschema`-Load — bewusst (keine Nicht-Stdlib-Deps, siehe DECISION-2). |
| **B3** Taxonomie | — | `check_taxonomy` (flache Taxonomie + `_vN`-Verbot) ✅ | **partial.** Flache Taxonomie erzwungen. Verschachtelte Zellen-Struktur (Sektion 7 d. Konzepts: System/Component-Postfix, cell-local `.se-state.yaml`, Rekursion) **NICHT erzwungen** → einzige substanzielle Validierungslücke. |
| **B4** L2-Trennregel | — | `check_l2_separation` ✅ | **code-complete.** |
| **B5** Review-Lifecycle | `schemas/se-review.schema.json` ✅ | `check_review_conventions` + `_check_review_id` + `_check_review_coverage` ✅ | **code-complete** (ID-Format RVW-YYYY-MM-DD-NNN, target_req-Integrität, Coverage). 4-Phasen-State-Machine-Transitionen nicht automatisiert — nicht erforderlich für Compliance-Prüfung. |
| B6 Bottom-Up | — | — | **nicht implementiert.** Außerhalb des HK-Scopes und außerhalb des Auftrags-Scopes (B1–B5). Nur vermerkt. |

`se-housekeeper`-**Agent**: existiert nirgends (nur in Konzept-Dokumenten). Keine
Rolle in `config/role-defaults.yaml`, kein Template in `agents/1-generic/`.
`docs/se/**` ist im Repo noch leer (Dogfood-Ziel, siehe OQ-5).

---

## 1. Problem / Ziel / Nicht-Ziele

### Problem
B1–B5 sind als deterministischer Gate ausgeliefert, aber (a) der Gate ist nur ein
CLI-Lauf ohne Rollen-/Eskalations-Schicht — Findings werden nicht an die zuständigen
SE-Rollen (`se-requirements`/`se-critic`/`se-architect`) geroutet; (b) die
verschachtelte Zellen-Struktur (B3-erweitert, Konzept-Sektion 7) wird nicht geprüft;
(c) die 13 offenen Fragen des Konzepts sind nie formal aufgelöst worden.

### Ziel
1. Entscheiden und festschreiben, ob/wie ein `se-housekeeper`-Agent existiert — und
   zwar als **dünner Orchestrierungs-/Eskalations-Wrapper** um den bestehenden Gate,
   nicht als Re-Implementierung.
2. Die eine echte Validierungslücke (B3 verschachtelte Zellen) spezifizieren.
3. Alle offenen Fragen evidenzbasiert auflösen oder als echte User-Entscheidung flaggen.

### Nicht-Ziele
- Re-Implementierung von HK-1..HK-5 (bereits erledigt).
- B6 Bottom-Up-Rückkopplung, viz-Logger-Events, Admin-UI (Konzept-Sektionen 6/8/9 —
  separate Issues, nicht B1–B5).
- Auto-Fix / schreibende Operationen (read-only-Prinzip, DECISION-3).
- Migrations-Script `migrate-se-frontmatter.py` (eigene Phase; hier nur referenziert).
- **Keine Implementierung in dieser Welle** — Spec+Review only (Coordinator-Scope).

---

## 2. System-Design

### 2.1 Component map

| Komponente | Art | Verantwortung (eine) | Status |
|------------|-----|----------------------|--------|
| `se_cascade.py` | bestehend | Deterministische B1–B5-Prüfung, liefert `list[Finding]` | ✅ vorhanden |
| `se_validate.py` | bestehend | CLI-Handler `--validate-se`, read-only, Exit-Code-Gate | ✅ vorhanden |
| **`check_cell_structure` (neu)** | Funktion in `se_cascade.py` | B3-erweitert: Postfix-Konvention, cell-local `.se-state.yaml`, Rekursions-Konsistenz | ❌ neu |
| **`se-housekeeper.md` (neu, optional)** | Agent-Template | Gate aufrufen, Findings interpretieren, an SE-Rollen eskalieren | ❌ neu, siehe DECISION-1 |
| `role-defaults.yaml` / `placeholders.py` / `delegation_table.py` | bestehend | Rollen-Registrierung + Conditional-Injection `SE_ENABLED` | Änderung nur falls Agent gebaut wird |

**Warum nicht eine Komponente mehr (eigener `housekeeper_runner.py`)?** Der Gate ist
bereits als CLI-Modus vorhanden; ein zweiter Runner wäre Duplikat. DECISION-4.

**Warum nicht null Komponenten (Agent ganz weglassen)?** Findings-Routing/Eskalation
ist genuine Agenten-Arbeit (Urteil, A2A-Handoff), die der Gate nicht leisten kann —
aber nur falls der Eskalationsbedarf real ist. Siehe DECISION-1 (Empfehlung: dünner
Wrapper, Bau nur bei bestätigtem Bedarf).

### 2.2 Interface contracts

**A) Neue Prüffunktion (falls B3-Lücke geschlossen wird):**

```python
# scripts/lib/consistency/se_cascade.py
def check_cell_structure(inv: SEInventory) -> list[Finding]:
    """B3 (Sektion 7): nested cell structure under L1/ and L2/.

    - Directory on L1/ or L2/ level that is not a taxonomy dir and does not
      end in 'System'/'Component' -> ERROR se-cascade.cell-postfix-missing
    - Cell dir without exactly one '.se-state.yaml' -> WARNING
      se-cascade.cell-state-missing
    - File with _iter-N / _critic- suffix is exempt from the _vN ban (already
      handled: VERSION_SUFFIX_RE matches _v<N> only, not _iter-N).
    """
```
- Einhängen in `run_se_cascade_checks()` (eine Zeile, analog zu `check_taxonomy`).
- Severity-Policy wie etabliert: harte Strukturverstöße ERROR, Lifecycle-/Vollständigkeits-Lücken WARNING.
- Datenbesitz: liest nur `SEInventory` (bereits gescannt) + Verzeichnis-Iteration. Kein neuer Scan-Pfad.

**B) `se-housekeeper`-Agent (falls gebaut) — read-only Wrapper:**

```yaml
# agents/1-generic/se-housekeeper.md (Frontmatter)
name: se-housekeeper
version: 1.0.0
description: "Read-only SE-Compliance: ruft --validate-se, interpretiert Findings, eskaliert."
workflow_tier: optional
se_only: true
tools: [Read, Glob, Grep, Bash]   # Bash NUR fuer: python3 scripts/sync.py --validate-se
```
- **Input (A2A):** `audit_request` | `post_implementation_check` (scope optional, default `docs/se`).
- **Verarbeitung:** genau ein Shell-Aufruf `python3 scripts/sync.py --validate-se`; Agent parst den Report, re-implementiert KEINE Checks.
- **Eskalations-Routing (Fehlerpfade):** HK-1→`se-requirements` (Rename), HK-2→`se-critic` (Inhalt extrahieren), HK-3→`se-architect` (ADR), HK-4→`se-critic` (Review nachholen), HK-5→`se-requirements` (Frontmatter). Eskalation per Text-Verweis, nicht per Tool-Call (Worker-Anti-Rekursion).
- **Output (A2A):** `housekeeper_report` (STATUS/RESULT/ARTIFACTS); keine Schreibzugriffe, 0 Auto-Fixes.

### 2.3 Data flow
`docs/se/**` (MD-Artefakte, committed) → `_scan_inventory()` → `SEInventory` →
Prüffunktionen → `list[Finding]` → `_print_se_report()` → Exit-Code (CLI) bzw.
Agent-Parsing → Eskalations-Handoff. Persistenz/State-Ownership: keine — der Pfad ist
vollständig read-only. Findings sind flüchtig (stdout/Exit-Code); kein Report-File.

---

## 3. Trade-off decisions

```
DECISION-1
context: Konzept fordert se-housekeeper-Agent mit 5 Pruefbloecken; diese sind bereits als Python-Gate erledigt.
choice: Agent — falls ueberhaupt — nur als duenner read-only Wrapper (Gate aufrufen + Findings eskalieren). Bau erst bei bestaetigtem Eskalationsbedarf; andernfalls reicht `--validate-se` in CI.
alternatives:
  - Voller LLM-Agent mit eigener Pruef-Logik: verworfen — dupliziert deterministischen, getesteten Code; nicht-deterministisch, Token-Kosten, schlechter fuer CI.
  - Agent ganz weglassen: zulaessig und default, falls Routing manuell/CI ausreicht (der Gate deckt die Compliance-Pruefung vollstaendig ab).
consequences: einfacher: kein Code-Duplikat, CI-Gate bleibt Single Source. haerter: Findings-Routing bleibt manuell, bis der duenne Wrapper gebaut wird.
```
```
DECISION-2
context: HK-5 im Konzept als "jsonschema Validate" gegen se-requirements.schema.json beschrieben.
choice: Enum-/Pflichtschluessel-Pruefung in Python-Konstanten (`REQ_ENUMS`) beibehalten, KEIN jsonschema-Load.
alternatives: jsonschema-Bibliothek laden — verworfen: `jsonschema` ist nicht Stdlib; CLAUDE.md verbietet Nicht-Stdlib-Deps.
consequences: einfacher: dependency-frei, bereits implementiert+getestet. haerter: Schema-Datei und Python-Konstanten muessen synchron gehalten werden (eine Vokabular-Quelle dupliziert; akzeptabel, Enum-Satz ist klein+stabil).
```
```
DECISION-3
context: Konzept-OQ-3 fragt nach optionalem Auto-Fix (--fix).
choice: Read-only, 0 Auto-Fixes — fuer Gate UND Agent.
alternatives: --fix-Flag fuer triviale Renames — verworfen (vorerst): erhoeht Blast-Radius, bricht read-only-Garantie von se_validate.py; Fixes gehoeren in Migrations-Script / zustaendige Rolle.
consequences: einfacher: read-only-Garantie bleibt, CI-sicher. haerter: Fixes manuell/ueber Eskalation.
```
```
DECISION-4
context: Konzept plant separaten housekeeper_runner.py CLI-Wrapper.
choice: Keinen neuen Runner — `sync.py --validate-se` ist der kanonische Einstieg.
alternatives: scripts/se-housekeeper.py — verworfen: Duplikat des bestehenden CLI-Modus.
consequences: einfacher: ein Einstiegspunkt. haerter: keiner.
```
```
DECISION-5
context: B3 verschachtelte Zellen-Struktur (Sektion 7) ist nicht geprueft; der Gate erzwingt flache Taxonomie.
choice: Neue Funktion check_cell_structure() in se_cascade.py (ERROR fuer Postfix, WARNING fuer fehlendes .se-state.yaml). Nur bauen, wenn Projekte die verschachtelte Struktur tatsaechlich nutzen.
alternatives: Nested-Struktur hart verpflichtend ab sofort — verworfen: agent-meta hat noch keine docs/se-Artefakte; verfrueht. Flach bleibt gueltiger Default (OQ-11).
consequences: einfacher: inkrementell, additive Pruefung. haerter: bis dahin keine Postfix-Durchsetzung — akzeptabel, da keine Nested-Artefakte existieren.
```

ADR-Persistenz: Diese Entscheidungen folgen dem `se-cascade-adr-standard`-Skill; bei
Umsetzung als `docs/se/ADR/ADR-NNN_*.md` ablegen (nicht hier duplizieren).

---

## 4. Auflösung der offenen Fragen

Die 7 vom Auftrag genannten (= Konzept-OQ 1–7) plus die 6 Struktur-Fragen (OQ 8–13).

| OQ | Frage | Auflösung (Evidenz) | Status |
|----|-------|---------------------|--------|
| 1 | `se-required` erzwingen? | **Aufgelöst:** keine Kopplung nötig. `has_se_artifacts()` überspringt Projekte ohne `docs/se` graceful (Exit 0). Gate ist opt-in via Artefakt-Präsenz, unabhängig vom Flag. | resolved |
| 2 | Default `implementation_state`? | **Aufgelöst:** `not_implemented` (ehrlich). Validator erzwingt Präsenz (ERROR bei Fehlen), injiziert keinen Default; Default setzt das Migrations-Script. | resolved |
| 3 | Auto-Fix in Phase 5? | **Aufgelöst:** Nein. `se_validate.py` ist explizit read-only; siehe DECISION-3. | resolved |
| 4 | Review-IDs committen? | **Aufgelöst:** Ja, committen. `_check_review_coverage` referenziert `docs/se/reviews/`-Dateien — Coverage-Check funktioniert nur bei committed files. Design setzt es bereits voraus. | resolved |
| 5 | Pilotprojekt? | **Aufgelöst:** agent-meta selbst. `docs/se/**` ist leer → Dogfood-Ziel. | resolved |
| 6 | `se-housekeeper` Tier? | **Aufgelöst (re-scoped):** Falls gebaut — `workflow_tier: optional`, `se_only: true`, read-only tools `[Read, Glob, Grep, Bash]`, Bash nur für `--validate-se`. Tier `senior` (role-defaults-Konvention). | resolved |
| 7 | Migrations-Script Auto-Commit? | **Aufgelöst:** Nein, nur Working-Tree. Repo-Regel: Commits nur über freigeschaltete Rolle/`git`-Agent, Scripts committen nicht selbst. | resolved |
| 8 | Postfix hart erzwingen? | **Bedingt aufgelöst:** Ja als ERROR — aber erst mit `check_cell_structure` (DECISION-5), d.h. wenn Nested-Struktur genutzt wird. Bis dahin nicht erzwingbar (keine Artefakte). | resolved (gated) |
| 9 | cell-local `.se-state.yaml`? | **Aufgelöst:** cell-local (Resume ohne Index-Lookup), geprüft als WARNING in `check_cell_structure`. | resolved |
| 10 | `source: graph-json` Marker überschreiben? | **Aufgelöst:** warnen + Backup `.md.bak`, kein stilles Überschreiben. Betrifft Adapter (nicht HK-Scope) — nur vermerkt. | resolved (scope: adapter) |
| 11 | Flat-Modus abschalten wann? | **Aufgelöst:** Flat bleibt vorerst gültiger Default (Gate erzwingt flache Taxonomie). Hard-Fail auf flach erst nach Nested-Adoption — nicht jetzt. | resolved |
| 12 | Rekursive `sub_components`? | **Offen (User):** Schema-Erweiterung `se-decomposition.schema.json` auf beliebige Tiefe betrifft den Decomposition-/Export-Pfad, nicht die HK-Compliance. Nicht aus Code entscheidbar — Produkt-Entscheidung. | **FLAGGED** |
| 13 | POC-Referenz auslagern? | **Aufgelöst:** irrelevant/trivial (Doku-Organisation). Inline belassen. | resolved |

**Einzige echte User-Entscheidung:** OQ-12 (rekursive `sub_components`-Schematiefe) —
außerhalb des HK-Scopes, Produkt-/Decomposition-Frage. Alle übrigen sind durch
Codebase-Evidenz bzw. etablierte Repo-Regeln auflösbar.

---

## 5. Phasen-Plan (Rest-Arbeit)

Reihenfolge nach Abhängigkeit; jede Phase eigenständig lieferbar.

| Phase | Inhalt | Dateien | Abhängigkeit | Aufwand |
|-------|--------|---------|--------------|---------|
| **R1** | B3-Lücke: `check_cell_structure()` + Einhängen + Tests | `se_cascade.py`, `tests/test_se_validate.py` | — | S |
| **R2** (optional) | `se-housekeeper`-Wrapper-Agent + Rollen-Registrierung + Conditional-Injection | `agents/1-generic/se-housekeeper.md`, `config/role-defaults.yaml`, `scripts/lib/placeholders.py`, `scripts/lib/delegation_table.py`, `tests/` | R1 | M |
| **R3** (separat, nicht B1–B5) | Migrations-Script, B6, viz-Events | je eigenes Issue | R1 | — |

**Empfehlung:** R1 zuerst (echte Lücke, additiv, kleiner Diff). R2 nur bei bestätigtem
Eskalationsbedarf (DECISION-1) — sonst deckt `--validate-se` die Compliance vollständig.
R3 ist nicht Teil von #339-B1–B5.

---

## 6. Akzeptanzkriterien

- **AC-1 (R1):** `check_cell_structure` meldet für ein Fixture mit (a) Ordner ohne
  `System`/`Component`-Postfix ERROR, (b) Zelle ohne `.se-state.yaml` WARNING,
  (c) Datei mit `_iter-N`-Suffix KEIN Finding. Positiv+negativ in `test_se_validate.py`.
- **AC-2 (R1):** `sync.py --validate-se` auf flachem `docs/se` ohne Nested-Zellen bleibt
  unverändert grün (Backward-Compat, keine False Positives).
- **AC-3 (R2, falls gebaut):** `se-housekeeper` ruft `--validate-se`, re-implementiert
  0 Checks (verifiziert via Template-Review: kein Regex/Enum im Prompt), eskaliert jeden
  der 5 HK-Typen an die korrekte Rolle, schreibt 0 Dateien.
- **AC-4 (R2):** Sync mit `SE_ENABLED=false` erzeugt byte-identischen Output wie vor R2
  (Zero-Overhead; `se-housekeeper` nur bei `SE_ENABLED=true` injiziert).
- **AC-5:** `python3 -m pytest -q tests/test_se_validate.py` grün.

---

## 7. Risiken

| Risiko | W | I | Mitigation |
|--------|---|---|------------|
| R2 baut doch Logik nach → Code-Duplikat | mittel | hoch | AC-3 Template-Review: Agent darf nur `--validate-se` aufrufen, keine Checks. |
| `check_cell_structure` erzeugt False Positives auf flachen Repos | mittel | mittel | AC-2; Funktion greift nur innerhalb `L1/`,`L2/`-Zellen, nicht auf flacher Ebene. |
| Enum-Duplikat (Schema vs. `REQ_ENUMS`) driftet | niedrig | niedrig | Ein kleiner, stabiler Enum-Satz; optional Test der beide vergleicht. |
| Scope-Creep nach B6/viz/Admin-UI | mittel | mittel | §1 Nicht-Ziele + §5 R3 als separate Issues abgegrenzt. |

---

## 8. Test-Plan

- **Einheit:** `tests/test_se_validate.py` erweitern um `check_cell_structure` (positiv:
  valide Zelle; negativ: Postfix fehlt, `.se-state.yaml` fehlt, Doppel-State; Exempt:
  `_iter-N`). Bestehende B1–B5-Tests bleiben Regressions-Basis.
- **Integration:** `sync.py --validate-se` gegen (a) leeres Repo → Exit 0,
  (b) Fixture mit absichtlichen Verstößen → Exit 1 + korrekte Finding-Anzahl.
- **Conditional-Injection (nur R2):** `tests/` prüft `SE_ENABLED=false` ⇒ kein
  `se-housekeeper` im Output (byte-identisch), analog bestehendem SE-Injection-Muster.
- **Invocation:** `python3 -m pytest -q tests/test_se_validate.py` (rootdir-weiter
  pytest ist durch `external/`-Collection-Errors gebrochen — tests/ explizit angeben).

---

## 9. Impact & Risk Zones

- **Blast-Radius R1:** minimal — eine additive Funktion + ein Einhäng-Punkt in
  `run_se_cascade_checks`. Kein bestehender Check verändert.
- **Blast-Radius R2:** mittel — berührt Syncer-Rollen-Pipeline (`role-defaults`,
  `placeholders`, `delegation_table`, Conditional-Injection). Gleiches Muster wie
  `se-critic` (Referenz vorhanden).
- **Coupling-Hotspot:** Vokabular-Duplikat Schema ↔ `REQ_ENUMS` (DECISION-2).
- **Migration:** keine für R1/R2. Bestandsprojekte nutzen `--validate-se` unverändert.

---

## 10. Offene Punkte für Reviewer / User

1. **OQ-12** (rekursive `sub_components`-Schematiefe) — einzige echte User-Entscheidung;
   Decomposition-/Export-Scope, nicht HK.
2. **R2 bauen?** — Entscheidung ob der dünne Wrapper-Agent überhaupt benötigt wird
   (DECISION-1) oder `--validate-se` in CI genügt.
3. **Größen-Korrektur:** Die Rest-Arbeit ist **M**, nicht L. Die L-Klassifikation des
   Coordinators war für das *ursprüngliche* 6-Phasen-Konzept korrekt; nach Auslieferung
   von B1–B5 (Issue #338) verbleibt M (R1=S, R2=M). Cross-cutting bleibt es (Syncer +
   Agents + Schemas), daher Design-Doc gerechtfertigt.
