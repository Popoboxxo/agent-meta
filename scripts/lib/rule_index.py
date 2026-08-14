"""Shared managed-index helpers for provider rule-file write loops.

Multiple independent registries (``mcp.py``, ``external_tools.py``) each write
their own ``<prefix>*.md`` rule files into a provider's rules_dir and need to
detect and delete stale files once a server/tool becomes inactive or is
removed from its registry. This module centralizes that read/diff/cleanup/
write pattern so each registry module only supplies its own index filename,
glob prefix and the set of filenames it actually wrote this run — mirrors the
pattern already used by ``rules.py::sync_rules()`` for the ``rules/`` layer,
kept as a separate, independent index per caller so the write loops never
clash over the same index file.
"""
from __future__ import annotations

from pathlib import Path

from .io import safe_path
from .log import SyncLog


def read_managed_index(index_path: Path) -> set[str]:
    """Read a newline-delimited managed-index file. Empty set if missing."""
    if not index_path.exists():
        return set()
    return {
        line.strip()
        for line in index_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def bootstrap_previously_managed(
    target_dir: Path,
    index_path: Path,
    glob_pattern: str,
    content_marker: str | None = None,
) -> set[str]:
    """Determine the 'previously managed' set for a stale-cleanup diff.

    Reads the index file if present. If absent — e.g. the first run of a
    stale-cleanup mechanism added after rule files already existed on disk —
    falls back to globbing ``glob_pattern`` in ``target_dir`` so legacy
    orphans get swept on the very first sync instead of lingering forever
    with no index to diff against.

    content_marker: when the glob prefix isn't exclusive to this caller (e.g.
    ``mcp-*.md`` also matches an unrelated, manually-authored rule like
    ``mcp-guardrails.md``), pass a string that's only ever present in content
    this caller itself generates (its footer/attribution line) — glob matches
    without it are left alone instead of being swept as false-positive stale
    files. Without a marker, every glob match is treated as previously managed
    (legacy behavior).
    """
    if index_path.exists():
        return read_managed_index(index_path)
    if not target_dir.is_dir():
        return set()
    candidates = target_dir.glob(glob_pattern)
    if content_marker is None:
        return {p.name for p in candidates}
    result: set[str] = set()
    for p in candidates:
        try:
            if content_marker in p.read_text(encoding="utf-8"):
                result.add(p.name)
        except OSError:
            continue
    return result


def cleanup_stale_managed_files(
    target_dir: Path,
    project_root: Path,
    previously_managed: set[str],
    now_managed: set[str],
    log: SyncLog,
    dry_run: bool,
    reason: str,
) -> None:
    """Delete files present in ``previously_managed`` but not in ``now_managed``."""
    for stale_name in sorted(previously_managed - now_managed):
        stale_path = safe_path(target_dir, stale_name)
        if stale_path.exists():
            log.action("DELETE", str(stale_path.relative_to(project_root)), reason)
            if not dry_run:
                stale_path.unlink()


def write_managed_index(index_path: Path, now_managed: set[str], dry_run: bool) -> None:
    """Write the managed-index file. No-op for dry_run or an empty set."""
    if dry_run or not now_managed:
        return
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("\n".join(sorted(now_managed)) + "\n", encoding="utf-8")
