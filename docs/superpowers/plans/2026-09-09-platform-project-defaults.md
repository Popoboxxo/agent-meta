# Plattform-Presets für project.yaml — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `platform-configs/<name>.defaults.yaml` (already the source of `{{platform.<name>.*}}` template placeholders) also supply platform-typical `dod-preset`/`conventions-preset`/`variables.*` defaults for `project.yaml`, with a clear override cascade (`project.yaml explicit > platform default > framework default`) and explicit additive extension (`<FIELD>+`) — without introducing a new config-file kind.

**Architecture:** One new resolver `resolve_platform_defaults(platforms, platform_config_dir=None) -> dict` in `scripts/lib/platform.py` merges the new `dod-preset`/`conventions-preset`/`variables` top-level sections across every `platforms:` entry (single pass, list order — scalars overwrite, `<FIELD>+` keys append onto whatever the field currently holds). Three call sites consume it: `apply_platform_variable_cascade()` (new, also in `platform.py`, called at the end of `scripts/lib/config.py::build_variables()`) for the curated `variables.*` fields; `scripts/lib/dod.py::resolve_dod_preset_name()` (new, shared by `resolve_dod()` and `config.py`'s `DOD_PRESET` display variable) for `dod-preset`; `scripts/lib/conventions.py::resolve_conventions()` for `conventions-preset`. `sync.py` additionally materializes the merged (pre-project-override) result into `.meta-config/platform-defaults.resolved.yaml`, registered in the existing `.meta-config/generated-file-hashes.json` baseline. `scripts/lib/setup.py`'s wizard pre-fills two questions from the same resolver. Sharkord's pre-existing `{{platform.sharkord.service_name}}`/`{{platform.sharkord.host_lan_ip}}` duplication is cleaned up last, once the generic `{{SERVICE_NAME}}`/`{{HOST_LAN_IP}}` placeholders are cascade-aware.

**Tech Stack:** Python 3.9+ stdlib only (`pathlib`, no new dependencies), PyYAML (already a soft dependency throughout `scripts/lib/`), pytest, Bash (scenario harness, `tests/scenarios/run.sh`).

**Spec:** `docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md` (branch `docs/platform-project-defaults-design`, PR #707).

## Global Constraints

- Python 3.9 floor: any `X | Y` union type hint requires `from __future__ import annotations` as the first statement after the module docstring. Verified present in every file this plan touches: `scripts/lib/platform.py` (L2), `scripts/lib/config.py` (L2), `scripts/lib/conventions.py` (L10), `scripts/lib/sync_pipeline.py` (L28), `scripts/lib/generated_file_drift.py` (L14), `scripts/lib/setup.py` (L6). `scripts/lib/dod.py` does **not** have it — this plan's only new code there (`resolve_dod_preset_name`) uses no `X | Y` syntax, so this is a no-op constraint for that file, not a gap to fix.
- No external Python dependencies — stdlib only (`CLAUDE.md` Code-Konventionen).
- `{{PLACEHOLDER}}` naming is always `{{GROSS_MIT_UNTERSTRICH}}` — no lowercase/mixed case (`rules/2-platform/agent-meta-conventions.md` Hard Invariant #3).
- Provider-agnostic credo: never branch on `if provider == "Name"` in `scripts/lib/*.py` — not applicable to this plan (no provider-specific code touched), stated for completeness.
- `platform-configs/*.defaults.yaml` is **not** covered by `config/project-config.schema.json` (only `.meta-config/project.yaml` is) — the new `dod-preset`/`conventions-preset`/`variables` top-level sections there need no schema change. Verified: `variables.*` in `project.yaml` itself already has a permissive `"additionalProperties": {"type": ["string","boolean","integer","number"]}` (schema L317-324) — the `<FIELD>+` project-override convention and every curated field name (including ones absent from the explicit `properties` list, e.g. `PLATFORM`, `RUNTIME`, `ENTRY_POINT_PATTERN`) already validate cleanly. No schema edits anywhere in this plan.
- `rules/2-platform/agent-meta-conventions.md` Hard Invariant #2: bump `version:` in a changed agent template's frontmatter — Major for renamed variable/changed behavior/new mandatory section, Minor for new optional section, Patch for text improvements/clarifications/config-path fixes. Task 8's `sharkord-docker.md` edit (placeholder rename, no behavior change) is a **Patch** bump.
- Per `tests/scenarios/registry.md`'s own convention ("Jedes neue Feature/jede neue Config-Option bekommt ein eigenes Szenario hier"), this feature needs scenario coverage before the plan is complete (Task 9).
- Byte-identity invariant for projects that never set `platforms:` or set only platforms without the new sections: every existing project's generated output must not change. Verified per-task below (Task 3/4/5's "no platforms" regression tests, Task 9 scenario 28).
- Test invocation convention used throughout this plan: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest <path> -v -o consider_namespace_packages=true` (matches `tests/test_platform_hacs_preset.py`'s documented hint and the `scripts.lib.*` dotted-import style used in `tests/test_config_variable_fallbacks.py`).

---

### Task 1: Platform-Defaults-YAMLs erweitern

**Files:**
- Modify: `platform-configs/hacs.defaults.yaml` (append)
- Modify: `platform-configs/sharkord.defaults.yaml` (append)
- Modify: `platform-configs/homeassistant.defaults.yaml` (append)
- Test: `tests/test_platform_defaults_yaml.py` (new)

**Interfaces:**
- Consumes: nothing new (pure YAML content).
- Produces (for Task 2+): the three files each gain optional top-level `dod-preset` (scalar), `variables` (dict, some keys `+`-suffixed for additive fields). `conventions-preset` is **deliberately omitted from all three** — verified against the real `config/conventions-presets.yaml` (only `default`/`calver`/`conventional-strict` exist; the design spec's own `conventions-preset: docker-service` example for sharkord is illustrative prose, not an existing preset — inventing one is explicitly out of scope per this task's instructions). Documented once here, not repeated per platform.

- [ ] **Step 1: Write the failing tests**

```python
"""Regression tests for the platform-preset cascade fields added to
platform-configs/*.defaults.yaml (Task 1 of the platform-project-defaults
feature). Pure YAML-load-level: verifies shape only, NOT merge semantics
(that's scripts/lib/platform.py::resolve_platform_defaults(), covered by
tests/test_platform_defaults_resolver.py).
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
"""
from __future__ import annotations

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PLATFORM_CONFIGS_DIR = _REPO_ROOT / "platform-configs"


def _load(name: str) -> dict:
    with (_PLATFORM_CONFIGS_DIR / f"{name}.defaults.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_hacs_defaults_have_platform_cascade_fields():
    data = _load("hacs")
    assert data["dod-preset"] == "standard"
    assert "conventions-preset" not in data  # deliberate omission, see plan
    assert isinstance(data["variables"], dict)
    assert data["variables"]["PLATFORM"] == "Home Assistant Custom Component"
    assert data["variables"]["RUNTIME"] == "Python 3.13 (HA Core)"
    assert data["variables"]["PROJECT_LANGUAGES"] == "Python"
    assert data["variables"]["TEST_COMMANDS"] == "pytest tests/ --cov"
    assert data["variables"]["CODE_CONVENTIONS+"] == "Python, ruff, mypy --strict"
    # Existing {{platform.hacs.*}} namespace is untouched (no duplication issue here)
    assert data["platform"]["hacs"]["custom_components_path"] == "custom_components"


def test_sharkord_defaults_migrate_service_name_and_host_lan_ip_into_variables():
    data = _load("sharkord")
    assert data["dod-preset"] == "standard"
    assert "conventions-preset" not in data
    assert isinstance(data["variables"], dict)
    assert data["variables"]["PLATFORM"] == "Sharkord Plugin SDK"
    assert data["variables"]["RUNTIME"] == "Bun"
    assert data["variables"]["PROJECT_LANGUAGES"] == "TypeScript"
    assert data["variables"]["SERVICE_NAME"] == "sharkord"
    assert data["variables"]["CONTAINER_NAME"] == "sharkord"
    assert data["variables"]["HOST_LAN_IP"] == "127.0.0.1"
    assert data["variables"]["TEST_COMMANDS+"] == "docker compose run --rm test"
    assert data["variables"]["CODE_CONVENTIONS+"] == "TypeScript, ESLint, Prettier"
    # Old {{platform.sharkord.*}} namespace stays untouched here -- Task 8 removes
    # the now-duplicate service_name/host_lan_ip sub-keys, not this task.
    assert data["platform"]["sharkord"]["service_name"] == "sharkord"
    assert data["platform"]["sharkord"]["host_lan_ip"] == "127.0.0.1"
    assert data["platform"]["sharkord"]["image_tag"] == "v0.0.16"  # untouched by Task 8 either


def test_homeassistant_defaults_have_platform_cascade_fields():
    data = _load("homeassistant")
    assert data["dod-preset"] == "rapid-prototyping"
    assert "conventions-preset" not in data
    assert isinstance(data["variables"], dict)
    assert data["variables"]["PLATFORM"] == "Home Assistant Automation Config"
    assert data["variables"]["RUNTIME"] == "Home Assistant Core (YAML)"
    assert data["variables"]["PROJECT_LANGUAGES"] == "YAML, Jinja2"
    assert data["variables"]["TEST_COMMANDS"] == "hass --script check_config"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_platform_defaults_yaml.py -v -o consider_namespace_packages=true`
Expected: FAIL with `KeyError: 'dod-preset'` (or similar) on all three tests — the fields don't exist yet.

- [ ] **Step 3: Write the implementation**

Append to `platform-configs/hacs.defaults.yaml` (after the existing `dev_instance_url: ""` line):

```yaml

# =============================================================================
# Platform-preset cascade (project.yaml `dod-preset`/`variables.*` defaults
# for projects with `platforms: [hacs]`). Resolved via
# scripts/lib/platform.py::resolve_platform_defaults() and layered UNDER
# explicit project.yaml values -- project.yaml always wins.
# `<FIELD>+` (see CODE_CONVENTIONS below) appends instead of replacing when
# more than one active platform sets the same field.
#
# conventions-preset: deliberately omitted. config/conventions-presets.yaml
# only defines default/calver/conventional-strict -- HACS integrations
# already match 'default' (SemVer via hacs.json + GitHub releases), so a
# dedicated preset adds no information. Not invented for this feature.
#
# See: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
# =============================================================================

dod-preset: standard

variables:
  PLATFORM: "Home Assistant Custom Component"
  RUNTIME: "Python 3.13 (HA Core)"
  PROJECT_LANGUAGES: "Python"
  TEST_COMMANDS: "pytest tests/ --cov"
  CODE_CONVENTIONS+: "Python, ruff, mypy --strict"
```

Append to `platform-configs/sharkord.defaults.yaml` (after the existing `host_lan_ip: "127.0.0.1"` line):

```yaml

# =============================================================================
# Platform-preset cascade -- see hacs.defaults.yaml's header comment above
# for the mechanism. variables.SERVICE_NAME/CONTAINER_NAME/HOST_LAN_IP below
# migrate the platform.sharkord.service_name/host_lan_ip values above into
# the generic, cascade-aware {{SERVICE_NAME}}/{{HOST_LAN_IP}} placeholders
# (design spec Architektur §1 -- sharkord config duplication). The
# platform.sharkord.* keys above stay UNTOUCHED here -- removing the now-
# redundant service_name/host_lan_ip sub-keys is Task 8, not this task.
#
# conventions-preset: deliberately omitted -- same reasoning as
# hacs.defaults.yaml (sharkord plugins already use SemVer via image_tag,
# i.e. 'default'; no differentiated preset exists to reference).
# =============================================================================

dod-preset: standard

variables:
  PLATFORM: "Sharkord Plugin SDK"
  RUNTIME: "Bun"
  PROJECT_LANGUAGES: "TypeScript"
  SERVICE_NAME: "sharkord"
  CONTAINER_NAME: "sharkord"
  HOST_LAN_IP: "127.0.0.1"
  TEST_COMMANDS+: "docker compose run --rm test"
  CODE_CONVENTIONS+: "TypeScript, ESLint, Prettier"
```

Append to `platform-configs/homeassistant.defaults.yaml` (after the existing `entities_csv_path: "hass_entities.csv"` line):

```yaml

# =============================================================================
# Platform-preset cascade -- see hacs.defaults.yaml's header comment above
# for the mechanism.
#
# dod-preset: rapid-prototyping -- home-automation YAML config projects are
# typically single-maintainer, fast-iteration setups (matches this very
# repo's own dod-preset choice), not the 'standard'/'full' rigor a packaged
# integration (hacs) or a distributed plugin (sharkord) needs.
#
# conventions-preset: deliberately omitted -- there is no packaged release
# in the SemVer/library sense for a home-automation YAML config at all.
# =============================================================================

dod-preset: rapid-prototyping

variables:
  PLATFORM: "Home Assistant Automation Config"
  RUNTIME: "Home Assistant Core (YAML)"
  PROJECT_LANGUAGES: "YAML, Jinja2"
  TEST_COMMANDS: "hass --script check_config"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_platform_defaults_yaml.py -v -o consider_namespace_packages=true`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add platform-configs/hacs.defaults.yaml platform-configs/sharkord.defaults.yaml \
        platform-configs/homeassistant.defaults.yaml tests/test_platform_defaults_yaml.py
git commit -m "feat: add platform-preset cascade fields to platform-configs/*.defaults.yaml"
```

---

### Task 2: `resolve_platform_defaults()` in `scripts/lib/platform.py`

**Files:**
- Modify: `scripts/lib/platform.py` (append)
- Test: `tests/test_platform_defaults_resolver.py` (new)

**Interfaces:**
- Consumes: `load_yaml_file(path: Path, *, on_error: str, default) -> dict` (`scripts/lib/io.py`, already imported in `platform.py` L8).
- Produces (for Task 3/4/5/6/7): `PLATFORM_CONFIGS_DIR = "platform-configs"` (already exists, L11 — reused, not redefined), `_ADDITIVE_JOIN: dict[str, str]`, `resolve_platform_defaults(platforms: list[str], platform_config_dir: Path | None = None) -> dict` returning `{"dod-preset": str | None, "conventions-preset": str | None, "variables": dict[str, str]}`.

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for scripts/lib/platform.py::resolve_platform_defaults() (Task 2
of the platform-project-defaults feature).

Fixture platform-configs live in tmp_path per test -- NEVER against the
real platform-configs/ directory (that's Task 1, covered separately by
tests/test_platform_defaults_yaml.py).
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.platform import resolve_platform_defaults


def _write_defaults(dir_: Path, name: str, content: dict) -> None:
    dir_.mkdir(parents=True, exist_ok=True)
    (dir_ / f"{name}.defaults.yaml").write_text(yaml.dump(content), encoding="utf-8")


def test_single_platform_scalars_pass_through(tmp_path):
    _write_defaults(tmp_path, "hacs", {
        "dod-preset": "standard",
        "variables": {"PLATFORM": "HACS"},
    })
    result = resolve_platform_defaults(["hacs"], tmp_path)
    assert result["dod-preset"] == "standard"
    assert result["conventions-preset"] is None
    assert result["variables"]["PLATFORM"] == "HACS"


def test_two_platforms_same_scalar_key_last_wins(tmp_path):
    _write_defaults(tmp_path, "a", {"variables": {"PLATFORM": "platform-a"}})
    _write_defaults(tmp_path, "b", {"variables": {"PLATFORM": "platform-b"}})
    result = resolve_platform_defaults(["a", "b"], tmp_path)
    assert result["variables"]["PLATFORM"] == "platform-b"


def test_order_sensitivity_swapped_platforms_flip_the_winner(tmp_path):
    _write_defaults(tmp_path, "a", {"variables": {"PLATFORM": "platform-a"}})
    _write_defaults(tmp_path, "b", {"variables": {"PLATFORM": "platform-b"}})
    result = resolve_platform_defaults(["b", "a"], tmp_path)
    assert result["variables"]["PLATFORM"] == "platform-a"


def test_additive_field_set_on_only_one_of_two_platforms(tmp_path):
    _write_defaults(tmp_path, "a", {"variables": {"TEST_COMMANDS+": "cmd-a"}})
    _write_defaults(tmp_path, "b", {"variables": {}})
    result = resolve_platform_defaults(["a", "b"], tmp_path)
    assert result["variables"]["TEST_COMMANDS"] == "cmd-a"


def test_additive_field_set_on_both_platforms_concatenates_in_list_order(tmp_path):
    _write_defaults(tmp_path, "a", {"variables": {"TEST_COMMANDS+": "cmd-a"}})
    _write_defaults(tmp_path, "b", {"variables": {"TEST_COMMANDS+": "cmd-b"}})
    result = resolve_platform_defaults(["a", "b"], tmp_path)
    assert result["variables"]["TEST_COMMANDS"] == "cmd-a && cmd-b"


def test_additive_field_uses_custom_join_char_for_code_conventions(tmp_path):
    _write_defaults(tmp_path, "a", {"variables": {"CODE_CONVENTIONS+": "rule-a"}})
    _write_defaults(tmp_path, "b", {"variables": {"CODE_CONVENTIONS+": "rule-b"}})
    result = resolve_platform_defaults(["a", "b"], tmp_path)
    assert result["variables"]["CODE_CONVENTIONS"] == "rule-a; rule-b"


def test_plain_field_after_additive_field_replaces_it_completely(tmp_path):
    # "<FIELD> ersetzt komplett" (design spec) applies regardless of whether
    # the accumulated value came from a prior scalar OR a prior '+' chain.
    _write_defaults(tmp_path, "a", {"variables": {"TEST_COMMANDS+": "cmd-a"}})
    _write_defaults(tmp_path, "b", {"variables": {"TEST_COMMANDS": "cmd-b"}})
    result = resolve_platform_defaults(["a", "b"], tmp_path)
    assert result["variables"]["TEST_COMMANDS"] == "cmd-b"


def test_unknown_platform_without_defaults_file_does_not_crash(tmp_path):
    result = resolve_platform_defaults(["does-not-exist"], tmp_path)
    assert result == {"dod-preset": None, "conventions-preset": None, "variables": {}}


def test_default_platform_config_dir_resolves_to_real_repo_platform_configs():
    # No platform_config_dir passed -- falls back to <repo_root>/platform-configs.
    result = resolve_platform_defaults(["hacs"])
    assert result["dod-preset"] == "standard"  # from the real Task 1 fixture
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_platform_defaults_resolver.py -v -o consider_namespace_packages=true`
Expected: FAIL with `ImportError: cannot import name 'resolve_platform_defaults' from 'lib.platform'`.

- [ ] **Step 3: Write the implementation**

Append to `scripts/lib/platform.py` (after `substitute_platform`, end of file):

```python
# Fields whose "+"-suffixed variant should be JOINED (not just overridden)
# when more than one platform in `platforms:` sets it. Command-like fields
# default to "&&" (matches the existing "cmd-a && cmd-b" convention already
# used for TEST_COMMANDS in this repo's templates/examples); free-text
# fields get an explicit, more readable join character. Per-field, not
# global (design spec "Offene Implementierungs-Punkte" §3).
_ADDITIVE_JOIN: dict[str, str] = {
    "CODE_CONVENTIONS": "; ",
}


def resolve_platform_defaults(
    platforms: list[str], platform_config_dir: 'Path | None' = None,
) -> dict:
    """Merge dod-preset/conventions-preset/variables across every active
    platform's platform-configs/<name>.defaults.yaml (Task 1's new sections).

    Single pass over `platforms` in list order -- for each platform's
    `variables` entries:
      - a plain key (no `+`) REPLACES whatever the field currently holds
        (from an earlier platform's plain key OR an earlier platform's `+`
        chain) -- "<FIELD> ersetzt komplett" (design spec).
      - a `<FIELD>+` key APPENDS onto whatever the field currently holds,
        using _ADDITIVE_JOIN.get(FIELD, " && ") as the join string; if
        nothing is held yet, it simply becomes the field's value (no
        leading join string) -- "<FIELD>+ hängt an" (design spec).
    Top-level `dod-preset`/`conventions-preset` scalars follow the same
    last-platform-wins rule as plain variables.

    A platform without a matching platform-configs/<name>.defaults.yaml
    file (or an unreadable/malformed one) contributes nothing and is not an
    error -- mirrors load_platform_config()'s "not all platforms need one,
    skip silently" contract (this module, L77-79/84-87).

    platform_config_dir defaults to <agent-meta repo root>/platform-configs
    -- derived from this file's own location (three parents up: lib -> scripts
    -> repo root), a convenience default for callers that don't already
    thread an explicit agent_meta_root (unlike load_platform_config()/
    resolve_dod()/resolve_conventions(), which always receive agent_meta_root
    explicitly and should pass `agent_meta_root / PLATFORM_CONFIGS_DIR` here
    rather than relying on this default).

    Returns {"dod-preset": str | None, "conventions-preset": str | None,
             "variables": dict[str, str]}.
    """
    if platform_config_dir is None:
        platform_config_dir = Path(__file__).resolve().parent.parent.parent / PLATFORM_CONFIGS_DIR

    result: dict = {"dod-preset": None, "conventions-preset": None, "variables": {}}

    for platform in platforms:
        defaults_path = platform_config_dir / f'{platform}.defaults.yaml'
        raw = load_yaml_file(defaults_path, on_error="default", default={})
        if not raw:
            continue

        if "dod-preset" in raw:
            result["dod-preset"] = raw["dod-preset"]
        if "conventions-preset" in raw:
            result["conventions-preset"] = raw["conventions-preset"]

        platform_vars = raw.get("variables", {})
        if not isinstance(platform_vars, dict):
            continue
        for key, value in platform_vars.items():
            if key.endswith("+"):
                field = key[:-1]
                base = result["variables"].get(field, "")
                join_char = _ADDITIVE_JOIN.get(field, " && ")
                result["variables"][field] = f"{base}{join_char}{value}" if base else str(value)
            else:
                result["variables"][key] = value

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_platform_defaults_resolver.py -v -o consider_namespace_packages=true`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/platform.py tests/test_platform_defaults_resolver.py
git commit -m "feat: add resolve_platform_defaults() merge resolver to scripts/lib/platform.py"
```

---

### Task 3: Kaskade in `build_variables()` (`scripts/lib/config.py`)

**Files:**
- Modify: `scripts/lib/platform.py` (append `_CASCADED_VARIABLE_FIELDS` + `apply_platform_variable_cascade`)
- Modify: `scripts/lib/config.py` (import + one call at the end of `build_variables()`, L1300-1303)
- Test: `tests/test_build_variables_platform_cascade.py` (new)

**Interfaces:**
- Consumes: `resolve_platform_defaults(platforms, platform_config_dir) -> dict` (Task 2, same module); `PLATFORM_CONFIGS_DIR` (same module).
- Produces (consumed by `build_variables()`): `apply_platform_variable_cascade(variables: dict, project_config: dict, platforms: list[str], agent_meta_root: Path) -> dict` (mutates and returns `variables`).

**Deliberate signature deviation, documented up front (not a Self-Review afterthought):** the task brief's illustrative signature was `apply_platform_variable_cascade(variables, project_config, platforms) -> dict` (3 args, no `agent_meta_root`). `resolve_platform_defaults()` needs a directory to locate `platform-configs/`, and every sibling `_build_*_variables()` helper already in `config.py` (`_build_platform_variables`, `_build_dod_variables`, `_build_convention_variables`, ...) takes `agent_meta_root` explicitly rather than deriving it from `__file__` — adding it here as a 4th parameter matches that established, explicit-threading convention instead of introducing `__file__`-relative magic into a function that already has the real root available one call away (`build_variables()`'s own `agent_meta_root` parameter).

- [ ] **Step 1: Write the failing tests**

```python
"""Regression tests for the platform-variable cascade in build_variables()
(Task 3 of the platform-project-defaults feature,
scripts/lib/platform.py::apply_platform_variable_cascade()).

Uses the REAL agent-meta repo_root and the real platform-configs/
hacs.defaults.yaml fixture from Task 1 (TEST_COMMANDS: "pytest tests/ --cov",
PROJECT_LANGUAGES: "Python") -- same pattern as the pre-existing
tests/test_config_variable_fallbacks.py (build_variables() against the real
agent-meta checkout, not a synthetic agent_meta_root).
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.config import build_variables

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_explicit_project_override_wins_over_platform_default():
    config = {
        "platforms": ["hacs"],
        "variables": {"TEST_COMMANDS": "custom-test-cmd"},
    }
    variables, _ = build_variables(config, _REPO_ROOT)
    assert variables["TEST_COMMANDS"] == "custom-test-cmd"


def test_plus_suffix_appends_to_platform_default():
    config = {
        "platforms": ["hacs"],
        "variables": {"TEST_COMMANDS+": "hacs-validate ."},
    }
    variables, _ = build_variables(config, _REPO_ROOT)
    assert variables["TEST_COMMANDS"] == "pytest tests/ --cov && hacs-validate ."


def test_platform_default_applies_when_project_sets_nothing():
    config = {"platforms": ["hacs"]}
    variables, _ = build_variables(config, _REPO_ROOT)
    assert variables["TEST_COMMANDS"] == "pytest tests/ --cov"
    assert variables["PROJECT_LANGUAGES"] == "Python"
    assert variables["PLATFORM"] == "Home Assistant Custom Component"


def test_no_platforms_set_leaves_old_behavior_unchanged():
    config = {}
    variables, _ = build_variables(config, _REPO_ROOT)
    # TEST_COMMANDS has no hardcoded framework default anywhere in config.py
    # (unlike DEV_COMMANDS/ARCHITECTURE) -- absent platforms, it stays unset,
    # exactly like before this feature existed.
    assert variables.get("TEST_COMMANDS") is None


def test_field_not_in_curated_list_is_never_platform_cascaded():
    # PROJECT_DESCRIPTION is not in _CASCADED_VARIABLE_FIELDS -- platform
    # defaults must never leak into non-curated fields, even if a platform
    # config happened to define one under the same name.
    config = {"platforms": ["hacs"], "variables": {"PROJECT_DESCRIPTION": "explicit"}}
    variables, _ = build_variables(config, _REPO_ROOT)
    assert variables["PROJECT_DESCRIPTION"] == "explicit"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_build_variables_platform_cascade.py -v -o consider_namespace_packages=true`
Expected: FAIL — `test_explicit_project_override_wins_over_platform_default` etc. fail with `KeyError: 'TEST_COMMANDS'` (cascade not wired in yet); `test_no_platforms_set_leaves_old_behavior_unchanged` and `test_field_not_in_curated_list_is_never_platform_cascaded` already pass (nothing to break yet) — expect 3 failed, 2 passed.

- [ ] **Step 3: Write the implementation**

Append to `scripts/lib/platform.py` (after `resolve_platform_defaults`, end of file):

```python
# Curated field list (design spec "Kuratierte Feldliste v1") -- ONLY these
# variables.* fields are platform-cascaded. Every other project.yaml
# variable stays purely project-individual, no platform coupling.
_CASCADED_VARIABLE_FIELDS = (
    "PLATFORM", "RUNTIME", "LANGUAGE", "PROJECT_LANGUAGES", "SYSTEM_DEPENDENCIES",
    "ENTRY_POINT_PATTERN", "GIT_MAIN_BRANCH", "SERVICE_NAME", "CONTAINER_NAME",
    "HOST_LAN_IP", "TEST_COMMAND", "TEST_COMMANDS", "DEV_COMMANDS",
    "BUILD_COMMAND", "BUILD_COMMANDS", "CODE_CONVENTIONS",
)


def apply_platform_variable_cascade(
    variables: dict, project_config: dict, platforms: list[str], agent_meta_root: 'Path',
) -> dict:
    """Layer platform-config variable defaults under explicit project.yaml
    values, for the curated fields in _CASCADED_VARIABLE_FIELDS only.

    Precedence per field, highest first:
      1. project_config["variables"][FIELD] explicit -> wins unchanged
         (already the value in `variables[FIELD]`, set earlier by
         build_variables()'s own project.yaml `variables:` loop -- left
         untouched here).
      2. project_config["variables"][f"{FIELD}+"] set -> the platform
         default (or whatever `variables[FIELD]` already holds, e.g. a
         framework default like DEV_COMMANDS's "" from build_variables()'s
         core stage, if no platform sets it) + join char + the project's
         `+` value.
      3. resolve_platform_defaults(platforms)["variables"][FIELD] set ->
         wins.
      4. Otherwise: `variables[FIELD]` is left exactly as build_variables()
         already set it (framework default stays the fallback).

    Called once, at the very end of build_variables(), after every other
    variable-building stage -- so stage 4's "whatever variables[FIELD]
    already holds" reflects the full framework-default pipeline, not a
    partial one.
    """
    platform_defaults = resolve_platform_defaults(
        platforms, agent_meta_root / PLATFORM_CONFIGS_DIR,
    )
    platform_vars = platform_defaults.get("variables", {})
    project_vars = project_config.get("variables", {}) or {}

    for field in _CASCADED_VARIABLE_FIELDS:
        if field in project_vars:
            continue  # 1. explicit project override -- already correct in `variables`
        plus_key = f"{field}+"
        if plus_key in project_vars:
            base = platform_vars.get(field, variables.get(field, ""))
            join_char = _ADDITIVE_JOIN.get(field, " && ")
            variables[field] = f"{base}{join_char}{project_vars[plus_key]}" if base else str(project_vars[plus_key])
            continue
        if field in platform_vars:
            variables[field] = str(platform_vars[field])
        # else: leave variables[field] exactly as build_variables() already set it

    return variables
```

Modify `scripts/lib/config.py`: add the import (near the existing `from .conventions import ...` line, L36):

```python
from .conventions import render_convention_block, resolve_conventions
from .platform import apply_platform_variable_cascade
```

Modify `scripts/lib/config.py::build_variables()` tail (currently L1300-1303):

```python
    _build_snippet_variables(variables, agent_meta_root)
    _build_convention_variables(variables, config, agent_meta_root)
    apply_platform_variable_cascade(variables, config, config.get("platforms", []), agent_meta_root)

    return variables, unmapped
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_build_variables_platform_cascade.py -v -o consider_namespace_packages=true`
Expected: 5 passed.

- [ ] **Step 5: Run the full pre-existing config test suite (regression guard)**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_config_variable_fallbacks.py tests/test_platform_hacs_preset.py -v -o consider_namespace_packages=true`
Expected: all pre-existing tests still pass — `apply_platform_variable_cascade` only touches `_CASCADED_VARIABLE_FIELDS`, never `PROJECT_CONTEXT`/`ARCHITECTURE`/`DEV_COMMANDS` (only `DEV_COMMANDS` is curated and only cascades when a platform sets it — hacs/sharkord/homeassistant's Task-1 fixtures never set `DEV_COMMANDS`, so `test_architecture_and_dev_commands_default_to_empty_string_not_missing` is unaffected since that test passes no `platforms:` at all).

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/platform.py scripts/lib/config.py tests/test_build_variables_platform_cascade.py
git commit -m "feat: cascade curated platform-config variables into build_variables()"
```

---

### Task 4: `dod-preset`-Kaskade in `scripts/lib/dod.py`

**Files:**
- Modify: `scripts/lib/dod.py` (new function + `resolve_dod()` edit, current L28-45)
- Modify: `scripts/lib/config.py` (`_build_dod_variables()`, current L1006 — `DOD_PRESET` display variable must use the same resolution, not a separate `config.get("dod-preset", "full")`)
- Modify: `scripts/lib/sync_pipeline.py` (`_sync_stage_config_and_presets()`, current L138 — the DoD summary log line has the same bypass)
- Test: `tests/test_dod_platform_cascade.py` (new)

**Interfaces:**
- Consumes: `resolve_platform_defaults(platforms, platform_config_dir) -> dict`, `PLATFORM_CONFIGS_DIR` (Task 2, `scripts/lib/platform.py`).
- Produces: `resolve_dod_preset_name(config: dict, agent_meta_root: Path) -> str` — the single source of truth for the effective preset NAME, consumed by `resolve_dod()` (this file), `config.py::_build_dod_variables()`'s `DOD_PRESET` variable, and `sync_pipeline.py`'s log line.

**Important finding from research (why 3 files, not 1):** `variables["DOD_PRESET"]` in `config.py` (currently `config.get("dod-preset", "full")`, L1006) is a **separate** read from `resolve_dod()`'s own internal `preset_name` resolution (L37) — it only reads the flat sub-field VALUES from `resolve_dod()`, but computes the displayed preset NAME independently. Without fixing this too, `{{DOD_PRESET}}` in the generated `CLAUDE.md` (`templates/context/claude-managed.md` L8: `DoD-Preset: **{{DOD_PRESET}}**`) would keep showing `"full"` even when a platform default resolves `resolve_dod()`'s actual field values to `"standard"` — an observable inconsistency a user would immediately notice. Factoring the precedence into one shared `resolve_dod_preset_name()` avoids duplicating the 1-liner in three places and keeps them from drifting apart.

- [ ] **Step 1: Write the failing tests**

```python
"""Regression tests for the platform dod-preset cascade
(Task 4 of the platform-project-defaults feature, scripts/lib/dod.py).

Uses the real agent-meta repo_root and the real
platform-configs/hacs.defaults.yaml fixture from Task 1 (dod-preset:
standard). Distinguishing assertions use dod-presets.yaml's real per-preset
field values (config/dod-presets.yaml): full.codebase-overview=True,
standard.tests-required=True/codebase-overview=False,
rapid-prototyping.tests-required=False.
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.dod import resolve_dod, resolve_dod_preset_name

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_explicit_project_dod_preset_wins_over_platform_default():
    config = {"platforms": ["hacs"], "dod-preset": "rapid-prototyping"}
    assert resolve_dod_preset_name(config, _REPO_ROOT) == "rapid-prototyping"
    resolved = resolve_dod(config, _REPO_ROOT)
    assert resolved["tests-required"] is False  # rapid-prototyping, not hacs' 'standard'


def test_platform_dod_preset_wins_when_project_does_not_set_one():
    config = {"platforms": ["hacs"]}
    assert resolve_dod_preset_name(config, _REPO_ROOT) == "standard"
    resolved = resolve_dod(config, _REPO_ROOT)
    assert resolved["tests-required"] is True      # 'standard', not 'full's implicit default
    assert resolved["codebase-overview"] is False   # 'full' would be True here


def test_no_platforms_and_no_override_falls_back_to_full():
    config = {}
    assert resolve_dod_preset_name(config, _REPO_ROOT) == "full"
    resolved = resolve_dod(config, _REPO_ROOT)
    assert resolved["codebase-overview"] is True  # 'full' preset value
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_dod_platform_cascade.py -v -o consider_namespace_packages=true`
Expected: FAIL with `ImportError: cannot import name 'resolve_dod_preset_name' from 'scripts.lib.dod'`.

- [ ] **Step 3: Write the implementation**

Modify `scripts/lib/dod.py`: add the import (after the existing `from .io import _load_yaml_or_json`, L6):

```python
from .io import _load_yaml_or_json
from .platform import PLATFORM_CONFIGS_DIR, resolve_platform_defaults
```

Replace `resolve_dod()` (current L28-45) with:

```python
def resolve_dod_preset_name(config: dict, agent_meta_root: Path) -> str:
    """Resolve the effective dod-preset NAME (not its resolved field
    values -- see resolve_dod() for that).

    Precedence: project.yaml explicit `dod-preset` > platforms: cascade
    default > "full". Shared by resolve_dod() (which resolves preset
    VALUES from this name) and config.py's DOD_PRESET display variable, so
    both stay consistent -- see this task's plan notes for why a single
    shared function exists instead of duplicating the precedence.
    """
    platforms = config.get("platforms", [])
    platform_dod_preset = resolve_platform_defaults(
        platforms, agent_meta_root / PLATFORM_CONFIGS_DIR,
    ).get("dod-preset")
    return config.get("dod-preset") or platform_dod_preset or "full"


def resolve_dod(config: dict, agent_meta_root: Path) -> dict:
    """Resolve effective DoD values from preset + overrides.

    Precedence (highest to lowest):
    1. Project override:  config["dod"][key]
    2. Preset default:    dod-presets.config.yaml[preset][key]
       (preset itself resolved via resolve_dod_preset_name(): project
       `dod-preset` > platforms: cascade default > "full")
    3. "full" preset:     fallback if preset not found
    """
    presets = load_dod_presets(agent_meta_root)
    preset_name = resolve_dod_preset_name(config, agent_meta_root)

    # Fallback to "full" preset when named preset not found
    if preset_name not in presets:
        if preset_name != "full":
            print(f"  !  Unknown dod-preset '{preset_name}' — falling back to 'full'",
                  file=sys.stderr)
        preset_name = "full"

    preset_values = presets.get(preset_name, {})

    dod_overrides = config.get("dod", {})

    # All known DoD keys — sourced from the full preset as authoritative key set
    full_preset = presets.get("full", {
        "req-traceability": True,
        "tests-required": True,
        "codebase-overview": True,
        "security-audit": False,
        "ai-security-review": False,
        "prompt-governance": False,
        "lifecycle-ownership": False,
        "se-required": "false",
    })

    resolved = {}
    for key, default_val in full_preset.items():
        if key == "release-gates":
            continue
        if key in dod_overrides:
            resolved[key] = dod_overrides[key]
        elif key in preset_values:
            resolved[key] = preset_values[key]
        else:
            resolved[key] = default_val
    return resolved
```

(`resolve_release_gates()`, after this in the file, is untouched — it has its own project.yaml override axis per its docstring, out of scope for this feature.)

Modify `scripts/lib/config.py`: add `resolve_dod_preset_name` to the existing `from .dod import resolve_dod` (L38):

```python
from .dod import resolve_dod, resolve_dod_preset_name
```

Modify `scripts/lib/config.py::_build_dod_variables()` (current L1006):

```python
    variables["DOD_PRESET"]           = resolve_dod_preset_name(config, agent_meta_root)
```

Modify `scripts/lib/sync_pipeline.py`: add `resolve_dod_preset_name` to the existing `from lib.dod import resolve_dod, resolve_release_gates` (L56):

```python
from lib.dod import resolve_dod, resolve_dod_preset_name, resolve_release_gates
```

Modify `scripts/lib/sync_pipeline.py::_sync_stage_config_and_presets()` (current L138):

```python
    preset_name = resolve_dod_preset_name(config, agent_meta_root)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_dod_platform_cascade.py -v -o consider_namespace_packages=true`
Expected: 3 passed.

- [ ] **Step 5: Regression check — no-platforms config keeps identical DOD_PRESET**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_config_variable_fallbacks.py -v -o consider_namespace_packages=true`
Expected: still all passing — `resolve_dod_preset_name({}, repo_root)` returns `"full"` exactly like the old `config.get("dod-preset", "full")` did for a `{}` config.

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/dod.py scripts/lib/config.py scripts/lib/sync_pipeline.py \
        tests/test_dod_platform_cascade.py
git commit -m "feat: cascade platform dod-preset defaults through resolve_dod()"
```

---

### Task 5: `conventions-preset`-Kaskade in `scripts/lib/conventions.py`

**Files:**
- Modify: `scripts/lib/conventions.py` (`resolve_conventions()`, current L42-64)
- Test: `tests/test_conventions_platform_cascade.py` (new)

**Interfaces:**
- Consumes: `resolve_platform_defaults(platforms, platform_config_dir) -> dict`, `PLATFORM_CONFIGS_DIR` (Task 2, `scripts/lib/platform.py`).
- Produces: no new public function — `resolve_conventions()`'s existing signature and return shape are unchanged, only its internal `preset_name` resolution gains the platform-cascade stage.

**Test-fixture note:** none of the real `platform-configs/*.defaults.yaml` files set `conventions-preset` (deliberate Task 1 omission — no differentiated real preset exists for any of the three platforms). This task's tests therefore build a small synthetic `agent_meta_root` in `tmp_path`: the REAL `config/conventions-presets.yaml` copied in verbatim (so `default`/`calver`/`conventional-strict` resolve exactly as in production), plus one synthetic `platform-configs/testplat.defaults.yaml` that sets `conventions-preset: calver`.

- [ ] **Step 1: Write the failing tests**

```python
"""Regression tests for the platform conventions-preset cascade
(Task 5 of the platform-project-defaults feature, scripts/lib/conventions.py).

See this task's plan notes for why a synthetic agent_meta_root fixture is
used instead of the real platform-configs/ (none of the three real
platforms sets conventions-preset, by design -- see Task 1).
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
"""
from __future__ import annotations

import shutil
from pathlib import Path

from scripts.lib.conventions import resolve_conventions

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _fake_agent_meta_root(tmp_path: Path) -> Path:
    (tmp_path / "config").mkdir(parents=True)
    shutil.copy(
        _REPO_ROOT / "config" / "conventions-presets.yaml",
        tmp_path / "config" / "conventions-presets.yaml",
    )
    platform_dir = tmp_path / "platform-configs"
    platform_dir.mkdir()
    (platform_dir / "testplat.defaults.yaml").write_text(
        "conventions-preset: calver\n", encoding="utf-8",
    )
    return tmp_path


def test_explicit_project_conventions_preset_wins_over_platform_default(tmp_path):
    root = _fake_agent_meta_root(tmp_path)
    config = {"platforms": ["testplat"], "conventions-preset": "conventional-strict"}
    resolved = resolve_conventions(config, root)
    assert resolved["release"]["changelog"]["format"] == "angular"  # conventional-strict marker


def test_platform_conventions_preset_wins_when_project_does_not_set_one(tmp_path):
    root = _fake_agent_meta_root(tmp_path)
    config = {"platforms": ["testplat"]}
    resolved = resolve_conventions(config, root)
    assert resolved["release"]["versioning"]["scheme"] == "calver"  # platform default 'calver'


def test_no_platforms_and_no_override_falls_back_to_default(tmp_path):
    root = _fake_agent_meta_root(tmp_path)
    config = {}
    resolved = resolve_conventions(config, root)
    assert resolved["release"]["versioning"]["scheme"] == "semver"
    assert resolved["release"]["changelog"]["format"] == "keep-a-changelog"  # 'default' marker
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_conventions_platform_cascade.py -v -o consider_namespace_packages=true`
Expected: FAIL — `test_platform_conventions_preset_wins_when_project_does_not_set_one` fails (`scheme == "semver"` instead of the expected `"calver"`); the other two pass already (they don't exercise the new stage). Expect 1 failed, 2 passed.

- [ ] **Step 3: Write the implementation**

Modify `scripts/lib/conventions.py`: add the import (after the existing `from .io import _deep_merge, _load_yaml_or_json`, L16):

```python
from .io import _deep_merge, _load_yaml_or_json
from .platform import PLATFORM_CONFIGS_DIR, resolve_platform_defaults
```

Modify `resolve_conventions()` (current L42-59, only the `preset_name` line changes):

```python
def resolve_conventions(config: dict, agent_meta_root: Path) -> dict:
    """Resolve effective conventions from preset + project overrides.

    Precedence (highest to lowest):
      1. config["conventions"][domain][field]  — project override
      2. conventions-preset[domain][field]     — preset default, itself
         resolved as: project.yaml explicit `conventions-preset` >
         platforms: cascade default > 'default'
      3. 'default' preset

    Deep-merges the project 'conventions' block over the selected preset,
    per-domain and per-field (same merge semantics as resolve_rules()).

    v1 constraint: for each domain, 'applies_to_roles' must resolve to a list of
    length exactly 1. Raises ValueError (naming the offending domain) if a preset
    or override declares more than one role for a domain — the caller catches
    this, surfaces it via log.warning, and continues with conventions skipped.
    """
    presets = load_conventions_presets(agent_meta_root)
    platforms = config.get("platforms", [])
    platform_conventions_preset = resolve_platform_defaults(
        platforms, agent_meta_root / PLATFORM_CONFIGS_DIR,
    ).get("conventions-preset")
    preset_name = config.get("conventions-preset") or platform_conventions_preset or "default"

    if preset_name not in presets and preset_name != "default":
        print(f"  !  Unknown conventions-preset '{preset_name}' — falling back to 'default'",
              file=sys.stderr)
        preset_name = "default"

    resolved = copy.deepcopy(presets.get(preset_name, {}))
    project_overrides = config.get("conventions", {}) or {}
    _deep_merge(resolved, copy.deepcopy(project_overrides))

    for domain, spec in resolved.items():
        if not isinstance(spec, dict):
            continue
        declared_roles = spec.get("applies_to_roles", [])
        if len(declared_roles) != 1:
            raise ValueError(
                f"conventions domain '{domain}': applies_to_roles must declare "
                f"exactly one role in v1, got {declared_roles!r}"
            )

    return resolved
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_conventions_platform_cascade.py -v -o consider_namespace_packages=true`
Expected: 3 passed.

- [ ] **Step 5: Regression check — the migration-invariant suite stays byte-identical**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_conventions_migration_invariant.py -v -o consider_namespace_packages=true`
Expected: still all passing — that suite never sets `platforms:`, so `resolve_platform_defaults([], ...)` returns `conventions-preset: None`, and `preset_name` resolves exactly as before (`config.get("conventions-preset") or None or "default"`).

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/conventions.py tests/test_conventions_platform_cascade.py
git commit -m "feat: cascade platform conventions-preset defaults through resolve_conventions()"
```

---

### Task 6: Materialisierte Resolved-Datei in `sync.py`

**Files:**
- Modify: `scripts/lib/sync_pipeline.py` (`_sync_stage_config_and_presets()`, current L116-157 — write the file at the end of the function)
- Modify: `scripts/lib/generated_file_drift.py` (register the new file in both `capture_generated_file_hashes()` and `scan_generated_file_drift()`)
- Test: `tests/test_platform_defaults_resolved_file.py` (new)

**Interfaces:**
- Consumes: `resolve_platform_defaults(platforms, platform_config_dir) -> dict`, `PLATFORM_CONFIGS_DIR` (Task 2); `_write_yaml(path: Path, data: dict) -> None` (`scripts/lib/io.py` L341-344, atomic write, consistent YAML formatting — same helper every other generated YAML file in this repo uses); `content_hash(text: str) -> str` (`scripts/lib/io.py` L347-349).
- Produces: `.meta-config/platform-defaults.resolved.yaml` (written on every non-dry-run sync), registered under key `.meta-config/platform-defaults.resolved.yaml` in `.meta-config/generated-file-hashes.json`'s `hashes` dict via the new `PLATFORM_DEFAULTS_RESOLVED_REL` constant.

**Scope note (documented, not hidden):** this task registers the file in the hash baseline (Task 6's literal test requirement) and, for consistency with `generated_file_drift.py`'s stated purpose ("warn when a sync.py-owned file was manually edited"), also wires it into `scan_generated_file_drift()`'s active warning path — a ~6-line symmetric addition, not a new detection mechanism. It deliberately does NOT add a dedicated pytest round-trip test for the warning path itself (edit the file by hand, re-sync, assert a warning fires) — that generic round-trip behavior is already covered for the shared mechanism by its own test suite (`tests/test_generated_file_drift.py`, unrelated to this feature); duplicating it here for one more file would be redundant coverage, not a real gap.

- [ ] **Step 1: Write the failing test**

```python
"""Task 6 (platform-project-defaults feature): .meta-config/
platform-defaults.resolved.yaml is written by every non-dry-run sync.py
run and registered in .meta-config/generated-file-hashes.json.

Runs the real sync.py as a subprocess against a synthetic project dir --
same mechanics as tests/scenarios/run.sh, kept as a pytest test here so it
also runs under a plain `pytest tests/` invocation.
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]

_MINIMAL_PROJECT_YAML = """
agent-meta-version: 0.101.0
ai-providers: [Claude]
platforms: [hacs]
roles: [orchestrator, developer, git]
project:
  name: platform-defaults-test
  prefix: pdt
  short: platform-defaults-test
"""


def test_resolved_file_written_and_registered(tmp_path):
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(_MINIMAL_PROJECT_YAML, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py")],
        cwd=str(tmp_path), capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    resolved_path = tmp_path / ".meta-config" / "platform-defaults.resolved.yaml"
    assert resolved_path.is_file()
    resolved = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
    assert resolved["dod-preset"] == "standard"
    assert resolved["variables"]["TEST_COMMANDS"] == "pytest tests/ --cov"

    hashes_path = tmp_path / ".meta-config" / "generated-file-hashes.json"
    assert hashes_path.is_file()
    hashes = json.loads(hashes_path.read_text(encoding="utf-8"))
    assert ".meta-config/platform-defaults.resolved.yaml" in hashes["hashes"]


def test_resolved_file_not_written_in_dry_run(tmp_path):
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(_MINIMAL_PROJECT_YAML, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"), "--dry-run"],
        cwd=str(tmp_path), capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / ".meta-config" / "platform-defaults.resolved.yaml").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_platform_defaults_resolved_file.py -v -o consider_namespace_packages=true`
Expected: `test_resolved_file_written_and_registered` FAILS (`assert resolved_path.is_file()` → `False`); `test_resolved_file_not_written_in_dry_run` already passes (nothing writes it yet). Expect 1 failed, 1 passed.

- [ ] **Step 3: Write the implementation**

Modify `scripts/lib/sync_pipeline.py`: extend the existing `from lib.io import SyncError, write_atomic` (L75) and `from lib.platform import load_platform_config` (L86):

```python
from lib.io import SyncError, _write_yaml, write_atomic
...
from lib.platform import PLATFORM_CONFIGS_DIR, load_platform_config, resolve_platform_defaults
```

Modify `_sync_stage_config_and_presets()` (current L153-157, the tail of the function):

```python
    # Load platform-config variables ({{platform.*}} placeholders)
    platform_vars = load_platform_config(agent_meta_root, project_root, platforms, log)
    if platform_vars is not None:
        log.note("platform-config", f"loaded {len(platform_vars)} platform variable(s) for: {', '.join(platforms)}")
    # Materialized, human-visible resolved platform-preset defaults (design
    # spec Architektur §4) -- informational only, NOT part of the resolution
    # path itself (apply_platform_variable_cascade()/resolve_dod_preset_name()/
    # resolve_conventions() all call resolve_platform_defaults() directly).
    if not args.dry_run:
        _write_yaml(
            project_root / ".meta-config" / "platform-defaults.resolved.yaml",
            resolve_platform_defaults(platforms, agent_meta_root / PLATFORM_CONFIGS_DIR),
        )
    return config, provider_config, providers, mode, platform_vars
```

Modify `scripts/lib/generated_file_drift.py`: add the new constant (after the existing `DRIFT_ALLOWLIST_FILE = "drift-allowlist.yaml"`, L27):

```python
GENERATED_FILE_HASHES_DIR = ".meta-config"
GENERATED_FILE_HASHES_FILE = "generated-file-hashes.json"
DRIFT_ALLOWLIST_FILE = "drift-allowlist.yaml"
# Task 6 (platform-project-defaults feature): the resolved platform-preset
# snapshot is a generated file too but lives outside every provider's
# managed-index tree (_iter_managed_files only walks agents_dir/rules_dir/
# hooks_dir/commands_dir/skills_dir/pipeline_details_dir) -- registered
# explicitly here rather than teaching _iter_managed_files a project-root-
# level, non-per-provider file shape for a single caller.
PLATFORM_DEFAULTS_RESOLVED_REL = ".meta-config/platform-defaults.resolved.yaml"
```

Modify `capture_generated_file_hashes()` (current L179-197, insert before `_save_hashes`):

```python
def capture_generated_file_hashes(
    agent_meta_root: Path, project_root: Path, config: dict, provider_config: dict, dry_run: bool,
) -> None:
    """Recompute and persist the complete hash baseline from the CURRENT
    on-disk state of every active provider's managed files. Called once,
    at the very end of the sync pipeline, after every writer has run --
    the on-disk content at this point is exactly what the next sync's
    scan_generated_file_drift() call should compare against.
    """
    active_providers = set(get_active_providers(config, provider_config))
    hashes: dict[str, str] = {}
    for provider, pc in provider_config.items():
        if provider not in active_providers:
            continue
        for abs_path in _iter_managed_files(agent_meta_root, project_root, provider, pc):
            rel_path = abs_path.relative_to(project_root).as_posix()
            hashes[rel_path] = content_hash(abs_path.read_text(encoding="utf-8"))
    resolved_path = project_root / PLATFORM_DEFAULTS_RESOLVED_REL
    if resolved_path.is_file():
        hashes[PLATFORM_DEFAULTS_RESOLVED_REL] = content_hash(resolved_path.read_text(encoding="utf-8"))
    _save_hashes(project_root, hashes, dry_run)
```

Modify `scan_generated_file_drift()` (current L145-176, insert before `return findings`):

```python
    stored_hashes = _load_hashes(project_root)
    allowlist = _load_allowlist_patterns(project_root)
    active_providers = set(get_active_providers(config, provider_config))

    findings: list[dict] = []
    for provider, pc in provider_config.items():
        if provider not in active_providers:
            continue
        for abs_path in _iter_managed_files(agent_meta_root, project_root, provider, pc):
            rel_path = abs_path.relative_to(project_root).as_posix()
            stored = stored_hashes.get(rel_path)
            if stored is None:
                continue
            current = content_hash(abs_path.read_text(encoding="utf-8"))
            if current == stored:
                continue
            if is_allowlisted(rel_path, allowlist):
                continue
            findings.append({"path": rel_path, "provider": provider})

    resolved_path = project_root / PLATFORM_DEFAULTS_RESOLVED_REL
    stored_resolved = stored_hashes.get(PLATFORM_DEFAULTS_RESOLVED_REL)
    if stored_resolved is not None and resolved_path.is_file():
        current_resolved = content_hash(resolved_path.read_text(encoding="utf-8"))
        if current_resolved != stored_resolved and not is_allowlisted(PLATFORM_DEFAULTS_RESOLVED_REL, allowlist):
            findings.append({"path": PLATFORM_DEFAULTS_RESOLVED_REL, "provider": "platform-defaults"})

    return findings
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_platform_defaults_resolved_file.py -v -o consider_namespace_packages=true`
Expected: 2 passed.

- [ ] **Step 5: Run the pre-existing drift-detection suite (regression guard)**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_generated_file_drift.py -v -o consider_namespace_packages=true`
Expected: all pre-existing tests still pass — every test there constructs `stored_hashes`/on-disk state without a `.meta-config/platform-defaults.resolved.yaml` present, so `resolved_path.is_file()` is `False` and the new code path is a no-op for all of them.

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/sync_pipeline.py scripts/lib/generated_file_drift.py \
        tests/test_platform_defaults_resolved_file.py
git commit -m "feat: write and hash-register .meta-config/platform-defaults.resolved.yaml"
```

---

### Task 7: Setup-Wizard Pre-Fill

**Files:**
- Modify: `scripts/lib/setup.py` (new helper + two call sites, current L262-292)
- Test: `tests/test_setup_wizard_platform_prefill.py` (new)

**Interfaces:**
- Consumes: `resolve_platform_defaults(platforms, platform_config_dir) -> dict`, `PLATFORM_CONFIGS_DIR` (Task 2, `scripts/lib/platform.py`).
- Produces: `_platform_prefill(agent_meta_root: Path, platforms: list[str], field: str, fallback: str) -> str` — pure, no I/O beyond the YAML read inside `resolve_platform_defaults()`, no stdin/questionary interaction. Kept separate from `_ask()`/`_ask_choice()` specifically so it is unit-testable without mocking the interactive wizard (per this task's own instruction).

- [ ] **Step 1: Write the failing tests**

```python
"""Task 7 (platform-project-defaults feature): pure default-selection
helper for the setup wizard's platform prefill (design spec §5) -- NOT the
full interactive wizard (see tests/test_setup_wizard_secrets_prompt.py for
wizard-level coverage of unrelated fields).
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.setup import _platform_prefill


def test_platform_prefill_uses_platform_default_when_available():
    result = _platform_prefill(_REPO_ROOT, ["hacs"], "TEST_COMMANDS", "bun test")
    assert result == "pytest tests/ --cov"


def test_platform_prefill_falls_back_when_no_platforms():
    result = _platform_prefill(_REPO_ROOT, [], "TEST_COMMANDS", "bun test")
    assert result == "bun test"


def test_platform_prefill_falls_back_when_field_not_set_by_platform():
    result = _platform_prefill(_REPO_ROOT, ["hacs"], "DEV_COMMANDS", "bun run build")
    assert result == "bun run build"


def test_platform_prefill_dod_preset():
    result = _platform_prefill(_REPO_ROOT, ["hacs"], "dod-preset", "standard")
    assert result == "standard"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_setup_wizard_platform_prefill.py -v -o consider_namespace_packages=true`
Expected: FAIL with `ImportError: cannot import name '_platform_prefill' from 'lib.setup'`.

- [ ] **Step 3: Write the implementation**

Modify `scripts/lib/setup.py`: add the helper (after the existing `_section()` function, current L144-148):

```python
def _section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def _platform_prefill(agent_meta_root: Path, platforms: list[str], field: str, fallback: str) -> str:
    """Return the platform-cascaded default for `field` (either the literal
    string "dod-preset" or a variables.<FIELD> key) if `platforms` resolves
    one, else `fallback`.

    Pure helper (Task 7, design spec §5) -- kept separate from the
    interactive _ask()/_ask_choice() calls so it's unit-testable without
    mocking stdin/questionary.
    """
    if not platforms:
        return fallback
    from lib.platform import PLATFORM_CONFIGS_DIR, resolve_platform_defaults
    resolved = resolve_platform_defaults(platforms, agent_meta_root / PLATFORM_CONFIGS_DIR)
    if field == "dod-preset":
        return resolved.get("dod-preset") or fallback
    return resolved.get("variables", {}).get(field) or fallback
```

Modify the two call sites in `run_setup_wizard()` (current L268-273 and L291-292):

```python
        _section("5. Quality Profile (DoD-Preset)")
        print("  INFO: Defines the strictness of the Definition of Done checks.")
        print("  full              — REQ-IDs, tests, CODEBASE_OVERVIEW required")
        print("  standard          — Tests required, REQ-IDs optional")
        print("  rapid-prototyping — All checks disabled for fast iteration")
        dod_preset = _ask_choice(
            "DoD-Preset", ["full", "standard", "rapid-prototyping"],
            default=_platform_prefill(agent_meta_root, platforms, "dod-preset", "standard"),
        )
```

```python
        dev_commands = _ask("Build/Dev Command (DEV_COMMANDS)", default="bun run build")
        test_commands = _ask(
            "Test Command (TEST_COMMANDS)",
            default=_platform_prefill(agent_meta_root, platforms, "TEST_COMMANDS", "bun test"),
        )
```

(`platforms` is already in scope at both call sites — assigned at L266, two lines before the `_section("5. ...")` block starts, and both edited lines sit further down in the same `if do_optional == "yes":` block.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_setup_wizard_platform_prefill.py -v -o consider_namespace_packages=true`
Expected: 4 passed.

- [ ] **Step 5: Regression check — existing wizard tests unaffected**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_setup_wizard_secrets_prompt.py -v -o consider_namespace_packages=true`
Expected: all pre-existing tests still pass — that suite doesn't set `platforms`, so `_platform_prefill` always hits its `if not platforms: return fallback` branch, keeping the previous hardcoded defaults (`"standard"`, `"bun test"`) verbatim.

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/setup.py tests/test_setup_wizard_platform_prefill.py
git commit -m "feat: pre-fill setup-wizard DoD-preset and test-command from platform defaults"
```

---

### Task 8: Sharkord-Duplikate aufräumen

**Files:**
- Modify: `agents/2-platform/sharkord-docker.md` (2 placeholder replacements, current L139 and L157; frontmatter `version:` bump)
- Modify: `platform-configs/sharkord.defaults.yaml` (remove now-redundant `service_name`/`host_lan_ip` sub-keys under `platform.sharkord`)
- Modify: `tests/test_platform_defaults_yaml.py` (Task 1's sharkord test — the two `data["platform"]["sharkord"]["service_name"/"host_lan_ip"]` assertions are now stale, replace with "keys are gone" assertions)
- Test: `tests/test_sharkord_service_name_migration.py` (new)

**Interfaces:**
- Consumes: nothing new — pure template-content + YAML edit.
- Produces: no new public function; `{{HOST_LAN_IP}}` now resolves via Task 3's `apply_platform_variable_cascade()` (already returns `"127.0.0.1"` for `platforms: [sharkord]` once Task 1's `variables.HOST_LAN_IP` fixture is in place) — verified working end-to-end by this task's own test rather than assumed.

**Research finding (grep-verified before writing this task, per the design spec's own instruction to check real call sites first):** `{{platform.sharkord.service_name}}` has **zero** real usages anywhere in the repo (only the design spec's own illustrative comment matches the grep — not a real call site). `{{platform.sharkord.host_lan_ip}}` has exactly **two** real usages, both in `agents/2-platform/sharkord-docker.md`: line 139 (`SHARKORD_WEBRTC_ANNOUNCED_ADDRESS={{platform.sharkord.host_lan_ip}}`) and line 157 (the "Instanziierung" placeholder-fill-in list). The generic `{{SERVICE_NAME}}`/`{{CONTAINER_NAME}}` placeholders are *already* used extensively in that same file (lines 78, 111, 157, etc.) — they simply had no resolvable value before Task 1/3 (no fallback anywhere in `config.py`), so `platforms: [sharkord]` projects that didn't set `variables.SERVICE_NAME` explicitly got a literal unresolved `{{SERVICE_NAME}}` in their generated `docker.md`. This task's Test verifies that pre-existing gap is now closed as a side effect, not just that the old placeholder is gone.

- [ ] **Step 1: Write the failing test**

```python
"""Task 8 (platform-project-defaults feature): sharkord's
{{platform.sharkord.host_lan_ip}} template placeholder migrated to the
generic, platform-cascaded {{HOST_LAN_IP}} (design spec Architektur §1 --
sharkord SERVICE_NAME/HOST_LAN_IP duplication cleanup).

Verified real call sites before writing this test (grep, see plan Task 8
notes): agents/2-platform/sharkord-docker.md lines 139 and 157 were the
ONLY two real usages of {{platform.sharkord.host_lan_ip}} in the whole
repo; {{platform.sharkord.service_name}} had ZERO real usages (only the
design spec's own illustrative comment) -- so only host_lan_ip needed a
template edit; service_name's now-redundant defaults key is removed outright.
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

_PROJECT_YAML = """
agent-meta-version: 0.101.0
ai-providers: [Claude]
platforms: [sharkord]
roles: [orchestrator, docker, git]
project:
  name: sharkord-migration-test
  prefix: smt
  short: sharkord-migration-test
"""


def test_generated_docker_agent_has_no_leftover_platform_namespace_placeholder(tmp_path):
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(_PROJECT_YAML, encoding="utf-8")

    sync_result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py")],
        cwd=str(tmp_path), capture_output=True, text=True, timeout=60,
    )
    assert sync_result.returncode == 0, sync_result.stdout + sync_result.stderr

    validate_result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"), "--validate"],
        cwd=str(tmp_path), capture_output=True, text=True, timeout=60,
    )
    assert validate_result.returncode == 0, validate_result.stdout + validate_result.stderr

    docker_agent = tmp_path / ".claude" / "agents" / "docker.md"
    assert docker_agent.is_file()
    content = docker_agent.read_text(encoding="utf-8")
    assert "{{platform.sharkord.service_name}}" not in content
    assert "{{platform.sharkord.host_lan_ip}}" not in content
    assert "127.0.0.1" in content  # HOST_LAN_IP resolved via the platform cascade (Task 3)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_sharkord_service_name_migration.py -v -o consider_namespace_packages=true`
Expected: FAIL — `assert "{{platform.sharkord.host_lan_ip}}" not in content` fails (the old placeholder is still there, unresolved, since `substitute_platform()` only warns and leaves it in place when no matching key exists — see `scripts/lib/platform.py` L123-127).

- [ ] **Step 3: Write the implementation**

Modify `agents/2-platform/sharkord-docker.md` line 3 (Patch bump — text/placeholder fix, no behavior/section change, per `agent-meta-conventions.md` Hard Invariant #2):

```yaml
version: "1.2.3"
```

Modify `agents/2-platform/sharkord-docker.md` line 139:

```
| Mediasoup verbindet nicht | `SHARKORD_WEBRTC_ANNOUNCED_ADDRESS={{HOST_LAN_IP}}` (LAN-IP, nicht localhost); UDP-Range exposen |
```

Modify `agents/2-platform/sharkord-docker.md` line 157:

```
{{PROJECT_NAME}}, {{PREFIX}}, {{platform.sharkord.image_tag}}, {{SYSTEM_DEPENDENCIES}}, {{SYSTEM_URLS}}, {{PLUGIN_DIR_NAME}}, {{CONTAINER_NAME}}, {{SERVICE_NAME}}, {{PRIMARY_PORT}}, {{EXTRA_PORTS}}, {{BUILD_COMMAND}}, {{HOST_LAN_IP}}, {{EXTRA_VOLUMES}}, {{EXTRA_STARTUP_INFO}}
```

Modify `platform-configs/sharkord.defaults.yaml`: replace the "Docker Compose" and "WebRTC / Mediasoup" sub-sections under `platform: sharkord:` (originally L39-53, now shifted down by Task 1's appended block but still directly following the `min_version` key) with a migration note — keep `image_tag`/`min_version` (still used via `{{platform.sharkord.image_tag}}`) untouched:

```yaml
    # -------------------------------------------------------------------------
    # Release notes
    # -------------------------------------------------------------------------

    # Minimum Sharkord version required by this plugin (for release notes)
    # Example: "0.0.16"
    min_version: "0.0.16"

    # NOTE: service_name/host_lan_ip migrated to variables.SERVICE_NAME/
    # variables.HOST_LAN_IP below (platform-preset cascade, see the header
    # comment further down this file) -- {{SERVICE_NAME}}/{{HOST_LAN_IP}} in
    # templates now resolve via scripts/lib/platform.py::
    # resolve_platform_defaults(), same values as before this migration.
```

Modify `tests/test_platform_defaults_yaml.py`'s `test_sharkord_defaults_migrate_service_name_and_host_lan_ip_into_variables()` (written in Task 1) — replace the three now-stale trailing assertions:

```python
    # Old {{platform.sharkord.*}} namespace stays untouched here -- Task 8 removes
    # the now-duplicate service_name/host_lan_ip sub-keys, not this task.
    assert data["platform"]["sharkord"]["service_name"] == "sharkord"
    assert data["platform"]["sharkord"]["host_lan_ip"] == "127.0.0.1"
    assert data["platform"]["sharkord"]["image_tag"] == "v0.0.16"  # untouched by Task 8 either
```

with:

```python
    # Task 8 migration: service_name/host_lan_ip sub-keys removed from the
    # {{platform.sharkord.*}} namespace (now redundant with variables.* above).
    assert "service_name" not in data["platform"]["sharkord"]
    assert "host_lan_ip" not in data["platform"]["sharkord"]
    assert data["platform"]["sharkord"]["image_tag"] == "v0.0.16"  # untouched
    assert data["platform"]["sharkord"]["min_version"] == "0.0.16"  # untouched
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_sharkord_service_name_migration.py tests/test_platform_defaults_yaml.py -v -o consider_namespace_packages=true`
Expected: 4 passed (1 from the new file, 3 from the updated Task-1 file).

- [ ] **Step 5: Run the pre-existing hacs scenario test suite (regression guard for the collect_* platform-file machinery)**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_platform_hacs_preset.py -v -o consider_namespace_packages=true`
Expected: all pre-existing tests still pass — this task only touches sharkord's files, `role_from_platform_file`/`collect_sources`/`collect_rule_sources` behavior for hacs is untouched.

- [ ] **Step 6: Commit**

```bash
git add agents/2-platform/sharkord-docker.md platform-configs/sharkord.defaults.yaml \
        tests/test_platform_defaults_yaml.py tests/test_sharkord_service_name_migration.py
git commit -m "refactor: migrate sharkord host_lan_ip placeholder to generic {{HOST_LAN_IP}}"
```

---

### Task 9: 10 neue Szenarien (`tests/scenarios/`)

**Files:**
- Create: `tests/scenarios/configs/22-platform-defaults-hacs-passthrough.project.yaml`
- Create: `tests/scenarios/asserts/22-platform-defaults-hacs-passthrough.sh`
- Create: `tests/scenarios/configs/23-platform-defaults-sharkord-explicit-override.project.yaml`
- Create: `tests/scenarios/asserts/23-platform-defaults-sharkord-explicit-override.sh`
- Create: `tests/scenarios/configs/24-platform-defaults-homeassistant-additive.project.yaml`
- Create: `tests/scenarios/asserts/24-platform-defaults-homeassistant-additive.sh`
- Create: `tests/scenarios/configs/25-platform-defaults-order-hacs-sharkord.project.yaml`
- Create: `tests/scenarios/asserts/25-platform-defaults-order-hacs-sharkord.sh`
- Create: `tests/scenarios/configs/26-platform-defaults-order-sharkord-hacs.project.yaml`
- Create: `tests/scenarios/asserts/26-platform-defaults-order-sharkord-hacs.sh`
- Create: `tests/scenarios/configs/27-platform-defaults-additive-three-platforms.project.yaml`
- Create: `tests/scenarios/asserts/27-platform-defaults-additive-three-platforms.sh`
- Create: `tests/scenarios/configs/28-platform-defaults-no-platforms-regression.project.yaml`
- Create: `tests/scenarios/asserts/28-platform-defaults-no-platforms-regression.sh`
- Create: `tests/scenarios/configs/29-platform-defaults-dod-preset-explicit-override.project.yaml`
- Create: `tests/scenarios/asserts/29-platform-defaults-dod-preset-explicit-override.sh`
- Create: `tests/scenarios/configs/30-platform-defaults-dod-preset-platform-fallback.project.yaml`
- Create: `tests/scenarios/asserts/30-platform-defaults-dod-preset-platform-fallback.sh`
- Create: `tests/scenarios/configs/31-platform-defaults-unknown-platform.project.yaml`
- Create: `tests/scenarios/asserts/31-platform-defaults-unknown-platform.sh`
- Modify: `tests/scenarios/registry.md` (append 10 rows to the `## Katalog` table)

**Interfaces:**
- Consumes: `tests/scenarios/run.sh`'s existing discovery contract (any `configs/<name>.project.yaml` + optional executable `asserts/<name>.sh`, no code change to `run.sh` itself needed — pure data addition, matching every prior scenario).
- Produces: nothing consumed elsewhere — these are leaf test fixtures.

**Where each assertion looks (verified real render locations, not guessed):**
- `{{TEST_COMMANDS}}` renders literally in `agents/1-generic/tester.md` (`` `{{TEST_COMMANDS}}`. Build a coverage matrix... `` — L48) → generated `.claude/agents/tester.md`.
- `{{PLATFORM}}` and `{{CODE_CONVENTIONS}}` render in `templates/context/partials/project-metadata.md` (`**Plattform:** {{PLATFORM}}` L9, `## Code-Konventionen\n\n{{CODE_CONVENTIONS}}` L21-23) — part of the always-generated context managed block → generated root `CLAUDE.md`.
- `{{DOD_PRESET}}` renders in `templates/context/claude-managed.md` (`DoD-Preset: **{{DOD_PRESET}}**` L8) → generated root `CLAUDE.md`.
- `.meta-config/platform-defaults.resolved.yaml` (Task 6) is the direct, pre-project-override snapshot — used for scenarios 28/31 where the interesting assertion is "nothing crashed and the cascade is empty/null", not a specific rendered string.

No scenario needs more than `roles: [orchestrator, git]` (+ `tester` where `{{TEST_COMMANDS}}` is the target) and `ai-providers: [Claude]` — single-provider keeps each fixture minimal, matching `01-minimal-claude`'s spirit; multi-provider isolation is already covered by `02-multi-provider` and is not this feature's concern.

- [ ] **Step 1: Scenario 22 — hacs passthrough, no overrides**

`tests/scenarios/configs/22-platform-defaults-hacs-passthrough.project.yaml`:

```yaml
agent-meta-version: 0.101.0
ai-providers:
- Claude
platforms:
- hacs
roles:
- orchestrator
- tester
- git
project:
  name: scenario-platform-hacs-passthrough
  prefix: s22
  short: platform-hacs-passthrough
variables:
  PROJECT_NAME: scenario-platform-hacs-passthrough
  PROJECT_DESCRIPTION: Platform-defaults passthrough test (hacs, no overrides).
  PROJECT_GOAL: Verify hacs' platform-config TEST_COMMANDS/PLATFORM/dod-preset defaults flow through unmodified.
  GIT_PLATFORM: GitHub
  GIT_REMOTE_URL: https://github.com/example/scenario-platform-hacs
  GIT_MAIN_BRANCH: main
rules-preset: default
speech-mode: full
tier-preset: Normal
se-focus: false
max-parallel-agents: 2
conventions-preset: default
debug-mode: false
allow-committed-secrets: false
```

`tests/scenarios/asserts/22-platform-defaults-hacs-passthrough.sh`:

```bash
#!/bin/bash
# Scenario assert for 22-platform-defaults-hacs-passthrough.
#
# Contract (see tests/scenarios/run.sh header): cwd = the scenario's temp
# project dir (the sync output); $1 and env REPO_ROOT both carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (22-platform-defaults-hacs-passthrough): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (22-platform-defaults-hacs-passthrough): $*"
    exit 1
}

[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
grep -q "Plattform:\*\* Home Assistant Custom Component" CLAUDE.md \
    || fail "CLAUDE.md: hacs' platform default PLATFORM not rendered"
grep -q "DoD-Preset: \*\*standard\*\*" CLAUDE.md \
    || fail "CLAUDE.md: hacs' platform default dod-preset 'standard' not rendered"

[ -f ".claude/agents/tester.md" ] || fail "generated file missing: .claude/agents/tester.md"
grep -q "pytest tests/ --cov" .claude/agents/tester.md \
    || fail "tester.md: hacs' platform default TEST_COMMANDS not rendered"

echo "ASSERT OK (22-platform-defaults-hacs-passthrough): hacs platform defaults resolved unmodified"
```

- [ ] **Step 2: Scenario 23 — sharkord, explicit non-additive override wins completely**

`tests/scenarios/configs/23-platform-defaults-sharkord-explicit-override.project.yaml`:

```yaml
agent-meta-version: 0.101.0
ai-providers:
- Claude
platforms:
- sharkord
roles:
- orchestrator
- tester
- git
project:
  name: scenario-platform-sharkord-explicit-override
  prefix: s23
  short: platform-sharkord-override
variables:
  PROJECT_NAME: scenario-platform-sharkord-explicit-override
  PROJECT_DESCRIPTION: Platform-defaults explicit-override test (sharkord).
  PROJECT_GOAL: Verify an explicit project.yaml variables.TEST_COMMANDS (no '+') fully replaces sharkord's platform default, no concatenation.
  TEST_COMMANDS: custom-sharkord-test-cmd
  GIT_PLATFORM: GitHub
  GIT_REMOTE_URL: https://github.com/example/scenario-platform-sharkord-override
  GIT_MAIN_BRANCH: main
rules-preset: default
speech-mode: full
tier-preset: Normal
se-focus: false
max-parallel-agents: 2
conventions-preset: default
debug-mode: false
allow-committed-secrets: false
```

`tests/scenarios/asserts/23-platform-defaults-sharkord-explicit-override.sh`:

```bash
#!/bin/bash
# Scenario assert for 23-platform-defaults-sharkord-explicit-override.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (23-platform-defaults-sharkord-explicit-override): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (23-platform-defaults-sharkord-explicit-override): $*"
    exit 1
}

[ -f ".claude/agents/tester.md" ] || fail "generated file missing: .claude/agents/tester.md"
grep -q "custom-sharkord-test-cmd" .claude/agents/tester.md \
    || fail "tester.md: explicit project TEST_COMMANDS not rendered"
if grep -q "docker compose run --rm test" .claude/agents/tester.md; then
    fail "tester.md: sharkord's platform-default TEST_COMMANDS leaked through despite an explicit project override"
fi

echo "ASSERT OK (23-platform-defaults-sharkord-explicit-override): explicit override replaced the platform default completely"
```

- [ ] **Step 3: Scenario 24 — homeassistant, project `+`-override appends with `&&`**

`tests/scenarios/configs/24-platform-defaults-homeassistant-additive.project.yaml`:

```yaml
agent-meta-version: 0.101.0
ai-providers:
- Claude
platforms:
- homeassistant
roles:
- orchestrator
- tester
- git
project:
  name: scenario-platform-homeassistant-additive
  prefix: s24
  short: platform-ha-additive
variables:
  PROJECT_NAME: scenario-platform-homeassistant-additive
  PROJECT_DESCRIPTION: Platform-defaults additive-override test (homeassistant).
  PROJECT_GOAL: Verify project.yaml variables.TEST_COMMANDS+ appends onto homeassistant's platform default TEST_COMMANDS with an ' && ' join.
  TEST_COMMANDS+: pytest tests/test_automations.py
  GIT_PLATFORM: GitHub
  GIT_REMOTE_URL: https://github.com/example/scenario-platform-ha-additive
  GIT_MAIN_BRANCH: main
rules-preset: default
speech-mode: full
tier-preset: Normal
se-focus: false
max-parallel-agents: 2
conventions-preset: default
debug-mode: false
allow-committed-secrets: false
```

`tests/scenarios/asserts/24-platform-defaults-homeassistant-additive.sh`:

```bash
#!/bin/bash
# Scenario assert for 24-platform-defaults-homeassistant-additive.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (24-platform-defaults-homeassistant-additive): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (24-platform-defaults-homeassistant-additive): $*"
    exit 1
}

[ -f ".claude/agents/tester.md" ] || fail "generated file missing: .claude/agents/tester.md"
grep -q "hass --script check_config && pytest tests/test_automations.py" .claude/agents/tester.md \
    || fail "tester.md: expected concatenated TEST_COMMANDS ('hass --script check_config && pytest tests/test_automations.py') not found"

echo "ASSERT OK (24-platform-defaults-homeassistant-additive): platform default + project '+' override concatenated with '&&'"
```

- [ ] **Step 4: Scenario 25 — order sensitivity, [hacs, sharkord] → sharkord (last) wins**

`tests/scenarios/configs/25-platform-defaults-order-hacs-sharkord.project.yaml`:

```yaml
agent-meta-version: 0.101.0
ai-providers:
- Claude
platforms:
- hacs
- sharkord
roles:
- orchestrator
- git
project:
  name: scenario-platform-order-hacs-sharkord
  prefix: s25
  short: platform-order-hacs-sharkord
variables:
  PROJECT_NAME: scenario-platform-order-hacs-sharkord
  PROJECT_DESCRIPTION: Platform-defaults order-sensitivity test ([hacs, sharkord]).
  PROJECT_GOAL: Verify that with platforms:[hacs, sharkord] the last platform (sharkord) wins for the plain scalar field PLATFORM.
  GIT_PLATFORM: GitHub
  GIT_REMOTE_URL: https://github.com/example/scenario-platform-order-hacs-sharkord
  GIT_MAIN_BRANCH: main
rules-preset: default
speech-mode: full
tier-preset: Normal
se-focus: false
max-parallel-agents: 2
conventions-preset: default
debug-mode: false
allow-committed-secrets: false
```

`tests/scenarios/asserts/25-platform-defaults-order-hacs-sharkord.sh`:

```bash
#!/bin/bash
# Scenario assert for 25-platform-defaults-order-hacs-sharkord.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (25-platform-defaults-order-hacs-sharkord): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (25-platform-defaults-order-hacs-sharkord): $*"
    exit 1
}

[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
grep -q "Plattform:\*\* Sharkord Plugin SDK" CLAUDE.md \
    || fail "CLAUDE.md: expected the LAST platform in the list (sharkord) to win for PLATFORM"
if grep -q "Plattform:\*\* Home Assistant Custom Component" CLAUDE.md; then
    fail "CLAUDE.md: hacs' PLATFORM value leaked through despite sharkord being listed later"
fi

echo "ASSERT OK (25-platform-defaults-order-hacs-sharkord): last-platform-wins confirmed for [hacs, sharkord]"
```

- [ ] **Step 5: Scenario 26 — order sensitivity, [sharkord, hacs] (swapped) → hacs (now last) wins**

`tests/scenarios/configs/26-platform-defaults-order-sharkord-hacs.project.yaml`:

```yaml
agent-meta-version: 0.101.0
ai-providers:
- Claude
platforms:
- sharkord
- hacs
roles:
- orchestrator
- git
project:
  name: scenario-platform-order-sharkord-hacs
  prefix: s26
  short: platform-order-sharkord-hacs
variables:
  PROJECT_NAME: scenario-platform-order-sharkord-hacs
  PROJECT_DESCRIPTION: Platform-defaults order-sensitivity test ([sharkord, hacs], swapped vs. scenario 25).
  PROJECT_GOAL: Verify that swapping the platforms: order flips the winner for the plain scalar field PLATFORM.
  GIT_PLATFORM: GitHub
  GIT_REMOTE_URL: https://github.com/example/scenario-platform-order-sharkord-hacs
  GIT_MAIN_BRANCH: main
rules-preset: default
speech-mode: full
tier-preset: Normal
se-focus: false
max-parallel-agents: 2
conventions-preset: default
debug-mode: false
allow-committed-secrets: false
```

`tests/scenarios/asserts/26-platform-defaults-order-sharkord-hacs.sh`:

```bash
#!/bin/bash
# Scenario assert for 26-platform-defaults-order-sharkord-hacs.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (26-platform-defaults-order-sharkord-hacs): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (26-platform-defaults-order-sharkord-hacs): $*"
    exit 1
}

[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
grep -q "Plattform:\*\* Home Assistant Custom Component" CLAUDE.md \
    || fail "CLAUDE.md: expected the LAST platform in the list (hacs, now swapped last) to win for PLATFORM"
if grep -q "Plattform:\*\* Sharkord Plugin SDK" CLAUDE.md; then
    fail "CLAUDE.md: sharkord's PLATFORM value leaked through despite hacs being listed later"
fi

echo "ASSERT OK (26-platform-defaults-order-sharkord-hacs): swapping the order flipped the winner, confirming order sensitivity"
```

- [ ] **Step 6: Scenario 27 — three platforms, additive field set by exactly two of them**

`tests/scenarios/configs/27-platform-defaults-additive-three-platforms.project.yaml`:

```yaml
agent-meta-version: 0.101.0
ai-providers:
- Claude
platforms:
- hacs
- sharkord
- homeassistant
roles:
- orchestrator
- git
project:
  name: scenario-platform-additive-three-platforms
  prefix: s27
  short: platform-additive-three
variables:
  PROJECT_NAME: scenario-platform-additive-three-platforms
  PROJECT_DESCRIPTION: Platform-defaults additive-merge test across 3 platforms, only 2 set the field.
  PROJECT_GOAL: Verify CODE_CONVENTIONS+ (additive in both hacs and sharkord's platform-configs, absent from homeassistant's) concatenates in list order, with homeassistant contributing nothing.
  GIT_PLATFORM: GitHub
  GIT_REMOTE_URL: https://github.com/example/scenario-platform-additive-three
  GIT_MAIN_BRANCH: main
rules-preset: default
speech-mode: full
tier-preset: Normal
se-focus: false
max-parallel-agents: 2
conventions-preset: default
debug-mode: false
allow-committed-secrets: false
```

`tests/scenarios/asserts/27-platform-defaults-additive-three-platforms.sh`:

```bash
#!/bin/bash
# Scenario assert for 27-platform-defaults-additive-three-platforms.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (27-platform-defaults-additive-three-platforms): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (27-platform-defaults-additive-three-platforms): $*"
    exit 1
}

[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
grep -q "Python, ruff, mypy --strict; TypeScript, ESLint, Prettier" CLAUDE.md \
    || fail "CLAUDE.md: expected CODE_CONVENTIONS concatenation (hacs; sharkord, in list order, '; '-joined) not found"

echo "ASSERT OK (27-platform-defaults-additive-three-platforms): additive field concatenated only the 2 of 3 platforms that set it, in list order"
```

- [ ] **Step 7: Scenario 28 — no `platforms:` key at all (regression guard)**

`tests/scenarios/configs/28-platform-defaults-no-platforms-regression.project.yaml`:

```yaml
agent-meta-version: 0.101.0
ai-providers:
- Claude
roles:
- orchestrator
- git
project:
  name: scenario-platform-no-platforms-regression
  prefix: s28
  short: platform-no-platforms
variables:
  PROJECT_NAME: scenario-platform-no-platforms-regression
  PROJECT_DESCRIPTION: Platform-defaults regression test -- no platforms:  key at all.
  PROJECT_GOAL: Verify sync.py does not crash and the old framework-default behavior (no platform cascade at all) is unchanged when platforms: is entirely absent.
  GIT_PLATFORM: GitHub
  GIT_REMOTE_URL: https://github.com/example/scenario-platform-no-platforms
  GIT_MAIN_BRANCH: main
rules-preset: default
speech-mode: full
tier-preset: Normal
se-focus: false
max-parallel-agents: 2
conventions-preset: default
debug-mode: false
allow-committed-secrets: false
```

`tests/scenarios/asserts/28-platform-defaults-no-platforms-regression.sh`:

```bash
#!/bin/bash
# Scenario assert for 28-platform-defaults-no-platforms-regression.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (28-platform-defaults-no-platforms-regression): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (28-platform-defaults-no-platforms-regression): $*"
    exit 1
}

[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
grep -q "DoD-Preset: \*\*full\*\*" CLAUDE.md \
    || fail "CLAUDE.md: expected the old implicit 'full' dod-preset default (no platforms:, no project override)"

RESOLVED=".meta-config/platform-defaults.resolved.yaml"
[ -f "$RESOLVED" ] || fail "resolved-defaults file missing: $RESOLVED"
python3 - "$RESOLVED" <<'PY' || exit 1
import sys
import yaml

with open(sys.argv[1], encoding="utf-8") as fh:
    data = yaml.safe_load(fh)

if data.get("dod-preset") is not None:
    print(f"ASSERT FAIL (28-platform-defaults-no-platforms-regression): expected dod-preset: null, got {data.get('dod-preset')!r}")
    sys.exit(1)
if data.get("variables"):
    print(f"ASSERT FAIL (28-platform-defaults-no-platforms-regression): expected empty variables, got {data.get('variables')!r}")
    sys.exit(1)
PY

echo "ASSERT OK (28-platform-defaults-no-platforms-regression): absent platforms: key -> empty cascade, old 'full' fallback unchanged"
```

- [ ] **Step 8: Scenario 29 — dod-preset: explicit project override wins over platform default**

`tests/scenarios/configs/29-platform-defaults-dod-preset-explicit-override.project.yaml`:

```yaml
agent-meta-version: 0.101.0
ai-providers:
- Claude
platforms:
- hacs
dod-preset: rapid-prototyping
roles:
- orchestrator
- git
project:
  name: scenario-platform-dod-preset-explicit-override
  prefix: s29
  short: platform-dod-explicit
variables:
  PROJECT_NAME: scenario-platform-dod-preset-explicit-override
  PROJECT_DESCRIPTION: Platform-defaults dod-preset explicit-override test (hacs sets 'standard', project sets 'rapid-prototyping').
  PROJECT_GOAL: Verify project.yaml's explicit dod-preset wins over hacs' platform-config dod-preset.
  GIT_PLATFORM: GitHub
  GIT_REMOTE_URL: https://github.com/example/scenario-platform-dod-explicit
  GIT_MAIN_BRANCH: main
rules-preset: default
speech-mode: full
tier-preset: Normal
se-focus: false
max-parallel-agents: 2
conventions-preset: default
debug-mode: false
allow-committed-secrets: false
```

`tests/scenarios/asserts/29-platform-defaults-dod-preset-explicit-override.sh`:

```bash
#!/bin/bash
# Scenario assert for 29-platform-defaults-dod-preset-explicit-override.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (29-platform-defaults-dod-preset-explicit-override): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (29-platform-defaults-dod-preset-explicit-override): $*"
    exit 1
}

[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
grep -q "DoD-Preset: \*\*rapid-prototyping\*\*" CLAUDE.md \
    || fail "CLAUDE.md: expected the explicit project.yaml dod-preset ('rapid-prototyping') to win over hacs' platform default ('standard')"

echo "ASSERT OK (29-platform-defaults-dod-preset-explicit-override): explicit project dod-preset won over the platform default"
```

- [ ] **Step 9: Scenario 30 — dod-preset: platform default wins over the old implicit "full"**

`tests/scenarios/configs/30-platform-defaults-dod-preset-platform-fallback.project.yaml`:

```yaml
agent-meta-version: 0.101.0
ai-providers:
- Claude
platforms:
- hacs
roles:
- orchestrator
- git
project:
  name: scenario-platform-dod-preset-platform-fallback
  prefix: s30
  short: platform-dod-fallback
variables:
  PROJECT_NAME: scenario-platform-dod-preset-platform-fallback
  PROJECT_DESCRIPTION: Platform-defaults dod-preset fallback test (hacs sets 'standard', project sets nothing).
  PROJECT_GOAL: Verify hacs' platform-config dod-preset ('standard') wins over the old implicit 'full' default when project.yaml does not set dod-preset at all.
  GIT_PLATFORM: GitHub
  GIT_REMOTE_URL: https://github.com/example/scenario-platform-dod-fallback
  GIT_MAIN_BRANCH: main
rules-preset: default
speech-mode: full
tier-preset: Normal
se-focus: false
max-parallel-agents: 2
conventions-preset: default
debug-mode: false
allow-committed-secrets: false
```

`tests/scenarios/asserts/30-platform-defaults-dod-preset-platform-fallback.sh`:

```bash
#!/bin/bash
# Scenario assert for 30-platform-defaults-dod-preset-platform-fallback.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (30-platform-defaults-dod-preset-platform-fallback): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (30-platform-defaults-dod-preset-platform-fallback): $*"
    exit 1
}

[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
grep -q "DoD-Preset: \*\*standard\*\*" CLAUDE.md \
    || fail "CLAUDE.md: expected hacs' platform default dod-preset ('standard') to win, not the old implicit 'full'"
if grep -q "DoD-Preset: \*\*full\*\*" CLAUDE.md; then
    fail "CLAUDE.md: still showing the old implicit 'full' default -- platform dod-preset cascade did not apply"
fi

echo "ASSERT OK (30-platform-defaults-dod-preset-platform-fallback): platform default 'standard' won over the old implicit 'full'"
```

- [ ] **Step 10: Scenario 31 — unknown platform without a defaults file (no crash)**

`tests/scenarios/configs/31-platform-defaults-unknown-platform.project.yaml`:

```yaml
agent-meta-version: 0.101.0
ai-providers:
- Claude
platforms:
- does-not-exist-platform
roles:
- orchestrator
- git
project:
  name: scenario-platform-unknown-platform
  prefix: s31
  short: platform-unknown
variables:
  PROJECT_NAME: scenario-platform-unknown-platform
  PROJECT_DESCRIPTION: Platform-defaults robustness test -- a platform name with no platform-configs/<name>.defaults.yaml file.
  PROJECT_GOAL: Verify sync.py does not crash and resolve_platform_defaults() falls back to an empty cascade, mirroring load_platform_config()'s existing 'skip silently' contract.
  GIT_PLATFORM: GitHub
  GIT_REMOTE_URL: https://github.com/example/scenario-platform-unknown
  GIT_MAIN_BRANCH: main
rules-preset: default
speech-mode: full
tier-preset: Normal
se-focus: false
max-parallel-agents: 2
conventions-preset: default
debug-mode: false
allow-committed-secrets: false
```

`tests/scenarios/asserts/31-platform-defaults-unknown-platform.sh`:

```bash
#!/bin/bash
# Scenario assert for 31-platform-defaults-unknown-platform.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (31-platform-defaults-unknown-platform): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (31-platform-defaults-unknown-platform): $*"
    exit 1
}

[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"

RESOLVED=".meta-config/platform-defaults.resolved.yaml"
[ -f "$RESOLVED" ] || fail "resolved-defaults file missing: $RESOLVED"
python3 - "$RESOLVED" <<'PY' || exit 1
import sys
import yaml

with open(sys.argv[1], encoding="utf-8") as fh:
    data = yaml.safe_load(fh)

if data.get("dod-preset") is not None:
    print(f"ASSERT FAIL (31-platform-defaults-unknown-platform): expected dod-preset: null for an unknown platform, got {data.get('dod-preset')!r}")
    sys.exit(1)
if data.get("conventions-preset") is not None:
    print(f"ASSERT FAIL (31-platform-defaults-unknown-platform): expected conventions-preset: null, got {data.get('conventions-preset')!r}")
    sys.exit(1)
if data.get("variables"):
    print(f"ASSERT FAIL (31-platform-defaults-unknown-platform): expected empty variables, got {data.get('variables')!r}")
    sys.exit(1)
PY

echo "ASSERT OK (31-platform-defaults-unknown-platform): unknown platform -> empty cascade, no crash"
```

- [ ] **Step 11: Make all 10 new assert scripts executable**

```bash
chmod +x tests/scenarios/asserts/22-platform-defaults-hacs-passthrough.sh \
         tests/scenarios/asserts/23-platform-defaults-sharkord-explicit-override.sh \
         tests/scenarios/asserts/24-platform-defaults-homeassistant-additive.sh \
         tests/scenarios/asserts/25-platform-defaults-order-hacs-sharkord.sh \
         tests/scenarios/asserts/26-platform-defaults-order-sharkord-hacs.sh \
         tests/scenarios/asserts/27-platform-defaults-additive-three-platforms.sh \
         tests/scenarios/asserts/28-platform-defaults-no-platforms-regression.sh \
         tests/scenarios/asserts/29-platform-defaults-dod-preset-explicit-override.sh \
         tests/scenarios/asserts/30-platform-defaults-dod-preset-platform-fallback.sh \
         tests/scenarios/asserts/31-platform-defaults-unknown-platform.sh
```

- [ ] **Step 12: Append the 10 new rows to `tests/scenarios/registry.md`'s `## Katalog` table**

Append after the existing `21-auto-commit-off-ignores-config` row:

```markdown
| `22-platform-defaults-hacs-passthrough` | Claude | strict (default) | Platform-preset cascade: hacs defaults flow through unmodified (dod-preset/PLATFORM/TEST_COMMANDS) |
| `23-platform-defaults-sharkord-explicit-override` | Claude | strict (default) | Platform-preset cascade: explicit project `variables.TEST_COMMANDS` fully replaces the platform default |
| `24-platform-defaults-homeassistant-additive` | Claude | strict (default) | Platform-preset cascade: project `variables.TEST_COMMANDS+` appends onto the platform default with `&&` |
| `25-platform-defaults-order-hacs-sharkord` | Claude | strict (default) | Platform-preset cascade: `platforms: [hacs, sharkord]` — last platform (sharkord) wins for a plain scalar |
| `26-platform-defaults-order-sharkord-hacs` | Claude | strict (default) | Platform-preset cascade: swapped order flips the winner (order-sensitivity proof) |
| `27-platform-defaults-additive-three-platforms` | Claude | strict (default) | Platform-preset cascade: 3 platforms, additive field set by only 2 — concatenation excludes the third |
| `28-platform-defaults-no-platforms-regression` | Claude | strict (default) | Platform-preset cascade: no `platforms:` key at all — old framework-default behavior unchanged (regression) |
| `29-platform-defaults-dod-preset-explicit-override` | Claude | strict (default) | Platform-preset cascade: explicit project `dod-preset` wins over the platform default |
| `30-platform-defaults-dod-preset-platform-fallback` | Claude | strict (default) | Platform-preset cascade: platform `dod-preset` wins over the old implicit `"full"` |
| `31-platform-defaults-unknown-platform` | Claude | strict (default) | Platform-preset cascade: unknown platform without a `defaults.yaml` — empty cascade, no crash |
```

- [ ] **Step 13: Run the 10 new scenarios**

Run: `tests/scenarios/run.sh 22 23 24 25 26 27 28 29 30 31`
Expected: `Scenarios: 10  Passed: 10  Failed: 0`.

- [ ] **Step 14: Run the FULL scenario suite (regression guard — 31 scenarios total)**

Run: `tests/scenarios/run.sh`
Expected: `Scenarios: 31  Passed: 31  Failed: 0` — scenarios 1-21 (pre-existing) are unaffected by this feature (none of them set `platforms:` to `hacs`/`sharkord`/`homeassistant` except `04-platform-bundle`, which never asserts on `PLATFORM`/`TEST_COMMANDS`/`dod-preset` values — only marker-file existence, per its own assert script read during planning).

- [ ] **Step 15: Commit**

```bash
git add tests/scenarios/configs/2[2-9]-platform-defaults-*.project.yaml \
        tests/scenarios/configs/3[0-1]-platform-defaults-*.project.yaml \
        tests/scenarios/asserts/2[2-9]-platform-defaults-*.sh \
        tests/scenarios/asserts/3[0-1]-platform-defaults-*.sh \
        tests/scenarios/registry.md
git commit -m "test: add 10 platform-preset-cascade scenarios (22-31)"
```

---

## Self-Review Notes

- **Spec coverage:** every section of the approved design spec (`docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md`) maps to a task — "1. Quelle" (new YAML sections) → Task 1; "2. Resolver" → Task 2; "3. Kaskade in build_variables()" → Task 3, and its two sibling resolvers (`resolve_dod`/`resolve_conventions`, spec's "Analog für dod-preset ... und conventions-preset") → Tasks 4/5; "4. Materialisierte Resolved-Datei" → Task 6; "5. Setup-Wizard" → Task 7; the "Offene Implementierungs-Punkte" list (1: sharkord migration + grep-check, 2: God-Function note, 3: additive join char per field) → Task 8 (point 1, grep-check performed and documented), Task 3 (point 2 — kept `apply_platform_variable_cascade` as a single call appended to `build_variables()` rather than inlining more branches into it, consistent with the spec's "nicht als weiterer Ast" guidance), Task 2 (point 3 — `_ADDITIVE_JOIN` per-field dict). "Tests" section's own worked example (hacs + `TEST_COMMANDS+` → resolved-file assertion) → Task 6's test, generalized into Task 9's fuller matrix.
- **Deviation from the spec's own illustrative example, documented and justified (not silently "fixed"):** the spec's Architektur §1 snippet shows `conventions-preset: docker-service` for sharkord. Verified against the real `config/conventions-presets.yaml` during research — no `docker-service` preset exists (only `default`/`calver`/`conventional-strict`). Task 1 omits `conventions-preset` from all three platforms rather than inventing a preset name, per this feature's own instruction ("keine Presets erfinden"); documented once in Task 1 instead of repeating the caveat three times.
- **Bug found during research and fixed inline in Task 4 (not deferred to this Self-Review section as a discovered-late issue — caught before Task 4 was written):** `config.py`'s `variables["DOD_PRESET"]` (the string actually rendered into `CLAUDE.md`'s `DoD-Preset: **{{DOD_PRESET}}**` line) is a *separate* read from `resolve_dod()`'s internal preset-name resolution — fixing only `resolve_dod()` would have left the *displayed* preset name wrong even though the *resolved field values* (tests-required, etc.) were correct, an easy-to-miss split-brain bug. Solved by factoring both call sites (plus `sync_pipeline.py`'s DoD summary log line, a third bypass found the same way) through one shared `resolve_dod_preset_name()`.
- **Signature deviation from the task brief, documented up front in Task 3 (not hidden):** `apply_platform_variable_cascade()` takes `agent_meta_root` as a 4th parameter, absent from the task brief's illustrative 3-arg signature — required to locate `platform-configs/` and consistent with every sibling `_build_*_variables()` helper in `config.py` (all take `agent_meta_root` explicitly, never `__file__`-derived).
- **Merge-algorithm refinement over the task brief's two-phase description, verified against all 6 requested test cases (Task 2, cases a-f) plus one extra (`test_plain_field_after_additive_field_replaces_it_completely`):** implemented as a single pass instead of two separate scalar/additive phases, so a later platform's plain `<FIELD>` always fully replaces whatever an earlier platform's `<FIELD>+` had accumulated — an ambiguity in the task brief's literal wording ("`<FIELD>` ersetzt komplett" vs. two independent key spaces) resolved in favor of the more literal, more useful reading. Directly enabled Task 9 scenario 27's "concatenation of exactly the two platforms that set it" to be realizable with real (Task 1) fixture data, not synthetic-only.
- **Placeholder scan:** no `TBD`/`FIXME`/"add error handling"-style placeholders in any code block above — every function body is complete, runnable Python; every YAML/Bash snippet is complete and was checked against a real sibling file's format (`18-auto-commit.project.yaml`, `04-platform-bundle.sh`, `2026-09-07-generated-file-drift-detection.md`'s Task-1 structure) before being written here.
- **Type consistency:** `resolve_platform_defaults()`'s return shape (`{"dod-preset": str | None, "conventions-preset": str | None, "variables": dict[str, str]}`) is used identically across Task 3 (`apply_platform_variable_cascade`), Task 4 (`resolve_dod_preset_name`), Task 5 (`resolve_conventions`), Task 6 (`yaml.dump`'d verbatim), and Task 7 (`_platform_prefill`) — no call site assumes a different shape or unwraps it differently.
- **No breaking changes:** every project that does not set `platforms:` (or sets one without the new `dod-preset`/`conventions-preset`/`variables` sections — true for every `platform-configs/*.defaults.yaml` file that predates this feature, and remains true for any third-party/project-local platform file a consumer project might add) gets `resolve_platform_defaults([...])` returning all-`None`/empty, so every touched resolver's precedence chain degrades to exactly its pre-feature behavior (Tasks 3/4/5's dedicated "no platforms" regression tests, Task 9 scenario 28, Task 3/8's regression runs against the pre-existing `test_config_variable_fallbacks.py`/`test_conventions_migration_invariant.py`/`test_platform_hacs_preset.py`/`test_generated_file_drift.py` suites).
