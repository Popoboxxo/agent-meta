# Plugin Catalog Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge `config/external-tools-registry.yaml` and `config/mcp-registry.yaml` into one kind-discriminated `config/plugin-catalog.yaml`, add plugin browse/probe/test capabilities, and fix a pre-existing token-loss bug for providers without a lazy channel — all without changing a single byte of the artifacts generated for the 7 existing entries.

**Architecture:** A new `scripts/lib/plugins.py` owns the unified catalog loader, `kind` split, active-plugin resolution, the per-provider compact decision, and a cheap availability probe. The existing render functions (`_generate_rule_content`, `_generate_tool_rule_content`), provider-config writers and secrets-template stay put; only their *data source* is redirected from the two old YAML files to the kind-filtered catalog, guaranteeing byte-identical output. New surfaces (CLI `--test-plugin`, `POST /api/plugins/<id>/test`, admin-UI "Verfügbare Plugins", sync-time hints, `agent-meta-scout` read access) all consume the one catalog through a shared `run_plugin_test` / `probe_plugin_availability` API.

**Tech Stack:** Python 3.9+, PyYAML (stdlib-only otherwise), pytest, vanilla-JS admin UI (`docs/ui/admin-ui.html`), stdlib `http.server` admin backend.

**Spec:** docs/plans/2026-09-05-plugin-catalog-unification.md

## Global Constraints

- Python 3.9 floor: every NEW `scripts/lib/*.py` module MUST start with `from __future__ import annotations` (enforced by `scripts/lib/consistency/python_compat.py::check_py39_union_syntax` — a `X | Y` annotation without it fails CI's 3.9 job).
- Provider-agnostic credo: NO `if provider == "Name"` branches — dispatch on capability flags / config keys only (`.claude/skills/provider-agnostic/SKILL.md`).
- Byte-identity invariant: for all 7 migrated entries the generated rule-content, skill file and `.mcp.json` MUST be byte-identical before and after migration. The active-server *order* must be preserved too (it determines `.mcp.json` key order → `--check` idempotence).
- No real network / no real process spawning in tests: mock `shutil.which`, `subprocess.run`/`Popen`, `urllib.request.urlopen` (pattern: `tests/test_auto_github_release_hook.py`).
- No manual edits to `.claude/agents/` (generated output). No new `{{PLACEHOLDER}}` without a CLAUDE.md variable-table entry. No breaking change without a major-version bump.
- `python3 scripts/sync.py --validate` and `--dry-run --check` must stay clean (no new warnings, no drift) after every task.
- Test run convention: prefix single-file runs with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` (avoids the `homeassistant` pytest-plugin collision with `scripts/lib`); full-suite runs additionally need `-o consider_namespace_packages=true`.

---

### Task 1: `scripts/lib/plugins.py` core (catalog loader + kind split + compact helper + probe)

**Files:**
- Create: `scripts/lib/plugins.py`
- Test: `tests/test_plugins_core.py`

**Interfaces:**
- Consumes: `scripts/lib/io.py::_load_yaml_or_json`, `_deep_merge`, `_normalize_enabled_config`.
- Produces (used by every later task — exact signatures):
  - `PLUGIN_CATALOG_YAML = "config/plugin-catalog.yaml"` (module constant)
  - `load_plugin_catalog(agent_meta_root: Path, config: dict | None = None, project_root: Path | None = None) -> dict` → `{plugin_id: plugin_def}`, all kinds, project overrides deep-merged.
  - `plugins_of_kind(catalog: dict, kind: str) -> dict` → subset whose `kind` equals `kind`.
  - `_plugin_is_active(plugin_id: str, plugin_def: dict, activation: dict) -> bool`
  - `resolve_active_plugins(config: dict, agent_meta_root: Path, project_root: Path | None = None, catalog: dict | None = None) -> list[str]`
  - `provider_has_lazy_channel(pc: dict) -> bool`
  - `resolve_plugin_compact(global_compact: bool, pcs: list[dict]) -> bool`
  - `probe_plugin_availability(plugin_def: dict) -> bool`

- [ ] **Step 1: Write the failing test**
```python
# tests/test_plugins_core.py
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.plugins import (  # noqa: E402
    PLUGIN_CATALOG_YAML,
    _plugin_is_active,
    plugins_of_kind,
    probe_plugin_availability,
    provider_has_lazy_channel,
    resolve_plugin_compact,
)

_CATALOG = {
    "graphify": {"kind": "cli-tool", "enabled-by-default": False},
    "viz-logger": {"kind": "mcp-server", "enabled-by-default": True},
    "honcho": {"kind": "mcp-server", "enabled-by-default": False},
}


def test_constant_points_at_new_catalog_file():
    assert PLUGIN_CATALOG_YAML == "config/plugin-catalog.yaml"


def test_plugins_of_kind_filters_by_discriminator():
    mcp = plugins_of_kind(_CATALOG, "mcp-server")
    assert set(mcp) == {"viz-logger", "honcho"}
    assert set(plugins_of_kind(_CATALOG, "cli-tool")) == {"graphify"}


def test_plugin_is_active_precedence():
    # explicit project setting wins over the registry default
    assert _plugin_is_active("honcho", _CATALOG["honcho"], {"honcho": {"enabled": True}}) is True
    assert _plugin_is_active("viz-logger", _CATALOG["viz-logger"], {"viz-logger": {"enabled": False}}) is False
    # fall back to enabled-by-default
    assert _plugin_is_active("viz-logger", _CATALOG["viz-logger"], {}) is True
    assert _plugin_is_active("honcho", _CATALOG["honcho"], {}) is False


def test_provider_has_lazy_channel():
    assert provider_has_lazy_channel({"has_rules": True}) is True
    assert provider_has_lazy_channel({"capabilities": ["agents", "skills"]}) is True
    # ZCode/KimiCode shape: no rules, no skills capability -> no lazy channel
    assert provider_has_lazy_channel({"capabilities": ["agents", "mcp"]}) is False
    assert provider_has_lazy_channel({}) is False


def test_resolve_plugin_compact_convergence_safe():
    has = {"has_rules": True}
    none = {"capabilities": ["mcp"]}
    assert resolve_plugin_compact(True, [has]) is True
    assert resolve_plugin_compact(True, [none]) is False          # no lazy channel -> force full
    assert resolve_plugin_compact(True, [has, none]) is False     # any shared user lacks it -> full
    assert resolve_plugin_compact(False, [has]) is False          # global full always wins


def test_probe_local_binary(monkeypatch):
    import lib.plugins as plugins
    monkeypatch.setattr(plugins.shutil, "which", lambda name: "/usr/bin/graphify" if name == "graphify" else None)
    assert probe_plugin_availability({"availability-probe": "command-v", "binary": "graphify"}) is True
    assert probe_plugin_availability({"availability-probe": "command-v", "binary": "nope"}) is False
    assert probe_plugin_availability({"availability-probe": "always"}) is True
    assert probe_plugin_availability({"availability-probe": "none"}) is False
```
- [ ] **Step 2: Run test to verify it fails**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_plugins_core.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'lib.plugins'`
- [ ] **Step 3: Write minimal implementation**
```python
# scripts/lib/plugins.py
"""Unified plugin catalog: loads config/plugin-catalog.yaml (kind-discriminated
mcp-server / cli-tool entries), resolves which plugins are active for a project,
decides the per-provider compact/full channel, and runs a cheap availability
probe. Replaces the two separate registry loaders (config/mcp-registry.yaml,
config/external-tools-registry.yaml) — see mcp_registry.py / external_tools.py,
whose loaders now source from here (kind-filtered) so rendered artifacts stay
byte-identical.
"""
from __future__ import annotations

import shutil
import urllib.request
from pathlib import Path

from .io import _deep_merge, _load_yaml_or_json, _normalize_enabled_config

PLUGIN_CATALOG_YAML = "config/plugin-catalog.yaml"


def load_plugin_catalog(
    agent_meta_root: Path,
    config: dict | None = None,
    project_root: Path | None = None,
) -> dict:
    """Load config/plugin-catalog.yaml and deep-merge project overrides.

    Sources (later wins, deep-merged):
      1. Framework: <agent_meta_root>/config/plugin-catalog.yaml
      2. Project:   <project_root>/.meta-config/plugin-catalog.yaml
      3. Inline:    config["plugin-catalog"] from project.yaml
    Returns a flat {plugin_id: plugin_def} dict.
    """
    data, _ = _load_yaml_or_json(agent_meta_root / PLUGIN_CATALOG_YAML)
    catalog: dict = {}
    if data and isinstance(data, dict):
        catalog = data.get("plugins", {})
        if not isinstance(catalog, dict):
            catalog = {}

    if project_root:
        proj_data, _ = _load_yaml_or_json(project_root / ".meta-config" / "plugin-catalog.yaml")
        if proj_data and isinstance(proj_data, dict):
            proj_plugins = proj_data.get("plugins", proj_data)
            if isinstance(proj_plugins, dict):
                _deep_merge(catalog, proj_plugins)

    if config:
        inline = config.get("plugin-catalog", {})
        if isinstance(inline, dict):
            _deep_merge(catalog, inline)

    return catalog


def plugins_of_kind(catalog: dict, kind: str) -> dict:
    """Return the subset of catalog whose 'kind' discriminator equals kind."""
    return {
        pid: pdef
        for pid, pdef in catalog.items()
        if isinstance(pdef, dict) and pdef.get("kind") == kind
    }


def _plugin_is_active(plugin_id: str, plugin_def: dict, activation: dict) -> bool:
    """True if plugin should render. Mirrors external_tools._tool_is_active:
    explicit project activation[plugin_id]['enabled'] wins, else the catalog's
    enabled-by-default, else False (opt-in)."""
    if plugin_id in activation and "enabled" in activation[plugin_id]:
        return bool(activation[plugin_id]["enabled"])
    if "enabled-by-default" in plugin_def:
        return bool(plugin_def["enabled-by-default"])
    return False


def _activation_from_config(config: dict) -> dict:
    """Resolve the canonical activation dict. Prefers the unified `plugins:`
    block; falls back to the legacy `mcp-servers:` list + `external-tools:`
    dict for un-migrated project.yaml files."""
    plugins_cfg = config.get("plugins")
    if plugins_cfg is not None:
        return _normalize_enabled_config(plugins_cfg)
    legacy = {s: {"enabled": True} for s in config.get("mcp-servers", []) or []}
    legacy.update(_normalize_enabled_config(config.get("external-tools", {})))
    return legacy


def resolve_active_plugins(
    config: dict,
    agent_meta_root: Path,
    project_root: Path | None = None,
    catalog: dict | None = None,
) -> list[str]:
    """All active plugin ids (any kind), catalog order. Used by the browse/probe/
    scout/test features — NOT by artifact generation (those keep the per-kind
    resolvers whose order is byte-identity-sensitive)."""
    if catalog is None:
        catalog = load_plugin_catalog(config=config, agent_meta_root=agent_meta_root, project_root=project_root)
    activation = _activation_from_config(config)
    return [pid for pid, pdef in catalog.items()
            if isinstance(pdef, dict) and _plugin_is_active(pid, pdef, activation)]


def provider_has_lazy_channel(pc: dict) -> bool:
    """True if the provider has a lazy (non-always-on) channel for full plugin
    content: a native rules dir OR the skills capability. Providers with
    neither (ZCode, KimiCode) must never receive the compact-only variant, or
    the full agent-hint is silently lost (spec status-quo gap)."""
    return bool(pc.get("has_rules")) or ("skills" in (pc.get("capabilities") or []))


def resolve_plugin_compact(global_compact: bool, pcs: list[dict]) -> bool:
    """Convergence-safe compact decision for embedded plugin content. Compact
    only when the project opted in AND every provider sharing the target
    context_file has a lazy channel — otherwise force full embedding (spec
    provider-agnostik fix; mirrors the #638 shared-file union rule)."""
    return global_compact and all(provider_has_lazy_channel(pc) for pc in pcs)


def probe_plugin_availability(plugin_def: dict) -> bool:
    """Cheap, side-effect-free reachability check for the sync-time hint
    (Layer 3). Never spawns a long-lived process or sends auth."""
    probe = plugin_def.get("availability-probe", "none")
    if probe == "always":
        return True
    if probe == "command-v":
        binary = plugin_def.get("binary") or (plugin_def.get("connection", {}) or {}).get("command", "")
        return bool(binary) and shutil.which(binary) is not None
    if probe == "npx-resolve":
        return shutil.which("npx") is not None
    if probe == "http-head":
        url = (plugin_def.get("connection", {}) or {}).get("url", "")
        if not url:
            return False
        try:
            req = urllib.request.Request(url, method="HEAD")  # noqa: S310 (curated catalog URL)
            with urllib.request.urlopen(req, timeout=3):  # noqa: S310
                return True
        except Exception:  # noqa: BLE001 - any failure means "not reachable"
            return False
    return False
```
- [ ] **Step 4: Run test to verify it passes**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_plugins_core.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add scripts/lib/plugins.py tests/test_plugins_core.py
git commit -m "feat: add unified plugin-catalog core module (plugins.py)"
```

---

### Task 2: `config/plugin-catalog.yaml` seed + frozen legacy fixtures + byte-identity invariant test

**Files:**
- Create: `config/plugin-catalog.yaml`
- Create: `tests/fixtures/legacy-registries/mcp-registry.yaml` (frozen verbatim copy of current `config/mcp-registry.yaml`)
- Create: `tests/fixtures/legacy-registries/external-tools-registry.yaml` (frozen verbatim copy of current `config/external-tools-registry.yaml`)
- Test: `tests/test_plugin_catalog_migration_invariant.py`

**Interfaces:**
- Consumes: `lib.plugins.load_plugin_catalog`, `lib.plugins.plugins_of_kind`; the render functions still living at `lib.mcp._generate_rule_content` and `lib.external_tools._generate_tool_rule_content` (unchanged in this task).
- Produces: the on-disk catalog every later task loads. Data contract: each entry carries the exact keys of its legacy counterpart PLUS `kind` (`mcp-server`|`cli-tool`), `origin-type`, `availability-probe`.

- [ ] **Step 1: Write the failing test**
```python
# tests/test_plugin_catalog_migration_invariant.py
"""Byte-identity migration invariant: the unified plugin-catalog must carry the
exact same per-entry data as the two legacy registries (frozen fixtures), and
must render byte-identical rule-content for every one of the 7 pre-existing
entries. Mirrors tests/test_conventions_migration_invariant.py (#521).
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.external_tools import _generate_tool_rule_content  # noqa: E402
from lib.mcp import _generate_rule_content  # noqa: E402
from lib.plugins import load_plugin_catalog, plugins_of_kind  # noqa: E402

_FIX = REPO_ROOT / "tests" / "fixtures" / "legacy-registries"
_LEGACY_MCP = yaml.safe_load((_FIX / "mcp-registry.yaml").read_text())["mcp-servers"]
_LEGACY_TOOLS = yaml.safe_load((_FIX / "external-tools-registry.yaml").read_text())["external-tools"]

# Keys the catalog adds on top of the legacy schema (ignored by all renderers).
_ADDED_KEYS = {"kind", "origin-type", "availability-probe", "binary"}


def _catalog():
    return load_plugin_catalog(agent_meta_root=REPO_ROOT)


def test_all_seven_legacy_entries_present():
    catalog = _catalog()
    for name in list(_LEGACY_MCP) + list(_LEGACY_TOOLS):
        assert name in catalog, f"{name} missing from plugin-catalog.yaml"


def test_mcp_entry_data_is_byte_identical():
    mcp = plugins_of_kind(_catalog(), "mcp-server")
    for name, legacy_def in _LEGACY_MCP.items():
        migrated = {k: v for k, v in mcp[name].items() if k not in _ADDED_KEYS}
        assert migrated == legacy_def, f"{name} data drifted from legacy registry"


def test_cli_tool_entry_data_is_byte_identical():
    tools = plugins_of_kind(_catalog(), "cli-tool")
    for name, legacy_def in _LEGACY_TOOLS.items():
        migrated = {k: v for k, v in tools[name].items() if k not in _ADDED_KEYS}
        assert migrated == legacy_def, f"{name} data drifted from legacy registry"


def test_rendered_rule_content_is_byte_identical():
    catalog = _catalog()
    for name, legacy_def in _LEGACY_MCP.items():
        assert _generate_rule_content(name, catalog[name]) == _generate_rule_content(name, legacy_def)
    for name, legacy_def in _LEGACY_TOOLS.items():
        got = _generate_tool_rule_content(name, catalog[name], {}, REPO_ROOT)
        want = _generate_tool_rule_content(name, legacy_def, {}, REPO_ROOT)
        assert got == want


def test_project_atlas_seed_present_and_disabled():
    catalog = _catalog()
    assert catalog["project-atlas"]["kind"] == "mcp-server"
    assert catalog["project-atlas"]["enabled-by-default"] is False
```
- [ ] **Step 2: Run test to verify it fails**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_plugin_catalog_migration_invariant.py -v`
Expected: FAIL — fixtures + `config/plugin-catalog.yaml` do not exist yet (`FileNotFoundError` / empty catalog).
- [ ] **Step 3: Write minimal implementation**
Freeze the current registries as fixtures verbatim (they still exist at this point — do NOT edit them):
```bash
mkdir -p tests/fixtures/legacy-registries
cp config/mcp-registry.yaml tests/fixtures/legacy-registries/mcp-registry.yaml
cp config/external-tools-registry.yaml tests/fixtures/legacy-registries/external-tools-registry.yaml
```
Then create `config/plugin-catalog.yaml` by lifting each legacy entry 1:1 under a top-level `plugins:` map, prepending `kind`/`origin-type`/`availability-probe` (and `binary` for cli-tools). The value fields (`description`, `category`, `tools`, `agent-hint`, `connection`, `secrets`, `hooks`, `rule-content`, `permitted-injections`, `provider-skip`, `enabled-by-default`) are copied EXACTLY from the fixtures. Header + the 8 entries:
```yaml
version: 1.0.0
plugins:
  home-assistant:
    kind: mcp-server
    origin-type: remote-saas
    availability-probe: http-head
    # --- fields below copied verbatim from legacy mcp-registry.yaml ---
    description: Home Assistant real-time device status, sensors, datetime and read-only
      data
    category: iot
    enabled-by-default: false
    tools:
      allowed: [GetLiveContext, GetDateTime, todo_get_items]
      blocked: [HassTurnOn, HassTurnOff, HassLightSet, HassCallService, HassSetVolume,
        HassBroadcast, HassMediaPlay, HassMediaPause]
    agent-hint: |
      # (copy the exact multiline agent-hint scalar from the fixture — do not reflow)
    connection:
      type: sse
      url: '{{MCP_HA_URL}}/api/mcp'
      headers:
        Authorization: Bearer {{MCP_HA_TOKEN}}
    secrets: [MCP_HA_URL, MCP_HA_TOKEN]
  influxdb:
    kind: mcp-server
    origin-type: local-process
    availability-probe: npx-resolve
    # ... verbatim influxdb fields ...
  viz-logger:
    kind: mcp-server
    origin-type: repo-owned-process
    availability-probe: always
    # ... verbatim viz-logger fields (enabled-by-default: true) ...
  a2a-handoff:
    kind: mcp-server
    origin-type: repo-owned-process
    availability-probe: always
    # ... verbatim a2a-handoff fields (enabled-by-default: true) ...
  honcho:
    kind: mcp-server
    origin-type: remote-saas
    availability-probe: http-head
    # ... verbatim honcho fields incl. provider-skip: [Opencode] ...
  reqogniloom:
    kind: mcp-server
    origin-type: remote-saas
    availability-probe: http-head
    # ... verbatim reqogniloom fields (full tools.allowed/blocked lists) ...
  playwright:
    kind: mcp-server
    origin-type: local-process
    availability-probe: npx-resolve
    # ... verbatim playwright fields ...
  graphify:
    kind: cli-tool
    origin-type: local-binary
    availability-probe: command-v
    binary: graphify
    # ... verbatim graphify fields (description, category, enabled-by-default,
    #     provider-skip, rule-content, hooks, permitted-injections) ...
  project-atlas:
    kind: mcp-server
    origin-type: local-process
    availability-probe: command-v
    binary: project-atlas
    description: >-
      Project Atlas — local MCP-based repo knowledge-graph tool
      (https://github.com/styler-ai/ProjectAtlas). Placeholder entry; exact
      connection.command/args verified at first real integration.
    category: dev-tool
    enabled-by-default: false
    tools:
      allowed: []
    connection:
      type: stdio
      command: project-atlas
      args: [--mcp]
    secrets: []
```
The invariant test's `test_*_data_is_byte_identical` and `test_rendered_rule_content_is_byte_identical` are the guardrail — iterate on the YAML until both pass, which proves each copied field is exact (including the multiline `agent-hint` scalars: copy them verbatim, do not reflow).
- [ ] **Step 4: Run test to verify it passes**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_plugin_catalog_migration_invariant.py -v`
Expected: PASS (all 5 tests)
- [ ] **Step 5: Commit**
```bash
git add config/plugin-catalog.yaml tests/fixtures/legacy-registries tests/test_plugin_catalog_migration_invariant.py
git commit -m "feat: seed unified plugin-catalog.yaml + migration invariant test"
```

---

### Task 3: Redirect the two registry loaders to the catalog (kind-filtered), keep order byte-identical

**Files:**
- Modify: `scripts/lib/mcp_registry.py:25-89` (`load_mcp_registry`, `resolve_active_mcp_servers`)
- Modify: `scripts/lib/external_tools.py:119-209` (`load_external_tools_registry`, `resolve_active_external_tools`)
- Test: `tests/test_plugin_loader_redirect.py`

**Interfaces:**
- Consumes: `lib.plugins.load_plugin_catalog`, `plugins_of_kind`, `_activation_from_config`.
- Produces: unchanged public signatures — `load_mcp_registry(agent_meta_root, config=None, project_root=None) -> dict`, `resolve_active_mcp_servers(config, agent_meta_root, project_root=None, registry=None) -> list[str]`, `load_external_tools_registry(...) -> dict`, `resolve_active_external_tools(...) -> list[str]`. Return shapes and ordering are identical to before, so all existing callers (sync.py, context.py, rules.py, agent_sync.py, admin-server.py, drift) and their tests keep working.

- [ ] **Step 1: Write the failing test**
```python
# tests/test_plugin_loader_redirect.py
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.external_tools import load_external_tools_registry, resolve_active_external_tools  # noqa: E402
from lib.mcp import load_mcp_registry, resolve_active_mcp_servers  # noqa: E402


def test_load_mcp_registry_sources_from_catalog():
    reg = load_mcp_registry(REPO_ROOT)
    # only mcp-server kind, cli-tools excluded
    assert "viz-logger" in reg and "honcho" in reg
    assert "graphify" not in reg


def test_load_external_tools_registry_sources_from_catalog():
    reg = load_external_tools_registry(REPO_ROOT)
    assert "graphify" in reg
    assert "honcho" not in reg


def test_active_server_order_preserved_for_legacy_config():
    # agent-meta's legacy activation order must be reproduced exactly:
    # explicit list order, then bundle additions -> byte-identical .mcp.json.
    config = {"mcp-servers": ["honcho", "playwright", "reqogniloom"], "platforms": ["agent-meta"]}
    active = resolve_active_mcp_servers(config, REPO_ROOT)
    assert active == ["honcho", "playwright", "reqogniloom", "viz-logger"]


def test_active_servers_from_unified_plugins_block_match_legacy():
    legacy = {"mcp-servers": ["honcho", "playwright", "reqogniloom"], "platforms": ["agent-meta"]}
    unified = {
        "plugins": {"honcho": {"enabled": True}, "playwright": {"enabled": True},
                    "reqogniloom": {"enabled": True}, "graphify": {"enabled": True}},
        "platforms": ["agent-meta"],
    }
    assert resolve_active_mcp_servers(unified, REPO_ROOT) == resolve_active_mcp_servers(legacy, REPO_ROOT)
    assert resolve_active_external_tools(unified, REPO_ROOT) == ["graphify"]
```
- [ ] **Step 2: Run test to verify it fails**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_plugin_loader_redirect.py -v`
Expected: FAIL — `load_mcp_registry` still returns cli-tools/`graphify` absent-check passes by accident but `test_active_servers_from_unified_plugins_block_match_legacy` fails (loaders still read old YAML, `plugins:` block ignored).
- [ ] **Step 3: Write minimal implementation**
In `scripts/lib/mcp_registry.py`, replace the body of `load_mcp_registry` so it filters the catalog, and teach `resolve_active_mcp_servers` to honour the `plugins:` block:
```python
# top of mcp_registry.py, after existing imports
from .plugins import _activation_from_config, load_plugin_catalog, plugins_of_kind

def load_mcp_registry(agent_meta_root, config=None, project_root=None):
    """Return the mcp-server slice of the unified plugin catalog (same shape as
    the old config/mcp-registry.yaml `mcp-servers` map)."""
    catalog = load_plugin_catalog(agent_meta_root=agent_meta_root, config=config, project_root=project_root)
    return plugins_of_kind(catalog, "mcp-server")
```
In `resolve_active_mcp_servers`, replace the two lines that build `explicit`/`active` from `config["mcp-servers"]` with an activation-aware version that preserves order (`plugins:` dict order, else legacy list order), keeping the platform-bundle loop below verbatim:
```python
    if registry is None:
        registry = load_mcp_registry(agent_meta_root, config, project_root)
    if config.get("plugins") is not None:
        activation = _activation_from_config(config)
        ordered = [pid for pid, v in activation.items()
                   if v.get("enabled") and pid in registry]
    else:
        ordered = list(config.get("mcp-servers", []))
    explicit: set[str] = set(ordered)
    active: list[str] = list(ordered)
    # ... existing platform-bundle loop unchanged ...
```
In `scripts/lib/external_tools.py`, replace `load_external_tools_registry`'s body with the catalog slice, and make `resolve_active_external_tools` read the `plugins:` block (falling back to `external-tools`):
```python
from .plugins import _activation_from_config, load_plugin_catalog, plugins_of_kind

def load_external_tools_registry(agent_meta_root, config=None, project_root=None):
    catalog = load_plugin_catalog(agent_meta_root=agent_meta_root, config=config, project_root=project_root)
    registry = plugins_of_kind(catalog, "cli-tool")
    for tool_name, tool_def in registry.items():
        if isinstance(tool_def, dict) and "permitted-injections" in tool_def:
            _validate_permitted_injections(tool_name, tool_def["permitted-injections"])
    return registry
```
And in `resolve_active_external_tools`, source `project_tools` from the unified activation:
```python
    if registry is None:
        registry = load_external_tools_registry(agent_meta_root, config, project_root)
    if (config or {}).get("plugins") is not None:
        project_tools = _activation_from_config(config)
    else:
        project_tools = _normalize_enabled_config((config or {}).get("external-tools", {}))
    # ... existing registry-order loop unchanged ...
```
Note the import direction: `plugins.py` does NOT import `mcp_registry`/`external_tools`, so these new top-level imports form no cycle.
- [ ] **Step 4: Run test to verify it passes**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_plugin_loader_redirect.py tests/test_mcp_config.py tests/test_external_tools_registry.py tests/test_plugin_catalog_migration_invariant.py -v`
Expected: PASS (redirect + all pre-existing registry/config tests still green)
- [ ] **Step 5: Commit**
```bash
git add scripts/lib/mcp_registry.py scripts/lib/external_tools.py tests/test_plugin_loader_redirect.py
git commit -m "refactor: source mcp/external-tool registries from unified catalog"
```

---

### Task 4: Provider-agnostik compact/full fix (close the ZCode/KimiCode token-loss gap)

**Files:**
- Modify: `scripts/lib/context.py:1079` and the two embed call sites `context.py:1123-1125` (mcp) and `context.py:1152-1155` (tool)
- Test: `tests/test_plugin_compact_provider_fix.py`

**Interfaces:**
- Consumes: `lib.plugins.resolve_plugin_compact` (Task 1).
- Produces: no new public API — behavioural change only. `_generate_rule_content` / `_generate_tool_rule_content` are still called with a `compact` bool; the bool is now per-shared-provider-set instead of global.

- [ ] **Step 1: Write the failing test**
```python
# tests/test_plugin_compact_provider_fix.py
"""ZCode/KimiCode have no lazy channel (no rules, no skills capability): under
project-wide compact mode they must still receive the FULL embedded plugin
content, or the agent-hint is silently lost. Regression for the spec gap.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.plugins import resolve_plugin_compact  # noqa: E402
from lib.providers import load_providers_config  # noqa: E402


def test_zcode_and_kimicode_forced_full_under_compact():
    pc = load_providers_config(REPO_ROOT)
    assert resolve_plugin_compact(True, [pc["ZCode"]]) is False
    assert resolve_plugin_compact(True, [pc["KimiCode"]]) is False
    # Claude has a native rules dir -> compact honoured
    assert resolve_plugin_compact(True, [pc["Claude"]]) is True
    # Opencode has the skills capability -> lazy channel -> compact honoured
    assert resolve_plugin_compact(True, [pc["Opencode"]]) is True
    # shared AGENTS.md mixing Opencode + ZCode -> convergence-safe full
    assert resolve_plugin_compact(True, [pc["Opencode"], pc["ZCode"]]) is False
```
- [ ] **Step 2: Run test to verify it fails**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_plugin_compact_provider_fix.py -v`
Expected: This unit test PASSES already (it only exercises Task-1 code). Add the *integration* assertion below FIRST so the step has a failing state — insert into the same file:
```python
def test_embedded_context_keeps_agent_hint_for_no_lazy_provider(tmp_path):
    # Build the ZCode context and assert the honcho agent-hint prose survives
    # even with context_file.mode: compact set.
    import lib.context as context
    from lib.config import load_config
    config = load_config(REPO_ROOT / ".meta-config" / "project.yaml")
    config["context_file"] = {"mode": "compact"}
    config.setdefault("mcp-servers", []).append("honcho")
    pc = load_providers_config(REPO_ROOT)
    hints = context.build_agent_hints_for_provider(  # helper introduced in Step 3 wiring
        "ZCode", config, REPO_ROOT, pc, project_root=REPO_ROOT,
    ) if hasattr(context, "build_agent_hints_for_provider") else ""
    assert "get_context" in hints  # a phrase only present in the full agent-hint
```
Expected now: FAIL — the context embed still passes the global `_compact` (compact drops the agent-hint) OR the helper is absent.
> Note: if wiring a full `build_agent_hints_for_provider` call is impractical, keep only the unit assertions on `resolve_plugin_compact` and drop this integration case — the unit test fully covers the decision logic. Decide during implementation; do not leave a non-runnable test behind.
- [ ] **Step 3: Write minimal implementation**
In `scripts/lib/context.py`, add the import near the other deferred `from .mcp import ...` (line ~1085) or at top with the lib imports:
```python
from .plugins import resolve_plugin_compact
```
Replace line 1079:
```python
        _global_compact = local_vars.get("COMPACT_MODE") == "true"
        _compact_pcs = (
            [provider_config[p] for p in shared_users]
            if provider_config else [pc]
        )
        _compact = resolve_plugin_compact(_global_compact, _compact_pcs)
```
The existing embed loops already pass `compact=_compact` to `_generate_rule_content` (line 1124) and `_generate_tool_rule_content` (line 1153) — no further change needed there. The plain-rules `compact_embedded_rule` call at line 1111-1114 keeps using `_global_compact` (that compaction is density-only on agent-meta's own always-on rules, not the plugin lazy-channel loss this fix targets — leave it on the global flag).
- [ ] **Step 4: Run test to verify it passes**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_plugin_compact_provider_fix.py tests/test_context_compact_mode.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add scripts/lib/context.py tests/test_plugin_compact_provider_fix.py
git commit -m "fix: force full embedded plugin content for providers without a lazy channel"
```

---

### Task 5: `scripts/lib/plugin_test.py` — health check per origin-type (mocked)

**Files:**
- Create: `scripts/lib/plugin_test.py`
- Test: `tests/test_plugin_test.py`

**Interfaces:**
- Consumes: nothing from earlier tasks at runtime except the plugin_def shape produced in Task 2 (`origin-type`, `connection`, `secrets`, `binary`).
- Produces: `run_plugin_test(plugin_id: str, plugin_def: dict, secrets: dict | None = None) -> dict` returning `{"status": "PASS"|"FAIL"|"UNKNOWN", "message": str, "latency_ms": int}`. This exact name/signature is reused verbatim by Task 6 (CLI) and Task 7 (admin endpoint).

- [ ] **Step 1: Write the failing test**
```python
# tests/test_plugin_test.py
"""run_plugin_test dispatches per origin-type. All process/HTTP calls are
mocked — no real network, no real subprocess (pattern: test_auto_github_release_hook).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import lib.plugin_test as pt  # noqa: E402
from lib.plugin_test import run_plugin_test  # noqa: E402


def test_local_binary_pass(monkeypatch):
    monkeypatch.setattr(pt.shutil, "which", lambda n: "/usr/bin/graphify")
    monkeypatch.setattr(pt, "_run_version", lambda binary: (True, "graphify 1.2.3"))
    res = run_plugin_test("graphify", {"origin-type": "local-binary", "binary": "graphify"})
    assert res["status"] == "PASS"
    assert "1.2.3" in res["message"]
    assert isinstance(res["latency_ms"], int)


def test_local_binary_missing(monkeypatch):
    monkeypatch.setattr(pt.shutil, "which", lambda n: None)
    res = run_plugin_test("graphify", {"origin-type": "local-binary", "binary": "graphify"})
    assert res["status"] == "FAIL"
    assert "not found" in res["message"].lower()


def test_local_process_handshake(monkeypatch):
    monkeypatch.setattr(pt, "_mcp_initialize_handshake",
                        lambda cmd, args, env: (True, "initialize ok"))
    pdef = {"origin-type": "local-process",
            "connection": {"type": "stdio", "command": "npx", "args": ["-y", "x"]}}
    res = run_plugin_test("influxdb", pdef)
    assert res["status"] == "PASS"


def test_remote_saas_reachable(monkeypatch):
    monkeypatch.setattr(pt, "_http_probe", lambda url, headers: (200, "OK"))
    pdef = {"origin-type": "remote-saas",
            "connection": {"type": "sse", "url": "https://x/mcp",
                           "headers": {"Authorization": "Bearer {{TOK}}"}}}
    res = run_plugin_test("honcho", pdef, secrets={"TOK": "secret"})
    assert res["status"] == "PASS"


def test_remote_saas_401_is_reachable(monkeypatch):
    monkeypatch.setattr(pt, "_http_probe", lambda url, headers: (401, "Unauthorized"))
    pdef = {"origin-type": "remote-saas", "connection": {"type": "sse", "url": "https://x/mcp"}}
    res = run_plugin_test("honcho", pdef)
    assert res["status"] == "PASS"  # 401 still means the endpoint answered


def test_remote_saas_refused(monkeypatch):
    def _boom(url, headers):
        raise ConnectionRefusedError("refused")
    monkeypatch.setattr(pt, "_http_probe", _boom)
    pdef = {"origin-type": "remote-saas", "connection": {"type": "sse", "url": "https://x/mcp"}}
    res = run_plugin_test("honcho", pdef)
    assert res["status"] == "FAIL"


def test_unknown_origin_type():
    res = run_plugin_test("mystery", {"origin-type": "quantum"})
    assert res["status"] == "UNKNOWN"
```
- [ ] **Step 2: Run test to verify it fails**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_plugin_test.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'lib.plugin_test'`
- [ ] **Step 3: Write minimal implementation**
```python
# scripts/lib/plugin_test.py
"""Active health-check for a single plugin, dispatched by origin-type. Shared by
`sync.py --test-plugin` (CLI) and admin-server `POST /api/plugins/<id>/test`
(HTTP) so both surfaces exercise one implementation. The three I/O seams
(_run_version, _mcp_initialize_handshake, _http_probe) are module-level so tests
mock them without real subprocess/network.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
import urllib.request

_SECRET_RE = re.compile(r"\{\{(\w+)\}\}")
_TIMEOUT = 8


def _resolve_secrets(text: str, secrets: dict) -> str:
    return _SECRET_RE.sub(lambda m: str(secrets.get(m.group(1), m.group(0))), text)


def _run_version(binary: str) -> tuple[bool, str]:
    try:
        out = subprocess.run([binary, "--version"], capture_output=True, text=True,
                             timeout=_TIMEOUT)  # noqa: S603
        msg = (out.stdout or out.stderr or "").strip().splitlines()
        return out.returncode == 0, (msg[0] if msg else f"{binary} present")
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def _mcp_initialize_handshake(command: str, args: list, env: dict) -> tuple[bool, str]:
    """Start the stdio MCP process, send an `initialize` request, read one line,
    terminate. Returns (ok, message)."""
    proc = None
    try:
        proc = subprocess.Popen([command, *args], stdin=subprocess.PIPE,  # noqa: S603
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                text=True, env=env or None)
        req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                          "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                     "clientInfo": {"name": "agent-meta", "version": "1"}}})
        proc.stdin.write(req + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        return ("result" in line or "jsonrpc" in line), "initialize responded"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    finally:
        if proc and proc.poll() is None:
            proc.terminate()


def _http_probe(url: str, headers: dict) -> tuple[int, str]:
    req = urllib.request.Request(url, headers=headers or {}, method="HEAD")  # noqa: S310
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:  # noqa: S310
        return resp.status, "reachable"


def _result(status: str, message: str, started: float) -> dict:
    return {"status": status, "message": message,
            "latency_ms": int((time.monotonic() - started) * 1000)}


def run_plugin_test(plugin_id: str, plugin_def: dict, secrets: dict | None = None) -> dict:
    """Test one plugin's reachability. status in {PASS, FAIL, UNKNOWN}."""
    secrets = secrets or {}
    started = time.monotonic()
    origin = plugin_def.get("origin-type")
    conn = plugin_def.get("connection", {}) or {}

    if origin == "local-binary":
        binary = plugin_def.get("binary") or plugin_id
        if shutil.which(binary) is None:
            return _result("FAIL", f"binary '{binary}' not found on PATH", started)
        ok, msg = _run_version(binary)
        return _result("PASS" if ok else "FAIL", msg, started)

    if origin in ("local-process", "repo-owned-process"):
        env = {_resolve_secrets(k, secrets): _resolve_secrets(str(v), secrets)
               for k, v in (conn.get("env") or {}).items()}
        ok, msg = _mcp_initialize_handshake(conn.get("command", ""), conn.get("args", []), env)
        return _result("PASS" if ok else "FAIL", msg, started)

    if origin == "remote-saas":
        url = _resolve_secrets(conn.get("url", ""), secrets)
        headers = {k: _resolve_secrets(str(v), secrets) for k, v in (conn.get("headers") or {}).items()}
        try:
            code, _ = _http_probe(url, headers)
        except Exception as exc:  # noqa: BLE001 - refused/timeout/etc = not reachable
            return _result("FAIL", f"not reachable: {exc}", started)
        reachable = code < 500 or code == 401
        return _result("PASS" if reachable else "FAIL", f"HTTP {code}", started)

    return _result("UNKNOWN", f"no test strategy for origin-type '{origin}'", started)
```
- [ ] **Step 4: Run test to verify it passes**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_plugin_test.py -v`
Expected: PASS (7 tests)
- [ ] **Step 5: Commit**
```bash
git add scripts/lib/plugin_test.py tests/test_plugin_test.py
git commit -m "feat: add plugin health-check (plugin_test.run_plugin_test)"
```

---

### Task 6: `sync.py --test-plugin <id>` CLI flag

**Files:**
- Modify: `scripts/sync.py:485-616` (`_build_arg_parser` — add flag) and `scripts/sync.py:627` (early-return dispatch in `_build_context`)
- Test: `tests/test_sync_test_plugin_cli.py`

**Interfaces:**
- Consumes: `lib.plugins.load_plugin_catalog`, `lib.plugin_test.run_plugin_test`, and a secrets reader from `.meta-config/secrets.local.yaml` (`lib.io._load_yaml_or_json`).
- Produces: a `_run_test_plugin(agent_meta_root, project_root, plugin_id) -> int` helper (exit code) callable from the early-return block. Prints `PASS/FAIL/UNKNOWN <id>: <message> (<latency_ms>ms)`.

- [ ] **Step 1: Write the failing test**
```python
# tests/test_sync_test_plugin_cli.py
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import sync  # noqa: E402


def test_arg_parser_accepts_test_plugin():
    parser = sync._build_arg_parser()
    args = parser.parse_args(["--test-plugin", "graphify"])
    assert args.test_plugin == "graphify"


def test_run_test_plugin_reports_status(monkeypatch, capsys):
    monkeypatch.setattr(sync, "run_plugin_test",
                        lambda pid, pdef, secrets=None: {"status": "PASS", "message": "ok", "latency_ms": 5})
    code = sync._run_test_plugin(REPO_ROOT, REPO_ROOT, "graphify")
    out = capsys.readouterr().out
    assert code == 0
    assert "PASS" in out and "graphify" in out


def test_run_test_plugin_unknown_id(capsys):
    code = sync._run_test_plugin(REPO_ROOT, REPO_ROOT, "does-not-exist")
    out = capsys.readouterr().out
    assert code == 1
    assert "not in catalog" in out.lower()
```
- [ ] **Step 2: Run test to verify it fails**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_sync_test_plugin_cli.py -v`
Expected: FAIL — `AttributeError: module 'sync' has no attribute 'run_plugin_test'` / `_run_test_plugin`; parser has no `test_plugin`.
- [ ] **Step 3: Write minimal implementation**
Add the import near sync.py's other `from lib.*` imports (top of file):
```python
from lib.plugin_test import run_plugin_test
from lib.plugins import load_plugin_catalog
```
Add the flag in `_build_arg_parser` (beside `--validate`):
```python
    parser.add_argument("--test-plugin", metavar="ID", default=None,
                        help="Run the health check for one plugin from the catalog and exit.")
```
Add the helper (module level) and dispatch it as an early-return mode in `_build_context`, before the `--config` requirement block (it needs the project root but not a full config):
```python
def _run_test_plugin(agent_meta_root: Path, project_root: Path, plugin_id: str) -> int:
    from lib.io import _load_yaml_or_json
    catalog = load_plugin_catalog(agent_meta_root=agent_meta_root, project_root=project_root)
    plugin_def = catalog.get(plugin_id)
    if not plugin_def:
        print(f"  !  '{plugin_id}' not in catalog ({', '.join(sorted(catalog)) or 'empty'})")
        return 1
    secrets, _ = _load_yaml_or_json(project_root / ".meta-config" / "secrets.local.yaml")
    res = run_plugin_test(plugin_id, plugin_def, secrets=secrets or {})
    print(f"  {res['status']}  {plugin_id}: {res['message']} ({res['latency_ms']}ms)")
    return 0 if res["status"] == "PASS" else 1
```
In `_build_context`, add right after the `--clear-cache` block (line ~631):
```python
    if args.test_plugin:
        sys.exit(_run_test_plugin(agent_meta_root, Path.cwd(), args.test_plugin))
```
- [ ] **Step 4: Run test to verify it passes**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_sync_test_plugin_cli.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add scripts/sync.py tests/test_sync_test_plugin_cli.py
git commit -m "feat: add sync.py --test-plugin <id> CLI health check"
```

---

### Task 7: Admin-server `POST /api/plugins/<id>/test` + `GET /api/config/plugin-catalog`

**Files:**
- Modify: `scripts/admin-server.py:201-219` (register `plugin-catalog` in `SUPER_ADMIN_FILES` + `project-plugin-catalog` in `PROJECT_FILES`)
- Modify: `scripts/admin-server.py:1348-1440` (add `test_plugin` method to `AuditService`, or a small standalone in the handler)
- Modify: `scripts/admin-server.py:3622-3637` (`_dispatch_post` — add a parametric plugin-test matcher, mirroring `_match_subserver_route`)
- Test: `tests/test_admin_plugin_test_endpoint.py`

**Interfaces:**
- Consumes: `lib.plugin_test.run_plugin_test`, `lib.plugins.load_plugin_catalog`, `ServiceContext.agent_meta_root()`, `ServiceContext.config_manager`.
- Produces: `AuditService.test_plugin(plugin_id: str) -> dict` returning `{"status", "message", "latency_ms"}` (or `{"error": ...}` on unknown id). HTTP route `POST /api/plugins/<id>/test` → that dict as JSON. Registry read route `GET /api/config/plugin-catalog` returns `{"plugins": {...}}`.

- [ ] **Step 1: Write the failing test**
```python
# tests/test_admin_plugin_test_endpoint.py
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location("admin_server", REPO_ROOT / "scripts" / "admin-server.py")
admin_server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(admin_server)


def test_match_plugin_test_route():
    h = admin_server.AdminRequestHandler
    assert h._match_plugin_test_route("/api/plugins/graphify/test") == "graphify"
    assert h._match_plugin_test_route("/api/plugins//test") is None
    assert h._match_plugin_test_route("/api/plugins/graphify") is None
    assert h._match_plugin_test_route("/api/other") is None


def test_plugin_catalog_registered_as_config_file():
    assert admin_server.SUPER_ADMIN_FILES.get("plugin-catalog") == "config/plugin-catalog.yaml"
    assert admin_server.PROJECT_FILES.get("project-plugin-catalog") == ".meta-config/plugin-catalog.yaml"
```
- [ ] **Step 2: Run test to verify it fails**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_admin_plugin_test_endpoint.py -v`
Expected: FAIL — `_match_plugin_test_route` missing; `plugin-catalog` not registered.
- [ ] **Step 3: Write minimal implementation**
Register the config files (admin-server.py:201-219):
```python
# in SUPER_ADMIN_FILES
    "plugin-catalog":    "config/plugin-catalog.yaml",
# in PROJECT_FILES
    "project-plugin-catalog": ".meta-config/plugin-catalog.yaml",
```
Add to `AuditService` (near `compute_injection_drift`, ~line 1440):
```python
    def test_plugin(self, plugin_id: str) -> dict:
        """Run the health check for one catalog plugin. Reuses the exact CLI
        implementation (lib.plugin_test.run_plugin_test) — no duplicate logic."""
        project_root = self._ctx.root
        try:
            _ensure_scripts_on_path(project_root)
            from lib.io import _load_yaml_or_json  # type: ignore[import]
            from lib.plugin_test import run_plugin_test  # type: ignore[import]
            from lib.plugins import load_plugin_catalog  # type: ignore[import]
            agent_meta_root = self._ctx.agent_meta_root()
            catalog = load_plugin_catalog(agent_meta_root=agent_meta_root, project_root=project_root)
            plugin_def = catalog.get(plugin_id)
            if not plugin_def:
                return {"status": "UNKNOWN", "message": f"'{plugin_id}' not in catalog", "latency_ms": 0}
            secrets, _ = _load_yaml_or_json(project_root / ".meta-config" / "secrets.local.yaml")
            return run_plugin_test(plugin_id, plugin_def, secrets=secrets or {})
        except Exception as exc:  # noqa: BLE001
            _, body = _generic_error_response(exc, "ERR_PLUGIN_TEST")
            return body
```
Add the parametric matcher + dispatch (mirror `_match_subserver_route`, ~line 3664), and wire it into `_dispatch_post` (after the subserver match, before `raise FileNotFoundError`):
```python
    @staticmethod
    def _match_plugin_test_route(path: str) -> str | None:
        """Return the plugin id if path is /api/plugins/<id>/test, else None."""
        prefix, suffix = "/api/plugins/", "/test"
        if not (path.startswith(prefix) and path.endswith(suffix)):
            return None
        plugin_id = path[len(prefix):-len(suffix)]
        return plugin_id or None
```
```python
        # in _dispatch_post, after the subserver block:
        plugin_id = self._match_plugin_test_route(path)
        if plugin_id is not None:
            return self._send_json(self._audit_service().test_plugin(plugin_id))
```
`GET /api/config/plugin-catalog` needs no new handler — the existing `/api/config/` prefix route (`_route_get_config`) resolves it via `SUPER_ADMIN_FILES`/`PROJECT_FILES`.
- [ ] **Step 4: Run test to verify it passes**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_admin_plugin_test_endpoint.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add scripts/admin-server.py tests/test_admin_plugin_test_endpoint.py
git commit -m "feat: add POST /api/plugins/<id>/test + plugin-catalog config route"
```

---

### Task 8: Admin-UI "Verfügbare Plugins" section (browse + activate + test)

**Files:**
- Modify: `docs/ui/admin-ui.html` (add `viewAvailablePlugins()` beside `viewProjectMcpOverrides()` ~line 2574; register a nav/route entry alongside the existing MCP entry)
- Test: `tests/test_admin_ui_plugins_section.py` (static assertions on the HTML — the UI is untestable via pytest otherwise; mirrors how other UI wiring is guarded)

**Interfaces:**
- Consumes: HTTP `GET /api/config/plugin-catalog` (Task 7), `GET /api/config/project`, `PUT /api/config/project/section` (`section: "plugins"`), `POST /api/plugins/<id>/test` (Task 7). Reuses existing JS helpers `el`, `api`, `toast`, `router`.
- Produces: no JS export (single-file SPA); a `viewAvailablePlugins` function referenced by the router.

- [ ] **Step 1: Write the failing test**
```python
# tests/test_admin_ui_plugins_section.py
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HTML = (REPO_ROOT / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")


def test_available_plugins_view_defined():
    assert "async function viewAvailablePlugins(" in HTML


def test_view_uses_catalog_and_test_endpoints():
    assert "/api/config/plugin-catalog" in HTML
    assert "/api/plugins/" in HTML and "/test" in HTML


def test_view_saves_plugins_section():
    # activation persists via the unified `plugins` project section
    assert 'section: "plugins"' in HTML or "section: 'plugins'" in HTML


def test_view_is_routed():
    assert "viewAvailablePlugins" in HTML  # referenced by the router table, not only defined
    assert HTML.count("viewAvailablePlugins") >= 2
```
- [ ] **Step 2: Run test to verify it fails**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_admin_ui_plugins_section.py -v`
Expected: FAIL — the function/route/strings do not exist yet.
- [ ] **Step 3: Write minimal implementation**
Add the view function near `viewProjectMcpOverrides` (~line 2574). It lists every catalog entry (any kind), shows a per-row active toggle backed by the unified `plugins` set, and a Test button:
```javascript
async function viewAvailablePlugins() {
  const wrap = el("div");
  wrap.appendChild(el("h1", {}, ["Verfügbare Plugins"]));
  wrap.appendChild(el("p", { class: "help-text" }, [
    "Alle katalogisierten Plugins (MCP-Server + CLI-Tools). Aktivieren, testen, konfigurieren."]));

  let catData, projData;
  try {
    catData = await api.get("/api/config/plugin-catalog").catch(() => ({ plugins: {} }));
    projData = await api.get("/api/config/project");
  } catch (err) { wrap.appendChild(renderError(err)); return wrap; }

  const catalog = catData.plugins || {};
  // unified activation set; tolerate legacy list-shorthand and dict form
  const raw = projData.plugins;
  const active = new Set(
    Array.isArray(raw) ? raw
      : Object.entries(raw || {}).filter(([, v]) => v && v.enabled).map(([k]) => k));
  let dirty = false;
  const markDirty = () => { dirty = true; router.setDirty(true); };

  const list = el("div", { style: "display:flex; flex-direction:column; gap:var(--space-2);" });
  Object.entries(catalog).sort().forEach(([id, def]) => {
    const row = el("div", { class: "card" });
    row.appendChild(el("div", { style: "font-weight:bold;" }, [`${id}  (${def.kind || "?"})`]));
    row.appendChild(el("div", { class: "help-text" }, [def.description || ""]));

    const toggle = el("input", { type: "checkbox" });
    toggle.checked = active.has(id);
    toggle.onchange = () => { toggle.checked ? active.add(id) : active.delete(id); markDirty(); };
    const tlabel = el("label", {}, [toggle, " Aktiviert"]);
    row.appendChild(tlabel);

    const testBtn = el("button", { class: "btn btn-sm" }, ["Test"]);
    const result = el("span", { style: "margin-left:var(--space-2);" });
    testBtn.onclick = async () => {
      result.textContent = "…";
      try {
        const r = await api.post(`/api/plugins/${encodeURIComponent(id)}/test`, {});
        result.textContent = `${r.status}: ${r.message} (${r.latency_ms}ms)`;
      } catch (e) { result.textContent = e.message; }
    };
    row.appendChild(testBtn); row.appendChild(result);
    list.appendChild(row);
  });
  wrap.appendChild(list);

  const save = el("button", { class: "btn btn-primary", style: "margin-top:var(--space-5);" },
                 ["Aktivierung speichern"]);
  save.onclick = async () => {
    // persist as dict-with-enabled so an explicit deactivation survives too
    const data = {}; Object.keys(catalog).forEach(id => { data[id] = { enabled: active.has(id) }; });
    try {
      await api.put("/api/config/project/section", { section: "plugins", data });
      toast("Plugin-Aktivierung gespeichert", "success");
      dirty = false; router.setDirty(false);
    } catch (e) { toast(e.message, "error"); }
  };
  wrap.appendChild(save);
  return wrap;
}
```
Register it in the router/nav table next to the MCP overview entry (find where `viewProjectMcpOverrides` is registered — add a sibling route e.g. `/project/plugins` → `viewAvailablePlugins`, matching the existing registration pattern exactly).
- [ ] **Step 4: Run test to verify it passes**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_admin_ui_plugins_section.py -v`
Then manual browser check: `python3 scripts/sync.py --admin-only --admin-port 7420`, open `http://127.0.0.1:7420`, navigate to "Verfügbare Plugins", confirm the list renders, a toggle marks the form dirty, Save persists, and Test prints a status line.
Expected: PASS + working UI
- [ ] **Step 5: Commit**
```bash
git add docs/ui/admin-ui.html tests/test_admin_ui_plugins_section.py
git commit -m "feat: admin-UI Verfügbare Plugins section (browse/activate/test)"
```

---

### Task 9: Sync-time availability probe (Layer 3 hints)

**Files:**
- Modify: `scripts/sync.py` around the post-generation summary (after the drift scan at `sync.py:1502-1503`)
- Test: `tests/test_sync_plugin_probe.py`

**Interfaces:**
- Consumes: `lib.plugins.load_plugin_catalog`, `resolve_active_plugins`, `probe_plugin_availability`.
- Produces: `_probe_inactive_plugins(agent_meta_root, project_root, config) -> list[str]` returning `[HINWEIS]` lines (one per available-but-inactive plugin). sync.py prints them.

- [ ] **Step 1: Write the failing test**
```python
# tests/test_sync_plugin_probe.py
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import sync  # noqa: E402


def test_probe_reports_available_but_inactive(monkeypatch):
    monkeypatch.setattr(sync, "load_plugin_catalog", lambda **kw: {
        "graphify": {"kind": "cli-tool", "availability-probe": "command-v", "binary": "graphify"},
        "honcho": {"kind": "mcp-server", "availability-probe": "http-head"},
    })
    monkeypatch.setattr(sync, "resolve_active_plugins", lambda *a, **k: ["honcho"])
    monkeypatch.setattr(sync, "probe_plugin_availability", lambda d: d.get("binary") == "graphify")
    lines = sync._probe_inactive_plugins(REPO_ROOT, REPO_ROOT, {})
    assert any("graphify" in ln and "HINWEIS" in ln for ln in lines)
    assert not any("honcho" in ln for ln in lines)  # active -> not reported
```
- [ ] **Step 2: Run test to verify it fails**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_sync_plugin_probe.py -v`
Expected: FAIL — `_probe_inactive_plugins` / `probe_plugin_availability` / `resolve_active_plugins` not imported in sync.
- [ ] **Step 3: Write minimal implementation**
Extend the sync.py import from Task 6:
```python
from lib.plugins import load_plugin_catalog, probe_plugin_availability, resolve_active_plugins
```
Add the helper:
```python
def _probe_inactive_plugins(agent_meta_root: Path, project_root: Path, config: dict) -> list[str]:
    catalog = load_plugin_catalog(agent_meta_root=agent_meta_root, config=config, project_root=project_root)
    active = set(resolve_active_plugins(config, agent_meta_root, project_root, catalog=catalog))
    lines: list[str] = []
    for pid, pdef in catalog.items():
        if pid in active:
            continue
        if probe_plugin_availability(pdef):
            lines.append(f"  [HINWEIS] Plugin '{pid}' lokal verfügbar, aber nicht aktiviert "
                         f"(--test-plugin {pid} zum Prüfen).")
    return lines
```
Call it after the drift scan (sync.py ~1503) and print each line. Guard with `if not args.dry_run or True:` — probing is read-only, so always run; skip when `args.check` (CI) to keep `--check` output stable:
```python
        if not args.check:
            for _hint in _probe_inactive_plugins(agent_meta_root, project_root, config):
                print(_hint)
```
- [ ] **Step 4: Run test to verify it passes**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_sync_plugin_probe.py -v`
Then: `python3 scripts/sync.py --dry-run` and confirm no crash, hints appear only for locally-available inactive plugins.
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add scripts/sync.py tests/test_sync_plugin_probe.py
git commit -m "feat: sync-time availability probe hints for inactive plugins"
```

---

### Task 10: `agent-meta-scout` catalog read access (Layer 4)

**Files:**
- Modify: `agents/1-generic/agent-meta-scout.md:66-72` (context section) and `:23-63` (add one workflow step)
- Test: `tests/test_scout_catalog_reference.py`

**Interfaces:**
- Consumes: nothing at runtime (template edit). The scout reads `{{AGENT_META_REL_PATH}}config/plugin-catalog.yaml` via its existing `Read` tool.
- Produces: no code — a documented additional recommendation source. Minimal-invasive: one context line + one workflow bullet, role unchanged.

- [ ] **Step 1: Write the failing test**
```python
# tests/test_scout_catalog_reference.py
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCOUT = (REPO_ROOT / "agents" / "1-generic" / "agent-meta-scout.md").read_text(encoding="utf-8")


def test_scout_references_plugin_catalog():
    assert "config/plugin-catalog.yaml" in SCOUT


def test_scout_still_read_only():
    # role must not gain write tools — Layer 4 is read-only recommendation
    assert "- Read" in SCOUT
    assert "- Write" not in SCOUT and "- Edit" not in SCOUT
```
- [ ] **Step 2: Run test to verify it fails**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_scout_catalog_reference.py -v`
Expected: FAIL on `test_scout_references_plugin_catalog` (string absent).
- [ ] **Step 3: Write minimal implementation**
In the `<context>` block, add under "Existing skills":
```markdown
**Plugin catalog:** see `{{AGENT_META_REL_PATH}}config/plugin-catalog.yaml` — the curated list of MCP servers + CLI tools. When proposing tooling, prefer an existing catalog entry (recommend activation) over a brand-new external candidate.
```
In `## 2. What you look for`, add a table row:
```markdown
| **Plugins** (MCP servers / CLI tools already curated) | `config/plugin-catalog.yaml` (recommend activation, no new integration) |
```
No tool changes — `Read` already covers it.
- [ ] **Step 4: Run test to verify it passes**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_scout_catalog_reference.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add agents/1-generic/agent-meta-scout.md tests/test_scout_catalog_reference.py
git commit -m "feat: give agent-meta-scout read access to the plugin catalog"
```

---

### Task 11: One-time migration script + migrate agent-meta's own project.yaml

**Files:**
- Create: `scripts/migrate-plugin-registry.py`
- Modify: `.meta-config/project.yaml:47-52` (replace `mcp-servers:` + `external-tools:` with a unified `plugins:` block)
- Test: `tests/test_migrate_plugin_registry.py`

**Interfaces:**
- Consumes: `lib.plugins.load_plugin_catalog`, `lib.mcp.resolve_active_mcp_servers`, `lib.external_tools.resolve_active_external_tools`.
- Produces: `build_plugins_block(config: dict) -> dict` (pure) mapping legacy activation → `{plugin_id: {"enabled": bool}}` in an order that preserves the resolved active-server sequence. The script rewrites a target project.yaml in place.

- [ ] **Step 1: Write the failing test**
```python
# tests/test_migrate_plugin_registry.py
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location("migrate_plugin_registry",
                                               REPO_ROOT / "scripts" / "migrate-plugin-registry.py")
mig = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mig)

from lib.external_tools import resolve_active_external_tools  # noqa: E402
from lib.mcp import resolve_active_mcp_servers  # noqa: E402


def test_build_plugins_block_preserves_active_set():
    legacy = {"mcp-servers": ["honcho", "playwright", "reqogniloom"],
              "external-tools": ["graphify"], "platforms": ["agent-meta"]}
    block = mig.build_plugins_block(legacy)
    # mcp entries appear in original order, ahead of tools
    assert list(block)[:3] == ["honcho", "playwright", "reqogniloom"]
    assert block["graphify"] == {"enabled": True}

    migrated = {"plugins": block, "platforms": ["agent-meta"]}
    assert resolve_active_mcp_servers(migrated, REPO_ROOT) == resolve_active_mcp_servers(legacy, REPO_ROOT)
    assert resolve_active_external_tools(migrated, REPO_ROOT) == resolve_active_external_tools(legacy, REPO_ROOT)


def test_agent_meta_project_yaml_is_migrated():
    import yaml
    data = yaml.safe_load((REPO_ROOT / ".meta-config" / "project.yaml").read_text())
    assert "plugins" in data
    assert "mcp-servers" not in data and "external-tools" not in data
```
- [ ] **Step 2: Run test to verify it fails**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_migrate_plugin_registry.py -v`
Expected: FAIL — script missing; project.yaml still has legacy keys.
- [ ] **Step 3: Write minimal implementation**
```python
# scripts/migrate-plugin-registry.py
"""One-time migration: rewrite a project.yaml's legacy `mcp-servers:` list and
`external-tools:` dict into the unified `plugins:` block. Order of the mcp
entries is preserved so the resolved active-server sequence (and thus
.mcp.json) stays byte-identical. Wegwerf-Werkzeug — delete after all consumer
projects migrated.

Usage: python3 scripts/migrate-plugin-registry.py .meta-config/project.yaml
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml


def build_plugins_block(config: dict) -> dict:
    """Legacy activation -> {plugin_id: {'enabled': bool}} preserving mcp order."""
    block: dict = {}
    for name in config.get("mcp-servers", []) or []:
        block[name] = {"enabled": True}
    tools = config.get("external-tools", {})
    if isinstance(tools, list):
        for name in tools:
            block[name] = {"enabled": True}
    elif isinstance(tools, dict):
        for name, val in tools.items():
            block[name] = {"enabled": bool((val or {}).get("enabled", True))}
    return block


def migrate_file(path: Path) -> bool:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if "mcp-servers" not in data and "external-tools" not in data:
        return False
    data["plugins"] = build_plugins_block(data)
    data.pop("mcp-servers", None)
    data.pop("external-tools", None)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return True


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".meta-config/project.yaml")
    print("migrated" if migrate_file(target) else "nothing to migrate", "-", target)
```
Then migrate agent-meta's own config:
```bash
python3 scripts/migrate-plugin-registry.py .meta-config/project.yaml
```
Verify the resulting `plugins:` block equals `{honcho, playwright, reqogniloom, graphify}` with the mcp entries first.
- [ ] **Step 4: Run test to verify it passes**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_migrate_plugin_registry.py -v`
Then prove no artifact drift from the activation migration:
Run: `python3 scripts/sync.py --dry-run --check`
Expected: PASS + no drift (`.mcp.json` and all rule files byte-identical to pre-migration)
- [ ] **Step 5: Commit**
```bash
git add scripts/migrate-plugin-registry.py .meta-config/project.yaml tests/test_migrate_plugin_registry.py
git commit -m "feat: add plugin-registry migration script; migrate own project.yaml"
```

---

### Task 12: Migrate the drift checker + drift rule doc to the catalog

**Files:**
- Modify: `scripts/lib/external_tools_drift.py:40-57` (`_generate_drift_content` header text) and `:1-11`/`:31-33` docstrings referencing the old file
- Modify: `.claude/rules/external-tools-drift.md:3` (the generated header sentence)
- Test: `tests/test_external_tools_drift_catalog_ref.py`

**Interfaces:**
- Consumes: unchanged — `scan_injection_drift` already reads `permitted-injections` through `load_external_tools_registry` (redirected in Task 3), so no logic change, only the user-facing reference to the old filename.
- Produces: drift content that names `config/plugin-catalog.yaml` instead of `config/external-tools-registry.yaml`.

- [ ] **Step 1: Write the failing test**
```python
# tests/test_external_tools_drift_catalog_ref.py
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.external_tools_drift import _generate_drift_content  # noqa: E402


def test_drift_header_names_catalog_not_legacy_file():
    content = _generate_drift_content([{"path": ".claude/skills/x", "kind": "skill", "tool": None}])
    assert "config/plugin-catalog.yaml" in content
    assert "config/external-tools-registry.yaml" not in content
```
- [ ] **Step 2: Run test to verify it fails**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_external_tools_drift_catalog_ref.py -v`
Expected: FAIL — header still says `config/external-tools-registry.yaml`.
- [ ] **Step 3: Write minimal implementation**
In `_generate_drift_content` (external_tools_drift.py:44-46) replace the reference:
```python
        "> Automatisch erkannt von `check_injection_drift` — Fremd-Artefakte, die keinem "
        "aktiven Tool in `config/plugin-catalog.yaml` als `permitted-injections` "
        "deklariert sind. Nur Warnung, kein automatisches Eingreifen.",
```
Update the two docstring mentions (module docstring line ~7-9 wording is generic; the concrete `config/external-tools-registry.yaml` reference at the top of `external_tools.py`'s `_generate_tool_rule_content` footer (external_tools.py:300) stays — it is part of the byte-identical rule-content and MUST NOT change, since the migration invariant froze it). Only the drift-specific header text and `.claude/rules/external-tools-drift.md:3` change. Regenerate the rule file: `python3 scripts/sync.py` (or hand-edit the one line to match).
> Caution: do NOT touch the `config/external-tools-registry.yaml` string inside `_generate_tool_rule_content`'s footer / `bootstrap_previously_managed` `content_marker` (external_tools.py:273, 300, 390) — those are load-bearing for byte-identity and the managed-index bootstrap. Changing them would break Task 2's invariant and orphan existing rule files. This task only touches the drift surface.
- [ ] **Step 4: Run test to verify it passes**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_external_tools_drift_catalog_ref.py tests/test_plugin_catalog_migration_invariant.py -v`
Expected: PASS (drift ref updated; invariant still green)
- [ ] **Step 5: Commit**
```bash
git add scripts/lib/external_tools_drift.py .claude/rules/external-tools-drift.md tests/test_external_tools_drift_catalog_ref.py
git commit -m "refactor: point injection-drift references at the unified catalog"
```

---

### Task 13: Delete the two legacy registry files + finalize config/doc references

**Files:**
- Delete: `config/external-tools-registry.yaml`, `config/mcp-registry.yaml`
- Modify: `scripts/admin-server.py:201-219` (remove `mcp-registry`/`external-tools-registry` from `SUPER_ADMIN_FILES`, remove `project-mcp-registry`/`project-external-tools-registry` from `PROJECT_FILES` — or repoint if the admin-UI MCP-overrides view still needs them; see Step 3)
- Modify: `scripts/lib/mcp_registry.py:21` and `scripts/lib/external_tools.py:32` (drop the now-dead `MCP_REGISTRY_YAML`/`EXTERNAL_TOOLS_REGISTRY_YAML` file constants only if no longer referenced — grep first)
- Test: `tests/test_legacy_registries_removed.py`

**Interfaces:**
- Consumes: the full green suite from Tasks 1-12 (nothing must still read the deleted files).
- Produces: a repo with a single catalog source of truth.

- [ ] **Step 1: Write the failing test**
```python
# tests/test_legacy_registries_removed.py
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_legacy_registry_files_deleted():
    assert not (REPO_ROOT / "config" / "mcp-registry.yaml").exists()
    assert not (REPO_ROOT / "config" / "external-tools-registry.yaml").exists()


def test_catalog_is_sole_source():
    assert (REPO_ROOT / "config" / "plugin-catalog.yaml").exists()


def test_no_source_reads_deleted_paths():
    # scan scripts/ for a live load of the deleted framework files (fixtures ok)
    offenders = []
    for py in (REPO_ROOT / "scripts").rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        for needle in ('config/mcp-registry.yaml"', 'config/external-tools-registry.yaml"'):
            if needle in text:
                offenders.append(f"{py.relative_to(REPO_ROOT)}: {needle}")
    assert not offenders, offenders
```
- [ ] **Step 2: Run test to verify it fails**
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_legacy_registries_removed.py -v`
Expected: FAIL — files still present; admin-server still lists the old paths.
- [ ] **Step 3: Write minimal implementation**
```bash
git rm config/mcp-registry.yaml config/external-tools-registry.yaml
```
Grep for every remaining live reference to the deleted framework paths and repoint or remove:
```bash
grep -rn "config/mcp-registry.yaml\|config/external-tools-registry.yaml" scripts/ config/ --include=*.py --include=*.yaml
```
- In `admin-server.py`, remove the `mcp-registry` / `external-tools-registry` `SUPER_ADMIN_FILES` entries. The admin-UI `viewProjectMcpOverrides` reads `/api/config/mcp-registry`; since that file is gone, repoint that view to `/api/config/plugin-catalog` filtered to mcp-server, OR leave the MCP-overrides view reading `plugin-catalog` (the new "Verfügbare Plugins" view from Task 8 supersedes it — if so, remove the now-dead MCP-overrides route). Decide during implementation; the test `test_no_source_reads_deleted_paths` only guards `scripts/*.py`, so update the JS `api.get("/api/config/mcp-registry")` call accordingly and keep the UI functional.
- Drop the `MCP_REGISTRY_YAML` / `EXTERNAL_TOOLS_REGISTRY_YAML` constants only if grep shows zero remaining importers (mcp.py re-exports `MCP_REGISTRY_YAML` at line 22 — check its importers first; keep the name as a re-export if any test imports it, else remove).
- The frozen fixtures under `tests/fixtures/legacy-registries/` STAY (they are the migration invariant's baseline).
- Update `CLAUDE.md` / `.claude/skills/*` doc mentions of the two files to name `config/plugin-catalog.yaml` (grep `grep -rln "mcp-registry.yaml\|external-tools-registry.yaml" .claude/ docs/ README.md`), skipping generated + fixture paths.
- [ ] **Step 4: Run test to verify it passes**
Run the full suite to prove nothing depends on the deleted files:
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -o consider_namespace_packages=true -q`
Then: `python3 scripts/sync.py --validate` and `python3 scripts/sync.py --dry-run --check`
Expected: full suite PASS, validate clean, no drift.
- [ ] **Step 5: Commit**
```bash
git add -A
git commit -m "refactor: delete legacy registry files; unify on plugin-catalog.yaml"
```
