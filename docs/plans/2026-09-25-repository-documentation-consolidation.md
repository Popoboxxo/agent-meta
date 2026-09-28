---
plan-id: PLAN-DOCS-CONSOLIDATION-2026-09-25
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
title: Repository-weite Doku-Konsolidierung agent-meta — Implementation Plan
status: APPROVED
revision: 0.7
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
> **Genehmigungsumfang:** Die Freigabe umfasst die **Ausführung dieses Plans** (W0–W8, **50**
> Tasks — **K39** (Rev. 0.6) m1: 47 → 48 durch den neuen Task **W2-0** „Modul-Split"; **Rev. 0.7
> / K56: 48 → 50** durch die neuen Tasks **W2-9** „Ledger-Writer adressiert diesen Plan" (E-8) und
> **W2-8** „Volltests entkoppeln" (E-6); vorher 47)
> inklusive der im Plan mit Owner und Entscheidungsweg versehenen Entscheidungs-Points
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
> **Änderungsnotiz — Rev. 0.6 (2026-09-27): K18…K24 — U-1 (Modul-Split der Consistency-Checks)
> und U-2 (AC-30 auf `README.md` + `llms.txt` verengt), beide als bereits getroffene
> Nutzerentscheidungen umgesetzt; W2-DAG auf echte write-set-disjunkte Kanten umgestellt.**
> **Eingang:** die zwei **verbindlichen** Nutzerentscheidungen vom 2026-09-27 (über `main_chat` an
> den `orchestrator`) **U-1** und **U-2** sowie die **Baseline-Messung 2026-09-27** (Übergabe vom
> Parent, in dieser Revisionsrunde **kein** Shell-Zugriff — alle Zahlen sind als *Baseline-Messung
> 2026-09-27, Übergabe vom Parent* markiert und **nicht** neu behauptet). **Rev. 0.5 und die
> Rev.-0.2/0.3/0.4-Blöcke bleiben wortgleich stehen**; es wird **nichts** gelöscht. `status:
> APPROVED` bleibt **unverändert**. **Kein** Task-, Wellen-, AC-, IC-, NFA-, R- oder OQ-ID wurde
> umnummeriert oder gestrichen; der **einzige** neue Task ist **W2-0**; die **einzige** neue
> offene Frage ist **OQ10** (in der Spec geführt); **kein** Produktionscode, **keine** Tests, **keine**
> Runner-Änderung in dieser Revision. Katalog:
>
> - **K18 — U-1: Modulgrenzen festgelegt (verbindlich, Spec §4.1).** `scripts/lib/consistency/docs.py`
>   (heute **599** Zeilen) wird zur **Fassade**; die Prüfebene wird nach **Familien** aufgeteilt:
>   `docs_links.py` (V3, V4, `check_sync_cli_docs`, `check_ui_help_mappings`) · `docs_freshness.py`
>   (V1a/V1b, **V5**, V6) · `docs_wiki.py` (V7, V8) · `docs_index.py` (V2, V9). **Jeder** V-Check V1…V9
>   und **jeder** der drei Altchecks ist **genau einem** Modul zugeordnet — **12 Zuordnungen auf
>   4 Module**, ohne Lücke und ohne Doppeleintrag. **Jedes Modul < 600 Zeilen.** Die
>   Schnittlogik ist **die Frage, die ein Check stellt**; die Größengrenze ist **Folge**, nicht
>   Zweck. **Zur Wahl von V5** (es hätte sonst kein Modul): der dokumentierte Rollenbestand gegen
>   die generierten Rollen ist dieselbe Frage wie V1 und V6. **Zur Wahl von V8/V9** (spätere Wellen
>   W6-2/W8-4): beide prüfen eine abgeleitete Doku-Oberfläche gegen ihren Erzeuger.
>   **Abgrenzung gegen die Fach-Module M1–M4** (K21, Spec §4.1): *M1–M4 = was wird gebaut (Fach);
>   U-1-Module = wo der Datei-Check-Code liegt (Datei).* Die U-1-Module liegen **vollständig in M1**;
>   **kein** M-Modul wird umbenannt, M1–M4 behalten IDs und Bedeutung.
> - **K19 — Fassaden-Contract rückwärtskompatibel, `__all__` exakt benannt (Spec §4.1).**
>   `docs.py` enthält **keine** Check-Logik, nur Re-Exports, und exportiert **exakt** die in der
>   Spec §4.1 aufgeführten Namen. **Belege statt Vermutung:** `scripts/consistency-check.py:52-56`
>   importiert genau `check_readme_docs_index`, `check_sync_cli_docs`, `check_ui_help_mappings`
>   (Aufrufe `run_checks()` `:199-201`); `tests/test_doc_facts.py` referenziert über
>   `docs_lib` (`:90`) genau 29 Stellen (`check_no_manual_counts` `:2244`, `Severity` 9×,
>   `V1_SCAN_RELPATHS` `:2457`, `v1a_count_spans`/`v1b_version_spans` `:2463-2464`, die drei
>   Altchecks `:2533-2563`, `check_internal_links` `:2649-2853`, `V3_INERT_PREFIXES` `:2799`);
>   `tests/test_doc_facts_expected.py` importiert `docs` **nicht** (`:58-59` bindet nur
>   `scripts.lib.doc_facts`). **Konsequenz:** `consistency-check.py:52-56` und der bestehende
>   **positive** Registrierungs-Pin bleiben **unangetastet** — W2-0 ändert **keinen** Import.
> - **K20 — W2-DAG neu gezogen: aus einer strikten Kette werden echte write-set-disjunkte
>   Parallelgruppen.** **Befund:** Rev. 0.5 ließ **alle** Tasks W2-3…W2-7 `docs.py` **und**
>   `tests/test_doc_facts.py` schreiben (`Reihenfolge-/Abhängigkeitsmatrix`, Spalte
>   „Datei-Ownership") — eine Kette, deren Parallelität **nur** scheinbar war. **Neu:** **(a)** neue
>   Task **W2-0** „Modul-Split" als Welle-2-Einstieg, **verhaltensneutral** (Nachweis: `163 passed`
>   bleibt grün, `consistency-check.py --json` unverändert, **keine** neue Registrierung);
>   **(b)** W2-3 (V7), W2-5 (V6) und W2-6 (V2+V4) laufen **parallel** in **PG-2a** (max. 3), weil
>   ihre Write-Sets disjunkt sind; **(c)** W2-4 (V5) folgt sequenziell, weil es dasselbe Modul
>   (`docs_freshness.py`) und dieselbe Testdatei schreibt wie W2-5; **(d)** W2-7 (Registrierung,
>   Common-Gate, `report.py`) bleibt der **Abschluss**. **Entscheidung — Tests werden je Modul in
>   eigene Dateien aufgeteilt:** `tests/test_doc_wiki.py` (W2-3), `tests/test_doc_freshness.py`
>   (W2-0 → W2-5 → W2-4), `tests/test_doc_index.py` (W2-6) — **Begründung:** Parallelität ist nur
>   echt, wenn auch die **Test**-Write-Sets disjunkt sind; ein geteiltes `test_doc_facts.py` würde
>   jede Parallelgruppe sofort wieder zur Kette machen.
>   **Ehrliche Grenze, die nicht kaschiert wird:** „genau **eine** schreibende Task je Datei" ist
>   mit **vier** Modulen (U-1) und **fünf** modul-anfassenden Tasks **nicht** gleichzeitig erfüllbar.
>   **Verwendete Regel (Rev. 0.5-Praxis, nicht neu erfunden):** eine Datei wird pro
>   **Parallelgruppe** von höchstens **einer** Task geschrieben; mehrere schreibende Tasks
>   derselben Datei sind **ausschließlich sequenziell** (belegte Präzedenz: `docs.py` wird in
>   Rev. 0.5 von W2-1…W2-7 **und** W8-4 geschrieben; die Plan-Regel steht bereits so im
>   Self-Review, „Ownership"-Absatz). **Zyklenprüfung** und **Fail-closed-Klausel** (Spec
>   §17.10.4, Plan-Abschnitt „Ownership-Matrix, DAG und Zyklenprüfung") sind ausformuliert:
>   Topologische Ordnung **W2-1 → W2-2 → W2-0 → {W2-3, W2-5, W2-6} → W2-4 → W2-7** — **keine Zyklen**.
> - **K21 — Modulgrenzen gegen Verwechslung mit M1–M4 abgesichert.** Siehe K18-Absatz und Spec
>   §4.1. **Betroffen:** Wellenübersicht PG-2, Task **W2-0**, Ownership-Matrix, Rollback W2,
>   `Files:`-Listen von W2-3…W2-7.
> - **K22 — U-2: AC-30 auf `README.md` + `llms.txt` verengt; die 25 `docs/**`-Links werden
>   Follow-up.** Die Verengung ist **nur** tragfähig, wenn die verbleibenden Findings im
>   verbleibenden Scope liegen **und** vom bestehenden Task behebbar sind — beides ist belegt
>   (Weigerungsnachweis Spec §17.10.2): die **2** verbleibenden Findings sind `branch=="layout"`
>   in **`README.md:722`**/`:723` und liegen damit **im** Scope; `llms.txt` = **0**; die **25**
>   `branch=="link"`-Findings liegen **ausschließlich** unter `docs/**` und damit **vollständig
>   außerhalb**. **W8-2 genügt und wird nicht erweitert:** sein `Files:` enthält `README.md`, sein
>   `V-Check:` ist **V3**, und die Behebung ist ein Umschreiben zweier Layout-Einträge — **kein**
>   zusätzlicher Task. **Follow-up `F-DOCS-LINKS-2026-09-27`:** Owner `developer`, Termin
>   **2026-10-11**, Nachweis = Zählwert über `--json`, **kein** Exit-Code (RVW-12). **Was die
>   Verengung ausdrücklich nicht leistet** (und deshalb hier steht): V3 bleibt **ERROR** und meldet
>   die 25 weiter ⇒ `docs.internal_links` geht in W0–W8 **nie** auf 0 und `--validate → 0` bleibt
>   **dauerhaft unerreichbar**; maßgeblich ist die **Deltasperre** der Plan-Regel `W-VALIDATE-ROT`,
>   und die Severity-Frage ist als **OQ10** (Owner `orchestrator`, Frist **vor W8-4**) in der Spec
>   geführt. **Betroffen:** W2-GATE-ERRORS, W-GATE-TABLE (V3-Zeile), Task **W8-2**, Coverage-Matrix
>   (AC-30), Wellenblock **W8**, `W-VALIDATE-ROT`.
> - **K23 — zwei belegte Faktenkorrekturen an AC-30-Belegen (mitgenommen, weil K22 sie berührt).**
>   **(a)** Die Trace-Matrix-Zeile `| AC-30 | W8 | README.md:721-724 (M-8), docs/REQUIREMENTS.md:21 | V3 |`
>   war **doppelt veraltet**: `docs/REQUIREMENTS.md:21` (REQ-CMD-09) ist **kein** V3-Finding — die
>   Zeile nennt `howto/commands.md`, `CLAUDE.md`, `howto/instantiate-project.md` in **Backticks**
>   einer Tabellenzeile, V3 extrahiert aber nur **Link-Syntax** (`V3_INLINE_LINK_RE`,
>   `V3_REFERENCE_DEF_RE`, `V3_HTML_HREF_RE`; `_v3_link_targets`) — deckt sich mit der Baseline
>   (**0** Findings in der Datei). **(b)** `README.md:721` (`howto/`) und `:724` (`howto/configs/`)
>   **existieren**; die beiden Layout-Findings sind **`:722`**/`:723`. **Korrigiert** in Spec
>   (F15-N, §1.2, AC-09, AC-30, §9.1) **und** in diesem Plan (Task **W2-2**-Akzeptanz, **W8-2**,
>   W-GATE-TABLE-Fußnote, Coverage-Matrix). **Der Pfadbefund selbst bleibt** als manueller Befund
>   (F15-N) erhalten — er wird **nicht** gelöscht, nur **nicht** als V3-Nachweis geführt.
> - **K24 — V7-Baseline 10 → 11 korrigiert.** Rev. 0.5 nannte **10** Wiki-Seiten mit
>   `type: "Architecture"` (Messung 2026-09-26). Baseline-Messung 2026-09-27: **11** (11 distinkte
>   Dateien in `knowledge/wiki`). Korrigiert an **allen** maßgeblichen Stellen dieses Plans
> (W2-GATE-ERRORS, W-GATE-TABLE-Fußnote ³) und in der Spec (§10 `--strict`-Punkt 5); die
> Rev.-0.5-Belegzeile bleibt als **historischer** Stand lesbar. **Kein** Sollwert, sondern eine
>   Bestandsangabe mit unverändertem Termin **W5-3** und Owner `tester`.
> - **Ledger-Zählungen Rev. 0.6 (mitgeführt, §L-1).** `check_internal_links()` **27** Findings =
> **25** `link` + **2** `layout` + `llms.txt` **0**; Verteilung der 25: `docs/guides` 10 (features 5,
>   setup 5) · `docs/concepts` 13 (davon **8** in `docs/concepts/archive/`, **5** in
>   `docs/concepts/*.md`) · `docs/superpowers/plans/` 2 — **live** (ohne `archive/`) also **17**;
>   Dateigrößen vorher/nachher: `docs.py` **599 → ~70** (Fassade), `docs_links.py` ~330,
>   `docs_freshness.py` ~480, `docs_wiki.py` ~200, `docs_index.py` ~180, `report.py` **115**
>   (unverändert), `consistency-check.py` **280** (unverändert in W2-0); **Vorher**-Testbasis
>   `tests/test_doc_facts.py` + `tests/test_doc_facts_expected.py` = **163 passed**; Ist
>   `docs-checks` = **0**, `docs-findings` = **0** (`consistency-check.py --json` → `total 85`,
>   `errors 0`, `warnings 85`, enthaltene Checks `crossrefs.changelog-missing-entry` und
>   `placeholders.unknown` — **kein** `docs.`-Check liefert Findings).
> - **Betroffene Stellen dieses Plans (übersichtlich):** Frontmatter `revision`; dieser Block;
>   `File Structure` (Code + Tests); Wellen-Übersicht PG-2 und Wellen-Tabelle W2; Absatz
>   „Warum W2 ‖ W3 parallel"; Step-Agent-Map; Wellenblock **W2** (Verifikation, W2-GATE-ERRORS,
>   Rollback); **neue** Task **W2-0**; Tasks **W2-3…W2-7**; Wellenblock **W8** und Task **W8-2**;
>   W-GATE-TABLE (V3-, V7-Zeile); Reihenfolge-/Abhängigkeitsmatrix + **neue** Ownership-Matrix,
>   DAG-Kantenliste und Zyklenprüfung; Coverage-Matrix (AC-30, AC-09); DoD Punkt 2; Self-Review
>   (Ownership, Parallelgruppen); Abschnitt **L** (L-1, L-3-Zählung).
> - **Unverändert bleiben:** AC-01…AC-29 und AC-31…AC-41, IC-01…IC-24, NFA-01…NFA-11, R1…R20,
>   F1…F25, M-1…M-13, NG-1…NG-11, FI-1…FI-10, OQ1…OQ10 (OQ1, OQ10 bleiben **offen**), W0…W8,
>   K1…K17, E-01…E-15, B-1…B-5, OP-1, alle Rollbacks außer W2, `status: APPROVED`.
>
> **Änderungsnotiz — Rev. 0.7 (2026-09-27): K54…K58 — vier verbindliche Nutzerentscheidungen
> (E-5, E-6, E-7, E-8) sind eingearbeitet; zwei neue Tasks (W2-8, W2-9), ein neues Modul
> (`docs_freshness_v5.py`), ein neu gefasster V4-Scope und ein neu belegter Zählstand.**
> **Eingang:** die vier **verbindlichen** Nutzerentscheidungen vom **2026-09-27** (über `main_chat`
> an den `orchestrator`), **getroffen** und **nicht** neu zur Entscheidung gestellt. **Rev. 0.6 und
> die Rev.-0.5-/Rev.-0.2/0.3/0.4-Blöcke sowie die Korrekturrunden 1–4 (K25…K53) bleiben wortgleich
> stehen**; es wird **nichts** gelöscht. `status: APPROVED` bleibt **unverändert**. **Kein**
> Task-, Wellen-, AC-, IC-, NFA-, R- oder OQ-ID wurde umnummeriert oder gestrichen; die **zwei**
> neuen Tasks sind **W2-9** und **W2-8**; die **einzige** neue offene Frage ist **keine** —
> **E-5…E-8 sind entschieden**; **kein** Produktionscode, **keine** Tests, **keine** Runner-Änderung,
> **keine** Git-Mutation in dieser Revision. **Katalog:**
>
> - **K54 — E-5: V4 auf den README-Index-Scope begrenzt; Mechanismus aus Evidenz abgeleitet
>   (Volltext in Spec §17.11.2).** `check_readme_docs_index` (Check-ID **`docs.readme_index`**) prüft
>   **nicht** mehr, ob alle **205** nicht-Archiv-`docs/**.md` in `README.md` verlinkt sind. **Neu:**
>   V4 liest die **`##`-Region `Documentation Index`** in `README.md` (Überschrift mit
>   `Documentation Index`, heute `README.md:347`, bis zur nächsten `##`-Überschrift, heute `:381`)
>   und verlangt je dort **deklarierter** `docs/`-Kategorie (gemessen **7**): **(a)** das Verzeichnis
>   existiert, **(b)** die Kategorie trägt **mindestens einen** `docs/<kategorie>/…`-Link in der
>   Region; fehlt die Überschrift ganz ⇒ **ein** Finding (fail-closed, nicht vakuum-grün).
>   **IC-05-Pin unverändert:** Check-ID, Severity **ERROR**, `file` = `README.md` — und die
>   **Signatur `(root: Path) -> list[Finding]`, einargumentig** (**K59 / RVW-7-01**: die zweigliedrige
>   Form `(root, config=None)` ist die Signatur der **neun neuen** V-Checks, **nicht** die des
>   IC-05-gepinnten Altchecks; gemessen `docs_links.py:167`, Docstring `:170-172` („the parameter
>   list stays `(root)`"), Testpin `tests/test_doc_index.py` per `inspect.signature`).
>   **V2 ist unberührt** (liest `docs/INDEX.md`, **seiten**-genau,
>   OQ6 = tracked) — die **193** sind genau die Menge, die V2 ab W3-6 abdeckt; die README ist ein
>   **kuratierter** Einstieg, `docs/INDEX.md` der **vollständige** Index. **V3 unberührt** (prüft
>   Linkziele; V4 prüft **nie** eines) ⇒ **keine** Doppelmeldung. **Die 193 werden Follow-up**
>   `F-DOCS-README-INDEX-2026-09-27` (Owner `developer`, Termin **2026-10-11**; Nachweis =
>   **Issue-Liste + once-count außerhalb V4**, **kein** `docs.readme_index`-Zählwert — **K60 /
>   RVW-7-02**: V4 zählt nach E-5 **Kategorien**, nicht Seiten; ein V4-Zählwert **beobachtet diese
>   Menge nicht** und wäre als Nachweis **vakuum**). **Erwartungswert am gemessenen Baum: genau 1** Finding
>   (Kategorie `docs/se-cascade/` deklariert, ohne Link in der Region) ⇒ zweiter Registereintrag
>   `F-DOCS-README-INDEX-SE-2026-09-27`, gleicher Owner/Termin, Nachweis `docs.readme_index` = **0**.
>   **Verworfene Alternative, ausdrücklich benannt (nicht stillschweigend):** die **Rücknahme auf den
>   Alt-Scope `docs/api/*.md`** (Lesart C, Spec F18, `docs.py:111`). Begründung der Verwerfung in
>   Spec §17.11.2 in drei Punkten: **(b)** ein Check mit **0** Findings kann seine Schärfe nicht
>   belegen, und `docs/api/` wächst über W2–W8 planmäßig nicht ⇒ **vakuum-trivial**; **(c)** IC-05s
>   V4-Spalte („erweitert", F8/F23) und die Aussage „die bisherige Teilmenge bleibt eine **echte**
>   Teilmenge" würden zu einem leeren Satz; **fachlich** blieben genau die **sechs** übrigen
>   deklarierten Kategorien ungeprüft — die Blindstelle, unter der sich die 193 angesammelt haben.
>   **Ehrliche Grenze:** V4 hat damit **keinen** Termin 0 in W0–W8; maßgeblich ist die Deltasperre.
> - **K55 — E-5: Grenze gegen V2 und V3 ausdrücklich gezogen.** V2 = **Seite** fehlt in
>   `docs/INDEX.md`; V3 = **Linkziel** existiert nicht; V4 = **deklarierte Kategorie** ist nicht
>   repräsentiert. Ein toter Link in der Index-Region ist ein **V3**- und **kein** V4-Finding; V4
>   kann rot sein, während V3 grün ist. **Betroffen:** Task **W2-6** (`Interfaces`, `Akzeptanz`,
>   neue Testauswahl), W2-GATE-ERRORS V4-Zeile, W-VALIDATE-ROT, W-GATE-TABLE V4-Zeile + Fußnote,
>   Coverage-Matrix AC-12, DoD Punkt 2, Spec IC-05 V4-Zeile.
> - **K56 — E-6 und E-7: Taskmenge 48 → 50, Modulmenge 4 → 5, Zählstand neu gemessen.**
>   **E-6 → neuer Task W2-8** („Volltests entkoppeln"): `Files:` `tests/test_knowledge_engine.py`,
>   `tests/test_sharkord_service_name_migration.py`; Agent `senior-developer`; AK **AC-11 und
>   AC-13** (Nachweis der Wohlgeformtheit, **kein** neuer AC); `V-Check:` — (Querschnitts-Task ohne
>   eigenen V-Check, wie W2-0); `Depends on:` **W2-4**; `parallel_group:` — (sequenziell);
>   **DAG: unmittelbar vor W2-7**. **E-7 → neues Modul
>   `scripts/lib/consistency/docs_freshness_v5.py`** (V5, **≈ 55–70** Z) und **W2-4s `Files:`** wird
>   umgestellt von `docs_freshness.py` + `tests/test_doc_freshness.py` auf
>   **`docs_freshness_v5.py` (Create) + `tests/test_doc_freshness_v5.py` (Create)**.
>   **Größenfolge (verbindlich):** `docs_freshness.py` **592** Z (V1a/V1b + V6, **8** Z Reserve,
>   **kein** weiterer V-Check) · `docs_freshness_v5.py` **≈ 55–70** Z (V5) — **beide < 600** ✓.
>   Ohne E-7 läge V5 bei **647–662** Z und W2-4s eigenes Abnahmekriterium (`wc -l` < 600) schlüge
>   fehl. **Nebeneffekt, ausdrücklich benannt:** die Kante `W2-5 → W2-4` (Begründung: gemeinsame
>   Schreibmenge) ist **gegenstandslos** und bleibt als **historische** Kante sichtbar; **W2-4 wird
>   in Phase B frei** und hängt nur noch an W2-5. **Modulzuordnung bleibt 12/12 disjunkt**, jetzt auf
>   **5** Module (K56). **Zählstand, in dieser Revision selbst gemessen:** Tasks **48 → 50**,
>   Checkboxen **199 → 207** (`^- \[x\]` = **59** unverändert, `^- \[ \]` = **140 → 148**);
>   Gegenprobe 44 Tasks × 4 + 5 × 5 + 1 × 6 = **207**. **Keine Zahl ist geschätzt**; Herleitung und
>   Partitionsmessung in Abschnitt **L-1, Rev.-0.7-Anhang**.
> - **K57 — E-8: `TASK_HEADER_RE` wird um die Wellen-/Task-Header erweitert; neuer Task W2-9.**
>   `scripts/lib/plan_identity.py:27-30` definiert `TASK_HEADER_RE` als `(?m)^###[ \t]+Task[ \t]+
>   ([A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*)[ \t]*(?::|[—–-])?[ \t]*(.*?)[ \t]*$` — das literale
>   Schlüsselwort `Task` ist Pflicht; dieser Plan schreibt `### W2-0:` ⇒ **kein** Treffer ⇒
>   `_task_blocks()` (`plan_ledger.py:71`) leer ⇒ `unmatched` ⇒ `sys.exit(1)` (`:272`).
>   **Zweiter Teilfehler — KORRIGIERT in Korrekturrunde 5 (K66 / RVW-7-08):** `normalize_task_id`
>   (`plan_identity.py:63-73`) lässt `W2-0` **heute schon unverändert** — der Durchreich-Zweig
>   `return raw` greift, weil `TASK_ID_RE = ^task-[0-9]+$` (`:18`) **nicht** passt. **Gemessen:**
>   `normalize_task_id("W2-0") == "W2-0"` — **verhaltensgleich abgedeckt** durch
>   `normalize_task_id("custom") == "custom"` (`tests/test_plan_identity.py:100`, **derselbe**
>   Durchreich-Zweig `return raw`); der **`W2-0`-Pin wird in W2-9 Akzeptanz (f) neu angelegt**
>   (**K71** — der Anker `:96-101` aus Korrekturrunde 5 war falsch: dort steht
>   `test_normalize_task_id` mit den Asserts `"3"/"TASK-3"/"task-3"/"custom"/"task-"`, **kein**
>   `"W2-0"`; der Sachstand ist richtig, nur der Beleg war es nicht). **Der in
>   Rev. 0.7 behauptete Teilfehler (b) existiert also nicht**; W2-9 muss **ausschließlich** den
>   Regex-Zweig (a) ändern. **Wichtig für die Umsetzung:** eine „Korrektur" von (b) — etwa ein
>   Vorher-Nachher-Umstellen von `W2-0` auf eine andere Form — **bricht den Round-Trip** und ist
>   deshalb **verboten**; (b) wird nur als **No-op-Pin** fortgeführt.
>   **W2-9 behebt (a) — und nach Korrekturrunde 5 ausschließlich (a).** **Position: Phase 0 von W2,
>   unmittelbar nach W2-0 und vor PG-2a** ⇒
>   **„Ledger-Writer einsetzbar ab Task W2-9"** — also für **W2-6, W2-4, W2-8 und W2-7**.
>   **Ausdrücklich: jetzt noch nicht.** Bis W2-9 gilt die **K53-Interim-Regel** (manuelles Abhaken
>   durch den Orchestrator mit Datum, Commit-Hash und Task-ID) **unverändert**; sie **endet** mit
>   W2-9 und wird **nicht** stillschweigend beendet. **Betroffen:** Task W2-9, DAG-Kanten 16,
>   Ownership-Matrix, DoD Punkt 14, Abschnitt L-1, PG-2-Diagramm.
> - **K58 — Faktenkorrektur zum Werkzeug-Ort.** Auftrag und Korrekturrunden-4-Block nennen
>   `TASK_HEADER_RE` als in `scripts/lib/plan_ledger.py` liegend. **Gemessen:** die **Definition**
>   steht in `scripts/lib/plan_identity.py:27-30`; `plan_ledger.py` ist der **Konsument** (Import
>   `:25`, `finditer` `:71`, Tupel-Entpackung `:133`, `unmatched` `:172`/`:182`). W2-9 besitzt
>   deshalb **beide** Dateien — `plan_ledger.py` wird **nur** geschrieben, falls sich der
>   Zwei-Gruppen-Vertrag des Treffers ändert. **Belegt** an den beiden Testdateien
>   `tests/test_plan_identity.py` (prüft `TASK_HEADER_RE` direkt, `:26-50`) und
>   `tests/test_plan_ledger_writer.py` (Round-Trip `update_plan_ledger` ↔ `parse_plan_ledger`).
> - **Betroffene Stellen dieses Plans (übersichtlich):** Frontmatter `revision`; **Genehmigungsumfang**
>   (48 → **50** Tasks); dieser Block; **Plan-Legende** (E-Namensraum `E-5…E-8` = entschieden,
>   K-Bereich `K1…K58`); Global Constraints; `File Structure` (Code + Tests + Modulzahlen);
>   Wellen-Übersicht PG-2 und Wellen-Tabelle W2; Absatz „Warum W2 ‖ W3 parallel"; Step-Agent-Map;
>   Wellenblock **W2** (Verifikation, W2-GATE-ERRORS, W-VALIDATE-ROT, Rollback); Tasks **W2-4**,
>   **W2-6**, **W2-7**; **neue** Tasks **W2-9** und **W2-8**; Reihenfolge-/Abhängigkeitsmatrix +
>   Ownership-Matrix + DAG-Kantenliste + Zyklenprüfung; Coverage-Matrix (AC-11, AC-12, AC-13);
>   DoD Punkt 2, 12 und 14; Self-Review; Abschnitt **L-1** (**Rev.-0.7-Anhang** mit Zählung und
>   Ende der Interim-Regel); **neuer** Schlussabschnitt „Entscheidungs-Abschluss Rev. 0.7".
> - **Unverändert bleiben:** AC-01…AC-41, IC-01…IC-24, NFA-01…NFA-11, R1…R20, F1…F25, M-1…M-13,
>   NG-1…NG-11, FI-1…FI-10, OQ1…OQ10 (**OQ1** und **OQ10** bleiben **offen**), W0…W8, K1…K53,
>   **E-1…E-4** (bleiben **offen, unentschieden**), E-01…E-15, B-1…B-5, OP-1, alle Rollbacks außer
>   W2, `status: APPROVED`, **alle Zeilen der Rev.-0.6- und Rev.-0.5-Blöcke sowie der
>   Korrekturrunden 1–4** (dort steht zu E-5…E-8 „offen, unentschieden" — das ist der **datierte
>   Stand vor der Entscheidung**; **maßgeblich** sind die **Plan-Legende**, dieser Block und der
>   Schlussabschnitt „Entscheidungs-Abschluss Rev. 0.7").
>
> **Korrekturrunde 5 (Rev. 0.7, K59…K70) — Concept-Review vom 2026-09-27 über Rev. 0.7:
> `CHANGES_REQUESTED`, 0 kritisch · 5 major · 4 minor · 2 info; `validator`: `PASS_WITH_NOTES`,
> 0 Blocker. Volltext des Zuordnungsregisters: Abschnitt „Korrekturrunde 5" am Ende dieses Plans.**
> **Kein Revisions-Bump** — `revision: 0.7` und `status: APPROVED` bleiben unverändert (Muster
> Korrekturrunde Rev. 0.6 Runde 1). **Kein** Produktionscode, **keine** Tests, **keine**
> Runner-Änderung, **keine** Git-Mutation in dieser Runde. Die Korrekturen wirken **ausschließlich
> auf Plan- und Spec-Text**; dort beschriebene Codeänderungen sind **Pflichten für W2-6, W2-8 und
> W2-9**, nicht ausgeführte Änderungen. **Keine** Task-, AC-, IC-, R-, OQ-, V-Check- oder F-ID
> wurde umnummeriert oder gestrichen; **W2-8/W2-9 behalten ihre IDs**, **W2-9 wird angepasst, nicht
> ersetzt**; **keine** neue Task-ID, **keine** neue offene Frage, **kein** neuer Sollwert.
> **Die Korrekturrunden 1–4, die Rev.-0.6- und Rev.-0.5-Blöcke und der Abschnitt
> „Entscheidungs-Abschluss Rev. 0.7" bleiben wortgleich** — diese Runde ist rein additiv.
> **Katalog (jede Kennung genau einmal belegt, Muster K41):**
>
> - **K59 — RVW-7-01 (major): IC-05-Pin-Zitat korrigiert.** Die Form `(root, config=None) ->
>   list[Finding]` ist die Signatur der **neun neuen** V-Checks; V4 ist **einargumentig**:
>   `check_readme_docs_index(root: Path) -> list[Finding]`. **Gemessen:** `docs_links.py:167`,
>   Docstring `:170-172` („the parameter list stays `(root)`"), Testpin
>   `tests/test_doc_index.py::test_v4_keeps_signature_and_severity` (`inspect.signature`, Parameterliste
>   `== ["root"]`). **Betroffen:** Plan-Kopf K54, Spec-Kopf **E-5**, Spec-Revisionszeile `0.7`,
>   Spec-§17.11.1 K54. **Unberührt:** IC-05 selbst (`:944-954`) — dort steht „Bestehende drei Checks
>   bleiben unverändert in Signatur und Severity", **ohne** Signatur-Literal; das ist korrekt und
>   wird nur um den **gemessenen** Beleg `(root)` ergänzt.
> - **K60 — RVW-7-02 (major): 191 aufgelöst zu 193, Nachweis messbar gemacht.** **Befund:** die
>   Herleitung „`docs/`-Baum **205** außerhalb `archive/`, davon **14** in `README.md` genannt ⇒
>   **191**" mischt **Einheiten**: die **14** genannten `docs/`-Pfade sind **12** `.md` + **2**
>   `.html` (`docs/ui/agent-graph.html`, `docs/ui/admin-ui.html`), der **205**-Bestand ist
>   `.md`-only. **Korrekt: `205 − 12 = 193`.** **Gemessen in dieser Runde** (Read/grep
>   `README.md:309`, `:354-376`): **14** eindeutige `](docs/…)`-Linkziele im **gesamten**
>   `README.md`, davon **12** `.md` — dieselbe Menge wie in der Index-Region `:347-381`. **Spec
>   §17.11.2 Lesart B rechnet bereits `193`**; §17.11.3 nannte `191` ⇒ **innerer Widerspruch der
>   Spec, zugunsten 193 aufgelöst.** **Zweit-Befund: der Nachweis war vakuum.** V4 zählt nach E-5
>   **deklarierte Kategorien**, nicht Seiten ⇒ `docs.readme_index` ist bei Registrierung **0** bzw.
>   **1** und **beobachtet die Menge nicht**. **Neuer Nachweis (verbindlich, beides zusammen):**
>   (a) die **Issue-Liste** des Follow-ups nennt die betroffenen Seiten **namentlich**;
>   (b) der **once-count** ist ein reiner Shell-Zählaufruf **außerhalb** des Check-Frameworks
>   (`find docs -name '*.md' -not -path '*/archive/*' -not -path '*/_archive/*' -not -name
>   'INDEX.md' -printf '%p\n' | while read -r f; do grep -qF "$f" README.md || echo "$f"; done |
>   wc -l`) ⇒ Baseline **193**, Ziel **0**. **K75 (Korrekturrunde 6) — die Baseline ist
>   zukunftssicher gefasst, weil der Aufruf `-not -name 'INDEX.md'` enthält:** heute ist die
>   Exclusion **folgenlos** (`docs/INDEX.md` existiert **nicht**, Universe **205** ⇒ **193** ✓), und
>   **ab W3-6** liefert **derselbe** Aufruf **192** (Universe **204**, davon **12** in `README.md`),
>   während die Baseline im Register **193** bleibt. **Deshalb gilt die Zahl als
>   `Universe 205 − 12 verlinkt = 193` (Baseline-Messung 2026-09-27, Stand vor W3-6)**, und der
>   Aufruf ist **nur für diesen Bezugszeitpunkt** der Sollwert — der **Sollwert 0** (Ziel) ist davon
>   **nicht** betroffen. **Ausdrücklich:** ein `docs.readme_index`-Zählwert ist
>   als Nachweis **unbrauchbar** und wird **nicht** mehr geführt. **Lesart-Regel (Muster K36/K42):**
>   jedes verbleibende Vorkommen von **191** in Spec und Plan, das die **Seitenzahl** meint, ist
>   als **193** zu lesen; **wortgleich korrigiert** sind Kopf, W-GATE-TABLE V4, W-VALIDATE-ROT,
>   W2-6, W2-8, Coverage-Matrix, DoD, L-1 und beide Follow-up-Register; **wortgleich stehen
>   bleiben** Korrekturrunde 3/4 und der Entscheidungs-Record (dort der datierte Stand vom
>   2026-09-27). **Ausdrücklich eingeschlossen** sind Stellen, die wie Records wirken: die
>   `approved-scope`-Zeile im Spec-Frontmatter, die Selbstreview- und Legacy-Erzählabsätze sowie die
>   Zustandstabelle „W-GATE-TABLE" im Plan.
> - **K61 — RVW-7-03 (major): die V4-Tests werden namentlich ersetzt, nicht angepasst.** W2-6
>   nannte „drei V4-Tests"; im Working Tree pinnen **sieben** Tests die von E-5 **entfernte**
>   Per-Seiten-Semantik. Vollständige Namen, Alt-Test → Ersatz-Test, Grün/Rot-Einstufung und der
>   **Nicht-Vakuum-Nachweis** (Plan-Standard **K33**) stehen in **W2-6, Akzeptanz V4**.
>   **Kern des Befunds:** **6 der 7** Fixtures schreiben `README_RELPATH, "# readme\n"` — **ohne**
>   `Documentation Index`-Überschrift (**K73**: **R7 hat kein Fixture**, sondern liest den echten
>   Baum; seine Rötung hat eine eigene, in R7 selbst genannte Ursache) ⇒ unter der fail-closed-Regel
>   feuert V4 **in diesen 6 Fixtures**, und
>   W2-6 **Schritt 3** („Tests grün beobachten") ist damit **unerreichbar**.
> - **K62 — RVW-7-04 (major): `scripts/lib/consistency/spec_plan.py` ist der dritte Konsument von
>   `TASK_HEADER_RE` — er kommt in W2-9s `Files:`.** **Gemessen:** `_parse_plan_tasks`
>   (`spec_plan.py:557`, Regex `:55` aus `plan_identity.py:27`) liest dieselbe Regex, extrahiert
>   Dep-Tokens aber mit **hart kodiertem** Muster `task-\d+|\d+` (`:570`) und speist
>   `check_plan_file_overlap` (`:533`) — das Instrument der **fail-closed**-Ownership-Klausel
>   (K20, Spec §17.10.4). **Folge nach W2-9, wenn nur `plan_identity.py` geändert wird:** `**W2-3**`
>   ⇒ `task-2`/`task-3`, `**W2-0**` ⇒ `task-0`; `find_dependency_errors` (`orchestration.py:207-216`)
>   meldet **dangling dependency** und `validate_plan` (`:287-289`) **bricht vor dem
>   Overlap-Check ab** — die Ownership-Prüfung fällt damit komplett aus statt falsch zu sein.
>   **Entscheidung: Muster auf `W\d+-\d+` erweitern und `spec_plan.py` in `Files:` aufnehmen**, mit
>   Testpflicht; die verworfene Alternative (plan-getriebener Fanout bleibe ungenutzt) ist in
>   **W2-9** begründet.
> - **K63 — RVW-7-05 (major): Mechanismus (ii) ist an W2-8s Position unerreichbar; (iii) nennt
>   jetzt das Werkzeug.** Gemessen: V4 nimmt **kein** `config` (`docs_links.py:167`), der Runner
>   ruft die Altchecks unbedingt mit `_AGENT_META_ROOT` (`consistency-check.py:40`, `:199-201`) —
>   `--root` (`:252`, `:257`) leitet sie **nicht** um —, und das Common-Gate, das
>   `docs-consolidation.enabled: false` auswertet, entsteht erst in **W2-7** (Kante 18), also
>   **nach** W2-8. Zusätzlich schließt Akzeptanz (d) jeden Produktivcode-Eingriff aus. (ii) ist
>   damit doppelt festgefahren und wird aus W2-8s zulässiger Liste **gestrichen** (mit Begründung
>   als **spätere** Option erhalten); (iii) wird auf das **Werkzeug `consistency-check.py --json`**
>   festgeschrieben, denn `sync.py` hat **kein** `--json` (nur `--validate`, `--validate-se`,
>   `--validate-spec-plan`).
> - **K64 — RVW-7-06 (minor): Extraktionsregel wortgleich nach W2-6.** Die Regel „jeder
>   `docs/<kategorie>/`-Pfad, der in der Region genannt wird" stand **nur** in der Spec
>   (§17.11.2). **Überschriften-only** ergäbe **6** statt **7** — `docs/architecture/` erscheint
>   **ausschließlich** im Link `README.md:371`, nicht in einer `###`-Überschrift. Beide Lesarten
>   liefern denselben Sollwert **1** (die Stabilität des Sollwerts ist damit **kein** Argument gegen
>   die Präzisierung). Regel + 7/6-Lesart stehen jetzt **wortgleich** in W2-6.
> - **K65 — RVW-7-07 (minor): Vorrangregel zwischen fail-closed und fail-soft.** Gemessen:
>   `docs_links.py:183` lässt `not readme.exists() or not docs_dir.is_dir()` **gemeinsam** ⇒ `[]`.
>   Die Vorrangregel (W2-6) entscheidet: **fehlender `docs/`-Baum ⇒ `[]`** (fail-soft, einzige
>   Ausnahme); fehlt `README.md` **oder** die `Documentation Index`-Überschrift bei vorhandenem
>   `docs/` ⇒ **1** Finding (fail-closed).
> - **K66 — RVW-7-08 (minor): K57-Teilfehler (b) war falsch diagnostiziert.** Gemessen:
>   `normalize_task_id("W2-0") == "W2-0"` **heute schon** (Durchreich-Zweig, **verhaltensgleich
>   abgedeckt** durch `normalize_task_id("custom") == "custom"`, `tests/test_plan_identity.py:100`
>   — **derselbe** Zweig; der **`W2-0`-Pin wird in Akzeptanz (f) neu angelegt**, **K71**). Nötig ist
>   **nur** (a). (b) wird **gestrichen** und
>   durch einen **No-op-Pin** ersetzt; eine „Reparatur" von (b) bricht den Round-Trip. Siehe
>   Plan-Kopf K57 und **W2-9**.
> - **K67 — RVW-7-09 (minor): V4 in den späteren `--validate`-rot-Aufzählungen.** V4 ist **heute
>   registriert** (`consistency-check.py:53`/`:201`) und hält **1** ERROR, stand aber in den
>   Zeilen **W3-7 … W8-1** und **W8-2 … W8-4** der Regel `W-VALIDATE-ROT` sowie in Spec §10
>   nicht. Ergänzt; zusätzlich ist der **heutige Arbeitsbaum-Zustand** des V4-Teils von W2-6
>   (Generalisierung ⇒ **193** ERROR) als Ursache der zwei roten Volltests benannt (L-1 W2-6).
> - **K68 — RVW-7-10 (info): Docstring-Scope als Plan-Pflicht für W2-6.** `docs_links.py:8-10` und
>   `:168-177` nennen weiter den Vor-E-5-Scope („pre-W2 subset stays a real subset"). **Hier wird
>   kein Code geändert**; die Korrektur ist als **Pflicht in W2-6** festgeschrieben (Docstring des
>   Moduls und der Funktion an den E-5-Scope).
> - **K69 — RVW-7-11 (info): Supersessions-Verweis — bewusst nicht in Runde 4.** Korrekturrunde 4
>   trägt **keinen** lokalen Verweis auf die nachfolgende Runde; der Vorrang ist **global** über
>   Plan-Legende, Rev.-0.7-Block und „Entscheidungs-Abschluss Rev. 0.7" regelkonform hergestellt
>   (Muster K36/K42). **Entscheidung: keine Änderung an Runde 4** — sie ist **wortgleich
>   festgeschrieben**, und ein eingefügter Verweis würde genau die Wortgleichheit brechen, die diese
>   Runde schützt. Der Verweis wird **hier** geführt (Korrekturrunde 5 ist die jeweils jüngere
>   Runde und damit der gültige Vorrang).
> - **K70 — Validator-Notizen `n1`…`n5`: explizite Zuordnung, jede einzeln begründet.** `n1` —
>   **bewusste Nicht-Zuordnung**: K6 ist im Rev.-0.2-Block (Plan `:852`) nur als Bereichsangabe
>   „Ausführungskorrekturen K1–K6" geführt; dieser Block ist **wortgleich festgeschrieben** und
>   **vorbestehend**, außerhalb des Rev.-0.7-Scopes. `n2` — **behoben** (Spec §16, Präzisierung der
>   ID-Tabelle: W0-5 existiert nicht, W0 hat **6** Tasks). `n3` — **bestätigte Bewusstant**, keine
>   Änderung. `n4` — **bestätigter Bewusstant**, keine Änderung. `n5` — **kosmetisch, bewusste
>   Nicht-Zuordnung**: die **Plan-Legende** ist maßgeblich, beide OQ-Listen stimmen inhaltlich.
>   Volltext in der Noten-Tabelle des Abschnitts „Korrekturrunde 5".
>
> **Betroffene Stellen der Korrekturrunde 5 (übersichtlich):** Plan-Kopf (K54, K57, **neue**
> K59…K70-Liste), Plan-Legende (`K1…K58` → `K1…K70`), W-GATE-TABLE V4-Zeile, W-VALIDATE-ROT
> (alle **vier** Zeitraumzeilen), Tasks **W2-6**, **W2-8**, **W2-9**, Coverage-Matrix AC-12, DoD
> Punkt 2, L-1-Anhang (W2-6-Zeile), Follow-up-Register + Zuordnungsnachweis, **neuer** Abschnitt
> „Korrekturrunde 5"; Spec: Kopf E-5, Revisionszeile `0.7`, IC-05, §10 `--validate`, §16
> (Präzisierung, `n2`), §17.11.1 (K54, K57), §17.11.2, §17.11.3, **neue** §17.11.5.
> **Unverändert bleiben:** alle Checkboxen (**keine** gesetzt, gestrichen oder ergänzt), alle
> Task-/AC-/IC-/R-/OQ-/V-Check-/F-IDs, `revision: 0.7`, `status: APPROVED`, die Korrekturrunden
> 1–4, die Rev.-0.5-/Rev.-0.6-Blöcke, „Entscheidungs-Abschluss Rev. 0.7" und alle Code-Dateien.
>
> **Korrekturrunde 6 (Rev. 0.7, K71…K75) — zweites Concept-Review über Rev. 0.7:
> `CHANGES_REQUESTED`, 0 kritisch · 1 major · 3 minor · 1 info; **rein mechanisch**, **kein**
> erneuter Sachentscheid. `validator`: `PASS_WITH_NOTES`, 0 Blocker. Volltext des
> Zuordnungsregisters: Abschnitt „Korrekturrunde 6" am Ende dieses Plans.** **Kein Revisions-Bump** —
> `revision: 0.7` und `status: APPROVED` bleiben unverändert (Muster Korrekturrunde Rev. 0.6 Runde 1
> und Runde 5). **Kein** Produktionscode, **keine** Tests, **keine** Runner-Änderung, **keine**
> Git-Mutation, **keine** Löschung oder Änderung der **3 uncommitteten W2-6-Dateien**
> (`scripts/lib/consistency/docs_index.py`, `tests/test_doc_index.py`,
> `scripts/lib/consistency/docs_links.py`). Die Korrekturen wirken **ausschließlich auf Plan- und
> Spec-Text**. **Keine** Checkbox gesetzt, gestrichen oder ergänzt. **Keine** Task-, AC-, IC-, R-,
> OQ-, V-Check- oder F-ID umnummeriert oder gestrichen; **W2-8/W2-9 behalten ihre IDs**, **W2-9
> wird ergänzt, nicht ersetzt**; **keine** neue Task-ID, **keine** neue offene Frage, **kein** neuer
> Sollwert, **keine** neue F-ID. **Die Korrekturrunden 1–5, die Rev.-0.6- und Rev.-0.5-Blöcke, der
> Abschnitt „Korrekturrunde 5" und „Entscheidungs-Abschluss Rev. 0.7" bleiben wortgleich** — diese
> Runde ist rein additiv.
> **Katalog (jede Kennung genau einmal belegt, Muster K41):**
>
> - **K71 — NEU-1 (major): `spec_plan.py` in **allen** abgeleiteten Write-Set-Inventaren.**
>   K62 hat `scripts/lib/consistency/spec_plan.py` **korrekt** in W2-9s `Files:` aufgenommen, aber
>   **keine** der daraus abgeleiteten, im Plan selbst als maßgeblich bezeichneten Stellen mitgezogen:
>   **Ownership-Matrix** (W2-9-Spalte, **4** `owns`-Zeilen statt **5**), Matrix-Narrativ („die
>   **vier** Werkzeug-/Testdateien"), Matrix-Narrativ („die **sechs** neuen Dateien"), Step-Agent-Map
>   (W2-9, 4 Dateien), `File Structure` (nur `plan_identity.py`/`plan_ledger.py`), Rollback **W2**
>   (**4** `git checkout`-Zeilen für W2-9 im **Vor**-Stand — `plan_identity.py`/`plan_ledger.py`/
>   `test_plan_identity.py`/`test_plan_ledger_writer.py`; **5** nach K71 durch die neue Zeile
>   `spec_plan.py`) und die **vier** Summenlisten des Self-Reviews. Die
>   „Betroffene Stellen"-Liste der Runde 5 nannte **weder** die Ownership-Matrix **noch** die
>   Step-Agent-Map ⇒ **keine** dokumentierte Ausnahme (anders als die `191`-Lesart-Regel, die ihre
>   Reststellen ausdrücklich benennt) ⇒ der Plan widersprach sich über die Schreibmenge einer Task,
>   deren Ownership-Klausel er selbst **fail-closed** nennt. **Keine Kollision:** kein anderer Task
>   führt `spec_plan.py`; der Mangel war reine **Deckungslücke** der Inventare.
>   **Neu gemessene Stände:** W2-9 = **5** `owns`-Zeilen, W2-9 + W2-8 = **7** Dateizeilen,
>   Rev.-0.7-Dateizeilen der Matrix = **9** (der Matrix-Kopf nannte **9** und war damit richtig —
>   die Tabelle war die unvollständige Stelle). **Korrigiert an 12 Stellen** (siehe
>   „Betroffene Stellen der Korrekturrunde 6"); der **historische** Entscheidungs-Record
>   `E-8` („Ownership-Matrix (4 Zeilen + 2 Spalten)") bleibt **wortgleich** und wird durch die
>   **Lesart-Regel** aufgelöst: jede Stelle, die W2-9s Write-Set **ohne** `spec_plan.py` nennt, meint
>   den Stand **vor** K62. **Re-Review 3 (R3-2, info — Korrektur von K71, keine neue K-ID):** die
>   Angabe „N `git checkout`-Zeilen für W2-9" ist im K71-Befundsatz durchgängig als **Vor**-Zustand
>   zu lesen (alle übrigen Mengen dort sind es ebenfalls: 4 `owns` statt 5, „vier" statt „fünf",
>   „sechs" statt „sieben"); der **Vor**-Wert ist **4**, der **Ist**-Wert **5** — der im Befund
>   genannte Wert „3" war in **beiden** Lesarten falsch.
> - **K72 — NEU-3 (minor): drei falsche `Datei:Zeile`-Anker nachgemessen.** IC-05 liegt bei
>   **`:944-954`** (nicht `:930-933` = Codeblock in **IC-04**); die Revisionszeile `0.7` liegt bei
>   **`:386`** (nicht `:383` = die `0.5`-Zeile der Revisionstabelle; und nicht `:367` = **Leerzeile**
>   unter der Überschrift „Verifikations-Legende" — die **VERIFIED**-Zeile liegt bei `:370`); der
>   §10-`--validate`-Bullet liegt bei **`:2257-2261`** (nicht `:2235` = §9.2). **Die Aussagen waren je
>   richtig, falsch waren nur die Anker** — relevant, weil die Runden ihre Belegqualität über
>   `Datei:Zeile` begründen und
>   die Spec in §16 verlangt, „jeder `Datei:Zeile`-Verweis wurde gelesen". Korrigiert an **4**
>   Stellen (Plan 3, Spec 1). **Re-Review 3 (R3-1, minor — Korrektur von K72, keine neue K-ID):** der
>   Revisionszeilen-Anker wurde **einmal nachgemessen** und steht auf **`:386`**; `:383` ist die
>   `0.5`-Zeile, und die alte Klammer-Begründung war ungenau — `:367` ist die **Leerzeile** unter
>   „Verifikations-Legende" (`:366`), die **VERIFIED**-Zeile ist `:370`. Die **Aussage** von K72
>   (Anker waren falsch, Aussagen richtig) bleibt unverändert.
> - **K73 — NEU-4 (minor): „alle sieben Fixtures" → „6 der 7 Fixtures", R7 gesondert.** **Gemessen**
>   in `tests/test_doc_index.py`: **R1…R6** (`:280`, `:294`, `:309`, `:320`, `:336`, `:350`) schreiben
>   je `_tree(root, README_RELPATH, "# readme\n")`; **R7**
>   (`test_real_repo_pages_are_reported_only_by_v2_until_w3_6`, `:394`) hat **kein** Fixture, sondern
>   liest den **echten** Baum (`REPO_ROOT`, `:404-408`). Die **Klassifikation „alle sieben heute rot
>   bzw. vakuum" bleibt korrekt** — die Begründung trug nur für 6 statt 7.
> - **K74 — NEU-2 (minor): der Beleg `tests/test_plan_identity.py:96-101` war falsch.**
>   **Gemessen:** dort steht `test_normalize_task_id` mit den Asserts `"3"→"task-3"`,
>   `"TASK-3"→"task-3"`, `"task-3"→"task-3"`, `"custom"→"custom"` (`:100`), `"task-"→"task-"` —
>   **kein** `"W2-0"`. **Der Sachstand ist richtig** (Durchreich-Zweig `return raw`,
>   `plan_identity.py:73`, weil `TASK_ID_RE = ^task-[0-9]+$` (`:18`) nicht passt) und der `W2-0`-Pin
>   wird in **W2-9 Akzeptanz (f) neu angelegt**; es geht **kein** Schutz verloren. Falsch war nur die
>   **Evidenzbehauptung**. **Ersetzt** an **6** Stellen durch den realen Anker:
>   „verhaltensgleich abgedeckt durch `normalize_task_id("custom") == "custom"`
>   (`tests/test_plan_identity.py:100`, derselbe Durchreich-Zweig); der `W2-0`-Pin wird in
>   Akzeptanz (f) neu angelegt".
> - **K75 — INFO-1 (info): die 193-Baseline ist zukunftssicher gefasst.** Der Nachweisaufruf enthält
>   `-not -name 'INDEX.md'`. Heute ist das **folgenlos** (`docs/INDEX.md` existiert **nicht**,
>   Universe **205** ⇒ **193** ✓); **ab W3-6** liefert **derselbe** Aufruf **192** (Universe **204**,
>   davon **12** verlinkt), während die Baseline im Register **193** bleibt. Die Exclusion ist
>   **gewollt** (V2-Konvention, IC-05 V2-Zeile „ohne `docs/INDEX.md` selbst"); nur der
>   **Bezugszeitpunkt** der Zahl fehlte. **Neu gefasst** als `Universe 205 − 12 verlinkt = 193`
>   (Bezugszeitpunkt **vor W3-6**), mit dem ausdrücklichen Vermerk, dass der **Sollwert 0**
>   zeitpunktunabhängig bleibt.
>
> **Betroffene Stellen der Korrekturrunde 6 (übersichtlich) — die Liste der Runde 5 ist damit
> erweitert, nicht ersetzt:** **Plan:** Plan-Kopf (K57-Anker, K59-Anker, K61-Fixture-Satz, K62?,
> K66-Anker, K60-Baseline) · **neue** Korrekturrunde-6-Liste K71…K75 · Plan-Legende
> (`K1…K70` → `K1…K75`) · „Warum W2 ‖ W3 parallel" (W2-9-Dateiliste + Summenangabe) ·
> **`File Structure`** (**neu**: `scripts/lib/consistency/spec_plan.py`) · **Rollback W2**
> (**neu**: `git checkout scripts/lib/consistency/spec_plan.py`, + Mengenangabe) · Task **W2-6**
> (Akzeptanz V4, Begründungsabsatz) · Task **W2-9** (`Interfaces`, gemessener Anker) ·
> **Step-Agent-Map** (W2-9-Spalte) · **Ownership-Matrix** (Kopf-Vermerk, **neue Zeile**,
> Matrix-Narrativ ×2) · **Self-Review-Summenlisten** (4 Stellen: Rev.-0.7-Dateiliste,
> Einfachschreiber-Liste, „Neu sind außerdem"-Zählung, Abweichung 8) · Zuordnungsregister Runde 5
> (RVW-7-01/02/08/09 — Anker- und Baseline-Nachbesserung) · Follow-up-Register ·
> **neuer** Abschnitt „Korrekturrunde 6". **Spec:** §17.11.1 **K57** (Anker) · §17.11.3
> (Register-Baseline) · §17.11.5 **K59**/**K60**/**K61**/**K66** (Anker, Baseline, Fixture-Satz) ·
> **neue** §17.11.6.
> **Unverändert bleiben:** alle Checkboxen, alle Task-/AC-/IC-/R-/OQ-/V-Check-/F-IDs,
> `revision: 0.7`, `status: APPROVED`, die Korrekturrunden **1–5**, die Rev.-0.5-/Rev.-0.6-Blöcke,
> „Entscheidungs-Abschluss Rev. 0.7" (dort stehende Mengenangaben werden durch die K71-Lesart-Regel
> aufgelöst) und alle Code-Dateien.
>
> **Legende der Kennungen (K25 — beseitigt die ID-Kollision `E-1`/`E-2`/M1).** In Rev. 0.6 waren
> zwei verschiedene Nummernkreise entstanden, die beide `E-1`/`E-2` hießen. Sie sind ab hier
> **getrennt geführt**; **keine** Kennung ist doppelt belegt:
>
> | Präfix | Bedeutung | Status |
> |---|---|---|
> | **`U-*`** (U-1, U-2) | **Nutzerentscheidung** — vom Nutzer **getroffen** (2026-09-27) | **geschlossen** |
> | `E-0*` (E-01…E-15) | **Errata** des Ausführungs-Ledgers, Abschnitt **L-3** dieses Plans | gemischt (behoben / offen / blockierend) |
> | `E-1…E-8` (ohne führende 0) | **Entscheidungsvorlagen** — **E-1…E-4** aus Rev. 0.5 (Spec §17.9.4) sind **offen, unentschieden** (z. B. ESCALATION E-2 in Task W8-4); **E-5…E-8** aus Korrekturrunde 4 sind **ENTSCHIEDEN am 2026-09-27** (Nutzer, `main_chat`) — **Rev. 0.7**, Volltext im Schlussabschnitt „Entscheidungs-Abschluss Rev. 0.7" und Spec §17.11 | **E-1…E-4: offen** · **E-5…E-8: entschieden (geschlossen)** |
> | `OQ*` (OQ1…OQ10) | **offene Frage** an den Auftraggeber, mit Owner und Frist | **offen** (OQ1, OQ3, OQ4, OQ9, OQ10) |
> | `K-*` (K1…**K76**) | **Korrektur-Kennungen** dieses Vorhabens (kein Status, nur Auditierbarkeit) — **Herkunft dieser Zeile: Plan-Legende = Stand Rev. 0.7, Korrekturrunde 6** (Runde 3 = K46…K50, **Runde 4 = K51…K53**, **Rev. 0.7 = K54…K58**, **Korrekturrunde 5 = K59…K70**, **Korrekturrunde 6 = K71…K75**, **additiv angehängt am 2026-09-28: K76 — Anhang „Ausführungsstand W2 Phase 0"; ausdrücklich keine Korrekturrunde und keine Plan-Revision, s. K76 und K34; K76 ist ausdrücklich die erste K-ID ohne Review-Befund und die erste Änderung einer Zeile im Rev.-0.7-Kopfblock — beide Ausnahmen sind je einmalig, s. F, K76**); die **Spec-Legende bleibt eingefroren** auf `K1…K45` (Spec-Statuskopf, Stand Korrekturrunde 2) | — |
>
> **Ergänzung Korrekturrunde 4 (additiv, 2026-09-27) zur Legende.** (a) Der E-Namensraum ist von
> **`E-1…E-4` auf `E-1…E-8`** erweitert: **`E-5`** (V4-Generalisierung ohne README-Index-Owner),
> **`E-6`** (zwei rote Volltests ohne Owner), **`E-7`** (600er-Grenze vs. V5-Bedarf in
> `docs_freshness.py`), **`E-8`** (Checkbox-Pflege: der maschinelle Ledger-Writer kann diesen Plan
> nicht adressieren). Alle vier sind **offen und unentschieden**; **keine** wurde unterstellt, keine
> wurde eigenmächtig getroffen — die **E-1…E-4** bleiben unter ihrer Kennung **wortgleich** und
> **unentschieden**. (b) Der K-Bereich ist von **`K1…K50` auf `K1…K53`** gezogen; Runde 4 hat den
> Katalog um **`K51`…`K53`** verlängert. **Nicht** nachgezogen und **nicht** angefasst wurden die
> festgeschriebenen Historic-Blöcke: die **K36**-Zeile der Runde-1-Tabelle, der **K45**-Absatz der
> Runde 2 und der Rev.-0.5-RVW-1-Absatz — sie nennen jeweils ihren damaligen Stand (`10 → 11`) und
> tragen den Zusatz „maßgeblich ist die **Plan-Legende** oben"; die Berichtigung steht in **K51**.
>
> > **Rev. 0.7 (additiv) — dieser Absatz beschreibt den Stand VOR der Entscheidung und bleibt
> > wortgleich.** Satz (a) dieses Absatzes („Alle vier sind **offen und unentschieden**; **keine**
> > wurde unterstellt, keine wurde eigenmächtig getroffen") gilt **für den 2026-09-27 zum Zeitpunkt
> > der Korrekturrunde 4** und ist **keine** Aussage über den heutigen Stand. **Heute gilt:**
> > **`E-5`…`E-8` sind am 2026-09-27 vom Nutzer entschieden** (verbindlich, über `main_chat`;
> > Volltext im Rev.-0.7-Block im Kopf und im Schlussabschnitt „Entscheidungs-Abschluss Rev. 0.7",
> > Begründungen in Spec §17.11). **Maßgeblich** ist die **Plan-Legende oben** (Zeile
> > `E-1…E-8`), nicht dieser datierte Absatz. **Unverändert offen bleiben `E-1`…`E-4`** — sie sind
> > **keine** Nutzerentscheidungen und werden hier **nicht** berührt.
>
> **Umbenennung, ausdrücklich und additiv:** Die beiden Rev.-0.6-Nutzerentscheidungen hießen in der
> Erstfassung `E-1`/`E-2` und wurden als **K25** auf **`U-1`/`U-2`** umbenannt — **an allen Stellen**
> beider Dokumente. **Achtung bei `E-1…E-4`:** die bleiben unter ihrer Kennung **unverändert** und
> sind **keine** Nutzerentscheidungen. Insbesondere ist die **ESCALATION E-2** in Task **W8-4**
> (V9-Altersschwelle als Config-Key oder Modulkonstante) **nicht** die Rev.-0.6-Entscheidung **U-2**.
>
> **Korrekturrunde Rev. 0.6, Runde 1 (Concept-Review 2026-09-27, `CHANGES_REQUESTED`, 0 kritisch ·
> 11 major · 7 minor · 5 info; `validator`: PASS mit 3 nicht-blockierenden Notizen).** Die
> **inhaltlichen Kernaussagen der Rev. 0.6 sind bestätigt und nicht umgestoßen**: Modulzuordnung
> (U-1), W2-DAG, **PG-2a**, verengtes **AC-30** (U-2) und das Follow-up-Register bleiben in der
> Sache **wortgleich**. Korrigiert wurden ausschließlich **Widersprüche und Rückstände**.
> `status: APPROVED` unverändert; **kein** Revisions-Bump; **keine** AC/IC/R/OQ/Task-/V-Check-ID
> umnummeriert oder gestrichen. **Katalog der Korrekturrunde 1 = K25…K40** (Tabelle unten) — dort
> ist jede Kennung genau einmal belegt; **die Korrekturrunde 2 verlängert den Katalog um
> K41…K45** (eigene Liste darunter), damit der **Stand der Korrekturrunde 2 K45** ist — **historischer
> Stand** (Korrekturrunde 3 hat den Katalog auf **K46…K50** verlängert; maßgeblich ist die
> Plan-Legende oben mit `K1…K50`).
>
> | K | Review-Befund | Kurztext |
> |---|---|---|
> | **K25** | M1 | ID-Kollision `E-1`/`E-2` beseitigt → **`U-1`/`U-2`** + Legende |
> | **K26** | M2 + M3 | **DoD Punkt 2** (V3 = 0 im AC-30-Scope) und **Punkt 12** (`--validate` → Deltasperre) |
> | **K27** | M4 | `W-VALIDATE-ROT` an 4 Stellen konsistent auf „kein Termin 0" + globale Vorrangregel |
> | **K28** | M7 | Fassaden-`__all__` um `check_spec_plan_path_convention` (V8) ergänzt |
> | **K29** | M8 | V1-Test-Anker auf `tests/test_doc_freshness.py`; 3 Testdateien in Spec §4 |
> | **K30** | m3 | K23 war unvollständig: Reststellen `README.md:721-723`/`:721-724` → `:722/:723` |
> | **K31** | M11 | §4.1-Abgrenzung: `doc_facts.py` + `consistency/docs.py` (nicht `doc_renderer.py`) |
> | **K32** | M10 | OQ10 als Zeile in „Entscheidungs-Tasks" + Querverweis in Task W8-4 |
> | **K33** | **M6** | `W2-GATE-V1`: `tests/test_doc_freshness.py` in **beide** Erfolgskriterien (sonst vakuum-grün) |
> | **K34** | **m6** / `validator` N-2 | Checkbox-Split **46 / 153** statt 40 / 159 |
> | **K35** | **m5** | Self-Review-Dateiliste um `tests/test_doc_facts.py` (W2-7) ergänzt |
> | **K36** | **M5** | W3-Block, RVW-1-Begründungstabelle: V7 **10 → 11**; V3 „**2** → W8-2 · **25** → Follow-up" |
> | **K37** | **M9** | Fußnote **⁵** (V3-Dreiklassen) angelegt — sie war referenziert, aber undefiniert |
> | **K38** | Runde-1-Minor (unnummeriert) | Follow-up-**Anlage** als benannter Schritt `F-ISSUE-ANLAGE` (2026-09-30) neben Abarbeitung (2026-10-11) |
> | **K39** | m1 + m2 | Taskzahl **47 → 48**; OQ-Liste **OQ1…OQ10** |
> | **K40** | m4 + m7 | RVW-1-Historie „10 Wiki-Seiten" markiert · `W2-1→…→W2-7` als **überholt** · Spec-`related` + Plan (`validator` N-3) |
>
> **Bereinigung des K-Namensraums (Runde 2, N1 — K41).** In Runde 1 war **`K26` sechsfach** belegt
> (DoD M2, DoD M3, `W2-GATE-V1` M6, Self-Review-Liste m5, Checkbox-Split m6, `W-VALIDATE-ROT`-
> Regelkopf) und **`K27`** doppelt (M4 **und** die m7-W2-Ketten-Markierung). **K41** vergibt die
> freien Kennungen **K33…K40** und zieht **alle** Verweise darauf um: Plan 1708, 1709, 1711
> (→ **K33**), 4157 und 4217 (→ **K34**), 4013 (→ **K35**), 2470 (→ **K36**; zugleich Reduktion von
> „K24/K31" auf „K24"), 2576 (→ **K37**), 3648 (→ **K40**). **`K26` bleibt** der DoD-Korrektur
> (M2 + M3) vorbehalten, **`K27`** der `W-VALIDATE-ROT`-Korrektur (M4). **M5 und M9** hatten in
> Runde 1 **gar keine** K-Kennung — sie haben jetzt **K36** bzw. **K37**. **Damit ist jede
> K-Kennung genau einmal belegt**; die Belegstelle ist die Tabelle oben.
>
> **Korrekturrunde Rev. 0.6, Runde 2 (Concept-Review 2026-09-27, `CHANGES_REQUESTED`, 1 major ·
> 4 minor) — K41…K45.** Der Reviewer bestätigt ausdrücklich: Modulzuordnung **12/12 disjunkt**, DAG
> **zyklusfrei**, PG-2a-Write-Sets **disjunkt**, **AC-30-Wortlaut unverändert**, **48** Tasks /
> **199** Checkboxen, **W2-0-Vertrag vollständig und widerspruchsfrei**. Die Restpunkte sind
> ausschließlich **Zitier-/Audit-Hygiene**; **keine** dieser Korrekturen berührt eine Invariante.
> `status: APPROVED` unverändert; **kein** Revisions-Bump. Katalog:
>
> - **K41 — N1 (Major): K-Namensraum bereinigt.** `K26` war sechsfach, `K27` doppelt belegt; **M5**
>   und **M9** hatten **keine** K-Kennung. Freie Kennungen **K33…K40** vergeben und **alle**
>   Verweise umgezogen; `K24/K31` in Plan:2470 auf **`K24`** reduziert. Die Spec-Aussage
>   „**keine** Kennung ist doppelt belegt" ist damit **wahr** und wird mit dem bereinigten ID-Satz
>   belegt, **nicht** abgeschwächt.
> - **K42 — N2: K-Bereiche nachgezogen.** Legende und Revisionsverweis von „K1…K31" / „K25…K31" auf
>   den Endstand der **Runde 2** gezogen, der damals **K1…K40** / **K25…K40** war (Spec-Legende,
>   Spec-Revisionszeile, Plan-Legende). **Nachgetragen (reine Bereichsangabe, ohne Bedeutungs-
>   änderung von K42):** Runde 2 hat den Katalog mit **K41…K45** verlängert, der **Stand nach
>   Korrekturrunde 2 war daher `K1…K45` / `K25…K45`**; alle drei Verweise wurden darauf nachgezogen.
>   **Historischer Stand, nicht der heutige** (Korrekturrunde 3 verlängert auf **K46…K50**): maßgeblich
>   ist die **Plan-Legende** (`K1…K50`, siehe oben); die **Spec-Legende** (Spec:72) bleibt
>   **eingefroren** auf `K1…K45` und wird von dieser Runde **nicht** nachgezogen.
> - **K43 — N3: Reststelle `README.md:721-724`** in der M-8-Tabelle auf **`:722-723`** korrigiert —
>   damit ist K30s Aussage „an allen benannten Stellen" **wahr**. **Fundort-Nachtrag (reine
>   Zeilenangabe):** K43 wurde zunächst mit „Plan:914" zitiert; nach den Zeilenverschiebungen der
>   Korrekturrunden trägt der korrigierte Text bei **Plan:934** (`File Structure` → „Geändert
>   (Doku/Agent)"). **Hinweis zur Nachhaltigkeit:** Zeilenangaben **innerhalb** dieses Plans sind
>   driftanfällig — maßgeblich ist der **Abschnittsanker** (`File Structure` → „Geändert
>   (Doku/Agent)"), die Zeilennummer nur eine Lesehilfe (K12-Logik).
> - **K44 — N4: Widerspruch im selben `--validate`-Bullet aufgelöst** (W8-4-Block) und **K27s
>   Absolutheitsaussage ehrlich gefasst** (Begründung der gewählten Lösung dort).
> - **K45 — N5: Wiki-Seiten-Zahl als Historie markiert** („10" = Ist-Stand 2026-09-26; maßgeblich
>   **11**).
>
> **Nicht angetastet:** die **historische** Rev.-0.5-Zählzeile (Plan Rev.-0.4-Block) — sie beschreibt
> den Stand des 2026-09-26 und bleibt als solcher stehen.
> - **Unverändert bleiben (Kontrollliste):** Modulzuordnung **12/12 disjunkt**, W2-DAG **zyklusfrei**,
>   PG-2a-Write-Sets disjunkt, **AC-30-Wortlaut**, **48** Tasks, **199** Checkboxen.
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
>   Gemessen am Working Tree (**Stand 2026-09-26 — HISTORIE, K45**): `knowledge/wiki` enthält
>   **10** Seiten mit `type: "Architecture"` — **maßgeblich ist der Wert 11** (Baseline-Messung
>   2026-09-27, **K24**); die 10 wird hier als historischer Messwert **nicht** fortgeschrieben
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
  dokumentieren (`scripts/lib/consistency/docs_links.py:30-65` mit `Severity.ERROR` **`:58`**;
  Rev. 0.6 / K48 — vor dem W2-0-Split `docs.py:9-44`).
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
- **Rev. 0.7 / E-8 — Ledger-Pflege:** Die Checkboxen dieses Plans werden **bis einschließlich dem
  Task W2-9** nach der **K53-Interim-Regel** gepflegt (von Hand durch den Orchestrator, jeweils mit
  Datum, Commit-Hash und Task-ID im Abschnitt **L-1**; **kein** Lauf von
  `scripts/lib/plan_ledger.py` gegen diesen Plan, weil `TASK_HEADER_RE`
  (`scripts/lib/plan_identity.py:27-30`) `### Task <id>` verlangt und dieser Plan `### W2-0:`
  schreibt). **Ab W2-9** ist der maschinelle Ledger-Writer **einsetzbar** und die Interim-Regel
  **endet** — ausdrücklich, nicht stillschweigend. Vor W2-9 ist ein Werkzeuglauf gegen diesen Plan
  **kein** gültiger Nachweis.
- **Rev. 0.7 / E-6 — Volltests sind kein Doku-Gate.** `python3 -m pytest tests/ -q` enthält zwei
  Tests, die den **repo-globalen** `sync.py --validate`-Exit-Code prüfen
  (`tests/test_knowledge_engine.py:228`, `tests/test_sharkord_service_name_migration.py:48`).
  Dieser Exit-Code ist nach `W-VALIDATE-ROT` **planmäßig rot** (V2/V3/V6 ab W2-7). **Konsequenz:**
  ein Volltest-Lauf ist erst ab **W2-8** ein gültiger Wellen-Nachweis für W2; **vorher** ist er
  **kein** Nachweis und **kein** Blocker — die rote Zahl wird **nicht** durch Absenken eines
  Sollwerts, sondern durch **Entkopplung** der beiden Tests von der Fremdgröße behandelt.
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
- Create: `scripts/lib/consistency/docs_links.py` — **Rev. 0.6 / U-1 (K18), Task W2-0**. Familie
  „Referenz auflösbar": **V3** `check_internal_links`, **V4** `check_readme_docs_index` (von
  `docs.py:102-124` übernommen) + Altchecks `check_sync_cli_docs` (`:11-46`) und
  `check_ui_help_mappings` (`:49-98`) — **die drei `:`-Anker sind Zeilen im Quellmodul `docs.py`
  vor dem Split** (Rev. 0.6 / K50, zur Vermeidung eines Missverständnisses als `docs.py:` zu lesen);
  **Ist nach W2-0 gemessen: `docs_links.py` = 334 Zeilen** (Prognose ~330), `docs.py`
  selbst = **80** Zeilen. Prognose **~330** Zeilen, **< 600** verbindlich.
  **Rev. 0.7 / E-5 (K54) — was W2-6 an V4 ändert und was nicht:** geändert wird **nur** der
  **Scope** — V4 liest ab W2-6 die `##`-Region `Documentation Index` in `README.md` und prüft deren
  **deklarierte** `docs/`-Kategorien (Existenz + mindestens **ein** Link je Kategorie) statt
  „alle 205 nicht-Archiv-`docs/**.md` sind verlinkt". **Unverändert:** Check-ID
  `docs.readme_index`, Signatur, Severity **ERROR**, `file` = `README.md`, Modul `docs_links.py`
  und der IC-05-Pin.   **Größenfolge:** `docs_links.py` **334** Z (nach W2-0, committet) → **404** Z (Working Tree nach
  W2-6, gemessen) — weiter **< 600** ✓ (Reserve **196** Z).
- Create: `scripts/lib/consistency/docs_freshness.py` — **Rev. 0.6 / U-1 (K18), Task W2-0**.
  Familie „Doku vs. berechneter Ist-Zustand": **V1a/V1b**   `check_no_manual_counts` (vor dem Split
  `docs.py:155-412`, inkl. Suppressionsregeln 1–4 und der K16-Eingrenzung) + **V6**
  `check_docs_facts_fresh` (W2-5). Prognose
  **~480** Zeilen. **Rev. 0.6 / K50 (Ist nach W2-0 gemessen): `docs_freshness.py` = 317 Zeilen**
  (V1-Block `:60-317`, `_v1_finding` `:255-273`) — damit **283 Zeilen Reserve** bis zur Grenze 600
  für die Aufnahme von **V5** (W2-4) und **V6** (W2-5).
  **Rev. 0.7 / E-7 (K56) — die Reserve ist aufgebraucht, V5 zieht aus.** **Ist nach W2-5 gemessen:
  592 Zeilen** (Reserve **8**). **Größenfolge, verbindlich:** `docs_freshness.py` **592** (V1a/V1b +
  V6; **kein** weiterer V-Check) · `docs_freshness_v5.py` **≈ 55–70** (V5) — **beide < 600** ✓.
  **Ohne E-7** läge W2-4 bei **647–662** Z und W2-4s eigenes Abnahmekriterium (`wc -l` < 600)
  schlüge fehl.
- Create: `scripts/lib/consistency/docs_freshness_v5.py` — **Rev. 0.7 / E-7 (K56), Task W2-4**.
  Familie „dokumentierter Rollenbestand vs. erzeugte Rollen": **V5**
  `check_role_generation_parity` — **einziger** Check dieses Moduls (Muster wie `docs_wiki.py` für
  V7/V8 und `docs_index.py` für V2/V9). Prognose **≈ 55–70** Zeilen, **< 600** verbindlich.
  **Grenze gegen die 600er-Regel, ausdrücklich:** W2-4s Abnahmekriterium `wc -l` < 600 wird **nicht**
  aufgeweicht und **nicht** auf eine Gesamtsumme umgedeutet — die Regel gilt **pro Modul**, und E-7
  erfüllt sie, indem V5 ein **eigenes** Modul bekommt. **Ausdrücklich verworfen** (E-7-Optionen
  (a) Wiederverwendung von `_v6_finding`/`_v6_computed_facts` — versteckte Kopplung über
  `V6_CHECK_ID`/`V6_SEVERITY_BY_KIND`; (b) Komprimieren der V1-Prosa — Lesbarkeitsverlust gegen eine
  harte Grenze): **beide** sind in Spec §17.11 / dem Rev.-0.7-Block begründet verworfen.
- Create: `scripts/lib/consistency/docs_wiki.py` — **Rev. 0.6 / U-1 (K18), Task W2-3** (W2-0 legt
  es **nicht** an, weil dort noch kein Bestand liegt; **K50: die Datei existiert nach W2-0 noch
  nicht**). Familie „abgeleitete Bestands-Oberfläche":
  **V7** `check_wiki_staleness` (W2-3) + **V8** `check_spec_plan_path_convention` (W6-2). Prognose
  **~200** Zeilen.
- Create: `scripts/lib/consistency/docs_index.py` — **Rev. 0.6 / U-1 (K18), Task W2-6** (W2-0 legt
  es **nicht** an; **K50: die Datei existiert nach W2-0 noch nicht**). Familie „Doku-Bau geführt": **V2**
  `check_docs_index_completeness` (W2-6) +
  **V9** `check_stale_backups` (W8-4). Prognose **~180** Zeilen.
- **Rev. 0.6 / K50 — Modulzahl `scripts/lib/consistency/`:** **20 → 22** nach W2-0 (Ist: 22 Dateien
  inkl. `__init__.py`, gemessen per Glob; `docs_links.py` und `docs_freshness.py` sind die beiden
  neuen). Alle vier `docs_*.py`-Familienmodule stehen damit unter der 600er-Grenze.
  **Rev. 0.7 / E-7 (K56) — Modulzahl 22 → 23** nach W2-6 (`docs_index.py`) und **23 → 24** nach W2-4
  (`docs_freshness_v5.py`). **Alle fünf** `docs_*.py`-Familienmodule stehen **< 600**:
  `docs.py` **80** (Fassade) ·   `docs_links.py` **334** (W2-0) → **404** (W2-6) · `docs_freshness.py`
  **592** (W2-5) · `docs_freshness_v5.py` **≈ 55–70** (W2-4) · `docs_wiki.py` **129** (W2-3) ·
  `docs_index.py` **211** (W2-6, im Working Tree gemessen). **Die 600er-Grenze ist pro Modul;** die
  Summe über alle Module ist **kein** Kriterium.

### Neu anzulegen (Tests)

- Create: `tests/test_doc_facts.py` — AC-01…AC-06, AC-11, AC-12, AC-25, V9-Test (W8-4).
- Create: `tests/test_doc_facts_expected.py` — AC-36.
- Create: `tests/test_doc_renderer.py` — AC-14…AC-18, AC-20…AC-24, AC-26, AC-27.
- Create: `tests/test_generated_file_drift_docs.py` — AC-19, AC-37.
- Create: `tests/test_docs_consolidation_migration.py` — AC-28, AC-29, AC-30, AC-32, AC-39, AC-40.
- Create: `tests/test_knowledge_index_gen.py` — AC-33, AC-34, AC-35, AC-41.
- Create: `tests/fixtures/docs_v1_fixtures.md` — V1a+V1b Positiv-Fixture (AC-07/AC-08), **erst
  nach Track-A-Merge** (Spec §2.3).
- Create: `tests/test_doc_wiki.py` — **Rev. 0.6 / K20 (Entscheidung „Tests je Modul aufgeteilt")**,
  Task **W2-3**: V7-Tests (AC-10, `test_v7_missing_and_stale_derived_from`). Grund: nur so ist die
  Schreibmenge der Parallelgruppe **PG-2a** von der des W2-5/W2-6 disjunkt.
- Create: `tests/test_doc_freshness.py` — **Rev. 0.6 / K20**, angelegt in **W2-0** (V1-Tests werden
  aus `test_doc_facts.py` **verschoben**, nicht dupliziert), erweitert in **W2-5** (V6).
  **Rev. 0.7 / E-7 (K56): W2-4 schreibt diese Datei nicht mehr** — die V5-Tests wandern nach
  `tests/test_doc_freshness_v5.py`; die Datei trägt damit **einen** schreibenden Task in PG-2a
  (**W2-5**) plus **W2-7** (V1-Pin, K46). Die Kante `W2-5 → W2-4` wird dadurch **gegenstandslos** und
  bleibt als historische Kante im Planungsbild sichtbar.
- Create: `tests/test_doc_freshness_v5.py` — **Rev. 0.7 / E-7 (K56), Task W2-4**: V5-Tests
  (AC-11), `test_v5_severity_depends_on_se_gate`. Grund: der V5-Testbestand muss **nicht** in
  `tests/test_doc_freshness.py` liegen, weil W2-4 und W2-5 nach E-7 **keine** gemeinsame
  Schreibmenge mehr haben — dadurch ist W2-4 in Phase B **frei** und die historische Kante
  `W2-5 → W2-4` wird **wirkungslos**, ohne dass eine Ownership-Regel gebrochen werden müsste.
- Create: `tests/test_doc_index.py` — **Rev. 0.6 / K20**, Task **W2-6**: V2-Tests (AC-12) und die
  **Rev. 0.7 / E-5**-Tests für den README-Index-Scope von V4 (`test_v4_declared_category_needs_a_link`,
  `test_v4_declared_category_must_exist`, `test_v4_without_index_section_is_a_finding`).
- Create: `docs/plans/2026-09-25-docs-consolidation-oq1.md`, `-oq2.md`, `-oq4.md`, `-oq6.md`,
  `-oq8.md`, `-oq9.md`, `-wave0-freeze.md`, `-track-a-gate.md` — W0-x / W5-1 / W8-1.

### Geändert (Code)

- Modify: `scripts/lib/consistency/docs.py` — IC-05, Checks V1…V9 (bestehende 3 unverändert).
  **Rev. 0.7 / E-7:** `docs.py` ist **Rev. 0.7-Kontext unberührt** — W2-4 fasst es **nicht** an
  (K46-Negativregel); das `__all__`-Inkrement für `check_role_generation_parity` bleibt **W2-7s**
  Eigentum, nur der Import-Pfad weicht von `docs_freshness` auf `docs_freshness_v5` (Spec §4.1).
- Modify: `scripts/lib/plan_identity.py` — **Rev. 0.7 / E-8 (K57/K58), Task W2-9**:
  `TASK_HEADER_RE` (`:27-30`) um einen alternativen Zweig für die **Wellen-/Task-Header-Form**
  (`### W2-0: …`) erweitern; `TASK_ID_RE` (`:18`) und `normalize_task_id` (`:63-73`) lernen die
  ID-Form `W<n>-<k>`. **Betroffen ist die Definition, nicht der Konsument.**
- Modify: `scripts/lib/plan_ledger.py` — **Rev. 0.7 / E-8 (K58), Task W2-9, bedingt**: **Konsument**
  von `TASK_HEADER_RE` (Import `:25`, `finditer` `:71`, Tupel-Entpackung `:133`, `unmatched`
  `:172`/`:182`). **Wird nur geschrieben, falls** sich der Zwei-Gruppen-Vertrag des Treffers ändert;
  im Normalfall **read-only** (Global Constraints: „Lesen ist kein Ownership").
- Modify: `scripts/lib/consistency/spec_plan.py` — **Rev. 0.7, Task W2-9, ergänzt in Korrekturrunde 6
  (K71 / RVW-7-04-Nachbesserung)**: der **dritte** Konsument von `TASK_HEADER_RE` (Regex-Bindung
  `:55`, `_parse_plan_tasks` `:547-583`, `finditer` `:557`) extrahiert seine **Dep-Tokens** über das
  **hart kodierte** Muster `task-\d+|\d+` (`:570`, **Vor-Implementierungs-Anker** — nach dem Commit von W2-9 `_DEP_TOKEN_RE` `:68`, Verwendung `:581`); es wird auf `W\d+-\d+` erweitert, weil sonst
  `**W2-0**` die Phantom-ID `task-0` erzeugt, `find_dependency_errors` (`orchestration.py:207-216`)
  **dangling dependency** meldet und `validate_plan` (`:287-289`) **vor**
  `check_plan_file_overlap` (`:533`) abkehrt — die fail-closed-Ownership-Klausel fiele dann **ganz
  aus**. **Gemessen:** keine andere Task des Plans führt `spec_plan.py` in ihrer `Files:`-Liste
  (W2-0 las sie **nur** für den Modul-Split) ⇒ Write-Set bleibt disjunkt.
- Modify: `scripts/lib/consistency/placeholders.py` — IC-06, `^DOCS_` in `_DYNAMIC_PREFIXES`.
- Modify: `scripts/consistency-check.py` — Registrierung der neun Checks + Common-Gate (AC-13).
- Modify: `scripts/lib/consistency/report.py` — **Rev. 0.5, K15 (B-5/E-15):** `line` und `branch`
  werden **Dataclass-Felder** von `Finding` (mit Defaults, damit bestehende Konstruktoraufrufe
  unverändert bleiben) und in `print_json_report` serialisiert; heute werden sie von
  **`docs_freshness.py:255-273`** (Rev. 0.6 / K48; vor dem W2-0-Split `docs.py:329-347`) als
  Instanzattribute gesetzt und im `--json`-Output **verworfen**
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
- Modify: `README.md` — W3-7 Marker-Regionen, W8-2 Totverweise (`:722-723`; **K43** — ehemals `:721-724`,
  `:721`/`:724` existieren), W8-3 Providerzahl.
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
| M-8 | Modify | W8 | `README.md:722-723` Totverweise (**K30**: ehemals `:721-724`; `:721`/`:724` existieren) |
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
PG-2 (W2 in 2 Phasen + W3-Kette parallel, max 3 Agents)
 |- W2 Phase 0 (sequenziell):  W2-1 -> W2-2 -> W2-0 (Modul-Split, Rev. 0.6) -> W2-9 (Rev. 0.7, E-8)
 |    W2-0 spaltet docs.py in die Fassade + docs_links.py + docs_freshness.py
 |    und legt tests/test_doc_freshness.py an (V1-Tests wandern, nicht kopiert).
 |    VERHALTENSNEUTRAL: 163 passed bleibt gruen, --json unveraendert, keine Registrierung.
 |    W2-9 macht TASK_HEADER_RE wellen-header-faehig -> LEDGER-WRITER EINSETZBAR AB HIER
 |    (Ende der K53-Interim-Regel; Plan-Aussage ausdruecklich: "jetzt noch nicht").
 |         v
 |- W2 PG-2a (3 Tasks PARALLEL, write-set-disjunkt, Rev. 0.6 / K20):
 |    |- W2-3 (V7)  -> docs_wiki.py      + tests/test_doc_wiki.py
 |    |- W2-5 (V6)  -> docs_freshness.py + tests/test_doc_freshness.py + tests/test_doc_facts_expected.py
 |    `- W2-6 (V2+V4) -> docs_index.py   + tests/test_doc_index.py + docs_links.py (V4-Scope, Rev. 0.7 / E-5)
 |         v  (W2-3 | W2-5 | W2-6, kein Zwischen-False-Start)
 |- W2 Phase B (sequenziell):  W2-4 (V5, Rev. 0.7: eigenes Modul docs_freshness_v5.py)
 |                          -> W2-8 (Rev. 0.7, E-6: Volltests entkoppeln) -> W2-7 (Registrierung, Common-Gate, report.py)
 |    Begruendung der Serialitaet: W2-7 schreibt docs.py, consistency-check.py und report.py
 |    und ist der Abschluss; W2-8 muss vor der Registrierung laufen, weil es die beiden
 |    Volltests von der dann planmaessig roten --validate-Ausgabe entkoppelt (W-VALIDATE-ROT).
 |    W2-4 ist seit E-7 frei von der Schreibmenge von W2-5 (hist. Kante W2-5 -> W2-4 ohne Wirkung).
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
| W2 | **10** (Rev. 0.6: + **W2-0**; **Rev. 0.7: + W2-9 und W2-8**) | AC-07…AC-11, AC-13, AC-36 | W1-A, W0-4 | **PG-2: W2 ‖ W3**; innerhalb W2: **PG-2a = W2-3 ‖ W2-5 ‖ W2-6** (max 3), davor (Phase 0) und danach (Phase B) sequenziell | `checks.strict: false` bzw. `enabled: false`; **`git rm` der fünf neuen `docs_*.py`** |
| W3 | 7 | AC-12, AC-14…AC-22, AC-26, AC-27, AC-37, AC-38 | W1-B, W0-1, W0-6, **W2-1 (nur Schritt 4, K16 — Rev. 0.5/RVW-4)** | PG-2 | `git rm docs/INDEX.md`; Marker entfernen; `enabled: false` |
| W4 | 3 | AC-28 (Teil), AC-29 | W3 | PG-3 seriell | `git mv` zurück + Stub `git checkout` |
| W5 | 3 | AC-28 (Teil), AC-31 | W1, W0-7 | PG-3 seriell | `git mv` zurück; Annotationen additiv revertierbar |
| W6 | 2 | AC-28 (Teil), AC-32 | W3 | PG-3 seriell | Config-Key additiv → Zeile entfernen |
| W7 | 5 | AC-33…AC-35, AC-41 | W5, W3, Rollenpflege-Branch gemergt | **isoliert** | `index-mode: llm` → Generator stumm; `restore_wiki_index()` |
| W8 | 4 | AC-30, AC-40 | W2, W3, **nach** W7 | PG-5 | additiv revertierbar |

### Warum W2 ‖ W3 parallel ist, W4/W5/W6 aber nicht

- **W2 ‖ W3:** Write-Sets disjunkt. W2 besitzt `scripts/lib/consistency/docs_links.py`,
  `docs_freshness.py`, `docs_wiki.py`, `docs_index.py`, `docs.py` (Fassade),
  `tests/test_doc_wiki.py`, `tests/test_doc_freshness.py`, `tests/test_doc_index.py`,
  `tests/test_doc_facts.py`, `tests/test_doc_facts_expected.py`,
  `tests/fixtures/docs_v1_fixtures.md`, `scripts/lib/consistency/report.py`,
  `scripts/consistency-check.py`. W3 besitzt `scripts/lib/doc_renderer.py`, `scripts/lib/doc_index.py`,
  `scripts/lib/sync_pipeline.py`, `scripts/lib/spec_plan_scaffold.py`,
  `scripts/lib/generated_file_drift.py`, `tests/test_doc_renderer.py`,
  `tests/test_generated_file_drift_docs.py`, `docs/INDEX.md`, `README.md`, `llms.txt`,
  `ARCHITECTURE.md`, `.meta-config/project.yaml`. Überschneidung: keine (`.gitignore` bleibt
  unberührt, OQ6 entschieden). Spec §9.2
  bestätigt diese Parallelität. **Rev. 0.6 (K20):** der W2-Teil dieser Aufzählung ist um die vier
  neuen Module und die drei neuen Testdateien gewachsen; **W2-0** nimmt zusätzlich
  `tests/test_doc_freshness.py` (Anlage, mit Verschiebung der V1-Tests) in seine Schreibmenge auf.
  **Wichtig für `scripts/lib/consistency/`:**   W2-0 fügt **4** Dateien hinzu — die beiden
  bestehenden W2-Altchecks liegen weiterhin in **denselben** Dateien wie vorher; es wird **keine**
  bestehende Datei des Runner-Importpfads umbenannt oder verschoben (§2.3-Tracking-Gate bleibt
  gewahrt).   **Rev. 0.7 (E-6/E-7/E-8):** W2 fügt **vier** Dateien hinzu — W2-6 `docs_index.py`,
  W2-4 `docs_freshness_v5.py` sowie je eine Testdatei dazu. **W2-9** (`plan_identity.py`,
  `plan_ledger.py`, `scripts/lib/consistency/spec_plan.py` (**K71**), `tests/test_plan_identity.py`,
  `tests/test_plan_ledger_writer.py`) und **W2-8**
  (`tests/test_knowledge_engine.py`, `tests/test_sharkord_service_name_migration.py`) schreiben
  Dateien, die **keine** andere Task **des gesamten Plans** schreibt — die W2-‖-W3-Parallelität
  bleibt damit **unberührt** (W3s Write-Set enthält keine dieser **sieben** Dateien).
- **Parallelität innerhalb von W2 (Rev. 0.6, K20 — der eigentliche Korrekturgegenstand):** die
  Wellengrenze W2 ‖ W3 war **schon** disjunkt, die **innere** W2-Kette war es **nicht** — in
  Rev. 0.5 schrieben W2-3…W2-7 **alle** `docs.py` **und** `tests/test_doc_facts.py`, also war jede
  angekündigte Parallelität in W2 eine Scheinparallelität. **Neu:** W2-0 stellt den Split fertig,
  danach sind **drei** Tasks mit **disjunkten** Write-Sets parallel (**PG-2a**: W2-3 ‖ W2-5 ‖ W2-6).
  **Warum W2-4 und W2-7 **nicht** in PG-2a liegen (Rev. 0.6-Stand; W2-4s Grund ändert sich in
  Rev. 0.7, siehe Absatz darunter):** W2-4 schrieb dasselbe Modul und dieselbe
  Testdatei wie W2-5 (beide gehören zur Familie „Doku vs. berechneter Ist-Zustand",
  `docs_freshness.py`); W2-7 schreibt die Fassade `docs.py`, den Runner `consistency-check.py` und
  `report.py` — es ist der **Abschluss** und hängt an allen drei PG-2a-Tasks. Beide Fälle sind
  **Kanten**, keine Zufälle; die Aufzählung steht im Abschnitt „Ownership-Matrix, DAG und
  Zyklenprüfung").
  **Rev. 0.7 (E-7) — W2-4s Grund für „nicht in PG-2a" hat sich geändert.** Er schrieb in Rev. 0.6
  `docs_freshness.py` + `tests/test_doc_freshness.py`, also W2-5s Schreibmenge. Nach E-7 schreibt
  er `docs_freshness_v5.py` + `tests/test_doc_freshness_v5.py` — **disjunkt** zu PG-2a. Er bleibt
  dennoch **sequenziell**, jetzt aus dem im Task genannten Grund: der Nachweis „`docs_freshness.py`
  bleibt bei 592 Zeilen" ist erst **nach** W2-5 beobachtbar. **Das ist eine Verschärfung der
  Trennschärfe, keine Lockerung**, und die Kante `W2-5 → W2-4` bleibt als **historische**
  Planungsentscheidung im Kantenbild stehen (mit dem Vermerk „gegenstandslos", Zyklenprüfung (e)).
  **W2-7 bleibt der Abschluss** und hängt nach Rev. 0.7 zusätzlich an **W2-8**.
- **Tests je Modul in eigene Dateien (Rev. 0.6, K20 — ausdrückliche Entscheidung).** **JA, die Tests
  werden aufgeteilt** auf `tests/test_doc_wiki.py`, `tests/test_doc_freshness.py`,
  `tests/test_doc_index.py`. **Begründung in einem Satz:** Parallelität ist nur echt, wenn auch die
  **Test**-Write-Sets disjunkt sind — ein gemeinsames `tests/test_doc_facts.py` würde jede
  Parallelgruppe sofort wieder zur Kette machen und den Aufwand des Modul-Splits zunichtemachen.
  **Rev. 0.7 (E-7):** die Aufteilung gilt unverändert, umfasst jetzt aber **vier** Testdateien je
  Modul — `tests/test_doc_wiki.py` (`docs_wiki.py`), `tests/test_doc_freshness.py`
  (`docs_freshness.py`), **`tests/test_doc_freshness_v5.py`** (`docs_freshness_v5.py`, **neu**),
  `tests/test_doc_index.py` (`docs_index.py`). Das Muster ist damit **vollständig durchgezogen**:
  **jedes** `docs_*.py`-Familienmodul hat **genau eine** eigene Testdatei.
  **Kosten, ausdrücklich benannt:** die V1-Tests werden aus `test_doc_facts.py` **verschoben**
  (nicht kopiert), damit die **163** Tests der Vorher-Baseline als **Summe** erhalten bleiben
  (Nachweis in W2-0 Schritt 5) — der Umfang wächst **nicht** durch Duplikate.
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
  Barrieren-Spaltung über 4 hinaus ist damit **nicht** erforderlich. **Rev. 0.6 (K20):** die
  Grenze wird jetzt **innerhalb** von W2 ausgeschöpft — **PG-2a** hat genau **3** Members
  (W2-3, W2-5, W2-6) und liegt damit **an**, aber **nicht über** der Grenze. **Warum nicht 4:**
  W2-4 kann nicht hinzukommen (gemeinsame Schreibmenge mit W2-5) —   die Grenze ist also **nicht**
  die bindende Größe, die **Ownership-Disjunktheit** ist es.
  **Rev. 0.7:** unverändert **3** gleichzeitige Agents in W2. **W2-9** liegt **vor** PG-2a und
  **W2-4/W2-8** **nach** ihr, damit die Gruppe **nicht** auf **4** Member wächst — wäre W2-9 Mitglied
  von PG-2a, wäre die Grenze von 4 relevant und dieOwnership-Regel (nicht die Agentenzahl) wäre
  erneut die bindende Größe.
- **`.meta-config/project.yaml` wird von W1-10, W3-4, W6-2, W7-2/5 und W8-4 geschrieben** — alle
  liegen in **verschiedenen, sequenziell geordneten** Wellen, daher keine Parallelitätskollision.

### Step-Agent-Map (plan-driven `implement`, Stufe 3)

| Task | Agent | Task | Agent | Task | Agent |
|---|---|---|---|---|---|
| W0-1, W0-4, W0-6, W0-7 | orchestrator | W1-1…W1-5, W1-7, W1-8 | senior-developer | W3-1…W3-4 | senior-developer |
| W0-2 | git | W1-6, W1-9, W1-10 | developer | W3-5…W3-7 | developer |
| W0-3 | agent-meta-manager | W0-1, W0-4, W0-6, W0-7, **W2-0** | developer | W4-1, W4-2, W5-2, W6-1 | developer |
| **Rev. 0.7:** **W2-9** (E-8, Ledger-Writer) | senior-developer | **Rev. 0.7:** **W2-8** (E-6, Volltests entkoppeln) | senior-developer | | | |
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

## W2 — Checks V1–V7 (V1 startet WARNING) · **Rev. 0.7: 10 Tasks, Einfahrt über W2-0 (Modul-Split) und W2-9 (Ledger-Writer), Abschluss über W2-8 (Volltests) + W2-7 (Registrierung)**

**Verifikation W2 (erwartete Exit-Codes):**
- **Rev. 0.6 (K20) — pytest-Zeile an die aufgeteilten Testdateien angepasst:**
  `python3 -m pytest tests/test_doc_facts.py tests/test_doc_facts_expected.py
  tests/test_doc_freshness.py tests/test_doc_wiki.py tests/test_doc_index.py -q` → **0**.
  **Vorher-Baseline (unverändert gültig):** `python3 -m pytest tests/test_doc_facts.py
  tests/test_doc_facts_expected.py -q` → **163 passed** (Baseline-Messung 2026-09-27, Übergabe vom
  Parent). **Bedeutung der Rev.-0.6-Zeile:** sie ist die **Summe** derselben Tests nach der
  Verschiebung; die V1-Tests **wandern** nach `tests/test_doc_freshness.py`, sie werden **nicht**
  dupliziert — die Gesamtzahl muss nach W2-0 **≥ 163** sein und **kein** Test darf verloren gehen
  (Nachweis in **W2-0 Schritt 5**). **Die drei neuen Testdateien existieren erst ab W2-0/W2-3/W2-6**;
  vor dem ersten W2-Lauf ist deshalb die **alte** Zeile maßgeblich.
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
  liest und bei Abwesenheit `False` liefert (**Rev. 0.6 / K48:** `docs_freshness.py:240-252`; vor
  dem W2-0-Split stand die Aussage auf `docs.py:359`/`:314-326`)
  und `.meta-config/project.yaml:398-399` **nur** `enabled: true` setzt; **(b)** V1 ist im
  Runner **nicht registriert** — `scripts/consistency-check.py:52-56` importiert V1 **nicht**
  (**Rev. 0.6 / K47:** `tests/test_doc_freshness.py:364-383` pinnt das; vor dem Split
  `tests/test_doc_facts.py:2403-2422`), der Runner emittiert also **kein**
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
  `checks.strict` tatsächlich `WARNING` (`docs_freshness.py:240-252` = `v1_strict`, Severity-Wahl
  **`:285`**; Rev. 0.6 / K48 — vor dem W2-0-Split `docs.py:359`),
  `.meta-config/project.yaml:398-399`).
  Sie trug **nicht** für **V2, V3, V6**: diese sind nach **W2-7** registriert und **ERROR**
  (IC-05), und `python3 scripts/sync.py --validate` liefert genau dann **Exit 1**, wenn der
**gesamte** Runner mindestens ein ERROR-Finding liefert (`scripts/lib/cli_commands.py:975` →
`:171-174` → `:1056`/`:1058-1059`). **Maßgeblich ist `W-VALIDATE-ROT`** (Wellenblock
  W2 — Verifikation): planmäßig rot von **W2-7** bis einschließlich **W8-2** — **und danach weiter
  (K27: `--validate` hat keinen Termin 0; maßgeblich ist die Deltasperre)**, Owner `validator`;
  Grundlage **Spec §6(b) und der §10-Aufzählungspunkt `--validate`**, die ein Nicht-Grün-Sein
  bei V1/V2/V3/V6 **ausdrücklich sanktionieren**. **Der Sollwert wird nicht abgesenkt, sondern als
  Dokuzeile ohne Sollwert geführt und durch die Deltasperre ersetzt.** Die Zeile bleibt als
  Historie sichtbar.
- `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0** (6/6)
- **Rev. 0.7 / E-6 (K56) — Volltest-Zeile, neu und ausdrücklich mit Termin:** `python3 -m pytest
  tests/test_knowledge_engine.py tests/test_sharkord_service_name_migration.py -q` → **0**.
  **Vor W2-8 ist diese Zeile planmäßig rot** und **kein** Blocker: beide Tests prüfen
  `returncode == 0` gegen den **repo-globalen** `sync.py --validate`-Exit, der nach
  `W-VALIDATE-ROT` **planmäßig rot** ist. **Maßgeblich ist der Zählwert**, nicht der Exit-Code eines
  Vollständigkeitslaufs; ein Volltest-Lauf ist erst **ab W2-8** ein gültiger Wellen-Nachweis. **Die
  Zeile wird nicht abgesenkt**, sondern durch **Entkopplung** (W2-8) erfüllbar gemacht.

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
| **nach W2-1** — V1 implementiert, **nicht** registriert | `v1-findings: 0`, leere `v1-severities`, leere `v1-files`. **Kein** Severity-Wert ist beobachtbar, weil der Runner V1 nicht aufruft; die Severity-Aussage wird in dieser Phase **ausschließlich** am Unit-Nachweis geprüft. | **vor W2-0:** `python3 -m pytest tests/test_doc_facts.py -q -k v1` → **0** (deckt `test_v1_positive_fixture_yields_exactly_four_findings` mit `Severity.WARNING` und `test_v1_is_not_wired_into_the_runner_yet`) **und** das Zähl-Kommando druckt `v1-findings: 0` · **ab W2-0 (K33):** `python3 -m pytest tests/test_doc_freshness.py tests/test_doc_facts.py -q -k v1` → **0** — die V1-Tests liegen dann in `tests/test_doc_freshness.py`; **ohne** die zweite Datei selektiert `-k v1` **nichts** und die Prüfung wäre vakuum-grün |
| **nach W2-7** — V1 registriert, `checks.strict` weiterhin **nicht** gesetzt | `v1-findings:` **≥ 1** und `v1-severities:` **exakt** `['WARNING']`. Der Sprung 0 → ≥ 1 ist der Registrierungsnachweis. `v1-files` ⊆ {`README.md`, `llms.txt`, `ARCHITECTURE.md`} (**Rev. 0.6 / K48:** `docs_freshness.py:63`
= `V1_SCAN_RELPATHS`; vor dem W2-0-Split `docs.py:158`) — **Dokuzeile, kein Prüfkriterium (RVW-15):** die Menge entsteht konstruktionsbedingt aus `V1_SCAN_RELPATHS`, kann also **nicht** fehlschlagen. | Zähl-Kommando druckt `v1-findings: ≥ 1` **und** `v1-severities: ['WARNING']`; zusätzlich `python3 -m pytest tests/test_doc_freshness.py tests/test_doc_facts.py tests/test_doc_facts_expected.py -q` → **0** (**K33**: `tests/test_doc_freshness.py` ergänzt, W2-0 verschiebt die V1-Tests dorthin) und `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0** |

**K33 (Rev. 0.6, Review-Befund M6) — `W2-GATE-V1` war nicht auf die neuen Testdateien gezogen.**
Beide Erfolgskriterien nannten **nur** `tests/test_doc_facts.py`. Ab **W2-0** liegen die V1-Tests
aber in **`tests/test_doc_freshness.py`**: ein Aufruf `-k v1` **ohne** diese Datei selektiert
**null** Tests und meldet Exit **0** — das Kriterium wäre **vakuum-grün** und hätte die
Verhaltensneutralität von W2-0 **nicht** geprüft. **Beide Zeilen sind korrigiert**; die
**Vor-W2-0-Fassung bleibt** als gültige Zeile für den Zeitraum zwischen W2-1 und W2-0 sichtbar.

**Zeitliche Bindung beider Zustände (RVW2-5, ergänzt):** die Zeile „nach **W2-1**" gilt **nur bis
W2-7** — sie stützt sich auf `test_v1_is_not_wired_into_the_runner_yet`
(**`tests/test_doc_freshness.py:364-383`**, Rev. 0.6 / K47; vor dem W2-0-Verschieb
`tests/test_doc_facts.py:2403-2422`), den **W2-7 Schritt 1** durch den positiven
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
| `docs.internal_links` (V3) | **planmäßig rot** (ERROR) | **Rev. 0.6, K22 — in drei Klassen aufgeteilt** (Volltext: Tabelle `W2-GATE-V3-KLASSEN`): **2** Layout-Findings `README.md:722`/`:723` ⇒ Termin **W8-2**; **25** Link-Findings unter `docs/**` ⇒ **Follow-up `F-DOCS-LINKS-2026-09-27`**, Termin **2026-10-11**, **kein** Termin 0 in W0–W8; `llms.txt` **0** | `developer` (W8-2 **und** Follow-up) |
| `docs.readme_index` (V4) | **Rev. 0.7 / E-5 (K54) — der Sollwert ändert sich von 0 auf 1, mit Termin.** **Warum:** V4 prüft nach E-5 **nicht** mehr „alle 205 nicht-Archiv-`docs/**.md` sind in `README.md` verlinkt" (⇒ **193** ERROR — **K60**, nicht 191 —, `--validate` blockiert, zwei Volltests rot), sondern den **README-Index-Scope**: jede in der `##`-Region `Documentation Index` deklarierte `docs/`-Kategorie muss existieren und **mindestens einen** Link tragen. **Gemessener Ist-Stand: genau 1** Finding — Kategorie `docs/se-cascade/` (deklariert `README.md:378`, ohne Link in der Region). **Termin: Follow-up `F-DOCS-README-INDEX-SE-2026-09-27`, 2026-10-11.** **Die 193** sind **kein** V4-Finding mehr, sondern Follow-up `F-DOCS-README-INDEX-2026-09-27` (2026-10-11; Nachweis = **Issue-Liste + once-count außerhalb V4**, **kein** V4-Zählwert — **K60**). **Check-ID `docs.readme_index`, Severity ERROR, `file` = `README.md` unverändert** (IC-05-Pin; Signatur **einargumentig** `(root: Path)` — **K59**). **Wichtig:** V4 ist **bereits heute** im Runner registriert (`consistency-check.py:53`/`:201`) — die Registrierungszeile ändert sich **nicht** | `developer` (W2-6 für den Scope, Follow-ups für die Behebung) |
| `docs.role_generation_parity` (V5) | **0** | `compute_active_roles()` schließt das deaktivierte Gate (`project.yaml:12-13`); **Rev. 0.7 / E-7:** Modul `docs_freshness_v5.py` (Task W2-4), Registrierung weiterhin **W2-7** | `developer` (W2-4) |
| `docs.docs_facts_fresh` (V6) | **planmäßig rot** (ERROR) | generierte Blöcke existieren erst ab **W3-7** | `developer` (W3-7) |
| `docs.wiki_staleness` (V7) | **planmäßig rot** (WARNING) | **10** Wiki-Seiten `type: "Architecture"` ohne `derived-from` — **Rev. 0.6 / K51: von 11 auf 10 korrigiert** (K24 war eine **Fehlmessung**: ein `type:`-Zeilen-Scan über ganze Dateien zählte einen **Body**-Kommentar in `knowledge/wiki/concepts/core-principle-knowledge-engine.md:46` mit; über **Frontmatter** gemessen sind es **10**. Die Messung 2026-09-26 (10) war richtig, die Übergabemessung 2026-09-27 (11) nicht) — Termin **W5-3** | `tester` (W5-3) |

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

**W2-GATE-V3-KLASSEN (neu, Rev. 0.6, K22) — die drei Klassen, in denen V3 rot ist.** V3 ist nach
W2-7 ein **ERROR**-Check und **eine** Zählwert-Zeile ist für ihn nicht ausreichend: die Klassen
haben **verschiedene** Termine und **verschiedene** Owner-Zuständigkeiten. Baseline-Messung
**2026-09-27** (Übergabe vom Parent; `check_internal_links()` direkt aufgerufen, **27** Findings
gesamt):

| Klasse | `branch` | Anzahl | Wo | Zustand | Termin 0 | Owner |
|---|---|---|---|---|---|---|
| **README-Layout** | `layout` | **2** | `README.md:722` (`howto/setup/`), `README.md:723` (`howto/features/`) — beide in `README.md`, beide im **AC-30-Scope** (Rev. 0.6) | **rot**, im Scope des AC-30 | **W8-2** | **`developer`** (Task W8-2) |
| **docs-Link-Fundstellen** | `link` | **25** | ausschließlich `docs/**` — `docs/guides` 10 (features 5, setup 5) · `docs/concepts` 13 (davon **8** in `docs/concepts/archive/`, **5** in `docs/concepts/*.md`) · `docs/superpowers/plans/` 2; **live** ohne `archive/` = **17** | **rot**, **außerhalb** des AC-30-Scope (U-2) | **Follow-up `F-DOCS-LINKS-2026-09-27`, Termin 2026-10-11** — **kein** Termin 0 in W0…W8 | **`developer`** |
| **`llms.txt`** | — | **0** | `llms.txt` | **grün** | — | — |

**Was daraus folgt, ausdrücklich (Ehrlichkeitsgrenze, K22):** weil V3 **ERROR** bleibt und die
**25** `docs/**`-Findings **weiter** meldet, ist **`docs.internal_links` innerhalb W0–W8 nie `0`**
und damit sind **`consistency-check.py → 0`** und **`sync.py --validate → 0`** **dauerhaft
unerreichbar** (die frühere Dokuzeile „spätester Termin 0: **W8-2**" gilt nur noch für die **2**
README-Layout-Findings). **Maßgeblich** ist ab Rev. 0.6 die **Deltasperre** der Regel
`W-VALIDATE-ROT` (`errors` darf nicht steigen; Owner `validator`, Baseline in **W3-7**). Die
Severity-Frage selbst ist **nicht** Gegenstand von U-1/U-2 und als **OQ10** in der Spec §11.1
geführt (Owner `orchestrator`, Frist **vor W8-4**).

**Ist-Zustand 2026-09-27 (Baseline-Messung, Übergabe vom Parent; Rev. 0.6 nachgezogen):**
`python3 scripts/consistency-check.py --json` → `{'total': 85, 'errors': 0, 'warnings': 85}`; die
enthaltenen Checks sind `crossrefs.changelog-missing-entry` und `placeholders.unknown` — **kein**
`docs.`-Check liefert Findings. Also **`docs-checks: 0`** und **`docs-findings: 0`**. Begründung: V1
ist **nicht registriert** (`scripts/consistency-check.py:52-56` importiert nur
`check_readme_docs_index`, `check_sync_cli_docs`, `check_ui_help_mappings`; Aufrufe in `run_checks()`
`:199-201`); der einzige heute registrierte Check mit `docs.`-Präfix ist `check_readme_docs_index`
mit `check="docs.readme_index"` (`scripts/lib/consistency/docs.py:118`), und er liefert **0**
Findings. **Zusätzlich, aus dem Rev.-0.6-Ledger:** `scripts/lib/consistency/docs.py` = **599**
Zeilen, `report.py` = **115**, `consistency-check.py` = **280**, `tests/test_doc_facts.py` = **2867**,
`tests/test_doc_facts_expected.py` = **526**; in `scripts/lib/consistency/` liegen **20** Module vor
W2-0, **24** danach; `docs/INDEX.md` existiert **nicht**. **Konsequenz:** die Aussage „V1…V7
implementiert" (IC-05) ist **nicht** gleichbedeutend mit „im Runner registriert"; die Registrierung
ist ein **eigener** Nachweis (Task **W2-7**) und wird **nicht** über `docs-checks` geführt.

**Historischer Ist-Zustand 2026-09-26 (gemessen am Working Tree, Datei:Zeile):** `docs-checks: 0` **und**
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
**Rev. 0.7 / E-5 — die Lücke ist für V4 geschlossen, für V5 bleibt sie:** V4 hat nach E-5 den
Erwartungswert **1** (≠ 0) und fällt damit **unter die Präsenzregel** — eine fehlende Zeile
`<check> <count> <severities>` für `docs.readme_index` ist jetzt ein **Befund**. **V5** behält den
Erwartungswert **0**; für ihn bleibt die Task-Ebene der einzige Registrierungsnachweis.

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

**Regel (K27, Rev. 0.6 — korrigiert):** `python3 scripts/sync.py --validate` ist **planmäßig rot**
von **W2-7** (dem ersten Lauf mit registrierten Doku-Checks) **bis einschließlich W8-2** — und
**danach weiter**. **K27:** V3 bleibt **ERROR** und meldet unter `docs/**` dauerhaft **25**
Findings, die AC-30 (U-2) **nicht** behebt ⇒ **`--validate → 0` hat keinen Termin 0**; maßgeblich
ist die **Deltasperre** (Owner `validator`, Baseline **W3-7**), offene Severity-Frage **OQ10**.
Verursachende Doku-Checks mit Termin und Owner:

| Zeitraum | Planmäßig rote Doku-ERROR-Checks | Erster Termin 0 | Owner |
|---|---|---|---|
| **W2-6 … W2-7** | **Rev. 0.7 / E-5 — V4 kommt in dieser Zeile hinzu.** V4 ist **schon heute** registriert und liefert nach E-5 **1** ERROR (Kategorie `docs/se-cascade/`), **nicht** 193; der Wert **193** wäre der Zustand der **verworfenen** Verallgemeinerung (**K60**). Fern **V2** (bis zum Sync in **W3-6**, Schritt 2), **V3**, **V6** | V4 → **Follow-up 2026-10-11** (kein Termin 0 in W0–W8) · V6 → **W3-7**; V2 → **W3-6**; V3 → **W8-2** (nur die **2** README-Layout-Findings) | `developer` (V4, V6) · `senior-developer` (V2) · `developer` (V3) |
| **W2-7 … W3-6** (Zeilenstand Rev. 0.6, bleibt gültig) | **V2** (bis zum Sync in **W3-6**, Schritt 2), **V3**, **V6** — **Rev. 0.7 / E-5: zusätzlich V4 mit 1 ERROR, Termin Follow-up 2026-10-11** (siehe Zeile darüber; die Aufzählung „nur V2, V3, V6" dieser historischen Zeile ist damit um **V4** erweitert) | V6 → **W3-7**; V2 → **W3-6**; V3 → **W8-2** (nur die **2** README-Layout-Findings) | `developer` (V6) · `senior-developer` (V2) · `developer` (V3) |
| **W3-7 … W8-1** | **V3** (durchgehend; die **2** Layout-Findings bis W8-2, die **25** `docs/**`-Findings **dauerhaft**) · **V2** ist nach W3-6 0, in **W4** und **W5** erneut rot und jeweils erst mit dem Abschluss-Sync-Lauf wieder 0 (W4-3 Schritt 4 / W5-2 Schritt 4 — Fußnote ¹ der `W-GATE-TABLE`); V6 ab W3-7 0 · **Rev. 0.7 / Korrekturrunde 5 (K67, RVW-7-09): zusätzlich V4 mit 1 ERROR** (Kategorie `docs/se-cascade/`, Follow-up `F-DOCS-README-INDEX-SE-2026-09-27`, Termin 2026-10-11) — V4 ist **bereits registriert** (`consistency-check.py:53`/`:201`) und stand in dieser Zeile zuvor **nicht**; die Zeile war damit **unvollständig**, nicht falsch | **W8-2** (die 2 Layout-Findings gehen auf 0; **V2** bleibt bis **W8-4 Schritt 5** rot — nächste Zeile). **Für `--validate` insgesamt: kein Termin 0** | `developer` (V3, V4) · `senior-developer` (V2) |
| **W8-2 … W8-4** | **Rev. 0.6 (K22): V3 bleibt unter `docs/**` dauerhaft rot (25 ERROR-Findings, Follow-up `F-DOCS-LINKS-2026-09-27`, Termin 2026-10-11) — `--validate` ist deshalb auch nach W8-4 nicht 0.** **V2** — W8-1 legt `docs/plans/…-oq4.md` an und bearbeitet `docs/REQUIREMENTS.md`; **W8-2** und **W8-3** führen **keinen** Sync, V2 bleibt dort rot. V9 ist **WARNING** und bricht `--validate` **nicht** (die Zählung `:174` filtert auf `Severity.ERROR`). **Rev. 0.7 / Korrekturrunde 5 (K67, RVW-7-09): zusätzlich V4 mit 1 ERROR** (gleiche Zeile, gleicher Termin wie oben) | **kein Termin 0 für `--validate`** — maßgeblich ist die **Deltasperre** (Owner `validator`, Baseline W3-7); Severity-Frage **OQ10** (Frist vor W8-4) |

**Lesehinweis zu Zeile 2 und 3 (RVW3-1, vierte Korrekturrunde; ergänzt um K27).** Die Fassung vor
dieser Korrekturrunde nannte als „ersten Termin 0 für `--validate`" den Wert **W8-4 Schritt 5**
und schrieb, Zeile 2 ende bei W8-2, weil dort alles grün sei. **Beides ist seit Rev. 0.6
überholt und bleibt nur als Historie lesbar:** (a) V3 ist nach W8-2 **nur im AC-30-Scope** grün —
unter `docs/**` meldet es **25** ERROR-Findings weiter (U-2/K22, Fußnote ⁵); (b) **V2** ist nicht
der Grund, warum `--validate` nach W8-4 rot bliebe, sondern V3. **Maßgeblich:** `--validate` hat
**keinen** Termin 0 (K27); es gilt die **Deltasperre**. **Kein** Sollwert wurde geändert — der
Sollwert `→ 0` ist als **Dokuzeile ohne Sollwert** geführt, die **Deltasperre** ist die bereits
bestehende, in Rev. 0.5 eingeführte Ersatzform.

**Grundlage (spec-zitiert, nicht eigene Setzung):** Spec §6(b) und der §10-Aufzählungspunkt
`--validate` **sanktionieren**
ausdrücklich, dass `--validate` bei **V1, V2, V3, V6** nicht grün ist
(„darf bei **V1, V2, V3, V6** nicht grün sein (ab W3; in W2 V1 noch WARNING)"; `--validate` ist
`TEST_COMMAND`, `.meta-config/project.yaml:193`). **K27:** der Sollwert `→ 0` wird deshalb
**nicht** abgesenkt, sondern als **Dokuzeile ohne Sollwert** geführt und durch die **Deltasperre**
ersetzt — dieselbe Lesart, die bereits für den repo-globalen Altbestand und für V9 gilt. **V2** wird
mit dem Abschluss-Sync-Lauf in **W8-4 Schritt 5** wieder 0 (das bleibt ein **Check**-Sollwert, kein
`--validate`-Sollwert). **Owner** der Messung und der Deltasperre: `validator`; **Termin** der
Baseline-Messung: **W3-7**. **Offen:** ob V3 für `docs/**` herabgestuft wird — **OQ10**, Owner
`orchestrator`, Frist **vor W8-4**.

**K27 — Globale Vorrangregel für alle Wellenblöcke (Rev. 0.6, Review-Befund M4).** Die Wellenblöcke
**W3, W4, W5, W6, W7 und W8** wiederholen die Formel „planmäßig rot bis einschließlich **W8-2**,
spätester Termin 0 **W8-4**" (u. a. W3-Block, W4-Block, W5-Block, W6-Block, W7-Block, W8-Block).
**Diese Wiederholungen sind nicht einzeln umgeschrieben**, weil sie alle **derselben** Regel
entstammen und eine gemeinsame Lesart haben. **Vorrang:** **Für `--validate` als Ganzes gilt
„kein Termin 0"** — jede Stelle, die „spätester Termin 0 W8-4" nennt, ist als Aussage über die
**behebbaren** Teilmenge zu lesen: **V2** (W8-4 Schritt 5) und die **2** V3-Layout-Findings
(W8-2). **Die 25 `docs/**`-Link-Findings sind darin nicht enthalten** und haben **keinen**
Termin 0. **Maßgeblich bleibt in jedem Wellenblock die Zeile der `W-GATE-TABLE`** (Spalte der
jeweiligen Welle) — nicht die wiederholte Formel.
**Grenze dieser Vorrangregel (K44, Review-Befund N4 — ehrlich gefasst):** Sie gilt **an jeder Stelle
mit Verweis auf diese Regel oder auf `W-GATE-TABLE`**. **Acht weitere Wellenblock-Formeln**
(Plan:2413, 2696, 2800, 2930, 3045, 3177, 3254, 4054) tragen **weder** einen lokalen K27-Verweis
**noch** eine Umformulierung — sie sind damit **nicht je Stelle** aufgelöst, sondern **global**
überwacht. **Warum die kleinere Lösung gewählt wurde (in einem Satz):** acht zusätzliche Verweise
wären eine Änderung an **acht** Wellenblöcken und würden deren Rev.-0.5-Formulierung jeweils sichtbar
überschreiben, ohne Informationsgewinn — der Aussagewert dieser Wiederholungen ist **null**, weil
Vorrangregel und `W-GATE-TABLE` ohnehin bestimmen, was gilt.
**Ehrliche Restaussage:** an diesen acht Stellen **kann** die alte Formulierung isoliert gelesen
werden; **maßgeblich** ist sie **nicht**. **Der Widerspruch im selben W8-4-Bullet** ist davon
unabhängig und **separat aufgelöst** (K44).

**Ausdrücklich nicht von dieser Regel erfasst:**- `python3 scripts/sync.py --check` — der Drift-Lauf, **nicht** der Consistency-Runner
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
wird erst in **W3-4** gesetzt. Erst dann liefert `v1_strict` (`docs_freshness.py:240-252`) `True` und
die Severity-Wahl (`docs_freshness.py:285`) emittiert `Severity.ERROR` (Rev. 0.6 / K48 — vor dem
W2-0-Split `docs.py:359`). Das W2-Gate läuft **vor** W3-4 und erwartet deshalb zu Recht `WARNING`; ein
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
**Rev. 0.6 (K18/K20) — Rollback um die vier neuen Module ergänzt.** W2-0 ist **rein additiv**
angelegt: es verschiebt Code **innerhalb** des Pakets `scripts/lib/consistency/` und legt vier
Dateien an. Der vollständige W2-Rollback ist deshalb **zweistufig** und in dieser Reihenfolge
auszuführen:

```bash
# Stufe 1 — W2-0 zurücksetzen (Fassade + Extraktion):
git rm scripts/lib/consistency/docs_links.py
git rm scripts/lib/consistency/docs_freshness.py
git rm scripts/lib/consistency/docs_wiki.py
git rm scripts/lib/consistency/docs_index.py
git checkout scripts/lib/consistency/docs.py          # Fassade -> Monolith zurück
git checkout tests/test_doc_facts.py                  # V1-Tests zurück in die alte Datei
git rm tests/test_doc_wiki.py                         # nur falls W2-3 bereits gelandet ist
git rm tests/test_doc_freshness.py                    # dito
git rm tests/test_doc_index.py                        # dito
# Stufe 2 — Konfigurations-Rollback (unveraendert):
#   docs-consolidation.checks.strict: false; vollstaendig: enabled: false (Fail-off => V1–V7 No-op)
git rm -f tests/fixtures/docs_v1_fixtures.md
git checkout scripts/consistency-check.py
git checkout scripts/lib/consistency/report.py        # Rev. 0.5, K15
# Stufe 3 — Rev. 0.7: die zusaetzlichen Dateien der neuen Tasks W2-4, W2-8 und W2-9.
#   W2-4 schreibt docs_freshness.py nach E-7 NICHT mehr; W2-8 schreibt nur die zwei Testdateien.
git rm scripts/lib/consistency/docs_freshness_v5.py   # nur falls W2-4 gelandet ist
git rm tests/test_doc_freshness_v5.py                 # dito
git checkout tests/test_knowledge_engine.py            # W2-8: Volltest-Entkopplung zuruecknehmen
git checkout tests/test_sharkord_service_name_migration.py
git checkout scripts/lib/plan_identity.py              # W2-9: TASK_HEADER_RE / normalize_task_id
git checkout scripts/lib/plan_ledger.py                 # W2-9 (nur falls dort geschrieben wurde)
git checkout scripts/lib/consistency/spec_plan.py        # W2-9 (K71): Dep-Token-Muster :570 (Vor-Implementierungs-Anker; nach W2-9: _DEP_TOKEN_RE :68, Verwendung :581)
git checkout tests/test_plan_identity.py
git checkout tests/test_plan_ledger_writer.py
```

**Reihenfolge-Begründung:** `git checkout docs.py` **vor** dem `git rm` der Nachfolger aufrufen —
sonst existiert die Fassade einen Moment ohne ihre Importe. **Was Stufe 1 ausdrücklich nicht
angreift:** `scripts/lib/doc_facts.py`, `doc_renderer.py`, `doc_index.py` (W1/W3) und die
gesamte W3-Kette; die Write-Sets von W2 und W3 sind nachweislich disjunkt (Absatz „Warum W2 ‖ W3
parallel ist"). **Konsistenz der Regel:** W2-0 verändert **keinen** Pfad des §2.3-Tracking-Gates
(kein `.gitignore`-Eintrag, keine getrackte `docs/**/*.md`), daher ist **kein** Wellen-Invalidierungs-
oder Tracking-Eintrag nötig. **Rev. 0.7 (K56): Stufe 3 ergänzt** die Dateien der Tasks **W2-4**
(zwei neue), **W2-8** (zwei Testdateien) und **W2-9** (**fünf** Werkzeug-/Testdateien — **K71**:
`plan_identity.py`, `plan_ledger.py`, **`scripts/lib/consistency/spec_plan.py`**,
`tests/test_plan_identity.py`, `tests/test_plan_ledger_writer.py`). **W2-9s
Rollback hat eine Eigenschaft, die die anderen nicht haben:** er stellt den **Werkzeugzustand**
vor Rev. 0.7 wieder her — danach ist der maschinelle Ledger-Writer für diesen Plan **wieder
unbrauchbar** und die K53-Interim-Regel muss **wieder** aktiviert werden. Das ist kein Fehler,
sondern dieUmkehrung einer dokumentierten Entscheidung; es wird im Task-Notiz-Format vermerkt und
**nicht** stillschweigend übergangen.

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
- [x] 4: **K16 / B-4 — Suppressionsregel 3 so eingrenzen, dass die vier README-Fundstellen
      `:688/:690/:696/:734` für V1 sichtbar werden**, ohne AC-08 (Fence-Fall bleibt ohne
      Finding) und ohne die Regeln 1, 2 und 4 zu verletzen; Negativ-Test gegen die unmarkierte
      Ist-Fassung schreiben; Mechanismus-Wahl in der LEDGER-Stand-Notiz begründet festhalten.
- [x] 5: commit via `git`-Agent: `feat: add V1 manual count detection with fixtures`. Die
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
>
> **Nachtrag 2026-09-26 — Schritt 4 (K16 / B-4 / E-14) ist umgesetzt und mit Schritt 5
> (Commit) abgeschlossen.** Der Absatz oben bleibt unverändert Historie; additiv folgt der Stand
> nach der Korrektur.
> **Gewählter Mechanismus: Suppressionsregel 3 unterdrückt nur noch Fences *mit*
> Info-String** (Sprachangabe) — ein Fence **ohne** Info-String ist zwar ebenfalls ein fenced
> code block, declares aber **keine** Sprache; V1 durchsucht seinen Inhalt als
> Literal-Transkript, und genau dort steht in den Einstiegsdokumenten das handgepflegte
> Inventar. Umsetzung: `_v1_suppressed_lines` (`scripts/lib/consistency/docs.py`)
> merkt sich je Fence `fence_suppresses = bool(line[opening.end():].strip())`; die
> Fence-Zustandsmaschine läuft **unverändert** weiter, ein untypisierter Block wird also weiterhin
> verfolgt (sonst würde sein schließendes ```` ``` ```` als öffnender Fence gelesen und Regel 3
> verlöre eine ganze Region statt einer Zeile).
> **Begründung der Wahl (warum gerade dieser Kandidat):** (a) die Verengung hängt **allein** am
> Markdown-Info-String — keine Sprach-Allowlist, kein Pfad-/Abschnitts-/Zeilen-Shape-Heuristik,
> damit kann sie die vier Fundstellen nicht aussondern, sondern nur den Blindfleck schließen;
> (b) AC-08 bleibt per Konstruktion grün, denn der Fence-Fall der Negativ-Fixture trägt die
> Info-Angabe ```` ```text ````; (c) sie verändert Regeln 1, 2 und 4 **nicht** — die gemeinsame
> Suppression entscheidet weiterhin zuerst an Region/Marker/Datei; (d) sie ist additiv in einer
> Funktion und ohne Zeilenverlust revertierbar. **Empirische Stütze:** von den 23 Fences in
> `README.md` sind 21 typisiert (Code/Config-Beispiele) und genau **2** untypisiert — der
> Directory-Structure-Block (`:680`…`:737`) und das Conventional-Commit-Literal (`:982`…`:985`);
> beide gehören zu dem, was V1 sehen muss.
> **Verifikationsbeleg:** `python3 -m pytest tests/test_doc_facts.py -q` → **106 passed** (vor der
> Änderung 104, +2 neue Tests); `… -k v1` → **14 passed**; AC-07 unveraendert grün (genau 4
> Findings, `WARNING`, `docs.no_manual_counts`, `line` 1/2/3 = `V1a`, `line` 4 = `V1b`), AC-08
> unveraendert grün (Fence-Fall ohne Finding), Gegenprobe `| Agents | 74 |` → genau 1 Finding;
> `wc -l < tests/fixtures/docs_v1_fixtures.md` → **4**; `python3 -m ruff check
> scripts/lib/consistency/docs.py tests/test_doc_facts.py` → **0**; `python3 -m py_compile
> scripts/lib/consistency/docs.py` → **0**. **Sichtbarkeitsnachweis (negativ, gegen die unmarkierte
> Ist-Fassung, nicht über den Runner — V1 ist noch nicht registriert):** `check_no_manual_counts`
> direkt auf dem Repo-Baum liefert **52** Findings gesamt, davon in `README.md:680`…`:737` genau
> die IC-05-**Fundstellen** `README.md:688` (`V1a`, `'6'`/`'presets'`), `:690` (`V1a`,
> `'6'`/`'provider'`), `:696` (`V1a`, `'1'`/`'hook'`) und `:734` (`V1b`, `'v1.0.0'`) — jede
> Fundstelle mit mindestens einem Befund. **Negativer Nachweis belegt:** mit temporär auf
> Vor-K16-Verhalten zurückgesetzter `fence_suppresses`-Belegung fallen **beide** neuen Tests um
> (`test_v1_sees_the_readme_directory_structure_facts`: „`README.md:688` is invisible to V1";
> `test_v1_fence_suppression_covers_typed_fences_only`: `[] == ['V1a']`), nach Rückbau wieder
> grün. **Beobachtung, ausdrücklich nicht in diesem Schritt behoben (Scope W2-1 Schritt 4 ist
> Regel 3, nicht die V1a-Präzision):** der nun sichtbare Block meldet zusätzlich `README.md:682`
> (`'0'`/`'skill'`) und `:683` (`'1'`/`'templates'`) — das sind **Pfad-Komponenten** aus
> `0-external/` bzw. `1-generic/`, keine Handzahlen, und `:696` meldet die Ziffer `1` aus
> `hooks/1-generic/` statt der eigentlichen Zahl `5` aus `# 5 hook scripts`. Das sind
> Präzisionsbefunde des V1a-Branches (Fehlalarm-Katalog §12.1 R4) und müssen **vor** der
> Hochstufung auf `ERROR` (W3-4) bewertet werden; die Sichtbarkeit der IC-05-Fundstellen war
> davon unberührt.

### W2-2: V3 `check_internal_links`

**Files:** Modify `scripts/lib/consistency/docs.py`, `tests/test_doc_facts.py`
**Interfaces:** Produces: `check_internal_links(root, config=None) -> list[Finding]`; prüft nur
relative repo-interne Pfade. Consumes: W2-1.
**Agent:** developer · **Depends on:** W2-1 · **parallel_group:** PG-2 / W2
**Ziel-AK (AC):** **AC-09** (IC-05) · **V-Check:** **V3**
**Akzeptanz:** `test_v3_flags_dead_howto_links` grün: `README.md:722-723` (**K30**, ehemals
`:721-723` — `:721` `howto/` und `:724` `howto/configs/` existieren und tragen **kein** Finding;
beide Findings tragen `branch="layout"`) auf `howto/setup/`, `howto/features/` liefert ≥ 1
`Finding(severity=ERROR, check="docs.internal_links", file="README.md")`. `http(s)://`, `mailto:` und
`#anchor` werden **nicht** geprüft (R6). Die Behebung erfolgt in W8-2.
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**;
~~`python3 scripts/consistency-check.py --strict` → **1, planmäßig** (V1-WARNINGS **plus**
V3-ERROR auf `README.md:722-723`, das erst W8-2 behebt — im Review als erwartet markieren).~~
**Ergänzung Rev. 0.5 (K13/RVW-2):** vor **W2-7** gibt es im Runner **keine** V1-Findings
(nicht registriert), der V1-Anteil dieses Exit-Code-1 ist also **erst nach W2-7** zu erwarten.
Die Zeile bleibt als Historie sichtbar; maßgeblich sind **W2-GATE-V1** und **W2-GATE-ERRORS**
(beide im Wellenblock **W2 — Verifikation**). **Diese Task-Zeile ist für sich genommen kein
Welle-Gate** (RVW-3) — sie prüft die Implementierung, nicht den Wellenabschluss.
**Steps:**
- [x] 1: Test schreiben (fail).
- [x] 2: V3 implementieren; Scope `docs/**` + `README.md` + `llms.txt`.
- [x] 3: Test grün beobachten; Fehlalarm-Probe auf `http(s)://` und Anker.
- [x] 4: commit via `git`-Agent: `feat: add V3 internal link check`.

### W2-0: Modul-Split — `docs.py` wird zur Fassade (Rev. 0.6, U-1; **verhaltensneutral**)

**Files:** Create `scripts/lib/consistency/docs_links.py`, `scripts/lib/consistency/docs_freshness.py`,
`tests/test_doc_freshness.py`; Modify `scripts/lib/consistency/docs.py` (**nur** Re-Exports),
`tests/test_doc_facts.py` (**nur** Verschiebung der V1-Tests, **keine** Löschung von Abdeckung).
**Explizit nicht in `Files:`** — `scripts/lib/consistency/docs_wiki.py` und `docs_index.py` werden
**nicht** von dieser Task angelegt (hier liegt noch kein Bestand); sie gehören **W2-3** bzw.
**W2-6**.
**Interfaces:** Produces: `docs.py` als **Fassade** mit exakt dem in **Spec §4.1** festgelegten
`__all__`; `docs_links.py` = **V3** + **V4** + `check_sync_cli_docs` + `check_ui_help_mappings`;
`docs_freshness.py` = **V1a/V1b** (inkl. Suppressionsregeln 1–4 in der K16-Eingrenzung) + Platz für
**V6** (W2-5) und **V5** (W2-4); `tests/test_doc_freshness.py` mit den **verschobenen** V1-Tests.
Consumes: **W2-1** (V1), **W2-2** (V3), W0-4 (Track-A-Merge), Spec §4.1 (Modulgrenzen, Fassaden-
Contract), §17.10 (K18–K21). **Schreibt keine Config, keinen Runner, keine `report.py`.**
**Agent:** developer · **Depends on:** W2-2 · **parallel_group:** — (sequenziell; **Einstieg in die
offene W2-Arbeit**, PG-2a startet erst hiernach)
**Ziel-AK (AC):** Querschnitt — **kein** neuer AC. Diese Task **verändert keinen** Vertrag; sie
stellt die Voraussetzung dafür her, dass W2-3…W2-7 überhaupt parallelisierbar sind (AC-07, AC-08,
AC-09 bleiben unverändert **inhaltlich** grün). · **V-Check:** V1a, V1b, V3, V4 + 3 Altchecks
(umbewegt)
**Akzeptanz — Verhaltensneutralität ist die eigentliche Abnahme (K18/K19):**
(a) `python3 -m pytest tests/test_doc_facts.py tests/test_doc_facts_expected.py
tests/test_doc_freshness.py -q` → **0** mit **≥ 163** Tests (Verschiebung, **kein** Verlust);
(b) `python3 scripts/consistency-check.py --json` liefert **unverändert** `{'total': 85, 'errors': 0,
'warnings': 85}` und **keinen** neuen `docs.`-Check; (c) **keine** neue Registrierung —
`scripts/consistency-check.py:52-56` und die Aufrufe `:199-201` sind **byte-identisch**, der
Nicht-Registrierungs-Pin `test_v1_is_not_wired_into_the_runner_yet` bleibt **grün** und wird erst
in **W2-7** ersetzt. **Rev. 0.6 / K47 — Ort des Pins korrigiert:** der Pin ist mit den V1-Tests nach
`tests/test_doc_freshness.py` **verschoben** worden und liegt dort gemessen in
**`:364-383`** (frühere Plan-Angabe: `tests/test_doc_facts.py:2403-2422` — die zu HEAD bereits
falsche Angabe `:2501-2522` bleibt unerwähnt, weil ohne Git-Zugriff nicht prüfbar). Die Formulierung
„bleibt grün in `tests/test_doc_facts.py`" ist damit **gegenstandslos**; maßgeblich ist: der
Assertion-Text `"check_no_manual_counts" not in runner` ist **inhaltlich unverändert** und wird
**erst in W2-7** durch `test_v1_is_registered_in_the_runner` ersetzt (RVW2-5 vollständig in Kraft);
(d) `scripts/lib/consistency/docs.py` enthält **keine** `Finding(...)`-Konstruktion und **kein**
`re.compile` mehr — nur Importe und `__all__`; (e) **Fassaden-Vollständigkeit** (K19): jeder Name
aus Spec §4.1 `__all__` ist aus `docs` importierbar, und die Referenzstellen auf die Doku-Checks
funktionieren **unverändert**. **Rev. 0.6 / K49 — Zählung präzisiert:** „29" ist eine **Zeilen**-
zählung, keine Vorkommenszählung — zu **HEAD** tragen **29 Zeilen** in `tests/test_doc_facts.py`
eine Referenz, aber **30 Vorkommen** von `docs_lib.`, weil `:2204` **zwei** Referenzen in einer Zeile
trägt. **Nach W2-0 gemessen:** in `tests/test_doc_facts.py` verbleiben **21 Zeilen / 22 Vorkommen**
(`:2204` weiterhin mit zwei); die **8** mit ihren Tests gewanderten Vorkommen liegen in
`tests/test_doc_freshness.py` und laufen dort gegen den Alias `docs_freshness_lib` (Import `:28`),
nicht mehr gegen die Fassade: `:107` `check_no_manual_counts`, `:320` `V1_SCAN_RELPATHS`, `:326`
`v1a_count_spans`, `:327` `v1b_version_spans`, `:142`/`:303`/`:347`/`:350` `Severity` — **8** Zeilen,
**8** Vorkommen. Gegenprobe: 21 + 8 = **29 Zeilen**, 22 + 8 = **30 Vorkommen** ✓. **Befund (siehe
Abschnitt „Korrekturrunde 3", **R3-B-1**):** die 8 gewanderten V1-Referenzen belegen die
Fassaden-Erreichbarkeit der V1-Namen **nicht** mehr; Nachweis bleibt das wortgleiche `__all__`
(Schritt 3) in Verbindung mit (d). **Kein** Sollwert und **keine** neue Pflicht wird eingeführt;
(f) **Modulgrenzen** (K18): jedes neue
Modul **< 600 Zeilen** (`wc -l` je Datei, Ergebnis in die Task-Notiz).
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py tests/test_doc_facts_expected.py
tests/test_doc_freshness.py -q` → **0**; `wc -l scripts/lib/consistency/docs*.py` → jede Zeile
**< 600**; `git diff --name-only` → **kein** Pfad außerhalb der `Files:`-Liste (insbesondere **nicht**
`scripts/consistency-check.py`, **nicht** `scripts/lib/consistency/report.py`). **Diese Task-Zeile ist
für sich genommen kein Welle-Gate** (RVW-3): W2-0 ist ein **Querschnitts**-Task der Welle W2, das
Wellen-Gate **W2** ist an **W2-7** gebunden (Wellenblock **W2 — Verifikation**:
`W2-GATE-V1` / `W2-GATE-ERRORS`).
**Belege des Ist-Zustands (Baseline-Messung 2026-09-27, Übergabe vom Parent; kein Shell-Zugriff in
dieser Revisionsrunde):** `docs.py` = **599** Zeilen — `check_sync_cli_docs` `:11-46`,
`check_ui_help_mappings` `:49-98`, `check_readme_docs_index` `:102-124`, V1-Konstanten `:155-173`,
`v1_strict` `:335-348`, `_v1_finding` `:350-369`, `check_no_manual_counts` `:371-412`, V3-Konstanten
`:416-445`, `check_internal_links` `:555-599`; `report.py` = **115**, `consistency-check.py` = **280**,
`tests/test_doc_facts.py` = **2867**, `tests/test_doc_facts_expected.py` = **526**; **20** Module in
`scripts/lib/consistency/`.
**Ist nach W2-0 (Rev. 0.6 / K50, **selbst gemessen** am 2026-09-27, `Read`-Zeilenzählung):**
`scripts/lib/consistency/docs.py` = **80** · `docs_links.py` = **334** · `docs_freshness.py` = **317** ·
`tests/test_doc_freshness.py` = **384** · `tests/test_doc_facts.py` = **2538** (vorher **2867**, also
**−329** durch den Test-Verschieb). **Alle Module < 600** ✓ (Akzeptanz (f) erfüllt). **Modulzahl in
`scripts/lib/consistency/`: 20 → 22** (die beiden neuen Module; `__init__.py` mitgezählt).
**Gemessene Anker in den neuen Modulen:** `docs_freshness.py` — `V1_SCAN_RELPATHS` `:63`,
`V1_CHECK_ID` `:60`, `V1_SUGGESTION` `:75-…`, `Span` `:112`, `v1_strict` `:240-252`, `_v1_finding`
**`:255-273`**, `check_no_manual_counts` `:276-317`; `docs_links.py` — `check_sync_cli_docs`
**`:30-65`**, `check_ui_help_mappings` **`:68-118`**, `check_readme_docs_index` `:121-…`,
`_v3_finding` `:183-…`, `check_internal_links` `:290-…`. **Ausdrücklich noch nicht vorhanden:**
`docs_wiki.py` und `docs_index.py` (je **W2-3** bzw. **W2-6**) — die Prognosen **~200**/**~180**
(Zeilen in „File Structure") sind damit **unverbraucht**. **Luft in `docs_freshness.py`:** **317** von
**600** Zeilen, also Reserve für **V5** (**W2-4**) und **V6** (**W2-5**). Die Zeilenschätzungen in
**Spec §4.1** (~70/~330/~480/~200/~180) waren **Prognosen** und stehen dort ausdrücklich **unter**
der 600er-Grenze; **Spec §4.1 bleibt unverändert** — die Modulzuordnung wird durch diese Korrektur
**nicht** verschoben.
**Steps:**
- [x] 1: `docs_freshness.py` anlegen (V1-Block `:155-412` inkl. `Span`, `v1a_count_spans`,
      `v1b_version_spans`, `v1_strict`, `_v1_finding` und der K16-Eingrenzung in
      `_v1_suppressed_lines`); `docs_links.py` anlegen (`:11-124` + `:416-599`).
- [x] 2: V1-Tests aus `tests/test_doc_facts.py` **verschieben** (nicht kopieren) nach
      `tests/test_doc_freshness.py`; Imports dort auf `docs_freshness` umstellen; die V3- und
      Altcheck-Tests **bleiben** in `test_doc_facts.py` und greifen weiter über die Fassade.
- [x] 3: `docs.py` auf Fassade reduzieren — `__all__` **wortgleich** nach Spec §4.1; `Finding` und
      `Severity` aus `.report` **durchreichen** (Testreferenz `docs_lib.Severity`).
- [x] 4: Nachweise (a)–(f) der Akzeptanz ausführen und im Review-Protokoll festhalten; insbesondere
      `163` als Vorher-Baseline gegen den Nachher-Zähler stellen und **jede** Differenz als
      Befund melden (kein stilles Nachziehen der Zahl).
- [x] 5: commit via `git`-Agent:
      `refactor: split consistency docs checks into family modules`.

### W2-9: `TASK_HEADER_RE` um die Wellen-/Task-Header erweitern (Rev. 0.7, E-8, K57/K58) — **der Ledger-Writer wird ab hier einsetzbar**

**Files:** Modify `scripts/lib/plan_identity.py` (**die Definition**),
**`scripts/lib/consistency/spec_plan.py` (K62 / RVW-7-04 — der dritte Konsument; siehe unten)**,
`tests/test_plan_identity.py`, `tests/test_plan_ledger_writer.py`; Modify
`scripts/lib/plan_ledger.py` (**bedingt** — nur falls sich der Zwei-Gruppen-Vertrag des Treffers
ändert; im Normalfall **read-only**).
**K58 (Faktenkorrektur, ausdrücklich):** `TASK_HEADER_RE` ist **nicht** in `plan_ledger.py`
definiert. **Gemessen:** Definition `scripts/lib/plan_identity.py:27-30`, importiert in
`plan_ledger.py:25`, benutzt in `_task_blocks()` (`:71`, `finditer`), entpackt in
`update_plan_ledger()` (`:133`, `for task_id, start, end in reversed(_task_blocks(original))`),
`unmatched` in `:172`/`:182`, Exit-Code in `:272`. **Beide** Dateien stehen deshalb in `Files:`.
**Interfaces:** Produces: `TASK_HEADER_RE` erkennt **zwei** Header-Formen — (i) `### Task <id>: …`
(**unverändert**, Rückwärtskompatibilität für alle anderen Pläne) und (ii) `### <Welle>-<k>: …`
mit ID-Form `W<n>-<k>`. **Die Zwei-Gruppen-Struktur bleibt erhalten** (`group(1)` = Task-ID,
`group(2)` = Resttitel), damit `_task_blocks()` und `update_plan_ledger()` **unverändert** bleiben.
**Ausdrücklich NICHT geändert (K66 / RVW-7-08):** `normalize_task_id` und `TASK_ID_RE`.
**Gemessen:** `normalize_task_id("W2-0") == "W2-0"` **heute schon** — der Durchreich-Zweig
`return raw` (`plan_identity.py:73`) greift, weil `TASK_ID_RE = ^task-[0-9]+$` (`:18`) **nicht**
passt; **belegt** ist das verhaltensgleich durch `normalize_task_id("custom") == "custom"`
(`tests/test_plan_identity.py:100`, **derselbe** Zweig) — der **`W2-0`-Pin wird in Akzeptanz (f)
neu angelegt** (**K71**; der Anker `:96-101` aus Korrekturrunde 5 war falsch, dort steht
`test_normalize_task_id` **ohne** `"W2-0"`). Der
Rev.-0.7-Text behauptete hier einen Teilfehler (b), den es **nicht** gibt. **Konsequenz:** W2-9
ändert **ausschließlich** (a); eine „Reparatur" von (b) **bricht den Round-Trip** und ist
**verboten**. (b) wird als **No-op-Pin** fortgeführt (Schritt 1).
**Ebenfalls in dieser Task, ausdrücklich (K62 / RVW-7-04):** `_parse_plan_tasks`
(`spec_plan.py:547-583`, Regex-Bindung `:55`, `finditer` `:557`) ist der **dritte** Konsument von
`TASK_HEADER_RE` und extrahiert seine **Dep-Tokens** über das **hart kodierte** Muster
`task-\d+|\d+` (`:570` — **Vor-Implementierungs-Anker**; Ist-Ort nach W2-9: `_DEP_TOKEN_RE` `:68`,
Verwendung `:581`). **Dieses Muster wird auf `W\d+-\d+` erweitert** (alternativ: Token gegen
`_DEPENDS_RE`-Treffer und `normalize_task_id` bilden). **Warum das zwingend ist:** ohne diese
Erweiterung liefert `**W2-3**` die Tokens `2`/`3` ⇒ `task-2`/`task-3` und `**W2-0**` ⇒ `task-0`;
`find_dependency_errors` (`orchestration.py:207-216`) meldet daraufhin **dangling dependency**, und
`validate_plan` (`:287-289`) kehrt **vor** dem Overlap-Check ab — die fail-closed-Ownership-Klausel
(K20, Spec §17.10.4) fiele damit **ganz aus**, statt falsch zu sein.
**Verworfene Alternative, begründet (K62):** die plan-getriebene Fanout-Prüfung für diesen Plan
**nicht** nutzen und stattdessen verbindlich festlegen. Verworfen, weil ein **erreichbares, aber
kaputtes** Instrument schlechter ist als ein nicht genutztes: `check_spec_plan_workflow` ist über
`_parse_plan_tasks` für **jeden** Plan aufrufbar, und die Dep-IDs `task-N` wären für **jeden**
Plan mit `W<n>-<k>`-Headern Phantom-IDs. Ein Pin, der nur sagt „wird hier nicht genutzt", hält das
Instrument nicht heil und macht die Ownership-Klausel unerzwingbar.
**Nicht Gegenstand dieser Task:** der **Overlap-Verdict** selbst wird **nicht** geändert.
`check_file_overlap` (`file_affinity.py:50-57`) bewertet gemeinsame Write-Set-Dateien als
**hard overlap** — für diesen Plan also `scripts/lib/consistency/docs.py` (W2-1/W2-2/W2-0/W2-7).
Das ist **kein** Fehlurteil: die Plan-Regel K20 erlaubt mehrere schreibende Tasks derselben Datei
**ausschließlich sequenziell**, und genau das bildet die topologische Ordnung ab. Der erwartete
Overlap-Befund wird deshalb in Akzeptanz (e) **namentlich als erwartet** festgeschrieben statt
wegdefiniert.
**Agent:** senior-developer · **Depends on:** **W2-0** (**Sequenzierungs-Kante, keine
Datenabhängigkeit** — W2-9 steht vor PG-2a, damit **alle noch offenen W2-Tasks** (W2-6, W2-4, W2-8,
W2-7) mit dem Werkzeug abgehakt werden können) · **parallel_group:** — (**sequenziell**, Phase 0)
**Ziel-AK (AC):** **Querschnitt — kein neuer AC.** Diese Task ändert **keinen** Vertrag des
Vorhabens; sie stellt ein **Werkzeug** her, mit dem die Checkboxen dieses Plans gepflegt werden
(DoD Punkt 14). · **V-Check:** — (kein Consistency-Check betroffen)
**Akzeptanz:**
(a) `tests/test_plan_identity.py` — ein Test, dass `TASK_HEADER_RE` **beide** Formen findet und
`group(1)` korrekt liefert (`### Task task-1: X` → `task-1`; `### W2-0: X` → `W2-0`); ein Test, dass
eine **Nicht-Task**-`###`-Überschrift (`### File Structure`, `### L-1 …`) **kein** Task ergibt
(sonst liest der Parser Abschnitte als Tasks — genau das Risiko aus K53);
(b) `tests/test_plan_ledger_writer.py` — Round-Trip `update_plan_ledger({…})` ↔
`parse_plan_ledger()` auf einem Fixture mit Wellen-Headern: `unmatched == ()`, `ok == True`;
(c) **End-to-End gegen diesen Plan** (der eigentliche Nachweis): `plan_ledger` gegen
`docs/plans/2026-09-25-repository-documentation-consolidation.md` mit `W2-6` läuft ohne
`unmatched` und **Exit 0**; **vorher** (Baseline, im Task belegt) `unmatched={W2-6}` und **Exit 1**;
(d) **Kein** Regressionsrisiko für die anderen Pläne: die bestehenden `### Task`-Tests
(`tests/test_plan_identity.py:26-50`) bleiben **wortgleich** grün;
(e) **Plan-Graph-Pflicht (K62 / RVW-7-04, neu):** ein Test, dass `_parse_plan_tasks` gegen
**diesen** Plan **50** Tasks liefert und **keine** Phantom-Dep-ID erzeugt — insbesondere
`W2-6` ⇒ Deps `{W2-0}` und **kein** `task-0`/`task-2`; `validate_plan` liefert für den Plan-Graph
**keine** `deadlock:`-/`cycle detected`-Meldung. **Erwarteter und namentlich festgeschriebener
Restbefund:** der `file_overlap`-Befund für `scripts/lib/consistency/docs.py` (W2-1/W2-2/W2-0/W2-7)
**bleibt** — er ist die korrekte Abbildung der K20-Regel „mehrere schreibende Tasks derselben
Datei ⇒ ausschließlich sequenziell" und wird **nicht** wegdefiniert; der Test **pinnt** ihn als
erwartet, damit eine spätere Änderung auffällt;
(f) **No-op-Pin für (b) (K66 / RVW-7-08, neu):** ein Test, der `normalize_task_id("W2-0") ==
"W2-0"` **vor und nach** der Änderung festhält — er darf **nicht** rot werden, und **darf nicht**
zu einem Vorher/Nachher-Vergleich umgebaut werden.
**Verifikation:** `python3 -m pytest tests/test_plan_identity.py tests/test_plan_ledger_writer.py
tests/test_plan_ledger.py tests/test_checkpoint_plan_identity.py tests/test_recovery.py -q` → **0**;
der End-to-End-Aufruf aus (c) druckt **keine** `unmatched task ids`-Zeile und liefert **0**;
`ruff check scripts/lib/plan_identity.py scripts/lib/plan_ledger.py
scripts/lib/consistency/spec_plan.py` → **0**.
**Position und Wirkung, ausdrücklich (die Pflichtaussage dieses Tasks):** W2-9 liegt in **Phase 0**
von W2, **unmittelbar nach W2-0 und vor PG-2a**. **⇒ „Ledger-Writer einsetzbar ab Task W2-9"**,
also für **W2-6**, **W2-4**, **W2-8** und **W2-7**. **Ausdrücklich: jetzt noch nicht** — bis W2-9
gelaufen ist, gilt die **K53-Interim-Regel** (manuelles Abhaken durch den Orchestrator mit Datum,
Commit-Hash und Task-ID im Abschnitt **L-1**) **unverändert**; ein Werkzeuglauf gegen diesen Plan ist
vor W2-9 **kein** gültiger Nachweis. **Ende der Regel:** mit dem Commit von W2-9 entfällt die
Interim-Regel **ausdrücklich** (nicht stillschweigend) — der erste abgehakte Task **danach** ist
W2-6.
**Diese Task-Zeile ist für sich genommen kein Welle-Gate** (RVW-3): W2-9 ist ein
**Querschnitts**-Task; das Wellen-Gate **W2** bleibt an **W2-7** gebunden.
**Steps:**
- [x] 1: Tests in `tests/test_plan_identity.py` und `tests/test_plan_ledger_writer.py` schreiben
      (fail) — beide Header-Formen, der Nicht-Task-Ausschluss, der Round-Trip, der **No-op-Pin (f)**
      und der **Plan-Graph-Test (e)**.
- [x] 2: `TASK_HEADER_RE` um den Wellen-/Task-Header-Zweig erweitern; **Zwei-Gruppen-Vertrag erhalten**;
      **Dep-Token-Muster in `scripts/lib/consistency/spec_plan.py:570` (Vor-Implementierungs-Anker;
      Ist-Ort nach W2-9: `_DEP_TOKEN_RE` `:68`, Verwendung `:581`) auf `W\d+-\d+` erweitern**;
      `normalize_task_id` / `TASK_ID_RE` **unangetastet** (K66).
- [x] 3: End-to-End-Nachweis (c) **und (e)** gegen diesen Plan ausführen (Baseline vorher:
      `unmatched` + Exit 1; `0` Tasks im Plan-Graph) und im Task-Notiz-Format festhalten;
      **K53-Interim-Regel ausdrücklich für beendet erklären**.
- [x] 4: commit via `git`-Agent: `feat: accept wave task headers in the plan ledger writer`.

> **LEDGER-Stand 2026-09-28 — W2-9 VOLLSTÄNDIG erledigt (Fortschrittsnotiz, keine Änderung der
> Task-Semantik).** Abgehakt nach der **Interim-Regel aus K53** — W2-9 ist der **letzte** Task
> unter dieser Regel: **4** von **4** Checkboxen von Hand gesetzt, mit **Datum (2026-09-28)**,
> **Task-ID `W2-9`** und **Commit-Titel** `feat: accept wave task headers in the plan ledger writer`;
> der **Hash** entsteht erst mit diesem Commit und ist deshalb **nicht** genannt (kein erfundener).
> **Ende der K53-Interim-Regel, ausdrücklich — nicht stillschweigend:** ab dem Commit dieses Tasks
> ist der maschinelle Ledger-Writer gegen diesen Plan einsetzbar; der erste abgehakte Task
> **danach** ist **W2-6**. Der „jetzt noch nicht"-Zustand der Task-Interfaces entfällt damit.
> **Gelandet:** `plan_identity.py` 86 → **116 Z** (`WAVE_ID_PATTERN` als Single Source der
> Wellen-ID, Wellen-Gate **begrenzt**), `spec_plan.py` 596 → **607 Z** (`_DEP_TOKEN_RE` `:68`,
> Verwendung `:581`), `test_plan_identity.py` 119 → **210 Z** (**8** Tests, +3),
> `test_plan_ledger_writer.py` 302 → **530 Z** (**22** Tests, +6). `plan_ledger.py` **unverändert**
> (275 Z): der Zwei-Gruppen-Vertrag ist auch durch die Fix-Runde nicht gewandert, der
> `Files:`-Eintrag „bedingt" greift also **nicht**.
> **Nachweis (a)–(d), (f):** (a) `test_header_regex_wave_and_task_forms` +
> `test_header_regex_ignores_non_task_h3_headings`; (b) `test_wave_header_ledger_round_trip`
> (`ok is True`, `unmatched == ()`) + `test_wave_header_does_not_answer_classic_task_ids`;
> (c) `test_ledger_writer_addresses_this_plan` — **End-to-End `dry_run` gegen diesen Plan**:
> `unmatched == ()`, `tasks_updated == ('W2-6',)`, **Exit 0**, **keine** `unmatched task ids`-Zeile,
> Plan **byte-unverändert**; **Baseline** (alte Regex via `git show HEAD:scripts/lib/plan_identity.py`
> nach `.tmp/` gebunden, Working Tree unberührt): `unmatched=('W2-6',)`, **Exit 1**,
> `unmatched task ids: W2-6`, und **0** Tasks im Plan-Graph; (d) die klassischen `### Task`-Tests
> **wortgleich** — der Test-Diff ist ein reiner Append; (f)
> `test_normalize_task_id_leaves_wave_id_unchanged`: reine Assertion, **kein**
> Vorher/Nachher-Vergleich, `normalize_task_id`/`TASK_ID_RE` unangetastet (K66).
> **Akzeptanz (e) — gemessen, zwei Prämissenfehler im Rev.-0.7-Text (nicht W2-9):** erfüllt sind
> **50** Tasks mit **50** eindeutigen IDs (keine Dubletten), `find_dependency_errors == []`,
> **keine** `deadlock:`-/cycle-Meldung, **keine** Phantom-Dep-ID (kein `task-0`/`task-2`) und
> **17** Overlap-Meldungen, alle `file overlap between …`. **Nicht erfüllt:** `W2-6` ⇒ Deps ist
> `()` , nicht `{W2-0}` — Ursache: `_DEPENDS_RE` (`spec_plan.py:60`) ist zeilenverankert, der Plan
> schreibt `**Depends on:**` **mittig** (`_DEPENDS_RE.findall(plan)` = **0**, 0 von 50 Tasks mit
> Deps); und **keine** der 17 Meldungen nennt `scripts/lib/consistency/docs.py` — Ursache:
> `_FILES_FIELD_RE` verlangt bei `Modify`/`Create` den **Doppelpunkt**, der Plan schreibt
> `**Files:** Create \`…\`` **ohne** ⇒ `files_touched == ()` für alle **50**, die Overlaps entstehen
> aus den Task-**Titeln**. Beides ist als **gemessener Zustand** mit Begründung gepinnt, **nicht**
> wegdefiniert.
> **Drei offene, dokumentierte Abweichungen** (Owner **Plan-Eigner** (`requirements`), Frist **vor
> dem Merge von PR #839**; **kein** Blocker für diesen Commit): **(1)** Akzeptanz (e) ist für diesen
> Plan **nicht erfüllbar** und braucht eine Korrektur des Rev.-0.7-Textes. **(2)** der
> `docs.py`-`file_overlap`-Befund ist **nicht erzeugbar** — beobachtbar erst nach einer
> `Files:`-Syntax-Korrektur bzw. einer `_FILES_FIELD_RE`-Änderung, **eigener Task**, nicht W2-9.
> **(3)** die Verifikationszeile `ruff … → 0` ist **unerreichbar**: HEAD-Baseline **14** vorbestehende
> Findings bei explizitem `--select I,UP,E,F,W` — **9** in `plan_ledger.py` (das laut Plan clean
> bleiben muss) + **3** in `plan_identity.py` + **2** in `spec_plan.py` —, in HEAD und Working Tree
> **identisch**, also **Delta W2-9 = 0** (kein einziges neues Finding). Der nackte Aufruf der
> Verifikationszeile meldet **13**, weil ruff im Default-Select `E4,E7,E9,F` das dort zusätzlich
> gezählte `E501` (`spec_plan.py:481`, 94 > 88) nicht führt; eine ruff-Config existiert im Repo
> nicht, `--isolated` ändert hier also nichts.
> **Fix-Runde Code-Review (m2–m5), jeweils gemessen:** **m2** Wellen-Gate **begrenzt** —
> `plan_identity.py:47` verlangt nach `<W>-<k>` jetzt `(?=[ \t]*(?::|[—–-])|[ \t]*$)`; vorher
> lieferten `### W2-0abc: X` und `### W2-0_x: X` die Task-IDs `W2-0abc`/`W2-0_x`, die
> `normalize_task_id` unverändert durchreicht — eigenständige, nie adressierbare Phantom-IDs, also
> genau die Klasse, die W2-9 beseitigen soll; jetzt **kein** Task. Blast-Radius: **50** Wellen-Header
> im Repo (alle **50** in diesem Plan, sonst nirgends), **0** Verhaltensänderungen zwischen
> begrenztem und unbeschränktem Gate; Scan-Scope **958** Markdown-Dateien über die Wurzeln `docs`,
> `agents`, `.claude`, `.opencode`, `scripts`, `snippets`, `knowledge`, `graphify-out`, `external`
> (ohne weitere Ausschlüsse; eigener Zählgang am selben Tag: **959** — die Differenz **1** ist eine
> zwischenzeitlich geänderte Datei, kein Scope-Unterschied). **m3** Benennung korrigiert
> (`plan_identity.py:40-46`, `test_plan_identity.py:127-131`): `group(1)`-Konsumenten sind
> `_task_blocks()` (`plan_ledger.py:76`) und `parse_task_ledgers()` (`spec_plan.py:127`), der
> **einzige** `group(2)`-Konsument ist `_parse_plan_tasks()` (`spec_plan.py:575` → `prompt` `:589`).
> **m4** vier Fälle ergänzt: `### W2-0abc: X`, `### W2-0_x: X`, `### W 2-0: X`, `### Wave 2-0: X`
> ⇒ **kein** Task; `### W2-0` ⇒ `group(1) == 'W2-0'`, `group(2) == ''`. **m5** Magic Numbers
> etikettiert, **keine** Sollwert-Änderung: `len(tasks) == 50` ist der Vertrag für diesen Planstand
> und muss von jeder Plan-Änderung mitgezogen werden; `len(errors) == 17` ist ein
> **provisorischer Tripwire** aus der Titel-Text-Extraktion, kein semantischer Wert. **Der Tripwire
> hat sich beim Schreiben dieser Notiz bewährt:** der erste Entwurf enthielt die Doppelpunktform
> von `Modify`/`Create` im Fließtext, worauf `_FILES_FIELD_RE` für **W2-9** den Phantom-Write-Set
> `('/',)` extrahierte und der Pin sofort rot wurde — der Fließtext eines Task-Blocks kann also eine
> Write-Menge **fälschen**; die Notiz ist deshalb umformuliert, nicht der Pin. **Vakuum-Stelle an der
> Assertion kenntlich gemacht** (`sum(... dependencies) == 0`): sie ist eine Kanone, kein Beweis —
> der tragende Nachweis bleibt `test_wave_header_dep_tokens_yield_wave_ids_only`.
> **Faktenkorrektur zum Tripwire (nachträglich gemessen):** der oben genannte Wert **17** war
> **nie** der Ist-Wert. Der Pin wurde in **`3d8499ca`** **geboren rot** eingeführt — gegen Plan
> **und** Baum dieses Commits misst er **13**, gegen den heutigen Baum **18**. Dieselbe
> Planfassung liefert je nach Baum verschiedene Zahlen, weil `check_file_overlap` die hier
> durchweg leeren Write-Sets aus den **Task-Titeln** bildet und sie um die Import-/Doc-Referenz-
> Kanten des Working Tree **weitet**; der Zähler hängt also an Plan- **und** Doku-Satz, nicht an
> einer Regel dieses Repos. Der Pin wurde in dieser Task **gepflegt, nicht abgeschwächt**:
> Ist-Wert **18**, exakt `==`, ohne `>=`/`<=`, ohne Weglassen, ohne `xfail`. **Pflegepflicht:**
> verschiebt sich die Zahl, ist neu zu messen, die Ursache zu benennen und das Literal
> nachzuziehen — Sichtbarkeitsgarantie, kein semantischer Vertrag.
> **Verifikation:** fokussierte Suite **58 passed**, Exit **0**; `python3 -m compileall -q
> scripts/lib` → **0**; `ruff check --select I,UP,E,F,W` über die drei Dateien **14** Findings
> (**9** `plan_ledger.py` / **3** `plan_identity.py` / **2** `spec_plan.py`) wie in der HEAD-Baseline,
> **Delta 0**; Volltests als Baseline (**kein** Kriterium, `W-VALIDATE-ROT`): **2 failed, 3390
> passed, 1 skipped, 35 errors** — die 2 roten sind die planmäßig roten W2-8/E-6-Kandidaten, die
> 35 errors sind `tests/browser/*` ohne Socket.
> **Reviews:** beide Stufen **`ACCEPTED_WITH_DEVIATIONS`**. Die majors aus Stufe 1 sind als
> Abweichungen **(1)–(3)** dokumentiert und **nicht** in W2-9 behoben; die minors **m2–m5** sind
> hier behoben. M1 (Commit-Hygiene) ist eine Anweisung an den `git`-Agenten, kein Code-Eingriff.

### W2-3: V7 `check_wiki_staleness` — **Rev. 0.6: eigenes Modul + eigene Testdatei (PG-2a)**

**Files:** Create `scripts/lib/consistency/docs_wiki.py`, `tests/test_doc_wiki.py`
(**Rev. 0.6 / K20** — neu; in Rev. 0.5: Modify `scripts/lib/consistency/docs.py`,
`tests/test_doc_facts.py`)
**Interfaces:** Produces: `check_wiki_staleness(root, config=None) -> list[Finding]`, Severity
**WARNING**, als **dünne Adapter-Schicht auf W1-4** in `docs_wiki.py`. Consumes: W1-4
(`compute_wiki_staleness`), **W2-0** (Modul-Familie „abgeleitete Bestands-Oberfläche"; später W6-2
mit V8).
**Agent:** developer · **Depends on:** **W2-0** (Rev. 0.6; vorher W2-2) · **parallel_group:**
**PG-2a** (Rev. 0.6; parallel mit **W2-5** und **W2-6**)
**Ziel-AK (AC):** **AC-10** (IC-05) · **V-Check:** **V7**
**Akzeptanz:** `test_v7_missing_and_stale_derived_from` grün: `type: Architecture` **ohne**
`derived-from` ⇒ Finding; `derived-from` mit `mtime(Quelle) > derived-at` ⇒ Finding nennt
`stale-source`. Die Behebung (Annotation) erfolgt in W5-3. **Rev. 0.6:** der Test steht in
`tests/test_doc_wiki.py` und der Check in `docs_wiki.py` — V7 ist damit **nicht** mehr aus der
`docs.py`-Fassade heraus zuständig, wohl aber **über sie** aufrufbar (`__all__`).
**Verifikation (Rev. 0.6):** `python3 -m pytest tests/test_doc_wiki.py -q` → **0**;
`wc -l scripts/lib/consistency/docs_wiki.py` → **< 600**; ~~`python3 scripts/consistency-check.py` →
**0** (nur WARNINGs).~~ **AUFGEHOBEN (Rev. 0.5, RVW-2) — die Klammer war sachlich falsch und die
Zeile unerreichbar.**
V7 ist zwar WARNING, aber W2-3 folgt auf **W2-2**: sobald V3 registriert ist, meldet
`check_internal_links` auf `README.md:722-723` einen **ERROR** (Task **W2-2**-Akzeptanz), und
`print_report` gibt `1 if errors else 0` (`scripts/lib/consistency/report.py:75`) — der rohe
Runner ist damit Exit **1**, nicht 0. Die Zeile bleibt als Historie sichtbar; maßgeblich ist
**W2-GATE-ERRORS** (Erwartungswert `docs.wiki_staleness` planmäßig rot, Termin **W5-3**,
Owner `tester`; V3 planmäßig rot, Termin **W8-2**). **Diese Task-Zeile ist für sich genommen
kein Welle-Gate** (RVW-3).
**Steps:**
- [x] 1: Test schreiben (fail).
- [x] 2: V7 als dünne Adapter-Schicht auf W1-4 implementieren.
- [x] 3: Test grün beobachten.
- [x] 4: commit via `git`-Agent: `feat: add V7 wiki staleness check`.

> **LEDGER-Stand 2026-09-27 — W2-3 VOLLSTÄNDIG erledigt (Fortschrittsnotiz, keine Änderung der
> Task-Semantik).** Gelandet: `scripts/lib/consistency/docs_wiki.py` (**neu, 129 Z**) und
> `tests/test_doc_wiki.py` (**neu, 391 Z**, **10** Tests) — reine Adapter-Schicht, **0** Zeilen
> Staleness-Logik, alles über `compute_wiki_staleness` (W1-4); ruff/compileall clean.
> **Nachweis:** V7 **nicht** registriert ⇒ Baseline `85/0/85` unverändert erhalten.
> **Reviews:** Stufe 1 + Stufe 2 im **PG-2a**-Durchgang, **kein** offener Befund am Code.
> **Nebenbefund (K51):** die V7-Baseline wurde von **11 auf 10** korrigiert — **K24** war eine
> Fehlmessung (ein `type:`-Body-Kommentar in
> `knowledge/wiki/concepts/core-principle-knowledge-engine.md:46`).
> **Kein Wellen-Gate:** W2-3 ist **kein** Querschnitts-Task; das Wellen-Gate **W2** bleibt an
> **W2-7** gebunden. Commit `8594e67f` (`feat: add V7 wiki staleness check`, 2 Dateien, +520).

### W2-4: V5 `check_role_generation_parity` (gate-bewusst) — **Rev. 0.7 / E-7: eigenes Modul `docs_freshness_v5.py` (K56), Phase B**

**Files:** Create `scripts/lib/consistency/docs_freshness_v5.py`,
Create `tests/test_doc_freshness_v5.py` (**Rev. 0.7 / E-7** — **rev. 0.6 / K20** nannte hier
`Modify scripts/lib/consistency/docs_freshness.py`, `tests/test_doc_freshness.py`; **Rev. 0.5**:
`Modify scripts/lib/consistency/docs.py`, `tests/test_doc_facts.py`). **Ausdrücklich `nicht` in
`Files:`** — `scripts/lib/consistency/docs_freshness.py`, `tests/test_doc_freshness.py` und
`scripts/lib/consistency/docs.py`: die ersten beiden behält **W2-5**, die Fassade ist
**W2-7s** alleiniges `__all__`-Eigentum (K46-Negativregel).
**Interfaces:** Produces: `check_role_generation_parity(root, config=None) -> list[Finding]`;
Severity **ERROR**, sobald `systems-engineering.enabled: true`, sonst **WARNING**; in
**`docs_freshness_v5.py`** (Familie „dokumentierter Rollenbestand vs. erzeugte Rollen", Spec §4.1,
Rev. 0.7). Der Name wird von der Fassade `docs.py` **weiter** durchgereicht — das `__all__`-Inkrement
ist **W2-7s** Schreibmenge, nicht W2-4s. Consumes: W1-3 (`compute_active_roles`), **W2-5** (Phase-B-Reihenfolge; die frühere Begründung „gemeinsame Schreibmenge" ist nach E-7 **gegenstandslos**, die Kante bleibt als historische Kante bestehen).
**Agent:** senior-developer · **Depends on:** W2-5 (Rev. 0.7; Rev. 0.6; vorher W2-3) ·
**parallel_group:** — (**sequenziell**, Rev. 0.6; Rev. 0.5: PG-2/W2)
**Ziel-AK (AC):** **AC-11** (IC-05) · **V-Check:** **V5**
**Akzeptanz:** `test_v5_severity_depends_on_se_gate` grün; Vergleichsmenge ist
`compute_active_roles()` (IC-04), **nicht** der `roles:`-Listeninhalt (F21-Dauerfehlalarm, NG-8).
**Verifikation (Rev. 0.7):** `python3 -m pytest tests/test_doc_freshness_v5.py
tests/test_doc_freshness.py -q` → **0**; `wc -l scripts/lib/consistency/docs_freshness_v5.py` →
**< 600**; `wc -l scripts/lib/consistency/docs_freshness.py` → **≤ 600** (muss **592** bleiben — der
Nachweis, dass W2-4 das Modul **nicht** anfasst).
**Warum W2-4 **nicht** Teil von PG-2a ist (K20, ehrlich benannt):** W2-4 lag in Rev. 0.6 in Phase B,
weil es dasselbe Modul (`docs_freshness.py`) und dieselbe Testdatei (`tests/test_doc_freshness.py`)
wie W2-5 (V6) schrieb. **Rev. 0.7 / E-7 hebt genau diesen Grund auf** — W2-4 schreibt jetzt zwei
**neue** Dateien und ist damit von jedem PG-2a-Task **write-set-disjunkt**. **Warum es trotzdem
sequenziell bleibt (begründet, nicht bequem):** die Kante `W2-5 → W2-4` wird **nicht** entfernt,
sondern **wirksam** gehalten. Grund: W2-4s Nachweis ist der Vergleich gegen `compute_active_roles()`
**und** die Modulgrößen-Invariante „`docs_freshness.py` bleibt 592" — Letzteres ist erst **nach**
W2-5 beobachtbar. **Das ist eine Verschärfung, keine Lockerung:** W2-4 könnte in PG-2a laufen, aber
dann wäre der Größennachweis `592` eine Behauptung statt einer Messung. **Kosten der
Entscheidung, benannt:** ein Task mehr in Phase B und damit ein zusätzlicher Agentenlauf.
**Größenfolge (verbindlich, K56):** `docs_freshness.py` **592** Z (V1a/V1b + V6, **8** Z Reserve,
**kein** weiterer V-Check) · `docs_freshness_v5.py` **≈ 55–70** Z (V5) — **beide < 600** ✓.
**Ausdrücklich verworfene Wege (E-7, nicht stillschweigend):** **(a)** Wiederverwendung von
`_v6_computed_facts` / `_v6_finding` — **versteckte Kopplung**: `V6_CHECK_ID` und
`V6_SEVERITY_BY_KIND` sind auf V6 verdrahtet, V5 braucht `check="docs.role_generation_parity"` und
ERROR **iff** `systems-engineering.enabled: true`; `_v6_computed_facts` rechnet **Doku-Facts**,
V5 **vergleicht Rollen** — **keine** Überlappung. **(b)** Komprimieren der V1-Prosa — rechnerisch
wirksam, aber ein **Lesbarkeitsverlust** der V1-Dokumentation gegen eine **harte** Grenze; die
Grenze wird nicht aufgeweicht, indem man die Nachbarschaft aufweicht. **Beide** Wege würden
entweder eine Kopplung in einen geteilten Helfer einziehen oder einen Sollwert (die < 600-Grenze)
neu auslegen; **E-7** nimmt statt dessen eine **fünfte** Moduldatei.
**Steps:**
- [x] 1: Test in `tests/test_doc_freshness_v5.py` schreiben (fail).
- [x] 2: `docs_freshness_v5.py` anlegen; V5 mit Gate-Auswertung implementieren.
- [x] 3: Tests grün beobachten; Ist-Zustand (F13) muss **WARNING** sein; beide `wc -l`-Belege
      (592 bzw. < 600) festhalten.
- [x] 4: commit via `git`-Agent: `feat: add V5 gate-aware role parity check in own module`.

> **LEDGER-Stand 2026-09-28 — W2-4 VOLLSTÄNDIG umgesetzt (Fortschrittsnotiz, keine Änderung der
> Task-Semantik).** Abgehakt über den **maschinellen Ledger-Writer** (`--update-plan-ledger` gegen
> diesen Plan, `--task W2-4`): Dry-Run `tasks updated: W2-4`, `checkboxes would toggle: 4`,
> **Exit 0**, **keine** `unmatched`-Zeile; schreibender Lauf `tasks updated: W2-4`,
> `checkboxes toggled: 4`, **Exit 0**, **keine** `unmatched`-Zeile. Der Plan-Diff gegen die
> Vorher-Kopie ist **genau diese 4 Zeilen** (alle vier in `**Steps:**` dieses Blocks, Zeilen
> 3060–3064); Plan bleibt `status: APPROVED`, `revision: 0.7`, keine ID umnummeriert.
> **Ehrlich zu Schritt 4:** auftragsgemäß mit abgehakt, der **Commit ist nicht erfolgt** — W2-4
> lief als **No-Commit**-Task; der Commit ist der Schritt des `git`-Agenten.
> **Größen, gemessen (Stand LANDUNG; Fix-Runde 1 hat sie geändert — aktuelle Werte siehe am Ende
> dieser Notiz):** `scripts/lib/consistency/docs_freshness_v5.py` **121 Z** (**< 600** ✓),
> `tests/test_doc_freshness_v5.py` **324 Z**, **8** Testfälle. Die Plan-Prognose „≈ 55–70 Z" ist
> **nicht** erreicht (+51): der Rev. 0.7-Auftrag macht den Modul-Docstring zum Pflichtbestandteil
> (IC-04-Begründung, `FactUnavailable`-Entscheidung mit V6-Muster, E-7-Verwerfungen,
> Gate-Lesart, Registrierungs-Vorwegnahme) — **42 der 121 Z** sind dieser Docstring. Die harte
> Grenze `< 600` ist mit **479 Z Reserve** erfüllt; **kein** Sollwert wurde abgesenkt.
> **592-Nachweis (der eigentliche Zweck der Kante W2-5 → W2-4), gemessen:** `docs_freshness.py`
> **592 Z vorher wie nachher**, und **byte-identisch** — `sha256` **vorher = nachher =
> `3184e222b1b2c490cbac4ef4d5f318d57ecaf002ef89981292093c453e22b31d`**. W2-4 fasst das Modul nicht an.
> **Vergleichsmenge, gemessen:** `compute_active_roles(REPO_ROOT, project.yaml)` ⇒ **58** gegen
> **59** Einträge in `roles:`; Differenzmenge **genau 1** ⇒ `se-component-requirements`. Auflösung
> über `roles.resolve_active_roles(..., require_template=True)` ⇒ **identisch** (Parität
> nachgewiesen, der in `doc_facts`:174-185 für W2-4 festgehaltene Consumer-Obligation-Satz (b)).
> **`FactUnavailable`, entschieden und begründet:** V5 **kann** degradieren (eine Vergleichsseite
> fehlt ⇒ es gibt nichts zu vergleichen) und degradiert deshalb zu **Stille** — dieselbe Lesart
> wie V6s `_v6_project_config` (`docs_freshness.py`:410) und `_v6_computed_facts` (`:426`), ein
> fehlender Sollwert ist **Abwesenheit, kein Drift**. Der Sentinel ist `None`, **nicht** `set()`;
> die verworfene Alternative (Ausnahme melden bzw. eine leere Menge erfinden) ist im Docstring
> benannt: `consistency-check.py` hat **keinen** Check-`try`-Block, eine Ausnahme würde den
> ganzen Runner abreißen, und ein Finding-Klasse „unavailable" ist in IC-05 nicht definiert.
> **F13-Ist-Wert, gemessen an diesem Repo:** `systems-engineering.enabled: false` ⇒ genau **1**
> Finding, Severity **WARNING** (gate `se` über `config/role-defaults.yaml::activation_groups`
> geschlossen; Gate-Lesart über `roles.resolve_activation_gates`, **kein** hart kodierter
> Gate-Pfad). **Beide Severity-Zweige** sind gemessen, nicht behauptet: die **ERROR**-Hälfte liest
> eine Kopie desselben Baums mit geöffnetem Gate **und** einer `roles:`-Rolle ohne Template.
> **Nicht-Vakuum-Nachweis, Mutanten (alle gemessen, `.tmp/w2-4/mutate.py`, **7** Mutanten — Stand
> LANDUNG; Fix-Runde 1 hat den achten ergänzt, aktuelle Tabelle am Ende dieser Notiz):**
> `roles:`-Liste als erzeugte Menge (**7** failed) · Severity fest ERROR (**2**) · Severity fest
> WARNING (**1**) · dauerhaft still (**7**) · Richtung umgekehrt (**7**) · Provider-Dimension
> ausgewertet statt übersprungen (**6**) · `FactUnavailable` zu `set()` (**1**) — die letzte ist der
> Mutant, der aus der verlockendsten Ein-Zeilen-„Korrektur" eine erfundene Meldung **pro
> deklarierter Rolle** macht. **Beide** Hälften des Akzeptanz-Tests
> `test_v5_severity_depends_on_se_gate` sind damit je **einem** Mutanten zugeordnet (fest ERROR ⇒
> 2 failed, fest WARNING ⇒ 1 failed), also **nicht** halb geprüft.
> **Befund aus dem Mutantenlauf, benannt statt geglättet:** die erste Fassung des
> Provider-Tests war **stumm mutierbar** — ein Mutant, der die Dimension mit einer Registry
> ohne `agents`-Fähigkeit auswertet, blieb **grün (0 failed)**, weil ein Registry-Name, der die
> deklarierten Provider nicht trifft, ebenfalls übersprungen wird. Der Test prüfte also nur
> „liest die Datei nicht", nicht „überspringt die Dimension". Abhilfe **gemessen, nicht behauptet:**
> die Prämisse ist jetzt im selben Funktionsrumpf gepinnt
> (`compute_active_roles(root, config, collapsed) == set()` bei
> `collapsed = {Claude, Opencode, Gemini: {capabilities: []}}`, gemessene deklarierte Provider aus
> `.meta-config/project.yaml::ai-providers`) ⇒ derselbe Mutant jetzt **6 failed**. Ohne diese
> Prämisse wäre „nicht registriert"/Provider-Überspringung ein **nicht** abgedeckter Akzeptanzpunkt
> gewesen. **Registrierungs-Vorwegnahme:**
> V5 ist **nicht** registriert — `scripts/consistency-check.py` **0** Treffer für den Namen und
> das Modul, `docs.py::__all__` **25** Einträge ohne den Namen (der **einzige** Treffer dort ist ein
> vorbestehender Kommentar in der leeren W2-3…W2-7-Sektion), `consistency-check.py --json` ⇒
> **0** Findings mit `check == "docs.role_generation_parity"` (der **1** Error ist der
> vorbestehende, terminierte W2-6-Sollwert `docs/se-cascade/`). **Bewusst kein Test** auf
> „noch nicht registriert": ein dauerhafter Negativ-Assert wäre die Zustands-Assertion, die das
> W2-5-Review als Mangel markiert hat — der Nachweis ist diese Messung.
> **Write-Menge eingehalten (K46-Negativregel):** `docs_freshness.py`,
> `tests/test_doc_freshness.py`, `docs.py`, `consistency-check.py` und die Szenario-Fixtures sind
> **unberührt**; `docs.py` wurde nur gelesen. `git status --porcelain` zeigt **genau** drei
> Einträge: die Plan-Datei (`M`) und die zwei neuen Dateien (`??`). Kein `xfail`, kein `-k`, kein
> `|| true`, kein abgesenkter Sollwert, kein ausgelassener Gate-Zweig.
> **Vorbestehender roter Test, gemessen und W2-4 nicht zugerechnet (nicht angefasst, nicht
> geschwächt):** `tests/test_plan_ledger_writer.py::test_validate_plan_reaches_the_expected_
> overlap_verdict` pinnt **17** Hard-Overlap-Findings und ist mit **18** rot.
> **Korrektur der Ursachenangabe aus dem Stufe-1-Review:** die erste Fassung dieser Notiz
> schrieb, der Zähler sei „durch Rev. 0.7s Umbenennung des W2-4-**Titels**" von 17 auf 18
> gewandert. Das ist **sachlich falsch** und hiermit berichtigt. **Eigene Messung** über
> `git show <commit>:docs/plans/…`, jeweils mit dem Parser des Working Tree
> (`.tmp/w2-4r1/hist.py`):
>
> | Commit | Hard-Overlap-Zähler | Pin in `test_plan_ledger_writer.py` |
> |---|---|---|
> | `c3ed5c9f` | **14** | kein `len(errors)`-Pin |
> | `c0988e18` | **19** | kein `len(errors)`-Pin |
> | `4b5eaa94` | **18** | kein `len(errors)`-Pin |
> | `3b32c156` | **18** | kein `len(errors)`-Pin |
> | `3d8499ca` | **18** | **neu: `assert len(errors) == 17`** |
> | `31a0db55` (HEAD) | **18** | `== 17` |
> | Worktree | **18** | `== 17` |
>
> **Belegte Einordnung:** `4b5eaa94` („apply E-5..E-8, add W2-8 and W2-9 (rev 0.7)") ist
> tatsächlich der Commit, der den W2-4-Titel auf `docs_freshness_v5.py` umbenannt hat
> (`-… Rev. 0.6: docs_freshness.py …` / `+… Rev. 0.7 / E-7: eigenes Modul docs_freshness_v5.py …`)
> — er hat den Zähler von **19 auf 18** gesenkt, also **weg von** 17, **nicht auf** 18. Der Pin
> `== 17` wurde erst in **`3d8499ca`** eingeführt, wo der Ist-Wert bereits **18** war ⇒ **der
> Test war von Geburt an rot und war nie grün**; W2-4 hat den Zähler **nicht** bewegt (18
> vorher wie nachher).
> **Die Reparatur gehört nicht in W2-4** (andere Schreibmenge, und der Testkommentar
> untersagt das Schwächen des Pins): sie gehört in **W2-7** — das `docs.py`-`__all__`-Inkrement
> dort verschiebt den Zähler **erneut** — bzw. in einen **W2-9-Nachlauf**, der den Pin gegen den
> dann gültigen Ist-Wert neu setzt. **Einordnung als Befund, nicht als W2-4-Regression.**
> Die inhaltlichen Pins desselben Tests sind **grün**: `files_touched == ()` für **alle** Tasks,
> und `scripts/lib/consistency/docs.py` erscheint in **keinem** Overlap-Finding (die vom
> W2-9-Review gefürchtete Phantom-Write-Menge ist **nicht** entstanden). Zwei weitere rote Tests
> (`test_knowledge_engine.py::test_knowledge_roles_pass_schema_validation`,
> `test_sharkord_service_name_migration.py::…no_leftover_platform_namespace_placeholder`) haben
> **0** Referenzen auf `docs/plans`, `docs_freshness` oder `role_generation` und sind
> vorbestehend; die **35** Errors stammen alle aus `tests/browser/*` (Playwright-Socket, kein
> laufender Admin-Server) und sind umgebungsbedingt.

> **LEDGER-Stand 2026-09-28 — Fix-Runde 1 (Review-Iteration 1, Stufe 1 = `ACCEPTED_WITH_DEVIATIONS`,
> keine Blocker, alle Akzeptanzpunkte erfüllt).** Behoben sind die **drei
> Dokumentations-Deviations** DEV-1, DEV-2 und DEV-4; **kein** Code-Refactoring, **keine**
> Änderung an Verhalten, Severity-Regel, Vergleichsmenge oder Sollwerten. **DEV-3** (Schritt 4 als
> abgehakt markiert, Commit offen) ist **bewusst unverändert** — Werkzeug-Granularität des
> Ledger-Writers (Toggle pro Task, nicht pro Schritt); der Commit ist der Schritt des `git`-Agenten.
> **DEV-1 (überzeichneter Test-Docstring), behoben durch** Variante (b) „Lese-Negativtest
> ergänzen", **nicht** durch Abschwächen der Formulierung. **Vorher gemessen, dass die Lücke
> real war:** ein Mutant, der `config/ai-providers.yaml` via `load_providers_config` **lädt und
> weiterreicht**, blieb gegen den alten Testsatz **grün (Exit 0, 0 failed)** — der Review hatte
> recht. **Ursache, selbst gemessen:** der Lösch-Test kann das nicht sehen, weil
> `load_providers_config` fail-soft ist **und** seinen eingebauten Fallback mitbringt, der
> `agents` deklariert (gemessen: Fallback = `Claude`, `capabilities` enthält `agents`) — auf dem
> gesunden Baum und auf dem Baum ohne Datei ist die erzeugte Menge also **identisch**.
> **Der einzige unterscheidende Baumzustand** ist eine Registry, die **existiert und parst**,
> ohne `agents` zu deklarieren; genau den baut der neue Test, indem er die Datei in der Kopie
> **umschreibt** statt sie zu löschen. **Nachher gemessen: derselbe Mutant ⇒ 1 failed**, und der
> einzige rote Test ist der neue. **Zeilenanker NACH der Änderung**
> (`tests/test_doc_freshness_v5.py`): `test_v5_provider_dimension_is_skipped_not_evaluated`
> **`:279`** (Docstring jetzt: „What this test enforces, stated exactly" + Verweis auf den
> Geschwister-Test + Warnung, die Prämisse **nicht** wegzudeduplizieren),
> `test_v5_does_not_read_the_provider_registry` **`:326`** (**neu**), `AGENTS_CAPABILITY` im Import
> **`:69`**. **Mutantentabelle neu (8 Mutanten, alle Zahlen gemessen,
> `.tmp/w2-4/mutate.py`):** m1 **8** · m2 **3** · m2b **1** · m3 **8** · m4 **1** · m5 **8** ·
> m6 **7** · **m7 (Laden + Weiterreichen der Registry) 1** — vorher **0**. Basis-Lauf **9 passed**
> (vorher 8).
> **DEV-2 (Zweitbegründung nur im Bericht), am Code geprüft und damit ins Modul überführt.**
> **Bestätigt, nicht widerlegt:** `scripts/consistency-check.py` enthält genau **drei** `try`-Blöcke
> — `get_changed_files` (`:72`, Git-Subprozess), `get_new_files_vs_main` (`:94`, dito) und `_read`
> (`:220`, `read_text`) — und **keiner** davon umschließt einen Check-Aufruf. AST-gemessen:
> `run_checks` (`:140`–`:216`) und `main` (`:229`–`:276`) enthalten **0** `ast.Try`-Knoten;
> `main` ruft `run_checks` bei `:266` ungeschützt. **Verhaltensgemessen** an einer **Kopie** des
> Runners unter `.tmp/` (die Repository-Datei blieb unberührt): ein werfender Check ⇒ **Exit 1**,
> Traceback in stderr, **kein** JSON-Report, **0** Findings in stdout — der Verlust betrifft den
> **gesamten** Report, nicht nur diesen Check. Die Begründung **trägt** und steht jetzt im
> Modul-Docstring (`docs_freshness_v5.py`:30-34): Degradieren ist hier ein **Vertrag**, weil der
> Runner dem Check keine Blast-Radius-Isolierung anbietet, in die er degradieren könnte.
> **DEV-4 (falsche Ursachenangabe), korrigiert** — siehe die korrigierte Fassung weiter oben mit
> der **eigen** gemessenen Zähler-Historie (`c3ed5c9f` 14 → `c0988e18` 19 → `4b5eaa94` **18** →
> `3b32c156` 18 → `3d8499ca` 18 → `31a0db55` 18 → Worktree **18**) und der Einordnung **geboren
> rot** in `3d8499ca`; Reparatur **nicht** in W2-4, sondern **W2-7** (das `docs.py`-Inkrement
> verschiebt den Zähler erneut) bzw. **W2-9-Nachlauf**, und **nicht** durch Abschwächen des Pins.
> **Verifikation, alle Läufe mit umgeleiteter Ausgabe gemessen (Stand Fix-Runde 1):** `python3 -m
> pytest tests/test_doc_freshness_v5.py -q` ⇒ **9 passed**; `pytest
> tests/test_doc_freshness_v5.py tests/test_doc_freshness.py -q` ⇒ **34 passed**; `pytest
> tests/test_doc_facts.py -q` ⇒ **126 passed**; `python3 -m compileall -q scripts/lib` ⇒ **Exit 0**;
> `docs_freshness.py` **592 Z** und sha256 **identisch** mit dem Vorzustand
> (`3184e222b1b2c490cbac4ef4d5f318d57ecaf002ef89981292093c453e22b31d`) — **byte-identisch**;
> `wc -l` ⇒ `docs_freshness_v5.py` **126 Z** (< 600), `tests/test_doc_freshness_v5.py` **396 Z**;
> ruff **Defaults 0** und `--select I,UP,E,F,W` **0** über beide neuen Dateien. **V5 weiterhin
> nicht registriert:** `consistency-check.py` **0** Treffer, `docs.__all__` **25** Einträge ohne den
> Namen, `--json` ⇒ **0** Findings mit `check == "docs.role_generation_parity"`.
> **Write-Menge unverändert:** nur `docs_freshness_v5.py` (Docstring-Zeile), `test_doc_freshness_v5.py`
> (ein Test plus Docstring) und diese Plan-Notiz; `docs_freshness.py`,
> `tests/test_doc_freshness.py`, `docs.py`, `consistency-check.py` und die Szenario-Fixtures
> **unberührt**. Die **4** Checkboxen bleiben abgehakt, **kein** Commit, **keine** Git-Mutation.

> **LEDGER-Stand 2026-09-28 — Fix-Runde 2 (Review-Iteration 2, Stufe 2 = `ACCEPTED_WITH_DEVIATIONS`,
> Rating B+, 0 Blocker).** Zwei Findings behoben, beide Ein-Zeilen-Änderungen in W2-4s Write-Menge;
> **kein** Verhalten im Ist-Zustand, **kein** Commit.
> **N1 (Degradierung griff nur für `FactUnavailable`) — zuerst selbst reproduziert, dann behoben.**
> Gemessen auf einer Baumkopie mit **unparsbarer** `config/role-defaults.yaml`
> (`.tmp/w2-4f2/repro.py`): `compute_doc_facts` ⇒ 22 Facts, `check_docs_facts_fresh` ⇒ 1 Finding,
> `check_role_generation_parity` ⇒ **`SyncError`, ausbrechend** — der einzige Check der Familie, der
> den Runner abbricht (kein `try` pro Check, siehe DEV-2 oben), also genau der Ausgang, den die
> Modul-Doku als Vermeidungsgrund für die Degradierung anführt. **Ursache gemessen:** `io.py`:78
> (`_load_yaml_or_json`) wirft `SyncError` bei **Parse**-Fehlern, und `doc_facts` bildet laut eigener
> Doku nur `OSError`/`ValueError` auf `FactUnavailable` ab — „any other exception type propagates
> unchanged" (`_template_role_names`, `:608-611`); der Fail-Soft-Vertrag `:768-772` nennt eine
> unlesbare Quelle ausdrücklich *unavailable*.
> **Fix:** `_v5_generated_roles` fängt jetzt `(FactUnavailable, SyncError)`, Import `SyncError` aus
> `..io`. **Nachher gemessen:** korrupte Registry ⇒ **0** Findings statt Exception, `compute_active_roles`
> **unverändert** weiter werfend (der Dispatcher-Vertrag bleibt unangetastet — `doc_facts.py` ist W1-3s
> Eigentum, die im Review erwähnte Dispatcher-Erweiterung ist bewusst **nicht** genommen), intakter
> Baum ⇒ **1** Finding unverändert. **Begründung steht im Modul** (`_v5_generated_roles`-Docstring,
> `docs_freshness_v5.py`:87-110): `SyncError` ist derselbe Fall „Quelle unlesbar", nur eine Ebene
> tiefer gemeldet, und der breitere `except` ist auf **diesen einen** Aufruf gescoped.
> **Pflichttest:** `test_v5_corrupt_role_registry_degrades_instead_of_escaping`
> (`tests/test_doc_freshness_v5.py`:272) — pinnt zuerst die **Prämisse** (`pytest.raises(SyncError)`
> an `compute_active_roles` direkt, also *warum* die Ausnahme erwartet wird), dann `== []` für V5, und
> im selben Rumpf den nicht-leeren Ausgang auf intakter Kopie (Nicht-Vakuum). Der Geschwister-Test
> `:247` deckt den **anderen** Zweig (Quelle **fehlt** ⇒ `FactUnavailable`) ab; erst das Paar
> unterscheidet „degradiert" von „propagiert". Fixture-Konstante `CORRUPT_ROLE_DEFAULTS` **:96**
> (Tab-Indentation + offene Flow-Sequenz ⇒ Parse-Fehler, nicht fehlende Datei).
> **Mutant gemessen:** **m8** (nur `FactUnavailable` gefangen) ⇒ **1 failed**, und der einzige rote
> Test ist der neue. **Mutantentabelle neu, 9 Mutanten, alle Zahlen gemessen:** m1 **9** · m2 **3** ·
> m2b **1** · m3 **9** · m4 **2** · m5 **9** · m6 **8** · m7 **1** · **m8 1** — kein Mutant grün;
> Basis-Lauf **10 passed**. **Nebenbefund, offen benannt:** das m4-Mutationsziel war nach N1 veraltet
> (`MUTATION TARGET NOT FOUND`, also **ungemessen**, nicht grün) und wurde auf die neue
> `except`-Zeile umgehängt — m4 ist erst jetzt wieder eine gültige Messung.
> **N2 (Signaturreihenfolge), behoben, beide Begründungsbeine geprüft:** V5 schrieb
> `config: None | dict = None`; jetzt `config: dict | None = None` (`docs_freshness_v5.py`:120),
> wortgleich mit allen **5** Geschwister-Checks (`docs_freshness.py`:295 und `:579`,
> `docs_links.py`:555, `docs_wiki.py`:91, `docs_index.py`:180). **RUF036** (=
> `none-not-at-end-of-union`) **reproduziert:** an der Vor-Fix-Form **1 error**, an der Nach-Fix-Form
> **All checks passed** — die Regel-Begründung des Reviews trägt also **ebenso** wie die
> Geschwister-Konsistenz. Rein kosmetisch: der Test prüft Namen und Default, nicht die Annotation.
> **Verifikation, alle Läufe mit umgeleiteter Ausgabe gemessen (Stand Fix-Runde 2):** `pytest
> tests/test_doc_freshness_v5.py -q` ⇒ **10 passed**; `pytest tests/test_doc_freshness_v5.py
> tests/test_doc_freshness.py -q` ⇒ **35 passed**; `pytest tests/test_doc_facts.py -q` ⇒ **126
> passed**; `compileall -q scripts/lib` ⇒ **Exit 0**; ruff **Defaults 0** und
> `--select I,UP,E,F,W` **0** über beide Dateien; `docs_freshness.py` **592 Z**, sha256
> **identisch** (`3184e222…b31d`), **byte-identisch**; `wc -l` ⇒ `docs_freshness_v5.py` **144 Z**
> (**< 600** ✓, +18 gegenüber Fix-Runde 1 = N1-Docstring + Import), `tests/test_doc_freshness_v5.py`
> **442 Z**. **V5 weiterhin nicht registriert:** `consistency-check.py` **0** Treffer,
> `docs.__all__` **25** Einträge ohne den Namen, `--json` ⇒ **0** V5-Findings. **Write-Menge:**
> `doc_facts.py` (W1-3), `docs_freshness.py`, `docs.py`, `consistency-check.py`,
> `test_doc_facts.py`, `test_doc_freshness.py` **unberührt**; `docs.py` und `doc_facts.py` nur
> gelesen. **N3 und N4 bewusst nicht angefasst** und als offene Punkte an den Reviewer: **N3** die
> Message-Formatkopplung in `_roles()` (6 von 9 Tests) und **N4** die globale Severity-Regel
> gegenüber dem per-Rolle-Suggestion-Text (spec-konform, gehört an den Spec-Owner).

### W2-5: V6 `check_docs_facts_fresh` inkl. Sollwert-Vergleich — **Rev. 0.6: `docs_freshness.py`, PG-2a**

**Files:** Modify `scripts/lib/consistency/docs_freshness.py`, `tests/test_doc_freshness.py`,
`tests/test_doc_facts_expected.py` (**Rev. 0.6 / K20** — `docs_freshness.py` und
`tests/test_doc_freshness.py` neu; in Rev. 0.5: Modify `scripts/lib/consistency/docs.py`,
`tests/test_doc_facts_expected.py`)
**Interfaces:** Produces: `check_docs_facts_fresh(root, config=None) -> list[Finding]` mit
`kind ∈ {handedit, expected-mismatch, missing-in-expected}`; `missing-in-expected` = **WARNING**,
die anderen **ERROR**; in `docs_freshness.py`. Consumes: W1-5, **W2-0**.
**Agent:** developer · **Depends on:** **W2-0** (Rev. 0.6; vorher W2-4) · **parallel_group:**
**PG-2a** (Rev. 0.6; parallel mit **W2-3** und **W2-6**)
**Ziel-AK (AC):** **AC-36** (IC-23, R14) · **V-Check:** **V6**
**Akzeptanz:** `test_mismatch_is_reported` grün: manipulierter Sollwert ⇒ **genau ein** Finding
`severity=ERROR, kind="expected-mismatch"` **obwohl** der gerenderte Block exakt
`compute_doc_facts()` entspricht — der Nachweis, dass der Kreis `doc_facts → Renderer → V6`
gebrochen ist (R14).
**Verifikation (Rev. 0.6):** `python3 -m pytest tests/test_doc_facts_expected.py
tests/test_doc_freshness.py -q` → **0**; `wc -l scripts/lib/consistency/docs_freshness.py` →
**< 600**.
**Steps:**
- [x] 1: Test schreiben (fail).
- [x] 2: V6 mit beiden Vergleichsachsen implementieren.
- [x] 3: Tests grün beobachten.
- [x] 4: commit via `git`-Agent: `feat: add V6 freshness check with expected-value axis`.

> **LEDGER-Stand 2026-09-27 — W2-5 VOLLSTÄNDIG erledigt (Fortschrittsnotiz, keine Änderung der
> Task-Semantik).** Gelandet: `docs_freshness.py` 317 → **592 Z** (< 600),
> `test_doc_freshness.py` +337, `test_doc_facts_expected.py` +75/−6; 3 `kind`-Werte gemessen
> (`handedit` ERROR, `expected-mismatch` ERROR, `missing-in-expected` WARNING — Severity-Map als
> Datenstruktur gepinnt).
> **AC-36-Nachweis unabhängig gemessen:** nur der Sollwert manipuliert ⇒ **genau 1**
> `expected-mismatch` ERROR, `handedit`-Findings leer, gerenderte Doku **byte-identisch** ⇒ der
> Kreis `doc_facts → Renderer → V6` ist gebrochen (R14). V1-Regression: **14** Testfälle
> unverändert, der Diff berührt **null** V1-Zeilen. V6 **nicht** registriert ⇒ 0 Errors,
> 0 Warnings beigetragen.
> **Reviews:** `code-reviewer` (im **PG-2a**-Durchgang, keine Beanstandung an der Implementierung) ·
> `tester` **PASS** mit **1 WARNING** + 1 INFO, beide **kein Blocker**.
> **Offen aus dem Review (nicht W2-5, gehört W3/W4):** der Tripwire
> `assert "agent-meta:docs-begin" not in path.read_text(...)`
> (`tests/test_doc_facts_expected.py:287-290`) ist eine **Zustands-** statt Property-Assertion und
> bricht aus **falschem** Grund, sobald W3/W4 die Blöcke rendert. Commit `b73e9422`
> (`feat: add V6 freshness check with expected-value axis`, 3 Dateien, +688/−7).

### W2-6: V2 `check_docs_index_completeness` und V4-Umfassung — **Rev. 0.7 / E-5: V4 prüft den README-Index-Scope, `docs_index.py`, PG-2a (K54/K55)**

**Files:** Create `scripts/lib/consistency/docs_index.py`, `tests/test_doc_index.py`;
Modify `scripts/lib/consistency/docs_links.py` (**nur die V4-Umfassung** — V4 liegt seit
W2-0 in `docs_links.py`); (**Rev. 0.6 / K20** — neu; in Rev. 0.5: Modify
`scripts/lib/consistency/docs.py`, `tests/test_doc_facts.py`)
**Interfaces:** Produces: `check_docs_index_completeness(root, config=None) -> list[Finding]` in
`docs_index.py`; `check_readme_docs_index` wird **von der Forderung „alle nicht-Archiv-`docs/**.md`
sind in `README.md` verlinkt" umgestellt auf den **README-Index-Scope** bei **unveränderter**
Signatur, Check-ID (`docs.readme_index`), Severity (**ERROR**) und `file` (`README.md`) — der
IC-05-Pin ist damit **nicht** gebrochen. **Signatur ausdrücklich (K59 / RVW-7-01):**
`(root: Path) -> list[Finding]`, **einargumentig** — die Form `(root, config=None)` gehört den
**neun neuen** V-Checks, **nicht** diesem Altcheck (gemessen `docs_links.py:167`, Docstring
`:170-172`). **Mechanismus, verbindlich (E-5, K54):** V4 liest die
`##`-Überschrift, deren Text `Documentation Index` enthält, bis zur nächsten `##`-Überschrift
(heute `README.md:347`…`:381`); aus dieser Region werden die **deklarierten** `docs/`-Kategorien
extrahiert — **Extraktionsregel wortgleich (K64 / RVW-7-06):** „**jeder `docs/<kategorie>/`-Pfad,
der in der Region genannt wird**" (gemessen **7**: `docs/guides/`, `docs/howto/`, `docs/api/`,
`docs/ui/`, `docs/architecture/`, `docs/plans/`, `docs/se-cascade/`). **Die 7/6-Lesart ist
verbindlich und wird nicht offengelassen:** eine rein **überschriften**-basierte Extraktion ergäbe
**6**, weil `docs/architecture/` **ausschließlich** im Link `README.md:371` genannt wird und in
**keiner** `###`-Überschrift steht. Beide Lesarten liefern denselben Sollwert **1** — die
Stabilität des Sollwerts ist deshalb **kein** Argument gegen die Präzisierung. Je Kategorie gilt
**(a)** Existenz des Verzeichnisses und **(b)** mindestens **ein** `docs/<kategorie>/…`-**Link** in
der Region; **fehlt** die Überschrift ganz, ist das **ein** Finding (fail-closed, **nicht** eine
leere Liste). **Vorrangregel fail-closed vs. fail-soft (K65 / RVW-7-07, verbindlich, ersetzt die
beide gleich behandelnde Bedingung `docs_links.py:183`):** **Reihenfolge** — zuerst der
fail-soft-Guard: fehlt der **`docs/`-Verzeichnisbaum**, liefert V4 **`[]`** (ein Projekt ohne
`docs/`-Baum ist durch diese Prüfung nicht defekt, und „fehlende Kategorie" wäre dort gegenstandslos,
weil es keine Region und keine deklarierten Kategorien gibt). **Existiert `docs/`**, gilt die
fail-closed-Region-Prüfung: fehlt `README.md` **oder** die `Documentation Index`-Überschrift ⇒
**genau ein** Finding. **Ausdrücklich nicht mehr gefordert:**
die Verlinkung aller **205** nicht-Archiv-`docs/**.md` — das ist **V2s** Zuständigkeit
(`docs/INDEX.md`, 100 % generiert, tracked per OQ6). Consumes: **W2-0**, W1-8.
**Agent:** developer · **Depends on:** **W2-0** (Rev. 0.6; Rev. 0.5: W2-5) · **parallel_group:**
**PG-2a** (Rev. 0.6; parallel mit **W2-3** und **W2-5**)
**Ziel-AK (AC):** **AC-12** (IC-05) · **V-Check:** **V2**, **V4**
**Akzeptanz V2 (unverändert):** `test_v2_missing_page` grün: eine getrackte `docs/**/*.md` außerhalb `archive/`, die
in `docs/INDEX.md` fehlt ⇒ **ERROR**; `docs/INDEX.md` selbst und `archive/`-Pfade ⇒ **kein**
Finding.
**Akzeptanz V4, neu (Rev. 0.7 / E-5, K54/K55) — die V4-Tests werden NAMTLICH ERSETZT, nicht
angepasst (K61 / RVW-7-03, verbindlich).** **Befund, der diese Task-Zeile begründet:** W2-6 nannte
„drei V4-Tests"; im Working Tree pinnen **sieben** Tests die von E-5 **entfernte** Per-Seiten-
Semantik. Sie sind **kein** Ausgangszustand, den man „anpassen" könnte, sondern eine **falsche
Lesart**, die nicht in den neuen Scope darf — jede Übernahme der Assertion würde den
191/193-Blocker konservieren. **Ersetzungstabelle (verbindlich, `tests/test_doc_index.py`):**

| # | Alt-Test im Working Tree | Zustand heute | Ersatz-Test (neu) |
|---|---|---|---|
| R1 | `test_v4_keeps_signature_and_severity` | **vakuum-grün mit falscher Semantik** — die Signatur-Hälfte ist gültig, die Severity-Hälfte pinnt „1 unlink ⇒ 1 Finding" | **getrennt**: `test_v4_signature_is_one_argument_root_only` (behält den IC-05-Pin via `inspect.signature`, `== ["root"]` — **K59**) **plus** `test_v4_declared_category_without_link_is_one_error` (Severity ERROR, `file == README.md`, **1** Finding) |
| R2 | `test_v4_generalized_to_the_whole_docs_tree` | **vakuum-grün mit falscher Semantik** | `test_v4_declared_category_needs_a_link` — Akzeptanz (a) |
| R3 | `test_v4_api_subset_still_fires` | **vakuum-grün mit falscher Semantik** | `test_v4_declared_category_must_exist` — Akzeptanz (b) — **plus** `test_v4_declared_category_with_link_is_silent` |
| R4 | `test_v4_ignores_archived_pages` | **rot** | `test_v4_archived_pages_are_not_declared_categories` — `archive/`/`_archive/` sind **keine** deklarierten Kategorien |
| R5 | `test_v4_reports_each_page_once` | **rot** | `test_v4_reports_each_unrepresented_category_once` — der once-count läuft über **Kategorien**, nicht Seiten |
| R6 | `test_v4_finding_names_the_page_and_readme` | **rot** | `test_v4_finding_names_the_category_and_readme` — die Message nennt die **Kategorie**, nicht eine Seitepfad |
| R7 | `test_real_repo_pages_are_reported_only_by_v2_until_w3_6` | **rot** — `finding.message.split("'")[1]` parst die **Seiten**-Message | `test_real_repo_readme_index_has_exactly_one_unrepresented_category` — **beziehungsbasiert**, nicht zahlbasiert: `docs.readme_index` am echten Baum ist **nicht leer** (Sollwert 1, Kategorie `docs/se-cascade/`), und **kein** Finding nennt einen ungelinkten **Seiten**pfad |

**Warum diese sieben heute rot bzw. vakuum sind (der Grund für die Ersatzung statt Anpassung) —
präzisiert in Korrekturrunde 6 (K73 / RVW-7-03-Nachbesserung):** **6 der 7** Tests schreiben ein
Fixture `README_RELPATH, "# readme\n"` — **ohne** die
`##`-Überschrift `Documentation Index` (**R1, R2, R3, R4, R5, R6**; **gemessen** in
`tests/test_doc_index.py:280`, `:294`, `:309`, `:320`, `:336`, `:350`). Unter der fail-closed-Regel
feuert V4 in **diesen sechs** Fixtures ⇒ W2-6 **Schritt 3** („Tests grün beobachten") ist mit dem
alten Testsatz **unerreichbar**. **R7 gesondert, weil es die Begründung nicht trägt:**
`test_real_repo_pages_are_reported_only_by_v2_until_w3_6` (`tests/test_doc_index.py:394`) hat
**kein** Fixture, sondern liest den **echten** Baum (`REPO_ROOT`, `:404-408`) samt realer
`README.md`; er ist rot aus dem in R7 selbst genannten Grund — `finding.message.split("'")[1]`
parst die **Seiten**-Message, die nach E-5 die **Kategorie** nennt. **Die Klassifikation „alle sieben
heute rot bzw. vakuum" bleibt damit unverändert richtig**; korrigiert ist nur die
Begründungsmenge (**6 Fixtures statt 7**).
**Zwei Tests bleiben und werden erweitert, nicht ersetzt:** `test_v4_absent_docs_tree_is_fail_soft`
(bleibt gültig — der fail-soft-Guard feuert ohne `docs/`-Baum) wird um
`test_v4_docs_tree_without_index_section_is_one_finding` und
`test_v4_readme_missing_with_docs_tree_is_one_finding` ergänzt; das ist der **Test der
Vorrangregel** (K65). **Neu für die Extraktionsregel (K64):**
`test_v4_declares_seven_categories_including_architecture_from_link_only` pinnt die **7** und
benennt `docs/architecture/` als **link-, nicht überschrift-gewonnen**.
**Akzeptanz (a)-(c), unverändert im Wortlaut der Forderung:** (a) eine in der Index-Region
deklarierte Kategorie **ohne** Link ⇒ **genau ein** ERROR, `file == "README.md"`; (b) eine
deklarierte Kategorie ohne Verzeichnis ⇒ **ERROR**; (c) `README.md` **ohne** die Überschrift bei
vorhandenem `docs/` ⇒ **ein** ERROR (**nicht** `0`). **Negativnachweis gegen die alte Lesart
(verbindlich):** eine Fixture mit **zwei** nicht verlinkten Seiten **unterhalb** einer deklarierten
Kategorie (etwa `docs/guides/ungenutzt-a.md`, `docs/guides/ungenutzt-b.md`) ⇒ **kein** V4-Finding.
Dieser Negativnachweis ist das, was den 193-Blocker auflöst; ohne ihn wäre die Umfassung nicht
belegt. **Nicht-Vakuum-Nachweis (Plan-Standard K33, verbindlich und neu):** `tests/
test_doc_index.py` steht in **beide** Erfolgskriterien — (i) „alle V2- **und** V4-Tests grün" und
(ii) den Negativ-/Vorrangnachweis. Zusätzlich muss **derselbe** Negativtest im selben Funktionsrumpf
neben `== []` **auch** ein **nichtleeres** Ergebnis für eine deklarierte Kategorie ohne Link
assertieren; ein Check, der **gar nichts** zurückgibt, kann den `== []`-Teil nicht erfüllen. **Ohne
diesen zweiten Assert ist die Vorrangregel vakuum-prüfbar** und der Nachweis ungültig.
**Gemessener Erwartungswert am echten Baum:** **genau 1** Finding (Kategorie `docs/se-cascade/`,
deklariert `README.md:378`, ohne Link in der Region) ⇒ Termin **Follow-up
`F-DOCS-README-INDEX-SE-2026-09-27`, 2026-10-11**. **Grenze gegen V2 und V3 (K55), ausdrücklich:**
V2 ist **seiten**-genau und liest `docs/INDEX.md`; V3 prüft **Linkziele**; V4 prüft **nie** ein
Linkziel, sondern die **Repräsentation einer deklarierten Kategorie** — ein toter Link in der
Index-Region ist ein **V3**- und **kein** V4-Finding. **Ehrliche Grenze, die nicht kaschiert wird:**
mit dieser Umfassung hat V4 **keinen** Termin 0 in W0–W8; maßgeblich ist die **Deltasperre** der
Regel `W-VALIDATE-ROT`.
**Docstring-Pflicht (K68 / RVW-7-10, info, hiermit verbindlich):** die Docstrings von
`docs_links.py:8-10` (Modul) und `:168-177` (`check_readme_docs_index`) nennen weiter den
**Vor-E-5**-Scope („pre-W2 subset stays a real subset", „the parameter list stays `(root)`",
`check_readme_docs_index` `:100`). Sie sind auf den **E-5**-Scope umzuschreiben: **Was** V4 prüft
(deklarierte Kategorien), **was** es **nicht** mehr prüft (die Verlinkung aller `docs/**.md`),
und dass die **Signatur** `(root)` **unverändert** bleibt. **Hier wird kein Code geändert** — die
Korrektur ist **Pflicht dieser Task**, weil W2-6 als einziger Task `docs_links.py` schreibt.
**Spec-Treue:** §9.1 führt AC-12 auf W3; die **Implementierung** liegt hier (Fixture-Ebene, damit
**Rev. 0.6:** nicht `docs.py` von zwei parallelen Ketten geschrieben wird), der
**E2E-Nachweis gegen das reale `docs/INDEX.md`** in W3-6. **Die 193** sind **kein** AC, sondern
Follow-up `F-DOCS-README-INDEX-2026-09-27` (Spec §17.11.3); ihr Nachweis ist die **Issue-Liste +
der once-count außerhalb V4** (K60), **nicht** ein `docs.readme_index`-Zählwert.
**Verifikation (Rev. 0.7):** `python3 -m pytest tests/test_doc_index.py -q` → **0**;
`wc -l scripts/lib/consistency/docs_index.py scripts/lib/consistency/docs_links.py` → je **< 600**
(gemessen im Working Tree: **211** bzw. **404**).
**Steps:**
- [x] 1: Tests schreiben (fail) — V2 **und** die **sieben** namentlich zu ersetzenden V4-Tests
      aus der Ersetzungstabelle (R1…R7) **sowie** die drei Erweiterungen (fail-soft, Vorrang,
      Extraktionsregel) aus dieser Akzeptanz.
- [x] 2: V2 implementieren; V4 auf den README-Index-Scope umstellen (E-5) inkl. Negativnachweis,
      Extraktionsregel (7/6-Lesart), Vorrangregel (fail-soft-Guard vor fail-closed-Region-Prüfung)
      und Docstring-Korrektur (K68).
- [x] 3: Tests grün beobachten; **Zählwert** `docs.readme_index` am echten Baum beobachten
      (Erwartung **1**); **Nicht-Vakuum-Nachweis** aus der Akzeptanz mitlaufen lassen
      (beide Erfolgskriterien, K33/K61); Szenario-Asserts 50–56 **nicht** anfassen (NG-10).
- [x] 4: commit via `git`-Agent: `feat: add V2 index completeness and scope V4 to the README index`.

> **LEDGER-Stand 2026-09-28 — W2-6 VOLLSTÄNDIG umgesetzt (Fortschrittsnotiz, keine Änderung der
> Task-Semantik).** Abgehakt über den **maschinellen Ledger-Writer** (`--update-plan-ledger` gegen
> diesen Plan, `--task W2-6`): Dry-Run `tasks updated: W2-6`, `checkboxes would toggle: 4`,
> **Exit 0**, **keine** `unmatched`-Zeile; schreibender Lauf `tasks updated: W2-6`,
> `checkboxes toggled: 4`, **Exit 0**, **keine** `unmatched`-Zeile. Der Plan-Diff gegen die
> Vorher-Kopie ist **genau diese 4 Zeilen** (alle vier in `**Steps:**` dieses Blocks, Zeilen
> 3223–3232); Plan bleibt `status: APPROVED`, `revision: 0.7`, keine ID umnummeriert.
> **Ehrlich zur Checkbox 4:** sie ist auftragsgemäß mit abgehakt, der **Commit selbst ist nicht
> erfolgt** — W2-6 lief als **No-Commit**-Task; der Commit ist der Schritt des `git`-Agenten.
> **E-5-Umstellung von V4, gemessen:** `_v4_in_scope` und `_v4_unlinked_relpaths` (rekursiver
> Walk, Substring-Test, `archive/`-Ausnahme) sind **ersetzt** durch `_v4_index_region` (`:129`),
> `_v4_declared_categories` (`:159`), `_v4_declared_heading_categories` (`:187`),
> `_v4_linked_categories` (`:207`), `_v4_region_finding` (`:228`) und `_v4_category_finding`
> (`:242`); `check_readme_docs_index` sitzt jetzt bei `:265`. Die Konstanten `V4_PAGE_SUFFIX` und
> `V4_ARCHIVE_DIRNAMES` sind entfallen (Restbestand im Modul: **0** Treffer), ersetzt durch
> `V4_INDEX_HEADING`, `V4_CATEGORY_RE`, `V4_CATEGORY_LINK_RE`, `V4_LINK_TARGET_RE` und
> `V4_REGION_SUGGESTION` (`:366`–`:383`).
> **Signatur unangetastet (K59):** `inspect.signature` ⇒ `['root']`, **kein** `config`;
> Check-ID `docs.readme_index`, Severity **ERROR** und `file == README.md` unverändert.
> **Vorrangregel fail-soft → fail-closed (K65):** fehlt der `docs/`-Baum ⇒ `[]` **zuerst**;
> existiert `docs/`, gilt fehlt `README.md` **oder** die `Documentation Index`-Überschrift ⇒
> **genau ein** Finding. Gepinnt von `test_v4_absent_docs_tree_is_fail_soft` (beide Fixtures:
> einer **mit** Index-Sektion, einer **ohne** README und **ohne** `docs/`) **und**
> `test_v4_docs_tree_without_index_section_is_one_finding` **sowie**
> `test_v4_readme_missing_with_docs_tree_is_one_finding`.
> **Extraktionsregel (K64), gemessen am echten Baum:** Region `README.md:347` bis `:380`
> (34 Zeilen; die nächste `##`-Überschrift steht bei `:381`), **7** deklarierte Kategorien
> (`docs/guides/`, `docs/howto/`, `docs/api/`, `docs/ui/`, `docs/architecture/`, `docs/plans/`,
> `docs/se-cascade/`), davon **6** mit Link. **Nachweis der Link-Gewinnung:** eine rein
> überschriften-basierte Extraktion liefert **6** und **ohne** `docs/architecture/` — die Kategorie
> steht ausschließlich im Link `README.md:371` und in **keiner** `###`-Überschrift; gepinnt in
> `test_v4_declares_seven_categories_including_architecture_from_link_only`.
> **Negativ- und Nicht-Vakuum-Nachweis (K33), beide Erfolgskriterien:** in **einem**
> Funktionsrumpf — `test_v4_unlinked_pages_below_a_declared_category_are_not_findings`. Fixture A
> mit **zwei** nicht verlinkten Seiten (`docs/guides/ungenutzt-a.md`, `docs/guides/ungenutzt-b.md`)
> unterhalb einer deklarierten **und** verlinkten Kategorie ⇒ `== []`; Fixture B, dieselbe Regel
> plus eine deklarierte Kategorie **ohne** Link ⇒ **nichtleer**:
> `_categories(findings) == ["docs/se-cascade/"]`, Severity ERROR, und **weder** `ungenutzt-a.md`
> **noch** `ungenutzt-b.md` in der Message. **Vakuum-Gegenprobe (Mutanten, gemessen):** ein
> umgekehrter Guard lässt `test_v4_absent_docs_tree_is_fail_soft` rot (**1** failed); die
> wiederhergestellte Per-Seiten-Regel lässt **8** Tests rot, darunter den Negativtest; ein
> dauerhaft stiller Check lässt **9** Tests rot, darunter ebenfalls den Negativtest; die
> Überschriften-Extraktion (6-Lesart) lässt den Extraktionstest rot (**1** failed). Jeder
> Akzeptanzpunkt ist damit **nicht vakuum-prüfbar**. Moduldatei im Testmodul als Kommentar mit
> Abschnittsanker erhalten (R1…R7 ⇒ Ersatztests, K61).
> **Testmatrix (K61):** R1 `test_v4_keeps_signature_and_severity` ⇒ **getrennt** in
> `test_v4_signature_is_one_argument_root_only` + `test_v4_declared_category_without_link_is_one_error`;
> R2 ⇒ `test_v4_declared_category_needs_a_link`; R3 ⇒ `test_v4_declared_category_must_exist` +
> `test_v4_declared_category_with_link_is_silent`; R4 ⇒
> `test_v4_archived_pages_are_not_declared_categories`; R5 ⇒
> `test_v4_reports_each_unrepresented_category_once`; R6 ⇒
> `test_v4_finding_names_the_category_and_readme`; R7 ⇒
> `test_real_repo_readme_index_has_exactly_one_unrepresented_category` (beziehungsbasiert: der
> Sollwert wird aus deklarierten, verlinkten und existierenden Kategorien **abgeleitet**, nicht
> als Ziffer festgeschrieben). Dazu **3 Erweiterungen/Vervollständigungen**
> (`test_v4_absent_docs_tree_is_fail_soft` erweitert, zwei Vorrangtests) und **2 neue** Tests
> (Extraktionsregel, Negativ-/Nicht-Vakuum-Nachweis). Kein Alt-Test wurde adaptiert oder
> weichgezeichnet — kein `xfail`, kein `-k`-Filter.
> **Abgang des 191/193-Blockers, gemessen:** die Per-Seiten-Lesart lieferte am echten Baum
> **193** Findings (bei **207** nicht-Archiv-`docs/**/*.md`, davon **14** mit Substring-Treffer im
> README) — das ist der als „191/193" bezeichnete Blocker. Nach E-5 liefert `docs.readme_index`
> **genau 1** Finding: Kategorie `docs/se-cascade/`, deklariert `README.md:378`, ohne Link in der
> Region; `file == README.md`, Severity **ERROR`, und die Message nennt die **Kategorie**, keinen
> Seitenpfad. **Follow-up `F-DOCS-README-INDEX-SE-2026-09-27`, Termin 2026-10-11.** Die Forderung
> nach Verlinkung aller nicht-Archiv-`docs/**.md` ist damit **abgetreten** und **V2s** Zuständigkeit
> (`docs/INDEX.md`, 100 % generiert) — V2 meldet am echten Baum **207** unindizierte Seiten und ist
> bis W3-6 planmäßig rot.
> **Modulgrößen, gemessen (Stand Fix-Runde 1):** `docs_index.py` **211** Z (unverändert),
> `docs_links.py` **404 → 550 → 599** Z, beide **< 600**; `tests/test_doc_index.py` **413 → 835** Z mit
> **34** statt **24** Tests (die 600er-Grenze gilt nur für `scripts/lib/`). **Budget gemeldet, nicht
> verschwiegen:** `docs_links.py` stand nach den vier Fixes zunächst bei **623** Z. Der Überschuss
> wurde durch **Wortlautstraffung der eigenen Docstrings** abgebaut (inhaltlich vollständig: K68-
> Umfang, K64-7/6-Begründung, D2-Gegenanforderung, D1, D3, D4, Vorrangregel alle erhalten), nicht
> durch Weglassen — Endstand **599** Z mit **1** Zeile Reserve.
> **Docstring-Pflicht (K68) erfüllt:** Modul- und Funktions-Docstring in `docs_links.py` nennen
> jetzt **was** V4 prüft (deklarierte Kategorien), **was es nicht mehr** prüft (die Verlinkung aller
> `docs/**.md`) und dass die **Signatur** `(root)` unverändert bleibt; die Vor-E-5-Formulierungen
> („pre-W2 subset stays a real subset", „the parameter list stays `(root)`") sind entfernt.
> **Verifikation, alle Läufe gemessen (Stand Fix-Runde 1):** `python3 -m pytest
> tests/test_doc_index.py -q` ⇒ **34 passed, Exit 0**; `wc -l` ⇒ **211** / **599** (je < 600);
> `python3 -m pytest tests/test_doc_facts.py -q` ⇒ **126 passed, Exit 0** (V1/V3 ohne Regression);
> `python3 -m compileall -q scripts/lib` ⇒ **Exit 0**. **V2 weiterhin nicht registriert:**
> `check_docs_index_completeness` kommt in `consistency-check.py` **nicht** vor, steht **nicht** in
> `docs.__all__`, und das Attribut existiert am Facade **nicht** ⇒ **0** Findings im `--json`-Report.
> **Pin geprüft:** `files_touched` für W2-6 ist `()` — auch nach dieser Notiz, weil im Fließtext
> bewusst **keine** der Doppelpunktform des Datei-Feldes (die N3 aus dem W2-9-Review als Phantom-
> Write-Menge auslöst) mit einem Pfad steht. **Erster Versuch war rot** und wird hier offen
> benannt: der wörtliche Hinweis auf jene Form im vorigen Absatz hat das Muster selbst getriggert
> (`files_touched` ⇒ `('/',)`) und ist deshalb umformuliert, nicht weggelassen.
> **Szenario-Asserts 50–56 (NG-10) unangetastet**, `docs.py` (Negativregel K46) **nicht** geschrieben.
> **Volltest-Baseline nur als Zählwert**, kein Kriterium.
>
> **LEDGER-Stand 2026-09-28 — Fix-Runde 1 (Review-Iteration 1, Stufe 1 = `ACCEPTED_WITH_DEVIATIONS`,
> keine Blocker, alle 10 Akzeptanzpunkte erfüllt).** Die **E-5-Umfassung selbst bleibt unangetastet**;
> behoben sind vier Härtungslücken, alle in `docs_links.py`, jede mit einem Test, der ohne den Fix
> rot ist. **Zeilenanker NACH der Änderung** (`docs_links.py`, 599 Z): `_v4_index_region` `:128`,
> `_v4_is_url_path` `:154`, `_v4_declared_categories` `:171`, `_v4_declared_heading_categories` `:195`,
> `_v4_category_of_target` `:217` (**neu**), `_v4_is_image_target` `:231` (**neu**),
> `_v4_linked_categories` `:250`, `_v4_region_finding` `:275`, `_v4_category_finding` `:289`,
> `check_readme_docs_index` `:312`; Konstanten `:405`–`:433` (`V4_REFERENCE_DEF_RE` **neu** `:421`,
> `V4_TOKEN_BOUNDARIES` **neu** `:417`, `V4_READ_ERRORS` **neu** `:425`). Entfallen: `V4_PAGE_SUFFIX`
> (tote Konstante nach D3, 0 Restbestand).
> **Fix-Matrix, alle Zahlen gemessen:** **D1** (Referenzdefinition galt nicht als Link ⇒ falscher
> ERROR) — `docs_links.py:250`/`_v4_linked_categories` sammelt jetzt **beide** Markdown-Linkformen;
> Test `test_v4_reference_definition_counts_as_a_link`; **Mutant M-D1** (RefDef-Schleife entfernt) ⇒
> **1 failed** von 34. **D2** (keine linke Grenze ⇒ `https://x.invalid/docs/spam/a.md` deklarierte
> Kategorie `spam`) — `docs_links.py:154`/`_v4_is_url_path` + Filter in `:171` und `:195`; Test
> `test_v4_url_prefix_does_not_declare_a_category`; **Mutant M-D2** (Filter entfernt) ⇒ **1 failed**.
> **D3** (Bildtarget erfüllte (b)) — `docs_links.py:231`/`_v4_is_image_target`; Test
> `test_v4_image_target_does_not_represent_a_category`; **Mutant M-D3** ⇒ **1 failed**.
> **D4** (`UnicodeDecodeError` flog aus der Funktion) — `docs_links.py:425`/`V4_READ_ERRORS =
> (OSError, UnicodeDecodeError)`, gefangen in `check_readme_docs_index:344`; Docstring `:350-357` auf
> die **messbare** Realität („missing, not a file, not decodable as UTF-8" — genau diese drei)
> gespitzt statt die Zusage hochgedreht; Test `test_v4_undecodable_readme_is_one_finding`;
> **Mutant M-D4** (zurück auf `except OSError`) ⇒ **1 failed**. Module nach allen Mutanten
> byte-identisch restauriert (gemessen).
> **D2 ausdrücklich gegen die Gegenanforderung geprüft:** Die **6** Überschrift-Kategorien des
> realen README stammen aus **Code-Spans** (`` `docs/guides/` ``). Der Filter schließt ausschließlich
> **URL-Präfixe** (`://` + Host im Token vor dem Match) aus, kein `` ` ``-/`(`/Leerzeichen-gebundenes
> Muster ⇒ die 7 bleiben **7**. Am echten Baum gemessen: Lesart 1 (Region) **7** mit
> `docs/architecture/`, Lesart 2 (nur Überschriften) **6** ohne sie — der K64-Pin
> `…seven_categories_including_architecture_from_link_only` bleibt grün.
> **D3 in engerer, plan-konformer Form umgesetzt — Spannung Plan gegen Review, hier offengelegt:**
> Die wörtliche Vorgabe „(b) nur über `.md`-Linkziele" ist **an diesem Baum nicht erfüllbar, ohne den
> Plan-Wortlaut zu verletzen.** Gemessen: `docs/ui/` wird real durch `](docs/ui/agent-graph.html)`
> (`README.md:369`) und `](docs/ui/admin-ui.html)` (`:370`) repräsentiert — **zwei `.html`-Links, kein
> Bild**. Eine `.md`-Einschränkung meldet damit eine Kategorie, die das README **nachweislich
> verlinkt**, und verschiebt den **Sollwert von 1 auf 2** (`docs/ui/` zusätzlich zu `docs/se-cascade/`),
> was dem im Plan festgeschriebenen Erwartungswert **„genau 1"** widerspricht. Umgesetzt wurde daher
> die Regel, die den *konkreten* D3-Defekt behebt, ohne den Plan zu brechen: **struktural** — ein
> **eingebettetes Bild** (`![…](…)`) ist kein Indexeintrag und erfüllt (b) nicht; ein ganz normaler
> Link auf eine `.html`-Dokumentation zählt. `V4_PAGE_SUFFIX` wurde deshalb als tote Konstante
> entfernt statt als Suffixregel eingeführt. **Gemessener Reststand: Sollwert unverändert `1`**
> (Kategorie `docs/se-cascade/`, `file == README.md`, Severity **ERROR**), K64 unberührt.
> **Bekannte Lücke, benannt statt versteckt:** die Referenzform eines Bildes (``![alt][ref]``) wird
> nicht erkannt — ihre Zeile ``[ref]: target`` trägt kein ``!`` —, ein solches Ziel zählt also weiter.
> Der Reviewer bewertet die frühere Begründung mit dem Zeilenbudget als **nicht tragfähig**; der Punkt
> ist damit **Folgetask**, nicht Rundenziel — siehe den Absatz „Offener Auftrag" am Ende dieser Notiz.
> **D3 — Entscheidung des Reviewers, hiermit dokumentarisch übernommen (kein Code-Änderungsbedarf):**
> die `.md`-Zusatzbedingung stammte aus dem **Review-Briefing**, ist **kein** Plan-Wortlaut (Plan:
> „mindestens ein `docs/<kategorie>/…`-**Link**"), und die umgesetzte **strukturelle** Regel — Bild ≠
> Indexeintrag, `.html`-Link zählt — ist damit die **wortlautgetreue** Lesart. Die obige
> Messbegründung (`docs/ui/`, Sollwert 1 → 2) bleibt als Begründung des Regelwegs stehen.
> **D6 — Zitat korrigiert.** Die vorige Notiz zitierte „`ruff check` über alle 3 Dateien ⇒ All checks
> passed"; das galt **nur für die ruff-Defaults**. Selbst gemessen mit der maßgeblichen Invocation
> `python3 -m ruff check --output-format=concise --select I,UP,E,F,W` über dieselben drei Dateien:
> **rc 1**, **24** Findings — `docs_links.py` **17** (E501, E701, W293; **0** davon in der
> V4-Region, alle in den Altchecks), `docs_index.py` **3** (E501, unverändert), `test_doc_index.py`
> **4** (alle E501, alle vorbestehend). Delta `docs_links.py` gegen **HEAD** (`git show
> HEAD:scripts/lib/consistency/docs_links.py`, unveränderter Working Tree): **22 → 17 = −5**. Die
> Defaults-Invocation bleibt separat zitierbar: `python3 -m ruff check <3 Dateien>` ⇒ **rc 0, All
> checks passed**. **Eigene E501 in der V4-Region: 0**; in den neuen Tests: **0**.
> **F-6 — Nebenangabe der vorigen Runde präzisiert.** Die damalige Formulierung „`test_doc_index.py`
> **5** (alle E501, alle vorbestehend)" war um **genau eine** Zeile falsch: `:108`, der Docstring des
> **D1-Runden**-Helpers `_declares_with_refdef`, war eine **eigene neue** Zeile (89 Zeichen) und
> **nicht** vorbestehend; sie ist in dieser Runde behoben, die verbleibenden **4** sind vorbestehend
> (Modul-Docstring `:1`, zwei V2-Tests, Registrierungs-Pin). Ebenso präzisiert: „Eigene E501 in den
> neuen Tests: **0**" galt nur ab dem Stand dieser Runde — in der Vor-Runde waren es **4** (davon die
> eine genannte), alle inzwischen behoben. Die **Gesamtzahlen** (24/17/3/4, Delta −5) sind die
> maßgeblichen, selbst gemessen.
> **Nicht behoben, bewusst verschoben (nur hier vermerkt, die Dateien bleiben unangetastet):**
> **(D5)** `tests/test_doc_facts.py:2229-2234` baut weiterhin das Vor-E-5-Fixture
> (``docs/api/orphan.md`` plus README **ohne** Index-Überschrift) und ist nach E-5 grün **über den
> fail-closed-Pfad**, nicht über den Orphan-Pfad; sein Docstring `:2193-2200` überzeichnet damit, was
> er belegt. **Verschobener Auftrag an W2-7** (Datei ist W2-7s Write-Menge) — Fixture auf den
> Kategorien-Scope umstellen oder den Docstring an die belegte Aussage angleichen.
> **(D7)** `files_touched(W2-6) == ()`, weil die `Files:`-Zeile des Plans die Doppelpunktform des
> Datei-Feldes nicht benutzt und der Overlap-Check für diesen **3-Dateien**-Task deshalb keine
> Write-Menge sieht. **Planeigenschaft, vom Plan-Owner zu klären** — hier nur gemeldet, nicht
> angefasst.
>
> **LEDGER-Stand 2026-09-28 — Fix-Runde 2 (Review-Iteration 2, Stufe 2 = `ACCEPTED_WITH_DEVIATIONS`,
> keine Blocker).** Behoben: **F-1** (O(n²)), **F-2**, **F-3**, **F-4**, **F-5**, **F-6**. Die
> **E-5-Umfassung** selbst und der **Sollwert 1** bleiben unangetastet. **Anker NACH der Änderung**
> (`docs_links.py`, **599** Z): `_v4_index_region` `:126`, `_v4_token_starts` `:145` (**neu**),
> `_v4_is_remote_path` `:159` (ersetzt `_v4_is_url_path`), `_v4_categories_in` `:183` (**neu**),
> `_v4_declared_categories` `:200`, `_v4_declared_heading_categories` `:215`,
> `_v4_category_of_target` `:236`, `_v4_is_image_target` `:251`, `_v4_linked_categories` `:270`,
> `_v4_finding` `:295` (**neu**), `_v4_region_finding` `:301`, `_v4_category_finding` `:308`,
> `check_readme_docs_index` `:321`; V4-Konstantenblock **`:426`**–`:445` (**F-5** hinter die
> V3-Regexe verschoben, eigener Abschnitt): `V4_BOUNDARY_RE` `:434` (**neu**),
> `V4_REMOTE_PREFIX_RE` `:435` (**neu**), `V4_LINK_TARGET_RE` `:439` (**Alias**), `V4_REFERENCE_DEF_RE`
> `:440` (**Alias + `MULTILINE`**), `V4_CATEGORY_LINK_RE` `:433` (aus `V4_CATEGORY_RE` abgeleitet).
> **F-1 (MEDIUM) — O(n²) aus D2 beseitigt.** `docs_links.py:145`/`_v4_token_starts` baut den
> Boundary-Index **einmal** pro Text (`V4_BOUNDARY_RE`, ein `finditer` über die Zeichenklasse), `:159`
> macht **ein** `bisect` pro Match ⇒ O(n + m log n) statt 9 Rückwärtsscansen pro Match.
> **Messung, identischer Aufbau (263 KB / 533 KB / 1,08 MB, plain `finditer` als Referenz):**
> vorher **116,5 / 488,4 / 2 105,7 ms** (Faktor **75,6 / 161,8 / 345,3**), nachher **13,3 / 28,0 /
> 60,8 ms** (Faktor **9,1 / 8,8 / 9,3**) — **8,8x / 17,4x / 34,6x** schneller, Wachstum **linear**
> statt quadratisch. *Ehrliche Einordnung:* die Review-Zahlen 497,8 / 1 910,2 / 7 959,5 ms stammen
> aus einem **dichteren** Generator bei gleichen Größen; absolut sind sie deshalb nicht deckungsgleich,
> die **Form** (Faktor explodiert mit n) ist dieselbe, und die Verbesserung ist auf **identischem
> Input** in beiden Spalten gemessen.
> **F-2 — der ungetestete Foil-Aufruf ist getestet, nicht gestrichen.** Der Aufruf bleibt, weil die
> **korrekte** Semantik lautet: die Folie soll sich ausschließlich über die **Überschrift** von der
> vollen Lesart unterscheiden, nie über die Frage, was eine Nennung ist. Test
> `test_v4_url_in_a_heading_is_filtered_in_both_readings` (`:705`), Mutant M-D2b (Filter nur aus dem
> Foil entfernt) ⇒ **1 failed** von 38; vorher überlebte derselbe Mutant mit **34 passed**.
> **F-3 — Grammatik statt Allowlist.** `docs_links.py:435`/`V4_REMOTE_PREFIX_RE` erkennt
> URI-Schema, **protokollrelatives `//`** und **Host-Marker `www.`** (`\A` verankert, kein Whitespace
> dazwischen), nach dem Muster von `V3_SCHEME_RE` — keine zweite Liste. Deckt `//cdn.invalid/…`,
> `www.example.com/…`, `mailto:docs/spam/a` und `](//x.invalid/…)` ab. Test
> `test_v4_scheme_and_host_prefixes_do_not_declare_a_category` (`:676`), Mutant (Grammatik zurück auf
> nur `://`) ⇒ **1 failed**. **K64 unberührt:** 7 Kategorien, davon 6 aus **Code-Spans**; eine Folge
> ist akzeptiert statt wegdefiniert: `siehe auch:docs/guides/` liest sich als Schema und fällt weg,
> genau wie V3 denselben Token behandelt.
> **F-4 (DRY) — Aliase statt Kopien.** `V4_LINK_TARGET_RE = V3_INLINE_LINK_RE`,
> `V4_REFERENCE_DEF_RE = re.compile(V3_REFERENCE_DEF_RE.pattern, re.MULTILINE)` (V4 braucht
> `MULTILINE`, weil es eine ganze Region scannt, V3 zeilenweise) — zeichengleich verifiziert, vor der
> Änderung **3** Kopien in `scripts/lib/` (inkl. `_V2_LINK_TARGET_RE` in `docs_index.py:73`, die
> **unangetastet** bleibt: Datei nicht in dieser Write-Menge). Test
> `test_v4_link_grammars_are_shared_with_v3` (`:777`), Mutant (Kopie in der Prä-F-4-Form) ⇒
> **1 failed**. **Wichtig, offen benannt:** ein reiner `is`-Vergleich hätte den Mutanten
> **überleben** lassen, weil `re.compile` ein **gecachtes** Objekt zurückgibt; tragend ist deshalb die
> Quelltext-Invariante „jede Grammatik genau einmal im Modul geschrieben".
> **F-5 — umgesetzt, weil F-4 es voraussetzte:** der V4-Konstantenblock (`:426`–`:445`) steht jetzt
> **hinter** den V3-Regexen in einem eigenen Abschnitt; vorher zerriss er den V3-Block. Zeilenneutral
> (−1), die 600er-Grenze ist **nicht** aufgeweicht.
> **Zeilenreserve gemeldet, nicht kaschiert:** nach F-1…F-4 stand das Modul zunächst bei **636** Z.
> Der Überschuss wurde abgebaut durch **strukturelle** Verdichtung (eine `_v4_finding`-Fabrik statt
> zwei, gemeinsame `_v4_categories_in` statt doppelter Schleife, `V4_REGION_SUGGESTION` ohne
> Klammer-Ausdruck) und **Wortlautstraffung der eigenen Docstrings** — inhaltlich vollständig, kein
> Anspruch entfernt. **Endstand 599 Z bei 599/600, also 1 Zeile Reserve**; genau diese Reserve ist der
> Grund, warum F-5 als Folgetask-Vorbedingung geführt und nicht erneut aufgegriffen wird.
> **Verifikation (alle Läufe gemessen):** `pytest tests/test_doc_index.py -q` ⇒ **38 passed, rc 0**
> (34 Alt + 4 neu); `pytest tests/test_doc_facts.py -q` ⇒ **126 passed, rc 0**;
> `compileall -q scripts/lib` ⇒ **rc 0**; `docs_index.py` **211** Z unverändert; V3-Altchecks
> `check_internal_links`/`check_sync_cli_docs`/`check_ui_help_mappings` **unverändert**. Mutanten
> M-F1…M-F4: je **1 failed von 38**, Modul danach **byte-identisch restauriert** (gemessen).
> **Sollwert und K64 am echten Baum:** `docs.readme_index` **1** (Kategorie `docs/se-cascade/`,
> `file == README.md`, Severity **ERROR**), Lesart 1 **7** inkl. `docs/architecture/`, Lesart 2 **6**
> ohne sie — unverändert.
> **Offener Auftrag (Plan-Owner, hier nur eingetragen, kein Task angelegt): V4 aus `docs_links.py`
> herauslösen** (Spec §4.1). Nimmt in **einem** Zug in sich auf: die nicht erkannte Bildform
> ``![alt][ref]``, die **1-Zeilen-Reserve** unter K18, den verbleibenden Teil von **F-5**
> (Eigene-Modul-Abschnitt statt Block-Umzug) und die Kopplung, die F-1 und F-2 überhaupt erst nötig
> gemacht hat.

### W2-8: Die zwei roten Volltests entkoppeln (Rev. 0.7, E-6, K56) — **eigener Task, Position unmittelbar vor W2-7**

**Files:** Modify `tests/test_knowledge_engine.py`,
Modify `tests/test_sharkord_service_name_migration.py`. **Ausdrücklich nicht in `Files:`** — kein
Produktionscode, kein `sync.py`, kein `scripts/lib/consistency/*`, kein `plan_ledger.py`: die
beiden Tests hängen an einer **Fremdgröße**, nicht an einem Defekt im Produktivcode, und die
Behebung gehört in die Tests.
**Interfaces:** Produces: zwei Tests, deren Aussage **auf ihren eigenen Gegenstand** begrenzt ist.
`test_knowledge_roles_pass_schema_validation` prüft weiterhin, dass die Knowledge-Rollen die
Config-Schema-Validierung bestehen — aber **nicht** mehr über den repo-globalen
`sync.py --validate`-Exit-Code des **Host-Repos**; `test_generated_docker_agent_has_no_leftover_platform_namespace_placeholder`
prüft weiterhin, dass im generierten `docker.md` kein `{{platform.sharkord.*}}`-Platzhalter steht —
der `--validate`-Schritt (`:44-48`) wird entkoppelt oder auf den **eigenen** Fixture-Scope
zurückgeführt. Consumes: W2-4 (Phase-B-Reihenfolge), **E-5** (die V4-Umfassung, die den
193-Blocker beseitigt — **K60**, nicht 191), Regel `W-VALIDATE-ROT`.
**Agent:** senior-developer · **Depends on:** **W2-4** (**Sequenzierungs-Kante**: W2-8 ist der
**letzte** Task vor W2-7, damit sein Nachweis die **vollständige** W2-Doku-Check-Landschaft prüft und
nicht einen Zwischenstand; siehe „Warum unmittelbar vor W2-7") · **parallel_group:** —
(**sequenziell**)
**Ziel-AK (AC):** **AC-11** und **AC-13** (Nachweis der Wohlgeformtheit: „keine Regression",
AC-13 Exit-Code-Vertrag unverändert) — **kein** neuer AC. **Warum kein neuer AC:** es entsteht
**keine** neue beobachtbare Anforderung an das Vorhaben, sondern die Wiederherstellung der
**Wohlgeformtheit** zweier bereits vorhandener Tests. · **V-Check:** — (Querschnitts-Task ohne
eigenen V-Check, Muster W2-0/W2-9)
**Akzeptanz:**
(a) `python3 -m pytest tests/test_knowledge_engine.py
tests/test_sharkord_service_name_migration.py -q` → **0**;
(b) **Mechanismus, verbindlich, und an W2-8s Position geprüft (K63 / RVW-7-05):** die beiden
Tests dürfen **nicht** mehr `assert result.returncode == 0` gegen einen `sync.py --validate`-Subprocess
**im Host-Repo** stellen. **Anwendbar — und nur diese zwei:**
**(i) Prüfung des eigenen Gegenstands** (Schema-Validierung der Knowledge-Rollen bzw.
Platzhalterfreiheit der generierten `docker.md`) **ohne** den globalen Exit-Code — anwendbar,
weil sie **keinerlei** Vorbedingung aus dem Doku-Check-Framework braucht (Position: **W2-8
Schritt 2**, erster Weg);
**(iii) eine scope-gefilterte Auswertung des `--json`-Reports.** **Das Werkzeug ist festgeschrieben
und ausdrücklich benannt (K63):** `--json` gibt **der Runner** `scripts/consistency-check.py`
(`:244-247`), **nicht** `sync.py` — `sync.py` kennt **kein** `--json`, nur `--validate`,
`--validate-se`, `--validate-spec-plan` (gemessen `sync.py:153`/`:158`/`:166`). **Konkreter
Aufruf, festsgeschrieben:**
`python3 scripts/consistency-check.py --json --root <eigenes Fixture-Projekt>` ⇒ JSON-Report,
aus dem **nur** die Dateien des jeweiligen Tests ausgewertet werden. **Grenze, die benannt wird
(behebt die Unschärfe des Findings, ohne sie zu leugnen):** `--root` leitet **nicht** alle Checks
um — die drei Altchecks inklusive V4 ruft der Runner **unbedingt** mit `_AGENT_META_ROOT`
(`consistency-check.py:40`, Aufrufe `:199-201`, `root` erst `:257`). `--root` verschiebt also den
**Teil** der Prüfungen, der `root` benutzt; die Altchecks laufen weiter gegen das Host-Repo. (iii)
ist deshalb **nur** zulässig in der Form „Auswertung **ausschließlich** der Dateien des Tests" —
ein **globaler** Zählwert über denselben Aufruf wäre dasselbe Fremdmaß wie vorher. **(ii) ist an
W2-8s Position NICHT anwendbar und wird aus dieser Liste gestrichen (K63):** der Mechanismus
verlässt sich auf das **Common-Gate** (`docs-consolidation.enabled: false` ⇒ Doku-Checks No-op,
IC-05), das erst in **W2-7** entsteht — W2-8 läuft **unmittelbar davor**; zusätzlich nimmt V4
**kein** `config` (`docs_links.py:167`, einargumentig — K59), sodass die Key-Wirkung im
Altcheck-Pfad gar nicht ankäme; und Akzeptanz (d) schließt jeden Eingriff in `scripts/lib/consistency/*`
aus. **Als spätere Option bleibt (ii) ausdrücklich erhalten** — für Tasks **nach** W2-7, die dann
echten Fixture-Scope **mit** Gate nutzen können; sie ist hier nur **nicht** erreichbar.
**Unzulässig:** ein pauschales `|| True`, ein `xfail`, ein
`-k`-Filter, ein Herabsetzen des Sollwerts, oder ein Eingriff in `sync.py`;
(c) **Härteste Probe, verbindlich:** beide Tests bleiben **auch dann** grün, wenn die
Doku-Checks des Host-Repos ERROR liefern — nachgewiesen entweder durch **(i)/(iii)** oder durch einen
**negativen** Test, der einen `docs/`-ERROR injiziert und das Weiterbestehen der Assertion prüft;
(d) **Keine** Änderung an Produktivcode: `git diff --name-only` dieser Task enthält **ausschließlich**
die zwei Testdateien;
(e) **Volltest-Bestand bleibt rot und sichtbar:** die **2** roten Tests aus dem Ausgangslage werden
**grün**, **ohne** dass ein weiterer Test rot wird — `python3 -m pytest tests/ -q` ⇒ **genau 0**
rote Tests (Baseline: genau **2**).
**Verifikation:** `python3 -m pytest tests/test_knowledge_engine.py
tests/test_sharkord_service_name_migration.py -q` → **0**; `python3 -m pytest tests/ -q` → **0**
rote Tests (Zählwert, kein Exit-Code-Kriterium, RVW-12); `git diff --name-only` → **nur** die zwei
`Files:`-Einträge.
**Warum ein eigener Task und nicht eine Zeile in W2-6 (E-6, begründet):** W2-6 schreibt
`docs_index.py`, `tests/test_doc_index.py` und `docs_links.py` und läuft in **PG2a** — ein Eingriff
in `tests/test_knowledge_engine.py` würde W2-6 einen **fremden** Write-Set geben und die
Parallelität brechen, für die K20 den Split gemacht hat. **Warum unmittelbar vor W2-7 (und nicht
früher):** ab W2-7 sind **V2, V3 und V6** als ERROR registriert — und **V4** ist bereits registriert
und trägt **1** ERROR (Kategorie `docs/se-cascade/`, **K67**); `sync.py --validate` ist dann
**planmäßig** rot (Spec §10, `W-VALIDATE-ROT`). W2-8 läuft deshalb **als letzter vor W2-7**, damit
sein Nachweis den Zustand **kurz vor** der Registrierung prüft und die Entkopplung **vor** dem
Wellenabschluss belegt ist — nicht erst, wenn die Welle schon rot ist. **Diese Task-Zeile ist für
sich genommen kein Welle-Gate** (RVW-3): das Wellen-Gate **W2** bleibt an **W2-7** gebunden.
**Steps:**
- [x] 1: Reproduktion: beide Tests laufen rot nach (die Volltest-Baseline: **genau 2** rote Tests,
      beide Stellen `:228` bzw. `:48`) und der Befund wird im Task-Notiz-Format festgehalten.
- [x] 2: Beide Tests entkoppeln — **ausschließlich** nach den Mechanismen **(i)/(iii)** der
      Akzeptanz (b) — **(ii) ist an dieser Position nicht anwendbar (K63)** und wird **nicht**
      gewählt; **kein** Eingriff in Produktivcode, `sync.py` oder Szenario-Fixtures (NG-10).
- [x] 3: Nachweise (a), (c), (d), (e) ausführen; insbesondere die **negative** Probe (c) und der
      Volltest-Lauf mit **0** roten Tests; Ergebnis in den Review-Protokoll aufnehmen.
- [x] 4: commit via `git`-Agent: `test: decouple full-suite tests from the global validate exit code`.

> **LEDGER-Stand 2026-09-28 — W2-8 abgehakt über den maschinellen Ledger-Writer (Fortschrittsnotiz,
> keine Änderung der Task-Semantik).** Die K53-Interim-Regel ist mit `3d8499ca` beendet, deshalb dieser
> Werkzeuglauf und **keine** Handsetzung. Abgehakt **4** von **4** Checkboxen gegen diesen Plan, Task-ID
> **`W2-8`**, Schritt **4** nennt den Commit-Titel
> `test: decouple full-suite tests from the global validate exit code`; ein Hash ist **nicht** genannt,
> weil dieser Task **nicht** committet.
> **Baseline, gemessen in Schritt 1 (ungefilterte Roh-Ausgabe, umgeleitet und aus der Datei gelesen —
> `rtk` filtert pytest-Fehlschläge):** `python3 -m pytest tests/ -q` ⇒
> **`2 failed, 3414 passed, 1 skipped, 117 warnings, 35 errors, 11 subtests passed`**, also genau
> **zwei** rote Tests: (1) `tests/test_knowledge_engine.py::test_knowledge_roles_pass_schema_validation`
> (Assertionsstelle damals `:228`) und (2) `tests/test_sharkord_service_name_migration.py::
> test_generated_docker_agent_has_no_leftover_platform_namespace_placeholder` (damals `:48`). **Kern der
> Fehlermeldung in beiden, wortgleich:** `[ERR] [docs.readme_index] documentation category
> 'docs/se-cascade/' is declared in the README.md Documentation Index section but the section links no
> page below it`. **Gemessene Ursache:** beide Tests prüften eine **Fremdgröße** — den repo-globalen
> Konsistenz-Exit-Code, nicht ihren Gegenstand. `_handle_validate` ruft den Runner über
> `agent_meta_root` (`scripts/lib/cli_commands.py:975`), und der Runner ruft
> `check_readme_docs_index(_AGENT_META_ROOT)` **unbedingt** (`scripts/consistency-check.py:201`; `--root`
> wirkt erst ab `:257`, die Altchecks stehen in `:196` und `:199-201`). Beim sharkord-Test gilt das
> **trotz** `cwd=tmp_path`, weil die Altchecks den Agent-Meta-Root benutzen, nicht den Projekt-Root.
> Die **35** `errors` sind unverändert `tests/browser/*` ohne Socket und **kein** Kriterium.
> **Mechanismus je Test — beide (i), (ii) nicht anwendbar, (iii) gemessen und begründet verworfen:**
> **(1) Knowledge-Test** prüft jetzt den **eigenen** Gegenstand in-process gegen
> `config/project-config.schema.json`: jede unter `group: knowledge` registrierte Rolle muss (a) im
> `roles.items.enum` des Schemas whitelisted sein, (b) ein `agents/1-generic/<rolle>.md` haben, und
> (c) eine Config, die **alle** Knowledge-Rollen einschaltet, muss das Schema bestehen; als
> **Nicht-Vakuum-Nachweis** (d) muss dieselbe Prüfung einen verbogenen `knowledge-engine.enabled`
> ablehnen (`pytest.raises(jsonschema.ValidationError)`). **Was wegfällt:** der
> `sync.py --dry-run --validate`-Subprozess samt `assert result.returncode == 0`. **Was hinzukommt:**
> `import jsonschema` via `importorskip` (kein Subprozess, keine Fremdgröße).
> **(2) sharkord-Test** prüft jetzt den **eigenen** Fixture-Scope: nach dem Sync darf **im ganzen
> generierten Agentenbaum** `.claude/agents/*.md` **kein** `{{platform.<ns>.<key>}}`-Platzhalter
> überleben (generalisierte, strengere Form der beiden Einzelnamen). **Was wegfällt:** der
> `sync.py --validate`-Subprozess samt `assert validate_result.returncode == 0`. **Was hinzukommt:** die
> Regex-Vollform plus der Baum-Scan; **erhalten bleiben** alle drei ursprünglichen Assertions
> (`service_name` und `host_lan_ip` nicht in `docker.md`, `127.0.0.1` aufgelöst) und
> `assert docker_agent.is_file()`. **Nicht-Vakuum beider Ersatzungen, gemessen:** der Schema-Check
> fällt bei `enabled: "not-a-bool"` um, und eine von Hand in das generierte `docker.md`
> eingeschleuste Zeile `sharkord/sharkord:{{platform.sharkord.image_tag}}` lässt den neuen Baum-Scan
> anschlagen (danach wieder leer) — das Muster ist **real**, `agents/2-platform/sharkord-docker.md`
> trägt es auf Template-Ebene an vier Stellen.
> **(iii) wurde gemessen und verworfen, mit dem Grund:** `python3 scripts/consistency-check.py --json
> --root <Fixture>` endet auf **Exit 1** mit **3** ERRORs — `README.md :: docs.readme_index` (Host) und
> `config/role-defaults.yaml :: crossrefs.role-defaults-missing` sowie
> `config/provider-capabilities.yaml :: fanout.capabilities-missing` (dem Fixture fehlen diese
> Framework-Dateien) — und **null** Findings zu `.claude/agents/docker.md`. Ein scope-gefilterter
> Auswertungsfilter wäre dort also ein No-op-Wächter gewesen, der 20 Sekunden Subprozess für kein
> Signal kostet; die Grenze ist stattdessen **im Code benannt** (Kommentar am Test), inklusive der
> Stellen `:196`/`:199-201`/`:257`.
> **Nachweis (a):** `python3 -m pytest tests/test_knowledge_engine.py
> tests/test_sharkord_service_name_migration.py -q` ⇒ **`46 passed`, 0 failed, Exit 0** (vorher
> `2 failed, 44 passed`) — die **Testanzahl bleibt 46**, es wurde nichts hinzugefügt oder entfernt.
> **Nachweis (b), am Diff belegt:** beide `assert … returncode == 0` gegen `sync.py --validate` sind
> entfernt; im Diff steht an ihrer Stelle nur der Subprozess `sync.py` **ohne** `--validate` im
> sharkord-Test, dessen `assert sync_result.returncode == 0` **den Fixture-Sync** betrifft und
> erhalten bleibt. Kein `|| True`, kein `xfail`, kein `-k`-Filter, kein herabgesetzter Sollwert, kein
> Eingriff in `scripts/sync.py`.
> **Nachweis (c) — die negative Probe, konkret gewählt:** der Host trägt **schon jetzt** den
> `docs.readme_index`-ERROR, deshalb genügt der Zustand allein nicht als Beweis; zusätzlich wurde ein
> **zweiter** `docs/`-ERROR injiziert (eine zusätzliche Readme-Dokumentationskategorie
> `docs/w28-probe/` ohne Seite darunter). Ergebnis: **2** ERRORs gleichzeitig in
> `scripts/consistency-check.py --json` (beide `README.md :: docs.readme_index`), und der gezielte Lauf
> der **beiden** Tests ⇒ **`2 passed`, Exit 0**. Die `README.md` wurde danach **byte-identisch**
> zurückgeschrieben (per Byterückgabe, **ohne** Git-Operation) und der Zustand erneut gemessen.
> **Nachweis (d):** `git diff --name-only` ⇒ **ausschließlich** `tests/test_knowledge_engine.py` und
> `tests/test_sharkord_service_name_migration.py`, plus diese Plan-Datei als **werkzeugbedingte
> Ausnahme** — der Ledger-Writer schreibt den Plan, das ist **kein** Produktivcode.
> **Nachweis (e):** `python3 -m pytest tests/ -q` ⇒ **`3416 passed, 1 skipped, 119 warnings, 35 errors,
> 11 subtests passed`**, **0 `FAILED`** (Baseline **2**), **35** `errors` wie in der Baseline und
> **0** davon außerhalb `tests/browser/*` — Zählwert, kein Exit-Code-Kriterium (`W-VALIDATE-ROT`).
> **Überlappungs-Pin, gemessen:** `tests/test_plan_ledger_writer.py::
> test_validate_plan_reaches_the_expected_overlap_verdict` bleibt grün mit dem Ist-Wert **18**
> (Literal `== 18`, `tests/test_plan_ledger_writer.py:524`, unangetastet), die Datei grün mit
> **`22 passed`**. Der Zähler liest nur den Header-**Titel** (`spec_plan.py:589` `prompt=title`), nicht
> den Block, deshalb verschiebt diese Notiz die Zahl nicht; `files_touched("W2-8")` bleibt `()`,
> ebenso für **W2-4**, **W2-6** und **W2-9**, und die Task-Zahl bleibt **50** — dafür ist im Fließtext
> bewusst **keine** Doppelpunktform der Feldwörter und **keine** zeilenbeginnende
> `Depends on:`-Zeile verwendet (W2-9s Notiz hat diesen Tripwire bereits einmal ausgelöst).
> **Diese Task-Zeile ist für sich genommen kein Welle-Gate** (RVW-3): das Wellen-Gate **W2** bleibt an
> **W2-7** gebunden.


### W2-7: Registrierung, Common-Gate und Exit-Codes — **Rev. 0.6: Abschluss der Welle (K20); Rev. 0.7: Abschluss nach W2-8**

**Files:** Modify `scripts/lib/consistency/docs.py` (**nur** die `__all__`-Einträge der neu
hinzugekommenen Checks, Spec §4.1), `scripts/consistency-check.py`,
`scripts/lib/consistency/report.py` (**Rev. 0.5, K15**), `tests/test_doc_freshness.py`,
`tests/test_doc_facts.py`.
**Rev. 0.6 / K46 — Ownership-Korrektur nach W2-0 (fail-closed, der eigentliche Anlass dieser
Runde).** W2-7 besitzt **fünf** Dateien, nicht vier: (1) `tests/test_doc_facts.py` — der
**Nicht-Registrierungs-Pin für V3** `test_v3_is_not_wired_into_the_runner_yet` (gemessen
`:2527-2537`) sowie die F1-PROMOTION- und Exit-Code-Tests bleiben dort; (2) **`tests/
test_doc_freshness.py`** — der **Nicht-Registrierungs-Pin für V1**
`test_v1_is_not_wired_into_the_runner_yet` ist mit den V1-Tests nach W2-0 dorthin **verschoben**
worden (gemessen **`:364-383`**) und wird in **Schritt 1** durch `test_v1_is_registered_in_the_runner`
ersetzt (RVW2-5 bleibt **vollständig** in Kraft). **Die frühere Aussage „dieselbe Datei, **kein**
neues File-Ownership" ist damit berichtigt:** es ist sehr wohl **neues** File-Ownership — es ist
**zulässig**, weil W2-7 **sequenziell** als **Letzter** der Welle schreibt und die angewandte
Ownership-Regel (Abschnitt „Ownership-Matrix, DAG-Kantenliste und Zyklenprüfung", *Ehrliche Grenze
der Regel (K20)*) mehrere schreibende Tasks derselben Datei **ausschließlich sequenziell** zulässt
(`W2-0 → W2-5 → W2-4 → W2-7`, Kanten 6, 8, 11; **Rev. 0.7 / E-7: `W2-4` schreibt `docs_freshness.py`
und `tests/test_doc_freshness.py` nicht mehr — die Kette ist `W2-0 → W2-5 → W2-7`, und W2-7 hängt
zusätzlich an W2-8**). **Negativregel (K46, verbindlich):** die
`Files:`-Listen von **W2-3, W2-4, W2-5, W2-6, W6-2 und W8-4** nehmen **kein**
`scripts/lib/consistency/docs.py` auf — **gemessen bestätigt**: nur W2-1, W2-2, W2-0 und W2-7 führen
`docs.py`, W6-2 führt `docs_wiki.py`, W8-4 führt `docs_index.py`. Grund: W2-3/W2-5/W2-6 laufen in
**PG-2a** parallel, und ein `docs.py`-Write-Set dort wäre genau die Ownership-Kollision, die **K20**
beseitigt hat. **W2-7 ist der alleinige Owner aller `__all__`-Inkremente.** Eine spätere Revision,
die eine dieser Listen „vollständig" macht, zerstört die Parallelität von PG-2a und ist **fail-closed**
(Fail-closed-Klausel oben).
**Interfaces:** Produces: Registrierung V1…V9 mit `check="docs.<name>"`; Common-Gate (No-op, wenn
`docs-consolidation.enabled != true`); unveränderter Exit-Code-Vertrag; **neu:** `Finding.line`
und `Finding.branch` als **Dataclass-Felder** mit Default (Default `""`/`None`, damit alle
**bestehenden** Konstruktoraufrufe unverändert bleiben) und ihre Serialisierung in
`print_json_report`. Consumes: W2-6, W1-10, W2-1 (K16-Rule-3-Eingrenzung, weil
`_v1_finding` in **`docs_freshness.py:255-273`** (Rev. 0.6 / K48; vor dem Split `docs.py:329-347`)
dieselben Felder setzt).
**Agent:** developer · **Depends on:** **W2-3, W2-4, W2-5, W2-6, W2-8** (Rev. 0.7 — **W2-8**
neu; Rev. 0.6 / K20; Rev. 0.5: W2-6) · **parallel_group:** — (**sequenziell**, Abschluss der W2)
**Ziel-AK (AC):** **AC-13** (IC-05), **AC-24** · **V-Check:** alle
**Akzeptanz:** `test_exit_codes_unchanged_with_new_checks` grün: 0 Errors → Exit **0**, genau 1
Error → Exit **1**, Skriptfehler → Exit **2**; bestehende Exit-Code-Doku
(`scripts/consistency-check.py:23-26`) bleibt gültig; in allen Szenario-Fixtures sind V1–V9
**vollständig No-op** (AC-38). Die bestehenden drei Checks
(**Rev. 0.6 / K48:** nach dem W2-0-Split in `docs_links.py`, nicht mehr in `docs.py` —
`check_sync_cli_docs` **`:30-65`**, `check_ui_help_mappings` **`:68-118`**, `check_readme_docs_index`
**`:121-…`**; die Plan-Angaben `:9`/`:47`/`:100` stammten aus einer älteren Zeilengeneration vor dem
Split) bleiben in Signatur und Severity unverändert.
**Akzeptanz, neu (Rev. 0.5, K15 — F1-PROMOTION, B-5/E-15):** `line` und `branch` sind
**Dataclass-Felder** von `Finding` (`scripts/lib/consistency/report.py:28-41`), **keine**
Instanzattribute mehr; `print_json_report` (`:78-97`) serialisiert **beide** mit;
**`docs_freshness.py:255-273`** (Rev. 0.6 / K48; vor dem Split `docs.py:329-347`)
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
**`tests/test_doc_freshness.py:364-383`** (Rev. 0.6 / K47 — nach dem W2-0-Verschieb; die frühere
Angabe `tests/test_doc_facts.py:2403-2422` ist der Ort *vor* dem Split)
(`test_v1_is_not_wired_into_the_runner_yet`, Assertion
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
**Verifikation (Rev. 0.6):** `python3 -m pytest tests/test_doc_facts.py
tests/test_doc_freshness.py tests/test_doc_wiki.py tests/test_doc_index.py
tests/test_doc_freshness_v5.py tests/test_doc_facts_expected.py -q` → **0**
(**Rev. 0.7 / E-7:** `tests/test_doc_freshness_v5.py` ergänzt — W2-4 schreibt die V5-Tests nach E-7
nicht mehr in `tests/test_doc_freshness.py`);
~~`python3 scripts/consistency-check.py` → **0**~~
**AUFGEHOBEN (Rev. 0.5, RVW-2) — unerreichbar.** W2-7 registriert V1–V7; V2, V3 und V6
sind **ERROR** (IC-05), und `print_report` gibt `1 if errors else 0`
(`scripts/lib/consistency/report.py:75`) ⇒ der rohe Runner ist ab W2-7 planmäßig Exit **1**.
Maßgeblich ist **W2-GATE-ERRORS** (Erwartungswert je V-Check, Termin, Owner). **Rev. 0.6 (K22):
die Dokuzeile zum spätesten Termin 0 ist zu präzisieren** — sie gilt nur noch für die **2**
README-Layout-Findings (**W8-2**, Owner `developer`); die **25** `docs/**`-Link-Findings behebt AC-30
**nicht** mehr (Follow-up `F-DOCS-LINKS-2026-09-27`, Termin **2026-10-11**), weshalb
`consistency-check.py → 0` **dauerhaft unerreichbar** bleibt — maßgeblich ist die **Deltasperre**,
Severity-Frage **OQ10**. Volltext: Tabelle `W2-GATE-V3-KLASSEN`. **Diese Task-Zeile ist für sich
genommen kein Welle-Gate** (RVW-3);
`bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0**;
`python3 scripts/consistency-check.py --json | python3 -c 'import json,sys;d=json.load(sys.stdin);print(sorted({k for f in d["findings"] for k in f}))'` → enthält `line` **und** `branch` (F1-PROMOTION, vacuously grün, solange `docs-consolidation.enabled: false` — dann mit dem pytest-Nachweis kombinieren).
**Steps:**
- [x] 1: Test schreiben (fail). **RVW2-5 (verbindlich in dieser Task):** den
      Nicht-Registrierungs-Pin `test_v1_is_not_wired_into_the_runner_yet`
      (**`tests/test_doc_freshness.py:364-383`**, Rev. 0.6 / K47 — Datei nach dem W2-0-Verschieb;
      vor dem Split `tests/test_doc_facts.py:2403-2422`) durch den **positiven** Registrierungs-Pin
      `test_v1_is_registered_in_the_runner` ersetzen (Import in `consistency-check.py` **und**
      `docs.no_manual_counts` im `findings[]` eines Fixture-Laufs mit `enabled: true`); den
      ausgeliehen Test **nicht** löschen, sondern im Testmodul kommentieren.
- [x] 2: Checks registrieren; Common-Gate als erste Bedingung in jeden Check einziehen.
      **RVW2-1:** die Registrierung ist damit der **einzige** Nachweis der Registrierungszahl —
      `docs-checks` im W-GATE zählt befundliefernde Checks und ist **kein** Registrierungsnachweis.
      **Rev. 0.6 (K20):** die Importe in `scripts/consistency-check.py:52-56` bleiben **unverändert**
      — registriert wird **weiter über die Fassade `docs.py`**, nicht modulweise; genau das macht den
      Fassaden-Contract (K19) zur Voraussetzung der Registrierung.
- [x] 3: Tests grün beobachten; Szenario-Lauf beobachten.
- [x] 4: **K15 / B-5 — `line` und `branch` in `report.py` zu Dataclass-Felder mit Default
      machen, in `print_json_report` serialisieren und `_v1_finding` (**`docs_freshness.py:255-273`**,
      Rev. 0.6 / K48) auf
      den Konstruktor umstellen**; F1-PROMOTION-Test schreiben (grün beobachten).
- [x] 5: commit via `git`-Agent: `feat: register docs checks behind fail-off common gate`.

> **LEDGER-Stand 2026-09-28 — W2-7 abgehakt über den maschinellen Ledger-Writer (Fortschrittsnotiz,
> keine Änderung der Task-Semantik).** Abgehakt **5** von **5** Checkboxen gegen diesen Plan, Task-ID
> **`W2-7`**. Dry-Run: `tasks updated: W2-7`, `checkboxes would toggle: 5`, **Exit 0**, **keine**
> `unmatched`-Zeile. Schreibender Lauf: `tasks updated: W2-7`, `checkboxes toggled: 5`, **Exit 0**,
> **keine** `unmatched`-Zeile; der Plan-Diff gegen die Vorher-Kopie umfasst ausschließlich diese
> **5** Checkboxen und diese Notiz. Plan bleibt `status: APPROVED`, `revision: 0.7`, keine ID
> umnummeriert. **Ehrlich zu Schritt 5:** auftragsgemäß mit abgehakt, der **Commit ist nicht erfolgt** —
> W2-7 lief als **No-Commit**-Task, der Commit ist der Schritt des `git`-Agenten.
> **Registrierung (RVW0/Schritt 2), gemessen — `check="docs.<name>"` pro Check:** Die einzige
> Registrierungsstelle ist die Tabelle `DOCS_CHECKS` in `scripts/consistency-check.py:105-113`, in
> IC-05-Reihenfolge: `check_no_manual_counts` (V1) `:106`, `check_docs_index_completeness` (V2) `:107`,
> `check_internal_links` (V3) `:108`, `_readme_docs_index` (V4) `:109`, `check_role_generation_parity`
> (V5) `:110`, `check_docs_facts_fresh` (V6) `:111`, `check_wiki_staleness` (V7) `:112`. **7** von **7**
> implementierten Checks registriert; **V8** (`check_spec_plan_path_convention`, W6-2) und **V9**
> (`check_stale_backups`, W8-4) existieren noch nicht und werden von ihren Tasks an derselben Stelle
> angehängt. Die Check-IDs stehen als Kommentar an der jeweiligen Registrierungszeile, weil die IDs den
> Familienmodulen gehören und eine zweite Quelle im Runner nur driftfähig wäre.
> **K20 — gemessene Lesart der Importvorgabe:** der Importblock `scripts/consistency-check.py:53-63`
> ist **weiterhin genau ein** `from lib.consistency.docs import (...)` — die Fassade, nicht modulweise;
> modulweise Importe (`lib.consistency.docs_links` / `docs_freshness` / `docs_freshness_v5` /
> `docs_index` / `docs_wiki`) kommen im Runner **mit 0 Treffern** nicht vor. Gewachsen ist
> **ausschließlich die Namensliste** innerhalb dieses einen Blocks, denn der Block *ist*
> laut Plan (`Registrierungszahl`-Zeile, `:2295`) die Registrierungsstelle, und der positive Pin (a)
> verlangt `check_no_manual_counts` wörtlich in diesem Block. Eine wörtlich unveränderte
> Dreier-Namensliste bei gleichzeitig registrierten V1…V7 wäre nicht widerspruchsfrei.
> **Die drei Zahlen, gemessen und nicht zu verwechseln (Korrektur einer früheren Notiz-Fassung, die
> „3 → 7 Namen" schrieb):** der Importblock hat **3 → 9** Namen, die Registry `DOCS_CHECKS` **7**,
> und die Fassade exportiert **9** `check_*`-Callables. Die Differenz **9 − 7 = 2** sind die beiden
> vorbestehenden, **ungegateten** Altchecks `check_sync_cli_docs` und `check_ui_help_mappings`, die
> IC-05 außerhalb der V-Familie hält (einargumentige Signatur, kein `config`): sie stehen im
> Importblock, werden aber **nicht** über `DOCS_CHECKS` registriert. Der Fassaden-Contract
> (K19) ist damit wirksam: die Namen stehen in `docs.py:79-85` im `__all__`
> (`V2_CHECK_ID`, `check_docs_index_completeness`, `V5_CHECK_ID`, `check_role_generation_parity`,
> `V6_CHECK_ID`, `check_docs_facts_fresh`, `V7_CHECK_ID`, `check_wiki_staleness`), die Importe in
> `docs.py:37-59`. **K46 eingehalten:** nur W2-1, W2-2, W2-0 und W2-7 führen die Fassade; W2-3/W2-4/
> W2-5/W2-6 führen sie nicht.
> **Common-Gate (IC-05/IC-22/AC-38), Ort und Fail-off-Beleg:** `docs_consolidation_enabled()`
> `scripts/consistency-check.py:131-149`, `load_project_config()` `:116-128`; die **erste Bedingung**
> des gesamten registrierten V-Blocks ist `scripts/consistency-check.py:292`, der Aufruf der
> sieben Checks `:293-294`. **Fail-off am Default, gemessen:** `docs-consolidation.enabled` ist in
> **diesem** Repo seit W1 explizit gesetzt (`.meta-config/project.yaml:398-399`, `enabled: true`) —
> der rohe Runner ist deshalb **nicht** no-op, und die Aussage „der Schalter ist im Repo nicht gesetzt"
> trifft für agent-meta selbst **nicht** zu (NFA-04/IC-22: in Consumer-Projekten ist er es). Der
> Fail-off-Nachweis ist deshalb an **Abwesenheit** geführt und in
> `tests/test_doc_freshness.py::test_the_common_gate_is_the_first_condition_of_every_registered_check`
> (`:463`) gepinnt: dieselbe `run_checks()`-Zeile liefert über einen Baum **ohne** Block **0**
> `docs.`-Findings und über einen Baum, der sich **nur** durch `docs-consolidation: {enabled: true}`
> unterscheidet, **4** (`docs.no_manual_counts`, `docs.docs_index_completeness`, `docs.internal_links`,
> `docs.readme_index`); explizites `enabled: false` verhält sich wie Abwesenheit. Die
> Schalter-Wahrheitstabelle (fehlender Block, leerer Block, `false`, Nicht-Boolean `"false"`,
> Nicht-Mapping `docs-consolidation: true` ⇒ **alle** zu) ist mitgemessen; `is True` statt
> Truthiness ist die fail-off-Seite und auf jedem schema-gültigen Input identisch zu
> `knowledge.py:127`. **Die sechs Szenario-Fixtures `5[0-6]-*.project.yaml` setzen den Schlüssel nach
> wie vor nicht** (gepinnt in `test_the_scenario_configs_never_set_the_common_gate`, `:511`).
> **Exit-Code-Vertrag (AC-24), alle drei Werte gemessen — Doku `scripts/consistency-check.py:24-26`
> unverändert gültig:** **0** (0 Errors) end-to-end als Prozess-Exit über ein Fixture mit
> Gate zu ⇒ `summary {total 0, errors 0, warnings 0}`, Exit **0** (auch im Textbericht); **1** (genau
> 1 Error) end-to-end über ein Gate-an-Plus-`checks.strict`-Fixture ⇒ `summary {total 1, errors 1}`,
> Exit **1**, und der eine Error ist ein `docs.no_manual_counts`-V1a-Fund; **2** (Skriptfehler)
> end-to-end über `--file <nicht vorhanden>` ⇒ Exit **2**. Gepinnt in
> `tests/test_doc_facts.py::test_exit_codes_unchanged_with_new_checks` (`:2682`), zusätzlich
> in-process an beiden Renderern (`print_report`/`print_json_report`: 0 ⇒ 0, 1 Error ⇒ 1).
> **F1-PROMOTION (K15/B-5), Felddefinition und Serialisierung:** `Finding` in
> `scripts/lib/consistency/report.py:31-61` — `line: int | None = None` (`:60`) und
> `branch: str = ""` (`:61`), beide **mit Default** und hinter `suggestion`, damit jeder bestehende
> Konstruktoraufruf einschließlich des positionellen in `python_compat.py` unverändert bleibt;
> serialisiert in `print_json_report` (`:105-126`, Schlüssel `:116-117`). `__str__` (`:63`) ist
> **unverändert** und zeigt weiterhin nur `message`, damit die message-only-Pins in
> `tests/test_doc_facts.py` grün bleiben. `from __future__ import annotations` (`:3`) ist
> hinzugekommen, weil `int | None` sonst ein Python-3.9-Importfehler wäre
> (`check_py39_union_syntax`).
> **Gemessener Schlüsselsatz aus dem echten Report:** `python3 scripts/consistency-check.py --json`
> ⇒ `['branch', 'check', 'file', 'line', 'message', 'severity', 'suggestion']` — **vor** W2-7 waren es
> `['check', 'file', 'message', 'severity', 'suggestion']`. Der F1-Nachweis als pytest
> (`test_finding_carries_line_and_branch_through_the_json_report`, `tests/test_doc_facts.py:2622`)
> läuft die **echte Kommandozeile** als Subprozess und liest sie mit `json.loads`; er prüft **drei**
> Formen in einem Report: V1a (`line 1`, `branch "V1a"`), V3 (`line 3`, `branch "link"`) und V2
> (`line None`, `branch ""`) — die letzte schließt eine bedingte Serialisierung aus.
> **Stand nach dem Abschluss-Fix (F-A) — der Konstruktor ist jetzt der Weg, und die frühere
> „keine Wirkung"-Aussage dieser Notiz war falsch:** `_v1_finding` in
> `scripts/lib/consistency/docs_freshness.py:274-293` (neu, **593** Zeilen, Decke **600**) übergibt
> `line=lineno` und `branch=branch` als **Konstruktorargumente**; der Docstring dort nennt jetzt den
> Grund (deklarierte Felder gehören in die Signatur) statt der überholten Behauptung „`Finding` trägt
> kein `line`-/`branch`-Feld". **Unverändert geblieben, weil nicht in der Write-Menge:** dieselbe
> Instanzattribut-Form steht in `docs_links.py:448-460` (`_v3_finding`) und in
> `docs_freshness.py:488-508` (`_v6_finding`, zusätzlich `kind`).
> **Die Folge ist nicht „keine", sondern eine echte Verhaltensänderung — an der Wertoberfläche selbst
> nicht, an `repr` und `eq` sehr wohl (gemessen):** (a) `repr(finding)` trägt jetzt `line=` und
> `branch=`, d. h. jede Testausgabe, die ein Finding reprint, wird ausführlicher; (b) zwei Findings,
> die sich **nur** in `line` unterscheiden, waren vorher **gleich** und sind jetzt **verschieden**.
> Das ist die beabsichtigte Konsequenz der F1-Promotion (der Dataclass-`__eq__` vergleicht alle
> deklarierten Felder) und kein Defekt — aber es ist eine Änderung, die ein Vergleich in einem Test
> treffen kann. `dataclasses.fields()` enthält beide Felder jetzt **deklariert**; die
> Instanz-``__dict__``-Belegung ist dieselbe wie beim nachträglichen Setzen.
> **Ebenso nicht angefasst:** `kind` von V6 bleibt reines Instanzattribut und erscheint **nicht** im
> `--json` (Begründung im Absatz weiter unten).
> **Ist-Stand `--json` nach W2-7, nach `check` gruppiert (gemessen, 386 Findings,
> `summary {errors 235, warnings 151}`, Prozess-Exit 1):** `docs.no_manual_counts` (V1) **52** WARNING
> — Sollwert „≥ 1, `['WARNING']`" erfüllt, Termin **W3-7**; `docs.docs_index_completeness` (V2)
> **207** ERROR — planmäßig rot, `docs/INDEX.md` existiert nicht, Termin **W3-6**;
> `docs.internal_links` (V3) **27** ERROR — **2** Layout-Findings (`README.md:722`/`:723`, Termin
> **W8-2**) + **25** unter `docs/**` (Follow-up `F-DOCS-LINKS-2026-09-27`, Termin 2026-10-11),
> `llms.txt` **0**; `docs.readme_index` (V4) **1** ERROR — Kategorie `docs/se-cascade/`, **planmäßig
> rot**, Follow-up `F-DOCS-README-INDEX-SE-2026-09-27`, Termin 2026-10-11; `docs.role_generation_parity`
> (V5) **1** WARNING — das `se`-Gate ist zu, also WARNING statt ERROR (IC-05-Konvention);
> `docs.docs_facts_fresh` (V6) **3** WARNING — die Art `missing-in-expected` ist per
> `V6_SEVERITY_BY_KIND` WARNING, die ERROR-Arten liefern am echten Baum **0**;
> `docs.wiki_staleness` (V7) **10** WARNING — deckungsgleich mit dem Sollwert der Planzeile.
> **Vorher** (Baseline vor dieser Task, gleicher Lauf): **1** Error, **85** Warnings, **86** Findings,
> davon **1** `docs.`-Finding (V4), Exit **1**; Schlüsselsatz ohne `line`/`branch`. **Abweichung
> gemeldet:** die Planzeile „V6 planmäßig rot (ERROR)" trifft auf die **Severity-Menge** nicht zu —
> V6 liefert am echten Baum **WARNING**; der Sollwert „rot" ist über den *Wert* erfüllt, die Severity
> nicht. Ebenso ist V5 mit **1** Fund nicht **0** (Planzeile), weil `se-component-requirements` unter
> dem geschlossenen `se`-Gate als **WARNING** gemeldet wird. Beide Abweichungen sind
> `W-GATE-TABLE-ABWEICHUNG`-Kandidaten für das W2-Review-Protokoll.
> **Ersetzung der Nicht-Registrierungs-Pins (RVW2-5, Schritt 1) — fünf Pins, nicht einer:** Der
> planlich benannte V1-Pin `test_v1_is_not_wired_into_the_runner_yet`
> (`tests/test_doc_freshness.py:364-377` vor der Änderung) ist durch
> **`test_v1_is_registered_in_the_runner`** (`:406`) ersetzt; seine Historie steht als Kommentar mit
> Abschnittsanker `:367-378` direkt darüber, der Test wird **nicht** parallel weitergeführt. Der
> positive Pin prüft **(a)** `check_no_manual_counts` im Runner-Text **plus**
> `from lib.consistency.docs import` **plus** `__all__`-Eintrag **plus** Eintrag in `DOCS_CHECKS`, und
> **(b)** `docs.no_manual_counts` im `findings[]` eines **echten** `run_checks()`-Laufs über ein eigenes
> Fixture mit `docs-consolidation.enabled: true` (Common-Gate **an**) mit `branch == "V1a"`,
> `line == 1`, `file == "README.md"`. **Über den ersten Auftrag hinaus mitgenommen, weil die Pins sonst
> das W2-Gate gerissen hätten:** dieselbe Ersetzung für den V6-Pin
> `test_v6_is_not_wired_into_the_runner_yet` (`test_doc_freshness.py:695-720` vor der Änderung) ⇒
> **`test_v6_is_registered_in_the_runner`** (`:852`) und für den V3-Pin
> `test_v3_is_not_wired_into_the_runner_yet` (`tests/test_doc_facts.py:2527-2537` vor der Änderung) ⇒
> **`test_v3_is_registered_in_the_runner`** (`:2598`). **Nachtrag aus dem Abschluss (2026-09-28, vom
> Parent ausdrücklich als Write-Menge übertragen, ausschließlich zum Ersetzen der Pins):** die beiden
> übrigen Pins sind jetzt ebenfalls durch positive Pins ersetzt, **strukturgleich** zu V3.
> `tests/test_doc_index.py`: `test_v2_is_not_registered_in_the_runner_yet` (alt `:870-890`, drei
> Asserts) ⇒ **`test_v2_is_registered_in_the_runner`** (neu `:909`), Historie als Kommentar mit
> Abschnittsanker `:870-882`; Hälfte (a) `:935-949` (Runner-Text, Fassaden-Import, `__all__`,
> `hasattr`, `DOCS_CHECKS`), Hälfte (b) `:951-957` (`run_checks()` über ein Fixture mit
> `docs-consolidation.enabled: true`, `V2_CHECK_ID` als Literal, `file`, Severity **ERROR**).
> `tests/test_doc_wiki.py`: `test_v7_is_not_wired_into_the_runner_yet` (alt `:379-391`, ein Assert)
> ⇒ **`test_v7_is_registered_in_the_runner`** (neu `:415`), Historie als Kommentar mit Abschnittsanker
> `:375-386`; Hälfte (a) `:442-454`, Hälfte (b) `:456-460` (echter `run_checks()`-Lauf, `V7_CHECK_ID`
> als Literal, `file`, Severity **WARNING**). **Gemessener Beweis, dass ausschließlich der Pin-Block
> verändert wurde** (Opcode-Diff gegen `git show HEAD`, nicht Zeilen-Diff): `tests/test_doc_index.py`
> **960 → 1027** Zeilen bei **38 → 38** Tests, alle Opcode zwischen HEAD-Zeile **870** und **890**;
> `tests/test_doc_wiki.py` **391 → 461** Zeilen bei **10 → 10** Tests, alle Opcode zwischen HEAD-Zeile
> **374** und **391**. Der Import von `importlib.util` liegt **in** dem jeweiligen Helper, nicht im
> Modulkopf, damit die Änderung auf den Block beschränkt bleibt. **Keine** der in W2-6 bzw. W2-3
> implementierten Prüfungen wurde umgeschrieben — die beiden Dateien enthalten weiterhin **38** bzw.
> **10** Tests, und die Nachbarn des Blocks (`test_v2_lives_in_docs_index_and_v4_in_docs_links`
> `:960`, `_is_architecture_page_without_provenance` `:352`) sind byteidentisch. Fünf Pin-Historien
> stehen jetzt als Kommentar mit Abschnittsanker im jeweiligen Modul.
> **Fünf Einzelpins ⇒ ein struktureller Pin (F-B).** Für **V4** und **V5** gab es keinen
> Registrierungs-Pin, und zwei neue Einzel-Pins in fremden Dateien wären der falsche Ort. Stattdessen
> trägt `tests/test_doc_facts.py` jetzt **einen** Test
> **`test_the_docs_registry_covers_exactly_what_the_facade_exports`** (neu `:2776`), der die
> Vollständigkeit **strukturell** erzwingt: die Id-Menge der Registry `DOCS_CHECKS` **gleich** der
> Id-Menge der Fassade-`check_*`-Exporte, die auf diesem Repository melden — in **beiden** Richtungen,
> also kein exportierter Check ohne Registry-Eintrag und kein Registry-Eintrag ohne Export. Dazu vier
> Nebenpins, jeder eine eigene Bruchform: jeder Eintrag meldet **genau eine** Id (ein toter Eintrag
> fällt durch), die sieben Funktionen sind paarweise **verschieden** (ein kopierter Eintrag fällt
> durch), jede Id beginnt mit `docs.` (IC-05), und das exportierte `*_CHECK_ID`-Vokabular ist
> vollständig benutzt, mit **genau einer** Id außerhalb — die des V4-Adapters, **abgeleitet** über den
> einzigen Export, dessen Name kein `__name__` der Registry ist, und namentlich als
> `check_readme_docs_index` benannt. Die Differenz **9 Exporte − 7 Registry-Einträge** wird als die
> beiden ungegateten Altchecks benannt, nicht heuristisch weggefiltert.
> **Die Kopplung, nüchtern benannt (bewusste Entscheidung, akzeptiert, kein Refactoring).** Pin 1
> („jeder Eintrag meldet **genau eine** Id") und die Benennung der zwei stillen Exporte
> (`silent == {check_sync_cli_docs, check_ui_help_mappings}`) hängen daran, dass der Test gegen den
> **echten Repository-Root** läuft und die „Clean"-Checks am **heutigen** Stand still sind. Das ist
> eine reale Fehlalarm-Quelle in **beiden** Richtungen, und beide sind gewollt: Pin 1 ist auf einem
> fremden, sauberen Root **rot**, weil dort **5 von 7** Einträgen nichts melden — richtig, denn ein
> Eintrag ohne Befund ist eine stille Lücke; und `silent` behauptet, dass zwei **Altchecks** heute
> nichts melden, was stimmt und morgen falsch sein kann. **Der konkreteste Fall:** ein späterer
> „alle Findings beheben"-Chore, der V2/V3/V6 auf 0 bringt, macht diesen Test rot — mit einer
> Registry-Färbung, die dann **irreführend** ist, weil die Gleichheit weiterhin hält und nur die
> *Id-Menge* schrumpft. **Bewusst nicht abgesichert**, weil jede Absicherung denselben Chore erneut
> bindet: der Test soll an der *Struktur* der Registry hängen, nicht an einem aktuellen
> Finding-Stand. Wer den Chore fährt, zieht den Test mit — das ist der richtige Zeitpunkt, ihn neu zu
> fassen.
> **Mutantennachweis, gemessen:** ein Zeilenpaar entfernt (der Import von `check_wiki_staleness` **und**
> sein Registry-Eintrag, damit das Modul weiter importiert) ⇒ **genau 1 failed**, und zwar an der
> Gleichheits-Assertion mit beide Seiten im Text
> (`registry=[…6 ids…]` gegen `exported-reporting=[…7 ids…]`, „Left contains one more item:
> `docs.wiki_staleness`"). Die Mutation wurde **vollständig zurückgenommen** (Datei wieder **373**
> Zeilen, `sha256` nach dem Restore geprüft, `tests/test_doc_facts.py` danach **129 passed**).
> **Lint-Zuwächse in der eigenen Datei behoben (F-C), gemessen:** `tests/test_doc_facts.py` hatte unter
> den Defaults **3** Befunde (**1× `I001`**, **2× `PLW1510`** — `subprocess.run` ohne `check=`) und
> unter `--select I,UP,E,F,W` **9**. Beide `PLW1510`-Stellen prüfen **absichtlich** Exit-Codes, deshalb
> **kein** `check=True`, sondern die Absicht explizit gemacht: `check=False` mit Begründungskommentar an
> beiden Stellen (im F1-Test, wo der Befund das Subject ist, und im Exit-Code-Test, wo der
> Rückgabewert das Subject ist). `I001` ist durch den mehrzeiligen `report`-Import behoben. Ergebnis
> **`tests/test_doc_facts.py`: Defaults 3 → 0**, `--select I,UP,E,F,W` **9 → 7** (die verbleibenden
> **7** `E501` sind vorbestehend).
> **`ruff` über alle acht geänderten Nicht-Plan-Dateien, beide Invocations.** **Definition,
> damit die Zahlen reproduzierbar sind:** gezählt werden die **Befunde je Datei** (die
> `ruff check`-Treffer, ein Treffer je Regelverstoß), **einmal je Datei**; **HEAD** (Inhalt von
> `git show HEAD:<pfad>`, über `--stdin-filename` unter demselben Pfad geprüft, damit die
> Konfigurationsauflösung identisch ist) gegen den **Working Tree**; Summen über die **acht**
> geänderten Nicht-Plan-Dateien. **Eigene Messung dieser Task (ruff 0.16.3, keine
> ruff-Config im Repo):** Defaults `docs.py` **0 → 0**, `report.py` **0 → 0**,
> `consistency-check.py` **2 → 2** (`EXE001`, `I001` — beide vorbestehend),
> `docs_freshness.py` **0 → 0**, `test_doc_facts.py` **0 → 0**, `test_doc_freshness.py` **0 → 0**,
> `test_doc_index.py` **0 → 0**, `test_doc_wiki.py` **0 → 0**; **Summe Defaults 2 → 2**.
> **`--select I,UP,E,F,W`:** **2 → 1**, **1 → 1**, **23 → 24**, **1 → 1**, **8 → 7**, **5 → 3**,
> **4 → 3**, **3 → 2**; **Summe `--select I,UP,E,F,W` 47 → 42**. **Korrektur einer früheren
> Notiz-Fassung, die für die Defaults „5 → 2“ schrieb:** die **5** waren nie gemessen —
> mit der oben definierten Zählung ist die HEAD-Summe **2** und die Working-Tree-Summe **2**,
> also **2 → 2**. **Abweichung zur Review-Messung, offen benannt:** das Stufe-2-Review
> misst die Defaults als **4 → 2**; die **2** der Zielseite stimmt mit der hier gemessenen
> überein, die **4** der HEAD-Seite nicht — nach der oben festgelegten Definition sind es
> **2** (`EXE001` + `I001` in `consistency-check.py`; alle sieben übrigen Dateien sind auf
> HEAD ruff-clean in der Default-Regelmenge). **Welche Zahl gilt, ist eine Frage der
> Zähldefinition, nicht des Codes** — beide Seiten sind in `.tmp/` nachmessbar.
> Keine neue Fehlerklasse; der einzige Zuwachs bleibt das eine
> `E402` im Runner für das neue `from lib.io import load_yaml_file` (gleiche Klasse wie die 14
> vorbestehenden, die der `sys.path`-Bootstrap erzeugt).
> **Befund aus der W2-Welle mitgenommen — `tests/test_doc_facts.py::test_existing_docs_checks_keep_signature_and_severity`
> (`:2198`):** Der V4-Teil baute das **Vor-E-5**-Fixture (`docs/api/orphan.md` plus README **ohne**
> `##`-Region `Documentation Index`) und war seit W2-6 grün **über den fail-closed-Pfad**
> (`_v4_region_finding`), **nicht** über den Orphan-Pfad, den der Docstring behauptete — E-5 hat die
> Per-Seiten-Lesart entfernt, `docs/api/orphan.md` ist kein V4-Gegenstand mehr. **Korrigiert:** das
> Fixture ist jetzt ein **E-5-Baum** (Index-Region mit einer verlinkten Kategorie `docs/guides/` und
> einer **deklarierten, unverlinkten** `docs/se-cascade/`), der Test **behauptet** den
> Kategorie-Fund und prüft ihn in beide Richtungen (die Kategorie steht in der Message, die
> verlinkte **nicht**); der **fail-closed**-Fall ist als **zweiter**, ausdrücklich benannter Block
> mit eigener Fixture erhalten. Der Docstring nennt jetzt beide Regeln und benennt die Korrektur.
> **Offene, gemessene Abweichung — die Verifikationszeile 2 der W2-Shell-Prüfung ist unerreichbar
> (Owner `developer` für die Fixture-Seite, Termin offen; hier ausdrücklich **nicht** umgangen).**
> `bash tests/scenarios/run.sh 50 51 52 54 55 56` liefert **0/6** (Exit 1) — und die **Baseline war
> ebenfalls 0/6**, gemessen **vor** der ersten Änderung dieser Task. W2-7 hat also nicht die Rotheit
> erzeugt, sondern die **Zahl** der Errors erhöht: **1 → 235** (Baseline: `docs.readme_index`, aus
> W2-6/E-5; nach W2-7 zusätzlich V1 52 W, V2 207 E, V3 27 E, V5 1 W, V6 3 W, V7 10 W). **Gemessene
> Ursache, die nicht an der Common-Gate-Semantik liegt:** `_run_consistency_checks(agent_meta_root)`
> (`scripts/lib/cli_commands.py:150-174`, aufgerufen aus `:975`) läuft über den **agent-meta-Checkout**,
> nicht über das Szenario-Projekt — im erhaltenen `validate.log` eines Szenario-Laufs stehen **301**
> `docs.`-Findings aus **allen sieben** Checks, obwohl die eingespielte Fixture-`project.yaml` den
> Schlüssel **nicht** setzt (im Temp-Verzeichnis nachgemessen). **Konsequenz, ausdrücklich
> festgehalten:** die Plan-Akzeptanz „in allen Szenario-Fixtures sind V1–V9 **vollständig** No-op
> (AC-38)" ist über **diesen** Shell-Aufruf **nicht messbar** — die Checks sehen die Fixture nie.
> **Was stattdessen geprüft wird und prüfbar ist**, ist der Kern von AC-38 in
> `tests/test_doc_freshness.py::test_the_scenario_configs_never_set_the_common_gate` (`:511`): **alle
> 63** Fixture-Dateien `tests/scenarios/configs/*.project.yaml` wurden gemessen — **0** davon
> enthalten den Text `docs-consolidation` (auch nicht in einem Kommentar), **0** haben einen
> geparsten `docs-consolidation`-Block, und **0** setzen `enabled` **explizit** (also auch keiner auf
> `false`). Der Test pinnt jetzt genau das: er läuft über **alle** Fixtures, nicht nur über `5[0-6]-*`
> — gemessen umfasst dieses Glob **7** Dateien (50, 51, 52, **53**, 54, 55, 56), während `run.sh` nur
> sechs davon startet. **Zusätzlich geprüft und nicht vorhanden:** **0** Treffer auf alternative
> Schreibweisen (`docs[-_]consolidation`, `documentation[-_]consolidation`) in irgendeiner Einrückung.
> **Konsequenz für den Plan, ohne ihn zu ändern:** die Zeile ist als **offene Abweichung** zu führen,
> nicht als erfülltes Gate; die Korrekturbedürftigkeit (entweder `_run_consistency_checks` auf das
> Szenario-Projekt umstellen oder die Zeile durch den direkten Test ersetzen) liegt beim Plan-Protokoll,
> nicht bei dieser Task.
> **Und hier ist der Befund von Gewicht dieser Welle, ohne Deckung:** weder `W-VALIDATE-ROT`
> noch `W2-GATE-ERRORS` führen diese Szenario-Zeile, und `scripts/lib/cli_commands.py`
> steht in **keiner** `Files:`-Liste des Plans — also **kein** Task, **kein** Termin und
> **kein** gedeckter Owner für ihre Unerreichbarkeit.
> **Der zweite gemeldete BLOCKER ist aufgelöst:** die beiden Nicht-Registrierungs-Pins für **V2** und
> **V7** lagen in `tests/test_doc_index.py:870-890` und `tests/test_doc_wiki.py:379-391` und damit
> außerhalb der ursprünglichen Schreibmenge; der Parent hat die Ownership für **genau diese zwei
> Testdateien** übertragen, **ausschließlich** zum Ersetzen der Pins. Beide sind jetzt durch positive
> Pins ersetzt (siehe den Absatz zur Pin-Ersetzung oben) — die Verifikationszeile 1 ist damit grün.
> **Nicht** angefasst wurden dort: irgendeine der in W2-6 bzw. W2-3 implementierten Prüfungen, der
> Modulkopf und alle anderen Tests beider Dateien.
> **Zwei Sollwert-Ist-Differenzen gegen die W-GATE-Tabelle, gemessen — die Tabelle wird hier
> ausdrücklich NICHT geändert, nur ihre Korrekturbedürftigkeit benannt:** (a) **`docs.docs_facts_fresh`
> (V6) liefert WARNING statt ERROR.** Gemessen: **3** Findings, alle Severity **WARNING**, alle mit
> `file == "config/doc-facts-expected.yaml"`; die Tabelle (Abschnitt „W2 — Verifikation", Zeile
> `docs.docs_facts_fresh (V6)`) fordert „planmäßig rot (ERROR)". **Ursache:** `V6_SEVERITY_BY_KIND`
> in `docs_freshness.py:385-389` stuft die Art `missing-in-expected` als **WARNING** und die beiden
> ERROR-Arten (`handedit`, `expected-mismatch`) als ERROR; am echten Baum ist **nur** die
> WARNING-Art vertreten (die ERROR-Arten liefern **0**), weil die gerenderten `DOCS_*`-Blöcke erst ab
> **W3-7** existieren. Der *Wert* „rot" ist erfüllt, die *Severity* nicht. (b)
> **`docs.role_generation_parity` (V5) liefert 1 statt 0.** Gemessen: **1** Finding, Severity
> **WARNING**, `file == ".meta-config/project.yaml"`, Rolle `se-component-requirements`; die Tabelle
> fordert **0** mit der Begründung, `compute_active_roles()` schließe das deaktivierte Gate.
> **Ursache:** das ist gerade **nicht** der Fall — `resolve_activation_gates` liefert die Gruppe mit
> `enabled: false`, die deklarierte Rolle bleibt also in der Differenzmenge, und `_v5_severity` stuft
> ein **geschlossenes** Gate als WARNING (F21-Umkehrung: geschlossen = Entscheidung, nicht Defekt).
> Beide Zeilen brauchen eine Korrektur der **Erwartungswert-Spalte** (Wert und/oder
> Severity) durch das W2-Review-Protokoll; von dieser Task wird keine K-ID erfunden.
> **Die Zuweisung an das W2-Review-Protokoll ist ausdrücklich OFFEN:** die Tabelle
> `W2-GATE-ERRORS` wird von dieser Task **nicht** geändert, und Termin **und** Owner für
> beide Zeilen sind noch nicht gesetzt. Ein Korrektur-Auftrag existiert dafür **nicht**.
> **`kind` von V6 — Einordnung, nicht Lücke der F1-Promotion, mit Beleg:** `kind` bleibt ein reines
> Instanzattribut und erscheint **nicht** im `--json`. Das ist **kein** Versehen der F1-Promotion:
> (i) W2-7 Schritt 4 und die `Interfaces:` dieser Task nennen ausdrücklich **nur** `line` und `branch`;
> (ii) **IC-05** (`spec:947-994`), der bindende IC für V1…V9, nennt weder `line`/`branch` **noch**
> `kind`; (iii) die Spec formuliert das `kind` als **Attribut des Findings** (AC-36,
> `spec:1954`: „V6 meldet dafür ein `Finding(severity=ERROR, check="docs.docs_facts_fresh",
> kind="expected-mismatch")`") — verlangt aber weder ein Dataclass-Feld noch eine JSON-Serialisierung,
> und der Finding **trägt** `kind` weiterhin auf der Instanz; (iv) die W-GATE-Kommandos der Wellen
> lesen `check`, `severity`, `file` und nie `kind`. **Nicht behoben, mit Begründung:** ein Feld `kind`
> in `Finding` würde in **jedem** Finding des `--json`-Reports einen neuen Schlüssel erzeugen — eine
> **Verhaltensänderung** des Report-Schemas ohne IC und ohne Akzeptanzpunkt; der Default müsste zudem
> frei gewählt werden (`""` neben `None`/`""` bei `line`/`branch` wäre die konsistente Wahl).
> Empfehlung an eine Folge-Task: entweder `kind` als Feld mit Default `""` **plus** Serialisierung
> (dann ist es eine Ausgabe-Erweiterung, die ins Review gehört) oder eine explizite
> „V6-intern, nicht Teil des Report-Vertrags"-Festlegung in IC-05. Der Docstring in
> `docs_freshness.py:488-496` nennt die Zwei-Teile-Form bereits vollständig.
> **Verifikation 1–5, alle Läufe gemessen (ungefilterte Roh-Ausgabe, umgeleitet und aus der Datei
> gelesen, weil `rtk` pytest-Fehlschläge filtert):** (1) `python3 -m pytest tests/test_doc_facts.py
> tests/test_doc_freshness.py tests/test_doc_wiki.py tests/test_doc_index.py
> tests/test_doc_freshness_v5.py tests/test_doc_facts_expected.py -q` ⇒ **`236 passed`, Exit 0** —
> **beide** Verifikations-Tests sind grün, die **beiden** V2-/V7-Pins sind durch positive Pins
> ersetzt. Zustand davor (Baseline vor der Task): **`232 passed`, Exit 0**; Zustand nach der
> Registrierung, vor der Pin-Übernahme: **`2 failed, 234 passed`**. Volle Suite zur
> Regressionskontrolle: `python3 -m pytest tests/ -q` ⇒ **`3420 passed, 1 skipped, 35 errors`**,
> **0 failed**; die **35** Errors sind ausschließlich `tests/browser/*` mit
> `pytest_socket.SocketBlockedError` (dieser Sandbox fehlt der Socket-Zugriff für den
> `admin_server`-Fixture) und damit umgebungsbedingt, nicht durch diese Task. (2) **unreachable,
> als offene Abweichung dokumentiert** (siehe den Absatz weiter oben): `0/6`, Exit 1, Baseline
> ebenfalls `0/6`; W2-7 erhöht die Error-Zahl **1 → 235**, nicht die Rotheit. (3) `python3
> scripts/consistency-check.py --json | python3 -c …` ⇒ Schlüsselsatz
> `['branch', 'check', 'file', 'line', 'message', 'severity', 'suggestion']`, also mit **`line`** und
> **`branch`**. (4) `python3 -m compileall -q scripts/lib` ⇒ **Exit 0**; `ruff` (0.16.3), **Defaults**:
> `docs.py` **0 → 0**, `report.py` **0 → 0**, `consistency-check.py` **2 → 2** (`EXE001` Shebang ohne
> Ausführbit, `I001` Importreihenfolge `frontmatter` vor `fanout_contracts`) — **beide vorbestehend**,
> gegen `git show HEAD:<datei>` gemessen; die beiden neu übernommenen Testdateien ebenfalls **0 → 0**
> (`test_doc_index.py`, `test_doc_wiki.py`). Mit **`--select I,UP,E,F,W`**: `docs.py` **2 → 1**
> (E501), `report.py` **1 → 1** (E501, vorbestehend), `consistency-check.py` **23 → 24**; die Zunahme
> ist **genau ein `E402`** für das neue `from lib.io import load_yaml_file` — dieselbe Klasse wie die
> **14** vorbestehenden `E402`, die der `sys.path`-Bootstrap dieses Laufs erzeugt; keine neue
> Fehlerklasse, Produktions-Gesamt **26 → 26**. `test_doc_index.py` **4 → 3** und `test_doc_wiki.py`
> **3 → 2** (E501), also beide **verbessert**. (5) Die Rohzeile ``python3 scripts/consistency-check.py
> → 0`` ist **aufgehoben** und wird **nicht** behauptet; der Ist-Stand steht oben nach `check`
> gruppiert.
> **Exit-Code-Vertrag, nach dem Pin-Umschreiben erneut end-to-end gemessen:** **0** (0 Errors, Gate zu)
> ⇒ `{total 0, errors 0, warnings 0}`, Prozess-Exit **0** (Textbericht ebenso **0**); **1** (genau
> 1 Error) ⇒ `{total 1, errors 1}`, Exit **1** (Textbericht **1**), und der eine Error ist ein
> `docs.no_manual_counts`-V1a-Fund mit `line == 1`, `branch == "V1a"`; **2** (`--file` auf eine
> nicht existierende Datei) ⇒ Exit **2**. Die Doku `scripts/consistency-check.py:24-26` ist
> unverändert und bleibt gültig.
> **Docstring-Korrekturen, gemessen und nur in der eigenen Schreibmenge:** in `docs.py:3-6` standen die
> Anker ``scripts/consistency-check.py:52-56`` und ``:199-201`` — vor W2-7 korrekt, durch die
> Registrierung **falsch geworden**. Sie zeigen jetzt ``:53-63`` (der Importblock) sowie ``:283-284``
> (die zwei ungegateten Altchecks) und ``:292-294`` (der gegatete V1…V7-Block), jeweils am echten
> Dateistand nachgemessen. **Bewusst nicht angefasst**, weil vorbestehend und nicht durch diese Task
> falsch geworden: `docs.py:8-15` („two family modules") — vor W2-7 durch W2-3/W2-4/W2-6 überholt,
> **nicht** durch W2-7.
> **Stale Docstrings außerhalb der Schreibmenge, gemeldet und nicht geöffnet.** **Zwei** bleiben
> übrig, nachdem `docs_freshness.py` mit dem F-A-Grant dazukam (deren Docstring ist dort jetzt
> korrigiert): `scripts/lib/consistency/docs_wiki.py:35-40` behauptet, `Finding` trage kein `line` und
> kein `branch`-Feld, und `scripts/lib/consistency/docs_links.py:450-452` behauptet, `Finding` habe
> keines der beiden Felder und W2-7 müsse sie hochziehen — beides ist seit der F1-Promotion falsch.
> **Nächster Owner:** `docs_wiki.py` → **W6-2** (der Plan führt die Datei in dessen `Files:`);
> `docs_links.py` → **kein** Owner im Plan, die Datei wird von **keiner** Task als Write-Menge
> geführt — das ist selbst der Befund, und er wird hier **nicht** erfunden. Termin und Owner sind vom
> Review-Protokoll zu setzen.
> **Überlappungs-Pin, gemessen:** `tests/test_plan_ledger_writer.py::test_validate_plan_reaches_the_expected_overlap_verdict`
> ist **grün** — der gepflegte Pin-Literalwert `== 18` (gepflegt in `0d2e5c13`) **trifft weiterhin
> zu**, der Assert wurde **nicht** abgeschwächt und die Zahl **nicht** angefasst. Der Tripwire
> wurde nach dem Schreiben dieser Notiz erneut gemessen, weil die Schreibmengen des Prüfers aus den
> im Task-Text genannten Dateinamen gebaut werden.
> **Write-Menge-Hygiene dieser Notiz:** keine `###`-Zeile, keine Zeile mit beginnendem
> `Depends on:`, keine Doppelpunktform der Feldnamen im Fließtext (sonst extrahiert
> `_FILES_FIELD_RE` eine Phantom-Write-Menge); `files_touched("W2-7")` bleibt `()`.

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
(`scripts/lib/consistency/docs_freshness.py:63` = `V1_SCAN_RELPATHS`; Rev. 0.6 / K48 — vor dem
W2-0-Split `docs.py:158`); V2 liest `docs/INDEX.md` als **Soll**, nicht als
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
| **V7** meldet **10** Wiki-Seiten `type: "Architecture"` **ohne** `derived-from` (WARNING) — **Rev. 0.6 / K51: von 11 auf 10 korrigiert** (K24/K36 hatten 10 auf 11 gehoben; **K24 war eine Fehlmessung** — ein `type:`-Zeilen-Scan über ganze Dateien zählte den **Body**-Wertelisten-Kommentar `type: "Concept" # Concept | Architecture | …` in `knowledge/wiki/concepts/core-principle-knowledge-engine.md:46` mit, dessen Seite den Typ `"Concept"` trägt. Über **Frontmatter** gemessen (`:2` in allen 10 Dateien) sind es **10**: `architecture.md`, `architecture-agent-roles.md`, `architecture-dev-workflow.md`, `architecture-external-skills.md`, `architecture-layer-model.md`, `architecture-prompt-modernization.md`, `architecture-se-cascade.md`, `architecture-sync-flow.md`, `architecture-versioning.md`, `core-principles-overview.md` — alle unter `knowledge/wiki/concepts/`) | `knowledge/wiki/concepts/architecture*.md:2` u. a.; **null** `derived-from:` im Baum | **W5-3** |
| **V3** meldet **2** tote Layout-Verweise auf `howto/setup/`, `howto/features/` (**ERROR**) | `README.md:722-723` (**K30**); im Baum existiert nur `howto/configs/project.yaml.example` | **2** → **W8-2** · **25** (`docs/**`) → **Follow-up `F-DOCS-LINKS-2026-09-27`, Termin 2026-10-11** |
| **V2** meldet jede getrackte `docs/**/*.md` ohne Eintrag (ERROR) | `docs/INDEX.md` existiert **nicht** | **W3-6** |
| **V9** meldet den Altbestand an `*.sync-backup-*` als **WARNING** und wird ihn **nicht** abräumen | W8-4-Akzeptanz: die Altlasten bleiben **unangetastet**; FI-10 („lokale Aufräumaktion, kein Spec-Gegenstand") | **kein Termin 0** (geduldet, FI-10) — zur **Zahl** siehe Fußnote ⁴ |
| **V4** (Rev. 0.7 / E-5) meldet **1** deklarierte README-Index-Kategorie ohne Link (**ERROR**) | `README.md:378` deklariert `docs/se-cascade/`, ohne Link in der Region `:347`…`:381` | **kein Termin 0** in W0–W8 — Follow-up `F-DOCS-README-INDEX-SE-2026-09-27`, Termin **2026-10-11** (siehe Fußnote **⁶**) |

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
| `docs.internal_links` (V3) | ERROR | rot | rot | rot | rot | rot | rot | **0** im AC-30-Scope⁵ | **W8-2** (2 Layout-Findings) · Follow-up `F-DOCS-LINKS-2026-09-27`, Termin 2026-10-11 (25 Link-Findings) | `developer` |
| `docs.readme_index` (V4) | ERROR | **1**⁶ | **1**⁶ | **1**⁶ | **1**⁶ | **1**⁶ | **1**⁶ | **0**⁶ | — | `developer` (W2-6 für den Scope) · Follow-up `F-DOCS-README-INDEX-SE-2026-09-27`, Termin **2026-10-11** |
| `docs.role_generation_parity` (V5) | WARNING | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — | `developer` (W2-4) |
| `docs.docs_facts_fresh` (V6) | ERROR | rot | **0** | 0 | 0 | 0 | 0 | 0 | **W3-7** | `developer` (W3-7) |
| `docs.wiki_staleness` (V7) | WARNING | rot | rot | rot | **0** | 0 | 0 | 0 | **W5-3** | `tester` (W5-3) |
| `docs.spec_plan_path_convention` (V8) | WARNING | n. i. | n. i. | n. i. | n. i. | 0 | 0 | 0 | — | `tester` (W6-2) |
| `docs.stale_backups` (V9) | WARNING | n. i. | n. i. | n. i. | n. i. | n. i. | n. i. | **geduldet**, kein Sollwert⁴ | **keiner** (FI-10) | `tester` (W8-4) |
| **`docs-checks`** (Counter) | — | *(Dokuzeile)* | *(Dokuzeile)* | *(Dokuzeile)* | *(Dokuzeile)* | *(Dokuzeile)* | *(Dokuzeile)* | *(Dokuzeile)* | — | `developer` (W2-7) |

**Rev. 0.7 / E-5 — die Spalte W2-7 der V4-Zeile heißt nicht „nicht implementiert", obwohl V4
kein neuer Check ist.** V4 ist **heute bereits registriert** (`scripts/consistency-check.py:53`/`:201`)
und liefert ab **W2-6** Findings — die Spalte **W2-7** ist die **Wellen-Gate-Spalte**, nicht die
Startwellen-Spalte. **Deshalb** steht dort der Wert des Wellenabschlusses (**1**) und **nicht**
`n. i.`. **Die Verschlechterungsregel 1** (Startwelle) hat dafür eine **ausdrücklich benannte
Ausnahme** für V4: Baseline **ab W2-6** = **1**.

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
   `howto/features/` fehlen; V7: **10** `type: "Architecture"`-Seiten ohne `derived-from` —
   **Rev. 0.6 / K51: von 11 auf 10 korrigiert** (K24 war eine **Fehlmessung** über den
   **Body**-Kommentar `core-principle-knowledge-engine.md:46`; über **Frontmatter** gemessen **10**,
   alle unter `knowledge/wiki/concepts/`; die Messung vom 2026-09-26 mit 10 war richtig)) und
   stehen in Verbindung mit einem **konkreten Termin und Owner**. Die **0**-Werte für **V4** und
   **V5** sind
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

 ⁵ **V3 in den Spalten W2…W8 — AC-30-Scope und Follow-up (Rev. 0.6, U-2/K22; **K37**, Review-Befund M9:
 diese Fußnote fehlte, obwohl sie in der V3-Zeile der Tabelle und im W8-Block referenziert
 wurde).** V3 (`docs.internal_links`, **ERROR**, IC-05) ist nach W2-7 in **drei Klassen** rot
 (Baseline-Messung 2026-09-27, **27** Findings gesamt):

 | Klasse | `branch` | Anzahl | Wo | Termin 0 | Owner |
 |---|---|---|---|---|---|
 | README-Layout | `layout` | **2** | `README.md:722` (`howto/setup/`), `README.md:723` (`howto/features/`) — **im** AC-30-Scope | **W8-2** | `developer` (Task W8-2) |
 | docs-Link-Fundstellen | `link` | **25** | ausschließlich `docs/**` — `docs/guides` 10 · `docs/concepts` 13 (**8** in `archive/`) · `docs/superpowers/plans/` 2; **live** = **17** | **kein** Termin 0 in W0–W8; **Follow-up `F-DOCS-LINKS-2026-09-27`**, Termin **2026-10-11** | `developer` |
 | `llms.txt` | — | **0** | — | — | — |

**Lesart der Spalten W2…W7:** V3 = „**rot**" bedeutet **beide** Klassen sind rot; das ist
 planmäßig und **kein** Fehlschlag der Welle. **Lesart der Spalte W8:** „**0 im AC-30-Scope⁵**"
 bedeutet **0** Findings mit `file` ∈ {`README.md`, `llms.txt`}; die **25** unter `docs/**` bleiben
 **erwartet rot** und sind Follow-up, **kein** AC und **kein** Termin 0. **Folge:** V3 ist als
 Zählwert in W0…W8 **nie 0** ⇒ `consistency-check.py → 0` und `sync.py --validate → 0` sind
 **dauerhaft unerreichbar**; maßgeblich ist die **Deltasperre** (Owner `validator`, Baseline
 **W3-7**), die Severity-Frage ist **OQ10** (Spec §11.1, Frist **vor W8-4**). Volltext in der
  Tabelle `W2-GATE-V3-KLASSEN` im W2-Block.

 **⁶ **V4 in den Spalten W2…W8 — README-Index-Scope (Rev. 0.7, E-5/K54; neue Fußnote, damit die
 in der V4-Zeile verwendete Marke definiert ist).** V4 (`docs.readme_index`, **ERROR**, IC-05)
 prüft seit W2-6 **nicht** mehr, ob alle **205** nicht-Archiv-`docs/**.md` in `README.md` verlinkt
 sind (das wäre der verworfene Zustand mit **193** ERROR-Findings — **K60** —, `--validate`
 blockiert und zwei
 Volltests rot), sondern den **README-Index-Scope**: die `##`-Region `Documentation Index` in
 `README.md` (heute `:347`…`:381`) und deren **deklarierte** `docs/`-Kategorien (gemessen **7**).

 | Klasse | Anzahl | Wo | Termin 0 | Owner |
 |---|---|---|---|---|
 | deklarierte Kategorie ohne Link | **1** | `docs/se-cascade/` — deklariert in `README.md:378`, kein `docs/se-cascade/`-Link innerhalb der Region (der Verweis `:654` liegt außerhalb) | **kein** Termin 0 in W0–W8; **Follow-up `F-DOCS-README-INDEX-SE-2026-09-27`**, Termin **2026-10-11** | `developer` |
 | nicht im README verlinkte `docs/`-Seiten | **193** (**K60**; Herleitung `205 − 12`, weil die **14** genannten `docs/`-Pfade **12** `.md` + **2** `.html` sind) | **kein** V4-Finding mehr (E-5) — **Follow-up `F-DOCS-README-INDEX-2026-09-27`**, Termin **2026-10-11**; Nachweis = **Issue-Liste + once-count außerhalb V4** | **kein** Termin 0; **kein** AC | `developer` |
 | fehlende `##`-Region | **0** (fail-closed: **1** Finding, falls sie fehlt) | `README.md` | — | — |

 **Grenze gegen V2 (K55):** V2 (`docs.docs_index_completeness`) liest `docs/INDEX.md` und ist
 **seiten**-genau — **alle** nicht-Archiv-`docs/**.md` (ohne `docs/INDEX.md`) müssen dort stehen; das
 wird ab **W3-6** erfüllbar, weil `docs/INDEX.md` **100 % generiert** ist (OQ6/OQ8). **Die 193 sind
 genau die Menge, die V2 abdeckt** — sie sind eine Eigenschaft des Formats (die README ist ein
 **kuratierter** Einstieg, `docs/INDEX.md` der **vollständige** Index), kein Fehler. **Grenze gegen
 V3:** V3 prüft, ob ein **Linkziel existiert**; V4 prüft **nie** ein Linkziel. **Keine
 Doppelmeldung** — ein toter Link in der Index-Region ist ein V3-Finding und **kein** V4-Finding,
 und V4 kann rot sein, während V3 grün ist. **Volltext:** Spec §17.11.2.

**Verschlechterungsregel (unabhängig von den Einzelwerten, in jeder Welle; neu gefasst, RVW2-1/RVW2-4):**
1. **Startwelle je Check:** ein V-Check darf **erst ab seiner IC-05-Startwelle** Findings liefern
   (V1–V7 ab **W2-7**, V8 ab **W6-2**, V9 ab **W8-4**). Findings eines Checks **vor** seiner
   Startwelle sind ein **Befund** (verfrühte Registrierung). **Rev. 0.7 / E-5 — die einzige
   Ausnahme, ausdrücklich benannt:** **V4** ist **kein** neuer Check, sondern ein **bereits
   registrierter** Altcheck (`scripts/consistency-check.py:53`/`:201`); er liefert ab **W2-6**
   Findings und **nicht** erst ab W2-7. Das ist **keine** verfrühte Registrierung, sondern der
   Zustand vor und nach W2-6. **Auswirkung auf die Regel:** für V4 beginnt die Verschlechterungs-
   messung ab **W2-6** (Baseline = **1**), für V1/V2/V3/V5/V6/V7 unverändert ab **W2-7**.
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
Hochstufung dreht nur die **Severity** (Severity-Wahl `docs_freshness.py:285`; Rev. 0.6 / K48 — vor
dem W2-0-Split `docs.py:359`), nicht die **Abdeckung** — bei geschlossener
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
  und bleibt bis **W8-2** rot (`README.md:722-723` (**K30**) verweisen auf `howto/setup/` und
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

**Files:** Modify `.meta-config/project.yaml` (`:61-63`), `tests/test_docs_consolidation_migration.py`,
**`scripts/lib/consistency/docs_wiki.py`** (**Rev. 0.6 / K18: V8 gehört zur Wiki-/Bestands-Familie**;
vor W2-0 `docs.py`)
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
`python3 scripts/sync.py --validate` → **planmäßig rot** (`W-VALIDATE-ROT`; **Rev. 0.6 (K22):**
V3 ist ERROR und bleibt **unter `docs/**` dauerhaft** rot — Follow-up `F-DOCS-LINKS-2026-09-27`,
Termin 2026-10-11 —; die Deprecation-WARNING ist **irrelevant** für den Exit, weil
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
  ist bedingt; Rev. 0.6 (K22): zusätzlich dauerhaft unerreichbar.** **In W8 ist V3 nach W8-2 im
  AC-30-Scope grün**; die **25** `docs/**`-Findings bleiben **ERROR** und halten `--validate`
  deshalb **auch nach W8-4** rot ⇒ maßgeblich ist die **Deltasperre**, nicht `→ 0`; **V2** ist ab
  **W8-1**
  rot (neue `docs/**/*.md`) und wird erst mit dem **Abschluss-Sync-Lauf in W8-4** (Schritt 5)
  wieder 0 — **RVW3-1: die Formulierung „nach W8-2 alle Doku-ERROR-Checks 0" war falsch** und ist
  korrigiert; W8-2 und W8-3 führen keinen Sync. V9 ist **WARNING** — `_run_consistency_checks`
  zählt nur `Severity.ERROR` (`scripts/lib/cli_commands.py:174`), V9 bricht `--validate` also
  **nicht**. **Restbedingung, die nicht gemessen ist:** `--validate` summiert **alle** ERROR-Findings
  des Repo. Ist der repo-weite Altbestand `errors > 0` (Messung in **W3-7**,
  W3-BASELINE-STRICT), bleibt `→ 0` unerreichbar und maßgeblich ist die **Deltasperre**. Owner
   `validator`, Entscheidungspunkt **W3-7**. **K44 (Rev. 0.6, Review-Befund N4): der bisherige
   Nachsatz „spätester Termin 0 **W8-4**" ist aus diesem Bullet entfernt** — er widersprach zwei
   Sätze früher demselben Bullet („auch nach W8-4 rot ⇒ maßgeblich ist die Deltasperre, nicht `→ 0`").
   **Korrigierte Fassung: `--validate` hat keinen Termin 0** (K27, Begründung: V3 bleibt **ERROR**
   unter `docs/**`); maßgeblich ist die **Deltasperre**. „W8-4" bleibt **ausschließlich** der Termin
   für **V2** (Check-Erwartungswert, Abschluss-Sync-Lauf Schritt 5) und der Termin der
   **Entscheidungsfrist von OQ10** — **nicht** ein Termin 0 für `--validate`. Grundlage **Spec §6(b) /
   §10, Aufzählungspunkt `--validate`**. **Der Sollwert wird nicht abgesenkt**, sondern als
   Dokuzeile ohne Sollwert geführt und durch die Deltasperre ersetzt.
- ~~`python3 scripts/consistency-check.py --strict` → **0** (V1a **und** V3 ohne Befund; V9 meldet die
  179 Altlasten als **WARNING** — lokale Aufräumaktion FI-10, kein Fehler)~~
  **UMGESTELLT (Rev. 0.5, RVW-3) — die Klammer war in sich widersprüchlich.** Sie verlangte
  gleichzeitig „V1a und V3 ohne Befund" und „V9 meldet 179 WARNINGs", verlangte mit `--strict`
  aber null **Warnings** — bei `--strict` setzt `consistency-check.py:273-274` den Exit 1
  **auch** für die V9-Warnings. **Maßgeblich ist W-GATE + W-GATE-TABLE, Spalte W8:** V1 0 ·
  **V3 0 im AC-30-Scope** (W8-2 behebt `README.md:722-723` — **K23: das sind die beiden
  Layout-Findings**; die **25** `docs/**`-Link-Findings bleiben nach U-2 rot und sind
  Follow-up `F-DOCS-LINKS-2026-09-27`, Termin **2026-10-11** — Fußnote ⁵) ·
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
`git checkout .meta-config/project.yaml`, V9-Block aus **`scripts/lib/consistency/docs_index.py`**
entfernen (Rev. 0.6 / K18; vor W2-0 aus `docs.py`).
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

### W8-2: M-8 — Tote interne Verweise (AC-30) — **Rev. 0.6, K22: Scope `README.md` + `llms.txt` (U-2)**

**Files:** Modify `README.md`, `tests/test_docs_consolidation_migration.py`
**Interfaces:** Produces: `README.md:722` (`howto/setup/`) und `README.md:723` (`howto/features/`)
auf existierende Ziele umgeschrieben bzw. entfernt — das sind **genau die zwei** verbleibenden
V3-Fundstellen (beide `branch=="layout"`, beide in `README.md`); `llms.txt` ist bereits bei **0**;
`test_no_dead_internal_links_after_migration`. Consumes: W4-2, W5-2, W6-1.
**Agent:** developer · **Depends on:** W8-1 · **parallel_group:** PG-5
**Ziel-AK (AC):** **AC-30** (IC-17, M-8) · **V-Check:** **V3**
**Akzeptanz (Rev. 0.6, K22 — **wesentlich geändert**):** **`README.md` und `llms.txt`** sind frei
von Findings auf **relative interne** Links; V3 liefert **im AC-30-Scope** keine Findings mehr.
`docs/**` ist **nicht mehr** AC-30-Scope — die **25** dortigen Link-Findings bleiben **rot** und
sind als **Follow-up `F-DOCS-LINKS-2026-09-27`** (Owner `developer`, Termin **2026-10-11**)
geführt. **Rev. 0.6 korrigiert außerdem zwei Belegstellen dieser Task (K23):** die Fundstellen sind
**`README.md:722`/`:723`**, nicht `:721-723` (`:721` `howto/` und `:724` `howto/configs/` existieren);
und `README.md:724` („`CLAUDE.md` als Template-Config", F15) ist **kein** V3-Finding — die Stelle ist
eine Prosazeile im Verzeichnis-Fence und wird nur als **manueller** Befund mitbehoben, falls die
Migration sie ohnehin anfasst. **Weigerungsnachweis, warum W8-2 genügt und kein zusätzlicher Task
nötig ist:** die beiden Findings stehen **in `README.md`**, `README.md` steht in `Files:` dieser Task,
und `V3` ist ihr `V-Check:` — Behebung = zwei Layout-Einträge umschreiben. **Zusicherung:** keine
Umbenennung von Dateien.
**Verifikation:** `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**;
~~`python3 scripts/consistency-check.py --strict` → **0**~~ **unter der Geltungsregel**
(Task-Verifikation, **kein** Welle-Gate; RVW-3 — maßgeblich ist W-GATE, Spalte **W8**).
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: Totverweise umschreiben/entfernen.
- [ ] 3: V3 beobachten — **Erwartungswert `0` im AC-30-Scope** (`README.md`, `llms.txt`);
      Zählwert über `W-GATE` bzw. `W2-GATE-V3-KLASSEN`, **kein** Exit-Code. **Die 25 Findings unter
      `docs/**` bleiben erwartet rot** (K22) und sind **kein** Fehlschlag dieser Task.
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

**Files:** Modify **`scripts/lib/consistency/docs_index.py`** (**Rev. 0.6 / K18: V9 liegt in der
Index-Familie**; vorher `scripts/lib/consistency/docs.py`), `.meta-config/project.yaml` (`:205-221` —
**nur** `PROJECT_STRUCTURE`, M-12), `tests/test_doc_facts.py`. **Kein** neuer `docs-consolidation`-Key —
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
**Modulkonstante** in `scripts/lib/consistency/docs_index.py` (Rev. 0.6) — Muster `V1_SCAN_RELPATHS`,
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
**OQ10 — Entscheidungspunkt dieser Task (K32, Rev. 0.6; neu, s. „Entscheidungs-Tasks").** Zusätzlich
zu **ESCALATION E-2** (V9-Altersschwelle) ist in dieser Task die offene Frage **OQ10** zu
behandeln: **behalten die 25 V3-Findings unter `docs/**` die Severity ERROR, oder wird V3 dort
auf WARNING herabgestuft?** Owner `orchestrator` → `main_chat`, **Frist: vor W8-4** (Spec §11.1).
**Wirkung ohne Entscheidung:** `--validate` bleibt dauerhaft rot, maßgeblich ist die Deltasperre
(`W-VALIDATE-ROT`, DoD Punkt 12). **Wirkung mit Entscheidung (a)** (Herabstufung): IC-05 ist in der
nächsten Spec-Revision zu ändern — **nicht** in dieser Task (RVW3-6); **mit (b)** (ERROR bleibt):
W8-4 ändert an der V3-Severity **nichts**, und der Doku-Endzustand bleibt planmäßig rot.
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
| W2-1 | W2 | developer | W1-6, W0-4 | — (Gate) | AC-07, AC-08 | V1a, V1b | `scripts/lib/consistency/docs.py` (→ wandert in **W2-0** nach `docs_freshness.py`), `tests/fixtures/docs_v1_fixtures.md`, `tests/test_doc_facts.py` (**Rev. 0.5, K16:** zusätzlich Schritt 4 — Rule-3-Eingrenzung in `docs.py` + Sichtbarkeitstest) |
| W2-2 | W2 | developer | W2-1 | — | AC-09 | V3 | `docs.py` (→ wandert in **W2-0** nach `docs_links.py`), `tests/test_doc_facts.py` |
| **W2-0** | W2 | **developer** | **W2-2** | **— (sequenziell, Einstieg der offenen W2)** | Querschnitt (kein neuer AC) | V1a, V1b, V3, V4 + 3 Altchecks (verschoben) | **Rev. 0.6:** `scripts/lib/consistency/docs.py` (**Fassade**), **`docs_links.py`** (Create), **`docs_freshness.py`** (Create), **`tests/test_doc_freshness.py`** (Create, V1-Tests wandern), `tests/test_doc_facts.py` (nur Verschiebung). **Kein** `consistency-check.py`, **kein** `report.py`, **kein** `.meta-config/` |
| **W2-3** | W2 | **developer** | **W2-0** | **PG-2a** (Rev. 0.6) | AC-10 | V7 | **Rev. 0.6:** **`docs_wiki.py`** (Create), **`tests/test_doc_wiki.py`** (Create) — *vorher:* `docs.py`, `tests/test_doc_facts.py` |
| **W2-4** | W2 | **senior-developer** (Rev. 0.7) | **W2-5** (Rev. 0.7; Rev. 0.6; Rev. 0.5: W2-3) | **— (sequenziell, Phase B)** | AC-11 | V5 | **Rev. 0.7 / E-7:** **`docs_freshness_v5.py`** (Create), **`tests/test_doc_freshness_v5.py`** (Create) — *Rev. 0.6:* `docs_freshness.py`, `tests/test_doc_freshness.py`; *Rev. 0.5:* `docs.py`, `tests/test_doc_facts.py` |
| **W2-5** | W2 | **developer** | **W2-0** (Rev. 0.6; Rev. 0.5: W2-4) | **PG-2a** (Rev. 0.6) | AC-36 | V6 | **Rev. 0.6:** `docs_freshness.py`, `tests/test_doc_freshness.py`, `tests/test_doc_facts_expected.py` — *vorher:* `docs.py`, `tests/test_doc_facts_expected.py` |
| **W2-6** | W2 | **developer** | **W2-0** (Rev. 0.6; Rev. 0.5: W2-5) | **PG-2a** (Rev. 0.6) | AC-12 | V2, V4 | **Rev. 0.6:** **`docs_index.py`** (Create), **`tests/test_doc_index.py`** (Create), `docs_links.py` (**nur** V4-Scope — **Rev. 0.7 / E-5**) — *vorher:* `docs.py`, `tests/test_doc_facts.py` |
| **W2-8** | W2 | **senior-developer** (Rev. 0.7) | **W2-4** (Rev. 0.7 — Sequenzierung, unmittelbar vor W2-7) | **— (sequenziell, Phase B)** | AC-11, AC-13 (**kein neuer AC** — Querschnitt) | — (Querschnitt) | **Rev. 0.7 / E-6:** `tests/test_knowledge_engine.py`, `tests/test_sharkord_service_name_migration.py` — **kein** Produktionscode, **kein** `sync.py` |
| **W2-9** | W2 | **senior-developer** (Rev. 0.7) | **W2-0** (Rev. 0.7 — Sequenzierung, Phase 0) | **— (sequenziell, Phase 0)** | Querschnitt (kein AC) | — (Werkzeug) | **Rev. 0.7 / E-8:** `scripts/lib/plan_identity.py` (**Definition**), `scripts/lib/plan_ledger.py` (**bedingt**), **`scripts/lib/consistency/spec_plan.py`** (Dep-Token-Muster, **K71**), `tests/test_plan_identity.py`, `tests/test_plan_ledger_writer.py` |
| W2-7 | W2 | developer | **W2-3, W2-4, W2-5, W2-6, W2-8** (Rev. 0.7 — **W2-8** neu; Rev. 0.6; Rev. 0.5: W2-6) | — (sequenziell, Abschluss) | AC-13, AC-24 | alle | `docs.py` (**nur** `__all__`-Einträge), `scripts/consistency-check.py`, **`scripts/lib/consistency/report.py` (Rev. 0.5, K15 — B-5/E-15: `line`/`branch` als Dataclass-Felder, F1-PROMOTION)**, `tests/test_doc_facts.py` **zweimal**: Modul (bestanden) + **positiver Registrierungs-Pin in Schritt 1 (RVW2-5)** |
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
| W6-2 | W6 | tester | W6-1 | PG-3 | AC-32, AC-28 | V8 | `.meta-config/project.yaml`, `tests/test_docs_consolidation_migration.py`; **Rev. 0.6 (K18): V8 wandert nach `docs_wiki.py`** |
| W7-1 | W7 | knowledge-curator | W6-2 | PG-4 (isoliert) | AC-35 | — | `knowledge/schema.md` |
| W7-2 | W7 | senior-developer | W7-1 | PG-4 | AC-33, AC-34 | V7 | `scripts/lib/knowledge.py`, `.meta-config/project.yaml`, `tests/test_knowledge_index_gen.py` |
| W7-3 | W7 | senior-developer | W7-2 | PG-4 | AC-35, AC-41 | — | `scripts/lib/knowledge.py`, `tests/test_knowledge_index_gen.py` |
| W7-4 | W7 | prompt-engineer | W7-3 | PG-4 | AC-35 | — | `agents/1-generic/knowledge-indexer.md` |
| W7-5 | W7 | knowledge-curator | W7-4 | PG-4 | AC-33/34/35 | V7 | `.meta-config/project.yaml`, `knowledge/wiki/index.md`, `knowledge/wiki/log.md` |
| W8-1 | W8 | requirements | W7-5 | PG-5 | AC-40 | V8 | `docs/plans/…-oq4.md`, `docs/REQUIREMENTS.md` |
| W8-2 | W8 | developer | W8-1 | PG-5 | AC-30 | V3 | `README.md`, `tests/test_docs_consolidation_migration.py` |
| W8-3 | W8 | developer | W8-2 | PG-5 | AC-40 | V1a, V6 | `llms.txt`, `README.md`, `tests/test_docs_consolidation_migration.py` |
| W8-4 | W8 | tester | W8-3 | PG-5 | AC-30, AC-40 | V9 | **`scripts/lib/consistency/docs_index.py`** (Rev. 0.6 / K18: V9-ALTERSSCHWELLE als Modulkonstante, kein Config-Key — RVW2-7; vorher `docs.py`), `.meta-config/project.yaml` (**nur** `PROJECT_STRUCTURE`, M-12), `tests/test_doc_facts.py`; **Schritt 5 (RVW2-6): Abschluss-Sync-Lauf — schreibt `docs/INDEX.md` nicht, der Generator aus W3-6 bleibt Eigentümer** |

**Zyklenprüfung:** Der Graph ist ein **DAG**. **Leitsatz (RVW2-9, korrigiert):** es gibt **keine
Rückwärtskante** (keine Kante von einer höheren auf eine niedrigere Welle) und **keine
Welle-zu-Welle-Rückkante**; zulässig sind Ketten **innerhalb** einer Welle und **Vorwärts**- oder
**Querwellenkanten** (W3-1 hängt an W1-10, W3-4 an W2-1 — beide nachgewiesen unten). Jede
**Querwelle**-Kante wird hier **namentlich** genannt. Die Ketten innerhalb einer Welle sind
W0-2 → {W0-1, W0-3, W0-4, W0-6, W0-7}, W1-1→…→W1-10 (kettenintern), W3-1→…→W3-7,
W4→W5→W6 durchgehend, W7-1→…→W7-5 und W8-1→…→W8-4. **K40 (Rev. 0.6, Review-Befund m7): die
Nennung „W2-1→…→W2-7" als *Kette* ist überholt** — W2 ist seit Rev. 0.6 **keine** Kette mehr,
sondern `W2-1 → W2-2 → W2-0 → {W2-3 ‖ W2-5 ‖ W2-6} → W2-4 → W2-7` mit der Parallelgruppe
**PG-2a**. **Maßgeblich ist der Abschnitt „Ownership-Matrix, DAG-Kantenliste und Zyklenprüfung"**
(dort: vollständige Kantenliste, Zyklenprüfung, Fail-closed-Klausel); dieser Absatz führt die
**übrigen** Wellen und die Querwellenkanten. **Querwellenkanten (vollständig):**
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

## Ownership-Matrix, DAG-Kantenliste und Zyklenprüfung (Rev. 0.6, K20)

**Warum dieser Abschnitt neu ist.** Rev. 0.5 führte die Ownership nur als **eine** Spalte der
Reihenfolge-Matrix und als Fließtext-Regel. Für die Rev. 0.6 reicht das nicht: die Parallelität in
W2 ist nur dann belastbar, wenn **je Datei und Task** nachweisbar ist, wer schreibt und wer liest,
und wenn die Kantenliste **explizit** aufgeschrieben ist. Beides steht hier.

### 1. Ownership-Matrix W2 (Task × Datei: `owns` / `reads`) — **Rev. 0.7: um die Spalten W2-9 und W2-8 sowie 9 Dateizeilen erweitert** (Korrekturrunde 6 / **K71**: die neunte Zeile ist `scripts/lib/consistency/spec_plan.py` — der Matrix-Kopf nannte **9**, gezählt waren **8**; die Lücke war genau diese Zeile)

`owns` = schreibt die Datei · `reads` = liest sie (Lesen ist **kein** Ownership, Global Constraints).

| Datei | W2-1 | W2-2 | **W2-0** | **W2-9** | **W2-3** | **W2-4** | **W2-5** | **W2-6** | **W2-8** | W2-7 |
|---|---|---|---|---|---|---|---|---|---|---|
| `scripts/lib/consistency/docs.py` | owns | owns | **owns** (→ Fassade) | — | reads | reads | reads | reads | — | **owns** (`__all__`) |
| `scripts/lib/consistency/docs_links.py` | — | — | **owns** (Create) | — | reads | reads | reads | **owns** (V4-Scope, E-5) | — | reads |
| `scripts/lib/consistency/docs_freshness.py` | — | — | **owns** (Create, V1) | — | reads | reads (**Rev. 0.7: nicht mehr — E-7**) | **owns** (V6) | reads | — | reads |
| **`scripts/lib/consistency/docs_freshness_v5.py`** (neu, E-7) | — | — | — | — | — | **owns** (Create, V5) | — | — | — | reads |
| `scripts/lib/consistency/docs_wiki.py` | — | — | — | — | **owns** (Create, V7) | reads | reads | reads | — | reads |
| `scripts/lib/consistency/docs_index.py` | — | — | — | — | reads | reads | reads | **owns** (Create, V2) | — | reads |
| **`scripts/lib/plan_identity.py`** (neu in W2, E-8) | — | — | — | **owns** (Modify, TASK_HEADER_RE) | — | — | — | — | — | — |
| **`scripts/lib/plan_ledger.py`** (bedingt, E-8/K58) | — | — | — | **owns** (Modify, bedingt) | — | — | — | — | — | — |
| **`scripts/lib/consistency/spec_plan.py`** (W2-9, K62/K71) | — | — | — | **owns** (Modify, Dep-Token-Muster `:570` → nach W2-9 `_DEP_TOKEN_RE` `:68`) | — | — | — | — | — | — |
| `scripts/consistency-check.py` | reads | reads | **reads** (darf es **nicht** ändern) | — | reads | reads | reads | reads | — | **owns** |
| `scripts/lib/consistency/report.py` | reads | reads | **reads** | — | reads | reads | reads | reads | — | **owns** (K15) |
| `tests/test_doc_facts.py` | owns | owns | **owns** (Verschiebung) | — | reads | reads | reads | reads | — | **owns** (V3-Pin `:2527-2537`, F1-/Exit-Tests) |
| `tests/test_doc_freshness.py` | — | — | **owns** (Create) | — | reads | reads (**Rev. 0.7: nicht mehr — E-7**) | **owns** (V6) | reads | — | **owns** (V1-Pin `:364-383`, **K46**) |
| **`tests/test_doc_freshness_v5.py`** (neu, E-7) | — | — | — | — | — | **owns** (Create) | — | — | — | — |
| `tests/test_doc_wiki.py` | — | — | — | — | **owns** (Create) | reads | reads | reads | — | — |
| `tests/test_doc_index.py` | — | — | — | — | reads | reads | reads | **owns** (Create) | — | reads |
| **`tests/test_knowledge_engine.py`** (W2-8, E-6) | — | — | — | — | — | — | — | — | **owns** (Modify) | — |
| **`tests/test_sharkord_service_name_migration.py`** (W2-8, E-6) | — | — | — | — | — | — | — | — | **owns** (Modify) | — |
| **`tests/test_plan_identity.py`** (W2-9, E-8) | — | — | — | **owns** (Modify) | — | — | — | — | — | — |
| **`tests/test_plan_ledger_writer.py`** (W2-9, E-8) | — | — | — | **owns** (Modify) | — | — | — | — | — | — |
| `tests/test_doc_facts_expected.py` | — | — | reads | — | reads | reads | **owns** | reads | — | reads |
| `tests/fixtures/docs_v1_fixtures.md` | owns | reads | reads | — | reads | reads | reads | reads | — | reads |
| `tests/scenarios/**` (Asserts 50–56) | reads | reads | reads | — | reads | reads | reads | reads | — | reads |

**Rev. 0.7 (K56) — was diese Matrix an den zwei neuen Spalten beweist.** **W2-9** und **W2-8** haben
**je eine** eigene Zeilengruppe, in der **keine andere** W2-Task `owns` trägt — die Write-Sets sind
zu **allen** W2-Aufgaben disjunkt, nicht nur innerhalb von PG-2a. **W2-4** verliert nach E-7 die
beiden `owns`-Einträge `docs_freshness.py` und `tests/test_doc_freshness.py` (sie stehen jetzt
ausdrücklich als **„nicht mehr"**) und gewinnt zwei **neue** `owns`-Zeilen. **Damit ist der Satz
„genau **eine** schreibende Task **pro Datei pro Parallelgruppe**" unverändert erfüllt**, und die
historische Kante `W2-5 → W2-4` ist **wirkungslos** (siehe Zyklenprüfung). **Neu zu prüfen, weil
neu:** W2-8 schreibt `tests/test_knowledge_engine.py` und `tests/test_sharkord_service_name_migration.py` —
**keine** dieser beiden Dateien wird von **irgendeiner** anderen Task des **gesamten** Plans
geschrieben; W2-9 analog für die **fünf** Werkzeug-/Testdateien (`plan_identity.py`,
`plan_ledger.py`, **`scripts/lib/consistency/spec_plan.py`**, `tests/test_plan_identity.py`,
`tests/test_plan_ledger_writer.py`). **W2-7 bleibt der alleinige Owner aller
`__all__`-Inkremente** (K46-Negativregel gilt für W2-4 unverändert: W2-4 fasst `docs.py` nicht an).

**Korrekturrunde 6 (K71) — die neunte Dateizeile ist nachgetragen, und alle abgeleiteten
Inventare sind auf den neuen Zählstand gezogen.** **Befund:** K62 hat `spec_plan.py` korrekt in
W2-9s `Files:` aufgenommen, aber **keine** der daraus abgeleiteten Stellen mitgezogen — Matrix,
Matrix-Narrativ, Step-Agent-Map, `File Structure`, Rollback W2 und die Self-Review-Summenlisten.
Der Matrix-Kopf nannte **9 Dateizeilen**, gezählt waren **8**: die Lücke war genau diese eine Zeile,
der Kopf war also richtig und die Tabelle unvollständig. **Neu gemessene Stände:** W2-9 führt jetzt
**5** `owns`-Zeilen (vorher 4), W2-9 + W2-8 zusammen **7** Zeilen (vorher 6), die Rev.-0.7-
Dateizeilen der Matrix **9** (vorher 8). **Kollisionsprüfung, ausdrücklich:** `spec_plan.py` wird
von **keiner** anderen Task des Plans in ihre `Files:`-Liste aufgenommen (W2-0 las sie **nur** für
den Modul-Split, W2-7 schreibt `consistency-check.py`/`docs.py`/`report.py`) ⇒ die Regel
„höchstens **eine** schreibende Task **pro Datei pro Parallelgruppe**" ist **auch mit** der
ergänzten Zeile erfüllt, und die Regel „**kein** Eintrag wird stillschweigend weggelassen" ist es
jetzt erst recht. **Keine Kollision, nur Deckungslücke — deshalb Korrektur an den Inventaren, nicht
an der Ownership-Entscheidung.**

**Zellen mit zwei `owns` in derselben Parallelgruppe: keine.** Geprüfte Gruppen:
**PG-2a = {W2-3, W2-5, W2-6}** — W2-3 schreibt `docs_wiki.py` + `test_doc_wiki.py`; W2-5 schreibt
`docs_freshness.py` + `test_doc_freshness.py` + `test_doc_facts_expected.py`; W2-6 schreibt
`docs_index.py` + `test_doc_index.py` + `docs_links.py`. **Mengenweise disjunkt.** W2-4 (Phase B)
**schrieb** in Rev. 0.6 dieselben zwei Dateien wie W2-5 und war deshalb sequenziell mit der Kante
`W2-5 → W2-4`; **Rev. 0.7 / E-7 hebt das auf** (W2-4 schreibt `docs_freshness_v5.py` +
`test_doc_freshness_v5.py`) — die Kante bleibt als **historische** Planungsentscheidung im
Kantenbild und ist **wirkungslos**; W2-4 bleibt **sequenziell**, jetzt aus dem im Task genannten
Grund (der Größennachweis „`docs_freshness.py` bleibt 592" ist erst nach W2-5 beobachtbar).
**Rev. 0.6 / K46 (korrigiert):** W2-7 (Phase B) schreibt **fünf** Dateien
(`docs.py`, `consistency-check.py`, `report.py`, `test_doc_facts.py`, `test_doc_freshness.py`).
Die frühere Aussage „vier Dateien, die kein PG-2a-Task schreibt" war nach dem W2-0-Verschieb des
V1-Pins **falsch**: W2-7 teilt sich `tests/test_doc_freshness.py` mit **W2-5** (PG-2a). Das ist
**kein** Verstoß — W2-7 ist **PG-2c**, läuft **sequenziell als Letzter** (Kanten 9–12) und fällt damit
unter die angewandte Regel „mehrere schreibende Tasks derselben Datei sind ausschließlich
**sequenziell**". **Neu entsteht also keine Kollision in PG-2a.** **Negativregel (K46, verbindlich):
W2-3, W2-4, W2-5, W2-6, W6-2 und W8-4 nehmen `scripts/lib/consistency/docs.py` **nicht** in ihre
`Files:`-Liste auf** — sie sind **gemessen** frei von `docs.py` (W6-2 → `docs_wiki.py`,
W8-4 → `docs_index.py`). Ein `docs.py`-Write-Set in W2-3/W2-5/W2-6 wäre genau die
Ownership-Kollision, die **K20** beseitigt hat; **W2-7 ist der alleinige Owner aller
`__all__`-Inkremente.** Eine spätere Revision, die eine dieser Listen „vollständig" macht, ist
**fail-closed** (Fail-closed-Klausel unten).

**Ehrliche Grenze der Regel (K20).** „Genau **eine** schreibende Task **pro Datei im ganzen Plan**"
ist mit **vier** Modulen (U-1) und **fünf** modul-anfassenden Tasks **nicht** erfüllbar; `docs.py`
wird in Rev. 0.5 ohnehin von W2-1…W2-7 **und** W8-4 geschrieben. **Angewandte Regel (Rev. 0.5-
Praxis, Self-Review-Absatz „Ownership"):** *höchstens eine schreibende Task **pro Parallelgruppe**;
mehrere schreibende Tasks derselben Datei sind ausschließlich **sequenziell**.* `check_plan_file_overlap`
prüft genau diese Eigenschaft.
**Rev. 0.7 (K56) — die Grenze verschiebt sich, sie wird nicht aufgehoben:** mit E-7 sind es **fünf**
Module und **sechs** modul-anfassende Tasks (W2-0, W2-3, W2-4, W2-5, W2-6, W2-7). **Angewandte Regel
unverändert.** **Neu zu prüfen war nur, ob W2-8/W2-9 die Regel verletzen** — beide tun es **nicht**,
weil ihre Dateien **kein** anderer Task schreibt (siehe die beiden neu aufgenommenen Zeilengruppen
oben). **Ausdrücklich nicht behauptet:** „genau eine schreibende Task pro Datei im ganzen Plan" —
das gilt für die **sieben** neuen Dateien von W2-8/W2-9 (**K71**; vorher stand hier „sechs", weil
`spec_plan.py` in keinem abgeleiteten Inventar geführt war), **nicht** für `docs.py`,
`docs_freshness.py`, `tests/test_doc_freshness.py` oder `tests/test_doc_facts.py`.

### 2. DAG-Kantenliste (vollständig, W2 + Querwellen)

| # | Kante | Art | Begründung der Kante |
|---|---|---|---|
| 1 | `W1-6 → W2-1` | Querwelle | W2-1 braucht W1-6 (Snippet-Bridge) + W0-4 (Track-A-Merge) |
| 2 | `W0-4 → W2-1` | Querwelle | Track-A-Kollisionsgate (R3) |
| 3 | `W1-5 → W2-5` | Querwelle | V6 braucht `load_expected_doc_facts` aus W1-5 |
| 4 | **`W2-2 → W2-0`** | **W2, seriell** | **Rev. 0.6:** W2-0 verschiebt den V1- und V3-Code; es kann erst laufen, wenn beide **existieren** |
| 5 | **`W2-0 → W2-3`** | **W2, seriell → PG-2a** | **Rev. 0.6:** W2-3 legt `docs_wiki.py` an und setzt die Modul-Familie voraus |
| 6 | **`W2-0 → W2-5`** | **W2, seriell → PG-2a** | **Rev. 0.6:** W2-5 erweitert `docs_freshness.py`, das W2-0 anlegt |
| 7 | **`W2-0 → W2-6`** | **W2, seriell → PG-2a** | **Rev. 0.6:** W2-6 generalisiert V4 in `docs_links.py` (W2-0) und legt `docs_index.py` an |
| 8 | **`W2-5 → W2-4`** | **W2, seriell** | **Rev. 0.6:** gemeinsame Schreibmenge `docs_freshness.py` + `test_doc_freshness.py`. **Rev. 0.7 / E-7 — historische Kante, in der Begründung überholt:** W2-4 schreibt jetzt `docs_freshness_v5.py` + `test_doc_freshness_v5.py`. Die Kante **bleibt** (Planungsentscheidung bleibt nachvollziehbar), ist aber **wirkungslos**; W2-4 bleibt aus dem **im Task genannten** Grund sequenziell (Größennachweis 592 erst nach W2-5 beobachtbar) |
| 9 | **`W2-3 → W2-7`** | **W2, seriell** | **Rev. 0.6:** Registrierung braucht alle implementierten Checks |
| 10 | **`W2-4 → W2-7`** | **W2, seriell** | dito |
| 11 | **`W2-5 → W2-7`** | **W2, seriell** | dito |
| 12 | **`W2-6 → W2-7`** | **W2, seriell** | dito |
| 13 | `W2-1 → W3-4` | Querwelle, **Vorwärts** | Rev. 0.5, K16/RVW-4 (unverändert) |
| 14 | `W1-10 → W3-1` | Querwelle (unverändert) | W3-1 braucht die Config-Keys |
| 15 | `W3-6 → W4-1`, `W4-3 → W5-1`, `W6-2 → W7-1`, `W7-5 → W8-1` | Wellenfolgen (unverändert) | §9.2 |

**Parallelgruppen (max. 3):** **PG-2a = {W2-3, W2-5, W2-6}** (3 Tasks, disjunkt) · **PG-2b = {W2-4}**
· **PG-2d = {W2-8}** · **PG-2c = {W2-7}** · **PG-2e = {W2-9}** (Phase 0, sequenziell) — dazu
unverändert **PG-2/W3** (die W3-Kette) parallel zu allen W2-Phasen. **Rev. 0.7 (K56):** die
Gruppenzahl steigt von **3** auf **5**, die **gleichzeitige** Agentenzahl bleibt bei **3** (PG-2a).
W2-9 und W2-8 liegen **außerhalb** von PG-2a, damit die Grenze von 3 nicht überschritten wird und die
bindende Größe weiterhin **Ownership-Disjunktheit** bleibt, nicht die Agentenzahl.

**Kanten neu in Rev. 0.7 (additiv angefügt, Nummerierung fortgesetzt, keine bestehende Nummer
geändert):** **16** `W2-0 → W2-9` (W2-9 beendet die K53-Interim-Regel und muss vor **allen** noch
offenen W2-Tasks laufen — W2-6, W2-4, W2-8, W2-7 — damit diese mit dem Werkzeug abgehakt werden
können; **reine Sequenzierung, keine Datenabhängigkeit**, ausdrücklich so deklariert) · **17**
`W2-4 → W2-8` (W2-8 ist der **letzte** Task vor W2-7; sein Nachweis soll die vollständige
W2-Doku-Check-Landschaft prüfen und nicht einen Zwischenstand) · **18** `W2-8 → W2-7` (die
Volltests müssen grün sein, **bevor** W2-7 V2/V3/V6 als ERROR registriert und `--validate` damit
planmäßig rot wird).

### 3. Zyklenprüfung (Rev. 0.7, neu gerechnet)

**Topologische Ordnung:** `W0-2 → W0-1/W0-3/W0-4/W0-6/W0-7 → W0-4 → W1-1 → … → W1-6 → W2-1 →
**W2-2 → W2-0 → W2-9 → {W2-3, W2-5, W2-6} → W2-4 → W2-8 → W2-7** → W3-1 → … → W3-7 → W4-1 → … → W6-2 → W7-1 →
… → W7-5 → W8-1 → … → W8-4`.

**Nachweis, fünf Teile:**
(a) **Keine Rückwärtskante** über Wellen: jede Kante zeigt von einer niedrigeren auf eine höhere
Welle; `W2-1 → W3-4` ist eine **Vorwärts**kante (Rev. 0.5, RVW-4, unverändert).
(b) **Innerhalb W2** zeigen alle Kanten **vorwärts** in der Reihenfolge oben: von `W2-0` (Knoten 4)
nach `W2-9` (16) und nach `W2-3`/`W2-5`/`W2-6` (5–7), von `W2-5` auf `W2-4` (8), von `W2-4` auf
`W2-8` (17) und auf `W2-7` (10), von `W2-8` auf `W2-7` (18), von `W2-3`/`W2-5`/`W2-6` auf `W2-7`
(9, 11, 12). **Es existiert keine Kante** `W2-3 → W2-0`, `W2-5 → W2-0`, `W2-9 → W2-0`,
`W2-8 → W2-4`, `W2-4 → W2-5` oder `W2-7 → W2-8` — jede Vertauschung der Richtung wäre der Fehler,
den RVW-4 in Rev. 0.5 aufgedeckt hat.
(c) **Innerhalb PG-2a gibt es überhaupt keine Kanten** — die drei Tasks sind bezüglich
Schreibmengen unabhängig; das ist der Grund, warum sie parallel laufen dürfen. **W2-9 und W2-8
liegen außerhalb** und sind damit **nicht** Teil dieser Unabhängigkeitsaussage.
(d) **Querwellenkanten** enden alle in W2 bzw. W3 und kehren **nicht** nach W2 zurück; die
Präzedenzfälle W0-4 → W1-1, W1-10 → W3-1 bestehen unverändert.
(e) **Die historische Kante `W2-5 → W2-4` (8) ist nach E-7 gegenstandslos.** Sie zeigt
**vorwärts** und kann den Graphen **nicht** zum Zyklus machen; sie wird deshalb **nicht** entfernt,
sondern als historische Planungsentscheidung im Kantenbild behalten. **Ausdrücklich:** sie zu
entfernen wäre eine stille Änderung an einer bereits abgenommenen Planungsentscheidung (K20-Logik);
sie als **gegenstandslos** zu markieren ist die dokumentierte Alternative. **Wirkung:** W2-4 ist nach
E-7 von PG-2a **disjunkt**; die Kante wird **wirkungslos**, die Regel „höchstens eine schreibende
Task pro Parallelgruppe" bleibt erfüllt.
**Ergebnis: keine Zyklen. Der Graph ist ein DAG.**

**Fail-closed-Klausel (K20, verbindlich, Rev. 0.7 unverändert in Kraft).** Wird **während**
W2-3…W2-9 eine Ownership-Zeile so
geändert, dass (1) `check_plan_file_overlap` für eine Parallelgruppe **zwei** Tasks mit gemeinsamer
Schreibmenge meldet, (2) eine Parallelgruppe **mehr als 3** gleichzeitige Agents umfassen würde,
(3) die Kantenliste oben einen **Zyklus** enthält, oder (4) ein Task eine Datei schreiben müsste,
die ein **früherer** Task derselben Gruppe bereits geschrieben hat, dann gilt: **die betroffene Task
wird nicht gestartet**, der Plan wird **nicht** stillschweigend angepasst, und es ist ein
**korrigierter Plan** mit neuer Ownership-Matrix **und** neuer Zyklenprüfung vorzulegen (Owner
`orchestrator`, Entscheidungsweg `main_chat`, Spec §17.10.4/§17.11.4). **Kein** Teillauf, **keine** stille
Korrektur an der Modulzuordnung. **Rev. 0.7:** der Bereich der Klausel ist von „W2-3…W2-7" auf
**„W2-3…W2-9"** erweitert, weil zwei Tasks hinzugekommen sind; **der Inhalt ist unverändert**.

## Entscheidungs-Tasks

| OQ | Task | Owner | Position | Folge, wenn nicht entschieden |
|---|---|---|---|---|
| **OQ6** — **ENTSCHIEDEN 2026-09-26** (`tracked`, kein `.gitignore`-Eintrag) | **W0-1** = Ergebnis-Record (vor W1-10 und W3-6) | `orchestrator` | W0, vor jedem Code-Task | **entfällt** — entschieden; W0-1 dokumentiert, W3-6 schreibt `docs/INDEX.md` tracked ohne `.gitignore`-Diff (Spec §11.2) |
| **OQ8** — **ENTSCHIEDEN 2026-09-26** (Sync/Validator, kein Hook) | **W0-6** = Ergebnis-Record (vor Abschluss W3) | `orchestrator` | W0, Umsetzung in W3-6 | **entfällt** — entschieden; V2 bleibt **ERROR**, Auslöser ist der Sync-/Validator-Lauf (Spec §11.2) |
| **OQ2** — **ENTSCHIEDEN 2026-09-26** (**Hybrid**: `{{DOCS_PROVIDERS_BLOCK}}` + `{{DOCS_REPO_FACTS_BLOCK}}`, Rest Handtext) | **W0-3** = Ergebnis-Record (vor Abschluss W1) | `agent-meta-manager` | W0 | **entfällt** — entschieden; `llms.txt` ist Wert von `docs-consolidation.sources` (IC-22), Prosa bleibt handgepflegt (Spec §11.2) |
| OQ1 (offen) | W0-7 (vor Abschluss W5) | `orchestrator` → `main_chat` | W0 | W5-3 annotiert ohne Scope-Grenze; FI-4 bliebe ungebunden |
| OQ9 (offen) | W5-1 (vor W5-2) | `technical-writer` + `documenter` | W5 | zwei SSoT-Kandidaten unter `docs/guides/` ohne Kennzeichnung (F24) |
| OQ4 (offen) | W8-1 (vor W8-3) | `requirements` + `validator` | W8 | F16 (zwei ID-Systeme) bleibt undokumentiert |
| **OQ10 (offen — neu, Rev. 0.6, K32)** | **W8-4** (Querverweis im Task-Text; **Frist: vor W8-4**) | `orchestrator` → `main_chat` | W8 | **V3 bleibt unter `docs/**` ERROR** ⇒ `consistency-check.py → 0` und `sync.py --validate → 0` bleiben **dauerhaft unerreichbar**; maßgeblich ist die **Deltasperre** (`errors` darf nicht steigen, Baseline W3-7). Fällt die Entscheidung für die **Herabstufung auf WARNING** (Scope-gestuft), ist **IC-05 in der nächsten Revision** zu ändern; **ohne** Entscheidung bleibt der Doku-Endzustand dauerhaft rot |
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
| AC-09 | W2-2 (Fund) + W8-2 (Behebung) | W2/W8 | V3 || AC-10 | W1-4 (Resolver) + W2-3 (Check) | W1/W2 | V7 |
| AC-11 | W2-4 · **Rev. 0.7: zusätzlich W2-8** (Wohlgeformtheitsnachweis, **kein** eigener AC-Anteil) | W2 | V5 |
| AC-12 | W2-6 (Implementierung) + W3-6 (E2E) · **Rev. 0.7 / E-5: V4-Anteil auf den README-Index-Scope begrenzt; die 193 sind Follow-up `F-DOCS-README-INDEX-2026-09-27`, kein AC** | W2/W3 | V2, V4 |
| AC-13 | W2-7 · **Rev. 0.7: zusätzlich W2-8** (die beiden Volltests als Wohlgeformtheitsnachweis) | W2 | alle |
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
| AC-30 | W8-2 (+ W8-4 Nachweis) · **Rev. 0.6 / K22: Scope auf `README.md` + `llms.txt` verengt**; die 25 `docs/**`-Fundstellen sind **kein** AC, sondern Follow-up `F-DOCS-LINKS-2026-09-27` (Owner `developer`, Termin 2026-10-11) | W8 | V3 |
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
**Rev. 0.7 (K56) — zwei Tasks **ohne** AC, ausdrücklich benannt (kein Loch, keine erfundene AC):**
**W2-8** (E-6) trägt **AC-11** und **AC-13** als **Wohlgeformtheitsnachweis** mit, hat aber **keinen
eigenen** AC-Anteil — es stellt eine bereits behauptete Eigenschaft wieder her; **W2-9** (E-8) ist ein
**reiner Querschnitts-Task** wie W2-0 und trägt **keinen** AC (es stellt ein **Werkzeug** her, DoD
Punkt 14). **Beide Fälle sind als solche benannt und nicht durch eine erfundene AC verdeckt** — eine
AC zu erfinden wäre eine Spec-Änderung.
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
2. **Alle neun V-Checks sind implementiert; V1, V2, V5, V6, V7 und V8 liefern in agent-meta je
   Check **0** `docs.*`-Findings, **`docs.readme_index` (V4) liefert nach W2-6 genau `1` Finding**,
   **`docs.internal_links` (V3) liefert `0` im AC-30-Scope**
   (`README.md` + `llms.txt`; die **25** `docs/**`-Fundstellen sind **Follow-up
   `F-DOCS-LINKS-2026-09-27`**, Owner `developer`, Termin **2026-10-11**, **kein** Termin 0 in
   W0–W8), `docs.stale_backups` (V9) meldet den Altbestand und ist **geduldet**
   (FI-10).** **Rev. 0.7 / K54 — der V4-Erwartungswert ist von `0` auf `1` umgestellt, und das ist
   ausdrücklich benannt.** Grund: die Lesart, die den 193-Blocker auflöst (kategorie-genaue
   Strukturvollständigkeit des README-Index), liefert am gemessenen Baum **genau 1** **echten**
   Befund — eine im Index deklarierte Kategorie (`docs/se-cascade/`) ohne Link. **W4 bleibt im
   Sollwert enthalten**; die alte Formulierung „V4 = `0`" wäre nach E-5 **falsch**, und ihre
   Aufrechterhaltung wäre eine **verdeckte Absenkung**. **Termin:** Follow-up
   `F-DOCS-README-INDEX-SE-2026-09-27` (Owner `developer`, **2026-10-11**). **Die 193** sind **kein**
   Sollwert, sondern Follow-up `F-DOCS-README-INDEX-2026-09-27` (gleicher Owner/Termin; Nachweis =
   Issue-Liste + once-count außerhalb V4, **K60**).
   **K26 (Rev. 0.6, Review-Befund M2) — der Erwartungswert von V3 ist korrigiert.** Die
   Fassung vor dieser Korrekturung („V1…V8 = 0") war mit der **U-2**-Verengung von AC-30
   unvereinbar: V3 bleibt **ERROR** (IC-05) und meldet die 25 `docs/**`-Findings **weiter**.
   **Nur** der V3-Erwartungswert ist geändert; **V1, V2, V5, V6, V7, V8** bleiben `0`
   unverändert (**Rev. 0.7: V4 kommt nach E-5 hinzu**). **Kein** Sollwert wurde stillschweigend
   abgesenkt — die Aussage ist
   **umformuliert und begründet** (K22, Spec §17.10.2), und die offene Severity-Frage ist als
   **OQ10** geführt (Owner `orchestrator`, Frist **vor W8-4**). **Neufassung in der dritten
   Korrekturrunde (RVW2-3)** — die Fassung davor war **in
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
   **je** V-Check, mit Termin und Owner. Am Ende des Vorhabens gilt: **V1, V2, V4, V5, V6, V7, V8 =
   0** und **V3 = 0 im AC-30-Scope** (K26); `docs.stale_backups` (V9) = **geduldet, kein Sollwert**,
   Obergrenze nach der Bestandsaufnahme in W8-4 Schritt 1; `docs-checks` = **Dokuzeile**;
   `docs-findings` = **kein** Kriterium.
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
     Regressionen; `python3 scripts/sync.py --check` → **0** (Drift-Lauf, RVW2-13).
     **K26 (Rev. 0.6, Review-Befund M3) — `--validate → 0` ist gestrichen und durch die Deltasperre
     ersetzt.** Die Fassung vor dieser Korrekturung („erst nach W8-4 erreichbar", Regel
     `W-VALIDATE-ROT`) war mit **K22** unvereinbar: V3 bleibt als **ERROR** registriert und meldet
     unter `docs/**` dauerhaft **25** Findings, die AC-30 **nicht** behebt — `→ 0` ist damit
     **dauerhaft unerreichbar**, auch nach W8-4. **Maßgeblich ist ab Rev. 0.6 die Deltasperre:**
     `errors` aus `consistency-check.py --json` **darf nicht steigen** gegenüber der in **W3-7**
     gemessenen Baseline; Owner `validator`, Mess-Ort **W3-7**, Termin **W3-7**. **Der Widerspruch
     zwischen `→ 0` und Deltasperre ist damit aufgelöst** — maßgeblich ist die Deltasperre; `→ 0`
     ist als **Dokuzeile ohne Sollwert** geführt. **Bleibt offen und ist nicht hier entschieden:**
     ob die V3-Severity für `docs/**` herabgestuft wird — **OQ10** (Spec §11.1, Owner
     `orchestrator`, Frist **vor W8-4**, dort als **W8-4**-Task geführt).
     **Rev. 0.7 / E-6 — der Volltest-Standard, neu und ausdrücklich.** `python3 -m pytest tests/ -q`
     → **0 rote Tests**. **Vor W2-8** sind **genau 2** rote Tests planmäßig
     (`test_knowledge_roles_pass_schema_validation`, `test_generated_docker_agent_has_no_leftover_platform_namespace_placeholder`),
     und sie sind **kein** Beweis eines Fehlers im Produktivcode: beide hängen am repo-globalen
     `--validate`-Exit, der nach `W-VALIDATE-ROT` planmäßig rot ist. **Maßgeblich ist der Zählwert
     der roten Tests**, kein Exit-Code (RVW-12). **Nach W2-8** ist `0` erreichbar **ohne**
     Sollwert-Absenkung, `xfail`, `-k`-Filter oder Eingriff in `sync.py` — Task W2-8 Schritt 2 legt
     die zulässigen Mechanismen fest.
13. **Traceability**: `validator`-Audit bestätigt AC-01…AC-41 → Task → Test; NFA-01…NFA-11 belegt.
14. **Ledger**: alle Checkboxen dieses Plans gesetzt (geschrieben durch den Ledger-Writer
     `scripts/lib/plan_ledger.py`); Merge des Wellen-Branches
     `feat/repository-documentation-consolidation-main` manuell bestätigt (Ausführungskorrektur
     2026-09-26: **ein** Wellen-Branch statt acht, s. W0-2-Akzeptanz); danach
     Verschiebung nach `docs/plans/archive/` gemäß `docs/plans/README.md:4-7`.
     **Rev. 0.7 / E-8 (K57) — die Voraussetzung dieses Punkts ist eine Task.** Der Ledger-Writer
     adressiert diesen Plan **erst ab W2-9**; bis dahin gilt die K53-Interim-Regel (manuelles Abhaken
     durch den Orchestrator mit Datum, Commit-Hash und Task-ID im Abschnitt **L-1**). **Ab W2-9**
     gilt: (a) `plan_ledger` läuft gegen diesen Plan **ohne** `unmatched`-Zeile und liefert **0**;
     (b) **kein** Checkbox wird von Hand gesetzt; (c) die K53-Interim-Regel ist **ausdrücklich für
     beendet** erklärt (Task W2-9 Schritt 3). **Wird W2-9 zurückgerollt**, ist die Interim-Regel
     **wieder** zu aktivieren — das ist kein Fehler, sondern die Umkehrung einer dokumentierten
     Entscheidung (W2-Rollback Stufe 3).

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
  **Rev. 0.7 (K57) — `E-5`…`E-8` sind keine Platzhalter und keine offenen Vorlagen mehr.** Sie sind
  am **2026-09-27** vom Nutzer **entschieden** (verbindlich, über `main_chat`); jede trägt Owner,
  Datum, Gewähltes **und** Verworfenes (Volltext: Schlussabschnitt „Entscheidungs-Abschluss
  Rev. 0.7" und Spec §17.11). **Weiterhin offen** bleiben **`E-1`…`E-4`** (Spec §17.9.4) — sie sind
  **keine** Nutzerentscheidungen und werden hier **nicht** berührt. **Vollständige
  Self-Review-Dateiliste der Rev. 0.7** (ergänzt die Rev.-0.6-Liste): zusätzlich
  `scripts/lib/consistency/docs_freshness_v5.py` (W2-4) · `tests/test_doc_freshness_v5.py` (W2-4) ·
  `tests/test_knowledge_engine.py` (W2-8) · `tests/test_sharkord_service_name_migration.py` (W2-8) ·
  `scripts/lib/plan_identity.py` (W2-9) · `scripts/lib/plan_ledger.py` (W2-9, bedingt) ·
  **`scripts/lib/consistency/spec_plan.py` (W2-9, K71)** ·
  `tests/test_plan_identity.py` (W2-9) · `tests/test_plan_ledger_writer.py` (W2-9).
- **AC-Vollständigkeit:** AC-01…AC-41 lückenlos, jede Zahl genau einmal in der Coverage-Matrix;
  W1=10, W2=7, W3=14, W4=2, W5=2, W6=2, W7=4, W8=2 — deckungsgleich mit Spec §9.2 (NEW-5).
  **Rev. 0.7 (K56) — die Zeile oben ist ein datierter Stand und wird hier nicht fortgeschrieben.**
  Sie nennt **W2 = 7** und stammt aus der Rev. 0.1-Zählung; **maßgeblich** ist die
  **Coverage-Matrix** dieses Plans, die **50** Tasks führt. **Neu in Rev. 0.7:** **W2-8** trägt
  **AC-11** und **AC-13** als Wohlgeformtheitsnachweis **mit** (ohne eigenen AC-Anteil), **W2-9**
  ist ein reiner Querschnitts-Task **ohne** AC (Muster W2-0). **Keine AC wurde erfunden**, um eine
  Lücke zu schließen — das wäre eine Spec-Änderung.
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
  **Rev. 0.6 (K20) — die Rev.-0.5-Auflösung („die serielle Kette löst es auf") ist damit gegenstandslos
  und wird hier nicht fortgeschrieben:** W2-0 macht `docs.py` zur **Fassade**, und ab da schreibt
  **kein** PG-2a-Task `docs.py` — die geteilte Schreibmenge ist **aufgelöst, nicht weggeregelt**.
  Verbleibende Mehrfachschreiber sind **ausschließlich sequenziell** und je Datei benannt:
  `docs.py` (W2-0 → W2-7), `docs_freshness.py` (W2-0 → W2-5 → W2-4),
  `tests/test_doc_freshness.py` (W2-0 → W2-5 → W2-4), `docs_wiki.py` (W2-3 → W6-2 für V8),
  `docs_index.py` (W2-6 → W8-4 für V9), `docs_links.py` (W2-0 → W2-6),
  `tests/test_doc_facts.py` (W2-1 → W2-2 → W2-0 → W8-4).
  **Rev. 0.7 / E-7 — die Liste oben ist der Stand Rev. 0.6; aktuell gilt:** `docs.py`
  (W2-0 → W2-7), `docs_freshness.py` (**W2-0 → W2-5** — W2-4 schreibt sie **nicht** mehr),
  `tests/test_doc_freshness.py` (**W2-0 → W2-5 → W2-7**), `docs_wiki.py` (W2-3 → W6-2),
  `docs_index.py` (W2-6 → W8-4), `docs_links.py` (W2-0 → W2-6), `tests/test_doc_facts.py`
  (W2-1 → W2-2 → W2-0 → W2-7 → W8-4). **Neu und je Einfachschreiber:** `docs_freshness_v5.py`
  (W2-4), `tests/test_doc_freshness_v5.py` (W2-4), `plan_identity.py` (W2-9), `plan_ledger.py`
  (W2-9), **`scripts/lib/consistency/spec_plan.py` (W2-9, K71)**,
  `tests/test_plan_identity.py` (W2-9), `tests/test_plan_ledger_writer.py` (W2-9),
  `tests/test_knowledge_engine.py` (W2-8), `tests/test_sharkord_service_name_migration.py` (W2-8).
  **Vollständige Matrix:** Abschnitt „Ownership-Matrix, DAG-Kantenliste und Zyklenprüfung".
  **K35 (Rev. 0.6, Review-Befund m5) — Dateiliste des Self-Reviews war unvollständig.** Sie nannte
  `tests/test_doc_facts.py` nicht, obwohl **W2-7** es schreibt (positiver Registrierungs-Pin,
  RVW2-5) — die Liste widersprach damit der Ownership-Matrix, die es als `owns` für W2-7 führt.
  **Ergänzt:** `tests/test_doc_facts.py` (W2-1 → W2-2 → W2-0 → **W2-7** → W8-4) sowie
  `tests/test_doc_facts_expected.py` (W2-5). **Vollständige Self-Review-Dateiliste damit:**
  `scripts/lib/consistency/{docs.py, docs_links.py, docs_freshness.py, docs_wiki.py,
  docs_index.py, report.py}` · `scripts/consistency-check.py` ·
  `tests/test_doc_facts.py` · `tests/test_doc_freshness.py` · `tests/test_doc_wiki.py` ·
  `tests/test_doc_index.py` · `tests/test_doc_facts_expected.py` · `tests/fixtures/docs_v1_fixtures.md`.
  **Rev. 0.7 / E-7 — zwei Mehrfachschreiber fallen weg, einer kommt hinzu.** `docs_freshness.py`
  und `tests/test_doc_freshness.py` haben nach E-7 **nur noch** W2-0 → W2-5 (W2-4 schreibt sie
  **nicht** mehr). **Neu** ist `docs_freshness_v5.py` (W2-4 → **kein** weiterer Schreiber) und
  `tests/test_doc_freshness_v5.py` (W2-4 → **kein** weiterer Schreiber) — beide sind
  **Einfachschreiber**. **Neu sind außerdem** die **sieben** Werkzeug-/Testdateien von W2-8 und W2-9
  (**K71**; vorher „sechs" — `spec_plan.py` war in keinem abgeleiteten Inventar geführt),
  die **je** genau **einen** Schreiber haben und **von keinem** anderen Task des Plans geschrieben
  werden. **Vollständige Mehrfachschreiber-Liste der Rev. 0.7:** `docs.py` (W2-0 → W2-7),
  `docs_freshness.py` (W2-0 → W2-5), `tests/test_doc_freshness.py` (W2-0 → W2-5 → W2-7),
  `docs_wiki.py` (W2-3 → W6-2), `docs_index.py` (W2-6 → W8-4), `docs_links.py` (W2-0 → W2-6),
  `tests/test_doc_facts.py` (W2-1 → W2-2 → W2-0 → W2-7 → W8-4).
- **Parallelgruppen:** PG-1 (3 Ketten), PG-2 (**5** Gruppen), PG-3 (seriell), PG-4 (isoliert),
  PG-5 (1). Maximal 3 gleichzeitig laufende Agents — **unter** der Grenze 4, daher ist keine
  Barrieren-Spaltung über 4 hinaus nötig. **Rev. 0.6 (K20):** PG-2 wird **innerhalb** von W2
  aufgeteilt in **PG-2a = {W2-3, W2-5, W2-6}** (3 Tasks, **write-set-disjunkt**), **PG-2b = {W2-4}**,
  **PG-2c = {W2-7}**; das Limit von **3** wird damit **von innen ausgeschöpft**, nicht überschritten —
  und die bindende Größe ist die **Ownership-Disjunktheit**, nicht die Agentenzahl (W2-4 *könnte*
  nicht hinzukommen, weil es W2-5s Schreibmenge teilt).
  **Rev. 0.7 (K56):** PG-2 hat jetzt **5** Gruppen — **PG-2a = {W2-3, W2-5, W2-6}** (unverändert
  3 Members), **PG-2b = {W2-4}**, **PG-2d = {W2-8}**, **PG-2c = {W2-7}**, **PG-2e = {W2-9}** (Phase 0).
  **Die gleichzeitige Agentenzahl bleibt 3** — W2-9 und W2-8 liegen **außerhalb** von PG-2a, damit die
  Grenze nicht überschritten wird. **Korrektur der Begründung oben:** nach E-7 *könnte* W2-4 nun
  **doch** in PG-2a (es teilt W2-5s Schreibmenge nicht mehr); es bleibt dort **freiwillig nicht**,
  aus dem im Task genannten Grund (der Größennachweis `592` ist erst nach W2-5 beobachtbar) — die
  bindende Größe bleibt also die **Ownership-Disjunktheit**, und die Grenze von 3 ist **auch**
  Rev. 0.7 **nicht** die bindende Größe.
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
    §10, Aufzählungspunkt `--validate`**; die Sollwerte werden **nicht** abgesenkt, sondern **terminiert**;
    **Rev. 0.6 (K22) — der Termin 0 `W8-4` gilt für `--validate` nur noch bedingt und ist mit
    der U-2-Verengung faktisch aufgehoben:** V3 meldet unter `docs/**` dauerhaft **25** ERROR-
    Findings, also ist `--validate → 0` **nicht** erreichbar; maßgeblich ist die **Deltasperre**
    (Owner `validator`, Baseline **W3-7**). Severity-Frage **OQ10**; (b) die
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
   7. **Rev. 0.6 (U-1/K20) — Modul-Split ohne Verhaltensänderung** als **eigener** Task **W2-0**
      statt als Nebenschritt in W2-1: nötig, weil die Parallelität in W2 sonst eine
      Scheinparallelität bleibt (alle Tasks schrieben `docs.py` **und** `test_doc_facts.py`).
      **W2-0 ist verhaltensneutral** und trägt **keinen** AC.
   8. **Rev. 0.6 (U-1/K20) — Mehrfachschreiber einer Datei sind sequenziell, nicht disjunkt.**
      „Genau **eine** schreibende Task pro Datei" ist mit vier Modulen (U-1) und fünf
      modul-anfassenden Tasks **nicht** erfüllbar. Angewandt wird die Rev.-0.5-Regel
      (*höchstens eine schreibende Task **pro Parallelgruppe***); `check_plan_file_overlap` prüft
      genau das. Betroffene Dateien: `docs.py`, `docs_freshness.py`, `docs_links.py`,
      `docs_wiki.py`, `docs_index.py`, `tests/test_doc_facts.py`,
      `tests/test_doc_freshness.py` — alle in der Ownership-Matrix namentlich aufgeführt.
      **Rev. 0.7 (K56) — Abweichung 8 bleibt gültig, ihre Zahlen sind überholt:** es sind jetzt
      **fünf** Module und **sechs** modul-anfassende Tasks (W2-0, W2-3, W2-4, W2-5, W2-6, W2-7);
      `docs_freshness.py` und `tests/test_doc_freshness.py` haben nach E-7 **zwei** statt **drei**
      Schreibende. **Neue Dateien mit je genau einem Schreibenden** (Einfachschreiber):
      `docs_freshness_v5.py`, `tests/test_doc_freshness_v5.py`, `plan_identity.py`,
      `plan_ledger.py`, **`scripts/lib/consistency/spec_plan.py` (K71)**,
      `tests/test_plan_identity.py`, `tests/test_plan_ledger_writer.py`,
      `tests/test_knowledge_engine.py`, `tests/test_sharkord_service_name_migration.py`.
   9. **Rev. 0.6 (U-2/K22) — AC-30 verengt** auf `README.md` + `llms.txt`; die 25 `docs/**`-Links
      sind **Follow-up** (Owner `developer`, Termin **2026-10-11**) statt AC. **Folge:** V3 und
      damit `consistency-check.py → 0` / `sync.py --validate → 0` sind **dauerhaft unerreichbar**;
      maßgeblich ist die **Deltasperre**. Severity-Frage = **OQ10** (offen).
   10. **Rev. 0.7 (E-5/K54) — V4 prüft den README-Index-Scope statt des ganzen `docs/`-Baums.** Die
       in Spec IC-05 und §9.2 beschriebene „Generalisierung auf den gesamten `docs/`-Baum" ist
       **aufgehoben** und durch eine **kategorie-genaue** Prüfung ersetzt. **Folge:** die **193**
       nicht im README verlinkten Seiten sind **kein** Check-Finding; V4 liefert am gemessenen Baum
       **1** Finding (deklarierte Kategorie `docs/se-cascade/` ohne Link). **Beides ist als
       Follow-up mit Owner, Termin und Nachweis geführt** (Spec §17.11.3), **nicht** stillschweigend.
       **Korrekturrunde 5 (K60):** Zahl **193** statt 191, Nachweis = Issue-Liste + once-count
       außerhalb V4 — **kein** `docs.readme_index`-Zählwert (V4 zählt Kategorien, nicht Seiten).
       **Die verworfene Alternative** (Rücknahme auf `docs/api/*.md`) ist in Spec §17.11.2
       begründet benannt.
   11. **Rev. 0.7 (E-7/K56) — ein fünftes Modul.** U-1 sah **vier** Module für die Dateicheck-Logik
       vor; V5 liegt jetzt in `docs_freshness_v5.py`. **Grund:** `docs_freshness.py` ist gemessen bei
       **592** Zeilen, V5 braucht **55–70** ⇒ **647–662** > 600, und W2-4s Abnahmekriterium
       (`wc -l` < 600) wäre gescheitert. **Die Zuordnung bleibt 12/12 disjunkt und lückenlos**, jetzt
       auf **5** Module. **Ausdrücklich nicht gemacht:** die < 600er-Grenze aufweichen, die
       Modulzuordnung der Spec stillschweigend verschieben oder `_v6_finding` in einen geteilten
       Helfer ziehen (versteckte Kopplung).
   12. **Rev. 0.7 (E-6/K56) — zwei Tests werden angefasst, um ihre eigene Aussage zu behalten.**
       `tests/test_knowledge_engine.py` und `tests/test_sharkord_service_name_migration.py`
       prüften bislang `returncode == 0` gegen den **repo-globalen** `sync.py --validate`-Exit. Das ist
       ein **Fremdmaß**: die Tests haben nichts mit den Doku-Checks zu tun, `--validate` ist aber nach
       §10 planmäßig rot. **Der Test wird nicht abgeschwächt, sondern von der Fremdgröße entkoppelt**
       (W2-8, drei zulässige Mechanismen, `xfail`/`-k`/`|| true`/Sollwert-Absenkung/`sync.py`-Eingriff
       ausdrücklich **unzulässig**). **Folge:** ein Volltest-Lauf ist erst **ab W2-8** ein gültiger
       Wellen-Nachweis.
   13. **Rev. 0.7 (E-8/K57) — der Ledger-Writer braucht eine Task, bevor er diesen Plan
       adressieren kann.** `TASK_HEADER_RE` verlangt `### Task <id>`; dieser Plan schreibt
       `### W2-0:`. **Statt** 48 (heute 50) Überschriften umzuschreiben — ein großer Diff an
       wortgleich festgeschriebenen Blöcken, der zudem mit den Nicht-Task-`###`-Überschriften
       kollidiert — wird der Regex **um einen Zweig erweitert**. **Folge:** der geteilte
       Identitäts-Parser akzeptiert **zwei** Header-Formen. **Bis W2-9** gilt die K53-Interim-Regel;
       **ab W2-9** ist der Werkzeugpfad aktiv (DoD Punkt 14).
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
  NF-9) und daher nicht Teil der 11. **Rev. 0.7 — zwei Lücken, die E-5 erzeugt und die benannt
  sind statt kaschiert zu werden:** **(a)** V4 hat **keinen** Termin 0 in W0–W8 (Erwartungswert
  **1** bis Follow-up `F-DOCS-README-INDEX-SE-2026-09-27`, 2026-10-11); **(b)** die Vollständigkeit
  der `docs/`-Seiten **als solcher** ist zwischen W2-6 und W3-6 **nicht** durch einen Check
  abgesichert — V2 ist bis W3-6 planmäßig rot, weil `docs/INDEX.md` noch nicht existiert. **Beides
  ist in `W2-GATE-ERRORS` und in der `W-GATE-TABLE` mit Termin und Owner geführt.**

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

> **K34 (Rev. 0.6, Review-Befund m6 / `validator` N-2) — Die Tabelle unten ist der Stand vom
> 2026-09-26 und bleibt unverändert.** Nach Rev. 0.5 wurden **W1-1…W1-10**, **W2-1** und **W2-2**
> **abgehakt bzw. fertiggestellt**; die Tabelle bildet diesen Fortschritt **noch nicht** ab, weil sie
> ausdrücklich auf den 2026-09-26-Stand datiert ist. **Maßgeblich ist der Ist-Zähler
> `^- \[x\]` = 46 / `^- \[ \]` = 153** (Übergabemessung `validator`, 2026-09-27, Summe **199** —
> konsistent mit der Gesamtzahl, s. die Rev.-0.6-Zählung unten). **Keine** Zeile der historischen
> Tabelle wird umgeschrieben; die Korrektur des Splits steht in der Zählung, **nicht** hier.

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
| **W2-1** | 3/5 | **teilweise** — Implementierung steht; offen sind Schritt 4 (**K16 / B-4**, Rule-3-Eingrenzung, in Rev. 0.5 neu) und Schritt 5 (Commit) — **Anhang 2026-09-27 (K53-Interim-Ledger, Zeileninhalt oben bleibt Historie, s. K34-Kopfnotiz):** Ist-Stand **5/5**, alle fünf Steps tragen `[x]` (bereits in Runde 3 so festgestellt) |
| W2-2 … W2-6 | 0/4 je Task | **nicht gestartet**, unverändert offen — **Anhang 2026-09-27 (K53-Interim-Ledger, Zeileninhalt oben bleibt Historie, s. K34-Kopfnotiz):** **W2-2** 4/4 (vorher abgehakt, unverändert), **W2-3** 4/4 (`8594e67f`) und **W2-5** 4/4 (`b73e9422`) nun abgehakt, **W2-4** und **W2-6** weiterhin **0/4** |
| **W2-0** | **0/5** | **Rev. 0.6: neu, nicht gestartet.** Rev. 0.6 fügt **5** offene Checkboxen hinzu (Schritt 1 Split, 2 Test-Verschiebung, 3 Fassade, 4 Nachweise, 5 Commit) — **Anhang 2026-09-27 (K53-Interim-Ledger, Zeileninhalt oben bleibt Historie, s. K34-Kopfnotiz):** „nicht gestartet" ist **überholt**; Ist-Stand **5/5**, committet `b5bb0fe9`. W2-0 ist ein **Querschnitts-Task** und **kein** Wellen-Gate — das Gate W2 bleibt an **W2-7** gebunden |
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
- **Zählung, fortgeschrieben durch Rev. 0.6 (K20) — 5 Checkboxen hinzugekommen:** **199** Checkboxen
  gesamt. **Herleitung der Gesamtzahl:** 42 Tasks mit je **4** Steps = 168, + W2-1 (5) + W2-7 (5) +
  W4-3 (5) + W5-2 (5) = 188, + W8-4 (6) = 194, + **W2-0 (5)** = **199**. Gegenprobe über alle
  **48** Tasks: 42 × 4 + 5 × 5 + 1 × 6 = **199** (W2-0, W2-1, W2-7, W4-3, W5-2 mit je 5 Steps;
  W8-4 mit 6). **Task-Anzahl je Welle:** W2 von **7** auf **8** gestiegen; alle anderen Wellen
  unverändert.
  **K34 (Rev. 0.6, Review-Befund m6, `validator` N-2) — der Ist-Split ist 46 / 153, nicht 40 / 159.**
  Die Erstfassung dieser Revision führte **40 gesetzt / 159 offen**. Das ist der **Stand vom
  2026-09-26**; **nach Rev. 0.5 wurden W1-1…W1-10, W2-1 und W2-2 abgehakt** (+6), W1-5 und W1-10
  wurden **fertiggestellt** (je +1 bzw. +2 = +3 Checkboxen) und **W2-1** ebenfalls (**5/5** statt
  **3/5**, +2 — **korrigiert in Korrekturrunde 3**: alle **fünf** Steps von W2-1 stehen auf `[x]`,
  auch Schritt 4 = K16-Eingrenzung und Schritt 5 = Commit) ⇒ **40 + 6 + 3 + 2 = 51**? **Nein** — die
  Gegenrechnung ist unten eindeutig; maßgeblich
  ist der **gemessene** Wert: **`^- \[x\]` = 46**, **`^- \[ \]` = 153**, Summe **199** (konsistent mit
  der Gesamtzahl). **Korrigierter Split: 46 gesetzt / 153 offen.** **Die Zeilen der früheren
  Runden (40 / 150 / 154) bleiben unverändert** — sie beschreiben den Stand des jeweiligen
  Datums und sind **Historie**. **Grenze:** `46` ist die Übergabemessung des `validator` vom
  2026-09-27 (Review-Begleitbefund N-2); in dieser Revisionsrunde stand **kein Shell-Zugriff** zur
  Verfügung, die Zahl wird daher **nicht** als eigenmessung behauptet, sondern als
  **Übergabemessung** geführt. Stimmt ein künftiger Zähler nicht überein, ist **hier** zu korrigieren,
  **nicht** in der Task-Struktur.
- **Rev.-0.6-Messwerte (Baseline-Messung 2026-09-27, Übergabe vom Parent — in dieser Runde nicht
  selbst gemessen):** `check_internal_links()` → **27** Findings = **25** `link` + **2** `layout`;
  `llms.txt` → **0**; Verteilung der 25: `docs/guides` 10, `docs/concepts` 13 (**8** davon in
  `archive/`), `docs/superpowers/plans/` 2 → **17 live**. Dateigrößen: `docs.py` **599**
  (→ Prognose **~70** als Fassade), `docs_links.py` **~330**, `docs_freshness.py` **~480**,
  `docs_wiki.py` **~200**, `docs_index.py` **~180**, `report.py` **115** (unverändert),
  `consistency-check.py` **280** (in W2-0 unverändert), `tests/test_doc_facts.py` **2867**,
  `tests/test_doc_facts_expected.py` **526**; Module in `scripts/lib/consistency/`: **20** vor W2-0,
  **24** danach. **Testbasis vorher:** `tests/test_doc_facts.py` + `tests/test_doc_facts_expected.py`
  = **163 passed** — die Zahl, gegen die W2-0 Schritt 4 den Nachher-Zähler stellt.
  **`docs-checks` Ist = 0**, **`docs-findings` Ist = 0**
  (`consistency-check.py --json` → `{'total': 85, 'errors': 0, 'warnings': 85}`; enthaltene Checks
  `crossrefs.changelog-missing-entry`, `placeholders.unknown` — **kein** `docs.`-Check liefert
  Findings). `knowledge/wiki`: **11** Seiten mit `type: "Architecture"` (**K24**, war 10).
  `docs/INDEX.md` existiert **nicht**.
- **Kein** Task wurde abgehakt, obwohl ein Step offen ist. Die drei teilweise erledigten Tasks
  tragen zusätzlich eine **LEDGER-Stand**-Notiz direkt unter ihrer Step-Liste (W1-5, W1-10, W2-1);
  seit 2026-09-27 tragen auch die **abgeschlossenen** Tasks **W2-3** und **W2-5** eine solche Notiz
  (W2-0 nicht — der Querschnitt ist in Korrekturrunde 3 ausführlich dokumentiert).
- **Nicht Gegenstand:** Die W0-Tasks sind im Repo durch die Ergebnis-Records
  (`docs/plans/2026-09-25-docs-consolidation-oq2.md`, `-oq6.md`, `-oq8.md`, `-oq1.md`,
  `-wave0-freeze.md`, `-track-a-gate.md`) und durch den Rev.-0.2-Block dieses Plans belegt; ihre
  Checkboxen wurden in diesem Abgleich **bewusst nicht angefasst**, weil nur W1/W2-1 zur
  Abstimmung beauftragt waren.

#### K53-Interim-Ledger 2026-09-27 — Checkbox-Setzung nach der Interim-Regel aus K53

> **Herkunft und Reichweite.** Die folgenden **13** Checkboxen wurden nach der **Interim-Regel aus
> K53** gesetzt: **von Hand** durch den Orchestrator, jeweils mit **Datum, Commit-Hash und
> Task-ID**, und **ohne** jeden Lauf von `scripts/lib/plan_ledger.py` (dieser Plan ist für das
> Werkzeug nicht adressierbar — `TASK_HEADER_RE` verlangt `### Task <id>`, der Plan schreibt
> `### W2-0:`; **E-8** ist offen, Owner `orchestrator` → `main_chat`, Frist **vor W2-7**). Die Regel
> ist **widerruflich** und **kein** stiller Ersatz für den Werkzeugpfad. **Rev. 0.6 bleibt 0.6,
> `status: APPROVED` bleibt APPROVED**, es wurde **keine** Revisionsnummer angehoben, **keine**
> AC/IC/R/OQ/Task-/V-Check-ID umnummeriert oder gestrichen und **kein** Sollwert geändert.

| Datum | Commit | Task | Ergebnis |
|---|---|---|---|
| 2026-09-27 | `b5bb0fe9` | **W2-0** | Verhaltensneutraler Modul-Split vollständig gelandet (`docs.py` 599 → **80** Z als Fassade, `docs_links.py` **334**, `docs_freshness.py` **317**, `test_doc_freshness.py` **384**, `test_doc_facts.py` 2867 → **2538**); Tests **163 → 163**, `consistency-check.py --json` unverändert `85/0/85`, alle Module < 600. **W2-0 ist ein Querschnitt-Task und KEIN Wellen-Gate** — das Gate W2 bleibt an **W2-7** gebunden. |
| 2026-09-27 | `8594e67f` | **W2-3** | V7 `check_wiki_staleness` vollständig gelandet (`docs_wiki.py` **129** Z, `test_doc_wiki.py` **391** Z mit **10** Tests, reine Adapter-Schicht ohne eigene Staleness-Logik); nicht registriert, Baseline `85/0/85` erhalten. |
| 2026-09-27 | `b73e9422` | **W2-5** | V6 `check_docs_facts_fresh` mit Sollwert-Achse vollständig gelandet (`docs_freshness.py` 317 → **592** Z < 600); AC-36-Nachweis unabhängig gemessen (Kreis `doc_facts → Renderer → V6` gebrochen, R14), V1-Regression mit **14** unveränderten Testfällen und **null** berührten V1-Zeilen. |

- **Korrigierter Zähler, in dieser Pflege selbst gemessen (`grep`, Muster `^- \[x\]` / `^- \[ \]`,
  Plan 2026-09-25):** **vorher** `^- \[x\]` = **46**, `^- \[ \]` = **153** (Partitionsmessung
  `1:` = 36, `2:` = 37, `3:` = 36, `4:` = 38, `5:`–`9:` = 6; **keine** Nicht-Ziffer-Zeile);
  **nachher** `^- \[x\]` = **59**, `^- \[ \]` = **140** (Partitionsmessung `1:` = 33, `2:` = 34,
  `3:` = 33, `4:` = 35, `5:`–`9:` = 5). **Summe unverändert 199 = 46 + 153 = 59 + 140**;
  **+13** Checkboxen gesetzt (**5** W2-0 + **4** W2-3 + **4** W2-5), **keine** gestrichen und
  **keine** ergänzt. **Die Gesamtzahl 199 bleibt damit unverändert** — es wurde **kein** Step
  angelegt oder entfernt, nur abgehakt.
- **Damit überholt, ohne Umschreiben (Historie bleibt wortgleich):** die Zählhinweise in **K34**,
  in der Korrekturrunde 3 („Abschnitt L (L-1, L-3)") und in der Korrekturrunde 4
  („Zählung in dieser Runde selbst gemessen") nennen **46 / 153**; sie beschreiben den Stand
  **vor** dieser K53-Setzung und bleiben darum **unverändert**. Ebenso unangetastet bleiben die
  historischen Herleitungen **188 → 190 → 194 → 199** (Rev. 0.4/0.5/0.6, Runden 1–4), die
  Gegenproben **40 × 4 + …**, **42 × 4 + 5 × 5 + 1 × 6** sowie die Zählstände **40 / 150 / 154**.
  **Maßgeblich ist ab sofort dieser Block.** Stimmt ein künftiger Zähler nicht mit **59 / 140**
  überein, ist **hier** zu korrigieren, **nicht** in der Task-Struktur.
- **Ergebnis der Setzung:** **W2-0** 5/5 · **W2-3** 4/4 · **W2-5** 4/4. **W2-1** (5/5) und
  **W2-2** (4/4) waren **bereits** abgehakt und wurden **nicht** angefasst. **W2-4**, **W2-6** und
  **W2-7** bleiben **vollständig offen** (0/4, 0/4, 0/5) — **W2-6** ist blockiert (V4 macht
  `--validate` rot: 191 Errors, 2 Volltests rot; **E-5**/**E-6** offen), **W2-4** und **W2-7** ebenfalls
  (**E-7** bzw. **E-5**/**E-6**/**E-8**). Das Wellen-Gate **W2** ist damit **nicht** erreicht.

#### Rev.-0.7-Anhang zu L-1 (2026-09-27) — Zählstand, Interim-Regel-Ende, Aufgabenstand W2

> **Was dieser Anhang ist und was nicht.** Er ist **additive** Statuspflege, **keine** Plan-Revision
> und **keine** Korrekturrunde. Die **K34-Kopfnotiz**, die historische Tabelle (Stand 2026-09-26),
> die Herleitungen **188 → 190 → 194 → 199** und der **K53-Interim-Ledger** bleiben **wortgleich**
> stehen; sie dokumentieren ihre jeweiligen Stände. **Maßgeblich für den heutigen Zählstand ist
> dieser Anhang.**

**Zählung, in dieser Revision selbst gemessen** (Muster `^- \[x\] ` / `^- \[ \] `, Plan
2026-09-25; **vorher** `^- \[x\]` = **59**, `^- \[ \]` = **140**, Partitionsmessung
`1:` = 33, `2:` = 34, `3:` = 33, `4:` = 35, `5:`–`9:` = 5, **keine** Nicht-Ziffer-Zeile):

| Größe | Wert | Herleitung / Beleg |
|---|---|---|
| `^- \[x\]` (gesetzt) | **59** | **unverändert** — in dieser Revision wurde **keine** Checkbox gesetzt, gestrichen oder umgeschrieben |
| `^- \[ \]` (offen) | **140 → 148** | **+8** aus **zwei** neuen Tasks mit je **4** Steps: **W2-9** (E-8) und **W2-8** (E-6) |
| **Summe** | **199 → 207** | Partitionsmessung nach dem Edit: `1:` = 35, `2:` = 36, `3:` = 35, `4:` = 37, `5:`–`9:` = 5 ⇒ **148** offen; **59 + 148 = 207** ✓ |
| **Gegenprobe über die Tasks** | **44 × 4 + 5 × 5 + 1 × 6 = 207** | **50** Tasks: **44** mit 4 Steps · **5** mit 5 Steps (W2-0, W2-1, W2-7, W4-3, W5-2) · **1** mit 6 Steps (W8-4). **48 → 50** durch **W2-9** und **W2-8** (beide 4 Steps) |
| **Taskzahl** | **48 → 50** | Katalog: Rev. 0.4 = 47 · Rev. 0.6 = 48 (K39, + W2-0) · **Rev. 0.7 = 50** (K56, + W2-9, + W2-8) |

**Keine Zahl ist geschätzt.** Die Herleitung ist **rechnerisch** (44 × 4 + 5 × 5 + 1 × 6) **und**
**partitionell gemessen**; beide stimmen überein. **Grenze der Messung, wie in K34:** die
Zählung ist eine Zeilenmessung dieses Dokuments; stimmt ein künftiger Zähler nicht mit **59 / 148**
überein, ist **hier** zu korrigieren, **nicht** in der Task-Struktur.

**Ende der K53-Interim-Regel — ausdrücklich, terminiert (E-8, K57).** Die K53-Interim-Regel
(Checkboxen **von Hand** durch den Orchestrator, ohne `scripts/lib/plan_ledger.py`) gilt
**unverändert bis einschließlich dem Task W2-9**. **Mit dem Commit von W2-9** entfällt sie
**ausdrücklich** (Task W2-9 Schritt 3). **Danach** gilt: `plan_ledger` adressiert diesen Plan, und
**keine** Checkbox wird von Hand gesetzt. **Der erste mit dem Werkzeug abzuhakende Task ist W2-6.**
**Ausdrücklich nicht behauptet:** der Ledger-Writer ist **heute** einsetzbar — er ist es **nicht**;
erst ab W2-9. **Wird W2-9 zurückgerollt** (W2-Rollback Stufe 3), ist die Interim-Regel **wieder** zu
aktivieren.

**Aufgabenstand W2 nach dieser Revision (additive Aktualisierung, K53-Block bleibt wortgleich).**

| Task | Checkboxen | Stand 2026-09-27 (Rev. 0.7) |
|---|---|---|
| **W2-0** | **5/5** | abgehakt (`b5bb0fe9`) — unverändert |
| **W2-1** | **5/5** | abgehakt — unverändert |
| **W2-2** | **4/4** | abgehakt — unverändert |
| **W2-3** | **4/4** | abgehakt (`8594e67f`) — unverändert |
| **W2-5** | **4/4** | abgehakt (`b73e9422`) — unverändert |
| **W2-4** | **0/4** | **offen.** **Rev. 0.7 / E-7:** `Files:` umgestellt (zwei neue Dateien); das alte Abnahmekriterium (`docs_freshness.py` < 600) ist **ersetzt** durch zwei (`docs_freshness_v5.py` < 600 **und** `docs_freshness.py` ≤ 600) |
| **W2-6** | **0/4** | **offen.** Working Tree enthält bereits `docs_index.py` (211 Z), `tests/test_doc_index.py` (413 Z) und die V4-Verbreiterung in `docs_links.py` (404 Z, +86/−16) — **uncommittet, von dieser Revision nicht angefasst.** **Rev. 0.7 / E-5:** der V4-Teil dieser Task ist **gegenstandslos geworden** (Scope-Umstellung statt Verallgemeinerung) und wird neu umgesetzt; Modul-Tests 208 passed, Volltests **2** rot (Ursache: die **193** aus der Verallgemeinerung — **K60**, nicht 191). **Korrekturrunde 5 (K61 / K67):** die im Working Tree vorhandenen **sieben** V4-Tests in `tests/test_doc_index.py` pinnen die entfernte Per-Seiten-Semantik (4 **rot**, 3 **vakuum-grün mit falscher Semantik**) und werden **namentlich ersetzt**, nicht angepasst; die Ersatzungsliste steht in W2-6. **K62:** `scripts/lib/consistency/spec_plan.py` (Dep-Token-Muster) kommt zu W2-9s `Files:` |
| **W2-8** | **0/4** | **offen, neu (Rev. 0.7, E-6).** Nimmt die zwei roten Volltests auf; Position unmittelbar vor W2-7 |
| **W2-9** | **0/4** | **offen, neu (Rev. 0.7, E-8).** Phase 0; macht den Ledger-Writer einsetzbar |
| **W2-7** | **0/5** | **offen.** **Rev. 0.7:** `Depends on` um **W2-8** erweitert |

**Damit überholt, ohne Umschreiben (Historie bleibt wortgleich):** die Zählhinweise in **K34** und
im **K53-Interim-Ledger** nennen **46 / 153** bzw. **59 / 140**; sie beschreiben den Stand **vor**
dieser Revision. **Maßgeblich ist dieser Anhang.**

#### Anhang 2026-09-28 — Ausführungsstand W2 Phase 0 (W2-9, W2-6)

> **Was dieser Anhang ist — und was nicht.** Wie die beiden vorangehenden Blöcke ist er **additive
> Statuspflege**: **keine** Plan-Revision, **keine** Korrekturrunde, **kein** Eingriff in eine als
> wortgleich festgeschriebene Stelle. **Wortgleich bleiben:** `status: APPROVED` (`:5`),
> `revision: 0.7` (`:6`), die **K34-Kopfnotiz**, die historische Tabelle (Stand 2026-09-26), die
> Herleitungen **188 → 190 → 194 → 199 → 207**, der **K53-Interim-Ledger**, der **Rev.-0.7-Anhang**,
> alle Task-/Wellen-/AC-/IC-/NFA-/R-/OQ-/V-Check-IDs, alle Akzeptanzkriterien, die Korrekturrunden
> **1–6** und ihr Zuordnungsregister. **Keine bestehende Zeile wurde entfernt, ersetzt oder
> umformuliert.** **Zwei ausdrücklich benannte Ausnahmen, beide rein additiv und beide
> nachprüfbar:** (1) die **K-Legendenzeile `:536`** ist um **K76** verlängert worden (rein additiver
> Einschub, der übrige Zeilenwortlaut unverändert); (2) an **drei** Stellen **außerhalb** dieses
> Anhangs wurde ein **`Datei:Zeile`-Anker** durch einen Zusatz in Klammern ergänzt — **`File Structure`**
> (Abschnitt „Geändert (Code)"), der Kommentar der Zeile `spec_plan.py` in **`Rollback W2`** und die
> **`spec_plan.py`-Zelle der Ownership-Matrix**. **Warum genau diese drei:** es sind die einzigen
> Fundstellen des Ankers, die **kein Task-Verbatim-Text** sind; alle drei wurden bereits in
> Korrekturrunde 6 (**K71**) als bearbeitbare Live-Stellen geführt. **Kein** Tasktext, **keine**
> Checkbox, **keine** ID, **kein** Sollwert und **keine** Datei außerhalb dieses Plans wurde
> angefasst — die Begründung und die vollständige Fundstellenliste stehen in **I**.
> Maßgeblich für den heutigen Ausführungsstand ist **dieser** Anhang (K34-Präzedenz).
>
> **Zwei Nummernkreise, ausdrücklich getrennt.** Die **eine** neue K-Kennung dieses Anhangs
> (**K76**) dokumentiert eine **Ausführungs-Korrektur** (F, Datum, Grund). Alles Übrige hier ist
> **Status** und trägt **bewusst keine** K-Kennung — dieselbe Zurückhaltung wie in den beiden
> vorangehenden Anhängen.
>
> **Grenze der Messung, ausdrücklich getrennt.** (a) **Selbst gemessen** (Read/Grep/Glob im
> Working Tree, 2026-09-28): die Checkboxenzähler je Task, die Zustände der Quell-Dateien, die
> Zeilenanker in `scripts/…`, das **Fehlen** von `docs_freshness_v5.py` und
> `tests/test_doc_freshness_v5.py`; **ferner, im Zuge der Review-Runde vom 2026-09-28:** die
> **vollständige** Fundstellenerhebung des Ankers `spec_plan.py:570` über den ganzen Plan (Grep `:570`)
> und die `Agent:`-Angaben der fünf offenen W2-Tasks. (b) **Übergabemessung** (read-only-Git-Erhebung
> vom 2026-09-28, Parent; in diesem Anhang **nicht** selbst gemessen, weil kein Shell-Zugriff vorlag):
> die Commit-Hashes, der `git status --porcelain`-Stand und der Dateigrößenwert **276 Z** des
> Review-Artefakts. **Keine Zahl dieses Anhangs ist geschätzt**; jede ist entweder gemessen,
> übernommen oder ausdrücklich als **nicht gemessen** markiert.

**A. Arbeitsstand 2026-09-28 — Arbeitsbaum (Übergabemessung) und Commits.**

- **Uncommittet, `M` (5):** `scripts/lib/consistency/docs_links.py`,
  `scripts/lib/consistency/spec_plan.py`, `scripts/lib/plan_identity.py`,
  `tests/test_plan_identity.py`, `tests/test_plan_ledger_writer.py`.
- **Untracked (`??`, 3):** `docs/specs/2026-09-25-repository-documentation-consolidation-rereview-2.md`,
  `scripts/lib/consistency/docs_index.py`, `tests/test_doc_index.py`.
- **Nichts gestaged.** Committet sind **W2-0** (`b5bb0fe9`), **W2-2** (`8f290b95`), **W2-3**
  (`8594e67f`), **W2-5** (`b73e9422`), **W2-1** (V1-Commits) sowie die Ledger-/Plan-Commits
  `942fafe6`, `c1dda65d`, `c3ed5c9f`, `6505341c`, `1ef78386`, `c0988e18`, `4b5eaa94`;
  `4b5eaa94` („apply E-5..E-8, add W2-8 and W2-9 (rev 0.7)") ist **docs-only** (Plan + Spec).

**B. Zählstand je Task (selbst gemessen; Muster `^- \[x\] ` / `^- \[ \] `).**

| Task | Checkboxen | Stand 2026-09-28 | Ausführender (`Agent:`, **selbst gemessen**) |
|---|---|---|---|
| **W2-9** | **0/4** | implementiert, **nicht committet**, nichts verifiziert (Phase 0) — s. C | `senior-developer` — Phase 0, **erster** Task; **Eigentümer** des Anker-Auftrags in I(d) |
| **W2-6** | **0/4** | uncommitteter roter Zwischenstand mit **überholter** Implementierung — s. D | `developer` — E-5-Rework **in-place**; **Eigentümer** der Neuvermessung in I(b) |
| **W2-4** | **0/4** | **nicht gestartet** — s. E | `senior-developer` — Phase B, setzt W2-5 voraus |
| **W2-8** | **0/4** | **nicht gestartet** — s. E | `senior-developer` — Volltest-Entkopplung, unmittelbar vor W2-7 |
| **W2-7** | **0/5** | **nicht gestartet** — s. E | `developer` — Registrierung, **Wellen-Gate W2** |

- **Summen unverändert.** Dieser Anhang fügt **ausschließlich Fließtext und Tabellenzeilen** hinzu;
  **keine** Zeile beginnt mit `- [ ]` oder `- [x]`, es wurde **keine** Checkbox gesetzt, gestrichen
  oder ergänzt. Die Zählstände des Rev.-0.7-Anhangs (**59** gesetzt / **148** offen, Summe **207**)
  bleiben damit **gültig** — das ist eine **Ableitung aus der Art des Eintrags**, keine neue Zählung.
- **Damit überholt, ohne Umschreiben:** die Zeilen „W2-4 **0/4**", „W2-6 **0/4**", „W2-8 **0/4**",
  „W2-9 **0/4**" und „W2-7 **0/5**" des Rev.-0.7-Anhangs (Stand 2026-09-27) sind **heute richtig** —
  sie werden hier **nicht** wiederholt, weil sie sich nicht geändert haben. **Geändert hat sich nur
  der Begründungsstand** (C und D), und genau der ist neu.
- **Zur Anker-Disziplin der Owner-Spalte (K12).** Maßgeblich ist der **Abschnittsanker** — jeweils die
  `Agent:`-Zeile **im Task-Block selbst** —, **nicht** eine Zeilenzahl; Zeilenzahlen dieses Plans
  driften mit jedem Revisionsblock. **Nachgemessen** (2026-09-28, Kontrollwerte, **nicht** normativ):
  W2-9 `senior-developer`, W2-4 `senior-developer`, W2-6 `developer`, W2-8 `senior-developer`,
  W2-7 `developer`. **Genau diese fünf** sind die in der Reihenfolge F genannten Tasks — **kein**
  sechster, **keine** offene Frage, **keine** Abweichung zum Plan: die `Agent:`-Angaben im Plan und
  die Owner-Spalte hier stimmen **überein**.

**C. W2-9 (Phase 0) — implementiert, aber NICHT committet.** Write-Set **exakt wie im Plan**
(`Files:` des Task W2-9):

- `scripts/lib/plan_identity.py` (**106 Z**): `WAVE_ID_PATTERN` (`:26`) und die Wellen-Header-
  Alternative in `TASK_HEADER_RE` (`:35-47`) **mit** Zwei-Gruppen-Vertrag. `TASK_ID_RE` (`:18`) und
  `normalize_task_id` (`:83`) sind **unangetastet** — das ist die verbindliche **K66**-Lesart
  („W2-9 ändert ausschließlich (a); eine Reparatur von (b) ist verboten").
- `scripts/lib/consistency/spec_plan.py` (**607 Z**): das neue `_DEP_TOKEN_RE` (`:68`), benutzt in
  `_parse_plan_tasks` (`:581`); die Regex-Bindung `_TASK_HEADER_RE` (`:55`) steht. Das ist **K62**.
- `tests/test_plan_identity.py`, `tests/test_plan_ledger_writer.py` (beide `M`).
- `scripts/lib/plan_ledger.py` ist **clean** — das ist **korrekt** und **kein** fehlender Write-Set:
  der Plan führt die Datei nur **bedingt** („Modify … **bedingt** — nur falls sich der
  Zwei-Gruppen-Vertrag des Treffers ändert; im Normalfall **read-only**"). Ein Eingriff dort wäre
  **nicht** durch `Files:` gedeckt.
- **Folge für das Ledger: die K53-Interim-Regel gilt unverändert weiter.** E-8/K57 sagt wörtlich:
  sie „gilt **unverändert bis einschließlich dem Task W2-9**"; erst „**mit dem Commit von W2-9**"
  entfällt sie. Da nichts committet ist, entfällt sie **nicht**. Der Rev.-0.7-Anhang sagt dasselbe:
  „der Ledger-Writer ist **heute** einsetzbar — er ist es **nicht**; erst ab W2-9". **Also: bis zum
  Commit von W2-9 keine Checkbox von Hand setzen**; ab dem Commit von W2-9 übernimmt
  `plan_ledger`, und **der erste mit dem Werkzeug abzuhakende Task ist W2-6** — genau die Reihenfolge
  in F.

**D. W2-6 — uncommitteter roter Zwischenstand, der eine ÜBERHOLTE Implementierung enthält. Kein
Reparatur-, sondern ein E-5-Rework-Task.**

- **Gemessen im Working Tree** (`scripts/lib/consistency/docs_links.py`, **404 Z**): `_v4_in_scope`
  (`:122-140`), `_v4_unlinked_relpaths` (`:143-164`), `check_readme_docs_index` (`:167-198`).
- **Was dort steht:** V4 als **Seiten**-Scan — „jede in-scope-Seite unter `docs/` muss in `README.md`
  verlinkt sein", als **rekursiver Walk** (`rglob`, `:156-160`), `archive/`/`_archive/` ausgenommen
  (`:140`). Das ist das Design **Rev. 0.6 / vor E-5**.
- **Was Rev. 0.7 / E-5 verlangt** (K54, K59–K65, K68): Extraktion der **sieben** deklarierten
  Kategorien aus der `##`-Region, deren Text `Documentation Index` enthält; **fail-soft-Guard zuerst**
  (fehlender `docs/`-Baum ⇒ `[]`), **danach** fail-closed; **Signatur `(root)` einargumentig
  unverändert**; Sollwert am echten Baum **genau 1** Finding (Kategorie `docs/se-cascade/`).
- **Gemessene Abweichung:** die Vorrangregel ist **nicht** umgesetzt — `docs_links.py:183` behandelt
  `not readme.exists() or not docs_dir.is_dir()` **gemeinsam** und liefert damit **immer** `[]`.
- **Die K68-Docstring-Korrektur ist nicht erfolgt:** `docs_links.py:168-177` trägt weiter den
  Vor-E-5-Wortlaut, einschließlich „Only the **scope** widened — … to the whole ``docs/`` tree"
  (`:172-174`) und „The pre-W2 subset stays a real subset" (`:176-177`).
- **Konsequenz, ausdrücklich:** W2-6 wird **in-place** umgesetzt — **kein** `git checkout`, **kein**
  Löschen, **kein** Reset der drei Dateien. **Der Diff ist die Historie.** Die **sieben** namentlich
  zu ersetzenden V4-Tests stehen in der Ersetzungstabelle **R1…R7** im Task W2-6 (`Akzeptanz V4`) und
  werden **ersetzt, nicht angepasst** (K61). Das ist der Grund, warum W2-6 den **ersten** abzuhakenden
  Task nach W2-9 ist: bis dahin wird das Ledger **nicht** von Hand gepflegt.

**E. Nicht gestartet: W2-4, W2-8, W2-7.**

- **W2-4 (0/4):** `scripts/lib/consistency/docs_freshness_v5.py` und
  `tests/test_doc_freshness_v5.py` **existieren nicht** (Dateisuche am 2026-09-28). Die
  Voraussetzung ist erfüllt — **W2-5** ist committet (`b73e9422`), womit der Größennachweis
  „`docs_freshness.py` bleibt 592" beobachtbar ist. W2-4 bleibt der Grund, warum **W2-8** nicht schon
  jetzt laufen kann (Kante **17** `W2-4 → W2-8`).
- **W2-8 (0/4):** nicht gestartet; `tests/test_knowledge_engine.py` und
  `tests/test_sharkord_service_name_migration.py` sind im Arbeitsbaum **nicht** als `M` geführt.
- **W2-7 (0/5):** nicht gestartet. `Depends on: W2-3, W2-4, W2-5, W2-6, W2-8` — davon sind **alle**
  fünf Voraussetzungen bis auf W2-4, W2-6 und W2-8 erfüllt.

**F. Ausführungs-Protokoll 2026-09-28 — verbindliche Reihenfolge (K76).**

> **Reihenfolge (Plan-DAG, bindend):** **`W2-9` (Phase 0) → `W2-6` → `W2-4` → `W2-8` → `W2-7`
> (Wellen-Gate W2).**

- **Die Reihenfolge ist nicht neu entschieden, sondern aus dem bestehenden DAG abgelesen.** Vier
  Belege, alle im Plan:
  1. **Kante 16** (`W2-0 → W2-9`) nennt die Reihenfolge der danach noch offenen Tasks **wörtlich**:
     „W2-9 beendet die K53-Interim-Regel und muss vor **allen** noch offenen W2-Tasks laufen —
     **W2-6, W2-4, W2-8, W2-7**".
  2. **Topologische Ordnung** (Zyklenprüfung): `… → W2-0 → W2-9 → {W2-3, W2-5, W2-6} → W2-4 → W2-8 →
     W2-7 → …`; von der Gruppe `{W2-3, W2-5, W2-6}` ist nach dem Ledger nur **W2-6** offen.
  3. **Kanten 17** (`W2-4 → W2-8`) und **18** (`W2-8 → W2-7`) sowie `W2-7 Depends on: W2-3, W2-4,
     W2-5, W2-6, W2-8` (Rev. 0.7).
  4. **K63 / E-6** begründet W2-8s Position **unmittelbar vor W2-7**: sein Nachweis prüft „den Zustand
     **kurz vor** der Registrierung" und belegt die Entkopplung „**vor** dem Wellenabschluss … nicht
     erst, wenn die Welle schon rot ist".
- **Kein Parallelismus mehr in W2 (Ableitung, keine Messung).** PG-2a = {W2-3, W2-5, W2-6} ist nach
  dem Ledger auf **W2-6** zusammengeschrumpft; PG-2b, PG-2d, PG-2c, PG-2e sind Einzeltasks. Die
  verbleibende W2-Arbeit ist damit **sequenziell** — die Größe **3** gleichzeitiger Agenten wird
  nicht mehr erreicht.
- **K76 — Ausrichtung auf den DAG, mit Datum, Grund und Folgen.** Das **A2A-Envelope vom 2026-09-28**
  listete den separaten Testfix **nach** W2-7. Das ist **an den Plan-DAG angeglichen**: der Testfix
  ist **W2-8** und läuft **unmittelbar vor W2-7** (Kante 18, K63). **Grund:** der Volltest-Nachweis
  muss den Stand **kurz vor** der Registrierung prüfen, sonst belegt er einen Zwischenstand.
  **Ausdrücklich festgehalten, weil es die Form des Eingriffs begrenzt:** es wird **keine** Plan-ID
  umnummeriert (**W2-8** behält ID, Ort und Wortlaut im Plan), **kein** Akzeptanzkriterium geändert,
  **keine** Checkbox gesetzt, **kein** Sollwert geändert, **keine** AC/IC/R-/OQ-/V-Check-ID neu oder
  gestrichen, **keine** neue Task angelegt, **keine** Ownership-Zeile geändert. **K76 ersetzt keine
  Plan-Revision** (K34-Präzedenz) — `revision: 0.7` und `status: APPROVED` bleiben unverändert, und
  **kein Revisions-Bump ist nötig** (kein AC, kein Sollwert, keine ID, kein Widerspruch geändert).
- **K76 — die zwei Ausnahmen, ausdrücklich benannt (in der K-Legende mitvermerkt).** K76 weicht von
  der Praxis aller übrigen K-Kennungen **an genau zwei Punkten** ab, und **beide** sind **je einmalig**:
  **(1)** K76 ist die **erste K-ID ohne Review-Befund** — sie entsteht aus einer Ausführungsbeobachtung
  (DAG-Ausrichtung), nicht aus einem Finding eines Concept-Reviews; **(2)** mit K76 wurde **zum ersten
  Mal eine Zeile im Rev.-0.7-Kopfblock** geändert (die K-Legendenzeile selbst), rein additiv. **K76
  bleibt eine Korrektur-Kennung** im Sinne der Legende („kein Status, nur Auditierbarkeit") und **kein
  Status-Element** — die Zählstände dieses Anhangs bleiben davon unberührt.

**G. Verifikation von Ownership-Matrix (W2) und DAG-Kantenliste — read-only, nicht neu geschrieben.**

- **Ownership-Matrix W2: vollständig und konsistent — keine Lücke.** Read-only nachgezählt, **ohne**
  jede Korrektur: **9** Rev.-0.7-Dateizeilen (Kopfvermerk und Tabelle stimmen überein — die Lücke aus
  **K71** ist damit geschlossen); **W2-9 = 5** `owns`-Zeilen; **W2-9 + W2-8 = 7**; **W2-4** `owns`
  genau die **zwei** neuen E-7-Dateien und trägt bei `docs_freshness.py` /
  `tests/test_doc_freshness.py` ausdrücklich „**nicht mehr** — E-7"; **W2-7** `owns` genau **fünf**
  Dateien (**K46**-Lesart); Raster **10 Spalten** (Datei + 9 Tasks) in Kopf und **23** Datenzeilen
  ohne Spaltenversatz. **K71 wird hier ausdrücklich nicht wiederholt, sondern nur bestätigt.**
- **DAG-Kantenliste: vollständig — keine Lücke.** Kanten **1–15** in der Tabelle, **16/17/18**
  additiv angehängt (Nummerierung fortgesetzt, keine bestehende Nummer geändert); die
  Parallelgruppenliste nennt **PG-2a/2b/2c/2d/2e**; die Zyklenprüfung trägt die Rev.-0.7-Ordnung und
  stimmt mit der Kantenliste überein.
- **Einzige Beobachtung, kein Widerspruch:** die Zelle `scripts/lib/consistency/spec_plan.py` trug
  einen **Vor-Implementierungs**-Anker (damals „Dep-Token-Muster **`:570`**"). **Er ist inzwischen an
  Ort und Stelle korrigiert** (`:570` → nach W2-9 `_DEP_TOKEN_RE` `:68`); die Matrix bleibt **10** Spalten
  breit und der Zählstand **9 / 5 / 7 / 23** ist unverändert. Vollständige Fundstellen und Auftrag:
  **I**.

**H. Das unversionierte Review-Artefakt — Eingangsgrundlage der Korrekturrunden 5 und 6.**

- `docs/specs/2026-09-25-repository-documentation-consolidation-rereview-2.md` (**276 Z**, `??`,
  **nie mitcommittet**) ist die **Eingangsgrundlage** beider Runden: **Runde 2 = Korrekturrunde 5
  (K59…K70)**; die Findings **NEU-1…NEU-4** desselben Artefakts = **Korrekturrunde 6 (K71…K75)**,
  jeweils über das **Re-Review 3** (R3-1, R3-2) nachgeschärft, dessen Notizen im Plan-Text stehen
  (es existiert **kein** separates Re-Review-3-Artefakt).
- Verdikt **`CHANGES_REQUESTED`**, 0 kritisch · **1 major** · 4 minor · 1 info. Die **1 major**
  (NEU-1 → **K71**) ist behoben; das Verdikt selbst bleibt **unverändert** stehen, weil es den
  damaligen Prüfstand dokumentiert.
- **Es wird mit committet — ohne Inhaltswechsel.** Das Artefakt ist **Eingangsdokument**, kein
  Editier-Ziel: kein Kommentar, keine Korrektur, keine Ergänzung, keine neue Verdiktzeile. Der
  Frontmatter-Stand (`review-id: RVW-DOCS-CONSOLIDATION-R2`, `subject-revision: 0.7`, `round: 2`)
  bleibt unangetastet. **Es wird auch kein Folgedokument erzeugt**, das es ersetzt.

**I. Befund — Ankerdrift: Vollständige Fundstellen, Ist/Soll-Trennung und Auftrag mit Owner/Frist.**

> **Herkunft dieses Abschnitts.** Die erste Fassung dieses Anhangs meldete denselben Befund, aber
> **unvollständig** (drei statt fünf Live-Stellen), mit einer **vertauschten Zustandszuordnung** und
> mit einer **unzulässigen Delegationsbegründung** (K48 in umgekehrter Bedeutung, ohne Owner/Frist).
> Beides ist im Concept-Review `docs/concepts/concept-review-ownership-amendments-2026-09-28.md`
> (2026-09-28, Verdikt `CHANGES_REQUESTED`, 3 major / 3 minor) beanstandet worden. Die Befunde
> **M1**, **M2**, **M3** sowie **m1**–**m3** sind hier abgearbeitet; die Fundstellen wurden
> **vollständig neu erhoben**, nicht aus dem Review übernommen.

- **(a) `spec_plan.py:570` — vollständige Erhebung: 5 Live-Stellen, 3 geschützte Aufzeichnungen, 1
  Fehltreffer.** **Selbst gemessen** (Grep `:570`, 2026-09-28) über den **ganzen** Plan:

  | # | Stelle | Status | Behandlung |
  |---|---|---|---|
  | 1 | **`File Structure`** → „Geändert (Code) → `spec_plan.py`" | **Live-Inventar** (in Korrekturrunde 6 durch **K71** bearbeitet) | **hier korrigiert** — `:570` ist als **Vor-Implementierungs-Anker** gekennzeichnet, Ist-Ort `_DEP_TOKEN_RE` `:68` / Verwendung `:581` genannt |
  | 2 | **`Rollback W2`**, Bash-Kommentar `# W2-9 (K71): Dep-Token-Muster :570` | **Live-Block** (Zeile von **K71** ergänzt) | **hier korrigiert** — gleiche Kennzeichnung; der Historic-Anker `:570` bleibt sichtbar |
  | 3 | **Ownership-Matrix**, Zelle `spec_plan.py` | **Live-Abschnitt** (Zeile von **K71** ergänzt) | **hier korrigiert** — „Dep-Token-Muster **`:570`**" → nach W2-9 „**`_DEP_TOKEN_RE` `:68`**" |
  | 4 | **Task W2-9 `Interfaces`** | **Task-Verbatim-Text** | **nicht** angetastet → **Auftrag** an `senior-developer`, Frist: **mit dem Commit von W2-9** (siehe unten) |
  | 5 | **Task W2-9 `Schritt 2`** (live Anweisung: „Dep-Token-Muster in `scripts/lib/consistency/spec_plan.py:570` erweitern") | **Task-Verbatim-Text** | **nicht** angetastet → **Auftrag** an `senior-developer`, Frist: **mit dem Commit von W2-9** (siehe unten) |
  | 6 | **K62-Katalog** im Kopf-Block der Korrekturrunde 5 | **wortgleich geschützt** | **bewusst ausgelassen** — dokumentiert den Stand der Korrekturrunde 5 |
  | 7 | **Zuordnungsregister Korrekturrunde 5**, Zeile `RVW-7-04` | **wortgleich geschützt** (Korrekturrunden 1–5) | **bewusst ausgelassen** |
  | 8 | **Zuordnungsregister Korrekturrunde 6**, Zeile `NEU-1` | **wortgleich geschützt** (Befundsatz) | **bewusst ausgelassen** — **Folge, ausdrücklich:** dieses Register zitiert die Matrix-Zelle **wortgleich mit `:570`**; die Korrektur oben macht das Zitat zum Stand **vor** dieser Korrektur und wird über die **K71-Lesart-Regel** aufgelöst (dieselbe Mechanik, mit der K71 den `E-8`-Record auflöst) |
  | — | `plan:570` **innerhalb von Task W1-10** (Absenz-Default IC-22) | **Fehltreffer** | ein **Planzeilen**-Verweis (auf den OQ2-Record), **kein** `spec_plan.py`-Anker — zu Recht nicht als Fundstelle geführt |

  **Nach der Korrektur dieses Anhangs: 2 Live-Stellen** (Nr. 4 und 5) sind offen, **3** sind behoben.
  **Das Betriebsrisiko ist damit kleiner, aber nicht null:** W2-9 `Schritt 2` bleibt bis zum Commit
  eine **live Anweisung**, die auf `:570` zeigt. Siehe den Auftrag unten.

- **(b) `check_readme_docs_index` — Ist und Soll sind getrennt und dürfen nicht verwechselt werden.**
  - **Ist (gemessen, Working Tree 2026-09-28, uncommitteter Zwischenstand):** die Funktion liegt bei
    **`docs_links.py:167-198`**; `_v4_in_scope` `:122-140`, `_v4_unlinked_relpaths` `:143-164`,
    fail-soft-Zeile `:183`, Docstring `:168-177`. **Diese Werte beschreiben den Zwischenstand vor dem
    E-5-Rework** — sie sind heute korrekt und werden **nicht** zu Sollwerten erklärt.
  - **Der Plan-Anker ist bereits heute veraltet.** `docs_links.py:121-…` (Task W2-7) stammt aus der
    **K48**-Tabelle (Korrekturrunde 4) und ist gegenüber dem Working Tree **schon jetzt** verrutscht.
    Es ist ein **Vor-Implementierungs-Anker**, kein Sollwert.
  - **Soll (nach dem E-5-Rework, W2-6): nicht vorab bestimmbar.** Der Funktionsrumpf wird ersetzt
    (K54/K59–K65/K68: Kategorie-Extraktion statt Seiten-Scan), die Docstring-Korrektur **K68** kommt
    hinzu ⇒ die Position **nach** dem Rework lässt sich **nicht** vorab als Zeilenzahl festschreiben.
    **Es wird deshalb ausdrücklich kein Soll-Anker gesetzt.** **Die Korrektur ist: neu messen beim
    Commit von W2-6**, nicht auf eine vorab geratene Zeile umschreiben.
  - **Gleiches gilt für die W2-6-eigenen Anker** (`docs_links.py:167`, Docstring `:170-172` in
    `Interfaces`): sie sind **Ist-Messungen** des heutigen Zwischenstands und **kein** Zielwert. Auch
    sie sind erst **nach** dem Rework neu zu messen — **beide** Anker bleiben deshalb unverändert und
    sind **kein** Befund, weil sie als Ist zutreffend sind.

- **(c) Bewertung unverändert: kein Widerspruch.** Keine ID, kein Sollwert, kein Akzeptanzkriterium und
  keine Ownership-Entscheidung sind betroffen — es ist **Ankerdrift**, dieselbe Klasse wie
  **K47/K48/K72**. Die betroffenen Stellen sind **nicht** als wortgleich festgeschrieben (Ausnahme:
  die drei Befundsaufzeichnungen in der Tabelle zu (a), die **bewusst** ausgelassen bleiben).

- **(d) Auftrag statt Empfehlung — die Delegation ist regelkonform belegt.** Die erste Fassung stützte
  die Aufschiebung auf **K48**; das war **in umgekehrter Richtung falsch**: K48 ist eine
  **In-place**-Regel („unvollständig, nicht falsch" → vollständig erfassen), **keine** Aufschiebung.
  **K48 wird hier nicht mehr als Delegationsbegründung angeführt.** Stattdessen gilt der Mechanismus,
  den dieser Plan für genau diesen Fall bereits etabliert hat: die **K71-Lesart-Regel** — eine Stelle
  nennt den Stand **vor** der Änderung und wird dadurch aufgelöst, **ohne** einen wortgleichen Block
  anzufassen. **Belege, die die Delegation tragen:**
  1. **Owner benannt:** `senior-developer` — der Agent des Tasks **W2-9** (`Agent:`-Zeile des Tasks,
     **selbst gemessen**). W2-9 **besitzt** `spec_plan.py` (`Files:` des Tasks; Ownership-Matrix
     `owns`-Zelle) und **verursacht** den Anker, weil W2-9 die Datei schreibt. Ein Task kann seine
     eigenen Anker nicht einem anderen Task überlassen.
  2. **Frist benannt:** **mit dem Commit von W2-9**, spätestens im **LEDGER-Stand-Vermerk von W2-9**
     (dessen Schritt 4). Eine Frist ohne benannten Task und ohne Zeitpunkt wäre unterdeterminiert.
  3. **Exakter Änderungsauftrag** (nachträglich anführbar, additiv, am K71-Muster): in W2-9
     `Interfaces` **und** in `Schritt 2` **je einen** Lesart-Satz ergänzen — *„der Anker `:570` ist ein
     **Vor-Implementierungs-Anker**; nach dem Commit gilt `_DEP_TOKEN_RE`
     (`scripts/lib/consistency/spec_plan.py:68`, Verwendung `:581`)"*. **Nur** dieser Satz, **kein**
     Eingriff in den übrigen Tasktext, **keine** Änderung von `Files:`, Akzeptanz oder Schrittzahl.
  4. **Warum hier nicht selbst korrigiert:** beide Stellen liegen im **Task-Verbatim-Text**. Der
     Auftrag dieses Anhangs ist **append-only** (K34-Präzedenz) und umfasst **nicht** den Tasktext.
     Eine eigene Einfügung dort würde genau die Wortlautgrenze verletzen, die K36/K42 als Fehler
     behandeln — die drei Stellen oben wurden stattdessen **an Ort und Stelle** korrigiert, weil sie
     **kein** Tasktext sind.

- **(e) Keine neue K-Kennung für diese Runde — bewusst entschieden.** Die Befunde **M1/M2/M3** und
  **m1**–**m3** sind **additive Berichtigungen dieses Anhangs**; ihr Register ist das Review-Artefakt
  `docs/concepts/concept-review-ownership-amendments-2026-09-28.md`, in dem jedes Finding eine eigene
  ID trägt. **K76 bleibt die höchste K-Kennung** — es wird **nichts** umnummeriert und **keine** ID
  vergeben. **Ausdrücklich abweichend vom Muster K72** (dort vergab die Korrekturrunde eine K-ID für
  einen Anker-Fix): hier liegt **kein** Korrekturgrund **im Plan**, sondern in **einem eigenen
  Anhang**; eine neue K-ID im Plan-Kopf würde den Katalog des Vorhabens mit einem Befund belasten, der
  den Plan selbst nicht betrifft. **Diese Entscheidung ist damit prüfbar und ggf. anfechtbar.**

**J. Was dieser Anhang ausdrücklich nicht behauptet.** Kein Task ist abgehakt. Kein Volltestlauf
wurde ausgeführt, kein `sync.py`, kein `pytest`, keine Git-Mutation. Die **1 major** des Reviews ist
über **K71** im *Plan* behoben — die **Verifikation im Working Tree** steht aus. W2-9 ist
implementiert, aber **nicht verifiziert** und **nicht committet**; W2-6 enthält eine Implementierung,
die **ersetzt**, nicht **repariert** wird. Das Wellen-Gate **W2** ist **nicht** erreicht.
#### Anhang 2026-09-28 (b) — Ausführungsstand W2-7 (Registrierung, Common-Gate, F1-Promotion)

> **Was dieser Anhang ist — und was nicht.** Wie die drei vorangehenden Blöcke ist er **additive
> Statuspflege**: **keine** Plan-Revision, **keine** Korrekturrunde, **kein** Eingriff in eine als
> wortgleich festgeschriebene Stelle, **keine** neue K-Kennung und **keine** umnummerierte ID.
> **Wortgleich bleiben:** `status: APPROVED` (`:5`), `revision: 0.7` (`:6`), die **K34-Kopfnotiz**,
> die historische Tabelle (Stand 2026-09-26), der **Rev.-0.7-Anhang** (Stand 2026-09-27), der
> vorangehende Anhang (Stand 2026-09-28, Phase 0), die Zählherleitungen, alle Task-/Wellen-/AC-/IC-/
> NFA-/R-/OQ-/V-Check-IDs, alle Akzeptanzkriterien und die Korrekturrunden **1–6**. **Keine bestehende
> Zeile wurde entfernt, ersetzt oder umformuliert.** Maßgeblich für den heutigen Ausführungsstand ist
> **dieser** Anhang (K34-Präzedenz).

**A. Einordnung der drei Fundstellen, die `W2-7 | 0/5` zeigten — einzeln gemessen, zwei Fälle.**

| Fundstelle | Tabelle (Kopfzeile) | Einordnung | Behandlung |
|---|---|---|---|
| `:6366-6384` | `### L-1 Checkbox-Abgleich`, Spalte **„Stand 2026-09-26"**, unter der **K34-Kopfnotiz** (`:6358`), die ausdrücklich sagt, die Tabelle bilde den Fortschritt **noch nicht** ab | **historisch, datiert** | **nicht** umgeschrieben |
| `:6533-6544` | `#### Rev.-0.7-Anhang zu L-1 (2026-09-27)`, Spalte **„Stand 2026-09-27 (Rev. 0.7)"**; der Block selbst sagt `:6546` „Damit überholt, ohne Umschreiben (Historie bleibt wortgleich)" | **historisch, datiert** | **nicht** umgeschrieben |
| `:6601-6607` | `#### Anhang 2026-09-28 — Ausführungsstand W2 Phase 0`, Spalte **„Stand 2026-09-28"** | **historisch, datiert** (siehe Begründung) | **nicht** umgeschrieben |

**Begründung zur dritten Fundstelle, weil sie die einzige nahe Grenze ist.** Sie trägt das Datum des
heutigen Tages und ist damit die **jüngste** Tabelle — aber sie ist **kein laufender Zähler**: sie ist
ein **datierter Phasen-0-Ausführungsstand** (W2-9, W2-6), und ihre **Geschwisterzeilen sind ebenso
überholt** (`:6605` **W2-4 `0/4` „nicht gestartet"**, `:6606` **W2-8 `0/4` „nicht gestartet"** — beide in
zwischen erledigt). Nur die W2-7-Zeile fortzuschreiben hieße, eine Tabelle intern widersprüchlich zu
machen und die Nachbarzeilen im Format **nicht** mitzuführen; die Vorgabe „wenn sie das Format der
anderen laufenden Einträge behält" wäre damit verletzt. **Deshalb gilt für alle drei derselbe Fall**,
und der Weg, den dieser Plan für einen newer-than-Stand bereits vorgesehen hat, ist ein **neuer
datierter Anhang** — genau der über W2-1, W2-4, W2-6 und W2-8. **Befund, nicht hier behoben:** die
Zeilen W2-3, W2-4, W2-5 und W2-8 der dritten Tabelle sind ebenfalls veraltet; sie gehören in die
Anhänge der Tasks, die sie abschließen, und werden hier **nicht** fremd fortgeschrieben.

**B. Zählstand W2-7 (selbst gemessen, 2026-09-28; Muster `^- \[x\] ` / `^- \[ \] ` im Task-Block).**

| Task | Checkboxen | Stand 2026-09-28 | Ausführender (`Agent:`, **selbst gemessen**) |
|---|---|---|---|
| **W2-7** | **5/5** | **implementiert und verifiziert, nicht committet** (No-Commit-Task; Schritt 5 nennt nur den Commit-Titel) | `developer` — Registrierung, Common-Gate, `Finding`-Vertrag; **Eigentümer des Wellen-Gates W2** |

- **Nachweis der Zählung:** `W2-7` besitzt **5** Checkboxen, alle **5** auf `- [x]` (Task-Block
  `:3870-…`, `**Steps:**` `:3966-3985`); **0** offen. Gesamt über den Plan: **50** Tasks
  (unverändert), Checkboxen-Summe **207** (unverändert — dieser Anhang setzt **keine** Checkbox).
- **Was der Fortschritt inhaltlich ist:** V1…V7 über **eine** Registrierungstabelle `DOCS_CHECKS`
  (`scripts/consistency-check.py`) registriert, alle **7** über **ein** Fail-off-Common-Gate
  (`docs-consolidation.enabled`) geführt, `line`/`branch` als **Dataclass-Felder** mit Default in
  `Finding` und im `--json` serialisiert, Exit-Code-Vertrag **0/1/2** unverändert.
- **Nicht behauptet:** der rohe Runner ist **planmäßig rot** (Exit **1**), die Verifikationszeile
  ``bash tests/scenarios/run.sh 50 51 52 54 55 56 → 0`` ist **unerreichbar**, und zwei
  Sollwert-Ist-Differenzen gegen `W2-GATE-ERRORS` sind **offen**. Das steht vollständig in der
  **Task-Notiz an W2-7** und wird hier **nicht** wiederholt.

**C. Summen und Zähler unverändert.** Dieser Anhang fügt **ausschließlich** Fließtext und
Tabellenzeilen hinzu; **keine** Zeile beginnt mit `- [ ]` oder `- [x]`, es wurde **keine** Checkbox
gesetzt, gestrichen oder ergänzt, **kein** Task angelegt und **keine** ID vergeben. Taskzahl **50**,
Checkboxen-Summe **207** und `files_touched("W2-7") == ()` bleiben damit **gültig** — Ableitung aus der
Art des Eintrags, keine neue Zählung.


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
  **ebenfalls unerreichbar** — belegt am Working Tree: V7 rot bis **W5-3** (~~10~~ **11** Wiki-Seiten
  `type: "Architecture"` ohne `derived-from`; **K24** — die 10 ist der **historische** Stand vom
  2026-09-26, maßgeblich ist die Baseline-Messung 2026-09-27 mit **11**), V3 rot bis **W8-2**
  (`README.md:722-723`; **K30** — und unter `docs/**` **dauerhaft**, Follow-up, K22), V2 rot
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

**Zählung L-3, Rev. 0.6 (K18…K24): unverändert 18 Zeilen.** Rev. 0.6 fügt **keine** neue
Errata-Zeile hinzu — die sieben Korrekturen K18…K24 sind **Plan-/Spec-Korrekturen**, keine
Ausführungsbefunde, und stehen deshalb im **Rev.-0.6-Kopfblock** und in der **Ownership-Matrix**,
nicht in dieser Liste. Die bestehenden Zeilen bleiben **wortgleich**; zwei berühren Rev. 0.6
inhaltlich und sind **markiert statt geändert**: **E-15** (`report.py`-Eigentümerlücke) bleibt bei
**W2-7** — W2-0 fasst `report.py` **nicht** an; **E-12** (`kind`-Vokabular des V6-Komparators) bleibt
bei **W2-5**, das den Check nun in `docs_freshness.py` statt `docs.py` schreibt — der
**Vertriffsbegriff** (`expected-mismatch`) ist unverändert, nur der **Ort** ändert sich.

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

- **Rev. 0.6 (K22) — AC-30 verengt ⇒ DoD Punkt 2 im Erwartungswert von V3 nachgezogen.** Die
  DoD-Zeile „V1…V8 = 0" ist mit der U-2-Verengung **nicht erfüllbar**, weil V3 unter `docs/**`
  dauerhaft **25** ERROR-Findings meldet. **Korrigiert wird ausschließlich der Erwartungswert von
  V3:** „**V3 = 0 im AC-30-Scope** (`README.md`, `llms.txt`) · die **25** `docs/**`-Findings sind
  **Follow-up `F-DOCS-LINKS-2026-09-27`** (Owner `developer`, Termin **2026-10-11**) und haben
  **keinen** Termin 0 in W0–W8". **V1, V2, V4, V5, V6, V7 und V8 bleiben `0`** wie bisher; **keine**
  andere DoD-Zeile wird angefasst. **Ausgesprochene Folge:** DoD Punkt 12
  (`python3 scripts/sync.py --validate → 0`) ist **dauerhaft unerreichbar**; maßgeblich ist die
  **Deltasperre** (`errors` darf nicht steigen; Owner `validator`, Baseline in **W3-7**). Die
  Severity-Frage ist **OQ10** (Spec §11.1) und wird hier **nicht** entschieden.

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

---

## Korrekturrunde 3 (Rev. 0.6, K46…K50) — W2-0 ist implementiert, der Plan war an fünf Stellen falsch

> **Namensraum-Trennung dieser Runde (Präfix-Schema `R3-B-*`; Präzedenzfall K41).** Die Befunde
> dieser Runde heißen **`R3-B-1`…`R3-B-6`** und sind damit **getrennt** von den **B-1…B-5** des
> Abschnitts **L-2** (V1-Abdeckungslücke = L-2/B-4, `report.py`-Eigentümerlücke = L-2/B-5 u. a.),
> die **wortgleich** stehen bleiben. Das ist **derselbe Defekt, den K41 im K-Namensraum beseitigt
> hat** (`K26` war sechsfach belegt) — hier im **B**-Namensraum. **Warum `R3-B-` und nicht `B-7`ff.:**
> eine Fortzählung bräche die Zählungsaussage dieser Runde („B-6 ist neu") semantisch auf, weil dann
> nicht mehr erkennbar wäre, welche B-Kennung aus L-2 stammt. **Umbenannt: 6 Befunde; alle Verweise
> umgezogen** (diese Runde sowie der von Runde 3 geschaffene Rückverweis in W2-0, Akzeptanz (d)) —
> **L-2 und alle älteren Blöcke sind unangetastet**.

> **Auslöser:** **W2-0 wurde implementiert** (verhaltensneutraler Modul-Split; Modulgrenzen aus
> Spec §4.1 eingehalten; Registrierung byte-identisch). Plan Schritt 2 verlangte, die V1-Tests aus
> `tests/test_doc_facts.py` **nach** `tests/test_doc_freshness.py` zu **verschieben** — damit ist
> eine **plan-eigene Folge** eingetreten, die den Plan falsch machte. Das ist die dokumentierte
> **Fail-closed-Bedingung**: korrigierter Plan, **kein** stilles Nachziehen.
> **Kein** Revisions-Bump: `revision: 0.6` und `status: APPROVED` bleiben **unverändert**; **keine**
> AC-/IC-/R-/OQ-/Task-/V-Check-ID wurde umnummeriert oder gestrichen; **keine** neue Pflicht und
> **kein** neuer Sollwert. **Spec Rev. 0.6 bleibt unverändert** — insbesondere wird die
> **Modulzuordnung nicht verschoben**. Rev. 0.5 und die Korrekturrunden 1+2 (K25…K45) stehen
> **wortgleich**; die Kopf-Änderungsnotiz ist nicht angetastet. **Keine** Checkbox wurde verändert.
> **Alle Zeilenangaben dieser Runde sind selbst gemessen** (`Read`-Zeilenzählung, `grep` im
> Working Tree); **kein** Git-Befehl, kein Zugriff auf den Vor-Split-Stand — Vorher-Werte sind als
> Vorher-Werte des Plans bzw. rekonstruiert gekennzeichnet.

### K46 — Ownership-Konflikt in W2-7 (der eigentliche Anlass)

- **Vorher:** W2-7 `Files:` = `docs.py`, `consistency-check.py`, `report.py`, `tests/test_doc_facts.py`,
  mit dem Zusatz „dieselbe Datei, **kein** neues File-Ownership" für den Nicht-Registrierungs-Pin
  `test_v1_is_not_wired_into_the_runner_yet` (`:2403-2422`).
- **Nachher:** W2-7 `Files:` = dieselben vier **plus** `tests/test_doc_freshness.py`; die
  Ownership-Behauptung ist berichtigt, der Pin-Ort korrigiert; **Negativregel** festgeschrieben.
- **Pin jetzt gemessen** in `tests/test_doc_freshness.py:364-383` (Datei gesamt **384** Zeilen).
  **RVW2-5 bleibt vollständig in Kraft:** W2-7 Schritt 1 ersetzt den Pin dort durch
  `test_v1_is_registered_in_the_runner`; der ausgeliehen Test wird **nicht** parallel weitergeführt.
- **Warum das erlaubt ist:** W2-7 ist **PG-2c** und schreibt **sequenziell als Letzter**
  (`W2-5 → W2-4 → W2-7`); die Regel „mehrere schreibende Tasks derselben Datei sind ausschließlich
  **sequenziell**" ist damit erfüllt. **Ownership-Matrix:** Zeile W2-7 **existierte** und wurde
  korrigiert — `tests/test_doc_freshness.py` trägt jetzt **`owns` (V1-Pin `:364-383`, K46)** statt
  `reads`; `tests/test_doc_facts.py` trägt jetzt `owns (V3-Pin `:2527-2537`, F1-/Exit-Tests)` statt
  `owns (Pin)`. Der Fließtext „W2-7 schreibt vier Dateien, die kein PG-2a-Task schreibt" war nach dem
  Verschieb **falsch** (jetzt fünf; `test_doc_freshness.py` teilt W2-7 mit W2-5) und ist korrigiert.
- **Negativregel (K46, verbindlich, verhindert eine spätere „Vervollständigung"):** W2-3, W2-4,
  W2-5, W2-6, W6-2 und W8-4 nehmen `scripts/lib/consistency/docs.py` **nicht** in ihre `Files:`-Liste
  auf. **Gemessen bestätigt:** nur W2-1, W2-2, W2-0 und W2-7 führen `docs.py`; W6-2 führt
  `docs_wiki.py`, W8-4 führt `docs_index.py`. W2-3/W2-5/W2-6 laufen in **PG-2a** parallel — ein
  `docs.py`-Write-Set dort wäre genau die Ownership-Kollision, die **K20** beseitigt hat.
  **W2-7 ist der alleinige Owner aller `__all__`-Inkremente.**

### K47 — Ankerdrift des Nicht-Registrierungs-Pins

- **Vorher:** `tests/test_doc_facts.py:2403-2422` (fünf Live-Stellen: W2-0 Akzeptanz (c), W2-Wellenblock
  zweimal, W2-7 `Akzeptanz, neu (RVW2-5)`, W2-7 **Schritt 1**) und
  die Aussage „bleibt **grün** in `tests/test_doc_facts.py`".
- **Nachher:** `tests/test_doc_freshness.py:364-383`; die Datei-Aussage ist als gegenstandslos
  markiert. Der Pin ist **inhaltlich unverändert** (`Assertion "check_no_manual_counts" not in runner`)
  und wird **erst in W2-7** ersetzt.
- **Korrigierte Live-Stellen:** W2-0 Akzeptanz (c), W2 Wellenblock (`v1_strict`-Begründung und
  W2-GATE-V1-Zeitbindung), W2-7 `Akzeptanz, neu (RVW2-5)` und W2-7 **Schritt 1**.
- **Bewusst nicht angefasst:** die Fundstellen in den **Rev.-Blöcken** (Kopfnotiz Rev. 0.5, Korrektur-
  runden 1+2) und im **L-3-Errata-Register** bleiben **wortgleich** — sie dokumentieren den
  Rev.-0.5-Stand und dürfen laut Auftrag nicht umgeschrieben werden.

### K48 — Ankerdrift der `docs.py`-Zeilenverweise

| Aussage | vor (veraltet) | nach (gemessen) |
|---|---|---|
| `_v1_finding` (setzt `line`/`branch`) | `docs.py:329-347` | **`docs_freshness.py:255-273`** |
| `check_sync_cli_docs` | `docs.py:9` | **`docs_links.py:30-65`** |
| `check_ui_help_mappings` | `docs.py:47` | **`docs_links.py:68-118`** |
| `check_readme_docs_index` | `docs.py:100` | **`docs_links.py:121-…`** |
| `v1_strict` (W2-Wellenblock) | `docs.py:359`, `:314-326` | **`docs_freshness.py:240-252`** |
| `V1_SCAN_RELPATHS` (W2-GATE-V1) | `docs.py:158` | **`docs_freshness.py:63`** |

- **Korrigierte Live-Stellen:** W2-7 `Interfaces`/`Akzeptanz`/`Akzeptanz neu (K15)`/**Schritt 4**,
  W2 Wellenblock (zwei Stellen), W2-GATE-V1-Tabelle, „File Structure → Geändert (Code) → `report.py`".
- **Korrektur an der obigen Aufzählung (Befund aus der `validator`-Prüfung dieser Runde):** die Liste
  war **unvollständig, nicht falsch** — der W2-Wellenblock trägt jetzt **drei** statt zwei korrigierte
  Stellen, die W2-GATE-V1 zusätzlich **eine**, und **sieben** weitere Stellen mit Vor-Split-Ankern waren
  überhaupt nicht erfasst. **Neu erfasst und einzeln entschieden** (Tabelle unten).
- **Befund R3-B-3 (nicht korrigiert):** der Plan enthielt **zwei Generationen** von Vor-Split-Ankern
  (`_v1_finding` einmal `:350-369` in der W2-0-Baseline, einmal `:329-347` in W2-7) — eine
  Generation-Mischung, die vor dieser Runde schon inkonsistent war. Sie ist jetzt durch **einen**
  gemessenen Anker ersetzt; die historischen Stellen in Rev.-/L-3-Blöcken bleiben bewusst stehen.
- **Eskalationsweg zu R3-B-3 (neu; R3-B-2 war bereits terminiert, R3-B-3 nicht):** **Owner
  `validator`**, **Frist vor W2-7** — sachliche Begründung: die betroffenen Stellen sind **live**
  Anker in Tasks, die W2-7 bzw. W8-4 treffen (W2-7 **Schritt 1** ersetzt den Nicht-Registrierungs-Pin,
  **Schritt 4** nimmt `line`/`branch` in `report.py`; W8-4 **Schritt 1** verortet die V9-Konstante).
  Wird die Frist gerissen, geht R3-B-3 **gemeinsam mit R3-B-4** an `main_chat`. **Eskalationsumfang:**
  (1) die in K48 genannten und korrigierten Live-Stellen — **erledigt**; (2) die **sieben** unten
  einzeln entschiedenen Reststellen — **fünf korrigiert, zwei als Historie klassifiziert**;
  (3) die **drei** weiterhin offenen Anker im selben Live-Block, siehe Absatz danach.

**Reststellen mit Vor-Split-Ankern — einzeln geprüft (Eskalationsumfang von R3-B-3).** Jede Stelle
wurde einzeln gelesen und das Split-Ziel **gemessen** (`Read`-Zeilenzählung im Working Tree, **kein**
Git-Zugriff, **kein** Raten). Die **Modulzuordnung wurde nicht verschoben** — korrigiert wurden
ausschließlich Anker und Statusaussagen.

| Plan-Stelle | zitierter Anker | Symbol (gemessen) | Entscheidung | Messbeleg |
|---|---|---|---|---|
| `:843` Global Constraints (NG-4) | `docs.py:9-44` | `check_sync_cli_docs` | **korrigiert** → `docs_links.py:30-65`, `Severity.ERROR` `:58` | `docs_links.py:30` `def`, `:58` `severity=Severity.ERROR`, `:65` `return findings` |
| `:1715` W2-Wellenblock (RVW2-2) | `docs.py:359` | `v1_strict` / Severity-Wahl | **korrigiert** → `docs_freshness.py:240-252`, Severity-Wahl `:285` | `docs_freshness.py:240` `def v1_strict`, `:252` `return`, `:285` `severity = Severity.ERROR if v1_strict(config) else Severity.WARNING` |
| `:1967` W2-GATE-V1 (Severity-Kippsatz) | `docs.py:359` | dito | **korrigiert** → `docs_freshness.py:240-252`, `:285` | dito |
| `:2097` W2-1 LEDGER-Notiz (Nachtrag Rev. 0.5) | `docs.py:359` | dito | **Historie — wortgleich** | Block ist ein datierter Rev.-0.5-Nachtrag und stuft sich selbst als Historie ein (`:2101` „Der Absatz oben bleibt unverändert Historie"); dieselbe Notiz nennt mit `docs.py` auch den alten Dateinamen |
| `:2555` W3-Wellenblock (W3-GATE-SCOPE) | `docs.py:158` | `V1_SCAN_RELPATHS` | **korrigiert** → `docs_freshness.py:63` | `docs_freshness.py:63` `V1_SCAN_RELPATHS: tuple[str, ...] = ("README.md", "llms.txt", "ARCHITECTURE.md")` |
| `:2909` W3-4 `Vorbedingung` (RVW-4) | `docs.py:359` | `v1_strict` / Severity-Wahl | **korrigiert** → `docs_freshness.py:240-252`, `:285` | dito |
| `:4569` L-2/B-5 (Statuspflege Rev. 0.5, K15) | `docs.py:329-347` | `_v1_finding` | **Historie — wortgleich** (L-2 bleibt unangetastet, siehe Namensraum-Trennung oben) | Belegzeile eines datierten Rev.-0.5-Statuspflege-Eintrags; `report.py:28-41`/`:78-97` darin sind weiterhin gültig (unverändert) |

- **Bleibt im Eskalationsumfang, bewusst nicht korrigiert (gemessen, aber nicht rekonstruierbar):**
  derselbe Live-Block **W2-GATE-V1** trägt in `:1960`/`:1962` noch `docs.py:219-233`, `:256-273` und
  `:383-390` (V1a-/V1b-Trefferbelege für `README.md:122` und `ARCHITECTURE.md:3`). Ihr Split-Ziel ist
  aus dem heutigen Baum **nicht eindeutig** ableitbar (kein Zugriff auf den Vor-Split-Stand, kein
  Git-Zugriff in dieser Runde) — sie werden **nicht geraten**, sondern gehören als Restpunkt in die
  **R3-B-3**-Eskalation an `validator`, Frist **vor W2-7**. **Kein** Modul wird verschoben, **kein**
  Sollwert geändert.

### K49 — Präzisierung „29 Referenzstellen"

- **Klarstellung:** „29" war als **Zeilen**zählung **korrekt**, nicht materiell falsch — zu **HEAD**
  tragen **29 Zeilen** in `tests/test_doc_facts.py` eine Referenz, aber **30 Vorkommen** von
  `docs_lib.`, weil `:2204` **zwei** Referenzen in einer Zeile trägt. **Diese HEAD-Zahl ist
  rekonstruiert**, nicht direkt gemessen (kein Git-Zugriff in dieser Runde): sie folgt aus der
  Ist-Messung 21 + 8 bzw. 22 + 8 (siehe unten) und ist damit **rechnerisch konsistent**.
- **Ist nach W2-0 (gemessen):** **21 Zeilen / 22 Vorkommen** verbleiben in `tests/test_doc_facts.py`
  (`:2204` weiterhin mit zwei). Die **8** mit ihren Tests gewanderten Vorkommen liegen in
  `tests/test_doc_freshness.py` und laufen gegen den Alias `docs_freshness_lib` (Import `:28`):
  `:107` `check_no_manual_counts`, `:142`/`:303`/`:347`/`:350` `Severity`, `:320` `V1_SCAN_RELPATHS`,
  `:326` `v1a_count_spans`, `:327` `v1b_version_spans` — **8** Zeilen, **8** Vorkommen.
  Gegenprobe: 21 + 8 = **29 Zeilen**, 22 + 8 = **30 Vorkommen** ✓.
- **Befund R3-B-1 (neu benannt, keine Pflicht):** die 8 gewanderten V1-Referenzen belegen die
  Fassaden-Erreichbarkeit der V1-Namen **nicht mehr**; Nachweis bleibt das wortgleiche `__all__`
  (W2-0 Schritt 3) zusammen mit Akzeptanz (d). **Keine** neue Abhängigkeit wird eingeführt.

### K50 — Modulbestand und Dateigrößen-Ist

- **Gemessen nach W2-0:** `docs.py` = **80** · `docs_links.py` = **334** · `docs_freshness.py` = **317**
  · `tests/test_doc_freshness.py` = **384** · `tests/test_doc_facts.py` = **2538** (vorher **2867**,
  also **−329** durch den Test-Verschieb). **Alle Module < 600** ✓ — Akzeptanz (f) ist erfüllt.
- **Modulzahl `scripts/lib/consistency/`: 20 → 22** (Ist: 22 Dateien inkl. `__init__.py`).
- **Noch nicht vorhanden:** `docs_wiki.py` und `docs_index.py` (je W2-3 bzw. W2-6) — die Prognosen
  **~200**/**~180** sind unverbraucht. **Luft in `docs_freshness.py`: 317 von 600** Zeilen, also
  Reserve für **V5** (W2-4) und **V6** (W2-5).
- **Verhältnis zur Spec:** die Schätzungen in **Spec §4.1** (~70/~330/~480/~200/~180) waren
  **Prognosen** und stehen dort ausdrücklich **unter** der 600er-Grenze. Die Ist-Zahlen stehen
  **nur hier** im Plan; die **Spec bleibt unverändert** und die **Modulzuordnung wird nicht verschoben**.
- **Klarstellung zu den Ankern in W2-0 Schritt 1** (`:155-412`, `:11-124`, `:416-599`): sie
  bezeichnen die Zeilen der **vor dem Split** existierenden `docs.py` und beschreiben die
  **Extraktion**, nicht den heutigen Baum. Sie bleiben deshalb **unverändert** — ein Umschreiben auf
  die neuen Modulzeilen würde die Extraktionsvorschrift in sich selbst ungültig machen. Die
  Checkboxen von W2-0 sind **nicht** angefasst.

### Geprüft, ohne Abweichung (keine Korrektur nötig)

- **DAG-Kantenliste / Zyklenprüfung:** unverändert gültig. Keine neue Kante nötig — W2-7 kommt als
  **Letzter** (Kanten 9–12) und teilt seine einzige neue Datei `test_doc_freshness.py` mit W2-5
  **sequenziell**, nie parallel. Zyklusprüfung (a)–(d) bleibt gültig; **keine** Rückwärtskante.
- **Wellen-Übersicht PG-2** („max 3 Agents", Phase 0 `W2-1 → W2-2 → W2-0`, **PG-2a = W2-3 ‖ W2-5 ‖ W2-6**,
  Phase B `W2-4 → W2-7`) und der Wellenblock **W2**: **korrekt, unverändert**.
- **File Structure (Tests):** W2-3 → `test_doc_wiki.py`, W2-5/W2-4 → `test_doc_freshness.py`,
  W2-6 → `test_doc_index.py` — **trifft den Ist-Stand**, keine Korrektur.
- **Abschnitt L (L-1, L-3):** **keine** Zählung geändert. W2-0 hat **5** Steps, alle noch `[ ]` —
  W2-0 ist implementiert, aber **noch nicht abgehakt**; das Abhaken (und die Anpassung der
  L-1-Statuszeile „nicht gestartet") macht der **Orchestrator nach dem Commit**. Die maßgeblichen
  Zähler (`^- \[x\]` = 46 / `^- \[ \]` = 153, Summe **199**) bleiben damit **konsistent**; eine
  Zählkorrektur in dieser Runde hätte sie ohne die Orchestrator-Setzung **verfälscht**. Die
  K34-Kopfnotiz (Tabelle ist Stand 2026-09-26) bleibt gültig.
- **Zählung in dieser Runde selbst gemessen (`grep`, Muster `^- \[x\] ` / `^- \[ \] `, Plan
  2026-09-25):** `^- \[x\]` = **46**; `^- \[ \]` = **153** (Partitionsmessung: `1:` = 36,
  `2:` = 37, `3:` = 36, `4:` = 38, `5:`/`6:` = 6); Summe **199** — **identisch** mit der
  Übergabemessung des `validator` (N-2), damit ist diese K34-Zahl jetzt **zweifach belegt**.
  **Keine** Checkbox wurde in dieser Runde gesetzt oder gelöscht; **vorher = nachher**.

### Befunde dieser Runde, die **nicht** eigenmächtig korrigiert wurden

- **R3-B-2 (Anker unbrauchbar):** W2-7 verweist für den `print_report`-Unverändertheitsnachweis auf
  `tests/test_doc_facts.py:2269-2272`. Gemessen zeigen diese Zeilen auf **vier Parametrize-Zeilen** der
  Inert-Prefix-Tabelle (`:2269`–`:2272`), **nicht** auf eine `__str__`-Assertion. Der richtige Zielanker
  ist **ohne Git-Zugriff nicht bestimmbar** (der Vor-Split-Zeilenstand ist nicht rekonstruierbar),
  und Raten wäre ein Befund im Plan. **Eskalation:** Nachmessung durch `validator` mit
  Git-Zugriff (`git show HEAD:tests/test_doc_facts.py`).
- **R3-B-4 (Modulzuordnungs-Konflikt, fail-closed):** **W8-4 Schritt 1** verortet die V9-Altersschwelle N
  als Modulkonstante in `scripts/lib/consistency/docs.py` (Anker `docs.py:158`/`:164`), obwohl W8-4s
  eigenes `Files:` (**Rev. 0.6 / K18**) auf **`docs_index.py`** zeigt und `docs.py` nach W2-0 eine
  **Fassade ohne Logik** ist (Akzeptanz (d)). Das ist ein **Restfehler aus K18**, den W2-0 **materiell**
  verschärft. **Nicht** korrigiert: die Fail-closed-Klausel verbietet die stille Korrektur an der
  Modulzuordnung, und K46-`Negativregel` untersagt W8-4 das `docs.py`-Ownership. **Eskalation an
  `main_chat`** — benötigt eine Entscheidung, ob W8-4 Schritt 1 nach `docs_index.py` wechselt
  (dann **keine** Modulzuordnung in der Spec, sondern nur ein Task-Text-Fix) oder ob die
  Fassaden-Vollständigkeit aufgeweicht wird. **Bis zur Entscheidung bleibt W8-4 unverändert.**
- **R3-B-5 (Anker zum Vor-Split-Stand in W8-4):** dieselben Anker `docs.py:158`/`:164` sind zu
  `docs_freshness.py:63` gewandert (R3-B-4-Folge) — im Rahmen von R3-B-4 mitzukorrigieren, **nicht** separat.
- **R3-B-6 (Hinweis, kein Mangel):** die Rev.-Blöcke Korrekturrunde 1+2 und L-3 enthalten weiterhin
  **historische** Vor-Split-Anker. Das ist **gewollt** (wortgleich, K12-Logik) und **kein** Mangel;
  maßgeblich sind die als Rev. 0.6 / K4x markierten Live-Stellen.

---

## Korrekturrunde 4 (Rev. 0.6, K51…K53 + E-5…E-8) — PG-2a ist zur Hälfte blockiert; drei strukturelle Konflikte liegen beim Auftraggeber

> **Namensraum-Trennung dieser Runde (Präfix-Schema `R4-B-*`; Präzedenzfall K41 und Korrekturrunde 3).**
> Die Befunde dieser Runde heißen **`R4-B-1`…`R4-B-4`** und sind damit **getrennt** von den **B-1…B-5**
> des Abschnitts **L-2** und den **`R3-B-1`…`R3-B-6`** der Korrekturrunde 3, die **wortgleich** stehen
> bleiben. **Warum `R4-B-` und nicht `B-7`ff.:** dieselbe Begründung wie in Runde 3 — eine Fortzählung
> bräche die Zählungsaussage der Runde 3 („`B-6` ist neu") und machte die Herkunft nicht mehr erkennbar.
> **Fortsetzung, keine neue Reihe:** die **Korrektur-Kennungen** laufen mit **K51…K53** hinter dem
> wahren Endstand der Runde 3 (**K50**) weiter; die **Entscheidungsvorlagen** mit **E-5…E-8** hinter
> **E-1…E-4**. **Keine** neue Task-ID, **kein** neues AC/IC/R/OQ/V-Check, **kein** neuer Sollwert.

> **Auslöser:** die Parallelgruppe **PG-2a** (**W2-3 ‖ W2-5 ‖ W2-6**) wurde ausgeführt. **W2-3 ist
> grün und committet**; **W2-5 und W2-6 sind blockiert** und bleiben **uncommittet**. Die Orchestrator-
> Entscheidung lautet: **nur W2-3 committen**, W2-5/W2-6 liegen zurück, und die **strukturellen**
> Konflikte werden hier als **Entscheidungsvorlagen** eingereicht statt eigenmächtig aufgelöst.
> **`code-reviewer` und `tester` haben die Blocker bestätigt**; ihre Messungen wurden in dieser Runde
> **eigenständig nachgemessen** (siehe „Übergabeprämissen, die der Nachmessung nicht standhielten").
>
> **Fail-closed-Bedingung dieser Runde:** korrigierter Plan, **kein** stilles Nachziehen. **Kein**
> Revisions-Bump — `revision: 0.6` (`:6`) und `status: APPROVED` (`:5`) bleiben **unverändert**; **keine**
> AC-/IC-/R-/OQ-/Task-/V-Check-ID wurde umnummeriert oder gestrichen; **kein** Sollwert geändert (die
> einzige Zahlenkorrektur, **11 → 10**, betrifft eine **Bestandsangabe** mit Termin, keinen Sollwert).
> Rev. 0.5 und die Korrekturrunden 1, 2 und 3 (K25…K50) sowie **L-2** und **L-3** bleiben **wortgleich**;
> diese Runde ist **rein additiv** angefügt. **Keine** Checkbox wurde gesetzt, gestrichen oder ergänzt.
> **Alle Zeilenangaben dieser Runde sind selbst gemessen** (`Read`-Zeilenzählung, `grep`/`glob` im
> Working Tree). **Kein** Testlauf, **kein** Git-Befehl, **kein** Zugriff auf einen Vor-Commit-Stand in
> dieser Runde; wo eine Zahl nur aus der Übergabe stammt, ist sie als **Übergabewert** gekennzeichnet und
> **nicht** als Messung ausgegeben.

### K51 — Faktenkorrektur: V7-Baseline 11 → 10 (K24 war eine Fehlmessung)

- **Was widerlegt ist:** die Baseline-Messung 2026-09-27, die **K24** (Plan-Kopfnotiz) und **K36**
  (Rev.-0.6-Katalog) von **10 auf 11** gehoben hat. **Gemessen über das Frontmatter:** in
  `knowledge/wiki` tragen **genau 10** Seiten `type: "Architecture"`, jede auf **Zeile 2**:
  `architecture.md`, `architecture-agent-roles.md`, `architecture-dev-workflow.md`,
  `architecture-external-skills.md`, `architecture-layer-model.md`,
  `architecture-prompt-modernization.md`, `architecture-se-cascade.md`, `architecture-sync-flow.md`,
  `architecture-versioning.md`, `core-principles-overview.md` — **alle** unter
  `knowledge/wiki/concepts/`. **Die elfte Datei ist kein Architecture-Typ:**
  `knowledge/wiki/concepts/core-principle-knowledge-engine.md` trägt in Zeile **2** `type: "Concept"`;
  die als elfte gezählte Stelle ist Zeile **46** — eine `type:`-Zeile **im Body**, innerhalb eines
  ```yaml```-Beispiels, und zwar der **Wertelisten-Kommentar**
  `type: "Concept" # Concept | Architecture | API Reference | Guide | Session Conclusion`.
  K24 war ein **naiver Zeilen-Scan über ganze Dateien**; der maßgebliche Resolver wertet das
  **Frontmatter** aus (`docs_wiki.py:55` importiert `WIKI_ARCHITECTURE_TYPE`).
- **Vorher / nachher an den maßgeblichen Stellen dieses Plans:**

  | Plan-Stelle (Abschnittsanker) | vor | nach |
  |---|---|---|
  | Wellenblock **W2 — Verifikation**, Tabelle `W2-GATE-ERRORS`, Zeile `docs.wiki_staleness` (V7) | **11** | **10** |
  | Wellenblock **W2 — Verifikation**, Tabelle „Warum das Aggregat `docs-findings: 0` dauerhaft unerreichbar war (RVW-1)", Zeile **V7** | **11** | **10** (+ Dateiliste, + Fehlmessungs-Begründung) |
  | Wellenblock **W2 — Verifikation**, Fußnote **³** („Redlichkeit der Erwartungswerte") | **11** | **10** |
  | **Legende** (Kopfnotiz) | `K1…K50` | `K1…K53` (siehe eigener Absatz) |

- **Spec-Änderung, damit auditierbar (K51, einzige Stelle):** die **live** Spec-Stelle
  **§10 `--strict`-Punkt, Unterpunkt 5** (`docs/specs/2026-09-25-repository-documentation-consolidation.md`,
  Abschnitt „Check-spezifische Kriterien mit Termin und Owner", Stand-2026-09-27-Satz) ist von
  **11** auf **10** berichtigt und um die Messmethode (Frontmatter, die 10 Dateien, der
  Body-Kommentar als Fehlzählquelle) ergänzt. **Sonst wurde in der Spec nichts geändert** — insbesondere
  **nicht** der Termin **W5-3**, **nicht** der Owner `tester`, **nicht** die Legende (Spec:70 bleibt
  auf `E-1…E-4` / `K1…K45` eingefroren), **nicht** die Revisionszeile.
- **Bewusst **nicht** angefasst (History, mit Begründung): der **K24**-Bullet der Rev.-0.6-Kopfnotiz
  (Änderungsprotokoll dieser Revision — er dokumentiert, **was** K24 tat; die Berichtigung steht hier),
  die **K36**-Zeile der Runde-1-Tabelle und der **K45**-Absatz der Runde 2 (festgeschriebene
  wortgleiche Blöcke, die ihren damaligen Stand nennen und selbst auf die Plan-Legende verweisen), der
  Rev.-0.5-RVW-1-Absatz „maßgeblich ist der Wert 11" (wortgleich; K45-Logik), die Spec-**§17.9.4**-
  Belegzeile (dort ausdrücklich als Rev.-0.5-Stand **historisierend** markiert) und die Spec-K24-
  Katalogzeile. **Diese Runde hat in keinem wortgleichen Block eine Zahl geändert.**
- **Nebenbefund zur Pfadangabe (gemessen, kein Mangel):** der Planpfad
  `knowledge/wiki/core-principle-knowledge-engine.md` (ohne `concepts/`) kommt in **Plan und Spec
  nicht vor** — 0 Treffer in beiden Dokumenten. Es war deshalb **kein** falscher Pfad zu korrigieren;
  die einzige falsche Angabe war die **Zahl**. Der Plan zitiert `knowledge/wiki/concepts/architecture*.md:2`
  (`W2`-Block, RVW-1-Tabelle) — das ist **korrekt**.
- **Charakter der Korrektur:** **Bestandsangabe**, **kein Sollwert** — Termin **W5-3** und Owner
  `tester` bleiben **unverändert**, die Verschlechterungsregel 3 (`W-VALIDATE-ROT`) ist nicht
  betroffen (10 → 10 ist keine Verschlechterung, sondern die Rückkehr auf den gemessenen Wert).
- **R4-B-1 (Hinweis, kein Mangel):** der maßgebliche Resolver `compute_wiki_staleness` /
  `check_wiki_staleness` (`docs_wiki.py:123-124`, Severity `WARNING`, `check=V7_CHECK_ID`) wurde in
  dieser Runde **nicht ausgeführt** (kein Testlauf). Die Zahl **10** ist über das Frontmatter
  **gemessen**, nicht über den Resolver — sie ist die Eingangsmenge, die er verarbeitet.

### K52 — W2-5-Akzeptanz: die Übergabeprämisse „der Test existiert nicht" hält der Nachmessung nicht stand

- **Befund (R4-B-2, korrigierte Fassung):** der Übergabe-Befund **F55** behauptete, W2-5 habe einen
  **nicht existierenden** Testnamen als grünen AC-36-Nachweis gemeldet (`test_mismatch_is_reported`,
  „0 Treffer in `tests/`"). **Gemessen: `tests/test_doc_facts_expected.py:216` —
  `def test_mismatch_is_reported(computed, expected, monkeypatch)` existiert.** Weitere Belege: die
  Datei referenziert den Namen selbst in ihrem Modul-Docstring (`:46`) und
  `tests/test_doc_freshness.py:398` verweist darauf. Auch das zugeschriebene Zitat „*The rendered
  document is not part of this test, which is the point*" hat in `tests/` **0 Treffer**; der dortige
  Docstring (`:45-49`) sagt etwas anderes: „W2-5 extends this file with the V6 findings; it does not
  change the oracle contract asserted here."
- **Damit ist die Plan-Akzeptanz von W2-5 — anders als die Übergabe annahm — sachlich belegt.** Die
  V6-Hälfte des Tests (`:249-270`) prüft **genau** das, was W2-5s `Akzeptanz` verlangt: genau **ein**
  Finding mit `severity == Severity.ERROR` und `kind == "expected-mismatch"` (`:254-257`),
  `check == "docs.docs_facts_fresh"` (`:259`), `file == EXPECTED_DOC_FACTS_RELPATH` (`:260`), und die
  **Handedit-Achse bleibt stumm** — die WARNING-Menge ist genau `DOCUMENTED_UNPINNED` (`:266-270`).
  Genau das ist der Nachweis, dass der Kreis `doc_facts → Renderer → V6` von außen gebrochen ist, obwohl
  der gerenderte Block `compute_doc_facts()` entspricht. **Kein Nachweis fehlt, es ist keiner zu
  ergänzen.**
- **Ownership passt ebenfalls:** `tests/test_doc_facts_expected.py` steht in **W2-5s** `Files:`
  (dritte Datei neben `docs_freshness.py` und `tests/test_doc_freshness.py`) und in
  `File Structure → Neu anzulegen (Tests)` („AC-36"). **Kein** zusätzlicher Task, **keine** neue Datei.
- **Was tatsächlich offen ist (und dies ist der einzige Punkt mit Owner und Frist):** der Nachweis
  existiert **nur im Working Tree**, W2-5 ist **nicht committet** und seine **4** Steps
  (alle `[ ]`, unberührt) sind nicht abgehakt. Ein Nachweis im Working Tree ist **kein** Commit-Nachweis.
  **Owner: Task W2-5** (unverändert — es wird **kein** Owner erfunden). **Frist: vor dem nächsten
  Commit von W2-5** — der Commit-Titel `feat: add V6 freshness check with expected-value axis` darf
  erst fallen, wenn `python3 -m pytest tests/test_doc_facts_expected.py tests/test_doc_freshness.py -q`
  (W2-5s `Verifikation`) grün ist **und** E-6 entschieden ist, weil die Volltests
  `test_knowledge_roles_pass_schema_validation` und
  `test_generated_docker_agent_has_no_leftover_platform_namespace_placeholder` derzeit rot sind und
  beide auf `sync.py --validate` laufen.
- **Nebenbefund, gemessen:** in `tests/test_doc_facts_expected.py` stehen **leere Zeilenfolgen**
  (`:271-276` und `:284-286`) unmittelbar vor dem Round-Trip-Block (`:277-283`). Das ist **kein**
  Testdefekt, aber ein **Zeichen einer uncommitteten In-place-Bearbeitung** in einer W2-5-eigenen
  Datei — hier nur vermerkt, weil ein gleichzeitiger Writer auf dieser Datei arbeiten könnte.

### K53 — Der maschinelle Ledger-Writer kann diesen Plan nicht adressieren (Feststellung, keine Wahl)

- **Gemessen:** `scripts/lib/plan_ledger.py:64-77` bildet die Task-Blöcke über
  `TASK_HEADER_RE.finditer(text)` (`:71`); `scripts/lib/plan_identity.py:27-30` definiert
  `TASK_HEADER_RE` als **zwei** implizit verkettete Raw-String-Fragmente — `:28`
  `r"(?m)^###[ \t]+Task[ \t]+([A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*)"` und `:29`
  `r"[ \t]*(?::|[—–-])?[ \t]*(.*?)[ \t]*$"`. Der Header verlangt also **`###`**, Whitespace und das
  **literale Schlüsselwort `Task`**; `group(1)` ist die Task-ID, `group(2)` der Rest der Zeile. Dieser
  Plan schreibt `### W2-0:`, `### W2-5:` usw. ⇒ **kein** Treffer ⇒ `_task_blocks()` liefert **leer** ⇒
  `matched_ids` leer ⇒ `unmatched={W2-0}` (alle angeforderten IDs, `plan_ledger.py:172`/`:182`) ⇒
  `sys.exit(1)` (`:272`, `code = 0 if (result.ok and not result.unmatched) else 1`). **Damit ist der
  maschinelle Ledger-Writer für diesen Plan unbrauchbar** — und das ist der Grund, warum diese Runde
  **keine** Checkbox setzt. **Für E-8 wichtig:** das Fragment auf `:29` lässt einen Doppelpunkt, einen
  Gedankenstrich und den Resttitel **zu** — es fehlt **nur** das Schlüsselwort `Task`. Nebenbefund:
  `TASK_ID_RE` (`plan_identity.py:18`) erwartet `task-<ziffern>`; `normalize_task_id` (`:63-73`) liefert
  für `W2-0` unverändert `W2-0` zurück — die ID-Form wäre also **auch nach** einer Regex-Reparatur
  **noch** zu klären, sofern man nicht bei `### W2-0:`-Formaten bleibt (dann greift `group(1)` gar nicht,
  weil `Task` fehlt).
- **Konsequenz für den Fortschrittsausweis:** die Checkboxen dieses Plans werden derzeit **ohne
  Werkzeug** gepflegt. **Beide Auswege sind benannt, keiner ist gewählt** — die Wahl ist **E-8**:
  (a) **Regex um einen alternativen Zweig erweitern** — eine Zeile Produktionscode in
  `plan_identity.py:27-30`, **projektweit** wirksam (auch andere Pläne mit `### W<n>-<n>:`-Überschriften
  gewinnen), aber der geteilte Identitäts-Parser akzeptiert dann **zwei** Überschriftenformen;
  (b) **48 Plan-Überschriften auf `### Task <id>` umstellen** — kein Produktionscode, aber ein großer
  Diff an einem Rev.-0.6-Plan mit festgeschriebenen wortgleichen Blöcken, und die `###`-Form kollidiert
  mit den **Nicht-Task**-`###`-Überschriften desselben Plans (`File Structure`, `L-1`…`L-4`,
  Wellen-Unterabschnitte), d. h. die Umstellung müsste **selektiv** erfolgen, sonst liest der Parser
  Abschnitte als Tasks.
- **Owner: `orchestrator` → `main_chat`** (Eskalation wie R3-B-3/R3-B-4). **Frist: vor dem nächsten
  Wellenabschluss W2-7**, weil W2-7 der Abschluss der Welle ist und dort Registrierung und Common-Gate
  passieren. **Interim-Regel bis zur Entscheidung (ausdrücklich **kein** stummer Ersatz):** bis E-8
  entschieden ist, setzt **der Orchestrator** die Checkboxen **von Hand** und hält jede Änderung mit
  **Datum, Commit-Hash und Task-ID** im Ledger-Abschnitt **L-1** fest; **kein** automatischer Lauf von
  `scripts/lib/plan_ledger.py` gegen diesen Plan. Diese Regel ist **widerruflich** — mit der
  Entscheidung zu E-8 entfällt sie, und die Werkzeugpflege beginnt.

### Geprüft, ohne Abweichung (keine Korrektur nötig)

- **W2-5 und W2-6 werden nirgends als erledigt geführt.** Beide Tasks tragen ihre **4** Steps
  vollständig als `[ ]` (`W2-5`: „Test schreiben (fail)" / „V6 mit beiden Vergleichsachsen
  implementieren" / „Tests grün beobachten" / „commit via `git`-Agent"; `W2-6`: „Tests schreiben (fail)" /
  „V2 implementieren; V4 generalisieren" / „Tests grün beobachten; Szenario-Asserts 50–56 **nicht**
  anfassen (NG-10)" / „commit via `git`-Agent"). **Kein** Wellenblock, **keine** Gate-Tabelle und
  **keine** Ownership-Zeile dieses Plans behauptet einen W2-5-/W2-6-Abschluss. **Diese Runde hat das
  nicht geändert** und behauptet ihn auch nicht.
- **W2-3 ist committet, seine 4 Steps bleiben `[ ]`.** W2-3 trägt **4** Steps (gemessen), nicht fünf;
  alle vier sind `[ ]`. W2-3 ist **sachlich für sich erfüllt** (`docs_wiki.py` + `tests/test_doc_wiki.py`
  existieren, `wc -l` < 600, V7-Tests), und **das Abhaken bleibt beim Orchestrator nach dem Commit**
  — dieselbe Regel, die Runde 3 für W2-0 festgehalten hat, und dieselbe Rechtfertigung: Checkboxen
  werden **nicht** von einer Korrekturrunde gesetzt, sondern vom Orchestrator nach dem Commit.
- **Checkbox-Zählung, in dieser Runde selbst gemessen** (`grep`, Muster `^- \[x\] ` / `^- \[ \] `):
  `^- \[x\]` = **46**; `^- \[ \]` = **153** (Partitionsmessung: `1:` = 36, `2:` = 37, `3:` = 36,
  `4:` = 38, `5:` = 5, `6:` = 1). Summe **199** — **identisch** mit Runde 3 und mit der Übergabemessung
  (`K34`). **Keine** Checkbox wurde gesetzt, gestrichen oder ergänzt: **vorher = nachher = 46 / 153**.
- **DAG / Ownership / PG-2a-Schreibmengen:** unverändert gültig. Runde 4 fügt **keine** Kante und
  **keine** Datei in ein `Files:`-Set ein; die drei Entscheidungsvorlagen betreffen **Zusagen**, keine
  Schreibmengen. Die `Negativregel` aus **K46** gilt unverändert.

### Übergabeprämissen, die der Nachmessung nicht standhielten (R4-B-3)

Damit dieselben Zitate nicht erneut in den Plan wandern, sind die **korrigierten Anker** festgehalten.
Alle vier Abweichungen betreffen **Zeilen- oder Pfadangaben**, **keine** inhaltliche Entscheidung:

| übernommene Angabe | selbst gemessen | Korrektur |
|---|---|---|
| `tests/test_knowledge_engine.py:221` „prüft `assert result.returncode == 0`" | `:221` ist der **Funktionsanfang** `def test_knowledge_roles_pass_schema_validation():`; der Assert steht in **`:228`**, auf `sync.py --dry-run --validate` in `_AGENT_META_ROOT` | Zitat auf **Testname + `:228`** umgestellt (E-6) |
| `tests/test_sharkord_service_name_migration.py:34` | `:34` ist der Funktionsanfang; der `--validate`-Assert steht in **`:48`**. Der Assert in **`:42`** ist ein **einfacher** `sync.py`-Lauf **ohne** `--validate` und von der V4-Generalisierung **nicht** betroffen | Zitat auf **Testname + `:48`** umgestellt; `:42` als **nicht** betroffen ausgewiesen (E-6) |
| W2-3 habe „5 Steps für sich erfüllt" | W2-3 trägt **4** Steps | „4 Steps" — ohne Aussage über Erfüllung |
| die V7-Live-Stelle in der Spec sei „§17.9.1" | §17.9.1 der Spec behandelt die Auftragsprämisse „V1 emittiert ERROR" — **ohne** Bezug zur Wiki-Zahl. Die Live-Stelle ist **§10 `--strict`-Punkt, Unterpunkt 5** | Fundstelle auf **§10 `--strict`-Punkt 5** berichtigt (K51) |
| Planpfad `knowledge/wiki/core-principle-knowledge-engine.md` sei falsch | Pfad kommt in Plan **und** Spec **nicht** vor (0 Treffer) | **kein** Pfad-Fehler; die Fehlmessung lag allein in der **Zahl** (K51) |
| Budget „218 Kommentar-/Docstring-Zeilen" in `docs_freshness.py` | in dieser Runde **nicht** nachgemessen (kein Werkzeug für Zeilenklassifikation) | als **Übergabewert** gekennzeichnet, **nicht** als Messung (E-7) |

### R4-B-4 — Nicht selbst entschieden: die vier strukturellen Konflikte

Die folgenden Punkte sind **echte Strukturkonflikte**. Sie werden hier **nicht** aufgelöst, weil jede
Auflösung einen Sollwert, eine Modulzuordnung, eine Akzeptanz oder den Aufbau des Plan-Ledgers ändert
und damit **nicht** in den Auftrag dieser Korrekturrunde fällt. Sie sind als **Entscheidungsvorlagen
E-5…E-8** eingereicht; alle vier sind **offen und unentschieden** und liegen beim **Auftraggeber**.

**E-5 — V4 wird auf den gesamten `docs/`-Baum generalisiert, aber niemand besitzt die 191 README-Index-Links.**

- **Gemessener Ausgangspunkt:** V4 ist **heute bereits im Runner registriert** —
  `scripts/consistency-check.py:53` importiert `check_readme_docs_index`, `:201` ruft es in
  `run_checks()` (definiert `:140`); die `check`-ID ist `docs.readme_index`. V4 liefert **0**, weil alle
  **sieben** `docs/api/*.md` in `README.md:362-373` verlinkt sind. **W2-6** verallgemeinert den Scope
  von `docs/api/*.md` auf den gesamten `docs/`-Baum — und **W2-6s `Files:` enthält kein `README.md`**
  (nur `docs_index.py` neu, `tests/test_doc_index.py` neu, `docs_links.py` modifiziert), und W2-6s
  `Akzeptanz` nennt **nur** `test_v2_missing_page`.
- **Größenordnung, in dieser Runde gemessen:** `README.md` verlinkt **14** `docs/**/*.md`
  (selbst gemessen, enumerated: die **sieben** `docs/api/*.md` + `guides/setup/instantiate-project.md` +
  `guides/mcp-onboarding-checklist.md` + `architecture/01-layer-model.md` + `howto/admin-ui-remote-access.md` +
  `plans/hacs-platform-preset-audit.md` + `RELEASE_GATES.md` + `se-cascade/se-workflow.md`).
  Der `docs/`-Baum enthält **205** `*.md` **außerhalb** `archive/` (selbst gemessen per Verzeichnis-Inventar:
  Wurzel 8 · `analysis` 4 · `api` 7 · `architecture` 8 · `concepts` 20 · `conclusions` 9 · `guides` 30 ·
  `howto` 1 · `issues` 5 · `plans` 41 · `providers` 6 · `se-cascade` 9 · `specs` 23 · `spikes` 2 ·
  `superpowers` 30 · `testing` 1 · `ui` 1). **205 − 14 = 191** fehlende Verlinkungen, wenn der
  generalisierte V4-Scope genau „getrackte `docs/**/*.md` außerhalb `archive/`" ist — genau dieses Prädikat
  nennt W2-6s `Interfaces`. **Severity von V4 ist `ERROR`** (`W-GATE-TABLE`), die 191 lägen damit als
  **ERROR** im Bestand.
- **Der Widerspruch, der es unentscheidbar macht:** `W-GATE-TABLE` und `W2-GATE-ERRORS` führen für
  `docs.readme_index` den Sollwert **0** mit Owner **`developer` (W2-6)** und **ohne** Termin 0;
  `W-VALIDATE-ROT` listet für **W2-7 … W3-6** planmäßig rot **nur V2, V3, V6** — **V4 fehlt**. Die 191
  lägen damit **außerhalb** des sanktionierten Rot-Satzes, und **keine** Task und **keine** Welle ist für
  ihre Behebung eingetragen. Das ist kein Ankerfehler, sondern eine **Zuständigkeitslücke**.
- **Entscheidungsvorlage (Details und Trade-offs in der E-Tabelle weiter unten).** Owner `main_chat`,
  Frist **vor W2-7**.

**E-6 — Zwei rote Volltests ohne Owner (F53).**

- **Gemessen:** `tests/test_knowledge_engine.py::test_knowledge_roles_pass_schema_validation`
  (`:221`, Assert `:228`) und
  `tests/test_sharkord_service_name_migration.py::test_generated_docker_agent_has_no_leftover_platform_namespace_placeholder`
  (`:34`, `--validate`-Assert `:48`) prüfen beide `assert result.returncode == 0` gegen einen
  `sync.py --validate`-Lauf. **Beide Testnamen kommen in diesem Plan **null Mal** vor** (gemessen,
  Muster `knowledge_engine|sharkord_service_name|test_knowledge_roles_pass|leftover_platform_namespace`
  → 0 Treffer) — **niemand besitzt sie**. Ursache ist laut Übergabe die V4-Generalisierung: 191
  **ERROR**-Findings ⇒ `sys.exit(1)` ⇒ beide Tests rot. **Nicht ausgeführt in dieser Runde** (kein
  Testlauf) — die Teststellen und die Zuordnung sind gemessen, die **Rotursache** ist aus der Übergabe
  übernommen.
- **Warum das unentscheidbar ist:** die Behebung hängt **vollständig** an der Antwort auf **E-5** —
  bleibt V4 bei `docs/api/*.md`, sind die Tests grün; wird generalisiert, braucht es entweder eine
  Terminierung (Muster V3-Follow-up), eine Severity-Änderung oder einen Testeingriff. Owner
  `main_chat`, Frist **vor W2-7** (W2-7 registriert die Checks und zieht das Common-Gate ein).

**E-7 — `docs_freshness.py` überschreitet mit V5 die harte 600er-Grenze (F54).**

- **Gemessen:** `scripts/lib/consistency/docs_freshness.py` = **592** Zeilen. Die Grenze ist **hart**:
  sie ist **W2-4s eigenes Abnahmekriterium** („`wc -l scripts/lib/consistency/docs_freshness.py` → **<
  600**"). V5 (`check_role_generation_parity`) braucht realistisch **55–70** Zeilen ⇒ Endstand
  **647–662** > 600. **Spec §4.1 nennt ~480 als Prognose und sagt ausdrücklich, die Zahl sei **kein**
  Sollwert** — das entschuldigt die Überschreitung **nicht**, weil die **Plan**-Grenze (U-1/K18,
  „jedes < 600 Zeilen") als Abnahmekriterium gesetzt ist. (Budget „218 Kommentar-/Docstring-Zeilen" =
  **Übergabewert**, hier nicht nachgemessen.)
- **Die vorgeschlagenen Wege, mit Bewertung (Übernahme der `code-reviewer`-Bewertung, gegen den Code
  gemessen):** **(a)** W2-4 nutzt `_v6_computed_facts` / `_v6_finding` wieder — das ist **kein** sauberer
  DRY-Move, sondern **versteckte Kopplung**: `_v6_finding` (`:488`) verdrahtet über `V6_CHECK_ID` (`:362`)
  `check="docs.docs_facts_fresh"` und über `V6_SEVERITY_BY_KIND` (`:385`) eine **andere** Severity-Achse;
  V5 braucht `check="docs.role_generation_parity"` und ERROR **iff** `systems-engineering.enabled: true`;
  `_v6_computed_facts` (`:426`) rechnet **Doku-Facts**, während V5 `compute_active_roles()` **vergleicht** —
  **keine** Überlappung. **(b)** W2-4 komprimiert die V1-Prosa — liegt **innerhalb** von W2-4s `Files:`
  (kein `Files:`-Verstoß) und ändert **keinen** Vertrag. **(c)** Prognose/Modulaufteilung neu fassen —
  berührte die Modulzuordnung (U-1, Spec §4.1) und wäre damit **keine** reine Plan-Korrektur.
- **Warum hier keine stille Wahl:** jede der drei Wege berührt entweder einen Abnahme-Sollwert, die
  Modulzuordnung oder die Kopplungsarchitektur. Owner `main_chat`, Frist **vor W2-4**.

**E-8 — Checkbox-Pflege: Workzeug unbrauchbar, Interim-Regel aktiv (Details in K53).** Owner
`orchestrator` → `main_chat`, Frist **vor W2-7**.

### Entscheidungsvorlagen dieser Runde (E-5…E-8) — offen, unentschieden, liegen beim Auftraggeber

> **Format nach dem bestehenden Muster der E-1…E-4** (Spec §17.9.4, Entscheidungsvorlagen-Tabelle):
> Frage · Optionen · Empfehlung · Owner · Frist. **Keine dieser Vorlagen ist entschieden, keine Option
> ist umgesetzt, und es wird keine Entscheidung unterstellt.** Die **E-1…E-4** bleiben **wortgleich**
> und unentschieden.

| **E-5** | Wie wird die **V4-Generalisierung** auf den gesamten `docs/`-Baum behandelt, wenn **191** README-Index-Links und **kein** Owner für ihre Behebung im Plan stehen? | (a) **README-Index als Write-Set einer Task zuweisen** — W2-6s `Files:` wird um `README.md` erweitert und die 191 Links werden dort ergänzt (W2-6 trägt dann Generalisierung **und** Doku-Umbau; Kollision mit W3-7s `README.md`-Markern beachten, PG-2a läuft parallel zu W3); (b) **V4-Generalisierung in eine spätere Welle verschieben**, in der `README.md` ohnehin angefasst wird (Kandidaten: **W3-7** Marker-Regionen, **W8-2** Tote Verweise) — W2-6 bliebe reiner V2-Task, V4 bekäme einen eigenen Termin; (c) **V4-Scope/Severity neu fassen** — Verallgemeinerung zurücknehmen (V4 bleibt `docs/api/*.md`) **oder** Severity auf WARNING herabstufen, sodass die 191 planmäßig rot sind; (d) als **Quer-Variante zu (c)**: die 191 als **rote Vorlaufmenge mit Termin und Owner** führen, exakt nach dem Muster, das der Plan bei **V3** (25 `docs/**`-Links → Follow-up `F-DOCS-LINKS-2026-09-27`) und bei **V9** (geduldet) bereits zweimal angewendet hat | **(d) — Empfehlung, ausdrücklich keine Entscheidung.** Sie ist die einzige Option, die den im Plan **bereits zweimal etablierten** precedent („roter Bestand mit Termin, Owner und Deltasperre") wiederverwendet, **ohne** einen Sollwert zu senken, **ohne** eine Task-Datei-Ownership zu erweitern und **ohne** `README.md` in PG-2a zu ziehen. **Gegenargument, ausdrücklich notiert:** (d) lässt 191 ERROR-Findings dauerhaft im Bestand und verlängert den Doku-ERROR-Altbestand über W2-7 hinaus — wer das nicht will, muss (a) oder (b) wählen. **Die Übergabe hat keine Option benannt; diese Empfehlung ist aus dem Plan-Precedenz abgeleitet und ersetzt keine Entscheidung des Auftraggebers.** | `main_chat` | **vor W2-7** — W2-7 ist der Wellenabschluss; dort werden die Checks registriert und das Common-Gate eingezogen. Danach wäre V4 bereits aktiv und die 191 wären ein unregistrierter Bestand |
| **E-6** | Wer trägt die **zwei roten Volltests** `test_knowledge_roles_pass_schema_validation` (`tests/test_knowledge_engine.py:221`, Assert `:228`) und `test_generated_docker_agent_has_no_leftover_platform_namespace_placeholder` (`tests/test_sharkord_service_name_migration.py:34`, `--validate`-Assert `:48`), die beide `returncode == 0` gegen `sync.py --validate` prüfen und im Plan **null Mal** vorkommen? | (a) als **planmäßig rot** mit Termin und Owner führen (Muster V2/V3, ggf. eigener Follow-up wie `F-DOCS-INDEX-2026-09-27`) — **kein** Eingriff in die Tests; (b) über die **E-5**-Entscheidung miterledigen — bei unverändertem V4-Scope bleiben die Tests grün, bei Generalisierung greift (a); (c) **Testeingriff** — die Volltests isolieren den Doku-Check (Config der Tests auf `enabled: false`), d. h. die Verantwortung wandert in den Test; (d) die Tests als **Bestandsfehler** mit eigener Task behandeln | **(b), hilfsweise (a) — Empfehlung, ausdrücklich keine Entscheidung.** Die beiden Tests sind **Symptom**, nicht Ursache: Ihre Rotheit ist eine **Funktion der E-5-Antwort**. Eine eigenständige Entscheidung über (a)/(c)/(d) würde den Konflikt an der falschen Stelle schließen und E-5 präjudizieren. **Reihenfolgebindung: E-5 vor E-6.** | `main_chat` | **vor W2-7** — dieselbe Registrierungs- und Common-Gate-Stelle wie E-5; danach sind die Tests dauerhaft rot und blockieren jede Wellen-Verifikation, die auf Volltests läuft |
| **E-7** | Wie wird die **harte 600er-Grenze** für `docs_freshness.py` gehalten, wenn V5 den Ist-Stand **592** um realistisch **55–70** Zeilen überschreitet (**647–662**)? | (a) **`_v6_computed_facts` / `_v6_finding` wiederverwenden** — nach `code-reviewer` und gegen den Code gemessen **versteckte Kopplung**, kein DRY-Gewinn: `V6_CHECK_ID` (`:362`), `V6_SEVERITY_BY_KIND` (`:385`) und `_v6_finding` (`:488`) sind auf V6 verdrahtet, V5 braucht `check="docs.role_generation_parity"` und ERROR iff `systems-engineering.enabled: true`; `_v6_computed_facts` (`:426`) rechnet Doku-Facts, V5 vergleicht `compute_active_roles()` — **keine** Überlappung; (b) **V1-Prosa komprimieren** — liegt **innerhalb** von W2-4s `Files:` (kein `Files:`-Verstoß), Budget **Übergabewert** 218 Kommentar-/Docstring-Zeilen, rechnerisch **47–62** ohne Code-Eingriff gewinnbar; (c) **Prognose/Modulaufteilung neu fassen** — Grenze aufweichen **oder** V5 in ein eigenes Modul auslagern; das berührt die Modulzuordnung (U-1, Spec §4.1) und ist damit **keine** reine Plan-Korrektur | **(b) — Empfehlung, ausdrücklich keine Entscheidung.** Es ist die einzige Option, die **weder** einen Sollwert ändert **noch** die Modulzuordnung berührt **noch** eine neue Kopplung in einen geteilten Helfer einzieht. **Gegenargument, ausdrücklich notiert:** (b) komprimiert Prosa und damit **Lesbarkeit** der V1-Dokumentation — ein Qualitätsverlust, der bewusst gegen eine harte Grenne abgewogen werden muss. **Die Übergabe hat keine Option benannt; diese Empfehlung ist aus der `code-reviewer`-Bewertung abgeleitet und ersetzt keine Entscheidung des Auftraggebers.** | `main_chat` | **vor W2-4** — W2-4 ist der Task, dessen Abnahmekriterium (`wc -l` < 600) sonst fehlschlägt |
| **E-8** | Wie werden die **Checkboxen** dieses Plans gepflegt, solange `scripts/lib/plan_ledger.py` ihn nicht adressieren kann (`TASK_HEADER_RE` verlangt `### Task <id>`, der Plan schreibt `### W2-0:`, `_task_blocks()` leer ⇒ `unmatched={W2-0}` ⇒ Exit 1)? | (a) **Regex um einen alternativen Zweig erweitern** — **eine** Zeile Produktionscode in `scripts/lib/plan_identity.py:27-30`, **projektweit** wirksam; Trade-off: der geteilte Identitäts-Parser akzeptiert dann **zwei** Überschriftenformen (dünnerer Format-Contract, mehr Akzeptanzpfade in einer Kern-Identität); (b) **48 Plan-Überschriften auf `### Task <id>` umstellen** — kein Produktionscode; das Fragment `plan_identity.py:29` lässt Doppelpunkt, Gedankenstrich und Resttitel bereits zu, es fehlt **nur** das Schlüsselwort `Task`; Trade-off: großer Diff an einem Rev-0.6-Plan mit festgeschriebenen wortgleichen Blöcken, und die `###`-Form kollidiert mit den Nicht-Task-`###`-Überschriften (`File Structure`, `L-1`…`L-4`, Wellen-Unterabschnitte) — die Umstellung müsste **selektiv** erfolgen, sonst liest der Parser Abschnitte als Tasks; (c) **manuelle Pflege** als dauerhafte Lösung — Checkboxen vom Orchestrator von Hand, Status im Ledger-Abschnitt L-1; Trade-off: kein Werkzeug, Status und Checkboxen können auseinanderlaufen (genau das, was der Ledger verhindern soll) | **(a), hilfsweise (b) — Empfehlung, ausdrücklich keine Entscheidung.** (a) ist projektweit wirksam und betrifft **keine** wortgleichen Blöcke dieses Plans; (b) ist riskanter, weil der Plan viele `###`-Überschriften **ohne** Task-Bezug trägt. **Die Übergabe hat keine Option benannt; diese Empfehlung ist aus der Fehlerursache abgeleitet und ersetzt keine Entscheidung des Auftraggebers.** | `orchestrator` → `main_chat` | **vor W2-7** — bis dahin gilt die in **K53** festgeschriebene **Interim-Regel** (manuelle Pflege mit Datum, Commit-Hash und Task-ID in L-1); **kein** automatischer `plan_ledger.py`-Lauf gegen diesen Plan |

> **Kein** Revisions-Bump, **keine** Sollwert- oder ID-Änderung, **keine** gelöschte Checkbox und
> **kein** Eingriff in Produktionscode oder Tests: Diese Runde hat **ausschließlich** den Plan
> (additiv, plus drei Live-Zahlenkorrekturen und die Legende) und **eine** Stelle der Spec
> (§10 `--strict`-Punkt 5) geändert. W2-5 und W2-6 bleiben **uncommittet** und **nicht** abgehakt.

---

## Korrekturrunde 5 (Rev. 0.7, K59…K70) — Concept-Review über Rev. 0.7: Belege, Zählfehler und drei unerreichbare Mechanismen

> **Auslöser und Ergebnis.** Concept-Review vom **2026-09-27** über Spec + Plan **Rev. 0.7**:
> `VERDICT: CHANGES_REQUESTED` — **0 kritisch, 5 major, 4 minor, 2 info** (11 Findings,
> `RVW-7-01`…`RVW-7-11`). `validator`: **`PASS_WITH_NOTES`, 0 Blocker** (Notizen `n1`…`n5`).
> **Kein Revisions-Bump** — `revision: 0.7` und `status: APPROVED` bleiben unverändert (Muster
> Korrekturrunde Rev. 0.6 Runde 1). **Kein** Produktionscode, **keine** Tests, **keine**
> Runner-Änderung, **keine** Git-Mutation. **Keine** Checkbox gesetzt, gestrichen oder ergänzt.
> **Keine** Task-, AC-, IC-, R-, OQ-, V-Check- oder F-ID umnummeriert oder gestrichen; W2-8 und
> W2-9 behalten ihre IDs (**W2-9 wird angepasst, nicht ersetzt**). **Keine** neue Task-ID, **keine**
> neue offene Frage, **kein** neuer Sollwert, **keine** neue F-ID. Die Rev.-0.5-/Rev.-0.6-Blöcke,
> die Korrekturrunden **1–4** und „Entscheidungs-Abschluss Rev. 0.7" bleiben **wortgleich**;
> dieser Abschnitt ist **rein additiv** und **vorangestellt**.
>
> **Caveat des Reviewers, übernommen und methodisch beachtet.** Die Read-Zeilennummern des
> Reviewers waren unzurelässig; **alle** Belege dieser Runde stammen aus **Grep/Read im Working
> Tree** und sind vor dem Edit **einzeln verifiziert**. Wo dieses Dokument und der Review
> abweichen, gilt **die Messung** — zwei Abweichungen sind ausdrücklich benannt: **(1)** der
> Reviewer nennt „sechs" V4-Tests, zählt in seinen eigenen Listen aber **sieben** (4 rot + 3
> vakuum-grün); **(2)** die Herleitung „`205 − 14 = 191`" ist ein **Einheitenfehler** (K60).
>
> **Kein Finding bleibt unzugewiesen.** Jedes `RVW-7-xx` und jede Validator-Note ist entweder
> **behoben** oder **namentlich als bewusste Nicht-Zuordnung mit Begründung** geführt.

### Korrekturrunde 5 · Finding → Änderung

| Finding | Sev | Behoben wie (Stelle) | Oder: bewusste Nicht-Zuordnung + Begründung |
|---|---|---|---|
| **RVW-7-01** | major | **K59.** IC-05-Pin-Zitat von `(root, config=None) -> list[Finding]` auf die **gemessene einargumentige** Form `(root: Path) -> list[Finding]` korrigiert: Plan-Kopf **K54**, W-GATE-TABLE V4-Zeile, **W2-6 `Interfaces`**, **W2-8 (b)**; Spec-Kopf **E-5** (`:73`), Revisionszeile `0.7` (`:386`), §17.11.1 **K54**. IC-05 selbst (`:944-954`) trägt **kein** Signatur-Literal — dort nur der **gemessene** Beleg `(root)` ergänzt. **Anker-Nachbesserung K72:** die hier genannten Spec-Zeilen sind **nachgemessen** (IC-05 `:944-954`; Revisionszeile 0.7 `:386`; §10-`--validate`-Bullet `:2257-2261`) — die ursprünglichen Angaben `:930-933`/`:367`/`:2235` waren falsch (`:930-933` ist ein Codeblock in **IC-04**, `:367` die **Leerzeile** unter „Verifikations-Legende" — die **VERIFIED**-Zeile ist `:370`, `:2235` steht in §9.2) | — |
| **RVW-7-02** | major | **K60.** **(a)** `191` → **`193`** an allen normativen Stellen; Herleitung als `205 − 12` mit der Einheiten-Auflösung `14 = 12 `.md` + 2 `.html`` (Spec §17.11.3, Plan-Register, Plan-L-Register, L-1 W2-6). **(b)** Der vakuume Nachweis ist ersetzt: **Issue-Liste (namentlich) + once-count außerhalb V4** als reiner Shell-Zählaufruf, Baseline **193** → Ziel **0**; `docs.readme_index` ist als Nachweis **ausdrücklich für unbrauchbar erklärt**. **(c)** Spec §17.11.2 Lesart B rechnete bereits `193` — der innere Widerspruch der Spec ist zugunsten 193 aufgelöst. **K75 (Korrekturrunde 6):** die Baseline **193** ist zusätzlich als `Universe 205 − 12 verlinkt` mit **Bezugszeitpunkt vor W3-6** festgeschrieben, weil der Zählaufruf `INDEX.md` ausschließt und ab W3-6 `192` liefert; der **Sollwert 0** bleibt davon unberührt | Nicht-Rest: die Stellen in **Korrekturrunde 3/4** und im Entscheidungs-Record `E-5` (Plan `:5823`, `:5839`, `:5899`, `:5922`) bleiben **wortgleich** (Muster K36/K42) und werden durch die K60-Lesartregel aufgelöst |
| **RVW-7-03** | major | **K61.** Die **sieben** V4-Tests sind in **W2-6, Akzeptanz V4** als **Ersetzungstabelle R1…R7** namentlich aufgeführt (Alt-Test → Ersatz-Test, Zustand, Begründung); **zwei** Tests bleiben und werden erweitert; **Nicht-Vakuum-Nachweis** (K33) verlangt `tests/test_doc_index.py` in **beide** Erfolgskriterien **und** einen nichtleeren Gegen-Assert im selben Negativtest. Schritt 1 nennt die **sieben**, Schritt 3 den Nicht-Vakuum-Nachweis | **Anzahlabweichung benannt, nicht übernommen:** der Reviewer schreibt „sechs", seine eigenen Listen ergeben **sieben** (4 rot + 3 vakuum-grün). Gemessen und übernommen: **7** |
| **RVW-7-04** | major | **K62.** `scripts/lib/consistency/spec_plan.py` steht in **W2-9s `Files:`**; das Dep-Token-Muster `:570` wird auf `W\d+-\d+` erweitert; **Akzeptanz (e)** pinnt 50 Tasks, keine Phantom-Dep-ID, kein `deadlock:`/`cycle detected`, und pinnt den **erwarteten** `docs.py`-Overlap als erwartet; **Akzeptanz (f)** + `ruff`-Zeile ergänzt; **Schritt 2** nennt die Datei | **Alternative verworfen, begründet** (in W2-9 `Interfaces`): ein erreichbares, aber kaputtes Instrument ist schlechter als ein ungenutztes — `check_spec_plan_workflow` ist für **jeden** Plan aufrufbar, und die Phantom-IDs `task-N` entstünden für **jeden** Plan mit `W<n>-<k>`-Headern. **Overlapping bleibt gewollt** und wird **nicht** wegdefiniert |
| **RVW-7-05** | major | **K63.** In **W2-8 (b)**: (ii) ist an W2-8s Position **unreachable** (Common-Gate entsteht erst in W2-7; V4 nimmt kein `config`; `--root` leitet die Altchecks nicht um; (d) schließt Produktivcode aus) und wird **aus der zulässigen Liste gestrichen** — als **spätere Option erhalten**, mit allen drei Belegen; (i) und (iii) sind als **anwendbar** benannt, (iii) mit **festgeschriebenem Werkzeug** `python3 scripts/consistency-check.py --json --root <eigenes Fixture-Projekt>` und mit der **Grenze**, dass `--root` die Altchecks nicht umleitet (`consistency-check.py:40`/`:199-201`/`:257`) | — |
| **RVW-7-06** | minor | **K64.** Extraktionsregel „**jeder `docs/<kategorie>/`-Pfad, der in der Region genannt wird**" **wortgleich** nach **W2-6 `Interfaces`** übernommen, mit der verbindlichen **7/6-Lesart** und dem Beleg, dass `docs/architecture/` nur im Link `README.md:371` vorkommt; Sollwert-Stabilität **1** ausdrücklich als **kein** Gegenargument vermerkt; Test `test_v4_declares_seven_categories_including_architecture_from_link_only` in W2-6 | — |
| **RVW-7-07** | minor | **K65.** **Vorrangregel** in **W2-6 `Interfaces`**: fail-soft-Guard (`docs/` fehlt ⇒ `[]`) wird **zuerst** geprüft und ist die **einzige** Ausnahme; bei vorhandenem `docs/` gilt fail-closed (fehlende `README.md` **oder** fehlende Überschrift ⇒ **1** Finding), was die gemeinsame Bedingung `docs_links.py:183` ersetzt. Zwei **neue** Tests in W2-6 | — |
| **RVW-7-08** | minor | **K66.** Plan-Kopf **K57** und **W2-9 `Interfaces`** sagen jetzt das **gemessene** Verhalten: `normalize_task_id("W2-0") == "W2-0"` **heute schon** (Durchreich-Zweig, **verhaltensgleich abgedeckt** durch `normalize_task_id("custom") == "custom"`, `tests/test_plan_identity.py:100` — der Anker `:96-101` war falsch, **K71**; der `W2-0`-Pin wird in Akzeptanz (f) neu angelegt); W2-9 ändert **ausschließlich** (a); eine „Reparatur" von (b) ist **verboten**, weil sie den Round-Trip bricht. (b) wird als **No-op-Pin** fortgeführt — **Akzeptanz (f)**, **Schritt 1** | — |
| **RVW-7-09** | minor | **K67.** V4 in den **beiden** späteren `W-VALIDATE-ROT`-Zeilen („W3-7 … W8-1", „W8-2 … W8-4") ergänzt — inkl. Owner-Spalte — und in **Spec §10, Aufzählungspunkt `--validate`** (`:2257-2261` — **nachgemessen**, **K72**; die Angabe `:2235` aus Korrekturrunde 5 war falsch und steht in §9.2) sowie im Spec-Kopf (`:89`); der **heutige Arbeitsbaum-Zustand** des V4-Teils von W2-6 (**193** ERROR) als Ursache der zwei roten Volltests in **L-1 W2-6** benannt | — |
| **RVW-7-10** | info | **K68.** Als **Plan-Pflicht für W2-6** festgeschrieben: Docstrings `docs_links.py:8-10` und `:168-177` auf den **E-5**-Scope umzuschreiben (was V4 prüft / nicht mehr prüft / Signatur bleibt `(root)`). **Kein Code-Edit durch diese Runde** — W2-6 ist der einzige Task, der `docs_links.py` schreibt | **Bewusste Nicht-Zuordnung als Code-Änderung:** Auftrag dieser Runde ist Plan + Spec; die 3 uncommitteten W2-6-Dateien (`docs_index.py`, `tests/test_doc_index.py`, `docs_links.py`) bleiben **unberührt** |
| **RVW-7-11** | info | **K69.** **Entscheidung: keine Änderung an Korrekturrunde 4.** Begründung: Runde 4 ist **wortgleich festgeschrieben**; ein eingefügter Verweis würde genau die Wortgleichheit brechen, die diese Runde schützt. Der Vorrang ist **global** regelkonform hergestellt (Plan-Legende, Rev.-0.7-Block, „Entscheidungs-Abschluss Rev. 0.7" — Muster K36/K42). Der Verweis wird **hier** geführt | **Bewusste Nicht-Zuordnung:** Ergänzung einer Verweiszeile in Korrekturrunde 4 (Plan `:5626`) unterbleibt — Begründung oben |

### Korrekturrunde 5 · Validator-Notizen n1…n5

| Note | Befund | Zuordnung |
|---|---|---|
| **n1** | **K6** im K-Namensraum **undefiniert** — nur Bereichsangabe „Ausführungskorrekturen K1–K6" (Plan `:852`, Rev.-0.2-Block) | **Bewusste Nicht-Zuordnung, begründet.** Der Rev.-0.2-Block ist **wortgleich festgeschrieben** und der Befund ist **vorbestehend** (Rev. 0.2, nicht Rev. 0.7). Eine K-Nummer für **K6** zu vergeben hieße, einen Block umzuschreiben, der seinen damaligen Stand dokumentiert — genau das, was K36/K42 als Fehler behandeln. **Maßgeblich** ist die Plan-Legende (`K1…K70`) |
| **n2** | **W0-5 fehlt** (W0 = 1,2,3,4,6,7); Spec §16 behauptet „W0…W8 lückenlos" (Spec `:2674`) | **Behoben (Präzisierung, kein ID-Change).** Spec §16: „W0…W8 lückenlos" wird als **Wellen**-Lückenlosheit präzisiert (W0…W8 = **9** Wellen, alle vorhanden); **Task-ID**-Lückenlosheit gilt für AC/IC/NFA/R/F/V, **nicht** für W-Tasks. Der gemessene W0-Stand (**6** Tasks: W0-1, W0-2, W0-3, W0-4, W0-6, W0-7) und das **Fehlen von W0-5** werden **namentlich** festgehalten. **Kein** W0-5 wird erfunden, **keine** W-ID geändert |
| **n3** | bewusste Spiegelung | **Bestätigter Bewusstant, keine Änderung.** Die Spiegelung zweier Stellen ist gewollt (Spec + Plan) und wird nicht entspiegelt |
| **n4** | hypothetischer F-ID-Name | **Bestätigter Bewusstant, keine Änderung.** Der Name ist als **hypothetisch** gekennzeichnet; eine Existenzbehauptung wäre eine Falschangabe |
| **n5** | zwei unterschiedlich komprimierte OQ-Open-Listen (Plan `:168` vs. `:280`) | **Bewusste Nicht-Zuordnung, begründet — kosmetisch.** Die **Plan-Legende** (`:280`) ist maßgeblich und nennt alle **5** offenen OQs (OQ1, OQ3, OQ4, OQ9, OQ10); die Rev.-0.6-Liste (`:168`) ist ein **datierter** Stand. Beide sind inhaltlich **konsistent** mit ihrem jeweiligen Stand; ein Angleichen hieße einen wortgleich festgeschriebenen Block umschreiben |

### Korrekturrunde 5 · Neu gemessene Zählungen

**Methode und Ehrlichkeit der Messung.** In dieser Runde **neu gemessen** per Grep/Read im
Working Tree: Tasks, W2-Tasks, Checkboxen, K-Katalog-Obergrenze, die `docs/`-Linkziele in
`README.md`. **Nicht** neu gemessen und deshalb als **übernommene Baseline-Messung 2026-09-27**
gekennzeichnet: der `docs/`-`.md`-Bestand **205** (in dieser Runde stand **kein** Shell-Werkzeug
zur Verfügung; die Zahl ist im Plan/Spec durchgehend als Baseline markiert). **Die Herleitung ist
dadurch trotzdem prüfbar:** der Register-Nachweis ist ein **konkreter Shell-Zählaufruf** (K60), mit
dem jede:r den Bestand in einer Zeile neu zählen kann — der Zählwert hängt damit **nicht** an
einer unüberprüfbaren Behauptung.

| Größe | Wert | Herleitung / Messmethode |
|---|---|---|
| Tasks | **50** | `^### W[0-9]-[0-9]+:` ⇒ 50 Treffer |
| davon W2 | **10** | W2-0, W2-1, W2-2, W2-3, W2-4, W2-5, W2-6, W2-7, W2-8, W2-9 |
| davon W0 | **6** | W0-1, W0-2, W0-3, W0-4, W0-6, W0-7 — **W0-5 existiert nicht** (`n2`) |
| Checkboxen `[x]` | **59** | `^\s*- \[x\]` ⇒ 59 Treffer — **unverändert** |
| Checkboxen `[ ]` | **148** | Gesamt 207 − 59; Gesamt aus `44 × 4 + 5 × 5 + 1 × 6 = 207` — **unverändert** |
| Checkboxen gesamt | **207** | **unverändert**; in dieser Runde **keine** Checkbox gesetzt, gestrichen oder ergänzt |
| K-Katalog-Obergrenze | **K70** | Rev. 0.7 = K54…K58, Korrekturrunde 5 = K59…K70; Plan-Legende `K1…K70`. Spec-Legende bleibt **eingefroren** auf `K1…K45` (K42) |
| `docs/`-Linkziele im **gesamten** `README.md` | **14** (12 `.md` + 2 `.html`) | `grep '\]\(docs/' README.md` — eindeutige Ziele: `guides/setup/instantiate-project.md` (`:309`/`:354`), `architecture/01-layer-model.md` (`:309`/`:371`), `guides/mcp-onboarding-checklist.md` (`:355`), `howto/admin-ui-remote-access.md` (`:358`), `api/{cli-reference,slash-commands,composition-system,pal-variables,admin-ui-reference,viz-api,viz-event-schema}.md` (`:362-366`/`:372`/`:373`), `ui/agent-graph.html` (`:369`), `ui/admin-ui.html` (`:370`), `plans/hacs-platform-preset-audit.md` (`:376`) |
| davon `.md` | **12** | die beiden `.html` (`docs/ui/agent-graph.html`, `docs/ui/admin-ui.html`) sind **keine** `.md`-Seiten ⇒ gehören **nicht** in den 205er-`.md`-Bestand |
| nicht im README verlinkte `.md`-Seiten | **193** | `205 − 12` (Baseline-205, übernommen; 12 in dieser Runde gemessen) |
| deklarierte `docs/`-Kategorien in der Index-Region | **7** (überschriften-only: **6**) | `README.md:347-381`; `docs/architecture/` nur im Link `:371` (**K64**) |
| V4-Sollwert am echten Baum | **1** | Kategorie `docs/se-cascade/` (deklariert `:378`, ohne Link in der Region) |
| Tests, die die entfernte Per-Seiten-Semantik pinnen | **7** | `tests/test_doc_index.py` (4 rot, 3 vakuum-grün) — **K61** |

### Korrekturrunde 5 · Betroffene Abschnitte (Edit-Protokoll)

**Plan** (`docs/plans/2026-09-25-repository-documentation-consolidation.md`): Frontmatter
**unverändert** (`revision: 0.7`) · Kopf-Block K54 · Kopf-Block K57 · **neue** Korrekturrunde-5-Liste
K59…K70 · Plan-Legende (`K1…K58` → `K1…K70`) · W-GATE-TABLE V4-Zeile ·
**W-VALIDATE-ROT** (alle vier Zeitraumzeilen) · Task **W2-6** (`Interfaces`, Akzeptanz V4 mit
Ersetzungstabelle, Erwartungswert/Spec-Treue, Docstring-Pflicht, `Verifikation`, Schritte 1–3) ·
Task **W2-8** (Akzeptanz (b), `Consumes`) · Task **W2-9** (`Files`, `Interfaces`, Akzeptanz (e)+(f),
`Verifikation`, Schritte 1–3) · Coverage-Matrix AC-12 · DoD Punkt 2 · L-1 (W2-6-Zeile) ·
Follow-up-Register + Zuordnungsnachweis · **neuer** Abschnitt „Korrekturrunde 5".
**Spec** (`docs/specs/2026-09-25-repository-documentation-consolidation.md`): Kopf **E-5** ·
Revisionszeile `0.7` · IC-05 (Belege) · §10 `--validate` · §16 (Präzisierung `n2`) ·
§17.11.1 K54 + K57 · §17.11.2 (Vorrangregel, 7/6-Lesart, 193) · §17.11.3 (Register 193 +
Nachweis) · **neue** §17.11.5.
**Nicht angefasst (bewusst):** alle Code-Dateien, alle Tests, `scripts/consistency-check.py`,
`sync.py`, die 3 uncommitteten W2-6-Dateien, die Korrekturrunden 1–4, die Rev.-0.5-/Rev.-0.6-Blöcke,
„Entscheidungs-Abschluss Rev. 0.7", alle Checkboxen, alle IDs außer dem K-Bereich.

## Korrekturrunde 6 (Rev. 0.7, K71…K75) — zweites Concept-Review über Rev. 0.7: Write-Set-Inventare, Anker, Fixture-Begründung und Baseline-Bezugszeitpunkt

> **Auslöser und Ergebnis.** Concept-Review vom **2026-09-27** (zweite Runde über denselben
> Revisionsstand) über Spec + Plan **Rev. 0.7**: `VERDICT: CHANGES_REQUESTED` — **0 kritisch,
> 1 major, 3 minor, 1 info** (5 Findings: `NEU-1`…`NEU-4`, `INFO-1`).
> **Rein mechanisch, kein erneuter Sachentscheid:** alle 11 Findings der Runde 1 waren am Code
> verifiziert erledigt, beide Autor-Korrekturen (7 V4-Tests, **193** statt 191) waren unabhängig
> bestätigt; die verbleibenden Punkte betrafen ausschließlich **Vollständigkeit abgeleiteter
> Inventare**, **Beleg-Qualität** und **Bezugszeitpunkte**. **Kein Revisions-Bump** — `revision: 0.7`
> und `status: APPROVED` bleiben unverändert. **Kein** Produktionscode, **keine** Tests, **keine**
> Runner-Änderung, **keine** Git-Mutation, **keine** Löschung oder Änderung der **3 uncommitteten
> W2-6-Dateien** (`scripts/lib/consistency/docs_index.py`, `tests/test_doc_index.py`,
> `scripts/lib/consistency/docs_links.py`). **Keine** Checkbox gesetzt, gestrichen oder ergänzt.
> **Keine** Task-, AC-, IC-, R-, OQ-, V-Check- oder F-ID umnummeriert oder gestrichen; W2-8 und
> W2-9 behalten ihre IDs (**W2-9 wird ergänzt, nicht ersetzt**). **Keine** neue Task-ID, **keine**
> neue offene Frage, **kein** neuer Sollwert, **keine** neue F-ID. Die Korrekturrunden **1–5**,
> die Rev.-0.5-/Rev.-0.6-Blöcke, der Abschnitt „Korrekturrunde 5" und „Entscheidungs-Abschluss
> Rev. 0.7" bleiben **wortgleich**; dieser Abschnitt ist **rein additiv** und **vorangestellt**.
>
> **Methodischer Vorbehalt, ausdrücklich und in beide Richtungen.** Die `grep`-/`read`-Zeilennummern
> beider Reviews sind in diesem Projekt **nachweislich unzuverlässig**; deshalb wurde **jeder** Anker
> **vor** dem Edit per Grep am Working Tree verifiziert. **Zwei Anker-Korrekturen der Runde 1 waren
> selbst falsch** (`:930-933`, `:367`, `:2235` — **K72**), und die vom Reviewer genannten
> Zeilennummern der Fundstellen wichen von den gemessenen ab (Beispiele: `tests/test_plan_index.py`
> → real `tests/test_plan_identity.py`; Plan-Fundstelle `W2-9 Interfaces` → real **W2-6 Akzeptanz
> V4**). **Maßgeblich ist die Messung, nicht die Fundstellenzahl des Reviews.**

### Korrekturrunde 6 · Finding → Änderung

| Finding | Sev | Behoben wie (Stelle, **gemessener** Anker) | Oder: bewusste Nicht-Zuordnung + Begründung |
|---|---|---|---|
| **NEU-1** | major | **K71.** `scripts/lib/consistency/spec_plan.py` steht jetzt in **allen** abgeleiteten Write-Set-Inventaren: **Ownership-Matrix** (neue Zeile, W2-9-Spalte **owns (Modify, Dep-Token-Muster `:570`)**, Kopfvermerk „die neunte Dateizeile ist `spec_plan.py`"), Matrix-Narrativ **1** („die **fünf** Werkzeug-/Testdateien"), Matrix-Narrativ **2** („die **sieben** neuen Dateien von W2-8/W2-9"), **Step-Agent-Map** (W2-9-Spalte, jetzt 5 Dateien), **`File Structure`** (**neuer** Eintrag `scripts/lib/consistency/spec_plan.py`), **Rollback W2** (**neue** Zeile `git checkout scripts/lib/consistency/spec_plan.py`; Textzählung **vier → fünf**), „Warum W2 ‖ W3 parallel" (W2-9-Dateiliste + „sechs → **sieben** Dateien") und die **vier** Self-Review-Summenlisten. „Betroffene Stellen" um genau diese Stellen **erweitert** (neue Liste im Kopf-Block, additiv neben der Runde-5-Liste) | **Historische Stelle, bewusst nicht angefasst:** die Spalte „Folge im Plan" des Entscheidungs-Records `E-8` nennt „Ownership-Matrix (4 Zeilen + 2 Spalten)" und die `Files:`-Liste des Records nennt vier Dateien. **Begründung:** der Abschnitt ist **wortgleich festgeschrieben** und dokumentiert den **datierten** Stand vom 2026-09-27; ein Edit würde genau die Wortgleichheit brechen, die K36/K42 als Fehler behandelt. **Aufgelöst über die K71-Lesart-Regel:** jede Stelle, die W2-9s Write-Set **ohne** `spec_plan.py` nennt, meint den Stand **vor** K62. **Keine Kollision:** `spec_plan.py` wird von **keiner** anderen Task in ihre `Files:`-Liste aufgenommen — der Mangel war reine Deckungslücke, nicht ein Fehlurteil der Ownership-Entscheidung |
| **NEU-2** | minor | **K74.** Der falsche Beleg `tests/test_plan_identity.py:96-101` ist an **allen Fundstellen** durch den **realen** Anker ersetzt: „verhaltensgleich abgedeckt durch `normalize_task_id("custom") == "custom"` (`tests/test_plan_identity.py:100`, **derselbe** Durchreich-Zweig); der `W2-0`-Pin wird in W2-9 **Akzeptanz (f) neu angelegt**". **Gemessen:** `:96` = `def test_normalize_task_id():`, `:100` = `assert normalize_task_id("custom") == "custom"`, `:101` = `assert normalize_task_id("task-") == "task-"` — **kein** `"W2-0"` im ganzen File. Fundstellen: Plan-Kopf **K57**, Kopf-Liste **K66**, **W2-9 `Interfaces`**, Zuordnungsregister **RVW-7-08**; Spec §17.11.1 **K57** und §17.11.5 **K66** | **Sachstand unverändert, ausdrücklich bestätigt:** `normalize_task_id` lässt `W2-0` heute unverändert (Durchreich-Zweig `return raw`, `plan_identity.py:73`; `TASK_ID_RE = ^task-[0-9]+$` (`:18`) passt nicht) — per Code gelesen, nicht behauptet. **Kein Schutz geht verloren:** der `W2-0`-Pin entsteht in Akzeptanz (f) **neu**; der alte Anker war nie einer |
| **NEU-3** | minor | **K72.** Die drei falschen Anker sind auf die **nachgemessenen** Werte umgestellt — **alle Fundstellen**: Plan-Kopf **K59** (IC-05 `:930-933` → **`:944-954`**), Plan-Register **RVW-7-01** (IC-05 → **`:944-954`**, Revisionszeile `0.7` `:367` → **`:386`**), Plan-Register **RVW-7-09** (§10 `--validate` `:2235` → **`:2257-2261`**), Spec §17.11.5 **K59** (IC-05 → **`:944-954`**). **Gemessen:** `:930-933` ist der Docstring-**Codeblock von IC-04** (`compute_active_roles`); `:367` ist die **Leerzeile** unter „Verifikations-Legende" (die **VERIFIED**-Zeile liegt bei `:370`); `:2235` steht in §9.2 (Merge-Regel). **Re-Review 3 (R3-1):** der Revisionszeilen-Anker **einmal nachgemessen** = **`:386`** (`:383` ist die `0.5`-Zeile) — K72 bleibt derselbe Eintrag, **keine** neue K-ID | **Keine inhaltliche Änderung:** die drei **Aussagen** waren je richtig (IC-05 trägt kein Signatur-Literal, die Revisionszeile 0.7 nennt K59, §10 trägt den V4-Zusatz). Falsch waren ausschließlich die Anker — genau das war der Befund |
| **NEU-4** | minor | **K73.** „**alle** sieben Fixtures" ist an **beiden** Fundstellen auf „**6 der 7** Fixtures" präzisiert (Plan-Kopf **K61**, Plan **W2-6 Akzeptanz V4**; Spec §17.11.5 **K61**), **R7 gesondert** begründet: `test_real_repo_pages_are_reported_only_by_v2_until_w3_6` (`tests/test_doc_index.py:394`) hat **kein** Fixture, sondern liest den **echten** Baum (`REPO_ROOT`, `:404-408`) und ist rot wegen `finding.message.split("'")[1]` auf einer Message, die nach E-5 die **Kategorie** nennt | **Die Klassifikation bleibt unverändert:** „alle sieben heute rot bzw. vakuum" ist **korrekt** (R1–R3 vakuum-grün mit falscher Semantik, R4–R6 rot, R7 rot) — die **Begründungsmenge** war falsch, nicht das Urteil. **Ergänzt** sind die gemessenen Fixture-Zeilen `:280`/`:294`/`:309`/`:320`/`:336`/`:350` |
| **INFO-1** | info | **K75.** Die Messgröße ist **zukunftssicher** gefasst: statt „Baseline 193" nun „**`Universe 205 − 12 verlinkt = 193`** (Bezugszeitpunkt **vor W3-6**)", mit der ausdrücklichen Begründung der Exclusion (`-not -name 'INDEX.md'`, V2-Konvention gemäß IC-05 V2-Zeile „ohne `docs/INDEX.md` selbst") und dem Vermerk, dass **ab W3-6** derselbe Aufruf **192** liefert (Universe **204**, davon **12** verlinkt), der **Sollwert 0** aber **zeitpunktunabhängig** bleibt. Fundstellen: Plan-Kopf **K60**, Plan Follow-up-Register, Plan-Register **RVW-7-02**, Spec §17.11.3 **Register**, Spec §17.11.5 **K60** | **Kein Baseline-Wert wird geändert** — `193` bleibt `193`; nur der **Bezugszeitpunkt** und die **Herleitungsform** werden ausdrücklich gemacht. **Kein neuer Sollwert**, keine neue F-ID |

### Korrekturrunde 6 · Neu gemessene Zählungen

**Methode.** In dieser Runde **neu gemessen** per Grep am Working Tree: Task-Header,
Checkboxen, K-Katalog-Obergrenze, die `owns`-Zeilen der Ownership-Matrix, die W2-9-Dateiliste in
`File Structure`/Rollback/Step-Agent-Map und die Fixture-Zeilen in `tests/test_doc_index.py`.
**Nicht** neu gemessen und deshalb als **übernommene Baseline-Messung 2026-09-27** gekennzeichnet:
der `docs/`-`.md`-Bestand **205** und die **14** `docs/`-Linkziele in `README.md` — beide Zahlen
stehen im Plan/Spec durchgehend als Baseline; die Herleitung `205 − 12 = 193` ist über den
konkreten Shell-Zählaufruf (K60) in **einer** Zeile nachprüfbar.

| Größe | Wert | Herleitung / Messmethode |
|---|---|---|
| Tasks | **50** | `^### W[0-9]-[0-9]+:` ⇒ **50** Treffer |
| davon W2 | **10** | W2-0, W2-1, W2-2, W2-3, W2-4, W2-5, W2-6, W2-7, W2-8, W2-9 |
| davon W0 | **6** | W0-1, W0-2, W0-3, W0-4, W0-6, W0-7 — **W0-5 existiert nicht** (`n2`) |
| Checkboxen `[x]` | **59** | `^- \[x\]` ⇒ **59** Treffer — **unverändert** |
| Checkboxen `[ ]` | **148** | Gesamt **207** − 59; Gesamt aus `44 × 4 + 5 × 5 + 1 × 6 = 207` — **unverändert**. Die Fünfer- und Sechser-Tasks wurden **verifiziert**: 5er-Schritte in W2-1, W2-0, W2-7, W4-3, W5-2; 6er-Schritte in **W8-4** (einziger `- [ ] 6:`-Treffer) |
| Checkboxen gesamt | **207** | **unverändert**; in dieser Runde **keine** Checkbox gesetzt, gestrichen oder ergänzt |
| K-Katalog-Obergrenze | **K75** | Rev. 0.7 = K54…K58, Runde 5 = K59…K70, **Runde 6 = K71…K75**; Plan-Legende `K1…K75`. **Spec-Legende bleibt eingefroren** auf `K1…K45` (K42) — **maßgeblich** ist die Plan-Legende |
| K-Einträge dieser Runde | **5** | K71, K72, K73, K74, K75 — **lückenlos, ohne Doppelung** (Muster K41) |
| `owns`-Zeilen der Ownership-Matrix, Spalte **W2-9** | **5** (vorher 4) | `plan_identity.py`, `plan_ledger.py`, **`spec_plan.py` (K71)**, `test_plan_identity.py`, `test_plan_ledger_writer.py` |
| Rev.-0.7-Dateizeilen der Matrix | **9** (vorher 8) | 8 aus Rev. 0.7 + **`spec_plan.py`** = **9** ⇒ der Matrix-Kopf „**9 Dateizeilen**" ist damit **stimig** |
| Werkzeug-/Testdateien von W2-9 | **5** (vorher 4) | Matrix, Step-Agent-Map, `File Structure`, Rollback, **3** Summenlisten — **alle** auf denselben Stand gezogen |
| Dateizeilen von W2-8 + W2-9 | **7** (vorher 6) | 5 + 2 |
| Fixtures der 7 V4-Tests, die `README_RELPATH, "# readme\n"` schreiben | **6** (R1–R6) | `tests/test_doc_index.py:280`, `:294`, `:309`, `:320`, `:336`, `:350` — **gemessen** |
| V4-Tests **ohne** Fixture | **1** (R7) | `:394` — liest `REPO_ROOT` (`:404-408`) |
| F-IDs | **keine neue** in Runde 6 | Bestand unverändert: `F-DOCS-README-INDEX-2026-09-27`, `F-DOCS-README-INDEX-SE-2026-09-27` (Rev. 0.7 / K55) |
| Task-/W-/AC-/IC-/R-/OQ-/V-IDs | unverändert | 50 Task-IDs unverändert, keine Umnummerierung; `revision: 0.7`, `status: APPROVED` unverändert |

### Korrekturrunde 6 · Betroffene Abschnitte (Edit-Protokoll)

**Plan** (`docs/plans/2026-09-25-repository-documentation-consolidation.md`): Frontmatter
**unverändert** (`revision: 0.7`) · Kopf-Block **K57** (Anker) · Kopf-Liste **K60** (Baseline),
**K61** (Fixtures), **K66** (Anker) · **neue** Korrekturrunde-6-Liste **K71…K75** ·
Plan-Legende (`K1…K70` → `K1…K75`) · „Warum W2 ‖ W3 parallel" (W2-9-Dateiliste + Summenangabe) ·
**`File Structure`** (neuer Eintrag `spec_plan.py`) · **Rollback W2** (neue `git checkout`-Zeile +
Mengenangabe) · Task **W2-6** (Akzeptanz V4, Begründungsabsatz) · Task **W2-9** (`Interfaces`:
gemessener Anker) · **Step-Agent-Map** (W2-9-Spalte) · **Ownership-Matrix** (Kopfvermerk, neue Zeile,
Narrativ ×2) · **Self-Review** (Rev.-0.7-Dateiliste, Einfachschreiber-Liste, „Neu sind außerdem"-
Zählung, Abweichung 8) · Zuordnungsregister Runde 5 (RVW-7-01, -02, -08, -09 als **Nachbesserung**
zu den dort genannten K-Einträgen, jeweils mit K-Nachweis im selben Satz) · Follow-up-Register ·
**neuer** Abschnitt „Korrekturrunde 6".
**Spec** (`docs/specs/2026-09-25-repository-documentation-consolidation.md`): §17.11.1 **K57**
(Anker) · §17.11.3 (Register-Baseline, K75) · §17.11.5 **K59** (IC-05-Anker), **K60** (Baseline),
**K61** (Fixture-Satz), **K66** (Anker-Wortlaut) · **neue** §17.11.6.
**Nicht angefasst (bewusst):** alle Code-Dateien, alle Tests, `scripts/consistency-check.py`,
`sync.py`, die **3 uncommitteten W2-6-Dateien**, die Korrekturrunden **1–5**, die Rev.-0.5-/
Rev.-0.6-Blöcke, „Entscheidungs-Abschluss Rev. 0.7" (stattdessen K71-Lesart-Regel), der Spec-Statuskopf
und die **eingefrorene** Spec-Legende `K1…K45`, alle Checkboxen, alle IDs außer dem K-Bereich.

## Entscheidungs-Abschluss Rev. 0.7 (2026-09-27) — E-5, E-6, E-7 und E-8 sind entschieden

> **Was dieser Abschnitt ist und was nicht.** Er ist die **entscheidende** Fassung zu `E-5`…`E-8` und
> **gleichrangig** mit der **Plan-Legende** und dem Rev.-0.7-Block im Kopf. **Wortgleich und
> unangetastet** bleiben die Abschnitte „Korrekturrunde 4 (Rev. 0.6, K51…K53 + E-5…E-8)" und
> „Entscheidungsvorlagen dieser Runde (E-5…E-8) — offen, unentschieden": sie dokumentieren den Stand
> **vor** der Entscheidung. **Ebenso unberührt:** `E-1`…`E-4` (bleiben **offen, unentschieden**),
> `K1`…`K53` und alle Rev.-0.5-/Rev.-0.6-Blöcke. `status: APPROVED` bleibt **unverändert**.

| E | **Gewählt** (verbindlich, 2026-09-27) | **Verworfen** (begründet) | Owner | Folge im Plan |
|---|---|---|---|---|
| **E-5** | V4 (`check_readme_docs_index`, Check-ID `docs.readme_index`) wird auf den **README-Index-Scope** begrenzt: die `##`-Region `Documentation Index` in `README.md` (heute `:347`…`:381`); je dort **deklarierter** `docs/`-Kategorie (gemessen **7**) muss (a) das Verzeichnis existieren und (b) **mindestens ein** `docs/<kategorie>/…`-Link in der Region liegen; fehlt die Überschrift, **1** Finding (fail-closed). **IC-05-Pin unverändert** (Check-ID, Signatur, Severity ERROR, `file` = `README.md`). **191** → Follow-up `F-DOCS-README-INDEX-2026-09-27`; verbleibender Ist-Befund **1** → Follow-up `F-DOCS-README-INDEX-SE-2026-09-27`. Beide Owner `developer`, Termin **2026-10-11**, Nachweis = **Zählwert** über `--json` | **(i)** Rücknahme auf den Alt-Scope `docs/api/*.md` (Lesart C) — **vakuum-trivial** (0 Findings ⇒ Schärfe nicht belegbar; `docs/api/` wächst über W2–W8 nicht), **IC-05-Spalte „erweitert" wird zum leeren Satz**, und **sechs** deklarierte Kategorien blieben ungeprüft — die Blindstelle, unter der sich die 191 angesammelt haben. **(ii)** Seitengenau innerhalb der Region (Lesart B) — liefert **193** statt 191 und löst den Blocker **nicht**. Volltext Spec §17.11.2 | `main_chat` (Nutzer), umgesetzt `developer` (W2-6) | W2-6, `W2-GATE-ERRORS` (V4), `W-VALIDATE-ROT` (neue Zeile W2-6…W2-7), `W-GATE-TABLE` V4 + Fußnote **⁶**, Verschlechterungsregel 1, Coverage-Matrix AC-12, DoD 2, Self-Review Abweichungen 10 |
| **E-6** | **Eigener Task W2-8** („Volltests entkoppeln"), `Files:` `tests/test_knowledge_engine.py` + `tests/test_sharkord_service_name_migration.py`, Agent `senior-developer`, **AK AC-11 + AC-13** (kein neuer AC), **kein** V-Check, `Depends on: W2-4`, **sequenziell**, **DAG unmittelbar vor W2-7**; **drei** zulässige Mechanismen, `xfail`/`-k`/`|| true`/Sollwert-Absenkung/`sync.py`-Eingriff **unzulässig**; Nachweis = Volltest-Lauf mit **0** roten Tests | **(a)** Volltests als „planmäßig rot" führen (Muster V2/V3) — **verworfen**, weil die Entkopplung machbar ist und die Rotheit **nicht** dem Test gehört, sondern der Fremdgröße `--validate`. **(b)** über E-5 miterledigen — **verworfen**, weil das eine **falsche Prämisse** ist: auch bei unverändertem V4-Scope bleiben die Tests ab **W2-7** rot, weil dann V2/V3/V6 registriert sind (`W-VALIDATE-ROT`, Spec §10). **(c)** Testeingriff **ohne** Aufgabenzuordnung — **verworfen**, weil eine Maßnahme ohne `Files:`, Agent und AK die Ownership-Lücke nur verlagert | `main_chat` (Nutzer), umgesetzt `senior-developer` (W2-8) | Neuer Task W2-8, W2-Wellenblock Verifikation (neue Volltest-Zeile), `W2-7` `Depends on`, Coverage-Matrix AC-11/AC-13, DoD 12, Ownership-Matrix (2 Zeilen), Self-Review Abweichungen 12 |
| **E-7** | **V5** wandert in das neue Modul **`scripts/lib/consistency/docs_freshness_v5.py`**; W2-4s `Files:` = Create `docs_freshness_v5.py` + Create `tests/test_doc_freshness_v5.py`; **Größenfolge:** `docs_freshness.py` **592** (Reserve **8**, kein weiterer V-Check) · `docs_freshness_v5.py` **≈ 55–70** — **beide < 600** ✓; Modulmenge **4 → 5**, Zuordnung **12/12 disjunkt** | **(a)** Wiederverwendung von `_v6_computed_facts`/`_v6_finding` — **versteckte Kopplung**: `V6_CHECK_ID`/`V6_SEVERITY_BY_KIND` sind auf V6 verdrahtet, V5 braucht eigene Check-ID und eigene Severity-Achse; `_v6_computed_facts` rechnet Doku-Facts, V5 **vergleicht Rollen** — keine Überlappung. **(b)** V1-Prosa komprimieren — rechnerisch wirksam, aber **Lesbarkeitsverlust** der V1-Dokumentation gegen eine **harte** Grenze; die Grenze wird nicht aufgeweicht, indem die Nachbarschaft aufgeweicht wird | `main_chat` (Nutzer), umgesetzt `developer` (W2-4) | Neues Modul + neue Testdatei in `File Structure`, W2-4 vollständig, W2-7 `Verifikation`, Ownership-Matrix (2 Zeilen + 2 Aufhebungen), Kantenliste Kante 8 als **gegenstandslos** markiert, `W-GATE-TABLE` V5, Self-Review Abweichungen 11, Spec §4.1 |
| **E-8** | `TASK_HEADER_RE` (`scripts/lib/plan_identity.py:27-30`) wird um einen alternativen Zweig für die **Wellen-/Task-Header**-Form erweitert; `TASK_ID_RE`/`normalize_task_id` lernen `W<n>-<k>`; **neuer Task W2-9**, `Files:` `plan_identity.py` + `plan_ledger.py` (bedingt) + `tests/test_plan_identity.py` + `tests/test_plan_ledger_writer.py`; **Position: Phase 0, nach W2-0, vor PG-2a** ⇒ **„Ledger-Writer einsetzbar ab Task W2-9"**; **jetzt noch nicht.** K53-Interim-Regel **endet mit W2-9** | **(a)** Alle **50** Überschriften auf `### Task <id>` umstellen — **verworfen**: großer Diff an **wortgleich festgeschriebenen** Blöcken, und die `###`-Form kollidiert mit den Nicht-Task-`###`-Überschriften (`File Structure`, `L-1`…`L-4`, Wellen-Unterabschnitte) — die Umstellung müsste **selektiv** erfolgen, sonst liest der Parser Abschnitte als Tasks. **(b)** Nur den Regex ändern, die ID-Form später klären — **verworfen**: `TASK_ID_RE` erwartet `task-<ziffern>`, `normalize_task_id` liefert `W2-0` unverändert; **beide** Teilfehler gehören in **eine** Task, sonst bliebe das Werkzeug unbenutzbar | `main_chat` (Nutzer), umgesetzt `senior-developer` (W2-9) | Neuer Task W2-9, PG-2-Diagramm, Kanten **16**, Ownership-Matrix (4 Zeilen + 2 Spalten), DoD 14, Global Constraints (2 Bullets), L-1 Rev.-0.7-Anhang, W2-Rollback Stufe 3, Self-Review Abweichungen 13 |

### Der neue W2-DAG als vollständige Kantenliste (Rev. 0.7)

**Kanten (18, davon 3 neu):**

| # | Kante | Art |
|---|---|---|
| 1 | `W1-6 → W2-1` | Querwelle |
| 2 | `W0-4 → W2-1` | Querwelle |
| 3 | `W1-5 → W2-5` | Querwelle |
| 4 | `W2-2 → W2-0` | W2, seriell |
| 5 | `W2-0 → W2-3` | W2 → PG-2a |
| 6 | `W2-0 → W2-5` | W2 → PG-2a |
| 7 | `W2-0 → W2-6` | W2 → PG-2a |
| 8 | `W2-5 → W2-4` | W2, seriell — **historisch, nach E-7 gegenstandslos, bleibt im Bild** |
| 9 | `W2-3 → W2-7` | W2, seriell |
| 10 | `W2-4 → W2-7` | W2, seriell |
| 11 | `W2-5 → W2-7` | W2, seriell |
| 12 | `W2-6 → W2-7` | W2, seriell |
| **16** | **`W2-0 → W2-9`** | **W2, seriell (Phase 0) — NEU, E-8** |
| **17** | **`W2-4 → W2-8`** | **W2, seriell (Phase B) — NEU, E-6** |
| **18** | **`W2-8 → W2-7`** | **W2, seriell — NEU, E-6** |
| 13 | `W2-1 → W3-4` | Querwelle, **Vorwärts** |
| 14 | `W1-10 → W3-1` | Querwelle |
| 15 | `W3-6 → W4-1`, `W4-3 → W5-1`, `W6-2 → W7-1`, `W7-5 → W8-1` | Wellenfolgen |

**Topologische Ordnung:**
`W2-1 → W2-2 → W2-0 → W2-9 → {W2-3 ‖ W2-5 ‖ W2-6} → W2-4 → W2-8 → W2-7`.

**Zyklenprüfung: keine Zyklen — der Graph ist ein DAG.** Vollständiger Nachweis (a)–(e) im Abschnitt
„Ownership-Matrix, DAG-Kantenliste und Zyklenprüfung, Zyklenprüfung" sowie in Spec §17.11.4.

### Follow-up-Register — Stand nach Rev. 0.7

**Maßgeblich ist das Register der Spec: §17.10.3 (Rev. 0.6) + §17.11.3 (Rev. 0.7).** Hier die
Plan-Sicht, ohne die Liste zu duplizieren:

| ID | Gegenstand | Owner | Termin | Nachweis |
|---|---|---|---|---|
| `F-DOCS-LINKS-2026-09-27` | **25** tote relative interne Links unter `docs/**` (V3) | `developer` | 2026-10-11 | Zählwert `docs.internal_links` unter `docs/**` = **0** |
| `F-REQUIREMENTS-LINKS-2026-09-27` | `docs/REQUIREMENTS.md:21` (kein V3-Finding, F15-N) | `developer` | 2026-10-11 | gemeinsam mit dem vorigen |
| `F-LAYOUT-README-2026-09-27` | `README.md:722`/`:723` | `developer` (W8-2) | **W8-2** | **kein** Follow-up — AC-30 / Task W8-2 |
| **`F-DOCS-README-INDEX-2026-09-27`** (Rev. 0.7) | **193** nicht-Archiv-`docs/**.md` **nicht** in `README.md` verlinkt (**K60** — Herleitung `205 − 12`, weil die **14** in `README.md` genannten `docs/`-Pfade **12** `.md` + **2** `.html` sind; **K75:** die Baseline ist als **`Universe 205 − 12 verlinkt = 193` (Stand vor W3-6)** gefasst, weil der Zählaufruf `-not -name 'INDEX.md'` enthält und **ab W3-6** `192` liefert) | `developer` | **2026-10-11** | **Issue-Liste (namentlich) + once-count außerhalb V4** (Shell-Zählaufruf, Spec §17.11.3): Baseline **193** (Bezugszeitpunkt **vor W3-6**) → Ziel **0** (zeitpunktunabhängig). **Ausdrücklich kein `docs.readme_index`-Zählwert** — V4 zählt Kategorien und beobachtet diese Menge nicht |
| **`F-DOCS-README-INDEX-SE-2026-09-27`** (Rev. 0.7) | Kategorie `docs/se-cascade/` im README-Index deklariert, **ohne** Link | `developer` | **2026-10-11** | Zählwert `docs.readme_index` = **0** |

**Keine unzugewiesene Folge jeder Entscheidung — Zuordnungsnachweis:**

| Folge | Zuordnung |
|---|---|
| 193 nicht im README verlinkte `docs/`-Seiten | **Follow-up `F-DOCS-README-INDEX-2026-09-27`** (Owner, Termin, Nachweis = Issue-Liste + once-count **außerhalb** V4, **K60**) |
| 1 verbleibender V4-Befund (Kategorie `docs/se-cascade/`) | **Follow-up `F-DOCS-README-INDEX-SE-2026-09-27`** (Owner, Termin, Nachweis) |
| 2 rote Volltests | **Task W2-8** (eigenes `Files:`, Agent, AK, Tests, Position vor W2-7) |
| 600er-Grenze für `docs_freshness.py` | **Task W2-4** (neues Modul `docs_freshness_v5.py`, Größenfolge im Task) |
| `docs_freshness.py`-Vorschau in `File Structure` und Modulzahl | **K56** im Rev.-0.7-Block (additive Berichtigung der Rev.-0.6-Angaben) |
| Kante `W2-5 → W2-4` ohne Begründung mehr | **als historische, gegenstandslose Kante im Bild behalten** (Zyklenprüfung (e), Spec §17.11.4) — Entfernen wäre eine stille Änderung an einer abgenommenen Planungsentscheidung |
| Folgen der Kante `W2-4 → W2-7` usw. | **unverändert** — W2-7 hängt nach Rev. 0.7 zusätzlich an **W2-8** |
| Prüfungs-Ort von `TASK_HEADER_RE` (`plan_ledger.py` vs. `plan_identity.py`) | **K58** (Faktenkorrektur; beide Dateien in W2-9s `Files:`) |
| Ledger-Pflege bis W2-9 | **K53-Interim-Regel**, Termin **W2-9**, DoD 14, L-1 Rev.-0.7-Anhang, Global Constraints |
| V4-Erwartungswert in `W-GATE-TABLE`/`DoD` | **= 1** mit Follow-up-Termin (K54) — **kein** Sollwert 0 mehr |
| Verschlechterungsregel „V1–V7 ab W2-7" | **V4-Ausnahme ab W2-6** ausdrücklich benannt (V4 ist **kein** neuer Check) |
| Spec-Zielrevision laut Auftrag (`0.5`) | **abweichend auf `0.7` gesetzt**, weil die Datei `revision: 0.6` mit vollständigem §17.10 trug; im Spec-`approved-scope` **ausdrücklich** vermerkt |
| **Nicht** zugeordnet | **keine**. Jede Folge ist Task, Registereintrag oder ausdrücklich begründete Nicht-Zuordnung (historische Kante). **Korrekturrunde 5:** zusätzlich ist **jedes** RVW-7-Finding und **jede** Validator-Note entweder behoben oder **namentlich** als bewusste Nicht-Zuordnung mit Begründung geführt — Tabelle im Abschnitt „Korrekturrunde 5" |

### Offen nach Rev. 0.7 — unverändert, nicht verdeckt

- **E-1, E-2, E-3, E-4** — Entscheidungsvorlagen aus Rev. 0.5, **offen**, beim Auftraggeber
  (Spec §17.9.4). **Von Rev. 0.7 nicht berührt.**
- **OQ1** (W0-7, vor Abschluss W5), **OQ9** (W5-1), **OQ4** (W8-1), **OQ10** (vor W8-4) — **offen**.
- **OP-1** — formaler Abschluss der Spec-Korrektur, Owner `orchestrator`.
- **R3-B-2, R3-B-3, R3-B-4, R3-B-5** — Befunde der Korrekturrunde 3, **unverändert offen**.
- **R4-B-1…R4-B-3** — Befunde der Korrekturrunde 4; **R4-B-4 („nicht selbst entschieden: die vier
  strukturellen Konflikte") ist durch dieses Rev.-0.7-Bild geschlossen** — alle vier Konflikte sind
  entschieden und einem Task bzw. Registereintrag zugeordnet. **Die übrigen R4-B-Befunde bleiben
  unverändert dokumentiert.**




