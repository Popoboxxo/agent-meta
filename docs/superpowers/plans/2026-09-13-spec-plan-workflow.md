# Nativer Spec/Plan-Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Entscheidungen F2–F12 der Design-Spezifikation als nativen, abschaltbaren Feature-Workflow (Spec → Plan → Execution) implementieren: ein zentraler Master-Switch, DoD-Kopplung, Config+Schema, Rule-Gating, Pipeline-Wiring, eigenständiger Validator, Knowledge-Engine-Anbindung, Rollen-/Regel-Erweiterung und Szenario/CI — stdlib-only, ohne Worktree, provider-agnostisch.

**Architecture:** Fundament ist eine einzige Helper-Funktion `resolve_spec_plan_enabled` in `scripts/lib/dod.py`, deren Ergebnis am Ende von `resolve_dod()` als synthetischer Key `spec-plan-enabled` injiziert wird. Aus diesem einen Seed leiten sich Rule-Auslieferung (intrinsisches, fail-closed Gate in `collect_rule_sources`), Pipeline-Stage-Gating (`condition: {dod_flag: spec-plan-enabled}`), Agent-Template-Conditional (`SPEC_PLAN_WORKFLOW_ENABLED`, als strippbares Flag registriert) und der Consistency-No-op ab. Config, Schema und DoD-Presets deklarieren die Oberfläche; ein neuer Validator-Modus `--validate-spec-plan` nutzt ausschließlich den Graph-Validator aus `orchestration.py`; ein Sync-Scaffold-Schritt legt die neutralen Zielpfade `docs/specs`/`docs/plans`/`docs/spikes` inkl. `.gitkeep` an (analog KE-Scaffolding); Rules und Rollen tragen den Prozess; ein Szenario plus CI-Anbindung pinnen das Verhalten.

**Tech Stack:** Python 3.9+ stdlib only (PyYAML bleibt optionale Soft-Dependency via `scripts/lib/io._load_yaml_or_json`), pytest (inkl. test-only `jsonschema`), `tests/scenarios/`-Harness, Markdown-Templates (Rules/Rollen) mit YAML-Frontmatter.

**Spec:** `docs/superpowers/specs/2026-09-13-spec-plan-workflow-design.md`

## Global Constraints

- Default-Pfade sind neutral: `docs/specs`, `docs/plans`, `docs/spikes`. Ein Sync-Scaffold-Schritt (`scripts/lib/spec_plan_scaffold.py`) legt diese Pfade bei `effective_enabled=true` an — `paths.plans`/`paths.spikes` nur, falls sie fehlen, jeweils inkl. `.gitkeep` (analog KE-Scaffolding in `scripts/lib/knowledge.py`). Bei `effective_enabled=false` findet **kein** Scaffold statt. `docs/superpowers/*` bleibt nur lesbar (Legacy), kein Massen-Umzug.
- `effective_enabled=false` ist durchgängig No-op: Rule-Auslieferung, Pipeline-Stages, Agent-Templates, Consistency-Check (`return []`), Index/Archiv und Orchestrator-Gate dürfen keine Wirkung entfalten (§10.1).
- Fail-closed Gate: `collect_rule_sources(agent_meta_root, platforms, *, config)` bekommt `config` als verpflichtenden Keyword-Parameter; ein vergessener Call-Site führt zu `TypeError`. Explizit `config=None` bedeutet: gated Rules werden **nicht** ausgeliefert.
- Keine neuen externen Dependencies — Python stdlib only; PyYAML/PyYAML-Loader bleibt die bestehende Soft-Dependency über `scripts/lib/io._load_yaml_or_json`. `jsonschema` bleibt reine Test-Dependency (`pytest.importorskip`).
- Kein Worktree: niemals `isolation: "worktree"`; Isolation ausschließlich über Datei-Ownership + Barrieren (`check_plan_file_overlap`) + Checkpoint-Recovery.
- Provider-Unterschiede nur über Config-Keys/Capability-Flags ausdrücken, nie über `if provider == "Name"`.
- Rollen-Version-Bumps sind Pflicht: Frontmatter-`version` jeder geänderten Rolle bumpen. Rückwärtskompatible Erweiterungen und rein additive neue Pflichtsektionen erhalten einen **Minor**-Bump (`x.Y.0`). Vorhandene `2-platform`-Overrides zusätzlich `version` + `based-on` aktualisieren (real betroffen: `agents/2-platform/homeassistant-documenter.md`).
- Keine Massen-Migration von `docs/superpowers/*` oder bestehenden `docs/plans/*`; Legacy wird nur gelesen.
- F1 (`systems-engineering`-Schema-Deklaration) ist ausdrücklich out-of-scope und wird **nicht** implementiert; nur der Hinweis-Abschnitt unten.
- `execute_plan` bleibt out-of-scope; nur der Graph-Validator (`FanoutPlan`/`validate_plan`/`check_plan_file_overlap`) wird verdrahtet (F6).
- Spec-Referenz zwischen Phasen läuft über das A2A-/Payload-Feld `spec_ref` — **kein** neuer `role-defaults`-Key, kein Config-Key ohne Consumer.
- Index-Routing (D8): `external-system-override.enabled: true` **oder** `knowledge-engine.enabled: false` ⇒ KE-Schreibpfade werden übersprungen und der `file-index`-Fallback greift (`index.fallback-index`, Default `docs/INDEX.md`). `okf.auto-index`/`okf.auto-log` steuern dagegen nur das automatische Schreiben/Aktualisieren der Index-/Log-Einträge (Default `true`); bei `false` werden die Dateien weiterhin gescaffoldet und agent-driven (`planner`/`knowledge-ingestor`→`knowledge-indexer`) gepflegt.
- Conventional Commits: `<type>: <description>`, max 72 Zeichen erste Zeile, Imperativ, Englisch.
- Spec/Plan-Block: kein Top-Level-`default`, `enabled` ohne `default` — Absenz muss von „explizit gesetzt“ unterscheidbar bleiben (§5.2/§5.4).
- Jedes neue Feature/jede neue `project.yaml`-Option erhält zeitgleich Szenario + Assert (`tests/scenarios/registry.md`-Konvention).
- Sprache: Prosa Deutsch, Code/Symbole/Pfade/Commit-Messages Englisch.

## File Structure

| Aktion | Pfad | Verantwortlichkeit |
|---|---|---|
| Modify | `scripts/lib/dod.py` | `resolve_spec_plan_enabled` + Injektion in `resolve_dod()` |
| Modify | `scripts/lib/config.py` | `SPEC_PLAN_WORKFLOW_ENABLED`/Pfad-Variablen; `dod=`-Passthrough |
| Modify | `scripts/lib/variables.py` | `SPEC_PLAN_WORKFLOW_ENABLED` in die Conditional-Liste (`strip_inactive_conditional_blocks`) |
| Modify | `scripts/lib/consistency/placeholders.py` | `SPEC_PLAN_WORKFLOW_ENABLED`/`SPEC_PLAN_SPECS_DIR`/`SPEC_PLAN_PLANS_DIR` in `_BUILTIN_VARS` |
| Modify | `scripts/lib/standalone.py` | `SPEC_PLAN_WORKFLOW_ENABLED: "false"` in `_CONDITIONAL_FALSE_FLAGS` |
| Modify | `config/dod-presets.yaml` | neue Keys `spec-plan-required`/`spec-plan-traceability` in `full` + relevante Presets |
| Modify | `config/project-config.schema.json` | `dod`-Keys, `dod-preset`-Enum `concept-driven`, `spec-plan-workflow`-Block |
| Modify | `.meta-config/project.yaml` | `spec-plan-workflow`-Block; `okf.allowed-types` + `Plan`/`Spec`; `PROJECT_STRUCTURE` |
| Modify | `scripts/lib/rules.py` | `collect_rule_sources`-Gate, `load_rule_gates`, 2 Call-Sites |
| Modify | `config/rules-presets.yaml` | Top-Level `rule-gates`; `lazy`-Einträge für 4 neue Rules |
| Modify | `scripts/lib/agent_sync.py` | 2 `collect_rule_sources`-Call-Sites |
| Modify | `scripts/lib/context.py` | 1 `collect_rule_sources`-Call-Site |
| Modify | `scripts/lib/sync_pipeline.py` | 1 `collect_rule_sources`-Call-Site; Scaffold-Call-Site nach `sync_knowledge_engine` |
| Modify | `config/role-defaults.yaml` | `concept-driven-dev`-Stages |
| Modify | `scripts/lib/knowledge.py` | Concept-Types; `.gitkeep`-Subdirs; `okf.auto-*`-Schreib-/Update-Wirkung; KE-Skip bei `external-system-override` |
| Modify | `knowledge/schema.md` | Concept-Type `Spec` + `Plan`-Bestätigung |
| Create | `scripts/lib/consistency/spec_plan.py` | Ledger-/Section-Parser + `check_spec_plan_workflow` |
| Create | `scripts/lib/spec_plan_validate.py` | `--validate-spec-plan`-Handler |
| Create | `scripts/lib/spec_plan_scaffold.py` | Sync-Scaffolding der Zielpfade + Index-Routing-/file-index-Fallback (R1/R2b) |
| Modify | `scripts/sync.py` | Flag-Registrierung + Dispatch |
| Create | `rules/1-generic/spec-plan-workflow.md` | Master-Rule |
| Create | `rules/1-generic/brainstorming-gate.md` | Klassifikation/Gate |
| Create | `rules/1-generic/writing-plans.md` | Plan-Qualitätsnorm |
| Create | `rules/1-generic/plan-ledger.md` | Execution/Ledger/Archiv |
| Modify | `agents/1-generic/explorer.md` | Spike-Modus (F10) |
| Modify | `agents/1-generic/ideation.md` | S/M/L/XL↔Klassen-Mapping + F7 + Gate |
| Modify | `agents/1-generic/concept-architect.md` | Design-Doc als Spec-Input + Trace-Anker |
| Modify | `agents/1-generic/concept-specifier.md` | Spec-Template §7.1 + Approval-Marker |
| Modify | `agents/1-generic/concept-reviewer.md` | Review gegen Pflichtsektionen/No-Placeholder |
| Modify | `agents/1-generic/planner.md` | Plan-Template §7.2 + `pipeline_stages` |
| Modify | `agents/1-generic/orchestrator.md` | Phasen-Dispatch/Gate/Fresh-Subagent/Recovery + `{{#if SPEC_PLAN_WORKFLOW_ENABLED}}`-Block |
| Modify | `agents/1-generic/documenter.md` | Archiv + Fallback-Index |
| Modify | `agents/1-generic/knowledge-ingestor.md` | Spec-Index-Route + KE-Archiv |
| Modify | `agents/2-platform/homeassistant-documenter.md` | `version` + `based-on` (Governance-Bump, Task 19) |
| Modify | `docs/api/cli-reference.md` | `--validate-spec-plan` dokumentieren |
| Modify | `docs/guides/ci/github-actions-sync-check.yml` | `--validate-spec-plan`-Step (F12) |
| Modify | `tests/scenarios/registry.md` | Katalogzeile `50-spec-plan-workflow` |
| Create | `tests/scenarios/configs/50-spec-plan-workflow.project.yaml` | Szenario-Config |
| Create | `tests/scenarios/asserts/50-spec-plan-workflow.sh` | Assertions (a)–(e) |
| Create | `tests/test_spec_plan_resolve_enabled.py` | Master-Switch-Präzedenz/Absenz |
| Create | `tests/test_spec_plan_enabled_render_paths.py` | `spec-plan-enabled` in Render-Pfaden |
| Create | `tests/test_spec_plan_config_schema.py` | DoD-Keys + Block/Schema |
| Create | `tests/test_rules_activation_gate.py` | Gate + neue Rules |
| Create | `tests/test_plan_ledger.py` | Ledger-Parsing + Checkpoint-Recovery |
| Create | `tests/test_spec_plan_consistency.py` | `check_spec_plan_workflow`-Checks |
| Create | `tests/test_spec_plan_migration.py` | Legacy gelesen, kein Auto-Move |
| Create | `tests/test_spec_plan_validate_cli.py` | `--validate-spec-plan` CLI/No-op |
| Create | `tests/test_spec_plan_conditional_flag.py` | Conditional-Registrierung + Template-Nutzung (R3) |
| Create | `tests/test_spec_plan_scaffold.py` | Sync-Scaffolding der Zielpfade (R1) |
| Create | `tests/test_spec_plan_override_fallback.py` | Override-Skip + file-index-Fallback (R2b) |
| Modify | `tests/test_config_null_blocks.py` | `spec-plan-workflow` in `_MAPPING_BLOCKS` |
| Modify | `tests/test_pipelines.py` | neue Stages + `dod_flag` |
| Modify | `tests/test_orchestration_contract.py` | Phasen-Reihenfolge, Gate-Zyklus- und `>2 Tasks`-Graph-Tests |
| Modify | `tests/test_knowledge_engine.py` | Concept-Types + `auto-index`/`auto-log` |
| Modify | `tests/test_knowledge_sync_integration.py` | Scaffolder-Ordner |
| Modify | `tests/test_conventions_platform_cascade.py` | Rollen-Bumps ohne Drift |
| Modify | `tests/test_se_role_boundary.py` | SE-Abgrenzung intakt |
| Modify | `tests/test_frontmatter_parity.py` | Rollen-Frontmatter-Parität |
| Modify | `tests/test_agents_frontmatter.py` | Frontmatter/Bumps + Archiv-Doku |
| Modify | `tests/test_barrier_runtime.py` | `FanoutPlan`-Nutzung |

**Reine Verifikationsläufe (kein Edit):** `tests/test_embed_rules_channel.py` und `tests/test_dod_platform_cascade.py` werden in Step-4-Kommandos ausgeführt, aber **nicht** geändert — sie stehen deshalb nicht als `Modify` in der Map.

---

## Phase A — Master-Switch-Foundation

### Task 1: Master-Switch-Resolver `resolve_spec_plan_enabled` + Injektion in `resolve_dod()`

**Files:**
- Modify: `scripts/lib/dod.py` (neue Funktion nach `resolve_dod_preset_name`, Injektion vor `return resolved` in `resolve_dod` bei `:100`)
- Create: `tests/test_spec_plan_resolve_enabled.py`

**Interfaces:**
- Consumes: `load_dod_presets` (`scripts/lib/dod.py:14`), `resolve_dod_preset_name` (`scripts/lib/dod.py:29`), `_load_yaml_or_json` via Preset-Loader.
- Produces: `resolve_spec_plan_enabled(config: dict, agent_meta_root: Path, *, dod: dict | None = None) -> bool`; synthetischer Key `spec-plan-enabled` in jedem von `resolve_dod()` zurückgegebenen Dict.

- [ ] **Step 1: Write the failing test**

  Create `tests/test_spec_plan_resolve_enabled.py`:

  ```python
  """Tests for resolve_spec_plan_enabled and its injection into resolve_dod
  (spec 5.4, F8). Precedence: explicit bool > dod.spec-plan-required > false.
  Absence semantics matter: a missing key falls back to the preset, never to
  a materialized nested default."""
  import sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(REPO_ROOT / "scripts"))

  from lib.dod import resolve_dod, resolve_spec_plan_enabled  # noqa: E402


  def _meta_root(tmp_path: Path, required: bool) -> Path:
      root = tmp_path / "agent-meta"
      config_dir = root / "config"
      config_dir.mkdir(parents=True)
      (config_dir / "dod-presets.yaml").write_text(
          "presets:\n"
          "  full:\n"
          f"    spec-plan-required: {str(required).lower()}\n"
          "    spec-plan-traceability: false\n"
          '    se-required: "false"\n',
          encoding="utf-8",
      )
      return root


  def test_explicit_enabled_true_wins(tmp_path):
      root = _meta_root(tmp_path, required=False)
      config = {"platforms": [], "spec-plan-workflow": {"enabled": True}}
      assert resolve_spec_plan_enabled(config, root) is True


  def test_explicit_enabled_false_wins_over_preset_true(tmp_path):
      root = _meta_root(tmp_path, required=True)
      config = {"platforms": [], "spec-plan-workflow": {"enabled": False}}
      assert resolve_spec_plan_enabled(config, root) is False


  def test_absent_key_falls_back_to_preset_true(tmp_path):
      root = _meta_root(tmp_path, required=True)
      assert resolve_spec_plan_enabled({"platforms": []}, root) is True


  def test_absent_key_and_preset_false_is_false(tmp_path):
      root = _meta_root(tmp_path, required=False)
      assert resolve_spec_plan_enabled({"platforms": []}, root) is False


  def test_dod_override_beats_preset(tmp_path):
      root = _meta_root(tmp_path, required=False)
      config = {"platforms": [], "dod": {"spec-plan-required": True}}
      assert resolve_spec_plan_enabled(config, root) is True


  def test_injected_dod_is_used_without_second_resolution(tmp_path):
      root = _meta_root(tmp_path, required=False)
      config = {"platforms": [], "spec-plan-workflow": {"enabled": True}}
      assert resolve_spec_plan_enabled(config, root, dod={"spec-plan-required": False}) is True


  def test_resolve_dod_injects_synthetic_key(tmp_path):
      root = _meta_root(tmp_path, required=True)
      resolved = resolve_dod({"platforms": []}, root)
      assert resolved["spec-plan-enabled"] is True
  ```

- [ ] **Step 2: Run the tests, confirm they fail**

  Run: `pytest tests/test_spec_plan_resolve_enabled.py -v`
  Expected: FAIL — `ImportError: cannot import name 'resolve_spec_plan_enabled'`.

- [ ] **Step 3: Implement the resolver and the injection**

  In `scripts/lib/dod.py`, after `resolve_dod_preset_name`:

  ```python
  def resolve_spec_plan_enabled(config: dict, agent_meta_root: Path,
                                *, dod: dict | None = None) -> bool:
      """Single source of truth for the native spec/plan workflow master switch.

      Precedence: explicit `spec-plan-workflow.enabled` bool > resolved DoD
      `spec-plan-required` > False. Pass `dod=` when the caller already holds
      the resolved DoD dict -- this avoids a second resolve_dod() call and the
      resolve_dod <-> resolve_spec_plan_enabled recursion.
      """
      block = config.get("spec-plan-workflow")
      if isinstance(block, dict) and "enabled" in block:
          return bool(block["enabled"])
      resolved_dod = dod if dod is not None else resolve_dod(config, agent_meta_root)
      return bool(resolved_dod.get("spec-plan-required", False))
  ```

  At the end of `resolve_dod()` (before `return resolved`), add:

  ```python
      # Synthetic render key -- MUST pass dod=resolved to avoid recursion
      # (resolve_spec_plan_enabled would otherwise call resolve_dod again).
      resolved["spec-plan-enabled"] = resolve_spec_plan_enabled(
          config, agent_meta_root, dod=resolved,
      )
      return resolved
  ```

- [ ] **Step 4: Run the tests again, confirm they pass**

  Run: `pytest tests/test_spec_plan_resolve_enabled.py -v`
  Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

  ```bash
  git add scripts/lib/dod.py tests/test_spec_plan_resolve_enabled.py
  git commit -m "feat: add resolve_spec_plan_enabled master switch"
  ```

---

### Task 2: `SPEC_PLAN_WORKFLOW_ENABLED` + Render-Pfad-Passthrough in `_build_dod_variables()`

**Files:**
- Modify: `scripts/lib/config.py:1627-1672`
- Create: `tests/test_spec_plan_enabled_render_paths.py`

**Interfaces:**
- Consumes: `resolve_spec_plan_enabled` (Task 1), `resolve_dod` (`config.py`-Import), `build_variables` (`scripts/lib/config.py:1905`), `inject_pipeline_blocks` (`scripts/lib/pipelines.py:554`).
- Produces: `variables["SPEC_PLAN_WORKFLOW_ENABLED"]` (`"true"`/`"false"`), `variables["SPEC_PLAN_SPECS_DIR"]`, `variables["SPEC_PLAN_PLANS_DIR"]`; das bereits aufgelöste `dod_resolved` wird unverändert an `_build_pipeline_variables` durchgereicht (keine zweite `resolve_dod`-Auflösung).

- [ ] **Step 1: Write the failing test**

  Create `tests/test_spec_plan_enabled_render_paths.py`:

  ```python
  """B3-Rest: SPEC_PLAN_WORKFLOW_ENABLED reaches the real render paths, and
  resolve_dod() is resolved exactly once per build_variables() call. The
  synthetic spec-plan-enabled key gates the conditional pipeline stage."""
  import sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(REPO_ROOT / "scripts"))

  import lib.config as config_mod  # noqa: E402
  import lib.dod as dod_mod  # noqa: E402
  from lib.config import build_variables  # noqa: E402
  from lib.dod import resolve_dod  # noqa: E402
  from lib.pipelines import inject_pipeline_blocks  # noqa: E402


  def _config(enabled):
      return {
          "platforms": [],
          "dod-preset": "full",
          "spec-plan-workflow": {"enabled": enabled},
      }


  _PIPELINES = {
      "concept-driven-dev": {
          "enabled": True,
          "stages": [
              {
                  "id": "specify",
                  "agent": "concept-specifier",
                  "task": "Spec schreiben",
                  "mode": "conditional",
                  "condition": {"dod_flag": "spec-plan-enabled"},
              }
          ],
      }
  }


  def test_variable_true_when_enabled():
      variables, _ = build_variables(_config(True), REPO_ROOT)
      assert variables["SPEC_PLAN_WORKFLOW_ENABLED"] == "true"


  def test_variable_false_when_disabled():
      variables, _ = build_variables(_config(False), REPO_ROOT)
      assert variables["SPEC_PLAN_WORKFLOW_ENABLED"] == "false"


  def test_default_paths_present():
      variables, _ = build_variables(_config(True), REPO_ROOT)
      assert variables["SPEC_PLAN_SPECS_DIR"] == "docs/specs"
      assert variables["SPEC_PLAN_PLANS_DIR"] == "docs/plans"


  def test_resolve_dod_called_once(monkeypatch):
      calls = {"config": 0, "dod": 0}
      real_config = config_mod.resolve_dod
      real_dod = dod_mod.resolve_dod

      def _spy_config(config, agent_meta_root):
          calls["config"] += 1
          return real_config(config, agent_meta_root)

      def _spy_dod(config, agent_meta_root):
          calls["dod"] += 1
          return real_dod(config, agent_meta_root)

      monkeypatch.setattr(config_mod, "resolve_dod", _spy_config)
      monkeypatch.setattr(dod_mod, "resolve_dod", _spy_dod)
      build_variables(_config(True), REPO_ROOT)
      assert calls["config"] == 1
      # A second, implicit module-level resolution inside resolve_spec_plan_enabled
      # would show up here — 0 proves the dod= passthrough (Task 1).
      assert calls["dod"] == 0


  def test_pipeline_gate_stage_hidden_when_disabled():
      rendered = inject_pipeline_blocks(
          "{{PIPELINE_DETAIL_BLOCKS}}", _PIPELINES, "Claude",
          resolve_dod(_config(False), REPO_ROOT),
      )
      assert "concept-specifier" not in rendered


  def test_pipeline_gate_stage_present_when_enabled():
      rendered = inject_pipeline_blocks(
          "{{PIPELINE_DETAIL_BLOCKS}}", _PIPELINES, "Claude",
          resolve_dod(_config(True), REPO_ROOT),
      )
      assert "concept-specifier" in rendered
  ```

- [ ] **Step 2: Run the tests, confirm they fail**

  Run: `pytest tests/test_spec_plan_enabled_render_paths.py -v`
  Expected: FAIL — `KeyError: 'SPEC_PLAN_WORKFLOW_ENABLED'` (Variable wird noch nicht gesetzt).

- [ ] **Step 3: Implement the variables in `_build_dod_variables()`**

  In `scripts/lib/config.py`, innerhalb `_build_dod_variables()` nach `dod_resolved = resolve_dod(config, agent_meta_root)` ergänzen:

  ```python
      sp_block = config.get("spec-plan-workflow") or {}
      sp_paths = sp_block.get("paths") or {}
      variables["SPEC_PLAN_SPECS_DIR"] = sp_paths.get("specs", "docs/specs")
      variables["SPEC_PLAN_PLANS_DIR"] = sp_paths.get("plans", "docs/plans")
      variables["SPEC_PLAN_WORKFLOW_ENABLED"] = (
          "true" if resolve_spec_plan_enabled(
              config, agent_meta_root, dod=dod_resolved,
          ) else "false"
      )
  ```

  Import am Modulkopf von `config.py` um `resolve_spec_plan_enabled` aus `.dod` ergänzen (dort wird `resolve_dod` bereits importiert). Die Signatur von `_build_dod_variables` bleibt unverändert; `return dod_resolved` bleibt bestehen, damit `_build_pipeline_variables` das bereits aufgelöste Dict erhält.

- [ ] **Step 4: Run the tests again, confirm they pass**

  Run: `pytest tests/test_spec_plan_enabled_render_paths.py -v`
  Expected: PASS (6 tests). Zusätzlich: `pytest tests/test_dod_platform_cascade.py tests/test_progress_file.py -q` bleibt grün.

- [ ] **Step 5: Commit**

  ```bash
  git add scripts/lib/config.py tests/test_spec_plan_enabled_render_paths.py
  git commit -m "feat: expose SPEC_PLAN_WORKFLOW_ENABLED to render paths"
  ```

---

### Task 2b: `SPEC_PLAN_WORKFLOW_ENABLED` als strippbares Conditional registrieren + in `orchestrator.md` nutzen

**Files:**
- Modify: `scripts/lib/variables.py:231-237` (Conditional-Liste in `strip_inactive_conditional_blocks`)
- Modify: `scripts/lib/consistency/placeholders.py:11-116` (`_BUILTIN_VARS`)
- Modify: `scripts/lib/standalone.py:119` (`_CONDITIONAL_FALSE_FLAGS`)
- Modify: `agents/1-generic/orchestrator.md`
- Create: `tests/test_spec_plan_conditional_flag.py`

**Interfaces:**
- Consumes: `SPEC_PLAN_WORKFLOW_ENABLED`/`SPEC_PLAN_SPECS_DIR`/`SPEC_PLAN_PLANS_DIR` (Task 2); `strip_inactive_conditional_blocks` (`scripts/lib/variables.py:217`); `_BUILTIN_VARS` (Platzhalter-Check); Standalone-Rendering.
- Produces: `SPEC_PLAN_WORKFLOW_ENABLED` wird von `strip_inactive_conditional_blocks` erkannt (`"false"` ⇒ Block entfernt); in `_BUILTIN_VARS` registriert; Standalone-Fallback `"false"`; `orchestrator.md` enthält einen `{{#if SPEC_PLAN_WORKFLOW_ENABLED}}…{{/if}}`-Block; `SPEC_PLAN_SPECS_DIR`/`SPEC_PLAN_PLANS_DIR` sind Builtins und werden in `rules/1-generic/spec-plan-workflow.md` (Task 7) verwendet.

- [ ] **Step 1: Write the failing test**

  Create `tests/test_spec_plan_conditional_flag.py`:

  ```python
  """SPEC_PLAN_WORKFLOW_ENABLED is a strippable conditional, a known builtin
  placeholder and a false-flag in standalone rendering (R3)."""
  import sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(REPO_ROOT / "scripts"))

  from lib.variables import strip_inactive_conditional_blocks  # noqa: E402
  from lib.consistency.placeholders import _BUILTIN_VARS  # noqa: E402
  from lib.standalone import _CONDITIONAL_FALSE_FLAGS  # noqa: E402


  def test_conditional_true_keeps_block():
      text = "a{{#if SPEC_PLAN_WORKFLOW_ENABLED}}X{{/if}}b"
      assert strip_inactive_conditional_blocks(
          text, {"SPEC_PLAN_WORKFLOW_ENABLED": "true"},
      ) == "aXb"


  def test_conditional_false_strips_block():
      text = "a{{#if SPEC_PLAN_WORKFLOW_ENABLED}}X{{/if}}b"
      assert strip_inactive_conditional_blocks(
          text, {"SPEC_PLAN_WORKFLOW_ENABLED": "false"},
      ) == "ab"


  def test_registered_as_builtin_and_standalone_flag():
      assert "SPEC_PLAN_WORKFLOW_ENABLED" in _BUILTIN_VARS
      assert "SPEC_PLAN_SPECS_DIR" in _BUILTIN_VARS
      assert "SPEC_PLAN_PLANS_DIR" in _BUILTIN_VARS
      assert _CONDITIONAL_FALSE_FLAGS["SPEC_PLAN_WORKFLOW_ENABLED"] == "false"


  def test_orchestrator_uses_the_conditional():
      text = (REPO_ROOT / "agents" / "1-generic" / "orchestrator.md").read_text(encoding="utf-8")
      assert "{{#if SPEC_PLAN_WORKFLOW_ENABLED}}" in text
      assert "{{/if}}" in text
  ```

- [ ] **Step 2: Run the tests, confirm they fail**

  Run: `pytest tests/test_spec_plan_conditional_flag.py -v`
  Expected: FAIL — Flag wird nicht als Conditional erkannt, Builtin/Fallback fehlen, `orchestrator.md` nutzt das Conditional noch nicht.

- [ ] **Step 3: Register the flag and use the conditional**

  In `scripts/lib/variables.py` die `conditional_vars.update({k for k in variables if k in (...)})`-Menge (Zeilen `231-237`) um `"SPEC_PLAN_WORKFLOW_ENABLED"` ergänzen.

  In `scripts/lib/consistency/placeholders.py` `_BUILTIN_VARS` (Zeilen `11-116`) additiv um `"SPEC_PLAN_WORKFLOW_ENABLED"`, `"SPEC_PLAN_SPECS_DIR"`, `"SPEC_PLAN_PLANS_DIR"` ergänzen.

  In `scripts/lib/standalone.py` `_CONDITIONAL_FALSE_FLAGS` (Zeile `119`) um `"SPEC_PLAN_WORKFLOW_ENABLED": "false",` ergänzen.

  In `agents/1-generic/orchestrator.md` im `<workflow>`-Abschnitt einen Conditional-Block ergänzen (der Phasen-Inhalt darin wird von Task 17 gefüllt):

  ```
  {{#if SPEC_PLAN_WORKFLOW_ENABLED}}
  > **Spec/Plan-Workflow aktiv** — Phasen `classify → spec → approve → plan → execute` (Details unten).
  {{/if}}
  ```

  Frontmatter-`version` bumpen (Minor, vgl. Global Constraints).

- [ ] **Step 4: Run the tests again, confirm they pass**

  Run: `pytest tests/test_spec_plan_conditional_flag.py tests/test_spec_plan_enabled_render_paths.py -q`
  Expected: PASS. Zusätzlich: `python3 scripts/sync.py --dry-run` läuft ohne Fehler (das Conditional wird als aktives Flag gerendert).

- [ ] **Step 5: Commit**

  ```bash
  git add scripts/lib/variables.py scripts/lib/consistency/placeholders.py scripts/lib/standalone.py agents/1-generic/orchestrator.md tests/test_spec_plan_conditional_flag.py
  git commit -m "feat: register SPEC_PLAN_WORKFLOW_ENABLED conditional flag"
  ```

---

### Task 3: DoD-Presets + `dod`-Schema-Keys + `concept-driven`-Enum

**Files:**
- Modify: `config/dod-presets.yaml`
- Modify: `config/project-config.schema.json:575-635`
- Create: `tests/test_spec_plan_config_schema.py`

**Interfaces:**
- Consumes: `resolve_dod` (Task 1) liest die neuen Keys, weil sie im `full`-Preset stehen.
- Produces: Preset-Keys `spec-plan-required`/`spec-plan-traceability`; Schema-Properties gleicher Namen im `dod`-Block; `dod-preset`-Enum enthält `concept-driven`.

- [ ] **Step 1: Write the failing test**

  Create `tests/test_spec_plan_config_schema.py`:

  ```python
  """Schema tests for the spec/plan workflow config surface (F8). The
  systems-engineering declaration is deliberately NOT covered -- it is the
  out-of-scope follow-up F1."""
  import copy
  import json
  import sys
  from pathlib import Path

  import pytest

  REPO_ROOT = Path(__file__).resolve().parent.parent
  SCHEMA_PATH = REPO_ROOT / "config" / "project-config.schema.json"
  sys.path.insert(0, str(REPO_ROOT / "scripts"))


  def _schema():
      return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


  def _base_config(**extra):
      cfg = {"platforms": []}
      cfg.update(extra)
      return cfg


  def test_dod_preset_enum_includes_concept_driven():
      schema = _schema()
      assert "concept-driven" in schema["properties"]["dod-preset"]["enum"]


  def test_dod_properties_accept_spec_plan_flags():
      jsonschema = pytest.importorskip("jsonschema")
      jsonschema.validate(
          _base_config(dod={"spec-plan-required": True, "spec-plan-traceability": False}),
          _schema(),
      )


  def test_dod_rejects_unknown_spec_plan_key():
      jsonschema = pytest.importorskip("jsonschema")
      with pytest.raises(jsonschema.ValidationError):
          jsonschema.validate(_base_config(dod={"spec-plan-bogus": True}), _schema())


  def test_full_preset_defines_both_keys():
      from lib.dod import load_dod_presets
      presets = load_dod_presets(REPO_ROOT)
      assert "spec-plan-required" in presets["full"]
      assert "spec-plan-traceability" in presets["full"]


  def test_concept_driven_preset_requires_spec_plan():
      from lib.dod import load_dod_presets
      presets = load_dod_presets(REPO_ROOT)
      assert presets["concept-driven"]["spec-plan-required"] is True
      assert presets["concept-driven"]["spec-plan-traceability"] is False
  ```

- [ ] **Step 2: Run the tests, confirm they fail**

  Run: `pytest tests/test_spec_plan_config_schema.py -v`
  Expected: FAIL — `concept-driven` fehlt im Enum, `spec-plan-*` fehlen in `full`.

- [ ] **Step 3: Add preset keys and schema properties**

  In `config/dod-presets.yaml` je Preset die zwei Keys gemäß Spezifikation-Tabelle §5.3 ergänzen: `full`/`standard`/`rapid-prototyping`/`spec-optional` → `spec-plan-required: false`, `spec-plan-traceability: false`; `spec-driven` → `true`/`true`; `concept-driven` → `true`/`false`; `spec-certified` → `true`/`true`.

  In `config/project-config.schema.json` im `dod`-Block (`properties`, vor `se-required`) ergänzen:

  ```json
  "spec-plan-required": {
    "type": "boolean",
    "description": "Require the native spec/plan workflow for feature-level changes. Default: false (preset-coupled).",
    "default": false
  },
  "spec-plan-traceability": {
    "type": "boolean",
    "description": "Require spec<->plan<->task<->test traceability. Default: false (preset-coupled).",
    "default": false
  },
  ```

  Im `dod-preset`-Enum (`:575-582`) additiv `"concept-driven"` ergänzen.

- [ ] **Step 4: Run the tests again, confirm they pass**

  Run: `pytest tests/test_spec_plan_config_schema.py tests/test_dod_platform_cascade.py tests/test_conventions_platform_cascade.py -q`
  Expected: PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add config/dod-presets.yaml config/project-config.schema.json tests/test_spec_plan_config_schema.py
  git commit -m "feat: add spec-plan DoD flags and concept-driven preset enum"
  ```

---

## Phase B — Projekt-Config + Schema

### Task 4: `spec-plan-workflow`-Block in Projekt-Config + Schema + Null-Block-Mapping

**Files:**
- Modify: `.meta-config/project.yaml` (neuer Top-Level-Block)
- Modify: `config/project-config.schema.json` (neue Top-Level-Property `spec-plan-workflow`)
- Modify: `tests/test_config_null_blocks.py:27-66` (`_MAPPING_BLOCKS`)
- Modify: `tests/test_spec_plan_config_schema.py` (Task 3 erweitern)

**Interfaces:**
- Consumes: Schema-Konventionen analog `knowledge-engine`; `load_config` normalisiert YAML-null-Mapping-Blöcke zu `{}`.
- Produces: validierbarer `spec-plan-workflow`-Block mit `paths`/`scan`/`index`/`archive`/`external-system-override`; `spec-plan-workflow: null` wird zu `{}`.

- [ ] **Step 1: Write the failing test**

  An `tests/test_spec_plan_config_schema.py` anhängen:

  ```python
  def test_spec_plan_workflow_block_valid():
      jsonschema = pytest.importorskip("jsonschema")
      jsonschema.validate(
          _base_config(**{
              "spec-plan-workflow": {
                  "enabled": True,
                  "paths": {
                      "specs": "docs/specs",
                      "plans": "docs/plans",
                      "spikes": "docs/spikes",
                      "legacy": ["docs/superpowers/specs", "docs/superpowers/plans"],
                  },
                  "scan": {"include": ["*.md"], "changed-files-only": True},
                  "index": {"mode": "file-index", "fallback-index": "docs/INDEX.md"},
                  "archive": {
                      "mode": "ask", "agent": "documenter",
                      "trigger": "plan-complete", "target": "docs/plans/archive",
                  },
                  "external-system-override": {"enabled": False, "system": "", "note": ""},
              }
          }),
          _schema(),
      )


  def test_spec_plan_workflow_block_rejects_unknown_key():
      jsonschema = pytest.importorskip("jsonschema")
      with pytest.raises(jsonschema.ValidationError):
          jsonschema.validate(_base_config(**{"spec-plan-workflow": {"bogus": 1}}), _schema())


  def test_spec_plan_workflow_has_no_schema_default():
      block = _schema()["properties"]["spec-plan-workflow"]
      assert "default" not in block
      assert "default" not in block["properties"]["enabled"]
  ```

- [ ] **Step 2: Run the tests, confirm they fail**

  Run: `pytest tests/test_spec_plan_config_schema.py -v`
  Expected: FAIL — `spec-plan-workflow` ist noch nicht deklariert; `additionalProperties:true` akzeptiert zwar den Block, aber `bogus` würde fälschlich durchlaufen bzw. der Block selbst ist keine bekannte Property.

- [ ] **Step 3: Add config block, schema property and null-block mapping**

  In `.meta-config/project.yaml` (auf gleicher Ebene wie `knowledge-engine`) den Block aus §5.1 einfügen:

  ```yaml
  spec-plan-workflow:
    # enabled bewusst OHNE Schema-Default (Absenz-Semantik, §5.4).
    # Fehlt der Key, greift die DoD-Preset-Kopplung. Expliziter bool gewinnt.
    enabled: true
    paths:
      specs: docs/specs
      plans: docs/plans
      spikes: docs/spikes
      legacy:
      - docs/superpowers/specs
      - docs/superpowers/plans
    scan:
      include:
      - '*.md'
      changed-files-only: true
    index:
      mode: knowledge-engine
      fallback-index: docs/INDEX.md
    archive:
      mode: ask
      agent: documenter
      trigger: plan-complete
      target: docs/plans/archive
    external-system-override:
      enabled: false
      system: ''
      note: ''
  ```

  In `config/project-config.schema.json` unter `properties` die Property `spec-plan-workflow` mit exakt dem JSON-Schema aus Spezifikation §5.2 einfügen (`type: object`, verschachtelte `paths`/`scan`/`index`/`archive`/`external-system-override`, jeweils `additionalProperties: false`, Top-Level `additionalProperties: false`, **kein** `default`, `enabled` **ohne** `default`).

  In `tests/test_config_null_blocks.py` in der Liste `_MAPPING_BLOCKS` (bei `:27-66`) den Eintrag `"spec-plan-workflow"` ergänzen (nach `"release-gates"`).

- [ ] **Step 4: Run the tests again, confirm they pass**

  Run: `pytest tests/test_spec_plan_config_schema.py tests/test_config_null_blocks.py -q`
  Expected: PASS. Zusätzlich: `python3 scripts/sync.py --validate` bleibt grün.

- [ ] **Step 5: Commit**

  ```bash
  git add .meta-config/project.yaml config/project-config.schema.json tests/test_config_null_blocks.py tests/test_spec_plan_config_schema.py
  git commit -m "feat: declare spec-plan-workflow project config block"
  ```

---

## Phase C — PROJECT_STRUCTURE (F9) + Sync-Scaffolding (R1)

### Task 5: `variables.PROJECT_STRUCTURE` um `docs/specs`/`docs/plans`/`docs/spikes` ergänzen

**Files:**
- Modify: `.meta-config/project.yaml:176-189`
- Modify: `tests/test_spec_plan_config_schema.py` (Assertion ergänzen)

**Interfaces:**
- Consumes: bestehenden `PROJECT_STRUCTURE`-Block.
- Produces: `PROJECT_STRUCTURE` listet `docs/specs/`, `docs/plans/`, `docs/spikes/`.

- [ ] **Step 1: Write the failing test**

  An `tests/test_spec_plan_config_schema.py` anhängen:

  ```python
  def test_project_structure_lists_spec_plan_paths():
      from lib.io import _load_yaml_or_json
      data, _ = _load_yaml_or_json(REPO_ROOT / ".meta-config" / "project.yaml")
      structure = data["variables"]["PROJECT_STRUCTURE"]
      assert "docs/specs/" in structure
      assert "docs/plans/" in structure
      assert "docs/spikes/" in structure
  ```

- [ ] **Step 2: Run the test, confirm it fails**

  Run: `pytest tests/test_spec_plan_config_schema.py::test_project_structure_lists_spec_plan_paths -v`
  Expected: FAIL — keiner der drei Pfade ist in `PROJECT_STRUCTURE` enthalten.

- [ ] **Step 3: Extend `PROJECT_STRUCTURE`**

  In `.meta-config/project.yaml` im `PROJECT_STRUCTURE`-Literal nach `docs/ui/` ergänzen:

  ```yaml
    docs/specs/       # Feature-Specs (Spec/Plan-Workflow, §5.1)
    docs/plans/       # Feature-Pläne + archive/ (docs/plans/README.md)
    docs/spikes/      # Wegwerf-Untersuchungen (explorer-Spike-Modus, F10)
  ```

- [ ] **Step 4: Run the test again, confirm it passes**

  Run: `pytest tests/test_spec_plan_config_schema.py -q`
  Expected: PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add .meta-config/project.yaml tests/test_spec_plan_config_schema.py
  git commit -m "docs: list spec/plan/spike paths in PROJECT_STRUCTURE"
  ```

---

### Task 5b: Sync-Scaffolding für `docs/specs`/`docs/plans`/`docs/spikes` + `file-index`-Fallback (R1)

**Files:**
- Create: `scripts/lib/spec_plan_scaffold.py`
- Modify: `scripts/lib/sync_pipeline.py:785-795` (Call-Site in `_sync_stage_knowledge_and_isolation`)
- Create: `tests/test_spec_plan_scaffold.py`

**Interfaces:**
- Consumes: `resolve_spec_plan_enabled` (Task 1); `paths.specs`/`paths.plans`/`paths.spikes` und `index.mode`/`index.fallback-index`/`external-system-override` (Task 4); `safe_path`/`write_checked` (`scripts/lib/io.py:582/387`); `SyncLog`.
- Produces: `scaffold_spec_plan_dirs(agent_meta_root: Path, project_root: Path, config: dict, log: SyncLog, dry_run: bool) -> None`; `resolve_index_mode(config: dict) -> tuple[str, str]` (effektiver Modus, Fallback-Pfad). Bei `effective_enabled=true` werden die Zielpfade inkl. `.gitkeep` angelegt; ist der effektive Index-Modus `file-index` (explizit, `external-system-override.enabled=true` oder `knowledge-engine.enabled=false`), wird zusätzlich der Fallback-Index (`index.fallback-index`, Default `docs/INDEX.md`) als Skelett geschrieben.

- [ ] **Step 1: Write the failing test**

  Create `tests/test_spec_plan_scaffold.py`:

  ```python
  """Sync scaffolds the neutral spec/plan/spike paths when the master switch is
  on, and nothing when it is off; the index router picks the file-index
  fallback for override/KE-off (R1/D8)."""
  import sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(REPO_ROOT / "scripts"))

  from lib.log import SyncLog  # noqa: E402
  from lib.spec_plan_scaffold import resolve_index_mode, scaffold_spec_plan_dirs  # noqa: E402


  def _config(enabled, knowledge_engine=True, **sp_extra):
      block = {"enabled": enabled, "paths": {
          "specs": "docs/specs", "plans": "docs/plans", "spikes": "docs/spikes"}}
      block.update(sp_extra)
      return {
          "spec-plan-workflow": block,
          "knowledge-engine": {"enabled": knowledge_engine},
      }


  def test_enabled_scaffolds_all_paths(tmp_path):
      log = SyncLog()
      scaffold_spec_plan_dirs(REPO_ROOT, tmp_path, _config(True), log, dry_run=False)
      for sub in ("docs/specs", "docs/plans", "docs/spikes"):
          assert (tmp_path / sub / ".gitkeep").is_file(), f"missing {sub}/.gitkeep"


  def test_disabled_scaffolds_nothing(tmp_path):
      log = SyncLog()
      scaffold_spec_plan_dirs(REPO_ROOT, tmp_path, _config(False), log, dry_run=False)
      assert not (tmp_path / "docs" / "specs").exists()


  def test_dry_run_scaffolds_nothing(tmp_path):
      log = SyncLog()
      scaffold_spec_plan_dirs(REPO_ROOT, tmp_path, _config(True), log, dry_run=True)
      assert not (tmp_path / "docs" / "specs").exists()


  def test_index_mode_defaults_to_knowledge_engine():
      cfg = _config(True, index={"mode": "knowledge-engine", "fallback-index": "docs/INDEX.md"})
      assert resolve_index_mode(cfg) == ("knowledge-engine", "docs/INDEX.md")


  def test_override_forces_file_index():
      cfg = _config(True, index={"mode": "knowledge-engine", "fallback-index": "docs/INDEX.md"},
                    **{"external-system-override": {"enabled": True}})
      assert resolve_index_mode(cfg) == ("file-index", "docs/INDEX.md")


  def test_ke_off_forces_file_index():
      cfg = _config(True, knowledge_engine=False,
                    index={"mode": "knowledge-engine", "fallback-index": "docs/INDEX.md"})
      assert resolve_index_mode(cfg) == ("file-index", "docs/INDEX.md")


  def test_file_index_fallback_written(tmp_path):
      log = SyncLog()
      cfg = _config(True, knowledge_engine=False,
                    index={"mode": "file-index", "fallback-index": "docs/INDEX.md"})
      scaffold_spec_plan_dirs(REPO_ROOT, tmp_path, cfg, log, dry_run=False)
      assert (tmp_path / "docs" / "INDEX.md").is_file()
  ```

- [ ] **Step 2: Run the tests, confirm they fail**

  Run: `pytest tests/test_spec_plan_scaffold.py -v`
  Expected: FAIL — `ModuleNotFoundError: lib.spec_plan_scaffold`.

- [ ] **Step 3: Implement the scaffolder + index router and wire the call-site**

  Create `scripts/lib/spec_plan_scaffold.py`: Docstring (R1, analog `sync_knowledge_engine`), stdlib-only, `from __future__ import annotations`, `from pathlib import Path`, Imports `from .io import safe_path, write_checked`, `from .log import SyncLog`, `from .dod import resolve_spec_plan_enabled`.

  ```python
  DEFAULT_SPECS_DIR = "docs/specs"
  DEFAULT_PLANS_DIR = "docs/plans"
  DEFAULT_SPIKES_DIR = "docs/spikes"
  DEFAULT_FALLBACK_INDEX = "docs/INDEX.md"
  _FILE_INDEX_SKELETON = "# INDEX\n\n> File-based index fallback (spec-plan-workflow, D8).\n"


  def resolve_index_mode(config: dict) -> tuple[str, str]:
      """Effective index mode and fallback path (D8).

      `external-system-override.enabled` or a disabled knowledge engine forces
      the `file-index` fallback, regardless of the declared `index.mode`.
      """
      sp = config.get("spec-plan-workflow") or {}
      index = sp.get("index") or {}
      override = sp.get("external-system-override") or {}
      ke = config.get("knowledge-engine") or {}
      mode = index.get("mode", "knowledge-engine")
      fallback = index.get("fallback-index", DEFAULT_FALLBACK_INDEX)
      if override.get("enabled", False) or not ke.get("enabled", False):
          mode = "file-index"
      return mode, fallback


  def scaffold_spec_plan_dirs(agent_meta_root: Path, project_root: Path,
                              config: dict, log: SyncLog, dry_run: bool) -> None:
      if not resolve_spec_plan_enabled(config, agent_meta_root):
          log.skip("spec-plan-workflow", "disabled")
          return
      block = config.get("spec-plan-workflow") or {}
      paths = block.get("paths") or {}
      for key, default in (("specs", DEFAULT_SPECS_DIR), ("plans", DEFAULT_PLANS_DIR),
                           ("spikes", DEFAULT_SPIKES_DIR)):
          rel = paths.get(key, default)
          target = safe_path(project_root, rel)
          if not dry_run:
              target.mkdir(parents=True, exist_ok=True)
          if write_checked(target / ".gitkeep", "", log, f"{rel}/.gitkeep", dry_run=dry_run):
              log.action("CREATE", f"{rel}/.gitkeep", "spec-plan scaffolding")
      mode, fallback = resolve_index_mode(config)
      if mode == "file-index":
          index_path = safe_path(project_root, fallback)
          if not dry_run:
              index_path.parent.mkdir(parents=True, exist_ok=True)
          if write_checked(index_path, _FILE_INDEX_SKELETON, log, fallback, dry_run=dry_run):
              log.action("CREATE", fallback, "spec-plan file-index fallback")
  ```

  In `scripts/lib/sync_pipeline.py` `_sync_stage_knowledge_and_isolation` nach dem `sync_knowledge_engine`-Aufruf (`:792`) ergänzen:

  ```python
      try:
          scaffold_spec_plan_dirs(agent_meta_root, project_root, config, log, args.dry_run)
      except SyncError as exc:
          print(f"\n  !!  Spec/plan scaffolding aborted: {exc}", file=sys.stderr)
          sys.exit(1)
  ```

  Import `from lib.spec_plan_scaffold import scaffold_spec_plan_dirs` ergänzen.

- [ ] **Step 4: Run the tests again, confirm they pass**

  Run: `pytest tests/test_spec_plan_scaffold.py -q && python3 scripts/sync.py --dry-run`
  Expected: PASS; der Scaffold ist im dry-run sichtbar, schreibt aber nichts.

- [ ] **Step 5: Commit**

  ```bash
  git add scripts/lib/spec_plan_scaffold.py scripts/lib/sync_pipeline.py tests/test_spec_plan_scaffold.py
  git commit -m "feat: scaffold spec/plan/spike paths and file-index fallback"
  ```

---

## Phase D — Rule-Gate (F3) + Rules

### Task 6: Intrinsisches fail-closed Gate in `collect_rule_sources` + `rule-gates`-Sektion + 6 Call-Sites

**Files:**
- Modify: `scripts/lib/rules.py:50-159` (neues `load_rule_gates`, erweiterte Signatur, Gate-Logik)
- Modify: `scripts/lib/rules.py:282`, `scripts/lib/rules.py:370`
- Modify: `scripts/lib/agent_sync.py:129`, `scripts/lib/agent_sync.py:190`
- Modify: `scripts/lib/context.py:1133`
- Modify: `scripts/lib/sync_pipeline.py:555`
- Modify: `config/rules-presets.yaml` (Top-Level-Sektion `rule-gates`)
- Create: `tests/test_rules_activation_gate.py`

**Interfaces:**
- Consumes: `_load_yaml_or_json` (bereits in `rules.py` importiert), `resolve_spec_plan_enabled` (Task 1).
- Produces: `load_rule_gates(agent_meta_root: Path) -> dict`; `collect_rule_sources(agent_meta_root: Path, platforms: list[str], *, config: dict | None) -> list[tuple[Path, str]]` (Keyword-only, verpflichtend; `config=None` = fail-closed).

- [ ] **Step 1: Write the failing test**

  Create `tests/test_rules_activation_gate.py`:

  ```python
  """Gate at the single choke-point collect_rule_sources: gated rules leave
  EVERY preset when the master switch is off, and None config is fail-closed."""
  import sys
  from pathlib import Path

  import pytest

  REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(REPO_ROOT / "scripts"))

  from lib.rules import collect_rule_sources  # noqa: E402


  def _meta_root(tmp_path: Path) -> Path:
      root = tmp_path / "agent-meta"
      rules_dir = root / "rules" / "1-generic"
      rules_dir.mkdir(parents=True)
      (rules_dir / "spec-plan-workflow.md").write_text("# spec-plan-workflow\n", encoding="utf-8")
      (rules_dir / "branch-guard.md").write_text("# branch-guard\n", encoding="utf-8")
      cfg_dir = root / "config"
      cfg_dir.mkdir(parents=True)
      (cfg_dir / "rules-presets.yaml").write_text(
          "presets:\n"
          "  default: {}\n"
          "  minimal: {}\n"
          "  silent: {}\n"
          "  lazy: {}\n"
          "rule-gates:\n"
          "  spec-plan-workflow:\n"
          "    requires: spec-plan-workflow.enabled\n",
          encoding="utf-8",
      )
      return root


  def _names(root, config):
      return {name for _, name in collect_rule_sources(root, [], config=config)}


  def test_gate_delivers_rule_when_enabled(tmp_path):
      root = _meta_root(tmp_path)
      config = {"spec-plan-workflow": {"enabled": True}}
      names = _names(root, config)
      assert "spec-plan-workflow.md" in names
      assert "branch-guard.md" in names


  @pytest.mark.parametrize("preset", ["default", "minimal", "silent", "lazy"])
  def test_gate_removes_rule_when_disabled_in_every_preset(tmp_path, preset):
      root = _meta_root(tmp_path)
      config = {"spec-plan-workflow": {"enabled": False}, "rules-preset": preset}
      names = _names(root, config)
      assert "spec-plan-workflow.md" not in names
      assert "branch-guard.md" in names


  def test_none_config_is_fail_closed(tmp_path):
      root = _meta_root(tmp_path)
      assert "spec-plan-workflow.md" not in _names(root, None)


  def test_missing_config_kwarg_is_type_error(tmp_path):
      root = _meta_root(tmp_path)
      with pytest.raises(TypeError):
          collect_rule_sources(root, [])
  ```

- [ ] **Step 2: Run the tests, confirm they fail**

  Run: `pytest tests/test_rules_activation_gate.py -v`
  Expected: FAIL — Signatur akzeptiert kein `config`, gated Rule wird in allen Presets ausgeliefert.

- [ ] **Step 3: Implement the gate and update all 6 call-sites**

  In `scripts/lib/rules.py` nach `load_rules_presets` ergänzen:

  ```python
  def load_rule_gates(agent_meta_root: Path) -> dict:
      """Load the preset-independent top-level `rule-gates` section."""
      data, _ = _load_yaml_or_json(agent_meta_root / RULES_PRESETS_CONFIG_YAML)
      if not data:
          return {}
      gates = data.get("rule-gates", {})
      return {k: v for k, v in gates.items() if not k.startswith("_")}


  def _rule_gate_satisfied(requires: str, config: dict | None,
                           agent_meta_root: Path) -> bool:
      """Fail-closed evaluation of one rule-gate requirement.

      Unknown requirements never activate a rule; config=None never does."""
      if config is None:
          return False
      if requires == "spec-plan-workflow.enabled":
          from .dod import resolve_spec_plan_enabled
          return resolve_spec_plan_enabled(config, agent_meta_root)
      return False
  ```

  Die Signatur von `collect_rule_sources` ändern zu
  `def collect_rule_sources(agent_meta_root: Path, platforms: list[str], *, config: dict | None) -> list[tuple[Path, str]]:`
  und im `generic_dir`-Loop das Gate anwenden:

  ```python
      gates = load_rule_gates(agent_meta_root)

      generic_dir = agent_meta_root / RULES_DIR / "1-generic"
      if generic_dir.exists():
          for f in sorted(generic_dir.glob("*.md")):
              if f.name.startswith("_"):
                  continue
              gate = gates.get(f.stem)
              if gate and not _rule_gate_satisfied(
                  gate.get("requires", ""), config, agent_meta_root,
              ):
                  continue
              seen[f.name] = f
  ```

  In `config/rules-presets.yaml` auf Top-Level (Geschwister von `presets:`) ergänzen:

  ```yaml
  # Preset-unabhaengige Gates: eine Rule wird nur ausgeliefert, wenn ihre
  # `requires`-Bedingung erfuellt ist. Fail-closed: unbekannte Bedingung oder
  # config=None => Rule bleibt draussen. Zuordnung greift in collect_rule_sources.
  rule-gates:
    spec-plan-workflow:
      requires: spec-plan-workflow.enabled
    brainstorming-gate:
      requires: spec-plan-workflow.enabled
    writing-plans:
      requires: spec-plan-workflow.enabled
    plan-ledger:
      requires: spec-plan-workflow.enabled
  ```

  Alle 6 Call-Sites auf `collect_rule_sources(agent_meta_root, platforms, config=config)` umstellen: `rules.py:282`, `rules.py:370`, `agent_sync.py:129`, `agent_sync.py:190`, `context.py:1133`, `sync_pipeline.py:555`. An jeder Stelle ist `config` bereits im Scope.

- [ ] **Step 4: Run the tests again, confirm they pass**

  Run: `pytest tests/test_rules_activation_gate.py tests/test_embed_rules_channel.py -q`
  Expected: PASS. Zusätzlich: `python3 scripts/sync.py --dry-run` läuft ohne `TypeError`.

- [ ] **Step 5: Commit**

  ```bash
  git add scripts/lib/rules.py scripts/lib/agent_sync.py scripts/lib/context.py scripts/lib/sync_pipeline.py config/rules-presets.yaml tests/test_rules_activation_gate.py
  git commit -m "feat: gate spec-plan rules fail-closed at choke-point"
  ```

---

### Task 7: Neue Rules + `lazy`-Preset-Einträge

**Files:**
- Create: `rules/1-generic/spec-plan-workflow.md`
- Create: `rules/1-generic/brainstorming-gate.md`
- Create: `rules/1-generic/writing-plans.md`
- Create: `rules/1-generic/plan-ledger.md`
- Modify: `config/rules-presets.yaml` (`presets.lazy`)
- Modify: `tests/test_rules_activation_gate.py` (Assertions ergänzen)

**Interfaces:**
- Consumes: Gate aus Task 6; Rule-Delivery über `channel: skill`.
- Produces: vier Rule-Stems mit `channel: skill` + englischer `skill-description`.

- [ ] **Step 1: Write the failing tests**

  An `tests/test_rules_activation_gate.py` anhängen:

  ```python
  import json  # noqa: E402

  _NEW_STEMS = (
      "spec-plan-workflow",
      "brainstorming-gate",
      "writing-plans",
      "plan-ledger",
  )


  def test_new_rule_files_exist():
      for stem in _NEW_STEMS:
          assert (REPO_ROOT / "rules" / "1-generic" / f"{stem}.md").is_file()


  def test_lazy_preset_routes_new_rules_to_skill_channel():
      from lib.io import _load_yaml_or_json
      data, _ = _load_yaml_or_json(REPO_ROOT / "config" / "rules-presets.yaml")
      lazy = data["presets"]["lazy"]
      for stem in _NEW_STEMS:
          assert lazy[stem]["channel"] == "skill"
          assert lazy[stem]["skill-description"].strip()


  def test_rule_gates_section_declares_all_new_stems():
      from lib.io import _load_yaml_or_json
      data, _ = _load_yaml_or_json(REPO_ROOT / "config" / "rules-presets.yaml")
      gates = data["rule-gates"]
      for stem in _NEW_STEMS:
          assert gates[stem]["requires"] == "spec-plan-workflow.enabled"
  ```

- [ ] **Step 2: Run the tests, confirm they fail**

  Run: `pytest tests/test_rules_activation_gate.py -v`
  Expected: FAIL — Rule-Dateien fehlen, `lazy`-Einträge fehlen.

- [ ] **Step 3: Create the four rules and register them**

  Plain Markdown (kein Pflicht-Frontmatter) mit je einer H1 und dem Prozessinhalt:

  - `rules/1-generic/spec-plan-workflow.md` — Master-Rule: Phasen `classify → spec → approve → plan → execute`; S/M/L/XL↔Klassen-Mapping inkl. F7-Zusatzkriterium (öffentliche Schnittstellen/Contracts, Datenmodell/Schema, mehr als eine Subsystem-/Komponentengrenze); Approval-Gate als Convention boundary; Spec-Template §7.1; Approval-Marker `Status: APPROVED`; Trace-Anker `spec-id: SPEC-<slug>`; SE-Abgrenzung (kein Auto-Start); Pfade über die Platzhalter `{{SPEC_PLAN_SPECS_DIR}}`/`{{SPEC_PLAN_PLANS_DIR}}` (Task 2/2b), nie hartcodiert.
  - `rules/1-generic/brainstorming-gate.md` — Klassifikation Spike/Bounded/Architectural; Gate „keine Implementierung ohne Approval“; Einzelfragen statt Fragenkatalog; 2–3 Optionen mit Trade-offs; abschnittsweise Abnahme.
  - `rules/1-generic/writing-plans.md` — Plan-Header inkl. `pipeline_stages`; File-Structure-Map; bite-sized TDD-Tasks; `Files:`/`Interfaces:` (Consumes/Produces); No-Placeholder; Self-Review.
  - `rules/1-generic/plan-ledger.md` — Execution: frischer Subagent pro Task, Review, Ledger = Checkboxen + `CheckpointStore`/`barrier.checkpoint_ref`, Ownership/Barrieren via `check_plan_file_overlap`, Worktree-Verbot-Adaption, Archiv-Trigger (alle Checkboxen + manuelle Merge-Bestätigung, Ziel `docs/plans/archive`).

  In `config/rules-presets.yaml` unter `presets.lazy` die vier Einträge aus Spezifikation §4.1 ergänzen (`channel: skill` + englische `skill-description`).

- [ ] **Step 4: Run the tests again, confirm they pass**

  Run: `pytest tests/test_rules_activation_gate.py -q && python3 scripts/sync.py --dry-run`
  Expected: PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add rules/1-generic/spec-plan-workflow.md rules/1-generic/brainstorming-gate.md rules/1-generic/writing-plans.md rules/1-generic/plan-ledger.md config/rules-presets.yaml tests/test_rules_activation_gate.py
  git commit -m "feat: add spec-plan rules and lazy skill channel entries"
  ```

---

## Phase E — Pipeline-Wiring

### Task 8: `concept-driven-dev` + `feature-lifecycle` erweitern

**Files:**
- Modify: `config/role-defaults.yaml:2344-2516`
- Modify: `tests/test_pipelines.py`
- Modify: `tests/test_orchestration_contract.py`

**Interfaces:**
- Consumes: `dod_flag: spec-plan-enabled` (Task 1/2); bestehende `parse_plan_ref`/`validate_plan_ref`/`pipeline_stages`-Rendering (`scripts/lib/pipelines.py:379/444/862`).
- Produces: `concept-driven-dev`-Stages `classify` (agent `ideation`, conditional `dod_flag`), `approve` (`requires_approval: true`, `dod_flag: spec-plan-enabled`), `plan` (agent `planner`) vor `implement`. Die Spec-Referenz zwischen den Phasen läuft ausschließlich über das A2A-/Payload-Feld `spec_ref` (Spec §9) — **kein** neuer `role-defaults`-Key.

- [ ] **Step 1: Write the failing tests**

  In `tests/test_pipelines.py` einen Test ergänzen, der das Provider-Block-Rendering für `concept-driven-dev` prüft: bei `spec-plan-enabled: false` fehlen `approve`/`plan`, bei `true` sind sie vorhanden und in der Reihenfolge `specify` → `plan` → `implement`. In `tests/test_orchestration_contract.py` die Phasen-Reihenfolge `classify → specify → approve → plan → implement → validate` assertieren.

  ```python
  def test_concept_driven_dev_spec_plan_stage_order():
      from lib.pipelines import inject_pipeline_blocks, load_quality_pipelines
      from lib.dod import resolve_dod
      pipelines = load_quality_pipelines(str(REPO_ROOT))
      dod = resolve_dod({"platforms": [], "spec-plan-workflow": {"enabled": True}}, REPO_ROOT)
      rendered = inject_pipeline_blocks(
          "{{PIPELINE_CONCEPT_DRIVEN_DEV_BLOCK}}", pipelines, "Claude", dod,
      )
      # Exakte Claude-Render-Strings (pipelines.py:639 sequential_item):
      #   {index}. background(agent="{agent}", prompt="{task}")
      order = [
          rendered.index('background(agent="concept-specifier"'),
          rendered.index('background(agent="planner"'),
          rendered.index('prompt="Implementierung'),
      ]
      assert order == sorted(order)
      assert "Abnahme erforderlich vor Stage 'approve'" in rendered


  def test_concept_driven_dev_spec_plan_hidden_when_disabled():
      from lib.pipelines import inject_pipeline_blocks, load_quality_pipelines
      from lib.dod import resolve_dod
      pipelines = load_quality_pipelines(str(REPO_ROOT))
      dod = resolve_dod({"platforms": [], "spec-plan-workflow": {"enabled": False}}, REPO_ROOT)
      rendered = inject_pipeline_blocks(
          "{{PIPELINE_CONCEPT_DRIVEN_DEV_BLOCK}}", pipelines, "Claude", dod,
      )
      assert "Abnahme erforderlich" not in rendered
      assert 'background(agent="planner"' not in rendered
  ```

- [ ] **Step 2: Run the tests, confirm they fail**

  Run: `pytest tests/test_pipelines.py tests/test_orchestration_contract.py -q`
  Expected: FAIL — `classify`/`approve`/`plan` fehlen.

- [ ] **Step 3: Extend both pipelines**

  In `config/role-defaults.yaml` unter `concept-driven-dev.stages` **vor** `specify` eine Stage ergänzen:

  ```yaml
      - id: classify
        agent: ideation
        task: 'Klassifikation Spike/Bounded/Architectural inkl. S/M/L/XL-Mapping (F7-Zusatzkriterium)'
        mode: conditional
        condition:
          dod_flag: spec-plan-enabled
  ```

  **Nach** `review` und **vor** `implement` ergänzen:

  ```yaml
      - id: approve
        agent: concept-reviewer
        task: 'Abnahme der Spec (Status: APPROVED) — explizite Nutzerfreigabe'
        mode: conditional
        requires_approval: true
        condition:
          dod_flag: spec-plan-enabled
      - id: plan
        agent: planner
        task: 'Umsetzungsplan gegen die freigegebene Spec (Plan-Template, pipeline_stages, F6-Graph-Validator)'
        mode: conditional
        condition:
          dod_flag: spec-plan-enabled
  ```

  Unter `feature-lifecycle` bleibt `accepts_plan_ref: true` unverändert. Die Spec-Referenz wird **nicht** als neuer Config-Key deklariert: der Orchestrator übergibt sie als A2A-/Payload-Feld `spec_ref` (Spec §9) an `concept-specifier`/`concept-reviewer`/`planner`. Es gibt keinen `accepts_spec_ref`-Consumer und daher auch keinen solchen Key.

  In `scripts/lib/pipelines.py` ist **keine** Code-Änderung nötig: `parse_plan_ref`/`validate_plan_ref` lesen `pipeline_stages` bereits (`:379`/`:444`) und `:862` rendert die Prüfzeile. Verifikation erfolgt über die Tests.

- [ ] **Step 4: Run the tests again, confirm they pass**

  Run: `pytest tests/test_pipelines.py tests/test_orchestration_contract.py -q`
  Expected: PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add config/role-defaults.yaml tests/test_pipelines.py tests/test_orchestration_contract.py
  git commit -m "feat: add classify/approve/plan stages to concept-driven-dev"
  ```

---

## Phase F — Validator (F6/F12)

### Task 9: Ledger-/Section-Parser in `scripts/lib/consistency/spec_plan.py`

**Files:**
- Create: `scripts/lib/consistency/spec_plan.py`
- Create: `tests/test_plan_ledger.py`

**Interfaces:**
- Consumes: `scripts/lib/consistency/report.py` (`Finding`, `Severity`); `CheckpointStore`/`Checkpoint` (`scripts/lib/checkpoint.py:263/349/410`).
- Produces: Konstanten `REQUIRED_SPEC_SECTIONS: tuple[str, ...]` und `REQUIRED_PLAN_SECTIONS: tuple[str, ...]`; `parse_plan_ledger(plan_path: Path) -> dict` mit `{"checkboxes": int, "checked": int, "complete": bool, "status": str | None}`.

- [ ] **Step 1: Write the failing test**

  Create `tests/test_plan_ledger.py`:

  ```python
  """Ledger parsing: checkbox/status view is the human-readable ledger; the
  CheckpointStore is the machine-readable recovery source (D2)."""
  import sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(REPO_ROOT / "scripts"))

  from lib.checkpoint import Checkpoint, CheckpointStore  # noqa: E402
  from lib.consistency.spec_plan import (  # noqa: E402
      REQUIRED_PLAN_SECTIONS,
      REQUIRED_SPEC_SECTIONS,
      parse_plan_ledger,
  )


  def _plan(tmp_path: Path, text: str) -> Path:
      path = tmp_path / "2026-09-13-demo.md"
      path.write_text(text, encoding="utf-8")
      return path


  def test_all_checked_is_complete(tmp_path):
      ledger = parse_plan_ledger(_plan(
          tmp_path,
          "# Demo Implementation Plan\n> Status: IN PROGRESS\n"
          "- [x] a\n- [x] b\n",
      ))
      assert ledger["checkboxes"] == 2
      assert ledger["checked"] == 2
      assert ledger["complete"] is True
      assert ledger["status"] == "IN PROGRESS"


  def test_open_checkbox_is_incomplete(tmp_path):
      ledger = parse_plan_ledger(_plan(
          tmp_path,
          "# Demo Implementation Plan\n> Status: geplant\n- [x] a\n- [ ] b\n",
      ))
      assert ledger["checkboxes"] == 2
      assert ledger["checked"] == 1
      assert ledger["complete"] is False


  def test_missing_status_is_none(tmp_path):
      ledger = parse_plan_ledger(_plan(tmp_path, "# Demo\n- [ ] a\n"))
      assert ledger["status"] is None
      assert ledger["complete"] is False


  def test_required_sections_include_pipeline_stages():
      assert "pipeline_stages" in " ".join(REQUIRED_PLAN_SECTIONS)
      assert REQUIRED_SPEC_SECTIONS


  def test_checkpoint_store_round_trip_is_recovery_source(tmp_path):
      store = CheckpointStore(project_root=tmp_path)
      store.save_checkpoint(
          "sess1",
          Checkpoint(task_id="task-3", agent="developer",
                     task_description="impl", status="completed"),
      )
      last = store.get_last_checkpoint("sess1")
      assert last is not None
      assert last.task_id == "task-3"
      assert [c.task_id for c in store.get_completed_steps("sess1")] == ["task-3"]
  ```

- [ ] **Step 2: Run the test, confirm it fails**

  Run: `pytest tests/test_plan_ledger.py -v`
  Expected: FAIL — `ModuleNotFoundError: lib.consistency.spec_plan`.

- [ ] **Step 3: Implement the parser**

  Create `scripts/lib/consistency/spec_plan.py` mit Modul-Docstring (Verweis §7.3/D9), `from __future__ import annotations`, `import re`, `from pathlib import Path`, `from .report import Finding, Severity` (Finding erst ab Task 10 genutzt, Import dennoch vorbereiten). Konstanten:

  ```python
  REQUIRED_SPEC_SECTIONS = (
      "## Problem", "## Ziel", "## Nicht-Ziele", "## Interface Contracts",
      "## Datenfluss", "## Acceptance Criteria", "## Offene Fragen",
      "## Trace-Anker",
  )
  REQUIRED_PLAN_SECTIONS = (
      "**Goal:**", "**Architecture:**", "**Tech Stack:**", "**Spec:**",
      "## Global Constraints", "## File Structure", "pipeline_stages",
  )
  ```

  `parse_plan_ledger`:

  ```python
  def parse_plan_ledger(plan_path: Path) -> dict:
      text = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""
      checkboxes = re.findall(r"^- \[( |x|X)\]", text, flags=re.MULTILINE)
      checked = sum(1 for box in checkboxes if box.lower() == "x")
      match = re.search(r"^\s*>?\s*Status:\s*(.+?)\s*$", text, flags=re.MULTILINE)
      status = match.group(1).strip() if match else None
      return {
          "checkboxes": len(checkboxes),
          "checked": checked,
          "complete": bool(checkboxes) and checked == len(checkboxes),
          "status": status,
      }
  ```

- [ ] **Step 4: Run the test again, confirm it passes**

  Run: `pytest tests/test_plan_ledger.py -v`
  Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

  ```bash
  git add scripts/lib/consistency/spec_plan.py tests/test_plan_ledger.py
  git commit -m "feat: add spec-plan ledger parser and section constants"
  ```

---

### Task 10: `check_spec_plan_workflow` — Checks, Graph-Validator, Legacy-Scan

**Files:**
- Modify: `scripts/lib/consistency/spec_plan.py`
- Create: `tests/test_spec_plan_consistency.py`
- Create: `tests/test_spec_plan_migration.py`
- Modify: `tests/test_orchestration_contract.py` (bestehende `FanoutPlan`/`validate_plan`/`check_plan_file_overlap`-Tests; R5)
- Modify: `tests/test_barrier_runtime.py`

**Interfaces:**
- Consumes: `parse_plan_ledger`, `REQUIRED_SPEC_SECTIONS`/`REQUIRED_PLAN_SECTIONS` (Task 9); `resolve_spec_plan_enabled` (Task 1); `resolve_dod`; `resolve_agent_meta_root` (`scripts/lib/providers.py:14`); `FanoutTask`/`FanoutPlan`/`validate_plan`/`check_plan_file_overlap` (`scripts/lib/orchestration.py:79/100/237/309`).
- Produces: `check_spec_plan_workflow(project_root: Path, config: dict | None = None, *, agent_meta_root: Path | None = None, changed_files: set[str] | None = None) -> list[Finding]`; Check-Codes `spec_plan_required_sections`, `spec_plan_no_placeholder`, `spec_plan_traceability`, `spec_plan_approval_marker`, `spec_plan_ledger_format`, `spec_plan_plan_graph`.

- [ ] **Step 1: Write the failing tests**

  Create `tests/test_spec_plan_consistency.py`:

  ```python
  """check_spec_plan_workflow: required sections incl. pipeline_stages,
  no-placeholder, traceability, approval marker, ledger format, plan graph.
  effective_enabled=false returns [] (no-op)."""
  import sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(REPO_ROOT / "scripts"))

  from lib.consistency.report import Severity  # noqa: E402
  from lib.consistency.spec_plan import check_spec_plan_workflow  # noqa: E402

  _ENABLED = {"spec-plan-workflow": {"enabled": True}}
  _DISABLED = {"spec-plan-workflow": {"enabled": False}}

  _GOOD_SPEC = (
      "# Demo — Spec\n> Status: APPROVED (2026-09-13)\n"
      "## Problem\nDemo-Problem\n"
      "## Ziel\nDemo-Ziel\n"
      "## Nicht-Ziele\nDemo-Nicht-Ziel\n"
      "## Interface Contracts\n"
      "## Datenfluss\n"
      "## Acceptance Criteria\n1. AC-1\n"
      "## Offene Fragen + Risiken\n"
      "## Trace-Anker: spec-id: SPEC-demo\n"
  )


  def _plan(text: str) -> str:
      return (
          "# Demo Implementation Plan\n> Status: geplant\n"
          "**Goal:** demo\n**Architecture:** demo\n**Tech Stack:** demo\n"
          "**Spec:** docs/specs/2026-09-13-demo-design.md\n"
          "## Global Constraints\n- stdlib only\n"
          "## File Structure\n- Create: docs/specs/x.md\n"
          "## Trace-Anker: spec-id: SPEC-demo\n"
          "---\npipeline_stages:\n  implement: 1\n---\n"
          + text
      )


  def _write(tmp_path: Path, spec: str, plan: str) -> Path:
      (tmp_path / "docs" / "specs").mkdir(parents=True)
      (tmp_path / "docs" / "plans").mkdir(parents=True)
      (tmp_path / "docs" / "specs" / "2026-09-13-demo-design.md").write_text(spec, encoding="utf-8")
      (tmp_path / "docs" / "plans" / "2026-09-13-demo.md").write_text(plan, encoding="utf-8")
      return tmp_path


  def test_disabled_returns_empty(tmp_path):
      _write(tmp_path, _GOOD_SPEC, _plan("- [x] Task 1\n"))
      assert check_spec_plan_workflow(
          tmp_path, _DISABLED, agent_meta_root=REPO_ROOT,
      ) == []


  def test_good_artifacts_pass(tmp_path):
      _write(tmp_path, _GOOD_SPEC, _plan("- [x] Task 1\n"))
      findings = check_spec_plan_workflow(
          tmp_path, _ENABLED, agent_meta_root=REPO_ROOT,
      )
      assert findings == []


  def test_missing_pipeline_stages_is_error(tmp_path):
      plan = _plan("- [x] Task 1\n").replace(
          "pipeline_stages:\n  implement: 1\n", "",
      )
      _write(tmp_path, _GOOD_SPEC, plan)
      findings = check_spec_plan_workflow(
          tmp_path, {**_ENABLED, "dod": {"spec-plan-required": True}},
          agent_meta_root=REPO_ROOT,
      )
      checks = {f.check for f in findings}
      assert "spec_plan_required_sections" in checks
      assert any(f.severity == Severity.ERROR for f in findings)


  def test_placeholder_is_error(tmp_path):
      _write(tmp_path, _GOOD_SPEC, _plan("- [ ] TBD\n"))
      findings = check_spec_plan_workflow(
          tmp_path, _ENABLED, agent_meta_root=REPO_ROOT,
      )
      assert any(f.check == "spec_plan_no_placeholder" for f in findings)


  def test_plan_graph_no_false_positive_on_acyclic_plan(tmp_path):
      plan = _plan(
          "### Task 1\n**Files:** Modify: a.py\n### Task 2\n**Files:** Modify: b.py\n"
      )
      _write(tmp_path, _GOOD_SPEC, plan)
      findings = check_spec_plan_workflow(
          tmp_path, _ENABLED, agent_meta_root=REPO_ROOT,
      )
      assert not any(f.check == "spec_plan_plan_graph" and f.severity == Severity.ERROR
                     for f in findings)
  ```

  Create `tests/test_spec_plan_migration.py`:

  ```python
  """Legacy paths are read (WARNING, not ERROR) and never auto-moved."""
  import sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(REPO_ROOT / "scripts"))

  from lib.consistency.report import Severity  # noqa: E402
  from lib.consistency.spec_plan import check_spec_plan_workflow  # noqa: E402

  _ENABLED = {
      "spec-plan-workflow": {
          "enabled": True,
          "paths": {"legacy": ["docs/superpowers/specs"]},
      }
  }


  def test_legacy_without_template_is_warning_not_error(tmp_path):
      legacy = tmp_path / "docs" / "superpowers" / "specs"
      legacy.mkdir(parents=True)
      (legacy / "old-note.md").write_text("# old\n", encoding="utf-8")
      findings = check_spec_plan_workflow(
          tmp_path, _ENABLED, agent_meta_root=REPO_ROOT,
      )
      assert all(f.severity != Severity.ERROR for f in findings)


  def test_no_auto_move_of_legacy_files(tmp_path):
      legacy = tmp_path / "docs" / "superpowers" / "specs"
      legacy.mkdir(parents=True)
      original = legacy / "2026-01-01-old-design.md"
      original.write_text("# old design\n", encoding="utf-8")
      check_spec_plan_workflow(tmp_path, _ENABLED, agent_meta_root=REPO_ROOT)
      assert original.exists()
  ```

- [ ] **Step 2: Run the tests, confirm they fail**

  Run: `pytest tests/test_spec_plan_consistency.py tests/test_spec_plan_migration.py -q`
  Expected: FAIL — `check_spec_plan_workflow` existiert noch nicht.

- [ ] **Step 3: Implement `check_spec_plan_workflow` and the checks**

  In `scripts/lib/consistency/spec_plan.py` ergänzen:

  1. `_load_config(project_root)` → `from ..config import load_config; load_config(project_root / ".meta-config" / "project.yaml")` (lazy import; **kein** `str()` — `load_config` erwartet `Path`, siehe `scripts/lib/config.py:221`).
  2. `_resolve_agent_meta_root(project_root, agent_meta_root)` → bei `None`: `from ..providers import resolve_agent_meta_root; resolve_agent_meta_root(project_root)`.
  3. Early return `[]` wenn `not resolve_spec_plan_enabled(config, agent_meta_root)`.
  4. Scan (Spec §5.1): `paths.specs`/`paths.plans` mit `scan.include`-Globs durchsuchen. Nur Dateien, die **genau** einem der drei Spec-Muster entsprechen — `YYYY-MM-DD-<topic>-design.md`, `YYYY-MM-DD-<topic>.md`, `*-spike.md` — und, falls `scan.changed-files-only` gesetzt ist, zusätzlich in `changed_files` liegen (`changed_files=None` ⇒ kein Changed-Files-Filter, alle Muster-Treffer). Legacy-Pfade (`paths.legacy`) werden **gelesen**; Dateien ohne Muster-Treffer erzeugen `Severity.WARNING` mit Check `spec_plan_legacy`.
  5. Checks (Finding-Felder `severity`, `check`, `file`, `message`, `suggestion`):
     - `spec_plan_required_sections`: fehlende Pflichtsektion → ERROR bei `spec-plan-required: true` (aus `resolve_dod`), sonst WARNING; `pipeline_stages` aus `REQUIRED_PLAN_SECTIONS` zählt mit.
     - `spec_plan_no_placeholder`: literal `TODO`, literal `TBD`, `<platzhalter>`, ein alleinstehender dreifacher Punkt oder leere `Interfaces:` → ERROR.
     - `spec_plan_traceability`: `**Spec:**`-Pfad existiert nicht → ERROR; `spec-id:`-Anker der Spec wird in keinem Plan referenziert → ERROR. Die Sub-Check „Task-ID ↔ Testname" wird **ausschließlich** bei `spec-plan-traceability: true` ausgewertet (fehlende Zuordnung → ERROR); bei `false` wird sie übersprungen, damit ein ansonsten sauberer Plan keine Findings erzeugt.
     - `spec_plan_approval_marker`: `Status: APPROVED` fehlt, während Plan Tasks hat → ERROR.
     - `spec_plan_ledger_format`: `parse_plan_ledger`-Inkonsistenz (z.B. Checkboxen vorhanden, `Status:` fehlt) → WARNING.
     - `spec_plan_plan_graph`: pro Plan aus den `### Task`-Blöcken je einen `FanoutTask` bauen — `task_id` aus der Task-Nummer, `target_agent` aus dem `Agent`-Feld der Task-Zeile, `prompt` aus dem Task-Titel, `files_touched` als Tupel der `Modify:`/`Create:`-Pfade, `dependencies` als Tupel der `Depends on`-IDs — dann `FanoutPlan(kind="sequential", tasks=tuple(erzeugte_tasks), max_parallel=len(erzeugte_tasks))` (nur Graph-/Konsistenzprüfung; `max_parallel` bewusst auf die Task-Anzahl gesetzt, damit die Parallelitäts-Budget-Regel hier nicht greift — jeder reale Plan hat mehr als 2 Tasks) und `validate_plan(plan, file_overlap=check_plan_file_overlap(plan, project_root))`; jeder Fehlerstring → ERROR. `execute_plan` wird **nicht** importiert.
  6. `agent_meta_root` in jede `resolve_spec_plan_enabled`/`resolve_dod`-Auswertung durchreichen.

  In `tests/test_orchestration_contract.py` zwei Tests ergänzen:
  - **Zyklus:** `check_spec_plan_workflow` mit einem zyklischen Plan aufrufen (Task 2 `dependencies: ("task-1",)`, Task 1 `dependencies: ("task-2",)`) und einen `ERROR`-Finding mit Check `spec_plan_plan_graph` erwarten.
  - **`>2 Tasks` (Regression zu R4):** einen azyklischen Plan mit drei Tasks (`t1 → t2 → t3`) durch `check_spec_plan_workflow` schicken und sicherstellen, dass **kein** `spec_plan_plan_graph`-ERROR entsteht (der Graph-Validator darf die `max_parallel`-Default-2-Budget-Regel nicht anwenden).
  In `tests/test_barrier_runtime.py` zusätzlich den Zyklus-Test analog ergänzen.

- [ ] **Step 4: Run the tests again, confirm they pass**

  Run: `pytest tests/test_spec_plan_consistency.py tests/test_spec_plan_migration.py tests/test_orchestration_contract.py tests/test_barrier_runtime.py -q`
  Expected: PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add scripts/lib/consistency/spec_plan.py tests/test_spec_plan_consistency.py tests/test_spec_plan_migration.py tests/test_orchestration_contract.py tests/test_barrier_runtime.py
  git commit -m "feat: add spec-plan consistency checks with graph validator"
  ```

---

### Task 11: `--validate-spec-plan` CLI-Modus (F12)

**Files:**
- Create: `scripts/lib/spec_plan_validate.py`
- Modify: `scripts/sync.py:147` (Flag), `scripts/sync.py:262-283` (Dispatch: `_MODE_HANDLERS` beginnt bei `:262`)
- Create: `tests/test_spec_plan_validate_cli.py`
- Modify: `docs/api/cli-reference.md`

**Interfaces:**
- Consumes: `check_spec_plan_workflow` (Task 10); `SyncLog` (`scripts/lib/log.py`); `_SyncContext`.
- Produces: `MODE = "validate-spec-plan"`, `validate_spec_plan(project_root: Path, config: dict | None, log: SyncLog) -> int`, `_handle_validate_spec_plan(ctx) -> None`.

- [ ] **Step 1: Write the failing test**

  Create `tests/test_spec_plan_validate_cli.py`:

  ```python
  """--validate-spec-plan exits 0 without artifacts and is a no-op when the
  master switch is off (F12)."""
  import sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(REPO_ROOT / "scripts"))

  from lib.log import SyncLog  # noqa: E402
  from lib.spec_plan_validate import validate_spec_plan  # noqa: E402


  def _log(tmp_path):
      return SyncLog()


  def test_no_artifacts_exit_zero(tmp_path):
      code = validate_spec_plan(
          tmp_path, {"platforms": [], "spec-plan-workflow": {"enabled": True}}, _log(tmp_path),
      )
      assert code == 0


  def test_enabled_false_is_noop_exit_zero(tmp_path):
      code = validate_spec_plan(
          tmp_path, {"platforms": [], "spec-plan-workflow": {"enabled": False}}, _log(tmp_path),
      )
      assert code == 0


  def test_flag_registered_in_parser():
      from sync import _build_arg_parser
      args = _build_arg_parser().parse_args(["--validate-spec-plan"])
      assert args.validate_spec_plan is True
  ```

- [ ] **Step 2: Run the tests, confirm they fail**

  Run: `pytest tests/test_spec_plan_validate_cli.py -v`
  Expected: FAIL — Modul und Flag fehlen.

- [ ] **Step 3: Implement handler, flag and dispatch**

  Create `scripts/lib/spec_plan_validate.py` analog `se_validate.py`: Docstring mit Exit-Code-Vertrag (0 = clean oder keine Artefakte; 1 = Findings), `MODE = "validate-spec-plan"`, `validate_spec_plan(project_root, config, log)` mit lazy Imports von `Severity`/`check_spec_plan_workflow`, leerem-Ergebnis-No-op (`log.note` + `return 0`), Report-Ausgabe und `_handle_validate_spec_plan(ctx)` (`ctx.mode = MODE`, `code = validate_spec_plan(ctx.project_root, ctx.config, ctx.log)`, `sys.exit(code)`).

  In `scripts/sync.py` neben `--validate-se` registrieren:

  ```python
    parser.add_argument("--validate-spec-plan", action="store_true",
                        help="Standalone spec/plan-workflow validation (F12): checks the "
                             "project's docs/specs and docs/plans artifacts for required "
                             "sections, placeholders, traceability, approval markers, ledger "
                             "format and the plan task graph. Exit 0 when clean, when no "
                             "artifacts exist, or when the workflow is disabled; exit 1 with "
                             "a findings list otherwise.")
  ```

  In `scripts/sync.py` den Handler importieren und in `_MODE_HANDLERS` ergänzen:

  ```python
      (lambda a: a.validate_spec_plan, _handle_validate_spec_plan),
  ```

  In `docs/api/cli-reference.md` eine Tabellenzeile für `--validate-spec-plan` ergänzen.

- [ ] **Step 4: Run the tests again, confirm they pass**

  Run: `pytest tests/test_spec_plan_validate_cli.py -q && python3 scripts/sync.py --validate-spec-plan`
  Expected: PASS; CLI-Lauf endet mit Exit 0 (no-op ohne Artefakte).

- [ ] **Step 5: Commit**

  ```bash
  git add scripts/lib/spec_plan_validate.py scripts/sync.py tests/test_spec_plan_validate_cli.py docs/api/cli-reference.md
  git commit -m "feat: add --validate-spec-plan standalone mode"
  ```

---

## Phase G — Knowledge Engine + Archiv

### Task 12: Concept-Types `Plan`/`Spec` (vier Stellen) + `okf.auto-index`/`auto-log` Schreib-/Update-Semantik

**Files:**
- Modify: `knowledge/schema.md:27-34`
- Modify: `scripts/lib/knowledge.py:13-21`, `scripts/lib/knowledge.py:90-97`, `scripts/lib/knowledge.py:100-168`
- Modify: `.meta-config/project.yaml:20-25`
- Modify: `tests/test_knowledge_engine.py`
- Modify: `tests/test_knowledge_sync_integration.py`

**Interfaces:**
- Consumes: `sync_knowledge_engine` (`knowledge.py:100`); `generate_initial_index`/`generate_initial_log`.
- Produces: `DOMAIN_CONCEPT_TYPES["internal-docs"]` enthält `plan`, `spec`; `_KNOWLEDGE_GITKEEP_SUBDIRS` enthält `wiki/plans`/`wiki/specs`. `okf.auto-index`/`okf.auto-log` steuern das **automatische Schreiben/Aktualisieren** von Index-/Log-Einträgen: `true` (Default) = Workflow schreibt/aktualisiert nach Spec-/Plan-Erstellung; `false` = keine automatischen Schreibzugriffe — `index.md`/`log.md` werden weiterhin gescaffoldet und agent-driven (`planner`/`knowledge-ingestor`→`knowledge-indexer`) gepflegt.

- [ ] **Step 1: Write the failing tests**

  In `tests/test_knowledge_engine.py` ergänzen:

  ```python
  def test_internal_docs_contains_plan_and_spec():
      from lib.knowledge import DOMAIN_CONCEPT_TYPES
      types = DOMAIN_CONCEPT_TYPES["internal-docs"]
      assert "plan" in types
      assert "spec" in types


  def test_gitkeep_subdirs_contain_plans_and_specs():
      from lib.knowledge import _KNOWLEDGE_GITKEEP_SUBDIRS
      rel = {p.as_posix() for p in _KNOWLEDGE_GITKEEP_SUBDIRS}
      assert "wiki/plans" in rel
      assert "wiki/specs" in rel


  def test_auto_flags_false_keep_scaffolded_files(tmp_path):
      from lib.knowledge import sync_knowledge_engine
      from lib.log import SyncLog
      log = SyncLog()
      config = {
          "knowledge-engine": {
              "enabled": True, "domain": "internal-docs", "bundle-path": "knowledge",
              "okf": {"auto-index": False, "auto-log": False},
          }
      }
      sync_knowledge_engine(REPO_ROOT, tmp_path, config, log, dry_run=False)
      # Dateien bleiben nutzbar (weiterhin gescaffoldet) ...
      assert (tmp_path / "knowledge" / "wiki" / "index.md").exists()
      assert (tmp_path / "knowledge" / "wiki" / "log.md").exists()
      # ... aber die automatische Pflege ist aus -> agent-driven.
      infos = " ".join(log.infos)
      assert "agent-driven" in infos
  ```

  (Im Test `REPO_ROOT` importieren, wie in den Bestandstests dieser Datei.)

  In `tests/test_knowledge_sync_integration.py` ergänzen: ein Sync-Lauf mit `internal-docs` erzeugt `knowledge/wiki/plans/.gitkeep` und `knowledge/wiki/specs/.gitkeep`.

- [ ] **Step 2: Run the tests, confirm they fail**

  Run: `pytest tests/test_knowledge_engine.py tests/test_knowledge_sync_integration.py -q`
  Expected: FAIL — `plan`/`spec` fehlen, Subdirs fehlen, `auto-*`-Semantik nicht implementiert.

- [ ] **Step 3: Implement at all four places and wire the flags**

  - `knowledge/schema.md`: Zeile für `Plan` bestätigen und `Spec` ergänzen (`| \`Spec\` | \`knowledge/wiki/plans/\` | Design-Spezifikation, aus der ein Plan abgeleitet wird |`). Additiv, kein Versions-Bump nötig (`knowledge/schema.md:43`).
  - `scripts/lib/knowledge.py:13-21`: `"internal-docs": ["concept", "architecture", "guide", "reference", "plan", "spec"]`.
  - `.meta-config/project.yaml:20-25`: `okf.allowed-types` um `Plan` und `Spec` ergänzen.
  - `scripts/lib/knowledge.py:90-97`: `Path("wiki", "plans")` und `Path("wiki", "specs")` in `_KNOWLEDGE_GITKEEP_SUBDIRS` aufnehmen.
  - `scripts/lib/knowledge.py` `sync_knowledge_engine`: `okf = ke_config.get("okf", {}) or {}` lesen. Die Scaffolder-Blöcke für `index.md`/`log.md` bleiben **unverändert** (Dateien werden immer angelegt); nur wenn `okf.get("auto-index", True)` bzw. `okf.get("auto-log", True)` `False` ist, die automatische Schreib-/Update-Pfadmarkierung überspringen und stattdessen `log.note("knowledge-engine", "index.md maintenance is agent-driven (okf.auto-index: false)")` bzw. analog für `log.md` ausgeben. Die agent-driven Pflege ist in `rules/1-generic/spec-plan-workflow.md` (Task 7) und `agents/1-generic/knowledge-ingestor.md` (Task 13) dokumentiert.

- [ ] **Step 4: Run the tests again, confirm they pass**

  Run: `pytest tests/test_knowledge_engine.py tests/test_knowledge_sync_integration.py -q`
  Expected: PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add knowledge/schema.md scripts/lib/knowledge.py .meta-config/project.yaml tests/test_knowledge_engine.py tests/test_knowledge_sync_integration.py
  git commit -m "feat: add Plan/Spec concept types and wire okf auto flags"
  ```

---

### Task 12b: `external-system-override` verdrahten — KE-Schreibpfade überspringen + `file-index`-Fallback (R2b)

**Files:**
- Modify: `scripts/lib/knowledge.py` (`sync_knowledge_engine`, nach dem `ke_config`-Read)
- Create: `tests/test_spec_plan_override_fallback.py`

**Interfaces:**
- Consumes: `spec-plan-workflow.external-system-override`/`knowledge-engine.enabled` (Task 4); `resolve_index_mode`/`scaffold_spec_plan_dirs` (Task 5b).
- Produces: Bei `external-system-override.enabled: true` ist `sync_knowledge_engine` ein No-op (keine KE-Schreibpfade) und loggt über `log.skip(...)`; der `file-index`-Fallback (`docs/INDEX.md`) wird vom Scaffolder (Task 5b) geschrieben. Damit ist D8/F4 verhaltensseitig verdrahtet, nicht nur deklariert.

- [ ] **Step 1: Write the failing test**

  Create `tests/test_spec_plan_override_fallback.py`:

  ```python
  """external-system-override.enabled=true skips every KE write path and the
  file-index fallback takes over (R2b/D8)."""
  import sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(REPO_ROOT / "scripts"))

  from lib.knowledge import sync_knowledge_engine  # noqa: E402
  from lib.log import SyncLog  # noqa: E402
  from lib.spec_plan_scaffold import scaffold_spec_plan_dirs  # noqa: E402

  _KE = {"knowledge-engine": {"enabled": True, "domain": "internal-docs", "bundle-path": "knowledge"}}
  _INDEX = {"index": {"mode": "knowledge-engine", "fallback-index": "docs/INDEX.md"}}
  _OVERRIDE = {"external-system-override": {"enabled": True, "system": "jira", "note": "external PM"}}


  def test_override_skips_all_ke_writes(tmp_path):
      log = SyncLog()
      config = {**_KE, "spec-plan-workflow": {"enabled": True, **_INDEX, **_OVERRIDE}}
      sync_knowledge_engine(REPO_ROOT, tmp_path, config, log, dry_run=False)
      assert not (tmp_path / "knowledge").exists()
      assert any("external-system-override" in entry for entry in log.skipped)


  def test_without_override_ke_writes(tmp_path):
      log = SyncLog()
      config = {**_KE, "spec-plan-workflow": {"enabled": True, **_INDEX}}
      sync_knowledge_engine(REPO_ROOT, tmp_path, config, log, dry_run=False)
      assert (tmp_path / "knowledge" / "wiki" / "index.md").exists()


  def test_override_end_to_end_uses_file_index_fallback(tmp_path):
      log = SyncLog()
      config = {**_KE, "spec-plan-workflow": {"enabled": True, **_INDEX, **_OVERRIDE}}
      sync_knowledge_engine(REPO_ROOT, tmp_path, config, log, dry_run=False)
      scaffold_spec_plan_dirs(REPO_ROOT, tmp_path, config, log, dry_run=False)
      assert not (tmp_path / "knowledge").exists()
      assert (tmp_path / "docs" / "INDEX.md").is_file()
  ```

- [ ] **Step 2: Run the tests, confirm they fail**

  Run: `pytest tests/test_spec_plan_override_fallback.py -v`
  Expected: FAIL — `sync_knowledge_engine` ignoriert `external-system-override` und schreibt weiterhin `knowledge/`.

- [ ] **Step 3: Skip the KE write paths when the override is active**

  In `scripts/lib/knowledge.py` in `sync_knowledge_engine` unmittelbar nach `ke_config = config.get("knowledge-engine") or {}` ergänzen:

  ```python
      sp = config.get("spec-plan-workflow") or {}
      override = sp.get("external-system-override") or {}
      if override.get("enabled", False):
          log.skip(
              "knowledge-engine",
              "external-system-override enabled — KE write paths skipped "
              "(file-index fallback active)",
          )
          return
  ```

  Keine weitere Änderung an `sync_knowledge_engine`; der `file-index`-Fallback liegt ausschließlich bei `scaffold_spec_plan_dirs` (Task 5b).

- [ ] **Step 4: Run the tests again, confirm they pass**

  Run: `pytest tests/test_spec_plan_override_fallback.py tests/test_knowledge_sync_integration.py -q`
  Expected: PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add scripts/lib/knowledge.py tests/test_spec_plan_override_fallback.py
  git commit -m "feat: skip knowledge-engine writes on external system override"
  ```

---

### Task 13: Archiv + Merge-Bestätigung (F5/F11)

**Files:**
- Modify: `agents/1-generic/documenter.md`
- Modify: `agents/1-generic/knowledge-ingestor.md`
- Modify: `rules/1-generic/plan-ledger.md` (Task 7 erweitern)
- Modify: `tests/test_agents_frontmatter.py`

**Interfaces:**
- Consumes: `archive`-Config-Keys (Task 4); `okf.auto-index`/`okf.auto-log` (Task 12); `docs/plans/README.md:1-11` (bestehende Konvention).
- Produces: dokumentierter Archiv-Ablauf (`mode: auto|ask|off`, `agent: documenter` Default, `knowledge-ingestor` bei KE-Route, `trigger: plan-complete`, Ziel `docs/plans/archive`); keine Auto-Merge-Erkennung; dokumentierte agent-driven Index-/Log-Pflege bei `okf.auto-*: false`.

- [ ] **Step 1: Write the failing test**

  In `tests/test_agents_frontmatter.py` ergänzen:

  ```python
  def test_documenter_documents_plan_archive_target():
      text = (REPO_ROOT / "agents" / "1-generic" / "documenter.md").read_text(encoding="utf-8")
      assert "docs/plans/archive" in text
      assert "plan-complete" in text
  ```

- [ ] **Step 2: Run the test, confirm it fails**

  Run: `pytest tests/test_agents_frontmatter.py::test_documenter_documents_plan_archive_target -v`
  Expected: FAIL — `documenter.md` nennt das Archiv-Ziel noch nicht.

- [ ] **Step 3: Document the archive flow**

  In `agents/1-generic/documenter.md` einen Abschnitt „Plan-Archivierung“ ergänzen: Trigger `archive.trigger: plan-complete` = alle Checkboxen gesetzt **und** Merge manuell bestätigt (F5); Ziel `archive.target` (Default `docs/plans/archive`); `mode: auto` → verschieben + loggen, `ask` → erst nach Zustimmung, `off` → nichts; `archive.agent` = `documenter` (Default) bzw. `knowledge-ingestor` bei KE-Route; kein Sync-Schritt. Frontmatter-`version` bumpen.

  In `agents/1-generic/knowledge-ingestor.md` die KE-Route ergänzen: bei `index.mode: knowledge-engine` übernimmt `knowledge-ingestor` die Archiv-/Index-Route und delegiert intern an `knowledge-indexer` (kein direkter Orchestrator-Dispatch). Zugleich die `okf.auto-index`/`okf.auto-log`-Semantik dokumentieren: bei `false` keine automatischen Index-/Log-Schreibzugriffe, sondern agent-driven Pflege durch `knowledge-indexer`. Frontmatter-`version` bumpen.

  In `rules/1-generic/plan-ledger.md` (aus Task 7) die Archiv-Sektion um dieselben Regeln präzisieren.

- [ ] **Step 4: Run the test again, confirm it passes**

  Run: `pytest tests/test_agents_frontmatter.py -q`
  Expected: PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add agents/1-generic/documenter.md agents/1-generic/knowledge-ingestor.md rules/1-generic/plan-ledger.md tests/test_agents_frontmatter.py
  git commit -m "docs: define agent-based plan archive flow"
  ```

---

## Phase H — Rollen-Templates

### Task 14: `explorer`-Spike-Modus (F10)

**Files:**
- Modify: `agents/1-generic/explorer.md`
- Modify: `tests/test_agents_frontmatter.py`

**Interfaces:**
- Consumes: `rules/1-generic/brainstorming-gate.md`/`spec-plan-workflow.md` (Task 7) als Klassen-Referenz.
- Produces: expliziter Spike-Modus im `explorer`-Prompt (read-only, Empfehlung, Wegwerf-Code-Markierung, Spike-Doc `docs/spikes/YYYY-MM-DD-issue-<n>-<topic>-spike.md`, danach STOP ohne Plan).

- [ ] **Step 1: Write the failing test**

  In `tests/test_agents_frontmatter.py` ergänzen:

  ```python
  def test_explorer_documents_spike_mode():
      text = (REPO_ROOT / "agents" / "1-generic" / "explorer.md").read_text(encoding="utf-8")
      assert "Spike-Modus" in text or "Spike mode" in text
      assert "docs/spikes/" in text
      assert "read-only" in text
  ```

- [ ] **Step 2: Run the test, confirm it fails**

  Run: `pytest tests/test_agents_frontmatter.py::test_explorer_documents_spike_mode -v`
  Expected: FAIL.

- [ ] **Step 3: Add the spike mode**

  In `agents/1-generic/explorer.md` einen Modus-Abschnitt ergänzen: Trigger (Recherche ohne Produktionsänderung, Ziel/Aufwand unklar); strikt read-only (keine Write-Rechte); billige Untersuchung; Befund + Empfehlung berichten; Wegwerf-Code unmissverständlich als solchen markieren (z.B. `SPIKE-CODE — nicht mergen`); Output `docs/spikes/YYYY-MM-DD-issue-<n>-<topic>-spike.md`; nach Spike STOP, kein Plan. Frontmatter-`version` bumpen.

- [ ] **Step 4: Run the test again, confirm it passes**

  Run: `pytest tests/test_agents_frontmatter.py -q`
  Expected: PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add agents/1-generic/explorer.md tests/test_agents_frontmatter.py
  git commit -m "feat: add explorer spike mode"
  ```

---

### Task 15: `ideation` + `concept-architect` + `concept-specifier` + `concept-reviewer` — Spec-Template §7.1

**Files:**
- Modify: `agents/1-generic/ideation.md:47-73`
- Modify: `agents/1-generic/concept-architect.md`
- Modify: `agents/1-generic/concept-specifier.md:35-53`
- Modify: `agents/1-generic/concept-reviewer.md`
- Modify: `tests/test_frontmatter_parity.py`

**Interfaces:**
- Consumes: Spec-Template §7.1; F7-Zusatzkriterium (§2.1).
- Produces: S/M/L/XL↔Spike/Bounded/Architectural-Mapping in `ideation`; Spec-Template + Approval-Marker + Trace-Anker in `concept-specifier`; Pflichtsektionen-Review in `concept-reviewer`; Design-Doc als Spec-Input in `concept-architect`.

- [ ] **Step 1: Write the failing tests**

  In `tests/test_frontmatter_parity.py` ergänzen:

  ```python
  def test_concept_specifier_uses_spec_template_sections():
      text = (REPO_ROOT / "agents" / "1-generic" / "concept-specifier.md").read_text(encoding="utf-8")
      assert "Interface Contracts" in text
      assert "Acceptance Criteria" in text
      assert "spec-id: SPEC-" in text
      assert "Status: APPROVED" in text


  def test_ideation_maps_task_sizes_to_classes():
      text = (REPO_ROOT / "agents" / "1-generic" / "ideation.md").read_text(encoding="utf-8")
      for marker in ("Bounded", "Architectural", "Spike", "S/M/L/XL"):
          assert marker in text
  ```

- [ ] **Step 2: Run the tests, confirm they fail**

  Run: `pytest tests/test_frontmatter_parity.py -q`
  Expected: FAIL.

- [ ] **Step 3: Update the four roles and bump versions**

  - `ideation.md`: Mapping-Tabelle S→übersprungen, M/L→Bounded, XL→Architectural, Recherche→Spike; F7-Zusatzkriterium (öffentliche Schnittstellen/Contracts, Datenmodell/Schema, mehr als eine Subsystem-/Komponentengrenze); Einzelfragen statt Fragenkatalog; 2–3 Optionen mit Trade-offs; Gate-Anbindung. Frontmatter-`version` bumpen.
  - `concept-architect.md`: Design-Doc als Spec-Input; Trace-Anker `spec-id: SPEC-<slug>` vergeben. Frontmatter-`version` bumpen.
  - `concept-specifier.md`: Spec-Template §7.1 als Pflichtsektionen; Approval-Marker `Status: Entwurf | APPROVED (Datum)`; Trace-Anker. Frontmatter-`version` bumpen.
  - `concept-reviewer.md`: Review-Verdikt APPROVED/CHANGES_REQUESTED/BLOCKED gegen Pflichtsektionen, No-Placeholder, Approval-Marker. Frontmatter-`version` bumpen.

- [ ] **Step 4: Run the tests again, confirm they pass**

  Run: `pytest tests/test_frontmatter_parity.py tests/test_agents_frontmatter.py -q`
  Expected: PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add agents/1-generic/ideation.md agents/1-generic/concept-architect.md agents/1-generic/concept-specifier.md agents/1-generic/concept-reviewer.md tests/test_frontmatter_parity.py
  git commit -m "feat: add spec template and classification to concept roles"
  ```

---

### Task 16: `planner` — Plan-Template §7.2 inkl. `pipeline_stages`

**Files:**
- Modify: `agents/1-generic/planner.md:38-51`
- Modify: `tests/test_pipelines.py`

**Interfaces:**
- Consumes: `pipelines.py:379 parse_plan_ref` (liest `pipeline_stages`); `pipelines.py:444 validate_plan_ref`.
- Produces: Plan-Template §7.2 als Pflicht (Header, `**Spec:**`, File-Structure-Map, `pipeline_stages`-Frontmatter, bite-sized TDD-Steps, `Files:`/`Interfaces:`, Self-Review).

- [ ] **Step 1: Write the failing test**

  In `tests/test_pipelines.py` ergänzen:

  ```python
  def test_planner_template_mentions_pipeline_stages_mandate(tmp_path):
      text = (REPO_ROOT / "agents" / "1-generic" / "planner.md").read_text(encoding="utf-8")
      assert "pipeline_stages" in text
      assert "fallback_agent" in text
      # A minimal generated plan with the documented frontmatter parses.
      plan = tmp_path / "2026-09-13-demo.md"
      plan.write_text("---\npipeline_stages:\n  implement: 1\n---\n# Demo\n", encoding="utf-8")
      from lib.pipelines import parse_plan_ref
      assert parse_plan_ref(str(plan))["stages"] == {"implement": 1}
  ```

- [ ] **Step 2: Run the test, confirm it fails**

  Run: `pytest tests/test_pipelines.py::test_planner_template_mentions_pipeline_stages_mandate -v`
  Expected: FAIL — `planner.md` nennt `fallback_agent` noch nicht.

- [ ] **Step 3: Update the planner template**

  In `agents/1-generic/planner.md` den Plan-Template-Abschnitt um `pipeline_stages` als Pflicht ergänzen (ohne dieses Frontmatter fällt ein Plan zur Laufzeit in den `fallback_agent`), inkl. `**Spec:**`, `## Global Constraints`, `## File Structure`, `Files:`/`Interfaces:` (Consumes/Produces), bite-sized TDD-Steps und Self-Review. Die bestehende `pipeline_stages`-Notiz (`:43-47`) bleibt erhalten und wird auf den neuen Abschnitt verwiesen. Frontmatter-`version` bumpen.

- [ ] **Step 4: Run the test again, confirm it passes**

  Run: `pytest tests/test_pipelines.py -q`
  Expected: PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add agents/1-generic/planner.md tests/test_pipelines.py
  git commit -m "feat: mandate pipeline_stages in planner template"
  ```

---

### Task 17: `orchestrator` — Phasen-Dispatch, Gate, Fresh-Subagent, Checkpoint-Recovery

**Files:**
- Modify: `agents/1-generic/orchestrator.md:39`
- Modify: `tests/test_orchestration_contract.py`

**Interfaces:**
- Consumes: `concept-driven-dev`-Stages (Task 8); `rules/1-generic/plan-ledger.md` (Task 7); `CheckpointStore`/`BarrierEntry.checkpoint_ref`.
- Produces: Phasen-Dispatch (`classify → spec → approve → plan → execute`), Gate-Anbindung, „frischer Subagent pro Task“ + Review, Checkpoint-Recovery, Gate auch außerhalb der Pipeline (Regel `use-orchestrator.md`-Anbindung).

- [ ] **Step 1: Write the failing test**

  In `tests/test_orchestration_contract.py` ergänzen: der orchestrator-Prompt nennt die Phasen-Kette und den frischen Subagenten pro Task.

  ```python
  def test_orchestrator_prompt_documents_spec_plan_phases():
      text = (REPO_ROOT / "agents" / "1-generic" / "orchestrator.md").read_text(encoding="utf-8")
      for marker in ("classify", "approve", "plan", "frischer Subagent"):
          assert marker in text
  ```

- [ ] **Step 2: Run the test, confirm it fails**

  Run: `pytest tests/test_orchestration_contract.py::test_orchestrator_prompt_documents_spec_plan_phases -v`
  Expected: FAIL.

- [ ] **Step 3: Update the orchestrator prompt**

  In `agents/1-generic/orchestrator.md` (im Abschnitt `:39`) die Phasen-Kette und die Aufgaben ergänzen: Classify über S/M/L/XL (F7), Gate vor Implementierung, Planungspflicht nach Approval, Execution mit frischem Subagent pro Task + Review + Ledger/Checkpoint-Recovery, Ownership/Barrieren, kein Worktree. Bei `spec-plan-enabled: false` Bestandsverhalten (kein Gate). Frontmatter-`version` bumpen.

- [ ] **Step 4: Run the test again, confirm it passes**

  Run: `pytest tests/test_orchestration_contract.py -q`
  Expected: PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add agents/1-generic/orchestrator.md tests/test_orchestration_contract.py
  git commit -m "feat: wire spec-plan phases into orchestrator prompt"
  ```

---

## Phase I — Szenario + CI + Governance

### Task 18: Szenario `50-spec-plan-workflow` + CI-Anbindung (F12)

**Files:**
- Create: `tests/scenarios/configs/50-spec-plan-workflow.project.yaml`
- Create: `tests/scenarios/asserts/50-spec-plan-workflow.sh`
- Modify: `tests/scenarios/registry.md`
- Modify: `docs/guides/ci/github-actions-sync-check.yml`

**Interfaces:**
- Consumes: alle vorigen Tasks; `tests/scenarios/run.sh`.
- Produces: Szenario mit Assertions (a)–(e) aus §12.3; CI-Step `--validate-spec-plan`.

- [ ] **Step 1: Write the failing scenario**

  Create `tests/scenarios/configs/50-spec-plan-workflow.project.yaml` exakt:

  ```yaml
  agent-meta-version: "1.1.0"
  ai-providers:
  - Claude
  dod-preset: concept-driven
  platforms: []
  rules-preset: lazy
  knowledge-engine:
    enabled: false
  spec-plan-workflow:
    enabled: true
    paths:
      specs: docs/specs
      plans: docs/plans
      spikes: docs/spikes
      legacy:
      - docs/superpowers/specs
      - docs/superpowers/plans
    scan:
      include:
      - '*.md'
      changed-files-only: true
    index:
      mode: knowledge-engine
      fallback-index: docs/INDEX.md
    archive:
      mode: ask
      agent: documenter
      trigger: plan-complete
      target: docs/plans/archive
    external-system-override:
      enabled: true
      system: ''
      note: ''
  project:
    name: scenario-spec-plan-workflow
    prefix: s50
    short: scenario-spec-plan
  variables:
    PROJECT_NAME: scenario-spec-plan-workflow
    PROJECT_DESCRIPTION: Native spec/plan workflow activation test.
    PROJECT_GOAL: Verify scaffolding, rule gate, approval stage, file-index fallback and the disabled no-op.
    GIT_PLATFORM: GitHub
    GIT_REMOTE_URL: https://github.com/example/scenario-spec-plan
    GIT_MAIN_BRANCH: main
  ```

  Create `tests/scenarios/asserts/50-spec-plan-workflow.sh` (ausführbar, `set -u`, `REPO_ROOT`-Kontrakt analog `06-se-cascade.sh`) exakt:

  ```bash
  #!/bin/bash
  # Scenario assert for 50-spec-plan-workflow
  #
  # Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
  # agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
  # violated assertion, printed to stdout/stderr.
  set -u

  REPO_ROOT="${1:-${REPO_ROOT:-}}"
  if [ -z "$REPO_ROOT" ]; then
      echo "ASSERT ERROR (50-spec-plan-workflow): REPO_ROOT missing (pass as \$1 or env var)"
      exit 2
  fi

  fail() {
      echo "ASSERT FAIL (50-spec-plan-workflow): $*"
      exit 1
  }

  # (a) docs/specs, docs/plans, docs/spikes sind gescaffoldet (R1)
  [ -d "docs/specs" ] || fail "docs/specs not scaffolded"
  [ -d "docs/plans" ] || fail "docs/plans not scaffolded"
  [ -d "docs/spikes" ] || fail "docs/spikes not scaffolded"

  # (b) spec-plan-workflow-SKILL.md nur bei enabled (rules-preset lazy -> skill channel)
  [ -f ".claude/skills/spec-plan-workflow/SKILL.md" ] || fail "spec-plan-workflow SKILL.md missing"

  # (c) dod_flag im generierten Pipeline-Block (Approval-Zeile)
  grep -R "Abnahme erforderlich" .claude/ >/dev/null || fail "approval gate line missing"

  # (d) file-index-Fallback greift real (KE off + external-system-override enabled)
  [ -f "docs/INDEX.md" ] || fail "file-index fallback docs/INDEX.md missing"
  [ ! -e "knowledge/wiki/index.md" ] || fail "KE index.md unexpectedly written"

  # (e) enabled:false ist ein harter No-op (--validate-spec-plan Exit 0)
  disabled_dir="$(mktemp -d)"
  mkdir -p "$disabled_dir/.meta-config"
  printf '%s\n' \
      'ai-providers:' \
      '- Claude' \
      'dod-preset: rapid-prototyping' \
      'platforms: []' \
      'knowledge-engine:' \
      '  enabled: false' \
      'spec-plan-workflow:' \
      '  enabled: false' \
      > "$disabled_dir/.meta-config/project.yaml"
  ( cd "$disabled_dir" && python3 "$REPO_ROOT/scripts/sync.py" --validate-spec-plan )
  rc=$?
  rm -rf "$disabled_dir"
  [ "$rc" = "0" ] || fail "--validate-spec-plan nonzero for enabled:false (rc=$rc)"

  echo "ASSERT OK (50-spec-plan-workflow): all markers present"
  ```

  Add a catalog row to `tests/scenarios/registry.md`:

  ```markdown
  | `50-spec-plan-workflow` | Claude | strict (default) | Nativer Spec/Plan-Workflow: Scaffolding, Rule-Gate/Skill-Channel, Approval-Stage, file-index-Fallback, `--validate-spec-plan`-No-op (F2–F12) |
  ```

- [ ] **Step 2: Run the scenario, confirm it fails**

  Run: `tests/scenarios/run.sh 50`
  Expected: FAIL — Assert-Script bzw. Config fehlen (und nach dem Anlegen: Assertions schlagen fehl, solange vorige Tasks nicht gemergt sind).

- [ ] **Step 3: Wire the CI step**

  In `docs/guides/ci/github-actions-sync-check.yml` neben dem bestehenden Sync-Check einen Step ergänzen:

  ```yaml
        - name: Validate spec/plan workflow artifacts (no-op when disabled)
          run: python .agent-meta/scripts/sync.py --validate-spec-plan
  ```

- [ ] **Step 4: Run the scenario again, confirm it passes**

  Run: `tests/scenarios/run.sh 50`
  Expected: PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add tests/scenarios/configs/50-spec-plan-workflow.project.yaml tests/scenarios/asserts/50-spec-plan-workflow.sh tests/scenarios/registry.md docs/guides/ci/github-actions-sync-check.yml
  git commit -m "test: add spec-plan-workflow scenario and CI step"
  ```

---

### Task 19: Rollen-/Versions-Governance + vollständige DoD-Verifikation

**Files:**
- Modify: `agents/2-platform/homeassistant-documenter.md` (`version` + `based-on`)
- Modify: `tests/test_conventions_platform_cascade.py`
- Modify: `tests/test_se_role_boundary.py`
- Verify (kein Edit): weitere `agents/2-platform/**` Overrides, `python3 scripts/sync.py --validate`, `python3 scripts/sync.py --check`, `tests/scenarios/run.sh`

**Interfaces:**
- Consumes: alle vorigen Tasks; `rules/2-platform/agent-meta-conventions.md:59-69` (Change Checklist).
- Produces: keine offenen Frontmatter-Drift/Validierungsfehler; SE-Abgrenzung unverändert.

- [ ] **Step 1: Write the failing drift test**

  In `tests/test_conventions_platform_cascade.py` ergänzen: jeder `2-platform`-Override einer in diesem Plan geänderten Rolle hat `version` und `based-on`, die zur `1-generic`-Version passen. Konkret geprüft wird `agents/2-platform/homeassistant-documenter.md` (Override der in Task 13 geänderten `documenter`-Rolle). In `tests/test_se_role_boundary.py` ergänzen: `systems-engineering` bleibt `enabled:false` in `.meta-config/project.yaml`, und `scripts/sync.py` erzeugt ohne SE-Artefakte keinen SE-Output.

- [ ] **Step 2: Run the tests, confirm they fail**

  Run: `pytest tests/test_conventions_platform_cascade.py tests/test_se_role_boundary.py -q`
  Expected: FAIL, solange der `2-platform`-Override noch die alte `based-on`-Version trägt.

- [ ] **Step 3: Bump `2-platform` overrides**

  Versions-Politik (Change Checklist `rules/2-platform/agent-meta-conventions.md:59-69`): rückwärtskompatible Rollen-Erweiterungen erhalten einen **Minor**-Bump (`x.Y.0`); rein additive neue Pflichtsektionen ebenfalls Minor. Für die in Tasks 13–17 geänderten Rollen mit bestehendem `2-platform`-Override `version` und `based-on` aktualisieren — real betroffen ist `agents/2-platform/homeassistant-documenter.md` (`version` hochziehen, `based-on: "1-generic/documenter.md@<neue 1-generic-Version>"`). Keine sonstigen Inhaltsänderungen.

- [ ] **Step 4: Run the full DoD verification**

  Run:

  ```bash
  python3 scripts/sync.py --validate
  python3 scripts/sync.py --check
  tests/scenarios/run.sh
  pytest tests/ -q
  ```

  Expected: alle grün; `--validate-spec-plan` bleibt bei `effective_enabled=false` Exit 0.

- [ ] **Step 5: Commit**

  ```bash
  git add agents/2-platform tests/test_conventions_platform_cascade.py tests/test_se_role_boundary.py
  git commit -m "chore: sync platform overrides and version bookkeeping"
  ```

---

## Out-of-Scope-Follow-up (F1)

`systems-engineering`-Schema-Deklaration: bewusst **nicht** Teil dieses Vorhabens (§5.2, §10.2, §13).
Der Block bleibt undeklariert und wird vom Top-Level `additionalProperties: true` (`config/project-config.schema.json:2105`) toleriert. Bis zur Deklaration ändert sich nichts.

Die **Issue-Erstellung für dieses Folge-Issue ist nicht Teil dieses Vorhabens** — weder im Plan noch als Task. Der Follow-up wird separat vom Team/User angelegt (siehe §13).

---

## Self-Review

### (a) Spec-Coverage-Tabelle

| Spec-Sektion | Abgedeckt in Task(s) |
|---|---|
| §1 Problem/Ziel/Nicht-Ziele/SE-Abgrenzung | Global Constraints, 10, 11, 19 |
| §2 Konzeptuelles Modell (Klassifikation, S/M/L/XL, F7, Spike, Gate) | 7, 8, 14, 15, 16, 17 |
| §3 Worktree-Konflikt + Bestands-Andocken (F6) | Global Constraints, 9, 10 |
| §4 Native Regeln + Gate (F3) | 6, 7 |
| §5 Config/Schema/DoD/`effective_enabled` (F8) | 1, 2, 2b, 3, 4, 8 |
| §6 Knowledge Engine + Fallback (F2, F4) | 4, 6, 12, 12b, 13 |
| §7 Templates + Validierung (F6, F12) | 9, 10, 11, 16 |
| §8 Auto-Index + Auto-Archiv (F2, F5, F11) | 12, 12b, 13 |
| §9 Rollen-/Pipeline-Wiring | 8, 13, 14, 15, 16, 17 |
| §10 Deaktivierbarkeit/Rückwärtskompatibilität/Migration (F9) | 1, 4, 5, 5b, 6, 10, 12 |
| §11 Trade-offs D1–D10 | D1→3,4; D2→9,10; D3→Global,17; D4→1,2; D5→4; D6→6; D7→10,11; D8→5b,12b; D9→10,11; D10→12,13 |
| §12 Test-/Verifikationsstrategie | 1, 2, 2b, 3, 4, 5, 5b, 6, 7, 8, 9, 10, 11, 12, 12b, 13, 14, 15, 16, 17, 18, 19 |
| §13 Offene Fragen F1–F12 | F1→Out-of-Scope-Abschnitt; F2→12; F3→6; F4→4,12b; F5→13; F6→10; F7→15; F8→1,3; F9→5,5b; F10→14; F11→13; F12→11,18 |

### (b) Placeholder-Scan

Bestätigt: **keine** Platzhalter. Kein `TBD`, kein `TODO`, kein alleinstehender dreifacher Punkt, kein `<platzhalter>`, keine leeren `Interfaces:`. Jede Task benennt exakte Pfade, Symbole, Signaturen und Commit-Messages. (`tuple[str, ...]` in Python-Typannotationen sowie die Template-Syntax `{{#if SPEC_PLAN_WORKFLOW_ENABLED}}…{{/if}}` und `{{SPEC_PLAN_SPECS_DIR}}`/`{{SPEC_PLAN_PLANS_DIR}}` sind Syntax, keine unaufgelösten Platzhalter.)

### (c) Type-/Namenskonsistenz-Check

- `resolve_spec_plan_enabled(config, agent_meta_root, *, dod=None) -> bool` — identisch in Task 1/2/2b/5b/6/10/11/12b.
- `collect_rule_sources(agent_meta_root, platforms, *, config)` — identisch in Task 6 (Definition) und allen 6 Call-Sites.
- `check_spec_plan_workflow(project_root, config=None, *, agent_meta_root=None, changed_files=None) -> list[Finding]` — identisch in Task 10/11.
- `scaffold_spec_plan_dirs(agent_meta_root, project_root, config, log, dry_run) -> None` / `resolve_index_mode(config) -> tuple[str, str]` — identisch in Task 5b (Definition) und Task 12b (Nutzer).
- `validate_spec_plan(project_root, config, log) -> int` / `MODE = "validate-spec-plan"` / `_handle_validate_spec_plan(ctx)` — analog `se_validate.py` in Task 11.
- Flag-Namen `spec-plan-required`, `spec-plan-traceability`, synthetisch `spec-plan-enabled` (F8) — durchgängig. Conditional-Variable `SPEC_PLAN_WORKFLOW_ENABLED` in Task 2/2b.
- Stage-IDs: `classify`, `specify`, `approve`, `plan`, `implement`, `validate` — konsistent in Task 8/17 und Szenario.
- Pfade `docs/specs`/`docs/plans`/`docs/spikes`, Archiv-Ziel `docs/plans/archive` — konsistent in Task 4/5/5b/13/18.

### (d) Offene Punkte

- **F1** (`systems-engineering`-Schema-Deklaration): bewusst out-of-scope, als separater kurzer Abschnitt dokumentiert; die Issue-Erstellung ist nicht Teil dieses Vorhabens.
- Keine weiteren offenen Punkte — F2–F12 sind vollständig in Tasks zerlegt.

---

## Execution Handoff

Zwei Ausführungswege stehen zur Wahl:

1. **`superpowers:subagent-driven-development` (empfohlen):** Der Orchestrator nimmt diesen Plan als `payload.plan_ref`, dispatcht Task für Task an frische Subagenten und lässt nach jedem Task reviewen. Ownership/Barrieren pro Task über die `Files:`-Blöcke; Recovery über `CheckpointStore`/`BarrierEntry.checkpoint_ref`. Kein Worktree.
2. **`superpowers:executing-plans`:** Ein einzelner Agent arbeitet die Checkbox-Steps sequenziell ab; Review nach jedem Task bleibt Pflicht.

Bevorzugt wird Weg 1, weil die Tasks aufeinander aufbauen (Foundation zuerst) und pro Task genau ein Agent verantwortlich ist.

---

## Branch- und Commit-Strategie

- **Branch:** `feat/spec-plan-workflow` (empfohlen). Der Branch wird **nicht** in diesem Task angelegt und es wird **nichts** committet — dieser Plan ist nur das Dokument.
- **Commits:** Conventional Commits, `<type>: <description>`, max 72 Zeichen erste Zeile, Imperativ, Englisch — je Task ein Commit mit der im Task-Step 5 angegebenen Message.
- **DoD:** `python3 scripts/sync.py --validate`, `python3 scripts/sync.py --check` und `tests/scenarios/run.sh` müssen grün sein; zusätzlich `pytest tests/ -q`.
