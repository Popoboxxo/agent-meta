---
review-id: RVW-DOCS-CONSOLIDATION-R2
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
plan-id: PLAN-DOCS-CONSOLIDATION-2026-09-25
subject-revision: 0.7
round: 2
reviewer: concept-reviewer
date: 2026-09-27
verdict: CHANGES_REQUESTED
---

# Concept-Review Runde 2 — Spec + Plan Rev. 0.7 (Korrekturrunde 5, K59…K70)

> **Verdikt: `CHANGES_REQUESTED`** — 0 kritisch · **1 major (neu, aus der Korrekturrunde)** ·
> 4 minor (davon 3 neu) · 1 info. **Kein** Blocker, **kein** `BLOCKED`.
> **Runde 1** (`CHANGES_REQUESTED`: 5 major, 4 minor, 2 info) ist **inhaltlich vollständig
> abgearbeitet**: alle **11** Findings `RVW-7-01`…`RVW-7-11` und alle **5** Validator-Notizen sind
> entweder **behoben** oder **begründet nicht zugeordnet**. **Beide Autor-Korrekturen sind belegt**
> (7 statt 6 V4-Tests, 193 statt 191). Der Commit ist **blockiert durch genau einen neuen,
> mechanisch behebbaren Widerspruch** (Ownership-Matrix) plus zwei Beleg-Präzisierungen.

**Scope.** Geprüft wurden `docs/specs/2026-09-25-repository-documentation-consolidation.md` und
`docs/plans/2026-09-25-repository-documentation-consolidation.md` (beide Rev. 0.7, **kein**
Revisions-Bump), gegen den Working Tree (HEAD `c0988e1`, Branch
`feat/repository-documentation-consolidation-main`) — **read-only**: keine Edits an den geprüften
Dokumenten, keine Git-Mutation, kein `sync.py`, die 3 uncommitteten W2-6-Dateien unberührt.
Prüfmodus: **Spec-Review (§7.1)**. Pflichtsektionen, Trace-Anker (`spec-id` in beiden Frontmattern,
`spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25`) und Approval-Marker (`status: APPROVED`,
`approved: 2026-09-26`) sind **vorhanden und konsistent**; Platzhalter in Pflichtsektionen: keine.
Die 4 offenen Entscheidungsvorlagen **E-1…E-4** bleiben korrekt **offen** (keine Unterstellung).

**Methode.** Alle Belege stammen aus Grep/Read im Working Tree. Read-Zeilennummern wurden nur
verwendet, wo sie durch Grep/Treffer gedeckt sind; Zeilenangaben der Dokumente wurden durch
direktes Gegenlesen der Zielzeilen geprüft.

---

## 1. Status je Finding

| ID | Sev (R1) | behoben? | Beleg (verifiziert) | Rest |
|---|---|---|---|---|
| **RVW-7-01** | major | **ja** | `docs_links.py:167` = `def check_readme_docs_index(root: Path) -> list[Finding]:` — **einargumentig** ✓; Docstring `:170-172` enthält „the parameter list stays ``(root)``" ✓; Aufrufer `consistency-check.py:201` übergibt **eine** Position ✓; Testpin `tests/test_doc_index.py:276-277` (`inspect.signature(...) == ["root"]`) ✓; Spec-IC-05 `:948-954` fixiert die gemessene Form und weist `(root, config=None)` ausdrücklich den **neun neuen** Checks zu (`:955`) ✓; Plan-Kopf K54, W-GATE-TABLE `:2153`, W2-6 `:2903-2905`, W2-8 (b) `:3059` ✓ | Anker falsch, s. **NEU-3** |
| **RVW-7-02** | major | **ja** | 14 eindeutige `](docs/…)`-Ziele in `README.md` **nachgezählt** = **12 `.md` + 2 `.html`** (`docs/ui/agent-graph.html:369`, `docs/ui/admin-ui.html:370`) ⇒ `205 − 12 = 193` ✓; Register §17.11.3 `:3475` trägt Herleitung + **Shell-Zählaufruf**; `docs.readme_index` ist als Nachweis **ausdrücklich für unbrauchbar** erklärt, mit Abgrenzung zum Kategorie-Eintrag `:3476` ✓; 205 ist als **übernommene Baseline, nicht neu gemessen** markiert (Plan `:6236-6240`) — methodisch sauber | Rest-`191` (Spec-Frontmatter `:6`, Spec-E-5 `:3346`, Plan-E-5-Records) ist durch die **Lesart-Regel** (Plan `:323-330`) **explizit** gedeckt, inkl. Nennung der `approved-scope`-Zeile ⇒ kein Befund. Siehe **INFO-1** |
| **RVW-7-03** | major | **ja** | Die **7** Tests sind unabhängig hergeleitet und **deckungsgleich** mit der Tabelle R1…R7 (Plan `:2940-2948`): 4 rot (`test_v4_ignores_archived_pages:316`, `test_v4_reports_each_page_once:332`, `test_v4_finding_names_the_page_and_readme:347`, `test_real_repo_pages_are_reported_only_by_v2_until_w3_6:394`) + 3 vakuum-grün (`test_v4_keeps_signature_and_severity:269`, `test_v4_generalized_to_the_whole_docs_tree:287`, `test_v4_api_subset_still_fires:301`). `test_v4_absent_docs_tree_is_fail_soft:325` bleibt zu Recht bestehen (fail-soft gilt nach E-5 unverändert). Nicht-Vakuum-Nachweis (K33) in Akzeptanz + Schritt 3 ✓ | Überdehnung im Begründungssatz, s. **NEU-4** |
| **RVW-7-04** | major | **ja (Inhalt)** | Alle Code-Fakten bestätigt: `spec_plan.py:55` (`_TASK_HEADER_RE = TASK_HEADER_RE`), `:557` (`finditer`), `:570` hart kodiert `re.findall(r"task-\d+|\d+", …)`, `:533` (`check_plan_file_overlap`); `orchestration.py:207-216` meldet `deadlock: … unknown task_id`, `:287-289` kehrt **vor** dem Overlap-Check ab (`:299-304`) ⇒ Kettenwirkung exakt wie beschrieben. W2-9 `Files:` `:2655-2659`, `Interfaces` `:2675-2683`, Akzeptanz (e) `:2715-2722`, (f) `:2723-2725`, Schritt 2 `:2746`, `ruff`-Zeile `:2729-2730` ✓; verworfene Alternative begründet `:2684-2689` ✓ | **NEU-1 (major)**: die abgeleiteten Schreibmengen-Inventare sind nicht mitgezogen |
| **RVW-7-05** | major | **ja** | (ii) **gestrichen** mit drei gemessenen Belegen (W2-8 (b) `:3055-3062`): Common-Gate erst W2-7, V4 nimmt kein `config` (`docs_links.py:167`), `--root` leitet die Altchecks nicht um (`consistency-check.py:199-201` gegen `:257`) — alle drei **verifiziert** ✓; (iii) mit **festgeschriebenem Werkzeug** `consistency-check.py --json --root <Fixture>` (`:3043-3048`), `--json` dem **Runner** zugeordnet (`:244-247`), `sync.py`-Flags geprüft (nur `--validate`, `--validate-se`, `--validate-spec-plan`), **Grenze** benannt: (iii) nur in der Form „nur die Dateien des Tests" (`:3049-3054`) ✓; (i) bleibt der erste Weg (`:3039-3042`) ✓ | keine |
| **RVW-7-06** | minor | **ja** | Extraktionsregel **wortgleich** in W2-6 `Interfaces` `:2909-2911`; 7/6-Lesart entschieden; Beleg `docs/architecture/` nur im Link `README.md:371` **nachgezählt**: `###`-Überschriften der Region `:347-381` sind `guides/`,`howto/`,`api/`,`ui/`,`plans/`,`se-cascade/` = **6** (`:351,357,360,368,375,378`) ⇒ **7** nur mit dem Link `:371` ✓; beide Lesarten ⇒ Sollwert **1** (nur `se-cascade/` ohne Link) — **unabhängig bestätigt** ✓ | keine |
| **RVW-7-07** | minor | **ja** | `docs_links.py:183` behandelt `not readme.exists() or not docs_dir.is_dir()` **gemeinsam** ⇒ `[]` — **wörtlich bestätigt**; Vorrangregel (fail-soft zuerst, dann fail-closed) in W2-6 `:2918-2924` und Spec `:3400-3409` **wortgleich**; **zwei neue Tests** benannt (`:2954-2957`) ✓ | keine |
| **RVW-7-08** | minor | **ja (Sachstand)** | Verhalten **korrekt gemessen**: `plan_identity.py:69-73` ⇒ `re.fullmatch(r"[0-9]+","W2-0")` → nein, `TASK_ID_RE` (`:18`) → nein, `return raw` ⇒ `"W2-0"` ✓. (b) zurückgenommen, W2-9 auf (a) beschränkt, Reparatur als round-trip-brechend **verboten** (`:2670-2674`), No-op-Pin (f) `:2723-2725` ✓ | Falscher Beleg, s. **NEU-2** |
| **RVW-7-09** | minor | **ja** | `W-VALIDATE-ROT`: **alle vier** Zeitraumzeilen tragen V4 (`:2267`, `:2268`, `:2269`, `:2270`) inkl. Owner-Spalte; Registrierung belegt (`consistency-check.py:53` Import, `:201` Aufruf — **beide verifiziert**) ✓; Spec §10 `:2258-2261` und Spec-Kopf `:98-100` ✓; Working-Tree-Ursache der 2 roten Volltests in L-1 W2-6 (`:5417`) ✓ | Anker `:2235` falsch, s. **NEU-3** |
| **RVW-7-10** | info | **ja** | Docstrings `docs_links.py:8-10` und `:168-177` nennen den Vor-E-5-Scope — **wörtlich bestätigt** (`:172-177` „Only the **scope** widened — from ``docs/api/*.md`` … to the whole ``docs/`` tree“ / „The pre-W2 subset stays a real subset“). Als **Pflicht in W2-6** festgeschrieben (`:2982-2988`, Schritt 2 `:3003`) ✓; kein Code-Edit in dieser Runde ✓ | keine |
| **RVW-7-11** | info | **ja (bewusst)** | Korrekturrunde 4 bleibt wortgleich; Vorrang global über Legende `:421`, Rev.-0.7-Block und „Entscheidungs-Abschluss Rev. 0.7" (Muster K36/K42) — regelkonform begründet (`:385-391`, `:6219`) ✓ | keine |
| **n1** | — | **begründet** | K6 kommt als Bereichsangabe „Ausführungskorrekturen K1–K6" im Rev.-0.2-Block vor (Plan `:852`); Nicht-Zuordnung mit Muster K36/K42 begründet (`:6225`) — trägt | keine |
| **n2** | — | **behoben** | Spec §16 `:2701`: „W0…W8 lückenlos — das heißt: alle **neun Wellen** … **keine** Aussage über Task-IDs innerhalb einer Welle (gemessen: **W0 hat 6 Tasks** — W0-1, W0-2, W0-3, W0-4, W0-6, W0-7 — und **`W0-5` existiert nicht**)". **Unabhängig bestätigt:** die Task-Liste des Plans enthält genau diese 6 W0-Tasks, **kein** W0-5 ✓; keine W-ID geändert, kein W0-5 erfunden ✓ | Anker `:2674` zeigt jetzt auf eine andere Tabellenzeile (kosmetisch) |
| **n3** | — | **bestätigt** | bewusste Spec/Plan-Spiegelung, nicht entspiegelt (`:6227`) — trägt | keine |
| **n4** | — | **bestätigt** | hypothetischer F-Name bleibt als hypothetisch gekennzeichnet (`:6228`) — trägt | keine |
| **n5** | — | **begründet** | Plan-Legende `:421` (OQ1, OQ3, OQ4, OQ9, OQ10) ist maßgeblich; Rev.-0.6-Liste `:168` ist ein datierter Stand; kosmetisch (`:6229`) — trägt | siehe **BEOB-1** (außerhalb des Korrekturumfangs) |

**Ergebnis: 0 Findings offen.** Alle 11 Findings sind inhaltlich erledigt oder begründet; alle
5 Notizen sind zugeordnet.

---

## 2. Verifikation der zwei Autor-Korrekturen

### (i) Sind es **7** V4-Tests? — **Ja. Die Korrektur ist richtig.**

Gemessen in `tests/test_doc_index.py` (uncommittet, von der Runde nicht angefasst):

| # | Test | Zeile | Zustand **heute** | Unter E-5 (fail-closed) | Plan-R1…R7 |
|---|---|---|---|---|---|
| 1 | `test_v4_keeps_signature_and_severity` | 269 | grün | **1** Finding (Überschrift) ⇒ (check, severity) stimmt ⇒ **grün, aber aus dem falschen Grund** | R1 ✓ |
| 2 | `test_v4_generalized_to_the_whole_docs_tree` | 287 | grün | **1** Finding, `file == README.md` ⇒ **grün, falscher Grund** | R2 ✓ |
| 3 | `test_v4_api_subset_still_fires` | 301 | grün | **1** Finding ⇒ **grün, falscher Grund** | R3 ✓ |
| 4 | `test_v4_ignores_archived_pages` | 316 | grün | **1** Finding ≠ `[]` ⇒ **rot** | R4 ✓ |
| 5 | `test_v4_reports_each_page_once` | 332 | grün | 1 statt 2 ⇒ **rot** | R5 ✓ |
| 6 | `test_v4_finding_names_the_page_and_readme` | 347 | grün | Message nennt die Kategorie, nicht `docs/guides/orphan.md` ⇒ **rot** | R6 ✓ |
| 7 | `test_real_repo_pages_are_reported_only_by_v2_until_w3_6` | 394 | grün | echter Baum: 1 Finding, `message.split("'")[1]` liefert `docs/se-cascade/`, das **im README steht** ⇒ **rot** | R7 ✓ |

⇒ **4 rot + 3 vakuum-grün = 7**, deckungsgleich mit der Autortabelle. `test_v4_absent_docs_tree_is_fail_soft`
(:325) bleibt gültig (kein `docs/`-Baum ⇒ fail-soft `[]`) und wird korrekt **nicht** in die 7
gezählt, sondern **erweitert**. **Kein** sechster/achter Test trägt die Per-Seiten-Semantik.
⇒ **Autor-Korrektur 1 bestätigt.**

### (ii) Ist es **193**? — **Ja. Die Korrektur ist richtig.**

Eigenzählung der `](docs/…)`-Linkziele im **gesamten** `README.md`:

`guides/setup/instantiate-project.md` (:309/:354) · `architecture/01-layer-model.md` (:309/:371) ·
`guides/mcp-onboarding-checklist.md` (:355) · `howto/admin-ui-remote-access.md` (:358) ·
`api/cli-reference.md` (:362) · `api/slash-commands.md` (:363) · `api/composition-system.md` (:364) ·
`api/pal-variables.md` (:365) · `api/admin-ui-reference.md` (:366) · `api/viz-api.md` (:372) ·
`api/viz-event-schema.md` (:373) · `plans/hacs-platform-preset-audit.md` (:376)
= **12 `.md`**; dazu `ui/agent-graph.html` (:369) + `ui/admin-ui.html` (:370) = **2 `.html`**.

**14 Ziele = 12 `.md` + 2 `.html`.** Der 205er-Bestand ist `.md`-only ⇒ **`205 − 12 = 193`** ✓.
`191` (= `205 − 14`) war der Einheitenfehler, den Runde 1 benannt hat. Ebenfalls bestätigt: die in
der Index-Region `:347-381` verlinkten Seiten sind **dieselben 12** (keine `.md` nur in der Region) —
die Lesart-B-Rechnung in §17.11.2 (`:3413-3415`) war also schon korrekt.
⇒ **Autor-Korrektur 2 bestätigt.** Der Beleg `205` selbst ist als **übernommene Baseline**
gekennzeichnet und in dieser Runde **nicht** neu gemessen (Plan `:6236-6240`) — das ist die
korrekte Offenlegung; der einmal-Zählaufruf aus §17.11.3 macht die Zahl in einer Zeile prüfbar.

---

## 3. Neue Widersprüche durch die Korrekturrunde

### NEU-1 · major · K62 vs. Ownership-Matrix: `spec_plan.py` fehlt in allen abgeleiteten Write-Set-Inventaren

K62 hat `scripts/lib/consistency/spec_plan.py` **korrekt** in W2-9s `Files:` aufgenommen
(Plan `:2655-2659`) — aber **keine** der daraus abgeleiteten und im Plan **selbst als maßgeblich
bezeichneten** Stellen mitgezogen:

| Stelle | Behauptung | Ist |
|---|---|---|
| Ownership-Matrix (`:4579-4602`), W2-9-Spalte | **4** `owns`-Zeilen: `plan_identity.py`, `plan_ledger.py`, `test_plan_identity.py`, `test_plan_ledger_writer.py` | **keine** Zeile für `spec_plan.py` |
| Matrix-Narrativ `:4613` | „W2-9 analog für die **vier** Werkzeug-/Testdateien" | **fünf** |
| Matrix-Narrativ `:4650` | „das gilt für die **sechs** neuen Dateien von W2-8/W2-9" | **sieben** |
| Matrix-Kopf `:4575` | „**9 Dateizeilen** erweitert" | **8** Zeilen tatsächlich neu — nach dem Ergänzen der `spec_plan.py`-Zeile wäre es 9 (die Lücke ist mit hoher Wahrscheinlichkeit genau diese) |
| Step-Agent-Map W2-9 (`:4505`) | 4 Dateien | **5** |
| `File Structure` (`:1245-1249`) | `plan_identity.py`, `plan_ledger.py` | ohne `spec_plan.py` |
| Rollback W2 (`:2386-2388`) | 3 `git checkout`-Zeilen | ohne `spec_plan.py` |
| DoD-/Ownership-Summenlisten (`:4984-4985`, `:5024-5027`, `:5121-5122`) | 4 Dateien | **5** |

Die Liste „Betroffene Stellen der Korrekturrunde 5" (`:401-406`) nennt **weder** die
Ownership-Matrix **noch** die Step-Agent-Map — es ist also **keine** dokumentierte bewusste
Ausnahme (anders als die `191`-Lesart-Regel, die ihre Reststellen ausdrücklich benennt).
Damit widerspricht der Plan sich selbst: die Task-Zeile sagt „5 Dateien", das als
**maßgeblich** bezeichnete Instrument (`:4541`) „4". K62 selbst beruft die Ownership-Klausel als
**fail-closed** (`:342`) — ein nicht registriertes Write-Set ist genau die Konstellation, die die
Fail-closed-Klausel (`:4718-4728`) und die Regel „höchstens eine schreibende Task pro Datei pro
Parallelgruppe" (`:4642`) ausschließen soll. **Keine Kollision mit einer anderen Task entsteht**
(kein weiterer Task führt `spec_plan.py` — geprüft), der Mangel ist rein die
Vollständigkeit/Deckungsgleichheit der Inventare.

**Verbesserung:** eine Zeile `scripts/lib/consistency/spec_plan.py | … | **owns** (Modify, Dep-Token-Muster, K62)`
in die Ownership-Matrix; `:4613` „vier" → „**fünf**", `:4650` „sechs" → „**sieben**"; eine
Dateiangabe in Step-Agent-Map `:4505`, `File Structure`, Rollback und den drei Summenlisten;
Matrix-Kopf auf „9 Dateizeilen" belassen (dann stimmig) und die Stelle in „Betroffene Stellen"
aufnehmen.

### NEU-2 · minor · K66: die Behauptung „gepinnt in `tests/test_plan_identity.py:96-101`" ist unbelegt

`tests/test_plan_identity.py:96-101` ist `test_normalize_task_id` mit den Asserts
`"3"→"task-3"`, `"TASK-3"→"task-3"`, `"task-3"→"task-3"`, **`"custom"→"custom"`**,
`"task-"→"task-"`. **Ein Assert auf `"W2-0"` existiert dort nicht.** Der **Sachstand** ist
richtig (Durchreich-Zweig ⇒ `"W2-0"`, per Code gelesen bestätigt), und der `W2-0`-Pin wird in
W2-9 Akzeptanz (f) **neu angelegt** — es geht also kein Schutz verloren. Falsch ist nur die
**Evidenzbehauptung**, die 5× wiederholt wird (Plan `:247`, `:372`, `:2670`, `:6216`; Spec
`:3554` „gepinnt“), obwohl die Runde ausdrücklich behauptet, **alle** Belege seien vor dem Edit
verifiziert worden.
**Verbesserung:** auf den realen Anker umstellen — „verhaltensgleich abgedeckt durch
`normalize_task_id("custom") == "custom"` (`:100`), derselbe Durchreich-Zweig; der `W2-0`-Pin
wird in Akzeptanz (f) **neu** angelegt" — und die Formulierung „gepinnt“ in beiden Dokumenten
ersetzen.

### NEU-3 · minor · drei falsche `Datei:Zeile`-Anker in den neuen K-Zeilen

| Angabe | Richtige Stelle (geprüft) |
|---|---|
| „IC-05 selbst (`:930-933`)“ (Plan `:304-306`, `:6209`; Spec `:3547`) | IC-05 liegt bei **`:944-954`**; `:930-933` ist ein Codeblock in **IC-04** (`compute_active_roles`) |
| „Revisionszeile `0.7` (`:367`)“ (Plan `:6209`) | Revisionszeile **0.7** liegt bei **`:383`**; `:367` ist die Zeile „VERIFIED“ der Verifikations-Legende |
| „Spec §10 `--validate` (`:2235`)“ (Plan `:6217`) | §10-Bullet liegt bei **`:2257-2261`**; `:2235` steht in §9.2 (Merge-Regel) |

Die **Aussagen** sind jeweils richtig (IC-05 trägt kein Signatur-Literal — dort steht jetzt
„jeweils `(root: Path) -> list[Finding]`, einargumentig“; die Revisionszeile 0.7 nennt K59; §10
trägt den V4-Zusatz). Falsch sind nur die Anker. Das ist relevant, weil die Runde ihre
Belegqualität ausdrücklich über `Datei:Zeile`-Zitate begründet und die Spec selbst in §16
verlangt, „jeder `Datei:Zeile`-Verweis wurde gelesen“.
**Verbesserung:** die drei Anker auf `:944-954`, `:383`, `:2257-2261` korrigieren (in **beiden**
Dokumenten konsistent).

### NEU-4 · minor · K61: überdehnter Begründungssatz „alle sieben Fixtures“

Plan `:2950-2951`: „**alle** Fixtures dieser sieben Tests schreiben `README_RELPATH, "# readme\n"`“.
R7 (`test_real_repo_pages_are_reported_only_by_v2_until_w3_6`, `:394`) hat **kein** Fixture, sondern
liest den **echten** Baum (`REPO_ROOT`) samt `## 📖 Documentation Index`-Überschrift. Die
Klassifikation „rot“ bleibt korrekt (aus dem in R7 selbst genannten Grund), nur die Begründung
greift für 6 statt 7 Tests. Auch Spec `:3549` wiederholt „alle Fixtures“ im Befund-Satz.
**Verbesserung:** auf „die **sechs** Test-Fixtures“ präzisieren und R7 gesondert begründen
(er liest den echten Baum; rot wegen `message.split("'")[1]` auf einer Message, die nach E-5 die
Kategorie nennt — dieselbe Message-Form, die der Plan in R7 ohnehin nennt).

### INFO-1 · info · K60: der once-count wird nach W3-6 eine andere Zahl liefern

Der Nachweisaufruf (Spec `:3475`, Plan `:320-322`) enthält `-not -name 'INDEX.md'`. Heute ist das
folgenlos — **`docs/INDEX.md` existiert nicht** (geprüft) —, also Universe = 205, Baseline **193**
✓. Ab W3-6 erzeugt der Generator diese Datei; dann lautet derselbe Aufruf **192** (Universe 204,
davon 12 verlinkt), während die Baseline im Register **193** bleibt. Die Exclusion ist **gewollt**
(V2-Konvention, IC-05 V2-Zeile `ohne docs/INDEX.md selbst`), nur der Bezugszeitpunkt der Zahl
fehlt.
**Verbesserung (optional, nicht blockierend):** eine Halbsatz-Begrenzung im Registereintrag
(„Baseline 193 **vor** W3-6; ab W3-6 ist derselbe Aufruf 192, weil `docs/INDEX.md` dann existiert
und per V2-Konvention ausgenommen ist").

---

## 4. Zähl-Konsistenz (neu gemessen)

| Größe | Erwartung | Gemessen | Urteil |
|---|---|---|---|
| Tasks | 50 | `^### W[0-9]-[0-9]+:` ⇒ **50** | ✓ |
| davon W2 | 10 | **10** (W2-0…W2-9) | ✓ |
| davon W0 | 6, **kein** W0-5 | **6** (W0-1,2,3,4,6,7) | ✓ |
| Checkboxen `[x]` | 59 | **59** | ✓ |
| Checkboxen `[ ]` | 148 (= 207 − 59) | Gesamt nicht direkt zählbar (Tool-Grenze); Herleitung `44 × 4 + 5 × 5 + 1 × 6 = 207` **arithmetisch korrekt**, `207 − 59 = 148` | ✓ (rechnerisch konsistent) |
| Checkboxen gesamt | 207, in dieser Runde **keine** geändert | Rev-0.7-Stand, unverändert behauptet und mit 59 gemessenen `[x]` stützend belegt | ✓ |
| K-Katalog-Obergrenze | K1…K70 | **K70** (Rev. 0.7 = K54…K58, Runde 5 = K59…K70), konsistent in Plan `:284`, `:296`, `:402`, `:421`, `:6250`, `:6262`; Spec-Legende eingefroren `K1…K45` (K42) | ✓ (**Abweichung von der Erwartung „K69“ in Runde 2: der Autor hat K70 für n1…n5 angelegt — das ist die saubere Lösung, keine Lücke**) |
| F-IDs | keine neue in Runde 5 | `F-DOCS-README-INDEX-2026-09-27` + `…-SE-…` stammen aus Rev. 0.7 (K55); Runde 5 änderte nur die **Zahl** im Bestand | ✓ |
| Task-/W-/AC-/IC-/R-/OQ-/V-IDs | unverändert | 50 Task-IDs unverändert, keine Umnummerierung; `revision: 0.7`, `status: APPROVED` unverändert | ✓ |
| K-Katalog: jede Kennung genau einmal belegt (Muster K41) | — | K59, K60, K61, K62, K63, K64, K65, K66, K67, K68, K69, K70 — **12 Einträge, lückenlos, ohne Doppelung** | ✓ |
| Vorrangregel K65 vs. `docs_links.py:183` | Fail-soft vor fail-closed | W2-6 `:2918-2924` und Spec `:3400-3409` **wortgleich** | ✓ |
| Negativnachweis gegen die alte Lesart | vorhanden | W2-6 `:2964-2967` (zwei unlinkte Seiten unter deklarierter Kategorie ⇒ **kein** Finding) | ✓ |
| Modul-/Zeilenzahlen | `docs_index.py` < 600, `docs_links.py` < 600 | Plan `:2994-2996` nennt 211 bzw. 404 (Working Tree) | ✓ plausibel |

---

## 5. Beobachtungen außerhalb des Korrekturumfangs (keine Findings)

* **BEOB-1:** Spec §16, Zeile „IDs“ (`:2701`) nennt `OQ1…OQ9` mit OQ5/OQ7 geschlossen, obwohl die
  Spec seit Rev. 0.6 **OQ10** führt (`OQ1…OQ10` im Plan-Kopf, Legende, §11.1). **Vorbestehend**
  (Rev. 0.6, nicht Runde 5) und von n5 nicht erfasst; dieselbe Zelle wurde für n2 editiert.
  Nur als Hinweis zur Gelegenheitskorrektur, **kein** Finding dieser Runde.
* **BEOB-2:** Matrix-Kopf `:4575` sagt „9 Dateizeilen“, gezählt sind 8 (vgl. NEU-1). Führte zur
  Klärung von NEU-1; nicht separat als Finding geführt, da dieselbe Stelle betroffen ist.
* **BEOB-3:** Das Design-Doc (`…-design.md:334`, `:374`) nennt „191+ Dateien“ bzw. „191 `docs/*.md`“.
  „191+“ bleibt für 193 formal richtig; die Risk-Zeile ist ein **Datumsstand vom 2026-09-25** und
  nicht Teil der Rev. 0.7-Korrektur. Nur zur Kenntnis.
* **BEOB-4:** `knowledge/sources/README.md` enthält eine **Kopie** des README-Standes (Zeilen
  306/351/…); sie stimmt nicht exakt mit `README.md` (Zeilenversatz 1–9). Für die 14er-Zählung des
  Plans ist ausschließlich `README.md` maßgeblich — kein Einwand gegen K60, aber eine Falle für
  jede künftige Nachzählung.
* **BEOB-5:** Zitierte Working-Tree-Zeilen (`docs_links.py:167/:183`, `docs_index.py` 211 Z,
  `test_doc_index.py` 413 Z) beziehen sich auf **uncommittete** Dateien; sie verschieben sich, sobald
  W2-6 (Docstring-Neuschreibung, K68) landet. Der Plan kennzeichnet die Dateien als uncommittet
  (`:5417`) — damit ist die Flüchtigkeit der Zeilenanker offengelegt, nicht verdeckt.

---

## 6. Verdict

### `CHANGES_REQUESTED`

**Begründung.** Alle **11** Findings und **5** Validator-Notizen aus Runde 1 sind am Text bzw. am
Code verifiziert erledigt; **beide** Autor-Korrekturen (7 statt 6 V4-Tests, 193 statt 191) sind
**belegt** — die Herleitung `205 − 12 = 193` habe ich durch eigenes Nachzählen der 14 README-Linkziele
(12 `.md` + 2 `.html`) bestätigt, ebenso die 4 rot / 3 vakuum-grün und die Namen R1…R7. Die
Zähl-Konsistenz (50 Tasks, 10 in W2, 59 `[x]`, 207 = 44×4+5×5+1×6, K1…K70, keine neue F-ID) ist
gegeben. **Ein** neuer Widerspruch aus dieser Korrekturrunde ist aber **blockierend**: K62 hat
`spec_plan.py` in W2-9s `Files:` aufgenommen, ohne die abgeleiteten und im Plan selbst als
**maßgeblich** bezeichneten Write-Set-Inventare mitzuziehen (Ownership-Matrix, Step-Agent-Map,
`File Structure`, Rollback, DoD-/Ownership-Summenlisten) — der Plan widerspricht sich damit über
die Schreibmenge einer Task, die er selbst zur fail-closed-Eigenschaft erklärt (**NEU-1**). Dazu
kommt eine unbelegte Evidenzbehauptung (**NEU-2**, K66) und drei falsche `Datei:Zeile`-Anker in den
neuen K-Zeilen (**NEU-3**) — beides nicht substanziell, aber die Runde beruht ausdrücklich auf
„Belegen statt Behauptungen“.

**Mindestens nötig vor dem Commit (alles mechanisch, keine erneute Sachprüfung):**

1. **NEU-1** — `scripts/lib/consistency/spec_plan.py` als `owns`-Zeile in die Ownership-Matrix
   aufnehmen; `:4613` „vier“ → „fünf“, `:4650` „sechs“ → „sieben“; eine Dateiangabe in
   Step-Agent-Map, `File Structure`, Rollback und den drei Summenlisten; Stelle in „Betroffene
   Stellen der Korrekturrunde 5“ nachtragen.
2. **NEU-2** — die Aussage „gepinnt in `tests/test_plan_identity.py:96-101`“ durch den realen
   Anker ersetzen (`:100`, `normalize_task_id("custom") == "custom"`, derselbe Zweig) und
   „gepinnt“ in Plan (4 Stellen) und Spec (1 Stelle) neutralisieren.
3. **NEU-3** — Anker korrigieren: IC-05 `:944-954` (nicht `:930-933`), Revisionszeile 0.7 `:383`
   (nicht `:367`), §10 `--validate` `:2257-2261` (nicht `:2235`).
4. **NEU-4** (empfohlen) — „alle sieben Fixtures“ → „die sechs Test-Fixtures“; R7 gesondert
   begründen.
5. **INFO-1** (optional) — Bezugszeitpunkt der Baseline 193 im Registereintrag begrenzen
   (vor W3-6; danach liefert derselbe Aufruf 192).

Danach ist der Plan **freigabefähig**; der Sachstand der Welle W2, die Gate-Logik und die
Nachweisformen sind tragfähig. **Kein** Revisions-Bump nötig (rein additive Präzisierungen in
Rev. 0.7, Muster Korrekturrunde Rev. 0.6 Runde 1), **kein** `BLOCKED`.
