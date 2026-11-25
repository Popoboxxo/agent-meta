"""Lexical path-containment gate (provider-neutral).

The kernel reads ``project_dir`` from ``NormEvent`` -- normalized by adapters
from ``AM_PROJECT_DIR``, never directly from a provider environment variable
(concept C7/D.3 step 2). The root is the normalized ``project_dir``; a nested
``.agent-meta`` checkout is not part of the jail and is skipped, mirroring
``hook_is_meta_submodule_dir`` in hook_common.sh.
"""
from __future__ import annotations

import os
from typing import Optional

from .model import Decision, NormEvent

_META_SUBMODULE = ".agent-meta"


def check_containment(event: NormEvent) -> Optional[Decision]:
    """Return a verdict for a write event with a path, otherwise ``None``.

    ``None`` means this gate has no opinion and the dispatcher should move on;
    a missing project root is not deferral but a fail-closed deny.
    """
    if event.tool_kind != "write" or not event.path:
        return None
    if not event.project_dir:
        return Decision.deny("containment.no-project-dir")

    root = os.path.realpath(event.project_dir)
    raw = os.path.expanduser(event.path)
    home = os.path.expanduser("~")
    raw = raw.replace("${HOME}", home).replace("$HOME", home)

    if os.path.isabs(raw):
        target = os.path.realpath(raw)
    else:
        base = event.cwd if event.cwd and os.path.isabs(event.cwd) else root
        target = os.path.realpath(os.path.join(base, raw))

    inside = target == root or target.startswith(root + os.sep)
    audit = {"path": target, "root": root}
    if not inside:
        return Decision.deny("containment.outside-root", audit)

    parts = os.path.relpath(target, root).split(os.sep)
    if parts and parts[0] == _META_SUBMODULE:
        return Decision.deny("containment.meta-submodule", audit)
    return Decision.allow("containment.within-root", audit)
