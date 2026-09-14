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

from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from .io import safe_path
from .log import SyncLog

ContentPredicate = Callable[[Path, str], bool]
# (path, file_text) -> True iff the file carries agent-meta provenance.


def _relative_posix(path: Path, project_root: Path) -> str:
    """Project-relative posix form of *path*; falls back to str() if outside."""
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return str(path)


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
    content_marker: Optional[str] = None,
    content_predicate: Optional[ContentPredicate] = None,
) -> set[str]:
    """Determine the 'previously managed' set for a stale-cleanup diff.

    Index-first: if the index exists and is readable, its contents win — even
    when empty (an empty index is a deliberate "nothing is managed" state and
    must never be widened by a predicate). If the index is absent or
    unreadable, falls back to globbing ``glob_pattern`` in ``target_dir`` and
    adopts only matches that carry provenance.

    content_marker: when the glob prefix isn't exclusive to this caller (e.g.
    ``mcp-*.md`` also matches an unrelated, manually-authored rule like
    ``mcp-guardrails.md``), pass a string that's only ever present in content
    this caller itself generates (its footer/attribution line) — glob matches
    without it are left alone instead of being swept as false-positive stale
    files.

    content_predicate: ``(path, file_text) -> bool`` provenance check. When
    supplied, only matches for which it returns True are adopted (in addition
    to ``content_marker`` matches). With neither a predicate nor a marker, an
    absent index adopts **nothing** (fail-closed) — a missing index must never
    degrade into a "delete everything unexpected" fallback.

    ``OSError`` / ``UnicodeDecodeError`` while reading a candidate file is
    treated as "no provenance" (never adopted). An unreadable index is also
    handled here (fail-closed predicate bootstrap); the caller may emit its
    own warning via ``read_managed_index``.
    """
    if index_path.exists():
        try:
            return read_managed_index(index_path)
        except (OSError, UnicodeDecodeError):
            # Corrupt/unreadable index: fall through to the fail-closed
            # predicate/marker bootstrap instead of propagating or deleting all.
            pass
    if not target_dir.is_dir():
        return set()
    candidates = target_dir.glob(glob_pattern)
    if content_marker is None and content_predicate is None:
        return set()
    result: set[str] = set()
    for p in candidates:
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if content_predicate is not None:
            try:
                if content_predicate(p, text):
                    result.add(p.name)
                    continue
            except (OSError, UnicodeDecodeError):
                continue
        if content_marker is not None and content_marker in text:
            result.add(p.name)
    return result


def cleanup_stale_managed_files(
    target_dir: Path,
    project_root: Path,
    previously_managed: set[str],
    now_managed: set[str],
    log: SyncLog,
    dry_run: bool,
    reason: str,
    backup: bool = False,
) -> list[str]:
    """Delete files present in ``previously_managed`` but not in ``now_managed``.

    With ``backup=True`` a ``<name>.sync-backup-<YYYYmmdd-HHMMSS>`` sibling is
    written (one timestamp per invocation) *before* the unlink, containing the
    pre-delete content. If the backup cannot be read/written, the file's unlink
    is skipped and a warning is logged, so one bad file cannot abort the sync.

    Returns the project-relative posix paths of the backups (written backups,
    or the would-be paths in ``dry_run``). Empty when ``backup=False``. The
    change from ``None`` to ``list[str]`` is backward compatible: existing
    callers ignore the result.
    """
    backups: list[str] = []
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    for stale_name in sorted(previously_managed - now_managed):
        stale_path = safe_path(target_dir, stale_name)
        if not stale_path.exists():
            continue
        rel = str(stale_path.relative_to(project_root))
        log.action("DELETE", rel, reason)
        backup_path = stale_path.with_name(f"{stale_name}.sync-backup-{ts}")
        if dry_run:
            if backup:
                backups.append(_relative_posix(backup_path, project_root))
            continue
        if backup:
            try:
                existing_content = stale_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                log.warning(
                    f"managed-index: could not read '{rel}' for backup: "
                    f"{type(exc).__name__}: {exc} — unlink skipped"
                )
                continue
            try:
                backup_path.write_text(existing_content, encoding="utf-8")
            except OSError as exc:
                log.warning(
                    f"managed-index: could not write backup for '{rel}': "
                    f"{type(exc).__name__}: {exc} — unlink skipped"
                )
                continue
            backups.append(_relative_posix(backup_path, project_root))
        stale_path.unlink()
    return backups


def write_managed_index(index_path: Path, now_managed: set[str], dry_run: bool) -> None:
    """Write the managed-index file, including when ``now_managed`` is empty.

    An empty set is a legitimate state (every server/tool got deactivated) —
    it must still be written so the index doesn't keep listing stale entries
    that cleanup_stale_managed_files() already deleted from disk. No-op only
    for dry_run.
    """
    if dry_run:
        return
    index_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(sorted(now_managed))
    index_path.write_text(f"{content}\n" if content else "", encoding="utf-8")
