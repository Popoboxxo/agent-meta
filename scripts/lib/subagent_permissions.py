"""Subagent permission policy (Feature A) — read-only resolution helpers.

The policy is prompt-based on every provider plus a sync-time validator; there
is deliberately no runtime dispatch gate (see
``docs/concepts/subagent-permissions-git-admin-ui.md`` §8/§10). This module is
the non-exiting read layer shared by ``config.py`` (variable building), the
per-provider sync loop and the consistency checks.

Contract: every function here is pure/non-exiting. Invalid or absent values
resolve to ``"off"`` — the hard ``sys.exit(1)`` lives exclusively in
``config._validate_subagent_permissions``.

Imports are kept low-level (stdlib + ``.frontmatter`` + ``.variables``); the
heavier ``agent_sync.compose_agent`` is imported lazily inside
``role_declares_tools`` so the module never participates in an import cycle.
"""
from __future__ import annotations

from pathlib import Path

from .frontmatter import parse_frontmatter_text
from .variables import (
    _resolve_subagent_permissions_mode,
    _subagent_permission_flags,
    normalize_subagent_permission_mode,
)

_MODE_PATH_GLOBAL = "subagent_permissions.mode"


def render_subagent_permission_block(mode: str) -> str:
    """Render the provider-agnostic prose block for ``mode``.

    Returns ``""`` for ``"off"`` (nothing rendered). ``"warn"`` is report-only;
    ``"strict"`` adds the dispatch gate plus the mandatory structured return
    format and the single retry before escalation.
    """
    if mode == "strict":
        return (
            "**Subagent Permission Policy (strict):** Dispatch a subagent only "
            "when its role template declares an explicit allow/deny contract "
            "(a non-empty `tools:` list in its frontmatter). If it does not, "
            "do NOT dispatch — escalate to `main_chat` instead. Every subagent "
            "result MUST follow the structured `STATUS` / `RESULT` / `ARTIFACTS` "
            "format; a result missing any of the three fields is discarded and "
            "the subagent is re-dispatched exactly once with a format hint. A "
            "second violation escalates to `main_chat`."
        )
    if mode == "warn":
        return (
            "**Subagent Permission Policy (warn):** Check every dispatch for an "
            "explicit allow/deny declaration and every result for the structured "
            "`STATUS` / `RESULT` / `ARTIFACTS` format — but do not block. Log "
            "each violation as a line `SUBAGENT_PERMISSION_WARNING: <role> — "
            "<reason>` in your own final report and continue."
        )
    return ""


def resolve_effective_subagent_permission_mode(
    config: dict, provider: str | None = None
) -> str:
    """Read + normalize the effective mode for ``config`` and ``provider``.

    Never raises/exits: an invalid or absent value resolves to ``"off"``. This
    is the single non-exiting entry point used by the consistency checks and the
    Admin-UI-facing read paths (M3: no ``try/except SystemExit``).
    """
    cfg = config.get("subagent_permissions") if isinstance(config, dict) else None
    if not isinstance(cfg, dict):
        cfg = {}

    provider_override: dict | None = None
    if provider is not None:
        overrides = cfg.get("provider-overrides")
        if isinstance(overrides, dict):
            candidate = overrides.get(provider)
            if isinstance(candidate, dict):
                provider_override = candidate

    return _resolve_subagent_permissions_mode(cfg, provider_override)


def resolve_subagent_permission_provider_vars(config: dict, provider: str) -> dict:
    """Full per-provider variable bundle for ``provider``.

    Contains the boolean flags from ``_subagent_permission_flags(mode)`` PLUS
    ``SUBAGENT_PERMISSIONS_BLOCK = render_subagent_permission_block(mode)``, so
    flags and block can never drift apart (M2). All nested access is defensive;
    an invalid/absent value resolves to ``"off"``.
    """
    mode = resolve_effective_subagent_permission_mode(config, provider)
    bundle = _subagent_permission_flags(mode)
    bundle["SUBAGENT_PERMISSIONS_BLOCK"] = render_subagent_permission_block(mode)
    return bundle


def invalid_subagent_permission_entries(config: dict) -> list[str]:
    """Human-readable paths of invalid mode values (global + per override).

    Pure read, never exits. YAML-1.1 booleans are not reported: they are
    normalized to ``"off"`` by ``config._normalize_subagent_permissions_mode``
    and are a parse artifact, not a user error.
    """
    entries: list[str] = []
    cfg = config.get("subagent_permissions") if isinstance(config, dict) else None
    if not isinstance(cfg, dict):
        return entries

    if isinstance(cfg.get("mode"), str) and normalize_subagent_permission_mode(
        cfg.get("mode")
    ) is None:
        entries.append(_MODE_PATH_GLOBAL)

    overrides = cfg.get("provider-overrides")
    if isinstance(overrides, dict):
        for provider in sorted(overrides):
            entry = overrides.get(provider)
            if not isinstance(entry, dict):
                continue
            value = entry.get("mode")
            if isinstance(value, str) and normalize_subagent_permission_mode(value) is None:
                entries.append(
                    f"subagent_permissions.provider-overrides.{provider}.mode"
                )
    return entries


def _source_declares_tools(source_path: Path, agent_meta_root: Path) -> bool:
    """True when a resolved source template declares a non-empty ``tools:``.

    Applies the ``extends:`` composition first (lazy ``agent_sync.compose_agent``)
    so a 2-platform override without its own ``tools:`` inherits the base
    declaration.
    """
    try:
        content = source_path.read_text(encoding="utf-8")
    except OSError:
        return False

    frontmatter = parse_frontmatter_text(content)
    extends_base = frontmatter.get("extends")
    if isinstance(extends_base, str) and extends_base:
        base_path = agent_meta_root / extends_base
        if base_path.exists():
            from .agent_sync import compose_agent
            from .log import SyncLog

            content = compose_agent(base_path, content, SyncLog())
            frontmatter = parse_frontmatter_text(content)

    tools = frontmatter.get("tools")
    if isinstance(tools, str):
        return bool(tools.strip())
    if isinstance(tools, list):
        return any(isinstance(t, str) and t.strip() for t in tools)
    return False


def role_declares_tools(role: str, agent_meta_root: Path, platforms: list[str]) -> bool:
    """True when ``role``'s resolved template declares a non-empty ``tools:``.

    Resolution runs through the real override chain
    (``frontmatter.collect_sources``: 1-generic < 2-platform < 3-project) and
    then composes ``extends:`` — never the hardcoded
    ``agents/1-generic/<role>.md`` path (B2). A role with no generated source
    is reported as ``False``.
    """
    from .frontmatter import collect_sources

    overrides, _ = collect_sources(agent_meta_root, platforms)
    source_path = overrides.get(role)
    if source_path is None:
        return False
    return _source_declares_tools(source_path, agent_meta_root)


def missing_tools_roles(
    active_roles: list[str], agent_meta_root: Path, platforms: list[str]
) -> list[str]:
    """Subset of ``active_roles`` whose resolved template has no ``tools:``."""
    from .frontmatter import collect_sources

    overrides, _ = collect_sources(agent_meta_root, platforms)
    missing: list[str] = []
    for role in active_roles:
        source_path = overrides.get(role)
        if source_path is None:
            continue
        if not _source_declares_tools(source_path, agent_meta_root):
            missing.append(role)
    return missing
