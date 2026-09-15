---
pipeline_stages:
  implement: 1
---

# Implementierungsplan — Framework-Support für `reference_standards`

> Status: geplant

**Spec:** `docs/specs/2026-09-15-reference-standards-design.md` (Status **APPROVED 2026-09-15**)
> Trace-Anker: `spec-id: SPEC-REFERENCE-STANDARDS-2026-09-15`
> Review: `docs/specs/2026-09-15-reference-standards-review.md` (Verdict **APPROVED**; Findings F-01…F-08 eingearbeitet, F-01 Opencode-Re-Klassifikation, F-03 Schema-Doppelkey).
> Verwandte Spec (gleiche Seams, keine Supersession): `SPEC-CONTEXT-FILE-MODES-2026-09-13` (`docs/specs/2026-09-13-context-file-modes-design.md`) — Frontmatter-Render, Per-Provider-Transformation und Consistency-Registrierung werden wiederbenutzt; deren Vokabular bleibt unangetastet.

**Goal:** Das optionale Agent-Frontmatter-Feld `reference_standards` (Liste von Strings, `<STANDARD>[@<version>][#<section>]`) framework-seitig erkennen (IC-01), strukturell validieren (IC-02) und provider-agnostisch per Default aus **jeder** generierten Provider-Frontmatter strippen (IC-03) — ohne Provider-Namens-Branch, mit Config-Opt-in „keep“ und ohne Provenance-Leak (IC-04); dazu der minimale Freshness-Schutz für `catalog.generated.yaml` (IC-06).
**Architecture:** Zwei bestehende Seams werden erweitert, keine neue Schnittstelle gezogen: (1) Der Frontmatter-Render in `scripts/lib/frontmatter.py` bekommt eine neutrale Feld-Konstante, einen Accessor und eine **Quiet-Strip**-Menge, die gestrippte Keys aus dem `agent-meta-provenance`-Kommentar heraushält. (2) Die Inline-Strip-Expression in `provider_transform.py:385-388` wird durch **einen** Config-Resolver in `providers.py` ersetzt (`FRONTMATTER_STRIP_DEFAULTS` ∪ Projekt-Kanal ∪ ai-providers-Kanal, minus Keep-Kanäle); das wirkt für alle 9 Provider identisch, die `frontmatter-mechanism`-Pfade (`opencode-native`, `codex-toml`) bleiben unverändert. Der Consistency-Check ist ein additives Modul im vorhandenen Registrierungspfad.
**Tech Stack:** Python 3.9 (Stdlib only, `from __future__ import annotations`, `typing`-Klammern, keine PEP-604-Union-Syntax in neuen Modulen), JSON Schema (`config/project-config.schema.json`), YAML (`config/ai-providers.yaml`, Frontmatter), Markdown, pytest (`tomllib`/`tomli`-Fallback nur in Tests für AC-02), `rtk`-präfigierte Kommandos.

**Estimated effort:** an `effort-estimator` delegieren (Text-Referenz, **kein** Tool-Call, kein eigenes Zahlenwerk in diesem Plan) — erwartet wird eine **M/Bounded**-Schätzung gemäß Spec-Klassifikation (6 Produktionsdateien ohne Tests/Doku).

## Global Constraints

- **Policy (verbindlich, User-Approval 2026-09-15):** `reference_standards` wird per Default aus **jedem** Provider gestrippt. Per-Provider-„keep“ ist ausschließlich Config-Sache (`frontmatter-keep-fields`) — kein zweiter Code-Pfad. **`keep` schlägt `strip`** (IC-03/IC-05).
- **Provider-Agnostik:** Kein Provider-Namens-Literal und kein `if provider == …` in neuem/geändertem Code; jede Differenz über Config-Keys/Resolver-Ergebnis. `tests/test_provider_agnostic_dispatch.py` bleibt grün und wird um `provider_transform` + `consistency/reference_standards` erweitert (AC-14).
- **Quiet-Strip (IC-04):** Das Token `reference_standards` darf in generierten Dateien weder als YAML-Key noch im `<!-- agent-meta-provenance: … -->`-Kommentar erscheinen. Das Provenance-Verhalten **anderer** Felder (`version`, `prompt_mode`, `generated-from`, `hint`, `based-on`) bleibt **byte-identisch**.
- **Byte-Identitäts-Invariante:** `build_frontmatter` ohne `quiet_fields` und `_transform_frontmatter_for_opencode` ohne Quiet-Menge sind byte-identisch zu heute; `tests/test_agents_frontmatter.py:51-89,107-186` bleiben unverändert grün (IC-04 Rückwärtskompatibilität).
- **Kanal-Vereinigung statt Override (F-02):** Der Resolver führt Projekt- und ai-providers-Kanal als **Union** mit den Defaults zusammen (heute `project or provider`). Beide Kanäle sind im Repo unset → Ist-Verhalten unverändert; nur Projekte, die **beide** setzen, wechseln bewusst von Override zu Union.
- **Getrennter Kanal:** `agent-transform.strip-fields` (`provider_transform.py:335-337`, Runtime-Felder) wird **nicht** angefasst; `config/ai-providers.yaml` und `config/role-defaults.yaml` werden mit dem gewählten Mechanismus **nicht** geändert.
- **R1-Ordering:** Task 2 aktiviert den Default-Strip; Task 3 macht ihn lautlos. Beide dürfen **nur im selben Review-/Merge-Fenster** nach `main` (kein Merge von Task 2 allein), sonst entsteht ein Leak-Zeitfenster in 8 Provider-Surfaces.
- **R3-Ordering:** Dieses Framework-Change landet **vor** oder im selben Batch wie die feld-einführenden Template-PRs #787/#788/#789/#790/#791/#793/#795.
- **Schema-Additivität:** `provider-options.<Provider>.additionalProperties: false` bleibt; kein neues Pflichtfeld; Absenz von `frontmatter-keep-fields`/`frontmatter-strip-fields` bleibt gültig.
- **Auftrag 2 (Nicht-Ziele):** Keine Eval-Case-Inhalte, keine Erwartungswerte, keine Katalog-Einträge, kein neuer CI-Workflow; AC-17 misst ausschließlich Frische (Byte-Gleichheit).
- **Konventionen:** Jeder Task ist bite-sized und TDD (Test fail → implementieren → Test pass → Commit). File-Ownership im `Files:`-Block ist der Barrieren-Input; in einer Parallel-Gruppe überlappt keine Datei. Kein Worktree. Repo-Containment bleibt aktiv. Nur `rtk`-präfigierte Kommandos.

## Interfaces

Neue und geänderte Symbole als `file:Symbol`. Alle nicht gelisteten, bereits existierenden Symbole bleiben unverändert.

| Symbol | Art | Vertrag |
|---|---|---|
| `scripts/lib/frontmatter.py:REFERENCE_STANDARDS_FIELD` | neu | `str = "reference_standards"`; zentrale Namens-Konstante für Accessor, Quiet-Menge und Consistency. |
| `scripts/lib/frontmatter.py:parse_reference_standards` | neu (IC-01) | `(content: str) -> object \| None`; roher YAML-Wert über `_parse_frontmatter_yaml(content).get(...)`; fehlendes Frontmatter/PyYAML-Fehler/kein Dict → `None`; wirft nie. Keine Validierung. |
| `scripts/lib/frontmatter.py:FRONTMATTER_QUIET_STRIP_FIELDS` | neu (IC-04) | `frozenset[str] = frozenset({REFERENCE_STANDARDS_FIELD})`. |
| `scripts/lib/frontmatter.py:build_frontmatter` | geändert, additiv (IC-04) | `+ quiet_fields: frozenset[str] \| None = None`; `None` → Default-Menge; gestrippte Quiet-Keys bleiben aus dem Provenance-Kommentar; Nicht-Mengen-Typ → regulärer (lauter) Provenance-Pfad, keine Exception; ohne Parameter byte-identisch. |
| `scripts/lib/providers.py:FRONTMATTER_STRIP_DEFAULTS` | neu (IC-03) | `tuple[str, ...] = (REFERENCE_STANDARDS_FIELD,)`; Modul-Konstante (kein ai-providers-Top-Level-Key, weil `load_providers_config()` `data.get("providers", data)` liefert). |
| `scripts/lib/providers.py:resolve_frontmatter_strip_fields` | neu (IC-03) | `(provider: str, config: dict, provider_config: dict) -> list[str]`; `strip = DEFAULT ∪ projekt ∪ ai-providers`, `keep = projekt ∪ ai-providers`, Ergebnis `strip \ keep` stabil geordnet; fehlender/`None`/Nicht-Dict-Eintrag trägt nichts bei; Nicht-Listen-Wert → leer + höchstens **eine** `log.warning` je `(provider, key)`; wirft nie. |
| `scripts/lib/provider_transform.py:transform_agent_content_for_provider` | geändert (IC-03) | Inline-Expression `:385-388` ersetzt durch `_strip_fields = resolve_frontmatter_strip_fields(provider, config, provider_config)`. |
| `scripts/lib/provider_transform.py:_transform_frontmatter_for_opencode` | geändert (IC-04) | Symmetrische Quiet-Menge beim Bau des Provenance-Kommentars (`:554-561`); `strip_fields` erweitert weiterhin `removes` (`:618-619`). |
| `scripts/lib/consistency/reference_standards.py:REFERENCE_STANDARDS_FORMAT_HINT` | neu (IC-02) | `str = "<STANDARD>[@<version>][#<section>]"`. |
| `scripts/lib/consistency/reference_standards.py:parse_reference_standards_entry` | neu (IC-02) | `(entry: str) -> tuple[str, str \| None, str \| None] \| None`; MVP-Grammatik, Reihenfolge `@` vor `#` fix; `None` bei Verstoß. |
| `scripts/lib/consistency/reference_standards.py:check_reference_standards` | neu (IC-02) | `(path: Path, content: str, agent_meta_root: Path, changed_files: set[str] \| None) -> list[Finding]`; Feld optional; Finding-Matrix laut Spec; kein YAML-Fehler-Doppel-ERROR. |
| `scripts/consistency-check.py` | geändert (IC-02) | Import bei `:57`; Aufruf im Agent-Loop bei `:172`; `consistency/__init__.py` unverändert. |
| `config/project-config.schema.json:provider-options.<Provider>.frontmatter-keep-fields` | neu (IC-05) | `array[string]`, optional; in **allen** modellierten Provider-Blöcken (Claude, Gemini, Continue, Opencode, Mammouth); beschreibt „keep wins over strip“. |
| `config/project-config.schema.json:provider-options.<Provider>.frontmatter-strip-fields` | neu, Nachtrag F-03 | `array[string]`, optional; modelliert den **bestehenden** dokumentierten Kanal nach, gleicher Block-Satz. |
| `.claude/skills/conventions/SKILL.md` + `docs/providers/multi-provider.md` | geändert (IC-05) | Feld + MVP-Format bzw. Default-Strip + Keep-Opt-in dokumentiert (OQ-8). |
| `tests/routing-llm-eval/README.md` | geändert (IC-06) | hand-maintained vs. generiert präzisiert (AC-15). |

## File Structure

### Neue Dateien

- Create: `tests/test_reference_standards_strip.py` — Resolver-Unit-Matrix (AC-03, AC-04, AC-05, AC-06) + provider-parametrisierte Strip-/Byte-Identitäts-Fälle (AC-01, AC-02, AC-08).
- Create: `scripts/lib/consistency/reference_standards.py` — Struktur-/Format-Check (IC-02).
- Create: `tests/test_consistency_reference_standards.py` — Finding-Matrix + CLI-Registrierung (AC-09 … AC-13).
- Create: `tests/test_provider_options_schema.py` — Schema-Akzeptanz/Reject der neuen Provider-Options-Keys (IC-05, R6/F-03).
- Create: `tests/test_reference_standards_documented.py` — Doku-Pin für Konventions-Skill + Provider-Doku (IC-05, AC-15-Nachbarschaft).

### Geänderte Dateien

- Modify: `scripts/lib/frontmatter.py` — `REFERENCE_STANDARDS_FIELD`, `parse_reference_standards` (IC-01), `FRONTMATTER_QUIET_STRIP_FIELDS` + `quiet_fields` (IC-04).
- Modify: `scripts/lib/providers.py` — `FRONTMATTER_STRIP_DEFAULTS`, `resolve_frontmatter_strip_fields` (IC-03).
- Modify: `scripts/lib/provider_transform.py` — Resolver-Aufruf statt Inline-Expression (`:385-388`); Quiet-Menge im Opencode-Provenance-Bau (`:554-561`) (IC-03/IC-04).
- Modify: `scripts/consistency-check.py` — Import (`:57`) + Aufruf (`:172`) des neuen Checks (IC-02).
- Modify: `config/project-config.schema.json` — `frontmatter-keep-fields` + `frontmatter-strip-fields` in den 5 modellierten Provider-Blöcken (`:731-780`), additiv (IC-05).
- Modify: `.claude/skills/conventions/SKILL.md` — Frontmatter-Feldliste (`:43`) um `reference_standards` + MVP-Format ergänzen (IC-05, OQ-8).
- Modify: `docs/providers/multi-provider.md` — Abschnitt um `:572-586`: Default-Strip + Keep-Opt-in; `:586` auf Bookkeeping-Felder eingrenzen (IC-05).
- Modify: `tests/test_agents_frontmatter.py` — Accessor-/Quiet-Matrix + provider-parametrisierte Strip-/Provenance-Pins (AC-01, AC-02, AC-05, AC-07, AC-08).
- Modify: `tests/test_provider_agnostic_dispatch.py` — `_TOUCHED_MODULES` (`:27`) um `provider_transform` + `consistency/reference_standards` erweitern (AC-14).
- Modify: `tests/test_agent_eval_framework.py` — Freshness-Test `catalog.generated.yaml` + Header-Pin (AC-16, AC-17, AC-18).
- Modify: `tests/routing-llm-eval/README.md` — Single-Source-of-Truth-Regel präzisieren (AC-15).

### Step-Agent-Map (plan-driven `implement`)

| Step | Task | Agent |
|------|------|-------|
| 1 | Recognition & Parse (IC-01) | developer |
| 2 | Strip-Resolver + Aufrufstelle (IC-03) | senior-developer |
| 3 | Quiet-Strip / Provenance-No-Leak (IC-04) | senior-developer |
| 4 | Consistency-Check + Registrierung + AST-Guard (IC-02) | developer |
| 5 | Provider-Matrix-Regression-Pin (Codex + 8/9 Patch-Surfaces) | tester |
| 6 | Config-Schema (IC-05, R6/F-03) | developer |
| 7 | Doku Konventionen + Provider (IC-05) | documenter |
| 8 | Auftrag 2: Katalog-Freshness-Gate (IC-06) | tester |

`pipeline_stages.implement: 1` zeigt auf Step 1 (Task 1, Agent `developer`).

---

### Task 1: Recognition & Parse (IC-01)

**Files:**
- Modify: `scripts/lib/frontmatter.py`
- Modify: `tests/test_agents_frontmatter.py`

**Interfaces:** (Produces / Consumes)
- Produces: `REFERENCE_STANDARDS_FIELD` (Konstante), `parse_reference_standards(content) -> object | None` (niemals Exception); Round-Trip eines rohen YAML-Werts.
- Consumes: bestehendes `_parse_frontmatter_yaml` (`scripts/lib/frontmatter.py`), bestehende Fixtures/Helper in `tests/test_agents_frontmatter.py`.

**Agent:** developer
**Depends on:** —

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_agents_frontmatter.py::test_parse_reference_standards_reads_raw_list` (Round-Trip `["Diátaxis", "C4 model", "arc42"]`), `::test_parse_reference_standards_absent_is_none`, `::test_parse_reference_standards_scalar_value_is_returned_raw` (keine Validierung im Bottom-Layer, OQ-6), `::test_parse_reference_standards_yaml_error_is_none`, `::test_reference_standards_field_constant`. Zuerst `rtk python3 -m pytest tests/test_agents_frontmatter.py -q` → fail (NameError).
- [ ] Step 2: Implementieren — in `scripts/lib/frontmatter.py` `REFERENCE_STANDARDS_FIELD: str = "reference_standards"` und `parse_reference_standards(content)` als reiner Lese-Accessor auf `_parse_frontmatter_yaml` mit `isinstance(..., dict)`-Guard; rein additiv, keine bestehende Signatur ändern.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_agents_frontmatter.py -q` → rc 0 (bestehendeTests `:51-89,107-186` unverändert grün).
- [ ] Step 4: Commit — `feat: recognise reference_standards frontmatter field`.

**Acceptance:** IC-01 (Accessor-Vertrag: absent/PyYAML/YAML-Fehler → `None`, never raises); Regression AC-05/AC-07 (byte-identischer Render, keine Policy im Bottom-Layer).

---

### Task 2: Strip-Resolver + Aufrufstelle (IC-03)

**Files:**
- Modify: `scripts/lib/providers.py`
- Modify: `scripts/lib/provider_transform.py`
- Create: `tests/test_reference_standards_strip.py`

**Interfaces:** (Produces / Consumes)
- Produces: `FRONTMATTER_STRIP_DEFAULTS`, `resolve_frontmatter_strip_fields(provider, config, provider_config) -> list[str]`; Aufruf in `transform_agent_content_for_provider` statt der Inline-Expression `provider_transform.py:385-388`.
- Consumes: `REFERENCE_STANDARDS_FIELD` (Task 1); bestehender `provider-options`-Zugriff (`resolve_provider_options`, `providers.py:519-532`); `load_providers_config()` (`providers.py:119`).

**Agent:** senior-developer
**Depends on:** 1

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_reference_standards_strip.py::test_resolver_default_contains_field_for_all_registered_providers` (AC-03, Parameter über `registered_provider_names`), `::test_resolver_union_of_project_and_ai_providers_channels` (AC-05/F-02), `::test_resolver_keep_wins_over_strip` (AC-04 Resolver-Seite), `::test_resolver_malformed_values_fail_safe_and_warn_once` (AC-06: String/`null`/Nicht-Dict-Provider/unbekannter Provider → keine Exception, Feld bleibt, höchstens eine `log.warning` je `(provider, key)`, `caplog`).
- [ ] Step 2: Implementieren — `FRONTMATTER_STRIP_DEFAULTS = (REFERENCE_STANDARDS_FIELD,)`; Resolver mit Union-`_as_str_list`-Guard, Keep-Subtraktion und stabiler Ordnung; in `provider_transform.py` `:385-388` durch den Resolver-Aufruf ersetzen. Kein Provider-Literal.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_reference_standards_strip.py tests/test_provider_agnostic_dispatch.py -q` → rc 0. **Hinweis (R1):** Der „kein Token“-Pin (AC-01) folgt erst in Task 5, nachdem Task 3 die Quiet-Menge liefert; Task 2 allein darf nicht nach `main`.
- [ ] Step 4: Commit — `feat: resolve frontmatter strip fields provider-agnostically`.

**Acceptance:** AC-03, AC-04 (Resolver-Seite), AC-05 (Union-Semantik), AC-06.

---

### Task 3: Quiet-Strip / Provenance-No-Leak (IC-04)

**Files:**
- Modify: `scripts/lib/frontmatter.py`
- Modify: `scripts/lib/provider_transform.py`
- Modify: `tests/test_agents_frontmatter.py`

**Interfaces:** (Produces / Consumes)
- Produces: `FRONTMATTER_QUIET_STRIP_FIELDS`; `build_frontmatter(..., quiet_fields=...)`; spiegelsymmetrische Quiet-Behandlung in `_transform_frontmatter_for_opencode`.
- Consumes: `build_frontmatter` (`frontmatter.py:211-238`), Provenance-Bau in `_transform_frontmatter_for_opencode` (`provider_transform.py:554-561`), Resolver-Ergebnis (Task 2).

**Agent:** senior-developer
**Depends on:** 2

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_agents_frontmatter.py::test_build_frontmatter_quiet_fields_omitted_from_provenance` (AC-07: `strip_fields=["reference_standards","version"]` → Kommentar enthält `version=…`, **kein** `reference_standards=`), `::test_build_frontmatter_quiet_none_uses_default_set` (AC-07), `::test_build_frontmatter_quiet_non_set_falls_back_loudly` (AC-07: Nicht-Menge → regulärer Pfad, keine Exception), `::test_opencode_provenance_omits_quiet_fields` (AC-07, gleiche Matrix für `_transform_frontmatter_for_opencode`), `::test_existing_strip_channel_provenance_is_byte_identical` (AC-05: `version`/`prompt_mode`/`generated-from`).
- [ ] Step 2: Implementieren — `FRONTMATTER_QUIET_STRIP_FIELDS = frozenset({REFERENCE_STANDARDS_FIELD})`; `quiet_fields`-Parameter additiv; Default bei `None`; Quiet-Keys aus `preserved` ausschließen; Nicht-Mengen-Typ → Fail-safe auf den heutigen (lauten) Pfad; dieselbe Menge im Opencode-Builder. `removes.extend(strip_fields)` (`:618-619`) bleibt.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_agents_frontmatter.py -q` → rc 0 (bestehende Provenance-Tests unverändert grün).
- [ ] Step 4: Commit — `feat: omit quietly stripped fields from provenance comment`.

**Acceptance:** AC-07 (beide Builder), AC-05 (Byte-Identität der übrigen Provenance); mitigiert R1 und ist Voraussetzung für AC-01/AC-08.

---

### Task 4: Consistency-Check + Registrierung + AST-Guard (IC-02)

**Files:**
- Create: `scripts/lib/consistency/reference_standards.py`
- Create: `tests/test_consistency_reference_standards.py`
- Modify: `scripts/consistency-check.py`
- Modify: `tests/test_provider_agnostic_dispatch.py`

**Interfaces:** (Produces / Consumes)
- Produces: `REFERENCE_STANDARDS_FORMAT_HINT`, `parse_reference_standards_entry(entry)`, `check_reference_standards(path, content, agent_meta_root, changed_files) -> list[Finding]`; Registrierung im Agent-Loop; erweiterte `_TOUCHED_MODULES`.
- Consumes: `Finding`/`Severity` (`consistency/report.py`), `_rel(...)`-Hilfe in `consistency-check.py`, `_parse_frontmatter_yaml`, `REFERENCE_STANDARDS_FIELD` (Task 1), `_TOUCHED_MODULES` (`tests/test_provider_agnostic_dispatch.py:27`).

**Agent:** developer
**Depends on:** 1

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_consistency_reference_standards.py` tabellengetrieben: `::test_absent_field_is_optional` (AC-09), `::test_valid_entries_pass` inkl. `"Some Unknown Standard"` (AC-10, keine Registry OQ-5), `::test_invalid_entry_matrix` (AC-11: Skalar→`reference-standards.not-list` ERROR; `[]`→`reference-standards.empty` WARNING; `[42]`→`entry-not-string` ERROR; `[""]`/`["  "]`→`entry-empty` ERROR; `["arc42#1@2"]`/`["@1.0"]`/`["x@@"]`/`["y##"]`/`["x#"]`→`entry-format` ERROR; `["arc42","arc42"]`→`duplicate` WARNING), `::test_no_frontmatter_or_yaml_error_yields_no_extra_finding` (AC-13), Subprozess `::test_cli_file_flag_exit_code` (AC-12: ERROR → rc 1, nur-WARNING → rc 0, `--strict` → rc 1). In `tests/test_provider_agnostic_dispatch.py` einen Fall ergänzen, der die erweiterte `_TOUCHED_MODULES`-Menge und das Fehlen neuer Provider-Literale pinnt (AC-14).
- [ ] Step 2: Implementieren — Modul mit Format-Grammatik (`STANDARD` nicht leer, kein führendes/abschließendes Whitespace, interne Leerzeichen erlaubt, keine `@`/`#` im Namen; `@version`/`#section` optional, nicht leer, ohne Whitespace/Delimiter, `@` vor `#`); `check_reference_standards` mit identischer Signatur wie `check_agent_frontmatter`; Import `consistency-check.py:57`; Aufruf `:172` direkt nach `check_agent_frontmatter`; `_TOUCHED_MODULES` um `provider_transform` + `consistency/reference_standards` erweitern. Kein Provider-Literal.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_consistency_reference_standards.py tests/test_provider_agnostic_dispatch.py -q` → rc 0; danach `rtk python3 scripts/consistency-check.py` → rc 0.
- [ ] Step 4: Commit — `feat: validate reference_standards in consistency check`.

**Acceptance:** AC-09, AC-10, AC-11, AC-12, AC-13, AC-14.

---

### Task 5: Provider-Matrix-Regression-Pin (AC-01/AC-02/AC-04/AC-08)

**Files:**
- Modify: `tests/test_agents_frontmatter.py`
- Modify: `tests/test_reference_standards_strip.py`

**Interfaces:** (Produces / Consumes)
- Produces: provider-parametrisierte Strip-/No-Leak-/Byte-Identitäts-Pins über `load_providers_config()`; Codex-Whitelist-Regression (nur `codex-toml` droppt unbekannte Felder) und korrigiertes 8/9-Patch-Surface-Verhalten (`opencode-native` = bewusste Verhaltensänderung).
- Consumes: Resolver (Task 2), Quiet-Menge (Task 3), `transform_agent_content_for_provider`, `build_agent_toml_document` (`agent_toml.py:46-89`), `tomllib`/`tomli`-Fallback.

**Agent:** tester
**Depends on:** 3

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_reference_standards_strip.py` + `tests/test_agents_frontmatter.py`, parametrisiert über alle registrierten Provider: AC-01 (Provider ohne `agent-transform.frontmatter-mechanism`, heute 7 → kein `reference_standards`-Token, kein Provenance-Eintrag für das Feld), AC-02 (`opencode-native` → YAML-Frontmatter parst und enthält keinen Key; `codex-toml` → `tomllib`-Parse ergibt genau `name`/`description`/optional `model`/`developer_instructions`, `version`/`generated-from` nur als Kommentar), AC-04 (Keep über Projekt-Kanal und über ai-providers-Kanal; widersprüchliche Angaben → keep gewinnt; andere Provider bleiben gestrippt), AC-08 (zwei Templates, die sich **nur** durch `reference_standards` unterscheiden → byte-identische Ausgabe je Provider), AC-05 (bestehender Opencode-Strip-Kanal byte-identisch).
- [ ] Step 2: Implementieren — test-only: erwartet **keine** Produktionsänderung. Schlägt ein Pin fehl, ist der Befund an Task 2/3 zurückzugeben (kein stiller Test-Aufweichen); die 8/9-Korrektur aus F-01 wird als Testdokumentation (Docstring) festgehalten.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_agents_frontmatter.py tests/test_reference_standards_strip.py -q` → rc 0.
- [ ] Step 4: Commit — `test: pin reference_standards strip and provenance across providers`.

**Acceptance:** AC-01, AC-02, AC-04, AC-08 (AC-05 wird re-gepinnt).

---

### Task 6: Config-Schema (IC-05, R6/F-03)

**Files:**
- Modify: `config/project-config.schema.json`
- Create: `tests/test_provider_options_schema.py`

**Interfaces:** (Produces / Consumes)
- Produces: Schema-Member `provider-options.<Provider>.frontmatter-keep-fields` und `provider-options.<Provider>.frontmatter-strip-fields` (`array[string]`, optional) in allen modellierten Provider-Blöcken.
- Consumes: bestehender `provider-options`-Block (`project-config.schema.json:731-780`), Muster `tests/test_context_topology_schema.py` (`pytest.importorskip("jsonschema")`).

**Agent:** developer
**Depends on:** 2

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_provider_options_schema.py::test_keep_and_strip_fields_modelled_for_every_modelled_provider` (IC-05/F-03: beide Keys, `type: array`, `items.type: string`, in Claude/Gemini/Continue/Opencode/Mammouth), `::test_absence_of_both_keys_remains_valid` (R6/Additivität), `::test_unknown_provider_option_key_still_rejected` (`additionalProperties: false` bleibt je Block), `::test_non_array_keep_fields_rejected`.
- [ ] Step 2: Implementieren — beide Keys additiv in die 5 modellierten Provider-Sub-Blöcke; `description` für „keep wins over strip“ bzw. den bestehenden Strip-Kanal; `additionalProperties: false` und `properties`-Struktur unverändert; kein Provider-Sonderfall.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_provider_options_schema.py tests/test_config_audit.py -q` → rc 0; danach `rtk python3 scripts/sync.py --validate` → rc 0.
- [ ] Step 4: Commit — `feat: model frontmatter strip and keep fields in provider options schema`.

**Acceptance:** IC-05, AC-04 (Config-Oberfläche des Keep-Kanals), R6/F-03.

---

### Task 7: Doku Konventionen + Provider (IC-05)

**Files:**
- Modify: `.claude/skills/conventions/SKILL.md`
- Modify: `docs/providers/multi-provider.md`
- Create: `tests/test_reference_standards_documented.py`

**Interfaces:** (Produces / Consumes)
- Produces: dokumentiertes Feld + MVP-Format im Konventions-Skill; Default-Strip + Keep-Opt-in in der Provider-Doku; Precisierung der bestehenden „reines Opt-in“-Aussage auf Bookkeeping-Felder; Doku-Pin-Test.
- Consumes: Schema-Keys (Task 6), Resolver-Semantik (Task 2/Task 3), `tests/routing-llm-eval/README.md`-Regel (Task 8).

**Agent:** documenter
**Depends on:** 3, 6

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_reference_standards_documented.py::test_conventions_skill_documents_field_and_format` (Feldname + Format-Hint), `::test_multi_provider_documents_default_strip_and_keep_opt_in` (`frontmatter-keep-fields`, Default-Strip-Aussage), `::test_all_conventions_skill_copies_agree` (OQ-8: alle gefundenen Kopien enthalten denselben Satz).
- [ ] Step 2: Implementieren — `.claude/skills/conventions/SKILL.md` Frontmatter-Feldliste (`:43`) um `reference_standards` + Format ergänzen; `docs/providers/multi-provider.md`-Abschnitt um `:572-586` um den Default-Strip-/Keep-Opt-in-Absatz erweitern und `:586` auf die Bookkeeping-Felder eingrenzen; weitere Provider-Skill-Kopien mit `rtk grep -rl "Adding a New Agent Role" .*/skills` finden und angleichen (OQ-8), oder den Test auf die tatsächlich existierende Kopie beschränken.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_reference_standards_documented.py -q` → rc 0; `rtk grep -n "reference_standards" .claude/skills/conventions/SKILL.md docs/providers/multi-provider.md`.
- [ ] Step 4: Commit — `docs: document reference_standards field and keep opt-in`.

**Acceptance:** IC-05, OQ-8; stützt AC-04 (Config-Opt-in dokumentiert).

---

### Task 8: Auftrag 2 — Katalog-Freshness-Gate (IC-06)

**Files:**
- Modify: `tests/test_agent_eval_framework.py`
- Modify: `tests/routing-llm-eval/README.md`

**Interfaces:** (Produces / Consumes)
- Produces: Freshness-Test für `tests/routing-llm-eval/catalog.generated.yaml` (Regenerierung via `--out <tmp>` + Byte-Vergleich); Pin des bestehenden promptfoo-Gates und des GENERATED-Headers; präzisierte README-Regel.
- Consumes: `scripts/gen_routing_llm_eval_catalog.py` (`--out`, `:170-183`), `tests/routing-llm-eval/catalog.generated.yaml`, `test_generated_promptfoo_config_is_fresh_and_valid` (`:113-125`), `scripts/gen_promptfoo_config.py --check`.

**Agent:** tester
**Depends on:** —

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_agent_eval_framework.py::test_generated_routing_catalog_is_fresh` (AC-17: `tempfile.TemporaryDirectory` → `rtk python3 scripts/gen_routing_llm_eval_catalog.py --out <tmp>/catalog.generated.yaml` → `read_bytes()`-Vergleich gegen die committete Datei), bestehenden `test_generated_promptfoo_config_is_fresh_and_valid` um den Header-Pin „do not edit by hand“ ergänzen (AC-16/AC-18). **Keine** Eval-Case-Änderung.
- [ ] Step 2: Implementieren — Freshness-Test mit Subprozess + Byte-Vergleich; Header-Assertion für `promptfooconfig.generated.yaml`; README-„Single Source of Truth“-Abschnitt (`:26-32`) um die explizite hand-maintained/generiert-Liste inkl. Generator-Pfade (AC-15) präzisieren. Kein Generator-Flag und kein CI-File nötig (OQ-9-Default, OQ-10).
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_agent_eval_framework.py -q` → rc 0; `rtk python3 scripts/gen_promptfoo_config.py --check` → rc 0.
- [ ] Step 4: Commit — `test: pin routing-llm-eval catalog freshness`.

**Acceptance:** AC-15, AC-16, AC-17, AC-18.

---

## AC-Abdeckung (AC ↔ Task)

| AC | Task(s) | | AC | Task(s) |
|---|---|---|---|---|
| AC-01 | 2, 3, 5 | | AC-10 | 4 |
| AC-02 | 5 | | AC-11 | 4 |
| AC-03 | 2 | | AC-12 | 4 |
| AC-04 | 2, 5, 6, 7 | | AC-13 | 4 |
| AC-05 | 2, 3, 5 | | AC-14 | 4 |
| AC-06 | 2 | | AC-15 | 7, 8 |
| AC-07 | 3 | | AC-16 | 8 |
| AC-08 | 3, 5 | | AC-17 | 8 |
| AC-09 | 4 | | AC-18 | 8 |

Alle 18 ACs sind mindestens einer Task zugeordnet; kein AC ohne Task. Erwartete-Berührungs-Matrix der Spec ist 1:1 abgedeckt (plus die neue Schema-Testdatei).

## Rollback / Safety-Net

- **Primärer Rollback (config-only, kein Code):** Ein Provider, dem das Feld erhalten bleiben soll, setzt `provider-options.<Provider>.frontmatter-keep-fields: [reference_standards]` bzw. `providers.<Provider>.frontmatter_keep_fields` — `keep` schlägt `strip` (AC-04).
- **Globaler Rollback (eine Zeile):** `FRONTMATTER_STRIP_DEFAULTS`-Eintrag entfernen; damit ist der Default-Strip aus, alle bestehenden Kanäle bleiben unverändert. Kein Schema-/Doku-Rollback nötig (rein additiv).
- **Fail-safe-Verhalten:** Jede fehlerhafte/nicht-Listen-Config-Quelle trägt nichts bei; der Default-Strip bleibt aktiv und es gibt höchstens eine `log.warning` je `(provider, key)` — nie eine Exception (AC-06).
- **Kanal-Rückwärtskompatibilität:** Projekt- und ai-providers-Strip-Kanäle behalten Name/Payload; die Union-Änderung wirkt nur, wenn ein Projekt **beide** Kanäle setzt (F-02). `agent-transform.strip-fields` bleibt ein getrennter, unberührter Kanal.
- **Byte-Identitäts-Netz:** Ohne neuen Parameter sind `build_frontmatter` und `_transform_frontmatter_for_opencode` byte-identisch; `tests/test_agents_frontmatter.py:51-89,107-186` sind die Regressionsschranke. AC-08 (Templates, die sich nur im Feld unterscheiden → byte-identisch) ist der stärkste Beweis.
- **R1-Merge-Gate:** Task 2 (Default-Strip) und Task 3 (Quiet-Menge) landen gemeinsam; wird nur Task 2 gemergt, leakt das Feld-Token über den Provenance-Kommentar in 8 Provider-Surfaces.
- **Consistency-Rollback:** Der neue Check ist ein additiver Aufruf; Entfernen von Import + Aufruf stellt den Vorzustand wieder her. Exit-Code-Vertrag bleibt unverändert (ERROR → rc 1, nur WARNING → rc 0, `--strict` → rc 1).
- **Auftrag 2:** Änderung ist test-/doku-only; Rollback = Revert des Tests/README, keine Produktionswirkung, keine Katalog-Inhaltsänderung.
- **Nicht-Regressions-Gate (Abschluss):** `rtk python3 scripts/sync.py --validate` (rc 0), `rtk python3 scripts/sync.py --check` (rc 0), `rtk python3 scripts/consistency-check.py` (rc 0), die in den Tasks genannten pytest-Suiten (rc 0), `rtk python3 scripts/gen_promptfoo_config.py --check` (rc 0).

## Self-Review

- **AC-Abdeckung:** AC-01 … AC-18 sind vollständig zugeordnet (Tabelle oben); kein AC ohne Task, keine Task ohne AC- bzw. IC-Bezug. Task 1 trägt IC-01 (dessen Vertrag mangels eigener AC-Nummer über seinen Unit-Test und die Regressions-AC-05/AC-07 gepinnt wird).
- **Test je Task:** Jede Task besitzt eine benannte Testdatei/Testnamen und ein `rtk`-präfigiertes Verifikationskommando mit erwartetem rc; jeder Task folgt dem TDD-Zyklus (Test fail → implementieren → Test pass → Commit).
- **Traceability:** `spec-id: SPEC-REFERENCE-STANDARDS-2026-09-15` ↔ `**Spec:**`-Pfad ↔ Task-ID ↔ Testname ist durchgängig; `pipeline_stages.implement: 1` zeigt auf Step 1 der Step-Agent-Map (Task 1, Agent `developer`).
- **Interface-Vollständigkeit:** Jede Task hat nicht-leere `Produces`/`Consumes`; alle neuen Symbole sind mit Datei, Name und Signatur benannt; die gespiegelten `quiet_fields`-Signaturen in `frontmatter.py` und `provider_transform.py` sind explizit ausgewiesen.
- **Datei-Ownership / Barrieren:** Keine Datei wird in einer Parallel-Gruppe von zwei Tasks geschrieben. `scripts/lib/frontmatter.py` (Task 1→3), `scripts/lib/provider_transform.py` (2→3) und `tests/test_agents_frontmatter.py` (1→3→5) werden sequenziell über strikt vorwärtsgerichtete `Depends on`-Kanten genutzt. Parallel-safe (ownership-disjunkt): {Task 4, Task 6, Task 8} untereinander und gegen {2,3}. Die bekannte `validate_plan`-`file_overlap`-Limitierung (ohne `kind`-Gate über sequenzielle Kanten) kann gekoppelte Dateien melden — dokumentierte Limitierung, keine Ownership-Verletzung.
- **Abhängigkeitsgraph:** Zyklenfrei und vorwärtsgerichtet: 1 → 2 → 3 → 5; 1 → 4; 2 → 6; 3/6 → 7; 8 unabhängig.
- **Risiko-Abdeckung:** R1 (Provenance-Leak) durch IC-04/Task 3 + AC-07/AC-08 + Merge-Gate; R3 (Merge-Reihenfolge) als Global Constraint; R6/F-03 durch Task 6; R4/R5 (Consistency prüft Templates, nicht generierte Dateien) akzeptiert gemäß OQ-7; R9 durch die test-only Beschränkung von Task 8.
- **Rahmenbedingungen:** Provider-agnostisch (kein Provider-Literal; Modell-/Mechanismus-Zugriff nur über Keys), Stdlib-only, Py3.9-konform, byte-identischer Nicht-Parameter-Pfad, Schema additiv, `additionalProperties: false` erhalten, keine Eval-Case-Änderung, kein neuer CI-Workflow, kein Worktree.
- **No-Placeholder:** Keine Platzhalter-Marker (Füllwort-Platzhalter, Ellipsen-Zeile), keine leeren `Interfaces:`; exakte Pfade, Symbole, Signaturen, Testnamen und Commit-Messages.

## Ausführungs-Handoff

- **Reihenfolge:** Task 1 → 2 → 3 → 5; Task 4 nach Task 1; Task 6 nach Task 2; Task 7 nach 3/6; Task 8 unabhängig. Task 2 und Task 3 bilden ein **gemeinsames** Merge-Fenster (R1).
- **Task-für-Task (plan-ledger):** Jeder Task läuft mit frischem Subagenten, wird zweistufig reviewt (Requirement-Treue → Qualität) und erst dann committet; Checkboxen werden über den Ledger-Writer aktualisiert. Kein Task ohne Test und Commit.
- **Blocked-Regel:** Kann ein Task sein Akzeptanzkriterium nicht belegen (z. B. Task 5-Pin schlägt fehl), bleibt er offen, wird an den Orchestrator eskaliert und blockiert Nachfolger; er wird nie stillschweigend übersprungen oder umsortiert.
- **Branch:** `feat/reference-standards-support` (Branch-Guard: keine Code-Änderungen auf `main`); Git-Mutationen über den `git`-Agent.
- **Nicht Teil dieses Plans:** Backfill von `reference_standards` in bestehende Templates (opportunistisch, WP2/Rollen-PRs), Registry-Validierung (OQ-5), Format-Grammatik in `frontmatter.py` (OQ-6), Änderungen an `config/ai-providers.yaml`/`config/role-defaults.yaml`.
