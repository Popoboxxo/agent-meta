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
    data = yaml.safe_load((REPO_ROOT / ".meta-config" / "project.yaml").read_text(encoding="utf-8"))
    assert "plugins" in data
    assert "mcp-servers" not in data and "external-tools" not in data
