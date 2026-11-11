---
pipeline_stages:
  implement: 1
status: DRAFT
date: 2026-11-11
base-commit: 9aa0e0c0
branch: fix/phase-b-small-bugs
trace:
  - roadmap-2026-11-10-phase-B
---

# Phase B — Kleine Bugs (13 Issues) — Implementation Plan

> Status: DRAFT (2026-11-11). Dieser Plan implementiert nichts, committet nichts, ändert keine Issues.
> Basis: `origin/main 9aa0e0c0` (Review 2026-11-11: Anker gegen 9aa0e0c0 neu gemessen; ursprünglich `a3d65da4`). "W" = Worktree auf diesem Stand. Roadmap: `docs/superpowers/plans/2026-11-10-backlog-roadmap.md` (APPROVED), Phase B, Welle 1.
> Issues: #1194, #1197, #1205, #1206, #1207, #1213, #1214, #1139, #1170, #1174, #1173, #898, #317.
> Abhängigkeiten (Roadmap §3): Welle 1 hängt von Phase A (CI grün) ab. B läuft vor C (Dateien `sync_pipeline.py`/`context.py` werden von B **nicht** berührt, siehe Abweichungen), vor G (#1170 vor #854) und vor E/F (`admin-ui.html`, `admin-server.py`).
> Branch-Vorschlag: `fix/phase-b-small-bugs`. Ein Phasen-PR, Squash-Merge nach grüner CI, kein Admin-Bypass.

**Goal:** 13 kleine, voneinander unabhängige Defekte (Sync-Pfad, Validator, Spec/Plan-Gate, Admin-UI, Tests, Doku) beheben, je Issue ein TDD-Task und ein Commit; keine Feature-Erweiterung.
**Architecture:** Jede Änderung ist eine lokale Ursachenbehebung in genau der Datei, die der Code-Befund (in W gelesen) nennt. Keine neuen Module außer reinen Testdateien. Keine Provider-Namensverzweigung; Provider-Unterschiede bleiben Config-Keys.
**Tech Stack:** Python 3.9 (stdlib + PyYAML), pytest, Markdown/YAML, eine Single-File-HTML-UI (`docs/ui/admin-ui.html`).
**Spec:** keine eigene Spec nötig (alle Issues S-Klasse). #1197 verweist auf die freigegebene Spec/den Plan von #1187: `docs/specs/2026-11-09-project-context-injection-scope-spec.md` und `docs/plans/2026-11-09-project-context-injection-scope-plan.md` (Status laut Plan-Kopf APPROVED, hier nicht erneut geprüft). Es gibt in dieser Phase keinen Spec-Gate-Task.

## Klassifizierung (Spec/Plan-Gate)

| Issue | Klasse | Begründung |
|---|---|---|
| #1139 | S | Testdatei, ein Literal |
| #1170 | S | tote Funktion löschen |
| #1194 | S | Sync-Pfad + Validator, lokal |
| #1205 | S | eine Quelle für Key-Allowlist; Punkt 3 des Issues wandert nach Phase C (#1142) |
| #1213 | S | Gate-Logik in einer Datei; Schweregrad fest WARNING (Entscheidung 34, B-N1) |
| #1214 | S | ein Regex + Klassifizierung |
| #1207 | S | reine Doku |
| #1197 | M (abhängig) | berührt Rendering von #1187 (APPROVED Spec/Plan, T9 deckt die 5 Prosa-Stellen ab). Phase B liefert nur den Ratchet-Test; Entscheidung 34 (B-N4) |
| #1174 | S | Wiki-Seite |
| #1173 | S | ein Handler; Lösungsweg Diff-Guard wie ai-providers, beantwortet durch Entscheidung 22 |
| #1206 | S | UI-Save-Pfad |
| #898 | S | Punkt 1 UI; Punkt 2 bereits gebaut; Punkt 3 Preise aus der models.dev-Funktion (`ModelsService`), beantwortet durch Entscheidung 23, Funktion bestätigt durch Entscheidung 37 |
| #317 | S (Roadmap: S-M) | nur Test, kein Produktivcode |

## Global Constraints

- Python 3.9 kompatibel (kein `X | Y` als Laufzeit-Typ ohne `from __future__ import annotations`, kein `match`).
- Nur stdlib + PyYAML; keine neue Abhängigkeit (`ruamel.yaml` ist per ADR 0001 ausgeschlossen).
- Provider-agnostisch: Unterschiede über Config-Keys/Capability-Flags, nie `if provider == "Name"`.
- Commits: Conventional Commits, Englisch, Betreffzeile höchstens 72 Zeichen, Imperativ, kein BOM. Commit-/PR-Texte werden später als Datei bereitgestellt; hier nur Betreffzeilen.
- Kein `isolation: "worktree"` beim Spawnen von Subagenten. Kein Push/Tag/Branch durch Worker (nur `git`-Rolle).
- Tests: `python3 -m pytest <datei>::<test>`; Gesamtprüfung am Ende `python3 scripts/sync.py --validate`.
- Pro Task: erst roter Test, dann Implementierung, dann grün, dann Commit. Task-Reihenfolge ist nach Datei geordnet; gleiche Datei ist strikt sequentiell (Task 5 vor 6, Task 11 vor 12).
- Vor Ausführung: Freshness-Check `check_plan_refs.py --plans <dieser Plan> --repo . --ref origin/main` (Skript liegt im Review-Worktree `.tmp/wt-check-plan-refs/scripts/`, nicht auf main) gegen `origin/main`; Zeilenanker in diesem Plan gelten für `9aa0e0c0` und veralten.

## File Structure

- Create: `tests/test_timeouts_usage.py` — pinnt zentrale Timeouts im CLI-Smoke-Modul (#1139)
- Modify: `tests/test_cli_smoke_multi_provider.py` — `timeout=300` durch `SLOW_TIMEOUT` ersetzen (#1139)
- Create: `tests/test_dead_gemini_tool_map_removed.py` — Löschung absichern (#1170)
- Modify: `scripts/lib/provider_transform.py` — `_map_claude_tools_to_gemini_tools` entfernen (#1170)
- Modify: `config/provider-capabilities.yaml` — Notiztext zu G4-2 entkoppeln (#1170)
- Modify: `scripts/lib/opencode_v2_config.py` — totes Top-Level-`subagent_depth` bei v2-Sync entfernen (#1194)
- Modify: `scripts/lib/artifact_validate.py` — `_validate_opencode_v2` um Verbotsprüfung ergänzen (#1194)
- Modify: `tests/test_opencode_v2_surface.py` — Sync- und Validator-Tests (#1194)
- Modify: `scripts/lib/auto_commit.py` — `_KEYS` aus dem Schema ableiten (#1205)
- Modify: `tests/test_auto_commit_violations.py` — Mengengleichheit + Meldungsinhalt (#1205)
- Modify: `scripts/lib/consistency/spec_plan.py` — Approval-Gate entkoppeln, `-spec.md` klassifizieren (#1213, #1214)
- Modify: `tests/test_spec_plan_consistency.py` — Regressionstests (#1213, #1214)
- Modify: `rules/1-generic/spec-plan-workflow.md` — Namenskonvention dokumentieren (#1214)
- Modify: `docs/specs/767-auto-commit-permission-authority.md` — Zeilenanker durch `datei::symbol` ersetzen (#1207)
- Create: `tests/test_spec_767_anchors.py` — Anker auflösbar (#1207)
- Create: `tests/test_project_context_placeholder_ratchet.py` — Duplikat-Ratchet (#1197)
- Modify: `knowledge/wiki/concepts/core-principle-pal-variables.md` — veraltete Verweise (#1174)
- Modify: `knowledge/wiki/log.md` — Log-Eintrag (#1174)
- Create: `tests/test_wiki_stale_variable_table_refs.py` — Wiki-Hygiene (#1174)
- Modify: `scripts/admin-server.py` — `_handle_post_tier_presets_update` (#1173)
- Create: `tests/test_admin_tier_presets_update.py` — Round-Trip-Test (#1173)
- Modify: `docs/ui/admin-ui.html` — `viewProjectAutoCommit` (#1206, #898). Für #1173 keine UI-Änderung: der bestehende Toast-Fehlerpfad zeigt den HTTP-400 an (`admin-ui.html:10953-10954`, Entscheidung 22)
- Create: `tests/test_admin_ui_auto_commit_section.py` — statische UI-Tests (#1206, #898)
- Modify: `config/pricing-overlay.yaml` — aktuelle Claude-IDs (#898, Entscheidung 23: Werte aus der models.dev-Funktion)
- Create: `tests/test_pricing_overlay_current_models.py` — Overlay deckt Claude-Tiers ab (#898)
- Create: `tests/test_viz_subserver_live.py` — Live-Subprozess-Test (#317)

## PR-Schnitt innerhalb der Phase

Ein PR `fix: phase B small bugs (13 issues)` (Entscheidung 17: strikt ein PR pro Phase, keine Abspaltung), 13 Commits, **ein Commit je Task** (Entscheidung 17), in dieser Reihenfolge (nach Datei/Risiko gruppiert):
1. Tests/Backend ohne Laufzeitwirkung: Task 1, 2.
2. Sync-/Validator-/Consistency-Bibliotheken: Task 3, 4, 5, 6.
3. Doku/Wiki/Ratchet: Task 7, 8, 9.
4. Admin (`admin-server.py`, `admin-ui.html`, Live-Test): Task 10, 11, 12, 13.
Die frühere Option einer Abspaltung von Gruppe 4 entfällt (Entscheidung 17).

---

### Task 1: #1139 — zentrales Timeout im CLI-Smoke-Modul
**Agent:** developer
**Files:**
- Modify: `tests/test_cli_smoke_multi_provider.py`
- Create: `tests/test_timeouts_usage.py`

**Interfaces:**
- Consumes: `tests/timeouts.py::SLOW_TIMEOUT` (`int`, Default 900, Env `AGENT_META_SLOW_TIMEOUT`, `tests/timeouts.py:69`)
- Produces: nichts (Testmodul)

Befund in W: `tests/test_cli_smoke_multi_provider.py:53` hat `timeout=300` in `_sync(root, *args)`; die Fixture `project` (`:27`) ruft `_sync(root, "--init")` für alle Provider. `SLOW_TIMEOUT` ist außer in `tests/timeouts.py` und `tests/README.md` ungenutzt. `SYNC_TIMEOUT` hat Default 180 (`tests/timeouts.py:36`) und ist damit kleiner als die heutigen 300 s; deshalb `SLOW_TIMEOUT`.

- [ ] Step 1: Roter Test in `tests/test_timeouts_usage.py`:
  ```python
  import re
  from pathlib import Path

  SMOKE = Path(__file__).parent / "test_cli_smoke_multi_provider.py"

  def test_smoke_module_uses_central_slow_timeout():
      src = SMOKE.read_text(encoding="utf-8")
      assert "from tests.timeouts import SLOW_TIMEOUT" in src
      assert "timeout=SLOW_TIMEOUT" in src

  def test_smoke_module_has_no_hardcoded_timeout_literal():
      src = SMOKE.read_text(encoding="utf-8")
      assert re.search(r"timeout\s*=\s*\d+", src) is None
  ```
- [ ] Step 2: `python3 -m pytest tests/test_timeouts_usage.py` — erwartet: 2 FAILED.
- [ ] Step 3: In `tests/test_cli_smoke_multi_provider.py` `from tests.timeouts import SLOW_TIMEOUT` ergänzen (Importstil wie `tests/test_generated_file_drift.py:844`) und `timeout=300` durch `timeout=SLOW_TIMEOUT` ersetzen. Kein weiterer Umbau (Punkt 3 des Issues: kein Skip, Hang-Guard genügt; Entscheidung 34, B-N5).
- [ ] Step 4: `python3 -m pytest tests/test_timeouts_usage.py` — erwartet: 2 passed. Danach `python3 -m pytest tests/test_cli_smoke_multi_provider.py` (kann lang dauern, Dauer auf der Host-Last notieren; nicht verifiziert, siehe unten).
- [ ] Step 5: Commit `test: use central SLOW_TIMEOUT in cli smoke matrix`

---

### Task 2: #1170 — tote Gemini-Tool-Map entfernen
**Agent:** developer
**Files:**
- Modify: `scripts/lib/provider_transform.py`
- Modify: `config/provider-capabilities.yaml`
- Create: `tests/test_dead_gemini_tool_map_removed.py`

**Interfaces:**
- Consumes: nichts
- Produces: entfernt `provider_transform._map_claude_tools_to_gemini_tools(tools: list) -> list[str]` (öffentliche Nutzung: keine)

Befund in W: Definition `scripts/lib/provider_transform.py:885` (Issue sagt `:854`, ältere Specs `:854-870`; Roadmap `:885` stimmt). Repo-weite Suche (ohne `.tmp/`): kein Aufrufer in `scripts/` oder `tests/`. Verweise nur in `config/provider-capabilities.yaml:290` (Notiztext, G4-2) und in historischen Dokumenten (`docs/specs/2026-11-09-commit-authority-grant-spec.md:297,898`, `docs/plans/2026-11-09-commit-authority-grant-plan.md:112`, `docs/plans/2026-09-06-phase4c-blast-radius.md:226`, `docs/reviews/2026-10-07-system-review.md:114`). Historische Dokumente bleiben unverändert (Aufzeichnung); AC "grep findet keinen Verweis" gilt für `scripts/`, `tests/`, `config/`.

- [ ] Step 1: Roter Test:
  ```python
  import sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(REPO_ROOT / "scripts"))
  NAME = "_map_claude_tools_to_gemini_tools"

  def test_function_is_gone():
      from lib import provider_transform
      assert not hasattr(provider_transform, NAME)

  def test_no_reference_in_code_tests_or_config():
      for base in ("scripts", "config"):
          for p in (REPO_ROOT / base).rglob("*"):
              if p.suffix in (".py", ".yaml", ".yml"):
                  assert NAME not in p.read_text(encoding="utf-8"), str(p)
  ```
  (Der Test selbst enthält den Namen, liegt aber in `tests/` und wird nicht durchsucht.)
- [ ] Step 2: `python3 -m pytest tests/test_dead_gemini_tool_map_removed.py` — erwartet: 2 FAILED.
- [ ] Step 3: Funktion in `scripts/lib/provider_transform.py` (Zeilen 885-901, nur Funktionskörper inkl. Leerzeile) löschen; `config/provider-capabilities.yaml:290` Satzteil zur gelöschten Funktion ersetzen durch "(Mapping-Funktion in #1170 entfernt; Tool-Namen kommen aus `agent-transform.tool-name-map`)". Vorher prüfen, ob ein Test den G4-2-Text pinnt (`G4-2` kommt in `tests/**/*.py` nicht vor, Suche in W).
- [ ] Step 4: `python3 -m pytest tests/test_dead_gemini_tool_map_removed.py` — passed; `python3 -m pytest tests/test_provider_toml_transform.py tests/test_provider_options_schema.py`; `python3 scripts/sync.py --validate` — erwartet rc 0.
- [ ] Step 5: Commit `refactor: remove dead gemini tool map from provider_transform`

---

### Task 3: #1194 — totes `subagent_depth` bei v2-Sync entfernen + Validator
**Agent:** developer
**Files:**
- Modify: `scripts/lib/opencode_v2_config.py`
- Modify: `scripts/lib/artifact_validate.py`
- Modify: `tests/test_opencode_v2_surface.py`

**Interfaces:**
- Consumes: `opencode_v2_config.sync_opencode_v2_managed_keys(project_root, config, provider, provider_config, agent_meta_root, log, dry_run, *, claimed_files)` (`:680`), `build_managed_keys(...)` (`:464`), `artifact_validate.validate_json_document(text, fmt, path)` (`:304`), `_validate_opencode_v2(doc, path)` (`:436`), `_finding(path, message, suggestion="")` (`:155`)
- Produces: Konstante `_DEAD_TOP_LEVEL_KEYS = ("subagent_depth",)` in `opencode_v2_config.py`; neuer ERROR-Finding in `_validate_opencode_v2`

Befund in W: Entfernung passiert nur in `context.py::apply_settings_surface_shape` (`:1815`), aufgerufen aus `_init_provider_settings_json` (`:1899`), das bei vorhandener Datei früh endet ("already exists — not overwritten", `:1927`). `sync_opencode_v2_managed_keys` liest die bestehende Datei (`:767`), verwaltet nur `experimental.subagent_depth`, `experimental.todo`, `providers.<id>`; v1-Frühausstieg bei `not targets and not state` (`:745`). `_validate_opencode_v2` (`:436-475`) prüft nur `mcp`. Docstring-Zusage "no top-level `subagent_depth`" steht bei `artifact_validate.py:315`. `context.py` bleibt unverändert.

- [ ] Step 1: Rote Tests in `tests/test_opencode_v2_surface.py` (vorhandene Helfer, gemessen in W: `_v2_pc() -> dict` `:371`, `_v1_pc() -> dict` `:382`, `_config(depth: int | None = None, **options) -> dict` `:403`, `_write_json(path, data) -> Path` `:411`, `_read_json(path) -> dict` `:417`, `_write_capabilities(root, provider, required_depth) -> Path` `:426`, `_run(project_root, config, providers, framework, log=None, dry_run=False, provider="Opencode", claimed_files=None) -> SyncLog` `:436`; `SyncLog` ist bereits importiert `:67`, `log.actions` ist eine Liste von Strings, Muster `:770`):
  ```python
  def test_dead_top_level_subagent_depth_removed_on_existing_v2_project(tmp_path):
      framework = _write_capabilities(tmp_path / "fw", "Opencode", 3)
      project = tmp_path / "project"
      _write_json(project / "opencode.json", {"subagent_depth": 3, "plugin": ["acme.js"]})
      log = _run(project, _config(depth=3), {"Opencode": _v2_pc()}, framework)
      doc = _read_json(project / "opencode.json")
      assert "subagent_depth" not in doc
      assert doc["experimental"]["subagent_depth"] == 3
      assert doc["plugin"] == ["acme.js"]
      assert any("dead top-level key 'subagent_depth'" in a for a in log.actions), log.actions

  def test_dead_key_removal_is_idempotent(tmp_path):
      ...  # zweiter _run: Bytes von opencode.json unveraendert

  def test_v1_surface_keeps_top_level_subagent_depth(tmp_path):
      framework = _write_capabilities(tmp_path / "fw", "Opencode", 3)
      project = tmp_path / "project"
      _write_json(project / "opencode.json", {"subagent_depth": 3})
      before = (project / "opencode.json").read_bytes()
      _run(project, _config(), {"Opencode": _v1_pc()}, framework)
      assert (project / "opencode.json").read_bytes() == before

  def test_validator_flags_top_level_subagent_depth_in_v2_doc():
      from lib.artifact_validate import validate_json_document
      bad = validate_json_document('{"subagent_depth": 3}', "opencode-json-v2", "opencode.json")
      assert len(bad) == 1 and "subagent_depth" in bad[0].message
      assert "experimental.subagent_depth" in bad[0].suggestion
      assert validate_json_document('{"experimental": {"subagent_depth": 3}}',
                                    "opencode-json-v2", "opencode.json") == []
  ```
  Der zweite Test ist kein Platzhalter, sondern vor dem Commit auszuformulieren (Aufbau wie Test 1): erster `_run`, `before = read_bytes()`, zweiter `_run`, `assert read_bytes() == before`; zusätzlich `assert not any("dead top-level key" in a for a in log2.actions)` für den zweiten Lauf (Regressionsschutz; der Test ist vor und nach der Änderung grün).
- [ ] Step 2: `python3 -m pytest tests/test_opencode_v2_surface.py -k "dead_top_level or dead_key_removal or v1_surface_keeps or validator_flags_top_level"` — erwartet (Plan-Wert, nicht ausgeführt): 2 FAILED (`dead_top_level…`, `validator_flags…`); `v1_surface_keeps` ist bereits grün (v1-Frühausstieg `:745`); `dead_key_removal_is_idempotent` ist vor der Änderung grün, weil heute nichts entfernt wird (Regressionsschutz, kein roter Test).
- [ ] Step 3: In `sync_opencode_v2_managed_keys` direkt NACH `changed = False` (`:776`) und vor der Merge-Schleife (`for path in …`, `:777`) — nicht davor, sonst setzt `:776` das Flag zurück: wenn `targets` nicht leer ist (v2 aktiv; auf v1/Rollback ist `targets` leer, kein Eingriff), je Schlüssel in `_DEAD_TOP_LEVEL_KEYS` `existing.pop(key, None)`; bei Treffer `changed = True` und `log.action("REMOVE", committed, f"opencode-v2 dead top-level key '{key}'")` (Muster Signatur wie `:819`). In `_validate_opencode_v2` am Anfang: enthält `doc` den Schlüssel `subagent_depth`, einen `_finding(path, "opencode-json-v2 carries a top-level 'subagent_depth' (dead key)", "use 'experimental.subagent_depth'")` anhängen.
- [ ] Step 4: Dieselben Tests grün; zusätzlich `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_opencode_v2_config.py tests/test_settings_depth_and_deny.py` (Init-Transform-Tests dürfen nicht kippen); `python3 scripts/sync.py --validate` rc 0.
- [ ] Step 5: Commit `fix: drop stale top-level subagent_depth on opencode v2 sync`

---

### Task 4: #1205 — eine Quelle für die `auto_commit`-Key-Allowlist
**Agent:** developer
**Files:**
- Modify: `scripts/lib/auto_commit.py`
- Modify: `tests/test_auto_commit_violations.py`

**Interfaces:**
- Consumes: `config/project-config.schema.json` → `properties.auto_commit.properties` (Keys heute: `mode`, `triggers`, `file_count_threshold`, `custom_script`, `secret_scan`; `additionalProperties: false`, `:1495-1546`)
- Produces: `auto_commit._STATIC_KEYS: frozenset`, `auto_commit._SCHEMA_PATH: Path`, `auto_commit._load_schema_keys(path: Path = _SCHEMA_PATH) -> frozenset`, `auto_commit._KEYS: frozenset` (statt `set`, `:164`)

Befund in W: `_KEYS` bei `scripts/lib/auto_commit.py:164`; Prüfung `unknown = sorted(set(ac_cfg) - _KEYS)` bei `:222-224`; jede Violation führt in `resolve_auto_commit_config` (`:269`) zum Fail-Safe `mode: off`. Aufrufer von `auto_commit_violations`: `sync_pipeline.py:1993`, `cli_commands.py:1465`, `config.py:1807`, `auto_commit.py:269`. Nutzer von `_KEYS` (Suche in W über `scripts/`, `tests/`): nur `auto_commit.py:222` und `tests/test_auto_commit_violations.py:116`/`:123`; der Typwechsel `set` -> `frozenset` ist für beide unkritisch (`set(ac_cfg) - _KEYS`, `set(_KEYS) == …`). Der Mengengleichheits-Test aus Issue-Punkt 2 existiert bereits: `test_enum_constants_match_schema` (`tests/test_auto_commit_violations.py:111-123`, `assert set(_KEYS) == set(ac["properties"])`); AK 2 ist damit heute schon erfüllt. Punkt 3 des Issues (unbekannte Keys nicht den ganzen Block invalidieren) kollidiert mit dem bestehenden Test `tests/test_auto_commit_violations.py::test_unknown_values_and_keys` und überschneidet #1142 (Phase C, Entscheidung 3 fail-soft). Er wird hier nicht umgesetzt (siehe Abweichung 5).

- [ ] Step 1: Rote Tests in `tests/test_auto_commit_violations.py` (`import json` ergänzen):
  ```python
  def _schema_keys():
      schema = json.loads((REPO_ROOT / "config" / "project-config.schema.json")
                          .read_text(encoding="utf-8"))
      return set(schema["properties"]["auto_commit"]["properties"])

  # set(_KEYS) == schema: bereits durch test_enum_constants_match_schema (:111-123) gepinnt, kein Duplikat.

  def test_static_fallback_equals_schema_properties():
      from lib import auto_commit
      assert set(auto_commit._STATIC_KEYS) == _schema_keys()

  def test_schema_only_key_is_accepted(tmp_path):
      # AK 1: a key added only in the schema must not be reported as unknown.
      from lib import auto_commit
      schema = json.loads((REPO_ROOT / "config" / "project-config.schema.json")
                          .read_text(encoding="utf-8"))
      schema["properties"]["auto_commit"]["properties"]["authority_overrides"] = {"type": "object"}
      path = tmp_path / "schema.json"
      path.write_text(json.dumps(schema), encoding="utf-8")
      assert "authority_overrides" in auto_commit._load_schema_keys(path)

  def test_missing_schema_falls_back_to_static_keys(tmp_path):
      from lib import auto_commit
      assert auto_commit._load_schema_keys(tmp_path / "missing.json") == auto_commit._STATIC_KEYS

  def test_unknown_key_message_names_key_and_source():
      v = auto_commit_violations({"auto_commit": {"mode": "off", "bogus": 1}})
      msg = [m for m in v if "bogus" in m][0]
      assert "config/project-config.schema.json" in msg and "allowed:" in msg
  ```
- [ ] Step 2: `python3 -m pytest tests/test_auto_commit_violations.py` — erwartet (Plan-Wert): 4 neue FAILED (`_STATIC_KEYS`/`_load_schema_keys` fehlen, Meldung ohne Quelle), Bestandstests grün.
- [ ] Step 3: `import json` ergänzen; `_STATIC_KEYS = frozenset({...5 Keys...})`; `_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "config" / "project-config.schema.json"` (`parents[2]` = Repo-/Framework-Root, da Datei in `scripts/lib/`); `def _load_schema_keys(path: Path = _SCHEMA_PATH) -> frozenset:` liest `properties.auto_commit.properties`, fängt `OSError, ValueError, KeyError, TypeError` und fällt auf `_STATIC_KEYS` zurück; `_KEYS = _load_schema_keys()`. Meldung erweitern: `f"auto_commit has unknown key(s): {', '.join(unknown)} (allowed: {', '.join(sorted(_KEYS))}; source: config/project-config.schema.json)"`. Nutzer von `_KEYS` sind bereits erhoben (siehe Befund).
- [ ] Step 4: `python3 -m pytest tests/test_auto_commit_violations.py tests/test_config_null_blocks.py` — grün; `python3 scripts/sync.py --validate` rc 0.
- [ ] Step 5: Commit `fix: derive auto_commit key allowlist from schema`

---

### Task 5: #1213 — Approval-Gate unabhängig vom Task-Header-Dialekt
**Agent:** developer
**Files:**
- Modify: `scripts/lib/consistency/spec_plan.py`
- Modify: `tests/test_spec_plan_consistency.py`

**Interfaces:**
- Consumes: `_check_approval_markers(project_root, plans, texts, findings)` (`spec_plan.py:479`), `_parse_plan_tasks(text)` (genutzt `:446`, `:490`), `parse_plan_ledger(plan_path)` (`:100`), `plan_identity.TASK_HEADER_RE` (`scripts/lib/plan_identity.py:27`, verlangt literal `### Task <id>`)
- Produces: `_TASK_LIKE_HEADER_RE`, `_check_task_detection(project_root, plans, texts, findings)`, neuer Check-Name `spec_plan_no_tasks_detected` (Schweregrad fest WARNING, Entscheidung 34)

Befund in W: Guard bei `spec_plan.py:490-492` (`has_tasks = bool(_parse_plan_tasks(text)) or parse_plan_ledger(plan)["checkboxes"] > 0; if not has_tasks: continue`). Aufruf in `check_spec_plan_workflow` bei `:197`. Reproduktion lt. Issue (`### T1 — …` ergibt 0 Tasks) ist aus dem Regex ableitbar, aber nicht ausgeführt. Schweregrad von `spec_plan_no_tasks_detected` fest WARNING (Entscheidung 34, B-N1); Approval-Gate bleibt ERROR wie im Issue gefordert.
**Messung im Review (read-only, W 9aa0e0c0):** `_TASK_LIKE_HEADER_RE` trifft bei leerem `_parse_plan_tasks` genau 5 Dateien (gescannt: `docs/plans`, `docs/superpowers/plans`, `docs/specs`; `docs/superpowers/plans` ist in `.meta-config/project.yaml` `spec-plan-workflow.paths.legacy` und wird mitgescannt): `docs/plans/2026-11-09-artifact-locations-matrix-plan.md` (`#### T1 —`), `docs/plans/2026-11-09-commit-authority-grant-plan.md` (`### T1 —`), `docs/plans/2026-11-09-project-context-injection-scope-plan.md` (`### T1 —`), `docs/superpowers/plans/2026-08-04-planner-agent-and-orchestration-refinement.md` und `…/2026-09-10-bug-batch-703-720.md` (je `## Task 1:`). Alle sind echte Task-Header, kein Fehlalarm. Folge für das Approval-Gate: `artifact-locations-matrix-plan.md` verweist auf `docs/specs/2026-11-09-artifact-locations-matrix-spec.md`, deren Kopf `> Status: **APPROVED** — …` (`:3`) von `_APPROVED_RE` (`spec_plan.py:85-87`, erlaubt `**` nur um `Status:`) NICHT erkannt wird (gemessen: `False`). Ohne Zusatz erzeugt Task 5 dort einen falschen ERROR `spec_plan_approval_marker` (Regression). Deshalb Step 3b.

- [ ] Step 1: Rote Tests (Helfer `_write`, `_plan`, `_ENABLED`, `_GOOD_SPEC` am Dateikopf, `:18-52`):
  ```python
  _DRAFT_SPEC = "# Demo — Spec\n> Status: DRAFT\n"

  def test_dashed_task_headers_still_trigger_approval_gate(tmp_path):
      _write(tmp_path, _DRAFT_SPEC, _plan("### T1 — step one\n### T2 — step two\n"))
      findings = check_spec_plan_workflow(tmp_path, _ENABLED, agent_meta_root=REPO_ROOT)
      assert any(f.check == "spec_plan_approval_marker" and f.severity == Severity.ERROR
                 for f in findings)

  def test_task_like_headers_without_parsed_tasks_report_explicit_finding(tmp_path):
      _write(tmp_path, _GOOD_SPEC, _plan("### T1 — step one\n"))
      findings = check_spec_plan_workflow(tmp_path, _ENABLED, agent_meta_root=REPO_ROOT)
      assert any(f.check == "spec_plan_no_tasks_detected" and f.severity == Severity.WARNING
                 for f in findings)

  def test_canonical_task_headers_produce_no_new_findings(tmp_path):
      _write(tmp_path, _GOOD_SPEC, _plan("### Task T1: step one\n"))
      findings = check_spec_plan_workflow(tmp_path, _ENABLED, agent_meta_root=REPO_ROOT)
      assert not any(f.check == "spec_plan_no_tasks_detected" for f in findings)
      assert not any(f.check == "spec_plan_approval_marker" for f in findings)

  def test_bold_approved_value_counts_as_approved(tmp_path):
      spec = _GOOD_SPEC.replace("> Status: APPROVED (2026-09-13)", "> Status: **APPROVED** — 2026-09-13")
      _write(tmp_path, spec, _plan("### T1 — step one\n"))
      findings = check_spec_plan_workflow(tmp_path, _ENABLED, agent_meta_root=REPO_ROOT)
      assert not any(f.check == "spec_plan_approval_marker" for f in findings)
  ```
- [ ] Step 2: `python3 -m pytest tests/test_spec_plan_consistency.py -k "dashed or task_like or canonical_task_headers or bold_approved"` — erwartet (Plan-Wert): 2 FAILED (dashed, task_like), canonical und bold_approved grün (bold_approved wird erst nach Step 3 ohne 3b rot und ist der Regressionsschutz für 3b).
- [ ] Step 3: `_TASK_LIKE_HEADER_RE = re.compile(r"(?m)^#{2,4}[ \t]+(?:Task[ \t]+)?T?[0-9]+[A-Za-z0-9._-]*[ \t]*(?::|[—–)-])")` neben `_TASK_HEADER_RE` (`:55`). In `_check_approval_markers` `has_tasks` um `or bool(_TASK_LIKE_HEADER_RE.search(text))` erweitern. Neue Funktion `_check_task_detection`: je Plan, wenn `_TASK_LIKE_HEADER_RE.search(text)` und `not _parse_plan_tasks(text)`, ein Finding `spec_plan_no_tasks_detected` mit fest `Severity.WARNING` (Entscheidung 34, B-N1) und Suggestion "use '### Task <id>: <title>'"; in `check_spec_plan_workflow` direkt nach `_check_approval_markers` (`:197`) aufrufen. `TASK_HEADER_RE` bleibt unverändert (Ledger-Writer-Vertrag, IC-07).
- [ ] Step 3b: `_APPROVED_RE` (`spec_plan.py:85-87`) um optionales `\**` vor dem Wert erweitern: `r"(?im)^[ \t]*>?[ \t]*\**Status:\**[ \t]*\**APPROVED\b"`. Grund: siehe Messung oben (falscher ERROR auf `artifact-locations-matrix-plan.md`).
- [ ] Step 4: Neue Tests grün; `python3 -m pytest tests/test_spec_plan_consistency.py tests/test_spec_plan_validate_cli.py tests/test_plan_ledger.py tests/test_plan_ledger_writer.py`. Vollscan-Vergleich vor/nach: `python3 -c "from pathlib import Path; from lib.consistency.spec_plan import check_spec_plan_workflow as c; fs=c(Path('..'), changed_files=None); print(len(fs))"` aus `scripts/`; neue ERRORs auf Bestandsplänen im PR-Text benennen. Achtung (im Review ausgeführt, W mit Phasenplänen): der Vollscan bricht heute mit `OSError: [Errno 36] File name too long` in `_check_traceability` ab (`spec_plan.py:413-414`, `(project_root / ref).exists()` auf einen Prosa-`**Spec:**`-Wert mit Pfadkomponente >255 Byte: `2026-11-11-phase-d-guards-hooks.md` 277 B, `2026-11-11-phase-i-features-concept.md` 353 B). Vor dem Vollscan diese beiden `**Spec:**`-Zeilen kürzen (Sache der Pläne D/I) oder den Vergleich ohne diese Dateien fahren; der Absturz selbst ist ein eigener Bug außerhalb von B (Issue-Vorschlag, nicht in diesem Task).
- [ ] Step 5: Commit `fix: gate spec approval for non-canonical plan task headers`

---

### Task 6: #1214 — `*-spec.md` als Spec klassifizieren
**Agent:** developer
**Depends on:** Task 5
**Files:**
- Modify: `scripts/lib/consistency/spec_plan.py`
- Modify: `tests/test_spec_plan_consistency.py`
- Modify: `rules/1-generic/spec-plan-workflow.md`

**Interfaces:**
- Consumes: `_classify(name: str) -> str` (`spec_plan.py:318`), `_matches_template(name: str) -> bool` (`:312`), `_DESIGN_RE` (`:50`), `REQUIRED_SPEC_SECTIONS` (`:31`)
- Produces: `_SPEC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-.+-spec\.md$")`; `_classify("…-spec.md") == "spec"`

Befund in W: `_classify` gibt für alles außer `-spike.md`/`-design.md` `"plan"` zurück (`:318-323`); `_matches_template` kennt `_DATED_RE` (`:51`) als Auffangmuster (`:312-315`), `*-spec.md` wird also schon heute als Artefakt erfasst und nur falsch klassifiziert. Variante (a) des Issues (Muster erweitern) ist die Vorzugsvariante des Issues (`.tmp/issues/1214.md:68`, keine nummerierte User-Entscheidung), weil sie keine Migration braucht: In W sind es 16 `docs/specs/YYYY-MM-DD-*-spec.md` (Issue nennt 13; `git ls-tree origin/main docs/specs`). Nach der Änderung laufen Pflichtsektions- und spec-id-Prüfungen für diese Dateien; echte fehlende Sektionen erscheinen weiterhin (WARNING, bzw. ERROR bei `spec-plan-required`). Das ist beabsichtigt, aber im PR-Text zu nennen.

- [ ] Step 1: Rote Tests:
  ```python
  from lib.consistency.spec_plan import _classify

  def test_classify_spec_suffix_is_spec():
      assert _classify("2026-11-09-x-spec.md") == "spec"
      assert _classify("2026-11-09-x-design.md") == "spec"
      assert _classify("2026-11-09-x-plan.md") == "plan"
      assert _classify("2026-11-09-x-spike.md") == "spike"

  def test_spec_suffix_file_is_not_blamed_for_missing_spec_field(tmp_path):
      (tmp_path / "docs" / "specs").mkdir(parents=True)
      (tmp_path / "docs" / "plans").mkdir(parents=True)
      (tmp_path / "docs" / "specs" / "2026-09-13-demo-spec.md").write_text(
          _GOOD_SPEC.replace("SPEC-demo", "SPEC-demo2"), encoding="utf-8")
      findings = check_spec_plan_workflow(tmp_path, _ENABLED, agent_meta_root=REPO_ROOT)
      spec_fs = [f for f in findings if f.file.endswith("-spec.md")]
      assert not any("no '**Spec:**' reference" in f.message for f in spec_fs)
      assert any("spec-id 'SPEC-demo2' is not referenced by any plan" in f.message
                 for f in spec_fs)
  ```
- [ ] Step 2: `python3 -m pytest tests/test_spec_plan_consistency.py -k "classify_spec_suffix or spec_suffix_file"` — erwartet: 2 FAILED.
- [ ] Step 3: `_SPEC_RE` neben `_DESIGN_RE` (`:50`) anlegen; nur in `_classify` (`:321`) `or _SPEC_RE.match(name)` ergänzen. `_matches_template` bleibt unverändert (`_DATED_RE` deckt `-spec.md` bereits ab; Erweiterung wäre wirkungslos). In `rules/1-generic/spec-plan-workflow.md` gibt es keinen Abschnitt zu Dateinamen (Suche in W nach `design`/`YYYY`/`Namens`/`-spec`: nur `:32`, Tabellenspalte "Design + Spec + Plan") und kein YAML-Frontmatter (keine Datei unter `rules/1-generic/` hat Frontmatter) — daher einen Satz "Specs heißen `YYYY-MM-DD-<topic>-design.md` oder `YYYY-MM-DD-<topic>-spec.md`" direkt unter der Phasen-Übersicht (`## Phasen`) ergänzen; keine Versionsangabe. Danach `python3 scripts/sync.py` im Repo, um gerenderte Regeln konsistent zu halten (Drift: `python3 scripts/sync.py --check`, Flag existiert lt. `--help`).
- [ ] Step 4: Tests grün; `python3 -m pytest tests/test_spec_plan_consistency.py tests/test_spec_plan_migration.py tests/test_spec_plan_scaffold.py tests/test_spec_plan_conditional_flag.py tests/test_rules_activation_gate.py tests/test_spec_plan_group_consistency.py` (die letzten drei referenzieren `spec-plan-workflow.md`); Vollscan-Zählung wie Task 5 Step 4, Erwartung: keine `plan has no '**Spec:**'`-Findings mehr auf `*-spec.md`.
- [ ] Step 5: Commit `fix: classify *-spec.md files as specs in spec-plan check`

---

### Task 7: #1207 — Zeilenanker in Spec #767 durch `datei::symbol` ersetzen
**Agent:** documenter
**Files:**
- Modify: `docs/specs/767-auto-commit-permission-authority.md`
- Create: `tests/test_spec_767_anchors.py`

**Interfaces:**
- Consumes: Symbole `scripts/lib/auto_commit.py::_ELIGIBLE_TOOLS` (`:28`), `::is_role_eligible` (`:146`), `::role_commit_authority` (`:127`), `::render_auto_commit_block` (`:322`), `::AUTHORITY_DIRECT` (`:34`); `scripts/lib/config.py::_build_core_variables` (`:1622`, `AUTO_COMMIT_ENABLED` `:1838`); `scripts/lib/sync_pipeline.py::_sync_stage_auto_commit_allowlist` (`:1974`); `scripts/lib/agent_sync.py::_tools_can_spawn` (`:70`), `::sync_agents_for_provider` (`:1519`); `scripts/lib/subagent_permissions.py` (existiert); `hooks/1-generic/orchestrator-guard-impl.sh::_ALLOWLIST` (`:448`)
- Produces: keine Code-Schnittstelle

Befund in W: Spec-Status ist "Entwurf" (`docs/specs/767-auto-commit-permission-authority.md:2`), nicht APPROVED wie das Issue annimmt; reine Doku-Änderung, kein Gate nötig. Betroffene Code-Anker `datei.py|sh:<zeile>` (Spec-Zeilen, per Regex des Tests in W gezählt: 14 Treffer): 9, 13, 15, 16, 26, 72, 78, 114, 115, 137, 140, 143, 230, 238; dazu der nackte Anker `(:32-39)` in `:10` und die Markdown-Anker `:11` (`orchestrator.md:7-12`) und `:17` (`orchestrator.md:335-336`). `_template_path` (Spec `:71`) existiert nicht mehr als Modul-Symbol (nur `config_audit.py::_template_path_for_role`). In W belegt: `agent_sync.py::sync_agents_for_provider` (`:1519`) und `scripts/lib/subagent_permissions.py` existieren — als `datei::symbol` bzw. Dateipfad verwendbar.

- [ ] Step 1: Roter Test:
  ```python
  import re
  from pathlib import Path

  REPO_ROOT = Path(__file__).resolve().parent.parent
  SPEC = REPO_ROOT / "docs" / "specs" / "767-auto-commit-permission-authority.md"

  def test_no_code_line_anchors():
      text = SPEC.read_text(encoding="utf-8")
      assert re.findall(r"[\w/.-]+\.(?:py|sh):\d+", text) == []

  def test_symbol_anchors_resolve():
      text = SPEC.read_text(encoding="utf-8")
      refs = re.findall(r"([\w/.-]+\.(?:py|sh))::(\w+)", text)
      assert refs, "spec must use datei::symbol anchors"
      for rel, sym in refs:
          f = REPO_ROOT / rel
          assert f.is_file(), rel
          assert sym in f.read_text(encoding="utf-8"), f"{rel}::{sym}"

  def test_is_role_eligible_claim_is_anchored():
      text = SPEC.read_text(encoding="utf-8")
      assert "scripts/lib/auto_commit.py::is_role_eligible" in text
  ```
- [ ] Step 2: `python3 -m pytest tests/test_spec_767_anchors.py` — erwartet: 3 FAILED.
- [ ] Step 3: Anker in der Spec ersetzen (volle Repo-Pfade). Root Cause 1 mit dem Zusatz "Stand vor #767; heute: `is_role_eligible` liefert `role_commit_authority(...) == AUTHORITY_DIRECT`" (belegt durch `auto_commit.py:146-153`) versehen. Verbleibende Nicht-Code-Anker (`orchestrator.md:335-336`, `agents/1-generic/orchestrator.md:7-12`) und den nackten Anker `(:32-39)` mit "(Stand 9aa0e0c0)" markieren (der Test prüft nur `datei.py|sh:<zeile>`).
- [ ] Step 4: `python3 -m pytest tests/test_spec_767_anchors.py` — 3 passed; `python3 scripts/sync.py --validate` rc 0.
- [ ] Step 5: Commit `docs: replace line anchors in spec 767 with symbol refs`

---

### Task 8: #1197 — Absicherung gegen weitere `{{PROJECT_CONTEXT}}`-Duplikate (Umsetzung via #1187)
**Agent:** tester
**Files:**
- Create: `tests/test_project_context_placeholder_ratchet.py`

**Interfaces:**
- Consumes: `agents/1-generic/*.md` (nur lesen)
- Produces: Ratchet-Konstante `_KNOWN_DUPLICATES`; der APPROVED-Plan von #1187 (T9) muss sie beim Umstellen der Prosa-Stellen senken

Befund in W (Vorkommen von `{{PROJECT_CONTEXT}}`, Art je Stelle):
| Datei | Zeile | Art |
|---|---|---|
| `agents/1-generic/ui-ux-designer.md` | 72 | Block (`**Project context:** …`) |
| | 77, 105 | Prosa |
| `agents/1-generic/bug-feature-analyzer.md` | 76 | Block |
| | 40 | Prosa |
| `agents/1-generic/knowledge-curator.md` | 22 | Block |
| | 55 | Prosa |
| `agents/1-generic/knowledge-migrator.md` | 26 | Block |
| | 38 | Prosa |

Zählung in W per `str.count` bestätigt: genau diese vier Dateien haben >1 Vorkommen (3/2/2/2), alle übrigen `agents/1-generic/*.md` ≤1. #1187-Spec und -Plan sind APPROVED (`docs/specs/2026-11-09-project-context-injection-scope-spec.md:3`, `docs/plans/2026-11-09-project-context-injection-scope-plan.md:3`). Die 5 Prosa-Stellen sind in `docs/plans/2026-11-09-project-context-injection-scope-plan.md` (Zielbild Punkt 4, Datei-Tabelle `:43-46`, T9) bereits zur Umstellung auf `{{#if PROJECT_CONTEXT_INJECTED}}…{{else}}{{CONTEXT_FILE}}{{/if}}` eingeplant. Eine eigene Umformulierung in Phase B würde dieselben vier Dateien mit Versionsbumps ändern und den `all`-Modus byte-ändern; deshalb liefert Phase B nur den Ratchet-Test (Entscheidung 34, B-N4: #1197 über #1187-T9, in B nur Ratchet). Akzeptanzkriterien 1 und 3 des Issues (`mode: core`-Golden, `all` byte-identisch) gehören zu #1187, nicht zu B. Kriterium 4 (Block-vs-Prosa dokumentiert) erfüllt die Tabelle oben plus Docstring im Test.

- [ ] Step 1: Test schreiben (grün ab Anfang, schlägt bei neuem Duplikat an):
  ```python
  from pathlib import Path

  REPO_ROOT = Path(__file__).resolve().parent.parent
  # Shrink-only ratchet. Block = one "**Project context:**" line, prose = sentence
  # references. #1187 T9 wraps prose sites in {{#if}} and keeps the token,
  # so counts stay 3/2/2/2; lower an entry only when a token is removed.
  _KNOWN_DUPLICATES = {
      "ui-ux-designer.md": 3,
      "bug-feature-analyzer.md": 2,
      "knowledge-curator.md": 2,
      "knowledge-migrator.md": 2,
  }

  def test_project_context_placeholder_count_ratchet():
      for f in sorted((REPO_ROOT / "agents" / "1-generic").glob("*.md")):
          n = f.read_text(encoding="utf-8").count("{{PROJECT_CONTEXT}}")
          limit = _KNOWN_DUPLICATES.get(f.name, 1)
          assert n <= limit, f"{f.name}: {n} > {limit} (new duplicate placeholder)"
          assert limit == 1 or n == limit, f"{f.name}: lower the ratchet to {n}"
  ```
- [ ] Step 2: `python3 -m pytest tests/test_project_context_placeholder_ratchet.py` — erwartet: passed (Ist-Stand 3/2/2/2 laut Suche in W). Negativprobe: Test lokal gegen eine Kopie mit zusätzlichem Platzhalter laufen lassen, erwartet FAILED (nicht im Repo behalten).
- [ ] Step 3: Kein Produktivcode. Querbezug: #1187-T9 umschließt die fünf Prosa-Stellen mit `{{#if PROJECT_CONTEXT_INJECTED}}`…`{{/if}}`, der Token `{{PROJECT_CONTEXT}}` bleibt stehen (`docs/plans/2026-11-09-project-context-injection-scope-plan.md:376-380`); `str.count` bleibt 3/2/2/2, der Ratchet bleibt grün und wird in T9 NICHT gesenkt. Der T9-Commit lässt diesen Test nur mitlaufen (erwartet passed). Querverweis steht im E-Plan (`2026-11-11-phase-e-artifact-locations.md:119`).
- [ ] Step 4: Commit `test: ratchet duplicate PROJECT_CONTEXT placeholders in templates`

---

### Task 9: #1174 — veralteten Verweis in der Wiki-Seite PAL-Variablen ersetzen
**Agent:** knowledge-gardener
**Files:**
- Modify: `knowledge/wiki/concepts/core-principle-pal-variables.md`
- Modify: `knowledge/wiki/log.md`
- Create: `tests/test_wiki_stale_variable_table_refs.py`

**Interfaces:**
- Consumes: `scripts/lib/config.py::_build_core_variables` (`:1622`), `scripts/lib/config.py::build_variables` (`:2779`), `.meta-config/project.yaml` (`variables:`)
- Produces: aktualisierte Seite; Log-Zeile im Format `YYYY-MM-DD HH:MM — <operation> — <summary>` (`knowledge/wiki/log.md:15-17`)

Befund in W: `knowledge/wiki/concepts/core-principle-pal-variables.md:81` verweist auf "Variablen-Tabelle der globalen `CLAUDE.md` / `AGENTS.md`"; `:80` nennt `_inject_dod()`, das in `scripts/lib/` nicht existiert (`_build_core_variables` und `build_variables` existieren). `agents/agent-meta-developer.md:165` aus dem Issue existiert in W nicht (Roadmap-Befund bestätigt). Der Text "Variablen-Tabelle" kommt in `knowledge/wiki/` nur an dieser einen Stelle vor (sonst nur in `knowledge/sources/CHANGELOG.md`, immutable Quelle, bleibt).

- [ ] Step 1: Roter Test:
  ```python
  from pathlib import Path

  WIKI = Path(__file__).resolve().parent.parent / "knowledge" / "wiki"

  def test_no_stale_variable_table_reference():
      for p in WIKI.rglob("*.md"):
          assert "Variablen-Tabelle" not in p.read_text(encoding="utf-8"), str(p)

  def test_no_removed_inject_dod_reference():
      page = WIKI / "concepts" / "core-principle-pal-variables.md"
      assert "_inject_dod" not in page.read_text(encoding="utf-8")
  ```
- [ ] Step 2: `python3 -m pytest tests/test_wiki_stale_variable_table_refs.py` — erwartet: 2 FAILED.
- [ ] Step 3: Seite anpassen: Schritt 1 "Registrierung in `scripts/lib/config.py` (`_build_core_variables` bzw. `build_variables`)"; Schritt 2 "Dokumentation: projektweite Werte unter `variables:` in `.meta-config/project.yaml`; Auto-injizierte Variablen im Konzeptdokument ablegen" (`docs/guides/features/sync-concept.md` existiert in W). Frontmatter `timestamp` auf `"2026-11-11"`. In `knowledge/wiki/log.md` eine Zeile `2026-11-11 HH:MM — update — core-principle-pal-variables: stale variable-table reference replaced (#1174)` anhängen (Uhrzeit zur Ausführungszeit). `index.md` bleibt unverändert, solange die Beschreibung gleich bleibt (OKF §6, im Plan nicht gegen `knowledge/schema.md` geprüft).
- [ ] Step 4: `python3 -m pytest tests/test_wiki_stale_variable_table_refs.py` — 2 passed. Danach Link-/Index-Pflege per `knowledge-gardener`, Lint per `knowledge-linter` über den Orchestrator (kein Lauf in dieser Planung).
- [ ] Step 5: Commit `docs: replace stale variable table reference in pal wiki page`

---

### Task 10: #1173 — Tier-Preset-Speichern verliert YAML-Kommentare (Entscheidung 22: Diff-Guard)
**Agent:** developer
**Files:**
- Modify: `scripts/admin-server.py`
- Create: `tests/test_admin_tier_presets_update.py`
(`docs/ui/admin-ui.html` bleibt in Task 10 unverändert: Fehleranzeige über bestehenden Toast, siehe Step 3.)

**Interfaces:**
- Consumes: `AdminRequestHandler._handle_post_tier_presets_update()` (`scripts/admin-server.py:5065`), `lib.yaml_roundtrip.assert_roundtrip_preserved(original_text, new_text, *, context, allow_lossy)` und `ALLOW_LOSSY_KEY` (`scripts/lib/yaml_roundtrip.py:184`, `:38`), `lib.io.yaml_dump_preserving_multiline(yaml_module, data, stream=None, **kwargs)` (`scripts/lib/io.py:409`)
- Produces: Guard wie bei ai-providers (`admin-server.py:4983-5000`), HTTP 400 ohne `__allow_lossy__`; UI-Anzeige des 400-Falls über den bestehenden Toast (kein neuer Code)

Befund in W: `yaml.dump(data, fh, default_flow_style=False, sort_keys=False)` bei `:5089` (Issue-Anker stimmt). Die Annahme des Issues, ein Kommentar-erhaltender Writer existiere, stimmt nicht: `yaml_dump_preserving_multiline` (`io.py:409-434`) erzwingt nur Block-Literal-Stil für mehrzeilige Strings und erhält keine Kommentare. Kommentar-Schutz im Repo = Diff-Guard `yaml_roundtrip` (bricht ab, schreibt keine Kommentare zurück; "ruamel.yaml is not allowed", `yaml_roundtrip.py:5-8`), eingesetzt für ai-providers (Issue #847). Die UI sendet `/api/tier-presets/update` ohne `__allow_lossy__` (`docs/ui/admin-ui.html:10907`, `:10950`); ein Guard allein macht das Speichern bei kommentierter Datei zu HTTP 400. Entscheidung 22 (Variante a) ist beantwortet: Diff-Guard wie bei ai-providers, HTTP 400 bei kommentierter Datei ohne `__allow_lossy__`, UI zeigt den Fehler an.
**PR-Notiz (Entscheidung 22):** Akzeptanzkriterium "Kommentare bleiben erhalten" des Issues ist mit dieser Lösung NICHT erfüllt; der Guard verhindert nur stillen Kommentarverlust. Im PR-Text ausdrücklich vermerken. Zweite Folge (gemessen in W), ebenfalls in den PR-Text: `config/tier-presets.yaml` dieses Repos enthält einen Kommentar (`:24`), daher liefert der UI-Save hier nach dem Fix immer HTTP 400 (die UI sendet kein `__allow_lossy__`). Das entspricht dem bestehenden ai-providers-Verhalten (`config/ai-providers.yaml` hat 234 Kommentarzeilen, UI-Save `admin-ui.html:10845` ohne `__allow_lossy__`), also dem Muster, das Entscheidung 22 vorgibt.
**Ist-Befund UI:** `docs/ui/admin-ui.html` enthält kein `__allow_lossy__` (Suche in W ohne Treffer); die 400-Fehlermeldung erscheint über den vorhandenen Toast-Pfad (Step 3), es wird nichts neu gebaut.

- [ ] Step 1: Test-Rahmen nach dem Muster `tests/test_ai_providers_roundtrip_847.py` (`_make_handler`, `_post_handler`, `handler._send_json = lambda result, status=200: captured.update(...)`, `:91-98`, `:212-217`); `config/tier-presets.yaml` im Temp-Root mit Kommentar anlegen, Payload = `yaml.safe_load` derselben Datei. Roter Test: `captured["status"] == 400` und Dateiinhalt unverändert; Zusatztest: Payload mit `ALLOW_LOSSY_KEY: True` schreibt (200) und der Schlüssel steht nicht in der Datei; Test: kommentarfreie Datei speichert wie bisher (200).
- [ ] Step 2: `python3 -m pytest tests/test_admin_tier_presets_update.py` — erwartet: rot (heute 200 und Kommentare weg).
- [ ] Step 3: Server: vor dem Schreiben `yaml_dump_preserving_multiline(yaml, data, default_flow_style=False, allow_unicode=True, sort_keys=False)` in `new_text` erzeugen, `ALLOW_LOSSY_KEY` aus `data` poppen (Pflicht VOR der Validierungsschleife `admin-server.py:5071-5078`, Muster `:4957`; sonst wird `__allow_lossy__` als ungültiger Preset mit HTTP 400 abgewiesen), `assert_roundtrip_preserved(...)` mit `context=f"config/{path.name}"`, bei `YamlRoundTripLoss` HTTP 400 (Muster `:4985-4999`); schreiben mit `fh.write(new_text)`. Nur dieser Handler ändert sich serverseitig.
  UI (Entscheidung 37-Messung in W, Korrektur): Die Save-Funktion (`saveBtn.onclick`, `docs/ui/admin-ui.html:10916-10959`, Aufrufe `:10950`; Anlage-Pfad `:10907`) hat KEIN Status-Element. Der bestehende Fehlerpfad ist `catch (err) { toast(err.message, "error"); }` (`:10953-10954`); `APIError` übernimmt `body.error` als Message (`admin-ui.html:1074-1078`), `api.post` wirft bei `!res.ok` (`:1025`). Ein HTTP-400 mit `{"error": ...}` wird damit ohne neuen Anzeige-Code angezeigt (Entscheidung 22: "Fehleranzeige in der UI" erfüllt); keine UI-Änderung in Task 10. Kein Bypass-Dialog (Entscheidung 22 verlangt keinen; ai-providers hat ebenfalls keinen).
- [ ] Step 4: `python3 -m pytest tests/test_admin_tier_presets_update.py tests/test_ai_providers_roundtrip_847.py tests/test_admin_server.py tests/test_tier_presets.py`. UI-Fehleranzeige: manuell im Browser (nicht verifiziert).
- [ ] Step 5: Commit (ein Commit je Task, Entscheidung 17): `fix: guard tier-preset save against silent comment loss`

---

### Task 11: #1206 — Auto-Commit-Save darf unbekannte Keys nicht löschen
**Agent:** developer
**Files:**
- Modify: `docs/ui/admin-ui.html`
- Create: `tests/test_admin_ui_auto_commit_section.py`

**Interfaces:**
- Consumes: `viewProjectAutoCommit()` (`docs/ui/admin-ui.html:7639`), `clone(obj)` (`:803`), `saveProjectSection(key, value, statusEl)` (`:5960`)
- Produces: Save-Pfad auf Basis `clone(ac)` (`ac` ist bereits ein Klon, `:7650`)

Befund in W: Save baut `const out = { mode }` neu (`:7753-7761`). Bestehender Browser-Test `tests/browser/test_git_admin_sections.py::test_auto_commit_custom_without_script_is_blocked_client_side` hängt an `#auto-commit-custom-script` und `#auto-commit-status` und muss unverändert grün bleiben. Der Schreibpfad `/api/config/project` ersetzt die Sektion als Ganzes (nicht verifiziert); der generische Schutz in `saveProjectSection` (Issue Punkt 3 "optional") wird nicht gebaut.

- [ ] Step 1: Roter statischer Test (Muster `tests/test_admin_ui_git_section.py:17`):
  ```python
  from pathlib import Path

  HTML = (Path(__file__).resolve().parent.parent / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")

  def _auto_commit_view():
      start = HTML.index("async function viewProjectAutoCommit()")
      end = HTML.index("/* --------------------------- Release Checklist")
      return HTML[start:end]

  def test_save_clones_loaded_object_instead_of_rebuilding():
      view = _auto_commit_view()
      assert "const out = { mode }" not in view
      assert "const out = clone(ac)" in view

  def test_save_drops_mode_specific_fields_outside_auto():
      view = _auto_commit_view()
      assert "delete out.triggers" in view
      assert "delete out.file_count_threshold" in view
  ```
- [ ] Step 2: `python3 -m pytest tests/test_admin_ui_auto_commit_section.py` — erwartet: 2 FAILED.
- [ ] Step 3: Save-Block (`:7753-7761`) ersetzen durch: `const out = clone(ac); out.mode = mode; if (mode === "auto") { out.triggers = triggers; out.file_count_threshold = <wie bisher geparst>; } else { delete out.triggers; delete out.file_count_threshold; } if (script) { out.custom_script = script; } else { delete out.custom_script; } out.secret_scan = ac.secret_scan !== false;` Validierungs-Gates davor (`:7735-7752`) unverändert.
- [ ] Step 4: Tests grün; Browser-Test `python3 -m pytest tests/browser/test_git_admin_sections.py` (benötigt Playwright, nicht verifiziert) und `python3 -m pytest tests/test_admin_ui_git_section.py tests/test_admin_ui_test_environments_section.py`. Manuell/Browser: `project.yaml` mit `auto_commit.authority_overrides` überlebt einen Save (nicht automatisiert, siehe Nicht verifiziert).
- [ ] Step 5: Commit `fix: keep unknown auto_commit keys on admin ui save`

---

### Task 12: #898 — Trigger als Checkbox-Gruppe, Inherit-Toggles geprüft, Claude-Modelle im Preis-Overlay
**Agent:** developer
**Depends on:** Task 11
**Files:**
- Modify: `docs/ui/admin-ui.html`
- Modify: `config/pricing-overlay.yaml`
- Modify: `tests/test_admin_ui_auto_commit_section.py`
- Create: `tests/test_pricing_overlay_current_models.py`

**Interfaces:**
- Consumes: `checkboxField(label, value, onChange, help)` (`admin-ui.html:6221`), `tagEditorField(label, values, onChange, helpText)` (`:6234`), `a11yField({ id, label, help, control })` (`:5992`), `ai-providers.yaml::providers.Claude.model-tiers` und `model-aliases` (`config/ai-providers.yaml:112-122`), `config/pricing-overlay.yaml::prices.anthropic`, models.dev-Funktionen (Teil B, Entscheidung 37, gemessen in W): `ModelsService._load_models_dev_data` (`scripts/admin-server.py:2846`; Quellen `_load_from_sdk_snapshot` `:2906`, `_load_from_models_dev_api` `:2957`, URL `https://models.dev/catalog.json` `:2961`), `ModelsService._apply_pricing_overlay` (`:2980`, Lesart `providers[<slug>].models[<id>].cost.input`/`.output`, Lesestelle `:3045-3057`), Import-Pfad `AdminRequestHandler._handle_post_models_dev_import` (`:4328`, Klasse `AdminRequestHandler` `:3319-5817`, schreibt `prices.<provider>.<key>` mit `input`/`output`), Key-Auflösung `ModelsService._resolve_registry_model_id` (`:3182`). Nicht das Ziel: Handler-Delegat `AdminRequestHandler._load_models_dev_data` (`:4278`, ruft nur `ModelsService` auf)
- Produces: Helfer `checkboxGroupField(label, options, selected, onChange, help)` (neu, neben `checkboxField`); Preiseinträge für die vier aktuellen Claude-IDs, aus dem models.dev-Payload übernommen (nicht von Hand)

Befund in W, Punkt 1: Trigger werden über `tagEditorField` (Freitext, `:7700-7705`) bearbeitet, nicht als Checkboxen. Schwellenwert-Feld `#auto-commit-threshold` ist immer sichtbar (`:7688-7710`). Punkt 2 ist bereits gebaut: Handler `admin-server.py` um `:4735-4813` (Roadmap-Anker `:4730`) und UI `docs/ui/admin-ui.html:8204-8291` (Select + Toggle, POST `/api/model-inherit`); hier wird nichts gebaut, nur im PR-Text als erledigt belegt. Punkt 3: Die IDs im Issue (`claude-haiku-4-5-20251001` usw.) sind veraltet; `config/ai-providers.yaml:113-122` führt `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`, `claude-fable-5-1`. `config/pricing-overlay.yaml` enthält diese vier IDs nicht (enthält `claude-sonnet-5`, `claude-fable-5`, ältere 4.x). Das UI-Dropdown ist datengetrieben (`list: "global-model-list"`, `:8155`); `grep` nach hartcodierten Claude-IDs in `admin-ui.html` findet nur den Platzhaltertext `claude-sonnet-5-5` (`:8155`).

**Teil A (Punkt 1, entscheidungsfrei):**
- [ ] Step 1: Roter Test in `tests/test_admin_ui_auto_commit_section.py`:
  ```python
  def test_triggers_use_checkbox_group_not_tag_editor():
      view = _auto_commit_view()
      assert 'tagEditorField(\n    "Triggers"' not in view and 'tagEditorField("Triggers"' not in view
      assert "checkboxGroupField(" in view
      assert "function checkboxGroupField(" in HTML

  def test_threshold_is_conditional_on_file_count_trigger():
      view = _auto_commit_view()
      assert "file-count-threshold" in view and "thresholdField.style.display" in view
  ```
- [ ] Step 2: `python3 -m pytest tests/test_admin_ui_auto_commit_section.py -k "checkbox_group or conditional"` — erwartet: 2 FAILED.
- [ ] Step 3: `checkboxGroupField` implementieren (je Option eine `<input type="checkbox">` mit `id="auto-commit-trigger-<name>"`, `onChange(selectedArray)` in der Reihenfolge von `TRIGGERS`, Hilfetext). In `viewProjectAutoCommit` das `tagEditorField` ersetzen; die `a11yField`-Hülle des Schwellenwerts bekommt eine Variable `thresholdField`, deren `style.display` bei jeder Änderung auf `ac.triggers` includes `file-count-threshold` und `mode === "auto"` gesetzt wird (initial gesetzt). Validierung (`:7735-7752`) und IDs `#auto-commit-custom-script`, `#auto-commit-status` unverändert.
- [ ] Step 4: Tests grün; Browser-Test `tests/browser/test_git_admin_sections.py` (Playwright, nicht verifiziert).
- [ ] Step 5: Kein eigener Commit für Teil A (Entscheidung 17: ein Commit je Task); Teil-A-Stand wird mit Teil B in den Task-12-Commit aufgenommen.

**Teil B (Punkt 3, Entscheidungen 23 und 37):** Preise kommen aus der bestehenden models.dev-Funktion des Projekts, NICHT von Hand und NICHT gespiegelt. Bestätigte Funktion (Entscheidung 37, Messung in W, Stand 9aa0e0c0): `scripts/admin-server.py`, Klasse `ModelsService` (`:2717-3318`): `_load_models_dev_data` (`:2846`, Quellen SDK-Snapshot `:2906` bzw. Live-API `:2957`, URL `https://models.dev/catalog.json` `:2961`), `_apply_pricing_overlay` (`:2980`, liest `cost.input`/`cost.output` je Modell unter `providers.anthropic.models`, Lesestelle `:3045-3057`), Import-Handler `AdminRequestHandler._handle_post_models_dev_import` (`:4328`, schreibt `prices.<provider>.<overlay_key>` mit `input`/`output`, Key-Auflösung `ModelsService._resolve_registry_model_id` `:3182`). Der Handler-Delegat `AdminRequestHandler._load_models_dev_data` (`:4278`) ist nur ein Weiterreicher und nicht das Ziel. In `scripts/lib/` gibt es keine models.dev-Funktion (Suche in W ohne Treffer).
Alte Aliase bleiben im Overlay (Tests pinnen sie, Entscheidung 23).

**Precondition P-12 (Entscheidung 37; vor Step 6, BLOCKER):** Prüfen, ob die vier aktuellen Claude-5.x-IDs im models.dev-Payload vorkommen.
- IDs (gelesen aus `config/ai-providers.yaml:112-122`, `model-tiers` und `model-aliases` ergeben genau diese vier): `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`, `claude-fable-5-1`.
- Gelesen in W (`config/pricing-overlay.yaml:1-60`): keine dieser vier IDs unter `prices.anthropic` (vorhanden sind u.a. `claude-sonnet-5`, `claude-fable-5`, `claude-haiku-4-5`, 4.x-Ids). Bestätigt den Befund; die Abdeckung im Payload ist damit der offene Punkt.
- Quelle: In W existiert kein SDK-Snapshot (`node_modules/@opencode-ai/models/dist/snapshot.js` nicht gefunden, Glob in W). Maßgeblich ist daher die Live-API, identisch zu `_load_from_models_dev_api` (`:2957-2979`, gleicher URL und UA `agent-meta-admin/1.0`, Timeout 30 s). Die Prüfung ist eine Nur-Lese-Abfrage außerhalb des Repos (`python3 -I`, Ausgabe nur auf stdout, keine Datei schreiben):
  `python3 -I -c "import json,urllib.request as u; r=u.Request('https://models.dev/catalog.json', headers={'User-Agent':'agent-meta-admin/1.0'}); m=json.load(u.urlopen(r, timeout=30))['providers']['anthropic']['models']; ids=['claude-haiku-5-5','claude-sonnet-5-5','claude-opus-5-5','claude-fable-5-1']; print({i: (i in m, (m.get(i) or {}).get('cost')) for i in ids})"`
- Entscheidungsregel: alle vier Ids vorhanden UND je ein `cost` mit `input` und `output` → Precondition erfüllt, Step 6 ff. weiter. Eine fehlende ID oder ein fehlender `cost` → Task 12 Teil B ist BLOCKED: nichts in `pricing-overlay.yaml` schreiben, keine Handwerte, Ergebnis (welche IDs fehlen) an den User zurückmelden.
- Ergebnis (Review 2026-11-11, obige Abfrage read-only ausgeführt): **erfüllt** — alle vier IDs vorhanden, je mit `cost.input`/`cost.output`: `claude-haiku-5-5` 0.1/0.5 (zusätzlich `cost.tiers` ab 100k Kontext 0.5/2.5), `claude-sonnet-5-5` 2/10, `claude-opus-5-5` 4/20, `claude-fable-5-1` 10/50. Live-Payload kann sich ändern: die Abfrage beim Umsetzen wiederholen; Werte nur aus diesem Lauf übernehmen. Hinweis: der Import-Pfad übernimmt nur `input`/`output`; `cost.tiers` von haiku geht nicht ins Overlay (bestehendes Verhalten `admin-server.py:4364-4365`).

- [ ] Step 6: Roter Test `tests/test_pricing_overlay_current_models.py`:
  ```python
  from pathlib import Path
  import yaml

  ROOT = Path(__file__).resolve().parent.parent

  def test_overlay_prices_every_current_claude_tier_and_alias_id():
      providers = yaml.safe_load((ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))["providers"]
      claude = providers["Claude"]
      ids = set(claude["model-tiers"].values()) | set(claude["model-aliases"].values())
      prices = yaml.safe_load((ROOT / "config" / "pricing-overlay.yaml").read_text(encoding="utf-8"))["prices"]["anthropic"]
      assert not [i for i in ids if i not in prices], sorted(ids - set(prices))
  ```
  Erwartet vor der Änderung: FAILED (vier fehlende IDs).
- [ ] Step 7: Werte aus dem models.dev-Payload lesen: `ModelsService._load_models_dev_data()` (`scripts/admin-server.py:2846`) liefert den models.dev-Katalog (Provider-Knoten `anthropic`; Schachtelung in W gelesen: `providers.anthropic.models.<id>.cost.input`/`.output`, Lesestelle `:3052-3057`, Docstring `:2988`). Für die vier IDs die Werte aus dem Payload (nur wenn Precondition P-12 beim Umsetzen erneut erfüllt ist; Review-Lauf 2026-11-11: erfüllt) über den bestehenden Import-Pfad (`AdminRequestHandler._handle_post_models_dev_import` `:4328`, Body `provider`, `model_id`, `input_cost` = `cost.input`, `output_cost` = `cost.output`; Key-Auflösung `_resolve_registry_model_id` `:3182`) in `config/pricing-overlay.yaml` unter `prices.anthropic` schreiben. Hinweis: der Import-Handler schreibt die gesamte Datei per `yaml.dump` neu (`:4372`); die Overlay-Datei enthält keine Kommentare (gelesen), daher kein Kommentarverlust. Kein Handschreiben der Zahlen. Nur ergänzen, nichts entfernen: Tests pinnen alte IDs (`tests/test_model_discovery.py:697-700`, `:778-781`, `tests/test_admin_server.py:412-428`), alte Aliase bleiben (Entscheidung 23). Fehlt eine der vier IDs oder ein `cost`, gilt P-12: BLOCKED, zurückmelden.
- [ ] Step 8: `python3 -m pytest tests/test_pricing_overlay_current_models.py tests/test_model_discovery.py tests/test_admin_server.py tests/test_eval_baseline_schema.py`.
- [ ] Step 9: Ein Commit für Task 12 (Entscheidung 17): `fix: correct auto-commit trigger UI and claude price overlay`

---

### Task 13: #317 — Live-Subprozess-Test für Viz-Subserver-Steuerung
**Agent:** tester
**Files:**
- Create: `tests/test_viz_subserver_live.py`

**Interfaces:**
- Consumes: `admin_server.VizManager(root)` mit `start_viz() -> bool`, `stop_viz() -> bool`, `restart_viz() -> bool`, `status() -> dict` (`scripts/admin-server.py:597`, `:749-783`, `:820`), `AdminRequestHandler._match_subserver_route(path)` (`:4208`), `_handle_subserver_action(name, action)` (`:4232`), `viz-report.py --serve --port --timeout` (`scripts/viz-report.py:953-961`), View `viewVizDashboard` (`docs/ui/admin-ui.html:9526`)
- Produces: nichts (Testmodul)

Befund in W: Die Issue-Pfade stimmen nicht ganz: UI liegt in `docs/ui/admin-ui.html` (nicht `docs/admin-ui.html`); der Viz-Subserver ist `scripts/viz-report.py` (kein `viz-server.py`-Start). `VizManager` löst Skripte über `resolve_asset(root, "scripts", name)` auf, ein Temp-Root braucht deshalb ein `scripts`-Symlink auf `REPO_ROOT/scripts` (POSIX; Windows überspringen). Der Port kommt aus `.meta-config/project.yaml` (`viz.server.port`, `_load_viz_config` `:483-518`); bei Parse-Fehler fällt `_load_viz_config` still auf Port 8765 zurück, daher prüft der Test `status()["viz"]["port"] == port`. Bestehende Tests nutzen `--no-viz`/keinen Subprozess (Suche nach `VizManager` in `tests/`: keine Treffer). Browser-seitiges iframe-Rendering bleibt außerhalb dieses Tasks (Playwright, nicht verifiziert); die UI-Verdrahtung wird statisch gepinnt.

- [ ] Step 1: Test schreiben (Modulladung wie `tests/test_admin_server.py:41-51`, `admin_server` laden):
  ```python
  @pytest.mark.skipif(sys.platform == "win32", reason="symlinked scripts + POSIX signals")
  def test_viz_start_restart_stop_live(viz_root):
      root, port = viz_root
      vm = admin_server.VizManager(root)
      assert vm.status()["viz"]["running"] is False
      assert vm.start_viz() is True
      st = vm.status()["viz"]
      assert st["running"] is True and st["port"] == port   # catches silent config fallback
      assert _wait_http(st["url"])                         # dashboard answers HTTP 200
      pid1 = st["pid"]
      assert vm.restart_viz() is True
      st2 = vm.status()["viz"]
      assert st2["running"] is True and st2["pid"] != pid1
      assert _wait_http(st2["url"])
      assert vm.stop_viz() is True
      assert vm.status()["viz"]["running"] is False
      with pytest.raises(OSError):
          urllib.request.urlopen(st2["url"], timeout=2)
  ```
  Fixture `viz_root(tmp_path)`: `scripts`-Symlink, `.meta-config/project.yaml` mit gültigem Mindestinhalt (Vorlage: `tests/test_cli_smoke_multi_provider.py:30-43`) plus `viz:\n  server:\n    port: <freier Port>\n    timeout_sec: 60`; Teardown `admin_server.VizManager(root).stop_all()`. `_wait_http(url, timeout=15)` pollt `urllib.request.urlopen` bis Status 200. Zweiter Test: `_handle_subserver_action("viz", "start")` über `AdminRequestHandler.__new__` mit `monkeypatch.setattr(AdminRequestHandler, "viz_manager", vm, raising=False)` und abgefangenem `_send_json`; erwartet `captured["success"] is True`, `captured["status"]["viz"]["running"] is True`; plus `_match_subserver_route("/api/subserver/viz/restart") == ("viz", "restart")` und `_match_subserver_route("/api/subserver/evil/start") is None`. Dritter Test (statisch): `viewVizDashboard`-Text enthält `el("iframe"`, `lastVizUrl` und `` `/api/subserver/${name}/${action}` ``.
- [ ] Step 2: `python3 -m pytest tests/test_viz_subserver_live.py` — erwartet: ein roter Lauf nur, falls die Fixture-Annahmen falsch sind (Test-only-Task; "rot" = erster Lauf zeigt die Annahmen, Ergebnis im PR-Text vermerken).
- [ ] Step 3: Kein Produktivcode, außer die Tests decken einen echten Fehler auf; dann eigenes Issue statt Scope-Erweiterung.
- [ ] Step 4: `python3 -m pytest tests/test_viz_subserver_live.py tests/test_admin_server.py` grün; danach `pgrep -f viz-report.py` zeigt keinen übrig gebliebenen Prozess (manuell).
- [ ] Step 5: Commit `test: add live subprocess test for viz subserver controls`

---

## Abweichung zur Roadmap

1. #1194: Roadmap nennt `context.py:1710`/`opencode_v2_config.py:513`. In W liegt die Ursache in `context.py:1815` (`apply_settings_surface_shape`), `:1899`/`:1927` (nur Init). Die Korrektur wird in `opencode_v2_config.py` (`sync_opencode_v2_managed_keys` `:680`) und `artifact_validate.py` (`:436`) umgesetzt; `context.py` bleibt unberührt. (Anker in 9aa0e0c0: `context.py:1815`, `:1899`, `:1927`; Roadmap-Welle-1-Zeile nennt weiter `context.py:1710`.) Folge: Welle 1 berührt `context.py` nicht, die Reihenfolge B-vor-C ist für diese Datei unkritisch.
2. #1170: Issue nennt `:854`, Roadmap `:885`. In W `:885` korrekt. Zusätzlich existiert ein Textverweis in `config/provider-capabilities.yaml:290`.
3. #1173: Das vorhandene "comment-preserving writer" gibt es nicht. `yaml_dump_preserving_multiline` (`scripts/lib/io.py:409`) erhält nur Block-Literal-Stil. Echter Schutz ist der Diff-Guard `lib/yaml_roundtrip.py`. Folge: Entscheidung 22 (Diff-Guard); AK "Kommentare bleiben erhalten" nicht erfüllt (im PR vermerkt).
4. #898: Punkt 2 ist gebaut (`admin-server.py:4735-4813`, `admin-ui.html:8204-8291`). Modell-IDs im Issue sind veraltet (`ai-providers.yaml:113-122`: 5.x-IDs). Punkt 1 stimmt (`admin-ui.html:7699-7705`). Punkt 3: Preise über die models.dev-Funktion (Entscheidungen 23, 37: `ModelsService`, nicht `scripts/lib/`). Abdeckung der vier IDs im Payload: Precondition P-12, Ergebnis offen.
5. #1205: Punkt 3 des Issues (unbekannte Keys einzeln melden, Block nicht invalidieren) wird nicht in B umgesetzt; er kollidiert mit `test_unknown_values_and_keys` und Entscheidung 3 (#1142, Phase C). AK 4 des Issues (`--validate` = Sync-Findings) gehört ebenfalls zu #1142.
6. #1197: In der Roadmap als schlichter S-Bug geführt, tatsächlich Teil des APPROVED-Plans von #1187 (T9). Phase B liefert nur den Ratchet. Die Issue-AK 1 und 3 bleiben bei #1187; #1197 kann erst mit #1187-T9 geschlossen werden (Entscheidung 34, B-N4).
7. #1207: Die Spec ist "Entwurf" (`docs/specs/767-auto-commit-permission-authority.md:2`), nicht APPROVED; Ankerliste der Roadmap/Issue sonst bestätigt, in 9aa0e0c0 verschoben: `auto_commit.py:28/:146/:322/:34`, `sync_pipeline.py:1974` (Roadmap `:1893`), `config.py:1622/:1838` (Roadmap `:1621/:1837`), Guard-Allowlist `:448`.
8. #317: UI-Pfad ist `docs/ui/admin-ui.html`; Subserver-Skript ist `viz-report.py`.
9. #1213/#1214: Zeilenanker bestätigt (`spec_plan.py:490-492`, `:50`, `:318-323`; `plan_identity.py:27`).
10. #1174: `agents/agent-meta-developer.md` existiert in W nicht (wie in Roadmap); zusätzlicher Fund `_inject_dod` auf der Wiki-Seite ohne Entsprechung in `scripts/lib/`.
11. #1139: Bestätigt (`tests/test_cli_smoke_multi_provider.py:53`, `SLOW_TIMEOUT` ungenutzt). `SYNC_TIMEOUT` (Default 180) ist kleiner als die heutigen 300 s, daher `SLOW_TIMEOUT`.

## Entscheidungen (beantwortet)

Quelle: Roadmap-Entscheidungen 17-34 (`.tmp/decisions-part2.md`) und 37 (`.tmp/decisions-part3.md`), User-beantwortet.

- **B-N1 (#1213) = Entscheidung 34:** `spec_plan_no_tasks_detected` ist WARNING; Approval-Gate bleibt ERROR. Umgesetzt in Task 5.
- **B-N2 (#1173) = Entscheidung 22:** Diff-Guard wie bei ai-providers (HTTP 400 ohne `__allow_lossy__`), UI zeigt den Fehler an. AK "Kommentare bleiben erhalten" ist explizit NICHT erfüllt (PR-Notiz, Task 10). Umgesetzt in Task 10.
- **B-N3 (#898 Punkt 3) = settled durch Entscheidungen 17-19, 23, 37:** Preise kommen aus der bestehenden models.dev-Funktion (nicht von Hand, nicht gespiegelt); alte Aliase bleiben (Tests pinnen sie). Funktion durch Entscheidung 37 bestätigt: `ModelsService` in `scripts/admin-server.py` (`_load_models_dev_data`, `_apply_pricing_overlay`, Import-Handler `_handle_post_models_dev_import`), Anker in W neu gemessen (Task 12 Teil B). Umgesetzt in Task 12 Teil B, gated durch Precondition P-12.
- **Entscheidung 37 (#898 Punkt 3, Funktionsbestätigung):** Der Nutzer bestätigt `ModelsService` (`scripts/admin-server.py`) als gemeinte Funktion. Plan-Anpassung: Task 12 Teil B, Precondition P-12 (Abdeckung der vier Claude-5.x-IDs im models.dev-Payload; BLOCKED bei Fehlen), Anker neu gemessen.
- **Entscheidung 37 (Anker Task 10):** Tier-Preset-Save-Pfad in W gemessen (`_handle_post_tier_presets_update` `:5065`, `yaml.dump` `:5089`, Guard-Muster `:4983-5000`, UI-Aufrufe `admin-ui.html:10907`, `:10950`): Zeilen unverändert. Korrektur: Die UI hat kein Status-Element; die Fehleranzeige läuft über den bestehenden Toast (`:10953-10954`). `ALLOW_LOSSY_KEY`-Pop muss vor der Validierungsschleife stehen (`:5071`).
- **Verfahren Abdeckung der vier Claude-5.x-IDs im models.dev-Payload (Entscheidung 37):** als Precondition P-12 in Task 12 Teil B festgelegt (Prüfmethode, Entscheidungsregel BLOCKED). Das Ergebnis ist ein Ausführungsfakt; Review-Lauf 2026-11-11: erfüllt (alle vier IDs mit `cost`), beim Umsetzen wiederholen.
- **Konflikt Entscheidung 23 vs. Code (Entscheidung 37):** durch den Nutzer geklärt: `ModelsService` in `scripts/admin-server.py` ist die gemeinte Funktion. Keine Funktion in `scripts/lib/` nötig.
- **B-N4 (#1197) = Entscheidung 34:** Umsetzung über #1187-T9; Phase B liefert nur den Ratchet-Test (Task 8). #1197 erst mit #1187-T9 schließbar.
- **B-N5 (#1139) = Entscheidung 34:** kein `pytest.skip`; der 900-s-Hang-Guard genügt (Task 1).
- **Entscheidung 17 (PR-Schnitt):** strikt ein Phasen-PR, ein Commit je Task (13 Commits).

## Offene Entscheidungen (neu, ungeklaert)

Keine. (Review 2026-11-11: Der frühere Punkt "Anzeige-Design Tier-Preset-Fehler" ist keine offene Entscheidung — Entscheidung 22 verlangt eine Fehleranzeige in der UI, der bestehende Toast `admin-ui.html:10953-10954` erfüllt sie; eine zusätzliche Statusmeldung hat niemand angefragt. Precondition P-12 ist ein Ausführungsfakt, kein User-Entscheid, und im Review-Lauf erfüllt.)

## Frische-Check-Referenzen

- Issues: #1194, #1197, #1205, #1206, #1207, #1213, #1214, #1139, #1170, #1174, #1173, #898, #317, #1187, #1142, #854, #1160, #847
- `scripts/lib/context.py` (`apply_settings_surface_shape`, `_init_provider_settings_json`)
- `scripts/lib/opencode_v2_config.py` (`sync_opencode_v2_managed_keys`, `build_managed_keys`)
- `scripts/lib/artifact_validate.py` (`_validate_opencode_v2`, `validate_json_document`, `_finding`)
- `scripts/lib/auto_commit.py` (`_KEYS`, neu: `_STATIC_KEYS`, `_SCHEMA_PATH`, `_load_schema_keys`; bestehend: `auto_commit_violations`, `resolve_auto_commit_config`, `_ELIGIBLE_TOOLS`, `is_role_eligible`, `role_commit_authority`, `render_auto_commit_block`, `AUTHORITY_DIRECT`)
- `scripts/lib/consistency/spec_plan.py` (`_check_approval_markers`, `_parse_plan_tasks`, `parse_plan_ledger`, `_classify`, `_matches_template`, `_DESIGN_RE`, `_APPROVED_RE`, `check_spec_plan_workflow`, `REQUIRED_SPEC_SECTIONS`; neu: `_SPEC_RE`, `_TASK_LIKE_HEADER_RE`, `_check_task_detection`)
- `scripts/lib/plan_identity.py` (`TASK_HEADER_RE`)
- `scripts/lib/provider_transform.py` (`_map_claude_tools_to_gemini_tools`)
- `scripts/lib/io.py` (`yaml_dump_preserving_multiline`)
- `scripts/lib/yaml_roundtrip.py` (`assert_roundtrip_preserved`, `ALLOW_LOSSY_KEY`, `YamlRoundTripLoss`)
- `scripts/lib/config.py` (`_build_core_variables`, `build_variables`)
- `scripts/lib/sync_pipeline.py` (`_sync_stage_auto_commit_allowlist`)
- `scripts/lib/agent_sync.py` (`_tools_can_spawn`, `sync_agents_for_provider`)
- `scripts/admin-server.py` (`_handle_post_tier_presets_update` `:5065` (yaml.dump `:5089`), `_handle_post_ai_providers_update` `:4941` (Guard `:4983-5000`), `VizManager`, `_match_subserver_route`, `_handle_subserver_action`, `_load_viz_config`, `resolve_asset`, `ModelsService` `:2717`: `_load_models_dev_data` `:2846`, `_load_from_sdk_snapshot` `:2906`, `_load_from_models_dev_api` `:2957`, `_apply_pricing_overlay` `:2980`, `_resolve_registry_model_id` `:3182`; `AdminRequestHandler._handle_post_models_dev_import` `:4328`; Handler-Delegat `_load_models_dev_data` `:4278`; Stand W 9aa0e0c0, gemessen Entscheidung 37)
- `https://models.dev/catalog.json` (Live-Payload, Gegenstand von Precondition P-12; Abfrage im Review 2026-11-11 ausgeführt)
- `scripts/viz-report.py`
- `docs/ui/admin-ui.html` (`viewProjectAutoCommit`, `viewVizDashboard`, `viewTierPresets` `:10856` (Save `:10916-10959`, Toast-Fehlerpfad `:10953-10954`), `APIError` `:1074`, `api.post` `:1019`, `checkboxField`, `tagEditorField`, `a11yField`, `clone`, `saveProjectSection`, `checkboxGroupField` (neu))
- `config/project-config.schema.json`
- `config/provider-capabilities.yaml`
- `config/ai-providers.yaml`
- `config/pricing-overlay.yaml`
- `config/tier-presets.yaml`
- `rules/1-generic/spec-plan-workflow.md`
- `docs/specs/767-auto-commit-permission-authority.md`
- `docs/specs/2026-11-09-project-context-injection-scope-spec.md`
- `docs/plans/2026-11-09-project-context-injection-scope-plan.md`
- `hooks/1-generic/orchestrator-guard-impl.sh`
- `agents/1-generic/ui-ux-designer.md`
- `agents/1-generic/bug-feature-analyzer.md`
- `agents/1-generic/knowledge-curator.md`
- `agents/1-generic/knowledge-migrator.md`
- `knowledge/wiki/concepts/core-principle-pal-variables.md`
- `knowledge/wiki/log.md`
- `tests/timeouts.py`
- `tests/test_cli_smoke_multi_provider.py`
- `tests/test_timeouts_usage.py`
- `tests/test_dead_gemini_tool_map_removed.py`
- `tests/test_opencode_v2_surface.py`
- `tests/test_auto_commit_violations.py`
- `tests/test_spec_plan_consistency.py`
- `tests/test_spec_767_anchors.py`
- `tests/test_project_context_placeholder_ratchet.py`
- `tests/test_wiki_stale_variable_table_refs.py`
- `tests/test_admin_tier_presets_update.py`
- `tests/test_ai_providers_roundtrip_847.py`
- `tests/test_admin_ui_auto_commit_section.py`
- `tests/test_pricing_overlay_current_models.py`
- `tests/test_viz_subserver_live.py`
- `tests/browser/test_git_admin_sections.py`

## Nicht verifiziert

- Keine Testausführung, kein `sync.py --validate` (alle Test-Erwartungen oben sind Plan-Werte). Vollscan von `check_spec_plan_workflow` im Review versucht: Absturz `OSError` Errno 36 (siehe Task 5 Step 4); Vorher/Nachher-Zählung daher offen. Gemessen statt gezählt: Regex-Treffer (Task 5) und `_APPROVED_RE`-Lücke.
- Task 1: tatsächliche Laufzeit von `tests/test_cli_smoke_multi_provider.py` auf belasteter Hardware; AK 3 des Issues ("grün auf belastetem Host") nicht belegbar ohne Lauf.
- Task 3: Der Test `test_dead_key_removal_is_idempotent` ist in Step 1 beschrieben, nicht ausformuliert (Helfer-Signaturen und `SyncLog.action(tag, target, source)` `scripts/lib/log.py:29` im Review gelesen).
- Task 5: Regex `_TASK_LIKE_HEADER_RE` im Review gegen `docs/plans`, `docs/superpowers/plans`, `docs/specs` gemessen (5 Treffer, alle echte Task-Header); Findings-Wirkung im Gesamtcheck nicht ausgeführt.
- Task 6: Rule-Änderung löst Re-Sync gerenderter Dateien aus (Regel wird laut `config/rules-presets.yaml:176-178` per Skill-Kanal ausgeliefert); ob Golden-Fixtures (`tests/fixtures/*-golden/`) den Regeltext pinnen, nicht geprüft.
- Task 9: Wiki-Lint (`knowledge-linter`) und OKF-Index-Regeln (`knowledge/schema.md`) nicht gelesen.
- Task 10: UI-Fehlerpfad im Tier-Preset-Save in W gelesen (Toast, kein Status-Element; Entscheidung 37). Nicht im Browser geprüft; Toast-Darstellung eines 400-Bodys nicht live getestet.
- Task 11: ob `/api/config/project` die Sektion `auto_commit` ersetzt oder mergt; kein Browser-Lauf (Playwright).
- Task 12: Verhalten der UI nach `checkboxGroupField` nicht im Browser geprüft.
- Task 12 Teil B, Precondition P-12: im Review 2026-11-11 erfüllt; der Live-Payload kann sich bis zur Umsetzung ändern (Abfrage wiederholen, bei Fehlen BLOCKED).
- Task 12 Teil B: Schachtelung `providers.anthropic.models.<id>.cost` ist aus `_apply_pricing_overlay` (`:3045-3057`) gelesen (Entscheidung 37); im Review-Lauf am Live-Payload bestätigt (`providers.anthropic.models.<id>.cost`). Kein SDK-Snapshot in W vorhanden (Glob ohne Treffer), daher nur der API-Pfad.
- Task 13: gültiger Mindestinhalt der Temp-`project.yaml`, Erreichbarkeit des Viz-Servers per HTTP 200 und Port-Rennen (freier Port wird vor dem Start ermittelt) nicht geprüft; Windows nicht abgedeckt.
- Roadmap-Aussage "#1170 ohne Aufrufer": nur per Textsuche in W belegt (Suche ohne `.tmp/`), kein dynamischer Nachweis.

## Self-Review

- Jeder der 13 Issues ist genau einem Task zugeordnet: #1139 T1, #1170 T2, #1194 T3, #1205 T4, #1213 T5, #1214 T6, #1207 T7, #1197 T8, #1174 T9, #1173 T10, #1206 T11, #898 T12, #317 T13.
- Spec-Gates: 0 (alle S; #1197 verweist auf bestehende APPROVED-Spec von #1187). Entscheidungen 17, 22, 23, 34 eingearbeitet (Abschnitt "Entscheidungen (beantwortet)"); Task 10 und Task 12 Teil B sind damit ausführbar. Entscheidung 37 eingearbeitet: #898-Funktion bestätigt (`ModelsService`), Precondition P-12 vor Task 12 Step 6 (BLOCKED-Regel). Precondition P-12 im Review-Lauf erfüllt (beim Umsetzen wiederholen); keine offenen User-Entscheidungen (siehe "Offene Entscheidungen (neu, ungeklaert)").
- PR-Schnitt konsistent mit Entscheidung 17: ein Phasen-PR, 13 Commits (ein Commit je Task; Task 12 ohne Teilcommit).
- Entscheidung 22 und 23 gegen Code geprüft: Diff-Guard-Muster `admin-server.py:4983-5000`; models.dev-Funktionen `admin-server.py:2846`, `:2980`, `:4328` (nicht in `scripts/lib/`).
- Entscheidung 37 (Re-Messung in W, 9aa0e0c0): Anker `:2846`, `:2980`, `:4328`, `:5065`, `:5089`, `:4983-5000`, `:10907`, `:10950` unverändert; `:4278` ist Handler-Delegat (`AdminRequestHandler`, nicht das Ziel) und wurde als Ziel entfernt. Abweichung: Tier-Preset-UI hat kein Status-Element (Toast-Pfad), Pop-Reihenfolge `ALLOW_LOSSY_KEY` vor `:5071` korrigiert. Vier Claude-5.x-IDs aus `ai-providers.yaml:112-122` gelesen; `pricing-overlay.yaml` enthält keine davon (gelesen).
- Jeder Task nennt eine Rolle (`developer`, `tester`, `documenter`, `knowledge-gardener`), `Files:` und `Interfaces:`; Dateiüberlappungen (Task 5/6 in `spec_plan.py`, Task 11/12 in `admin-ui.html`) sind über `Depends on:` sequentiell.
- Alle Signaturen und Zeilenanker stammen aus Lesezugriffen in W (ursprünglich `a3d65da4`, im Review 2026-11-11 gegen `9aa0e0c0` nachgemessen und korrigiert); nicht Gelesenes ist in "Nicht verifiziert" aufgeführt.
- Keine Platzhalter im Plan; zwei Stellen (Task 3 Idempotenz-Test, Task 13 Fixture) sind bewusst als Ausformulierungsauftrag mit vollständiger Soll-Beschreibung angegeben.
- `pipeline_stages` im Frontmatter vorhanden; Plan-Status DRAFT; Aufwandsschätzung: `effort-estimator` (Textverweis, hier nicht berechnet).
