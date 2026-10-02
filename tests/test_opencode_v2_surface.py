"""Opencode v2 surface wiring tests.

SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30, §4.1 / AC-5 / AC-21 / AC-23
(design DECISION-7; scenario 69):

``surface-version`` is config data that selects TWO declared surfaces:

  - ``mcp-config.format`` through ``mcp-config.surface-formats``
    (covered by ``tests/test_surface_version_selection.py``);
  - ``agent-transform.frontmatter-mechanism`` through
    ``agent-transform.surface-mechanisms`` (new wiring under test here,
    ``v1`` -> ``opencode-native``, ``v2`` -> ``opencode-native-v2``).

Both selections happen once, generically, in ``load_providers_config``; the
writers consume the resolved value only and never read ``surface-version``.

The v2 settings surface (``opencode.json``) additionally drops the v1-only
``subagent_depth`` key and emits ``default_agent`` from the ``primary-role``
data key. ``apply_settings_surface_shape`` dispatches on the resolved
``mcp-config.format`` value only; every non-v2 format is returned
byte-for-byte so the shipped v1 surface stays frozen.

Run: python3 -m pytest tests/test_opencode_v2_surface.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.context import apply_settings_surface_shape
from lib.providers import load_providers_config

_SURFACE_MECHANISMS = {"v1": "opencode-native", "v2": "opencode-native-v2"}

_SETTINGS_TEMPLATE = (
    "{\n"
    "  // opencode configuration\n"
    '  "subagent_depth": 3,\n'
    "  // \"model\": \"anthropic/claude-sonnet-4-6\",\n"
    "}\n"
)


def _write_config(root: Path, providers: dict) -> None:
    """Write a minimal ``config/ai-providers.yaml`` fixture under ``root``."""
    cfg_dir = root / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "ai-providers.yaml").write_text(
        yaml.safe_dump({"providers": providers}, sort_keys=False),
        encoding="utf-8",
    )


def _opencode_like(surface: str, mechanisms: dict | None = _SURFACE_MECHANISMS) -> dict:
    transform: dict = {"frontmatter-mechanism": "opencode-native"}
    if mechanisms is not None:
        transform["surface-mechanisms"] = dict(mechanisms)
    mcp: dict = {"committed-file": "opencode.json", "format": "opencode-json"}
    mcp["surface-formats"] = {"v1": "opencode-json", "v2": "opencode-json-v2"}
    return {
        "surface-version": surface,
        "primary-role": "orchestrator",
        "mcp-config": mcp,
        "agent-transform": transform,
    }


# --- mechanism selection ----------------------------------------------------


def test_real_registry_opencode_v1_keeps_opencode_native():
    """AC-5: the committed v1 default resolves to the v1 mechanism."""
    cfg = load_providers_config(_REPO_ROOT)["Opencode"]
    assert cfg["surface-version"] == "v1"
    assert cfg["agent-transform"]["frontmatter-mechanism"] == "opencode-native"


def test_real_registry_declares_surface_mechanisms_map():
    """The mechanism selection data exists on the Opencode entry."""
    cfg = load_providers_config(_REPO_ROOT)["Opencode"]
    assert (
        cfg["agent-transform"]["surface-mechanisms"] == _SURFACE_MECHANISMS
    )


def test_v2_selects_opencode_native_v2(tmp_path):
    _write_config(tmp_path, {"Opencode": _opencode_like("v2")})
    cfg = load_providers_config(tmp_path)["Opencode"]
    assert cfg["agent-transform"]["frontmatter-mechanism"] == "opencode-native-v2"


def test_v1_selects_opencode_native(tmp_path):
    _write_config(tmp_path, {"Opencode": _opencode_like("v1")})
    cfg = load_providers_config(tmp_path)["Opencode"]
    assert cfg["agent-transform"]["frontmatter-mechanism"] == "opencode-native"


def test_absent_surface_mechanisms_leaves_declared_value(tmp_path):
    """A provider without ``surface-mechanisms`` is untouched — even on v2."""
    _write_config(
        tmp_path,
        {
            "Other": {
                "surface-version": "v2",
                "agent-transform": {"frontmatter-mechanism": "provider-md"},
            }
        },
    )
    cfg = load_providers_config(tmp_path)["Other"]
    assert cfg["agent-transform"]["frontmatter-mechanism"] == "provider-md"


def test_unknown_surface_version_keeps_declared_mechanism(tmp_path):
    _write_config(tmp_path, {"Opencode": _opencode_like("v3")})
    cfg = load_providers_config(tmp_path)["Opencode"]
    assert cfg["agent-transform"]["frontmatter-mechanism"] == "opencode-native"


def test_mechanism_selection_is_provider_name_agnostic(tmp_path):
    """Selection keys off the declared data (map + version), not the name."""
    _write_config(
        tmp_path,
        {
            "FutureProvider": {
                "surface-version": "v2",
                "agent-transform": {
                    "frontmatter-mechanism": "placeholder",
                    "surface-mechanisms": _SURFACE_MECHANISMS,
                },
            }
        },
    )
    cfg = load_providers_config(tmp_path)["FutureProvider"]
    assert cfg["agent-transform"]["frontmatter-mechanism"] == "opencode-native-v2"


def test_mechanism_selection_does_not_leak_to_neighbours(tmp_path):
    _write_config(
        tmp_path,
        {
            "Mapped": _opencode_like("v2"),
            "Plain": {
                "surface-version": "v2",
                "agent-transform": {"frontmatter-mechanism": "codex-toml"},
            },
        },
    )
    cfg = load_providers_config(tmp_path)
    assert cfg["Mapped"]["agent-transform"]["frontmatter-mechanism"] == "opencode-native-v2"
    assert cfg["Plain"]["agent-transform"]["frontmatter-mechanism"] == "codex-toml"


# --- v2 settings surface ----------------------------------------------------


def _pc_v2() -> dict:
    return {
        "surface-version": "v2",
        "primary-role": "orchestrator",
        "mcp-config": {"format": "opencode-json-v2"},
    }


def test_v2_settings_drops_subagent_depth_and_emits_default_agent():
    out = apply_settings_surface_shape(_SETTINGS_TEMPLATE, _pc_v2())
    doc = json.loads(out)
    assert "subagent_depth" not in doc
    assert doc["default_agent"] == "orchestrator"


def test_v2_settings_default_agent_comes_from_primary_role():
    pc = _pc_v2()
    pc["primary-role"] = "developer"
    doc = json.loads(apply_settings_surface_shape(_SETTINGS_TEMPLATE, pc))
    assert doc["default_agent"] == "developer"


def test_v2_settings_without_primary_role_emits_no_default_agent():
    pc = _pc_v2()
    pc.pop("primary-role")
    doc = json.loads(apply_settings_surface_shape(_SETTINGS_TEMPLATE, pc))
    assert "subagent_depth" not in doc
    assert "default_agent" not in doc


def test_v1_settings_template_is_byte_identical():
    """The shipped v1 surface must stay frozen, comments included."""
    pc = {"surface-version": "v1", "mcp-config": {"format": "opencode-json"}}
    assert apply_settings_surface_shape(_SETTINGS_TEMPLATE, pc) == _SETTINGS_TEMPLATE


def test_non_v2_format_is_byte_identical():
    pc = {"surface-version": "v2", "mcp-config": {"format": "gemini-settings"}}
    assert apply_settings_surface_shape(_SETTINGS_TEMPLATE, pc) == _SETTINGS_TEMPLATE


def test_unparseable_template_is_returned_unchanged():
    pc = _pc_v2()
    broken = "{ not valid json"
    assert apply_settings_surface_shape(broken, pc) == broken
