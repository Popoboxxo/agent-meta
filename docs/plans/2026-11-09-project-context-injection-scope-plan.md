# Project-Context-Injection Scope — Implementation Plan

> **Status:** DRAFT
> **Issue:** [#1187](https://github.com/Popoboxxo/agent-meta/issues/1187) — feat(config): project-context-injection scope (core | +orchestrator | +whitelist | all)
> **Revision:** 2 (Review-Auflösung 2026-11-09)
> **Spec:** `docs/specs/2026-11-09-project-context-injection-scope-spec.md` (spec-id `SPEC-project-context-injection-scope-2026-11-09`, Revision 2, **Status: DRAFT** — Freigabe vor Task-Beginn einholen)
> **Klasse:** **L** (cross-cutting in `sync`-Rendering; ~14 produktive Dateien + 4 neue Testdateien; kein neues Subsystem)
> **Datum:** 2026-11-09 · **Basis:** Branch `docs/config-wave-plans-1181-1188`, HEAD `aaed14c2`, agent-meta `v2.0.0-beta.8`
> **Kanonische Welle:** `#1187 → #1186 → #1188 → #1181 → #1141` → Whitelist-Ableitung (eigenes Follow-up). Dieser Plan ist **Schritt 1** der Welle und setzt die Rollen-Schleife neu auf, auf der #1186/#1188/#1181 aufsetzen.
> **Voraussetzungen:**
> 1. Spec von `main_chat`/Daniel auf `Status: APPROVED` gesetzt (OQ-1…OQ-5 aus §8.2 beantwortet oder die Empfehlungen übernommen).
> 2. Baseline bestätigt: `.tmp/issue-dump/baseline-validate.txt` (PASS, 1 Warnung), `.tmp/issue-dump/baseline-check.txt` (DRY-RUN, 3 bestehende Warnungen).
> 3. Kein paralleler Branch auf `scripts/lib/agent_sync.py` (#1188/#1181), `scripts/lib/sync_pipeline.py` (#1186/#1181), `config/project-config.schema.json`, `docs/ui/admin-ui.html` (Konfliktflächen §10 der Spec).
> 4. Python ≥ 3.9, stdlib-only; `pytest` vorhanden; `PYTEST_BASETEMP` in der Shell gesetzt (Konvention aus `docs/plans/2026-10-31-release-checklist-plan.md:23`).
>
> **Branch-Guard:** Die Implementierung läuft auf `feat/1187-project-context-injection` (abgeleitet von `main` nach dem Docs-Branch-Merge). **Keine** Änderung auf `main`/`master`. Push/Tag/Branch-Merge ausschließlich durch den `git`-Agenten.
> **Aufwand:** Gesamt **L**. Referenz für die Summenbildung: `effort-estimator` (Text-Referenz, kein Tool-Aufruf) — 15 Tasks, 4 Meilensteine, 2 neue produktive Codeblöcke (`config.py`-Resolver, `agent_sync.py`-Renderpfad).

---

## 1. Zielbild in 5 Sätzen

1. `project-context-injection.mode` steuert **pro Rolle**, ob der Projektabsatz (`{{PROJECT_CONTEXT}}`) in den generierten Rollen-Prompt eingebettet wird — `all` (Default) reproduziert das heutige Byte-Ergebnis, `core` bettet gar nichts ein.
2. Jede Rolle **ohne** eingebetteten Block erhält **genau eine** physische Pointer-Zeile, die die **real aufgelöste** Kontextdatei des Providers nennt (`pc["context_file"]`, z. B. `AGENTS.md` für Gemini — nicht `GEMINI.md`). Mechanik: Block blankieren → leer gewordene `**Project context:**`-Zeile entfernen → Pointer als eine Zeile vor dem letzten `</context>` einfügen; Fallbacks vor `</workflow>` (`intern-developer`) bzw. Dateiende + `log.note` (13 `se-*` + `mammouth-expert`).
3. Die Entscheidung fällt im Renderer pro Rolle (`agent_sync.sync_agents_for_provider` → Rollen-Schleife), nicht in 83 Templates; der Template-Text bleibt unverändert.
4. Fünf Prosa-Vorkommen in vier Templates werden auf `{{#if PROJECT_CONTEXT_INJECTED}}…{{else}}{{CONTEXT_FILE}}{{/if}}` umgestellt, damit `core` keine grammatisch zerlegten Sätze erzeugt und `all` byte-identisch bleibt.
5. Der Sync-Log meldet pro Provider `injected=n/total`, die Zahl der Pointer-Zeilen und die gesparten Zeichen; die Sektion ist im Admin-UI schreibbar, und `sync.py --validate` bleibt ohne neue Findings grün.

---

## 2. File-Structure-Map

Alle Pfade sind gegen HEAD `aaed14c2` geprüft. „Zeile" = heutige Ankerzeile (verschiebt sich durch die Änderung).

| Datei | neu/ändern | Zweck | Task |
|---|---|---|---|
| `config/project-config.schema.json` | ändern | neue Top-Level-Property `project-context-injection` (`mode`/`whitelist`/`orchestrator`, `additionalProperties: false`), Einfügung nach dem `context-profile`-Block (`:2842-2849`, vor `required` `:2851`) | T1 |
| `scripts/lib/config.py` | ändern | `PROJECT_CONTEXT_MODES`-Konstanten; `resolve_project_context_scope()` (Validierung) + `project_context_injected_for_role()` (pure Modus-Matrix); Aufruf am Ende von `build_variables` bei den Provider-Variablen (`:2810-2827`); `_SYNC_SKIPPED_DEFAULT_KEYS` (`:183-191`) | T2, T5 |
| `scripts/lib/consistency/placeholders.py` | ändern | `PROJECT_CONTEXT_MODE`, `PROJECT_CONTEXT_INJECTED` in `_BUILTIN_VARS` (`:12-45`, neben `PROJECT_CONTEXT` `:15` und `CONTEXT_FILE` `:38`) | T3 |
| `scripts/lib/variables.py` | ändern | `PROJECT_CONTEXT_INJECTED` in die Conditional-Whitelist von `strip_inactive_conditional_blocks` (`:556`, Sammelzeile `:570-572`) — **ohne das bleiben `{{#if}}`-Zweige stehen und werden durch die Orphan-Cleanup (`:690-693`) zusammengeklebt** | T3 |
| `scripts/lib/standalone.py` | ändern | `PROJECT_CONTEXT_INJECTED: "true"`, `PROJECT_CONTEXT_MODE: "all"` in den Conditional-Fallbacks (`:160-194`), damit exportierte Personas den `all`-Zweig rendern | T3 |
| `scripts/lib/agent_sync.py` | ändern | Pointer-Konstante; `PROJECT_CONTEXT_INJECTED`/`PROJECT_CONTEXT_MODE`-Default in `_build_provider_vars` (`:489-554`); Per-Rolle-Anwendung in der Schleife (`:1444-1470` vor `_apply_content_pipeline` `:1460`); Label-Cleanup + dreistufiger Pointer-Fallback (`</context>` → `</workflow>` → Dateiende) + Delta-Zähler + Log-Zeile nach der Schleife. **Achtung: #1181 (T8) ändert dieselbe Schleife `:1457-1468` und `_finalize_agent_content` — seriell, nicht parallel.** | T4-T7 |
| `agents/1-generic/ui-ux-designer.md` | ändern | 2 Prosa-Vorkommen (`:77`, `:105`) auf `{{#if}}`/`{{else}}`; `version: "1.6.0"` → `"1.6.1"` | T9 |
| `agents/1-generic/bug-feature-analyzer.md` | ändern | 1 Prosa-Vorkommen (`:40`); `version: "1.5.1"` → `"1.5.2"` | T9 |
| `agents/1-generic/knowledge-curator.md` | ändern | 1 Prosa-Vorkommen (`:55`); `version: "1.4.2"` → `"1.4.3"` | T9 |
| `agents/1-generic/knowledge-migrator.md` | ändern | 1 Prosa-Vorkommen (`:38`); `version: "1.5.2"` → `"1.5.3"` | T9 |
| `scripts/lib/consistency/project_context_injection.py` | **neu** | 3 Check-IDs (`pointer-missing`, `whitelist-no-effect`, `mode-unknown`), Muster: `scripts/lib/consistency/context_size.py:44-100` | T11 |
| `scripts/consistency-check.py` | ändern | Import-Block (`:42-70`) + Aufruf im Provider-Block (`:251-267`) | T11 |
| `scripts/admin-server.py` | ändern | `"project-context-injection"` in `PROJECT_WRITABLE_SECTIONS` (`:234-259`) | T12 |
| `docs/ui/admin-ui.html` | ändern | `viewProjectContextInjection`, Nav (`:1632-1633`), `router.register` (`:11264-11265`), `routeMap` (`:11381-11383`); Pane-Muster `:7650-7761`, Speichern über `saveProjectSection` (`:5960-5962`) | T13 |
| `docs/api/admin-ui-reference.md` | ändern | Help-Block mit `<!-- help-id: project_instance-project_context_injection -->` — ohne das schlägt `docs.ui_help_mappings` fehl (`scripts/lib/consistency/docs.py:47-97`) | T13 |
| `docs/guides/features/sync-concept.md` | ändern | Variablen-Tabelle „Auto-injiziert" (`:278-292`) um `PROJECT_CONTEXT_MODE`/`PROJECT_CONTEXT_INJECTED` erweitern | T14 |
| `howto/configs/project.yaml.example` **und** `templates/configs/project.yaml.example` | ändern | kommentierter `project-context-injection`-Block in **beiden** existierenden Beispiel-Dateien mit derselben Sektion (Muster `release-checklist` in `howto/…:99`, `context-profile` in `templates/…:318`); Divergenz zwischen den beiden Dateien ist ein Doku-Fehler | T14 |
| `CHANGELOG.md` | ändern | Eintrag unter „Unreleased" | T14 |
| `tests/test_project_context_injection_config.py` | **neu** | Schema, Resolver, Platzhalter-Registrierung | T1-T3 |
| `tests/test_project_context_injection_render.py` | **neu** | Golden `all`, `core`, `core+whitelist`, `core+orchestrator`, Pointer-Heuristik, Delta | T4-T10 |
| `tests/test_project_context_injection_consistency.py` | **neu** | 3 Check-IDs + Registrierung + `--validate`-Integration | T11 |
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
- **Ziel:** `pointer-missing`/`whitelist-no-effect`/`mode-unknown` laufen in `--validate`, die Sektion ist über die Admin-API schreibbar und im UI editierbar, Doku ist nachgezogen, ein Scratch-Konsument spielt alle vier Modi durch.
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
- `test_schema_defaults_are_all_empty_inherit` — `properties["project-context-injection"]["properties"]["{mode,whitelist,orchestrator}"]["default"]` == `"all"` / `[]` / `"inherit"`.
**Implementierung:** JSON-Property exakt wie Spec §4.1, eingefügt nach dem `context-profile`-Block (`:2849`) und vor `"required"` (`:2851`). `whitelist.items.pattern: "^[a-z0-9][a-z0-9-]*$"`.
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_config.py -k schema --basetemp="$PYTEST_BASETEMP" -q` → 4 passed.
**Abhängigkeiten:** keine · **Größe:** S

---

### T2 — Resolver `resolve_project_context_scope()` + Variablen
**Datei:** `scripts/lib/config.py` (ändern) · `tests/test_project_context_injection_config.py` (neu)
**Test zuerst:**
- `test_scope_absent_config_defaults_to_all` — `resolve_project_context_scope({}, root)` == `{"mode": "all", "whitelist": [], "orchestrator": "inherit", "orchestrator_roles": ("orchestrator", ...), "present": False}`; wirft nicht (Pflicht: `derive_builder_vars` ruft `build_variables({}, …)`, `placeholders.py:299-306`).
- `test_scope_null_section_is_all` — `{"project-context-injection": None}` → `mode="all"`, `present=False`.
- `test_scope_unknown_mode_raises_sync_error` — `mode: "slim"` → `SyncError` mit `project-context-injection.mode-unknown` **und** dem Wert `'slim'` in der Meldung.
- `test_scope_unknown_orchestrator_value_raises`.
- `test_scope_whitelist_unknown_role_lists_all_names` — `["developer","nope","nada"]` → `SyncError`, Meldung enthält `nope` **und** `nada` (sortiert, kommagetrennt).
- `test_scope_whitelist_known_roles_accepted` — `["developer","planner"]` → ok (Namen aus `build_role_map`).
- `test_scope_all_plus_exclude_is_error` und `test_scope_core_orchestrator_plus_exclude_is_error`.
- `test_scope_orchestrator_roles_include_primary_role` — Provider-Registry mit `primary-role: lead` in `provider_config` → Menge enthält `orchestrator` **und** `lead`, dedupliziert; Provider ohne `primary-role` tragen nur `orchestrator` bei.
- `test_build_variables_exposes_mode` — `build_variables({"project-context-injection": {"mode": "core"}}, root)[0]["PROJECT_CONTEXT_MODE"] == "core"`.
**Implementierung (Signaturen):**
```python
PROJECT_CONTEXT_MODES: tuple[str, ...] = ("all", "core+orchestrator", "core+whitelist", "core")
PROJECT_CONTEXT_ORCHESTRATOR_VALUES: tuple[str, ...] = ("inherit", "include", "exclude")

def resolve_project_context_scope(config: dict, agent_meta_root: Path,
                                  provider_config: dict | None = None) -> dict:
    """{'mode': str, 'whitelist': list[str], 'orchestrator': str,
        'orchestrator_roles': tuple[str, ...], 'present': bool}. Raises SyncError.

    ``provider_config=None`` loads ``config/ai-providers.yaml`` via
    load_providers_config(); tests inject a fake registry.
    """
```
Auflösung: `section = config.get("project-context-injection")`; Mapping → Werte prüfen, alles andere (None/String/Liste) → wie „fehlt" (`all`), aber `present=False`; ein **Mapping** mit falschen Enum-Werten → `SyncError`. Rollen-Registry: `build_role_map(agent_meta_root)` (`roles.py:80`). Orchestrator-Menge: `{"orchestrator"} ∪ {pc["primary-role"] for provider in resolve_providers(config, load_providers_config(agent_meta_root)) if pc.get("primary-role")}` — Datenquelle `config/ai-providers.yaml` über `provider_config[P]` (Beleg: `context.py:1711` liest `pc.get("primary-role")`), **kein** Provider-Namenszweig.
Aufruf am Ende von `build_variables` neben dem `context-profile`-Block (`:2810-2827`):
```python
variables["_PROJECT_CONTEXT_SCOPE"] = resolve_project_context_scope(config, agent_meta_root)
variables["PROJECT_CONTEXT_MODE"] = variables["_PROJECT_CONTEXT_SCOPE"]["mode"]
```
`_SYNC_SKIPPED_DEFAULT_KEYS` (`:183-191`) um `"project-context-injection"` ergänzen. (Die Sektion hat **keinen** Top-Level-Default — die Defaults stehen nur in `properties.*.default`. Der einzige Nested-Fill-Zweig `:1379-1389` behandelt ausschließlich `dod.*`; der Eintrag ist deshalb ein **reiner Regressionsschutz** für eine künftige allgemeine Nested-Materialisierung, kein heute wirksamer Fix. `--fill-defaults`/`--init` dürfen die Sektion materialisieren; die Spec fordert das nicht.)
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_config.py -k "scope or exposes" --basetemp="$PYTEST_BASETEMP" -q` → 9 passed.
**Abhängigkeiten:** T1 · **Größe:** M

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
**Implementierung:** im `provider_vars`-Dict (`:510-535`) bzw. nach dem `provider_vars.update(...)`-Block:
```python
scope = variables.get("_PROJECT_CONTEXT_SCOPE") or {}
provider_vars["PROJECT_CONTEXT_MODE"] = scope.get("mode", "all")
provider_vars["PROJECT_CONTEXT_INJECTED"] = "true"   # konservativer Default = heute
```
Mutieren von `merged_vars` bleibt sicher, weil `_build_provider_vars` mit `{**variables, **provider_vars}` (`:554`) eine flache Kopie zurückgibt.
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_render.py -k provider_vars --basetemp="$PYTEST_BASETEMP" -q` → 2 passed.
**Abhängigkeiten:** T2, T3 · **Größe:** S

---

### T5 — Per-Rolle-Injektionsentscheidung
**Datei:** `scripts/lib/agent_sync.py` (ändern) · `tests/test_project_context_injection_render.py` (neu)
**Test zuerst:**
- `test_injection_matrix` — parametrisiert `(mode, whitelist, orchestrator, role) → bool` exakt nach Spec §3.1-Tabellen (16 Fälle inkl. `core`+`include`, `core+whitelist`+`include`, `core+whitelist`+`inherit`, `all`+`inherit`, Whitelist-Rolle mit `primary-role`):
  - `all` → immer `True`
  - `core` → `False` außer `orchestrator == "include"` und Rolle ∈ orchestrator_set
  - `core+orchestrator` → nur orchestrator_set
  - `core+whitelist` → **nur** Whitelist; orchestrator_set kommt **nur** bei `orchestrator == "include"` hinzu (`inherit` und `exclude` inkludieren keine Orchestrator-Rolle)
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
`agent_sync` importiert `project_context_injected_for_role` aus `.config` (dort bereits importiert), damit `consistency/project_context_injection.py` keinen neuen Modul-Rand zu `agent_sync` braucht.
Aufruf in der Schleife (`:1458` nach `_build_provider_vars`, **vor** `_apply_content_pipeline` `:1460`), weil `substitute` (`:730`) und `strip_inactive_conditional_blocks` (`:737`) den Wert vorher brauchen (Spec §5.3 Schritt 2-4).
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_render.py -k "matrix or apply_scope" --basetemp="$PYTEST_BASETEMP" -q` → 19 passed.
**Abhängigkeiten:** T4 · **Größe:** M

---

### T6 — Pointer-Zeile: Label-Cleanup + dreistufiger Fallback
**Datei:** `scripts/lib/agent_sync.py` (ändern) · `tests/test_project_context_injection_render.py` (neu)
**Test zuerst:**
- `test_pointer_line_text_is_exact` — Konstante entspricht zeichengenau Spec §3.2 (eine Zeile, Englisch, Backticks um `{context_file}`).
- `test_pointer_uses_resolved_context_file_per_provider` — Claude → `CLAUDE.md`, Gemini → `AGENTS.md`, Opencode → `AGENTS.md`, Continue → `.continue/rules/project-context.md` (Quelle `pc["context_file"]`, `agent_sync.py:515`).
- `test_pointer_inserted_at_end_of_context_section` — gerendertes `developer.md` in `core`: Pointer steht vor `</context>` (`developer.md:92`), **eine** Zeile.
- `test_pointer_inserted_before_workflow_when_no_context_section` — `intern-developer.md` (kein `<context>`, `</workflow>` `:39`) → Pointer vor `</workflow>`.
- `test_pointer_appended_at_eof_with_note` — `mammouth-expert.md` **und** je eine `se-*`-Rolle (weder `<context>` noch `</workflow>`) → Pointer am Dateiende **und** `log.note("project-context-injection", "no <context>/</workflow> in mammouth-expert.md — pointer appended at EOF")`.
- `test_dangling_project_context_label_is_removed` — Template-Form `**Project context:** {{PROJECT_CONTEXT}}` (60 Dateien, z. B. `orchestrator.md:316`): in `core` enthält das Artefakt **kein** `**Project context:**` mehr. Diese Mechanik ist jetzt in Spec §3.2/§3.6 D-2 verbindlich dokumentiert (kein reines Plan-Detail mehr).
- `test_no_pointer_when_injected` — `all` enthält die Pointer-Zeile nicht.
- `test_exactly_one_pointer_per_excluded_role` — über **alle 98** Rollen eines Providerlaufs: `content.count(pointer) == 1` für exkludierte, `== 0` für inkludierte Rollen; der Lauf enthält mindestens eine Rolle aus jeder Fallback-Gruppe (`developer` = `<context>`, `intern-developer` = `</workflow>`, `se-architect` + `mammouth-expert` = Dateiende).
**Implementierung:**
```python
_PROJECT_CONTEXT_POINTER = (
    "Project context: read `{context_file}` first — it is the single source for "
    "project-specific facts (embedded here only when "
    "`project-context-injection.mode` includes this role)."
)

def insert_project_context_pointer(content: str, pointer: str, role: str,
                                   source_name: str, log) -> str:
    """1) drop an empty '**Project context:**' label line (only when the line
        contains nothing else); 2) insert `pointer` as one line before the
        last '</context>', else before the last '</workflow>', else append at
        EOF and emit a note."""
```
Reihenfolge: erst Label-Cleanup (Regex `^[ \t]*\*\*Project context:\*\*[ \t]*\r?\n`, `re.MULTILINE`), dann Einfügen. Der Cleanup läuft **nur** im Nicht-Injiziert-Zweig, deshalb bleibt `all` byte-identisch. Insert-Semantik: `content.rfind("</context>")` (Zeilenanfang berücksichtigen, Pointer-Zeile + `\n` davor), sonst `rfind("</workflow>")`, sonst `content.rstrip("\n") + "\n\n" + pointer + "\n"`. Für Rollen mit Block-Vorkommen kommt der Aufruf nach dem Blanking; für Rollen ohne Vorkommen (`se-*`, `mammouth-expert`, `intern-developer`) nur der Insert-Teil.
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_render.py -k "pointer or dangling" --basetemp="$PYTEST_BASETEMP" -q` → 8 passed.
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
- `test_core_keeps_required_sections_non_empty` — für `core` enthält jedes der 8 Artefakte weiterhin seine Pflichtsektionen; `<context>` bleibt nicht-leer, **wo das Template eine hat** (`intern-developer` und `mammouth-expert` haben keine — dort wird der Pointer-Fallback geprüft, nicht eine erfundene `<context>`-Sektion). AC7-Vorstufe.
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

### T11 — Konsistenz-Checks (3 IDs) + Registrierung
**Datei:** `scripts/lib/consistency/project_context_injection.py` (neu), `scripts/consistency-check.py` (ändern) · `tests/test_project_context_injection_consistency.py` (neu)
**Test zuerst:**
- `test_mode_unknown_is_error` — Config mit `mode: "slim"` → `Finding(severity=ERROR, check="project-context-injection.mode-unknown")`, ohne `jsonschema`-Abhängigkeit.
- `test_whitelist_no_effect_warns_for_other_mode` — `{"mode": "core", "whitelist": ["developer"]}` → `WARN`, Meldung „whitelist ignored (mode=core)".
- `test_whitelist_no_effect_warns_for_role_without_placeholder` — `mode: core+whitelist`, Whitelist enthält `se-architect` (kein Vorkommen) → `WARN`, Datei `agents/1-generic/se-architect.md` in der Meldung.
- `test_pointer_missing_warns_when_artifact_lacks_pointer` — Fixture-Projektverzeichnis mit `CLAUDE.md` + `.claude/agents/developer.md` ohne Pointer, `mode: core` → `WARN` `pointer-missing`.
- `test_pointer_present_is_clean` — Artefakt mit genau einer Pointer-Zeile → keine Findings.
- `test_check_registered_in_run_checks` — `check_project_context_injection` im Import-Block und im Provider-Block von `scripts/consistency-check.py` referenziert (Quelltext-Assertion).
**Implementierung:**
```python
def check_project_context_injection(root: Path, config: dict | None = None,
                                   provider_config: dict | None = None) -> list[Finding]:
    """3 IDs: mode-unknown (ERROR), whitelist-no-effect (WARN),
    pointer-missing (WARN). Fail-soft: fehlende Sektion => []."""
```
Datenquelle für `pointer-missing`: pro aktivem Provider (`resolve_providers`) `<agents_dir>/*.md` lesen (Muster `context_size.py:91-100`), Rolle = Datei-Stem, erwartete Injektion aus `resolve_project_context_scope` + `project_context_injected_for_role` (beide `lib.config`), Pointer-Text mit `pc["context_file"]`. Keine Datei → überspringen (nie Fehler). Registrierung in `scripts/consistency-check.py:251-267`.
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_consistency.py --basetemp="$PYTEST_BASETEMP" -q` → 6 passed; `python3 scripts/sync.py --validate` → PASS.
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
- `test_pane_offers_mode_and_orchestrator_enums` — Quelltext enthält `["all", "core+orchestrator", "core+whitelist", "core"]` und `["inherit", "include", "exclude"]`.
- `test_help_id_mapping_present` — `check_ui_help_mappings(REPO_ROOT)` liefert kein Finding für `project_instance-project_context_injection`.
**Implementierung:** `async function viewProjectContextInjection(wrap)` (Muster `viewProjectAutoCommit` `:7649-7761`): `const data = await loadProject();` → `const pci = (data["project-context-injection"] && typeof … === "object") ? clone(...) : {};`; drei `dropdownField`/Multi-Select-Felder; Whitelist-Optionen: `api.get("/api/config/role-defaults")` (super-admin-Pfad, `:1901`), bei Fehler `data.roles || []`, bei beidem leer Freitext-Comma-Eingabe; Save: `saveProjectSection("project-context-injection", out, status)`. Zusätzlich read-only Effekt-Vorschau „Rolle → injiziert ja/nein" (JS-Spiegel der Matrix, mit Hinweis „Server ist maßgeblich"). Help-Block in `docs/api/admin-ui-reference.md` nach dem Muster `<!-- help-id: project_instance-auto_commit -->` (`:182`).
**Verifikation:** `python3 -m pytest tests/test_admin_ui_project_context_injection_section.py --basetemp="$PYTEST_BASETEMP" -q`; `python3 scripts/sync.py --validate` → PASS (inkl. `docs.ui_help_mappings`).
**Abhängigkeiten:** T12 · **Größe:** M

---

### T14 — Doku
**Datei:** `docs/guides/features/sync-concept.md`, `howto/configs/project.yaml.example`, `templates/configs/project.yaml.example`, `CHANGELOG.md` (ändern) · `tests/test_project_context_injection_config.py` (neu)
**Test zuerst:**
- `test_sync_concept_documents_both_variables` — beide Variablennamen stehen in der Tabelle `:278-292`.
- `test_project_example_documents_section` — **beide** Beispiel-Dateien (`howto/configs/project.yaml.example` und `templates/configs/project.yaml.example`) enthalten einen auskommentierten `project-context-injection`-Block mit allen drei Keys; der Test parametrisiert über beide Pfade, damit die Sektion nicht divergiert.
- `test_changelog_mentions_issue_1187` — `CHANGELOG.md` enthält `#1187`.
**Implementierung:** je ein Tabelleneintrag + Beispielblock in **beiden** Beispiel-Dateien (sie dokumentieren dieselbe Sektion, `howto/…` ist das ausführliche Template, `templates/…` das kondensierte) + Changelog-Zeile. Kein `--explain`, kein Preset (Spec §3.4). `docs/guides/project.yaml.example` ist ein Orchestrator-Fragment und wird **nicht** angefasst.
**Verifikation:** `python3 -m pytest tests/test_project_context_injection_config.py -k "docs or changelog or example" --basetemp="$PYTEST_BASETEMP" -q` → 3 passed.
**Abhängigkeiten:** T2 · **Größe:** S

---

### T15 — Voller Szenarientest (Scratch-Konsument) + Gesamt-Regression
**Datei:** `.tmp/scenario-context-1187/` (Scratch, **kein** Repo-Artefakt) + `docs/plans/2026-11-09-project-context-injection-scope-plan.md` (Ausführungsnachweis anhängen)
**Test zuerst (ausführbares Shell-Szenario `run.sh`, das die Asserts enthält):**
1. `mkdir -p .tmp/scenario-context-1187/{project,meta}`; `meta/` = Symlink/Checkout des Arbeitsbaums; `project/.meta-config/project.yaml` mit `project{name,prefix,description}`, `ai-providers: [Claude, Opencode, Gemini]`, `roles: [orchestrator, developer, planner, ui-ux-designer, se-architect, mammouth-expert, intern-developer]` (die beiden letzten decken die `</workflow>`- und die Dateiende-Fallback-Gruppe ab).
2. Lauf A (`Sektion fehlt`) → Snapshot `.claude/agents`, `.opencode/agents`, `.gemini/agents`; danach `grep -c '^project-context-injection:' .meta-config/project.yaml` == `0` (der Sync materialisiert die Sektion **nicht**; die Assertion gehört hierher, weil Lauf B die Sektion selbst in die Test-Config schreibt).
3. Lauf B (`mode: all`) → `diff -r` gegen A **leer** (AC2).
4. Lauf C (`mode: core`) → `grep -c "Project context:" `.claude/agents/developer.md` == `1`; Absatz fehlt (AC3); `grep -c "CLAUDE.md"` ≥ `1`; `AGENTS.md` in `.gemini/agents/developer.md` (nicht `GEMINI.md`); `mammouth-expert.md` und `se-architect.md` haben je genau eine Pointer-Zeile am Dateiende; `intern-developer.md` hat sie vor `</workflow>`; Logzeile enthält `mode=core` und `chars saved=` > 0 (AC6).
5. Lauf D (`mode: core+whitelist`, `whitelist: [developer]`, `orchestrator` fehlt ⇒ `inherit`) → Absatz nur in `developer.md`; **`orchestrator.md` ohne Absatz**; unbekannter Name (`whitelist: [nope]`) → Exit ≠ 0, `nope` in stderr (AC4).
6. Lauf E (`mode: core+orchestrator`) → Absatz nur in `orchestrator.md` (+ `primary-role`-Rollen) (AC5). Zusatzlauf `core+whitelist` + `orchestrator: include` → `orchestrator.md` **mit** Absatz.
7. Lauf F (`mode: core+orchestrator`, `orchestrator: exclude`) → Exit ≠ 0 mit `orchestrator-exclude-conflict`; Zusatzlauf `mode: all` + `exclude` → derselbe Exit. Der Nachweis ist an `test_scope_core_orchestrator_plus_exclude_is_error` und `test_scope_all_plus_exclude_is_error` (T2) gekoppelt. **`mode: core` + `exclude` ist erlaubt** (exkludiert die Orchestrator-Rolle, Spec §3.1 Tabelle `:151`) und darf **nicht** als Fehler erwartet werden.
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

Harte Fehler (`SyncError`, rc 1, ohne Traceback): unbekannter `mode`/`orchestrator`-Wert; unbekannter Whitelist-Rollenname (alle Namen in der Meldung); `mode in {core+orchestrator, all}` + `orchestrator: exclude`. Warnungen (`log.note`/`WARN`): `whitelist` bei anderem Modus; Whitelist-Eintrag ohne Platzhalter; Rolle ohne `<context>`/`</workflow>` beim Pointer-Fallback.

### 5.2 Variablen-Vertrag

| Variable | Werte | Gesetzt in | Default bei fehlendem Kontext |
|---|---|---|---|
| `PROJECT_CONTEXT` | Absatz oder `""` | `agent_sync.apply_project_context_scope` (pro Rolle) | Absatz (Fallback `config.py:1860-1861`) |
| `PROJECT_CONTEXT_MODE` | 4 Enum-Werte | `config.build_variables` | `"all"` |
| `PROJECT_CONTEXT_INJECTED` | `"true"`/`"false"` | `agent_sync.apply_project_context_scope` | `"true"` (`_build_provider_vars`) |
| `CONTEXT_FILE` | Provider-Kontextdatei | `_build_provider_vars` (`:515`) | unverändert |

Interne Träger-Variable: `_PROJECT_CONTEXT_SCOPE` (`dict`, führender Unterstrich ⇒ von `derive_builder_vars` ausgefiltert, `placeholders.py:305-306`).

### 5.3 Pointer-Vertrag

```
Project context: read `{context_file}` first — it is the single source for project-specific facts (embedded here only when `project-context-injection.mode` includes this role).
```
- Genau **eine** physische Zeile; `{context_file}` = `pc["context_file"]` (`agent_sync.py:515`), kein verschachtelter Platzhalter (Substitution ist einpassig, `variables.py:698`).
- Mechanik (verbindlich, Spec §3.2): Block blankieren → leer gewordene `**Project context:**`-Zeile entfernen → Pointer als eine Zeile vor dem letzten `</context>` einfügen.
- Fallbacks für Rollen **ohne** Block-Vorkommen: letzte `</workflow>`-Zeile → davor (`intern-developer`); sonst Dateiende + `log.note` (13 `se-*` + `mammouth-expert`). Unter den 15 Rollen ohne Platzhalter hat heute **keine** ein `<context>`.

### 5.4 Render-Reihenfolge (Invariante, Spec §5.3)

`scope auflösen (einmal)` → `apply_project_context_scope(merged_vars, role, scope)` → `substitute` (`:730`) → `strip_inactive_conditional_blocks` (`:737`) → `Label-Cleanup + Pointer` (auch für Rollen ohne Block) → `write` (`:1469`) → `Delta-Zähler`.

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

Provider-Achse wird über `pc["context_file"]` parametrisiert, nicht über Provider-Namen im Code (Provider-Agnostik, Spec §4.5).

**Zwischentests:** siehe Meilenstein-Gates (§3). Nach jedem Meilenstein zusätzlich `python3 scripts/sync.py --validate` und `python3 scripts/sync.py --check` (DRY-RUN, keine neuen Warnungen gegenüber `.tmp/issue-dump/baseline-check.txt:1-7`).

**Ein voller Szenarientest am Ende:** T15, `.tmp/scenario-context-1187/`, alle vier Modi + zwei Fehlerfälle, Ergebnis dokumentiert.

**Konventions-Abweichung (bewusst):** Es wird **kein** Eintrag in `tests/scenarios/registry.md` angelegt (Konvention `rules/2-platform/agent-meta-conventions.md:123`). Grund: Der Wave-Scope legt den End-to-End-Beweis als Scratch-Konsumenten in `.tmp/` fest. Falls der Wave-Orchestrator die Szenarien doch registriert: **`94` ist für #1181 reserviert, `95`–`98` für #1187, `99` für #1186** (kein zusätzlicher Implementierungsaufwand außer den Config-Dateien). Dieser Plan verbraucht keine ID vorab.

---

## 7. Migration & Rollback

- **Default bleibt `all`:** Fehlt die Sektion (oder ist sie `null`/kein Mapping), liefert der Resolver `mode=all`, `present=False`; es wird nichts blankiert und kein Pointer eingefügt. Nachweis: `test_scope_absent_config_defaults_to_all` + `test_all_matches_default_absent_key`.
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

---

## 9. AC→Task-Traceability

| AC (Spec §7) | Task(s) | Absicherung |
|---|---|---|
| **AC1** Schema + Admin-UI-Schreibbarkeit | T1, T12, T13 | Schema-Tests (valid/invalid), `PROJECT_WRITABLE_SECTIONS`-Assertion, `PUT /api/config/project/section`-Round-Trip, Route/Help-ID |
| **AC2** `all` byte-identisch | T4, T8, T9, T10 | `test_all_matches_default_absent_key`, unverändertes Golden-Gate, `test_all_prose_matches_golden`; Sektion wird nicht materialisiert (`grep -c '^project-context-injection:' == 0`, T15 Schritt 2 / Lauf A) |
| **AC3** `core`: 0 Blöcke, 1 Pointer, reale Datei | T5, T6, T8 | `test_core_renders_zero_blocks`, `test_pointer_uses_resolved_context_file_per_provider`, `test_exactly_one_pointer_per_excluded_role` (inkl. `intern-developer` → `</workflow>`, 13 `se-*` + `mammouth-expert` → Dateiende) |
| **AC4** `core+whitelist`, unbekannter Name = Fehler | T2, T8 | `test_scope_whitelist_unknown_role_lists_all_names`, `test_core_whitelist_only_whitelisted_roles`, `test_core_whitelist_unknown_name_fails_render` |
| **AC5** `core+orchestrator` | T2, T5, T8 | `test_scope_orchestrator_roles_include_primary_role`, `test_core_orchestrator_only_orchestrator_roles` |
| **AC6** Delta im Sync-Log | T7 | 4 Log-Tests inkl. `chars saved == 0` bei `all` |
| **AC7** Prompt-Qualität bei `core` | T8, T11, T15 | `test_core_keeps_required_sections_non_empty`, `pointer-missing = 0`, `sync.py --validate` grün im Szenario |
| Issue-Requirement „Default bleibt `all`" | T2, T8 | `test_scope_absent_config_defaults_to_all`, AC2-Tests |
| Issue-Requirement „Delegation-Contract unverändert" | T15 (Diff-Check) | `schemas/a2a-handoff.schema.json` nicht in `git diff --name-only aaed14c2..HEAD -- schemas/a2a-handoff.schema.json` (eingefrorener Basis-Hash, nicht `HEAD`) |
| Issue-Requirement „Provider-aware Pointer" | T6 | Test über alle Provider aus `config/ai-providers.yaml`, Gemini-Fall (`AGENTS.md`) explizit |

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
| **OQ-2** | Gehören `primary-role`-Rollen zur Orchestrator-Achse? | **Ja** — `primary-role` ist der reale Provider-Einstieg (`config/ai-providers.yaml`; Beleg `context.py:1711`). Achtung: Spec schreibt „`providers.<P>.primary-role`", die Datenquelle ist die Provider-Registry, nicht `project.yaml`. | **blockiert T2** (`orchestrator_roles`). Bei „nein": nur `{"orchestrator"}`, AC5-Test einfacher, Provider mit abweichendem Einstieg verlieren in `core` den Kontext. |
| **OQ-3** | `all` + `orchestrator: exclude` = Fehler oder stille Verengung? | **Harter Fehler** (analog unbekannter Whitelist-Name). | **blockiert T2** (`SyncError`-Fall). Bei „stille Verengung": Matrix in T5 bekommt einen fünften Pfad, AC5-Set ändert sich. |
| **OQ-4** | AC7 nennt „existing prompt-quality checks", die es unter diesem Namen nicht gibt (vorhanden: Frontmatter `frontmatter.py`, Platzhalter `placeholders.py:12`, `context.*` `context_budget.py:293/540`) | **AC7 = `sync.py --validate` grün + `project-context-injection.pointer-missing == 0` + nicht-leere Pflichtsektionen** | **blockiert T8/T15-Testdefinition**. Bei anderer Auslegung muss ein neuer Check definiert werden (nicht in dieser Spec). |
| **OQ-5** | Pointer-Sprache Englisch oder Projektsprache? | **Englisch** (konsistent mit `<context>`-Blöcken; Lokalisierung ist ein separates Thema). | **blockiert T6** (Text-Assertions). Bei Projektsprache: `pointer` müsste aus `COMMUNICATION_LANGUAGE` abgeleitet werden (neue Logik, Spec-Änderung). |
| **OQ-6** (neu, aus dem Plan) | Was passiert mit dem leer werdenden `**Project context:**`-Label in 60 Templates (`developer.md:66`, `orchestrator.md:316`)? | **Aufgelöst (Review 2026-11-09):** Label-Zeile entfernen, nur im Nicht-Injiziert-Zweig — jetzt verbindlich in Spec §3.2/§3.6 D-2. AC2 bleibt unberührt, AC7 („keine leeren Pflichtsektionen") wird erfüllt. | **nicht mehr blockierend** (Spec-Revision 2). |
| **OQ-7** (neu, aus dem Plan) | Fallback für Rollen ohne `<context>` **und** ohne `</workflow>`? | **Aufgelöst (Review 2026-11-09):** Pointer ans Dateiende + `log.note`, jetzt Spec-Vertrag (§3.2 Fallback-Tabelle). Betroffen: 13 `se-*` + `mammouth-expert`; `intern-developer` hat `</workflow>` und nutzt den zweiten Fall. | **nicht mehr blockierend** (Spec-Revision 2). Ohne den Fallback fehlte 14 Rollen der Pointer → AC3 verletzt. |

---

## 13. Review-Auflösung (2026-11-09)

Alle Befunde aus dem Review vom 2026-11-09 sind eingearbeitet. Status bleibt `DRAFT`; Plan-Revision 2 (identisch zur Spec-Revision 2).

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
| **RVW2-1187-01** (MAJOR) | Lauf F erwartete bei `mode: core` + `orchestrator: exclude` einen Fehler, obwohl Spec §3.1 (`:151`) das erlaubt (exkludiert). Lauf F auf `mode: core+orchestrator` (+ Zusatzlauf `all`) + `exclude` umgestellt und an `test_scope_core_orchestrator_plus_exclude_is_error`/`test_scope_all_plus_exclude_is_error` gekoppelt; `core` + `exclude` ist ausdrücklich **kein** Fehler. | T15 Schritt 7 |
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

## 14. Ausführungsnachweis

> Wird bei der Ausführung befüllt (Datum, HEAD, Szenario-Logzeilen, Testläufe). Bis dahin leer — **kein** Platzhalter für Implementierungsdetails, nur das Ergebnisprotokoll.
