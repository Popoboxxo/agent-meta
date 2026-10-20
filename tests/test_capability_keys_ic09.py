"""IC-09 (SPEC-CONTEXT-PROFILES-2026-10-11, Task 0a.5): every provider in
config/provider-capabilities.yaml carries all context-budget / channel
capability keys with a valid type or enum. Pure data -- no render use."""

from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
_CAPS = yaml.safe_load(
    (_ROOT / "config" / "provider-capabilities.yaml").read_text(encoding="utf-8")
)["capabilities"]
_PROVIDERS = sorted(_CAPS)

_INT_OR_NULL = (
    "context_hard_cap_bytes",
    "context_soft_cap_bytes",
    "context_soft_cap_chars",
    "context_soft_cap_lines",
)
_BOOLS = (
    "roster_in_harness",
    "agents_md_visible_to_subagents",
    "main_agent_selectable",
    "strips_html_comments",
    "subagent_allowlist_required",
)
_CHANNELS = {"embedded", "native-rules-dir", "skills", "path-scoped"}
_SURFACES = {
    "agents", "commands", "skills", "rules", "settings", "mcp",
    "workspace_agents_autoload", "context_file",
}
_VERIFIED = {
    "VERIFIED-RUNTIME", "VERIFIED-SOURCE", "SOURCE-DERIVED", "DOCUMENTED",
    "UNVERIFIED",
}
_ALL_KEYS = (
    _INT_OR_NULL + _BOOLS + (
        "rules_read_channels", "skills_discovery_dirs", "agents_md_precedence",
        "required_depth", "rules_required_suffix", "read_only_enforcement",
        "surface_verified_state", "legacy_artifacts", "agent_config_format",
    )
)


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


_EXPECTED_PROVIDERS = {
    "Claude", "Gemini", "Opencode", "Continue", "Copilot", "Mammouth",
    "Codex", "ZCode", "KimiCode",
}
# Every provider with a written rules directory now declares a file read channel
# (native-rules-dir / path-scoped): Gemini with IC-15 Nr. 8 (embedded via
# context.fileName), Copilot with IC-15 Nr. 3 (Task 1.29: .github/instructions
# path-scoped). The former "skills-only" set (F-17) is empty, so no provider is
# pinned here anymore.


def test_providers_present():
    assert len(_PROVIDERS) == 9
    assert set(_PROVIDERS) == _EXPECTED_PROVIDERS


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_depth_and_skill_dirs(provider):
    c = _CAPS[provider]
    assert c["required_depth"] >= 2  # spec IC-09: orchestrator -> worker
    assert c["skills_discovery_dirs"], "skills_discovery_dirs must not be empty"


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_all_keys_present(provider):
    missing = [k for k in _ALL_KEYS if k not in _CAPS[provider]]
    assert not missing, f"{provider} missing {missing}"


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_key_types_and_enums(provider):
    c = _CAPS[provider]
    for k in _INT_OR_NULL:
        assert c[k] is None or (_is_int(c[k]) and c[k] > 0), k
    for k in _BOOLS:
        assert isinstance(c[k], bool), k
    ch = c["rules_read_channels"]
    assert isinstance(ch, list) and set(ch) <= _CHANNELS
    assert len(ch) == len(set(ch))
    dirs = c["skills_discovery_dirs"]
    assert isinstance(dirs, list) and all(isinstance(d, str) and d for d in dirs)
    assert c["agents_md_precedence"] in {"concatenate", "nearest"}
    assert _is_int(c["required_depth"]) and c["required_depth"] >= 1
    suffix = c["rules_required_suffix"]
    assert suffix is None or (isinstance(suffix, str) and suffix)
    assert c["read_only_enforcement"] in {
        "tools", "permission-map", "sandbox", "none",
    }
    legacy = c["legacy_artifacts"]
    assert isinstance(legacy, list) and all(isinstance(p, str) for p in legacy)
    assert c["agent_config_format"] in {"toml", "yaml", "json", "markdown", None}


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_surface_verified_state(provider):
    svs = _CAPS[provider]["surface_verified_state"]
    assert isinstance(svs, dict)
    assert "context_file" in svs
    assert set(svs) <= _SURFACES
    assert all(v in _VERIFIED for v in svs.values())


def test_roster_in_harness_spec_values():
    """IC-09 / C2 (spec §4.2/IC-05): ``roster_in_harness`` is the roster gate.

    The authoritative data is ``config/provider-capabilities.yaml``; the render
    reads it, so the values are pinned here against the spec (true: Claude,
    Codex, OpenCode, Mammouth, Kimi, ZCode; false: Gemini, Continue, Copilot).
    """
    expected = {
        "Claude": True,
        "Opencode": True,
        "Gemini": False,
        "Continue": False,
        "Copilot": False,
        "Mammouth": True,
        "Codex": True,
        "ZCode": True,
        "KimiCode": True,
    }
    assert {p: _CAPS[p]["roster_in_harness"] for p in _PROVIDERS} == expected


def test_roster_in_harness_consumers_are_key_driven():
    """The roster gate reads the capability key, never a provider literal.

    (The AST guard ``test_no_provider_literal_usage_in_lib`` proves the absence
    of provider-name dispatch; this pins that both render paths actually consume
    the IC-09 key.)
    """
    for module in ("config.py", "context.py"):
        source = (_ROOT / "scripts" / "lib" / module).read_text(encoding="utf-8")
        assert "roster_in_harness" in source, module


def test_spec_example_values():
    assert _CAPS["Codex"]["context_hard_cap_bytes"] == 32768
    assert _CAPS["ZCode"]["context_hard_cap_bytes"] == 100 * 1024
    assert _CAPS["KimiCode"]["context_soft_cap_bytes"] == 32768
    assert _CAPS["Claude"]["context_soft_cap_lines"] == 200
    assert _CAPS["Copilot"]["context_soft_cap_chars"] == 4000
    assert _CAPS["Copilot"]["rules_required_suffix"] == ".instructions.md"
    assert _CAPS["Codex"]["agent_config_format"] == "toml"
    assert _CAPS["Codex"]["rules_read_channels"] == ["embedded", "skills"]
    assert _CAPS["Copilot"]["rules_read_channels"] == ["path-scoped", "skills"]
    assert _CAPS["Codex"]["surface_verified_state"]["context_file"] == "VERIFIED-RUNTIME"
    assert _CAPS["ZCode"]["surface_verified_state"]["context_file"] == "VERIFIED-SOURCE"
    assert _CAPS["ZCode"]["surface_verified_state"]["workspace_agents_autoload"] == "UNVERIFIED"
    assert _CAPS["Mammouth"]["legacy_artifacts"] == [".mammouth/settings.json"]
    assert _CAPS["KimiCode"]["subagent_allowlist_required"] is True
    assert _CAPS["Claude"]["strips_html_comments"] is True
    assert _CAPS["ZCode"]["main_agent_selectable"] is False
