"""Lexical path-containment gate (provider-neutral).

The kernel reads ``project_dir`` from ``NormEvent`` -- normalized by adapters
from ``AM_PROJECT_DIR``, never directly from a provider environment variable
(concept C7/D.3 step 2). The root is the normalized ``project_dir``; a nested
``.agent-meta`` checkout is not part of the jail and is skipped, mirroring
``hook_is_meta_submodule_dir`` in hook_common.sh.

Issue #1275a: writes under ``external/``, ``.agent-meta/`` and every valid
``.gitmodules`` submodule path are denied.  ``AM_ALLOW_PROTECTED_WRITE=1``
bypasses only that protected-path gate; it never widens the jail root.  Reads
still defer.  This mirrors the deployed flat hook module and remains a
convention boundary, not a security boundary.
"""
from __future__ import annotations

import os
import posixpath
import re
import shlex
from typing import Optional

from .model import Decision, NormEvent

_META_SUBMODULE = ".agent-meta"
_DEFAULT_PROTECTED_PATHS = ("external", _META_SUBMODULE)
_GITMODULES_PATH_RE = re.compile(r"^\s*path\s*=\s*(.*?)\s*$", re.IGNORECASE)
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")


def _within(base, target):
    try:
        normalized_base = os.path.normcase(base)
        return os.path.commonpath(
            [normalized_base, os.path.normcase(target)]
        ) == normalized_base
    except ValueError:
        return False


def _gitmodules_paths(root):
    try:
        with open(os.path.join(root, ".gitmodules"), encoding="utf-8") as handle:
            lines = handle.readlines()
    except (OSError, UnicodeError):
        return []

    paths = []
    for line in lines:
        match = _GITMODULES_PATH_RE.match(line)
        if match is None:
            continue
        lexer = shlex.shlex(match.group(1), posix=True)
        lexer.whitespace = "\t\r\n"
        lexer.whitespace_split = True
        lexer.commenters = "#;"
        try:
            values = list(lexer)
        except ValueError:
            continue
        if len(values) == 1 and values[0].strip():
            paths.append(values[0].strip())
    return paths


def _protected_roots(root):
    roots = []
    for raw in (*_DEFAULT_PROTECTED_PATHS, *_gitmodules_paths(root)):
        canonical = raw.replace("\\", "/")
        if not canonical or _WINDOWS_DRIVE_RE.match(canonical):
            continue
        normalized = posixpath.normpath(canonical)
        if normalized in (".", "..") or normalized.startswith(("../", "/")):
            continue
        candidate = os.path.realpath(os.path.join(root, normalized))
        if candidate == root or not _within(root, candidate):
            continue
        if candidate not in roots:
            roots.append(candidate)
    return roots


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

    audit = {"path": target, "root": root}
    if not _within(root, target):
        return Decision.deny("containment.outside-root", audit)

    if os.environ.get("AM_ALLOW_PROTECTED_WRITE") != "1":
        parts = os.path.relpath(target, root).split(os.sep)
        if parts and parts[0] == _META_SUBMODULE:
            return Decision.deny("containment.meta-submodule", audit)
        for protected_root in _protected_roots(root):
            if _within(protected_root, target):
                return Decision.deny("containment.protected-path", audit)
    return Decision.allow("containment.within-root", audit)
