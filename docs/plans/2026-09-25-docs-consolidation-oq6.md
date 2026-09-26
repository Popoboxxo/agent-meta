---
plan-id: PLAN-DOCS-CONSOLIDATION-2026-09-25
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
title: W0-1 — Ergebnis-Record OQ6 — docs/INDEX.md versioniert (tracked)
status: done
revision: 0.3
related:
  - docs/plans/2026-09-25-repository-documentation-consolidation.md
  - docs/specs/2026-09-25-repository-documentation-consolidation.md
  - docs/specs/2026-09-25-repository-documentation-consolidation-design.md
  - docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md
  - docs/plans/2026-09-25-docs-consolidation-track-a-gate.md
---

# W0-1 — Ergebnis-Record OQ6: `docs/INDEX.md` versioniert (tracked)

> Ergebnis-Record der Plan-Task **W0-1** („REC-OQ6 — `docs/INDEX.md` tracked"), Plan
> `PLAN-DOCS-CONSOLIDATION-2026-09-25`, Spec `SPEC-DOCS-CONSOLIDATION-2026-09-25`.
> **Ausführende Rolle:** `documenter` (Rollen-Ownership dieses Records; der Commit
> (`docs: record OQ6 index tracking decision`) verbleibt beim `git`-Agenten).
>
> **Nachführung 2026-09-26 (Rev. 0.2 → 0.3, Plan Rev. 0.3):** (a) Die Wellen-Branch-Konvention
> in der Abgrenzung (Punkt 2) führt die **Spec-Abweichung „ein Branch pro Welle"** als offenen
> Punkt **OP-1** und den **Branch-Bestand von 2 Branches** (1 aktiv, 1 überholt und auf
> Nutzer-Vorgabe erhalten); (b) zwei Zeilenangaben zu `.gitignore` sind korrigiert (Review-Befund
> N4: `:42` ist die Endmarkierung, nicht der Kopfkommentar); (c) die **Evidenzklassen-Konvention**
> ist ergänzt. **Die Tracking-Entscheidung (**tracked**), die `.gitignore`-Folge, der Sollwert `1`
> und alle Aussagen zu `docs/INDEX.md` bleiben unverändert.**
>
> **Nachführung 2026-09-26 (Rev. 0.1 → 0.2):** Der Plan wurde auf **Rev. 0.2** korrigiert; die
> Branch-Strategie-Aussage in der Abgrenzung (Kapitel „Abgrenzung", Punkt 2) wurde darauf
> nachgeführt. Die Tracking-Entscheidung (**tracked**), die `.gitignore`-Folge und alle
> Verifikationswerte dieses Records bleiben inhaltlich **unverändert**.
>
> **Charakter:** Dieser Record **trifft die Entscheidung nicht**, er **dokumentiert** eine
> bereits getroffene Entscheidung. Die normative Quelle bleibt **Spec §11.2 (OQ6)**; bei
> Widerspruch zwischen diesem Record und der Spec gilt die **Spec**.

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
Sollwert-Check `nicht gemessen` (es lag kein Git-Werkzeug vor) und die `.gitignore`-Vorprüfung
`gezählt ohne Shell` (Lesezugriff/Grep ohne Shell).

## Trace-Anker

| Anker | Quelle | Aussage |
|---|---|---|
| Spec §11.2, Zeile **OQ6** | Spec „Geschlossene Fragen" | `docs/INDEX.md` ist **versioniert (tracked)**; **kein** `.gitignore`-Eintrag; der Vertrag aus `spec_plan_scaffold.py` + `project.yaml` bleibt unverändert; W0/W1-Blockade aufgehoben |
| Spec §3.1 „Generationsmodi" | Modus **generiert** | `docs/INDEX.md` ist 100 % Generator-Output; Handedit ist ein Fehler (Drift-Folge V6) |
| Spec §5.1, Check **V2** | `check_docs_index_completeness` | bezieht sich auf **getrackte** `docs/**/*.md` — Tracking ist Voraussetzung des Checks |
| Spec §5.4, **IC-22** | Rollback-/Gate-Config | `docs-consolidation.index-mode`: `full` (Voll-Index ersetzt nur ein Scaffold-Skeleton) / `skeleton` (Rollback-Hebel); Fail-off-Defaults |
| Spec §9.2 / §11.2-OQ6-Nachtrag | Wellenfolge | Umsetzung in **W3**, Entscheidungspunkt in **W0** (`W0-1`), Blockade **W0/W1** |
| Plan „File Structure", Eintrag `.gitignore` | Plan | `.gitignore` ist **unverändert**; **kein** Task schreibt oder verändert die Datei |
| Code-Vertrag | `scripts/lib/spec_plan_scaffold.py:23` (`DEFAULT_FALLBACK_INDEX`), `scripts/lib/spec_plan_scaffold.py` → `resolve_index_mode()` | `docs/INDEX.md` ist der etablierte Fallback-Index-Pfad; `project.yaml:70` (`fallback-index: docs/INDEX.md`) setzt ihn für agent-meta |

## Zweck und Geltungsbereich

Dieser Record schließt die Plan-Task **W0-1** ab und macht die Tracking-Entscheidung für
alle Folgewellen (W1–W8) eindeutig dokumentiert.

| | |
|---|---|
| **Entscheidung** | `docs/INDEX.md` ist **versioniert (tracked)** |
| **Datum** | **2026-09-26** |
| **Entscheider** | **Nutzer**, über `main_chat` an den `orchestrator` (Vermerk in Spec §11.2 OQ6) |
| **Scope der Entscheidung** | (a) Git-Tracking-Status des generierten Doku-Index; (b) die daraus folgende `.gitignore`-Frage; (c) die Reihenfolge: Entscheidungspunkt **W0**, Umsetzung **W3** |
| **Nicht im Scope** | Inhalt/Format des Index (IC-10), der `index-mode`-Wert selbst (IC-22, Default `full`), der Regenerationsauslöser (OQ8, eigener Record W0-6), jede `.gitignore`-Änderung |

**Gewählt / verworfen.** Gewählt: **tracked** — deckt sich mit der Empfehlung der Spec
(`project.yaml:70` schreibt `docs/INDEX.md` ohnehin als Fallback-Skeleton *im Repo*), mit
Spec §3.1 („100 % generiert" unter `docs/`) und mit dem Plan (Create `docs/INDEX.md`, W3-6).
**Verworfen:** die Alternative *generiert-untracked wie `.claude/`* — sie hätte die Datei per
`.gitignore` ausgeschlossen und damit die Sichtbarkeit des generierten Index im Review
(Drift-PRs) sowie die V2-Prüfmenge (nur **getrackte** `docs/**/*.md`) unterlaufen.

## Verifikation

### 1. Umsetzungsvoraussetzung (Plan-W0-1, „Verifikation")

**Sollwert: `git check-ignore -q docs/INDEX.md; echo $?` → `1`** (nicht ignoriert). Da die
gesicherte Entscheidung `tracked` ist, ist **`1` der Sollwert**; ein Exit **`0`** würde
bedeuten, dass eine Ignore-Regel `.gitignore` auf `docs/INDEX.md` anwendet — das wäre ein
**Widerspruch zur Entscheidung** und ist in diesem Fall als solcher zu melden, nicht zu
korrigieren.

**Status: in diesem Record NICHT gemessen.** Der ausführende Agent hat kein Git-Werkzeug;
es wurde **kein Messwert erhoben und keiner erfunden**. Die Ausführung des Kommandos erfolgt
beim `git`-Agenten (Commit-Task der W0-1, Commit-Message `docs: record OQ6 index tracking
decision`) bzw. spätestens in **W3-6**, wo dasselbe Kommando als Akzeptanz- und
Verifikationskriterium erneut geführt wird.

### 2. Inhaltliche Vorprüfung ohne Shell (Grep/Lesezugriff, hier durchgeführt)

Evidenzklasse: **`gezählt ohne Shell`** (Lesezugriff und Grep, kein Shell-Lauf). Der **tragende
Nachweis ist die vollständige Musterdurchsicht**, nicht die Trefferzählung — siehe die
Einschränkung am Ende dieses Abschnitts.

| Prüffrage | Ergebnis |
|---|---|
| Existiert ein `.gitignore`-Eintrag, der `docs/INDEX.md` trifft? | **nein** |
| Existiert ein Eintrag für `docs/INDEX*` oder ein generisches `INDEX.md`? | **nein** |
| Existiert eine Regel, die `docs/` als ganzes oder `*.md` ausschließt? | **nein** |
| Treffer der Suche nach `INDEX`/`index` in `.gitignore` | genau **ein** Treffer, `.gitignore:74` — ein **Kommentar** (`# ProjectAtlas local repository-intelligence index …`), keine Musterzeile |

**Musterdurchsicht (tragender Nachweis):** Alle **75 Zeilen** (Stand 2026-09-26) wurden
klassifiziert. Die **nicht-verankerten Basename-Muster** — also Muster **ohne** führenden `/`
und **ohne** inneren Pfadtrenner, die deshalb einen Dateinamen in **beliebiger Tiefe** treffen
können — sind vollständig aufgelistet:

| Muster (ohne Pfadanker) | Zeile(n) | Kann `docs/INDEX.md` treffen? |
|---|---|---|
| `*.pyc` | 1 | nein (Endung) |
| `__pycache__/` | 2 | nein (Verzeichnisname) |
| `CLAUDE.personal.md` | 7, 40 | nein (exakter Basename) |
| `sync.log` | 8, 41 | nein (exakter Basename) |
| `package-lock.` | 9 | nein (exakter Basename) |
| `*.sync-backup-*` | 22 | nein (Muster `*.sync-backup-*`) |
| `AGENTS.personal.md` | 39 | nein (exakter Basename) |
| `.mcp.json` | 29, 46 | nein (Punktdatei) |
| `.opencode.json` | 47 | nein (Punktdatei) |
| `.cursorrules` | 45 | nein (Punktdatei) |
| `.windsurfrules` | 48 | nein (Punktdatei) |
| `*.bak.*` | 64 | nein (Muster) |
| `node_modules/` | 68 | nein (Verzeichnisname) |
| `.venv/`, `.local/`, `.input/`, `.backup/`, `.ship-safe/`, `.tokensave/`, `.graphify`-Verzeichnisse (`.projectatlas/`, `.meta-viz/`, `graphify-out/`), `.claude/`, `.gemini/`, `.mammouth/`, `.opencode/`, `.serena/` | 2–17, 62–75 | nein (ausschließlich Verzeichnisnamen) |

Die übrigen Muster sind **Pfad-verankert** (enthalten einen inneren `/` oder einen führenden
`/`) und damit auf einen Ort im Baum begrenzt: `/external/*` mit Ausnahme
`!/external/AGENT_META_INFO.md` (18–19), die `.claude/…`, `.gemini/…`, `.meta-config/…`,
`.opencode/…`, `.kiro/…`-Einzeldateien (23–37, 49–53) sowie die **einzigen** `docs/`-Muster
`docs/concepts/.local-Inputs/architecture_law.md`, `…/featuretemplate.md`, `…/reqmanager-se.md`
(59–61) — alle drei **explizit benannt**, keines ist `docs/**/*.md`.

**Ergebnis:** **kein Muster erreicht `docs/INDEX.md`** — weder als Pfad-Muster noch als
Basename-Muster. Kein Konfliktpotenzial; der Sollwert `1` ist inhaltlich gestützt. Die
Vorprüfung ersetzt **nicht** die Messung, sie begründet den Sollwert.

> **Einschränkung der Trefferzählung (Proxy, nicht tragend):** Die Suche nach `INDEX`/`index`
> ist **case-sensitiv** und zählt nur **Zeilen**, nicht **Muster**. Sie fände weder ein Muster mit
> alternierenden Zeichenklassen (`*[Ii][Nn][Dd][Ee][Xx]*`) noch ein generisches `docs/*.md` und
> wäre bei einem solchen Muster ein **Fehlbefund**. Deshalb ist die **Musterdurchsicht oben der
> tragende Nachweis**; die Trefferzahl ist nur der Hinweis, dass überhaupt kein `INDEX`-Muster
> existiert.


## Folgen der Entscheidung

| Betroffen | Folge |
|---|---|
| **W3-6** (Plan, W3) | Legt `docs/INDEX.md` an und committet sie (**tracked**). Schreibt **nicht** in `.gitignore`; dessen `Files:`-Liste nennt ausdrücklich „**kein** `.gitignore`-Eintrag (OQ6 entschieden: `tracked`)". Akzeptanz: `git check-ignore -q docs/INDEX.md` → `1`, V2/V4 grün gegen das reale `docs/INDEX.md`, zweiter Sync-Lauf `unchanged` mit null Schreibvorgängen |
| **W3-7** (Plan, W3) | Kein eigener Tracking-Teil; die Hybrid-Regionen in `README.md`, `llms.txt`, `ARCHITECTURE.md` stehen in derselben Welle. `docs/INDEX.md` selbst wird **nicht** zur Hybrid-Datei (Modus bleibt **generiert**) |
| **W1 / W1-10** (Plan, W1; IC-22) | `docs-consolidation.index-mode` (Default `full`, agent-meta explizit `full`) sowie `enabled: true` explizit, `checks.strict` erst in W3-4. Der Tracking-Entscheid ändert **keinen** Config-Key; `index-mode` steuert das **Schreibverhalten** (Voll-Index ersetzt nur ein Scaffold-Skeleton, `skeleton` = Rückroll-Hebel), **nicht** den Tracking-Status |
| **W1-9 / IC-15** (`spec_plan_scaffold.py`) | Vertrag `DEFAULT_FALLBACK_INDEX` / `resolve_index_mode()` bleibt **unverändert**; `is_file_index_skeleton()` + Marker (IC-15) sind der Mechanismus, der Skeleton und Voll-Index unterscheidbar macht — Voraussetzung dafür, dass eine getrackte Datei zweimal sauber ersetzt wird |
| **Fact-Hash / Drift (W1, W3-2, W3-5; IC-14, IC-16)** | Weil die Datei getrackt ist, ist ihr Diff im Review sichtbar; der Footer enthält **nur** `facts-hash: <16 hex>` und `generator: doc-indexer/1`, **kein** Datum, **keine** Uhrzeit, **keinen** absoluten Pfad, **keinen** Benutzernamen (AC-18/NFA-02). Volatile Fakten erscheinen ausschließlich in der `docs-volatile`-Sektion **vor** dem Footer und fließen **nicht** in den Hash ein (R1) |
| **AC-12 / V2** | `check_docs_index_completeness()` prüft „jede **getrackte** `docs/**/*.md`" (ohne `archive/`, `_archive/`, ohne `docs/INDEX.md` selbst). Tracking ist damit **Voraussetzung** der Vollständigkeitsprüfung; `docs/INDEX.md` selbst und `archive/`-Pfade erzeugen **kein** Finding |
| **AC-20** (IC-13, IC-15) | `sync_docs_consolidation(...)` ersetzt ein Scaffold-Skeleton durch den Voll-Index: `log.action("UPDATE","docs/INDEX.md",…)` **einmalig**, zweiter Lauf `unchanged` mit **null** Schreibvorgängen — auf einer **getrackten** Datei |
| **AC-21** (IC-15, IC-13) | `index-mode: skeleton` lässt die getrackte Datei byte-identisch zum Skeleton; bei `resolve_index_mode() == "knowledge-engine"` wird **kein** `docs/INDEX.md` geschrieben, Eintrag in `skipped` + `log.note` |
| **R7 (Doppel-Writer)** | Der Skeleton-/Voll-Index-Unterschied plus verbindliche Stage-Reihenfolge (Generator **nach** Scaffold) verhindert den Doppelschreiben auch auf einer getrackten Datei |

## Auswirkung auf das DoD

- **DoD-Punkt 4 des Gesamtvorhabens** („`docs/INDEX.md` existiert, ist **getrackt** und 100 %
  generiert; zweimaliger Sync ⇒ `unchanged`, null Schreibvorgänge") ist mit dieser Entscheidung
  **inhaltlich erfüllbar**; ohne Tracking wäre der „getrackt"-Teil unerreichbar.
- **Nachweis, dass die Datei getrackt ist:** `git check-ignore -q docs/INDEX.md; echo $?` → `1`
  (W0-1/W3-6) **in Verbindung mit** der Aufnahme der Datei in den Commit der Welle W3. Der
  Exit-Code allein belegt nur „nicht ignoriert" — die Git-Hashing-Seite ist zusätzlich durch
  den Commit-Nachweis (`git status --porcelain` ohne unversionierten `docs/INDEX.md`-Eintrag
  bzw. Existenz im Commit-Dateibaum) abzudecken.
- **Nachweis der Regenerierbarkeit/Determinie:** zweimaliger Sync-Lauf meldet `unchanged` mit
  null Schreibvorgängen (NFA-01/AC-20) und `python3 scripts/sync.py --check` → `0`; der
  `facts-hash`-Footer wechselt nur bei Faktenänderung (AC-18).
- **Nachweis der Vollständigkeit:** V2 (`check_docs_index_completeness`, ERROR ab W3) und V4
  (`check_readme_docs_index`, erweitert auf den gesamten `docs/`-Baum) gegen das **reale**
  `docs/INDEX.md`.
- **DoD-Punkt 9** verlangt für alle sechs Entscheidungs-Records: Owner, Entscheidung und Datum —
  dieser Record liefert sie für **OQ6** (Abschnitt „Zweck und Geltungsbereich").
- **DoD-Punkt 12** (`python3 scripts/sync.py --validate` → `0`, `--check` → `0`) ist von der
  Tracking-Entscheidung **nicht** betroffen; W0–W2 laufen weiterhin mit `docs-consolidation.enabled`
  noch nicht wirksam (Featur-Default fail-off, IC-22).

## Abgrenzung

1. **`.gitignore` wird nicht angefasst.** Kein Task der W0–W8 schreibt oder verändert diese
   Datei; es entsteht **kein** Ignore-Eintrag für `docs/INDEX.md` und **kein** Diff an
   `.gitignore`. `.gitignore:22` (`*.sync-backup-*`) wird ausschließlich als **Beleg** für den
   Check V9 (`check_stale_backups`) zitiert, nicht verändert. Der Bestand in `.gitignore:21`
   (Kopfmarkierung des verwalteten Blocks, `# --- agent-meta managed (do not edit) ---`) und
   `.gitignore:42` (Endmarkierung, `# --- end agent-meta managed ---`) bleibt unberührt.
2. **Kein CI-Bezug.** Der Plan enthält **keine** Stelle zu GitHub-Actions/CI; die
   Basis-Branch-Angabe `main` (PR #839, Basis `main`) ist Kontext des Auftrags und der
   Wellen-Branch-Konvention (Plan Rev. 0.2/0.3: **ein** Wellen-Branch statt „ein Branch pro
   Welle", R16, Ausführungskorrektur 2026-09-26; Wellenzuordnung über die Wellenkennung im
   Commit-Titel bzw. die Task-ID im Commit-Body) — dieser Record leitet daraus
   **keine** CI-Aussage ab und behauptet insbesondere nicht, dass eine CI-Prüfung die
   Tracking-Entscheidung bestätigt. Der einzige normative Nachweis ist das
   `check-ignore`-Kommando aus Abschnitt „Verifikation".
   > **Nachführung 2026-09-26:** Dieser Record wurde vor Plan Rev. 0.2 geschrieben und zitierte
   > die überholte Plan-Zeile „Ein Branch pro Welle". Die Branch-Strategie ist seither die
   > andere; die Tracking-Entscheidung dieses Records (OQ6 → **tracked**) und alle
   > Abgrenzungen bleiben davon unberührt.
   >
   > **Spec-Abweichung, offener Punkt OP-1 (Stand 2026-09-26) — nicht verdeckt:** **Spec §9.2 W0
   > und R16 verlangen weiterhin einen Branch pro Welle; umgesetzt ist ein Branch.** Korrektur
   > der Spec (**Rev. 0.4**) ist **beauftragt, aber nicht ausgeführt** — sie erfordert ein
   > **Concept-Review**. Bis dahin gilt die umgesetzte Strategie. Details: W0-2-Record
   > Kapitel 7.1 und §10, Track-A-Gate-Record §10, Plan Rev. 0.3 Self-Review.
   >
   > **Branch-Bestand (gemessen 2026-09-26):** `git branch --list
   > 'feat/repository-documentation-consolidation*'` → **2** Zeilen — der **aktive** Wellen-Branch
   > `feat/repository-documentation-consolidation-main` und der **überholte** Branch
   > `feat/repository-documentation-consolidation` (divergente Doppelkopie der Spec-/Plan-Commits,
   > nicht in `main`), der auf ausdrückliche **Nutzer-Vorgabe („nicht löschen")** erhalten bleibt.
   > Es wird **kein** Branch gelöscht; ein Post-Merge-Cleanup ist eine eigene Entscheidung
   > (**OP-2** im W0-2-Record §10). Für OQ6 ohne Wirkung — die Tracking-Entscheidung hängt an
   > keinem Branch.
3. **Keine Code-, Config- oder Pipeline-Wirkung.** Dieser Record ist rein dokumentarisch; ein
   Rollback besteht im Entfernen der Datei. Er ändert weder `spec_plan_scaffold.py` noch
   `.meta-config/project.yaml` und ist **keine** Freigabe für W3.
4. **Abgrenzung zu den Nachbar-Records:** W0-3 (OQ2 `llms.txt` Hybrid) und W0-6 (OQ8
   Regenerationsauslöser) betreffen andere Entscheidungen desselben Wellen-Blocks; OQ6 ist
   davon unabhängig und wird **nur** hier dokumentiert.
