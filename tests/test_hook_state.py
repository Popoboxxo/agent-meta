"""Unit tests for scripts/lib/hook_state.py — one import-free hook-enablement
predicate shared by hooks.sync_hooks and the auto-commit guard (#1181, T15).

Strict-bool semantics mirror the former hooks._strict_enabled: only a real
``True`` enables; a quoted ``"true"``/``"false"`` is invalid AND disabled.

Run: python -m pytest tests/test_hook_state.py -q
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.hook_state import (  # noqa: E402
    ORCHESTRATOR_GUARD_HOOK,
    ORCHESTRATOR_GUARD_ENABLED_BY_DEFAULT,
    guard_hook_enabled,
    resolve_hook_enabled,
)


def test_guard_default_is_enabled():
    """Guard is enabled by default (hooks/1-generic/orchestrator-guard.sh:7)."""
    assert ORCHESTRATOR_GUARD_HOOK == "orchestrator-guard"
    assert ORCHESTRATOR_GUARD_ENABLED_BY_DEFAULT is True
    assert guard_hook_enabled({}) == (True, False)


def test_guard_explicit_false_disables():
    """An explicit bool false disables the guard, no invalidity (RVW-1181-01)."""
    config = {"hooks": {"orchestrator-guard": {"enabled": False}}}
    assert guard_hook_enabled(config) == (False, False)


def test_guard_quoted_false_is_invalid_and_disabled():
    """A quoted 'false' is invalid AND disabled, same as hooks._strict_enabled."""
    config = {"hooks": {"orchestrator-guard": {"enabled": "false"}}}
    assert guard_hook_enabled(config) == (False, True)


def test_resolve_uses_enabled_by_default_flag():
    """resolve_hook_enabled honours the explicit enabled_by_default flag."""
    assert resolve_hook_enabled({}, "x", True) == (True, False)
    assert resolve_hook_enabled({}, "x") == (False, False)


def test_resolve_ignores_other_hooks():
    """An unrelated hook's config never perturbs the guard default."""
    hooks_config = {"dod-push-check": {"enabled": True}}
    assert resolve_hook_enabled(
        hooks_config, ORCHESTRATOR_GUARD_HOOK, ORCHESTRATOR_GUARD_ENABLED_BY_DEFAULT
    ) == (True, False)
