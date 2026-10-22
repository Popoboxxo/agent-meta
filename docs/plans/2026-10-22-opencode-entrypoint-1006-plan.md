# Opencode-Einstiegspunkt (#1006) — Implementation Plan

> Status: Entwurf
>
> **Freigabevermerk:** offen. Der Plan ist erst ausführbar, wenn die Spec den Approval-Marker (`Status: APPROVED`) trägt; der Marker wird nur vom Nutzer bzw. `concept-reviewer` gesetzt, nie vom Planer.

**Goal:** Der Opencode-Einstiegspunkt funktioniert auf Surface v1 und v2: die explizit deklarierte `primary-role` wird als `mode: primary` generiert, `default_agent` wird per Managed-Merge (eigener State-Key, Rollback) in eine bestehende `opencode.json` geschrieben, der Edit-/Bash-Deny des Permission-Tier-Gates wird an diesen Einstiegspunkt gekoppelt, und der primäre Orchestrator hebelt das Gate nicht per `edit: allow` aus. Mammouth und jeder Provider ohne explizites `primary-role` bleiben byte-identisch.
**Architecture:** Neuer Helper `providers.explicit_primary_role` (kein Code-Default) als einzige Quelle für die Mode-Ableitung (`provider_transform`) und den Einstiegspunkt im Merge (`isolation._opencode_entry_point`); `_sync_opencode_runtime_gate` bekommt `active_set`, einen zweiten State-Namespace `default-agent` und die Gate-Kopplung; die Edit-Sperre des Primär-Orchestrators wird im Transform (`deny_edit`/`edit_allow_paths`) aus `config/provider-tools.yaml` gespeist. Create-Pfad (`context.py`) und v1-Settings-Template bleiben unverändert.
**Tech Stack:** Python 3.9/3.11/3.12 (Stdlib + PyYAML), pytest, Bash-Szenarien (`tests/scenarios/run.sh`), YAML-Config.
**Spec:** `docs/specs/2026-10-22-opencode-entrypoint-1006-spec.md`
**Spec-ID:** `spec-id: SPEC-OPENCODE-ENTRYPOINT-1006-2026-10-22` (Rev. 1.2, Entwurf; Reviews `docs/reviews/2026-10-22-opencode-entrypoint-1006-spec-review.md`, `docs/reviews/2026-10-22-opencode-entrypoint-1006-spec-rereview.md`)
**Tracking:** #1006 (Folgearbeit Opencode v2: #1007, eigener Plan B)

## Entry-/Exit-Kriterien

**Entry (alle erfüllt, bevor Task 1 startet):**
1. Nutzer gibt die Spec frei (`Status: APPROVED` in `docs/specs/2026-10-22-opencode-entrypoint-1006-spec.md`).
2. Nutzer bestätigt OQ-3 (ADR-5): Option B (scoped allow-list `.tmp/**` + `.meta-viz/**`, Default) oder A (Skalar `deny`). Bei A wird in Task 8 `opencode_primary_edit_allow: []` gesetzt (keine Code-Änderung); der Plan bleibt sonst unverändert.
3. Arbeitsbranch nach `.claude/rules/branch-guard.md`: `fix/1006-opencode-entry-point` (angelegt durch den `git`-Agenten; Tasks laufen nicht auf `main`).
4. OQ-4 (Rollback bei Tier-Wechsel/Provider-Entfernung) ist als Folge-Issue entschieden (Default: Folge-Issue, nicht Teil dieses Plans).

**Exit (alle erfüllt, bevor der PR-Hand-off erfolgt):**
1. `python3 -m pytest tests -q` grün (keine `failed`/`error`), inklusive neu geschriebener und angepasster Tests (Task 15).
2. `python3 scripts/sync.py --validate` Exit 0 (Task 12, Task 15).
3. `tests/scenarios/run.sh` meldet für alle Szenarien `PASS` (Task 15).
4. AC-01-Rebaseline: genau 2 geänderte + 1 hinzugefügter Hash, Goldens `slimming-golden/` und `compact-golden/` unverändert (Task 11).
5. `CHANGELOG.md` enthält unter `## [Unreleased]` den Abschnitt `### Fixed` (Task 14); kein Version-Bump, kein Major.
6. Alle Checkboxen dieser Datei gesetzt (Ledger = Plan-Datei, Skill `plan-ledger`).

## Global Constraints

- **Task-Format (maschinenlesbar):** `### Task <n>: <Titel>`; zeilenverankerte Felder `**Agent:**`, `**Depends on:**` (nur Task-Nummern dieses Plans), `Files:`-Block mit je einer Zeile `- Create:`/`- Modify:` mit Pfad in Backticks; `Interfaces:` mit Produces/Consumes.
- Provider-agnostisch: Unterschiede nur über Config-Keys/Capability-Flags, nie `if provider == "Name"` (Skill `provider-agnostic`); neue Logzeilen in `scripts/lib` nennen keinen Provider-Literal (nur `{provider}`-Formatierung); `tests/test_provider_agnostic_dispatch.py` bleibt grün (wird in den Tasks 3, 6, 7, 8 mitgeprüft).
- Python-3.9-kompatibel (`from __future__ import annotations` ist in `providers.py`, `isolation.py`, `provider_transform.py` vorhanden; keine `match`-Statements, keine `X | Y` zur Laufzeit außerhalb von Annotationen); nur Stdlib + PyYAML.
- **Byte-Stabilität:** v1-Settings-Template (`templates/configs/OPENCODE.settings-template.json`) und `context.apply_settings_surface_shape` / `_init_provider_settings_json` bleiben unverändert (Nicht-Ziel, ADR-3). Mammouth-Artefakte ändern sich nicht (AC-01, AC-03).
- **Bekannte Rot-Phasen:** (1) `tests/test_ac01_render_identity.py` ist ab Task 3 absichtlich rot (Opencode-Orchestrator wechselt auf `mode: primary`) und wird erst in Task 11 rebaselined; die Per-Task-Testkommandos schließen diese Datei bis dahin aus. (2) Das Szenario `69-opencode-v2-surface` ist ab Task 6 absichtlich rot (`69-opencode-v2-surface.sh:141` `assert "default_agent" not in doc` scheitert, sobald der Merge auf v1 `default_agent` schreibt) und wird erst mit Task 10 wieder grün (Rot-Phase Task 6 → Task 10, analog AC-01). Ausnahme dokumentiert, keine frühere Szenario-Anpassung: die Tasks 6–9 führen keine Szenarien aus, Task 10 stellt den Assert um.
- Rebaselines (`tests/fixtures/ac01-baseline/hashes.json`) nur nach Diff-Review und mit Eintrag im Rebaseline-Log (Docstring von `tests/test_ac01_render_identity.py`); `tests/fixtures/slimming-golden/` und `tests/fixtures/compact-golden/` werden nicht angefasst.
- TDD: jeder Code-Task beginnt mit einem roten Test (Beobachtung vor/nach in der PR-Beschreibung). Ausnahme sind die explizit als „Charakterisierung“ markierten Tasks 1 und 4.
- Logmeldungen im Code: Englisch. Dokumente: Deutsch. Commit-Messages: Englisch, Conventional Commits, ≤ 72 Zeichen, Imperativ; Commit durch die per `auto_commit` freigeschaltete Rolle bzw. den Orchestrator, Push/Branch/PR nur `git`.
- Ausführung nach Skill `plan-ledger`: frischer Subagent je Task, zweistufiges Review (req → quality), **kein** `isolation: "worktree"`. Repo-Containment: Schreiben nur im Projektroot und `.tmp/`.
- Zeilenangaben sind Orientierung (Stand Branch `docs/opencode-v2-1006-plans`, 2026-10-22); maßgeblich sind die Symbole.
- Guard-Charakter: der Gate-Deny bleibt eine Convention boundary (`.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary`).

## Ausführungsmodell

- DAG: `1 ∥ 2 ∥ 4 ∥ 13` (= `parallel_group: g1`, ownership-disjunkt) → `2 → 3`; `2 → 5 → 6 → 7`; `(1, 3, 4, 5) → 8`; `3 → 9`; `(3, 6) → 10`; `(3, 6, 7, 8, 9) → 11`; `(7, 8) → 12`; `(3, 6, 7, 8, 9, 10, 11, 12, 13) → 14 → 15`.
- Alle übrigen Tasks laufen sequenziell in Nummernreihenfolge (gemeinsame Dateien: `provider_transform.py` 3/8, `isolation.py` 5/6/7, `tests/test_opencode_runtime_gate.py` 5/6/7, `tests/test_runtime_gate_wiring.py` 7, `config/provider-tools.yaml` 8, `config/ai-providers.yaml` 9). Parallel nur Gruppe `g1`; Disjunktheit nach `check_plan_file_overlap` (`scripts/lib/orchestration.py`) im Self-Review nachgewiesen.
- Plan B (Opencode v2) startet erst nach Merge dieses Plans (`context.py`/`isolation.py` werden dort ebenfalls berührt; Merge seriell, R-6 der Spec).
- Aufwand: Schätzung über `effort-estimator` (Textreferenz, nicht von diesem Plan berechnet).

## File Structure

**Create:**
- Create: `docs/analysis/2026-10-22-opencode-permission-precedence.md` — Evidenz zur Permission-Rangfolge (OQ-1) und Pfad-Semantik, Task 1
- Create: `tests/test_explicit_primary_role.py` — Tests für `explicit_primary_role` (IC-1), Task 2
- Create: `tests/test_opencode_primary_edit_lock.py` — Tests für die Edit-Sperre des Primär-Orchestrators (IC-3, AC-11), Task 8

**Modify (Code/Config):**
- Modify: `scripts/lib/providers.py` — `explicit_primary_role` (IC-1)
- Modify: `scripts/lib/provider_transform.py` — Mode-Ableitung (IC-2), `deny_edit`/`edit_allow_paths` (IC-3), Docstrings
- Modify: `scripts/lib/isolation.py` — `_STATE_DEFAULT_AGENT_KEY`, `_read_state`, `opencode_runtime_gate_wanted`, `_opencode_entry_point`, erweiterter `_sync_opencode_runtime_gate` (IC-4/5/6)
- Modify: `scripts/lib/sync_pipeline.py` — Aufrufer übergibt `active_set` (IC-7)
- Modify: `scripts/lib/cli_commands.py` — Aufrufer (`--test`-Pfad) übergibt `active_set` (IC-7)
- Modify: `scripts/lib/frontmatter.py` — nur falls Task 4 den Serializer als unzureichend belegt (bedingt)
- Modify: `config/provider-tools.yaml` — Schlüssel `opencode_primary_edit_allow` (IC-3)
- Modify: `config/ai-providers.yaml` — Kommentar am Opencode-`primary-role`, `orchestrator_hint` (IC-8)

**Modify (Tests/Fixtures):**
- Modify: `tests/test_transform_contracts.py` — v1-Primary-Test, Mammouth-/Kein-Default-Fälle (AC-02/03/04)
- Modify: `tests/test_agents_frontmatter.py` — Serializer-Charakterisierung (Task 4)
- Modify: `tests/test_opencode_runtime_gate.py` — State/Helper/Default-Agent/Gate-Kopplung, Fixture-Anpassung (AC-06…10, 13, 14)
- Modify: `tests/test_runtime_gate_wiring.py` — Fixture `primary-role`, Pipeline-Test ohne `primary-role`, `active_set`-Durchreichung (AC-10)
- Modify: `tests/test_orchestrator_hint_flag.py` — Opencode-Hint ohne `@orchestrator`
- Modify: `tests/scenarios/asserts/69-opencode-v2-surface.sh`, `tests/scenarios/registry.md` — v1-Einstiegspunkt (AC-15 b.1)
- Modify: `tests/test_ac01_render_identity.py`, `tests/fixtures/ac01-baseline/hashes.json` — Rebaseline (AC-01)

**Modify (generiert/Doku):**
- Modify: `.opencode/agents/orchestrator.md`, `opencode.json`, `.opencode/agent-meta-state.json` — Self-Sync (AC-12), Task 12
- Modify: `docs/specs/2026-09-30-provider-audit-opencode-v2.md`, `docs/specs/2026-09-30-provider-audit-opencode-v2-design.md`, `docs/specs/2026-10-03-admin-ui-opencode-surface-amendment.md` — OQ-8-Amendment A2 / Querverweise, Task 13
- Modify: `CHANGELOG.md` — `### Fixed`, Task 14

---
pipeline_stages:
  implement: 3
---

## Vorab-Verifikation

### Task 1: Permission-Rangfolge in Opencode verifizieren (Doku + optionale `opencode run`-Probe)
**Agent:** tester · **Issue:** #1006 · **AC:** AC-11 (Voraussetzung), OQ-1, R-1, R-2 · **parallel_group:** g1
**Depends on:** —
**Hintergrund:** Entscheidung 4 verlangt, die Permission-Rangfolge VOR der finalen edit-Änderung (Task 8) zu belegen. Doku-Beleg (Spec): „Agent permissions are merged with the global config, and agent rules take precedence“ (opencode.ai/docs/permissions, Abschnitt Agents; letzter passender Match gewinnt). **Unsicherheit:** das Laufzeitverhalten von Opencode 1.18.x ist nicht lokal belegt; die Probe benötigt Binary, Modell-Credentials und Netz und ist deshalb optional. Ohne Probe gilt der Doku-Beleg mit explizit markierter Restunsicherheit (R-1). **Zweite Unsicherheit (Pfad-Semantik):** die Doku definiert `*`/`?`, nicht `**`, und sagt nicht, ob `edit`-Patterns gegen relative oder absolute Pfade matchen (Beispiele mischen beides). Matcht Opencode absolut, greifen `.tmp/**`/`.meta-viz/**` nie und Option B degradiert stillschweigend zu A (fail-closed, kein Sicherheitsproblem, aber ADR-5-Ziel verfehlt).
**Files:**
- Create: `docs/analysis/2026-10-22-opencode-permission-precedence.md`
**Interfaces:** Produces Evidenzdokument mit Verdikt-Zeile `Verdikt: CONFIRMED_BY_DOC | CONFIRMED_BY_PROBE | CONTRADICTED` (Gate für Task 8) und eigener Zeile zur Pfad-Semantik; Consumes Opencode-Doku (opencode.ai/docs/permissions, opencode.ai/docs/agents, opencode.ai/docs/config), `docs/analysis/2026-09-30-provider-audit-runtime-consolidation.md:103` (v1 akzeptiert `default_agent`), optional ein installiertes `opencode`-Binary.
- [ ] Step 1: Verfügbarkeit prüfen: `command -v opencode && opencode --version`. Ergebnis (Pfad/Version oder „nicht installiert“) im Dokument unter `## Probe-Voraussetzungen` festhalten.
- [ ] Step 2: Doku-Quellen lesen (permissions, agents, config) und je ein wörtliches Zitat plus URL unter `## Doku-Beleg` ablegen: (a) Agent-Regeln haben Vorrang vor globaler Config, (b) letzter passender Match gewinnt, (c) Default-Agent muss ein primärer Agent sein, sonst Fallback auf `build`. Zusätzlich eine eigene Zeile `Pfad-Semantik edit-Patterns (relativ vs. absolut, `**`): belegt (Zitat + URL) | nicht belegt` unter `## Doku-Beleg`; „nicht belegt“ ist zulässig.
- [ ] Step 3 (nur wenn Binary + Credentials vorhanden, sonst überspringen und im Dokument „Probe nicht ausgeführt: <Grund>“ vermerken): Wegwerf-Verzeichnis `.tmp/opencode-probe/` anlegen mit `opencode.json` = `{"default_agent": "probe", "permission": {"edit": {"**": "deny"}}}` und `.opencode/agents/probe.md` (Frontmatter `mode: primary`, `permission: {edit: {"*": "deny", ".tmp/**": "allow"}}`). Ausführen: `cd .tmp/opencode-probe && opencode run "Create the files .tmp/ok.txt and blocked.txt, each containing the word ok"`. Beobachtung dokumentieren: `.tmp/ok.txt` vorhanden (⇒ relatives Matching mit `**` funktioniert; sonst Pfad-Semantik widerlegt, Option B wirkt faktisch wie A)? `blocked.txt` vorhanden? Zweite Variante mit Agent-Level `edit: allow` (Skalar) gegen globalen Deny: entsteht `blocked.txt`?
- [ ] Step 4: Verdikt festlegen und unter `## Ergebnis` als Zeile `Verdikt: <Wert>` eintragen: `CONFIRMED_BY_PROBE` (Probe stützt Doku), `CONFIRMED_BY_DOC` (keine Probe; Restunsicherheit inkl. Pfad-Semantik ausdrücklich genannt; reicht als Gate für Task 8), `CONTRADICTED` (Probe widerspricht der Doku). Bei `CONTRADICTED`: Task 8 NICHT starten, an den Orchestrator eskalieren (Folge: IC-3 wirkungslos, Gate sperrt dann auch Subagents; Entscheidung 4 neu bewerten, Folge-Issue). Ist die Pfad-Semantik „nicht belegt“, steht sie unter `## Ergebnis` als Restrisiko (Task 8 trägt sie als markierte Unsicherheit).
- [ ] Step 5: Prüfen: `Grep` nach `^Verdikt: (CONFIRMED_BY_DOC|CONFIRMED_BY_PROBE|CONTRADICTED)$` in der Datei liefert genau 1 Treffer; `.tmp/opencode-probe/` bleibt im Wegwerfbereich (nicht committen).
- [ ] Step 6: commit `docs: record opencode permission precedence verification`

## Paket A1 — Primary-Role-Helper und Mode-Ableitung (IC-1, IC-2)

### Task 2: `explicit_primary_role` ohne Code-Default bereitstellen
**Agent:** developer · **Issue:** #1006 · **AC:** AC-03, AC-04 (Grundlage) · **parallel_group:** g1
**Depends on:** —
**Files:**
- Modify: `scripts/lib/providers.py`
- Create: `tests/test_explicit_primary_role.py`
**Interfaces:** Produces `providers.explicit_primary_role(provider_config: dict, provider: str) -> str | None` (nur nicht-leerer `str`; sonst `None`; wirft nie); Consumes `provider_config[provider]["primary-role"]` (Registry-Form, wie `load_providers_config` sie liefert).
- [ ] Step 1: Test schreiben (fail) in `tests/test_explicit_primary_role.py` (Import `from scripts.lib.providers import explicit_primary_role, load_providers_config`; `REPO_ROOT = Path(__file__).resolve().parents[1]`): `test_returns_declared_role` (`{"P": {"primary-role": "orchestrator"}}` → `"orchestrator"`), `test_missing_provider_returns_none`, `test_entry_without_key_returns_none`, `test_non_dict_entry_returns_none` (`{"P": "x"}`), `test_non_str_or_empty_value_returns_none` (`5`, `["orchestrator"]`, `""`), `test_non_dict_registry_returns_none` (`None`, `[]`), `test_real_registry_opencode_explicit_mammouth_none` (`load_providers_config(REPO_ROOT)`: Opencode → `"orchestrator"`, Mammouth → `None`).
- [ ] Step 2: Test laufen lassen: `python3 -m pytest tests/test_explicit_primary_role.py -q` → Collection-Fehler `ImportError: cannot import name 'explicit_primary_role'` (`1 error`).
- [ ] Step 3: implementieren in `scripts/lib/providers.py` (nach `resolve_agent_meta_root`, vor `_apply_surface_format_selection`):
  ```python
  def explicit_primary_role(provider_config: dict, provider: str) -> str | None:
      """Declared ``primary-role`` of *provider* or ``None`` (no code default)."""
      entry = provider_config.get(provider) if isinstance(provider_config, dict) else None
      value = entry.get("primary-role") if isinstance(entry, dict) else None
      return value if isinstance(value, str) and value else None
  ```
- [ ] Step 4: Test (pass): `python3 -m pytest tests/test_explicit_primary_role.py -q` → `7 passed`.
- [ ] Step 5: commit `feat: add explicit_primary_role provider helper`

### Task 3: `mode: primary` für die explizite `primary-role` auf v1 und v2 ausgeben
**Agent:** developer · **Issue:** #1006 · **AC:** AC-02, AC-03, AC-04, AC-05, AC-15 (b.2)
**Depends on:** 2
**Files:**
- Modify: `scripts/lib/provider_transform.py`
- Modify: `tests/test_transform_contracts.py`
**Interfaces:** Produces `mode`-Ableitung im Zweig `mechanism in ('opencode-native', 'opencode-native-v2')` von `_apply_agent_transform`: v1/v2 + `role == explicit_primary_role(...)` → `'primary'`; sonst v2 → `'subagent'`, v1 → `None` (Fallback `subagent` bleibt in `_transform_frontmatter_for_opencode`); Consumes Task 2 `providers.explicit_primary_role`. Der Kimi-Zweig (`_primary_role = ….get('primary-role', 'orchestrator')`, `subagents-allowlist`) bleibt unverändert (Nicht-Ziel).
- [ ] Step 1: Tests schreiben (fail) in `tests/test_transform_contracts.py`: den bestehenden `test_opencode_native_v1_stays_subagent` ersetzen durch `test_opencode_native_v1_primary_role_emits_primary_others_subagent` (`_transform("Opencode", role="orchestrator")` → `mode == "primary"`; `role="developer"` → `"subagent"`); neu: `test_mammouth_without_primary_role_stays_subagent` (Vorbedingung `"primary-role" not in _PROVIDER_CONFIG["Mammouth"]`; `_transform("Mammouth", role="orchestrator")` → `"subagent"`), `test_mammouth_with_explicit_primary_role_emits_primary` (`copy.deepcopy(_PROVIDER_CONFIG)`, `config["Mammouth"]["primary-role"] = "orchestrator"`, `_transform("Mammouth", role="orchestrator", provider_config=config)` → `"primary"`), `test_opencode_native_v2_without_primary_role_emits_no_primary` (`_opencode_v2_config()`, `config["Opencode"].pop("primary-role")`, Orchestrator → `"subagent"`). Modul-Docstring (Zeilen 13-14) auf „v1 and v2“ anpassen.
- [ ] Step 2: Test laufen lassen: `python3 -m pytest tests/test_transform_contracts.py -q` → `3 failed` (v1-primary, mammouth-explicit, v2-ohne-key; `AssertionError: assert 'subagent' == 'primary'` bzw. `'primary' == 'subagent'`), übrige passed.
- [ ] Step 3: implementieren in `scripts/lib/provider_transform.py`: Import erweitern zu `from .providers import explicit_primary_role, resolve_frontmatter_strip_fields`; im Zweig (bisher `mode = None` / `if mechanism == 'opencode-native-v2': …`) ersetzen durch
  ```python
          # Entry point (#1006, OQ-8 amendment A2): only an EXPLICIT `primary-role`
          # yields `mode: primary`, on v1 and v2 alike; there is no code default.
          mode = None
          primary_role = explicit_primary_role(provider_config, provider)
          if primary_role is not None and role == primary_role:
              mode = 'primary'
          elif mechanism == 'opencode-native-v2':
              mode = 'subagent'
  ```
  Docstring-Einträge zu `frontmatter-mechanism: opencode-native(-v2)` und „Provider-level keys honoured here“ (Zeilen ≈ 341-347, 354-356) auf das neue Verhalten anpassen.
- [ ] Step 4: Test (pass): `python3 -m pytest tests/test_transform_contracts.py tests/test_explicit_primary_role.py tests/test_provider_agnostic_dispatch.py tests/test_agents_frontmatter.py tests/test_opencode_v2_surface.py tests/test_surface_version_selection.py tests/test_settings_depth_and_deny.py tests/test_provider_config_contracts.py -q` → alle passed (`0 failed`); `test_v1_settings_template_is_byte_identical` und `test_v1_settings_are_byte_identical` (AC-05) bleiben grün.
- [ ] Step 5: commit `fix: emit mode primary for explicit primary-role on opencode v1`

## Paket A2 — Serializer-Prüfung (IC-3 Voraussetzung)

### Task 4: Frontmatter-Serializer für verschachtelte `permission`-Mappings prüfen (Charakterisierung)
**Agent:** tester · **Issue:** #1006 · **AC:** AC-11 (Voraussetzung) · **parallel_group:** g1
**Depends on:** —
**Hintergrund:** `frontmatter._update_frontmatter_dict` serialisiert via `yaml.dump(..., default_flow_style=False, sort_keys=False)`; verschachtelte Mappings und der Schlüssel `"*"` (muss gequotet werden) sollten korrekt und in Einfügereihenfolge ausgegeben werden. Dieser Task belegt das, bevor Task 8 darauf aufbaut. Charakterisierungstest: er darf beim ersten Lauf grün sein; nur bei Rot wird `frontmatter.py` minimal korrigiert.
**Files:**
- Modify: `tests/test_agents_frontmatter.py`
- Modify: `scripts/lib/frontmatter.py`
**Interfaces:** Produces Test `test_update_frontmatter_dict_preserves_nested_permission_mapping_order` (Garantie: Rundlauf liefert dieselbe Struktur, Schlüsselreihenfolge `"*"` zuerst, kein Flow-Style); Consumes `scripts.lib.frontmatter._update_frontmatter_dict(content: str, updates: dict, removes: list | None = None) -> str` und `_parse_frontmatter_yaml`.
- [ ] Step 1: Test schreiben in `tests/test_agents_frontmatter.py` (Import `_update_frontmatter_dict`, `_parse_frontmatter_yaml` aus `scripts.lib.frontmatter` ergänzen): Eingabe `"---\nname: x\n---\nbody\n"`, `updates = {"permission": {"read": "allow", "edit": {"*": "deny", ".tmp/**": "allow", ".meta-viz/**": "allow"}, "bash": "deny"}}`. Asserts: (1) `_parse_frontmatter_yaml(out)["permission"]` == `updates["permission"]`; (2) `list(parsed["permission"]["edit"]) == ["*", ".tmp/**", ".meta-viz/**"]`; (3) `list(parsed["permission"]) == ["read", "edit", "bash"]`; (4) `"{" not in out.split("---")[1]` (kein Flow-Style); (5) der Body `body\n` steht unverändert nach dem Frontmatter.
- [ ] Step 2: Test laufen lassen: `python3 -m pytest tests/test_agents_frontmatter.py -q` → erwartet `passed` (Charakterisierung). Ist er rot: `frontmatter.py` minimal anpassen (nur die betroffene Ausgabe-Stelle), erneut laufen lassen, Abweichung im Task-Ergebnis berichten.
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_agents_frontmatter.py tests/test_transform_contracts.py -q` → `0 failed`.
- [ ] Step 4: commit `test: pin nested permission mapping frontmatter serialization`

## Paket A3 — Merge: State, Einstiegspunkt, default_agent, Gate-Kopplung (IC-4…IC-7)

### Task 5: State-Namespace `default-agent` und Einstiegspunkt-Helper bereitstellen
**Agent:** developer · **Issue:** #1006 · **AC:** AC-13 · **Depends on:** 2
**Files:**
- Modify: `scripts/lib/isolation.py`
- Modify: `tests/test_opencode_runtime_gate.py`
**Interfaces:** Produces `isolation._STATE_DEFAULT_AGENT_KEY = "default-agent"`; `_read_state(state_path, key)` liefert für `key in (_STATE_RUNTIME_GATE_KEY, _STATE_DEFAULT_AGENT_KEY)` ein `dict` (`{}` bei fehlend/ungültig), sonst `list`; `isolation.opencode_runtime_gate_wanted(config: dict, provider: str, agent_meta_root: Path, provider_config: dict) -> bool`; `isolation._opencode_entry_point(provider: str, provider_config: dict, active_set) -> str | None` (explizite `primary-role` UND generiert: `active_set is None` oder `role in active_set.roles`). `_opencode_runtime_gate_entries` und `_write_state` bleiben unverändert; Consumes Task 2 `providers.explicit_primary_role`.
- [ ] Step 1: Tests schreiben (fail) in `tests/test_opencode_runtime_gate.py` (Konstante `_DEFAULT_AGENT_KEY = isolation._STATE_DEFAULT_AGENT_KEY`; `types.SimpleNamespace` importieren): `test_default_agent_namespace_reads_as_dict` (fehlende Datei → `{}`; geschriebener Wert `{"value": "orchestrator", "prior": None}` → identisches dict), `test_default_agent_namespace_coexists_with_siblings` (AC-13: `isolation-deny`-Liste, `runtime-gate-deny`-dict und `default-agent`-dict schreiben; `default-agent` per leerem Wert entfernen → die beiden anderen unverändert; Sentinel `_agent-meta` vorhanden), `test_entry_point_requires_explicit_primary_role` (`{"Opencode": {}}` → `None`; `{"Opencode": {"primary-role": "orchestrator"}}` → `"orchestrator"`), `test_entry_point_respects_active_set` (`SimpleNamespace(roles=frozenset({"developer"}))` → `None`; mit `"orchestrator"` → `"orchestrator"`; `active_set=None` → `"orchestrator"`), `test_runtime_gate_wanted_mirrors_entries` (strict + Tier `permission` via `_write_caps` → `True`; advisory-Modus → `False`).
- [ ] Step 2: Test laufen lassen: `python3 -m pytest tests/test_opencode_runtime_gate.py -q` → Collection-Error der ganzen Datei (`1 error`; `AttributeError: module 'lib.isolation' has no attribute '_STATE_DEFAULT_AGENT_KEY'` beim Import, weil die Modul-Konstante `_DEFAULT_AGENT_KEY = isolation._STATE_DEFAULT_AGENT_KEY` schon bei der Collection ausgewertet wird; keine `failed/passed`-Zählung, auch die 9 bestehenden Tests laufen nicht). Alternative: Konstante lazy im Test lesen (z. B. in einem Fixture/Funktionskörper) — dann `5 failed, 9 passed`.
- [ ] Step 3: implementieren in `scripts/lib/isolation.py`: Konstante `_STATE_DEFAULT_AGENT_KEY = "default-agent"` neben `_STATE_RUNTIME_GATE_KEY` (Kommentar: Wert `{"value": <role>, "prior": <str | None>}`); in `_read_state` die dict-Bedingung auf `key in (_STATE_RUNTIME_GATE_KEY, _STATE_DEFAULT_AGENT_KEY)` erweitern (Docstring anpassen); nach `_opencode_runtime_gate_entries`:
  ```python
  def opencode_runtime_gate_wanted(config, provider, agent_meta_root, provider_config) -> bool:
      return bool(_opencode_runtime_gate_entries(config, provider, agent_meta_root, provider_config))

  def _opencode_entry_point(provider, provider_config, active_set):
      role = providers.explicit_primary_role(provider_config, provider)
      if role is None:
          return None
      if active_set is not None and role not in active_set.roles:
          return None
      return role
  ```
  (mit den Typannotationen aus der Interfaces-Zeile und Docstrings nach IC-4; `active_set.has(role)` statt `role in active_set.roles` ist gleichwertig, `active_set.py:66`).
- [ ] Step 4: Test (pass): `python3 -m pytest tests/test_opencode_runtime_gate.py -q` → `14 passed` (9 bestehend + 5 neu).
- [ ] Step 5: commit `feat: add default-agent state namespace and entry point helpers`

### Task 6: `default_agent` im Managed-Merge schreiben (State, Idempotenz, Rollback, Warnung)
**Agent:** senior-developer · **Issue:** #1006 · **AC:** AC-06, AC-07, AC-08, AC-09, AC-14 · **Depends on:** 5
**Files:**
- Modify: `scripts/lib/isolation.py`
- Modify: `tests/test_opencode_runtime_gate.py`
**Interfaces:** Produces `_sync_opencode_runtime_gate(project_root: Path, config: dict, provider: str, provider_config: dict, agent_meta_root: Path, log: SyncLog, dry_run: bool, active_set=None) -> None` (neuer optionaler Parameter, rückwärtskompatibel); interner Helper `_merge_default_agent(existing: dict, desired: str | None, st: dict, gate_effective: bool, provider: str, log: SyncLog) -> dict` (mutiert `existing["default_agent"]`, gibt den neuen State-Wert zurück; `{}` entfernt den Namespace); Konstante `_DEFAULT_AGENT_JSON_KEY = "default_agent"`. Logik 1:1 nach IC-6 Schritt 3: `desired and not st`: `current is None` → schreiben + `{"value": d, "prior": None}`; `current == d` → nichts schreiben + `{"value": d, "prior": d}`; sonst Warnung ohne State. `desired and st`: `current == st["value"]` → bei `d != value` nachziehen (`prior` bleibt), sonst idempotent; `current != st["value"]` → Warnung, State bleibt. `desired is None and st`: `current == st["value"]` → `prior is None` ⇒ Key entfernen, sonst `prior` zurückschreiben; Nutzerwert bei Abweichung belassen; Namespace in beiden Fällen entfernt. Ein State ohne `str`-`value` gilt als „kein State“. Warntext (stabil, ein Satz, Provider nur als `{provider}`): `default_agent is '<user>' but the entry point role is '<role>'; leaving the user value untouched` plus — nur bei `gate_effective` — ` — the runtime gate is active, so '<user>' is locked: set default_agent to '<role>' or disable strict for this provider via orchestrator.provider-overrides`. Der Gate-Deny-Zweig bleibt in diesem Task unverändert (Kopplung: Task 7); `gate_effective = bool(entries)`. Consumes Task 5 (`_opencode_entry_point`, `_STATE_DEFAULT_AGENT_KEY`).
- [ ] Step 1: Tests schreiben (fail) in `tests/test_opencode_runtime_gate.py` (Helfer `_pc(primary=True)` → `{"Opencode": {"has_hooks": False, "primary-role": "orchestrator"}}` bzw. ohne Key; Helfer `_sync(project_root, framework, config, pc, log, active_set=None, dry_run=False)` ruft `isolation._sync_opencode_runtime_gate(..., active_set=active_set)`): 
  1. `test_default_agent_written_with_state_and_idempotent` (AC-06): bestehendes `opencode.json` ohne Key, strict → `data["default_agent"] == "orchestrator"`, State `default-agent == {"value": "orchestrator", "prior": None}`, zweiter Lauf byte-identisch (JSON und State).
  2. `test_differing_user_default_agent_not_overwritten_warns` (AC-07): `"default_agent": "build"`, strict → bleibt `"build"`, kein `default-agent`-State, genau eine Warnung mit `build`, `orchestrator`, `provider-overrides`; Gate-Deny (`permission.edit["**"] == "deny"`) wird trotzdem geschrieben. Zweite Variante ohne strict: genau eine Warnung mit `build`/`orchestrator`, die `provider-overrides` NICHT enthält.
  3. `test_same_user_default_agent_records_prior_and_survives_rollback` (AC-08): Nutzerwert `"orchestrator"` → keine Dateiänderung am JSON, State `{"value": "orchestrator", "prior": "orchestrator"}`; Sync ohne `primary-role` → Wert bleibt stehen, Namespace entfernt.
  4. `test_default_agent_rollback_removes_key_when_prior_none` (AC-09): erst Sync mit, dann ohne `primary-role` → Key entfernt, Namespace weg, Nutzer-Keys (z. B. `"theme": "x"`) und Namespace `runtime-gate-deny`/`isolation-deny` unberührt.
  5. `test_default_agent_rollback_keeps_user_changed_value` (AC-09): nach verwaltetem Schreiben `default_agent` im JSON auf `"build"` ändern → Sync ohne `primary-role` lässt `"build"`, Namespace entfernt.
  6. `test_default_agent_follows_changed_primary_role`: State `value=orchestrator`, `current=orchestrator`, `pc["Opencode"]["primary-role"] = "developer"` → `default_agent == "developer"`, `prior` unverändert `None`.
  7. `test_user_deleted_default_agent_is_not_rewritten_warns`: verwaltet geschrieben, Key aus JSON gelöscht → nicht neu geschrieben, Warnung, State bleibt.
  8. `test_inactive_primary_role_gets_no_default_agent`: `active_set=SimpleNamespace(roles=frozenset({"developer"}))` → kein `default_agent`, kein Namespace.
  9. `test_unparseable_opencode_json_is_left_untouched` (AC-14): Inhalt `"{not json"` → Bytes unverändert, keine State-Datei, mindestens eine Warnung.
  10. `test_dry_run_with_primary_role_never_writes` (AC-14): `dry_run=True` → weder `opencode.json` noch State angelegt.
- [ ] Step 2: Test laufen lassen: `python3 -m pytest tests/test_opencode_runtime_gate.py -q` → `10 failed` (alle 10 neuen Tests, auch 9 und 10, scheitern mit `TypeError: _sync_opencode_runtime_gate() got an unexpected keyword argument 'active_set'`, weil der Helfer `_sync` immer `active_set=` übergibt), 14 bestehende passed. Ab diesem Task ist das Szenario 69 rot (`:141`, siehe Global Constraints „Bekannte Rot-Phasen“) bis Task 10.
- [ ] Step 3: implementieren in `scripts/lib/isolation.py`: Signatur um `active_set=None` erweitern; nach dem Laden von `existing`/`state` (a) `entry = _opencode_entry_point(provider, provider_config, active_set)`, (b) `da_state = _read_state(state_path, _STATE_DEFAULT_AGENT_KEY)`, `before = existing.get("default_agent")`, (c) `new_da_state = _merge_default_agent(existing, entry, da_state, bool(entries), provider, log)` (nach Berechnung von `entries`); nach dem Schreiben von `opencode.json`: `if new_da_state != da_state: _write_state(state_path, new_da_state, dry_run, _STATE_DEFAULT_AGENT_KEY)`; `log.action("WRITE", …)`-Text um `, default_agent` ergänzen, wenn `existing.get("default_agent") != before`. Docstring der Funktion auf beide Namespaces und die Rollback-Regeln erweitern.
- [ ] Step 4: Test (pass): `python3 -m pytest tests/test_opencode_runtime_gate.py tests/test_runtime_gate_wiring.py tests/test_provider_agnostic_dispatch.py -q` → alle passed (`24` in `test_opencode_runtime_gate.py`).
- [ ] Step 5: commit `fix: merge default_agent into existing opencode.json with rollback`

### Task 7: Gate-Deny an den Einstiegspunkt koppeln, Aufrufer anpassen, bestehende Tests umstellen
**Agent:** senior-developer · **Issue:** #1006 · **AC:** AC-10, AC-15 (b.3, b.4) · **Depends on:** 6
**Files:**
- Modify: `scripts/lib/isolation.py`
- Modify: `scripts/lib/sync_pipeline.py`
- Modify: `scripts/lib/cli_commands.py`
- Modify: `tests/test_opencode_runtime_gate.py`
- Modify: `tests/test_runtime_gate_wiring.py`
**Interfaces:** Produces Gate-Kopplung in `_sync_opencode_runtime_gate`: ist `entries` nicht leer und `entry is None`, wird `entries = {}` gesetzt (der vorhandene Rollback-Zweig nimmt einen verwalteten Deny zurück) und `log.warning(...)` mit Text `runtime gate (permission.edit/bash deny) NOT written for provider '{provider}': no explicit and generated primary-role — the gate would lock every agent; declare primary-role in config/ai-providers.yaml and keep that role in the active set` ausgegeben; Aufrufer `sync_pipeline._sync_stage_per_provider` und `cli_commands` (`--test`-Pfad) übergeben `active_set=active_set`; Test-Helfer `_provider_config(has_plugins=False, primary_role="orchestrator")` und `_run_per_provider(..., active_set=None, log=None, primary_role="orchestrator")`. Consumes Task 6.
- [ ] Step 1: Tests schreiben/anpassen (fail):
  - `tests/test_opencode_runtime_gate.py`: alle Fixtures, die einen Deny erwarten (`test_scalar_permission_family_tolerated`, `test_prior_user_value_recorded_and_restored`, `test_second_strict_sync_is_idempotent_and_byte_identical`, `test_isolation_and_runtime_gate_coexist` (Opencode-Eintrag), `test_dry_run_never_writes`, `test_absent_config_is_created_with_managed_block`) bekommen `"primary-role": "orchestrator"` im Opencode-Eintrag; `test_absent_config_is_created_with_managed_block` erwartet exakt `{"permission": {"edit": {"**": "deny"}, "bash": {"**": "deny"}}, "default_agent": "orchestrator"}`. Neu: `test_strict_without_primary_role_writes_no_deny_and_warns` (AC-10: kein `permission.edit["**"]`/`bash["**"]`, kein `default_agent`, genau eine Warnung mit `primary-role`), `test_strict_with_inactive_primary_role_writes_no_deny` (`active_set` ohne Rolle), `test_managed_deny_rolled_back_when_entry_point_disappears` (erst Sync mit `primary-role` → Deny + `default_agent`; dann ohne → Prior je Familie wiederhergestellt bzw. `**` entfernt, `default_agent` entfernt, Namespaces `runtime-gate-deny` und `default-agent` entfernt, Warnung), `test_strict_with_primary_role_writes_deny_and_default_agent` (AC-10 positiver Fall).
  - `tests/test_runtime_gate_wiring.py`: `_provider_config(...)` und `_run_per_provider(...)` um die genannten Parameter erweitern (`pc["primary-role"] = primary_role` nur wenn nicht `None`; übergebenes `log`/`active_set` an `_sync_stage_per_provider` durchreichen); `test_strict_sync_writes_mapping_deny` und `test_single_provider_strict_writes_deny` zusätzlich `data["default_agent"] == "orchestrator"`; neu: `test_strict_without_primary_role_writes_no_deny_and_warns` (Pipeline-Ebene: `primary_role=None`, `tier="permission"`, strict → kein `permission`-Deny in einer ggf. vorhandenen `opencode.json`, `log.warnings` enthält `primary-role`), `test_gate_writer_receives_active_set` (`record_writer=True`, Sentinel `SimpleNamespace(roles=frozenset({"orchestrator"}))` → `writer_calls[0][1]["active_set"] is sentinel`).
- [ ] Step 2: Test laufen lassen: `python3 -m pytest tests/test_opencode_runtime_gate.py tests/test_runtime_gate_wiring.py -q` → `5 failed` (3 Kopplungstests in `test_opencode_runtime_gate.py`, 2 neue in `test_runtime_gate_wiring.py`), übrige passed.
- [ ] Step 3: implementieren: in `isolation._sync_opencode_runtime_gate` direkt nach der Berechnung von `entry` und `entries`: `if entries and entry is None: log.warning(<Text oben>); entries = {}`; `gate_effective` für `_merge_default_agent` bleibt `bool(entries)` (nach der Kopplung). In `scripts/lib/sync_pipeline.py` (Aufruf bei `provider_runtime_gate_tier(pc, caps) == "permission"`) und `scripts/lib/cli_commands.py` (gleiche Bedingung im `--test`-Pfad) `active_set=active_set` als Keyword ergänzen (Variable ist in beiden Scopes vorhanden). Danach mit `Grep` `pattern: _sync_opencode_runtime_gate\(` über `scripts/` bestätigen: genau 2 Aufrufer, beide mit `active_set=`.
- [ ] Step 4: Test (pass): `python3 -m pytest tests/test_opencode_runtime_gate.py tests/test_runtime_gate_wiring.py tests/test_provider_agnostic_dispatch.py tests/test_context_file_modes.py -q` → alle passed (`28` in `test_opencode_runtime_gate.py`, `12` in `test_runtime_gate_wiring.py`).
- [ ] Step 5: commit `fix: couple opencode runtime gate deny to explicit entry point`

## Paket A4 — Edit-Sperre des Primär-Orchestrators (IC-3)

### Task 8: `edit: allow` des primären Orchestrators unter aktivem Gate durch Sperre ersetzen
**Agent:** developer · **Issue:** #1006 · **AC:** AC-11 · **Depends on:** 1, 3, 4, 5
**Gate:** Start nur, wenn Task 1 das Verdikt `CONFIRMED_BY_DOC` oder `CONFIRMED_BY_PROBE` trägt; bei `CONTRADICTED` abbrechen und eskalieren (Entscheidung 4 neu bewerten).
**Unsicherheit (markiert):** Die Rangfolge (Agent-Regeln vor Global) ist per Doku belegt; ohne Probe bleibt ein Restrisiko (R-1). Die Pfad-Semantik der allow-list (`**`, relativ vs. absolut) ist ohne Task-1-Probe unbelegt; Worst Case: `.tmp/**`/`.meta-viz/**` greifen nie und Option B degradiert stillschweigend zu A (fail-closed). Mitigation: `deny_edit` ist ein Parameter und per Config (`opencode_primary_edit_allow`) ausgestaltbar; OQ-3 (Option A vs. B) liegt beim Nutzer — dieser Task implementiert B und kann per `opencode_primary_edit_allow: []` auf A schalten.
**Files:**
- Modify: `scripts/lib/provider_transform.py`
- Modify: `config/provider-tools.yaml`
- Create: `tests/test_opencode_primary_edit_lock.py`
**Interfaces:** Produces `_transform_frontmatter_for_opencode(content, name, description, model, steps, generated_from, agent_meta_root, temperature="", strip_fields=None, quiet_fields=None, mode=None, subagent_depth=None, deny_edit: bool = False, edit_allow_paths: tuple[str, ...] = ()) -> str`: nur bei `deny_edit=True` UND `perms.get("edit") == "allow"` wird dieser Wert durch `"deny"` (leere `edit_allow_paths`) bzw. `{"*": "deny", <p1>: "allow", …}` (`"*"` zuerst) ersetzt, Schlüsselreihenfolge der übrigen Permissions unverändert; jeder andere Wert bleibt unverändert — insbesondere steht `edit` dank `opencode_deny_critical: [Bash, Write, Edit]` für Rollen ohne `Write`/`Edit` immer als `"deny"` im Mapping (`provider_transform.py:746-749`) und wird NICHT durch die allow-list erweitert (kein Rechtegewinn durch einen Sperr-Mechanismus); Default-Aufruf byte-identisch zu vorher; Config-Schlüssel `opencode_primary_edit_allow: [".tmp/**", ".meta-viz/**"]` in `config/provider-tools.yaml`; Aufrufstelle im Opencode-Zweig von `_apply_agent_transform`: `deny_edit = mode == 'primary' and opencode_runtime_gate_wanted(config, provider, agent_meta_root, provider_config)` mit Lazy-Import `from .isolation import opencode_runtime_gate_wanted` innerhalb der Funktion (einziger Lazy-Import), `edit_allow_paths` = nicht-leere `str`-Einträge der Liste aus `load_provider_tools_config(agent_meta_root).get("opencode_primary_edit_allow")` (Nicht-Liste ⇒ `()`). `_map_claude_tools_to_opencode_permissions` bleibt unverändert (liefert weiterhin `dict[str, str]`; die Erweiterung auf verschachtelte Werte geschieht erst im Transform, Abweichung von der Spec-Formulierung „Rückgabetyp erweitert“ ohne Verhaltensunterschied). Consumes Task 3 (`mode`), Task 4 (Serializer-Garantie), Task 5 (`opencode_runtime_gate_wanted`).
- [ ] Step 1: Tests schreiben (fail) in `tests/test_opencode_primary_edit_lock.py` (Aufbau wie `tests/test_transform_contracts.py::_transform`: `transform_agent_content_for_provider(content, provider, role, role, "desc", "1-generic/orchestrator.md@0.101.0", project_config, REPO_ROOT, REPO_ROOT, target_path, provider_config, SyncLog())`; Inhalt mit `tools: [Read, Bash, Grep, Write]`; `STRICT = {"orchestrator": {"mode": "strict"}}`; echte Registry via `load_providers_config(REPO_ROOT)`):
  1. `test_primary_orchestrator_edit_is_scoped_under_active_gate` (AC-11): `STRICT`, Rolle `orchestrator` → `permission.edit == {"*": "deny", ".tmp/**": "allow", ".meta-viz/**": "allow"}` und `list(permission["edit"]) == ["*", ".tmp/**", ".meta-viz/**"]`.
  2. `test_empty_allow_list_falls_back_to_scalar_deny`: `monkeypatch.setattr("scripts.lib.provider_transform.load_provider_tools_config", lambda root: {**real, "opencode_primary_edit_allow": []})` (`real = load_provider_tools_config(REPO_ROOT)` vorab) → `permission.edit == "deny"`.
  3. `test_no_lock_without_strict`: `project_config={}` → `permission.edit == "allow"`.
  4. `test_no_lock_for_non_primary_role`: `STRICT`, Rolle `developer` → `"allow"`.
  5. `test_no_lock_when_tier_is_not_permission`: Kopie der Registry mit `config["Opencode"].update(has_hooks=True, hook_protocol="claude-code-json")`, `STRICT` → `"allow"`.
  6. `test_other_permissions_unchanged_under_lock`: `STRICT`-Render vs. Nicht-Strict-Render: alle Schlüssel außer `edit` gleich (inkl. `bash`, `task`, `read`, `todowrite`, Reihenfolge), und `locked["edit"] != "allow"`.
  7. `test_role_without_write_tool_keeps_edit_deny_under_lock`: Inhalt mit `tools: [Read]`, `STRICT`, Rolle `orchestrator` → `permission["edit"] == "deny"` (Skalar, stammt aus `opencode_deny_critical`; KEINE Erweiterung zum allow-list-Mapping — Regressionsschutz gegen Rechtegewinn).
  8. `test_default_call_is_byte_identical`: `_transform_frontmatter_for_opencode(..., deny_edit=False)` == Aufruf ohne die neuen Parameter.
- [ ] Step 2: Test laufen lassen: `python3 -m pytest tests/test_opencode_primary_edit_lock.py -q` → `4 failed, 4 passed` (Tests 1, 2, 6, 8 rot: `assert 'allow' == {...}` bzw. `TypeError: … unexpected keyword argument 'deny_edit'`; Tests 3, 4, 5 und 7 laufen vorab grün — Test 7, weil `edit == "deny"` für Rollen ohne Write-Tool bereits im Bestand aus `opencode_deny_critical` stammt; er bleibt nach der Implementierung grün und fängt eine fehlerhafte unbedingte Ersetzung ab).
- [ ] Step 3: implementieren: `config/provider-tools.yaml` direkt nach `opencode_deny_critical` einfügen:
  ```yaml
  # Write scope of the primary orchestrator while the Opencode runtime gate is
  # active (#1006): permission.edit becomes {"*": deny, <path>: allow, ...}.
  # An empty list yields the scalar `edit: deny`.
  opencode_primary_edit_allow:
    - .tmp/**
    - .meta-viz/**
  ```
  In `scripts/lib/provider_transform.py`: Parameter `deny_edit`/`edit_allow_paths` an `_transform_frontmatter_for_opencode` ergänzen (Docstring: Verhalten + „closed by default“), Anwendung nach der Berechnung von `perms` (Kopie via `perms = dict(perms)`, dann den Wert von `"edit"` NUR ersetzen, wenn `perms.get("edit") == "allow"`); Aufrufstelle im Opencode-Zweig von `_apply_agent_transform` wie in `Interfaces`. Falls Option A durch den Nutzer gewählt wurde: Liste auf `[]` setzen und Test 1 entsprechend auf den Skalar umstellen.
- [ ] Step 4: Test (pass): `python3 -m pytest tests/test_opencode_primary_edit_lock.py tests/test_transform_contracts.py tests/test_agents_frontmatter.py tests/test_provider_agnostic_dispatch.py tests/test_provider_matrix_sync.py -q` → alle passed (`8 passed` in der neuen Datei).
- [ ] Step 5: commit `fix: lock edit for primary orchestrator while gate is active`

## Paket A5 — Config, Szenario, Rebaseline, Self-Sync

### Task 9: Opencode-`primary-role`-Kommentar und `orchestrator_hint` korrigieren
**Agent:** developer · **Issue:** #1006 · **AC:** AC-15 (a) · **Depends on:** 3
**Hintergrund:** `orchestrator_hint` ist ein unrendered Wert (`ORCHESTRATOR_INVOCATION_HINT` wird in `scripts/lib/context.py` und `scripts/lib/rules.py` nur zugewiesen, in keinem Template verwendet; `tests/test_context_file_modes.py` führt ihn als `_UNRENDERED_PROVIDER_SCOPED`) — die Änderung ist AC-01-neutral.
**Files:**
- Modify: `config/ai-providers.yaml`
- Modify: `tests/test_orchestrator_hint_flag.py`
**Interfaces:** Produces Kommentar am Key `primary-role` (Opencode) und neuen Hint-Text; Consumes Task 3.
- [ ] Step 1: Test schreiben (fail) in `tests/test_orchestrator_hint_flag.py`: `test_opencode_orchestrator_hint_names_default_agent_not_mention` → `hint = _orchestrator_hints()["Opencode"]`; `"@orchestrator" not in hint` und `"Default" in hint`.
- [ ] Step 2: Test laufen lassen: `python3 -m pytest tests/test_orchestrator_hint_flag.py -q` → `1 failed` (`assert '@orchestrator' not in …`), 2 passed.
- [ ] Step 3: implementieren in `config/ai-providers.yaml`: (a) über `primary-role: orchestrator` (Opencode) den Kommentar `# v1 and v2 emit this role as `mode: primary` and write it as `default_agent`; without this key `primary` is never emitted (#1006, OQ-8 amendment A2).`; den bestehenden Kommentar (Zeilen ≈ 236-239, „PRE-3/OQ-4: orchestrator is emitted as mode: primary“) nicht widersprüchlich lassen; (b) `orchestrator_hint` des Opencode-Eintrags: `'- **In Opencode (VS Code):** Der `orchestrator` ist der Default-Agent (mit Tab wechseln); `@orchestrator` ist nicht mehr nötig.'`. Mammouth bekommt bewusst KEIN `primary-role` (nicht anfassen).
- [ ] Step 4: Test (pass): `python3 -m pytest tests/test_orchestrator_hint_flag.py tests/test_provider_config_contracts.py tests/test_context_file_modes.py tests/test_surface_version_selection.py -q` → alle passed.
- [ ] Step 5: commit `chore: document opencode primary entry and fix orchestrator hint`

### Task 10: Szenario 69 für den v1-Einstiegspunkt anpassen
**Agent:** tester · **Issue:** #1006 · **AC:** AC-15 (b.1) · **Depends on:** 3, 6
**Files:**
- Modify: `tests/scenarios/asserts/69-opencode-v2-surface.sh`
- Modify: `tests/scenarios/registry.md`
**Interfaces:** Produces Teil 1b prüft auf v1: `doc["default_agent"] == "orchestrator"` und `.opencode/agents/orchestrator.md` `mode: primary` (in `$PROJ_UNSET`); das `cmp`-Paar `unset`/`v1` und die Flat-`mcp`-Prüfung bleiben; Consumes Task 3, Task 6. Beendet die Rot-Phase des Szenarios 69 (seit Task 6, `69-opencode-v2-surface.sh:141`).
- [ ] Step 1: Assert anpassen (fail-first): in `tests/scenarios/asserts/69-opencode-v2-surface.sh` Zeile `assert "default_agent" not in doc, …` (≈ 141; seit Task 6 rot) ersetzen durch `assert doc.get("default_agent") == "orchestrator", "v1 must carry default_agent from the explicit primary-role (#1006)"`; nach dem Python-Block einen weiteren Block ergänzen, der `"$PROJ_UNSET/.opencode/agents/orchestrator.md"` einliest und `mode: primary` verlangt (Parser wie im Teil 2c), sowie für `developer.md` `mode: subagent`. Kopfkommentar (Zeilen ≈ 20-23 „… no `default_agent`“) und Teil-1b-Beschreibung auf „flat `mcp` shape frozen; entry point (`mode: primary` + `default_agent`) emitted on v1 as well (#1006)“ umformulieren; den Abschluss-`echo` unverändert lassen.
- [ ] Step 2: `tests/scenarios/registry.md` Zeile `69-opencode-v2-surface` (≈ 116): Beschreibung um „v1/unset: flat `mcp` + entry point (`default_agent`, `mode: primary`)“ ergänzen.
- [ ] Step 3: Szenario laufen lassen: `tests/scenarios/run.sh 69` → Ausgabe `PASS` für `69-opencode-v2-surface` (Exit 0). Reihenfolge-Nachweis in der PR-Beschreibung: die Assert-Zeile `:141` war ab Task 6 rot (dokumentierte Rot-Phase) und wird hier umgestellt; Assert-Zeile in der PR zitieren.
- [ ] Step 4: commit `test: assert opencode v1 entry point in scenario 69`

### Task 11: AC-01-Baseline kontrolliert rebaselinen
**Agent:** tester · **Issue:** #1006 · **AC:** AC-01, AC-15 (b.5) · **Depends on:** 3, 6, 7, 8, 9
**Files:**
- Modify: `tests/fixtures/ac01-baseline/hashes.json`
- Modify: `tests/test_ac01_render_identity.py`
**Interfaces:** Produces Manifest mit genau den Änderungen `changed: Opencode/.opencode/agents/orchestrator.md` (nur `mode`), `changed: Opencode/opencode.json` (nur neuer Key `default_agent`), `added: Opencode/.opencode/agent-meta-state.json` (nur Namespace `default-agent` + Sentinel `_agent-meta`); Eintrag im Rebaseline-Log (Docstring); Consumes Tasks 3, 6, 7, 8, 9. Nicht angefasst werden: `tests/fixtures/slimming-golden/`, `tests/fixtures/compact-golden/`.
- [ ] Step 1: Drift beobachten (rot): `python3 -m pytest tests/test_ac01_render_identity.py -q` → `1 failed` mit Drift-Liste, die **exakt** diese drei Zeilen enthält: `changed: Opencode/.opencode/agents/orchestrator.md`, `changed: Opencode/opencode.json`, `added: Opencode/.opencode/agent-meta-state.json`. **Stop-Kriterium:** jede weitere Zeile (insbesondere `Mammouth/…`, ein anderer Provider, `Opencode/.meta-config/generated-file-hashes.json`, oder ein zusätzlicher Edit-Lock im Matrix-Orchestrator) ⇒ Rebaseline NICHT schreiben, Ursache klären und berichten (Matrixprojekt ist nicht strikt; kein `edit`-Deny erwartet).
- [ ] Step 2: Inhaltlich prüfen (Diff-Review, nicht blind): Matrix-Projekt in ein Wegwerfverzeichnis unter `.tmp/ac01-review/` rendern (`python3 scripts/sync.py --config <projekt>/.meta-config/project.yaml --init` analog `_make_project`) und bestätigen: `orchestrator.md` unterscheidet sich vom Vorstand nur in `mode: subagent` → `mode: primary`; `opencode.json` nur um `"default_agent": "orchestrator"`; State-Datei enthält nur `default-agent` + `_agent-meta`.
- [ ] Step 3: Rebaseline schreiben (begründete Ausnahme: Branch ist nicht `main`; Grund im Log): `python3 tests/test_ac01_render_identity.py --write` → Ausgabe `wrote N hashes to …/hashes.json` (N = alter Wert + 1). Rebaseline-Log-Eintrag im Docstring von `tests/test_ac01_render_identity.py` ergänzen: „Task 11 (#1006, OQ-8 amendment A2): Opencode entry point on v1 — orchestrator `mode: primary`, `default_agent` written by the managed merge, new `agent-meta-state.json` (`default-agent` namespace). Changed: `Opencode/.opencode/agents/orchestrator.md`, `Opencode/opencode.json`; added: `Opencode/.opencode/agent-meta-state.json` (2 changed, 1 added). `AC01_EXCEPTIONS` is NOT extended; Mammouth and all other providers unchanged.“
- [ ] Step 4: Diff-Nachweis: `git diff --stat tests/fixtures/ac01-baseline/hashes.json` → genau 3 Zeilen +/−: `2 deletions(-)` und `3 insertions(+)` (2 geänderte Hashes, 1 hinzugefügter); `git status --short tests/fixtures/slimming-golden tests/fixtures/compact-golden` → leere Ausgabe.
- [ ] Step 5: Test (pass): `python3 -m pytest tests/test_ac01_render_identity.py tests/test_template_slimming_equivalence.py tests/test_compact_matrix.py -q` → alle passed.
- [ ] Step 6: commit `test: rebaseline AC-01 hashes for opencode entry point`

### Task 12: Eigenes `opencode.json` per Self-Sync konvergieren lassen
**Agent:** developer · **Issue:** #1006 · **AC:** AC-12 · **Depends on:** 7, 8
**Files:**
- Modify: `.opencode/agents/orchestrator.md`
- Modify: `opencode.json`
- Modify: `.opencode/agent-meta-state.json`
**Interfaces:** Produces Repo-Stand mit funktionierendem Einstiegspunkt; Consumes Tasks 7, 8 (`.meta-config/project.yaml`: `orchestrator.strict: true`, `mode: strict`, `checkpointing: true`, `ai-providers` enthält `Opencode`).
- [ ] Step 1: Vorzustand sichern: `git status --short` muss sauber sein (außer eigenen Task-Änderungen); `Read` von `opencode.json` bestätigt: kein `default_agent`, `permission.edit["**"]` und `permission.bash["**"]` = `deny`.
- [ ] Step 2: `python3 scripts/sync.py` ausführen; danach `git diff -- opencode.json .opencode/` und `git status --short` prüfen. Erwartete Änderungen: (a) `.opencode/agents/orchestrator.md`: `mode: primary`, `permission.edit` = Mapping `'*': deny` / `.tmp/**: allow` / `.meta-viz/**: allow` bei Variante B (Default, OQ-3 / ADR-5; bei Variante A der Skalar `deny`; der Skalar `allow` entfällt in beiden Fällen), `bash: deny` unverändert; (b) `opencode.json`: neuer Key `"default_agent": "orchestrator"`, übrige Keys (`$schema`, `subagent_depth`, `plugin`, `mcp`, `permission.edit/bash["**"]="deny"`) unverändert; (c) `.opencode/agent-meta-state.json`: Namespace `runtime-gate-deny` unverändert, neu `default-agent` = `{"value": "orchestrator", "prior": null}` und der Sentinel `_agent-meta` (R-7: Repo-State war älter als #802). Weitere geänderte Dateien (z. B. Versions-/Datumszeilen in generierten Kontextdateien) sind **nicht** Teil dieses Tasks: im Ergebnis melden, nicht in den Commit aufnehmen.
- [ ] Step 3: Idempotenz: `git diff > .tmp/self-sync-1.diff`, `python3 scripts/sync.py`, `git diff > .tmp/self-sync-2.diff`, `cmp .tmp/self-sync-1.diff .tmp/self-sync-2.diff` → keine Ausgabe (identisch).
- [ ] Step 4: Validierung: `python3 scripts/sync.py --validate` → Exit 0.
- [ ] Step 5: commit (nur die drei Dateien) `chore: self-sync opencode entry point artifacts`

## Paket A6 — Doku und Abschluss

### Task 13: OQ-8-Amendment A2 und Querverweise dokumentieren
**Agent:** documenter · **Issue:** #1006 · **AC:** Spec „OQ-8-Amendment“ · **parallel_group:** g1
**Depends on:** —
**Files:**
- Modify: `docs/specs/2026-09-30-provider-audit-opencode-v2.md`
- Modify: `docs/specs/2026-09-30-provider-audit-opencode-v2-design.md`
- Modify: `docs/specs/2026-10-03-admin-ui-opencode-surface-amendment.md`
**Interfaces:** Produces Amendment-Text A2 (Wortlaut 1:1 aus dem Abschnitt „OQ-8-Amendment“ der Entrypoint-Spec) im Abschnitt `### OQ-8 — v1→v2 default flip` direkt nach der `DECISION (2026-10-01)`-Zeile, plus Zusatz in der Tabellenzeile OQ-8 (≈ Zeile 26: „; the entry point (`mode: primary` + `default_agent`) is excluded from the v1 freeze, see Amendment A2“); je ein einzeiliger Querverweis in `…-design.md` (OQ-8-Tabellenzeile ≈ 589) und `…admin-ui-opencode-surface-amendment.md` (≈ Zeilen 42 und 67); Consumes die Entrypoint-Spec.
- [ ] Step 1: Prüfung vor der Änderung: `Grep` `pattern: Amendment A2` über die drei Dateien → keine Treffer.
- [ ] Step 2: Amendment-Text einfügen (Blockquote `> **Amendment A2 (2026-10-22, Issue #1006):** …`; Referenz `SPEC-OPENCODE-ENTRYPOINT-1006-2026-10-22`); Status-/Approval-Marker der bearbeiteten Specs nicht verändern; Querverweise als eine Zeile `Siehe Amendment A2 (#1006) in docs/specs/2026-09-30-provider-audit-opencode-v2.md: Surface-Format bleibt frozen, Einstiegspunkt nicht.` Die Zeichenfolge „Amendment A2“ darf in `docs/specs/2026-09-30-provider-audit-opencode-v2.md` genau zweimal vorkommen: (1) im Blockquote-Kopf `> **Amendment A2 (2026-10-22, Issue #1006):**` und (2) im Zusatz der OQ-8-Tabellenzeile; keine weitere Erwähnung (Fließtext sonst „der Zusatz A2“ o. ä. vermeiden bzw. nur dort verwenden).
- [ ] Step 3: Prüfung: `Grep` `pattern: Amendment A2` mit `output_mode: count` → in `docs/specs/2026-09-30-provider-audit-opencode-v2.md` **genau 2 Treffer** (1× Blockquote-Kopf im Abschnitt OQ-8, 1× Zusatz in der OQ-8-Tabellenzeile) und je ≥ 1 Treffer in den beiden anderen Dateien; `python3 scripts/sync.py --validate` → Exit 0 (Spec-Plan-Validator toleriert die Änderungen).
- [ ] Step 4: commit `docs: add OQ-8 amendment A2 for opencode entry point`

### Task 14: CHANGELOG „Fixed“ eintragen
**Agent:** documenter · **Issue:** #1006 · **AC:** AC-16 · **Depends on:** 3, 6, 7, 8, 9, 10, 11, 12, 13
**Files:**
- Modify: `CHANGELOG.md`
**Interfaces:** Produces Abschnitt `### Fixed` unter `## [Unreleased]` mit dem Eintrag aus dem Abschnitt „CHANGELOG-Eintrag“ der Spec (Englisch, wörtlich, inkl. des Absatzes „Behavior change for all Opencode projects“); kein Version-Bump, kein `### Changed`/Major-Hinweis.
- [ ] Step 1: Prüfung vorher: `Read` von `CHANGELOG.md` Zeilen 1-5 → `## [Unreleased]` ist leer (direkt gefolgt von `## [2.0.0-beta.2]`).
- [ ] Step 2: Eintrag direkt unter `## [Unreleased]` einfügen (Leerzeile davor/danach, `### Fixed` + Bullet **Opencode entry point (#1006)** gemäß Spec).
- [ ] Step 3: Prüfung: `Grep` `pattern: Opencode entry point \(#1006\)` in `CHANGELOG.md` → genau 1 Treffer; `python3 scripts/sync.py --validate` → Exit 0 (CHANGELOG-Konventionen).
- [ ] Step 4: commit `docs: add changelog entry for opencode entry point fix`

### Task 15: Nachzügler-Suche und Gesamtverifikation
**Agent:** tester · **Issue:** #1006 · **AC:** AC-05, AC-12, AC-15 · **Depends on:** 14
**Files:**
- Modify: `docs/analysis/2026-10-22-opencode-permission-precedence.md`
**Interfaces:** Produces Nachzügler-Bericht (angehängt als Abschnitt `## Nachzügler-Suche #1006`), Exit-Nachweis; Consumes alle vorherigen Tasks.
- [ ] Step 1: Nachzügler-Grep (Ergebnis je Muster im Bericht festhalten; Treffer, die altes Verhalten festnageln und nicht in Tasks 3, 6-12 behandelt sind, werden als Befund gemeldet und per Folge-Fix im selben PR korrigiert): `Grep` über `tests/` und `scripts/` für `default_agent`, `mode: subagent`, `primary-role`, `edit: allow`, `"edit"\]`, `runtime-gate-deny`, `_sync_opencode_runtime_gate`, `mode == "subagent"`. Erwartet: keine ungeprüften Treffer außer (a) `tests/routing-llm-eval/provider-opencode.sh` (`sed 's/^mode: subagent$/mode: primary/'` ist jetzt ein No-Op, bleibt als harmloser Workaround), (b) `tests/test_opencode_v2_surface.py::test_v2_settings_without_primary_role_emits_no_default_agent` (Create-Pfad, unverändert), (c) Kimi-Zweig `provider_transform.py` (`.get('primary-role', 'orchestrator')`, Nicht-Ziel).
- [ ] Step 2: Unverändert-grün-Liste (AC-15 a): `python3 -m pytest tests/test_surface_version_selection.py tests/test_provider_config_contracts.py tests/test_settings_depth_and_deny.py tests/test_opencode_v2_surface.py tests/test_agents_frontmatter.py tests/test_artifact_contracts.py tests/test_surface_version_consistency.py -q` → alle passed.
- [ ] Step 3: Gesamtlauf: `python3 -m pytest tests -q` → `N passed` ohne `failed`/`error`; `python3 scripts/sync.py --validate` → Exit 0; `tests/scenarios/run.sh` → alle Szenarien `PASS`.
- [ ] Step 4: Mammouth-Beweis mit konkretem Basisbranch `main` (Branch-Diff, nicht Working-Tree-Diff): `git diff --stat main...HEAD -- tests/fixtures/ac01-baseline/hashes.json` zeigt keine `Mammouth/`-Zeile; Prüfung per `git diff main...HEAD -- tests/fixtures/ac01-baseline/hashes.json | grep -c Mammouth` → `0`.
- [ ] Step 5: commit (nur falls Nachzügler-Fixes oder Bericht-Änderungen entstanden) `test: record follow-up search and final verification for #1006`

## Self-Review

**Traceability AC → Task → Test**

| AC | Task | Test |
|---|---|---|
| AC-01 | 11 | `tests/test_ac01_render_identity.py` (+ Goldens unverändert: `test_template_slimming_equivalence.py`, `test_compact_matrix.py`) |
| AC-02, AC-03, AC-04 | 2, 3 | `tests/test_explicit_primary_role.py`, `tests/test_transform_contracts.py` |
| AC-05 | 3, 15 | `tests/test_opencode_v2_surface.py:204`, `tests/test_settings_depth_and_deny.py:85` (unverändert grün) |
| AC-06, AC-07, AC-08, AC-09, AC-14 | 6 | `tests/test_opencode_runtime_gate.py` (10 neue Tests) |
| AC-10 | 7 | `tests/test_opencode_runtime_gate.py`, `tests/test_runtime_gate_wiring.py` |
| AC-11 | 1, 4, 8 | `docs/analysis/2026-10-22-opencode-permission-precedence.md`, `tests/test_agents_frontmatter.py`, `tests/test_opencode_primary_edit_lock.py` |
| AC-12 | 12 | `sync.py`-Lauf, `cmp` der Diffs, `--validate` |
| AC-13 | 5 | `tests/test_opencode_runtime_gate.py` |
| AC-15 (a, b.1-b.5) | 3, 7, 10, 11, 15 | siehe Tasks |
| AC-16 | 14 | `Grep` + `--validate` |
| OQ-8-Amendment, `orchestrator_hint` | 13, 9 | `tests/test_orchestrator_hint_flag.py` |

**Checks**
- Jeder Task mappt auf genau eine Rolle (`developer`, `senior-developer`, `tester`, `documenter`); jedes Akzeptanzkriterium ist über Testkommando oder Grep/Diff messbar.
- `Files:`/`Interfaces:` vollständig; Parallelgruppe `g1` = {Task 1: `docs/analysis/…`; Task 2: `providers.py`, `test_explicit_primary_role.py`; Task 4: `test_agents_frontmatter.py`, (bedingt) `frontmatter.py`; Task 13: drei `docs/specs/*`-Dateien} ist dateidisjunkt. Alle übrigen Tasks laufen sequenziell, weil sie `provider_transform.py`, `isolation.py`, `tests/test_opencode_runtime_gate.py`, `tests/test_runtime_gate_wiring.py`, `config/provider-tools.yaml` oder `config/ai-providers.yaml` teilen. Nachweis per `spec_plan._parse_plan_tasks`/`validate_plan`/`check_plan_file_overlap` vor Ausführung.
- Alle genannten Pfade/Symbole wurden gegen den Stand von 2026-10-22 geprüft (u. a. `isolation._read_state`, `_write_state`, `_opencode_runtime_gate_entries`, `_sync_opencode_runtime_gate`; `provider_transform._apply_agent_transform`, `_transform_frontmatter_for_opencode`, `_map_claude_tools_to_opencode_permissions`; `frontmatter._update_frontmatter_dict`; `ActiveSet.roles`; `SyncLog.warning`); neu angelegte Symbole sind in `Interfaces` als Produces ausgewiesen.
- `pipeline_stages` deckt die einzige `plan-driven`-Stage `implement` ab (Frontmatter-Block oben).
- Keine Platzhalter; offene Punkte sind als Unsicherheit mit Default benannt (siehe unten).

**Annahmen / Unsicherheiten**
1. Permission-Rangfolge (R-1): per Doku belegt, Laufzeit nur per optionaler Probe (Task 1); Task 8 ist darauf gegated. Pfad-Semantik der allow-list (`**`, relativ/absolut) ist ebenfalls nur per Probe belegbar; ohne Beleg degradiert Option B im Worst Case fail-closed zu A (R-2).
2. OQ-3: Plan setzt Option B (scoped allow-list) um; Option A = `opencode_primary_edit_allow: []`.
3. OQ-4 (Rollback bei Tier-Wechsel/Provider-Entfernung) bleibt Folge-Issue; kein Task.
4. Warntexte sind Englisch (Code-Konvention); die deutsche Formulierung in AC-07 der Spec wird sinngemäß umgesetzt (Substring-Tests auf Nutzerwert, Rolle, `provider-overrides`).
5. Tests setzen voraus, dass das AC-01-Matrixprojekt nicht strikt ist (Reviewer-Befund); Task 11 Step 1 enthält ein Stop-Kriterium, falls nicht.
6. `write_checked` kann bei „nichts zu tun“ ein leeres `{}` anlegen (Bestandsverhalten, unverändert); der Wiring-Test in Task 7 prüft daher tolerant auf Existenz.
7. Re-Planning: nach Task 3 (erste Verhaltensänderung), nach Task 8 (Gate-Verdikt) und nach Task 11 (Rebaseline) Annahmen prüfen und den Plan aktualisieren, nicht einfrieren.
8. Plan-Ledger-Checkboxen (`rules/1-generic/plan-ledger.md:36-38`: Writer-Skript braucht `bash`, manueller Edit als Fallback) sind dem Opencode-Orchestrator unter Strict auch mit Option B nur via Subagent möglich (Spec R-2; akzeptiert oder Folge-Issue).
