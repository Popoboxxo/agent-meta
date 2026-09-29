---
review-id: RVW-DOCS-CONSOLIDATION-R9
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
plan-id: PLAN-DOCS-CONSOLIDATION-2026-09-25
subject: docs/specs/2026-09-25-repository-documentation-consolidation.md
subject-revision: 0.8
round: 9
reviewer: concept-reviewer
date: 2026-09-29
verdict: CHANGES_REQUESTED
---

# Concept-Review Runde 9 — Verifikation der Korrekturrunde K61…K70 (Spec Rev. 0.8)

> **Verdikt: `CHANGES_REQUESTED`** — 0 kritisch · **2 major** · 7 minor · 1 info.
> **Alle 10 Findings aus Runde 8 (RVW8-1…RVW8-10) sind inhaltlich behoben** und am Working Tree
> belegt — kein Finding wurde nur wegen eines existierenden Katalog-Eintrags als behoben akzeptiert.
> Die Korrekturrunde hat jedoch **zwei neue Fehler eingeschleppt**: eine **K-ID-Kollision mit
> zehn** bereits belegten Korrektur-Kennungen (RVW9-1) und eine **unregistrierte Plan-Divergenz**,
> die die in §17.12.4 festgeschriebene W3-6-Akzeptanz unerfüllbar macht (RVW9-2).

**Scope.** Geprüft wurde `docs/specs/2026-09-25-repository-documentation-consolidation.md`
Rev. 0.8 (korrigierte Fassung, `revision: 0.8`, `status: APPROVED`, `pending-approval:`) gegen
den Working Tree, read-only, gegen `docs/specs/2026-09-29-…-rereview-8.md` (RVW8-1…RVW8-10) und
`docs/specs/2026-09-25-…-design-agent-meta-exception.md`. **Keine** Datei des geprüften Dokuments
wurde geändert, keine Git-Mutation, kein `sync.py`, kein Testlauf. Prüfmodus: **Spec-Review (§7.1)**
+ **Verifikation einer Korrekturrunde**. Nur dieses Review-Artefakt wurde geschrieben.

**Werkzeug-Vorbehalt (Prüfpunkt 6) — bestätigt und selbst reproduziert.**
`tests/test_docs_consolidation_migration.py:42-44` und `tests/test_doc_renderer.py:1090-1091`
rendert das Read-Tool leer; im Lauf dieser Runde kam `:1090-1091` **tatsächlich leer** zurück,
während `:1092-1098` (derselbe Block!) lesbar war. **Alle** Belege in diesem Report stammen daher
aus dem **Grep-Tool** (liefert `file:line` + Zeileninhalt) bzw. aus Read **außerhalb** dieser
Zonen. Wo Read genutzt wurde, ist das explizit vermerkt.

**§7.1-Checks (alle grün):**

| Check | Ergebnis |
|---|---|
| Pflichtsektionen | vorhanden (§2 Problem/Ziel/Nicht-Ziele, §5 Interface Contracts, §6 Datenfluss, §7 AC, §11 offene Fragen, §12 Risiken, §17.12 Nachweis/Testakzeptanz) |
| Trace-Anker | `spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25` in Frontmatter `:2` **und** §15 `:3092`; Rev.-0.8-Block `:3134-3165` |
| Approval-Marker | `status: APPROVED` + `approved: 2026-09-26`; Rev. 0.8 **konsistent** als **nicht gedeckt** gekennzeichnet (Frontmatter `pending-approval:` `:8`, Kopfblock `:216`, `:3141`, Revisionszeile `:488`) |
| No-Placeholder | kein `TODO`/`TBD`/`<…>`/`{{…}}` in den Pflichtsektionen des Deltas |

---

## 1. Verifikationstabelle RVW8-1…RVW8-10

Status-Legende: **behoben** = am Working Tree gemessen und im Spec an der zitierten Stelle
korrigiert · **teilweise** = Substanz korrigiert, Restfehler verbleib (als neues Finding
geführt) · **offen** = nicht korrigiert.

| # | Sev (R8) | Status | Beleg im Spec (Zeile) | Gegenmessung Working Tree | Restaufwand |
|---|---|---|---|---|---|
| **RVW8-1** falsche Messung `:42` | major | **behoben** | K-3 `:4181`; T-4 `:4335`; V-D4 `:4360`; Kopfblock `:204-206`; §15 `:3150`; Katalog `:4398` | **Grep:** `test_docs_consolidation_migration.py:42` „# IC-22 enumerates six rows; five of them are `docs-consolidation.*` keys, the" · `:43` „# sixth (`knowledge-engine.okf.index-mode`) belongs to a different block and is" · `:44` „# deferred to W7-2. `checks.strict` is a nested key, so it is one property here." ⇒ Kommentar **existiert**; Abbruchbedingung in T-4 **gestrichen** | RVW9-3 (Ordinal in T-4) |
| **RVW8-2** `_IC22_ABSENCE_DEFAULTS` | major | **behoben** | T-3 (a)+(b) `:4334`; P-3-E `:4173`; V-D4 `:4360`; Coverage `:4377`; Nachweis `:4350`/`:4351`; Katalog `:4399` | **Grep:** `test_doc_renderer.py:1092` `_IC22_ABSENCE_DEFAULTS: dict = {`, `:1093-1097` fünf Keys (`enabled`/`index-mode`/`checks`/`sources`/`volatile-facts`); `:1114` `def _schema_absence_defaults` mit `:1122` `for key, prop in block_schema["properties"].items()` ⇒ iteriert **alle** Block-Properties; `:1371` `assert _schema_absence_defaults(block_schema) == _IC22_ABSENCE_DEFAULTS`; `:1318` `def test_absent_block_is_noop` | RVW9-6, RVW9-7 (Formulierung) |
| **RVW8-3** Trace-Matrix AC-42…46 | major | **behoben** | §9.1 `:2561-2565`; AC-39 `:2527`; AC-21 `:2543`; Begründung `:2574-2584`; §9.2 W3 `:2607`, W8 `:2612`; Zählsatz `:2614-2624`; §15 `:3145-3147` | **Nachgerechnet:** W1 10 · W2 7 · W3 **19** · W4 2 · W5 2 · W6 2 · W7 4 · W8 2 = 48 Zuordnungen − 2 (AC-28 dreifach) = **46** AC ⇒ Zählsatz und §15 stimmen | RVW9-8 (info) |
| **RVW8-4** Wellen-Reihenfolge | major | **behoben (spec-intern)** · **Plan offen** | V-D7 `:4363`; T-3 `:4334`; T-5 `:4336`; T-8 `:4339`; Nachweis `:4350`; §9.1 `:2527`/`:2565`; §9.2 `:2607`/`:2612`; E-13a **zurückgenommen** `:4253`; E-13b `:4254`; E-13 bleibt OFFEN `:4256` | Spec-Durchzug lückenlos (T-8 → T-3 → T-5, alle **W3-6**). **Plan:** `…-consolidation.md:4920-4944` (W3-6) `Files:` ohne `config/project-config.schema.json` / `tests/test_docs_consolidation_migration.py`, `Ziel-AK` `:4926` = AC-20/AC-12/AC-38, Steps `:4938-4944` ohne T-3/T-5/T-7/T-8; `:2080-2098` (W1-9, **`[x]` gelandet**) trägt Schema-Block + Migrationstest und behauptet „**sechs** Properties" (`:2084`, `:2096`), gemessen sind **fünf**; Plan-Frontmatter `:1-13` ohne `pending-approval:` | **RVW9-2 (major)** |
| **RVW8-5** Threat Model (g) | major | **behoben** | (g) `:2976`; Q3 `:2992-2999` + `:3000-3006`; Q4 (g) `:3023-3030`; Q4 (d) `:3016-3018`; Bewertung `:3032-3040`; Coverage `:4379` | Alle vier Fragen beantwortet; Kopier-Pfad **explizit** als Restrisiko geführt und **ausdrücklich NICHT akzeptiert** (`:3002-3003`); Ziffer **sieben** (`:3032`); `config.py:342`/`:388` belegt | RVW9-4 (Querverweis) |
| **RVW8-6** Schema ≠ geschlossener Wächter | minor | **behoben** | IC-25 `:1592-1600`; IC-13 `:1424`; §12.3 (g) `:2976` | **Grep:** `scripts/lib/config.py:342` „4. Schema validation against agent-meta.schema.json if jsonschema is" · `:388` „pass  # jsonschema not installed or validation error — best-effort" | — |
| **RVW8-7** AC-42 (d) Anker | minor | **behoben** | `:2301-2305` (`:629` + Def `:531`; `:635-639` + Marker `:371`) | **Grep:** `doc_renderer.py:531` `def _facts_section`, `:629` `lines.extend(_facts_section(facts))`, `:636` `facts-hash:`, `:637` `generator:`, `:638` `FOOTER_END_MARKER,`, `:371` `FOOTER_BEGIN_MARKER: str =` ⇒ beide Hälften getrennt belegt | — |
| **RVW8-8** Anker-Drift-Politik | minor | **behoben** | Auswahlregel + Inventar V-D1 `:4357` (**14** Fundstellen mit Zielanker); V-D2 `:4358` (+ AC-22 `:2513`, + A4 `:2968`); angewandt IC-15 `:1465-1466` | **Grep/Read:** `spec_plan_scaffold.py` Zielanker `:28/:29/:30/:80/:100/:102-104/:115-116/:121` plausibel; Regel explizit formuliert und angewandt | RVW9-8 (Selbstverweis) |
| **RVW8-9** AC-39 Belegquelle | minor | **behoben** | `:2429-2445` („**nicht** ein `.meta-config`-Stand: dort trägt der Block nur `enabled` und `checks.strict`") | **Read `.meta-config/project.yaml:395-401`:** `:398` `docs-consolidation:` · `:399` `enabled: true` · `:400-401` `checks:` / `strict: true` ⇒ **nur zwei** Keys, genau wie belegt | — |
| **RVW8-10** Plan-Befund W3-7 + namenlose Testpin-Zeile | minor | **behoben** | V-D6 `:4362`; §17.12.4 Zeile 4 `:4294` (Test **namentlich**, Fall b) | **Grep `scripts/`:** `apply_fact_blocks` nur Docstring-Erwähnungen (`generated_file_drift.py:174`, `docs_freshness.py:468`, `doc_renderer.py:4/:44/:160`), **kein** Produktionsaufrufer; Def `:183`. **Grep `.meta-config/project.yaml`:** **kein** `docs-consolidation.sources` (nur `auto-detect-sources: true` `:46`, `sources-dir: sources` `:52`) | RVW9-9 (Plan-Interaktion W1-10) |

**Ergebnis: 10/10 inhaltlich behoben.** Kein Finding wurde allein wegen eines Katalog-Eintrags
akzeptiert — jede Zeile der Tabelle trägt eine eigene Gegenmessung.

---

## 2. Prüfpunkt 3 — Registrierte Sollwert-Änderung K62: genau zwei harte Mengen-Pins

**Beide Erweiterungen sind Mengen-Erweiterungen, keine Absenkungen — bestätigt.**

| Pin | Datei`:`Zeile` | Ist-Stand | Änderung laut Spec | Art |
|---|---|---|---|---|
| `_EXPECTED_PROPERTIES` | `tests/test_docs_consolidation_migration.py:45-51`, geprüft `:99/:101/:102` in `::test_schema_block_present_and_closed` (`:81`) | **5** Einträge (Grep `:46-50`: `enabled`, `index-mode`, `checks`, `sources`, `volatile-facts`) | **(a) fünf → sechs**, `+ "index-owner"` (T-3, `:4334`) | **Erweiterung** |
| `_IC22_ABSENCE_DEFAULTS` | `tests/test_doc_renderer.py:1092-1098`, geprüft `:1371` in `::test_absent_block_is_noop` (`:1318`) | **5** Keys (Grep `:1093-1097`) | **(b) fünf → sechs**, `+ "index-owner": "auto"` (T-3, `:4334`) | **Erweiterung** |

Der Wert `"auto"` ist korrekt: IC-22 `:1828` führt `docs-consolidation.index-owner` mit
**Default bei Abwesenheit `auto`** — der Pin bildet genau das ab.

**Unberührt bleiben — belegt:**

* `_EXPECTED_CHECKS_PROPERTIES` `tests/test_docs_consolidation_migration.py:53` = `{"strict"}`,
  geprüft `:112` `assert set(checks["properties"]) == _EXPECTED_CHECKS_PROPERTIES`.
  `index-owner` ist eine **Top-Level**-Property des `docs-consolidation`-Blocks
  (`config/project-config.schema.json:2421` Block, `:2439` `checks`, `:2451` `sources`,
  `:2459` `volatile-facts`, `:2470` `additionalProperties: false`) ⇒ das `checks`-Unterobjekt
  ändert sich **nicht**. ✅
* Fail-off-Defaults-Test: **Definition bei `:185`** `def test_schema_declares_the_absence_defaults()`,
  Docstring `:186-192` („IC-22 fail-off defaults, expressed as JSON Schema ``default``"),
  Asserts `:194-199`. Er liest die fünf Keys **namentlich**; das **einzige** `set(...)` ist
  `:196` `set(properties["index-mode"]["enum"]) == {"full", "skeleton"}` — also über die
  **Enum-Werte**, nicht über die Property-Menge. Eine sechste Property bricht ihn **nicht**. ✅

**Vollständigkeit der Pin-Suche (unabhängig nachgeführt, Grep über beide Testdateien):**

* `test_docs_consolidation_migration.py`: Mengen-Vergleiche nur bei `:99`, `:101`, `:102`
  (→ `_EXPECTED_PROPERTIES`), `:112` (→ `_EXPECTED_CHECKS_PROPERTIES`), `:196` (Enum-Werte);
  `:120/:121` baut `names = set(block["properties"])` **dynamisch** und prüft in `:122-128`
  ausschließlich gegen Provider-Namen aus `_provider_names()` (`:76`) — **kein** Sollwert-Pin;
  `index-owner` enthält keinen Providernamen ⇒ bleibt grün.
* `test_doc_renderer.py`: `assert … set(…) ==` nur bei `:288`, `:322`, `:729`, `:732`, `:764`,
  `:774`, `:1371`, `:1749`, `:2348` — davon ist **genau eine** (`:1371`) ein Pin auf die
  `docs-consolidation`-Blockmenge. Die Fail-off-Konfigurationstests (`:1268-1297` Master-Schalter,
  `:1711-1727` `plan == _EMPTY_PLAN`) vergleichen **Ergebnispläne**, keine Key-Mengen.

⇒ **Genau zwei** harte Mengen-Pins betroffen, beide **Erweiterung**, beide in T-3 registriert.
Die Aussage „Sollwert-Änderungen vollständig registriert: **zwei**" (Coverage `:4377`) ist
**korrekt**.

---

## 3. Prüfpunkt 4 — Neue Wellenzuordnung K64/V-D7: Durchzug

| Stelle | Inhalt | Status |
|---|---|---|
| §9.1 AC-39 `:2527` | „W1, **W3-6**" | ✅ |
| §9.1 AC-46 `:2565` | „**W3-6** (T-8/T-3/T-5, Reihenfolge **V-D7**)" | ✅ |
| §9.2 W3 `:2607` | AC-42…AC-46 + „T-8/T-5/T-3, Reihenfolge **V-D7**" | ✅ |
| §9.2 W8 `:2612` | nur Dokuanteil, „Code-, Schema- und Testanteil liegen in jedem Fall in W3-6 (V-D7)" | ✅ |
| Testliste T-3 `:4334` / T-5 `:4336` / T-8 `:4339` | alle „**Welle W3-6**", Reihenfolge **T-8 → T-3 → T-5** | ✅ |
| Nachweiszeilen `:4350` / `:4351` | Schema-Nachweis inkl. **beider** Pins; Einheitentest inkl. `_IC22_ABSENCE_DEFAULTS` | ✅ |
| E-13a `:4253` | in bisheriger Form **zurückgenommen**, korrigierte Fassung als Empfehlung | ✅ |
| E-13 `:4256` | „**Die technische Wellenzuordnung … steht fest; sie ist keine offene Frage mehr.**" — offener Rest: **nur** der Dokuanteil | ✅ |
| V-D7 `:4363` | Messung + Festlegung + „E-13 selbst bleibt OFFEN" | ✅ |
| **Plan W3-6** `…-consolidation.md:4920-4944` | **kein** Schema-File, **kein** Migrationstest, **keine** `index-owner`-Zeile, **keine** AC-42…AC-46, **keine** Reihenfolge | ❌ **RVW9-2** |
| **Plan W1-9** `:2080-2098` | trägt Schema-Block + Migrationstest, **gelandet `[x]`**, behauptet „sechs Properties" | ❌ **RVW9-2** |

---

## 4. Neue Findings aus der Korrekturrunde

### MAJOR

#### RVW9-1 — K-ID-**Kollision**: der neue Katalog K61…K70 überschreibt zehn belegte Korrektur-Kennungen
**Ort:** Spec `:4391` (§17.12.6-Vorspann), `:4398-4407` (Katalog), Kopfblock `:215`, `:221`,
Frontmatter `:8`, Coverage `:4382-4383`; kollidierender Bestand `:4027-4075` (§17.11.5) und
`:4077-4090` (§17.11.6).
**Befund.** Der Vorspann des neuen Korrektur-Katalogs behauptet: „**Neue Katalog-IDs ab K61;
K18…K60 bleiben unberührt**, keine Umnummerierung" (`:4391`). **Gemessen ist die Obergrenze
K75, nicht K60.** Das Dokument selbst belegt es an zwei Stellen:
* Legende `:257-263`: „Maßgeblich für den heutigen K-Stand ist die **Plan-Legende** (`K1…K70` —
  **Stand Korrekturrunde 5**; **Korrekturrunde 6 hat sie auf `K1…K75` verlängert**, §17.11.6 …)";
* `:261-263`: „**Korrekturrunde 5** um `K59`…`K70` (11 Review-Findings + 5 Validator-Notizen) —
  Volltext **§17.11.5**; **Korrekturrunde 6** um `K71`…`K75`".

Damit sind **alle zehn** neuen Kennungen bereits belegt — §17.11.5 `:4053-4064`:

| neu | bereits belegt (Spec) | bisherige Bedeutung |
|---|---|---|
| K61 | `:4055` | RVW-7-03 (major) — W2-6 nannte „drei V4-Tests", tatsächlich sieben |
| K62 | `:4056` | RVW-7-04 (major) — `TASK_HEADER_RE`-Dep-Tokens, `spec_plan.py` in W2-9 |
| K63 | `:4057` | RVW-7-05 (major) — Mechanismus (ii) in W2-8 unerreichbar |
| K64 | `:4058` | RVW-7-06 (minor) — Extraktionsregel, 7/6-Lesart |
| K65 | `:4059` | RVW-7-07 (minor) — Vorrangregel fail-soft vor fail-closed |
| K66 | `:4060` | RVW-7-08 (minor) — K57-Teilfehler (b) zurückgenommen |
| K67 | `:4061` | RVW-7-09 (minor) — V4 in `W-VALIDATE-ROT` |
| K68 | `:4062` | RVW-7-10 (info) — Docstrings `docs_links.py` |
| K69 | `:4063` | RVW-7-11 (info) — Korrekturrunde 4 ohne Supersessions-Verweis |
| K70 | `:4064` | Validator-Notizen `n1…n5` |

Die Kollision ist **nicht nur formal**: `K62` steht jetzt im Kopfblock `:221` für
„_zwei_ harte Sollwert-Änderungen" und in §17.12.1 `:3877` für „`spec_plan.py` in W2-9s `Files:`";
`K65` steht in §12.3 `:3003` für das Restrisiko und in §17.11.5 `:4059` für die Vorrangregel.
Ein Reviewer oder `validator`, der „K62" auflöst, trifft zwei verschiedene normative
Korrekturen. Das bricht die Invariante, die Runde 2 ausdrücklich als Muster festgehalten hat
(„K-Katalog: jede Kennung genau einmal belegt"), und widerlegt die Selbstauskunft in Coverage
`:4382-4383`.
**Verbesserung.** Katalog auf **`K76…K85`** umnummerieren und **alle** Vorkommen nachziehen
(§17.12.6-Tabelle, Kopfblock `:215`/`:221`, Frontmatter `:8`, Revisionszeile `:488`, IC-25
`:1592`, §9.1 `:2574`, E-13 `:4253`/`:4254`, V-D1 `:4357`, V-D3 `:4359`, T-3 `:4334`, T-4
`:4335`, IC-13 `:1424`, Coverage `:4378`/`:4379`, AC-21/AC-39/AC-46-Verweise `:2370`/`:2429`/
`:2565`). Vorspann auf „Neue Katalog-IDs ab **K76**; **K1…K75** bleiben unberührt" korrigieren
und die maßgebliche Obergrenze (`K75`, Plan-Legende, §17.11.6) dort nennen. **Keine** der zehn
bisherigen Bedeutungen wird gestrichen — die Kollision ist vollständig additiv auflösbar.

#### RVW9-2 — Der Plan trägt Rev. 0.8 nicht: W3-6-Akzeptanz nach §17.12.4 ist unerfüllbar
**Ort:** Spec §17.12.4 `:4345-4351`, §9.1 `:2527`/`:2565`, V-D7 `:4363`; Plan
`docs/plans/2026-09-25-repository-documentation-consolidation.md` `:1-13` (Frontmatter),
`:2080-2098` (W1-9), `:4920-4944` (W3-6), `:5694` (Ledger-Zeile W1-9).
**Befund.** K64/V-D7 legt T-3/T-5/T-8 **ausschließlich** in W3-6 und knüpft die W3-6-Akzeptanz
an „gruen inkl. 2 neuer Enum-Tests und erweiterter Property-Menge" (`:4350`). Der Plan, Rev. 0.7,
`status: APPROVED`, enthält dazu **nichts**:
* W3-6 `Files:` `:4920-4921` = `docs/INDEX.md`, `.meta-config/project.yaml`, `README.md`,
  `tests/test_doc_renderer.py` — **weder** `config/project-config.schema.json` **noch**
  `tests/test_docs_consolidation_migration.py`;
* W3-6 `Ziel-AK` `:4926` = **AC-20, AC-12 (E2E), AC-38** — **kein** AC-42…AC-46, kein AC-39;
* W3-6 Steps `:4938-4944` — keine Config-Zeile `index-owner` (T-7), keine Schema-Property
  (T-8), keine Pins (T-3), keine Enum-Tests (T-5), keine Reihenfolge;
* **Grep** über den Plan: `index-owner` = **0** Treffer, `AC-4[2-6]` = **0** Treffer,
  `pending-approval` = **0** Treffer;
* Der Schema-Block und `tests/test_docs_consolidation_migration.py` sind im Plan **W1-9**
  zugeordnet (`:2082`, Ledger `:5694`) — und W1-9 ist **bereits abgearbeitet** (`:2095-2098`
  alle `[x]`, Commit `feat: declare docs-consolidation config block in schema`). W1-9 behauptet
  „**sechs** Properties aus IC-22" (`:2084`, `:2096`); **gemessen sind fünf**
  (`tests/test_docs_consolidation_migration.py:46-50`, Schema `:2424-2469`) — dieselbe
  Fehlzählung, die P-3-E in der Spec korrekt diagnostiziert, im **Plan** aber unberührt lässt.

**Auswirkung.** Wird W3-6 nach Plan umgesetzt, entsteht **weder** die Deklaration (T-7) **noch**
die Schema-Property (T-8) — der KE-Vorrang-Zweig `doc_renderer.py:702-703` blockiert dann
weiterhin jeden Schreibvorgang, `docs/INDEX.md` entsteht nicht, und die in §17.12.4
festgeschriebenen Nachweise sind nicht erreichbar. Zusätzlich fehlt im Plan die
`pending-approval:`-Spiegelung: wer den Plan liest, sieht das Freigabe-Gate für Rev. 0.8 nicht.
Der einzige registrierte Plan-Befund ist V-D6 (`:4362`) und betrifft **W3-7** — die kleinere
Lücke; die größere ist nirgends erfasst.
**Verbesserung.** Als **V-D8** registrieren (Muster V-D6: Befund, keine Spec-Pflicht) mit
Sollwert: „Plan Rev. 0.7 kennt Rev. 0.8 nicht: W3-6 ohne T-3/T-5/T-7/T-8/AC-42…AC-46, W1-9
abgeschlossen und mit der Fehlzählung ‚sechs Properties', **kein** `pending-approval:` im
Plan-Frontmatter." Und in §17.12.4 bzw. als Befund festhalten, welcher **Plan**-Delta vor
Umsetzung von W3-6 zwingend ist (W3-6 `Files:` + `Ziel-AK` + Steps inkl. Reihenfolge T-8 → T-3 →
T-5; `pending-approval:` im Plan-Frontmatter; Korrektur der W1-9-Textziffer). Der Plan selbst
ist **nicht** Teil dieser Spec-Korrekturrunde — die Registrierung muss es aber machen, damit die
Lücke nicht unsichtbar bleibt.

### MINOR

#### RVW9-3 — T-4 schreibt eine **falsche Ordnungszahl** in genau den Kommentar, den es korrigiert
**Ort:** Spec `:4335` (T-4), `:4181` (K-3).
**Befund.** T-4 verlangt: Text in `:42` von „six rows/five of them" auf „**seven rows/six** of
them"; „die **Hälfte ab Zeile `:43`** bleibt **wortgleich**" — mit der Begründung, der KE-Key
liege weiterhin in einem anderen Block. Zeile `:43` lautet aber (Grep): „# **sixth**
(`knowledge-engine.okf.index-mode`) belongs to a different block and is". Nach der
IC-22-Tabelle (`grep`/Read `:1821-1829`) hat sie nach Rev. 0.8 **sieben** Zeilen, davon **sechs**
`docs-consolidation.*`-Keys. Der KE-Key ist damit die **siebte**, nicht die sechste Zeile. Das
vorgegebene Ergebnis lautet damit: „IC-22 enumerates **seven** rows; **six** of them are
`docs-consolidation.*` keys, the **sixth** (`knowledge-engine.okf.index-mode`) belongs to a
different block" — **in sich falsch**. Die Formulierung „sechs von sieben" und „the sixth" kann
nicht gleichzeitig stimmen.
**Verbesserung.** `:43` mitziehen: „# **seventh** (`knowledge-engine.okf.index-mode`) belongs to a
different block and is". `:44` (`:53`-Anker, `checks.strict`) bleibt wortgleich; die
IC-22-Tabelle (sieben Zeilen, `:1839`) bleibt der Bezug. K-3 entsprechend präzisieren.

#### RVW9-4 — §12.3 verweist auf eine „Ergänzung zu E-13", die in E-13 nicht steht; Q4 verweist auf die falsche Sektion
**Ort:** Spec `:3000-3006` (Q3-Bullet), `:3030` (Q4-Verweis), `:4256` (E-13), `:4249-4258`
(E-13-Optionentabelle).
**Befund.** Q3-Bullet verweist die Kopier-Ausprägung als „**Ergänzung zu E-13** (offen,
§17.12.2)" und benennt als zu entscheidende Frage, „**wer** die Deklaration dokumentiert und ob
eine `validate`/`--strict`-Meldung gefordert wird". Die E-13-Vorlage `:4249-4258` enthält
**keine** solche Option (nur die Doku-Zuordnung W3-6/W8-4 bzw. „alles in W3-6"); die
Optionentabelle wurde nicht nachgezogen. Q4 `:3030` verweist auf „§17.12.**3** Q3-Bullet" — der
Bullet steht in **§12.3** (Threat Model), nicht in §17.12.3 (DECISION-1…4).
**Verbesserung.** In §17.12.2 eine **dritte** E-13-Zeile (z. B. „E-13c — Kopier-Pfad") mit den
beiden Entscheidungspunkten (Doku-Pflichtträger; `validate`/`--strict`-Meldung bei
`index-owner` + `knowledge-engine.enabled: true`) und **Owner/Termin** ergänzen, oder den
Verweis in §12.3 auf eine ausdrücklich noch anzulegende Vorlage (`E-14`) umstellen. Verweis in
Q4 auf „§12.3 Q3-Bullet" korrigieren.

#### RVW9-5 — `P-3-E` steht als **sechste** Zeile in einer als „P-1…P-5" überschriebenen Freigabetabelle
**Ort:** Spec `:6` (Frontmatter), `:8`, `:214-226` (Kopfblock), `:3139`, `:3159`, `:4166`
(§17.12.1-Titel), `:4173` (P-3-E-Zeile), `:4411`.
**Befund.** Die P-Tabelle in §17.12.1 trägt **sechs** Zeilen (P-1, P-2, P-3, **P-3-E**, P-4,
P-5), während Frontmatter `:6` von „Die **fünf** inhaltlichen Pflichtänderungen P-1…P-5" und
§17.12.1-Titel `:4166`, §15 `:3139`/`:3159` und das Ergebnisprotokoll `:4411` von
„P-1…P-5" sprechen. `P-3-E` ist im Katalog-Kontext nirgends als **neu in dieser Korrekturrunde**
ausgewiesen; Kopfblock `:217-218` sagt sogar „Die Runde behob **ausschließlich Beleg- und
Zuordnungsfehler** und erzeugte **keine** neue Pflicht", während `:219-221` vier Korrekturen
als „**inhaltlich**" ausweist. Inhaltlich ist die Offenlegung vorhanden und gut (die zweite
Sollwert-Änderung wird im Kopfblock ausdrücklich als bestätigungspflichtig genannt) — die
**Zählung und die ID-Herkunft** sind es nicht.
**Verbesserung.** Entweder (a) `P-3-E` als **Teilstück von P-3** kennzeichnen („P-3 (e)") und
„fünf" beibehalten, oder (b) konsequent „P-1…P-5 (+ P-3-E)" schreiben und P-3-E in Frontmatter
`:6`, §15 `:3139` und `:4411` mitführen; in beiden Fällen in `:217` „keine neue Pflicht" auf
„keine neue Pflicht **außerhalb** des bestehenden P-3" präzisieren. Der Frontmatter-Satz
„neu sind ausschließlich IC-25, IC-26, AC-42…AC-46" (`:6`) sollte die P-Nennung einschließen.

#### RVW9-6 — K62 verortet die beiden Pins an der falschen Tabelle
**Ort:** Spec `:4399` (K-62), `:4301-4316` (Tabelle „Bestehende Tests, die unverändert grün
bleiben"), `:4298` (Modus-Übersicht Zeile 8), `:4334` (T-3).
**Befund.** K62 behauptet: „beide Pins stehen in der ‚bleiben grün'-Tabelle **und** in der
Coverage-Checkliste". Gemessen steht in der „bleiben grün"-Tabelle **keiner** der beiden Pins —
sie listet die **unveränderten** Nachbarn (`_EXPECTED_CHECKS_PROPERTIES` `:4316`, Fail-off-Test
`:4315`). Die beiden geänderten Pins stehen korrekt in der Modus-Übersicht (`:4298`) und in
T-3 (`:4334`); die Coverage-Zeile `:4377` ist zutreffend.
**Verbesserung.** K62 auf „Modus-Übersicht Zeile 8 und T-3 (a)/(b) sowie Coverage-Zeile
‚Sollwert-Änderungen vollständig registriert'" umstellen. Rein sprachlich, ohne Sachwirkung.

#### RVW9-7 — Neue Zeile in der „bleiben grün"-Tabelle nennt einen **nicht existierenden** Testnamen
**Ort:** Spec `:4315`, `:4360`, `:4399`; Testdatei `tests/test_docs_consolidation_migration.py:185-199`.
**Befund.** Die Zeile lautet „`::test_fail_off_defaults_*` (Fail-off-Defaults des Blocks) |
`tests/test_docs_consolidation_migration.py:186-199`". **Gemessen (Grep):** ein Test mit diesem
Namen existiert **nicht**; der Test heißt `def test_schema_declares_the_absence_defaults()`
(`:185`), Docstring `:186-192`, Asserts `:194-199`. Die **Aussage** der Zeile ist korrekt
(belegt und von mir bestätigt: namentliches Lesen, kein Mengen-Vergleich → sechste Property
bricht ihn nicht) — aber der Zeilenbereich beginnt **im Docstring** (`:186` statt `:185`) und
der Testname ist ein **Wildcard**, den es so nicht gibt. Das ist genau die Fehlerklasse, die
**K70** (RVW8-10) für die Modus-Übersicht Zeile 4 abgestellt hat, während die Coverage-Zeile
`:4373` („**alle** Zeilen mit Testnamen") und `:4382` („10/10 Findings, je mit `file:line`-Beleg")
eine Vollständigkeit behaupten.
**Verbesserung.** Auf `::test_schema_declares_the_absence_defaults` (`:185-199`) umstellen, in
V-D4 `:4360` und K62 `:4399` ebenfalls.

#### RVW9-8 — V-D1 verweist auf die **falsche Zeile** der von ihr selbst angewandten Korrektur
**Ort:** Spec `:4357` (V-D1), `:4405` (K68), `:1465-1466` (IC-15 nach Korrektur).
**Befund.** V-D1 schreibt „**getan**, IC-15 `:1449-1450` ⇒ `:28`/`:29`". Gemessen liegt die
angewandte Korrektur bei **`:1465-1466`** („`DEFAULT_FALLBACK_INDEX = "docs/INDEX.md"   # :28`",
„`_FILE_INDEX_SKELETON = "…"   # :29`") — genau wie K68 `:4405` korrekt zitiert. `:1449-1450`
trägt heute den IC-14-Überschrift/Absatzbereich. Es ist ein **veralteter Selbstverweis** — dieselbe
Klasse wie RVW8-8, hier im Spec selbst statt gegen den Code.
**Verbesserung.** `:1449-1450` → `:1465-1466` in V-D1. Zusätzlich §9.2/§9.1-Hinweis: AC-39 ist in
§9.1 (`:2527`) W1 **und** W3-6, erscheint aber nicht in der AC-Menge der W3-Zeile `:2607`; die
Nicht-Doppelzählung ist im Zählsatz `:2619-2623` begründet — dieselbe Konvention einmal in §9.2
sichtbar machen (info).

#### RVW9-9 — Offener Schritt von W1-10 schreibt **denselben** Config-Block wie T-7
**Ort:** Plan `:2100-2120` (W1-10, Step 2 `[ ]` **offen**), Spec `:4338` (T-7), `:4204-4220`
(E-10), `:4362` (V-D6); Runde-8-Liste `…-rereview-8.md:377-378`.
**Befund.** W1-10 Step 2 ist ausdrücklich offen und will `index-mode`, `checks.strict`,
`sources`, `volatile-facts` **in den `docs-consolidation`-Block** von
`.meta-config/project.yaml` nachtragen (Plan `:2115-2118`, „4 von 5 Properties"). T-7 will
`index-owner` in **denselben** Block (`:398-401`) schreiben. Zusätzlich würde das gesetzte
`sources` den Gate-Zweig `apply_fact_blocks` aktivieren — genau die Abhängigkeit, die E-10
(`:4206-4220`) und V-D6 (`:4362`) als **eigene** Config-Zeile für W3-7 führen. Der
Runde-8-Blockierpunkt „CAN_RUN_IN_PARALLEL: W1-9/W1-10-Rest" stützt sich auf die Annahme, W1-10
berühre **keine** `docs-consolidation`-Zeile — diese Annahme trifft für den **offenen** Step 2
nicht zu.
**Verbesserung.** Als Befund registrieren und die Reihenfolge festhalten: W1-10 Step 2 **vor**
W3-6 ziehen (dann ist der Live-Block vor dem Delta vollständig) **oder** als Bestandteil von
W3-6 führen; die `CAN_RUN_IN_PARALLEL`-Liste entsprechend berichtigen.

---

## 5. Regressionsprüfung (Prüfpunkt 2)

| Prüfpunkt | Ergebnis | Beleg |
|---|---|---|
| P-1…P-5 **inhaltlich unverändert** | ✅ | §17.12.1 `:4170-4175` deckt sich Zeile für Zeile mit Design §6.1 `:681-685` (IC-13 bedingt · IC-15 Neuanlage-Bedingung · IC-22 siebter Key · AC-21 bedingt + AC-42…46 · R7 dritter Hebel) |
| Keine Umnummerierung bestehender IDs | ✅ | §15 `:3162-3165`; AC-40 `:2556`, AC-41 `:2560`, IC-16 u. a. unangetastet |
| Keine neuen IC-/AC-/Task-/Wellen-IDs | ✅ | neu in Rev. 0.8 (nicht in dieser Runde): IC-25/IC-26, AC-42…AC-46, T-1…T-8, W3-6 |
| E-9…E-13 weiterhin **offen**, nicht unterstellt | ✅ | `:4185` „**OFFEN, nicht entschieden**"; E-9 `:4191-4202`, E-10 `:4204-4220`, E-11 `:4222-4235`, E-12 `:4237-4247`, E-13 `:4249-4265` — je Option + Empfehlung, keine Festlegung. V-D7 schließt **nur den technischen** Teil per Messung und hält E-13 ausdrücklich offen (`:4256`, `:4363`) |
| OQ1 weiterhin **offen** | ✅ | Record `docs/plans/2026-09-25-docs-consolidation-oq1.md:5` `status: open`, `:94` „**OFFEN** — nicht entschieden", `:96` Owner `main_chat`, `:99` Blockade W5; Spec `:4272` („**BLEIBT OFFEN**", keine Aufhebung der W5-Blockade) |
| `pending-approval:` gesetzt | ✅ | Frontmatter `:8`; Kopfblock `:216`; §15 `:3141`; `status: APPROVED`/`approved: 2026-09-26` **unverändert** — der Approval-Marker spiegelt Rev. 0.8 **nicht** |
| Neue Pflicht eingeschleppt? | ⚠️ | **P-3-E** (RVW9-5) — inhaltlich offengelegt, aber als sechste Zeile einer Fünfer-Tabelle geführt; Kopfblock `:217-218` („keine neue Pflicht") und `:219-221` („vier Korrekturen sind inhaltlich") stehen nebeneinander |
| Neue Fehler eingeschleppt? | ❌ | **RVW9-1** (K-ID-Kollision, major), **RVW9-2** (Plan-Divergenz, major), RVW9-3…RVW9-9 (minor) |

---

## 6. Verdikt

**`CHANGES_REQUESTED`** — 0 kritisch · 2 major · 7 minor · 1 info. Kein Blocker, **kein**
`BLOCKED`: das Delta selbst ist tragfähig, seine Begrenztheit ist sauber belegt, und
**alle zehn Findings aus Runde 8 sind am Working Tree verifiziert behoben**. IC-25 verengt
ausschließlich einen Auslöser; die Consumer sind per Konstruktion unerreichbar; die
Fail-closed-Reihenfolge steht vor der KE-Prüfung; die Namensfreiheit ist echt; keine
Entscheidung wird unterstellt.

**Was trägt.** Die Beleg- und Zuordnungsebene, an der Runde 8 gescheitert war, ist jetzt sauber:
Der Zählkommentar ist als existent erkannt und mit Grep-Belegen geführt (RVW8-1); **beide**
harten Mengen-Pins sind registriert, als Erweiterungen charakterisiert und ihre Unversehrtheit
der dritten Pins nachgewiesen (RVW8-2); die Trace-Matrix ist vollständig und der Zählsatz geht
auf (RVW8-3); die technische Wellenzuordnung ist gemessen und über **acht** Stellen konsistent
gezogen, ohne E-13 zu entscheiden (RVW8-4); das Threat Model beantwortet alle vier Fragen zu
(g) und benennt den Kopier-Pfad als **ausdrücklich nicht akzeptiertes** Restrisiko (RVW8-5); die
best-effort-Relativierung des Schemas steht an allen drei geforderten Stellen (RVW8-6); die
Anker sind getrennt belegt (RVW8-7); die Anker-Drift hat eine Regel und ein vollständiges
Inventar (RVW8-8); AC-39 nennt die richtige Quelle (RVW8-9); die Planlücke ist erfasst und die
Testpin-Zeile benannt (RVW8-10).

**Was blockiert.** Nicht die Architektur, sondern die **Korrekturrunde selbst**: Sie hat einen
neuen Katalog angelegt, dessen Kennungen **zehnfach belegt** sind (RVW9-1) — womit die
Selbstauskunft „K18…K60 bleiben unberührt" im selben Absatz falsch wird und die Traceierbarkeit
der Runde 8 aufgehoben ist; und sie hat die Wellenzuordnung im Spec festgelegt, ohne den
**ausführbaren** Plan mitzuziehen (RVW9-2), sodass die in §17.12.4 festgeschriebene W3-6-Akzeptanz
vom aktuellen Plan aus nicht erreichbar ist.

---

## 7. `BLOCKING_FOR_W3-6`

Vor Umsetzung von W3-6 zwingend:

1. **RVW9-1** — K-Katalog auf `K76…K85` umnummerieren, alle ~20 Vorkommen nachziehen, Vorspann
   „ab K61 / K18…K60" auf „ab K76 / K1…K75" korrigieren.
2. **RVW9-2** — Plan-Divergenz als V-D8 registrieren und den **fOrderlichen Plan-Delta** benennen
   (W3-6 `Files:`/`Ziel-AK`/Steps inkl. Reihenfolge T-8 → T-3 → T-5, `pending-approval:` im
   Plan-Frontmatter, W1-9-Textziffer); Plan Rev. 0.7 selbst erst nach User-Freigabe revidieren.
3. **RVW9-3** — T-4: `:43` auf „**seventh**" mitziehen (sonst entsteht ein widersprüchlicher
   Zählkommentar).
4. **RVW9-4** — E-13-Optionstabelle um die Kopier-Pfad-Entscheidung ergänzen (oder `E-14`
   anlegen); Q4-Verweis auf §12.3 korrigieren.
5. **RVW9-5** — „P-1…P-5" ↔ `P-3-E` in Frontmatter/Kopfblock/§15/Ergebnisprotokoll auflösen.
6. **RVW9-7** — `::test_fail_off_defaults_*` → `::test_schema_declares_the_absence_defaults`
   (`:185-199`) in `:4315`, `:4360`, `:4399`.
7. **RVW9-6**, **RVW9-8**, **RVW9-9** — Textberichtigungen (K62-Verortung, V-D1-Selbstverweis,
   W1-10-Reihenfolge).
8. **Freigabe von P-1…P-5 (inkl. P-3-E) durch den Nutzer** — der Delta-Umfang bleibt bis dahin
   nicht umsetzbar (Frontmatter `pending-approval:`, Kopfblock `:216`, §15 `:3141`).

## 8. `CAN_RUN_IN_PARALLEL`

Ohne Berührung des Deltas, ohne Konflikt mit den Findings:

* **W0-2** (Ledger-Writer, `W2-9`/`plan_identity.py`) — `scripts/lib/plan_*.py`, nicht
  `doc_renderer.py`/Schema/Config-Block.
* **W2-7 / V4-Registrierung** (`consistency-check.py`, `docs_links.py`) — gemeinsames Gate
  `consistency-check.py:138` wird nicht angefasst.
* **W2-8** (Entkopplung der zwei roten Volltests) — andere Dateien.
* **W1-9** — abgeschlossen (`[x]`, Plan `:2095-2098`); die Textziffer „sechs" (`:2084`, `:2096`)
  ist eine reine Plan-Korrektur ohne Codewirkung.
* **W5-1…W5-3-Content-Arbeit** ohne die `git mv`-Wellen — greifen `knowledge/**`, nicht
  `docs/INDEX.md`; OQ1-Blockade W5 bleibt zu beachten.
* **Reine Lese-/Zählnachweise**: `bash tests/scenarios/run.sh 50 51 52 54 55 56`,
  `git check-ignore -q docs/INDEX.md`, `python3 -c "import json;json.load(open('config/project-config.schema.json'))"`.
* ⚠️ **Korrigiert gegenüber Runde 8:** **W1-10-Rest ist NICHT konfliktfrei** — der offene Step 2
  (Plan `:2115-2118`) schreibt in **denselben** `docs-consolidation`-Block wie T-7 und würde
  `sources` aktivieren (E-10/V-D6). Vor W3-6 serialisieren (RVW9-9).
