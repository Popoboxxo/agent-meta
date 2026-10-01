---
plan-id: PLAN-DOCS-CONSOLIDATION-2026-09-25-PAUSE
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
title: PAUSE-Record — Repository-weite Doku-Konsolidierung agent-meta (Cut vor dem Index-Exception-Punkt)
status: PAUSED
revision: 0.1
date: 2026-09-26
related:
  - docs/specs/2026-09-25-repository-documentation-consolidation.md
  - docs/plans/2026-09-25-repository-documentation-consolidation.md
  - docs/plans/2026-09-25-repository-documentation-consolidation-pause.md
---

# PAUSE-Record — Repository-weite Doku-Konsolidierung agent-meta

> **Additiver Status-Record. Kein Bestandteil der Spec-Revision, keine Plan-Revision, keine
> Korrekturrunde, keine neue K-Kennung, keine umnummerierte ID, kein Eingriff in eine als
> wortgleich festgeschriebene Stelle.** Dieser Record setzt **keine** Task-Checkbox, erteilt
> **keinen** Implementierungsauftrag und erzeugt **keinen** Produktionscode. Er **ersetzt
> keinen** Sollwert, **entscheidet keine** offene Vorlage und **hebt keine** bestehende
> User-Freigabe auf.

**Lesehinweis zu den Zeilenangaben.** Alle Belege in diesem Record sind **nach** den drei
Pause-Änderungen (Spec, Plan, dieser Record) **neu gemessen**. Die Zeilennummern der Spec und
des Plans haben sich dadurch gegenüber dem Stand vor der Pause **verschoben**; die in anderen
Dokumenten zitierten Vor-Pause-Zeilen bleiben dort **unverändert** stehen. Diese Drift ist in
**Abschnitt 4.7** als benannte Abweichung festgehalten und **nicht** stillschweigend geändert.

---

## 1. Status

**`PAUSED` — CUT vor dem Index-Exception-Punkt.** Datum des Pause-Beschlusses: **2026-09-26**.
Der Vorhaben-Stand wird damit vor dem Punkt **W3-6** (`docs/INDEX.md` tracked, Erstgenerierung,
OQ6/OQ8-Umsetzung) angehalten, also **vor** dem Punkt, an dem die agent-meta-Ausnahme im
KE-Vorrang-Gate wirksam würde.

**Redaktions- und Commit-Datum: 2026-09-29.** Die beiden Daten sind **nicht** dasselbe und
werden hier bewusst getrennt geführt:

| Datum | Bedeutung |
|---|---|
| **2026-09-26** | Datum des Pause-Beschlusses (vom Auftraggeber so vorgegeben) und zugleich Datum der historischen User-Freigabe des Umfangs W0–W8 (Spec `:5`). |
| **2026-09-29** | Redaktions- und Commit-Datum dieses Records. |

**Hinweis zur Nachvollziehbarkeit:** der letzte Commit, dessen Subject für dieses Vorhaben
belegt ist, ist **`534f95ac` („test: cover one-time docs index skeleton replacement") vom
2026-09-28** — Übergabe des `git`-Agenten, in diesem Durchgang **nicht** per Git-Kommando
nachgelesen. Zwischen dem Pause-Datum (2026-09-26) und dem Commit-Datum (2026-09-29) liegen
also **drei Tage**, in denen Spec-Rev. 0.8 und die Korrekturrunden 8, 9 und 10 entstanden sind
(Spec `:8`, `:532-534`).

---

## 2. Erreichter Stand

### 2.1 Pull Requests

| PR | Stand | Beleg / Anmerkung |
|---|---|---|
| **#833** | **gemergt** (Squash **`3c46920a`**, 2026-09-26) | Übergabe des `git`-Agenten. |
| **#837** | **ersetzt** durch **#839** | Übergabe des `git`-Agenten. Nicht mehr relevant; ein Diff zu #837 ist **nicht darstellbar** und wird hier **nicht** rekonstruiert. |
| **#839** | **OPEN / DRAFT**, Base `main` | <https://github.com/Popoboxxo/agent-meta/pull/839> — Übergabe des `git`-Agenten. |

**Branch / HEAD:** `feat/repository-documentation-consolidation-main`, HEAD-Kurz-SHA
**`534f95ac`**, Subject „test: cover one-time docs index skeleton replacement"; upstream
**ahead 6 / behind 0**. Übergabe des `git`-Agenten, in diesem Durchgang nicht per
Git-Kommando nachgelesen.

### 2.2 Wellenstand — mit benannter Abweichung

Die Auftragsvorgabe nennt **W0, W1, W2 als abgeschlossen**. Der Working Tree des Plans trägt
dazu **eine Abweichung**, die hier **nicht** geglättet, sondern mit beiden Quellen stehen bleibt:

| Welle | Aussage der Auftragsvorgabe | Beleg im Plan | Status dieses Records |
|---|---|---|---|
| **W2** | abgeschlossen | **Gate-Votum `WAVE_COMPLETE_WITH_OPEN_ITEMS`**, Anhang „Abschluss der Welle W2", Plan `:7083` / `:7120`; **43** von **43** Checkboxen über **10** Tasks, Plan `:7113` | **abgeschlossen mit offenen Punkten** — die offenen Punkte stehen in Abschnitt 4 dieses Records. |
| **W1** | abgeschlossen | **W1-5 Schritt 4 offen** (Plan `:2026`; LEDGER-Stand 2026-09-26 „W1-5 TEILWEISE erledigt … Offen ist ausschließlich Step 4 (Commit)", Plan `:2028`); **W1-10 Schritt 2 und Schritt 4 offen** (Plan `:2141`, `:2146`; LEDGER-Stand 2026-09-26 „W1-10 TEILWEISE erledigt", Plan `:2148`) | **nicht** vollständig abgeschlossen — **zwei** Tasks mit offenen Schritten. Ein Wellen-Gate-Votum für W1 ist im Plan **nicht** belegt. |
| **W0** | abgeschlossen | **alle** Checkboxen von W0-1…W0-7 sind offen (Plan `:1684-1897`); die Ergebnis-Records existieren als eigene Dateien (u. a. `docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md` mit Feld `status` = done, `:5`) | **nicht** abgehakt. Die inhaltlichen Ergebnis-Records sind geliefert, das Plan-Ledger ist es nicht. |

**Was daraus folgt:** belastbar abgeschlossen ist **W2**. Für **W0** und **W1** wird der
Widerspruch zwischen Auftragsvorgabe und Plan-Ledger **hier festgehalten** und **nicht**
zugunsten einer Seite aufgelöst. Er ist ein eigener Klärungspunkt für den Resume (siehe
Abschnitt 5, Schritt 0).

**W3–W8 sind nicht begonnen.** Beleg: **W3-6** trägt vier offene Schritte (Plan `:4982-4987`),
**W4-3** fünf (Plan `:5154-5166`); die Task-Belegungstabelle des Plans führt W3-6 mit
`senior-developer` (Plan `:5766`) und W4-3 mit `tester` (Plan `:5770`).

### 2.3 Teststände — mit Belegstatus

| Wert | Belegstatus |
|---|---|
| **3421** | **Übergabewert.** Laut `git`-Agent steht diese Zahl **ausschließlich in der Commit-Message von `c5495a00`** (2026-09-28, W2-7; der Plan führt denselben Hash in der Zählstand-Tabelle, `:7109`). Ein **Grep über den gesamten Datei-Baum liefert 0 Treffer** für `3421`. Die Commit-Message selbst war in diesem Durchgang **nicht** lesbar (kein Git-Kommando verfügbar) — der Wert wird deshalb als Übergabe, **nicht** als gemessene Zahl geführt. |
| **3479** | **nirgends belegt.** Weder im Datei-Baum (Grep ⇒ **0** Treffer) noch in den letzten **30** Commits (Übergabe des `git`-Agenten). **Nicht** verwendet. |
| **3420** *(im Plan gemessen)* | Der **einzige** im Plan selbst belegte Wert der jüngeren Volltestläufe: `python3 -m pytest tests/ -q` ⇒ **`3420 passed, 1 skipped, 35 errors`**, **0 failed** (Plan `:4386-4388`, W2-7-Verifikation). Ältere Läufe: **`3416 passed`** (Plan `:3881-3882`), **`3414 passed`** mit `2 failed` (Plan `:3822`), **`3390 passed`** mit `2 failed` (Plan `:2998-2999`). |
| **`236 passed`** *(fokussiert)* | Die **sechs** Verifikations-Testdateien zusammen (Plan `:4381-4384`); Baseline davor **`232 passed`**, nach Registrierung vor Pin-Übernahme **`2 failed, 234 passed`** (Plan `:4385-4386`). |

**Benannte Abweichung:** die Auftragsvorgabe nennt **3421**, der Plan misst **3420** für
denselben Gegenstand (Volltest nach W2-7). Die Differenz von **einem** Test wird **nicht**
geglättet und **nicht** erklärt; sie ist als offene Frage an den Resume übergeben.

---

## 3. Ausdrücklich NICHT freigegeben

Dieser Abschnitt ist der Kern des Records. Er ist eine **Freigabe-Sperre**, keine
Aufgabenliste.

### 3.1 P-1 … P-5 (inkl. P-3 (e) / „P-3-E")

Volltext in **Spec §17.12.1** (Spec `:4256`; P-Tabelle `:4266-4274`). Verdictschnitt im
Systemdesign **Kap. 6.1** (Design `:677-690`).

> **Wortlaut: keine Implementierungsfreigabe.** Diese fünf Punkte sind **normative**
> Änderungen an einer `APPROVED`-Spec (IC-Vertrag, Config-Tabelle, Akzeptanzkriterium,
> Risikotabelle). Sie sind **keine** Korrekturen versehentlicher Fehler und **keine**
> Korrekturrunden-Korrekturen. **Keiner** von ihnen ist freigegeben, **keiner** wird
> unterstellt, **keiner** darf als erledigt gelesen werden. Sie begründen den **neuen,
> nicht freigegebenen** Umfang `docs-consolidation.index-owner` (IC-25, IC-26, AC-42…AC-46;
> Spec §17.12.3, `:4402-4409`).

| ID | Kurzbezeichnung | Quelle (Datei:Zeile) | Owner | Termin/Blocker |
|---|---|---|---|---|
| **P-1** | IC-13-Tabellenzeile wird **bedingt**; zwei Zeilen kommen hinzu (Override ⇒ schreiben; unbekannter Wert ⇒ fail-closed) | Spec `:4269`; Design `:681` | `main_chat` (Nutzer) | **vor** der Umsetzung von **W3-6** (Spec `:4257`, `:4377-4379`) |
| **P-2** | IC-15 erhält die **zweite Schreibbedingung** „Ziel existiert nicht ⇒ Voll-Index anlegen", unabhängig von `resolve_index_mode()` | Spec `:4270`; Design `:682` | `main_chat` (Nutzer) | **vor** **W3-6** |
| **P-3** | IC-22-Config-Tabelle: **siebte** Zeile `docs-consolidation.index-owner`; der Absatz „für alle **sechs** Keys" wird zu „**sieben**" | Spec `:4271`; Design `:683` | `main_chat` (Nutzer) | **vor** **W3-6** |
| **P-3 (e)** *(= „P-3-E", Teilstelle (e) von P-3, **kein sechstes** P-Element)* | AC-39 wird von „**genau** den **sechs** Properties" auf den **gemessenen** Stand umgestellt: Block = **sechs** Properties **nach** Rev. 0.8, **fünf** davor. **An P-3 selbst ändert diese Zeile nichts.** | Zählauflösung Spec `:4258-4265`; Tabellenzeile Spec `:4272`; Modus-Übersicht Zeile 8 Spec `:4424`; Design führt P-3 **ohne** (e) (Design `:683`) | `main_chat` (Nutzer) | **vor** **W3-6** |
| **P-4** | AC-21s zweiter Given/When/Then-Block wird **bedingt** formuliert („`index-owner` nicht gesetzt"); **AC-42…AC-46** kommen hinzu | Spec `:4273`; Design `:684` | `main_chat` (Nutzer) | **vor** **W3-6** |
| **P-5** | R7s Mitigation-Tabelle erhält einen **dritten** Hebel (`index-owner`) plus den Nachweis, dass das Risiko in agent-meta **sinkt** | Spec `:4274`; Design `:685` | `main_chat` (Nutzer) | **vor** **W3-6** |

**Nicht** freigegeben heißt hier ausdrücklich auch: **keine** der neu eingeführten
Akzeptanzkriterien **AC-42…AC-46** und **keine** der neuen Interface-Verträge **IC-25** /
**IC-26** ist umsetzbar, und **kein** Produktionscode, **keine** Config-Zeile und **kein**
Test wurde und wird auf dieser Grundlage geändert.

### 3.2 E-9 … E-13 (einschließlich **E-13c**)

Volltext in **Spec §17.12.2** (Spec `:4284-4400`), Quelle der Vorlagen im Systemdesign
**Kap. 5** (Design `:593-671`). **E-13c** ist eine **Suboption von E-13**, keine neue
E-Reihe (Spec `:4289-4292`).

| ID | Kurzbezeichnung | Quelle (Datei:Zeile) | Owner | Termin/Blocker |
|---|---|---|---|---|
| **E-9** | Wert des Keys: **zweiwertiges Enum** oder **boolescher** Override. Optionen **E-9a** (Empfehlung, Enum `["auto", "docs-consolidation"]`), **E-9b** (Boolean), **E-9c** (**verworfen**, DECISION-2) | Spec `:4294-4305`; Design `:600-609` | `main_chat` (Nutzer) | **vor** **W3-6** |
| **E-10** | Reichweite: **nur** `docs/INDEX.md` oder auch die W3-7-Marker-Regionen. Optionen **E-10a** (Empfehlung), **E-10b** | Spec `:4307-4323`; Design `:611` | `main_chat` (Nutzer) | **vor** **W3-6** |
| **E-11** | Reicht der Key für `docs/architecture/INDEX.md` (**W4-3**)? Optionen **E-11a** (Empfehlung: nichts ändern, in W4-3 **verifizieren**), **E-11b** (vorab Scope-Erweiterung) | Spec `:4325-4338`; Design `:629` | `main_chat` (Nutzer) | **vor** **W3-6** |
| **E-12** | Reicht eine **Docstring-Korrektur**, oder **zwei Fixtures** im AC-20-Test? Optionen **E-12a** (Empfehlung), **E-12b**, **E-12c** (Zusatztest an der verdrahteten Stage) | Spec `:4340-4350`; Design `:643` | `main_chat` (Nutzer) | **vor** **W3-6** |
| **E-13** | Dokumentationspflicht: wer trägt Schema-/Beispiel-Eintrag? **E-13a in seiner ursprünglichen Form zurückgenommen** (K-81, Spec `:4356`), **korrigierte Fassung**: T-3/T-5/T-8 liegen **alle in W3-6**; offen bleibt die Zuordnung des **Dokuanteils** (optional W8-4). **E-13b**: alles in W3-6 | Spec `:4352-4362`; Design `:654-662` | `main_chat` (Nutzer) | **vor** **W3-6** |
| **E-13c** — **Kopier-Pfad** | **Wer dokumentiert die kopierte Deklaration** `index-owner: docs-consolidation` in einem KE-Projekt (`knowledge-engine.enabled: true`), und wird dafür eine `validate`/`--strict`-**Meldung** gefordert? **Zwei Entscheidungspunkte:** **c(1)** Doku-Pflichtträger — **c(1)-a** (Empfehlung: Pflicht im IC-25-Dokuabschnitt dieser Spec), **c(1)-b** (README-Abschnitt), **c(1)-c** (keine Pflicht; **nicht** empfohlen); **c(2)** `validate`/`--strict`-Meldung — **c(2)-a** (Empfehlung: **nein**), **c(2)-b** (ja, neuer V-Check), **c(2)-c** (ja, als `WARN`). **Empfehlung gesamt: c(1)-a + c(2)-a.** | Optionenzeile Spec `:4358`; Suboptionen-Tabelle Spec `:4364-4374`; Empfehlung/Owner/Termin Spec `:4376-4384` | **`main_chat`** (Spec `:4377`) | **vor** der Umsetzung von **W3-6** (Spec `:4378-4379`) |

**Zwei Abgrenzungen, die ausdrücklich gelten:**

- **E-13c ist kein sechstes P-Element und kein neues AC.** Es ist eine **offene
  Entscheidungsvorlage** (Spec `:4358`, `:4365`).
- **E-13a und E-13b sind nur in der *technischen* Dimension vorgesehen** — die Wellenzuordnung
  von **T-3 / T-5 / T-8** ist durch **V-D7 gemessen und festgeschrieben** (Spec `:4510`) und
  damit **keine offene Frage mehr**. **E-13 selbst bleibt OFFEN**: die Zuordnung des
  **Dokuanteils** (W8-4 oder W3-6) ist ausdrücklich **nicht** entschieden (Spec `:4360`,
  `:4510`).

**Sachstand zu E-13c, gemessen:** ein gültiger, kopierter `index-owner: docs-consolidation` ist
per Konstruktion **nicht** als Tippfehler erkennbar — weder per Enum (der Wert ist gültig) noch
per fail-closed Zweig IC-25 (1) (der Wert ist bekannt). Das Restrisiko ist **ausdrücklich nicht
akzeptiert** (Spec `:4358`). Eine Datei `config/agent-meta.config.example.yaml` als
Beispielträger **existiert im Repo nicht**; **keine** der beiden Beispiel-Configs enthält
heute einen `docs-consolidation`-Block (Spec `:4385-4391`).

### 3.3 Offene Fragen der Spec (§11.1)

Volltext: **Spec §11.1** (Spec `:2921-2939`). Die Legende nennt den offenen Satz
**„OQ1, OQ3, OQ4, OQ9, OQ10"** (Spec `:293`); Rev. 0.8 stellt **keine** davon auf und löst
**keine** auf (Spec `:2958-2959`).

| ID | Kurzbezeichnung | Quelle (Datei:Zeile) | Owner | Termin/Blocker |
|---|---|---|---|---|
| **OQ1** | Sollen `knowledge/wiki/topics/` vollständig in `docs/guides/` aufgehen, oder bleibt das Wiki bestehen? | Spec `:2925`; Bestätigung Spec `:4398` | `main_chat` (Eskalation) | **W5** |
| **OQ3** | `AGENTS.md`-Bootstrap-Block mitgenerieren? | Spec `:2926` | `requirements` (via `main_chat`) | **nach W8** |
| **OQ4** | ID-System: `REQ-*` vs. `SPEC-<NAME>-<JJJJ-MM-TT>` vereinheitlichen oder als zwei Ebenen definieren? | Spec `:2927` | `requirements` + `validator` | **W8** |
| **OQ9** | Welche der beiden Beispiel-Configs ist SSoT? | Spec `:2928` | `technical-writer` + `documenter` | **W5** |
| **OQ10** | V3-Severity für `docs/**`: behalten die **25** Fundstellen **ERROR**, oder Herabstufung auf **WARNING**, während `README.md` + `llms.txt` **ERROR** bleiben? **Solange offen, bleibt V3 dauerhaft rot und `--validate` auf 0 unerreichbar.** | Spec `:2929` | `orchestrator` (via `main_chat`) | Entscheidung **vor W8-4**; Welle **W8-4** (nur zur Terminierung von `--validate`; **kein** Blocker für W2–W7) |

**„Jede weitere offene Frage, die die Spec selbst als offen führt":** nach Prüfung der
Kennungslegende (Spec `:293`) und der Rev.-0.8-Bestätigung (Spec `:2958-2959`) ist der
vollständige offene Satz dieser Spec **genau** `OQ1, OQ3, OQ4, OQ9, OQ10`. **OQ10 ist damit
aufgenommen**; weitere offene OQ-IDs führt die Spec nicht.

**Geschlossen — nicht wieder aufrollen:**

| ID | Feststellung | Quelle (Datei:Zeile) |
|---|---|---|
| **OQ2** | `llms.txt` = **Hybrid** — handgepflegt, generiert werden ausschließlich `{{DOCS_PROVIDERS_BLOCK}}` und `{{DOCS_REPO_FACTS_BLOCK}}` | Spec `:2971` (§11.2); Bestätigung Rev. 0.8 Spec `:4399` |
| **OQ5** | **GESCHLOSSEN: kein Backport.** `DOCS_*`-Platzhalter werden ausschließlich von E3 substituiert, nie von E1/E2 | Spec `:2974` (§11.2) |
| **OQ6** | `docs/INDEX.md` ist **tracked**; **kein** `.gitignore`-Eintrag | Spec `:2972` (§11.2); Bestätigung Rev. 0.8 Spec `:4399` |
| **OQ7** | **GESCHLOSSEN: eine Datei, vier Module.** Die Entscheidung liegt beim `planner` | Spec `:2975` (§11.2) |
| **OQ8** | Regenerierung läuft **deterministisch über Sync/Validator**, **kein** Commit-Hook | Spec `:2973` (§11.2); Bestätigung Rev. 0.8 Spec `:4399` |
| **E-5…E-8** | **ENTSCHIEDEN** am 2026-09-27 (Nutzer, `main_chat`) — werden **nicht** neu aufgerollt | Spec `:4286-4287`; Plan `:560` |

---

## 4. Offene W2-Punkte und Abweichungen

Jeder Punkt unten trägt eine **Datei:Zeile**-Quelle. Wo die Auftragsvorgabe und der Working Tree
auseinandergehen, stehen **beide** nebeneinander.

### 4.1 W2-GATE-V1-Waiver

**Namensklärung, damit nichts erfunden wird:** der Plan führt **keine** Kennung
`W2-GATE-V1-Waiver`. Er führt (a) das Gate **`W2-GATE-V1`** (Plan `:2245`) und (b) das
**Gate-Votum `WAVE_COMPLETE_WITH_OPEN_ITEMS`** im Anhang „Abschluss der Welle W2"
(Plan `:7083`, `:7120`). „W2-GATE-V1-Waiver" ist die **Bezeichnung dieses Records** für
dieses Zusammenspiel, keine Plan-ID.

**Das Gate besteht in Zählung, nicht im Exit-Code.** Belege: Plan `:2199` („maßgeblich ist
**W2-GATE-V1** (Zählung statt Exit-Code)"); Plan `:886-889` („W2-GATE-V1, W2-GATE-ERRORS und
W-GATE sind **ohne** `sys.exit` geschrieben; ihr Exit-Code ist **kein** Kriterium"); Plan
`:2255-2264` („Das Kommando ruft **kein** `sys.exit` … Ausgewertet wird **ausschließlich** der
gedruckte Zählwert").

**Die drei Erfolgskomponenten und ihr Erfüllungsstand** (Komponenten-Tabelle Plan
`:7126-7130`; Kriterienzeile „nach **W2-7**" Plan `:2269`):

| Komponente von `W2-GATE-V1` (Zeile „nach **W2-7**") | Ist-Stand | Erfüllt |
|---|---|---|
| Zähl-Kommando druckt `v1-findings:` mindestens **1** | **52** | **ja** |
| Zähl-Kommando druckt `v1-severities:` **exakt** `['WARNING']` | **exakt** `['WARNING']` | **ja** |
| `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0** | **0/6**, Exit **1** | **nein** — Zeile aufgehoben, offener Punkt **(a)** |

**Ein Waivern ist keine Erfüllung.** Das Votum selbst legt das ausdrücklich fest, Plan
`:7132-7140`: die unerreichbare Komponente ist „seit der Baseline (ebenfalls 0/6) **nicht** durch
W2-7 entstanden", der „prüfbare Kern von AC-38 ist über den Test-Pin erfüllt" — **und**:
„**Warum es kein ‚grün' ohne Einschränkung ist:** die Zeile bleibt im Plan sichtbar,
gestrichen und begründet — **eine Welle gilt hier nicht als abgeschlossen, wenn eine geforderte
Verifikationszeile nachweislich unerreichbar ist**."

**Punkt (a) als offener Eintrag** (Plan `:7158`): Ersatzregel ist der Test-Pin über alle **63**
Fixtures. Owner **Vorschlag** `senior-developer`, Termin **Vorschlag 2026-10-11** — Plan
`:7165-7167` stellt ausdrücklich fest: „**Vorschläge zur Entscheidung durch den
Plan-Owner**, ausdrücklich **keine beschlossene Terminierung**".

### 4.2 W2-GATE-ERRORS

Definition Plan `:2286-2295`; Erwartungstabelle Plan `:2301-2307`. **Welche `docs.*`-Checks
planmäßig rot bleiben:**

| `check` (V) | Erwartung / Ist-Stand | Termin | Owner | Quelle (Plan) |
|---|---|---|---|---|
| `docs.no_manual_counts` (V1) | mindestens **1**, `['WARNING']` | Handzahlen werden erst in **W3-7** ersetzt | `developer` (W3-7) | `:2301` |
| `docs.docs_index_completeness` (V2) | **planmäßig rot** (ERROR) — `docs/INDEX.md` existiert **nicht** (Glob über die Repo-Wurzel ohne Treffer) | **W3-6** | `senior-developer` (W3-6) | `:2302` |
| `docs.internal_links` (V3) | **planmäßig rot** (ERROR), **drei** Klassen aus `W2-GATE-V3-KLASSEN` (Plan `:2323-2333`): **2** Layout-Findings `README.md:722`/`:723` (`:2331`) · **25** Link-Findings unter `docs/**`, live ohne `archive/` = **17** (`:2332`) · `llms.txt` **0** (`:2333`) | Layout ⇒ **W8-2**; Follow-up `F-DOCS-LINKS-2026-09-27` ⇒ **2026-10-11**, **kein** Termin 0 in W0–W8 | `developer` (W8-2 **und** Follow-up) | `:2303`, `:2323-2333` |
| `docs.readme_index` (V4) | Ist-Stand **genau 1** Finding — Kategorie `docs/se-cascade/` (deklariert `README.md:378`, ohne Link in der Region) | Follow-up `F-DOCS-README-INDEX-SE-2026-09-27`, **2026-10-11** | `developer` (W2-6 für den Scope, Follow-ups für die Behebung) | `:2304` |
| `docs.role_generation_parity` (V5) | Erwartung **0**, gemessener Ist-Stand **1 WARNING** — **Sollwert-Ist-Abweichung** | Termin-**Vorschlag** „W2-Wellenabschluss-Nachlauf" | Owner-**Vorschlag** `developer` (V5-Implementierung / Gate-Logik) | `:2305`, `:7159` |
| `docs.docs_facts_fresh` (V6) | **planmäßig rot** — Wert „rot" erfüllt, **Severity nicht**: Ist-Stand **3 WARNING**, ausschließlich Art `missing-in-expected` | Termin-**Vorschlag** **W3-7** | Owner-**Vorschlag** `developer` (W3-7), unverändert | `:2306`, `:7159` |
| `docs.wiki_staleness` (V7) | **planmäßig rot** (WARNING) — **10** Wiki-Seiten `type: "Architecture"` ohne `derived-from` | **W5-3** | `tester` (W5-3) | `:2307` |

**V5/V6: Owner und Termin sind ausdrücklich Vorschläge, keine beschlossene Terminierung.**
Plan `:2305` und `:2306` tragen beide den Zusatz „**Vorschlag zur Entscheidung durch den
Plan-Owner, keine beschlossene Terminierung**"; der Anhang wiederholt es für den offenen Punkt
**(b)** (Plan `:7159`, `:7165-7173`).

**Beleg, dass W2-GATE-ERRORS nicht vollständig grün ist** — Plan `:7141-7144`, wörtlich:
„**Was das Votum ausdrücklich nicht behauptet:** `W2-GATE-ERRORS` ist **nicht** vollständig
grün. Zwei Zeilen dieser Tabelle tragen eine **gemessene** Abweichung vom Erwartungswert
(**V5, V6**), und der rohe Runner ist **planmäßig** rot. Das ist der vorgesehene Zustand, wird
aber nicht als Zielerreichung ausgegeben." Zusätzlich Plan `:7074`: „Sollwert-Ist-Differenzen
gegen `W2-GATE-ERRORS` sind **offen**."

**Nicht verhandelbar:** diese Tabelle wird **nicht** nach unten gesetzt. Plan `:7180-7183`:
„Was dieser Anhang **nicht** tut: er setzt **keine** Checkbox, erteilt **keinen** Auftrag, legt
**keinen** Task an, vergibt **keine** K-Kennung und ersetzt **keinen** Sollwert der Tabelle
`W2-GATE-ERRORS`."

### 4.3 Modulreserven

**Sollzustand (Rev. 0.6, K18).** `scripts/lib/consistency/docs.py` wird zur **Fassade**; die
Prüfebene wird nach Familien aufgeteilt — `docs_links.py` (V3, V4,
`check_sync_cli_docs`, `check_ui_help_mappings`) · `docs_freshness.py` (V1a/V1b, V6) ·
`docs_wiki.py` (V7, V8) · `docs_index.py` (V2, V9). **12** Zuordnungen auf **4** Module, jedes
**kleiner als 600** Zeilen. Quelle: Spec `:63`, Spec `:527` (Rev.-0.6-Zeile), Plan `:92-104`,
Plan `:2788`.

**Gemessener Ist-Stand (DoD-Votum vom 2026-09-28):**

| Modul | Ist | Reserve | Quelle |
|---|---|---|---|
| `scripts/lib/consistency/docs_links.py` | **599** Zeilen | **1** Zeile | Plan `:7160` (DoD-Votum 2026-09-28). **Unabhängig bestätigt:** die Datei endet bei Zeile **599**. |
| `scripts/lib/consistency/docs_freshness.py` | **598** Zeilen | **2** Zeilen | Plan `:7161` |
| `docs_freshness.py` — **ältere** Werte | **593** (F1-Promotion-Notiz) bzw. **592** (W2-4/W2-5) | — | Plan `:7161` (nennt beide als Historie) |

**Benannter Widerspruch — Modulanzahl.** „**4** Module / **12** Zuordnungen" ist der Stand
**Rev. 0.6 (K18)**. **Rev. 0.7 / E-7 / K56** hat **V5** in ein eigenes Modul
**`docs_freshness_v5.py`** verschoben; der belegte heutige Stand ist **5 Familienmodule + 1
Fassade = 6 Dateien**, und die Zuordnung bleibt **12/12 disjunkt** (Spec `:529`, Rev.-0.7-Zeile:
„Zuordnung bleibt **12/12 disjunkt**, jetzt auf **5** Module"). Im Repo vorhanden (Glob
`scripts/lib/consistency/docs*.py`): `docs.py`, `docs_freshness.py`, `docs_freshness_v5.py`,
`docs_index.py`, `docs_links.py`, `docs_wiki.py`. **Beide** Stände bleiben hier stehen; keiner
wird gelöscht.

**Weiterer offener Punkt (c)** (Plan `:7160`): geplanter Folgetask „**V4 aus `docs_links.py`
herauslösen**" (nimmt Bildform, 1-Zeilen-Reserve, Rest von F-5 und die F-1/F-2-Kopplung in
einem Zug auf). Owner: **Plan-Owner**, im Plan eingetragen, **kein** Task angelegt. Termin:
**im Plan nicht belegt** — die Task-Notiz nennt keinen Termin.

**Weiterer offener Punkt (d)** (Plan `:7161`): `docs_freshness.py` **598/600**, 2 Zeilen
Reserve; Termin **im Plan nicht belegt**.

### 4.4 Stale Docstrings

Beide sind **gemessen** am Working Tree, beide stehen als offene Items (e) und (f) im
DoD-Anhang.

| # | Fundort | Behauptung | Ist | Owner | Termin | Quelle |
|---|---|---|---|---|---|---|
| **(e)** | `scripts/lib/consistency/docs_wiki.py:35-40` | „``Finding`` (``report.py``) carries no ``line`` and no ``branch`` field" | seit der F1-Promotion **falsch** | **W6-2** (der Plan führt die Datei in dessen Schreibmenge) | **im Plan nicht belegt** | Plan `:7162`; **am Working Tree gelesen** (`docs_wiki.py:35-40`) |
| **(f)** | `scripts/lib/consistency/docs_links.py:450-452` | Docstring von `_v3_finding`: ``Finding`` habe weder ``line`` noch ``branch`` und „W2-7 owns the runner and should promote them" | **W2-7 hat das getan, aber nur für `docs_freshness.py`**; `_v3_finding` blieb unangetastet, weil W2-7 die Datei **nicht** in seiner Schreibmenge führt | **W2-6** (`developer`) — **mit ausdrücklicher Einschränkung:** W2-6s `Files:` ist auf die **V4**-Umfassung begrenzt, der Fundort liegt jedoch im **V3**-Teil. **Der nächste Besitzer für genau diesen Eingriff ist im Plan nicht belegt und wird hier nicht geraten.** | **im Plan nicht belegt** | Plan `:7163`; **am Working Tree gelesen** (`docs_links.py:448-453`) |

### 4.5 V6-`kind` — die Art dieser Abweichung

Das Attribut `kind` von V6 bleibt ein **reines Instanzattribut** und erscheint **nicht** im
`--json`. Ein Feld `kind` in `Finding` wäre eine **Ausgabe-Erweiterung** des Report-Schemas
**ohne** IC und **ohne** Akzeptanzpunkt; die Task-Interfaces und **IC-05** nennen ausdrücklich
**nur** `line` und `branch`. Plan `:7191-7194` wörtlich: „**Kein Defekt der F1-Promotion** —
planseitig klassifiziert, **kein offener Auftrag**."

**Art der Abweichung:** eine **bewusst nicht abgesicherte, dokumentierte Beobachtung**. Sie
trägt **keine** Handlung, wird deshalb **nicht** unter den offenen Items geführt und geht
**nicht** in das Gate-Votum ein (Plan `:7185-7189`, Abschnitt E des DoD-Anhangs: „sie tragen
keine Handlung, werden deshalb **nicht** unter den offenen Items geführt und gehen **nicht** in
das Gate-Votum aus Abschnitt B ein"). Sie wird hier genau deshalb festgehalten, damit sie bei
einem späteren Chore nicht verloren geht — und ausdrücklich **nicht**, damit ein Task daraus wird.

**Gleichartige Beobachtung, ebenfalls kein Task** (Plan `:7196-7200`): der strukturelle
Registry-Test `test_the_docs_registry_covers_exactly_what_the_facade_exports` hängt am
heutigen Stillstand der „Clean"-Checks; eine spätere Chore, die V2/V3/V6 auf **0** bringt,
macht ihn rot. Das ist **bewusst nicht abgesichert**.

### 4.6 B6 — CI-Stelle für `sync.py --check` und die Drift-Detection

**B6 als Blocker.** Quelle: Systemdesign
`docs/specs/2026-09-25-repository-documentation-consolidation-design.md:304` — „`AGENTS.md`-Layout
(aus `PROJECT_STRUCTURE`) ändert sich → generierte Kontextdatei in **jedem** Consumer" ·
Betroffene: alle Submodule-Consumer · Einstufung **niedrig** · Mitigation: „managed-block-Mechanismus
(`context.py:36`) fängt Handpflege ab; **Drift-Detection meldet**". Entlastungsabsatz: Design
`:306` (echter Downstream-Impact ist auf **B2**, **B5** und **B6** begrenzt).

**Plan-Bezug R13/B6:** Risikotabelle Plan `:6135` („R13 `PROJECT_STRUCTURE`-Diff (B6) | niedrig |
W8-4 additiver Config-Edit, managed block + Drift-Detection, Layout-Diff muss im Review
quittiert werden"); Umsetzung in **W8-4**; Layout-Diff-Quittierung als Merge-Gate Plan
`:5556-5559` („**explizit quittiert** werden (B6); ohne Quittung kein Merge"); W8-3 Schritt 3
Plan `:5716` („Layout-Diff im Review quittieren lassen (B6/R13)"). **Spec R13** Spec `:3002`.

**Gemessener CI-Befund — die Auftragsprämisse „fehlender `--check`-CI" trifft nicht zu; die
Lücke liegt woanders.** Diese Formulierung ist **als Beleg** formuliert, nicht erfunden:

| CI-Stelle | Was sie ausführt | Quelle |
|---|---|---|
| `.github/workflows/validate.yml` | Szenario-Suite; `python scripts/sync.py --validate`; **Drift-Gate: `python3 scripts/sync.py --check`**; Frontmatter-Lint der `agents/**/*.md` | `.github/workflows/validate.yml:22`, `:34`, `:40-41`, `:42-57` |
| `.github/workflows/orchestration-test.yml` | `python -m pytest tests/ -q` (Matrix 3.9 / 3.11 / 3.12); `python scripts/sync.py --validate` | `.github/workflows/orchestration-test.yml:33`, `:48`, `:51` |

**Was tatsächlich fehlt — zwei getrennte Lücken:**

1. **Kein Workflow führt `scripts/consistency-check.py` aus.** In `.github/workflows/` stehen
   nur die beiden Dateien `validate.yml` und `orchestration-test.yml`; ein Treffer auf
   `consistency-check` unter `.github/` existiert **nicht**. Damit hat die **Doku-Check-Ebene
   (V1…V9)** in CI **keine** Stelle. Die Wellen-Gates `W2-GATE-V1` / `W2-GATE-ERRORS` /
   `W-GATE` werten Zählwerte aus `consistency-check.py --json` aus (Plan `:2250-2253`,
   `:2292-2295`) — **kein** CI-Job erzeugt diese Zählwerte.
2. **Das Drift-Gate ist auf Self-Hosting nicht grün.** Der Kommentar in
   `.github/workflows/validate.yml:35-39` benennt den offenen Mangel selbst: bei
   agent-meta-Self-Hosting sind die generierten Provider-Verzeichnisse gitignoriert, ein frischer
   CI-Checkout meldet deshalb **zusätzliche `[INIT]`-Aktionen** für absichtlich fehlende Dateien
   (Issue **#739**, Defekt **4**) — „the gate becomes fully green once that defect is fixed".

**Historischer, inzwischen überholter Befund — beide Quellen bleiben stehen.**
`docs/plans/2026-09-11-audit-batch-730-743-plan.md:24` behauptet: „`.github/workflows/validate.yml`
runs only `--validate` (no `--check`)". Das ist **durch** `.github/workflows/validate.yml:40-41`
**überholt**. Die ältere Aussage wird hier **nicht** gelöscht und **nicht** umgeschrieben; sie
ist als überholt markiert.

**Nebenbefund, gleichgelagert:** `docs/guides/ci/github-actions-sync-check.yml` ist eine
**Vorlage** („Copy this job into your project's CI workflow", `:2`) für **Consumer**-Projekte
(`python .agent-meta/scripts/sync.py --dry-run --check`, `:20`; `--validate-spec-plan`, `:25`).
Sie ist **keine** aktive CI-Konfiguration dieses Repos und wird hier **nicht** als CI-Stelle
gewertet.

### 4.7 Zeilenanker-Drift durch die Pause-Änderungen — benannte Abweichung

Die drei Pause-Änderungen fügen Zeilen **in** die Spec und **in** den Plan ein. Damit verschieben
sich die Zeilennummern **dieser beiden Dokumente**, und Verweise **anderer** Dokumente auf
Plan-Zeilen — etwa die Belege in Spec **V-D8** (Spec `:4511`) und in **V-D8-Uebergabe**
(Spec `:4523-4532`) — zeigen nun auf **Vor-Pause-Zeilen**.

**Gemessene Verschiebung:**

| Datei | Bereich | Verschiebung |
|---|---|---|
| Spec | Zeilen 1…8 | **0** (Frontmatter-Kopf unverändert) |
| Spec | Zeilen 9…24 | **+1** (neues Feld `paused` in Zeile 9) |
| Spec | Zeilen 25… und darüber hinaus | **+23** (PAUSE-Block im Kopf, 21 Zeilen, plus 1 aus dem Frontmatter, plus 1 aus der neuen Revisionszeile Runde 10) |
| Plan | Zeilen 1…5 | **0** |
| Plan | Zeilen 6…22 | **+3** (Felder `approved`, `approved-scope`, `paused`) |
| Plan | Zeilen 23…4918 | **+26** (PAUSE-Block im Kopf, 23 Zeilen, plus 3 aus dem Frontmatter) |
| Plan | Zeilen 4919…5071 | **+43** (zusätzlich der ENTRY-BLOCKER in Task W3-6) |
| Plan | Zeilen 5072… und darüber hinaus | **+56** (zusätzlich der ENTRY-BLOCKER in Task W4-3) |

**Behandlung:** die Belege **in diesem Record** sind auf den neuen Stand nachgezogen. Die
Belege **in der Spec** (V-D8 und V-D8-Uebergabe zitieren Plan-Zeilen wie `:4920-4921`,
`:4926`, `:4938-4944`, `:2115-2118`, `:2082`, `:5694`, `:2095-2098`, `:2084`, `:2096`, `:7349`)
sind **nicht** nachgezogen. Grund: sie stehen in **normativem** Spec-Text (V-D8-Register und
V-D8-Uebergabe), und das Nachziehen wäre eine inhaltliche Änderung der Spec — die dieser
Record ausdrücklich **nicht** vornimmt (siehe Abschnitt 6). **Folge:** die Spec-Formulierung
„Plan Rev. 0.7 … `:5-6`" (Spec `:4511`) beschreibt den **Pausen-Stand nicht** mehr exakt; sie
beschreibt den Stand **vor** der Pause. Das ist eine **benannte** Abweichung, kein stiller Fehler,
und sie ist Kandidat für den in Abschnitt 5, Schritt 2, vorgesehenen Plan-Delta (PD-1…PD-10).

---

## 5. Resume-Reihenfolge

Die Reihenfolge ist **zwingend** und ergibt sich aus Spec §17.12.5, V-D8-Uebergabe (Spec
`:4513-4519`): „**Reihenfolge-Zwang:** P-1…P-5 ⇒ Plan-Revision ⇒ **dann** W3-6. Vor der
Freigabe darf **kein** Plan-Task angefasst werden."

### Schritt 0 — Widerspruch W0/W1 auflösen *(nachträglich, vor Schritt 1 nützlich)*

- **Owner:** Plan-Owner über `main_chat`.
- **Eintrittsbedingung:** keine.
- **Gegenstand:** der in Abschnitt 2.2 benannte Widerspruch zwischen Auftragsvorgabe
  („W0, W1, W2 abgeschlossen") und dem Plan-Ledger (W0 komplett offen; W1-5 Schritt 4 und
  W1-10 Schritte 2 und 4 offen).
- **Danach erst erlaubt:** ein belastbares Wellen-Resume. Wird er **nicht** aufgelöst, gilt ab
  Schritt 1 die **konservativere** Lesart: W1-10 ist offen, und damit greift zusätzlich die
  Reihenfolgebindung aus **PD-8** (Spec `:4530`): W1-10 **Step 2 vor W3-6 ziehen** oder als
  Bestandteil von W3-6 führen.

### Schritt 1 — User-Entscheidung über **P-1 … P-5** und **E-9 … E-13**

- **Owner:** `main_chat` / Nutzer (Spec `:4377`, `:4257`).
- **Eintrittsbedingung:** keine — das ist der auslösende Schritt.
- **Gegenstand:** die fünf Pflichtänderungen P-1…P-5 (Abschnitt 3.1) und die fünf
  Entscheidungsvorlagen E-9…E-13 einschließlich **E-13c** (Abschnitt 3.2). Jede Vorlage hat
  eine Empfehlung; die Empfehlung ersetzt **keine** Entscheidung (Spec `:4376-4377`).
- **Danach erst erlaubt:** das Aufsetzen von Schritt 2. **Nicht** erlaubt bleibt: jedes
  Anfassen eines Plan-Tasks.

### Schritt 2 — **Plan-Revision auf Rev. 0.8**

- **Owner:** `planner` (Spec `:4496-4497`).
- **Eintrittsbedingung:** Schritt 1 abgeschlossen; das Ergebnis ist in Spec §17.12.1 / §17.12.2
  nachvollziehbar festgehalten.
- **Gegenstand:** der **forderliche Plan-Delta** **V-D8-Uebergabe**, **PD-1 … PD-10**
  (Spec `:4513`, `:4523-4532`): Frontmatter `pending-approval:` (PD-1); W3-6 `Files:`
  (PD-2), `Ziel-AK` (PD-3), `Akzeptanz` (PD-4), `Steps` mit Reihenfolge **T-8 → T-3 → T-5**
  (PD-5), `Verifikation` (PD-6); W1-9-Zifferkorrektur (PD-7); W1-10-Reihenfolge (PD-8);
  Trace-Matrizen (PD-9); Plan-E-13-Zeile (PD-10).
- **Warum zwingend:** die W3-6-Akzeptanz nach Spec §17.12.4 ist **vom heutigen Plan aus
  unerfüllbar** — `index-owner`, `AC-4[2-6]` und `pending-approval` sind im Plan **0** Treffer
  (Spec `:4487-4498`, V-D8 Spec `:4511`).
- **Danach erst erlaubt:** W3-6. `revision: 0.7` des Plans **bleibt bis hierher 0.7** — die
  Plan-Rev. 0.8 ist der Resume-Schritt, **nicht** Teil dieser Pause.

### Schritt 3 — **W3-6**

- **Owner:** `senior-developer` (Plan `:4968`).
- **Eintrittsbedingung:** Schritt 2 abgeschlossen. **Ohne** User-Entscheidung und **ohne**
  Plan-Rev. 0.8 ist W3-6 **nicht startbar** (Spec `:4515-4516`; ENTRY-BLOCKER im Plan direkt
  unter der Task-Überschrift W3-6).
- **Gegenstand:** `docs/INDEX.md` tracked, Erstgenerierung, OQ6/OQ8-Umsetzung (Plan `:4944`).
  Die Spec bindet den Nachweis an T-7, T-8, T-3 (a/b) und T-5 **in derselben Welle** (V-D7,
  Spec `:4510`).
- **Danach erst erlaubt:** W3-7 (Plan `:5767`) und der Rest der Welle W3.

### Schritt 4 — **W4-3**

- **Owner:** `tester` (Plan `:5132`).
- **Eintrittsbedingung:** Schritt 3 abgeschlossen. Die Querwellenkette ist
  **W3-6 → W4-1 → W4-2 → W4-3** (Plan `:5766`, `:5768`, `:5769`, `:5770`; Kantenliste
  Plan `:5973`). **Ohne** User-Entscheidung und **ohne** Plan-Rev. 0.8 ist W4-3 ebenfalls
  **nicht startbar** — zusätzlich ist E-11 ausdrücklich **vor** W3-6 zu entscheiden
  (Abschnitt 3.2).
- **Gegenstand:** `docs/architecture/INDEX.md` und AC-29-Nachweis (Plan `:5114`), inklusive
  Abschluss-Sync-Lauf in Schritt 4 (Plan `:5159-5165`).
- **Danach erst erlaubt:** W5-1 (Plan `:5771`), damit die Kante `W4-3 → W5-1` (Plan `:5973`,
  `:8182`) bedient ist.

---

## 6. Was dieser Record **nicht** tut

- **Kein Beta.** Es wird kein Release-Stand erzeugt, kein `VERSION` angefasst, kein Changelog
  geschrieben.
- **Kein Merge.** Weder PR #839 noch ein anderer PR wird gemergt; es erfolgt **keine**
  Git-Mutation durch diesen Record.
- **Kein Ready.** Es wird **kein** `READY_FOR_MERGE`, **kein** `STATUS: done` und **keine**
  Archivierung ausgelöst. `docs/plans/README.md:3-7` stellt die Archivierung von abgeschlossenen
  Plänen unter die Bedingung „sobald sie erledigt sind" — dieser Record **erledigt** nichts.
- **Keine Freigabe von P-1 … P-5 und E-9 … E-13.** Der Record **sperrt**; er erteilt keine
  Implementierungsfreigabe für IC-25, IC-26, AC-42…AC-46, T-3, T-4, T-5, T-7, T-8 und für
  keinen der Sollwert-Pins.
- **Kein Zurückziehen des Freigabe-Markers für den Umfang W0–W8.** Die historische
  User-Freigabe vom **2026-09-26** bleibt als **Fakt** stehen. Im Spec ist sie über
  `approved: 2026-09-26` (Spec `:5`) und `approved-scope` (Spec `:6`) erhalten; im Plan ist sie
  über die **neu hinzugefügten** Felder `approved: 2026-09-26` (Plan `:6`) und `approved-scope`
  (Plan `:7`) erhalten, **obwohl** das Feld `status` von `APPROVED` auf `PAUSED` gesetzt wurde.
  **Benannte Abweichung:** die K34-Wortgleich-Klausel des Plan-Anhangs (Plan `:7088`) nennt
  „`status: APPROVED` (`:5`)" als wortgleich zu haltende Stelle; das bezieht sich auf den Stand
  **vor** dieser Pause und ist durch den ausdrücklichen Auftrag, den Plan-Status auf `PAUSED` zu
  setzen, **überholt**. Der Plan-Satz, der denselben Freigabefakt trug, steht unverändert im
  Statusabsatz des Kopfs. Der Umfang W0–W8 wird **nicht** zurückgezogen; gehalten wird nur, dass
  er vor W3-6 angehalten wurde. W3–W8 bleiben im Grundsatz vom Nutzer freigegeben, aber **nicht**
  startbar, solange die Sperre aus Abschnitt 3 besteht.
- **Keine Löschung von Revisions- oder Review-Historie.** Weder die Spec-Revisionen
  0.4 / 0.5 / 0.6 / 0.7 / 0.8 (Spec `:525`, `:526`, `:527`, `:529`, `:530`) noch die
  Korrekturrunden-Historie (Spec `:532`, `:533`, und die **neu hinzugefügte** Zeile für Runde 10,
  Spec `:534`) noch die Plan-Revisionen 0.1…0.7 noch die sechs Korrekturrunden des Plans werden
  gekürzt, zusammengezogen oder umformuliert. Dieser Record ist **eine** additive Zeile in dieser
  Historie, **kein** Bestandteil davon.
- **Keine ID-Änderung, keine Checkbox, kein Sollwert.** Es wird keine Task-, Wellen-, AC-, IC-,
  NFA-, R-, OQ-, F-, V-Check- oder K-Kennung vergeben, umnummeriert oder gestrichen; keine
  Checkbox gesetzt, gestrichen oder ergänzt; kein Sollwert ersetzt. Der Revisionswert des Plans
  bleibt **0.7**; die Task-Checkboxen von W3-6 (Plan `:4982-4987`) und W4-3 (Plan
  `:5154-5166`) bleiben **unverändert offen**.

---

## 7. Belegverzeichnis dieses Records

Alle Zeilenangaben wurden am Working Tree per Read/Grep geprüft, **nach** den drei
Pause-Änderungen. **Nicht** per Grep nachlesbar waren die als **Übergabe** markierten Angaben
(PR-Status, Branch, HEAD, Commit-Datum, Testzahl 3421, Testzahl 3479), weil kein
Git-Kommando verfügbar war; sie sind in Abschnitt 2 als solche gekennzeichnet.

| Gegenstand | Primärquelle (Post-Pause-Stand) |
|---|---|
| P-1…P-5, P-3 (e) | Spec `:4256` (Überschrift), `:4266-4274` (P-Tabelle), `:4258-4265` (Zählauflösung); Design `:677-690` |
| E-9…E-13, E-13c | Spec `:4284-4400`; Design `:593-671` |
| OQ-Menge offen / geschlossen | Spec `:293`, `:2921-2939`, `:2967-2975`, `:2958-2959`, `:4393-4400` |
| V-D7, V-D8, V-D8-Uebergabe, PD-1…PD-10, Reihenfolge-Zwang | Spec `:4510`, `:4511`, `:4513-4519`, `:4523-4532` |
| W3-6-Akzeptanz unerfüllbar (Hinweis) | Spec `:4487-4498` |
| W2-Gate-Votum und Komponenten-Tabelle | Plan `:7083`, `:7120`, `:7126-7130`, `:7141-7144` |
| W2-GATE-V1 (Zählung statt Exit-Code) | Plan `:2199`, `:2245-2269`, `:886-889` |
| W2-GATE-ERRORS, W2-GATE-V3-KLASSEN | Plan `:2286-2333` |
| Offene Items (a)…(f) | Plan `:7152-7163`, Terminlogik `:7165-7173` |
| Modulreserven, Modulanzahl | Spec `:63`, `:527`, `:529`; Plan `:92-104`, `:2788`, `:7160-7161` |
| Stale Docstrings | Plan `:7162-7163`; `docs_wiki.py:35-40`; `docs_links.py:448-453` |
| V6-`kind` | Plan `:7185-7189`, `:7191-7194`, `:7196-7200` |
| B6, R13 | Design `:304`, `:306`; Spec `:3002`; Plan `:5556-5559`, `:5716`, `:6135` |
| CI-Stellen | `.github/workflows/validate.yml:22`, `:34`, `:35-41`; `.github/workflows/orchestration-test.yml:33`, `:48`, `:51`; `docs/guides/ci/github-actions-sync-check.yml:2`, `:20`, `:25` |
| W3-6 / W4-3 Einstieg und Kette | Plan `:4944`, `:4963-4969`, `:4981-4987`, `:5114`, `:5129`, `:5132`, `:5154-5166`, `:5766-5771`, `:5973`, `:8182` |
| W1 offene Schritte | Plan `:2026`, `:2028`, `:2141`, `:2146`, `:2148` |
| W0 offene Checkboxen | Plan `:1684-1897` |
| Vollteststände | Plan `:2998-2999`, `:3822`, `:3881-3882`, `:4381-4384`, `:4385-4386`, `:4386-4388` |
| `docs/INDEX.md` existiert nicht | Glob über die Repo-Wurzel ⇒ keine Treffer |
| Spec-/Plan-Kennungen und Pause-Felder | Spec `:5-9`; Plan `:5-9`; Plan-Katalog-Legende Plan `:560-562` |
| Zeilenanker-Drift dieser Pause | Abschnitt 4.7 dieses Records |
