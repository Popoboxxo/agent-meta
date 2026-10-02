"""Contract tests for the provider registry data in ``config/ai-providers.yaml``.

Task 4 of SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30 pins the provider
contract keys as *config data* (values only, no provider-name branches in
``scripts/lib/``):

  - ``surface-version`` (str, enum ``v1``/``v2``, default ``v1``)
  - ``agent-discovery`` (bool, default ``false``; ``true`` enables the
    ``.agents/*`` discovery surface, Gemini/Antigravity default-off)
  - ``model-format`` / ``model-catalog`` (KimiCode ``kimi-code/{model}``)
  - ``agent-transform.{tools-format, tool-name-map, allowed-fields,
    reject-fields, frontmatter-mechanism}``
  - ``mcp-config.format`` (e.g. ``kimi-json``, ``codex-toml-mcp``)
  - ``primary-role`` (Opencode) and ``model-literal`` (Antigravity)
  - the migrated artifact paths (Copilot, Gemini/Antigravity discovery
    surface, Mammouth context file)

The tests read the real registry so a newly onboarded provider is covered
automatically and the registry cannot silently drift back.

Run: python3 -m pytest tests/test_provider_config_contracts.py -q
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CONFIG = _REPO_ROOT / "config" / "ai-providers.yaml"

_TOOLS_FORMATS = {"keep", "filter", "skip", "remove", "map"}
_FRONTMATTER_MECHANISMS = {
    "provider-md",
    "opencode-native",
    "opencode-native-v2",
    "codex-toml",
}
_MCP_FORMATS = {
    "claude-settings",
    "gemini-settings",
    "antigravity-mcp-json",
    "opencode-json",
    "opencode-json-v2",
    "continue-yaml",
    "codex-toml-mcp",
    "kimi-json",
    "zcode-json",
    "vscode-settings",
}

# Antigravity tool vocabulary (docs-part1 §2.1 / G-2): Claude tool name ->
# provider tool name; the mapping is data, not code.
_ANTIGRAVITY_TOOL_NAME_MAP = {
    "Read": "view_file",
    "Write": "replace_file_content",
    "Grep": "grep_search",
    "Bash": "run_command",
}

# Pinned shape of the nested ``discovery:`` sub-map that ``agent-discovery: true``
# selects (default ``false`` emits the provider's own top-level paths instead).
_DISCOVERY_SURFACE = {
    "agents_dir": ".agents/agents",
    "rules_dir": ".agents/rules",
    "skills_dir": ".agents/skills",
}
_DISCOVERY_MCP = {
    "committed-file": ".agents/mcp_config.json",
    "format": "antigravity-mcp-json",
}


def _load_providers() -> dict:
    data = yaml.safe_load(_CONFIG.read_text(encoding="utf-8")) or {}
    return data.get("providers") or {}


_PROVIDERS = _load_providers()
_PROVIDER_NAMES = sorted(_PROVIDERS)


def _mcp_formats(providers: dict) -> list[tuple[str, str]]:
    """All declared MCP format values, incl. the flag-gated discovery surface."""
    out: list[tuple[str, str]] = []
    for name, cfg in providers.items():
        fmt = (cfg.get("mcp-config") or {}).get("format")
        if fmt:
            out.append((name, fmt))
        disc = (cfg.get("discovery") or {}).get("mcp-config") or {}
        if disc.get("format"):
            out.append((name, disc["format"]))
    return out


def test_registry_is_nonempty_with_reference_provider():
    """Vacuous-pass guard: every sweep below parametrizes over this registry."""
    assert _PROVIDER_NAMES, "config/ai-providers.yaml declares no providers"
    assert "Claude" in _PROVIDER_NAMES
    assert "Gemini" in _PROVIDER_NAMES
    assert "KimiCode" in _PROVIDER_NAMES
    assert "Mammouth" in _PROVIDER_NAMES


@pytest.mark.parametrize("provider", _PROVIDER_NAMES)
def test_every_provider_declares_surface_version_v1(provider):
    """AC-21/OQ-8: surface-version is a string defaulting to ``v1`` everywhere;
    ``v2`` is an opt-in that selects ``opencode-json-v2`` (Task 6/8)."""
    value = _PROVIDERS[provider].get("surface-version")
    assert value == "v1", (
        f"{provider}.surface-version must be the string 'v1' (v2 is opt-in)"
    )


@pytest.mark.parametrize("provider", _PROVIDER_NAMES)
def test_every_provider_declares_agent_discovery_bool(provider):
    """OQ-1/AC-9: provider-neutral bool gate for the ``.agents/*`` surface."""
    value = _PROVIDERS[provider].get("agent-discovery")
    assert isinstance(value, bool), (
        f"{provider}.agent-discovery must be a bool (got {value!r})"
    )
    assert value is False, (
        f"{provider}.agent-discovery is default-off; true is an explicit opt-in"
    )


@pytest.mark.parametrize("provider", _PROVIDER_NAMES)
def test_every_provider_declares_model_format(provider):
    """AC-2/OQ-3: model-format is a str whose only placeholder is ``{model}``."""
    value = _PROVIDERS[provider].get("model-format")
    assert isinstance(value, str) and value, (
        f"{provider}.model-format must be a non-empty str"
    )
    assert "{model}" in value, (
        f"{provider}.model-format must contain the '{{model}}' placeholder"
    )


@pytest.mark.parametrize("provider", _PROVIDER_NAMES)
def test_every_provider_declares_agent_transform_contract(provider):
    """AC-13/AC-21: the agent-transform contract keys exist with the right
    container types and enum values."""
    transform = _PROVIDERS[provider].get("agent-transform")
    assert isinstance(transform, dict), (
        f"{provider}.agent-transform must be a mapping"
    )
    assert transform.get("tools-format") in _TOOLS_FORMATS, (
        f"{provider}.agent-transform.tools-format must be one of "
        f"{sorted(_TOOLS_FORMATS)}"
    )
    assert isinstance(transform.get("tool-name-map"), dict), (
        f"{provider}.agent-transform.tool-name-map must be a mapping"
    )
    assert isinstance(transform.get("reject-fields"), list), (
        f"{provider}.agent-transform.reject-fields must be a list"
    )
    # ``frontmatter-mechanism`` is optional: an absent key means the
    # provider-md patch default (the documented 2/7 partition is asserted by
    # tests/test_reference_standards_strip.py). When declared it must be valid.
    mechanism = transform.get("frontmatter-mechanism")
    if mechanism is not None:
        assert mechanism in _FRONTMATTER_MECHANISMS, (
            f"{provider}.agent-transform.frontmatter-mechanism must be one of "
            f"{sorted(_FRONTMATTER_MECHANISMS)}"
        )


def test_mcp_config_format_values_are_known():
    """§2.5: the writer dispatches on the declared format value only."""
    declared = _mcp_formats(_PROVIDERS)
    assert declared, "no mcp-config.format values declared"
    unknown = [(p, f) for p, f in declared if f not in _MCP_FORMATS]
    assert not unknown, f"unknown mcp-config.format values: {unknown}"


def test_opencode_surface_v1_primary_role_and_format():
    """PRE-3/OQ-4 + OQ-8: one Opencode provider, v1 default, orchestrator as
    the v2 primary entry, flat ``opencode-json`` MCP format for v1."""
    cfg = _PROVIDERS["Opencode"]
    assert cfg["surface-version"] == "v1"
    assert cfg["agent-discovery"] is False
    assert cfg["primary-role"] == "orchestrator"
    assert cfg["mcp-config"]["format"] == "opencode-json"
    assert cfg["agent-transform"]["frontmatter-mechanism"] == "opencode-native"
    allowed = cfg["agent-transform"].get("allowed-fields")
    assert isinstance(allowed, list) and allowed, (
        "Opencode.agent-transform.allowed-fields must be populated (§4.3)"
    )
    assert all(isinstance(f, str) for f in allowed)
    # Task-18: both surfaces emit `prompt_mode` verbatim (Opencode declares no
    # strip-fields) and the provider preserves unknown keys in `options`, so the
    # allow-list must include it or a v2 project fails `sync.py --validate`.
    assert "prompt_mode" in allowed, (
        "prompt_mode is an emitted Opencode key and must be in allowed-fields"
    )


def test_kimicode_model_namespace_and_catalog():
    """F2/H6/OQ-3: exactly one ``kimi-code/`` prefix via model-format, an
    initial runtime-alias catalog, and the ``kimi-json`` MCP format."""
    cfg = _PROVIDERS["KimiCode"]
    assert cfg["model-format"] == "kimi-code/{model}"
    catalog = cfg.get("model-catalog")
    assert isinstance(catalog, list) and catalog, (
        "KimiCode.model-catalog must be a non-empty list"
    )
    assert all(isinstance(m, str) and m.startswith("kimi-code/") for m in catalog), (
        f"KimiCode.model-catalog entries must be 'kimi-code/...': {catalog}"
    )
    assert cfg["mcp-config"]["format"] == "kimi-json"


def test_mammouth_tools_format_is_map():
    """F8/N17/AC-6: Mammouth needs the object form ``tools: {name: true}``."""
    cfg = _PROVIDERS["Mammouth"]
    assert cfg["agent-transform"]["tools-format"] == "map"


def test_mammouth_context_file_migrated_to_agents_md():
    """PRE-5/OQ-7: Mammouth reads ``AGENTS.md``; ``MAMMOUTH.md`` is retired."""
    cfg = _PROVIDERS["Mammouth"]
    assert cfg["context_file"] == "AGENTS.md"
    assert cfg["context_adapter_file"] == "AGENTS.md"


def test_copilot_migrated_paths():
    """PRE-4/OQ-5 + AC-8: GitHub-cloud canonical paths and ``.agent.md``."""
    cfg = _PROVIDERS["Copilot"]
    assert cfg["agents_dir"] == ".github/agents"
    assert cfg["agent_ext"] == ".agent.md"
    assert cfg["context_file"] == ".github/copilot-instructions.md"
    assert cfg["rules_dir"] == ".github/instructions"


def test_gemini_antigravity_default_paths_unchanged():
    """OQ-1/AC-9: with ``agent-discovery: false`` the current ``.gemini/*``
    discovery artifact paths stay byte-for-byte."""
    cfg = _PROVIDERS["Gemini"]
    assert cfg["agent-discovery"] is False
    assert cfg["agents_dir"] == ".gemini/agents"
    assert cfg["rules_dir"] == ".gemini/rules"
    assert cfg["skills_dir"] == ".gemini/skills"


def test_gemini_antigravity_discovery_surface_is_gated_data():
    """OQ-1/AC-9: the ``.agents/*`` discovery surface paths + ``serverUrl``
    MCP format are declared as data reachable only when agent-discovery is on."""
    cfg = _PROVIDERS["Gemini"]
    discovery = cfg.get("discovery")
    assert isinstance(discovery, dict), (
        "Gemini.discovery must declare the flag-gated .agents/* surface"
    )
    assert discovery["agents_dir"] == ".agents/agents"
    assert discovery["rules_dir"] == ".agents/rules"
    assert discovery["skills_dir"] == ".agents/skills"
    assert discovery["mcp-config"]["format"] == "antigravity-mcp-json"
    assert discovery["mcp-config"]["committed-file"] == ".agents/mcp_config.json"


@pytest.mark.parametrize("provider", _PROVIDER_NAMES)
def test_discovery_surface_shape_is_pinned_and_bool_gated(provider):
    """OQ-1/AC-9: the nested ``discovery:`` sub-map is a pinned shape selected
    by ``agent-discovery: true`` only; the bool is the sole gate (default off,
    so the provider's own top-level paths are what gets emitted)."""
    cfg = _PROVIDERS[provider]
    assert cfg.get("agent-discovery") is False, (
        f"{provider}.agent-discovery must default off in the registry"
    )
    discovery = cfg.get("discovery")
    if discovery is None:
        return
    assert isinstance(discovery, dict), (
        f"{provider}.discovery must be a mapping (got {discovery!r})"
    )
    for key, expected in _DISCOVERY_SURFACE.items():
        assert discovery.get(key) == expected, (
            f"{provider}.discovery.{key} must be {expected!r}"
        )
    assert discovery.get("mcp-config") == _DISCOVERY_MCP, (
        f"{provider}.discovery.mcp-config must be {_DISCOVERY_MCP!r}"
    )
    # Gating: while the bool is false the discovery paths are not the emitted
    # top-level paths, so the default surface stays byte-stable.
    assert cfg.get("agents_dir") != discovery["agents_dir"], (
        f"{provider}.agents_dir must stay the default path while discovery is off"
    )


def test_gemini_antigravity_model_literal_and_tool_name_map():
    """OQ-6 (model: inherit) + G-2 (tool vocabulary as data)."""
    cfg = _PROVIDERS["Gemini"]
    assert cfg["model-literal"] == "inherit"
    assert cfg["agent-transform"]["tool-name-map"] == _ANTIGRAVITY_TOOL_NAME_MAP


def test_codex_and_continue_mcp_formats():
    """CX-1/CX-2: Codex TOML and Continue YAML dispatch values stay declared."""
    assert _PROVIDERS["Codex"]["mcp-config"]["format"] == "codex-toml-mcp"
    assert _PROVIDERS["Codex"]["agent-transform"]["frontmatter-mechanism"] == "codex-toml"
    assert _PROVIDERS["Continue"]["mcp-config"]["format"] == "continue-yaml"
    assert _PROVIDERS["Claude"]["mcp-config"]["format"] == "claude-settings"
