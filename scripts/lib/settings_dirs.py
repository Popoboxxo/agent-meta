"""Additive local allow-list writer (#1079/D20), data-driven via provider key."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from . import repo_containment as rc
from .io import (
    is_absent_gitignored_target,
    read_json_lenient,
    safe_path,
    write_atomic,
)
from .log import SyncLog

#: Return values of :func:`sync_allowed_directories`.
STATUS_WRITTEN = "written"
STATUS_SKIPPED = "skipped"
STATUS_WARNED = "warned"


def outside_project_dirs(project_root: Path, candidates: List[str]) -> List[str]:
    """Return the resolved, deduped candidates NOT under ``project_root``."""
    root = Path(project_root).resolve()
    outside: List[str] = []
    for candidate in candidates:
        text = str(candidate).strip()
        if not text:
            continue
        resolved = Path(text).expanduser().resolve()
        try:
            resolved.relative_to(root)
            continue
        except ValueError:
            pass
        if str(resolved) not in outside:
            outside.append(str(resolved))
    return outside

def basetemp_dirs(project_root: Path, config: Optional[dict]) -> List[str]:
    """Resolved pytest basetemp when outside the project; [] on config error."""
    from .tmp_paths import resolve_tmp_paths  # local: avoids an import cycle

    try:
        paths = resolve_tmp_paths(project_root, config)
    except rc.TmpSinkError:
        return []
    return outside_project_dirs(project_root, [paths.pytest_basetemp])

def sync_allowed_directories(project_root: Path, pc: dict, directories: List[str],
                             log: SyncLog, dry_run: bool) -> str:
    """Add ``directories`` to the local allow-list additively (never remove).

    The target is resolved through :func:`safe_path`, like every sibling writer:
    a path (or a symlinked directory/file) that resolves outside the project
    root is rejected with a warning and nothing is written. Symlinks that stay
    inside the project are followed — an in-root file symlink is preserved and
    its target receives the update.

    Returns one of ``written``, ``skipped`` or ``warned`` so callers can avoid
    reporting success when the writer only warned.
    """
    key = pc.get("settings-allow-dirs-key")
    settings_rel = pc.get("settings_local_file")
    if not key or not settings_rel or not directories:
        return STATUS_SKIPPED
    try:
        path = safe_path(Path(project_root), settings_rel)
    except ValueError:
        log.warn(f"settings-dirs: refusing to write {settings_rel} — "
                 "resolves outside the project root")
        return STATUS_WARNED
    if is_absent_gitignored_target(path, dry_run):
        # Fresh clone / CI: the gitignored target does not exist yet. Not
        # drift — ``--check``/``--dry-run`` must stay rc 0 (#752).
        log.skip(settings_rel, "absent (target root gitignored)")
        return STATUS_SKIPPED
    doc = None
    if path.exists():
        doc = read_json_lenient(path)
        if not isinstance(doc, dict):
            log.warn(f"settings-dirs: {settings_rel} is not valid JSON — "
                     "additionalDirectories not updated")
            return STATUS_WARNED
    doc = doc if doc is not None else {}
    parts = [part for part in str(key).split(".") if part] or [str(key)]
    node = doc
    missing = object()
    for part in parts[:-1]:
        child = node.get(part, missing)
        if child is missing:
            child = {}
            node[part] = child
        elif not isinstance(child, dict):
            # Never replace a user value: additive means "do not remove".
            log.warn(f"settings-dirs: {settings_rel} key {key!r} — "
                     f"{part!r} is not an object, not updated")
            return STATUS_WARNED
        node = child
    entries = node.get(parts[-1])
    if entries is None:
        node[parts[-1]] = entries = []
    if not isinstance(entries, list):
        log.warn(f"settings-dirs: {settings_rel} key {key!r} is not a list — "
                 "additionalDirectories not updated")
        return STATUS_WARNED
    added = [directory for directory in directories if directory not in entries]
    if not added:
        log.skip(settings_rel, "allowed directories already present")
        return STATUS_SKIPPED
    entries.extend(added)
    log.action("UPDATE", settings_rel, f"allowed directories: {', '.join(added)}")
    if dry_run:
        return STATUS_WRITTEN
    write_atomic(path, json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    return STATUS_WRITTEN
