---
plan-id: PLAN-DOCS-CONSOLIDATION-2026-09-25
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
title: W0-2 — Design-Freeze, Contract-Liste, Commit-/Reihenfolge-Konvention
status: done
revision: 0.3
related:
  - docs/plans/2026-09-25-repository-documentation-consolidation.md
  - docs/specs/2026-09-25-repository-documentation-consolidation.md
  - docs/specs/2026-09-25-repository-documentation-consolidation-design.md
---

# W0-2 — Design-Freeze, Contract-Liste, Commit-/Reihenfolge-Konvention

> Ergebnis-Record der Plan-Task **W0-2** („Design-Freeze, Contract-Liste, Branch-Scaffold"),
> Plan `PLAN-DOCS-CONSOLIDATION-2026-09-25`, Spec `SPEC-DOCS-CONSOLIDATION-2026-09-25`
> (Rev. 0.3, `status: APPROVED` vom 2026-09-26). **Agent:** `documenter` (Rollen-Ownership
> dieses Records; der Plan sieht für W0-2 den `git`-Agenten vor, die Commit-Leistung für
> W0-2 verbleibt beim `git`-Agenten).
>
> **Nachführung 2026-09-26 (Rev. 0.2 → 0.3, Plan Rev. 0.3):** Vier Korrekturen aus dem
> Code-Review dieses Records, **keine** Änderung einer eingefrorenen Größe und **keine** Änderung
> der Entscheidungen: (a) Kapitel 6 lockert die Commit-Titel-Konvention, weil `0 von 47`
> Step-4-Commit-Messages den `W<N>`-Präfix tragen; (b) Kapitel 7 führt die **Spec-Abweichung
> „ein Branch pro Welle"** als **offenen Punkt OP-1** und den **Branch-Bestand von 2 Branches**
> (gemessen); (c) Kapitel 8 führt die **Evidenzklasse** je Zeile (Enum siehe „Konvention:
> Evidenzklassen" am Record-Anfang) und
> korrigiert das `scripts/lib/`-Gate auf `origin/main..HEAD` → **0** (gemessen 0);
> (d) die Verifikationszeile zu `NFA-` escapet ihr Pipe. Eingefrorene Listen (Kapitel 1–6) und
> IC-/NFA-Zahlen bleiben **unverändert**.
>
> **Nachführung 2026-09-26 (Rev. 0.1 → 0.2):** Die Verweise auf den Plan-Stand wurden auf
> **Plan Rev. 0.2** nachgeführt — der Plan hat die Vorgabe „Ein Branch pro Welle" selbst als
> überholt markiert und prüft seither **Stand-Synchronität + genau einen Wellen-Branch** statt
> `chore/docs-consolidation-w*` → 0. *(Formulierung in Rev. 0.3 präzisiert: die Prüfung adressiert
> den Wellen-Branch unter **exaktem Namen**; der Präfix-Match liefert gemessen 2 Zeilen — siehe
> Kapitel 7.2.)* Eingefrorene Listen (Kapitel 1–6), Branch-Entscheidung und
> die Abweichungsbegründung (Kapitel 7) bleiben inhaltlich **unverändert**.
>
> **Charakter:** Dieser Record ist **keine** neue Spezifikation und **keine** Kopie der Spec.
> Er friert **Verweise und Kurzbezeichnungen** ein. Die **normative Quelle bleibt die Spec**;
> bei Widerspruch zwischen diesem Record und der Spec gilt die **Spec**.

## Zweck und Geltungsbereich

W0-2 friert die **Design-Basis** ein, die von allen Folgewellen **W0–W8** unverändert
übernommen wird:

1. die **24 Interface Contracts** IC-01…IC-24 (Spec §5),
2. die **11 nicht-funktionalen Anforderungen** NFA-01…NFA-11 (Spec §8),
3. die **Zielstruktur / SSoT-Matrix** (Spec §3.1–§3.3),
4. die **Migrationsreihenfolge W0–W8** (Spec §9.2, Plan „Wellen-Übersicht"),
5. die **Commit- und Reihenfolge-Konvention** je Welle (dieser Record, Kapitel 6).

**Änderungsregel für W1–W8:** Wer eine hier eingefrorene Größe ändern will, ändert **nicht**
diesen Record, sondern erzeugt zuerst eine **Spec-Revision** (Rev. 0.4) mit Concept-Review und
Nutzer-Freigabe. Ein Wellen-Task, der gegen diesen Record verstößt, ist **blockiert**, nicht
„im Plan geregelt".

**Ausdrücklich nicht Gegenstand dieses Records:** Implementierung, Code, Config-Änderungen,
Änderungen an Spec, Plan oder Design sowie das Anlegen von Branches (siehe Kapitel 7).

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
Folgewellen: ein `✅` **ohne** Evidenzklasse ist unvollständig.

---

## 1. Eingefrorene IC-Liste (IC-01…IC-24)

Verweis: **Spec §5 „Interface Contracts"**; Abschnittsgrenzen zum Freeze-Zeitpunkt verifiziert:
§5.1 (M1) = IC-01…IC-06, §5.2 (M2) = IC-07…IC-16, §5.3 (M3) = IC-17…IC-18,
§5.4 (M4) = IC-19…IC-22, §5.5 (Querschnitt) = IC-23…IC-24. Spalte „Welle" ist die
Umsetzungszuordnung aus **Spec §9.1 / §9.2** und dem Plan-Kapitel „File Structure".

| IC | Kurzbezeichnung (eingefroren) | Zielmodul / Artefakt | Welle | Spec-Abschnitt |
|---|---|---|---|---|
| IC-01 | `doc_facts.py` (neu): Faktum-API `compute_doc_facts()` | M1 | W1 | §5.1 |
| IC-02 | Faktum-Vertrag Platzhalter → Quelle → Formel (inkl. `DOCS_*`-Namespace, volatile Markierung) | M1 | W1 | §5.1 |
| IC-03 | `doc_facts.py` Staleness-Resolver (gate-bewusst) | M1 | W1 | §5.1 |
| IC-04 | `doc_facts.py` aktive-Rollen-Menge (F13/F21-Korrektur) | M1 | W1 | §5.1 |
| IC-05 | `consistency/docs.py` (erweitert): Checks **V1–V9** (bestehende 3 unverändert) | M1 | W2 (+ Stufen W3, W6, W8) | §5.1, §5.1.1 |
| IC-06 | `consistency/placeholders.py`: `^DOCS_`-Namespace-Registrierung | M1 | W1 | §5.1 |
| IC-07 | `doc_renderer.py` (neu): Rendering-/Marker-API | M2 | W1 | §5.2 |
| IC-08 | Marker-Syntax in `README.md` (Hybrid-Modus, `agent-meta:docs-*`) | M2 | W3 | §5.2 |
| IC-09 | `doc_index.py` (neu): Doku-Baum-Modell `build_index_model()` | M2 | W1 | §5.2 |
| IC-10 | `docs/INDEX.md`-Format (kanonisch, 100 % generiert) | M2 | W3 | §5.2 |
| IC-11 | Snippet-Bridge in `config.py` (Erweiterung der Block-Snippet-Logik) | M2 | W1 | §5.2 |
| IC-12 | `sync_pipeline.py`: Doku-Stage und **Reihenfolge-Pflicht** | M2 | W3 | §5.2 |
| IC-13 | Schreib-, Idempotenz- und `dry_run`-Vertrag + Besitzregel | M2 | W3 | §5.2 |
| IC-14 | Fact-Hash-Footer (Diff-Stabilität) | M2 | W3 | §5.2 |
| IC-15 | C8 Scaffold-Guard in `spec_plan_scaffold.py` | M2 | W3 | §5.2 |
| IC-16 | `generated_file_drift.py`: Doku-Dateien in die Hash-Baseline | M2 | W3 | §5.2 |
| IC-17 | Migrationsoperationen (alle `git mv`, **kein** Inhalts-Rewrite) | M3 | W4, W5, W6 | §5.3 |
| IC-18 | `ARCHITECTURE.md` als generierter Stub (T-4) | M3 | W4 | §5.3 |
| IC-19 | `knowledge.py`: `index.md`-Generator | M4 | W7 | §5.4 |
| IC-20 | `knowledge/wiki/log.md`-Append (Bedingung (c)) | M4 | W7 | §5.4 |
| IC-21 | `agents/1-generic/knowledge-indexer.md` (Bedingung (b), **einzige** `agents/`-Berührung) | M4 | W7 | §5.4 |
| IC-22 | Rollback-/Gate-Config (`docs-consolidation`, sechs Properties, fail-off) | Querschnitt | W1 | §5.4 |
| IC-23 | `config/doc-facts-expected.yaml` + `load_expected_doc_facts()` (R14) | Querschnitt | W1 (Anlage), W2 (Vergleich) | §5.5 |
| IC-24 | `knowledge.py::restore_wiki_index()` (M6, Restore-Pfad W7) | Querschnitt | W7 | §5.5 |

**Eingefrorene IC-Zahlen:** 24 Contracts, IDs lückenlos IC-01…IC-24, keine Wiederverwendung
einer gestrichenen ID. Verifiziert per `grep -c '^#### IC-'` gegen die Spec (Ergebnis
**24**, Kapitel 8).

## 2. Eingefrorene NFA-Liste (NFA-01…NFA-11)

Verweis: **Spec §8 „Nicht-funktionale Anforderungen"** (NFA-Tabelle). Kurzform der
Anforderungsaussage; die Nachweis-Spalte der Spec bleibt maßgeblich.

| NFA | Eingefrorene Kurzform | Nachweis (Spec §8) |
|---|---|---|
| NFA-01 | Idempotenz: zwei Läufe ⇒ null Schreibvorgänge, identischer Output | AC-17, AC-20, AC-33 |
| NFA-02 | Diff-Minimalität: kein Zeitstempel, keine absoluten Pfade, keine Host-/User-Daten; nur `facts-hash` variiert | AC-18, AC-03, AC-27, AC-34 |
| NFA-03 | Provider-Parität: kein `if provider == …` in M1–M4, provider-neutrale Ausgabe | AC-01, IC-22 |
| NFA-04 | Downstream-Kompatibilität: Writer **und** Checks V1–V9 per Default aus (fail-off) | AC-24, AC-26, AC-33 |
| NFA-05 | Handedit-Schutz: handeditierte generierte Region wird gemeldet, **nicht** überschrieben | AC-19 |
| NFA-06 | Rollback je Welle: benannter Rückrollpunkt pro W1–W8, der keine andere Welle invalidiert; W7 zusätzlich Restore-Pfad | AC-20, AC-21, AC-32, AC-35, AC-41 |
| NFA-07 | Stdlib-only für M1, M2, M4; Dependency-Invariante ohne Zyklen | AC-01 |
| NFA-08 | Begrenzter Blast Radius; Ausnahme nur IC-21 in W7 | AC-28, AC-31, AC-32, AC-39 |
| NFA-09 | Beobachtbare Drift über die Hash-Baseline, inkl. Handprosa-Schutz | AC-19, AC-37 |
| NFA-10 | Keine Secrets, keine Env-Werte in generierten Dateien | AC-18, IC-02 |
| NFA-11 | Unabhängige Verifikation der Zahlen gegen eine zweite, handgepflegte Quelle (**elf** Sollwerte) | AC-36 |

**Eingefrorene NFA-Zahlen:** 11 Anforderungen, IDs lückenlos NFA-01…NFA-11. Verifiziert per
`grep -c '^| NFA-'` gegen die Spec (Ergebnis **11**, Kapitel 8).

## 3. Eingefrorene Zielstruktur (SSoT-Matrix, Kurzform)

Verweis: **Spec §3.1 (Generationsmodi), §3.2 (SSoT-Matrix je Faktumklasse), §3.3 (SSoT je
Bereich)**. Eingefroren sind die fünf Generationsmodi und die Bereichsentscheidungen:

| Modus | Kurzform (eingefroren) | Drift-Folge |
|---|---|---|
| generiert | 100 % Generator-Output; Handedit ist ein Fehler | V6 ERROR |
| hybrid | Handprosa + generierte `agent-meta:docs-*`-Regionen | V1 (ERROR ab W3-Ende), V6 |
| handgepflegt | rein manuell, optionaler Fakten-Footer | keiner (bewusst) |
| redirect | reine Verweis-Seite auf den SSoT | V3 |
| archiviert | historischer Beleg, nicht mehr referenziert | keiner |

Bereichsentscheidungen (§3.3, unverändert aus Design §1.1): Root-Doku = `README.md`
(Handprosa + `DOCS_*`-Faktenblöcke), `docs/INDEX.md` = 100 % generiert, Architektur =
`docs/architecture/` mit generiertem Root-Stub, Guides = `docs/guides/`, Specs/Pläne =
`docs/{specs,plans,spikes}/` mit `archive/superpowers/`, Knowledge-Wiki = **kein SSoT**
(ableitender Schatten, alle Seiten mit `derived-from`), Traceability = `docs/REQUIREMENTS.md`.
Zusätzlich eingefroren: `knowledge/sources/` bleibt **unveränderlich** (NG-2).

## 4. Eingefrorene Migrationsreihenfolge W0–W8

Verweis: **Spec §9.2** (Welle → Modul → AC → Parallelität → Rückrollpunkt) und das
Wellen-Kapitel des Plans. Reihenfolge, Parallelität und Rückrollpunkt sind eingefroren.

| Welle | Modul | Wellenzweck (eingefroren) | Parallelität |
|---|---|---|---|
| W0 | — | Definition, Entscheidungs-Records (OQ2/OQ6/OQ8), Design-Freeze, Track-A-Gate; **kein Code** | sequenziell, Freeze zuerst |
| W1 | M1+M2 | DocFacts, Renderer-Grundgerüst, Snippet-Bridge, Schema-Block, Sollwert-Quelle — **rein additiv**, kein Datei-Diff außer `llms.txt` | PG-1, max. 3 Agents |
| W2 | M1 | Checks V1 (startet **WARNING**), V3, V5, V6 inkl. Sollwert-Vergleich, V7, V2/V4-Implementierung; V1-Fixture | mit W3 |
| W3 | M2 | `docs/INDEX.md`-Generator, Fact-Hash-Footer, volatile Sektion, C8-Scaffold-Guard, Besitzregel, Stage-Reihenfolge, Drift-Store, Marker-Regionen — **erster echter Datei-Diff** | mit W2, W4 |
| W4 | M3 | Architektur-Konsolidierung: `git mv` Langfassung, Root-Stub, wandernde Stale-Deklaration | mit W5, W6 |
| W5 | M3 | Guides-Auflösung (`howto/`, `docs/howto/`) + `derived-from`-Annotation + Architektur-Redirects | mit W4, W6 |
| W6 | M3 | Spec/Plan-Legacy: `git mv` nach `archive/superpowers/`, `legacy:` additiv | mit W4, W5 |
| W7 | M4 | `index.md`-Generator, `log.md`-Append, `schema.md`, `knowledge-indexer`-Umschreibung, Restore-Pfad — **isoliert, letzter Commit vor dem Merge** | **kein** Parallelbetrieb |
| W8 | M1+M3 | Totverweise, V9 `check_stale_backups`, generierte Providerzahl, `PROJECT_STRUCTURE`-Korrektur, ID-Deklaration | — |

**Eingefrorene Reihenfolge-Begründung:** W1 zuerst (additiv, kein Diff, größte Erkenntnis);
W3 vor W4/W6 (Index macht verschobene Pfade sofort sichtbar); W7 **zuletzt und isoliert**
(einziger Policy-Bruch, einziges Datenverlust-Potenzial, einzige `agents/`-Berührung).
W7-4 ist der **letzte Commit** von W7 und erfolgt erst nach dem Rollenpflege-Merge (R19).

## 5. Eingefrorene V-Check-Matrix (V1–V9)

Verweis: **Spec §5.1 / §5.1.1** (IC-05) und **Spec §10**. Wichtig für W0–W8: die
**Startwelle** (Spalte „Start") und die Severity-Stufen sind eingefroren.

| V | Check | Severity / Start (eingefroren) |
|---|---|---|
| V1 | `check_no_manual_counts` (zwei Branches V1a/V1b) | W2 **WARNING**, ab W3 ERROR |
| V2 | `check_docs_index_completeness` | ERROR ab W3 (Implementierung W2) |
| V3 | `check_internal_links` | ERROR ab W2 |
| V4 | `check_readme_docs_index` (erweitert) | ERROR, Start W3 (Implementierung W2) |
| V5 | `check_role_generation_parity` | ERROR nur bei aktiviertem SE-Gate, sonst WARNING, Start W2 |
| V6 | `check_docs_facts_fresh` (inkl. `kind=expected-mismatch` aus IC-23) | ERROR ab W2 |
| V7 | `check_wiki_staleness` | WARNING ab W2 |
| V8 | `check_spec_plan_path_convention` | WARNING ab W6 |
| V9 | `check_stale_backups` | WARNING (lokal, gitignored) ab W8 |

**Common-Gate (eingefroren):** Jeder der neun Checks ist ein No-op, solange
`docs-consolidation.enabled` nicht `true` ist. Die bestehenden drei Checks behalten Signatur
und Severity unverändert.

## 6. Commit- und Reihenfolge-Konvention je Welle

Verweis: Plan „Global Constraints" (Conventional Commits, `git add <pfad>`, kein `git add -A`),
Plan R3 („ein Commit pro Datei") und Plan R16 (PR-/Branch-Kollision, Kapitel 7 dieses Records).

1. **Format:** Conventional Commits, **Englisch**, **imperativ**, erste Zeile **≤ 72
   Zeichen** (Commit-Konvention des Repos, `AGENTS.md`).
2. **Wellenkennung im Commit-Titel —wo verbindlich (präzisiert 2026-09-26, Plan Rev. 0.3
   Punkt K8):** Der **`W<N>`-Präfix ist verbindlich** für
   (a) den **Wellen-Abschluss-Commit** `docs(docs-consolidation): W<N> complete` und
   (b) jeden **Commit-Titel, der Wellen koordiniert** (Wellen-Übergang, Reihenfolge-/Merge-
   Entscheidung, Wellen-Sammelstand) — Schema `docs(docs-consolidation): W<N> <Zweck>`.
   Für **einzelne Datei-Commits innerhalb** einer Welle (Plan R3, „ein Commit pro Datei") ist
   der Präfix **optional**; der Titel folgt dann `docs(docs-consolidation): <Zweck>` und der
   **Commit-Body führt zwingend die Task-ID** (`Task: W<N>-<k>`).
   *Begründung der Präzisierung:* Die Fassung Rev. 0.2 machte den Präfix für **alle** Commits
   einer Welle verpflichtend. Das ist mit den **47** im Plan festgeschriebenen Step-4-Commit-
   Messages unvereinbar — **0 von 47** tragen ihn; die Konvention wäre nur durch Umschreiben
   dieser 47 Stellen erfüllbar gewesen. Die **Wellenzuordnung** bleibt vollständig
   rekonstruierbar: über den Abschluss-Commit, über die koordinierenden Titel und über die
   Task-ID im Body jedes Datei-Commits.
3. **Wellen-Abschluss:** Eine Welle gilt als **abgeschlossen**, wenn genau **ein** Abschluss-Commit
   mit dem Schema `docs(docs-consolidation): W<N> complete` existiert. Er wird **erst** nach
   grüner Wellen-Verifikation erzeugt. Der Abschluss-Commit enthält **keine** inhaltliche
   Änderung, sondern den Verifikationsnachweis im Commit-Body.
4. **Granularität innerhalb einer Welle:** **ein Commit pro Datei** (Plan R3); staging nur mit
   **expliziten Pfaden** (`git add <pfad>`); verboten sind `git add -A`, `git add .`,
   `git commit -a`. Bei `git mv`-Wellen (W4, W5, W6) trägt **derselbe** Commit die Verschiebung
   **und** den Inhalts-Edit, damit Git sie als R+A-Paar führt (AC-28, DoD-6).
5. **Ausführungsreihenfolge:** Wellen in der Reihenfolge des Kapitels 4; W7-4 als letzter
   Commit der Welle; vor jedem Merge Rebase gegen `main` (Plan R3).
6. **Merge-Regel (aus Plan W0-2 Schritt 3):** `git mv`-Wellen (**W4, W5, W6**) werden
   **zuerst** gemergt, weil sie Pfade verschieben und jeden folgenden Doku-PR sonst brechen.
   Auf einem Branch ist die Entsprechung: die W4–W6-Commits müssen **vor** den Wellen W7/W8
   liegen, wenn der Branch vor dem Abschluss von W7/W8 gemergt wird.
7. **Agenten-Zuordnung:** Commit/Push ausschließlich über den `git`-Agenten; dieser Record
   erzeugt selbst **keinen** Commit.

## 7. Abweichung vom Plan: **ein** Branch statt **acht** Branches

> **Abweichung vom Plan — dokumentiert, nicht stillschweigend.**

Der Plan (Task **W0-2** Schritt 2, Global Constraints, Spec §9.2 W0, R16; **Plan-Stand vor
Rev. 0.2**) sah **acht
Wellen-Branches** `chore/docs-consolidation-w0` … `chore/docs-consolidation-w8` mit gestapelten
PRs vor. **Umgesetzt wird das nicht.** Der Nutzer hat für dieses Vorhaben **einen**
Feature-Branch **`feat/repository-documentation-consolidation-main`** mit **einem** PR (**#839**,
Base `main`) vorgegeben; dieser Branch existiert bereits auf Basis von `origin/main`.

**Was stattdessen gilt (eingefroren):**

- Die Wellen W0–W8 laufen als **sequenzielle Commits auf diesem einen Branch**.
- Die Wellen-Zuordnung erfolgt über die **Wellenkennung im Commit-Titel**
  (`docs(docs-consolidation): W<N> …`, Kapitel 6), **nicht** über die Branch-Struktur.
- **Es werden keine Branches angelegt.** Insbesondere wird `chore/docs-consolidation-w0` …
  `chore/docs-consolidation-w8` **nicht** erstellt.

**Begründung:**

1. **Nutzer-Vorgabe hat Vorrang.** Ein Branch und ein PR sind die ausdrücklich vorgegebene
   Struktur; eine Umgehung durch acht Branches wäre eine stille Planänderung.
2. **Nachvollziehbarkeit bleibt erhalten.** Die Wellenzuordnung ist im PR-Verlauf über die
   Wellenkennung im Commit-Titel (Kapitel 6, Punkt 2) und den Wellen-Abschluss-Commit
   (Punkt 3) eindeutig rekonstruierbar — der Informationsgehalt des Branch-Namens wird
   vollständig im Commit-Titel ersetzt.
3. **Kein zusätzlicher Merge-Aufwand.** Acht Branches müssten nach dem Merge **alle** in `main`
   landen; das erzeugt acht Merge-Kernel und acht Review-Zyklen, ohne dass ein zusätzlicher
   Erkenntnisgewinn entsteht (die Wellen sind ohnehin sequenziell und teilweise nicht parallel
   ausführbar, Spec §9.2).
4. **R16-Intent bleibt abgedeckt.** Das Risiko, das R16 adressiert (ein unbrauchbar großer,
   konfliktbehafteter Doku-PR), wird weiterhin über die Reihenfolge-Regel (Kapitel 6, Punkt 6)
   und die Merge-Regel „`git mv`-Wellen zuerst" beherrscht, nicht über die Branch-Anzahl.

**Folgen für die Plan-Aussage (Nachführung 2026-09-26, Plan Rev. 0.2):** Die Plan-Zeile
„Ein Branch pro Welle" (Global Constraints; Spec §9.2 W0, R16) gilt für dieses Vorhaben
**nicht**. Der Plan hat diese Vorgabe in **Rev. 0.2 selbst als überholt markiert** und die
hier dokumentierte Abweichung — **ein** Wellen-Branch, sequenzielle W-Commits mit Wellenkennung
im Commit-Titel — als begründete **Ausführungskorrektur** übernommen (Task W0-2, dort
„Ausführungskorrektur 2026-09-26"). Die damalige Verifikationszeile
`git branch --list 'chore/docs-consolidation-w*'` → **0** ist im Plan **entfallen**, weil sie
bei der umgesetzten Strategie nichts geprüft hätte; der Plan prüft seither die tatsächliche
Strategie (Stand-Synchronität **und** Existenz des Wellen-Branches unter **exaktem Namen**, siehe
Kapitel 8). **Step 2 von W0-2 („Branches anlegen") bleibt ausdrücklich nicht als erfüllt zu
behandeln**; W0-2 gilt als erfüllt über Kapitel 1–6 dieses Records.

### 7.1 Spec-Abweichung — offener Punkt **OP-1** (Stand 2026-09-26)

> **Spec-Abweichung, dokumentiert und nicht verdeckt.** **Spec §9.2 W0 und R16 verlangen
> weiterhin einen Branch pro Welle** (`chore/docs-consolidation-w<N>`, gestapelte PRs, dort
> wörtlich „**Verbindlich**: ein Branch pro Welle"); **umgesetzt ist ein Branch**. Weil dieser
> Record die Spec zur **normativen Quelle** erklärt (siehe Kopf), gewinnt nach dieser eigenen Regel
> bei Widerspruch die **Spec** — der hier eingefrorene Zustand verletzt damit die normative
> Quelle.
>
> **Beauftragt: ja. Ausgeführt: nein.** Die Korrektur der Spec (**Rev. 0.4**) ist beauftragt,
> aber **nicht ausgeführt**, weil sie ein **Concept-Review** erfordert, das nicht stattgefunden
> hat; eine Spec-Inhaltsänderung gehört nicht zum Auftrag dieses Records (Files-Ownership). Der
> Widerspruch wird deshalb **nicht** durch eine stille Planänderung beseitigt, sondern
> ausdrücklich als **offener Punkt OP-1** geführt. **Bis dahin gilt die umgesetzte Strategie.**
> Geführt ebenfalls in: Plan Rev. 0.3 (Global Constraints, W0-2, Self-Review),
> `docs/plans/…-track-a-gate.md` §10 und `…-oq6.md` (Abgrenzung, Punkt 2).
> Owner Concept-Review: `orchestrator`; Entscheidung über die Spec-Rev. 0.4: `main_chat`.

### 7.2 Branch-Bestand: **zwei** Branches mit gemeinsamem Präfix (gemessen 2026-09-26)

`git branch --list 'feat/repository-documentation-consolidation*'` ist ein **Präfix**-Match und
liefert **2** Zeilen — nicht eine, wie die Fassung Rev. 0.2 annahm:

| Branch | Status | Grund |
|---|---|---|
| `feat/repository-documentation-consolidation-main` | **aktiv** — trägt Spec/Plan/Design und PR #839 (Basis `origin/main`) | Auftragszustand, Nutzer-Vorgabe „ein Branch, ein PR" |
| `feat/repository-documentation-consolidation` | **überholt, absichtlich erhalten** | trägt eine **divergente Doppelkopie** der Spec-/Plan-Commits auf Basis eines anderen Vorfahren; **nicht** in `main` gelandet. Erhalt auf ausdrückliche **Nutzer-Vorgabe („nicht löschen")** — ein Löschen bzw. ein Post-Merge-Cleanup ist eine **eigene Entscheidung** und nicht Teil dieses Vorhabens. |

**Folge für die Verifikation:** „genau ein Wellen-Branch" bedeutet **einen aktiven
Wellen-Branch unter exaktem Namen**, nicht „genau eine Zeile" eines Präfix-Matches. Die
Prüfung adressiert deshalb `git rev-parse --verify --quiet
refs/heads/feat/repository-documentation-consolidation-main` → **0**; der Präfix-Wert **2**
ist als **dokumentierter Bestand** mitgeführt, damit ein **dritter** Branch auffällt. Es wird
**kein** Branch gelöscht.

## 8. Verifikation des Plans

**Lesehinweis:** Die Spalte „Evidenzklasse" ist **verpflichtend** (Enum siehe
„Konvention: Evidenzklassen" am Record-Anfang). Sie trennt gemessene Werte von abgeleiteten und
übernommenen — ohne sie erschiene jede Zeile als gleichwertig belegt.

| Prüfung | Kommando | Soll | Ist | Evidenzklasse | Ergebnis |
|---|---|---|---|---|---|
| IC-Anzahl | `grep -c '^#### IC-' docs/specs/2026-09-25-repository-documentation-consolidation.md` | **24** | **24** | `gezählt ohne Shell` | ✅ Übereinstimmung |
| NFA-Anzahl | `grep -c '^\| NFA-' docs/specs/2026-09-25-repository-documentation-consolidation.md` | **11** | **11** | `gezählt ohne Shell` | ✅ Übereinstimmung |
| Wellen-Branch (exakter Name) | `git rev-parse --verify --quiet refs/heads/feat/repository-documentation-consolidation-main` | existiert | existiert | `gemessen` (2026-09-26) | ✅ Übereinstimmung — Grundlage: Kapitel 7.2 |
| Branch-Bestand (dokumentiert) | `git branch --list 'feat/repository-documentation-consolidation*'` | **2** | **2** — 1 aktiver Wellen-Branch + 1 überholter, absichtlich erhaltener Branch | `gemessen` (2026-09-26) | ✅ Übereinstimmung — **kein** Prüffehler, dokumentierter Bestand (Kapitel 7.2) |
| Stand-Synchronität | `git rev-list --left-right --count origin/main...HEAD` | linke Zahl **0** (rechte Zahl unbeschränkt) | linke Zahl **0** (gemessen `0 2`) | `aus Record track-a-gate übernommen` (dort §4, `gemessen`) | ✅ Übereinstimmung — Nachführung 2026-09-26 nach Plan Rev. 0.2 |
| `scripts/lib/`-Ruhe | `git log --oneline origin/main..HEAD -- scripts/lib/` | **0** | **0** (gemessen 2026-09-26) | `gemessen` (2026-09-26) | ✅ Übereinstimmung — Plan Rev. 0.3, K7 |
| Keine `chore/`-Wellen-Branches | `git branch --list 'chore/docs-consolidation-w*'` | **entfällt** — Prüfung in Plan Rev. 0.2 gestrichen | **keine** solchen Branches angelegt (Kapitel 7) | `nicht gemessen` (Prüfung entfällt) | ➖ **nicht mehr Gegenstand** |

**Zur Zeile `scripts/lib/`-Ruhe:** Die Fassung Rev. 0.2 verlangte `git log --oneline -20 --
scripts/lib/` → **0**. Das Kommando zählt die letzten 20 Commits des Branch und ist damit
**unerfüllbar und sinnlos** (gemessen 20) — dieselbe Fehlerklasse wie `0 0`, `ls` → 1 und
`ls-tree -d` mit Pfadspec. Plan Rev. 0.3 (K7) stellt die Prüfung um auf
`git log --oneline origin/main..HEAD -- scripts/lib/` → **0**; dieselbe Begründungslogik wie K1
beim Synchronitätskriterium: abgedeckt wird ein **veralteter Prüfstand**, nicht die Existenz von
Historie. **Gemessen 0** am 2026-09-26.

**Zur Zeile „Stand-Synchronität":** Der Wert stammt **nicht** aus einer eigenen Messung dieses
Records, sondern aus dem W0-4-Gate-Record (`…-track-a-gate.md` §4, dort `gemessen`). Er wird
hier unverändert übernommen; eine erneute Messung ist der W0-4-Lauf.

**Ausführungsform der beiden grep-Prüfungen:** ausgeführt mit der dateisuchenden Prüffunktion
des Dokumentations-Agenten (Muster `^#### IC-` bzw. `^\| NFA-` gegen die Spec, Treffer
gezählt) — inhaltlich identisch zu `grep -c`, aber **ohne** Shell, daher Evidenzklasse
`gezählt ohne Shell`. Für die Protokollierung im
Plan-Ledger kann der `git`-
Agent die beiden `grep -c`-Kommandos wiederholen; die Sollwerte
24 und 11 sind belegt.

**Befund zur Verifikationsform:** Der Plan nannte zum Zeitpunkt dieses Records für die
NFA-Zählung kein grep-Muster. Die
NFA stehen in der Spec **nicht** als `####`-Überschriften, sondern als Zeilen der Tabelle in
§8; das zutreffende Muster ist deshalb `^| NFA-`. Ein `grep -c '^#### NFA-'` liefert
**0** und wäre kein Befund, sondern ein Musterfehler. IC-Überschriften sind dagegen `####`
(§5) und damit plan-konform prüfbar.
> **Nachführung 2026-09-26 (Plan Rev. 0.2):** Der Plan nennt das Muster `^| NFA-` inzwischen
> ausdrücklich (Sollwert **11**, gemessen 2026-09-26) und begründet die Abweichung vom
> IC-Muster selbst. Die Sollwerte dieses Records (IC **24**, NFA **11**) bleiben unverändert.

**Weitere Befunde (nicht durch diesen Record behoben, nur protokolliert):**

- **B-1 — Lücke in der W0-Task-Nummerierung:** Der Plan enthält W0-1, W0-2, W0-3, W0-4, W0-6,
  W0-7; **W0-5 existiert nicht**. Die Task-Gesamtzahl **47** (Plan-Kopf) ist dennoch korrekt:
  6 + 10 + 7 + 7 + 3 + 3 + 2 + 5 + 4 = 47. Kein Handlungsbedarf, aber die Nummerierung ist
  nicht lückenlos — bei Ledger-Verweisen auf „W0-5" wäre „existiert nicht" zu notieren.
- **B-2 — `scripts/lib/`-Ruhe-Gate: umgestellt (Plan Rev. 0.3, K7).** Der Plan verlangte für W0
  `git log --oneline -20 -- scripts/lib/` → **0**. Das Kommando zählt die 20 letzten Commits des
  Branch und ist **unerfüllbar** (gemessen **20**) und als Ruhe-Nachweis **sinnlos** — es würde
  auch dann 20 liefern, wenn W0 `scripts/lib/` nie berührt hätte. Umgestellt auf
  `git log --oneline origin/main..HEAD -- scripts/lib/` → **0**, **gemessen 0** am 2026-09-26
  (Evidenzklasse `gemessen`, siehe Tabelle in Kapitel 8). Dieser Record verändert ausschließlich
  `docs/plans/`; die Gegenprobe `git diff --name-only origin/main..HEAD -- scripts/lib/` → **leer**
  deckt zusätzlich `config/` mit ab (W0-4, K10) und ist in `…-track-a-gate.md` §3 belegt.

## 9. Trace-Anker

```
plan-id: PLAN-DOCS-CONSOLIDATION-2026-09-25
→ Task W0-2 (Design-Freeze, Contract-Liste, Branch-Scaffold)
→ Record: docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md
→ Normative Quelle (bleibt unverändert):
     docs/specs/2026-09-25-repository-documentation-consolidation.md
        §3 Zielstruktur/SSoT · §5 Interface Contracts (IC-01…IC-24) · §7 AC-01…AC-41
        §8 NFA-01…NFA-11 · §9.1/§9.2 Trace-Matrix und Wellenfolge · §10 Pipeline-Gate
        §12 Risiken R1…R20 · §15 Trace-Anker
     docs/specs/2026-09-25-repository-documentation-consolidation-design.md
        (verbindliche Design-Grundlage, read-only für diesen Record)
→ Verwandt:
     docs/plans/README.md                                  (Ablage-Konvention docs/plans/)
     scripts/lib/spec_plan_scaffold.py:23                  (docs/INDEX.md-Vertrag)
     AGENTS.md                                             (Commit-Konvention, Conventional Commits)
→ Abweichung von der Planvorgabe (dokumentiert, begründet): Kapitel 7 — ein Feature-Branch
  feat/repository-documentation-consolidation-main / PR #839 statt acht Wellen-Branches;
  Stand 2026-09-26: vom Plan in Rev. 0.2 als begründete Ausführungskorrektur übernommen
→ Branch-Bestand (gemessen 2026-09-26): 2 Branches mit gemeinsamem Präfix — 1 aktiver
  Wellen-Branch + 1 überholter, auf Nutzer-Vorgabe erhaltener Branch; kein Branch gelöscht
→ Offener Punkt OP-1 (Kapitel 7.1 und 10): Spec §9.2 W0 / R16 verlangen weiterhin „ein Branch
  pro Welle"; Spec-Korrektur Rev. 0.4 ist beauftragt, aber nicht ausgeführt (Concept-Review
  steht aus)
→ Gegengeprüft von: documenter (W0-2-Ausführung); Commit über git-Agent
```

## 10. Offene Punkte

| # | Offener Punkt | Stand | Owner | Wirkung |
|---|---|---|---|---|
| **OP-1** | **Spec-Abweichung „ein Branch pro Welle":** Spec §9.2 W0 und R16 verlangen weiterhin **verbindlich** einen Branch pro Welle; umgesetzt ist **ein** Branch. Weil dieser Record die Spec zur normativen Quelle erklärt, ist der eingefrozene Zustand formal eine Verletzung der normativen Quelle. Korrektur der Spec (**Rev. 0.4**) **beauftragt, nicht ausgeführt** — sie erfordert ein Concept-Review. | offen, dokumentiert, **nicht verdeckt** (2026-09-26) | `orchestrator` (Concept-Review), `main_chat` (Entscheidung über Rev. 0.4) | **keine** für die laufenden Wellen: bis zur Spec-Korrektur gilt die umgesetzte Strategie; W1/W2 sind durch W0-4 freigegeben, unabhängig von OP-1 |
| **OP-2** | **Post-Merge-Cleanup des überholten Branches** `feat/repository-documentation-consolidation` (divergente Doppelkopie der Spec-/Plan-Commits, nicht in `main`). Erhalt auf ausdrückliche Nutzer-Vorgabe; ein Löschen ist **nicht** Teil dieses Vorhabens. | offen, bewusst zurückgestellt (2026-09-26) | `main_chat` | keine; der Branch wird nicht angefasst |
| **OP-3** | **Liste der zuletzt von Track A berührten `scripts/lib/`-Dateien** — in W0-4 zugesagt, dort bewusst nicht enthalten (Plan nimmt sie vom Nachweisumfang); Klärung, ob eigener Record. | offen (aus W0-4 übernommen) | `main_chat` / `git`-Agent | keine; R3 ist über die Gegenproben `scripts/lib/` und `config/` abgedeckt (K10) |

**Kein Platzhalter:** Alle drei Punkte sind benannt, mit Stand, Owner und Wirkung versehen. Keine
weiteren offenen Punkte in diesem Record.
