---
spec-id: SPEC-ROUTING-LANGUAGE-779-780-2026-11-11
title: Routing-Sprache und Keyword-Hygiene (#779 Rest + #780) — Spec
status: APPROVED
date: 2026-11-22
approval: "Nutzergo 22.11 — Spezifikation auf Basis des freigegebenen Phasenplans 2026-11-11-phase-h-context-eval.md nachgetragen, keine neue Entscheidung"
related-issue: ["#779", "#780"]
basis: docs/superpowers/plans/2026-11-11-phase-h-context-eval.md (Task 11, Zeilen 284-291)
---

# Routing-Sprache und Keyword-Hygiene (#779 Rest + #780) — Spec
> Status: APPROVED (Nutzergo 22.11 — Spezifikation auf Basis des freigegebenen Phasenplans 2026-11-11-phase-h-context-eval.md nachgetragen, keine neue Entscheidung)
> Datum: 2026-11-22 | Ist-Anker: `chore/phase-h-bundle 87564958` (alle file:line-Belege gegen diesen Stand neu gemessen) | Plan: `docs/superpowers/plans/2026-11-11-phase-h-context-eval.md`, Task 11 (Z. 284-291)
> Entscheidungen: 34 / D-H3 (Z. 130), 34 / D-H5 (Z. 134) | Ausgangspunkt: Abweichung Nr. 7/8 (Z. 104-105) | Klasse: M | Gate: Task 11 → Tasks 12/13

## Problem / Ziel / Nicht-Ziele

**Problem.** Der Generator-Teil von #780 (Design C) ist gebaut: `_select_examples` löst sprachgetaggte `examples` auf (`scripts/lib/delegation_table.py:229-271`), der Docstring nennt den Stand aber selbst `passthrough-only until bilingual data exists` (`:253-255`). Offen sind die dokumentierte kanonische-Keyword-Regel (AC1), die DE/EN-Beispieldaten (AC3) und der Guard gegen sprachspezifische Keywords (AC4). Aus #779 bleiben IT-2 (`provider-expert` ohne Registrierung) und IT-4 (DE-Eingabe vs. sprachliche Keywords) offen; IT-1/IT-5 sind behoben, IT-3/IT-6/IT-7 sind per Test belegt. Ohne eingefrorene Allowlist kann die kanonische Keyword-Schicht durch neue Umlaut-/Stoppwort-Keywords wachsen; ohne Registrierung bleibt `provider-expert` aus der Adressierbarkeit ausgeschlossen.

**Ziel.** Implementierbare Verträge für die Plan-Tasks 12 und 13: kanonische-Keyword-Regel mit eingefrorener Allowlist (D-H3), Guard-Test, DE/EN-Beispieldaten für Pilotrollen, Registrierung von `provider-expert` als `name_only` (D-H5) und Nachweis, dass keine Routing-Coverage verloren geht. Alle Aussagen stammen aus dem freigegebenen Phasenplan; diese Spec trifft keine neue Produktentscheidung.

**Nicht-Ziele.**
- Keine Übersetzung aller 88 Keyword-Rollen — nur Pilotrollen nach dem Kriterium in S3.
- Keine Erweiterung von `config/routing-language.yaml:keyword_allow` (17 Einträge); der bestehende Ratchet darf nur schrumpfen.
- Keine Änderung an `KNOWN_KEYWORD_OVERLAPS` (9 Tokens) oder `KNOWN_EXAMPLE_OVERLAPS` (`{}`).
- Kein Eingriff in den Generator (`_select_examples`, `get_routing_rules`), in `scripts/lib/agents.py` oder in Provider-Config-Dateien; Design C bleibt unverändert (AC2).
- Keine REQ-ID-Formatarbeit (#1167, Tasks 19-21) — siehe Abgrenzung am Ende.
- Keine Implementierung; dieses Dokument spezifiziert nur. Keine closing keywords in Commit-/PR-Texten (Plan Z. 89).

### Ist-Tabelle IT-1..IT-7 (Stand 87564958)

| IT | Issue-Befund | Status | file:line-Beleg | Wirkung auf Tasks 12/13 |
|---|---|---|---|---|
| IT-1 | `openscad-developer` ohne Routing | behoben | `config/role-defaults.yaml:803-820` (`routing:` :809, `routing_patterns:` :811, `keywords:` :813-817, `examples:` :818-820); `tests/test_routing_tool_definitions.py:75-78` | keine Änderung; AC5 hält die 88 Keyword-Rollen |
| IT-2 | `provider-expert` verwaist | offen → hier nach D-H5 entschieden | `agents/1-generic/provider-expert.md:1-6` (Kopfkommentar `INTENTIONALLY EXCLUDED FROM ROUTING: Base template only`); `config/role-defaults.yaml`: 0 Treffer; `scripts/lib/frontmatter.py:56` (`WRAPPER_TEMPLATES = frozenset({"provider-expert"})`) | S4: Eintrag `addressability: name_only` + `name_only_reason` |
| IT-3 | 9 mehrdeutige Keywords, kein Tie-Break | behoben (dokumentierte Ausnahmen) | `tests/test_routing_overlap.py:28-48` (9 Tokens: `a11y`, `accessibility`, `architektur`, `audit`, `design`, `post-mortem`, `refactoring`, `schema`, `se leaf`), :96-112; `scripts/lib/consistency/active_set_refs.py:408-434` (INFO `routing.keyword-overlap`); `tests/test_routing_keyword_overlap_check.py:36-58` | AC4: Exception-Set bleibt unverändert |
| IT-4 | DE-Eingabe vs. sprachliche Keywords / keine DE-Beispieldaten | offen (Daten) | `config/role-defaults.yaml:189-190` (flache Liste), 88 flache `examples:`-Listen (`:37` … `:2389`); `scripts/lib/delegation_table.py:236-255` (Design-C-Docstring, :253-255 „passthrough-only"); `tests/test_routing_keyword_overlap_check.py:67-99` | AC3: Pilotrollen auf `examples: {Deutsch: [...], English: [...]}` |
| IT-5 | Keywords doppelt (`routing.intent_keywords`) | behoben | `tests/test_routing_tool_definitions.py:47-57`; `config/role-defaults.yaml` ohne `intent_keywords` | AC1: Single-Source `routing_patterns.keywords` bleibt |
| IT-6 | kein Coverage-Test | behoben | `tests/test_role_addressability_coverage.py:1-9`, :24-25 (`_EXPECTED_TOTAL = 102`, `_EXPECTED_DISTRIBUTION = {"keyword": 88, "name_only": 13, "excluded": 1}`) | AC5: Pins auf 103 / 88/14/1 anheben |
| IT-7 | kein Overlap-Detektor | behoben | `tests/test_routing_overlap.py:1`, :85-156; `tests/test_routing_keyword_overlap_check.py:1,36-108` (Inhalte in dieser Spec gelesen — Plan-Lücke Z. 469 geschlossen) | AC4: beide Tests bleiben grün |

## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)

Alle Anker gegen `chore/phase-h-bundle 87564958` gemessen. Python 3.9-kompatibel; keine Provider-Namensverzweigung.

### S1 — Kanonische-Keyword-Regel und eingefrorene Allowlist (AC1, D-H3)

- **Ist, Mechanismus (unverändert):** `config/routing-language.yaml:1-43` — `keyword_allow` (`:9-43`) mit **17** Einträgen mit je einem `keyword`-Feld (String) und einem `reason`-Feld (String) (Zeilen 10-42); Ratchet-Kommentar `:3-8`. `tests/test_routing_keywords_language_neutral.py:23` `PHASE0_ALLOW_MAX = 17`; `:24` `_UMLAUT_RE = re.compile("[äöüßÄÖÜ]")`; `:25-29` `_STOPLIST` (26 Wörter: `und, oder, der, die, das, mit, für, fuer, nicht, bitte, ein, eine, einen, zum, zur, von, dem, den, des, auf, aus, bei, nach, wie, ist, wird`); `:36-45` `find_german_keywords(keywords_by_role: dict, allow: set) -> list` (Tokenisierung `re.findall(r"[^\W\d_]+", str(kw).casefold())`; „deutsch" bei Umlaut-Treffer **oder** Schnitt mit `_STOPLIST`, sofern nicht in `allow`); `:63-65` Test gegen echte Rollen; `:68-74` Reason/Stale/Unique; `:77-79` Ratchet `len(keyword_allow) == PHASE0_ALLOW_MAX`.
- **Soll (Doku):** In `docs/guides/framework-reference.md` (bisher 10 Überschriften, `:1-260`; kein Routing-Absatz in `docs/guides/`) neuer Absatz `## 7. Routing-Sprache und Keywords` mit drei Aussagen: (a) `routing_patterns.keywords` sind kanonisch und sprachneutral; (b) sprachliche Nuance liegt ausschließlich in `routing_patterns.examples` als `{"Deutsch": [...], "English": [...]}` (Beleg: `scripts/lib/delegation_table.py:236-255`); (c) die 17 Einträge in `config/routing-language.yaml:keyword_allow` sind die eingefrorene Ist-Menge („bestehende DE-Keywords bleiben erlaubt"), neue Umlaut-/Stoppwort-Keywords sind verboten, die Liste darf nur schrumpfen. Die Zieldatei ist vom Plan gefordert (`Zieldatei in der Spec festlegen`, Task 11 Z. 288) und hiermit festgelegt.
- **Fehlerpfade:** keine (reine Doku). Insbesondere darf Task 12 `config/routing-language.yaml` nicht erweitern; ein 18. Eintrag würde `test_allowlist_only_shrinks` (`:77-79`) rot färben.

### S2 — Guard-Test gegen sprachspezifische Keywords (AC4)

- **Soll:** Neue Datei `tests/test_routing_language_guard.py` (Plan Task 12, Z. 293-301). Keine Duplizierung der Detektor-Logik: `find_german_keywords`, `_UMLAUT_RE`, `_STOPLIST` und `PHASE0_ALLOW_MAX` werden aus `tests/test_routing_keywords_language_neutral.py:23-29,36-45` importiert; `allow` = die 17 `keyword`-Werte aus `config/routing-language.yaml:9-43`.
- **Consumes:** `scripts.lib.roles.load_roles_config(_AGENT_META_ROOT)["roles"]` (`scripts/lib/roles.py:52-53`; Muster `tests/test_routing_tool_definitions.py:29,47-49`); `scripts.lib.delegation_table._select_examples(examples: object, language: str, *, role: str = "", info_sink: list[str] | None = None) -> list[str]` (`scripts/lib/delegation_table.py:229-235`).
- **Testsignaturen (fail zuerst):**
  - `test_keywords_are_canonical() -> None`: `find_german_keywords(_keywords_by_role(), allow) == []`; injiziertes „Prüfen" ohne Allowlist ist rot, mit Allowlist grün (Muster `tests/test_routing_keywords_language_neutral.py:53-61`); zusätzlich `len(allow) <= PHASE0_ALLOW_MAX` (17). Die 17 bestehenden DE-Keywords bleiben erlaubt (D-H3).
  - `test_examples_language_variants_resolve() -> None`: für jede Rolle mit dict-`examples` liefern `_select_examples(examples, "Deutsch")` und `_select_examples(examples, "English")` je eine nicht-leere Liste.
  - `test_keyword_coverage_unchanged() -> None`: Anzahl Rollen mit nicht-leerem `routing_patterns.keywords` ≥ **88** (Stand 87564958: 88 `keywords:`-Blöcke in `config/role-defaults.yaml`, deckungsgleich mit `tests/test_role_addressability_coverage.py:25`).
- **Fehlerpfade:** neu injiziertes Umlaut-/Stoppwort-Keyword außerhalb der Allowlist → `test_keywords_are_canonical` rot; gewachsene Allowlist → rot; leere Sprachvariante → `test_examples_language_variants_resolve` rot; Rückgang unter 88 → `test_keyword_coverage_unchanged` rot. `KNOWN_KEYWORD_OVERLAPS` (9) und `KNOWN_EXAMPLE_OVERLAPS` (`{}`, `tests/test_routing_overlap.py:28-55`) werden nicht verändert.

### S3 — DE/EN-Beispiele für Pilotrollen (AC3)

- **Ist:** alle 88 Rollen mit `routing_patterns` haben flache `examples:`-Listen (Beispiele `config/role-defaults.yaml:189-190`, `:819-820`); 0 Mapping-Rollen. Der Generator unterstützt das Mapping bereits (`scripts/lib/delegation_table.py:257-271`), die Testdaten liegen in `tests/test_routing_tool_definitions.py:219-275` und `tests/test_routing_keyword_overlap_check.py:67-108` vor.
- **Soll (Task 13):** für die Pilotrollen wird `routing_patterns.examples` von der flachen Liste auf ein sprachgetagtes `examples`-Mapping mit den Schlüsseln `Deutsch` und `English` umgestellt, das je mindestens einen Beispielsatz enthält. `routing_patterns.keywords` jeder Pilotrolle bleibt byte-identisch (S1/AC1).
- **Auswahlkriterium (aus dem Plan, keine Rollenliste):** Der Plan nennt keine konkreten Pilotrollen (Task 11 Z. 288 „Pilotrollen fuer DE-Beispiele", Task 12 Z. 296 „fuer jede Rolle mit dict-`examples`", Task 13 Z. 305 „Pilotrollen laut Spec"). Es gilt daher ausschließlich das strukturelle Kriterium: Pilotrolle ist eine Rolle mit bereits vorhandenem `routing_patterns`-Block und flacher `examples`-Liste (Stand: 88 Rollen, `config/role-defaults.yaml`), die in Task 12/13 auf das sprachgetaggte Mapping umgestellt wird. Namen und Anzahl werden nicht in dieser Spec festgelegt; der Implementierungstask dokumentiert seine Auswahl im Task-Kontext. Die ACs formulieren deshalb über die Struktur („jede Rolle mit dict-`examples`"), nicht über eine Rollenliste.
- **Fehlerpfade:** unbekannter Sprachschlüssel → deterministischer Fallback auf die erste Listen-Variante plus genau eine INFO `routing.examples-language-fallback` mit Rollenname (`scripts/lib/delegation_table.py:249-268`; Tests `tests/test_routing_keyword_overlap_check.py:67-78,81-99,102-108`); ohne `role` oder bei Alias (z. B. `en`) kein Log (`:102-108`). Dieses Verhalten bleibt unverändert.

### S4 — Registrierung von `provider-expert` als `name_only` (AC5, D-H5)

- **Ist:** `agents/1-generic/provider-expert.md:1-6` erklärt die Rolle zur reinen Wrapper-Basis (`INTENTIONALLY EXCLUDED FROM ROUTING`, `No role-defaults.yaml entry by design`, Plattform-Overrides via `based-on:`); `config/role-defaults.yaml` enthält 0 Treffer; `scripts/lib/frontmatter.py:56` führt sie in `WRAPPER_TEMPLATES`.
- **Soll (Task 13):** neuer Eintrag in `config/role-defaults.yaml` mit `routing: {addressability: name_only}` und einem nicht-leeren `name_only_reason`. Feldmuster: `config/role-defaults.yaml:107-108` (`intern-developer`) bzw. `:158-159` (`principal-developer`). Kein `routing_patterns`-Block (Regel `tests/test_role_addressability_coverage.py:4-8`: nur `keyword`-Rollen dürfen Patterns tragen); `_NAME_ONLY_PATTERN_EXCEPTIONS` bleibt `frozenset()` (`:29`). Der Begründungstext wird aus dem Kopfkommentar `provider-expert.md:2-6` abgeleitet (Wrapper-Basis für plattformspezifische `*-expert`-Overrides, keine eigene Routing-Fläche, nur explizite Namens-Delegation); die genaue Formulierung ist Implementierungsdetail und keine neue Entscheidung.
- **Konsequenz (mechanisch):** `tests/test_role_addressability_coverage.py:24-25` wird von `102 / {keyword: 88, name_only: 13, excluded: 1}` auf `103 / {keyword: 88, name_only: 14, excluded: 1}` angehoben. `excluded` bleibt genau `orchestrator`; die 88 Keyword-Rollen bleiben unverändert.
- **Fehlerpfade:** `name_only` ohne `name_only_reason` → `tests/test_role_addressability_coverage.py:7-8` rot; `routing_patterns` an einer `name_only`-Rolle → Ratchet-Verletzung (`:29`) rot.

## Datenfluss

- **Sprachwahl:** `variables.COMMUNICATION_LANGUAGE` (`.meta-config/project.yaml:184` = `Deutsch`; Schema `config/project-config.schema.json:235`) → `scripts/lib/agents.py:328` (`language=variables.get("COMMUNICATION_LANGUAGE", "en")`) → `get_routing_rules(...)` (`scripts/lib/delegation_table.py:289-300`) → `_select_examples` (`:229-271`) → `examples` im Rule-Dict → `build_routing_tool_definition` (`scripts/lib/agents.py:276-286`) → gerenderte Routing-Tool-Definition je Provider. `keywords` durchlaufen denselben Pfad sprachneutral.
- **Keyword-Kanonizität:** `config/role-defaults.yaml::routing_patterns.keywords` → `load_roles_config` (`scripts/lib/roles.py:53`) → `find_german_keywords` (`tests/test_routing_keywords_language_neutral.py:36-45`) gegen `config/routing-language.yaml:keyword_allow` (17) → neuer Guard `tests/test_routing_language_guard.py`; Doku-Regel in `docs/guides/framework-reference.md`.
- **Overlap (unverändert):** `load_roles_config` → `_collect_overlaps` (`tests/test_routing_overlap.py:62-68`, Normalisierung `.strip().casefold()`) → `KNOWN_KEYWORD_OVERLAPS` (9) / `KNOWN_EXAMPLE_OVERLAPS` (`{}`) → `check_keyword_overlap` (`scripts/lib/consistency/active_set_refs.py:408-434`, INFO, nur `ActiveSet.routable`) → `tests/test_routing_keyword_overlap_check.py` (Fixtures `pall`/`p10`).
- **Adressierbarkeit:** neuer `provider-expert`-Eintrag → `load_roles_config` → Coverage-Counts (103 / 88/14/1) und `name_index` → `_routing_name_only_entries` (`scripts/lib/agents.py:423-430`) → `name_only`-Anzeige mit Reason im gerenderten Routing.

## Acceptance Criteria (nummeriert, testbar)

Given/When/Then, je AC mindestens einem Vertrag S1-S4 zugeordnet.

**AC1 — dokumentierte kanonische-Keyword-Regel (S1).**
Given `docs/guides/framework-reference.md` ohne Routing-Absatz, When Task 12 den Absatz `## 7. Routing-Sprache und Keywords` ergänzt hat, Then enthält er drei explizite Aussagen: Keywords kanonisch/sprachneutral; Sprachvarianten nur in `examples` als `{"Deutsch": [...], "English": [...]}`; `config/routing-language.yaml:keyword_allow` (17 Einträge) ist eingefroren und darf nur schrumpfen. Beleg der Regel: `scripts/lib/delegation_table.py:236-255`. `config/routing-language.yaml` selbst ist unverändert (weiter 17 Einträge, `PHASE0_ALLOW_MAX = 17`).

**AC2 — Generator-Design C bleibt unverändert (S1/S3, Ist-Stand).**
Given eine Rolle mit dict-`examples` nach dem Muster `tests/test_routing_tool_definitions.py:219-275`, When `get_routing_rules(..., language="Deutsch")` und `language="English"` aufgerufen werden, Then liefert `_select_examples` je die passende nicht-leere Liste und `keywords` sind in beiden Sprachen identisch; bei unbekanntem Sprachschlüssel folgt der deterministische Fallback auf die erste Variante mit genau einer `routing.examples-language-fallback`-INFO pro Rolle (`tests/test_routing_keyword_overlap_check.py:67-78,81-99,102-108`). `scripts/lib/delegation_table.py` und `scripts/lib/agents.py` sind in Tasks 12/13 nicht geändert.

**AC3 — DE/EN-Beispiele für Pilotrollen (S3).**
Given die Pilotrollen nach dem Kriterium in S3 (vorhandener `routing_patterns`-Block mit flacher `examples`-Liste), When Task 13 deren `examples` auf `{Deutsch: [...], English: [...]}` umgestellt hat, Then gilt für jede Rolle mit dict-`examples`: `get_routing_rules(language="Deutsch")` liefert andere, je nicht-leere Beispiele als `language="English"`, während `keywords` identisch bleiben. Ein DE-Projekt (`COMMUNICATION_LANGUAGE: Deutsch`) erhält DE-Beispiele, ein EN-Projekt EN-Beispiele — aus derselben Keyword-Quelle. `python3 -m pytest tests/test_routing_tool_definitions.py -k pilot -q` ist grün (Plan Task 13 Step 1/4).

**AC4 — Guard-Test und eingefrorene Allowlist (S2).**
Given `tests/test_routing_language_guard.py` mit `allow` = den 17 Werten aus `config/routing-language.yaml:9-43` und `PHASE0_ALLOW_MAX = 17`, When `python3 -m pytest tests/test_routing_language_guard.py -q`, Then: (a) `test_keywords_are_canonical` ist grün mit den 17 bestehenden DE-Keywords und rot bei injiziertem neuem Umlaut-/Stoppwort-Keyword außerhalb der Allowlist sowie bei `len(allow) > 17`; (b) `test_examples_language_variants_resolve` ist grün für alle Rollen mit dict-`examples`; (c) `test_keyword_coverage_unchanged` ist grün bei ≥ 88 Keyword-Rollen. Zusätzlich bleiben `python3 -m pytest tests/test_routing_overlap.py tests/test_routing_keyword_overlap_check.py -q` grün: 9 INFO-Findings `routing.keyword-overlap` im `pall`-Fixture und 0 `KNOWN_EXAMPLE_OVERLAPS`; die 9 Tokens und `{}` werden nicht erweitert.

**AC5 — kein Coverage-Verlust, `provider-expert` registriert (S4).**
Given `tests/test_role_addressability_coverage.py:24-25` mit den alten Pins `102 / {keyword: 88, name_only: 13, excluded: 1}`, When `config/role-defaults.yaml` den Eintrag `provider-expert` mit `addressability: name_only` und nicht-leerem `name_only_reason` enthält, Then lauten die Pins `103 / {keyword: 88, name_only: 14, excluded: 1}`, die 88 Keyword-Rollen sind unverändert, `excluded` ist weiter genau `orchestrator`, `provider-expert` trägt kein `routing_patterns` und `_NAME_ONLY_PATTERN_EXCEPTIONS` bleibt leer. `python3 -m pytest tests/test_routing_tool_definitions.py tests/test_routing_lines_compact.py -q` und `python3 scripts/sync.py --validate` sind grün; ac01-/Budget-Tests laufen und werden bei Output-Änderung per Helper (Plan Task 6) mit dokumentiertem Grund neu gepinnt (Plan Task 13 Step 4).

Anzahl AC: 5 (AC1→S1, AC2→S1/S3, AC3→S3, AC4→S2, AC5→S4). Jede AC ist testbar und mindestens einem Interface Contract zugeordnet.

## Offene Fragen + Risiken

**Offene Fragen (aus dem Plan übernommen, keine neue Entscheidung).**
- **O1 — Pilotrollen-Namen:** offen gelassen vom Plan (Z. 288/296/305). Diese Spec legt nur das strukturelle Auswahlkriterium fest (S3); Namen/Anzahl werden im Implementierungstask dokumentiert. Keine User-Rückfrage nötig, da die ACs strukturell formuliert sind.
- **O2 — Doku-Zieldatei:** Plan verlangt „Zieldatei in der Spec festlegen"; gewählt `docs/guides/framework-reference.md` (kein Regex-/Routing-Absatz in `docs/guides/`, 10 Überschriften `:1-260`). Plan-delegierte Wahl, keine Produktentscheidung.
- **O3 — `name_only_reason`-Wortlaut:** aus `provider-expert.md:2-6` abgeleitet; genaue Formulierung Implementierungsdetail (S4).

**Risiken.**
- R1: Task 12 erweitert versehentlich `keyword_allow` (17 → 18) — bricht den Ratchet. Mitigation: AC4 (`len(allow) <= PHASE0_ALLOW_MAX`), bestehender Test `tests/test_routing_keywords_language_neutral.py:77-79`.
- R2: Neue DE-Beispielsätze erzeugen unkontrollierte Example-Overlaps (`KNOWN_EXAMPLE_OVERLAPS` war `{}`, `tests/test_routing_overlap.py:55`). Mitigation: AC4 verlangt unveränderte Exception-Menge; neue Kollision ist zu schärfen, nicht zuzulassen (Policy `:9-12`).
- R3: Der `provider-expert`-Eintrag bricht die Coverage-Pins `tests/test_role_addressability_coverage.py:24-25`. Mitigation: AC5 hebt sie mechanisch auf 103 / 88/14/1 an.
- R4: Gerenderter Orchestrator-Output ändert sich durch die neuen Beispiele → ac01-/Budget-Hash-Drift (Plan Task 13 Step 4). Mitigation: Re-Pin per Helper aus Plan Task 6 mit Grund im Kommentar; kein „Neu-Einfrieren um einen roten Test zu löschen" (Plan Z. 93).
- R5: `language` defaultet auf `"en"` (`scripts/lib/agents.py:328`), während `.meta-config/project.yaml:184` `Deutsch` setzt. DE-Beispiele erscheinen nur bei gesetzter Variable; unverhaltensgeändert durch diese Spec.

**Abweichungen zum Plan / Anker-Drift (Spec gewinnt für Task 11; Plan nachziehen).**
- D1: Plan verweist auf `tests/test_routing_overlap.py` / `tests/test_routing_keyword_overlap_check.py` als „Inhalt nicht gelesen" (Z. 104, Z. 469). Inhalt jetzt gelesen; Befund floss in IT-3/IT-7 und AC4 ein (9 Tokens, `{}` Example-Overlaps, Fallback-Log pro Rolle).
- D2: `openscad-developer`-Anker im `docs/specs/2026-10-11-context-profiles-spec.md` (`:875-883`) gegen 87564958 neu gemessen: `config/role-defaults.yaml:803-820`, `routing_patterns:` :811 (keywords :813-817, examples :819-820).
- D3: Anker „`language` aus `COMMUNICATION_LANGUAGE` durchgereicht (`agents.py:284`)" im `docs/specs/2026-10-11-context-profiles-spec.md` ist veraltet; gegen 87564958: `scripts/lib/agents.py:328`.
- D4: `provider-expert.md`-Kopfkommentar im `docs/specs/2026-10-11-context-profiles-spec.md` (`:1-5`) endet gegen 87564958 bei `:6`.
- D5: Plan Task 12 nennt „DE-Stoppwoerter (Liste in der Spec)"; keine neue Liste erfunden — die eingefrorene Liste ist die vorhandene `_UMLAUT_RE` + `_STOPLIST` (`tests/test_routing_keywords_language_neutral.py:24-29`) samt 17 `keyword_allow`-Einträgen (`config/routing-language.yaml:9-43`). Damit keine neue Entscheidung.
- D6: Plan nennt für `test_keyword_coverage_unchanged` „Zahl aus Spec"; gegen 87564958 gemessen: 88 Rollen mit `routing_patterns.keywords` (88 `keywords:`-Blöcke, deckungsgleich mit `tests/test_role_addressability_coverage.py:25`).
- D7: Plan Task 11 Z. 288 sagt „Abgrenzung zu #1167 nicht noetig"; zur Vollständigkeit dennoch eine knappe Abgrenzung (siehe nächster Absatz) — kein fachlicher Eingriff in #1167.

**Nicht verifiziert (ehrlich).**
- Keine Tests ausgeführt, kein `sync.py`-Lauf, kein `git`-Befehl (Spec-Worker ohne Shell). Alle PASS/FAIL-Erwartungen sind Planwerte plus statisch gelesene Belege.
- Issue-Texte (#779/#780) nicht direkt gelesen; IT-/AC-Nummerierung aus dem Plan und `docs/specs/2026-10-11-context-profiles-spec.md:311-317,2264` übernommen.
- Anzahlen (17 Allowlist-Einträge, 88 Keyword-Rollen, 9 Overlap-Tokens) statisch aus Dateiinhalt und Test-Pins gezählt, nicht per Python-Ausführung bestätigt.
- `.tmp/issues/` nicht vorhanden; keine further issue-lokalen Details einbezogen.

**ADR (Kontext / Entscheidung / Konsequenz — alle aus dem Plan übernommen, keine neue Entscheidung).**
- **ADR-R1 (D-H3, Keyword-Freeze):** Kontext — Design C hält Keywords kanonisch; 17 deutsche Keywords sind historisch gewachsen (`config/routing-language.yaml:9-43`). Entscheidung — DE-Keywords bleiben, der Guard friert die Menge ein; `keyword_allow` darf nur schrumpfen. Konsequenz — neue sprachspezifische Keywords sind blockiert (AC4), Sprachnuance wandert in `examples` (AC3), kein Eval-Lauf nötig.
- **ADR-R2 (D-H5, `provider-expert`):** Kontext — Wrapper-Basis ohne Registrierung (`provider-expert.md:1-6`, `frontmatter.py:56`); IT-2 offen. Entscheidung — Registrierung als `addressability: name_only` mit `name_only_reason`. Konsequenz — explizite Namens-Delegation möglich, kein Keyword-Routing, Coverage-Pin 103 / 88/14/1 (AC5).
- **ADR-R3 (Pilotkriterium / Doku-Ziel):** Kontext — Plan lässt Pilotrollen und Doku-Zieldatei offen (Z. 288/288). Entscheidung — strukturelles Kriterium (S3) und `docs/guides/framework-reference.md` (S1). Konsequenz — ACs ohne feste Rollenliste, Reviewbarkeit der Doku-Regel; keine Produktentscheidung.

**Abgrenzung zu #1167.** Diese Spec betrifft ausschließlich Routing-Keywords und sprachgetaggte Beispiele (#779 IT-2/IT-4, #780). #1167 (Tasks 19-21) behandelt das REQ-ID-Format in Templates, Validator und Presets; Dateimengen und Regeln sind disjunkt. Der Plan erklärt eine Abgrenzung für nicht nötig (Z. 288); dieser Absatz dient nur der Vollständigkeit und ändert nichts an #1167.

## Trace-Anker: spec-id: SPEC-ROUTING-LANGUAGE-779-780-2026-11-11
