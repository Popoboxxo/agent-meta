"""Import-free predicate for the effective enablement of a hook (#1181, T15).

Shared by ``hooks.sync_hooks`` and the auto-commit guard so both apply the
exact same strict-bool semantics. Only stdlib typing/collections.abc imports
live here — no repo modules — which lets both callers load it without a cycle.

Contract: only a real ``bool`` ``True`` enables. A quoted ``"true"`` /
``"false"`` is invalid and disabled. The second element of the returned tuple
flags invalidity so callers can emit their own warning with unchanged wording.
"""
from __future__ import annotations

from collections.abc import Mapping

ORCHESTRATOR_GUARD_HOOK = "orchestrator-guard"
ORCHESTRATOR_GUARD_ENABLED_BY_DEFAULT = True


def resolve_hook_enabled(
    hooks_config: Mapping,
    hook_stem: str,
    enabled_by_default: bool = False,
) -> tuple[bool, bool]:
    """Return ``(enabled, invalid)`` for ``hook_stem`` in ``hooks_config``.

    Mirrors the former ``hooks._strict_enabled``: only ``value is True``
    enables; any non-bool raw value is invalid AND disabled. A missing
    ``enabled`` key falls back to ``enabled_by_default`` (already a bool) and
    is never invalid.
    """
    raw = hooks_config.get(hook_stem, {}).get("enabled", enabled_by_default)
    if not isinstance(raw, bool):
        return (False, True)
    return (raw is True, False)


def guard_hook_enabled(config: dict) -> tuple[bool, bool]:
    """Enablement of the orchestrator guard, defaulted on (#1181)."""
    return resolve_hook_enabled(
        config.get("hooks") or {},
        ORCHESTRATOR_GUARD_HOOK,
        ORCHESTRATOR_GUARD_ENABLED_BY_DEFAULT,
    )
