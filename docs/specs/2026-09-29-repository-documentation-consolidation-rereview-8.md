---
review-id: RVW-DOCS-CONSOLIDATION-R8
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
plan-id: PLAN-DOCS-CONSOLIDATION-2026-09-25
subject: docs/specs/2026-09-25-repository-documentation-consolidation.md
subject-revision: 0.8
round: 8
reviewer: concept-reviewer
date: 2026-09-29
verdict: CHANGES_REQUESTED
---

# Concept-Review Runde 8 — Spec Rev. 0.8 (agent-meta-Ausnahme, IC-25/IC-26)

> **Verdikt: `CHANGES_REQUESTED`** — 0 kritisch · **5 major** · 5 minor · 0 info.
> **Kein** Blocker, **kein** `BLOCKED`: der Delta-Entwurf ist tragfähig, in seiner Begrenztheit
> sauber belegt und in seiner Struktur reif. Die Findings betreffen **Belegbarkeit** (eine
> falsche Messung), **Vollständigkeit der Nachweis-Tabelle** (eine zweite, nicht registrierte
> Sollwert-Änderung), **Trace-Matrix** (fünf AC ohne Welle), **Wellen-Reihenfolge** (T-3/T-5/T-8)
> und das **Threat Model** (Zeile g unvollständig).

**Scope.** Geprüft wurde `docs/specs/2026-09-25-repository-documentation-consolidation.md`
Rev. 0.8 (`revision: 0.8`, `status: APPROVED`, `pending-approval:` — Delta **nicht** gedeckt)
gegen den Working Tree, read-only. **Keine** Datei des geprüften Dokuments wurde geändert,
keine Git-Mutation, kein `sync.py`. Prüfmodus: **Spec-Review (§7.1)** + **Spec-Review eines
ungfreigegebenen Deltas**.

**§7.1-Checks (alle grün):**

| Check | Ergebnis |
|---|---|
| Pflichtsektionen | vorhanden (§2 Problem/Ziel/Nicht-Ziele, §5 Interface Contracts, §6 Datenfluss, §7 AC, §11 offene Fragen, §12 Risiken) |
| Trace-Anker | `spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25` in Frontmatter **und** §15 (`:3009`), Rev.-0.8-Eintrag `:3051-3067` |
| Approval-Marker | `status: APPROVED` + `approved: 2026-09-26`; Rev. 0.8 korrekt als **nicht gedeckt** gekennzeichnet (Frontmatter `pending-approval:`, Kopfblock `:136-217`, Revisionszeile `:472`) — **konsistent** |
| No-Placeholder | keine `TODO`/`TBD`/`<…>`/`{{…}}` in Pflichtsektionen des Deltas |

---

## Findings

### MAJOR

#### RVW8-1 — Falsche Messung: `tests/test_docs_consolidation_migration.py:42` ist **nicht** leer
**Ort:** Spec `:4083` (K-3), `:4235` (T-4), `:4260` (V-D4).
**Befund.** Die Spec behauptet dreifach, die Zeile `:42` sei leer und der „belegte Träger" sei
`_EXPECTED_PROPERTIES` (`:45-51`). **Gemessen ist das Gegenteil.** Zeile 42–44 trägt einen
dreizeiligen Zählkommentar:

```
42: # IC-22 enumerates six rows; five of them are `docs-consolidation.*` keys, the
43: # sixth (`knowledge-engine.okf.index-mode`) belongs to a different block and is
44: # deferred to W7-2. `checks.strict` is a nested key, so it is one property here.
```

Zusatzbeleg: das **Quell-Design** zitiert denselben Kommentar wörtlich
(`…-design-agent-meta-exception.md:683`, `:698` — „`tests/test_docs_consolidation_migration.py:42`
(„IC-22 enumerates six rows; five of them are `docs-consolidation.*`")"). Die Spec widerspricht
damit ihrer eigenen Quelle an genau der Stelle, die sie zu belegen vorgibt.
**Auswirkung.** T-4 trägt die ausdrückliche Abbruchbedingung „**Fehlt der Kommentar am Working
Tree, entfällt T-4 ersatzlos**". Wird nach dieser Fehlmessung verfahren, bleibt ein Kommentar
stehen, der nach Rev. 0.8 **falsch** ist (sieben Zeilen in der IC-22-Tabelle, sechs
`docs-consolidation.*`-Keys) — und V-D4 stuft eine reine Sollwert-Änderung (T-3) als
„die einzige echte" ein, was den Kern von K-3/T-4 zerstört.
**Korrektur.** V-D4, K-3 und T-4 auf den belegten Stand setzen: Träger ist der **Kommentar
`:42-44`** plus `_EXPECTED_PROPERTIES` `:45-51`. T-4 bleibt **verbindlich** (Textänderung
„six rows/five" → „seven rows/six"; `:44` „deferred to W7-2" ist weiterhin gültig) und die
Abbruchbedingung entfällt. Zudem: alle vier V-D-Befunde gegen dieselbe Messmethode
prüfen, bevor sie als „am Working Tree gemessen" in die Coverage-Checkliste `:4253-4276`
wandern.

---

#### RVW8-2 — Zweite, **nicht registrierte** harte Sollwert-Änderung: `_IC22_ABSENCE_DEFAULTS`
**Ort:** Spec `:4234` (T-3, „**die einzige echte Sollwert-Änderung in Rev. 0.8**"), `:4228-4239`
(Tabelle T-1…T-8), `:4203-4216` („Bestehende Tests, die unverändert grün bleiben").
**Befund.** `tests/test_doc_renderer.py:1092-1098` pinnt
`_IC22_ABSENCE_DEFAULTS` als **hartes Fünf-Key-Dict**; `tests/test_doc_renderer.py:1371`
(Assertion innerhalb `::test_absent_block_is_noop`, `:1318`) vergleicht
`_schema_absence_defaults(block_schema) == _IC22_ABSENCE_DEFAULTS`. `_schema_absence_defaults`
(`:1114-1130`) iteriert **alle** Properties des Schema-Blocks und bildet deren `default` ab.
Eine neue Property `index-owner` mit `"default": "auto"` erzeugt dort einen **sechsten** Schlüssel
⇒ **Assertion rot**.
Diese Änderung ist in Rev. 0.8 **nirgends** registriert: nicht in T-1…T-8, nicht in
V-D1…V-D5, nicht in der „bleiben grün"-Tabelle, nicht in der Coverage-Checkliste.
**Auswirkung.** W3-6 würde `pytest tests/test_doc_renderer.py -q` nicht grün bekommen, obwohl
§17.12.4 (`:4251`) genau das als Nachweis fordert; die Aussage „T-3 ist die einzige echte
Sollwert-Änderung" (`:4234`) ist falsch.
**Korrektur.** T-3 um eine zweite Zeile ergänzen: `tests/test_doc_renderer.py:1092-1098`
`_IC22_ABSENCE_DEFAULTS`: `"index-owner": "auto"` ergänzen (Erweiterung einer Menge, keine
Absenkung). Die Formulierung „die einzige echte Sollwert-Änderung" auf „die **erste** von zwei"
korrigieren und beide Pins in der Coverage-/Nachweistabelle nennen. Vor der Freigabe ist per
grep nach weiteren Mengen-Pins zu suchen (`_EXPECTED_PROPERTIES`, `_IC22_ABSENCE_DEFAULTS`,
`_EXPECTED_CHECKS_PROPERTIES` — letztere bleibt unberührt, da `checks` keine neue Property
erhält).

---

#### RVW8-3 — Trace-Matrix ohne AC-42…AC-46 (§9.1 **und** §9.2)
**Ort:** Spec `:2487-2529` (§9.1), `:2557-2564` (§9.2), `:2566-2571` (Zählsatz), `:3061`
(§15 „Geändert"-Liste nennt §9.1 **nicht**).
**Befund.** §9.1 endet mit `AC-41` (`:2529`); für **AC-42, AC-43, AC-44, AC-45, AC-46 existiert
keine Zeile** — keine Welle, keine betroffenen Dateien, keine V-Check-Zuordnung. §9.2 führt
W3 mit „AC-12, AC-14…AC-22, AC-26, AC-27, AC-37, AC-38" (`:2559`) und W1 mit „AC-39" (`:2557`);
der Zählsatz `:2566` („W1: **10**, W2: **7**, W3: **14** …") ist unverändert. Zusätzlich ist die
**AC-21**-Zeile (`:2512`) nach P-4 weiterhin auf „`.meta-config/project.yaml` (neuer Key)"
verkürzt, obwohl AC-21 jetzt **bedingt** ist.
Damit sind die §16-Invarianten gebrochen: „Jedes AC ≥ 1 Interface Contract | §9.1 … | geprüft
(§16)" (`:3098`), „Jedes AC ≥ 1 V-Check oder explizit als `—` begründet | §9.1" (`:3099`) und
„Jede Welle W1–W8 ist durch mindestens ein AC abgedeckt" (`:2566`).
**Auswirkung.** Die normative AC→Welle-Zuordnung — die `validator` (Traceability-Audit) und der
Plan benutzen — kennt die fünf neuen AK nicht. E-13a/T-7/T-8 wellenzuordnen wird dadurch
unbelegt; die Plan-Zeile „**Ziel-AK (AC): AC-20, AC-12 (E2E), AC-38**" (Plan `:4926`) und die
W3-6-Akzeptanz stehen im Widerspruch zu AC-42…AC-45.
**Korrektur.** Fünf Zeilen in §9.1 ergänzen (Welle **W3-6** für AC-42…AC-45 → `scripts/lib/doc_renderer.py:663-711`,
`tests/test_doc_renderer.py`; **W8-4** für AC-46 → `config/project-config.schema.json:2424-2469`,
`tests/test_docs_consolidation_migration.py`; V-Check-Spalte „— (Unit-Test)" mit
Begründungsverweis wie `:2531-2536`). AC-21-Zeile um den `index-owner`-Bezug ergänzen. §9.2
(W3- und W8-Zeile), den Zählsatz `:2566-2571` und §15 „Geändert" (`:3061`) nachziehen.

---

#### RVW8-4 — Wellen-Reihenfolge von T-3/T-5/T-8 unauflösbar; W3-6-Akzeptanz unerfüllbar
**Ort:** Spec `:4155`/`:4159-4160` (E-13a), `:4234-4236` (T-3/T-5), `:4239` (T-8), `:4250`
(Nachweis „Schema … gruen inkl. **2** neuer Enum-Tests und erweiterter Property-Menge"),
`:2496` (§9.1 AC-39 → Welle **W1**).
**Befund.** Drei Änderungen sind technisch untrennbar:
* **T-8** (Schema-Property `index-owner` mit `enum`/`default`) ist Voraussetzung dafür, dass
  `docs-consolidation.index-owner` im geschlossenen Block überhaupt zulässig ist
  (`config/project-config.schema.json:2470` `additionalProperties: false`).
* **T-3** (`_EXPECTED_PROPERTIES` fünf → sechs) bricht ohne T-8 `::test_schema_block_present_and_closed`
  (`:99-103`) — so korrekt in `:4234` erkannt.
* **T-5** (`::test_index_owner_enum_accepts_both_values`) validiert eine Config mit
  `index-owner` gegen das Schema; ohne T-8 wirft `jsonschema` **ValidationError** — T-5 kann
  ohne T-8 nicht grün werden.

E-13a legt T-8 nach **W8-4** („Schema-Abschluss und Doku"), §9.1 führt AC-39 nach **W1**.
§17.12.4 stellt den Schema-Nachweis (`:4250`) aber in dieselbe Nachweisliste wie die
**W3-6-Kernlieferung** (`:4245`) und verlangt „erweiterte Property-Menge" im selben Lauf.
Unter der E-13a-Lesart ist W3-6s eigener Nachweis **unerfüllbar**; unter der anderen Lesart
(T-3/T-5/T-8 alle in W3-6) ist E-13a und die AC-39-Wellenzeile falsch. Die Spec wählt nicht.
**Korrektur.** Eine der beiden Lesarten ausdrücklich festlegen und **beide** Stellen
verknüpfen: entweder (a) „T-3, T-5, T-8 sind **eine** atomare Änderung in **W3-6**" — dann E-13a
korrigieren (W8-4 behält nur die Doku), §9.1 AC-39 auf „W1, W3-6" erweitern und den
W8-4-Hinweis streichen; oder (b) „T-3/T-5/T-8 in **W8-4**" — dann den Schema-Nachweis `:4250`
aus der W3-6-Liste nehmen, W3-6-Nachweis auf „unveränderte Property-Menge" präzisieren und
explizit festhalten, dass W3-6 den **Schema-**Teil der Ausnahme **nicht** enthält. Zusätzlich
als V-D-Befund registrieren (aktuell ist es keiner).

---

#### RVW8-5 — Threat Model Zeile (g) unvollständig; Kopier-Risiko nicht abgedeckt
**Ort:** Spec `:2923` (Zeile g), `:2925-2938` (Frage 3), `:2940-2951` (Frage 4),
`:2953-2957` (Bewertung „Alle **sechs** Bedrohungen").
**Befund.** (1) **Frage 3** enthält **keine** Gegenmaßnahme-Bullet zu (g) — die Liste endet bei
(f)/OQ8. (2) **Frage 4** enthält **keinen** Konsequenz-Eintrag zu (g) — sie führt (a), (b),
(c), (e), (f), **(d) fehlt ebenfalls** (vorbestehend). (3) Die Bewertung spricht von „**sechs**
Bedrohungen", obwohl die Tabelle jetzt **sieben** Zeilen (a…g) hat. (4) **Kernlücke:** Zeile (g)
benennt ausschließlich den Tippfehler-Pfad und die „Pflegepflicht". Das in Prüfpunkt 9
adressierte Risiko — **ein Consumer-Projekt übernimmt die Ausnahme** (Kopieren der
`project.yaml`-Zeile aus agent-meta, Übernahme einer Beispiel-Config, Scaffold eines neuen
Projekts) — wird **nirgends** behandelt. IC-26/6 argumentiert „per Konstruktion unerreichbar",
aber ausschließlich für `tests/scenarios/configs/*.project.yaml` **dieses** Repos; für ein
Downstream-Submodul mit `knowledge-engine.enabled: true` wäre die Deklaration ein
**Verweigerungszweig, der die KE-Autorität stillschweigend aufhebt** — genau der vom Auftraggeber
festgehaltene Schutz.
**Auswirkung.** Vier Fragen sind für ein Feature Pflicht; Frage 3 und 4 sind für (g) leer. Der
Ausnahme-Pfad ist der einzige, der die Autorität einer **fremden** Instanz berührt.
**Korrektur.** (i) Frage 3: Gegenmaßnahme-Bullet für (g) — namentlich der **Code-Zweig
IC-25 (1)** als einzige **garantierte** fail-closed Absicherung (die `enum` ist Konvention,
siehe RVW8-6) plus die Sichtbarkeit im Config-Diff. (ii) Frage 4: Konsequenz-Eintrag (g) —
eine kopierte Deklaration entzieht einem KE-Projekt den `docs/INDEX.md`-Pfad; Recovery ist
`index-owner` auf `auto` bzw. Entfernen der Zeile, aber bis dahin ist der Index in jedem
Sync `skipped` (grüner Log, eingefrorener Index). (iii) Bewertungsziffer auf **sieben**
korrigieren. (iv) Den Kopier-Pfad **explizit** als Restrisiko benennen und entweder eine
Gegenmaßnahme fordern (z. B. eine `validate`-/`--strict`-Meldung, wenn `index-owner` in einem
Projekt mit `knowledge-engine.enabled: true` gesetzt ist) oder als bewusst akzeptiertes Restrisiko
mit Owner und Termin führen.

---

### MINOR

#### RVW8-6 — §12.3 (g) überschätzt das Schema als geschlossenen Tippfehler-Wächter
**Ort:** Spec `:2923`; Belegspalte `:1408` (IC-13-Zeile „unbekannter Wert").
**Befund.** Die Belegzelle sagt, der Tippfehler-Pfad sei durch `enum` +
`additionalProperties: false` **geschlossen**. Gemessen ist die Schema-Validierung im Sync-Pfad
**best-effort**: `scripts/lib/config.py:342` („Schema validation … **if** jsonschema is
available"), `:372-388` („jsonschema not installed or validation error — **best-effort**",
`pass`). Die **einzige** garantierte Absicherung ist der Code-Zweig IC-25 (1) — die Spec
spezifiziert ihn und pinnt ihn in AC-44(c), sagt die Begründung aber nirgends.
**Korrektur.** In IC-25 (Fail-closed-Zweig), IC-13-Belegzeile und §12.3 (g) ergänzen: das Schema
ist Autocomplete-/Tippfehler-Konvention; die harte Zusage ist der Codepfad (nicht vertretbar
durch „Enum zu lassen", wenn `jsonschema` fehlt). `config.py:342`/`:388` als Beleg nennen.

#### RVW8-7 — AC-42 (d): Anker deckt nur die `doc-indexer/1`-Hälfte
**Ort:** Spec `:2275-2278`.
**Befund.** AC-42 (d) verlangt beide Belege — `doc-indexer/1` **und** den `docs-facts`-Block —
und belegt beide mit `doc_renderer.py:635-639`. Gemessen liegt `:635-639` im **Footer**
(`FOOTER_BEGIN_MARKER`, `facts-hash`, `generator: doc-indexer/1`, `FOOTER_END_MARKER`); der
`docs-facts`-Block entsteht bei `:629` (`_facts_section(facts)`), der Volatile-Abschnitt bei
`:631`.
**Korrektur.** Beleg auf `:629` (facts) **und** `:635-639` (Generator-ID/Footer) aufteilen.

#### RVW8-8 — Anker-Drift-Politik uneinheitlich; V-D1/V-D2-Inventar unvollständig
**Ort:** Spec `:4084` (K-4), `:4257` (V-D1), `:4258` (V-D2).
**Befund.** K-4 korrigiert zwei Anker derselben Klasse, während mindestens **elf weitere**
gemessen veraltete `spec_plan_scaffold.py`-/`sync_pipeline.py`-Anker unregistriert bleiben:
`:515` (F8 `:23`), `:528` (F20 `:24`), `:593` (NG-7 `:23`), `:1449-1450` (IC-15 `:23`/`:24` —
in V-D1(a) registriert), `:2187` (AC-22-Text `:40-44`), `:2255` (AC-38 `:49-51` — in V-D1(c)
registriert), `:2511-2513` (§9.1 AC-20 `:24, :62-68`, AC-21 `:27-44`, AC-22 `:40-44`),
`:2866` (§11.2 OQ6 `:23`), `:2968` (§13 A4 `:62-68`), `:3017` (§15 `:23` — in V-D1(b)
registriert), `:3110` (§16 `:20-24, :27-44, :46-68`), `:3161` (§17.3 CR-1 `:49-51`).
V-D2 registriert **IC-12**, nicht aber **AC-22**, das dieselben zwei Anker wiederholt
(`:2184-2187`). Damit ist der Umfang der „nächsten Korrekturrunde" unterbestimmt.
**Korrektur.** Entweder alle Anker einer Klasse in einem Durchgang korrigieren (K-4 wird dann zu
K-4a/K-4b und die Liste ist vollständig), oder eine **Auswahlregel** formulieren und anwenden
(z. B. „nur Anker in Abschnitten, die Rev. 0.8 ohnehin anfasst"), und V-D1/V-D2 um die
übrigen Fundstellen ergänzen, damit sie nicht verloren gehen.

#### RVW8-9 — AC-39: Belegquelle der fünf Properties falsch attribuiert
**Ort:** Spec `:2406-2412`.
**Befund.** „`enabled`, `index-mode`, `checks`, `sources`, `volatile-facts`
(**`.meta-config`-Ist-Stand** vor Rev. 0.8)". Diese fünf Namen sind **kein** `.meta-config`-Stand
(`.meta-config/project.yaml:398-401` trägt nur `enabled` und `checks.strict`), sondern der
**Schema-Block**-Stand (`config/project-config.schema.json:2424-2469`) bzw. der Test-Pin
(`tests/test_docs_consolidation_migration.py:45-51`).
**Korrektur.** Klammer auf „Schema-Block-Ist-Stand (`config/project-config.schema.json:2424-2469`)
und Test-Pin (`tests/test_docs_consolidation_migration.py:45-51`)" umstellen.

#### RVW8-10 — Plan-Befund zu W3-7/`sources` nicht als V-D registriert; eine Testpin-Zeile namenlos
**Ort:** Spec `:4106-4122` (E-10), `:4253-4261` (V-D1…V-D5), `:4196` (§17.12.4 Zeile 4).
**Befund.** E-10 stellt korrekt fest, dass W3-7 **nicht** durch dieses Gate blockiert ist, sondern
an `docs-consolidation.sources` hängt (belegt: `apply_fact_blocks` hat heute **keinen**
Produktionsaufrufer — `scripts/`-Grep findet nur Docstring-Erwähnungen; `docs-consolidation.sources`
wird **nirgends** im Code gelesen; `.meta-config/project.yaml:398-401` führt den Key nicht).
Plan W3-7 (`:4946-4997`) trägt die nötige Config-Zeile jedoch weder in `Files:` noch in den Steps
— eine **Planlücke**, die als Befund nirgends registriert ist und damit für die nächste
Korrekturrunde unsichtbar wird. Zusätzlich nennt §17.12.4 Zeile 4 in der Spalte „Testpin"
**keinen** Testnamen, während alle übrigen Zeilen einen nennen.
**Korrektur.** Die Planlücke als V-D-Befund (V-D6) aufnehmen: „Plan W3-7 (`:4946-4997`) führt
`docs-consolidation.sources` weder in `Files:` noch als Step; E-10 weist die Abhängigkeit korrekt
aus — die Ergänzung ist eine **Plan**-Änderung." In §17.12.4 Zeile 4 den Testnamen nennen
(`::test_index_owner_override_does_not_relax_skeleton_or_ownership`, Fall b).

---

## Ankerkatalog (gemessen am Working Tree)

| # | Anker aus dem Auftrag / der Spec | Fundstelle | gemessen | Ergebnis |
|---|---|---|---|---|
| 1 | `_index_mode_block_reason` | `scripts/lib/doc_renderer.py:663-711` | def `:663`, `return None` `:711` | ✅ ja |
| 2 | KE-Gate | `doc_renderer.py:702-703` | `if resolve_index_mode(config)[0] == "knowledge-engine": return KE_AUTHORITATIVE_REASON` | ✅ ja |
| 3 | `KE_AUTHORITATIVE_REASON` | `doc_renderer.py:277` | exakt | ✅ ja |
| 4 | Konstanten-Block | `doc_renderer.py:270-275` | `FULL/SKELETON/DEFAULT_INDEX_MODE` | ✅ ja |
| 5 | `UNKNOWN_INDEX_MODE_REASON` | `doc_renderer.py:285-299` | exakt | ✅ ja |
| 6 | `OWNERSHIP_REASON` | `doc_renderer.py:255-259` | exakt | ✅ ja |
| 7 | Aufrufer-Log (nur bei Grund) | `doc_renderer.py:810-814` | `if mode_reason is not None: … log.note` | ✅ ja |
| 8 | `sync_docs_consolidation` | `doc_renderer.py:714` | def | ✅ ja |
| 9 | Facts + Render | `doc_renderer.py:821-824` | `compute_doc_facts` / `render_docs_index` | ✅ ja |
| 10 | CREATE-Zweig | `doc_renderer.py:829-830` | `except FileNotFoundError: tag = "CREATE"` | ✅ ja |
| 11 | `unchanged`-Zweig | `doc_renderer.py:845-848` | exakt | ✅ ja |
| 12 | Besitzverweigerung | `doc_renderer.py:855-858` | exakt | ✅ ja |
| 13 | `write_checked` / Dry-Run-Tag | `doc_renderer.py:861` / `:867` | exakt | ✅ ja |
| 14 | `apply_fact_blocks` | `doc_renderer.py:183` | def | ✅ ja |
| 15 | `DOCS_GENERATOR_ID` | `doc_renderer.py:310` | exakt | ✅ ja |
| 16 | Footer (Generator-ID) | `doc_renderer.py:635-639` | Footer-Block | ⚠️ teilweise (AC-42 d) → RVW8-7 |
| 17 | `docs-facts`-Block | `doc_renderer.py:629` | `_facts_section(facts)` | ✅ ja (fehlt in AC-42 d) |
| 18 | `has_docs_tree` / `DOCS_INDEX_RELPATH` | `scripts/lib/doc_index.py:136` / `:121` | exakt | ✅ ja |
| 19 | V2 | `scripts/lib/consistency/docs_index.py:180-211` | exakt | ✅ ja |
| 20 | `DEFAULT_FALLBACK_INDEX` / `_FILE_INDEX_SKELETON` | `spec_plan_scaffold.py:28` / `:29` | exakt (**Spec-Text `:23`/`:24` veraltet**) | ✅ ja (Drift in V-D1(a)) |
| 21 | `is_file_index_skeleton` | `spec_plan_scaffold.py:41-77` | exakt | ✅ ja |
| 22 | permissive Marker-Suche | `spec_plan_scaffold.py:52-68` | Docstring-Abschnitt | ✅ ja |
| 23 | `resolve_index_mode` | `spec_plan_scaffold.py:80-97` | def `:80`, return `:97` | ✅ ja |
| 24 | `scaffold_spec_plan_dirs` / Modus-Zweig | `:100` / `:115-116` (Ende `:121`) | exakt | ✅ ja |
| 25 | deaktivierter Early-Return | `spec_plan_scaffold.py:102-104` | exakt (V-D1(c)) | ✅ ja |
| 26 | K-4 `:62-68 → :115-121`, `:40-44 → :80-97` | `spec_plan_scaffold.py` | beide gemessen | ✅ ja |
| 27 | Pipeline-Anker | `sync_pipeline.py:930/958/966/974/980/985/1139/1151` | alle exakt (V-D2) | ✅ ja |
| 28 | `knowledge.py` KE-Gate / Index-Modus | `knowledge.py:127` / `:185` | exakt | ✅ ja |
| 29 | Schema-Block `properties` | `config/project-config.schema.json:2424-2469` | 5 Properties, `additionalProperties: false` `:2470` | ✅ ja |
| 30 | Schema-Muster (Enum) | `project-config.schema.json:2430-2438` | `index-mode` | ✅ ja |
| 31 | Live-Config `docs-consolidation` | `.meta-config/project.yaml:398-401` | `enabled: true`, `checks.strict: true`; **kein** `index-owner`, **kein** `sources` | ✅ ja |
| 32 | `resolve_index_mode`-Eingaben agent-meta | `project.yaml:15` / `:69` / `:77` / `:80-81` | exakt (`false or not true` ⇒ kein Absenken) | ✅ ja |
| 33 | `docs/INDEX.md` fehlt | Glob | kein Treffer | ✅ ja |
| 34 | `_EXPECTED_PROPERTIES` (5) | `tests/test_docs_consolidation_migration.py:45-51` | 5 Einträge | ✅ ja |
| 35 | `test_schema_block_present_and_closed` | `:81` / `:99-103` | exakt | ✅ ja |
| 36 | `test_no_property_name_is_a_provider_name` | `:116` | exakt, liest Property-Namen dynamisch | ✅ ja |
| 37 | Enum-Testmuster | `:174-176` / `:179-182` | exakt | ✅ ja |
| 38 | **Zählkommentar** | `:42-44` | **Text vorhanden** | ❌ **nein** → RVW8-1 |
| 39 | `_EXPECTED_PROPERTIES`-Prüfer | `:99-103` | `set(properties) == _EXPECTED_PROPERTIES` | ✅ ja |
| 40 | **`_IC22_ABSENCE_DEFAULTS`** | `tests/test_doc_renderer.py:1092-1098`, geprüft `:1371` | **hart gepinnt, nicht in Rev. 0.8 registriert** | ❌ **nein** → RVW8-2 |
| 41 | `_KE_AUTHORITATIVE_CONFIG` (ohne Key) | `tests/test_doc_renderer.py:2481-2484` | exakt | ✅ ja |
| 42 | `_SKELETON_MODE_CONFIG` | `:2486-2488` | exakt | ✅ ja |
| 43 | `_scaffolded_root()` | `:2510-2526` | exakt | ✅ ja |
| 44 | `test_scaffold_guard_recognises_only_the_skeleton` | `:2529` | exakt | ✅ ja |
| 45 | `test_skeleton_mode_preserves_scaffold` / `…creates_no_index_at_all` | `:2559` / `:2590` | exakt | ✅ ja |
| 46 | `test_ke_authoritative_writes_no_index(_even_when_absent)` | `:2614` / `:2650` | exakt | ✅ ja |
| 47 | `_tree_snapshot`-Muster | `:2571` / `:2635` | exakt | ✅ ja |
| 48 | `test_unknown_index_mode_is_fail_closed` | `:2720-2737` | exakt | ✅ ja |
| 49 | `test_index_mode_off_permits_the_full_index` | `:2740` | exakt | ✅ ja |
| 50 | `test_stage_order_after_scaffold` (Fixture `:3064-3069` ohne Key) | `:3013` | exakt | ✅ ja |
| 51 | `test_ke_index_stays_authoritative` (Fixture `:3118-3123` ohne Key) | `:3100` | exakt | ✅ ja |
| 52 | `_e2e_config()` / `knowledge-engine: {enabled: False}` | `:3209-3238` / `:3237` | exakt → `index-owner` ist dort per Konstruktion No-op | ✅ ja |
| 53 | `test_skeleton_replaced_once` | `:3258` | exakt; Sollwert bleibt grün | ✅ ja |
| 54 | W4-3-Pin (kein `architecture/INDEX.md`) | `:3319-3320` | exakt | ✅ ja |
| 55 | `docs_consolidation_enabled` | `scripts/consistency-check.py:138` | exakt | ✅ ja |
| 56 | keine Struktur-Heuristik | `consistency-check.py:144-145` | exakt | ✅ ja |
| 57 | `DOCS_GENERATED_RELS` | `scripts/lib/generated_file_drift.py:82` | enthält `docs/INDEX.md` (E-11) | ✅ ja |
| 58 | Provider-Achse | `AGENTS.md:50`; `.opencode/skills/provider-agnostic/SKILL.md:12-18` | exakt | ✅ ja |
| 59 | V-D3(a) `AGENTS.md:247` | `AGENTS.md:246`/`:248` Roster; `:39` Platzhalter-Aussage | „Roster-Zeile" grob richtig, `:39` exakt | ⚠️ teilweise |
| 60 | `docs-consolidation.sources` im Code | `scripts/`-Grep | **kein Treffer** (E-10 korrekt) | ✅ ja |
| 61 | `apply_fact_blocks`-Aufrufer | `scripts/`-Grep | nur Docstrings, kein Produktionsaufrufer | ✅ ja |
| 62 | Schema-Validierung im Sync-Pfad | `scripts/lib/config.py:342` / `:388` | best-effort | ✅ ja (→ RVW8-6) |
| 63 | Plan W3-6 Anchors | Plan `:4926`, `:4929`, `:4931-4932`, `:4935-4937` | exakt | ✅ ja |
| 64 | Plan W3-7 `Files:`/Steps | Plan `:4946-4997` | **keine** `sources`-Config-Zeile | ✅ Messung ja (→ RVW8-10) |
| 65 | Plan-Status | Plan `status: APPROVED`, `revision: 0.7` | **kein** `pending-approval`, keine AC-42…46 | ✅ ja |
| 66 | OQ1-Record | `docs/plans/2026-09-25-docs-consolidation-oq1.md:94` / `:99`, `status: open` | exakt | ✅ ja |
| 67 | Design-Eingang | `…-design-agent-meta-exception.md:2/5/6` | `spec-id` identisch (Bundle-Konvention), `status: draft`, `revision: 0.1` | ✅ ja |
| 68 | Design K-3 zitiert `:42` | Design `:683`, `:698` | wörtlich derselbe Kommentar → widerspricht Spec | ✅ ja (→ RVW8-1) |
| 69 | Design E-13a nennt `agent-meta.config.example.yaml` | Design `:658` | Datei existiert **nicht** (V-D3(b) korrekt) | ✅ ja |
| 70 | §9.1 AC-42…AC-46 / §9.2 W3-Zeile | Spec `:2487-2529` / `:2559` | **fehlen** | ❌ **nein** → RVW8-3 |
| 71 | §12.3 (g) in Q3/Q4 | Spec `:2925-2951` | kein Bullet / kein Eintrag | ❌ **nein** → RVW8-5 |

---

## Verdikt

**`CHANGES_REQUESTED`** — 5 major, 5 minor, 0 kritisch, kein Blocker.

**Was trägt.** Die Kernarchitektur des Deltas ist sauber und vollständig begründet:
`IC-25` verengt **ausschließlich** einen Auslöser, fügt **keinen** Eigentümer hinzu
(`DECISION-2`, `K-5` bleibt zu Recht wortwörtlich stehen); `resolve_index_mode()`,
`is_file_index_skeleton()`, die Besitzregel und der `dry_run`-Vertrag bleiben unangetastet
(`IC-26/2-5`, alle vier Anker gemessen); die B2-Reihenfolge Scaffold→Generator bleibt in Kraft
(`V-D2`-Anker alle korrekt). Der Fail-closed-Zweig steht **vor** der KE-Prüfung
(`IC-25` Zweig (1)) und läuft für `null`, `None` und jeden Fremdstring in den Verweigerungszweig
— die Reihenfolge ist der richtige Vertrag (Prüfpunkt 4 bestanden). Namensfreiheit ist echt:
deklarativer Key, Feature-Name statt Repo-Name, kein `project.name`/`platforms`-Vergleich, keine
Strukturerkennung (`IC-26/8`, `AGENTS.md:50`, `SKILL.md:12-18`, `consistency-check.py:144-145` —
alles gemessen). ID-Disziplin hält: nichts umnummeriert, IC-25/26 und AC-42…46 kollisionsfrei
(`IC-16` war bereits belegt, `:197-200`). Keine stillschweigende Entscheidung: E-9…E-13 und OQ1
stehen nachweislich offen (`§11.1:2852-2859`, `§17.12.2:4087-4176`, Record `:94`/`:99`).
Der W3-7-Befund (Prüfpunkt 8) ist **inhaltlich richtig** und am Code geprüft.

**Was blockiert.** Nicht die Architektur, sondern die **Beleg- und Zuordnungsebene**: eine
falsche Messung, die eine Pflicht zur Nicht-Pflicht erklärt (RVW8-1); eine zweite harte
Sollwert-Änderung, die nicht registriert ist und W3-6 rot lässt (RVW8-2); fünf normative AK
ohne Welle in der Trace-Matrix (RVW8-3); eine unauflösbare Reihenfolge zwischen Test- und
Schemaänderung (RVW8-4); und ein Threat Model, das für seine eigene neue Bedrohung zwei von
vier Fragen unbeantwortet lässt (RVW8-5). Ein Approval-Marker-Spiegel, der ein Delta als
freigegeben ausweist, wäre ein Blocker — das ist hier **nicht** der Fall.

---

## BLOCKING_FOR_W3-6

Vor Umsetzung von W3-6 zwingend:

1. **RVW8-1** — V-D4/K-3/T-4 auf den belegten Stand korrigieren (Kommentar `:42-44` **existiert**).
2. **RVW8-2** — `_IC22_ABSENCE_DEFAULTS` (`tests/test_doc_renderer.py:1092-1098`) als zweite
   Sollwert-Änderung registrieren; Aussage „T-3 ist die einzige" zurücknehmen.
3. **RVW8-3** — §9.1/§9.2 um AC-42…AC-46 ergänzen (Wellen W3-6 / W8-4), Zählsatz und
   AC-21-Zeile nachziehen.
4. **RVW8-4** — Wellenzuordnung von T-3/T-5/T-8 **entscheiden** und E-13a, §9.1 AC-39 und den
   Schema-Nachweis `:4250` konsistent darauf abstellen.
5. **RVW8-5** — §12.3: Gegenmaßnahme **und** Konsequenz für (g) ergänzen, Bewertungsziffer
   korrigieren, Kopier-Pfad als Restrisiko benennen.
6. **RVW8-6** — Fail-closed-Begründung um den best-effort-Charakter der Schema-Validierung
   (`config.py:342`/`:388`) präzisieren.
7. **Freigabe von P-1…P-5 durch den Nutzer** — der Delta-Umfang bleibt bis dahin nicht
   umsetzbar (Frontmatter `pending-approval:`, Kopfblock `:158-165`).

## CAN_RUN_IN_PARALLEL

Ohne Berührung des Deltas, ohne Konflikt mit den Findings:

- **W0-2** (Ledger-Writer, `W2-9`/`plan_identity.py`) — berührt `scripts/lib/plan_*.py`, nicht `doc_renderer.py`.
- **W1-9/W1-10-Rest** (`config.py`-Snippets, Beispiel-Configs) — **keine** `docs-consolidation`-Zeile und
  **kein** Schema-Block (V-D3(b)/E-13 belegt: beide Beispiel-Configs führen den Block nicht).
- **W2-7/V4-Registrierung** (`consistency-check.py`, `docs_links.py`) — gemeinsames Gate
  `consistency-check.py:138` wird **nicht** angefasst.
- **W2-8** (Entkopplung der zwei roten Volltests) — andere Dateien.
- **W5-1…W5-3-Content-Arbeit** ohne die `git mv`-Wellen — greifen `knowledge/**`, nicht `docs/INDEX.md`.
- **Reine Lese-/Zähl-Nachweise**: `bash tests/scenarios/run.sh 50 51 52 54 55 56`,
  `git check-ignore -q docs/INDEX.md`, `python3 scripts/sync.py --validate` (nur als
  Ist-Aufnahme, **kein** Sync mit Schreibwirkung).
- **Doku-Artefakte** (`docs/REQUIREMENTS.md`, `docs/guides/**`) ohne `docs/INDEX.md`-Generator.

**Nicht parallel** zu W3-6: jedes `scripts/lib/doc_renderer.py`, `scripts/lib/spec_plan_scaffold.py`,
`tests/test_doc_renderer.py`, `tests/test_docs_consolidation_migration.py`,
`config/project-config.schema.json`, `.meta-config/project.yaml`.
