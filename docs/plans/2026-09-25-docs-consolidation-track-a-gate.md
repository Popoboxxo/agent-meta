---
plan-id: PLAN-DOCS-CONSOLIDATION-2026-09-25
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
title: W0-4 — Track-A-Kollisionsgate (R3, R15) — Gate-Record
status: done
revision: 0.2
related:
  - docs/plans/2026-09-25-repository-documentation-consolidation.md
  - docs/specs/2026-09-25-repository-documentation-consolidation.md
  - docs/specs/2026-09-25-repository-documentation-consolidation-design.md
  - docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md
  - docs/plans/2026-09-25-docs-consolidation-oq6.md
---

# W0-4 Gate-Record — Track-A-Kollisionsgate (R3, R15)

**Datum:** 2026-09-26
**Ausführungsinstanz:** `test-executor` (Subagent, Execution-only)
**Branch:** `feat/repository-documentation-consolidation-main` @ `95ac76df`
**Vergleichs-Referenz:** `origin/main` = `3c46920a` (Squash-Merge PR #833)
**Plan:** `docs/plans/2026-09-25-repository-documentation-consolidation.md` — Task **W0-4** (plan:363-397)
**Nachführung:** 2026-09-26 — Plan-Verweise auf **Plan Rev. 0.2** nachgeführt (Synchronitätskriterium
`0 0` → **linke Zahl `0`**; die beiden Kommando-Formulierungsfehler im Plan sind dort korrigiert).
Messwerte, Bewertung, Gate-Entscheidung und Freigabe sind **unverändert**.
**Nachführung 2026-09-26 (Rev. 0.1 → 0.2, Plan Rev. 0.3):** Vier Ergänzungen, **keine** Änderung
der Gate-Entscheidung und **keine** Änderung der Freigabe W1/W2: (a) **YAML-Frontmatter**
ergänzt — der Record war über `plan_identity.py` nicht zuordenbar und führte zwei Nachführungen
ohne `revision`; (b) **zwei R3-Gegenproben** (`scripts/lib/`, `config/`) als Nachweiszeile
ergänzt, damit R3 vollständig abgedeckt ist; (c) Artefaktinventar um `verify.txt` ergänzt und
die `.tmp/`-Belege als **nicht teil des PRs** gekennzeichnet; (d) **Evidenzklassen-Spalte**
(Konvention siehe „Konvention: Evidenzklassen" unten) und Branch-Bestand (**2** Branches)
übernommen. Details in §3.1, §9 und §10.
**Ziel-AK:** AC-07, AC-08 (Fixture-Kollision), AC-39 (Schema-Datei)

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
Folgewellen: ein `✅` **ohne** Evidenzklasse ist unvollständig. In diesem Record ist **jede**
Zeile der Gate-Tabellen `gemessen` (alle Kommandos wurden ausgeführt), mit Ausnahme der
Bestandszeilen, die aus dem W0-2-Record stammen — dort ist die Quelle benannt.

## 1. Gate-Entscheidung

> ## ✅ GO — W1 und W2 sind freigegeben.
>
> Der Track-A-Merge ist **gegen `origin/main`** nachgewiesen. Beide Kollisionskriterien
> (a) und (b) sind inhaltlich erfüllt, die Stand-Synchronität ist erfüllt. Zusätzlich sind die
> beiden weiteren R3-Kollisionsflächen `scripts/lib/` und `config/` durch Gegenproben belegt
> (siehe §3.1) — sie sind **Nachweis**, nicht Freigabebedingung.

**Abgedeckter Nachweisumfang dieses Gates (Plan Rev. 0.3, K10):** R3 nennt **drei**
Kollisionsflächen. Dieses Record belegt **alle drei** — `tests/fixtures/` über den
`ls-tree`-Nachweis (§3, Kommandos 2–4) sowie `scripts/lib/` und `config/` über die beiden
Gegenproben (§3.1). Die Kriterienliste **(a)–(d)** der Fassung Rev. 0.1 beschrieb dagegen nur
die Fixture-Fläche plus Synchronität; der **tatsächlich abgedeckte Umfang** ist deshalb hier
explizit benannt — es wurde die Gate-Aussage **nicht** verengt, sondern der Nachweisumfang
ergänzt.

| Kriterium | Erwartung | Ergebnis | Evidenzklasse | Status |
|---|---|---|---|---|
| (a) `tests/fixtures/slimming-golden/` in `origin/main` | Treffer | Verzeichnis als Tree `1b6a74e1` in `main` vorhanden, 59 Einträge | `gemessen` | ✅ |
| (b) `tests/fixtures/docs_v1_fixtures.md` in `origin/main` | leer | leer (zusätzlich: kein Treffer im gesamten Baum) | `gemessen` | ✅ |
| (c) `docs_v1_fixtures.md` im Arbeitsbaum | nicht vorhanden | nicht vorhanden | `gemessen` | ✅ |
| (d) Branch nicht hinter `origin/main` | linke Zahl = 0 | `0 2` → links `0` | `gemessen` | ✅ |
| (e) `scripts/lib/` ohne Diff gegen `origin/main` | leer | **leer** (keine geänderten Dateien) | `gemessen` | ✅ |
| (f) `config/` ohne Diff gegen `origin/main` | leer | **leer** (keine geänderten Dateien) | `gemessen` | ✅ |

**Freigabe betrifft:** W1 (alle Tasks) und W2 (alle Tasks).
**Freigabe betrifft NICHT:** W3 und alle übrigen Wellen — sie sind durch dieses Gate nicht
berührt und bleiben von ihren eigenen Kriterien abhängig.
**Nicht Gegenstand dieses Gates:** der überholte Branch
`feat/repository-documentation-consolidation` (Bestand: **2** Branches mit gemeinsamem Präfix,
davon 1 aktiv, 1 auf Nutzer-Vorgabe erhalten; siehe W0-2-Record Kapitel 7.2). Er wird
**nicht** gelöscht und ist **kein** Gate-Kriterium.

## 2. Vorprüfung

| Kommando | Ergebnis |
|---|---|
| `git status --porcelain` | **leer** (Exit 0) — Arbeitsbaum sauber, keine Vorabänderungen |
| `git branch --show-current` | `feat/repository-documentation-consolidation-main` |
| `git log --oneline -3` | `95ac76df` docs(docs-consolidation): apply OQ2/OQ6/OQ8 decisions and plan fixes · `80260cf4` docs(repo): add documentation consolidation spec and plan · `3c46920a` feat(routing): add dynamic role activation and template slimming (#833) |
| `git remote -v` | ausgeführt; Ausgabe **bewusst nicht** in diesen Record übernommen (Host-/Identitätsdaten) |

## 3. Gate-Prüfungen — Einzelkommandos

| # | Kommando | Erwartet (Plan) | Exit | Gekürzter Output | Status |
|---|---|---|---|---|---|
| 1 | `git fetch origin` | `0` | **0** | *(stillschweigend)* | ✅ |
| 2 | `git ls-tree -d origin/main -- tests/fixtures/slimming-golden/` | Treffer | **0** | **leer** | ⚠️ siehe §5.1 |
| 3 | `git ls-tree -r --name-only origin/main -- tests/fixtures/slimming-golden/` | nicht leer | **0** | **59** Einträge (58 Fixtures + `README.md`) | ✅ |
| 4 | `git ls-tree origin/main -- tests/fixtures/docs_v1_fixtures.md` | leer | **0** | **leer** | ✅ |
| 5 | `ls tests/fixtures/docs_v1_fixtures.md` | `1` | **2** | `ls: Zugriff auf '…' nicht möglich: Datei oder Verzeichnis nicht gefunden` | ⚠️ siehe §5.2 |
| 6 | `git rev-list --left-right --count origin/main...HEAD` | `0 0` | **0** | **`0 2`** | ⚠️ siehe §4 |

> **Nachführung 2026-09-26 (Plan Rev. 0.2):** Die Spalte „Erwartet (Plan)" gibt den
> Plan-Stand **vor** Rev. 0.2 wieder. Der Plan verlangt seither **linke Zahl `0`** (rechte Zahl
> unbeschränkt), gleichbedeutend `git merge-base --is-ancestor origin/main HEAD` → Exit `0`.
> Der gemessene Wert `0 2` erfüllt diese Fassung; Bewertung (§4) und Gate-Entscheidung (§1)
> dieses Records bleiben unverändert.

**Ergänzende Gegenproben (zur Absicherung von (a), da Kommando 2 den Nachweis nicht liefert):**

| Kommando | Exit | Output |
|---|---|---|
| `git ls-tree origin/main -- tests/fixtures/` | 0 | `… tests/fixtures/legacy-registries` · `… tests/fixtures/slimming-golden` → **Tree vorhanden** |
| `git ls-tree -d origin/main -- tests/fixtures/` | 0 | `040000 tree 1b6a74e1ac10696404f4f829a17367f8d4012cc0 tests/fixtures/slimming-golden` |
| `git cat-file -t 1b6a74e1ac10696404f4f829a17367f8d4012cc0` | 0 | `tree` (Objekt existiert real in `main`) |
| `git ls-tree origin/main -- tests/fixtures/slimming-golden/` (ohne `-d`) | 0 | 59 Blobs, u. a. `effort-estimator.md`, `orchestrator.md` |
| `git ls-tree -r --name-only origin/main \| grep -i docs_v1` | 1 | **kein Treffer** im gesamten Baum (unabhängige Bestätigung von (b)) |

### 3.1 R3-Gegenproben für `scripts/lib/` und `config/` (Plan Rev. 0.3, K10)

**Lücke, die diese Nachweiszeile schließt:** R3 nennt **drei** Kollisionsflächen —
`scripts/lib/`, `config/` **und** `tests/fixtures/`. Die Plan-Fassung Rev. 0.2 beliegte nur
`tests/fixtures/`; der `scripts/lib/`-Nachweis war per Plan aus dem Nachweisumfang entfernt
worden. Damit war R3 nur **1 von 3** Flächen abgedeckt. Beide fehlenden Flächen sind jetzt
**ausdrücklich Teil der W0-4-Welle** und hier gemessen (2026-09-26, Evidenzklasse `gemessen`):

| # | Kommando | Erwartet (Plan Rev. 0.3) | Exit | Output | Evidenzklasse | Status |
|---|---|---|---|---|---|---|
| 7 | `git diff --name-only origin/main..HEAD -- scripts/lib/` | **leer** | **0** | **leer** — keine Datei unter `scripts/lib/` unterscheidet sich von `origin/main` | `gemessen` | ✅ |
| 8 | `git diff --name-only origin/main..HEAD -- config/` | **leer** | **0** | **leer** — keine Datei unter `config/` unterscheidet sich von `origin/main` | `gemessen` | ✅ |

**Aussage der Gegenproben:** Der Wellen-Branch `feat/repository-documentation-consolidation-main`
verändert gegenüber `origin/main` **weder** `scripts/lib/` **noch** `config/`. Das ist genau die
Aussage, die R3 für W1/W2 braucht (keine Kollision mit Track A). Beide Gegenproben sind
**Nachweis, nicht Freigabebedingung** — die Gate-Freigabe W1/W2 bleibt an den Kriterien (a)–(d)
gebunden und ist unverändert.
**Abgrenzung:** Diese Gegenproben prüfen **den Wellen-Branch gegen `origin/main`**. Sie sagen
**nichts** darüber, welche `scripts/lib/`-Dateien Track A zuletzt berührt hat; dafür bleibt die
in W0-4 zugesagte Liste (offener Punkt **OP-3** im W0-2-Record, §10).

## 4. Synchronitätskriterium — Befund `0 2` statt `0 0`

**Gemessener Wert:** `git rev-list --left-right --count origin/main...HEAD` → **`0 2`**
(links `0` Commits auf `origin/main` fehlen im Branch; rechts `2` eigene Commits darüber).
Bestätigt durch `git rev-list --count origin/main..HEAD` = `2` und
`git rev-list --count HEAD..origin/main` = `0`.

**Auslegung der Absicht.** Der Plan begründete das Kriterium wörtlich (Plan-Stand **vor**
Rev. 0.2) mit
*"damit der Gate-Record nicht über einen veralteten Stand entscheidet"*. Das Risiko, das
das Kriterium abdecken soll, ist ein **veralteter Prüfstand** — also Commits, die auf
`main` gelandet sind, während der Branch sie nicht enthält. Genau diese Zahl ist die
**linke** Spalte. Die rechte Spalte (eigene Commits des Branches) erzeugt **keinen**
veralteten Stand: Sie ist der normale, erwartete Zustand eines Feature-Branches, der
seine Spec/Plan-Arbeit trägt.

**Bewertung.** Das Kriterium `0 0` ist in diesem Zustand **nicht erfüllbar** und war es
auch nie: Es würde verlangen, dass der Branch **keine eigenen Commits** hat. Der Branch
trägt aber konstruktionsbedingt seine beiden Spec-/Plan-Commits (`80260cf4`, `95ac76df`)
— das ist der Auftragszustand selbst (Spec + Plan + Design als eigene Commits, `#839` mit
3 Dateien gegenüber `main`). `0 0` ist damit kein Messfehler, sondern ein im Kriterium
verankerter Denkfehler: es verwechselt „Branch ist aktuell" mit „Branch ist leer".

**Angewandtes Kriterium (fachlich korrekt):** **linke Zahl = 0** — der Branch liegt
**nicht hinter** `origin/main`. Gemessen: `0 2` → linke Zahl `0` → **erfüllt**.

**Korrekte Sollformulierung für den Plan** — **übernommen in Plan Rev. 0.2** (Nachführung
2026-09-26; die Formulierung unten entspricht der Task W0-4 im Plan in Rev. 0.2):

> Branch und `origin/main` müssen *nicht hintereinander* liegen:
> `git rev-list --left-right --count origin/main...HEAD` → **linke Zahl `0`**
> (rechte Zahl unbeschränkt, sie zählt die eigenen Spec-/Plan-Commits des Branches).
> Äquivalent und robuster: `git merge-base --is-ancestor origin/main HEAD` → Exit `0`.

## 5. Zwei weitere Plan-Text-Defekte (Kommandos, nicht der Zustand)

### 5.1 `git ls-tree -d` mit Pfadspec auf das Verzeichnis selbst liefert leer (Prüfung 2)

Der Plan verlangte in Akzeptanz (a) und Verifikation (Plan-Stand **vor** Rev. 0.2) einen Treffer
aus `git ls-tree -d origin/main -- tests/fixtures/slimming-golden/`. Dieses Kommando
liefert **Exit 0 mit leerer Ausgabe** — auch ohne das `--` nicht. Ursache: mit `-d` gibt
`ls-tree` nur Verzeichnis-*Einträge* aus; ein Pfadspec, der **auf** das Verzeichnis zeigt,
liefert den Eintrag selbst nicht. Der Eintrag wird nur beim Auflisten des **Eltern**
pfads sichtbar. Das Verzeichnis ist nachweislich in `main` — der Nachweis ist mit
`git ls-tree -d origin/main -- tests/fixtures/` (Tree `1b6a74e1`) und
`git cat-file -t` erbracht. **Der Zustand erfüllt (a); das Kommando ist falsch formuliert.**

> **Nachführung 2026-09-26 (Plan Rev. 0.2):** Der Plan hat die Kommando-Formulierung
> korrigiert — der hier beschriebene Defekt ist in Rev. 0.2 nicht mehr enthalten. Messung und
> Gate-Entscheidung dieses Records bleiben unverändert.

### 5.2 `ls` auf fehlende Datei liefert Exit 2, nicht 1 (Prüfung 5)

Der Plan erwartete `1` (Plan-Stand **vor** Rev. 0.2; der Plan nennt seither `2`). GNU `ls` beendet sich bei fehlendem Operanden mit
**2** — unabhängig vom Pfad verifiziert (`ls /nonexistent-path-xyz` → ebenfalls `2`).
Die inhaltliche Aussage „Datei existiert nicht" ist erfüllt; nur der erwartete
Exit-Code im Plan ist falsch. Robust prüfbar mit `test ! -e <pfad>` (Exit 0 = nicht vorhanden).

**Beide Defekte ändern die Gate-Entscheidung nicht** — sie betreffen die Formulierung der
Verifikation, nicht den geprüften Zustand.

## 6. Re-Baseline-Fix in `main` (FIX_IN_MAIN)

`git show origin/main:tests/fixtures/slimming-golden/effort-estimator.md | head -5`

```
---
name: effort-estimator
version: 1.4.0
description: Estimates effort for development tasks based on task type and LLM
  capabilities — with named assumptions, lead time and slack instead of a bare point value.
hint: Effort estimation for tasks — delegate here when the user asks about time/cost
```

Die Fixture in `origin/main` steht auf **`version: 1.4.0`** — der Re-Baseline-Fix ist in
`main` gelandet. Verteilung der Versionsstände über alle 58 Fixtures in `main`:
7× `1.4.0`, 7× `1.5.0`, 7× `1.6.0` und je 1–5× diverse weitere Stände (0.4.0–8.2.0);
`README.md` ohne `version:`-Feld. Versionsvielfalt ist erwartet (Golden Fixtures bilden
den Rollen-Stand zum Zeitpunkt der Erzeugung ab, nicht einen einheitlichen Wert).

**Zusatzbeleg:** Der Fixture-Baum ist in `origin/main` und `HEAD` **identisch**
(`git rev-parse` → beide `1b6a74e1ac10696404f4f829a17367f8d4012cc0`); `git diff --stat
origin/main -- tests/fixtures/slimming-golden/` ist leer. Es gibt also **keine** lokale
Fixture-Drift — der Arbeitsbaum entspricht exakt `main`.

## 7. Ausdrücklich kein Merge-Nachweis (wie im Plan festgehalten)

`git log --oneline -20 -- tests/fixtures/slimming-golden/` und
`git log --oneline -20 -- scripts/lib/` wurden **nicht** als Nachweis verwendet. Der
Merge-Nachweis ist ausschließlich der `git ls-tree`-Nachweis gegen `origin/main`
(plan:385-388). Zuletzt von Track A berührte `scripts/lib/`-Dateien sind in diesem
Gate **nicht** Gegenstand; die in der Task-Interfaces zugesagte Liste ist nicht Teil
dieses Records (offener Punkt **OP-3** im W0-2-Record §10).

**Abgrenzung zu den R3-Gegenproben (§3.1):** Die Gegenproben `git diff --name-only
origin/main..HEAD -- scripts/lib/` und `-- config/` prüfen, ob der **Wellen-Branch** gegen
`origin/main` etwas geändert hat — das ist die Aussage, die W1/W2 brauchen. Die in diesem
Abschnitt genannten `git log`-Kommandos beantworten eine **andere** Frage (welche Dateien hat
Track A zuletzt berührt) und sind kein Nachweis des Track-A-Merges. Beides bleibt unverändert:
§3.1 ist ergänzend, §1 (a)–(d) ist die Freigabegrundlage.

## 8. Rollback-Hinweis

Dieser Record ist **rein dokumentarisch** und hat keinerlei Code-, Fixture- oder
Pipeline-Wirkung. Ein Rollback besteht im Entfernen dieser Datei. Ein **Rebase ist vor
jedem Merge des Branches verpflichtend**, weil der Branch eigene Commits trägt: Vor dem
Merge `git fetch origin` ausführen, die linke Zahl von
`git rev-list --left-right --count origin/main...HEAD` erneut prüfen und bei `> 0` den
Branch auf `origin/main` aktualisieren. **Verfällt diese Freigabe**, sobald `origin/main`
weitere Commits erhält und der Branch nicht nachgezogen wurde, ist dieses Gate erneut
auszuführen.

## 9. Ausführungsprotokoll / Artefakte

**Wo die Belege liegen:** Die Rohoutputs der Messungen wurden **außerhalb des versionierten
Bereichs** abgelegt, in einem lokalen Arbeitsverzeichnis unter `.tmp/w0-4/` — `.tmp/` ist
**gitignoriert**. Sie sind damit **nicht Teil des PRs #839** und für PR-Reviewer **nicht
erreichbar**; es wird hier **nicht** behauptet, man könne sie nachprüfen. **Der tragende Nachweis
ist deshalb ausschließlich die oben inline tabellierte Kommando-/Ergebnis-Tabelle** (§1, §2, §3,
§3.1) — jede Zeile nennt Kommando, Erwartung, Exit und gekürzten Output und ist damit im PR
selbst lesbar. Die Artefaktliste ist nur ein **Hinweis auf den Erzeugungsort** (Vollständigkeit
der Protokollierung), kein Beleg im Review.

| Artefakt (lokal, nicht versioniert) | Inhalt |
|---|---|
| `.tmp/w0-4/gate-checks.txt` | Rohoutput der 6 Gate-Kommandos |
| `.tmp/w0-4/investigate.txt` | Pfad-Existenz, `ls`-Semantik |
| `.tmp/w0-4/lstree-variants.txt` | `ls-tree`-Varianten + Versionsnachweis |
| `.tmp/w0-4/crosscheck.txt` | Tree-Gleichheit, Versionsverteilung |
| `.tmp/w0-4/verify.txt` | Ausgangs-/Endverifikation des Laufs (Arbeitsbaum sauber, Branch-Stand, Zähler) |

**Hinweis zu den R3-Gegenproben (§3.1):** Für die beiden Diff-Gegenproben wurde **kein**
zusätzliches Artefakt abgelegt; ihr Ergebnis steht vollständig inline in der Tabelle §3.1.

**Ausführungsumgebung:** alle Kommandos read-only gegen das Repository; einzige
Netzoperation `git fetch origin` (Exit 0). Kein Commit, kein Push, kein Branch-Wechsel,
kein Merge/Rebase/Force, kein Stash, kein Checkout von `main`, **kein Löschen eines Branches**.
Geschrieben wurde ausschließlich dieser Record.

## 10. Offene Punkte

1. **~~Plan-Korrektur stand aus~~ — erledigt.** Dieser Record wurde geschrieben, als der
   Plan-Text in Task W0-4 noch `0 0` verlangte. **Nachführung 2026-09-26: Der Plan ist auf
   Rev. 0.2 korrigiert** und verlangt nun **linke Zahl `0`** bei
   `git rev-list --left-right --count origin/main...HEAD` (rechte Zahl unbeschränkt),
   gleichbedeutend `git merge-base --is-ancestor origin/main HEAD` → Exit `0`. Der in §4
   gemessene Wert `0 2` erfüllt diese Fassung; Bewertung, Gate-Entscheidung und Freigabe
   dieses Records bleiben unverändert.
2. **~~Zwei Verifikations-Kommandos im Plan waren falsch formuliert~~ — erledigt** (§5.1
   `-d`-Pfadspec, §5.2 `ls`-Exit-Code). **Nachführung 2026-09-26: Beide Formulierungsfehler
   sind in Plan Rev. 0.2 korrigiert.** Die Befunde dieses Records bleiben als Begründung
   dokumentiert; die Gate-Entscheidung ist unverändert.
3. **Bestätigung durch `main_chat`**, dass die Freigabe W1/W2 so akzeptiert wird, da sie
   auf dem fachlich korrigierten statt auf dem wörtlichen Kriterium beruht.
4. Die in W0-4 zugesagte **Liste der zuletzt von Track A berührten `scripts/lib/`-Dateien**
   ist in diesem Record bewusst nicht enthalten (plan:385-387 nimmt sie vom Nachweis aus);
   Klärung, ob sie als eigener Record zu führen ist. → geführt als **OP-3** im W0-2-Record §10.
5. **OP-1 (übernommen aus W0-2-Record Kapitel 7.1, Stand 2026-09-26) — Spec-Abweichung
   „ein Branch pro Welle":** **Spec §9.2 W0 und R16 verlangen weiterhin einen Branch pro
   Welle; umgesetzt ist ein Branch.** Korrektur der Spec (**Rev. 0.4**) ist **beauftragt, aber
   nicht ausgeführt** — sie erfordert ein **Concept-Review**. Bis dahin gilt die umgesetzte
   Strategie; der Widerspruch ist dokumentiert und **nicht verdeckt**. Für dieses Gate ohne
   Wirkung: die Freigabe W1/W2 hängt an den Kriterien (a)–(f), nicht an der Branch-Anzahl.
   Der überholte Branch `feat/repository-documentation-consolidation` bleibt auf
   Nutzer-Vorgabe („nicht löschen") erhalten und ist **kein** Gate-Kriterium.

