---
plan-id: PLAN-DOCS-CONSOLIDATION-2026-09-25
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
title: Repository-weite Doku-Konsolidierung agent-meta — Implementation Plan
status: APPROVED
revision: 0.5
pipeline_stages:
  implement: 3
related:
  - docs/specs/2026-09-25-repository-documentation-consolidation.md
  - docs/specs/2026-09-25-repository-documentation-consolidation-design.md
  - docs/plans/README.md
---

# Repository-weite Doku-Konsolidierung agent-meta — Implementation Plan

> Status: **APPROVED (2026-09-26)** — der Plan ist **genehmigt**; die Ausführung ist
> freigegeben. Grundlage: die Spec `SPEC-DOCS-CONSOLIDATION-2026-09-25` trägt seit 2026-09-26
> `status: APPROVED` (`docs/specs/2026-09-25-repository-documentation-consolidation.md:4`,
> Freigabevermerk im Spec-Kopf). Das Wertepaket des Plan-Templates
> (`geplant | IN PROGRESS | complete`) kennt kein `Entwurf`; hier gilt die Gate-Sprache der
> Spec. **Kein** `APPROVED` wird erfunden — es liegt eine dokumentierte User-Freigabe vor.
>
> **Genehmigungsumfang:** Die Freigabe umfasst die **Ausführung dieses Plans** (W0–W8, 47
> Tasks) inklusive der im Plan mit Owner und Entscheidungsweg versehenen Entscheidungs-Points
> W0-1/W0-3/W0-6 (davon **OQ2/OQ6/OQ8 bereits entschieden** — Ergebnis-Records) und der noch
> offenen Entscheidungs-Tasks W0-7/W5-1/W8-1. Die **Checkboxen sind bewusst nicht abgehakt** — das
> Plan-Ledger bleibt offen, die Genehmigung betrifft den Plan, nicht den Fortschritt. Die
> Task-Checkboxen werden erst während der Ausführung gesetzt.
>
> **Offene Entscheidungen aus der Spec** (bleiben offen, Entscheidung liegt bei den
> jeweiligen Ownern): **OQ1, OQ3, OQ4, OQ9** (Spec §11.1). Durch den Nutzer am
> 2026-09-26 entschieden und damit geschlossen: **OQ2** (`llms.txt` = **Hybrid**),
> **OQ6** (`docs/INDEX.md` = **tracked**) und **OQ8** (Regenerierung deterministisch über
> **Sync/Validator**, kein Commit-Hook) — Spec §11.2. **Konsequenz für diesen Plan:** die auf
> OQ2/OQ6/OQ8 bezogenen Punkte (u. a. `docs/plans/2026-09-25-docs-consolidation-oq2.md` /
> `-oq6.md` / `-oq8.md`) sind **keine offenen Entscheidungs-Tasks mehr**; sie werden als
> **Ergebnis-Dokumentation** der getroffenen Entscheidung geführt, nicht als offene Frage.
> Die betroffenen Task-Beschreibungen (W0-1, W0-3, W0-6, W1-6, W3-6, W3-7) sind gegen diese
> Entscheidung **korrigiert** und bei Ausführungsbeginn nochmals abzugleichen.
>
> **Ablage:** aktiv in `docs/plans/`, nicht `archive/` — `docs/plans/README.md:3-7`. Archivierung
> erst nach `STATUS: done` (Merge manuell bestätigt, Skill `plan-ledger`).
>
> **System-Design (verbindliche Eingangsgrundlage):**
> `docs/specs/2026-09-25-repository-documentation-consolidation-design.md`
> (concept-architect, 2026-09-25; Trace-Anker
> `spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25`).
>
> **Änderungsnotiz — Rev. 0.5 (2026-09-26): K13–K17 — vier belegte Gate-/Ownership-Mängel
> korrigiert, Ausführungs-Ledger (Abschnitt L) mitgenommen.** Eingang sind die Befunde
> **B-1**, **B-2**, **B-4**, **B-5** und die Errata **E-11**, **E-14**, **E-15** aus dem
> Ausführungs-Ledger dieses Plans (Abschnitt L). Alle Belege sind am 2026-09-26 am Working
> Tree **neu gemessen**; die Auftragsprämisse „V1 emittiert ERROR" hat sich dabei als
> **falsch** erwiesen und wurde **nicht** übernommen (Nachmessung, Zitatform, im Spec
> §17.9.1 vollständig). **Rev. 0.4 und die Rev.-0.2/0.3-Blöcke bleiben wortgleich stehen**;
> Abschnitt L wird **mitgenommen** (additive Statuspflege, **keine** Löschung, **kein**
> Replace). `status: APPROVED` und das Datum 2026-09-26 bleiben **unverändert**. **Kein**
> Task-, Wellen-, AC-, IC-, NFA-, R- oder OQ-ID wurde geändert, **keine** Task neu angelegt,
> **keine** Entscheidung (OQ2/OQ6/OQ8) umgedreht, **kein** OP-1- oder OQ1-Abschluss
> (OQ1 bleibt **offen**). Katalog:
>
> - **K13 — W2-Gate auf reale V1-Registrierung/Severity umgestellt (B-2, E-11).** Die
>   Wellen-Verifikation **W2** verlangte `--strict` → **1**, „die **einzigen** Findings sind
>   `docs.no_manual_counts`-V1-WARNINGS". Dieser Zustand existiert **nicht** und hat **zwei**
>   belegte Ursachen: **(a)** V1 emittiert im Ist-Zustand **WARNING**, nicht ERROR —
>   `docs.py:359` wählt die Severity über `v1_strict`, das `docs-consolidation.checks.strict`
>   liest und bei Abwesenheit `False` liefert (`:314-326`); `.meta-config/project.yaml:398-399`
>   setzt unter `docs-consolidation:` **nur** `enabled: true`; **(b)** V1 ist im Runner
>   **nicht registriert** — `scripts/consistency-check.py:52-56` importiert nur
>   `check_readme_docs_index`, `check_sync_cli_docs`, `check_ui_help_mappings`, und
>   `tests/test_doc_facts.py:2403-2422` pindet die Nicht-Registrierung explizit. **Neu:**
>   zwei getrennte, beobachtbare Abnahmekriterien (Zustand nach **W2-1** vs. nach **W2-7**),
>   beide über `--json` + Zählung, mit exaktem Kommando und erwarteter
>   Findings-Menge. **RVW-12 (Review der Rev. 0.5):** das Kriterium ist der **Zählwert** in der
>   Kommandoausgabe, **nicht** ein Exit-Code. Grund: ein Kommando der Form
>   `consistency-check.py --json | python3 -c '…'` gibt den Exit-Code des **letzten**
>   Pipe-Segments zurück; `print_json_report` liefert `1 if errors else 0`
>   (`scripts/lib/consistency/report.py:99`, aufgerufen in
>   `scripts/consistency-check.py:268-269`), und ein `sys.exit(0)` im Zähl-Konsumenten
>   neutralisiert diesen Roh-Exit zusätzlich. Beide `--json`-Kommandos der Rev. 0.5 sind deshalb
>   **explizit `sys.exit`-frei** geschrieben; ausgewertet wird der **gedruckte Zählwert**.
>   Die bisherigen zwei `--strict`-Zeilen bleiben als **aufgehoben** sichtbar.
>   **Betroffen:** Wellenblock **W2 — Verifikation**, Task **W2-1** (LEDGER-Stand-Notiz).
> - **K14 — W3-`--strict`-Gate auf den Spec-Scope begrenzt (B-1).** Der W3-Block und die
>   W3-7-Akzeptanz machten aus dem **datei-bezogenen** Spec-Pflichtumfang (`scripts/lib/doc_*.py`
>   + `docs/INDEX.md`, Spec §10) ein **repo-globales** `--strict == 0`. Das ist unerreichbar:
>   `consistency-check.py:273-274` setzt Exit 1 bei **irgendeinem** `WARNING`, `report.py:75`
>   bei Errors, und die warnungs-emittierenden Bestandschecks decken `agents/1-generic`,
>   `agents/2-platform` und `commands/*` ab — Pfade, die **keine** Welle W1–W8 anfasst.
>   **Neu:** zwei getrennte Scopes — **(a)** §10-Scope (Datei-Filter über `--json`,
>   Erwartungswert `scope-findings: 0`) und **(b)** Doku-Scope (Filter auf `check`-Präfix
>   `docs.`) — plus die **getrennt ausgewiesene
>   Baseline** des repo-globalen `--strict` als **Altbestand mit Zählung + Kommando**.
>   **Zweite Korrekturrunde (RVW-1/RVW-12/RVW-14):** Kriterium (b) ist nicht mehr das Aggregat
>   `docs-findings: 0` (dauerhaft unerreichbar, siehe Katalog unten), sondern die
>   **check-spezifische Kriterientabelle `W-GATE-TABLE`**; Kriterium (a) ist eine **Dokuzeile
>   ohne Prüfkraft**; **beide** Kommandos werten einen **Zählwert**, keinen Exit-Code.
>   **Zusätzlich belegt:** §10s Datei-Scope erfasst die Doku-Checks **nicht** — V1 scannt
>   `README.md`, `llms.txt`, `ARCHITECTURE.md` (`docs.py:158`) — ein rein auf §10 bezogenes
>   Gate wäre deshalb ein **scheinbar grüner** Nachweis. Deshalb ist Kriterium (b) notwendig.
>   **Betroffen:** Wellenblock **W3 — Verifikation**, Task **W3-7** (Akzeptanz), Task **W3-4**
>   (Vorbedingung aus K16), Spec §10 (Präzisierung Rev. 0.5).
> - **K15 — `scripts/lib/consistency/report.py` erhält Ownership (B-5, E-15).** Die Datei
>   erschien in **keiner** `Files:`-Liste **irgendeiner** Task; `line`/`branch` sind
>   Instanzattribute statt Dataclass-Felder (`report.py:28-41`), und `print_json_report`
>   (`:78-97`) serialisiert nur fünf Felder — der `--json`-Output **verwirft** `line`/`branch`
>   (gesetzt in `docs.py:329-347`, dessen Docstring bereits auf W2-7 verweist). **Neu:**
>   Ownership bei **W2-7** (besitzt bereits Registrierung **und** Common-Gate) — `Files:`,
>   `Interfaces:`, Reihenfolge-/Abhängigkeitsmatrix, benanntes Abnahmekriterium
>   **F1-PROMOTION** und ein eigener Step. **Betroffen:** Task **W2-7**, Matrixzeile **W2-7**.
> - **K16 — Abdeckungslücke von Suppressionsregel 3 als benannte Aufgabe (B-4, E-14).** Regel 3
>   unterdrückt alle Zeilen in Fenced-Code-Blöcken (`docs.py:281-311`,
>   `_V1_FENCE_OPEN_RE` `:203`); die IC-05-Fundstellen **F2**, **F3-Site-2** und **F4** liegen
>   aber im Directory-Structure-Fence (`README.md:680` öffnet, `:737` schließt; Fundstellen
>   `:688`, `:690`, `:696`, `:734`). V1 kann sie weder finden noch als grün melden. **Neu:**
>   Umsetzung als **Schritt 4 der Task W2-1** (Owner `developer`, also **vor** W3-4), mit
>   Abnahmekriterium: AC-07/AC-08 bleiben grün
>   **und** die vier Fundstellen werden sichtbar (negativer Nachweis). **Reihenfolgebindung
>   W2-1 ↔ W3-4** explizit gemacht. **RVW-4 (Review der Rev. 0.5, korrigiert):** die Bindung ist
>   als **Kante `W2-1 → W3-4`** in der Reihenfolge-/Abhängigkeitsmatrix und in der Wellen-Tabelle
>   (Spalte „Abhängig von", W3) abgebildet — eine **Vorwärts**kante über die Wellengrenze, die
>   **keinen** Zyklus erzeugt (Nachweis im Absatz **Zyklenprüfung**). Die frühere Formulierung
>   „ohne neue Kante im Abhängigkeitsgraphen" mit der Begründung „eine Kante W3-4 → W2-1 wäre
>   eine Rückwärtskante" war in der **Kantenrichtung falsch**. **Betroffen:** Task **W2-1**
>   (`Interfaces:`, `Akzeptanz`, `Steps`), Task
>   **W3-4** (`Depends on`, `Vorbedingung`), Reihenfolge-/Abhängigkeitsmatrix (Zeile W3-4),
>   Wellen-Übersicht (W3-Zeile, PG-2-Diagramm), Spec §5.1.1 (Präzisierung Rev. 0.5).
> - **K17 — Anker und Zählungen nachgeführt (K12-Logik).** Die `plan:<Zeile>`-Verweise in
>   L-1…L-4 galten für den **Rev.-0.4-Zeilenstand**; sie sind jetzt ausdrücklich als
>   **historisch** markiert, alle neuen Verweise nutzen **Abschnitts-/Task-Anker**. Zählungen
>   (Stand nach der **zweiten** Korrekturrunde, RVW2-6): Checkboxen **188 → 190 → 194**
>   (2 neue Steps in Rev. 0.5: W2-1 Schritt 4, W2-7 Schritt 4; **4 weitere** in der zweiten
>   Korrekturrunde: W4-3 Schritt 4 = Abschluss-Sync-Lauf, W5-2 Schritt 4 = Abschluss-Sync-Lauf,
>   W8-4 Schritt 4 = V9-Obergrenze, W8-4 Schritt 5 = Abschluss-Sync-Lauf), gesetzt
>   **unverändert 40**, offen **148 → 150 → 154**; W2-1 **3/5**, W2-7 **0/5**, W4-3 **0/5**,
>   W5-2 **0/5**, W8-4 **0/6**. **Herleitung (RVW-8 korrigiert, in der dritten Korrekturrunde
>   fortgeschrieben — RVW-8/RVW2-6):** 42 Tasks mit je **4** Steps = 168, + W2-1 (5) + W2-7 (5)
>   + W4-3 (5) + W5-2 (5) = 188, + W8-4 (6) = **194**; gesetzt **40**; 40 + 154 = **194**
>   = 190 + 4. Gegenprobe über alle **47** Tasks: 42 × 4 + 4 × 5 + 1 × 6 = **194**.
>   **Grenze der Zählung (RVW2-6, ehrlich):** in dieser Revisionsrunde stand **kein Shell-Zugriff**
>   zur Verfügung — die Zahlen sind **hergeleitet**, **nicht gemessen**. Nachzumessen durch
>   `validator` (Zählung `^- \[x\]` und `^- \[ \]`); weicht der Ist-Zähler ab, ist die Herleitung
>   hier zu korrigieren, nicht die Task-Struktur.
>   Task-Anzahl je Welle und Welleninhalt **unverändert** (kein neuer Task). **Betroffen:**
>   Kopfnotiz Abschnitt **L**, **L-1**, **L-2**, **L-3**, **L-4**.
> - **Prämissenkorrektur (B-1/B-2 gemeinsame Wurzel).** Die Auftragsangabe „V1 emittiert ERROR
>   (nicht WARNING)" ist am Code **nicht gedeckt**; die Messung trägt **WARNING** und zusätzlich
>   „nicht registriert". Beide Ursachen sind oben mit Datei:Zeile belegt und in die
>   Abnahmekriterien eingearbeitet. **Konsequenz:** das W2-Gate ist **nicht** „repariert" durch
>   Umdeutung, sondern **neu** definiert; das W3-Gate wird **begrenzt**, nicht abgeschwächt.
> - **Grenze der Messung (offengelegt).** In dieser Revisionsrunde stand **kein Shell-Zugriff**
>   zur Verfügung. Alle Belege sind deshalb **Datei:Zeile-Zitate** am Working Tree, **keine**
>   Laufzeit-Ausgaben. **Nicht gemessen** und daher **nicht behauptet** sind: (a) die exakte
>   Anzahl der Findings des repo-globalen `--strict` (Baseline) — sie wird als
>   **zu messen** mit exaktem Kommando und Owner geführt; (b) die Exit-Codes der
> repo-globalen Läufe. **Nachzumessen** durch `developer` bzw. `validator` beim ersten
> W3-Lauf; das Ergebnis wird als **Baseline-Zahl** im Review-Protokoll festgehalten.
>
> **Review der Rev. 0.5 — `concept-reviewer`, 2026-09-26, `VERDICT: CHANGES_REQUESTED`,
> 15 Findings (RVW-1…RVW-15: 1 Blocker, 4 Major, 8 Minor, 2 Info). Diese Korrekturrunde ist
> **Teil derselben, noch unveränderten Korrekturrunde Rev. 0.5** — es ist **kein**
> Revisions-Bump: `revision` bleibt **0.5**, `status: APPROVED` und das Datum 2026-09-26
> bleiben unverändert. Die nachstehende Liste dokumentiert **additiv**, was je Finding geändert
> wurde; die K13–K17-Einträge oben bleiben stehen und sind nur dort korrigiert, wo der Review
> es verlangt (K13 → RVW-12, K17 → RVW-8, K16 → RVW-4).**
>
> **Autorisierung dieser Korrekturrunde (RVW-5b).** Der Auftraggeber hat am **2026-09-26**
> über ein A2A-Envelope (`main_chat` → `orchestrator` → `concept-architect`) genau die fünf
> Korrekturen **1–5** beauftragt — **(1)** W2-Gate, **(2)** W3-7-Gate-Scope,
> **(3)** `report.py`-Ownership, **(4)** Fenced-Code-Regel 3, **(5)** Anker/Zählungen — **und
> ausdrücklich die Beibehaltung von `status: APPROVED`** verlangt. Der Concept-Review dieser
> Korrekturrunde (dieser Block) hat **innerhalb** genau dieses beauftragten Umfangs
> nachgeschärft; **jenseits** davon wurde **keine** Pflicht installiert. Die Aussage
> „**keine** neue normative Pflicht" ist damit **nicht haltbar** und wird **ersetzt** — nicht
> nur präzisiert (siehe unten „Präzisierung der Normativitätsaussage").
>
> - **Präzisierung der Normativitätsaussage (RVW-5a).** „Keine neue normative Pflicht" war in
>   der Fassung vor diesem Review **nicht haltbar** und wird wie folgt präzisiert: Rev. 0.5
>   installiert **keine** Pflicht **außerhalb** des am 2026-09-26 beauftragten Korrekturumfangs.
>   **Innerhalb** dieses Umfangs ändert Rev. 0.5 very wohl Nachweisformen, und diese Änderungen
>   sind: **(i)** Aufhebung einer **geschriebenen** Nachweisform — das repo-globale
>   `--strict → 0` bzw. `consistency-check.py → 0` als Wellen-Nachweis (W2-Block, W3-Block,
>   W3-7-Akzeptanz, W4–W8-Wellenblöcke, DoD Punkt 2); **(ii)** Einführung **neuer**
>   Nachweisformen — die Zähl-Kommandos über `--json` (W2-GATE-V1, W-GATE) und die
>   **check-spezifische** Kriterientabelle **W-GATE-TABLE** mit Termin und Owner je V-Check;
>   **(iii)** Verlagerung der Aussage „null `docs.*`-Findings" von der **DoD-Ebene** auf die
>   **Wellenebene**, wo sie je V-Check terminierbar und erfüllbar ist; **(iv)** eine
>   **Ausführungsreihenfolge-Kante** W2-1 → W3-4 (K16/RVW-4); **(v)** die Eingrenzung von
>   Suppressionsregel 3 als benannte, terminierte Umsetzungspflicht (W2-1 Schritt 4);
>   **(vi)** die `report.py`-Ownership mit benanntem Abnahmekriterium (F1-PROMOTION).
>   **Unverändert** bleibt der normative **Pflichtumfang** der Spec §10 (`scripts/lib/doc_*.py`
>   + `docs/INDEX.md`), die Exit-Code-Semantik des Runners und der DoD-Punkt 2, dessen
>   `docs.*`-Aussage **inhaltlich unverändert** bleibt — nur ihre **Messform** wechselt.
> - **RVW-1 (Blocker) — `W3-GATE-DOCS` (Ziel `0 docs.*`-Findings) war bei W3-7 unerreichbar.**
>   Gemessen am Working Tree: `knowledge/wiki` enthält **10** Seiten mit `type: "Architecture"`
>   und **null** `derived-from:` ⇒ V7 (`check_wiki_staleness`, WARNING) ist bis **W5-3** rot;
>   `howto/setup/` und `howto/features/` existieren **nicht** (nur `howto/configs/`) ⇒ V3
>   (`check_internal_links`, ERROR) ist bis **W8-2** rot; `docs/INDEX.md` existiert **nicht** ⇒
>   V2 ist bis **W3-6** rot. Das Gate ist damit **dauerhaft** unerreichbar — auch ab W8-4
>   nicht, weil **V9** den Altbestand an Backups per Spezifikation **dauerhaft** als WARNING
>   meldet und nicht abräumt (FI-10, „kein Spec-Gegenstand"). **RVW2-4:** die in dieser Zeile
>   ursprünglich genannte Zahl „179" ist eine **Bestandsangabe**, im Working Tree **nicht
>   messbar** (gitignoriert) und **kein** Sollwert — die Aussage „V9 meldet dauerhaft" bleibt
>   davon **unberührt**. **Korrektur:** das Aggregat `docs-findings: 0` ist als
>   Wellen-Gate **ersetzt** durch die **check-spezifische Kriterientabelle `W-GATE-TABLE`**
>   (Wellenblock **W3 — Verifikation**) mit Erwartungswert, **Termin** und **Owner** je
>   V-Check; das Kommando `W-GATE` zählt **je `check`-Name** statt zu aggregieren. Vollständige
>   Kriterienmenge **je Welle** in derselben Tabelle. **Nicht** verschoben, sondern
>   **geschnitten**: der Wellenabschluss wird an dem gemessen, was in der Welle erreichbar ist,
>   und jeder Rest wird **namentlich** mit Termin und Owner geführt.
> - **RVW-2 (Major) — drei unerreichbare `consistency-check.py → 0`-Zeilen in W2.** Nach W2-7
>   sind V2, V3 und V6 als **ERROR** registriert (IC-05), und `print_report` gibt
>   `1 if errors else 0` (`scripts/lib/consistency/report.py:75`, aufgerufen in
>   `scripts/consistency-check.py:271`) ⇒ der rohe Runner ist **planmäßig rot**. Betroffen:
>   Wellenblock **W2 — Verifikation**, Task **W2-2** (`Verifikation`), Task **W2-3**
>   (`Verifikation`, die Klammer „nur WARNINGs" war **sachlich falsch** — V3 ist ERROR, und
>   W2-3 folgt auf W2-2), Task **W2-7** (`Verifikation`). **Korrektur:** alle drei Zeilen
>   bleiben als Historie sichtbar und sind **additiv** auf **W2-GATE-ERRORS** umgestellt
>   (Zähl-Kommando, Erwartungswert je V-Check, Termin, Owner). Der Zustand „roher Runner
>   Exit 0" wird erstmals als **Dokuzeile** mit dem **spätesten** Termin **W8-2** und Owner
>   `developer` geführt, nicht als W2-Kriterium.
> - **RVW-3 (Major) — W4–W8 behielten repo-globale `--strict → 0`-Zeilen; die Geltungsregel
>   hatte keine Wellenwirkung.** **Korrektur:** die **fünf Wellenblock**-Zeilen (W4, W5, W6, W7,
>   W8) sind additiv auf die Scope-Kriterien mit **Wellen-Delta** (Erwartungswert, Termin,
>   Owner je V-Check) umgestellt. Die **Task**-Verifikationen bleiben unter der Geltungsregel
>   („Task-Verifikation"), erhalten aber eine **ausdrückliche Wellenabschluss-Relevanz**:
>   eine Task-Zeile ist **für sich** kein Welle-Gate; verbindlich ist die Zeile der
>   Kriterientabelle zur Welle. Owner der Textpflege: `orchestrator` (**nicht** `validator` —
>   `validator` besitzt die Baseline-Messung), Termin **vor W6-1** (dann sind alle fünf
>   Wellenblock-Zeilen umgestellt) — die Textpflege **blockiert** keine Welle.
> - **RVW-4 (Major) — die Reihenfolgebindung aus K16 war nicht im DAG; die Zyklus-Begründung
>   war falsch.** W2 ‖ W3 laufen bewusst parallel, **aber** `W2-1 → W3-4` ist eine
>   **Vorwärts**kante über die Wellengrenze (W2 vor W3) und erzeugt **keinen** Zyklus; die
>   bisherige Behauptung „eine Kante W3-4 → W2-1 wäre eine Rückwärtskante" war **falsch** — sie
>   verwechselte die Kantenrichtung. **Korrektur:** die Matrixzeile **W3-4** führt jetzt
>   `Depends on: W3-3, W2-1`; die Wellen-Tabelle in der Welle-Übersicht führt für **W3** die
>   Spalte „Abhängig von" um **W2-1 (Schritt 4, K16)**; der Absatz **Zyklenprüfung** ist
>   korrigiert. **Keine neue Task-ID** — es ist **eine** zusätzliche Kante auf einen
>   existierenden Task. Der Graph wurde danach **verifiziert**: DAG, keine Zyklen, keine
>   Rückwärtskante (Nachweis im Wellenblock „Reihenfolge-/Abhängigkeitsmatrix").
> - **RVW-5 (Major) — siehe den Absatz „Präzisierung der Normativitätsaussage" oben.** Die
>   Revisionszeile des Rev.-0.5-Blocks und die Spec-Frontmatter sind entsprechend gefasst.
> - **RVW-6 (Minor) — Rev. 0.5 fehlte in der Revisions-Tabelle und im §15-Trace-Anker.** Beide
>   Stellen sind in der Spec nachgezogen (0.5-Zeile in §Revision, Rev.-0.5-Anker in §15).
> - **RVW-7 (Minor) — falscher Stellenverweis `§12.2 R4 (Hochstufungsreihenfolge)`.** R4 liegt
>   in **§12.1** (Design-Risiken) und enthält **keine** Aussage zur Reihenfolge; die
>   Reihenfolgebindung ist eine **Ausführungsreihenfolge-Vorbedingung** des Plans, kein
>   Bestandteil dieses Risikos. Verweis korrigiert (Spec-Kopf, Rev.-0.5-Block) und im
>   K16-Eintrag dieses Plans präzisiert.
> - **RVW-8 (Minor) — Zählherleitung im K17-Kopf ergab 148, L-1 korrekt 150.** K17-Kopf auf die
>   **L-1-Formel** umgestellt (35 × 4 + W2-7 (5) + 1 + 2 + 2 = 150; Gesamtformel
>   45 × 4 + 2 × 5 = 190; 40 + 150 = 190 = 188 + 2). Die **Gesamtzahlen** waren und sind
>   korrekt — nur die Herleitung war falsch.
> - **RVW-9 (Minor) — die Geltungsregel enumerierte falsch.** Sie nannte Task-Zeilen ohne
>   `--strict`-Zeile und ließ die Wellenblock-Zeilen von W5/W6/W7/W8 aus. Auf **Abschnittsanker**
>   umgestellt (K12-Logik) und an den **tatsächlichen** Zeilenbestand angeglichen.
> - **RVW-10 (Minor) — der Self-Review zitierte den von K13 widerlegten Zustand als Beispiel.**
>   Die Beispielzeile („W2 `--strict` = 1 wegen V1-WARNING") ist als **historisch (Rev. 0.4)**
>   markiert; die korrigierte Aussage steht unmittelbar darunter.
> - **RVW-11 (Minor) — W2-1 `Interfaces:` zitierte die unpräzisierte Suppressionsregel 3**, die
>   Akzeptanz aber verlangt ihre Eingrenzung. `Interfaces:` nennt jetzt die „in der durch
>   Rev. 0.5 eingegrenzten Fassung".
> - **RVW-12 (Minor) — K13 versprach ein Exit-Code-Kriterium, das das Kommando neutralisiert.**
>   Auf **Zählwert** umgestellt (siehe K13 oben). **Gilt für jedes neue `--json`-Kommando**:
>   W2-GATE-V1, W2-GATE-ERRORS und W-GATE sind **ohne** `sys.exit` geschrieben; ihr Exit-Code
>   ist **kein** Kriterium. Negativbeispiel bleibt das **historische** Kommando mit
>   `sys.exit(0)` am Roh-Exit in der Fassung **vor** diesem Review (Abschnittsanker: Wellenblock
>   **W2 — Verifikation**, W2-GATE-V1, Absatz „Zum Exit-Code dieses Kommandos") — RVW2-11: der
>   Zeilenanker `plan:1086-1089` ist **entfallen**, weil er auf den Rev.-0.4-Zeilenstand zeigte
>   und mit K12/K17 durch Abschnittsanker ersetzt ist; der Abschnitt benennt das Kommando jetzt
>   ausdrücklich als unzulässig.
> - **RVW-13 (Minor) — Global Constraints nannte die Rev.-0.4-Spec-Korrektur als nicht
>   ausgeführt, der Self-Review als erfolgt.** Der Absatz in **Global Constraints** ist als
>   **historisch (Stand Rev. 0.4)** markiert und verweist auf **Spec §17.6/§17.7**; maßgeblich
>   ist der Self-Review. **Der Status von OP-1 bleibt unangetastet offen.**
> - **RVW-14 (Info) — `W3-GATE-SCOPE` ist konstruktionsbedingt tautologisch.** Kein Check
>   meldet auf `docs/INDEX.md` oder `scripts/lib/doc_*.py`: V1 scannt `README.md`, `llms.txt`,
>   `ARCHITECTURE.md` (`docs.py:158`), V2 liest `docs/INDEX.md` **als Soll**, V4 liest
>   `README.md` als Soll, V6 liest die generierten Blöcke. Der Erwartungswert
>   `scope-findings: 0` ist damit **0 per Konstruktion** und wird als **Dokuzeile** geführt,
>   **nicht** als Prüfkriterium; die eigentliche Doku-Aussage trägt **W-GATE / W-GATE-TABLE**.
> - **RVW-15 (Info) — `v1-files` ⊆ `V1_SCAN_RELPATHS` kann konstruktionsbedingt nicht
>   fehlschlagen** (`docs.py:158` ist die einzige Quelle der Scan-Menge). Als **Dokuzeile**
>   geführt, **nicht** als Prüfkriterium; beweiskräftig für die Abdeckung ist der
>   Sichtbarkeitsnachweis aus K16 (W2-1 Schritt 4).
>
> **Dritte Korrekturrunde (Review-Runde 2) — Concept-Review vom 2026-09-26,
> `VERDICT: CHANGES_REQUESTED`,
> 14 Findings (RVW2-1…RVW2-14: 2 Blocker, 4 Major, 7 Minor, 1 Info).** **Kein Revisions-Bump** —
> dieselbe, noch unveränderte Korrekturrunde Rev. 0.5; `revision: 0.5`, `status: APPROVED` und das
> Datum 2026-09-26 bleiben unverändert. Vollständiger Abgleich: **Spec §17.9.4** (Tabelle
> RVW2-1…RVW2-14 + Normativitätstabelle Punkt **(vii)–(x)** + Entscheidungsvorlagen
> **E-1…E-4**). Kurzfassung:
>
> - **RVW2-1 (Blocker) — `docs-checks` war per Konstruktion unerreichbar.** Der Counter zählt
>   **befundliefernde** Checks, nicht registrierte; die Tabelle verlangte an denselben Stellen
>   `V4 = 0` und `V5 = 0`. Bei **W2-7** weist die Tabelle **fünf** befundliefernde Checks aus
>   (V1 ≥ 1, V2 rot, V3 rot, V6 rot, V7 rot) — gefordert waren **sieben**; bei **W8** weist sie
>   unter V1–V8 **null** aus (alle Erwartungswerte 0), V9 trägt nur bei vorhandenen und alten
>   Backups — gefordert waren **neun**. **Die Zahlen der zweiten Hälfte sind bewusst nicht
>   nachgerechnet**, weil sie von der V9-Messung abhängen. **Korrektur:** drei
>   getrennte Aussagen — Counter = **Dokuzeile ohne Sollwert**; **Präsenzregel** je Check mit
>   Erwartungswert ≠ 0; **Registrierungszahl** = **nicht messbar** aus dieser Quelle
>   (kein Registry-Dump im Runner), Nachweis über **W2-7 Schritt 1** (positiver Registrierungs-Pin).
>   **Ist-Zustand 2026-09-26: `docs-checks: 0`** (V1 nicht registriert; der einzige heute
>   `docs.`-tragende Check liefert 0 Findings). Der belegte V4-Name `docs.readme_index`
>   (`docs.py:118`) ist in der Tabelle korrigiert.
> - **RVW2-2 (Blocker) — `sync.py --validate → 0` war in W2…W8 unerreichbar.**
>   `_run_consistency_checks` (`cli_commands.py:975` → `:171-174`) zählt **alle** ERROR-Findings,
>   der Exit folgt bei `:1056`/`:1058-1059`; V2/V3/V6 sind ERROR. **Korrektur:** neue Regel
>   **`W-VALIDATE-ROT`** — planmäßig rot bis einschließlich **W8-2**, spätester Termin 0 **W8-4**,
>   Owner `validator`, Grundlage **Spec §6(b) / §10, Aufzählungspunkt `--validate`**. **Kein Sollwert abgesenkt, sondern
>   terminiert.** Alle sieben Wellenblock-Zeilen und neun Task-Zeilen sind darauf umgestellt.
> - **RVW2-3 (Major) — DoD Punkt 2 war in sich widersprüchlich.** „null `docs.*`-Findings über
>   alle neun" **und** V9 = 179 zugleich; der Klammerzusatz „V9 wird im Doku-Scope nicht
>   emittiert" war falsch (Filter `startswith("docs.")`, V9 trägt `docs.stale_backups`).
>   **Korrektur:** Neufassung „V1…V8 = 0, V9 geduldet (FI-10)", **markiert als
>   Entscheidungsvorlage an den Nutzer** (Spec §17.9.4 Punkt (vii)); substanziell spec-konform
>   (IC-05, FI-10) und damit **belegt, nicht erfunden**.
> - **RVW2-4 (Major) — V9 = 179 war unmesbar und maschinenlokal.** `.gitignore:13`/`:22`, im
>   Working Tree **eine** Datei; das Vorhaben erzeugt selbst neue Backups. **Korrektur:** **keine**
>   Zahl als Sollwert; **Bestandsaufnahme** `BACKUP-BASELINE` in W8-4 Schritt 1, **Obergrenze erst
>   danach** (Schritt 4), Ausnahme in der Verschlechterungsregel, DoD/Wellenblock/
>   Coverage-Matrix/Task-Akzeptanz nachgezogen.
> - **RVW2-5 (Major) — `test_v1_is_not_wired_into_the_runner_yet` (`tests/test_doc_facts.py:2403-2422`)
>   wurde von W2-7 zwingend rot, ohne dass eine Task ihn abräumte.** **Korrektur:** Zuordnung an
>   den **bestehenden** Task **W2-7** (Schritt 1, `Files:`, `Akzeptanz`, Matrix) — **keine** neue
>   Task-ID; der Pin wird **nicht gelöscht**, sondern durch einen **positiven** Registrierungs-Pin
>   ersetzt. AC-13/AC-38-Abhängigkeit geprüft und unverändert.
> - **RVW2-6 (Major) — die drei Abschluss-Sync-Läufe standen in keinem Step.** **Korrektur:** je
>   **eigener Step** in **W4-3** (Schritt 4), **W5-2** (Schritt 4) und **W8-4** (Schritt 5), ohne
>   neues Datei-`Ownership`; Aufnahme als **neue Nachweisform** in Spec §17.9.4 Punkt (viii);
>   Checkboxen **190 → 194**, offen **150 → 154** (Herleitung korrigiert und als **nicht gemessen**
>   gekennzeichnet).
> - **RVW2-7 (Minor) — W8-4 führte einen siebten Config-Key unter einem geschlossenen Block.**
>   **Korrektur:** Altersschwelle N als **Modulkonstante** (Muster `V1_SCAN_RELPATHS`,
>   `docs.py:158`); **kein** Config-Key, `Files:` entsprechend eingegrenzt. Beleg:
>   `config/project-config.schema.json:2421-2470`, IC-22, M-11.
> - **RVW2-8 (Minor) — `docs/guides/configs/project.yaml.example` ist keine `.md`.**
>   **Korrektur:** Fußnote ¹, W5-Block und W5-2-Zusatz auf den `.md`-Pfad korrigiert;
>   **neu festgestellt und ergänzt:** W5-1 legt `docs/plans/…-oq9.md` an ⇒ V2 rot **ab W5-1**.
>   OQ9-Wortlaut **ohne OQ9 zu entscheiden** präzisiert (`docs/guides/INDEX.md` existiert nicht —
>   gemeint ist die Zeile im generierten `docs/INDEX.md`, Abschnitt `## guides`).
> - **RVW2-9 (Minor) — der Leitsatz der Zyklenprüfung war widerlegt.** **Korrektur:** umgestellt auf
>   „keine Rückwärtskante; Vorwärts- und Querwellenkanten zulässig und **namentlich genannt**".
> - **RVW2-10 (Minor) — die LEDGER-Notiz an W2-1 nannte Schritt 4 „Commit".** **Korrektur:** auf
>   „Schritt 4 (K16-Regel-3-Eingrenzung) **und** Schritt 5 (Commit)" gezogen; deckt sich mit L-1.
> - **RVW2-11 (Minor) — Rev.-0.5-Text zitierte eigene historische Zeilenanker.** **Korrektur:**
>   `plan:1086-1089`, `plan:1058/1235/1329`, `plan:924-940` durch Abschnitts-/Task-Anker ersetzt;
>   Geltungsbereich der K17-Regel auf Task-Notizen und Rev.-0.5-Text erweitert; **Rev.-0.4-Text in
>   L-2/L-3/L-4 bleibt wortgleich** und ist als überholt qualifiziert.
> - **RVW2-12 (Minor) — die Aufhebung des `--strict` ruhte auf einer ungemessenen Prämisse.**
>   **Korrektur:** „rund 19" als **Schätzung, nicht gemessen** markiert (auch in L-2/B-1);
>   **Rückfallregel** in **W3-BASELINE-STRICT** — `errors: 0` **und** `warnings: 0` ⇒ `--strict → 0`
>   ist für W4…W8 **wieder** maßgeblich, Aufhebung annullieren, Owner `validator`, Punkt **W3-7**.
> - **RVW2-13 (Minor) — `--check` wurde zu Unrecht auf V1/V2/V6 zurückgeführt.** **Korrektur:**
>   `--check` ist der **Drift-Lauf** (`sync_pipeline.py:914`; `_run_consistency_checks` wird nur von
>   `_handle_validate` aufgerufen, `cli_commands.py:975`); alle betroffenen Zeilen tragen jetzt
>   „Drift-Lauf, **kein** Consistency-Nachweis". Die Präzisierung des `--check`-Halbsatzes in
>   **Spec §6(b)** ist als **Entscheidungsvorlage E-3** eskaliert, nicht eigenmächtig geändert.
> - **RVW2-14 (Info) — Fußnote ³ war zeitgebunden formuliert.** **Korrektur:** „zum Planungszeitpunkt
>   nicht messbar; **ab dem ersten W2-7-Lauf** messbar".
>
> **Unverändert in dieser Runde:** `status: APPROVED`, `revision: 0.5`, Datum 2026-09-26, alle
> Task-/Wellen-/AC-/IC-/NFA-/R-/OQ-/NG-/FI-/M-IDs, OQ1 **offen**, OQ2/OQ6/OQ8 **geschlossen**,
> OP-1 **unberührt**, die Rev.-0.2/0.3/0.4-Blöcke, B-1…B-5 und E-01…E-15, **keine** neue Task-ID,
> **kein** Produktionscode.
>
> **Vierte Korrekturrunde (Review-Runde 3) — Concept-Review vom 2026-09-26,
> `VERDICT: CHANGES_REQUESTED`, 10 Findings (RVW3-1…RVW3-10: 0 Blocker, 6 Major, 4 Minor).**
> **Kein Revisions-Bump** — dieselbe Korrekturrunde Rev. 0.5; `revision: 0.5`, `status: APPROVED`
> und das Datum 2026-09-26 bleiben unverändert. **Gehebe: ausschließlich Korrektur** falscher
> Sollwert-Formulierungen, Widersprüche, Step-/Zeilenanker und Selbstverweise — **keine** neue
> Gate-Form, **kein** neues Kommando, **kein** neuer Sollwert, **keine** neue Task-ID, **keine**
> neue Ausführungspflicht. Vollständiger Abgleich: **Spec §17.9.4**, Behandlungstabelle
> RVW3-1…RVW3-10. Kurzfassung:
>
> - **RVW3-1 (Major) — `W-VALIDATE-ROT`, Zeile „W8-2 … W8-4", nannte „kein Doku-ERROR-Check".**
>   **Korrektur:** Spalte auf **V2** (W8-1 legt `…-oq4.md` an, bearbeitet `docs/REQUIREMENTS.md`;
>   W8-2/W8-3 führen keinen Sync), Termin **W8-4 Schritt 5**, Owner `tester`; Lesehinweis ergänzt,
>   damit `--validate` im Endintervall nicht als grün gelesen wird. Ergänzend: die Zwischenzeile
>   „W3-7 … W8-1" nennt jetzt auch die erneute V2-Rotheit in W4/W5.
> - **RVW3-2 (Major) — W5-2 Schritt 4 wertete „V7 0" der W5-Spalte aus** (V7 wird 0 erst in
>   W5-3). **Korrektur:** Zwischenzustand ausgewiesen („V7 planmäßig rot, Termin **W5-3**") —
>   dieselbe Form, die W4-3 Schritt 4 für die W4-Spalte bereits verwendet. **Keine** neue Regel.
> - **RVW3-3 (Major) — die Begründung der vorläufigen E-1-Anwendung war falsch („strenger").**
>   **Korrektur** in DoD Punkt 2 und Spec §17.9.4 (vii): (a) ist die **einzige Lesart, die den
>   Vorhabensabschluss nicht dauerhaft unerreichbar macht**, und wird **vorläufig** angewendet, bis
>   E-1 entschieden ist; ausdrücklich als die **schwächere** Lesart gegenüber (b) ausgewiesen.
> - **RVW3-4 (Major) — „drei Entscheidungsvorlagen" gegen „vier".** **Korrektur:** alle vier Stellen
>   in der Spec auf **vier … E-1…E-4** gezogen (Frontmatter `approved-scope`, Kopfblock, §17.9.3,
>   §17.9.4-Einleitung).
> - **RVW3-5 (Major) — drei Vorlagen ohne Frist; zwei Verweise auf ein nicht existierendes
>   „Übergabeprotokoll".** **Korrektur:** Spalte **Frist** in der E-Tabelle der Spec (E-1 vor
>   Vorhabensabschluss, E-2 vor W8-4 Schritt 1 als **voraussetzungsstiftende** Frist, E-3/E-4 vor
>   W3-7); beide Plan-Selbstverweise (W3-Block, W8-4 `Interfaces:`) auf **Spec §17.9.4,
>   Entscheidungsvorlage E-x** umgestellt.
> - **RVW3-6 (Major) — W8-4 Schritt 4 ließ die ausführende Task die APPROVED-Spec ändern.**
>   **Korrektur:** der Spec-Nachtrag ist **gestrichen**; die Obergrenze bleibt **Plan-Protokoll**
>   (`V9-OBERGRENZE` im W8-4-Review-Protokoll). Step 4, Absatz „Bestandsaufnahme", IC-05-Hinweis
>   und §17.9.4 (x) sind darauf gezogen. **Kein** neuer Freigabeweg, die Spec bleibt unverändert.
> - **RVW3-7 (Minor) — falsche Step-Nummer in W4-3 Schritt 3 („Schritt 5").** **Korrektur:**
>   „Schritt 4" (der Abschluss-Sync; Schritt 5 ist der Commit). **Alle** Step-Verweise in
>   W4-3/W5-2/W8-4 wurden gegen ihre Step-Listen geprüft — **keine** weitere Off-by-one-Stelle.
> - **RVW3-8 (Minor) — W3-6 fiel in keine Zeile des `W-VALIDATE-ROT`-Rasters.** **Korrektur:**
>   Zeile 1 auf „W2-7 … W3-6" verlängert.
> - **RVW3-9 (Minor) — zwei Nummerierungssysteme unter „§10 Punkt n".** **Korrektur:** im Plan
>   durchgehend benannte Anker („§6(b) / §10, Aufzählungspunkt `--validate`"); dieselbe
>   Umstellung in der Spec. Historische Behandlungstabellen der Runden 1/2 bleiben wortgleich.
> - **RVW3-10 (Minor) — die Revisionszeile nannte „§16 (Tabellenumfang)".** **Korrektur:**
>   Nennung **gestrichen**; §16 bleibt der dokumentierte Rev.-0.3-Stand (ohne Diff nicht
>   belegbar, deshalb nicht behauptet).
>
> **Als OFFEN gekennzeichnet, nicht ausgeführt (Pflichtprüfung dieser Runde):** die
> **`W3-BASELINE-STRICT`-Textpflicht in W4 und W5** (Rückfallregel, Owner `orchestrator`, Termin
> vor W6-1) steht **nicht** in der Normativitätstabelle Spec §17.9.4 und geht über den beauftragten
> Korrekturumfang hinaus. Der Text bleibt unverändert stehen, wird aber **nicht** als beschlossen
> und **nicht** als vom Auftrag gedeckt geführt (Prüfvermerk in Spec §17.9.4 unmittelbar nach der
> Normativitätstabelle; Plan-Vermerk bei `W3-BASELINE-STRICT` (b) und in der Geltungsregel). Die
> drei **Abschluss-Sync-Läufe** (W4-3/4, W5-2/4, W8-4/5) sind in Spec §17.9.4 **(viii) namentlich
> geführt** — als neue Nachweisform **deklariert**; die Deklaration ist die Grenze der
> Autorisierung, nicht deren Aufhebung.
>
> **Zählung unverändert:** **194** Checkboxen gesamt, **40** gesetzt, **154** offen (47 Tasks; in
> dieser Runde wurde **keine** Checkbox ergänzt, entfernt oder gesetzt). **E-1…E-4 bleiben
> unentschieden** und liegen beim Auftraggeber; OQ1 **offen**, OQ2/OQ6/OQ8 **geschlossen**, OP-1
> **unberührt**, B-1…B-5 und E-01…E-15 unverändert, **kein** Produktionscode.


> **Änderungsnotiz — Rev. 0.4 (2026-09-26): K12 nachgezogen, dazu belegte Faktenkorrekturen
> aus der Commit-Blocker-Prüfung — keine Neuerfindung.** Der Rev.-0.3-Block ist **inhaltlich
> unverändert**; K12 war dort nachträglich eingetragen und ist mit dem Revisions-Bump in diesen
> Block verschoben (wortgleich, nur die Falschangabe zur Zeilenzahl korrigiert). Rev. 0.4
> enthält **ausschließlich** belegte Korrekturen von Zahlen- und Tatsachenaussagen — **keine**
> inhaltliche Änderung. **Betroffene Stellen:** K12 (dieser Block), System-Design-Notiz,
> **Spec:**-Kopf, Self-Review „Offener Punkt OP-1". **Kein** Task-, Wellen-, AC-, IC-, NFA-,
> Risiko-, Entscheidungs- (OQ2/OQ6/OQ8) oder Gate-Inhalt (W1/W2) geändert, **keine** neue ID.
> Katalog:
>
> - **K12 (aus dem Rev.-0.3-Block hierher verschoben)** — die drei numerischen
>   `Spec:<Zeile>`-Anker dieses Plans wurden durch **Abschnittsanker** ersetzt, weil die Spec
>   zwischen Rev. 0.3 und Rev. 0.4 **net +232 Zeilen** gewachsen ist (gemessen am 2026-09-26
>   gegen Basis `35bb176f`: **2051** Zeilen → **2283** Zeilen, `git diff --numstat` 258/26) und
>   damit alle drei Anker sofort veraltet waren: (a) `Spec:62-66` (Klassifikation) →
>   Spec-Statuskopf, Abschnitt „Klassifikation (Master-Rule `spec-plan-workflow`)"; (b) `Spec:1105`
>   (Sollwertzahl elf) → Spec §5.5, IC-23; (c) `Spec:907` (R18) → Spec §5.2 IC-16 (M8-Tabelle)
>   bzw. §12.2 R18. Zusätzlich entfällt die Zeilenangabe „2015 Zeilen im Rev.-0.3-Stand" im
>   **Spec:**-Kopf dieses Plans — eine Zeilenzahl eines Vorstands ist driftanfällig und ohne
>   Aussagewert. **Kein** Task-, Wellen-, AC-, IC-, NFA- oder Gate-Inhalt geändert.
> - **Zeilenzahl „+133" → „+232" (Plan, zwei Stellen).** Der Zuwachs der Spec wurde mit **133**
>   Zeilen angegeben; gemessen sind es **net +232** (2051 → 2283, `git diff --numstat` 258/26,
>   Basis `35bb176f`). Betroffen: K12 oben und der **Spec:**-Kopf dieses Plans.
> - **Driftanfällige Design-Zeilenzahl entfernt (Plan + Spec).** Die Notiz „System-Design
>   (verbindliche Eingangsgrundlage)" nannte eine Zeilenzahl des Designs („397 Zeilen"). Sie ist
>   **entfallen** — dieselbe Begründung wie bei K12: eine Zeilenzahl eines fremden Dokuments ist
>   driftanfällig und ohne Aussagewert; die Design-**Entscheidungen** (T-1…T-6) und Komponenten
>   (C1…C8) bleiben unverändert genannt. Die gleiche Angabe ist auch im Spec-Kopf entfernt.
> - **Überholte Aussage im Self-Review (offener Punkt OP-1, Plan).** „Ausgeführt: nein" — das
>   Concept-Review hat nicht stattgefunden" war überholt: das Concept-Review **ist erfolgt**
>   (2026-09-26, `VERDICT: BLOCKED`, Befund **F-1**), die Spec-Rev. 0.4 ist am 2026-09-26 durch den
>   Nutzer bestätigt (Spec §17.6/§17.7). Korrigiert auf diesen Stand; der **formale Abschluss von
>   OP-1 in Plan und W0-Records** bleibt ein **Folgeschritt** mit exaktem Änderungsauftrag in Spec
>   §17.6/§17.7 — er ist **nicht** Teil dieser Revision.
> - **Ownership-Aussage in §16 präzisiert (Spec).** „Plan, Design und die sechs W0-Records wurden
>   gelesen, nicht geändert" war im Working Tree unzutreffend (der Plan wurde in diesem Durchgang
>   geändert); korrigiert auf den tatsächlichen Umfang.
> - **Normativitätsstellen-Zahl: zwei → drei (Spec).** Kopfblock, Revisionszeile 0.4 und §17.6
>   nannten „**zwei** Normativitätsstellen"; Rev. 0.4 hat **drei** korrigiert (§9.2 W0-Zeile,
>   §9.2-Absatz „PR-/Branch-Kollision", §12.2 R16-Mitigation).
> - **OP1-2/OP1-3 konsistent zugeordnet (Spec).** Revisionszeile und §17.6 widersprachen sich in
>   der Reihenfolge; die Zuordnung ist jetzt in beiden Tabellen identisch und folgt der
>   Dokumentreihenfolge (§9.2 vor §12.2).
> - **Beleg W4/W5/W6-Parallelität vervollständigt (Spec).** §9.2, §13 A14, §17.6 und §17.8 belegten
>   mit `design:269-271`; `design:275` führt W5 zusätzlich als gleichzeitig ausführbar mit
>   W2 ‖ W3 („W2 ‖ W3 ‖ W5") und ist nun mitzitiert.
>
> **Änderungsnotiz — Rev. 0.3 (2026-09-26): Korrekturen K7–K10 aus dem Review der W0-Records.**
> Diese Revision korrigiert ausschließlich **Verifikations-Kommandos, Erwartungswerte und
> Formulierungen**, die das W0-Review an Plan und Records als falsch belegt hat. **Kein**
> Task-, Wellen-, AC-, IC- oder NFA-ID wurde geändert, **keine** Entscheidung (OQ2/OQ6/OQ8),
> **keine** Gate-Freigabe (W1/W2) und **keine** W0-Akzeptanz wurde angetastet. Betroffene
> Stellen: Global Constraints (Commit-Konvention, Spec-Abweichung), W0-Wellenverifikation,
> Task **W0-2**, Task **W0-4**, Self-Review. Katalog:
>
> - **K7** — W0-Verifikation: `git log --oneline -20 -- scripts/lib/` → **0** war unerfüllbar
>   und sinnlos (es zählt die 20 letzten Commits des Branch, nicht eine W0-Berührung).
>   Umgestellt auf `git log --oneline origin/main..HEAD -- scripts/lib/` → **0** — **gemessen 0**
>   am 2026-09-26. Dieselbe Begründungslogik wie K1: abgedeckt wird ein *veralteter Prüfstand*,
>   nicht die Existenz von Historie.
> - **K8** — Commit-Titel-Konvention: der `W<N>`-**Präfix** ist verbindlich für den
>   Wellen-Abschluss-Commit und für Commit-Titel, die Wellen koordinieren; für einzelne
>   Datei-Commits **innerhalb** einer Welle ist er **optional**, dann trägt der **Body** die
>   Task-ID. Bisherige Formulierung kollidierte mit den 47 Step-4-Commit-Messages, von denen
>   **0** den `W`-Präfix tragen.
> - **K9** — Branch-Prüfung: `git branch --list 'feat/repository-documentation-consolidation*'`
>   ist ein **Präfix**-Match und liefert **2** Zeilen, nicht eine. Umgestellt auf eine
>   Existenzprüfung mit **exaktem Namen**; der überholte Zweit-Branch wird als *dokumentierter
>   Bestand* geführt (Nutzer-Vorgabe „nicht löschen"), nicht als Prüffehler.
> - **K10** — W0-4: die Nachweispflicht aus **R3** umfasst `tests/fixtures/` **und**
>   `scripts/lib/` **und** `config/`; die beiden letzten Flächen sind jetzt ausdrücklich der
>   W0-4-Welle zugeordnet und in der Verifikation genannt.
> - **K1 (bereits in Rev. 0.2 als Ausführungskorrektur markiert; das Review vertieft sie zum
>   offenen Punkt)** — die Spec verlangt in §9.2 W0 und R16 weiterhin „ein Branch pro
>   Welle". Eine Spec-Änderung (Rev. 0.4) ist **beauftragt, aber nicht ausgeführt** — sie
>   erfordert ein Concept-Review. Der Widerspruch ist in Plan und Records sichtbar geführt
>   (offener Punkt **OP-1**), nicht verdeckt.
> - **K11** — ein Formfehler im Verifikationstext von W0-4 wurde behoben (unbalanciertes
>   Backtick/Bold in `1`/`**1**`).
>
> **Änderungsnotiz — Rev. 0.2 (2026-09-26): Ausführungskorrekturen K1–K6, keine Neuerfindung.**
> Diese Revision korrigiert **ausschließlich Kommandos, Exit-Code-Erwartungen und die
> Branch-Strategie** an den Stellen, an denen die Ausführung von **W0-2** und **W0-4** die
> Plan-Vorgabe empirisch widerlegt hat. Quelle sind die beiden Ergebnis-Records der W0:
> `docs/plans/2026-09-25-docs-consolidation-track-a-gate.md` (W0-4, §4–§5) und
> `docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md` (W0-2, Kapitel 7–8). **Kein**
> Task-, Wellen-, AC-, IC- oder NFA-ID wurde geändert, **keine** Gate- oder Aufgaben-Semantik
> verschoben, **keine** neue Anforderung erfunden. Betroffene Stellen: Global Constraints
> („Ein Branch pro Welle"), W0-Wellenverifikation, Task **W0-2**, Task **W0-4**, Risiko **R16**,
> DoD-Punkt 14, Self-Review. Die inhaltliche Gate-Aussage von W0-4 (Fixture-Verzeichnis in `main`
> vorhanden, `docs_v1_fixtures.md` nicht vorhanden) bleibt **unverändert**.

**Goal:** Die 11 nachweislich falschen Handzahlen der Einstiegs-Doku (F1–F4, F14 ×3, F22 ×2,
`ARCHITECTURE.md:3`) durch berechnete `DOCS_*`-Fakten ersetzen, den bereits spezifizierten,
unerfüllten `docs/INDEX.md`-Vertrag aus `scripts/lib/spec_plan_scaffold.py:23` erfüllen, die
mehrfach geführten Spec/Plan- und Guide-Bäume konsolidieren und die Wiki-Staleness maschinell
machen — ohne Inhalts-Rewrite bestehender Doku.

**Architecture:** Vier abgeschlossene Module (Spec §4): M1 `doc_facts.py` (stdlib-Blatt, reine
Faktenberechnung) → M2 `doc_renderer.py` / `doc_index.py` / Snippet-Bridge / Pipeline-Stage
(Writer) → M3 reine Migration (`git mv`, keine neue Code-Datei) → M4
`knowledge.py::sync_wiki_index` (Schwester-Modul zu M2, importiert M1 **nicht**).
Schichtungs-Invariante `scripts/lib/variables.py:9-17` — keine Zyklen. Absenz-Defaults sind
**fail-off** für Writer **und** Checks (Präzedenz `scripts/lib/knowledge.py:127`).

**Tech Stack:** Python 3, **nur Stdlib** (NFA-07) + `scripts/lib`-Module, pytest, Markdown/YAML/JSON,
`scripts/sync.py`, `scripts/consistency-check.py`, Bash (`tests/scenarios/run.sh`).

**Spec:** `docs/specs/2026-09-25-repository-documentation-consolidation.md`
(`spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25`, Rev. 0.5, `status: APPROVED` (2026-09-26)).
**Keine Zeilenangabe:** eine Zeilenzahl der Spec ist per Definition driftanfällig — die Spec ist in
dieser Sitzung mehrfach gewachsen (Rev. 0.4: **net +232 Zeilen** gegenüber Rev. 0.3; gemessen am
2026-09-26 gegen die Basis `35bb176f`: **2051** Zeilen → **2283** Zeilen,
`git diff --numstat` 258/26), wodurch drei
numerische `Spec:<Zeile>`-Anker dieses Plans (Klassifikation, IC-23-Sollwertzahl, R18) bereits beim
Schreiben dieses Plans veraltet waren. Sie sind deshalb **Abschnittsanker** (Stand 2026-09-26).
Klassifikation **XL / Architectural** (Spec: Statuskopf, Abschnitt „Klassifikation
(Master-Rule `spec-plan-workflow`)").

## Global Constraints

- **Ausführung freigegeben (2026-09-26).** Das Gate ist erfüllt: die Spec trägt
  `Status: APPROVED` (Freigabe 2026-09-26), dieser Plan trägt `Status: APPROVED (2026-09-26)`.
  Kein Task startet **vor** der Bestätigung, dass **W0-4** (Track-A-Merge-Status) grün ist —
  **W0-4 ist das Track-A-Gate** und sperrt W1 und W2; W0-2 ist der Design-Freeze und **kein**
  Gate. Dieser Plan ist ab der Freigabe ein **Startsignal**; die
  Task-Checkboxen sind zum Freigabezeitpunkt **bewusst alle offen** (Ledger-Start).
- **Datei-Ownership:** Jede Datei wird in genau **einer** Task geschrieben. `Files:` ist der Input
  für `check_plan_file_overlap` (`scripts/lib/orchestration.py`) und die Barrieren-Gruppen.
  **Lesen ist kein Ownership** — W2 liest `README.md`, ohne es zu besitzen.
- **Ein Wellen-Branch statt acht Wellen-Branches (Ausführungskorrektur 2026-09-26, Quelle:
   empirische Messung in W0-2/W0-4 — Abweichung zu Spec §9.2 W0 und R16, **begründet
   dokumentiert** in W0-2-Record Kapitel 7, nicht stillschweigend erfüllt):** Es gilt **ein**
   Feature-Branch `feat/repository-documentation-consolidation-main` (Basis `origin/main`) mit
   **einem** PR. Die Wellen W0→W8 laufen als **sequenzielle Commits** auf diesem Branch; die
   Wellen-Zuordnung trägt die **Wellenkennung im Commit-Titel** (`docs(docs-consolidation): W<N>
   <Zweck>`) und einen **Abschluss-Commit** `docs(docs-consolidation): W<N> complete` je grüner
   Welle. **Ein Commit pro Datei**, Rebase gegen `origin/main` vor dem Merge. Begründung:
   (1) die Nutzer-Vorgabe (ein Branch, ein PR) hat Vorrang; (2) acht Branches erzeugen acht
   Merge-Kernel und acht Review-Zyklen **ohne Erkenntnisgewinn**, da die Wellen ohnehin sequenziell
   und teilweise nicht parallel ausführbar sind (Spec §9.2); (3) der **R16-Intent** wird weiterhin
   über die Reihenfolge-Regel und die Merge-Regel „`git mv`-Wellen zuerst" abgedeckt, nicht über die
   Branch-Anzahl. **Kein** `chore/docs-consolidation-w<N>` wird angelegt.
  > **Spec-Abweichung (Zeilenstand Rev. 0.4 — HISTORISCH, RVW-13; maßgeblich ist der
  > Self-Review-Absatz dieses Plans):** **Spec §9.2 W0 und R16 verlangten weiterhin einen
  > Branch pro Welle** (`chore/docs-consolidation-w<N>`, gestapelte PRs); **umgesetzt ist ein
  > Branch**. Die Korrektur der Spec (Rev. 0.4) war zu diesem Zeitpunkt **beauftragt, aber
  > nicht ausgeführt** — sie erforderte ein Concept-Review, das **damals noch nicht**
  > stattgefunden hatte. **Stand 2026-09-26 (Rev. 0.5):** das Concept-Review **ist erfolgt**
  > (`VERDICT: BLOCKED`, Befund **F-1**), und **Rev. 0.4 ist am 2026-09-26 durch den Nutzer
  > bestätigt** — **Spec §17.6** (Korrektur und Belege) und **§17.7** (Freigabe-Auflösung). Die
  > Aussage „nicht ausgeführt" ist damit **überholt** und bleibt hier **nur als historischer
  > Zeilenstand des Rev.-0.4-Plan-Standes** stehen; maßgeblich ist der Self-Review-Absatz
  > („Offener Punkt OP-1"). **Der Status von OP-1 bleibt davon unberührt offen** — offen ist
  > ausschließlich der **formale Abschluss** in Plan und W0-Records, Owner `orchestrator`.
  > Der Widerspruch zwischen der normativen Quelle (Spec) und der Ausführung bleibt
  > dokumentiert und wird **nicht verdeckt**; geführt als offener Punkt
  > **OP-1** in W0-2-Record, Track-A-Gate-Record und Self-Review dieses Plans.
- **Commit-Titel-Konvention — Wo-wellenzugeordnet wird (Präzisierung 2026-09-26, K8):** Der
  `W<N>`-**Präfix** ist **verbindlich** für (a) den **Wellen-Abschluss-Commit**
  `docs(docs-consolidation): W<N> complete` und (b) jeden Commit-Titel, der **Wellen
  koordiniert** (z. B. Wellen-Übergang, Reihenfolge-/Merge-Entscheidung, Wellen-Sammelstand).
  Für **einzelne Datei-Commits innerhalb** einer Welle (Plan R3, „ein Commit pro Datei") ist
  der Präfix **optional**; der Titel folgt dann der Repo-Commit-Konvention
  (`docs(docs-consolidation): <Zweck>`) und der **Commit-Body führt zwingend die Task-ID**
  (`Task: W<N>-<k>`). Diese Präzisierung löst einen Kollisionsfehler der Fassung Rev. 0.2: sie
  machte den `W<N>`-Präfix für **alle** Commits einer Welle verpflichtend, während **0 von 47**
  der im Plan festgeschriebenen Step-4-Commit-Messages ihn tragen — die Konvention wäre ohne
  Umschreiben dieser 47 Stellen nicht erfüllbar gewesen. **Wellenzuordnung** ist damit
  garantiert: über den Abschluss-Commit, über die koordinierenden Titel und über die Task-ID im
  Body jedes Datei-Commits.
- **Bestand: zwei Branches mit gemeinsamem Präfix (dokumentiert 2026-09-26, K9):** Der
   Präfix `feat/repository-documentation-consolidation` ist von zwei Branches belegt: dem
   **aktiven** Wellen-Branch `feat/repository-documentation-consolidation-main` und dem
   **überholten** Branch `feat/repository-documentation-consolidation`. Der überholte Branch
   trägt eine divergente Doppelkopie der Spec-/Plan-Commits auf Basis eines anderen Standes; er
   ist **nicht** in `main` gelandet. Er bleibt auf ausdrückliche **Nutzer-Vorgabe („nicht
   löschen")** erhalten — ein Löschen wäre eine eigene Entscheidung (Post-Merge-Cleanup). Die
   Plan-Prüfung adressiert deshalb den **exakten Branch-Namen**, nicht das Präfix.

- **Track-A-Kollision (R3, R15, Spec §2.3):** W1 und W2 starten **erst** nach dem Track-A-Merge
  (`tests/fixtures/slimming-golden/`); Gate = Task W0-4. W1/W2 laufen **sequenziell zu** Track A
  und **nicht** parallel zu Änderungen an `scripts/lib/config.py` und `scripts/lib/consistency/*`.
  Die V1-Fixture `tests/fixtures/docs_v1_fixtures.md` entsteht erst danach. **Nachweisumfang
  von R3 (drei Kollisionsflächen, präzisiert 2026-09-26):** `tests/fixtures/`
  (`slimming-golden/`-Merge-Nachweis), `scripts/lib/` und `config/` — die beiden letzten
  Flächen werden **gegen `origin/main`** über `git diff --name-only origin/main..HEAD --
  scripts/lib/` bzw. `-- config/` geprüft (Soll: **leer**) und gehören **ausdrücklich zur
  W0-4-Welle**, nicht zum ausführenden `git`-Agenten. Alle drei Flächen sind im W0-4-Record
  belegt.
- **Provider-Agnostik (NFA-03):** kein `if provider == "Name"` in M1–M4; kein Config-Key enthält
  einen Providernamen. Guard `tests/test_provider_agnostic_dispatch.py`.
- **Fail-off für alle sechs Config-Keys** (IC-22): `docs-consolidation.enabled` ist bei Abwesenheit
  `false`; agent-meta selbst setzt ihn **explizit** `true` (NG-9). Gleiches gilt für V1–V9.
- **Kein neues `sync.py`-CLI-Flag** (NG-4) — jedes Flag wäre in `docs/api/cli-reference.md` zu
  dokumentieren (`scripts/lib/consistency/docs.py:9-44`, `Severity.ERROR`).
- **Keine inhaltliche Neuschreibung** bestehender Guides/Architektur/Wiki-Seiten (NG-1).
  Migrationen sind `git mv` + Marker-Regionen + additive Frontmatter-Zeilen.
- **Keine Mutation an `knowledge/sources/`** (NG-2); **kein** Eingriff in generierte Kontextdateien
  außer M-12 (NG-5); **kein** Rollen-Paritäts-Fix (NG-8); **kein** Platzhalter-Marker in
  Provider-Dateien (NG-11).
- **NG-10 / AC-38:** kein Assert-Skript und keine Fixture-Config der Szenarien 50/51/52/54/55/56
  wird angefasst. Szenario `64-docs-facts-drift` bleibt **Track A** (Spec §2.3), nur koordiniert.
- **NFA-10:** keine Secrets, keine Env-Werte in generierten Dateien.
- **Konventionen:** Conventional Commits (Englisch, ≤72 Zeichen, imperativ), PEP 8, snake_case,
  `from __future__ import annotations` in neuen Modulen (Muster
  `scripts/lib/spec_plan_scaffold.py:12`). Commit/Push **nur** über den `git`-Agenten und **nur**
  mit expliziten Pfaden (`git add <pfad>`; verboten: `git add -A`, `git add .`, `git commit -a`).
- **Kein Worktree**, Repo-Containment, ein frischer Subagent pro Task (Skill `plan-ledger`).
- **Keine Platzhalter** (`TODO`/`TBD`/`…`) in diesem Plan. Offene Punkte sind ausschließlich die
  Entscheidungs-Tasks W0-7/W5-1/W8-1 (OQ1/OQ9/OQ4) mit Owner und Entscheidungsweg sowie die
  Ergebnis-Records W0-1/W0-3/W0-6 zu den bereits entschiedenen OQ6/OQ2/OQ8 (Spec §11.2).

## File Structure

### Neu anzulegen (Code)

- Create: `scripts/lib/doc_facts.py` — IC-01…IC-04, IC-23. Stdlib-Blatt, 23 `DOCS_*`-Fakten.
- Create: `scripts/lib/doc_renderer.py` — IC-07, IC-10, IC-13, IC-14.
- Create: `scripts/lib/doc_index.py` — IC-09, einzige Komponente mit Doku-FS-Semantik.
- Create: `snippets/docs/repo-facts.md`, `agent-roster.md`, `pipelines.md`, `hooks.md`,
  `providers.md`, `tier-presets.md` — IC-11, 6 `*_BLOCK`-Snippet-Dateien.
- Create: `config/doc-facts-expected.yaml` — IC-23, **elf** handgepflegte Sollwerte; einziger Ort
  mit Sollzahlen im Repo-Baum (R14, NFA-11).
- Create: `docs/INDEX.md` — W3-6, 100 % generiert (§3.1), tracked (OQ6).
- Create: `docs/architecture/INDEX.md` — W4-3, Teil-Vorschau auf denselben Baum (IC-10(d)).

### Neu anzulegen (Tests)

- Create: `tests/test_doc_facts.py` — AC-01…AC-06, AC-11, AC-12, AC-25, V9-Test (W8-4).
- Create: `tests/test_doc_facts_expected.py` — AC-36.
- Create: `tests/test_doc_renderer.py` — AC-14…AC-18, AC-20…AC-24, AC-26, AC-27.
- Create: `tests/test_generated_file_drift_docs.py` — AC-19, AC-37.
- Create: `tests/test_docs_consolidation_migration.py` — AC-28, AC-29, AC-30, AC-32, AC-39, AC-40.
- Create: `tests/test_knowledge_index_gen.py` — AC-33, AC-34, AC-35, AC-41.
- Create: `tests/fixtures/docs_v1_fixtures.md` — V1a+V1b Positiv-Fixture (AC-07/AC-08), **erst
  nach Track-A-Merge** (Spec §2.3).
- Create: `docs/plans/2026-09-25-docs-consolidation-oq1.md`, `-oq2.md`, `-oq4.md`, `-oq6.md`,
  `-oq8.md`, `-oq9.md`, `-wave0-freeze.md`, `-track-a-gate.md` — W0-x / W5-1 / W8-1.

### Geändert (Code)

- Modify: `scripts/lib/consistency/docs.py` — IC-05, Checks V1…V9 (bestehende 3 unverändert).
- Modify: `scripts/lib/consistency/placeholders.py` — IC-06, `^DOCS_` in `_DYNAMIC_PREFIXES`.
- Modify: `scripts/consistency-check.py` — Registrierung der neun Checks + Common-Gate (AC-13).
- Modify: `scripts/lib/consistency/report.py` — **Rev. 0.5, K15 (B-5/E-15):** `line` und `branch`
  werden **Dataclass-Felder** von `Finding` (mit Defaults, damit bestehende Konstruktoraufrufe
  unverändert bleiben) und in `print_json_report` serialisiert; heute werden sie von
  `docs.py:329-347` als Instanzattribute gesetzt und im `--json`-Output **verworfen**
  (`report.py:28-41`, `:78-97`). Owner: **W2-7**.
- Modify: `scripts/lib/config.py` — IC-11, Snippet-Verzeichnis `snippets/docs/`; `_load_block_snippet`
  (`config.py:1842-1858`) bleibt **unverändert**.
- Modify: `scripts/lib/sync_pipeline.py` — IC-12, Stage **nach** `scaffold_spec_plan_dirs` (`:935`),
  **vor** Hash-Capture (`:1090-1099`).
- Modify: `scripts/lib/spec_plan_scaffold.py` — IC-15, `is_file_index_skeleton()` + Marker.
- Modify: `scripts/lib/generated_file_drift.py` — IC-16, Doku-Pfade symmetrisch in Scan **und**
  Capture; Allowlist gegen Basis-Pfad.
- Modify: `scripts/lib/knowledge.py` — IC-19, IC-20, IC-24 (nur W7).
- Modify: `config/project-config.schema.json` — M-11, IC-22, geschlossener Block
  `docs-consolidation` mit **sechs** Properties.

### Geändert (Config / Doku / Agent)

- Modify: `.meta-config/project.yaml` — W1-10 fünf additive Keys; W3-4 `checks.strict: true`;
  W6-2 `legacy:` +2 Zeilen (`:61-63`); W7-2/W7-5 `okf.index-mode`; W8-4 `PROJECT_STRUCTURE`
  (`:205-221`).
- **Unverändert:** `.gitignore` — OQ6 ist entschieden (2026-09-26): `docs/INDEX.md` ist
  **tracked**, also gibt es **keinen** `.gitignore`-Eintrag für `docs/INDEX.md`; die Datei
  `.gitignore` selbst wird von **keinem** Task geschrieben oder verändert. **W3-6 legt
  `docs/INDEX.md` an und committet sie (tracked)** — W3-6 schreibt **nicht** in `.gitignore`.
  Verifiziert wird stattdessen `git check-ignore -q docs/INDEX.md` → Exit **1**.
- Modify: `README.md` — W3-7 Marker-Regionen, W8-2 Totverweise (`:721-724`), W8-3 Providerzahl.
- Modify: `llms.txt` — W3-7 `:5`/`:24`, W8-3 Providerzahl.
- Modify: `ARCHITECTURE.md` — W3-7 `:3` als Region, W4-2 Stub.
- Modify: `knowledge/schema.md` — W7-1, Absatz „`index.md` is generated“ (`:41-42`), mit
  **User-Sign-off** (`:44-46`).
- Modify: `agents/1-generic/knowledge-indexer.md` — W7-4, IC-21 (einzige `agents/`-Berührung, NFA-08).
- Modify: `knowledge/wiki/**/*.md` — W5-3, additive `derived-from`/`derived-at`; W7-5 generiert
  `index.md` und hängt eine Zeile an `log.md`.
- Modify: `docs/REQUIREMENTS.md` — W8-1, deklarativer ID-Abschnitt (keine Umbenennung, NG-6).

### Verschoben / Stub / Archiviert / Gelöscht (M3)

| Op | Aktion | Welle | Quelle → Ziel |
|---|---|---|---|
| M-1 | `git mv` | W4 | `ARCHITECTURE.full.md` → `docs/architecture/00-overview-full.md` |
| M-2 | Stub schreiben | W4 | `ARCHITECTURE.md` (84 Z) → generierter Stub (IC-18) |
| M-7 | additiv | W4 | Stale-Deklaration wandert in die Langfassung |
| M-5 | `git mv` | W5 | `howto/configs/project.yaml.example` (340 Z) → `docs/guides/configs/project.yaml.example` |
| M-6 | `git mv` | W5 | `docs/howto/admin-ui-remote-access.md` → `docs/guides/admin-ui-remote-access.md`; danach `docs/howto/` entfernt |
| M-9/M-10 | additiv | W5 | `derived-from`/`derived-at`; Architektur-Redirects |
| M-3 | `git mv` | W6 | `docs/superpowers/specs/` → `docs/specs/archive/superpowers/` |
| M-4 | `git mv` | W6 | `docs/superpowers/plans/` → `docs/plans/archive/superpowers/`; danach `docs/superpowers/` entfernt |
| M-8 | Modify | W8 | `README.md:721-724` Totverweise |
| M-11 | Modify | W1 | Schema-Block |
| M-12 | Modify (Config) | W8 | `PROJECT_STRUCTURE` |
| M-13 | Modify | W6 | `legacy:` additiv |

### Bewusst **nicht** angefasst (mit Grund)

- `docs/CODEBASE_OVERVIEW.md` — NG-3 (gehört `documenter`) **und kein AC** in der Spec ⇒ nicht
  geplant; FI-2 bleibt Folge-Issue.
- `knowledge/sources/**` — NG-2, append-only.
- `tests/scenarios/asserts/5{0,1,2,4,5,6}*.sh`, `tests/scenarios/configs/*` — NG-10 / AC-38.
- `AGENTS.md`-Bootstrap-Block — NG-5 / OQ3, eigene REQ nach W8.
- `docs/README.md` — NG-7, wird nicht eingeführt (T-3).

---

## Wellen-Übersicht, Reihenfolge und Entscheidungs-Vorlauf

```
W0 (6 Tasks, kein Code)
 |- W0-1 REC-OQ6 -----> Ergebnis-Record, entschieden 2026-09-26: tracked, kein .gitignore-Eintrag
 |- W0-3 REC-OQ2 -----> Ergebnis-Record, entschieden 2026-09-26: Hybrid (2 Blöcke, Rest Handtext)
 |- W0-4 Track-A-Gate -> blockiert W1 und W2
 |- W0-6 REC-OQ8 -----> Ergebnis-Record, entschieden 2026-09-26: Sync/Validator, kein Hook
 |- W0-7 DEC-OQ1 -----> blockiert Abschluss W5 (offen)
 `- W0-2 Freeze -------> blockiert alle W0-Folge-Tasks (W0-1, W0-3, W0-4, W0-6, W0-7)
        v
PG-1 (3 Ketten parallel, max 3 Agents)
 |- W1-A: W1-1 -> W1-2 -> W1-3 -> W1-4 -> W1-5 -> W1-6   (doc_facts + Config-Bridge)
 |- W1-B: W1-7 -> W1-8 -> W1-10                        (doc_renderer + doc_index + Config-Keys)
 `- W1-C: W1-9                                        (Schema-Block M-11)
        v
PG-2 (2 Ketten parallel, max 2 Agents)
 |- W2: W2-1 -> W2-2 -> W2-3 -> W2-4 -> W2-5 -> W2-6 -> W2-7   (consistency/docs.py)
 `- W3: W3-1 -> W3-2 -> W3-3 -> W3-4 -> W3-5 -> W3-6 -> W3-7   (Renderer/Stage/Drift/Index)
       +-- Zusatzkante (Rev. 0.5, K16/RVW-4):  W2-1 (Schritt 4) --> W3-4
       |   Vorwaerts-Kante ueber die Wellengrenze W2 -> W3: kein Zyklus, keine neue Task.
       |   Folge: W3-4 startet erst nach W2-1 Schritt 4; W3-1..W3-3 und W3-5..W3-7
       |   bleiben parallel zu W2 (Write-Sets weiterhin disjunkt).
        v
PG-3 (BEWUSST SERIELL, 1 Agent)  W4-1 -> W4-2 -> W4-3 -> W5-1 -> W5-2 -> W5-3 -> W6-1 -> W6-2
        v
PG-4 (isoliert, 1 Agent)         W7-1 -> W7-2 -> W7-3 -> W7-4 -> W7-5
        v
PG-5 (1 Agent)                    W8-1 -> W8-2 -> W8-3 -> W8-4
```

| Welle | Tasks | AC-Menge (Spec §9.2) | Abhängig von | Parallel | Rückrollpunkt |
|---|---|---|---|---|---|
| W0 | 6 | Anker (W0 trägt laut Spec §9.2 kein eigenes AC) | — | — | Dateien löschen, kein Code berührt |
| W1 | 10 | AC-01…AC-06, AC-23…AC-25, AC-39 | W0 | PG-1: W1-A ‖ W1-B ‖ W1-C | `docs-consolidation.enabled: false`; kein Datei-Diff |
| W2 | 7 | AC-07…AC-11, AC-13, AC-36 | W1-A, W0-4 | PG-2: W2 ‖ W3 | `checks.strict: false` bzw. `enabled: false` |
| W3 | 7 | AC-12, AC-14…AC-22, AC-26, AC-27, AC-37, AC-38 | W1-B, W0-1, W0-6, **W2-1 (nur Schritt 4, K16 — Rev. 0.5/RVW-4)** | PG-2 | `git rm docs/INDEX.md`; Marker entfernen; `enabled: false` |
| W4 | 3 | AC-28 (Teil), AC-29 | W3 | PG-3 seriell | `git mv` zurück + Stub `git checkout` |
| W5 | 3 | AC-28 (Teil), AC-31 | W1, W0-7 | PG-3 seriell | `git mv` zurück; Annotationen additiv revertierbar |
| W6 | 2 | AC-28 (Teil), AC-32 | W3 | PG-3 seriell | Config-Key additiv → Zeile entfernen |
| W7 | 5 | AC-33…AC-35, AC-41 | W5, W3, Rollenpflege-Branch gemergt | **isoliert** | `index-mode: llm` → Generator stumm; `restore_wiki_index()` |
| W8 | 4 | AC-30, AC-40 | W2, W3, **nach** W7 | PG-5 | additiv revertierbar |

### Warum W2 ‖ W3 parallel ist, W4/W5/W6 aber nicht

- **W2 ‖ W3:** Write-Sets disjunkt. W2 besitzt `scripts/lib/consistency/docs.py`,
  `tests/test_doc_facts.py`, `tests/test_doc_facts_expected.py`, `tests/fixtures/docs_v1_fixtures.md`,
  `scripts/consistency-check.py`. W3 besitzt `scripts/lib/doc_renderer.py`, `scripts/lib/doc_index.py`,
  `scripts/lib/sync_pipeline.py`, `scripts/lib/spec_plan_scaffold.py`,
  `scripts/lib/generated_file_drift.py`, `tests/test_doc_renderer.py`,
  `tests/test_generated_file_drift_docs.py`, `docs/INDEX.md`, `README.md`, `llms.txt`,
  `ARCHITECTURE.md`, `.meta-config/project.yaml`. Überschneidung: keine (`.gitignore` bleibt
  unberührt, OQ6 entschieden). Spec §9.2
  bestätigt diese Parallelität.
- **W4/W5/W6 seriell (bewusste Abweichung von Spec §9.2 „Parallel mit“):** die Spec bindet die
  Testdateinamen (§7-Einleitung). AC-28, AC-29, AC-31 und AC-32 verweisen **alle** per `::` auf
  `tests/test_docs_consolidation_migration.py`. Tasks, die dieselbe Datei anlegen oder erweitern,
  sind nicht ownership-disjunkt; `check_plan_file_overlap` würde den Parallelstart als Fehler
  melden. Zusätzlich erzeugt jede `git mv`-Welle R+A-Diffs auf denselben Stammpfaden.
  **Entscheidung: PG-3 läuft mit einem Agenten sequenziell W4 → W5 → W6.** Das verlängert die
  Laufzeit, verletzt aber weder Ownership noch `plan-ledger`.
- **W7 isoliert** (NFA-06, R2, R19): einziger Policy-Bruch (`scripts/lib/knowledge.py:112-114`),
  einziges Datenverlust-Potenzial, einzige `agents/`-Berührung.
- **W8 nach W7**, obwohl Spec §9.2 nur W2/W3 nennt: W7 aktiviert den Generator und verschiebt den
  Diff-Bezugsrahmen; W8s M-12 wirkt auf **alle** generierten Kontextdateien. Die Sequenzierung
  hält NFA-06 („Rollback je Welle invalidiert keine andere Welle“) aufrecht.
- **Maximal 3 gleichzeitig laufende Agents** — unter der Grenze von 4. Eine wellen-interne
  Barrieren-Spaltung über 4 hinaus ist damit **nicht** erforderlich.
- **`.meta-config/project.yaml` wird von W1-10, W3-4, W6-2, W7-2/5 und W8-4 geschrieben** — alle
  liegen in **verschiedenen, sequenziell geordneten** Wellen, daher keine Parallelitätskollision.

### Step-Agent-Map (plan-driven `implement`, Stufe 3)

| Task | Agent | Task | Agent | Task | Agent |
|---|---|---|---|---|---|
| W0-1, W0-4, W0-6, W0-7 | orchestrator | W1-1…W1-5, W1-7, W1-8 | senior-developer | W3-1…W3-4 | senior-developer |
| W0-2 | git | W1-6, W1-9, W1-10 | developer | W3-5…W3-7 | developer |
| W0-3 | agent-meta-manager | W2-1…W2-7 | developer | W4-1, W4-2, W5-2, W6-1 | developer |
| W4-3, W5-3, W6-2, W8-4 | tester | W5-1 | technical-writer | W7-1, W7-5 | knowledge-curator |
| W7-2, W7-3 | senior-developer | W7-4 | prompt-engineer | W8-1 | requirements |
| W8-2, W8-3 | developer | | | | |

> `pipeline_stages.implement = 3` = Stufe `implement` (frischer Subagent pro Task, zweistufiges
> Review `review-req` → `review-quality`, Ledger = Checkboxen dieser Datei, Skill `plan-ledger`).

---

## W0 — Definition, Entscheidungen, Freeze (kein Code)

**Verifikation W0 (erwartete Exit-Codes):** `git rev-list --left-right --count origin/main...HEAD`
→ **linke Zahl `0`** (kein Rückstand gegen `main`; die **rechte** Zahl zählt die eigenen
Wellen-Commits des Branches und ist **unbeschränkt**) **und** der Wellen-Branch existiert unter
**exaktem Namen** (`git rev-parse --verify --quiet
refs/heads/feat/repository-documentation-consolidation-main` → **0**); `git log --oneline
origin/main..HEAD -- scripts/lib/` → **0** (nur lesend: **keine** Änderung an `scripts/lib/`
gegenüber `origin/main` — das ist die Aussage „W0 berührt `scripts/lib/` nicht"; **nicht** die
Aussage „dieser Pfad hat nie Historie"). **Kein** `sync.py`-Lauf mit
Schreibwirkung, kein Commit von Fremdänderungen.
*Ausführungskorrektur 2026-09-26 (K9, Präfix-Match):* die Prüfung adressiert den **exakten
Branch-Namen**. `git branch --list 'feat/repository-documentation-consolidation*'` ist ein
**Präfix**-Match und liefert **gemessen 2 Zeilen** (2026-09-26) — nicht eine, wie die Fassung
Rev. 0.2 annahm: `feat/repository-documentation-consolidation-main` (aktiv) und
`feat/repository-documentation-consolidation` (überholt, auf Nutzer-Vorgabe erhalten). Der
Präfix-Wert **2** ist damit **kein Prüffehler**, sondern der dokumentierte Bestand; er ist
**zusätzlich** als Expect-Wert geführt, damit ein dritter Branch auffällt.
*Ausführungskorrektur 2026-09-26 (K7, veralteter Prüfstand):* `git log --oneline -20 --
scripts/lib/` → **0** war unerfüllbar und sinnlos — das Kommando zählt die letzten 20 Commits
des Branch und **nicht** eine W0-Berührung. Umgestellt auf die Differenz gegen die Basis
(gleiche Begründungslogik wie K1 beim Synchronitätskriterium: abgedeckt wird ein *veralteter
Prüfstand*, nicht die Existenz von Historie).
*Ausführungskorrektur 2026-09-26:* die
ursprüngliche Prüfung `git branch --list 'chore/docs-consolidation-w*'` → **0** ist entfallen,
weil **keine** Wellen-Branches angelegt werden (siehe Global Constraints und W0-2) — sie hätte
auch bei erfüllter Strategie nichts geprüft.
**Review W0:** `concept-reviewer` (Spec-Treue der Entscheidungs-Records) → `orchestrator`.
**Gate bei CHANGES_REQUESTED:** W0-1/W0-3/W0-6/W0-7 kehren in die Welle zurück; W0-2/W0-4 sperren
alle Folgewellen bis zur Auflösung.
**Rollback W0:** `git rm docs/plans/2026-09-25-docs-consolidation-*.md`; der Wellen-Branch
`feat/repository-documentation-consolidation-main` trägt die Spec-/Plan-Commits und wird **nicht**
gelöscht, sondern auf `origin/main` zurückgesetzt; kein Code berührt, keine andere Welle invalidiert
(Ausführungskorrektur 2026-09-26: kein `chore/docs-consolidation-w<N>`-Branch angelegt).

### W0-1: REC-OQ6 — `docs/INDEX.md` tracked (Ergebnis-Record, entschieden 2026-09-26)

**Files:** Create `docs/plans/2026-09-25-docs-consolidation-oq6.md`
**Interfaces:** Produces: **Ergebnis-Record** der Tracking-Entscheidung (**tracked**) +
Begründung + Folge für `.gitignore`. Consumes: Spec §11.2 **OQ6** (entschieden 2026-09-26),
`scripts/lib/spec_plan_scaffold.py:23`, `.meta-config/project.yaml:70`.
**Agent:** orchestrator · **Depends on:** W0-2 · **parallel_group:** — (sequenziell, OQ6-Ergebnis-Record; das Track-A-Gate ist **W0-4**)
**Ziel-AK (AC):** AC-20, AC-21 (Index-Writer-Vertrag), AC-12 (Index im Repo).
**Akzeptanz:** Record nennt die **bereits getroffene** Entscheidung (**tracked**), Entscheider,
Datum 2026-09-26 und die exakte `.gitignore`-Folge: **kein** `.gitignore`-Eintrag,
`.gitignore` bleibt unverändert. **Diese Task trifft die Entscheidung nicht**, sie dokumentiert
sie (Spec §11.2).
**Verifikation:** `git check-ignore -q docs/INDEX.md; echo $?` → **1** (nicht ignoriert). Die
gesicherte Entscheidung ist `tracked`, also ist **1 der Sollwert**; **0** (ignoriert) wäre ein
**Widerspruch zur Entscheidung** und ist im Record als solcher zu melden. **Kein**
entscheidungsabhängiger Offenstand mehr.
**Steps:**
- [ ] 1: Die getroffene Entscheidung aus Spec §11.2 OQ6 übernehmen: **tracked**; Traces aus
      `scripts/lib/spec_plan_scaffold.py:23` und `project.yaml:70` im Record belegen.
- [ ] 2: `.gitignore`-Folge festschreiben (**kein** Eintrag) und die verworfene Alternative
      (`untracked` wie `.claude/`) benennen.
- [ ] 3: Record schreiben inkl. „Folge für W3-6“ und des gewählten `index-mode`-Werts.
- [ ] 4: commit via `git`-Agent: `docs: record OQ6 index tracking decision`.

### W0-2: Design-Freeze, Contract-Liste, Branch-Scaffold

**Files:** Create `docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md`
**Interfaces:** Produces: eingefrorene IC-Liste IC-01…IC-24, NFA-01…NFA-11, Startwelle je
V-Check, **ein** Wellen-Branch `feat/repository-documentation-consolidation-main` mit sequenziellen
W-Commits, Commit-Reihenfolge. Consumes: Spec §5, §8, §9.2, §15.
**Agent:** git · **Depends on:** — · **parallel_group:** —
**Ziel-AK (AC):** Querschnittsanker AC-01…AC-41 (W0 trägt laut Spec §9.2 kein eigenes AC).
**Akzeptanz:** Record listet alle 24 IC mit Zielmodul und Welle, die 9 V-Checks mit Startwelle und
die Wellen-Zuordnung über die Commit-Titel-Konvention `docs(docs-consolidation): W<N> …` plus den
Abschluss-Commit `docs(docs-consolidation): W<N> complete` je grüner Welle. Es wird **genau ein**
Wellen-Branch verwendet (`feat/repository-documentation-consolidation-main`); **kein**
`chore/docs-consolidation-w<N>` wird angelegt.
> **Ausführungskorrektur 2026-09-26 (Quelle: empirische Messung in W0-2/W0-4) — Abweichung mit
> Begründung, keine stille Erfüllung.** Die ursprüngliche Vorgabe „**acht** Wellen-Branches
> `chore/docs-consolidation-w0`…`-w8` anlegen, gestapelte PRs" (Plan-W0-2 Schritt 2, Global
> Constraints, Spec §9.2 W0, R16) ist **überholt und wurde nicht umgesetzt**: Der Nutzer hat
> **einen** Feature-Branch und **einen** PR vorgegeben. Begründung der Anpassung: Nutzer-Vorgabe
> hat Vorrang; acht Branches erzeugen acht Merge-Kernel ohne Erkenntnisgewinn (die Wellen sind
> ohnehin sequenziell, W4/W5/W6 sogar seriell); der R16-Intent wird über Reihenfolge- und
> Merge-Regel abgedeckt, nicht über die Branch-Anzahl. Die Wellen-Zuordnung bleibt über die
> Wellenkennung im Commit-Titel, den Wellen-Abschluss-Commit und die Task-ID im Commit-Body
> vollständig rekonstruierbar. Beleg: W0-2-Record Kapitel 7.
> **Spec-Abweichung, offen (Stand 2026-09-26) — nicht verdeckt:** **Spec §9.2 W0 und R16
> verlangen weiterhin einen Branch pro Welle**; umgesetzt ist **ein** Branch. Da dieser Record die
> Spec zur **normativen Quelle** erklärt, gewinnt nach dieser eigenen Regel die Spec — der
> eingefrorene Zustand verletzt damit die normative Quelle. Die Korrektur der Spec (Rev. 0.4) ist
> **beauftragt, aber nicht ausgeführt**, weil sie ein **Concept-Review** erfordert. **Bis dahin
> gilt die umgesetzte Strategie**; der Widerspruch ist dokumentiert. Fgeführt als offener Punkt
> **OP-1** (Self-Review dieses Plans, W0-2-Record Kapitel 7/10, Track-A-Gate-Record §10).
**Verifikation:** `git rev-list --left-right --count origin/main...HEAD` → **linke Zahl `0`**
(kein Rückstand gegen `main`; die rechte Zahl ist unbeschränkt) **und** der Wellen-Branch
existiert unter **exaktem Namen** (`git rev-parse --verify --quiet
refs/heads/feat/repository-documentation-consolidation-main` → **0**); als **dokumentierter
Präfix-Bestand** `git branch --list 'feat/repository-documentation-consolidation*'` → **2**
(1 aktiver Wellen-Branch + 1 überholter, absichtlich erhaltener Branch; gemessen 2026-09-26 —
siehe Global Constraints, „Bestand: zwei Branches mit gemeinsamem Präfix");
`grep -c '^#### IC-' docs/specs/2026-09-25-repository-documentation-consolidation.md` → **24**
(gemessen 2026-09-26; die IC stehen in §5.1–§5.5 als `####`-Überschriften: §5.1 = IC-01…06,
§5.2 = IC-07…16, §5.3 = IC-17…18, §5.4 = IC-19…22, §5.5 = IC-23…24);
`grep -c '^| NFA-' docs/specs/2026-09-25-repository-documentation-consolidation.md` → **11**
(gemessen 2026-09-26). Das NFA-Muster weicht **bewusst** vom IC-Muster ab, weil die NFA in Spec §8
als **Tabellenzeilen** und nicht als `####`-Überschriften geführt werden — `grep -c '^#### NFA-'`
liefert **0** und wäre ein Musterfehler, kein Befund.
*Ausführungskorrektur 2026-09-26:* die ersetzte Prüfung `git branch --list
'chore/docs-consolidation-w*'` → **0** verlor ihren Sinn, da keine Wellen-Branches angelegt
werden.
*Präzisierung 2026-09-26 (K8):* „genau **1** eigener Wellen-Branch" bedeutet **einen aktiven
Wellen-Branch unter exaktem Namen** — nicht „genau eine Zeile" eines Präfix-Matches. Die
Fassung Rev. 0.2 war mit dem Präfix-Messwert **2** nicht erfüllbar.
**Steps:**
- [ ] 1: IC-/NFA-/V-/Wellen-Liste aus der Spec extrahieren und im Record spiegeln.
- [ ] 2: Commit-Titel-Konvention festschreiben — `W<N>`-**Präfix verbindlich** für den
      Wellen-Abschluss-Commit `docs(docs-consolidation): W<N> complete` und für wellen-
      koordinierende Titel; **optional** für einzelne Datei-Commits innerhalb einer Welle, dann
      mit **Task-ID im Commit-Body** (`Task: W<N>-<k>`); **einen** Wellen-Branch
      `feat/repository-documentation-consolidation-main` führen und die Abweichung von der
      Vorgabe „acht Wellen-Branches" (Spec §9.2 W0, R16) **begründet** dokumentieren; **kein**
      `chore/docs-consolidation-w<N>`-Branch anlegen.
- [ ] 3: Commit-Reihenfolge und Merge-Regel („`git mv`-Wellen zuerst mergen“) festschreiben.
- [ ] 4: commit via `git`-Agent: `docs: freeze docs-consolidation contracts and wave branches`.

### W0-3: REC-OQ2 — `llms.txt` Hybrid (Ergebnis-Record, entschieden 2026-09-26)

**Files:** Create `docs/plans/2026-09-25-docs-consolidation-oq2.md`
**Interfaces:** Produces: **Ergebnis-Record** der Modusentscheidung + Eintrag in IC-22
`docs-consolidation.sources`. Consumes: Spec §11.2 **OQ2** (entschieden 2026-09-26), IC-08,
IC-22, `llms.txt:3-12`.
**Agent:** agent-meta-manager · **Depends on:** W0-2 · **parallel_group:** W0-PG-B
**Ziel-AK (AC):** AC-25, AC-40.
**Akzeptanz:** Record hält die **bereits getroffene** Entscheidung fest — `llms.txt` bleibt
**handgepflegt** (Handtext-Einleitung und Linkliste unverändert), generiert werden
**ausschließlich** `{{DOCS_PROVIDERS_BLOCK}}` und `{{DOCS_REPO_FACTS_BLOCK}}`; ein
**Vollgenerieren** der Datei ist **nicht** entschieden. `llms.txt` ist ein Wert von
`docs-consolidation.sources`; Prosa-Ton `llms.txt:3-12` bleibt erhalten. **Diese Task trifft
die Entscheidung nicht** — sie dokumentiert sie (Spec §11.2).
**Verifikation:** `grep -n 'llms.txt' docs/plans/2026-09-25-docs-consolidation-oq2.md` → **0**
(mindestens ein Treffer).
**Steps:**
- [ ] 1: Die getroffene Entscheidung aus Spec §11.2 OQ2 übernehmen: **Hybrid** — Handtext
      bleibt, generiert werden nur `{{DOCS_PROVIDERS_BLOCK}}` + `{{DOCS_REPO_FACTS_BLOCK}}`.
      Die verworfene Vollgenerierung **benennen, nicht wählen**.
- [ ] 2: Folge für `docs-consolidation.sources` (IC-22) festschreiben und den Folge-Edit in
      **W1-6** (Snippet-Bridge) und **W3-7** (Marker-Regionen, `llms.txt:5`) benennen.
- [ ] 3: Record schreiben (Entscheidung, Entscheider, Datum 2026-09-26, Gewähltes/Verworfenes).
- [ ] 4: commit via `git`-Agent: `docs: record OQ2 llms.txt hybrid decision`.

### W0-4: Track-A-Kollisionsgate (R3, R15)

**Files:** Create `docs/plans/2026-09-25-docs-consolidation-track-a-gate.md`
**Interfaces:** Produces: go/no-go-Freigabe für W1 und W2 + Liste der zuletzt von Track A
berührten `scripts/lib/`-Dateien. Consumes: Spec §2.3, §9.2 (R3), Git-Historie **von
`origin/main`** (nicht des Feature-Branches).
**Agent:** orchestrator · **Depends on:** W0-2 · **parallel_group:** W0-PG-B
**Ziel-AK (AC):** AC-07, AC-08 (Fixture-Kollision), AC-39 (Schema-Datei).
**Akzeptanz:** Der Record belegt den Track-A-Merge-Status **gegen `origin/main`** — nicht gegen
einen Feature-Branch: (a) `git ls-tree -r --name-only origin/main --
tests/fixtures/slimming-golden/` ist **nicht leer** (Verzeichnis in `main` vorhanden; Soll:
**59** Einträge = 58 Fixtures + `README.md`), (b) `git ls-tree origin/main --
tests/fixtures/docs_v1_fixtures.md` ist **leer**, (c) `tests/fixtures/docs_v1_fixtures.md`
existiert auch im Arbeitsbaum nicht. **Erst dieser Nachweis gegen `origin/main`** gilt als
Track-A-Merge; ohne ihn bleiben W1 und W2 gesperrt. Der Branch muss dabei **nicht hinter**
`origin/main` liegen: `git rev-list --left-right --count origin/main...HEAD` → **linke Zahl `0`**
(die **rechte** Zahl ist **unbeschränkt** — sie zählt die eigenen Spec-/Plan-Commits des Branches
und erzeugt keinen veralteten Prüfstand); äquivalent und robuster `git merge-base --is-ancestor
origin/main HEAD` → Exit **0** („`main` ist Vorfahr des Branches"). Beide Formen sind
gleichbedeutend: das abgedeckte Risiko ist ein **veralteter Prüfstand**, also Commits, die auf
`main` gelandet sind und im Branch fehlen — genau die **linke** Zahl. Inhaltlich unverändert geprüft
wird dieselbe Aussage wie bisher: Fixture-Verzeichnis in `main` vorhanden, V1-Fixture
`docs_v1_fixtures.md` nicht vorhanden.
**Verifikation:** `git fetch origin` → **0**; `git ls-tree -r --name-only origin/main --
tests/fixtures/slimming-golden/` → **nicht leer** (**59** Einträge; zulässige Alternative:
`git ls-tree -d origin/main -- tests/fixtures/` → enthält den Tree-Eintrag
`tests/fixtures/slimming-golden`); `git ls-tree origin/main -- tests/fixtures/docs_v1_fixtures.md` →
**leer**; `ls tests/fixtures/docs_v1_fixtures.md` → **2** (nicht vorhanden — GNU `ls` liefert bei
fehlendem Operanden **2**; der Wert `1` wäre „No such file or directory" in anderen Werkzeugen und
ist hier nicht der Fall; robust prüfbar mit `test ! -e tests/fixtures/docs_v1_fixtures.md` → **0**);
`git rev-list --left-right --count origin/main...HEAD` → **linke Zahl `0`** (rechte Zahl
unbeschränkt) **oder** `git merge-base --is-ancestor origin/main HEAD` → **0**.
**Ergänzende R3-Gegenproben (Teil der W0-4-Welle, keine Freigabebedingung):**
`git diff --name-only origin/main..HEAD -- scripts/lib/` → **leer**; `git diff --name-only
origin/main..HEAD -- config/` → **leer** (beide gemessen **leer**, 2026-09-26). Damit sind alle
drei von R3 genannten Kollisionsflächen belegt — `tests/fixtures/` über den `ls-tree`-Nachweis
oben, `scripts/lib/` und `config/` über die Gegenproben.
> **Ausführungskorrektur 2026-09-26 (Quelle: empirische Messung in W0-4, Record §3–§5).** Drei
> Fehler in der Verifikationsformulierung, **keine** Änderung des geprüften Zustands und **keine**
> Änderung der Gate-Aussage: (i) das Synchronitätskriterium `0 0` war ein Denkfehler und ist
> unerfüllbar — es verlangte einen Branch **ohne eigene Commits**, obwohl der Branch seine
> Spec-/Plan-Commits konstruktionsbedingt trägt; umgestellt auf **linke Zahl = 0**;
> (ii) `git ls-tree -d` **mit** einem Pfadspec, der auf das Verzeichnis selbst zeigt, liefert
> **leer** (Exit 0) — der Verzeichnis-Eintrag wird nur beim Auflisten des **Elternpfads** sichtbar;
> (iii) `ls` auf eine fehlende Datei liefert **2**, nicht `1`. Inhaltlich bleibt: Fixture-
> Verzeichnis in `main` vorhanden, `docs_v1_fixtures.md` nicht vorhanden; W1/W2 sind nur frei, wenn
> der Branch **nicht hinter** `main` liegt.
> **Präzisierung 2026-09-26 (K10) — Nachweisumfang deckt alle drei R3-Flächen ab:** R3 nennt
> `tests/fixtures/`, `scripts/lib/` **und** `config/`. Die Fassung Rev. 0.2 belieegte nur
> `tests/fixtures/`. **Neu und ausdrücklich Teil der W0-4-Welle** sind die beiden Gegenproben
> `git diff --name-only origin/main..HEAD -- scripts/lib/` → **leer** und `git diff --name-only
> origin/main..HEAD -- config/` → **leer** (beide **gemessen leer** am 2026-09-26, im
> W0-4-Record §3 belegt). Sie sind **keine** Bedingung der Freigabe — die inhaltliche
> Gate-Aussage bleibt die Fixture-Prüfung —, sondern schließen die Nachweislücke.
**Ausdrücklich kein Merge-Nachweis:** `git log --oneline -20 --
tests/fixtures/slimming-golden/` (und `git log --oneline -20 -- scripts/lib/`) führen nur die
zuletzt von Track A berührten Dateien auf — sie sind **kein** Nachweis des Merges nach `main`.
Der Merge-Nachweis ist ausschließlich der `git ls-tree`-Befehl gegen `origin/main` oben.
**Steps:**
- [ ] 1: `git fetch origin`; dann `git ls-tree -r --name-only origin/main --
      tests/fixtures/slimming-golden/` (Soll: **nicht leer**, 59 Einträge) und `git ls-tree
      origin/main -- tests/fixtures/docs_v1_fixtures.md` auswerten (Nachweis **gegen
      `origin/main`**, nicht gegen den Feature-Branch) und `git rev-list --left-right --count
      origin/main...HEAD` → **linke Zahl `0`** (Stand-Synchronität) prüfen.
- [ ] 2: Track-A-Merge-Status **gegen `origin/main`** feststellen; bei offen **stoppen** und an
      `main_chat` eskalieren.
- [ ] 3: Record mit go/no-go und Rebase-Pflicht vor jedem Merge schreiben.
- [ ] 4: commit via `git`-Agent: `docs: record track-a collision gate for docs consolidation`.

### W0-6: REC-OQ8 — wer re-generiert `docs/INDEX.md` bei neuer Doku-Datei (Ergebnis-Record)

**Files:** Create `docs/plans/2026-09-25-docs-consolidation-oq8.md`
**Interfaces:** Produces: **Ergebnis-Record** des Workflow-Vertrags — **gewählt:**
deterministischer **Sync-/Validator-Lauf** (`sync.py` im Default-Sync, `--validate` als
`TEST_COMMAND`, `.meta-config/project.yaml:193`); **verworfen:** `pre-commit`-Hook,
CONTRIBUTING-Regel, Severity-Downgrade; **gewählter Umsetzungsschritt:** W3-6 (W3-7 braucht
keinen, da keine neue Doku-Datei entsteht).
Consumes: Spec §10, §11.2 **OQ8** (entschieden 2026-09-26), IC-05 (V2), IC-22.
**Agent:** orchestrator · **Depends on:** W0-2 · **parallel_group:** W0-PG-B
**Ziel-AK (AC):** AC-12, AC-38.
**Akzeptanz:** Der Record hält die **bereits getroffene** Entscheidung fest: Auslöser ist der
Sync-/Validator-Lauf, **kein** `pre-commit`-Hook und **keine** CONTRIBUTING-Regel. **V2 bleibt
ERROR** (Spec-Empfehlung), damit die Vertragsverletzung sichtbar bleibt; **kein** neues
`sync.py`-CLI-Flag (NG-4) und **kein** neuer Hook — der vorhandene Sync-Pfad genügt. **Diese Task
trifft die Entscheidung nicht**, sie dokumentiert sie (Spec §11.2).
**Verifikation:** `grep -n 'pre-commit\|CONTRIBUTING' docs/plans/2026-09-25-docs-consolidation-oq8.md`
→ **0** (mindestens ein Treffer). **Scharfung der Erwartung:** `pre-commit` und `CONTRIBUTING`
müssen im Record als **verworfene** Alternative erscheinen (die Spec-Empfehlung war der
`pre-commit`-Hook); der **Sync-/Validator-Lauf** muss als **gewählter** Weg erscheinen. Der
Treffer belegt also die Entscheidungsdokumentation, **nicht** eine Hook-Implementierung.
**Abgrenzung:** `index-mode` (IC-22, `docs-consolidation.index-mode`) ist **kein** Mechanismus
von OQ8 und gehört **nicht** in die Verifikationserwartung. Es ist der **IC-22-Rollback-Schalter**
(für W7, `index-mode: llm`); im OQ8-Record darf er allenfalls als dieser IC-22-Verweis genannt
werden, **nicht** als der gewählte Weg dieser Entscheidung.
**Steps:**
- [ ] 1: Die getroffene Entscheidung aus Spec §11.2 OQ8 übernehmen: Sync-/Validator-Lauf;
      die **verworfene** Spec-Empfehlung (`pre-commit`-Hook → `sync.py --dry-run`) und die
      Alternative CONTRIBUTING-Regel als **verworfen** benennen.
- [ ] 2: Entscheidung als Workflow-Vertrag festschreiben (Owner, Auslöser, Kosten).
- [ ] 3: Umsetzungsschritt in W3-6 referenzieren. **W3-7 braucht keinen Doku-Schritt** für
      OQ8: gewählt ist der Sync-/Validator-Lauf, also entsteht **kein** Hook, **keine**
      CONTRIBUTING-Regel und **keine** neue Doku-Datei (Spec §11.2) — der Vertrag lebt im
      W0-6-Record und in Spec §10.
- [ ] 4: commit via `git`-Agent: `docs: record OQ8 index regeneration contract`.

### W0-7: DEC-OQ1 — Wiki-Topics vs. `docs/guides/` (Produktentscheidung)

**Files:** Create `docs/plans/2026-09-25-docs-consolidation-oq1.md`
**Interfaces:** Produces: Scope-Grenze für W5-3 (Annotation statt Inhaltsmigration) + Titel der
Folge-REQ. Consumes: Spec §11.1 OQ1, §3.3, FI-4.
**Agent:** orchestrator (Eskalation an `main_chat`) · **Depends on:** W0-2 · **parallel_group:** W0-PG-B
**Ziel-AK (AC):** AC-31.
**Akzeptanz:** Entscheidung **vor Abschluss von W5**; Inhaltsmigration ausgeschlossen (NG-1) und
als FI-4 Folge-REQ geführt.
**Verifikation:** `grep -n 'OQ1\|FI-4' docs/plans/2026-09-25-docs-consolidation-oq1.md` → **0**.
**Steps:**
- [ ] 1: Produktfrage an `main_chat` eskalieren (Spec-Owner für OQ1).
- [ ] 2: Antwort als Scope-Grenze festhalten: W5-3 annotiert **additiv**, migriert **nichts**.
- [ ] 3: Record schreiben inkl. Folge-REQ-Referenz FI-4.
- [ ] 4: commit via `git`-Agent: `docs: decide OQ1 wiki topics scope`.

---

## W1 — DocFacts, Renderer, Snippet-Bridge, Schema (rein additiv)

**Verifikation W1 (erwartete Exit-Codes):**
- `python3 -m pytest tests/test_doc_facts.py tests/test_doc_facts_expected.py tests/test_doc_renderer.py tests/test_docs_consolidation_migration.py -q` → **0**
- `python3 scripts/sync.py --dry-run` → **0** (führt die Consistency-Suite **nicht** aus — `--dry-run`
  ist von ERROR-Checks unabhängig, RVW2-2)
- `python3 scripts/sync.py --validate` (= `TEST_COMMAND`, `.meta-config/project.yaml:193`) → **0**
  — **Erreichbarkeit im W1-Stand nicht gemessen (RVW2-2).** In W1 sind **keine** Doku-Checks
  registriert (V1–V9 starten W2-7), die Zeile hängt also **ausschließlich** am repo-weiten
  ERROR-Altbestand. `W-VALIDATE-ROT` (Wellenblock W2) und `W3-BASELINE-STRICT` (b) gelten
  wortgleich: ist die in **W3-7** gemessene Baseline `errors > 0`, ist `→ 0` unerreichbar und
  maßgeblich ist die **Deltasperre** (`errors` darf durch W1–W8 nicht steigen). Owner `validator`.
  **Kein Sollwert wird abgesenkt.**
- `python3 scripts/consistency-check.py` → **0** (V1–V9 existieren erst ab W2) — **gleiche
  Bedingung** wie oben: nicht gemessen, Deltasperre maßgeblich.
- `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0** (6/6 grün, AC-38)
- `git status --porcelain` zeigt **keine** Änderung an `README.md`, `llms.txt`, `ARCHITECTURE.md`
  (W1 ist additiv; der erste echte Datei-Diff entsteht in W3).
**Review W1:** Stufe 1 `validator` (AC-Treue) → Stufe 2 `code-reviewer` (Blast-Radius; Prüfpunkt:
kein Diff in `agents/`, `hooks/`, `commands/`, `config/*.yaml`).
**Gate bei CHANGES_REQUESTED:** Task zurück in dieselbe Kette; bei Befund an
`scripts/lib/config.py` oder `scripts/lib/consistency/*` zusätzlich Rebase gegen Track A.
**Rollback W1:** `docs-consolidation.enabled: false` (additiv-revert), Schema-Block entfernen,
Config-Keys entfernen, `git rm` der neuen `scripts/lib/doc_*.py`, `snippets/docs/`,
`config/doc-facts-expected.yaml` und der Testdateien. Kein Datei-Diff, keine andere Welle
invalidiert.

### W1-1: `doc_facts.py` Grundgerüst und `compute_doc_facts` (Key-Set)

**Files:** Create `scripts/lib/doc_facts.py`, `tests/test_doc_facts.py`
**Interfaces:** Produces: `compute_doc_facts(agent_meta_root, config, *, provider_config=None,
log=None) -> dict[str, str]` mit **exakt** 23 Schlüsseln; `HOOK_EXCLUDED_DIRS`,
`HOOK_EXCLUDED_SUFFIXES = ("-impl.sh",)`, `AGENT_HELPER_PREFIX`. Consumes:
`scripts/lib/roles.py:129` (`resolve_activation_gates`), `scripts/lib/config.py:1060-1064`
(`read_version`).
**Agent:** senior-developer · **Depends on:** W0-1, W0-4 · **parallel_group:** PG-1 / W1-A
**Ziel-AK (AC):** **AC-01** (IC-01, IC-02) · **V-Check:** — (Key-Set-Invariant, Unit-Test)
**Akzeptanz:** `test_fact_key_set_exact` grün; alle Werte `str`; keine Exceptions; Verzeichnis-Hash
von `agent_meta_root` vor/nach identisch (kein Schreibzugriff).
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py::test_fact_key_set_exact -q` → **0**.
**Steps:**
- [x] 1: Test zuerst schreiben (fail, ImportError).
- [x] 2: `doc_facts.py` mit den 23 IC-02-Schlüsseln implementieren. Die Suffix-Regel muss
      **Bindestrich** haben (Spec NF-12: `"_impl.sh"` hätte nichts gematcht und
      `DOCS_HOOKS_COUNT` wäre 13 statt 11 gelaufen).
- [x] 3: Test laufen lassen (pass), Hash-Gleichheit des Baums beobachten.
- [x] 4: commit via `git`-Agent: `feat: add doc_facts module with exact fact key set`.

### W1-2: Skalarformeln und volatile-Markierung

**Files:** Modify `scripts/lib/doc_facts.py`, `tests/test_doc_facts.py`
**Interfaces:** Produces: 13 Formel-Assertions; `volatile: true` ausschließlich für
`DOCS_SCENARIO_COUNT`; sechs `*_BLOCK`-Fakten. Consumes: W1-1.
**Agent:** senior-developer · **Depends on:** W1-1 · **parallel_group:** PG-1 / W1-A
**Ziel-AK (AC):** **AC-02** (IC-02), **AC-03** (IC-02) · **V-Check:** — (Unit-Test)
**Akzeptanz:** `test_scalar_fact_formulas` (parametrisiert, **13** Assertions) und
`test_volatile_fact_absent_from_hybrid_files` grün. **Kein** Wert wird gegen eine im Test
hinterlegte Konstante geprüft (Spec NEW-8: der `xfail`-Snapshot ist entfernt; Sollzahlen stehen
ausschließlich in `config/doc-facts-expected.yaml`).
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**.
**Steps:**
- [x] 1: Formel-Tests schreiben (fail).
- [x] 2: Formeln aus IC-02 implementieren; `DOCS_AGENTS_ACTIVE_COUNT` über `compute_active_roles`
      (IC-04), **nicht** `len(roles)` (F13/F21).
- [x] 3: Volatile-Unterdrückung implementieren; Tests grün beobachten.
- [x] 4: commit via `git`-Agent: `feat: implement doc fact formulas and volatile marking`.

### W1-3: Fehlertoleranz und aktive Rollenmenge

**Files:** Modify `scripts/lib/doc_facts.py`, `tests/test_doc_facts.py`
**Interfaces:** Produces: `compute_active_roles(agent_meta_root, config, provider_config=None) -> set[str]`;
Fehlerpfad „Quelle fehlt → `\"\"` + `log.debug`, kein `SyncError`“. Consumes: W1-2,
`scripts/lib/agent_sync.py:548`.
**Agent:** senior-developer · **Depends on:** W1-2 · **parallel_group:** PG-1 / W1-A
**Ziel-AK (AC):** **AC-04** (IC-01), **AC-05** (IC-04) · **V-Check:** **V5**
**Akzeptanz:** `test_missing_source_is_fail_soft` und
`test_se_role_excluded_by_gate_not_by_roles_list` grün; `se-component-requirements` ist **nicht**
im Ergebnis, weil `systems-engineering.enabled: false` (`.meta-config/project.yaml:12-13`).
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**;
`grep -n 'systems-engineering' .meta-config/project.yaml` → **0**.
**Steps:**
- [x] 1: Tests schreiben (fail).
- [x] 2: `compute_active_roles` = `roles:` ∩ Templates ∩ `resolve_activation_gates()` implementieren.
- [x] 3: Fail-soft-Pfade implementieren; Tests grün beobachten.
- [x] 4: commit via `git`-Agent: `feat: add fail-soft fact paths and gate-aware active roles`.

### W1-4: Staleness-Resolver

**Files:** Modify `scripts/lib/doc_facts.py`, `tests/test_doc_facts.py`
**Interfaces:** Produces: `compute_wiki_staleness(wiki_root, project_root) -> dict[str, str]` mit
`""` / `"missing-derived-from"` / `"stale-source"` / `"age-<n>d"`. Consumes: W1-3;
`knowledge/wiki/index.md:24` (Quelle wandert nach W4 mit → `docs/architecture/00-overview-full.md`, M-7).
**Agent:** senior-developer · **Depends on:** W1-3 · **parallel_group:** PG-1 / W1-A
**Ziel-AK (AC):** **AC-10** (IC-03, Prüfung in W2-3), **AC-29(c)** · **V-Check:** **V7**
**Akzeptanz:** Resolver liefert die vier Werte; `status:stale-upstream` wird **maschinell**
extrahiert und nicht mehr manuell gepflegt; Quelle ist die **Langfassung**, nicht der
`ARCHITECTURE.md`-Stub (Spec A12: die Stub-Quelle verschwindet nach W4).
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**.
**Steps:**
- [x] 1: Tests schreiben (fail).
- [x] 2: Resolver implementieren (`mtime(derived-from) > derived-at` → `stale-source`).
- [x] 3: Tests grün beobachten.
- [x] 4: commit via `git`-Agent: `feat: add wiki staleness resolver`.

### W1-5: Unabhängige Sollwert-Quelle (R14)

**Files:** Create `config/doc-facts-expected.yaml`, `tests/test_doc_facts_expected.py`;
Modify `scripts/lib/doc_facts.py`
**Interfaces:** Produces: `load_expected_doc_facts(agent_meta_root, log=None) -> dict[str, str]`,
`compare_expected_doc_facts(computed, expected) -> list[dict[str, str]]` (sortiert nach `fact`,
`kind ∈ {mismatch, missing-in-expected}`). Consumes: W1-2.
**Agent:** senior-developer · **Depends on:** W1-2 · **parallel_group:** PG-1 / W1-A
**Ziel-AK (AC):** **AC-36** (IC-23), **NFA-11** · **V-Check:** **V6** (`expected-mismatch`)
**Akzeptanz:** YAML enthält **elf** Einträge (Spec: §5.5 „Querschnitts-Contracts", IC-23
`config/doc-facts-expected.yaml` — Abschnittsanker, ersetzt den Former `Spec:1105`, der im
Rev.-0.4-Stand nicht mehr traf); `test_expected_values_match` grün;
`test_mismatch_is_reported` liefert bei manipuliertem Wert **genau einen**
`kind == "expected-mismatch"` mit beiden Werten; `compute_doc_facts()` nimmt **keinen**
Sollwert-Parameter (keine Kopplung, kein Zirkel).
**Verifikation:** `python3 -m pytest tests/test_doc_facts_expected.py -q` → **0**;
`grep -c '^[A-Z_]*:' config/doc-facts-expected.yaml` → **11**.
**Steps:**
- [x] 1: Tests schreiben (fail); manipulierter Sollwert als Negativ-Fixture im Test.
- [x] 2: `config/doc-facts-expected.yaml` anlegen (11 Keys, `verified-at`, `verified-by: human`).
- [x] 3: `load_/compare_` implementieren; Tests grün beobachten.
- [ ] 4: commit via `git`-Agent: `feat: add independent expected doc facts source`.

> **LEDGER-Stand 2026-09-26 — W1-5 TEILWEISE erledigt (Fortschrittsnotiz, keine
> Änderung der Task-Semantik).** Die **Test-/Loader-/Comparator-Hälfte** ist gelandet:
> `config/doc-facts-expected.yaml` existiert mit **elf** Einträgen plus `schema-version`,
> `verified-at: "2026-09-26"`, `verified-by: human` (`config/doc-facts-expected.yaml:41-56`),
> und `load_expected_doc_facts()` / `compare_expected_doc_facts()` sind implementiert
> (`scripts/lib/doc_facts.py` — `FACT_KEYS`-gebunden, `EXPECTED_COMPARABLE_FACT_KEYS:1509`).
> **Offen ist ausschließlich Step 4 (Commit)** zum Zeitpunkt dieses Eintrags. Die Task ist damit
> **nicht** als Ganzes abgehakt; der Rest der W1-Welle (W1-6…W1-10) und das Wellen-Gate W1
> (`plan:700-715`) bleiben davon unberührt. **Belegte Restpunkte** im Umfeld dieser Task: das
> `kind`-Vokabular des Komparators ist zwischen Akzeptanz (`kind == "expected-mismatch"`,
> `plan:807`) und `Interfaces:` (`kind ∈ {mismatch, missing-in-expected}`, `plan:799-800`)
> gespalten — geführt als **E-12** in der konsolidierten Errata-Liste
> („Ausführungs-Ledger und Errata", E-12).

### W1-6: Snippet-Bridge und `DOCS_`-Platzhalter-Namespace

**Files:** Modify `scripts/lib/config.py`, `scripts/lib/consistency/placeholders.py`,
`tests/test_doc_facts.py`; Create `snippets/docs/repo-facts.md`, `agent-roster.md`,
`pipelines.md`, `hooks.md`, `providers.md`, `tier-presets.md`
**Interfaces:** Produces: `variables["DOCS_*_BLOCK"]` aus `snippets/docs/*.md` über den
**unveränderten** `_load_block_snippet` (`config.py:1842-1858`); `^DOCS_` in `_DYNAMIC_PREFIXES`
(`placeholders.py:128-131`). Consumes: W1-4, OQ2-Entscheidung (**Hybrid**, Spec §11.2; Record
W0-3).
**Agent:** developer · **Depends on:** W1-4, W0-3 · **parallel_group:** PG-1 / W1-A
**Ziel-AK (AC):** **AC-25** (IC-11), **AC-06** (IC-06) · **V-Check:** — (Unit-Test)
**Akzeptanz:** `test_docs_snippet_inlining_contract` und
`test_docs_prefix_registered_in_placeholders` grün; `QUALITY_PIPELINES_BLOCK` bleibt vorhanden
(`config.py:1882`); Ergänzung **nach** dem `snippets/security/`-Block (`:1923-1924`);
`DOCS_LANGUAGE`/`INTERNAL_DOCS_LANGUAGE` (`.meta-config/project.yaml:183-184`) bleiben unberührt
(R12); Snippets sind **frontmatter-behaftet**, Inlining-Output ist frontmatter-frei.
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**;
`ls snippets/docs/*.md | wc -l` → **6**.
**Steps:**
- [x] 1: Tests schreiben (fail).
- [x] 2: Sechs Snippets mit eigenem Frontmatter anlegen; `config.py` additiv erweitern; `^DOCS_` registrieren.
- [x] 3: Tests grün beobachten; `QUALITY_PIPELINES_BLOCK`-Regression gegenprüfen.
- [x] 4: commit via `git`-Agent: `feat: add docs snippet bridge and DOCS_ placeholder namespace`.

### W1-7: `doc_renderer.py` — Marker-API

**Files:** Create `scripts/lib/doc_renderer.py`, `tests/test_doc_renderer.py`
**Interfaces:** Produces: `DOCS_BLOCK_RE`, `render_doc_fact_block(region, facts) -> str`,
`apply_fact_blocks(text, facts, log=None) -> str`. Consumes: W1-1 (Fakten), Muster
`scripts/lib/context.py:36-50` (Regionspaar, `count=1`).
**Agent:** senior-developer · **Depends on:** W1-1 · **parallel_group:** PG-1 / W1-B
**Ziel-AK (AC):** **AC-14**, **AC-15**, **AC-16**, **AC-27** (IC-07, IC-08) · **V-Check:** **V6**
**Akzeptanz:** `test_apply_fact_block_single_region`, `test_unbalanced_marker_is_noop_with_warning`,
`test_duplicate_region_first_only`, `test_output_independent_of_dict_order` grün; unbalancierte
Region → Rückgabe **byte-identisch** plus **genau ein** `log.warning`; erlaubte Regionsnamen
`facts|roster|pipelines|hooks|providers|version`; leerer Wert → `<!-- agent-meta:docs-empty: … -->`;
`docs-*` ist eigener Namespace neben `agent-meta:managed-*` (keine Kollision, IC-08).
**Verifikation:** `python3 -m pytest tests/test_doc_renderer.py -q` → **0**.
**Steps:**
- [x] 1: Tests schreiben (fail).
- [x] 2: `DOCS_BLOCK_RE` + die drei Funktionen implementieren.
- [x] 3: Tests grün beobachten.
- [x] 4: commit via `git`-Agent: `feat: add doc renderer marker API`.

### W1-8: `doc_index.py` — Doku-Baum-Modell

**Files:** Create `scripts/lib/doc_index.py`, `tests/test_doc_renderer.py`
**Interfaces:** Produces: `build_index_model(project_root) -> dict` mit
`{'root', 'entries': [{'path','title','description','kind','depth'}]}`,
`EXCLUDED_DIR_SEGMENTS = {'archive','_archive','local-Inputs'}`, `DESCRIPTION_MAX_CHARS = 120`.
Consumes: W1-7.
**Agent:** senior-developer · **Depends on:** W1-7 · **parallel_group:** PG-1 / W1-B
**Ziel-AK (AC):** **AC-17** (IC-09, Modell-Anteil), **NFA-01** · **V-Check:** **V2** (ab W2-6)
**Akzeptanz:** zweimaliger Aufruf auf demselben Baum ⇒ **byte-identisches** Ergebnis; `archive/`
ausgeschlossen; Frontmatter-lose Datei → Dateiname als `title`, `—` als description; **keine**
erfundene Beschreibung; Sortierung `kind` dann `path` (NFA-02).
**Verifikation:** `python3 -m pytest tests/test_doc_renderer.py -q` → **0**.
**Steps:**
- [x] 1: Test schreiben (fail).
- [x] 2: `build_index_model` implementieren — **einzige** Komponente mit Doku-FS-Semantik
      (kein Pfadlogik-Duplikat in `doc_facts.py`).
- [x] 3: Determinismus beobachten.
- [x] 4: commit via `git`-Agent: `feat: add docs tree index model`.

### W1-9: Schema-Block `docs-consolidation` (M-11)

**Files:** Modify `config/project-config.schema.json`; Create `tests/test_docs_consolidation_migration.py`
**Interfaces:** Produces: geschlossener Top-Level-Block `docs-consolidation` mit
`additionalProperties: false` und **sechs** Properties aus IC-22. Consumes: IC-22;
`config/project-config.schema.json:2058, :2073` (Selbstauskunft „geschlossene Unterobjekte als
Tippfehler-Wächter“), `:2425` (Wurzel permissiv).
**Agent:** developer · **Depends on:** W0-4 · **parallel_group:** PG-1 / W1-C
**Ziel-AK (AC):** **AC-39** (IC-17 M-11) · **V-Check:** — (Schema-Operation, Unit-Test)
**Akzeptanz:** `test_schema_block_present_and_closed` grün; **kein** Property-Name ist ein
Providername; `project.yaml` mit `docs-consolidation.enabled: true` validiert grün. M-11 ist
Konventions- und Autocomplete-Pflicht, **keine** Fehlerbehebung.
**Verifikation:** `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**;
`python3 -c "import json;json.load(open('config/project-config.schema.json'))"` → **0**.
**Steps:**
- [x] 1: Test schreiben (fail).
- [x] 2: Block mit sechs Properties ergänzen.
- [x] 3: Test grün beobachten; Validierung mit aktiviertem Key prüfen.
- [x] 4: commit via `git`-Agent: `feat: declare docs-consolidation config block in schema`.

### W1-10: Additive Config-Keys und Absenz-Default

**Files:** Modify `.meta-config/project.yaml`, `tests/test_doc_renderer.py`
**Interfaces:** Produces: `docs-consolidation.{enabled,index-mode,checks.strict,sources,volatile-facts}`
in `.meta-config/project.yaml`; `enabled: true` **explizit** in agent-meta (NG-9).
`knowledge-engine.okf.index-mode` folgt erst in W7-2. Consumes: W1-8, IC-22, W0-3.
**Agent:** developer · **Depends on:** W1-8 · **parallel_group:** PG-1 / W1-B
**Ziel-AK (AC):** **AC-24** (IC-13, IC-22) · **V-Check:** alle (Common-Gate)
**Akzeptanz:** `test_disabled_flag_is_noop` und `test_absent_block_is_noop` grün; bei Abwesenheit
`false` (Präzedenz `scripts/lib/knowledge.py:127`); in Consumer-Projekten kein Schreibzugriff;
`checks.strict` bleibt in W1 **nicht** `true` (erst W3-4).
**Verifikation:** `python3 -m pytest tests/test_doc_renderer.py -q` → **0**;
`grep -n 'docs-consolidation' .meta-config/project.yaml` → **0**.
**Steps:**
- [x] 1: Tests schreiben (fail).
- [ ] 2: Fünf additive Keys anlegen. **⚠️ TEILWEISE — nicht abgehakt.** Gelandet ist nur
      `docs-consolidation.enabled: true` (separat autorisierte, eng zugeschnittene Gate-Änderung,
      außerhalb dieser Task genehmigt). **Offen:** `index-mode`, `checks.strict`, `sources`,
      `volatile-facts` (4 von 5 Properties).
- [x] 3: Tests grün beobachten; **kein** Sync-Lauf mit Schreibwirkung.
- [ ] 4: commit via `git`-Agent: `feat: add additive docs-consolidation config keys`.

> **LEDGER-Stand 2026-09-26 — W1-10 TEILWEISE erledigt (Fortschrittsnotiz, keine Änderung der
> Task-Semantik).** W1-10 ist **nicht** als Ganzes abgehakt. Stand der Landung:
> - **Testhälfte (Steps 1 und 3):** abgeschlossen — `test_disabled_flag_is_noop` und
>   `test_absent_block_is_noop` sind geschrieben und grün (`tests/test_doc_renderer.py`).
> - **Produktionshälfte (Step 2):** **nur teilweise.** In `.meta-config/project.yaml` steht
>   ausschließlich `docs-consolidation.enabled: true`. Diese Änderung wurde **nicht** als
>   Ausführung dieser Task, sondern als **separat autorisierte, eng zugeschnittene
>   Gate-Änderung** geliefert (Begründung: `enabled` wird von W2-7 als Common-Gate-Bedingung
>   gebraucht, `plan:1081`).
> - **Fehlend (4 von 5 Properties aus IC-22, `plan:904`):** `docs-consolidation.index-mode`,
>   `docs-consolidation.checks.strict`, `docs-consolidation.sources`,
>   `docs-consolidation.volatile-facts`. Der Schema-**Block** mit allen **sechs** Properties
>   existiert seit W1-9 (`config/project-config.schema.json`, `plan:881-899`) und ist
>   `additionalProperties: false` — die fehlenden vier Properties sind also **deklariert, aber
>   nicht gesetzt**. Konsequenz: `index-mode` (IC-15) und `sources` (IC-22, OQ2-Folge aus
>   `plan:570`) haben bis zu ihrer Lieferung keinen Wert; der Absenz-Default aus IC-22
>   (`plan:909-911`) greift. **Owner der Restlieferung:** `developer` im Rahmen von W1-10,
>   abhängig von W1-8 (bereits erledigt) — derzeit **blockiert** durch die offene
>   W3-`--strict`-Gate-Frage (siehe „Blockierende Befunde", **B-1**) und durch den Umstand,
>   dass `checks.strict` laut Akzeptanz (`plan:911`) erst in W3-4 auf `true` gesetzt werden darf.
>   Geführt als **E-13** in der konsolidierten Errata-Liste.
>   **Statuspflege Rev. 0.5 (K14):** die erste Blockadegrundlage („offene W3-`--strict`-Gate-Frage",
>   B-1) ist **entfallen** — B-1 ist geschlossen, das W3-Gate ist datei-bezogen
>   (**W3-GATE-SCOPE** als Dokuzeile / **W-GATE + W-GATE-TABLE** als verbindliches Kriterium,
>   RVW-1/RVW-14). **Es bleibt** die zweite Grundlage: `checks.strict` darf
>   erst in **W3-4** auf `true` gesetzt werden, und W3-4 setzt es **erst** nach **W2-1 Schritt 4**
>   (K16). Die Restlieferung von `checks.strict` selbst bleibt damit an W3-4 gebunden, **nicht**
>   an W1-10 — die Reihenfolge ist unverändert, nur die Begründung ist präzisiert.

---

## W2 — Checks V1–V7 (V1 startet WARNING)

**Verifikation W2 (erwartete Exit-Codes):**
- `python3 -m pytest tests/test_doc_facts.py tests/test_doc_facts_expected.py -q` → **0**
- ~~`python3 scripts/consistency-check.py` → **0**~~ ~~(V1 erscheint als **WARNING**)~~
  **AUFGEHOBEN durch Rev. 0.5 (K13) — der Klammer-Text war unbelegt** (V1 ist im Runner
  **nicht registriert**, `scripts/consistency-check.py:52-56`, und erscheint daher **nicht** im
  Report) — **und die Zeile selbst war unerreichbar (RVW-2).** Nach **W2-7** sind **V2**, **V3**
  und **V6** als **ERROR** registriert (IC-05); `print_report` gibt `1 if errors else 0`
  (`scripts/lib/consistency/report.py:75`, aufgerufen in `scripts/consistency-check.py:271`) ⇒
  der rohe Runner ist ab **W2-7** **planmäßig rot**. Die Zeile bleibt als Historie sichtbar;
  maßgeblich ist **W2-GATE-V1** (Zählung statt Exit-Code) **zusammen mit W2-GATE-ERRORS**
  (Zählung je V-Check, Erwartungswert, Termin, Owner) unten.
- ~~`python3 scripts/consistency-check.py --strict` → **1, planmäßig** — die **einzigen** Findings
  sind `docs.no_manual_counts`-V1-WARNINGS.~~ **AUFGEHOBEN durch Rev. 0.5 (K13) — der beschriebene
  Zustand existiert nicht.** Die Zeile bleibt als Historie sichtbar; maßgeblich ist das
  Abnahmekriterium **W2-GATE-V1** unten. Begründung der Aufhebung mit Beleg: **(a)** die
  Severity ist im Ist-Zustand **WARNING**, weil `v1_strict` `docs-consolidation.checks.strict`
  liest und bei Abwesenheit `False` liefert (`scripts/lib/consistency/docs.py:359`, `:314-326`)
  und `.meta-config/project.yaml:398-399` **nur** `enabled: true` setzt; **(b)** V1 ist im
  Runner **nicht registriert** — `scripts/consistency-check.py:52-56` importiert V1 **nicht**
  (`tests/test_doc_facts.py:2403-2422` pinnt das), der Runner emittiert also **kein**
  `docs.no_manual_counts`-Finding. Die alte Begründung „Spec A11 (V1 startet WARNING) und
  `scripts/consistency-check.py:23-26`" bleibt als **Spec-Bezug** gültig, trägt aber **nicht**
  die Exit-Code-Erwartung.
- ~~Der Gate-Nachweis `--strict == 0` erfolgt in W3.~~ **AUFGEHOBEN und ersetzt (Rev. 0.5,
  K13/K14/RVW-1):** in W3 gilt der **Spec-Scope**-Nachweis (`W3-GATE-SCOPE`, Dokuzeile) **zuzüglich**
  des **check-spezifischen** Doku-Gates (`W-GATE + W-GATE-TABLE`), **nicht** ein repo-globales
  `--strict == 0` und **nicht** das Aggregat `docs-findings: 0`
  (siehe Wellenblock **W3 — Verifikation**).
- ~~`python3 scripts/sync.py --validate` → **0** (`checks.strict` fehlt ⇒ Default `false` ⇒ keine Errors)~~
  **UMGESTELLT (dritte Korrekturrunde, RVW2-2) — die Zeile war unerreichbar und ihre Klammer
  unvollständig.** Die Klammer adressierte **nur V1** (dessen Severity ist ohne
  `checks.strict` tatsächlich `WARNING`, `docs.py:359`, `.meta-config/project.yaml:398-399`).
  Sie trug **nicht** für **V2, V3, V6**: diese sind nach **W2-7** registriert und **ERROR**
  (IC-05), und `python3 scripts/sync.py --validate` liefert genau dann **Exit 1**, wenn der
**gesamte** Runner mindestens ein ERROR-Finding liefert (`scripts/lib/cli_commands.py:975` →
`:171-174` → `:1056`/`:1058-1059`). **Maßgeblich ist `W-VALIDATE-ROT`** (Wellenblock
W2 — Verifikation): planmäßig rot von **W2-7** bis einschließlich **W8-2**, spätester Termin 0
**W8-4**, Owner `validator`; Grundlage **Spec §6(b) und der §10-Aufzählungspunkt `--validate`**, die ein Nicht-Grün-Sein
bei V1/V2/V3/V6 **ausdrücklich sanktionieren**. **Der Sollwert wird nicht abgesenkt, sondern
terminiert.** Die Zeile bleibt als Historie sichtbar.
- `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0** (6/6)

**W2-GATE-V1 (neu, Rev. 0.5, K13) — das verbindliche W2-Abnahmekriterium.**
`scripts/consistency-check.py` besitzt **keinen** Scope-/Pfadfilter (`--file` schließt alle
repo-weiten Checks aus, `scripts/consistency-check.py:185`), deshalb wird über die
maschinenlesbare Ausgabe gezählt. **Zähl-Kommando (bestandteil jedes Aufrufs):**

```bash
python3 scripts/consistency-check.py --json \
  | python3 -c 'import json,sys;d=json.load(sys.stdin);s=[f for f in d["findings"] if f["check"]=="docs.no_manual_counts"];print("v1-findings:",len(s));print("v1-severities:",sorted({f["severity"] for f in s}));print("v1-files:",sorted({f["file"] for f in s}))'
```

**Zum Exit-Code dieses Kommandos (RVW-12, verbindlich für alle Zähl-Kommandos der Rev. 0.5):**
Das Kommando ruft **kein** `sys.exit` — es ist damit bewusst **`sys.exit`-frei**. Ausgewertet
wird **ausschließlich der gedruckte Zählwert**. Das ist keine Formalie: `print_json_report`
liefert `1 if errors else 0` (`scripts/lib/consistency/report.py:99`), `main()` gibt diesen Wert
unverändert zurück (`scripts/consistency-check.py:268-276`) — aber in einer Pipeline
`A | B` ist der Exit-Code der **letzten** Komponente maßgeblich. Ein `sys.exit(0)` am Ende des
Konsumenten (wie in der Fassung vor diesem Review) hätte den Roh-Exit **neutralisiert** und
damit ein Exit-Code-Kriterium vorgetäuscht, das gar nicht prüfte. **Ein `sys.exit(0)` auf dem
Roh-Exit eines Zähl-Kommandos ist unzulässig.** Wer ein CI-Signal braucht, wertet den
**Zählwert** im selben Aufruf aus.

| Zustand | Erwartung | Erfolgskriterium (exakt) |
|---|---|---|
| **nach W2-1** — V1 implementiert, **nicht** registriert | `v1-findings: 0`, leere `v1-severities`, leere `v1-files`. **Kein** Severity-Wert ist beobachtbar, weil der Runner V1 nicht aufruft; die Severity-Aussage wird in dieser Phase **ausschließlich** am Unit-Nachweis geprüft. | `python3 -m pytest tests/test_doc_facts.py -q -k v1` → **0** (deckt `test_v1_positive_fixture_yields_exactly_four_findings` mit `Severity.WARNING` und `test_v1_is_not_wired_into_the_runner_yet`) **und** das Zähl-Kommando druckt `v1-findings: 0` |
| **nach W2-7** — V1 registriert, `checks.strict` weiterhin **nicht** gesetzt | `v1-findings:` **≥ 1** und `v1-severities:` **exakt** `['WARNING']`. Der Sprung 0 → ≥ 1 ist der Registrierungsnachweis. `v1-files` ⊆ {`README.md`, `llms.txt`, `ARCHITECTURE.md`} (`docs.py:158`) — **Dokuzeile, kein Prüfkriterium (RVW-15):** die Menge entsteht konstruktionsbedingt aus `V1_SCAN_RELPATHS`, kann also **nicht** fehlschlagen. | Zähl-Kommando druckt `v1-findings: ≥ 1` **und** `v1-severities: ['WARNING']`; zusätzlich `python3 -m pytest tests/test_doc_facts.py -q` → **0** und `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0** |

**Zeitliche Bindung beider Zustände (RVW2-5, ergänzt):** die Zeile „nach **W2-1**" gilt **nur bis
W2-7** — sie stützt sich auf `test_v1_is_not_wired_into_the_runner_yet`
(`tests/test_doc_facts.py:2403-2422`), den **W2-7 Schritt 1** durch den positiven
Registrierungs-Pin ersetzt. Ab W2-7 trägt die Registrierung der **positive** Pin; die
`v1-findings`-/`v1-severities`-Zählung ist davon **unberührt**.

**W2-GATE-ERRORS (neu, Rev. 0.5, RVW-2; präzisiert in der dritten Korrekturrunde, RVW2-1) — das
zweite W2-Abnahmekriterium: Befund- und Schweregrad-Zustand **aller** im Runner registrierten
Doku-Checks.** W2-GATE-V1 deckt **nur** V1 ab; die
unerreichbaren `consistency-check.py → 0`-Zeilen des W2-Blocks, von **W2-2** und von **W2-7**
betrafen dagegen die **ERROR**-Checks V2, V3 und V6. Beide Kommandos sind **ein** Aufruf:

```bash
python3 scripts/consistency-check.py --json \
  | python3 -c 'import json,sys,collections;d=json.load(sys.stdin);rows=[f for f in d["findings"] if f["check"].startswith("docs.")];c=collections.Counter(f["check"] for f in rows);print("docs-checks:",len(c));[print("  ",k,c[k],sorted({f["severity"] for f in rows if f["check"]==k})) for k in sorted(c)];print("docs-findings:",len(rows))'
```

**Erwartungswert bei W2-Abschluss (nach W2-7):**

| `check` (V) | Erwartung | Warum / Termin | Owner |
|---|---|---|---|
| `docs.no_manual_counts` (V1) | **≥ 1**, `['WARNING']` | Handzahlen werden erst in **W3-7** ersetzt | `developer` (W3-7) |
| `docs.docs_index_completeness` (V2) | **planmäßig rot** (ERROR) | `docs/INDEX.md` existiert **nicht** — Termin **W3-6** | `senior-developer` (W3-6) |
| `docs.internal_links` (V3) | **planmäßig rot** (ERROR) | `howto/setup/`, `howto/features/` existieren nicht — Termin **W8-2** | `developer` (W8-2) |
| `docs.readme_index` (V4) | **0** | bestehender Check, `docs/api`-Teilmenge bleibt Teilmenge; Name **belegt** (`docs.py:118`) | `developer` (W2-6) |
| `docs.role_generation_parity` (V5) | **0** | `compute_active_roles()` schließt das deaktivierte Gate (`project.yaml:12-13`) | `developer` (W2-4) |
| `docs.docs_facts_fresh` (V6) | **planmäßig rot** (ERROR) | generierte Blöcke existieren erst ab **W3-7** | `developer` (W3-7) |
| `docs.wiki_staleness` (V7) | **planmäßig rot** (WARNING) | **10** Wiki-Seiten `type: "Architecture"` ohne `derived-from` (gemessen 2026-09-26) — Termin **W5-3** | `tester` (W5-3) |

**`docs-checks` — die Zahl ist KEIN Registrierungsnachweis (RVW2-1, Blocker; korrigiert).**
Das Kommando oben zählt `len(collections.Counter(f["check"] for f in rows))` über die
**Findings** — es zählt damit die Anzahl **befundliefernder** `docs.`-Checks, **nicht** die Anzahl
**registrierter**. Ein registrierter, aber befundfreier Check erscheint im Counter **nicht**.
Die Fassung vor diesem Review führte `docs-checks` als „Anzahl registrierter Doku-Checks" mit
Sollwerten 7/7/7/7/8/8/9 und forderte an denselben Stellen `V4 = 0` und `V5 = 0` — bei W2-7 ist
der gedruckte Wert damit **5** (V1, V2, V3, V6, V7), gefordert waren 7. **Diese Kopplung ist
aufgehoben.** Es gelten drei getrennte Aussagen:
| Größe | Was sie misst | Sollwert | Beleg / Grenze |
|---|---|---|---|
| `docs-checks` (Counter) | Anzahl **befundliefernder** `docs.`-Checks **in diesem Lauf** | **kein Sollwert** — **Dokuzeile**. Der Wert ist per Konstruktion die Anzahl der Zeilen mit Erwartungswert ≠ 0 und damit aus der Einzelzählung **ableitbar**, nicht zusätzlich prüfbar | Kommando oben; `collections.Counter` über `d["findings"]` (`report.py:78-97`) |
| **Präsenzregel** (ersetzt die Registrierungszahl) | für jeden V-Check mit Erwartungswert **≠ 0** und ≠ `n. i.` muss eine Zeile `<check> <count> <severities>` **gedruckt** werden | **je Welle, aus W-GATE-TABLE** | Eine fehlende Zeile = fehlende Registrierung **oder** fehlende Findings — beides ist ein Befund |
| **Registrierungszahl** (Vollständigkeit V1…V9) | Anzahl **registrierter** Doku-Checks | **nicht gemessen, Messung erfolgt in Task W2-7** | **Aus dieser Quelle nicht messbar:** der Runner bietet keinen Registry-Dump (`scripts/consistency-check.py` kennt `--json`/`--strict`/`--file`/`--changed`, `:23-26`); die einzige Registrierungsstelle ist der Importblock `:52-56`, dessen Form nach W2-7 durch **keine** IC festgelegt ist. Owner `developer` (W2-7), Termin **W2-7** |

**Ist-Zustand 2026-09-26 (gemessen am Working Tree, Datei:Zeile):** `docs-checks: 0` **und**
`docs-findings: 0`. Begründung: V1 ist **nicht registriert**
(`scripts/consistency-check.py:52-56` importiert nur `check_readme_docs_index`,
`check_sync_cli_docs`, `check_ui_help_mappings`); der einzige heute registrierte Check mit
`docs.`-Präfix ist `check_readme_docs_index` mit `check="docs.readme_index"`
(`scripts/lib/consistency/docs.py:118`), und er liefert **0** Findings, weil alle **sieben**
`docs/api/*.md` bereits in `README.md:362-373` verlinkt sind. **Konsequenz:** die Aussage „V1…V7
implementiert" (IC-05) ist **nicht** gleichbedeutend mit „im Runner registriert"; die Registrierung
ist ein **eigener** Nachweis (Task **W2-7**) und wird **nicht** über `docs-checks` geführt.

**Vollständigkeitslücke der Präsenzregel — offen ausgewiesen, nicht kaschiert:** die Präsenzregel
erkennt eine fehlende Registrierung **nur** für Checks mit Erwartungswert ≠ 0. Für **V4** und
**V5** (Erwartungswert 0) ist eine fehlende Registrierung über diesen Weg **nicht** erkennbar.
Deren Registrierung wird deshalb auf Task-Ebene nachgewiesen — **W2-6** (V4) und **W2-4** (V5)
über ihre jeweiligen Unit-Tests, **W2-7** über den Registrierungs-Schritt und den Test
`test_exit_codes_unchanged_with_new_checks` (AC-13). Das ist **keine** Abschwächung eines
Sollwerts, sondern die Angabe, welche Aussage **wo** getragen wird.

**Zu den `check`-Namen (RVW2-1, präzisiert):** IC-05 legt `check="docs.<name>"` fest. **Belegt
am Code** sind heute: V1 = `docs.no_manual_counts` (`scripts/lib/consistency/docs.py:155`,
`V1_CHECK_ID`) und V4 = **`docs.readme_index`** (`scripts/lib/consistency/docs.py:118` — der heute
registrierte `check_readme_docs_index`; die Tabelle dieses Plans führte bis zur zweiten
Korrekturrunde den **abgeleiteten** Namen `docs.readme_docs_index`, der so **nicht** im Code steht
und hier auf den belegten Namen korrigiert ist). Für V3 ist der Name durch Plan Task **W2-2** (`check="docs.internal_links"`)
festgelegt. Die Namen der übrigen Checks (**V2, V5, V6, V7, V8, V9**) sind die Ableitung dieses
Musters aus den in IC-05 genannten Funktionsnamen (`check_<x>` → `docs.<x>`). Sie sind damit
**abgeleitet, nicht hier festgelegt**: weicht die Implementierung ab, ist der abweichende Name
im **W2-7-Review-Protokoll** als Ist-Angabe festzuhalten. Das **Kriterium ist der Zählwert**,
nicht der String — ein abweichender Name ändert die Aussage nicht, solange er eindeutig
zuordenbar bleibt. **Für die Präsenzregel (RVW2-1) ist der String die Schlüssel:** die
Prüfung liest die gedruckten Zeilen und vergleicht sie mit der Tabelle; ein abweichender Name wird
deshalb im W2-7-Review-Protokoll als `W-GATE-TABLE-ABWEICHUNG` festgehalten und die Tabelle
danach auf den Ist-Namen gezogen.

**W-VALIDATE-ROT (neu, dritte Korrekturrunde, RVW2-2 — Blocker) — die verbindliche Regel für
`python3 scripts/sync.py --validate` in allen Wellen W2…W8.** Die Regel steht hier, weil W2 die
**erste** betroffene Welle ist, und gilt **wortgleich** für W3, W4, W5, W6, W7 und W8.

**Mechanik (gemessen am Code, 2026-09-26):** `_handle_validate` ruft
`_run_consistency_checks(agent_meta_root)` (`scripts/lib/cli_commands.py:975`); diese führt den
**gesamten** Runner aus und gibt die **Anzahl der ERROR-Findings** zurück
(`:171-174`, `sum(1 for f in findings if f.severity == Severity.ERROR)`); der Exit folgt daraus mit
`sys.exit(1 if (consistency_errors or _strict_exit_code) else 0)` (`:1056`) bzw. `sys.exit(1)`
(`:1058-1059`). **Folge:** `python3 scripts/sync.py --validate` → **0** verlangt **null
ERROR-Findings im ganzen Repo** — nicht nur in den Doku-Checks.

**Regel:** `python3 scripts/sync.py --validate` ist **planmäßig rot** von **W2-7** (dem ersten
Lauf mit registrierten Doku-Checks) **bis einschließlich W8-2**. Verursachende Doku-Checks mit
Termin und Owner:

| Zeitraum | Planmäßig rote Doku-ERROR-Checks | Erster Termin 0 | Owner |
|---|---|---|---|
| **W2-7 … W3-6** | **V2** (bis zum Sync in **W3-6**, Schritt 2), **V3**, **V6** | V6 → **W3-7**; V2 → **W3-6**; V3 → **W8-2** | `developer` (V6) · `senior-developer` (V2) · `developer` (V3) |
| **W3-7 … W8-1** | **V3** (durchgehend bis W8-2) · **V2** ist nach W3-6 0, in **W4** und **W5** erneut rot und jeweils erst mit dem Abschluss-Sync-Lauf wieder 0 (W4-3 Schritt 4 / W5-2 Schritt 4 — Fußnote ¹ der `W-GATE-TABLE`); V6 ab W3-7 0 | **W8-2** (V3 geht auf 0; **V2** bleibt bis **W8-4 Schritt 5** rot — nächste Zeile) | `developer` (V3) · `senior-developer` (V2) |
| **W8-2 … W8-4** | **V2** — W8-1 legt `docs/plans/…-oq4.md` an und bearbeitet `docs/REQUIREMENTS.md`; **W8-2** und **W8-3** führen **keinen** Sync, V2 bleibt dort rot. V9 ist **WARNING** und bricht `--validate` **nicht** (die Zählung `:174` filtert auf `Severity.ERROR`) | **W8-4** — V2 in **Schritt 5** (Abschluss-Sync-Lauf; **nicht** Schritt 4) | `tester` |

**Lesehinweis zur dritten Zeile (RVW3-1, vierte Korrekturrunde):** die Zeile nennt **V2**, weil V2
der letzte planmäßig rote Doku-ERROR-Check ist. Die Regelzeile oben endet mit „bis einschließlich
W8-2" **nicht**, weil dort alles grün wäre, sondern weil **V3** (Termin W8-2) der letzte rote Check
des Intervalls W2-7…W8-2 ist. In **W8-3** und in **W8-4 bis Schritt 5** bleibt `--validate` deshalb
weiterhin planmäßig rot; der erste Termin 0 für `--validate` ist damit **W8-4 Schritt 5** und steht
unter der Bedingung von W3-BASELINE-STRICT (b) (unten). **Kein** Sollwert wurde geändert.

**Grundlage (spec-zitiert, nicht eigene Setzung):** Spec §6(b) und der §10-Aufzählungspunkt
`--validate` **sanktionieren**
ausdrücklich, dass `--validate` bei **V1, V2, V3, V6** nicht grün ist
(„darf bei **V1, V2, V3, V6** nicht grün sein (ab W3; in W2 V1 noch WARNING)"; `--validate` ist
`TEST_COMMAND`, `.meta-config/project.yaml:193`). Der Sollwert `→ 0` wird **nicht** abgesenkt,
sondern **terminiert**: erst **nach** W8-4, und auch dann **nur unter der Bedingung** von
W3-BASELINE-STRICT (b): ist der repo-weite ERROR-Altbestand `> 0`, bleibt `→ 0` unerreichbar und
maßgeblich ist die **Deltasperre** (`errors` darf nicht steigen). **Owner** der Messung und der
Deltasperre: `validator`; **Termin** der Erstentscheidung: **W3-7** (mit der Baseline-Messung),
**spätester Termin 0**: **W8-4**.

**Ausdrücklich nicht von dieser Regel erfasst:**
- `python3 scripts/sync.py --check` — der Drift-Lauf, **nicht** der Consistency-Runner
  (RVW2-13, siehe Wellenblock W3). Er wird rot, wenn generierte Dateien vom Ist abweichen, und
  sagt **nichts** über V1–V9 aus.
- `python3 scripts/sync.py --dry-run` — führt die Consistency-Suite **nicht** aus
  (`_run_consistency_checks` wird nur in `_handle_validate` aufgerufen,
  `scripts/lib/cli_commands.py:975`); die Zeile `--dry-run → 0` ist von ERROR-Checks **nicht**
  abhängig.
- `python3 scripts/consistency-check.py` **ohne** `--validate` — roher Runner-Exit, bereits über
  `W2-GATE-ERRORS` und den Dokuzeile-Termin **W8-2** geregelt.


**Warum `≥ 1` belegbar ist:** `README.md:122` (`## Agent Roster — 74 Generic Agents`) liegt
außerhalb jedes Fenced-Blocks und außerhalb jeder Marker-Region und ist damit ein
V1a-Treffer (`docs.py:219-233`, `:256-273`); `ARCHITECTURE.md:3`
(`> Repo version: **0.92.0** — content last substantively reviewed: …`) ist ein V1b-Treffer
(`docs.py:383-390`). Der Wert **0** ist damit nach W2-7 **kein** erfüllbarer Zustand — er
würde eine Regression der Registrierung bedeuten.

**Wann die Severity kippt — und warum das W2-Gate davon unberührt ist:** `checks.strict: true`
wird erst in **W3-4** gesetzt. Erst dann liefert `v1_strict` `True` und `docs.py:359` emittiert
`Severity.ERROR`. Das W2-Gate läuft **vor** W3-4 und erwartet deshalb zu Recht `WARNING`; ein
W2-Gate, das `ERROR` erwartete, wäre unerfüllbar. **Nach** W3-4 dreht **dieses** Kriterium seine
Erwartung auf `v1-severities: ['ERROR']` — die Umstellung wird als Bestandteil von **W3-4**
geführt, **nicht** stillschweigend vorgenommen.

**Was dieses Kriterium nicht leistet (bewusst offengelegt):** es zählt über die
**V1-Erkennung**, nicht über die **V1-Abdeckung**. Dass die Fundstellen F2, F3-Site-2 und F4 im
Directory-Structure-Fence für V1 **unsichtbar** sind, ist **B-4** und wird als **Schritt 4 der
Task W2-1** geschlossen (Rev. 0.5, K16) — **vor** der Hochstufung auf `ERROR` in W3-4. Ohne
diesen Schritt ist das W2-Gate erfüllbar und trotzdem **nicht** beweiskräftig für
„11 Handzahlen = 0"; dieser Vorbehalt bleibt bis zum Abschluss von K16 in Kraft.

**Review W2:** `tester` (Fixture-Treue) → `code-reviewer` → `validator` (AC-07…AC-13, AC-36).
**Gate bei CHANGES_REQUESTED:** jeder Fehlalarm in der Positiv-Fixture ⇒ `concept-reviewer`; jeder
nicht spezifizierte Treffer ⇒ R4-Eskalation an `main_chat`, Startseverity bleibt WARNING.
**Rollback W2:** `docs-consolidation.checks.strict: false`; da die Checks an
`docs-consolidation.enabled` gebunden sind, ist der vollständige Rollback `enabled: false`
(Fail-off ⇒ V1–V7 No-op). `git rm tests/fixtures/docs_v1_fixtures.md`;
`scripts/lib/consistency/docs.py` und `scripts/consistency-check.py` via `git checkout`.
**Rev. 0.5 (K15):** im W2-Rollback ist zusätzlich `scripts/lib/consistency/report.py` via
`git checkout` zurückzusetzen — die `line`/`branch`-Felder sind additiv und ohne Codeverlust
revertierbar.

### W2-1: V1a/V1b `check_no_manual_counts` + Positiv-Fixture

**Files:** Modify `scripts/lib/consistency/docs.py`, `tests/test_doc_facts.py`;
Create `tests/fixtures/docs_v1_fixtures.md`
**Interfaces:** Produces: `check_no_manual_counts(root, config=None) -> list[Finding]` mit zwei
disjunkten Branches und `branch`-Attribut `V1a`/`V1b`; Suppressionsregeln 1–4 (§5.1.1) **in der
durch Rev. 0.5 eingegrenzten Fassung** — Regel 3 bleibt in Kraft, wird aber so eingegrenzt, dass
die vier Directory-Structure-Fundstellen `README.md:688/:690/:696/:734` für V1 sichtbar werden,
**ohne** die Regeln 1, 2 und 4 aufzuweichen (Schritt 4, K16; die Mechanismus-Wahl ist
Implementierungsgegenstand, kein Vorgegebenes).
Consumes: W1-4, W0-4 (Track-A-Merge als Vorbedingung für die Fixture).
**Agent:** developer · **Depends on:** W1-6, W0-4 · **parallel_group:** PG-2 / W2
**Ziel-AK (AC):** **AC-07**, **AC-08** (IC-05, §5.1.1) · **V-Check:** **V1a**, **V1b**
**Akzeptanz:** Fixture mit **genau vier** wörtlichen Zitatzeilen (Zeilen 1–4: `## Agent Roster — 74
Generic Agents`, `## Hooks (7 hooks, propagated to all providers)`,
`  ai-providers.yaml          # 6 provider configs (Claude, Gemini, Opencode, Continue, Copilot,
Mammouth)`, `VERSION                      # Current version (v1.0.0)`). Ergebnis = **genau 4**
Findings, `severity=WARNING`, `check="docs.no_manual_counts"`, `line` 1/2/3 = `V1a`, `line` 4 =
`V1b`. Die drei Suppressionsfälle (Marker-Region, `docs-exempt`, Fenced-Code) erzeugen **kein**
Finding; die Gegenprobe `| Agents | 74 |` außerhalb jeder Region erzeugt **genau eines**. Nach
`checks.strict: true` sind dieselben vier Befunde `Severity.ERROR`.
**Akzeptanz, neu (Rev. 0.5, K16 — B-4/E-14, Sichtbarkeit der README-Facts):** Die drei
Suppressionsfälle bleiben unangetastet — insbesondere erzeugt der Fence-Fall
`## Hooks (7 hooks)` **weiterhin kein** Finding (AC-08) —, **und** V1 wird für die vier
Directory-Structure-Fundstellen `README.md:688` (F2), `:690` (F3-Site-2), `:696` und `:734`
(F4) **sichtbar**. Nachweis: ein **negativer** Test, der gegen die **unmarkierte** Ist-Fassung
mindestens **einen** `docs.no_manual_counts`-Befund je Fundstelle erwartet (V1a für `:688`,
`:690`, `:696`; V1b für `:734`). **Die Eingrenzung von Suppressionsregel 3 ist
Implementierungsgegenstand, nicht Vorgabe:** zulässig ist jeder Mechanismus, der beide
Fixtures (AC-07 grün, AC-08 grün) und den Sichtbarkeitsnachweis erfüllt; **kein** Mechanismus
darf die Regeln 1 (Region), 2 (`docs-exempt`) und 4 (generierte Datei) aufweichen. Die
Mechanismus-Wahl wird **begründet** in der LEDGER-Stand-Notiz dieser Task festgehalten; passt
kein Kandidat, geht die Entscheidung an `orchestrator` (keine stille Wahl). **Ohne diesen
Schritt darf W3-4 `checks.strict: true` nicht setzen** (Vorbedingung, siehe Task **W3-4**).
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**;
`wc -l < tests/fixtures/docs_v1_fixtures.md` → **4**.
**Steps:**
- [x] 1: Fixture (Positiv + Exempt + Gegenprobe) anlegen; Tests schreiben (fail).
- [x] 2: V1a (Zahl-Token ohne `\d+\.\d+` + Nomen auf derselben Zeile) und V1b (Versions-Literal)
      implementieren. Die Rev.-0.1-Regex wird **nicht** verwendet (sie matchte keine Fundstelle).
- [x] 3: Suppressionen implementieren; Tests grün beobachten.
- [ ] 4: **K16 / B-4 — Suppressionsregel 3 so eingrenzen, dass die vier README-Fundstellen
      `:688/:690/:696/:734` für V1 sichtbar werden**, ohne AC-08 (Fence-Fall bleibt ohne
      Finding) und ohne die Regeln 1, 2 und 4 zu verletzen; Negativ-Test gegen die unmarkierte
      Ist-Fassung schreiben; Mechanismus-Wahl in der LEDGER-Stand-Notiz begründet festhalten.
- [ ] 5: commit via `git`-Agent: `feat: add V1 manual count detection with fixtures`. Die
      Regel-3-Eingrenzung aus Schritt 4 wird als **eigener** Commit geliefert, damit
      W2-1-Umsetzung und K16-Korrektur getrennt revertierbar bleiben.

> **LEDGER-Stand 2026-09-26 — W2-1 TEILWEISE erledigt (Fortschrittsnotiz, keine Änderung der
> Task-Semantik).** Die Implementierungshälfte (Steps 1–3) ist gelandet:
> `check_no_manual_counts` mit den disjunkten Branches V1a/V1b, den Suppressionsregeln 1–4
> (§5.1.1) und der Positiv-Fixture `tests/fixtures/docs_v1_fixtures.md` (existiert).
> **Offen sind zum Zeitpunkt dieses Eintrags Schritt 4 (K16 / B-4 — Rule-3-Eingrenzung) und
> Schritt 5 (Commit)** — RVW2-10: die Fassung davor nannte hier fälschlich „ausschließlich Step 4
> (Commit)"; nach der Einfügung von Schritt 4 in Rev. 0.5 (K16) ist der Commit **Schritt 5**, wie
> L-1 bereits korrekt führt. W2-1 ist damit **nicht** als Ganzes abgehakt, und das Wellen-Gate W2
> (Abschnitt **W2 — Verifikation**) ist **nicht** erreicht.
> **Zwei Review-Befunde aus der W2-1-Prüfung sind offen und blockieren den Abschluss:**
> **B-4** (V1-Abdeckungslücke: Suppressionsregel 3 „fenced code" verdeckt `README.md:688/690/696/734`,
> d. h. IC-05-Befunde F2, F3-Site-2 und F4 sind für V1 unsichtbar — Remediation-Owner **W3-7**,
> **vor** der Hochstufung von V1 auf `ERROR`) und **B-5** (`scripts/lib/consistency/report.py`
> erscheint in **keiner** `Files:`-Liste des Plans — der F1-Verlust von `line`/`branch` im
> `--json`-Output hat derzeit keinen Owner). Beide sind im Abschnitt „Blockierende Befunde"
> mit Evidenz verankert.
>
> **Nachtrag Rev. 0.5 (2026-09-26, K13/K15/K16) — die Zuordnung oben ist überholt, der
> Befund-Text bleibt Historie.** (a) **B-4** ist von „Remediation-Owner **W3-7**" auf
> **W2-1, Schritt 4** gewechselt: W3-7 ersetzt die **Zahlen**, nicht die **Sichtbarkeit** —
> eine Erkennung, die die Fundstellen nicht sieht, kann W3-7 weder belegen noch verhindern;
> die Zuweisung an W3-7 hätte die Lücke erst **nach** W3-4 geschlossen. (b) **B-5** hat jetzt
> den Owner **W2-7** (Dateianennung in `Files:`, Abnahmekriterium **F1-PROMOTION**). (c) **Neu
> und für das Wellen-Gate entscheidend:** der oben genannte Zustand „W2-Gate nicht erreicht"
> bleibt richtig, seine **Begründung** war unvollständig — V1 ist im Runner **nicht
> registriert** (`scripts/consistency-check.py:52-56`), weshalb `consistency-check.py`
> derzeit **kein** `docs.no_manual_counts`-Finding ausgibt; und die Severity ist im
> Ist-Zustand **WARNING**, nicht ERROR (`docs.py:359`, `.meta-config/project.yaml:398-399`).
> Das verbindliche Abnahmekriterium steht als **W2-GATE-V1** im Wellenblock **W2 — Verifikation**.

### W2-2: V3 `check_internal_links`

**Files:** Modify `scripts/lib/consistency/docs.py`, `tests/test_doc_facts.py`
**Interfaces:** Produces: `check_internal_links(root, config=None) -> list[Finding]`; prüft nur
relative repo-interne Pfade. Consumes: W2-1.
**Agent:** developer · **Depends on:** W2-1 · **parallel_group:** PG-2 / W2
**Ziel-AK (AC):** **AC-09** (IC-05) · **V-Check:** **V3**
**Akzeptanz:** `test_v3_flags_dead_howto_links` grün: `README.md:721-723` (Links auf
`howto/setup/`, `howto/features/`) liefert ≥ 1 `Finding(severity=ERROR,
check="docs.internal_links", file="README.md")`. `http(s)://`, `mailto:` und `#anchor` werden
**nicht** geprüft (R6). Die Behebung erfolgt in W8-2.
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**;
~~`python3 scripts/consistency-check.py --strict` → **1, planmäßig** (V1-WARNINGS **plus**
V3-ERROR auf `README.md:721-723`, das erst W8-2 behebt — im Review als erwartet markieren).~~
**Ergänzung Rev. 0.5 (K13/RVW-2):** vor **W2-7** gibt es im Runner **keine** V1-Findings
(nicht registriert), der V1-Anteil dieses Exit-Code-1 ist also **erst nach W2-7** zu erwarten.
Die Zeile bleibt als Historie sichtbar; maßgeblich sind **W2-GATE-V1** und **W2-GATE-ERRORS**
(beide im Wellenblock **W2 — Verifikation**). **Diese Task-Zeile ist für sich genommen kein
Welle-Gate** (RVW-3) — sie prüft die Implementierung, nicht den Wellenabschluss.
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: V3 implementieren; Scope `docs/**` + `README.md` + `llms.txt`.
- [ ] 3: Test grün beobachten; Fehlalarm-Probe auf `http(s)://` und Anker.
- [ ] 4: commit via `git`-Agent: `feat: add V3 internal link check`.

### W2-3: V7 `check_wiki_staleness`

**Files:** Modify `scripts/lib/consistency/docs.py`, `tests/test_doc_facts.py`
**Interfaces:** Produces: `check_wiki_staleness(root, config=None) -> list[Finding]`, Severity
**WARNING**. Consumes: W1-4 (`compute_wiki_staleness`).
**Agent:** developer · **Depends on:** W2-2 · **parallel_group:** PG-2 / W2
**Ziel-AK (AC):** **AC-10** (IC-05) · **V-Check:** **V7**
**Akzeptanz:** `test_v7_missing_and_stale_derived_from` grün: `type: Architecture` **ohne**
`derived-from` ⇒ Finding; `derived-from` mit `mtime(Quelle) > derived-at` ⇒ Finding nennt
`stale-source`. Die Behebung (Annotation) erfolgt in W5-3.
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**;
~~`python3 scripts/consistency-check.py` → **0** (nur WARNINGs).~~
**AUFGEHOBEN (Rev. 0.5, RVW-2) — die Klammer war sachlich falsch und die Zeile unerreichbar.**
V7 ist zwar WARNING, aber W2-3 folgt auf **W2-2**: sobald V3 registriert ist, meldet
`check_internal_links` auf `README.md:721-723` einen **ERROR** (Task **W2-2**-Akzeptanz), und
`print_report` gibt `1 if errors else 0` (`scripts/lib/consistency/report.py:75`) — der rohe
Runner ist damit Exit **1**, nicht 0. Die Zeile bleibt als Historie sichtbar; maßgeblich ist
**W2-GATE-ERRORS** (Erwartungswert `docs.wiki_staleness` planmäßig rot, Termin **W5-3**,
Owner `tester`; V3 planmäßig rot, Termin **W8-2**). **Diese Task-Zeile ist für sich genommen
kein Welle-Gate** (RVW-3).
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: V7 als dünne Adapter-Schicht auf W1-4 implementieren.
- [ ] 3: Test grün beobachten.
- [ ] 4: commit via `git`-Agent: `feat: add V7 wiki staleness check`.

### W2-4: V5 `check_role_generation_parity` (gate-bewusst)

**Files:** Modify `scripts/lib/consistency/docs.py`, `tests/test_doc_facts.py`
**Interfaces:** Produces: `check_role_generation_parity(root, config=None) -> list[Finding]`;
Severity **ERROR**, sobald `systems-engineering.enabled: true`, sonst **WARNING**. Consumes: W1-3.
**Agent:** developer · **Depends on:** W2-3 · **parallel_group:** PG-2 / W2
**Ziel-AK (AC):** **AC-11** (IC-05) · **V-Check:** **V5**
**Akzeptanz:** `test_v5_severity_depends_on_se_gate` grün; Vergleichsmenge ist
`compute_active_roles()` (IC-04), **nicht** der `roles:`-Listeninhalt (F21-Dauerfehlalarm, NG-8).
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**.
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: V5 mit Gate-Auswertung implementieren.
- [ ] 3: Test grün beobachten; Ist-Zustand (F13) muss **WARNING** sein.
- [ ] 4: commit via `git`-Agent: `feat: add V5 gate-aware role parity check`.

### W2-5: V6 `check_docs_facts_fresh` inkl. Sollwert-Vergleich

**Files:** Modify `scripts/lib/consistency/docs.py`, `tests/test_doc_facts_expected.py`
**Interfaces:** Produces: `check_docs_facts_fresh(root, config=None) -> list[Finding]` mit
`kind ∈ {handedit, expected-mismatch, missing-in-expected}`; `missing-in-expected` = **WARNING**,
die anderen **ERROR**. Consumes: W1-5, W2-4.
**Agent:** developer · **Depends on:** W2-4 · **parallel_group:** PG-2 / W2
**Ziel-AK (AC):** **AC-36** (IC-23, R14) · **V-Check:** **V6**
**Akzeptanz:** `test_mismatch_is_reported` grün: manipulierter Sollwert ⇒ **genau ein** Finding
`severity=ERROR, kind="expected-mismatch"` **obwohl** der gerenderte Block exakt
`compute_doc_facts()` entspricht — der Nachweis, dass der Kreis `doc_facts → Renderer → V6`
gebrochen ist (R14).
**Verifikation:** `python3 -m pytest tests/test_doc_facts_expected.py -q` → **0**.
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: V6 mit beiden Vergleichsachsen implementieren.
- [ ] 3: Tests grün beobachten.
- [ ] 4: commit via `git`-Agent: `feat: add V6 freshness check with expected-value axis`.

### W2-6: V2 `check_docs_index_completeness` und V4-Erweiterung

**Files:** Modify `scripts/lib/consistency/docs.py`, `tests/test_doc_facts.py`
**Interfaces:** Produces: `check_docs_index_completeness(root, config=None) -> list[Finding]`;
`check_readme_docs_index` generalisiert von `docs/api/*.md` (`:111`) auf den gesamten `docs/`-Baum
bei **unveränderter** Signatur und Severity. Consumes: W2-5, W1-8.
**Agent:** developer · **Depends on:** W2-5 · **parallel_group:** PG-2 / W2
**Ziel-AK (AC):** **AC-12** (IC-05) · **V-Check:** **V2**, **V4**
**Akzeptanz:** `test_v2_missing_page` grün: eine getrackte `docs/**/*.md` außerhalb `archive/`, die
in `docs/INDEX.md` fehlt ⇒ **ERROR**; `docs/INDEX.md` selbst und `archive/`-Pfade ⇒ **kein**
Finding. Die bisherige Teilmenge `docs/api/*.md` bleibt eine echte Teilmenge der neuen Prüfung.
**Spec-Treue:** §9.1 führt AC-12 auf W3; die **Implementierung** liegt hier (Fixture-Ebene, damit
`scripts/lib/consistency/docs.py` nicht von zwei parallelen Ketten geschrieben wird), der
**E2E-Nachweis gegen das reale `docs/INDEX.md`** in W3-6.
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: V2 implementieren; V4 generalisieren.
- [ ] 3: Tests grün beobachten; Szenario-Asserts 50–56 **nicht** anfassen (NG-10).
- [ ] 4: commit via `git`-Agent: `feat: add V2 index completeness and generalize V4`.

### W2-7: Registrierung, Common-Gate und Exit-Codes

**Files:** Modify `scripts/lib/consistency/docs.py`, `scripts/consistency-check.py`,
`scripts/lib/consistency/report.py` (**neu in Rev. 0.5, K15**), `tests/test_doc_facts.py`
(**RVW2-5:** die Datei trägt zusätzlich den **Nicht-Registrierungs-Pin**
`test_v1_is_not_wired_into_the_runner_yet`, `:2403-2422`, der in **Schritt 1** durch den positiven
Registrierungs-Pin ersetzt wird — dieselbe Datei, **kein** neues File-Ownership)
**Interfaces:** Produces: Registrierung V1…V9 mit `check="docs.<name>"`; Common-Gate (No-op, wenn
`docs-consolidation.enabled != true`); unveränderter Exit-Code-Vertrag; **neu:** `Finding.line`
und `Finding.branch` als **Dataclass-Felder** mit Default (Default `""`/`None`, damit alle
**bestehenden** Konstruktoraufrufe unverändert bleiben) und ihre Serialisierung in
`print_json_report`. Consumes: W2-6, W1-10, W2-1 (K16-Rule-3-Eingrenzung, weil
`_v1_finding` in `docs.py:329-347` dieselben Felder setzt).
**Agent:** developer · **Depends on:** W2-6 · **parallel_group:** PG-2 / W2
**Ziel-AK (AC):** **AC-13** (IC-05), **AC-24** · **V-Check:** alle
**Akzeptanz:** `test_exit_codes_unchanged_with_new_checks` grün: 0 Errors → Exit **0**, genau 1
Error → Exit **1**, Skriptfehler → Exit **2**; bestehende Exit-Code-Doku
(`scripts/consistency-check.py:23-26`) bleibt gültig; in allen Szenario-Fixtures sind V1–V9
**vollständig No-op** (AC-38). Die bestehenden drei Checks
(`check_sync_cli_docs` `:9`, `check_ui_help_mappings` `:47`, `check_readme_docs_index` `:100`)
bleiben in Signatur und Severity unverändert.
**Akzeptanz, neu (Rev. 0.5, K15 — F1-PROMOTION, B-5/E-15):** `line` und `branch` sind
**Dataclass-Felder** von `Finding` (`scripts/lib/consistency/report.py:28-41`), **keine**
Instanzattribute mehr; `print_json_report` (`:78-97`) serialisiert **beide** mit; `docs.py:329-347`
setzt sie über den Konstruktor. **Nachweis:** ein Test, der für ein V1-Finding
`json.loads(consistency-check.py --json)` prüft und **beide** Schlüssel `line` und `branch`
im Finding-Objekt findet — der heutige Zustand verwirft sie (Feldliste ohne `line`/`branch`).
**Kein** Regressionsrisiko für andere Checks: die beiden neuen Felder sind **optional**
(Defaults), die `print_report`-Ausgabe bleibt unverändert (`__str__` zeigt sie weiterhin nur
über `message`, `tests/test_doc_facts.py:2269-2272` bleibt damit grün). **Verantwortung:**
W2-7 besitzt damit **Registrierung, Common-Gate und Finding-Kontrakt** — das ist die einzige
Task, die ein Gate-Werkzeug end-to-end verantwortet; eine eigene Task wäre eine zusätzliche
Welle ohne zusätzliche Entscheidung.
**Akzeptanz, neu in der dritten Korrekturrunde (RVW2-5 — der Nicht-Registrierungs-Pin wird von
dieser Task zwingend rot; **keine** neue Task, Zuordnung an den **bestehenden** W2-7):**
`tests/test_doc_facts.py:2403-2422` (`test_v1_is_not_wired_into_the_runner_yet`, Assertion
`"check_no_manual_counts" not in runner`) pinnt den **Ist-Zustand vor dieser Task**. W2-7
registriert V1 und macht den Test damit **zwangsläufig rot** — und `python3 -m pytest
tests/test_doc_facts.py -q` ist zugleich das **W2-Wellen-Gate**. **Verbindlich:** der Pin wird in
**Schritt 1** dieser Task durch einen **positiven** Registrierungs-Pin ersetzt, nicht entfernt:
`test_v1_is_registered_in_the_runner` mit (a) `"check_no_manual_counts" in runner` — Import- bzw.
Registrierungsnachweis in `scripts/consistency-check.py:52-56` — **und** (b) `docs.no_manual_counts`
im `findings[]` eines Fixture-Laufs mit `docs-consolidation.enabled: true` (Common-Gate **an**).
Der alte Test wird **nicht** parallel weitergeführt; seine Historie bleibt im Testmodul als
Kommentar mit Abschnittsanker. **Abhängigkeit von AC-13/AC-38 — geprüft und unverändert:** AC-13
(„V1–V9 registriert, Exit-Code-Vertrag unverändert") ist genau die Aussage, die der neue positive
Pin trägt; AC-38 (Szenarien 50/51/52/54/55/56 **vollständig No-op**) bleibt grün, weil die
Szenario-Fixtures `docs-consolidation.enabled` **nicht** setzen (IC-22, Fail-off) — der positive
Pin läuft gegen ein **eigenes** Fixture, **nicht** gegen ein Szenario. **Kein** AC und **kein**
Sollwert wird dadurch verändert.
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**;
~~`python3 scripts/consistency-check.py` → **0**~~
**AUFGEHOBEN (Rev. 0.5, RVW-2) — unerreichbar.** W2-7 registriert V1–V7; V2, V3 und V6
sind **ERROR** (IC-05), und `print_report` gibt `1 if errors else 0`
(`scripts/lib/consistency/report.py:75`) ⇒ der rohe Runner ist ab W2-7 planmäßig Exit **1**.
Maßgeblich ist **W2-GATE-ERRORS** (Erwartungswert je V-Check, Termin, Owner). **Dokuzeile zum
spätesten Termin, zu dem der rohe Runner `Exit 0` liefert: W8-2** (letzter ERROR-Check ist V3) —
Owner `developer`; das ist **kein** W2-Kriterium, sondern die Terminierung des
Altbestands-Zustands. **Diese Task-Zeile ist für sich genommen kein Welle-Gate** (RVW-3);
`bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0**;
`python3 scripts/consistency-check.py --json | python3 -c 'import json,sys;d=json.load(sys.stdin);print(sorted({k for f in d["findings"] for k in f}))'` → enthält `line` **und** `branch` (F1-PROMOTION, vacuously grün, solange `docs-consolidation.enabled: false` — dann mit dem pytest-Nachweis kombinieren).
**Steps:**
- [ ] 1: Test schreiben (fail). **RVW2-5 (verbindlich in dieser Task):** den
      Nicht-Registrierungs-Pin `test_v1_is_not_wired_into_the_runner_yet`
      (`tests/test_doc_facts.py:2403-2422`) durch den **positiven** Registrierungs-Pin
      `test_v1_is_registered_in_the_runner` ersetzen (Import in `consistency-check.py` **und**
      `docs.no_manual_counts` im `findings[]` eines Fixture-Laufs mit `enabled: true`); den
      ausgeliehen Test **nicht** löschen, sondern im Testmodul kommentieren.
- [ ] 2: Checks registrieren; Common-Gate als erste Bedingung in jeden Check einziehen.
      **RVW2-1:** die Registrierung ist damit der **einzige** Nachweis der Registrierungszahl —
      `docs-checks` im W-GATE zählt befundliefernde Checks und ist **kein** Registrierungsnachweis.
- [ ] 3: Tests grün beobachten; Szenario-Lauf beobachten.
- [ ] 4: **K15 / B-5 — `line` und `branch` in `report.py` zu Dataclass-Felder mit Default
      machen, in `print_json_report` serialisieren und `_v1_finding` (`docs.py:329-347`) auf
      den Konstruktor umstellen**; F1-PROMOTION-Test schreiben (grün beobachten).
- [ ] 5: commit via `git`-Agent: `feat: register docs checks behind fail-off common gate`.

---

## W3 — Generator, Stage, Drift-Store, Index-Erzeugung

**Verifikation W3 (erwartete Exit-Codes):**
- `python3 -m pytest tests/test_doc_renderer.py tests/test_generated_file_drift_docs.py -q` → **0**
- `python3 scripts/sync.py --dry-run` → **0**, `written` nur als `would-update`. **Bleibt
  unberührt (RVW2-2):** `--dry-run` führt die Consistency-Suite **nicht** aus —
  `_run_consistency_checks` wird ausschließlich in `_handle_validate` aufgerufen
  (`scripts/lib/cli_commands.py:975`); die Zeile ist von ERROR-Checks **nicht** abhängig.
- ~~`python3 scripts/sync.py --check` → **planmäßig 1** im Intervall W3-4…W3-6 (V1/V2/V6 noch rot;
  Spec §6(b): `--check`/`--validate` *dürfen* ab W3 bei V1/V2/V3/V6 nicht grün sein), **0** ab W3-7~~
  **KORRIGIERT (dritte Korrekturrunde, RVW2-13) — die Zuschreibung an V1/V2/V6 war falsch.**
  `python3 scripts/sync.py --check` ist der **Drift-Lauf** (Abgleich generierter Dateien gegen den
  Ist-Zustand), **nicht** der Consistency-Runner: der Pfad `--check` ist in
  `scripts/lib/sync_pipeline.py:914` verdrahtet, `_run_consistency_checks` wird nur von
  `_handle_validate` aufgerufen (`scripts/lib/cli_commands.py:975`). `--check` kann deshalb
  **nicht** an V1/V2/V6 rot werden. **Korrigierte Fassung:** `python3 scripts/sync.py --check` → **0**
  bedeutet **keine generierte Datei driftet**; ob V1/V2/V6 rot sind, sagt ausschließlich
  `--validate` bzw. `W-GATE`. Der Verweis auf Spec §6(b) trägt für `--validate`, **nicht** für
  `--check` — §6(b) nennt beide Modi gemeinsam; die Präzisierung dieses Halbsatzes der Spec ist als
  **Entscheidungsvorlage** an den Parent eskaliert (**ESCALATION E-3**, Spec §17.9.4,
  Entscheidungsvorlagen; **Frist: vor W3-7**), hier **nicht** eigenmächtig geändert.
- ~~`python3 scripts/consistency-check.py --strict` → **0 ab W3-7** (Pflicht ab W3, Spec §10)~~
  **AUFGEHOBEN (Rev. 0.5, K14) — der Pflichtumfang ist datei-, nicht repo-bezogen.** Die
  Zeile bleibt als Historie sichtbar. Sie war **unerreichbar**: `consistency-check.py:273-274`
  setzt Exit 1, sobald **irgendein** Finding `WARNING` trägt, und `report.py:75` bei Errors.
  **RVW2-12 — die Begründung ist damit unvollständig:** belegt ist die **Pfadabdeckung** der
  Bestandschecks (`agents/1-generic`, `agents/2-platform`, `commands/*` — `consistency-check.py:108-135`),
  **nicht** deren tatsächliche Warning-Emitterung; diese ist **ungemessen** und wird in
  **W3-7** gemessen (W3-BASELINE-STRICT). **Rückfallregel:** fällt die Baseline mit
  `errors: 0, warnings: 0` aus, ist `--strict → 0` für W4…W8 **wieder** maßgeblich und die
  Aufhebung ist zu annullieren. Die Zahl „rund 19" aus L-2/B-1 ist eine **ungeprüfte
  Schätzung** und wird hier **nicht** als Prämisse geführt. **Maßgeblich sind jetzt
  W3-GATE-SCOPE (Dokuzeile, RVW-14) und W-GATE + W-GATE-TABLE (verbindlich)** unten.
- ~~`python3 scripts/sync.py --validate` (= `TEST_COMMAND`) → **0 nach W3-7**~~
  **UMGESTELLT (dritte Korrekturrunde, RVW2-2) — unerreichbar und in sich widersprüchlich.**
  Der W3-Block behauptete an anderer Stelle (bis zur Korrektur), `--check`/`--validate` seien im
  Intervall W3-4…W3-6 „planmäßig nicht grün", verlangte hier aber `→ 0 nach W3-7` — während
  **V3** erst in **W8-2** auf 0 geht. **Maßgeblich ist `W-VALIDATE-ROT`** (Wellenblock
  W2 — Verifikation): planmäßig rot bis einschließlich **W8-2**, spätester Termin 0 **W8-4**,
  Owner `validator`, Grundlage **Spec §6(b) / §10, Aufzählungspunkt `--validate`**.
- `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0** (6/6, AC-38: `54:26-27` findet Datei
  **und** `File-based index fallback`; `55:24-25` dito; `56:31` findet Datei; `50:32` findet Datei;
  `51:32` und `52:44` finden **keine** `docs/INDEX.md`)
- `grep -c 'Repo version:' ARCHITECTURE.md` → **0** nach W3-7 (F4, zweite Fundstelle)

**W3-GATE-SCOPE (Rev. 0.5, K14) — Spec-§10-Pflichtumfang, datei-bezogen.**
`scripts/consistency-check.py` besitzt **keinen** Scope-/Pfadfilter (`--file` schließt alle
repo-weiten Checks aus, `scripts/consistency-check.py:185`; `--changed` filtert nur
`agents/`/`commands/`), deshalb wird über die `--json`-Ausgabe gefiltert — sie enthält `file`
und `check` (`report.py:78-97`).

```bash
python3 scripts/consistency-check.py --json \
  | python3 -c 'import json,sys,fnmatch;d=json.load(sys.stdin);s=[f for f in d["findings"] if f["file"]=="docs/INDEX.md" or fnmatch.fnmatch(f["file"],"scripts/lib/doc_*.py")];print("scope-findings:",len(s));[print(" ",f["severity"],f["check"],f["file"]) for f in s]'
```

**Erwartungswert: `scope-findings: 0`.** **Ausdrücklich keine Prüfkraft (RVW-14, Info) — der
Wert ist 0 per Konstruktion:** kein V-Check meldet **auf** `docs/INDEX.md` oder
`scripts/lib/doc_*.py`. V1 scannt `README.md`, `llms.txt`, `ARCHITECTURE.md`
(`scripts/lib/consistency/docs.py:158`); V2 liest `docs/INDEX.md` als **Soll**, nicht als
Fundstelle; V4 liest `README.md` als Soll; V6 vergleicht die generierten Blöcke. Der Filter kann
also konstruktionsbedingt nichts anderes als 0 liefern. **Diese Zeile ist deshalb als
Dokuzeile geführt, nicht als Prüfkriterium** — sie dokumentiert die Aussage des Pflichtumfangs
(Spec §10), beweist aber nichts. **Die eigentliche Doku-Aussage trägt W-GATE / W-GATE-TABLE
unten.** Das Kommando ruft kein `sys.exit`; ausgewertet wird der gedruckte Zählwert (RVW-12).

**W-GATE (ersetzt W3-GATE-DOCS, Rev. 0.5, RVW-1) — check-spezifisches Doku-Gate der Wellen
W3…W8.** Das Aggregat `docs-findings: 0` ist als Wellen-Gate **aufgehoben**, weil es
**dauerhaft** unerreichbar ist (Nachweis unten). An seine Stelle tritt die Zählung **je
`check`-Name**:

```bash
python3 scripts/consistency-check.py --json \
  | python3 -c 'import json,sys,collections;d=json.load(sys.stdin);rows=[f for f in d["findings"] if f["check"].startswith("docs.")];c=collections.Counter(f["check"] for f in rows);print("docs-checks:",len(c));[print("  ",k,c[k],sorted({f["severity"] for f in rows if f["check"]==k})) for k in sorted(c)];print("docs-findings:",len(rows))'
```

**Ausgewertet wird die gedruckte Tabelle**, nicht der Exit-Code (RVW-12: das Kommando ruft
**kein** `sys.exit`; ein `sys.exit` am Roh-Exit würde den Runner-Exit neutralisieren und ein
Kriterium vortäuschen, das nicht prüft). **Verbindlich sind zwei Größen** — und **nicht** die,
die die Fassung vor diesem Review nannte:

- **verbindlich:** die **Einzelzählung je `check`-Name** (Wert **und** Severity-Menge) gegen
  `W-GATE-TABLE`, Spalte der jeweiligen Welle — das ist das eigentliche Wellen-Gate;
- **verbindlich als Präsenzregel:** für jeden V-Check mit Erwartungswert **≠ 0** und ≠ `n. i.`
  **muss** eine Zeile `<check> <count> <severities>` gedruckt werden (siehe W2-GATE-ERRORS,
  „`docs-checks` — die Zahl ist KEIN Registrierungsnachweis");
- **Dokuzeile ohne Sollwert:** `docs-checks` (Counter über die Findings) und `docs-findings`
  (Gesamtzahl). `docs-checks` ist die Anzahl **befundliefernder** Checks in diesem Lauf, nicht die
  Anzahl registrierter (RVW2-1); `docs-findings` ist reine Information und **kein** Kriterium.

**Warum das Aggregat `docs-findings: 0` dauerhaft unerreichbar war (RVW-1, am Working Tree
gemessen 2026-09-26):**

| Grund | Beleg | Behoben wann |
|---|---|---|
| **V7** meldet **10** Wiki-Seiten `type: "Architecture"` **ohne** `derived-from` (WARNING) | `knowledge/wiki/concepts/architecture*.md:2` u. a.; **null** `derived-from:` im Baum | **W5-3** |
| **V3** meldet tote interne Verweise auf `howto/setup/`, `howto/features/` (ERROR) | `README.md:721-723`; im Baum existiert nur `howto/configs/project.yaml.example` | **W8-2** |
| **V2** meldet jede getrackte `docs/**/*.md` ohne Eintrag (ERROR) | `docs/INDEX.md` existiert **nicht** | **W3-6** |
| **V9** meldet den Altbestand an `*.sync-backup-*` als **WARNING** und wird ihn **nicht** abräumen | W8-4-Akzeptanz: die Altlasten bleiben **unangetastet**; FI-10 („lokale Aufräumaktion, kein Spec-Gegenstand") | **kein Termin 0** (geduldet, FI-10) — zur **Zahl** siehe Fußnote ⁴ |

Der vierte Punkt ist der entscheidende: **auch ab W8-4 ist `docs-findings: 0` nicht erreichbar**,
ohne den ausdrücklich unangetasteten Bestand zu verletzen. Das Aggregat ist damit nicht bloß
verfrüht, sondern **falsch** — die Korrektur ist ein **Schnitt auf check-Ebene**, keine
Verschiebung.

**W-GATE-TABLE (verbindlich) — Erwartungswert, Termin und Owner je V-Check.** Spaltenbedeutung:
**0** = Kriterium erfüllt bei Wellenabschluss · **planmäßig rot** = bewusst nicht erfüllt, mit
**Termin** (Welle, in der der Check 0 wird) und **Owner** (Task, die ihn behebt) ·
**nicht implementiert** (`n. i.`) = noch nicht registriert (Startwelle laut IC-05) · **geduldet**
= gemeldet, aber **kein Sollwert** und **kein** Termin 0.

| `check` (V) | Severity | W2-7 | W3-7 | W4 | W5 | W6 | W7 | W8 | Termin 0 | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| `docs.no_manual_counts` (V1) | ERROR ab W3-4 | ≥ 1 | **0** | 0 | 0 | 0 | 0 | 0 | **W3-7** | `developer` |
| `docs.docs_index_completeness` (V2) | ERROR | rot | **0** | rot¹ | rot¹ | 0 | 0 | 0² | **W3-6** | `senior-developer` (W3-6) |
| `docs.internal_links` (V3) | ERROR | rot | rot | rot | rot | rot | rot | **0** | **W8-2** | `developer` |
| `docs.readme_index` (V4) | ERROR | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — | `developer` (W2-6) |
| `docs.role_generation_parity` (V5) | WARNING | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — | `developer` (W2-4) |
| `docs.docs_facts_fresh` (V6) | ERROR | rot | **0** | 0 | 0 | 0 | 0 | 0 | **W3-7** | `developer` (W3-7) |
| `docs.wiki_staleness` (V7) | WARNING | rot | rot | rot | **0** | 0 | 0 | 0 | **W5-3** | `tester` (W5-3) |
| `docs.spec_plan_path_convention` (V8) | WARNING | n. i. | n. i. | n. i. | n. i. | 0 | 0 | 0 | — | `tester` (W6-2) |
| `docs.stale_backups` (V9) | WARNING | n. i. | n. i. | n. i. | n. i. | n. i. | n. i. | **geduldet**, kein Sollwert⁴ | **keiner** (FI-10) | `tester` (W8-4) |
| **`docs-checks`** (Counter) | — | *(Dokuzeile)* | *(Dokuzeile)* | *(Dokuzeile)* | *(Dokuzeile)* | *(Dokuzeile)* | *(Dokuzeile)* | *(Dokuzeile)* | — | `developer` (W2-7) |

¹ **V2 wird in W4 und W5 erneut rot, weil die `git mv`-Wellen neue getrackte `docs/**/*.md`-Pfade
erzeugen,** die noch nicht in `docs/INDEX.md` stehen. **Korrigiert (RVW2-8):** die Fassung vor
dieser Korrekturrunde nannte auch `docs/guides/configs/project.yaml.example` — das ist **keine
`.md`-Datei**; IC-05 begrenzt V2 auf „jede **getrackte** `docs/**/*.md`"
(Spec IC-05, Zeile der V2-Zeile), ein `.yaml.example` fällt darunter nicht. **Korrigierte
Menge:** W4-1 (`docs/architecture/00-overview-full.md`) und W4-3 (`docs/architecture/INDEX.md`),
W5-1 (`docs/plans/2026-09-25-docs-consolidation-oq9.md` — **neu** in dieser Korrekturrunde
festgestellt: W5-1 legt eine getrackte `docs/**/*.md` an) und W5-2
(`docs/guides/admin-ui-remote-access.md`; der zweite `git mv` in W5-2 betrifft
`docs/guides/configs/project.yaml.example` und ist für V2 **ohne** Belang).
Termin der Behebung ist jeweils das **Wellenende**: der Abschluss-Sync-Lauf in **W4-3**
(Owner `tester`) bzw. **W5-2** (Owner `developer`). Das ist **kein** neuer Task und **kein** neues
Datei-`Ownership`: `docs/INDEX.md` bleibt im Besitz des Generators aus **W3-6**; ein Sync-Lauf ist
Ausführung, nicht Schreib-Ownership. **RVW2-6:** der Sync-Lauf steht jetzt als **eigener Step** in
W4-3 und W5-2 (nicht mehr nur im Fließtext) und ist in der Normativitätstabelle der Spec
(§17.9.4, Punkt (viii)) als neue Nachweisform geführt.
**Präzisierung zu OQ9 (RVW2-8, ohne OQ9 zu entscheiden):** der Ergebnis-Ort der
OQ9-Entscheidung ist in Spec §11.1 als „eine `docs/guides/INDEX.md`-Zeile" formuliert. **Eine Datei
`docs/guides/INDEX.md` wird von keiner Welle erzeugt** (W5-1 `Files:` listet nur
`docs/plans/2026-09-25-docs-consolidation-oq9.md`). Gemeint ist damit die **Zeile im generierten
`docs/INDEX.md`**, Abschnitt `## guides` (IC-10(d)) — plus der Pointer in **beiden** Beispiel-Configs
(Plan Task **W5-1**, `Akzeptanz`). **Diese Klarstellung entscheidet OQ9 nicht**; sie stellt nur
fest, dass der Ergebnis-Ort **keine neue Datei** ist und damit **keinen** zusätzlichen V2-Rotpunkt
erzeugt. Wird die Entscheidung später als eigene `docs/guides/INDEX.md` geführt, verschiebt sich
der V2-Rotpunkt auf **W5-1** — die Terminspalte der Tabelle (V2/W5: „Termin W5-2") wäre dann zu
korrigieren. **Diese Nachlaufregel ist vor dem ersten W5-Lauf zu prüfen**, Owner `technical-writer`
(W5-1).
² **V2 wird in W8 erneut kurz rot**, weil **W8-1** `docs/REQUIREMENTS.md` bearbeitet und
`docs/plans/2026-09-25-docs-consolidation-oq4.md` anlegt; Termin ist der Abschluss-Sync-Lauf
in **W8-4** (Owner `tester`, **eigener Step** seit RVW2-6).
`n. i.` = **nicht implementiert** — der Check ist bis zu seiner Startwelle nicht registriert
und erscheint deshalb **nicht** in der Tabelle. **Korrigiert (RVW2-1):** ein `docs.`-Name, der
**außerhalb** dieser neun erscheint, ist ein **Befund** (überzählige Registrierung) — das ist
mit dem Kommando **prüfbar**. **Die Gegenrichtung ist es nicht:** ein **fehlender** (nicht
implementierter) Check ist über das Kommando **nicht** erkennbar, weil er keine Findings erzeugt.
Diese Lücke wird durch die **Präsenzregel** nur für Checks mit Erwartungswert ≠ 0 geschlossen; für
**V4** und **V5** (Erwartungswert 0) tragen die Unit-Tests der Tasks **W2-6** und **W2-4** sowie
der Registrierungsnachweis in **W2-7**. Das ist als Lücke **benannt**, nicht kaschiert.

³ **Redlichkeit der Erwartungswerte — was gemessen ist und was nicht.** Die **rot**-Werte der
Tabelle sind **am Working Tree belegt** (V2: `docs/INDEX.md` fehlt; V3: `howto/setup/` und
`howto/features/` fehlen; V7: 10 `type: "Architecture"`-Seiten ohne `derived-from`) und stehen in
Verbindung mit einem **konkreten Termin und Owner**. Die **0**-Werte für **V4** und **V5** sind
**Prognosen aus der Spezifikation**, **keine Messungen**: V4s generalisierter Umfang wird erst in
**W2-6** implementiert, V5s Satzmenge `compute_active_roles()` schließt das deaktivierte Gate
(`project.yaml:12-13`). **RVW2-14 — zeitgebundene Formulierung:** „nicht implementiert und
daher nicht vorab prüfbar" gilt **zum Planungszeitpunkt (2026-09-26)**. **Ab dem ersten W2-7-Lauf
sind V4 und V5 implementiert und damit messbar** — die dortige Aussage entfällt, sie wird nicht
stillschweigend fortgeschrieben. **Regel:** `W2-GATE-ERRORS` wird beim **ersten W2-7-Lauf**
gemessen; weicht ein **0**-Wert vom
Ist-Zustand ab, ist **nicht** der Erwartungswert zu senken, sondern die betroffene Task
(W2-6 bzw. W2-4) zu korrigieren — die Abweichung wird im **W2-7-Review-Protokoll** als
`W-GATE-TABLE-ABWEICHUNG` festgehalten. Gleiches gilt für jeden späteren Wellenabschluss.

⁴ **V9 — kein Sollwert, sondern eine Obergrenze, die erst nach einer Messung festgeschrieben wird
(RVW2-4).** Die Zahl **179** stammt aus dem System-Design und FI-10 und bezeichnet einen
**maschinenlokalen, gitignorierten** Bestand: die Dateien liegen unter `.claude/agents/`, und
`.gitignore:13` (`.claude/`) sowie `.gitignore:22` (`*.sync-backup-*`) schließen sie aus der
Versionierung aus. **Im Working Tree ist die Zahl nicht messbar** — eine Suche nach
`**/*.sync-backup-*` findet **genau eine** Datei (`CLAUDE.md.sync-backup-20260913-200441`). Ein
exakter Sollwert „179" wäre damit weder reproduzierbar noch CI-fähig und in jeder anderen
Umgebung falsch. **Regel (verbindlich):**
1. V9 **meldet** Backup-Funde; der Zählwert ist **kein** Sollwert des Gates und **kein**
   DoD-Kriterium.
2. **W8-4, Schritt 1** nimmt **vor** der Implementierung eine **Bestandsaufnahme** auf
   (`*.sync-backup-*` in den Provider-Verzeichnissen, Muster `.gitignore:22`) und schreibt sie als
   `BACKUP-BASELINE = <n>` in das W8-4-Review-Protokoll. Owner `tester`, Termin **W8-4**.
3. Die **Obergrenze** wird als **Soll + Toleranz** erst **nach** dieser Messung festgeschrieben —
   als Artefakt des **W8-4-Review-Protokolls** (`V9-OBERGRENZE`). **Ein** Folgestand in der Spec
   (IC-05, V9-Zeile) findet **nicht** statt (RVW3-6: die ausführende Task trägt keinen neuen
   Sollwert in die normative Quelle ein). **Vor** der Messung wird
   **keine** Zahl als Sollwert geführt — eine Prognose wäre hier eine Prädiktion, weil
   (a) die Altersschwelle N erst in W8-4 festgelegt wird und (b) das Vorhaben **selbst** neue
   Backups erzeugt (Drift-Store legt vor jedem Overwrite `*.sync-backup-*` an; AC-35/W7-3 verlangt
   `knowledge/wiki/index.md.sync-backup-*`).

**Verschlechterungsregel (unabhängig von den Einzelwerten, in jeder Welle; neu gefasst, RVW2-1/RVW2-4):**
1. **Startwelle je Check:** ein V-Check darf **erst ab seiner IC-05-Startwelle** Findings liefern
   (V1–V7 ab **W2-7**, V8 ab **W6-2**, V9 ab **W8-4**). Findings eines Checks **vor** seiner
   Startwelle sind ein **Befund** (verfrühte Registrierung).
2. **Präsenz:** für jeden Check mit Erwartungswert ≠ 0 muss die Zeile stehen (siehe W2-GATE-ERRORS).
3. **Planmäßig rote Checks:** der Zählwert darf **nicht steigen** (neu hinzugekommene Fundstellen
   desselben Checks sind ein Befund); **sinken** ist erlaubt, aber nicht gefordert.
4. **Ausnahme V9 (neu):** für `docs.stale_backups` gilt die Regel 3 **nicht**. Der Bestand ist
   maschinenlokal, gitignoriert und wird per FI-10 **nicht** abgeräumt; ein Anstieg durch **eigene**
   neue Backups des Vorhabens (Drift-Store, W7-3, Abschluss-Sync-Läufe) ist **erlaubt** und **kein**
   Befund. Maßgeblich ist allein die Obergrenze aus Fußnote ⁴, und die existiert erst nach der
   Bestandsaufnahme in W8-4.
5. **`docs-checks` und `docs-findings`** sind **Dokuzeilen**, **keine** Kriterien.

**Zu den `check`-Namen — siehe den gleichlautenden Absatz im Wellenblock W2 (W2-GATE-ERRORS), der
in der dritten Korrekturrunde um den belegten V4-Namen `docs.readme_index`
(`scripts/lib/consistency/docs.py:118`) ergänzt und als Schlüssel der Präsenzregel präzisiert
wurde. Die Doppelführung bleibt erhalten, damit der Absatz bei jeder Wellenprüfung im W3-Block
selbst lesbar ist; maßgeblich ist der Text in W2-GATE-ERRORS.

**W3-BASELINE-STRICT (Rev. 0.5, K14) — Altbestand, getrennt ausgewiesen.**
`python3 scripts/consistency-check.py --strict` ist **kein** Abnahmekriterium von W3. Es wird als
**Altbestand-Baseline** geführt und **einmal** gemessen:

```bash
python3 scripts/consistency-check.py --strict; echo "exit=$?"
python3 scripts/consistency-check.py --json | python3 -c 'import json,sys;d=json.load(sys.stdin);print("errors:",d["summary"]["errors"],"warnings:",d["summary"]["warnings"])'
```

**Owner der Messung:** `validator` beim **ersten** W3-Lauf (W3-7). Das Ergebnis wird als
`BASELINE-STRICT = <errors>/<warnings>` plus Dateiliste im **Review-Protokoll** festgehalten.
**Regel:** jede Verschlechterung dieser Baseline durch W1–W8 ist ein **Befund**; jede
**Verbesserung** ist **erlaubt**, aber **nicht** gefordert. **Stand der Messung am
2026-09-26:** in der Revisionsrunde stand **kein** Shell-Zugriff zur Verfügung — die Baseline ist
daher **nicht** gemessen und **nicht** behauptet; die Erwartung „0" wird **ausdrücklich nicht**
geführt. Belegt ist nur die Mechanik (`consistency-check.py:273-274`, `report.py:75`) und die
**Pfadabdeckung** der Bestandschecks (`agents/1-generic`, `agents/2-platform`, `commands/*` — über
`collect_agent_files`/`collect_command_files`, `consistency-check.py:108-135`).

**RVW2-12 — die Prämisse der Aufhebung ist ungemessen, und es fehlt eine Rückfallregel. Beides
ist hier korrigiert.**

(a) **Ungemessen.** Aufhebungskette RVW-1/RVW-2/RVW-3/K14 stützt sich darauf, dass die
Bestandschecks über `agents/1-generic`, `agents/2-platform` und `commands/*` **Warnings**
emittieren. **Belegt ist ausschließlich die Pfadabdeckung, nicht die tatsächliche
Warning-Emitterung.** Die in Abschnitt **L-2, B-1** genannte Zahl „rund **19**" ist eine
**Schätzung aus dem Rev.-0.4-Abgleich, nicht gemessen**; sie wird hier **nicht** als Prämisse
geführt. Weder „19" noch „warnings > 0" wird irgendwo als Voraussetzung der Aufhebung behauptet.

(b) **Rückfallregel (verbindlich).** Ergibt die Messung in W3-7
`errors: 0` **und** `warnings: 0`, dann ist die strengere Nachweisform
(`python3 scripts/consistency-check.py --strict` → **0** als Wellen-Nachweis) für die Wellen
**W4…W8** **wieder** maßgeblich; die Aufhebung aus K14/RVW-3 ist für diese Wellen zu
**annullieren**, und die Wellenblock-Zeilen von W4, W5, W6, W7 und W8 sind wieder wörtlich zu
restaurieren. **Owner:** `validator` (Messung) und `orchestrator` (Textpflege), **Entscheidungs-
punkt: W3-7**, also **vor** W4-1. Die Textpflege **blockiert keine Welle**, die Annullierung der
Aufhebung **wohl** — sie entscheidet die Nachweisform, nicht den Inhalt. **Ergebnis** wird als
`W3-BASELINE-STRICT = <errors>/<warnings>` **plus** `STRICT-AUFHEBUNG: aufgehoben | zurückgenommen`
im Review-Protokoll festgehalten.
**OFFEN — nicht vom beauftragten Korrekturumfang gedeckt (vierte Korrekturrunde, Prüfvermerk):**
diese Rückfallregel verlangt eine **Textpflicht in zwei späteren Wellen** (W4, W5 — bei W4/W5/W6/W7/W8
wörtliche Restaurierung der Wellenblock-Zeilen). Sie ist in der Normativitätstabelle der Spec
(§17.9.4, Punkte (i)–(x)) **nicht** als neue Nachweisform geführt und damit **nicht** als beschlossen
und **nicht** als vom Auftrag gedeckt zu führen. Der Text bleibt **unverändert** stehen; die
Festlegung, ob er als verbindliche Nachweisform in die Spec gehört, ist ein **offener Punkt** beim
Auftraggeber und wird hier **nicht** entschieden.

(c) **Folge für `--validate` (siehe Regel `W-VALIDATE-ROT`):** derselbe Messwert entscheidet
auch dort. Ist `errors > 0`, ist `python3 scripts/sync.py --validate` → **0** wegen des
**repo-weiten** ERROR-Altbestands **nicht erreichbar**; maßgeblich ist dann die **Deltasperre**
(`errors` darf durch W1–W8 nicht steigen).

**Geltung für alle späteren Wellenblöcke (Rev. 0.5, RVW-3 — additiv, keine Neuschreibung;
Abschnittsanker statt Zeilenanker, K12-Logik).** Die repo-globale Formulierung
`python3 scripts/consistency-check.py --strict` → **0** steht weiterhin **wortgleich** in den
Wellenblöcken **W4**, **W5**, **W6**, **W7**, **W8** sowie in den Task-Verifikationen von
**W4-2**, **W4-3**, **W5-3**, **W7-5**, **W8-2**, **W8-3**, **W8-4** (Task **W8-4** nennt es
zusätzlich im Fließtext der Spec-Lücken-Notiz) und in **DoD Punkt 2**. **RVW-9:** die
Enumerationsliste der Fassung vor diesem Review war falsch — sie nannte **W5-1**, **W6-2** und
**W7-2**, die **keine** `--strict`-Zeile führen, und ließ die **Wellenblock**-Zeilen von W5, W6,
W7 und W8 aus. **Korrekt ist:** alle **fünf Wellenblock**-Zeilen sind im Rahmen dieses Reviews
**umgestellt** (siehe die Annotation an jedem Wellenblock) und gelten als **W-GATE +
W-GATE-TABLE, Zeile der jeweiligen Welle**; die **Task**-Verifikationen bleiben unter dieser
Geltungsregel, sind aber **ausdrücklich kein Welle-Gate** — eine Task-Zeile prüft die
Implementierung, verbindlich für den **Wellenabschluss** ist allein die Zeile der W-GATE-TABLE.
**Task-Verifikationen unter der Geltungsregel:** W4-2, W4-3, W5-3, W7-5, W8-2, W8-3, W8-4,
DoD Punkt 2. **Owner der Textpflege:** `orchestrator`, Termin **vor W6-1**; **blockiert keine
Welle** (reine Textvereinheitlichung, kein Code, keine Gate-Wirkung). **Auch diese Textpflicht ist
im Prüfvermerk der vierten Korrekturrunde als OFFEN / nicht vom beauftragten Umfang gedeckt
gekennzeichnet** (siehe (b) oben) — sie wird **nicht** stillschweigend als beschlossen geführt.

**Geltung für `--check` (neu in der dritten Korrekturrunde, RVW2-13).** `python3 scripts/sync.py
--check` ist der **Drift-Lauf**, nicht der Consistency-Runner, und steht deshalb **außerhalb** der
Geltungsregel: die Zeile bedeutet „**keine generierte Datei driftet**". Sie darf **nicht** als
Doku-Gate gelesen werden. Betroffene Stellen (RVW2-13 korrigiert): Wellenblöcke **W3** (Zeile mit
dem gestrichenen Intervall-Text) und **W8**, Task-Verifikationen **W3-6**, **W3-7**, **W5-2**,
**W8-3**. Alle tragen nun den Zusatz „Drift-Lauf, **kein** Consistency-Nachweis".
**Geltung für `--validate` (neu, RVW2-2).** Siehe **`W-VALIDATE-ROT`** im Wellenblock W2; die
Wellenblöcke **W2, W3, W4, W5, W6, W7, W8** sowie die Task-Verifikationen **W3-4**, **W3-6**,
**W3-7**, **W4-3**, **W5-2**, **W6-2**, **W7-5**, **W8-3**, **W8-4** sind auf diese **eine** Regel
umgestellt: planmäßig rot bis einschließlich **W8-2**, spätester Termin 0 **W8-4**, Owner
`validator`.


**Review W3:** `code-reviewer` (Stage-Reihenfolge, Doppel-Writer-Risiko B2) → `validator`
(AC-20…AC-22, AC-38) → `concept-reviewer` (Besitzregel IC-13).
**Gate bei CHANGES_REQUESTED:** bricht der Scaffold-Guard ein Szenario, geht W3-3 zurück; eine
Umkehr der Stage-Reihenfolge (IC-12) ist ein **Stopp** mit Eskalation an `main_chat` (Spec A4).
**Rollback W3:** `git rm docs/INDEX.md`; `docs-consolidation.enabled: false`; `checks.strict`
zurück auf `false`; Marker-Regionen aus `README.md`/`llms.txt`/`ARCHITECTURE.md` entfernen;
`doc_renderer.py`, `doc_index.py`, `sync_pipeline.py`, `spec_plan_scaffold.py`,
`generated_file_drift.py` via `git checkout`. `docs/architecture/INDEX.md` entsteht erst in W4-3
und ist vom W3-Rollback **nicht** betroffen.

### W3-1: Schreib-, Idempotenz- und `dry_run`-Vertrag

**Files:** Modify `scripts/lib/doc_renderer.py`, `scripts/lib/doc_index.py`, `tests/test_doc_renderer.py`
**Interfaces:** Produces: `sync_docs_consolidation(agent_meta_root, project_root, config,
provider_config, log, dry_run) -> {'written','unchanged','skipped'}` inkl. Besitzregel (IC-13).
Consumes: W1-7, W1-8, W1-10.
**Agent:** senior-developer · **Depends on:** W1-10 · **parallel_group:** PG-2 / W3
**Ziel-AK (AC):** **AC-23**, **AC-26** (IC-13) · **V-Check:** **V6**
**Akzeptanz:** `test_dry_run_no_writes` grün (null Dateisystem-Schreibvorgänge, `written` listet
Kandidaten, `knowledge/wiki/log.md` unverändert); `test_no_docs_dir_is_skipped_not_created` grün
(kein `mkdir` in Fremdprojekten); Zielinhalt == Istinhalt ⇒ `unchanged` **ohne** `write_checked`;
`enabled != true` ⇒ `log.skip("docs-consolidation", "disabled in project.yaml")` ohne jeden
Schreibzugriff. Besitzregel: der Generator überschreibt **nie** eine Datei, die ein anderer Writer
legitim geschrieben hat.
**Verifikation:** `python3 -m pytest tests/test_doc_renderer.py -q` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: `sync_docs_consolidation` mit Besitzregel und `dry_run`-Pfad implementieren.
- [ ] 3: Tests grün beobachten.
- [ ] 4: commit via `git`-Agent: `feat: add docs consolidation writer contract`.

### W3-2: `docs/INDEX.md`-Volltext, Fact-Hash-Footer, Volatile-Sektion

**Files:** Modify `scripts/lib/doc_renderer.py`, `tests/test_doc_renderer.py`
**Interfaces:** Produces: `render_docs_index(index_model, facts) -> str` nach IC-10; Footer
`facts-hash: <16 hex>` + `generator: doc-indexer/1` (IC-14). Consumes: W3-1, W1-8.
**Agent:** senior-developer · **Depends on:** W3-1 · **parallel_group:** PG-2 / W3
**Ziel-AK (AC):** **AC-17**, **AC-18**, **AC-03** (IC-10, IC-14) · **V-Check:** **V2**, **V6**
**Akzeptanz:** `test_index_deterministic_and_archive_excluded` und
`test_footer_has_no_timestamp` grün; Regex `\d{4}-\d{2}-\d{2}` auf dem generierten Footer-Bereich
findet **keinen** Treffer; `docs-volatile` steht als **letzte** Sektion **vor** dem Footer; zwei
Renderings, die sich **nur** in `DOCS_SCENARIO_COUNT` unterscheiden ⇒ **identischer** `facts-hash`;
jeder `docs/**/*.md`-Pfad (ohne `archive/`, `_archive/`) genau einmal, `docs/INDEX.md` nie.
**Verifikation:** `python3 -m pytest tests/test_doc_renderer.py -q` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: `render_docs_index` + Hash-Algorithmus implementieren (SHA-256 über sortierte
      **nicht-volatile** Fakten, 16 Hex-Zeichen, kein Zeitstempel, kein absoluter Pfad).
- [ ] 3: Tests grün beobachten; Diff-Minimalität stichprobenartig prüfen.
- [ ] 4: commit via `git`-Agent: `feat: render full docs index with stable fact hash`.

### W3-3: Scaffold-Guard und Besitzregel

**Files:** Modify `scripts/lib/spec_plan_scaffold.py`, `tests/test_doc_renderer.py`
**Interfaces:** Produces: `is_file_index_skeleton(text) -> bool`,
`_FILE_INDEX_SKELETON_MARKER = "File-based index fallback"` (F20); `DEFAULT_FALLBACK_INDEX` bleibt
identisch (`:23`), `_FILE_INDEX_SKELETON` (`:24`) bleibt identisch. Consumes: W3-2, IC-15.
**Agent:** senior-developer · **Depends on:** W3-2 · **parallel_group:** PG-2 / W3
**Ziel-AK (AC):** **AC-21** (IC-15, IC-13) · **V-Check:** **V4**
**Akzeptanz:** `test_skeleton_mode_preserves_scaffold` und
`test_ke_authoritative_writes_no_index` grün; bei `index-mode: skeleton` bleibt das Skeleton
**immer** unangetastet; bei `resolve_index_mode() == "knowledge-engine"` (Szenario 52) wird **kein**
`docs/INDEX.md` geschrieben, Eintrag in `skipped` + `log.note` mit Grund. Der Generator schreibt
**nie** einen Skeleton.
**Verifikation:** `python3 -m pytest tests/test_doc_renderer.py -q` → **0**;
`bash tests/scenarios/run.sh 52 54 55 56` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: `is_file_index_skeleton` implementieren; Generator ruft es **vor** dem Schreiben.
- [ ] 3: Tests grün beobachten; vier Szenarien beobachten.
- [ ] 4: commit via `git`-Agent: `feat: guard scaffold skeleton against docs index writer`.

### W3-4: Stage-Reihenfolge und `checks.strict`

**Files:** Modify `scripts/lib/sync_pipeline.py`, `.meta-config/project.yaml`, `tests/test_doc_renderer.py`
**Interfaces:** Produces: `_sync_stage_docs_consolidation(...)` (IC-12); Reihenfolge
Drift-Scan (`:587-620`) → Knowledge/Scaffold (`:922-945`, `:929`, `:935`) → **Docs** →
Hash-Capture (`:1090-1099`) → Auto-Commit-Allowlist (`:1102`); `docs-consolidation.checks.strict: true`.
Consumes: W3-3.
**Agent:** senior-developer · **Depends on:** W3-3, **W2-1 (Schritt 4 — K16/RVW-4)** · **parallel_group:** PG-2 / W3
**Ziel-AK (AC):** **AC-22** (IC-12) · **V-Check:** **V1** (Severity-Wechsel WARNING → ERROR)
**Akzeptanz:** `test_stage_order_after_scaffold` und `test_ke_index_stays_authoritative` grün;
`checks.strict: true` gesetzt; V1 wechselt von WARNING auf ERROR. **Keine** Interaktion mit
`_sync_stage_auto_commit_allowlist` (`sync_pipeline.py:1102-1117` liest den Drift-Store nicht —
R18 analysiert und nicht zutreffend).
**Vorbedingung, neu (Rev. 0.5, K16 — Reihenfolgebindung W2-1 ↔ W3-4; als Kante abgebildet,
RVW-4):** `checks.strict: true` darf **erst** gesetzt werden, wenn **W2-1 Schritt 4**
(Sichtbarkeit der README-Fundstellen F2, F3-Site-2, F4) abgeschlossen ist. **Begründung:** die
Hochstufung dreht nur die **Severity** (`docs.py:359`), nicht die **Abdeckung** — bei geschlossener
Abdeckungslücke wird der erste `ERROR`-Befund einer **Spezifikationslücke** geschuldet (Regel 3
verdeckt `README.md:688/690/696/734`) und nicht einer Doku-Drift; die Wellen-Aussage „V1 ist ab W3
grün" wäre dann nicht haltbar. **Kantenrichtung (RVW-4, korrigiert):** die Bindung ist
**`W2-1 → W3-4`** und damit eine **Vorwärts**kante über die Wellengrenze — sie ist jetzt als
**echte Kante** in der Reihenfolge-/Abhängigkeitsmatrix geführt und erzeugt **keinen** Zyklus
(Nachweis im Absatz **Zyklenprüfung**). Die Fassung vor diesem Review nannte sie umgekehrt
(„W3-4 → W2-1") und begründte das mit einer Rückwärtskante; das war **falsch**. **Konsequenz
für PG-2:** W3-4 kann nicht parallel zu W2-1 starten; die übrigen W3-Tasks bleiben es.
**Konsequenz, ausdrücklich:** im Intervall W3-4 … W3-6 ist V1 damit `ERROR`-severity und V1
meldet **weiterhin** die noch nicht ersetzten Handzahlen — **`--validate` ist in diesem Intervall
planmäßig rot** (`W-VALIDATE-ROT`, Wellenblock W2 — Verifikation; V1 rot bis **W3-7**,
V2 rot bis **W3-6**, V3 rot bis **W8-2**; spätester Termin 0 **W8-4**, Owner `validator`,
Grundlage Spec §6(b) / §10, Aufzählungspunkt `--validate`). **RVW2-13:** die Fassung vor dieser Korrekturrunde schrieb
hier „`--check` planmäßig 1 im Intervall W3-4…W3-6" — das war **falsch**; `--check` ist der
Drift-Lauf und führt die Consistency-Suite nicht aus (`scripts/lib/cli_commands.py:975` wird nur
von `_handle_validate` aufgerufen). Richtig ist: **`--check` ist rot, solange generierte Dateien
nicht synchron sind** — das ist eine **eigene**, von V1 unabhängige Aussage.
**Verifikation:** `python3 -m pytest tests/test_doc_renderer.py -q` → **0**;
`grep -n 'checks.strict' .meta-config/project.yaml` → **0**.
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: Stage-Funktion unmittelbar nach `scaffold_spec_plan_dirs` einhängen; `checks.strict: true`.
- [ ] 3: Tests grün beobachten; `--validate` im Intervall als erwartet rot markieren
      (`W-VALIDATE-ROT`: planmäßig rot bis **W8-2**; Grundlage Spec §6(b) / §10, Aufzählungspunkt
      `--validate`).
- [ ] 4: commit via `git`-Agent: `feat: wire docs stage after scaffold and enable strict checks`.

### W3-5: Drift-Store für Doku-Dateien

**Files:** Modify `scripts/lib/generated_file_drift.py`, `tests/test_generated_file_drift_docs.py`
**Interfaces:** Produces: `DOCS_GENERATED_RELS = ("docs/INDEX.md","docs/architecture/INDEX.md")`,
`DOCS_FACT_BLOCK_HOSTS = ("README.md","llms.txt","ARCHITECTURE.md")`, `DOCS_MARKER_KEY_SUFFIX =
"#docs:"`; Store-Key `<rel>#docs:<region>`; Allowlist-Match gegen den **Basis-Pfad**.
Consumes: W3-4, IC-16.
**Agent:** developer · **Depends on:** W3-4 · **parallel_group:** PG-2 / W3
**Ziel-AK (AC):** **AC-19**, **AC-37** (IC-16) · **V-Check:** — (Drift-Store, Unit-Test)
**Akzeptanz:** `test_marker_body_only`, `test_no_backup_for_hash_key` und
`test_allowlist_matches_base_path` grün: Handprosa erzeugt **kein** Finding; ein Finding mit
`provider == "docs-consolidation"` und Pfad `README.md#docs:facts` erscheint; `apply_fact_blocks()`
überschreibt die editierte Region **nicht** (NFA-05); **keine** Datei namens `README.md#docs:facts`
entsteht; `allow-edits: ["README.md"]` unterdrückt den Marker-Body-Drift. Scan **und** Capture
werden symmetrisch ergänzt. Kein Eintritt in `_iter_managed_files` (`:240-310`).
**Verifikation:** `python3 -m pytest tests/test_generated_file_drift_docs.py tests/test_generated_file_drift.py -q` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: Doku-Pfade in Scan **und** Capture ergänzen; `is_allowlisted` (`:82-84`) gegen den
      Basis-Pfad matchen.
- [ ] 3: Tests grün beobachten; bestehende Drift-Tests mitlaufen lassen.
- [ ] 4: commit via `git`-Agent: `feat: track docs files in generated file drift store`.

### W3-6: `docs/INDEX.md` tracked, Erstgenerierung, OQ6/OQ8-Umsetzung

**Files:** Create `docs/INDEX.md`; Modify `.meta-config/project.yaml`, `README.md`,
`tests/test_doc_renderer.py` — **kein** `.gitignore`-Eintrag (OQ6 entschieden: `tracked`)
**Interfaces:** Produces: getrackte, 100 % generierte `docs/INDEX.md`; OQ6-Folge: `.gitignore`
bleibt **unverändert**; OQ8-Workflow-Vertrag (**Sync-/Validator-Lauf**, kein Hook) gemäß W0-6.
Consumes: W3-5, W0-1, W0-6, W2-6.
**Agent:** senior-developer · **Depends on:** W3-5, W0-1, W0-6 · **parallel_group:** PG-2 / W3
**Ziel-AK (AC):** **AC-20**, **AC-12** (E2E), **AC-38** · **V-Check:** **V2**, **V4**
**Akzeptanz:** `test_skeleton_replaced_once` grün: Skeleton wird **einmalig** ersetzt
(`log.action("UPDATE","docs/INDEX.md",…)` genau einmal), zweiter Lauf meldet `unchanged` mit
**null** Schreibvorgängen; `git check-ignore -q docs/INDEX.md` → **1** (entschieden: `tracked`);
V2 und V4
sind gegen das reale `docs/INDEX.md` grün; `docs/architecture/INDEX.md` wird in W3 **nicht**
erzeugt (W4-3), die Datei erscheint daher noch nicht im Index.
**Verifikation:** `python3 scripts/sync.py --check` → **0** (Drift-Lauf: keine generierte Datei
driftet; **kein** Consistency-Nachweis — RVW2-13);
`git check-ignore -q docs/INDEX.md; echo $?` → **1**;
`bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0**. **`--validate` ist hier planmäßig rot**
(`W-VALIDATE-ROT`: V3 bis **W8-2**; V2 ist mit dem Sync dieses Tasks auf 0).
**Steps:**
- [ ] 1: E2E-Test schreiben (fail).
- [ ] 2: Sync mit `enabled: true` ⇒ `docs/INDEX.md` erzeugen; OQ6-Folge anwenden (kein
      `.gitignore`-Eintrag); OQ8-Vertrag umsetzen — der Sync-/Validator-Lauf ist der Auslöser,
      **kein** Hook und keine Doku-Regel.
- [ ] 3: Tests grün beobachten; zweiten Lauf auf `unchanged` beobachten.
- [ ] 4: commit via `git`-Agent: `feat: generate and track docs index`.

### W3-7: Marker-Regionen in `README.md`, `llms.txt`, `ARCHITECTURE.md`

**Files:** Modify `README.md`, `llms.txt`, `ARCHITECTURE.md`
**Interfaces:** Produces: 11 Handzahlen (F1, F2, F3 ×2, F4 ×2, F14 ×3, F22 ×2) durch
`agent-meta:docs-*-Regionen` ersetzt — `README.md:381-390` (Überschrift **und** Preset-Tabelle,
`concept-driven` ergänzen), `README.md:479-489` (8 Pipelines, `concept-driven-dev` ergänzen,
`se-cascade` als deaktiviert kennzeichnen), `README.md:501` (`DOCS_HOOKS_COUNT`),
`README.md:688-696` (`DOCS_DOD_PRESET_COUNT`, `DOCS_TIER_PRESET_COUNT`, `DOCS_HOOKS_1GENERIC_COUNT`),
`README.md:734` (`DOCS_VERSION`), `ARCHITECTURE.md:3` (Stale-Deklaration wandert in W4-1 mit),
`llms.txt:5` (Proverbenamen-Liste). **Hybrid-Scope (OQ2, Spec §11.2):** in `llms.txt` werden
**ausschließlich** `{{DOCS_PROVIDERS_BLOCK}}` und `{{DOCS_REPO_FACTS_BLOCK}}` generiert —
Handtext-Einleitung und Linkliste bleiben handgepflegt, **kein** Vollgenerieren. Consumes:
W3-6, W1-6 (Snippets), W0-3 (OQ2-Record, **Hybrid**).
**Agent:** developer · **Depends on:** W3-6 · **parallel_group:** PG-2 / W3
**Ziel-AK (AC):** **AC-40** (Teil: `README.md:690`, `llms.txt:5`), **AC-07** (Wirkung: V1 wird grün)
· **V-Check:** **V1a**, **V1b**, **V6**
**Akzeptanz:** ~~`python3 scripts/consistency-check.py --strict` → **0** (kein `docs.*`-Finding)~~
**AUFGEHOBEN (Rev. 0.5, K14/RVW-1) — ersetzt durch W-GATE + W-GATE-TABLE des Wellenblocks
W3.** Die Zeile bleibt als Historie sichtbar. Sie war doppelt falsch zugeschnitten: sie war
**repo-global** statt datei-bezogen (unerreichbar, weil die Bestandschecks `agents/1-generic`,
`agents/2-platform`, `commands/*` abdecken — Pfade, die keine Welle W1–W8 fasst an; **RVW2-12:**
die tatsächliche **Warning-Emitterung** dieser Checks ist **ungemessen** und wird in W3-7 gemessen,
mit Rückfallregel — belegt ist bisher nur die Pfadabdeckung)
**und** sie verlangte das Aggregat `docs-findings: 0`, das **weder bei W3-7 noch am Ende des
Vorhabens** erreichbar ist (V7 bis **W5-3**, V3 bis **W8-2**, V2 bis **W3-6**, V9 **geduldet,
kein Termin 0** — FI-10).
**Maßgeblich ist jetzt:**
- **W3-GATE-SCOPE** → `scope-findings: 0` — **Dokuzeile ohne Prüfkraft** (RVW-14: 0 per
  Konstruktion; §10-Pflichtumfang `docs/INDEX.md` + `scripts/lib/doc_*.py`),
- **W-GATE** + **W-GATE-TABLE, Spalte W3-7** → das verbindliche Abschlusskriterium: V1 **0**,
  V2 **0**, V4 **0**, V5 **0**, V6 **0**; V3 und V7 **planmäßig rot** mit Termin **W8-2** bzw.
  **W5-3** und benanntem Owner; `docs-checks` = **Dokuzeile**, **kein** Sollwert (RVW2-1: der
  Counter zählt befundliefernde Checks, nicht registrierte),
- **W3-BASELINE-STRICT** → Altbestand, getrennt gemessen, **kein** Kriterium dieser Task.
- **W-VALIDATE-ROT** → `python3 scripts/sync.py --validate` ist auch bei W3-7 **planmäßig rot**:
  V3 bleibt bis **W8-2** ERROR. Die Fassung vor dieser Korrekturrunde führte hier **keine**
  `--validate`-Zeile; sie ist damit **kein** Verifikationskriterium dieser Task.

`python3 scripts/sync.py --check` → **0** (Drift-Lauf, **kein** Consistency-Nachweis — RVW2-13);
`grep -c 'Repo version:' ARCHITECTURE.md` → **0**;
zweimaliger Sync ⇒ `unchanged` für alle drei Dateien (kein Diff-Churn, R1). Kreuz-Rendering ist
verboten: `DOCS_HOOKS_COUNT` **nur** in `:501`, `DOCS_HOOKS_1GENERIC_COUNT` **nur** in `:696`
mit dem verpflichtenden Klammerzuschlag `(+2 *-impl.sh helpers)`.
**Verifikation:** siehe Akzeptanz; zusätzlich `python3 -m pytest tests/test_doc_facts.py -q` → **0**
(V1-Fixture-Zeilen bleiben als Positiv-Fixture bestehen).
**Steps:**
- [ ] 1: Regionen `roster|pipelines|hooks|providers|version|facts` einführen (IC-08-Namensraum,
        getrennt von `agent-meta:managed-*`).
- [ ] 2: Snippets einbinden; `concept-driven-dev`-Zeile ergänzen; `se-cascade` als deaktiviert
        kennzeichnen; Prose außerhalb der Regionen unverändert lassen (NG-1).
- [ ] 3: `--check`/`--strict` beobachten; Idempotenz beobachten.
- [ ] 4: commit via `git`-Agent: `docs: replace manual counts with generated doc fact blocks`.

---

## W4 — Architektur-Konsolidierung (`git mv` + Stub)

**Verifikation W4 (erwartete Exit-Codes):**
- `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**
- ~~`python3 scripts/sync.py --validate` → **0**~~
  **UMGESTELLT (dritte Korrekturrunde, RVW2-2) — planmäßig rot.** Verursachende Doku-ERROR-Checks
  in W4: **V3** (Termin **W8-2**, Owner `developer`) und **V2** (neu erzeugte `docs/**/*.md`-Pfade
  aus W4-1/W4-3, Termin **W4-3** = Abschluss-Sync-Lauf, Owner `tester`). **Maßgeblich ist
  `W-VALIDATE-ROT`** (Wellenblock W2 — Verifikation): planmäßig rot bis einschließlich **W8-2**,
  spätester Termin 0 **W8-4**, Owner `validator`, Grundlage **Spec §6(b) / §10, Aufzählungspunkt `--validate`**. Der
  Sollwert wird **nicht** abgesenkt, sondern **terminiert**.
- ~~`python3 scripts/consistency-check.py --strict` → **0** (V3 grün)~~
  **UMGESTELLT (Rev. 0.5, RVW-3) — der Klammertext „V3 grün" war falsch.** V3 ist **ERROR**
  und bleibt bis **W8-2** rot (`README.md:721-723` verweisen auf `howto/setup/` und
  `howto/features/`, die **nicht** existieren; im Baum liegt nur
  `howto/configs/project.yaml.example`). **Maßgeblich ist W-GATE + W-GATE-TABLE, Spalte W4:**
  V1 0 · V4 0 · V5 0 · V6 0 · V7 rot (Termin **W5-3**, Owner `tester`) · V3 rot (Termin **W8-2**,
  Owner `developer`) · **V2 planmäßig rot**, weil W4-1 und W4-3 zwei neue `docs/**/*.md`-Pfade
  erzeugen — Termin **W4-3** (Abschluss-Sync-Lauf, Owner `tester`) · `docs-checks` = **Dokuzeile**
  (RVW2-1: befundliefernde Checks, **kein** Registrierungsnachweis, **kein** Sollwert).
  **Die Task-Zeilen W4-2 und W4-3 bleiben unter der Geltungsregel** (Task-Verifikation, **kein**
  Welle-Gate).
- `test ! -e ARCHITECTURE.full.md` → **0**; `test -e docs/architecture/00-overview-full.md` → **0**
- `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0**
**Review W4:** `code-reviewer` (Diff ist **ausschließlich** R+A) → `validator` (AC-28-Teil, AC-29).
**Gate bei CHANGES_REQUESTED:** jeder Inhalts-Diff in einer verschobenen Datei ⇒ **Stopp** (NG-1);
`git log -M --follow` muss reine Renames zeigen (AC-28).
**Rollback W4:** `git mv docs/architecture/00-overview-full.md ARCHITECTURE.full.md`;
`ARCHITECTURE.md` via `git checkout`; additive Stale-Zeile entfernen; `docs/architecture/INDEX.md`
entfernen; `docs/INDEX.md` neu generieren.

### W4-1: `git mv` Langfassung + wandernde Stale-Deklaration (M-1, M-7)

**Files:** Move `ARCHITECTURE.full.md` → `docs/architecture/00-overview-full.md` (via `git mv`)
**Interfaces:** Produces: Langfassung an kanonischem Ort; **additive** Stale-Deklaration
(`Repo version:` / `last substantively reviewed`) wandert mit. Consumes: M-1, M-7, IC-18.
**Agent:** developer · **Depends on:** W3-6 · **parallel_group:** PG-3 (seriell)
**Ziel-AK (AC):** **AC-28** (Teil, M-1), **AC-29(b)** (M-7) · **V-Check:** **V3**
**Akzeptanz:** `git log -M --follow --name-status` zeigt **R100** ohne Inhalts-Diff; die
Stale-Deklaration steht in der Langfassung; `ARCHITECTURE.full.md` existiert **nicht** mehr.
**Verifikation:** `git log -M -1 --name-status` → **R100**;
`grep -c 'Repo version:' docs/architecture/00-overview-full.md` → **1**;
`test ! -e ARCHITECTURE.full.md` → **0**.
**Steps:**
- [ ] 1: `git mv` ausführen; Byte-Identität des Inhalts belegen.
- [ ] 2: Stale-Deklaration additiv in die Langfassung eintragen.
- [ ] 3: `git log -M` beobachten.
- [ ] 4: commit via `git`-Agent: `docs: move architecture longform into docs tree`.

### W4-2: `ARCHITECTURE.md` als generierter Stub (M-2, IC-18)

**Files:** Modify `ARCHITECTURE.md` (84 Z → Stub)
**Interfaces:** Produces: Titel, generierter Diagramm-Index (`docs/architecture/*.md` +
`docs/concepts/viz-logging-mcp.md` + `docs/concepts/a2a-handoff-protocol.md`, heute `:8-20`),
Pointer auf `docs/architecture/INDEX.md` und `docs/architecture/00-overview-full.md`, **keine**
eigene Architektur-Prose, **keine** `Repo version:`-Zeile. Consumes: W4-1.
**Agent:** developer · **Depends on:** W4-1 · **parallel_group:** PG-3 (seriell)
**Ziel-AK (AC):** **AC-29(a)** (IC-18) · **V-Check:** **V3**
**Akzeptanz:** `llms.txt:24`-Link auf `ARCHITECTURE.md` bleibt gültig (T-4-B — „Löschen bricht
Deeplinks“); keine eigene Prosa im Stub.
**Verifikation:** `grep -c 'Repo version:' ARCHITECTURE.md` → **0**; `wc -l < ARCHITECTURE.md` → **< 84**;
~~`python3 scripts/consistency-check.py --strict` → **0**~~ **unter der Geltungsregel**
(Task-Verifikation, **kein** Welle-Gate; RVW-3 — maßgeblich ist W-GATE + W-GATE-TABLE, Zeile der
Welle). V3 ist in W4 **planmäßig rot** (Termin **W8-2**, Owner `developer`).
**Steps:**
- [ ] 1: Stub-Inhalt nach IC-18 entwerfen.
- [ ] 2: `ARCHITECTURE.md` ersetzen; Linkziele prüfen.
- [ ] 3: V3 beobachten.
- [ ] 4: commit via `git`-Agent: `docs: reduce ARCHITECTURE.md to generated stub`.

### W4-3: `docs/architecture/INDEX.md` und AC-29-Nachweis

**Files:** Create `docs/architecture/INDEX.md`; Modify `tests/test_docs_consolidation_migration.py`
**Interfaces:** Produces: Teil-Vorschau auf denselben Doku-Baum (IC-10(d));
`test_architecture_stub_shape`, `test_stale_declaration_moved_with_longform`. Consumes: W4-2, W1-4.
**Agent:** tester · **Depends on:** W4-2 · **parallel_group:** PG-3 (seriell)
**Ziel-AK (AC):** **AC-29** (IC-18, IC-03, M-7), **AC-28** (Teil) · **V-Check:** **V3**, **V7**
**Akzeptanz:** AC-29 inkl. Teil (c): `compute_wiki_staleness()` liefert für
`knowledge/wiki/concepts/architecture.md` mit `derived-from: docs/architecture/00-overview-full.md`
einen **auswertbaren** Wert (kein `missing-derived-from`) — der Wert wird in **W5-3** gesetzt;
W4-3 stellt den Test so auf, dass er ab W5-3 grün ist und den Zwischenzustand als erwarteten
Befund dokumentiert.
**Akzeptanz, neu (Rev. 0.5, RVW-1; als **eigener Step** in der dritten Korrekturrunde, RVW2-6) —
Abschluss-Sync-Lauf der Welle:** W4-1 und W4-3 erzeugen
zwei neue getrackte `docs/**/*.md`-Pfade (`docs/architecture/00-overview-full.md`,
`docs/architecture/INDEX.md`), die in `docs/INDEX.md` noch nicht stehen ⇒ **V2
(`check_docs_index_completeness`, ERROR) ist bei W4-Abschluss planmäßig rot**. Termin der
Behebung ist der **Abschluss-Sync-Lauf in W4-3, Schritt 4**; Owner `tester`. **Kein neuer Task und
kein neues Datei-`Ownership`:** `docs/INDEX.md` bleibt im Besitz des Generators aus **W3-6**; ein
Sync-Lauf ist Ausführung, nicht Schreib-Ownership. Der Index-Diff ist **Teil des W4-3-Reviews**
(erwartet: genau die zwei neuen Pfade, `facts-hash` ändert sich, kein Zeitstempel — IC-14).
**Verifikation:** `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**;
~~`python3 scripts/consistency-check.py --strict` → **0** (V3)~~ **unter der Geltungsregel**
(Task-Verifikation, **kein** Welle-Gate; RVW-3 — V3 ist in W4 planmäßig rot, Termin **W8-2**);
`python3 scripts/sync.py --validate` → **planmäßig rot** (`W-VALIDATE-ROT`: V3 bis **W8-2**, V2
bis Schritt 4).
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: `docs/architecture/INDEX.md` generieren lassen; Test auf W5-3 vorbereiten.
- [ ] 3: Tests bzw. erwarteten Zwischenbefund beobachten; `--validate` als planmäßig rot beobachten
      (V3 Termin **W8-2**, V2 Termin Schritt 4 — **RVW3-7** korrigiert; die Fassung davor nannte
      fälschlich „Schritt 5", das ist der Commit).
- [ ] 4: **Abschluss-Sync-Lauf der Welle (RVW2-6, neu in Rev. 0.5, Normativitätstabelle Spec
      §17.9.4 Punkt (viii)):** `python3 scripts/sync.py` mit `docs-consolidation.enabled: true`
      laufen lassen, sodass `docs/INDEX.md` die zwei neuen Pfade aufnimmt; **Index-Diff im
      Task-Review prüfen** (erwartet: genau `docs/architecture/00-overview-full.md` und
      `docs/architecture/INDEX.md`, `facts-hash` ändert sich, **kein** Zeitstempel — IC-14); danach
      `W-GATE`/`W-GATE-TABLE` Spalte **W4** auswerten (V1/V4/V5/V6 0, V2 0, V7 planmäßig rot Termin
      **W5-3**, V3 planmäßig rot Termin **W8-2**). **Kein** neues Datei-`Ownership`.
- [ ] 5: commit via `git`-Agent: `test: cover architecture stub shape after move`.

---

## W5 — Guides-Auflösung und Wiki-Annotation

**Verifikation W5 (erwartete Exit-Codes):**
- `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**
- ~~`python3 scripts/sync.py --validate` → **0**~~
  **UMGESTELLT (dritte Korrekturrunde, RVW2-2) — planmäßig rot.** Verursachende Doku-ERROR-Checks
  in W5: **V3** (Termin **W8-2**, Owner `developer`) und **V2** (neue getrackte `docs/**/*.md` aus
  **W5-1** (`docs/plans/…-oq9.md`) und **W5-2** (`docs/guides/admin-ui-remote-access.md`; der zweite
  `git mv` betrifft eine `.yaml.example` und ist für V2 **ohne** Belag — RVW2-8), Termin **W5-2** =
  Abschluss-Sync-Lauf, Owner `developer`). **Maßgeblich ist `W-VALIDATE-ROT`** (Wellenblock
  W2 — Verifikation): planmäßig rot bis einschließlich **W8-2**, spätester Termin 0 **W8-4**,
  Owner `validator`, Grundlage **Spec §6(b) / §10, Aufzählungspunkt `--validate`**.
- ~~`python3 scripts/consistency-check.py --strict` → **0** (V7 grün nach der Annotation)~~
  **UMGESTELLT (Rev. 0.5, RVW-3) — der Klammertext „V7 grün" galt erst mit W5-3, dem letzten
  Task dieser Welle.** **Maßgeblich ist W-GATE + W-GATE-TABLE, Spalte W5:** V1 0 · V4 0 · V5 0 ·
  V6 0 · **V7 0** (W5-3 annotiert die Wiki-Seiten additiv mit `derived-from`/`derived-at`) ·
  **V3 planmäßig rot** (Termin **W8-2**, Owner `developer`) · **V2 planmäßig rot**, weil W5-1 und
  W5-2 neue `docs/**/*.md`-Pfade erzeugen — Termin **W5-2** (Abschluss-Sync-Lauf, **eigener
  Step**, Owner `developer`) · `docs-checks` = **Dokuzeile** (RVW2-1). **Die Task-Zeile W5-3 bleibt
  unter der Geltungsregel** (Task-Verifikation, **kein** Welle-Gate).
- `test ! -e howto` → **0**; `test ! -e docs/howto` → **0**
- `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0**
**Review W5:** `code-reviewer` (Additiv-Garantie) → `knowledge-linter` (Frontmatter/OKF) →
`validator` (AC-28-Teil, AC-31).
**Gate bei CHANGES_REQUESTED:** jede **gelöschte** Zeile außer der Ersetzung eines bestehenden
`status:`-Werts ⇒ **Stopp** (AC-31-Additivität).
**Rollback W5:** beide `git mv` zurück; `docs/howto/` wiederherstellen; Annotationen additiv
revertieren (je annotierter Wiki-Seite `git checkout`, commitweise rückwärts).

### W5-1: DEC-OQ9 — SSoT der beiden Beispiel-Configs

**Files:** Create `docs/plans/2026-09-25-docs-consolidation-oq9.md`
**Interfaces:** Produces: SSoT-Entscheidung zwischen `docs/guides/project.yaml.example` (179 Z) und
`docs/guides/configs/project.yaml.example` (340 Z) + Folge-Edit in beiden Dateien.
Consumes: Spec §11.1 OQ9, F24, NG-1.
**Agent:** technical-writer · **Depends on:** W4-3, W0-7 · **parallel_group:** PG-3 (seriell)
**Ziel-AK (AC):** **AC-28** (Teil, M-5-Ziel) · **V-Check:** **V2**
**Akzeptanz:** Entscheidung **vor** W5-2 (Spec §11.1 OQ9, Blockade W5); Ergebnis ist eine Zeile im
generierten `docs/INDEX.md`, Abschnitt `## guides` (IC-10(d)) plus ein Pointer in **beiden** Dateien
— **kein** Merge, **keine** Löschung (NG-1: eine Löschung würde Beispielkonfiguration entfernen).
**RVW2-8 (Klarstellung ohne OQ9-Entscheidung):** Spec §11.1 formuliert den Ergebnis-Ort als
„eine `docs/guides/INDEX.md`-Zeile". **Eine Datei `docs/guides/INDEX.md` wird von keiner Welle
angelegt** — W5-1 `Files:` nennt nur `docs/plans/2026-09-25-docs-consolidation-oq9.md`. Gemeint
ist die Zeile im generierten `docs/INDEX.md`; das ist eine **Klarstellung**, keine Entscheidung.
**Folge für V2 (neu festgestellt, ehrlich benannt):** W5-1 legt mit
`docs/plans/2026-09-25-docs-consolidation-oq9.md` eine **getrackte `docs/**/*.md`** an, die in
`docs/INDEX.md` noch nicht steht ⇒ **V2 ist bereits ab W5-1 planmäßig rot** (nicht erst ab W5-2).
Termin bleibt der **Abschluss-Sync-Lauf am Wellenende**, jetzt als **eigener Step 4 in W5-2**
(Owner `developer`); Fußnote ¹ der W-GATE-Tabelle ist entsprechend ergänzt. Sollte die Entscheidung
doch als eigene `docs/guides/INDEX.md` geführt werden, ist die Fußnote vor dem ersten W5-Lauf
nachzuziehen.
**Verifikation:** `wc -l docs/guides/project.yaml.example docs/guides/configs/project.yaml.example`
→ **179** / **340**.
**Steps:**
- [ ] 1: Reichweiten beider Dateien vergleichen (ohne Rewrite).
- [ ] 2: Entscheidung festhalten (Spec-Empfehlung: 340 Z = vollständige Referenz, 179 Z =
      Kurzfassung mit Pointer darauf).
- [ ] 3: Pointer-Edit für W5-2 vormerken.
- [ ] 4: commit via `git`-Agent: `docs: decide OQ9 example config single source`.

### W5-2: M-5 und M-6 (`git mv` der Guides)

**Files:** Move `howto/configs/project.yaml.example` → `docs/guides/configs/project.yaml.example`;
Move `docs/howto/admin-ui-remote-access.md` → `docs/guides/admin-ui-remote-access.md`;
entfernen: `docs/howto/` (leer) und `howto/` (Root)
**Interfaces:** Produces: **ein** Guide-Ort `docs/guides/`; Pointer-Zeile aus W5-1 in beiden
Beispiel-Configs. Consumes: W5-1.
**Agent:** developer · **Depends on:** W5-1 · **parallel_group:** PG-3 (seriell)
**Ziel-AK (AC):** **AC-28** (Teil, M-5, M-6) · **V-Check:** **V2**, **V3**
**Akzeptanz:** `git log -M` zeigt R100 für beide Dateien; `docs/INDEX.md` erkennt die neuen Pfade
bei der nächsten Generierung; `howto/` und `docs/howto/` existieren **nicht** mehr (F6, F15, F23).
**Verifikation:** `test ! -e howto` → **0**; `test ! -e docs/howto` → **0**;
`python3 scripts/sync.py --check` → **0** (Drift-Lauf, **kein** Consistency-Nachweis — RVW2-13);
`python3 scripts/sync.py --validate` → **planmäßig rot** (`W-VALIDATE-ROT`: V3 bis **W8-2**).
**Zusatz (Rev. 0.5, RVW-1; korrigiert in der dritten Korrekturrunde, RVW2-6/RVW2-8) —
Abschluss-Sync-Lauf der Welle, jetzt ein **eigener Step mit Checkbox**:** W5-1 und W5-2 erzeugen
**zwei** neue getrackte `docs/**/*.md`: `docs/plans/2026-09-25-docs-consolidation-oq9.md` (W5-1)
und `docs/guides/admin-ui-remote-access.md` (W5-2). Der zweite `git mv` dieser Task
(`docs/guides/configs/project.yaml.example`) ist **keine** `.md`-Datei und damit für V2
**ohne** Belag (IC-05: „jede **getrackte** `docs/**/*.md`"; **RVW2-8** — die Fassung vor dieser
Korrekturrunde nannte ihn fälschlich). **V2 ist deshalb ab W5-1 planmäßig rot**; Termin ist der
**Abschluss-Sync-Lauf am Ende von W5-2** (Schritt 4), Owner `developer`. `docs/INDEX.md` bleibt
Besitz des Generators aus W3-6; der Index-Diff gehört in das **W5-2-Review**.
**Steps:**
- [ ] 1: Beide `git mv` ausführen; `howto/` und `docs/howto/` entfernen.
- [ ] 2: Pointer aus W5-1 additiv eintragen.
- [ ] 3: `--check` und V2/V3 beobachten (V2 planmäßig rot, Termin Schritt 4).
- [ ] 4: **Abschluss-Sync-Lauf der Welle (RVW2-6, neu in Rev. 0.5, Normativitätstabelle Spec
      §17.9.4 Punkt (viii)):** `python3 scripts/sync.py` mit `docs-consolidation.enabled: true`
      laufen lassen, sodass `docs/INDEX.md` die neuen Pfade aufnimmt; **Index-Diff im Task-Review
      prüfen** (erwartet: genau die neuen Pfade, `facts-hash` ändert sich, **kein** Zeitstempel —
      IC-14); danach `W-GATE`/`W-GATE-TABLE` Spalte **W5** auswerten (V2 0; **V7 planmäßig rot,
      Termin W5-3** — W5-3 läuft **nach** dieser Task und setzt V7 auf 0; V3 planmäßig rot mit
      Termin **W8-2**). **Kein** neues Datei-`Ownership` — `docs/INDEX.md` bleibt Eigentum
      des Generators aus W3-6.
- [ ] 5: commit via `git`-Agent: `docs: consolidate guide locations under docs/guides`.

### W5-3: M-9/M-10 — `derived-from`-Annotation und Architektur-Redirects

**Files:** Modify `knowledge/wiki/**/*.md` (additive Frontmatter-Zeilen),
`knowledge/wiki/concepts/architecture*.md` (Kurzform-Redirects);
Modify `tests/test_docs_consolidation_migration.py`
**Interfaces:** Produces: `derived-from: <existierender Rel-Pfad>` + `derived-at: <ISO-8601>`;
`SSoT: docs/architecture/…`-Redirect für die Architektur-Wiki-Seiten. Consumes: W5-2, W0-7, W1-4.
**Agent:** tester · **Depends on:** W5-2, W0-7 · **parallel_group:** PG-3 (seriell)
**Ziel-AK (AC):** **AC-31** (IC-17, IC-03), **AC-29(c)** · **V-Check:** **V7**
**Akzeptanz:** `test_wiki_annotation_is_additive` grün — der Diff ist **ausschließlich** additiv
(keine gelöschte Zeile außer der Ersetzung eines bestehenden `status:`-Werts); jede annotierte
Seite trägt `derived-from` **und** `derived-at`; `knowledge/sources/` ist **unberührt** (NG-2).
**Verifikation:** `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**;
`python3 scripts/consistency-check.py --strict` → **0** (V7);
`git diff --stat -- knowledge/sources/` → **0 Dateien**.
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: Annotationen additiv setzen; Architektur-Seiten auf
      `docs/architecture/00-overview-full.md` umhängen (IC-03 liest **nicht** aus dem Stub).
- [ ] 3: Tests grün beobachten; V7 beobachten.
- [ ] 4: commit via `git`-Agent: `docs: annotate wiki pages with derived-from provenance`.

---

## W6 — Spec/Plan-Legacy archivieren

**Verifikation W6 (erwartete Exit-Codes):**
- `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**
- `test ! -e docs/superpowers` → **0**
- ~~`python3 scripts/consistency-check.py --strict` → **0** (V8 grün)~~
  **UMGESTELLT (Rev. 0.5, RVW-3).** **Maßgeblich ist W-GATE + W-GATE-TABLE, Spalte W6:**
  V1 0 · V2 0 · V4 0 · V5 0 · V6 0 · **V7 0** (seit W5-3) · **V8 0** (Startwelle von V8 ist W6,
  Owner `tester` in W6-2) ·   **V3 planmäßig rot** (Termin **W8-2**, Owner `developer`) ·
  `docs-checks` = **Dokuzeile ohne Sollwert** (RVW2-1 — die Angabe „8 (V8 neu)" aus der Fassung
  davor war ein Sollwert für eine **befundliefernde** Zählung und ist **nicht** als
  Registrierungsnachweis tragfähig); die V8-**Präsenz** (Startwelle W6) ist über die
  **Präsenzregel** zu prüfen, die V8-**Registrierung** über Task **W6-2**.
  **Hinweis:** W6-1 verschiebt nach `docs/{specs,plans}/archive/`;
  V2 nimmt `archive/` **ausdrücklich** aus (`docs/INDEX.md`-Vollständigkeit ohne
  `archive/`, `_archive/`), W6-2 belegt das über `test_moves_are_renames`. Die Task-Zeile
  **W6-2** führt **keine** `--strict`-Zeile (RVW-9) — sie bleibt unverändert.
- ~~`python3 scripts/sync.py --validate` → **0**~~
  **UMGESTELLT (dritte Korrekturrunde, RVW2-2) — planmäßig rot.** Verursachender Doku-ERROR-Check
  in W6: **V3** (Termin **W8-2**, Owner `developer`). V2 nimmt `archive/` aus, V8 ist WARNING.
  **Maßgeblich ist `W-VALIDATE-ROT`** (Wellenblock W2 — Verifikation): planmäßig rot bis
  einschließlich **W8-2**, spätester Termin 0 **W8-4**, Owner `validator`, Grundlage **Spec §6(b) /
  §10, Aufzählungspunkt `--validate`**.
- `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0**
**Review W6:** `code-reviewer` (R+A) → `validator` (AC-28, AC-32) → `release` (B1: Release-Notes,
Minor-Bump für die Deprecation-WARNING).
**Gate bei CHANGES_REQUESTED:** Inhalts-Diff ⇒ **Stopp**; fehlende Release-Notes ⇒ Merge gesperrt
(B1/R8).
**Rollback W6:** beide `git mv` zurück, `docs/superpowers/` wiederherstellen, die zwei additiven
`legacy:`-Zeilen entfernen.

### W6-1: M-3 und M-4 (`git mv` nach `archive/superpowers/`)

**Files:** Move `docs/superpowers/specs/` → `docs/specs/archive/superpowers/`;
Move `docs/superpowers/plans/` → `docs/plans/archive/superpowers/`; entfernen: `docs/superpowers/`
**Interfaces:** Produces: zwei archivierte Legacy-Bäume; `docs/superpowers/` verschwindet (F7);
Archiv-Trennung gemäß `docs/plans/README.md`. Consumes: W5-3.
**Agent:** developer · **Depends on:** W5-3 · **parallel_group:** PG-3 (seriell)
**Ziel-AK (AC):** **AC-28** (Teil, M-3, M-4) · **V-Check:** **V8**
**Akzeptanz:** `git log -M` zeigt R100; keine Inhalte umgeschrieben.
**Verifikation:** `test ! -e docs/superpowers` → **0**;
`ls docs/specs/archive/superpowers | wc -l` → **> 0**;
`ls docs/plans/archive/superpowers | wc -l` → **> 0**.
**Steps:**
- [ ] 1: `git mv` für beide Bäume ausführen; `docs/superpowers/` entfernen.
- [ ] 2: Prüfen, dass keine Inhalte umgeschrieben wurden.
- [ ] 3: `git log -M` und V8 beobachten.
- [ ] 4: commit via `git`-Agent: `docs: archive superpowers spec and plan trees`.

### W6-2: M-13, `legacy:`-Erweiterung und AC-28-Abschlussnachweis

**Files:** Modify `.meta-config/project.yaml` (`:61-63`), `tests/test_docs_consolidation_migration.py`
**Interfaces:** Produces: `legacy:` mit **vier** Einträgen (2 alte + 2 Archivpfade);
Deprecation-WARNING statt Fehler für die alten Pfade; `test_legacy_list_extended_additively`,
`test_moves_are_renames`. Consumes: W6-1, W5-2, W4-1.
**Agent:** tester · **Depends on:** W6-1 · **parallel_group:** PG-3 (seriell)
**Ziel-AK (AC):** **AC-32** (IC-17, IC-13, IC-22), **AC-28** (M-1, M-3, M-4, M-6) · **V-Check:** **V8**
**Akzeptanz:** `test_moves_are_renames` grün: `ARCHITECTURE.full.md`, `docs/superpowers/`, `howto/`
und `docs/howto/` existieren **nicht** mehr; `git log --diff-filter=R --name-only` zeigt je Datei
ein **R**ena-**+ A**dd-Paar. `test_legacy_list_extended_additively` grün (4 Einträge).
**Verifikation:** `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**;
`grep -c 'docs/superpowers' .meta-config/project.yaml` → **2** (bleiben toleriert, B1);
`python3 scripts/sync.py --validate` → **planmäßig rot** (`W-VALIDATE-ROT`: V3 ist ERROR und bleibt
bis **W8-2** rot; die Deprecation-WARNING ist **irrelevant** für den Exit, weil
`_run_consistency_checks` nur `Severity.ERROR` zählt — `scripts/lib/cli_commands.py:174`).
**Die Formulierung „Exit bleibt 0" aus der Fassung vor dieser Korrekturrunde war falsch.**
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: `legacy:` additiv um zwei Zeilen erweitern; Release-Notes-Eintrag vorbereiten.
- [ ] 3: Tests grün beobachten; `--validate` als **planmäßig rot** beobachten (V3, Termin **W8-2**;
      die Deprecation-WARNING bleibt sichtbar).
- [ ] 4: commit via `git`-Agent: `feat: extend legacy path list for archived spec plan trees`.

---

## W7 — Knowledge-Index-Generierung (isoliert, einziger Policy-Bruch)

**Harte Voraussetzung vor W7:** Rollenpflege-/Track-A-Branch **gemergt**; `knowledge/schema.md` um
„`index.md` is generated“ ergänzt und **User-Sign-off** eingeholt (IC-19-Bedingung (a),
`knowledge/schema.md:44-46`).
**Verifikation W7 (erwartete Exit-Codes):**
- `python3 -m pytest tests/test_knowledge_index_gen.py -q` → **0**
- ~~`python3 scripts/consistency-check.py --strict` → **0** (V7)~~
  **UMGESTELLT (Rev. 0.5, RVW-3).** **Maßgeblich ist W-GATE + W-GATE-TABLE, Spalte W7:**
  V1 0 · V2 0 · V4 0 · V5 0 · V6 0 · V7 0 · V8 0 · **V3 planmäßig rot** (Termin **W8-2**, Owner
  `developer`) · `docs-checks` = **Dokuzeile** (RVW2-1). **W7 berührt keine `docs/**/*.md`** (Write-Set:
  `knowledge/schema.md`, `scripts/lib/knowledge.py`, `.meta-config/project.yaml`,
  `tests/test_knowledge_index_gen.py`, `agents/1-generic/knowledge-indexer.md`,
  `knowledge/wiki/index.md`, `knowledge/wiki/log.md`) ⇒ V2 bleibt 0 ohne Sync-Nachweis. Die
  Task-Zilen **W7-5** bleiben unter der Geltungsregel; **W7-2** führt **keine** `--strict`-Zeile
  (RVW-9).
- ~~`python3 scripts/sync.py --validate` → **0**~~
  **UMGESTELLT (dritte Korrekturrunde, RVW2-2) — planmäßig rot.** Verursachender Doku-ERROR-Check
  in W7: **V3** (Termin **W8-2**, Owner `developer`). W7 fasst keine `docs/**/*.md` an, V7 ist
  ab W5-3 0. **Maßgeblich ist `W-VALIDATE-ROT`** (Wellenblock W2 — Verifikation): planmäßig rot bis
  einschließlich **W8-2**, spätester Termin 0 **W8-4**, Owner `validator`, Grundlage **Spec §6(b) /
  §10, Aufzählungspunkt `--validate`**.
- `git diff --stat -- knowledge/wiki/log.md` → **genau 1 Zeile** (Format `knowledge/wiki/log.md:13-17`)
- `ls knowledge/wiki/index.md.sync-backup-* | wc -l` → **≥ 1**
- `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0** (KE-Write-Pfade in Szenario 54 unverändert)
**Review W7:** `code-reviewer` → `knowledge-curator` (Policy) → `validator` (AC-33…AC-35, AC-41) →
`knowledge-linter`. **Gate:** fehlende Erstsicherung oder Diff ohne vorheriges Review ⇒ **Stopp** (R2).
**Rollback W7:** `knowledge-engine.okf.index-mode: llm` (Generator stumm) **und**
`restore_wiki_index(project_root, log)` (IC-24); `agents/1-generic/knowledge-indexer.md` via
`git checkout`; `knowledge/schema.md`-Absatz via `git checkout`. W7 invalidiert keine andere Welle
(NFA-06).

### W7-1: Policy-Voraussetzung — `knowledge/schema.md`

**Files:** Modify `knowledge/schema.md` (Abschnitt „Usage“, `:41-42`)
**Interfaces:** Produces: Absatz „`index.md` is generated“ mit Verweis auf IC-19 und den
Rollback-Hebel `knowledge-engine.okf.index-mode`. Consumes: IC-19-Bedingung (a),
`knowledge/schema.md:44-46`.
**Agent:** knowledge-curator · **Depends on:** W6-2 · **parallel_group:** PG-4 (isoliert)
**Ziel-AK (AC):** **AC-35** (IC-19) · **V-Check:** — (Policy-Dokument)
**Akzeptanz:** **User-Sign-off liegt vor** (strukturelle Änderung nach
`knowledge/schema.md:44-46`); Text nennt Generator, Flag und Rückrollweg. Ohne Sign-off startet W7
**nicht** — das ist Bedingung (a) von IC-19.
**Verifikation:** `grep -n 'index.md' knowledge/schema.md` → **0** (Treffer vorhanden).
**Steps:**
- [ ] 1: Absatzentwurf nach IC-19 vorlegen.
- [ ] 2: **User-Sign-off einholen** (Gate).
- [ ] 3: Absatz einfügen.
- [ ] 4: commit via `git`-Agent: `docs: declare knowledge index as generated`.

### W7-2: `sync_wiki_index` und `log.md`-Append

**Files:** Modify `scripts/lib/knowledge.py` (`:103-205`), `.meta-config/project.yaml` (`:18-29`);
Create `tests/test_knowledge_index_gen.py`
**Interfaces:** Produces: `sync_wiki_index(agent_meta_root, project_root, config, log, dry_run) -> dict`
(No-op, wenn `knowledge-engine.okf.index-mode != "generated"`); `knowledge-engine.okf.index-mode`
**neben** dem bestehenden `auto-index: true` (`.meta-config/project.yaml:28`) in der Config.
Consumes: W7-1, Verzeichnisnamen-Muster `knowledge.py:_KNOWLEDGE_GITKEEP_SUBDIRS` (`:87-100`).
**Agent:** senior-developer · **Depends on:** W7-1 · **parallel_group:** PG-4 (isoliert)
**Ziel-AK (AC):** **AC-33** (IC-19, IC-22), **AC-34** (IC-20) · **V-Check:** **V7**
**Akzeptanz:** `test_index_mode_flag_and_determinism` grün (jede Wiki-Seite **genau einmal**,
alphabetisch ⇒ minimaler Diff); `test_log_append_only_on_change` grün (genau **eine** Zeile
`YYYY-MM-DD HH:MM — index/update — <summary>` bei Wiki-Änderung, **keine** sonst; Bestand
append-only, nie umsortiert). `index-mode: llm` ⇒ `index.md` byte-identisch.
**Verifikation:** `python3 -m pytest tests/test_knowledge_index_gen.py -q` → **0**;
`grep -n 'index-mode' .meta-config/project.yaml` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: `sync_wiki_index` + Append implementieren; `index-mode: llm` als Default.
- [ ] 3: Tests grün beobachten.
- [ ] 4: commit via `git`-Agent: `feat: add deterministic knowledge index generator`.

### W7-3: Erstsicherung und Restore-Pfad

**Files:** Modify `scripts/lib/knowledge.py`; Modify `tests/test_knowledge_index_gen.py`
**Interfaces:** Produces: Erstsicherung `index.md.sync-backup-<YYYYmmdd-HHMMSS>` vor dem ersten
Rewrite; `restore_wiki_index(project_root, log, *, dry_run=False) -> list[str]` (IC-24, Reihenfolge
Sibling-Backup → `git -C <project_root> checkout -- knowledge/wiki/index.md` → `log.error` +
**kein** Schreibzugriff). Consumes: W7-2, Muster `generated_file_drift.py:354-402, :388`.
**Agent:** senior-developer · **Depends on:** W7-2 · **parallel_group:** PG-4 (isoliert)
**Ziel-AK (AC):** **AC-35**, **AC-41** (IC-24) · **V-Check:** — (Restore-Ebene, Unit-Test)
**Akzeptanz:** `test_first_activation_is_backed_up`, `test_restore_from_backup_sibling`,
`test_restore_dry_run` und `test_restore_fails_closed_without_source` grün; Restore liefert
**exakt einen** Rel-Pfad und stellt den Alt-Inhalt byte-identisch wieder her (Vergleich über
`io.content_hash`); ohne Sicherung **und** ohne Git-Tracking: `log.error`, **kein** Write
(fail-closed, kein stiller Datenverlust). Aufruf **nur** als manueller Runbook-Schritt, **ohne**
neues CLI-Flag (NG-4).
**Verifikation:** `python3 -m pytest tests/test_knowledge_index_gen.py -q` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: Sicherung + `restore_wiki_index` implementieren (Reihenfolge ist vertraglich: Sibling
      schlägt Git, weil es den exakten Vor-Rewrite-Zustand sichert).
- [ ] 3: Tests grün beobachten; Dry-Run-Substep des Runbooks dokumentieren.
- [ ] 4: commit via `git`-Agent: `feat: add wiki index backup and restore path`.

### W7-4: `knowledge-indexer`-Umschreibung (IC-21) — **letzter Commit der Welle**

**Files:** Modify `agents/1-generic/knowledge-indexer.md`
**Interfaces:** Produces: Rolle „prüfe Generator-Output, melde Drift“ statt „schreibe `index.md`“;
provider-agnostisch. Consumes: W7-3, Rollenpflege-Branch (muss gemergt sein — R19).
**Agent:** prompt-engineer · **Depends on:** W7-3 · **parallel_group:** PG-4 (isoliert)
**Ziel-AK (AC):** **AC-35** (IC-19, IC-24, IC-21) · **V-Check:** — (Agent-Rolle)
**Akzeptanz:** **einzige** von dieser Initiative berührte Datei unter `agents/` (NFA-08); kein
Claude-Literal, keine Provider-Verzweigung; IC-21 wird als **letzter** Commit von W7 committet,
damit ein Rebase der Rollenpflege nicht in einem `agents/1-generic/`-Template-Diff landet.
**Verifikation:** `python3 -m pytest tests/test_provider_agnostic_dispatch.py -q` → **0**;
`grep -rn 'Claude' agents/1-generic/knowledge-indexer.md` → **1** (kein Treffer erwartet).
**Steps:**
- [ ] 1: Rollenpflege-Branch-Status prüfen; bei offen **stoppen** (R19).
- [ ] 2: Rolle umschreiben.
- [ ] 3: Provider-Agnostik-Guard beobachten.
- [ ] 4: commit via `git`-Agent: `docs(agent): shift knowledge-indexer to drift reporting`.

### W7-5: Aktivierung `index-mode: generated` und W7-Abschluss

**Files:** Modify `.meta-config/project.yaml`, `knowledge/wiki/index.md` (generiert),
`knowledge/wiki/log.md` (Generator-Append)
**Interfaces:** Produces: `knowledge-engine.okf.index-mode: generated`; deterministisch gerenderte
`index.md`; genau **eine** Log-Zeile. Consumes: W7-4.
**Agent:** knowledge-curator · **Depends on:** W7-4 · **parallel_group:** PG-4 (isoliert)
**Ziel-AK (AC):** **AC-33**, **AC-34**, **AC-35** · **V-Check:** **V7**
**Akzeptanz:** `index-mode: llm` ⇒ `index.md` **byte-identisch**; `index-mode: generated` ⇒
deterministisch neu gerendert, jede Wiki-Seite genau einmal; `log.md` wächst um **eine** Zeile im
Format `knowledge/wiki/log.md:13-17` (`operation ∈ {index, index/update}`).
**Verifikation:** `python3 scripts/sync.py --validate` → **planmäßig rot** (`W-VALIDATE-ROT`: V3,
Termin **W8-2**, Owner `developer`);
~~`python3 scripts/consistency-check.py --strict` → **0**~~ **unter der Geltungsregel**
(Task-Verifikation, **kein** Welle-Gate; RVW-3);
`git diff --stat -- knowledge/wiki/log.md` → **1 Zeile**.
**Steps:**
- [ ] 1: Diff-Review von `knowledge/wiki/index.md` **vor** Aktivierung (R2).
- [ ] 2: `index-mode: generated` setzen; Sync; Log-Diff prüfen.
- [ ] 3: `--validate` als **planmäßig rot** beobachten (V3) und V7 (0) auswerten.
- [ ] 4: commit via `git`-Agent: `feat: activate generated knowledge index`.

---

## W8 — Totverweise, V9, Config-Struktur, ID-Deklaration

**Verifikation W8 (erwartete Exit-Codes):**
- `python3 -m pytest tests/test_doc_facts.py tests/test_docs_consolidation_migration.py -q` → **0**
- `python3 scripts/sync.py --check` → **0** (Drift-Lauf, **kein** Consistency-Nachweis — RVW2-13)
- ~~`python3 scripts/sync.py --validate` → **0**~~
  **UMGESTELLT (dritte Korrekturrunde, RVW2-2) — Termin statt Sofortwert, und die Erreichbarkeit
  ist bedingt.** **In W8 ist V3 nach W8-2 der einzige rote Doku-ERROR-Check**; **V2** ist ab **W8-1**
  rot (neue `docs/**/*.md`) und wird erst mit dem **Abschluss-Sync-Lauf in W8-4** (Schritt 5)
  wieder 0 — **RVW3-1: die Formulierung „nach W8-2 alle Doku-ERROR-Checks 0" war falsch** und ist
  korrigiert; W8-2 und W8-3 führen keinen Sync. V9 ist **WARNING** — `_run_consistency_checks`
  zählt nur `Severity.ERROR` (`scripts/lib/cli_commands.py:174`), V9 bricht `--validate` also
  **nicht**. **Restbedingung, die nicht gemessen ist:** `--validate` summiert **alle** ERROR-Findings
  des Repo. Ist der repo-weite Altbestand `errors > 0` (Messung in **W3-7**,
  W3-BASELINE-STRICT), bleibt `→ 0` unerreichbar und maßgeblich ist die **Deltasperre**. Owner
  `validator`, Entscheidungspunkt **W3-7**, spätester Termin 0 **W8-4**. Grundlage **Spec §6(b) /
  §10, Aufzählungspunkt `--validate`**. **Der Sollwert wird nicht abgesenkt.**
- ~~`python3 scripts/consistency-check.py --strict` → **0** (V1a **und** V3 ohne Befund; V9 meldet die
  179 Altlasten als **WARNING** — lokale Aufräumaktion FI-10, kein Fehler)~~
  **UMGESTELLT (Rev. 0.5, RVW-3) — die Klammer war in sich widersprüchlich.** Sie verlangte
  gleichzeitig „V1a und V3 ohne Befund" und „V9 meldet 179 WARNINGs", verlangte mit `--strict`
  aber null **Warnings** — bei `--strict` setzt `consistency-check.py:273-274` den Exit 1
  **auch** für die V9-Warnings. **Maßgeblich ist W-GATE + W-GATE-TABLE, Spalte W8:** V1 0 ·
  **V3 0** (W8-2 behebt `README.md:721-724` — der letzte planmäßig rote ERROR-Check, M-8) ·
  V4 0 · V5 0 · V6 0 · V7 0 · V8 0 · **V2 0** nach dem Abschluss-Sync-Lauf in **W8-4** (Schritt 5,
  Owner `tester`; W8-1 legt `docs/plans/…-oq4.md` an und bearbeitet `docs/REQUIREMENTS.md`) ·
  **`docs.stale_backups` (V9): geduldet, kein Sollwert** (RVW2-4) — kein Termin 0, Owner
  `tester` (W8-4), Grund FI-10 (Abbau des Altbestands ist lokale Aufräumaktion, **kein
  Spec-Gegenstand**); die **179** sind eine **Bestandsangabe** aus dem System-Design, im Working
  Tree **nicht messbar** (gitignoriert, `.gitignore:13`/`:22`; Suche findet **eine** Datei) und
  deshalb **kein** Sollwert — maßgeblich ist die Obergrenze aus Fußnote ⁴, die erst nach der
  Bestandsaufnahme in W8-4 Schritt 1 festgeschrieben wird. **Das ist
  der Grund, warum das Aggregat `docs-findings: 0` als Wellen-Gate aufgehoben wurde** (RVW-1) —
  es wäre selbst am Ende des Vorhabens unerreichbar. · `docs-checks` = **Dokuzeile** (RVW2-1). Die
  Task-Zilen **W8-2**, **W8-3**, **W8-4** bleiben unter der Geltungsregel (Task-Verifikation,
  **kein** Welle-Gate).
- `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0**
- `grep -c 'docs/INDEX.md' AGENTS.md` → **≥ 1** (M-12-Wirkung sichtbar)
**Review W8:** `code-reviewer` → `validator` (AC-30, AC-40) → `requirements` (OQ4) → `release`
(M-12 wirkt auf alle generierten Kontextdateien, B6/R13).
**Gate bei CHANGES_REQUESTED:** der Layout-Diff in `AGENTS.md`/`CLAUDE.md` muss im Review
**explizit quittiert** werden (B6); ohne Quittung kein Merge.
**Rollback W8:** additiv revertierbar — `git checkout README.md llms.txt docs/REQUIREMENTS.md`,
`git checkout .meta-config/project.yaml`, V9-Block aus `scripts/lib/consistency/docs.py` entfernen.
Kein `git mv` betroffen ⇒ keine andere Welle invalidiert.

### W8-1: DEC-OQ4 — ID-System-Deklaration

**Files:** Create `docs/plans/2026-09-25-docs-consolidation-oq4.md`; Modify `docs/REQUIREMENTS.md`
**Interfaces:** Produces: deklarativer Abschnitt „`SPEC-*` = Spec-Pipeline-Artefakt-ID, `REQ-*` =
Requirements-Master-ID, Einweg-Verweis“; **keine** Umbenennung (NG-6). Consumes: F16.
**Agent:** requirements · **Depends on:** W7-5 · **parallel_group:** PG-5
**Ziel-AK (AC):** **AC-40** (IC-02, IC-22 — Deklaration F16 gehört in W8) · **V-Check:** **V8**
**Akzeptanz:** Entscheidung **vor** W8-3 (Spec §11.1 OQ4, Blockade W8); Deklarationsabschnitt **additiv** in
`docs/REQUIREMENTS.md` ergänzt; **keine** bestehende `SPEC-*`-ID umbenannt; Szenario
`53-spec-plan-traceability` bleibt grün.
**Verifikation:** `grep -n 'REQ-\|SPEC-' docs/REQUIREMENTS.md` → **0** (beide Muster vorhanden);
`bash tests/scenarios/run.sh 53` → **0**.
**Steps:**
- [ ] 1: Zwei-Ebenen-Modell mit `validator` abstimmen.
- [ ] 2: Deklarationsabschnitt additiv ergänzen.
- [ ] 3: Szenario 53 beobachten.
- [ ] 4: commit via `git`-Agent: `docs: declare REQ and SPEC identifier layers`.

### W8-2: M-8 — Tote interne Verweise (AC-30)

**Files:** Modify `README.md`, `tests/test_docs_consolidation_migration.py`
**Interfaces:** Produces: `README.md:721-723` auf existierende Ziele umgeschrieben bzw. entfernt;
`README.md:724` (`CLAUDE.md` als Template-Config) entfernt — die Datei existiert nicht (F15);
`test_no_dead_internal_links_after_migration`. Consumes: W4-2, W5-2, W6-1.
**Agent:** developer · **Depends on:** W8-1 · **parallel_group:** PG-5
**Ziel-AK (AC):** **AC-30** (IC-17, M-8) · **V-Check:** **V3**
**Akzeptanz:** `README.md`, `llms.txt` und `docs/**` frei von Findings auf **relative interne**
Links; V3 liefert **keine** Findings mehr (`exit 0`); keine Umbenennung von Dateien.
**Verifikation:** `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**;
~~`python3 scripts/consistency-check.py --strict` → **0**~~ **unter der Geltungsregel**
(Task-Verifikation, **kein** Welle-Gate; RVW-3 — maßgeblich ist W-GATE, Spalte **W8**).
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: Totverweise umschreiben/entfernen.
- [ ] 3: V3 beobachten (Erwartungswert **0**; Zählwert über `W-GATE`, **kein** Exit-Code).
- [ ] 4: commit via `git`-Agent: `docs: fix dead internal links in README`.

### W8-3: Providerzahl generiert (AC-40)

**Files:** Modify `llms.txt`, `README.md`, `tests/test_docs_consolidation_migration.py`
**Interfaces:** Produces: Providerzahl in `llms.txt` und `README.md:690` **ausschließlich** aus
einem `agent-meta:docs-*-Block`; `docs/INDEX.md` führt `DOCS_PROVIDERS_BLOCK`;
`test_provider_count_is_generated_in_readme_llms_index`. Consumes: W8-2, W0-3 (OQ2-Record,
**Hybrid**, Spec §11.2).
**Agent:** developer · **Depends on:** W8-2 · **parallel_group:** PG-5
**Ziel-AK (AC):** **AC-40** (IC-02, IC-22) · **V-Check:** **V1a**, **V6**
**Akzeptanz:** keine handgeschriebene Providerzahl mehr im Fließtext; Wert entspricht
`DOCS_PROVIDER_COUNT`; `llms.txt:5` führt alle 9 Providernamen oder verweist auf den Block
(`config/ai-providers.yaml:1` + 9 Blöcke).
**Verifikation:** `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**;
~~`python3 scripts/consistency-check.py --strict` → **0**~~ **unter der Geltungsregel** (RVW-3);
`python3 scripts/sync.py --check` → **0** (Drift-Lauf, **kein** Consistency-Nachweis — RVW2-13).
**`--validate` ist hier planmäßig rot:** V3 ist ab W8-2 0, aber **V2** ist es erst mit dem
Abschluss-Sync-Lauf in **W8-4, Schritt 5** (`W-VALIDATE-ROT`).
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: `DOCS_PROVIDERS_BLOCK` in beide Dateien einbinden; Prosa drumherum erhalten
      (OQ2-Hybrid, NG-1).
- [ ] 3: Tests grün beobachten; V1a/V6 beobachten.
- [ ] 4: commit via `git`-Agent: `docs: generate provider count in README and llms.txt`.

### W8-4: V9, M-12 und Abschluss

**Files:** Modify `scripts/lib/consistency/docs.py`, `.meta-config/project.yaml` (`:205-221` — **nur**
`PROJECT_STRUCTURE`, M-12), `tests/test_doc_facts.py`. **Kein** neuer `docs-consolidation`-Key —
siehe Klammer bei `Interfaces:`.
**Interfaces:** Produces: `check_stale_backups(root, config=None)` (**WARNING**,
`*.sync-backup-*` älter als N Tage, Muster `.gitignore:22`); `PROJECT_STRUCTURE` um `docs/INDEX.md`,
`docs/guides/configs/`, `docs/providers/`, `docs/se-cascade/`, `docs/concepts/` ergänzt (M-12).
**RVW2-7 (Korrektur) — die V9-Altersschwelle N ist KEIN Config-Key.** IC-22 legt für
`docs-consolidation` **sechs** Keys fest, und der Schema-Block ist **geschlossen**:
`config/project-config.schema.json:2421-2470` — `properties` mit `enabled`, `index-mode`,
`checks` (darin `checks.strict`), `sources`, `volatile-facts` und `additionalProperties: false`
(derselbe Wert in `checks`, `:2449`). Ein zusätzlicher Key — etwa `checks.stale-backup-days` —
wäre ein **siebter** Key, für den weder IC-22 noch M-11 (Spec IC-17, M-11: „neuer Top-Level-Block
`docs-consolidation` mit den 6 Keys aus IC-22, `additionalProperties: false`") eine Grundlage hat,
und würde die Projekt-Config **schema-invalid** machen. **Korrigierte Fassung:** N ist eine
**Modulkonstante** in `scripts/lib/consistency/docs.py` — Muster `V1_SCAN_RELPATHS`,
`V1_GENERATED_RELPATHS`, `V1_MAX_TOKEN_GAP` (`docs.py:158`, `:162`, `:164`), also ein im Repo
**bereits etabliertes** Muster für schwellenartige V9-Parameter. Der **Wert** von N wird in
W8-4 Schritt 1 festgelegt und im W8-4-Review-Protokoll als `V9-ALTERSSCHWELLE = <N>` festgehalten;
er wird hier **nicht** vorweggenommen, weil er im Ist-Zustand **nicht messbar** ist. **Wäre ein
Config-Key gewünscht**, ist das eine **neue normative Pflicht** (neuer Key in IC-22 **und** M-11,
Nachlieferung über W1-9) und **hier nicht beschlossen** — siehe **ESCALATION E-2**, Spec §17.9.4,
Entscheidungsvorlagen (E-2). **Frist: vor W8-4 Schritt 1** — diese Task setzt N bereits als
Modulkonstante um; fiele E-2 auf (b), wäre die Arbeit hinfällig und W1-9 nachzuliefern.
Consumes: W8-3.
**Agent:** tester · **Depends on:** W8-3 · **parallel_group:** PG-5
**Ziel-AK (AC):** **AC-30** (V3-Nachweis), **AC-40** · **V-Check:** **V9**
**Spec-Lücke (ehrlich benannt, nicht kaschiert):** **V9 hat in der Spec kein AC** — §9.1 führt
V1–V8, V9 erscheint nur in IC-05 mit Start W8. Eine AC zu erfinden wäre eine Spec-Änderung und
unterbleibt. V9 wird in W8-4 implementiert und nachgewiesen über **W-GATE-TABLE, Zeile
`docs.stale_backups`: geduldet, kein Sollwert** sowie FI-10 („Abbau des Altbestands ist lokale
Aufräumaktion, kein Spec-Gegenstand“). **RVW-1/RVW-3 (Korrektur):** die frühere Formulierung
`--strict` (Exit **0**, „V9 meldet ausschließlich WARNING") war **in sich widersprüchlich** — bei
`--strict` setzt `scripts/consistency-check.py:273-274` den Exit 1 **auch** für WARNINGs, V9
könnte also nie Exit 0 liefern. **RVW2-4 (Korrektur):** die Formulierung „V9 meldet die
**179** Altlasten" wird als **Bestandsangabe** geführt, **nicht** als Sollwert — die 179 stammen aus
System-Design/FI-10, liegen in `.claude/agents/` (gitignoriert, `.gitignore:13`, `:22`) und sind im
Working Tree **nicht messbar** (Suche findet **eine** Datei). **Die inhaltliche Aussage bleibt:**
V9 meldet den Altbestand, und der bleibt unangetastet.
**Akzeptanz:** M-12 wirkt sichtbar in `AGENTS.md`/`CLAUDE.md` (managed block,
`context.py:36-38`; Drift-Detection fängt Handpflege ab); der Altbestand an `*.sync-backup-*`
bleibt **unangetastet**.
**Bestandsaufnahme (RVW2-4, neu, verbindlich):** **vor** der Implementierung wird der Zählwert als
`BACKUP-BASELINE = <n>` in das W8-4-Review-Protokoll geschrieben (Owner `tester`). Erst danach wird
die **Obergrenze** festgeschrieben — ebenfalls **nur** als Artefakt dieses Review-Protokolls
(`V9-OBERGRENZE`); **ein Nachtrag in der Spec (IC-05, V9-Zeile) findet nicht statt** (RVW3-6: die
ausführende Task trägt keinen neuen Sollwert in die normative Quelle ein — das wäre ohne
Revisions-Bump, Concept-Review und Freigabe ein Spec-Verstoß nach §2.2). **Vorher wird keine Zahl
als Sollwert geführt.**
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**;
~~`python3 scripts/consistency-check.py --strict` → **0**~~ **unter der Geltungsregel** (RVW-3);
`python3 scripts/sync.py --validate` → **0 erst nach Schritt 5** (bis dahin planmäßig rot wegen V2,
`W-VALIDATE-ROT`; zusätzlich bedingt auf die Baseline aus W3-7, siehe dort Rückfallregel (b));
`grep -c 'docs/INDEX.md' AGENTS.md` → **≥ 1**.
**Zusatz, neu (Rev. 0.5, RVW-1; als **eigener Step** in der dritten Korrekturrunde, RVW2-6):
Abschluss-Sync-Lauf der Welle:** W8-1 legt `docs/plans/2026-09-25-docs-consolidation-oq4.md`
an und bearbeitet `docs/REQUIREMENTS.md` ⇒ **V2 ist bis zum Sync-Lauf am Ende von W8-4
planmäßig rot**; Termin **W8-4, Schritt 5**, Owner `tester`. `docs/INDEX.md` bleibt Besitz des
Generators aus W3-6. Die `docs.stale_backups`-Zeile (V9) bleibt **geduldet ohne Sollwert** — FI-10,
Obergrenze nach Bestandsaufnahme.
**Steps:**
- [ ] 1: **Bestandsaufnahme** `*.sync-backup-*` in den Provider-Verzeichnissen (Muster
      `.gitignore:22`) ⇒ `BACKUP-BASELINE = <n>` ins W8-4-Review-Protokoll; danach V9
      implementieren (Severity **WARNING**; Altersschwelle N als **Modulkonstante** in
      `scripts/lib/consistency/docs.py`, Muster `V1_SCAN_RELPATHS`/`V1_MAX_TOKEN_GAP`,
      `docs.py:158`/`:164` — **kein** Config-Key, siehe Klammer).
- [ ] 2: `PROJECT_STRUCTURE` additiv ergänzen; Sync ⇒ Layout-Diff.
- [ ] 3: Layout-Diff im Review quittieren lassen (B6/R13).
- [ ] 4: Obergrenze für V9 aus `BACKUP-BASELINE` + Toleranz festschreiben und **ausschließlich**
      im W8-4-Review-Protokoll als `V9-OBERGRENZE` festhalten. **Kein** Nachtrag in der Spec
      (IC-05 bleibt unverändert — RVW3-6); die Entscheidung ist **nicht** stille, sie ist genau
      dort protokolliert.
- [ ] 5: **Abschluss-Sync-Lauf der Welle (RVW2-6, neu in Rev. 0.5, Normativitätstabelle Spec
      §17.9.4 Punkt (viii)):** `python3 scripts/sync.py` mit `docs-consolidation.enabled: true`
      laufen lassen, sodass `docs/INDEX.md` `docs/plans/2026-09-25-docs-consolidation-oq4.md` und
      `docs/REQUIREMENTS.md` aufnimmt; **Index-Diff im Task-Review prüfen** (IC-14: `facts-hash`
      ändert sich, **kein** Zeitstempel); danach `W-GATE`/`W-GATE-TABLE` Spalte **W8** auswerten
      (V1…V8 = 0, V9 geduldet) und `python3 scripts/sync.py --validate` beobachten.
- [ ] 6: commit via `git`-Agent: `feat: add V9 stale backup check and project structure fix`.

---

## Reihenfolge-/Abhängigkeitsmatrix

| Task | Welle | Agent | Depends on | parallel_group | AC | V-Check | Datei-Ownership (Schreibmenge) |
|---|---|---|---|---|---|---|---|
| W0-1 | W0 | orchestrator | W0-2 | — (Gate) | AC-20/21/12 | — | `docs/plans/…-oq6.md` |
| W0-2 | W0 | git | — | — | AC-01…41 (Anker) | — | `docs/plans/…-wave0-freeze.md` + Branches |
| W0-3 | W0 | agent-meta-manager | W0-2 | W0-PG-B | AC-25/40 | — | `docs/plans/…-oq2.md` |
| W0-4 | W0 | orchestrator | W0-2 | W0-PG-B | AC-07/08/39 | — | `docs/plans/…-track-a-gate.md` |
| W0-6 | W0 | orchestrator | W0-2 | W0-PG-B | AC-12/38 | V2 | `docs/plans/…-oq8.md` |
| W0-7 | W0 | orchestrator | W0-2 | W0-PG-B | AC-31 | V7 | `docs/plans/…-oq1.md` |
| W1-1 | W1 | senior-developer | W0-1, W0-4 | PG-1/W1-A | AC-01 | — | `scripts/lib/doc_facts.py`, `tests/test_doc_facts.py` |
| W1-2 | W1 | senior-developer | W1-1 | PG-1/W1-A | AC-02, AC-03 | — | dieselben 2 |
| W1-3 | W1 | senior-developer | W1-2 | PG-1/W1-A | AC-04, AC-05 | V5 | dieselben 2 |
| W1-4 | W1 | senior-developer | W1-3 | PG-1/W1-A | AC-10, AC-29c | V7 | dieselben 2 |
| W1-5 | W1 | senior-developer | W1-2 | PG-1/W1-A | AC-36, NFA-11 | V6 | + `config/doc-facts-expected.yaml`, `tests/test_doc_facts_expected.py` |
| W1-6 | W1 | developer | W1-4, W0-3 | PG-1/W1-A | AC-25, AC-06 | — | + `scripts/lib/config.py`, `scripts/lib/consistency/placeholders.py`, `snippets/docs/*.md` (6) |
| W1-7 | W1 | senior-developer | W1-1 | PG-1/W1-B | AC-14/15/16/27 | V6 | `scripts/lib/doc_renderer.py`, `tests/test_doc_renderer.py` |
| W1-8 | W1 | senior-developer | W1-7 | PG-1/W1-B | AC-17 (Modell), NFA-01 | V2 | + `scripts/lib/doc_index.py` |
| W1-10 | W1 | developer | W1-8 | PG-1/W1-B | AC-24 | alle | + `.meta-config/project.yaml` |
| W1-9 | W1 | developer | W0-4 | PG-1/W1-C | AC-39 | — | `config/project-config.schema.json`, `tests/test_docs_consolidation_migration.py` |
| W2-1 | W2 | developer | W1-6, W0-4 | PG-2/W2 | AC-07, AC-08 | V1a, V1b | `scripts/lib/consistency/docs.py`, `tests/fixtures/docs_v1_fixtures.md`, `tests/test_doc_facts.py` (**Rev. 0.5, K16:** zusätzlich Schritt 4 — Rule-3-Eingrenzung in `docs.py` + Sichtbarkeitstest) |
| W2-2 | W2 | developer | W2-1 | PG-2/W2 | AC-09 | V3 | `docs.py`, `tests/test_doc_facts.py` |
| W2-3 | W2 | developer | W2-2 | PG-2/W2 | AC-10 | V7 | dieselben 2 |
| W2-4 | W2 | developer | W2-3 | PG-2/W2 | AC-11 | V5 | dieselben 2 |
| W2-5 | W2 | developer | W2-4 | PG-2/W2 | AC-36 | V6 | `docs.py`, `tests/test_doc_facts_expected.py` |
| W2-6 | W2 | developer | W2-5 | PG-2/W2 | AC-12 | V2, V4 | `docs.py`, `tests/test_doc_facts.py` |
| W2-7 | W2 | developer | W2-6 | PG-2/W2 | AC-13, AC-24 | alle | + `scripts/consistency-check.py`, **`scripts/lib/consistency/report.py` (Rev. 0.5, K15 — B-5/E-15: `line`/`branch` als Dataclass-Felder, F1-PROMOTION)**, `tests/test_doc_facts.py` **zweimal**: Modul (bestanden) + **positiver Registrierungs-Pin in Schritt 1 (RVW2-5)** |
| W3-1 | W3 | senior-developer | W1-10 | PG-2/W3 | AC-23, AC-26 | V6 | `scripts/lib/doc_renderer.py`, `doc_index.py`, `tests/test_doc_renderer.py` |
| W3-2 | W3 | senior-developer | W3-1 | PG-2/W3 | AC-17, AC-18, AC-03 | V2, V6 | `doc_renderer.py`, `tests/test_doc_renderer.py` |
| W3-3 | W3 | senior-developer | W3-2 | PG-2/W3 | AC-21 | V4 | + `scripts/lib/spec_plan_scaffold.py` |
| W3-4 | W3 | senior-developer | W3-3, **W2-1 (Schritt 4, K16 — Rev. 0.5/RVW-4)** | PG-2/W3 | AC-22 | V1 | + `scripts/lib/sync_pipeline.py`, `.meta-config/project.yaml` |
| W3-5 | W3 | developer | W3-4 | PG-2/W3 | AC-19, AC-37 | — | + `scripts/lib/generated_file_drift.py`, `tests/test_generated_file_drift_docs.py` |
| W3-6 | W3 | senior-developer | W3-5, W0-1, W0-6 | PG-2/W3 | AC-20, AC-12, AC-38 | V2, V4 | + `docs/INDEX.md`, `README.md` (kein `.gitignore` — OQ6 entschieden) |
| W3-7 | W3 | developer | W3-6 | PG-2/W3 | AC-40 (Teil), AC-07 | V1a, V1b, V6 | + `llms.txt`, `ARCHITECTURE.md`, `README.md` |
| W4-1 | W4 | developer | W3-6 | PG-3 (seriell) | AC-28 (Teil), AC-29b | V3 | `ARCHITECTURE.full.md` → `docs/architecture/00-overview-full.md` |
| W4-2 | W4 | developer | W4-1 | PG-3 | AC-29a | V3 | `ARCHITECTURE.md` |
| W4-3 | W4 | tester | W4-2 | PG-3 | AC-29, AC-28 (Teil) | V3, V7 | `docs/architecture/INDEX.md`, `tests/test_docs_consolidation_migration.py`; **Schritt 4 (RVW2-6): Abschluss-Sync-Lauf — schreibt `docs/INDEX.md` nicht, der Generator aus W3-6 bleibt Eigentümer** |
| W5-1 | W5 | technical-writer | W4-3, W0-7 | PG-3 | AC-28 (Teil) | V2 | `docs/plans/…-oq9.md` (**legt eine getrackte `docs/**/*.md` an ⇒ V2 rot ab W5-1, Termin W5-2 Schritt 4**) |
| W5-2 | W5 | developer | W5-1 | PG-3 | AC-28 (Teil) | V2, V3 | `howto/configs/…` → `docs/guides/configs/…`, `docs/howto/…` → `docs/guides/…`; **Schritt 4 (RVW2-6): Abschluss-Sync-Lauf — schreibt `docs/INDEX.md` nicht, der Generator aus W3-6 bleibt Eigentümer** |
| W5-3 | W5 | tester | W5-2, W0-7 | PG-3 | AC-31, AC-29c | V7 | `knowledge/wiki/**/*.md`, `tests/test_docs_consolidation_migration.py` |
| W6-1 | W6 | developer | W5-3 | PG-3 | AC-28 (Teil) | V8 | `docs/superpowers/**` → `docs/{specs,plans}/archive/superpowers/**` |
| W6-2 | W6 | tester | W6-1 | PG-3 | AC-32, AC-28 | V8 | `.meta-config/project.yaml`, `tests/test_docs_consolidation_migration.py` |
| W7-1 | W7 | knowledge-curator | W6-2 | PG-4 (isoliert) | AC-35 | — | `knowledge/schema.md` |
| W7-2 | W7 | senior-developer | W7-1 | PG-4 | AC-33, AC-34 | V7 | `scripts/lib/knowledge.py`, `.meta-config/project.yaml`, `tests/test_knowledge_index_gen.py` |
| W7-3 | W7 | senior-developer | W7-2 | PG-4 | AC-35, AC-41 | — | `scripts/lib/knowledge.py`, `tests/test_knowledge_index_gen.py` |
| W7-4 | W7 | prompt-engineer | W7-3 | PG-4 | AC-35 | — | `agents/1-generic/knowledge-indexer.md` |
| W7-5 | W7 | knowledge-curator | W7-4 | PG-4 | AC-33/34/35 | V7 | `.meta-config/project.yaml`, `knowledge/wiki/index.md`, `knowledge/wiki/log.md` |
| W8-1 | W8 | requirements | W7-5 | PG-5 | AC-40 | V8 | `docs/plans/…-oq4.md`, `docs/REQUIREMENTS.md` |
| W8-2 | W8 | developer | W8-1 | PG-5 | AC-30 | V3 | `README.md`, `tests/test_docs_consolidation_migration.py` |
| W8-3 | W8 | developer | W8-2 | PG-5 | AC-40 | V1a, V6 | `llms.txt`, `README.md`, `tests/test_docs_consolidation_migration.py` |
| W8-4 | W8 | tester | W8-3 | PG-5 | AC-30, AC-40 | V9 | `scripts/lib/consistency/docs.py` (**V9-ALTERSSCHWELLE als Modulkonstante, kein Config-Key — RVW2-7**), `.meta-config/project.yaml` (**nur** `PROJECT_STRUCTURE`, M-12), `tests/test_doc_facts.py`; **Schritt 5 (RVW2-6): Abschluss-Sync-Lauf — schreibt `docs/INDEX.md` nicht, der Generator aus W3-6 bleibt Eigentümer** |

**Zyklenprüfung:** Der Graph ist ein **DAG**. **Leitsatz (RVW2-9, korrigiert):** es gibt **keine
Rückwärtskante** (keine Kante von einer höheren auf eine niedrigere Welle) und **keine
Welle-zu-Welle-Rückkante**; zulässig sind Ketten **innerhalb** einer Welle und **Vorwärts**- oder
**Querwellenkanten** (W3-1 hängt an W1-10, W3-4 an W2-1 — beide nachgewiesen unten). Jede
**Querwelle**-Kante wird hier **namentlich** genannt. Die einzigen Ketten innerhalb einer Welle sind
W0-2 → {W0-1, W0-3, W0-4, W0-6, W0-7}, W1-1→…→W1-10 (kettenintern), W2-1→…→W2-7, W3-1→…→W3-7,
W4→W5→W6 durchgehend, W7-1→…→W7-5 und W8-1→…→W8-4. **Querwellenkanten (vollständig):**
**W1-1→W1-2…** (kettenintern, W1), **W1-5→W2-5**, **W1-6→W2-1**, **W1-8→W1-9** (alle in W1),
**W1-10→W3-1**, **W0-4→W1-1**, **W2-1→W3-4**, **W3-6→W4-1**, **W4-3→W5-1**, **W6-2→W7-1**,
**W7-5→W8-1**. **Alle zeigen auf eine frühere oder dieselbe Welle.** **Keine Zyklen.**

**Rev. 0.5, K16/RVW-4 — die Kante `W2-1 → W3-4` (korrigiert).** Die Fassung vor diesem Review
führte die Bindung „W3-4 setzt `checks.strict: true` erst nach W2-1 Schritt 4" als
**Ausführungsreihenfolge-Vorbedingung ohne Kante** und begründte das mit: „eine Kante W3-4 → W2-1
wäre eine Rückwärtskante und würde die Zyklenprüfung brechen". **Diese Begründung war falsch:**
sie verwechselte die Kantenrichtung. Die tatsächliche Bindung ist **`W2-1 → W3-4`**, und sie ist
eine **Vorwärts**kante über die Wellengrenze (W2 liegt vor W3) — sie erzeugt **keinen** Zyklus
und **keine** Rückwärtskante. Sie ist jetzt als **echte Kante** in der Matrix Zeile **W3-4**
geführt (`Depends on: W3-3, W2-1`) und in der Wellen-Tabelle unter der Spalte „Abhängig von"
der Welle **W3**. **Warum das die Zyklenprüfung nicht bricht — expliziter Nachweis:**
(a) W3-4 hat Vorgänger **nur** in W3 (W3-3) und in der **früheren** Welle W2 (W2-1); es hat
**keinen** Vorgänger in einer späteren Welle; (b) W2-1 hat Vorgänger **nur** in W2 (W1-6) und in
der früheren Welle W1 (W0-4) — **keine** Kante zeigt auf W3-4 zurück; (c) eine Kette
W3-4 → … → W3-7 existiert, endet aber in W3 und kehrt **nicht** nach W2 zurück; (d) der
Präzedenzfall existiert bereits: **W3-1** hängt an **W1-10** (Welle W1), ohne den Graphen zu
verändern. **Folge für die Parallelität:** W2 ‖ W3 bleiben bezüglich der **Write-Sets**
disjunkt (unverändert), aber **W3-4 kann nicht starten, bevor W2-1 Schritt 4 abgeschlossen
ist** — der Start von W3-4 ist damit **sequenziell** an W2-1 gebunden, der Rest von PG-2/W3
(W3-1…W3-3 und W3-5…W3-7) bleibt parallel zu W2. **Keine neue Task-ID**: es ist **eine**
zusätzliche Kante auf einen **existierenden** Task.

## Entscheidungs-Tasks

| OQ | Task | Owner | Position | Folge, wenn nicht entschieden |
|---|---|---|---|---|
| **OQ6** — **ENTSCHIEDEN 2026-09-26** (`tracked`, kein `.gitignore`-Eintrag) | **W0-1** = Ergebnis-Record (vor W1-10 und W3-6) | `orchestrator` | W0, vor jedem Code-Task | **entfällt** — entschieden; W0-1 dokumentiert, W3-6 schreibt `docs/INDEX.md` tracked ohne `.gitignore`-Diff (Spec §11.2) |
| **OQ8** — **ENTSCHIEDEN 2026-09-26** (Sync/Validator, kein Hook) | **W0-6** = Ergebnis-Record (vor Abschluss W3) | `orchestrator` | W0, Umsetzung in W3-6 | **entfällt** — entschieden; V2 bleibt **ERROR**, Auslöser ist der Sync-/Validator-Lauf (Spec §11.2) |
| **OQ2** — **ENTSCHIEDEN 2026-09-26** (**Hybrid**: `{{DOCS_PROVIDERS_BLOCK}}` + `{{DOCS_REPO_FACTS_BLOCK}}`, Rest Handtext) | **W0-3** = Ergebnis-Record (vor Abschluss W1) | `agent-meta-manager` | W0 | **entfällt** — entschieden; `llms.txt` ist Wert von `docs-consolidation.sources` (IC-22), Prosa bleibt handgepflegt (Spec §11.2) |
| OQ1 (offen) | W0-7 (vor Abschluss W5) | `orchestrator` → `main_chat` | W0 | W5-3 annotiert ohne Scope-Grenze; FI-4 bliebe ungebunden |
| OQ9 (offen) | W5-1 (vor W5-2) | `technical-writer` + `documenter` | W5 | zwei SSoT-Kandidaten unter `docs/guides/` ohne Kennzeichnung (F24) |
| OQ4 (offen) | W8-1 (vor W8-3) | `requirements` + `validator` | W8 | F16 (zwei ID-Systeme) bleibt undokumentiert |
| OQ3 | — (nach W8) | `requirements` via `main_chat` | außerhalb dieses Plans | eigene REQ (Spec §11.1 OQ3, nach W8) |
| OQ5, OQ7 | — | — | geschlossen (Spec §11.2) | kein Task |

## Coverage-Matrix Task → AC → Welle → V-Check

| AC | Task(s) | Welle | V-Check |
|---|---|---|---|
| AC-01 | W1-1 | W1 | — |
| AC-02 | W1-2 | W1 | — |
| AC-03 | W1-2 (volatile) + W3-2 (Index-Sektion) | W1/W3 | V6 |
| AC-04 | W1-3 | W1 | — |
| AC-05 | W1-3 | W1 | V5 |
| AC-06 | W1-6 | W1 | — |
| AC-07 | W2-1 (Erkennung) + W3-7 (Wirkung: kein Befund mehr) | W2/W3 | V1a, V1b |
| AC-08 | W2-1 | W2 | V1a, V1b |
| AC-09 | W2-2 (Fund) + W8-2 (Behebung) | W2/W8 | V3 |
| AC-10 | W1-4 (Resolver) + W2-3 (Check) | W1/W2 | V7 |
| AC-11 | W2-4 | W2 | V5 |
| AC-12 | W2-6 (Implementierung) + W3-6 (E2E) | W2/W3 | V2 |
| AC-13 | W2-7 | W2 | alle |
| AC-14 | W1-7 (Implementierung) + W3-6 (Aktivierung) | W1/W3 | V6 |
| AC-15 | W1-7 | W1 | V6 |
| AC-16 | W1-7 | W1 | V6 |
| AC-17 | W1-8 (Modell) + W3-2 (Volltext) | W1/W3 | V2 |
| AC-18 | W3-2 | W3 | — (Determinismus) |
| AC-19 | W3-5 | W3 | — (Drift-Store) |
| AC-20 | W3-6 | W3 | V4 |
| AC-21 | W3-3 | W3 | V4 |
| AC-22 | W3-4 | W3 | — |
| AC-23 | W3-1 | W3 | — |
| AC-24 | W1-10 (+ W2-7 Common-Gate) | W1/W2 | alle |
| AC-25 | W1-6 | W1 | — |
| AC-26 | W3-1 | W3 | — |
| AC-27 | W1-7 | W1 | V6 |
| AC-28 | W4-1, W4-3, W5-1, W5-2, W6-1, W6-2 | W4/W5/W6 | V8 |
| AC-29 | W1-4, W4-2, W4-3, W5-3 | W1/W4/W5 | V3, V7 |
| AC-30 | W8-2 (+ W8-4 Nachweis) | W8 | V3 |
| AC-31 | W5-3 | W5 | V7 |
| AC-32 | W6-2 | W6 | V8 |
| AC-33 | W7-2, W7-5 | W7 | V7 |
| AC-34 | W7-2, W7-5 | W7 | — |
| AC-35 | W7-1, W7-3, W7-4, W7-5 | W7 | — |
| AC-36 | W1-5 (Quelle) + W2-5 (Prüfung) | W1/W2 | V6 |
| AC-37 | W3-5 | W3 | — (Allowlist) |
| AC-38 | W3-6 (Szenario-Nachweis); Szenario-Lauf in **jeder** Welle | W3 | — (bestehender Runner) |
| AC-39 | W1-9 | W1 | — |
| AC-40 | W3-7 (README/llms-Anteil), W8-1, W8-3 | W3/W8 | V1a, V6 |
| AC-41 | W7-3 | W7 | — (Restore) |

**Alle 41 AC sind durch mindestens einen Task abgedeckt. Keine AC wird gestrichen.**
18 AC haben bewusst **keinen** Consistency-Check (Spec §16, NEW-6) und werden per Unit-Test bzw.
bestehendem Runner abgesichert: AC-01, AC-02, AC-03, AC-04, AC-06, AC-18, AC-19, AC-22, AC-23,
AC-24, AC-25, AC-26, AC-34, AC-35, AC-37, AC-38, AC-39, AC-41.

**Nicht planbar / bewusst außerhalb (mit Begründung, nicht stillschweigend):**
- **V9 hat kein AC.** Die Spec führt V1–V8 in der AC-/V-Zuordnung, V9 nur in IC-05 (Start W8).
  V9 wird in W8-4 implementiert und über **W-GATE-TABLE, Zeile `docs.stale_backups` (V9)
  = geduldet, kein Sollwert** plus FI-10 nachgewiesen. **RVW2-4:** die früher geführte Zahl
  **179** ist eine **Bestandsangabe**, im Working Tree **nicht messbar** (gitignoriert,
  `.gitignore:13`/`:22`; Suche findet **eine** Datei) und wird **nicht** als Sollwert geführt; die
  Obergrenze entsteht erst nach der Bestandsaufnahme in W8-4 Schritt 1. **Rev. 0.5, K14/RVW-1:**
  die frühere Formulierung
  „`--strict == 0`" ist aufgehoben — repo-globales `--strict == 0` ist unerreichbar (Altbestand,
  siehe W3-BASELINE-STRICT); das Doku-Aggregat `docs-findings: 0` ist **dauerhaft**
  unerreichbar, weil V9 den Altbestand **per Spezifikation unangetastet** meldet. Eine AC
  zu erfinden wäre eine Spec-Änderung.
- **`docs/CODEBASE_OVERVIEW.md`** (SSoT-Matrix §3.2) hat **kein AC** und ist über NG-3 der
  `documenter`-Ownership entzogen ⇒ kein Task; FI-2 bleibt Folge-Issue.
- **`knowledge/sources/docs/guides/`** (FI-7) — NG-2, kein Eingriff.
- **`AGENTS.md`-Bootstrap-Block** (OQ3/FI-5) — NG-5, eigene REQ nach W8.

## Risiken-Übernahme (R1–R20) und Restrisiko nach Planung

| # | W. | Planungsmaßnahme im Plan | Restrisiko nach Planung |
|---|---|---|---|
| R1 Doku-Diff-Churn | hoch | W1-2 volatile-Unterdrückung, W3-2 `docs-volatile` als letzte Sektion, Fact-Hash nur über nicht-volatile Fakten, Idempotenz-Tests in W3-1/3-2/3-7 | **niedrig** — Restdiff = genau eine Zeile pro Szenario, im Review begründet |
| R2 LLM-Handpflege-Kollision | hoch | W7-3 Erstsicherung **vor** Erst-Rewrite, IC-24-Restore, W7-5 Diff-Review vor Aktivierung, W7 isoliert und letzte Welle, `index-mode: llm` als Rollback | **niedrig** — Datenverlustpfad ist spezifiziert und getestet |
| R3 Track-A-Konflikt | hoch | W0-4 Gate-Task, W1/W2 sequenziell nach Track A, ein Commit pro Datei, Rebase vor jedem Merge, W7-4 erst nach Rollenpflege-Merge | **niedrig** |
| R4 V1-Fehlalarme | mittel | W2-1 Positiv- **und** Negativ-Fixture, `docs-exempt`-Marker, Start WARNING, `checks.strict` Default `false`; die zwei heute korrekten Handzahlen (`README.md:689`, `:695`) werden in W3-7 zu Regionen | **niedrig** — Restrisiko Fließtext („3 tests“) wird in W3-7-Wirkung sichtbar |
| R5 Rollen-Parität | niedrig | W2-4 V5 gate-bewusst und WARNING; Fix ist eigene REQ (NG-8) | **niedrig** |
| R6 Link-Check-Fehlalarme | mittel | W2-2 prüft nur relative repo-interne Pfade, ohne `http(s)://`, `mailto:`, `#anchor` | **niedrig** |
| R7 Doppel-Writer `docs/INDEX.md` | hoch | W3-3 `is_file_index_skeleton`, W3-4 verbindliche Stage-Reihenfolge, Besitzregel IC-13, `index-mode: skeleton`, Szenarien 50/51/52/54/55/56 in **jeder** Welle | **niedrig** |
| R8 Downstream-Bruch B1 | mittel | W6-2 `legacy:` additiv, ein Release Toleranz, Release-Pflicht + Minor-Bump über `release` im Review | **niedrig** |
| R9 Scope-Creep | mittel | Wellen sind additiv bzw. `git mv`-only, NG-1, OQ1/OQ9 als Entscheidungs-Tasks statt Inhaltsarbeit, NFA-08 | **niedrig** |
| R10 `AGENTS.md`-Bootstrap | niedrig | als OQ3/FI-5 bewusst außerhalb, kein Task | **niedrig** |
| R11 `CODEBASE_OVERVIEW.md` | mittel | kein Task (NG-3), FI-2 als Folge-Issue bei `documenter` | **niedrig** |
| R12 `DOCS_`-Namenskollision | mittel | W1-6 registriert nur `^DOCS_`; `DOCS_LANGUAGE`/`INTERNAL_DOCS_LANGUAGE` bleiben Built-ins; IC-02 verbietet ihre Belegung | **niedrig** |
| R13 `PROJECT_STRUCTURE`-Diff (B6) | niedrig | W8-4 additiver Config-Edit, managed block + Drift-Detection, Layout-Diff muss im Review quittiert werden | **niedrig** |
| R14 Falsche-Fakt-Kette | **hoch** | W1-5 `config/doc-facts-expected.yaml` (**elf** Werte) + `compare_expected_doc_facts`, W2-5 V6 mit `kind=expected-mismatch`; AC-02 prüft **Formeln**, nicht Zahlen | **mittel, bewusst akzeptiert** — jede gewollte Zahlenänderung macht V6 rot, bis die Datei im selben Commit mitgezogen wird (Review-Signalweg) |
| R15 Kollision über Track A hinaus | mittel | W0-4 Fixture-Gate, W1-9 Schema-Block in W1, W2-1 Fixtures nach Track-A-Merge; Szenario-Fixtures unverändert (NG-10) | **niedrig** |
| R16 PR-/Branch-Kollision | mittel | W0-2 **ein** Wellen-Branch mit sequenziellen W-Commits und Wellenkennung im Commit-Titel (Ausführungskorrektur 2026-09-26 statt acht Wellen-Branches, s. W0-2-Akzeptanz), `git mv`-Wellen zuerst mergen, ein Commit pro Datei | **niedrig** |
| R17 Downstream-Asymmetrie | mittel | Absenz-Default `false` (IC-22) für Writer **und** Checks; W2-7 Common-Gate in jedem Check; W3-1 Besitzregel | **niedrig** |
| R18 Auto-Commit-Interaktion | — | als **analysiert und nicht zutreffend** geführt (Spec: §5.2 **IC-16** (M8-Tabelle) und §12.2 **R18** — Abschnittsanker, ersetzen den Former `Spec:907`, der im Rev.-0.4-Stand nicht mehr traf; `sync_pipeline.py:1102-1117` liest den Drift-Store nicht); kein Plan-Task nötig | **keines** |
| R19 `knowledge-indexer`-Kollision | mittel | W7-4 als **letzter** Commit von W7, erst nach Rollenpflege-Merge; Rollback `git checkout` | **niedrig** |
| R20 V2-ERROR vs. menschliche Doku-Erstellung | mittel | **W0-6** entscheidet den Auslöser **vor** W3; W3-6 setzt ihn um; W3-7 dokumentiert den Vertrag | **niedrig** nach W0-6 |

## Definition of Done (Gesamtvorhaben)

1. **Alle 41 AC** sind durch je einen beobachtbaren Test oder Kommando **tatsächlich beobachtet**
   (nicht angenommen); die Coverage-Matrix ist ohne Lücke.
2. **Alle neun V-Checks sind implementiert; V1…V8 liefern in agent-meta je Check **0**
   `docs.*`-Findings, `docs.stale_backups` (V9) meldet den Altbestand und ist **geduldet**
   (FI-10).** **Neufassung in der dritten Korrekturrunde (RVW2-3)** — die Fassung davor war **in
   sich widersprüchlich**: sie behauptete „null `docs.*`-Findings" **und** legte V9 auf einen
   festen Zählwert fest; ihr Klammerzusatz „V9 wird im Doku-Scope nicht emittiert" war zudem
   **falsch** — der Doku-Scope des Gates ist `f["check"].startswith("docs.")` (W-GATE), und V9 trägt
   genau `docs.stale_backups`; W-GATE-Tabelle und W8-Block führen V9 selbst als Zeile.
   **Ersetzt sind:** (a) die Aggregation über alle neun (als DoD-Nachweis **aufgehoben**, weil
   **dauerhaft** unerreichbar — V9 meldet den Altbestand per Spezifikation **unangetastet**,
   FI-10); (b) die feste Zahl **179** als Sollwert (RVW2-4: **Bestandsangabe**, im Working Tree
   **nicht messbar** — gitignoriert, `.gitignore:13`/`:22`); (c) die Aussage `docs-checks = 9`
   (RVW2-1: der Counter zählt **befundliefernde** Checks, nicht registrierte — er ist eine
   **Dokuzeile ohne Sollwert**).
   **Maßgeblich ist jetzt die Messform:** **W-GATE + W-GATE-TABLE, Spalte W8** — Erwartungswert
   **je** V-Check, mit Termin und Owner. Am Ende des Vorhabens gilt: **V1…V8 = 0**;
   `docs.stale_backups` (V9) = **geduldet, kein Sollwert**, Obergrenze nach der Bestandsaufnahme
   in W8-4 Schritt 1; `docs-checks` = **Dokuzeile**; `docs-findings` = **kein** Kriterium.
   **Historisch aufgehobene Nachweisformen** (bleiben sichtbar, ersetzt wie oben): repo-globales
   `--strict → 0` (K14/RVW-1 — verlangt zusätzlich null Warnings aus den Bestandschecks über
   `agents/1-generic`, `agents/2-platform`, `commands/*`; belegt ist nur die Pfadabdeckung, die
   tatsächliche Warning-Emitterung ist **ungemessen** — RVW2-12) und `sync.py --validate → 0` vor
   **W8-4** (`W-VALIDATE-ROT`, RVW2-2). Ferner **W3-GATE-SCOPE** als Dokuzeile ohne Prüfkraft
   (RVW-14).
   **⚠ Entscheidungsvorlage an den Nutzer (RVW2-3, Spec §17.9.4 Punkt (vii)):** diese Neufassung
   **löst formal einen bisher im Plan behaupteten Sollwert auf** („alle neun V-Checks = null
   `docs.*`-Findings"). **Substanziell** ist sie spezifikationskonform — IC-05 führt V9 als
   `WARNING`, FI-10 stellt den Abbau ausdrücklich als „lokale Aufräumaktion, **kein
   Spec-Gegenstand**" fest, und §10 nennt **nie** ein „null `docs.*`-Findings" als Norm, sondern
   nur den datei-bezogenen `--strict`-Pflichtumfang. Der Mangel war **formal**, nicht inhaltlich.
   Weil ein Sollwert formal aufgelöst wird, ist die Neufassung **vor dem Abschluss des Vorhabens
   dem Nutzer zur Bestätigung vorzulegen** (Entscheidungsweg `main_chat` → `orchestrator`);
   **bis zur Bestätigung** bleibt die DoD-Zeile in dieser Fassung **in Kraft** — sie ist die
   **einzige Lesart, die den Vorhabensabschluss nicht dauerhaft unerreichbar macht** (Option (b)
   verlangt einen Sollwert, den V9 per FI-10 dauerhaft verhindert) und wird deshalb **vorläufig**
   angewendet, **bis E-1 entschieden ist**. **RVW3-3:** die Fassung davor begründete das mit
   „**strenger** als jede andere Lesart" — das war **falsch** (a) ist gegenüber (b) die
   **schwächere** Lesart, (b) ist die Obermenge); eine Stärke-Aussage wird **nicht** mehr geführt.
3. **11 Handzahlen = 0**: `python3 scripts/consistency-check.py` meldet **keinen**
   `docs.no_manual_counts`-Befund; `grep -c 'Repo version:' ARCHITECTURE.md` → **0**.
4. **`docs/INDEX.md` existiert, ist getrackt und 100 % generiert**; zweimaliger Sync ⇒
   `unchanged`, null Schreibvorgänge (NFA-01).
5. **11 unabhängige Sollwerte** in `config/doc-facts-expected.yaml`; AC-36 grün; die Datei wird bei
   jeder gewollten Zahlenänderung **im selben Commit** mitgezogen (Review-Regel).
6. **Migration ohne Inhaltsverlust**: `git log --diff-filter=R` zeigt für alle 13 Operationen
   R+A-Paare; `test ! -e ARCHITECTURE.full.md && test ! -e docs/superpowers && test ! -e howto &&
   test ! -e docs/howto` → **0** (AC-28).
7. **Szenarien 50/51/52/54/55/56** bleiben nach **jeder** Welle grün; **kein** Assert-Skript und
   **keine** Fixture-Config wurde geändert (AC-38, NG-10).
8. **W7 isoliert**: Erstsicherung vorhanden, `restore_wiki_index` getestet (Backup, Dry-Run,
   fail-closed), User-Sign-off zu `knowledge/schema.md` liegt vor, `index-mode: llm` als Rollback
   dokumentiert.
9. **Alle sechs Entscheidungs-Records** (OQ1, OQ2, OQ4, OQ6, OQ8, OQ9) existieren mit Owner,
   Entscheidung und Datum. **OQ2/OQ6/OQ8** sind bereits **entschieden (2026-09-26, Nutzer)** — ihre
   Records dokumentieren die getroffene Entscheidung (Gewähltes **und** Verworfenes), nicht eine
   offene Wahl. OQ3 ist als Folge-REQ geführt.
10. **Provider-Agnostik**: `python3 -m pytest tests/test_provider_agnostic_dispatch.py -q` → **0**;
    kein `if provider == "Name"` in M1–M4; kein Config-Key mit Providernamen.
11. **NFA-07** eingehalten: M1, M2, M4 importieren nur Stdlib + `scripts/lib`.
12. **DoD-Standard**: Code komplett, Konventionen und Conventional Commits eingehalten, keine
     Regressionen; `python3 scripts/sync.py --validate` → **0** — **RVW2-2: erst nach W8-4
     erreichbar** (Regel `W-VALIDATE-ROT`; davor planmäßig rot wegen V2/V3/V6) und **bedingt**
     auf die in W3-7 gemessene Baseline (`errors: 0`; sonst Deltasperre);
     `python3 scripts/sync.py --check` → **0** (Drift-Lauf, RVW2-13).
13. **Traceability**: `validator`-Audit bestätigt AC-01…AC-41 → Task → Test; NFA-01…NFA-11 belegt.
14. **Ledger**: alle Checkboxen dieses Plans gesetzt (geschrieben durch den Ledger-Writer
     `scripts/lib/plan_ledger.py`); Merge des Wellen-Branches
     `feat/repository-documentation-consolidation-main` manuell bestätigt (Ausführungskorrektur
     2026-09-26: **ein** Wellen-Branch statt acht, s. W0-2-Akzeptanz); danach
     Verschiebung nach `docs/plans/archive/` gemäß `docs/plans/README.md:4-7`.

## Self-Review (kein Platzhalter, Konsistenz gegen die Spec)

- **No-Placeholder:** kein `TODO`, kein `TBD`, kein `???`, kein leeres Feld. Offene Punkte sind
  ausschließlich die Entscheidungs-Tasks W0-7/W5-1/W8-1 (OQ1/OQ9/OQ4) mit Owner, Entscheidungsweg
  und Folge sowie die Ergebnis-Records W0-1/W0-3/W0-6 (OQ6/OQ2/OQ8, entschieden 2026-09-26).
  **Dritte Korrekturrunde (RVW2):** hinzu kommen **vier Entscheidungsvorlagen E-1…E-4** (Spec
  §17.9.4) — E-1 Bestätigung der DoD-Punkt-2-Neufassung, E-2 V9-Altersschwelle als Config-Key
  oder Modulkonstante, E-3 Präzisierung des `--check`-Halbsatzes in §6(b), E-4 `TEST_COMMANDS`-
  Punkt in §10. Sie sind **keine** Platzhalter: jede trägt Optionen, Empfehlung, Owner und
  Entscheidungsweg; **keine** ist eigenmächtig entschieden, und die jeweils angewendete
  Zwischenlösung ist im Dokument benannt.
  Jede
  Interface-Signature ist vollständig, jeder Task nennt exakte Pfade, Symbole und eine
  Commit-Message. `Interfaces:` ist in **jedem** Task gefüllt (Produces **und** Consumes).
- **AC-Vollständigkeit:** AC-01…AC-41 lückenlos, jede Zahl genau einmal in der Coverage-Matrix;
  W1=10, W2=7, W3=14, W4=2, W5=2, W6=2, W7=4, W8=2 — deckungsgleich mit Spec §9.2 (NEW-5).
- **Wellen-Konsistenz:** W0–W8 vollständig, Reihenfolge aus Spec §9.2 übernommen; die beiden
  Umordnungen (W4/W5/W6 seriell, W8 nach W7) sind **begründet** und markiert.
- **V-Checks:** V1–V9 implementiert; V9 ohne AC ist als Lücke **benannt**, nicht kaschiert.
- **Entscheidungen:** OQ6 (W0-1) und OQ8 (W0-6) sowie OQ2 (W0-3) sind **entschieden**
  (Nutzer, 2026-09-26, Spec §11.2) und als benannte Tasks **vor** der abhängigen Welle
  geführt, nicht als Fußnote: W0-1/W0-3/W0-6 sind **Ergebnis-Records** (Gewähltes **und**
  Verworfenes), W0-6 nennt den Sync-/Validator-Lauf und **ausdrücklich nicht** den
  `pre-commit`-Hook. OQ1/OQ9/OQ4 bleiben offen (W0-7/W5-1/W8-1); OQ3 außerhalb,
  OQ5/OQ7 geschlossen.
- **Ownership:** Jede Datei erscheint in höchstens einer Task-`Files:`-Liste **pro Parallelgruppe**.
  `.meta-config/project.yaml` wird von fünf Tasks geschrieben — diese liegen in fünf
  **sequenziell geordneten** Wellen, also nie gleichzeitig. **Rev. 0.5 (K15):**
  `scripts/lib/consistency/report.py` erscheint jetzt in **genau einer** `Files:`-Liste
  (**W2-7**) — die Eigentümerlücke aus B-5/E-15 ist damit geschlossen; `scripts/lib/consistency/docs.py`
  wird von W2-1…W2-7 **innerhalb** von `PG-2/W2` geteilt, was durch die serielle Kette
  W2-1 → … → W2-7 der Parallelgruppe aufgelöst ist (W2-1 Schritt 4 aus K16 und W2-7 Schritt 4
  aus K15 liegen damit **nicht** gleichzeitig).
- **Parallelgruppen:** PG-1 (3 Ketten), PG-2 (2 Ketten), PG-3 (seriell), PG-4 (isoliert),
  PG-5 (1). Maximal 3 gleichzeitig laufende Agents — **unter** der Grenze 4, daher ist keine
  Barrieren-Spaltung über 4 hinaus nötig.
- **Track-A-Bedingung:** W1/W2 nicht parallel zu `scripts/lib/config.py`- und
  `scripts/lib/consistency/*`-Änderungen; als Gate-Task W0-4 verankert, plus Rebase-Pflicht.
- **Exit-Codes:** pro Welle konkret genannt, inklusive der **planmäßig nicht-null** Fälle
  (W2/W3 Zwischenzustände), damit `--validate` als
  `TEST_COMMAND` nicht fälschlich als Regression gelesen wird.
  **RVW-10 (Review der Rev. 0.5):** das hier ursprünglich als Beispiel genannte „W2 `--strict` = 1
  wegen V1-WARNING" ist **HISTORISCH (Rev. 0.4)** und **durch K13 widerlegt** — der beschriebene
  Zustand existiert nicht (V1 ist im Runner nicht registriert, und die Severity ist WARNING statt
  ERROR). Es bleibt als Beispiel dafür stehen, dass Zwischenzustände benannt werden müssen,
  **nicht** als gültige Exit-Code-Aussage. **Korrigierte Aussage:**
   **Rev. 0.5 (K13/K14/RVW-1/RVW-2/RVW-3)** — Wellen-Gates werden nicht
   mehr über den **repo-globalen** Exit-Code geführt, sondern über **zählbare** Kriterien auf der
   `--json`-Ausgabe (**W2-GATE-V1**, **W2-GATE-ERRORS**, **W-GATE + W-GATE-TABLE**). Grund: der
   repo-globale Code ist **unreachable-by-design** (Beleg: `consistency-check.py:273-274`,
   `report.py:75`; die **Pfadabdeckung** der Bestandschecks in `agents/1-generic`,
   `agents/2-platform`, `commands/*` ist belegt, die **tatsächliche Warning-Emitterung ist
   ungemessen** — Messung in W3-7 mit **Rückfallregel**, RVW2-12) **und** das Doku-Aggregat
   `docs-findings: 0` ist **dauerhaft** unerreichbar (V9 meldet den geduldeten Altbestand als
   WARNING, FI-10). Jede verbleibende `--strict`-Zeile in W4–W8
   gilt gemäß der Geltungsregel im W3-Block als **W-GATE + W-GATE-TABLE**; die **fünf
   Wellenblock**-Zeilen (W4, W5, W6, W7, W8) sind **im Rahmen von RVW-3 umgestellt** und tragen
   ihre Erwartung, ihren Termin und ihren Owner direkt an Ort und Stelle. **RVW-12:** kein
   Zähl-Kommando wertet einen Exit-Code aus — maßgeblich ist der gedruckte Zählwert.
   **Dritte Korrekturrunde (RVW2-2, RVW2-12, RVW2-13):** (a) `python3 scripts/sync.py --validate`
   wird in **allen** Wellen über die **eine** Regel **`W-VALIDATE-ROT`** geführt — planmäßig rot
   von **W2-7** bis einschließlich **W8-2** (Mechanik `cli_commands.py:975` → `:171-174` →
   `:1056`/`:1058-1059`), spätester Termin 0 **W8-4**, Owner `validator`, Grundlage **Spec §6(b) /
   §10, Aufzählungspunkt `--validate`**; die Sollwerte werden **nicht** abgesenkt, sondern **terminiert**; (b) die
   Aufhebung des `--strict` ruht auf einer **ungemessenen** Prämisse und hat eine **Rückfallregel**
   in **W3-BASELINE-STRICT** erhalten — `errors: 0` **und** `warnings: 0` ⇒ `--strict → 0` ist für
   W4…W8 **wieder** maßgeblich; (c) `--check` ist der **Drift-Lauf**, nicht der
   Consistency-Runner, und ist ausdrücklich als **kein** Doku-Gate geführt.
- **Bekannte Abweichungen von der Spec (alle begründet, keine stillschweigend):**
  1. W4/W5/W6 seriell statt parallel (geteilter Testdatei-Besitz, §9.2).
  2. W8 nach W7 (NFA-06, B6).
  3. AC-12 Implementierung in W2-6, E2E-Nachweis in W3-6 (Datei-Ownership).
  4. AC-14/15/16/27 Implementierung in W1-7, Aktivierung in W3-6 (Spec §9.1 nennt W3).
  5. W0-Tasks verweisen als **Gate-Anker** auf ACs, obwohl W0 laut Spec §9.2 kein eigenes AC trägt.
  6. **Ein** Wellen-Branch statt acht Wellen-Branches (Nutzer-Vorgabe; Ausführungskorrektur
     2026-09-26, Global Constraints, W0-2-Akzeptanz, R16).
- **Offener Punkt OP-1 — Spec-Korrektur auf Rev. 0.4 ausgeführt (Stand 2026-09-26); offen ist
  nur noch der formale Abschluss in Plan und W0-Records:** Die **Spec** verlangte im
  Rev.-0.3-Stand in **§9.2 W0** und **R16** weiterhin **verbindlich** „**ein Branch pro Welle**
  (`chore/docs-consolidation-w<N>`), gestapelte PRs", während **ein** Branch umgesetzt war
  (`feat/repository-documentation-consolidation-main`, PR #839) — der eingefrorene Spec-Stand
  verletzte damit die normative Quelle. **Die Korrektur der Spec auf Rev. 0.4 ist ausgeführt:**
  das **Concept-Review ist erfolgt** (2026-09-26, `VERDICT: BLOCKED`, Befund **F-1**) und Rev. 0.4
  ist am 2026-09-26 **durch den Nutzer bestätigt** (Spec §17.6/§17.7). Die frühere Angabe
  „Ausgeführt: nein — das Concept-Review hat nicht stattgefunden" ist damit **überholt** und
  entfernt. **Offen** bleibt ausschließlich der **formale Abschluss von OP-1** (K1-Liste im
  Änderungsblock, Global Constraints, Self-Review, W0-2-Spezifikationsabweichungs-Box sowie die
  sechs W0-Records); er ist als **Folgeschritt mit exaktem Änderungsauftrag** in Spec §17.6/§17.7
  geführt und **nicht** Teil dieser Revision. **Geltende Strategie:** die ausgeführte (ein Branch,
  ein PR); der Widerspruch ist in Global Constraints, W0-2, W0-2-Record Kapitel 7 und §10,
  Track-A-Gate-Record §10 sowie OQ6-Record sichtbar dokumentiert und **nicht verdeckt**.
  Owner des formalen Abschlusses: `orchestrator`.
- **Ehrliche Lücken:** V9 ohne AC; `docs/CODEBASE_OVERVIEW.md` ohne AC und NG-3; `llms.txt:5`
  Providernamen-Liste ist inhaltlich (AC-40), aber keine „manuell gepflegte Zahl“ (Spec Rev. 0.3,
  NF-9) und daher nicht Teil der 11.

---

## Ausführungs-Ledger — Stand 2026-09-26 (Fortschrittsabgleich W1 / W2-1)

> **Was dieser Abschnitt ist — und was nicht.** Dieser Abschnitt wurde am 2026-09-26 vom
> Dokumentations-Agenten ergänzt, weil die Checkboxen dieses Plans als **Ledger** und als
> **menschlich lesbarer Fortschrittsausweis** dienen und ein falsches Ledger ein
> Korrektheitsproblem für das gesamte Vorhaben ist. Er enthält **ausschließlich**:
> (a) den Abgleich der Checkboxen gegen die tatsächlich gelandete Arbeit,
> (b) **neu markierte** Abweichungs-/Errata-Notizen und
> (c) eine **konsolidierte** Liste der bisher über W1- und W2-1-Reviews verstreut erhobenen
> Befunde.
> **Unverändert bleiben:** `status: APPROVED` (`:5`), `revision: 0.4` (`:6` — **Rev. 0.5 (K17):
> inzwischen `revision: 0.5`; die Erwähnung `0.4` hier ist ein Zitat des Rev.-0.4-Standes, an dem
> dieser Abschnitt entstanden ist, und bleibt als solches stehen**), sämtliche Task-,
> Wellen-, AC-, IC-, NFA-, R- und OQ-IDs, alle Akzeptanzkriterien, alle Verifikations-Kommandos,
> alle Gates und der vollständige Revisions- und Änderungsnotiz-Block (Rev. 0.2–0.4, K1–K12).
> **Keine bestehende Abweichungsnotiz wurde entfernt, ersetzt oder umformuliert.** OP-1 bleibt
> unverändert offen und wird durch diesen Abschnitt **nicht** berührt. Dieser Abschnitt ist
> **additive Dokumentation**, kein Bestandteil einer Plan-Revision; eine spätere Revision muss ihn
> mitnehmen.
>
> **Zeilenanker in diesem Abschnitt:** Alle `plan:<Zeile>`-Verweise beziehen sich auf den
> **Zeilenstand Rev. 0.4, also vor diesem Abgleich** (die drei LEDGER-Notizen an W1-5, W1-10 und
> W2-1 verschieben die Zeilen danach). Das ist bewusst so markiert und folgt der Begründung von
> **K12** (eine Zeilenzahl eines Dokumentstandes ist driftanfällig): **maßgeblich sind die
> Abschnitts- und Task-Anker**, nicht die Zeilenzahl. Verweise auf **andere** Dateien
> (`scripts/…`, `config/…`, `docs/specs/…`) tragen den Zeilenstand vom 2026-09-26.
>
> **Nachtrag Rev. 0.5 (2026-09-26, K17) — Ankerstand.** Die `plan:<Zeile>`-Verweise oben sind
> **historisierend**: sie bezeichnen den **Rev.-0.4-Zeilenstand** und sind durch die Rev. 0.5
> **überholt** (Rev. 0.5 fügt Text in W2, W2-1, W2-7, W3, W3-4, W3-7, Matrix, DoD und
> Self-Review ein). Sie werden **nicht** nachgeführt — das wäre die Zeilenanker-Drift, die **K12**
> vermeiden wollte. **Maßgeblich sind ab Rev. 0.5 ausschließlich Abschnitts- und Task-Anker.**
> Die **neuen** Verweise der Rev. 0.5 verwenden daher durchgehend Abschnittsanker
> („Wellenblock W2 — Verifikation", „Task W2-1", „Task W2-7", „Wellenblock W3 — Verifikation",
> „Task W3-4", „Task W3-7", „Reihenfolge-/Abhängigkeitsmatrix", „L-1"…„L-4") und
> **Erweiterung (RVW2-11, dritte Korrekturrunde):** dieselbe Regel gilt für die
> `plan:<Zeile>`-Verweise in den **LEDGER-Stand-Notizen der Task-Bereiche** (W1-5, W1-10) und in den
> **Rev.-0.5-Text selbst** — dort sind in dieser Korrekturrunde die Anker `plan:1086-1089`
> (RVW-12-Liste), `plan:1058` / `plan:1235` / `plan:1329` (L-2/B-2-Nachtrag RVW-2) und
> `plan:924-940` (L-2/LEDGER-Notiz W2-1) **durch Abschnitts-/Task-Anker ersetzt** worden. Die
> **verbleibenden** `plan:<Zeile>`-Verweise (L-2, L-3, L-4 und die genannten Task-Notizen) sind
> **Rev.-0.4-Text** und bleiben **wortgleich** stehen — sie werden **nicht** umgeschrieben
> (Historie), gelten aber als **überholt**; maßgeblich ist der jeweilige Abschnitts-/Task-Anker.
> `Datei:Zeile` gilt weiterhin **ausschließlich** für Dateien **außerhalb** dieses Plans.

### L-1 Checkbox-Abgleich

| Task | Checkboxen | Stand 2026-09-26 |
|---|---|---|
| **W1-1** | 4/4 | vollständig abgeschlossen, reviewed, committed |
| **W1-2** | 4/4 | vollständig abgeschlossen, reviewed, committed |
| **W1-3** | 4/4 | vollständig abgeschlossen, reviewed, committed |
| **W1-4** | 4/4 | vollständig abgeschlossen, reviewed, committed |
| **W1-5** | 3/4 | **teilweise** — Test-/Loader-/Comparator-Hälfte steht; nur Step 4 (Commit) offen |
| **W1-6** | 4/4 | vollständig abgeschlossen |
| **W1-7** | 4/4 | vollständig abgeschlossen |
| **W1-8** | 4/4 | vollständig abgeschlossen |
| **W1-9** | 4/4 | vollständig abgeschlossen |
| **W1-10** | 2/4 | **teilweise** — nur `docs-consolidation.enabled: true` gelandet; 4 Properties + Commit offen |
| **W2-1** | 3/5 | **teilweise** — Implementierung steht; offen sind Schritt 4 (**K16 / B-4**, Rule-3-Eingrenzung, in Rev. 0.5 neu) und Schritt 5 (Commit) |
| W2-2 … W2-6 | 0/4 je Task | **nicht gestartet**, unverändert offen |
| **W2-7** | 0/5 | **nicht gestartet** — Schritt 4 ist in Rev. 0.5 **neu** (**K15 / B-5**, `report.py`-Ownership: `line`/`branch` als Dataclass-Felder); Schritt 1 trägt seit der dritten Korrekturrunde zusätzlich den **positiven** Registrierungs-Pin (**RVW2-5**, ersetzt `test_v1_is_not_wired_into_the_runner_yet`) |
| **W4-3** | 0/5 | **nicht gestartet** — Schritt 4 ist in der dritten Korrekturrunde **neu** (**RVW2-6**: Abschluss-Sync-Lauf der Welle, trägt die V2-Spalte W4 der W-GATE-TABLE) |
| **W5-2** | 0/5 | **nicht gestartet** — Schritt 4 ist in der dritten Korrekturrunde **neu** (**RVW2-6**: Abschluss-Sync-Lauf der Welle, trägt die V2-Spalte W5) |
| **W8-4** | 0/6 | **nicht gestartet** — von 4 auf **6** Steps erweitert: Schritt 1 trägt die **Bestandsaufnahme** für V9 (**RVW2-4**), Schritt 4 die **V9-Obergrenze**, Schritt 5 den **Abschluss-Sync-Lauf** (**RVW2-6**); der V9-Altersschwellen-Wert ist **Modulkonstante**, **kein** Config-Key (**RVW2-7**) |
| W0-1 … W0-7, W3-1 … W8-3 (ohne die vorstehend genannten) | 0/4 je Task | unverändert offen — **nicht** Gegenstand dieses Abgleichs |

- **Zählung (Stand Rev. 0.4-Abgleich):** **vor** dem Abgleich **0 von 188** Checkboxen gesetzt
  (188 offen); **nach** dem Abgleich **40 von 188** gesetzt (**148 offen**). Setzung: W1-1…W1-4 (16) +
  W1-5 (3) + W1-6…W1-9 (16) + W1-10 (2) + W2-1 (3).
- **Zählung, fortgeschrieben durch Rev. 0.5 (K17) — 2 Checkboxen hinzugekommen, keine gesetzt:**
  **190** Checkboxen gesamt, **40** gesetzt (**unverändert**), **150** offen. Herleitung:
  35 Tasks mit je **4** offenen Steps (gemessen: 36 Treffer auf `^- \[ \] 1:`, davon ist W2-7,
  das jetzt **5** offene Steps hat) = 140, + W2-7 (5) = 145, + W1-5 (1) + W1-10 (2) + W2-1 (2,
  da Schritt 4 neu) = **150**; gesetzt **40** (gemessen: 40 Treffer auf `^- \[x\]`, nach der
  Rev. 0.5 **unverändert** 40); 40 + 150 = 190 = 188 + 2. **Neu:** W2-1 Schritt 4 (K16) und
  W2-7 Schritt 4 (K15). **Task-Anzahl je Welle unverändert** — es wurde **kein** Task angelegt,
  nur **zwei** Steps in **bereits existierenden** Tasks ergänzt. **RVW-8 (Review der Rev. 0.5):**
  die Herleitung im **Rev.-0.5-Kopf** dieses Plans war abweichend und ergab **148**; Kopf und
  L-1 sind jetzt **identisch** (diese Formel). Die **Gesamtzahlen** waren und sind korrekt — nur
  die Herleitung im Kopf war falsch. Gegenprobe über alle **47** Tasks: 45 × 4 + 2 × 5 = **190**.
- **Zählung, fortgeschrieben durch die dritte Korrekturrunde (RVW2-6) — 4 Checkboxen
  hinzugekommen, keine gesetzt:** **194** Checkboxen gesamt, **40** gesetzt (**unverändert**),
  **154** offen. Herleitung: 42 Tasks mit je **4** Steps = 168, + W2-1 (5) + W2-7 (5) + W4-3 (5)
  + W5-2 (5) = 188, + W8-4 (6) = **194**; 40 + 154 = **194** = 190 + 4. **Neu:** W4-3 Schritt 4
  und W5-2 Schritt 4 (Abschluss-Sync-Läufe, Normativitätstabelle Spec §17.9.4 Punkt (viii)),
  W8-4 Schritt 4 (V9-Obergrenze, **RVW2-4**) und W8-4 Schritt 5 (Abschluss-Sync-Lauf).
  Gegenprobe über alle **47** Tasks: 42 × 4 + 4 × 5 + 1 × 6 = **194**. **Task-Anzahl je Welle
  unverändert** — **kein** neuer Task, nur **vier** Steps in **bereits existierenden** Tasks
  (W4-3, W5-2, W8-4). **Grenze der Messung:** die Zählung ist in dieser Runde **nicht gemessen**
  (kein Shell-Zugriff), sondern **hergeleitet**; Nachmessung durch `validator`, Abweichung wird
  in der Herleitung korrigiert, **nicht** in der Task-Struktur.
- **Kein** Task wurde abgehakt, obwohl ein Step offen ist. Die drei teilweise erledigten Tasks
  tragen zusätzlich eine **LEDGER-Stand**-Notiz direkt unter ihrer Step-Liste (W1-5, W1-10, W2-1).
- **Nicht Gegenstand:** Die W0-Tasks sind im Repo durch die Ergebnis-Records
  (`docs/plans/2026-09-25-docs-consolidation-oq2.md`, `-oq6.md`, `-oq8.md`, `-oq1.md`,
  `-wave0-freeze.md`, `-track-a-gate.md`) und durch den Rev.-0.2-Block dieses Plans belegt; ihre
  Checkboxen wurden in diesem Abgleich **bewusst nicht angefasst**, weil nur W1/W2-1 zur
  Abstimmung beauftragt waren.

### L-2 Blockierende Befunde (B-1 … B-5)

> **Keine Korrektur an Spec oder Plan wurde in diesem Abschnitt vorgenommen.** B-1 und B-2 sind
> **Korrekturbedarf an der normativen Quelle**, keine Ausführungsfehler; sie brauchen — wie der
> bereits dokumentierte offene Punkt **OP-1** — ein **Concept-Review** und eine anschließende
> Spec-/Plan-Revision. Sie sind hier **nicht** behoben, sondern **begrenzt und belegt** geführt.

**B-1 — Das verpflichtende Gate der Welle W3 ist im Plan falsch zugeschnitten.**
- **Sachverhalt:** Spec §10 verpflichtet `python scripts/consistency-check.py --strict` ab W3
  **für `scripts/lib/doc_*.py` und `docs/INDEX.md`**
  (`docs/specs/2026-09-25-repository-documentation-consolidation.md:1802-1803`). Der W3-Block des
  Plans hat daraus ein **repo-globales** `--strict == 0` gemacht
  (`plan:1094` — Verifikation W3: „`--strict` → **0 ab W3-7** (Pflicht ab W3, Spec §10)"), und
  das Wellen-Gate ist daran gekoppelt (`plan:1258` Akzeptanz von W3-7).
- **Mechanik:** `scripts/consistency-check.py:273-274` setzt Exit **1**, sobald **irgendein**
  Finding `Severity.WARNING` trägt; `scripts/lib/consistency/report.py:75` gibt Exit **1** bei
  Errors. Repo-globales `--strict == 0` verlangt also **null Errors und null Warnings**.
- **Konflikt:** Die rund **19** bereits vorhandenen, warnungs-emittierenden Checks decken
  `agents/1-generic`, `agents/2-platform` und `commands/*` ab — Pfade, die **keine** Welle W1–W8
  anfasst. Das Wellen-Gate ist damit **nicht erreichbar**, ohne außerhalb des Plans Änderungen an
  genau diesen Pfaden vorzunehmen.
  **RVW2-12 (Präzisierung, 2026-09-26 — die Zahl und die Prämisse sind ungemessen):** „rund
  **19**" ist eine **Schätzung** aus dem Rev.-0.4-Abgleich, **keine Messung**, und wird hier
  **nicht** als Prämisse der Aufhebung geführt. Belegt ist ausschließlich die **Pfadabdeckung**
  (`collect_agent_files`/`collect_command_files`, `scripts/consistency-check.py:108-135`), **nicht**
  die tatsächliche Warning-Emitterung. Die Messung erfolgt in **W3-7** mit exaktem Kommando
  (**W3-BASELINE-STRICT**, Owner `validator`), **erst nach** der Aufhebung; die **Rückfallregel**
  dort — `errors: 0` **und** `warnings: 0` ⇒ `--strict → 0` ist für W4…W8 **wieder** maßgeblich und
  die Aufhebung ist zu annullieren — schließt den Fall, dass die Aufhebung eine unbeabsichtigte
  Absenkung war. **Die Zeile oben bleibt als Rev.-0.4-Befundtext stehen** und wird hier nur
  qualifiziert.
- **Status:** **blockierend** · **Owner:** `orchestrator` (Spec-/Plan-Korrektur mit
  Concept-Review, Präzedenz OP-1) · **Status im Plan:** offen, dokumentiert · **Korrektur hier
  ausdrücklich nicht ausgeführt.**
- **Statuspflege Rev. 0.5 (K14, 2026-09-26) — im Plan-Teil korrigiert, Spec-Teil präzisiert.**
  Der oben beschriebene Mangel ist im **Plan** behoben: das W3-Gate wurde auf die Spec-Semantik
  zurückgeführt (datei-bezogener §10-Scope **W3-GATE-SCOPE** als Dokuzeile — RVW-14 — plus das
  **check-spezifische** Doku-Gate **W-GATE + W-GATE-TABLE**), das repo-globale `--strict == 0` ist
  **aufgehoben** und als
  **Altbestand-Baseline (W3-BASELINE-STRICT)** getrennt ausgewiesen. Die Spec wurde in **§10**
  um die Messform ergänzt (Pflichtumfang **wortgleich**); ein **neuer** §17.9 dokumentiert
  Katalog und Nachmessung.   **Reststand:** das **Concept-Review über Spec Rev. 0.5** ist
  **nicht erfolgt** (Owner `orchestrator`); es blockiert die Ausführung **nicht**, weil Rev. 0.5
  **keine Pflicht jenseits des am 2026-09-26 beauftragten Korrekturumfangs** einführt (RVW-5a/b —
  die Fassung vor dem Review behauptete pauschal „keine neue normative Pflicht"; das war
  unhaltbar, weil Rev. 0.5 sehr wohl Nachweisformen ändert; siehe Rev.-0.5-Block, Abschnitt
  „Präzisierung der Normativitätsaussage"). **B-1 ist damit im Plan geschlossen, in der Spec
  präzisiert.**
- **Nachtrag Rev. 0.5 (RVW-1, 2026-09-26) — die erste Korrektur des Gates war selbst noch
  unerreichbar und ist nachgeschärft.** Das in der Statuspflege oben genannte
  **Doku-Aggregat** `docs-findings: 0` (vormals „W3-GATE-DOCS") ist als Wellen-Gate
  **ebenfalls unerreichbar** — belegt am Working Tree: V7 rot bis **W5-3** (10 Wiki-Seiten
  `type: "Architecture"` ohne `derived-from`), V3 rot bis **W8-2** (`README.md:721-723`), V2 rot
  bis **W3-6** (`docs/INDEX.md` fehlt), und V9 **dauerhaft** (geduldete WARNINGs auf den
  unangetasteten Altbestand, FI-10; **RVW2-4:** „179" ist eine **Bestandsangabe**, im Working Tree
  **nicht messbar**, **kein** Sollwert).
  **Korrektur:** das Aggregat ist durch die **check-spezifische Kriterientabelle W-GATE-TABLE**
  (Erwartungswert, Termin, Owner je V-Check und je Welle) **ersetzt**; die **fünf Wellenblock**-
  Zeilen von W4, W5, W6, W7 und W8 sind entsprechend umgestellt (RVW-3). **B-1 bleibt damit
  geschlossen, aber auf einer belastbaren Form.**
- **Nachtrag dritte Korrekturrunde (RVW2-1, RVW2-2, RVW2-12, 2026-09-26) — B-1 ist geschlossen,
  die Messform ist nachgeschärft.** (a) **RVW2-1:** die Kopfzahl `docs-checks` der
  Kriterientabelle war **selbst** unerreichbar, weil der Counter **befundliefernde** statt
  **registrierter** Checks zählt — ersetzt durch **Präsenzregel** + Dokuzeile
  (`W2-GATE-ERRORS`, W-GATE). (b) **RVW2-2:** `python3 scripts/sync.py --validate → 0` war in
  **allen** Wellen unerreichbar — neue Regel **`W-VALIDATE-ROT`**, Termin statt Sofortwert.
  (c) **RVW2-12:** die Aufhebung des repo-globalen `--strict` ruhte auf einer **ungemessenen**
  Prämisse (die Zahl „19" ist eine Schätzung, die **Warning-Emitterung** der Bestandschecks ist
  **nicht** belegt) — **Rückfallregel** in W3-BASELINE-STRICT: `errors: 0` **und** `warnings: 0`
  ⇒ `--strict → 0` ist für W4…W8 **wieder** maßgeblich, Aufhebung annullieren, Owner `validator`,
  Entscheidungspunkt **W3-7**. **B-1 bleibt geschlossen;** alle drei Korrekturen betreffen die
  **Messform**, nicht den **Pflichtumfang** der Spec §10.

**B-2 — Die Wellen-Erwartung der Welle W2 ist so nicht erfüllbar.**
- **Sachverhalt:** Die W2-Verifikation erwartet `--strict` → **1** und verlangt, die **einzigen**
  Findings seien `docs.no_manual_counts`-V1-**WARNING**s (`plan:927-931`).
- **Mechanik:** (a) V1 wird erst in **W2-7** registriert (`plan:1081`), in W2-1 ist der Check
  implementiert, aber **nicht registriert** — die W2-Erwartung beschreibt also einen Zustand, der
  erst nach W2-7 existiert und dann von W2-1 nicht mehr verifiziert wird; (b) die drei
  bestehenden Doku-Checks (`check_sync_cli_docs` `:9`, `check_ui_help_mappings` `:47`,
  `check_readme_docs_index` `:100`) emittieren ausschließlich `Severity.ERROR` und **nie**
  `WARNING`; (c) die Bestands-Baseline ist bereits **rot** gegen `--strict`.
- **Folge:** Der beschriebene Zustand (Exit 1 **ausschließlich** wegen V1-Warnings) existiert
  nicht — weder in W2-1 noch nach W2-7. Die Erwartung ist damit als **Wellen-Abnahmekriterium
  unbrauchbar**.
- **Status:** **blockierend** · **Owner:** `orchestrator` (Plan-Korrektur der W2-Verifikation) ·
  **Korrektur hier nicht ausgeführt.**
- **Statuspflege Rev. 0.5 (K13, 2026-09-26) — geschlossen.** Die W2-Verifikation enthält jetzt
  das Abnahmekriterium **W2-GATE-V1** mit **zwei** getrennten Zuständen (nach W2-1: `v1-findings: 0`,
  weil V1 nicht registriert ist; nach W2-7: `v1-findings: ≥ 1` **und** `v1-severities: ['WARNING']`).
  Die beiden `--strict`-Zeilen des Wellenblocks sind als **aufgehoben** markiert und bleiben
  sichtbar. **Beleg für die Prämisse-Korrektur:** `docs.py:359` + `:314-326`,
  `.meta-config/project.yaml:398-399`, `scripts/consistency-check.py:52-56`,
  `tests/test_doc_facts.py:2403-2422`. **Ergänzt und in der Auftragsangabe nicht enthalten
  gewesen:** der §10-Dateiscope erfasst V1 **nicht** (V1 scannt `README.md`, `llms.txt`,
  `ARCHITECTURE.md`, `docs.py:158`) — ein Gate nur über §10 wäre **scheinbar grün**; deshalb das
  zweite Kriterium **W-GATE + W-GATE-TABLE** (check-spezifisch, RVW-1). **B-2 ist geschlossen.**
- **Nachtrag Rev. 0.5 (RVW-2, 2026-09-26) — drei weitere, unerreichbare `→ 0`-Zeilen in W2.**
  Die Korrektur K13 erfasste nur die **beiden** `--strict`-Zeilen des W2-Wellenblocks. Offen
  blieben **drei** Zeilen `python3 scripts/consistency-check.py` → **0**: Wellenblock **W2 —
  Verifikation**, Task **W2-2** und Task **W2-7** (RVW2-11: die früheren Zeilenanker
  `plan:1058`, `plan:1235`, `plan:1329` sind **entfallen** — sie zeigten auf den
  **Rev.-0.4-Zeilenstand**; maßgeblich sind die Abschnitts-/Task-Anker **W2 — Verifikation**,
  **W2-2 `Verifikation`**, **W2-7 `Verifikation`**). Sie sind nach W2-7 **planmäßig rot**: W2-7
  registriert V1–V7, V2/V3/V6 sind
  **ERROR** (IC-05), und `print_report` gibt `1 if errors else 0`
  (`scripts/lib/consistency/report.py:75`). Die Klammer von W2-2/W2-3 („nur WARNINGs") war
  **sachlich falsch**, weil W2-3 auf W2-2 folgt und V3 dort ERROR ist. **Korrektur:** alle
  drei Zeilen bleiben als Historie sichtbar und sind additiv auf **W2-GATE-ERRORS** umgestellt
  (Zähl-Kommando, Erwartungswert je V-Check, Termin, Owner). **Dokuzeile zum spätesten
  Termin, zu dem der rohe Runner `Exit 0` liefert: W8-2**, Owner `developer` — das ist **kein**
  W2-Kriterium, sondern die Terminierung des Altbestands-Zustands.

**B-3 — W1-10 ist nur zur Hälfte gelandet.** Siehe die LEDGER-Stand-Notiz an W1-10 und **E-13**.
Von den fünf additiven `docs-consolidation.*`-Properties ist **eine** gesetzt
(`.meta-config/project.yaml`, `docs-consolidation.enabled: true`, als **separat autorisierte,
eng zugeschnittene Gate-Änderung** geliefert). **Offen:** `index-mode`, `checks.strict`,
`sources`, `volatile-facts` — deklariert im Schema (W1-9), aber **ohne Wert** in der
Projekt-Config. **Status:** **als offener Follow-up geführt, blockiert den Abschluss von W1** ·
**Owner:** `developer` (Restlieferung W1-10), Entscheidung über den Umgang mit dem erweiterten
Gate `orchestrator`.

**B-4 — V1 hat eine Abdeckungslücke (Befund F2 aus dem W2-1-Review).**
- **Sachverhalt:** Suppressionsregel 3 der Spec §5.1.1 („fenced code") unterdrückt
  `README.md:688/690/696/734`. Die IC-05-Befunde **F2**, **F3-Site-2** und **F4** sind für V1
  damit **unsichtbar** — V1 kann sie weder finden noch als grün melden.
- **Konsequenz:** Der DoD-Punkt „11 Handzahlen = 0" (`plan:1868-1869`) und die W3-7-Akzeptanz
  „`--strict` → 0, kein `docs.*`-Finding" (`plan:1258`) sind mit dieser Lücke **nicht** belastbar
  beweiskräftig.
- **Status:** **blockierend für die Hochstufung von V1 auf `ERROR`** · **Remediation-Owner:
  W3-7**, **vor** der Umstellung von `checks.strict` in W3-4 · **Status im Plan:** offen,
  dokumentiert · **Korrektur hier nicht ausgeführt.**
- **Statuspflege Rev. 0.5 (K16, 2026-09-26) — Owner korrigiert, Aufgabe terminiert.** Der
  Remediation-Owner ist **von W3-7 auf W2-1, Schritt 4** gewechselt: W3-7 ersetzt die **Zahlen**,
  nicht die **Sichtbarkeit**; eine Erkennung, die `README.md:688/690/696/734` nicht sieht, kann
  W3-7 weder belegen noch verhindern — die Zuweisung an W3-7 hätte die Lücke erst **nach** W3-4
  geschlossen. **Neu:** Abnahmekriterium (AC-07 **und** AC-08 bleiben grün; je Fundstelle
  mindestens **ein** Befund gegen die unmarkierte Ist-Fassung), Owner `developer`, Termin
  **vor** W3-4 (Vorbedingung in Task **W3-4**). **Beleg:** `README.md:680` (Fence öffnet),
  `README.md:737` (schließt), Fundstellen `:688`, `:690`, `:696`, `:734`;
  `docs.py:281-311`, `_V1_FENCE_OPEN_RE` `docs.py:203`; Spec §5.1.1 (Präzisierung Rev. 0.5).
  **B-4 ist damit zugeordnet, aber noch nicht behoben** — behoben ist er erst mit dem grünen
  Schritt 4 der Task W2-1.
- **Nachtrag Rev. 0.5 (RVW-4, 2026-09-26) — die Reihenfolgebindung ist jetzt eine echte
  DAG-Kante.** Die Fassung vor diesem Review führte sie als „Ausführungsreihenfolge-Vorbedingung
  **ohne** Kante" und begründte das mit „eine Kante W3-4 → W2-1 wäre eine Rückwärtskante". Das war
  in der **Kantenrichtung falsch**. Die Bindung ist **`W2-1 → W3-4`**, eine **Vorwärts**kante über
  die Wellengrenze (W2 vor W3), sie ist jetzt in der **Reihenfolge-/Abhängigkeitsmatrix**
  (Zeile W3-4: `Depends on: W3-3, W2-1`), in der **Wellen-Tabelle** (W3, Spalte „Abhängig von")
  und im **PG-2-Diagramm** abgebildet und im Absatz **Zyklenprüfung** mit Nachweis belegt. **Keine
  neue Task-ID**, keine Rückwärtskante, keine Zyklen.

**B-5 — `scripts/lib/consistency/report.py` hat keinen Task-Owner (Befund F1 aus dem W2-1-Review).**
- **Sachverhalt:** `line` und `branch` sind **Instanzattribute** auf `Finding`, **keine**
  Dataclass-Felder (`scripts/lib/consistency/report.py:28-41`). `print_json_report`
  (`:78-97`) serialisiert nur `severity`, `check`, `file`, `message`, `suggestion` — der
  `--json`-Output **verwirft** `line` und `branch`.
- **Eigentümerlücke:** Die Deferral zeigt auf **W2-7**, aber `scripts/lib/consistency/report.py`
  erscheint in **keiner** `Files:`-Liste **irgendeiner** Task dieses Plans (W2-7 besitzt
  `scripts/lib/consistency/docs.py`, `scripts/consistency-check.py`,
  `tests/test_doc_facts.py` — `plan:1064-1065`). Damit besitzt **keine** Task die Promotion, und
  der Verlust wird **per Default dauerhaft**.
- **Status:** **blockierend** (stillschweigender Datenverlust in einem Gate-Werkzeug) · **Owner
  bislang: keiner** — die `Files:`-Liste einer Task (nächstliegend **W2-7**, sonst eine
  Wellen-Gate-Korrektur) muss `report.py` ausdrücklich aufnehmen · **Korrektur hier nicht
  ausgeführt.**
- **Statuspflege Rev. 0.5 (K15, 2026-09-26) — geschlossen, Owner = W2-7.** `report.py` ist jetzt
  ausdrücklich in der `Files:`-Liste der Task **W2-7** (Besitz **Registrierung + Common-Gate +
  Finding-Kontrakt**), in der **Reihenfolge-/Abhängigkeitsmatrix** (Zeile W2-7) und in einem
  **neuen Step 4** mit Abnahmekriterium **F1-PROMOTION** (`line`/`branch` als **Dataclass-Felder**,
  Serialisierung in `print_json_report`, `--json`-Output vollständig). **Beleg:**
  `report.py:28-41`, `:78-97`, `docs.py:329-347` (dessen Docstring verweist bereits auf W2-7).
  **B-5 ist geschlossen** (Plan-Ownership); die Code-Änderung selbst ist mit W2-7 zu liefern.

### L-3 Konsolidierte Errata- und Befundliste W1 / W2-1 (E-01 … E-15)

> **Zweck:** Die in den W1- und W2-1-Reviews erhobenen Befunde standen bisher über mehrere
> Berichte verstreut. Diese Liste ist der **einzige** Sammel-Ort; die ursprünglichen
> Berichte bleiben unverändert bestehen und werden nicht zurückgezogen. **Statusspalte:**
> *behoben* = am Code belegt erledigt · *offener Follow-up* = aufgenommen, mit Owner, ohne
> Gate-Wirkung · *blockierend* = verhindert ein Gate oder einen Wellen-Abschluss (siehe L-2).

| ID | Befund | Evidenz | Status | Owner |
|---|---|---|---|---|
| **E-01** | **Fakten-Key-Erratum 23 vs. 22.** Die Task W1-1 nennt „**exakt 23 Schlüssel**" (IC-02) und „die 23 IC-02-Schlüssel"; die Implementierung führt **22** Einträge. | `plan:721`, `plan:732` vs. `scripts/lib/doc_facts.py:224-246` (`FACT_KEYS`, 22 Einträge) | *offener Follow-up* — Plan-/Spec-Korrektur beauftragt, **nicht** ausgeführt; keine Gate-Wirkung, da die Key-Set-Invariante relativ zu `FACT_KEYS` getestet wird | `orchestrator` (Plan-Korrektur) |
| **E-02** | **R1 — doppelte Versionsdarstellung / nicht auflösbarer verschachtelter Platzhalter.** | W1-7-Review; Kreuz-Rendering-Ort `README.md:734` (`DOCS_VERSION`) und `DOCS_REPO_FACTS_BLOCK` | *offener Follow-up* — vor W3-7 zu belegen, da W3-7 die Version **einmal** rendern soll | `developer` (W3-7) |
| **E-03** | **R2 — verwaiste `docs-end`-Markierung wird stillschweigend ignoriert.** Nur ein unbalanciertes *Start*-Marker erzeugt eine Warnung (`plan:849-852`); ein **End**-Marker ohne Start bleibt ohne Befund. | W1-7-Review; `DOCS_BLOCK_RE` / `apply_fact_blocks` in `scripts/lib/doc_renderer.py` | *offener Follow-up* — echter Fehlalarm-Freiheit vs. unbemerkter Marker-Verlust abzuwägen | `developer` (W1-7-Nachzug, sonst W3-7) |
| **E-04** | **R3 — das Verifikations-Kommando der Task W1-5 kann `DOCS_HOOKS_1GENERIC_COUNT` nicht matchen.** `grep -c '^[A-Z_]*:'` erlaubt keine Ziffern im Schlüsselnamen; der erwartete Wert **11** ist mit diesem Kommando **nicht erreichbar** (der Dateiinhalt selbst hat 11 `DOCS_`-Einträge). | `plan:810` vs. `config/doc-facts-expected.yaml:46-56` (Schlüssel mit Ziffer) | *offener Follow-up* — Kommando oder Erwartungswert im Plan ist zu korrigieren | `orchestrator` (Plan-Korrektur) |
| **E-05** | **R4 — `^DOCS_` schluckt Namespace-Tippfehler.** Die Registrierung ist `^DOCS_[A-Z0-9_]+$`; jeder unbekannte `DOCS_*`-Name ist damit ein gültiger dynamischer Platzhalter. Teilabdeckung: zwei bekannte Tippfehler sind in `_KNOWN_TYPOS` gelistet. | `scripts/lib/consistency/placeholders.py:136` (Registrierung), `:140-144` (`_KNOWN_TYPOS`) vs. `plan:823` | *offener Follow-up* — Restabdeckung (Whitelist statt Präfix) zu entscheiden | `developer` (W3-6/W3-7) |
| **E-06** | **Lücke 7 vs. 6 bei den Block-Fakten.** Es gibt **sieben** `*_BLOCK`-Fakten, aber nur **sechs** Snippets: `DOCS_DOD_PRESET_BLOCK` hat **weder** Snippet **noch** Region, während `DOCS_TIER_PRESET_BLOCK` ein Snippet, aber **keine** Region hat. | `scripts/lib/doc_facts.py:240-246` (7 `*_BLOCK`) und `:1407-1408` (`BLOCK_FACT_KEYS`) vs. `snippets/docs/` (6 Dateien: `repo-facts`, `agent-roster`, `pipelines`, `hooks`, `providers`, `tier-presets`) vs. W3-7-Regionenliste `roster|pipelines|hooks|providers|version|facts` (`plan:1266`) | *offener Follow-up mit Gate-Wirkung* — vor W3-7 zu klären, sonst bleibt eine der 11 Handzahlen unersetzt | `developer` (W3-7) + `concept-architect` (Scope-Entscheid) |
| **E-07** | **IC-04 — Wortlaut 53 vs. 58.** | W1-3/W2-4-Review; `DOCS_AGENTS_ACTIVE_COUNT`-Formel in `scripts/lib/doc_facts.py` | *offener Follow-up* — Zahlen-Aussage des Vertrags, kein Laufzeitfehler | `orchestrator` (Spec-Klarstellung) |
| **E-08** | **AC-39 nennt „sechs Properties", die W1-10 nicht liefert.** AC-39 ist mit der W1-9-Akzeptanz (`plan:889-892`) und der W1-10-Wirkung verknüpft; tatsächlich gesetzt ist **eine** von fünf. | `plan:889`, `plan:897` vs. `.meta-config/project.yaml` (nur `docs-consolidation.enabled: true`) | *blockierend für AC-39* — identisch mit **B-3** / **E-13** | `developer` (W1-10-Restlieferung) |
| **E-09** | **Ausschluss-Lücke 13 vs. 11.** W1-2 verlangt **13** Formel-Assertions, die unabhängige Sollwert-Quelle pinnt **11** Werte. Die Differenz ist nur teilweise ausgewiesen (volatile Fakten, Differenz-Fakten, zwei als `missing-in-expected` gemeldete Lücken) — die Zuordnung „welche der 13 Formeln sind ungepinnt" ist nicht abschließend dokumentiert. | `plan:741-748` vs. `config/doc-facts-expected.yaml:22-31` (Regel 2) und `scripts/lib/doc_facts.py:1509` (`EXPECTED_COMPARABLE_FACT_KEYS`) | *offener Follow-up* — R14-Gegenmaßnahme darf nicht stillschweigend verkürzt werden | `developer` (W2-5 / V6) + `validator` |
| **E-10** | **IC-03 — F4/F5 sind nicht deterministisch.** Die Staleness-Auswertung über `mtime(derived-from) > derived-at` ist zeitabhängig; zwei Renderings können sich unterscheiden, ohne dass sich ein Input geändert hat. | `plan:788-792` (W1-4 Resolver) | *offener Follow-up mit NFA-Wirkung* (NFA-01 verlangt byte-Identität bei gleichem Baum) | `developer` (W1-4-Nachzug, Test in W2-3) |
| **E-11** | **W2-`--strict`-Erwartung unerfüllbar** (identisch mit **B-2**). | `plan:927-931` vs. `plan:1081`, `scripts/lib/consistency/docs.py:9/47/100` | *blockierend* | `orchestrator` |
| **E-11 (Rev. 0.5)** | **Statuspflege zu E-11 (K13):** im Plan **geschlossen** durch **W2-GATE-V1** (zwei Zustände, Zähl-Kommando). **Zusätzlich belegte Ursachenkorrektur:** die Unerreichbarkeit hat **zwei** Ursachen — Severity **WARNING** statt ERROR (`docs.py:359`, `.meta-config/project.yaml:398-399`) **und** fehlende Registrierung (`scripts/consistency-check.py:52-56`). | Wellenblock **W2 — Verifikation**; `docs.py:359`; `consistency-check.py:52-56` | *behoben (Plan-Gate)* — Code folgt mit W2-7 | `orchestrator` (ausgeführt) |
| **E-12** | **Gespaltenes `kind`-Vokabular des Komparators.** `Interfaces:` nennt `kind ∈ {mismatch, missing-in-expected}`, die Akzeptanz fordert `kind == "expected-mismatch"`. | `plan:799-800` vs. `plan:806-808` | *offener Follow-up* — Vertragsbegriff muss eindeutig sein, bevor V6 darauf prüft | `developer` (W2-5) + `validator` |
| **E-13** | **W1-10 teilweise geliefert** (identisch mit **B-3** / **E-08**). | `.meta-config/project.yaml` (nur `docs-consolidation.enabled: true`); Schema-Block vollständig seit W1-9 | *blockierend für den Abschluss von W1* | `developer` (W1-10) |
| **E-14** | **V1-Abdeckungslücke** (identisch mit **B-4**). | Suppressionsregel 3 (§5.1.1) gegen `README.md:688/690/696/734` | *blockierend für die V1-Hochstufung auf `ERROR`* | `developer` (W3-7), vor W3-4 |
| **E-14 (Rev. 0.5)** | **Statuspflege zu E-14 (K16):** zugeordnet an **W2-1, Schritt 4** (nicht W3-7), Owner `developer`, Termin **vor** W3-4; Abnahme: AC-07 **und** AC-08 grün **und** je Fundstelle `README.md:688/:690/:696/:734` mindestens **ein** Befund gegen die unmarkierte Ist-Fassung. | `README.md:680-737` (Fence), `docs.py:281-311`, `docs.py:203`; Task **W2-1** `Akzeptanz`/`Steps`, Task **W3-4** `Vorbedingung` | *offener Follow-up mit harter Terminierung* — **zugeordnet, noch nicht behoben** | `developer` (W2-1 Schritt 4) |
| **E-15** | **`report.py`-Eigentümerlücke** (identisch mit **B-5**). | `scripts/lib/consistency/report.py:28-41`, `:78-97` vs. `plan:1064-1065` (W2-7 `Files:`) | *blockierend* | **derzeit keiner** — `Files:`-Liste ist zu erweitern |
| **E-15 (Rev. 0.5)** | **Statuspflege zu E-15 (K15):** Ownership an **W2-7** vergeben — `Files:`-Liste, Reihenfolge-/Abhängigkeitsmatrix, `Interfaces:` (Dataclass-Felder mit Default), Abnahmekriterium **F1-PROMOTION**, neuer Step 4. | Task **W2-7** `Files:`/`Interfaces:`/`Akzeptanz`/`Steps`; Matrixzeile **W2-7** | *behoben (Ownership)* — Code folgt mit W2-7 | `developer` (W2-7 Schritt 4) |

**Zählung L-3 (Stand Rev. 0.4-Abgleich):** **15** Einträge — **0 × behoben**, **10 × offener
Follow-up** (E-01, E-02, E-03, E-04, E-05, E-06, E-07, E-09, E-10, E-12), **5 × blockierend**
(E-08, E-11, E-13, E-14, E-15 — jeweils identisch mit bzw. Verweis auf **B-2 … B-5**). Für
**keinen** der genannten Befunde liegt am 2026-09-26 ein belegter Fix vor; „behoben" ist deshalb
bewusst **nirgends** eingetragen. **B-1** (W3-`--strict`-Gate) ist nicht doppelt in dieser Liste
geführt, sondern ausschließlich in L-2 — es ist ein **Gate-** und kein Codebefund.

**Zählung L-3, fortgeschrieben durch Rev. 0.5 (K17):** Die 15 Zeilen bleiben **unverändert
erhalten** (Historie); Rev. 0.5 fügt **drei** Statuspflege-Zeilen hinzu
(**E-11 (Rev. 0.5)**, **E-14 (Rev. 0.5)**, **E-15 (Rev. 0.5)**) ⇒ **18** Zeilen in der Liste.
**Bilanz der drei Statuspflegen:** **2 × behoben im Plan** (E-11 Gate-Form, E-15 Ownership),
**1 × zugeordnet, noch offen** (E-14, Termin W2-1 Schritt 4 vor W3-4). **Die vier
Code-Änderungen selbst sind damit NICHT geliefert** — E-11 ist ein Plan-Gate (Text), E-15 ist
Ownership (Text), E-14 ist Code. Der ursprüngliche Satz „für keinen der genannten Befunde liegt
ein belegter Fix vor" gilt **unverändert für den Rev.-0.4-Stand** und ist durch diese
Fortschreibung **nicht** zurückgenommen: Rev. 0.5 liefert **Dokumentations- und
Ownership-Korrekturen, keine Produktionsänderung**.

### L-4 OQ1 bleibt offen — und blockiert W5, nicht W1–W4

- **OQ1** („Wiki-Topics vs. `docs/guides/`") ist **weiterhin offen**. Der Abgleich dieser
  Ledger-Korrektur **löst OQ1 nicht auf** und darf **nicht** als Auflösung gelesen werden: W1 und
  W2-1 sind **ohne** OQ1 gelandet, und **kein** dortiger Schritt berührt die OQ1-Scope-Grenze.
- **Entscheidungsweg:** OQ1 wird von seinem Owner entschieden — Task **W0-7** (Produktentscheidung
  an `main_chat` eskaliert, Record `docs/plans/2026-09-25-docs-consolidation-oq1.md`,
  `plan:680-694`). Die Entscheidung liegt **beim Spec-Owner**, nicht bei der Ausführung und nicht
  bei diesem Ledger-Abgleich.
- **Abhängigkeit:** OQ1 blockiert **W5** (W5-1 … W5-3, insbesondere die Scope-Grenze von W5-3:
  „annotiert **additiv**, migriert **nichts**", `plan:692`, `plan:1403-1423`). OQ1 blockiert
  **nicht** W1, W2, W3 und W4.
- **Konsequenz für die Reihenfolge:** W3 und W4 sind von OQ1 unabhängig und können weiterlaufen.
  **Rev. 0.5 (K17, Präzisierung):** der alte Zusatz „— abhängig von **B-1**" ist **überholt**:
  B-1 ist im Plan geschlossen (K14, **W3-GATE-SCOPE** als Dokuzeile plus **W-GATE +
  W-GATE-TABLE** als verbindliches check-spezifisches Gate), die
  Spec-Seite ist in §10 präzisiert. **Was W3 weiterhin blockiert, ist nicht B-1**, sondern
  **B-4/K16** (Sichtbarkeit der README-Fundstellen) **vor** W3-4 — W3 selbst bleibt lauffähig.
  **Vor** W5 ist die OQ1-Entscheidung abzuwarten.
- **Verhältnis zu OP-1:** **getrennt**. OP-1 ist der formale Abschluss der Branch-Spec-Korrektur
  und bleibt unverändert offen; OQ1 ist eine **offene Produktentscheidung**. Beide sind offen und
  werden hier nur nebeneinander benannt, nicht verknüpft.
- **Rev. 0.5 (K17):** an L-4 wurde **inhaltlich nichts** geändert. OQ1 ist **offen**, der
  Entscheidungsweg **W0-7** und der Owner `orchestrator` → `main_chat` bleiben unverändert; die
  `plan:680-694`-Verweise sind **historisch** (Rev.-0.4-Zeilenstand) und werden nicht
  nachgeführt (K12-Logik, siehe Kopfnotiz dieses Abschnitts).

