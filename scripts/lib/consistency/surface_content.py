"""Content-expectation predicate for declared provider surfaces (IC-10).

``context.declared-surface-empty`` must not flag surfaces that are empty by
design. Whether content is expected is derived from project data, never from a
provider name:

* ``commands``/``settings``: a declared surface is always generated.
* ``skills``: expected when the provider's rule routing really produces skill
  artifacts (lazy ``embed: false`` / ``channel: skill`` rules, MCP/tool
  skills) -- mirrored from the writers via ``rules.lazy_skill_stems``.
* ``mcp``: expected when at least one MCP server is active for the project.
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

_FRAMEWORK_ROOT = Path(__file__).resolve().parents[3]


def _project_config(project_root: Path) -> dict:
    """Read the consumer project's ``.meta-config/project.yaml`` (fail-soft ``{}``)."""
    try:
        import yaml
        data = yaml.safe_load(
            (project_root / ".meta-config" / "project.yaml").read_text(encoding="utf-8"))
    except Exception:  # absent, unreadable, malformed or no PyYAML
        return {}
    return data if isinstance(data, dict) else {}


def _active_mcp_servers(project_root: Path) -> list:
    """Active MCP servers of the consumer project (fail-soft ``[]``)."""
    try:
        from ..registry_query import resolve_active_mcp_servers
        return list(resolve_active_mcp_servers(
            _project_config(project_root), _FRAMEWORK_ROOT, project_root))
    except Exception:  # registry unavailable/corrupt -> no expectation
        return []


def content_expected(project_root: Path, provider: str, caps: Mapping, surface: str) -> bool:
    """Whether a declared surface should contain generated content (IC-10).

    Provider-agnostic: only capability keys and registries are consulted.
    """
    if surface in ("commands", "settings"):
        return True
    root = Path(project_root)
    if surface == "skills":
        try:
            from ..rules import lazy_skill_stems
            return bool(lazy_skill_stems(
                _FRAMEWORK_ROOT, root, _project_config(root), provider, caps))
        except Exception:  # registry/config problem -> no expectation
            return False
    if surface == "mcp":
        return bool(_active_mcp_servers(root))
    return False
