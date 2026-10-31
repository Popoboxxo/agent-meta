---
pipeline_stages:
  implement: 8
---

# Test Environments Implementation Plan

> Status: geplant

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox syntax (`- [ ]`) for tracking.

**Goal:** Pro Projekt deklarierbare Test-Umgebungen (`test-environments`, lokal/remote/beides) mit Remote-Freigabeprotokoll in sechs Rollen-Templates, sieben Overrides, Admin-UI und Manager-Rezept bereitstellen.

**Architecture:** Neues lib-Modul `scripts/lib/test_environments.py` validiert (hart, Python), löst auf (Defaults, Fallback-URL) und rendert den Platzhalter-Block `{{TEST_ENVIRONMENT_BLOCK}}` samt Flag `TEST_ENVIRONMENTS_SET`; Bestandsmodule bekommen nur Aufruf- und Registrierungszeilen. Die sechs Basis-Templates tragen den Block nach `</constraints>` in einem `{{#if TEST_ENVIRONMENTS_SET}}`-Gate (unkonfiguriert byte-identisch), extends-Overrides erben ihn, `sharkord-docker` (Standalone) bekommt ihn manuell. Admin-Server (Whitelist + Section-Guard), Admin-UI-Sektion und Manager-Rezept schreiben dasselbe Fragment in `.meta-config/project.yaml`.

**Tech Stack:** Python >= 3.9 (stdlib only), JSON-Schema (draft-07), Markdown-Templates mit `{{...}}`-Platzhaltern, vanilla-JS Admin-UI (`docs/ui/admin-ui.html`), pytest, `tests/scenarios/run.sh`.

**Spec:** docs/specs/2026-10-31-test-environments-spec.md

**Aufwand:** Gesamt L (Spec §21, ca. 28-34 Dateien); Detailschätzung liefert `effort-estimator` (Textverweis, hier nicht berechnet).

**Reihenfolge:** Plan 1 (`docs/plans/2026-10-31-release-checklist-plan.md`) läuft zuerst: `agent-meta-manager` 1.26.0 (Plan 1) -> 1.27.0 (dieser Plan, Task 12); der Satz zu AC-ENV-19 in `docs/RELEASE_GATES.md` entsteht in Task 14 dieses Plans.

## Trace-Anker: spec-id: SPEC-TEST-ENVIRONMENTS-2026-10-31

## Global Constraints

- C1: Stdlib only; Python >= 3.9 (`from __future__ import annotations`, kein `X | Y` zur Laufzeit, kein `match`).
- C2: Provider-Agnostik: Provider-Unterschiede nur über Config-Keys/Capability-Flags (`config/provider-capabilities.yaml`), nie `if provider == "Name"`.
- C3: Leerer Block (kein `test-environments`) => generierte Templates byte-identisch; Mechanik: `{{#if TEST_ENVIRONMENTS_SET}}\n…{{/if}}\n` entfernt inaktive Blöcke samt Zeilenumbruch (`scripts/lib/variables.py:483`).
- C4: Neue lib-Module <= 600 Zeilen (`scripts/lib/test_environments.py`); `config.py` hat 2466 Zeilen, bestehende Module bekommen nur Aufruf-/Registrierungs-/Guard-Zeilen.
- C5: Platzhalter-Registrierung nach `rules/2-platform/agent-meta-conventions.md:105-109`: `_SET`-Muster (`config.py:1442`) bzw. Builder-Aufruf nahe `_build_convention_variables` (`config.py:2293`), `scripts/lib/consistency/placeholders.py` (`_BUILTIN_VARS`), `scripts/lib/standalone.py` (`_CONDITIONAL_FALSE_FLAGS`, Fallback-Block `""`), Doku `docs/guides/features/sync-concept.md` (Tabelle „Auto-injiziert“, :278-287). Das Suffix `_SET` ist in der Whitelist von `strip_inactive_conditional_blocks` (`variables.py:447`) bereits abgedeckt.
- C6: Jeder Bool in einem Enum-Feld (`kind`, `access`, `remote-access`) ist ein harter Fehler „quote the value“; keine implizite Abbildung (`off` -> `False`).
- C7: Sprache: Dokumente Deutsch; Code, Identifier, Commits Englisch.
- C8: Die JSON-Schema-Validierung warnt nur (und nur mit installiertem `jsonschema`); harte Fehler stehen im Python-Validator `validate_test_environments`; unbekannte Keys sind im Validator hart.
- C9: Kein Top-Level-`default` im Schema für `test-environments` (`--fill-defaults` würde es in `project.yaml` schreiben, Issue #1074).
- Secrets: nur als Env-Var-NAME (`token-env`), der auf einen `environments:`-Eintrag mit `secret: true` verweist; Wert kommt per `source .meta-config/env.sh`; keine Secret-Werteingabe in der Admin-UI.
- Nicht im MVP (NZ1/NZ8): keine Hooks, keine `permissions.ask/deny`-Erzeugung. Unverändert bleiben: `scripts/lib/env.py`, `scripts/lib/mcp.py`, `scripts/lib/hooks.py`, `scripts/lib/platform.py`, `config/provider-capabilities.yaml`, `.claude/settings.json`, `.meta-config/secrets.local.yaml`.
- Namensverwechslung `environments:` (Env-Var-Definitionen) vs. `test-environments:` (Ziele) wird in Schema-Description, Doku, Manager und UI gegenseitig dokumentiert (AZ6).
- Commits: Conventional Commits, Englisch, erste Zeile <= 72 Zeichen, Imperativ; pro Task ein Commit mit `git add <Pfade>` + `git commit -m "..."`.
- Testkommando-Konvention: `python3 -m pytest <datei>::<test> --basetemp={{PYTEST_BASETEMP}}` (Wert aus `.meta-config/project.yaml` `variables.TEST_COMMANDS`; Quelle `repo_containment.tmp-sink.system-temp-exception`; kein `/tmp`-Literal, nie ein Basetemp im Arbeitsbaum). An Template-/Config-Tasks zusätzlich `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`.
- Branch: Ausführung auf Feature-Branch `feat/test-environments` (nicht `main`); kein Merge, Push/Tag/Branch nur durch die Rolle `git`; kein `isolation: "worktree"`.

## Review Focus

Fünf Eingaben/Fehlerfälle, die die Spec impliziert, aber nicht ausdrücklich festlegt; jede Zeile wird im besitzenden Task per Test abgesichert.

| # | Eingabe / Fehlerfall | Erwartung | Test im Task |
|---|---|---|---|
| RF1 | `test-environments:` ist `null`/`{}` bzw. kein Mapping (Liste, String, Zahl) | `null`/`{}` = unkonfiguriert (kein Fehler, Block `""`); Nicht-Mapping = harter Fehler `test-environments: expected a mapping, got <typ>` | Task 3 (`test_absent_null_and_empty_block_are_unconfigured`, `test_non_mapping_block_is_hard_error`) |
| RF2 | Umgebungsname ist kein String (YAML-Key `123:`, `true:`, `~:`) oder verletzt das Namensmuster | Fehler `invalid environment name`, kein `TypeError`/Crash | Task 3 (`test_invalid_environment_name`) |
| RF3 | `token-env` verweist auf `environments`-Eintrag mit `secret: "true"` (String), `secret: 1` o. ä., oder `environments` fehlt/ist kein Mapping | Fehler: nur der Bool `True` zählt als `secret: true`; fehlende Definition = `environments entry 'X' not defined`; kein Crash | Task 4 (`test_token_env_requires_secret_true`, `test_environments_not_a_mapping_gives_not_defined_error`) |
| RF4 | `url`/`notes` enthalten `{{`/`}}`, `\|` oder Zeilenumbrüche | `{{`/`}}` = Validator-Fehler `placeholder syntax not allowed` (sonst Sync-Abbruch „Unknown placeholder“ ab 2.1.0); `\|` und Zeilenumbrüche werden im Renderer maskiert (`\|`, Leerzeichen), Tabelle bleibt intakt | Task 3 (`test_placeholder_syntax_rejected`), Task 6 (`test_cells_are_sanitized`) |
| RF5 | Admin-Schreibwege außerhalb des Einzel-Writes: `environments`-Write, der eine `token-env`-Referenz bricht; `test-environments: null` (Sektion löschen); Full-Document-`PUT /api/config/project` | Referenzbruch = HTTP 400, nichts geschrieben; `null` wird akzeptiert (unkonfiguriert); der PUT-Pfad prüft dieselbe Regel; ein bereits ungültiger Altstand blockiert fremde Sektionen nicht | Task 10 (`test_environments_write_breaking_reference_rejected`, `test_null_deletes_section_without_error`, `test_full_document_put_guarded`, `test_unrelated_section_not_blocked_by_preexisting_invalid_config`) |

---

## Abweichungen und Korrekturen gegenüber den Spec-Belegen

Beim Erstellen des Plans per Lesen/Grep geprüft (Pfad/Zeile):

- OF-8 entschieden: `scripts/lib/platform.py:34` `load_platform_config` liefert nur das gemergte Flat-Dict (Defaults + Projekt), keinen getrennten Projekt-Layer. Der Plan nutzt einen eigenen Lesepfad `load_project_platform_vars(project_root)` (liest `.claude/platform-config.yaml` über `platform.CLAUDE_PLATFORM_CONFIG`, flacht mit `platform._flatten_yaml_dict`); `platform.py` bleibt unverändert.
- Registrierung (C5): `_build_convention_variables` (`config.py:2293`) hat kein `project_root`; die Plattform-Fallback-URL braucht es. Der Plan registriert daher über genau eine Aufrufzeile `variables.update(build_test_environment_variables(config, project_root))` in `build_variables` nach `_build_convention_variables` (`config.py:2463`); der `_SET`-Wert wird im neuen Modul nach dem Muster von `config.py:1442` (`"true" if … else "false"`) gebildet.
- `consistency/placeholders.py`: Zeile :263 ist das Ratchet-Set `_UNREGISTERED_BUILDER_RATCHET` („shrink only“, dort darf nichts ergänzt werden). Neue Variablen gehören in `_BUILTIN_VARS` (Nachbarzeile von `RELEASE_CUSTOM_CHECKLIST_BLOCK`, :107).
- Zusätzliche Fixtures, die die Spec nicht nennt, aber der Change auslöst: AC-01-Manifest `tests/fixtures/ac01-baseline/hashes.json` (Versions-Bumps der Templates, Manager), die in `tests/test_opencode_v2_surface.py` eingebetteten Fixture-Tree-Digests und das `slimming-golden` des `agent-meta-manager` (Task 15).
- Block-Sprache: Die Block-Prosa ist Englisch (alle `1-generic`-Templates sind Englisch); die in der Spec deutsch zitierten Marker („URL nicht konfiguriert“, „Wert aus der Shell-Umgebung …“) sind sinngemäß als `URL not configured` bzw. „the value comes from the shell environment …“ umgesetzt. Maschinenlesbare Tokens (`APPROVAL_REQUEST`, `APPROVED`, `STATUS: partial`) bleiben wörtlich. Das Freigabeprotokoll wird nur gerendert, wenn mindestens eine Umgebung `kind: remote|both` hat (bei `kind: local` ist `remote-access` laut §9.4 Regel 5 wirkungslos).
- IC-14 (optionaler Command `commands/1-generic/set-test-environment.md`) wird nicht umgesetzt: er fügte 7 neue Pfade zum AC-01-Manifest hinzu und braucht Doku in `README.md`/`docs/api/slash-commands.md`/`docs/guides/features/commands.md`; Spec §21 führt ihn als optional.
- IC-15 optionale GET-Route `/api/test-environments` entfällt: die UI liest über `loadProject()` wie `viewProjectEnvironments`.
- `.claude/skills/{conventions,sync-interface,architecture}` und `hacs-developer.md:31` / `hacs-integration-development.md:15` (Spec §15, Status N): Grep zeigt keine Platzhalter-Tabellen in den Skills; Platzhalter-Listen existieren nur in `docs/guides/features/sync-concept.md` und `rules/2-platform/agent-meta-conventions.md`. Keine Änderung an den Skills und kein Verweis aus den hacs-Dateien (Spec: „ggf.“).
- Admin-UI: `/project/environments` hat heute keinen `routeMap`-/Help-Eintrag (`docs/ui/admin-ui.html:10961ff`); für die neue Sektion entstehen routeMap-Eintrag und Help-Block (Check `scripts/lib/consistency/docs.py:47`).
- Szenario-IDs: höchste vorhandene ID ist 87; der Plan nummeriert 88-90. Hat Plan 1 diese IDs schon belegt, nimmt der Ausführende die nächsten drei freien IDs (Task 13).
- Verifizierte Zeilenbelege: `config.py` 393-396 (Validator-Aufrufe in `_validate_config`, Einfügepunkt nach :396), :1442, :2293, :2463; `variables.py` :431-451 / :483; `standalone.py` :110-121 / :122ff / :138; `admin-server.py` :233-252, :3801, :3887-3946 (`_route_put_config`), :5176-5200; `admin-ui.html` :1644, :8632, :10868, :10961; `platform-configs/hacs.defaults.yaml:55` (`dev_instance_url: ""`) und `homeassistant.defaults.yaml:48` (`ha_url` nicht leer); Template-`</constraints>`-Zeilen: developer 147, tester 134, docker 118, devops-engineer 192, e2e-tester 144, test-executor 125; Override-Anker sind Tag-Anker (`<persona>`, `<workflow>`, `<context>`, `<constraints>`, `<output_contract>`), per Grep verifiziert; die Liste der 7 Overrides per Grep nach `based-on:`/`extends:` in `agents/2-platform` bestätigt.

## Task-Übersicht

| # | Step | Agent | Depends on | Acceptance criteria |
|---|---|---|---|---|
| 0 | Feature-Branch anlegen | git | — | `git branch --show-current` = `feat/test-environments` |
| 1 | Render-Baseline-Harness (5 Plattform-Varianten, vor jeder Template-Änderung) | tester | 0 | `test_unset_render_matches_baseline` PASS auf unveränderten Templates |
| 2 | Schema-Key `test-environments` | developer | 1 | `tests/test_test_environments_schema.py` PASS, `--validate` ohne Befund |
| 3 | Validator Teil A: Struktur, Enums, Bool, url/notes, Warnungen | developer | 2 | `tests/test_test_environments_lib.py` (Teil A) PASS |
| 4 | Validator Teil B: `token-env`-Referenz, harter Abbruch im Config-Load | developer | 3 | Teil-B-Tests PASS, `load_config` bricht bei ungültigem Block mit rc 1 ab |
| 5 | Resolver + Fallback-URL | developer | 4 | Resolver-Tests PASS (Präzedenz HACS > HA, Default löst nichts aus) |
| 6 | Renderer `render_test_environment_block` | developer | 5 | `tests/test_test_environments_render_block.py` PASS, Modul <= 600 Zeilen |
| 7 | Platzhalter-Registrierung (config, placeholders, standalone, sync-concept) | developer | 6 | `tests/test_test_environments_consistency.py` PASS |
| 8 | Sechs Basis-Templates + Versionen + Render-/Secret-Tests | developer | 7 | gerenderte Agenten enthalten Block; unset == Baseline |
| 9 | Sieben Overrides nachziehen (`sharkord-docker` manuell) | developer | 8 | alle 7 rendern, Anker lösen auf, `based-on` aktuell |
| 10 | Admin-Server: Whitelist + Section-Guard (+ PUT-Pfad) | developer | 7 | `tests/test_admin_ui_test_environments_section.py` (Server-Teil) PASS |
| 11 | Admin-UI-Sektion + Help | developer | 10 | UI-Tests PASS, `check_ui_help_mappings` ohne Befund |
| 12 | Manager-Rezept + §3-Bestätigung (1.27.0) | developer | 10 | Manager-Tests PASS inkl. Parität |
| 13 | Szenarien test-env-local / -remote-ask / -unset | tester | 9, 12 | `tests/scenarios/run.sh 88 89 90` PASS |
| 14 | Doku, Beispiel-Config, CHANGELOG, RELEASE_GATES-Satz | documenter | 11, 12 | `tests/test_test_environments_docs.py` PASS |
| 15 | Baselines/Goldens neu pinnen (AC-01, Digests, Manager-Golden) | tester | 9, 12, 13, 14 | AC-01-, Opencode-, Slimming-Tests PASS |
| 16 | Real-Sync der eigenen Artefakte + Gesamtlauf | developer | 15 | `pytest tests/` und `tests/scenarios/run.sh` grün |
| 17 | Self-Review der gesamten Änderung | code-reviewer | 16 | Review-Checkliste ohne offenen Befund |
| 18 | PR-Vorbereitung (kein Merge) | git | 17 | Draft-PR gegen `main` angelegt, nicht gemergt |

## File Structure

- Create: `scripts/lib/test_environments.py` — Validator, Resolver, Renderer, Builder (<= 600 Zeilen)
- Modify: `config/project-config.schema.json` — Key `test-environments` (Zusatz, kein Top-Level-`default`)
- Modify: `scripts/lib/config.py` — Import + Validator-Aufruf nach :396 + Builder-Aufruf nach :2463
- Modify: `scripts/lib/consistency/placeholders.py` — `_BUILTIN_VARS` um zwei Namen
- Modify: `scripts/lib/standalone.py` — `_CONDITIONAL_FALSE_FLAGS` + Fallback `""`
- Modify: `agents/1-generic/{tester,e2e-tester,developer,docker,devops-engineer,test-executor}.md` — Gate-Block + minor-Bump
- Modify: `agents/2-platform/{homeassistant-developer,sharkord-developer,hacs-developer,agent-meta-developer,hacs-tester,hacs-devops-engineer,sharkord-docker}.md` — `based-on`/`version`, `sharkord-docker` Block manuell
- Modify: `agents/1-generic/agent-meta-manager.md` — Rezept + §3-Zeile, Version 1.27.0
- Modify: `scripts/admin-server.py` — Whitelist + Section-Guard + PUT-Pfad
- Modify: `docs/ui/admin-ui.html`, `docs/api/admin-ui-reference.md` — Sektion, Nav, Router, routeMap, Help
- Create: `tests/test_test_environments_{schema,lib,resolver,render_block,render,secrets_via_render,consistency,docs,manager_recipe}.py`, `tests/test_admin_ui_test_environments_section.py`, `tests/_te_admin_helpers.py`, `tests/fixtures/test-env-baseline/hashes.json`
- Create: `tests/scenarios/configs/{88,89,90}-*.project.yaml`, `tests/scenarios/asserts/{88,89,90}-*.sh`; Modify: `tests/scenarios/registry.md`
- Create: `docs/guides/features/test-environments.md`; Modify: `docs/guides/features/sync-concept.md`, `howto/configs/project.yaml.example`, `CHANGELOG.md`, `docs/RELEASE_GATES.md`
- Modify (Rebaseline): `tests/fixtures/ac01-baseline/hashes.json`, `tests/test_ac01_render_identity.py` (Log), `tests/test_opencode_v2_surface.py` (Digests), `tests/fixtures/slimming-golden/agent-meta-manager.md`, `tests/test_template_slimming_equivalence.py` (Log)

---

### Task 0: Feature-Branch anlegen

**Agent:** git
**Files:**
- Modify: `.git` (nur Branch-Ref `feat/test-environments`, kein Dateiinhalt)

**Interfaces:** Produces: Branch `feat/test-environments` ab `main`-Stand nach Plan 1. Consumes: sauberer Stand von `main`.

- [ ] **Step 1: Stand prüfen.** `git status --short` zeigt nur die bereits vorhandenen Hash-Dateien (`.meta-config/context-hashes.json`, `.meta-config/generated-file-hashes.json`) oder nichts; `git log -1 --oneline` zeigt den Merge von Plan 1 (Release-Checkliste) oder dokumentiert dessen Fehlen (dann STOP: Plan 2 läuft nach Plan 1, Spec R8).
- [ ] **Step 2: Branch anlegen.** `git switch -c feat/test-environments` (kein Commit in diesem Task).
- [ ] **Step 3: Verifizieren.** `git branch --show-current` => `feat/test-environments`; `grep -n '^version' agents/1-generic/agent-meta-manager.md` => `version: "1.26.0"` (Vorbedingung für Task 12).

---

### Task 1: Render-Baseline-Harness vor jeder Template-Änderung

**Agent:** tester
**Depends on:** 0
**Files:**
- Create: `tests/test_test_environments_render.py` (Helfer + Baseline-Test; später in Task 8/9 erweitert)
- Create: `tests/fixtures/test-env-baseline/hashes.json`

**Interfaces:** Produces — in `tests/test_test_environments_render.py`:
`_sync_project(root: Path, platforms: Sequence[str] = (), extra_yaml: str = "", extra_env: Optional[dict] = None) -> Path`,
`_role_of(stem: str) -> Optional[str]` (Rolle per längstem Suffix aus `("developer","tester","e2e-tester","docker","devops-engineer","test-executor")`),
`_role_texts(project: Path) -> Dict[str, str]` (Stem -> Text aller `.claude/agents/*.md`, die einer der sechs Rollen zugeordnet werden),
`_normalized_hash(text: str) -> str` (CRLF -> LF, Zeilen `version:`/`based-on:`/`model:` entfernt, Projektpfad -> `<ROOT>`, sha256),
`_matrix_hashes(root: Path) -> Dict[str, str]` (Schlüssel `"<label>/<stem>"` über `PLATFORM_MATRIX`),
`PLATFORM_MATRIX = (("base", ()), ("homeassistant", ("homeassistant",)), ("sharkord", ("sharkord",)), ("hacs", ("hacs",)), ("agent-meta", ("agent-meta",)))`,
CLI `python3 tests/test_test_environments_render.py --capture-baseline`.
Consumes: `scripts/sync.py --config <yaml> --init` (wie `tests/test_ac01_render_identity.py::_run_sync`).

- [ ] **Step 1: Failing Test schreiben.** `_sync_project` schreibt `.meta-config/project.yaml` aus: `agent-meta-version: "2.0.0-beta.5"`, `ai-providers: [Claude]`, `dod-preset: rapid-prototyping`, optional `platforms:`, `roles:` = die sechs Rollen, `project: {name: te, prefix: te, short: te}`, `variables: {PROJECT_NAME: te, AGENT_META_REPO: example/agent-meta}`, danach `extra_yaml` (Top-Level-Keys ab Spalte 0), `git init -q`, `python3 scripts/sync.py --config … --init` (rc 0 asserten). Tests:
  ```python
  BASELINE = Path(__file__).parent / "fixtures" / "test-env-baseline" / "hashes.json"
  OVERRIDE_COVERAGE = {"homeassistant": {"developer"}, "sharkord": {"developer", "docker"},
                       "hacs": {"developer", "tester", "devops-engineer"}, "agent-meta": {"developer"}}

  def test_unset_render_matches_baseline(tmp_path_factory):
      baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
      assert _matrix_hashes(tmp_path_factory.mktemp("teb")) == baseline

  def test_matrix_exercises_every_override(tmp_path_factory):
      current = _matrix_hashes(tmp_path_factory.mktemp("teo"))
      for label, roles in OVERRIDE_COVERAGE.items():
          for role in roles:
              stems = [k.split("/", 1)[1] for k in current if k.startswith(label + "/") and _role_of(k.split("/", 1)[1]) == role]
              assert stems, (label, role)
              assert any(current[f"{label}/{s}"] != current.get(f"base/{s}") for s in stems), (label, role)
  ```
- [ ] **Step 2: Run, erwartet FAIL.** `python3 -m pytest tests/test_test_environments_render.py::test_unset_render_matches_baseline --basetemp={{PYTEST_BASETEMP}}` => FAIL (`FileNotFoundError` auf `hashes.json`).
- [ ] **Step 3: Baseline auf unveränderten Templates erfassen.** Vorbedingung: `git diff --quiet HEAD -- agents/1-generic/tester.md agents/1-generic/e2e-tester.md agents/1-generic/developer.md agents/1-generic/docker.md agents/1-generic/devops-engineer.md agents/1-generic/test-executor.md agents/2-platform` endet mit rc 0. Dann `python3 tests/test_test_environments_render.py --capture-baseline` (schreibt `tests/fixtures/test-env-baseline/hashes.json`, sortierte Keys, Scratch-Verzeichnis unter `{{PYTEST_BASETEMP}}`).
- [ ] **Step 4: Run, erwartet PASS.** Beide Tests aus Step 1 mit `--basetemp={{PYTEST_BASETEMP}}`. Schlägt `test_matrix_exercises_every_override` fehl, ist eine Plattform-Variante wirkungslos (Dateinamen/`platforms:` prüfen) — vor dem Commit beheben.
- [ ] **Step 5: Commit.** `git add tests/test_test_environments_render.py tests/fixtures/test-env-baseline/hashes.json` und `git commit -m "test: add test-environments render baseline harness"`.

---

### Task 2: Schema-Key `test-environments`

**Agent:** developer
**Depends on:** 1
**Files:**
- Modify: `config/project-config.schema.json` (neuer Eintrag in `properties`, direkt vor `"repo_containment"`, ca. :2555)
- Create: `tests/test_test_environments_schema.py`

**Interfaces:** Produces: `properties."test-environments"` (Schema §9.2, kein `default`). Consumes: nichts.

- [ ] **Step 1: Failing Tests schreiben** (Muster `tests/test_auto_commit_schema.py`, `_cfg(envs)` baut `{"project": {...}, "ai-providers": ["Claude"], "roles": [...], "test-environments": envs}`):
  ```python
  def test_schema_has_block_without_toplevel_default():
      prop = _schema()["properties"]["test-environments"]
      assert "default" not in prop
      assert prop["propertyNames"] == {"pattern": "^[a-z0-9][a-z0-9-]*$"}
      item = prop["additionalProperties"]
      assert item["additionalProperties"] is False
      assert item["properties"]["kind"]["enum"] == ["local", "remote", "both"]
      assert item["properties"]["access"]["enum"] == ["read", "deploy"]
      assert item["properties"]["remote-access"]["enum"] == ["deny", "ask", "allow"]
      assert item["properties"]["token-env"]["pattern"] == "^[A-Z][A-Z0-9_]*$"
      assert item["properties"]["url"]["minLength"] == 1
      assert "environments" in prop["description"] and "secret: true" in prop["description"]   # AC-ENV-17

  def test_spec_example_validates():
      jsonschema.validate(_cfg({"ha-dev": {"kind": "both", "url": "http://ha-dev.lan:8123", "token-env": "HA_DEV_TOKEN",
                                           "access": "deploy", "remote-access": "ask", "notes": "x"},
                                "sharkord-local": {"kind": "local", "notes": "y"}}), _schema())

  @pytest.mark.parametrize("bad", [{"kind": "remoteish"}, {"access": "write"}, {"remote-access": "maybe"},
                                   {"remote-access": False}, {"token-env": "lowercase"}, {"colour": "red"}, {"url": ""}])
  def test_invalid_entry_rejected(bad):
      with pytest.raises(jsonschema.ValidationError):
          jsonschema.validate(_cfg({"a": bad}), _schema())

  def test_invalid_name_rejected():
      with pytest.raises(jsonschema.ValidationError):
          jsonschema.validate(_cfg({"Bad_Name": {}}), _schema())
  ```
- [ ] **Step 2: Run, erwartet FAIL.** `python3 -m pytest tests/test_test_environments_schema.py --basetemp={{PYTEST_BASETEMP}}` => `KeyError: 'test-environments'`.
- [ ] **Step 3: Schema ergänzen.** Objekt wörtlich aus Spec §9.2 (`type: object`, Description mit Satz „NOT to be confused with 'environments' (env-var definitions); token-env must reference an 'environments' entry with secret: true.“, `propertyNames.pattern`, `additionalProperties` mit `properties` `kind`/`url`/`token-env`/`access`/`remote-access`/`notes`, `additionalProperties: false`); `notes` = `{"type": "string"}`; kein `default` auf Top-Level.
- [ ] **Step 4: Run, erwartet PASS.** Tests aus Step 1; danach `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate` (kein neuer Befund).
- [ ] **Step 5: Commit.** `git add config/project-config.schema.json tests/test_test_environments_schema.py` und `git commit -m "feat: add test-environments schema block"`.

---

### Task 3: Validator Teil A — Struktur, Enums, Bool, url/notes, Warnungen

**Agent:** developer
**Depends on:** 2
**Files:**
- Create: `scripts/lib/test_environments.py` (Konstanten + `check_test_environments`)
- Create: `tests/test_test_environments_lib.py`

**Interfaces:** Produces — `scripts/lib/test_environments.py`:
`KINDS = ("local","remote","both")`, `ACCESS_LEVELS = ("read","deploy")`, `REMOTE_ACCESS = ("deny","ask","allow")`,
`DEFAULTS = {"kind": "local", "access": "read", "remote-access": "ask"}`,
`NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")`, `TOKEN_ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")`,
`check_test_environments(config: dict) -> tuple[list[str], list[str]]` (Rückgabe `(errors, warnings)`; Fehlerformat `test-environments.<name>.<key>: <Meldung>`, Block-Ebene `test-environments: <Meldung>`).
Consumes: nur Stdlib.

- [ ] **Step 1: Failing Tests schreiben** (`sys.path.insert(0, scripts)`; `SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"`; `_cfg(envs, **extra) = {"test-environments": envs, **extra}`):
  ```python
  def test_absent_null_and_empty_block_are_unconfigured():                       # RF1
      for cfg in ({}, {"test-environments": None}, {"test-environments": {}}):
          assert check_test_environments(cfg) == ([], [])

  @pytest.mark.parametrize("bad", [[], ["a"], "text", 3])
  def test_non_mapping_block_is_hard_error(bad):                                  # RF1
      errors, _ = check_test_environments({"test-environments": bad})
      assert errors == [f"test-environments: expected a mapping, got {type(bad).__name__}"]

  @pytest.mark.parametrize("name", ["Bad", "-x", "a_b", "", 123, True, None])
  def test_invalid_environment_name(name):                                        # RF2
      errors, _ = check_test_environments(_cfg({name: {}}))
      assert len(errors) == 1 and "invalid environment name" in errors[0]

  def test_entry_must_be_mapping():
      assert check_test_environments(_cfg({"a": "x"}))[0] == ["test-environments.a: expected a mapping, got str"]

  def test_unknown_key_is_error():
      assert check_test_environments(_cfg({"a": {"colour": "red"}}))[0] == ["test-environments.a.colour: unknown key"]

  @pytest.mark.parametrize("key,bad", [("kind", "remoteish"), ("access", "write"), ("remote-access", "maybe")])
  def test_invalid_enum_value(key, bad):
      err = check_test_environments(_cfg({"a": {key: bad}}))[0][0]
      assert f"test-environments.a.{key}" in err and "invalid value" in err

  @pytest.mark.parametrize("key", ["kind", "access", "remote-access"])
  @pytest.mark.parametrize("val", [True, False])
  def test_bool_in_enum_field_is_error_quote_the_value(key, val):
      assert "quote the value" in check_test_environments(_cfg({"a": {key: val}}))[0][0]

  def test_yaml_1_1_off_is_caught():
      cfg = yaml.safe_load("test-environments:\n  a:\n    kind: remote\n    remote-access: off\n")
      assert any("quote the value" in e for e in check_test_environments(cfg)[0])

  @pytest.mark.parametrize("url", ["http://u:p@host/x", "https://user@host", "https://:pw@host"])
  def test_url_userinfo_is_error(url):
      assert "url must not contain userinfo" in check_test_environments(_cfg({"a": {"kind": "remote", "url": url}}))[0][0]

  @pytest.mark.parametrize("url", ["", 5])
  def test_url_empty_or_non_string_is_error(url):
      assert "url must be a non-empty string" in check_test_environments(_cfg({"a": {"url": url}}))[0][0]

  @pytest.mark.parametrize("key,val", [("url", "http://h/{{X}}"), ("notes", "see {{TOKEN}}"), ("notes", "a }} b")])
  def test_placeholder_syntax_rejected(key, val):                                 # RF4
      assert "placeholder syntax not allowed" in check_test_environments(_cfg({"a": {"kind": "remote", key: val}}))[0][0]

  def test_notes_must_be_string():
      assert "notes must be a string" in check_test_environments(_cfg({"a": {"notes": 5}}))[0][0]

  def test_defaults_alone_have_no_findings():
      assert check_test_environments(_cfg({"a": {}})) == ([], [])

  def test_warnings_for_ineffective_or_conflicting_settings():
      _, w = check_test_environments(_cfg({"a": {"kind": "local", "url": "http://x"}}))
      assert w == ["test-environments.a: kind: local ignores url"]
      _, w = check_test_environments(_cfg({"a": {"kind": "local", "remote-access": "ask"}}))
      assert w == ["test-environments.a: kind: local ignores remote-access"]
      _, w = check_test_environments(_cfg({"a": {"kind": "local", "access": "deploy"}}))
      assert w == ["test-environments.a: access: deploy has no effect for kind: local"]
      _, w = check_test_environments(_cfg({"a": {"kind": "remote", "access": "deploy", "remote-access": "deny"}}))
      assert w == ["test-environments.a: access: deploy conflicts with remote-access: deny (deny wins)"]

  def _root_imports(tree):
      roots = set()
      for n in ast.walk(tree):
          if isinstance(n, ast.Import):
              roots |= {a.name.split(".")[0] for a in n.names}
          elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
              roots.add(n.module.split(".")[0])
      return roots

  def test_module_budget_and_constraints():                                        # AC-ENV-18, AC-ENV-11
      text = (SCRIPTS / "lib" / "test_environments.py").read_text(encoding="utf-8")
      assert text.count("\n") <= 600 and "provider ==" not in text and "provider==" not in text
      assert _root_imports(ast.parse(text)) <= {"__future__", "re", "pathlib", "typing", "sys", "logging", "urllib"}
  ```
- [ ] **Step 2: Run, erwartet FAIL.** `python3 -m pytest tests/test_test_environments_lib.py --basetemp={{PYTEST_BASETEMP}}` => `ModuleNotFoundError: lib.test_environments`.
- [ ] **Step 3: Implementieren** in `scripts/lib/test_environments.py` (Modul-Docstring mit Namensabgrenzung `environments` vs. `test-environments`): Konstanten wie oben; `check_test_environments(config)`. Regeln (Spec §9.4): fehlender/`None`/leerer Block = `([], [])`; Nicht-Mapping = Fehler `test-environments: expected a mapping, got <typname>`; Namen nicht-String oder nicht `NAME_RE` = `test-environments: invalid environment name <name!r> (expected ^[a-z0-9][a-z0-9-]*$)`; Eintrag kein Mapping; unbekannter Key = `<pfad>.<key>: unknown key`; Enum-Felder: `bool` zuerst prüfen (`… must be a quoted string, quote the value (got bool <v>)`), danach Enum (`invalid value <v!r> (allowed: …)`); `url`: nicht-leerer String sonst `url must be a non-empty string`, Userinfo per `urllib.parse.urlsplit(url).netloc` enthält `@` => `url must not contain userinfo`; `url`/`notes` mit `{{` oder `}}` => `placeholder syntax not allowed`; `notes` kein String => `notes must be a string`; Warnungen genau mit den Texten aus dem Test. Iteration über `sorted(names, key=str)`. Der `token-env`-Zweig kommt in Task 4.
- [ ] **Step 4: Run, erwartet PASS.** Wie Step 2.
- [ ] **Step 5: Commit.** `git add scripts/lib/test_environments.py tests/test_test_environments_lib.py` und `git commit -m "feat: add test-environments structure validator"`.

---

### Task 4: Validator Teil B — `token-env`-Referenz, harter Abbruch im Config-Load

**Agent:** developer
**Depends on:** 3
**Files:**
- Modify: `scripts/lib/test_environments.py` (token-env-Regeln, `collect_test_environment_errors`, `validate_test_environments`)
- Modify: `scripts/lib/config.py` (Import + eine Aufrufzeile nach :396)
- Modify: `tests/test_test_environments_lib.py`

**Interfaces:** Produces: `collect_test_environment_errors(config: dict) -> list[str]` (nur Fehler, nicht-exitend), `validate_test_environments(config: dict, config_path: Path) -> None` (druckt `ERROR: <config_path>: <Fehler>` auf stderr und `sys.exit(1)`; Warnungen als `WARN: <config_path>: <Text>` auf stderr, kein Exit). Consumes: `check_test_environments` (Task 3), `config["environments"]`.

- [ ] **Step 1: Failing Tests ergänzen:**
  ```python
  ENVS = {"HA_DEV_TOKEN": {"description": "t", "secret": True}}

  def test_token_env_valid_reference():
      assert check_test_environments(_cfg({"a": {"kind": "remote", "token-env": "HA_DEV_TOKEN"}}, environments=ENVS)) == ([], [])

  @pytest.mark.parametrize("val", ["lower", "1ABC", "has space", "secret-value-123", "ghp_x/y", 5])
  def test_token_env_must_be_a_name(val):
      assert "expected env var NAME, not a value" in check_test_environments(_cfg({"a": {"token-env": val}}, environments=ENVS))[0][0]

  def test_token_env_not_defined():
      assert "environments entry 'HA_DEV_TOKEN' not defined" in check_test_environments(_cfg({"a": {"token-env": "HA_DEV_TOKEN"}}))[0][0]

  @pytest.mark.parametrize("envs", [None, [], "x"])                                # RF3
  def test_environments_not_a_mapping_gives_not_defined_error(envs):
      assert "not defined" in check_test_environments(_cfg({"a": {"token-env": "HA_DEV_TOKEN"}}, environments=envs))[0][0]

  @pytest.mark.parametrize("secret", [False, "true", "yes", 1, None])             # RF3
  def test_token_env_requires_secret_true(secret):
      envs = {"HA_DEV_TOKEN": {"description": "t", "secret": secret}}
      assert "must have secret: true" in check_test_environments(_cfg({"a": {"token-env": "HA_DEV_TOKEN"}}, environments=envs))[0][0]

  def test_referenced_entry_with_default_warns():                                  # CA12, NZ3
      envs = {"HA_DEV_TOKEN": {"secret": True, "default": "abc"}}
      errors, warnings = check_test_environments(_cfg({"a": {"token-env": "HA_DEV_TOKEN"}}, environments=envs))
      assert errors == [] and len(warnings) == 1 and "default" in warnings[0] and "HA_DEV_TOKEN" in warnings[0]

  def test_referenced_entry_with_empty_default_does_not_warn():
      envs = {"HA_DEV_TOKEN": {"secret": True, "default": ""}}
      assert check_test_environments(_cfg({"a": {"token-env": "HA_DEV_TOKEN"}}, environments=envs)) == ([], [])

  def test_collect_returns_errors_only_and_never_exits():
      assert collect_test_environment_errors(_cfg({"a": {"kind": "x"}})) != []
      assert collect_test_environment_errors({}) == []

  def test_validate_exits_with_path_message(tmp_path, capsys):                     # AC-ENV-2
      with pytest.raises(SystemExit) as exc:
          validate_test_environments(_cfg({"a": {"kind": "x"}}), tmp_path / "project.yaml")
      err = capsys.readouterr().err
      assert exc.value.code == 1 and "ERROR:" in err and "test-environments.a.kind" in err and str(tmp_path / "project.yaml") in err

  def test_validate_prints_warnings_without_exit(tmp_path, capsys):
      validate_test_environments(_cfg({"a": {"kind": "local", "url": "http://x"}}), tmp_path / "project.yaml")
      assert "WARN:" in capsys.readouterr().err

  def test_load_config_aborts_on_invalid_block(tmp_path):
      p = tmp_path / ".meta-config" / "project.yaml"; p.parent.mkdir()
      p.write_text('agent-meta-version: "2.0.0-beta.5"\nai-providers:\n- Claude\ndod-preset: rapid-prototyping\n'
                   'test-environments:\n  a:\n    kind: remote\n    remote-access: off\n', encoding="utf-8")
      with pytest.raises(SystemExit):
          load_config(p)
  ```
- [ ] **Step 2: Run, erwartet FAIL.** `python3 -m pytest tests/test_test_environments_lib.py --basetemp={{PYTEST_BASETEMP}}` => ImportError/AssertionError für die neuen Funktionen und Regeln.
- [ ] **Step 3: Implementieren.** `token-env`-Regeln in `check_test_environments` (Spec §9.4 Regel 3): String + `TOKEN_ENV_RE` sonst `expected env var NAME, not a value`; `environments = config.get("environments")`; kein Mapping oder Name fehlt => `environments entry '<NAME>' not defined`; Eintrag kein Mapping oder `entry.get("secret") is not True` => `environments entry '<NAME>' must have secret: true`; nicht-leerer `default` (`str(default).strip()`) => Warnung `environments entry '<NAME>' has a non-empty default (secret value in project.yaml)`. `collect_test_environment_errors` = erste Komponente. `validate_test_environments` wie oben. In `scripts/lib/config.py`: Import `from .test_environments import validate_test_environments` und direkt nach `_validate_subagent_permissions(config, config_path)` (:396) die Zeile `validate_test_environments(config, config_path)`.
- [ ] **Step 4: Run, erwartet PASS.** Wie Step 2; zusätzlich `python3 -m pytest tests/test_conventions_migration_invariant.py --basetemp={{PYTEST_BASETEMP}}` (Config-Load unverändert grün).
- [ ] **Step 5: Commit.** `git add scripts/lib/test_environments.py scripts/lib/config.py tests/test_test_environments_lib.py` und `git commit -m "feat: validate token-env references and hard-fail on errors"`.

---

### Task 5: Resolver und Fallback-URL

**Agent:** developer
**Depends on:** 4
**Files:**
- Modify: `scripts/lib/test_environments.py`
- Create: `tests/test_test_environments_resolver.py`

**Interfaces:** Produces: `load_project_platform_vars(project_root: Path) -> dict` (flaches Dict `platform.<name>.<key>` nur aus `.claude/platform-config.yaml`; fehlend/kaputt => `{}`), `resolve_test_environments(config: dict, platform_project_vars: Optional[dict]) -> dict[str, dict]` (je Umgebung Schlüssel `kind`, `url` (str oder `None`), `url_source` (`"config"`, `"platform.hacs.dev_instance_url"`, `"platform.homeassistant.ha_url"` oder `""`), `token-env` (str oder `None`), `access`, `remote-access`, `notes` (`""` wenn leer); nie Exception/Exit, kaputte Config => `{}` plus `SyncLog().warning`). Consumes: `check_test_environments`, `platform._flatten_yaml_dict`, `platform.CLAUDE_PLATFORM_CONFIG`, `io.load_yaml_file(path, on_error="default", default={})`.

- [ ] **Step 1: Failing Tests schreiben:**
  ```python
  HACS, HA = "platform.hacs.dev_instance_url", "platform.homeassistant.ha_url"

  def test_defaults_resolve():                                                     # AC-ENV-3
      assert resolve_test_environments(_cfg({"a": {}}), {})["a"] == {
          "kind": "local", "url": None, "url_source": "", "token-env": None,
          "access": "read", "remote-access": "ask", "notes": ""}

  def test_invalid_or_odd_input_yields_empty_and_never_raises():
      assert resolve_test_environments(_cfg({"a": {"kind": "x"}}), {}) == {}
      assert resolve_test_environments({"test-environments": ["x"]}, {}) == {}
      assert resolve_test_environments({}, None) == {}

  def test_fallback_prefers_hacs_over_ha():                                        # AC-ENV-4
      r = resolve_test_environments(_cfg({"ha": {"kind": "remote"}}), {HACS: "http://dev:8123", HA: "http://ha:8123"})
      assert (r["ha"]["url"], r["ha"]["url_source"]) == ("http://dev:8123", HACS)

  def test_fallback_ha_only():
      r = resolve_test_environments(_cfg({"ha": {"kind": "both"}}), {HA: "http://ha:8123"})
      assert (r["ha"]["url"], r["ha"]["url_source"]) == ("http://ha:8123", HA)

  def test_explicit_url_wins():
      r = resolve_test_environments(_cfg({"ha": {"kind": "remote", "url": "http://own"}}), {HACS: "http://dev:8123"})
      assert (r["ha"]["url"], r["ha"]["url_source"]) == ("http://own", "config")

  def test_platform_default_alone_triggers_nothing():
      r = resolve_test_environments(_cfg({"ha": {"kind": "remote"}}), {})   # Defaults sind nie Teil der Projektvariablen
      assert (r["ha"]["url"], r["ha"]["url_source"]) == (None, "")

  def test_empty_platform_value_is_ignored():
      assert resolve_test_environments(_cfg({"ha": {"kind": "remote"}}), {HACS: ""})["ha"]["url"] is None

  def test_two_urlless_remote_envs_get_no_fallback():
      r = resolve_test_environments(_cfg({"a": {"kind": "remote"}, "b": {"kind": "both"}}), {HACS: "http://dev:8123"})
      assert r["a"]["url"] is None and r["b"]["url"] is None

  def test_local_env_does_not_count_and_gets_no_fallback():
      r = resolve_test_environments(_cfg({"loc": {}, "ha": {"kind": "remote"}}), {HACS: "http://dev:8123"})
      assert r["loc"]["url"] is None and r["ha"]["url"] == "http://dev:8123"

  def test_load_project_platform_vars_reads_only_project_layer(tmp_path):
      (tmp_path / ".claude").mkdir()
      (tmp_path / ".claude" / "platform-config.yaml").write_text(
          "platform:\n  hacs:\n    dev_instance_url: http://dev:8123\n  homeassistant:\n    notify_group: all\n", encoding="utf-8")
      assert load_project_platform_vars(tmp_path) == {HACS: "http://dev:8123", "platform.homeassistant.notify_group": "all"}

  def test_load_project_platform_vars_missing_or_broken_file(tmp_path):
      assert load_project_platform_vars(tmp_path) == {}
      (tmp_path / ".claude").mkdir()
      (tmp_path / ".claude" / "platform-config.yaml").write_text("platform: [unclosed", encoding="utf-8")
      assert load_project_platform_vars(tmp_path) == {}
  ```
- [ ] **Step 2: Run, erwartet FAIL.** `python3 -m pytest tests/test_test_environments_resolver.py --basetemp={{PYTEST_BASETEMP}}` => ImportError.
- [ ] **Step 3: Implementieren** gemäß Spec §10.2: Fallback nur wenn (a) genau eine Umgebung mit `kind` in `("remote","both")` keine `url` hat, (b) ein Projekt-Plattformwert (nicht-leerer String) existiert, (c) Präzedenz `platform.hacs.dev_instance_url` > `platform.homeassistant.ha_url`. Konstante `FALLBACK_PLATFORM_KEYS = (HACS-Key, HA-Key)`. Kein Provider-Bezug.
- [ ] **Step 4: Run, erwartet PASS.** Wie Step 2.
- [ ] **Step 5: Commit.** `git add scripts/lib/test_environments.py tests/test_test_environments_resolver.py` und `git commit -m "feat: resolve test environments with platform URL fallback"`.

---

### Task 6: Renderer `render_test_environment_block`

**Agent:** developer
**Depends on:** 5
**Files:**
- Modify: `scripts/lib/test_environments.py`
- Create: `tests/test_test_environments_render_block.py`

**Interfaces:** Produces: `render_test_environment_block(resolved: dict) -> str` (`""` bei `{}`; sonst Markdown ohne rollenspezifische Logik und ohne abschließenden Zeilenumbruch; Umgebungen alphabetisch nach Name). Consumes: Rückgabe von `resolve_test_environments` (Task 5).

Textbausteine (wörtlich in Tests und Implementierung):
- Überschrift `## Test environments`; Abgrenzung: ``- `environments:` defines environment variables; `test-environments:` defines targets. `token-env` only references an `environments:` entry.``
- Tabellenkopf `| Name | kind | URL / source | access | remote-access | notes |` + `|---|---|---|---|---|---|`. Zeile: URL-Zelle = `url`, bei Plattform-Fallback `url (from <url_source>)`, ohne URL `URL not configured` (remote/both) bzw. `—` (local); `access`/`remote-access` bei `kind: local` = `—`; leere Notes `—`; Zellen: `\n`/`\r\n` -> Leerzeichen, `|` -> `\|`.
- Immer: `Access approval is a prompt convention (convention boundary), not a technical barrier.`
- `kind` (nur wenn vorkommend): local `- **local:** local tests and dev stack only; no remote access.`; remote `- **remote:** the remote environment is the test target; access only as allowed by remote-access and access.`; both `- **both:** test locally first, then the remote environment only after approval as required by its remote-access.`
- `access` (nur für remote/both-Umgebungen): read `- **access read:** read/query only (status, logs, config check); never write or deploy.`; deploy `- **access deploy:** may also roll out or change things, only together with remote-access ask or allow (deny always wins).`
- `remote-access` (nur für remote/both-Umgebungen): deny `- **remote-access deny:** never contact the environment (ssh, scp, curl, \`docker -H\`, deploy); if the task needs it, report it to main_chat.`; allow `- **remote-access allow:** access is permitted within the access level; still report every deploy in your result.`; ask `- **remote-access ask:** stop BEFORE the first remote access (ssh, scp, curl, \`docker -H\`, deploy). Return \`STATUS: partial\` with \`APPROVAL_REQUEST: env=<name>; action=<read|deploy: action>\`. The orchestrator obtains the user's approval and re-dispatches with \`APPROVED: env=<name>; action=<action>\` in the task. The approval applies only to the named environment and action; every further action needs a new APPROVAL_REQUEST. Record the approval in your report.`
- Ziel unklar: bei mehr als einer Umgebung oder einer remote/both-Umgebung ohne URL `- If the target or its URL is unclear, return \`STATUS: partial\` with \`APPROVAL_REQUEST: target?\` and ask main_chat.`
- Secrets, je Umgebung mit `token-env` NAME: ``- **Token for `<env>`:** env var `${NAME}`; the value comes from the shell environment, provided via `source .meta-config/env.sh` (from the `environments:` entry `NAME` with `secret: true`, masked). Never print, log or write the value, and never read it from files; use `${NAME}` in the shell only.``

- [ ] **Step 1: Failing Tests schreiben** (Fixtures im Testmodul, Schema aus Task 5):
  ```python
  HA_ENV = {"ha-dev": {"kind": "both", "url": "http://ha-dev.lan:8123", "url_source": "config", "token-env": "HA_DEV_TOKEN",
                       "access": "deploy", "remote-access": "ask", "notes": "Integration erst lokal testen."}}
  LOCAL_ENV = {"sharkord-local": {"kind": "local", "url": None, "url_source": "", "token-env": None,
                                  "access": "read", "remote-access": "ask", "notes": "docker compose run --rm test"}}

  def _with(env, **over): return {k: {**v, **over} for k, v in env.items()}

  def test_empty_returns_empty_string(): assert render_test_environment_block({}) == ""

  def test_table_lists_all_environments_sorted():
      out = render_test_environment_block({**LOCAL_ENV, **HA_ENV})
      assert out.startswith("## Test environments")
      assert "| Name | kind | URL / source | access | remote-access | notes |" in out
      assert "| ha-dev | both | http://ha-dev.lan:8123 | deploy | ask | Integration erst lokal testen. |" in out
      assert "| sharkord-local | local | — | — | — | docker compose run --rm test |" in out
      assert out.index("| ha-dev |") < out.index("| sharkord-local |")

  def test_ask_protocol_texts():                                                   # AC-ENV-8, AC-ENV-20
      out = render_test_environment_block(HA_ENV)
      for s in ("stop BEFORE the first remote access", "STATUS: partial", "APPROVAL_REQUEST: env=<name>; action=<read|deploy: action>",
                "APPROVED: env=<name>; action=<action>", "applies only to the named environment and action", "Record the approval in your report"):
          assert s in out

  def test_both_requires_local_first():
      assert "test locally first, then the remote environment only after approval" in render_test_environment_block(HA_ENV)

  def test_deny_text():                                                            # AC-ENV-20
      out = render_test_environment_block(_with(HA_ENV, **{"remote-access": "deny"}))
      assert "never contact the environment" in out and "report it to main_chat" in out
      assert "APPROVAL_REQUEST: env=" not in out

  def test_allow_text():                                                           # AC-ENV-20
      out = render_test_environment_block(_with(HA_ENV, **{"remote-access": "allow"}))
      assert "report every deploy" in out and "APPROVAL_REQUEST: env=" not in out

  def test_protocol_texts_absent_for_local_only():
      out = render_test_environment_block(LOCAL_ENV)
      assert "APPROVAL_REQUEST: env=" not in out and "never contact" not in out
      assert "Access approval is a prompt convention (convention boundary), not a technical barrier." in out

  def test_secret_hint_names_only_the_name():                                     # AC-ENV-6
      out = render_test_environment_block(HA_ENV)
      for s in ("`${HA_DEV_TOKEN}`", "source .meta-config/env.sh", "Never print, log or write the value", "`secret: true`"):
          assert s in out

  def test_missing_url_marker_and_target_rule():                                  # AC-ENV-4
      out = render_test_environment_block(_with(HA_ENV, url=None, url_source=""))
      assert "URL not configured" in out and "APPROVAL_REQUEST: target?" in out

  def test_fallback_url_shows_source():
      out = render_test_environment_block(_with(HA_ENV, url="http://dev:8123", url_source="platform.hacs.dev_instance_url"))
      assert "http://dev:8123 (from platform.hacs.dev_instance_url)" in out

  def test_unclear_target_rule_only_when_needed():
      assert "APPROVAL_REQUEST: target?" in render_test_environment_block({**LOCAL_ENV, **HA_ENV})
      assert "APPROVAL_REQUEST: target?" not in render_test_environment_block(LOCAL_ENV)

  def test_cells_are_sanitized():                                                  # RF4
      out = render_test_environment_block(_with(LOCAL_ENV, notes="a|b\nc"))
      assert "| a\\|b c |" in out

  def test_deploy_rule_mentions_deny_wins():
      assert "deny always wins" in render_test_environment_block(HA_ENV)

  def test_render_is_deterministic_without_trailing_newline():
      a = render_test_environment_block({**LOCAL_ENV, **HA_ENV})
      assert a == render_test_environment_block({**HA_ENV, **LOCAL_ENV}) and not a.endswith("\n")

  def test_namensabgrenzung_sentence():                                            # AC-ENV-17
      assert "`environments:` defines environment variables" in render_test_environment_block(LOCAL_ENV)
  ```
- [ ] **Step 2: Run, erwartet FAIL.** `python3 -m pytest tests/test_test_environments_render_block.py --basetemp={{PYTEST_BASETEMP}}` => ImportError.
- [ ] **Step 3: Implementieren** gemäß Textbausteinen (reine String-Funktion, keine Rollen-/Provider-Parameter, b12/C2).
- [ ] **Step 4: Run, erwartet PASS.** Wie Step 2; zusätzlich `python3 -m pytest tests/test_test_environments_lib.py::test_module_budget_and_constraints --basetemp={{PYTEST_BASETEMP}}` (Modul weiterhin <= 600 Zeilen, AC-ENV-18).
- [ ] **Step 5: Commit.** `git add scripts/lib/test_environments.py tests/test_test_environments_render_block.py` und `git commit -m "feat: render test environment block with approval protocol"`.

---

### Task 7: Platzhalter-Registrierung

**Agent:** developer
**Depends on:** 6
**Files:**
- Modify: `scripts/lib/test_environments.py` (`build_test_environment_variables`)
- Modify: `scripts/lib/config.py` (Import + Aufrufzeile nach :2463)
- Modify: `scripts/lib/consistency/placeholders.py` (`_BUILTIN_VARS`, neben :107)
- Modify: `scripts/lib/standalone.py` (`_CONDITIONAL_FALSE_FLAGS` neben :138, `_ORCHESTRATION_FALLBACKS` neben `SUBAGENT_PERMISSIONS_BLOCK`)
- Modify: `docs/guides/features/sync-concept.md` (Tabelle :278-287)
- Create: `tests/test_test_environments_consistency.py`

**Interfaces:** Produces: `build_test_environment_variables(config: dict, project_root: Optional[Path]) -> dict` (genau die Keys `TEST_ENVIRONMENT_BLOCK` (str) und `TEST_ENVIRONMENTS_SET` (`"true"`/`"false"`); nutzt `load_project_platform_vars` nur wenn `project_root` gesetzt). Consumes: `resolve_test_environments`, `render_test_environment_block`.

- [ ] **Step 1: Failing Tests schreiben:**
  ```python
  def test_builder_unconfigured():
      assert build_test_environment_variables({}, None) == {"TEST_ENVIRONMENT_BLOCK": "", "TEST_ENVIRONMENTS_SET": "false"}

  def test_builder_configured_uses_platform_fallback(tmp_path):
      (tmp_path / ".claude").mkdir()
      (tmp_path / ".claude" / "platform-config.yaml").write_text("platform:\n  hacs:\n    dev_instance_url: http://dev:8123\n", encoding="utf-8")
      v = build_test_environment_variables({"test-environments": {"ha": {"kind": "remote"}}}, tmp_path)
      assert v["TEST_ENVIRONMENTS_SET"] == "true" and "http://dev:8123 (from platform.hacs.dev_instance_url)" in v["TEST_ENVIRONMENT_BLOCK"]

  def test_build_variables_carries_both_keys():
      cfg = load_config(REPO_ROOT / ".meta-config" / "project.yaml")
      v, _ = build_variables(cfg, REPO_ROOT)
      assert (v["TEST_ENVIRONMENT_BLOCK"], v["TEST_ENVIRONMENTS_SET"]) == ("", "false")
      cfg2 = {**cfg, "test-environments": {"sharkord-local": {"kind": "local"}}}
      v2, _ = build_variables(cfg2, REPO_ROOT)
      assert v2["TEST_ENVIRONMENTS_SET"] == "true" and v2["TEST_ENVIRONMENT_BLOCK"].startswith("## Test environments")

  def test_placeholders_registered():
      from lib.consistency.placeholders import _BUILTIN_VARS, _UNREGISTERED_BUILDER_RATCHET
      assert {"TEST_ENVIRONMENT_BLOCK", "TEST_ENVIRONMENTS_SET"} <= _BUILTIN_VARS
      assert not {"TEST_ENVIRONMENT_BLOCK", "TEST_ENVIRONMENTS_SET"} & _UNREGISTERED_BUILDER_RATCHET

  def test_standalone_fallbacks():
      from lib.standalone import _CONDITIONAL_FALSE_FLAGS, _ORCHESTRATION_FALLBACKS
      assert _CONDITIONAL_FALSE_FLAGS["TEST_ENVIRONMENTS_SET"] == "false" and _ORCHESTRATION_FALLBACKS["TEST_ENVIRONMENT_BLOCK"] == ""

  def test_sync_concept_documents_both_placeholders():                             # Issue #1082: escaped Beispiele
      text = (REPO_ROOT / "docs/guides/features/sync-concept.md").read_text(encoding="utf-8")
      assert "{{%TEST_ENVIRONMENT_BLOCK%}}" in text and "{{%TEST_ENVIRONMENTS_SET%}}" in text
      assert "{{TEST_ENVIRONMENT_BLOCK}}" not in text.replace("{{%TEST_ENVIRONMENT_BLOCK%}}", "")

  def test_set_suffix_gate_strips_with_trailing_newline():
      gate = "a\n{{#if TEST_ENVIRONMENTS_SET}}\nX\n{{/if}}\nb\n"
      assert strip_inactive_conditional_blocks(gate, {"TEST_ENVIRONMENTS_SET": "false"}) == "a\nb\n"
      assert strip_inactive_conditional_blocks(gate, {"TEST_ENVIRONMENTS_SET": "true"}) == "a\nX\nb\n"
  ```
- [ ] **Step 2: Run, erwartet FAIL.** `python3 -m pytest tests/test_test_environments_consistency.py --basetemp={{PYTEST_BASETEMP}}` => ImportError bzw. `KeyError`.
- [ ] **Step 3: Implementieren.** Builder wie oben; `config.py`: Import und in `build_variables` direkt nach `_build_convention_variables(...)` die Zeile `variables.update(build_test_environment_variables(config, project_root))`; `placeholders.py`: beide Namen in `_BUILTIN_VARS` (Kommentar „Test environments (build_test_environment_variables)“); `standalone.py`: `"TEST_ENVIRONMENTS_SET": "false"` in `_CONDITIONAL_FALSE_FLAGS`, `"TEST_ENVIRONMENT_BLOCK": ""` in `_ORCHESTRATION_FALLBACKS` (Kommentar: nur innerhalb des `{{#if}}`-Gates referenziert); `sync-concept.md`: zwei Tabellenzeilen mit escapten Beispielen `{{%TEST_ENVIRONMENT_BLOCK%}}` („Markdown-Block der deklarierten Test-Umgebungen aus `test-environments`, leer wenn nicht konfiguriert“) und `{{%TEST_ENVIRONMENTS_SET%}}` („`true`/`false`; steuert das Gate um den Block in den Rollen-Templates“).
- [ ] **Step 4: Run, erwartet PASS.** Wie Step 2; danach `python3 -m pytest tests/test_conventions_migration_invariant.py --basetemp={{PYTEST_BASETEMP}}` und `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate` (keine ungelösten Platzhalter, AC-ENV-15).
- [ ] **Step 5: Commit.** `git add scripts/lib/test_environments.py scripts/lib/config.py scripts/lib/consistency/placeholders.py scripts/lib/standalone.py docs/guides/features/sync-concept.md tests/test_test_environments_consistency.py` und `git commit -m "feat: register TEST_ENVIRONMENT_BLOCK placeholders"`.

---

### Task 8: Sechs Basis-Templates, Versionen, Render- und Secret-Tests

**Agent:** developer
**Depends on:** 7
**Files:**
- Modify: `agents/1-generic/tester.md` (:134, Version 2.8.0 -> 2.9.0)
- Modify: `agents/1-generic/e2e-tester.md` (:144, 1.6.1 -> 1.7.0)
- Modify: `agents/1-generic/developer.md` (:147, 4.8.1 -> 4.9.0)
- Modify: `agents/1-generic/docker.md` (:118, 1.9.1 -> 1.10.0)
- Modify: `agents/1-generic/devops-engineer.md` (:192, 1.7.1 -> 1.8.0)
- Modify: `agents/1-generic/test-executor.md` (:125, 1.2.2 -> 1.3.0)
- Modify: `tests/test_test_environments_render.py`
- Create: `tests/test_test_environments_secrets_via_render.py`

**Interfaces:** Produces: pro Template der Gate-Block `{{#if TEST_ENVIRONMENTS_SET}}\n{{TEST_ENVIRONMENT_BLOCK}}\n<Rollenzeile>\n{{/if}}\n` direkt nach `</constraints>` (vor `{{OUTPUT_GUARD_BLOCK}}`, soweit vorhanden). Statische Rollenzeilen (`ROLE_LINES`):
tester und e2e-tester: `Run tests locally before touching any remote environment.`;
developer: `Develop and test locally first; touch a remote environment only as the rules above allow.`;
docker und devops-engineer: `Deploy to a remote environment only if its access is deploy and the approval protocol above is satisfied.`;
test-executor: `Read-only: run existing suites against environments only as the rules above allow; never deploy.`
Consumes: `{{TEST_ENVIRONMENT_BLOCK}}`/`TEST_ENVIRONMENTS_SET` (Task 7), Harness (Task 1).

- [ ] **Step 1: Failing Tests schreiben** in `tests/test_test_environments_render.py` (Konstanten `BASE_VERSIONS = {"tester": "2.9.0", "e2e-tester": "1.7.0", "developer": "4.9.0", "docker": "1.10.0", "devops-engineer": "1.8.0", "test-executor": "1.3.0"}`, `ROLE_LINES` wie oben, `CONFIG_YAML` = Spec §9.1: `environments:` mit `HA_DEV_TOKEN` (`description`, `secret: true`, ohne Wert) und `test-environments:` mit `ha-dev` (both, `http://ha-dev.lan:8123`, `token-env: HA_DEV_TOKEN`, deploy, ask, notes) und `sharkord-local` (local)):
  ```python
  @pytest.mark.parametrize("role", sorted(BASE_VERSIONS))
  def test_template_has_gated_block_directly_after_constraints(role):
      src = (REPO_ROOT / "agents" / "1-generic" / f"{role}.md").read_text(encoding="utf-8")
      gate = "{{#if TEST_ENVIRONMENTS_SET}}\n{{TEST_ENVIRONMENT_BLOCK}}\n" + ROLE_LINES[role] + "\n{{/if}}\n"
      assert f'version: "{BASE_VERSIONS[role]}"' in src and src.count(gate) == 1
      end = src.index("</constraints>") + len("</constraints>")
      assert src[end:src.index(gate)].strip() == ""
      if "{{OUTPUT_GUARD_BLOCK}}" in src:
          assert src.index(gate) < src.index("{{OUTPUT_GUARD_BLOCK}}")

  @pytest.fixture(scope="module")
  def configured(tmp_path_factory):
      return _role_texts(_sync_project(tmp_path_factory.mktemp("cfg"), extra_yaml=CONFIG_YAML))

  def test_configured_render_has_block_table_and_role_line(configured):            # AC-ENV-7
      assert {_role_of(s) for s in configured} == set(BASE_VERSIONS)
      for stem, text in configured.items():
          assert "## Test environments" in text and "| ha-dev | both | http://ha-dev.lan:8123 | deploy | ask |" in text
          assert ROLE_LINES[_role_of(stem)] in text
          assert text.index("</constraints>") < text.index("## Test environments")

  def test_approval_protocol_in_all_six_roles(configured):                         # AC-ENV-8, AC-ENV-20
      for text in configured.values():
          assert "APPROVAL_REQUEST: env=<name>; action=<read|deploy: action>" in text and "APPROVED: env=<name>; action=<action>" in text
          assert "convention boundary" in text
          block = text.split("## Test environments", 1)[1].split("\n## ", 1)[0]
          assert "{{" not in block

  def test_settings_json_identical_and_no_secrets_file(tmp_path_factory):         # AC-ENV-11 (Ersatz), AC-ENV-1
      unset = _sync_project(tmp_path_factory.mktemp("u"))
      cfg = _sync_project(tmp_path_factory.mktemp("c"), extra_yaml=CONFIG_YAML)
      assert (unset / ".claude/settings.json").read_bytes() == (cfg / ".claude/settings.json").read_bytes()
      assert not (unset / ".meta-config/secrets.local.yaml").exists() and not (cfg / ".meta-config/secrets.local.yaml").exists()
  ```
  (`test_unset_render_matches_baseline` aus Task 1 bleibt unverändert und muss grün bleiben.) `tests/test_test_environments_secrets_via_render.py`:
  ```python
  CANARY = "canary-secret-8f3a91"
  def test_no_token_value_in_any_generated_file(tmp_path):                         # AC-ENV-6, AZ2
      project = _sync_project(tmp_path, extra_yaml=CONFIG_YAML, extra_env={"HA_DEV_TOKEN": CANARY})
      for f in project.rglob("*"):
          if f.is_file() and ".git" not in f.parts:
              assert CANARY.encode() not in f.read_bytes(), f
      assert any("${HA_DEV_TOKEN}" in t for t in _role_texts(project).values())
      env_sh = (project / ".meta-config" / "env.sh").read_text(encoding="utf-8")
      assert "HA_DEV_TOKEN" in env_sh and "[SECRET]" in env_sh and CANARY not in env_sh
  ```
  (Importe der Helfer und `CONFIG_YAML` aus `test_test_environments_render` per `from test_test_environments_render import _sync_project, _role_texts, CONFIG_YAML`; pytest legt das Testverzeichnis in `sys.path`.)
- [ ] **Step 2: Run, erwartet FAIL.** `python3 -m pytest tests/test_test_environments_render.py tests/test_test_environments_secrets_via_render.py --basetemp={{PYTEST_BASETEMP}}` => Gate/Version fehlen; `test_unset_render_matches_baseline` bleibt grün.
- [ ] **Step 3: Templates ändern.** Pro Template: `version` bumpen; direkt hinter der `</constraints>`-Zeile das Gate einfügen. Layout so, dass das Entfernen von `{{#if…}}…{{/if}}\n` exakt den Originaltext ergibt (OF-4, der Ausführende entscheidet anhand der Baseline): bei den fünf Templates mit `{{OUTPUT_GUARD_BLOCK}}` bleibt die Leerzeile nach `</constraints>`, das Gate folgt unmittelbar vor `{{OUTPUT_GUARD_BLOCK}}`; bei `test-executor` (Dateiende) steht das Gate ohne Leerzeile direkt unter `</constraints>`. `docker.md:84` (`{{#if DEV_STACK_START_SET}}`) bleibt unberührt.
- [ ] **Step 4: Run, erwartet PASS.** Wie Step 2 (alle Tests inkl. Baseline); `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`. Erwartete, bis Task 15 bewusst offene Drift: `tests/test_ac01_render_identity.py` (Versions-Pins) — hier nicht ausführen.
- [ ] **Step 5: Commit.** `git add agents/1-generic/tester.md agents/1-generic/e2e-tester.md agents/1-generic/developer.md agents/1-generic/docker.md agents/1-generic/devops-engineer.md agents/1-generic/test-executor.md tests/test_test_environments_render.py tests/test_test_environments_secrets_via_render.py` und `git commit -m "feat: add test environment block to six role templates"`.

---

### Task 9: Sieben Overrides nachziehen

**Agent:** developer
**Depends on:** 8
**Files:**
- Modify: `agents/2-platform/homeassistant-developer.md` (version 2.1.2 -> 2.1.3, based-on `1-generic/developer.md@4.9.0`)
- Modify: `agents/2-platform/sharkord-developer.md` (3.0.2 -> 3.0.3, `developer.md@4.9.0`)
- Modify: `agents/2-platform/hacs-developer.md` (1.3.1 -> 1.3.2, `developer.md@4.9.0`)
- Modify: `agents/2-platform/agent-meta-developer.md` (2.0.2 -> 2.0.3, `developer.md@4.9.0`)
- Modify: `agents/2-platform/hacs-tester.md` (1.0.4 -> 1.0.5, `tester.md@2.9.0`)
- Modify: `agents/2-platform/hacs-devops-engineer.md` (1.0.1 -> 1.0.2, `devops-engineer.md@1.8.0`)
- Modify: `agents/2-platform/sharkord-docker.md` (Standalone, 1.2.4 -> 1.2.5, `docker.md@1.10.0`; Gate-Block manuell)
- Modify: `tests/test_test_environments_render.py`

**Interfaces:** Produces: extends-Overrides erben den Block (liegt außerhalb der Tag-Anker); `sharkord-docker` enthält das Gate vor `## Sprache`. Consumes: Basisversionen aus Task 8.

- [ ] **Step 1: Failing Tests ergänzen:**
  ```python
  OVERRIDES = {"homeassistant-developer.md": ("2.1.3", "1-generic/developer.md@4.9.0"), "sharkord-developer.md": ("3.0.3", "1-generic/developer.md@4.9.0"),
               "hacs-developer.md": ("1.3.2", "1-generic/developer.md@4.9.0"), "agent-meta-developer.md": ("2.0.3", "1-generic/developer.md@4.9.0"),
               "hacs-tester.md": ("1.0.5", "1-generic/tester.md@2.9.0"), "hacs-devops-engineer.md": ("1.0.2", "1-generic/devops-engineer.md@1.8.0"),
               "sharkord-docker.md": ("1.2.5", "1-generic/docker.md@1.10.0")}

  @pytest.mark.parametrize("fname", sorted(OVERRIDES))
  def test_override_version_and_based_on(fname):                                   # AC-ENV-10
      head = (REPO_ROOT / "agents" / "2-platform" / fname).read_text(encoding="utf-8").split("---", 2)[1]
      ver, based = OVERRIDES[fname]
      assert f'version: "{ver}"' in head and f'based-on: "{based}"' in head

  def test_extends_overrides_do_not_duplicate_the_block():
      for fname in OVERRIDES:
          if fname != "sharkord-docker.md":
              assert "TEST_ENVIRONMENT_BLOCK" not in (REPO_ROOT / "agents" / "2-platform" / fname).read_text(encoding="utf-8")

  def test_sharkord_docker_has_manual_gate_before_sprache():
      src = (REPO_ROOT / "agents" / "2-platform" / "sharkord-docker.md").read_text(encoding="utf-8")
      gate = "{{#if TEST_ENVIRONMENTS_SET}}\n{{TEST_ENVIRONMENT_BLOCK}}\nDeploy auf eine Remote-Umgebung nur bei `access: deploy` und erfülltem Freigabeprotokoll.\n{{/if}}\n"
      assert src.count(gate) == 1 and src.index("## Don'ts") < src.index(gate) < src.index("## Sprache")

  @pytest.mark.parametrize("label", ["homeassistant", "sharkord", "hacs", "agent-meta"])
  def test_override_render_with_block_resolves_anchors(label, tmp_path_factory):
      project = _sync_project(tmp_path_factory.mktemp(label), platforms=(label,), extra_yaml=CONFIG_YAML)
      log_file = project / "sync.log"
      log = log_file.read_text(encoding="utf-8", errors="replace").lower() if log_file.exists() else ""
      assert "anchor" not in log or "not found" not in log                         # keine Composition-Patch-Warnung
      texts = _role_texts(project)
      for role in OVERRIDE_COVERAGE[label]:
          stems = [s for s in texts if _role_of(s) == role]
          assert stems, (label, role)
          for s in stems:
              text = texts[s]
              assert "## Test environments" in text
              if "</constraints>" in text:                                         # extends-Overrides: Block nach den Tag-Ankern
                  assert text.rindex("</constraints>") < text.index("## Test environments")
              else:                                                                # sharkord-docker (Standalone)
                  assert text.index("## Test environments") < text.index("## Sprache")
  ```
- [ ] **Step 2: Run, erwartet FAIL.** `python3 -m pytest tests/test_test_environments_render.py --basetemp={{PYTEST_BASETEMP}}` => alte Versionen/`based-on`, fehlender Block in `sharkord-docker`.
- [ ] **Step 3: Overrides ändern.** Frontmatter `version`/`based-on` wie oben; `sharkord-docker.md`: Gate zwischen dem letzten `## Don'ts`-Listenpunkt und `## Sprache` einfügen, so dass das Entfernen des Gates samt Zeilenumbruch den Originaltext ergibt (Leerzeile vor dem Gate). Patch-Texte in den extends-Overrides bleiben unverändert (Block liegt nach `</constraints>`, nie innerhalb gepatchten Textes).
- [ ] **Step 4: Run, erwartet PASS.** Wie Step 2 (inkl. `test_unset_render_matches_baseline` für alle 5 Varianten); `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate` (Consistency: `based-on` aktuell, keine Anker-Warnung).
- [ ] **Step 5: Commit.** `git add agents/2-platform/homeassistant-developer.md agents/2-platform/sharkord-developer.md agents/2-platform/hacs-developer.md agents/2-platform/agent-meta-developer.md agents/2-platform/hacs-tester.md agents/2-platform/hacs-devops-engineer.md agents/2-platform/sharkord-docker.md tests/test_test_environments_render.py` und `git commit -m "feat: align platform overrides with test environment block"`.

---

### Task 10: Admin-Server — Whitelist und Section-Guard

**Agent:** developer
**Depends on:** 7
**Files:**
- Modify: `scripts/admin-server.py` (`PROJECT_WRITABLE_SECTIONS` :233-252; `_write_project_section` :5176-5200; `_route_put_config` Projekt-Zweig :3921-3942; zwei neue Methoden)
- Create: `tests/_te_admin_helpers.py` (`_handler(root)`, `_post(handler, section, data)`)
- Create: `tests/test_admin_ui_test_environments_section.py` (Server-Teil; UI-Teil folgt in Task 11)

**Interfaces:** Produces: `AdminRequestHandler._guard_test_environments_config(self, candidate: dict) -> None` (ruft `lib.test_environments.collect_test_environment_errors(candidate)`, `ValueError("invalid test-environments config: " + "; ".join(errors))` bei Fehlern), `AdminRequestHandler._guard_test_environments_write(self, section: str, data: Any, existing: dict) -> None` (greift nur für `section in ("test-environments", "environments")`, Kandidat = `{**existing, section: data}`); Testhelfer `_handler(root: Path)` (lädt `scripts/admin-server.py` per `importlib` wie `tests/test_admin_server.py:40-50`, setzt `AdminRequestHandler.root` und `config_manager = ConfigManager(root, mode="project_admin")`, `_send_json = lambda result: None`) und `_post(handler, section, data) -> None` (setzt `handler._read_body = lambda: {"section": section, "data": data}`, ruft `_write_project_section()`). Consumes: `collect_test_environment_errors` (Task 4).

- [ ] **Step 1: Failing Tests schreiben:**
  ```python
  ENVS = {"HA_DEV_TOKEN": {"description": "t", "secret": True}}
  VALID = {"ha-dev": {"kind": "remote", "url": "http://ha-dev.lan:8123", "token-env": "HA_DEV_TOKEN", "access": "read", "remote-access": "ask"}}

  def test_whitelist_contains_section():                                           # AC-ENV-12
      assert "test-environments" in admin_server.PROJECT_WRITABLE_SECTIONS

  def test_valid_payload_round_trips(tmp_path):
      h = _handler(tmp_path); h.config_manager.write("project", {"environments": ENVS})
      _post(h, "test-environments", VALID)
      assert h.config_manager.read("project")["test-environments"] == VALID

  @pytest.mark.parametrize("bad,needle", [({"a": {"kind": "remoteish"}}, "kind"), ({"a": {"kind": True}}, "quote the value"),
                                          ({"a": {"colour": "x"}}, "unknown key"), ({"a": {"url": "http://u:p@h"}}, "userinfo"),
                                          ({"a": {"token-env": "HA_DEV_TOKEN"}}, "not defined")])
  def test_invalid_payload_rejected_nothing_written(tmp_path, bad, needle):
      h = _handler(tmp_path); h.config_manager.write("project", {"git": {"keep": 1}})
      with pytest.raises(ValueError) as exc: _post(h, "test-environments", bad)
      assert needle in str(exc.value) and h.config_manager.read("project") == {"git": {"keep": 1}}

  def test_token_env_with_non_secret_entry_rejected(tmp_path):
      h = _handler(tmp_path); h.config_manager.write("project", {"environments": {"HA_DEV_TOKEN": {"description": "t", "secret": False}}})
      with pytest.raises(ValueError, match="secret: true"): _post(h, "test-environments", VALID)

  def test_null_deletes_section_without_error(tmp_path):                           # RF5
      h = _handler(tmp_path); h.config_manager.write("project", {"environments": ENVS, "test-environments": VALID})
      _post(h, "test-environments", None)
      assert h.config_manager.read("project").get("test-environments") is None

  def test_environments_write_breaking_reference_rejected(tmp_path):               # RF5
      h = _handler(tmp_path); h.config_manager.write("project", {"environments": ENVS, "test-environments": VALID})
      with pytest.raises(ValueError, match="environments entry 'HA_DEV_TOKEN' not defined"): _post(h, "environments", {})
      assert h.config_manager.read("project")["environments"] == ENVS

  def test_environments_write_unrelated_variable_ok(tmp_path):
      h = _handler(tmp_path); h.config_manager.write("project", {"environments": ENVS, "test-environments": VALID})
      _post(h, "environments", {**ENVS, "OTHER": {"description": "x"}})

  def test_full_document_put_guarded(tmp_path):                                    # RF5
      h = _handler(tmp_path); h.config_manager.write("project", {"git": {"keep": 1}})
      h._read_body = lambda: {"test-environments": {"a": {"kind": "x"}}}
      with pytest.raises(ValueError): h._route_put_config("project")
      assert h.config_manager.read("project") == {"git": {"keep": 1}}

  def test_unrelated_section_not_blocked_by_preexisting_invalid_config(tmp_path): # RF5
      h = _handler(tmp_path); h.config_manager.write("project", {"test-environments": {"a": {"kind": "x"}}})
      _post(h, "git", {"auto_commit": False})
  ```
  (`admin_server` im Testmodul = Modul aus `_te_admin_helpers`, per `from _te_admin_helpers import admin_server, _handler, _post`.)
- [ ] **Step 2: Run, erwartet FAIL.** `python3 -m pytest tests/test_admin_ui_test_environments_section.py --basetemp={{PYTEST_BASETEMP}}` => `section not allowed: test-environments`.
- [ ] **Step 3: Implementieren.** `"test-environments"` in `PROJECT_WRITABLE_SECTIONS` (neben `"environments"`); `_write_project_section`: nach `self._guard_model_block_write(...)` die Zeile `self._guard_test_environments_write(section, data, existing)`; `_route_put_config` (Projekt-Zweig, nach den `_guard_context_profile_write`-Aufrufen): wenn `"test-environments"` oder `"environments"` in `body`, `self._guard_test_environments_config(self._deep_merge(existing, body))`; Import von `collect_test_environment_errors` lazy innerhalb der Methode (Muster `from lib.yaml_roundtrip import …`). `None` für `test-environments` gilt als unkonfiguriert (Task 3).
- [ ] **Step 4: Run, erwartet PASS.** Wie Step 2; zusätzlich `python3 -m pytest tests/test_admin_server.py --basetemp={{PYTEST_BASETEMP}}` (keine Regression).
- [ ] **Step 5: Commit.** `git add scripts/admin-server.py tests/_te_admin_helpers.py tests/test_admin_ui_test_environments_section.py` und `git commit -m "feat: guard test-environments writes in admin server"`.

---

### Task 11: Admin-UI-Sektion und Help

**Agent:** developer
**Depends on:** 10
**Files:**
- Modify: `docs/ui/admin-ui.html` (neue Funktion `viewProjectTestEnvironments` nach dem Ende von `viewProjectEnvironments` (:8632ff); Nav nach :1644; `router.register` nach :10868; `routeMap` :10961ff; Gegen-Hinweis in `viewProjectEnvironments`)
- Modify: `docs/api/admin-ui-reference.md` (Help-Block)
- Modify: `tests/test_admin_ui_test_environments_section.py` (UI-Teil)

**Interfaces:** Produces: `async function viewProjectTestEnvironments()` (Tabelle + Modal, Muster `viewProjectEnvironments`), Nav `{ route: "/project/test-environments", label: "Test Environments", icon: "🧪" }`, `router.register("/project/test-environments", viewProjectTestEnvironments)`, `routeMap`-Eintrag `"project/test-environments": "project_instance-test_environments"`, Help-Block `<!-- help-id: project_instance-test_environments -->`. Consumes: `loadProject()`, `saveProjectSection(key, value, statusEl)` (:5958), `selectField(options, value, onChange)` (:1995), `confirmDestructive(message, onConfirm, opts)` (:845), Server-Guard (Task 10).

- [ ] **Step 1: Failing Tests ergänzen** (Muster `tests/test_admin_ui_git_section.py`; `HTML`/`HELP_REF` werden wie dort eingelesen; `_view_body()` schneidet den Text von `async function viewProjectTestEnvironments(` bis zur nächsten `\nasync function ` heraus):
  ```python
  def test_view_defined_routed_and_in_nav():                                       # AC-ENV-12
      assert "async function viewProjectTestEnvironments(" in HTML
      assert re.search(r'router\.register\(\s*"/project/test-environments"\s*,\s*viewProjectTestEnvironments\s*\)', HTML)
      assert 'route: "/project/test-environments"' in HTML

  def test_saved_via_partial_update_with_string_enums():
      body = _view_body()
      assert 'saveProjectSection("test-environments"' in body
      for enum in ('["local", "remote", "both"]', '["read", "deploy"]', '["deny", "ask", "allow"]'):
          assert enum in body

  def test_no_secret_value_input():                                                # Z7, AZ2
      body = _view_body()
      assert not re.search(r'type:\s*"password"', body)
      assert "TOKEN_ENV_RE" in body and "^[A-Z][A-Z0-9_]*$" in body
      assert "nie hier eintragen" in body

  def test_remote_activation_requires_confirmation():
      assert "confirmDestructive(" in _view_body()

  def test_cross_hints_between_environments_views():                               # AC-ENV-17
      assert "Environment Variables" in _view_body() and "secret" in _view_body().lower()
      env_view = HTML.split("async function viewProjectEnvironments(", 1)[1].split("\nasync function ", 1)[0]
      assert "Test Environments" in env_view

  def test_routemap_and_help_block_and_checker():
      assert '"project/test-environments": "project_instance-test_environments"' in HTML
      assert "<!-- help-id: project_instance-test_environments -->" in HELP_REF
      from lib.consistency.docs import check_ui_help_mappings
      assert [f.message for f in check_ui_help_mappings(REPO_ROOT) if "test_environments" in f.message] == []
  ```
- [ ] **Step 2: Run, erwartet FAIL.** `python3 -m pytest tests/test_admin_ui_test_environments_section.py --basetemp={{PYTEST_BASETEMP}}` => View fehlt.
- [ ] **Step 3: Implementieren.** View mit Feldern Name (Client-Regex `^[a-z0-9][a-z0-9-]*$`), `kind`/`access`/`remote-access` über `selectField` (immer Strings), `url`, `token-env` (nur NAME, Client-Regex `TOKEN_ENV_RE = /^[A-Z][A-Z0-9_]*$/`, Hinweistext „Name eines Eintrags aus ‚Umgebungsvariablen' mit secret=true; Wert kommt per `source .meta-config/env.sh` bzw. aus der Shell — nie hier eintragen“), `notes`; kein Passwort-/Token-Wertfeld; leere optionale Felder werden nicht gespeichert; Aktivieren von `remote`/`both`/`deploy`/`allow` (gegenüber dem Vorzustand) öffnet `confirmDestructive(message, onConfirm, {title: "Confirm remote access", confirmLabel: "Enable"})`; Einleitungstext mit Namensabgrenzung zu „Environment Variables“; in `viewProjectEnvironments` ein Gegenhinweis („Test targets are configured under Test Environments; `token-env` there must reference a variable here with Secret enabled.“). Help-Block in `docs/api/admin-ui-reference.md` im Format der Nachbarblöcke (`### Test Environments`, `help-id`, `last-updated`, `author: Agent Meta Admin`, deutscher Text inkl. Namensabgrenzung, Freigabeprotokoll und „kein `permissions`-Mechanismus“).
- [ ] **Step 4: Run, erwartet PASS.** Wie Step 2; zusätzlich `python3 -m pytest tests/test_admin_ui_git_section.py --basetemp={{PYTEST_BASETEMP}}` (keine Regression der Nachbar-Routen).
- [ ] **Step 5: Commit.** `git add docs/ui/admin-ui.html docs/api/admin-ui-reference.md tests/test_admin_ui_test_environments_section.py` und `git commit -m "feat: add test environments section to admin ui"`.

---

### Task 12: Manager-Rezept und §3-Bestätigung (1.27.0)

**Agent:** developer
**Depends on:** 10
**Files:**
- Modify: `agents/1-generic/agent-meta-manager.md` (§3-Tabelle :60-73, neuer Rezeptabschnitt vor `</workflow>`, Version `1.26.0` -> `1.27.0`)
- Create: `tests/test_test_environments_manager_recipe.py`

**Interfaces:** Produces: Rezeptabschnitt `## <nächste freie Nr.>. Test environments (test-environments)` (Stand dieses Plans nach §17 = Nr. 18; nach Plan 1 ggf. höher — Nummer = letzte `## N.`-Nummer + 1) mit einem yaml-Codeblock, der `environments:` und `test-environments:` zeigt; §3-Zeile ``| Enable remote test environments (`kind: remote\|both`, `remote-access: allow`, `access: deploy`) | Behavior change — agents may contact or deploy to a remote target |``. Consumes: `collect_test_environment_errors`, `tests/_te_admin_helpers.py` (Task 10) für den Paritätstest.

- [ ] **Step 1: Failing Tests schreiben:**
  ```python
  SRC = (REPO_ROOT / "agents/1-generic/agent-meta-manager.md").read_text(encoding="utf-8")
  HEADING = re.search(r"(?m)^## \d+[a-z]?\. Test environments.*$", SRC)

  def test_version_is_1_27_0():                                                    # AC-ENV-13
      assert 'version: "1.27.0"' in SRC

  def test_recipe_steps_present():
      assert HEADING
      recipe = SRC[HEADING.start():].split("\n## ", 1)[0]
      for s in ("Ask which kind", "local, remote or both", "`environments:`", "secret: true", "without a value", "token-env", "only the NAME",
                "source .meta-config/env.sh", "never post the value in the chat", "sync.py", "--validate",
                "`environments:` (env-var definitions)", "`test-environments:` (targets)"):
          assert s in recipe, s

  def test_confirmation_table_row():
      assert re.search(r"(?m)^\| Enable remote test environments .*Behavior change", SRC)

  def test_recipe_example_is_valid_and_has_parity_with_ui_write(tmp_path):         # AC-ENV-14
      recipe = SRC[HEADING.start():].split("\n## ", 1)[0]
      example = yaml.safe_load(re.search(r"```yaml\n(.*?)```", recipe, re.S).group(1))
      assert collect_test_environment_errors(example) == []
      h = _handler(tmp_path)
      for section in ("environments", "test-environments"):                        # Referenzziel zuerst schreiben
          _post(h, section, example[section])
      persisted = h.config_manager.read("project")
      assert {k: persisted[k] for k in example} == example
  ```
- [ ] **Step 2: Run, erwartet FAIL.** Vorbedingung `grep -n '^version' agents/1-generic/agent-meta-manager.md` => `1.26.0` (sonst STOP, Plan 1 fehlt). `python3 -m pytest tests/test_test_environments_manager_recipe.py --basetemp={{PYTEST_BASETEMP}}` => FAIL.
- [ ] **Step 3: Implementieren.** Rezept nach Spec §13: (1) Art erfragen („Ask which kind: local, remote or both“), (2) falls `token-env`: zuerst den `environments:`-Eintrag (`secret: true`, without a value, kein `default`) anlegen/prüfen, dann den Block in `.meta-config/project.yaml` schreiben, nur `token-env: NAME` („only the NAME“), (3) Hinweis „provide the value via the shell environment or `source .meta-config/env.sh` — never post the value in the chat“, (4) `python3 {{AGENT_META_REL_PATH}}scripts/sync.py` + `--validate`, (5) Remote-Aktivierung vorher bestätigen lassen (§3). Die Namensabgrenzung steht als Satz im Abschnitt und enthält wörtlich die beiden Teilstrings aus dem Test (jeweils mit Backticks um den Key). §3-Tabellenzeile nach der `auto_commit`-Zeile. `version: "1.27.0"`.
- [ ] **Step 4: Run, erwartet PASS.** Wie Step 2; `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`. Erwartete, bis Task 15 offene Drift: Manager-Golden und AC-01-Hashes.
- [ ] **Step 5: Commit.** `git add agents/1-generic/agent-meta-manager.md tests/test_test_environments_manager_recipe.py` und `git commit -m "feat: add test environments recipe to agent-meta-manager"`.

---

### Task 13: Szenarien test-env-local / test-env-remote-ask / test-env-unset

**Agent:** tester
**Depends on:** 9, 12
**Files:**
- Create: `tests/scenarios/configs/88-test-env-local.project.yaml`, `tests/scenarios/asserts/88-test-env-local.sh`
- Create: `tests/scenarios/configs/89-test-env-remote-ask.project.yaml`, `tests/scenarios/asserts/89-test-env-remote-ask.sh`
- Create: `tests/scenarios/configs/90-test-env-unset.project.yaml`, `tests/scenarios/asserts/90-test-env-unset.sh`
- Modify: `tests/scenarios/registry.md` (drei Zeilen im Format der Liste ab Zeile 162, nach `87-project-description`)

**Interfaces:** Produces: drei Szenarien (IDs 88-90; Vorbedingung: `ls tests/scenarios/configs | sort | tail -3` — sind 88+ belegt, die nächsten freien IDs nehmen und überall konsistent verwenden). Consumes: `tests/scenarios/run.sh <id-prefix>`, Assert-Vertrag (cwd = Temp-Projekt, `$1`/`REPO_ROOT`).

- [ ] **Step 1: Failing Asserts gegen Configs ohne Block schreiben.** Alle drei Configs zunächst ohne `test-environments`-Key (Muster `04-platform-bundle.project.yaml`: `ai-providers: [Claude]`, `roles:` = die sechs Rollen, `project: {name: scenario-test-env, prefix: ten, short: test-env}`, passende `variables`). Asserts (Muster `04-platform-bundle.sh`, Dateien per Glob `.claude/agents/*developer.md` usw.):
  - 88: jede der sechs Rollen-Dateien enthält `## Test environments` und `| sharkord-local | local |`, enthält NICHT `APPROVAL_REQUEST: env=`.
  - 89: alle sechs enthalten `APPROVAL_REQUEST: env=<name>; action=<read|deploy: action>`, `APPROVED: env=<name>; action=<action>`, `` `${HA_DEV_TOKEN}` ``; `.meta-config/env.sh` existiert, enthält `HA_DEV_TOKEN` und `[SECRET]`; `.claude/settings.json` enthält kein `ssh`/`curl`-Permission-Muster (NZ8).
  - 90: keine der sechs Rollen-Dateien enthält `Test environments`, `TEST_ENVIRONMENT` oder `{{TEST_ENV`; `grep -c APPROVAL_REQUEST` über die sechs Dateien = 0.
- [ ] **Step 2: Run, erwartet FAIL (88, 89).** `tests/scenarios/run.sh 88 89 90` => 88 und 89 FAIL (Block fehlt), 90 PASS.
- [ ] **Step 3: Blöcke in die Configs eintragen.** 88: `test-environments: {sharkord-local: {kind: local, notes: "docker compose run --rm test"}}`, `platforms: [sharkord]`. 89: `platforms: [homeassistant]`, `environments: {HA_DEV_TOKEN: {description: "Long-lived access token of the HA dev server", secret: true}}`, `test-environments: {ha-dev: {kind: both, url: "http://ha-dev.lan:8123", token-env: HA_DEV_TOKEN, access: deploy, remote-access: ask, notes: "Integration erst lokal testen, dann auf den Dev-Server."}}`. 90: Config von 89 ohne beide Blöcke. `registry.md`: drei Zeilen `| 88 | \`88-test-env-local\` | … |` usw. mit Feature-Beschreibung (lokal-only rendert keine Freigabetexte; HA-Dev-Server mit `ask`-Protokoll und Secret-Referenz; unkonfiguriert byte-clean).
- [ ] **Step 4: Run, erwartet PASS.** `tests/scenarios/run.sh 88 89 90` => dreimal PASS; danach `tests/scenarios/run.sh` (alle) ohne neuen FAIL.
- [ ] **Step 5: Commit.** `git add tests/scenarios/configs tests/scenarios/asserts tests/scenarios/registry.md` und `git commit -m "test: add test-env scenarios"`.

---

### Task 14: Doku, Beispiel-Config, CHANGELOG, RELEASE_GATES-Satz

**Agent:** documenter
**Depends on:** 11, 12
**Files:**
- Create: `docs/guides/features/test-environments.md` (Deutsch)
- Modify: `howto/configs/project.yaml.example` (Beispielblock zwischen den Markern `# --- test-environments (example) ---` und `# --- end test-environments ---`, Zeilen mit Präfix `# `)
- Modify: `CHANGELOG.md` (`## [Unreleased]`)
- Modify: `docs/RELEASE_GATES.md` (ein Satz, Abschnitt `## Projekt-eigene Pre-Release-Checkliste`, :511ff; hat Plan 1 den Abschnitt umbenannt, ans Ende der Checklisten-Doku)
- Create: `tests/test_test_environments_docs.py`

**Interfaces:** Produces: Kapitel mit Abschnitten Zweck, Namensabgrenzung `environments` vs. `test-environments`, Schema-Felder und Defaults, Referenzregel `token-env`, Fallback-URL (§10.2), Freigabeprotokoll, Hinweis „kein `permissions`-Mechanismus, siehe F6“, Convention-boundary-Hinweis (AZ3). RELEASE_GATES-Satz: „Ein Dry-Check (`MODE: check-only`) gegen eine Test-Umgebung führt ausschließlich `access: read`-Aktionen aus und beachtet `remote-access` sowie das Freigabeprotokoll (`test-environments`).“

- [ ] **Step 1: Failing Tests schreiben:**
  ```python
  def test_chapter_documents_distinction_protocol_and_limits():                    # AC-ENV-17
      t = (REPO_ROOT / "docs/guides/features/test-environments.md").read_text(encoding="utf-8")
      for s in ("`environments:`", "`test-environments:`", "token-env", "secret: true", "APPROVAL_REQUEST", "APPROVED", "Convention boundary", "F6", "permissions", "dev_instance_url", "ha_url"):
          assert s in t, s
      assert "{{TEST_ENVIRONMENT" not in t.replace("{{%TEST_ENVIRONMENT_BLOCK%}}", "")   # Issue #1082

  def test_release_gates_sentence():                                               # AC-ENV-19
      t = (REPO_ROOT / "docs/RELEASE_GATES.md").read_text(encoding="utf-8")
      assert "Dry-Check" in t and "access: read" in t and "test-environments" in t

  def test_example_config_block_is_valid():
      raw = (REPO_ROOT / "howto/configs/project.yaml.example").read_text(encoding="utf-8")
      start, end = "# --- test-environments (example) ---", "# --- end test-environments ---"
      body = raw.split(start, 1)[1].split(end, 1)[0]
      cfg = yaml.safe_load("\n".join(l[2:] if l.startswith("# ") else l.lstrip("#") for l in body.strip().splitlines()))
      assert "environments" in cfg and "test-environments" in cfg
      assert collect_test_environment_errors(cfg) == []

  def test_changelog_unreleased_mentions_feature():
      t = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("## [2.0.0-beta.5]", 1)[0]
      assert "test-environments" in t
  ```
- [ ] **Step 2: Run, erwartet FAIL.** `python3 -m pytest tests/test_test_environments_docs.py --basetemp={{PYTEST_BASETEMP}}`.
- [ ] **Step 3: Dokumente schreiben.** Kapitel deutsch, Beispiele aus Spec §9.1; Platzhalter-Beispiele nur escaped. CHANGELOG unter `[Unreleased]` / `### Added`: `test-environments` (Schema, Validator, Block, 6 Templates + 7 Overrides, Admin-UI, Manager 1.27.0, Szenarien 88-90). Beispiel-Config: kommentierter Block mit Namensabgrenzung zwischen den Markern.
- [ ] **Step 4: Run, erwartet PASS.** Wie Step 2; `python3 scripts/sync.py --validate`.
- [ ] **Step 5: Commit.** `git add docs/guides/features/test-environments.md howto/configs/project.yaml.example CHANGELOG.md docs/RELEASE_GATES.md tests/test_test_environments_docs.py` und `git commit -m "docs: document test environments and approval protocol"`.

---

### Task 15: Baselines und Goldens neu pinnen

**Agent:** tester
**Depends on:** 9, 12, 13, 14
**Files:**
- Modify: `tests/fixtures/ac01-baseline/hashes.json` (nur geänderte Einträge)
- Modify: `tests/test_ac01_render_identity.py` (Rebaseline-Log im Modul-Docstring, vor `Run:`)
- Modify: `tests/test_opencode_v2_surface.py` (eingebettete Fixture-Tree-Digests des `ac01-baseline`)
- Modify: `tests/fixtures/slimming-golden/agent-meta-manager.md`, `tests/test_template_slimming_equivalence.py` (Golden-Rebaseline-Log)

**Interfaces:** Produces: konsistente Baselines nach den Version-Bumps der sechs Templates und der Manager-Änderung. Consumes: `render_matrix_hashes`, `_hash_file` aus `tests/test_ac01_render_identity.py`; dokumentiertes Rebaseline-Verfahren (Docstring ab Zeile 48 von `tests/test_template_slimming_equivalence.py`, AC-01-Log).

- [ ] **Step 1: Drift messen (Rot-Lauf).** `python3 -m pytest tests/test_ac01_render_identity.py tests/test_template_slimming_equivalence.py tests/test_opencode_v2_surface.py --basetemp={{PYTEST_BASETEMP}}` => FAIL. Erwartete Drift-Menge: ausschließlich die Agent-Artefakte der sechs Rollen (nur `version:`-Zeile) und `agent-meta-manager` je Provider plus die zugehörigen `generated-file-hashes.json`-Pfadmengen; dazu das Manager-Golden und die Fixture-Digests. Jede weitere Datei in der Drift ist ein Befund und blockiert den Rebaseline.
- [ ] **Step 2: Nur-Version-Beweis.** `python3 -m pytest tests/test_test_environments_render.py::test_unset_render_matches_baseline --basetemp={{PYTEST_BASETEMP}}` => PASS (die sechs Rollen unterscheiden sich unkonfiguriert nur in `version`/`based-on`).
- [ ] **Step 3: AC-01-Manifest pro Eintrag patchen** (Präzedenz im Log: nicht per `--write`, sondern geänderte Einträge einzeln, Digests unabhängig mit `_hash_file` aus den gerenderten Bytes neu berechnet; Scratch-Verzeichnis unter `{{PYTEST_BASETEMP}}`). Log-Eintrag im Docstring: „Test environments (SPEC-TEST-ENVIRONMENTS-2026-10-31): sechs Rollen-Templates minor-gebumpt (tester 2.9.0, e2e-tester 1.7.0, developer 4.9.0, docker 1.10.0, devops-engineer 1.8.0, test-executor 1.3.0), Gate-Block unkonfiguriert byte-neutral; `agent-meta-manager` 1.27.0 (Rezept). Geändert: N von M Hashes, 0 added/removed; `AC01_EXCEPTIONS` NOT extended.“ (N/M aus der Messung einsetzen).
- [ ] **Step 4: Digests und Golden.** `tests/test_opencode_v2_surface.py`: den Fixture-Tree-Digest des `ac01-baseline` (Test um :2491, Wert aus der Fehlermeldung des Rot-Laufs, aus den Fixture-Bytes neu berechnet) ersetzen und den Kommentarblock ab :5246 um einen Satz ergänzen; `slimming-golden/agent-meta-manager.md` gemäß dokumentiertem Verfahren neu erzeugen (Diff vorher zeilenweise prüfen: nur Rezeptabschnitt, §3-Zeile, Version), Log in `test_template_slimming_equivalence.py` ergänzen. Die Goldens von `developer`, `tester`, `docker`, `devops-engineer`, `e2e-tester` und `test-executor` müssen unverändert bleiben — ändert sich eines, ist das Gate nicht byte-neutral (zurück zu Task 8).
- [ ] **Step 5: Run, erwartet PASS.** Wie Step 1 (grün) und `python3 -m pytest tests/test_test_environments_render.py --basetemp={{PYTEST_BASETEMP}}`.
- [ ] **Step 6: Commit.** `git add tests/fixtures/ac01-baseline/hashes.json tests/test_ac01_render_identity.py tests/test_opencode_v2_surface.py tests/fixtures/slimming-golden/agent-meta-manager.md tests/test_template_slimming_equivalence.py` und `git commit -m "test: rebaseline ac01 manifest and goldens for test environments"`.

---

### Task 16: Real-Sync der eigenen Artefakte und Gesamtlauf

**Agent:** developer
**Depends on:** 15
**Files:**
- Modify: von `python3 scripts/sync.py` erzeugte, versionierte Artefakte (`.claude/agents/*`, weitere Provider-Verzeichnisse, `.meta-config/generated-file-hashes.json`, `.meta-config/context-hashes.json`, soweit im Repo getrackt)

**Interfaces:** Consumes: alle vorigen Tasks. Produces: regenerierte Repo-Artefakte (Change Checklist: „1-generic/<role>.md -> sync affected projects“).

- [ ] **Step 1: Stand prüfen.** `git status --short` — die bereits vor dem Plan modifizierten Hash-Dateien (`.meta-config/context-hashes.json`, `.meta-config/generated-file-hashes.json`) sind erwartet; sonst nichts Unbekanntes.
- [ ] **Step 2: Sync.** `python3 scripts/sync.py` (echt), danach `python3 scripts/sync.py --validate`; `git status --short` listet nur Artefakte der geänderten Rollen (`developer`, `tester`, `e2e-tester`, `docker`, `devops-engineer`, `test-executor`, `agent-meta-manager`, ggf. `agent-meta-developer`) und die Hash-Dateien.
- [ ] **Step 3: Gesamtlauf.** `python3 -m pytest tests/ --basetemp={{PYTEST_BASETEMP}}` und `tests/scenarios/run.sh` => grün (keine neuen Fehlschläge gegenüber `main`).
- [ ] **Step 4: Secret-Scan** der zu committenden Dateien (Projekt-Scan vor jedem Commit); Fund blockiert den Commit.
- [ ] **Step 5: Commit.** `git add <die in Step 2 gelisteten Pfade>` und `git commit -m "chore: regenerate synced artifacts for test environments"`.

---

### Task 17: Self-Review der gesamten Änderung

**Agent:** code-reviewer
**Depends on:** 16
**Files:**
- Modify: keine (read-only Review; Befunde gehen als Liste an den Orchestrator)

**Interfaces:** Produces: Review-Bericht mit Befundliste. Consumes: `git diff main...HEAD`, Spec, dieser Plan.

- [ ] **Step 1: Unveränderlichkeits-Check.** `git diff --stat main...HEAD -- scripts/lib/env.py scripts/lib/mcp.py scripts/lib/hooks.py config/provider-capabilities.yaml scripts/lib/platform.py` ist leer (NZ2, NZ8, NZ9); `settings.json`-Änderungen im Diff nur als Folge des regulären Syncs, nie feature-bedingt (Szenario 89 deckt das ab).
- [ ] **Step 2: Constraint-Check.** `scripts/lib/test_environments.py` <= 600 Zeilen und ohne `provider ==` (Test aus Task 3 grün); `config.py` wächst nur um Import + zwei Aufrufzeilen; Python-3.9-Syntax (kein `X | Y` zur Laufzeit) per `python3 -m pytest tests/test_test_environments_lib.py::test_module_budget_and_constraints --basetemp={{PYTEST_BASETEMP}}`.
- [ ] **Step 3: Spec-Coverage-Check.** Jede Zeile der Tabelle „Spec Coverage“ unten gegen die genannten Tests prüfen; jede Review-Focus-Zeile RF1-RF5 hat ihren Test im genannten Task.
- [ ] **Step 4: Sicherheits-Check.** Grep im Diff nach Token-ähnlichen Literalen, `type: "password"` in `docs/ui/admin-ui.html` (soll 0 Treffer in der neuen View haben), Klartext-URLs mit Userinfo; Freigabe-Texte sagen nirgends „Sperre“ ohne „prompt convention“ (AZ3).
- [ ] **Step 5: Bericht.** Befunde mit Datei:Zeile, Schweregrad und Zuordnung zum Task; ohne Befund „keine offenen Befunde“. Befunde werden vor Task 18 durch die Rolle `developer` über den Orchestrator behoben und mit Conventional Commit nachgezogen.

---

### Task 18: PR-Vorbereitung (kein Merge)

**Agent:** git
**Depends on:** 17
**Files:**
- Create: `.tmp/pr-test-environments.md` (PR-Beschreibung, Sandbox-Pfad, nicht committet)

**Interfaces:** Consumes: Review-Bericht (Task 17). Produces: gepushter Branch und Draft-PR gegen `main`.

- [ ] **Step 1: Historie prüfen.** `git log --oneline main..HEAD` zeigt die Commits der Tasks 1-16 (Conventional Commits, Subject <= 72 Zeichen, kein BOM); `git status --short` sauber.
- [ ] **Step 2: PR-Text.** `.tmp/pr-test-environments.md`: Zusammenfassung (Feature, Opt-in, byte-identisch ohne Block), Liste der geänderten Bereiche, Test-Nachweise (`pytest tests/`, `tests/scenarios/run.sh`, `--validate`), Hinweise (Reihenfolge nach Plan 1, Manager 1.27.0, kein `permissions`-Mechanismus/F6, Folge-Optionen F1-F7), Abweichungsliste dieses Plans.
- [ ] **Step 3: Push und Draft-PR.** `git push -u origin feat/test-environments`; `/home/hermes/.local/bin/gh pr create --draft --base main --title "feat: add test environments with remote approval protocol" --body-file .tmp/pr-test-environments.md` (gh liegt nicht im `$PATH`). Kein Merge, kein Tag.

---

## Spec Coverage

| AC | Kriterium (Kurzform) | Task(s) |
|---|---|---|
| AC-ENV-1 | Ohne Block: 6 Templates + 7 Overrides byte-identisch (außer `version`/`based-on`); `settings.json`/`secrets.local.yaml` unberührt | 1 (Baseline), 8 (`test_unset_render_matches_baseline`, `test_settings_json_identical_and_no_secrets_file`), 9, 15 |
| AC-ENV-2 | Ungültiges Enum, Bool, unbekannter Key => Abbruch im Python-Validator | 2 (Schema), 3, 4 (`test_validate_exits_with_path_message`, `test_load_config_aborts_on_invalid_block`) |
| AC-ENV-3 | Defaults `ask`/`read`/`local` | 5 (`test_defaults_resolve`) |
| AC-ENV-4 | Fallback-URL (HACS > HA), mehrere url-lose / Plattform-Default => „URL not configured“ | 5, 6 (`test_missing_url_marker_and_target_rule`, `test_fallback_url_shows_source`) |
| AC-ENV-5 | Userinfo, `token-env`-Nicht-Name, fehlender/nicht-secret `environments`-Eintrag => Fehler | 3, 4 |
| AC-ENV-6 | Block nennt Namen + Shell-/`env.sh`-Hinweis; kein Token-Wert in Artefakten; `mcp.py`/`env.py`/`secrets.local.yaml` unverändert | 6 (`test_secret_hint_names_only_the_name`), 8 (`test_no_token_value_in_any_generated_file`), 17 (Unveränderlichkeits-Check) |
| AC-ENV-7 | Sechs Rollen enthalten Block, Tabelle, Regeln, Convention-boundary-Satz, Rollenzeile | 6, 8 (`test_configured_render_has_block_table_and_role_line`) |
| AC-ENV-8 | `both` = erst lokal; `ask` = Freigabeprotokoll (Template-Text-Asserts) | 6 (`test_both_requires_local_first`, `test_ask_protocol_texts`), 8 |
| AC-ENV-9 | `deploy`+`deny` => deny gewinnt + Warnung; `deploy` bei `local` => Warnung | 3 (`test_warnings_for_ineffective_or_conflicting_settings`), 6 (`test_deploy_rule_mentions_deny_wins`) |
| AC-ENV-10 | Alle 7 Overrides rendern, Anker lösen auf, `based-on` aktuell, Block außerhalb der Anker; `sharkord-docker` manuell | 9 |
| AC-ENV-11 | (Ersatz) keine `permissions`-Erzeugung, `settings.json` unverändert, kein `if provider ==` | 3 (`test_module_budget_and_constraints`), 8 (`test_settings_json_identical_and_no_secrets_file`), 13 (Szenario 89), 17 |
| AC-ENV-12 | Admin-UI: View, Nav, Router, Help-ID, kein Secret-Feld; Section-Guard 400; Whitelist | 10, 11 |
| AC-ENV-13 | Manager: Rezept, `environments:`-Eintrag mit `secret: true`, Shell-Hinweis, §3-Bestätigung, Version 1.27.0 | 12 |
| AC-ENV-14 | Parität Manager/UI (identisches Fragment) | 12 (`test_recipe_example_is_valid_and_has_parity_with_ui_write`) |
| AC-ENV-15 | Platzhalter in `config.py`, `placeholders.py`, `standalone.py`, `sync-concept.md`; `--validate` ohne ungelöste Platzhalter | 7 |
| AC-ENV-16 | Szenarien `test-env-local`, `test-env-remote-ask`, `test-env-unset` bestehen | 13 |
| AC-ENV-17 | Abgrenzung `environments` vs. `test-environments` in Schema-Description, Doku, Manager, UI | 2, 6 (`test_namensabgrenzung_sentence`), 11, 12, 14 |
| AC-ENV-18 | Neue Module <= 600 Zeilen, Python >= 3.9, stdlib only | 3 (`test_module_budget_and_constraints`), 6, 17 |
| AC-ENV-19 | Ein Satz in `docs/RELEASE_GATES.md` (Dry-Check nur `access: read`) | 14 (`test_release_gates_sentence`) |
| AC-ENV-20 | `ask` nennt `APPROVAL_REQUEST`/`APPROVED`; `deny` verbietet Kontakt + Hinweis an `main_chat`; `allow` verlangt Report über Deploys | 6 (`test_ask_protocol_texts`, `test_deny_text`, `test_allow_text`), 8 |

## Self-Review

- Spec-Coverage: AC-ENV-1..20 jeweils mindestens einem Task mit benanntem Test zugeordnet (Tabelle oben); entfallene Spec-Elemente (CA7/CA11, IC-9, IC-12, WP3, WP5) bleiben entfallen, AC-ENV-11 ist durch die Ersatz-Zusicherung abgedeckt.
- Step-Scan: keine unbestimmten Platzhalter-Wörter und keine abgekürzten Testkörper; Funktionskörper der Implementierung stehen nirgends im Plan, nur Signaturen, Regeln und wörtliche Textbausteine.
- Typ-/Namenskonsistenz: `check_test_environments` (Task 3) -> `collect_test_environment_errors`/`validate_test_environments` (Task 4) -> `resolve_test_environments`/`load_project_platform_vars` (Task 5, Rückgabeschlüssel `kind`, `url`, `url_source`, `token-env`, `access`, `remote-access`, `notes`) -> `render_test_environment_block` (Task 6, verbraucht dieselben Schlüssel) -> `build_test_environment_variables` (Task 7) -> Templates/Overrides (Task 8/9) -> `_guard_test_environments_config/_write` (Task 10, nutzt Task 4); Testhelfer `_sync_project`/`_role_texts`/`_role_of` (Task 1) werden in Task 8/9 wiederverwendet, `_handler`/`_post` (Task 10) in Task 12; keine Referenz auf eine später angelegte Funktion.
- Review Focus: RF1 (Task 3), RF2 (Task 3), RF3 (Task 4), RF4 (Task 3 + 6), RF5 (Task 10) — jeweils mit benanntem Test.
- Proportion: Tasks 1-18 mit je einem eigenen Testzyklus; Template-/Override-Tasks sind parametrisiert statt pro Datei dupliziert; bekannte, bis Task 15 offene Drift (AC-01, Manager-Golden) ist an den betroffenen Tasks (8, 12) ausdrücklich vermerkt.
- Offene Annahmen: Plan 1 ist gemergt (Manager 1.26.0, Szenario-IDs, RELEASE_GATES-Struktur); die Nummer des Manager-Rezeptabschnitts und die Szenario-IDs 88-90 werden zur Ausführungszeit gegen den dann aktuellen Stand geprüft; Dateinamen der gerenderten Agenten (`.claude/agents/*<role>.md`) bestätigt die Baseline in Task 1.
