# Concept-Review — Ownership-Amendments, Plan `PLAN-DOCS-CONSOLIDATION-2026-09-25`

**Plan:** `docs/plans/2026-09-25-repository-documentation-consolidation.md` (`PLAN-DOCS-CONSOLIDATION-2026-09-25`)
**Gegenstand:** Anhang „2026-09-28 — Ausführungsstand W2 Phase 0 (W2-9, W2-6)" (Abschnitte A–J)
sowie die Legendenerweiterung `K-*` (`K1…K75` → `K1…K76`).
**Reviewer:** concept-reviewer · **Methode:** Read/Grep/Glob, read-only.

| Runde | Datum | Verdikt | Befunde |
|---|---|---|---|
| **1** | 2026-09-28 | `CHANGES_REQUESTED` | 3 major / 3 minor |
| **2** | 2026-09-28 | **`APPROVED`** | **0 major / 1 minor** (+3 info) |

---

## ⚠️ ERRATA — Korrektur an Runde 1 (durch den Autor gemeldet, bestätigt)

> **Diese Korrektur ist vor Runde 3 zu lesen. Runde-3-Reviewer dürfen auf die
> Zeilenanker der Runde 1 NICHT vertrauen, ohne sie gegen die `###`-Header neu zu prüfen.**

**Fehler in Runde 1, Finding m2:** Ich schrieb *„W2-4 `senior-developer` (`:2991`)"*.
**Richtig ist:** **W2-4** steht bei **`:2945`** (`**Agent:** senior-developer · **Depends on:**
W2-5 (Rev. 0.7; Rev. 0.6; vorher W2-3)`). **`:2991` ist die `Agent:`-Zeile von W2-5**
(`**Agent:** developer · **Depends on:** **W2-0** (Rev. 0.6; vorher W2-4)`).

**Beweis der Zuordnung** (`###`-Header des Plans, gemessen):
`### W2-4` `:2931` · `### W2-5` `:2982` · `### W2-6` `:3025` · `### W2-8` `:3150` ·
`### W2-7` `:3238`. Die `Agent:`-Zeile liegt **innerhalb** des jeweiligen Task-Blocks:
`:2945` ∈ (2931, 2982) ⇒ W2-4 · `:2991` ∈ (2982, 3025) ⇒ W2-5 · `:3059` ∈ (3025, 3150) ⇒ W2-6 ·
`:3165` ∈ (3150, 3238) ⇒ W2-8 · `:3273` ∈ (3238, …) ⇒ W2-7 · `:2829` ⇒ W2-9.

**Was die Korrektur inhaltlich ändert: nichts.** Die vom Anhang behauptete Owner-Zuordnung
(W2-9 `senior-developer`, W2-6 `developer`, W2-4 `senior-developer`, W2-8 `senior-developer`,
W2-7 `developer`) ist **vollständig korrekt**; mein Zeilenanker war falsch, nicht der Befund.
Meine übrigen Zeilenanker der Runde 1 (`:2829`, `:3059`, `:3165`, `:3273`, `:1371`, `:2513`,
`:2810`, `:2878`, `:4730`, `:355`, `:6672`, `:6767`, `:2137`) habe ich in Runde 2 **alle**
nachgemessen — sie sind korrekt.

**Ursache (methodisch, für künftige Runden):** Ich habe Task-IDs aus der Planreihenfolge
abgeleitet statt die `###`-Header zu prüfen. **Regel:** in diesem Plan **niemals** eine
Task-ID über eine Zeilenzahl bestimmen; `## File Structure` beginnt `:1256`, `Rollback W2`
`:2477`, `## Reihenfolge-/Abhängigkeitsmatrix` `:4618` — Positionsangaben zu *Nicht-Task*-Blöcken
stehen **außerhalb** jedes `###`-Task-Blocks. Der Anhang selbst wendet genau diese Regel an
(Owner-Spalte, „K12-Anker-Disziplin", Abschnitt B).

---

## Runde 2 — Prüfprotokoll

**Methode:** Read/Grep/Glob, read-only. Keine Datei geändert, kein Commit, keine Git-Mutation,
kein `sync.py`, kein `pytest`. Einzige Schreibausnahme: dieses Artifact.
**Kein Prompt-Injection-Verdacht** in den gelesenen Inhalten.

### Behobene Findings — Ergebnis

| ID | Runde-1-Befund | Status | Nachweis am Plan |
|---|---|---|---|
| **M1** | „drei" statt fünf Fundstellen für `spec_plan.py:570` | **BEHOBEN** | I(a) `:5805-5822`: Tabelle mit **8 Zeilen + Fehltreffer** = **5 Live** · **3 geschützt** · **1 Fehltreffer** = **9**. Unabhängig nachgezählt (Grep `:570` über den ganzen Plan): `355`(prot.) `1371` `2137`(FP) `2513` `2810` `2878` `4730` `6672`(prot.) `6767`(prot.) = **exakt 9**, Verteilung **5/3/1** ✓. `File Structure` + `Rollback W2` namentlich ergänzt ✓. „Nach der Korrektur: **2** Live-Stellen (Nr. 4, 5) offen, **3** behoben" ✓ |
| **M2** | Ist/Soll bei `check_readme_docs_index` vertauscht | **BEHOBEN** | I(b) `:5824-5840`: **Ist** = Working Tree `:167-198` (`:122-140`, `:143-164`, `:183`, `:168-177`), ausdrücklich „**Diese Werte beschreiben den Zwischenstand vor dem E-5-Rework** … werden **nicht** zu Sollwerten erklärt" ✓. Plan-Anker `:121-…` = **K48-Wert**, „**bereits heute** verrutscht", „**Vor-Implementierungs-Anker**, kein Sollwert" ✓. **Soll: „nicht vorab bestimmbar"**, „**Es wird deshalb ausdrücklich kein Soll-Anker gesetzt**", Korrektur = **neu messen beim Commit von W2-6** ✓ |
| **M3** | Delegation stützte sich auf K48 in umgekehrter Bedeutung; kein Owner/Frist | **BEHOBEN** | I(d) `:5847-5869`: **„K48 … war in umgekehrter Richtung falsch … K48 wird hier nicht mehr als Delegationsbegründung angeführt"** ✓. Ersatzmechanismus **K71-Lesart-Regel** benannt ✓. **Owner `senior-developer`** (Agent des Tasks W2-9, selbst gemessen) **+ Frist „mit dem Commit von W2-9"** (Schritt 4) **+ exakter, wortwörtlicher Änderungsauftrag** (je ein Lesart-Satz in `Interfaces` und `Schritt 2`, sonst nichts) ✓. Begründung, warum Tasktext *nicht* selbst korrigiert wird: K36/K42-Wortlautgrenze ✓ |
| **m1** | K76-Legende ohne Ausnahme-Vermerk | **BEHOBEN** | `:536`: „K76 ist ausdrücklich die **erste K-ID ohne Review-Befund** und die **erste Änderung einer Zeile im Rev.-0.7-Kopfblock** — beide Ausnahmen sind **je einmalig**"; **zweiseitig** registriert: zusätzlich F `:5753-5759` ✓ |
| **m2** | Kein Owner je Task | **BEHOBEN** | B `:5641-5647`: Spalte „Ausführender (`Agent:`, **selbst gemessen**)" für alle 5 Tasks + K12-Disziplinnotiz `:5657-5663`. Alle 5 Werte **gegen die `Agent:`-Zeilen geprüft — korrekt** (siehe Errata) ✓ |
| **m3** | Kopfnotiz vs. Legendenedit | **BEHOBEN** | `:5598-5608`: „**Zwei ausdrücklich benannte Ausnahmen, beide rein additiv und beide nachprüfbar**" — (1) Legendenzeile, (2) die drei Ankerstellen; **zusätzlich** in I(c) `:5844-5845` re-statiert ✓ |
| — | Abschnitt G mitkorrigiert | **BEHOBEN** | `:5774-5778`: Matrix-Zelle „**inzwischen an Ort und Stelle korrigiert**", „Matrix bleibt **10** Spalten breit", „Zählstand **9 / 5 / 7 / 23** unverändert" — **Raster 10 Spalten** (Datei + 9 Tasks) am Plan bestätigt ✓ |

### Findings Runde 2

#### MINOR

**m4 — I(b) benennt nur *eine* Fundstelle des veralteten `check_readme_docs_index`-Ankers.**
**Anker:** `:5829-5831`.

**Befund:** „`docs_links.py:121-…` (**Task W2-7**) stammt aus der **K48**-Tabelle und ist …
**schon jetzt** verrutscht." Der Plan trägt denselben Anker-Klassentyp aber an **weiteren** Stellen:

| Plan | Task/Block | Anchor | Status ggü. Working Tree |
|---|---|---|---|
| `:2758` | **W2-0** | `check_readme_docs_index \`:121-…\`` | ebenfalls verrutscht — **nicht genannt** |
| `:2745` | **W2-0** | `check_readme_docs_index \`:102-124\`` | ebenfalls verrutscht — **nicht genannt** |
| `:3126` | W2-6 | `check_readme_docs_index \`:100\`` | vom Anhang in I(b) ausdrücklich als **Ist** eingeordnet ✓ |
| `:3281` | W2-7 | `check_readme_docs_index` + Folgeanker | genannt ✓ |
| `:6229` | K48-Tabelle | `docs_links.py:121-…` | **wortgleich geschützt** ✓ (nicht genannt, korrekt) |

**Bewertung: nicht blockierend.** Es bleibt **kein** unerledigter Arbeitspunkt: der einzige
delegierte Auftrag („neu messen beim Commit von W2-6", Owner `developer`) deckt W2-7 ab, und
**W2-0 ist committet** (`b5bb0fe9`) — seine Anker waren zum Commitzeitpunkt korrekt und sind
nach dem Muster K48 als historischer Stand zu belassen. Es fehlt also nur die **Begründung des
Ausschlusses**, nicht die Behandlung.

**Geforderte Änderung:** ein Halbsatz in I(b): *„W2-0 trägt dieselben Anker (`:102-124`, `:121-…`);
sie sind zum Commitzeitpunkt (`b5bb0fe9`) korrekt und bleiben als historischer Stand stehen."*

### INFO (keine Änderung gefordert)

- **Zählung:** erneut nachgezählt — **59** × `- [x] `, **148** × `- [ ] `
  (35×`1:` + 36×`2:` + 35×`3:` + 42×`4–9:`), **Summe 207** ✓ unverändert. **Keine** Zeile im
  Anhang (`:5590-5885`) beginnt mit `- [ ]`/`- [x]`; alle Treffer liegen unter `plan:4614`.
- **Selbst gemessene Code-Anker unverändert korrekt:** `plan_identity.py:18/26/35/47/83` ·
  `spec_plan.py:55/68/581` · `docs_links.py:122/140/143/158/167/172-177/183`, 404 Z. **Keine
  erfundenen Anker.** Nur die Anhang-internen Zeilenangaben (Abschnitts-/Tabellenanker) sind
  Planzeilen und unterliegen K12.
- **Asymmetrie in I(a) vs. I(b) (zulässig, aber nicht ausgesprochen):** I(a) friert die
  Working-Tree-Werte `:68`/`:581` als Erwartung für den **Commit von W2-9** ein, I(b) setzt für
  den **Commit von W2-6** bewusst **keinen** Wert. Das ist **inhaltlich berechtigt** — W2-9 ist
  implementiert und sein Write-Set steht, W2-6s Rework ersetzt den Funktionsrumpf — sollte aber
  als Grund genannt werden, damit die Differenz nicht als Ungleichbehandlung lesbar ist.
- **I(a) Zeile 3, Formulierung:** die Spalte „Behandlung" liest sich wie eine Ersetzung
  („`:570` → nach W2-9 `:68`"); die tatsächliche Korrektur an `:4730` ist **additiv** (`:570`
  bleibt sichtbar, `:68` tritt hinzu) — wie in der Kopfnotiz korrekt beschrieben. Kein Widerspruch.
- **Fehltreffer-Klassifikation `plan:570` (`:2137`, Task W1-10):** die Einstufung als
  *Planzeilen-Verweis statt `spec_plan.py`-Anker* ist **richtig**; der Parenthese
  „(auf den OQ2-Record)" ist gegen die heutige Zeilenzählung **nicht** nachprüfbar und für die
  Klassifikation **nicht erforderlich**.

### Unverändert bestätigte Prüfpunkte (Runde 2)

| Prüfpunkt | Ergebnis |
|---|---|
| **Reihenfolge W2-9 → W2-6 → W2-4 → W2-8 → W2-7** | **BESTÄTIGT, widerspruchsfrei.** W2-7 `Depends on: W2-3, W2-4, W2-5, W2-6, W2-8` (`:3273`); Kante 17 = „W2-8 ist der **letzte** Task vor W2-7" (`:4844`); Kante 18 (`:4845`, `:6761`); W2-8-Header (`:3165-3167`); K63 „Common-Gate entsteht **erst in W2-7**" (`:368`); Zyklenprüfung `:4852`/`:6767`. Die vier Belege in F (`:5727-5738`) tragen **alle**. |
| **K76-Vergabe** | **BESTÄTIGT.** Additiv, nächste freie ID, keine Umnummerierung; Präzedenz: beide Vorgänger-Anhänge sind K-verknüpft (`K53-Interim-Ledger`, `:5418`; Rev.-0.7-Anhang K54–K58). **I(e)** (`:5871-5878`) verzichtet bewusst auf eine neue K-ID für die M1–M3/m1–m3-Nachbesserungen und **begründet** das (kein Korrekturgrund im Plan, sondern in einem eigenen Anhang) — nachvollziehbar und ausdrücklich anfechtbar. |
| **Widerspruch zu `APPROVED` / `revision: 0.7` / K34 / K53 / K20 / K46** | **KEIN WIDERSPRUCH.** K34-Addendum trägt; K53-Folgerung („gilt bis einschließlich W2-9, entfällt erst mit dessen Commit", `:5679-5685`) deckungsgleich mit `:2868-2870`; K20/K46-Matrix (10 Spalten, W2-7 `owns` = 5) unverändert. |
| **Vollständigkeit** | **BESTÄTIGT.** Alle 5 offenen W2-Tasks mit Zähler, Owner und Datei-Ankern; Fundstellen-Erhebung vollständig (5/3/1). |

---

## Runde 1 — Originalbefunde (inhaltlich gültig, Zeilenanker durch Errata oben relativiert)

| ID | Schwere | Befund | Status |
|---|---|---|---|
| **M1** | major | Fundstellen für `spec_plan.py:570` unvollständig („drei" statt fünf); `File Structure` + `Rollback W2` nicht genannt | **behoben** |
| **M2** | major | `docs_links.py:167` als Soll- statt Ist-Zustand geführt; Anker `:121-…` als erst „nach W2-6" veraltet bezeichnet | **behoben** |
| **M3** | major | Delegation der Anker-Korrektur mit „Muster K48" begründet — K48 ist eine **In-place**-Regel (`:6124-6152`); Präzedenz K72 korrigiert an **allen** Fundstellen und wurde einmal **erneut falsch** gemessen (R3-1); Delegation ohne Owner/Frist, obwohl K48s eigener Deferral-Weg (R3-B-3) Owner + Frist verlangt | **behoben** |
| **m1** | minor | K76-Legende ohne Vermerk der Ausnahmen | **behoben** |
| **m2** | minor | Kein Owner/Agent je Task — ⚠️ **Zeilenanker `:2991` in diesem Befund war falsch, siehe Errata** | **behoben** |
| **m3** | minor | Kopfnotiz „keine Zeile umformuliert" vs. Edit der Legendenzeile | **behoben** |

**Runde-1-Methodik (Fehlerquelle, für Runde 3 relevant):** Zeilenanker zu Nicht-Task-Blöcken
(`:1371`, `:2513`, `:4730`) wurden über den Fließtext statt über die umgebenden `##`-/`###`-Header
bestimmt; Task-Anker über die Planreihenfolge statt über `###`-Header. Beides in Runde 2
korrigiert und oben belegt. **Runde 3: Task-/Block-IDs nur über `###`/`##`-Header bestimmen.**

---

## Verdict Runde 2

**`APPROVED`**

**Begründung:** Alle drei major-Befunde der Runde 1 sind behoben — und zwar **nicht** durch
Übernahme meiner Belegliste, sondern durch eine **eigenständige Neuerhebung**, die ich
unabhängig nachgezählt habe und die exakt aufgeht (5 Live / 3 geschützt / 1 Fehltreffer = 9;
Zählung 59/148/207 unverändert; kein erfundener Anker). M3 ist nicht bloß umformuliert,
sondern **sachlich umentschieden**: K48 wird ausdrücklich als falsche Begründung **zurückgezogen**
und durch den im Plan bereits etablierten Mechanismus (K71-Lesart-Regel) mit Owner, Frist und
wortwörtlichem Änderungsauftrag ersetzt. I(b) trennt Ist und Soll jetzt sauber und setzt
bewusst **keinen** Soll-Anker. Es bleibt **ein minor** (m4, reine Begründungslücke ohne
Arbeitsrest) und drei info-Punkte. Kein Befund verletzt `status: APPROVED`, `revision: 0.7`,
K34, K53, K20, K46 oder die Zählkonsistenz; keine ID, kein Sollwert, kein Akzeptanzkriterium
und keine Checkbox wurden berührt.

**Fortsetzung:** `Route: quality_pipelines.concept-driven-dev` — kein `requirements`-Handoff
(reifes Plan-Dokument). Ausführung in der Reihenfolge F; die zwei offenen Live-Stellen
(Nr. 4/5) sind der Auftrag `senior-developer` mit Frist „mit dem Commit von W2-9".
