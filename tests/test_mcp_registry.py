"""Unit tests for lib.mcp_registry (extracted from mcp.py in #613 to break an
import cycle, #650).

Covers the three public functions:
- load_mcp_registry: base registry + project-level + config-level override merge
- resolve_active_mcp_servers: explicit config list vs. platform-bundle lookup
  (respecting enabled-by-default)
- build_mcp_guardrails_list: rendering the blocked-tools bullet list
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.mcp_registry import (
    build_mcp_guardrails_list,
    load_mcp_registry,
    resolve_active_mcp_servers,
)

_BASE_REGISTRY = """\
mcp-servers:
  honcho:
    tools:
      blocked: [delete_conclusion, set_config]
  playwright:
    enabled-by-default: true
    tools:
      blocked: [browser_evaluate]
  reqogniloom:
    enabled-by-default: false
    tools:
      blocked: [workspace.close]
"""


def _write_registry(agent_meta_root: Path, body: str = _BASE_REGISTRY) -> None:
    d = agent_meta_root / "config"
    d.mkdir(parents=True, exist_ok=True)
    (d / "mcp-registry.yaml").write_text(body, encoding="utf-8")


# --- load_mcp_registry -------------------------------------------------------

def test_load_mcp_registry_reads_base_registry(tmp_path):
    _write_registry(tmp_path)
    registry = load_mcp_registry(tmp_path)
    assert set(registry) == {"honcho", "playwright", "reqogniloom"}
    assert registry["honcho"]["tools"]["blocked"] == ["delete_conclusion", "set_config"]


def test_load_mcp_registry_missing_file_returns_empty_dict(tmp_path):
    assert load_mcp_registry(tmp_path) == {}


def test_load_mcp_registry_merges_project_override(tmp_path):
    _write_registry(tmp_path)
    project_root = tmp_path / "project"
    (project_root / ".meta-config").mkdir(parents=True)
    (project_root / ".meta-config" / "mcp-registry.yaml").write_text(
        "mcp-servers:\n  honcho:\n    enabled-by-default: false\n", encoding="utf-8",
    )

    registry = load_mcp_registry(tmp_path, project_root=project_root)

    assert registry["honcho"]["enabled-by-default"] is False
    # deep-merge preserves sibling keys instead of replacing the whole entry
    assert registry["honcho"]["tools"]["blocked"] == ["delete_conclusion", "set_config"]


def test_load_mcp_registry_merges_config_override(tmp_path):
    _write_registry(tmp_path)
    config = {"mcp-registry": {"honcho": {"tools": {"blocked": ["only_this_one"]}}}}

    registry = load_mcp_registry(tmp_path, config=config)

    assert registry["honcho"]["tools"]["blocked"] == ["only_this_one"]


# --- resolve_active_mcp_servers ----------------------------------------------

def test_resolve_active_servers_explicit_list_from_config(tmp_path):
    _write_registry(tmp_path)
    config = {"mcp-servers": ["honcho"], "platforms": []}

    active = resolve_active_mcp_servers(config, tmp_path)

    assert active == ["honcho"]


def test_resolve_active_servers_platform_bundle_enabled_by_default(tmp_path):
    _write_registry(tmp_path)
    platform_dir = tmp_path / "rules" / "2-platform"
    platform_dir.mkdir(parents=True)
    (platform_dir / "myplatform-mcp.yaml").write_text(
        "mcp-servers:\n  - honcho\n  - playwright\n  - reqogniloom\n", encoding="utf-8",
    )
    config = {"mcp-servers": [], "platforms": ["myplatform"]}

    active = resolve_active_mcp_servers(config, tmp_path)

    # honcho: no enabled-by-default -> defaults True -> active
    # playwright: enabled-by-default true -> active
    # reqogniloom: enabled-by-default false -> skipped
    assert active == ["honcho", "playwright"]


def test_resolve_active_servers_no_platform_bundle_file_is_a_noop(tmp_path):
    _write_registry(tmp_path)
    config = {"mcp-servers": ["honcho"], "platforms": ["unknown-platform"]}

    active = resolve_active_mcp_servers(config, tmp_path)

    assert active == ["honcho"]


def test_resolve_active_servers_reuses_preloaded_registry(tmp_path):
    _write_registry(tmp_path)
    registry = {"custom": {"enabled-by-default": True}}
    config = {"mcp-servers": ["custom"], "platforms": []}

    active = resolve_active_mcp_servers(config, tmp_path, registry=registry)

    assert active == ["custom"]


# --- build_mcp_guardrails_list ------------------------------------------------

def test_build_guardrails_list_renders_blocked_tools_sorted_by_server():
    registry = {
        "honcho": {"tools": {"blocked": ["delete_conclusion", "set_config"]}},
        "playwright": {"tools": {"blocked": ["browser_evaluate"]}},
    }
    text = build_mcp_guardrails_list(registry, ["playwright", "honcho"])

    lines = text.splitlines()
    assert lines[0].startswith("- **honcho:**")
    assert "`delete_conclusion`" in lines[0]
    assert lines[1].startswith("- **playwright:**")


def test_build_guardrails_list_skips_servers_without_blocked_tools():
    registry = {"clean-server": {"tools": {}}}
    text = build_mcp_guardrails_list(registry, ["clean-server"])
    assert text == "- (keine aktiven MCP-Server mit gesperrten Tools)"


def test_build_guardrails_list_empty_active_servers():
    text = build_mcp_guardrails_list({"honcho": {"tools": {"blocked": ["x"]}}}, [])
    assert text == "- (keine aktiven MCP-Server mit gesperrten Tools)"
