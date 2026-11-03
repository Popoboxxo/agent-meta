"""Additive local allow-list writer (#1079/D20), data-driven via provider key."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from . import repo_containment as rc
from .io import read_json_lenient, write_atomic
from .log import SyncLog


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
                             log: SyncLog, dry_run: bool) -> None:
    """Add ``directories`` to the local allow-list additively (never remove)."""
    key = pc.get("settings-allow-dirs-key")
    settings_rel = pc.get("settings_local_file")
    if not key or not settings_rel or not directories:
        return
    path = Path(project_root) / settings_rel
    doc = None
    if path.exists():
        doc = read_json_lenient(path)
        if not isinstance(doc, dict):
            log.warn(f"settings-dirs: {settings_rel} is not valid JSON — "
                     "additionalDirectories not updated")
            return
    doc = doc if doc is not None else {}
    parts = [part for part in str(key).split(".") if part] or [str(key)]
    node = doc
    for part in parts[:-1]:
        child = node.get(part)
        if not isinstance(child, dict):
            child = {}
            node[part] = child
        node = child
    entries = node.get(parts[-1])
    if entries is None:
        node[parts[-1]] = entries = []
    if not isinstance(entries, list):
        log.warn(f"settings-dirs: {settings_rel} key {key!r} is not a list — "
                 "additionalDirectories not updated")
        return
    added = [directory for directory in directories if directory not in entries]
    if not added:
        log.skip(settings_rel, "allowed directories already present")
        return
    entries.extend(added)
    log.action("UPDATE", settings_rel, f"allowed directories: {', '.join(added)}")
    if dry_run:
        return
    write_atomic(path, json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
