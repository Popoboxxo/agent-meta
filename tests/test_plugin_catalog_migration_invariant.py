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
