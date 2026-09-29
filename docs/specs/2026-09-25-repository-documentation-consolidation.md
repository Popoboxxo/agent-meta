---
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
title: Repository-weite Doku-Konsolidierung agent-meta — Technical Specification
status: APPROVED
approved: 2026-09-26
approved-scope: **Rev. 0.8 (2026-09-29) — ZUR USER-FREIGABE AUSSTEHEND; der Approval-Marker `APPROVED` DECKT DIESEN UMFANG NICHT.** Die **fünf inhaltlichen Pflichtänderungen P-1…P-5** (IC-13, IC-15, IC-22-Config-Tabelle, AC-21 + AC-39, R7 — Volltext **§17.12.1**), darunter **P-3 (e)** („P-3-E"), die **fünfte Tabellenzeile** von §17.12.1 und **kein sechstes** P-Element — sie präzisiert **ausschließlich den Sollwert-Zähler in AC-39** und ändert **sonst nichts** an P-3, begründen den **neuen, noch nicht freigegebenen** Umfang `docs-consolidation.index-owner` (IC-25, IC-26, AC-42…AC-46; §17.12.3). Sie sind **vor** der Umsetzung von W3-6 mit dem Nutzer zu entscheiden. Der **bereits freigegebene** Umfang **W0–W8** und das Datum 2026-09-26 bleiben davon **unberührt**; Rev. 0.8 ist ein **echter Revisions-Bump**, **kein** Korrekturrunden-Sammelblock. **Fünf Entscheidungsvorlagen E-9…E-13** sind **offen** und liegen beim Auftraggeber (§17.12.2) — **keine** ist entschieden, **keine** wird unterstellt; **E-5…E-8** bleiben entschieden und werden **nicht** neu aufgerollt. **Keine** bestehende IC-, AC-, Task-, Wellen-, V-Check-, R-, OQ- oder F-ID wurde umnummeriert oder gestrichen; neu sind ausschließlich **IC-25, IC-26, AC-42…AC-46**; die inhaltlichen Pflichtänderungen bleiben **P-1…P-5 (inkl. P-3 (e) / „P-3-E")** — **keine** sechste P-Zeile. Ausführung W0–W8; Rev. 0.4 (Commit-/Branch-Normativität) am 2026-09-26 durch den Nutzer bestätigt; A13 und A14 als offene, dokumentierte Abweichungen registriert; Rev. 0.5 (Gate-Präzisierung W2/W3, Finding-Ownership, V1-Sichtbarkeit vor Hochstufung) am 2026-09-26 durch den Nutzer **beauftragt** (A2A-Envelope vom 2026-09-26, Korrekturen 1–5) — **keine** Pflicht **jenseits** dieses beauftragten Umfangs; innerhalb des Umfangs werden Nachweisformen geändert (Präzisierung §17.9.4). Dritte Korrekturrunde (Concept-Review 2026-09-26, RVW2-1…RVW2-14) innerhalb **derselben** Revision, ebenfalls ohne Revisions-Bump: Nachweisformen geändert (§10, Aufzählungspunkt `--validate`; §10, `--strict`-Punkt, Unterpunkt 5; §17.9.4 (vii)–(x)); **vier Entscheidungsvorlagen E-1…E-4 sind offen und liegen beim Auftraggeber** — es wird keine Entscheidung unterstellt. Vierte Korrekturrunde (Concept-Review 2026-09-26, RVW3-1…RVW3-10) innerhalb **derselben** Revision, ebenfalls ohne Revisions-Bump: ausschließlich **Korrekturen** bestehender Sollwert-Formulierungen, Verweise und Anker — **keine** neue Pflicht, **keine** neue Task-ID, **kein** neuer Sollwert. **Rev. 0.6 (2026-09-27): zwei vom Nutzer getroffene Entscheidungen sind umgesetzt — U-1 (Modul-Split der Consistency-Checks, §4.1, Katalog K18…K21) und U-2 (AC-30 auf `README.md` + `llms.txt` verengt, die 25 toten `docs/**`-Links werden Follow-up **F-DOCS-LINKS-2026-09-27** mit Owner und Termin, Katalog K22…K24).** Rev. 0.6 ist ein **echter Revisions-Bump** (inhaltliche Pflichtänderung: AC-30-Wortlaut, Modulgrenzen), **kein** Korrekturrunden-Sammelblock. `status: APPROVED` und `approved: 2026-09-26` bleiben unverändert; die **beiden** Entscheidungen sind **bereits getroffene Nutzerentscheidungen** und werden hier **nicht** neu bewertet. Volltext **§17.10**. **Rev. 0.7 (2026-09-27): vier vom Nutzer getroffene Entscheidungen sind umgesetzt — E-5 (V4 auf den README-Index-Scope begrenzt, die 191 `docs/`-Links werden Follow-up **F-DOCS-README-INDEX-2026-09-27**; E-6 (dedizierter Task **W2-8** für die zwei roten Volltests, Position vor W2-7); E-7 (V5 wandert in das neue Modul `docs_freshness_v5.py`, §4.1); E-8 (`TASK_HEADER_RE` wird um die Wellen-/Task-Header erweitert, neuer Task **W2-9**, Ledger-Writer einsetzbar ab W2-9). Katalog **K54…K58** in **§17.11**.** Rev. 0.7 ist ein **echter Revisions-Bump** (inhaltliche Pflichtänderung: V4-Scope, Modulgrenzen, Taskmenge 48 → **50**), **kein** Korrekturrunden-Sammelblock. `status: APPROVED` und `approved: 2026-09-26` bleiben unverändert; die **vier** Entscheidungen sind **bereits getroffene, verbindliche Nutzerentscheidungen** und werden hier **nicht** neu bewertet. **Keine** AC-/IC-/R-/OQ-/V-Check-ID wurde umnummeriert oder gestrichen; **zwei** neue Task-IDs: **W2-8**, **W2-9**. **Abweichung vom Auftrag, ausdrücklich notiert:** der Auftrag nannte als Zielrevision der Spec **0.5**; die Datei trug jedoch `revision: 0.6` mit vollständigem **§17.10** (U-1/U-2). Ein Sprung auf **0.5** wäre eine **Regression** und würde den dokumentierten Rev.-0.6-Stand überschreiben — deshalb ist die Zielrevision der Spec **0.7**; der begleitende Plan steht ebenfalls auf **0.7**.
revision: 0.8
pending-approval: Rev. 0.8 (2026-09-29) — P-1…P-5 (einschliesslich **P-3 (e)**, im Folgenden „P-3-E") offen beim Auftraggeber; E-9…E-13 offen. Der Umfang W0–W8 bleibt freigegeben (Freigabedatum 2026-09-26, unveraendert). Volltext §17.12. Korrekturrunde zu Rev. 0.8 (Concept-Review Runde 8, 2026-09-29, CHANGES_REQUESTED) behob K77…K86 (§17.12.6) ohne neue Pflicht; P-1…P-5 und E-9…E-13 bleiben unveraendert ausstehend, pending-approval: besteht fort. ZWEITE Korrekturrunde zu Rev. 0.8 (Concept-Review Runde 9, 2026-09-29, CHANGES_REQUESTED — 2 major / 7 minor / 1 info) behob RVW9-1…RVW9-9 im selben Revisionsstand, **ohne** neue Pflicht, **ohne** neue IC-/AC-/Task-/Wellen-/V-Check-ID und **ohne** Umnummerierung bestehender IDs: (a) Katalog-IDs K61…K70 ⇒ **K77…K86** (RVW9-1, dann RVW10-1; die belegte Obergrenze ist **K76** — Plan-Legende, gemessen); (b) **V-D8** als Plan-Befund registriert mit **forderlichem** Plan-Delta (**V-D8-Uebergabe**, §17.12.5) — der **Plan Rev. 0.7 selbst wird erst nach** User-Freigabe von P-1…P-5 revidiert; (c) T-4-Ordinal, E-13-Optionstabelle (Kopier-Pfad), P-3-E-Zählung, Testname, K78-Verortung, V-D1-Selbstverweis und W1-10-Reihenfolge berichtigt. P-1…P-5 (inkl. P-3-E) inhaltlich **unveraendert**, E-9…E-13 und OQ1 **offen**.
paused: 2026-09-26 — **PAUSE. Rev. 0.8 ist ein Entwurf und KEINE Implementierungsfreigabe.** Der Grund ist, dass die Ausführung vor dem Index-Exception-Punkt angehalten wurde, weil die fünf inhaltlichen Pflichtänderungen **P-1…P-5** (§17.12.1) und die fünf Entscheidungsvorlagen **E-9…E-13 einschließlich E-13c „Kopier-Pfad"** (§17.12.2) beim Auftraggeber offen sind. Beide sind **vor** der Umsetzung von **W3-6** zu entscheiden, und der Plan Rev. 0.7 trägt den Rev.-0.8-Umfang nicht (V-D8, §17.12.5). **Vollständiger Record** in `docs/plans/2026-09-25-repository-documentation-consolidation-pause.md` (PAUSE-Record, Feld `status` = PAUSED, Feld `revision` = 0.1). **Was die Pause ausdrücklich NICHT tut** — sie zieht das Feld `approved` mit dem Datum 2026-09-26, den freigegebenen Umfang **W0–W8** oder den Hinweis, dass Rev. 0.8 selbst nicht freigegeben ist, **nicht** zurück. Sie löscht **keine** Revisions-, Korrekturrunden- oder Review-Historie, sie bumppt **keine** Revision (Rev. bleibt **0.8**), und sie vergibt, umnummeriert oder streicht **keine** ID. **Redaktions- und Commit-Datum des Pause-Records ist der 2026-09-29**; das Pause-Datum 2026-09-26 ist davon zu unterscheiden.
related:
  - docs/specs/2026-09-25-repository-documentation-consolidation-design.md
  - docs/specs/2026-09-25-repository-documentation-consolidation-design-agent-meta-exception.md
  - docs/plans/2026-09-25-repository-documentation-consolidation.md
  - docs/REQUIREMENTS.md
  - docs/plans/README.md
  - scripts/lib/spec_plan_scaffold.py
---

# Repository-weite Doku-Konsolidierung agent-meta — Technical Specification

> Status: **`APPROVED` (2026-09-26)** — **User-Freigabe liegt vor** (Nutzer, über `main_chat`
> an den `orchestrator`). Dieses Dokument ist eine **Spezifikation**: es definiert Interface
> Contracts, Datenfluss und Acceptance Criteria und enthält **keine Implementierung und
> keinen Plan**. Der Approval-Marker wurde nach dem Review durch `concept-reviewer`
> gesetzt (Approval-Gate, Master-Rule `spec-plan-workflow`).
>
> > ⏸ **PAUSE — Rev. 0.8 ist ein ENTWURF, keine Implementierungsfreigabe (Pause-Datum
> > 2026-09-26; Redaktions-/Commit-Datum des Pause-Records 2026-09-29).** Die Ausführung ist vor
> > dem Index-Exception-Punkt angehalten: **W3-6** (`docs/INDEX.md` tracked, Erstgenerierung)
> > ist **nicht** startbar. **Grund:** die fünf inhaltlichen Pflichtänderungen **P-1…P-5**
> > (inkl. **P-3 (e)** / „P-3-E", §17.12.1) und die fünf Entscheidungsvorlagen
> > **E-9…E-13 einschließlich E-13c „Kopier-Pfad"** (§17.12.2) sind **beim Auftraggeber offen**
> > und **vor** W3-6 zu entscheiden; der **Plan Rev. 0.7** trägt den Rev.-0.8-Umfang nicht
> > (**V-D8**, §17.12.5, `V-D8-Uebergabe` mit **PD-1…PD-10**). **Reihenfolge-Zwang**
> > (§17.12.5): „P-1…P-5 ⇒ Plan-Revision ⇒ **dann** W3-6. Vor der Freigabe darf
> > **kein** Plan-Task angefasst werden." **Vollständiger Record:**
> > `docs/plans/2026-09-25-repository-documentation-consolidation-pause.md`.
> >
> > **Was die Pause ausdrücklich NICHT tut** — die folgenden historischen Fakten bleiben
> > **unverändert** stehen und werden **nicht** zurückgezogen: `approved: 2026-09-26` (Nutzer,
> > über `main_chat` an den `orchestrator`), der **freigegebene Umfang W0–W8** sowie der
> > Umstand, dass **Rev. 0.8 selbst nicht freigegeben** ist (`approved-scope`,
> > `pending-approval:`). **Kein** Revisions-Bump (Rev. bleibt **0.8**), **keine** Löschung der
> > Rev.-0.4…0.8- oder Korrekturrunden-Historie (Rev. 0.5 / RVW2, Rev. 0.6 / K18…K24,
> > Rev. 0.7 / K54…K58, Rev. 0.8 / K77…K86, Runde 10), **keine** umnummerierte oder gestrichene
> > ID, **kein** Produktionscode.
>
> **Rev. 0.4 ist am 2026-09-26 durch den Nutzer bestätigt** — über den Entscheidungsweg laut
> Plan Rev. 0.4, K1 (`main_chat`). Das Concept-Review von Rev. 0.4 endete zuvor mit
> `VERDICT: BLOCKED` (F-1: neue normative Pflichten ohne erneute User-Freigabe); die
> Bestätigung liegt nun **extern** vor, die Auflösung ist in **§17.7** protokolliert.
> **Offen und bewusst nicht aufgelöst:** die W4/W5/W6-Serialität (**A14**, **§17.8**).
>
> **Rev. 0.6 (2026-09-27) — Umsetzung zweier bereits getroffener Nutzerentscheidungen:
> Modul-Split der Consistency-Checks (U-1) und Verengung von AC-30 (U-2).** Der Volltext steht
> in **§17.10**, der Katalog der Korrekturen **K18…K24** ebendort, die Modulgrenzen in **§4.1**.
> **Dies ist ein echter Revisions-Bump** (über Rev. 0.5 hinweg) und **kein**
> Korrekturrunden-Sammelblock wie Rev. 0.5: Rev. 0.6 installiert **zwei inhaltliche Pflichten**,
> die beide **vom Nutzer entschieden** wurden und hier **nicht** neu bewertet werden.
> `status: APPROVED` und `approved: 2026-09-26` bleiben **unverändert**; die Ausführung W0–W8
> bleibt freigegeben. **Keine** Task-, Wellen-, AC-, IC-, R-, OQ- oder V-Check-ID wurde
> umnummeriert oder gestrichen; der einzige neue Plan-Task ist **W2-0**.
> - **U-1 → §4.1:** `scripts/lib/consistency/docs.py` wird zur **Fassade**; die Checks werden
>   nach Familien auf `docs_links.py`, `docs_freshness.py`, `docs_wiki.py`, `docs_index.py`
>   aufgeteilt, **jedes Modul < 600 Zeilen**. Das betrifft **Dateicheck-Module** und ist
>   **nicht** identisch mit der Fach-Modulaufteilung **M1–M4** — die Abgrenzung ist in §4.1
>   ausdrücklich hergestellt, damit keine Namensverwechslung entsteht.
> - **U-2 → AC-30:** AC-30 gilt künftig **nur** für **`README.md` + `llms.txt`**. Die **25** am
>   2026-09-27 gemessenen toten relativen internen Links unter `docs/**` werden als
>   **explizites Follow-up** `F-DOCS-LINKS-2026-09-27` mit **Owner `developer`** und **Termin
>   2026-10-11** geführt — **nicht** als AC und **nicht** stillschweigend. Der
>   **Weigerungsnachweis** (die Verengung trägt nur, weil die 2 verbleibenden Findings in
>   `README.md` liegen und W8-2 sie behebt) steht in **§17.10.2**.
> - **Zwei belegte Faktenkorrekturen** mitgenommen: die V3-Fundstellen in `README.md` sind
>   **`:722`/`:723`** (nicht `:721-723`), und `docs/REQUIREMENTS.md:21` ist
>   **kein** V3-Finding (Backtick-Pfade in einer Tabellenzeile, keine Link-Syntax) — die
>   Trace-Matrix-Zeile `| AC-30 | W8 | … |` ist entsprechend berichtigt (**K23**).
>
> > **Rev. 0.7 (2026-09-27) — Umsetzung von vier bereits getroffenen Nutzerentscheidungen:
> > E-5 (V4-Scope), E-6 (eigener Task für zwei rote Volltests), E-7 (V5 in ein eigenes Modul),
> > E-8 (Ledger-Writer adressiert diesen Plan).** Der Volltext steht in **§17.11**, der Katalog der
> > Korrekturen **K54…K58** ebendort, die V4-Scope-Definition in **§17.11.2**, die Modulgrenzen in
> > **§4.1** und die IC-05-Zeile in **IC-05**. **Dies ist ein echter Revisions-Bump** (über Rev. 0.6
> > hinweg) und **kein** Korrekturrunden-Sammelblock: Rev. 0.7 installiert **vier inhaltliche
> > Pflichten**, die alle **vom Nutzer entschieden** wurden und hier **nicht** neu bewertet werden.
> > `status: APPROVED` und `approved: 2026-09-26` bleiben **unverändert**; die Ausführung W0–W8
> > bleibt freigegeben. **Keine** Task-, Wellen-, AC-, IC-, R-, OQ- oder V-Check-ID wurde
> > umnummeriert oder gestrichen; die **zwei** neuen Plan-Tasks sind **W2-8** (E-6) und **W2-9**
> > (E-8) — die Taskzahl des Vorhabens steigt damit von **48** auf **50**.
> > - **E-5 → IC-05 (V4) und §17.11.2:** V4 (`check_readme_docs_index`, Check-ID **`docs.readme_index`**)
> >   verlangt **nicht** mehr, dass alle **205** `docs/**.md` außerhalb `archive/` in `README.md`
> >   verlinkt sind. Der **Scope** wird auf den **README-Index-Scope** begrenzt: V4 liest die
> >   **Dokumentations-Index-Region** von `README.md` (die `##`-Überschrift mit `Documentation Index`
> >   bis zur nächsten `##`-Überschrift) und prüft deren **deklarierte** `docs/`-Kategorien — jede
> >   deklarierte Kategorie muss (a) ein **existierendes** Verzeichnis sein und (b) **mindestens
> >   einen** `docs/<kategorie>/…`-**Link** in der Region tragen. **Unverändert bleiben:** Check-ID,
> >   Severity **ERROR** und `file` = `README.md` — und die **Signatur `(root: Path) ->
> >   list[Finding]`, einargumentig** (**K59 / RVW-7-01, Korrekturrunde 5**: die zweigliedrige Form
> >   `(root, config=None)` ist die Signatur der **neun neuen** V-Checks, **nicht** die des
> >   IC-05-gepinnten Altchecks; gemessen `docs_links.py:167`, Docstring `:170-172` „the parameter
> >   list stays `(root)`", Testpin `tests/test_doc_index.py` per `inspect.signature`).
> >   **Die 193** nicht im README verlinkten `docs/`-**Seiten** sind **kein** V4-Finding mehr, sondern
> >   **Follow-up `F-DOCS-README-INDEX-2026-09-27`** (Owner `developer`, Termin **2026-10-11**) —
> >   vollständige Liste in **§17.11.3**. **K60 / RVW-7-02:** die Herleitung lautet `205 − 12 = 193`,
> >   **nicht** `205 − 14 = 191` — die **14** in `README.md` genannten `docs/`-Pfade sind **12**
> >   `.md` + **2** `.html` (`docs/ui/agent-graph.html`, `docs/ui/admin-ui.html`). **Der Nachweis ist
> >   die Issue-Liste + ein once-count außerhalb V4**, **kein** `docs.readme_index`-Zählwert: V4
> >   zählt nach E-5 **Kategorien**, nicht Seiten, und ein V4-Zählwert **beobachtet diese Menge
> >   nicht** (ein solcher Nachweis wäre **vakuum**). **Grenze gegen V2:** V2 liest `docs/INDEX.md` und ist
> >   **seiten**-genau (alle nicht-Archiv-`docs/**.md`); V4 liest `README.md` und ist
> >   **kategorie**-genau (die vom handgepflegten Index deklarierten Scopes). **Grenze gegen V3:** V3
> >   prüft, ob ein **Linkziel existiert**; V4 prüft **nie** ein Linkziel, sondern ob eine
> >   **deklarierte Kategorie repräsentiert** ist — ein toter Link in der Index-Region ist ein
> >   **V3**-Finding und **kein** V4-Finding (keine Doppelmeldung).
> > - **E-6 → Plan §17.11 / Task W2-8:** die zwei roten Volltests
> >   `tests/test_knowledge_engine.py::test_knowledge_roles_pass_schema_validation` (`:221`, Assert
> >   **`:228`**) und
> >   `tests/test_sharkord_service_name_migration.py::test_generated_docker_agent_has_no_leftover_platform_namespace_placeholder`
> >   (`:34`, `--validate`-Assert **`:48`**) erhalten einen **eigenen** Task **W2-8** mit eigenem
> >   `Files:`, eigenem Agent, eigenen AK und **Position vor W2-7**. Beide Tests hängen am
> >   repo-globalen `--validate`-Exit-Code; dieser ist nach **§10, Aufzählungspunkt `--validate`**
> >   **planmäßig rot** (V1/V2/V3/V6, **Korrekturrunde 5 / K67: seit Rev. 0.7 zusätzlich V4** mit
> >   **1** ERROR — Kategorie `docs/se-cascade/`, Follow-up `F-DOCS-README-INDEX-SE-2026-09-27`;
> >   V4 ist **bereits registriert**, `consistency-check.py:53`/`:201`) — W2-8 entkoppelt beide Tests
> >   von dieser Fremdgröße. **Ergänzung Korrekturrunde 5 (K63 / RVW-7-05):** von den drei in
> >   W2-8 benannten Entkopplungsmechanismen sind an W2-8s Position nur **(i)** und **(iii)**
> >   anwendbar; **(ii)** stützt sich auf das **Common-Gate**, das erst in **W2-7** entsteht, und ist
> >   deshalb aus W2-8s zulässiger Liste gestrichen (als spätere Option erhalten).
> > - **E-7 → §4.1:** **V5** `check_role_generation_parity` wird aus `docs_freshness.py` in das neue
> >   Modul **`scripts/lib/consistency/docs_freshness_v5.py`** ausgelagert. Grund: `docs_freshness.py`
> >   ist nach W2-5 gemessen bei **592** Zeilen; V5 braucht realistisch **55–70** Zeilen und würde die
> >   harte **< 600**-Grenze reißen. **Größenfolge:** `docs_freshness.py` **592** (V1a/V1b + V6,
> >   **8** Zeilen Reserve) · `docs_freshness_v5.py` **≈ 55–70** (V5) — **beide < 600** ✓. Die
> >   Zuordnung bleibt **12/12 disjunkt**, jetzt auf **5** statt 4 Module verteilt (**K56**).
> > - **E-8 → Plan §17.11 / Task W2-9:** `TASK_HEADER_RE` (`scripts/lib/plan_identity.py:27-30`,
> >   verwendet in `scripts/lib/plan_ledger.py:25`/`:71`/`:133`) wird um einen alternativen Zweig für
> >   die **Wellen-/Task-Header-Form** dieses Plans (`### W2-0: …`) erweitert, und `normalize_task_id`
> >   (`plan_identity.py:63-73`) lernt die ID-Form `W<n>-<k>`. **Positionierung:** W2-9 läuft in
> >   **Phase 0** von W2, **vor** PG-2a ⇒ **der Ledger-Writer ist ab W2-9 einsetzbar, also für
> >   W2-6, W2-4, W2-8 und W2-7** (die K53-Interim-Regel des manuellen Abhakens endet mit W2-9).
> >   **Ausdrücklich festgehalten: „Ledger-Writer einsetzbar ab Task W2-9"** — **nicht** ab heute
> >   (Stand vor W2-9 gilt die widerrufbare K53-Interim-Regel: der Orchestrator hakt von Hand ab).
> > - **Eine Belegkorrektur mitgenommen (K58):** der Auftrag und der Korrekturrunden-4-Block nennen
> >   `TASK_HEADER_RE` als in `scripts/lib/plan_ledger.py` liegend. **Gemessen** ist: die
> >   **Definition** steht in `scripts/lib/plan_identity.py:27-30`, `plan_ledger.py` ist der
> >   **Konsument** (Import `:25`, `finditer` `:71`, Tupel-Entpackung `:133`). W2-9 besitzt deshalb
> >   **beide** Dateien, wobei `plan_ledger.py` nur geschrieben wird, falls sich der Zwei-Gruppen-
> >   Vertrag ändert.
> > - **Zählungen, ehrlich gemessen (Plan-Abschnitt L, Rev. 0.7):** Checkboxen **199 → 207**
> >   (`[x]` **59** unverändert, `[ ]` **140 → 148**), Tasks **48 → 50**. Herleitung:
> >   44 × 4 + 5 × 5 + 1 × 6 = **207**. **Keine** Zahl ist geschätzt; die Zählung ist im Plan
> >   dokumentiert und gegengeprüft.
> > **Bewusst nicht angefasst:** die Rev.-0.6-Blöcke (§17.10, §17.10.5), die Korrekturrunden 1–4 des
> > Plans (K25…K53) und die dortigen Entscheidungsvorlagen-Tabellen **E-5…E-8** bleiben
> > **wortgleich** und dokumentieren den Stand **vor** der Entscheidung; **maßgeblich** sind die
> > **Plan-Legende**, dieser Rev.-0.7-Block und **§17.11**.
>
> > **Rev. 0.8 (2026-09-29) — agent-meta-Ausnahme im KE-Vorrang-Gate (IC-25/IC-26) —
> > ACHTUNG: `status: APPROVED` DECKT DIESEN UMFANG NICHT.** Der Volltext steht in
> > **§17.12**, der Katalog der Korrekturen **K-1…K-5** ebendort (§17.12.1), die
> > Entscheidungsvorlagen **E-9…E-13** in **§17.12.2**, die Nachweis- und
> > Testakzeptanztabelle in **§17.12.4**. **Dies ist ein echter Revisions-Bump** und **kein**
> > Korrekturrunden-Sammelblock.
> >
> > **Vorentscheidung des Nutzers (bereits getroffen, hier NICHT neu bewertet):** eine
> > **explizite agent-meta-Ausnahme**, damit **W3-6** `docs/INDEX.md` schreiben kann; die
> > **Knowledge Engine bleibt für Consumer-Projekte autoritativ**. **Ausdrücklich nicht
> > entschieden und nicht unterstellt:** eine globale Umstellung von `index.mode` — der
> > genehmigte Schlüssel ist ausschließlich `docs-consolidation.index-owner` (IC-25), **kein**
> > `project.name`-/`platforms`-Vergleich und **keine** agent-meta-Erkennung über
> > Repo-Struktur (DECISION-1, §17.12.3).
> >
> > **Internen Verweisen dieser Revision gilt eine bewusste Regel:** Rev. 0.8 fügt Zeilen **oberhalb**
> > fast aller späteren Abschnitte ein. Alle von Rev. 0.8 **neu** gesetzten Verweise auf **eigene**
> > Abschnitte sind deshalb **namenbasiert** (`IC-13`, `AC-21`, `R7`, `§17.12.1`) und **nicht**
> > zeilenbasiert — sonst wiederholte Rev. 0.8 genau der Anker-Drift, den sie als **K-4** und
> > **V-D1/V-D2** gerade abstellt. **Verweise auf Code, Config, Tests und Pläne bleiben
> > `Datei:Zeile`** und sind am Working Tree gemessen.
> >
> > **P-1…P-5 SIND ZUR USER-FREIGABE AUSSTEHEND.** Sie sind **inhaltliche Pflichtänderungen**
> > der APPROVED-Fassung an **fünf normativen Stellen** (IC-13, IC-15, IC-22-Tabelle,
> > AC-21 + AC-39, R7). `status: APPROVED` und `approved: 2026-09-26` bleiben unverändert,
> > und der **freigegebene Umfang W0–W8 bleibt vollständig freigegeben** — Rev. 0.8
> > installiert **keine** neue Task-ID, **keine** neue Welle und **keinen** neuen V-Check; sie
> > ändert **ausschließlich** die Bedingung, unter der das bereits verdrahtete Gate
> > `_index_mode_block_reason()` einen Schreibvorgang verbietet. **Bis zur Freigabe von
> > P-1…P-5 darf W3-6 die Ausnahme nicht umsetzen.**
> >
> > - **P-1 → IC-13** (Situationstabelle, Zeile „`resolve_index_mode` ⇒ kein Schreiben"): die
> >   Zeile ist **absolut** formuliert und wird **bedingt**; die Verengung liegt in
> >   `_index_mode_block_reason()` (`doc_renderer.py:702-703`). **Kein** Formulierungsfehler —
> >   ein **neuer Vertrag**.
> > - **P-2 → IC-15** (Skeleton-Übernahme-Absatz): IC-15 regelt nur den **Skeleton**-Fall
> >   (`resolve_index_mode() == "file-index"`). In agent-meta entsteht der Index **ohne**
> >   Skeleton (Neuanlage, `doc_renderer.py:829-830`). IC-15 wird dadurch **nicht falsch,
> >   sondern unvollständig**; ergänzt wird die Neuanlage-Bedingung.
> > - **P-3 → IC-22** (Config-Tabelle **und** ihr Fail-off-Absatz): ein **siebter** Key
> >   (`index-owner`) kommt hinzu; „**alle sechs** Keys" wird zu „alle **sieben**". **Erweitert
> >   gemessen (P-3 (e), §17.12.1):** **AC-39** nennt „**genau** den **sechs** Properties" — der
> >   Schema-**Block** hat heute **fünf**
> >   (`config/project-config.schema.json:2424-2469`), und sein **gepinnter** Test
> >   `tests/test_docs_consolidation_migration.py::test_schema_block_present_and_closed`
> >   (`:81`, `_EXPECTED_PROPERTIES` `:45-51`) ebenfalls **fünf**; die Zahl **sechs** ist damit
> >   bereits heute falsch und wird durch `index-owner` nicht richtiger. Rev. 0.8 stellt sie auf
> >   den **gemessenen** Stand.
> > - **P-4 → AC-21** (zweiter Given/When/Then-Block): die
> >   KE-Autorität zur **ungefähren** Vorbedingung. Mit der Ausnahme ist sie **bedingt** ⇒
> >   **zusätzliche** AK für den Override-Pfad (**AC-42**) und für die Absenz-Semantik
> >   (**AC-43**), sonst widerspräche der Test der Spec.
> > - **P-5 → R7** (Mitigation-Tabelle): zwei Hebel plus Besitzregel und
> >   `index-mode: skeleton`; ein **dritter** Hebel (`index-owner`) kommt hinzu. Das **Risiko
> >   selbst sinkt** in agent-meta (dort gibt es nur einen Writer), die normative
> >   Mitigation-Tabelle ändert sich.
> >
> > **Neu:** **IC-25** (Key, Werte, Fail-closed-Zweig, geänderte Entscheidungsfolge) und
> > **IC-26** (Begrenztheitsvertrag) in §5.2; **eine** Zeile in der **IC-22**-Tabelle;
> > **AC-42…AC-46** in §7 (M2); **AC-21** bedingt, **AC-39** korrigiert; **R7** um den dritten
> > Hebel ergänzt; Revisionszeile **0.8**; §15 Trace-Anker. **Keine** bestehende IC-, AC-,
> > Task-, Wellen-, V-Check-, R-, OQ- oder F-ID wurde umnummeriert oder gestrichen — IC-16
> > war bereits belegt (Hash-Baseline-Vertrag `scripts/lib/generated_file_drift.py:75-91`),
> > IC-17…IC-24 ebenfalls, deshalb beginnen die
> > neuen ICs bei **IC-25**; die neuen ACs beginnen bei **AC-42** (AC-01…AC-41 belegt).
> >
> > **Korrekturen ohne Freigabebedarf (K-1…K-5, §17.12.1):** **K-1** Docstring
> > `doc_renderer.py:669-672`; **K-2** Docstring `tests/test_doc_renderer.py:3209-3223`;
> > **K-3** Zählkommentar `tests/test_docs_consolidation_migration.py:42-44` (K-77: der
> > Kommentar **existiert** — die frühere Angabe „Zeile leer" war eine Fehlmessung, per Grep
> > widerlegt); **K-4** zwei
> > **veraltete Zeilenanker** `spec_plan_scaffold.py:62-68` → **`:115-121`** und
> > `:40-44` → **`:80-97`** (beide **am Working Tree gemessen**); **K-5**
> > `doc_renderer.py:685-686` („the complete list of what forbids a write") bleibt
> > **wortwörtlich stehen** — die Liste blockierender Eigentümer bleibt **geschlossen** (zwei),
> > weil der neue Key keinen Eigentümer **hinzufügt**, sondern nur den einen **Auslöser**
> > stilllegt.
> >
> > **Korrekturrunde zu Rev. 0.8 (2026-09-29, Concept-Review Runde 8, `CHANGES_REQUESTED`:
> > 5 major / 5 minor / 0 kritisch) — Katalog `K77…K86`, §17.12.6. `status: APPROVED` und
> > `approved: 2026-09-26` bleiben unverändert, `pending-approval:` besteht fort.** Die Runde
> > behob **ausschließlich Beleg- und Zuordnungsfehler** und erzeugte **keine** neue Pflicht
> > **außerhalb des bestehenden P-3** (die einzige Sollwert-Präzisierung dieser Runde, die zweite
> > Mengen-Pin, ist **P-3 (e) / „P-3-E"** — die fünfte Zeile der P-Tabelle, kein sechstes
> > P-Element): **P-1…P-5 (inkl. P-3-E) bleiben zur User-Freigabe ausstehend**, **E-9…E-13 und
> > OQ1 bleiben offen**. Vier Korrekturen sind **inhaltlich** und daher im Freigabe-Snapshot zu
> > bestätigen: (1) **zwei** statt einer harten Sollwert-Änderung — `_EXPECTED_PROPERTIES`
> > **und** `_IC22_ABSENCE_DEFAULTS`, beide fünf → sechs (K-78, V-D4); (2) **T-8 → T-3 → T-5
> > liegen alle in W3-6** — die technische Unteilbarkeit ist gemessen (V-D7), E-13a in seiner
> > bisherigen Formulation ist damit **nicht durchführbar** (K-80); (3) §12.3 (g) führt das
> > **Restrisiko „Ausnahme wird von einem Consumer-Projekt kopiert"** — **nicht** akzeptiert,
> > als **Ergänzung zu E-13** offen, jetzt als eigene Optionenzeile **E-13c** in §17.12.2
> > ausgewiesen (K-81); (4) die **Trace-Matrix** führt AC-42…AC-46 jetzt
> > mit, Zählsatz W3 14 → **19** (K-79).
> >
> > **Zweite Korrekturrunde zu Rev. 0.8 (2026-09-29, Concept-Review Runde 9,
> > `CHANGES_REQUESTED`: 2 major / 7 minor / 1 info) — kein Revisions-Bump, kein ID-Zuwachs.**
> > RVW9-1 (major): Katalog-IDs **K61…K70 ⇒ K77…K86**; die belegte Obergrenze ist **K76**
> > (Plan-Legende, **gemessen**), **K1…K76 bleiben unberührt**, je **genau einmal** belegt. **RVW10-1 (major):** der erste Wurf **K61…K70** und die Zwischenlage **K76…K85** waren beide **dokumentübergreifend kollidierend** (`K76` ist im Plan belegt) ⇒ der Katalog steht jetzt endgültig auf **K77…K86**; **RVW10-2 (minor):** V-D1-Selbstverweis auf **`:1487-1488`** statt `:1465-1466`; **RVW10-3 (info):** zweiter Träger derselben Ordinal-Formulierung geprüft und registriert (`tests/test_doc_renderer.py:1090`, **unverändert**). RVW9-2
> > (major): **V-D8** als Plan-Befund registriert — Plan Rev. 0.7 kennt Rev. 0.8 nicht, die
> > W3-6-Akzeptanz nach §17.12.4 ist **vom heutigen Plan aus unerfüllbar**; der **forderliche
> > Plan-Delta** ist in **§17.12.5 (V-D8-Uebergabe)** präzise benannt und wird **erst nach**
> > User-Freigabe von P-1…P-5 ausgeführt — **dieser Spec-Text ändert den Plan nicht**.
> > RVW9-3…RVW9-9 (7 minor) + 1 info: T-4-Ordinal „sixth" ⇒ **„seventh"**; **E-13c**
> > (Kopier-Pfad) als dritte Optionenzeile in §17.12.2 und Q4-Verweis auf **§12.3** statt
> > §17.12.3; P-3-E als **P-3 (e)** geklärt; Testname
> > `::test_schema_declares_the_absence_defaults` (`:185-199`) statt des Wildcards
> > `::test_fail_off_defaults_*`; K-78 auf Modus-Übersicht Zeile 8 / T-3 / Coverage umgestellt;
> > V-D1-Selbstverweis `:1449-1450` ⇒ **`:1465-1466`**; W1-10-Step-2-Reihenfolge vor W3-6
> > festgehalten. **Keine** P-1…P-5 wurde inhaltlich geändert, **keine** offene Vorlage
> > entschieden, `pending-approval:` besteht fort.
> >
> > **E-5…E-8 werden NICHT neu aufgerollt** (Rev. 0.7, §17.11, entschieden 2026-09-27).
> > **E-9…E-13 sind NEUE, offene Entscheidungsvorlagen** mit Optionen, Empfehlung und
> > Auswirkung auf W3-6 / W3-7 / W4-1…W4-3 (§17.12.2). **OQ1 bleibt offen**, Owner `main_chat`
> > (`docs/plans/2026-09-25-docs-consolidation-oq1.md:94`, Blockade **W5**, `:99`); die
> > agent-meta-Ausnahme berührt `knowledge/wiki/**` **nicht** und hebt diese Blockade
> > **nicht** auf.
> >
> **Legende der Kennungen (neu, Rev. 0.6, K25 — beseitigt die ID-Kollision `E-1`/`E-2`/M1;
> Bereich korrigiert in K42, Eindeutigkeit hergestellt in K41).**
> In Rev. 0.6 sind zwei **verschiedene** Nummernkreise entstanden, die beide `E-1`/`E-2` hießen.
> Sie sind ab hier **getrennt geführt**. **Aussage zur Eindeutigkeit (K41, präzisiert):** Nach der
> Bereinigung des K-Namensraums in Runde 2 ist **jede** `U-`-, `E-`- und `OQ`-Kennung **von Natur
> aus** eindeutig (verschiedene Präfixe, durchgezählt), und **jede** `K-`-Kennung ist **genau
> einmal** belegt — belegt durch die **Katalog-Tabellen K25…K40** (Korrekturrunde 1) und
> **K41…K45** (Korrekturrunde 2) in §17.10.5 dieses Dokuments und im Plan-Kopfblock; der
> **wahre Endstand ist K45**. **In der Erstfassung von Runde 1 war diese Aussage nicht wahr**
> (`K26` sechsfach, `K27` doppelt); sie ist deshalb hier nicht behauptet, sondern **mit den
> Tabellen belegt**.
>
> | Präfix | Bedeutung | Status | Ort |
> |---|---|---|---|
> | **`U-*`** (U-1, U-2) | **Nutzerentscheidung** — vom Nutzer **getroffen** und **geschlossen** | **geschlossen** | Rev. 0.6, §4.1, §17.10 |
> | `E-*` (E-1…E-4) | **Errata-Liste / Entscheidungsvorlage** des Rev.-0.5-Ausführungs-Ledgers (Abschnitt L-3 des Plans) bzw. **offene** Entscheidungsvorlage | E-01…E-15: Errata · E-1…E-4: **offen**, unentschieden · **E-5…E-8: ENTSCHIEDEN 2026-09-27** (Rev. 0.7, §17.11) | Plan Abschnitt L-3; Spec §17.9.4, **§17.11** |
> | `OQ*` (OQ1…OQ10) | **offene Frage** an den Auftraggeber, mit Owner und Frist | **offen** (OQ1, OQ3, OQ4, OQ9, OQ10) | Spec §11.1 |
> | `K-*` (K1…**K45**) | **Korrektur-Kennungen** dieses Vorhabens (kein Status, nur Auditierbarkeit) | — | Rev.-Kopfblöcke, §17 |
>
> >   **K-Bereich, Rev. 0.7 (K57, additiv — die Spec-Legende bleibt eingefroren).** Die Zeile oben
> > nennt `K1…K45`; sie bleibt **unverändert**, weil die Spec-Legende seit **K42** bewusst
> > eingefroren ist (Stand Korrekturrunde 2). **Maßgeblich** für den heutigen K-Stand ist die
> > **Plan-Legende** (`K1…K70` — **Stand Korrekturrunde 5**; **Korrekturrunde 6 hat sie auf
> > `K1…K75` verlängert**, §17.11.6, Muster K36/K42: diese Zeile nennt ihren damaligen Stand und
> > bleibt **wortgleich**). **Rev. 0.7 hat den Katalog um `K54`…`K58` verlängert**
> > (E-5-Mechanismus, E-7-Modulgrenze, E-8-Werkzeugpfad, Zählung, Faktenkorrektur) — Volltext
> > **§17.11.1**; **Korrekturrunde 5** um `K59`…`K70` (11 Review-Findings + 5 Validator-Notizen) —
> > Volltext **§17.11.5**; **Korrekturrunde 6** um `K71`…`K75` (1 major · 3 minor · 1 info,
> > rein mechanisch) — Volltext **§17.11.6**.
>
> **Umbenennung, ausdrücklich und additiv:** Die beiden Rev.-0.6-Nutzerentscheidungen hießen in der
> Erstfassung dieses Revisionsblocks `E-1`/`E-2` und wurden deshalb als **K25** auf **`U-1`/`U-2`**
> umbenannt — **an allen Stellen** beider Dokumente. Die **E-1…E-4** der Rev.-0.5-Ledger und der
> Entscheidungsvorlagen bleiben unter ihrer Kennung **unverändert** und sind **keine**
> Nutzerentscheidungen. Eine Verwechslung ist damit **strukturell** ausgeschlossen.
>
> **Rev. 0.5 (2026-09-26) — Präzisierung der Gates W2/W3, Schließung zweier
> Eigentümerlücken.** Der Volltext steht in **§17.9**, die Review-Korrekturliste der zweiten
> Korrekturrunde in **§17.9.4**. `status: APPROVED` und `approved: 2026-09-26` bleiben
> **unverändert**; die Ausführung W0–W8 bleibt freigegeben. **Rev. 0.5 wurde am 2026-09-26
> per A2A-Envelope beauftragt** (Korrekturen 1–5, s. u.) — **keine** Pflicht **jenseits** dieses
> beauftragten Umfangs; **innerhalb** des Umfangs ändert Rev. 0.5 sehr wohl **Nachweisformen**
> (Präzisierung der Normativitätsaussage: **§17.9.4**). Das nach Master-Rule
> `spec-plan-workflow` verpflichtende Concept-Review über **Rev. 0.5** ist in **§17.9** mit Owner
> und Ergebnis-Ort benannt.
>
> **Trace-Anker (aus dem Systemdesign **unverändert** übernommen und vom Plan zu referenzieren):**
> `spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25`.
>
> **Verbindliche Eingangsgrundlage:** `docs/specs/2026-09-25-repository-documentation-consolidation-design.md`
> (concept-architect, 2026-09-25, Entscheidungen T-1…T-6, Komponenten C1…C8,
> Checks V1…V9, Wellen W0…W8, Risiken R1…R11, offene Fragen OQ1…OQ6, Downstream-Impacts B1…B6).
> Alle `Datei:Zeile`-Angaben zu `scripts/lib/`, `scripts/`, `config/`, `.meta-config/`,
> `tests/scenarios/`, `knowledge/` und zur Root-Doku wurden am 2026-09-26 gegen den Working
> Tree **re-verifiziert**. Wo diese Spec bewusst vom Design abweicht, steht die Abweichung
> mit Begründung in §13 „Abweichungen vom Design" — stillschweigende Abweichungen gibt es
> nicht.
>
> **Rev. 0.2 (2026-09-26) — Überarbeitung nach Concept-Review (CHANGES_REQUESTED).**
> Eingang: Concept-Review der Rolle `concept-reviewer` vom 2026-09-26 (Verdikt
> **CHANGES_REQUESTED**, 5 kritisch / 8 mittel / 3 niedrig + 5 Aufnahmepunkte; das
> Review-Artefakt selbst ist ein Session-Artefakt und nicht Teil des Repo-Baums — der
> vollständige Findings-Abgleich steht in §17.1). **Alle 16 Findings sind behoben.**
> Sieben Reviewer-Angaben wurden **eigenständig am Repo nachgeprüft**; **drei davon waren
> selbst ungenau und sind korrigiert** (dokumentiert in §17.2). Die Frontmatter blieb
> zu diesem Zeitpunkt `status: Entwurf` — es lag keine User-Freigabe vor.
>
> **Rev. 0.3 (2026-09-26) — Überarbeitung nach Re-Review (CHANGES_REQUESTED, 0 kritisch /
> 2 major / 4 minor / 2 info).** Eingang: Re-Review der Rolle `concept-reviewer` vom
> 2026-09-26 (Verdikt **CHANGES_REQUESTED**, `RESIDUAL_BLOCKERS: Keine`,
> `PLAN_READINESS: Ja`; vollständiger Abgleich in §17.5). **Alle 8 Findings (NEW-1…NEW-8) sind
> behoben**, zusätzlich die **Gegenkorrektur** des Re-Reviewers zu §17.2. **Neu:** `README.md:381`
> als **zweite** F22-Fundstelle (NEW-2) — F22 ist damit eine Zwei-Stellen-Falschzahl wie F3/F14;
> `DOCS_HOOK_SCRIPT_FILES_COUNT == 17` **entfällt** und wird durch
> `DOCS_HOOKS_1GENERIC_COUNT == 9` ersetzt (NEW-1, semantisch an `README.md:696` gebunden);
> Sollwert-Zahl **einheitlich elf** (NEW-4); AC-02 ist **durchsetzbar** formuliert, der
> `xfail`-Snapshot ist als unenforceable entfernt und seine Durchsetzung nach IC-23/AC-36
> **verlagert** (NEW-8). Im selben Codepfad zusätzlich **NF-12** gefunden: `HOOK_EXCLUDED_SUFFIXES`
> schrieb `"_impl.sh"` statt `"-impl.sh"` — die Regel hätte nichts gematcht. Alle übrigen
> Rev.-0.2-Korrekturen (16 Vorreview-Findings, R14–R18, Threat Model, OQ8, OQ6-Reihenfolge)
> sind als behoben **bestätigt** und wurden nicht angefasst. Die Frontmatter blieb
> zu diesem Zeitpunkt `status: Entwurf` — es lag keine User-Freigabe vor.
>
> **Rev. 0.4 (2026-09-26) — Ausführungskorrektur der Branch-/PR-Strategie (offener Punkt OP-1
> der Ausführungs-Records).** Diese Revision korrigiert **drei Normativitätsstellen** und deren
> Folgeverweise: die in Rev. 0.1–0.3 wörtlich „**Verbindlich**" geforderte Strategie „**ein Branch
> pro Welle** (`chore/docs-consolidation-w<N>`), gestapelte PRs" — geführt in der **W0-Zeile von
> §9.2** (OP1-1), im **§9.2-Absatz „PR-/Branch-Kollision"** (OP1-2) und in der **Mitigation von R16**
> (§12.2, OP1-3) — trug die **tatsächlich ausgeführte** Strategie nicht.
> Umgesetzt ist **ein** Wellen-Branch `feat/repository-documentation-consolidation-main` (Basis
> `origin/main`) mit **einem** PR gegen `main`; die Wellen laufen als **sequenzielle Commits** mit
> Wellenkennung im Commit-Titel. Da dieses Dokument sich zur **normativen Quelle** erklärt
> (Kopfzeile „stillschweigende Abweichungen gibt es nicht"; §2.2 „hart — Abweichung gilt als
> Spec-Verstoß"), wäre der eingefrorene Stand eine Verletzung der eigenen Norm — die Korrektur ist
> deshalb **hier** und **sichtbar** erfolgt, nicht in den Ausführungs-Records. **Keine inhaltliche
> Neuerfindung:** unverändert bleiben
> AC-01…AC-41, IC-01…IC-24, NFA-01…NFA-11, R1…R20 (R16 **nur** im Lösungsansatz), F1…F25,
> M-1…M-13, NG-1…NG-11, FI-1…FI-10, OQ1…OQ9, W0…W8, die Modulaufteilung M1–M4, die Welleninhalte
> und die SSoT-Zielstruktur; **keine** neue Welle, **kein** neues AC/IC/NFA/Risiko, **keine**
> geänderte Architektur. **A13 (neu, rev. 0.4): das Design nennt in seiner W0-Zeile einen
> Branch mit anderem Namen** — `chore/docs-consolidation`
> (`docs/specs/2026-09-25-repository-documentation-consolidation-design.md:265`) gegenüber
> `feat/repository-documentation-consolidation-main` (Basis `origin/main`) hier. Das Design
> verlangt an keiner Stelle gestapelte PRs; die **Zahl** der Branches stimmt, der **Name**
> nicht — das ist eine bewusste Abweichung (**§13 A13**), keine stille. **A14 (neu, rev. 0.4):
> offene Abweichung** — §9.2 führte W4/W5/W6 paarweise parallel, ausgeführt werden sie
> **sequenziell** (**§13 A14**, **§17.8**). §13 umfasst damit **14** Abweichungen
> (A1…A12 unverändert, A13/A14 neu). Volltext, betroffene Stellen und Ausführungsbelege:
> **§17.6**, Freigabe-Auflösung **§17.7**, offener Punkt **§17.8**. Der **formale Abschluss von
> OP-1 in Plan und W0-Records ist ein Folgeschritt** und nicht Teil dieser Revision; das
> **Concept-Review über Rev. 0.4 ist erfolgt** (2026-09-26, `VERDICT: BLOCKED`, F-1) und der
> **Entscheidungsweg `main_chat`** (Plan Rev. 0.4, K1) hat am 2026-09-26 entschieden
> (**§17.7**).
>
> **Freigabevermerk (2026-09-26).** Freigebende Instanz: **Nutzer-Freigabe**, über `main_chat`
> an den `orchestrator` weitergeleitet und hier durch die Rolle `documenter` auf Veranlassung
> des Orchestrators formalisiert. Review-Stand: **Runde 1** (Concept-Review vom 2026-09-26)
> endete mit `CHANGES_REQUESTED` und **5 kritischen Befunden** (K1…K5) → Rev. 0.2 mit
> **16 behobenen** Vorreview-Findings; **Runde 2** (Re-Review vom 2026-09-26) endete mit
> **0 kritischen Befunden**, `RESIDUAL_BLOCKERS: Keine` und `PLAN_READINESS: Ja` → Rev. 0.3
> mit **8 behobenen** Findings (NEW-1…NEW-8) plus der Gegenkorrektur zu §17.2. **Umfang der
> Freigabe:** sie umfasst die **Ausführung der Wellen W0–W8** dieses Vorhabens inklusive der
> in §11.1 weiterhin offenen, mit Owner und Wellen-Blockade versehenen Entscheidungen.
> **Datumsabweichung (dokumentiert):** der Nutzer hat den 2026-09-25 genannt; das ist das
> Datum der **Anfrage**, nicht das der Freigabe. Der Freigabevermerk trägt daher korrekt
> **2026-09-26**.
>
> **Rev. 0.5 (2026-09-26) — Präzisierung der Gates W2/W3, Schließung zweier
> Eigentümerlücken (Katalog K13…K17, Volltext §17.9).** Die Ausführungskorrektur der
> Branch-Strategie (Rev. 0.4) bleibt **unberührt**; diese Revision folgt aus dem
> Ausführungs-Ledger des Plans (Rev. 0.4, Abschnitt L, Befunde **B-1**, **B-2**, **B-4**,
> **B-5**), der vier belegte Gate-/Ownership-Mängel aufgenommen hat. **Betroffene Stellen:**
> §10 (Pflichtumfang des `--strict`-Gates, **zusätzlich** Punkt 5/6 in Rev. 0.5), §5.1.1
> Suppressionsregel 3 (Widerspruch zu IC-05), **§12.1 R4** (V1-Fehlalarme — **RVW-7**: R4 liegt in
> §12.1 und enthält **keine** Aussage zur Hochstufungsreihenfolge; die Reihenfolgebindung ist
> eine Ausführungs-Vorbedingung des Plans, siehe §17.9.4/RVW-4) — alle **präzisierend**.
> **Neu in §17.9:** die
> belegte Nachmessung, die die Auftragsprämisse „V1 emittiert ERROR" **widerlegt** (V1
> emittiert im Ist-Zustand **WARNING**, und ist im Runner **gar nicht** registriert), sowie
> die Feststellung, dass §10s Datei-Scope die Doku-Checks **nicht** erfasst.
> **Unverändert:** AC-01…AC-41, IC-01…IC-24, NFA-01…NFA-11, R1…R20, F1…F25, M-1…M-13,
> NG-1…NG-11, FI-1…FI-10, OQ1…OQ9 (OQ1 bleibt **offen**), W0…W8, die Modulaufteilung M1–M4,
> die SSoT-Zielstruktur, der Ausführungsfreigabeumfang und `status: APPROVED`.
> **Kein** Task-, Wellen-, AC-, IC-, NFA-, Risiko- oder OQ-ID wurde geändert, **keine**
> Entscheidung (OQ2/OQ6/OQ8) umgedreht, **kein** OP-1- oder OQ1-Abschluss.
>
> **Zweite Korrekturrunde derselben Revision (`concept-reviewer`, 2026-09-26,
> `VERDICT: CHANGES_REQUESTED`, 15 Findings RVW-1…RVW-15).** Kein Revisions-Bump — `revision`
> bleibt **0.5**. **Autorisierung (RVW-5b):** der Auftraggeber hat am **2026-09-26** über ein
> A2A-Envelope genau die Korrekturen **1–5** beauftragt — (1) W2-Gate, (2) W3-7-Gate-Scope,
> (3) `report.py`-Ownership, (4) Fenced-Code-Regel 3, (5) Anker/Zählungen — und **ausdrücklich
> die Beibehaltung von `status: APPROVED`** verlangt. Der Review hat **innerhalb** genau dieses
> Umfangs nachgeschärft. **Präzisierung der Normativitätsaussage (RVW-5a):** „keine neue
> normative Pflicht" war unhaltbar und wird ersetzt durch „keine Pflicht **jenseits** des
> beauftragten Umfangs" — **innerhalb** ändert Rev. 0.5 Nachweisformen (§17.9.4). Vollständige
> Liste: **§17.9.4**.
>
> **Dritte Korrekturrunde derselben Revision (`concept-reviewer`, 2026-09-26,
> `VERDICT: CHANGES_REQUESTED`, 14 Findings RVW2-1…RVW2-14: 2 Blocker, 4 Major, 7 Minor, 1 Info).**
> **Kein Revisions-Bump** — dieselbe, noch unveränderte Korrekturrunde; `revision` bleibt **0.5**,
> `status: APPROVED` und `approved: 2026-09-26` bleiben unverändert. **Betroffene Stellen:** §10
> Aufzählungspunkt `--validate` (Mechanik und Terminierung), §10, `--strict`-Punkt, Unterpunkt 5
> (Präsenzregel statt Registrierungszahl; V9 ohne Sollwert; Verschlechterungs-Ausnahme),
> §6(b) (**unverändert**,
> Präzisierung als Entscheidungsvorlage E-3 zurückgestellt), §17.9.4 (Normativitätstabelle um
> **(vii)**…**(x)**; Behandlungstabelle RVW2-1…RVW2-14; Entscheidungsvorlagen **E-1**…**E-4** — in
> der dritten Runde **vier**, die drei Prosa-Erwähnungen sind in der vierten Runde nachgezogen,
> RVW3-4). **Ankerpräzisierung (RVW3-9, vierte Runde):** die beiden Verweise auf „§10 Punkt 1"
> und „§10 Punkt 5" gehören **verschiedenen Ebenen** — Punkt 1 ist der Top-Level-Aufzählungspunkt
> `--validate`, Punkt 5 der **Unterpunkt 5** des `--strict`-Punkts. Ab der vierten Runde wird
> deshalb **benannt statt gezählt**: „§10, Aufzählungspunkt `--validate`" bzw.
> „§10, `--strict`-Punkt, Unterpunkt 5".
> **Plan-Seite:** Wellenblöcke W2…W8, Tasks W2-7, W3-4, W3-6, W3-7, W4-3, W5-1, W5-2, W6-2, W7-5,
> W8-2, W8-3, W8-4, Matrix, Zyklenprüfung, DoD Punkt 2, Self-Review, Abschnitt L (L-1, L-2).
> **Unverändert:** alle AC-/IC-/NFA-/R-/F-/M-/NG-/FI-/OQ-/W-IDs, OQ1 **offen**, OQ2/OQ6/OQ8
> geschlossen, OP-1 unberührt, `status: APPROVED`, keine Produktionsänderung.
>
> **Vierte Korrekturrunde derselben Revision (`concept-reviewer`, 2026-09-26,
> `VERDICT: CHANGES_REQUESTED`, 10 Findings RVW3-1…RVW3-10: 0 Blocker, 6 Major, 4 Minor).**
> **Kein Revisions-Bump** — dieselbe Korrekturrunde; `revision` bleibt **0.5**, `status: APPROVED`
> und `approved: 2026-09-26` bleiben unverändert. **Gehebe dieser Runde:** ausschließlich
> **Korrektur** — falsche Sollwert-Formulierungen, Widersprüche, Step-/Zeilenanker und
> Selbstverweise; **keine** neue Gate-Form, **kein** neues Kommando, **kein** neuer Sollwert,
> **keine** neue Task-ID, **keine** neue Ausführungspflicht. **Plan-Seite:** `W-VALIDATE-ROT`
> (W8-2…W8-4, W3-6), Task **W4-3** Schritt 3, Task **W5-2** Schritt 4, Task **W8-4** Schritt 4,
> W3-Block (`--check`-Zeile), W8-4 `Interfaces:`, DoD Punkt 2, Kopfblock. Vollständiger Abgleich
> mit Behandlungstabelle: **§17.9.4, „Vierte Korrekturrunde"**. **E-1…E-4 bleiben unentschieden**
> und liegen beim Auftraggeber; OQ1 bleibt **offen**, OQ2/OQ6/OQ8 **geschlossen**, OP-1
> **unberührt**. Ein **außerhalb** des Korrekturumfangs liegender Punkt (die
> `W3-BASELINE-STRICT`-Textpflicht in W4/W5) ist als **OFFEN** gekennzeichnet, **nicht** ausgeführt.
>
> **Rev. 0.4 — gesonderte Bestätigung (2026-09-26, extern).** Rev. 0.4 ist eine
> **Inhaltsrevision**: Sie führt neue normative Pflichten ein (verbindliche
> Commit-Titel-/Body-Konvention, Branch-Aufbewahrung als Scope-Aussage). Das Concept-Review
> von Rev. 0.4 endete deshalb mit `VERDICT: BLOCKED` (**F-1**) — die Normativität wurde ohne
> erneute User-Freigabe mit derselben Verbindlichkeitstiefe installiert, obwohl §15 `APPROVED`
> nur nach Concept-Review **und** User-Freigabe zulässt. **F-1 ist damit aufgelöst:** Rev. 0.4
> ist am **2026-09-26 durch den Nutzer ausdrücklich bestätigt**, über den Entscheidungsweg
> laut Plan Rev. 0.4, K1 (`main_chat`). **Worauf sich die Bestätigung bezieht:**
>
> - **unverändert:** der Umfang der Ausführungsmechanik **W0–W8** — der Freigabeumfang der
>   Erstfreigabe bleibt unberührt; keine Welle, kein AC/IC/NFA/Risiko wurde verschoben.
> - **neu bestätigt:** die in Rev. 0.4 aufgenommenen **Normativitätsaussagen** — die
>   verbindliche **Commit-Titel-/Body-Konvention** (§9.2 Punkt 2, R16-Mitigation) und die
>   **Branch-Aufbewahrung** als Scope-Aussage (§9.2 Punkt 4, „diese Spec schreibt weder
>   Löschung noch Aufbewahrung eines Branches vor").
> - **Bedingung der Bestätigung:** **A13** (Branch-Namensabweichung) und die
>   **W4/W5/W6-Serialität** (A14) sind als **offene, dokumentierte Abweichungen**
>   registriert — A13 in §13, A14 zusätzlich in **§17.8** mit Status **offen**.
>
> Die zuvor im Dokument selbst ausgerichtete Ausnahme („Inhaltsrevision ohne erneute
> Freigabe") ist damit **entfallen** — sie ist nicht mehr nötig, weil die Freigabe extern
> vorliegt. `status: APPROVED` besteht unverändert; die inhaltliche Revisionshistorie endet
> bei **Rev. 0.4**. (Konvention: `docs/specs/2026-09-13-stale-role-cleanup-design.md:39`,
> `docs/specs/2026-09-15-reference-standards-design.md:67` — beide führen die Freigabe als
> eigene Zeile, **ohne** Revisions-Bump; hier liegt sie zusätzlich als Rev. 0.4 vor.)
>
> **Zusätzlich am 2026-09-26 durch den Nutzer entschieden:** **OQ2**, **OQ6** und **OQ8** (§11.2).
> Alle drei sind damit **geschlossen** und nicht mehr als offene Frage zu führen; §16
> (Selbstreview Rev. 0.3) nennt OQ2/OQ6/OQ8 noch als offen — das ist der historische Rev.-0.3-Stand
> und bleibt als solcher stehen; maßgeblich ist §11.
>
> **Provider-agnostik ist Pflicht.** Kein neuer oder geänderter Codepfad verzweigt über ein
> Provider-Namensliteral. Provider-Unterschiede ausschließlich über Config-Keys /
> Capability-Flags (`config/ai-providers.yaml`, `.meta-config/project.yaml:159-169`).
>
> **Klassifikation (Master-Rule `spec-plan-workflow`):** **XL / Architectural** — die Spec
> berührt vier Modulgrenzen, migriert 4 Doku-Bäume, bricht eine bestehende Policy
> (`knowledge.py:112-114`) und verschiebt öffentliche Pfade. Produktions-Footprint
> (Code): 8 Dateien in `scripts/` + 2 Config-Dateien + 1 Schema-Datei; Doku-/Migrations-
> Footprint: ~65 Dateien (ausschließlich `git mv` + Marker-Regionen).

### Verifikations-Legende

| Marker | Bedeutung |
|---|---|
| **VERIFIED** | am 2026-09-26 im Working Tree gelesen; `Datei:Zeile` genannt |
| **VERIFIED-DESIGN** | aus dem freigegebenen Design übernommen und dort belegt |
| **HYPOTHESIS** | Annahme, vor Implementierung in der jeweiligen Welle zu prüfen |
| **REVIEWER-KORRIGIERT** | Reviewer-Angabe war selbst ungenau; korrigiert, Beleg in §17.2 |

### Revision

| Rev | Datum | Änderung | Autor |
|---|---|---|---|
| 0.1 | 2026-09-26 | Initiale Spezifikation aus `docs/specs/2026-09-25-repository-documentation-consolidation-design.md`; alle `scripts/lib/`-, `config/`-, `.meta-config/`-, `knowledge/`- und Root-Doku-Referenzen re-verifiziert; Modulaufteilung M1–M4; AC-01…AC-35; Trace-Matrix; R1…R13; OQ1…OQ7 | concept-specifier |
| 0.2 | 2026-09-26 | **Review-Überarbeitung (CHANGES_REQUESTED, 16/16 Findings behoben).** **K1** V1-Regel neu spezifiziert (2 Branches, Positiv-/Negativ-Fixture, AC-07/AC-08 ersetzt). **K2** F19 **gestrichen** — Tier-Presets = 5, `README.md:689` ist korrekt (Reviewer bestätigt). **K3** neuer Befund **F22** — DoD-Presets = 7, `README.md:688` ist Drift (Reviewer bestätigt). **K4** F14 erweitert — 8 Pipelines / 7 aktiv, `concept-driven-dev` fehlt in `README.md:479-489` (Reviewer bestätigt). **K5** Absenz-Default = **aus** für Writer **und** Checks (Präzedenz `knowledge.py:127`), `knowledge-engine`-Schreibverbot, Besitzregel für `docs/INDEX.md`; **Anzahl der brechenden Szenarien von 6 auf 3 harte Fehlschläge korrigiert** (§17.2). **M1** Hook-Zählung in zwei benannte Keys getrennt (11 / 17). **M2/M3** Trace-Matrix und W8-ACs repariert. **M4** F6 = vier Orte, Migrationen M-6/M-7 ergänzt, **F23/F24** erfasst. **M5** AC-29 entzirkelt (Stale-Quelle wandert mit der Langfassung). **M6** Restore-Pfad als **IC-24** spezifiziert, AC-35 entsprechend. **M7** R1 auf `docs/INDEX.md` ausgedehnt. **M8** Allowlist-Interaktion **analysiert statt vermutet** (verifiziert: `fnmatch` matcht den Basis-Pfad nicht). **N1–N3** Selbstwidersprüche korrigiert, OQ5/OQ7 als geschlossen markiert, `knowledge-indexer`-Kollision als R19. **Neu:** §12 Threat Model, **R14** (unabhängige Sollwert-Fixture → IC-23 + AC-36/AC-37), **R15** (Schema → M-11), **R16** (PR-/Branch-Kollision), **R17** (Downstream-Asymmetrie), **R18** (Auto-Commit-Interaktion), **R20** (V2-ERROR vs. menschliche Doku-Erstellung), **OQ8** (Index-Regenerierung), **OQ9** (zwei Beispiel-Configs), **§17** (Review-Auflösung + eigene Befunde), AC-01…AC-41, F1…F25 (F19 gestrichen), M-1…M-13, R1…R20, NFA-11, IC-23/IC-24 | concept-specifier |
| 0.3 | 2026-09-26 | **Re-Review-Überarbeitung (CHANGES_REQUESTED, 8/8 Findings + 1 Gegenkorrektur behoben).** **NEW-1** `DOCS_HOOK_SCRIPT_FILES_COUNT == 17` **entfällt** (die 17 zählen `hooks/**`, nicht `hooks/1-generic/`); neu `DOCS_HOOKS_1GENERIC_COUNT == 9` mit der Regel `hooks/1-generic/*.sh` minus `*-impl.sh`, exklusiv für `README.md:696`; `DOCS_HOOKS_COUNT == 11` bleibt unverändert exklusiv für `README.md:501`. **NEW-2** F22 um `README.md:381` erweitert (zweite Falschzahl: Überschrift „6 presets" **und** fehlende `concept-driven`-Zeile). **NEW-3** §1/§1.2-Zählung neu gerechnet: **11** falsche Zahlen (10 in `README.md`, 1 in `ARCHITECTURE.md:3`), `llms.txt:5` ist Prosa, keine Zahl. **NEW-4** Sollwerte einheitlich **elf**. **NEW-5** §9.2-Wellensummen korrigiert (W1: **10**, W3: **14**). **NEW-6** §16-Liste der AC ohne V-Check vervollständigt (**18**). **NEW-7** AC-38-Begründung für `51:32` auf Absenz-Default (IC-13/IC-22) umgestellt. **NEW-8** AC-02 ohne `xfail` Snapshot **durchsetzbar**; Zahlen-Sollwerte liegen ausschließlich in IC-23/AC-36. **Gegenkorrektur** §17.2: **0** Szenarien brechen unter der spezifizierten Abschirmung, **3** in der naiven Variante (nur als Begründung der Abschirmung genannt, kein Arbeitsauftrag — NG-10). **Neu:** NF-9 (Falschzahlenzählung), NF-10 (Sollwertzahl), NF-11 (`README.md:381` als Beleg des Designs), **NF-12** (`HOOK_EXCLUDED_SUFFIXES` schrieb `"_impl.sh"` statt `"-impl.sh"` — hätte `DOCS_HOOKS_COUNT` auf 13 statt 11 laufen lassen; im selben Codepfad wie NEW-1 gefunden und korrigiert) | concept-specifier |
| **0.4** | 2026-09-26 | **Ausführungskorrektur der Branch-/PR-Strategie (offener Punkt OP-1) — drei Normativitätsstellen, keine Design-Änderung, keine inhaltliche Neuerfindung.** **OP1-1** §9.2, **W0-Zeile**: „**ein Branch pro Welle** (`chore/docs-consolidation-w<N>`)" → **ein** Wellen-Branch `feat/repository-documentation-consolidation-main` (Basis `origin/main`) mit **einem** PR gegen `main`; Wellen-Zuordnung über die **Wellenkennung im Commit-Titel**. **OP1-2** §9.2-Absatz „PR-/Branch-Kollision" vollständig neu gefasst (Ein-Branch-/Ein-PR-Regel, Commit-Titel-Konvention inkl. `… W<N> complete` und Task-ID im Commit-Body, Merge-Regel `git mv`-Wellen W4/W5/W6 zuerst, sequenzielle W1→W8, dokumentierter Bestand des überholten Vor-Branches, Rebase gegen `origin/main` vor dem PR-Merge). **OP1-3** **R16-Mitigation** (§12.2): „Ein Branch **pro Welle** …, gestapelte PRs in Reihenfolge" → Reihenfolge- und Merge-Regel statt Branch-Anzahl. **OP1-4** §15 Trace-Anker um den Rev.-0.4-Ausführungskorrektur-Anker ergänzt. **OP1-5** §16 um zwei Abgrenzungszeilen (Rev.-0.4-Grenze, Ownership-Grenze Rev. 0.4) ergänzt. **OP1-6** §17.6 als vollständiger Korrektur- und Beleg-Abschnitt angelegt. **Unverändert:** AC-01…AC-41, IC-01…IC-24, NFA-01…NFA-11, R1…R20 (R16 **nur** im Lösungsansatz), F1…F25, M-1…M-13, NG-1…NG-11, FI-1…FI-10, OQ1…OQ9, W0…W8, §9.1, §9.2-Welleninhalt und AC-Mengen, §3–§12 im Übrigen. **§13 umfasst 14 Abweichungen** (A1…A12 unverändert; **neu in Rev. 0.4: A13** Branch-Namensabweichung gegen das Design und **A14** offene Abweichung W4/W5/W6-Serialität — das Design verlangt an keiner Stelle gestapelte PRs, die **Zahl** der Branches stimmt, der **Name** nicht). **Freigabe:** Rev. 0.4 am **2026-09-26 durch den Nutzer bestätigt** (Entscheidungsweg laut Plan Rev. 0.4, K1 → `main_chat`) — Auflösung des Review-Blocks `VERDICT: BLOCKED` (F-1) in **§17.7**; die zuvor im Dokument ausgerichtete Ausnahme („Inhaltsrevision ohne erneute Freigabe") ist **entfallen**. **Keine neue ID, keine neue Welle, kein neues Risiko.** Quelle der Korrektur: `docs/plans/2026-09-25-repository-documentation-consolidation.md` (Rev. 0.3, K1/K8/K9, Global Constraints, Task W0-2) und `docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md` §7.1/§7.2. **OP-1 wird in Plan und Records erst durch einen Folgeschritt formal geschlossen**; Concept-Review über Rev. 0.4 **ist erfolgt** (2026-09-26, `VERDICT: BLOCKED`, Befund **F-1**), die **Nutzer-Bestätigung** liegt vor; Auflösung und Wortlaut in **§17.7**, siehe §17.7. | concept-specifier |
| **0.5** | 2026-09-26 | **Gate-Präzisierung W2/W3 und Schließung zweier Eigentümerlücken (Katalog K13…K17, Volltext §17.9) — plus zweite Korrekturrunde desselben Revisionsstandes (Review `CHANGES_REQUESTED`, 15/15 Findings RVW-1…RVW-15 behoben, §17.9.4).** **Erste Runde:** **K13** W2-Gate auf die reale V1-Registrierung/Severity umgestellt (B-2/E-11) — zwei getrennte, beobachtbare Zustände (nach W2-1 / nach W2-7), gezählt über `--json` statt über den repo-globalen Exit-Code. **K14** W3-Gate auf den Spec-Scope begrenzt (B-1) — §10-Dateiscope plus **getrenntes** Doku-Gate; repo-globales `--strict == 0` als **Altbestand-Baseline** getrennt ausgewiesen. **K15** `scripts/lib/consistency/report.py` erhält **Ownership** (B-5/E-15, Task W2-7, Abnahmekriterium F1-PROMOTION). **K16** Abdeckungslücke der Suppressionsregel 3 als **benannte, terminierte** Aufgabe (B-4/E-14, W2-1 Schritt 4) mit Reihenfolgebindung an W3-4. **K17** Abschnitts-/Zählungsanker im Ledger nachgeführt (K12-Logik). **Nachmessung §17.9.1:** die Auftragsprämisse „V1 emittiert ERROR" ist **widerlegt** (V1 emittiert WARNING — `docs.py:359`, `:314-326`, `.meta-config/project.yaml:398-399` — und ist im Runner **nicht registriert**, `consistency-check.py:52-56`, gepinnt in `tests/test_doc_facts.py:2403-2422`). **Zweite Runde (RVW-1…RVW-15):** **RVW-1** Doku-Aggregat `docs-findings: 0` ist **dauerhaft** unerreichbar (V7 rot bis W5-3, V3 bis W8-2, V2 bis W3-6, V9 **nie** — 179 geduldete WARNINGs, FI-10) ⇒ **§10, `--strict`-Punkt, Unterpunkt 5 neu**: check-spezifische Kriterien mit **Termin** und **Owner** je V-Check. **RVW-2** drei weitere unerreichbare `consistency-check.py → 0`-Zeilen in W2 auf ein Zähl-Kriterium umgestellt. **RVW-3** die **fünf Wellenblock**-Zeilen W4–W8 auf die Scope-Kriterien umgestellt, Task-Zeilen unter der Geltungsregel mit ausdrücklicher Wellenabschluss-Relevanz. **RVW-4** die K16-Reihenfolgebindung als **echte Vorwärts**kante **`W2-1 → W3-4`** im DAG (die frühere Zyklus-Begründung war **falsch**). **RVW-5** Normativitätsaussage präzisiert: „keine neue normative Pflicht" war unhaltbar → „keine Pflicht **jenseits** des am **2026-09-26** beauftragten Korrekturumfangs" (Auftrag: A2A-Envelope vom 2026-09-26, Korrekturen 1–5, ausdrückliche Weisung `status: APPROVED` beizubehalten). **RVW-6** diese 0.5-Zeile + Rev.-0.5-Anker in §15 nachgezogen. **RVW-7** falscher Verweis „§12.2 R4" → **§12.1 R4** (R4 enthält keine Reihenfolgeaussage). **RVW-8** Zählherleitung im Plan-Kopf auf die L-1-Formel umgestellt. **RVW-9** Geltungsregel auf Abschnittsanker und tatsächlichen Zeilenbestand korrigiert. **RVW-10** Self-Review-Beispiel als historisch markiert. **RVW-11** W2-1 `Interfaces:` nennt die eingegrenzte Fassung der Suppressionsregeln. **RVW-12** K13-Kriterium auf **Zählwert** statt Exit-Code; alle neuen `--json`-Kommandos `sys.exit`-frei. **RVW-13** Global Constraints des Plans als historischer Rev.-0.4-Stand markiert (**OP-1 bleibt offen**). **RVW-14/15** zwei konstruktionsbedingte Aussagen als **Dokuzeilen, nicht als Prüfkriterien** geführt. **Unverändert:** AC-01…AC-41, IC-01…IC-24, NFA-01…NFA-11, R1…R20, F1…F25, M-1…M-13, NG-1…NG-11, FI-1…FI-10, OQ1…OQ9 (**OQ1 offen**), W0…W8, der normative **Pflichtumfang** von §10 Punkt 1, `status: APPROVED`, `approved: 2026-09-26`, der Ausführungsfreigabeumfang. **Keine** neue ID, **kein** Revisions-Bump innerhalb Rev. 0.5, **keine** neue Task-ID | concept-architect |
| **0.6** | 2026-09-27 | **Umsetzung zweier bereits getroffener Nutzerentscheidungen — U-1 (Modul-Split) und U-2 (AC-30-Verengung). Volltext §17.10, Katalog K18…K24; Korrekturrunden K25…K45 (§17.10.5, Runde 1 = K25…K40, Runde 2 = K41…K45; **wahrer Endstand K45**).** **U-1:** `scripts/lib/consistency/docs.py` wird zur **Fassade** und re-exportiert alle nach außen sichtbaren Namen rückwärtskompatibel; die neun V-Checks und die drei Altchecks werden **je genau einem** von vier neuen Familienmodulen zugeordnet — `docs_links.py` (V3, V4, `check_sync_cli_docs`, `check_ui_help_mappings`), `docs_freshness.py` (V1a/V1b, V5, V6), `docs_wiki.py` (V7, V8), `docs_index.py` (V2, V9) — **jedes < 600 Zeilen** (**K18**, Modulgrenzen **§4.1** mit expliziter Abgrenzung zu den **Fach**-Modulen M1–M4, **K19**). **U-2:** **AC-30** auf **`README.md` + `llms.txt`** verengt; die **25** toten relativen internen Links unter `docs/**` werden als **Follow-up `F-DOCS-LINKS-2026-09-27`** (Owner `developer`, Termin **2026-10-11**) geführt — **kein** AC, **keine** Stillschweigung (**K22**). **Weigerungsnachweis** in §17.10.2: die Verengung trägt, weil die **2** verbleibenden Findings in `README.md:722`/`:723` liegen und der bestehende Task **W8-2** sie behebt — **kein** zusätzlicher Task nötig. **Faktenkorrekturen:** V3-Fundstellen sind `README.md:722`/`:723`, **nicht** `:721-724` (`README.md:721` `howto/` und `:724` `howto/configs/` existieren) (**K23**); `docs/REQUIREMENTS.md:21` ist **kein** V3-Finding — die Zeile nennt Backtick-Pfade in einer Tabellenzeile und V3 matcht nur Link-Syntax (`V3_INLINE_LINK_RE`, `V3_REFERENCE_DEF_RE`, `V3_HTML_HREF_RE`) — die Trace-Matrix-Zeile `| AC-30 | W8 | … |` ist auf `README.md:722-723` berichtigt; die F15-Zeile nennt `docs/REQUIREMENTS.md:21` nur noch als **manueller** Befund. **V7-Baseline 10 → 11** (`knowledge/wiki`, **11** Seiten mit `type: "Architecture"`, Baseline-Messung 2026-09-27) (**K24**). **Neu:** §4.1 (Modulgrenzen), §17.10 (Volltext, Weigerungsnachweis, Follow-up-Register, Zyklenprüfung-/Fail-closed-Klausel). **Plan-Seite:** neuer Task **W2-0** (Modul-Split, verhaltensneutral), korrigierter W2-DAG mit **echten write-set-disjunkten** Kanten, neue Testdateien `tests/test_doc_{wiki,freshness,index}.py`, korrigierte Wellen-Gate-Kommandos, Rollback-Erweiterung. **Unverändert:** AC-01…AC-29 und AC-31…AC-41, IC-01…IC-24, NFA-01…NFA-11, R1…R20, F1…F25, M-1…M-13, NG-1…NG-11, FI-1…FI-10, OQ1…OQ9 (OQ1 **offen**, OQ2/OQ6/OQ8 geschlossen), W0…W8, das System-Design, `status: APPROVED`, `approved: 2026-09-26`, kein Produktionscode | concept-architect |

| **0.7** | 2026-09-27 | **Umsetzung von vier bereits getroffenen Nutzerentscheidungen — E-5, E-6, E-7, E-8. Volltext §17.11, Katalog K54…K58.** **E-5:** V4 `check_readme_docs_index` (Check-ID `docs.readme_index`) wird vom Scope „alle 205 nicht-Archiv-`docs/**.md` gegen `README.md`" auf den **README-Index-Scope** begrenzt: die Prüfung liest die `##`-Region `Documentation Index` in `README.md` und verlangt, dass jede dort **deklarierte** `docs/`-Kategorie (a) existiert und (b) mindestens **einen** `docs/<kategorie>/…`-Link in der Region trägt. **IC-05-Pin unverändert:** Check-ID, Severity ERROR, `file` = `README.md`, **Signatur einargumentig** `(root: Path) -> list[Finding]` (**K59**). **193** nicht im README verlinkte `docs/`-**Seiten** → **Follow-up `F-DOCS-README-INDEX-2026-09-27`** (Owner `developer`, Termin **2026-10-11**), **kein** Termin 0 in W0–W8 (**K55**, §17.11.2, Register §17.11.3); Herleitung `205 − 12`, Nachweis = **Issue-Liste + once-count außerhalb V4** (**K60**). **E-6:** neuer Plan-Task **W2-8** „Volltests entkoppeln" mit eigenem `Files:` (`tests/test_knowledge_engine.py`, `tests/test_sharkord_service_name_migration.py`), Agent `senior-developer`, Position **vor W2-7**; er löst die Kopplung beider Tests an den repo-globalen `--validate`-Exit-Code, der nach §10 **planmäßig rot** ist (**K56**). **E-7:** V5 wandert aus `docs_freshness.py` (gemessen **592** Zeilen nach W2-5) in das neue Modul **`scripts/lib/consistency/docs_freshness_v5.py`**; Größenfolge `592` (Reserve **8**) + **≈55–70** (V5), **beide < 600**; Zuordnung bleibt **12/12 disjunkt**, jetzt auf **5** Module (**K56**). **E-8:** `TASK_HEADER_RE` wird um die Wellen-/Task-Header-Form erweitert (Definition `scripts/lib/plan_identity.py:27-30`, Konsument `scripts/lib/plan_ledger.py:25`/`:71`/`:133`), `normalize_task_id` lernt `W<n>-<k>`; neuer Plan-Task **W2-9** in **Phase 0** von W2 ⇒ **Ledger-Writer einsetzbar ab W2-9** (die K53-Interim-Regel endet) (**K57**, **K58**). **Neu:** §17.11 (Volltext + Katalog + Register-Fortsetzung + Zyklenprüfung), §4.1 (fünftes Modul), IC-05 (V4-Zeile), §9.2 (W2-Zeile), §4 (Testdatei `tests/test_doc_freshness_v5.py`). **Zählung:** Tasks **48 → 50**, Checkboxen **199 → 207** (`[x]` **59**, `[ ]` **148**), Herleitung 44 × 4 + 5 × 5 + 1 × 6. **Unverändert:** `status: APPROVED`, `approved: 2026-09-26`, AC-01…AC-41, IC-01…IC-24, NFA-01…NFA-11, R1…R20, F1…F25, M-1…M-13, NG-1…NG-11, FI-1…FI-10, OQ1…OQ10 (OQ1, OQ10 bleiben **offen**), W0…W8, E-1…E-4 (**offen**), E-01…E-15, B-1…B-5, OP-1, keine Produktions- oder Teständerung in dieser Revision | concept-architect |
| **0.8** | 2026-09-29 | **agent-meta-Ausnahme im KE-Vorrang-Gate — NEUER, ZUR USER-FREIGABE AUSSTEHENDER UMFANG. Volltext §17.12, Katalog K-1…K-5 (§17.12.1), Entscheidungsvorlagen E-9…E-13 (§17.12.2), DECISION-1…DECISION-4 (§17.12.3), Nachweis-/Testakzeptanz (§17.12.4).** **Auslöser (gemessen):** W3-6 scheitert an **einer** Codezeile — `scripts/lib/doc_renderer.py:702-703`; `resolve_index_mode()` löst in agent-meta `"knowledge-engine"` auf (`.meta-config/project.yaml:69` + `:77` + `:15`), der KE-Vorrang-Zweig blockiert damit jeden `docs/INDEX.md`-Schreibvorgang. `docs/INDEX.md` existiert **nicht** (Glob ohne Treffer), und V2 (`scripts/lib/consistency/docs_index.py:180-211`) meldet deshalb **jede** Seite unter `docs/` als ERROR. **Vorentscheidung des Nutzers (nicht neu bewertet):** explizite agent-meta-Ausnahme; die KE bleibt für Consumer autoritativ. **Inhaltliche Pflichtänderungen P-1…P-5 (zur Freigabe ausstehend):** IC-13 Zeile 2 bedingt, IC-15 um die Neuanlage-Bedingung ergänzt, IC-22-Tabelle siebter Key + „alle sieben Keys" (+ **P-3-E** AC-39 auf den gemessenen Property-Stand), AC-21 bedingt, R7 um einen dritten Hebel. **Neu:** IC-25 (Key `docs-consolidation.index-owner`, zweiwertiges Enum `auto` \| `docs-consolidation`, Fail-closed-Zweig **vor** der KE-Prüfung, Entscheidungsfolge als Vertrag) und IC-26 (Begrenztheitsvertrag: Wirkung ausschließlich auf `docs/INDEX.md`, `resolve_index_mode()` unberührt, Besitzregel und `is_file_index_skeleton()` unberührt, `dry_run`-Vertrag unberührt, Consumer per Konstruktion unerreichbar, kein Provider- und kein Projektname im Code); AC-42…AC-46 (Override schreibt / Absenz blockiert / unbekannter Wert fail-closed / Override hebt `skeleton` und Besitzregel **nicht** auf / `dry_run` schreibt nicht / Schema-Enum). **Korrekturen ohne Freigabebedarf K-1…K-5:** zwei Docstrings (`doc_renderer.py:669-672`, `tests/test_doc_renderer.py:3209-3223`), ein Zählkommentar (`tests/test_docs_consolidation_migration.py:42`), zwei veraltete Zeilenanker `spec_plan_scaffold.py:62-68` → **`:115-121`** und `:40-44` → **`:80-97`**; `doc_renderer.py:685-686` bleibt **wortgleich**. **Explizit nicht geändert:** `status: APPROVED`, `approved: 2026-09-26`, der freigegebene Umfang **W0–W8**, §17.10/§17.11, E-1…E-8. **Unverändert:** IC-01…IC-24, AC-01…AC-41 (bis auf AC-21/AC-39), NFA-01…NFA-11, R1…R20 (bis auf R7), F1…F25, M-1…M-13, NG-1…NG-11, FI-1…FI-10, OQ1…OQ10, V1…V9, W0…W8, Taskzahl **50** — **keine** bestehende ID umnummeriert oder gestrichen, **keine** neue Task-ID, **kein** neuer V-Check | concept-specifier |
| **Freigabe** | **2026-09-26** | **User-Freigabe** (Nutzer, über `main_chat` an den `orchestrator`); formalisiert durch `documenter`. Frontmatter `status:` auf `APPROVED` gesetzt. **Freigabestand:** Concept-Review **Runde 1** (2026-09-26) `CHANGES_REQUESTED`, **5 kritische Befunde** (K1…K5) → Rev. 0.2; Re-Review **Runde 2** (2026-09-26) `CHANGES_REQUESTED` mit **0 kritischen Befunden**, `RESIDUAL_BLOCKERS: Keine`, `PLAN_READINESS: Ja` → Rev. 0.3 mit **8 behobenen** Findings (NEW-1…NEW-8) + Gegenkorrektur. **Umfang:** Freigabe der **Ausführung W0–W8**. **Zusätzlich entschieden (Nutzer, 2026-09-26):** OQ2 (`llms.txt` = **Hybrid**), OQ6 (**tracked**) und OQ8 (Regenerierung über Sync/Validator) → nach §11.2 verschoben. **Keine inhaltliche Änderung** an IC/AC/Risiken — die Freigabe ist eine Statuszeile, kein Revisions-Bump (Konvention: `docs/specs/2026-09-13-stale-role-cleanup-design.md:39`, `docs/specs/2026-09-15-reference-standards-design.md:67`). **Datumsabweichung:** Nutzer nannte 2026-09-25 (Datum der Anfrage); der Freigabevermerk trägt das **Freigabedatum 2026-09-26**. **Nach der Freigabe (rev. 0.4, 2026-09-26):** die Ausführungskorrektur der Branch-/PR-Strategie (§17.6) — **ohne** Änderung an IC/AC/Risiken; die dort zunächst im Dokument ausgerichtete Ausnahme („ohne neue Freigabe") ist **durch die nachfolgende Nutzer-Bestätigung ersetzt**, siehe nächste Zeile | documenter |
| **0.8 — erste Korrekturrunde (RVW8-1…RVW8-10)** | 2026-09-29 | Concept-Review vom 2026-09-29 über Spec Rev. 0.8: `VERDICT: CHANGES_REQUESTED`, **10 Findings** (0 kritisch, 5 major, 5 minor, 0 info). **Alle 10 inhaltlich behoben**, **kein Revisions-Bump** — Rev. bleibt 0.8, `status: APPROVED` / `approved: 2026-09-26` unverändert, `pending-approval:` besteht fort. Katalog **K77…K86** (§17.12.6; **K77** war im ersten Wurf K61 — korrigiert in der zweiten Korrekturrunde, s. u.). **Betroffene Stellen:** K-3/T-4/V-D4 (Zählkommentar `:42-44` **existiert** — Fehlmessung des Read-Tools, per Grep widerlegt), T-3 **zweite** Zeile `_IC22_ABSENCE_DEFAULTS`, Trace-Matrix §9.1/§9.2 + Zählsatz (W3 14 → **19**), **V-D7** (T-8 → T-3 → T-5, alle W3-6) + E-13a zurückgenommen, §12.3 (g) auf alle vier Fragen beantwortet inkl. Kopier-Pfad (Ziffer sechs → sieben), IC-25/IC-13/§12.3 (Schema ist **best-effort**, `config.py:342`/`:388`), AC-42 (d) Anker geteilt, **V-D1** Anker-Auswahlregel + vollständiges Inventar, **V-D2** um AC-22/§13 A4 ergänzt, AC-39 Belegquelle, **V-D6** (Planlücke W3-7/`sources`). **Unverändert:** P-1…P-5 (inkl. **P-3 (e)**) zur User-Freigabe ausstehend, E-9…E-13 und OQ1 offen, Umfang W0–W8, keine Umnummerierung bestehender IDs, kein Produktionscode | concept-architect |
| **0.8 — zweite Korrekturrunde (RVW9-1…RVW9-9)** | 2026-09-29 | Concept-Review vom 2026-09-29 über Spec Rev. 0.8 (korrigierte Fassung): `VERDICT: CHANGES_REQUESTED`, **10 Findings** (0 kritisch, **2 major**, **7 minor**, 1 info). **Alle 10 behoben**, **kein Revisions-Bump** — Rev. bleibt 0.8, `status: APPROVED` / `approved: 2026-09-26` unverändert, `pending-approval:` besteht fort. **Katalog K77…K86** — RVW9-1 hat den ersten Wurf **K61…K70** (zehnfach belegt) umnummeriert, Vorspann „ab K77; **K1…K76** bleiben unberührt", maßgebliche Obergrenze **K76** (Plan-Legende, **gemessen**) dort genannt; **RVW10-1** zieht den Katalog ein drittes Mal nach, weil die Zwischenlage **K76…K85** mit dem Plan kollidierte (`K76` dort belegt); **keine** der zehn bisherigen Bedeutungen gestrichen. **RVW9-2:** **V-D8** neu registriert — Plan Rev. 0.7 kennt Rev. 0.8 nicht (W3-6 ohne T-3/T-5/T-7/T-8/AC-42…AC-46, W1-9 abgeschlossen mit der Fehlzählung „sechs Properties", **kein** `pending-approval:` im Plan-Frontmatter), die W3-6-Akzeptanz nach §17.12.4 ist **vom heutigen Plan aus unerfüllbar**; der **forderliche Plan-Delta** ist in **§17.12.5 (V-D8-Uebergabe)** präzise benannt und wird **erst nach** User-Freigabe ausgeführt — dieser Durchgang ändert den **Plan nicht**. **RVW9-3…RVW9-9 + info:** T-4-Ordinal „sixth" ⇒ „seventh", **E-13c** (Kopier-Pfad) als dritte Optionenzeile + Q4-Verweis §17.12.3 ⇒ §12.3, **P-3 (e)** als fünfte P-Zeile geklärt, Testname `::test_schema_declares_the_absence_defaults`, K-78-Verortung, V-D1-Selbstverweis `:1449-1450` ⇒ `:1465-1466`, W1-10-Step-2-vs-T-7-Reihenfolge, §9.2-Fußnote ¹ zur AC-39-Zählkonvention. **Unverändert:** P-1…P-5 (inkl. P-3 (e)) **inhaltlich** zur User-Freigabe ausstehend, **E-9…E-13 einschließlich der neuen Optionenzeile E-13c und OQ1 offen**, Umfang W0–W8, **keine** neue IC-/AC-/Task-/Wellen-/V-Check-ID, **keine** Umnummerierung bestehender IDs, kein Produktionscode | concept-architect |
| **0.8 — dritte Korrekturrunde (Runde 10, RVW10-1…RVW10-3)** | 2026-09-29 | **Endverifikation der zweiten Korrekturrunde** über Spec Rev. 0.8; `VERDICT: CHANGES_REQUESTED`, **3 Findings** (1 major, 1 minor, 1 info). **Alle 3 behandelt**, **kein Revisions-Bump** — Rev. bleibt 0.8, `status: APPROVED` / `approved: 2026-09-26` unverändert, `pending-approval:` besteht fort. **RVW10-1 (major):** der zweite Wurf des Korrektur-Katalogs (**K76…K85**) war **dokumentübergreifend** kollidierend — `K76` ist in der **Plan-Legende** belegt (Plan `:536`) — der Katalog steht jetzt endgültig auf **K77…K86**, und die im Vorspann genannte maßgebliche Obergrenze **K76** ist dort festgehalten. **RVW10-2 (minor):** der in der zweiten Runde eingesetzte Ersatzanker für V-D1s Selbstverweis war selbst falsch und ist auf den **gemessenen** Träger **`:1487-1488`** berichtigt. **RVW10-3 (info):** ein zweiter Träger derselben Ordinal-Formulierung geprüft und registriert (`tests/test_doc_renderer.py:1090`, **unverändert**). **Bilanz der zweiten Runde laut Runde 10:** 1 major **vollständig** behoben, 1 major **teilweise** (Restfehler → RVW10-1), 6 minor **vollständig** behoben, 1 minor **teilweise** (Restfehler → RVW10-2), 1 info behoben. **Kein technischer Blocker** — RVW10-1 und RVW10-2 sind Dokumentations-Hygiene. **Unverändert:** P-1…P-5 (inkl. **P-3 (e)**) **inhaltlich** zur User-Freigabe ausstehend, **E-9…E-13 einschließlich E-13c und OQ1 offen**, Umfang W0–W8, **keine** neue Pflicht, **keine** neue oder umnummerierte ID, kein Produktionscode. **Zusammengeführte Historie der Concept-Review-Runden zu Rev. 0.8** (drei Zeilen, **keine** ersetzt oder gestrichen): Runde 8 / K77…K86 → Runde 9 / RVW9-1…RVW9-9 → **Runde 10 / RVW10-1…RVW10-3, diese Zeile**. **Nachsatz, additiv:** nach Abschluss dieser Runde wurde das Vorhaben **pausiert** — Pause-Datum **2026-09-26**, Record `docs/plans/2026-09-25-repository-documentation-consolidation-pause.md` (`status: PAUSED`, `revision: 0.1`); Rev. 0.8 bleibt **nicht freigegeben**, `pending-approval:` besteht fort | concept-architect |
| **Freigabe (Rev. 0.4)** | **2026-09-26** | **Nutzer-Bestätigung der Rev. 0.4** (Nutzer, über `main_chat` an den `orchestrator`; Entscheidungsweg laut Plan Rev. 0.4, K1); formalisiert durch `documenter`. **Anlass:** das Concept-Review von Rev. 0.4 endete mit `VERDICT: BLOCKED` (**F-1**) — neue normative Pflichten (verbindliche Commit-Titel-/Body-Konvention, Branch-Aufbewahrung als Scope-Aussage) waren ohne erneute User-Freigabe mit derselben Verbindlichkeitstiefe installiert worden. **Bezug der Bestätigung:** unverändert der Umfang der Ausführungsmechanik **W0–W8**; **neu bestätigt** die in Rev. 0.4 aufgenommenen Normativitätsaussagen. **Bedingung:** **A13** und die **W4/W5/W6-Serialität** (A14) sind als **offene, dokumentierte Abweichungen** registriert (§13, §17.7, §17.8). **Kein** Revisions-Bump — Rev. bleibt 0.4 | documenter |
| **0.5 — dritte Korrekturrunde (RVW2-1…RVW2-14)** | 2026-09-26 | Concept-Review vom 2026-09-26 über Spec + Plan Rev. 0.5: `VERDICT: CHANGES_REQUESTED`, **14 Findings** (2 Blocker, 4 Major, 7 Minor, 1 Info). **Alle 14 behandelt**, **kein Revisions-Bump**, `status: APPROVED` und `approved: 2026-09-26` unverändert. **Betroffene Stellen:** §6(b) (Präzisierung **zurückgestellt**, E-3), §10 Aufzählungspunkt `--validate` (Mechanik + **Terminierung** von `--validate`), §10, `--strict`-Punkt, Unterpunkt 5 (a: **Präsenzregel statt Registrierungszahl**; V9 **ohne Sollwert**; Verschlechterungs-Ausnahme), §10 `TEST_COMMANDS`-Punkt (Spannungslage dokumentiert, **E-4**), §11.1 OQ9 (Ergebnis-Ort präzisiert, **ohne** OQ9 zu entscheiden), IC-05 (V9-Hinweis), IC-22/M-11-Hinweis, FI-10, §17.9.3, §17.9.4 (Normativitätstabelle **(vii)–(x)**, Behandlungstabelle RVW2-1…RVW2-14, Entscheidungsvorlagen **E-1…E-4**), Revisionszeile 0.5, Frontmatter `approved-scope`. **Vier Entscheidungsvorlagen offen** (E-1 DoD-Punkt-2-Bestätigung, E-2 V9-Schwelle als Config-Key, E-3 §6(b)-`--check`-Halbsatz, E-4 `TEST_COMMANDS`-Punkt) — **keine** wurde eigenmächtig entschieden. **Unverändert:** AC-01…AC-41, IC-01…IC-24, NFA, R1…R20, F1…F25, M-1…M-13, NG-1…NG-11, FI-1…FI-10, OQ1…OQ9 (OQ1 **offen**, OQ2/OQ6/OQ8 geschlossen), W0…W8, 47 Tasks, **keine** neue Task-ID, kein Produktionscode | concept-architect |
| **0.5 — vierte Korrekturrunde (RVW3-1…RVW3-10)** | 2026-09-26 | Concept-Review vom 2026-09-26 über Spec + Plan Rev. 0.5: `VERDICT: CHANGES_REQUESTED`, **10 Findings** (0 Blocker, 6 Major, 4 Minor). **Alle 10 behandelt**, **kein Revisions-Bump** — dieselbe Korrekturrunde; `status: APPROVED`, `approved: 2026-09-26` und `revision: 0.5` unverändert. **Betroffene Stellen:** §10, Aufzählungspunkt `--validate` und `--strict`-Punkt, Unterpunkt 5 (**RVW3-6**: Obergrenze wird Plan-Protokoll, **kein** Spec-Sollwert; **RVW3-9**: benannte statt gezählte Anker), §10-Unterpunkte 5/6 (Ankerpräzisierung), FI-10 (Anker), §15-Trace-Anker, §16-Coveragezeile, §17.9.3, §17.9.4 (Normativitätstabelle (vii)/(ix)/(x), Behandlungstabelle RVW3-1…RVW3-10, Entscheidungsvorlagen **E-1…E-4** mit **Frist**-Spalte), Revisionszeile 0.5, Frontmatter `approved-scope`, Kopfblock. **Plan-Seite:** `W-VALIDATE-ROT`, Tasks W4-3/W5-2/W8-4, W3-Block, DoD Punkt 2. **Gestrichen:** die Nennung „§16 (Tabellenumfang)" in der Zeile der dritten Runde (**RVW3-10**) und der Spec-Nachtrag der V9-Obergrenze in W8-4 Schritt 4 (**RVW3-6**). **Als OFFEN gekennzeichnet, nicht ausgeführt:** die `W3-BASELINE-STRICT`-Textpflicht in W4/W5 — sie steht nicht in der Normativitätstabelle und ist vom beauftragten Korrekturumfang **nicht** gedeckt. **Unverändert:** AC-01…AC-41, IC-01…IC-24, NFA, R1…R20, F1…F25, M-1…M-13, NG-1…NG-11, FI-1…FI-10, OQ1…OQ9 (OQ1 **offen**, OQ2/OQ6/OQ8 geschlossen), W0…W8, 47 Tasks, **194 / 40 / 154** Checkboxen, **keine** neue Task-ID, **E-1…E-4 unentschieden**, OP-1 unberührt, kein Produktionscode | concept-architect |

---

## 1. Problem / messbare Baseline

Die agent-meta-Dokumentation ist an mehreren Stellen gewachsen, ohne dass eine Stelle die
andere ersetzt: eine **fünffache Architektur-Doku**, eine **vierfache Guide-Führung** (Rev. 0.1
nannte drei, M4), **vier Spec/Plan-Bäume** ohne dokumentierte Abgrenzung und **~190
`.md`-Dateien unter `docs/`** (≈ 190, **HYPOTHESIS** — die exakte Zahl wird erst durch
`DOCS_DOCS_FILE_COUNT` belegbar) ohne Index. Gleichzeitig ist jede manuell gepflegte Zahl in
`README.md` nachweislich falsch oder widersprüchlich: **10** Stück (F1, F2, F3 ×2, F4, F14 ×3,
F22 ×2) plus **1** in `ARCHITECTURE.md:3` (F4, zweite Fundstelle) = **11**. Der Zustand ist nicht
„ungenau", er ist **strukturell drift-anfaellig**: es gibt keine Maschine, die eine Zahl in
`README.md` mit der Quelle vergleicht — und in Rev. 0.1 gab es auch keine Maschine, die die
**Formel** hinter der Zahl prüft, weshalb drei falsche Zahlen unentdeckt blieben (§12.3, R14).

> **Rev. 0.3 — Zählung nachgerechnet (NEW-3).** Rev. 0.2 schrieb „10 (F1, F2, F3 ×2, F4, F14 ×3,
> F22) plus 2 in `llms.txt`"; die Aufzählung ergab **9**, und `llms.txt` enthält **keine**
> Zahl. Korrigiert auf **11 = 10 (`README.md`) + 1 (`ARCHITECTURE.md:3`)**, mit den beiden
> Änderungen aus NEW-2 (F22 hat jetzt **zwei** Fundstellen) und der Aufnahme von
> `ARCHITECTURE.md:3` als zweiter F4-Fundstelle. `llms.txt:5` („Claude Code, Gemini/Antigravity,
> Opencode, Continue, GitHub Copilot, Mammouth Code") listet 6 von 9 Providernamen
> (`config/ai-providers.yaml:1` + Blöcke `:2, :98, :172, :249, :316, :369, :434, :493, :545`) —
> das ist eine **inhaltliche** Lücke wie F14s fehlende `concept-driven-dev`-Zeile, über
> **AC-40** behoben, aber **keine** „manuell gepflegte Zahl" und deshalb nicht mitgezählt.
> Beleg und Korrektur in §17.4 (**NF-9**).

### 1.1 Baseline (alle Befunde mit `Datei:Zeile`)

| # | Befund | Beobachteter Wert | Beleg (VERIFIED) |
|---|---|---|---|
| F1 | Agenten-Zahl driftet | `README.md:122` „Agent Roster — **74** Generic Agents"; Ist **80** Rollen-`.md` in `agents/1-generic/` (83 Dateien − 3 `_*`-Helper) | `README.md:122`; Verzeichnislisting `agents/1-generic/` |
| F2 | Provider-Zahl driftet | `README.md:690` „**6** provider configs (Claude, Gemini, Opencode, Continue, Copilot, Mammouth)"; Ist **9** | `README.md:690`; `config/ai-providers.yaml:1` + Provider-Blöcke `:2, :98, :172, :249, :316, :369, :434, :493, :545` |
| F3 | Hook-Zahl **dreifach** widersprüchlich | `README.md:501` „## Hooks (**7** hooks, propagated to all providers)" vs. `README.md:696` „hooks/1-generic/  **5** hook scripts"; Ist **11** deploybare Hooks für `:501` (13 Top-Level-`.sh` — 2 `0-external/` + 11 `1-generic/` — minus 2 `*-impl.sh`) und **9** Hook-Skripte für `:696` (11 Top-Level-`.sh` in `hooks/1-generic/` minus 2 `*-impl.sh`). Die **17** `.sh` unter `hooks/**` (2 + 11 + 1 `lib/hook_common.sh` + 3 `release-gates/`) sind eine **Belegzahl für dieses Befund-Row, kein `DOCS_*`-Faktum** (Rev. 0.3, NEW-1) | `README.md:501`, `README.md:696`; `hooks/**/*.sh`-Listing: `0-external/{graphify-read-guard,graphify-search-guard}.sh`, `1-generic/{antigravity-json-adapter,auto-github-release,lifecycle-check,sync-on-config-change,viz-log,pre-release-check,orchestrator-guard,repo-containment,dod-push-check}.sh`, `1-generic/{orchestrator-guard-impl,repo-containment-impl}.sh`, `1-generic/lib/hook_common.sh`, `1-generic/release-gates/{docker-image-scan,action-pin-validation,artifact-freshness}.sh`; `scripts/lib/hooks.py:95-105` (nicht-rekursives `*.sh`-Glob je Layer: `0-external` `:95-98`, `1-generic` `:101-104`); `scripts/lib/external_tools.py:217-220` („all 0-external hooks are always copied; registration in settings.json stays opt-in per project") |
| F4 | Version driftet — **zwei** Fundstellen (Rev. 0.3) | `README.md:734` „VERSION  # Current version (**v1.0.0**)"; Ist `1.2.0-beta.2`. **Zweite Fundstelle (NEW-3):** `ARCHITECTURE.md:3` „Repo version: **0.92.0** — content last substantively reviewed: 2026-07-20"; dieselbe Zahl ist **zweimal falsch** (auch das Datum predates laut eigenem Kommentar mehrere Releases) | `README.md:734`; `ARCHITECTURE.md:3`; `VERSION:1` (`1.2.0-beta.2`); `.meta-config/project.yaml:1` (`agent-meta-version: 1.2.0-beta.2`). Die `ARCHITECTURE.md`-Deklaration wandert mit M-7 in die Langfassung (§13-A12, AC-29) |
| F5 | **Fünffache** Architektur-Doku | `ARCHITECTURE.md` (84 Zeilen; `:3` „Repo version: **0.92.0**"), `ARCHITECTURE.full.md` (Root), `docs/architecture/` (8 Dateien: `01-layer-model.md` … `07-se-cascade.md` + `prompt-modernization.md`), `knowledge/wiki/concepts/architecture*.md`, `knowledge/sources/ARCHITECTURE.full.md` | `ARCHITECTURE.md:3-4`, `:8-20`; `knowledge/wiki/index.md:24` |
| F6 | **Vierfache** Guide-Führung | `docs/guides/`, `docs/howto/`, `howto/configs/`, `knowledge/wiki/topics/` — **Reviewer-Korrektur M4:** Rev. 0.1 nannte nur drei Orte; `docs/howto/admin-ui-remote-access.md` ist ein vierter, bisher weder in F6 noch in einer Migration erfasst (→ **F23**) | `howto/` enthält **ausschließlich** `configs/`; `howto/configs/` enthält **ausschließlich** `project.yaml.example`; `docs/howto/` enthält **ausschließlich** `admin-ui-remote-access.md`; alle drei VERIFIED per Glob |
| F7 | **Vier** Spec/Plan-Bäume ohne dokumentierte Abgrenzung | `docs/specs/` (22 Einträge inkl. `.gitkeep`), `docs/plans/`, `docs/superpowers/specs/`, `docs/superpowers/plans/` | `docs/specs/`-Listing; `.meta-config/project.yaml:58-63` |
| F8 | `docs/INDEX.md` fehlt, ist aber **bereits spezifizierter Vertrag** | `DEFAULT_FALLBACK_INDEX = "docs/INDEX.md"`; `fallback-index: docs/INDEX.md`; Szenarien 54/55/102 verlangen die Datei | `scripts/lib/spec_plan_scaffold.py:23`; `.meta-config/project.yaml:70`; `tests/scenarios/registry.md:101-102`; `tests/scenarios/asserts/54-spec-plan-external-override.sh:26-27` |
| F9 | Kein generierter Doku-Index | einziger Index-Generator im Repo ist `standalone/README.md` über `render_index()` / `write_standalone_files()` | `scripts/lib/standalone.py:309-369`, `:372-417` |
| F10 | Wiki-Index driftet strukturell | letzter `log.md`-Eintrag 2026-09-03, Specs/Pläne bis 2026-09-19 | `knowledge/wiki/log.md:30` |
| F11 | Wiki-Index deklariert seine Architekturquelle selbst als stale | `status:stale-upstream` | `knowledge/wiki/index.md:24` |
| F12 | `sync_knowledge_engine` regeneriert `index.md`/`log.md` **nie** | Docstring: „never overwrites existing `schema.md`/`wiki/index.md`/`wiki/log.md`" | `scripts/lib/knowledge.py:112-114` |
| F13 | Rollen-Parität: **falsch belegt** (Korrektur, siehe §13-A1) | `se-component-requirements` **ist** in `roles:` enthalten (`project.yaml:148`) und das Template existiert (`agents/1-generic/se-component-requirements.md`). Die Paritätsverletzung entsteht **ausschließlich** aus `systems-engineering.enabled: false` → alle 14 `se-*`-Rollen werden mit `log.skip(..., "systems-engineering is disabled")` übersprungen | `.meta-config/project.yaml:12-13, :148`; `scripts/lib/agent_sync.py:548`; `scripts/lib/roles.py:129` (`resolve_activation_gates`) |
| F14 | Pipeline-Zahl **und** Inhalt driftet | `README.md:479` „## Quality Pipelines (**7** pipelines)" listet 7 Zeilen (`:483-489`). Ist: **8** Pipelines in `config/role-defaults.yaml:2489` (`feature-lifecycle:2490`, `quick-fix:2547`, `bugfix:2572`, `concept-development:2607`, `concept-driven-dev:2633`, `refactor:2706`, `docs-update:2737`, `se-cascade:2755`), davon **7 aktiv** — deaktiviert ist ausschließlich `se-cascade` (`.meta-config/project.yaml:339-342` → `quality-pipelines.overrides.se-cascade.enabled: false`; `role-defaults.yaml:2877` `enabled: false`). **Drei** Fehler in einer Zeile: (a) Zahl 7 statt 8, (b) `concept-driven-dev` fehlt in der Tabelle **ganz**, (c) `se-cascade` steht drin, ist aber deaktiviert. *Reviewer-Korrektur K4: Rev. 0.1 nannte „6 von 7" und stufte die Zahl 7 als korrekt ein — beides falsch.* | `README.md:479-489`; `config/role-defaults.yaml:2489-2877`; `.meta-config/project.yaml:339-342` |
| F15 | **Tote Verweise** | `README.md:721-723` verweist auf `howto/setup/`, `howto/features/` (existieren nicht — `howto/` enthält nur `configs/`); `README.md:724` nennt `CLAUDE.md` als Template-Config (existiert nicht, nur `project.yaml.example`); `docs/REQUIREMENTS.md:21`; `docs/CODEBASE_OVERVIEW.md:33-44` dokumentiert `agents/1-generic/se-orchestrator.md` (existiert nicht — 14 `se-*`-Templates, keines davon `se-orchestrator`) | `README.md:721-724`; `docs/CODEBASE_OVERVIEW.md:33-44` |
| **F15-N (neu, Rev. 0.6 — K23, Präzisierung von F15, F15 bleibt unverändert bestehen)** | **Von F15 genannt, aber von V3 nicht auffindbar.** `docs/REQUIREMENTS.md:21` (REQ-CMD-09) nennt `howto/commands.md`, `CLAUDE.md` und `howto/instantiate-project.md` — die Pfade existieren nicht (`howto/` enthält nur `configs/project.yaml.example`). **Die Stelle ist trotzdem kein V3-Finding:** sie nennt die Pfade in **Backticks** in einer Tabellenzeile, V3 matcht aber nur **Link-Syntax** (`V3_INLINE_LINK_RE`, `V3_REFERENCE_DEF_RE`, `V3_HTML_HREF_RE`; `_v3_link_targets`). Ebenso ist `README.md:721` (`howto/`, existiert) und `README.md:724` (`howto/configs/`, existiert) **kein** Finding; die **beiden** Layout-Fundstellen sind erst `README.md:722` (`howto/setup/`) und `README.md:723` (`howto/features/`). | `docs/REQUIREMENTS.md:21` (Backtick-Pfade, keine Link-Syntax); `scripts/lib/consistency/docs.py:436-446` (Regex-Set), `:497-502` (`_v3_link_targets`), `:591-598` (Layout-Branch nur in `V3_ENTRY_RELPATHS`); `README.md:721-724`; Baseline-Messung 2026-09-27 (Übergabe vom Parent): **0** Findings in `docs/REQUIREMENTS.md`, **2** in `README.md` |
| F16 | Zwei parallele ID-Systeme | `REQ-*` (Format-Regel: `docs/REQUIREMENTS.md:4`) vs. `SPEC-<NAME>-<JJJJ-MM-TT>` (z. B. `docs/specs/2026-09-15-reference-standards-design.md:2`) | beide VERIFIED |
| F17 | Generierte Provider-Verzeichnisse sind gitignored, generierte Root-Kontextdateien **nicht** | `.gitignore:13-17` (`.claude/`, `.gemini/`, `.mammouth/`, `.opencode/`, `.serena/`); für `AGENTS.md` / `CLAUDE.md` existiert **kein** Eintrag | `.gitignore:13-17` (gesamte Datei gelesen) |
| F18 | Bestehende Doku-Checks sind auf `docs/api/` begrenzt | `check_sync_cli_docs` (`:9-44`), `check_ui_help_mappings` (`:47-97`), `check_readme_docs_index` (`:100-121`, globbt **nur** `docs/api/*.md`) | `scripts/lib/consistency/docs.py` (vollständig gelesen, 122 Zeilen) |
| ~~**F19**~~ | ~~Tier-Preset-Zahl driftet~~ — **GESTRICHEN in Rev. 0.2 (K2).** `README.md:689` „tier-presets.yaml  **5** tier presets (cheap, normal, advanced, expensive, expensive as hell)" ist **korrekt**: `config/tier-presets.yaml` hat **5** Top-Level-Tiers (`Cheap:1`, `Normal:31`, `Advanced:85`, `Expensive:115`, **`Expensive as Hell:145`**). Rev. 0.1 zählte nur vier und hätte den Wert **4** generiert — eine falsche Korrektur eines richtigen Befunds. Die ID F19 wird **nicht** neu vergeben, um ID-Recycling zu vermeiden; die Nachfolger erhalten F20…F25. | `README.md:689`; `config/tier-presets.yaml:1, :31, :85, :115, :145` |
| **F20** | **Neuer Befund:** `docs/INDEX.md`-Skeleton trägt eine Textmarke, die der Generator erkennen muss | Skeleton-Text enthält die Zeile `File-based index fallback` | `tests/scenarios/asserts/54-spec-plan-external-override.sh:27`; `scripts/lib/spec_plan_scaffold.py:24` |
| **F21** | **Neuer Befund:** Rollen-Parität ist **nicht** durch `roles:` prüfbar, sondern nur gate-bewusst | `roles:` umfasst 59 Einträge (`.meta-config/project.yaml:92-150`), `config/role-defaults.yaml:1` umfasst 84 Rollen — „roles ⊄ generiert" ist ohne Gate-Auswertung ein Dauerfehlalarm | `.meta-config/project.yaml:92-150`; `config/role-defaults.yaml:1-2403`; `scripts/lib/roles.py:129, :256` |
| **F22** | **Neuer Befund (K3, erweitert in Rev. 0.3 / NEW-2):** DoD-Preset-Zahl driftet — an **zwei** Stellen | (a) `README.md:688` „dod-presets.yaml           # **6** DoD presets"; (b) `README.md:381` „## DoD Presets (**6** presets)" mit einer Tabelle, die **6** Zeilen führt und `concept-driven` **nicht** enthält — dieselbe Fehlerklasse wie F14 (fehlende Tabellenzeile). Ist **7**: `config/dod-presets.yaml:12` `presets:` → `full:13`, `standard:30`, `rapid-prototyping:46`, `spec-optional:62`, `spec-driven:79`, `concept-driven:96`, `spec-certified:113`. *Rev. 0.1 führte (a) als „korrekt, nicht zu ändern" — sie ist der Beleg, auf dem das Fehlalarm-Argument in R4 sich stützte, und ist selbst Drift. Rev. 0.2 führte (a) allein und behauptete in NF-4, `README.md:381` existiere nicht — das ist **widerlegt** (§17.4, NF-11).* | `README.md:688`; `README.md:381-390` (Überschrift + 6 Tabellenzeilen `:385-390`); `config/dod-presets.yaml:12-113` |
| **F23** | **Neuer Befund (M4):** vierter Guide-Ort ohne SSoT-Entscheidung | `docs/howto/admin-ui-remote-access.md` existiert, ist in keiner Migration und keiner SSoT-Entscheidung verortet; `howto/`-Root verschwindet (F15), `docs/howto/` bliebe als dritter Guide-Ort ohne Zuordnung stehen | Glob `docs/howto/**` (genau 1 Datei) |
| **F24** | **Neuer Befund (M4):** zwei Beispiel-Configs für denselben Zweck | `docs/guides/project.yaml.example` (**179** Zeilen) und `howto/configs/project.yaml.example` (**340** Zeilen). Nach M-5 liegen **beide** unter `docs/guides/` — eine SSoT-Entscheidung ist nicht getroffen; sie ist eine **inhaltliche** Frage (NG-1) und daher **OQ9** | Dateilängen per Read bestätigt (179 / 340 Zeilen, Endzeilen gelesen) |
| **F25** | **Neuer Befund (R15):** Config-Schema kennt die neuen Keys nicht | `config/project-config.schema.json` (2645 Zeilen) enthält keinen `docs-consolidation`-Block; das Wurzel-Schema ist `additionalProperties: true` (`:2425`) — die Keys würden also **nicht** validiert, aber auch **nicht** per IDE-Autocomplete angeboten. Das Repo nutzt geschlossene Unterobjekte ausdrücklich als Tippfehler-Wächter (Selbstauskunft `:2058`, `:2073`) | `config/project-config.schema.json:2425, :2058, :2073` |

**Korrekt und daher nicht zu ändern** (Beleg, damit V1 keinen Fehlalarm erzeugt):

| Zeile | Aussage | Warum korrekt |
|---|---|---|
| `README.md:689` | „5 tier presets (cheap, normal, advanced, expensive, expensive as hell)" | `config/tier-presets.yaml` hat **5** Top-Level-Tiers (`:1, :31, :85, :115, :145`) — **Reviewer-Korrektur K2**, Rev. 0.1 hatte diese Zeile fälschlich als Drift geführt |
| `README.md:695` | „22 slash-command definitions" | `commands/1-generic/*.md` = **22** Dateien (Glob) |

> **Konsequenz für R4:** Rev. 0.1 stützte sein V1-Fehlalarm-Argument auf `README.md:688`
> („6 DoD presets ist korrekt"). Diese Zeile ist **Drift** (F22), das Argument trägt nicht mehr,
> und R4 wird in §12 entsprechend neu begründet.

### 1.2 Quantifizierter Zielzustand

| Metrik | Ist (2026-09-26) | Ziel nach W8 | Prüfbar durch |
|---|---|---|---|
| manuell gepflegte Zahlen in `README.md` / `llms.txt` / `ARCHITECTURE.md` | **11** = 10 in `README.md` (F1, F2, F3 ×2, F4, F14 ×3, **F22 ×2** — nach NEW-2 mit `README.md:381`) + 1 in `ARCHITECTURE.md:3` (F4). `llms.txt:5` ist eine Prosa-Aufzählung (6 von 9 Providernamen), **keine** Zahl → nicht mitgezählt, inhaltlich über AC-40 behoben | **0** | V1a (Counts), V1b (Versions-Literal) — AC-07/AC-08 |
| Doku-Bäume mit demselben SSoT-Gegenstand | 5 (Architektur), **4** (Guides, korrigiert), 4 (Spec/Plan) | 1 / 1 / 1 (+ archivierte Legacy-Bäume) | V2, V8 |
| `docs/INDEX.md` | existiert nicht | existiert, 100 % generiert, tracked | V2, V4 |
| tote relative interne Links in **`README.md` + `llms.txt`** (Rev. 0.6, U-2/K22: AC-30-Scope **verengt**) | **2** (Baseline-Messung 2026-09-27: beide `branch=="layout"`, `README.md:722` `howto/setup/` und `README.md:723` `howto/features/`; `llms.txt` = **0**) | **0** | V3 |
| tote relative interne Links unter **`docs/**`** — **Rev. 0.6, U-2: aus dem AC-Scope genommen** | **25** (Baseline-Messung 2026-09-27: `docs/guides` 10, `docs/concepts` 13 — davon 8 in `docs/concepts/archive/` —, `docs/superpowers/plans/` 2; **live** ohne `archive/` = **17**) | **Follow-up `F-DOCS-LINKS-2026-09-27`**, Owner `developer`, Termin **2026-10-11** — **kein** AC, **kein** Sollwert dieses Vorhabens | V3 (meldet weiter, ohne Termin 0 in W0–W8) |
| Wiki-Seiten ohne `derived-from` bei `type: Architecture` | nicht erhebbar ohne Generator | **0**; alle übrigen Abweichungen nur WARN | V7 |
| `log.md` Alterung | 4 Wochen (F10) | 1 Zeile pro Sync mit Wiki-Änderung | V7 + W7 |
| **unabhängig gepflegte Sollwerte** (Handpflege, nicht aus der Formel abgeleitet) | **0** — kein Gate prüft die Formel gegen eine unabhängige Zahl (R14) | **elf** Werte in `config/doc-facts-expected.yaml` (IC-23), geprüft von einem Test | AC-36 (IC-23) |

---

## 2. Ziel / Nicht-Ziele

### 2.1 Ziel

1. **Jede Zahl in der Einstiegs-Doku ist berechnet, nicht geschrieben.** Eine einzige
   Faktum-Berechnung (`doc_facts.py`) liefert `DOCS_*`-Werte aus den jeweils kanonischen
   Quellen; Rendering und Checks konsumieren dieselbe Quelle — **und** eine zweite,
   unabhängig handgepflegte Datei (`config/doc-facts-expected.yaml`, IC-23) prüft die Formel
   von außen, damit ein systematisch falscher Faktor nicht alle Gates passiert (R14).
2. **Ein kanonischer Doku-Index** (`docs/INDEX.md`, generiert) erfüllt den bereits
   spezifizierten, aber unerfüllten Vertrag aus `spec_plan_scaffold.py:23`.
3. **Verify-by-construction:** die Doku-Checks V1–V9 machen die in §1.1 dokumentierten
   Fehlerklassen *nicht wiederholbar*, statt sie einmal zu korrigieren.
4. **Staleness wird maschinell.** `derived-from` + `derived-at` + Quell-mtime liefern
   `status: stale-source`; das Wiki bleibt ein **abgeleiteter Schatten** mit Herkunftsangabe
   und wird nie ein zweiter Architektur-SSoT.
5. **Migration ohne Inhaltsverlust:** alle Pfadverschiebungen sind `git mv`; keine
   Neuschreibung bestehender Guide- oder Architektur-Inhalte.
6. **Additive, abwesenheits-tolerante Defaults.** Kein Key dieser Initiative verändert
   bestehendes Verhalten, wenn er nicht explizit gesetzt ist — für **Writer und Checks
   gleichermaßen** (Präzedenz `knowledge.py:127-129`).

### 2.2 Nicht-Ziele (hart — Abweichung gilt als Spec-Verstoß)

| # | Nicht-Ziel | Begründung / Beleg |
|---|---|---|
| NG-1 | **Keine inhaltliche Neuschreibung** bestehender Guides, Architektur-Dokumente oder Wiki-Seiten | R9; Migrationswellen sind `git mv` + Marker + Annotationszeilen. Inhaltsarbeit ist eigene REQ. |
| NG-2 | **Keine Mutation an `knowledge/sources/`.** Append-only; nur `knowledge-ingestor` schreibt, `knowledge-curator`/`knowledge-gardener` haben dort kein Schreibrecht | Design §5.1; Policy-Zanker `knowledge/schema.md:44-46` („Removing or renaming an existing type is a structural change and requires user sign-off") |
| NG-3 | **Keine Änderung der Doku-Ownership.** `docs/CODEBASE_OVERVIEW.md` gehört dem `documenter`-Agenten; diese Spec erzeugt dort ausschließlich einen generierten Fakten-Footer und **keinen** Inhalt | `knowledge/wiki/log.md:30` („docs/CODEBASE_OVERVIEW.md bewusst NICHT migriert (HARD CONSTRAINT — gehört documenter-Agent)"); Design R11 |
| NG-4 | **Kein neues `sync.py`-CLI-Flag.** Jedes Flag wäre in `docs/api/cli-reference.md` zu dokumentieren (`consistency/docs.py:9-44` erzwingt das als `Severity.ERROR`) und erzeugte damit selbst Doku-Drift | Design T-5; `scripts/lib/consistency/docs.py:34-42` |
| NG-5 | **Kein Eingriff in generierte Kontextdateien** (`AGENTS.md`, `CLAUDE.md`, Provider-Verzeichnisse) außer dem in M3 beschriebenen, config-seitigen `PROJECT_STRUCTURE`-Korrektur-Edit | Design §7.1; `.gitignore:13-17` |
| NG-6 | **Keine Umbenennung bestehender `SPEC-*`-IDs.** `SPEC-<NAME>-<JJJJ-MM-TT>` bleibt; das Verhältnis zu `REQ-*` wird nur *dokumentiert* (OQ4) | F16; Design OQ4 |
| NG-7 | **Keine Umbenennung/Veröffentlichung von `docs/INDEX.md` in ein anderes Schema** (`docs/README.md` verworfen) | Design T-3; `spec_plan_scaffold.py:23` ist der bestehende Vertrag |
| NG-8 | **Kein Rollen-Paritäts-Fix.** `se-component-requirements` bleibt in `roles:`, die Parität bleibt über den SE-Gate geregelt; V5 wird **gate-bewusst** gebaut, nicht am `roles:`-Listeninhalt | F13/F21-Korrektur, §13-A2; Fix wäre ein Config-Edit und gehört in eigene REQ |
| NG-9 | **Kein Rollout in Consumer-Projekte ohne Opt-in.** `docs-consolidation.enabled` ist **in allen** Projektlayouts per Default `false` — auch in agent-meta selbst wird der Wert **explizit** `true` gesetzt (`.meta-config/project.yaml`, W1). Damit ist die Absenz-Semantik identisch zur Fail-off-Präzedenz `knowledge.py:127` (`ke_config.get("enabled", False)`) und erzeugt **keinen** ungewollten Verhaltenswechsel in den Szenario-Fixtures | Design §3.4 (angepasst, siehe §13-A10); agent-meta ist Submodul in Fremdprojekten (Downstream-Kompatibilität) |
| NG-10 | **Keine Änderung an den Szenarien 50–56.** Sie sind der bestehende Regressionstest für den `docs/INDEX.md`-Vertrag. Diese Spec passt sich **ihnen** an (Absenz-Defaults, Besitzregel, `knowledge-engine`-Schreibverbot) — nicht umgekehrt | `tests/scenarios/registry.md:97-103`; IC-13, IC-15, AC-38 |
| NG-11 | **Kein Platzhalter-Marker in generierten Provider-Dateien.** `DOCS_*`-Platzhalter werden ausschließlich von E3 (`doc_renderer`) aufgelöst, nie von E1/E2 — sonst würden sie in Consumer-Provider-Dateien landen | IC-11, OQ5 (geschlossen, §11) |

### 2.3 Scope-Grenzen gegen Nachbar-Initiativen

- **Track A** (parallel, arbeitet in `tests/`, `tests/fixtures/`, `scripts/lib/`, `config/`):
  W1/W2 werden **nicht** parallel zu Track A gestartet. Vor W1: `git log --oneline -20 -- scripts/lib/`
  prüfen; pro Welle ein Commit pro Datei; vor jedem Merge Rebase gegen den Track-A-Branch
  (Design R3). **Neu (R15/§2.3-A):** Track A committet derzeit in
  `tests/fixtures/slimming-golden/`; die in AC-07/AC-08 spezifizierte V1-Fixture
  (`tests/fixtures/docs_v1_fixtures.md`) darf deshalb **nicht** angelegt werden, bevor der
  Track-A-Branch gemergt ist. Ownership-Konflikt, kein Berechtigungs-Konflikt.
- **Szenario `64-docs-facts-drift.md`**: von **Track A** verfasst, nicht in dieser Initiative
  (Design §4, Ownership-Konflikt). Diese Spec definiert nur das Verhalten, das es prüft
  (AC-15). **Nummerierungskorrektur (Rev. 0.2, §17.1-NF-1):** das Design nennt
  `63-docs-facts-drift.md`, die Nummer **63 ist im Repo bereits vergeben**
  (`registry.md:110` = `63-context-file-modes`, `asserts/63-context-file-modes.sh`,
  `configs/63-context-file-modes.project.yaml`). Korrekt ist **64**.
- **Der AGENTS.md-Bootstrap-Block** (66 hartgelistete Agenten am Repo-Ende) driftet
  ebenfalls, ist aber **bewusst außerhalb** des Scopes (OQ3, Design R10).

---

## 3. Zielstruktur / SSoT-Matrix

### 3.1 Generationsmodi (verbindliche Definition)

| Modus | Definition | Schreibrecht | Drift-Folge |
|---|---|---|---|
| **generiert** | Datei ist 100 % Generator-Output; Handedit ist ein Fehler | Generator | V6 (ERROR) |
| **hybrid** | Handprosa + generierte Marker-Regionen (`agent-meta:docs-*`) | Mensch außerhalb, Generator innerhalb der Marker | V1 (ERROR ab W2-Ende), V6 (ERROR) |
| **handgepflegt** |rein manuell; nur optionaler generierter Fakten-Footer | Mensch | keiner (bewusst) |
| **redirect** | reine Verweis-Seite ohne eigenen Inhalt, zeigt auf das SSoT | Mensch (ein Link) | V3 (ERROR auf toten Link) |
| **archiviert** | historischer Beleg, nicht mehr referenziert | keines | keiner |

### 3.2 SSoT-Matrix: Faktumklasse → kanonische Quelle → Konsumenten → Modus

| Faktumklasse | Kanonische Quelle (SSoT) | Konsumenten | Modus |
|---|---|---|---|
| Version | `VERSION` (gelesen via `read_version()`, `scripts/lib/config.py:1060-1064`) | `README.md`, `llms.txt`, `ARCHITECTURE.md`, `docs/INDEX.md` | generiert (Faktenblock) |
| Agenten-Templates gesamt / SE / non-SE | `agents/1-generic/*.md` mit Frontmatter `name` (80 Dateien, 3 `_*`-Helper ausgeschlossen) | `README.md:122`, `docs/INDEX.md` | generiert |
| Rollen **aktiv** (erzeugte Provider-Dateien) | `roles:` (`.meta-config/project.yaml:92-150`) ∩ Templates ∩ `resolve_activation_gates()` (`scripts/lib/roles.py:129`) | `README.md`, `docs/INDEX.md` | generiert |
| Hooks | `hooks/**/*.sh`, Top-Level-Regel ohne `lib/`, ohne `release-gates/`, **ohne `*-impl.sh`** → **11** deploybare Hooks (`DOCS_HOOKS_COUNT`, global, „propagated to all providers"); für die Verzeichnis-Zeile `README.md:696` ein **eigenes, enger gebundenes** Faktum `DOCS_HOOKS_1GENERIC_COUNT` = `hooks/1-generic/*.sh` ohne `*-impl.sh` → **9** | `README.md:501` → 11 (`DOCS_HOOKS_COUNT`), `README.md:696` → 9 (`DOCS_HOOKS_1GENERIC_COUNT`), `docs/INDEX.md` → `DOCS_HOOKS_BLOCK` | generiert |
| Provider | `config/ai-providers.yaml:1` → 9 Blöcke | `README.md:690`, `llms.txt:5`, `docs/INDEX.md` | generiert |
| Pipelines (mit Enabled-Status) | `config/role-defaults.yaml:2489` (8) ∩ `.meta-config/project.yaml:339-343` → 7 aktiv | `README.md:479-489`, `docs/INDEX.md` | generiert |
| DoD-Presets / Tier-Presets | `config/dod-presets.yaml:12` (7) / `config/tier-presets.yaml:1, :31, :85, :115, :145` (5) | `README.md:381-390` (Überschrift **und** Preset-Tabelle, F22 b) → 7, `README.md:688` (F22 a) → 7, `README.md:689` → 5 | generiert |
| Commands | `commands/1-generic/` | `README.md:695` | generiert |
| Szenarien (**volatil**) | `tests/scenarios/asserts/*.sh` (63 Dateien) | **nur** `docs/INDEX.md`, in einer `docs-volatile`-Sektion **am Dateiende vor dem Footer** und **nicht** im `facts-hash` (R1) | generiert, README/llms ausgeschlossen (R1) |
| Doku-Baum + 1-Zeilen-Beschreibungen | Dateisystem `docs/**/*.md` + Frontmatter `description` | `docs/INDEX.md`, `docs/architecture/INDEX.md` | generiert |
| Doku-Architektur-Langfassung | `docs/architecture/00-overview-full.md` (aus Root via `git mv`) | `ARCHITECTURE.md` (Stub), `llms.txt:24` | handgepflegt |
| Architektur-Detailseiten | `docs/architecture/01…07` | `ARCHITECTURE.md`-Stub, `docs/architecture/INDEX.md` | handgepflegt |
| Architektur-Diagramm-Index | `ARCHITECTURE.md` (Diagramm-Tabelle `:8-20`) | `llms.txt:24`, Root | generierter Stub (T-4) |
| Guides | `docs/guides/` (inkl. M-6 aus `docs/howto/`) | `docs/INDEX.md`, Wiki-Redirects | handgepflegt |
| Beispiel-Configs | `docs/guides/configs/project.yaml.example` (340 Z, aus `howto/configs/`, M-5) **und** `docs/guides/project.yaml.example` (179 Z, bereits vorhanden) — **SSoT zwischen beiden ungeklärt → OQ9**; bis zur Entscheidung bleiben **beide** bestehen (kein Merge, NG-1) | `docs/INDEX.md` | handgepflegt |
| Provider-Referenz | `docs/providers/` (6 von 9 — Lücke als Befund) | `docs/INDEX.md` | handgepflegt |
| CLI-/UI-Referenz | `docs/api/` (7 Dateien) | `README.md` (V4), `llms.txt:17-19` | handgepflegt |
| Specs / Pläne / Spikes | `docs/specs/`, `docs/plans/`, `docs/spikes/` (`.meta-config/project.yaml:58-60`) | `docs/INDEX.md` | handgepflegt / archiviert |
| Spec-Plan-Legacy | `docs/superpowers/{specs,plans}` → `docs/{specs,plans}/archive/superpowers/` | keiner (historisch) | archiviert |
| Doku-Index | `docs/INDEX.md` | alle Doku-Konsumenten | generiert |
| Knowledge-Quellen | `knowledge/sources/` | Wiki (nur lesend) | **unveränderlich** (NG-2) |
| Knowledge-Wiki-Seiten | `knowledge/wiki/{concepts,entities,topics,plans,specs,sources,queries}/` | `knowledge/wiki/index.md` | handgepflegt (LLM) + Pflicht-`derived-from` |
| Knowledge-Index | `knowledge/wiki/index.md` | Knowledge-Agenten | generiert (W7, Flag-gated) |
| Knowledge-Log | `knowledge/wiki/log.md` | Knowledge-Agenten | hybrid (Generator-Append + manuell) |
| `docs/CODEBASE_OVERVIEW.md` | `documenter`-Agent | Nutzer | handgepflegt, **nur** Fakten-Footer (NG-3) |
| Anforderungen | `docs/REQUIREMENTS.md` (`REQ-*`, Format `:4`) | `validator` | handgepflegt |

### 3.3 SSoT-Entscheidung je Bereich (aus Design §1.1, unverändert übernommen)

| Bereich | SSoT | Wird Stub/Redirect | Wird archiviert | Verschwindet |
|---|---|---|---|---|
| Root-Doku | `README.md` (Handprosa) + `DOCS_*`-Faktenblöcke | `ARCHITECTURE.md` → generierter Pointer auf `docs/architecture/INDEX.md` | — | `howto/`-Root (F15) |
| docs-INDEX | `docs/INDEX.md`, 100 % generiert | — | — | kein `docs/README.md` (T-3/T-4) |
| Architektur | `docs/architecture/` (00 + 01–07 + `prompt-modernization.md`) | Root-`ARCHITECTURE.md`; `knowledge/wiki/concepts/architecture*.md` → Verweis-Seiten | `ARCHITECTURE.full.md` → `docs/architecture/00-overview-full.md` | keiner |
| Guides | `docs/guides/` | `knowledge/wiki/topics/*-guide*` → Redirect | `howto/configs/` → `docs/guides/configs/`; `docs/howto/admin-ui-remote-access.md` → `docs/guides/admin-ui-remote-access.md` (M-6) | `howto/`-Root (F15), `docs/howto/`-Root (F23) |
| Specs/Pläne | `docs/specs/`, `docs/plans/`, `docs/spikes/` | — | `docs/superpowers/{specs,plans}` → `docs/{specs,plans}/archive/superpowers/` | `docs/superpowers/` |
| Knowledge-Wiki | **kein SSoT** — abgeleiteter Schatten | alle mit `derived-from` | `knowledge/sources/` bleibt unverändert | keiner |
| Traceability | `docs/REQUIREMENTS.md` (`REQ-*`) | — | `SPEC-*`-Naming bleibt (NG-6) | — |

---

## 4. Modulaufteilung (vier in sich abgeschlossene Module, eine Spec-Datei)

Begründung der Ein-Datei-Entscheidung: die Repo-Konvention verlangt **eine** Spec-Datei pro
`spec-id` mit Frontmatter-`spec-id` (`docs/specs/2026-09-15-reference-standards-design.md:1-8`,
`docs/specs/2026-09-13-stale-role-cleanup-design.md:1-9`) und einen `Trace-Anker`-Block; sie
verlangt **nicht** genau eine Datei für vier Wellen-Gruppen. Das Design empfahl in §11 vier
Wellen-Specs. Diese Spec hält die vier Module als **getrennte, in sich abgeschlossene
Abschnitte mit eigenen ICs, ACs, Wellen und Rollback-Punkten**; eine Aufteilung in vier
Dateien ist eine **Planungsentscheidung** und wird hier **nicht** vorweggenommen
(**OQ7 — geschlossen**, §11).

| Modul | Verantwortung (genau eine) | Dateien (Code) | Wellen | Vorgänger | Rollback |
|---|---|---|---|---|---|
| **M1 — DocFacts + Doku-Checks** | Berechnet `DOCS_*`-Fakten und bewertet Doku-Drift | `scripts/lib/doc_facts.py` (neu), `scripts/lib/consistency/docs.py` (erweitert), `scripts/consistency-check.py` (Registrierung), `scripts/lib/consistency/placeholders.py` (Namespace), `config/doc-facts-expected.yaml` (neu, handgepflegt) | W1, W2 | — | `docs-consolidation.checks.strict: false`; `docs-consolidation.enabled: false` |
| **M2 — Renderer + Indexer + Brücke** | Rendert `docs/INDEX.md` und `DOCS_*`-Blöcke; garantiert Idempotenz, `dry_run`, Fact-Hash | `scripts/lib/doc_renderer.py` (neu), `scripts/lib/doc_index.py` (neu), `scripts/lib/config.py` (Snippet-Bridge), `scripts/lib/sync_pipeline.py` (Stage), `scripts/lib/spec_plan_scaffold.py` (Guard), `scripts/lib/generated_file_drift.py` (Docs-Dateiliste), `snippets/docs/*.md` (neu) | W1, W3, W4 | M1 | `git rm docs/INDEX.md`; Marker entfernen; `docs-consolidation.enabled: false` |
| **M3 — Migration** | Pfadverschiebungen und Marker-Regionen (`git mv`, kein Inhalts-Rewrite) | keine neuen Code-Dateien; `README.md`, `ARCHITECTURE.md`, `.meta-config/project.yaml`, `config/project-config.schema.json`, `docs/**` | W4, W5, W6, W8 | M2 (W3) | je Welle: `git mv` zurück; Config-Key additiv → Zeile entfernen |
| **M4 — Knowledge-Index-Generierung** | Rendert `knowledge/wiki/index.md` deterministisch; hängt `log.md` an | `scripts/lib/knowledge.py` (erweitert), `agents/1-generic/knowledge-indexer.md` (Umschreibung) | W7 | M3 (W5) | `knowledge-engine.okf.index-mode: llm` → Generator stumm; `restore_wiki_index()` (IC-24) |

**Test-Dateien** (von der Implementierung zu erzeugen, kein Produktions-Footprint, aber vom
Plan zu berücksichtigen — Dateinamen sind über die ACs verbindlich festgelegt):
`tests/test_doc_facts.py`, `tests/test_doc_renderer.py`, `tests/test_generated_file_drift_docs.py`,
`tests/test_knowledge_index_gen.py`, `tests/test_docs_consolidation_migration.py`,
`tests/fixtures/docs_v1_fixtures.md` (V1-Fixture, AC-07/AC-08).
**Ergänzt in Rev. 0.6 (K29, U-1/K20) — drei neue, je Modul getrennte Test-Dateien.** Grund ist die
Parallelität in W2: ohne getrennte Test-Write-Sets wäre jede Parallelgruppe wieder eine Kette.
Die **Zahl** der Tests wächst dadurch **nicht** — die V1-Tests **wandern** aus `test_doc_facts.py`:

| Test-Datei (neu) | Task (Plan) | Modul | Tests |
|---|---|---|---|
| `tests/test_doc_freshness.py` | **W2-0** (Anlage, V1-Tests wandern) → **W2-5** (V6) | `docs_freshness.py` | V1a/V1b (AC-07/AC-08), V6 (AC-36) |
| `tests/test_doc_freshness_v5.py` (neu, **Rev. 0.7 / E-7**) | **W2-4** (V5) | `docs_freshness_v5.py` | V5 (AC-11) |
| `tests/test_doc_wiki.py` | **W2-3** | `docs_wiki.py` | V7 (AC-10) |
| `tests/test_doc_index.py` | **W2-6** | `docs_index.py` | V2 (AC-12) · V4 (README-Index-Scope, **Rev. 0.7 / E-5**) |

**Summe bleibt die Vorher-Baseline:** `tests/test_doc_facts.py` + `tests/test_doc_facts_expected.py`
= **163 passed** (Baseline-Messung 2026-09-27); nach W2-0 muss der Gesamtzähler **≥ 163** sein
(Plan Task W2-0, Schritt 5).

**Schichtungs-Invariante (unverändert, Design §2):** M1 ist das stdlib-only-Blatt ohne
Doku-Dateisystem-Wissen; M2 konsumiert M1; M3 ist reiner Datenumzug ohne Code; M4 ist ein
Schwester-Modul zu M2, das M1 **nicht** importiert (kein Zyklus, keine Kopplung).

### 4.1 Dateicheck-Modulgrenzen innerhalb von M1 (U-1, Rev. 0.6)

> **Abgrenzung — M1–M4 und die U-1-Module sind NICHT dasselbe, Namensverwechslung ausgeschlossen.**
> **M1–M4** (Tabelle oben) sind **Fach**-Module: sie beschreiben **Verantwortungsbereiche über
> Wellen hinweg** (Faktenberechnung, Rendering, Migration, Knowledge-Index) und tragen die
> **AC-** und **IC-**-Verträge. **M1** umfasst dabei *zwei* Code-Ebenen: `doc_facts.py` (Rechnung)
> und `consistency/docs.py` (Prüfen) — **korrigiert in K31**: die Erstfassung dieses Absatzes
> nannte zusätzlich `doc_renderer.py`/`doc_index.py`, die laut Modultabelle oben jedoch **M2** sind
> und dort unverändert bleiben.
> Die **U-1-Module** sind dagegen **rein technische Dateicheck-Familien** — sie schneiden
> **ausschließlich** die *Prüfebene* von M1 in vier Dateien und sagen **nichts** über
> Zuständigkeiten über Wellen hinweg aus. **Merksatz:** *M1–M4 = was wird gebaut (Fach);
> U-1-Module = wo der Datei-Check-Code liegt (Datei).* Die U-1-Module bleiben **vollständig
> innerhalb M1**; **kein** U-1-Modul ist ein M-Modul und **kein** M-Modul wird umbenannt.
> M1–M4 behalten ihre IDs und ihre Bedeutung unverändert (Rev. 0.6 ändert an dieser Tabelle
> **nichts**).

**Begründung des Schnitts (K18).** Die Familie ist **die Frage, die ein Check stellt**, nicht die
Dateigröße und nicht die Wellenzugehörigkeit: (a) *Ist die Referenz auflösbar?* · (b) *Stimmt die
Doku mit dem berechneten Ist-Zustand überein?* · (c) *Stimmt die abgeleitete Bestands-Oberfläche
mit ihrem Erzeuger überein?* · (d) *Ist der Doku-Bau vollständig und geführt?* Jeder Check beantwortet
genau **eine** Frage, und kein Check zweier Module teilt eine Frage — das ist die eigentliche
Zusicherung der Trennschärfe. Die Größengrenze (< 600 Zeilen) ist **Folge**, nicht Zweck.

| U-1-Modul (Datei) | Frage | V-Checks | Altchecks | Fach-Modul | Erwartete Endzeilen |
|---|---|---|---|---|---|
| `scripts/lib/consistency/docs_links.py` (neu) | Ist jede **Referenz** auflösbar? | **V3** `check_internal_links`, **V4** `check_readme_docs_index` | `check_sync_cli_docs`, `check_ui_help_mappings` | M1 (Prüfebene) | **~330** |
| `scripts/lib/consistency/docs_freshness.py` (neu) | Stimmt die Doku mit dem **berechneten Ist-Zustand** überein? | **V1a/V1b** `check_no_manual_counts`, **V6** `check_docs_facts_fresh` | — | M1 | **~480** · **Ist nach W2-5: 592** |
| `scripts/lib/consistency/docs_freshness_v5.py` (neu, **Rev. 0.7 / E-7**) | Ist der **dokumentierte Rollenbestand** mit den **erzeugten** Rollen identisch? | **V5** `check_role_generation_parity` | — | M1 | **≈ 55–70** |
| `scripts/lib/consistency/docs_wiki.py` (neu) | Stimmt die **abgeleitete Wissens-/Bestands-Oberfläche** mit ihren Quellen überein? | **V7** `check_wiki_staleness`, **V8** `check_spec_plan_path_convention` | — | M1 | **~200** |
| `scripts/lib/consistency/docs_index.py` (neu) | Ist der **Doku-Bau** vollständig und geführt? | **V2** `check_docs_index_completeness`, **V9** `check_stale_backups` | — | M1 | **~180** |
| `scripts/lib/consistency/docs.py` (**Fassade**) | Re-Export-Contract | — (re-exportiert alle) | — | M1 | **~70** |

**Jeder V-Check V1…V9 und jeder der drei Altchecks ist genau einem Modul zugeordnet** — die
Vollständigkeit dieser Zuordnung ist eine Eigenschaft der Tabelle: 9 V-Checks (V1 zählt als V1a/V1b
**eines** Moduls) + 3 Altchecks = **12 Zuordnungen auf 4 Module**, ohne Doppel- und ohne
Lückenzuordnung.

> **Rev. 0.7 / E-7 — aus 4 Modulen werden 5; die 12/12-Disjunktheit bleibt.** `docs_freshness.py` ist
> nach **W2-5 gemessen bei 592 Zeilen**; V5 braucht realistisch **55–70** Zeilen und würde die harte
> **< 600**-Grenze reißen (**647–662**). V5 wird deshalb in das eigene Modul
> `docs_freshness_v5.py` ausgelagert. **Größenfolge (verbindlich):** `docs_freshness.py` **592**
> (V1a/V1b + V6 — **8** Zeilen Reserve, **kein** weiterer V-Check) · `docs_freshness_v5.py`
> **≈ 55–70** (V5) — **beide < 600** ✓. **Zuordnung nach E-7:** `docs_links` = V3 + V4 + 2 Altchecks
> (4) · `docs_freshness` = V1a/V1b + V6 (3) · `docs_freshness_v5` = V5 (1) · `docs_wiki` = V7 + V8 (2)
> · `docs_index` = V2 + V9 (2) ⇒ **12 Zuordnungen auf 5 Module**, weiterhin disjunkt und lückenlos.
> **Die Schnittlogik bleibt dieselbe Frage-Frage-Zuordnung:** `docs_freshness_v5` beantwortet
> *„Stimmt der dokumentierte Rollenbestand mit dem erzeugten Rollenbestand überein?"* — dieselbe
> Familie wie V1 (Handzahl vs. berechnete Zahl), aber **eigener Modulbestand**, weil der gemeinsame
> Bestand die Größengrenze reißt. **Die Größengrenze ist Folge, nicht Zweck** (K18-Logik) — hier
> ist die Folge einmalig durchgesetzt worden, weil ein Modul an der Grenze stand und die
> Alternativen (V1-Prosa komprimieren, `_v6_finding` wiederverwenden) **Kopplung** erzeugt hätten
> (E-7-Auswahl, Plan Rev. 0.7).
>
> > **Der unmittelbar folgende Absatz („Zur Zuordnung von V5") bleibt wortgleich und ist durch
> > E-7 überholt.** Seine Aussage „ein eigenes Modul dafür wäre eine fünfte Datei und würde die
> > U-1-Vorgabe verlassen" beschreibt den Stand **vor** E-7. **Heute gilt:** V5 liegt in
> > `docs_freshness_v5.py` — es **ist** die fünfte Datei, und die U-1-Vorgabe wird damit
> > **ausdrücklich erweitert**, nicht stillschweigend verlassen. **Warum die Erweiterung die
> > richtige war:** die Alternative (gleiches Modul, 647–662 Zeilen) hätte entweder den
> > **Abnahme-Sollwert** `< 600` gebrochen oder **Kopplung** in einen geteilten Helfer eingezogen;
> > **beides** wäre eine stillschweigende Änderung gewesen.

**Zur Zuordnung von V5** (bewusst getroffen, weil U-1 genau vier Module vorsah und
V5 sonst nirgends hingehört): `check_role_generation_parity` vergleicht den in der Doku
**dokumentierten** Rollenbestand mit den **tatsächlich generierten** Rollen — das ist dieselbe
Frage wie V1 (Handzahl vs. berechnete Zahl) und V6 (generierter Block vs. berechneter Fakt). Ein
eigenes Modul dafür wäre eine fünfte Datei und würde die U-1-Vorgabe verlassen. **Zur Zuordnung von
V8** (später Welle W6-2) und **V9** (W8-4): beide prüfen, ob eine **abgeleitete Doku-Oberfläche**
(`docs/{specs,plans}`-Pfadkonvention bzw. generierte Stammbäume) noch zu ihrem Erzeuger passt —
`docs_wiki` bzw. `docs_index`. Die Zeilenschätzungen sind **Prognosen** aus dem gemessenen
Ist-Stand (`docs.py` **599** Zeilen, Baseline-Messung 2026-09-27) und stehen unter der Grenze von
**600** mit Beleg-Reserve; **keine** der Zahlen ist ein Sollwert des Gates (K18).

**Fassaden-Contract (K19) — rückwärtskompatibel, nicht verhandelbar.** `docs.py` bleibt das
einzige Modul, das der Runner und die Test-Suite importieren. Es enthält **keine** Check-Logik,
nur Re-Exports, und exportiert **exakt** diese Namen:

```python
# scripts/lib/consistency/docs.py — Fassaden-__all__ (Rev. 0.6)
__all__ = [
    # --- Fassaden-Durchreichung an die Tests (heute genutzt) ---
    "Finding", "Severity",          # aus .report — Testreferenz docs_lib.Severity
    # --- V1 (docs_freshness) ---
    "check_no_manual_counts", "V1_CHECK_ID", "V1_SCAN_RELPATHS",
    "V1_GENERATED_RELPATHS", "V1_MAX_TOKEN_GAP", "V1_REGION_BEGIN", "V1_REGION_END",
    "V1_EXEMPT_MARKER", "V1_SUGGESTION", "v1a_count_spans", "v1b_version_spans", "v1_strict",
    "Span",
    # --- V3 (docs_links) ---
    "check_internal_links", "V3_CHECK_ID", "V3_SUGGESTION", "V3_ENTRY_RELPATHS",
    "V3_DOCS_RELDIR", "V3_DOC_SUFFIXES", "V3_INERT_PREFIXES",
    # --- Altchecks (docs_links) ---
    "check_sync_cli_docs", "check_ui_help_mappings", "check_readme_docs_index",
    # --- in W2-3…W2-7 nachrückend, ebenfalls durch die Fassade sichtbar (IC-05-Konvention) ---
    "check_wiki_staleness",          # W2-3  (docs_wiki)
    "check_role_generation_parity",  # W2-4  (docs_freshness)
    "check_docs_facts_fresh",        # W2-5  (docs_freshness)
    "check_docs_index_completeness", # W2-6  (docs_index)
    "check_spec_plan_path_convention",  # W6-2  (docs_wiki)  — K28
    "check_stale_backups",           # W8-4  (docs_index)
]
```

**Belege für die Vollständigkeit dieser Liste (kein Name geraten):** `scripts/consistency-check.py:52-56`
importiert genau `check_readme_docs_index`, `check_sync_cli_docs`, `check_ui_help_mappings`; die
Aufrufe stehen in `run_checks()` `:199-201`. `tests/test_doc_facts.py` referenziert über
`from scripts.lib.consistency import docs as docs_lib` (`:90`) genau: `check_no_manual_counts`
(`:2244`), `Severity` (`:2279`, `:2440`, `:2484`, `:2487`, `:2545`, `:2556`, `:2563`, `:2655`,
`:2685`), `V1_SCAN_RELPATHS` (`:2457`), `v1a_count_spans` / `v1b_version_spans` (`:2463-2464`),
`check_sync_cli_docs` / `check_ui_help_mappings` / `check_readme_docs_index` (`:2533-2563`),
`check_internal_links` (`:2649-2853`), `V3_INERT_PREFIXES` (`:2799`). **Kein** weiterer Name wird
von außen referenziert; `tests/test_doc_facts_expected.py` importiert `docs` **nicht** (es bindet
ausschließlich `scripts.lib.doc_facts`, `:58-59`). **Damit ist der Fassaden-Contract vollständig
aus der Ist-Nutzung abgeleitet und nicht aus einer Vermutung** (K19).

> **Rev. 0.7 / E-7 — der V5-Eintrag des `__all__` bleibt unverändert, nur sein Herkunftsmodul
> ändert sich.** `"check_role_generation_parity"` (`# W2-4 (docs_freshness)`) ist **nach E-7** in
> **`docs_freshness_v5.py`** beheimatet. **Am `__all__`-Vertrag ändert sich damit nichts**: der Name
> wird von der Fassade **weiter** durchgereicht, nur aus einem anderen Modul importiert. **Wer den
> V5-Eintrag schreibt, bleibt W2-7** (K46-Negativregel: W2-4 fasst `docs.py` **nicht** an) —
> dieselbe Regel wie für V2/V6/V7. **Konsequenz für die Zwischenphase:** zwischen **W2-4** (V5
> implementiert) und **W2-7** (`__all__`-Inkrement) ist V5 **nur modulweise** aufrufbar, nicht über
> die Fassade; das ist der dokumentierte Normalfall des Musters und **kein** Fehlerzustand.

**K28 (Rev. 0.6, Concept-Review) — `check_spec_plan_path_convention` (V8) war in der Fassung vor
dieser Korrekturrunde nicht im `__all__`.** Das ist ein **Lückenfehler**: V8 liegt in
`docs_wiki.py` (§4.1) und wird von **W6-2** registriert — **ebenso wie alle anderen Checks über die
Fassade** (Plan W2-7 Schritt 2, IC-05-Konvention). Fehlte der Name, könnte W6-2 den Check nicht
importieren. **Ergänzt** (siehe Liste oben), mit Herkunftskommentar `# W6-2 (docs_wiki)`. **Die
Vollständigkeitsaussage dieses Absatzes gilt damit als wiederhergestellt:** für **jeden** der neun
V-Checks und die drei Altchecks enthält `__all__` genau einen importierbaren Namen.

---

## 5. Interface Contracts

Alle neuen Module sind **stdlib-only** und folgen der Dependency-Invariante
`scripts/lib/variables.py:9-17` (keine Zyklen, neutraler Boden unten). Docstrings, Naming
(snake_case) und `from __future__ import annotations` folgen `scripts/lib/spec_plan_scaffold.py:12`.

### 5.1 Modul M1 — DocFacts

#### IC-01 — `scripts/lib/doc_facts.py` (neu): Faktum-API

```python
# scripts/lib/doc_facts.py
"""Berechnet die DOCS_*-Fakten aus den kanonischen Quellen (SSoT je Faktumklasse).

Neutrales Blatt: kennt keine Doku-Datei, liest keine Handprosa, schreibt nichts.
Alle nicht berechenbaren Faktuen ergeben "" (fail-soft, identisch zum
_load_block_snippet-Vertrag, config.py:1850-1851).
"""
from __future__ import annotations

from pathlib import Path

# Exklusionsregeln Hook-Zaehlung — kodieren die README:501-vs-:696-Widerspruechlichkeit
# strukturell (Design §3.2), nicht per Korrektur. Die beiden Regeln sind KEINE
# Alternativen, sondern gelten fuer verschiedene Fragen (siehe Aufloesung M1).
# ACHTUNG (rev. 0.3, NF-12): die Suffix-Regel muss "-impl.sh" (Bindestrich) lauten, nicht
# "_impl.sh" — die Dateien heissen `orchestrator-guard-impl.sh` / `repo-containment-impl.sh`
# (verifiziert per Glob). Mit "_impl.sh" wuerde die Regel nichts matchen und DOCS_HOOKS_COUNT
# liefe auf 13 statt 11.
HOOK_EXCLUDED_DIRS: frozenset[str] = frozenset({"lib", "release-gates"})
HOOK_EXCLUDED_SUFFIXES: tuple[str, ...] = ("-impl.sh",)
AGENT_HELPER_PREFIX: str = "_"

def compute_doc_facts(
    agent_meta_root: Path,
    config: dict,
    *,
    provider_config: dict | None = None,
    log=None,
) -> dict[str, str]:
    """Return the full DOCS_* fact dict. Never raises on a missing source."""
```

**Fehlerpfade:** `agent_meta_root` existiert nicht → alle Faktuen `""` plus ein
`log.debug`-Eintrag (kein Abbruch). Eine einzelne Quelle ist unlesbar → nur dieses Faktum
`""`. **Kein** `SyncError` — der Generator darf nie einen Sync wegen einer Zahl abbrechen.

**M1-Auflösung (verbindlich, rev. 0.3):** `HOOK_EXCLUDED_DIRS` und `HOOK_EXCLUDED_SUFFIXES` werden
**beide** angewandt — aber auf **zwei verschiedene, je Frage und je Zielstelle benannte**
Faktum-Keys. Damit entfällt die Frage „welche Zahl gilt?" **und** die Frage „welche Zahl gehört an
diese Zeile?":

| Key | Regel | VERIFIED 2026-09-26 | Beantwortet | Einzige Zielstelle |
|---|---|---|---|---|
| `DOCS_HOOKS_COUNT` | `hooks/**/*.sh` **ohne** `lib`, **ohne** `release-gates`, **ohne** `*-impl.sh` | **11** | „Wie viele Hooks werden registriert und an alle Provider propagiert?" — die Frage, die die **Überschrift** `README.md:501` stellt | `README.md:501` |
| `DOCS_HOOKS_1GENERIC_COUNT` | `hooks/1-generic/*.sh` (**nicht-rekursiv**, wie der Collector) **ohne** `*-impl.sh` | **9** | „Wie viele Hook-Skripte liegen in dem Verzeichnis, das diese Zeile **namentlich** nennt?" — die Frage, die die **Tree-Zeile** `README.md:696` stellt | `README.md:696` |

**Warum zwei Keys und nicht einer (rev. 0.3, NEW-1).** Die beiden Zielstellen stellen zwei
verschiedene Fragen, und Rev. 0.2 hat sie mit einem globalen Key beantwortet, der an der zweiten
Stelle **semantisch nicht passt**:

- `README.md:501` liegt in der **Hooks-Sektion** und fragt nach der **Anzahl** der Hooks, die an
  alle Provider propagiert werden — eine Aussage über den **gesamten** `hooks/`-Baum. Hier ist **11**
  richtig: 2 `0-external/` + 11 top-level `1-generic/` − 2 `*-impl.sh`. Die Registrierung dieser
  11 erfolgt durch `sync_hooks()`, das `0-external` (`:95-98`) und `1-generic` (`:101-104`)
  nicht-rekursiv je Layer sammelt und `2-platform`-Overrides darüber legt (`hooks/2-platform/`
  enthält heute nur `.gitkeep`).
- `README.md:696` ist eine **Zeile im Verzeichnisbaum** und nennt den Pfad `hooks/1-generic/`
  selbst. Ihre Zahl kann daher nur eine Eigenschaft **dieses Verzeichnisses** sein. Der
  17er-Wert zählt `hooks/**` und hätte dort eine Zahl über einen anderen Pfad behauptet — genau
  die F19/F22-Fehlerklasse („Zahl steht an einer Stelle, gilt aber für eine andere"). Echte
  `.sh`-Dateien in `hooks/1-generic/` auf Top-Level sind **11**; zwei davon sind
  `*-impl.sh`-Geschwister von `orchestrator-guard.sh` / `repo-containment.sh` (Helper, keine
  Hooks — dieselbe Einstufung wie in `DOCS_HOOKS_COUNT`, konsistent mit
  `consistency/repo_containment.py:22` „hook wrapper/impl"). Also **9**.

**Verbindliche Renderform (keine Auslegungsspielräume):**

- `README.md:501` → `## Hooks ({{DOCS_HOOKS_COUNT}} hooks, propagated to all providers)`
- `README.md:696` → `hooks/1-generic/               # {{DOCS_HOOKS_1GENERIC_COUNT}} hook scripts (+2 *-impl.sh helpers)`
  Der Klammerzuschlag ist **verpflichtend**, weil er den Dateizähler (11) vom Hook-Zähler (9)
  unterscheidet; ohne ihn wäre die Zeile mit `ls hooks/1-generic/*.sh | wc -l` nicht
  reproduzierbar.

**Ausdrücklich gestrichen (rev. 0.3):** `DOCS_HOOK_SCRIPT_FILES_COUNT == 17` aus Rev. 0.2. Die 17
bleiben eine **Belegzahl in §1.1 (F3)** und in §16, sind aber **kein `DOCS_*`-Faktum**: es gibt
keine README-Zeile, die „alle Hook-Skript-Dateien im Repo" behauptet, und ein Faktum ohne
Zielstelle wäre eine zweite, ungeprüfte Zahl in genau der Datei, die diese Spec bereinigen soll.
Ein späteres Bedürfnis nach dieser Zahl (z. B. `docs/INDEX.md`) braucht eine eigene, neu
verifizierte Zielstelle — nicht die Wiederverwendung dieser Zahl.

**Kreuz-Rendering ist verboten:** `DOCS_HOOKS_COUNT` wird **nicht** in `README.md:696` gerendert
und `DOCS_HOOKS_1GENERIC_COUNT` **nicht** in `README.md:501`. Die früher widersprüchliche
Doppelangabe („7" vs. „5") entsteht dann nicht mehr, weil zwei verschiedene Fragen zwei
verschiedene Keys **mit je eigener Zielstelle** bekommen.

#### IC-02 — Faktum-Vertrag (Platzhalter → Quelle → Formel)

Alle Werte sind **Strings**. `volatile: true` markiert Faktuen, die in `README.md` und
`llms.txt` **nicht** gerendert werden dürfen (R1).

| Platzhalter | Quelle (kanonisch) | Berechnungsregel | `volatile` |
|---|---|---|---|
| `DOCS_VERSION` | `VERSION` via `read_version()` (`config.py:1060-1064`) | exakter Dateiinhalt, `strip()` | nein |
| `DOCS_AGENT_TEMPLATES_COUNT` | `agents/1-generic/*.md` | Anzahl Dateien mit Frontmatter-`name`, ohne `_*`-Präfix (VERIFIED heute: 80) | nein |
| `DOCS_AGENTS_SE_COUNT` | dito | Teilmenge mit Namenspräfix `se-` (VERIFIED heute: 14) | nein |
| `DOCS_AGENTS_NONSE_COUNT` | dito | Differenz (VERIFIED heute: 66) | nein |
| `DOCS_AGENTS_ACTIVE_COUNT` | `roles:` (`project.yaml:92-150`) ∩ Templates ∩ `resolve_activation_gates()` (`roles.py:129`) | `len(...)` — **nicht** `len(roles)`, um F13/F21 nicht zu reproduzieren | nein |
| `DOCS_HOOKS_COUNT` | `hooks/**/*.sh` | `HOOK_EXCLUDED_DIRS` **und** `HOOK_EXCLUDED_SUFFIXES` (VERIFIED heute: **11**); renders **ausschließlich** in `README.md:501` | nein |
| `DOCS_HOOKS_1GENERIC_COUNT` | `hooks/1-generic/*.sh` (nicht-rekursiv) | `HOOK_EXCLUDED_SUFFIXES` (VERIFIED heute: **9**); renders **ausschließlich** in `README.md:696` | nein |
| `DOCS_PROVIDER_COUNT` | `config/ai-providers.yaml:1` | `len(data["providers"])` (VERIFIED heute: 9) | nein |
| `DOCS_PIPELINES_COUNT` | `config/role-defaults.yaml:2489` | Top-Level-Keys unter `quality_pipelines:` — **inkl.** disabled (VERIFIED heute: **8**) | nein |
| `DOCS_PIPELINES_ACTIVE_COUNT` | dito ∩ `project.yaml:339-343` | nur `enabled != false` **nach** Merge der `quality-pipelines.overrides` (VERIFIED heute: **7 von 8**) | nein |
| `DOCS_DOD_PRESET_COUNT` | `config/dod-presets.yaml:12` | `len(presets)` (VERIFIED heute: **7**) | nein |
| `DOCS_TIER_PRESET_COUNT` | `config/tier-presets.yaml` | Top-Level-Keys (VERIFIED heute: **5** — Korrektur von Rev. 0.1, das fälschlich 4 behauptete) | nein |
| `DOCS_COMMAND_COUNT` | `commands/1-generic/` | Anzahl `*.md` | nein |
| `DOCS_SCENARIO_COUNT` | `tests/scenarios/asserts/*.sh` (VERIFIED heute: 63) | `len(glob("*.sh"))` — **nicht** `tests/scenarios/*.md` (dort liegt nur `registry.md`) | **ja** |
| `DOCS_DOCS_FILE_COUNT` | `docs/**/*.md` | ohne Pfadsegment `_archive` / `archive` | nein |
| `DOCS_AGENT_ROSTER_BLOCK` | Templates + `config/role-defaults.yaml` | Markdown-Tabelle, eine Zeile je Rolle | nein |
| `DOCS_PIPELINES_BLOCK` | dito | Tabelle **mit** Enabled-Spalte | nein |
| `DOCS_HOOKS_BLOCK` | `hooks/**/*.sh` | Tabelle Hook/Trigger/Pfad | nein |
| `DOCS_PROVIDERS_BLOCK` | `config/ai-providers.yaml` | Tabelle Provider/Verzeichnis/Capabilities | nein |
| `DOCS_TIER_PRESET_BLOCK` | `config/tier-presets.yaml` | Tabelle Tier/Modell (5 Zeilen) | nein |
| `DOCS_DOD_PRESET_BLOCK` | `config/dod-presets.yaml` | Tabelle Preset/Begründung (7 Zeilen) | nein |
| `DOCS_REPO_FACTS_BLOCK` | alle obigen **ohne** volatile | kompakter Faktenblock für `llms.txt` | nein |

**Schlüsselzahl: 23** (17 Skalar + 6 `*_BLOCK`). `DOCS_TIER_PRESET_COUNT` und
`DOCS_DOD_PRESET_COUNT` bleiben **beide** erhalten: F22 (DoD) ist ein Drift-Befund, F19
(Tier) war keiner — die Zahl wird unabhängig vom Befundstatus berechnet, weil ein SSoT-Faktum
nicht davon abhängt, ob die heutige Doku gerade richtig oder falsch ist.

**Nicht im Namespace:** `DOCS_LANGUAGE` und `INTERNAL_DOCS_LANGUAGE` sind **bereits**
existierende Built-ins (`.meta-config/project.yaml:183-184`) und dürfen **nicht** von
`doc_facts.py` belegt oder überschrieben werden. Namensraum-Disziplin: `*_BLOCK` ist belegt
(`QUALITY_PIPELINES_BLOCK`, `config.py:1882`); alle neuen Namen tragen zwingend `DOCS_`-Präfix.

#### IC-03 — `scripts/lib/doc_facts.py` :: Staleness-Resolver (gate-bewusst)

```python
def compute_wiki_staleness(wiki_root: Path, project_root: Path) -> dict[str, str]:
    """Map rel-wiki-page-path -> computed status tag ("" = fresh).

    status:stale-source  iff mtime(derived-from target) > derived-at
    status:age-<n>d      iff floor((now - derived-at).days) == n  (observation, not a status)
    """
```

- `type: Architecture` **ohne** `derived-from` → Ergebnis `"missing-derived-from"`; dieser
  Wert ist die V7-ERROR-Quelle (siehe IC-05).
- `status:stale-upstream` (aktuell manuell gepflegt, `knowledge/wiki/index.md:24`) bleibt als
  historisches Tag **erhalten**, wird aber nicht mehr manuell gepflegt, sondern maschinell
  extrahiert. **Quelle ist `docs/architecture/00-overview-full.md` — NICHT `ARCHITECTURE.md`**:
  `knowledge/wiki/index.md:24` beschreibt die Wiki-Seite `concepts/architecture.md` als
  „Rohkopie von **ARCHITECTURE.full.md**", und `ARCHITECTURE.md:3` („Repo version: **0.92.0**
  — content last substantively reviewed: 2026-07-20") ist lediglich der **Stub**, der auf die
  Langfassung verweist. Nach M-1 wandert der Text in die Langfassung, nach M-2 verschwindet er
  aus dem Stub ⇒ liest man weiter aus dem Stub, ist die Quelle nach W4 **weg** und V7 bekäme
  keinen Träger (das ist der Zirkelschluss aus M5). Deshalb wandert die Extraktionsquelle mit
  (M-7 in IC-17) und AC-29 prüft beide Seiten getrennt.

#### IC-04 — `scripts/lib/doc_facts.py` :: aktive-Rollen-Menge (F13/F21-Korrektur)

```python
def compute_active_roles(
    agent_meta_root: Path, config: dict, provider_config: dict | None = None
) -> set[str]:
    """Rollen, die sync.py in mindestens einem aktiven Provider-Verzeichnis erzeugt.

    = set(config["roles"]) & {template name in agents/1-generic/}
      & {r for r in ... if is_role_enabled(r, resolve_activation_gates(agent_meta_root, config))}
      & {r for r in ... if provider supports agents for at least one active provider}
    """
```

Hintergrund: `se-component-requirements` ist in `roles:` **enthalten**
(`.meta-config/project.yaml:148`) und wird dennoch nicht erzeugt, weil
`systems-engineering.enabled: false` (`project.yaml:12-13`) den Aktivierungs-Gate schließt
(`scripts/lib/agent_sync.py:548`, `scripts/lib/roles.py:129`). Ein Check auf
`roles ⊄ generiert` ohne Gate-Auswertung ist daher ein **Dauerfehlalarm** (F21) — die
Vergleichsmenge muss `compute_active_roles()` sein.

#### IC-05 — `scripts/lib/consistency/docs.py` (erweitert): Checks V1–V9

Bestehende drei Checks bleiben **unverändert** in Signatur und Severity
(`check_sync_cli_docs` `:9`, `check_ui_help_mappings` `:47`, `check_readme_docs_index` `:100`).
**Signatur der drei Altchecks, gemessen (K59 / RVW-7-01, Korrekturrunde 5 — hiermit erstmals
festgeschrieben, statt sie aus der Form der neuen Checks abzuleiten):** **jeweils
`(root: Path) -> list[Finding]`, einargumentig** — `check_readme_docs_index` heute
`docs_links.py:167`, Docstring `:170-172` („the parameter list stays `(root)`"), Testpin
`tests/test_doc_index.py` per `inspect.signature` (Parameterliste `== ["root"]`). **Die Form
`(root, config=None)` im Folgenden gilt ausschließlich den **neun neuen** Checks** und ist **kein**
IC-05-Pin für die drei Altchecks.
Neu kommen neun Checks mit der Signatur `check_*(root: Path, config: dict | None = None) -> list[Finding]`
und `check="docs.<name>"`:

| # | Check | Erkennt | Severity | Gate | Start |
|---|---|---|---|---|---|
| V1 | `check_no_manual_counts` | **zwei Branches, siehe §5.1.1** — V1a Count-Branch, V1b Versions-Branch | F1, F2, F3 ×2, F4, F14 ×3, F22 | ERROR | **W2: WARNING**, nach W3: ERROR |
| V2 | `check_docs_index_completeness` | jede getrackte `docs/**/*.md` (ohne `archive/`, `_archive/`, ohne `docs/INDEX.md` selbst) fehlt in `docs/INDEX.md` | F8, F15, F20 | ERROR | W3 |
| V3 | `check_internal_links` | relative Markdown-Links in `docs/**`, `README.md`, `llms.txt` auf nicht existierende Ziele (ohne `#anchor`-Prüfung, ohne `http(s)://`, ohne `mailto:`) | F15 | ERROR | W2 |
| V4 | `check_readme_docs_index` (**umgefasst, Rev. 0.7 / E-5**) | **README-Index-Scope** (Rev. 0.7): die `##`-Region `Documentation Index` in `README.md` wird gelesen; **jede dort deklarierte `docs/`-Kategorie** muss (a) ein existierendes Verzeichnis sein und (b) **mindestens einen** `docs/<kategorie>/…`-**Link** in der Region tragen. **Nicht** gefordert: Verlinkung **aller** 205 nicht-Archiv-`docs/**.md` — das ist **V2s** Zuständigkeit (`docs/INDEX.md`). Die bisherige Teilmenge `docs/api/*.md` bleibt eine **echte** Teilmenge (alle sieben Seiten sind in `README.md:362-373` verlinkt) | F8, F23 | ERROR (unverändert) | W2 (Registrierung W2-7) |
| V5 | `check_role_generation_parity` | `compute_active_roles()` (IC-04) ⊄ erzeugte Provider-Agent-Dateien | F13, F21 | **ERROR, sobald** `systems-engineering.enabled: true`; sonst WARNING | W2 |
| V6 | `check_docs_facts_fresh` | (a) gerenderter `DOCS_*`-Block ≠ `compute_doc_facts()` **oder** (b) `compute_doc_facts()` ≠ Sollwert aus IC-23 | Handedit-Drift **oder** Formel-Drift | ERROR | W2 |
| V7 | `check_wiki_staleness` | Wiki-Seite mit `derived-from` älter als die Quelle, oder `type: Architecture` ohne `derived-from` | F5, F10, F11 | WARNING | W2 |
| V8 | `check_spec_plan_path_convention` | Spec/Plan außerhalb `docs/{specs,plans,spikes}` bzw. nicht unter `archive/` | F7, F16 | WARNING | W6 |
| V9 | `check_stale_backups` | `*.sync-backup-*` (`.gitignore:22`) in Provider-Verzeichnissen älter als N Tage | 179 Altlasten | WARNING (lokal, gitignored) | W8 |

**Hinweis zu V9 (RVW2-4, dritte Korrekturrunde — Präzisierung, keine Änderung der Zeile):** die
Spaltenangabe „**179 Altlasten**" ist eine **Bestandsangabe** aus dem System-Design und **kein
Sollwert**: die Dateien liegen unter `.claude/agents/` und sind **gitignoriert**
(`.gitignore:13`, `.gitignore:22`), der Zählwert ist im Working Tree deshalb **nicht messbar** und
in jeder anderen Umgebung ein anderer. **Verbindlich ist regelbasiert:** (a) V9 **meldet** den
Altbestand und wird ihn **nicht** abräumen (FI-10); (b) die Task **W8-4** nimmt **vor** der
Implementierung eine Bestandsaufnahme als `BACKUP-BASELINE` auf; (c) die **Obergrenze** wird erst
**danach** festgeschrieben — als Artefakt des **W8-4-Review-Protokolls** (`V9-OBERGRENZE`),
**nicht** als Sollwert in dieser Spec (RVW3-6: die ausführende Task trägt hier keinen neuen Sollwert
ein); (d) ein Anstieg durch **eigene** neue Backups des
Vorhabens (Drift-Store, W7-3) ist **erlaubt** und kein Befund. Die **Altersschwelle N** ist **kein**
Config-Key (IC-22 fixiert **sechs** Keys; der Schema-Block `docs-consolidation` ist geschlossen,
`config/project-config.schema.json:2421-2470`, `additionalProperties: false`) — sie ist eine
**Modulkonstante** in `scripts/lib/consistency/docs.py` (Muster `V1_SCAN_RELPATHS`,
`docs.py:158`); ihr **Wert** wird in W8-4 festgelegt und ist hier **nicht** vorweggenommen.

**V1-Common-Gate (verbindlich, neu):** Jeder der neun Checks ist ein **No-op**, wenn
`docs-consolidation.enabled` nicht `true` ist. Begründung: identische Absenz-Semantik wie der
Generator (IC-22) — sonst feuern die Checks in Consumer-Projekten, deren `docs/` nicht
agent-meta gehört (NFA-04, R17), **und** in allen 63 Szenario-Fixtures, die den Key nicht
setzen (AC-38). Kein „agent-meta-Eigenerkennung\"-Heuristik-Gate.

#### 5.1.1 V1-Erkennungsregel (verbindlich; ersetzt die Rev.-0.1-Regex vollständig)

Die Rev.-0.1-Regex
`^\s*\|?\s*(\d+)\s+(agents?|hooks?|providers?|pipelines?|presets?|configs?|templates?|tiers?|szenarien?)\b`
matchte **keine** der sechs in IC-05 genannten Fundstellen (K1). Sie wird durch **zwei
disjunkte Branches** ersetzt, die an den verifizierten Zitatzeilen kalibriert sind.

**Gemeinsame Suppression (vor beiden Branches):**

1. Zeile liegt **innerhalb** einer `agent-meta:docs-begin`…`agent-meta:docs-end`-Region.
2. Zeile trägt irgendwo einen `agent-meta:docs-exempt`-Marker.
3. Zeile liegt **innerhalb** eines Markdown-Fenced-Code-Blocks (` ``` ` oder `~~~`) der
   geprüften Datei.
4. Datei ist selbst generiert (`docs/INDEX.md`).

**Präzisierung Rev. 0.5 zu Suppressionsregel 3 (K16) — der Widerspruch zu IC-05 wird
aufgelöst, die Regel selbst bleibt in Kraft.** Regel 3 unterdrückt **heute jede** Zeile eines
Fenced-Blocks. IC-05 verlangt von V1 aber ausdrücklich die Abdeckung der Fundstellen **F2**
(`README.md` dod-/tier-presets), **F3-Site-2** (`ai-providers.yaml`) und **F4**
(`VERSION`-Zeile) — und genau diese drei Stellen liegen im Ist-Zustand **im Directory-Structure-
Fence** (`README.md:680` öffnet, `:737` schließt; Fundstellen `:688`, `:690`, `:696`, `:734`).
Regel 3 und IC-05 sind damit **unvereinbar**, solange V1 die Zahlen nicht sieht. **Verbindlich
neu:** V1 **muss** F2, F3-Site-2 und F4 melden können; die dafür nötige Eingrenzung von
Regel 3 ist eine **benannte, terminierte Umsetzungsaufgabe** (Plan Rev. 0.5, Task **W2-1**,
Schritt 4) mit Owner `developer` — **nicht** eine stillschweigende Lockerung. **Unverändert
bleiben:** die Negativ-Fixture AC-08 — der Fence-Fall `## Hooks (7 hooks)` muss weiterhin
**kein** Finding erzeugen; und die Positiv-Fixture AC-07 (4 Befunde, `line` 1/2/3/4). Die
Umsetzung darf den Mechanismus wählen, muss aber **beide** Fixtures grün halten und die
Sichtbarkeit der vier genannten Fundstellen belegen (negativer Nachweis: gegen die
unmarkierte Ist-Fassung meldet V1 je Fundstelle **mindestens einen**
`docs.no_manual_counts`-Befund). **Reihenfolgebindung:** diese Sichtbarkeit muss stehen,
**bevor** `docs-consolidation.checks.strict: true` V1 auf `ERROR` hochstuft (W3-4) — sonst
wird der erste ERROR-Befund einer Spezifikationslücke geschuldet und nicht einem Drift.
**Abbildung im Plan (RVW-4, 2026-09-26):** die Bindung ist als **DAG-Kante `W2-1 → W3-4`**
geführt (Reihenfolge-/Abhängigkeitsmatrix, Wellen-Tabelle, PG-2-Diagramm) — eine
**Vorwärts**kante über die Wellengrenze, **kein** Zyklus. **Abgrenzung (RVW-7):** diese
Reihenfolgebindung ist **kein** Bestandteil des Design-Risikos **R4** (§12.1) und wird dort
**nicht** nachgetragen; R4 behandelt die Fehlalarm-Ursache der Nomen-Whitelist, nicht die
Hochstufungsreihenfolge.

**Branch V1a — „gezählte Sache"** (deckt F1, F2, F3 ×2, F14 ×3, F22):

- Ein **Zahl-Token** `\b\d{1,4}\b`, das **nicht** Bestandteil eines `\d+\.\d+`-Tokens ist
  (⇒ `1.0.0` ist keine Zählung).
- Auf **derselben Zeile** steht ein **Nomen aus der Whitelist** (case-insensitive, optionaler
  Plural):
  `agent(s) | hook(s) | provider(s) | pipeline(s) | preset(s) | tier(s) | template(s) |
  config(s) | command(s) | scenario(s) | szenario(sien) | role(s) | skill(s) | rule(s) | test(s)`.
- **Abstandsregel:** höchstens **3 Tokens** zwischen Zahl und Nomen (erlaubt Adjektive wie
  „Generic", „DoD"; verhindert, dass ein Zähler zwei Sätze später greift).
- Der Finding nennt `branch="V1a"`, `file`, `line`, das Zahl-Token und das Nomen.

**Branch V1b — „Versions-Literal"** (deckt F4):

- Ein Semver-artiges Literal `\b\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?\b` auf einer Zeile, die
  zusätzlich `version` (case-insensitive) enthält.
- Begründung der Trennung: `VERSION  # Current version (v1.0.0)` enthält **keine** Ganzzahl
  und würde von V1a **nicht** erfasst. V1a pauschal auf Versionszeilen anzuwenden erzeugt
  dagegen Fehlalarme in Changelog, `docs/api/cli-reference.md` und
  `docs/specs/**` (dort stehen Versionsangaben legitim). Der Finding nennt `branch="V1b"`.

**Positiv-Fixture (verbindlich, wörtlich):** `tests/fixtures/docs_v1_fixtures.md` enthält
mindestens diese vier Zeilen, **1:1 aus `README.md`** inklusive `##`-Prefix und
Einrückung — damit ist der Heading-Fall belegt, den Rev. 0.1 nicht abgedeckt hat:

```markdown
## Agent Roster — 74 Generic Agents
## Hooks (7 hooks, propagated to all providers)
  ai-providers.yaml          # 6 provider configs (Claude, Gemini, Opencode, Continue, Copilot, Mammouth)
VERSION                      # Current version (v1.0.0)
```

Erwartung: **4 Findings**, alle `severity=WARNING`, `check="docs.no_manual_counts"`, `file`
= Fixture-Pfad, `line` = 1/2/3/4, `branch` = `V1a` für 1–3 und `V1b` für 4.
Mit `docs-consolidation.checks.strict: true` sind alle vier `Severity.ERROR`.

**Negativ-Fixture (verbindlich, wörtlich):** `tests/fixtures/docs_v1_fixtures.md` enthält
zusätzlich je einen Fall pro Suppression:

```markdown
<!-- agent-meta:docs-begin facts -->
| Agents | 74 |
<!-- agent-meta:docs-end facts -->

## Agent Roster — 74 Generic Agents <!-- agent-meta:docs-exempt: Beispiel -->

```text
## Hooks (7 hooks)
```

- `74` **innerhalb** einer `docs-*-Region` ⇒ kein Finding
- `74` mit `docs-exempt`-Marker ⇒ kein Finding
- `7` **innerhalb** eines Fenced-Code-Blocks ⇒ kein Finding
- eine Zeile `| Agents | 74 |` außerhalb jeder Region **innerhalb der Fixture** ⇒ **1 Finding**
  (Gegenprobe: das Nomen steht hier **vor** der Zahl, die Abstandsregel greift in beide
  Richtungen)

Erwartung Negativ-Teil: **genau 1 Finding** (die Gegenprobe), sonst 0.

**V1-Anti-Pattern (verbindlich, unverändert):** V1a/V1b prüfen **nicht die Zahl**, sondern die
**Abwesenheit einer Marker-Region an dieser Stelle**. Ein Autor muss eine Zahl entweder
generieren lassen oder die Zeile bewusst als
`<!-- agent-meta:docs-exempt: <grund> -->`
markieren. Damit bleibt `README.md:689` („5 tier presets", **korrekt**) exempt-fähig, ohne
Regex-Hexerei. **Kein stilles Durchwinken.**

**Registrierung:** `scripts/consistency-check.py:52-56` (Import-Block `lib.consistency.docs`)
wird um die neun Namen erweitert; der Aufruf erfolgt in der bestehenden `run_checks()`-Liste.
Die bestehende Importform (`from lib.consistency.docs import (...)`, `:52-56`) bleibt
namensgleich. **Exit-Codes** (Modul-Docstring `:23-26`): `0` = keine Errors (Warnings
erlaubt, außer `--strict`), `1` ≥ 1 Error, `2` Skriptfehler — unverändert.

#### IC-06 — `scripts/lib/consistency/placeholders.py` :: Namespace-Registrierung

```python
# scripts/lib/consistency/placeholders.py
_DYNAMIC_PREFIXES: tuple[re.Pattern, ...] = (
    re.compile(r'^PAL_[A-Z0-9_]+$'),
    re.compile(r'^PIPELINE_[A-Z0-9_]+_(BLOCK|PROVIDER_BLOCKS)$'),
    re.compile(r'^DOCS_[A-Z0-9_]+$'),          # NEU — IC-02-Namensraum
)
```

**Korrektur zum Design (siehe §13-A3):** `check_placeholders` erzeugt für unbekannte Namen
`Severity.WARNING` (`:177-182`), **nicht** ERROR. Ein nicht aufgelöstes `{{DOCS_*}}` ist daher
**kein** Fehler-Gate; das Fehler-Gate ist **V6**. Die Spec verlässt sich auf V6, nicht auf
eine (nicht existierende) ERROR-Stufe.

### 5.2 Modul M2 — Renderer, Indexer, Brücke

#### IC-07 — `scripts/lib/doc_renderer.py` (neu): Rendering-API

```python
# scripts/lib/doc_renderer.py
"""Rendert docs/INDEX.md (Volltext) und DOCS_*-Faktenbloecke in Marker-Regionen."""
from __future__ import annotations

DOCS_BLOCK_RE = re.compile(
    r"(<!--\s*agent-meta:docs-begin\s+(?P<region>[a-z0-9-]+)\s*-->)(?P<body>.*?)"
    r"(<!--\s*agent-meta:docs-end\s+(?P=region)\s*-->)",
    re.DOTALL,
)
"""Marker-Paar je Region. Form folgt context.py:36-39 (_MANAGED_BLOCK_RE, re.DOTALL)."""

def render_doc_fact_block(region: str, facts: dict[str, str]) -> str:
    """Body-Text fuer eine Region. Deterministisch, kein Zeitstempel (NFA-02)."""

def render_docs_index(index_model: dict, facts: dict[str, str]) -> str:
    """Volltext docs/INDEX.md inkl. Fakten-Footer (IC-14)."""

def apply_fact_blocks(text: str, facts: dict[str, str], log=None) -> str:
    """Ersetze den Body jeder DOCS_BLOCK_RE-Region. Fehlende Region -> unveraendert."""
```

**Fehlerpfade:** Eine `docs-begin`-Region ohne zugehöriges `docs-end` → `text` bleibt
unverändert **plus** `log.warning("docs", "unbalanced marker region '<region>'")`; kein
Abbruch, kein Halbschreiben. Zwei Regionen gleichen Namens → nur die **erste** wird
ersetzt (`count=1`, Muster `context.py:42-50`), die zweite erzeugt eine Warnung.
**Leere Fact-Werte:** rendert `<!-- agent-meta:docs-empty: <name> -->` anstelle einer
leeren Zeile (kein stilles Leerzeichen-Rauschen im Diff).

#### IC-08 — Marker-Syntax in `README.md` (Hybrid-Modus)

```
<!-- agent-meta:docs-begin facts -->
…generiert…
<!-- agent-meta:docs-end facts -->
```

Erlaubte Regionsnamen: `facts`, `roster`, `pipelines`, `hooks`, `providers`, `version`.
**Eigener Namespace** neben `agent-meta:managed-begin/end` (`context.py:36-38`,
`context.py:1264-1265`, `cli_commands.py:95-96`): `docs-*` ≠ `managed-*` ⇒ keine Kollision.
VERIFIED: `README.md` enthält **keinen** `agent-meta:managed-*`-Marker ⇒ die Doku-Region
kann nicht in eine Kontext-Region hineinlaufen. `.gitignore`-Managed-Block
(`context.py:294-295`) bleibt unverändert, weil `README.md`/`docs/INDEX.md` **keine**
Provider-Dateien sind (§7.1 des Designs).

#### IC-09 — `scripts/lib/doc_index.py` (neu): Docs-Baum-Modell

```python
# scripts/lib/doc_index.py
"""Baut den Doku-Baum + 1-Zeilen-Beschreibungen. Einzige Komponente, die
Doku-Dateisystem-Semantik kennt — darf NICHT nach Doku-Pfaden in doc_facts.py dupliziert werden."""
from __future__ import annotations

EXCLUDED_DIR_SEGMENTS: frozenset[str] = frozenset({"archive", "_archive", "local-Inputs"})
DESCRIPTION_MAX_CHARS: int = 120

def build_index_model(project_root: Path) -> dict:
    """{'root': rel, 'entries': [{'path', 'title', 'description', 'kind', 'depth'}]}"""
```

- `title`: erstes `# `-Heading, sonst Dateiname ohne Endung.
- `description`: Frontmatter-`description`, auf `DESCRIPTION_MAX_CHARS` gekürzt mit `…`;
  **Fallback**: `""` → der Renderer schreibt `—`. Kein erfundener Text.
- `kind`: `architecture|api|providers|guides|specs|plans|spikes|concepts|se-cascade|other`.
- Sortierung: `kind`-Reihenfolge aus §3.2, dann `path` aufsteigend — deterministisch, damit
  der Diff stabil bleibt (NFA-02).
- **Zweimal laufend auf demselben Baum → byte-identisches Ergebnis** (NFA-01).

#### IC-10 — `docs/INDEX.md`-Format (kanonisch, 100 % generiert)

````markdown
# Documentation Index

> Generated by agent-meta `sync.py` (docs-consolidation). Do not edit by hand —
> every region below is regenerated on each sync. Hand prose lives in the pages
> this index links to.

## architecture
- [Layer Model](architecture/01-layer-model.md) — Override-Priorität der 4 Layer …

## guides
- …

<!-- agent-meta:docs-facts:begin -->
| Fact | Value |
|------|-------|
| Version | 1.2.0-beta.2 |
| Agent templates | 80 |
<!-- agent-meta:docs-facts:end -->

## volatile
<!-- agent-meta:docs-volatile:begin -->
| Scenarios | 63 |
<!-- agent-meta:docs-volatile:end -->

<!-- agent-meta:docs-footer -->
facts-hash: <sha256 über den kanonischen **nicht-volatilen** Faktum-Satz, 16 Hex-Zeichen>
generator: doc-indexer/1
<!-- /agent-meta:docs-footer -->
````

**Regeln:** (a) kein Zeitstempel (NFA-02, Muster `standalone.py:365` — dort steht die
Version, kein Datum); (b) `facts-hash` ist `sha256` über `"\\n".join(f"{k}={v}" for k in
sorted(non_volatile_facts))`, gekürzt auf 16 Zeichen — **stabil** gegenüber
Reihenfolge-Änderungen **und** gegenüber Szenario-Zahl-Änderungen (R1); (c) jeder
`docs/**/*.md`-Pfad (ohne `archive/`, `_archive/`) erscheint **genau einmal** als
Link; `docs/INDEX.md` selbst nie; (d) `docs/architecture/INDEX.md` ist eine Teil-Vorschau
auf denselben Baum (Design §1); (e) **Die Volatile-Sektion steht als letzte Sektion vor dem
Footer**, damit ein Szenario-Diff genau **eine** Zeile betrifft und der Review-Diff nicht
über die Datei springt (M7).

#### IC-11 — Snippet-Bridge in `scripts/lib/config.py` (C3, Erweiterung `:1861-1914`)

```python
# scripts/lib/config.py :: _build_snippet_variables  (bestehende Signatur unverändert)
#   _build_snippet_variables(variables: dict, agent_meta_root: Path) -> None
    # ERGÄNZUNG — neues Verzeichnis, kein Neu-Inventar des Mechanismus:
    _docs_snippets_dir = agent_meta_root / "snippets" / "docs"
    for _snippet_name, _var_stem in (
        ("repo-facts", "DOCS_REPO_FACTS"),
        ("agent-roster", "DOCS_AGENT_ROSTER"),
        ("pipelines", "DOCS_PIPELINES"),
        ("hooks", "DOCS_HOOKS"),
        ("providers", "DOCS_PROVIDERS"),
        ("tier-presets", "DOCS_TIER_PRESET"),
    ):
        _snippet_path = _docs_snippets_dir / f"{_snippet_name}.md"
        _var_name = f"{_var_stem}_BLOCK"
        variables[_var_name] = (
            _load_block_snippet(_snippet_path)
            if _snippet_path.exists() else ""
        )
```

- **`_load_block_snippet` wird wiederverwendet, nicht modifiziert** (`config.py:1842-1858`):
  Frontmatter-Strip, CRLF→LF-Normalisierung, `strip("\n")` — der kanonische
  Inlining-Transform bleibt unverändert (§7.1 des Designs).
- Die Ergänzung steht **nach** dem bestehenden `snippets/security/`-Block
  (`config.py:1923-1924`), damit die bestehende Reihenfolge der Orchestrator-/Developer-/
  Security-Snippets unangetastet bleibt.
- Die Resultate werden **vor** dem Rendern durch `doc_renderer.apply_fact_blocks()` mit den
  C1-Werten substituiert; die Substitutions-Engine ist Engine E3 des Designs
  (`substitution.py:83-93`, Keep-Policy `:86-88`), **nicht** E1/E2 — damit sind
  Doku-Platzhalter nie von Provider-Engines auflösbar (OQ5, rückwärtskompatibel).

#### IC-12 — `scripts/sync_pipeline.py` :: Doku-Stage und **Reihenfolge-Pflicht**

Neue Stage-Funktion, Muster identisch zu `_sync_stage_knowledge_and_isolation` (`:922-945`):

```python
def _sync_stage_docs_consolidation(
    agent_meta_root: Path, project_root: Path, config: dict,
    provider_config: dict, args: argparse.Namespace, log: SyncLog,
) -> None:
    """Doku-Index + DOCS_*-Faktenbloecke. Laeuft NACH scaffold_spec_plan_dirs,
    damit der Generator den KE-off-fallback nicht ueberschreibt (IC-15)."""
    try:
        sync_docs_consolidation(
            agent_meta_root, project_root, config, provider_config, log, args.dry_run,
        )
    except SyncError as exc:
        print(f"\n  !!  Docs consolidation aborted: {exc}", file=sys.stderr)
        sys.exit(1)
```

**Verbindliche Aufrufreihenfolge** (Abweichung vom Design, siehe §13-A4):

1. `_sync_stage_generated_file_drift_scan` (`sync_pipeline.py:587-620`) — **vor** jedem
   Writer, damit Handedit-Drift noch sichtbar ist.
2. `_sync_stage_knowledge_and_isolation` (`:922-945`) → darin `sync_knowledge_engine` (`:929`)
   und `scaffold_spec_plan_dirs` (`:935`).
3. **`_sync_stage_docs_consolidation` (neu) — unmittelbar nach `scaffold_spec_plan_dirs`.**
4. `_sync_stage_generated_file_hash_capture` (`:1090-1099`) — fasst den Endzustand ein.
5. `_sync_stage_auto_commit_allowlist` (`:1102`) — bleibt die letzte Stage (`:1106-1109`).

Begründung: `scaffold_spec_plan_dirs` schreibt `docs/INDEX.md` **nur** im `file-index`-Modus
(`spec_plan_scaffold.py:115-121`; **K-4:** der frühere Anker `:62-68` ist veraltet — gemessen
beginnt der Modus-Zweig bei `:115`, `scaffold_spec_plan_dirs` selbst bei `:100`). Läuft der Generator davor, überschreibt der Scaffold das
Voll-Index mit dem Skeleton (B2). Das ist die stärkere Form von C8.

#### IC-13 — Schreib-, Idempotenz- und `dry_run`-Vertrag

```python
def sync_docs_consolidation(
    agent_meta_root: Path, project_root: Path, config: dict,
    provider_config: dict, log: SyncLog, dry_run: bool,
) -> dict:
    """Return {'written': [...], 'unchanged': [...], 'skipped': [...]}."""
```

| Situation | Verhalten | Muster / Beleg |
|---|---|---|
| `docs-consolidation.enabled` **nicht** `true` — **auch bei kompletter Abwesenheit des Keys** | `log.skip("docs-consolidation", "disabled in project.yaml")`, **kein** Schreibzugriff, **keine** V1–V9-Ausführung | `knowledge.py:127-129` (`ke_config.get("enabled", False)`) — **Fail-off-Präzedenz** |
| `resolve_index_mode(config)[0] == "knowledge-engine"` (KE-Index ist autoritativ) **und** `docs-consolidation.index-owner` **nicht** `docs-consolidation` (Abwesenheits-Default `auto`, IC-25) | **kein** `docs/INDEX.md` schreiben; `skipped` + `log.note("docs-consolidation", "knowledge-engine index is authoritative")` | `doc_renderer.py:702-703` (Bedingung), `:277` (`KE_AUTHORITATIVE_REASON`); **K-4:** Anker `spec_plan_scaffold.py:40-44` → **`:80-97`** (gemessen); **Szenario 52** (`asserts/52:44` `[ ! -e "docs/INDEX.md" ]`); **AC-21**, **AC-43** (pinnt die Absenz-Semantik) |
| **`docs-consolidation.index-owner: docs-consolidation`** (agent-meta-Ausnahme, IC-25) und `index-mode` **nicht** `skeleton` | `docs/INDEX.md` wird geschrieben, **auch** bei `resolve_index_mode() == "knowledge-engine"` — die KE-Autorität gilt **nur** für Projekte **ohne** diese Deklaration; `log.note` nennt den Grund **nicht** | IC-25/IC-26; `doc_renderer.py:810-814`, `:821-824`, `:861`; **AC-42**. **Zur Freigabe ausstehend (P-1, §17.12.1)** |
| `docs-consolidation.index-owner` **weder** `auto` **noch** `docs-consolidation` | **kein** Schreibvorgang; `skipped` + **eigener** Grund `UNKNOWN_INDEX_OWNER_REASON` (fail-closed) | IC-25 Fail-closed-Zweig (1) — **die einzige *garantierte* Absicherung**: das Schema ist Autocomplete-/Tippfehler-**Konvention**, `enum` + `additionalProperties: false` (`config/project-config.schema.json:2470`) greifen **nur**, wenn `jsonschema` installiert ist; die Schema-Validierung im Sync-Pfad ist **best-effort** (`scripts/lib/config.py:342` „**if** jsonschema is available", `:388` „jsonschema not installed or validation error — best-effort", `pass`). Fehlt das Modul, bleibt allein der Codepfad. **AC-44** |
| `resolve_index_mode(config)[0] == "file-index"` und Ziel ist **nicht** das Scaffold-Skeleton | **kein** `docs/INDEX.md` schreiben; `skipped` + `log.note(..., "file-index fallback owned by scaffold")` | **Szenarien 54/55/56** (`asserts/54:27`, `asserts/55:25` `grep -q 'File-based index fallback'`) |
| `resolve_index_mode(config)[0] == "file-index"` und Ziel **ist** das Scaffold-Skeleton (Präfix-Erkennung) | Voll-Index **einmalig** ersetzen | IC-15, F20, `asserts/54:26-27` |
| Ziel existiert **nicht** (agent-meta selbst, vor W3) | Voll-Index anlegen | IC-10 |
| Zielinhalt == Istinhalt | in `unchanged`, **kein** `write_checked` | `standalone.py:386-389, :404-410` |
| Inhalt weicht ab | `write_checked(...)` + `log.action("UPDATE", rel, "docs consolidation")` | `knowledge.py:158-159` |
| `dry_run=True` | rendert, schreibt **nichts**, meldet `would-update` in `written` | `knowledge.py:153, :158`; `standalone.py:391-393` |
| Consumer ohne `docs/`-Verzeichnis | `skipped` + `log.note`; **kein** `mkdir` in Fremdprojekten | Design §3.4 |
| Faktum nicht berechenbar | Wert `""` → `docs-empty`-Marker (kein Abbruch) | IC-01 |
| Platzhalter-**Name** unbekannt | bleibt wörtlich stehen (`substitution.py:86-87`, Default-Keep) **plus** V6-ERROR | IC-05, IC-07 |
| `docs-consolidation.index-mode: skeleton` | Scaffold-Skeleton bleibt **immer** unangetastet | IC-15, AC-21 |

**Besitzregel (K5-Kern, verbindlich):** Der Generator **besitzt `docs/INDEX.md` nur dann,
wenn er sie selbst erzeugt hat** — d. h. wenn das Ziel vorher nicht existierte, **oder** wenn
es das Scaffold-Skeleton ist. Er überschreibt **nie** eine Datei, die ein anderer Writer
  legitim geschrieben hat. Ohne diese Regel hätte die Spec (mit `enabled: true` als
  Absenz-Default) in den Szenario-Fixtures — die keinen `docs-consolidation`-Key führen
  (`run.sh:46-52` kopiert `tests/scenarios/configs/*.project.yaml` unverändert nach
  `$tmp/.meta-config/project.yaml`) — den Scaffold-Skeleton mit dem Voll-Index überschrieben
  und die Szenarien 54/55/56 sowie 52 gebrochen (AC-38).
  **Die agent-meta-Ausnahme (IC-25) schwächt diese Regel nicht ab** (IC-26/3): eine fremde
  Datei ohne Scaffold-Marker und ohne `doc-indexer/1` wird auch mit
  `index-owner: docs-consolidation` **nicht** überschrieben (`doc_renderer.py:855-858`,
  `OWNERSHIP_REASON` `:255-259`); gepinnt in **AC-44**. **Zur Freigabe ausstehend (P-1,
  §17.12.1).**

#### IC-14 — Fact-Hash-Footer (Diff-Stabilität)

- Algorithmus: `sha256("\n".join(sorted(f"{k}={facts[k]}" for k in facts
  if k not in volatile_facts)))` → erste 16 Hex-Zeichen. **Volatile Fakten gehen nicht ein**
  (R1/M7: sonst erzeugt jedes neue Szenario zusätzlich einen `facts-hash`-Wechsel, der
  inhaltlich bedeutungslos ist).
- **Kein Zeitstempel, kein absoluter Pfad, keine Host-/User-Information** (Secrets-Regel und
  NFA-02). Muster `standalone.py:362-368` (dort: `Generated from agent-meta v{version}`).
- `generator: doc-indexer/1` ist eine **statische** Versions-Konstante, die nur bei einer
  bewussten Formatänderung von `1` hochgezählt wird — sonst Diff-Stabilität.

#### IC-15 — C8 Scaffold-Guard in `scripts/lib/spec_plan_scaffold.py`

```python
# scripts/lib/spec_plan_scaffold.py
DEFAULT_FALLBACK_INDEX = "docs/INDEX.md"   # :28  — bleibt identisch (K-80, RVW8-8)
_FILE_INDEX_SKELETON = "…"                  # :29  — bleibt identisch (K-80, RVW8-8)
_FILE_INDEX_SKELETON_MARKER = "File-based index fallback"   # NEU

def is_file_index_skeleton(text: str) -> bool:
    """True iff *text* ist der vom Scaffold geschriebene Skeleton (Zeilen-Brk ein-aus)."""
```

Der Generator (IC-10) ruft `is_file_index_skeleton()` **vor** dem Schreiben. Ist das Ziel ein
Skeleton **und** ist `docs-consolidation.index-mode: full` **und** ist
`docs-consolidation.enabled == true` **und** ist `resolve_index_mode() == "file-index"`, wird
es durch das Voll-Index ersetzt (erlaubt, einmalig). In **allen anderen** Fällen bleibt der
Scaffold-Skeleton unangetastet (Consumer-Vertrag, Szenarien 54/55/56). Ist `index-mode:
skeleton`, bleibt der Scaffold-Skeleton **immer** unangetastet. **Nie** der umgekehrte Fall:
der Generator schreibt **nie** einen Skeleton.
Regressionsschutz: Szenarien 54/55/56 (`registry.md:97-103`,
`asserts/54-spec-plan-external-override.sh:26-27`, `asserts/55-spec-plan-ke-off-fallback.sh:24-25`,
`asserts/56-spec-plan-preset-coupling.sh:31`) sowie AC-38.

**Ergänzung Rev. 0.8 (P-2, §17.12.1 — IC-15 war unvollständig, nicht falsch).** Der Absatz
regelt ausschließlich den **Skeleton**-Fall und setzt dafür
`resolve_index_mode() == "file-index"` voraus. In agent-meta entsteht `docs/INDEX.md` jedoch
**ohne** Skeleton, als **Neuanlage** — `resolve_index_mode()` löst dort `"knowledge-engine"` auf
(`spec_plan_scaffold.py:80-97`; `.meta-config/project.yaml:69` + `:77` + `:15`), der Scaffold
schreibt also **nichts** (`spec_plan_scaffold.py:116` bleibt `False`), und der Generator nimmt
den `FileNotFoundError`-Zweig (`doc_renderer.py:829-830`, Tag `CREATE`). **Verbindlich ergänzt:**
**Zweite Schreibbedingung** — Ziel existiert **nicht** ⇒ Voll-Index anlegen, sofern
`docs-consolidation.enabled == true` **und** `index-mode` **nicht** `skeleton` **und**
`index-owner` **nicht** fail-closed (IC-25). Diese Bedingung ist **unabhängig** von
`resolve_index_mode()`; sie macht den Fall „KE-Modus **und** Ausnahme" erst **spezifizierbar**
und ist der Grund, weshalb W3-6 in agent-meta überhaupt etwas schreiben kann. **Zur Freigabe
ausstehend (P-2).** Gepinnt in **AC-42** (Override ⇒ `CREATE`), **AC-20** (Skeleton-Fall
unverändert) und **AC-43** (derselbe Aufbau **ohne** den Key ⇒ `skipped`).

#### IC-16 — `scripts/lib/generated_file_drift.py` :: Docs-Dateien in die Hash-Baseline

Der Store ist **provider-unabhängig** keybar (`generated_file_drift.py:333`
`relative_to(project_root).as_posix()`), und es existiert bereits ein provider-freier
Präzedenzfall: `PLATFORM_DEFAULTS_RESOLVED_REL` (`:44`) wird in `scan_generated_file_drift`
(`:344-349`, Pseudo-Provider `"platform-defaults"` `:349`) und in
`capture_generated_file_hashes` (`:422-424`) behandelt.

```python
DOCS_GENERATED_RELS: tuple[str, ...] = ("docs/INDEX.md", "docs/architecture/INDEX.md")
DOCS_FACT_BLOCK_HOSTS: tuple[str, ...] = ("README.md", "llms.txt", "ARCHITECTURE.md")
DOCS_MARKER_KEY_SUFFIX = "#docs:"            # Key-Form: <rel-pfad>#docs:<region>
# + jeder Pfad, dessen Inhalt einen <!-- agent-meta:docs-begin ... -->-Marker trägt
```

- **Kein** Eintritt in `_iter_managed_files` (`:240-310`) — das ist provider-scoped und würde
  Doku-Dateien fälschlich einem Provider zuordnen. Stattdessen eine eigene, einmalige
  Ergänzung neben dem `PLATFORM_DEFAULTS_RESOLVED_REL`-Handling (`:344-349`, `:422-424`),
  mit Pseudo-Provider `"docs-consolidation"`.
- **Grenze:** `README.md` enthält **Handprosa plus** generierte Regionen. Ein Diff in der
  Handprosa darf **kein** Drift-Finding sein. Deshalb wird für `DOCS_FACT_BLOCK_HOSTS` nicht
  die ganze Datei gehasht, sondern **nur der extrahierte Marker-Body** (normalisiert:
  `"\n".join(line.rstrip() for line in body.splitlines()).strip()`). Der Store-Key lautet
  dann `README.md#docs:facts` (analog `platform-defaults.resolved.yaml`-Präzedenz, Key ist
  ein String und muss kein Pfad sein).

**M8-Auflösung — analysiert statt vermutet (Rev. 0.2).** Rev. 0.1 führte den `#`-Key als
`HYPOTHESIS` und empfahl, das Key-Design zu ändern. Der Code wurde am Working Tree
**nachgelesen**; das Ergebnis ist spezifizierbar, und die nötige Änderung ist **kleiner** als
ein Key-Design-Wechsel:

| Consumer des Hash-Stores | Verhalten mit `README.md#docs:facts` | Beleg | Konsequenz |
|---|---|---|---|
| `_load_hashes` / `_save_hashes` | Key ist ein beliebiger String, wird als Dict-Schlüssel persistiert | `:51-67` | **kein** Problem |
| `is_allowlisted(rel_path, patterns)` | `fnmatch` matcht gegen den **ganzen** String ⇒ ein Muster `README.md` matcht `README.md#docs:facts` **nicht** | `:82-84` | **Verbindliche Regel:** für Marker-Body-Keys wird gegen den **Basis-Pfad** (Key ohne `#`-Suffix) gematcht. Sonst umgeht ein Allowlist-Eintrag für `README.md` genau die Marker-Keys, die er unterdrücken soll |
| `backup_drifted_files` | `target = project_root / finding["path"]` (`:379`); `read_text` schlägt fehl ⇒ `log.debug` + `continue`: **fail-soft, kein Fehler, aber auch kein Backup** | `:379-386` | **Verbindlich (NFA-05):** der Generator darf eine handeditierte Region **nicht** überschreiben, sondern meldet sie (AC-19) — das ist die *Konsequenz* daraus, dass kein Backup entsteht |
| `_sync_stage_auto_commit_allowlist` | **keine Interaktion.** Die Stage liest `config` + `active_roles` via `resolve_auto_commit_config(config, active_roles, agent_meta_root)` und schreibt `.meta-config/auto-commit-allowlist.json`; sie liest den Drift-Store **nicht** | `sync_pipeline.py:1102-1117` | **Reviewer-Korrektur R18** (§17.2): die befürchtete Interaktion existiert nicht — R18 wird als *analysiert und nicht zutreffend* geführt, mit verifiziertem Beleg |
| `capture_generated_file_hashes` | `hashes[rel_path] = content_hash(...)` je aktivem Provider plus Pseudo-Provider-Ergänzung | `:405-425` | Doku-Keys müssen in **beide** Richtungen (Scan **und** Capture) symmetrisch ergänzt werden, sonst meldet der Scan dauerhaft Drift |

- `drift-allowlist.yaml` (`generated_file_drift.py:37`, `allow-edits`) gilt unverändert auch
  für Doku-Pfade — mit der Basis-Pfad-Regel oben.

#### IC-25 — `docs-consolidation.index-owner`: Eigentümerdeklaration für `docs/INDEX.md` (Rev. 0.8, **P-1** — zur Freigabe ausstehend)

> **Zweck dieses Vertrags.** W3-6 scheitert heute an **einer** Codezeile:
> `doc_renderer.py:702-703` — `if resolve_index_mode(config)[0] == "knowledge-engine": return
> KE_AUTHORITATIVE_REASON`. In agent-meta löst `resolve_index_mode()` genau diesen Wert auf
> (`.meta-config/project.yaml:69` `index.mode: knowledge-engine`, `:77`
> `external-system-override.enabled: false`, `:15` `knowledge-engine.enabled: true` ⇒
> `false or not true` ⇒ **kein** Absenken auf `file-index`; `spec_plan_scaffold.py:80-97`).
> IC-25 verengt **ausschließlich den Auslöser** dieses **einen** Gates. **Kein** dritter
> blockierender Eigentümer, **keine** Änderung an `resolve_index_mode()`, **keine** Änderung an
> der Besitzregel (IC-13), an `is_file_index_skeleton()` (IC-15) oder am `dry_run`-Vertrag.
> **Der Code enthält keine agent-meta-Kenntnis** — die Ausnahme entsteht dadurch, dass **nur**
> agent-meta den Key setzt. Beleg der Begrenztheit: DECISION-1…DECISION-4 (§17.12.3),
> Begrenztheitsvertrag IC-26, Messbeleg AC-42…AC-46 (§7 M2).

```python
# scripts/lib/doc_renderer.py — neue Modulkonstanten neben :270-275

INDEX_OWNER_AUTO: str = "auto"
"""Abwesenheits-Default von ``index-owner`` — die Modus-Aufloesung entscheidet
( wortwoertlich IC-13, Zeile 2 )."""

INDEX_OWNER_GENERATOR: str = "docs-consolidation"
"""Dieser Generator erklaert sich zum Eigentuemer von ``docs/INDEX.md``."""

KE_OVERRIDE_REASON: str = (
    "index-owner: docs-consolidation — the docs generator owns docs/INDEX.md in "
    "this project"
)
"""Optionaler Audit-Hinweis, **kein** Pflicht-Log. **Gemessen** ist: der Aufrufer loggt
ausschliesslich, wenn das Gate einen Grund liefert (``doc_renderer.py:810-814``); im
erlaubten Zweig wird **nichts** geloggt. Deshalb ist diese Konstante **nicht** Teil des
gepinnten Interface-Contracts — sie darf als Konstante existieren, **ohne** Pflicht zu sein.
**Verbindlich** ist allein die negative Zusage: der Log nennt ``KE_AUTHORITATIVE_REASON``
in diesem Fall **nicht** (AC-42c). Ob zusaetzlich ein Override-Hinweis geloggt wird, ist eine
**Plan**-Entscheidung, **keine** Spec-Pflicht (V-D5, §17.12.5)."""

UNKNOWN_INDEX_OWNER_REASON: str = (
    "index-owner is neither 'auto' nor 'docs-consolidation' — not written "
    "(fail-closed, IC-22)"
)
"""Grund fuer einen unbekannten Wert — eigener Grund, damit die Liste der blockierenden
Eigentuemer **geschlossen** bleibt (``doc_renderer.py:685-686``); Muster ist
``UNKNOWN_INDEX_MODE_REASON`` (``:285-299``): ein Wert, der nichts bedeutet, darf keinen
wahren Satz loggen."""
```

**Geänderte Entscheidungsfolge in `_index_mode_block_reason()`** (`doc_renderer.py:663-711`) —
**jeder** Schritt kann nur konservativer werden; die Reihenfolge **ist** der Vertrag
(`:729-731`):

> **Warum Zweig (1) die einzige *garantierte* Absicherung ist (RVW8-6, K82).** Das `enum` des
> Schemas (`config/project-config.schema.json:2421-2470`) ist Autocomplete und
> Tippfehler-**Konvention**. Die Schema-Validierung im Sync-Pfad ist **best-effort** und läuft
> **nur**, wenn `jsonschema` verfügbar ist: `scripts/lib/config.py:342` („Schema validation … **if**
> jsonschema is available"), `:372-388` („jsonschema not installed or validation error —
> **best-effort**", `pass`). Fehlt das Modul, validiert **nichts** — `index-owner: "agent-meta"`
> wäre dann ein gültiger Config-Wert mit unbekannter Wirkung. Der Zweig (1) ist deshalb **nicht**
> durch „Enum zu lassen" vertretbar; er ist die Zusage, AC-44(c) pinnt ihn, und die
> Konvention darf ihn **nicht** ersetzen.

```python
def _index_mode_block_reason(config: dict) -> str | None:
    block = config.get("docs-consolidation")
    block = block if isinstance(block, dict) else {}
    owner = block.get("index-owner", INDEX_OWNER_AUTO)
    if owner not in (INDEX_OWNER_AUTO, INDEX_OWNER_GENERATOR):
        return UNKNOWN_INDEX_OWNER_REASON      # (1) fail-closed, VOR der KE-Pruefung
    if (
        owner == INDEX_OWNER_AUTO
        and resolve_index_mode(config)[0] == "knowledge-engine"
    ):
        return KE_AUTHORITATIVE_REASON          # (2) unveraendert, nur bedingt
    mode = block.get("index-mode", DEFAULT_INDEX_MODE)
    if mode == SKELETON_INDEX_MODE:
        return SKELETON_MODE_REASON             # (3) unveraendert
    if mode != FULL_INDEX_MODE:
        return UNKNOWN_INDEX_MODE_REASON        # (4) unveraendert
    return None
```

**Warum genau diese Reihenfolge (Vertrag, nicht Geschmack):** Der Fail-closed-Zweig (1) steht
**vor** der KE-Prüfung, damit ein Tippfehler nie als „KE ist autoritativ" fehlgedeutet wird —
dasselbe Argument, mit dem der Bestand die KE-Prüfung vor den `index-mode`-Zweig legt
(`:682-694`). Der Zweig (2) ist eine **Verengung** (`auto and KE`), **keine** Erweiterung:
`index-owner: docs-consolidation` kann **keinen** Eigentümer entfernen, nur **einen** Auslöser
stilllegen. **Verbindliche Wertetabelle** (jede Zeile ist durch **AC-42…AC-44** gepinnt):

| `index-owner` | `resolve_index_mode()` | `index-mode` | Ergebnis |
|---|---|---|---|
| Key **fehlt** (Default `auto`) | `knowledge-engine` | beliebig | `KE_AUTHORITATIVE_REASON` — **identisch zum heutigen Verhalten** (`:702-703`) |
| Key **fehlt** | `file-index` / `off` | `full` | `None` — **identisch zum heutigen Verhalten** |
| Key **fehlt** | beliebig | `skeleton` | `SKELETON_MODE_REASON` — **identisch** |
| `docs-consolidation` | `knowledge-engine` | `full` | **`None`** ⇒ Schreiben erlaubt — **die agent-meta-Ausnahme** |
| `docs-consolidation` | `knowledge-engine` | `skeleton` | `SKELETON_MODE_REASON` — **Gegenprobe: die Ausnahme hebt (3) nicht auf** |
| beliebiger / unbekannter Wert | beliebig | beliebig | `UNKNOWN_INDEX_OWNER_REASON`, **kein** Schreiben (fail-closed) |

**Schema-Eintrag** (verbindlich, Muster `config/project-config.schema.json:2430-2438`), in
`docs-consolidation.properties` (`:2424-2469`); `additionalProperties: false` (`:2470`) bleibt
⇒ ein Tippfehler wie `index-owner: agent-meta` oder `index-owner: docs` ist ein
**Schema-Fehler**, kein stiller No-op:

```json
"index-owner": {
  "type": "string",
  "enum": ["auto", "docs-consolidation"],
  "default": "auto",
  "description": "auto = the resolved index mode decides (IC-13). docs-consolidation = this project declares the docs generator the owner of docs/INDEX.md, so a knowledge-engine mode does not block the write. Fail-off: absent means auto."
}
```

**Warum `auto` und nicht `knowledge-engine` als Default:** `auto` ist wortwoertlich das heutige
Verhalten („die Modus-Aufloesung entscheidet") und haelt die Absenz-Semantik von IC-13 Zeile 2
**wortgleich**; ein Default `knowledge-engine` wuerde eine Aussage treffen, die es ohne Key gar
nicht gibt. Ein **expliziter** Wert `knowledge-engine` im Enum wird **bewusst nicht
eingefuehrt** (DECISION-2, §17.12.3 — er wuerde einen **dritten** blockierenden Eigentuemer in die
geschlossen dokumentierte Liste aufnehmen und `:685-686` widersprechen).

#### IC-26 — Begrenztheitsvertrag der agent-meta-Ausnahme (Rev. 0.8, **P-1/P-5** — zur Freigabe ausstehend)

1. **Wirkung ausschliesslich auf `docs/INDEX.md`.** `index-owner` wird an **genau einer**
   Stelle gelesen (`_index_mode_block_reason`, `doc_renderer.py:663-711`); diese Funktion ist
   ausschliesslich fuer den Index-Writer zustaendig (`sync_docs_consolidation` `:714`, Aufrufer
   `sync_pipeline.py:985` → `:958`). Die Hybrid-Regionen von **W3-7** laufen ueber
   `apply_fact_blocks()` (`doc_renderer.py:183`) und werden **nicht** beruehrt (E-10, §17.12.2).
2. **`resolve_index_mode()` bleibt unveraendert** (`spec_plan_scaffold.py:80-97`). Folge in
   agent-meta: der Scaffold schreibt **weiterhin kein** Skeleton (`spec_plan_scaffold.py:116`
   bleibt `False`). Die B2-Invariante „Scaffold zuerst, Generator ersetzt das Skeleton
   **einmalig**" (IC-12, IC-15, R7) ist damit **nicht** gebrochen, sondern fuer agent-meta
   **sachlich gegenstandslos**: es gibt nur **einen** Writer und **einen** Erstschreibvorgang
   (`CREATE`, `doc_renderer.py:829-830`). Sobald die Datei existiert, greift der Besitzzweig
   ueber `_carries_generator_id()` (`:644-655`, ID `doc-indexer/1` `:310`) ⇒ der zweite Lauf
   meldet `unchanged` (`:845-848`), **null** Aktionen. Gepinnt in **AC-20** (unveraendert),
   **AC-42** (einmalig), **AC-45** (`dry_run`).
3. **Besitzregel unveraendert** (IC-13): eine fremde Datei **ohne** Scaffold-Marker und **ohne**
   Generator-ID wird auch mit `index-owner: docs-consolidation` **nicht** ueberschrieben
   (`:855-858`, `OWNERSHIP_REASON` `:255-259`). Gepinnt in **AC-44**.
4. **`is_file_index_skeleton()` unveraendert** (`spec_plan_scaffold.py:41-77`), einschliesslich
   der dokumentierten **permissiven** Marker-Suchrichtung (`:52-68`) — **kein** Eingriff, **keine**
   Verengung des Übernahmeradius.
5. **`dry_run`-Vertrag unveraendert** (IC-13, AC-23, AC-45): genau **ein** `write_checked`
   (`:861`), im Dry-Run nur Aenderungserkennung, Action getaggt `WOULD-CREATE`/`WOULD-UPDATE`
   (`:867`).
6. **Consumer unberuehrt.** **Kein** Szenario-Fixture enthaelt einen `docs-consolidation`-Key
   (Grep ueber `tests/scenarios/configs/*.project.yaml` ⇒ **0** Treffer; IC-22-Absatz `:1553-1557`;
   `tests/scenarios/run.sh:46-52` spielt sie 1:1 ein) ⇒ `enabled` fail-off ⇒ die Ausnahme ist
   fuer die Szenarien **per Konstruktion unerreichbar**. Szenarien **50/51/52/54/55/56** bleiben
   **ohne** Aenderung gruen (AC-38, NG-10).
7. **KE-Modi der Consumer unveraendert.** `knowledge.py:185-196` liest `resolve_index_mode()`
   unveraendert; `knowledge/wiki/index.md` bleibt Eigentum der KE (`knowledge.py:163-169`).
8. **Kein Provider-Name, kein Projektname im Code.** Der Schluessel-Wert ist **kein** Projektname
   (`docs-consolidation` = Feature-Name, nicht Repo-Name) und **kein** Vorkommen von
   `platforms[0]` (`.meta-config/project.yaml:80-81` fuehrt `agent-meta` — der Key-Vergleich
   benutzt dieses Feld **nicht**). Nachweis: Guard `tests/test_provider_agnostic_dispatch.py`
   (bestehend) und Policy `.opencode/skills/provider-agnostic/SKILL.md:12-18` (Config-Keys statt
   `if provider == "Name"`; gleichlautend `AGENTS.md:50`). **Keine** Repo-Struktur-Erkennung:
   von der APPROVED-Fassung bereits entschieden (R17, Risikotabelle §12.2 — „Ein ‚agent-meta-Eigenerkennung'-
   Heuristik-Gate wird **nicht** gebaut") und unabhaengig davon im Code der
   `docs_consolidation_enabled`-Common-Gate (IC-05) festgehalten
   (`scripts/consistency-check.py:144-145`).
9. **Kein `facts-hash`-Churn.** `index-owner` fliesst **nicht** in `compute_doc_facts()` ein
   ⇒ **kein** Churn, **kein** AC. Festgehalten, damit es nicht erneut aufgerollt wird (§17.12.2).

### 5.3 Modul M3 — Migration

#### IC-17 — Migrationsoperationen (alle `git mv`, kein Inhalts-Rewrite)

| # | Operation | Quelle | Ziel | Welle | Rollback |
|---|---|---|---|---|---|
| M-1 | `git mv` Langfassung | `ARCHITECTURE.full.md` | `docs/architecture/00-overview-full.md` | W4 | `git mv` zurück |
| M-2 | Stub schreiben | `ARCHITECTURE.md` (84 Z, regeneriert) | `ARCHITECTURE.md` | W4 | `git checkout` |
| M-3 | `git mv` Legacy-Specs | `docs/superpowers/specs/` | `docs/specs/archive/superpowers/` | W6 | `git mv` zurück |
| M-4 | `git mv` Legacy-Pläne | `docs/superpowers/plans/` | `docs/plans/archive/superpowers/` | W6 | `git mv` zurück |
| M-5 | `git mv` Beispiel-Configs | `howto/configs/project.yaml.example` (340 Z) | `docs/guides/configs/project.yaml.example` | W5 | `git mv` zurück |
| M-6 | `git mv` Howto-Guide (**neu, M4**) | `docs/howto/admin-ui-remote-access.md` | `docs/guides/admin-ui-remote-access.md` | W5 | `git mv` zurück; `docs/howto/` danach leer und `git rm` |
| M-7 | Stale-Deklaration wandert mit (**neu, M5**) | `ARCHITECTURE.md:3` | **additive** Stale-Zeile in `docs/architecture/00-overview-full.md`; im Stub **entfällt** sie | W4 | Zeile entfernen; Stub via `git checkout` |
| M-8 | Verweise bereinigen | `README.md:721-724` | Zeilen auf existierende Ziele umgeschrieben bzw. entfernt | W8 | `git checkout` |
| M-9 | `derived-from`-Annotation | `knowledge/wiki/**` | Frontmatter-Zeile ergänzt (**additive** Zeile pro Seite, kein Textumbau) | W5 | Zeile entfernen (additiv revertierbar) |
| M-10 | Wiki-Architektur-Redirects | `knowledge/wiki/concepts/architecture*.md` | Kurzform: eine Zeile „SSoT: `docs/architecture/…`" + `derived-from` | W5 | `git checkout` |
| M-11 | Config-Schema-Block (**neu, R15**) | `config/project-config.schema.json` | **neuer Top-Level-Block** `docs-consolidation` mit den 6 Keys aus IC-22, `additionalProperties: false` | **W1** | `git checkout` |
| M-12 | `PROJECT_STRUCTURE`-Korrektur | `.meta-config/project.yaml:205-221` | Fehlende Wurzel-Einträge ergänzt (`docs/INDEX.md`, `docs/guides/configs/`, `docs/providers/`, `docs/se-cascade/`, `docs/concepts/`) — **Config-Edit**, kein Doku-Edit | W8 | `git checkout` |
| M-13 | `legacy:`-Liste erweitern | `.meta-config/project.yaml:61-63` | **additive zwei Zeilen** (die zwei neuen Archivpfade) | W6 | Zeile entfernen |

**M-11-Begründung und -Korrektur (R15, rev. 0.2):** `scripts/lib/config.py` validiert
`project.yaml` gegen `config/project-config.schema.json` (Präzedenz: `dod-presets.yaml:8`
verweist ebenfalls auf das Schema). Das **Wurzel**-Schema ist permissiv
(`additionalProperties: true`, `:2425`) — die 6 neuen Keys sind also **kein** harter
Blocker, sie würden die Validierung nicht brechen. Sie zu deklarieren ist dennoch
**Repo-Konvention**: das Schema nutzt geschlossene Unterobjekte ausdrücklich als
Tippfehler-Wächter (Selbstauskunft in `:2058` und `:2073`). M-11 ist damit
**Konventions- und Autocomplete-Pflicht, keine Fehlerbehebung** — diese Einordnung korrigiert
die Reviewer-Lesart „geht sonst gar nichts" (siehe §17.2).

**B1-Mitigation verbindlich:** die alten `legacy:`-Einträge (`docs/superpowers/specs`,
`docs/superpowers/plans`, `project.yaml:61-63`) bleiben **ein Release** stehen und erzeugen
eine Deprecation-WARNING im Sync-Log. Release-Notes-Pflicht, Minor-Bump.

**B6-Hinweis:** M-12 verändert `PROJECT_STRUCTURE`, das in **jeder** generierten Kontextdatei
landet (`.meta-config/project.yaml:205-221` → `AGENTS.md`/`CLAUDE.md`). Der managed-block-Mechanismus
(`context.py:36-38`) und die Drift-Detection fangen Handpflege ab; der Layout-Diff ist
**sichtbar** und damit ein Review-Punkt, kein stiller Side-Effect.

#### IC-18 — `ARCHITECTURE.md` als generierter Stub (T-4)

Der Stub enthält: Titel, **generierter** Diagramm-Index (Tabelle aus `docs/architecture/*.md`
+ `docs/concepts/viz-logging-mcp.md` + `docs/concepts/a2a-handoff-protocol.md`, heute
`ARCHITECTURE.md:8-20`), einen Pointer auf `docs/architecture/INDEX.md`, den Link auf
`docs/architecture/00-overview-full.md` und **keine eigenen Inhalte**. `llms.txt:24` verlinkt
weiterhin auf `ARCHITECTURE.md` und bleibt damit gültig (T-4-B, „Löschen bricht Deeplinks").

**Stale-Deklaration (M5, entzirkelt):** `ARCHITECTURE.md:3` („Repo version: **0.92.0** —
content last substantively reviewed: 2026-07-20") ist heute die maschinenlesbare Quelle für
`status:stale-upstream` (`knowledge/wiki/index.md:24`). Nach M-1 liegt dieser Inhalt in
`docs/architecture/00-overview-full.md`, nach M-2 ist er aus dem Stub **weg**. Rev. 0.1
verlangte in AC-29, die Zeile `Repo version:` zu verbieten, **und** berief sich dabei auf
genau diese maschinelle Extraktion — nach W4 ist die Quelle weg, der AC war zirkulär. Auflösung:

- **M-7** verschiebt die Deklaration in die Langfassung (additive Zeile dort, keine im Stub).
- **IC-03** liest die Deklaration aus `docs/architecture/00-overview-full.md` — **nicht** aus
  dem Stub.
- **AC-29** prüft beide Seiten **getrennt**: (a) der Stub enthält generierten Diagramm-Index,
  beide Pointer und keine eigene Architektur-Prose; (b) die Stale-Deklaration steht in der
  Langfassung, nicht im Stub; (c) `compute_wiki_staleness()` liefert für
  `concepts/architecture.md` mit `derived-from: docs/architecture/00-overview-full.md` einen
  auswertbaren Wert. Damit verbietet der AC nichts, dessen Quelle er voraussetzt.

### 5.4 Modul M4 — Knowledge-Index-Generierung

#### IC-19 — `scripts/lib/knowledge.py` (Erweiterung `:103-205`): `index.md`-Generator

**Policy-Bruch, Bedingung (a):** `knowledge.py:112-114` sagt „never overwrites existing
`schema.md`/`wiki/index.md`/`wiki/log.md`". Diese Spec bricht das **nur** für `index.md` und
**nur** unter den Bedingungen des Rollback-Flags. Vor Aktivierung wird
`knowledge/schema.md` (§2 „Usage", `:41-42`) um einen Absatz „`index.md` is generated"
ergänzt — eine **strukturelle** Änderung, die laut `knowledge/schema.md:44-46`
User-Sign-off braucht (**Bedingung für W7**, nicht für diese Spec).

```python
def sync_wiki_index(agent_meta_root: Path, project_root: Path,
                     config: dict, log: SyncLog, dry_run: bool) -> dict:
    """Deterministischer 1:1-Index aus dem Dateisystem. No-op wenn
    knowledge-engine.okf.index-mode != "generated" (Rollback-Flag)."""
```

| Schicht | Ort | Schreibrecht | Ableitung | Pflicht-Frontmatter |
|---|---|---|---|---|
| Quelle | `knowledge/sources/` | nur `knowledge-ingestor`, additiv (NG-2) | keine | `source-of`, `captured-at`, `immutable: true`, optional `supersedes` |
| Wiki-Seite | `knowledge/wiki/{concepts,entities,topics,plans,specs,sources,queries}/` | Knowledge-Agenten (LLM-owned) | `derived-from: <rel-pfad>` + `derived-at: <ISO>` | `type`, `derived-from`, `derived-at`, `status` |
| Index | `knowledge/wiki/index.md` | **Generator (IC-19)** | 1:1 aus dem Dateisystem | — |
| Log | `knowledge/wiki/log.md` | Generator-**Append** + manuell erlaubt | 1 Zeile pro Sync mit Wiki-Änderung | — |

Verzeichnisnamen folgen `knowledge.py:_KNOWLEDGE_GITKEEP_SUBDIRS` (`:87-100`, 14 Einträge inkl.
`wiki/{concepts,entities,topics,sources,queries,plans,specs}`). Sortierung alphabetisch, damit
der Diff minimal bleibt (NFA-02).

#### IC-20 — `knowledge/wiki/log.md`-Append (Bedingung (c))

- Format exakt nach `knowledge/wiki/log.md:13-17`:
  `YYYY-MM-DD HH:MM — <operation> — <summary>`.
- **Genau eine Zeile** pro Sync, in dem sich mindestens eine Wiki-Datei geändert hat; sonst
  **kein** Append (verhindert Log-Churn, NFA-02).
- `operation` ∈ `{index, index/update}` (Vokabular aus `:22, :24, :27`).
- Bestehender Inhalt wird **nie** umsortiert oder gekürzt (append-only, Policy).

#### IC-21 — `agents/1-generic/knowledge-indexer.md` (Bedingung (b))

Umschreibung der Rolle von „schreibe `index.md`" zu „prüfe Generator-Output, melde Drift".
Provider-agnostik: **kein** Claude-Literal, keine Provider-Verzweigung
(`provider-agnostic`-Regel; Guard `tests/test_provider_agnostic_dispatch.py`).
Folgen: alle generierten Provider-Kopien der Rolle werden durch den nächsten Sync neu erzeugt.

**Kollisionsvermerk (N2, rev. 0.2):** dies ist die **einzige** Datei unter `agents/`, die
diese Initiative anfasst, und sie liegt in der von Track A / Rollenpflege berührten Zone
(§2.3). Verbindliche Reihenfolge: W7 startet **erst**, wenn der Rollenpflege-Branch gemergt
ist; IC-21 wird als **letzter** Commit von W7 committet, damit ein Rebase der Rollenpflege
nicht in einem `agents/1-generic/`-Template-Diff landet. Risiko **R19**; Rollback
`git checkout`.

#### IC-22 — Rollback-/Gate-Config

| Key | Ort | **Default bei Abwesenheit** | Default agent-meta (explizit gesetzt) | Wirkung |
|---|---|---|---|---|
| `docs-consolidation.enabled` | `.meta-config/project.yaml` (neu) | **`false`** | `true` (explizit, in W1) | Master-Schalter für **Generator (IC-13) und Checks V1–V9 (IC-05)** |
| `docs-consolidation.index-mode` | dito (neu) | `full` | `full` | `full` = Voll-Index ersetzt **nur** ein Scaffold-Skeleton; `skeleton` = Scaffold-Skeleton bleibt immer |
| `docs-consolidation.checks.strict` | dito (neu) | `false` | `true` (ab W3) | V1 als ERROR vs. WARNING (B4) |
| `docs-consolidation.sources` | dito (neu) | `[]` | `[README.md, llms.txt, ARCHITECTURE.md]` | Liste der hybrid-Dateien; leer = kein Rendering (NG-9) |
| `docs-consolidation.volatile-facts` | dito (neu) | `[DOCS_SCENARIO_COUNT]` | dito | Fakten, die in Hybrid-Dateien unterdrückt und aus dem `facts-hash` ausgeschlossen werden (R1) |
| **`docs-consolidation.index-owner`** (Rev. 0.8, **P-3**, **IC-25**) | dito (neu) | **`auto`** | **`docs-consolidation`** (explizit, in **W3-6**) | Deklariert den Eigentuemer des Pfads `docs/INDEX.md`. `auto` = die Modus-Aufloesung entscheidet (wortwoertlich IC-13 Zeile 2); `docs-consolidation` = **dieses** Projekt erklaert den Doku-Generator zum Eigentuemer, dann blockiert ein `knowledge-engine`-Modus das Schreiben **nicht**. Fail-off: **abwesend = `auto`**. Verengt **ausschliesslich** den KE-Vorrang-Zweig in `_index_mode_block_reason` (`doc_renderer.py:702-703`) auf `docs/INDEX.md`; **kein** Eigentuemer wird hinzugefuegt (DECISION-2). **Zur Freigabe ausstehend.** |
| `knowledge-engine.okf.index-mode` | `.meta-config/project.yaml:18-29` (ergänzt) | `llm` | `llm` für ein Release, danach `generated` | Generator an/aus (T-6, Rollback W7) |

**Selbstwiderspruch aufgelöst (K5, rev. 0.2).** Rev. 0.1 schrieb: „Alle Keys sind **additiv**;
keiner verändert bestehendes Verhalten **bei Abwesenheit** (Schema-Default = Default
agent-meta)" — und setzte zugleich `enabled: true` als Abwesenheits-Default. Beides ist
unvereinbar: `true` **ist** ein Verhaltenswechsel bei Abwesenheit. Die auflösende Regel ist die
**Fail-off-Präzedenz** des Repos: `knowledge.py:127` prüft
`ke_config.get("enabled", False)` — „nicht explizit `true`" heißt „aus", und zwar für den
Knowledge-Engine-Writer (`:127-129`) **und** für dessen Auto-Index-Schalter (`:132`
`okf.get("auto-index", True)` folgt derselben Logik). Genau diese Regelung wird hier für
`docs-consolidation.enabled` übernommen, **für alle sieben Keys** (Rev. 0.8: `index-owner`
tritt hinzu, **P-3**) und **für Writer und Checks gleichermaßen**.

**Konsequenz, die explizit benannt wird (K5):** Die Szenario-Fixtures
`tests/scenarios/configs/*.project.yaml` werden von `tests/scenarios/run.sh:46-52`
unverändert als `$tmp_dir/.meta-config/project.yaml` eingespielt und enthalten **keinen**
`docs-consolidation`-Key (verifiziert am Beispiel `54-spec-plan-external-override.project.yaml`,
34 Zeilen, und `52-spec-plan-enabled.project.yaml`, 32 Zeilen). Mit Fail-off sind Generator
**und** V1–V9 dort vollständig inaktiv. Das ist kein Nebeneffekt, sondern der **vertragliche
Grund**, warum die Szenarien 50/51/52/54/55/56 ohne jede Änderung grün bleiben (NG-10, AC-38).
Ein Szenario, das das Doku-Verhalten prüfen will, muss den Key **explizit** setzen — dafür
ist `64-docs-facts-drift` vorgesehen (§2.3).

**Kein** Key enthält einen Provider-Namen.

### 5.5 Querschnitts-Contracts (rev. 0.2)

#### IC-23 — `config/doc-facts-expected.yaml` + `scripts/lib/doc_facts.py::load_expected_doc_facts` (R14)

**Problemklasse (Korrektheit, nicht Churn).** Die Kette `doc_facts → Renderer → V6` ist ein
**geschlossener Kreis**: V6 vergleicht den gerenderten Block gegen `compute_doc_facts()` —
also gegen dieselbe Formel, die ihn erzeugt hat. Ein **systematisch** falscher Faktor passiert
damit **alle** Gates. Rev. 0.1 hat genau das dreifach bewiesen: F19 (Tier 4 statt 5), F22
(DoD 6 statt 7, Rev. 0.1 als „korrekt" eingestuft) und F14 (6/7 statt 7/8) waren drei
Zählfehler, die **kein** Gate dieser Initiative gefunden hätte. R1 führte das als
„Doku-Diff-Churn"; es ist ein **Korrektheitsrisiko**.

```python
# scripts/lib/doc_facts.py
def load_expected_doc_facts(agent_meta_root: Path, log=None) -> dict[str, str]:
    """Liest config/doc-facts-expected.yaml. {} bei Abwesenheit/Fehler (fail-soft,
    Muster load_yaml_file(..., on_error="default"))."""

def compare_expected_doc_facts(
    computed: dict[str, str], expected: dict[str, str]
) -> list[dict[str, str]]:
    """Return [{'fact', 'computed', 'expected', 'kind'}] mit kind in
    {'mismatch', 'missing-in-expected'}. Deterministisch, nach 'fact' sortiert."""
```

```yaml
# config/doc-facts-expected.yaml   (HANDGEPFLEGT, niemals generiert)
schema-version: 1
verified-at: "2026-09-26"
verified-by: human
DOCS_VERSION: "1.2.0-beta.2"
DOCS_AGENT_TEMPLATES_COUNT: "80"
DOCS_AGENTS_SE_COUNT: "14"
DOCS_PROVIDER_COUNT: "9"
DOCS_HOOKS_COUNT: "11"
DOCS_HOOKS_1GENERIC_COUNT: "9"
DOCS_PIPELINES_COUNT: "8"
DOCS_PIPELINES_ACTIVE_COUNT: "7"
DOCS_DOD_PRESET_COUNT: "7"
DOCS_TIER_PRESET_COUNT: "5"
DOCS_COMMAND_COUNT: "22"
```

**Schlüsselzahl: elf (11).** Rev. 0.2 schrieb an einer Stelle „zwölf" (IC-23-Text, AC-36,
NFA-11, R14) und an anderer „11" (§1.2) — **beides konnte nicht stimmen**, weil die
Yaml-Datei genau **11** Einträge hat. Verbindlich ist **elf** und diese Datei ist der
**einzige** Ort, an dem konkrete Sollzahlen stehen (rev. 0.3, NEW-4/NEW-8: der `xfail`-Snapshot
in AC-02 ist als unenforceable entfernt, damit es nicht zwei Orte für dieselbe Zahl gibt).
Nicht enthalten: `DOCS_AGENTS_NONSE_COUNT` (reine Differenz `SE + NONSE == TEMPLATES`, in AC-02
formelgeprüft), `DOCS_SCENARIO_COUNT` (volatile) und die `*_BLOCK`-Fakten (Text, keine Zahl).

**Vertrag:**

- `compute_doc_facts()` bekommt **keinen** Parameter für die Sollwerte (keine Kopplung, kein
  Zirkel in der anderen Richtung).
- **V6** liest beide Quellen und emittiert zwei Fehlerklassen:
  (a) `kind: "handedit"` — gerenderter Block ≠ `compute_doc_facts()` (bestehender Zweck);
  (b) `kind: "expected-mismatch"` — `compute_doc_facts()` ≠ Sollwert, **obwohl** der
  Render-Output exakt stimmt. `kind: "missing-in-expected"` ist **WARNING**, kein Fehler
  (die Datei darf wachsen).
- **Bekannte, bewusst akzeptierte Kosten:** jede gewollte Änderung einer dieser Zahlen (z. B.
  ein neues Pipeline-Preset) macht V6 rot, bis die Sollwert-Datei im **selben** Commit
  mitgezogen wird. Genau das ist der gewollte Review-Signalweg. Geführt als R14-Restrisiko.
- Die Datei ist **kein** Doku-Output und steht **nicht** unter `docs/`; sie ist eine
  Test-Referenz neben den übrigen Config-Dateien und folgt derselben Schreibdisziplin wie
  `config/dod-presets.yaml` (Prezedenz: `dod-presets.yaml:8` verweist auf das Schema).
- **NG-1 gilt nicht:** die Datei ist neu, es gibt keinen Altinhalt umzuschreiben.

#### IC-24 — `scripts/lib/knowledge.py::restore_wiki_index` (M6, rev. 0.2)

**Problemklasse.** Rev. 0.1 verlangte in AC-35, der Rollback `index-mode: llm` stelle den
Ausgangszustand **byte-identisch** wieder her, spezifizierte aber **nirgends** einen
Restore-Pfad. `index-mode: llm` stellt den **Generator** stumm — die Datei bleibt, was der
Generator geschrieben hat. Es gibt außerdem **keinen** CLI-Restore dafür: `sync.py --backup` /
`--restore` (`cli_commands.py:864`, `:888-900`, `backup.py:376+`) sind
**Provider-Verzeichnis-Zip**-Operationen (`restore_provider_dir`, `deactivation.py:21`,
`:303-353`) und können `knowledge/wiki/index.md` **nicht** wiederherstellen (am Working
Tree verifiziert).

```python
# scripts/lib/knowledge.py
def restore_wiki_index(
    project_root: Path, log: SyncLog, *, dry_run: bool = False
) -> list[str]:
    """Stellt knowledge/wiki/index.md aus der Sicherung des Erstrewrites wieder her.

    Reihenfolge:
      1. jüngste existierende Sibling-Sicherung `index.md.sync-backup-<ts>`
         (Muster backup_drifted_files, generated_file_drift.py:354-402, :388)
         -> dorthin zurueckkopieren;
      2. sonst, wenn `index.md` git-getrackt ist:
         `git -C <project_root> checkout -- knowledge/wiki/index.md`;
      3. sonst: log.error + KEIN Schreibzugriff (fail-closed).
    Gibt die Liste der beruehrten Rel-Pfade zurueck; [] bei No-op.
    """
```

**Vertrag:**

- Aufruf **nur** als manueller Runbook-Schritt in W7 (im Plan als Task mit
  Dry-Run-Substep), **nicht** als Sync-Stage und **ohne** neues CLI-Flag (NG-4).
- `dry_run=True` schreibt nicht, meldet aber die geplanten Zielpfade.
- Fail-closed bei Schritt 3: ein „nichts tun und trotzdem Erfolg melden" wäre Datenverlust
  mit grünem Log.
- Reihenfolge ist vertraglich: Sibling-Backup schlägt Git, weil es den **exakten** Zustand
  unmittelbar vor dem Rewrite sichert, nicht den Commit-Zustand.
- AC-35b/AC-35 in §7 sind entsprechend abgeschwächt und verweisen hierher.

---

## 6. Datenfluss

### (a) Normaler Sync (ohne `--dry-run`, ohne `--check`)

```
project.yaml ──► config.py (load) ──► roles.py::resolve_activation_gates
                                          │
agents/1-generic/ ─┐                       │
config/*.yaml ─────┼──► doc_facts.py ──────┴──► {DOCS_*: str}   (rein, kein Write)
hooks/**/*.sh ─────┘        │
                            ├─► doc_index.py::build_index_model ──► doc_renderer.render_docs_index
                            │                                              │
                            │                                     write_checked("docs/INDEX.md")
                            │                                     (is_file_index_skeleton-Guard IC-15)
                            └─► config.py::_build_snippet_variables ──► DOCS_*_BLOCK (snippets/docs/*.md)
                                            │
   README.md / llms.txt / ARCHITECTURE.md ──► doc_renderer.apply_fact_blocks (DOCS_BLOCK_RE)
                                            │   (fehlende Region → unverändert; keine Handedit-Überschreibung)
                                            └──► write_checked je Datei
Knowledge-Wiki (nur wenn okf.index-mode=generated):
   doc_index.py-Muster ──► knowledge.py::sync_wiki_index ──► knowledge/wiki/index.md
                                                   └──────► knowledge/wiki/log.md (1 Append-Zeile)
Danach: generated_file_drift.capture_generated_file_hashes (inkl. Doku-Pfade, IC-16)
```

### (b) `--check` (Doku-Gate)

```
compute_doc_facts()  vs.  Ist-Inhalt der Marker-Regionen / docs/INDEX.md   → V6 (kind=handedit)
compute_doc_facts()  vs.  config/doc-facts-expected.yaml                  → V6 (kind=expected-mismatch, IC-23)
   → Abweichung: log.warning + Non-Zero-Status (kein Write)
consistency-check.py: V1..V9  →  exit 0 (keine Errors) / 1 (≥1 Error) / 2 (Skriptfehler)
   (V1..V9 sind No-op, solange docs-consolidation.enabled != true — IC-05-Common-Gate)
```

`sync.py:149` `--check` und `sync.py:153` `--validate` dürfen bei **V1, V2, V3, V6** nicht
grün sein. `--validate` ist laut `.meta-config/project.yaml:193` bereits `TEST_COMMAND`.

**Präzisierungsbedarf, RVW2-13 (in der dritten Korrekturrunde festgestellt — hier **nicht**
geändert, Entscheidungsvorlage):** der Satz nennt `--check` und `--validate` **gemeinsam**.
Belegt ist das Nicht-Grün-Sein nur für `--validate`: `_run_consistency_checks` wird
ausschließlich in `_handle_validate` aufgerufen (`scripts/lib/cli_commands.py:975`); der Pfad
`--check` liegt in `scripts/lib/sync_pipeline.py:914` und prüft **Drift generierter Dateien**, nicht
die Consistency-Suite. **Optionen (E-3, zur Entscheidung):** (a) Satz auf `--validate` allein
verengern; (b) `--check` mit der V6-Aussage („Handedit-Drift") verknüpfen, weil V6 genau den
Drift-Zustand beschreibt; (c) Satz unverändert lassen und die Abweichung nur im Plan führen
(Stand heute). **Bis zur Entscheidung** wird (c) angewendet: der Plan behandelt `--check` als
Drift-Lauf ohne Doku-Gate-Wirkung.

### (c) `--dry-run`

`sync_docs_consolidation(..., dry_run=True)` rendert vollständig, sammelt die Soll-Inhalte,
schreibt **nichts** (kein `write_checked`, kein `mkdir`, kein `log.md`-Append) und meldet
jeden Write-Kandidaten als `would-update`. Reihenfolge und Marker-Verarbeitung identisch zu (a).

### (d) Migration (W4–W6, W8)

```
git mv (Datei)  ──► docs/INDEX.md neu generieren (erkennt neue Pfade)
                 ──► V2 (Vollständigkeit) und V3 (Link-Integrität) prüfen
                 ──► V8 (Spec/Plan-Pfadkonvention) prüft nach W6
config-Edit (legacy:, PROJECT_STRUCTURE) ──► additiv, ein Release tolerant
```

### (e) Consumer-Projekt (Submodul-Layout)

```
Consumer-Projecten (docs-consolidation.enabled nicht true — Default)
   → log.skip("docs-consolidation", "disabled in project.yaml"); KEIN Schreibzugriff,
     KEIN docs/INDEX.md-Erzeugen, KEIN Snippet-Inlining in Consumer-Kontextdateien.
   → V1..V9: vollständiger No-op. Kein Doku-Check läuft gegen fremde docs/.
   → docs/ sind **nicht** generierte Provider-Artefakte (§7.1 des Designs):
     echter Downstream-Impact beschränkt sich auf B2, B5 (nur bei KE-Nutzung) und B6.
```

---

## 7. Acceptance Criteria

Jedes AC ist nummeriert, beobachtbar (Datei, Befehl, Exit-Code) und mit mindestens einem
Interface Contract und einem Verifikations-Check verknüpft. Testdateinamen sind verbindlich;
`tests/scenarios/`-Artefakte gehören **Track A** (siehe §2.3).

**Testpfad-Konvention innerhalb einer Gruppe:** das erste AC einer Gruppe nennt den vollen
Pfad (`tests/test_doc_facts.py::test_…`); die folgenden ACs derselben Gruppe schreiben nur
noch `::test_…` und meinen dieselbe Datei.

### M1 — DocFacts + Checks

- **AC-01** (IC-01, IC-02) Given ein vollständiges `agent-meta`-Checkout, when
  `compute_doc_facts(agent_meta_root, config, provider_config=provider_config)` läuft, then
  ist das Resultat ein `dict[str, str]` mit **genau** den 23 in IC-02 gelisteten Schlüsseln,
  alle Werte `str`, keine Exceptions, kein Schreibzugriff (Assertion: Verzeichnis-Hash von
  `agent-meta_root` vor/nach identisch). *Test `tests/test_doc_facts.py::test_fact_key_set_exact`.*
- **AC-02** (IC-02) — **rev. 0.3: durchsetzbar formuliert, Snapshot entfernt (NEW-8).** Given der
  Working Tree, when `compute_doc_facts()` läuft, then gilt für **jedes** Skalar-Faktum die
  **Formel**, nicht eine Zahl: `DOCS_AGENTS_SE_COUNT + DOCS_AGENTS_NONSE_COUNT ==
  DOCS_AGENT_TEMPLATES_COUNT`; `DOCS_AGENTS_SE_COUNT` == Anzahl `se-`-Präfix-Templates;
  `DOCS_AGENTS_NONSE_COUNT` == Anzahl der übrigen; `DOCS_PROVIDER_COUNT == len(providers)`;
  `DOCS_HOOKS_COUNT` == `glob(hooks/**/*.sh)` − `{lib/, release-gates/}` − `{*-impl.sh}`;
  `DOCS_HOOKS_1GENERIC_COUNT` == `glob(hooks/1-generic/*.sh)` − `{*-impl.sh}` **und**
  `DOCS_HOOKS_1GENERIC_COUNT <= DOCS_HOOKS_COUNT`;
  `DOCS_PIPELINES_ACTIVE_COUNT == DOCS_PIPELINES_COUNT − disabled overrides` **und**
  `DOCS_PIPELINES_ACTIVE_COUNT <= DOCS_PIPELINES_COUNT`; `DOCS_DOD_PRESET_COUNT ==
  len(dod-presets.yaml presets)`; `DOCS_TIER_PRESET_COUNT` == Top-Level-Keys von
  `tier-presets.yaml`; `DOCS_COMMAND_COUNT == len(glob(commands/1-generic/*.md))`;
  `DOCS_VERSION` == `Path("VERSION").read_text().strip()`. Kein Wert wird gegen eine im Test
  hinterlegte Konstante geprüft. *Test
  `tests/test_doc_facts.py::test_scalar_fact_formulas` (parametrisiert über eine
  Fixture-Konfiguration, **13** Formel-Assertions).*
  **Bewusste Entscheidung (rev. 0.3):** Rev. 0.2 führte zusätzlich einen Stand-Snapshot
  `test_snapshot_counts_2026_09_26` mit **zwölf** Zahlen, der als `xfail` markiert war — ein
  `xfail` ist **nicht durchsetzbar** und hätte einen Fehler nur dokumentiert. Der Snapshot ist
  deshalb **entfernt**; die Durchsetzung der konkreten Zahlen liegt **eindeutig** bei
  `config/doc-facts-expected.yaml` (IC-23) und wird von **AC-36** geprüft. Damit gibt es
  genau **einen** Ort mit Sollzahlen im Repo-Baum und einen **durchsetzbaren** AC dafür.
- **AC-03** (IC-02, IC-14) Given `DOCS_SCENARIO_COUNT` als `volatile`, when
  `apply_fact_blocks()` auf `README.md` oder `llms.txt` angewandt wird, then kommt der Wert
  **nicht** im Output vor. Given zwei Renderings von `docs/INDEX.md`, die sich **nur** in
  `DOCS_SCENARIO_COUNT` unterscheiden, when der `facts-hash` verglichen wird, then sind die
  Hashes **identisch**, und der unterschiedliche Wert steht in der `docs-volatile`-Sektion
  **am Dateiende vor dem Footer** (R1/M7). *Test
  `tests/test_doc_facts.py::test_volatile_fact_absent_from_hybrid_files` +
  `::test_volatile_fact_excluded_from_facts_hash`.*
- **AC-04** (IC-01) Given `config/ai-providers.yaml` fehlt, when `compute_doc_facts()` läuft,
  then ist `DOCS_PROVIDER_COUNT == ""`, alle übrigen Faktuen sind berechnet, und **kein**
  `SyncError` wird geworfen. *Test `tests/test_doc_facts.py::test_missing_source_is_fail_soft`.*
- **AC-05** (IC-04) Given `.meta-config/project.yaml` mit `systems-engineering.enabled: false`
  (Ist-Zustand `:12-13`) und `se-component-requirements` in `roles:` (Ist-Zustand `:148`),
  when `compute_active_roles()` läuft, then ist `se-component-requirements` **nicht** im
  Ergebnis, und `len(result) < len(config["roles"])` ist der einzige zulässige Grund.
  *Test `tests/test_doc_facts.py::test_se_role_excluded_by_gate_not_by_roles_list`.*
- **AC-06** (IC-06) Given ein Agent-Template mit `{{DOCS_PROVIDERS_BLOCK}}` im Body, when
  `consistency-check.py` läuft, then wird **kein** `placeholders.unknown`-Finding erzeugt
  (Prefix `^DOCS_` in `_DYNAMIC_PREFIXES`). *Test
  `tests/test_doc_facts.py::test_docs_prefix_registered_in_placeholders`.*
- **AC-07** (IC-05, §5.1.1, V1a+V1b — **ersetzt die Rev.-0.1-Fassung, K1**) Given die
  Positiv-Fixture `tests/fixtures/docs_v1_fixtures.md` mit genau diesen **vier wörtlichen**
  Zitatzeilen (Zeilennummern 1–4),
  `## Agent Roster — 74 Generic Agents`,
  `## Hooks (7 hooks, propagated to all providers)`,
  `  ai-providers.yaml          # 6 provider configs (Claude, Gemini, Opencode, Continue, Copilot, Mammouth)`,
  `VERSION                      # Current version (v1.0.0)`,
  when `check_no_manual_counts()` läuft, then sind es **genau 4** Findings mit
  `severity=WARNING`, `check="docs.no_manual_counts"`, `file="tests/fixtures/docs_v1_fixtures.md"`,
  `line` = 1/2/3/4, wobei `line` 1/2/3 `branch="V1a"` und `line` 4 `branch="V1b"` tragen.
  Nach Aktivierung von `docs-consolidation.checks.strict: true` sind dieselben vier Befunde
  `Severity.ERROR`. *Test `tests/test_doc_freshness.py::test_v1_flags_manual_counts` +
  `::test_v1_four_quote_lines_all_detected` — **Anker in Rev. 0.6 (K29) umgezogen**: die
  Erstfassung nannte `tests/test_doc_facts.py`, weil dort der Ort noch nicht getrennt war; W2-0
  **verschiebt** genau diese V1-Tests nach `tests/test_doc_freshness.py` (kein Duplikat).*
- **AC-08** (IC-05, §5.1.1, V1a+V1b) Given dieselbe Datei mit zusätzlich den drei
  Suppressions-Fällen (Zahl in einer `agent-meta:docs-*-Region`; Zahl mit
  `<!-- agent-meta:docs-exempt: … -->`; Zahl innerhalb eines Fenced-Code-Blocks), when
  `check_no_manual_counts()` läuft, then erzeugt **keiner** dieser drei Fälle ein Finding,
  und die Gegenprobe `| Agents | 74 |` außerhalb jeder Region erzeugt **genau eines**.
  *Test `::test_v1_exempt_and_inside_marker` +
  `::test_v1_noun_before_number_is_detected` — **Datei in Rev. 0.6 (K29) umgezogen** nach
  `tests/test_doc_freshness.py`.*
- **AC-09** (IC-05, V3) Given `README.md:722-723` unverändert (Layout-Einträge `howto/setup/`,
  `howto/features/`, die nicht existieren), when `check_internal_links()` läuft, then ≥ 1
  `Finding(severity=ERROR, check="docs.internal_links")` mit `file="README.md"`. Nach M-8
  (W8) ist derselbe Befund leer. *Test `tests/test_doc_facts.py::test_v3_flags_dead_howto_links` —
  **bleibt** in `test_doc_facts.py`: V3 wird nicht verschoben (Plan W2-0 verschiebt **nur** die
  V1-Tests); über die Fassade `docs.py` aufrufbar.*
  **Korrektur Rev. 0.6 (K23, Beleg):** die Fundstellen sind **`:722`/`:723`**, nicht `:721-723`
  — `README.md:721` (`howto/`) und `:724` (`howto/configs/`) existieren und tragen **kein**
  Finding. Beide Findings tragen `branch="layout"`, nicht `branch="link"`: sie stammen aus dem
  Layout-Zweig, der **nur** in `V3_ENTRY_RELPATHS` läuft
  (`scripts/lib/consistency/docs.py:591-598`, `_v3_layout_entries` `:526-551`).
- **AC-10** (IC-05, V7) Given eine Wiki-Seite mit `type: Architecture` **ohne**
  `derived-from`, when `check_wiki_staleness()` läuft, then ≥ 1 Finding
  `check="docs.wiki_staleness"`. Given `derived-from` mit `mtime(Quelle) > derived-at`, then
  das Finding nennt `stale-source`. *Test `::test_v7_missing_and_stale_derived_from`.*
- **AC-11** (IC-05, V5) Given Ist-Zustand F13/F21, when `check_role_generation_parity()` läuft,
  then ist das Finding **WARNING** (nicht ERROR), weil
  `systems-engineering.enabled == false`. Given eine Testkonfiguration mit
  `systems-engineering.enabled: true` und einer `roles:`-Rolle ohne Template, then ist es
  `ERROR`. *Test `::test_v5_severity_depends_on_se_gate`.*
- **AC-12** (IC-05, V2) Given eine getrackte `docs/**/*.md` außerhalb von `archive/`, when
  `check_docs_index_completeness()` läuft und `docs/INDEX.md` fehlt den Pfad, then ≥ 1
  `Finding(severity=ERROR, check="docs.docs_index_completeness")`; `docs/INDEX.md` selbst und
  Pfade unter `archive/` erzeugen **kein** Finding. *Test `::test_v2_missing_page`.*
- **AC-13** (IC-05) Given alle neun Checks, when `consistency-check.py` ohne `--strict` läuft
  und keine Errors vorliegen, then ist `exit 0`; bei genau einem Error `exit 1`. Die
  bestehenden Exit-Code-Dokumentation (`consistency-check.py:23-26`) bleibt gültig.
  *Test `::test_exit_codes_unchanged_with_new_checks`.*

### M2 — Renderer, Indexer, Brücke

- **AC-14** (IC-07, IC-08) Given `README.md` mit **einer** Region
  `<!-- agent-meta:docs-begin facts -->…<!-- agent-meta:docs-end facts -->`,
  when `apply_fact_blocks(text, facts)` läuft, then ist der Body durch den
  `render_doc_fact_block("facts", facts)`-Output ersetzt und Header/Footer **byte-identisch**
  geblieben. *Test `tests/test_doc_renderer.py::test_apply_fact_block_single_region`.*
- **AC-15** (IC-07) Given eine `docs-begin`-Region **ohne** `docs-end`, when
  `apply_fact_blocks()` läuft, then ist der Rückgabewert byte-identisch zum Eingabetext **und**
  genau ein `log.warning` mit `docs` als Channel wurde emittiert. *Test
  `::test_unbalanced_marker_is_noop_with_warning`.*
- **AC-16** (IC-07, IC-08) Given zwei Regionen gleichen Namens, when `apply_fact_blocks()`
  läuft, then ist nur die **erste** ersetzt (Muster `context.py:42-50`) und ein
  `log.warning` nennt die Duplikat-Region. *Test `::test_duplicate_region_first_only`.*
- **AC-17** (IC-09, IC-10) Given ein Fixture mit 5 `.md` unter `docs/` (davon 1 unter
  `archive/`, 1 ohne Frontmatter, 1 ohne `# `-Heading), when `build_index_model()` +
  `render_docs_index()` zweimal laufen, then sind beide Outputs **byte-identisch** (NFA-01)
  und das Ergebnis enthält: die 3 nicht-archivierten Pfade als Links, den `archive/`-Pfad
  **nicht**, für die Frontmatter-lose Datei den Dateinamen als `title` und `—` als
  description, und **keine** erfundene Beschreibung. *Test
  `::test_index_deterministic_and_archive_excluded`.*
- **AC-18** (IC-10, IC-14) Given ein gerendertes `docs/INDEX.md`, when der Footer geprüft
  wird, then enthält er `facts-hash: <16 hex>` und `generator: doc-indexer/1`, und **kein**
  Datum, **keine** Uhrzeit, **keinen** absoluten Pfad, **keinen** Benutzernamen. Ein Regex
  `\d{4}-\d{2}-\d{2}` auf den generierten Footer-Bereich findet **keinen** Treffer.
  *Test `::test_footer_has_no_timestamp`.*
- **AC-19** (IC-16) Given `README.md`, dessen `agent-meta:docs-begin facts`-Region von Hand
  editiert wurde (Handprosa unverändert), when ein Sync mit aktivierter
  Drift-Erkennung läuft, then (a) die **Handprosa** kein Drift-Finding erzeugt,
  (b) ein Drift-Finding mit `provider == "docs-consolidation"` und Pfad
  `README.md#docs:facts` gemeldet wird, (c) `apply_fact_blocks()` die editierte Region
  **nicht** überschreibt, und (d) **keine** Datei namens `README.md#docs:facts` im
  `project_root` entsteht (fail-soft, `generated_file_drift.py:379-386`).
  *Test `tests/test_generated_file_drift_docs.py::test_marker_body_only` +
  `::test_no_backup_for_hash_key`.*
- **AC-20** (IC-13, IC-15) Given ein `docs/INDEX.md` mit exakt dem vom Scaffold geschriebenen
  Inhalt **und** `docs-consolidation.enabled: true` **und** `index-mode: full` **und**
  `resolve_index_mode() == "file-index"`, when `sync_docs_consolidation(..., dry_run=False)`
  läuft, then wird die Datei durch das Voll-Index ersetzt, `log.action("UPDATE",
  "docs/INDEX.md", …)` erscheint **einmalig**, und ein zweiter Lauf meldet `unchanged` mit
  **null** Schreibvorgängen. *Test `tests/test_doc_renderer.py::test_skeleton_replaced_once`.*
- **AC-21** (IC-15, IC-13) Given **dieselbe** Ausgangslage, aber `index-mode: skeleton`,
  when `sync_docs_consolidation()` läuft, then bleibt `docs/INDEX.md` byte-identisch zum
  Scaffold-Skeleton (`is_file_index_skeleton(text) is True`). Given **dieselbe** Ausgangslage,
  aber `resolve_index_mode() == "knowledge-engine"` (KE autoritativ, Szenario 52) **und**
  `docs-consolidation.index-owner` **nicht** gesetzt (Abwesenheits-Default `auto`, IC-25), when
  `sync_docs_consolidation()` läuft, then wird **kein** `docs/INDEX.md` geschrieben, der
  Eintrag steht in `skipped`, und ein `log.note` nennt den Grund.
  **Bedingung Rev. 0.8 (P-4, §17.12.1 — **die KE-Autorität ist ab hier eine bedingte, keine
  ungefähre Vorbedingung**):** dieser zweite Block gilt **nur** für Projekte **ohne** die
  Deklaration `index-owner: docs-consolidation`. Für den deklarierenden Override gilt
  **AC-42** (Schreiben erlaubt) und **AC-44** (der Override hebt `index-mode: skeleton` und die
  Besitzregel **nicht** auf); für den **unveränderten** Bestand bleiben **AC-21** und **AC-38**
  wortgleich gültig. **Zur Freigabe ausstehend.**
  *Test `::test_skeleton_mode_preserves_scaffold` + `::test_ke_authoritative_writes_no_index` —
  **beide unverändert**, ihre Fixtures setzen den Key nicht
  (`tests/test_doc_renderer.py:2486-2488` bzw. `:2481-2484`).*
- **AC-22** (IC-12) Given die Stage-Reihenfolge, when `sync.py` läuft, then ruft
  `_sync_stage_docs_consolidation` **nach** `scaffold_spec_plan_dirs` (`sync_pipeline.py:935`)
  und **vor** `_sync_stage_generated_file_hash_capture` (`:1090-1099`).
  **Korrektur der Rev.-0.1-Fassung (K5):** bei `knowledge-engine.enabled: true` mit
  `index.mode: knowledge-engine` löst `resolve_index_mode()` (`spec_plan_scaffold.py:40-44`)
  **nicht** zu `file-index` auf — der KE-Index bleibt autoritativ, es wird **kein**
  `docs/INDEX.md` geschrieben. Rev. 0.1 behauptete hier das Gegenteil („gewinnt der
  Voll-Index") und hätte Szenario 52 gebrochen.
  *Test `tests/test_doc_renderer.py::test_stage_order_after_scaffold` +
  `::test_ke_index_stays_authoritative`.*
- **AC-23** (IC-13) Given `dry_run=True`, when `sync_docs_consolidation()` läuft, then sind
  **null** Dateisystem-Schreibvorgänge erfolgt (Hash-Vergleich des `project_root` vor/nach,
  mit Ausnahme der von `sync.py` selbst geschriebenen `sync.log`), `written` listet die
  Write-Kandidaten, und `knowledge/wiki/log.md` ist unverändert. *Test
  `::test_dry_run_no_writes`.*
- **AC-24** (IC-13, IC-22) Given eine `project.yaml` **ohne** `docs-consolidation`-Block
  (der Absenz-Fall, den alle 63 Szenario-Fixtures repräsentieren), when ein normaler Sync
  läuft, then emittiert der Log `skip` mit `docs-consolidation` / `disabled in project.yaml`,
  **keine** Datei unter `docs/` wird angelegt oder verändert, **und** alle neun Checks
  V1–V9 sind No-op (kein Finding aus `consistency-check.py`). Given explizit
  `enabled: false`, then identisches Verhalten. *Test
  `::test_disabled_flag_is_noop` + `::test_absent_block_is_noop`.*
- **AC-25** (IC-11) Given `snippets/docs/repo-facts.md` mit eigenem YAML-Frontmatter und
  `{{DOCS_VERSION}}` im Body, when `_build_snippet_variables()` läuft, then ist
  `variables["DOCS_REPO_FACTS_BLOCK"]` frontmatter-frei, CRLF-normalisiert, ohne führendes/
  abschließendes `\n` (Muster `config.py:1842-1858`), und `QUALITY_PIPELINES_BLOCK` bleibt
  unverändert vorhanden (kein Namensraumkonflikt, `config.py:1882`). *Test
  `tests/test_doc_facts.py::test_docs_snippet_inlining_contract`.*
- **AC-26** (IC-07) Given ein Projekt ohne `docs/`-Verzeichnis und
  `docs-consolidation.enabled: true`, when ein Sync läuft, then wird **kein** Verzeichnis
  angelegt; `skipped` enthält `docs/INDEX.md` und ein `log.note` nennt den Grund. *Test
  `::test_no_docs_dir_is_skipped_not_created`.*
- **AC-27** (IC-07, NFA-02) Given `README.md` mit `DOCS_`-Region und
  `llms.txt` mit `DOCS_PROVIDERS_BLOCK`, when `apply_fact_blocks()` mit identischem
  Faktum-Dict läuft, then sind die Outputs byte-identisch — unabhängig von der
  Python-Dict-Iterationreihenfolge des Aufrufers. *Test `::test_output_independent_of_dict_order`.*
- **AC-36** (IC-23, R14 — **neu**) Given die handgepflegte
  `config/doc-facts-expected.yaml` mit den **elf** Sollwerten, when
  `load_expected_doc_facts()` und `compare_expected_doc_facts()` laufen, then ist die
  Ergebnisliste **leer**. Given eine **manipulierte** Datei (ein Sollwert absichtlich falsch),
  when dieselben Funktionen laufen, then enthält die Liste **genau einen** Eintrag mit
  `kind == "expected-mismatch"` und nennt beide Werte; `compute_doc_facts()` bleibt dabei
  unverändert (die Sollwerte fließen **nicht** in die Berechnung ein). V6 meldet dafür ein
  `Finding(severity=ERROR, check="docs.docs_facts_fresh", kind="expected-mismatch")` **obwohl**
  der gerenderte Block exakt `compute_doc_facts()` entspricht — das ist der Test dafür, dass
  der Kreis `doc_facts → Renderer → V6` gebrochen ist. *Test
  `tests/test_doc_facts_expected.py::test_expected_values_match` +
  `::test_mismatch_is_reported`.*
- **AC-37** (IC-16, M8 — **neu**) Given `.meta-config/drift-allowlist.yaml` mit
  `allow-edits: ["README.md"]`, when `scan_generated_file_drift()` einen Marker-Body-Drift in
  `README.md` auswertet (Store-Key `README.md#docs:facts`), then wird das Finding
  **unterdrückt** — die Allowlist wird gegen den **Basis-Pfad** gematcht, nicht gegen den
  `#`-Key (Beleg: `is_allowlisted` nutzt `fnmatch` auf den ganzen String,
  `generated_file_drift.py:82-84`). Given **denselben** Allowlist-Eintrag und einen Drift in
  der **Handprosa** von `README.md`, then wird die Handprosa **nicht** gehasht und erzeugt
  **kein** Finding. *Test `tests/test_generated_file_drift_docs.py::test_allowlist_matches_base_path`.*
- **AC-38** (IC-13, IC-15, IC-22, NG-10 — **neu, K5-Regressionsgarantie**) Given die
  **unveränderten** Szenario-Fixtures `tests/scenarios/configs/{50,51,52,54,55,56}*.project.yaml`
  (keines enthält einen `docs-consolidation`-Key; `run.sh:46-52` spielt sie 1:1 ein), when
  `tests/scenarios/run.sh` über diese **sechs** Szenarien läuft, then sind **alle sechs grün**,
  und im Einzelnen gilt: `asserts/54:26-27` findet die Datei **und** den Scaffold-Inhalt
  `File-based index fallback`; `asserts/55:24-25` dito; `asserts/56:31` findet die Datei;
  `asserts/50:32` findet die Datei; `asserts/51:32` findet **keine** `docs/INDEX.md`;
  `asserts/52:44` findet **keine** `docs/INDEX.md`. **Tragende Begründung für `51:32`
  (rev. 0.3, NEW-7 — korrigiert):** nicht der Scaffold-Gate, sondern der **Absenz-Default**.
  `configs/51-spec-plan-disabled.project.yaml:1-34` enthält **keinen** `docs-consolidation`-Key;
  `spec-plan-workflow.enabled: false` (`:11-12`) betrifft ausschließlich den **Scaffold**, einen
  anderen Writer, und ist für dieses Assert **nicht** die Begründung. Entscheidend ist:
  `docs-consolidation.enabled` ist bei Abwesenheit **`false`** (IC-22), also endet
  `sync_docs_consolidation()` mit `log.skip` und **ohne jeden Schreibzugriff** (IC-13, Zeile 1) —
  der Generator legt in Szenario 51 weder `docs/INDEX.md` an noch ein `docs/`-Verzeichnis.
  Zwei **nachrangige** Rückfall-Abschirmungen, falls die erste je entfiele: (2) `docs/`
  existiert in 51 nicht (kein Scaffold ⇒ `spec_plan_scaffold.py:49-51` bricht **vor** jedem
  `mkdir` ab) ⇒ IC-13, letzte Zeile („Consumer ohne `docs/`-Verzeichnis → `skipped`, **kein**
  `mkdir`"); (3) `resolve_index_mode()` löst in 51 auf **`file-index`** (KE disabled
  `configs/51-…:7-8` **oder** `external-system-override.enabled: true` `:20-21`,
  `spec_plan_scaffold.py:80-97`; **K-4:** der frühere Anker `:40-44` ist veraltet — gemessen
  beginnt `resolve_index_mode` bei `:80` und endet bei `:97`) und das Ziel ist **nicht** das Scaffold-Skeleton ⇒ IC-13,
  Zeile 3 („`file-index` und Ziel ist nicht das Scaffold-Skeleton → **kein** Schreiben").
  **Kein** Assert-Skript und **keine** Fixture-Config wird geändert (NG-10). *Test
  `tests/scenarios/run.sh 50 51 52 54 55 56`
  (bestehender Runner, keine neuen Dateien).*

- **AC-42** (IC-25, IC-26, IC-15 — **neu, Rev. 0.8, P-1/P-2; ZUR USER-FREIGABE AUSSTEHEND**) —
  **Modus A (agent-meta-Ausnahme).** Given der **Live**-Block aus
  `.meta-config/project.yaml:398-401` **plus** `index-owner: docs-consolidation`, **plus**
  `knowledge-engine: {enabled: true}` und `spec-plan-workflow.index.mode: knowledge-engine`
  (⇒ `resolve_index_mode(config)[0] == "knowledge-engine"`, `spec_plan_scaffold.py:80-97`), when
  `sync_docs_consolidation(..., dry_run=False)` in einem leeren `docs/`-Baum läuft, then
  (a) `plan == {"written": ["docs/INDEX.md"], "unchanged": [], "skipped": []}`,
  (b) **genau eine** Action mit Tag `CREATE` (`doc_renderer.py:829-830`, `:861`),
  (c) `KE_AUTHORITATIVE_REASON` **nicht** im Log (verbindlich **negativ**; ein zusätzlicher
  Override-Hinweis ist **nicht** gepinnt — V-D5, §17.12.5), (d) die geschriebene Datei trägt **beide**
  Belege — der **`docs-facts`-Block** (`doc_renderer.py:629`, `lines.extend(_facts_section(facts))`,
  Definition `:531`) **und** die **Generator-ID** im Fact-Hash-Footer (`doc_renderer.py:635-639`,
  `FOOTER_BEGIN_MARKER` / `facts-hash` / `generator: doc-indexer/1` / `FOOTER_END_MARKER`; die
  Marker-Konstante selbst steht bei `:371`) — was beweist, dass `compute_doc_facts()` (`:821-824`)
  betreten wurde und der Lauf **nicht leer** war, und (e) ein **zweiter** Lauf meldet `unchanged` mit
  **null** Aktionen (Besitzzweig über `_carries_generator_id()`, `:644-655`, `:845-848`).
  **Modus B (Consumer im KE-Modus — dieselbe Konfiguration, nur ohne den Key).** Given
  **identische** Konfiguration **ohne** `index-owner`, when dieselbe Funktion läuft, then
  `plan == {"written": [], "unchanged": [], "skipped": ["docs/INDEX.md"]}`,
  `KE_AUTHORITATIVE_REASON` im Log, **null** Aktionen, und der `project_root`-Baum ist
  byte-identisch vorher/nachher. **Modus A und Modus B sind ein Testpaar** und unterscheiden
  sich in **genau einem** Config-Wert.
  *Tests **beide neu zu erstellen** in `tests/test_doc_renderer.py`:
  `::test_index_owner_override_writes_in_a_ke_authoritative_project` (Modus A) und
  `::test_index_owner_absent_keeps_the_ke_authoritative_block` (Modus B). Pin-Vorbild für die
  Fixture-Technik: `_KE_AUTHORITATIVE_CONFIG` (`:2481-2484`) und `_scaffolded_root()`
  (`:2510-2526`); Pin-Vorbild für den Tree-Vergleich: Muster `_tree_snapshot(root)` in
  `:2571`/`:2635`. **Neu** gegenüber dem Bestand ist hier nur, dass der **Live**-Block
  gelesen wird (Muster `_e2e_config()`, `:3209-3238`).*

- **AC-43** (IC-25, IC-13, AC-21 — **neu, Rev. 0.8, P-4; ZUR USER-FREIGABE AUSSTEHEND**) —
  **Die Absenz-Semantik ist wortgleich zum Bestand.** Given **keinerlei** `index-owner`-Angabe
  (Default `auto`, `INDEX_OWNER_AUTO`), when `_index_mode_block_reason(config)` auf einer
  KE-autoritiven Konfiguration läuft, then ist das Ergebnis **zeichengleich**
  `KE_AUTHORITATIVE_REASON` (`doc_renderer.py:277`, `:702-703`) — **kein** neuer Grund, **kein**
  zusätzlicher Log-Eintrag, **keine** veränderte Skip-Position. **Damit ist der Nachweis für
  beide Modi in einem Test erbracht:** der Consumer-Pfad ist unverändert (Modus B aus AC-42), und
  **nur** die Deklaration unterscheidet die Modi.
  *Test **neu zu erstellen**:
  `tests/test_doc_renderer.py::test_index_owner_absent_keeps_the_ke_authoritative_block` —
  **derselbe** Test wie der Modus-B-Test aus AC-42 (eine Behauptung, zwei Modi; **keine**
  Doppelpflege). Zusätzlich **bestehende, unveränderte** Pins für denselben Nicht-Override-Pfad:
  `::test_ke_authoritative_writes_no_index` (`:2614`) und
  `::test_ke_authoritative_writes_no_index_even_when_absent` (`:2650`).*

- **AC-44** (IC-25, IC-26/3, IC-15, IC-22 — **neu, Rev. 0.8, P-1; ZUR USER-FREIGABE AUSSTEHEND**) —
  **Die Ausnahme verengt das Gate, sie weicht nichts auf.** Given
  `index-owner: docs-consolidation` **und** `index-mode: skeleton`, when
  `sync_docs_consolidation()` läuft, then `skipped` + `SKELETON_MODE_REASON` und der
  Scaffold-Skeleton bleibt byte-identisch (IC-15 unberührt). Given `index-owner:
  docs-consolidation` **und** `index-mode: full` **und** ein **fremdes** Ziel (Text **ohne**
  Scaffold-Marker und **ohne** `doc-indexer/1`), when dieselbe Funktion läuft, then `skipped` +
  `OWNERSHIP_REASON` (`doc_renderer.py:855-858`) und **kein** Schreibzugriff. Given
  `index-owner: "docs"` (unbekannter Wert), when dieselbe Funktion läuft, then `skipped` +
  `UNKNOWN_INDEX_OWNER_REASON` und **kein** Schreibzugriff — fail-closed, **vor** jeder
  KE-Prüfung (IC-25 Zweig (1)).
  *Tests **neu zu erstellen**:
  `tests/test_doc_renderer.py::test_index_owner_override_does_not_relax_skeleton_or_ownership`
  (Fälle a und b) sowie
  `::test_unknown_index_owner_is_fail_closed` (Fall c; Muster
  `::test_unknown_index_mode_is_fail_closed`, `:2720-2737`). Bestehende, **unveränderte** Pins
  für dieselben Zusagen: `::test_skeleton_mode_preserves_scaffold` (`:2559`),
  `::test_skeleton_mode_creates_no_index_at_all` (`:2590`),
  `::test_scaffold_guard_recognises_only_the_skeleton` (`:2529`).*

- **AC-45** (IC-13, IC-26/5, AC-23 — **neu, Rev. 0.8; ZUR USER-FREIGABE AUSSTEHEND**) —
  **`dry_run` bleibt schreibfrei unter dem Override.** Given
  `index-owner: docs-consolidation` im KE-Modus **und** `dry_run=True`, when
  `sync_docs_consolidation()` läuft, then sind **null** Dateisystem-Schreibvorgänge erfolgt
  (Tree-Vergleich vorher/nachher), `written` enthält **dennoch** `docs/INDEX.md`, und die Action
  ist `WOULD-CREATE` (nicht `CREATE`) getaggt (`doc_renderer.py:867`) — ein Dry-Run-Log darf
  nicht als Schreibprotokoll lesbar sein. **Consumer-Modus:** dieselbe Konfiguration **ohne** den
  Key ⇒ `written` bleibt **leer**, `skipped` enthält den Pfad; ein Dry-Run kann einen Skip
  **nicht** vortaeuschen.
  *Test **neu zu erstellen**:
  `tests/test_doc_renderer.py::test_index_owner_override_keeps_dry_run_free_of_writes`.
  Bestehender, **unveränderter** Pin für den Vertrag selbst: `::test_dry_run_no_writes` (AC-23).*

- **AC-46** (IC-22, IC-25, AC-39 — **neu, Rev. 0.8, P-3 / P-3 (e); ZUR USER-FREIGABE AUSSTEHEND**) —
  **Der Schema-Wächter pinnt die zwei Werte.** Given
  `config/project-config.schema.json`, when `docs-consolidation.properties` geparst wird, then
  existiert `index-owner` mit `enum == ["auto", "docs-consolidation"]` und `default == "auto"`.
  Given eine `project.yaml` mit `index-owner: "docs-consolidation"`, when die Config validiert
  wird, then ist die Schema-Validierung grün. Given `index-owner` mit einem der Werte
  `"knowledge-engine"`, `"agent-meta"`, `"docs"` **oder** ein nicht-stringiger Wert, when
  validiert wird, then `jsonschema.ValidationError` — der Schreibvorgang bleibt also
  **fail-closed**, und ein Tippfehler ist ein **Validierungsfehler**, kein stiller No-op
  (`additionalProperties: false`, `config/project-config.schema.json:2470`).
  *Tests **neu zu erstellen** in `tests/test_docs_consolidation_migration.py`, Muster der
  bestehenden Enum-Tests `::test_index_mode_enum_accepts_both_modes` (`:174-176`) und
  `::test_index_mode_enum_rejects_everything_else` (`:179-182`) ⇒
  `::test_index_owner_enum_accepts_both_values` und
  `::test_index_owner_enum_rejects_everything_else`.*

### M3 — Migration

- **AC-28** (IC-17, M-1, M-3, M-4, M-6) Given W4/W5/W6 abgeschlossen, when
  `python3 scripts/sync.py --validate` läuft, then existieren `ARCHITECTURE.full.md`,
  `docs/superpowers/`, `howto/` **und** `docs/howto/` **nicht** mehr, und
  `git log --diff-filter=R --name-only` dieser Wellen zeigt für jede verschobene Datei ein
  **R**ena **+ A**dd-Paar (kein Inhalts-Diff, wenn `git log -M --follow` genutzt wird).
  *Test `tests/test_docs_consolidation_migration.py::test_moves_are_renames`.*
- **AC-29** (IC-18, IC-03, M-7 — **entzirkelt, M5**) Given der neue `ARCHITECTURE.md`-Stub,
  when er gelesen wird, then (a) enthält er einen generierten Diagramm-Index, einen Link auf
  `docs/architecture/INDEX.md` und auf `docs/architecture/00-overview-full.md` und **keine**
  eigene Architektur-Prose; (b) enthält er **keine** Zeile mit `Repo version:` **und**
  `docs/architecture/00-overview-full.md` enthält die Stale-Deklaration
  (`Repo version:` / `last substantively reviewed`); (c) `compute_wiki_staleness()` liefert
  für `knowledge/wiki/concepts/architecture.md` mit `derived-from:
  docs/architecture/00-overview-full.md` einen auswertbaren Wert (kein
  `missing-derived-from`); (d) der Link in `llms.txt:24` bleibt gültig. Der AC verbietet
  **nicht** etwas, dessen Quelle er gleichzeitig voraussetzt — die Quelle wandert mit (M-7).
  *Test `::test_architecture_stub_shape` + `::test_stale_declaration_moved_with_longform`.*
- **AC-30 (IC-17, M-8) — NEU FASUNG Rev. 0.6, U-2/K22: Scope auf `README.md` + `llms.txt`
  verengt.** Given W8 abgeschlossen, when `check_internal_links()` läuft, then sind
  **`README.md` und `llms.txt`** frei von Findings auf **relative interne Links** (V3, exit 0
  **im AC-30-Scope**). `docs/**` ist **nicht** mehr AC-30-Scope; die dort am 2026-09-27
  gemessenen **25** toten Links werden als **Follow-up `F-DOCS-LINKS-2026-09-27`** geführt
  (Owner `developer`, Termin **2026-10-11**, §17.10.3) — **nicht** als AC, **nicht**
  stillschweigend. *Test `::test_no_dead_internal_links_after_migration` (unverändert benannt;
  der Test prüft ab Rev. 0.6 den verengten Scope).*
  **Belege:** Baseline-Messung 2026-09-27 (Übergabe vom Parent) — `check_internal_links()` direkt
  aufgerufen: **27** Findings = **25** `branch=="link"` (alle `docs/**`, **0** in `README.md`/
  `llms.txt`) + **2** `branch=="layout"` (`README.md:722`, `README.md:723`); `llms.txt`: **0**.
  **Weigerungsnachweis:** die Verengung ist **nur** tragfähig, weil die **2** verbleibenden
  Findings in **`README.md`** liegen und damit **im** verengten Scope bleiben; der bestehende
  Task **W8-2** behebt sie (`Files:` enthält `README.md`) — **kein** zusätzlicher Task.
  Volltext §17.10.2.
- **AC-31** (IC-17, M-9, IC-03) Given eine Wiki-Seite in `knowledge/wiki/concepts/` mit
  `type: Architecture`, when die W5-Annotation angewandt ist, then trägt sie
  `derived-from: <existierender Rel-Pfad>` **und** `derived-at: <ISO-8601>`, und der Diff
  dieser Welle ist **ausschließlich** additiv (keine gelöschte Zeile außer der Ersetzung eines
  bestehenden `status:`-Werts). *Test `::test_wiki_annotation_is_additive`.*
- **AC-32** (IC-17, M-13, IC-22) Given `.meta-config/project.yaml`, when die `legacy:`-Liste
  gelesen wird, then enthält sie **vier** Einträge (die zwei alten + die zwei neuen Archivpfade,
  Ist-Stand `:61-63` hat zwei), und ein Sync mit einer der alten Pfade erzeugt eine
  Deprecation-WARNING statt eines Fehlers. *Test `::test_legacy_list_extended_additively`.*
- **AC-39** (IC-17, M-11, R15, IC-22, IC-25 — **Zählung berichtigt in Rev. 0.8, P-3 (e) / „P-3-E"; ZUR
  USER-FREIGABE AUSSTEHEND**) Given `config/project-config.schema.json`, when die Datei geparst
  wird, then existiert ein **geschlossener** Top-Level-Block `docs-consolidation`
  (`additionalProperties: false`, `config/project-config.schema.json:2470`) mit **genau** den
  Properties aus IC-22, **keinem** Provider-Namen als Property-Namen, und **keinem** Projekt- oder
  Repo-Namen. **Property-Zahl: Rev. 0.8 setzt den gemessenen Stand.** Der Block enthält **sechs**
  Properties — `enabled`, `index-mode`, `checks`, `sources`, `volatile-facts`
  (Schema-Block-Ist-Stand vor Rev. 0.8, `config/project-config.schema.json:2424-2469`, **und**
  Test-Pin `tests/test_docs_consolidation_migration.py:45-51` — **nicht** ein `.meta-config`-Stand:
  dort trägt der Block nur `enabled` und `checks.strict`, `.meta-config/project.yaml:398-401`)
  **plus `index-owner`** (IC-25). **Die Zahl „sechs" aus
  der Fassung bis Rev. 0.7 war bereits damals falsch**: der Block hatte **fünf** Properties
  (gemessen `config/project-config.schema.json:2424-2469`), und der **gepinte** Test ebenfalls
  **fünf** (`tests/test_docs_consolidation_migration.py:45-51`, `_EXPECTED_PROPERTIES`, geprüft
  in `::test_schema_block_present_and_closed`, `:99-103`). **Der sechste Eintrag der IC-22-Tabelle
  ist `knowledge-engine.okf.index-mode`** und liegt in einem **anderen** Block — deshalb war
  „genau den sechs Properties aus IC-22" eine Verwechslung von **Tabelle** und **Block**.
  **Verbindlich:** `_EXPECTED_PROPERTIES` wird um `index-owner` erweitert (**fünf → sechs**);
  `::test_schema_block_present_and_closed` prüft die Block-Menge, und die IC-22-Tabelle zählt
  **sieben** Zeilen. Given eine `project.yaml`, die `docs-consolidation.enabled: true` setzt, when
  die Config geladen wird, then ist die Schema-Validierung grün. *Test
  `tests/test_docs_consolidation_migration.py::test_schema_block_present_and_closed`
  (bestehend, **Sollwert-Erweiterung** `_EXPECTED_PROPERTIES` `:45-51`) +
  `::test_index_owner_enum_accepts_both_values` (AC-46, neu).*
- **AC-40** (IC-02, IC-22 — **neu, schließt die W8-Lücke M3**) Given W8 abgeschlossen, when
  `llms.txt` gelesen wird, then kommt die Providerzahl **nicht** mehr als handgeschriebene
  Zahl im Fließtext vor, sondern ausschließlich aus einem `agent-meta:docs-*-Block`, dessen
  Wert `DOCS_PROVIDER_COUNT` entspricht; dasselbe gilt für `README.md:690` und für
  `docs/INDEX.md`. *Test `::test_provider_count_is_generated_in_readme_llms_index`.*

### M4 — Knowledge-Index-Generierung

- **AC-33** (IC-19, IC-22) Given `knowledge-engine.okf.index-mode: llm`, when ein Sync läuft,
  then ist `knowledge/wiki/index.md` byte-identisch (Generator stumm). Given
  `index-mode: generated`, then wird `index.md` deterministisch neu gerendert, und jede
  Wiki-Seite erscheint **genau einmal**. *Test
  `tests/test_knowledge_index_gen.py::test_index_mode_flag_and_determinism`.*
- **AC-34** (IC-20) Given zwei aufeinanderfolgende Syncs, von denen der erste genau eine
  Wiki-Datei ändert und der zweite keine, when beide laufen, then wird im ersten **eine** Zeile
  im Format `YYYY-MM-DD HH:MM — index/update — <summary>` angehängt und im zweiten **keine**;
  der bestehende Log-Inhalt ist in beiden Fällen unverändert (append-only). *Test
  `::test_log_append_only_on_change`.*
- **AC-35** (IC-19, IC-24, M-6 — **abgeschwächt, M6**) Given `index-mode: generated` und eine
  handgeschriebene `knowledge/wiki/index.md`, when der Generator **das erste Mal** aktiviert
  wird, then existiert **vor** dem ersten Rewrite eine vollständige Sicherung des
  Alt-`index.md` (Sibling `index.md.sync-backup-<YYYYmmdd-HHMMSS>` mit exakt dem Alt-Inhalt,
  Muster `backup_drifted_files`, `generated_file_drift.py:354-402, :388`, dry-run-geeignet).
  **Zurückgezogen** ist die Rev.-0.1-Forderung „der Rollback `index-mode: llm` stellt den
  Ausgangszustand byte-identisch wieder her": `index-mode: llm` stellt den **Generator**
  stumm, nicht die Datei wieder her; es gibt dafür keinen CLI-Pfad
  (`cli_commands.py:864`, `:888-900`, `backup.py:376+` sind Provider-Zip-Operationen).
  Der **Restore-Pfad ist jetzt IC-24 spezifiziert**, nicht behauptet.
  *Test `tests/test_knowledge_index_gen.py::test_first_activation_is_backed_up`.*
- **AC-41** (IC-24, M6 — **neu, ersetzt die Rückforderung aus Rev. 0.1**) Given die
  Sicherung `knowledge/wiki/index.md.sync-backup-<ts>` aus AC-35 und ein durch den
  Generator überschriebenes `index.md`, when `restore_wiki_index(project_root, log)` läuft,
  then ist `knowledge/wiki/index.md` **byte-identisch** mit dem Alt-Inhalt (verglichen über
  `io.content_hash`), und der Rückgabewert nennt genau den berührten Rel-Pfad. Given
  `dry_run=True`, when dieselbe Funktion läuft, then wird **nicht** geschrieben, aber der
  Zielpfad wird gemeldet. Given **weder** Sicherung **noch** Git-Tracking, when dieselbe
  Funktion läuft, then wird **nicht** geschrieben und `log.error` nennt den Grund
  (fail-closed, kein stiller Datenverlust). *Test
  `tests/test_knowledge_index_gen.py::test_restore_from_backup_sibling` +
  `::test_restore_dry_run` + `::test_restore_fails_closed_without_source`.*

---

## 8. Nicht-funktionale Anforderungen

| # | Anforderung | Nachweis |
|---|---|---|
| NFA-01 | **Idempotenz.** Zwei Läufe ohne Eingangsänderung erzeugen **null** Schreibvorgänge und identischen Output. | AC-17, AC-20, AC-33; Muster `standalone.py:386-389, :404-410` |
| NFA-02 | **Diff-Minimalität.** Generierte Dateien enthalten **keinen Zeitstempel, keine absolute Pfadangabe, keine Host-/User-Daten**. Der einzige veränderliche Teil ist der `facts-hash` (Muster) über die **nicht-volatilen** Fakten; Volatile Werte erzeugen genau **eine** Zeilen-Diff am Dateiende (M7). Der Hash bleibt stabil, solange kein nicht-volatiles Faktum kippt; er wechselt nur bei geänderten Faktuen. | AC-18, AC-03, AC-27, AC-34; Muster `standalone.py:362-368` |
| NFA-03 | **Provider-Parität.** Die Doku-Generierung ist **provider-neutral**: identischer `docs/INDEX.md`-, `README.md`- und `llms.txt`-Output unabhängig von der aktiven Provider-Menge. Kein `if provider == …` in M1–M4; Provider-Unterschiede nur über `provider_config`-Capability-Keys. | AC-01, IC-22 (keine Provider-Namen in Config-Keys); Regel `provider-agnostic`, Guard `tests/test_provider_agnostic_dispatch.py` |
| NFA-04 | **Downstream-Kompatibilität.** agent-meta ist ein Git-Submodul. In Consumer-Projekten sind M2 **und alle Checks V1–V9** per Default **aus** (`docs-consolidation.enabled` nicht `true` — Fail-off wie `knowledge.py:127`); M4 berührt `knowledge/` nur bei `index-mode: generated`. | AC-24, AC-26, AC-33, §6(e), IC-22 |
| NFA-05 | **Handedit-Schutz.** Eine von Hand editierte generierte Region wird **nicht** überschrieben, sondern gemeldet. Überschreiben ist explizit kein Ziel (Muster `generated_file_drift.py:591-596`: „skip-overwrite is an explicit non-goal"). Für Marker-Bodies ist das zwingend, weil der `#`-Key **kein** Backup erzeugen kann (IC-16, M8-Tabelle). | AC-19 |
| NFA-06 | **Rollback je Welle.** Jede Welle W1–W8 hat einen benannten, in §4/IC-17 angegebenen Rückrollpunkt, der **keine** andere Welle invalidiert. W7 hat zusätzlich einen **spezifizierten** Restore-Pfad (IC-24) und ist deshalb **isoliert und letzte Welle**. | AC-20, AC-21, AC-32, AC-35, AC-41 |
| NFA-07 | **Stdlib-only.** M1, M2, M4 importieren ausschließlich die Python-Standardbibliothek plus bestehende `scripts/lib`-Module; keine externe Abhängigkeit (Projektregel „Keine externen Python-Dependencies außer Stdlib"). Dependency-Invariante `variables.py:9-17` (keine Zyklen). | AC-01; Modul-Docstrings mit explizitem Importverbot |
| NFA-08 | **Begrenzter Blast Radius.** M3 berührt ausschließlich `docs/`, `knowledge/wiki/`, `README.md`, `ARCHITECTURE.md`, `.meta-config/project.yaml` (additive Config-Zeilen) und `config/project-config.schema.json` (ein geschlossener Block). `agents/`, `hooks/`, `commands/`, `config/*.yaml` und `knowledge/sources/` werden **nicht** inhaltlich angefasst — **eine** Ausnahme ist IC-21 `agents/1-generic/knowledge-indexer.md` in W7 (Rollback `git checkout`, Kollisionsvermerk R19, Reihenfolge in IC-21 verbindlich). | AC-28, AC-31, AC-32, AC-39 |
| NFA-09 | **Beobachtbare Drift.** Jede vom Generator geschriebene Doku-Datei ist über die Hash-Baseline drift-detektierbar (IC-16), inklusive Handprosa-Schutz (nur Marker-Body) und korrekter Allowlist-Wirkung auf den Basis-Pfad. | AC-19, AC-37 |
| NFA-10 | **Keine Secrets.** Generierte Dateien enthalten keine Env-Werte, Tokens oder Secrets. Die einzige Wertquelle ist `VERSION` plus Zählungen/Config-Struktur. | AC-18, IC-02 |
| NFA-11 | **Unabhängige Verifikation der Zahlen (neu, R14).** Die Faktum-Formel wird **nicht** nur von einem Kreis aus Generator und Selbstcheck verifiziert, sondern gegen eine zweite, handgepflegte Quelle (`config/doc-facts-expected.yaml`, IC-23) geprüft. **Elf** Sollwerte, jenseits der Reachability jedes Generators. | AC-36 |

---

## 9. Trace-Matrix

### 9.1 AC → Welle → betroffene Dateien

| AC | Welle | Betroffene Dateien (Code / Config / Doku) | V-Check |
|---|---|---|---|
| AC-01 | W1 | `scripts/lib/doc_facts.py` (neu) | — |
| AC-02 | W1 | `scripts/lib/doc_facts.py`; gelesen: `config/tier-presets.yaml`, `config/dod-presets.yaml`, `config/role-defaults.yaml`, `hooks/1-generic/*.sh`, `hooks/**/*.sh`, `commands/1-generic/`, `VERSION` | — |
| AC-03 | W1 | `scripts/lib/doc_facts.py`, `scripts/lib/doc_renderer.py` | — |
| AC-04 | W1 | `scripts/lib/doc_facts.py` | — |
| AC-05 | W1 | `scripts/lib/doc_facts.py`, `scripts/lib/roles.py:129` (gelesen) | V5 |
| AC-06 | W1 | `scripts/lib/consistency/placeholders.py:128-131` | — |
| AC-25 | W1 | `scripts/lib/config.py:1861-1914`, `snippets/docs/repo-facts.md` (neu) | — |
| AC-39 | W1, **W3-6** | `config/project-config.schema.json` (M-11; Block `:2421`, Properties `:2424-2469`, `additionalProperties: false` `:2470`) | — (Schema-Form, per Unit-Test `::test_schema_block_present_and_closed`) |
| AC-07 | W2 | `scripts/lib/consistency/docs.py`, `tests/fixtures/docs_v1_fixtures.md` | V1a, V1b |
| AC-08 | W2 | `scripts/lib/consistency/docs.py`, `tests/fixtures/docs_v1_fixtures.md` | V1a, V1b |
| AC-09 | W2 | `scripts/lib/consistency/docs.py`, `README.md:721-723` | V3 |
| AC-10 | W2 | `scripts/lib/consistency/docs.py`, `scripts/lib/doc_facts.py::compute_wiki_staleness` | V7 |
| AC-11 | W2 | `scripts/lib/consistency/docs.py` | V5 |
| AC-13 | W2 | `scripts/consistency-check.py:52-56` | alle |
| AC-36 | W2 | `config/doc-facts-expected.yaml` (neu), `scripts/lib/doc_facts.py::load_expected_doc_facts` | V6 (`expected-mismatch`) |
| AC-12 | W3 | `scripts/lib/consistency/docs.py` | V2 |
| AC-14 | W3 | `scripts/lib/doc_renderer.py`, `README.md` | V6 |
| AC-15 | W3 | `scripts/lib/doc_renderer.py` | V6 |
| AC-16 | W3 | `scripts/lib/doc_renderer.py` | V6 |
| AC-17 | W3 | `scripts/lib/doc_index.py` (neu), `scripts/lib/doc_renderer.py` | V2 |
| AC-18 | W3 | `scripts/lib/doc_renderer.py` (IC-10/IC-14) | — (Determinismus, per Unit-Test) |
| AC-19 | W3 | `scripts/lib/generated_file_drift.py:344-349, :379-386, :405-425` | — (Drift-Store, per Unit-Test) |
| AC-20 | W3 | `scripts/lib/spec_plan_scaffold.py:24, :62-68`, `scripts/lib/doc_renderer.py` | V4 |
| AC-21 | W3 | `scripts/lib/spec_plan_scaffold.py:28-30, :80-97`, `.meta-config/project.yaml` (neuer Key `index-owner`, **bedingt** — AC-21 gilt nur, wenn der Key **nicht** gesetzt ist, §7 AC-21 Modus B / P-4) | V4 |
| AC-22 | W3 | `scripts/lib/sync_pipeline.py:922-945`, `scripts/lib/spec_plan_scaffold.py:40-44` | — |
| AC-23 | W1 | `scripts/lib/doc_renderer.py`, `scripts/lib/knowledge.py` (später) | — |
| AC-24 | W1 | `.meta-config/project.yaml` (neuer Key `docs-consolidation.enabled`) | — |
| AC-26 | W3 | `scripts/lib/doc_renderer.py` | — |
| AC-27 | W3 | `scripts/lib/doc_renderer.py` | V6 |
| AC-37 | W3 | `scripts/lib/generated_file_drift.py:82-84` | — (Allowlist, per Unit-Test) |
| AC-38 | W3 | `tests/scenarios/configs/{50,51,52,54,55,56}*.project.yaml` (unverändert) | — (bestehender Runner) |
| AC-28 | W4, W5, W6 | `ARCHITECTURE.full.md` → `docs/architecture/00-overview-full.md`; `docs/superpowers/{specs,plans}` → `docs/{specs,plans}/archive/superpowers/`; `howto/`, `docs/howto/` → `docs/guides/` | V8 |
| AC-29 | W4 | `ARCHITECTURE.md`, `docs/architecture/00-overview-full.md` | V3 |
| AC-30 | W8 | `README.md:722-723` (M-8; **korrigiert Rev. 0.6, K23** — vorher `README.md:721-724`; `:721`/`:724` existieren und tragen **kein** Finding) | V3 |
| AC-31 | W5 | `knowledge/wiki/**` (additive Frontmatter-Zeile) | V7 |
| AC-32 | W6 | `.meta-config/project.yaml:61-63` | V8 |
| AC-40 | W8 | `llms.txt:5`, `README.md:690` (M-12-Umfeld) | V1a, V6 |
| AC-33 | W7 | `scripts/lib/knowledge.py:103-205`, `.meta-config/project.yaml:18-29` | V7 |
| AC-34 | W7 | `scripts/lib/knowledge.py`, `knowledge/wiki/log.md:13-17` | — |
| AC-35 | W7 | `scripts/lib/knowledge.py`, `agents/1-generic/knowledge-indexer.md`, `knowledge/schema.md:41-46` | — |
| AC-41 | W7 | `scripts/lib/knowledge.py::restore_wiki_index` (IC-24) | — |
| AC-42 | **W3-6** | `scripts/lib/doc_renderer.py:663-711` (IC-25 Entscheidungsfolge, Zweig (1)/(2)); `tests/test_doc_renderer.py` (**5 neue Tests**, §17.12.4 T-2) | — (Unit-Test; Paar Modus A/B, §9.1 V-Check-Spalte) |
| AC-43 | **W3-6** | `scripts/lib/doc_renderer.py:277, :702-703`; `tests/test_doc_renderer.py` (1 neu + 2 **bestehend unverändert** `:2614`, `:2650`) | — (Unit-Test, Absenz-Semantik) |
| AC-44 | **W3-6** | `scripts/lib/doc_renderer.py:255-259, :663-711`; `tests/test_doc_renderer.py` (2 neu; bestehend `:2529`, `:2559`, `:2590`) | — (Unit-Test; `skeleton`/Besitzregel) |
| AC-45 | **W3-6** | `scripts/lib/doc_renderer.py:861-867` (`write_checked` / Dry-Run-Tag); `tests/test_doc_renderer.py` (1 neu; `::test_dry_run_no_writes`, AC-23, unverändert) | — (Unit-Test, `dry_run`) |
| AC-46 | **W3-6** (T-8/T-3/T-5, Reihenfolge **V-D7**), Doku-Teil **E-13-abhängig** (offen) | `config/project-config.schema.json:2421-2470` (Property `index-owner`); `tests/test_docs_consolidation_migration.py` (T-5: 2 neue Enum-Tests; T-3 `_EXPECTED_PROPERTIES` `:45-51`; T-4 Kommentar `:42-44`) | — (Unit-Test, Schema-Form) |

**V-Check-Spalte, korrigiert (M2).** Rev. 0.1 mappte sachfremde Checks: AC-19 (Marker-Body-Drift)
→ V9 `check_stale_backups` (Backup-Leichen) ist **falsch**, AC-18 (Footer-Determinismus) → V2 und
AC-29 (Stub-Form) → V3/V4 sind **irrelevant**. Neu: AC-19, AC-37, AC-38, AC-34, AC-35, AC-41
sind Invarianten **ohne** Konsistenz-Check (Store-, Szenario- und Restore-Ebene) und werden
per Unit-Test bzw. bestehendem Runner abgesichert — das ist die in §16 geforderte Begründung,
kein Lückenbleiben.

**Nachtrag Rev. 0.8 (K-79, RVW8-3 — schließt dieselbe Lücke für AC-42…AC-46).** AC-42…AC-46 sind
**Gate-Ebene**-Invarianten, keine Dokumenteigenschaften: sie handeln vom *Zustand des Generators*
(erlaubt/verweigert, fail-closed, `dry_run`) bzw. von der *Form des Schemas*. V1–V9 lesen
`docs/**` bzw. `README.md` — **keiner** von ihnen beobachtet den Verzweig in
`_index_mode_block_reason()`. Eine Zuordnung wäre **Scheinpräzision** (dieselbe Fehlerklasse wie
AC-19/V9, die Rev. 0.1 zurückgenommen hat). Sie werden daher durch die in §17.12.4 benannten
Unit-Tests mit festen Namen abgesichert (`::test_index_owner_*` in `tests/test_doc_renderer.py`;
`::test_index_owner_enum_*` + `::test_schema_block_present_and_closed` in
`tests/test_docs_consolidation_migration.py`). **AC-42(a)(b)(c)** sind zusätzlich durch den
W3-6-Nachweis `python3 scripts/sync.py --dry-run` bzw. den zweiten Sync-Lauf (§17.12.4 Zeile „W3-6
Kernlieferung") end-to-end belegt.

**Entfernter Beleg der AC-30-Zeile — `docs/REQUIREMENTS.md:21` (Rev. 0.6, K23; die Zeile selbst
bleibt bestehen, nur der Beleg ist berichtigt).** Die Trace-Matrix nannte bis Rev. 0.5
`docs/REQUIREMENTS.md:21` als zweiten Beleg der AC-30-Zeile. **Die Zeile war veraltet.**
`docs/REQUIREMENTS.md:21` (REQ-CMD-09) nennt `howto/commands.md`, `CLAUDE.md` und
`howto/instantiate-project.md` in **Backticks** innerhalb einer Tabellenzeile. V3 extrahiert
ausschließlich **Link-Syntax** — Inline-Links, Referenz-Definitionen und `href`-Attribute
(`scripts/lib/consistency/docs.py:436-446`, `_v3_link_targets` `:497-502`) — ein Backtick-Pfad ist
**kein** Link und wird **nicht** gemeldet. Deckt sich mit der Baseline-Messung 2026-09-27
(Übergabe vom Parent): **0** Findings in `docs/REQUIREMENTS.md`. Der Pfadbefund selbst ist
**echt** und bleibt als **F15-N** (§2.3) und als manueller Befund in F15 erhalten — er ist aber
**kein V3-Nachweis** und trägt AC-30 nicht. **Konsequenz:** die AC-30-Zeile wird allein durch
`README.md:722-723` getragen, und diese beiden Stellen sind **beide** vom bestehenden Task **W8-2**
behebbar (§17.10.2).

### 9.2 Welle → Modul → AC-Menge → Parallelität

| Welle | Modul | Inhalt | AC | Abhängig von | Parallel mit | Rückrollpunkt |
|---|---|---|---|---|---|---|
| W0 | — | Design-Freeze, Contract-Liste, **ein Wellen-Branch für das gesamte Vorhaben** (`feat/repository-documentation-consolidation-main`, Basis `origin/main`) mit **einem** PR gegen `main`; Wellen-Zuordnung über die **Wellenkennung im Commit-Titel**. **Rev. 0.4 — Ausführungskorrektur 2026-09-26 (OP-1):** ersetzt die Fassung Rev. 0.1–0.3 „**ein Branch pro Welle** (`chore/docs-consolidation-w<N>`), gestapelte PRs"; Einzelheiten und Belege in §17.6, Verbindlichkeitsformulierung im Absatz „PR-/Branch-Strategie" direkt unter dieser Tabelle — Entscheidungs-Records zu OQ2/OQ6/OQ8 — **OQ6/OQ8 entschieden 2026-09-26** (§11.2: `docs/INDEX.md` tracked, **kein** `.gitignore`-Eintrag; Regeneration über Sync/Validator) | — | — | — | — |
| W1 | M1+M2 | C1 DocFacts, C2 DocRenderer, C3 Snippet-Bridge, `config/doc-facts-expected.yaml`; Schema-Block (M-11); **rein additiv**, kein Datei-Diff außer `llms.txt` | AC-01…AC-06, AC-23…AC-25, AC-39 | W0 | W2 (verschiedene Dateien) | revert; kein Datei-Diff |
| W2 | M1 | Checks V1a/V1b, V3, V5, V6 (inkl. Sollwert-Vergleich), V7; **V1 startet WARNING**; V1-Fixture; **Rev. 0.6 (U-1/K18): Modul-Split — `consistency/docs.py` wird zur Fassade, die Prüfebene wird auf `docs_links.py` / `docs_freshness.py` / `docs_wiki.py` / `docs_index.py` aufgeteilt (Modulgrenzen §4.1), verhaltensneutral über den Task W2-0**. **Rev. 0.7: W2 hat 10 Tasks** — zusätzlich **W2-9** (E-8, Ledger-Writer, Phase 0) und **W2-8** (E-6, Volltests entkoppeln, vor W2-7); **fünftes** Modul `docs_freshness_v5.py` (E-7, §4.1); V4 prüft nur noch den **README-Index-Scope** (E-5, IC-05) | AC-07…AC-11, AC-13, AC-36 | W1 (V6 braucht C1) | W3 | `docs-consolidation.checks.strict: false`; zusätzlich `git rm` der **fünf** neuen Module |
| W3 | M2 | `docs/INDEX.md`-Generator + C8 Scaffold-Guard + Besitzregel; volatile-Sektion; Allowlist-Basis-Pfad; **erster echter Datei-Diff**, `docs/INDEX.md` tracked; **Rev. 0.8 (K-79): zusätzlich die agent-meta-Ausnahme** — `index-owner`-Deklaration (T-7), Gate-Zweig IC-25, 5 neue Renderer-Tests (T-2), Schema-Property `index-owner` + 2 Enum-Tests + Mengen-Pins (T-8/T-5/T-3, Reihenfolge **V-D7**) | AC-12, AC-14…AC-22, AC-26, AC-27, AC-37, AC-38, **AC-42, AC-43, AC-44, AC-45, AC-46** — **plus AC-39** über die W3-6-Halbzeile (siehe Fußnote ¹) | W1 | W2 (PG-2); **W4 ist Vorgänger, nicht Partner** (rev. 0.4, Folge aus A14) | `git rm docs/INDEX.md`; Scaffold-Skeleton regeneriert; Config-Zeile `index-owner` entfernen |
| W4 | M3 | Architektur-Konsolidierung: `git mv` Langfassung, Root-Stub, Stale-Deklaration wandert mit (M-7) | AC-28 (Teil), AC-29 | W3 | **sequenziell** (PG-3, rev. 0.4) — **nicht** parallel | `git mv` zurück + Stub wiederherstellen |
| W5 | M3 | Guides: `howto/`- und `docs/howto/`-Auflösung (M-5, M-6) + `derived-from`-Annotation (M-9, M-10) | AC-28 (Teil), AC-31 | W1 (C7 braucht C1), W4 (PG-3) | **sequenziell** (PG-3, rev. 0.4) — **nicht** parallel | `git mv` zurück; Annotationen additiv revertierbar |
| W6 | M3 | Spec/Plan-Legacy: `git mv` + `legacy:` additiv erweitern | AC-28 (Teil), AC-32 | W3, W5 (PG-3) | **sequenziell** (PG-3, rev. 0.4) — **nicht** parallel | Config-Key additiv → Zeile entfernen |
| W7 | M4 | `index.md`-Generator (C6), `log.md`-Append, `schema.md`-Update, `knowledge-indexer`-Umschreibung, **Restore-Pfad** (IC-24) | AC-33…AC-35, AC-41 | W5, W3, Rollenpflege-Branch | — (kein Parallel) | `index-mode: llm` → Generator stumm; `restore_wiki_index()` |
| W8 | M1+M3 | `check_stale_backups` (V9), README-Totverweise (M-8), `llms.txt`-/`README.md`-Providerzahl (AC-40), `PROJECT_STRUCTURE`-Korrektur (M-12), ID-Deklaration (OQ4); **Rev. 0.8 (K-79): der Doku-Anteil der `index-owner`-Deklaration, falls E-13 die Zuordnung so entscheidet — E-13 ist OFFEN; W8-4 trägt ihn nur dann. Code-, Schema- und Testanteil liegen in jedem Fall in W3-6 (V-D7)** | AC-30, AC-40 | W2, W3 | — | additiv |

> **¹ Zählkonvention der W3-Zeile (RVW9-8, info) — in §9.2 sichtbar gemacht.** §9.2 zählt
> **Halbwellen nicht**: W3-6 ist ein **Task innerhalb** der Welle W3, **keine** eigene Welle.
> **AC-39** ist deshalb in der W3-Zeile **mit** AC-42…AC-46 zu lesen, obwohl AC-39 in §9.1 (`:2549`)
> die Wellenangabe „W1, **W3-6**" trägt — diese Angabe bedeutet **zusätzliche Task-Welle**, nicht
> zusätzliches AC. **W1 bleibt 10**, **W3 bleibt 19**; AC-39 wird **nicht** doppelt gezählt
> (eine AC, **eine** Zuordnung in **einer** Wellen-AC-Spalte — Zählsatz unten).

**Jede Welle W1–W8 ist durch mindestens ein AC abgedeckt** (W1: **10**, W2: **7**, W3: **19**,
W4: 2, W5: 2, W6: 2, W7: 4, W8: 2; AC-28 zählt in W4/W5/W6 dreifach). Die Summen sind in Rev. 0.3
**neu gezählt** (NEW-5): Rev. 0.2 nannte W1: 9 und W3: 13 — W1 war AC-39, W3 war AC-38
(eigene AC-Spalte) nicht mitgezählt. **Nachzählung:** W1 = AC-01…AC-06 (6) + AC-23…AC-25 (3) +
AC-39 (1) = 10; W3 = AC-12 (1) + AC-14…AC-22 (9) + AC-26 (1) + AC-27 (1) + AC-37 (1) +
AC-38 (1) = 14. **W0** ist Definitions-Welle ohne AC. **Nachzählung Rev. 0.8 (K-79, RVW8-3):**
W3 = 14 + **AC-42, AC-43, AC-44, AC-45, AC-46** (5) = **19**; W1 bleibt **10** (AC-39 wandert
zur Welle **W3-6** hinzu, zählt aber **nicht** doppelt — es ist **eine** AC in **einer** AC-Spalte,
die W3-6-Angabe in §9.1 bedeutet zusätzliche Welle, nicht zusätzliches AC, **vgl. Fußnote ¹** unter
der Tabelle); W8 bleibt **2**, weil
der Doku-Anteil der Ausnahme **kein** eigenes AC ist, sondern denselben AC-46 trägt. **Summe
AC:** 46 (Rev. 0.7: 41). **M3-Änderungen:** Rev. 0.1Migrationen sind zu M-1…M-13 **neu** nummeriert
(alphabetische Reihenfolge, keine ID-Recycling); die Zuordnung AC → M-Nummer wurde
entsprechend nachgezogen.

**Ownership-disjunkte Parallelität:** W2 ‖ W3 sind gleichzeitig ausführbar (Dateien:
`scripts/lib/consistency/docs.py` / `docs/INDEX.md` + `scripts/lib/doc_*.py`). **W4/W5/W6 sind
rev. 0.4 als `sequenziell` ausgewiesen** (PG-3, ein Agent, W4 → W5 → W6) — Grund: alle vier
AC **AC-28, AC-29, AC-31, AC-32** verweisen per `::` auf denselben Testdatei-Anker
`tests/test_docs_consolidation_migration.py`; `check_plan_file_overlap` würde den Parallelstart
als Fehler melden, und jede `git mv`-Welle erzeugt R+A-Diffs auf denselben Stammpfaden
(Plan Rev. 0.4, Wellenübersicht/PG-3 und „Warum W2 ‖ W3 parallel ist, W4/W5/W6 aber nicht").
**Diese Angabe ist eine registrierte, offene Abweichung** — sie ist **nicht** in der Design-Quelle
begründet (das Design führt W4/W5/W6 als paarweise parallel, `docs/specs/2026-09-25-repository-documentation-consolidation-design.md:269-271`, zusätzlich `:275` — „W2 ‖ W3 ‖ W5 sind gleichzeitig ausführbar"),
sondern im Plan; Details, Status und Owner: **§13 A14** und **§17.8**. **Konflikt:** W1/W2
berühren `scripts/lib/config.py` bzw. `scripts/lib/consistency/*` — dieselben Dateien, an denen
Track A arbeitet. W1/W2 daher **sequenziell nach Track A**, ein Commit pro Datei, Rebase vor
jedem Merge. Zusätzlich **Fixture-Kollision**: die V1-Fixture `tests/fixtures/docs_v1_fixtures.md`
wird erst **nach** dem Track-A-Merge angelegt (§2.3, R15).

**PR-/Branch-Strategie** (R16, rev. 0.2; **rev. 0.4 — Ausführungskorrektur 2026-09-26, OP-1**): 8
Wellen auf **einem** Branch erzeugen einen ~65-Dateien-PR, der jeden konkurrierenden Doku-PR in
Konfliktdiffs taucht. Ein `git mv`-Welle-Merge macht jeden nachfolgenden Doku-PR konfligiert. Der
**Risiko-Inhalt bleibt unverändert**; verbindlich ist nach Rev. 0.4 die **Reihenfolge- und
Merge-Regel**, nicht die **Branch-Anzahl** — mit derselben Verbindlichkeitstiefe wie die
aufgehobene Fassung, aber mit dem ausgeführten Sachverhalt:

1. **Ein Wellen-Branch, ein PR.** Verbindlich: **ein** Feature-Branch
   `feat/repository-documentation-consolidation-main` (Basis `origin/main`) mit **einem** PR gegen
   `main`. **Kein** `chore/docs-consolidation-w<N>` wird angelegt; die Rev.-0.1- bis
   Rev.-0.3-Vorgabe „ein Branch **pro Welle**, gestapelte PRs in Reihenfolge W1→W8" ist
   **aufgehoben** (Rev. 0.4, §17.6).
2. **Wellen-Zuordnung über die Commits.** Verbindlich: Wellenkennung im Commit-Titel
   `docs(docs-consolidation): W<N> <Zweck>` und ein **Abschluss-Commit** je grüner Welle
   `docs(docs-consolidation): W<N> complete`. Der `W<N>`-**Präfix ist verbindlich** für (a) den
   Wellen-Abschluss-Commit und (b) jeden Commit-Titel, der **Wellen koordiniert** (Wellen-Übergang,
   Reihenfolge-/Merge-Entscheidung, Wellen-Sammelstand). Für **einzelne Datei-Commits innerhalb**
   einer Welle („ein Commit pro Datei", R3) ist der Präfix **optional**; der Titel folgt dann
   `docs(docs-consolidation): <Zweck>` und der **Commit-Body führt zwingend die Task-ID**
   (`Task: W<N>-<k>`). Die Wellenzuordnung ist damit dreifach garantiert: Abschluss-Commit,
   koordinierende Titel, Task-ID im Body.
3. **Merge-Regel.** Die `git mv`-Wellen (**W4/W5/W6**) werden **zuerst** gemergt, weil sie die
   Pfade verschieben und damit jeden folgenden Doku-PR sonst brechen. Die Wellen laufen als
   **sequenzielle** Commits in der Reihenfolge W1→W8; Rebase des Wellen-Branch gegen
   `origin/main` **vor** dem PR-Merge. Damit bleibt der **R16-Intent** — kein Konflikt-Diff in
   konkurrierende Doku-PRs — abgedeckt, ohne die ausgeführte Ein-Branch-Strategie aufzugeben.
4. **Dokumentierter Bestand.** Der überholte Vor-Branch `feat/repository-documentation-consolidation`
   (gemeinsames Präfix, divergente Doppelkopie der Spec-/Plan-Commits, **nicht** in `main`
   gelandet) bleibt auf ausdrückliche Nutzer-Vorgabe („nicht löschen") **erhalten**. Ein
   Post-Merge-Cleanup ist eine **eigene Entscheidung** und **nicht** Teil dieses Vorhabens; diese
   Spec schreibt weder Löschung noch Aufbewahrung eines Branches vor.
5. **Ausführungsnachweis und Belegkette.** `docs/plans/2026-09-25-repository-documentation-consolidation.md`
   (Rev. 0.4, Global Constraints, Task **W0-2**, K1/K8/K9) und
   `docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md` §7.1 (Spec-Abweichung OP-1) und §7.2
   (Commit-Bestand). **Design-Abweichung (rev. 0.4, A13):** das Design nennt in seiner W0-Zeile
   zwar nur *einen* Branch, aber mit ** anderem Namen** — `chore/docs-consolidation`
   (`docs/specs/2026-09-25-repository-documentation-consolidation-design.md:265`); gestapelte PRs
   kommen im Design nicht vor. Der Branch-**Name** ist damit eine bewusste Abweichung (§13 A13).
   §13 umfasst damit **14** Abweichungen (A1…A14).

**Reihenfolge-Begründung:** W1 zuerst (additiv, kein Diff, größte Erkenntnis). W3 vor W4/W6,
weil beide `git mv` sind und ein existierender kanonischer Index die neuen Pfade sofort
sichtbar macht. W7 zuletzt und isoliert, weil es die einzige Welle mit echtem Policy-Bruch,
Datenverlust-Potenzial und `agents/`-Berührung ist.

---

## 10. Nicht-funktionale Akzeptanz (Pipeline-Gate)

- `python3 scripts/sync.py --validate` (= `TEST_COMMAND`, `.meta-config/project.yaml:193`)
  darf bei **V1, V2, V3, V6** nicht grün sein (ab W3; in W2 V1 noch WARNING). **Korrekturrunde 5
  (K67 / RVW-7-09):** die Aufzählung ist um **V4** zu ergänzen — V4 ist **bereits registriert**
  (`scripts/consistency-check.py:53`/`:201`) und hält nach E-5 **1** ERROR (Kategorie
  `docs/se-cascade/`, Follow-up `F-DOCS-README-INDEX-SE-2026-09-27`, Termin 2026-10-11); die
  Aufzählung war damit **unvollständig**, nicht falsch. **Neu (M7):**
  V6 meldet zusätzlich `kind=expected-mismatch` aus IC-23 — der Test wird bei einer
  unbeabsichtigten Zähländerung rot, auch wenn der Render-Output korrekt ist.
  **Mechanik, RVW2-2 (in der dritten Korrekturrunde ergänzt, belegt):** `_handle_validate` ruft
  `_run_consistency_checks(agent_meta_root)` (`scripts/lib/cli_commands.py:975`); diese führt den
  **gesamten** Runner aus und gibt die **Anzahl der ERROR-Findings** zurück
  (`:171-174`, `sum(1 for f in findings if f.severity == Severity.ERROR)`); der Exit folgt aus
  `sys.exit(1 if (consistency_errors or _strict_exit_code) else 0)` (`:1056`) bzw. `sys.exit(1)`
  (`:1058-1059`). **Folge:** `--validate → 0` verlangt **null ERROR-Findings im ganzen Repo**.
  **Terminierung (Plan-Regel `W-VALIDATE-ROT`, RVW2-2):** planmäßig rot von **W2-7** bis
  einschließlich **W8-2** (letzter planmäßig roter Doku-ERROR-Check ist V3); spätester Termin 0
  ist **W8-4**. **Der Sollwert wird nicht abgesenkt, sondern terminiert** — der obige Satz
  („darf nicht grün sein") bleibt **wortgleich in Kraft** und ist die Grundlage dieser Terminierung.
  **⚠ Folge aus Rev. 0.6 / U-2 (K22) — die Terminierung ist unter dem verengten AC-30-Scope
  nicht mehr haltbar, und das ist hier ausdrücklich benannt.** V3 bleibt **ERROR**
  (`docs.py`, IC-05) und meldet die **25** toten Links unter `docs/**` **weiter**; AC-30 fordert
  deren Behebung **nicht** mehr. **Folge:** `docs.internal_links` erreicht **innerhalb W0–W8
  insgesamt nie 0**, und damit ist auch `--validate → 0` innerhalb dieses Vorhabens
  **dauerhaft unerreichbar**. Die obige Zeile „spätester Termin 0 ist **W8-4**" ist daher **als
  revidiert zu lesen**: sie gilt **nur** für die **behebbaren** Doku-ERROR-Checks (V2 → W8-4
  Schritt 5) und **nicht** für V3. **Maßgeblich** ist ab Rev. 0.6 die **Deltasperre** der Plan-Regel
  (`errors` darf nicht steigen, Owner `validator`, Baseline in **W3-7**) — dieselbe Lesart, die
  bereits für den repo-globalen Altbestand und für V9 gilt. **Es wird kein Sollwert abgesenkt**;
  die Verschiebung ist **nicht** stillschweigend, sondern hier und in §17.10.2 ausgewiesen, und
  der zugehörige Termin ist mit Owner und Datum im Follow-up-Register (§17.10.3) festgeschrieben.
  **Korrekturbedarf, der hier ausdrücklich NICHT eigenmächtig entschieden wird:** die Frage, ob
  die **25** V3-Findings unter `docs/**` die Severity ERROR behalten oder auf WARNING
  herabgestuft werden, ist eine **Spec-Entscheidung über V3 selbst** und **nicht** Gegenstand von
  U-1/U-2; sie ist als **offener Punkt OQ10** in §11.1 zu führen (Owner `orchestrator`,
  Entscheidungsweg `main_chat`, Frist **vor W8-4**).
  **Abgrenzung, RVW2-13:** `--check` ist der **Drift-Lauf** (Abgleich generierter Dateien), **nicht**
  der Consistency-Runner, und bricht **nicht** wegen V1–V9. Der erste Halbsatz von §6(b), der
  `--check` und `--validate` gemeinsam nennt, ist insoweit **zu präzisieren**; das ist als
  **Entscheidungsvorlage** zurückgestellt und in dieser Revision **nicht** geändert.
  **`--dry-run`** führt die Consistency-Suite **nicht** aus und ist von ERROR-Checks unabhängig.
- `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`
  (= `TEST_COMMANDS`, `project.yaml:194`) läuft in jeder Welle grün.
  **⚠ Spannungslage, RVW2-2 (in der dritten Korrekturrunde festgestellt — hier **nicht**
  geändert, Entscheidungsvorlage E-4):** dieser Satz steht im Widerspruch zum **ersten** Punkt
  dieser Liste, der `--validate` ein Nicht-Grün-Sein bei V1/V2/V3/V6 **ausdrücklich** erlaubt, und
  zur gemessenen Mechanik (`cli_commands.py:975` → `:171-174` → `:1056`/`:1058-1059`: der Exit
  folgt der **Anzahl aller ERROR-Findings**). Beide Sätze stehen hier seit Rev. 0.1 unverändert;
  **welcher** gilt, ist eine **Normativitätsfrage** und wird **nicht** eigenmächtig entschieden.
  **Bis zur Entscheidung** wendet der Plan die Lesart an, die der §10-Aufzählungspunkt `--validate`
  selbst normativ festschreibt
  (`W-VALIDATE-ROT`: planmäßig rot bis einschließlich W8-2, spätester Termin 0 W8-4) — das ist die
  **einzige** der beiden Lesarten, die mit demselben Aufzählungspunkt **vereinbar** ist.
- `python scripts/consistency-check.py --strict` (`:21`) ist ab W3 für `scripts/lib/doc_*.py`
  und `docs/INDEX.md` verpflichtend.
  **Präzisierung Rev. 0.5 (K14) — Messform, ohne Änderung des Pflichtumfangs.** Der obige
  Satz bleibt **wortgleich in Kraft**; die Präzisierung betrifft ausschließlich, **wie** der
  Pflichtumfang nachgewiesen wird:
  1. **Datei-, nicht repo-bezogen.** Ein grünes **repo-globales** `--strict` ist **kein**
     Nachweis dieses Pflichts und **keine** zulässige Ersatzform. Umgekehrt ist ein rotes
     repo-globales `--strict` **kein** Verstoß gegen diesen Pflichts: `scripts/consistency-check.py:273-274`
     setzt Exit 1, sobald **irgendein** Finding `WARNING` trägt, und
     `scripts/lib/consistency/report.py:75` bei Errors — das repo-globale Kriterium verlangt
     also null Errors **und** null Warnings.
  2. **Nachweisform.** `scripts/consistency-check.py` besitzt **keinen** Scope-/Pfadfilter
     (`--file` schließt alle repo-weiten Checks aus, `scripts/consistency-check.py:185`; `--changed`
     filtert nur `agents/`- und `commands/`-Dateien). Der Nachweis läuft deshalb über die
     maschinenlesbare Ausgabe, die `file` und `check` **enthält**
     (`scripts/lib/consistency/report.py:78-97`):
      ```bash
      python3 scripts/consistency-check.py --json \
        | python3 -c 'import json,sys,fnmatch;d=json.load(sys.stdin);s=[f for f in d["findings"] if f["file"]=="docs/INDEX.md" or fnmatch.fnmatch(f["file"],"scripts/lib/doc_*.py")];print("scope-findings:",len(s))'
      ```
      **Erwartungswert: `scope-findings: 0`** — der **Zählwert** in der Ausgabe, **kein**
      Exit-Code. Ein Kommando der Form `A | B` gibt den Exit-Code von `B` zurück, nicht den von
      `A`; `print_json_report` liefert `1 if errors else 0`
      (`scripts/lib/consistency/report.py:99`) — ein `sys.exit(0)` im Konsumenten würde diesen
      Roh-Exit neutralisieren und ein Prüfkriterium vortäuschen, das nicht prüft. **Ein
      `sys.exit(0)` auf dem Roh-Exit eines Zähl-Kommandos ist unzulässig** (RVW-12).
      **Prüfkraft: keine — siehe Unterpunkt 6.**
   3. **Getrennter Doku-Scope.** Für die Doku-Checks V1…V9 gilt **zusätzlich** der Scope ihrer
      eigenen Scan-Mengen — für V1 sind das `README.md`, `llms.txt`, `ARCHITECTURE.md`
       (`scripts/lib/consistency/docs.py:158`). Ein grüner §10-Pflichtumfang allein belegt
       deshalb **nicht** „keine manuell gepflegten Zahlen"; dafür gilt ein **eigenes**,
       ebenso explizites Kriterium über dieselbe `--json`-Ausgabe, das der Plan als
       **check-spezifische Kriterientabelle** in **W3-7** festlegt (Unterpunkt 5). Die Vermischung
      beider Scopes zu einem repo-globalen `--strict == 0` — **und** zu einem Aggregat
      `docs-findings == 0` — ist **unzulässig**.
   4. **Altbestand getrennt ausweisen.** Warnungen aus Bestandschecks über `agents/1-generic`,
      `agents/2-platform` und `commands/*` sind **Altbestand**: sie betreffen Pfade, die keine
      Welle W1–W8 anfasst. Sie werden als **gemessene Baseline** (Zählung + Kommando, im
      Review-Protokoll festgehalten) geführt und sind **kein** Abnahmekriterium dieser Welle.
   5. **Check-spezifische Kriterien mit Termin und Owner (neu in Rev. 0.5, RVW-1; präzisiert in
      der dritten Korrekturrunde, RVW2-1/RVW2-4; Rev. 0.6: U-2/K24 nachgezogen).** Die
      Aussage „keine `docs.*`-Findings" ist als **Aggregat über alle neun Checks** **dauerhaft
      unerreichbar** und wird deshalb **nicht** als Aggregat geführt. **Stand 2026-09-27
      (Baseline-Messung; **Rev. 0.6 / K51 berichtigt**: K24 hatte 10 auf 11 gehoben — die
      Übergabemessung war eine **Fehlmessung**):** **V7** (`check_wiki_staleness`, WARNING) meldet
      **10** Wiki-Seiten mit `type: "Architecture"` **ohne** `derived-from` — **über das Frontmatter
      gemessen** (`:2` in allen 10 Dateien, sämtlich unter `knowledge/wiki/concepts/`; ein
      `type:`-Zeilen-Scan über ganze Dateien zählte zusätzlich den **Body**-Wertelisten-Kommentar
      `type: "Concept" # Concept | Architecture | …` in `core-principle-knowledge-engine.md:46`, dessen
      Seite den Typ `"Concept"` trägt) — Termin **W5-3**;
      **V3** (`check_internal_links`, ERROR) meldet **drei Klassen**: **2** `branch=="layout"`
      (`README.md:722`/`:723`, `howto/setup/`, `howto/features/` — Termin **W8-2**, Owner
      `developer`), **25** `branch=="link"` (alle unter `docs/**`, **kein** Termin 0 in W0–W8 —
      **Rev. 0.6, U-2/K22:** Follow-up `F-DOCS-LINKS-2026-09-27`, Owner `developer`, Termin
      **2026-10-11**), und `llms.txt` = **0**; **V2**
      (`check_docs_index_completeness`, ERROR) ist rot, solange `docs/INDEX.md` fehlt — Termin
      **W3-6**; **V9** (`check_stale_backups`, WARNING) meldet einen **maschinenlokalen,
      gitignorierten** Altbestand und wird ihn **nicht** abräumen (FI-10) — **kein Termin 0**.
      Maßgeblich ist deshalb je
      V-Check ein **eigener Erwartungswert mit Termin und Owner**; der Plan führt ihn als
      Kriterientabelle (Rev. 0.5, `W-GATE-TABLE`) mit vollständiger Kriterienmenge **je Welle**.
      **Zusätzlich verbindlich:**
      (a) **Präsenzregel statt Registrierungszahl (RVW2-1).** Für jeden V-Check mit
      Erwartungswert **≠ 0** muss die Zählliste eine Zeile `<check> <count> <severities>`
      enthalten; eine fehlende Zeile ist ein Befund. Die in der Fassung vor dieser Korrekturrunde
      zusätzlich geforderte **Anzahl registrierter** `docs.`-Checks (7 nach W2-7, 8 ab W6-2,
      9 ab W8-4) ist **aus der Messquelle nicht ableitbar** und wird **nicht** als Sollwert
      geführt: der Runner bietet keinen Registry-Dump, und ein registrierter, aber befundfreier
      Check erscheint in jeder Findings-Zählung **nicht**. Der Registrierungsnachweis wird
      deshalb auf Task-Ebene geführt (W2-7). Für Checks mit Erwartungswert **0** ist die
      Präsenzregel **nicht** empfindlich; deren Registrierung tragen die Unit-Tests der
      zuständigen Tasks. **Das ist als Grenze der Nachweisform benannt, nicht kaschiert.**
      (b) **Verschlechterungsregel** — der Zählwert eines planmäßig roten Checks darf **nicht**
      steigen; **Ausnahme V9**: ein Anstieg durch **eigene** neue Backups des Vorhabens ist
      erlaubt, weil der Bestand maschinenlokal ist und per FI-10 nicht abgeräumt wird.
      **Für V9 wird keine Zahl als Sollwert geführt (RVW2-4):** die in der Fassung vor dieser
      Korrekturrunde genannten „**179** Altlasten" (IC-05, V9-Zeile) sind eine **Bestandsangabe**
      aus dem System-Design und im Working Tree **nicht messbar** — die Dateien liegen unter
      `.claude/agents/` und sind gitignoriert (`.gitignore:13`, `.gitignore:22`). **Regel:** W8-4
       nimmt **vor** der Implementierung eine Bestandsaufnahme als `BACKUP-BASELINE` auf; die
       **Obergrenze** wird erst **danach** festgeschrieben — als Artefakt des
       **W8-4-Review-Protokolls** (`V9-OBERGRENZE`), **nicht** als Sollwert in dieser Spec: eine
       ausführende Task trägt hier keinen neuen Sollwert ein (RVW3-6). Eine
      **Altersschwelle N** ist **kein** Config-Key — IC-22 fixiert sechs Keys, und der
      Schema-Block `docs-consolidation` ist geschlossen
      (`config/project-config.schema.json:2421-2470`, `additionalProperties: false`); N ist eine
      **Modulkonstante** in `scripts/lib/consistency/docs.py`, Wert in W8-4 festgelegt.
      **Diese Regel verlagert die DoD-Aussage „null `docs.*`-Findings" von der
      DoD- auf die Wellenebene**, weil nur dort je Check ein erfüllbarer Sollwert mit Termin
      existiert. **Über die inhaltliche DoD-Aussage selbst siehe §17.9.4 Punkt (vii)** — sie ist
      in der dritten Korrekturrunde formal neu gefasst worden und ist dort als
      **Entscheidungsvorlage an den Nutzer** gekennzeichnet; die Fassung davor („alle neun
      V-Checks = null `docs.*`-Findings") ist **aufgehoben**, weil sie mit V9 unvereinbar war.
   6. **Was §10 ausdrücklich *nicht* prüft (RVW-14/RVW-15, Info — Dokuzeile, kein
      Prüfkriterium).** (a) Der §10-Dateiscope `scripts/lib/doc_*.py` + `docs/INDEX.md` ist
      **0 per Konstruktion**: V1 scannt `README.md`, `llms.txt`, `ARCHITECTURE.md`
      (`docs.py:158`), V2 liest `docs/INDEX.md` als **Soll**, V4 liest `README.md` als Soll, V6
      vergleicht die generierten Blöcke — **kein** Check meldet **auf** die beiden Scope-Pfade.
      Der Erwartungswert `scope-findings: 0` dokumentiert den Pflichtumfang, **beweist aber
      nichts**; die eigentliche Doku-Aussage trägt Punkt 5. (b) Die Teilmengen-Aussage
      `v1-files ⊆ V1_SCAN_RELPATHS` ist ebenfalls **konstruktionsbedingt** wahr, weil
      `docs.py:158` die einzige Quelle der Scan-Menge ist; beweiskräftig für die **Abdeckung**
      von F2/F3-Site-2/F4 ist allein der Sichtbarkeitsnachweis (§5.1.1, Präzisierung Rev. 0.5).

- **Szenarien 50, 51, 52, 54, 55, 56** (`registry.md:97-103`) bleiben nach **jeder** Welle grün —
  sie sind der härteste Regressionstest für B2/IC-15 und für die Absenz-Defaults aus IC-22.
  Verbindlich als **AC-38** verankert; kein Assert-Skript und keine Fixture-Config wird
  angefasst (NG-10).
- Szenario `64-docs-facts-drift.md` (Offset-Drift: Rolle hinzugefügt, Index nicht regeneriert)
  muss `--check` fehlschlagen lassen — **Ownership Track A**, in W2 koordiniert, nicht parallel
  geschrieben. **Nummer 64, nicht 63**: `63` ist bereits `63-context-file-modes`
  (`registry.md:110`, `asserts/63-context-file-modes.sh`,
  `configs/63-context-file-modes.project.yaml`) — eine Kollision, die das Design (§4, Zeile
  207) nicht gesehen hat (§17.1-NF-1).
- **Workflow-Vertrag, neu (OQ8):** V2 ist ab W3 **ERROR**. Legt ein Mensch eine neue
  `docs/**/*.md` an, ist `--validate` **rot**, bis ein Sync mit `docs-consolidation.enabled:
  true` gelaufen ist. Dieser Vertrag ist in W3 im Plan als **expliziter Schritt** zu
  dokumentieren. **Auslöser ist entschieden (Nutzer, 2026-09-26, §11.2 OQ8): der
  deterministische Sync-/Validator-Lauf** — kein Commit-Hook, kein CONTRIBUTING-Hinweis.

---

## 11. Entscheidungsstand (offene Fragen + geschlossene Punkte)

### 11.1 Offen — hier **nicht** entschieden

| # | Frage | Warum nicht entscheidbar | Empfehlung | Owner | Entscheidungsweg | Blockiert |
|---|---|---|---|---|---|---|
| **OQ1** | Sollen `knowledge/wiki/topics/` (43 Guides) vollständig in `docs/guides/` aufgehen, oder bleibt das Wiki als LLM-optimierte Aufbereitung bestehen? | **Produktentscheidung.** Wiki-Seiten sind nicht 1:1 mit Guides (Duplikate *und* Unique); ein Merge verändert den Lesefluss für Knowledge-Agenten. | `docs/guides/` = SSoT; Wiki-Topics behalten nur, was es in `docs/` nicht gibt; Duplikate → Redirect. Umfang erst nach dem C4-Baum-Inventar bezifferbar. | `main_chat` (Eskalation) | Produktentscheidung im Review-Loop; danach Folge-REQ | W5 |
| **OQ3** | `AGENTS.md`-Bootstrap-Block (66 hartgelistete Agenten am Repo-Ende) mitgenerieren? | Der Block liegt in einer generierten Kontextdatei, die in **alle** Submodule-Consumer geht → B6-Risiko. | **Scope-Grenze dieser Initiative** (NG-5). Eigene REQ, da derselbe `DOCS_*`-Mechanismus, anderer Blast Radius. | `requirements` (via `main_chat`) | Eigene REQ nach Abschluss von W8 | nach W8 |
| **OQ4** | ID-System: `REQ-*` vs. `SPEC-<NAME>-<JJJJ-MM-TT>` vereinheitlichen oder als zwei Ebenen definieren? | Betrifft `docs/REQUIREMENTS.md:4` und 4 Spec-Bäume; Umbenennung ist ein Traceability-Bruch für alle offenen Issues. | **Keine Umbenennung** (NG-6). `SPEC-*` = Spec-Pipeline-Artefakt-ID, `REQ-*` = Requirements-Master-ID, mit Einweg-Verweis. Die Deklaration selbst gehört in **W8** (F16) und ist als **AC-40** verankert. | `requirements` + `validator` | Entscheidung vor W8; Ergebnis als deklarativer Abschnitt in `docs/REQUIREMENTS.md` | W8 |
| **OQ9** | Welche der beiden Beispiel-Configs ist SSoT — `docs/guides/project.yaml.example` (179 Z, ab jetzt) oder `docs/guides/configs/project.yaml.example` (340 Z, aus `howto/configs/`)? | **Inhaltsentscheidung.** NG-1 verbietet Neuschreiben; ein Merge wäre Doku-Rewrite. Die Dateien decken unterschiedlich tiefe Abschnitte ab, eine bloße Löschung würde Beispielkonfiguration entfernen. | Beide behalten, die 340-Z-Datei als **vollständige Referenz** kennzeichnen, die 179-Z-Datei als **Kurzfassung** mit Pointer darauf. Zwei Zeilen Zusatz, kein Rewrite. | `technical-writer` + `documenter` | Entscheidung **vor W5**; Ergebnis ist eine `docs/guides/INDEX.md`-Zeile plus ein Pointer in beiden Dateien | **W5** |
| **OQ10** | **NEU, Rev. 0.6 (K22) — Folge der U-2-Verengung von AC-30.** Behalten die **25** V3-Findings unter `docs/**` die Severity **ERROR** (IC-05), oder wird V3 für `docs/**` auf **WARNING** herabgestuft, während `README.md` + `llms.txt` **ERROR** bleiben? | **V3-Severity ist eine IC-05-Eigenschaft**, und IC-05 wird von **U-1/U-2 nicht berührt** — eine Herabstufung wäre daher eine **eigenständige** Spec-Änderung an einem Check-Vertrag und **keine** Konsequenz der Verengung. Solange sie offen ist, bleibt V3 dauerhaft rot und `--validate → 0` unerreichbar (§10, Aufzählungspunkt `--validate`). | **Scope-gestuft behalten:** `README.md`/`llms.txt` = **ERROR**, `docs/**` = **WARNING**, bis das Follow-up `F-DOCS-LINKS-2026-09-27` (Termin **2026-10-11**) abgearbeitet ist — die einzige Lesart, die den Check auf seinem eigenen Scope scharf hält, ohne den Altbestand als ERROR zu führen. | `orchestrator` (via `main_chat`) | Entscheidung **vor W8-4**; bei Entscheidung für die Herabstufung ist IC-05 in der nächsten Revision zu ändern | **W8-4** (nur für die Terminierung von `--validate`; **kein** Blocker für W2–W7) |

**Klarstellung zum Ergebnis-Ort von OQ9 (RVW2-8, in der dritten Korrekturrunde — **keine
Entscheidung über OQ9**):** die Formulierung „eine `docs/guides/INDEX.md`-Zeile" ist **mehrdeutig**,
weil **keine Welle W0–W8 eine Datei `docs/guides/INDEX.md` erzeugt**. Gemeint ist die **Zeile im
generierten `docs/INDEX.md`**, Abschnitt `## guides` (IC-10(d)), plus der Pointer in **beiden**
Beispiel-Configs (Plan Task **W5-1**). **Folge, falls die Entscheidung anders ausfällt:** würde sie
als eigene Datei `docs/guides/INDEX.md` geführt, entstünde ein **zweiter** neuer getrackter
`docs/**/*.md`-Pfad in W5 und V2 (`check_docs_index_completeness`, ERROR) wäre bereits ab **W5-1**
statt erst ab W5-2 rot. Das ist eine **Nachlaufregel** für den Fall der abweichenden Entscheidung,
keine Vorwegnahme.

**OQ6-Reihenfolgekorrektur (rev. 0.2, §17.1-NF-2):** Rev. 0.1 ließ OQ6 **W3** blockieren. Das
ist zu spät: die Entscheidung „tracked vs. untracked" bestimmt, **ob** `docs/INDEX.md` in
`.gitignore` landet, und `.gitignore` ist bereits in **W1** (M-11-Umfeld) bzw. W3 Welleninhalt
— eine in W3 getroffene `.gitignore`-Entscheidung erzeugt einen zusätzlichen Commit am
falschen Ort. Korrekt: Blockade **W0/W1**, Umsetzung in W3. **Erfüllt:** die Entscheidung
liegt seit 2026-09-26 vor (§11.2, OQ6).

**Nachtrag 2026-09-26 (Statuswechsel, kein Inhaltswechsel):** **OQ2**, **OQ6** und **OQ8** sind
durch **Nutzer-Entscheidung** vom 2026-09-26 **geschlossen** und stehen jetzt in §11.2. Die
verbleibenden offenen Fragen dieser Spec sind damit **OQ1, OQ3, OQ4, OQ9** — jede mit
Owner, Empfehlung, Entscheidungsweg und Wellen-Blockade. **Rev. 0.6:** die offene Menge dieser Spec
ist damit **OQ1, OQ3, OQ4, OQ9, OQ10** (OQ10 neu, K22 — V3-Severity für `docs/**` nach der
U-2-Verengung; §11.1-Tabelle unten). §16 (Selbstreview Rev. 0.3) und die
Wellenübersicht §9.2 nennen OQ2/OQ6/OQ8 noch als offen; das ist der **historische Rev.-0.3-Stand**
und bleibt als solcher stehen — maßgeblich für den aktuellen Status ist §11. **Ausnahme nur für
den Rev.-0.3-Stand:** §15 (Trace-Anker) ist dagegen ein **Ist-Zustands-Anker** und führt den
aktuellen Stand (§11.1 offen / §11.2 geschlossen).
**Rev. 0.8 (2026-09-29):** die **OQ-Menge dieser Spec ist unverändert** — OQ1, OQ3, OQ4, OQ9,
OQ10 bleiben **offen**, OQ2/OQ5/OQ6/OQ7/OQ8 bleiben **geschlossen**; Rev. 0.8 stellt **keine**
OQ auf und löst **keine** auf. Neu sind **fünf Entscheidungsvorlagen E-9…E-13** (vom Typ
Entscheidungsvorlage wie E-5…E-8, **nicht** vom Typ offene Frage wie OQ\*) mit Optionen,
Empfehlung und Wellen-Auswirkung in **§17.12.2**; sie sind **offen**, und **keine** davon wird
unterstellt. **Ausdrücklich ungelöst:** **OQ1** (Wiki-Topics ↔ `docs/guides/`, Owner
`main_chat`, `docs/plans/2026-09-25-docs-consolidation-oq1.md:94`, Blockade **W5** `:99`) — die
agent-meta-Ausnahme berührt `knowledge/wiki/**` **nicht** und hebt diese Blockade **nicht** auf.

### 11.2 Geschlossen — **nicht** mehr als offene Frage führen (N3)

| # | Ursprüngliche Frage | Status | Begründung |
|---|---|---|---|
| **OQ2** | `llms.txt` — **generiert** oder **handgepflegt**? | **GESCHLOSSEN 2026-09-26 — Hybrid: `llms.txt` bleibt handgepflegt, generiert werden ausschließlich `{{DOCS_PROVIDERS_BLOCK}}` und `{{DOCS_REPO_FACTS_BLOCK}}`.** | **Entschieden vom Nutzer** am 2026-09-26, über `main_chat` an den `orchestrator`. **Entspricht der Empfehlung dieser Spec** (Hybrid wie T-2 A) — die Entscheidung **bestätigt** sie, weicht also nicht ab. Handtext-Einleitung und Linkliste (`llms.txt:3-12`, `:17-19`, `:24`) bleiben **handgepflegt**; ein **Vollgenerieren** der Datei ist ausdrücklich **nicht** entschieden. **Folge für `docs-consolidation.sources` (IC-22):** `llms.txt` ist ein Wert der Liste der Hybrid-Dateien — Default bleibt `[README.md, llms.txt, ARCHITECTURE.md]` (IC-22-Tabelle, `volatile-facts`-Regel IC-02 unberührt); die Liste steuert nur, **welche** Dateien zwei Marker-Regionen erhalten, nicht wie viel Prose generiert wird. Genau diese beiden Blöcke sind es, die W3-7 (Plan) in `llms.txt:5` einführt. **Kein neues CLI-Flag** (NG-4), keine neue Doku-Datei, kein Eingriff in den Prosa-Ton. **IC/AC unberührt** (AC-25, AC-40) — betroffen ist ein Modus-Vertrag, kein Code-Vertrag. **W1-Blockade (§11.1) ist damit aufgehoben.** |
| **OQ6** | Soll `docs/INDEX.md` **tracked** sein (git) oder generiert-untracked wie `.claude/`? | **GESCHLOSSEN 2026-09-26 — `docs/INDEX.md` ist versioniert (tracked).** | **Entschieden vom Nutzer** am 2026-09-26, über `main_chat` an den `orchestrator`. Deckt sich mit der Empfehlung dieser Spec (tracked, weil `project.yaml:70` die Datei ohnehin als Fallback-Skeleton *im Repo* schreibt) und mit §3.1 („100 % generiert" unter `docs/`) sowie mit dem Plan (Create `docs/INDEX.md`, W3-6). **Folge:** `docs/INDEX.md` wird **nicht** in `.gitignore` aufgenommen; die `.gitignore`-Entscheidung ist damit gegenstandslos und der Wellenpunkt aus §9.2 (W0) entfällt ersatzlos. Der Vertrag aus `scripts/lib/spec_plan_scaffold.py:23` + `project.yaml:70` bleibt unverändert. **Blockade W0/W1 (§11.1-Hinweis) ist damit aufgehoben.** |
| **OQ8** | **Wer re-generiert `docs/INDEX.md`, wenn ein Mensch eine neue `.md` unter `docs/` anlegt?** V2 ist ab W3 **ERROR** — jede neue Doku-Datei blockiert `--validate` (= `TEST_COMMAND`) bis ein Sync gelaufen ist. | **GESCHLOSSEN 2026-09-26 — Regenerierung läuft deterministisch über Sync/Validator.** | **Entschieden vom Nutzer** am 2026-09-26, über `main_chat` an den `orchestrator`: kein Commit-Hook, sondern der bestehende, ohnehin verpflichtende Sync-/Validator-Lauf (`sync.py` im Default-Sync, `--validate` als `TEST_COMMAND`, `project.yaml:193`). **Kein neuer Hook, kein neuer Vertrag, keine neue Doku-Datei** (`docs/guides/project.yaml.example` bleibt unverändert). **Abweichung von der Empfehlung dieser Spec** (die einen `pre-commit`-Hook vorsah) — die Entscheidung des Nutzers geht vor; die IC/AC bleiben unberührt, da kein Code-, sondern ein Workflow-Vertrag betroffen ist. **V2 bleibt ERROR**, die Vertragsverletzung wird also weiter sichtbar; `W3` bleibt davon abhängig, dass der Sync-Pfad den Index tatsächlich schreibt (C2/C8). |
| **OQ5** | Müssen `DOCS_*`-Platzhalter in **bereits-released** agent-meta-Versionen funktionieren (Submodul-Pinning auf ältere Tags)? | **GESCHLOSSEN: kein Backport.** | IC-11 legt fest, dass Doku-Platzhalter **ausschließlich** von E3 (`doc_renderer`, IC-07) substituiert werden, **nie** von E1/E2 (`variables.py:56`, `builder.py:13`) — den Engines, die in Fremdprojekte deployen. Ein älterer Tag, der keinen `doc_renderer` enthält, kennt die Platzhalter nicht und löst sie nicht auf; ein **neuer** Tag in einem alten Consumer-Projekt löst sie auf, ohne dass der alte Tag etwas zurückportieren muss. NG-11 verankert das als Nicht-Ziel. Widerlegung wäre ein Trigger für eine **neue** REQ, keine offene Frage dieser Spec. |
| **OQ7** | Eine Spec-Datei (aktuell) oder vier Wellen-Specs (Design §11)? | **GESCHLOSSEN: eine Datei, vier Module.** | Repo-Konvention: eine `spec-id` pro Datei (`docs/specs/2026-09-15-reference-standards-design.md:1-8`). Die Aufteilung ist eine **Planungsentscheidung des Planners** (§4), keine Spec-Frage — sie wird im Plan entschieden, nicht in dieser Spec. Rev. 0.1 führte sie unnötig als OQ. |

---

## 12. Risiken (R1…R20) und Threat Model

### 12.1 Design-Risiken R1…R11 (mit Korrekturen aus Rev. 0.2)

| # | Risiko | W. | Mitigation (in dieser Spec verankert) | Owner |
|---|---|---|---|---|
| **R1** | **Doku-Diff-Churn**: jede Rollen-/Hook-Änderung erzeugt einen README-Diff; bei volatilen Zahlen Flattern. **Erweitert (M7):** der Flattern-Pfad ist nicht auf Hybrid-Dateien begrenzt — `DOCS_SCENARIO_COUNT` wird weiterhin in `docs/INDEX.md` gerendert (§3.2), Track A fügt laufend Szenarien hinzu ⇒ Diff in `docs/INDEX.md` **plus** `facts-hash`-Wechsel bei jedem Szenario. | hoch | Footer enthält **nur Fact-Hash, keinen Zeitstempel** (IC-14, NFA-02; Muster `standalone.py:365`). Volatile Fakten werden (a) in Hybrid-Dateien **unterdrückt** (IC-02, `docs-consolidation.volatile-facts`, AC-03), (b) in `docs/INDEX.md` in eine **`docs-volatile`-Sektion am Dateiende vor dem Footer** gerendert — Diff = genau **eine** Zeile, und (c) **nicht** in den `facts-hash` einbezogen, damit der Hash nicht flackert. Verbleibender Restdiff ist eine Zeile pro Szenario und damit im Review sichtbar begründet. | `developer` |
| **R2** | **LLM-Handpflege-Kollision im Wiki**: Knowledge-Agenten schreiben `index.md`, Generator überschreibt → Datenverlust (B5) | hoch | Erstsicherung vor dem ersten Rewrite (AC-35); **spezifizierter** Restore-Pfad (IC-24, AC-41 — Rev. 0.1 behauptete einen ohne Pfad); `index-mode: llm`-Rollback (IC-22); Diff-Review vor Aktivierung; W7 **isoliert und letzte Welle**; ReqogniLoom-Workspace-Export als Zwischenkopie | `knowledge-curator` + `orchestrator` |
| **R3** | **Track-A-Konflikt**: parallele Änderungen in `scripts/lib/`, `config/` **und `tests/fixtures/`** | hoch | W1/W2 sequenziell nach Track A; ein Commit pro Datei; Rebase vor jedem Merge; vor W1 `git log --oneline -20 -- scripts/lib/` prüfen (§2.3). **Ergänzt:** die V1-Fixture `tests/fixtures/docs_v1_fixtures.md` wird erst **nach** dem Track-A-Merge angelegt | `orchestrator` |
| **R4** | **V1-Fehlalarme.** *Neu begründet:* Rev. 0.1 stützte dieses Risiko auf `README.md:688` („6 DoD presets" sei korrekt). Diese Zeile ist **Drift** (F22) — das Argument trägt nicht mehr. Das Risiko bleibt **real**, aber aus einem anderen Grund: die Nomen-Whitelist in V1a ist breit (`test(s)`, `rule(s)`, `skill(s)`), und Fließtext wie „3 tests" in einem Guide würde matchen. **Abgrenzung (RVW-7, Rev. 0.5):** R4 behandelt ausschließlich die **Fehlalarm-Ursache**. Die **Hochstufungsreihenfolge** (V1 sichtbar, bevor `checks.strict: true` auf `ERROR` hochstuft) ist **kein** Bestandteil dieses Risikos und wird hier **nicht** nachgetragen — sie ist als Ausführungs-Vorbedingung in §5.1.1 und als DAG-Kante `W2-1 → W3-4` im Plan Rev. 0.5 verankert. | mittel | V1a/V1b prüfen Marker-**Abwesenheit**, nicht die Zahl; `agent-meta:docs-exempt`-Marker (IC-05, §5.1.1); die beiden einzigen **heute** korrekten Handzahlen (`README.md:689` Tier, `README.md:695` Commands) sind **beide** exempt-fähig; Start als **WARNING**, `checks.strict: false` per Default (IC-22); **Positiv- und Negativ-Fixture** verpflichtend (AC-07/AC-08) | `developer` |
| **R5** | Rollen-Parität (F13) | niedrig | V5 ist **gate-bewusst** (IC-04, AC-05, AC-11) und bleibt WARNING, solange `systems-engineering.enabled: false` (`project.yaml:12-13`). Ein etwaiger Fix ist ein **Config-Edit in eigener REQ** (NG-8) | `developer` |
| **R6** | **Link-Check-Fehlalarme** auf externe URLs/Anker | mittel | V3 prüft **nur relative repo-interne Pfade**; `http(s)://`, `mailto:` und `#anchor` werden nicht geprüft; Allowlist-Pattern über den bestehenden `drift-allowlist.yaml`-Mechanismus bzw. `config`-Key (IC-05) | `developer` |
| **R7** | **B2 Doppel-Writer** `docs/INDEX.md` (Generator vs. Scaffold) | hoch | C8 `is_file_index_skeleton()` (IC-15) **plus** verbindliche Stage-Reihenfolge Generator **nach** Scaffold (IC-12) **plus Besitzregel** (IC-13: der Generator überschreibt nur Skeletons und Neuanlagen); `index-mode: skeleton` als zweiter Hebel; Szenarien 50/51/52/54/55/56 als harte Regression (AC-20, AC-21, AC-22, **AC-38**). **Rev. 0.8, P-5 — dritter Hebel:** `docs-consolidation.index-owner` (IC-25). Er verengt den **KE**-Vorrang-Zweig und ist damit **kein** weiterer Writer, sondern eine **Wegbedingung**: in agent-meta schreibt der Scaffold im KE-Modus **nichts** (`spec_plan_scaffold.py:116` bleibt `False`), es gibt dort also **nur einen** Writer und **einen** Erstschreibvorgang (`CREATE`, `doc_renderer.py:829-830`) — der zweite Lauf meldet `unchanged` (`:845-848`). **Das Risiko selbst sinkt in agent-meta**; unverändert bleibt es für **jedes** Projekt, das `index-owner` **nicht** setzt. **Gepinnt** in AC-42 (einmalig), AC-44 (Override hebt `skeleton` und Besitzregel **nicht** auf), AC-45 (`dry_run`), **AC-38** (Szenarien 50–56, `tests/scenarios/configs/*.project.yaml` enthalten **keinen** `docs-consolidation`-Key ⇒ per Konstruktion unerreichbar, IC-26/6). **Zur Freigabe ausstehend.** | `developer` |
| **R8** | **B1 Downstream-Bruch** durch `docs/superpowers`-Verschiebung | mittel | `legacy:`-Liste additiv erweitert (IC-17 M-13), alte Einträge **ein Release** mit Deprecation-WARNING toleriert (AC-32); Release-Notes-Pflicht, Minor-Bump | `release` |
| **R9** | **Scope-Creep**: ~190 `docs/*.md` (**HYPOTHESIS**, exakte Zahl erst über `DOCS_DOCS_FILE_COUNT` belegbar) + 100+ Wiki-Seiten → Migration wird zum Doku-Rewrite | mittel | Wellen sind additiv / `git mv`-only; **keine inhaltliche Neuschreibung** (NG-1); Inhaltsarbeit ist eigene REQ (u. a. OQ9); NFA-08 begrenzt den Blast Radius | `orchestrator` |
| **R10** | `AGENTS.md`-Bootstrap-Block driftet ebenfalls | niedrig | **Bewusst außerhalb des Scopes** (NG-5), als **OQ3** geführt, nicht in den Wellen | `requirements` |
| **R11** | `docs/CODEBASE_OVERVIEW.md` (2245 Z) liegt außerhalb des SSoT-Baums und gehört `documenter` | mittel | **NG-3**: im SSoT-Baum als eigenständiger Entry geführt, **Content-Ownership unangetastet**; Generierung ausschließlich für den Fakten-Footer. Beleg: `knowledge/wiki/log.md:30` („HARD CONSTRAINT — gehört documenter-Agent"); toter Verweis darin (`docs/CODEBASE_OVERVIEW.md:33-44`, `se-orchestrator.md`) wird als **eigenes Folge-Issue** geführt, nicht in dieser Spec korrigiert | `documenter` |

### 12.2 In dieser Spec neu identifizierte Risiken R12…R20

| # | Risiko | W. | Mitigation | Owner |
|---|---|---|---|---|
| **R12** | Der `DOCS_`-Prefix kollidiert semantisch mit den **bereits existierenden** Built-ins `DOCS_LANGUAGE` / `INTERNAL_DOCS_LANGUAGE` (`project.yaml:183-184`) und den `placeholders.py`-Typo-Mappings (`:135-136`) | mittel | IC-02 verbietet explizit die Belegung dieser zwei Namen; `DOCS_`-Namensraum ist auf **Fakten** (`_COUNT`, `_VERSION`, `_BLOCK`) beschränkt; Prefix-Regex `:177` + `_KNOWN_TYPOS` bleiben unangetastet | `developer` |
| **R13** | `PROJECT_STRUCTURE`-Korrektur (M-12) verändert `AGENTS.md`/`CLAUDE.md` in **jedem** Consumer (B6) | niedrig | Additiver Config-Edit; managed-block-Mechanismus (`context.py:36-38`) fängt Handpflege ab; Drift-Detection meldet; als expliziter Review-Punkt in W8 (IC-17) | `developer` + `release` |
| **R14** | **Falsche-Fakt-Kette (Korrektheitsrisiko, nicht Churn).** `doc_facts → Renderer → V6` ist ein **geschlossener Kreis**: V6 vergleicht den Render-Output gegen `compute_doc_facts()`, also gegen dieselbe Formel, die ihn erzeugt hat. Ein **systematisch** falscher Faktor passiert **alle** Gates dieser Initiative. Real belegt: Rev. 0.1 enthielt **drei** solche Zählfehler (F19 4 statt 5, F22 6 statt 7, F14 6/7 statt 7/8) — keiner wäre von V1–V9 gefunden worden. | **hoch** | **IC-23 + AC-36:** unabhängig handgepflegte Sollwert-Datei `config/doc-facts-expected.yaml` (**elf** Werte, rev. 0.3 — die Yaml-Datei hat genau 11 Einträge; Rev. 0.2 nannte an dieser Stelle fälschlich „12"), geprüft von `load_expected_doc_facts()` / `compare_expected_doc_facts()`; V6 meldet `kind=expected-mismatch` als ERROR. **Restrisiko (bewusst akzeptiert):** jede gewollte Zahlenänderung macht den Test rot, bis die Datei im selben Commit mitgezogen wird — das ist der gewollte Review-Signalweg, kein Defekt | `developer` + `validator` |
| **R15** | **Kollision geht über Track A hinaus.** R3 nennt nur `scripts/lib/` und `config/`. Real betroffen sind (a) **sechs** Szenario-Asserts (50/51/52/54/55/56) und (b) `config/project-config.schema.json`, das in Rev. 0.1 **nirgends** als Operation auftauchte. **Korrektur der Einordnung:** das Wurzel-Schema ist `additionalProperties: true` (`:2425`) — die 6 neuen Keys brechen die Validierung **nicht**; fehlend wären Autocomplete und der Tippfehler-Wächter, den das Repo selbst ausdrücklich nutzt (`:2058`, `:2073`). | mittel | (a) Absenz-Defaults fail-off + Besitzregel + `knowledge-engine`-Schreibverbot ⇒ alle sechs Szenarien bleiben unverändert grün (AC-38, NG-10). (b) **M-11** nimmt den Schema-Block als Operation in **W1** auf (IC-17, AC-39). (c) V1-Fixture erst nach Track-A-Merge (§2.3) | `developer` |
| **R16** | **PR-/Branch-Kollision.** 8 Wellen, ~65 Dateien, ein Branch ⇒ ein Groß-PR, der jeden konkurrierenden Doku-PR in Konflikt-Diffs taucht. Ein `git mv`-Welle-Merge macht jeden nachfolgenden Doku-PR konfligiert. **Risiko-Inhalt unverändert.** | mittel | **Rev. 0.4 (Ausführungskorrektur 2026-09-26, OP-1):** die Branch-Anzahl ist **nicht** der Lösungsansatz — abgedeckt wird der R16-Intent über **Reihenfolge- und Merge-Regel**: (1) **ein** Wellen-Branch `feat/repository-documentation-consolidation-main` mit **einem** PR gegen `main`, kein `chore/docs-consolidation-w<N>`; (2) Wellen **sequenziell** W1→W8, Wellenzuordnung über Wellenkennung im Commit-Titel `docs(docs-consolidation): W<N> …` + Abschluss-Commit `… W<N> complete`; (3) `git mv`-Wellen (W4/W5/W6) **zuerst** mergen; (4) ein Commit pro Datei, Task-ID im Commit-Body; (5) Rebase gegen `origin/main` vor dem PR-Merge. Die aufgehobene Forderung „Branch pro Welle, gestapelte PRs" (Rev. 0.1–0.3) und die Begründung der Korrektur stehen in §9.2 (Absatz „PR-/Branch-Strategie") und §17.6 | `orchestrator` + `git` |
| **R17** | **Downstream-Asymmetrie `docs/INDEX.md`.** In Consumer-Projekten bleibt das Scaffold-Skeleton, die V-Checks sind per Default aus. Wäre das nicht so, wäre V2 dort **dauerhaft** rot — eine Asymmetrie, die als „grüner Zustand" erscheint, obwohl nie geprüft wurde. | mittel | **Bewusste, dokumentierte Asymmetrie:** alle neun Checks sind an `docs-consolidation.enabled` gebunden (IC-05-Common-Gate), in Consumer also vollständig inaktiv. Das ist Absicht (NFA-04) und **sichtbar**: V1 meldet nichts, wo gar nicht geprüft wird. Wer Consumer absichtlich prüfen will, setzt den Key explizit. Ein „agent-meta-Eigenerkennung\"-Heuristik-Gate wird **nicht** gebaut (es würde in Fremd-Repos Doku-Claims aufstellen, die niemand gepflegt hat) | `developer` |
| **R18** | **Auto-Commit-Interaktion.** *Analysiert und nicht zutreffend (Rev. 0.2):* die Befürchtung, generierte Doku-Dateien könnten in den Auto-Commit-Pfad geraten, ist **unbegründet**. `_sync_stage_auto_commit_allowlist` (`sync_pipeline.py:1102-1117`) liest `config` + `active_roles` über `resolve_auto_commit_config(config, active_roles, agent_meta_root)` und schreibt `.meta-config/auto-commit-allowlist.json` als **generierte** Ausgabe; der Drift-Store `.meta-config/generated-file-hashes.json` wird dort **nicht** gelesen. Auch der vom Reviewer genannte Pfad `.meta-config/auto-commit-allowlist.json` **existiert im Repo nicht** (Glob: keine Treffer) — es ist ein Sync-Output. | — | keine Mitigation nötig; die Analyse ist in IC-16 (M8-Tabelle) als Beleg verankert, damit die Frage nicht erneut aufgerollt wird | `—` |
| **R19** | **`knowledge-indexer`-Kollision.** IC-21 fasst `agents/1-generic/knowledge-indexer.md` an — eine Datei in der von Track A / Rollenpflege berührten Zone. Ein Rebase der Rollenpflege landet sonst in einem Template-Diff. | niedrig | **Verbindliche Reihenfolge** in IC-21: W7 startet erst nach dem Rollenpflege-Merge; IC-21 ist der **letzte** Commit von W7. Kollisionsvermerk steht dort, nicht nur in einer Klammer (N2) | `orchestrator` |
| **R20** | **V2-ERROR vs. menschliche Doku-Erstellung.** Ab W3 ist V2 ERROR: legt ein Mensch eine neue `docs/**/*.md` an, ist `--validate` (= `TEST_COMMAND`) **rot**, bis ein Sync mit `docs-consolidation.enabled: true` gelaufen ist. Das ist ein **Workflow-Vertrag ohne Owner** und blockiert potenziell jeden Doku-PR. | **hoch** | Als **OQ8** mit Owner (`orchestrator` + `git`), Reihenfolge (Entscheidung vor W3) und Empfehlung (Commit-Hook) aufgenommen; der Vertrag ist in §10 als expliziter W3-Schritt festgehalten. **Nicht** durch Abschwächen von V2 gelöst — V2 ist der Zweck der Initiative. **Stand 2026-09-26:** die Empfehlung (Commit-Hook) ist **nicht** übernommen — der Nutzer hat den deterministischen **Sync-/Validator-Lauf** entschieden (§11.2 OQ8); der Owner- und Reihenfolge-Vertrag bleibt, **V2 bleibt ERROR**, ein neuer Hook wird **nicht** gebaut | `orchestrator` |

### 12.3 Threat Model (vier Fragen)

**1. Was bauen wir?** Einen deterministischen Doku-Fakten- und Index-Generator (4 Module,
8 Dateien in `scripts/`, 1 neue Config-Datei, 1 Schema-Block) plus ~65 Doku-Dateien-Umzüge
und 9 Konsistenz-Checks. Kein Datenspeicher, keine Authentifizierung, keine Autorisierung,
keine Netzwerkzugriffe, keine neuen Abhängigkeiten. Nutzerursprung: **intern**
(agent-meta-Repo) + **Downstream-Submodule** (agent-meta wird als Git-Submodul eingebunden).

**2. Was kann schiefgehen?**

| # | Bedrohung | Real belegt? |
|---|---|---|
| a | **Falscher Fakt wandert in eine getrackte `README.md`/`llms.txt`** und fällt im Review nicht mehr auf, weil er maschinell „aussieht". Ein systematisch falscher Zähler passiert V1–V9 **alle**, weil V6 gegen dieselbe Formel prüft | **ja** — Rev. 0.1 enthielt drei solche Fehler (Tier 4/5, DoD 6/7, Pipelines 6/7 bzw. 7/8) |
| b | **Doppel-Writer** zerstört den `docs/INDEX.md`-Vertrag (Generator überschreibt Scaffold-Skeleton oder umgekehrt) | **ja** — 6 Szenario-Asserts hängen exakt daran (`asserts/50:32`, `:51:32`, `:52:44`, `:54:26-27`, `:55:24-25`, `:56:31`) |
| c | Generator überschreibt LLM-eigenes `knowledge/wiki/index.md` → Datenverlust | **ja** — Policy-Bruch gegen `knowledge.py:112-114` |
| d | Unvollständige Fakten rendern `docs-empty`-Marker in eine **Referenzdatei**, die von Nutzern gelesen wird | möglich — `{{DOCS_*}}` löst in `llms.txt`/`README.md` sichtbar auf |
| e | Ein Allowlist-Eintrag unterdrückt genau die Drift-Findings, die er unterdrücken soll (Basis-Pfad vs. `#`-Key) | **ja, im Code belegt** — `fnmatch` matcht den ganzen String (`generated_file_drift.py:82-84`) |
| f | Neue Doku-Datei blockiert `--validate` und damit den gesamten Dev-Workflow (R20/OQ8) | möglich, Owner unbekannt |
| g | **Rev. 0.8:** ein deklarativer Eigentümer-Key (`docs-consolidation.index-owner`) wird zum zweiten Pfad, auf dem `docs/INDEX.md` geschrieben oder **nicht** geschrieben wird — und damit zu einer zweiten Stelle, an der ein Tippfehler den Index einfrieren könnte. **Zweite Ausprägung (RVW8-5):** die Deklaration wird von einem **Consumer-Projekt kopiert** (Übernahme der `project.yaml`-Zeile aus agent-meta, Beispiel-Config, Scaffold eines neuen Projekts) und hebt dort die KE-Autorität stumm auf | **ja, teilweise** — der Tippfehler-Pfad ist durch `enum` + `additionalProperties: false` (`config/project-config.schema.json:2470`) **abgedeckt**, aber die Schema-Validierung im Sync-Pfad ist **best-effort**: `scripts/lib/config.py:342` („Schema validation … **if** jsonschema is available"), `:372-388` („jsonschema not installed or validation error — **best-effort**", `pass`). Fehlt `jsonschema`, greift **kein** Enum. Die **einzige garantierte** Absicherung ist deshalb der **Code-Zweig IC-25 (1)** (`doc_renderer.py:663-711`, fail-closed vor der KE-Prüfung, gepinnt in AC-44c). **Der Kopier-Pfad ist davon unberührt** — er ist kein Tippfehler, sondern eine gültige Deklaration |

**3. Was tun wir dagegen?**

- **Master-Schalter:** `docs-consolidation.enabled` fail-off, für **Writer und Checks
  gleichermaßen** — schaltet das gesamte Feature ab (IC-13, IC-05, IC-22).
- **Zweiter Hebel:** `index-mode: skeleton` lässt den Scaffold-Skeleton unangetastet (IC-15).
- **Besitzregel:** der Generator überschreibt nur, was er selbst erzeugt hat (IC-13).
- **Unabhängige Zahlenquelle:** `config/doc-facts-expected.yaml` bricht den Kreis
  `doc_facts → Renderer → V6` (IC-23, R14) — das ist die **einzige** Gegenmaßnahme gegen (a).
- **Szenarien als Fremd-Gate:** 50/51/52/54/55/56 sind unveränderbar und schützen (b)
  unabhängig von dieser Spec (AC-38).
- **First-Write-Sicherung + spezifizierter Restore-Pfad** gegen (c) (AC-35, IC-24, AC-41).
- **`docs-empty`-Marker** + Fact-Hash-Footer + `dry_run`-Vertrag gegen (d) (IC-07, IC-14).
- **Allowlist-Basis-Pfad-Regel** + AC-37 gegen (e).
- **Workflow-Vertrag** (OQ8, R20) gegen (f).
- **Gegen (g) — fail-closed Code-Zweig IC-25 (1)** (`doc_renderer.py:663-711`): jeder Wert, der
  weder `auto` noch `docs-consolidation` ist, wird **vor** der KE-Prüfung in
  `UNKNOWN_INDEX_OWNER_REASON` verweigert; `null`, `None` und jeder Fremdstring sind eingeschlossen.
  **Das ist die einzige *garantierte* Absicherung** — sie ist **nicht** durch das Schema ersetzbar,
  weil `enum` nur greift, wenn `jsonschema` installiert ist (`config.py:342`, `:388`, best-effort).
  Gepinnt in **AC-44(c)**, Modus-Übersicht §17.12.4 Zeile 5. **Sichtbarkeit:** die Deklaration ist
  eine **einezelne Zeile** in `.meta-config/project.yaml:398-401` und erscheint im Config-Diff;
  ein absichtliches Zurücksetzen auf `auto` ist damit im Review sichtbar.
- **Gegen (g), Kopier-Ausprägung — *noch keine* Gegenmaßnahme, bewusst offen:** ein gültiger,
  kopierter `index-owner: docs-consolidation` ist per Konstruktion **nicht** als Tippfehler
  erkennbar, weder per Enum noch per Code-Zweig. **Restrisiko, ausdrücklich NICHT akzeptiert und
  NICHT entschieden** — als **E-13c „Kopier-Pfad"** geführt: die Optionenzeile in **§17.12.2**
  benennt die beiden Entscheidungspunkte namentlich (Doku-Pflichtträger; `validate`/`--strict`-
  Meldung, wenn `index-owner` in einem Projekt mit `knowledge-engine.enabled: true` gesetzt ist)
  mit Optionen, Empfehlung, Owner und Termin. **RVW9-4:** dieser Bullet ist der Beleg dafür, dass
  der Kopier-Pfad **keine** unterstellte Entscheidung ist — er ist **offen** und wird in dieser
  Revision **nicht** entschieden.

**4. Welche Konsequenzen?**
- (a) Nutzer und alle Downstream-Submodule erhalten falsche Zahlen über `README.md` und
  `llms.txt`; die Korrektur ist teuer, weil sie über Submodul-Grenzen propagiert. **Schwer.**
  → R14, IC-23.
- (b) Roter Regressionstest auf `TEST_COMMAND`-Ebene ⇒ **alle** Wellen blockiert. **Schwer.**
  → R7, IC-12/IC-13/IC-15, AC-38.
- (c) Datenverlust im Wiki-Index; Recovery über Sibling-Backup oder Git. **Mittel**, weil
  `knowledge/` git-getrackt ist. → R2, IC-24.
- (d) Ein `docs-empty`-Marker erscheint in einer gelesenen Referenzdatei; die Aussage ist
  sichtbar, nicht still — Recovery ist das Nachrechnen der Fakten. **Gering.** → IC-01 Fehlerpfade,
  IC-07, IC-14.
- (e) Drift wird still übersehen — das Gegenteil des Ziels, aber **leise**. **Mittel.**
  → R17-Klassifikation, AC-37.
- (f) Frustration, Workaround über `checks.strict: false`, damit der Gain wieder verloren ist.
  **Mittel.** → R20, OQ8.
- (g) Zwei Ausprägungen. **Tippfehler:** der Index bleibt in jedem Sync `skipped` — Recovery ist
  das Zurücksetzen des Werts; grüner Log, eingefrorener Index, **keine** Fehlermeldung, weil
  `skipped` der erwartete Zustand ist. **Schwer zu bemerken**, leicht zu beheben → IC-25 (1),
  AC-44(c). **Kopierte Deklaration in einem KE-Projekt:** dasselbe eingefrorene Bild, aber ohne
  falsche Eingabe — die KE-Autorität ist für **dieses** Projekt stillschweigend aufgehoben, während
  die Oberfläche weiter „knowledge-engine ist autoritativ" behauptet. **Recovery:** `index-owner`
  auf `auto` setzen bzw. die Zeile entfernen. **Schwerer**, weil kein Fehler entsteht, den man suchen
  würde → **Restrisiko, an E-13c offen** (§12.3 Q3-Bullet; Vorlage **E-13c** in **§17.12.2** — RVW9-4: der Verweis zeigte bis dahin auf §17.12.3 DECISION-1…4, wo der Bullet **nicht** steht).

**Bewertung:** Alle **sieben** Bedrohungen (a…g) sind adressiert, aber **zwei** nur unvollständig:
(a) wird ausschließlich durch eine **Handpflege-Datei** gebrochen — ein Fehler in *dieser* Datei
ist wiederum ein Fehler, nur in einer anderen Quelle. Das ist eine echte, benannte
Restgrenze (R14-Restrisiko in IC-23) und kein Versehen: eine dritte, unabhängige Quelle wäre
Over-Engineering für elf stabile Zählwerte. **(g)** ist gegen den Tippfehler-Pfad hart
(IC-25 (1), AC-44c), gegen die **kopierte** Deklaration jedoch **offen**: dort greift weder das
`enum` (die Deklaration ist gültig) noch der fail-closed Zweig (der Wert ist bekannt). Die
Entscheidung darüber ist **nicht** in Rev. 0.8 gefallen — sie ist als **Ergänzung zu E-13**
registriert und liegt beim Auftraggeber.

---

## 13. Abweichungen vom Design (bewusst, begründet)

| # | Design sagt | Diese Spec sagt | Begründung |
|---|---|---|---|
| **A1** | F13: „Rollen-Parität gebrochen: Template existiert, `roles:` **nicht**" (`project.yaml:91-151`) | **Korrigiert:** `se-component-requirements` **ist** in `roles:` (`.meta-config/project.yaml:148`) und das Template existiert. Die Paritätsverletzung entsteht **allein** aus `systems-engineering.enabled: false` (`:12-13`) → `agent_sync.py:548` überspringt alle 14 `se-*`-Rollen | VERIFIED am Working Tree. Die Design-Aussage ist falsch; sie hätte in W8 zu einem wirkungslosen Config-Edit geführt („Einzeiler in `project.yaml roles:`", R5), obwohl die Rolle dort bereits steht |
| **A2** | V5: „`project.yaml roles:` ⊄ generierte Provider-Agent-Dateien" | **Gate-bewusst:** Vergleichsmenge ist `compute_active_roles()` = `roles` ∩ Templates ∩ `resolve_activation_gates()` (IC-04) | `roles:` umfasst 59 Einträge (`:92-150`), `role-defaults.yaml:1` umfasst 84, SE ist deaktiviert → die Design-Formel ist ein **Dauerfehlalarm** (F21) und hätte V2/W2 blockiert. Siehe NG-8 |
| **A3** | §3.4: „unbekannter Platzhalter-Name → bleibt wörtlich + **`--validate` ERROR**" | Unbekannter Name → bleibt wörtlich (`substitution.py:86-87`) + `placeholders.unknown` = **WARNING** (`placeholders.py:177-182`). Das **ERROR**-Gate ist **V6** | VERIFIED: `check_placeholders` kennt nur WARNING. Die Design-Formulierung versprach ein Gate, das im Code nicht existiert. Zusätzlich verlangt IC-06 die Registrierung des `DOCS_`-Prefixes, die das Design nicht nannte |
| **A4** | C8 als alleiniger Schutz gegen den Doppel-Writer (B2) | **C8 plus verbindliche Stage-Reihenfolge**: Generator **nach** `scaffold_spec_plan_dirs` (IC-12) | `scaffold_spec_plan_dirs` schreibt `docs/INDEX.md` nur im `file-index`-Modus (`spec_plan_scaffold.py:62-68`) und läuft in `_sync_stage_knowledge_and_isolation` (`sync_pipeline.py:935`). Läuft der Generator davor, gewinnt der Scaffold. Reihenfolge ist die stärkere, einfachere Garantie; C8 bleibt als zweite Verteidigungslinie |
| **A5** | §3.2: `{{DOCS_SCENARIO_COUNT}}` Quelle = `tests/scenarios/` | Quelle = `tests/scenarios/asserts/*.sh` (63 Dateien); `tests/scenarios/*.md` enthält **nur** `registry.md` | VERIFIED. Mit der Design-Quelle wäre der Wert 1 statt 63 |
| **A6** | §3.2/§0 F3: „Ist 15 `.sh` unter `hooks/**`" | Ist **17** `.sh`; nach der Exklusionsregel (ohne `lib/`, ohne `release-gates/`) **13** | VERIFIED per Glob. Die Designzahl 15 ist falsch; die Exklusionsregel selbst ist korrekt und wird in IC-02 kodiert |
| **A7** | F-Liste endet bei F18 | F19 **gestrichen** (Tier-Presets sind 5, `README.md:689` ist korrekt); ergänzt **F20** (Skeleton-Marke), **F21** (`roles` 59 vs. 84 vs. generiert), **F22** (DoD-Presets 7 vs. `README.md:688` „6"), **F23** (vierter Guide-Ort `docs/howto/`), **F24** (zwei Beispiel-Configs), **F25** (Config-Schema kennt die Keys nicht) | **Korrektur einer eigenen Fehlkorrektur.** Rev. 0.1 führte F19 als Befund und hätte den Wert **4** generiert; `config/tier-presets.yaml` hat nachweislich 5 Tiers (`:1, :31, :85, :115, :145`). F19 ist ersatzlos entfallen (kein ID-Recycling); die übrigen sechs Befunde sind am Working Tree verifiziert. F20 begründet die Marke in IC-15, F21 die Korrektur A2, F22 die Zahl 7 in IC-02, F23 die Migration M-6, F24 die offene Frage OQ9, F25 die Operation M-11 |
| **A8** | Drift über `capture_generated_file_hashes()` „README-Marker-Regionen und `docs/INDEX.md` aufnehmen" | **Nur** `docs/INDEX.md` + `docs/architecture/INDEX.md` als ganze Dateien; Marker-**Hosts** (`README.md`, `llms.txt`, `ARCHITECTURE.md`) nur über den **extrahierten Marker-Body** mit Store-Key `<datei>#docs:<region>` | `README.md` enthält Handprosa (hybrid). Ein Ganzdatei-Hash würde jede Prosa-Änderung als Drift melden — R1-Churn. Für Marker-Bodies gilt NFA-05 (nicht überschreiben), weil `backup_drifted_files` für einen `#`-Key fail-soft **kein** Backup erzeugt (`generated_file_drift.py:379-386`, verifiziert) — und `is_allowlisted` wird deshalb gegen den **Basis-Pfad** gematcht (`:82-84`, verifiziert). Siehe IC-16, AC-19, AC-37 |
| **A9** | §11: vier Wellen-Specs | **Eine** Spec-Datei mit vier abgeschlossenen Modulen (§4) | Auftragsvorgabe; die Repo-Konvention verlangt eine `spec-id` pro Datei, nicht eine Datei pro Welle. Aufteilung ist **Planungsentscheidung** des Planners (§4) — als **OQ7 geschlossen** geführt, nicht offen (§11.2) |
| **A10** | Design nennt keinen `docs-consolidation`-Config-Block | IC-22 definiert **sechs** additive Keys mit **Fail-off**-Defaults (`enabled` = `false` bei Abwesenheit, auch in agent-meta explizit `true`) | **Korrektur der Rev.-0.1-Fassung (K5).** Rev. 0.1 setzte „Schema-Default = Default agent-meta" **und** `enabled: true` als Abwesenheits-Default — unvereinbar, weil `true` selbst ein Verhaltenswechsel bei Abwesenheit ist. Auflösende Präzedenz: `knowledge.py:127` (`ke_config.get("enabled", False)`), fail-off für Writer **und** Checks. Ohne diese Regel hätte die neue Stage 6 Szenarien gebrochen. Zusätzlich: M-11 nimmt `config/project-config.schema.json` als Operation auf (R15) |
| **A11** | V1 gilt als ERROR ab Start | V1 startet **WARNING** in W2, wird nach W3 ERROR — wie im Design §6 W2 vorgesehen; zusätzlich `docs-consolidation.checks.strict` (IC-22) | Konsistent mit Design W2 („V1 startet als WARNING, `--validate` noch nicht blockierend"); als Config-Key operationalisiert, damit B4 für Consumer auflösbar ist |
| **A12** | **Neu (rev. 0.2):** IC-03 las die Stale-Deklaration aus `ARCHITECTURE.md:3` (Design §5.3: „aus `ARCHITECTURE.md:3` maschinell extrahiert") | Quelle ist **`docs/architecture/00-overview-full.md`**; die Deklaration **wandert mit** der Langfassung (M-7) | Der Design-Satz und IC-18/AC-29 waren **zirkulär**: der Stub verliert nach W4 (M-2) alle eigenen Inhalte, also auch `:3` — die Quelle der Extraktion wäre weg. Beleg: `knowledge/wiki/index.md:24` beschreibt `concepts/architecture.md` als „Rohkopie von **ARCHITECTURE.full.md**", nicht von `ARCHITECTURE.md`. IC-03, IC-18 und AC-29 sind konsistent auf die Langfassung umgestellt |
| **A13** | **Neu (rev. 0.4):** Design-W0 nennt den Branch `chore/docs-consolidation` — `docs/specs/2026-09-25-repository-documentation-consolidation-design.md:265`, Spalte „Inhalt" der Tabelle in §6 MIGRATION_ORDER | Verbindlich ist seit Rev. 0.4 der Wellen-Branch **`feat/repository-documentation-consolidation-main`** (Basis `origin/main`) mit **einem** PR gegen `main` (§9.2 W0-Zeile und Absatz „PR-/Branch-Strategie", Punkt 1) | **Nutzer-Vorgabe + Plan-Korrektur K1/K9** (Plan Rev. 0.4, Global Constraints, Task **W0-2**). Die Rev. 0.1–0.3-Fassung „ein Branch **pro Welle** (`chore/docs-consolidation-w<N>`)" war selbst schon eine **Eigenkonstruktion** ohne Design-Deckung — das Design verlangt an keiner Stelle gestapelte PRs und nennt **einen** Branch. Korrektur des Branch-**Namens** gegen die Design-Angabe; der **Umfang** (ein Branch, ein PR) stimmt mit dem Design überein. **Verifiziert am 2026-09-26:** Design-Zeile gelesen, Branch-Name wörtlich `chore/docs-consolidation`. Status: **geschlossen** (Nutzer-Bestätigung Rev. 0.4 vom 2026-09-26, §17.7) |
| **A14** | **Neu (rev. 0.4):** Design §6 führt **W4, W5 und W6 paarweise parallel** — `docs/specs/2026-09-25-repository-documentation-consolidation-design.md:269` (W4: „W5, W6"), `:270` (W5: „W4, W6"), `:271` (W6: „W4, W5"); **zusätzlich** `:275` („Ownership-disjunkte Parallelität: W2 ‖ W3 ‖ W5 sind gleichzeitig ausführbar") — W5 ist danach auch mit **W2/W3** parallel ausgewiesen | §9.2 weist **W4 → W5 → W6 sequenziell** aus (`parallel_group` PG-3, ein Agent) | **Plan-Begründung (PG-3, Plan Rev. 0.4, „Warum W2 ‖ W3 parallel ist, W4/W5/W6 aber nicht"):** die vier AC **AC-28, AC-29, AC-31, AC-32** verweisen **alle** per `::` auf denselben Testdatei-Anker `tests/test_docs_consolidation_migration.py`; parallel ausgeführte Tasks, die dieselbe Datei anlegen oder erweitern, sind nicht ownership-disjunkt — `check_plan_file_overlap` (`scripts/lib/orchestration.py`) würde den Parallelstart als Fehler melden. Zusätzlich erzeugt jede `git mv`-Welle R+A-Diffs auf denselben Stammpfaden. **Diese Abweichung ist vorbestehend und NICHT von Rev. 0.4 erzeugt.** **Status: OFFEN** — vom Nutzer am 2026-09-26 bewusst als *offene, dokumentierte* Abweichung registriert und **hier nicht inhaltlich aufgelöst**. Owner: `orchestrator` → `main_chat`. Volltext, Auflösungsweg und Review-Pflicht: **§17.8** |

**Zählung:** **14** Abweichungen — A1…A12 (rev. 0.1/0.2, unverändert) + **A13** (rev. 0.4,
geschlossen) + **A14** (rev. 0.4, **offen**).

**Übernommen ohne Änderung:** T-1…T-6, die SSoT-Zielstruktur (§1/§1.1 des Designs → §3 hier),
C1–C8 (→ M1–M4 hier), V1–V9 (→ IC-05 hier, mit den Korrekturen A2/A3), W0–W8 (§9.2),
B1–B6 (→ AC-32, IC-17, IC-22, NFA-04, R2/R7/R8), §5.1–§5.4 der Knowledge-Policy (→ IC-19…IC-21).

---

## 14. Out of scope / Folge-Issues

| # | Folge-Issue | Begründung / Owner |
|---|---|---|
| FI-1 | **REQ-IDs für die Traceability-Lücken** (Knowledge Engine, `spec-plan-workflow`, auto-commit, quality-pipelines, hooks, Codex/ZCode/KimiCode) | `docs/REQUIREMENTS.md` kennt heute nur `REQ-CMD-*`, `REQ-GEN-*`, `REQ-PROV-*`, `REQ-SYNC-*`, `REQ-SE-*` (`:9-60`); die genannten Bereiche haben **keine** REQ. Zuweisung ist Aufgabe von `requirements`, **nicht** dieser Spec (kein REQ-ID-Auftrag) |
| FI-2 | `docs/CODEBASE_OVERVIEW.md:33-44` — toter Verweis auf `agents/1-generic/se-orchestrator.md` | **NG-3**: Datei gehört `documenter` (`knowledge/wiki/log.md:30`). Nicht in dieser Initiative editierbar. Owner `documenter` |
| FI-3 | `docs/providers/` deckt 6 von 9 Providern ab (fehlen u. a. eigene Seiten für Claude, Continue, Copilot, Mammouth) | Inhaltliche Doku-Arbeit (NG-1), keine Struktur-Arbeit. Owner `documenter` |
| FI-4 | Inhaltliche Konsolidierung von `knowledge/wiki/topics/` ↔ `docs/guides/` | **OQ1**, Produktentscheidung |
| FI-5 | `AGENTS.md`-Bootstrap-Block (66 hartgelistete Agenten) generieren | **OQ3**, eigener Blast Radius (B6) |
| FI-6 | provider-Referenzseiten für die 3 fehlenden Provider + `README.md:690`-Text auf generierten Block umstellen | Teil von W3/W8, aber **inhaltlich** nach FI-3 |
| FI-7 | `knowledge/sources/docs/guides/` enthält einen alten Guide-Snapshot; die SSoT-Umstellung macht ihn zur reinen Historie | Kein Eingriff (NG-2, append-only). Nur als Doku-Hinweis in `docs/architecture/00-overview-full.md` |
| FI-8 | Rollen-Paritäts-Fix (Config-Edit in `roles:` bzw. SE-Gate) | **NG-8**, eigene REQ |
| FI-9 | `docs/specs/`-Namensschema vereinheitlichen (`SPEC-*`-Naming vs. `REQUIREMENTS.md`) | **OQ4** / **NG-6**, Entscheidung `requirements` + `validator` |
| FI-10 | Abbau der 179 `*.sync-backup-*`-Leichen in `.claude/agents/` | **V9** (W8) meldet nur; das Aufräumen ist eine lokale Aufräumaktion, kein Spec-Gegenstand. **RVW2-4:** die Zahl **179** ist eine **Bestandsangabe**, im Working Tree **nicht messbar** (gitignoriert, `.gitignore:13`/`:22`) — sie ist **kein** Sollwert; verbindlich ist die regelbasierte Form in IC-05 (V9) und §10, `--strict`-Punkt, Unterpunkt 5 |

---

## 15. Trace-Anker

```
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
→ Eingang für concept-specifier (Stage "specify" in quality_pipelines.concept-driven-dev)
→ Approval-Gate: Status Entwurf → APPROVED nur durch concept-reviewer nach User-Freigabe
   (Gate durchlaufen: Freigabe 2026-09-26, siehe §Freigabevermerk oben)
→ Plan referenziert: SPEC-DOCS-CONSOLIDATION-2026-09-25
→ Verwandt (unverändert übernommen, keine Supersession):
    docs/REQUIREMENTS.md                        (REQ-*-Master-IDs, Formatregel :4)
    docs/plans/README.md                        (docs/plans/-Konvention, archive/)
    scripts/lib/spec_plan_scaffold.py:23        (docs/INDEX.md-Vertrag)
    docs/specs/2026-09-25-repository-documentation-consolidation-design.md
                                              (verbindliche Design-Grundlage)
    Concept-Review + Re-Review vom 2026-09-26 (Session-Artefakte, nicht committet;
                                              Ausgang in §17.1 und §17.5 protokolliert)
→ Bei Aufteilung (OQ7 geschlossen, §11.2 — Planungsentscheidung des Planners):
    SPEC-DOCS-FACTS-2026-09-25        (M1, W1+W2)
    SPEC-DOCS-INDEX-2026-09-25       (M2, W3+W4)
    SPEC-DOCS-MIGRATION-2026-09-25   (M3, W5+W6+W8)
    SPEC-KNOWLEDGE-INDEX-GEN-2026-09-25 (M4, W7)
→ Rev. 0.4 (2026-09-26) — Ausführungskorrektur der Branch-/PR-Strategie (OP-1), §17.6:
     Ausführung belegt in docs/plans/2026-09-25-repository-documentation-consolidation.md
       (Rev. 0.4, Global Constraints, Task W0-2)
    und docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md §7.1/§7.2
    Geändert: §9.2 (W0-Zeile, Absatz "PR-/Branch-Strategie"), R16-Mitigation, §15/§16/§17.6.
     Unverändert: alle ID-Mengen, §9.1, status APPROVED.
     §13: 14 Abweichungen — A1…A12 unverändert, A13 (Branch-Name) und A14 (W4/W5/W6 seriell,
       offen) in Rev. 0.4 ergänzt.
     Rev. 0.4 am 2026-09-26 durch den Nutzer bestätigt (§17.7); A14 bleibt offen (§17.8).
     Kein neuer spec-id, keine Supersession.
→ Rev. 0.5 (2026-09-26) — Gate-Präzisierung W2/W3, Finding-Ownership, V1-Sichtbarkeit vor
  Hochstufung, §17.9; zweite Korrekturrunde desselben Revisionsstandes, §17.9.4:
      Auftrag: A2A-Envelope vom 2026-09-26 (Korrekturen 1–5; ausdrückliche Weisung,
        status APPROVED beizubehalten) · Review: concept-reviewer 2026-09-26,
        CHANGES_REQUESTED, 15 Findings RVW-1…RVW-15, alle behoben
     Geändert: §10 (Nachweisform, neue Punkte 5/6), §5.1.1 (Suppressionsregel 3),
        §12.1 R4-Verweis, §Revision (0.5-Zeile), §15/§17.9/§17.9.4, Frontmatter approved-scope.
       Unverändert: alle ID-Mengen, §9.1, §9.2-Welleninhalt, der normative Pflichtumfang
         im §10-Aufzählungspunkt --validate, status APPROVED, approved 2026-09-26,
         revision 0.5 (kein Bump).
      Ausführung belegt in docs/plans/2026-09-25-repository-documentation-consolidation.md
        (Rev. 0.5, Abschnitte „W2 — Verifikation", „W3 — Verifikation", Kriterientabelle
        W-GATE-TABLE, Reihenfolge-/Abhängigkeitsmatrix, Abschnitt L).
      Kein neuer spec-id, keine Supersession; OQ1 bleibt offen, OP-1 bleibt offen.
→ Rev. 0.8 (2026-09-29) — agent-meta-Ausnahme im KE-Vorrang-Gate, §17.12:
     Eingang: docs/specs/2026-09-25-repository-documentation-consolidation-design-agent-meta-exception.md
       (concept-architect, 2026-09-29, status: draft, DECISION-1…DECISION-4, P-1…P-5, K-1…K-5, E-9…E-13)
     AUSLÖSER (gemessen): doc_renderer.py:702-703 · project.yaml:69/:77/:15 · spec_plan_scaffold.py:80-97
       · docs/INDEX.md existiert nicht (Glob) · docs_index.py:180-211
     ZUR USER-FREIGABE AUSSTEHEND: P-1…P-5 (IC-13, IC-15, IC-22-Tabelle, AC-21 + AC-39, R7) — §17.12.1;
       darunter P-3 (e) / "P-3-E" als fünfte Zeile der P-Tabelle, kein sechstes P-Element.
       status: APPROVED und approved: 2026-09-26 bleiben unverändert; der Umfang W0–W8 bleibt
       freigegeben; Rev. 0.8 ist NICHT durch status: APPROVED gedeckt (Frontmatter pending-approval:).
     OFFEN: E-9…E-13 (Entscheidungsvorlagen, §17.12.2) — keine ist entschieden.
       E-5…E-8 bleiben entschieden (Rev. 0.7, §17.11). OQ1 bleibt offen, Blockade W5.
     Geändert: IC-13, IC-15, IC-22; NEU IC-25, IC-26; AC-21, AC-39; NEU AC-42…AC-46; R7;
       §12.3 Threat Model (Zeile g, Q3, Q4, Bewertung); **§9.1 (AC-42…AC-46, AC-21, AC-39)**,
       **§9.2 (W3-, W8-Zeile, Zählsatz, Fußnote ¹)**; Revisionszeile 0.8; §17.12 (Volltext, K-1…K-5,
       E-9…E-13, DECISION-1…DECISION-4, Nachweis-/Testakzeptanz, V-D1…V-D4, Coverage-Checkliste).
     KORREKTURRUNDE ZU REV. 0.8 (2026-09-29, Concept-Review Runde 8, CHANGES_REQUESTED,
       5 major / 5 minor — Katalog **K77…K86**, §17.12.6):
       RVW8-1 K-3/T-4/V-D4 auf den belegten Stand (Kommentar :42-44 EXISTIERT — Fehlmessung
         des Read-Tools, per Grep widerlegt); RVW8-2 _IC22_ABSENCE_DEFAULTS als ZWEITE harte
         Sollwert-Änderung registriert ("die einzige" zurückgenommen); RVW8-3 AC-42…AC-46 in
         §9.1/§9.2 + Zählsatz (W3 14→19); RVW8-4 V-D7 (T-8→T-3→T-5, alle W3-6) + E-13a
         zurückgenommen; RVW8-5 §12.3 (g) auf alle vier Fragen beantwortet inkl. Kopier-Pfad,
         Ziffer sechs→sieben, (d) ergänzt; RVW8-6 best-effort-Charakter der Schema-Validierung
         (config.py:342/:388); RVW8-7 AC-42(d) Anker geteilt (:629 / :635-639); RVW8-8
         Anker-Auswahlregel + vollständiges V-D1/V-D2-Inventar; RVW8-9 AC-39 Belegquelle
          berichtigt; RVW8-10 V-D6 (Planlücke W3-7/sources) + Testname in Zeile 4.
     ZWEITE KORREKTURRUNDE ZU REV. 0.8 (2026-09-29, Concept-Review Runde 9, CHANGES_REQUESTED,
       2 major / 7 minor / 1 info — Katalog unverändert **K77…K86**, §17.12.6; kein Revisions-Bump):
       RVW9-1 (major) K-Katalog **K61…K70 ⇒ K77…K86**, Vorspann auf "ab K77; K1…K76 bleiben
         unberührt"; maßgebliche Obergrenze K76 (Plan-Legende, gemessen) dort genannt; alle ~20 Fundstellen
         nachgezogen (Frontmatter, Kopfblock, IC-15 :1465-1466, IC-25 :1592, §9.1, §9.2, §15,
         §17.12.1, §17.12.4, §17.12.5, §17.12.6, Trace-Matrix, Coverage).
       RVW9-2 (major) **V-D8** registriert: Plan Rev. 0.7 kennt Rev. 0.8 nicht — W3-6 ohne T-3/T-5/
         T-7/T-8/AC-42…AC-46, W1-9 abgeschlossen und mit der Fehlzählung "sechs Properties",
         **kein** pending-approval: im Plan-Frontmatter; **forderlicher Plan-Delta** präzise
         benannt in §17.12.5 (V-D8-Uebergabe an den planner) — Plan **erst nach** User-Freigabe.
       RVW9-3 T-4-Ordinal "sixth" ⇒ "seventh" (tests/…migration.py:43), K-77 nachgezogen.
       RVW9-4 **E-13c** (Kopier-Pfad) als dritte Optionenzeile in §17.12.2; Q4-Verweis
         §17.12.3 ⇒ **§12.3** (:3030).
       RVW9-5 P-3-E als **P-3 (e)** geklärt (fünfte P-Tabellenzeile, kein sechstes P-Element).
       RVW9-6 K-78-Verortung auf Modus-Übersicht Zeile 8 / T-3 / Coverage berichtigt.
       RVW9-7 Testname ::test_fail_off_defaults_* ⇒ **::test_schema_declares_the_absence_defaults**
         (tests/…migration.py:185-199) in :4329, :4374, :4413.
       RVW9-8 V-D1-Selbstverweis :1449-1450 ⇒ **:1487-1488** (**RVW10-2**: der RVW9-8-Zwischenanker :1465-1466 war IC-13-Fließtext, nicht der Anker) ⇒ RVW9-8 geschlossen; **Info-Notiz
         ohne eigene R9-ID** (Label aus der R10-Tabelle, `rereview-10.md:59`): §9.2-W3-Fußnote ¹ macht die AC-39-Zählkonvention sichtbar. **Runde 10 vollständig: §17.12.6 :4599-4606.**
       RVW9-9 W1-10-Step-2-vs-T-7 Reihenfolge festgehalten (§17.12.4 T-7, §17.12.5 V-D8).
      DRITTE KORREKTURRUNDE ZU REV. 0.8 (2026-09-29, Concept-Review Runde 10, CHANGES_REQUESTED,
        1 major / 1 minor / 1 info — Katalog unverändert **K77…K86**, §17.12.6; kein Revisions-Bump):
        RVW10-1 (major) K-Katalog **K76…K85 ⇒ K77…K86** umnummeriert (rein additiv; **keine** der
          zehn Bedeutungen gestrichen, **keine** K-ID unterhalb K76 angetastet); maßgebliche
          Obergrenze auf den **gemessenen** Plan-Stand `K1…K76` korrigiert; alle Fundstellen
          nachgezogen.
        RVW10-2 (minor) V-D1-Selbstverweis auf den gemessenen Anker **:1487-1488** gezogen
          (bisher `:1465-1466` — IC-13-Fließtext, nicht der Anker) ⇒ RVW9-8 geschlossen.
        RVW10-3 (info) Registriert, **nicht** geändert: der zweite Träger derselben
          Ordnungs-Formulierung (`tests/test_doc_renderer.py:1090-1091`) liegt außerhalb der
          `Files:`-Liste ⇒ keine Testdatei geändert, keine neue T-ID, kein Eingriff in T-3.
        Autoritative Aufzeichnung: **§17.12.6 :4599-4606** (R10-Tabelle) — dort ist jede
          Fundstelle einzeln benannt und belegt; der Vollständigkeitssatz der Runde 10 gilt
          einschließlich des in dieser Korrekturrunde nachgetragenen §15-Blocks.
     UNVERÄNDERT durch die Korrekturrunde: P-1…P-5 bleiben ZUR USER-FREIGABE AUSSTEHEND,
       E-9…E-13 und OQ1 bleiben OFFEN, pending-approval: besteht fort, status APPROVED und
       approved 2026-09-26 unverändert, Umfang W0–W8 unverändert, keine Umnummerierung.
     Unverändert: status APPROVED, approved 2026-09-26, Umfang W0–W8, §17.10/§17.11,
       IC-01…IC-24, AC-01…AC-18 und AC-20/AC-22…AC-38/AC-40/AC-41, NFA-01…NFA-11, R1…R6/R8…R20,
       F1…F25, M-1…M-13, NG-1…NG-11, FI-1…FI-10, OQ1…OQ10, V1…V9, Taskzahl 50.
     Kein neuer spec-id, keine Supersession; keine bestehende ID umnummeriert oder gestrichen.
```

**Vollständigkeits-Checkliste (Coverage, keine Selbstbewertung):**

| Pflichtelement | Ort | Status |
|---|---|---|
| Problem / messbare Baseline mit `Datei:Zeile` | §1.1 (F1…F25, davon F19 gestrichen), §1.2 | vorhanden |
| Scope-Grenzen explizit (inkl. `sources/`- und Ownership-Hard-Constraint) | §2.2 NG-1…NG-11, §2.3 | vorhanden |
| Zielstruktur / SSoT-Matrix mit Generationsmodus | §3.1, §3.2, §3.3 | vorhanden |
| DocFacts-Berechnung | IC-01, IC-02, IC-03, IC-04 | vorhanden |
| **Unabhängige Sollwert-Quelle gegen den Kreis `doc_facts → Renderer → V6`** | IC-23, AC-36, R14, NFA-11 | vorhanden |
| Platzhalter-Namespace `DOCS_*` + `DOCS_*_BLOCK` | IC-02, IC-06, IC-11 | vorhanden |
| Synchronisation in die Default-Stage (Muster `sync_knowledge_engine`) | IC-12 (Stage nach `sync_pipeline.py:935`) | vorhanden |
| **Besitzregel für `docs/INDEX.md` (Doppel-Writer)** | IC-13, IC-15, AC-38 | vorhanden |
| `dry_run` / `write_checked` | IC-13, AC-23 | vorhanden |
| Idempotenz-Muster | IC-13, IC-17, NFA-01 | vorhanden |
| Fact-Hash-Footer ohne Zeitstempel, Diff-Stabilität, volatile-Ausnahme | IC-14, NFA-02, AC-03, AC-18 | vorhanden |
| Fallback bei nicht berechenbarem Faktum | IC-01 Fehlerpfade, IC-13, AC-04 | vorhanden |
| **Restore-Pfad für den Policy-Bruch in W7** | IC-24, AC-41 | vorhanden |
| Acceptance Criteria mit V1…V9-Verknüpfung, beobachtbar | §7 (AC-01…AC-41), §9.1 | vorhanden |
| Nicht-funktionale Anforderungen | §8 (NFA-01…NFA-11) | vorhanden |
| Trace-Matrix AC → Wellen → Dateien | §9.1 (**46** AC, K-79), §9.2 (W3-Fußnote ¹) | vorhanden |
| **Threat Model (4 Fragen)** | §12.3 | vorhanden |
| Brücke zu offenen Entscheidungen **und** geschlossenen Punkten | §11.1 (OQ1, OQ3, OQ4, OQ9 — **offen**) / §11.2 (OQ2, OQ5, OQ6, OQ7, OQ8 — **geschlossen**; OQ2/OQ6/OQ8 per Nutzer-Entscheidung vom **2026-09-26**) | vorhanden |
| Risiken R1…R20 mit Mitigation und Owner | §12.1, §12.2 | vorhanden |
| Out of scope / Folge-Issues | §2.2, §14 | vorhanden |
| **Review-Auflösung mit korrigierten Reviewer-Angaben** | §17 | vorhanden |
| **Gate-Erreichbarkeit: je V-Check ein erfüllbarer Erwartungswert mit Termin und Owner** | §10, `--strict`-Punkt, Unterpunkt 5; Plan Rev. 0.5 `W-GATE-TABLE` (Spalten W2…W8) | vorhanden |
| **Nachweisform-Korrekturen ohne neue Pflicht jenseits des beauftragten Umfangs** | §17.9.4 (Präzisierung der Normativitätsaussage + Autorisierung vom 2026-09-26) | vorhanden |
| Kein `TBD`, kein unbenanntes Placeholder | gesamtes Dokument | geprüft (§16) |
| Jedes AC ≥ 1 Interface Contract | §9.1 Spalte „Betroffene Dateien" + IC-Verweise in §7 | geprüft (§16) |
| Jedes AC ≥ 1 V-Check oder explizit als „—" begründet | §9.1 Spalte „V-Check" + Begründungsabsatz | geprüft (§16) |

---

## 16. Selbstreview (concept-specifier, Rev. 0.3, 2026-09-26)

| Prüfung | Ergebnis |
|---|---|
| **No-Placeholder** | Kein `TBD`, kein `???`, kein `FIXME`, kein leeres Feld. Offene Entscheidungen sind ausschließlich **OQ1, OQ2, OQ3, OQ4, OQ6, OQ8, OQ9** (§11.1) mit Owner, Empfehlung, Entscheidungsweg und Wellen-Blockade; **OQ5** und **OQ7** sind in §11.2 ausdrücklich als **geschlossen** mit Begründung geführt. Jede Interface-Signatur ist vollständig typisiert; jede AC nennt Datei **oder** Befehl **und** Exit-Code/Assertion. |
| **Spec vs. Design** | T-1…T-6, C1–C8, V1–V9, W0–W8, B1–B6, §5.1–§5.4, §1/§1.1 übernommen oder **explizit** begründet abweichend. **14** Abweichungen in §13: 3 Faktualkorrekturen (A1, A5, A6), 3 Gate-Korrekturen (A2, A3, A4), 3 Ergänzungen (A7, A10, A11), 1 Sicherheits-Korrektur (A8), 1 Formatentscheidung (A9), 1 Zirkel-Auflösung (A12), 1 Branch-Namens-Korrektur (A13, rev. 0.4), 1 **offene** Parallelitäts-Abweichung (A14, rev. 0.4, §17.8). Keine stille Abweichung. **Neu gegenüber Rev. 0.1:** A7 enthält die Korrektur der eigenen Fehlkorrektur F19, A10 die Fail-off-Auflösung, A12 die Stale-Quellen-Wanderung. **Neu in Rev. 0.4:** A13 (Design nennt `chore/docs-consolidation`, verbindlich ist `feat/repository-documentation-consolidation-main`) und A14 (W4/W5/W6 seriell statt paarweise parallel — **nicht** aufgelöst, bewusst offen). |
| **IDs** | `spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25` im Frontmatter **und** im Trace-Anker (§15), Format `SPEC-<NAME>-<JJJJ-MM-TT>` konsistent mit `docs/REQUIREMENTS.md:4`-Nachbarn und `docs/specs/2026-09-15-reference-standards-design.md:2`. Kein `REQ-*` vergeben (FI-1, Zuständigkeit `requirements`). **AC-01…AC-41 lückenlos und je genau einmal definiert; §9.1 führt alle 41; §9.2 verteilt sie auf W1–W8, jede Welle mit ≥ 1 AC. IC-01…IC-24 lückenlos. NFA-01…NFA-11 lückenlos. R1…R20 lückenlos. F1…F25 lückenlos, F19 ausdrücklich gestrichen (kein Recycling). V1…V9 lückenlos. W0…W8 lückenlos — das heißt: alle **neun Wellen** W0…W8 sind vorhanden; es ist **keine** Aussage über Task-IDs innerhalb einer Welle (gemessen: **W0 hat 6 Tasks** — W0-1, W0-2, W0-3, W0-4, W0-6, W0-7 — und **`W0-5` existiert nicht**; Task-ID-Lückenlosheit gilt für AC/IC/NFA/R/F/V, **nicht** für W-Tasks — Präzisierung Korrekturrunde 5, `validator`-Note `n2`). OQ1…OQ9, davon OQ5/OQ7 geschlossen. M-1…M-13 lückenlos.** |
| **Querverweise** | Jeder `Datei:Zeile`-Verweis wurde am 2026-09-26 gelesen. **Neu bzw. korrigiert in Rev. 0.2:** `config/tier-presets.yaml:1, :31, :85, :115, :145` (5 Tiers); `config/dod-presets.yaml:12, :13, :30, :46, :62, :79, :96, :113` (7 Presets); `config/role-defaults.yaml:2489, :2490, :2547, :2572, :2607, :2633, :2706, :2737, :2755, :2877` (8 Pipelines, 1 disabled); `.meta-config/project.yaml:339-343` (nur `se-cascade`); `README.md:479-489` (7 Zeilen, `concept-driven-dev` fehlt), `:501`, `:688`, `:689`, `:690`, `:695`, `:696`, `:734`; `hooks/**/*.sh` (17 Dateien, 11 deploybar); `commands/1-generic/*.md` (22); `tests/scenarios/asserts/{50,51,52,54,55,56}*.sh` mit **exakten** Zeilen `:32`, `:44`, `:26-27`, `:24-25`, `:31`; `tests/scenarios/run.sh:46-52`; `tests/scenarios/configs/{51,52,54}*.project.yaml`; `tests/scenarios/registry.md:97-110`; `scripts/lib/spec_plan_scaffold.py:20-24, :27-44, :46-68`; `scripts/lib/knowledge.py:103-114, :116-129, :131-132, :153-169`; `scripts/lib/generated_file_drift.py:35-37, :44, :51-67, :82-84, :240-310, :313-351, :344-349, :354-402, :379-386, :388, :405-425, :422-424, :591-596`; `scripts/lib/consistency/placeholders.py:128-131, :135-136, :148-183, :177-182`; `scripts/lib/sync_pipeline.py:587-620, :922-945, :929, :935, :1090-1099, :1102-1117, :1139`; `scripts/lib/cli_commands.py:72, :864, :888-900, :1139`; `scripts/lib/backup.py:376+`; `scripts/lib/deactivation.py:21, :303-353`; `config/project-config.schema.json:2058, :2073, :2425`; `ARCHITECTURE.md:3, :8-20`; `knowledge/wiki/index.md:24`; `knowledge/wiki/log.md:13-17, :30`; `docs/guides/project.yaml.example` (179 Z), `howto/configs/project.yaml.example` (340 Z), `docs/howto/admin-ui-remote-access.md`. **Neu bzw. korrigiert in Rev. 0.3:** `README.md:381-390` (F22 b — Überschrift + 6 Preset-Zeilen, `concept-driven` fehlt; `config/dod-presets.yaml:96`); `ARCHITECTURE.md:3` (F4, zweite Fundstelle) gegen `VERSION:1`; `hooks/1-generic/*.sh` (**11** Dateien, davon 2 `*-impl.sh` ⇒ **9**) gegen `scripts/lib/hooks.py:95-105` und `scripts/lib/external_tools.py:217-220`; `scripts/lib/spec_plan_scaffold.py:49-51` und `:62-68` für die Abschirmungskette in AC-38; `tests/scenarios/configs/51-spec-plan-disabled.project.yaml:1-34` (kein `docs-consolidation`-Key; `spec-plan-workflow.enabled: false` `:11-12`; `knowledge-engine.enabled: false` `:7-8`; `external-system-override.enabled: true` `:20-21`); `tests/scenarios/asserts/{50:32, 51:29-32, 52:41-44, 54:26-27}` direkt gelesen. `hooks/**/*.sh` = **17** Dateien bleibt eine **Belegzahl der Befund-Zeile F3** und ist **kein** `DOCS_*`-Faktum (NEW-1). **Nicht** verifizierbar und daher als HYPOTHESIS markiert: die exakte Zahl der `docs/**/*.md` (~190, §1) und die Zahl der Knowledge-Agenten im `AGENTS.md`-Bootstrap-Block (66, OQ3, aus dem Design übernommen). |
| **Coverage** | Jedes AC in §7 verweist auf mindestens eine IC; die Zuordnung AC → Welle → Datei → V-Check ist in §9.1 für alle **41** AC gefüllt. AC **ohne** V-Check sind in §9.1 je einzeln begründet; die Liste ist in Rev. 0.3 **vollständig** (NEW-6: Rev. 0.2 ließ AC-06, AC-22 und AC-38 weg) und umfasst **18** AC: **AC-01, AC-02, AC-03, AC-04, AC-06** (Fakten-Invarianten bzw. Key-Set, per Unit-Test in `tests/test_doc_facts.py`), **AC-18, AC-19, AC-22, AC-23, AC-24, AC-25, AC-26** (Determinismus, Drift-Store, Scaffold-Vertrag, Config-/Snippet-Bridge, per Unit-Test), **AC-34, AC-35, AC-37, AC-38, AC-39, AC-41** (Wiki-Restore, Allowlist, Szenario-Runner, Schema-Operation, Restore-Pfad). Die Begründungsklassen: Konfigurations-/Fakten-Invarianten; Determinismus-, Drift-Store-, Szenario- und Restore-Ebene — abgesichert per Unit-Test bzw. bestehendem Runner statt per Consistency-Check. |
| **Modularisierung** | Vier Module M1–M4, jeweils mit eigener Verantwortung, Dateiliste, Wellen, Vorgänger und Rollback (§4). Die Entscheidung „eine Datei" ist in §4 begründet; OQ7 ist als **geschlossen** mit Verweis auf die Planungsentscheidung geführt (§11.2). |
| **Review-Auflösung** | Rev. 0.2: Alle 16 Reviewer-Findings behoben (§17.1), drei Reviewer-Angaben als ungenau nachgewiesen und korrigiert (§17.2 CR-1…CR-6), drei weitere bestätigt (§17.3). **Rev. 0.3: Re-Review** (Concept-Reviewer-Re-Review vom 2026-09-26, CHANGES_REQUESTED, 0 kritisch / 2 major / 4 minor / 2 info) — **alle 8 Findings behoben** (§17.5) plus die **Gegenkorrektur** des Re-Reviewers zu §17.2 CR-1/CR-2. Der Re-Reviewer hat seinerseits **sechs** eigene Angaben (CR-1…CR-6) **zurückgezogen** und die Korrekturen aus Rev. 0.2 ausdrücklich **gestützt**; eine dieser Angaben (die Szenario-Zählung) wurde durch seine eigene Rücknahme **präzisiert**, nicht bestätigt (§17.2, CR-1). |
| **Ownership-Grenze** | Diese Spec-Revision hat **ausschließlich** `docs/specs/2026-09-25-repository-documentation-consolidation.md` geschrieben. Kein Code, keine Config, keine `agents/`-/`knowledge/`-/`tests/fixtures/`-Änderung, kein Commit, kein Push. Der parallele Track A (`tests/fixtures/slimming-golden/`) wurde weder gelesen als Spezifikationsquelle noch verändert. |
| **Rev. 0.4 — Abgrenzung** | Rev. 0.4 korrigiert die Branch-/PR-Normativität auf den ausgeführten Stand: §9.2 W0-Zeile, §9.2-Absatz „PR-/Branch-Strategie", R16-Mitigation sowie die Folgeverweise in §15, §16 und §17.6 (Volltext und Belege in §17.6); zusätzlich §9.2-Spalte „Parallel mit" auf den ausgeführten **sequenziellen** W4/W5/W6-Stand umgestellt und **A13**/**A14** in §13 registriert. **Unverändert:** AC-01…AC-41, IC-01…IC-24, NFA-01…NFA-11, R1…R20 (**R16 nur im Lösungsansatz**, nicht im Risiko-Inhalt und nicht in der W-Wahrscheinlichkeit „mittel"), F1…F25, M-1…M-13, NG-1…NG-11, FI-1…FI-10, OQ1…OQ9, W0…W8, §9.1, die §9.2-Welleninhalte und AC-Mengen, §3–§12 im Übrigen. **Keine** neue ID, **keine** neue Welle, **kein** neues Risiko, **keine** geänderte Architektur. **§13 umfasst 14 Abweichungen** — **A13** registriert die Branch-Namensabweichung (Design-W0 nennt `chore/docs-consolidation`, `docs/specs/2026-09-25-repository-documentation-consolidation-design.md:265`), **A14** die W4/W5/W6-Serialität und ist **offen** (§17.8). `status: APPROVED` besteht unverändert; Rev. 0.4 ist am **2026-09-26 durch den Nutzer bestätigt** (§17.7) — die zuvor im Dokument ausgerichtete Ausnahme ist entfallen. |
| **Ownership-Grenze (Rev. 0.4)** | Die Rev. 0.4 hat **ausschließlich** `docs/specs/2026-09-25-repository-documentation-consolidation.md` geschrieben. Design und die sechs W0-Records wurden **gelesen, nicht geändert**; die sechs W0-Records bleiben unverändert und führen OP-1 weiterhin offen — der formale Abschluss von OP-1 ist ein **Folgeschritt** (§17.6/§17.7). Der **Plan** `docs/plans/2026-09-25-repository-documentation-consolidation.md` wurde im selben Durchgang **nur in Ankern und Faktenangaben** geändert (K12, Revisions-Bump 0.3 → 0.4, berichtigte Zeilenzahlen, berichtigte OP-1-Aussage im Self-Review) — **kein** Task-, Wellen-, AC-, IC-, NFA- oder Gate-Inhalt. Kein Code, keine Config, kein Commit, kein Push, kein Branch-Wechsel, kein Merge/Rebase/Force. |
| **Rev. 0.5 — Abgrenzung** | Rev. 0.5 präzisiert die Gates des Plans (K13/K14) und schließt zwei Eigentümerlücken (K15 `report.py`, K16 Suppressionsregel 3); die zweite Korrekturrunde (RVW-1…RVW-15) schärft ausschließlich **innerhalb** des am **2026-09-26** beauftragten Korrekturumfangs nach. **Normativitätsaussage (RVW-5):** „keine neue normative Pflicht" ist **ersetzt** durch „keine Pflicht **jenseits** des beauftragten Umfangs" — **innerhalb** werden Nachweisformen geändert (§17.9.4, Tabelle (i)–(x)). **Unverändert:** AC-01…AC-41, IC-01…IC-24, NFA-01…NFA-11, R1…R20, F1…F25, M-1…M-13, NG-1…NG-11, FI-1…FI-10, OQ1…OQ9 (**OQ1 offen**), W0…W8, der **normative Pflichtumfang** im §10-Aufzählungspunkt `--validate`, die Exit-Code-Semantik des Runners, §9.1, die §9.2-Welleninhalte und AC-Mengen. **Keine** neue ID, **keine** neue Welle, **kein** neuer Task, **kein** neues Risiko, **kein** Revisions-Bump innerhalb Rev. 0.5, `status: APPROVED` und `approved: 2026-09-26` unverändert. **RVW-7:** der Verweis auf „R4 (Hochstufungsreihenfolge)" ist auf **§12.1 R4** korrigiert; R4 wird **nicht** um eine Reihenfolgeaussage erweitert (§12.1-R4-Zeile, §5.1.1-Abgrenzung). **RVW-4:** die K16-Bindung ist als **DAG-Kante** im **Plan** abgebildet, nicht in dieser Spec — die Spec führt sie als Ausführungs-Vorbedingung (§5.1.1). |
| **Ownership-Grenze (Rev. 0.5)** | Die Rev. 0.5 (beide Korrekturrunden) hat **ausschließlich** `docs/specs/2026-09-25-repository-documentation-consolidation.md` und `docs/plans/2026-09-25-repository-documentation-consolidation.md` geschrieben. **Kein** Produktionscode, **keine** Tests, **keine** generierten Agent-Dateien (`.claude/`, `.opencode/`, …), **keine** Submodule, **kein** `.gitignore`, **kein** `graphify-out/`. Kein Commit, kein Push, kein Branch-Wechsel, kein Worktree, kein Merge/Rebase/Squash/Force. **OQ1 bleibt offen**, **OQ2/OQ6/OQ8 bleiben geschlossen**, **OP-1 bleibt offen** (nur dessen formaler Abschluss ist offen), **A14 bleibt offen**. Alle B-1…B-5- und E-01…E-15-Zeilen sowie die Rev.-0.2/0.3/0.4-Blöcke stehen **unverändert**; K13–K17 sind additiv fortgeschrieben bzw. dort korrigiert, wo der Review es verlangt. |

---

## 17. Review-Auflösung und Ausführungskorrekturen (Rev. 0.2, Rev. 0.3, Rev. 0.4, Rev. 0.5)

### 17.1 Findings des Concept-Review — alle behoben

| Finding | Severity | Behebung in dieser Rev. | Verifikation |
|---|---|---|---|
| **K1** V1-Regex matcht die Befunde nicht | kritisch | §5.1.1: V1 Regel neu spezifiziert als **zwei disjunkte Branches** — V1a (Zahl + Whitelist-Nomen, ≤ 3 Token Abstand, **beide Richtungen**) und V1b (Semver-Literal + `version`). **Positiv-Fixture mit den 4 wörtlichen Zitatzeilen** und Negativ-Fixture mit 3 Suppressionsfällen + 1 Gegenprobe; AC-07/AC-08 ersetzt. Branch-Name ist Teil des Findings. | **bestätigt.** Alle vier Zeilen erneut gelesen: `README.md:122` (`## Agent Roster — 74 Generic Agents`), `:501` (`## Hooks (7 hooks, …)`), `:690` (`  ai-providers.yaml  # 6 provider configs (…`), `:734` (`VERSION  # Current version (v1.0.0)`). Keine davon matcht die alte Regex (Zahl steht nie am Zeilenanfang). |
| **K2** F19 ist eine falsche Korrektur | kritisch | F19 **gestrichen**, `DOCS_TIER_PRESET_COUNT == 5`, `README.md:689` in „korrekt, nicht zu ändern", §13-A7 korrigiert | **bestätigt.** `config/tier-presets.yaml` hat 5 Top-Level-Keys: `Cheap:1`, `Normal:31`, `Advanced:85`, `Expensive:115`, **`Expensive as Hell:145`**. |
| **K3** DoD-Presets sind 7 | kritisch | Neuer Befund **F22**, `DOCS_DOD_PRESET_COUNT == 7`, Absatz „korrekt" korrigiert, R4 neu begründet | **bestätigt.** `config/dod-presets.yaml:12` `presets:` mit 7 Einträgen: `:13`, `:30`, `:46`, `:62`, `:79`, `:96`, `:113`. |
| **K4** Pipelines: 8 / 7 aktiv, Tabelle unvollständig | kritisch | F14 auf drei Fehler erweitert (Zahl, fehlende Zeile, deaktivierte Zeile), `DOCS_PIPELINES_COUNT == 8`, `DOCS_PIPELINES_ACTIVE_COUNT == 7`, `DOCS_PIPELINES_BLOCK` auf „alle 8" erweitert | **bestätigt.** Alle 8 Pipeline-Keys gelesen; nur `se-cascade` ist `enabled: false` (`:2877`, überschrieben in `project.yaml:339-342`). `README.md:479-489` listet 7 Zeilen ohne `concept-driven-dev`. |
| **K5** Stage bricht bestehende Szenarien | kritisch | **Fail-off-Absenz-Default** (Präzedenz `knowledge.py:127`) für `enabled` **und** für alle V1–V9 (IC-05-Common-Gate); `knowledge-engine`-Schreibverbot; **Besitzregel** in IC-13; `index-mode: skeleton` als echter Hebel; **AC-38** als explizite Regressionsgarantie; NG-10 | **bestätigt, aber in der Zahl korrigiert** — siehe §17.2, CR-1. |
| **M1** Hook-Zählung widersprüchlich | mittel | IC-01-Auflösung: **zwei** Keys mit **getrennt benannten** Regeln **und je genau einer Zielstelle**. **Rev. 0.2-Stand:** `DOCS_HOOKS_COUNT == 11` (ohne `lib`, ohne `release-gates`, ohne `*_impl.sh`) für `README.md:501`, `DOCS_HOOK_SCRIPT_FILES_COUNT == 17` (keine Ausschlussregel) für `README.md:696`. **Rev. 0.3 (NEW-1):** der 17er-Key ist **gestrichen**, weil seine Zahl `hooks/**` zählt und damit an einer Zeile stand, die `hooks/1-generic/` nennt; neu `DOCS_HOOKS_1GENERIC_COUNT == 9` für `README.md:696`. Kreuz-Rendering ist verboten. | **bestätigt, in Rev. 0.3 korrigiert.** 17 `.sh` unter `hooks/**` = 2 `0-external/` + 11 top-level `1-generic/` + 1 `lib/hook_common.sh` + 3 `release-gates/` (Glob). Für `README.md:501` (global, „propagated to all providers"): 17 − 1 − 3 − 2 = **11**. Für `README.md:696` (Verzeichnis-Zeile): 11 top-level `1-generic/` − 2 `*-impl.sh` = **9**. Sammel-Nachweis der Layer-Regel: `hooks.py:95-98` (`0-external`), `:101-104` (`1-generic`), jeweils **nicht-rekursives** `*.sh`-Glob; `external_tools.py:217-220`. |
| **M2** Trace-Matrix inkonsistent | mittel | §9.1: AC-19 → **—** (Drift-Store, begründet), AC-18 → **—** (begründet), AC-29 → **V3**; AC-31 fest auf **W5**; Begründungsabsatz „V-Check-Spalte, korrigiert" ergänzt | **bestätigt** (sachfremde Mappings). |
| **M3** W8-Aktivitäten ohne AC | mittel | **AC-40** (neu) deckt die `llms.txt`-/`README.md`-Providerzahl ab; die **ID-Deklaration (OQ4)** ist über OQ4 mit Owner und Wellen-Blockade in §11.1 verankert und in §9.2 W8 als Inhalt geführt; **AC-30** deckt die README-Totverweise, **AC-39** (neu) die Schema-Operation aus R15, **M-12** die `PROJECT_STRUCTURE`-Korrektur. Jede W8-Aktivität in §9.2 hat damit mindestens ein AC **oder** eine verankerte OQ mit Blockade. | **bestätigt.** Rev. 0.1 führte AC-31 doppelt (W5 und W8) und nannte für W8 zwei Aktivitäten ohne AC. |
| **M4** Guide-Inventar unvollständig | mittel | F6 = **vier** Orte; neue Befunde **F23** (Guide-Sonderpfad) und **F24** (zwei Beispiel-Configs); Migrationen **M-6** (`docs/howto/` → `docs/guides/`) und **M-5** bleibt; SSoT-Entscheidung für beide Beispiel-Configs als **OQ9** (Inhaltsfrage, NG-1) mit Owner | **bestätigt.** `docs/howto/admin-ui-remote-access.md` existiert (Glob, 1 Datei); `docs/guides/project.yaml.example` = **179** Zeilen, `howto/configs/project.yaml.example` = **340** Zeilen (Endzeilen gelesen). |
| **M5** AC-29 zirkulär | mittel | §13-**A12** neu: die Stale-Deklaration **wandert mit** der Langfassung (M-7), IC-03 liest `docs/architecture/00-overview-full.md`, AC-29 prüft beide Seiten getrennt | **bestätigt — und in der Diagnose geschärft.** Die Deklaration in `ARCHITECTURE.md:3` betrifft nicht die Stub-Aussage selbst; `knowledge/wiki/index.md:24` beschreibt `concepts/architecture.md` als „Rohkopie von **ARCHITECTURE.full.md**". |
| **M6** AC-35 übererfüllt | mittel | **IC-24** `restore_wiki_index()` mit Pfad, Reihenfolge und fail-closed; **AC-41** neu; AC-35 auf „Backup existiert" zurückgenommen; NFA-06 aktualisiert | **bestätigt.** `sync.py --backup`/`--restore` (`cli_commands.py:864`, `:888-900`) sind über `backup.py:376+` Provider-Verzeichnis-Zip-Operationen (`deactivation.py:21`, `:303-353`) und können `knowledge/wiki/index.md` nicht wiederherstellen. |
| **M7** R1 nur für Hybrid-Dateien | mittel | R1 erweitert; §3.2 volatile-Zeile auf `docs/INDEX.md` konkretisiert; IC-10 (e) volatile-Sektion am Dateiende; IC-14 schließt volatile aus dem `facts-hash` aus; AC-03 erweitert | **bestätigt.** |
| **M8** `#`-Key als HYPOTHESIS | mittel | **Analysiert statt vermutet:** IC-16-M8-Tabelle listet alle fünf Consumer des Hash-Stores mit Code-Belegen. Verbindliche Regel: Allowlist-Match auf den **Basis-Pfad**; NFA-05 wird zwingend, weil kein Backup entsteht. AC-37 prüft es. | **bestätigt und präzisiert.** `is_allowlisted` = `any(fnmatch.fnmatch(rel_path, p) …)`, `generated_file_drift.py:82-84` — ein Muster `README.md` matcht `README.md#docs:facts` **nicht**. `backup_drifted_files` liest `project_root / finding["path"]` (`:379`) und überspringt fail-soft (`:381-386`). |
| **N1** Selbstwidersprüche | niedrig | Revisionstabelle nennt **AC-01…AC-41**; §15/§16 nennen **OQ1…OQ9** mit OQ5/OQ7 geschlossen. **Rev. 0.3:** die damalige Teilbehauptung „AC-02 sagt „zwölf" und listet zwölf" ist **überholt** — AC-02 ist jetzt rein formelbasiert und enthält **keine** Zahlenliste (NEW-8); die Sollwert-Zahl steht ausschließlich in IC-23 und lautet **elf** (NEW-4) | **bestätigt, in Rev. 0.3 überholt.** |
| **N2** `knowledge-indexer`-Kollision | niedrig | IC-21 trägt jetzt einen eigenen **Kollisionsvermerk** mit verbindlicher Reihenfolge (W7 erst nach Rollenpflege-Merge, IC-21 als letzter Commit); NFA-08 nennt es als **einzige** Ausnahme; **R19** | **bestätigt** (Lag nur im NFA-08-Klammersatz). |
| **N3** OQ5 / OQ7 faktisch entschieden | niedrig | **§11.2** führt beide als **geschlossen** mit Begründung; OQ7 zusätzlich in §4 und §15 | **bestätigt.** |

### 17.2 Korrigierte Reviewer-Angaben (mit Beleg)

> **Rev. 0.3 — Gegenkorrektur des Re-Reviewers zu CR-1/CR-2 (verbindlich).** Der Re-Reviewer
> hat CR-1…CR-6 **zurückgezogen** und die Korrekturen aus Rev. 0.2 **gestützt** — mit **einer**
> Präzisierung: die Formulierung „**3 harte Fehlschläge**" beschreibt die **naive** Variante
> (Generator ohne Abschirmung), **nicht** die spezifizierte. Verbindlich gilt:
> **0 Szenarien brechen unter der in dieser Spec festgelegten Abschirmung** (Fail-off-
> Absenz-Default `docs-consolidation.enabled = false`, IC-13 Zeile 1 / IC-22; KE-Schreibverbot,
> IC-13 Zeile 2; **kein** `mkdir` in Consumer ohne `docs/`, IC-13 letzte Zeile) — so behauptet
> AC-38 zu Recht. **3** ist die Anzahl der Szenarien, die in der **naiven** Variante
> brechen würden, und steht hier **ausschließlich als Begründung der Abschirmung** — es ist
> **kein Arbeitsauftrag**: NG-10 verbietet jede Änderung an `tests/scenarios/`, also darf der
> Planer insbesondere **keine** der drei Zeilen „reparieren".

| # | Reviewer-Angabe | Korrektur | Beleg |
|---|---|---|---|
| **CR-1** | „**6** bestehende Szenarien brechen", darunter `asserts/50:32` und `asserts/56:31` | **0 brechen** unter der spezifizierten Abschirmung; **3** in der naiven Variante. `asserts/50:32` und `asserts/56:31` prüfen nur `[ -f "docs/INDEX.md" ]` — **Existenz**, und die Datei existiert nach dem Scaffold weiter, also bleiben sie **grün**. Ebenso `asserts/54:26` und `asserts/55:24` (Existenz). `asserts/51:32` (`[ ! -e "docs/INDEX.md" ]`) bleibt grün, weil die Fixture **keinen** `docs-consolidation`-Key trägt ⇒ Absenz-Default `enabled = false` ⇒ der Generator führt **keinen** Schreibzugriff aus (IC-13 Zeile 1 / IC-22). `spec-plan-workflow.enabled: false` ist dafür **nicht** die Begründung, sondern betrifft nur den Scaffold (anderer Writer). | `asserts/50:32` `[ -f "docs/INDEX.md" ]`; `asserts/56:31` `[ -f "docs/INDEX.md" ]`; `asserts/51:29-32` prüft `docs/specs|plans|spikes` **nicht** existent, dann `:32 [ ! -e "docs/INDEX.md" ]`; `configs/51-spec-plan-disabled.project.yaml:1-34` (kein `docs-consolidation`-Key), `:11-12` `spec-plan-workflow.enabled: false`, `:7-8` `knowledge-engine.enabled: false`, `:20-21` `external-system-override.enabled: true`; `spec_plan_scaffold.py:49-51` → `log.skip` vor jedem `mkdir` |
| **CR-2** | **Harte** Fehlschläge: `54:27`, `55:25`, `51:32`, `52:44` | In der **naiven** Variante wären es `54:27` (grep `File-based index fallback`), `55:25` (grep dito) und `52:44` (`[ ! -e docs/INDEX.md ]` — KE autoritativ). `51:32` bricht auch naiv **nicht** (s. CR-1). Unter Abschirmung: **0**. Der Spec-Text des Reviews nennt für 56 „Inhaltsprüfung (`:31`)" — `:31` ist jedoch `[ -f ]`, eine reine Existenzprüfung. | `asserts/54:26-27` (`[ -f ]` + `grep -q 'File-based index fallback'`); `asserts/55:24-25` dito; `asserts/52:41-44` Kommentar „no file-index fallback is written" + `[ ! -e "docs/INDEX.md" ]`; `asserts/56:31` `[ -f "docs/INDEX.md" ]` |
| **CR-3** | R18: „Interaktion `_sync_stage_auto_commit_allowlist` mit `auto-commit-allowlist.json` nicht analysiert" | **Nicht zutreffend.** Die Stage liest den Drift-Store nicht; sie schreibt eine **generierte** Ausgabe aus `config` + `active_roles`. Außerdem existiert `.meta-config/auto-commit-allowlist.json` im Repo **nicht** (Glob: 0 Treffer) — es ist ein Sync-Output, kein Input. Risiko als **analysiert und nicht zutreffend** geführt, mit Beleg in IC-16 und R18. | `sync_pipeline.py:1102-1117` (`resolve_auto_commit_config(config, active_roles, agent_meta_root)`, `write_atomic(allowlist_path, …)`); `.meta-config/` hat keine `auto-commit-allowlist.json`; `auto_commit.py:49` beschreibt es als **geschrieben** |
| **CR-4** | R15 impliziert: ohne Schema-Update „geht gar nichts" | **Falsch.** Das Wurzel-Schema ist `additionalProperties: true` (`:2425`) — die 6 Keys brechen die Validierung nicht. Was fehlt, ist Autocomplete und der Tippfehler-Wächter, den das Repo selbst ausdrücklich nutzt. M-11 ist **Konventions-Pflicht**, keine Fehlerbehebung. | `config/project-config.schema.json:2425` `"additionalProperties": true`; Selbstauskunft in `:2058` („Required because spec-plan-workflow is a closed object; additionalProperties:false additionally turns it into a strict typo guard") und `:2073` |
| **CR-5** | M8: Allowlist-/Auto-Commit-Pfad „nicht geprüft" → Key-Design ändern | Nach Prüfung: **kein** Key-Design-Wechsel nötig. `_load_hashes`/`_save_hashes` sind key-agnostisch (`:51-67`); das einzige echte Problem ist der `fnmatch`-Match auf den Gesamtstring (`:82-84`), gelöst durch die Basis-Pfad-Regel. | wie oben |
| **CR-6** | Design/Rev. 0.1: Szenario `63-docs-facts-drift.md` | Nummer **63 ist vergeben** an `63-context-file-modes`. Korrekt: **64**. | `tests/scenarios/registry.md:110`; `asserts/63-context-file-modes.sh`; `configs/63-context-file-modes.project.yaml` |

### 17.3 Geprüfte und **bestätigte** Reviewer-Angaben (DEVIATION_REVIEW A1–A11)

> **Geltungsbereich:** Diese Prüftabelle deckt den **Rev.-0.2-Stand** ab und umfasst die
> §13-Abweichungen **A1…A12**. Die in **Rev. 0.4** hinzugekommenen **A13** und **A14** sind hier
> **nicht** Gegenstand — zu A13 siehe §13/A13 und §17.6, zu A14 siehe §13/A14 und **§17.8**.

| # | Urteil nach eigener Prüfung | Beleg |
|---|---|---|
| **A1** | **trägt** — Design-F Aussage war falsch, die Korrektur ist berechtigt | `project.yaml:148` `se-component-requirements` in `roles:`; `:12-13` `systems-engineering.enabled: false`; `agents/1-generic/se-component-requirements.md` existiert; `agent_sync.py:544-548` `log.skip(rel, "systems-engineering is disabled")` |
| **A2** | **trägt** | `roles:` 59 Einträge (`:92-150`); `role-defaults.yaml:1` 84 Rollen (2-Space-Keys bis `:2403`); Gate-bewusste Vergleichsmenge ist korrekt |
| **A3** | **trägt** | `placeholders.py:128-131` `_DYNAMIC_PREFIXES` (2 Einträge, **kein** `DOCS_`); `:177-182` `Severity.WARNING` |
| **A4** | **trägt inhaltlich, war unvollständig** | `spec_plan_scaffold.py:62-68` schreibt nur bei `mode == "file-index"`; die Regel für `mode == "knowledge-engine"` fehlte → in IC-13 (Zeile „`resolve_index_mode() == knowledge-engine`") und IC-15 ergänzt |
| **A5** | **trägt** | `tests/scenarios/asserts/*.sh` = **63** (gezählt); `tests/scenarios/*.md` enthält nur `registry.md` |
| **A6** | **trägt (Zahlen), Regel war widersprüchlich — Präzisierung in Rev. 0.3 (NEW-1)** | 17 `.sh` unter `hooks/**`, 13 nach `lib/`+`release-gates/`-Ausschluss; IC-01 führte zusätzlich die Suffix-Regel (rev. 0.3: korrekt `-impl.sh`, s. NF-12) → M1 aufgelöst. **Neu:** die 17 sind eine **Belegzahl der F3-Zeile**, kein Faktum; für `README.md:696` gilt der Verzeichnis-Wert **9** (`hooks/1-generic/*.sh` minus 2 `*-impl.sh`) |
| **A7** | **trägt nicht** (F19 falsch) | siehe K2; §13-A7 in Rev. 0.2 korrigiert |
| **A8** | **Begründung trägt, Annahme war ungeprüft** | `generated_file_drift.py:51-67, :82-84, :344-349, :354-402, :405-425` vollständig gelesen; Ergebnis in IC-16 (M8-Tabelle) spezifiziert |
| **A9** | **trägt** | Repo-Konvention `spec-id` pro Datei; Aufteilung als Planungsentscheidung korrekt eskaliert (jetzt OQ7 geschlossen) |
| **A10** | **trägt inhaltlich, Default-Formulierung war der K5-Fehler** | Präzedenz `knowledge.py:127-129` existiert, aber genau deren Fail-**off**-Muster widerspricht „Schema-Default = Default agent-meta" → in IC-22 aufgelöst |
| **A11** | **trägt** | konsistent mit IC-05 (Start WARNING in W2, ERROR ab W3) |

### 17.4 Eigene neue Befunde bei der Überarbeitung (über den Review hinaus)

| # | Befund | Behandlung |
|---|---|---|
| **NF-1** | Das Design (und Rev. 0.1) reserviert Szenario-Nummer **63** für `63-docs-facts-drift` — die ist im Repo bereits belegt | Umbenannt auf **64** (§2.3, §10) |
| **NF-2** | Die Rev.-0.1-Aussage „`README.md:479-489` Pipeline-Tabelle … die *Zahl* 7 stimmt" ist **falsch**; zugleich war die Zahl 7 in `§1.2` als „korrkt" geführt | Korrigiert in F14 und §1.2 |
| **NF-3** | Die Rev.-0.1-Liste „Korrekt und daher nicht zu ändern" enthielt **drei** Einträge, von denen **zwei falsch** waren (`README.md:688` DoD, `README.md:479-489` Pipelines) | Liste auf zwei verifiziert korrekte Zeilen reduziert, beide mit Beleg |
| **NF-4** | ~~Das Design zitiert `README.md:381` als Beleg für die korrekte DoD-Zahl; die Zeile existiert dort nicht (korrekt ist `:688`)~~ — **WIDERLEGT in Rev. 0.3 (NEW-2).** `README.md:381` **existiert**: „## DoD Presets (6 presets)" mit einer 6-zeiligen Tabelle (`:383-390`), der `concept-driven` fehlt. Die Rev.-0.2-Aussage war selbst ein Fehlbefund. | **Als widerlegt markiert und korrigiert:** `README.md:381` ist die **zweite** F22-Fundstelle (Zahl **und** fehlende Zeile) und wird in F22, §3.2 (SSoT-Zielstelle) und §1 mitgezählt. `README.md:688` bleibt die Fundstelle für den Datei-Kommentar. Beleg: `README.md:381-390`; `config/dod-presets.yaml:96` (`concept-driven`) |
| **NF-5** | `DOCS_SCENARIO_COUNT` (63) war in AC-02 gelistet, gehört aber zu den volatilen Fakten und war in der Rev.-0.1-AC-02-Liste die einzige Zahl **ohne** zugehörigen Wert im selben Satz (Aufzählung endete bei `DOCS_SCENARIO_COUNT == 63` ohne Erklärung) | AC-02 auf die **nicht-volatilen** Skalar-Fakten umgestellt; `DOCS_SCENARIO_COUNT` in AC-03 verschoben, wo die Volatilität geprüft wird. **Rev. 0.3:** der in Rev. 0.2 daraus folgende Zahlen-Snapshot (zwölf konkrete Werte als `xfail`) ist **gestrichen** (NEW-8) — AC-02 ist rein **formelbasiert** und damit durchsetzbar; die konkreten Sollzahlen stehen ausschließlich in IC-23 und werden von AC-36 geprüft |
| **NF-6** | Rev. 0.1 zählte in §1.1 „manuell gepflegte Zahlen: 9" und in §1.2 „5 Architektur / 3 Guides" — beides nach Korrektur falsch | §1.2 auf **4** Guides korrigiert; die **Zahlen**-Angabe in Rev. 0.2 war selbst falsch und ist in Rev. 0.3 durch **NF-9** ersetzt |
| **NF-7** | `docs/architecture/` enthält **8** Dateien (`:01-07` + `prompt-modernization.md`), `docs/api/` **7** — beides in §3.2 als Fakt behauptet, aber nirgends belegt | als F5-Beleg belassen (Zeilenangabe `ARCHITECTURE.md:8-20` verweist auf alle), in §16 unter „nicht verifizierbar" nicht aufgeführt, weil über die Diagramm-Tabelle gedeckt |
| **NF-8** | Der parallele Track A committet in `tests/fixtures/`; die von AC-07/AC-08 geforderte Fixture liegt im **selben** Verzeichnis | Als Ownership-Konflikt in §2.3, R3 und R15 geführt; Reihenfolge festgelegt (Fixture erst nach Track-A-Merge) |
| **NF-9** | **Rev. 0.3 (neu):** die Rev.-0.2-Angabe „**10** Stück (F1, F2, F3 ×2, F4, F14 ×3, F22) plus 2 in `llms.txt`" war **doppelt falsch**: die Aufzählung summiert **9** (1+1+2+1+3+1), und `llms.txt` enthält **keine** manuell gepflegte Zahl — `:5` ist Prosa („Claude Code, Gemini/Antigravity, Opencode, Continue, GitHub Copilot, Mammouth Code", 6 von 9 Providernamen). Zusätzlich war `ARCHITECTURE.md:3` als falsche Version **nicht** mitgezählt, obwohl die Zeile der Messzeile in §1/§1.2 (`README.md` / `llms.txt` / `ARCHITECTURE.md`) untersteht | Nachgerechnet und **jede Stelle am Repo belegt**: **11** = 10 in `README.md` (F1 `:122`; F2 `:690`; F3 ×2 `:501`/`:696`; F4 `:734`; F14 ×3; F22 ×2 `:688`/`:381`) + 1 in `ARCHITECTURE.md:3` (F4, zweite Fundstelle, `0.92.0` vs. `VERSION:1` = `1.2.0-beta.2`). `llms.txt:5` als **inhaltliche** Lücke (F2-Analogon, fehlende Providernamen) über **AC-40** adressiert, aber nicht als Zahl gezählt. Korrigiert in §1, §1.1 (F4), §1.2 |
| **NF-10** | **Rev. 0.3 (neu):** die Sollwert-Zahl war uneinheitlich — §1.2 sagte „11", IC-23-Text, AC-36, NFA-11 und R14 sagten „zwölf"/„12", und die Yaml-Datei in IC-23 enthält **11** Einträge | Einheitlich **elf** an allen fünf Stellen; die Yaml-Datei in IC-23 ist der **einzige** Ort mit Sollzahlen. Grund: zwei Orte für dieselbe Zahl sind genau die Fehlerklasse F19/F22 (R14) |
| **NF-11** | **Rev. 0.3 (neu):** die Rev.-0.2-Aussage in NF-4, `README.md:381` existiere nicht, war ein **Fehlbefund** der Spec selbst (siehe oben) | Als **widerlegt** markiert; `README.md:381-390` ist die zweite F22-Fundstelle und wird in F22, §3.2, §1/§1.2 mitgezählt. Lehrpunkt für die Planung: eine Aussage über eine **Nicht-Existenz** braucht denselben Beleg wie eine Existenz-Aussage — hier hätte ein `Read` von `README.md:381` genügt |
| **NF-12** | **Rev. 0.3 (neu, außerhalb der 8 Findings, aber im selben Codepfad wie NEW-1):** IC-01 spezifizierte `HOOK_EXCLUDED_SUFFIXES: tuple[str, ...] = ("_impl.sh",)` — mit **Unterstrich**. Die Dateien heißen `orchestrator-guard-impl.sh` und `repo-containment-impl.sh` (**Bindestrich**, per Glob verifiziert). Die Regel hätte damit **nichts** gematcht und `DOCS_HOOKS_COUNT` liefe auf **13** statt 11 — die eigene Zahl der Spec wäre nicht reproduzierbar, also genau die Fehlerklasse, die V1/IC-23 verhindern sollen | Korrigiert auf `("-impl.sh",)`; die drei Prosa-Stellen (`§3.2`, IC-01-Auflösungstabelle, §17.1-M1) auf `*-impl.sh` vereinheitlicht; Warnkommentar im Code-Block gesetzt |

### 17.5 Re-Review (Rev. 0.3) — Findings NEW-1…NEW-8

Eingang: Re-Review der Rolle `concept-reviewer` vom 2026-09-26 (Session-Artefakt, nicht
committet; der vollständige Findings-Abgleich steht in dieser Tabelle)
(CHANGES_REQUESTED; 0 kritisch / 2 major / 4 minor / 2 info; `RESIDUAL_BLOCKERS: Keine`;
`PLAN_READINESS: Ja`). Der Re-Reviewer bestätigt ausdrücklich die 16 Vorreview-Findings sowie
R14–R18, das Threat Model, OQ8 und die OQ6-Reihenfolge als behoben und zieht seine **eigenen**
sechs Angaben CR-1…CR-6 **zurück**.

| Finding | Sev | Behebung in Rev. 0.3 | Verifikation (jede Stelle am Repo gelesen) |
|---|---|---|---|
| **NEW-1** `DOCS_HOOK_SCRIPT_FILES_COUNT == 17` an `README.md:696` | major | Faktor **gestrichen**; neu `DOCS_HOOKS_1GENERIC_COUNT == 9`, exklusiv für `README.md:696`, mit verbindlicher Renderform inkl. Klammerzuschlag „(+2 `*-impl.sh` helpers)". `DOCS_HOOKS_COUNT == 11` bleibt exklusiv für `README.md:501`. 17 bleibt **Belegzahl** in F3/§16 | `README.md:696` nennt `hooks/1-generic/`; 11 top-level `.sh` dort (Glob), davon 2 `*-impl.sh` ⇒ **9**. `README.md:501` ist die Hooks-**Überschrift** (globale Aussage) ⇒ 17 − 1 `lib/` − 3 `release-gates/` − 2 `*-impl.sh` = **11**. Layer-Regel: `hooks.py:95-98`, `:101-104` (nicht-rekursiv); `external_tools.py:217-220`; `consistency/repo_containment.py:22` („hook wrapper/impl"). **Abweichung vom Reviewer-Vorschlag** (er nannte 11): dokumentiert in §5.1 IC-01 — 11 ist die **Datei**zahl, die Zeile sagt „hook scripts", und die Spec stuft `*-impl.sh` bereits in `DOCS_HOOKS_COUNT` als Nicht-Hooks ein |
| **NEW-2** F22 erfasst nur `README.md:688`; `README.md:381` ist eine zweite Falschzahl; NF-4 widerlegt | major | F22 auf **zwei** Fundstellen erweitert; §3.2-SSoT-Zielstelle auf `README.md:381-390` erweitert; NF-4 als **widerlegt** markiert; Zählung in §1/§1.2 um +1 | `README.md:381` „## DoD Presets (6 presets)", Tabelle `:383-390` mit 6 Zeilen (`full`, `standard`, `rapid-prototyping`, `spec-optional`, `spec-driven`, `spec-certified`); `config/dod-presets.yaml` hat **7** (`:13, :30, :46, :62, :79, :96, :113`) — `concept-driven:96` fehlt in der Tabelle, dieselbe Fehlerklasse wie F14 |
| **NEW-3** §1.2 nennt 10, die Aufzählung ergibt 9 | minor | Neu gerechnet: **11** = 10 (`README.md`) + 1 (`ARCHITECTURE.md:3`); `llms.txt` als Prosa ohne Zahl eingestuft. Beleg und Korrektur in §1, §1.2 und **NF-9** | Aufzählung Rev. 0.2: 1+1+2+1+3+1 = 9 ≠ 10. `ARCHITECTURE.md:3` „Repo version: **0.92.0**" vs. `VERSION:1` = `1.2.0-beta.2`; `llms.txt:5` enthält keine Ziffer |
| **NEW-4** §1.2 sagt 11, IC-23/AC-36/NFA-11/R14 sagen zwölf | minor | Einheitlich **elf** an allen fünf Stellen; Schlüsselzahl-Begründung in IC-23 ergänzt (**NF-10**) | `config/doc-facts-expected.yaml` (IC-23-Block) hat genau **11** Einträge, gezählt |
| **NEW-5** §9.2 nennt W1: 9 / W3: 13, §9.1 nennt 10 / 14 | minor | §9.2 auf **W1: 10, W3: 14** korrigiert, **Nachzählung** beider Wellen als Formel in den Text aufgenommen (AC-39 bzw. AC-38 waren nicht mitgezählt) | W1 = AC-01…AC-06 (6) + AC-23…AC-25 (3) + AC-39 (1) = 10; W3 = AC-12 (1) + AC-14…AC-22 (9) + AC-26 (1) + AC-27 (1) + AC-37 (1) + AC-38 (1) = 14; alle übrigen Wellen unverändert (W2 7, W4 2, W5 2, W6 2, W7 4, W8 2) |
| **NEW-6** §16-Liste der AC ohne V-Check unvollständig | minor | Liste **vollständig** auf **18** AC gebracht, nach Begründungsklassen gruppiert | §9.1 V-Check-Spalte durchgezählt: `—` bei AC-01, AC-02, AC-03, AC-04, AC-06, AC-18, AC-19, AC-22, AC-23, AC-24, AC-25, AC-26, AC-34, AC-35, AC-37, AC-38, AC-39, AC-41 = **18**; Rev. 0.2 nannte 15 (AC-06, AC-22, AC-38 fehlten) |
| **NEW-7** AC-38s Begründung für `51:32` nennt den Scaffold-Gate | info | Umgestellt auf den **Absenz-Default** (`docs-consolidation.enabled` bei Abwesenheit `false` ⇒ `log.skip`, **kein** Schreibzugriff) als tragende Begründung; Scaffold-Abschirmung als **nachrangige** Rückfallebene markiert. Zusatz: die AC referenziert **IC-13/IC-15/IC-22** — ein von der Reviewer-Notiz genanntes „IC-26" existiert in dieser Spec nicht (§16: IC-01…IC-24 lückenlos) | `configs/51-spec-plan-disabled.project.yaml:1-34` enthält **keinen** `docs-consolidation`-Key; `:11-12` `spec-plan-workflow.enabled: false` (betrifft nur den Scaffold), `:7-8` `knowledge-engine.enabled: false`, `:20-21` `external-system-override.enabled: true`; `asserts/51:29-32`; `spec_plan_scaffold.py:49-51` (`log.skip` vor jedem `mkdir`), `:62-68` (Skeleton nur bei `mode == "file-index"`), `:40-44` (`resolve_index_mode`); `IC-13`-Zeilen 1/3 und letzte Zeile |
| **NEW-8** AC-02-Snapshot ist `xfail` und damit nicht durchsetzbar | info | Snapshot **gestrichen**; AC-02 ist jetzt **rein formelbasiert** und durchsetzbar (**13** Formel-Assertions über eine Fixture-Konfiguration). Die Durchsetzung
 der konkreten Sollzahlen liegt **eindeutig** bei IC-23/AC-36; die Entscheidung ist im AC als „bewusste Entscheidung" begründet | `xfail` markiert einen **erwarteten** Fehlschlag: ein fehlerhafter Formel-Faktor wäre darin **invisible**; doppelte Zahlenhaltung (Test + `doc-facts-expected.yaml`) wäre ein zweiter Sollwert-Ort (R14) |
| **Gegenkorrektur** §17.2 „3 harte Fehlschläge" | info | §17.2 sagt jetzt **0 nach Abschirmung, 3 in der naiven Variante** — mit explizitem Hinweis, dass die 3 **kein Arbeitsauftrag** sind (NG-10 verbietet jede Änderung an `tests/scenarios/`) | Absenz-Default `false` (IC-22) ⇒ alle sechs Fixtures ohne `docs-consolidation`-Key ⇒ Generator inaktiv (IC-13 Zeile 1). `asserts/50:32` und `asserts/56:31` sind reine `[ -f ]`-Existenzprüfungen; `asserts/54:26-27` und `asserts/55:24-25` erwarten den Scaffold-Inhalt `File-based index fallback` (Skeleton bleibt unangetastet, IC-15); `asserts/52:41-44` verlangt `knowledge/wiki/index.md` **und** **kein** `docs/INDEX.md` (KE autoritativ). Naive Variante ohne Abschirmung: genau 3 Zeilen wären betroffen |

### 17.6 Rev. 0.4 — Ausführungskorrektur der Branch-/PR-Strategie (offener Punkt **OP-1**)

**Charakter dieser Revision.** Rev. 0.4 ist **keine** Inhalts- oder Design-Erweiterung, sondern die
Korrektur eines **Normativitätswiderspruchs**: Rev. 0.1–0.3 forderten an **drei** Stellen (OP1-1…OP1-3,
siehe Tabelle unten) die Strategie „ein **Branch pro Welle** (`chore/docs-consolidation-w<N>`),
gestapelte PRs" — in der W0-Zeile von §9.2, im §9.2-Absatz „PR-/Branch-Kollision" (dort wörtlich mit
dem Präfix „**Verbindlich**") und in der Mitigation von R16 (§12.2) —,
während die Ausführung einen Wellen-Branch mit einem PR verwendet hat. Da dieses Dokument sich zur
**normativen Quelle** erklärt (Kopfzeile „stillschweigende Abweichungen gibt es nicht"; §2.2 „hart
— Abweichung gilt als Spec-Verstoß"), wäre der unveränderte Stand eine Verletzung der eigenen Norm.
Korrektur deshalb **hier**, nicht in den Records.

**Betroffene Stellen (vollständig, alle geändert am 2026-09-26):**

| # | Stelle | Vorher (Rev. 0.1–0.3) | Nachher (Rev. 0.4) |
|---|---|---|---|
| **OP1-1** | §9.2, **W0-Zeile** (Spalte „Inhalt") | „Design-Freeze, Contract-Liste, **ein Branch pro Welle** (`chore/docs-consolidation-w<N>`), Entscheidungs-Records …" | „… **ein Wellen-Branch für das gesamte Vorhaben** (`feat/repository-documentation-consolidation-main`, Basis `origin/main`) mit **einem** PR gegen `main`; Wellen-Zuordnung über die **Wellenkennung im Commit-Titel**." Ausdrücklicher Rev.-0.4-/OP-1-Vermerk mit Verweis auf den Absatz „PR-/Branch-Strategie" und auf §17.6 |
| **OP1-2** | §9.2, Absatz „PR-/Branch-Kollision" (Rev. 0.1–0.3) | „**Verbindlich:** ein Branch **pro Welle** (`chore/docs-consolidation-w<N>`, in §9.2 Spalte W0 verankert), gestapelte PRs in Reihenfolge W1→W8, `git mv`-Wellen (W4/W5/W6) werden **zuerst** gemergt, weil …" | Neu gefasst als „**PR-/Branch-Strategie** (R16, rev. 0.2; rev. 0.4 …)" mit fünf verbindlichen Punkten: (1) Ein Branch / ein PR, `chore/docs-consolidation-w<N>` **aufgehoben**; (2) Wellen-Zuordnung über Commit-Titel `docs(docs-consolidation): W<N> <Zweck>`, Abschluss-Commit `… W<N> complete`, `W<N>`-Präfix verbindlich für Abschluss- und wellen-koordinierende Titel, **optional** für Datei-Commits (dort Task-ID `Task: W<N>-<k>` im Body), ein Commit pro Datei; (3) Merge-Regel: `git mv`-Wellen W4/W5/W6 **zuerst**, Wellen sequenziell W1→W8, Rebase gegen `origin/main` vor dem PR-Merge; (4) dokumentierter Bestand des überholten Vor-Branches, Post-Merge-Cleanup = eigene Entscheidung; (5) Ausführungsnachweis + Nicht-Design-Abweichung |
| **OP1-3** | §12.2, **R16** (Spalte „Mitigation") | „Ein Branch **pro Welle** (`chore/docs-consolidation-w<N>`, §9.2 W0), gestapelte PRs in Reihenfolge, `git mv`-Wellen **zuerst** mergen, ein Commit pro Datei" | Rev.-0.4-Vermerk: Branch-Anzahl ist **nicht** der Lösungsansatz; fünf Teile Reihenfolge-/Merge-Regel (identisch zu OP1-2, kurz), Verweise auf §9.2 und §17.6. **Risiko-Text und Wahrscheinlichkeit „mittel" unverändert** |
| **OP1-4** | §15, Trace-Anker | ohne Rev.-0.4-Eintrag | Rev.-0.4-Anker ergänzt (Ausführungsbelege, geänderte/unveränderte Stellen, „kein neuer `spec-id`, keine Supersession") |
| **OP1-5** | §16, Selbstreview-Tabelle | 8 Datenzeilen (im Stand `35bb176f` gemessen) | 2 Zeilen ergänzt: „**Rev. 0.4 — Abgrenzung**" und „**Ownership-Grenze (Rev. 0.4)**" ⇒ **10** Datenzeilen; der Kopf der Tabelle trägt weiterhin den Rev.-0.3-Stand (historischer Stand, wie in §11.1/§16 für OQ2/OQ6/OQ8 bereits vermerkt) |
| **OP1-6** | §17 | 17.1–17.5 | 17.6 als vollständiger Korrektur- und Beleg-Abschnitt (dieser Abschnitt) |
| **OP1-7** | Kopfblock, Frontmatter, Revisions-Tabelle, Freigabevermerk | `revision: 0.3`; Revisionshistorie „endet bei Rev. 0.3"; Revisions-Tabelle ohne 0.4 | `revision: 0.4`; Rev.-0.4-Änderungsblock im Kopf; Revisionszeile **0.4** mit Begründung. **Freigabevermerk (Stand nach der Korrektur):** Rev. 0.4 ist am **2026-09-26 durch den Nutzer bestätigt** (Entscheidungsweg laut Plan Rev. 0.4, K1); die zunächst im Dokument ausgerichtete Ausnahme („Inhaltsrevision, aber **keine** erneute Freigabe") ist **entfallen** — Auflösung und Wortlaut in **§17.7**. Frontmatter: `status: APPROVED`, `approved: 2026-09-26`, `approved-scope: …`, `revision: 0.4` |
| **OP1-8** | §13, Abweitungstabelle | A1…A12, Zählung „12 Abweichungen" | **A13** (Branch-Namensabweichung gegen Design:265) und **A14** (W4/W5/W6 seriell statt paarweise parallel, **offen**) ergänzt; Zählung auf **14** angehoben; alle Stellen, die „12 Abweichungen" nannten, nachgezogen (Kopfblock, Revisionszeile 0.4, §9.2 Punkt 5, §15, §16). **Keine** Design-Änderung — das Design bleibt unverändert |

**Unverändert geblieben (ausdrücklich geprüft, kein Widerspruch):**

- **§2.3** (Track A) und **R3**: „pro Welle ein Commit pro Datei; vor jedem Merge Rebase gegen den
  Track-A-Branch" bzw. „Rebase vor jedem Merge". Beide Formulierungen sind **wortgleich aus dem
  Design** übernommen (`docs/specs/2026-09-25-repository-documentation-consolidation-design.md:275`
  bzw. `:368`) und **branch-anzahl-unabhängig**: unter der Ein-Branch-Strategie existiert genau
  **ein** Merge, der Rebase geschieht davor. Keine Änderung — eine Änderung wäre eine
  Design-Abweichung und gehörte in §13.
- **§9.2 Spalte „Rückrollpunkt"** (je Welle): der Plan führt dieselben Punkte
  (`docs/plans/2026-09-25-repository-documentation-consolidation.md`, Wellenübersicht) unverändert
  und **commitweise**; die Wellen-Rückrolle wird durch die Ein-Branch-Strategie **nicht** berührt.
- **§9.2 Spalte „Parallel mit" / „Abhängig von"** für **W4/W5/W6**: war nicht Teil von OP-1 und ist
  in Rev. 0.4 **doch** angefasst worden — die Spalte wurde auf den ausgeführten **sequenziellen**
  Stand umgestellt (PG-3), der Plan führt W4/W5/W6 seit Rev. 0.3 seriell. Grund der
  **Abweichung** (Design :269-271 parallel ↔ Plan PG-3 seriell; `:275` führt W5 zusätzlich als
  gleichzeitig ausführbar mit W2 ‖ W3): gemeinsamer Testdatei-Anker
  AC-28/AC-29/AC-31/AC-32 und `check_plan_file_overlap`. Die Abweichung ist **vorbestehend** und
  wurde **nicht** von Rev. 0.4 erzeugt; sie ist **nicht aufgelöst**, sondern als **A14** in §13 und
  **offener Punkt in §17.8** registriert (Owner `orchestrator` → `main_chat`). Für W1, W2, W3, W7
  und W8 bleiben die Spalten inhaltlich unverändert. *(Ausnahme: die **W3**-Zeile nannte zuvor „W2, W4"; da W4 nach der PG-3-Kette **Vorgänger** von W3 ist, wurde „W4" dort zu „Vorgänger, nicht Partner" präzisiert — dieselbe Korrektur, keine eigene Abweichung.)*
- **§2.2 NG-1…NG-11, §7 (AC-01…AC-41), §8 (NFA-01…NFA-11), §9.1, §3–§8, §10, §11, §12.1/§12.3,
  §13, §14**: keine der 41 AC, 24 IC, 11 NFA, 20 R, 25 F, 13 M, 11 NG, 10 FI, 9 OQ, 9 V, 9 Wellen
  nennt eine Branch-, PR- oder Merge-Anforderung. Beleg: vollständige Suche nach
  `chore/docs-consolidation`, „pro Welle", „gestapelt", „Branch pro", „Merge", „Rebase" — die
  Fundstellen sind oben exhaustiv aufgeführt.

**Verbindlichkeits-Fazit:** Nach Rev. 0.4 ist diese Spec wieder die **normative Quelle** *und*
deckungsgleich mit der Ausführung. Der R16-Schutzziel wird weiterhin verfolgt (Merge-Regel
`git mv`-Wellen zuerst, Reihenfolge W1→W8, ein Commit pro Datei, Sequenzierung über die
Commit-Historie), nur über den ausgeführten statt über den überholten Mechanismus.

**Offener Punkt-Status:** **OP-1 ist mit dieser Revision inhaltlich aufgelöst** (die normative
Quelle stimmt wieder mit der Ausführung überein) und durch die **Nutzer-Bestätigung der Rev. 0.4
vom 2026-09-26** abgesichert (§17.7). **Formal geschlossen** wird er damit **nicht** —
Plan und die sechs W0-Records führen ihn weiterhin als offen und sind in dieser Revision
**nicht** geändert (Files-Ownership). Zum Abschluss nachzuführen (Vorgabe, **nicht** ausgeführt):

| Nachzuführen | Stelle | Was |
|---|---|---|
| `docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md` | Kapitel 7.1 (`:289-302`), Kapitel 10 (OP-1-Tabelle `:417`, Zusammenfassung `:407`), Zeile 25 (Kopf) | OP-1 von „offen" auf „inhaltlich aufgelöst durch Spec Rev. 0.4 (2026-09-26, durch den Nutzer bestätigt — §17.7)"; die Formulierung „Korrektur der Spec (**Rev. 0.4**) **beauftragt, nicht ausgeführt** — sie erfordert ein Concept-Review" (`:417`) **entfällt**; Verweis auf §17.6/§17.7 |
| `docs/plans/2026-09-25-docs-consolidation-track-a-gate.md` | §10, Punkt 5 (`:302`) | dasselbe |
| `docs/plans/2026-09-25-docs-consolidation-oq6.md` | Kopfpunkt 2 (`:24`), OP-1-Hinweis (`:216`) | dasselbe |
| `docs/plans/2026-09-25-repository-documentation-consolidation.md` | K1-Liste im Änderungsblock (`:77`), Global Constraints (`:158`), Self-Review (`:476` und offene Punkte `:1895`), Task **W0-2** (Spezifikationsabweichungs-Box) | OP-1 schließen; die Formulierung „die Korrektur der Spec (Rev. 0.4) ist **beauftragt, aber nicht ausgeführt**" entfällt; Rev.-0.4-Bezug auf `§17.6` + `§17.7` (Nutzer-Bestätigung) umstellen. **In dieser Revision bewusst nicht ausgeführt** — der Plan wurde **nur in Ankern und Faktenangaben** angefasst (K12, Revisions-Bump 0.3 → 0.4, berichtigte Zeilenzahlen, berichtigte OP-1-Aussage im Self-Review; **kein** Task-, Wellen-, AC-, IC-, NFA- oder Gate-Inhalt). Die hier genannten Plan-Zeilenanker (`:77`, `:158`, `:476`, `:1895`) sind durch den Revisions-Bump des Plans **verschoben** und bei der Umsetzung dieses Folge-Schritts neu zu bestimmen |
| `docs/plans/2026-09-25-docs-consolidation-oq1.md` | Kopf (`:42`), Punkt 3 (`:422`) | **keine inhaltliche Änderung nötig** — die Vorrang-Regel („bei Widerspruch gilt die Spec") ist durch Rev. 0.4 wieder stimmig; nur die Datums-/Versionsangabe wäre optional nachzuziehen |
| `docs/plans/2026-09-25-docs-consolidation-oq2.md`, `…-oq8.md` | Kopf (`:38-39` bzw. `:35`) | **keine inhaltliche Änderung nötig**, siehe vorige Zeile |

Ein **Concept-Review** über Rev. 0.4 **ist als erfolgt zu führen** (2026-09-26,
`VERDICT: BLOCKED`, Befund **F-1**); der Entscheidungsweg `main_chat` (Plan Rev. 0.4, K1) hat
am **2026-09-26** entschieden — Auflösung und Wortlaut in **§17.7**. Der Abschluss von **OP-1**
in Plan und Records bleibt ein **Folgeschritt** (siehe Tabelle oben).

---

### 17.7 Nutzerfreigabe der Rev. 0.4 (Behebung von **F-1**)

| Feld | Angabe |
|---|---|
| **Befund** | **F-1** — Concept-Review der Rev. 0.4: `VERDICT: BLOCKED`. Rev. 0.4 führte **neue normative Pflichten** ein (verbindliche Commit-Titel-/Body-Konvention, Branch-Aufbewahrung als Scope-Aussage) und installierte sie „mit derselben Verbindlichkeitstiefe", **ohne erneute User-Freigabe**. Der Freigabevermerk richtete die Ausnahme **im Dokument selbst** aus; §15 lässt `APPROVED` nur nach Concept-Review **und** User-Freigabe zu. |
| **Ursache** | Die Rev. 0.4 war als **Inhaltsrevision** ohne Freigabeschritt entstanden; der Autor hat die Ausnahme selbst erteilt, weil der Freigabeumfang (W0–W8) unverändert blieb. Diese Begründung trug dem Gate nicht Rechnung. |
| **Entscheidung** | Der **Nutzer** hat **Rev. 0.4 am 2026-09-26 ausdrücklich freigegeben** — über den Entscheidungsweg laut Plan Rev. 0.4, K1 (`main_chat`), weitergeleitet an den `orchestrator` und hier durch `documenter` formalisiert. |
| **Bezugsrahmen der Bestätigung** | **unverändert:** der Umfang der Ausführungsmechanik **W0–W8** (keine Welle, kein AC/IC/NFA/Risiko verschoben). **neu bestätigt:** die in Rev. 0.4 aufgenommenen **Normativitätsaussagen** — die verbindliche **Commit-Titel-/Body-Konvention** (§9.2 „PR-/Branch-Strategie", Punkt 2; R16-Mitigation) und die **Branch-Aufbewahrung** als Scope-Aussage (Punkt 4: „diese Spec schreibt weder Löschung noch Aufbewahrung eines Branches vor"). |
| **Bedingung** | **A13** und die **W4/W5/W6-Serialität** (A14) sind als **offene, dokumentierte Abweichungen** zu registrieren — erledigt: A13/A14 in §13, A14 zusätzlich als offener Punkt in **§17.8**. |
| **Ergebnis** | **F-1 aufgelöst.** Die in diesem Dokument ausgerichtete Ausnahme („Inhaltsrevision ohne erneute Freigabe") ist **entfallen** — die Freigabe liegt extern vor. `status: APPROVED` besteht unverändert, **kein** Revisions-Bump: die inhaltliche Revisionshistorie endet bei **Rev. 0.4**. Geändert wurden: Frontmatter (`approved: 2026-09-26`, `approved-scope`), Statuskopf, Revisionszeile **0.4**, Revisionszeile **„Freigabe (Rev. 0.4)"**, §16 (Zeile „Rev. 0.4 — Abgrenzung") und §17.6 (OP1-7). |
| **Nicht betroffen** | AC-01…AC-41, IC-01…IC-24, NFA-01…NFA-11, R1…R20, F1…F25, M-1…M-13, NG-1…NG-11, FI-1…FI-10, OQ1…OQ9, W0…W8 — **keine** inhaltliche Änderung durch die Freigabe. |

---

### 17.8 **Offener Punkt** — W4/W5/W6-Serialität (A14)

> **Status: OFFEN.** Dieser Punkt ist **bewusst nicht aufgelöst.** Er wurde vom Nutzer am
> 2026-09-26 als *offene, dokumentierte Abweichung* registriert; die Inhaltsentscheidung ist
> ausdrücklich der Ausführungsmessung überlassen.

| Feld | Angabe |
|---|---|
| **Sachverhalt** | §9.2 führte **W4, W5, W6** in der Spalte „Parallel mit" als **paarweise parallel** (W4‖W5, W4‖W6, W5‖W6) — das entspricht dem Design (`docs/specs/2026-09-25-repository-documentation-consolidation-design.md:269-271`; `:275` führt W5 zusätzlich als gleichzeitig ausführbar mit W2 ‖ W3). Der Plan Rev. 0.4 führt sie **seriell**: `PG-3 (BEWUSST SERIELL, 1 Agent) W4-1 → … → W6-2` (Wellenübersicht) und in den Task-Köpfen W4-1…W6-2 (`parallel_group: PG-3 (seriell)`). **Ausgeführt wird seriell.** |
| **Registrierung in §9.2** | Die Spalte „Parallel mit" weist für W4/W5/W6 seit Rev. 0.4 **`sequenziell` (PG-3)** aus; die Spalte „Abhängig von" führt die PG-3-Kette mit. Die Angabe bildet damit die **tatsächliche Umsetzung** ab. |
| **Begründung des Plans** | Alle vier AC der drei Wellen — **AC-28, AC-29, AC-31, AC-32** — verweisen per `::` auf denselben Testdatei-Anker `tests/test_docs_consolidation_migration.py`. Tasks, die dieselbe Datei anlegen oder erweitern, sind **nicht ownership-disjunkt**; `check_plan_file_overlap` (`scripts/lib/orchestration.py`) würde den Parallelstart als Fehler melden. Zusätzlich erzeugt jede `git mv`-Welle R+A-Diffs auf denselben Stammpfaden. (Plan Rev. 0.4, Abschnitt „Warum W2 ‖ W3 parallel ist, W4/W5/W6 aber nicht".) |
| **Charakter** | **Echte, vorbestehende Spec-Abweichung** (Plan gegen Spec) — **nicht** von Rev. 0.4 erzeugt und **nicht** Teil der Branch-Korrektur (OP-1). Der Concept-Reviewer hat sie als solche bestätigt. |
| **Abweichungs-ID** | **A14** in §13 (Design ↔ Spec ↔ Plan). |
| **Status** | **OFFEN** |
| **Owner** | `orchestrator` → Eskalation an `main_chat` (Produkt-/Ausführungsentscheidung). |
| **Auflösungsweg** | Eine Auflösung — also die Rückführung der §9.2-Angabe auf „parallel" **oder** eine Änderung der Ausführungsreihenfolge — erfordert eine **eigene Spec-Revision mit Concept-Review**. Der Punkt wird **nicht** nebenläufig in Plan oder Records entschieden. |
| **Zwischendurch geltende Regel** | Bis zur Auflösung gilt die **Ausführung** (seriell, PG-3); die Abweichung ist dokumentiert und nicht stillschweigend. |

---

### 17.9 Rev. 0.5 — Gate-Präzisierung W2/W3 und Schließung zweier Eigentümerlücken (K13…K17)

**Eingang.** Ausführungs-Ledger des Plans Rev. 0.4, Abschnitt L (Befunde **B-1**, **B-2**,
**B-4**, **B-5**; Errata **E-11**, **E-14**, **E-15**), gemessen am 2026-09-26 gegen den
Working Tree des Branches `feat/repository-documentation-consolidation-main`.
**Charakter:** ausschließlich **Präzisierung** — **kein** neuer AC, **keine** neue IC, **kein**
neues NFA, **kein** neues Risiko, **keine** neue Welle, **keine** geänderte ID.

#### 17.9.1 Nachmessung — die Auftragsprämisse „V1 emittiert ERROR" ist **falsch**

> **Ergebnis: die Prämisse wurde NICHT übernommen.** Gemessen am 2026-09-26 am Working Tree.
> **Methode:** Code-Inspektion an den belegten Stellen (in dieser Revisionsrunde stand **kein**
> Shell-Zugriff zur Verfügung; alle Belege sind deshalb **Datei:Zeile**-Zitate aus dem
> Working Tree, keine Laufzeit-Ausgaben — das ist die offengelegte Grenze der Messung).

| Nr. | Behauptung der Prämisse | Messung | Ergebnis |
|---|---|---|---|
| 1 | V1 emittiert `Severity.ERROR` | `scripts/lib/consistency/docs.py:359` — `severity = Severity.ERROR if v1_strict(config) else Severity.WARNING`; `v1_strict` (`:314-326`) liest `docs-consolidation.checks.strict`, **fehlend ⇒ `False`**; `.meta-config/project.yaml:398-399` enthält unter `docs-consolidation:` **ausschließlich** `enabled: true` | **widerlegt** — im Ist-Zustand **WARNING** |
| 2 | Der W2-Gate-Zustand („nur V1-WARNINGs, Exit 1") existiert | `scripts/consistency-check.py:52-56` importiert **nur** `check_readme_docs_index`, `check_sync_cli_docs`, `check_ui_help_mappings`; `check_no_manual_counts` kommt in `scripts/` **nirgends** vor (einzige Fundstellen: `docs.py:128/155/350` und `tests/test_doc_facts.py`). Zusätzlich pindet `tests/test_doc_facts.py:2403-2422` (`test_v1_is_not_wired_into_the_runner_yet`) die Nicht-Registrierung **explizit** | **widerlegt** — der Runner emittiert derzeit **kein** `docs.no_manual_counts`-Finding |
| 3 | Der Zustand tritt „nach W2-7" ein | Die Registrierung ist W2-7-Aufgabe; selbst dann wäre die Severity **WARNING**, solange `checks.strict` fehlt (`checks.strict: true` wird erst in **W3-4** gesetzt) | **widerlegt** — die Unerreichbarkeit hat **zwei** unabhängige Ursachen: **(a)** Severity-Erwartung, **(b)** fehlende Registrierung |

**Folge für die Normativität:** §10 bleibt in seinem **Pflichtumfang** unverändert; die
Wellen-Gates des Plans werden auf **beobachtbare, erfüllbare** Kriterien umgestellt (Plan Rev.
0.5, Katalog **K13**/**K14** und Kriterientabelle `W-GATE-TABLE`; betroffene Stellen:
Wellen-Verifikation **W2**, **W3**, **W4**…**W8**, Task-Akzeptanz **W3-7**, DoD Punkt 2).
**Zweite Korrekturrunde (RVW-1/RVW-2/RVW-3):** die erste Fassung dieser Umstellung war selbst
noch unerreichbar — das Aggregat `docs-findings: 0` ist **dauerhaft** unerreichbar (V7 bis W5-3,
V3 bis W8-2, V2 bis W3-6, V9 **nie**). Es ist deshalb durch **check-spezifische Kriterien mit
Termin und Owner** ersetzt (§10, `--strict`-Punkt, Unterpunkt 5). **Zur Normativität
insgesamt: §17.9.4.**

#### 17.9.2 Katalog K13…K17

| ID | Befund | Korrektur (additiv, mit Beleg) | Betroffene Stellen |
|---|---|---|---|
| **K13** | Das W2-Gate beschrieb einen **nicht existierenden** Zustand (B-2 / E-11): `--strict` → 1 „ausschließlich wegen V1-WARNINGS" | W2 bekommt **zwei** getrennte, beobachtbare Abnahmekriterien: **nach W2-1** (V1 implementiert, **nicht** registriert) und **nach W2-7** (registriert, Severity noch WARNING). Beide über die `--json`-Ausgabe mit **Zählung**, **nicht** über den repo-globalen Exit-Code — ausgewertet wird ein **Zählwert**, kein Exit-Code (RVW-12: ein `A \| B`-Kommando gibt den Exit von `B` zurück; ein `sys.exit(0)` im Konsumenten neutralisiert den Roh-Exit). Erklärt ausdrücklich, dass `checks.strict: true` (W3-4) die Severity erst **danach** dreht. **Zweite Korrekturrunde (RVW-2):** zusätzlich **`W2-GATE-ERRORS`** für die drei weiteren unerreichbaren `consistency-check.py → 0`-Zeilen (W2-Block, W2-2, W2-7) | Plan Rev. 0.5: Wellenblock **W2 — Verifikation** (`W2-GATE-V1`, `W2-GATE-ERRORS`), Task **W2-1** (LEDGER-Notiz), Task **W2-2**/**W2-3**/**W2-7** (`Verifikation`) |
| **K14** | Das Plan-Gate für W3 war **repo-global** (`--strict == 0`), die Spec verlangt einen **Datei-Scope** (B-1) | Zwei getrennte Scopes: **(a)** §10-Pflichtumfang (`docs/INDEX.md` + `scripts/lib/doc_*.py`, **Dokuzeile ohne Prüfkraft** — RVW-14) und **(b)** das Doku-Gate, das in der zweiten Korrekturrunde (RVW-1) von einem Aggregat auf **check-spezifische Kriterien mit Termin und Owner** umgestellt wurde (§10, `--strict`-Punkt, Unterpunkt 5). Baseline des repo-globalen `--strict` als **Altbestand mit Zählung + Kommando** getrennt ausgewiesen. Hinzugefügt wurde die Feststellung, dass §10s Datei-Scope die Doku-Checks **nicht** erfasst (V1 scannt `README.md`/`llms.txt`/`ARCHITECTURE.md`) — ein rein auf §10 bezogenes Gate wäre ein **scheinbar grüner** Nachweis | **§10** (Präzisierung Rev. 0.5, `--strict`-Punkt, Unterpunkte 1–6); Plan Rev. 0.5: Wellenblock **W3 — Verifikation** (`W3-GATE-SCOPE`, `W-GATE`, `W-GATE-TABLE`, `W3-BASELINE-STRICT`), Task **W3-7** (Akzeptanz), Wellenblöcke **W4–W8** |
| **K15** | `scripts/lib/consistency/report.py` hat **keinen** Task-Owner (B-5 / E-15); `line`/`branch` gehen im `--json`-Output verloren (`report.py:28-41`, `:78-97`; gesetzt als Instanzattribute in `docs.py:329-347`) | Ownership wird **W2-7** zugewiesen (nächstliegende Task: sie besitzt Registrierung **und** Common-Gate) — `Files:`-Liste, Reihenfolge-/Abhängigkeitsmatrix, benanntes Abnahmekriterium **F1-PROMOTION**, eigener Step. Abnahme: `line`/`branch` sind **Dataclass-Felder**; `print_json_report` serialisiert sie; **kein** Finding-Attribut geht im `--json`-Output verloren | Plan Rev. 0.5: Task **W2-7** (`Files:`, `Interfaces:`, `Akzeptanz`, `Steps`), **Reihenfolge-/Abhängigkeitsmatrix** (Zeile W2-7) |
| **K16** | Suppressionsregel 3 (§5.1.1, `docs.py:281-311`, `_V1_FENCE_OPEN_RE` `:203`) macht die IC-05-Fundstellen **F2**, **F3-Site-2**, **F4** für V1 unsichtbar — sie liegen im Directory-Structure-Fence (`README.md:680`…`:737`, Fundstellen `:688/:690/:696/:734`) (B-4 / E-14) | Die Lücke bekommt eine **benannte, terminierte** Aufgabe mit Owner: **W2-1, Schritt 4** (`developer`). Abnahme: AC-07- und AC-08-Fixture bleiben grün **und** die vier Fundstellen werden sichtbar (negativer Nachweis gegen die unmarkierte Ist-Fassung). **Reihenfolgebindung:** als **DAG-Kante `W2-1 → W3-4`** abgebildet — **RVW-4:** die Fassung vor diesem Review führte die Bindung **ohne** Kante und begründte das damit, „eine Kante W3-4 → W2-1 wäre eine Rückwärtskante"; das war in der **Kantenrichtung falsch**. `W2-1 → W3-4` ist eine **Vorwärts**kante über die Wellengrenze (W2 vor W3), sie erzeugt **keinen** Zyklus und ist jetzt in Matrix, Wellen-Tabelle und PG-2-Diagramm abgebildet und im Absatz **Zyklenprüfung** mit Nachweis belegt. **Keine neue Task-ID.** | **§5.1.1** (Präzisierung Rev. 0.5 zu Suppressionsregel 3); Plan Rev. 0.5: Task **W2-1** (`Interfaces:`, `Akzeptanz`, `Steps`), Task **W3-4** (`Depends on`, `Vorbedingung`), Reihenfolge-/Abhängigkeitsmatrix (Zeile W3-4), Wellen-Übersicht (W3-Zeile, PG-2-Diagramm) |
| **K17** | Abschnitts-/Zählungsanker im Ledger-Abschnitt L waren an den **Rev.-0.4-Zeilenstand** gebunden | Rev. 0.5 markiert die `plan:<Zeile>`-Verweise in L-1…L-4 ausdrücklich als **historisch (Rev. 0.4)**; alle **neuen** Verweise verwenden **Abschnitts-/Task-Anker** (K12-Logik). Zählungen sind nachgeführt und ihre Herleitung ist belegt | Plan Rev. 0.5: **L-1**, **L-2**, **L-3**, Kopfnotiz des Abschnitts **L** |

#### 17.9.3 Nicht betroffen und weiterhin offen

- **Unverändert:** AC-01…AC-41, IC-01…IC-24, NFA-01…NFA-11, R1…R20, F1…F25, M-1…M-13,
  NG-1…NG-11, FI-1…FI-10, W0…W8, `status: APPROVED`, `approved: 2026-09-26`, der
  Ausführungsfreigabeumfang W0–W8, der **normative Pflichtumfang** im §10-Aufzählungspunkt
  `--validate` (`scripts/lib/doc_*.py` + `docs/INDEX.md`) und die Exit-Code-Semantik des Runners.
- **OQ1 bleibt OFFEN** (blockiert W5). **OQ2/OQ6/OQ8 bleiben geschlossen** und werden nicht
  umgedreht. **OP-1** (formaler Abschluss der Branch-Spec-Korrektur in Plan und W0-Records)
  bleibt unverändert offen. **A14** (§17.8) bleibt unverändert offen.
- **Eigenständig offen (neu benannt, nicht Gegenstand dieser Revision):** das nach
  Master-Rule `spec-plan-workflow` verpflichtende **Concept-Review über Rev. 0.5** ist
  **nicht erfolgt**. Owner: `orchestrator` (Dispatch an `concept-reviewer`). Ergebnis-Ort:
  §17.9.1 bei einem abweichenden Messergebnis. **Blockiert** die Ausführung **nicht** — Rev. 0.5
  führt **keine Pflicht jenseits** des am 2026-09-26 beauftragten Korrekturumfangs ein
  (Präzisierung: **§17.9.4**, nicht die pauschale Aussage der Fassung vor diesem Review).
  **Stand nach der vierten Korrekturrunde:** das Review vom 2026-09-26 liegt vor
  (`VERDICT: CHANGES_REQUESTED`, 15 Findings → Rev. 0.5 K13…K17, danach 14 Findings
  RVW2-1…RVW2-14 und 10 Findings RVW3-1…RVW3-10 → dieselbe Runde). **Vier Entscheidungsvorlagen
  E-1…E-4 sind offen** und liegen beim Auftraggeber; **E-1** (DoD-Punkt-2-Neufassung) ist vor dem
  Abschluss des Vorhabens vorzulegen. **Fristen:** E-1 vor dem Abschluss des Vorhabens (DoD
  Punkt 2), E-2 vor **W8-4 Schritt 1** (voraussetzungsstiftend), E-3 und E-4 vor **W3-7**
  (Gate-Lesart) — Tabelle unten.

---

#### 17.9.4 Review-Korrekturliste der zweiten Korrekturrunde (RVW-1…RVW-15, danach RVW2-1…RVW2-14)

**Eingang:** Concept-Review vom **2026-09-26** (`VERDICT: CHANGES_REQUESTED`) über die Spec- und
Plan-Fassung Rev. 0.5 mit **15 Findings**: **1 Blocker** (RVW-1), **4 Major** (RVW-2…RVW-5),
**8 Minor** (RVW-6…RVW-13), **2 Info** (RVW-14, RVW-15). **Kein Revisions-Bump** — es ist dieselbe,
noch unveränderte Korrekturrunde; `revision` bleibt **0.5**, `status: APPROVED` und
`approved: 2026-09-26` bleiben unverändert.

**Autorisierung (RVW-5b).** Der Auftraggeber hat am **2026-09-26** über ein **A2A-Envelope**
(`main_chat` → `orchestrator` → `concept-architect`) genau die Korrekturen **1–5** beauftragt:
**(1)** W2-Gate, **(2)** W3-7-Gate-Scope, **(3)** `report.py`-Ownership, **(4)** Fenced-Code-Regel 3,
**(5)** Anker/Zählungen — **und ausdrücklich die Beibehaltung von `status: APPROVED` verlangt**.
Der Review hat **innerhalb genau dieses Umfangs** nachgeschärft; **jenseits** davon wurde nichts
installiert. **Dies ist die Belegstelle für die Fortführung des Freigabestands.**

**Präzisierung der Normativitätsaussage (RVW-5a).** Die Aussage der Fassung vor diesem Review,
Rev. 0.5 führe „**keine** neue normative Pflicht" ein, war **nicht haltbar**. Korrigiert wird sie
zu: Rev. 0.5 installiert **keine** Pflicht **außerhalb** des beauftragten Korrekturumfangs.
**Innerhalb** dieses Umfangs ändert Rev. 0.5 sehr wohl **Nachweisformen**, und diese Änderungen
sind:

| # | Was ist **neu** an Rev. 0.5 | Art | Ort |
|---|---|---|---|
| (i) | Das repo-globale `--strict → 0` bzw. `consistency-check.py → 0` als Wellen-Nachweis ist **aufgehoben** — eine **geschriebene** Nachweisform entfällt | **Aufhebung** | §10, Aufzählungspunkte `--validate` und `TEST_COMMANDS`; Plan W2/W3/W4–W8, DoD Punkt 2 |
| (ii) | Zähl-Kommandos über `--json` und die **check-spezifische Kriterientabelle** mit Termin und Owner | **neue Nachweisform** | §10, `--strict`-Punkt, Unterpunkte 2 und 5; Plan `W2-GATE-V1`, `W2-GATE-ERRORS`, `W-GATE`, `W-GATE-TABLE` |
| (iii) | Die Aussage „null `docs.*`-Findings" wird von der **DoD-** auf die **Wellenebene** verlagert, wo sie je V-Check erfüllbar und terminierbar ist; die **inhaltliche** DoD-Aussage bleibt — **RVW2-3: formal in (vii) präzisiert** | **Verlagerung** | §10, `--strict`-Punkt, Unterpunkt 5; Plan DoD Punkt 2, `W-GATE-TABLE` |
| (iv) | Die Reihenfolgebindung `W2-1 → W3-4` (K16) wird als **DAG-Kante** abgebildet | **neue Ausführungsbindung** | §17.9.4/RVW-4; Plan Matrix, Wellen-Tabelle, PG-2 |
| (v) | Suppressionsregel 3 wird als **benannte, terminierte** Umsetzungspflicht (W2-1 Schritt 4) mit Abnahmekriterium | **neue Umsetzungspflicht** | §5.1.1 (Präzisierung Rev. 0.5); Plan Task W2-1 |
| (vi) | `report.py` erhält Ownership und ein benanntes Abnahmekriterium (F1-PROMOTION) | **neue Verantwortung** | Plan Task W2-7 |
| (vii) | **DoD Punkt 2 wird formal neu gefasst (RVW2-3) — Entscheidungsvorlage an den Nutzer.** Die Neufassung („V1…V8 = 0; V9 geduldet") löst den bisher **behaupteten** Sollwert „alle neun V-Checks = null `docs.*`-Findings" **formal** auf. **Substanziell** ist sie spezifikationskonform und **keine** verschleierte Absenkung: IC-05 führt V9 als `WARNING` mit lokaler Duldung, FI-10 stellt den Abbau ausdrücklich als „lokale Aufräumaktion, **kein Spec-Gegenstand**" fest, und §10 nennt **nie** ein „null `docs.*`-Findings" als Norm, sondern nur den datei-bezogenen `--strict`-Pflichtumfang. **Weil ein Sollwert formal aufgelöst wird, ist die Fassung vor dem Abschluss dem Nutzer zur Bestätigung vorzulegen** (Entscheidungsweg `main_chat` → `orchestrator`).   **Bis zur Entscheidung** gilt die Neufassung — sie ist die **einzige Lesart, die den
  Vorhabensabschluss nicht dauerhaft unerreichbar macht** (Option (b) verlangt einen Sollwert, den
  V9 per FI-10 dauerhaft verhindert) und die mit dem `--strict`-Punkt desselben Abschnitts in sich
  stimmig ist; sie wird deshalb **vorläufig** angewendet, **bis E-1 entschieden ist**. Eine
  Stärke-Aussage wird **nicht** geführt: (a) ist gegenüber (b) die **schwächere** Lesart
  (b) ist die Obermenge) | **Entscheidungsvorlage** (Sollwert-Auflösung) | Plan DoD Punkt 2; §10, `--strict`-Punkt, Unterpunkt 5 (letzter Absatz) |
| (viii) | **Die drei Abschluss-Sync-Läufe (W4-3, W5-2, W8-4) werden als eigene, terminierte Steps geführt (RVW2-6).** Sie tragen die Spalten **V2** der W-GATE-TABLE für W4, W5 und W8 und standen zuvor **nur** im Fließtext — in **keiner** `Steps:`-Liste, in **keiner** Checkbox und **nicht** in dieser Tabelle. Sie sind damit **neue Nachweisformen** (kein neuer Task, **kein** neues Datei-`Ownership` — `docs/INDEX.md` bleibt Eigentum des Generators aus W3-6) | **neue Nachweisform** (Ausführungspflicht) | Plan Task W4-3 Schritt 4, W5-2 Schritt 4, W8-4 Schritt 5; §17.9.4 (viii) |
| (ix) | **`python3 scripts/sync.py --validate` wird im §10-Aufzählungspunkt `--validate` terminiert (RVW2-2).** Die normative Aussage („darf bei V1, V2, V3, V6 nicht grün sein") bleibt **wortgleich**; **neu** ist ausschließlich die **Mechanik-Begründung** und der **Termin 0 = W8-4** | **Präzisierung** (keine Absenkung) | §10, Aufzählungspunkt `--validate`; Plan `W-VALIDATE-ROT` |
| (x) | **V9: `179` entfällt als Sollwert; Obergrenze erst nach Messung (RVW2-4).** Der Altbestand ist maschinenlokal und gitignoriert; die Zahl ist im Working Tree **nicht messbar**. Neu sind: `BACKUP-BASELINE` vor der Implementierung, Obergrenze danach, Verschlechterungs-Ausnahme für V9, und die Festlegung der Altersschwelle N als **Modulkonstante** statt als **Config-Key** (IC-22 hat sechs Keys, Schema-Block geschlossen — `config/project-config.schema.json:2421-2470`). **Korrekturtur (RVW3-6):** die Obergrenze ist **kein** Sollwert dieser Spec — sie wird als Artefakt des **W8-4-Review-Protokolls** festgehalten; ein Spec-Nachtrag durch die ausführende Task findet **nicht** statt | **Präzisierung** (keine neue Pflicht) | §10, `--strict`-Punkt, Unterpunkt 5; IC-05 (V9-Zeile, Hinweis); IC-22 (Hinweis) |

**Unverändert** bleibt der **normative Pflichtumfang** (§10, Aufzählungspunkt `--validate`), die
Exit-Code-Semantik des Runners (`consistency-check.py:23-26`, `:273-276`, `report.py:75`, `:99`)
und der **normative Inhalt** der DoD-Aussage. **Formal geändert** wurde ihre **Fassung** in
DoD Punkt 2 (Punkt (vii) oben) — dort ist die Entscheidungsvorlage an den Nutzer benannt.

**Prüfung der vierten Runde (RVW3) — was gedeckt ist und was nicht.** (a) Die **drei
Abschluss-Sync-Läufe** (W4-3 Schritt 4, W5-2 Schritt 4, W8-4 Schritt 5) sind in **(viii) namentlich
geführt**; sie sind damit als **neue Nachweisform deklariert** — die Deklaration in (viii) ist die
**Grenze** der Autorisierung, **nicht** deren Aufhebung, und sie werden hier **nicht** als
Bestandskorrektur und **nicht** als eigene Pflicht geführt. (b) **NICHT gedeckt und daher als OFFEN
gekennzeichnet, nicht ausgeführt:** die **`W3-BASELINE-STRICT`-Textpflicht in W4 und W5**
(Rückfallregel: `errors: 0` **und** `warnings: 0` ⇒ `--strict → 0` ist für W4…W8 wieder maßgeblich
und die Wellenblock-Zeilen sind wieder wörtlich zu restaurieren; Owner `orchestrator`, Termin **vor
W6-1**; Plan-Text: `W3-BASELINE-STRICT` (b) und die Geltungsregel-Absätze). Sie steht **nicht** in
dieser Normativitätstabelle, geht aber als **Textpflicht in zwei späteren Wellen** über den
beauftragten Umfang hinaus. Sie bleibt als Text im Plan **unverändert und ungestrichen** bestehen,
wird aber **nicht** als beschlossen und **nicht** als vom Auftrag gedeckt geführt.

**Dritte Korrekturrunde (Review-Runde 2) (Concept-Review vom 2026-09-26,
`VERDICT: CHANGES_REQUESTED`, 14 Findings:
2 Blocker, 4 Major, 7 Minor, 1 Info).** **Kein Revisions-Bump** — dieselbe, noch unveränderte
Korrekturrunde; `revision: 0.5`, `status: APPROVED` und `approved: 2026-09-26` bleiben
unverändert. Die Behandlung **innerhalb** des beauftragten Umfangs (Korrekturen 1–5); eine
**Entscheidung** wird **nicht** unterstellt — die **vier** Entscheidungsvorlagen **E-1**…**E-4** sind
unten als solche gekennzeichnet und liegen beim Auftraggeber. **Betroffene Stellen** der dritten
Runde: §6(b) (Präzisierung **zurückgestellt**, E-3), §10 Aufzählungspunkt `--validate` (Mechanik +
**Terminierung**), §10, `--strict`-Punkt, Unterpunkt 5 (a: **Präsenzregel statt
Registrierungszahl**; V9 **ohne Sollwert**; Verschlechterungs-Ausnahme), §10 `TEST_COMMANDS`-Punkt
(Spannungslage dokumentiert, **E-4**), §11.1 OQ9 (Ergebnis-Ort präzisiert, **ohne** OQ9 zu
entscheiden), IC-05 (V9-Hinweis), IC-22/M-11-Hinweis, FI-10, §17.9.3, §17.9.4 (Normativitätstabelle
**(vii)–(x)**; Behandlungstabelle RVW2-1…RVW2-14; Entscheidungsvorlagen **E-1**…**E-4**).
**RVW3-10:** die Angabe „§16 (Tabellenumfang)" als betroffene Stelle dieser Runde ist **gestrichen** —
§16 enthält keinen Verweis auf E-1…E-4 und **keine** dort sichtbare Änderung aus dieser Runde; ohne
Diff ist eine Änderung dort **nicht belegbar** und wird **nicht** behauptet. §16 bleibt der
dokumentierte **Rev.-0.3-Stand** (der `No-Placeholder`-Eintrag nennt weiterhin OQ2/OQ6/OQ8; das ist
als historischer Rev.-0.3-Stand qualifiziert, maßgeblich ist §11).

| ID | Schwere | Befund | Behandlung in dieser Korrekturrunde |
|---|---|---|---|
| **RVW2-1** | Blocker | `docs-checks` zählt `len(Counter(check))` über **Findings**, nicht registrierte Checks; die Tabelle verlangte 7/8/9, forderte aber `V4 = 0` und `V5 = 0` ⇒ real 5 bzw. 7. Im Ist-Zustand ist der Wert **0** (V1 nicht registriert) | **§10 Punkt 5(a) neu**: **Präsenzregel** (Zeile muss für jeden Check mit Erwartungswert ≠ 0 erscheinen) **ersetzt** die Registrierungszahl; der Counter ist **Dokuzeile ohne Sollwert**; die Registrierungszahl ist aus der Messquelle **nicht ableitbar** und wird **nicht** behauptet (Ist-Zustand `0` ist im Plan ausgewiesen, Termin/Owner **W2-7**). Der belegte V4-Name `docs.readme_index` (`docs.py:118`) ist im Plan korrigiert. Die fehlende Empfindlichkeit der Regel für Checks mit Erwartungswert 0 ist als **Grenze benannt** |
| **RVW2-2** | Blocker | `sync.py --validate → 0` in **allen** Wellenblöcken unerreichbar; W3-Block widersprach sich selbst; §6(b)/§10 Pkt 1 sanktionieren das Nicht-Grün-Sein | **§10 Punkt 1** um Mechanik und **Termin** ergänzt (wortgleicher Sollwert bleibt); neue Plan-Regel **`W-VALIDATE-ROT`** — planmäßig rot W2-7…W8-2, spätester Termin 0 **W8-4**, Owner `validator`, benannte V-Checks. Sieben Wellenblock- und neun Task-Zeilen umgestellt. **Kein Sollwert abgesenkt** |
| **RVW2-3** | Major | DoD Punkt 2 in sich widersprüchlich; Klammer „V9 wird im Doku-Scope nicht emittiert" falsch | DoD Punkt 2 **neu gefasst**; **§17.9.4 Punkt (vii)** als **Entscheidungsvorlage an den Nutzer**; §10 Punkt 5 letzter Absatz entsprechend korrigiert. Spec-Konformität belegt (IC-05, FI-10, §10) |
| **RVW2-4** | Major | V9 = **179** unmesbar, maschinenlokal (`.gitignore:13`/`:22`), kollidiert mit der Verschlechterungsregel; N unbestimmt | **§10 Punkt 5** und Plan: `179` nur noch als **Bestandsangabe**; `BACKUP-BASELINE` (W8-4 Schritt 1), **Obergrenze erst danach** (Schritt 4), **Ausnahme** in der Verschlechterungsregel, DoD/Wellenblock/Coverage-Matrix/Task-Akzeptanz nachgezogen. N als **Modulkonstante** statt Config-Key (siehe RVW2-7) |
| **RVW2-5** | Major | `tests/test_doc_facts.py:2403-2422` wird von W2-7 zwingend rot; keine Task räumt ihn ab; W2-Gate hängt daran | **Bestehender** Task **W2-7** (Schritt 1, `Files:`, `Akzeptanz`, Matrix) — **keine** neue Task-ID. Der Pin wird **ersetzt, nicht gelöscht**: positiver Registrierungs-Pin (Import **und** `docs.no_manual_counts` im `findings[]` eines Fixture-Laufs mit `enabled: true`). AC-13/AC-38-Abhängigkeit geprüft: AC-38 bleibt grün, weil die Szenario-Fixtures den Key nicht setzen (IC-22, Fail-off) |
| **RVW2-6** | Major | Abschluss-Sync-Läufe in W4-3/W5-2/W8-4 in keiner `Steps:`-Liste, nicht in der Normativitätstabelle, tragen aber die V2-Spalten W4/W5/W8 | Je **eigener Step** (W4-3 Schritt 4, W5-2 Schritt 4, W8-4 Schritt 5), **ohne** neues Datei-`Ownership`; aufgenommen als **§17.9.4 Punkt (viii)**; Checkboxen **190 → 194**, offen **150 → 154**, Herleitung korrigiert und als **nicht gemessen** gekennzeichnet |
| **RVW2-7** | Minor | W8-4 führte einen siebten Config-Key unter einem `additionalProperties: false`-Block | **Key entfällt**: N wird **Modulkonstante** in `scripts/lib/consistency/docs.py` (Muster `V1_SCAN_RELPATHS`/`V1_MAX_TOKEN_GAP`, `docs.py:158`/`:164`); `Files:` auf „nur `PROJECT_STRUCTURE`" eingegrenzt. Beleg: `config/project-config.schema.json:2421-2470`, IC-22, M-11. **Wäre** ein Config-Key gewünscht, wäre das eine **neue** Pflicht (IC-22 + M-11 + W1-9) — **nicht** beschlossen (**E-2**) |
| **RVW2-8** | Minor | `docs/guides/configs/project.yaml.example` als `docs/**/*.md` gezählt | Plan: Fußnote ¹, W5-Block und W5-2-Zusatz auf den `.md`-Pfad korrigiert; **neu ergänzt:** W5-1 legt `docs/plans/…-oq9.md` an ⇒ V2 rot **ab W5-1** (Termin bleibt das Wellenende). OQ9-Wortlaut **ohne OQ9 zu entscheiden** präzisiert: `docs/guides/INDEX.md` wird von keiner Welle erzeugt — gemeint ist die Zeile im generierten `docs/INDEX.md`, Abschnitt `## guides` |
| **RVW2-9** | Minor | Leitsatz der Zyklenprüfung („jede Kante zeigt auf eine **niedrigere** Welle") durch `W2-1 → W3-4` widerlegt | Leitsatz umgestellt auf „**keine** Rückwärtskante; Vorwärts- und Querwellenkanten zulässig und **namentlich genannt**"; alle Querwellenkanten enumeriert |
| **RVW2-10** | Minor | LEDGER-Notiz W2-1 nennt „ausschließlich Step 4 (Commit)"; Commit ist Schritt 5 | Auf „Schritt 4 (K16-Regel-3-Eingrenzung) **und** Schritt 5 (Commit)" korrigiert; deckungsgleich mit L-1 |
| **RVW2-11** | Minor | Rev.-0.5-Text zitiert eigene historische Zeilenanker, obwohl K12/K17 sie abgeschafft haben | `plan:1086-1089`, `plan:1058/1235/1329`, `plan:924-940` durch Abschnitts-/Task-Anker ersetzt; K17-Regel auf Task-Notizen und Rev.-0.5-Text erweitert; **Rev.-0.4-Text in L-2/L-3/L-4 bleibt wortgleich** und ist als überholt qualifiziert |
| **RVW2-12** | Minor | Aufhebung des `--strict` ruht auf ungemessener Prämisse („rund 19"), keine Rückfallregel | „19" als **Schätzung, nicht gemessen** markiert (auch in L-2/B-1); **Rückfallregel** in `W3-BASELINE-STRICT`: `errors: 0` **und** `warnings: 0` ⇒ `--strict → 0` ist für W4…W8 **wieder** maßgeblich und die Aufhebung ist zu annullieren; Owner `validator`, Entscheidungspunkt **W3-7** |
| **RVW2-13** | Minor | `--check` wird auf V1/V2/V6 zurückgeführt — unbelegt und sachlich falsch | Alle betroffenen Zeilen tragen „**Drift-Lauf, kein Consistency-Nachweis**"; Beleg `sync_pipeline.py:914` und `cli_commands.py:975`. **§6(b) bleibt unverändert** und ist als **Entscheidungsvorlage E-3** zurückgestellt (Optionen a/b/c dort benannt) |
| **RVW2-14** | Info | Fußnote ³ („nicht implementiert, nicht vorab prüfbar") gilt nur zum Planungszeitpunkt | Neu: „**zum Planungszeitpunkt** nicht messbar; **ab dem ersten W2-7-Lauf** messbar" — zeitgebunden, keine Fortschreibung |

**Entscheidungsvorlagen (nicht getroffene Entscheidungen — liegen beim Auftraggeber).** Vier
offene Punkte; **keine** davon ist in dieser Revision entschieden:
| ID | Frage | Optionen | Empfehlung der Autorin | Owner | **Frist** (RVW3-5) |
|---|---|---|---|---|---|
| **E-1** | Bestätigung der Neufassung von **DoD Punkt 2** (formal aufgelöster Sollwert, §17.9.4 (vii)) | (a) bestätigen — „V1…V8 = 0, V9 geduldet"; (b) Sollwert „null `docs.*`-Findings über alle neun" bewusst **halten** und den Vorhabensabschluss entsprechend **nicht** erreichen; (c) DoD um eine **dritte** Variante ergänzen | **(a)** — (b) ist dauerhaft unerreichbar, (c) ist eine Neuerfindung | `main_chat` → `orchestrator` | **vor dem Abschluss des Vorhabens** (DoD-Punkt-2-Abnahme) |
| **E-2** | Soll die V9-Altersschwelle N ein **Config-Key** sein? | (a) **Modulkonstante** (jetzt im Plan umgesetzt, IC-22/Schema bleiben unberührt); (b) zusätzlicher Key in **IC-22 und M-11** + Nachlieferung über W1-9 | **(a)** — (b) ist eine **neue** normative Pflicht und ein **siebter** Key unter `additionalProperties: false` | `orchestrator` | **vor W8-4 Schritt 1** — **voraussetzungsstiftend**: dort setzt W8-4 N bereits als Modulkonstante um; bei (b) wäre die W8-4-Arbeit hinfällig und W1-9 nachzuliefern |
| **E-3** | Präzisierung des `--check`-Halbsatzes in **§6(b)** | (a) auf `--validate` allein verengen; (b) `--check` mit der V6-Aussage verknüpfen; (c) unverändert lassen, Abweichung nur im Plan führen (**jetzt angewendet**) | **(a)** oder (c); (b) erzeugt eine zusätzliche Kopplung | `orchestrator` → `concept-reviewer` | **vor W3-7** — die Lesart des `--check`-Gates wird dort ausgewertet |
| **E-4** | Widerspruch **innerhalb von §10**: der Aufzählungspunkt `--validate` erlaubt planmäßig rot, der `TEST_COMMANDS`-Punkt behauptet „läuft in jeder Welle grün" | (a) `TEST_COMMANDS`-Punkt auf „**planmäßig rot** bis W8-2 (siehe den `--validate`-Punkt und `W-VALIDATE-ROT`)" qualifizieren; (b) `TEST_COMMANDS` aus der Wellen-Verifikation **streichen** und nur `TEST_COMMAND` (`--validate`) mit der Terminierung führen; (c) beide Sätze unverändert lassen (**jetzt angewendet**, mit dokumentierter Spannung) | **(a)** — (b) verändert den Repo-Vertrag, (c) lässt einen Widerspruch in der normativen Quelle stehen | `orchestrator` → `concept-reviewer` → `main_chat` | **vor W3-7** — dieselbe Lesart wie E-3; die Spannung zwischen den beiden §10-Sätzen ist spätestens dort zu entscheiden |

**Vierte Korrekturrunde (Review-Runde 3) (Concept-Review vom 2026-09-26, `VERDICT:
CHANGES_REQUESTED`, 10 Findings: 0 Blocker, 6 Major, 4 Minor).** **Kein Revisions-Bump** — dieselbe
Korrekturrunde; `revision: 0.5`, `status: APPROVED` und `approved: 2026-09-26` bleiben unverändert.
**Gehebe: ausschließlich Korrektur bestehender Sollwert-Formulierungen, Widersprüche, Step- und
Zeilenanker sowie Selbstverweise.** Keine neue Gate-Form, kein neues Kommando, kein neuer Sollwert,
keine neue Task-ID, keine neue Ausführungspflicht, keine neue Entscheidungsvorlage; **E-1…E-4
bleiben unentschieden**. Vollständiger Abgleich: **Plan Rev. 0.5**, Kopfblock „Vierte Korrekturrunde".

| ID | Schwere | Befund | Behandlung in dieser Korrekturrunde |
|---|---|---|---|
| **RVW3-1** | Major | `W-VALIDATE-ROT`, Zeile „W8-2 … W8-4", nennt „keinen Doku-ERROR-Check" — V2 ist aber ERROR (IC-05) und ab W8-1 rot; W8-2/W8-3 führen keinen Sync | Plan: Spalte auf **V2** berichtigt, Termin **W8-4 Schritt 5** (nicht Schritt 4 — dort ist der Abschluss-Sync **nicht**; Schritt 5 ist er), Owner `tester`; V9 bleibt WARNING und bricht `--validate` nicht. Ergänzend: die Zwischenzeilen W3-7…W8-1 nennen jetzt auch die erneute V2-Rotheit in W4/W5 (Fußnote ¹ der W-GATE-TABLE) |
| **RVW3-2** | Major | W5-2 Schritt 4 wertete die W5-Spalte inkl. „V7 0" aus; V7 wird 0 erst in W5-3 | Plan: W5-2 Schritt 4 weist den Zwischenzustand aus („V7 planmäßig rot, Termin **W5-3**") — dieselbe Form, die W4-3 Schritt 4 für die W4-Spalte bereits verwendet. **Keine** neue Regel |
| **RVW3-3** | Major | Die Begründung für die vorläufige Anwendung der unbestätigten E-1-Fassung war falsch („strengere der beiden Lesarten") | Spec §17.9.4 (vii) und Plan DoD Punkt 2: ersetzt durch die **zutreffende** Begründung — (a) ist die **einzige Lesart, die den Vorhabensabschluss nicht dauerhaft unerreichbar macht**, und wird **vorläufig** angewendet, **bis E-1 entschieden ist**. Ausdrücklich festgehalten: (a) ist gegenüber (b) die **schwächere** Lesart ((b) ist die Obermenge); eine Stärke-Aussage wird nicht mehr geführt |
| **RVW3-4** | Major | „drei Entscheidungsvorlagen E-1…E-3" an vier Stellen gegen „vier" (E-4 fehlte im maschinenlesbaren Freigabeumfang) | Auf **vier** vereinheitlicht: Frontmatter `approved-scope`, Kopfblock (dritte Runde), §17.9.3, §17.9.4-Einleitung |
| **RVW3-5** | Major | E-2/E-3/E-4 ohne Frist; zwei Verweise auf ein **nicht existierendes** „Übergabeprotokoll" | Spec: Spalte **Frist** in der Entscheidungsvorlagen-Tabelle ergänzt (E-1 vor Vorhabensabschluss, E-2 vor W8-4 Schritt 1 als **voraussetzungsstiftende** Frist, E-3/E-4 vor W3-7). Plan: beide Selbstverweise auf **Spec §17.9.4, Entscheidungsvorlage E-x** umgestellt |
| **RVW3-6** | Major | W8-4 Schritt 4 ließ die ausführende Task einen neuen Sollwert in die **APPROVED**-Spec (IC-05) nachtragen — ohne Revisions-Bump/Review/Freigabe, während die Form als E-2 offen ist | **Spec-Nachtrag gestrichen.** Die Festlegung der Obergrenze bleibt **Plan-Protokoll** in W8-4 (`V9-OBERGRENZE` im W8-4-Review-Protokoll, neben `BACKUP-BASELINE`); die Spec bleibt **unverändert** und führt **keinen** V9-Sollwert. §10, `--strict`-Punkt, Unterpunkt 5 entsprechend berichtigt; §17.9.4 (x) um denselben Vorbehalt ergänzt. **Kein** neuer Freigabeweg |
| **RVW3-7** | Minor | Falsche Step-Nummer in W4-3 Schritt 3 („V2 Termin Schritt 5"; der Sync ist Schritt 4, Schritt 5 ist der Commit) | Auf **Schritt 4** korrigiert. **Alle** Step-Verweise in W4-3/W5-2/W8-4 wurden gegen ihre Step-Listen geprüft: W4-3 (`:2403`, `:2410-2411`, `:2416`, Step 4, Step 5) und W8-4 (Schritt 5 für den Sync, Schritt 1/4 für Bestand/Obergrenze) sind konsistent; **keine** weitere Off-by-one-Stelle |
| **RVW3-8** | Minor | Die Task **W3-6** fiel in keine Zeile des `W-VALIDATE-ROT`-Rasters (V2 und V6 dort rot) | Zeile 1 von „W2-7 … W3-5" auf „**W2-7 … W3-6**" verlängert — V2 geht mit dem Sync dieses Tasks auf 0 (Task-Text, Schritt 2), V6 mit W3-7 |
| **RVW3-9** | Minor | Zwei Nummerierungssysteme unter einer Notation („§10 Punkt 1" = Top-Level `--validate`, „§10 Punkt 2/5/6" = Unterpunkte des `--strict`-Punkts; „§10 Punkt 5" löst auf den Szenario-64-Punkt auf) | Auf **benannte Anker** umgestellt: „§10, Aufzählungspunkt `--validate`" bzw. „§10, `--strict`-Punkt, Unterpunkt n" — in §10 selbst, §11.1/§15, §16-Coverage, §17.9.3/§17.9.4, FI-10 **und** im Plan (dort durchgehend „§6(b) / §10 Punkt 1"). Die Notationsdifferenz ist im Kopfblock der dritten Runde benannt. **Historisch gewahrt:** die Behandlungstabellen der Runden 1 und 2 (RVW-1…RVW-15, RVW2-1…RVW2-14) behalten ihre damalige Zähl-Notation **wortgleich** — sie sind Records des damaligen Stands; maßgeblich ist die benannte Form |
| **RVW3-10** | Minor | Die Revisionszeile nannte „§16 (Tabellenumfang)" als betroffene Stelle; §16 enthält keinen E-1…E-4-Bezug | Nennung **gestrichen** (Zeile Rev. 0.5 und §17.9.4-Einleitung); §16 bleibt der dokumentierte **Rev.-0.3-Stand**. Nicht gemessen: ohne Diff ist eine Änderung in §16 **nicht belegbar** und wird **nicht** behauptet |

**Die 15 Findings und ihre Behandlung:**

| ID | Schwere | Befund | Behandlung in dieser Korrekturrunde |
|---|---|---|---|
| **RVW-1** | Blocker | `W3-GATE-DOCS` (Ziel `0 docs.*`-Findings) bei W3-7 unerreichbar | **§10 Punkt 5 neu**: check-spezifische Kriterien mit **Termin** und **Owner** je V-Check; Plan: `W3-GATE-DOCS` **ersetzt** durch `W-GATE` + `W-GATE-TABLE` mit vollständiger Kriterienmenge **je Welle W2…W8**. Nicht verschoben, sondern **geschnitten**. Beleg der Unerreichbarkeit unten. |
| **RVW-2** | Major | drei unerreichbare `consistency-check.py → 0`-Zeilen in W2 (historisch `plan:1058`, `plan:1235`, `plan:1329`) | Plan: alle drei Zeilen bleiben als Historie sichtbar und sind additiv auf **`W2-GATE-ERRORS`** umgestellt (Zähl-Kommando, Erwartungswert je V-Check, Termin, Owner). Die Klammer „nur WARNINGs" (W2-3) ist als **sachlich falsch** korrigiert — V3 ist ERROR und W2-3 folgt auf W2-2. Dokuzeile: der rohe Runner liefert spätestens ab **W8-2** Exit 0. |
| **RVW-3** | Major | W4–W8 behielten repo-globale `--strict → 0`-Zeilen; die Geltungsregel hatte keine Wellenwirkung | Plan: die **fünf Wellenblock**-Zeilen (W4, W5, W6, W7, W8) sind additiv auf die Scope-Kriterien mit **Wellen-Delta** (Erwartungswert, Termin, Owner) umgestellt. Task-Verifikationen bleiben unter der Geltungsregel, mit **ausdrücklicher Wellenabschluss-Relevanz** („eine Task-Zeile ist kein Welle-Gate"). Owner der Textpflege: `orchestrator`, Termin **vor W6-1**, **blockiert keine Welle**. |
| **RVW-4** | Major | K16-Reihenfolgebindung nicht im DAG; die Zyklus-Begründung war falsch | Kante **`W2-1 → W3-4`** in der Reihenfolge-/Abhängigkeitsmatrix, in der Wellen-Tabelle (W3, „Abhängig von") und im PG-2-Diagramm abgebildet; Absatz **Zyklenprüfung** korrigiert und mit Nachweis versehen. Sie ist eine **Vorwärts**kante (W2 vor W3) und erzeugt **keinen** Zyklus; die frühere Begründung verwechselte die Kantenrichtung. **Keine neue Task-ID.** |
| **RVW-5** | Major | „keine neue normative Pflicht" nicht haltbar | Siehe den Absatz **„Präzisierung der Normativitätsaussage"** oben (sechs-itemige Tabelle + Autorisierungsbeleg vom **2026-09-26**). Frontmatter `approved-scope`, Kopfblock und diese Revisionszeile sind entsprechend gefasst. **Keine Pflicht jensehalb des beauftragten Umfangs.** |
| **RVW-6** | Minor | Rev. 0.5 fehlte in Revisions-Tabelle und §15-Anker | 0.5-Zeile in §Revision ergänzt; Rev.-0.5-Anker in §15 Trace-Anker ergänzt (nach Dokumentkonvention der Rev.-0.4-Zeile). |
| **RVW-7** | Minor | falscher Verweis „§12.2 R4 (Hochstufungsreihenfolge)" | Korrigiert auf **§12.1 R4** (V1-Fehlalarme). R4 enthält **keine** Reihenfolgeaussage und wird **nicht** um eine erweitert — die Reihenfolgebindung ist eine Ausführungs-Vorbedingung des Plans (Task W3-4), keine Risiko-Mitigation. Kopfblock und Revisionszeile korrigiert; Plan K16-Eintrag präzisiert. |
| **RVW-8** | Minor | Zählherleitung im Plan-Kopf ergab 148, L-1 korrekt 150 | Plan-Kopf (K17) auf die **L-1-Formel** umgestellt: 35 × 4 + W2-7 (5) + W1-5 (1) + W1-10 (2) + W2-1 (2) = **150**; Gesamtformel 45 × 4 + 2 × 5 = **190** (47 Tasks, davon 2 mit 5 Steps); 40 + 150 = 190 = 188 + 2. Gesamtzahlen unverändert korrekt. |
| **RVW-9** | Minor | Geltungsregel enumerierte falsch (W5-1/W6-2/W7-2 ohne Zeile; Wellenblock W5–W8 fehlten) | Auf **Abschnittsanker** umgestellt (K12-Logik) und an den tatsächlichen Zeilenbestand angeglichen; die Liste der Task-Verifikationen ist im Plan Rev. 0.5 Block **explizit** aufgeführt. |
| **RVW-10** | Minor | Self-Review zitierte den von K13 widerlegten Zustand als Beispiel | Als **historisch (Rev. 0.4)** markiert; die korrigierte Aussage steht unmittelbar darunter. |
| **RVW-11** | Minor | W2-1 `Interfaces:` zitierte die unpräzisierte Suppressionsregel 3 | Ergänzt: „Suppressionsregeln 1–4 (§5.1.1) **in der durch Rev. 0.5 eingegrenzten Fassung**" mit Kurzbegründung. |
| **RVW-12** | Minor | K13 versprach ein Exit-Code-Kriterium, das das Kommando neutralisiert | Auf **Zählwert** umgestellt. **Gilt für jedes neue `--json`-Kommando**: `W2-GATE-V1`, `W2-GATE-ERRORS`, `W-GATE` und §10 Punkt 2 sind **`sys.exit`-frei**; §10 Punkt 2 nennt die Pipe-Falle explizit. Negativbeispiel (historisches Kommando mit `sys.exit(0)`) bleibt als solches gekennzeichnet. |
| **RVW-13** | Minor | Global Constraints (Plan) nannte die Rev.-0.4-Spec-Korrektur als nicht ausgeführt, Self-Review als erfolgt | Der Absatz in **Global Constraints** ist als **historischer Rev.-0.4-Zeilenstand** markiert und verweist auf **§17.6/§17.7**; maßgeblich ist der Self-Review. **Der Status von OP-1 bleibt unangetastet offen** (nur der formale Abschluss ist offen). |
| **RVW-14** | Info | `W3-GATE-SCOPE` ist konstruktionsbedingt tautologisch | Als **Dokuzeile ohne Prüfkraft** geführt, **nicht** als Prüfkriterium — neu **§10 Punkt 6a** und Plan-Annotation. Verweis auf das Doku-Gate (Punkt 5 / `W-GATE-TABLE`). |
| **RVW-15** | Info | `v1-files` ⊆ `V1_SCAN_RELPATHS` kann konstruktionsbedingt nicht fehlschlagen | Als **Dokuzeile** geführt, **nicht** als Prüfkriterium — neu **§10 Punkt 6b** und in der W2-GATE-V1-Tabelle. Beweiskräftig für die Abdeckung ist allein der Sichtbarkeitsnachweis aus K16. |

**Beleg der Unerreichbarkeit (RVW-1), am Working Tree gemessen 2026-09-26:**

| Befund | Messung | Termin | Owner |
|---|---|---|---|
| V7 | **10** Dateien in `knowledge/wiki` mit `type: "Architecture"` (`concepts/architecture.md:2`, `architecture-*.md:2`, `core-principles-overview.md:2` u. a.); **null** Treffer auf `derived-from:` im gesamten `knowledge/wiki` — **K24 (Rev. 0.6): am 2026-09-27 nachgemessen = 11; die Zeile bleibt als Rev.-0.5-Stand lesbar, maßgeblich ist 11** | **W5-3** | `tester` |
| V3 | `README.md:721-723` verweist auf `howto/setup/`, `howto/features/`; im Repo existiert **nur** `howto/configs/project.yaml.example` — weder `howto/setup/` noch `howto/features/`. **K23 (Rev. 0.6): präzisiert auf `README.md:722`/`:723`** (`:721` `howto/` und `:724` `howto/configs/` existieren) | **W8-2** | `developer` |
| V2 | `docs/INDEX.md` existiert **nicht** (Glob ohne Treffer) | **W3-6** | `senior-developer` |
| V9 | der Altbestand an `*.sync-backup-*` bleibt laut W8-4-Akzeptanz **unangetastet**; FI-10 stuft ihn als lokale Aufräumaktion ein. **RVW2-4:** die früher hier genannte Zahl **179** ist eine **Bestandsangabe**, im Working Tree **nicht messbar** (gitignoriert) — sie ist **kein** Sollwert; verbindlich ist die regelbasierte Form (Bestandsaufnahme vor der Implementierung, Obergrenze danach) | **kein Termin 0** (geduldet, FI-10) | `tester` |

**Grenze der Messung:** verfügbar waren nur Lesewerkzeuge (kein Shell-Zugriff), alle Belege sind
daher **Datei:Zeile-Zitate** und **Dateilisten-Zählungen** am Working Tree, **keine
Laufzeit-Ausgaben** des Runners. **Nicht gemessen** und daher **nicht behauptet** sind: die
konkrete Anzahl der Findings des repo-globalen `--strict` (Baseline) und die tatsächliche
Finding-Menge je V-Check nach der jeweiligen Welle. Beides wird mit Kommando, Owner und Ort
geführt (`W3-BASELINE-STRICT`, `W-GATE`). Die obige Tabelle ist eine **Prognose auf Basis der
Spezifikation und des Ist-Zustands**, keine gemessene Laufzeit.

---

### 17.10 Rev. 0.6 — E-1 (Modul-Split) und E-2 (AC-30-Verengung), Katalog K18…K24

**Eingang und Autorisierung.** Zwei **bereits getroffene Entscheidungen des Nutzers** vom
**2026-09-27**, über `main_chat` an den `orchestrator` und hierher beauftragt:
**U-1** — die Consistency-Checks werden nach **Familien** aufgeteilt, `docs.py` wird zur
**Fassade**, **jedes** neue Modul **< 600 Zeilen**; **U-2** — **AC-30** gilt künftig **nur** für
**`README.md` + `llms.txt`**, die **25** toten `docs/**`-Links werden als **explizites
Follow-up mit Owner und Termin** geführt. Beide Entscheidungen sind **verbindlich** und werden hier
**nicht** neu bewertet. **Was Rev. 0.6 zusätzlich selbst feststellt, sind ausschließlich
belegte Faktenkorrekturen** (K23, K24) und die daraus folgenden **Konsequenz-Klarstellungen**
(OQ10, `--validate`-Punkt) — keine neue Entscheidung. **Kennung:** `U-1`/`U-2` statt `E-1`/`E-2`
(K25 — Begründung und Legende im Kopfblock dieses Dokuments).

**Abgrenzung zu Rev. 0.5.** Rev. 0.5 war eine Korrekturrunde **innerhalb** einer Revision
(Nachweisformen, keine neue Pflicht). **Rev. 0.6 ist ein echter Revisions-Bump**: AC-30s Wortlaut
ändert sich und neue verbindliche Modulgrenzen kommen hinzu. `status: APPROVED` und
`approved: 2026-09-26` bleiben **unverändert**; die Ausführung W0–W8 bleibt freigegeben. **Keine**
ID wird umnummeriert oder gestrichen; **eine** Task-ID ist neu: **W2-0** (Plan).

#### 17.10.1 Katalog K18…K24

> **Bereichskorrektur (reine Zitier-Angabe, ohne Bedeutungsänderung):** Dieser Abschnitt führt
> ausschließlich die **Rev.-0.6-Hauptrunde** (K18…K24). Die Korrekturrunden tragen **K25…K40**
> (Runde 1) und **K41…K45** (Runde 2) und stehen vollständig in **§17.10.5**; sie gehören nicht in
> diesen Katalog. **Der wahre Endstand ist K45.** (Die Überschrift nannte zuvor `K18…K31` und
> war damit zu weit.)

| K | Befund / Entscheidung | Behandlung | Ort |
|---|---|---|---|
| **K18** | **U-1 — Modul-Split.** `docs.py` ist mit **599** Zeilen an der Grenze und mischt **drei** Altchecks mit V1 und V3; eine Erweiterung um V2, V4, V5, V6, V7, V8, V9 ist ohne Bruch nicht möglich. | **Verbindliche** Modulgrenzen nach **Familien** (die Frage, die ein Check stellt), **jedes Modul < 600 Zeilen**; Zuordnung **jedes** V-Checks V1…V9 und **jeder** der drei Altchecks zu **genau einem** Modul: `docs_links` = V3 + V4 + 2 Altchecks, `docs_freshness` = V1a/V1b + V5 + V6, `docs_wiki` = V7 + V8, `docs_index` = V2 + V9. Die Grenze ist **Folge**, nicht Zweck. | §4.1 (Tabelle + Zuordnungstabelle) |
| **K19** | **U-1 — Fassaden-Contract.** `consistency-check.py:52-56` und `tests/test_doc_facts.py` importieren `docs`; ein Bruch des Imports bricht den Runner und 163 Tests. | `docs.py` re-exportiert **alle** nach außen sichtbaren Namen rückwärtskompatibel; `__all__` ist **exakt** benannt und **aus der Ist-Nutzung abgeleitet** (Importblock des Runners + 29 Referenzstellen im Testmodul), **nicht** geraten. Kein Check-Code bleibt in der Fassade. | §4.1 (Fassaden-Contract, Belegliste) |
| **K20** | **U-1 — Ownership-Kollision der Task-Nummerierung.** Rev. 0.5 ließ **alle** Tasks W2-3…W2-7 `docs.py` **und** `tests/test_doc_facts.py` schreiben — eine **strikte Kette** ohne echte Parallelität. | **Neue** Task **W2-0** als Welle-2-Einstieg (verhaltensneutraler Split) + korrigierter **DAG** mit **echten, write-set-disjunkten** Kanten, **max. 3 parallel**; Tests je Modul in **eigene** Dateien, damit die Write-Sets der Parallelgruppe wirklich disjunkt sind. Zyklenprüfung und **Fail-closed-Klausel** ausformuliert. | Plan Rev. 0.6 (Task W2-0, W2-3…W2-7, Ownership-Matrix, DAG, Zyklenprüfung) |
| **K21** | **U-1 — Modulgrenzen vs. Fach-Module.** Die vier U-1-Dateien heißen `docs_*.py` und stehen in **M1**; ohne Abgrenzung droht Verwechslung mit den **Fach**-Modulen **M1–M4**. | **Explizite Abgrenzung** in §4.1: *M1–M4 = was wird gebaut (Fach); U-1-Module = wo der Datei-Check-Code liegt (Datei).* M1–M4 behalten IDs und Bedeutung; **kein** Modul wird umbenannt. | §4.1 (Abgrenzungsabsatz) |
| **K22** | **U-2 — AC-30 verengt.** Die Verengung ist **nur** tragfähig, wenn die verbleibenden Findings im verbleibenden Scope liegen **und** vom bestehenden Task behebbar sind. | AC-30 auf **`README.md` + `llms.txt`** verengt; die **25** `docs/**`-Fundstellen als **Follow-up** mit **Owner `developer`** und **Termin 2026-10-11**; **Weigerungsnachweis** in §17.10.2; die Folge für `--validate` **benannt** (nicht verschwiegen) und als **OQ10** geführt. | AC-30, §1.2, §10 `--validate`/`--strict`-Punkt 5, §11.1 OQ10, §17.10.2/§17.10.3 |
| **K23** | **Faktenkorrektur.** Die Trace-Matrix nannte `docs/REQUIREMENTS.md:21` als Beleg der AC-30-Zeile und `README.md:721-724` als Fundstellen. **Beides ist falsch.** | `docs/REQUIREMENTS.md:21` nennt **Backtick-Pfade** in einer Tabellenzeile; V3 matcht nur **Link-Syntax** (`V3_INLINE_LINK_RE`, `V3_REFERENCE_DEF_RE`, `V3_HTML_HREF_RE`, `_v3_link_targets`) ⇒ **kein** V3-Finding, deckt sich mit der Baseline (**0** in der Datei). `README.md:721`/`:724` **existieren** ⇒ die Fundstellen sind **`:722`/`:723`**. AC-09, AC-30, Trace-Matrix und §1.2 berichtigt; der Pfadbefund bleibt als **F15-N** erhalten (manual, kein V3-Nachweis). **K30: die Erstfassung dieses Eintrags war eine unvollständige Korrekturliste** — Reststellen `README.md:721-723` bzw. `:721-724` in Plan und Spec sind in K30 nachgezogen. | F15-N (§2.3), §1.2, AC-09, AC-30, §9.1-Anmerkung |
| **K24** | **Faktenkorrektur.** V7-Baseline stood auf **10** Wiki-Seiten mit `type: "Architecture"` (Messung 2026-09-26). | Nachgemessen am **2026-09-27: 11**. Korrigiert an allen maßgeblichen Stellen (§10 `--strict`-Punkt 5, Plan `W2-GATE-ERRORS`, `W-GATE-TABLE`-Fußnote ³, Plan W3-Block RVW-1-Begründungstabelle); die Rev.-0.5-Belegzeile bleibt als historischer Stand lesbar und ist als solcher markiert. **Kein** Sollwert, sondern eine **Bestandsangabe** mit Termin **W5-3**. | §10 `--strict`-Punkt 5, §17.9.4-Belegtabelle (historisierend) |

#### 17.10.2 Weigerungsnachweis zur U-2-Verengung (AC-30)

**Die Verengung ist nur tragfähig, wenn beide Bedingungen erfüllt sind.** Beide sind erfüllt — und
werden hier **beieinander** nachgewiesen, damit die Verengung nicht als Behauptung dasteht.

**Bedingung 1 — die verbleibenden Findings liegen im verbleibenden Scope.** Baseline-Messung
2026-09-27 (Übergabe vom Parent, `check_internal_links()` direkt aufgerufen): **27** Findings =
**25** `branch=="link"` + **2** `branch=="layout"`.

| Klasse | Anzahl | Wo | Im AC-30-Scope (`README.md` + `llms.txt`)? |
|---|---|---|---|
| `branch=="link"` | **25** | ausschließlich `docs/**` — `docs/guides` 10, `docs/concepts` 13 (davon **8** in `docs/concepts/archive/`), `docs/superpowers/plans/` 2; **live** ohne `archive/` = **17** | **nein** → Follow-up |
| `branch=="layout"` | **2** | `README.md:722` (`howto/setup/`), `README.md:723` (`howto/features/`) — beide `branch=="layout"`, beide in **`README.md`** | **ja** → AC-30 |
| `llms.txt` | **0** | — | **ja**, trivially erfüllt |

**Beide** verbleibenden Findings sind `layout`-Findings und liegen in **`README.md`** — also **im**
verengten Scope. Die 25 `link`-Findings liegen **ausschließlich** in `docs/**`, also **vollständig
außerhalb**. Der verbleibende AC-30-Scope ist damit genau: `llms.txt` = **0** + die **2**
README-Layout-Findings.

**Bedingung 2 — der bestehende Task W8-2 genügt; kein zusätzlicher Task nötig.** Der Task
**W8-2** („M-8 — Tote interne Verweise (AC-30)") hat `Files:` **`README.md`** und
`tests/test_docs_consolidation_migration.py`, `Agent:` `developer`, `V-Check:` **V3**. Die
beiden Findings sind **Zeilen in `README.md`** (`:722`, `:723`) und stehen **im selben
Directory-Structure-Fence**, den W8-2 ohnehin anfasst; die Behebung ist ein **Umschreiben zweier
Layout-Einträge auf existierende Ziele** (`howto/setup/`, `howto/features/` → nach der Migration
**W5-2** existierende Pfade unter `docs/guides/`). **W8-2 besitzt damit genau die Datei, in der
beide Findings stehen, und genau die V-Check-Semantik** — die Behebung erfordert **keinen** neuen
Task, **keinen** neuen Check und **keine** neue Wellenzuordnung. **Ergebnis: die Verengung trägt.**

**Was die Verengung ausdrücklich *nicht* leistet (K22, Ehrlichkeitsgrenze).** Sie leistet **nicht**,
dass `docs.internal_links` innerhalb W0–W8 auf **0** geht: V3 bleibt **ERROR** (IC-05) und meldet
die **25** `docs/**`-Findings **weiter**. Daraus folgt, dass (a) die `W-GATE-TABLE`-Zeile für V3
in der Plan-Spalte **W8** von „**0**" auf „**0 im AC-30-Scope**, 25 Follow-up" umgestellt werden
**muss** (im Plan geschehen), und (b) **`sync.py --validate → 0` und `consistency-check.py → 0`
werden dauerhaft unerreichbar** — im §10-Aufzählungspunkt `--validate` ausdrücklich als Folge
benannt, mit der **Deltasperre** als maßgeblicher Lesart (derselbe Mechanismus, der bereits für den
repo-globalen Altbestand und V9 gilt) und mit **OQ10** als der offenen Frage, ob die Severity für
`docs/**` herabgestuft wird. **Beides wird nicht stillschweigend gesetzt.**

#### 17.10.3 Follow-up-Register (Owner und Termin — **kein** AC, **keine** Stillschweigung)

| ID | Gegenstand | Umfang | Owner | Termin | Entscheidungsweg / Nachweis |
|---|---|---|---|---|---|
| **`F-DOCS-LINKS-2026-09-27`** | **25** tote relative interne Links unter `docs/**` (`branch=="link"`) | Behebung oder **bewusstes** Umschreiben auf existierende Ziele; **kein** Inhalts-Rewrite (NG-1) | **`developer`** | **2026-10-11** | Folge-Issue in `Popoboxxo/agent-meta`; **Anlage ist ein benannter Schritt, kein Platzhalter** — siehe „Anlagestand" unten. Nachweis ist `check_internal_links()` mit `docs.internal_links` = **0** Findings unter `docs/**`, ausgewertet als **Zählwert** über `--json` (kein Exit-Code, RVW-12) |
| **`F-REQUIREMENTS-LINKS-2026-09-27`** | `docs/REQUIREMENTS.md:21` (REQ-CMD-09) nennt nicht existierende `howto/commands.md`, `CLAUDE.md`, `howto/instantiate-project.md` | Textkorrektur der REQ-Zeile (**Backtick-Pfade**, kein V3-Finding — F15-N) | `developer` | **2026-10-11** | gemeinsam mit `F-DOCS-LINKS-2026-09-27`; **kein** AC, da V3 diesen Pfad nicht detektiert |
| **`F-LAYOUT-README-2026-09-27`** | `README.md:722`/`:723` (`howto/setup/`, `howto/features/`) | Behebung **im** AC-30-Scope | `developer` (Task **W8-2**) | **W8-2** | **kein** Follow-up außerhalb des Vorhabens — AC-30 / Task W8-2 |

**Anlagestand des Folge-Issues — als benannter Schritt verankert (K38; Review-Befund Runde-1-Minor
„unnummeriert", der Reviewer hat ihn unter OQ10/M10 mitgeführt).** Die Erstfassung führte die
Issue-Nummer nur als Platzhalter. Verankert ist statt
dessen der **Schritt**, nicht die Nummer:

| Schritt | Inhalt | Owner | Frist | Ergebnis |
|---|---|---|---|---|
| **F-ISSUE-ANLAGE** | Issue in `Popoboxxo/agent-meta` anlegen: Titel „Docs: 25 dead relative internal links under `docs/**` (V3)", Body mit Baseline-Messung (25 Fundstellen, Verteilung `docs/guides` 10 / `docs/concepts` 13 / `docs/superpowers/plans/` 2, live 17), Scope-Abgrenzung (AC-30 deckt **nur** `README.md` + `llms.txt`), Owner und Termin | `developer` | **2026-09-30** | Issue-URL + Issue-Nummer werden in die Zeile `F-DOCS-LINKS-2026-09-27` dieser Tabelle **nachträglich eingetragen**; das Register ist ab dann **issue-referenziert** statt platzhalterbasiert |
| **F-ISSUE-ABARBEITUNG** | Behebung der 25 Fundstellen | `developer` | **2026-10-11** | Nachweis = Zählwert `docs.internal_links` unter `docs/**` = **0** |

**Warum zwei Stufen und nicht einer:** der Termin **2026-10-11** ist die **Fertigstellung**, nicht
die Anlage; das Anlage-Datum muss **früher** liegen, sonst ist der Termin nicht haltbar. Beide
Schritte sind **datierte** Termine mit benanntem Owner — **keine** offene Entscheidung und **kein**
Platzhalter.

**Regel:** ein Follow-up dieser Liste ist **kein** Sollwert eines Gates und **kein** AC. Es wird
**nicht** durch eine Wellenabschluss-Zeile als erledigt erklärt; es gilt als erledigt **nur** über
den jeweils genannten Nachweis. **Termine ohne Wellen-Bezug** sind **datierte** Termine mit
Owner, keine offenen Entscheidungen.

#### 17.10.4 Zyklenprüfung und Fail-closed-Klausel (K20, Plan-Seite)

**Zyklenprüfung des korrigierten W2-DAG** (Kanten: `W2-0 → W2-3`, `W2-0 → W2-5`, `W2-0 → W2-6`,
`W2-0 → W2-4`, `W2-3 → W2-4`, `W2-4 → W2-7`, `W2-5 → W2-7`, `W2-6 → W2-7`; Querwellen-Kanten
unverändert `W1-6 → W2-1`, `W0-4 → W2-1`, `W1-5 → W2-5`, `W2-1 → W3-4`, `W1-10 → W3-1`):
**Der Graph ist ein DAG.** Nachweis: (a) **keine** Kante zeigt von einer höheren auf eine niedrigere
Welle; (b) alle W2-**Querkanten** zeigen von `W2-0` (Einstieg) nach hinten auf `W2-3`/`W2-4`/`W2-5`/
`W2-6` und von dort auf `W2-7` (Ende) — es gibt **keine** Kante `W2-3 → W2-0`, `W2-5 → W2-0` oder
`W2-7 → W2-3`; (c) die Topologische Ordnung ist
**W2-1 → W2-2 → W2-0 → {W2-3, W2-5, W2-6} → W2-4 → W2-7** — jede Kante zeigt **vorwärts** in dieser
Reihenfolge; (d) die Wellen-Kopplung bleibt **W2 ‖ W3** mit der **Vorwärts**kante `W2-1 → W3-4`
(RVW-4, unverändert). **Keine Zyklen.**

**Fail-closed-Klausel (verbindlich, K20).** Wird **während** W2-3…W2-7 eine Ownership-Zeile so
geändert, dass eine Datei von **zwei Tasks derselben Parallelgruppe** geschrieben wird, oder dass
eine neue **Rückwärts**- oder **Querkante** entsteht, die die Zyklenprüfung oben bricht, dann
gilt: **die betroffene Task wird nicht gestartet**; der Plan-Rev. 0.6 wird **nicht** stillschweigend
angepasst, sondern es ist ein **korrigierter Plan** mit neuer Ownership-Matrix **und** neuer
Zyklenprüfung **vorzulegen** (Owner `orchestrator`, Entscheidungsweg `main_chat`). **Abbruchkriterien
wörtlich:** (1) `check_plan_file_overlap` meldet für eine Parallelgruppe **zwei** Tasks mit
gemeinsamer Schreibmenge; (2) eine geplante Parallelgruppe **übersteigt 3** gleichzeitige Agents;
(3) die Kantenliste enthält einen **Zyklus**; (4) ein Task müsste eine Datei schreiben, die ein
**früherer** Task derselben Gruppe bereits geschrieben hat. In **allen vier** Fällen gilt
**fail-closed**: **kein** Start, **kein** Teillauf, **keine** stille Korrektur an der
Modulzuordnung.

#### 17.10.5 Korrekturrunden zum Rev. 0.6 — Concept-Review vom 2026-09-27, Katalog K25…K45

**Runde 1 — Eingang:** Concept-Review vom **2026-09-27** über die Rev. 0.6, `VERDICT:
CHANGES_REQUESTED`, **0 kritisch · 11 major · 7 minor · 5 info**, zusätzlich `validator`-Verdikt
**PASS** mit drei nicht-blockierenden Notizen. **Die inhaltlichen Kernaussagen der Rev. 0.6 sind
bestätigt und werden nicht umgestoßen:** die Modulzuordnung (U-1), der korrigierte W2-DAG, die
Parallelgruppe **PG-2a**, das verengte **AC-30** (U-2) und das Follow-up-Register bleiben
**wortgleich in der Sache**. Korrigiert wurden ausschließlich **Widersprüche und Rückstände**.
`status: APPROVED` und `approved: 2026-09-26` bleiben unverändert; **kein** Revisions-Bump
(Korrekturrunde innerhalb derselben Revision, wie schon Rev. 0.5); **keine** AC/IC/R/OQ/Task- oder
V-Check-ID wurde umnummeriert oder gestrichen.

| K | Befund (Review) | Behandlung | Ort |
|---|---|---|---|
| **K25** | **M1 — ID-Kollision.** `E-1`/`E-2` bezeichneten gleichzeitig die Rev.-0.6-Nutzerentscheidungen und die Rev.-0.5-Errata/Entscheidungsvorlagen. | **Umbenennung** der beiden Nutzerentscheidungen auf **`U-1`** (Modul-Split) und **`U-2`** (AC-30-Verengung) an **allen** Stellen beider Dokumente; **Legendenzeile** im Kopfblock grenzt `U-*` (geschlossen) / `E-*` (Errata bzw. offene Vorlage) / `OQ*` (offene Frage) / `K-*` (Korrekturkennung) ab. Die `E-1…E-4` bleiben **unverändert** und sind **keine** Nutzerentscheidungen. | Spec-Kopf (Legende), Frontmatter `approved-scope`, Statuskopf, Revisionszeile 0.6, §1.2, §4.1, AC-30, §9.2, §10, §11.1, §17.10; Plan Kopfblock + alle U-Stellen |
| **K26** | **M2/M3 — DoD widerspricht der Verengung.** DoD Punkt 2 („V1…V8 = 0") und Punkt 12 (`--validate` → 0 nach W8-4) waren mit U-2/K22 unvereinbar. | **Umgestellt** auf „**V3 = 0 im AC-30-Scope**" bzw. auf die **Deltasperre**; der Widerspruch wird mit Verweis auf **OQ10** aufgelöst. | Plan DoD Punkt 2 und Punkt 12; Plan `W-VALIDATE-ROT` |
| **K27** | **M4 — `W-VALIDATE-ROT` in sich widersprüchlich** (Regelkopf, Zeile 2, Lesehinweis, Dokuzeile gegen Zeile 3). | **Alle vier** Stellen einheitlich auf „**kein Termin 0**" umgestellt bzw. als **überholt markiert**; Begründung: V3 bleibt **ERROR**. **Aussage der globalen Vorrangregel in K44 eingegrenzt.** | Plan `W-VALIDATE-ROT` (4 Stellen), W3-Block |
| **K28** | **M7 — `__all__` unvollständig:** `check_spec_plan_path_convention` (V8) fehlte, obwohl W6-2 über die Fassade registriert. | **Ergänzt** mit Herkunftskommentar `# W6-2 (docs_wiki)`; Vollständigkeitsaussage wiederhergestellt. | §4.1 Fassaden-`__all__` |
| **K29** | **M8 — V1-Test-Anker verwaist** nach der Verschiebung; §4-Testliste unvollständig. | AC-07/AC-08-Anker auf `tests/test_doc_freshness.py` umgezogen (K29-Hinweis im AC-Text); die **drei neuen Test-Dateien** mit Task-/Modul-/Test-Zuordnung in §4 aufgenommen. | §4 Test-Dateien, AC-07, AC-08 |
| **K30** | **m3 — K23 war eine unvollständige Korrekturliste** — Reststellen `README.md:721-723` / `:721-724` blieben stehen. | **Nachgezogen** an allen benannten Stellen; K23-Eintrag in §17.10.1 als unvollständig gekennzeichnet. | Plan 8 Stellen, Spec §17.10.1 |
| **K31** | **M11 — Selbstwiderspruch in der Abgrenzung:** §4.1 nannte `doc_renderer.py`/`doc_index.py` zu M1, sie sind **M2**. | Korrigiert auf `doc_facts.py` + `consistency/docs.py`; M2 unangetastet. | §4.1 Abgrenzungsabsatz |
| **K32** | **M10 — OQ10 ohne Plan-Task.** | **OQ10** als Zeile in „Entscheidungs-Tasks" (Owner, Frist, Wellenbezug W8) **+** Querverweis in Task **W8-4**. | Plan „Entscheidungs-Tasks", Task W8-4 |
| **K33** | **M6 — `W2-GATE-V1` nicht auf die neuen Testdateien gezogen** (sonst vakuum-grün). | `tests/test_doc_freshness.py` in **beide** Erfolgskriterien aufgenommen. | Plan `W2-GATE-V1` |
| **K34** | **m6 / `validator` N-2 — Checkbox-Split.** | Ist-Split auf **46 / 153** korrigiert (historische Rundenzeilen unverändert). | Plan L-1, Rev.-0.6-Zählung |
| **K35** | **m5 — Self-Review-Dateiliste unvollständig.** | `tests/test_doc_facts.py` (W2-7) + `tests/test_doc_facts_expected.py` (W2-5) ergänzt. | Plan Self-Review „Ownership" |
| **K36** | **M5 — W3-Block, RVW-1-Begründungstabelle:** V7 stand auf 10, V3 auf „Behoben wann W8-2". | V7 = **11**; V3 = „**2** → W8-2 · **25** → Follow-up 2026-10-11". | Plan W3-Block |
| **K37** | **M9 — Fußnote ⁅ fehlt** (referenziert, aber nicht definiert). | **Fußnote ⁵** mit V3-Dreiklassen-Tabelle angelegt. | Plan `W-GATE-TABLE` |
| **K38** | **Runde-1-Minor (unnummeriert) — Follow-up-Issue nur als Platzhalter.** | **Anlage** als benannter Schritt `F-ISSUE-ANLAGE` (2026-09-30) neben Abarbeitung (2026-10-11). | §17.10.3 |
| **K39** | **m1 + m2 — Taskzahl und OQ-Liste.** | **47 → 48** Tasks; OQ-Liste **OQ1…OQ10**. | Plan Kopf, Revisionszeile |
| **K40** | **m4 + m7 / `validator` N-3 — Historienummer, W2-Kette, `related`.** | „10 Wiki-Seiten" als **Historie** markiert (Ist-Stand 2026-09-26, maßgeblich **11**); `W2-1→…→W2-7` als **überholt** markiert; Spec-`related` um den Plan ergänzt. | Plan RVW-1-Absatz, Zyklenprüfung, Spec Frontmatter |

**Runde 2 — Eingang:** Concept-Review vom **2026-09-27**, `VERDICT: CHANGES_REQUESTED`,
**1 major · 4 minor**. Der Reviewer bestätigt ausdrücklich: Modulzuordnung **12/12 disjunkt**, DAG
**zyklusfrei**, PG-2a-Write-Sets **disjunkt**, **AC-30-Wortlaut unverändert**, **48** Tasks /
**199** Checkboxen, **W2-0-Vertrag vollständig und widerspruchsfrei**; die Restpunkte sind
ausschließlich **Zitier-/Audit-Hygiene**. **Keine** Korrektur dieser Runde berührt eine dieser
Invarianten. `status: APPROVED` unverändert; **kein** Revisions-Bump; **keine** AC/IC/R/OQ/Task-/
V-Check-ID umnummeriert.

| K | Befund (Review) | Behandlung | Ort |
|---|---|---|---|
| **K41** | **N1 (Major) — ID-Kollision im K-Namensraum, die die eigene Legende widerlegte.** `K26` war **dreifach** belegt (Spec §17.10.5 = M2/M3, Plan:1711 = M6, Plan:4217 = m6), `K27` war zusätzlich doppelt; **M5** und **M9** hatten **gar keine** K-Kennung. | Freie Kennungen **K33…K40** vergeben und **alle** Verweise umgezogen: Plan 1708, 1709, 1711 (→ **K33**), 4157, 4217 (→ **K34**), 4013 (→ **K35**), 2470 (→ **K36**, zugleich Reduktion „K24/K31" → „K24"), 2576 (→ **K37**), 3648 (→ **K40**). `K26` bleibt DoD (M2+M3) vorbehalten, `K27` der `W-VALIDATE-ROT`-Korrektur (M4). M5 → **K36**, M9 → **K37**. **M-Verweise in beiden Dokumenten deckungsgleich.** Die Legenden-Aussage (Spec:55–58) ist damit **wahr** und wird **mit den Tabellen K25…K40 (Runde 1) und K41…K45 (Runde 2) belegt**, nicht abgeschwächt. | Plan Kopfblock, 1708/1709/1711/2470/2576/3648/4013/4157/4217; Spec Legende |
| **K42** | **N2 — K-Bereich nicht nachgezogen.** Legende „K1…K31" (Spec:64) und Revisionsverweis „K25…K31" (Spec:286) wichen von §17.10.5 (K25…K32) ab. | Auf den Endstand der **Runde 2 gezogen**, der damals **K1…K40** / **K25…K40** war (Spec:64, Spec:292, Plan:179). **Nachgetragen (reine Bereichsangabe, ohne Bedeutungsänderung von K42):** Runde 2 hat den Katalog mit **K41…K45** verlängert, der **wahre Endstand ist daher `K1…K45` / `K25…K45`**; die drei Verweise wurden darauf nachgezogen. | Spec:64, Spec:292, Plan:179 |
| **K43** | **N3 — Reststelle.** Plan:925 nannte `README.md` „W8-2 Totverweise (`:721-724`)", wodurch K30s Aussage „an allen benannten Stellen" unzutreffend war. | Auf **`:722-723`** korrigiert (`:721`/`:724` existieren) — K30s Aussage ist damit **wahr**. | Plan:925 (File Structure, „Geändert (Doku/Agent)") |
| **K44** | **N4 — Widerspruch im selben `--validate`-Bullet + überzogene Absolutheitsaussage.** Im W8-4-Bullet standen „auch nach W8-4 rot ⇒ Deltasperre" und zwei Sätze später „spätester Termin 0 W8-4"; K27 behauptete „an keiner Stelle ein Widerspruch lesbar", obwohl acht Wiederholungen **keinen** lokalen Verweis tragen. | **Widerspruch aufgelöst:** der Nachsatz „spätester Termin 0 W8-4" ist aus dem Bullet **entfernt**; „W8-4" bleibt **nur** Termin für V2 und für die OQ10-Entscheidungsfrist. **K27s Absolutheitsaussage ehrlich gefasst** und mit den **benannten acht Stellen** dokumentiert — die kleinere Lösung wurde gewählt, weil acht zusätzliche Verweise acht Wellenblöcke sichtbar umschreiben würden, ohne Informationsgewinn. | Plan W8-4-Block (`--validate`-Zeile), Plan `W-VALIDATE-ROT` Vorrangregel |
| **K45** | **N5 — Wiki-Seiten-Zahl ohne Historien-Markierung.** Plan:396 nannte „**10** Seiten" ohne Datum. | Als **Historie** markiert (Ist-Stand **2026-09-26**) und der aktuelle Wert **11** danebengestellt (K24). | Plan RVW-1-Absatz |

### 17.11 Rev. 0.7 — E-5, E-6, E-7 und E-8 (entschieden 2026-09-27), Katalog K54…K58

**Eingang und Autorisierung.** Vier **bereits getroffene Entscheidungen des Nutzers** vom
**2026-09-27**, über `main_chat` an den `orchestrator` und hierher beauftragt. Sie sind
**verbindlich** und werden hier **nicht** neu bewertet, **nicht** zur Entscheidung gestellt und
**nicht** als offene Vorlage geführt:

| Kennung | Entscheidung in einem Satz | Owner der Entscheidung | Datum |
|---|---|---|---|
| **E-5** | V4 wird vom Scope „alle 205 nicht-Archiv-`docs/**.md` gegen `README.md`" auf den **README-Index-Scope** begrenzt; die **191** daraus entstehenden Findings werden **Follow-up**. | `main_chat` (Nutzer) | 2026-09-27 |
| **E-6** | Die zwei roten Volltests erhalten einen **eigenen Task W2-8** mit eigenem `Files:`, Agent, AK und **Position vor W2-7**. | `main_chat` (Nutzer) | 2026-09-27 |
| **E-7** | **V5** wird in das neue Modul `scripts/lib/consistency/docs_freshness_v5.py` ausgelagert, um die harte `< 600`-Grenze zu halten. | `main_chat` (Nutzer) | 2026-09-27 |
| **E-8** | `TASK_HEADER_RE` wird um die **Wellen-/Task-Header** erweitert; neuer Task **W2-9**; **Ledger-Writer einsetzbar ab W2-9**. | `main_chat` (Nutzer) | 2026-09-27 |

**Abgrenzung zu Rev. 0.6.** Rev. 0.6 war ein **echter** Revisions-Bump (U-1/U-2). **Rev. 0.7 ist
ebenfalls ein echter Revisions-Bump** — er ändert den **Scope eines bestehenden Checks** (V4), die
**Modulzuordnung** (E-7) und die **Taskmenge** (48 → **50**). `status: APPROVED` und
`approved: 2026-09-26` bleiben **unverändert**. **Keine** ID wird umnummeriert oder gestrichen;
**zwei** Task-IDs sind neu: **W2-8**, **W2-9**. **Keine** AC, kein IC **außer** der V4-Zeile in
IC-05, kein R, kein OQ, kein V-Check wird gestrichen; **kein** Sollwert wird gesenkt.

**Wortgleich und unangetastet bleiben:** §17.10 samt §17.10.1–§17.10.5, die Rev.-0.6-Blöcke, die
Revisionshistorie-Zeile `0.6`, die Korrekturrunden 1–4 des Plans (**K25…K53**) und deren
Entscheidungsvorlagen-Tabellen **E-5…E-8** (dort: „offen, unentschieden"). Diese Tabellen
dokumentieren den Stand **vor** der Entscheidung; **maßgeblich** sind die **Plan-Legende** und
dieser Abschnitt.

#### 17.11.1 Katalog K54…K58

| K | Befund / Entscheidung | Behandlung | Ort |
|---|---|---|---|
| **K54** | **E-5 — Mechanismuswahl.** „README-Index-Scope" lässt **zwei** technisch tragfähige Lesarten zu. Auswahlkriterien waren: (a) die **193** Findings auflösen (**K60**, nicht 191), (b) V4 **nicht vakuum-trivial** machen, (c) **IC-05 nicht brechen**. | **Gewählt: kategorie-genaue Strukturvollständigkeit des README-Index** (Definition in §17.11.2). **Verworfen und begründet: Rücknahme auf den Alt-Scope `docs/api/*.md`** (Begründung dort). **IC-05-Pin unverändert** (Check-ID `docs.readme_index`, **Signatur einargumentig** `(root: Path)` — **K59**, Severity ERROR, `file` = `README.md`). Die **193** werden **kein** AC, sondern **Follow-up `F-DOCS-README-INDEX-2026-09-27`** (§17.11.3) — **kein** Termin 0 in W0–W8, **kein** stilles Absenken. | IC-05 (V4-Zeile), §17.11.2, §17.11.3, Plan Rev. 0.7 (`W2-GATE-ERRORS`, W-VALIDATE-ROT, DoD 2) |
| **K55** | **E-5 — Grenzziehung gegen V2 und V3.** Nach der Umfangsänderung bestand die Gefahr, dass V4 mit V2 (beide `docs/`-Vollständigkeit) oder mit V3 (beide README/Link) verschmilzt und Doppelmeldungen entstehen. | **Drei disjunkte Fragen, explizit:** V2 = **Seite** fehlt in `docs/INDEX.md` (generiert, vollständig, alle nicht-Archiv-`docs/**.md`). V3 = **Linkziel** existiert nicht. V4 = **deklarierte Kategorie** des handgepflegten README-Index ist nicht repräsentiert; V4 prüft **nie** ein Linkziel. Ein toter Link in der Index-Region ist ein **V3**-Finding und **kein** V4-Finding. | §17.11.2, Plan Rev. 0.7 Task W2-6 Akzeptanz |
| **K56** | **E-6 und E-7 — Taskmenge und Modulmenge.** Die beiden Entscheidungen erzeugen **zwei** Tasks (**W2-8**, **W2-9**) und ein **fünftes** Modul; die Zählungen 48/199 und „4 Module" wurden dadurch überholt. | **Tasks 48 → 50**, **Checkboxen 199 → 207** (`[x]` **59** unverändert, `[ ]` **140 → 148**), Herleitung **44 × 4 + 5 × 5 + 1 × 6 = 207**. **Module 4 → 5** für die Dateicheck-Logik, Zuordnung **12/12 disjunkt und lückenlos** auf **5** Module. `docs_freshness.py` = **592** Z (Reserve **8**), `docs_freshness_v5.py` = **≈ 55–70** Z — **beide < 600**. **Die alten Aussagen bleiben wortgleich** und werden **hier** berichtigt (K18-/K42-Logik: der historische Block nennt seinen damaligen Stand). | Plan Rev. 0.7 (Frontmatter, Kopf, File Structure, PG-2, Matrices, L-1), §4.1, §9.2, §4 |
| **K57** | **E-8 — Werkzeugpfad.** `TASK_HEADER_RE` verlangt `### Task <id>`; dieser Plan schreibt `### W2-0:` ⇒ `_task_blocks()` leer ⇒ `unmatched={…}` ⇒ Exit 1. **Teilfehler (b) — „`TASK_ID_RE` erwartet zusätzlich `task-<ziffern>`" — ist in Rev. 0.7 FALSCH DIAGNOSTIZIERT und wird hiermit zurückgenommen (K66 / RVW-7-08):** `normalize_task_id("W2-0")` liefert **heute schon** `"W2-0"` (Durchreich-Zweig `return raw`, `plan_identity.py:73`, weil `TASK_ID_RE = ^task-[0-9]+$` (`:18`) nicht passt); **verhaltensgleich belegt** durch `normalize_task_id("custom") == "custom"` (`tests/test_plan_identity.py:100`) — der **`W2-0`-Pin wird in W2-9 Akzeptanz (f) neu angelegt**, **K74**). **Ein** Teilfehler, ein Werkzeug. | **Eigener Task W2-9** mit dem **einzigen** Teilfehler (a): alternativer Regex-Zweig für die Wellen-/Task-Header-Form. `normalize_task_id` / `TASK_ID_RE` bleiben **unangetastet**; eine „Reparatur" von (b) würde den Round-Trip **brechen** und ist **verboten** — (b) wird als **No-op-Pin** fortgeführt. **K62 / RVW-7-04 (additiv):** `scripts/lib/consistency/spec_plan.py` ist der **dritte** Konsument der Regex; sein hart kodiertes Dep-Token-Muster (`:570`) wird auf `W\d+-\d+` erweitert — sonst erzeugt `**W2-0**` die Phantom-ID `task-0`, `find_dependency_errors` meldet `deadlock:` und `validate_plan` bricht **vor** dem Overlap-Check ab, sodass die fail-closed-Ownership-Klausel **ganz ausfiele**. **Position Phase 0, vor PG-2a** ⇒ einsetzbar für **W2-6, W2-4, W2-8, W2-7**. Die K53-Interim-Regel (manuelles Abhaken) **endet mit W2-9** — ausdrücklich, nicht stillschweigend. | Plan Rev. 0.7 Task W2-9 (`Files:`, `Interfaces`, Akzeptanz (e)/(f)), DoD 14, Abschnitt L, DAG-Kanten 16 |
| **K58** | **Faktenkorrektur.** Auftrag und Korrekturrunden-4-Block nennen `TASK_HEADER_RE` als in `scripts/lib/plan_ledger.py` liegend. | **Gemessen:** Definition in `scripts/lib/plan_identity.py:27-30`; `plan_ledger.py` ist **Konsument** (Import `:25`, `finditer` `:71`, Tupel-Entpackung `:133`). W2-9 besitzt deshalb **beide** Dateien — `plan_ledger.py` nur, falls sich der Zwei-Gruppen-Vertrag ändert. | Plan Rev. 0.7 Task W2-9 `Files:`; Statuskopf Rev. 0.7 |

#### 17.11.2 E-5 — der gewählte Mechanismus, und die ausdrücklich verworfene Alternative

**Die beiden technisch tragfähigen Lesarten von „README-Index-Scope".** Beide sind gegen den
gemessenen Baum belegbar; sie unterscheiden sich in der **Granularität**, in der V4 die
Vollständigkeit prüft.

**Lesart A — kategorie-genaue Strukturvollständigkeit (GEWÄHLT).** V4 liest die
`##`-Überschrift, deren Text `Documentation Index` enthält (gemessen `README.md:347`), bis zur
nächsten `##`-Überschrift (gemessen `README.md:381`) — die **Index-Region**. Aus ihr werden die
**deklarierten** `docs/`-Kategorien extrahiert (jeder `docs/<kategorie>/`-Pfad, der in der Region
genannt wird; gemessen **7**: `docs/guides/`, `docs/howto/`, `docs/api/`, `docs/ui/`,
`docs/architecture/`, `docs/plans/`, `docs/se-cascade/`). Je Kategorie gilt **zwei** Bedingungen:
**(a) Existenz** — das Verzeichnis existiert; **(b) Repräsentation** — die Kategorie trägt
**mindestens einen** `docs/<kategorie>/…`-**Link** (Markdown-Linkziel) **innerhalb** der Region.
Fehlt die Überschrift ganz, liefert V4 **ein** Finding („kein Documentation-Index-Abschnitt") —
**nicht** eine leere Liste (fail-closed statt vakuum-grün).

**Die 7/6-Lesart ist entschieden, nicht offengelassen (K64 / RVW-7-06, Korrekturrunde 5).** Die
Extraktionsregel ist „**jeder `docs/<kategorie>/`-Pfad, der in der Region genannt wird**" — **nicht**
„jede `###`-Überschrift, die eine Kategorie nennt". Eine **überschriften**-basierte Lesart ergäbe
**6** statt **7**, weil `docs/architecture/` **ausschließlich** im Link `README.md:371` genannt
wird und in **keiner** `###`-Überschrift der Region steht. **Beide** Lesarten liefern denselben
Sollwert **1** (die einzige Lücke ist `docs/se-cascade/` in beiden); die Stabilität des Sollwerts ist
deshalb **kein** Argument gegen die Präzisierung. Die Regel steht **wortgleich** in **W2-6,
`Interfaces`**, damit Implementierung und Spec nicht auseinanderlaufen.

**Vorrangregel fail-closed vs. fail-soft (K65 / RVW-7-07, Korrekturrunde 5 — verbindlich, ersetzt
eine gleich behandelte Doppelausnahme).** Gemessen behandelt `docs_links.py:183` die Fälle
`README.md` fehlt **und** `docs/` fehlt **gemeinsam** (`not readme.exists() or not
docs_dir.is_dir()` ⇒ `[]`), ohne zu sagen, welcher Fall gilt, wenn `docs/` **existiert**,
`README.md` aber fehlt. **Reihenfolge, verbindlich:** **(1)** fehlt der **`docs/`-Verzeichnisbaum**,
liefert V4 **`[]`** — *fail-soft*, die **einzige** Ausnahme: ein Projekt ohne `docs/`-Baum ist
durch diese Prüfung nicht defekt, und „nicht repräsentierte Kategorie" wäre dort gegenstandslos, weil
es weder Region noch deklarierte Kategorien gibt. **(2)** existiert `docs/`, gilt die fail-closed-
Regel: fehlt `README.md` **oder** die `Documentation Index`-Überschrift, ist das **genau ein**
Finding.

**Lesart B — Seiten-genau innerhalb der Region (VERWORFEN).** Das *Suchgebiet* für den Linknachweis
wird auf die Index-Region begrenzt, die *geprüfte Seitenmenge* bleibt der ganze `docs/`-Baum. Das
ist ebenfalls baubar, scheitert aber an Kriterium (a): gemessen trägt die Region **12** `docs/`-**Seiten**
(7 aus `docs/api/`, 2 aus `docs/guides/`, 1 aus `docs/howto/`, 1 aus `docs/architecture/`, 1
aus `docs/plans/`), der nicht-Archiv-`docs/`-Baum hat **205** `.md`-Seiten ⇒ **205 − 12 = 193**
Findings — Lesart B liefert damit **dieselbe** Menge wie die unveränderte Prüfung und löst den
Blocker also **nicht** auf. **K60 / RVW-7-02 (Korrekturrunde 5):** diese Rechnung ist die
**korrekte**; die Herleitung „**191**" in §17.11.3 war ein **Einheitenfehler** und ist hiermit
ersetzt. Genau: die **14** in `README.md` genannten `docs/`-Pfade sind **12** `.md` + **2** `.html`
(`docs/ui/agent-graph.html`, `docs/ui/admin-ui.html`); der **205**-Bestand ist `.md`-only, die
`.html`-Pfade gehören **nicht** hinein. **205 − 12 = 193.**

**Die dritte, ebenfalls diskutierte Lesart — Rücknahme auf den Alt-Scope `docs/api/*.md`
(Lesart C) — ist die verworfene Alternative im Sinne des Auftrags.** Sie ist der Stand vor W2-6
(`docs.py:111`, Spec F18) und liefert am Baum gemessen **0** Findings, weil alle **sieben**
`docs/api/*.md` in `README.md:362-373` verlinkt sind. **Sie ist verworfen, weil sie gegen die drei
Auswahlkriterien fällt:**
1. **Kriterium (b) — sie ist vakuum-trivial.** Ein Check, der **0** Findings liefert, kann seine
   eigenen Schärfe **nicht** belegen; Lesart C feuert künftig nur, wenn jemand **im Verzeichnis
   `docs/api/`** eine Datei anlegt — einem Verzeichnis, das über W2–W8 **planmäßig** nicht wächst.
   Unter Lesart A hat V4 **heute** einen **echten** Befund (siehe unten), die Schärfe ist damit
   **belegt statt behauptet**.
2. **Kriterium (c) formal, Inhalt bricht sie:** IC-05s V4-Spalte („erweitert", F8/F23) und die
   Aussage „die bisherige Teilmenge bleibt eine **echte** Teilmenge der neuen Prüfung" werden zu
   einem **leeren** Satz, wenn die Prüfung exakt die alte Teilmenge ist. Das ist eine
   **Sollwert-/Vertragsauflösung** durch die Hintertür.
3. **Fachlich:** sie lässt **genau** die **sechs** anderen deklarierten Kategorien des
   README-Index strukturell ungeprüft — also genau die Blindstelle, unter der sich die 193
   unbemerkt angesammelt haben. Das ist der Grund, weshalb die Verallgemeinerung ersonnen wurde.

**Erwartungswert am gemessenen Baum (Lesart A).** **Genau 1 Finding**, Kategorie
`docs/se-cascade/`: die Region trägt für diese Kategorie **keinen** Link (gemessen: `README.md:378`
ist die Überschrift mit Backtick-Pfad, `:379` ist Prosa; der einzige `docs/se-cascade/`-Verweis
außerhalb der Region ist `README.md:654`, ebenfalls **kein** Link). Das ist ein **echter** Befund
der geforderten Art — eine im Index angekündigte Kategorie ohne Eintrag — und wird als
**Follow-up `F-DOCS-README-INDEX-SE-2026-09-27`** mit Owner und Termin geführt (**§17.11.3**), **nicht**
stillschweigend auf 0 gesetzt. **Ehrliche Grenze der Aussage:** V4 ist damit **kein** Sollwert-
Check mit Term 0 in W0–W8; maßgeblich ist die **Deltasperre** der Regel `W-VALIDATE-ROT`
(Plan, Spec §10 `--validate`).

**Warum Lesart A V2 und V3 nicht dupliziert (K55).** V2 liest `docs/INDEX.md` und ist
**seiten**-genau: **alle** nicht-Archiv-`docs/**.md` (ohne `docs/INDEX.md` selbst) müssen dort
stehen — und werden das ab **W3-6**, weil `docs/INDEX.md` **100 % generiert** ist (OQ6/OQ8,
IC-10/IC-13). V4 liest `README.md` und ist **kategorie**-genau: es fragt nichts über einzelne
Seiten. **Die 193 sind genau die Menge, die V2 abdeckt** — sie sind deshalb **kein** Fehler des
README, sondern eine **Eigenschaft des Formats** (die README ist ein **kuratierter** Einstieg mit
**Auswahl**, `docs/INDEX.md` ist der **vollständige** Index). V3 prüft, ob ein **Linkziel
existiert**; V4 prüft **nie** ein Linkziel. **Überschneidung:** keine — ein toter Link in der
Index-Region ist ein V3-Finding und **kein** V4-Finding, und umgekehrt kann V4 rot sein, während
V3 grün ist (fehlende Repräsentation bei existierendem Ziel).

**Was E-5 ausdrücklich *nicht* leistet.** (a) `--validate → 0` wird **nicht** erreichbar — weder
vorher noch nachher; maßgeblich ist die Deltasperre. (b) Die Vollständigkeit der `docs/`-Seiten
**als solcher** wird **nicht** geprüft — dafür ist V2 zuständig, und es prüft sie ab W3-6 gegen
die generierte Quelle. (c) Es entsteht **keine** neue AC; AC-12 bleibt an V2/W3-6 gebunden.

#### 17.11.3 Follow-up-Register — Fortsetzung (§17.10.3 bleibt die erste Hälfte)

**Regel unverändert:** ein Follow-up ist **kein** Sollwert und **kein** AC; er gilt als erledigt
**nur** über den jeweils genannten Nachweis, ausgewertet als **Zählwert** über `--json`
(kein Exit-Code, RVW-12). **Maßgeblich ist §17.10.3 + diese Fortsetzung.**

| ID | Gegenstand | Umfang | Owner | Termin | Entscheidungsweg / Nachweis |
|---|---|---|---|---|---|
| **`F-DOCS-README-INDEX-2026-09-27`** | **193** nicht-Archiv-`docs/**.md`, die in `README.md` **nicht** verlinkt sind. **K60 / RVW-7-02 (Korrekturrunde 5) — Herleitung korrigiert, die frühere „**191**" war ein Einheitenfehler:** Baseline-Messung 2026-09-27: `docs/`-Baum **205** `.md`-Seiten außerhalb `archive/`/`_archive/`; `README.md` nennt **14** `docs/`-Pfade, davon **12** `.md` und **2** `.html` (`docs/ui/agent-graph.html`, `docs/ui/admin-ui.html`) ⇒ **205 − 12 = 193**. **§17.11.2 Lesart B rechnete bereits 193**; dieser Registereintrag war die einzige abweichende Stelle | Kuratierte Verlinkung der **vom Projekt als Einstieg bestimmten** Seiten in `README.md`; **kein** Inhalts-Rewrite (NG-1), **kein** Zwang, **alle 205** zu verlinken — der vollständige Index ist `docs/INDEX.md` (V2) | **`developer`** | **2026-10-11** | Folge-Issue in `Popoboxxo/agent-meta`, Titel „Docs: 193 `docs/` pages not linked in README Documentation Index (V4/E-5)"; **Anlage** als benannter Schritt (Anlage-Datum **2026-09-30**, Muster `F-ISSUE-ANLAGE` aus §17.10.3). **Nachweis — beides zusammen, messbar (K60, ersetzt den vakuumen V4-Nachweis aus Rev. 0.7):** (a) die **Issue-Liste** nennt die betroffenen Seiten **namentlich** (Eindeutigkeit, nicht nur eine Zahl); (b) der **once-count** läuft **außerhalb** des Check-Frameworks als reiner Shell-Zählaufruf: `find docs -name '*.md' -not -path '*/archive/*' -not -path '*/_archive/*' -not -name 'INDEX.md' -printf '%p\n' \| while read -r f; do grep -qF "$f" README.md \|\| echo "$f"; done \| wc -l` ⇒ Baseline **193**, Ziel **0**. **K75 (Korrekturrunde 6) — die Baseline ist zukunftssicher gefasst:** der Aufruf enthält `-not -name 'INDEX.md'`, was der **V2-Konvention** entspricht (IC-05 V2-Zeile „ohne `docs/INDEX.md` selbst"). Das ist heute **folgenlos** (`docs/INDEX.md` existiert **nicht**; Universe **205** ⇒ **193** ✓), **ab W3-6** liefert **derselbe** Aufruf aber **192** (Universe **204**, davon **12** verlinkt), während die Baseline **193** bleibt. **Deshalb gilt die Zahl als `Universe 205 − 12 verlinkt = 193` mit Bezugszeitpunkt vor W3-6**; der **Sollwert 0** ist davon **nicht** betroffen. **Ausdrücklich kein `docs.readme_index`-Zählwert:** V4 zählt nach E-5 **deklarierte Kategorien**, nicht Seiten; der Zählwert ist bei Registrierung **0** bzw. **1** und **beobachtet diese Menge nicht** — als Nachweis wäre er **vakuum** |
| **`F-DOCS-README-INDEX-SE-2026-09-27`** | Kategorie **`docs/se-cascade/`** ist im README-Index deklariert (`README.md:378`) und trägt dort **keinen** Link | **ein** Link-Eintrag in der Index-Region, auf eine existierende Seite unter `docs/se-cascade/`; additiv, kein Rewrite | **`developer`** | **2026-10-11** | gemeinsam mit `F-DOCS-README-INDEX-2026-09-27`; **Nachweis:** Zählwert `docs.readme_index` = **0** Findings — das ist zugleich der Sollwert 0, den W2-6 für V4 führt. **Abgrenzung zu K60, ausdrücklich:** **hier** ist der `docs.readme_index`-Zählwert der **richtige** Nachweis, weil der Gegenstand eine **Kategorie** ist und genau das ist, was V4 zählt |

**Warum zwei Einträge und nicht einer:** die beiden Mengen haben **verschiedene** Gegenstände
(ein **Design**-Eintrag gegen einen **fehlenden** Eintrag) und **verschiedene** Erfüllungsbelege
(Kuratierung gegen ein Link-Edit). Zusammenführen würde den Nachweis des einen an den des anderen
koppeln und den jeweils eigenen Fortschritt unsichtbar machen. **Anlagestand:** beide teilen sich
den Anlage-Schritt und das Anlage-Datum **2026-09-30**; die Abarbeitung hat Termin **2026-10-11**.
**Ausdrücklich, weil es leicht verwechselt wird (K60):** die beiden Zeilen haben auch **zwei
verschiedene Nachweisformen** — nur die **zweite** ist ein `docs.readme_index`-Zählwert; die
**erste** braucht den Issue-Listen- plus Shell-Nachweis, weil ihr Gegenstand **Seiten** sind, die
V4 nicht zählt.

#### 17.11.4 Zyklenprüfung des W2-DAG nach E-6/E-7/E-8 (Plan-Seite, K57)

**Kanten neu:** `W2-0 → W2-9` (Werkzeugpfad vor allen noch offenen W2-Tasks) · `W2-4 → W2-8`
(E-6-Fix als letzter Schritt vor der Registrierung) · `W2-8 → W2-7`. **Kanten geändert:** `W2-7`
hängt zusätzlich an **W2-8**; `W2-4 → W2-7` bleibt bestehen.

**Topologische Ordnung:** `W2-1 → W2-2 → W2-0 → W2-9 → {W2-3 ‖ W2-5 ‖ W2-6} → W2-4 → W2-8 → W2-7`.

**Nachweis:** (a) **keine** Kante zeigt von einer höheren auf eine niedrigere Welle; die
Querwellenkanten (`W1-6 → W2-1`, `W0-4 → W2-1`, `W1-5 → W2-5`, `W2-1 → W3-4`, `W1-10 → W3-1`)
bleiben unverändert **Vorwärts**kanten. (b) Innerhalb W2 zeigen alle Kanten **vorwärts** in der
Reihenfolge oben; es existiert **keine** Kante `W2-9 → W2-0`, `W2-8 → W2-4` oder `W2-7 → W2-8`.
(c) **PG-2a = {W2-3, W2-5, W2-6}** bleibt bei **3** Members — die Grenze von **3** gleichzeitigen
Agents wird **nicht** überschritten, weil W2-9 **vor** und W2-4/W2-8 **nach** der Gruppe liegen.
(d) **Write-Set-Disjunktheit** ist gewahrt: W2-9 schreibt `scripts/lib/plan_identity.py`,
`scripts/lib/plan_ledger.py`, `tests/test_plan_identity.py`, `tests/test_plan_ledger_writer.py` —
**keine** dieser Dateien wird von einer anderen W2-Task geschrieben; W2-8 schreibt
`tests/test_knowledge_engine.py` und `tests/test_sharkord_service_name_migration.py` — ebenfalls
**disjunkt** zu allen W2-Write-Sets. (e) W2-4 schreibt nach E-7 **`docs_freshness_v5.py`** (neu)
und **`tests/test_doc_freshness_v5.py`** (neu) und **nicht mehr** `docs_freshness.py` /
`tests/test_doc_freshness.py` — die Kante `W2-5 → W2-4` wird damit **gegenstandslos** und bleibt als
**historische** Kante im Plan-Planungsbild sichtbar (ihre Begründung — gemeinsame Schreibmenge —
trifft nach E-7 nicht mehr zu); die **Wirkung** ist eine **Verschärfung**, keine Lockerung: W2-4
ist jetzt **in Phase B frei** und hängt nur noch an W2-5 (Bestand `docs_freshness.py` wird von
niemandem mehr berührt). **Korrekturrunde 5 (K62) — (d) ist um eine Datei zu ergänzen:** W2-9
schreibt zusätzlich **`scripts/lib/consistency/spec_plan.py`** (Dep-Token-Muster, `:570`), weil
`_parse_plan_tasks` der **dritte** Konsument von `TASK_HEADER_RE` ist. **Write-set-disjunkt bleibt
gewahrt:** `spec_plan.py` wird von **keiner** anderen W2-Task geschrieben (W2-7 schreibt
`consistency-check.py`, `docs.py`, `report.py`; W2-0 schrieb `spec_plan.py` **nur lesend** für den
Modul-Split) — die Disjunktheit wird damit **nicht** verletzt, sondern war ohne diese Ergänzung
eine **unvollständige** Aussage.
**Ergebnis: keine Zyklen. Der Graph ist ein DAG.**

#### 17.11.5 Korrekturrunde 5 (K59…K70) — Concept-Review über Rev. 0.7: Belege, Zähleinheit, Vorrang und drei unerreichbare Mechanismen

**Eingang und Autorisierung.** Concept-Review vom **2026-09-27** über Spec + Plan **Rev. 0.7**:
`VERDICT: CHANGES_REQUESTED` — **0 kritisch, 5 major, 4 minor, 2 info** (11 Findings
`RVW-7-01`…`RVW-7-11`); `validator`: **`PASS_WITH_NOTES`, 0 Blocker** (Notizen `n1`…`n5`).
Diese Runde setzt **keine** neue Entscheidung des Nutzers um: E-5…E-8 bleiben, wie entschieden.
**Kein Revisions-Bump** — `status: APPROVED`, `approved: 2026-09-26` und `revision: 0.7` bleiben
unverändert. **Kein** Produktionscode, **keine** Tests, **keine** Runner-Änderung, **keine**
Git-Mutation. Die Korrekturen wirken **ausschließlich auf Spec- und Plan-Text**; die dort
beschriebenen Codeänderungen sind **Pflichten für W2-6, W2-8 und W2-9**, keine ausgeführten
Änderungen. **Keine** Task-, AC-, IC-, R-, OQ-, V-Check- oder F-ID wurde umnummeriert oder
gestrichen; **keine** neue Task-ID, **keine** neue offene Frage, **kein** neuer Sollwert, **keine**
neue F-ID. §17.10 samt §17.10.1–§17.10.5, §17.11.1–§17.11.4, die Rev.-0.6-/Rev.-0.5-Blöcke und die
Korrekturrunden 1–4 des Plans bleiben **wortgleich**, soweit sie nicht durch einen ausdrücklich als
solchen gekennzeichneten Zusatz ergänzt wurden. **Die Spec-Legende bleibt eingefroren** auf
`K1…K45`; **maßgeblich** ist die **Plan-Legende** (`K1…K70`).

**Methodischer Vorbehalt, übernommen.** Die Read-Zeilennummern des Reviewers waren unzuverlässig;
**alle** Belege dieser Runde stammen aus **Grep/Read im Working Tree** und wurden **vor** dem Edit
verifiziert. **Zwei Abweichungen zwischen Review und Messung sind ausdrücklich festgehalten:**
**(a)** der Review nennt „**sechs**" V4-Tests, seine eigenen Listen ergeben **sieben** (4 **rot** +
3 **vakuum-grün mit falscher Semantik**); maßgeblich ist die **Messung**; **(b)** die Herleitung
„`205 − 14 = 191`" ist ein **Einheitenfehler** — maßgeblich ist **`205 − 12 = 193`**.

| K | Befund (Severity) | Behandlung | Ort |
|---|---|---|---|
| **K59** | **RVW-7-01 (major)** — der IC-05-Pin für V4 zitierte die Signatur `(root, config=None)`; **gemessen** ist der Pin **einargumentig** (`docs_links.py:167`, Docstring `:170-172`, Testpin `inspect.signature`) | Pin-Zitat auf `(root: Path) -> list[Finding]` korrigiert; die Form `(root, config=None)` wird **ausdrücklich** den **neun neuen** V-Checks zugeordnet. IC-05 (`:944-954` — **K72: nachgemessen**; die Angabe `:930-933` der Runde 5 war falsch und ist ein Codeblock in **IC-04**) trug **kein** Signatur-Literal — dort nur der gemessene Beleg `(root)` ergänzt | Kopf E-5, Revisionszeile `0.7`, IC-05, §17.11.1 K54, Plan (Kopf K54, W-GATE-TABLE, W2-6, W2-8) |
| **K60** | **RVW-7-02 (major)** — (i) die Zahl **191** mischt **Einheiten** (`205 − 14`, obwohl die **14** genannten Pfade **12** `.md` + **2** `.html` sind); (ii) der Nachweis war **vakuum**, weil `docs.readme_index` nach E-5 **Kategorien** zählt und die Seitenmenge nicht beobachtet | **(i)** `191` → **`193`** (`205 − 12`) an allen normativen Stellen; Lesart B in §17.11.2 rechnete bereits 193 ⇒ der **innere Widerspruch der Spec** ist zugunsten 193 aufgelöst. **(ii)** Nachweis = **Issue-Liste (namentlich) + once-count außerhalb V4** (konkreter Shell-Zählaufruf), Baseline **193** → Ziel **0**; `docs.readme_index` ist als Nachweis **ausdrücklich für unbrauchbar** erklärt — mit der ausdrücklichen Abgrenzung, dass er für den **Kategorie**-Eintrag weiterhin der richtige Nachweis **ist**. **K75 (Korrekturrunde 6 — Bezugszeitpunkt explizit):** der Zählaufruf enthält `-not -name 'INDEX.md'` (V2-Konvention); heute ist das **folgenlos** (`docs/INDEX.md` existiert **nicht**, Universe **205** ⇒ **193**), **ab W3-6** liefert **derselbe** Aufruf **192** (Universe **204**, davon **12** verlinkt). Die Baseline ist deshalb als **`Universe 205 − 12 verlinkt = 193`, Bezugszeitpunkt vor W3-6** gefasst; der **Sollwert 0** bleibt **zeitpunktunabhängig** | Kopf E-5, Revisionszeile `0.7`, §17.11.1 K54, §17.11.2, §17.11.3, §10 `--validate` (via K67), Plan (Kopf K54, W-GATE-TABLE, W-VALIDATE-ROT, W2-6, W2-8, Coverage-Matrix, DoD, L-1, Follow-up-Register) |
| **K61** | **RVW-7-03 (major)** — W2-6 nannte „drei V4-Tests"; im Working Tree pinnen **sieben** Tests die von E-5 **entfernte** Per-Seiten-Semantik, und **6 der 7** Fixtures schreiben `README.md` **ohne** `Documentation Index`-Überschrift ⇒ V4 feuert in diesen sechs Fixtures und W2-6 Schritt 3 ist **unerreichbar**. **K73 (Korrekturrunde 6 — Begründungsmenge präzisiert):** **R7 hat kein Fixture**, sondern liest den **echten** Baum (`tests/test_doc_index.py:394`, `REPO_ROOT` `:404-408`); er ist rot aus dem **in R7 selbst genannten** Grund (`message.split("'")[1]` auf einer Message, die nach E-5 die **Kategorie** nennt). **Die Klassifikation „alle sieben rot bzw. vakuum" bleibt korrekt** | Die **sieben** Tests werden **namentlich ersetzt, nicht angepasst** (Ersetzungstabelle mit Alt-Test → Ersatz-Test und Zustand in Plan W2-6). **Nicht-Vakuum-Nachweis** (Muster **K33**): `tests/test_doc_index.py` steht in **beide** Erfolgskriterien, und der Negativtest assertiert im selben Rumpf **auch** ein **nichtleeres** Ergebnis — sonst könnte ein Check, der nichts zurückgibt, den `== []`-Teil erfüllen | Plan W2-6 `Akzeptanz V4`, Schritte 1/3, L-1 W2-6, Kopf-Block K61 |
| **K62** | **RVW-7-04 (major)** — `TASK_HEADER_RE` hat **drei** Konsumenten; `_parse_plan_tasks` (`spec_plan.py:557`) nutzt dieselbe Regex, hat aber hart kodierte Dep-Tokens (`:570`) und speist `check_plan_file_overlap` (`:533`) — das Instrument der **fail-closed**-Ownership-Klausel. `spec_plan.py` fehlte in W2-9s `Files:` | **Dep-Token-Muster auf `W\d+-\d+` erweitern** und `scripts/lib/consistency/spec_plan.py` in W2-9s `Files:` aufnehmen, mit Testpflicht (Akzeptanz (e): 50 Tasks, keine Phantom-Dep-ID, kein `deadlock:`/`cycle detected`) **und** ausdrücklichem Festpinnen des **erwarteten** `docs.py`-Overlap. **Alternative verworfen** (begründet in Plan W2-9): ein erreichbares, aber kaputtes Instrument ist schlechter als ein ungenutztes — `check_spec_plan_workflow` ist für **jeden** Plan aufrufbar, und `task-N` wären für **jeden** Plan mit `W<n>-<k>`-Headern Phantom-IDs. **Kettenwirkung, die den Befund trägt:** `find_dependency_errors` meldet dangling dependency **vor** dem Overlap-Check, `validate_plan` kehrt dort ab ⇒ die Ownership-Prüfung **fiele ganz aus** statt falsch zu sein | Plan W2-9 (`Files`, `Interfaces`, Akzeptanz (e), `Verifikation`, Schritte 1–3), §17.11.1 K57, §17.11.4 (d) |
| **K63** | **RVW-7-05 (major)** — Mechanismus (ii) ist an W2-8s Position **unerreichbar** (Common-Gate entsteht erst in **W2-7**; V4 nimmt **kein** `config`; der Runner ruft die Altchecks unbedingt mit `_AGENT_META_ROOT`, `--root` leitet sie nicht um; Akzeptanz (d) schließt Produktivcode aus). (iii) nennt das Werkzeug nicht — `--json` gibt der **Runner**, nicht `sync.py --validate` | (ii) aus W2-8s zulässiger Liste **gestrichen** — als **spätere Option** mit allen drei Belegen erhalten; (i) und (iii) als **anwendbar** benannt, (iii) **mit festgeschriebenem Werkzeug** `python3 scripts/consistency-check.py --json --root <eigenes Fixture-Projekt>` und mit der Grenze, dass `--root` die Altchecks **nicht** umleitet — (iii) ist nur in der Form „nur die Dateien des Tests" zulässig | Plan W2-8 Akzeptanz (b), Kopf E-6 |
| **K64** | **RVW-7-06 (minor)** — die Extraktionsregel stand **nur** in der Spec; überschriften-only ergäbe **6** statt **7** (`docs/architecture/` nur im Link `README.md:371`) | Regel „**jeder `docs/<kategorie>/`-Pfad, der in der Region genannt wird**" **wortgleich** in W2-6 `Interfaces` übernommen, die **7/6-Lesart ausdrücklich entschieden** und vermerkt, dass beide Lesarten den Sollwert **1** liefern — Stabilität des Sollwerts ist **kein** Gegenargument | §17.11.2, Plan W2-6 `Interfaces` |
| **K65** | **RVW-7-07 (minor)** — fail-closed („Überschrift fehlt ⇒ 1") und fail-soft-Guard („kein `docs/` ⇒ `[]`") standen ohne **Vorrangregel** nebeneinander (`docs_links.py:183` behandelt beide Fälle **gemeinsam**) | **Vorrangregel** verbindlich: der **fail-soft-Guard zuerst** — fehlt der `docs/`-Baum, `[]` (einzige Ausnahme); bei vorhandenem `docs/` gilt **fail-closed** (fehlende `README.md` **oder** Überschrift ⇒ **1**). Zwei **neue** Tests in W2-6 | §17.11.2, Plan W2-6 `Interfaces` |
| **K66** | **RVW-7-08 (minor)** — K57-Teilfehler (b) war **falsch diagnostiziert**: `normalize_task_id("W2-0")` liefert **heute schon** `"W2-0"` (Durchreich-Zweig `return raw`, `plan_identity.py:73`; **verhaltensgleich belegt** durch `normalize_task_id("custom") == "custom"`, `tests/test_plan_identity.py:100` — **K74**: der Anker `:96-101` der Runde 5 war falsch, dort steht `test_normalize_task_id` **ohne** `"W2-0"`; der `W2-0`-Pin wird in Akzeptanz (f) **neu** angelegt) | Gemessenes Verhalten ausgesagt, (b) **zurückgenommen**, W2-9 auf (a) beschränkt, (b) als **No-op-Pin** fortgeführt; eine „Reparatur" von (b) ist als **Round-Trip-brechend** und damit **verboten** markiert | §17.11.1 K57, Kopf E-8, Plan Kopf K57 + W2-9 |
| **K67** | **RVW-7-09 (minor)** — V4 fehlte in den späteren `--validate`-rot-Aufzählungen, obwohl es **heute registriert** ist (1 ERROR); der heutige Arbeitsbaum-Zustand des V4-Teils von W2-6 (Generalisierung) als Ursache der zwei roten Volltests war ungedeckt | V4 in **beiden** späteren `W-VALIDATE-ROT`-Zeilen (inkl. Owner-Spalte), in **§10 `--validate`** und im Kopf ergänzt; die Aufzählung war damit **unvollständig**, nicht falsch — das ist so festgehalten | §10 `--validate`, Kopf E-6, Plan `W-VALIDATE-ROT` (4 Zeilen), L-1 W2-6 |
| **K68** | **RVW-7-10 (info)** — Docstrings nennen weiter den Vor-E-5-Scope (`docs_links.py:8-10`, `:168-177`) | Als **Plan-Pflicht für W2-6** festgeschrieben (W2-6 ist der einzige Task, der `docs_links.py` schreibt). **Hier wird kein Code geändert** | Plan W2-6 `Akzeptanz V4` + Schritt 2 |
| **K69** | **RVW-7-11 (info)** — Korrekturrunde 4 ohne lokalen Supersessions-Verweis | **Entscheidung: keine Änderung an Runde 4**, mit Begründung (siehe Plan, Korrekturrunde 5). Der Vorrang ist **global** regelkonform hergestellt; ein eingefügter Verweis würde die Wortgleichheit brechen, die diese Runde schützt | Plan Korrekturrunde 5, Kopf (kein Eingriff in Plan `:5626`) |
| **K70** | **Validator-Notizen `n1`…`n5`** | Jede **einzeln** zugeordnet: `n1` bewusste Nicht-Zuordnung (Rev.-0.2-Block, wortgleich, vorbestehend), `n2` **behoben** (Präzisierung §16), `n3`/`n4` bestätigte Bewusstanten, `n5` kosmetische Nicht-Zuordnung (Legende maßgeblich). Volltext: Plan, Abschnitt „Korrekturrunde 5" | §16 (`n2`), Plan Korrekturrunde 5 |

**Neu gemessene Zahlen dieser Runde (Methode offengelegt).** Neu gemessen per Grep/Read: Tasks
**50** (W2: **10**, W0: **6** — **`W0-5` existiert nicht**), Checkboxen `[x]` **59** / `[ ]` **148** /
gesamt **207** (**keine** Checkbox in dieser Runde gesetzt, gestrichen oder ergänzt), K-Obergrenze
**K70**, `README.md`-Linkziele **14** = **12** `.md` + **2** `.html`, davon in der Index-Region
**7** deklarierte Kategorien (überschriften-only **6**), V4-Sollwert **1**. **Nicht** neu gemessen und
als **übernommene Baseline-Messung 2026-09-27** gekennzeichnet: der `docs/`-`.md`-Bestand **205** (in
dieser Runde stand kein Shell-Werkzeug zur Verfügung). **Die Herleitung bleibt trotzdem prüfbar:**
der Register-Nachweis ist ein **konkreter Shell-Zählaufruf** (K60), mit dem der Bestand in einer
Zeile neu gezählt werden kann — der Zählwert hängt damit nicht an einer unüberprüfbaren Behauptung.


#### 17.11.6 Korrekturrunde 6 (K71…K75) — zweites Concept-Review über Rev. 0.7: Write-Set-Inventare, Anker, Fixture-Begründung und Baseline-Bezugszeitpunkt

**Eingang und Autorisierung.** Concept-Review vom **2026-09-27** (zweite Runde über denselben
Revisionsstand) über Spec + Plan **Rev. 0.7**: `VERDICT: CHANGES_REQUESTED` — **0 kritisch,
1 major, 3 minor, 1 info** (5 Findings: `NEU-1`…`NEU-4`, `INFO-1`). **Rein mechanisch, kein erneuter
Sachentscheid:** alle 11 Findings der ersten Runde waren am Code verifiziert erledigt, beide
Autor-Korrekturen (7 V4-Tests, **193** statt 191) waren unabhängig bestätigt. **Kein
Revisions-Bump** — `status: APPROVED`, `approved: 2026-09-26` und `revision: 0.7` bleiben
unverändert. **Kein** Produktionscode, **keine** Tests, **keine** Runner-Änderung, **keine**
Git-Mutation, **keine** Löschung oder Änderung der **3 uncommitteten W2-6-Dateien**
(`scripts/lib/consistency/docs_index.py`, `tests/test_doc_index.py`,
`scripts/lib/consistency/docs_links.py`). **Keine** Checkbox gesetzt, gestrichen oder ergänzt.
**Keine** Task-, AC-, IC-, R-, OQ-, V-Check- oder F-ID umnummeriert oder gestrichen; **keine**
neue Task-ID, **keine** neue offene Frage, **kein** neuer Sollwert, **keine** neue F-ID.
§17.10 samt §17.10.1–§17.10.5, §17.11.1–§17.11.5, die Rev.-0.6-/Rev.-0.5-Blöcke und die
Korrekturrunden 1–5 des Plans bleiben **wortgleich**, soweit sie nicht durch einen ausdrücklich als
solchen gekennzeichneten Zusatz ergänzt wurden. **Die Spec-Legende bleibt eingefroren** auf
`K1…K45`; **maßgeblich** ist die **Plan-Legende** (`K1…K76` — **gemessen** am Working Tree 2026-09-29: Plan `:536` „`K-*` (K1…**K76**)“, Plan `:6960` „**K76 bleibt die höchste K-Kennung**“; Plan Rev. 0.7 bleibt unverändert).

**Methodischer Vorbehalt, in beide Richtungen.** Die `grep`-/`read`-Zeilennummern beider Reviews sind
in diesem Projekt **nachweislich unzuverlässig**; deshalb wurde **jeder** Anker **vor** dem Edit per
Grep am Working Tree verifiziert. **Zwei Anker-Korrekturungen der ersten Runde waren selbst falsch**
(NEU-3) und die vom Review genannten Fundstellen wichen von den gemessenen ab (u. a.
`tests/test_plan_index.py` → real `tests/test_plan_identity.py`; Plan `W2-9 Interfaces` → real
**W2-6 Akzeptanz V4**). **Maßgeblich ist die Messung, nicht die Fundstellenzahl des Reviews.**

| K | Befund | Behebung | Ort |
|---|---|---|---|
| **K71** | **NEU-1 (major)** — K62 hat `scripts/lib/consistency/spec_plan.py` korrekt in W2-9s `Files:` aufgenommen, aber **keine** der daraus abgeleiteten, im Plan als **maßgeblich** bezeichneten Stellen mitgezogen: Ownership-Matrix (W2-9: **4** `owns`-Zeilen), Matrix-Narrativ („die **vier** Werkzeug-/Testdateien", „die **sechs** neuen Dateien"), Step-Agent-Map (4 Dateien), `File Structure`, Rollback W2, **vier** Self-Review-Summenlisten. Die „Betroffene Stellen"-Liste der Runde 5 nannte **weder** Matrix **noch** Step-Agent-Map ⇒ **keine dokumentierte Ausnahme**. **Keine Kollision** (kein anderer Task führt `spec_plan.py`) | **Alle** Inventare auf den neuen Zählstand gezogen: neue Matrix-Zeile `spec_plan.py | owns (Modify, Dep-Token-Muster :570)`; Narrativ „**fünf**" bzw. „**sieben**"; Step-Agent-Map, `File Structure` (neuer Eintrag), Rollback (neue `git checkout`-Zeile) und die **vier** Summenlisten; „Betroffene Stellen" der Runde 6 nennt **alle** betroffenen Stellen. **Neu gemessen:** W2-9 = **5** `owns`-Zeilen, W2-9 + W2-8 = **7**, Rev.-0.7-Dateizeilen der Matrix = **9** — der Matrix-Kopf „**9 Dateizeilen**" war damit **richtig**, die Tabelle war die unvollständige Stelle | Plan: Ownership-Matrix (Kopf, Zeile, Narrativ ×2), Step-Agent-Map, `File Structure`, Rollback W2, „Warum W2 ‖ W3 parallel", Self-Review ×4, Kopf-Block K71, **neue** Liste der betroffenen Stellen |
| **K72** | **NEU-3 (minor)** — drei falsche `Datei:Zeile`-Anker: IC-05 `:930-933` (real **`:944-954`**; `:930-933` ist ein Codeblock in **IC-04**), Revisionszeile `0.7` `:367` (real **`:386`**; `:383` ist die `0.5`-Zeile der Revisionstabelle und `:367` die **Leerzeile** unter „Verifikations-Legende" — die **VERIFIED**-Zeile ist `:370`), §10-`--validate` `:2235` (real **`:2257-2261`**; `:2235` steht in §9.2). **Re-Review 3 (R3-1):** der Revisionszeilen-Anker **einmal nachgemessen** = `:386` — K72 bleibt derselbe Eintrag, **keine** neue K-ID | An **allen** Fundstellen umgestellt. **Die Aussagen waren je richtig** — falsch waren nur die Anker, und genau das verletzt §16 („jeder `Datei:Zeile`-Verweis wurde gelesen") | Plan-Kopf K59, Plan-Register RVW-7-01 und RVW-7-09, §17.11.5 K59 |
| **K73** | **NEU-4 (minor)** — „**alle** sieben Fixtures schreiben `README_RELPATH`" ist falsch: **R7 hat kein Fixture**, sondern liest den echten Baum (`tests/test_doc_index.py:394`, `REPO_ROOT` `:404-408`) | Auf „**6 der 7** Fixtures" präzisiert, **R7 gesondert** begründet (`message.split("'")[1]` auf einer Message, die nach E-5 die **Kategorie** nennt). **Die Klassifikation „alle sieben rot bzw. vakuum" bleibt korrekt** — die Begründung trug für 6 statt 7 | Plan-Kopf K61, Plan W2-6 Akzeptanz V4, §17.11.5 K61 |
| **K74** | **NEU-2 (minor)** — der Beleg `tests/test_plan_identity.py:96-101` ist falsch: dort steht `test_normalize_task_id` mit `"3"/"TASK-3"/"task-3"/"custom"/"task-"` — **kein** `"W2-0"` | Auf den realen Anker umgestellt: „verhaltensgleich abgedeckt durch `normalize_task_id("custom") == "custom"` (`:100`, **derselbe** Durchreich-Zweig); der `W2-0`-Pin wird in **Akzeptanz (f) neu angelegt**". **Der Sachstand ist richtig** und **kein** Schutz geht verloren | §17.11.1 K57, §17.11.5 K66, Plan-Kopf K57, Plan-Kopf K66, Plan W2-9 `Interfaces`, Plan-Register RVW-7-08 |
| **K75** | **INFO-1 (info)** — der once-count enthält `-not -name 'INDEX.md'`: heute **folgenlos** (`docs/INDEX.md` existiert nicht, Universe **205** ⇒ **193** ✓), **ab W3-6** liefert derselbe Aufruf **192** bei bleibender Baseline **193** | Baseline **zukunftssicher** gefasst als **`Universe 205 − 12 verlinkt = 193`, Bezugszeitpunkt vor W3-6**; Exclusion begründet (V2-Konvention, IC-05 V2-Zeile) und der **Sollwert 0** als **zeitpunktunabhängig** vermerkt. **Kein Baseline-Wert und kein Sollwert wurde geändert** | §17.11.3 Register, §17.11.5 K60, Plan-Kopf K60, Plan Follow-up-Register, Plan-Register RVW-7-02 |

**Bewusste Nicht-Zuordnung (K71) — der historische Entscheidungs-Record bleibt wortgleich.** Die
Spalte „Folge im Plan" des Records `E-8` nennt „Ownership-Matrix (4 Zeilen + 2 Spalten)" und vier
Dateien in `Files:`. Der Abschnitt „Entscheidungs-Abschluss Rev. 0.7" ist **wortgleich
festgeschrieben** und dokumentiert den **datierten** Stand vom 2026-09-27; ein Edit würde genau die
Wortgleichheit brechen, die K36/K42 als Fehler behandelt. **Aufgelöst über die K71-Lesart-Regel:**
jede Stelle, die W2-9s Write-Set **ohne** `spec_plan.py` nennt, meint den Stand **vor** K62.

**Bewusste Nicht-Zuordnung (K72/K71) — Katalog-Obergrenzen in Fremd-Blöcken.** Der Spec-Statuskopf
und §17.11.5 nennen als „maßgeblich" die **Plan-Legende** mit dem damaligen Stand `K1…K70`; beide
Stellen bleiben **wortgleich** und tragen ihren **datierten** Stand. **Vorrang** (Muster K36/K42):
**maßgeblich ist die Plan-Legende `K1…K76`** (RVW10-1: **gemessener** Stand, Plan `:536`/`:6960`; `K1…K75` war der Stand dieser Korrekturrunde).

**Neu gemessene Zahlen dieser Runde (Methode offengelegt).** Neu gemessen per Grep am Working Tree:
Tasks **50** (W2: **10**, W0: **6** — `W0-5` existiert nicht), Checkboxen `[x]` **59** / `[ ]`
**148** / gesamt **207** (**keine** Checkbox in dieser Runde gesetzt, gestrichen oder ergänzt; die
Partitionsmessung `44 × 4 + 5 × 5 + 1 × 6 = 207` wurde **verifiziert** — 5er-Schritte in W2-1, W2-0,
W2-7, W4-3, W5-2; der einzige 6er-Schritt in W8-4), K-Obergrenze **K75** (Runde 6 = K71…K75), `owns`-
Zeilen der Matrix-Spalte **W2-9** = **5** (vorher 4), Rev.-0.7-Dateizeilen der Matrix = **9**
(vorher 8), Fixtures der 7 V4-Tests = **6** (`tests/test_doc_index.py:280`, `:294`, `:309`, `:320`,
`:336`, `:350`; **R7** ohne Fixture), `docs/`-Linkziele in `README.md` **14** = **12** `.md` + **2**
`.html`. **Nicht** neu gemessen und als **übernommene Baseline-Messung 2026-09-27** gekennzeichnet:
der `docs/`-`.md`-Bestand **205**; die Herleitung `205 − 12 = 193` bleibt über den **konkreten**
Shell-Zählaufruf (K60) in **einer** Zeile nachprüfbar. **Keine neue F-ID** (Bestand unverändert).


**Fail-closed-Klausel (K20, fortgeltend).** Wird eine Ownership-Zeile so geändert, dass
`check_plan_file_overlap` für eine Parallelgruppe **zwei** Tasks mit gemeinsamer Schreibmenge
meldet, eine Parallelgruppe **mehr als 3** gleichzeitige Agents umfassen würde, die Kantenliste
einen **Zyklus** enthält, oder ein Task eine Datei schreiben müsste, die ein **früherer** Task
derselben Gruppe bereits geschrieben hat, gilt: **die betroffene Task wird nicht gestartet**, der
Plan wird **nicht** stillschweigend angepasst, und es ist ein **korrigierter Plan** mit neuer
Ownership-Matrix **und** neuer Zyklenprüfung vorzulegen (Owner `orchestrator`, Entscheidungsweg
`main_chat`). **Unverändert** in Kraft.

---

### 17.12 Rev. 0.8 — agent-meta-Ausnahme im KE-Vorrang-Gate (2026-09-29)

**Eingang.** Systemdesign **fertig vorliegend**:
`docs/specs/2026-09-25-repository-documentation-consolidation-design-agent-meta-exception.md`
(`status: draft`, `revision: 0.1`, concept-architect, 2026-09-29) — DECISION-1…DECISION-4,
P-1…P-5, K-1…K-5, E-9…E-13. **Jede Kernangabe wurde am Working Tree nachgemessen**, nicht aus
dem Entwurf übernommen; die Abweichungen zwischen Entwurf und Messung sind in
**§17.12.5, V-D3** benannt.

**Vorentscheidung des Nutzers — bereits getroffen, hier NICHT neu bewertet:** explizite
**agent-meta-Ausnahme**, damit **W3-6** `docs/INDEX.md` schreiben kann; die **Knowledge Engine
bleibt für Consumer-Projekte autoritativ**; **keine** globale Umstellung von `index.mode`.

**Warum eine Spec-Revision und keine stille Korrekturrunde.** P-1…P-5 betreffen ausschließlich
**normative** Stellen (IC-Vertrag, Config-Tabelle, Akzeptanzkriterium, Risikotabelle). Keine davon
ist ein versehentlicher Fehler. Deshalb `revision: 0.8` **mit** Bump, und deshalb ist der neue
Umfang als **noch nicht freigegeben** gekennzeichnet (§Kopf, Frontmatter `pending-approval:`,
Revisionszeile 0.8).

#### 17.12.1 Verdictschnitt — P-1…P-5 (inkl. **P-3 (e)**, inhaltliche Pflichtänderungen, **ZUR USER-FREIGABE AUSSTEHEND**) und K-1…K-5 (Korrekturen, ohne Freigabebedarf)

> **Zählauflösung (RVW9-5).** Diese Tabelle trägt **fünf** P-Elemente: **P-1, P-2, P-3,
> P-4, P-5**. **`P-3-E` ist kein sechstes P-Element**, sondern die **fünfte Tabellenzeile** — die
> Teilstelle **(e)** von **P-3** (RVW8-2). P-3 (e) präzisiert **ausschließlich den Sollwert-Zähler
> in AC-39** und die **Registrierung der zweiten Mengen-Pin**; am Gegenstand von P-3 (der siebten
> Zeile der IC-22-Tabelle) ändert sie **nichts**. Deshalb bleibt es bei „**P-1…P-5**" in
> Frontmatter `approved-scope`, §15 Trace-Anker und Ergebnisprotokoll; die Schreibweisen
> „**P-3-E**" (P-3-Zeile, Kopfblock) und „**P-3 (e)**" (Tabellenkopf, Revisionszeilen) bezeichnen
> **dieselbe** Zeile. **Im Freigabe-Snapshot an den Nutzer wird sie ausdrücklich mitgeführt.**

| ID | Was ändert sich | Warum es **inhaltlich** ist | Blast-Radius | Ort in dieser Spec |
|---|---|---|---|---|
| **P-1** | Die IC-13-Tabellenzeile „`resolve_index_mode(config)[0] == "knowledge-engine"` ⇒ **kein** `docs/INDEX.md` schreiben" wird **bedingt**; zwei Zeilen kommen hinzu (Override ⇒ schreiben; unbekannter Wert ⇒ fail-closed). | Die alte Zeile ist **absolut**: bei `enabled: true` + KE-Modus ist Schreiben **immer** verboten. Die Ausnahme kehrt das für ein deklariertes Projekt um — das ist **ein neuer Vertrag**, kein Formulierungsfehler. Der Vertrag wird **nur** verengt, nie erweitert (IC-25 Wertetabelle). | 1 Code-Bedingung in 1 Funktion (`doc_renderer.py:702-703`), 1 Config-Wert in 1 Projekt. **Null** Wirkung auf Consumer (kein Fixture setzt den Key, IC-26/6). | IC-13, IC-25 |
| **P-2** | IC-15 erhält die **zweite Schreibbedingung** „Ziel existiert **nicht** ⇒ Voll-Index anlegen", unabhängig von `resolve_index_mode()`. | IC-15 regelt **nur** den Skeleton-Fall und setzt `file-index` voraus. In agent-meta entsteht die Datei **ohne** Skeleton (Neuanlage). IC-15 wird dadurch **nicht falsch, sondern unvollständig** — die Lücke ist genau der Fall, den W3-6 braucht. | Rein **ergänzend**; der Skeleton-Pfad und alle Szenarien 54/55/56 bleiben wortgleich. | IC-15 |
| **P-3** | IC-22-Tabelle: **siebte** Zeile `docs-consolidation.index-owner`; der Absatz „**für alle sechs** Keys" wird zu „**sieben**". | Die Tabelle **zählt** die Gate-/Rollback-Keys auf; ein fehlender Key ist in einer fail-off-Spezifikation eine **Lücke**, kein Detail. | 1 Config-Key, 1 Schema-Property, 1 Enum-Default. Consumer: **kein** neues Feld, **null** Verhaltensaenderung (IC-26/6). | IC-22 |
| **P-3 (e)** *(= „P-3-E", **Teilstelle (e) von P-3**, **kein sechstes P-Element** — RVW9-5; Erweiterung, **selbst gemessen**)* | **AC-39** wird von „**genau** den **sechs** Properties" auf den **gemessenen** Stand umgestellt: Block = **sechs** Properties **nach** Rev. 0.8, **fünf** davor. | Die Zahl **sechs** war **schon in Rev. 0.7 falsch**: `config/project-config.schema.json:2424-2469` hat **fünf** Properties, und der **gepinte** Test `tests/test_docs_consolidation_migration.py:45-51` ebenfalls **fünf** (geprüft `:99-103`, Mengen-Assertion `:101`). Der sechste Eintrag der IC-22-**Tabelle** ist `knowledge-engine.okf.index-mode` und liegt in einem **anderen** Block — eine Verwechslung von Tabelle und Block. `index-owner` macht sie **nicht** richtiger. **Deshalb hiermit berichtigt** statt fortgeschrieben. **An P-3 selbst ändert diese Zeile nichts** — P-3 bleibt „siebte Zeile der IC-22-Tabelle". | 1 Sollwert-Zahl in **einem** AC; **zwei** Test-Pins, je **Erweiterung einer Menge** (T-3 a/b, §17.12.4); **K-78:** `_IC22_ABSENCE_DEFAULTS` (`tests/test_doc_renderer.py:1092-1098`) ist die **zweite** harte Sollwert-Änderung — ohne sie bleibt W3-6 rot | AC-39 |
| **P-4** | AC-21s zweiter Given/When/Then-Block wird **bedingt** formuliert („`index-owner` **nicht** gesetzt"); **AC-42…AC-46** kommen hinzu. | AC-21 machte die KE-Autorität zur **ungefähren** Vorbedingung. Mit der Ausnahme ist sie **bedingt** — ohne zusätzliche AK widerspräche der Test der Spec, sobald agent-meta `index-owner` setzt. | **Rein** additional: **kein** bestehendes AC wird gestrichen oder in seinen Sollwerten gesenkt; AC-20/AC-21/AC-23/AC-24/AC-38 bleiben in ihren Sollwerten **wortgleich**. | AC-21, AC-42…AC-46 |
| **P-5** | R7s Mitigation-Tabelle erhält einen **dritten** Hebel (`index-owner`) und den Nachweis, dass das Risiko in agent-meta **sinkt**. | Die Mitigation-Tabelle ist **normativ** (sie begründet, warum R7 beherrscht ist). Ein dritter Hebel ändert die Begründung; die Risiko-Aussage selbst bleibt in der Substanz richtig. | Risikotabelle; **kein** Sollwert, **kein** R-Id, **keine** neue Welle. | R7 |

| ID | Korrektur | Art | Nachweis |
|---|---|---|---|
| **K-1** | Docstring `_index_mode_block_reason` (`doc_renderer.py:669-672`): „Scenario 52 asserts no `docs/INDEX.md` is written there … so the generator has nothing to do **in that project**" gilt für agent-meta ab dem Key-Set **nicht** mehr. | Reiner **Text**, **kein** Verhalten. | `doc_renderer.py:669-672` gelesen; Szenario-52-Aussage selbst bleibt **richtig** (Szenario 52 setzt den Key nicht). |
| **K-2** | Docstring `_e2e_config()` (`tests/test_doc_renderer.py:3209-3223`) behauptet, IC-13/IC-15 machten die KE zum „authoritative owner of `docs/INDEX.md`" **für agent-metas Konfiguration**. Nach dem Key ist das für agent-meta **falsch**. | Reiner **Text**; der **Sollwert** von `test_skeleton_replaced_once` bleibt **unverändert** (Begründung §17.12.4). Die Ergänzung muss **namentlich** sagen, dass `_e2e_config()` eine **abweichende** Konfiguration benutzt (`knowledge-engine: {"enabled": False}`, `:3237`) und **warum**. | `tests/test_doc_renderer.py:3209-3223` gelesen, `:3237` gelesen, `test_skeleton_replaced_once` `:3258` gelesen. |
| **K-3** | Zählkommentar `tests/test_docs_consolidation_migration.py:42-44` („IC-22 enumerates six rows; five of them are `docs-consolidation.*`") ⇒ **sieben / sechs**. **RVW9-3: das Ordnungswort in `:43` ist mitzuziehen** — nach der IC-22-Tabelle (sieben Zeilen, `:1845-1851`, KE-Key in `:1851`) ist `knowledge-engine.okf.index-mode` die **siebte**, nicht die sechste Zeile; Zieltext `# **seventh** (knowledge-engine.okf.index-mode) belongs to a different block and is`. | Reiner **Kommentar** — die Zahlen im **Text** der Zeilen 42-44. | **V-D4** (§17.12.5), **neu gemessen 2026-09-29 (K-77, RVW8-1):** der Kommentar **existiert**; Zeile `:42` und `:44` per Grep belegt, `:43` per Grep belegt. **Die frühere Aussage dieser Zelle („die Zeile ist leer") war eine Fehlmessung des Belegwerkzeugs, nicht des Working Tree** — das Read-Tool rendert diese drei Kommentarzeilen leer, das Grep-Tool nicht. Der Träger der **Property-Menge** bleibt `_EXPECTED_PROPERTIES` `:45-51` (als **T-3** geführt). |
| **K-4** | **Zwei veraltete Zeilenanker:** `spec_plan_scaffold.py:62-68` → **`:115-121`**; `spec_plan_scaffold.py:40-44` → **`:80-97`**. | Reine **Anker**, **kein** Sollwert. Unabhängig von dieser Änderung — der Anker-Drift bestand bereits. | **Gemessen:** `scaffold_spec_plan_dirs` beginnt bei `spec_plan_scaffold.py:100`, der Modus-Zweig bei `:115-116` (Datei-Ende `:121`); `resolve_index_mode` beginnt bei `:80` und endet bei `:97`. Fundstellen **namenbasiert**: IC-12 (Aufrufreihenfolge, Begründungsabsatz), IC-13 (Situationstabelle), AC-38 (Zweite-Abschirmung-Liste). |
| **K-5** | `doc_renderer.py:685-686` („The two owners above are the complete list of what forbids a write") — **BLEIBT WORTWÖRTLICH STHEN.** | Ausdrücklich als **nicht** zu ändern vermerkt, damit der Guard nicht als Widerspruch missverstanden wird. Die Liste bleibt **geschlossen bei zwei**, weil IC-25 keinen Eigentümer **hinzufügt**, sondern nur den einen **Auslöser** stilllegt (DECISION-2). | `doc_renderer.py:682-694` gelesen; die Liste am Docstring-Anfang (`:666-676`) bleibt bei zwei Eigentümern. |

#### 17.12.2 Entscheidungsvorlagen E-9…E-13 (einschließlich **E-13c**) — **OFFEN, nicht entschieden**

> **Nicht** entschieden. **E-5…E-8** sind ENTSCHIEDEN (Rev. 0.7, §17.11) und werden **nicht** neu
> aufgerollt. **E-1…E-4** bleiben offen (§17.9.4) und betreffen andere Themen. Neue Vorlagen
> beginnen daher bei **E-9**; **keine** bestehende E-ID wird umnummeriert oder verdrängt.
> **E-13c ist eine Suboption von E-13** (keine neue E-Reihe): sie macht den Kopier-Pfad, den
> §12.3 (g) Q3 als „Ergänzung zu E-13" führte, zu einer **benannten, entscheidbaren** Vorlage mit
> zwei Entscheidungspunkten (RVW9-4). **E-13c ist ebenso offen wie E-13** und wird hier
> **nicht** entschieden.

**E-9 — Wert des Keys: zweiwertiges Enum oder boolescher Override?**

| Option | Beschreibung | Auswirkung |
|---|---|---|
| **E-9a (Empfehlung)** | Enum `["auto", "docs-consolidation"]`, Default `auto` | Schema-Wächter greift; ein Tippfehler wird zum **Validierungsfehler**; self-documenting; **keine** Sollwert-Änderung |
| E-9b | Boolean `index-override: true`, Default `false` | kürzer, aber ein **Negativname**; ein Tippfehler (`overide: true`) wäre ein stiller No-op ⇒ der Wächter verliert seinen Zweck; ein späterer dritter Wert wird ein breaking rename |
| E-9c | Enum `["auto", "knowledge-engine", "docs-consolidation"]` | symmetrisch, fügt aber einen **dritten** blockierenden Eigentümer ein und widerspricht `doc_renderer.py:685-686` ⇒ **verworfen** (DECISION-2) |

**Empfehlung: E-9a. Blockiert:** die Wertetabelle in **IC-25**, **AC-46** und den Fail-closed-Zweig.
**Auswirkung auf die Wellen:** **W3-6** — bei E-9a **keine** Sollwert-Änderung; bei E-9b wären
**AC-44(c)** und **AC-46** auf einen Boolean umzuschreiben (ein Test weniger). **W3-7** und
**W4-1…W4-3** unberührt.

**E-10 — Reichweite: nur `docs/INDEX.md` oder auch die W3-7-Marker-Regionen?**

**Sachstand (gemessen):** `apply_fact_blocks()` (`doc_renderer.py:183`) wird vom KE-Gate
**nicht** berührt. Ihre Gates sind `docs-consolidation.enabled` (Common-Gate,
`scripts/consistency-check.py:138`) und `docs-consolidation.sources` (IC-22), das in
`.meta-config/project.yaml:398-401` **fehlt** (Default `[]` ⇒ kein Rendering, NG-9).
**W3-7 ist also durch dieses Gate nicht blockiert** — es fehlt `sources`, nicht die Ausnahme.

| Option | Beschreibung | Auswirkung |
|---|---|---|
| **E-10a (Empfehlung)** | `index-owner` gilt **ausschließlich** für `docs/INDEX.md` | hält den Aufgaben-Scope; W3-7 bleibt eigenständig; entspricht DECISION-4 |
| E-10b | Key = „der Doku-Generator besitzt **alle** generierten Doku-Artefakte" | erzwingt eine **Umbenennung** (der Name meint nur einen Pfad), skaliert `sources` mit und zieht W3-7 in den Scope |

**Empfehlung: E-10a. Blockiert:** den Umfang von **IC-26/1** und **AC-45**.
**Auswirkung auf die Wellen:** **W3-6** läuft mit E-10a. **W3-7** braucht in **jedem** Fall
`docs-consolidation.sources: [README.md, llms.txt, ARCHITECTURE.md]` — das ist eine **eigene**
Config-Zeile und **keine** Folge dieser Ausnahme. **W4-1…W4-3** unberührt.

**E-11 — Reicht der Key für `docs/architecture/INDEX.md` (W4-3)?**

**Sachstand (gemessen):** `docs/architecture/INDEX.md` steht in `DOCS_GENERATED_RELS`
(`generated_file_drift.py:82`), unterliegt aber **keinem** Mode-Gate — es gibt nur **einen**
Aufrufer von `_index_mode_block_reason`, den Index-Writer. W3-6 erzeugt die Datei ausdrücklich
**nicht** (Plan `:4931-4932`; Test-Pin `tests/test_doc_renderer.py:3319-3320`).

| Option | Beschreibung | Auswirkung |
|---|---|---|
| **E-11a (Empfehlung)** | Nichts ändern; in W4-3 **verifizieren**, nicht vorab entscheiden | W4-3 bleibt wie geplant |
| E-11b | W4-3 verlangt **vorab** eine Scope-Erweiterung des Keys | nimmt E-10 faktisch vorweg ⇒ **nicht** ohne E-10-Entscheidung |

**Empfehlung: E-11a. Blockiert:** nichts in W3-6; W4-3 bleibt **verifikationspflichtig**, nicht
entscheidungspflichtig.

**E-12 — Reicht eine Docstring-Korrektur, oder zwei Fixtures im AC-20-Test?**

| Option | Beschreibung | Auswirkung |
|---|---|---|
| **E-12a (Empfehlung)** | Docstring korrigieren **und** den neuen Override-Test (AC-42 Modus A) als **zweites** Fixture danebenstellen; `_e2e_config()` **nicht** umbauen | der Test behält seine Aussage (Skeleton-Übernahme); die neue Aussage kommt **additiv** dazu; Sollwert von `test_skeleton_replaced_once` bleibt unberührt |
| E-12b | `_e2e_config()` umbauen, sodass es **beide** Modi durchläuft | **ein** Test mit **zwei** Verhaltensweisen ⇒ schwerer zu diagnostizieren; der Skeleton-Fall verliert seinen eigenen Namen |
| E-12c | zusätzlich ein Test an der **verdrahteten** Stage (`sync_pipeline.py:985`) | stärkerer Nachweis (Stellenwert: `test_ke_index_stays_authoritative`, `:3100`, argumentiert genau damit); Kosten: ein weiterer Test |

**Empfehlung: E-12a**, mit **E-12c als möglicher Erweiterung**. **Blockiert:** den Zusatz zu K-2
und den Testumfang von **AC-42** (ob ein Test an der verdrahteten Stage dazukommt).
**Auswirkung auf die Wellen:** **W3-6** Testaufwand unverändert bei E-12a; **W4** unberührt.

**E-13 — Dokumentationspflicht: wer trägt Schema-/Beispiel-Eintrag?**

| Option | Beschreibung | Auswirkung |
|---|---|---|
| **E-13a (Empfehlung)** | **W3-6**: eine Zeile `index-owner` in `.meta-config/project.yaml`; **W8-4**: Schema-Abschluss und Doku | verteilt die Pflicht auf die Wellen, die ohnehin `.meta-config/project.yaml` bzw. den Schema-Stand besitzen. **K-81 / RVW8-4: in dieser Form NICHT durchführbar — als Option zurückgenommen.** T-8 (Schema-Property) ist Voraussetzung für T-3 und T-5 (V-D7); ein Schema-Abschluss in **W8-4** würde W3-6s eigenen Nachweis „erweiterte Property-Menge" unerfüllbar machen. **Korrigierte Fassung:** T-3/T-5/T-8 liegen **alle in W3-6**; **W8-4** behält — *falls* die Doku-Zuordnung so entschieden wird — **nur den Dokuanteil**. |
| E-13b | alles in **W3-6** | W3-6 würde größer als geplant und berührte `admin-ui`-Belange (fremde Welle). **K-81: in der technischen Dimension bereits durch V-D7 entschieden** (T-3/T-5/T-8 gehören zusammen) — offen bleibt nur, ob der **Dokuanteil** zusätzlich mitwandert. |
| **E-13c — Kopier-Pfad** *(dritte Ausprägung, in §12.3 (g) Q3 als **Ergänzung zu E-13** geführt; **erst mit dieser Korrekturrunde (RVW9-4)** als eigene Optionenzeile in §17.12.2 ausgewiesen — **nicht entschieden**, siehe Suboptionen unter der Tabelle)* | **Doku-Pflichtträger** für die **kopierte** Deklaration: wer dokumentiert, dass `index-owner: docs-consolidation` in einem KE-Projekt (`knowledge-engine.enabled: true`) die KE-Autorität aufhebt — und ob eine `validate`/`--strict`-**Meldung** dafür gefordert wird | **Sachstand (gemessen, unverändert gegenüber §12.3 (g)):** ein gültiger, kopierter `index-owner: docs-consolidation` ist per Konstruktion **nicht** als Tippfehler erkennbar — weder per Enum (der Wert ist gültig) noch per fail-closed Zweig IC-25 (1) (der Wert ist bekannt). **Restrisiko, ausdrücklich NICHT akzeptiert** (§12.3 Q3-Bullet, Q4 (g), Bewertung). **Achtung — Abgrenzung:** E-13c ist **kein** sechstes P-Element und **kein** neues AC; es ist eine **offene Entscheidungsvorlage**. |

**Empfehlung: E-13a — in der korrigierten Fassung (T-3/T-5/T-8 in W3-6, Dokuanteil optional in W8-4). Blockiert:** die Zuordnung des **Dokuanteils**, **nicht** W3-6 selbst. **Die technische Wellenzuordnung von T-3/T-5/T-8 ist durch V-D7 gemessen und steht fest; sie ist keine offene Frage mehr.**
**Auswirkung auf die Wellen:** **W3-6** +1 Config-Zeile + Schema-Property + 2 Enum-Tests + 2 Mengen-Pins; **W4-1…W4-3** unberührt; **W8-4** ggf. ein
zusätzlicher Punkt in dessen `Files:`-Liste (**Plan**-Änderung, **keine** Spec-Änderung).

**E-13c — Kopier-Pfad: Suboptionen (RVW9-4; §12.3 (g) Q3-Bullet verlangt genau diese beiden
Entscheidungspunkte). Beide Punkte sind **offen**; **keine** ist entschieden.**

| Suboption | Entscheidungspunkt | Option | Auswirkung |
|---|---|---|---|
| **c(1)** | **Doku-Pflichtträger** für die kopierte Deklaration | **c(1)-a (Empfehlung):** Pflicht in der **IC-25-Dokuabschnitt** dieser Spec (die Zeile `index-owner: docs-consolidation` in `.meta-config/project.yaml` wird im W3-6-Commit-Body und in der Task-`Interfaces:`-Zeile kommentiert) | **keine** neue Welle, **kein** neues AC, **keine** Code-Änderung; das Restrisiko bleibt benannt und gemessen |
| | | c(1)-b: Pflicht als **README-Abschnitt** (Konsumenten-sichtbar) | zusätzlicher Dokuanteil in **W3-6** oder **W8-4** — E-13a (Dokuanteil) wird damit belegt; **W3-7**/**W4-1…W4-3** unberührt |
| | | c(1)-c: **keine** Pflicht — das Restrisiko bleibt ausschließlich in Spec §12.3 benannt | **günstigster**, lässt die Oberfläche „knowledge-engine ist autoritativ" aber widersprechen; **nicht** empfohlen, weil §12.3 (g) es ausdrücklich **nicht akzeptiert** |
| **c(2)** | `validate`/`--strict`-**Meldung**, wenn `index-owner` **und** `knowledge-engine.enabled: true` gesetzt sind | **c(2)-a (Empfehlung):** **nein** — eine Meldung wäre ein **dritter** Eigentümer-Signalpfad neben `doc_renderer.py:702-703` und dem Schema-Enum und würde DECISION-2/IC-26/1 berühren | **kein** zusätzlicher V-Check, **keine** neue Welle; W3-6 bleibt beim bisherigen Umfang + **V-D8-Plan-Delta** |
| | | c(2)-b: **ja**, als **neuer V-Check** neben V1…V9 | **neue** Wellenzuordnung, **neuer** Plan-Task, **neue** `W-VALIDATE-ROT`-Eintragung; **größer** als Rev. 0.8 — **nur** mit ausdrücklicher Scope-Erweiterung, die in Rev. 0.8 **nicht** beauftragt ist |
| | | c(2)-c: **ja**, aber als `WARN` statt `ERROR` | Mittelweg: Gate im `--strict`-Modus rot, im Normalmodus sichtbar; berührt §10 (Severity-Regel), **keine** neue Welle |

**Empfehlung: c(1)-a + c(2)-a.** **Begrenzung (bewusst):** die Empfehlung ersetzt **keine**
Entscheidung — sie ist die Begründung, mit der der Auftraggeber entscheidet. **Owner:** `main_chat`
(alle übrigen offenen Vorlagen ebenso, §17.12.2-Einleitung). **Termin:** **vor** der Umsetzung von
**W3-6** (identisch mit P-1…P-5, §17.12.1) — danach ist die kopierte Deklaration ein
Implementierungs-, kein Entscheidungsproblem mehr.
**Auswirkung auf die Wellen:** **W3-6** — bei c(1)-a/c(2)-a **keine** Erweiterung über den
Rev.-0.8-Umfang hinaus; c(1)-b berührt den **Dokuanteil** (E-13a); c(2)-b/c erfordern einen
**neuen** Plan-Task und sind **außerhalb** Rev. 0.8. **W3-7** und **W4-1…W4-3** in **allen**
Suboptionen unberührt.
**Sachstand, der E-13 präzisiert (gemessen):** eine Datei
`config/agent-meta.config.example.yaml`, die als Beispielträger in Frage käme, **existiert im
Repo nicht** (Glob ⇒ keine Treffer), und **keine** der beiden Beispiel-Configs
(`docs/guides/project.yaml.example`, `docs/guides/configs/project.yaml.example`) enthält
heute überhaupt einen `docs-consolidation`-Block (Grep ⇒ **0** Treffer). Die **IC-22-Tabelle**
ist damit der **einzige** normative Ort, der die Keys dieses Blocks aufzählt — weshalb P-3
(„siebter Key") überhaupt eine Pflicht ist.

**Ausdrücklich KEINE offene Frage** (festgehalten, damit sie nicht erneut aufgerollt wird):

| Thema | Feststellung |
|---|---|
| `facts-hash`-Churn durch den neuen Key | Der Key fließt **nicht** in `compute_doc_facts()` ein (kein Aufruf, kein Parameter) ⇒ **kein** Churn, **kein** AC (IC-26/9). |
| **OQ1** (Wiki-Topics ↔ `docs/guides/`) | **BLEIBT OFFEN**, Owner `main_chat` (`docs/plans/2026-09-25-docs-consolidation-oq1.md:94`), Blockade **W5** (`:99`). Diese Ausnahme berührt `knowledge/wiki/**` **nicht** und hebt die Blockade **nicht** auf. **Weder OQ1 noch eine andere offene Spec-Frage wird durch Rev. 0.8 stillschweigend aufgelöst.** |
| **OQ6**, **OQ8** | **ENTSCHIEDEN** (§11.2) — von **W3-6** umzusetzen, hier **nicht** neu bewertet. |
| OQ2, OQ3, OQ4, OQ5, OQ7, OQ9, OQ10 | Status **unverändert** (§11.1/§11.2); Rev. 0.8 stellt **keine** davon auf. |

#### 17.12.3 DECISION-1…DECISION-4 (übernommen, jede am Code belegt)

| ID | Entscheidung | Verworfene Alternativen (Kurzform) | Beleg |
|---|---|---|---|
| **DECISION-1** | **Anbindungsachse: deklarativer Config-Key** `docs-consolidation.index-owner` (Default `auto`), gelesen von **genau einer** Funktion, in agent-meta explizit auf `docs-consolidation` gesetzt. | **B-1** Vergleich über `project.name` / `platforms` — verstößt gegen die Aufgaben-Constraint und `AGENTS.md:50`, und zählt eine Projekt**identität**, die eine Variable ist, keine Fähigkeit. **B-2** Struktur-/Marker-Erkennung („dieses Repo *ist* das Framework-Repo") — von der APPROVED-Fassung **bereits entschieden** (**R17**, Risikotabelle §12.2) und unabhängig davon im Common-Gate festgehalten (`scripts/consistency-check.py:144-145`). **C** Capabilities-Key im `knowledge-engine`-Block — würde der KE Jurisdiktion über den **Doku**-Index geben und koppelt zwei Features, die IC-13 entkoppelt hält. **D** `resolve_index_mode()`-Default umdrehen bzw. `index.mode: file-index` in agent-meta — kehrt die KE-Präzedenz um und macht den Scaffold zum Mit-Schreiber. | `AGENTS.md:50`; `.opencode/skills/provider-agnostic/SKILL.md:12-18`; **R17** (Abschnitt §12.2); `consistency-check.py:144-145`; `.meta-config/project.yaml:80-81` (`platforms: [agent-meta]` — vorhanden und **unbenutzt**); `resolve_index_mode` `spec_plan_scaffold.py:80-97`; IC-26/8 |
| **DECISION-2** | **Kein expliziter Wert `knowledge-engine` im Enum.** Der Key kann einen Eigentümer **nicht** hinzufügen, nur den einen Auslöser stilllegen. | Wert `knowledge-engine` — **dritter** blockierender Eigentümer, widerspricht `:685-686`; zusätzlich Verhaltensaenderung für jedes `file-index`-Projekt, das den Key setzt. | `doc_renderer.py:685-686`, `:666-676`; IC-25 Wertetabelle; AC-44 |
| **DECISION-3** | **Kein Eingriff in `resolve_index_mode()`** — die Ausnahme lebt im **Doku**-Gate, das die Funktion nur aufruft, nie in der Funktion, die auch der Scaffold liest. | Optionaler dritter Parameter `resolve_index_mode(config, *, owner_override=False)` — breitete die Ausnahme in die Scaffold-Entscheidung (`:115`) und in `knowledge.py:185` aus, also genau in die Pfade, die unverändert bleiben **müssen**; außerdem Signaturänderung eines Schnittstellenpunkts, den W1-1…W3-5 als stabil behandeln. | `spec_plan_scaffold.py:80-97`, `:115`; `knowledge.py:185`; IC-26/2 |
| **DECISION-4** | **W3-7 wird von dieser Ausnahme ausdrücklich NICHT miterfasst.** Der Key wirkt ausschließlich auf `_index_mode_block_reason`, also auf den Index-Writer; die Hybrid-Regionen (`apply_fact_blocks`, `doc_renderer.py:183`) bleiben unberührt. | Den Key als „der Doku-Generator besitzt alle generierten Doku-Artefakte" lesen und `sources` mitskalieren — Scheinkonsistenz (der Name meint nur einen Pfad) **und** Scope-Ausweitung ohne Gate-Bedarf. | `doc_renderer.py:183`; `consistency-check.py:138`; IC-26/1; E-10 |

#### 17.12.4 Nachweisformen und Testakzeptanz — **beide Modi**

**Modus-Übersicht (jede Zeile nennt den Testpin, oder weist ihn als neu aus):**

| # | Aussage | agent-meta-Ausnahme (Override) | Consumer im KE-Modus | Testpin | Status |
|---|---|---|---|---|---|
| 1 | Ein Schreibvorgang ist erlaubt | `written == ["docs/INDEX.md"]`, `CREATE`, `doc-indexer/1` **und** `docs-facts`-Block im Dokument; zweiter Lauf `unchanged`, **null** Aktionen | `skipped`, `KE_AUTHORITATIVE_REASON`, **null** Aktionen, Baum identisch | `tests/test_doc_renderer.py::test_index_owner_override_writes_in_a_ke_authoritative_project` + `::test_index_owner_absent_keeps_the_ke_authoritative_block` | **beide NEU** (AC-42) |
| 2 | Absenz-Semantik | Default `auto` ⇒ Grund ist **zeichengleich** `KE_AUTHORITATIVE_REASON` (`:277`) | dito | `::test_index_owner_absent_keeps_the_ke_authoritative_block` (neu) + **bestehend unverändert** `::test_ke_authoritative_writes_no_index` (`:2614`), `::test_ke_authoritative_writes_no_index_even_when_absent` (`:2650`) | gemischt (AC-43) |
| 3 | `skeleton` wird **nicht** aufgehoben | `skipped` + `SKELETON_MODE_REASON`, Skeleton byte-identisch | dito (unverändert) | **neu** `::test_index_owner_override_does_not_relax_skeleton_or_ownership`; **bestehend unverändert** `::test_skeleton_mode_preserves_scaffold` (`:2559`), `::test_skeleton_mode_creates_no_index_at_all` (`:2590`) | gemischt (AC-44 a) |
| 4 | Besitzregel wird **nicht** aufgehoben | `skipped` + `OWNERSHIP_REASON` bei fremder Datei | dito (unverändert) | **neu** `::test_index_owner_override_does_not_relax_skeleton_or_ownership` (Fall **b**, §17.12.4 Zeile 4 nennt den Testnamen; Fall a = Zeile 3); `::test_scaffold_guard_recognises_only_the_skeleton` (`:2529`) unverändert | gemischt (AC-44 b) |
| 5 | Unbekannter Wert ist fail-closed | `skipped` + `UNKNOWN_INDEX_OWNER_REASON`, **kein** Schreiben | dito | **neu** `::test_unknown_index_owner_is_fail_closed`; Muster `::test_unknown_index_mode_is_fail_closed` (`:2720`) | **neu** (AC-44 c) |
| 6 | `dry_run` schreibt nicht | `written` **enthält** den Pfad, Action `WOULD-CREATE`, Baum identisch | `written` **leer**, `skipped` enthält den Pfad | **neu** `::test_index_owner_override_keeps_dry_run_free_of_writes`; `::test_dry_run_no_writes` (AC-23) unverändert | **neu** (AC-45) |
| 7 | Schema pinnt die zwei Werte | `index-owner: docs-consolidation` **valid** | `"knowledge-engine"` / `"agent-meta"` / `"docs"` **invalid** | **neu** `::test_index_owner_enum_accepts_both_values`, `::test_index_owner_enum_rejects_everything_else`; Muster `:174-182` | **neu** (AC-46) |
| 8 | Property-Menge des Blocks | **sechs** Properties | **sechs** Properties (der Key ist ein reines Deklarations-Key) | **bestehend, Sollwert-Erweiterung** `::test_schema_block_present_and_closed` (`:81`) ⇒ `_EXPECTED_PROPERTIES` `:45-51` **fünf → sechs** | geändert (AC-39) |
| 9 | `off` ist **kein** blockierender Eigentümer | unverändert | unverändert | **bestehend unverändert** `::test_index_mode_off_permits_the_full_index` (`:2740`) | unverändert |

**Bestehende Tests, die unverändert grün bleiben (Sollwerte unangetastet):**

| Test / Assert | `file:line` | Warum unverändert |
|---|---|---|
| `tests/scenarios/asserts/{50:32, 51:32, 52:44, 54:26-27, 55:24-25, 56:31}` | `tests/scenarios/asserts/50-spec-plan-workflow.sh:32` · `51-spec-plan-disabled.sh:32` · `52-spec-plan-enabled.sh:44` · `54-spec-plan-external-override.sh:26-27` · `55-spec-plan-ke-off-fallback.sh:24-25` · `56-spec-plan-preset-coupling.sh:31` | **Keines** der Fixtures `tests/scenarios/configs/*.project.yaml` enthält einen `docs-consolidation`-Key (Grep ⇒ **0** Treffer; `tests/scenarios/run.sh:46-52` spielt sie 1:1 ein) ⇒ `enabled` fail-off ⇒ der Code-Pfad **nie** erreicht. **AC-38 bleibt wörtlich gültig, NG-10 gewahrt.** |
| `::test_ke_authoritative_writes_no_index` | `tests/test_doc_renderer.py:2614` | Fixture `_KE_AUTHORITATIVE_CONFIG` (`:2481-2484`) hat **keinen** `index-owner`-Key ⇒ `auto` ⇒ Gate feuert unverändert. |
| `::test_ke_authoritative_writes_no_index_even_when_absent` | `:2650` | dito. |
| `::test_ke_index_stays_authoritative` | `:3100` | Fixture `:3118-3123` ohne `index-owner` ⇒ bleibt grün. |
| `::test_index_mode_off_permits_the_full_index` | `:2740` | `off` + **kein** `index-owner` ⇒ unverändert; der Test pinnt ausdrücklich, dass `off` **kein** blockierender Eigentümer ist (DECISION-2). |
| `::test_skeleton_mode_preserves_scaffold` · `::test_skeleton_mode_creates_no_index_at_all` | `:2559` · `:2590` | `index-mode: skeleton` wird von der Ausnahme **nicht** aufgehoben (IC-26/3, AC-44 a). |
| `::test_skeleton_replaced_once` | `:3258` | **Sollwert bleibt unangetastet** — siehe unten. |
| `::test_scaffold_guard_recognises_only_the_skeleton` | `:2529` | `is_file_index_skeleton()` unberührt (IC-26/4). |
| `::test_stage_order_after_scaffold` | `:3013` | fährt die **verdrahtete** Stage; Fixture ohne `index-owner` ⇒ bleibt grün. |
| `::test_no_property_name_is_a_provider_name` | `tests/test_docs_consolidation_migration.py:116` | Der Key-Name `index-owner` enthält **keinen** Provider-Namen (Enum `config/project-config.schema.json:24-34`); der Test liest die Property-Namen **dynamisch** und bleibt deshalb grün. |
| `::test_schema_declares_the_absence_defaults` (Fail-off-Defaults des Blocks) | `tests/test_docs_consolidation_migration.py:185-199` (Def `:185`, Docstring `:186-192`, Asserts `:194-199`) | **K-78 (RVW8-2, belegt):** der Test liest die fünf Keys **namentlich** (`properties["enabled"]["default"]` usw.) und iteriert die Block-Property-Menge **nicht** ⇒ eine sechste Property bricht ihn **nicht**. **RVW9-7:** der frühere Wildcard-Name `::test_fail_off_defaults_*` existiert **nicht** — belegt durch den Namen `def test_schema_declares_the_absence_defaults()` bei `:185`; der Zeilenbereich beginnt **nicht** im Docstring (`:185`, nicht `:186`). |
| `_EXPECTED_CHECKS_PROPERTIES` | `tests/test_docs_consolidation_migration.py:53`, geprüft `:112` | **K-78 (belegt):** `checks` erhält **keine** neue Property (`index-owner` liegt auf Top-Level) ⇒ Pin bleibt unberührt. |

> **K78-Verortung (RVW9-6).** Die **zwei geänderten** Pins `_EXPECTED_PROPERTIES`
> (`tests/test_docs_consolidation_migration.py:45-51`) und `_IC22_ABSENCE_DEFAULTS`
> (`tests/test_doc_renderer.py:1092-1098`) stehen in **keiner** Zeile dieser Tabelle — sie sind
> **keine** „unverändert grün"-Fälle. Ihre Orte sind: **Modus-Übersicht Zeile 8** (oben),
> **T-3 (a)/(b)** (§17.12.4 Teständerungsliste) und die **Coverage-Zeile „Sollwert-Änderungen
> vollständig registriert"** (§17.12.5). Die Tabelle trägt ausschließlich die **unveränderten**
> Nachbarn (`_EXPECTED_CHECKS_PROPERTIES`, Fail-off-Defaults-Test).

**`test_skeleton_replaced_once` — Sollwert-Stabilität als Design-Anforderung (K-2).**
`_e2e_config()` (`:3209-3238`) kopiert den **Live**-Block inklusive des neuen Keys und setzt
zusätzlich `knowledge-engine: {"enabled": False}` (`:3237`). Damit läuft der Test in einer
`file-index`-Konfiguration, in der `index-owner` per Konstruktion ein **No-op** ist (der
KE-Zweig greift ohnehin nicht). Der Test bleibt also grün, **ohne** dass sein Sollwert
angefasst wird. **Das ist Absicht und muss im Review so verteidigt werden:** der Test beweist
die **Skeleton-Übernahme** (AC-20), **nicht** die **Eigentümer-Deklaration**; für die zweite
Aussage kommt der neue Test aus Zeile 1 daneben — derselbe Live-Block, aber mit
`knowledge-engine: {enabled: true}`. **Einzige** Textänderung ist der Docstring (**K-2**).

**Erforderliche Teständerungen (keine Sollwert-Absenkung, nur Erweiterung):**

| # | Datei `file:line` | Änderung | Grund |
|---|---|---|---|
| T-1 | `tests/test_doc_renderer.py:3209-3223` | **Docstring** von `_e2e_config()` korrigieren und **ausdrücklich** benennen, dass die Fixture eine **abweichende** Konfiguration benutzt (`:3237`) und warum. | **K-2** — die Aussage ist für agent-meta nach dem Key-Set falsch. **Reiner Text.** |
| T-2 | `tests/test_doc_renderer.py` (neu, nach `:3258`) | **5 neue Tests** (Zeilen 1–6 der Tabelle oben, ohne Zeile 7). | AC-42…AC-45. |
| T-3 | `tests/test_docs_consolidation_migration.py:45-51`<br>**und** `tests/test_doc_renderer.py:1092-1098`<br>**Welle W3-6** (Reihenfolge T-8 → T-3 → T-5, **V-D7**) | **(a)** `_EXPECTED_PROPERTIES`: **fünf → sechs** (`+ "index-owner"`). Erforderlich, sonst bricht `::test_schema_block_present_and_closed` (`:99-103`, `:101`) mit `unexpected properties: ['index-owner']`.<br>**(b)** `_IC22_ABSENCE_DEFAULTS`: **fünf → sechs** (`+ "index-owner": "auto"` — der Wert ist der Absenz-Default aus IC-22). Erforderlich, sonst bricht `assert _schema_absence_defaults(block_schema) == _IC22_ABSENCE_DEFAULTS` (`:1371`, in `::test_absent_block_is_noop`, `:1318`), weil `_schema_absence_defaults` (`:1114-1130`) **alle** Block-Properties iteriert und deren `default` abbildet. | AC-39 / P-3 (e). **K-78 (RVW8-2):** dies sind **zwei** harte Sollwert-Änderungen in Rev. 0.8, **nicht eine** — die frühere Formulierung „die einzige echte Sollwert-Änderung" ist **zurückgenommen** (sie machte W3-6 rot, obwohl §17.12.4 genau das als Nachweis fordert). **Beide sind Erweiterungen einer Menge, keine Absenkung.** Ein Grep nach weiteren Mengen-Pins (`_EXPECTED_CHECKS_PROPERTIES` u. a.) belegt: **keine weiteren** (V-D4). **RVW9-6: die Orte von K78** sind Modus-Übersicht Zeile 8, T-3 (a)/(b) und die Coverage-Zeile — **nicht** die „bleiben grün"-Tabelle. |
| T-4 | `tests/test_docs_consolidation_migration.py:42-44` | Zählkommentar: **Text** in Zeile `:42` von „six rows/five of them" auf „**seven rows/six** of them" **und** das Ordnungswort in Zeile `:43` von „**sixth**" auf „**seventh**" — die **Hälfte ab Zeile `:44`** bleibt **wortgleich**: `knowledge-engine.okf.index-mode` liegt weiterhin in einem anderen Block und der Verweis **„deferred to W7-2"** gilt unverändert (`:44`: „`checks.strict` is a nested key, so it is one property here"). | **K-3**. **K-77 (RVW8-1):** der Kommentar **existiert** am Working Tree (Grep-Beleg `:42`, `:43`, `:44`); die frühere Abbruchbedingung („fehlt der Kommentar, entfällt T-4") ist damit **gegenstandslos** und **ersatzlos gestrichen**. **T-4 ist verbindlich** — ein Kommentar, der nach Rev. 0.8 falsch ist (sieben Zeilen in der IC-22-Tabelle, sechs `docs-consolidation.*`-Keys), ist selbst ein Befund. **RVW9-3:** `:43` **mitziehen** — bei sieben Zeilen ist der KE-Key die **siebte**; „sechs von sieben" und „the sixth" können nicht gleichzeitig stimmen. Solltext `:43`: `# seventh (\`knowledge-engine.okf.index-mode\`) belongs to a different block and is`. |
| T-5 | `tests/test_docs_consolidation_migration.py` (neu) — **Welle W3-6**, **nach** T-8 und T-3 (V-D7) | **2 neue Enum-Tests** (Zeile 7). | AC-46. |
| T-6 | `scripts/lib/doc_renderer.py:669-672` | **Docstring**-Korrektur. | **K-1** — reiner Text, kein Verhalten. |
| T-7 | `.meta-config/project.yaml:398-401` | **eine** Zeile `index-owner: docs-consolidation`. | P-3 / IC-25; **kein** Code, **kein** Test. **Reihenfolge (RVW9-9):** T-7 schreibt in **denselben** `docs-consolidation`-Block, den der **offene** Schritt 2 von Plan-**W1-10** (`docs/plans/2026-09-25-repository-documentation-consolidation.md:2115-2118`, „4 von 5 Properties": `index-mode`, `checks.strict`, `sources`, `volatile-facts`) füllen will. **Reihenfolge festgehalten: W1-10 Step 2 ist VOR W3-6 zu ziehen** (dann ist der Live-Block vor dem Delta vollständig) **oder** als Bestandteil von W3-6 zu führen; die `CAN_RUN_IN_PARALLEL`-Liste des Plans ist entsprechend zu berichtigen (Plan-Sache, Teil des V-D8-Deltas). **Zusatz-Abhängigkeit:** ein in W1-10 gesetztes `sources` aktiviert den Gate-Zweig `apply_fact_blocks` — dieselbe Abhängigkeit, die E-10 und **V-D6** als eigene Config-Zeile für W3-7 führen (`doc_renderer.py:183`, `docs-consolidation.sources` in IC-22). |
| T-8 | `config/project-config.schema.json:2421-2470` (Block; Properties `:2424-2469`, `additionalProperties: false` `:2470`) — **Welle W3-6, zuerst** (V-D7) | **eine** Property `index-owner`. | P-3 / IC-25. **K-81:** T-8 ist Voraussetzung für T-3 und T-5. |

**Nachweisformen (Kommandos, keine neuen Dateien):**

| Nachweis | Kommando | Soll |
|---|---|---|
| W3-6 Kernlieferung | `python3 scripts/sync.py --dry-run` (einmal), danach `python3 scripts/sync.py` | 1. Lauf `CREATE docs/INDEX.md`; 2. Lauf `unchanged`, **null** Actions |
| Drift-Baseline | `python3 scripts/sync.py --check` | **0** — sobald die Datei existiert, greift `DOCS_GENERATED_RELS` (`generated_file_drift.py:82`, Verdrahtung `:204-207`); der Docstring dort (`:201`) sagt den Fall bereits voraus: „``docs/INDEX.md`` only arrives in W3-6" |
| Szenario-Regression | `bash tests/scenarios/run.sh 50 51 52 54 55 56` | **0** (bestehender Runner, **keine** neuen Dateien — AC-38, NG-10) |
| V2-Nachweis | `python3 scripts/sync.py --validate` | V2 **0** (`docs_index.py:180-211`); `--validate` bleibt planmäßig **rot** über V3 (Plan `:4936-4937`) |
| tracked (OQ6) | `git check-ignore -q docs/INDEX.md; echo $?` | **1** (Plan `:4929`, `:4935`) |
| Schema (T-8 → T-3 → T-5, **alle in W3-6**, Reihenfolge **V-D7**) | `python3 -m pytest tests/test_docs_consolidation_migration.py -q` | gruen inkl. **2** neuer Enum-Tests und erweiterter Property-Menge (**beide** Pins: `_EXPECTED_PROPERTIES` `:45-51` **und** `_IC22_ABSENCE_DEFAULTS` `test_doc_renderer.py:1092-1098`, K-78) |
| Einheiten | `python3 -m pytest tests/test_doc_renderer.py -q` | gruen inkl. **5** neuer Tests **und** erweitertem `_IC22_ABSENCE_DEFAULTS` (K-78) |

> **Diese W3-6-Akzeptanz ist vom heutigen Plan aus unerfüllbar — V-D8 (RVW9-2, major).**
> Die Nachweisformen dieser Tabelle verlangen T-7, T-8, T-3 (a/b) und T-5 **in W3-6**. Plan
> Rev. 0.7 (`docs/plans/2026-09-25-repository-documentation-consolidation.md:4918-4944`) kennt
> davon **keins**: `Files:` `:4920-4921` nennt weder `config/project-config.schema.json` noch
> `tests/test_docs_consolidation_migration.py`; `Ziel-AK` `:4926` = **AC-20, AC-12 (E2E), AC-38**
> — **kein** AC-42…AC-46, kein AC-39; Steps `:4938-4944` ohne T-7/T-8/T-3/T-5; Grep über den Plan:
> `index-owner` **0** Treffer, `AC-4[2-6]` **0** Treffer, `pending-approval` **0** Treffer. Wird
> W3-6 nach Plan umgesetzt, entsteht **weder** die Deklaration **noch** die Schema-Property ⇒ der
> KE-Vorrang-Zweig `doc_renderer.py:702-703` blockiert weiter, `docs/INDEX.md` entsteht nicht.
> **Der Plan wird in dieser Korrekturrunde NICHT geändert.** Der **forderliche Plan-Delta** ist in
> **§17.12.5 (V-D8, V-D8-Uebergabe)** präzise benannt und wird **erst nach** der User-Freigabe von
> P-1…P-5 (inkl. P-3 (e)) durch den `planner` ausgeführt.

#### 17.12.5 Befunde aus der Nachmessung — was der Entwurf annahm und was der Working Tree zeigt

| ID | Befund | Behandlung |
|---|---|---|
| **V-D1** | **Weitere veraltete Zeilenanker derselben Klasse wie K-4**, die der Entwurf **nicht** belegt und die Rev. 0.8 deshalb **nicht** angefasst hat: **(a)** IC-15 nennt `DEFAULT_FALLBACK_INDEX` bei `:23` und `_FILE_INDEX_SKELETON` bei `:24` — gemessen sind sie **`:28`** und **`:29`** (`spec_plan_scaffold.py:25-30`); **(b)** der **§15-Trace-Anker** nennt `spec_plan_scaffold.py:23` — real **`:28`**; **(c)** AC-38s zweite Abschirmung nennt `spec_plan_scaffold.py:49-51` für den „**vor** jedem `mkdir`"-Abbruch — real ist der Early-Return der deaktivierten Scaffold `spec_plan_scaffold.py:102-104` (die Funktion beginnt bei `:100`). | **Auswahlregel Rev. 0.8 (K-80, RVW8-8 — damit die Behandlung der Ankerdrift *einheitlich* ist):** Rev. 0.8 korrigiert **genau** die Anker, die in den **ohnehin von Rev. 0.8 geänderten** IC-/AC-Zeilen stehen; **alle übrigen** Fundstellen werden hier **vollständig** registriert, damit sie für die nächste Korrekturrunde nicht verloren gehen. Nach dieser Regel ist **(a)** in Rev. 0.8 zu korrigieren (IC-15 ist ein Rev.-0.8-IC, P-2) — getan, IC-15 **`:1487-1488`** ⇒ `:28`/`:29`; **(b)** und **(c)** bleiben **vorgemerkt** (Abschnitte, die Rev. 0.8 nicht anfasst). **RVW9-8: der Beleg dieser Selbstreferenz ist korrigiert** — V-D1 schrieb zuvor „IC-15 `:1449-1450`"; **RVW10-2: der von RVW9-8 gesetzte Ersatzanker `:1465-1466` war selbst falsch** und ist auf den **gemessenen** Träger gezogen** — durch K-84 (`docs/specs/2026-09-25-repository-documentation-consolidation.md:1487-1488`, `DEFAULT_FALLBACK_INDEX = "docs/INDEX.md"   # :28` und `_FILE_INDEX_SKELETON = "…"   # :29`) belegt liegt die angewandte Korrektur bei **`:1487-1488`**; `:1449-1450` trägt heute den IC-14-Überschrift-/Absatzbereich, `:1465-1466` **IC-13-Fließtext** (Szenarien 54/55/56 sowie 52, AC-38) — IC-15 beginnt bei `:1483`. **Vollständiges Inventar der übrigen Fundstellen (alle am 2026-09-29 per Grep erneut bestätigt):** `:515` (F8, `:23` → `:28`), `:528` (F20, `:24` → `:30`), `:571` (Fließtext, `:23` → `:28`), `:593` (NG-7, `:23` → `:28`), `:2187` (AC-22-Text, `:40-44` → `:80-97`), `:2255` (AC-38, `:49-51` → `:102-104`), `:2511` (AC-20, `:24, :62-68` → `:30`, `:115-121`), `:2513` (AC-22, `:40-44` → `:80-97`), `:2866` (OQ6, `:23` → `:28`), `:2968` (A4, `:62-68` → `:115-121`), `:3017` (§15, `:23` → `:28`), `:3110` (§16 Querverweise, `:20-24, :27-44, :46-68` → `:28-30, :80-97, :100-121`), `:3161` (§17.3 CR-1, `:49-51` → `:102-104`), `:3179` (A4-Nachweis, `:62-68` → `:115-121`). **Die inhaltlichen Aussagen an allen Fundstellen sind richtig — nur die Anker sind alt.** |
| **V-D2** | **IC-12s Aufrufreihenfolge** nennt `sync_pipeline.py:922-945` / `:929` / `:935` / `:1090-1099` / `:1102` / `:1106-1109`. Gemessen: `_sync_stage_knowledge_and_isolation` **`:966`**, `sync_knowledge_engine(...)` **`:974`**, `scaffold_spec_plan_dirs(...)` **`:980`**, `_sync_stage_docs_consolidation(...)` **`:985`**, `_sync_stage_generated_file_hash_capture` **`:1139`**, `_sync_stage_auto_commit_allowlist` **`:1151`**. Die **Reihenfolge** als Aussage ist richtig; nur die Anker sind alt. **Ergänzung RVW8-8 (K-80):** dieselben veralteten Pipeline-Anker stehen **zusätzlich** in **AC-22s §9.1-Zeile** (`:2513`, `sync_pipeline.py:922-945`) und in **§13 A4** (`:2968`, `sync_pipeline.py:935`) — V-D2 registrierte bislang **nur IC-12**; damit war der Umfang der nächsten Korrekturrunde unterbestimmt. **Vollständiges Inventar:** `:2513` (AC-22) und `:2968` (A4), beide auf denselben gemessenen Stage-Ankern umzuschreiben. **Die Rev.-0.8-Texte (IC-25, IC-26/1, §17.12.4) verwenden deshalb durchgängig die gemessenen Anker.** | **Nicht** angefasst (außerhalb des Delta-Auftrags, und die *Aussagen* dort sind richtig — nur die Anker sind alt); **vorgemerkt** mit vollständigem Inventar. Der Widerspruch zwischen IC-12 und IC-25 ist damit **sichtbar** und nicht verdeckt. |
| **V-D3** | **Zwei Belegstellen des Entwurfs sind am Working Tree nicht haltbar:** (a) die Korrektur-Klausel „neue Platzhalter dokumentiert" mit Anker `AGENTS.md:247` — in der generierten `AGENTS.md` gibt es diese Regel **nicht** (`:247` ist eine Zeile der Agent-Roster-Tabelle; die einzige placeholder-bezogene Aussage ist `AGENTS.md:39`); (b) `config/agent-meta.config.example.yaml` als Beispielträger — die Datei **existiert nicht** (Glob ⇒ keine Treffer). **Korrekte** Anker: Provider-Achse `AGENTS.md:50` **und** `.opencode/skills/provider-agnostic/SKILL.md:12-18`; Projekt-Achse `AGENTS.md:50` (Text) plus das Fehlen jeder Struktur-Heuristik in `consistency-check.py:144-145` und R17 (Abschnitt §12.2). | **K-1…K-5 wurden ausschließlich an den Stellen angewandt, an denen sie belegt sind**; die unbelegten Verweise wurden durch die **gemessenen** Anker ersetzt (§17.12.3 DECISION-1, IC-26/8). **E-13** beschreibt den Ist-Stand (kein Beispielträger vorhanden), statt eine nicht existierende Datei als Pflicht zu behaupten. |
| **V-D4** | **Zwei notwendige Teständerungen, die der Entwurf als reine Kommentar-Korrektur führt.** (a) `tests/test_docs_consolidation_migration.py:45-51` (`_EXPECTED_PROPERTIES`) ist ein **hart gepinnter Mengen-Sollwert** und wird von `::test_schema_block_present_and_closed` (`:99-103`, `assert set(properties) == _EXPECTED_PROPERTIES`, `:101`) geprüft. Eine neue Schema-Property **bricht** diesen Test ⇒ **Sollwert-Erweiterung** (fünf ⇒ sechs). (b) `_IC22_ABSENCE_DEFAULTS` (`tests/test_doc_renderer.py:1092-1098`, hartes Fünf-Key-Dict) wird gegen `_schema_absence_defaults(block_schema)` geprüft (`:1371`, in `::test_absent_block_is_noop`, `:1318`); `_schema_absence_defaults` (`:1114-1130`) iteriert **alle** Properties des Blocks und bildet deren `default` ab ⇒ eine neue Property `index-owner` erzeugt einen **sechsten** Schlüssel ⇒ **Assertion rot**. **K-77 (RVW8-1) korrigiert zusätzlich den Träger des Kommentars:** `:42-44` **existiert** (Grep-Beleg; das Read-Tool rendert ihn leer — Fehlmessung des Werkzeugs, nicht des Working Tree). **Vollständigkeits-Greep 2026-09-29 (K-78):** die Suche nach weiteren Mengen-Pins über `_EXPECTED_PROPERTIES`, `_IC22_ABSENCE_DEFAULTS`, `_EXPECTED_CHECKS_PROPERTIES` und `_block()["properties"]` ergibt **genau zwei** zu ändernde Sollwerte. `_EXPECTED_CHECKS_PROPERTIES` (`tests/test_docs_consolidation_migration.py:53`, geprüft `:112`) bleibt **unberührt**, weil `checks` **keine** neue Property erhält; der Fail-off-Defaults-Test **`::test_schema_declares_the_absence_defaults`** (`tests/test_docs_consolidation_migration.py:185-199` — Def `:185`, Docstring `:186-192`, Asserts `:194-199`; **RVW9-7:** der frühere Wildcard-Name `::test_fail_off_defaults_*` existiert **nicht**) liest die fünf Keys **namentlich** und prüft die Menge **nicht** ⇒ bleibt grün. | (a) als **T-3**, (b) als **T-3, zweite Zeile** (§17.12.4) geführt und beide als **P-3 (e)** in §17.12.1 zur Freigabe gestellt. **Keine Absenkung** — beide sind Erweiterungen einer Menge. **RVW9-6: die Orte** von K78 sind Modus-Übersicht Zeile 8, T-3 (a)/(b) und die Coverage-Zeile „Sollwert-Änderungen vollständig registriert" — **nicht** die „bleiben grün"-Tabelle, die nur die unveränderten Nachbarn listet. |
| **V-D5** | **`KE_OVERRIDE_REASON` ist im Entwurf nicht erreichbar.** Der Entwurf definiert die Konstante, lässt sie aber in seiner eigenen Entscheidungsfolge unbenutzt: der Zweig (2) gibt `None` zurück, und der Aufrufer loggt **ausschließlich** bei einem Grund (`doc_renderer.py:810-814`, gemessen). Ohne Eingriff in den Aufrufer bleibt die Konstante toter Code. | **Als optionale Audit-Konstante spezifiziert, nicht als Pflicht-Log** (IC-25-Docstring). **Verbindlich** ist allein die **negative** Zusage in **AC-42(c)**: `KE_AUTHORITATIVE_REASON` erscheint **nicht** im Log. Ob zusätzlich ein Override-Hinweis geloggt wird, ist eine **Plan**-Entscheidung und **keine** Spec-Pflicht — damit ist die Lücke geschlossen, ohne dem Plan eine Entscheidung abzunehmen. |
| **V-D6** | **Planlücke bei W3-7 / `docs-consolidation.sources` (K-86, RVW8-10).** **E-10 stellt korrekt fest, dass W3-7 durch dieses Gate nicht blockiert ist**, sondern an `docs-consolidation.sources` hängt — belegt: `apply_fact_blocks` hat heute **keinen** Produktionsaufrufer (Grep über `scripts/` findet nur Docstring-Erwähnungen, `doc_renderer.py:183`); `docs-consolidation.sources` wird **nirgends** im Code gelesen; `.meta-config/project.yaml:398-401` führt den Key **nicht**. **Plan W3-7** (`:4946-4997`) trägt die nötige Config-Zeile jedoch weder in `Files:` (`:4948` nennt nur `README.md`, `llms.txt`, `ARCHITECTURE.md`) noch in den Steps (`:4991-4997`) — eine **Plan**-Lücke. | **Als Befund registriert, hier nicht behoben** — die Ergänzung ist eine **Plan**-Änderung (`Files:` + Step), **keine** Spec-Pflicht, weil **keine** inhaltliche Pflichtänderung daraus folgt. Ohne diese Registrierung wäre die Lücke in der nächsten Korrekturrunde unsichtbar geworden. **E-10 bleibt davon unberührt** (offen). |
| **V-D7** | **T-3, T-5 und T-8 sind technisch untrennbar (K-81, RVW8-4).** Die drei Änderungen bilden **eine** Änderung: (i) **T-8** (Schema-Property `index-owner` mit `enum`/`default`) ist Voraussetzung dafür, dass `docs-consolidation.index-owner` im geschlossenen Block überhaupt zulässig ist — `config/project-config.schema.json:2470` `additionalProperties: false`; (ii) **T-3** (`_EXPECTED_PROPERTIES` **und** `_IC22_ABSENCE_DEFAULTS` fünf → sechs) bricht **ohne** T-8 `::test_schema_block_present_and_closed` (`tests/test_docs_consolidation_migration.py:99-103`) **und** die Assertion in `::test_absent_block_is_noop` (`tests/test_doc_renderer.py:1371`); (iii) **T-5** (`::test_index_owner_enum_accepts_both_values`) validiert eine Config mit `index-owner` gegen das Schema — **ohne** T-8 wirft `jsonschema` **ValidationError**, T-5 kann ohne T-8 nicht grün werden. **E-13a war in der Formulierung „W3-6: Config-Zeile; W8-4: Schema-Abschluss" damit **nicht durchführbar**:** der W3-6-Nachweis „erweiterte Property-Menge" (§17.12.4) verlangt T-8 **im selben Lauf**, in dem T-3 läuft. **Die Reihenfolge ist damit festgelegt: T-8 → T-3 → T-5, alle in derselben Welle.** **Auflösung ohne E-13-Entscheidung:** Die *technische* Unteilbarkeit (T-3/T-5/T-8 zusammen) ist eine **Messung**, keine Entscheidung und wird hier festgeschrieben. Die *offene* Frage — ob **W8-4 zusätzlich die Doku** (Schema-Kommentar/IC-22-Tabelleneintrag/Doku-Absatz) trägt — bleibt **E-13** und ist **nicht** entschieden. | **Verbindlich:** Wellenzuordnung in §9.1 (AC-39/AC-46 auf **W3-6**), E-13a in §17.12.2 als **in dieser Form zurückgenommen** markiert, Nachweiszeile §17.12.4 auf **W3-6** umgehängt. **E-13 selbst bleibt OFFEN** und wird hier **nicht** entschieden. |
| **V-D8** | **Der Plan Rev. 0.7 kennt Rev. 0.8 nicht — die W3-6-Akzeptanz nach §17.12.4 ist unerfüllbar (RVW9-2, major).** K-81/V-D7 legt T-3/T-5/T-8 (und T-7) **ausschließlich** in W3-6 und knüpft die W3-6-Akzeptanz an „gruen inkl. 2 neuer Enum-Tests und erweiterter Property-Menge" (`:4360`/§17.12.4-Nachweiszeilen). **Gemessen am Working Tree, Plan `docs/plans/2026-09-25-repository-documentation-consolidation.md` (Rev. 0.7, `status: APPROVED`, `:5-6`):** (a) **W3-6 `Files:`** `:4920-4921` = `docs/INDEX.md`, `.meta-config/project.yaml`, `README.md`, `tests/test_doc_renderer.py` — **weder** `config/project-config.schema.json` **noch** `tests/test_docs_consolidation_migration.py`; (b) **W3-6 `Ziel-AK`** `:4926` = **AC-20, AC-12 (E2E), AC-38** — **kein** AC-42…AC-46, kein AC-39; (c) **W3-6 Steps** `:4938-4944` — keine Config-Zeile `index-owner` (T-7), keine Schema-Property (T-8), keine Pins (T-3), keine Enum-Tests (T-5), **keine Reihenfolge**; (d) **Grep** über den Plan: `index-owner` = **0** Treffer, `AC-4[2-6]` = **0** Treffer, `pending-approval` = **0** Treffer; (e) der Schema-Block und `tests/test_docs_consolidation_migration.py` sind im Plan **W1-9** zugeordnet (`:2082`, Ledger-Zeile `:5694`) — und W1-9 ist **bereits abgearbeitet** (`:2095-2098` alle `[x]`, Commit `feat: declare docs-consolidation config block in schema`), mit der Behauptung „**sechs** Properties" (`:2084` `Interfaces:`, `:2096` Step 2) — **gemessen sind fünf** (`tests/test_docs_consolidation_migration.py:46-50`, Schema `config/project-config.schema.json:2424-2469`): dieselbe Fehlzählung, die P-3 (e) in der Spec korrekt diagnostiziert, im **Plan** aber unberührt lässt; (f) **RVW9-9:** der **offene** W1-10 Step 2 (`:2115-2118`) schreibt in **denselben** `docs-consolidation`-Block wie T-7 und würde `sources` aktivieren (E-10/V-D6) — der Runde-8-Blockierpunkt „CAN_RUN_IN_PARALLEL: W1-9/W1-10-Rest" traf für den **offenen** Step 2 nicht zu. **Auswirkung, wenn W3-6 nach Plan umgesetzt wird:** es entsteht **weder** die Deklaration (T-7) **noch** die Schema-Property (T-8) ⇒ der KE-Vorrang-Zweig `doc_renderer.py:702-703` blockiert weiterhin jeden Schreibvorgang, `docs/INDEX.md` entsteht **nicht**, und die in §17.12.4 festgeschriebenen Nachweise sind **nicht erreichbar**. Zusätzlich fehlt im Plan die `pending-approval:`-Spiegelung: wer den Plan liest, sieht das Freigabe-Gate für Rev. 0.8 **nicht**. Der einzige registrierte Plan-Befund war V-D6 (`:4376`) und betrifft **W3-7** — die kleinere Lücke. | **Als Befund registriert, hier NICHT behoben (Muster V-D6).** Der Plan ist **nicht** Teil dieser Spec-Korrekturrunde und wird hier **nicht** geändert; der **forderliche Plan-Delta** ist unten (**V-D8-Uebergabe**) präzise benannt. **Ausführung erst nach User-Freigabe von P-1…P-5 (inkl. P-3 (e)) durch den `planner`.** **Keine** inhaltliche Pflichtänderung: der Sollwert steht bereits in der Spec (§17.12.4), der Plan muss ihn nur **abbilden**. **E-9…E-13 einschließlich E-13c und OQ1 bleiben davon unberührt** (offen). |

#### V-D8-Uebergabe — **forderlicher Plan-Delta** (RVW9-2), auszuführen durch den `planner`, **erst nach** User-Freigabe von P-1…P-5 (inkl. **P-3 (e)**)

> **Reihenfolge-Zwang:** P-1…P-5 ⇒ Plan-Revision ⇒ **dann** W3-6. Vor der Freigabe darf **kein**
> Plan-Task angefasst werden; Rev. 0.8 ist nicht umsetzbar (`pending-approval:`, §17.12.4-Nachweis
> verlangt T-7/T-8/T-3/T-5, der Plan kennt sie nicht). **Bezug:** Plan Rev. 0.7,
> `status: APPROVED`, `revision: 0.7` (`:5-6`); alle Zeilenangaben dieses Abschnitts sind am
> Working Tree per Grep/Read **gemessen** (2026-09-29).

| # | Planstelle (Ist-Stand) | Forderlicher Soll | Quelle in dieser Spec |
|---|---|---|---|
| **PD-1** | **Frontmatter** `:1-13` — `status: APPROVED` (`:5`), `revision: 0.7` (`:6`), **kein** `pending-approval:` (Grep ⇒ **0** Treffer) | `pending-approval:`-Feld nach dem Muster der Spec (`docs/specs/2026-09-25-repository-documentation-consolidation.md:8`) mit dem Wortlaut: Rev. 0.8 — **P-1…P-5 (inkl. P-3 (e))** offen beim Auftraggeber, **E-9…E-13 (inkl. E-13c)** offen, Umfang W0–W8 freigegeben (2026-09-26, unverändert). **Bestehende** `status: APPROVED` / `approved:`-Zeilen **nicht** ändern. | §17.12.1, §17.12.2, Frontmatter `:8` |
| **PD-2** | **W3-6 `Files:`** `:4920-4921` — nennt `docs/INDEX.md`, `.meta-config/project.yaml`, `README.md`, `tests/test_doc_renderer.py` | **zwei** Einträge ergänzen: `config/project-config.schema.json` (T-8) und `tests/test_docs_consolidation_migration.py` (T-3 (a), T-4, T-5). `tests/test_doc_renderer.py` bleibt (T-2, T-3 (b)). | §17.12.4 T-2…T-5, T-8 |
| **PD-3** | **W3-6 `Ziel-AK`** `:4926` = **AC-20, AC-12** (E2E), **AC-38** | ergänzen um **AC-39, AC-42, AC-43, AC-44, AC-45, AC-46** (Reihenfolge in der Zeile wie in §9.1; **V-Check** bleibt **V2, V4** — die Begründung für `—` steht in §9.1 `:2596-2606`) | §9.1 (`:2549`, `:2583-2587`), §9.2 W3-Zeile (`:2629`) |
| **PD-4** | **W3-6 `Akzeptanz`** `:4927-4932` | die **beiden** Nachweiszeilen aus §17.12.4 aufnehmen: „`python3 -m pytest tests/test_docs_consolidation_migration.py -q` → gruen inkl. **2** neuer Enum-Tests und erweiterter Property-Menge (**beide** Pins)" und „`python3 -m pytest tests/test_doc_renderer.py -q` → gruen inkl. **5** neuer Tests **und** erweitertem `_IC22_ABSENCE_DEFAULTS`" | §17.12.4 Nachweiszeilen |
| **PD-5** | **W3-6 `Steps`** `:4938-4944` — vier Schritte, **keine** Reihenfolge-T-Angabe | die Reihenfolge **T-8 → T-3 → T-5** **explizit** als Schrittfolge bzw. als Zeile in `Interfaces:` aufnehmen; T-7 (Config-Zeile `index-owner` in `.meta-config/project.yaml:398-401`) **eigenes** benanntes Step-Feld. **Nicht** in W8-4 verschieben — V-D7 hat das gemessen und festgeschrieben | V-D7 (`:4487`), T-3/T-4/T-5/T-7/T-8 |
| **PD-6** | **W3-6 `Verifikation`** `:4933-4937` | die **beiden** pytest-Kommandos aus **PD-4** ergänzen (die Zeile `:4936` „`--validate` ist hier planmäßig rot" bleibt **wortgleich**) | §17.12.4 |
| **PD-7** | **W1-9 `Interfaces:`** `:2084` („**sechs** Properties aus IC-22") und **Step 2** `:2096` („Block mit sechs Properties ergänzen") — W1-9 ist `[x]`-abgeschlossen (`:2095-2098`) | **reine Textziffer-Korrektur** auf **fünf** (`tests/test_docs_consolidation_migration.py:46-50`; Schema `config/project-config.schema.json:2424-2469`), mit dem Zusatz, dass Rev. 0.8 die **sechste** Property `index-owner` in **W3-6** nachzieht (T-8). **Kein** erneutes Öffnen des Tasks, **kein** Code | P-3 (e), T-8 |
| **PD-8** | **W1-10 Step 2** `:2115-2118` (`[ ]`, **offen**) — will `index-mode`, `checks.strict`, `sources`, `volatile-facts` in **denselben** Block wie T-7; **CAN_RUN_IN_PARALLEL**-Liste der Runde 8 stützt sich auf die Annahme, W1-10 berühre **keine** `docs-consolidation`-Zeile | Reihenfolge **festhalten**: W1-10 Step 2 **vor** W3-6 ziehen (dann ist der Live-Block vor dem Delta vollständig) **oder** als Bestandteil von **W3-6** führen; `CAN_RUN_IN_PARALLEL` entsprechend berichtigen. **Zusatz:** ein in W1-10 gesetztes `sources` aktiviert den Gate-Zweig `apply_fact_blocks` (`doc_renderer.py:183`) — die Abhängigkeit aus E-10/V-D6 | RVW9-9, T-7, V-D6, E-10 |
| **PD-9** | **Plan-Trace-Matrix** `Ziel-AK`-Spalten: Ledger-Zeile **W1-9** `:5694` (trägt `config/project-config.schema.json`, `tests/test_docs_consolidation_migration.py`, **AC-39**), **W1-10** `:5693`, **W3-1** `:5705`; AC-Matrix **AC-39** `:6031` („W1-9") | die **neue** Zuordnung **W3-6 ← AC-39, AC-42…AC-46** in den Plan-Matrizen spiegeln, **ohne** die abgeschlossene W1-9-Zeile zu löschen (W1-9 trägt weiterhin AC-39 über den Schema-Block, W3-6 zusätzlich) | §9.1 `:2549`, §9.2 `:2629` + Fußnote ¹ |
| **PD-10** | **Plan-E-13-Zeile** `:7349` („E-13 — W1-10 teilweise gelandet", „*blockierend für den Abschluss von W1*") | **keine** Änderung aus dieser Spec: die Plan-Zeile zu „E-13" ist die **Rev.-0.5/0.6-E-13** und **nicht** die Rev.-0.8-Vorlage **E-13/E-13c** (§17.12.2). Der `planner` muss die Namensgleichheit beim Lesen **unterscheiden**, damit die offene Vorlage nicht mit der geschlossenen verwechselt wird | §17.12.2 |

**Abgrenzung des Plan-Deltas (was er ausdrücklich NICHT ist):** **keine** neue IC-/AC-/Task-/
Wellen-/V-Check-ID, **keine** Umnummerierung, **keine** inhaltliche Spec-Entscheidung — der
Delta **abbildet** die bereits spezifizierten T-1…T-8, AC-39 und AC-42…AC-46 auf den Plan.
**Offen und durch den Delta ausdrücklich NICHT entschieden:** E-9, E-10, E-11, E-12, E-13,
**E-13c** und OQ1. Insbesondere darf **PD-5** den Dokuanteil nicht nach W8-4 verschieben
(E-13a bleibt in der korrigierten Fassung eine **Empfehlung**, E-13 bleibt **offen**) und darf
**PD-4/PD-6** keinen `--validate`-Sollwert ändern.

**Vollständigkeits-Checkliste Rev. 0.8 (Coverage, keine Selbstbewertung):**

| Pflichtelement | Ort | Status |
|---|---|---|
| Problem / Fehlschlagstelle mit `Datei:Zeile` | §17.12.1 (P-1), IC-25 Einleitung | vorhanden |
| Interface Contracts (neue + geänderte) | **IC-25**, **IC-26**; geändert **IC-13**, **IC-15**, **IC-22** | vorhanden |
| Datenfluss (Wirkung auf den Pfad) | IC-25 Wertetabelle, IC-26/1–2, §17.12.4 Nachweisformen | vorhanden |
| Acceptance Criteria für **beide** Modi | **AC-42…AC-46**; geändert **AC-21**, **AC-39** | vorhanden |
| Testpin je AK (bestehend **oder** neu ausgewiesen) | §17.12.4 Modus-Übersicht + Teständerungsliste T-1…T-8 (**alle** Zeilen mit Testnamen) | vorhanden |
| Provider- und Projektname **nicht** im Code | IC-26/8, DECISION-1, `AGENTS.md:50` | vorhanden |
| Offene Fragen **nicht** entschieden | **E-9…E-13 einschließlich E-13c** (§17.12.2), OQ1 **unberührt** | vorhanden |
| **Trace-Matrix vollständig** (jedes AC ≥ 1 Welle, jede Welle ≥ 1 AC) | §9.1 (**AC-42…AC-46** ergänzt, K63), §9.2 W3/W8, Zählsatz | vorhanden |
| **Sollwert-Änderungen vollständig registriert** | **zwei**, beide in T-3 (K-78, V-D4) + Grep-Nachweis „keine weiteren"; Orte: Modus-Übersicht Zeile 8, T-3 (a)/(b), Coverage (RVW9-6) | vorhanden |
| **Wellen-Reihenfolge auflösbar** | V-D7: T-8 → T-3 → T-5, **alle W3-6**; E-13a entsprechend markiert (K-80) | vorhanden |
| **Plan führt Rev. 0.8 (V-D8)** | §17.12.4-Warnung, **V-D8** + **V-D8-Uebergabe PD-1…PD-10** (§17.12.5) | **Befund registriert**, Delta **benannt**, Ausführung **erst nach User-Freigabe** |
| **Testnamen belegt** (kein Wildcard) | §17.12.4 `::test_schema_declares_the_absence_defaults` `tests/test_docs_consolidation_migration.py:185` (RVW9-7) | vorhanden |
| **Threat Model zu (g) vollständig** (alle vier Fragen, inkl. Kopier-Pfad) | §12.3 Zeile g, Q3 (2 Bullets), Q4 (g **und** d), Bewertung „**sieben**" (K-81) | vorhanden |
| Risiko-/Finding-Nachweis | R7 (P-5), **V-D1…V-D8** (§17.12.5) | vorhanden |
| Kein `TBD`, kein `TODO`, kein unbenanntes Placeholder | gesamtes Dokument; alle neuen Aussagen mit `Datei:Zeile` oder Messbeleg | vorhanden |
| **Korrektur-Katalog der Runde 8** | **§17.12.6, K77…K86** (10/10 Findings, je mit `file:line`-Beleg) | vorhanden |
| **K-Eindeutigkeit belegt** (Muster K41) | Grep-Beleg 2026-09-29 über **Spec und Plan** (Repo-Wurzel; **beide** Legendenzitate: Spec-Legende **eingefroren** auf `K1…K45`, Plan-Legende `K1…K76` **maßgeblich** — Plan `:536` + `:6960`): **K1…K76** sind je **genau einmal** belegt — **K1…K45** in §17.10.5/§17.11.1, **K46…K53** in der **Plan-Legende** (Plan-Katalog Korrekturrunden 1–4, Spec-Verweise `:132`/`:3932`), **K54…K58** in §17.11.1, **K59…K70** in §17.11.5, **K71…K75** in §17.11.6, **K76** in der **Plan-Legende** (Plan `:536`, `:6808`, `:6829`, `:6839`, `:6960` — **gemessen**, Plan bleibt unverändert). **K77…K86** in §17.12.6. **Keine** Lücke, **keine** Doppelbelegung (RVW9-1 spec-intern, **RVW10-1 dokumentübergreifend** gegen den Plan nachgemessen) | vorhanden |
| Keine Umnummerierung bestehender IDs | Kopfblock Rev. 0.8, Revisionszeile 0.8, §17.12.6 | vorhanden |

#### 17.12.6 Korrektur-Katalog der Korrekturrunde zu Rev. 0.8 (K77…K86)

> **Eingang:** Concept-Review Runde 8,
> `docs/specs/2026-09-29-repository-documentation-consolidation-rereview-8.md`
> (`review-id: RVW-DOCS-CONSOLIDATION-R8`, round 8, `CHANGES_REQUESTED`, 0 kritisch / 5 major /
> 5 minor / 0 info). **Alle 10 Findings behoben.** **Neue Katalog-IDs ab K77; K1…K76 bleiben
> unberührt, keine Umnummerierung, keine neue IC-/AC-/Task-/Wellen-ID.**
> **Maßgebliche Obergrenze vor diesem Katalog: K76** — **gemessen** an der **Plan-Legende** (Plan `:536` „`K-*`
> (K1…**K76**)“, Plan `:6960` „**K76 bleibt die höchste K-Kennung**“; **nicht** K60, **nicht** K75 — §17.11.6 endete bei K75, der Plan ist seither **additiv** um K76 gewachsen (Plan `:6808`, `:6829`, `:6839-6843`). **RVW9-1:** der erste Wurf dieses
> Katalogs vergab **K61…K70** und überschrieb damit **zehn** bereits belegte Kennungen aus §17.11.5
> (`:4069-4078`, Korrekturrunde 5). Der Wurf ist **rein additiv** aufgelöst: die zehn neuen
> Einträge heißen jetzt **K77…K86**; **keine** der zehn bisherigen Bedeutungen wurde gestrichen.
> **Verifikationsmethode (K-77):** für `tests/test_docs_consolidation_migration.py:42-44` und
> `tests/test_doc_renderer.py:1090-1091` gilt das Read-Tool als
> **unzuverlässig** (es rendert die belegten Kommentarzeilen leer); die Belege wurden deshalb per
> **Grep** neu geführt.

| ID | Finding | Was geändert wurde | `file:line`-Beleg (Working Tree, 2026-09-29) |
|---|---|---|---|
| **K77** | **RVW8-1** (major) — falsche Messung: der Zählkommentar `:42` sei leer | **Drei Stellen auf den belegten Stand korrigiert.** Der Kommentar **existiert**; die frühere Fehlmessung ist im Spec als **Fehlmessung des Belegwerkzeugs** benannt, nicht als Befund. **K-3**: Träger auf `:42-44` (vorher „die Zeile ist leer"). **T-4**: jetzt **verbindlich** (Text in `:42` „six rows/five" → „seven rows/six"; `:44` **wortgleich**, „deferred to W7-2" gilt unverändert) — die Abbruchbedingung „fehlt der Kommentar, entfällt T-4" ist **ersatzlos gestrichen**. **RVW9-3: `:43` ist mitgezogen** — „# **sixth**" → „# **seventh**" (bei sieben IC-22-Tabellenzeilen ist der KE-Key die siebte). **V-D4**: Träger auf Kommentar **plus** `_EXPECTED_PROPERTIES`, Vokabel „reine Kommentar-Korrektur" **zurückgenommen**. | Beleg Neu (Grep, 2026-09-29): `tests/test_docs_consolidation_migration.py:42` (`# IC-22 enumerates six rows; five of them are \`docs-consolidation.*\` keys, the`), `:43` (`# sixth (\`knowledge-engine.okf.index-mode\`) belongs to a different block and is`), `:44` (`# deferred to W7-2. \`checks.strict\` is a nested key, so it is one property here.`). Spec-Stellen: `docs/specs/2026-09-25-repository-documentation-consolidation.md:4257` (K-3), `:4446` (T-4), `:4484` (V-D4). |
| **K78** | **RVW8-2** (major) — zweite, nicht registrierte harte Sollwert-Änderung `_IC22_ABSENCE_DEFAULTS` | **Registriert als zweite harte Sollwert-Änderung.** T-3 hat eine **zweite Zeile** (keine neue T-ID); die Formulierung „**die einzige echte** Sollwert-Änderung" ist **zurückgenommen**; beide Pins stehen in der **Modus-Übersicht Zeile 8**, in **T-3 (a)/(b)** und in der **Coverage-Checkliste** („Sollwert-Änderungen vollständig registriert"). **Erweiterung einer Menge, keine Absenkung.** Der von der Korrektur verlangte Grep nach weiteren Mengen-Pins ist **geführt** und im Spec protokolliert: **genau zwei** zu ändernde Sollwerte. **RVW9-6: die Verortung ist berichtigt** — die frühere Fassung nannte die „bleiben grün"-Tabelle; dort steht **keiner** der beiden geänderten Pins, sie listet die **unveränderten** Nachbarn. | Pin: `tests/test_doc_renderer.py:1092-1098` (`_IC22_ABSENCE_DEFAULTS`, hartes Fünf-Key-Dict), geprüft `:1371` (`assert _schema_absence_defaults(block_schema) == _IC22_ABSENCE_DEFAULTS`) in `::test_absent_block_is_noop` (`:1318`); `_schema_absence_defaults` `:1114-1130`, iteriert **alle** Block-Properties (`:1122`). Unberührt, **belegt**: `tests/test_docs_consolidation_migration.py:53` (`_EXPECTED_CHECKS_PROPERTIES`), geprüft `:112`; Fail-off-Defaults-Test **`::test_schema_declares_the_absence_defaults`** `:185-199` liest namentlich, prüft die Menge nicht. Spec: `:4445` (T-3), `:4401` (Modus-Übersicht Zeile 8), `:4418-4424` (bleiben-grün-Tabelle + K78-Verortungsvermerk), `:4249` (P-3 (e)). |
| **K79** | **RVW8-3** (major) — AC-42…AC-46 fehlen in der Trace-Matrix | **Fünf Zeilen in §9.1 ergänzt** (Wellen W3-6 bzw. E-13-abhängiger Dokuanteil, betroffene Dateien mit Anker, V-Check-Spalte „—" mit Begründung), **§9.2** W3- und W8-Zeile nachgezogen, **Zählsatz** korrigiert (W3: 14 → **19**; Summe AC 41 → **46**), **AC-21** um den `index-owner`-Bezug ergänzt, **AC-39** auf „W1, **W3-6**" erweitert, **§15 „Geändert"** um §9.1/§9.2 ergänzt. Begründungsabsatz für die `—`-Spalte **neu** (V1–V9 lesen `docs/**` bzw. `README.md` und beobachten den Gate-Zweig nicht — dieselbe Fehlerklasse wie die in Rev. 0.1 zurückgenommene AC-19/V9-Zuordnung). | Spec: `:2549` (AC-39), `:2565` (AC-21), `:2583-2587` (AC-42…AC-46), `:2596-2606` (V-Check-Begründung), `:2629` (§9.2 W3), `:2634` (§9.2 W8), `:2643-2656` (Zählsatz). |
| **K80** | **RVW8-4** (major) — Wellen-Reihenfolge von T-3/T-5/T-8 unauflösbar | **Aufgelöst, ohne E-13 zu entscheiden.** Die *technische* Unteilbarkeit ist eine **Messung** und als **V-D7** festgeschrieben: **T-8 → T-3 → T-5, alle in W3-6.** Daraus folgt zwingend, dass **E-13a in seiner bisherigen Form nicht durchführbar** ist und als Option **zurückgenommen** wurde (in der korrigierten Fassung weiterhin die Empfehlung). §9.1 (AC-39/AC-46), §9.2 (W3/W8), die Teständerungsliste (T-3/T-5/T-8) und die Nachweiszeile wurden **konsistent darauf abgestellt**. **E-13 selbst bleibt OFFEN** — offen ist nur noch der **Dokuanteil**. **RVW9-2: die Reihenfolge ist am Plan noch nicht umgesetzt** — dafür **V-D8** + **V-D8-Uebergabe PD-5** (§17.12.5). | Abhängigkeit gemessen: `config/project-config.schema.json:2470` (`additionalProperties: false`), Property-Bereich `:2424-2469`; `tests/test_docs_consolidation_migration.py:99-103` (`:101` Mengen-Assertion), `tests/test_doc_renderer.py:1371`; Enum-Testmuster `tests/test_docs_consolidation_migration.py:174-182`. Spec: `:4487` (V-D7), `:4333-4337` (E-13a/b), `:4445`/`:4447`/`:4450` (T-3/T-5/T-8), `:4461-4462` (Nachweiszeilen), `:2587` (AC-46), `:2549` (AC-39). |
| **K81** | **RVW8-5** (major) — Threat Model Zeile (g) unvollständig | **Alle vier Fragen zu (g) beantwortet.** Frage 3: **zwei** Gegenmaßnahmen-Bullets — der fail-closed Code-Zweig IC-25 (1) als **einzige garantierte** Absicherung, und der Kopier-Pfad als **ausdrücklich nicht akzeptiertes Restrisiko**; Frage 4: **(g)**-Eintrag mit **beiden** Ausprägungen (Tippfehler ⇒ eingefrorener Index, Recovery = Wert zurücksetzen; **kopierte Deklaration** ⇒ KE-Autorität stillschweigend aufgehoben, Recovery = `auto`/Zeile entfernen, **schwerer**, weil kein Fehler entsteht); der **vorbestehend fehlende (d)-Eintrag** ergänzt, damit die Bewertung „alle sieben" trägt. Bewertungsziffer **sechs → sieben**. **„Ausnahme wird von einem Consumer-Projekt kopiert"** ist nun ausdrücklich benannt. **RVW9-4: der Kopier-Pfad ist als Optionenzeile E-13c in §17.12.2 ausgewiesen** (zwei Entscheidungspunkte, Suboptionen, Empfehlung, Owner, Termin) und der Q4-Verweis zeigt auf **§12.3** statt §17.12.3. | Spec: `:2976` (Zeile g), `:2992-3006` (Frage 3), `:3008-3030` (Frage 4), `:3032-3042` (Bewertung), `:4335-4349` (E-13c). Konsistenz: §12.3-Frage-3-Bullet verweist auf die noch offene **E-13c**, **nicht** auf eine neue Pflicht. |
| **K82** | **RVW8-6** (minor) — §12.3 (g) überschätzt das Schema als geschlossenen Wächter | **Drei Stellen präzisiert:** IC-25 (neuer Begründungsblock vor dem Code), IC-13-Belegzeile des unbekannten Werts, §12.3 (g). Das Schema ist nun als **Autocomplete-/Tippfehler-Konvention** beschrieben, die harte Zusage ist der **Codepfad**; „Enum zu lassen" ist ausdrücklich **nicht** vertretbar. | Messung: `scripts/lib/config.py:342` („Schema validation … **if** jsonschema is available"), `:372-388` (`:388` „jsonschema not installed or validation error — **best-effort**", `pass`). Spec: `:1592-1600` (IC-25), `:1424` (IC-13), `:2976` (§12.3 g). |
| **K83** | **RVW8-7** (minor) — AC-42 (d): Anker deckt nur die `doc-indexer/1`-Hälfte | **Beleg aufgeteilt:** der `docs-facts`-Block auf `:629` (Aufruf) mit Definition `:531`, die Generator-ID auf `:635-639` (Footer-Block) mit Marker-Konstante `:371`. | Messung: `scripts/lib/doc_renderer.py:629` (`lines.extend(_facts_section(facts))`), `:531` (`def _facts_section`), `:635-639` (Footer: `FOOTER_BEGIN_MARKER` / `facts-hash` / `generator: doc-indexer/1` / `FOOTER_END_MARKER`), `:371` (`FOOTER_BEGIN_MARKER: str = …`). Spec: `:2301-2307` (AC-42 d). |
| **K84** | **RVW8-8** (minor) — Anker-Drift-Politik uneinheitlich, V-D1/V-D2 unvollständig | **Auswahlregel formuliert und angewendet**, Inventar **vollständig** registriert. Regel: Rev. 0.8 korrigiert genau die Anker in den **ohnehin geänderten** IC-/AC-Zeilen — angewendet auf **IC-15** (`:23`/`:24` → `:28`/`:29`); **alle übrigen 14 Fundstellen** sind mit Sollwert und Zielanker in V-D1 aufgenommen, damit sie nicht verloren gehen. **V-D2** um **AC-22** (`:2513`) und **§13 A4** (`:2968`) ergänzt. **RVW9-8: V-D1s Selbstverweis auf die angewandte Korrektur ist von `:1449-1450` auf `:1487-1488` berichtigt** (`:1449-1450` trägt den IC-14-Bereich). **RVW10-2: der Zwischenanker `:1465-1466` aus RVW9-8 war IC-13-Fließtext, nicht der Anker — auf die gemessenen `:1487-1488` gezogen (IC-15 ab `:1483`).** | Messung: `scripts/lib/spec_plan_scaffold.py:28` (`DEFAULT_FALLBACK_INDEX`), `:29` (`_FILE_INDEX_SKELETON`), `:30` (`_FILE_INDEX_SKELETON_MARKER`), `:80` (`def resolve_index_mode`), `:100` (`def scaffold_spec_plan_dirs`), `:102-104` (Early-Return), `:115-116` (Modus-Zweig), `:121` (Dateiende). Spec: `:1487-1488` (IC-15, angewendet), `:4481` (V-D1, Inventar), `:4482` (V-D2, Inventar). |
| **K85** | **RVW8-9** (minor) — AC-39: Belegquelle falsch attribuiert | **Klammer umgestellt** von „`.meta-config`-Ist-Stand" auf **Schema-Block-Ist-Stand + Test-Pin**, mit dem ausdrücklichen Hinweis, dass der Live-Block dort **nur zwei** Keys trägt. | Messung: `config/project-config.schema.json:2424-2469` (Block-Properties), `tests/test_docs_consolidation_migration.py:45-51` (`_EXPECTED_PROPERTIES`), `.meta-config/project.yaml:398-401` (**nur** `enabled: true` + `checks.strict: true`). Spec: `:2434-2438` (AC-39, Property-Herkunft). |
| **K86** | **RVW8-10** (minor) — Plan-Befund W3-7/`sources` nicht registriert; eine Testpin-Zeile namenlos | **V-D6 neu angelegt** (Planlücke, **nicht** inhaltliche Pflicht ⇒ **keine** Spec-Pflicht, Registrierung genügt). In §17.12.4 Zeile 4 wird der Test **namentlich** genannt inkl. Fall-Zuordnung. **RVW9-7: der Wildcard-Testname `::test_fail_off_defaults_*` in der Nachbarzeile derselben Tabelle ist durch den **realen** Namen ersetzt.** | Messung: Plan `docs/plans/2026-09-25-repository-documentation-consolidation.md:4946-4997` — `Files:` `:4948` nennt nur `README.md`, `llms.txt`, `ARCHITECTURE.md`; Steps `:4991-4997` ohne `sources`-Config-Zeile. `scripts/lib/doc_renderer.py:183` (`apply_fact_blocks`); `.meta-config/project.yaml:398-401` führt `sources` nicht. Testname (Grep): `tests/test_docs_consolidation_migration.py:185` `def test_schema_declares_the_absence_defaults() -> None:`. Spec: `:4486` (V-D6), `:4397` (§17.12.4 Zeile 4), `:4418` (bleiben-grün-Tabelle, korrekter Name). |

**Ergebnis der Korrekturrunde:** 10 Findings, **10 behoben**, 0 offen aus dieser Runde. **Keine**
inhaltliche Pflichtänderung wurde **neu** erfunden; **keine** bestehende ID wurde umnummeriert oder
gestrichen. **P-1…P-5 (inkl. P-3 (e) / „P-3-E") bleiben ZUR USER-FREIGABE AUSSTEHEND**,
**E-9…E-13 einschließlich der Suboption E-13c und OQ1 bleiben OFFEN**, `pending-approval:` besteht fort.

**Zweite Korrekturrunde zu Rev. 0.8 (Concept-Review Runde 9, 2026-09-29, `CHANGES_REQUESTED`,
0 kritisch / 2 major / 7 minor / 1 info) — 10/10 behoben, kein Revisions-Bump, kein ID-Zuwachs.**

| Finding | Sev | Behandlung in dieser Spec | Beleg |
|---|---|---|---|
| **RVW9-1** | major | Katalog **K61…K70 ⇒ K77…K86**; Vorspann auf „ab **K77**; **K1…K76** bleiben unberührt" und maßgebliche Obergrenze **K76** genannt (Plan-Legende, **gemessen**); **alle** Fundstellen nachgezogen (Frontmatter `:6`/`:8`, Kopfblock, IC-15 `:1465-1466`, IC-25 `:1592`, §9.1, §9.2 W3/W8, §15 Trace-Anker + Coverage, §17.12.1, §17.12.4, §17.12.5, §17.12.6, Revisionszeilen `:510-511`). **Die zehn bisherigen Bedeutungen (§17.11.5) sind unverändert.** | Grep 2026-09-29 über **Spec und Plan** (Repo-Wurzel; Stand in der **Plan-Legende** maßgeblich — Plan `:536`): **K1…K45** §17.10.5/§17.11.1 · **K46…K53** Plan-Legende (Plan-Katalog Runde 1–4) · **K54…K58** §17.11.1 · **K59…K70** §17.11.5 · **K71…K75** §17.11.6 — je **genau einmal** belegt; **K77…K86** genau einmal in §17.12.6 — **keine** Doppelbelegung. Coverage-Zeile „K-Eindeutigkeit belegt". |
| **RVW9-2** | major | **V-D8** als Plan-Befund registriert (Muster V-D6) + **V-D8-Uebergabe PD-1…PD-10** als forderlicher Plan-Delta (§17.12.5) + Warnung in §17.12.4. **Der Plan ist nicht geändert.** Ausführung **erst nach** User-Freigabe von P-1…P-5. | Plan gemessen: `:1-13` (Frontmatter, `revision: 0.7`, **kein** `pending-approval`), `:4920-4921` (`Files:`), `:4926` (`Ziel-AK`), `:4938-4944` (Steps), `:2080-2098` (W1-9, `[x]`, „sechs Properties" `:2084`/`:2096`), `:2115-2118` (W1-10 Step 2 `[ ]`), `:5693`/`:5694` (Ledger), `:6031` (AC-Matrix), `:7349` (Plan-E-13). Grep: `index-owner` **0**, `AC-4[2-6]` **0**, `pending-approval` **0**. |
| **RVW9-3** | minor | T-4 zieht `:43` mit: „# **sixth**" ⇒ „# **seventh**"; `:44` bleibt wortgleich. K-3 entsprechend präzisiert. | `tests/test_docs_consolidation_migration.py:43` (Grep): `# sixth (\`knowledge-engine.okf.index-mode\`) belongs to a different block and is`; IC-22-Tabelle `:1845-1851` — **sieben** Zeilen, davon **sechs** `docs-consolidation.*`, der KE-Key in `:1851` ist die **siebte**. |
| **RVW9-4** | minor | **E-13c „Kopier-Pfad"** als dritte Zeile der E-13-Optionentabelle + Suboptionen c(1)/c(2) mit Empfehlung, **Owner `main_chat`** und **Termin vor W3-6**; §12.3-Q3-Bullet auf E-13c umgestellt; Q4-Verweis §17.12.3 ⇒ **§12.3**. | §12.3 `:3000-3006` (Q3-Bullet), `:3030` (Q4 (g)); §17.12.2 `:4333-4335` (E-13a/b/c) + `:4339-4349` (E-13c-Suboptionen). |
| **RVW9-5** | minor | **P-3 (e)** = fünfte Zeile der P-Tabelle, **kein** sechstes P-Element; Zählauflösung als Kasten über §17.12.1; Kopfblock `:217-219` auf „keine neue Pflicht **außerhalb des bestehenden P-3**" präzisiert; Frontmatter `approved-scope` und §15 Trace-Anker mitgeführt. | §17.12.1 Kasten + P-Tabelle; Frontmatter `:6`/`:8`; §15 Trace-Anker. |
| **RVW9-6** | minor | K78-Verortung auf **Modus-Übersicht Zeile 8 / T-3 (a)(b) / Coverage** umgestellt; die „bleiben grün"-Tabelle trägt einen eigenen K78-Verortungsvermerk. | §17.12.4 Modus-Übersicht `:4401`, bleiben-grün-Tabelle `:4418-4424` + Verortungsvermerk `:4421-4424`, T-3 `:4445`. |
| **RVW9-7** | minor | `::test_fail_off_defaults_*` ⇒ **`::test_schema_declares_the_absence_defaults`** in der bleiben-grün-Tabelle, in V-D4 und in K86. | `tests/test_docs_consolidation_migration.py:185` (Grep): `def test_schema_declares_the_absence_defaults() -> None:`; Docstring `:186-192`, Asserts `:194-199`. |
| **RVW9-8** | minor | V-D1-Selbstverweis `:1449-1450` ⇒ **`:1487-1488`** (**RVW10-2**: der RVW9-8-Zwischenanker `:1465-1466` war IC-13-Fließtext, nicht der Anker). | Spec `:1487-1488` (`DEFAULT_FALLBACK_INDEX = "docs/INDEX.md"   # :28`, `_FILE_INDEX_SKELETON = "…"   # :29`) — identisch mit der Angabe in K84; `:1465-1466` = IC-13-Fließtext, IC-15 beginnt `:1483`. |
| **RVW9-9** | minor | Reihenfolge **W1-10 Step 2 vs. T-7** in T-7 festgehalten (vor W3-6 ziehen **oder** in W3-6 führen; `sources`-Aktivierung = E-10/V-D6) und als **PD-8** in die Plan-Übergabe aufgenommen. | Plan `:2115-2118` (Step 2 `[ ]`, „4 von 5 Properties"); T-7 `.meta-config/project.yaml:398-401`; `doc_renderer.py:183`. |
| **Info-Notiz zu §9.2 (kein eigenes R9-Finding; Label aus der R10-Tabelle, `rereview-10.md:59` — RVW9-8 selbst bleibt der minor-Befund)** | info | **§9.2** macht die AC-39-Zählkonvention sichtbar: W3-6 ist **keine** eigene Welle; Fußnote ¹ unter der §9.2-Tabelle, Zählsatz verweist darauf. | §9.2 W3-Zeile `:2629` + Fußnote ¹ `:2636-2641`; Zählsatz `:2648-2653`. |

**Ergebnis der zweiten Korrekturrunde:** 10 Findings, **10 behoben**, 0 offen. **P-1…P-5 (inkl.
P-3 (e)) inhaltlich unverändert** und weiterhin **ZUR USER-FREIGABE AUSSTEHEND**; **E-9…E-13
einschließlich E-13c und OQ1 bleiben OFFEN**; `pending-approval:` besteht fort; `status: APPROVED`
und `approved: 2026-09-26` bleiben unverändert; Umfang W0–W8 unverändert; **keine** neue
IC-/AC-/Task-/Wellen-/V-Check-ID; **keine** Umnummerierung bestehender IDs.

**Dritte Korrekturrunde zu Rev. 0.8 (Concept-Review Runde 10, 2026-09-29, `CHANGES_REQUESTED`,
0 kritisch / 1 major / 1 minor / 1 info) — 3/3 behoben, kein Revisions-Bump, kein ID-Zuwachs.**

| Finding | Sev | Behandlung in dieser Spec | Beleg |
|---|---|---|---|
| **RVW10-1** | major | **Katalog `K76…K85` ⇒ `K77…K86` umnummeriert** (rein additiv: **keine** der zehn Bedeutungen gestrichen, **keine** K-ID unterhalb K76 angetastet). **Alle** Fundstellen nachgezogen — Frontmatter `:8`; Kopfblock `:215`, `:233-234`; IC-15 `:1487-1488`; IC-25 `:1614`; §9.1 `:2596`; §9.2 `:2629`, `:2634`, `:2648`; §15 Trace-Anker `:3182`, `:3193`, `:3194`, `:3202`, `:3206`, `:3213`, `:3214` (Runde-10-Block, in dieser Korrekturrunde nachgetragen), `:3254`; §17.12.1 `:4249`, `:4257`; §17.12.2 `:4333`, `:4334`; §17.12.4 `:4418`, `:4419`, `:4421`, `:4445`, `:4446`, `:4450`, `:4461`, `:4462`; §17.12.5 `:4481`, `:4482`, `:4484`, `:4486`, `:4487`, `:4488`; Coverage `:4531`, `:4532`, `:4535`, `:4538`, `:4539`; §17.12.6 `:4542`, `:4547`, `:4549-4550`, `:4553`, `:4554`, `:4561-4581`; Revisionszeilen `:510`, `:511`; Kopfblock-Legende `:278`. **Maßgebliche Obergrenze auf den gemessenen Plan-Stand `K1…K76` korrigiert** (Spec `:4161` und §17.12.6-Vorspann `:4549-4550`); die Coverage-Zeile `:4539` nennt jetzt **beide** Legendenzitate. **Keine inhaltliche Pflicht geändert. Der Plan bleibt unverändert.** | Plan `:536` („`K-*` (K1…**K76**)“, „additiv angehängt am 2026-09-28: K76"), `:6808`, `:6829`, `:6839-6843`, `:6960` („**K76 bleibt die höchste K-Kennung** — es wird **nichts** umnummeriert und **keine** ID vergeben“). Grep 2026-09-29 über **Spec und Plan** (Repo-Wurzel), Definitionsträger je K-ID ausgezählt: **K1…K76 je genau einmal** — K13…K45 §17.10.5/§17.11.1 · K46…K53 Plan-Anlage F/G · K54…K58 §17.11.1 · K59…K70 §17.11.5 · K71…K75 §17.11.6 · **K76** Plan-Legende; **K77…K86 je genau einmal** §17.12.6 — **keine Lücke, keine Doppelbelegung**; **keine** verwaiste Referenz auf `K76…K85` oder `K61…K70`. |
| **RVW10-2** | minor | **V-D1-Selbstverweis auf den gemessenen Anker `:1487-1488` gezogen** (bisher `:1465-1466` — selbst falsch, IC-13-Fließtext). RVW9-8 damit **geschlossen**; der RVW10-Befund als **bestätigt** vermerkt. **Keine** inhaltliche Änderung an IC-15. | Spec `:1487` `DEFAULT_FALLBACK_INDEX = "docs/INDEX.md"   # :28`, `:1488` `_FILE_INDEX_SKELETON = "…"   # :29` (IC-15 beginnt `:1483`); `:1465-1466` = IC-13-Fließtext; `:1449-1450` = IC-14-Bereich. Fundstellen: V-D1 `:4481`, K-Katalog `:4568`, Register `:4589`. |
| **RVW10-3** | info | **Registriert, nicht geändert.** Vollständigkeits-Grep über `docs/`, `scripts/`, `tests/` nach `sixth|seventh` und `IC-22 row`: **zwei** Testträger derselben Ordnungs-Formulierung. Der erste (`tests/test_docs_consolidation_migration.py:43`) ist durch **T-4** abgedeckt und wird dort gezogen. Der zweite (`tests/test_doc_renderer.py:1090-1091`) liegt **außerhalb** der `Files:`-Liste dieses Fixes ⇒ **nur als Befund registriert, keine Testdatei geändert**, **keine** neue T-ID, **kein** Eingriff in T-3. | `tests/test_doc_renderer.py:1090-1091` (Grep 2026-09-29): `#: ``checks`` is a block whose only member is ``strict``; the sixth IC-22 row` / `#: (``knowledge-engine.okf.index-mode``) belongs to W7-2 and is out of scope.` IC-22-Tabelle Spec `:1845-1851` = **sieben** Zeilen, KE-Key in `:1851` ⇒ dieselbe Fehlerklasse wie T-4, **bleibt offen** für die nächste Korrekturrunde. Werkzeug-Fehlmessung erneut reproduziert (Read rendert beide Zonen leer, Grep liefert den Text). |

**Ergebnis der dritten Korrekturrunde:** 3 Findings, **3 behoben**, 0 offen. **P-1…P-5 (inkl.
P-3 (e)) inhaltlich unverändert** und weiterhin **ZUR USER-FREIGABE AUSSTEHEND**; **E-9…E-13
einschließlich E-13c und OQ1 bleiben OFFEN**; `pending-approval:` besteht fort; `status:` und
`approved: 2026-09-26` bleiben unverändert; Umfang W0–W8 unverändert; **keine** neue
IC-/AC-/Task-/Wellen-/V-Check-ID; **keine** inhaltliche Änderung an IC-25, IC-26, IC-13,
IC-15, IC-22, AC-42…AC-46, R7 oder §12.3 (g); **kein Produktionscode**, keine Testdatei
geändert; **der Plan bleibt unverändert** (V-D8 bleibt beim `planner` nach Freigabe).
