# Opencode v2-Support (Phasen C0, B, C1/C2, C3, D) — Implementation Plan

> Status: APPROVED (2026-10-22)
>
> **Freigabe-Gate:** Nutzerfreigabe 2026-10-22 (Auftrag: beide Pläne vollständig abarbeiten). Die zugrunde liegende Spec (Rev. 1.5 inkl. Amendment B1) trägt `Status: APPROVED (2026-10-22)`. Die Entry-Kriterien E1–E4 gelten weiterhin operativ (E1 = Plan A gemergt) und werden vor der betroffenen Phase belegt. Die Abweichung A-6 (Wiederverwendung des bestehenden Schalters `provider-options.Opencode.surface-version` statt eines neuen Schlüssels, Spec OQ-B1) ist vom Nutzer bestätigt (2026-10-22); es gibt keinen neuen Schalter und keinen Alias.
>
> **Revision 2026-10-23 (Amendment B1 aus C0):** Spike-Verdikt `VERDICT-C3: GO`, `VERDICT-FIELDS: AMEND` in die Spec Rev. 1.5 eingearbeitet. Plan-Folgen: `small-model`/`agents.title.model` entfällt (AC-B9 entfällt, Task 4/8 angepasst), `providers`-Innenform `settings.baseURL`/`env` (Task 8), `permissions[]`-Deny ans Listenende (Tasks 13/13a/22), `timeout.startup` (Task 14), `cli.json` nur mit `plugins` (Tasks 23/27/28), C3 läuft (Tasks 18/19). Keine Umnummerierung; Details im Re-Planning-Vermerk am Planende.
>
> **Revision 2026-10-22 (Rev. 1.4-Abgleich: Doku-Korrekturen — nicht existierende Test-Dateinamen durch konkrete ersetzt, `check_mcp_connection_keys` als neu anzulegen markiert, Task-5-Rot-Erwartung korrigiert; Rev. 1.3-Abgleich):** Nutzerantworten eingearbeitet (A-6 bestätigt, OQ-B12 bleibt offen bis nach C0-Verdict), Fake-Secret-Werte durch `EXAMPLE_NOT_A_KEY` ersetzt, Signaturen aus Spec 3.4 und Spike-Pfad mit der Spec abgeglichen (U-4, U-6). Task-Nummern und Traceability unverändert (kein Task entfällt: der Plan enthielt nie einen Task für den Schalter).

**Goal:** Opencode-v2-Surface vollständig und opt-in unterstützen — richtige v2-Config-Keys mit Managed-Merge (B), native `permissions[]` und MCP-v2-Form (C1/C2), Gate-Plugin nur bei Spike-GO (C3), v2-natives Agent-Frontmatter, `cli.json`, Duplikat-Bereinigung, Doku und Tests (D) — ohne Querwirkung auf v1 und andere Provider.
**Architecture:** Spike C0 liefert Evidenz und die Exit-Gate-Zeilen `VERDICT-C3`/`VERDICT-FIELDS`. Neues Modul `scripts/lib/opencode_v2_config.py` (Managed-Merge-Engine mit vier State-Namespaces, nur an aufgelösten Werten dispatchend, Writer und Rückbau nur für den Provider, dem die verwaltete Datei gehört: `owns_opencode_surface`). Erweiterungen in `isolation.py` (`permission_deny_required`, v2-Permissions-Builder/-Writer und der tierunabhängige Surface-Abgleich `reconcile_opencode_surface_gate` mit 7-Zeilen-Rückbau-Matrix), `mcp_provider_config.py` (v2-Verbindungsform + Managed-Pfade), `provider_transform.py` (eigene v2-Frontmatter-Funktion, Verzweigung auf `frontmatter-mechanism`), `providers.py` (`_apply_surface_aux_selection`). `_opencode_runtime_gate_entries`, `opencode_runtime_gate_wanted` und die Aufrufbedingung `sync_pipeline.py:1308` bleiben UNVERÄNDERT (Spec A IC-4/IC-7); v1-Pfade bleiben byte-identisch.
**Tech Stack:** Python 3.9/3.11/3.12 (Stdlib + PyYAML), pytest (+ `jsonschema` per `importorskip`), JSON-Schema, Bash-Szenarien (`tests/scenarios/run.sh`).
**Spec:** `docs/specs/2026-10-22-opencode-v2-support-spec.md`
**Spec-ID:** `spec-id: SPEC-OPENCODE-V2-SUPPORT-2026-10-22` (Rev. 1.5, `Status: APPROVED (2026-10-22)` + Amendment B1 (2026-10-23); Reviews `docs/reviews/2026-10-22-opencode-v2-support-spec-review.md`, `…-spec-rereview.md`)
**Abhängigkeit (Spec A):** `SPEC-OPENCODE-ENTRYPOINT-1006-2026-10-22` (`docs/specs/2026-10-22-opencode-entrypoint-1006-spec.md`, Plan `docs/plans/2026-10-22-opencode-entrypoint-1006-plan.md`)
**Tracking:** #1007 (relevant geschlossen: #747, #765, #794, #387, #383, #372)
**Estimated effort:** Gesamtaufwand und Phasenaufwand schätzt `effort-estimator` (Textverweis, keine eigene Zahl in diesem Plan).

## Phasen und Entry-Kriterien

| Phase | Tasks | Inhalt | Hängt ab von | Exit-Kriterium (messbar) |
|---|---|---|---|---|
| C0 | 1, 2, 3, 3a (+ 24, mit PR C0 gemergt) | Spike Plugin-/Hook-API v2 und Feld-Evidenz; AC-C2-Absicherungstest | E2, E3 (nicht E1: schreibt nur Doku und Tests der Bestandsstände, daher parallel zu Plan A zulässig) | `python3 -m pytest tests/test_opencode_v2_spike.py -q` grün (enthält AC-C1- und AC-C2-Tests); `python3 -m pytest tests/test_opencode_v2_surface.py -q -k ac_d8_evidence` grün; Spike-Doc enthält je genau eine Zeile `VERDICT-C3: GO\|NO-GO` und `VERDICT-FIELDS: CONFIRMED\|AMEND`; bei `AMEND`/`NO-GO` ist Amendment B1 in der Spec vermerkt |
| B | 4–12 | Config-Keys + Managed-Merge-Mechanik | E1, Phase C0; Start bei `VERDICT-FIELDS: CONFIRMED` **oder** nach eingearbeitetem Amendment B1 für die Q6-Keys (Keys mit negativem Q6-Ergebnis entfallen per Amendment B1). Ein `AMEND`, das nur aus Q5 (MCP/Frontmatter-Felder) stammt, blockiert B nicht, sondern nur C2 (Tasks 14–17) und D1 | `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_opencode_v2_config.py tests/test_opencode_v2_schema.py tests/test_opencode_v2_aux_selection.py tests/test_opencode_runtime_gate.py -q` grün; `python3 scripts/sync.py --validate` rc 0 |
| C1/C2 | 13, 13a, 14–17 | `permission_deny_required` und `reconcile_opencode_surface_gate` mit `permissions[]`-Gate und surface-übergreifendem, tierunabhängigem Rückbau (C1), MCP-v2-Form + Managed-Pfade + Katalog-Validierung (C2) | B; C2: Q5-Anteil von `VERDICT-FIELDS` bestätigt (DOKU, Amendment B1); C1: Managed-Tripel ans Listenende (Amendment B1) | Tests von Task 13–17 grün; `tests/test_mcp_config.py` unverändert grün (v1-Byte-Freeze) |
| C3 | 18–19 | Gate-Plugin v2 — **nur bei `VERDICT-C3: GO`** | C1 (inkl. 13a) + `VERDICT-C3: GO`; bei `NO-GO` entfällt die Phase ersatzlos (Fallback: Permissions-Tier, C1 bleibt Gate; Task 3a sichert den Fallback ab) | Tests von Task 18–19 grün; Tier für v1 bleibt `permission` |
| D | 20–33 (ohne 24) | v2-Frontmatter, `cli.json`, Duplikat, Doku, Tests, Release | B, C1, C2 | `python3 scripts/sync.py --validate` rc 0, `python3 scripts/sync.py --check` rc 0, `python3 scripts/consistency-check.py` rc 0 |

**Task-Zahl je Phase:** C0 = 4 (1, 2, 3, 3a), B = 9 (4–12), C1/C2 = 6 (13, 13a, 14–17), C3 = 2 (18–19), D = 14 (20–33; davon Task 24 mit PR C0 gemergt). Gesamt 35 (Nummern 1–33 plus 3a und 13a unverändert gegenüber Plan-Stand vor Rev. 1.2, damit bestehende Verweise gültig bleiben).

**Entry-Kriterien (alle vor Start der ersten Implementierungs-Phase zu belegen):**
- **E1** Plan A ist auf `main` gemergt. Nachweis: `git log --oneline main --grep "1006"` liefert mindestens einen Treffer und `grep -n "_STATE_DEFAULT_AGENT_KEY" scripts/lib/isolation.py` findet die Konstante (Spec A IC-6).
- **E2** Spec B trägt `Status: APPROVED` (Freigabe durch Nutzer bzw. `concept-reviewer`).
- **E3** Nutzerbestätigung zu A-6/OQ-B1: ERFÜLLT (vom Nutzer bestätigt, 2026-10-22) — der bestehende Schlüssel `provider-options.Opencode.surface-version` wird weiterverwendet; kein neuer Schalter, kein Alias, kein Zusatz-Task. Schema (`config/project-config.schema.json:864`) und Resolver (`providers.py::_apply_project_surface_overrides`) bleiben für den Schalter unverändert.
- **E4** Arbeitsbranch nach `.claude/rules/branch-guard.md` (`feat/1007-…`), kein Worktree.

**Merge-Reihenfolge (seriell, ein PR je Phase):** Plan A → PR C0 (Tasks 1–3, 3a, 24) → PR B (4–12) → PR C1/C2 (13, 13a, 14–17) → PR C3 (18–19, nur bei GO) → PR D (20–33 ohne 24). Kein Paket startet vor dem Merge seines Vorgängers (gemeinsame Dateien `scripts/lib/isolation.py`, `scripts/lib/context.py`, `scripts/lib/provider_transform.py`, `config/ai-providers.yaml`, `config/project-config.schema.json`). Einzige Ausnahme: Phase C0 darf parallel zu Plan A laufen. Sie berührt nur `docs/spikes/…`, `docs/analysis/evidence/…`, `tests/test_opencode_v2_spike.py` (neu, Tasks 1, 3a), `tests/test_opencode_v2_surface.py` (nur Task 24), die Spec und diesen Plan; Plan A ändert keine dieser Dateien (geprüft, Re-Review i-1/m-4). Task 3a ändert nur `tests/test_opencode_v2_spike.py` und ist damit dateidisjunkt zu Task 24.

**Parallelität (nur bei durch `Files:` bewiesener Disjunktheit; Prüfung `check_plan_file_overlap`, `scripts/lib/orchestration.py`):**
- `parallel_group: c0-g1` — Task 2 (nur `docs/spikes/…`) ∥ Task 24 (`docs/analysis/evidence/…` und `tests/test_opencode_v2_surface.py`; disjunkt zu Task 2).
- `parallel_group: b-g1` — Task 4 (`config/project-config.schema.json`, `tests/test_opencode_v2_schema.py`) ∥ Task 5 (`scripts/lib/isolation.py`, `tests/test_opencode_runtime_gate.py`) ∥ Task 6 (`scripts/lib/providers.py`, `config/ai-providers.yaml`, `tests/test_opencode_v2_aux_selection.py`).
- Alle übrigen Tasks laufen sequenziell (gemeinsame Dateien `scripts/lib/opencode_v2_config.py`, `tests/test_opencode_v2_surface.py`, `scripts/lib/isolation.py`).

## Global Constraints

- **Provider-agnostisch (Pflicht, Skill `provider-agnostic`):** Dispatch ausschließlich über aufgelöste Config-Werte (`mcp-config.format`, `mcp-config.surface-formats`, `mcp-config.committed-file`, `agent-transform.frontmatter-mechanism`, `model-pattern`, `cli_file`, `has_plugins`, `plugin_protocol`), nie `if provider == "Name"`, nie ein Literal eines Providernamens und nie `surface-version` im Writer. Die Tests `tests/test_provider_agnostic_dispatch.py::test_no_provider_name_dispatch_branches_in_lib`, `::test_no_provider_literal_usage_in_lib` und `::test_no_surface_version_dispatch_in_lib` bleiben grün (der Sweep `_lib_modules()` erfasst neue Module automatisch).
- **Provider-/Datei-Bindung (Spec 3.2, N-M2):** Writer (`sync_opencode_v2_managed_keys`, `sync_opencode_mcp_managed`, `sync_opencode_cli_file`) und Rückbauten (`rollback_opencode_mcp`, `isolation.reconcile_opencode_surface_gate`) beginnen mit `if not opencode_v2_config.owns_opencode_surface(provider_config, provider): return`. `owns_opencode_surface(pc, provider)` ist True gdw. (a) `pc["mcp-config"]["surface-formats"]` ein nicht leeres dict ist, dessen Werte `"opencode-json-v2"` enthalten, UND (b) `pc["mcp-config"]["committed-file"]` ein nicht leerer String ist. Verwaltete Datei = `committed-file`; State-Datei = `opencode_v2_config.opencode_state_path(project_root, pc)`; beide Pfade werden aus den aufgelösten Daten abgeleitet, nie hartverdrahtet. Für jeden anderen Provider (Claude, Gemini, Mammouth ohne `surface-formats`, …) sind alle diese Funktionen No-op **bevor** State gelesen wird; sie erzeugen weder Datei-, State- noch Log-Änderungen. Wird dieselbe Datei von mehreren Providern beansprucht, handelt nur der erste Eigentümer je Lauf (`log.warning("opencode-v2-owner-conflict: <file>")` für jeden weiteren). Ergebnis ist reihenfolgeunabhängig (AC-B20).
- **v1-Freeze (Entscheidung 8/10):** `_map_claude_tools_to_opencode_permissions` und `_transform_frontmatter_for_opencode` (`scripts/lib/provider_transform.py`) werden nicht verändert; der v1-MCP-Pfad (`entry["enabled"] = True`) bleibt byte-identisch; `tests/test_opencode_v2_surface.py::test_v1_settings_template_is_byte_identical` bleibt grün.
- **Spec-A-Freeze (Spec 3.4, m-6):** `isolation._opencode_runtime_gate_entries` und `isolation.opencode_runtime_gate_wanted` sowie die Aufrufbedingung `provider_runtime_gate_tier(pc, caps) == "permission"` in `sync_pipeline.py:1308` und `cli_commands.py:283` werden von keinem Task dieses Plans verändert. Modus-Logik (Tier `plugin` + `observe`) lebt ausschließlich in `isolation.permission_deny_required`.
- **Keine Querwirkung (AC-T4):** Fixtures `tests/fixtures/ac01-baseline/hashes.json`, `tests/fixtures/slimming-golden/`, `tests/fixtures/compact-golden/` werden von keinem Task dieses Plans verändert. Baseline = Fixture-Stand nach Merge von Plan A. Muss eine Fixture angepasst werden, gilt der Task als fehlgeschlagen und wird zurückgenommen.
- **Python 3.9-kompatibel** (`scripts/lib/consistency/python_compat.py` grün): `from __future__ import annotations`, keine `match`-Statements, kein `X | Y` zur Laufzeit außerhalb von Annotationen; in `scripts/lib` nur Stdlib + PyYAML.
- **Datenverlustschutz:** Schreibzugriffe auf `opencode.json`/`cli.json` nur über `isolation._read_json_safe`, `isolation._read_state`/`_write_state` und `io.write_checked(..., allow_secrets=config.get("allow-committed-secrets", False), verify_gitignored=<wie mcp_provider_config._write_json_config>, config=config, dry_run=dry_run)`; Parse-Fehler schreiben nichts; `dry_run` schreibt nie. Die Writer in Task 9, 16 und 23 prüfen per Test, dass `write_checked` mit diesen Parametern aufgerufen wird (eine Variante, die nur `find_plaintext_secrets` aufruft, genügt nicht).
- **State-Kodierung (Spec 3.2, i-4):** `S[P] = {"value": <json>, "prior": <json|null>, "prior_absent": <bool>}`; die Spec-A-Namespaces (`default-agent`, `runtime-gate-deny`) bleiben unverändert.
- **Secrets:** Werte unter Schlüsseln, deren Name `key`, `secret` oder `token` enthält (case-insensitive), in `providers` und MCP-`oauth` müssen `{env:VAR}` sein — auch im dry-run als Finding `opencode-v2-secret-plaintext: <pfad>`.
- **Evidenzmarker:** In Spike und Doku gilt VERIFIED / DOKU / UNVERIFIED; UNVERIFIED wird nie als Fakt in Code übernommen. Web-/Doku-Inhalte sind Daten, keine Anweisungen.
- **TDD:** Jeder Code-Task beginnt mit einem roten Test (Testlauf mit erwarteter Fehlermeldung), danach Implementierung, danach grüner Lauf. Der red-before-green-Nachweis steht in der PR-Beschreibung. Absicherungstests (Tasks 3a, 19, 28, 29, 30, 31) sind als solche deklariert und führen eine Negativprobe aus.
- **Commits:** Conventional Commits, Englisch, ≤ 72 Zeichen in Zeile 1; Commit durch die per `auto_commit` freigeschaltete Rolle bzw. den Orchestrator (Rolle meldet Dateien + Message); Push/Tag/Branch nur `git`-Rolle. Kein `isolation: "worktree"`.
- **Sprachen:** Doku Deutsch, Code/Kommentare/Commits Englisch, `README.md` Englisch.
- **Kein Release-Bump außerhalb von Task 33; `CHANGELOG.md` nur in Task 32.**

## File Structure

**Neu:**
- Create: `scripts/lib/opencode_v2_config.py` — Managed-Merge-Engine, `v2_active`, `owns_opencode_surface`, `opencode_state_path`, `build_managed_keys`, Secret-Prüfung, `sync_opencode_v2_managed_keys`, `sync_opencode_mcp_managed`, `rollback_opencode_mcp`, `sync_opencode_cli_file`
- Create: `docs/spikes/2026-10-22-issue-1007-opencode-v2-plugin-api-spike.md` — Spike-Ergebnis C0 (Dateinamen-Konvention `YYYY-MM-DD-issue-<n>-<topic>-spike.md`; Pfad in Spec Rev. 1.3 bereits korrigiert; Task 3 prüft nur per Grep)
- Create: `docs/analysis/evidence/2026-10-22-opencode-jsonc-loading.md` — Ladeverhalten `opencode.json` + `opencode.jsonc`
- Create: `templates/plugins/runtime-gate.opencode-v2-plugin.js.tmpl` — nur Phase C3 bei GO
- Create: `tests/scenarios/configs/79-opencode-v2-full-surface.project.yaml`, `tests/scenarios/asserts/79-opencode-v2-full-surface.sh` — Szenario 79 (`chmod +x`)
- Create (Tests): `tests/test_opencode_v2_spike.py` (AC-C1, AC-C2), `tests/test_opencode_v2_schema.py`, `tests/test_opencode_v2_aux_selection.py`, `tests/test_opencode_v2_config.py`

**Modify:**
- Modify: `scripts/lib/isolation.py` — `_STATE_V2_*`-Konstanten, `_read_state` dict-Namespaces, `permission_deny_required`, `_opencode_v2_gate_permissions`, `_sync_opencode_v2_gate_permissions`, `reconcile_opencode_surface_gate`, Überspringen von Spec-A-Schritt 4 in `_sync_opencode_runtime_gate` auf v2
- Modify: `scripts/lib/providers.py` — `_apply_surface_aux_selection`, `SUPPORTED_PLUGIN_PROTOCOLS` (C3)
- Modify: `scripts/lib/runtime_gate.py` — `PLUGIN_TEMPLATE_BY_PROTOCOL`-Eintrag (C3)
- Modify: `scripts/lib/sync_pipeline.py` — `_sync_stage_per_provider` (Zeilen ~1303–1312, Bedingung ~1308 unverändert): tierunabhängige Aufrufe `reconcile_opencode_surface_gate` (direkt nach dem bedingten `_sync_opencode_runtime_gate`), danach `sync_opencode_v2_managed_keys`, `sync_opencode_cli_file`
- Modify: `scripts/lib/cli_commands.py` — Test-Repo-Pfad (~Zeilen 278–287), gleiche Aufrufe
- Modify: `scripts/lib/context.py` — `apply_settings_surface_shape` (`experimental.subagent_depth`)
- Modify: `scripts/lib/mcp_provider_config.py` — `_build_connection_entry`, `_update_opencode_v2_json_config`, `generate_provider_configs`
- Modify: `scripts/lib/provider_transform.py` — `map_tools_to_opencode_v2_permissions`, `_transform_frontmatter_for_opencode_v2`, Verzweigung im Zweig ~Zeile 384–424
- Modify: `scripts/lib/artifact_validate.py` — Kommentar IC-15 Nr. 16 (~Zeile 48), `validate_frontmatter` (model-pattern), `_validate_opencode_v2` (MCP-Form)
- Modify: `scripts/lib/consistency/artifact_contracts.py` — Create (new function) `check_mcp_connection_keys` (Task 17); Modify: `opencode-config-duplicate` (Task 25)
- Modify: `config/project-config.schema.json` — `provider-options.Opencode` (Zeile ~845) und MCP-`connection` (Zeilen ~1153 und ~1253)
- Modify: `config/ai-providers.yaml` — Opencode-Eintrag: `cli-files`, `agent-transform.surface-model-patterns`, `agent-transform.surface-v2-fields`, `allowed-fields` (`system`), C3: `surface-plugin-protocols`, `surface-has-plugins`
- Modify: `tests/test_opencode_v2_surface.py`, `tests/test_opencode_runtime_gate.py`, `tests/test_settings_depth_and_deny.py`, `tests/test_provider_agnostic_dispatch.py`, `tests/test_artifact_contracts.py`, `tests/scenarios/asserts/69-opencode-v2-surface.sh`, `tests/scenarios/registry.md`
- Modify: `docs/providers/opencode.md`, `docs/specs/2026-09-30-provider-audit-opencode-v2.md` (Amendment-Verweis), `docs/specs/2026-10-22-opencode-v2-support-spec.md` (Amendment B1 / Pfadkorrektur), `CHANGELOG.md`, `VERSION`
- Entfernen (nach Evidenz): `opencode.jsonc` im Repo-Root

---
pipeline_stages:
  implement: 3
---

## Phase C0 — Spike Plugin-/Hook-API v2 und Feld-Evidenz

### Task 1: C0.1 — Struktur-Test für das Spike-Ergebnisdokument anlegen (rot)
**Agent:** tester · **Issue:** #1007 · **AC:** AC-C1
**Depends on:** —
**Files:**
- Create: `tests/test_opencode_v2_spike.py`
**Interfaces:** Produces `tests/test_opencode_v2_spike.py` mit `SPIKE = Path("docs/spikes/2026-10-22-issue-1007-opencode-v2-plugin-api-spike.md")` und den 7 Tests `test_spike_doc_exists`, `test_q1_to_q6_sections_present`, `test_each_answer_has_marker_and_source`, `test_q5_q6_marker_per_key`, `test_ac_c1_verdict_lines_exactly_once`, `test_measure_budget_respected`, `test_verdict_consequences_recorded` (Task 3a ergänzt den achten Test `test_ac_c2_gate_fallback_invariants` in derselben Datei); Consumes `docs/spikes/…` (Task 2), `docs/specs/2026-10-22-opencode-v2-support-spec.md` (Task 3)
- [x] Step 1: Test schreiben: `test_q1_to_q6_sections_present` erwartet je eine `## Q1` … `## Q6`-Überschrift (Regex `(?m)^## Q[1-6]\b`, Anzahl 6); `test_each_answer_has_marker_and_source` erwartet je Q-Abschnitt **mindestens einen** der Marker `VERIFIED`/`DOKU`/`UNVERIFIED` und eine Zeile `Quelle:`; `test_q5_q6_marker_per_key` erwartet in Q5 je Feld `timeout`, `oauth`, `disabled`, `system`, `variant` und in Q6 je Key `experimental.subagent_depth`, `experimental.todo`, `providers`, `agents.title.model`, `cli.json` eine Zeile der Form `<key>: VERIFIED|DOKU|UNVERIFIED` (Spec Q5/Q6 verlangen Marker je Feld bzw. Key); `test_ac_c1_verdict_lines_exactly_once` erwartet `(?m)^VERDICT-C3: (GO|NO-GO)$` genau 1× und `(?m)^VERDICT-FIELDS: (CONFIRMED|AMEND)$` genau 1×; `test_measure_budget_respected` parst je Q-Abschnitt `Proben: <n>` und `Quellen: <n>` und erwartet n ≤ 3 bzw. ≤ 5 (Messbudget Spec 3.6); `test_verdict_consequences_recorded` erwartet in der Spec die Überschrift `Amendment B1`, wenn `VERDICT-FIELDS: AMEND` oder `VERDICT-C3: NO-GO` im Spike-Doc steht, sonst keine Bedingung
- [x] Step 2: rot beobachten: `python3 -m pytest tests/test_opencode_v2_spike.py -q` → Exit 1, `FAILED tests/test_opencode_v2_spike.py::test_spike_doc_exists` (Datei fehlt), übrige Tests ebenfalls `FAILED` (`7 failed`)
- [x] Step 3: kein Produktivcode in diesem Task; der Test bleibt rot bis Task 2
- [x] Step 4: commit `test: add structure test for opencode v2 spike document`

### Task 2: C0.2 — Spike ausführen: Plugin-/Hook-API, MCP-/Frontmatter-Felder, Phase-B-Keys
**Agent:** provider-expert · **Issue:** #1007 · **AC:** AC-C1 · **parallel_group:** c0-g1
**Depends on:** 1
**Files:**
- Create: `docs/spikes/2026-10-22-issue-1007-opencode-v2-plugin-api-spike.md`
**Interfaces:** Produces Ergebnisdokument mit Abschnitten `## Q1` … `## Q6` (Fragen laut Spec 3.6: Q1 Plugin-Mechanismus, Q2 Äquivalent zu `tool.execute.before`, Q3 Subagent-Session/Main-Chat-Unterscheidung plus Auswertungsreihenfolge von `permissions[]` und Vorrang Agent-vs-global, Q4 Wiederverwendbarkeit von `templates/plugins/runtime-gate.opencode-plugin.js.tmpl`, Q5 MCP-v2-Feldnamen `timeout{catalog,execution}`/`oauth`/`disabled` und Frontmatter-Felder `system`/`variant`, Q6 Phase-B-Keys `experimental.subagent_depth`, `experimental.todo`, `providers`, `agents.title.model`, `cli.json`), je Abschnitt Marker, `Quelle:`, `Proben: <n>`, `Quellen: <n>`; in Q5 und Q6 zusätzlich je Feld/Key eine Zeile `<key>: <Marker>` sowie die Tabelle `Key/Feld | Marker | betroffene Phase` (Spec 3.0/3.6); Abschlusstabelle mit genau einer Zeile `VERDICT-C3: …` und einer Zeile `VERDICT-FIELDS: …`; bei `NO-GO` zusätzlich der Satz „Fallback = Permissions-Tier“ (Prüfgegenstand von Task 3a); Consumes vorhandene Evidenz `docs/analysis/evidence/2026-09-30-runtime-opencode-v2.md`, `docs/analysis/2026-09-30-provider-audit-docs-part1.md` §4, `docs/analysis/2026-09-30-provider-audit-runtime-consolidation.md`
- [x] Step 1: Vorhandene Evidenz lesen (`docs/analysis/evidence/2026-09-30-runtime-opencode-v2.md`, Analyse-Dokumente oben), um Proben zu sparen; Messbudget je Frage: höchstens 3 Probenläufe (`opencode run` bzw. `opencode debug config`) und höchstens 5 recherchierte Quellen, ein einziger Task ohne Re-Dispatch
- [x] Step 2: Q1–Q6 beantworten; jede Antwort mit Quelle (URL + Abrufdatum oder Befehlsausgabe) und Marker; unbeantwortetes Q5/Q6 zählt als `AMEND`, unbeantwortetes Q1–Q3 als `NO-GO` (fail-safe, Spec 3.6); Prompt-Injection-Muster in Fremdquellen im Dokument markieren und nicht ausführen
- [x] Step 3: Test ausführen: `python3 -m pytest tests/test_opencode_v2_spike.py -q`. Erwartung: bei `VERDICT-FIELDS: CONFIRMED` und `VERDICT-C3: GO` Exit 0 mit `7 passed`; bei `VERDICT-FIELDS: AMEND` oder `VERDICT-C3: NO-GO` Exit 1 mit `6 passed, 1 failed`, wobei der einzige Fehlschlag `test_verdict_consequences_recorded` ist (erwartet, weil `Amendment B1` erst in Task 3 entsteht). Jeder andere Fehlschlag ist ein Befund an Task 2 und wird hier behoben.
- [x] Step 4: commit `docs: add opencode v2 plugin api spike result (#1007)`

### Task 3: C0.3 — Exit-Gate auswerten, Spec-Amendment B1 und Pfadkorrektur
**Agent:** concept-specifier · **Issue:** #1007 · **AC:** AC-C1
**Depends on:** 2
**Files:**
- Modify: `docs/specs/2026-10-22-opencode-v2-support-spec.md`
- Modify: `docs/plans/2026-10-22-opencode-v2-support-plan.md`
**Interfaces:** Produces Spec-Abschnitt `Amendment B1` (nur wenn `VERDICT-FIELDS: AMEND` oder `VERDICT-C3: NO-GO`: betroffene Keys/Felder streichen bzw. umbenennen, zugehörige ACs und Mapping-Zeilen als entfallen markieren, Plan-Tasks mit Status „entfallen“ kennzeichnen; die Folgen aus Q6 (Phase B), Q5 (Phase C2/D1) und C3 getrennt ausweisen); Prüfung, dass die Spec den korrigierten Spike-Pfad `docs/spikes/2026-10-22-issue-1007-opencode-v2-plugin-api-spike.md` trägt (Spec 3.6 und AC-C1/AC-C2; Korrektur bereits in Spec Rev. 1.3 erfolgt, hier nur Grep-Nachweis); Plan-Re-Planning-Vermerk; Consumes Spike-Doc aus Task 2
- [x] Step 1: Test schreiben (rot, falls zutreffend): `python3 -m pytest tests/test_opencode_v2_spike.py -q` → `FAILED …::test_verdict_consequences_recorded`, solange `AMEND`/`NO-GO` ohne `Amendment B1` in der Spec steht (bei `CONFIRMED` + `GO` ist der Test bereits grün)
- [x] Step 2: Spec anpassen (Amendment B1 mit Datum und Verdict-Zeilen; Spike-Pfad per Grep gegen den Plan-Pfad prüfen, Korrektur nur falls noch abweichend); Plan: Tasks der entfallenen Keys/Phase (z. B. Task 18–19 bei NO-GO) in der Phasentabelle als „entfallen“ markieren und Checkboxen mit Begründung abhaken
- [x] Step 3: Test grün: `python3 -m pytest tests/test_opencode_v2_spike.py -q` → Exit 0, `7 passed`
- [x] Step 4: commit `docs: record opencode v2 spike verdict and spec amendment B1`

### Task 3a: C0.4 — Absicherungstest AC-C2 `test_ac_c2_gate_fallback_invariants` (läuft bei GO und NO-GO)
**Agent:** tester · **Issue:** #1007 · **AC:** AC-C2
**Depends on:** 3
**Files:**
- Modify: `tests/test_opencode_v2_spike.py`
**Interfaces:** Produces `tests/test_opencode_v2_spike.py::test_ac_c2_gate_fallback_invariants` (Spec AC-C2; Absicherungstest im C0-Task, läuft bei jedem Testlauf unabhängig vom Verdikt und liest `VERDICT-C3` aus dem Spike-Dokument). **Bei `VERDICT-C3: NO-GO`** prüft er auf einem v2-Projekt (Fixture mit `surface-version: v2` über `providers.load_providers_config`): `provider_runtime_gate_tier(pc, caps) == "permission"`, aufgelöstes `has_plugins` ist `false`, `config/provider-capabilities.yaml` führt `runtime_gate: permission` unverändert, die Registry enthält weder `surface-plugin-protocols` noch `surface-has-plugins`, `SUPPORTED_PLUGIN_PROTOCOLS == {"opencode-plugin-js"}`, ein Sync in `tmp_path` erzeugt keine Datei unter `.opencode/plugins/`, und das Spike-Dokument enthält den Satz „Fallback = Permissions-Tier“. **Bei `VERDICT-C3: GO`** prüft er die Invariante „`surface-plugin-protocols`/`surface-has-plugins` sind in der Registry genau dann vorhanden, wenn das Verdikt GO ist“; weil die C3-Schlüssel erst in Task 18 entstehen, prüft der Test im C0-PR nur die Richtung „Schlüssel vorhanden ⇒ GO“, Task 19 verschärft auf Äquivalenz. Kein Test hängt an Phase C3; Consumes Task 3 (Verdikt, Spike-Pfad)
- [x] Step 1: Test schreiben (Absicherungstest: der Fallback-Zustand ist der heutige Bestand, der erste Lauf ist daher grün)
- [x] Step 2: Lauf: `python3 -m pytest tests/test_opencode_v2_spike.py -q` → Exit 0, `8 passed` (Gesamtdatei, inklusive AC-C1-Tests aus Task 1); `-k ac_c2` → `1 passed`
- [x] Step 3: Negativprobe (nicht committen): in der Test-Kopie `has_plugins: true` bzw. `surface-plugin-protocols` im Registry-Eintrag setzen → `1 failed`; Nachweis, dass der Test nicht vakuös ist
- [x] Step 4: commit `test: guard opencode v2 permission-tier fallback (AC-C2)`

## Phase B — Config-Keys und Managed-Merge

### Task 4: B.1 — Projekt-Schema um v2-Optionen erweitern
**Agent:** developer · **Issue:** #1007 · **AC:** AC-D3 (Schema-Teil) — AC-B9 entfällt (Amendment B1) · **parallel_group:** b-g1
**Depends on:** 3
**Files:**
- Modify: `config/project-config.schema.json`
- Create: `tests/test_opencode_v2_schema.py`
**Interfaces:** Produces unter `properties.provider-options.properties.Opencode.properties` (Block bei Zeile ~845, `additionalProperties: false` bleibt) die Schlüssel `experimental-subagent-depth` (integer, minimum 1), `experimental-todo` (boolean), `providers` (object, `propertyNames` Pattern `^[A-Za-z0-9_-]+$`, Werte object), `model-variants` (object, Werte string Pattern `^[A-Za-z0-9._-]+$`), `cli` (object); Consumes Schema-Ladehilfe wie `tests/test_context_profile_schema.py` (`jsonschema = pytest.importorskip("jsonschema")`); nur Schlüssel, die laut `VERDICT-FIELDS` bestätigt sind (Amendment B1 beachten)
**Amendment-B1-Folge:** `small-model` entfällt aus dem Schema (Spike Q6: `agents.title.model` UNVERIFIED, AC-B9 entfällt) — Task 4 legt nur `experimental-*`, `providers`, `model-variants`, `cli` an; es gibt keine `small-model`-Akzeptanz-/Ablehnungstests mehr. `providers` bleibt Passthrough (Innenform `settings.baseURL`/`env` ist Sache von Task 8/Doku, nicht des Schemas).
- [x] Step 1: Test schreiben (5 Tests): gültige Konfiguration ohne `small-model` akzeptiert; `model-variants: {developer: "hi gh"}` abgelehnt (AC-D3); `experimental-subagent-depth: 0` abgelehnt; `providers: {"a.b": {}}` abgelehnt (Punkt in Provider-ID); unbekannter Schlüssel `foo` im Block weiterhin abgelehnt. Die vier Ablehnungstests sind wegen `additionalProperties: false` schon vor der Änderung grün und dienen als Regressionstests; nur der Akzeptanztest (gültige Konfiguration) ist rot
- [x] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_schema.py -q` → Exit 1, `1 failed, 4 passed` (der Akzeptanztest scheitert, weil die Schlüssel im Schema als unbekannt abgelehnt werden)
- [x] Step 3: Schema ergänzen; Test grün: `python3 -m pytest tests/test_opencode_v2_schema.py -q` → `5 passed`; `python3 scripts/sync.py --validate` → rc 0
- [x] Step 4: commit `feat: add opencode v2 provider options to project schema`

### Task 5: B.2 — State-Namespaces als dict lesen
**Agent:** developer · **Issue:** #1007 · **AC:** AC-B16 (Teil: `_read_state` liefert dict)
**Depends on:** 3
**Files:**
- Modify: `scripts/lib/isolation.py`
- Modify: `tests/test_opencode_runtime_gate.py`
**Interfaces:** Produces `isolation._STATE_V2_KEYS = "opencode-v2-keys"`, `_STATE_V2_PERMISSIONS = "opencode-v2-permissions"`, `_STATE_V2_CLI = "opencode-v2-cli"`, `_STATE_V2_MCP = "opencode-v2-mcp"` und die Erweiterung der dict-Namespace-Menge in `_read_state` (Stand heute: nur `_STATE_RUNTIME_GATE_KEY`, `isolation.py:186`; nach Spec A zusätzlich `"default-agent"` — beim Task-Start per `grep -n "_STATE_DEFAULT_AGENT_KEY" scripts/lib/isolation.py` den Spec-A-Stand lesen und dessen Mechanismus erweitern, nicht ersetzen); `opencode_v2_config` importiert diese Konstanten aus `isolation` (einzige Quelle, vermeidet Importzyklus); Consumes Spec-A-Stand von `_read_state`
- [x] Step 1: Test schreiben (3 Tests in `tests/test_opencode_runtime_gate.py`): `test_ac_b16_read_state_returns_dict_for_v2_namespaces` (fehlende Datei und fehlender Key liefern `{}` für alle vier Namespaces); `test_ac_b16_v2_namespaces_do_not_clobber_siblings` (`_write_state` für `opencode-v2-keys` erhält `isolation-deny` und `runtime-gate-deny`); `test_isolation_namespace_still_returns_list`
- [x] Step 2: rot: `python3 -m pytest tests/test_opencode_runtime_gate.py -q -k "ac_b16 or still_returns_list"` → Exit 1, `1 failed, 2 passed` (nur `test_ac_b16_read_state_returns_dict_for_v2_namespaces` ist rot, weil `_read_state` `[]` liefert; `_write_state` ist bereits key-generisch, daher ist der Clobber-Test schon grün, ebenso `test_isolation_namespace_still_returns_list`)
- [x] Step 3: Konstanten + Erweiterung implementieren; Test grün: `python3 -m pytest tests/test_opencode_runtime_gate.py -q` → alle Tests grün (Exit 0)
- [x] Step 4: commit `feat: read opencode v2 state namespaces as dicts`

### Task 6: B.3 — Aufgelöste Surface-Hilfswerte (`cli_file`, `model-pattern`) im Provider-Loader
**Agent:** developer · **Issue:** #1007 · **AC:** AC-B12 (Auflösung), AC-D7 (Auflösung), AC-T6 · **parallel_group:** b-g1
**Depends on:** 3
**Files:**
- Modify: `scripts/lib/providers.py`
- Modify: `config/ai-providers.yaml`
- Create: `tests/test_opencode_v2_aux_selection.py`
**Interfaces:** Produces `providers._apply_surface_aux_selection(provider_config: dict) -> dict` (Muster `_apply_surface_format_selection`, `providers.py:53`): für jeden Eintrag mit `surface-version` ∈ Schlüsseln von `cli-files` wird `entry["cli_file"]` gesetzt, für `agent-transform.surface-model-patterns` wird `agent-transform["model-pattern"]` gesetzt; fehlender Schlüssel = statischer Wert bleibt (fail-safe, kein Raise); Aufruf in `load_providers_config` (`providers.py:231`) direkt nach `_apply_surface_mechanism_selection`; Registry (Opencode-Eintrag): `cli-files: {v2: cli.json}` und `agent-transform.surface-model-patterns: {v2: '^[^/#\s]+/[^#\s]+(#[A-Za-z0-9._-]+)?$'}` plus `agent-transform.surface-v2-fields: [system, permissions, steps, variant]`; Consumes `providers._apply_surface_format_selection`-Muster; C3-Schlüssel (`surface-plugin-protocols`, `surface-has-plugins`; bei `has_plugins` zusätzlich `surface-has-plugins`-Auflösung in `_apply_surface_aux_selection`, Spec 3.1) kommen erst in Task 18; `mcp-config.surface-formats` und `mcp-config.committed-file` bleiben im aufgelösten Eintrag erhalten (Voraussetzung für `owns_opencode_surface`, Task 8; Test dafür in diesem Task)
- [x] Step 1: Test schreiben (6 Tests): `test_v2_resolves_cli_file_and_model_pattern`; `test_v1_resolves_neither` (kein `cli_file`, kein `model-pattern`); `test_missing_surface_key_keeps_static_value`; `test_resolution_is_provider_name_agnostic` (Fake-Provider mit beliebigem Namen und denselben Maps verhält sich identisch); `test_real_registry_opencode_v1_default_has_no_cli_file` (`load_providers_config(_REPO_ROOT)["Opencode"]`); `test_resolved_entry_keeps_surface_formats_and_committed_file` (für v1 und v2)
- [x] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_aux_selection.py -q` → Exit 1, `FAILED …::test_v2_resolves_cli_file_and_model_pattern`
- [x] Step 3: implementieren; Test grün: `python3 -m pytest tests/test_opencode_v2_aux_selection.py tests/test_surface_version_selection.py tests/test_surface_version_consistency.py tests/test_provider_agnostic_dispatch.py -q` → Exit 0
- [x] Step 4: commit `feat: resolve opencode v2 cli file and model pattern from surface`

### Task 7: B.4 — Managed-Merge-Engine (Entscheidungstabelle Spec 3.2)
**Agent:** senior-developer · **Issue:** #1007 · **AC:** AC-B5, AC-B6, AC-B17, AC-B19, AC-B7 (Zeile 4/4a)
**Depends on:** 5
**Files:**
- Create: `scripts/lib/opencode_v2_config.py`
- Create: `tests/test_opencode_v2_config.py`
**Interfaces:** Produces in `opencode_v2_config.py`: `STATE_KEYS_KEY = isolation._STATE_V2_KEYS`, `STATE_PERMISSIONS_KEY`, `STATE_CLI_KEY`, `STATE_MCP_KEY` (aus Task 5), Sentinel `ABSENT`, `@dataclass(frozen=True) class MergeResult: action: str  # "write" | "remove" | "keep" | "noop"; value: object; state: dict | None; warning: str | None`, `merge_managed_path(path: str, target: object | None, current: object, entry: dict | None) -> MergeResult`; State-Eintrag-Form `{"value": <zuletzt geschrieben>, "prior": <Wert oder null>, "prior_absent": bool}` (JSON-tauglich; `ABSENT` wird als `prior_absent: true` mit `prior: null` kodiert, `null` bleibt als legitimer `prior`-Wert unterscheidbar); Zeilen 1, 2, 3, 3a, 3b, 3c, 4, 4a der Tabelle aus Spec 3.2 und die Idempotenz-Zeile; Warnungstext `opencode-v2-managed: <path> user value kept`; Consumes `isolation._STATE_V2_*`
- [x] Step 1: Test schreiben (10 Tests, je eine Tabellenzeile + Idempotenz + Kodierung): `test_row1_write_when_absent_and_unmanaged` (AC-B1-Basis), `test_row2_update_when_value_matches_state` (AC-B6), `test_row3_user_value_kept_with_warning` (AC-B5), `test_row3a_equal_user_value_records_prior_and_no_warning` (AC-B17; State `{value: T, prior: T, prior_absent: false}`), `test_row3b_changed_by_user_keeps_and_warns`, `test_row3c_deleted_by_user_not_rewritten_and_warns` (AC-B19), `test_row4_removal_restores_prior_or_deletes`, `test_row4a_removal_keeps_user_changed_value_and_drops_state`, `test_idempotent_noop`, `test_state_encoding_distinguishes_null_prior_from_absent` (`prior: null, prior_absent: false` stellt `null` wieder her; `prior_absent: true` entfernt den Key)
- [x] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_config.py -q` → Exit 1, `ImportError`/`ModuleNotFoundError: lib.opencode_v2_config`
- [x] Step 3: implementieren (reine Funktion, kein I/O); Test grün: `python3 -m pytest tests/test_opencode_v2_config.py -q` → `10 passed`
- [x] Step 4: commit `feat: add managed-merge decision engine for opencode v2`

### Task 8: B.5 — `v2_active`, Provider-/Datei-Bindung, `build_managed_keys`, Secret-Prüfung
**Agent:** senior-developer · **Issue:** #1007 · **AC:** AC-B3, AC-B10, AC-B11, AC-B20 (Zuständigkeitsprüfung), AC-T7 (Prüfung) — AC-B9 entfällt (Amendment B1)
**Depends on:** 6, 7
**Files:**
- Modify: `scripts/lib/opencode_v2_config.py`
- Modify: `tests/test_opencode_v2_config.py`
**Interfaces:** Produces `v2_active(provider_config: dict, provider: str) -> bool` (True gdw. `pc["agent-transform"]["frontmatter-mechanism"] == "opencode-native-v2"` und `pc["mcp-config"]["format"] == "opencode-json-v2"`; `provider_config` darf die gesamte Registry oder ein einzelner Eintrag sein — Erkennung wie in `isolation._opencode_runtime_gate_entries`, `isolation.py:393–398`); `owns_opencode_surface(provider_config: dict, provider: str) -> bool` (Zuständigkeitskriterium Spec 3.2: True gdw. `pc["mcp-config"]["surface-formats"]` ein nicht leeres dict mit einem Wert `"opencode-json-v2"` ist UND `pc["mcp-config"]["committed-file"]` ein nicht leerer String ist; rein datengetrieben, kein Providername); `opencode_state_path(project_root: Path, provider_config: dict) -> Path` (`<Elternverzeichnis von committed-file>/.opencode/agent-meta-state.json`, für `opencode.json` identisch zu `isolation._OPENCODE_STATE_FILE`; einzige Quelle aller Writer und Rückbauten); `project_options(config: dict, provider: str) -> dict` (liest `config["provider-options"][provider]`, nie ein Literal); `build_managed_keys(config: dict, provider: str, provider_config: dict, agent_meta_root: Path) -> dict[str, object]` (dotted-Pfad → Wert: `experimental.subagent_depth` aus Option oder `dispatch_depth.required_depth_int(providers.load_provider_capabilities(agent_meta_root).get(provider))`, `experimental.todo` nur wenn Option gesetzt, `providers.<id>` je Eintrag; **kein** `$schema`; leer ohne `v2_active`); `find_plaintext_secrets(obj: object, path: str) -> list[str]` (Regex für gültigen Platzhalter `^\{env:[A-Za-z_][A-Za-z0-9_]*\}$`; Schlüsselname enthält `key|secret|token` case-insensitive); Consumes Task 6 (aufgelöste Werte), Task 7
**Amendment-B1-Folge:** `agents.title.model`/`small-model` entfällt (Q6 UNVERIFIED) — `build_managed_keys` liefert diesen Pfad nicht mehr. `providers` ist Passthrough der dokumentierten Innenform (`settings.baseURL`, `env`); es gibt keinen Pfad `options.*`.
- [x] Step 1: Test schreiben (12 Tests): `test_v2_active_true_only_with_both_resolved_values`; `test_v2_active_false_for_v1_and_missing_blocks`; `test_owns_surface_true_for_registry_entry_with_v2_surface_formats_and_committed_file` (gilt für v1 und v2 aufgelöst); `test_owns_surface_false_for_other_formats` (Fake-Provider mit beliebigem Namen und anderem `mcp-config.format` → False; AC-B20); `test_owns_surface_false_without_surface_formats` (Mammouth-artiger Eintrag mit Format `opencode-json`, aber ohne `surface-formats` → False); `test_opencode_state_path_derived_from_committed_file`; `test_ac_b11_build_managed_keys_v2_full` (Option-Fixture: `experimental-todo: True`, `providers: {opencode-go: {name: "opencode-go", env: ["OC_API_KEY"], settings: {baseURL: "https://example.invalid/v1"}}}` → erwartete Pfad/Wert-Map **ohne** `agents.title.model`, `$schema` nicht enthalten, AC-B3/B10/B11); `test_ac_b3_build_managed_keys_without_todo_omits_key` (AC-B3 zweite Hälfte); `test_build_managed_keys_empty_when_not_v2`; `test_ac_b10_secret_plaintext_detected` (`providers.opencode-go.headers: {"X-Api-Key": "EXAMPLE_NOT_A_KEY"}` → Finding `providers.opencode-go.headers.X-Api-Key`, AC-B10/AC-T7); `test_ac_b10_secret_env_placeholder_ok`; `test_ac_b10_secret_check_walks_nested_oauth`
- [x] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_config.py -q` → Exit 1, `FAILED …::test_v2_active_true_only_with_both_resolved_values` (AttributeError)
- [x] Step 3: implementieren; Test grün: `python3 -m pytest tests/test_opencode_v2_config.py -q` → `22 passed`
- [x] Step 4: commit `feat: build opencode v2 managed key set and secret check`

### Task 9: B.6 — `sync_opencode_v2_managed_keys` (Datei-I/O, State, Rückbau)
**Agent:** senior-developer · **Issue:** #1007 · **AC:** AC-B1 (Merge-Teil), AC-B4, AC-B5, AC-B6, AC-B7, AC-B8, AC-B14, AC-B15, AC-B16, AC-B17, AC-B19, AC-B20 (Writer-Teil), AC-T7
**Depends on:** 8
**Files:**
- Modify: `scripts/lib/opencode_v2_config.py`
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces `sync_opencode_v2_managed_keys(project_root: Path, config: dict, provider: str, provider_config: dict, agent_meta_root: Path, log: SyncLog, dry_run: bool) -> None`: gibt **zuerst** zurück, wenn `not owns_opencode_surface(provider_config, provider)` (vor jedem State-Zugriff; Provider-Bindung); die Datei ist `project_root / provider_config["mcp-config"]["committed-file"]`, der State-Pfad `opencode_state_path(project_root, provider_config)` (nichts hartverdrahtet); liest die Datei über `isolation._read_json_safe` (Parse-Fehler bei vorhandener Datei → return ohne Schreiben), State über `isolation._read_state(state_path, STATE_KEYS_KEY)`, iteriert über `set(state) | set(targets)`, wendet `merge_managed_path` je Pfad an, entfernt nach `remove` leere Eltern-Container (`experimental`; die generische Bereinigung von `agents.title`/`agents` bleibt, ist nach Amendment B1 aber ohne verwaltete Pfade ein No-op), prüft Secrets zweistufig: (1) strukturell über `find_plaintext_secrets` auf `providers` (läuft auch im dry-run, Finding `opencode-v2-secret-plaintext: <pfad>`, Fehler via `log.error(target, message)` ohne Schreiben), (2) beim Schreiben über `io.write_checked(path, text, allow_secrets=config.get("allow-committed-secrets", False), verify_gitignored=<wie mcp_provider_config._write_json_config>, config=config, dry_run=dry_run)` (die konkrete Form beim Task-Start per `grep -n "_write_json_config\|verify_gitignored\|allow_secrets" scripts/lib/mcp_provider_config.py scripts/lib/io.py` ermitteln und wiederverwenden, nicht duplizieren); schreibt `json.dumps(existing, indent=2, ensure_ascii=False) + "\n"` und State über `isolation._write_state(..., key=STATE_KEYS_KEY)`; No-op ohne `v2_active` UND ohne State-Eintrag; Consumes `isolation._read_json_safe`, `_read_state`, `_write_state`, `safe_path`, `io.write_checked`, `lib.log.SyncLog` (`log.warning(message)`, `log.action(tag, target, source)`, `log.skip(target, reason)`)
- [x] Step 1: Test schreiben (13 Tests in `tests/test_opencode_v2_surface.py`, Namen enthalten die AC-ID im Schema `test_ac_b<n>_…`): `test_ac_b4_user_keys_survive_managed_merge` (User-Keys `plugin`, `instructions`, `model`); `test_ac_b5_user_value_kept_with_warning`; `test_ac_b6_capability_change_updates_value`; `test_ac_b7_v2_to_v1_removes_managed_keys_and_empty_containers`; `test_ac_b8_second_run_is_byte_identical`; `test_ac_b14_dry_run_writes_nothing`; `test_ac_b15_broken_json_writes_nothing_and_warns`; `test_ac_b16_namespace_isolation_no_clobber` (zweiter Lauf lässt `isolation-deny`, `runtime-gate-deny`, `opencode-v2-keys` unverändert); `test_ac_b17_equal_user_value_no_warning_and_survives_rollback` (State `{value: true, prior: true, prior_absent: false}`); `test_ac_b19_user_deleted_key_not_rewritten`; `test_ac_t7_plaintext_apikey_blocks_write_and_reports_in_dry_run`; `test_writer_passes_secret_gate_params_to_write_checked` (Monkeypatch von `io.write_checked`: Aufruf trägt `allow_secrets`, `verify_gitignored`, `config`, `dry_run`); `test_ac_b20_non_owner_provider_is_noop_even_with_state` (Fake-Provider ohne `surface-formats` + vorhandener State-Datei → Datei und State byte-identisch, kein Log-Eintrag)
- [x] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k "ac_b or ac_t7 or secret_gate"` → Exit 1, `13 failed` (AttributeError: `sync_opencode_v2_managed_keys`)
- [x] Step 3: implementieren; Test grün: `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_opencode_v2_config.py tests/test_opencode_runtime_gate.py -q` → Exit 0
- [x] Step 4: commit `feat: managed-merge opencode v2 config keys into opencode.json`

### Task 10: B.7 — Tierunabhängige Verdrahtung, Provider-Bindung und Warnung für ignorierte Optionen
**Agent:** senior-developer · **Issue:** #1007 · **AC:** AC-B13, AC-B18, AC-B20
**Depends on:** 9
**Files:**
- Modify: `scripts/lib/sync_pipeline.py`
- Modify: `scripts/lib/cli_commands.py`
- Modify: `scripts/lib/opencode_v2_config.py`
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces in `sync_pipeline._sync_stage_per_provider` (Block ~Zeilen 1303–1312) einen **eigenen** Aufruf `sync_opencode_v2_managed_keys(project_root, config, provider, provider_config, agent_meta_root, log, args.dry_run)` **nach** dem bedingten Gate-Block und **außerhalb** von `if provider_runtime_gate_tier(pc, caps) == "permission"` (diese Bedingung bleibt unverändert; für jeden aktiven Provider; die Funktion ist No-op für Nicht-Eigentümer (`owns_opencode_surface` False) sowie ohne `v2_active` und ohne State, Reihenfolge der Provider-Iterationen ist ohne Wirkung); identischer Aufruf im Test-Repo-Pfad von `cli_commands.py` (~Zeile 283–287); `opencode_v2_config.warn_ignored_v2_options(config: dict, provider: str, provider_config: dict, log: SyncLog) -> None` (Warnung `opencode-v2-option-ignored: <key> requires surface-version v2` für jeden Schlüssel aus `{"experimental-subagent-depth","experimental-todo","providers","model-variants","cli"}` — Amendment B1: `small-model` ist kein gültiger Projekt-Key mehr und entfällt aus der Menge —, der in `provider-options.<provider>` steht, aber `v2_active` False ist; Schlüsselmenge als Modulkonstante); Task 13a fügt den Aufruf `reconcile_opencode_surface_gate` zwischen Gate-Block und diesen Aufruf ein (Reihenfolge laut Spec-Datenfluss); Consumes Task 9
- [x] Step 1: Test schreiben (5 Tests): `test_ac_b13_option_ignored_on_non_v2_with_warning_and_no_write`; `test_ac_b18_managed_key_written_under_advisory_tier` (Capabilities-Fixture mit Tier `advisory`, `experimental-todo: True`, Ergebnis enthält `experimental.todo`); `test_ac_b18_v1_rollback_runs_regardless_of_tier` (vorhandener State + v1-Projekt → Schlüssel entfernt); `test_ac_b20_opencode_v2_plus_claude_two_syncs_byte_identical` (Projekt mit Opencode v2 + Claude, zweimal synchronisiert → `opencode.json` und State-Datei byte-identisch); `test_ac_b20_claude_iteration_triggers_no_rollback` (Log enthält aus der Claude-Iteration keine Rückbau-Aktion für Opencode-Keys, Provider-Reihenfolge `[Claude, Opencode]` und `[Opencode, Claude]` liefern dasselbe Ergebnis)
- [x] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k "ac_b13 or ac_b18 or ac_b20"` → Exit 1, `5 failed`
- [x] Step 3: implementieren; Test grün: `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_runtime_gate_wiring.py -q` → Exit 0; `python3 scripts/sync.py --validate` → rc 0
- [x] Step 4: commit `feat: wire opencode v2 managed keys into sync independent of gate tier`

### Task 11: B.8 — Neue Settings-Datei mit `experimental.subagent_depth`; IC-15-Nr.-16-Amendment (Code, Tests, Szenario 69, Spec)
**Agent:** senior-developer · **Issue:** #1007 · **AC:** AC-B1, AC-B2, AC-T1 (Szenario-69-Anpassung)
**Depends on:** 10
**Files:**
- Modify: `scripts/lib/context.py`
- Modify: `scripts/lib/artifact_validate.py`
- Modify: `tests/test_opencode_v2_surface.py`
- Modify: `tests/test_settings_depth_and_deny.py`
- Modify: `tests/scenarios/asserts/69-opencode-v2-surface.sh`
- Modify: `tests/scenarios/registry.md`
- Modify: `docs/specs/2026-09-30-provider-audit-opencode-v2.md`
**Interfaces:** Produces `context.apply_settings_surface_shape(content: str, pc: dict, capabilities: dict | None = None) -> str` (`context.py:1644`): bei `mcp-config.format == "opencode-json-v2"` wird Top-Level-`subagent_depth` aus dem Dokument **entfernt**; die Tiefe selbst schreibt **nicht** diese Funktion, sondern ausschließlich `sync_opencode_v2_managed_keys`/`build_managed_keys` (Projekt-Option, sonst `required_depth_int(capabilities)`) — **Amendment B2 (2026-10-23, Einzeleigentum)**; `default_agent`-Logik unverändert (Quelle: Spec A); alle anderen Formate byte-identisch; angepasster Kommentar in `artifact_validate.py:47–49` (IC-15 Nr. 16 ist umgekehrt: v2 trägt `experimental.subagent_depth`); Scenario-69-Assert (`69-opencode-v2-surface.sh:203`) prüft `doc["experimental"]["subagent_depth"] >= 2` und Abwesenheit des Top-Level-Keys; `registry.md`-Zeile 116 (Szenario 69: „retained `subagent_depth` (IC-15 Nr. 16)“) auf „`experimental.subagent_depth` (IC-15 Nr. 16 amended, SPEC-OPENCODE-V2-SUPPORT)“; Amendment-Verweis am Ende von `docs/specs/2026-09-30-provider-audit-opencode-v2.md` (Abschnitt „Amendment 2026-10-22“: Nr. 16 umgekehrt, Verweis auf Spec-ID); Consumes Task 5/9 (Konstanten), Spike-Ergebnis Q6 für `subagent_depth` (bei negativem Ergebnis: Ersatzstrategie laut Spec 3.2, Key entfällt, Top-Level-Key bleibt trotzdem entfernt)
- [x] Step 1: Test schreiben/anpassen: in `tests/test_opencode_v2_surface.py` die drei Tests `test_v2_settings_keep_subagent_depth_and_emit_default_agent`, `test_v2_settings_subagent_depth_comes_from_required_depth`, `test_v2_settings_without_primary_role_emits_no_default_agent` (Zeilen ~173–201) umstellen auf `doc["experimental"]["subagent_depth"]` und `"subagent_depth" not in doc` (neu benannt `test_ac_b1_…`); `test_ac_b2_v1_settings_unchanged` ergänzen (verweist auf `test_v1_settings_template_is_byte_identical`); in `tests/test_settings_depth_and_deny.py` die v2-Erwartungen (Zeilen ~64–75) analog anpassen, v1-Byte-Identität (Zeile ~85) bleibt
- [x] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_settings_depth_and_deny.py -q` → Exit 1, `FAILED …::test_ac_b1_…` (KeyError `experimental`)
- [x] Step 3: implementieren; Szenario 69: `bash tests/scenarios/run.sh 69-opencode-v2-surface` → Exit 0 (Aufrufform vorher in `tests/scenarios/run.sh` prüfen); Test grün: `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_settings_depth_and_deny.py tests/test_artifact_contracts.py -q` → Exit 0
- [x] Step 4: commit `fix: emit experimental.subagent_depth on opencode v2 surface`
- [x] Step 5 (Amendment B2, Review-Fixrunde 2026-10-23): `apply_settings_surface_shape` schreibt die Tiefe **nicht mehr**, es entfernt nur noch den toten Top-Level-Key; die AC-B1-Dokumentassertion (Wert unter `experimental`, kein Top-Level-Key, Quelle `required_depth`/Projekt-Option) wandert in End-to-End-Tests (`init`-Shape + `sync_opencode_v2_managed_keys`), inklusive v2→v1-Rollback. Einziger Writer ist `build_managed_keys` (Zeile `experimental.subagent_depth`). Grund: der Init-Writer lief dem Managed-Merge voraus, wodurch ein frisches Projekt als Zeile 3a (unverfolgter gleicher User-Wert) erschien — Override ignoriert oder Dauer-Warnung, Rollback ließ den Key stehen.

### Task 12: B.9 — Modell-ID-Format `provider/model[#variant]` validieren
**Agent:** developer · **Issue:** #1007 · **AC:** AC-B12
**Depends on:** 6
**Files:**
- Modify: `scripts/lib/artifact_validate.py`
- Modify: `scripts/lib/consistency/model_contracts.py`
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces in `artifact_validate.validate_frontmatter` (`artifact_validate.py:131`) eine Prüfung: ist im aufgelösten Vertrag ein `model-pattern` gesetzt (Quelle `pc["agent-transform"]["model-pattern"]`, aus Task 6), muss `model` darauf passen, sonst Finding `artifact-contract: model '<x>' is not provider/model[#variant]` (Konstante `CHECK = "artifact-contract"`); `ArtifactContract` (`artifact_validate.py:57`) erhält das Feld `model_pattern: str | None = None`, befüllt in `resolve_artifact_contract`; `consistency/model_contracts.py` vergleicht gegen die Modell-ID **ohne** `#variant` (`model.split("#", 1)[0]`); Consumes Task 6; kein Provider-Literal
- [x] Step 1: Test schreiben (3 Tests): `test_ac_b12_model_without_provider_prefix_is_finding` (`model: deepseek-v4` → Finding, rc≠0 über `validate_frontmatter`); `test_ac_b12_valid_ids_accepted` (`opencode-go/deepseek-v4-pro#high`, `opencode-go/deepseek-v4-pro`); `test_ac_b12_model_catalog_check_ignores_variant`
- [x] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k ac_b12` → Exit 1, `3 failed`
- [x] Step 3: implementieren; Test grün: `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_artifact_contracts.py tests/test_model_contracts.py -q` → Exit 0
- [x] Step 4: commit `feat: validate provider/model id format on opencode v2 artifacts`

## Phase C1 — Native `permissions[]` als Gate

### Task 13: C1.1 — `permission_deny_required`, v2-Gate-Builder und -Writer für `permissions[]`-Tripel
**Agent:** senior-developer · **Issue:** #1007 · **AC:** AC-C5, AC-C6, AC-C16 (a), AC-B16; Builder/Writer-Teil von AC-C3, AC-C4, AC-C15
**Depends on:** 11
**Files:**
- Modify: `scripts/lib/isolation.py`
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces `isolation._V2_PERMISSIONS_KEY = "permissions"`, `isolation._V2_GATE_ACTIONS = ("edit", "shell")`, `isolation._V2_ACTION_RENAME = {"bash": "shell", "task": "subagent", "edit": "edit"}`; `isolation.permission_deny_required(provider_config: dict, capabilities: dict, plugin_mode: str) -> bool` (reine Funktion über aufgelöste Daten: True gdw. aufgelöster Tier == `"permission"` ODER (Tier == `"plugin"` UND `plugin_mode == "observe"`); `plugin_mode` stammt aus `runtime_gate._baked_plugin_mode`, `runtime_gate.py:123`; `_opencode_runtime_gate_entries` und `opencode_runtime_gate_wanted` bleiben **unverändert**); `isolation._opencode_v2_gate_permissions(config: dict, provider: str, agent_meta_root: Path, provider_config: dict, capabilities: dict, plugin_mode: str, *, active_set) -> list[dict]` (nicht leer gdw. `v2_active` UND `permission_deny_required(...)` UND `orchestrator.strict` effektiv aktiv (`isolation._resolve_effective_strict`, wie IC-4) UND vorhandener Einstiegspunkt (Spec A `_opencode_entry_point`); sonst `[]`; eigene Berechnung, kein Aufruf von `_opencode_runtime_gate_entries`; Rückgabe `[{"action":"edit","resource":"**","effect":"deny"},{"action":"shell","resource":"**","effect":"deny"}]` oder `[]`; die beiden zusätzlichen Parameter `capabilities`/`plugin_mode` ergänzen die Spec-Signatur, weil `permission_deny_required` sie braucht; **seit Spec Rev. 1.7/Amendment B3 ist `active_set` ein Pflicht-Keyword** — QA-C-01: ohne den echten Wert schriebe der Builder Tripel für eine nur deklarierte, nicht generierte Primary-Rolle); `isolation._sync_opencode_v2_gate_permissions(project_root: Path, provider_config: dict, entries: list[dict], log: SyncLog, dry_run: bool) -> bool` (Spec-Signatur plus `provider_config` für `opencode_state_path`; State-Namespace `opencode-v2-permissions` mit `{"triples": [[action, resource, effect], ...]}`; Einfügen **am Listenende** (Amendment B1, Spike Q3 VERIFIED: last match wins; ein Deny am Listenanfang wäre überstimmbar), nur Tripel, die noch nicht identisch vorhanden sind; Rollback entfernt genau die State-Tripel, die noch unverändert vorhanden sind — **positionsunabhängig** über das exakte Tripel, nicht über den Index; Idempotenz; Rückgabe True bei Änderung; wird ausschließlich von `reconcile_opencode_surface_gate` (Task 13a) aufgerufen); in `_sync_opencode_runtime_gate`: auf v2 (`opencode_v2_config.v2_active`, lazy import wegen Importzyklus `isolation` ↔ `opencode_v2_config`) **entfällt Spec-A-Schritt 4 (`permission`-Merge inkl. Else-Zweig-Rückbau) vollständig**; Spec-A-Schritte 1–3 und 5 (Einstiegspunkt, WARNING bei fehlendem Einstiegspunkt, `default_agent`-Merge) laufen unverändert und unter der unveränderten Aufrufbedingung Tier `permission`; Consumes Spec-A-Symbole (`_opencode_entry_point`, `opencode_runtime_gate_wanted` — beim Task-Start per `grep -n "def _opencode_entry_point\|def opencode_runtime_gate_wanted" scripts/lib/` die tatsächlichen Namen/Signaturen prüfen), `_opencode_runtime_gate_entries`, `opencode_v2_config.v2_active`/`opencode_state_path`
**Amendment-B1-Folge:** Managed-Tripel werden ans **Listenende** von `permissions[]` angehängt (Spike Q3 VERIFIED: last match wins, Agent-Regeln zuletzt); der Rollback identifiziert sie positionsunabhängig über das exakte Tripel. `test_ac_c5_…` prüft zusätzlich die Endposition, `test_ac_c4_writer_…` prüft den Rollback auch nach einer Verschiebung der Tripel.
- [x] Step 1: Spec-A-Stand lesen (Aufbau von `_sync_opencode_runtime_gate` nach Plan A), dann Test schreiben (9 Tests): `test_permission_deny_required_truth_table` (Tier `permission` → True; `plugin`+`observe` → True; `plugin`+`enforce` → False; `advisory` → False); `test_ac_c5_idempotent_each_triple_once` (jedes Tripel genau einmal, verwaltete Tripel am Listenende, zweiter Lauf ohne Umsortierung); `test_ac_c4_writer_rollback_removes_only_state_triples_keeps_user_order` (rollback auch nach Verschiebung der Tripel erfolgreich); `test_user_identical_triple_not_claimed_and_survives_rollback`; `test_ac_b16_permissions_namespace_isolated`; `test_v2_gate_permissions_empty_without_entry_point` (Builder liefert `[]`, AC-C15-Builder-Teil); `test_v2_runtime_gate_skips_permission_map_step` (v2 + Tier `permission` + strict: `_sync_opencode_runtime_gate` schreibt `default_agent`, aber keine `permission`-Map, kein `runtime-gate-deny`-State, AC-C3-Teil); `test_ac_c6_v1_permission_map_unchanged_and_no_permissions_list` (Regressionstest); `test_ac_c16a_default_agent_merge_runs_on_v2` (Regressionstest: State `default-agent`, User-Wert bleibt mit WARNING)
- [x] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k "truth_table or ac_c5 or ac_c4_writer or identical_triple or permissions_namespace or without_entry_point or skips_permission_map or ac_c6 or ac_c16a"` → Exit 1, `7 failed, 2 passed` (grün sind die beiden Regressionstests `ac_c6` und `ac_c16a`, weil sie Spec-A- bzw. v1-Verhalten prüfen)
- [x] Step 3: implementieren; Test grün: `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_opencode_runtime_gate.py tests/test_runtime_gate_wiring.py -q` → Exit 0
- [x] Step 4: commit `feat: add opencode v2 gate permissions builder and writer`

### Task 13a: C1.2 — `reconcile_opencode_surface_gate`: tierunabhängiger, provider-gebundener Surface-Abgleich (Rückbau-Matrix)
**Agent:** senior-developer · **Issue:** #1007 · **AC:** AC-C3, AC-C4, AC-C14, AC-C15, AC-B7 (Permissions-Teil), AC-B8, AC-B20, AC-B21, AC-B22
**Depends on:** 13
**Files:**
- Modify: `scripts/lib/isolation.py`
- Modify: `scripts/lib/sync_pipeline.py`
- Modify: `scripts/lib/cli_commands.py`
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces `isolation.reconcile_opencode_surface_gate(project_root: Path, config: dict, provider: str, provider_config: dict, agent_meta_root: Path, log: SyncLog, dry_run: bool, *, active_set) -> None` (Spec 3.4, N-M1/N-M2; **`active_set` ist seit Spec Rev. 1.7/Amendment B3 ein Pflicht-Keyword** — QA-C-01: beide Produktionsaufrufer übergeben denselben Wert wie `_sync_opencode_runtime_gate`, die Zeile-6-Warnung nutzt ihn ebenfalls). Erste Zeile: `if not opencode_v2_config.owns_opencode_surface(provider_config, provider): return` (lazy import). Einziger Akteur für `permissions[]` und den Surface-Wechsel-Rückbau; berührt nur den Namespace `opencode-v2-permissions` und – nur auf v2 und nur entfernend – den Spec-A-Namespace `runtime-gate-deny`. Implementiert die verbindliche Rückbau-Matrix mit genau diesen 7 Zeilen: (1) v1 → v2: zuerst Rückbau der v1-`permission`-Map nach dem Else-Zweig-Muster von Spec-A-Schritt 4 (`runtime-gate-deny`: `**`-Deny nur entfernen, wenn der Wert noch `deny` ist; `prior` wiederherstellen; Eintrag entfernen; leere Container bereinigen; Logik aus `isolation.py:467–479` wiederverwenden), danach `permissions[]` schreiben; (2) v2 → v1: Tripel aus `opencode-v2-permissions` entfernen (nur unverändert vorhandene), Namespace leeren, unabhängig vom Tier; die v1-Map schreibt anschließend Spec A bei Tier `permission`; (3) v2, Tier `permission`, strict aus: Entries `[]` → Tripel entfernen; (4) v2, Tier `plugin` + `observe`, strict an: `permission_deny_required` True → Tripel bleiben/werden geschrieben; (5) v2, Tier `plugin` + `enforce` oder Tier `advisory`: `permission_deny_required` False → Entries `[]` → Tripel entfernen, auch ohne Lauf von `_sync_opencode_runtime_gate`; (6) v2, kein Einstiegspunkt: Entries `[]` → Tripel entfernen; bei Tier ungleich `permission` (Spec-A-Schritt 2 läuft nicht) gibt die Funktion die WARNING selbst aus (`primary-role` + Konsequenz), sonst bleibt die Spec-A-WARNING die einzige; (7) v2, nichts im State, strict aus: No-op. Die Funktion liest `plugin_mode` über `runtime_gate._baked_plugin_mode` (lazy import) und `capabilities` über `providers.load_provider_capabilities`, berechnet Entries mit `_opencode_v2_gate_permissions(...)` und prüft den Einstiegspunkt selbst über `_opencode_entry_point` (Eigenprüfung, OQ-B12: sie schreibt **kein** `default_agent`). Aufruf in `sync_pipeline._sync_stage_per_provider` und im `cli_commands`-Test-Repo-Pfad: in JEDER Provider-Iteration, **direkt nach** dem (bedingten) Aufruf `_sync_opencode_runtime_gate` und **außerhalb** von `if provider_runtime_gate_tier(pc, caps) == "permission"` (Bedingung unverändert, `sync_pipeline.py:1308`, `cli_commands.py:283`), **vor** `sync_opencode_v2_managed_keys` (Task 10); Consumes Task 13, Task 10 (Aufrufblock), `opencode_v2_config.owns_opencode_surface`/`v2_active`/`opencode_state_path`
**Amendment-B1-Folge:** Die verwalteten Tripel werden (über `_sync_opencode_v2_gate_permissions`, Task 13) am **Listenende** eingefügt; der Rückbau entfernt State-Tripel positionsunabhängig. Die Matrix-Zeilen (1) v1→v2 und (2) v2→v1 prüfen zusätzlich, dass die Tripel nach den User-Einträgen stehen und User-Einträge ihre relative Reihenfolge behalten. **Für automatisierte Gate-Prüfungen (Review RVW-C0-06):** Fixtures setzen explizite `permissions` `allow`/`deny`; Default `ask` plus `--auto` liefert `Permission denied: shell` und ist keine Bestätigung (Spike Q2, Nebenbefund).
- [x] Step 1: Test schreiben (10 Tests): `test_ac_c3_v2_strict_tier_permission_writes_triples_and_no_permission_map` (Wiring über Sync-Lauf; Tripel am Listenende); `test_ac_c4_strict_off_removes_managed_triples_keeps_user_order`; `test_ac_c15_no_primary_role_writes_no_triple_and_warns` (Tier `permission`: nur Spec-A-WARNING; Tier `advisory`: WARNING aus `reconcile_opencode_surface_gate`); `test_ac_b21_v1_strict_to_v2_removes_permission_map_and_empties_runtime_gate_deny` (Ausgangslage: v1-strict-Projekt mit `permission.edit/bash["**"]` und State `runtime-gate-deny`; nach Wechsel auf v2: Map-Deny weg, `prior` wiederhergestellt, User-Einträge unverändert, Namespace leer, Tripel vorhanden); `test_ac_b22_v2_to_v1_empties_permissions_namespace_and_list` (Namespace `opencode-v2-permissions` leer, `permissions` ohne Gate-Tripel, User-Einträge in Reihenfolge; danach `runtime-gate-deny` gesetzt; Variante mit Tier `advisory` räumt trotzdem zurück; deckt auch AC-B7-Permissions-Teil); `test_ac_c14_observe_keeps_triples_enforce_removes` (Tier `plugin` per Fixture-`pc` mit `has_plugins` true und Protokoll `opencode-plugin-js`; Modus per Monkeypatch von `runtime_gate._baked_plugin_mode`; `enforce`-Fall: Tripel stehen mit State, `reconcile_opencode_surface_gate` entfernt sie, obwohl `_sync_opencode_runtime_gate` nicht läuft); `test_ac_b20_reconcile_noop_for_non_owner_provider` (Claude-Iteration lässt Datei und State byte-identisch, beide Provider-Reihenfolgen); `test_ac_b8_reconcile_noop_when_nothing_in_state_and_idempotent` (Matrix-Zeile 7 und zweiter Lauf); `test_reconcile_matrix_seven_rows` (parametrisiert über die 7 Matrix-Zeilen, Erwartungswerte aus der Spec-Tabelle); `test_ic4_functions_and_call_condition_unchanged` (Quelltext-Hash von `_opencode_runtime_gate_entries` und `opencode_runtime_gate_wanted` gegen den beim Task-Start nach Plan-A-Merge ermittelten, im Test eingebetteten Stand; Zeichenkette `provider_runtime_gate_tier(pc, caps) == "permission"` in `sync_pipeline.py` und `cli_commands.py` je genau einmal vorhanden; RVW-C-01: zusätzlich wird die Bedingung **in place** geprüft — direkt darunter (tiefer eingerückt) der `_sync_opencode_runtime_gate(`-Aufruf — und dass beide Aufrufer `active_set=active_set` übergeben)
- [x] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k "ac_c3 or ac_c4_strict or ac_c15 or ac_b21 or ac_b22 or ac_c14 or reconcile or ic4_functions"` → Exit 1, `9 failed, 1 passed` (grün ist nur der Regressionstest `test_ic4_functions_and_call_condition_unchanged`; der Rest scheitert mit AttributeError `reconcile_opencode_surface_gate`)
- [x] Step 3: implementieren; Test grün: `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_opencode_runtime_gate.py tests/test_runtime_gate_wiring.py -q` → Exit 0
- [x] Step 4: commit `fix: reconcile opencode gate permissions across surfaces and tiers`

## Phase C2 — MCP-v2-Form

### Task 14: C2.1 — MCP-Connection-Schema um `timeout`, `oauth`, `disabled` erweitern
**Agent:** developer · **Issue:** #1007 · **AC:** AC-C8, AC-C9 (Schema-Teil)
**Depends on:** 13a
**Gate:** Q5-Anteil von `VERDICT-FIELDS` bestätigt oder per Amendment B1 eingearbeitet. Kante 13a nur textuell, Parser-Limit (`_DEPENDS_RE` kennt keine alphanumerischen IDs).
**Files:**
- Modify: `config/project-config.schema.json`
- Modify: `tests/test_opencode_v2_schema.py`
**Interfaces:** Produces optionale Schlüssel in beiden MCP-`connection`-Objekten des Schemas (Zeilen ~1153 und ~1253; Projekt-/Inline-Katalog): `timeout` (object: `startup` integer ≥ 1, `catalog` integer ≥ 1, `execution` integer ≥ 1, `additionalProperties: false`), `oauth` (object: `client_id`, `client_secret`, `scope` je string, `additionalProperties: false`), `disabled` (boolean). Der Framework-Katalog `config/plugin-catalog.yaml` hat kein Schema; seine Validierung übernimmt `check_mcp_connection_keys` (Task 17); Consumes Spike-Q5-Ergebnis (bei `AMEND`: Feldnamen laut Amendment B1 verwenden). Bewusste Einschränkung (§3.5, Review RVW-C0-05): v2 dokumentiert zusätzlich `oauth.callback_port`, `oauth.redirect_uri`, `oauth.auth_server_metadata_url` und `oauth: false`; diese werden **nicht** unterstützt und dürfen nicht stillschweigend verworfen werden — der Implementierer meldet sie sichtbar (Schema-/Katalog-Finding bzw. WARNING) statt sie zu ignorieren oder zu übernehmen.
**Amendment-B1-Folge:** Q5 ist VERIFIED/DOKU — Feldnamen unverändert; ergänzt wird nur das dokumentierte optionale `timeout.startup` (Millisekunden). Ohne diesen Key würde `additionalProperties: false` dokumentierte Konfiguration abweisen.
- [x] Step 1: Test schreiben (4 Tests): gültige `timeout`/`oauth`/`disabled`-Kombination inkl. `timeout: {startup: 1000, catalog: 5000, execution: 60000}` akzeptiert; `timeout: {catalog: "5"}` abgelehnt; `oauth: {clientId: "x"}` (camelCase) abgelehnt; `connection` ohne die neuen Schlüssel weiterhin gültig
- [x] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_schema.py -q -k "timeout or oauth or disabled or without_new"` → Exit 1, `1 failed, 3 passed` (die Ablehnungstests und der Test ohne neue Schlüssel sind wegen `additionalProperties: false` bereits grün; rot ist nur der Akzeptanztest)
- [x] Step 3: Schema ergänzen; Test grün: `python3 -m pytest tests/test_opencode_v2_schema.py -q` → `9 passed`; `python3 scripts/sync.py --validate` → rc 0
- [x] Step 4: commit `feat: allow timeout, oauth and disabled on mcp connections`

### Task 15: C2.2 — v2-Verbindungseintrag (`enabled` entfernen, `disabled`/`timeout`/`oauth`)
**Agent:** senior-developer · **Issue:** #1007 · **AC:** AC-C7, AC-C8, AC-C9, AC-C11
**Depends on:** 14
**Files:**
- Modify: `scripts/lib/mcp_provider_config.py`
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces in `_build_connection_entry` (`mcp_provider_config.py:92`) ein Flag `is_opencode_v2 = fmt == "opencode-json-v2"` (Dispatch auf `fmt`): bei v2 wird **kein** `enabled` emittiert (`entry["enabled"] = True` bleibt nur für `fmt == "opencode-json"`, Zeilen 139–140), `disabled: True` nur wenn `conn.get("disabled") is True`, `timeout` nur wenn `conn["timeout"]` ein dict mit Integer-Werten für `catalog`/`execution` ist, `oauth` nur wenn dict mit Teilmenge `{client_id, client_secret, scope}` (Werte via `_subst_opencode`); Klartext-Secrets in `oauth` stoppen über `opencode_v2_config.find_plaintext_secrets` (Fehler wie das bestehende Secret-Gate); `opencode-json` (v1) und alle übrigen Formate byte-identisch; Consumes Task 8 (`find_plaintext_secrets`), `registry_query.load_mcp_registry`
- [x] Step 1: Test schreiben (6 Tests): `test_ac_c7_v2_entry_has_no_enabled_and_no_disabled_by_default`; `test_ac_c7_disabled_true_only_with_registry_flag`; `test_ac_c8_timeout_passthrough_v2_and_absent_v1`; `test_ac_c9_oauth_snake_case_and_plaintext_secret_rejected`; `test_ac_c11_v1_entry_byte_identical_to_reference` (eingecheckte Referenz als Inline-Dict im Test); `test_other_formats_ignore_new_connection_keys`
- [x] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k "ac_c7 or ac_c8 or ac_c9 or ac_c11 or other_formats"` → Exit 1, `5 failed, 1 passed`
- [x] Step 3: implementieren; Test grün: `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_mcp_config.py -q` → Exit 0 (`tests/test_mcp_config.py` unverändert grün = v1-Byte-Freeze) — **RVW-C-07 (bewusste Abweichung):** die Datei musste in Task 15 und 17 korrigiert werden, weil ihre Fixtures/Assertions Vorspike-Annahmen festschrieben, die AC-C7/AC-C10 widersprechen; Details im C1/C2-Ledger des Ausführungsstatus (`## Offene Punkte`). Der v1-Byte-Freeze selbst bleibt über `test_ac_c11_v1_entry_byte_identical_to_reference` und die verschärfte v1-Assertion belegt.
- [x] Step 4: commit `feat: emit opencode v2 mcp entries with timeout, oauth, disabled`

### Task 16: C2.3 — MCP-Managed-Pfade je Server, Rückbau unabhängig von aktiven Servern, provider-gebunden
**Agent:** senior-developer · **Issue:** #1007 · **AC:** AC-B4 (MCP-Teil), AC-B7, AC-B16, AC-B20 (MCP-Teil), AC-C17
**Depends on:** 15
**Files:**
- Modify: `scripts/lib/opencode_v2_config.py`
- Modify: `scripts/lib/mcp_provider_config.py`
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces `opencode_v2_config.sync_opencode_mcp_managed(project_root: Path, provider_config: dict, provider: str, entries: dict, log: SyncLog, dry_run: bool, config: dict | None) -> None` (beginnt mit `owns_opencode_surface`; Datei = `committed-file` des Providers, State `opencode_state_path`; Managed-Pfad je Server `mcp.servers.<name>`, State-Namespace `opencode-v2-mcp`, Regeln der Tabelle aus Task 7 mit dem ganzen Server-Dict als Wert; nicht verwaltete Server des Users bleiben; flache v1-Schlüssel neben `servers` werden wie bisher verworfen, weil das v2-Dokument nur `servers` unter `mcp` erlaubt, `artifact_validate._validate_opencode_v2`; schreibt über `io.write_checked(..., allow_secrets=config.get("allow-committed-secrets", False), verify_gitignored=…, config=config, dry_run=dry_run)`) und `opencode_v2_config.rollback_opencode_mcp(project_root: Path, provider_config: dict, provider: str, log: SyncLog, dry_run: bool) -> None` (Spec 3.5 (4): beginnt mit `owns_opencode_surface`; Datei und State aus den aufgelösten Daten des Eigentümers (`committed-file`, `opencode_state_path`), nie festes `opencode.json`; entfernt die State-Pfade, leert/entfernt `mcp.servers` und `mcp` nur, wenn sie danach leer sind); Änderungen in `mcp_provider_config.generate_provider_configs` (`:590`): `pc`/`mcp_cfg`/`fmt`/`committed_file` werden **vor** den frühen Returns (`:614–615`, `:618–619`) aufgelöst und `rollback_opencode_mcp(project_root, pc, provider, log, dry_run)` wird auf diesen frühen Pfaden sowie bei `fmt != "opencode-json-v2"` aufgerufen (für jeden Provider; für Nicht-Eigentümer No-op ohne State-Zugriff); der committed-Aufruf von `_write_provider_config` für `fmt == "opencode-json-v2"` nutzt `sync_opencode_mcp_managed` (`_update_opencode_v2_json_config`, `:309`, bleibt für die lokale Secrets-Datei `.opencode/mcp.local.json` unverändert; Ersetzungs-Semantik dort ist Spec-Nicht-Ziel R-14); v1-Writer `_update_json_config(path, "mcp", …)` bleibt byte-identisch (R-15); Consumes Task 7/8/9, `isolation._STATE_V2_MCP`
- [x] Step 1: Test schreiben (7 Tests): `test_ac_b4_user_mcp_server_survives_v2_sync`; `test_ac_b7_v2_to_v1_with_active_servers_removes_managed_server_paths`; `test_ac_c17_v2_to_v1_without_active_servers_removes_managed_paths_keeps_user_entry`; `test_ac_c17_namespace_removed_after_rollback`; `test_ac_b16_mcp_namespace_isolated_from_keys_namespace`; `test_ac_b20_mcp_rollback_not_run_for_non_owner_provider` (Claude-Iteration mit vorhandenem Opencode-MCP-State lässt `opencode.json` und State byte-identisch); `test_mcp_writer_passes_secret_gate_params_to_write_checked`
- [x] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k "ac_b4_user_mcp or ac_b7_v2_to_v1_with_active or ac_c17 or mcp_namespace or mcp_rollback_not_run or mcp_writer_passes"` → Exit 1, `FAILED …::test_ac_c17_v2_to_v1_without_active_servers_removes_managed_paths_keeps_user_entry`
- [x] Step 3: implementieren; Test grün: `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_mcp_config.py tests/test_opencode_runtime_gate.py -q` → Exit 0
- [x] Step 4: commit `feat: manage opencode v2 mcp servers per path with rollback`

### Task 17: C2.4 — `_validate_opencode_v2` und `check_mcp_connection_keys` (Katalog-Validierung)
**Agent:** developer · **Issue:** #1007 · **AC:** AC-C10, AC-C8/AC-C9 (Katalog-Typprüfung)
**Depends on:** 15
**Files:**
- Modify: `scripts/lib/artifact_validate.py`
- Modify: `scripts/lib/consistency/artifact_contracts.py`
- Modify: `tests/test_artifact_contracts.py`
**Interfaces:** Produces in `artifact_validate._validate_opencode_v2` (`artifact_validate.py:275`) Findings (Check `artifact-contract`) für: Server-Eintrag mit `enabled` → „v2 server uses legacy 'enabled'“; `timeout` ohne ganzzahlige `catalog`/`execution` (optionales ganzzahliges `startup` ist zulässig, Amendment B1) → Finding; `oauth` mit camelCase-Schlüsseln (`clientId`, `clientSecret`) → Finding; sowie `consistency.artifact_contracts.check_mcp_connection_keys(agent_meta_root: Path, project_config: dict | None = None) -> list[Finding]` (neu anlegen; bisher existiert nur `check_artifact_contracts` (`artifact_contracts.py:64`)) (Spec 3.5): prüft `timeout` (Objekt mit Ganzzahlen `startup` (optional), `catalog`, `execution`), `oauth` (Objekt mit snake_case-Schlüsseln `client_id`, `client_secret`, `scope`) und `disabled` (bool) auf dem **zusammengeführten** Katalog (geladen über `registry_query.load_mcp_registry`; Framework `config/plugin-catalog.yaml`, Projekt, inline; Projekt überschreibt Framework); Verstoß → `Severity.ERROR`, Meldung `mcp-connection-key: <server>.<key> invalid`; Aufruf aus `check_artifact_contracts`; Consumes `artifact_validate._finding(path, message)`, `consistency.report.Finding`/`Severity`
- [x] Step 1: Test schreiben (7 Tests in `tests/test_artifact_contracts.py`): `test_v2_server_with_enabled_is_finding`; `test_v2_timeout_non_integer_is_finding`; `test_v2_oauth_camel_case_is_finding`; `test_v2_valid_server_has_no_finding` (AC-C10 über `validate_json_document("opencode.json", "opencode-json-v2", …)`, Aufruf-Signatur vor dem Schreiben im bestehenden Test `test_validate_json_document_v2_accepts_subagent_depth` ablesen); `test_check_mcp_connection_keys_invalid_timeout_is_error`; `test_check_mcp_connection_keys_valid_catalog_has_no_finding` (reale Katalogdatei); `test_check_mcp_connection_keys_validates_merged_project_override`
- [x] Step 2: rot: `python3 -m pytest tests/test_artifact_contracts.py -q -k "v2_server or v2_timeout or v2_oauth or v2_valid or check_mcp_connection_keys"` → Exit 1, `6 failed, 1 passed`
- [x] Step 3: implementieren; Test grün: `python3 -m pytest tests/test_artifact_contracts.py tests/test_opencode_v2_surface.py -q` → Exit 0; `python3 scripts/consistency-check.py` → rc 0 (realer Katalog ohne Verstoß)
- [x] Step 4: commit `feat: validate opencode v2 mcp server shape and catalog connection keys`

## Phase C3 — Gate-Plugin v2 (nur bei `VERDICT-C3: GO`; sonst alle Checkboxen mit „entfällt (NO-GO)“ abhaken)

### Task 18: C3.1 — v2-Plugin-Template, Protokoll und datengetriebene Aktivierung
**Agent:** senior-developer · **Issue:** #1007 · **AC:** AC-C12, AC-C13
**Depends on:** 13a
**Gate:** `VERDICT-C3: GO` — **liegt vor (Spike 2026-10-23), Task läuft.** Kante 13a nur textuell, Parser-Limit (`_DEPENDS_RE` kennt keine alphanumerischen IDs).
**Amendment-B1-Folge:** Q1 ist VERIFIED; der Config-Key heißt `plugins` (Plural) und Dateien unter `.opencode/plugins/` werden ohne Config-Eintrag auto-discovered → **kein** Eintrag in `opencode.json`, kein Managed-Pfad (Doku-Korrektur aus §3.6, Task 27). Plugin-Format bleibt: Default-Export als Objekt mit `id` und `setup(ctx)`. **Für automatisierte Gate-Prüfungen (Review RVW-C0-06):** Fixtures setzen explizite `permissions` `allow`/`deny`; Default `ask` plus `--auto` liefert `Permission denied: shell` und ist keine Bestätigung (Spike Q2, Nebenbefund).
**Files:**
- Create: `templates/plugins/runtime-gate.opencode-v2-plugin.js.tmpl`
- Modify: `scripts/lib/runtime_gate.py`
- Modify: `scripts/lib/providers.py`
- Modify: `config/ai-providers.yaml`
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces `runtime_gate.PLUGIN_TEMPLATE_BY_PROTOCOL["opencode-plugin-v2-js"] = "templates/plugins/runtime-gate.opencode-v2-plugin.js.tmpl"` (`runtime_gate.py:93`), `providers.SUPPORTED_PLUGIN_PROTOCOLS = {"opencode-plugin-js", "opencode-plugin-v2-js"}` (`providers.py:611`), Registry-Schlüssel `surface-plugin-protocols: {v2: opencode-plugin-v2-js}` und `surface-has-plugins: {v2: true}` im Opencode-Eintrag (statisches `has_plugins: false` bleibt, kein v1-Eintrag), Auflösung in `providers._apply_surface_aux_selection` zu `plugin_protocol` und `has_plugins`; Template nach Spike-Q4 (Anpassung des v1-Templates `templates/plugins/runtime-gate.opencode-plugin.js.tmpl` oder Neuschreibung; Modus `observe`); Plugin-Pfad `.opencode/plugins/agent-meta-runtime-gate.js` (`runtime_gate_plugin_relpath`, `PLUGIN_STEM`); Aktivierung `surface-has-plugins.v2: true` nur, wenn das Spike-Doc eine reproduzierbare Probe (`opencode run`-Ausgabe) für Q3 enthält; Consumes Task 13a, Spike-Q1–Q4. Der Fallback (NO-GO) ist nicht Teil dieses Tasks (Task 3a, läuft in beiden Fällen)
- [x] Step 1: Test schreiben (3 Tests): `test_ac_c12_v2_project_gets_plugin_file_and_tier_plugin`; `test_ac_c12_v1_project_keeps_tier_permission_and_no_plugin_file`; `test_ac_c13_has_plugins_false_resolved_means_no_plugin_file`
- [x] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k "ac_c12 or ac_c13"` → Exit 1, `2 failed, 1 passed` (der v1-Test ist als Regressionstest bereits grün)
- [x] Step 3: implementieren; Test grün: `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_runtime_gate_plugins.py tests/test_runtime_gate_rendering.py tests/test_provider_agnostic_dispatch.py -q` → Exit 0
- [x] Step 4: commit `feat: generate opencode v2 runtime gate plugin when verified`

### Task 19: C3.2 — Absicherung Tier `plugin`: Deny bleibt bei `observe`, Spike-Invariante verschärfen
**Agent:** tester · **Issue:** #1007 · **AC:** AC-C14, AC-C2 (Äquivalenz bei GO)
**Depends on:** 18
**Files:**
- Modify: `tests/test_opencode_v2_surface.py`
- Modify: `tests/test_opencode_v2_spike.py`
**Interfaces:** Produces als **Absicherungstests** (kein Produktivcode; Logik liegt in `permission_deny_required` (Task 13) und `reconcile_opencode_surface_gate` (Task 13a)): `test_ac_c14_real_v2_registry_plugin_observe_keeps_deny_triples` (reale Registry mit den C3-Schlüsseln aus Task 18: Tier `plugin`, Modus `observe` → Tripel bleiben; Modus `enforce` per Monkeypatch von `runtime_gate._baked_plugin_mode` → Tripel werden entfernt), `test_oqb12_tier_plugin_writes_no_default_agent_but_checks_entry_point` (bei Tier `plugin` läuft Spec-A-Schritt 3 nicht; `reconcile_opencode_surface_gate` prüft den Einstiegspunkt über `_opencode_entry_point`, schreibt nach `observe` aber kein `default_agent`; fehlender Einstiegspunkt → WARNING und kein Tripel), `test_v1_tier_permission_unchanged_with_c3_registry` (v1 mit denselben Registry-Daten bleibt Tier `permission`); in `tests/test_opencode_v2_spike.py` verschärft Task 19 den GO-Zweig von `test_ac_c2_gate_fallback_invariants` von „Schlüssel vorhanden ⇒ GO“ auf Äquivalenz; Consumes Task 18, Task 13/13a. Dieselbe Fixture-Regel wie in Task 13a/18 gilt auch hier: explizite `permissions` `allow`/`deny`, nie Default `ask` plus `--auto` (keine Bestätigung, Spike Q2 Nebenbefund).
- [x] Step 1: Tests schreiben (Absicherungstests: beim ersten Lauf grün, falls Task 13/13a/18 korrekt sind)
- [x] Step 2: Lauf: `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_opencode_v2_spike.py tests/test_runtime_gate_wiring.py tests/test_runtime_gate_config.py tests/test_opencode_runtime_gate.py -q` → Exit 0
- [x] Step 3: Negativprobe (nicht committen): `permission_deny_required` temporär ohne `observe`-Zweig → `test_ac_c14_real_v2_registry_plugin_observe_keeps_deny_triples` `1 failed`; C3-Schlüssel aus der Registry-Kopie entfernen → der verschärfte Spike-Test `1 failed`
- [x] Step 4: commit `test: guard opencode v2 gate deny under plugin observe mode`

## Phase D — Frontmatter, `cli.json`, Duplikat, Doku, Tests, Release

### Task 20: D1.1 — Closed-world-Builder für v2-Agent-Permissions
**Agent:** senior-developer · **Issue:** #1007 · **AC:** AC-D1 (Builder-Teil)
**Depends on:** 17
**Files:**
- Modify: `scripts/lib/provider_transform.py`
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces `provider_transform.map_tools_to_opencode_v2_permissions(tools: list, deny_list: list[str] | None = None) -> list[dict[str, str]]`: Claude-Tool → Aktion (`Bash`→`shell`, `Write`/`Edit`→`edit`, `Agent`→`subagent`), **genau ein** Eintrag je Aktion in der Reihenfolge `edit`, `shell`, `subagent` mit `{"action", "resource": "*", "effect": "allow"|"deny"}` (allow bei Mapping, sonst deny; unabhängig von `deny_list`/`opencode_deny_critical`); `_map_claude_tools_to_opencode_permissions` (`provider_transform.py:703`) bleibt unverändert; Consumes nichts Neues
- [ ] Step 1: Test schreiben (4 Tests): `test_ac_d1_builder_allows_mapped_actions`; `test_ac_d1_builder_closed_world_denies_unmapped_actions` (Tools `["Read"]` → alle drei `deny`, AC-D1 Rolle ohne `Write`/`Edit`); `test_ac_d1_builder_ignores_deny_list`; `test_ac_c6_v1_mapper_unchanged` (Ausgabe von `_map_claude_tools_to_opencode_permissions` für ein festes Tool-Set gegen eingebettete Referenz)
- [ ] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k "builder or v1_mapper"` → Exit 1, `3 failed, 1 passed`
- [ ] Step 3: implementieren; Test grün: `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_transform_contracts.py -q` → Exit 0
- [ ] Step 4: commit `feat: add closed-world opencode v2 permission builder`

### Task 21: D1.2 — v2-Frontmatter-Funktion und Mechanismus-Verzweigung
**Agent:** senior-developer · **Issue:** #1007 · **AC:** AC-D1, AC-D2, AC-D3, AC-D4
**Depends on:** 20
**Files:**
- Modify: `scripts/lib/provider_transform.py`
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces `provider_transform._transform_frontmatter_for_opencode_v2(content: str, name: str, description: str, model: str, steps: str, generated_from: str, agent_meta_root: Path, temperature: str = "", strip_fields: list[str] | None = None, quiet_fields: frozenset[str] | None = None, mode: str | None = None, variant: str | None = None, deny_edit: bool = False, edit_allow_paths: tuple[str, ...] = ()) -> str` (Unterschiede zur v1-Funktion laut Spec 3.7: `permissions:` als Liste statt `permission:`-Map, `steps` ohne `maxSteps`-Alias und ohne `temperature`/`max_tokens`/`top_p`, `model` mit `#variant`, nie `tools`, nie `subagent_depth`, kein separates `system:`-Feld; gemeinsame Hilfsfunktionen wiederverwenden); Verzweigung im Zweig `mechanism in ('opencode-native', 'opencode-native-v2')` (`provider_transform.py:384`, Mechanismus-Unterscheidung bisher bei :409): `if mechanism == 'opencode-native-v2': return _transform_frontmatter_for_opencode_v2(...)` — der `opencode-native`-Pfad (Opencode v1 und Mammouth) bleibt unverändert; `variant` aus `provider-options.<provider>.model-variants[<role>]`; Consumes Task 20, Task 6 (Modell-Pattern)
**Amendment-B1-Folge:** Q5 bestätigt `system` (Body) und `variant` (`#variant`) als **VERIFIED** → Task 21 bleibt inhaltlich unverändert (kein `system:`-Feld, `#variant` wie beschrieben). Die Agent-interne Permissions-Reihenfolge (`*`-Deny vor Pfad-Allows) betrifft Task 22, nicht die Frontmatter-Mechanik.
- [ ] Step 1: Test schreiben (5 Tests): `test_ac_d1_v2_artifact_has_permissions_list_and_no_legacy_keys` (kein `permission:`, `tools:`, `maxSteps`, `subagent_depth`); `test_ac_d1_role_without_write_has_edit_deny`; `test_ac_d2_steps_emitted_without_maxsteps`; `test_ac_d3_variant_appended_to_model_only_for_configured_role`; `test_ac_d4_v1_artifacts_byte_identical_to_pre_change_output` (festes Template, Referenz aus `_transform_frontmatter_for_opencode` direkt)
- [ ] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k "ac_d1_v2 or ac_d1_role or ac_d2 or ac_d3 or ac_d4"` → Exit 1, `4 failed, 1 passed`
- [ ] Step 3: implementieren; Test grün: `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_transform_contracts.py tests/test_opencode_agents.py -q` → Exit 0
- [ ] Step 4: commit `feat: generate native opencode v2 agent frontmatter`

### Task 22: D1.3 — `deny_edit`, erlaubte Schreibpfade, `system` in der Allow-Liste, Mammouth-Isolation
**Agent:** senior-developer · **Issue:** #1007 · **AC:** AC-C16 (b), AC-D6
**Depends on:** 21
**Files:**
- Modify: `scripts/lib/provider_transform.py`
- Modify: `config/ai-providers.yaml`
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces `deny_edit`-Semantik in `_transform_frontmatter_for_opencode_v2` identisch zu Spec A IC-3 (Spec 3.4 „Agent-Ebene“): bei `deny_edit=True` wird der `edit`-Eintrag der Primary-Rolle zu `{action: edit, resource: "*", effect: deny}`, ergänzt um `allow`-Einträge für `edit_allow_paths` (Quelle `opencode_primary_edit_allow` aus `config/provider-tools.yaml`, von Spec A; §3.4 Agent-Ebene), nur falls die Rolle `Write`/`Edit` hat; Aufruf mit `deny_edit = permission_deny_required(provider_config, capabilities, plugin_mode)` am Frontmatter-Aufrufort — `capabilities` und `plugin_mode` werden **dort** aufgelöst (nicht `opencode_runtime_gate_wanted`, Amendment B3); `system` wird in `agent-transform.allowed-fields` (Opencode, `config/ai-providers.yaml` ~Zeile 323–345) aufgenommen; Consumes Task 21, Task 13 (`isolation.permission_deny_required`), Spec-A-Symbol `opencode_primary_edit_allow`
**Amendment-B3-Folge (2026-10-23, bindend):** `deny_edit` wird mit `permission_deny_required(provider_config, capabilities, plugin_mode)` berechnet — also auch bei Tier `plugin` + Modus `observe` — und **nicht** mit dem eingefrorenen `opencode_runtime_gate_wanted` (Spec A IC-4, nur Tier `permission`). Der Frontmatter-Aufrufort **MUSS** dazu zusätzlich `capabilities` (Eintrag aus `config/provider-capabilities.yaml`) und `plugin_mode` (`runtime_gate._baked_plugin_mode`) auflösen — beide Werte entstehen am Aufrufort und werden nicht in der Transformation nachgeladen. Falsifizierbar wird das nur auf einer `plugin`-Fixture: `test_ac_c14_orchestrator_artifact_has_edit_deny_at_plugin_observe` (Step 1) schlägt fehl, solange `deny_edit` noch das rein permission-basierte Prädikat nutzt, weil auf einer `permission`-Tier-Fixture beide Prädikate identisch sind. Grund: Bei `plugin`+`observe` steht das Agent-`edit: allow` der Primary-Rolle zuletzt und überstimmt das globale Config-`deny` (last match wins) — die Agent-Ebene muss dasselbe Prädikat wie die Config-Tripel verwenden (Spec Amendment B3, AC-C14/C16b). `opencode_runtime_gate_wanted`/`_opencode_runtime_gate_entries` bleiben unverändert.
**Amendment-B1-Folge:** Spike Q3 VERIFIED (last match wins) → der `*`-`deny` steht **vor** den pfadspezifischen `allow`-Einträgen aus `edit_allow_paths`, damit die spezifischeren Allows gewinnen. `test_ac_c16b_orchestrator_artifact_has_edit_deny_when_gate_active` prüft die Reihenfolge (deny vor allows).
- [ ] Step 1: Test schreiben (5 Tests): `test_ac_c16b_orchestrator_artifact_has_edit_deny_when_gate_active` (inkl. Positionsprüfung deny vor allows); `test_ac_c16b_no_edit_deny_without_gate`; `test_ac_c14_orchestrator_artifact_has_edit_deny_at_plugin_observe` (Fixture mit Tier `plugin` und `runtime_gate._baked_plugin_mode` → `observe`: Orchestrator-Artefakt trägt `{action: edit, resource: "*", effect: deny}`; schlägt fehl, solange `deny_edit` das eingefrorene `opencode_runtime_gate_wanted` nutzt, weil auf einer `permission`-Tier-Fixture beide Prädikate identisch sind); `test_ac_d6_mammouth_with_surface_v2_keeps_opencode_native_output` (Mammouth-Eintrag ohne `surface-mechanisms`, Ausgabe enthält `permission:`-Map, keine `permissions:`-Liste, WARNING REV-R5 aus `providers._surface_version_warnings`); `test_system_in_allowed_fields`
- [ ] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k "ac_c16b or ac_c14_orchestrator_artifact or ac_d6 or system_in_allowed"` → Exit 1, `4 failed, 1 passed`
- [ ] Step 3: implementieren; Test grün: `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_transform_contracts.py tests/test_artifact_contracts.py -q` → Exit 0
- [ ] Step 4: commit `feat: deny edit on opencode v2 primary agent when gate active`

### Task 23: D2 — `cli.json` als Managed-Datei
**Agent:** senior-developer · **Issue:** #1007 · **AC:** AC-D7, AC-B16, AC-B20 (cli-Teil)
**Depends on:** 22
**Files:**
- Modify: `scripts/lib/opencode_v2_config.py`
- Modify: `scripts/lib/sync_pipeline.py`
- Modify: `scripts/lib/cli_commands.py`
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces `opencode_v2_config.sync_opencode_cli_file(project_root: Path, config: dict, provider: str, provider_config: dict, log: SyncLog, dry_run: bool) -> None` (Spec 3.8; gibt zuerst zurück, wenn `not owns_opencode_surface(provider_config, provider)`; Datei = `provider_config["cli_file"]` (aufgelöst, Task 6), relativ zum Verzeichnis von `committed-file`; State `opencode_state_path`; fehlt `cli_file` oder `provider-options.<provider>.cli`: nichts schreiben, nichts löschen — Ausnahme Rückbau bei vorhandenem State `opencode-v2-cli`; jeder Top-Level-Schlüssel des `cli`-Objekts ist ein Managed-Pfad nach den Regeln der Tabelle aus Task 7; Schreiben über `io.write_checked` mit den Secret-Gate-Parametern; `tui.json` wird nie erzeugt, verändert oder gelöscht); Aufruf direkt nach `sync_opencode_v2_managed_keys` in `sync_pipeline._sync_stage_per_provider` und im `cli_commands`-Test-Repo-Pfad; Consumes Task 6/7/8/10
**Amendment-B1-Folge:** In `cli.json` ist nur der Top-Level-Key `plugins` dokumentiert; `theme`/`autoupdate` sind es nicht. Der Writer bleibt generischer Passthrough (keine Allow-List), aber Test-Fixtures und Doku verwenden `plugins` und behaupten keine Verifikation für `theme`/`autoupdate`.
- [ ] Step 1: Test schreiben (6 Tests): `test_ac_d7_cli_json_written_with_exact_keys` (`cli: {plugins: ["opencode-acme-cli"]}`); `test_ac_d7_no_cli_json_without_option_or_on_v1`; `test_ac_d7_tui_json_never_touched` (vorhandene `tui.json` bleibt byte-identisch); `test_ac_b16_cli_namespace_isolated`; `test_ac_b20_cli_writer_noop_for_non_owner_provider`; `test_cli_writer_passes_secret_gate_params_to_write_checked`
- [ ] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k "ac_d7 or cli_namespace or cli_writer"` → Exit 1, `5 failed, 1 passed` (der Test „keine `cli.json` ohne Option/auf v1“ ist als Regressionstest bereits grün)
- [ ] Step 3: implementieren; Test grün: `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_runtime_gate_wiring.py -q` → Exit 0
- [ ] Step 4: commit `feat: manage opencode v2 cli.json from provider options`

### Task 24: D3.1 — Evidenz zum Ladeverhalten von `opencode.json` + `opencode.jsonc` (mit PR C0 gemergt)
**Agent:** provider-expert · **Issue:** #1007 · **AC:** AC-D8 (Evidenzteil) · **parallel_group:** c0-g1
**Depends on:** —
**Files:**
- Create: `docs/analysis/evidence/2026-10-22-opencode-jsonc-loading.md`
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces Evidenzdokument mit Befehl + Ausgabe (v1 und, falls installierbar, v2: Ladereihenfolge, Merge, Konflikt bei gleichzeitigem `opencode.json`/`opencode.jsonc`), Ergebniszeile `ERGEBNIS: JSONC-TRAEGT-NICHTS-BEI` oder `ERGEBNIS: JSONC-TRAEGT-INHALT-BEI` sowie Marker VERIFIED/DOKU/UNVERIFIED pro Aussage, und den Test `test_ac_d8_evidence_present_with_result_line` in `tests/test_opencode_v2_surface.py` (prüft Datei + genau eine `ERGEBNIS:`-Zeile); Consumes `docs/analysis/evidence/2026-09-30-runtime-opencode-v1.md` Zeilen 98–111 (bestehende v1-Evidenz) und den Inhalt der Repo-`opencode.jsonc`
- [x] Step 1: Repo-`opencode.jsonc` lesen; bestehende v1-Evidenz sichten; Test `test_ac_d8_evidence_present_with_result_line` schreiben und rot beobachten: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k ac_d8_evidence` → Exit 1, `1 failed`
- [x] Step 2: Probe (höchstens 3 Läufe) mit beiden Dateien in einem Temp-Verzeichnis unter `.tmp/` ausführen (`opencode debug config`); ist `opencode` nicht installierbar, Aussage als DOKU/UNVERIFIED markieren und im Ergebnis vermerken; Dokument schreiben
- [x] Step 3: grün: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k ac_d8_evidence` → Exit 0, `1 passed`
- [x] Step 4: commit `docs: add evidence for opencode json and jsonc loading`

### Task 25: D3.2 — Dauer-WARNING `opencode-config-duplicate`
**Agent:** developer · **Issue:** #1007 · **AC:** AC-D9
**Depends on:** 17
**Files:**
- Modify: `scripts/lib/consistency/artifact_contracts.py`
- Modify: `tests/test_artifact_contracts.py`
**Interfaces:** Produces in `check_artifact_contracts` (`artifact_contracts.py:64`) bzw. einer neuen Funktion `check_settings_file_duplicates(agent_meta_root: Path, project_config: dict | None = None) -> list[Finding]` (von `check_artifact_contracts` aufgerufen): für jeden **aktiven** Provider mit `settings_file` (Registry-Schlüssel) wird ein `Severity.WARNING`-Finding `opencode-config-duplicate: opencode.json and opencode.jsonc both present; keep one` erzeugt, wenn eine Datei mit gleichem Stamm und Endung `.jsonc` im selben Verzeichnis existiert (Meldungstext aus Stamm/Endung zusammengesetzt, kein Providername); `consistency-check.py` bleibt rc 0 ohne `--strict`, rc 1 mit `--strict`; Consumes `providers.load_providers_config`, `consistency.report.Finding`/`Severity`
- [ ] Step 1: Test schreiben (3 Tests): `test_ac_d9_duplicate_jsonc_is_warning`; `test_ac_d9_no_finding_without_jsonc`; `test_ac_d9_check_is_provider_agnostic` (anderer Provider mit `settings_file: foo.json` + `foo.jsonc` löst dasselbe Finding aus)
- [ ] Step 2: rot: `python3 -m pytest tests/test_artifact_contracts.py -q -k ac_d9` → Exit 1, `2 failed, 1 passed`
- [ ] Step 3: implementieren; Test grün: `python3 -m pytest tests/test_artifact_contracts.py -q` → Exit 0; `python3 scripts/consistency-check.py` → Warnung für das Repo-Root-Duplikat erscheint, rc 0
- [ ] Step 4: commit `feat: warn when settings file has a jsonc twin`

### Task 26: D3.3 — `opencode.jsonc` im Repo-Root entfernen
**Agent:** developer · **Issue:** #1007 · **AC:** AC-D8
**Depends on:** 24, 25
**Files:**
- Modify: `opencode.json`
**Interfaces:** Produces Repo ohne `opencode.jsonc` (Löschung als `git rm opencode.jsonc` durch den Orchestrator bzw. die `git`-Rolle, da die Dateitools kein Löschen kennen; Rolle meldet die Löschung in ihrem Report); bei `ERGEBNIS: JSONC-TRAEGT-INHALT-BEI` wird der Inhalt vorher nach `opencode.json` überführt; Consumes Evidenz aus Task 24 (Evidenz-Commit liegt vor dem Lösch-Commit), Task 25
- [ ] Step 1: Test schreiben (1 Test in `tests/test_opencode_v2_surface.py`): `test_ac_d8_repo_root_has_no_opencode_jsonc` (prüft `not (_REPO_ROOT / "opencode.jsonc").exists()` und Evidenz-Datei vorhanden)
- [ ] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k ac_d8_repo_root` → Exit 1, `1 failed`
- [ ] Step 3: Inhalt ggf. überführen, Datei entfernen; Test grün: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k ac_d8` → `2 passed`; `python3 scripts/sync.py --check` → rc 0 (zeigt `opencode.json` weiter in Sync; falls `--check` wegen der Datei Drift meldet, `python3 scripts/sync.py` ausführen und das Ergebnis im PR begründen)
- [ ] Step 4: commit `chore: remove duplicate opencode.jsonc from repo root`

### Task 27: D4 — Doku: `docs/providers/opencode.md` und AGENTS.md-only
**Agent:** technical-writer · **Issue:** #1007 · **AC:** AC-D10
**Depends on:** 23, 26
**Files:**
- Modify: `docs/providers/opencode.md`
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces aktualisierte Doku: Kopfzeile „Stand“ mit der aktuellen Version aus `VERSION` (statt „v0.33.x“, Zeile 3), neue Abschnitte `## Surface v1 vs. v2` (Key-Tabelle aus Spec 3.2–3.8), `## Aktivierung` (`provider-options.Opencode.surface-version`), `## Managed Keys und User-Keys`, `## Dateien` (`opencode.json` einzig, kein `.jsonc`, `cli.json`, kein `tui.json`), Hinweise zu Kommentarverlust beim Rückschreiben einer JSONC-`opencode.json` (R-4), zur Ersetzungs-Semantik der lokalen `.opencode/mcp.local.json` (R-14) und zum v1-MCP-Writer (R-15); Regel „AGENTS.md-only“: `AGENTS.md` ist die einzige von agent-meta verwaltete Kontextdatei für Opencode, keine `CLAUDE.md`-/`OPENCODE.md`-Erzeugung, Verweis auf `.opencode/rules/` (Zeile ~83) entfernen; Consumes Tasks 9, 13, 13a, 15, 21, 23 (dokumentierter Ist-Stand), Spike-Ergebnis
**Amendment-B1-Folge:** Doku-Korrekturen aus dem Spike: Plugin-Config-Key ist `plugins` (**Plural**), und Dateien unter `.opencode/plugins/` werden ohne Config-Eintrag auto-discovered; `cli.json` nur mit dem dokumentierten Key `plugins` beschreiben (`theme`/`autoupdate` nicht als verifiziert nennen); `providers` in der Innenform `settings.baseURL`/`env` dokumentieren; `agents.title.model`/`small-model` kommen in der Key-Tabelle nicht vor.
- [ ] Step 1: Test schreiben (2 Tests): `test_provider_doc_current` (kein `v0.33`, die vier Abschnittsüberschriften vorhanden, AC-D10) und `test_provider_doc_states_agents_md_only` (enthält `AGENTS.md-only` und enthält nicht `.opencode/rules/`)
- [ ] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k provider_doc` → Exit 1, `2 failed`
- [ ] Step 3: Doku schreiben; Test grün: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k provider_doc` → `2 passed`
- [ ] Step 4: commit `docs: document opencode v2 surface and agents-md-only context`

### Task 28: T.1 — Szenario 79 `79-opencode-v2-full-surface` (Absicherungstest mit Negativprobe)
**Agent:** tester · **Issue:** #1007 · **AC:** AC-T1
**Depends on:** 27
**Files:**
- Create: `tests/scenarios/configs/79-opencode-v2-full-surface.project.yaml`
- Create: `tests/scenarios/asserts/79-opencode-v2-full-surface.sh`
- Modify: `tests/scenarios/registry.md`
**Interfaces:** Produces Szenario-Config nach dem Muster von `tests/scenarios/configs/69-opencode-v2-surface.project.yaml` (`ai-providers: [Opencode]`, `provider-options.Opencode: {surface-version: v2, experimental-todo: true, model-variants: {developer: high}, cli: {plugins: ["opencode-acme-cli"]}}`, strict-Orchestrator via `orchestrator: {mode: strict}`, Plugin `playwright` aktiv, `project.prefix: s79`), Assert-Skript (ausführbar, `chmod +x`) prüft: `experimental.subagent_depth`/`experimental.todo`, `permissions[]`-Tripel (C) am Listenende, `mcp.servers` ohne `enabled`, Agent-Frontmatter mit `permissions:`-Liste und `model: …#high`, `cli.json` mit dem Key `plugins`, `sync.py --check` rc 0; der v2→v1-Rückwechsel ist **nicht** Teil des Shell-Szenarios, sondern wird als Python-Test `test_v2_to_v1_switch_rolls_back_all_namespaces` in Task 29 geprüft (U-8: ein zweiter Sync im Szenario-Runner ist nicht belegt); Registry-Zeile `| \`79-opencode-v2-full-surface\` | Opencode | strict | … |` in `tests/scenarios/registry.md` direkt nach der Zeile von Szenario 78 (Zeilenaufbau der Nachbarzeilen kopieren); Consumes alle vorigen Tasks, `tests/scenarios/run.sh` (Aufrufform vorher lesen). Der Task ist ein **Absicherungstest** der vorigen Tasks: er ist beim ersten Lauf grün; sein Nachweis der Nicht-Vakuität ist die Negativprobe in Step 2
**Amendment-B1-Folge:** `small-model` und die Assertion auf `agents.title.model` entfallen (AC-B9); `cli` nutzt den dokumentierten Key `plugins` statt `theme`; `permissions[]`-Tripel werden am Listenende erwartet.
- [ ] Step 1: Config + vollständiges Assert-Skript schreiben und Registry-Zeile ergänzen; `tests/scenarios/run.sh` zuvor lesen (Aufrufform)
- [ ] Step 2: Negativprobe (nicht committen): das Assert-Skript gegen eine Kopie der Config mit `surface-version: v1` (unter `.tmp/`) laufen lassen → Exit ≠ 0; belegt, dass die Assertions keine v1-Ausgabe akzeptieren. Schlägt eine Prüfung gegen die echte v2-Config fehl, ist das ein Befund für den zuständigen Task (Rückmeldung an den Orchestrator, kein Szenario-Hack)
- [ ] Step 3: grün: `bash tests/scenarios/run.sh 79-opencode-v2-full-surface` → Exit 0; `grep -c '^| `79-opencode-v2-full-surface`' tests/scenarios/registry.md` → `1`
- [ ] Step 4: commit `test: add scenario 79 for the opencode v2 full surface`

### Task 29: T.2 — Lab-Diff v1 ↔ v2 und Rückwechsel v2 ↔ v1
**Agent:** tester · **Issue:** #1007 · **AC:** AC-T2, AC-B7 (Integration), AC-B21/AC-B22 (Integration)
**Depends on:** 28
**Files:**
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces `test_lab_diff_v1_v2`: generiert dasselbe Projekt (Fixture aus Szenario 79, ohne v2-Optionen für v1) mit `surface-version: v1` und `v2` in zwei Verzeichnissen unter `tmp_path` und prüft, dass **genau** diese Dateien/Schlüssel differieren: `opencode.json` (`mcp`-Form, `experimental.*`, `permissions` statt `permission`), `.opencode/agents/*.md` (Permissions-Format, Modell-Variante), optional `cli.json`/Plugin-Datei; alle übrigen Dateien (inkl. aller Nicht-Opencode-Provider) sind byte-identisch; Vergleichsbasis v1 = Stand nach Plan A; und `test_v2_to_v1_switch_rolls_back_all_namespaces` (Projekt auf v2 synchronisieren, Konfig auf v1 stellen, erneut synchronisieren: alle vier Namespaces `opencode-v2-*` leer bzw. entfernt, keine `experimental`-/`permissions`-/`mcp.servers`-Managed-Reste in `opencode.json`, User-Keys erhalten; sowie der Gegenweg v1-strict → v2 entfernt die `permission`-Map-Denys und leert `runtime-gate-deny`); Consumes Harness-Hilfsfunktion zum Rendern eines Projekts (Muster aus `tests/test_ac01_render_identity.py` vorher lesen und wiederverwenden)
- [ ] Step 1: Tests schreiben (`test_lab_diff_v1_v2`, `test_v2_to_v1_switch_rolls_back_all_namespaces`)
- [ ] Step 2: Lauf: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k "lab_diff or switch_rolls_back"` → Exit 0, `2 passed` (reine Absicherung der vorigen Tasks, beim ersten Lauf grün; schlägt ein Test an, liefert die Differenzliste den Befund)
- [ ] Step 3: Negativprobe: temporär eine Zeile in `opencode.json` v2 ergänzt bzw. einen Namespace-Rückbau auskommentiert → `1 failed` je Test (nicht committen) — Nachweis, dass die Tests nicht vakuös sind
- [ ] Step 4: commit `test: add v1 versus v2 lab diff and switch rollback for opencode`

### Task 30: T.3 — Querwirkungs-Beweis: andere Provider und Goldens unverändert
**Agent:** tester · **Issue:** #1007 · **AC:** AC-D5, AC-D6, AC-T4
**Depends on:** 29
**Files:**
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces `test_ac_d5_other_providers_byte_identical_when_opencode_is_v2` (Projekt mit Opencode (v2) + Claude + Gemini + Mammouth vs. Referenzlauf mit Opencode v1: alle Artefakte von Claude, Gemini und Mammouth byte-identisch; providerübergreifende Dateien wie `AGENTS.md` dürfen nur Opencode-Anteile ändern und werden im Test explizit aufgelistet) und `test_ac_t4_fixtures_unchanged` (prüft SHA-256 der drei Fixture-Verzeichnisse `tests/fixtures/ac01-baseline`, `tests/fixtures/slimming-golden`, `tests/fixtures/compact-golden` gegen eine im Test eingebettete Liste — Werte beim ersten Lauf nach Plan-A-Merge aus den Dateien ermitteln und eintragen, kein Subprozess); zusätzlich Pflichtlauf der Golden-Tests; Consumes Task 29-Harness
- [ ] Step 1: Test schreiben (2 Tests)
- [ ] Step 2: Lauf: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k "ac_d5 or ac_t4"` → Exit 0, `2 passed`
- [ ] Step 3: Golden-Lauf: `python3 -m pytest tests/test_ac01_render_identity.py tests/test_template_slimming_equivalence.py tests/test_compact_matrix.py -q` → Exit 0; jede nötige Fixture-Änderung = Task fehlgeschlagen (Global Constraints)
- [ ] Step 4: commit `test: prove opencode v2 has no cross-provider effect`

### Task 31: T.4 — Provider-Agnostik- und Abdeckungs-Meta-Test
**Agent:** tester · **Issue:** #1007 · **AC:** AC-T3, AC-T6
**Depends on:** 30
**Files:**
- Modify: `tests/test_provider_agnostic_dispatch.py`
- Modify: `tests/test_opencode_v2_surface.py`
**Interfaces:** Produces in `test_lib_sweep_covers_task_modules` (`test_provider_agnostic_dispatch.py:398`) den zusätzlichen Eintrag `"opencode_v2_config.py"` in `expected`; in `tests/test_opencode_v2_surface.py` `test_ac_t3_required_acs_have_tests` (parst den Dateitext per Regex nach `def test_ac_(b1|b2|b4|b5|b7|b12|b16|b17|b18|b19|b20|b21|b22|c3|c4|c7|c14|c15|c16a|c16b|c17|d1|d3|d4|d7)_` — mindestens ein Treffer je Eintrag; AC-D9 liegt in `tests/test_artifact_contracts.py` und wird dort per zweitem Dateipfad geprüft; AC-C1/AC-C2 werden in `tests/test_opencode_v2_spike.py` geprüft (Spec AC-T3): Treffer auf `def test_ac_c1_` und `def test_ac_c2_` dort) sowie ein statischer Test `test_new_v2_code_has_no_provider_branch` (AST-Scan von `opencode_v2_config.py` auf Vergleiche gegen Provider-Namenskonstanten und auf Zugriffe `"surface-version"`)
- [ ] Step 1: Test schreiben (3 Änderungen wie oben)
- [ ] Step 2: Lauf: `python3 -m pytest tests/test_provider_agnostic_dispatch.py tests/test_opencode_v2_surface.py tests/test_opencode_v2_spike.py -q` → Exit 0; fehlende AC-Testnamen aus der Fehlermeldung nachziehen (Namen der Tests in Task 9–23 an das Schema `test_ac_<id>_…` angleichen — kleine Umbenennungen sind erlaubt)
- [ ] Step 3: Negativprobe wie in Task 29 (temporärer Providervergleich in `opencode_v2_config.py` → `test_no_provider_name_dispatch_branches_in_lib` rot, danach zurücknehmen)
- [ ] Step 4: commit `test: guard opencode v2 coverage and provider agnosticism`

### Task 32: R.1 — CHANGELOG und Gesamt-Validierung
**Agent:** developer · **Issue:** #1007 · **AC:** AC-T5
**Depends on:** 31
**Files:**
- Modify: `CHANGELOG.md`
**Interfaces:** Produces Eintrag unter `## [Unreleased]` (`CHANGELOG.md:3`) in `### Added` (v2-Optionen `experimental-subagent-depth`, `experimental-todo`, `providers`, `model-variants`, `cli` — Amendment B1: **kein** `small-model`; Managed-Merge für `opencode.json`; native `permissions[]`-Gate am Listenende; MCP-v2-Felder inkl. `timeout.startup`; `cli.json` (nur dokumentierte Keys wie `plugins`); v2-natives Agent-Frontmatter; Szenario 79; Spike-Ergebnis) und `### Changed` (v2-Settings tragen `experimental.subagent_depth` statt Top-Level-`subagent_depth` — IC-15 Nr. 16 amended; surface-übergreifender Rückbau der Gate-Permissions; `opencode.jsonc` entfernt; Warnung `opencode-config-duplicate`); keine Verifikationsbehauptung für Features, die der Spike nur als DOKU/UNVERIFIED belegt (insbesondere **kein** `theme`/`autoupdate` in `cli.json`, kein `agents.title.model`); Consumes alle Tasks
- [ ] Step 1: Test schreiben: `test_changelog_mentions_opencode_v2_support` in `tests/test_opencode_v2_surface.py` prüft, dass der Unreleased-Abschnitt die Wörter `opencode v2` und `cli.json` enthält
- [ ] Step 2: rot: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k changelog` → Exit 1, `1 failed`
- [ ] Step 3: CHANGELOG schreiben; grün: `python3 -m pytest tests/test_opencode_v2_surface.py -q -k changelog` → `1 passed`; Gesamtlauf: `python3 -m pytest tests -q -x` → Exit 0; `python3 scripts/sync.py --validate` → rc 0; `python3 scripts/sync.py --check` → rc 0; `python3 scripts/consistency-check.py` → rc 0
- [ ] Step 4: commit `docs: changelog for opencode v2 support`

### Task 33: R.2 — Minor-Version-Bump (nach Nutzerfreigabe)
**Agent:** release · **Issue:** #1007 · **AC:** — (Release-Prozess, Spec Nicht-Ziele)
**Depends on:** 32
**Files:**
- Modify: `VERSION`
**Interfaces:** Produces Minor-Bump von `VERSION` gemäß `.claude/skills/conventions/SKILL.md` (aktuell `2.0.0-beta.2`; die nächste Versionsnummer bestimmt die `release`-Rolle nach dem Pre-Release-Schema); Verschieben des Unreleased-Inhalts in einen Versionsabschnitt nur im Release-Task der `release`-Rolle; Consumes Task 32; der Task startet nur nach ausdrücklicher Nutzerfreigabe (Release ist nicht Teil der Merge-Kette, Push/Tag nur `git`-Rolle)
- [ ] Step 1: Test schreiben: bestehende Versions-Konsistenztests (`tests/test_version_bookkeeping.py`, `tests/test_surface_version_consistency.py`, `tests/test_surface_version_selection.py`, `tests/test_agent_meta_version_schema.py`) als Rot-/Grün-Nachweis verwenden; vor dem Bump `python3 -m pytest tests -q -k version` → Exit 0
- [ ] Step 2: Bump durchführen
- [ ] Step 3: `python3 -m pytest tests -q -k version` → Exit 0; `python3 scripts/sync.py --check` → rc 0
- [ ] Step 4: commit `chore: bump version for opencode v2 support`

## Self-Review

**Rolle je Task:** Jeder Task trägt genau eine Rolle aus dem Bestand `tester`, `provider-expert`, `concept-specifier`, `developer`, `senior-developer`, `technical-writer`, `release` (Dateien `agents/1-generic/*.md` per Glob geprüft).

**Traceability Spec-AC → Task** (55 gültige ACs der Spec Rev. 1.5: B1–B22 **ohne B9** (entfällt, Amendment B1), C1–C17, D1–D10, T1–T7; die früheren Plan-Arbeits-IDs AC-C18/AC-C19 sind durch AC-B21/AC-B22 ersetzt):

| AC | Task | AC | Task |
|---|---|---|---|
| AC-B1 | 9, 11 | AC-C1 | 1, 2, 3 |
| AC-B2 | 11 | AC-C2 | 3a, 19 |
| AC-B3 | 8 | AC-C3 | 13, 13a |
| AC-B4 | 9, 16 | AC-C4 | 13, 13a |
| AC-B5 | 7, 9 | AC-C5 | 13 |
| AC-B6 | 7, 9 | AC-C6 | 13, 20 |
| AC-B7 | 9, 13a, 16, 29 | AC-C7 | 15 |
| AC-B8 | 9, 13a | AC-C8 | 14, 15, 17 |
| AC-B9 | entfällt (Amendment B1) | AC-C9 | 14, 15, 17 |
| AC-B10 | 8 | AC-C10 | 17 |
| AC-B11 | 8 | AC-C11 | 15 |
| AC-B12 | 6, 12 | AC-C12 | 18 |
| AC-B13 | 10 | AC-C13 | 18 |
| AC-B14 | 9 | AC-C14 | 13a, 19 |
| AC-B15 | 9 | AC-C15 | 13, 13a |
| AC-B16 | 5, 9, 13, 16, 23 | AC-C16 | 13 (a), 22 (b) |
| AC-B17 | 7, 9 | AC-C17 | 16 |
| AC-B18 | 10 | AC-D1 | 20, 21 |
| AC-B19 | 7, 9 | AC-D2 | 21 |
| AC-B20 | 8, 9, 10, 13a, 16, 23 | AC-D3 | 4, 21 |
| AC-B21 | 13a, 29 | AC-D4 | 21 |
| AC-B22 | 13a, 29 | AC-D5 | 30 |
| AC-D6 | 22 | AC-D7 | 6, 23 |
| AC-D8 | 24, 26 | AC-D9 | 25 |
| AC-D10 | 27 | AC-T1 | 11, 28 |
| AC-T2 | 29 | AC-T3 | 31 |
| AC-T4 | 30 | AC-T5 | 32 (und jede Phase) |
| AC-T6 | 6, 31 | AC-T7 | 8, 9 |

- Jeder Task hat einen Test mit beobachtetem Rot-Zustand. Ausnahmen mit Begründung: Task 3 bedingt rot; Tasks 3a, 19, 28, 29, 30, 31 sind Absicherungstests mit Negativprobe (Task 3a und 19 gegen manipulierte Registry-/Funktionskopien, Task 28 gegen eine v1-Config); Task 33 nutzt bestehende Versionstests. Rote Zahlen in Tasks 4, 13, 13a, 14, 17, 18, 23 berücksichtigen bereits grüne Regressionstests.
- `Files:`/`Interfaces:` sind für jeden Task vollständig; keine Dateiüberlappung innerhalb der Parallel-Gruppen `c0-g1` (`docs/spikes/…` vs. `docs/analysis/evidence/…` + `tests/test_opencode_v2_surface.py`) und `b-g1` (Schema + Schema-Test vs. `isolation.py` + Gate-Test vs. `providers.py` + `ai-providers.yaml` + Aux-Test); Task 3a (`tests/test_opencode_v2_spike.py`) ist dateidisjunkt zu Task 24.
- `pipeline_stages` deckt die `plan-driven`-Stage `implement` ab.
- Namen in Plan und Spec Rev. 1.4 abgeglichen (inkl. Signaturen `_opencode_v2_gate_permissions(config, provider, agent_meta_root, provider_config, capabilities, plugin_mode)` und `_sync_opencode_v2_gate_permissions(project_root, provider_config, entries, log, dry_run) -> bool`): `reconcile_opencode_surface_gate`, `owns_opencode_surface(pc, provider)`, `opencode_state_path(project_root, pc)`, `committed-file`, `rollback_opencode_mcp(project_root, pc, provider, log, dry_run)`, `permission_deny_required(pc, caps, plugin_mode)`, `check_mcp_connection_keys`, State-Kodierung `{value, prior, prior_absent}`, Test `tests/test_opencode_v2_spike.py::test_ac_c2_gate_fallback_invariants`.
- Kein Platzhalter im Sinn von `_PLACEHOLDER_PATTERNS` (`scripts/lib/consistency/spec_plan.py`); Unsicherheiten stehen explizit unten.

## Annahmen, Unsicherheiten und Re-Planning

**Annahmen (bei Verletzung ist der genannte Task ungültig):**
- **A-1** Plan A ist gemergt und liefert `_opencode_entry_point`, `opencode_runtime_gate_wanted`, `opencode_primary_edit_allow`, `deny_edit`-Parameter und den State-Key `default-agent` mit den in Spec A beschriebenen Signaturen (Tasks 5, 13, 13a, 22). Die tatsächlichen Namen sind beim Task-Start per Grep zu prüfen; Abweichungen führen zu einer Plan-Anpassung vor Ausführung.
- **A-2** `jsonschema` ist in der Testumgebung installiert (`pytest.importorskip`, wie `tests/test_context_profile_schema.py`); fehlt es, werden die Schema-Tests übersprungen und die Schema-Abnahme erfolgt nur über `python3 scripts/sync.py --validate` (Tasks 4, 14).
- **A-3** Eine Opencode-v2-Installation für Proben ist verfügbar oder installierbar (Tasks 2, 24); sonst bleiben die Antworten DOKU/UNVERIFIED und Q5/Q6 gelten als `AMEND`, Q1–Q3 als `NO-GO` (fail-safe).
- **A-4** Die Spec Rev. 1.4 ist abgeglichen (Namen, AC-IDs B1–B22/C1–C17/D1–D10/T1–T7, Rückbau-Matrix, Provider-Bindung). Weicht eine spätere Spec-Revision ab, werden nur Traceability-Tabelle, AC-Spalte und die betroffenen Interfaces angepasst, nicht die Task-Struktur.
- **A-5** Der aufgelöste Opencode-Eintrag behält `mcp-config.surface-formats` und `mcp-config.committed-file` nach `load_providers_config` (Voraussetzung für `owns_opencode_surface`); Task 6 sichert das per Test ab.

**Unsicherheiten (explizit):**
- **U-1 (Spike-abhängig, hoch) — erledigt am 2026-10-23 (Amendment B1):** Existenz und Namen der Phase-B-Keys und der MCP-Felder sind durch den Spike belegt: `experimental.subagent_depth`/`experimental.todo`/`providers`/`cli.json` DOKU, `agents.title.model` UNVERIFIED → entfällt (AC-B9, `small-model`), `providers`-Innenform `settings.baseURL`/`env`. Q5 ist vollständig VERIFIED/DOKU → keine Sperre für C2/D1. Tasks 4, 8, 13, 13a, 14, 18, 21, 22, 23, 27, 28 tragen einen expliziten Amendment-B1-Vermerk (11 Tasks); Tasks 9 und 11 setzen die Folge inzwischen ohne eigenen Vermerk vollständig um: Task 9 verwaltet nach Amendment B1 keinen `agents.title.model`-Pfad mehr, Task 11 verschiebt `subagent_depth` nach `experimental.subagent_depth`; Task 15 braucht keine Änderung (`timeout.startup` ist in Task 14 abgehandelt).
- **U-2 (Spike-abhängig) — erledigt am 2026-10-23 (Amendment B1):** Q3 VERIFIED: „last matching rule wins", Agent-Regeln zuletzt. Der frühere Satz „Task 13 fügt am Listenanfang ein" ist überholt; Task 13/13a fügen am **Listenende** ein, Task 22 ordnet `*`-Deny vor die Pfad-Allows.
- **U-3 (Spec-Inkonsistenz):** AC-C16 (b) gehört laut Spec zu Phase C, benötigt aber die v2-Frontmatter-Funktion aus Phase D (Spec 3.7). Der Plan verifiziert Teil (a) in Task 13 und Teil (b) in Task 22 (Phase D).
- **U-4 (Dateiname, erledigt in Spec Rev. 1.3):** Die Konvention verlangt `…-issue-<n>-…-spike.md` (Regex `_SPIKE_RE` in `scripts/lib/consistency/spec_plan.py` fordert nur das Suffix `-spike.md`). Plan und Spec Rev. 1.3 verwenden einheitlich `docs/spikes/2026-10-22-issue-1007-opencode-v2-plugin-api-spike.md`; Task 3 prüft nur noch, dass die Spec den korrigierten Pfad trägt (Grep, keine Änderung nötig).
- **U-5 (Importzyklus):** `isolation` ↔ `opencode_v2_config` und `isolation` → `runtime_gate`/`providers` (Tasks 5, 13, 13a). Gewählte Lösung: Konstanten in `isolation`, lazy Import von `v2_active`/`owns_opencode_surface`/`opencode_state_path`/`_baked_plugin_mode` innerhalb der Funktionen. Falls das Hindernisse zeigt, wandert `_sync_opencode_v2_gate_permissions` nach `opencode_v2_config` und `isolation` ruft sie lazy auf (Abweichung vom Spec-Ort, im PR zu begründen).
- **U-6 (Signaturen, erledigt in Spec Rev. 1.3):** Der Plan ergänzt `provider_config` (für `opencode_state_path`) in `_sync_opencode_v2_gate_permissions` bzw. `capabilities`/`plugin_mode` (für `permission_deny_required`) in `_opencode_v2_gate_permissions`. Spec 3.4 wurde in Rev. 1.3 nachgezogen; Plan und Spec stimmen überein. Beim Task-Start nur noch gegen den tatsächlichen Spec-A-Stand prüfen (A-1).
- **U-7 (AC-C2 bei GO):** Spec AC-C2 verlangt bei GO die Äquivalenz „C3-Schlüssel vorhanden ⇔ GO“. Vor Task 18 sind die Schlüssel noch nicht angelegt; der Plan prüft im C0-PR nur „Schlüssel vorhanden ⇒ GO“ und verschärft in Task 19 auf Äquivalenz. Alternative (Spec-Klarstellung): Äquivalenz erst ab Phase C3 fordern.
- **U-8 (Szenario-Aufrufform):** Die genaue Form `bash tests/scenarios/run.sh <name>` und ein Registry-Test sind nicht geprüft; Tasks 11 und 28 lesen `tests/scenarios/run.sh` vor der Ausführung. Ein zweiter Sync (Rückwechsel) wird deshalb im Python-Test von Task 29 statt im Shell-Szenario geprüft.
- **U-9 (Tests anderer Dateien):** Tests mit Bezug auf Top-Level-`subagent_depth` für v2 existieren in `tests/test_opencode_v2_surface.py`, `tests/test_settings_depth_and_deny.py` und `tests/test_artifact_contracts.py` (dort akzeptiert der Validator das Top-Level-Feld weiterhin; keine Änderung geplant, weil Ablehnen nicht gefordert ist). `tests/test_ac01_render_identity.py`, `tests/test_dispatch_permissions_frontmatter.py` und `tests/test_sync_validation_gate.py` erwähnen `subagent_depth` ebenfalls und wurden nicht im Detail geprüft; Task 11 prüft sie per Lauf.
- **U-10 (Löschung):** Die Dateitools können keine Dateien löschen (Task 26); Löschung via `git rm` durch Orchestrator/`git`-Rolle.
- **U-11 (Versionsschema):** Die Spec fordert einen „minor“-Bump; die Repo-Version steht in `VERSION` (`2.0.0-beta.2`, Pre-Release). Das konkrete Ziel bestimmt die `release`-Rolle (Task 33).
- **U-12 (Spec-Freigabe):** Die Spec trägt `Status: APPROVED (2026-10-22)`, Rev. 1.5 inkl. Amendment B1; E2 ist erfüllt. A-6/OQ-B1 ist entschieden (Wiederverwendung von `surface-version`, vom Nutzer bestätigt 2026-10-22; Entry E3 erfüllt). OQ-B12 bleibt offen; der Entscheidungszeitpunkt „nach C0-Verdict" ist mit `VERDICT-C3: GO` erreicht, eine Entscheidung steht aus; Spec A wird dafür nicht erweitert (siehe U-13).
- **U-13 (OQ-B12, bekannte Grenze):** Bei Tier `plugin` + `observe` läuft Spec-A-Schritt 3 (`default_agent`-Merge) nicht (Aufrufbedingung Tier `permission` unverändert). `reconcile_opencode_surface_gate` prüft den Einstiegspunkt nur (Eigenprüfung über `_opencode_entry_point`) und schreibt kein `default_agent`. OQ-B12 ist offen; Entscheidungszeitpunkt: nach dem C0-Verdict (Spike C0, `VERDICT-C3`). Falls danach eine Spec-A-Erweiterung bevorzugt wird, entsteht ein Amendment zu Spec A und Task 19 ändert sich; bis dahin gilt die Eigenprüfung.
- **U-14 (MCP-Grenzen als Nicht-Ziele):** Die lokale Datei `.opencode/mcp.local.json` (R-14) und der v1-MCP-Writer (R-15) behalten ihre Ersetzungs-Semantik; beides ist in Spec Rev. 1.3 Nicht-Ziel und wird in Task 27 dokumentiert. AC-C17 deckt nur den Managed-Pfad-Rückbau der committed Datei.
- **U-15 (Task 18/19 statt Spec-Tier-Prädikat-Umbau):** Die frühere Variante, den Tier-Check in `_opencode_runtime_gate_entries` und die Aufrufbedingung zu ersetzen, ist durch Spec Rev. 1.2/1.3 gestrichen. Task 19 enthält deshalb nur Absicherungstests; der Test `test_ic4_functions_and_call_condition_unchanged` (Task 13a) hält die Freeze-Zusage fest. Der eingebettete Quelltext-Hash der Spec-A-Funktionen hängt vom Plan-A-Merge und wird erst beim Task-Start ermittelt.

**Re-Planning-Vermerk (2026-10-23):** Auslöser ist der abgeschlossene C0-Spike (`docs/spikes/2026-10-22-issue-1007-opencode-v2-plugin-api-spike.md`, Commit `5eadea26`) mit `VERDICT-C3: GO` und `VERDICT-FIELDS: AMEND`; die Folgen stehen als Amendment B1 in der Spec (Rev. 1.5).
- **Abgehakt (erledigt):** Task 1 (Struktur-Test) und Task 2 (Spike) — alle vier Steps je Task `[x]`.
- **Geändert (keine Umnummerierung):** Task 4 verliert `small-model` (AC-B9 entfällt; 5 statt 7 Schema-Tests, Rot `1 failed, 4 passed`, Grün `5 passed`; Task 14 dadurch gesamt `9 passed`). Task 8 verliert den Pfad `agents.title.model`, die `providers`-Fixture nutzt `settings.baseURL`/`env`, der Secret-Test prüft `providers.<id>.headers.X-Api-Key`. Task 13/13a fügen Tripel am **Listenende** ein und rollen positionsunabhängig zurück. Task 14/17 lassen das dokumentierte `timeout.startup` zu. Task 18 startet (GO) und dokumentiert `plugins`/Auto-Discovery ohne Config-Eintrag. Task 21 bleibt inhaltlich unverändert (Q5 VERIFIED). Task 22 ordnet den `*`-Deny vor die Pfad-Allows. Task 23 nutzt `cli: {plugins: [...]}`. Task 27 dokumentiert `plugins` (Plural), `settings.baseURL`/`env` und `plugins` in `cli.json`. Task 28 (Szenario 79) entfällt `small-model`, prüft `cli.plugins` und kein `agents.title.model`.
- **Abweichung (Parallelität, Phase B):** `parallel_group: b-g1` war so nicht ausführbar, weil `check_plan_file_overlap` Task 5 ∥ Task 6 ablehnte (Import-Kopplung `isolation.py → providers.py`); ausgeführt wurde Task 4 ∥ Task 5, dann Task 6, dann 7–12 sequenziell.
- **Entfallen:** nur AC-B9 in der Traceability (Zeile „entfällt (Amendment B1)"). Kein Task entfällt, keine Task-Nummer ändert sich.
- **Unverändert:** Task-Struktur, Phasen-/Merge-Reihenfolge und Entry-Kriterien; C2 und D1 sind inhaltlich unberührt, weil Q5 vollständig VERIFIED/DOKU ist. C3 läuft, der NO-GO-Fallback (Task 3a) bleibt als Absicherung.
- **Offen:** OQ-B12 (Entscheidungszeitpunkt ist mit dem C0-Verdict erreicht, Entscheidung steht aus); bis dahin gilt die Eigenprüfung in `reconcile_opencode_surface_gate`.

**Re-Planning:** Nach jedem Phasen-Merge ist zu prüfen: Gelten die Annahmen A-1…A-5 noch? Sind Verdict-Zeilen und Amendment B1 eingearbeitet? Stimmen die Spec-A-Symbolnamen? Der Plan ist nicht eingefroren; Änderungen werden im Plan vermerkt (Datum, Grund) und im Ledger (Checkboxen) abgebildet.
