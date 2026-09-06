"""ABI-stability tests for the registry facade modules (#613 / #478).

Issue #478 moved the registry-query implementation into the plugins-free
``lib.registry_query`` core and turned ``lib.plugins``, ``lib.mcp_registry``
and ``lib.external_tools`` into facades over it. Every historical import
path must keep working — most importantly the #613 re-exports on
``lib.mcp`` (imported by rules.py callers, tests and external consumers).
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import lib.external_tools  # noqa: E402
import lib.mcp  # noqa: E402
import lib.mcp_registry  # noqa: E402
import lib.plugins  # noqa: E402
import lib.registry_query  # noqa: E402


def test_mcp_facade_reexports_abi_stable():
    """Issue #613 ABI: these symbols must remain importable from lib.mcp."""
    for name in (
        "SECRETS_LOCAL_FILE",
        "build_mcp_guardrails_list",
        "load_mcp_registry",
        "resolve_active_mcp_servers",
        "generate_mcp_artifacts",
        "generate_provider_configs",
        "_update_json_config",
        "MCP_RULE_PREFIX",
        "DEFAULT_RULES_DIR",
    ):
        assert hasattr(lib.mcp, name), f"lib.mcp lost ABI symbol {name}"


def test_mcp_registry_facade_reexports_abi_stable():
    for name in (
        "SECRETS_LOCAL_FILE",
        "build_mcp_guardrails_list",
        "load_mcp_registry",
        "resolve_active_mcp_servers",
    ):
        assert hasattr(lib.mcp_registry, name), f"lib.mcp_registry lost ABI symbol {name}"


def test_plugins_facade_reexports_abi_stable():
    for name in (
        "PLUGIN_CATALOG_YAML",
        "load_plugin_catalog",
        "plugins_of_kind",
        "resolve_active_plugins",
        "probe_plugin_availability",
        "resolve_plugin_compact",
        "resolve_active_mcp_servers",
        "resolve_active_external_tools",
    ):
        assert hasattr(lib.plugins, name), f"lib.plugins lost ABI symbol {name}"


def test_external_tools_facade_reexports_abi_stable():
    for name in (
        "load_external_tools_registry",
        "resolve_active_external_tools",
        "_validate_permitted_injections",
        "generate_external_tool_artifacts",
        "_generate_tool_rule_content",
        "resolve_injection_path",
        "scan_injection_drift",
        "render_injection_drift_artifacts",
        "TOOL_RULE_PREFIX",
        "DEFAULT_RULES_DIR",
    ):
        assert hasattr(lib.external_tools, name), f"lib.external_tools lost ABI symbol {name}"


def test_registry_query_is_plugins_free():
    """The inversion core must never (transitively) import lib.plugins at
    top level — that edge is what recreated the plugins ↔ mcp_registry cycle
    before #478."""
    seen: dict[int, object] = {}
    stack = [lib.registry_query]
    while stack:
        mod = stack.pop()
        if id(mod) in seen:
            continue
        seen[id(mod)] = mod
        for value in vars(mod).values():
            if isinstance(value, type(mod)) and value.__name__.startswith("lib."):
                stack.append(value)
    names = {getattr(m, "__name__", "") for m in seen.values()}
    assert "lib.plugins" not in names
