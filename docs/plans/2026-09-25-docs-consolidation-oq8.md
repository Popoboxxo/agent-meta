---
plan-id: PLAN-DOCS-CONSOLIDATION-2026-09-25
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
title: W0-6 — REC-OQ8, Regenerationsvertrag für docs/INDEX.md
status: done
revision: 0.2
related:
  - docs/plans/2026-09-25-repository-documentation-consolidation.md
  - docs/specs/2026-09-25-repository-documentation-consolidation.md
  - docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md
  - docs/plans/2026-09-25-docs-consolidation-track-a-gate.md
---

# W0-6 — REC-OQ8: Regenerationsvertrag für `docs/INDEX.md`

> Ergebnis-Record der Plan-Task **W0-6** (als **REC-OQ8** geführt).
> Plan `PLAN-DOCS-CONSOLIDATION-2026-09-25`, Spec `SPEC-DOCS-CONSOLIDATION-2026-09-25`
> (Rev. 0.3, `status: APPROVED` vom 2026-09-26). **Autor dieses Records:** `documenter`
> (Rollenangabe; Commit-Leistung bleibt beim `git`-Agenten).
>
> **Nachführung 2026-09-26 (Rev. 0.1 → 0.2):** Ergänzt wurde ausschließlich die
> **Evidenzklassen-Konvention** (global für alle W0-Records) und der **Branch-Bestand** (2
> Branches mit gemeinsamem Präfix, davon 1 aktiv; der überholte bleibt auf Nutzer-Vorgabe
> erhalten). **Der Regenerationsvertrag, die Entscheidung OQ8 (Sync-/Validator-Lauf statt
> `pre-commit`-Hook), der Severity-Stand von V2 und alle Sollwerte bleiben unverändert.**
>
> **Branch-Bestand (gemessen 2026-09-26):** `git branch --list
> 'feat/repository-documentation-consolidation*'` → **2** Zeilen — der **aktive** Wellen-Branch
> `feat/repository-documentation-consolidation-main` und der **überholte** Branch
> `feat/repository-documentation-consolidation` (divergente Doppelkopie der Spec-/Plan-Commits,
> nicht in `main`), der auf ausdrückliche **Nutzer-Vorgabe („nicht löschen")** erhalten bleibt.
> Für OQ8 **ohne Wirkung**; Details: W0-2-Record Kapitel 7.2, offener Punkt **OP-2** dort §10.
>
> **Charakter:** Dieser Record **trifft die Entscheidung nicht**, er **dokumentiert** sie.
> Die normative Quelle bleibt die Spec; bei Widerspruch zwischen diesem Record und der Spec
> gilt die **Spec**. Der Contract-Stand (IC-05, IC-13, IC-22, AC-12, AC-38) ist von dieser
> Entscheidung **nicht** berührt.

## Konvention: Evidenzklassen (global für alle W0-Records)

Jede Verifikationszeile dieses Records trägt die **Evidenzklasse** — also **wie** der Wert
zustande kam. Ohne diese Angabe ist ein „✅" mehrdeutig, weil es gemessene, abgeleitete und
übernommene Werte gleich erscheinen lässt. Enum (geschlossen, genau vier Werte):

| Evidenzklasse | Bedeutung |
|---|---|
| `gemessen` | Der Wert wurde in diesem Vorhaben durch **Ausführung des Kommandos** ermittelt. |
| `gezählt ohne Shell` | Der Wert wurde mit dateisuchender Prüffunktion (**Muster + Trefferzählung**) ermittelt, ohne Shell — inhaltlich identisch zum Kommando, aber kein Shell-Lauf. |
| `aus Record X übernommen` | Der Wert stammt **unverändert** aus einem anderen Record dieses Vorhabens; die Messung ist dort ausgewiesen. |
| `nicht gemessen` | Es liegt **kein** Wert vor. Er wird **nicht** geschätzt und **nicht** erfunden; die Ausführung bleibt einer benannten Instanz vorbehalten. |

Diese Konvention gilt **global für alle sechs W0-Records** dieses Wellen-Blocks und für alle
Folgewellen: ein `✅` **ohne** Evidenzklasse ist unvollständig. In diesem Record ist der
Verifikations-Prüfbefehl `nicht gemessen`; die Verweise auf `llms.txt`-Zeilen und Config-Keys
sind Dateistands-Angaben, keine Messwerte.

## Zweck und Geltungsbereich

Gegenstand ist die Frage **OQ8** aus Spec §11.2: *Wer re-generiert `docs/INDEX.md`, wenn ein
Mensch eine neue `.md` unter `docs/` anlegt?* — V2 ist ab W3 **ERROR** (IC-05, AC-12), jede
neue, getrackte Doku-Datei außerhalb von `archive/` blockiert damit `sync.py --validate`
(= `TEST_COMMAND`, Spec §10) bis ein Sync gelaufen ist.

**Geltung:** Der hier festgehaltene Vertrag gilt für `docs/INDEX.md` in agent-meta und in
allen Consumer-Projekten, in denen `docs-consolidation.enabled` explizit `true` ist
(IC-22). Für Consumer ohne diesen Key bleibt alles inaktiv (Absenz-Default `false`,
IC-22, NFA-04).

**Nicht Gegenstand dieses Records:** Implementierung (W3-6), Code-Änderungen, Config-Änderungen,
Änderungen an Spec, Plan oder Design, neue CLI-Flags, neue Hooks, neue Doku-Dateien.

## 1. Entscheidung

| Feld | Inhalt |
|---|---|
| **Entscheidung** | Die Regenerierung von `docs/INDEX.md` läuft **deterministisch über den vorhandenen Sync-Pfad und den Validator** (`sync.py` im Default-Sync, `--validate` als `TEST_COMMAND`, konfiguriert in `.meta-config/project.yaml`). |
| **Datum** | **2026-09-26** |
| **Entscheider** | **Nutzer**, über `main_chat` an den `orchestrator`; formalisiert und dokumentiert durch `documenter` (W0-6-Ausführung) |
| **Entscheidungsweg** | Produktentscheidung vor Ausführungsbeginn der W3; Record-Pflicht: Plan-Task W0-6, Plan-Kapitel „Wellenübersicht" (`W0-6 REC-OQ8`) und Reihenfolge-/Abhängigkeitsmatrix (Task-Zeile W0-6) |
| **Scope** | Der **Workflow-Vertrag** der Doku-Index-Regenerierung: Auslöser, Owner, Kosten. Kein Code-, Interface- oder Akzeptanzvertrag. |
| **Status in der Spec** | OQ8 steht in **§11.2 „Geschlossen"**; die IC/AC bleiben unverändert, weil kein Code-, sondern ein Workflow-Vertrag betroffen ist (ebenso §10, Workflow-Vertrag-Klausel) |
| **AC-Zuordnung der Task** | **AC-12** (V2-ERROR bei fehlendem Index-Eintrag), **AC-38** (Regressionsgarantie der sechs Szenarien) |

**Vertrag in einem Satz:** Legt ein Mensch eine neue getrackte `docs/**/*.md` an, ist
`--validate` ab W3 **rot**; wer den Vertrag erfüllen will, führt den Sync aus — es gibt
weder einen automatischen Commit-Hook noch eine Dokumentationspflicht in einer
Mitwirkenden-Doku.

## 2. Verworfene Alternativen

Die folgenden drei Wege wurden geprüft und **ausdrücklich verworfen**. Sie erscheinen hier
nominiert, damit die Verifikation (Kapitel 4) die Entscheidungsdokumentation belegt.

### 2.1 `pre-commit`-Hook — **verworfen**

- Dies war die **Empfehlung der Spec** (Risiko R20, §12: „Empfehlung (Commit-Hook)"; siehe
  auch die Formulierung in §11.2 OQ8) und wäre ein **neuer Hook** im Repo.
- **Verwerfungsbegründung:** Der bereits vorhandene, ohnehin verpflichtende Lauf
  (`sync.py` im Default-Sync, `--validate` als `TEST_COMMAND`) erfüllt denselben Zweck
  deterministisch. Ein zusätzlicher Hook wäre ein **zweiter** Auslöserpfad mit eigener
  Pflegepflicht, eigene Fehlerpfade und ein Duplikat des ohnehin roten `--validate`. Die
  Vertragsverletzung bleibt über V2 = **ERROR** sichtbar, ohne dass ein zweiter Mechanismus
  danebensteht.
- **Folge der Verwerfung:** Es entsteht **kein** Hook, **kein** Hook-Skript, **keine** neue
  Hook-Datei, **kein** Eintrag in den Hook-Fakten (`DOCS_HOOKS_COUNT`, `DOCS_HOOKS_1GENERIC_COUNT`
  bleiben unverändert; NFA-01-Absenz zählt nur, was real existiert).

### 2.2 CONTRIBUTING-Regel — **verworfen**

- Alternative: eine Regel in einer Mitwirkenden-Doku, die den Sync- bzw. Validationsschritt
  als Pflicht vor dem Commit festschreibt.
- **Verwerfungsbegründung:** Eine Prosa-Regel ist **nicht deterministisch** und nicht
  prüfbar; sie erzeugt eine neue Doku-Datei, ohne den Zustand zu verbessern. Die Entscheidung
  schließt ausdrücklich **keine neue Doku-Datei** ein — `docs/guides/project.yaml.example`
  bleibt **unverändert** (ebenso §11.2 OQ8). Der Vertrag lebt in **diesem Record** und in
  **Spec §10**, nicht in einer weiteren Handbuchdatei.
- **Folge der Verwerfung:** W3-7 braucht **keinen** Doku-Schritt für OQ8; es entsteht keine
  neue Beitrags-Dokumentation.

### 2.3 Severity-Downgrade von V2 — **verworfen**

- Alternative: `check_docs_index_completeness()` (V2) auf **WARNING** herabstufen, damit
  `--validate` bei einer neuen Doku-Datei nicht rot wird.
- **Verwerfungsbegründung:** V2 ist der **Zweck** der Initiative (Spec §11.2, §12 R20) — die
  Vollständigkeit des generierten Index ist das maschinenlesbare SSoT. Ein Downgrade würde
  das Risiko R20 („Workflow-Vertrag ohne Owner") durch **Abschwächen des Checks** beseitigen
  statt durch einen benannten Owner und einen benannten Auslöser; die Vertragsverletzung
  bliebe unsichtbar, und IC-05/AC-12 müssten angefasst werden.
- **Folge der Verwerfung:** **V2 bleibt ERROR.** `docs-consolidation.checks.strict` (IC-22)
  wird dadurch für V2 **nicht** ausgenutzt; die Strict-Hierarchie der Spec (NFA-04) bleibt
  unberührt.

## 3. Gewählter Weg

**Deterministische Regeneration über den vorhandenen Sync-Pfad und den Validator.**

| Aspekt | Festlegung |
|---|---|
| **Auslöser** | `sync.py` im Default-Sync schreibt `docs/INDEX.md` (IC-13 `sync_docs_consolidation()`); `--validate` prüft den Zustand (IC-05, V2) |
| **Kein neuer Hook** | Es entsteht **kein** `pre-commit`- oder anderer Hook (Kapitel 2.1) |
| **Kein neues CLI-Flag** | Es wird **kein** `sync.py`-Flag ergänzt (NG-4). Jedes neue Flag erzeugt Pflegepflicht in `docs/api/cli-reference.md` — genau diesen Pflegeposten vermeidet die Entscheidung |
| **Keine neue Doku-Datei** | Kein Eintrag in einer Mitwirkenden-/Beitragsdoku, keine Änderung an `docs/guides/project.yaml.example` (Kapitel 2.2) |
| **V2 bleibt ERROR** | Die Vertragsverletzung bleibt sichtbar; kein Severity-Downgrade (Kapitel 2.3) |
| **Absenz-Defaults** | Bleiben **fail-off** für Writer **und** Checks (IC-22, NFA-04, Präzedenz `scripts/lib/knowledge.py`): ohne `docs-consolidation.enabled: true` schreibt der Generator nicht und V1–V9 laufen nicht. Der Vertrag ist damit in Consumer-Projekten ohne explizite Aktivierung **inaktiv** — das ist gewollt und verhindert Seiteneffekte in Fremdprojekten (AC-38) |
| **Kosten des Vertrags** | Ein zusätzlicher Sync-Lauf zwischen Datei-Anlage und Commit. Der Default-Sync läuft ohnehin, und `--validate` läuft ohnehin → der Mehraufwand ist der **erzwungene Reihenfolge-Schritt**, kein neuer Kommando-Umfang |

**Warum deterministisch:** Der Sync-Pfad ist der einzige Ort, an dem der Index entsteht
(IC-09/IC-10, IC-13). Er ist idempotent (NFA-01: zwei Läufe ⇒ null Schreibvorgänge,
identischer Output) und diff-stabil (NFA-02, IC-14 Fact-Hash-Footer). Ein zweiter
Erzeugungsmechanismus (Hook) würde diese Eindeutigkeit verletzen.

## 4. Abgrenzung: `index-mode` ist **nicht** der Mechanismus dieser Entscheidung

**Ausdrückliche Festlegung, um eine Fehldeutung auszuschließen:**

- `docs-consolidation.index-mode` (IC-22; Werte `full` / `skeleton`) ist der
  **Rollback-Schalter für W7** — genauer: die Index-Strategie, nach der IC-13/IC-15 den
  Scaffold-Skeleton behandeln bzw. ersetzen. Er ist **kein** Regenerationsauslöser.
- `index-mode` gehört **nicht** in die Verifikationserwartung dieses Records und **nicht**
  als Mechanismus des gewählten Weges. Er darf in diesem Record ausschließlich als
  IC-22-Verweis genannt werden.
- Ebenso ist der Knowledge-Schalter `knowledge-engine.okf.index-mode` (IC-22; `llm` /
  `generated`) **Rollback für W7** (IC-19/IC-24) und hat mit der `docs/INDEX.md`-Regenerierung
  **nichts** zu tun.
- Der gewählte Weg dieser Entscheidung ist **ausschließlich** der Sync-/Validator-Lauf
  (Kapitel 3). Wer `index-mode` als „den Weg" liest, hat den Record missverstanden.

## 5. Verifikation

| Kommando | Sollwert | Bedeutung | Evidenzklasse |
|---|---|---|---|
| `grep -n 'pre-commit\|CONTRIBUTING' docs/plans/2026-09-25-docs-consolidation-oq8.md` | **0** bei **mindestens einem** Treffer | Belegt, dass die **Entscheidungsdokumentation** existiert | `nicht gemessen` (Ausführung steht aus) |

**Scharfung der Erwartung (aus der Plan-Task W0-6, Kapitel „Verifikation"):** Der Treffer
belegt **nicht** eine Hook-Implementierung. Er belegt, dass die beiden Alternativen als
**verworfen** benannt sind und der **Sync-/Validator-Lauf** als **gewählter** Weg dasteht —
genau das ist der Inhalt dieses Records (Kapitel 2.1, 2.2, 3). Ein Sollwert von `0` Treffern
wäre der **Fehlerfall**: dann wäre die Verwerfung nicht dokumentiert.

**Ausführungsstand:** Dieses Kommando wurde **bei der Erstellung dieses Records nicht
ausgeführt** — es greift definitionsgemäß erst **nach** dem Schreiben der Datei. Ein
gemessener Treffer-Zählwert wird hier **bewusst nicht** behauptet; die Ausführung und der
Messwert gehören in den Ausführungsbericht des aufrufenden Agenten. Aus demselben Grund
wird hier **kein** Messwert für `--validate`, `--check` oder die Szenarien 50/51/52/54/55/56
(AC-38) behauptet — diese Prüfungen gehören zu **W3-6**, nicht zu W0-6.

**Zusätzlich zu beachtende Abgrenzung der Erwartung:** `index-mode` (Kapitel 4) ist **nicht**
Gegenstand dieser Verifikation; ein Fund von `index-mode` in diesem Record ist zulässig und
wäre kein Befund.

## 6. Folgen für die betroffenen Stellen

| Stelle | Folge dieser Entscheidung |
|---|---|
| **W3-6** (Plan) — `docs/INDEX.md` tracked, Erstgenerierung, OQ6/OQ8-Umsetzung | **Umsetzungsschritt dieser Entscheidung.** Der Generator läuft **nach** dem Spec-Plan-Scaffold, und **diese Reihenfolge ist eine verbindliche Invariante**: der Scaffold schreibt das Skeleton, der Generator ersetzt es **einmalig** (Präfix-Erkennung, IC-13 Zeile 4). Ein Vorziehen des Generators vor den Scaffold würde den Skeleton-Zustand zerstören bzw. den Scaffold-Skeleton nicht ersetzen. In W3 entsteht **kein** Hook und **keine** neue Doku-Datei; der Workflow-Vertrag wird dort als expliziter Schritt festgehalten (Spec §10) |
| **W3-7** (Plan) — Marker-Regionen | **Kein Doku-Schritt für OQ8.** W3-7 braucht keine Hook-, keine CONTRIBUTING- und keine Index-Regenerations-Doku, weil der Sync-/Validator-Lauf der Auslöser ist. Der Vertrag lebt in diesem Record und in Spec §10. Der Hybrid-Scope für `llms.txt` (OQ2) bleibt davon unberührt |
| **IC-13** (Besitzregel) | Unverändert und weiterhin **verbindlich**: Der Generator besitzt `docs/INDEX.md` **nur**, wenn er sie selbst erzeugt hat (Ziel existierte nicht, oder Ziel ist das Scaffold-Skeleton). Er überschreibt nie eine Datei eines anderen legitimen Writers. Diese Regel ist der Grund, warum die Szenarien 52/54/55/56 ohne Änderung grün bleiben |
| **IC-22** (Rollback-/Gate-Config) | Unverändert: `enabled` (Default `false`, agent-meta explizit `true`), `index-mode`, `checks.strict`, `sources`, `volatile-facts` und der Knowledge-Schalter behalten ihre Werte. `index-mode` ist Rollback für W7 (Kapitel 4), nicht Teil dieses Vertrags |
| **AC-12** (V2) | Bleibt **ERROR**: getrackte `docs/**/*.md` außerhalb von `archive/`, die in `docs/INDEX.md` fehlen ⇒ mindestens ein `Finding(severity=ERROR)`. `docs/INDEX.md` selbst und `archive/`-Pfade erzeugen kein Finding. Die Entscheidung bestätigt den Schweregrad, statt ihn zu senken |
| **AC-38** (Regressionsgarantie) | Unverändert: die sechs Szenario-Fixtures 50/51/52/54/55/56 bleiben ohne jede Änderung grün. Tragend ist der **Absenz-Default** (`enabled` = `false` bei Abwesenheit) — der Generator schreibt dort weder `docs/INDEX.md` noch ein `docs/`-Verzeichnis. Kein Assert-Skript und keine Fixture-Config wird angefasst |
| **R20** (V2-ERROR vs. menschliche Doku-Erstellung) | **Bleibt als Risiko offen, aber mit benanntem Owner und Auslöser.** Nicht gelöst durch Abschwächen von V2, sondern durch den deterministischen Sync-/Validator-Lauf als Owner-Pfad. Die Spec-Empfehlung (Commit-Hook) ist **nicht** übernommen; es entsteht **kein** neuer Hook |
| **NFA-04** (Downstream-Kompatibilität) | Erfüllt, weil der Vertrag an die Fail-off-Absenz-Defaults gebunden bleibt: Generator und Checks V1–V9 sind in Consumer-Projekten ohne explizite Aktivierung vollständig inaktiv |
| **NFA-01 / NFA-09** (Idempotenz, beobachtbare Drift) | Erfüllt über den gewählten Weg: zwei Sync-Läufe ⇒ null Schreibvorgänge; Drift zwischen Doku-Baum und Index wird über V2 **beobachtbar** (ERROR), nicht über einen Nebenmechanismus |
| **NG-4** (kein neues CLI-Flag) | Eingehalten: kein neues `sync.py`-Flag, damit keine Pflegepflicht in `docs/api/cli-reference.md` entsteht |

## 7. Workflow-Vertrag

1. **Auslöser:** `sync.py` im Default-Sync schreibt `docs/INDEX.md`; `sync.py --validate`
   prüft den Zustand über V2.
2. **Owner:** Die Agenten-Pipeline (`orchestrator` im Entwicklungsfluss, `git` für den
   Commit), wie in Spec §12 R20 hinterlegt. Ein **neuer** Hook-Owner entsteht **nicht**.
3. **Reihenfolge:** Neue Doku-Datei anlegen → **Sync ausführen** → `--validate` grün → Commit.
4. **Konsequenz, ausdrücklich benannt:** Eine neue, getrackte Doku-Datei unter `docs/`
   löst ab W3 **V2 als ERROR** aus und damit einen **roten `--validate`**, bis ein Sync
   gelaufen ist. Das ist kein Defekt, sondern der gewählte Vertrag: **der Sync ist der
   verbindliche Regenerationsweg.** Wird er übersprungen, ist der Fehler sichtbar und der
   nächste Sync korrigiert den Zustand deterministisch (kein Handedit von `docs/INDEX.md`).
5. **Handedit-Schutz:** `docs/INDEX.md` ist 100 % generiert; ein Handedit ist ein Fehler
   (Generator-Modus, Spec §3.1; NFA-05).
6. **Unabhängigkeit von W0-7 (DEC-OQ1):** W0-7 (OQ1 — Wiki-Topics vs. `docs/guides/`) bleibt
   eine **eigenständige** Entscheidung mit eigenem Owner, eigenem Record und eigener
   Wellen-Blockade (W5). Die hier getroffene Entscheidung zu OQ8 hat **keinen** Einfluss auf
   OQ1, OQ2 oder OQ6 und umgekehrt: W0-7 wird **nicht** durch diesen Vertrag ersetzt und
   dieser Vertrag **nicht** durch W0-7. Beide Records sind unabhängig voneinander gültig.
7. **Kein Code-, kein Config-Effekt:** Dieser Record ist rein dokumentarisch. Ein Rollback
   besteht im Entfernen der Datei; bis dahin gilt der Vertrag in Kapitel 7.1–7.3.

## 8. Trace-Anker

```
plan-id: PLAN-DOCS-CONSOLIDATION-2026-09-25
→ Task W0-6 (REC-OQ8 — wer re-generiert docs/INDEX.md bei neuer Doku-Datei)
→ Record: docs/plans/2026-09-25-docs-consolidation-oq8.md
→ Normative Quelle (bleibt unverändert):
     docs/specs/2026-09-25-repository-documentation-consolidation.md
        §5.1  IC-05  (Checks V1–V9; V2 = docs_index_completeness)
        §5.2  IC-13  (Schreib-, Idempotenz-, dry_run-Vertrag + Besitzregel)
        §5.4  IC-22  (Rollback-/Gate-Config; index-mode = Rollback W7)
        §7    AC-12 (V2-ERROR), AC-38 (Regressionsgarantie Szenarien 50–56)
        §8    NFA-01, NFA-04, NFA-05, NFA-09
        §9    Trace-Matrix / Wellenfolge (W3)
        §10   Pipeline-Gate, Workflow-Vertrag-Klausel OQ8
        §11.2 OQ8 — GESCHLOSSEN 2026-09-26
        §12   R20 (V2-ERROR vs. menschliche Doku-Erstellung)
        §17.2 Review-Auflösung
     docs/specs/2026-09-25-repository-documentation-consolidation-design.md
        (verbindliche Design-Grundlage, read-only für diesen Record)
→ Plan-Stellen, die diesen Vertrag konsumieren:
     Plan-Kapitel „Wellen-Übersicht"            (W0-6 REC-OQ8)
     Plan-Kapitel „Reihenfolge-/Abhängigkeitsmatrix" (Task-Zeile W0-6)
     Plan-Task W3-6  (Umsetzungsschritt; Scaffold-vor-Generator = Invariante)
     Plan-Task W3-7  (kein Doku-Schritt für OQ8)
→ Verwandt:
     docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md  (W0-2, Contract-Liste)
     docs/plans/2026-09-25-docs-consolidation-track-a-gate.md  (W0-4, Gate)
     docs/api/cli-reference.md                                 (CLI-Flag-Dokumentation, NG-4)
     .meta-config/project.yaml                                  (Default-Sync, --validate)
→ Gegen geprüft von: documenter (W0-6-Ausführung); Commit über git-Agent
```

## 9. Offene Punkte dieses Records

1. **Kein offener Entscheidungsbedarf.** OQ8 ist entschieden; dieser Record enthält keine
   offene Frage, keinen Entscheidungsweg und keinen Platzhalter.
2. **Messwerte offen (keine Shell-Ausführung in diesem Task):** Der Grep aus Kapitel 5
   sowie alle W3-Prüfungen (`sync.py --check`, `git check-ignore`, Szenarien 50–56) sind
   **nicht** gemessen und werden **nicht** behauptet. Sie gehören in den Ausführungsbericht
   des aufrufenden Agenten bzw. zu W3-6.
3. **Übernahme des Vertrags in W3:** W3-6 referenziert diesen Record als Umsetzungsschritt
   (Kapitel 6). Ob und wann W3-6 ausgeführt wird, entscheidet der Plan-Ledger, nicht dieser
   Record.
4. **Abweichung von der Spec-Empfehlung ist dokumentiert, nicht bereinigt:** Die Spec
   empfahl in R20 einen Commit-Hook; der Nutzer hat den Sync-/Validator-Lauf entschieden
   (§11.2 OQ8). IC/AC bleiben unberührt — die Empfehlung wird nicht nachgezogen, weil ein
   Code- oder Akzeptanzvertrag nicht betroffen ist.
