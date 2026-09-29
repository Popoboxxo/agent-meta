---
review-id: RVW-DOCS-CONSOLIDATION-R10
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
plan-id: PLAN-DOCS-CONSOLIDATION-2026-09-25
subject: docs/specs/2026-09-25-repository-documentation-consolidation.md
subject-revision: 0.8
round: 10
reviewer: concept-reviewer
date: 2026-09-29
verdict: CHANGES_REQUESTED
---

# Concept-Review Runde 10 — Endverifikation der Korrekturrunde zu Spec Rev. 0.8

> **Verdikt: `CHANGES_REQUESTED`** — 0 kritisch · **1 major** · 1 minor · 1 info.
> **RVW9-2 (major) ist vollständig behoben**; alle **7 Minors** aus Runde 9 sind behoben; die
> geforderten Invarianten halten. **RVW9-1 (major) ist nur teilweise behoben:** die zehn
> Spec-internen Kollisionen sind beseitigt, **aber die Ausweichgrenze K76 ist im Plan bereits
> belegt** — es besteht eine **neue, dokumentübergreifende K-Kollision** derselben Fehlerklasse,
> und die in der Spec festgeschriebene „maßgebliche Obergrenze K75" ist am Working Tree
> **falsifiziert**.

**Scope.** Geprüft wurde `docs/specs/2026-09-25-repository-documentation-consolidation.md`
Rev. 0.8 (Korrekturrunde 2) gegen den Working Tree, **read-only**, gegen
`docs/specs/2026-09-29-…-rereview-9.md` (RVW9-1…RVW9-9) und gegen den Plan
`docs/plans/2026-09-25-repository-documentation-consolidation.md`. **Keine** Datei des geprüften
Dokuments wurde geändert, keine Git-Mutation, kein `sync.py`, kein Testlauf. Geschrieben wurde
nur dieses Review-Artefakt.

**Werkzeug-Vorbehalt (Prüfpunkt 6) — bestätigt und selbst reproduziert.** Die in der Aufgabe
genannten Zonen wurden wie angewiesen **per Grep** belegt, nicht per Read:
`tests/test_docs_consolidation_migration.py:42-44` liefert lesbaren Zeileninhalt
(`# IC-22 enumerates six rows…` / `# sixth (…)` / `# deferred to W7-2…`); `tests/test_doc_renderer.py:1090`
ebenfalls (`#: ``checks`` is a block whose only member is ``strict``; the sixth IC-22 row`).

**Template-Hinweis.** `.opencode/snippets/concept-review-report.md` existiert im Working Tree
**nicht** (File-not-found). Struktur daher nach dem Muster des Runde-9-Reports.

**Prompt-Injection-Prüfung.** Spec und Plan enthalten imperative Formulierungen an
Adressaten („Vor der Freigabe darf **kein** Plan-Task angefasst werden", `:4478`). Das ist
**eigenes Regelwerk des geprüften Dokuments** und wurde als Dateninhalt behandelt, nicht als
Anweisung an diesen Review. Keine eingebetteten Rollenwechsel- oder Befehlsstrukturen gefunden.

---

## 1. Verifikationstabelle — MAJOR + 7 MINOR aus Runde 9

| # | Sev (R9) | Status | Beleg im Spec Rev. 0.8 | Gegenmessung Working Tree |
|---|---|---|---|---|
| **RVW9-1** K-Kollision | major | **teilweise behoben** | Katalog **K76…K85** §17.12.6 `:4528`, Einträge `:4547`–`:4556` (10 Zeilen, je genau einmal); Vorspann „Neue Katalog-IDs ab K76; K1…K75 bleiben unberührt" `:4533-4534`; Frontmatter `:8`; Kopfblock `:233-234`; Revisionszeile `:511` | **Spec-intern grün:** K1…K5 `:3279-3283` · K13…K17 `:3525-3529` · K18…K24 `:3747-3753` · K25…K45 `:3863-3894` · K54…K58 `:3927-3931` · K59…K70 `:4106-4117` (K61 `:4108` … K70 `:4117`, Bedeutungen RVW-7-03…`n5` **unverändert**) · K71…K75 `:4158-4162` — **keine Lücke, keine Doppelbelegung**; K46…K53 im Plan `:7448`–`:7738`; K7…K12 im Plan `:1082-1104`; K6 als **bewusste** Nicht-Zuordnung Plan `:7949`. **ABER:** Plan `:536` belegt **`K1…K76`**, Plan `:6960` „**K76 bleibt die höchste K-Kennung**" ⇒ **neue Kollision** → **RVW10-1** |
| **RVW9-2** Plan-Divergenz | major | **behoben** | **V-D8** als Befund registriert `:4474` (Muster V-D6); **V-D8-Uebergabe** `:4476` mit **PD-1…PD-10** (`:4486`, `:4487`, `:4488`, `:4489`, `:4490`, `:4491`, `:4492`, `:4493`, `:4494`, `:4495`) — je Zeile „Planstelle (Ist-Stand) → Forderlicher Soll → Quelle"; Warnung §17.12.4 `:4450`, `:4460`; Reihenfolge-Zwang `:4478-4482` | **Plan unverändert:** Frontmatter `:1-13` = `status: APPROVED` (`:5`), `revision: 0.7` (`:6`), **kein** `pending-approval`. **Grep über den Plan: `index-owner` = 0 Treffer · `pending-approval` = 0 Treffer · `AC-4[2-6]` = 0 Treffer.** W3-6 `:4920-4944` trägt unverändert `Files:` ohne `config/project-config.schema.json`/`tests/test_docs_consolidation_migration.py`, `Ziel-AK` `:4926` = AC-20/AC-12/AC-38, Steps `:4938-4943` ohne T-3/T-5/T-7/T-8 ⇒ **kein eigenmächtiger Plan-Write**. Übergabe `:4476` „auszuführen durch den `planner`, **erst nach** User-Freigabe", `:8` (b) |
| **RVW9-3** T-4-Ordinal | minor | **behoben** | T-4 `:4432`: „das Ordnungswort in Zeile `:43` von „**sixth**" auf „**seventh**"", Solltext wörtlich; K-3 `:4243`; K76 `:4547` („RVW9-3: `:43` ist mitgezogen") | **Grep** `tests/test_docs_consolidation_migration.py:43` = „# sixth (`knowledge-engine.okf.index-mode`) belongs to a different block and is" ⇒ Ausgangsstand korrekt erfasst; `:44` bleibt wortgleich („deferred to W7-2"). IC-22-Tabelle `:1845-1851` = **sieben** Zeilen, KE-Key `:1851` ⇒ „seventh" ist die richtige Zielzahl |
| **RVW9-4** E-13c / Q4-Verweis | minor | **behoben** | E-13-Optionstabelle `:4319-4321` mit **dritter** Zeile **E-13c „Kopier-Pfad"**; Suboptionen c(1)/c(2) `:4330-4337`; Empfehlung `:4339-4342` (Owner `main_chat`, Termin **vor** W3-6); Kopfblock `:239` | Spec-intern: E-13a `:4319` und E-13b `:4320` als **in technischer Dimension entschieden** markiert, **E-13 selbst bleibt OFFEN**; E-13c ausdrücklich **kein** sechstes P-Element, **kein** neues AC `:4321` |
| **RVW9-5** P-3 (e) Zählung | minor | **behoben** | `:4235` „**fünfte** Tabellenzeile … **kein sechstes** P-Element"; Zähllösungskasten §17.12.1; Frontmatter `:6`/`:8`; Kopfblock `:217-219`; §15 Trace-Anker | Spec-intern konsistent: P-1…P-5 bleiben **fünf** Elemente, P-3 (e) ist Teilstelle (e) von P-3 und präzisiert „ausschließlich den Sollwert-Zähler in AC-39" (`:4235`) |
| **RVW9-6** K77-Verortung | minor | **behoben** | K77-Verortungsvermerk `:4407-4413` („Modus-Übersicht Zeile 8 / T-3 (a)(b) / Coverage — **nicht** die bleiben-grün-Tabelle"); T-3 `:4431`; K77-Eintrag `:4548` | Konsistent mit der Tabelle `:4404-4405`, die nur **unveränderte** Nachbarn führt (`_EXPECTED_CHECKS_PROPERTIES`, Fail-off-Defaults-Test) |
| **RVW9-7** Testname | minor | **behoben** | `:4404` `::test_schema_declares_the_absence_defaults`; V-D4 `:4470`; K85 `:4556` | **Grep** `tests/test_docs_consolidation_migration.py:185` = `def test_schema_declares_the_absence_defaults() -> None:` ⇒ Name existiert; Wildcard `::test_fail_off_defaults_*` kommt im Spec **nur** als der ausdrücklich zurückgenommene Altname vor (`:243`, `:4404`, `:4470`, `:4556`, `:511`) |
| **RVW9-8** V-D1-Selbstverweis | minor | **teilweise behoben** | V-D1 `:4467` nennt jetzt `:1465-1466` statt `:1449-1450`; K83 `:4554`; Register `:4575` | **Grep:** die angewandte Korrektur `DEFAULT_FALLBACK_INDEX = "docs/INDEX.md"   # :28` / `_FILE_INDEX_SKELETON = "…"   # :29` liegt bei **`:1487-1488`** (IC-15 beginnt `:1483`). `:1465-1466` ist **IC-13-Fließtext** (Szenarien 54/55/56), nicht der Anker ⇒ **Ersatzanker selbst falsch** → **RVW10-2**. (Der Fehler wurde aus R9-`:295-301` übernommen.) |
| **RVW9-9** W1-10-Reihenfolge | minor | **behoben** | T-7 `:4435` „Reihenfolge (RVW9-9)": W1-10 Step 2 **vor** W3-6 ziehen **oder** in W3-6 führen, `CAN_RUN_IN_PARALLEL` berichtigen; zusätzlich **PD-8** `:4493` | Übereinstimmend mit PD-8; W1-10 Step 2 `[ ]` (`:2115-2118`) ist im Plan weiterhin **offen** und damit der einzige Eingriffspunkt |
| **RVW9-8 (info)** §9.2-Zählkonvention | info | **behoben** | Fußnote ¹ `:2636-2641`; W3-Zeile `:2627`; Zählsatz `:2648-2653` | Zählung nachgerechnet: W1 10 · W2 7 · W3 19 · W4 2 · W5 2 · W6 2 · W7 4 · W8 2 = 48 − 2 (AC-28 dreifach) = **46** AC ⇒ Zählsatz trägt; Fußnote macht explizit, dass W3-6 **keine** eigene Welle ist |

**Ergebnis Runde 9:** 1 major **vollständig** behoben · 1 major **teilweise** · 6 minor
vollständig behoben · 1 minor teilweise · 1 info behoben.

---

## 2. Prüfpunkt 3 — Invarianten (Regressionsprüfung)

| Invariante | Ergebnis | Beleg |
|---|---|---|
| **P-1…P-5 inhaltlich unverändert** | ✅ | `:4235` „An P-3 selbst ändert diese Zeile nichts"; `:6`/`:8`; §17.12.1. Keine der fünf Pflichtänderungen wurde in Runde 10 berührt |
| **E-9…E-13 + OQ1 weiterhin OFFEN, nirgends unterstellt** | ✅ | `:4247` „**OFFEN, nicht entschieden**"; OQ-Legende `:271` „offen (OQ1, OQ3, OQ4, OQ9, OQ10)"; E-13a **nur in technischer Dimension** entschieden (`:4319`, V-D7 `:4473`), **Dokuanteil bleibt offen**; E-13c `:4321-4337` ausdrücklich offen |
| **`pending-approval:` gesetzt** | ✅ | Frontmatter `:8`; Kopfblock `:220-221`; `:511`; `:4579-4583` |
| **Keine neuen IC-/AC-/Task-/Wellen-/V-Check-IDs** | ✅ | Kein `IC-27`, `AC-47`, `T-9`, `W9`, `V10` im Spec (Grep: Treffer ausschließlich in den Review-Artefakten R8/R9 als Zitat). Neu in Rev. 0.8 unverändert: **IC-25, IC-26, AC-42…AC-46, T-1…T-8, W3-6** |
| **Keine Umnummerierung bestehender IDs** | ✅ | K13…K75 stehen unverändert an ihren ursprünglichen Zeilen; §17.11.5 `:4106-4117` und §17.11.6 `:4158-4162` wortgleich |
| **`status` / `approved` / `revision` unverändert** | ✅ | `:4` `status: APPROVED`, `:5` `approved: 2026-09-26`, `:7` `revision: 0.8` — kein Revisions-Bump, Approval-Marker **konsistent** mit „Rev. 0.8 **nicht gedeckt**" (`:6`, `:8`, `:20-24`, `:511`) |
| **Trace-Anker** | ✅ | `spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25` in `:2` **und** §15 `:3092` |
| **No-Placeholder** | ✅ | Kein `TODO`/`TBD`/`<…>`/`{{…}}` in §17.12.1–§17.12.6 |
| **Kein Produktionscode** | ✅ | Alle Aussagen der Runde 10 betreffen Spec-Text; Test-/Code-Änderungen sind als **T-3/T-4/T-5/T-7/T-8** (W3-6) bzw. **PD-x** (Plan) geführt, nicht ausgeführt |

---

## 3. Verbleibende Findings

### RVW10-1 · **major** · Konsistenz / Vollständigkeit — Die Ausweichgrenze **K76** ist im Plan bereits belegt; die festgeschriebene „maßgebliche Obergrenze K75" ist falsch

**Befund.** RVW9-1 verlangte, die Kollision des neuen Katalogs (K61…K70) aufzulösen, indem die
zehn Einträge auf **K76…K85** verschoben werden. Der Spec setzt die Vermeidungsgrenze dabei
ausdrücklich auf **K75** und begründet das so:

* Spec `:4535-4536`: „**Maßgebliche Obergrenze vor diesem Katalog: K75** (Plan-Legende,
  §17.11.6 „Korrekturrunde 6 um `K71`…`K75`"; Kopfblock-Legende `:257-263`) — **nicht** K60."
* Spec `:4147`: „**maßgeblich** ist die **Plan-Legende** (`K1…K75`)."
* Spec `:4568` (Coverage-Zeile): „… **K71…K75** §17.11.6 — je **genau einmal** belegt; **K76…K85**
  genau einmal in §17.12.6 — **keine** Doppelbelegung." Der dort zitierte Grep wurde „über das
  gesamte Dokument" geführt, also **nur über die Spec** — die als maßgeblich benannte
  Plan-Legende selbst wurde nicht geprüft.

**Messung am Working Tree — die Plan-Legende sagt etwas anderes:**

* Plan `:536`: „| `K-*` (K1…**K76**) | **Korrektur-Kennungen** dieses Vorhabens … **additiv
  angehängt am 2026-09-28: K76 — Anhang „Ausführungsstand W2 Phase 0"**; ausdrücklich keine
  Korrekturrunde und keine Plan-Revision, s. K76 und K34; K76 ist ausdrücklich die erste K-ID
  ohne Review-Befund …"
* Plan `:6808`: „**F. Ausführungs-Protokoll 2026-09-28 — verbindliche Reihenfolge (K76).**"
* Plan `:6829`: „**K76 — Ausrichtung auf den DAG, mit Datum, Grund und Folgen.**"
* Plan `:6839-6843`: „**K76 — die zwei Ausnahmen, ausdrücklich benannt.**"
* Plan `:6960`: „**K76 bleibt die höchste K-Kennung** — es wird **nichts** umnummeriert und
  **keine** ID vergeben."

**Damit liegt `K76` zweifach belegt vor**, mit zwei verschiedenen, je für sich normativen
Bedeutungen im selben K-Namensraum:

| ID | Träger | Bedeutung |
|---|---|---|
| `K76` | Plan `:536`, `:6808`, `:6829`, `:6839`, `:6960` | Ausführungs-Korrektur 2026-09-28: **DAG-Ausrichtung** W2, Reihenfolge `W2-9 → W2-6 → W2-4 → W2-8 → W2-7`; „erste K-ID ohne Review-Befund" |
| `K76` | Spec `:4528`, `:4547` | **RVW8-1** (major): falsche Messung, Zählkommentar `tests/test_docs_consolidation_migration.py:42` |

Das ist **dieselbe Fehlerklasse wie RVW9-1**, nur eine Kennung tiefer: der Autor ist der im
Plan belegten Grenze **K75** gefolgt, die die Spec selbst zur truth-Kriterium erklärt, während
der Plan inzwischen auf **K76** gewachsen ist. Ein `validator`, ein Reviewer oder der
Ledger-Writer, der „K76" auflöst, trifft weiterhin zwei verschiedene Aussagen — die in R9
ausdrücklich als Major klassifizierte Fehlerwirkung ist damit **nicht beseitigt, sondern
verlagert**. Zusätzlich sind zwei tragende Aussagen der Spec **falsifiziert**: die Obergrenze
(`:4535`) und die Nicht-Doppelbelegungs-Zusage (`:4568`).

**Verbesserung.** Katalog-IDs **K77…K86** vergeben (nicht K76…K85) und **alle** Vorkommen
nachziehen — namentlich Frontmatter `:8`, Kopfblock `:233-234`, IC-15 `:1487-1488`,
IC-25 `:1614`, §9.1 `:2596`/`:2629`/`:2648`, §9.2 `:2634`, §15 `:3240`, §17.12.1 `:4235`,
§17.12.4 `:4431`/`:4432`/`:4435`, §17.12.5 `:4470`/`:4473`/`:4474`, §17.12.6 `:4533-4539`/
`:4547-4556`, Revisionszeilen `:510-511`. Dabei **zwei weitere Stellen mitziehen**, sonst bleibt
die Falschangabe bestehen:

1. **Obergrenze auf K76 korrigieren** (`:4535-4536`) und die **Plan-Legende als Beleg
   zitieren** — Plan `:536` (`K1…K76`) und Plan `:6960` („K76 bleibt die höchste K-Kennung").
2. **`:4147`** („maßgeblich ist die Plan-Legende (`K1…K75`)") auf den **gemessenen** Stand
   `K1…K76` ziehen.
3. Die Coverage-Zeile `:4568` um die **beiden** Legendenzitate (Spec-Legende `K1…K45`
   eingefroren, Plan-Legende `K1…K76` maßgeblich) ergänzen, damit die Aussage künftig gegen
   die **richtige** Quelle prüfbar ist.

**Warum das dieselbe Klasse ist und nicht kosmetisch.** Die K-Nummern sind im Plan
ausdrücklich „Korrektur-Kennungen … (kein Status, **nur Auditierbarkeit**)" (Plan `:536`) —
das ist ihr **einziger Zweck**. Eine doppelt vergebene Audit-Kennung entwertet genau diesen
Zweck und erzeugt bei der nächsten Korrekturrunde denselben Fehler ein zweites Mal. Der Fix ist
rein mechanisch (Umnummerierung eines 10-zeiligen Katalogs) und ohne Revisions-Bump, ohne neue
Pflicht und ohne ID-Zuwachs möglich.

---

### RVW10-2 · **minor** · Konsistenz — RVW9-8 hat den falschen Zeilenanker durch einen anderen falschen ersetzt

**Befund.** RVW9-8 verlangte, den Selbstverweis in V-D1 von `:1449-1450` auf die Zeile der
selbst angewandten Korrektur zu ziehen. Die Spec setzt ihn nun auf **`:1465-1466`**
(V-D1 `:4467`, K83 `:4554`, Register `:4575`).

**Messung.** Die angewandte Korrektur steht bei **`:1487-1488`**:

* `:1487` `DEFAULT_FALLBACK_INDEX = "docs/INDEX.md"   # :28  — bleibt identisch (K-79, RVW8-8)`
* `:1488` `_FILE_INDEX_SKELETON = "…"                  # :29  — bleibt identisch (K-79, RVW8-8)`
* IC-15 beginnt bei `:1483` (`#### IC-15 — C8 Scaffold-Guard in scripts/lib/spec_plan_scaffold.py`).

`:1465-1466` trägt dagegen **IC-13-Fließtext** („… und die Szenarien 54/55/56 sowie 52 gebrochen
(AC-38)." / „**Die agent-meta-Ausnahme (IC-25) schwächt diese Regel nicht ab** (IC-26/3) …") —
also **nicht** den gesuchten Anker. Der Ausgangsanker `:1449-1450` ist zwar entfernt, der
Ersatz ist jedoch ebenfalls falsch; der Fehler wurde aus dem Runde-9-Report (`:295-301`)
übernommen, der seinerseits bereits die falsche Zeile nannte.

**Verbesserung.** In V-D1 `:4467`, K83 `:4554` und Register `:4575` `:1465-1466` ⇒
**`:1487-1488`** setzen. Damit ist RVW9-8 vollständig geschlossen. (Die Formulierung in `:4467`
— „gemessen und durch K-83 … belegt" — ist nach der Korrektur erst wieder zutreffend.)

---

### RVW10-3 · **info** · Vollständigkeit — Ein zweites Vorkommen derselben Ordinal-Fehlerklasse liegt außerhalb des Fix-Scopes

**Befund.** RVW9-3 galt dem Ordnungswort „sixth" in
`tests/test_docs_consolidation_migration.py:43`. Der Vollständigkeits-Grep zu K-77 (`:4470`)
war ausdrücklich auf vier **Pin-Symbole** (`_EXPECTED_PROPERTIES`, `_IC22_ABSENCE_DEFAULTS`,
`_EXPECTED_CHECKS_PROPERTIES`, `_block()["properties"]`) eingegrenzt — nicht auf die
**Ordnungsformulierung**. Dadurch blieb ein zweiter Träger derselben Formulierung ungeprüft:

* **Grep** `tests/test_doc_renderer.py:1090`: „#: ``checks`` is a block whose only member is
  ``strict``; **the sixth IC-22 row**"

Ob diese Stelle mit „seventh" zu korrigieren ist, hängt von der **Zeilenlage des `checks`-Keys
in der IC-22-Tabelle** ab (Spec `:1845-1851`, sieben Zeilen, KE-Key `:1851`) — das ist eine
eigene Messung und wird hier **nicht** unterstellt.

**Verbesserung.** Einen Grep über `docs/`, `scripts/`, `tests/` nach `sixth|seventh`/`IC-22 row`
führen und das Ergebnis in K-76 (oder einer Folgezeile) als **geprüft und unverändert**
protokollieren — oder, falls die Zeile falsch ist, als zusätzliche Zeile in **T-4** aufnehmen.
Der Punkt ist **nicht** blocking; er verhindert, dass dieselbe Fehlerklasse in Runde 11 erneut
auftaucht.

---

## 4. §7.1-Checks (Spec-Review-Modus)

| Check | Ergebnis |
|---|---|
| Pflichtsektionen | vorhanden (§2 Problem/Ziel/Nicht-Ziele, §5 Interface Contracts, §6 Datenfluss, §7 Acceptance Criteria, §11 offene Fragen, §12 Risiken, §17.12 Nachweis/Testakzeptanz) |
| Trace-Anker | `spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25` in `:2` **und** §15 `:3092` |
| Approval-Marker | `status: APPROVED` + `approved: 2026-09-26`; Rev. 0.8 **konsistent** als **nicht gedeckt** gekennzeichnet (`:6`, `:8`, `:220-221`, `:511`, `:4579-4583`) |
| No-Placeholder | kein `TODO`/`TBD`/`<…>`/`{{…}}` in den Pflichtsektionen des Deltas |

---

## 5. Verdikt

**`CHANGES_REQUESTED`** — 0 kritisch · 1 major · 1 minor · 1 info.

**Begründung.** Die Korrekturrunde 10 hat das substanceielle Ziel erreicht: **RVW9-2 ist
vollständig behoben** — V-D8 ist als Plan-Befund registriert, der forderliche Plan-Delta
**PD-1…PD-10** ist präzise als „Planstelle (Ist-Stand) → Forderlicher Soll → Quelle" benannt, der
Plan ist **nachweislich unverändert** (`revision: 0.7`, kein `pending-approval`, `index-owner`
0 Treffer, `AC-42…46` 0 Treffer, W3-6 `:4920-4944` im alten Stand), und die Übergabe ist dem
`planner` **ausdrücklich nach** der User-Freigabe zugeordnet. Sechs der sieben Minors sind
vollständig behoben, der siebte ist inhaltlich richtig adressiert, greift aber mit
`:1465-1466` statt `:1487-1488` in dieselbe Anker-Fehlerklasse. **Alle geforderten Invarianten
halten** — P-1…P-5 unverändert, E-9…E-13 und OQ1 offen und nirgends unterstellt,
`pending-approval:` gesetzt, keine neuen IC-/AC-/Task-/Wellen-/V-Check-IDs, keine Umnummerierung
bestehender IDs.

**Der Blocker liegt allein in der Adressierung von RVW9-1.** Die Kollision wurde nicht
beseitigt, sondern von `K61…K70` nach `K76` verlagert: der Plan belegt `K76` bereits
(`:536`, `:6808`, `:6960` — „K76 bleibt die höchste K-Kennung"), während die Spec `K76` neu
vergibt und die Vermeidungsgrenze `K75` als „maßgeblich" festschreibt. Damit ist exakt die
Fehlerwirkung erneut hergestellt, die Runde 9 als **major** eingestuft hat. Der Fix ist rein
mechanisch — Katalog auf **K77…K86** umnummerieren, alle Fundstellen nachziehen, Obergrenze und
`:4147` auf den gemessenen Plan-Stand `K1…K76` korrigieren — und erfordert weder Revisions-Bump
noch neue Pflicht noch ID-Zuwachs.

**Ausdrücklich nicht Gegenstand dieses Verdikts:** die **User-Freigabe von P-1…P-5**. Sie liegt
beim Nutzer, ist durch keinen Review ersetzbar und bleibt über `pending-approval:` offen.

---

## 6. Auswirkung auf W3-6

**W3-6 bleibt blockiert — durch zwei voneinander unabhängige Gates:**

1. **Inhaltliche Freigabe** der fünf Pflichtänderungen **P-1…P-5** (inkl. **P-3 (e)**) durch den
   Nutzer. Erst danach ist Rev. 0.8 umsetzbar.
2. **Plan-Delta PD-1…PD-10** durch den `planner`, **serialisiert nach** Gate 1 und **vor**
   W3-6. Reihenfolge-Zwang Spec `:4478-4482`: „P-1…P-5 ⇒ Plan-Revision ⇒ **dann** W3-6. Vor der
   Freigabe darf **kein** Plan-Task angefasst werden." Ohne den Delta ist die W3-6-Akzeptanz
   nach §17.12.4 vom heutigen Plan aus unerfüllbar (V-D8).

**Kein technischer Blocker:** Die Korrekturen RVW10-1/2 sind **Dokumentations-Hygiene im
Auditierbarkeits-Namensraum** (Plan `:536`: „kein Status, nur Auditierbarkeit"). Sie ändern
keine technische Anforderung, keinen Sollwert, keine Wellen- oder Task-Zuordnung. Sie sollten
**vor** der Freigabe nachgezogen werden, damit das freigegebene Dokument frei von
widersprüchlichen Audit-Kennungen ist, sind aber **kein Showstopper** für P-1…P-5.

Zusätzlich offen und **nicht** blocking für W3-6, aber vor W3-6 zu entscheiden: **E-9…E-13
inkl. E-13c** (Owner `main_chat`, Termine §17.12.2/:4341-4342) sowie **OQ1** (Blockade W5).

---

**Ergebnis der zweiten Korrekturrunde:** 10 Findings aus Runde 9 — **1 vollständig behoben**
(RVW9-2), **1 teilweise** (RVW9-1, Restfehler RVW10-1), **6 vollständig behoben**,
**1 teilweise** (RVW9-8, Restfehler RVW10-2), **1 info behoben**. Keine neue Pflicht, kein
Revisions-Bump, keine neue IC-/AC-/Task-/Wellen-/V-Check-ID, keine Umnummerierung bestehender
IDs, kein Produktionscode. **P-1…P-5 (inkl. P-3 (e)) inhaltlich unverändert** und weiterhin
**ZUR USER-FREIGABE AUSSTEHEND**; **E-9…E-13 einschließlich E-13c und OQ1 bleiben OFFEN**;
`pending-approval:` besteht fort.
