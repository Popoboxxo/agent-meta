"""Neutral MCP registry core — facade over :mod:`lib.registry_query`.

Exposing the mcp-server slice of the unified plugin catalog
(``config/plugin-catalog.yaml``), resolving which servers are active for a
project, and building the guardrails bullet list — used by both :mod:`mcp`
(rule/provider-config generation) and :mod:`rules` (``resolve_rules``'s
``MCP_GUARDRAILS_LIST`` variable).

History: split out of ``mcp.py`` (issue #613) to break the ``mcp ↔
mcp_provider_config ↔ rules`` import cycle. Issue #478 moved the actual
registry-query implementation into the plugins-free
:mod:`lib.registry_query` core (which also owns the cli-tool slice and the
catalog loading itself) so ``plugins`` / ``rules`` / ``mcp`` /
``mcp_provider_config`` / ``external_tools`` can all import the resolution
layer top-level without any cycle. This module is now a thin facade that
re-exports the mcp-server names — every historical import path keeps
working (``from lib.mcp_registry import resolve_active_mcp_servers`` and
``from lib.mcp import ...`` via mcp.py's own re-export).
"""
from __future__ import annotations

from .registry_query import (  # noqa: F401 -- re-exported for API compat (Issue #478)
    SECRETS_LOCAL_FILE,
    build_mcp_guardrails_list,
    load_mcp_registry,
    resolve_active_mcp_servers,
)
