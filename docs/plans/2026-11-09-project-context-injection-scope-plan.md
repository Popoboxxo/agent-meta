# Project-Context-Injection Scope — Implementation Plan

> **Status:** DRAFT
> **Issue:** [#1187](https://github.com/Popoboxxo/agent-meta/issues/1187) — feat(config): project-context-injection scope (core | +orchestrator | +whitelist | all)
> **Revision:** 3 (Entscheidungen D5–D8 eingearbeitet, 2026-11-09)
> **Spec:** `docs/specs/2026-11-09-project-context-injection-scope-spec.md` (spec-id `SPEC-project-context-injection-scope-2026-11-09`, Revision 4, **Status: DRAFT** — Freigabe vor Task-Beginn einholen)
> **Klasse:** **L** (cross-cutting in `sync`-Rendering; ~14 produktive Dateien + 4 neue Testdateien; kein neues Subsystem)
> **Datum:** 2026-11-09 · **Basis:** Branch `docs/config-wave-plans-1181-1188`, HEAD `aaed14c2`, agent-meta `v2.0.0-beta.8`
> **Kanonische Welle:** `#1187 → #1186 → #1188 → #1181 → #1141` → Whitelist-Ableitung (eigenes Follow-up). Dieser Plan ist **Schritt 1** der Welle und setzt die Rollen-Schleife neu auf, auf der #1186/#1188/#1181 aufsetzen.
> **Voraussetzungen:**
> 1. Spec von `main_chat`/Daniel auf `Status: APPROVED` gesetzt. OQ-1…OQ-7 sind beantwortet: OQ-2…OQ-5 durch die Entscheidungen **D5–D8** (Spec §13, `DECIDED 2026-11-09`), OQ-1/OQ-6/OQ-7 bereits in Spec-Revision 2 (§8.2).
> 2. Baseline bestätigt: `.tmp/issue-dump/baseline-validate.txt` (PASS, 1 Warnung), `.tmp/issue-dump/baseline-check.txt` (DRY-RUN, 3 bestehende Warnungen).
> 3. Kein paralleler Branch auf `scripts/lib/agent_sync.py` (#1188/#1181), `scripts/lib/sync_pipeline.py` (#1186/#1181), `config/project-config.schema.json`, `docs/ui/admin-ui.html` (Konfliktflächen §10 der Spec).
> 4. Python ≥ 3.9, stdlib-only; `pytest` vorhanden; `PYTEST_BASETEMP` in der Shell gesetzt (Konvention aus `docs/plans/2026-10-31-release-checklist-plan.md:23`).
>
> **Branch-Guard:** Die Implementierung läuft auf `feat/1187-project-context-injection` (abgeleitet von `main` nach dem Docs-Branch-Merge). **Keine** Änderung auf `main`/`master`. Push/Tag/Branch-Merge ausschließlich durch den `git`-Agenten.
> **Aufwand:** Gesamt **L**. Referenz für die Summenbildung: `effort-estimator` (Text-Referenz, kein Tool-Aufruf) — 15 Tasks, 4 Meilensteine, 2 neue produktive Codeblöcke (`config.py`-Resolver, `agent_sync.py`-Renderpfad).

---

## 1. Zielbild in 5 Sätzen

1. `project-context-injection.mode` steuert **pro Rolle**, ob der Projektabsatz (`{{PROJECT_CONTEXT}}`) in den generierten Rollen-Prompt eingebettet wird — `all` (Default) reproduziert das heutige Byte-Ergebnis, `core` bettet gar nichts ein.
2. Jede Rolle **ohne** eingebetteten Block erhält **genau eine** physische Pointer-Zeile, die die **real aufgelöste** Kontextdatei des Providers nennt (`pc["context_file"]`, z. B. `AGENTS.md` für Gemini — nicht `GEMINI.md`). Mechanik: Block blankieren → leer gewordene `**Project context:**`-Zeile entfernen → Pointer als eine Zeile vor dem letzten `</context>` einfügen; Fallbacks vor `</workflow>` (`intern-developer`) bzw. Dateiende + `log.note` (13 `se-*` + `mammouth-expert`). Der Pointer-Text ist konfigurierbar (Default Englisch, `pointer-language`/`pointer-text`, D8).
3. Die Entscheidung fällt im Renderer pro Rolle (`agent_sync.sync_agents_for_provider` → Rollen-Schleife), nicht in 83 Templates; der Template-Text bleibt unverändert.
4. Fünf Prosa-Vorkommen in vier Templates werden auf `{{#if PROJECT_CONTEXT_INJECTED}}…{{else}}{{CONTEXT_FILE}}{{/if}}` umgestellt, damit `core` keine grammatisch zerlegten Sätze erzeugt und `all` byte-identisch bleibt.
5. Der Sync-Log meldet pro Provider `injected=n/total`, die Zahl der Pointer-Zeilen und die gesparten Zeichen; die Sektion ist im Admin-UI schreibbar, `sync.py --validate` bleibt ohne neue Findings grün, und `orchestrator: exclude` ist in jedem Modus zulässig (WARN statt Abbruch, D6).

---

## 2. File-Structure-Map

Alle Pfade sind gegen HEAD `aaed14c2` geprüft. „Zeile" = heutige Ankerzeile (verschiebt sich durch die Änderung).

| Datei | neu/ändern | Zweck | Task |
|---|---|---|---|
| `config/project-config.schema.json` | ändern | neue Top-Level-Property `project-context-injection` mit **sechs** Keys (`mode`/`whitelist`/`orchestrator`/`orchestrator-roles`/`pointer-language`/`pointer-text`, `additionalProperties: false`); `orchestrator-roles`/`pointer-text` **ohne** `default` (D5/D8), Einfügung nach dem `context-profile`-Block (`:2842-2849`, vor `required` `:2851`) | T1 |
| `scripts/lib/config.py` | ändern | `PROJECT_CONTEXT_MODES`/`PROJECT_CONTEXT_ORCHESTRATOR_VALUES`/`PROJECT_CONTEXT_POINTER_LANGUAGES`-Konstanten, drei Pointer-Default-Texte + Sprach-Abbildung; `resolve_project_context_scope()` (Validierung inkl. `orchestrator-roles`, `pointer-language`, `pointer-text`-Tokens, WARN-Sink), `format_project_context_pointer()` (pure `{context_file}`-Substitution) + `project_context_injected_for_role()` (pure Modus-Matrix); Aufruf am Ende von `build_variables` bei den Provider-Variablen (`:2810-2827`) mit `communication_language=variables.get("COMMUNICATION_LANGUAGE")`; `_SYNC_SKIPPED_DEFAULT_KEYS` (`:183-191`) | T2, T5 |
| `scripts/lib/consistency/placeholders.py` | ändern | `PROJECT_CONTEXT_MODE`, `PROJECT_CONTEXT_INJECTED` in `_BUILTIN_VARS` (`:12-45`, neben `PROJECT_CONTEXT` `:15` und `CONTEXT_FILE` `:38`) | T3 |
| `scripts/lib/variables.py` | ändern | `PROJECT_CONTEXT_INJECTED` in die Conditional-Whitelist von `strip_inactive_conditional_blocks` (`:556`, Sammelzeile `:570-572`) — **ohne das bleiben `{{#if}}`-Zweige stehen und werden durch die Orphan-Cleanup (`:690-693`) zusammengeklebt** | T3 |
| `scripts/lib/standalone.py` | ändern | `PROJECT_CONTEXT_INJECTED: "true"`, `PROJECT_CONTEXT_MODE: "all"` in den Conditional-Fallbacks (`:160-194`), damit exportierte Personas den `all`-Zweig rendern | T3 |
| `scripts/lib/agent_sync.py` | ändern | `_PROJECT_CONTEXT_POINTER` **pro Provider** (aus `scope.pointer_text` + `pc["context_file"]`) und `PROJECT_CONTEXT_INJECTED`/`PROJECT_CONTEXT_MODE`-Default in `_build_provider_vars` (`:489-554`); Per-Rolle-Anwendung in der Schleife (`:1444-1470` vor `_apply_content_pipeline` `:1460`); Label-Cleanup + dreistufiger Pointer-Fallback (`</context>` → `</workflow>` → Dateiende) + Delta-Zähler + Log-Zeile nach der Schleife. **Achtung: #1181 (T8) ändert dieselbe Schleife `:1457-1468` und `_finalize_agent_content` — seriell, nicht parallel.** | T4-T7 |
| `agents/1-generic/ui-ux-designer.md` | ändern | 2 Prosa-Vorkommen (`:77`, `:105`) auf `{{#if}}`/`{{else}}`; `version: "1.6.0"` → `"1.6.1"` | T9 |
| `agents/1-generic/bug-feature-analyzer.md` | ändern | 1 Prosa-Vorkommen (`:40`); `version: "1.5.1"` → `"1.5.2"` | T9 |
| `agents/1-generic/knowledge-curator.md` | ändern | 1 Prosa-Vorkommen (`:55`); `version: "1.4.2"` → `"1.4.3"` | T9 |
| `agents/1-generic/knowledge-migrator.md` | ändern | 1 Prosa-Vorkommen (`:38`); `version: "1.5.2"` → `"1.5.3"` | T9 |
| `scripts/lib/consistency/project_context_injection.py` | **neu** | 4 Check-IDs (`pointer-missing`, `whitelist-no-effect`, `orchestrator-role-no-template`, `mode-unknown`), Muster: `scripts/lib/consistency/context_size.py:44-100` | T11 |
| `scripts/consistency-check.py` | ändern | Import-Block (`:42-70`) + Aufruf im Provider-Block (`:251-267`) | T11 |
| `scripts/admin-server.py` | ändern | `"project-context-injection"` in `PROJECT_WRITABLE_SECTIONS` (`:234-259`) | T12 |
| `docs/ui/admin-ui.html` | ändern | `viewProjectContextInjection`, Nav (`:1632-1633`), `router.register` (`:11264-11265`), `routeMap` (`:11381-11383`); Pane-Muster `:7650-7761`, Speichern über `saveProjectSection` (`:5960-5962`) | T13 |
| `docs/api/admin-ui-reference.md` | ändern | Help-Block mit `<!-- help-id: project_instance-project_context_injection -->` — ohne das schlägt `docs.ui_help_mappings` fehl (`scripts/lib/consistency/docs.py:47-97`) | T13 |
| `docs/guides/features/sync-concept.md` | ändern | Variablen-Tabelle „Auto-injiziert" (`:278-292`) um `PROJECT_CONTEXT_MODE`/`PROJECT_CONTEXT_INJECTED` erweitern | T14 |
| `howto/configs/project.yaml.example` **und** `templates/configs/project.yaml.example` | ändern | kommentierter `project-context-injection`-Block in **beiden** existierenden Beispiel-Dateien mit derselben Sektion (Muster `release-checklist` in `howto/…:99`, `context-profile` in `templates/…:318`); Divergenz zwischen den beiden Dateien ist ein Doku-Fehler | T14 |
| `CHANGELOG.md` | ändern | Eintrag unter „Unreleased" | T14 |
| `tests/test_project_context_injection_config.py` | **neu** | Schema (6 Keys), Resolver (Modus/Whitelist/`orchestrator-roles`/Pointer-Sprache/-Text), Platzhalter-Registrierung | T1-T3 |
| `tests/test_project_context_injection_render.py` | **neu** | Golden `all`, `core`, `core+whitelist`, `core+orchestrator`, Pointer-Heuristik, Delta | T4-T10 |
| `tests/test_project_context_injection_consistency.py` | **neu** | 4 Check-IDs + Registrierung + `--validate`-Integration | T11 |
| `tests/test_admin_ui_project_context_injection_section.py` | **neu** | Whitelist, Endpoint-Round-Trip, UI-Wiring, Help-ID | T12-T13 |
| `tests/fixtures/slimming-golden/*.md` | **nicht anfassen** | AC2-Golden (6 betroffene + `intern-developer` + `mammouth-expert`) | T10 |

**Nicht geändert** (bewusst): `schemas/a2a-handoff.schema.json`, `config/ai-providers.yaml` (nur lesend), `scripts/lib/context.py`, `scripts/lib/standalone.py`-Kontextkanal (`:57-74`), die 83 Block-Vorkommen selbst.

**Querschnitt mit der Config-Welle (kanonisch `#1187 → #1186 → #1188 → #1181 → #1141` → Whitelist-Ableitung):**

| Geteilte Fläche | Wer ändert sie | Konsequenz für diesen Plan |
|---|---|---|
| `scripts/lib/agent_sync.py:1444-1468` + `_finalize_agent_content` (`:935`) | #1187 (diese Tasks T4-T7), **#1188** (`_apply_role_issue_convention_overrides`, Aufruf neben `:1459`) **und** #1181 (per-Role-`auto_commit`-Overlay `:1459`) | dieselbe Rollen-Schleife, drei Autoren; **kein** Parallelbetrieb — #1187 ist Schritt 1 |
| `scripts/lib/sync_pipeline.py` | #1186 (Scaffold `:1699`, neue Stage 14c „resolved.json" nach `:1615`), #1181 (T9, Umbau Stage 14 `:1893-1924`) | #1187 hat dort **keinen** Task und fasst die Datei nicht an — die Kollision bleibt zwischen #1186 und #1181 (Reihenfolge #1186 → #1181) |
| `scripts/lib/variables.py` (`:570-598`), `scripts/lib/standalone.py` (`:150-204`) | #1187 (T3) | #1186 ändert dort **nichts** (nur Hotspot, kein Edit) — additiv, aber gleiche Datei → seriell |
| `tests/scenarios/registry.md` | #1181 (`94`), #1187 (`95`–`98`), #1186 (`99`) | IDs vorab vergeben; dieser Plan registriert nichts (Scratch-Szenario), Fallback-IDs siehe §6 |
| `templates/configs/project.yaml.example` **und** `howto/configs/project.yaml.example` | #1187, #1186, #1188, #1181 | zwei existierende Beispiel-Dateien mit derselben Sektion; immer beide pflegen |
| `docs/issue-labels.md` | #1188 erzeugt (generierte Doku), #1186 klassifiziert (`project-docs.files.issue-labels`) | Querschnittsnotiz, **keine** Task in #1187 |
| `.meta-config/issue-labels-state.json` | #1188 erzeugt (persistiertes Prune-Manifest), #1186 klassifiziert als **`unmanaged`** (Negativ-Deklaration, K1) | Querschnittsnotiz, **keine** Task in #1187 |

Vollständige Matrix inkl. `config/project-config.schema.json`, `scripts/lib/config.py`, `scripts/admin-server.py` und `docs/ui/admin-ui.html`: Spec §10.

---

## 3. Meilensteine

Jeder Meilenstein ist einzeln grün lauffähig; die Reihenfolge ist die Ausführungsreihenfolge.

### M1 — Konfigurationsfläche & Auflösung (ohne Render-Änderung)
- **Ziel:** Sektion im Schema, Resolver mit allen harten Fehlern, Diagnose-Variablen registriert. Bei fehlender Sektion ändert sich am Rendering **nichts** (Resolver liefert `mode=all`).
- **Tasks:** T1, T2, T3.
- **Zwischentest-Gate:**
  - `python3 -m pytest tests/test_project_context_injection_config.py --basetemp="$PYTEST_BASETEMP"`
  - `python3 scripts/sync.py --validate` → `[PASS] All checks passed.` (weiterhin genau die `active-set.gate-dropped`-Notiz)
  - `python3 scripts/sync.py --check` → DRY-RUN ohne neue Findings (keine Logzeilen-Assertion hier: die `project-context-injection:`-Zeile entsteht erst mit T7 in M2).

### M2 — Renderer-Injektion (Block/Pointer/Delta) mit `mode: all` als No-Op
- **Ziel:** Pro Rolle entschieden; `all` byte-identisch; `core` bettet 0 Blöcke und genau 1 Pointer-Zeile ein; Delta im Log.
- **Tasks:** T4, T5, T6, T7, T8.
- **Zwischentest-Gate:**
  - `python3 -m pytest tests/test_project_context_injection_render.py --basetemp="$PYTEST_BASETEMP"`
  - `python3 scripts/sync.py --validate` (unverändert grün)
  - `python3 scripts/sync.py --check` → DRY-RUN, Logzeile `project-context-injection: mode=all injected=<n>/<n> roles, pointer=0, chars saved=0 (vs mode=all)` (AC6-Beleg für den Default) **und** eine zweite Zeile mit `pointer=<m>` bei gesetzter Nicht-`all`-Testconfig in `.tmp/`.

### M3 — Prosa-Vorkommen (D-3) und Golden-Sicherung
- **Ziel:** 5 Prosa-Stellen konditional; `all` unverändert (Golden-Gate grün), `core` grammatisch heil.
- **Tasks:** T9, T10.
- **Zwischentest-Gate:**
  - `python3 -m pytest tests/test_template_slimming_equivalence.py --basetemp="$PYTEST_BASETEMP"` (**unveränderte Datei, muss grün bleiben** — das ist der AC2-Beleg)
  - `python3 -m pytest tests/test_project_context_injection_render.py --basetemp="$PYTEST_BASETEMP"`

### M4 — Konsistenz, Admin-UI, Doku, Szenario
- **Ziel:** `pointer-missing`/`whitelist-no-effect`/`orchestrator-role-no-template`/`mode-unknown` laufen in `--validate`, die Sektion ist über die Admin-API schreibbar und im UI editierbar, Doku ist nachgezogen, ein Scratch-Konsument spielt alle vier Modi plus die D5/D6/D8-Fälle durch.
- **Tasks:** T11, T12, T13, T14, T15.
- **Zwischentest-Gate:**
  - `python3 -m pytest tests/test_project_context_injection_consistency.py tests/test_admin_ui_project_context_injection_section.py --basetemp="$PYTEST_BASETEMP"`
  - `python3 scripts/sync.py --validate` → PASS
  - `python3 scripts/sync.py --check` → DRY-RUN ohne neue Findings
  - `bash .tmp/scenario-context-1187/run.sh` → `SCENARIO OK` (T15)

---

## 4. Bite-sized TDD-Tasks

Konvention für alle Verifikationen: `python3 -m pytest <datei>::<test> --basetemp="$PYTEST_BASETEMP" -q`. Jeder Task beginnt mit dem fehlschlagenden Test.

---

### T1 — Schema-Sektion `project-context-injection`
**Datei:** `config/project-config.schema.json` (ändern) · `tests/test_project_context_injection_config.py` (neu)
**Test zuerst:**
- `test_schema_section_accepts_all_four_modes` — für `mode` in `("all","core+orchestrator","core+whitelist","core")` validiert `Draft7Validator(schema).is_valid({"project": {...}, "project-context-injection": {"mode": m}})` → `True`.
- `test_schema_section_rejects_unknown_key` — `{"project-context-injection": {"enabled": true}}` → ungültig (`additionalProperties: false`).
- `test_schema_section_rejects_duplicate_and_nonstring_whitelist` — `["developer","developer"]` und `[1]` ungültig (`uniqueItems`, `items.type`).
- `test_schema_defaults_are_mode_whitelist_orchestrator_pointer_language` — `properties[...]["properties"]["{mode,whitelist,orchestrator,pointer-language}"]["default"]` == `"all"` / `[]` / `"inherit"` / `"en"`.
- `test_schema_orchestrator_roles_and_pointer_text_have_no_default` — beide Property-Schemata enthalten **keinen** `default`-Schlüssel (D5/D8; ein materialisiertes `[]` bzw. ein eingefrorener Text würde die Semantik des nächsten Syncs ändern).
- `test_schema_section_accepts_orchestrator_roles_and_pointer_settings` — `{"orchestrator-roles": ["orchestrator","senior-developer"], "pointer-language": "de", "pointer-text": "Projektkontext: lies `{context_file}`."}` → gültig; `{"orchestrator-roles": ["senior-developer","senior-developer"]}` und `{"orchestrator-roles": [1]}` → ungültig.
- `test_schema_rejects_unknown_pointer_language_and_empty_pointer_text` — `{"pointer-language": "fr"}` ungültig (Enum), `{"pointer-text": ""}` ungültig (`minLength: 1`).
**Implementierung:** JSON-Property exakt wie Spec §4.1 (sechs Keys), eingefügt nach dem `context-profile`-Block (`:2849`) und vor `"required"` (`:2851`). `whitelist.items.pattern` und `orchestrator-roles.items.pattern`: `^[a-z0-9][a-z0-9-]*$`. `orchestrator-roles` und `pointer-text` **ohne** `default`.
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_config.py -k schema --basetemp="$PYTEST_BASETEMP" -q` → 7 passed.
**Abhängigkeiten:** keine · **Größe:** S

---

### T2 — Resolver `resolve_project_context_scope()` + Variablen
**Datei:** `scripts/lib/config.py` (ändern) · `tests/test_project_context_injection_config.py` (neu)
**Test zuerst:**
- `test_scope_absent_config_defaults_to_all` — `resolve_project_context_scope({}, root)` liefert `mode="all"`, `whitelist=[]`, `orchestrator="inherit"`, `orchestrator_roles=("orchestrator",)`, `pointer_language="en"`, `pointer_text` == der englische Defaulttext aus Spec §3.2 (zeichengenau), `present=False`; wirft nicht (Pflicht: `derive_builder_vars` ruft `build_variables({}, …)`, `placeholders.py:299-306`).
- `test_scope_null_section_is_all` — `{"project-context-injection": None}` → `mode="all"`, `present=False`.
- `test_scope_unknown_mode_raises_sync_error` — `mode: "slim"` → `SyncError` mit `project-context-injection.mode-unknown` **und** dem Wert `'slim'` in der Meldung.
- `test_scope_unknown_orchestrator_value_raises` — `orchestrator: "sometimes"` → `SyncError` `orchestrator-unknown`.
- `test_scope_whitelist_unknown_role_lists_all_names` — `["developer","nope","nada"]` → `SyncError`, Meldung enthält `nope` **und** `nada` (sortiert, kommagetrennt).
- `test_scope_whitelist_known_roles_accepted` — `["developer","planner"]` → ok (Namen aus `build_role_map`).
- `test_scope_orchestrator_roles_default_per_provider_set` (parametrisiert, 3 Fälle) — Config jeweils mit passender `ai-providers`-Liste, Fake-Registry: `{"Claude": {}}` → `("orchestrator",)`; `{"Claude": {}, "Lead": {"primary-role": "lead"}}` + `ai-providers: [Claude, Lead]` → `("lead", "orchestrator")` (sortiert); `{"Alpha": {}, "Beta": {"primary-role": "orchestrator"}}` + `ai-providers: [Alpha, Beta]` → `("orchestrator",)` (dedupliziert). Kein Provider-`if` — nur `pc.get("primary-role")`.
- `test_scope_orchestrator_roles_override_replaces_default` — `orchestrator-roles: ["senior-developer"]` → `("senior-developer",)`; **`orchestrator` ist nicht enthalten** (kein stilles Dazumischen).
- `test_scope_empty_orchestrator_roles_allowed` — `orchestrator-roles: []` → `()` und **kein** `SyncError`.
- `test_scope_orchestrator_roles_unknown_lists_all_names` — `["senior-developer","nope","nada"]` → `SyncError` `orchestrator-roles-unknown`, Meldung enthält `nope` und `nada`, **nicht** im Whitelist-Fehlercode.
- `test_scope_all_plus_exclude_warns_not_raises` — `mode: all` + `exclude` → **kein** `SyncError`; `warn_sink` enthält exakt `project-context-injection.exclude-overrides-mode: mode=all + orchestrator=exclude — orchestrator roles (orchestrator) excluded; exclude wins`.
- `test_scope_core_orchestrator_plus_exclude_warns_and_degrades` — `mode: core+orchestrator` + `exclude` → kein Raise; dieselbe WARN, `mode=core+orchestrator` im Text.
- `test_scope_core_plus_exclude_stays_silent` — `mode: core` + `exclude` → kein Raise, **kein** Warn-Eintrag.
- `test_scope_empty_set_with_core_orchestrator_warns` — `mode: core+orchestrator` + `orchestrator-roles: []` + `orchestrator: inherit` → WARN `project-context-injection.empty-orchestrator-set: mode=core+orchestrator + orchestrator-roles=[] — no role receives the block (mode degenerates to core)`.
- `test_exclude_and_empty_set_warn_once` — `exclude` **und** leere Menge → `warn_sink` enthält **genau einen** Eintrag (`exclude-overrides-mode`, Priorität vor `empty-orchestrator-set`).
- `test_pointer_language_defaults_to_en` — ohne `pointer-language` → `pointer_language == "en"` und `pointer_text` == englischer Default (§3.2.1, zeichengenau).
- `test_pointer_language_de_selects_german_default` — `pointer-language: "de"` → deutscher Default-Text, `{context_file}` genau einmal.
- `test_pointer_language_project_derives_from_communication_language` (parametrisiert) — `"Deutsch"`, `"de"`, `"German"` → `de`; `"English"`, `"en"` → `en`; Groß-/Kleinschreibung und Whitespace egal.
- `test_pointer_language_project_unknown_falls_back_with_warn` — `"Klingonisch"` → `pointer_language == "en"`, WARN `project-context-injection.pointer-language-fallback: COMMUNICATION_LANGUAGE='Klingonisch' has no pointer text — falling back to 'en'`.
- `test_pointer_text_override_wins_over_language` — `pointer-language: "de"` + `pointer-text: "See `{context_file}`."` → `pointer_text` == exakt der Override (kein deutscher Default).
- `test_pointer_text_unknown_token_raises` — `"Read {context_file} and {mode}."` → `SyncError` `pointer-text-unknown-token`, Meldung enthält `{mode}`.
- `test_pointer_text_requires_exactly_one_context_file_token` — `"Read the project file."` (0×) und `"{context_file} / {context_file}"` (2×) → `SyncError` `pointer-text-context-file-count`.
- `test_pointer_text_multiline_raises` — `"Read {context_file}\nfirst."` → `SyncError` `pointer-text-multiline`.
- `test_format_project_context_pointer_substitutes_token` — `format_project_context_pointer("Read `{context_file}`.", "AGENTS.md")` == ``"Read `AGENTS.md`."`` (pure Funktion, keine I/O).
- `test_build_variables_exposes_mode` — `build_variables({"project-context-injection": {"mode": "core"}}, root)[0]["PROJECT_CONTEXT_MODE"] == "core"`; `_PROJECT_CONTEXT_SCOPE` enthält `pointer_text`/`orchestrator_roles`.
**Implementierung (Signaturen):**
```python
PROJECT_CONTEXT_MODES: tuple[str, ...] = ("all", "core+orchestrator", "core+whitelist", "core")
PROJECT_CONTEXT_ORCHESTRATOR_VALUES: tuple[str, ...] = ("inherit", "include", "exclude")
PROJECT_CONTEXT_POINTER_LANGUAGES: tuple[str, ...] = ("en", "de", "project")

_PROJECT_CONTEXT_POINTER_TEXTS: dict[str, str] = {
    "en": "Project context: read `{context_file}` first — it is the single source for "
          "project-specific facts (embedded here only when "
          "`project-context-injection.mode` includes this role).",
    "de": "Projektkontext: lies zuerst `{context_file}` — sie ist die einzige Quelle für "
          "projektspezifische Fakten (hier nur eingebettet, wenn "
          "`project-context-injection.mode` diese Rolle einschließt).",
}
_POINTER_LANGUAGE_ALIASES: dict[str, str] = {
    "de": "de", "deutsch": "de", "german": "de", "ger": "de",
    "en": "en", "englisch": "en", "english": "en", "eng": "en",
}

def resolve_project_context_scope(
    config: dict, agent_meta_root: Path,
    provider_config: dict | None = None,
    communication_language: str | None = None,
    warn_sink: list[str] | None = None,
) -> dict:
    """{'mode': str, 'whitelist': list[str], 'orchestrator': str,
        'orchestrator_roles': tuple[str, ...], 'pointer_text': str,
        'pointer_language': str, 'present': bool}. Raises SyncError.

    ``provider_config=None`` loads ``config/ai-providers.yaml`` via
    load_providers_config(); tests inject a fake registry.
    ``communication_language`` is the already-defaulted value from
    ``variables['COMMUNICATION_LANGUAGE']`` (fallback 'Deutsch', config.py:221) —
    passed in so the resolver does not re-implement the fallback chain.
    ``warn_sink`` collects the D6/D8 warnings (drained into build_variables'
    pre_warnings, emitted once per run by cli_commands.py:691-692).
    """

def format_project_context_pointer(template: str, context_file: str) -> str:
    """Pure ``template.format(context_file=context_file)``. Token validity is
    enforced at resolve time, so this never raises for resolved scopes."""
```
Auflösung: `section = config.get("project-context-injection")`; Mapping → Werte prüfen, alles andere (None/String/Liste) → wie „fehlt" (`all`), aber `present=False`; ein **Mapping** mit falschen Enum-Werten → `SyncError` (`mode-unknown`, `orchestrator-unknown`, `pointer-language-unknown`). Rollen-Registry: `build_role_map(agent_meta_root)` (`roles.py:80`) für Whitelist **und** `orchestrator-roles` (getrennte Fehler-Codes).
**Orchestrator-Menge (D5):** fehlt `orchestrator-roles`, dann `tuple(sorted({"orchestrator"} | {pc["primary-role"] for provider in resolve_providers(...) if pc.get("primary-role")}))` — Datenquelle `config/ai-providers.yaml` über `provider_config[P]` (Beleg: `context.py:1711` liest `pc.get("primary-role")`), **kein** Provider-Namenszweig; ein vorhandener Key (auch `[]`) **ersetzt** die Menge.
**Orchestrator-Achse (D6):** `exclude` löst **nie** einen `SyncError` aus. WARN-Bedingungen und -Texte exakt wie Spec §3.1.2; Priorität `exclude-overrides-mode` vor `empty-orchestrator-set`; höchstens ein Eintrag pro Aufruf.
**Pointer (D8):** Präzedenz `pointer-text` > `pointer-language` > `en`; `project` mappt `communication_language` über `_POINTER_LANGUAGE_ALIASES` (case-insensitiv, getrimmt), unbekannt/leer → `en` + WARN `pointer-language-fallback`. `pointer-text`-Validierung: Tokens ⊆ {`{context_file}`} (alle anderen `{`/`}` = Fehler), genau **ein** `{context_file}`, **kein** Zeilenumbruch.
Aufruf am Ende von `build_variables` neben dem `context-profile`-Block (`:2810-2827`):
```python
variables["_PROJECT_CONTEXT_SCOPE"] = resolve_project_context_scope(
    config, agent_meta_root,
    communication_language=variables.get("COMMUNICATION_LANGUAGE"),
    warn_sink=unmapped,
)
variables["PROJECT_CONTEXT_MODE"] = variables["_PROJECT_CONTEXT_SCOPE"]["mode"]
```
`_SYNC_SKIPPED_DEFAULT_KEYS` (`:183-191`) um `"project-context-injection"` ergänzen. (Die Sektion hat **keinen** Top-Level-Default — die Defaults stehen nur in `properties.*.default`. Der einzige Nested-Fill-Zweig `:1379-1389` behandelt ausschließlich `dod.*`; der Eintrag ist deshalb ein **reiner Regressionsschutz** für eine künftige allgemeine Nested-Materialisierung, kein heute wirksamer Fix. `--fill-defaults`/`--init` dürfen die Sektion materialisieren, aber mangels Default **nicht** `orchestrator-roles`/`pointer-text` schreiben.)
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_config.py -k "scope or pointer or exclude or exposes or format" --basetemp="$PYTEST_BASETEMP" -q` → alle benannten Tests grün (24 Testfunktionen, davon 3 parametrisiert).
**Abhängigkeiten:** T1 · **Größe:** L

---

### T3 — Diagnose-Variablen registrieren (D-5) + Conditional-Whitelist
**Datei:** `scripts/lib/consistency/placeholders.py`, `scripts/lib/variables.py`, `scripts/lib/standalone.py` (ändern) · `tests/test_project_context_injection_config.py` (neu)
**Test zuerst:**
- `test_builtin_vars_contain_project_context_flags` — beide Namen in `_BUILTIN_VARS`.
- `test_builder_known_set_has_no_project_context_findings` — `check_builder_known_set(REPO_ROOT)` enthält keine Meldung mit `PROJECT_CONTEXT` (Muster: `tests/test_release_checklist_consistency.py:53-56`).
- `test_conditional_strip_removes_inactive_project_context_branch` — `strip_inactive_conditional_blocks("A{{#if PROJECT_CONTEXT_INJECTED}}X{{else}}Y{{/if}}B", {"PROJECT_CONTEXT_INJECTED": "false"})` == `"AYB"`; mit `"true"` == `"AXB"`.
- `test_standalone_flags_default_to_all` — `standalone`-Fallback-Dict liefert `PROJECT_CONTEXT_INJECTED == "true"` und `PROJECT_CONTEXT_MODE == "all"`.
**Implementierung:** `_BUILTIN_VARS` (`:12-45`) ergänzen um `"PROJECT_CONTEXT_MODE"`, `"PROJECT_CONTEXT_INJECTED"`; in `variables.py` die Sammelzeile `:570-572` bzw. eine neue `conditional_vars.update({"PROJECT_CONTEXT_INJECTED"})` in `:575-598` ergänzen. `PROJECT_CONTEXT_INJECTED` **nicht** in `_FALSE_DEFAULT_CONDITIONALS` (`:54-73`): fehlt der Wert (Standalone-/Direktrender), muss der historische `all`-Zweig aktiv bleiben — das ist die Bedingung für AC2 in Nebenpfaden.
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_config.py -k "builtin or strip or standalone" --basetemp="$PYTEST_BASETEMP" -q` → 4 passed; `python3 scripts/sync.py --validate` → PASS.
**Abhängigkeiten:** T2 · **Größe:** S

---

### T4 — Provider-Defaults in `_build_provider_vars`
**Datei:** `scripts/lib/agent_sync.py` (ändern) · `tests/test_project_context_injection_render.py` (neu)
**Test zuerst:**
- `test_provider_vars_default_injected_true_without_config` — `_build_provider_vars({}, "Claude", {"PROJECT_CONTEXT": "P"}, root)` → `merged["PROJECT_CONTEXT_INJECTED"] == "true"`, `merged["PROJECT_CONTEXT_MODE"] == "all"` (Rückwärtskompatibilität für `tests/test_orchestrator_name_dispatch.py:56`).
- `test_provider_vars_carry_scope_from_variables` — `variables={"_PROJECT_CONTEXT_SCOPE": {...mode: core}}` → `PROJECT_CONTEXT_INJECTED == "true"` (**noch** nicht rollenspezifisch; die Rolle entscheidet T5) und `PROJECT_CONTEXT_MODE == "core"`.
- `test_provider_vars_carry_formatted_pointer_per_provider` (parametrisiert, 3 Fälle) — `pc["context_file"]` = `CLAUDE.md` / `AGENTS.md` / `.continue/rules/project-context.md` → `_PROJECT_CONTEXT_POINTER` enthält genau diesen Wert und **kein** `{context_file}` mehr; deutscher `pointer_text` → deutscher Pointer mit demselben Dateinamen (D8).
**Implementierung:** im `provider_vars`-Dict (`:510-535`) bzw. nach dem `provider_vars.update(...)`-Block:
```python
scope = variables.get("_PROJECT_CONTEXT_SCOPE") or {}
provider_vars["PROJECT_CONTEXT_MODE"] = scope.get("mode", "all")
provider_vars["PROJECT_CONTEXT_INJECTED"] = "true"   # konservativer Default = heute
provider_vars["_PROJECT_CONTEXT_POINTER"] = format_project_context_pointer(
    scope.get("pointer_text") or _PROJECT_CONTEXT_POINTER_TEXTS["en"],
    provider_vars["CONTEXT_FILE"],
)
```
Mutieren von `merged_vars` bleibt sicher, weil `_build_provider_vars` mit `{**variables, **provider_vars}` (`:554`) eine flache Kopie zurückgibt. `_PROJECT_CONTEXT_POINTER` trägt einen führenden Unterstrich und wird damit von `derive_builder_vars` ausgefiltert (`placeholders.py:305-306`); es ist **kein** Template-Platzhalter. **Import:** `agent_sync.py` importiert `config` bewusst **nicht** auf Modulebene (Load-Time-Zyklus, Modul-Docstring `:8`); `format_project_context_pointer` und `_PROJECT_CONTEXT_POINTER_TEXTS` werden deshalb **lazy in `_build_provider_vars`** importiert — genau wie `resolve_subagent_permission_provider_vars` (`:551`).
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_render.py -k provider_vars --basetemp="$PYTEST_BASETEMP" -q` → 3 Testfunktionen grün (eine parametrisiert).
**Abhängigkeiten:** T2, T3 · **Größe:** S

---

### T5 — Per-Rolle-Injektionsentscheidung
**Datei:** `scripts/lib/agent_sync.py` (ändern) · `tests/test_project_context_injection_render.py` (neu)
**Test zuerst:**
- `test_injection_matrix` — parametrisiert `(mode, whitelist, orchestrator, role) → bool` exakt nach Spec §3.1-Tabellen (20 Fälle inkl. `core`+`include`, `core+whitelist`+`include`, `core+whitelist`+`inherit`, `all`+`inherit`, `all`+`exclude`, `core+orchestrator`+`exclude`, Whitelist-Rolle mit `primary-role`):
  - `all` → immer `True`, **außer** `exclude` und Rolle ∈ orchestrator_set (D6: „alle außer Orchestrator")
  - `core` → `False` außer `orchestrator == "include"` und Rolle ∈ orchestrator_set
  - `core+orchestrator` → nur orchestrator_set; bei `exclude` **niemand** (D6, Modus degeneriert zu `core`)
  - `core+whitelist` → **nur** Whitelist; orchestrator_set kommt **nur** bei `orchestrator == "include"` hinzu (`inherit` und `exclude` inkludieren keine Orchestrator-Rolle)
- `test_injection_matrix_uses_overridden_orchestrator_roles` — `orchestrator-roles: ["senior-developer"]` + `mode: core+orchestrator`: `senior-developer` → `True`, `orchestrator` → `False` (D5: Override ersetzt, kein Dazumischen).
- `test_injection_matrix_empty_orchestrator_roles` — `orchestrator-roles: []` + `mode: core+orchestrator` → jede Rolle `False`.
- `test_apply_scope_blanks_context_for_excluded_role` — `merged["PROJECT_CONTEXT"] == ""` und `PROJECT_CONTEXT_INJECTED == "false"`.
- `test_apply_scope_keeps_paragraph_for_included_role`.
- `test_apply_scope_does_not_mutate_shared_variables` — das übergebene `variables`-Dict behält seinen `PROJECT_CONTEXT`-Wert (Schutz gegen Leak über Rollen hinweg).
**Implementierung:**
```python
# scripts/lib/config.py (pure, keine I/O — auch vom Konsistenz-Check nutzbar)
def project_context_injected_for_role(scope: dict, role: str) -> bool:
    """Pure matrix from spec §3.1; never raises."""

# scripts/lib/agent_sync.py
def apply_project_context_scope(merged_vars: dict, role: str, scope: dict) -> bool:
    """Sets PROJECT_CONTEXT_INJECTED ('true'/'false') and blanks/locates
    merged_vars['PROJECT_CONTEXT']; returns the injected flag."""
```
`agent_sync` bezieht `project_context_injected_for_role` per **Lazy-Import** aus `.config` (kein Modul-Import — Zyklusvermeidung, `agent_sync.py:8`), damit `consistency/project_context_injection.py` keinen neuen Modul-Rand zu `agent_sync` braucht.
Aufruf in der Schleife (`:1458` nach `_build_provider_vars`, **vor** `_apply_content_pipeline` `:1460`), weil `substitute` (`:730`) und `strip_inactive_conditional_blocks` (`:737`) den Wert vorher brauchen (Spec §5.3 Schritte 3–5).
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_render.py -k "matrix or apply_scope" --basetemp="$PYTEST_BASETEMP" -q` → 21 Testfunktionen grün (zwei parametrisiert).
**Abhängigkeiten:** T4 · **Größe:** M

---

### T6 — Pointer-Zeile: Label-Cleanup + dreistufiger Fallback
**Datei:** `scripts/lib/agent_sync.py` (ändern) · `tests/test_project_context_injection_render.py` (neu)
**Test zuerst:**
- `test_pointer_line_text_is_exact` — der **Default**-Pointer (`_PROJECT_CONTEXT_POINTER_TEXTS["en"]`, Spec §3.2) ist zeichengenau: eine Zeile, Englisch, Backticks um `{context_file}`; kein Modul-lokales Duplikat in `agent_sync.py` (D8: eine Quelle in `config.py`).
- `test_pointer_german_default_used` — `pointer-language: "de"` → das gerenderte Artefakt enthält den deutschen Default (§3.2.1) inkl. aufgelöstem Dateinamen und **nicht** den englischen Text.
- `test_pointer_text_override_used_verbatim` — `pointer-text: "See `{context_file}` for project facts."` → exakt dieser String mit ersetztem Dateinamen; weder englischer noch deutscher Default.
- `test_pointer_uses_resolved_context_file_per_provider` — Claude → `CLAUDE.md`, Gemini → `AGENTS.md`, Opencode → `AGENTS.md`, Continue → `.continue/rules/project-context.md` (Quelle `pc["context_file"]`, `agent_sync.py:515`).
- `test_pointer_inserted_at_end_of_context_section` — gerendertes `developer.md` in `core`: Pointer steht vor `</context>` (`developer.md:92`), **eine** Zeile.
- `test_pointer_inserted_before_workflow_when_no_context_section` — `intern-developer.md` (kein `<context>`, `</workflow>` `:39`) → Pointer vor `</workflow>`.
- `test_pointer_appended_at_eof_with_note` — `mammouth-expert.md` **und** je eine `se-*`-Rolle (weder `<context>` noch `</workflow>`) → Pointer am Dateiende **und** `log.note("project-context-injection", "no <context>/</workflow> in mammouth-expert.md — pointer appended at EOF")`.
- `test_dangling_project_context_label_is_removed` — Template-Form `**Project context:** {{PROJECT_CONTEXT}}` (60 Dateien, z. B. `orchestrator.md:316`): in `core` enthält das Artefakt **kein** `**Project context:**` mehr. Diese Mechanik ist jetzt in Spec §3.2/§3.6 D-2 verbindlich dokumentiert (kein reines Plan-Detail mehr).
- `test_no_pointer_when_injected` — `all` enthält die Pointer-Zeile nicht.
- `test_exactly_one_pointer_per_excluded_role` — über **alle 98** Rollen eines Providerlaufs: `content.count(pointer) == 1` für exkludierte, `== 0` für inkludierte Rollen; der Lauf enthält mindestens eine Rolle aus jeder Fallback-Gruppe (`developer` = `<context>`, `intern-developer` = `</workflow>`, `se-architect` + `mammouth-expert` = Dateiende).
**Implementierung:**
```python
def insert_project_context_pointer(content: str, pointer: str, role: str,
                                   source_name: str, log) -> str:
    """1) drop an empty '**Project context:**' label line (only when the line
        contains nothing else); 2) insert `pointer` as one line before the
        last '</context>', else before the last '</workflow>', else append at
        EOF and emit a note."""
```
`pointer` ist **immer** `merged_vars["_PROJECT_CONTEXT_POINTER"]` (T4) — kein Modul-lokales Text-Literal mehr; damit gelten Sprache/Override aus §3.2.1 automatisch für alle Provider und alle Fallback-Gruppen.
Reihenfolge: erst Label-Cleanup (Regex `^[ \t]*\*\*Project context:\*\*[ \t]*\r?\n`, `re.MULTILINE`), dann Einfügen. Der Cleanup läuft **nur** im Nicht-Injiziert-Zweig, deshalb bleibt `all` byte-identisch. Insert-Semantik: `content.rfind("</context>")` (Zeilenanfang berücksichtigen, Pointer-Zeile + `\n` davor), sonst `rfind("</workflow>")`, sonst `content.rstrip("\n") + "\n\n" + pointer + "\n"`. Für Rollen mit Block-Vorkommen kommt der Aufruf nach dem Blanking; für Rollen ohne Vorkommen (`se-*`, `mammouth-expert`, `intern-developer`) nur der Insert-Teil.
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_render.py -k "pointer or dangling" --basetemp="$PYTEST_BASETEMP" -q` → 10 Testfunktionen grün.
**Abhängigkeiten:** T5 · **Größe:** M

---

### T7 — Delta-Zähler und Log-Zeile (AC6)
**Datei:** `scripts/lib/agent_sync.py` (ändern) · `tests/test_project_context_injection_render.py` (neu)
**Test zuerst:**
- `test_log_line_format_all_mode` — Log enthält `project-context-injection: mode=all injected=<n>/<n> roles, pointer=0, chars saved=0 (vs mode=all)`.
- `test_log_line_counts_pointer_and_savings` — `core` mit 3 Rollen: `pointer=3`, `chars saved` == `Σ len(Absatz)` über die 3 Rollen `-` `3 * len(pointer)` (nur Rollen **mit** Blockvorkommen zählen positiv; Rollen ohne Vorkommen tragen nur `-len(pointer)` bei).
- `test_chars_saved_is_zero_for_all` — exakt `0`, nicht „ungefähr".
- `test_log_line_emitted_in_dry_run` — `dry_run=True` erzeugt dieselbe Zeile (AC6 „`--check`-Ausgabe").
**Implementierung:** lokale Zähler in `sync_agents_for_provider` vor der Schleife (`:1441`): `roles_seen`, `roles_injected`, `pointer_lines`, `chars_removed`, `chars_added`; nach `_cleanup_stale_agents` (`:1479`) bzw. direkt nach der Schleife:
```python
log.note("project-context-injection",
         f"mode={mode} injected={roles_injected}/{roles_seen} roles, "
         f"pointer={pointer_lines}, chars saved={chars_removed - chars_added} (vs mode=all)")
```
`len(...)` gegen den **vor** dem Blanking gemessenen Absatz (in T5 mitführen), nicht gegen `merged_vars` nach der Mutation.
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_render.py -k log_line --basetemp="$PYTEST_BASETEMP" -q` → 4 passed.
**Abhängigkeiten:** T6 · **Größe:** S

---

### T8 — Render-Verträge je Modus (AC2, AC3, AC4, AC5)
**Datei:** `tests/test_project_context_injection_render.py` (neu)
**Test zuerst (Render-Helfer, Muster `tests/test_template_slimming_equivalence.py:1191-1240`):**
```python
def _render(role: str, config: dict, tmp_path: Path) -> str:
    """load_config-Ersatz: config direkt übergeben; build_variables + echte
    _compose_role_content → _apply_content_pipeline → _finalize_agent_content."""
```
- `test_all_matches_default_absent_key` — `{}` vs `{"project-context-injection": {"mode": "all"}}` → byte-identisch für `developer`, `orchestrator`, `ui-ux-designer`, `bug-feature-analyzer`, `knowledge-curator`, `knowledge-migrator`, `intern-developer`, `mammouth-expert`.
- `test_core_renders_zero_blocks` — `content.count("<Absatz>") == 0` für alle 8 Rollen; `content.count(pointer) == 1`.
- `test_core_whitelist_only_whitelisted_roles` — `whitelist: ["developer"]` (Default `orchestrator: inherit`): `developer` enthält Absatz, `planner` nicht, **`orchestrator` nicht** (weil `inherit` nicht inkludiert), und je 1 Pointer für die anderen.
- `test_core_whitelist_include_adds_orchestrator` — `mode: core+whitelist`, `orchestrator: include`: Absatz in `developer` **und** `orchestrator`; `exclude`/`inherit` bleiben bei Whitelist-only.
- `test_core_whitelist_unknown_name_fails_render` — `SyncError` mit Namen in der Meldung (Integration über `build_variables`, nicht nur Resolver-Unit).
- `test_core_orchestrator_only_orchestrator_roles` — Absatz in `orchestrator` **und** in einer `primary-role`-Rolle des Test-Provider-Sets, in `developer` nicht.
- `test_core_include_moves_orchestrator_in` — `mode: core` + `orchestrator: include` → Absatz in `orchestrator`.
- `test_core_keeps_required_sections_non_empty` — für `core` enthält jedes der 8 Artefakte weiterhin seine Pflichtsektionen; `<context>` bleibt nicht-leer, **wo das Template eine hat** (`intern-developer` und `mammouth-expert` haben keine — dort wird der Pointer-Fallback geprüft, nicht eine erfundene `<context>`-Sektion). AC7-Vorstufe (D7: Frontmatter-/Platzhalter-Checks bleiben grün).
- `test_all_plus_exclude_only_orchestrator_excluded` — `mode: all` + `exclude` (D6): `orchestrator` enthält **keinen** Absatz, aber den Pointer; `developer` unverändert mit Absatz; der Lauf ist **kein** Fehler; die WARN `exclude-overrides-mode` steht genau einmal im Log.
- `test_core_orchestrator_with_overridden_roles` — `mode: core+orchestrator` + `orchestrator-roles: ["senior-developer"]`: Absatz in `senior-developer`, **nicht** in `orchestrator`, nicht in `developer` (D5).
- `test_core_orchestrator_with_empty_roles_injects_nothing` — `orchestrator-roles: []` → **keine** Rolle erhält den Absatz, jede erhält genau einen Pointer; WARN `empty-orchestrator-set` genau einmal.
- `test_pointer_language_de_renders_german_pointer` — `pointer-language: "de"` in `core`: jedes Artefakt enthält den deutschen Pointer mit dem jeweiligen `context_file`-Wert (Claude `CLAUDE.md`, Gemini `AGENTS.md`); `mode: all` bleibt davon unberührt (kein Pointer).
**Implementierung:** nur Testdatei.
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_render.py --basetemp="$PYTEST_BASETEMP" -q` → alle Tests grün.
**Abhängigkeiten:** T7 · **Größe:** M

---

### T9 — Prosa-Vorkommen auf `{{#if}}` umstellen (D-3) + Versionsbumps
**Datei:** `agents/1-generic/ui-ux-designer.md`, `bug-feature-analyzer.md`, `knowledge-curator.md`, `knowledge-migrator.md` (ändern) · `tests/test_project_context_injection_render.py` (neu)
**Test zuerst:**
- `test_no_bare_prose_placeholder_remains` — in den vier Templates steht kein `{{PROJECT_CONTEXT}}` mehr ohne umschließendes `{{#if PROJECT_CONTEXT_INJECTED}}` (Regex-Zählung pro Datei: Vorkommen == Vorkommen innerhalb eines `#if`-Blocks).
- `test_core_prose_stays_grammatical` — `core`-Render von `ui-ux-designer` enthält `` `CLAUDE.md` provides the design vision `` und **nicht** `` ```` provides the design vision `` (doppelte Backticks/leerer Inhalt).
- `test_all_prose_matches_golden` — `all`-Render der vier Rollen gegen `tests/fixtures/slimming-golden/<role>.md` (Portierung volatiler Meta-Tokens über `from test_template_slimming_equivalence import _port_golden_meta_tokens`, `sys.path.insert(0, str(Path(__file__).parent))`).
**Implementierung (exakt fünf Stellen):**
1. `ui-ux-designer.md:77`: `` `{{PROJECT_CONTEXT}}` provides `` → `` {{#if PROJECT_CONTEXT_INJECTED}}`{{PROJECT_CONTEXT}}`{{else}}`{{CONTEXT_FILE}}`{{/if}} provides ``
2. `ui-ux-designer.md:105`: `` - No designs without a `{{PROJECT_CONTEXT}}` reference `` → `` - No designs without a {{#if PROJECT_CONTEXT_INJECTED}}`{{PROJECT_CONTEXT}}`{{else}}`{{CONTEXT_FILE}}`{{/if}} reference ``
3. `bug-feature-analyzer.md:40`: `` Behavior covered by `{{PROJECT_CONTEXT}}`? `` → `` Behavior covered by {{#if PROJECT_CONTEXT_INJECTED}}`{{PROJECT_CONTEXT}}`{{else}}`{{CONTEXT_FILE}}`{{/if}}? ``
4. `knowledge-curator.md:55`: `` Liest `{{PROJECT_CONTEXT}}`, `` → `` Liest {{#if PROJECT_CONTEXT_INJECTED}}`{{PROJECT_CONTEXT}}`{{else}}`{{CONTEXT_FILE}}`{{/if}}, ``
5. `knowledge-migrator.md:38`: `` 1. Lies `{{PROJECT_CONTEXT}}` — `` → `` 1. Lies {{#if PROJECT_CONTEXT_INJECTED}}`{{PROJECT_CONTEXT}}`{{else}}`{{CONTEXT_FILE}}`{{/if}} — ``

Die 4 Block-Vorkommen (`ui-ux-designer.md:72`, `bug-feature-analyzer.md:76`, `knowledge-curator.md:22`, `knowledge-migrator.md:26`) bleiben **unverändert** — sie werden vom Renderer über den Variablenwert gesteuert. (Die „5" im vorigen Absatz zählt die Prosa-Stellen, nicht die Block-Vorkommen.) Versionsbumps: `ui-ux-designer` 1.6.0→1.6.1, `bug-feature-analyzer` 1.5.1→1.5.2, `knowledge-curator` 1.4.2→1.4.3, `knowledge-migrator` 1.5.2→1.5.3 (Konvention `rules/2-platform/agent-meta-conventions.md:111-123`). Keine `2-platform`-Datei hängt von diesen vier ab (`based-on`-Suche leer).
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_render.py -k prose --basetemp="$PYTEST_BASETEMP" -q` → 3 passed.
**Abhängigkeiten:** T5, T8 · **Größe:** M

---

### T10 — Golden-Gate unverändert grün (AC2-Beleg)
**Datei:** keine Änderung — `tests/test_template_slimming_equivalence.py` (nur ausführen) · `tests/test_project_context_injection_render.py` (neu)
**Test zuerst:** Der Test existiert bereits; der Beweis ist der **unveränderte, grüne** Lauf. Zusätzlich:
- `test_golden_gate_file_untouched_by_this_issue` — `subprocess.run(["git","diff","--name-only","aaed14c2..HEAD","--","tests/test_template_slimming_equivalence.py","tests/fixtures/slimming-golden"])` liefert **leeren** Output (eingefrorener Basis-Hash; `HEAD` allein wäre nach dem Commit vakuum-grün). Muster in `tests/test_context_compact_mode.py:24-26`, aber mit explizitem Basis-Hash statt `HEAD`.
**Implementierung:** nichts. Wenn der Golden-Lauf nach T9 rot wird, ist die D-3-Umsetzung falsch — **nicht** die Fixtures rebaselinen.
**Verifikation:** `python3 -m pytest tests/test_template_slimming_equivalence.py --basetemp="$PYTEST_BASETEMP" -q` → grün, ohne Fixture-Änderung.
**Abhängigkeiten:** T9 · **Größe:** S

---

### T11 — Konsistenz-Checks (4 IDs) + Registrierung
**Datei:** `scripts/lib/consistency/project_context_injection.py` (neu), `scripts/consistency-check.py` (ändern) · `tests/test_project_context_injection_consistency.py` (neu)
**Test zuerst:**
- `test_mode_unknown_is_error` — Config mit `mode: "slim"` → `Finding(severity=ERROR, check="project-context-injection.mode-unknown")`, ohne `jsonschema`-Abhängigkeit.
- `test_whitelist_no_effect_warns_for_other_mode` — `{"mode": "core", "whitelist": ["developer"]}` → `WARN`, Meldung „whitelist ignored (mode=core)".
- `test_whitelist_no_effect_warns_for_role_without_placeholder` — `mode: core+whitelist`, Whitelist enthält `se-architect` (kein Vorkommen) → `WARN`, Datei `agents/1-generic/se-architect.md` in der Meldung.
- `test_pointer_missing_warns_when_artifact_lacks_pointer` — Fixture-Projektverzeichnis mit `CLAUDE.md` + `.claude/agents/developer.md` ohne Pointer, `mode: core` → `WARN` `pointer-missing`.
- `test_pointer_present_is_clean` — Artefakt mit genau einer Pointer-Zeile → keine Findings.
- `test_pointer_missing_accepts_german_and_overridden_pointer` (D8) — `pointer-language: "de"` bzw. `pointer-text`-Override: ein Artefakt mit dem **konfigurierten** Pointer ist clean; der englische Default-Pointer wird in diesem Fall als `pointer-missing` gemeldet (der Check darf nicht hart auf den Default-String prüfen).
- `test_pointer_missing_uses_orchestrator_roles_override` — `orchestrator-roles: ["senior-developer"]`, `mode: core+orchestrator`: `senior-developer.md` **ohne** Pointer ist ein Finding, `orchestrator.md` **ohne** Pointer nicht (D5).
- `test_orchestrator_role_no_template_warns` — `orchestrator-roles: ["se-architect"]` (Registry-Rolle ohne `{{PROJECT_CONTEXT}}`) → WARN `orchestrator-role-no-template` mit `se-architect` und dem Dateipfad in der Meldung (D5).
- `test_check_registered_in_run_checks` — `check_project_context_injection` im Import-Block und im Provider-Block von `scripts/consistency-check.py` referenziert (Quelltext-Assertion).
**Implementierung:**
```python
def check_project_context_injection(root: Path, config: dict | None = None,
                                   provider_config: dict | None = None) -> list[Finding]:
    """4 IDs: mode-unknown (ERROR), whitelist-no-effect (WARN),
    orchestrator-role-no-template (WARN), pointer-missing (WARN).
    Fail-soft: fehlende Sektion => []."""
```
Datenquelle für `pointer-missing`: pro aktivem Provider (`resolve_providers`) `<agents_dir>/*.md` lesen (Muster `context_size.py:91-100`), Rolle = Datei-Stem, erwartete Injektion aus `resolve_project_context_scope` (mit `communication_language=config["variables"].get("COMMUNICATION_LANGUAGE")`) + `project_context_injected_for_role` (beide `lib.config`), erwarteter Pointer-Text über `format_project_context_pointer(scope["pointer_text"], pc["context_file"])` — **nicht** über ein hartkodiertes Literal (D8). WARN-Fälle aus dem Resolver (`exclude-overrides-mode`, `empty-orchestrator-set`, `pointer-language-fallback`) werden hier **nicht** dupliziert; sie entstehen in `build_variables` (einmal pro Lauf).
Keine Datei → überspringen (nie Fehler). Registrierung in `scripts/consistency-check.py:251-267`.
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_consistency.py --basetemp="$PYTEST_BASETEMP" -q` → 9 Testfunktionen grün; `python3 scripts/sync.py --validate` → PASS.
**Abhängigkeiten:** T5, T8 · **Größe:** M

---

### T12 — Admin-API-Schreibbarkeit
**Datei:** `scripts/admin-server.py` (ändern) · `tests/test_admin_ui_project_context_injection_section.py` (neu)
**Test zuerst:**
- `test_whitelist_contains_section` — `"project-context-injection" in admin_server.PROJECT_WRITABLE_SECTIONS`.
- `test_valid_payload_round_trips` — `_post(h, "project-context-injection", {"mode": "core"})` → `config_manager.read("project")["project-context-injection"] == {"mode": "core"}` (Helfer `tests/_te_admin_helpers.py`).
- `test_invalid_section_still_400` — `_post(h, "project-context-injectio", {...})` → HTTP 400 mit `section not allowed` (Regressionsschutz).
- `test_roundtrip_does_not_touch_other_sections` — `git`-Sektion bleibt unverändert (Guard `:5257-5274`).
**Implementierung:** String in das `frozenset` (`:234-259`) aufnehmen, z. B. neben `"context-profile"` (`:243`). Kein neuer Endpoint.
**Verifikation:** `python3 -m pytest tests/test_admin_ui_project_context_injection_section.py --basetemp="$PYTEST_BASETEMP" -q` → 4 passed.
**Abhängigkeiten:** T1 · **Größe:** S

---

### T13 — Admin-UI-Pane + Help-ID
**Datei:** `docs/ui/admin-ui.html`, `docs/api/admin-ui-reference.md` (ändern) · `tests/test_admin_ui_project_context_injection_section.py` (neu)
**Test zuerst:**
- `test_nav_router_and_routemap_entries_exist` — `"/project/project-context-injection"` in Nav (`:1632`-Nachbarschaft), `router.register` (`:11264`-Nachbarschaft) und `routeMap` (`:11381`-Nachbarschaft) vorhanden (String-Assertions wie `tests/test_context_profile_admin.py:39-48`).
- `test_pane_persists_own_section` — UI-Quelltext enthält `saveProjectSection("project-context-injection"`.
- `test_pane_offers_mode_and_orchestrator_enums` — Quelltext enthält `["all", "core+orchestrator", "core+whitelist", "core"]`, `["inherit", "include", "exclude"]` und `["en", "de", "project"]` (D8: Pointer-Sprache).
- `test_pane_persists_orchestrator_roles_and_pointer_text` — Quelltext enthält die Feld-Schlüssel `orchestrator-roles` und `pointer-text` und unterscheidet „Key weglassen" (Default-Ableitung) von „leere Liste" (D5).
- `test_help_id_mapping_present` — `check_ui_help_mappings(REPO_ROOT)` liefert kein Finding für `project_instance-project_context_injection`.
**Implementierung:** `async function viewProjectContextInjection(wrap)` (Muster `viewProjectAutoCommit` `:7649-7761`): `const data = await loadProject();` → `const pci = (data["project-context-injection"] && typeof … === "object") ? clone(...) : {};`; Felder: Modus-Select, Whitelist-Multi-Select, Orchestrator-Select, **Orchestrator-Rollen-Multi-Select mit „Default-Ableitung"-Schalter** (Schalter an ⇒ Key *weglassen*, Schalter aus + leere Auswahl ⇒ `[]`), **Pointer-Sprache-Select `["en","de","project"]`**, **einzeiliges Pointer-Text-Feld** (Platzhalter-Hinweis „erlaubtes Token: `{context_file}`"; mehrzeilig/leer wird clientseitig abgelehnt, serverseitig hart geprüft); Whitelist-/Rollen-Optionen: `api.get("/api/config/role-defaults")` (super-admin-Pfad, `:1901`), bei Fehler `data.roles || []`, bei beidem leer Freitext-Comma-Eingabe; Save: `saveProjectSection("project-context-injection", out, status)`. Zusätzlich read-only Effekt-Vorschau „Rolle → injiziert ja/nein" (JS-Spiegel der Matrix inkl. `orchestrator-roles`/`exclude`, mit Hinweis „Server ist maßgeblich"). Help-Block in `docs/api/admin-ui-reference.md` nach dem Muster `<!-- help-id: project_instance-auto_commit -->` (`:182`).
**Verifikation:** `python3 -m pytest tests/test_admin_ui_project_context_injection_section.py --basetemp="$PYTEST_BASETEMP" -q`; `python3 scripts/sync.py --validate` → PASS (inkl. `docs.ui_help_mappings`).
**Abhängigkeiten:** T12 · **Größe:** M

---

### T14 — Doku
**Datei:** `docs/guides/features/sync-concept.md`, `howto/configs/project.yaml.example`, `templates/configs/project.yaml.example`, `CHANGELOG.md` (ändern) · `tests/test_project_context_injection_config.py` (neu)
**Test zuerst:**
- `test_sync_concept_documents_both_variables` — beide Variablennamen stehen in der Tabelle `:278-292`.
- `test_project_example_documents_section` — **beide** Beispiel-Dateien (`howto/configs/project.yaml.example` und `templates/configs/project.yaml.example`) enthalten einen auskommentierten `project-context-injection`-Block mit **allen sechs** Keys (`mode`, `whitelist`, `orchestrator`, `orchestrator-roles`, `pointer-language`, `pointer-text`) und dem Hinweis „fehlender `orchestrator-roles`-Key = Default-Ableitung, `[]` = keine Orchestrator-Rolle"; der Test parametrisiert über beide Pfade, damit die Sektion nicht divergiert.
- `test_changelog_mentions_issue_1187` — `CHANGELOG.md` enthält `#1187`.
**Implementierung:** je ein Tabelleneintrag + Beispielblock in **beiden** Beispiel-Dateien (sie dokumentieren dieselbe Sektion, `howto/…` ist das ausführliche Template, `templates/…` das kondensierte) + Changelog-Zeile. Kein `--explain`, kein Preset (Spec §3.4). `docs/guides/project.yaml.example` ist ein Orchestrator-Fragment und wird **nicht** angefasst.
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_config.py -k "docs or changelog or example" --basetemp="$PYTEST_BASETEMP" -q` → 3 passed.
**Abhängigkeiten:** T2 · **Größe:** S

---

### T15 — Voller Szenarientest (Scratch-Konsument) + Gesamt-Regression
**Datei:** `.tmp/scenario-context-1187/` (Scratch, **kein** Repo-Artefakt) + `docs/plans/2026-11-09-project-context-injection-scope-plan.md` (Ausführungsnachweis anhängen)
**Test zuerst (ausführbares Shell-Szenario `run.sh`, das die Asserts enthält):**
1. `mkdir -p .tmp/scenario-context-1187/{project,meta}`; `meta/` = Symlink/Checkout des Arbeitsbaums; `project/.meta-config/project.yaml` mit `project{name,prefix,description}`, `ai-providers: [Claude, Opencode, Gemini]`, `roles: [orchestrator, senior-developer, developer, planner, ui-ux-designer, se-architect, mammouth-expert, intern-developer]` (`senior-developer` ist die Override-Zielrolle für D5; die beiden letzten decken die `</workflow>`- und die Dateiende-Fallback-Gruppe ab).
2. Lauf A (`Sektion fehlt`) → Snapshot `.claude/agents`, `.opencode/agents`, `.gemini/agents`; danach `grep -c '^project-context-injection:' .meta-config/project.yaml` == `0` (der Sync materialisiert die Sektion **nicht**; die Assertion gehört hierher, weil Lauf B die Sektion selbst in die Test-Config schreibt).
3. Lauf B (`mode: all`) → `diff -r` gegen A **leer** (AC2).
4. Lauf C (`mode: core`) → `grep -c "Project context:" `.claude/agents/developer.md` == `1`; Absatz fehlt (AC3); `grep -c "CLAUDE.md"` ≥ `1`; `AGENTS.md` in `.gemini/agents/developer.md` (nicht `GEMINI.md`); `mammouth-expert.md` und `se-architect.md` haben je genau eine Pointer-Zeile am Dateiende; `intern-developer.md` hat sie vor `</workflow>`; Logzeile enthält `mode=core` und `chars saved=` > 0 (AC6).
5. Lauf D (`mode: core+whitelist`, `whitelist: [developer]`, `orchestrator` fehlt ⇒ `inherit`) → Absatz nur in `developer.md`; **`orchestrator.md` ohne Absatz**; unbekannter Name (`whitelist: [nope]`) → Exit ≠ 0, `nope` in stderr (AC4).
6. Lauf E (`mode: core+orchestrator`) → Absatz nur in `orchestrator.md` (+ `primary-role`-Rollen) (AC5). Zusatzlauf `core+whitelist` + `orchestrator: include` → `orchestrator.md` **mit** Absatz.
7. Lauf F (D6): `mode: all` + `orchestrator: exclude` → Exit **0**; `orchestrator.md` **ohne** Absatz, aber mit genau einer Pointer-Zeile; `developer.md` mit Absatz („alle außer Orchestrator"); stderr enthält **genau eine** Zeile mit `project-context-injection.exclude-overrides-mode`, `mode=all` und `exclude wins`. Zusatzlauf `mode: core+orchestrator` + `exclude` → Exit **0**, **keine** Rolle mit Absatz, dieselbe WARN mit `mode=core+orchestrator`. **Kein** Lauf erwartet einen Fehler. `mode: core` + `exclude` bleibt erlaubt und erzeugt **keine** WARN. Gekoppelt an `test_scope_all_plus_exclude_warns_not_raises` und `test_scope_core_orchestrator_plus_exclude_warns_and_degrades` (T2).
   - **Lauf G (D5):** `mode: core+orchestrator` + `orchestrator-roles: [senior-developer]` → Absatz **nur** in `senior-developer.md`; `orchestrator.md` ohne Absatz, mit Pointer. Zusatzlauf `orchestrator-roles: []` → Exit **0**, keine Rolle mit Absatz, genau eine WARN `empty-orchestrator-set`. Zusatzlauf `orchestrator-roles: [nope]` → Exit ≠ 0, `nope` in stderr, Fehlercode `orchestrator-roles-unknown`.
   - **Lauf H (D8):** `mode: core` + `pointer-language: de` → jede Rollendatei enthält den deutschen Pointer (z. B. „Projektkontext: lies zuerst `CLAUDE.md`"), **nicht** den englischen. Zusatzlauf `pointer-text: "See \`{context_file}\` for project facts."` → exakt dieser Text mit ersetztem Dateinamen. Negativ: `pointer-text: "Read {context_file} and {mode}."` → Exit ≠ 0 mit `pointer-text-unknown-token` und `{mode}` in stderr; `pointer-language: fr` → Exit ≠ 0 mit `pointer-language-unknown`.
8. `python3 scripts/sync.py --validate` im Konsumenten → PASS (AC7); die Materialisierungs-Assertion (`grep -c '^project-context-injection:' == 0`) steht in Schritt 2 (Lauf A), **nicht** nach Lauf B — dort setzt die Test-Config die Sektion selbst. **Keine** Byte-Identitäts-Assertion der ganzen Datei, weil strukturelle Auto-Fills sie ändern.
9. Negativ-Assertions gegen den eingefrorenen Basis-Hash: `git diff --name-only aaed14c2..HEAD -- schemas/a2a-handoff.schema.json tests/test_template_slimming_equivalence.py tests/fixtures/slimming-golden` ist leer (nicht `HEAD` allein — nach dem Commit wäre das vakuum-grün).
**Implementierung:** `run.sh` mit `set -euo pipefail` und einem `assert_eq`/`assert_contains`-Helper; Exit `SCENARIO OK`. Ergebnisse (Datum, HEAD, 5 Logzeilen) in einem Abschnitt „Ausführungsnachweis" am Planende dokumentieren. Falls der Wave-Orchestrator das Szenario doch in `tests/scenarios/registry.md` registriert, sind `95`–`98` für #1187 reserviert (`94` gehört #1181, `99` #1186).
**Zusätzlich (Regression):** `python3 -m pytest tests/test_project_context_injection_config.py tests/test_project_context_injection_render.py tests/test_project_context_injection_consistency.py tests/test_admin_ui_project_context_injection_section.py tests/test_template_slimming_equivalence.py tests/test_admin_server.py tests/test_context_profile_admin.py --basetemp="$PYTEST_BASETEMP" -q`.
**Verifikation:** `bash .tmp/scenario-context-1187/run.sh` → `SCENARIO OK`; Regression grün.
**Abhängigkeiten:** T1-T14 · **Größe:** L

---

## 5. Interfaces & Signaturen

### 5.1 Config-Keys (`project.yaml`)

| Key | Typ | Default | Auflösungsort |
|---|---|---|---|
| `project-context-injection.mode` | `"all" \| "core+orchestrator" \| "core+whitelist" \| "core"` | `all` | `config.resolve_project_context_scope` |
| `project-context-injection.whitelist` | `string[]`, unique, Pattern `^[a-z0-9][a-z0-9-]*$` | `[]` | dito; nur bei `core+whitelist` ausgewertet |
| `project-context-injection.orchestrator` | `"inherit" \| "include" \| "exclude"` | `inherit` | dito |
| `project-context-injection.orchestrator-roles` | `string[]`, unique, gleiches Pattern | **kein Default** (fehlt = `{orchestrator} ∪ primary-role` aktiver Provider; `[]` = leere Menge) | dito (D5) |
| `project-context-injection.pointer-language` | `"en" \| "de" \| "project"` | `en` | dito (D8) |
| `project-context-injection.pointer-text` | String, ≥ 1 Zeichen, genau ein `{context_file}`, einzeilig | **kein Default** (fehlt = Sprach-Default) | dito (D8) |

Harte Fehler (`SyncError`, rc 1, ohne Traceback): unbekannter `mode`/`orchestrator`/`pointer-language`-Wert; unbekannter Whitelist-Rollenname (alle Namen in der Meldung); unbekannter Rollenname in `orchestrator-roles` (alle Namen, eigener Fehler-Code); `pointer-text` mit Fremd-Token, ≠ 1 × `{context_file}` oder Zeilenumbruch. **Kein** harter Fehler mehr für `orchestrator: exclude` (D6).
Sync-Warnungen (`log.warn`, einmal pro Lauf): `exclude` bei `mode ∈ {all, core+orchestrator}`; leere Orchestrator-Menge bei `mode: core+orchestrator`; `pointer-language: project` ohne abbildbare `COMMUNICATION_LANGUAGE`; Rolle ohne `<context>`/`</workflow>` beim Pointer-Fallback (`log.note`). Konsistenz-Check-WARNs (`--validate`, §5.4 der Spec): Whitelist/Modus ohne Wirkung; `orchestrator-roles`-Eintrag ohne Platzhalter.

### 5.2 Variablen-Vertrag

| Variable | Werte | Gesetzt in | Default bei fehlendem Kontext |
|---|---|---|---|
| `PROJECT_CONTEXT` | Absatz oder `""` | `agent_sync.apply_project_context_scope` (pro Rolle) | Absatz (Fallback `config.py:1860-1861`) |
| `PROJECT_CONTEXT_MODE` | 4 Enum-Werte | `config.build_variables` | `"all"` |
| `PROJECT_CONTEXT_INJECTED` | `"true"`/`"false"` | `agent_sync.apply_project_context_scope` | `"true"` (`_build_provider_vars`) |
| `CONTEXT_FILE` | Provider-Kontextdatei | `_build_provider_vars` (`:515`) | unverändert |
| `_PROJECT_CONTEXT_POINTER` | aufgelöster Pointer-Text dieses Providers | `_build_provider_vars` (`format_project_context_pointer`) | englischer Default |

Interne Träger-Variablen (führender Unterstrich ⇒ von `derive_builder_vars` ausgefiltert, `placeholders.py:305-306`): `_PROJECT_CONTEXT_SCOPE` (`dict` mit `mode`, `whitelist`, `orchestrator`, `orchestrator_roles`, `pointer_text`, `pointer_language`, `present`) und `_PROJECT_CONTEXT_POINTER` (`str`, pro Provider).

### 5.3 Pointer-Vertrag

```
Project context: read `{context_file}` first — it is the single source for project-specific facts (embedded here only when `project-context-injection.mode` includes this role).
```

Deutscher Default (nur bei `pointer-language: de` bzw. `project` + deutscher `COMMUNICATION_LANGUAGE`):

```
Projektkontext: lies zuerst `{context_file}` — sie ist die einzige Quelle für projektspezifische Fakten (hier nur eingebettet, wenn `project-context-injection.mode` diese Rolle einschließt).
```

- Genau **eine** physische Zeile; `{context_file}` = `pc["context_file"]` (`agent_sync.py:515`), kein verschachtelter Platzhalter (Substitution ist einpassig, `variables.py:698`).
- Auflösung: `pointer-text` (Override) > `pointer-language` (`en`/`de`/`project`) > `en` — Texte und Sprach-Abbildung liegen als Konstanten **in `config.py`** (D8), nicht in `agent_sync.py`.
- Mechanik (verbindlich, Spec §3.2): Block blankieren → leer gewordene `**Project context:**`-Zeile entfernen → Pointer als eine Zeile vor dem letzten `</context>` einfügen.
- Fallbacks für Rollen **ohne** Block-Vorkommen: letzte `</workflow>`-Zeile → davor (`intern-developer`); sonst Dateiende + `log.note` (13 `se-*` + `mammouth-expert`). Unter den 15 Rollen ohne Platzhalter hat heute **keine** ein `<context>`.

### 5.4 Render-Reihenfolge (Invariante, Spec §5.3)

`scope auflösen (einmal, inkl. pointer_text/pointer_language)` → `_build_provider_vars` (`_PROJECT_CONTEXT_POINTER` formatieren) → `apply_project_context_scope(merged_vars, role, scope)` → `substitute` (`:730`) → `strip_inactive_conditional_blocks` (`:737`) → `Label-Cleanup + Pointer` (auch für Rollen ohne Block) → `write` (`:1469`) → `Delta-Zähler`.

### 5.5 Golden-Test-Vertrag für `mode: all`

- `tests/fixtures/slimming-golden/*.md` bleibt **eingefroren**; `tests/test_template_slimming_equivalence.py` wird von #1187 **nicht editiert** und muss grün bleiben.
- Zusätzlich byte-identisch: `config ohne Sektion` == `config mit mode: all` für alle 8 Referenzrollen (T8).
- `chars saved` ist bei `all` exakt `0` (T7).

---

## 6. Teststrategie

**Bestehende Dateien (wiederverwendet, nicht verändert):**
- `tests/fixtures/slimming-golden/` — AC2-Golden (enthält `developer`, `orchestrator`, `ui-ux-designer`, `bug-feature-analyzer`, `knowledge-curator`, `knowledge-migrator`, `intern-developer`, `mammouth-expert`).
- `tests/test_template_slimming_equivalence.py:1191-1240` — Render-Helfer-Muster (ist der einzige bestehende Byte-Gate).
- `tests/_te_admin_helpers.py` — `_handler`/`_post` für Admin-API-Tests.
- `tests/test_context_profile_admin.py` — Quelltext-Assertion-Muster für UI-Wiring.
- `tests/test_release_checklist_consistency.py:53-56` — `check_builder_known_set`-Muster.
- `tests/test_context_compact_mode.py:24-26` — `subprocess`/Git-Assertion-Muster.

**Neue Dateien:** `tests/test_project_context_injection_config.py` (T1-T3, T14), `tests/test_project_context_injection_render.py` (T4-T10), `tests/test_project_context_injection_consistency.py` (T11), `tests/test_admin_ui_project_context_injection_section.py` (T12-T13).

**Matrix Modus × Provider × Rolle:**

| Modus | Claude (`CLAUDE.md`) | Gemini (`AGENTS.md`) | Opencode (`AGENTS.md`) | Continue (`.continue/rules/project-context.md`) |
|---|---|---|---|---|
| `all` | Golden byte-identisch (8 Rollen) | `test_provider_vars_carry_scope` + Golden-Diff | Golden-Diff | Pointer-Text-Unit-Test (T6) |
| `core` | 0 Block + 1 Pointer (8 Rollen) | Pointer nennt `AGENTS.md`, **nicht** `GEMINI.md` | Pointer nennt `AGENTS.md` | Pointer nennt den Rule-Pfad |
| `core+whitelist` | Whitelist-Rolle ja, `planner` nein, `orchestrator` nein (Default `inherit`) | dito (1 Provider genügt, Matrix-Rest ist Pointer-only) | — | — |
| `core+orchestrator` | `orchestrator` ja, `developer` nein | — | — | — |
| `core+orchestrator` + `orchestrator-roles: [senior-developer]` | `senior-developer` ja, `orchestrator` nein (D5) | — | — | — |
| `all` + `orchestrator: exclude` | `orchestrator` nein + WARN, `developer` ja (D6) | — | — | — |
| `core` + `pointer-language: de` | deutscher Pointer mit `CLAUDE.md` | deutscher Pointer mit `AGENTS.md` | deutscher Pointer mit `AGENTS.md` | deutscher Pointer mit `.continue/rules/project-context.md` |

Provider-Achse wird über `pc["context_file"]` parametrisiert, nicht über Provider-Namen im Code (Provider-Agnostik, Spec §4.5).

**Zwischentests:** siehe Meilenstein-Gates (§3). Nach jedem Meilenstein zusätzlich `python3 scripts/sync.py --validate` und `python3 scripts/sync.py --check` (DRY-RUN, keine neuen Warnungen gegenüber `.tmp/issue-dump/baseline-check.txt:1-7`).

**Ein voller Szenarientest am Ende:** T15, `.tmp/scenario-context-1187/`, alle vier Modi + zwei Fehlerfälle, Ergebnis dokumentiert.

**Konventions-Abweichung (bewusst):** Es wird **kein** Eintrag in `tests/scenarios/registry.md` angelegt (Konvention `rules/2-platform/agent-meta-conventions.md:123`). Grund: Der Wave-Scope legt den End-to-End-Beweis als Scratch-Konsumenten in `.tmp/` fest. Falls der Wave-Orchestrator die Szenarien doch registriert: **`94` ist für #1181 reserviert, `95`–`98` für #1187, `99` für #1186** (kein zusätzlicher Implementierungsaufwand außer den Config-Dateien). Dieser Plan verbraucht keine ID vorab.

---

## 7. Migration & Rollback

- **Default bleibt `all`:** Fehlt die Sektion (oder ist sie `null`/kein Mapping), liefert der Resolver `mode=all`, `present=False`; es wird nichts blankiert und kein Pointer eingefügt. Nachweis: `test_scope_absent_config_defaults_to_all` + `test_all_matches_default_absent_key`.
- **Neue Keys sind rückwärtskompatibel:** `orchestrator-roles` fehlt → Default-Ableitung (heute faktisch `("orchestrator",)`, weil nur Opencode `primary-role` trägt); `pointer-language` fehlt → `en` (heutiger Wortlaut); `pointer-text` fehlt → Sprach-Default. Ein Bestandsprojekt ohne diese Keys rendert bei `mode: all` byte-identisch. Nachweis: `test_schema_orchestrator_roles_and_pointer_text_have_no_default` + AC2-Golden.
- **Keine Config-Migration:** Die Sektion hat keinen Top-Level-Default, und der Nested-Fill behandelt nur `dod.*`; ein normaler Sync materialisiert sie daher nicht. Der `_SYNC_SKIPPED_DEFAULT_KEYS`-Eintrag ist reiner Regressionsschutz (Spec §4.1). Damit ändert sich in Consumer-Projekten nur `project.yaml`, wenn der Nutzer die Sektion selbst anlegt. Nachweis: T15 Schritt 2 (Lauf A) — `grep -c '^project-context-injection:' .meta-config/project.yaml` == `0` (**nicht** Byte-Identität der ganzen Datei, weil strukturelle Auto-Fills sie ändern; nach Lauf B wäre die Assertion falsch, weil die Test-Config die Sektion selbst setzt).
- **Rollback (ein Schritt):** `project-context-injection`-Block aus `.meta-config/project.yaml` löschen → nächster Sync rendert wieder `all`. Kein Code-Rollback nötig; die Schema-Sektion bleibt rückwärtskompatibel (Default `all`).
- **Sync-Backups:** Der nächste Sync nach dem Rollback überschreibt die Agenten; vorhandene `.sync-backup-*`-Dateien (vgl. `.tmp/issue-dump/baseline-check.txt:5`) werden nicht angefasst. Kein Backup wird durch diesen Plan gelöscht.
- **Consumer-Re-Sync:** Nicht Teil dieses Issues (Spec §6). Kein Projekt wird rückwirkend bereinigt.

---

## 8. Risiko-Tabelle

| Risiko | Eintritt | Auswirkung | Gegenmaßnahme |
|---|---|---|---|
| `PROJECT_CONTEXT_INJECTED` fehlt in der Conditional-Whitelist → `{{#if}}`-Marker bleiben stehen und die Orphan-Cleanup klebt beide Zweige zusammen | mittel (leicht zu vergessen, `variables.py:570-598` ist eine lange Sammelzeile) | doppelter Text in 4 Templates, Golden rot | T3-Test `test_conditional_strip_removes_inactive_project_context_branch`; Golden-Gate T10 |
| Golden wird „rebaselined", um AC2 zu retten | niedrig, aber schwerwiegend | AC2 wertlos, heutige Doppel-Renderung wird eingefroren | T10 verbietet Fixture-Änderung explizit; Gate ist der unveränderte grüne Lauf |
| Pointer-Heuristik trifft die falsche Sektion (mehrere `</context>`/`</workflow>`-Vorkommen) | mittel | Pointer landet im Workflow statt im Kontext | T6 nutzt `rfind` (letzte Sektion) + Test über alle Fallback-Gruppen: `developer` (`</context>`), `intern-developer` (`</workflow>`), `se-architect` + `mammouth-expert` (Dateiende) |
| `**Project context:**`-Label bleibt in `core` leer stehen | hoch ohne Cleanup | leere Überschrift, AC7-Risiko | T6-Cleanup + `test_dangling_project_context_label_is_removed`; Mechanik jetzt in Spec §3.2/§3.6 D-2 dokumentiert |
| Resolver wirft bei `build_variables({}, …)` (`derive_builder_vars`, `placeholders.py:299-306`) | mittel | `--validate` bricht für alle Projekte | T2: `{}`/`None` ⇒ `all`, kein Raise; Test explizit |
| Whitelist-Name existiert in `role-defaults.yaml`, aber ohne generisches Template | niedrig | Rolle wird „erlaubt", aber nie gerendert | Meldung nutzt `build_role_map` (nur Rollen mit Template); Konfliktfälle zeigt die bestehende `roles_without_template`-Warnung (`sync_pipeline.py:1840-1849`) |
| Vier parallele Wellen ändern dieselben Dateien | hoch (Spec §10) | Rebase-Konflikte in Schema/`config.py`/`admin-server.py`/UI | Kanonische Reihenfolge: **#1187 → #1186 → #1188 → #1181 → #1141** → Whitelist-Ableitung (eigenes Follow-up); #1187 ist Schritt 1, weil es die Rollen-Schleife aufsetzt, die #1186/#1181 mitnutzen |
| `docs.ui_help_mappings` schlägt fehl, weil die Help-ID fehlt | mittel | `--validate` rot, AC7 verletzt | T13-Test `test_help_id_mapping_present`; Doku-Änderung ist Teil des Tasks, nicht „später" |
| Admin-UI-Pane gebaut, Sektion aber nicht in der Whitelist | mittel | HTTP 400 beim Speichern (AC1 halb erfüllt) | T12 vor T13; Round-Trip-Test über `PUT /api/config/project/section` |
| Delta-Zählung zählt Rollen ohne Blockvorkommen als „gespart" | mittel | falsche AC6-Zahl | T7: `chars_removed` nur für Rollen mit Blockvorkommen; `test_log_line_counts_pointer_and_savings` |
| `orchestrator-roles: []` schaltet die Injektion still ab | mittel (ein Tippfehler im Key, ein bewusst leeres Set) | `core+orchestrator` injiziert nichts mehr | Semantik ist Spec-Vertrag (§3.1.1) und wird bei `core+orchestrator` mit WARN `empty-orchestrator-set` benannt; T2/T8-Tests |
| `--fill-defaults`/`--init` materialisiert `orchestrator-roles: []` oder einen eingefrorenen `pointer-text` | niedrig | Semantikänderung im nächsten Sync | Schema **ohne** Default für beide Keys (T1-Test), `_SYNC_SKIPPED_DEFAULT_KEYS`-Eintrag |
| `pointer-text` mit Fremd-Token, mehreren `{context_file}` oder Zeilenumbruch | mittel | Pointer kaputt, AC3 („genau eine Zeile") verletzt | vier harte Resolver-Regeln (T2) **und** Admin-UI-Eingabeprüfung (T13); Server bleibt maßgeblich |
| `pointer-language: project` + nicht abbildbare `COMMUNICATION_LANGUAGE` | niedrig | falscher Pointer-Text | Fallback `en` + WARN `pointer-language-fallback`, einmal pro Lauf (T2) |
| `exclude`-WARN wird pro Provider statt pro Lauf ausgegeben | mittel | doppelte WARN-Zeilen, flaky Szenario-Assertion | WARN entsteht in `build_variables`-Pre-Warnings (`cli_commands.py:691-692`); T2/T15 zählen genau **eine** Zeile |
| `pointer-missing` prüft gegen den hartkodierten englischen Pointer | mittel | False-Positives bei `pointer-language: de`/Override | T11 nutzt `format_project_context_pointer(scope["pointer_text"], pc["context_file"])`; Test `test_pointer_missing_accepts_german_and_overridden_pointer` |

---

## 9. AC→Task-Traceability

| AC (Spec §7) | Task(s) | Absicherung |
|---|---|---|
| **AC1** Schema + Admin-UI-Schreibbarkeit | T1, T12, T13 | Schema-Tests (valid/invalid, sechs Keys, keine Defaults für `orchestrator-roles`/`pointer-text`), `PROJECT_WRITABLE_SECTIONS`-Assertion, `PUT /api/config/project/section`-Round-Trip, Route/Help-ID |
| **AC2** `all` byte-identisch | T4, T8, T9, T10 | `test_all_matches_default_absent_key`, unverändertes Golden-Gate, `test_all_prose_matches_golden`; Sektion wird nicht materialisiert (`grep -c '^project-context-injection:' == 0`, T15 Schritt 2 / Lauf A) |
| **AC3** `core`: 0 Blöcke, 1 Pointer, reale Datei | T5, T6, T8 | `test_core_renders_zero_blocks`, `test_pointer_uses_resolved_context_file_per_provider`, `test_exactly_one_pointer_per_excluded_role` (inkl. `intern-developer` → `</workflow>`, 13 `se-*` + `mammouth-expert` → Dateiende), `test_pointer_german_default_used`/`test_pointer_text_override_used_verbatim` (D8) |
| **AC4** `core+whitelist`, unbekannter Name = Fehler | T2, T8 | `test_scope_whitelist_unknown_role_lists_all_names`, `test_core_whitelist_only_whitelisted_roles`, `test_core_whitelist_unknown_name_fails_render` |
| **AC5** `core+orchestrator` | T2, T5, T8 | `test_scope_orchestrator_roles_default_per_provider_set`, `test_scope_orchestrator_roles_override_replaces_default`, `test_core_orchestrator_only_orchestrator_roles`, `test_core_orchestrator_with_overridden_roles` (D5) |
| **AC6** Delta im Sync-Log | T7 | 4 Log-Tests inkl. `chars saved == 0` bei `all`; `len(pointer)` = aufgelöster Pointer (D8) |
| **AC7** Prompt-Qualität bei `core` | T8, T11, T15 | `test_core_keeps_required_sections_non_empty`, `pointer-missing = 0`, `sync.py --validate` grün im Szenario — D7: alle **drei** Bedingungen, kein neuer Check |
| Issue-Requirement „Default bleibt `all`" | T2, T8 | `test_scope_absent_config_defaults_to_all`, AC2-Tests |
| Issue-Requirement „Delegation-Contract unverändert" | T15 (Diff-Check) | `schemas/a2a-handoff.schema.json` nicht in `git diff --name-only aaed14c2..HEAD -- schemas/a2a-handoff.schema.json` (eingefrorener Basis-Hash, nicht `HEAD`) |
| Issue-Requirement „Provider-aware Pointer" | T6 | Test über alle Provider aus `config/ai-providers.yaml`, Gemini-Fall (`AGENTS.md`) explizit |
| **D5** `orchestrator-roles` | T1, T2, T5, T8, T13, T15 | Default-Menge, Override, leere Liste, unbekannte Rolle, Pane-Feld, Szenario-Lauf G |
| **D6** `exclude` gewinnt mit WARN | T2, T5, T8, T15 | Kein `SyncError`, exakter WARN-Text, genau eine WARN pro Lauf, Szenario-Lauf F |
| **D7** AC7-Auslegung | T8, T11, T15 | Drei-Bedingungen-Definition, `pointer-missing` in `--validate`, kein neuer Check |
| **D8** Pointer-Text/-Sprache | T1, T2, T6, T8, T11, T13, T15 | Default `en`, `de`, `project` (+ Fallback-WARN), Override, vier harte Validierungsregeln, Pane-Felder, Szenario-Lauf H |

**Keine AC ohne Task.** Umgekehrt gilt: T3, T14 sind Voraussetzungen (Registrierung/Doku), keine eigenen ACs.

---

## 10. Backlog-Bugs

Entschieden gegen die echten Issue-Texte (`.tmp/issue-dump/issue-*.json`).

| Issue | Titel | Einordnung | Betroffene Tasks | Begründung |
|---|---|---|---|---|
| [#1183](https://github.com/Popoboxxo/agent-meta/issues/1183) | `compact`-Profil ersetzt den eingebetteten Regelblock durch die Gate-Karte | **nur abhängig** | T15 (nur Regression) | Anderer Kanal (Einstiegsdatei `AGENTS.md`/`CLAUDE.md`, `context.py`/`context-anchors.yaml`) und andere Dateien (`rules/`). Gemeinsam ist nur die Metrik „weniger Tokens pro Kontext". #1187 darf den `compact`-Pfad nicht anfassen: die Kontextdatei bleibt unverändert (Spec §2.3, §6). |
| [#1182](https://github.com/Popoboxxo/agent-meta/issues/1182) | `compact` + `orchestrator.mode: advisory/main-chat` bricht mit `SyncError` ab | **nur abhängig** | T2 (Nicht-Verschärfung), T15 | Abbruch sitzt im Gate-Card-Builder (`context.py:2209`, `:2822`), nicht im Rollen-Rendering. Relevanz für #1187: der neue Resolver darf **keinen** zusätzlichen Abbruchpfad für gültige Kombinationen einführen — T2 wirft nur für die vier in §5.1 genannten Fälle, und `orchestrator.mode` (Gate-Strenge) bleibt unberührt von `project-context-injection.orchestrator` (eine andere Achse). |
| [#1161](https://github.com/Popoboxxo/agent-meta/issues/1161) | Token-Reduktion (`route_intent`, Agent-Directory, branch-guard, Hook-Kosten) | **teilweise** | T7, T15 | Gleiches Ziel („weniger pro-Spawn-Kontext"), aber #1161 misst Tokens (cl100k-Proxy) und ändert andere Artefakte (`agents.py`-Routing-JSON, `AGENT_TABLE`, `.claude/rules/branch-guard.md`). #1187 liefert **Zeichen**-Delta (Spec §3.5); die Zahl ist damit nicht direkt mit #1161 vergleichbar — T7 dokumentiert das in der Logzeile `chars saved`, nicht als Token-Schätzung (keine erfundene Konversion). |
| [#1180](https://github.com/Popoboxxo/agent-meta/issues/1180) | Regeln verweisen auf `docs/concepts/*.md`, die sync nie ausliefert | **teilweise** | T6, T11 | #1187 erzeugt eine Pointer-Klasse auf eine Datei, die sync **tatsächlich** schreibt (`context_file`) — kein Dead-Link. #1180 liefert die `docs/`-Auslieferung und eine generische Datei-Pointer-Prüfung; #1187 prüft nur seinen eigenen Pointer (`pointer-missing`) und dupliziert #1180 nicht. Wenn #1180 zuerst landet, soll `pointer-missing` dessen Resolver wiederverwenden; solange nicht, bleibt es lokal (kein Blocker). |

---

## 11. Neu gemeldete Findings

| # | Finding | Status | Warum nicht in #1187 |
|---|---|---|---|
| **F1** | `{{PROJECT_CONTEXT}}` wird in 4 Rollen mehrfach gerendert: `ui-ux-designer.md:72,77,105` (3×), `bug-feature-analyzer.md:40,76` (2×), `knowledge-curator.md:22,55` (2×), `knowledge-migrator.md:26,38` (2×) — 89 Vorkommen in 84 Dateien | **[#1197](https://github.com/Popoboxxo/agent-meta/issues/1197)** | AC2 (Byte-Identität `all`) verbietet die Bereinigung in diesem Issue (Spec D-4). |
| **F2** | 15 Rollen ohne Platzhalter haben teils **keine** `<context>`- *und* keine `</workflow>`-Sektion (13 `se-*`, `intern-developer`, `mammouth-expert`) — Spec §3.2 nannte ursprünglich nur den `</workflow>`-Fall | **in Spec §3.2 aufgelöst, kein Issue** | Dreistufiger Fallback (Dateiende + `log.note`) ist jetzt Spec-Vertrag; ohne ihn wäre AC3 für diese Rollen nicht mechanisch erfüllbar. `intern-developer` nutzt den `</workflow>`-Fall, die übrigen 14 das Dateiende. |
| **F3** | 60 Templates rendern `**Project context:** {{PROJECT_CONTEXT}}` in **einer** Zeile; Blankieren des Werts hinterlässt ein leeres Label | **in Spec §3.2/§3.6 D-2 aufgelöst, kein Issue** | Label-Cleanup ist jetzt **Spec-Mechanik** (nicht mehr reine Plan-Erfindung), nur im Nicht-Injiziert-Zweig; AC2 bleibt unberührt. |

**Keine erfundenen Issue-Nummern.** F1 ist #1197; F2/F3 sind Spec-Detailentscheidungen, keine Backlog-Issues.

---

## 12. Offene Entscheidungen

| # | Frage | Empfehlung | Blockadewirkung |
|---|---|---|---|
| **OQ-1** | AC3 „exactly one pointer line per role" auch für die 15 Rollen **ohne** Platzhalter? | **Aufgelöst (Review 2026-11-09):** Ja — Spec §3.2 benennt die 15 Rollen exakt und definiert den dreistufigen Fallback; AC3 gilt für alle 98 Rollen. | **nicht mehr blockierend** (Spec-Revision 2). Bei späterer AC-Umdeutung wäre nur der Fallback-Abschnitt zu ändern, nicht T5. |
| **OQ-2** | Gehören `primary-role`-Rollen zur Orchestrator-Achse? | **Entschieden 2026-11-09 — D5 (Spec §13):** konfigurierbar über `orchestrator-roles`; Default = `{orchestrator} ∪ primary-role` aktiver Provider, explizite Liste ersetzt vollständig, `[]` zulässig, unbekannte Rolle = harter Fehler. Plan-T2/T5/T8/T15 tragen die Fälle. | **nicht mehr blockierend** |
| **OQ-3** | `all` + `orchestrator: exclude` = Fehler oder stille Verengung? | **Entschieden 2026-11-09 — D6 (Spec §13):** kein Fehler. `exclude` gewinnt, Orchestrator-Rollen ausgenommen, WARN `exclude-overrides-mode` (§3.1.2 der Spec). Der `SyncError`-Pfad ist aus T2/T5/T15 entfernt; Lauf F prüft WARN statt Exit ≠ 0. | **nicht mehr blockierend** |
| **OQ-4** | AC7 nennt „existing prompt-quality checks", die es unter diesem Namen nicht gibt (vorhanden: Frontmatter `frontmatter.py`, Platzhalter `placeholders.py:12`, `context.*` `context_budget.py:293/540`) | **Entschieden 2026-11-09 — D7 (Spec §13):** AC7 = `sync.py --validate` grün **und** `pointer-missing == 0` **und** keine leeren Pflichtsektionen (bestehende Checks). Kein neuer Check; Issue-Text wird redaktionell nachgezogen. T8/T11/T15 prüfen genau diese drei Bedingungen. | **nicht mehr blockierend** |
| **OQ-5** | Pointer-Sprache Englisch oder Projektsprache? | **Entschieden 2026-11-09 — D8 (Spec §13):** konfigurierbar mit Default Englisch (`pointer-language` `en`/`de`/`project`, `pointer-text`-Override). `project` leitet aus `COMMUNICATION_LANGUAGE` ab, unbekannt → `en` + WARN; Fremd-Token/mehrzeilig = harter Fehler. T1/T2/T6/T8/T11/T13/T15 tragen die Fälle. | **nicht mehr blockierend** |
| **OQ-6** (neu, aus dem Plan) | Was passiert mit dem leer werdenden `**Project context:**`-Label in 60 Templates (`developer.md:66`, `orchestrator.md:316`)? | **Aufgelöst (Review 2026-11-09):** Label-Zeile entfernen, nur im Nicht-Injiziert-Zweig — jetzt verbindlich in Spec §3.2/§3.6 D-2. AC2 bleibt unberührt, AC7 („keine leeren Pflichtsektionen") wird erfüllt. | **nicht mehr blockierend** (Spec-Revision 2). |
| **OQ-7** (neu, aus dem Plan) | Fallback für Rollen ohne `<context>` **und** ohne `</workflow>`? | **Aufgelöst (Review 2026-11-09):** Pointer ans Dateiende + `log.note`, jetzt Spec-Vertrag (§3.2 Fallback-Tabelle). Betroffen: 13 `se-*` + `mammouth-expert`; `intern-developer` hat `</workflow>` und nutzt den zweiten Fall. | **nicht mehr blockierend** (Spec-Revision 2). Ohne den Fallback fehlte 14 Rollen der Pointer → AC3 verletzt. |

---

## 13. Review-Auflösung (2026-11-09)

Alle Befunde aus dem Review vom 2026-11-09 sind eingearbeitet. Status bleibt `DRAFT`; Plan-Revision 2
(Review) und Revision 3 (Entscheidungen D5–D8, §14) bei Spec-Revision 4.

| Befund-ID | Änderung | Betroffene Stelle |
|---|---|---|
| **BLOCKER** (Validator, `plan:195`) | `core+whitelist` + `inherit` inkludiert **keine** Orchestrator-Rolle; nur `include` fügt die Orchestrator-Menge hinzu. T5-Matrixbullet korrigiert, T8 um `test_core_whitelist_include_adds_orchestrator` und explizite `orchestrator`-Negativ-Assertion ergänzt. | T5, T8, §6-Matrix |
| **RVW-1187-01** (MAJOR) | Logzeilen-Assertion aus M1-Gate entfernt (dort erst nach T7/M2 möglich) und in M2-Gate verschoben. | §3 M1/M2-Gates |
| **RVW-1187-02** (MAJOR) | Eine Pointer-Mechanik: Block blankieren → leere `**Project context:**`-Zeile entfernen → Pointer vor letztem `</context>`; Fallbacks `</workflow>` und Dateiende. Spec §3.2/§3.6 D-2/§5.3 nachgezogen, T6-Tests entsprechend. | T6, §5.3, §5.4 |
| **RVW-1187-03** (MAJOR) | AC3-Rollenmenge exakt: 15 Rollen ohne Platzhalter = 13 `se-*` + `intern-developer` + `mammouth-expert`; dreistufiger Fallback in Spec §3.2. T6-Test deckt alle Fallback-Gruppen ab; T15-Schritt 4 prüft `mammouth-expert`/`se-architect`/`intern-developer`. | T6, T15, §11 F2 |
| **RVW-1187-04** (MAJOR) | Negativ-Assertions über `git diff --name-only HEAD` durch `git diff --name-only aaed14c2..HEAD -- <pfad>` ersetzt (T10, T15 Schritt 9, §9 Delegation-Contract). | T10, T15, §9 |
| **RVW-1187-05** (MINOR) | „`project.yaml` byte-identisch" ersetzt durch `grep -c '^project-context-injection:' == 0` (ursprünglich T15 Schritt 8, §7; mit RVW2-1187-02 nach Schritt 2 verschoben). | T15, §7 |
| **RVW-1187-06** (MINOR) | `_SYNC_SKIPPED_DEFAULT_KEYS`-Begründung entschärft: Sektion hat keinen Top-Level-Default, Eintrag ist reiner Regressionsschutz. | T2 |
| **Validator-WARN** (`spec:433`) | #1181-Key ist `auto_commit.authority_overrides` (nested), in der Konfliktmatrix korrigiert. | §2 (agent_sync-Zeile), §8; Spec §10 |
| **NIT** | T9: „5 Block-Vorkommen" → „4 Block-Vorkommen" (die 5 zählen die Prosa-Stellen). | T9 |
| Querschnitt: Reihenfolge | Kanonisch `#1187 → #1186 → #1188 → #1181 → #1141` → Whitelist-Ableitung; im Header, §8 und Spec §10 verankert. | Header, §8 |
| Querschnitt: Konfliktmatrix | `agent_sync.py`-Zeile korrigiert (drei Autoren: #1187, #1188 `_apply_role_issue_convention_overrides`, #1181 T8 `:1457-1468`/`_finalize_agent_content`); `sync_pipeline.py` (#1186/#1181, #1187 ohne Task), `variables.py`/`standalone.py` (nur #1187, #1186 nur Hotspot), `tests/scenarios/registry.md`, beide `project.yaml.example` und die #1188-Dateien ergänzt. | §2, §8; Spec §10 |
| Querschnitt: Szenario-IDs | `94` = #1181, `95`–`98` = #1187, `99` = #1186; T15/Fallback angepasst. | T15, §6 |
| Querschnitt: `docs/issue-labels.md` / `.meta-config/issue-labels-state.json` | Beide von #1188 erzeugt (`project-docs.files.issue-labels` bzw. **`unmanaged`** — K1, `project-state` gestrichen), in #1186 zu klassifizieren — Querschnittsnotiz, keine Task hier. | Spec §10 (Notiz) |
| Finding #1197 | F1 verweist jetzt auf #1197. | §11 F1 |
| **RVW2-1187-01** (MAJOR) | Lauf F erwartete bei `mode: core` + `orchestrator: exclude` einen Fehler, obwohl Spec §3.1 (`:151`) das erlaubt (exkludiert). Lauf F wurde damals auf `mode: core+orchestrator` (+ Zusatzlauf `all`) + `exclude` umgestellt; `core` + `exclude` war ausdrücklich **kein** Fehler. **Überholt durch D6 (§14):** seit 2026-11-09 ist `exclude` in **keinem** Modus ein Fehler; Lauf F prüft jetzt WARN + Exit 0 (T15). | T15 Schritt 7 |
| **RVW2-1187-02** (MINOR) | Materialisierungs-Assertion (`grep -c '^project-context-injection:' == 0`) von Lauf B nach Lauf A verschoben — Lauf B setzt die Sektion selbst (Zähler 1). | T15 Schritte 2/8; §7; §9 |
| **RVW2-X-01** (MAJOR) | Konfliktmatrix auf die verbindliche Zielmatrix gezogen: `agent_sync.py` → #1187/#1188/#1181; `sync_pipeline.py` → #1186/#1181 (#1187 ohne Task); `variables.py`/`standalone.py` → nur #1187 (#1186 nur Hotspot, kein Edit); `tests/scenarios/registry.md` → #1181/#1187/#1186; beide `project.yaml.example` → alle vier; `docs/issue-labels.md` und `.meta-config/issue-labels-state.json` → von #1188 erzeugt, von #1186 klassifiziert. | §2; Spec §10 |

### 13.1 Szenario-Konflikte K1–K8 (2026-11-09)

| Befund | Änderung | Stelle |
|---|---|---|
| **K1** (BLOCKER) | `.meta-config/issue-labels-state.json` ist `unmanaged`, nicht `project-state` | §2 (Querschnittstabelle), Review-Zeile „Querschnitt: docs/issue-labels.md …" |
| **K2** | **Nicht betroffen**: kein Label-Separator | geprüft: §2 |
| **K3** | **Nicht betroffen**: §3.4 der Spec schließt eine Preset-Ebene aus | geprüft: §2 |
| **K4** | **Nicht betroffen**: keine `taxonomyAxis` | geprüft: T1 |
| **K5** | **Nicht betroffen**: keine Grant-Präzedenztabelle | geprüft: T2 |
| **K6** | **Nicht betroffen**: keine `$defs`-Skizze | geprüft: T1 |
| **K7** | **Nicht betroffen**: `project-context-injection` ist kebab-case | geprüft: T1 |
| **K8** | **Nicht betroffen**: kein `_KEYS`-Block | geprüft: T2 |

---

## 14. Entscheidungsprotokoll (2026-11-09)

Vom User entschiedene offene Fragen (Spec §13). Status bleibt `DRAFT`; die Entscheidungen sind
verbindlich und ersetzen die früheren Empfehlungen in §12. Marker `DECIDED 2026-11-09` steht auch am
jeweiligen Änderungsort.

| D-Nr | Frage | Entscheidung (`DECIDED 2026-11-09`) | Stelle |
|---|---|---|---|
| **D5** | OQ-2: Gehören `primary-role`-Rollen zur Orchestrator-Achse, oder nur die Rolle `orchestrator`? | Neuer Key `project-context-injection.orchestrator-roles: []`. Fehlt der Key → Default `{orchestrator} ∪ {providers.<P>.primary-role aktiver Provider}` (deterministisch, dedupliziert); ein Eintrag **ersetzt** den Default vollständig; unbekannte Rolle = harter Sync-Fehler; leere Liste zulässig (keine Orchestrator-Rolle). Umgesetzt in Schema (T1), Resolver (T2), Matrix/Render (T5/T8), Admin-UI (T13), Szenario-Lauf G (T15). Tests: Default-Menge pro Provider-Set, expliziter Override, unbekannte Rolle, leere Liste. | T1, T2 (Signaturen + WARN/Validierung), T5, T8, T13, T15; §5.1, §5.2, §9 |
| **D6** | OQ-3: Ist `mode: all` + `orchestrator: exclude` ein Fehler oder eine stille Verengung? | **Kein** harter Fehler. Die Orchestrator-Rollen werden ausgenommen („alle außer Orchestrator"), der Sync läuft weiter und gibt eine **WARN** `project-context-injection.exclude-overrides-mode` aus, die Widerspruch und Ergebnis benennt (Text: Spec §3.1.2). Der `SyncError`-Pfad ist aus T2/T5/T15 entfernt; `core` + `exclude` bleibt gültig (ohne WARN). Gleiche Behandlung für `core+orchestrator` + `exclude` (Modus degeneriert zu `core`). Lauf F prüft Exit 0 + genau eine WARN. | T2, T5, T8, T15 Schritt 7; §5.1, §5.2, §8, §9, §13 (RVW2-1187-01 überholt) |
| **D7** | OQ-4: Was bedeutet AC7? | AC7 = `sync.py --validate` grün **und** `pointer-missing == 0` **und** keine leeren Pflichtsektionen (bestehende Frontmatter-/Platzhalter-Checks). Kein neuer Check; der Issue-Text wird redaktionell nachgezogen. T8 prüft nicht-leere Pflichtsektionen, T11 `pointer-missing`, T15 `--validate` im Szenario. | T8, T11, T15 Schritt 8; §9 AC7 |
| **D8** | OQ-5: Pointer-Text Englisch oder Projektsprache? | Pointer-Text ist konfigurierbar, Default **Englisch**: `pointer-language` (`en`\|`de`\|`project`, Default `en`) und `pointer-text` (Override, erlaubtes Token `{context_file}`, genau einmal, einzeilig). `project` leitet aus `COMMUNICATION_LANGUAGE` ab; unbekannte Sprache → `en` + WARN `pointer-language-fallback`; Fremd-Token/≠ 1 × `{context_file}`/Zeilenumbruch = harter Sync-Fehler. Texte/Konstanten liegen in `config.py`, der Renderer konsumiert nur `_PROJECT_CONTEXT_POINTER`; `pointer-missing` vergleicht gegen den aufgelösten Text. | T1, T2, T4, T6, T8, T11, T13, T15 Schritt 7 (Lauf H); §5.1, §5.2, §5.3, §5.4, §9 |

**Konsequenz für §12:** OQ-2…OQ-5 sind geschlossen; OQ-1/OQ-6/OQ-7 waren bereits in Revision 2
geschlossen. Es bleiben **keine** offenen Entscheidungen — die Spec-Freigabe ist der einzige
verbleibende Schritt.

**Rest-Auslegung (bewusst nicht entschieden, kein Blocker):** Ob `orchestrator-roles`-Einträge, die
zwar in `role-defaults.yaml`, aber **ohne** generisches Template existieren, als Fehler statt WARN
behandelt werden sollen. Aktuell WARN `orchestrator-role-no-template` (§8), konsistent zur
bestehenden `roles_without_template`-Meldung.

---

## 15. Ausführungsnachweis

> Wird bei der Ausführung befüllt (Datum, HEAD, Szenario-Logzeilen, Testläufe). Bis dahin leer — **kein** Platzhalter für Implementierungsdetails, nur das Ergebnisprotokoll.
