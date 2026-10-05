"""Owner-only file permissions for secret-bearing project config (issue #864).

``.meta-config/project.yaml`` can hold a plaintext admin token
(``admin-ui.token``) or other credential keys. The Admin-UI save path has
always chmodded it to ``0600`` (issue #589), but the CLI writers
(``--init``, ``--fill-defaults``, the ``--setup`` wizard and the
agent-meta-version write-back) did not — so a config created or rewritten by
the CLI stayed group/world-readable under a typical ``022`` umask.

These helpers centralise the best-effort chmod so every writer enforces the
same owner-only protection the Admin-UI already applies. They are
provider-agnostic and cross-platform-safe: on platforms without POSIX mode
bits (or when chmod fails for any reason) they no-op instead of breaking a
sync.
"""
from __future__ import annotations

import os
from pathlib import Path

OWNER_ONLY_MODE = 0o600

#: Sibling files under ``.meta-config/`` that the Admin-UI save path also
#: restricts (``admin-server.py`` PROJECT_FILES). Hardened only when present —
#: never created here.
_ADMIN_CONFIG_SIBLINGS = ("plugin-catalog.yaml",)


def restrict_owner_only(path: Path) -> bool:
    """Best-effort chmod of ``path`` to ``0600``.

    Returns ``True`` when the mode was applied, ``False`` when it was skipped:
    the path is missing, the platform has no POSIX mode bits (Windows), or the
    chmod raised ``OSError``. Never raises — a failed chmod must not break a
    sync.
    """
    if os.name == "nt":
        return False
    if not path.exists():
        return False
    try:
        os.chmod(path, OWNER_ONLY_MODE)
    except OSError:
        return False
    return True


def harden_admin_config_files(config_path: Path) -> None:
    """Restrict owner-only permissions on a project's ``.meta-config`` files.

    Mirrors the Admin-UI save path (``admin-server.py`` PROJECT_FILES, issue
    #589 / #864): ``config_path`` itself is always hardened, and a sibling
    ``plugin-catalog.yaml`` is hardened only when it already exists. No file is
    created and a permission failure never propagates.
    """
    restrict_owner_only(config_path)
    if config_path.parent.name == ".meta-config":
        for name in _ADMIN_CONFIG_SIBLINGS:
            sibling = config_path.parent / name
            if sibling != config_path and sibling.exists():
                restrict_owner_only(sibling)
