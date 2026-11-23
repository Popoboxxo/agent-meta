---
pipeline_stages:
  implement: 3
status: geplant
date: 2026-11-23
issue: 1204
issue-url: "https://github.com/Popoboxxo/agent-meta/issues/1204"
spec: docs/specs/2026-11-23-decision-1204-adminui-conventions-spec.md
spec-id: SPEC-1204-ADMINUI-CONVENTIONS
spec-status: APPROVED
class: M
branch: fix/decision-points-bundle-20261123
base-commit: 52bb8d9
spec-measured-at: 278ba54f
---

# Admin-UI: inerte conventions.issues.* kennzeichnen, issues.language editierbar (#1204) — Implementierungsplan

> Status: geplant
> **Quelle:** `docs/specs/2026-11-23-decision-1204-adminui-conventions-spec.md` (`Status: APPROVED`, `SPEC-1204-ADMINUI-CONVENTIONS`, User-Einzelentscheidung 2026-11-23, Klasse M).
> **Umsetzungsfreigabe:** Spec APPROVED → Implementierung autorisiert (Master-Rule `spec-plan-workflow`). #1188 ist Dependency (Spec + Plan APPROVED, **Code absent**), aber kein Code-Blocker: #1204 läuft autonom durch.
> **Stände:** Spec-Re-Messung bei `278ba54f`; dieses Planset läuft auf `52bb8d9`. Task 1 verifiziert die Anker am Ausführungs-Checkout.

**Goal:** `conventions.issues.language` in beiden Admin-UI-Editoren editierbar machen und die vier wirkungslosen `issues.*`-Felder als `documentation only` kennzeichnen — ohne Render-/Config-Pfade, bestehende Projektdaten oder #1188-Code anzutasten.
**Architecture:** Reine UI-/Test-Änderung. `docs/ui/admin-ui.html` ist der einzige Produktivcode-Träger: `DOMAIN_FIELDS.issues` (Overrides-View), `scalarField`-Einschub (Preset-Editor), Intro-Text, `render()`-Badge und eine CSS-Regel. Consumer-Pfade (`config.py → ISSUE_LANGUAGE`, `conventions.py → GIT_ISSUE_NAMING_BLOCK`) bleiben read-only; die Feldtaxonomie gehört #1188, dieser Plan markiert nur.
**Tech Stack:** Python 3 (Stdlib), pytest, statische HTML/JS-Admin-UI, Markdown.
**Spec:** docs/specs/2026-11-23-decision-1204-adminui-conventions-spec.md

## Global Constraints

- **Nur eine Produktivdatei:** `docs/ui/admin-ui.html`. `scripts/lib/conventions.py`, `scripts/lib/config.py`, `agents/1-generic/git.md`, `config/conventions-presets.yaml`, `scripts/admin-server.py` und `tests/test_issue_language.py` bleiben byte-identisch (AC-05).
- **Markieren, nicht löschen** (D-1204-A, entschieden): Die 4 Felder `title_format`, `types`, `labels.namespace`, `closing_keywords` bleiben sichtbar, editierbar und gespeichert; nur der Wirksamkeitsindikator ändert sich.
- **Keine #1188-Semantik:** Kein Feld-Set aus der noch nicht ausgelieferten Taxonomie, kein Pane-Umzug, kein Deprecation-Redirect jetzt (D-1204-C vertagt). Kein toter Link auf eine #1188-Sektion (D-1204-B Default).
- **R-1:** Nur `default` hat `language: english` (`conventions-presets.yaml:67`); `calver`/`conventional-strict` zeigen `—`. Der Hinweistext darf daraus keinen „fehlenden Wert" ableiten; Laufzeit-Default bleibt `english`.
- **Badge-Klasse (Review-Befund):** `.badge.muted` existiert nicht (nur `.badge.optional` `:363`, `.badge.legacy` `:368`). Bindende Plan-Entscheidung: `.badge.muted` als CSS-Regel neben `.badge.optional` ergänzen; `.badge.legacy` ist erlaubter Fallback, dann passt Task 2 den CSS-Pin an. Nie `badge muted` ohne Definition ausliefern.
- **Keine Closing-Keywords:** Weder im Plan noch im Commit-Entwurf (`Fixes`/`Closes`/`Resolves` + Issue-Referenz). Kein Push, Tag oder Branch-Management.
- **TDD-Reihenfolge:** Red (Task 2) → Green (Task 3) → Regression (Task 4). Kein Implementieren vor bestandenem Red-Nachweis.

## File Structure

- **Modify:** `docs/ui/admin-ui.html` — `DOMAIN_FIELDS.issues` +4. Element `docOnly` und `language`-Zeile (`:4220-4225`); Per-Preset-Editor `scalarField("language", …)` (`:4158-4168`); Intro-Hinweis (`:4181-4183`); `render()`-Badge (`:4286-4326`, Zeile `:4323`); CSS `.badge.muted` (bei `:363`). Save-Pfad `:4338-4339` bleibt unberührt.
- **Create:** `tests/test_admin_ui_conventions_overrides_section.py` — statische HTML-Slice-Tests im Stil von `tests/test_admin_ui_auto_commit_section.py:1-33`; pinnt AC-01..AC-04 und die Badge-Entscheidung.
- **Read-only (Nie-Ziel, byte-identisch):** `scripts/lib/conventions.py:131-132/277-292`, `scripts/lib/config.py:3454/3501-3503`, `tests/test_issue_language.py:26-56`, `config/conventions-presets.yaml:53-67`, `agents/1-generic/git.md:159`.
- **Kein Output:** keine neue Spec, kein ADR (Single-File-Scope), kein Schema/API/State, kein Tracker-Call.

## Entscheidungen (bindend für die Tasks)

| ID | Status | Plan-Wirkung |
|---|---|---|
| D-1204-A | entschieden | Markieren statt Löschen → `docOnly: true`, keine `delPath`-Änderung für die 4 Felder. |
| D-1204-B | offen, Default | Neutraler Hinweis ohne #1188-Link (AC-03). Eskalation nur bei explizitem User-Wunsch. |
| D-1204-C | vertagt | Kein Feld-Set erfinden, kein Umzug der `issues`-Domain. Deprecation-Hinweis/Redirect erst nach #1188 mit separater Freigabe. |
| R-1 | Risiko | Hinweis nennt `language` als verhaltenswirksam, ohne aus `—` in `calver`/`conventional-strict` einen Fehler abzuleiten. |

---

### Task 1: Interface-Reverifikation am Checkout 52bb8d9 (read-only)

**Agent:** `explorer`
**Files:** Read-only: `docs/ui/admin-ui.html`, `scripts/lib/conventions.py`, `scripts/lib/config.py`, `tests/test_issue_language.py`, `config/conventions-presets.yaml` — keine Schreibrechte, keine Dateierstellung.
**Interfaces:** Consumes: Spec IC-1..IC-5, Trace-Anker, `base-commit: 52bb8d9`. Produces: Verifikationsnotiz im Task-Kommentar (Ist-Zeilen, Badge-Befund, #1188-Abgrenzung).

- [ ] Step 1: Anker `admin-ui.html:4158-4168`, `:4178-4183`, `:4211-4226`, `:4260-4268`, `:4286-4326`, `:4323`, `:4338-4339`, `conventions.py:131-132/277-292`, `config.py:3454/3501-3503`, `tests/test_issue_language.py:26-56`, `conventions-presets.yaml:53-67` gegen den Checkout prüfen; Abweichungen mit Ist-Zeilennummer notieren.
- [ ] Step 2: Badge-Befund bestätigen: `.badge.muted` fehlt, `.badge.optional` (`:363`) und `.badge.legacy` (`:368`) existieren → Plan-Entscheidung (`.badge.muted` ergänzen, `.badge.legacy` Fallback) gegen Datei verifizieren.
- [ ] Step 3: Bestätigen, dass `PROJECT_WRITABLE_SECTIONS` (`scripts/admin-server.py:239-246`) `conventions`/`conventions-preset` bereits enthält → kein Server-/API-Task nötig; #1188-Code bleibt absent.

**Akzeptanzkriterium (messbar):** Alle 11 Anker sind bestätigt oder mit Ist-Zeile korrigiert; Badge-Entscheidung ist schriftlich fixiert; `0` geänderte Dateien.

---

### Task 2: Red-Tests für IC-1/IC-2/IC-3/IC-6 (AC-01..AC-04)

**Agent:** `tester`
**Files:** Create `tests/test_admin_ui_conventions_overrides_section.py` (Style-Vorlage: `tests/test_admin_ui_auto_commit_section.py:1-33`). Schreibownership nur auf dieser Testdatei.
**Interfaces:** Consumes: statische HTML-Slices aus `docs/ui/admin-ui.html`, Spec IC-1/IC-2/IC-3/IC-6. Produces: `-> None`-pytest-Funktionen, Red-Status plus grüne Baseline.

- [ ] Step 1: Helfer `_conventions_overrides_view()` (`HTML.index("async function viewProjectConventionsOverrides()")` bis `Views — Project Knowledge Engine`) und `_preset_editor_issues()` (Slice `// issues domain` bis `panel.appendChild(issSec)`) anlegen.
- [ ] Step 2: Acht Tests schreiben: (a) `language`-Zeile in `DOMAIN_FIELDS.issues`; (b) `scalarField("language", issues, "language")` im Preset-Editor; (c) vier `docOnly: true`-Marker, `language` ohne Marker; (d) `docOnly`-Zeile nutzt `.badge.muted` + Label `documentation only`, kein `badge ok` in dieser Zeile; (e) Intro nennt `git.md`-Hilfetext und `language` als wirksam, kein #1188-Link; (f) Consumer-Pin: jedes `DOMAIN_FIELDS.issues`-Label hat `ISSUE_LANGUAGE`/`GIT_ISSUE_NAMING_BLOCK` **oder** `docOnly` — unbekanntes Feld ohne beides lässt den Test fehlschlagen (AC-04); (g) `.badge.muted {` existiert im CSS; (h) die zwei `saveProjectSection`-Aufrufe `:4338-4339` sind unverändert.
- [ ] Step 3: Red bestätigen: `python3 -m pytest tests/test_admin_ui_conventions_overrides_section.py -q` → mindestens 1 Failure; gleichzeitig `python3 -m pytest tests/test_issue_language.py -q` → 4 passed (Baseline grün, AC-05-Voraussetzung).

**Akzeptanzkriterium (messbar):** Neue Testdatei existiert, der neue Testlauf ist rot (≥1 `failed`), `tests/test_issue_language.py` ist 4/4 grün; keine Produktivdatei geändert.

---

### Task 3: Implementierung — language + docOnly + Hinweis + Badge (Green)

**Agent:** `developer`
**Files:** Modify `docs/ui/admin-ui.html` — einzige Produktivdatei. Kein anderer Pfad, keine Testdatei (Testdatei gehört Task 2).
**Interfaces:** Consumes: Spec IC-1/IC-2/IC-3, R-1, D-1204-A/B/C, Task-1-Notiz. Produces: editierbares `language` in beiden Editoren, `docOnly`-Marker, Hinweistext, `.badge.muted`-CSS, unveränderter Save-Pfad.

- [ ] Step 1 (IC-1, AC-01/AC-04): In `DOMAIN_FIELDS.issues` (`:4220-4225`) `[["language"], "language", "scalar"]` ergänzen; die vier Zeilen `:4221-4224` um das 4. Element `docOnly: true` erweitern. `countOverrides()` (`:4263`) destrukturiert weiter `[path]` und `render()` (`:4286`) `[path, label, type, docOnly]`; Zählung und `setPath`/`delPath` bleiben unverändert.
- [ ] Step 2 (IC-2, AC-01, R-1): Im Preset-Editor (`:4158-4168`) `issSec.appendChild(scalarField("language", issues, "language"))` nach `closing_keywords` einfügen. Typ `scalar`, kein Validierungszwang, kein Default-Schreiben — `calver`/`conventional-strict` zeigen weiter `—`.
- [ ] Step 3 (IC-3, AC-03, D-1204-B/C): Intro-Text (`:4181-4183`) um einen neutralen Satz ergänzen: die markierten Felder betreffen nur den Hilfetext in `git.md` (`GIT_ISSUE_NAMING_BLOCK`), `language` ist das verhaltenswirksame Feld (`ISSUE_LANGUAGE`). Kein Link auf eine #1188-Sektion, kein Feld-Set aus #1188, kein jetziger Deprecation-Redirect.
- [ ] Step 4 (IC-3, AC-02): In `render()` (`:4323`) Badge-Klasse für `docOnly`-Zeilen auf `muted` setzen — `const badgeClass = docOnly ? "muted" : (isOverridden ? "warn" : "ok");` — und den Badge-Text auf `documentation only · ${fmt(activeVal) || "—"}` stellen. Kein grünes `ok` für markierte Zeilen; Input-Feld bleibt editierbar und speicherbar.
- [ ] Step 5 (Badge-Entscheidung): `.badge.muted { background: rgba(110,118,129,0.12); color: var(--text-muted); }` neben `.badge.optional` (`:363`) ergänzen. Falls `.badge.legacy` (`:368`) als Klasse gewählt wird: dieselbe Zeile mit `legacy` ausliefern und Task-2-Test (g) vor Green anpassen — nie eine undefinierte Klasse erzeugen.
- [ ] Step 6 (Green): `python3 -m pytest tests/test_admin_ui_conventions_overrides_section.py tests/test_issue_language.py -q` → alle Tests grün.

**Akzeptanzkriterium (messbar):** Beide Editoren bieten `language`; vier Zeilen tragen `docOnly: true` und zeigen `documentation only` mit `.badge.muted` ohne `ok`; Hinweistext ohne #1188-Link; `.badge.muted` (oder `.badge.legacy`) ist definiert; alle Tests grün; `git diff --name-only` zeigt genau `docs/ui/admin-ui.html` als Produktivänderung.

---

### Task 4: Regressionslauf und Nicht-Ziel-Byte-Identität (AC-05)

**Agent:** `tester`
**Files:** Test (read-only): gesamte Suite, `scripts/sync.py`, die fünf Nie-Ziel-Dateien. Keine Schreibrechte.
**Interfaces:** Consumes: Green-Stand aus Task 3, Spec AC-05. Produces: Testergebnis-Protokoll im Task-Kommentar.

- [ ] Step 1: `python3 scripts/sync.py --validate` → Exit 0, keine Drift-Meldung.
- [ ] Step 2: `python3 -m pytest -q` → 0 Failures, inklusive `tests/test_issue_language.py:26-56` (Default, Override, Unabhängigkeit von `git`, Self-Hosting).
- [ ] Step 3: Byte-Identität der fünf Nie-Ziel-Dateien per lesendem `git diff --exit-code -- scripts/lib/conventions.py scripts/lib/config.py agents/1-generic/git.md config/conventions-presets.yaml tests/test_issue_language.py` → Exit 0.

**Akzeptanzkriterium (messbar):** Beide Kommandos exit 0; `pytest` 0 Failures; der `git diff --exit-code`-Aufruf liefert Exit 0 und damit 0 Abweichungen in den fünf Nie-Ziel-Dateien.

---

### Task 5: DoD-/Acceptance-Audit

**Agent:** `validator`
**Files:** Read-only: Spec, `docs/ui/admin-ui.html`, neue Testdatei, Commit-Entwurf. Keine Schreibrechte.
**Interfaces:** Consumes: AC-01..AC-05, IC-1..IC-6, D-1204-A/B/C, R-1, Task-4-Protokoll. Produces: Audit-Kurzbericht im Task-Kommentar.

- [ ] Step 1: AC-01..AC-05 einzeln gegen Code + Tests abhaken (AC-Map unten); jede Zeile mit Datei:Anker belegen.
- [ ] Step 2: Abgrenzung prüfen: 0 implementierte #1188-Semantik, 0 toter #1188-Link, 0 gelöschte Felder, 0 erfundenes Feld-Set, 0 Änderung an `PROJECT_WRITABLE_SECTIONS`.
- [ ] Step 3: Commit-Entwurf prüfen: Subject `< 72` Zeichen, beginnt auf Byte 0 mit `feat:` (kein UTF-8-BOM), 0 Closing-Keywords, 0 Push/Tag/Branch-Aktionen.
- [ ] Step 4: Plan-Self-Review gegen `writing-plans`-Checkliste bestätigen (pipeline_stages, Spec-Ref, Ownership, Interfaces, AC-Map, keine Platzhalter).

**Akzeptanzkriterium (messbar):** 5/5 AC mit Anker belegt, 0 Abweichungen in Schritt 2, 0 Closing-Keywords und 0 BOM im Commit-Entwurf; Self-Review vollständig.

---

### Task 6: Commit vorbereiten (durch Caller/Orchestrator angewendet)

**Agent:** `git`
**Files:** Commit-Scope genau: Modify `docs/ui/admin-ui.html`, Create `tests/test_admin_ui_conventions_overrides_section.py`. Kein Push, kein Tag, kein Branch-Management, kein Merge.
**Interfaces:** Consumes: Task-4-Protokoll (grün), Task-5-Audit (0 Abweichungen). Produces: 1 lokaler Commit auf `fix/decision-points-bundle-20261123`.

- [ ] Step 1: Caller/Orchestrator führt den Secret-Scan gegen die zwei gemeldeten Dateien aus; bei Fund Block und manuelle Intervention, kein Commit.
- [ ] Step 2: Commit mit vorbereiteter Nachricht anwenden (Subject beginnt auf Byte 0 mit `feat:`, kein BOM, keine Closing-Keywords):
  ```
  feat: expose issue language in admin UI, mark inert fields doc-only
  ```
- [ ] Step 3: Verifikation: genau 1 Commit, genau 2 Dateien im Scope, 0 Remote-Operationen.

**Akzeptanzkriterium (messbar):** `1` Commit mit den `2` genannten Dateien und der obigen Subject-Zeile; `0` Pushes, `0` Tags, `0` Closing-Keywords.

---

## AC-Abdeckung

| AC | Gefordertes Ergebnis | Tasks | Nachweis |
|---|---|---|---|
| AC-01 | `language` in Overrides-View und Preset-Editor editierbar → `deutsch` → `ISSUE_LANGUAGE` | 2, 3, 4 | Tests (a)/(b); `DOMAIN_FIELDS`-Zeile + `scalarField`; `test_issue_language.py:33-38` grün |
| AC-02 | 4 Inert-Felder mit `documentation only` + `.badge.muted`, kein grünes `ok`, Werte editierbar | 2, 3 | Tests (c)/(d); `docOnly: true` + `badgeClass`-Ausdruck; `setPath`/`delPath` unverändert |
| AC-03 | Intro nennt `git.md`-Hilfetext + `language` wirksam; kein #1188-Link | 2, 3, 5 | Test (e); Intro-Text `:4181-4183`; Audit Schritt 2 |
| AC-04 | Jedes angebotene Feld hat Consumer oder `docOnly`; neues Feld ohne beides lässt Test failen | 2, 3 | Test (f) über `DOMAIN_FIELDS.issues`-Labels; `docOnly`-Marker |
| AC-05 | `--validate` + alle Testsuiten grün; 5 Nie-Ziel-Dateien byte-identisch | 1, 2, 4, 5 | Task-4-Protokoll; `git diff --exit-code` über die 5 Dateien |

## Self-Review

- Jeder Task mappt auf genau eine bestehende Rolle: `explorer`, `tester`, `developer`, `tester`, `validator`, `git`; keine Re-Delegation an `orchestrator`.
- Jedes Akzeptanzkriterium ist messbar (Exit-Codes, Testzahlen, Datei-Anzahlen, `git diff --exit-code`), kein „works correctly".
- `Files:`/`Interfaces:` vollständig; Schreibownership überschneidet sich nicht: Task 2 nur Testdatei, Task 3 nur `admin-ui.html`, Tasks 1/4/5 read-only, Task 6 commit-scope nur diese zwei Dateien.
- `pipeline_stages: implement: 3` deckt die `implement`-Stage ab — Task 3 ist die Implementierung; Red läuft in Task 2, Regression in Task 4.
- AC-01..AC-05 sind je mindestens einem Task und einem IC zugeordnet; IC-4/IC-5 bleiben read-only und sind über AC-05 abgedeckt.
- Keine Platzhalter, keine TBDs, keine geschätzten Zeilennummern ohne Anker; Badge-Klassen-Widerspruch (IC-3 vs. CSS) ist mit konkreter Regel + Fallback aufgelöst.
- D-1204-A/B/C und R-1 sind als bindende Entscheidungen mit Default dokumentiert; keine #1188-Semantik, kein toter Link, keine Closing-Keywords.
- Referenz auf `effort-estimator` (textuell, kein Tool-Aufruf): Aufwand M / bounded — 1 Produktivdatei mit 5 lokalen Änderungspunkten + 1 neue statische Testdatei + 2 Verifikations-/Audit-Pässe; keine Schema-, API-, Persistenz- oder #1188-Code-Arbeit.
