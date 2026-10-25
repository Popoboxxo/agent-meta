"""Central subprocess timeouts for the test suite (CI timeout-flake fix).

WHY: ``sync.py --validate`` is not a cheap flag check. It internally runs the
repository-wide consistency suite (``_run_consistency_checks`` with
``changed_only=False``) plus the config audit and the strict / hook-drift /
temp-literal checks. On a cold, shared GitHub runner that work can exceed 60 s
(observed: CI run 40210737659, Python 3.9, ``subprocess.TimeoutExpired``).
These constants are a hang guard, not a performance assertion: a slow machine
must not turn a green suite red, while a truly wedged subprocess still dies.

They are env-configurable so a deliberately slower CI environment can raise
them without editing tests:

* ``AGENT_META_SYNC_TIMEOUT``           -> :data:`SYNC_TIMEOUT`
* ``AGENT_META_SYNC_VALIDATE_TIMEOUT``  -> :data:`SYNC_VALIDATE_TIMEOUT`
  (falls back to ``AGENT_META_SYNC_TIMEOUT``)
* ``AGENT_META_SCRIPT_TIMEOUT``         -> :data:`SCRIPT_TIMEOUT`

A non-integer, empty or non-positive value falls back to the default; importing
this module must never raise.

REJECTED: a session-scoped cache fixture for ``sync.py --validate``.
``_run_consistency_checks(agent_meta_root)`` is repo-global and therefore
cacheable, but ``check_stale_deployed_hooks``,
``check_hook_enablement_consistency`` and ``check_repo_containment_support``
evaluate the *per-project* ``project_root``, and the test-repo branch depends on
``../agent-meta-test`` / ``AGENT_META_TEST_REPO`` existing. A shared cache would
replay per-project findings from one tmp project in another and mask exactly
that environment difference -- a false green. Re-running is the honest option.
"""
from __future__ import annotations

import os

_DEFAULT_SYNC_TIMEOUT = 180
_DEFAULT_SCRIPT_TIMEOUT = 60


def _env_seconds(name: str, default: int) -> int:
    """Return ``$name`` as a positive int, else ``default`` (never raises)."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw.strip())
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    return value


#: Full ``sync.py`` run (non-dry-run) in a synthetic project directory.
SYNC_TIMEOUT: int = _env_seconds("AGENT_META_SYNC_TIMEOUT", _DEFAULT_SYNC_TIMEOUT)

#: ``sync.py --validate``: runs the repository-wide consistency suite.
SYNC_VALIDATE_TIMEOUT: int = _env_seconds(
    "AGENT_META_SYNC_VALIDATE_TIMEOUT", SYNC_TIMEOUT
)

#: Helper scripts (eval wrappers, hook adapters, ``git status``): unchanged
#: 60 s semantics -- none of them carries the repo-wide consistency suite.
SCRIPT_TIMEOUT: int = _env_seconds("AGENT_META_SCRIPT_TIMEOUT", _DEFAULT_SCRIPT_TIMEOUT)
