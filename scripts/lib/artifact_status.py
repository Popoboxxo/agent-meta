"""Report + data-file helpers for the artifact-locations matrix (Issue #1186, T15).

Two public surfaces live here, both fed by the single resolver in
:mod:`lib.artifact_locations` (no second resolution logic):

* :func:`build_report` / :func:`render_table` power ``sync.py --status-artifacts``
  (human table and the additive JSON contract ``schema_version: "1"``).
* :func:`build_resolved_payload` produces ``.meta-config/artifact-locations.resolved.json``
  (Stage 14c), the shared data file read by the path-guard hooks, the
  containment hook (D1) and the baseline of the T14 consistency check.

Design constraints:

* ``*.sync-backup-*`` siblings never contribute to counts or to the baseline
  inventory (#1195) — the shared ``artifact_file_stats`` helper enforces this.
* ``naming``, ``field_sources`` and ``kinds`` are additive: a class without a
  naming pattern simply omits the key, an unmanaged path is never a class (D8).
* Pure with respect to ``config``; never calls ``sys.exit`` and never branches
  on a provider name.
"""
from __future__ import annotations

import fnmatch
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from .artifact_locations import (
    CLASS_REGISTRY,
    artifact_file_stats,
    resolve_artifact_locations,
)

#: Machine contract version of both the report and the resolved data file.
SCHEMA_VERSION = "1"

#: Relative path of the data file written by Stage 14c.
RESOLVED_RELPATH = Path(".meta-config") / "artifact-locations.resolved.json"

_BACKUP_MARKER = ".sync-backup-"
_MARKER_FILENAMES = frozenset({".gitkeep", ".gitignore", ".keep"})
_SKIP_DIRS = frozenset({".git", "__pycache__", ".pytest_cache", ".venv", "node_modules"})


# ---------------------------------------------------------------------------
# Small shared helpers
# ---------------------------------------------------------------------------
def _pattern_matches(relpath: str, pattern: str) -> bool:
    """Match a project-relative path against a ``legacy[]``/``unmanaged[]`` pattern.

    Mirrors the three shapes used by the framework presets: recursive
    ``dir/**``, directory prefixes and fnmatch file patterns.
    """
    pattern = pattern.replace("\\", "/")
    if not pattern:
        return False
    if pattern.endswith("/**"):
        return relpath.startswith(pattern[:-2])
    if pattern.endswith("/"):
        return relpath.startswith(pattern)
    if "**" in pattern:
        return relpath.startswith(pattern.split("**", 1)[0])
    if any(char in pattern for char in "*?["):
        return fnmatch.fnmatchcase(relpath, pattern)
    return relpath == pattern or relpath.startswith(pattern + "/")


def _matches_any(relpath: str, patterns: Iterable[str]) -> bool:
    return any(_pattern_matches(relpath, pattern) for pattern in patterns)


def _iter_project_files(project_root: Path) -> Iterable[Path]:
    root = Path(project_root)
    if not root.is_dir():
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def _class_stats(path: str, project_root: Path) -> tuple[int, Optional[str]]:
    """Count class files and find the newest, ignoring backup siblings (#1195)."""
    if not path:
        return 0, None
    directory = Path(project_root) / path
    if not directory.is_dir():
        return 0, None
    names = [item.name for item in directory.rglob("*") if item.is_file()]
    return artifact_file_stats(names)


def _class_violations(name: str, cls: Any) -> list[dict]:
    """Report classes the status command cannot fully resolve.

    The Python validator only checks *non-empty* paths, so an explicitly blank
    path slips through validation yet leaves a ``files`` class unresolvable.
    Each finding carries the stable ``{code, path, expected}`` shape.
    """
    violations: list[dict] = []
    form = CLASS_REGISTRY[name].form if name in CLASS_REGISTRY else "directory"
    if cls.mode == "files" and form != "file-set":
        if not cls.path:
            violations.append({
                "code": "artifact-locations.path-missing",
                "path": name,
                "expected": "a non-empty project-relative path",
            })
        elif cls.path.startswith("/") or ".." in cls.path.split("/"):
            violations.append({
                "code": "artifact-locations.path-invalid",
                "path": name,
                "expected": "a path inside the project root",
            })
    if form == "file-set" and not cls.files:
        violations.append({
            "code": "artifact-locations.files-missing",
            "path": name,
            "expected": "at least one declared project-docs file",
        })
    return violations


# ---------------------------------------------------------------------------
# Public report API
# ---------------------------------------------------------------------------
def build_report(config: dict, agent_meta_root: Path, project_root: Path) -> dict:
    """Build the ``--status-artifacts`` report from the single resolver.

    ``classes`` is a mapping keyed by class name (23 entries); each entry has
    the required ``mode``/``source``/``exists`` plus additive fields. The
    ``unmanaged`` list is a top-level entry and never a class (D8, AC-12).
    """
    matrix = resolve_artifact_locations(config, agent_meta_root, project_root)
    classes: dict[str, dict] = {}
    for name, cls in matrix.classes.items():
        path = cls.path or ""
        if path:
            file_count, newest = _class_stats(path, project_root)
            exists = (Path(project_root) / path).exists()
        else:
            file_count, newest = 0, None
            exists = bool(cls.files) and all(
                (Path(project_root) / value).exists() for value in cls.files.values()
            )

        entry: dict[str, Any] = {
            "mode": cls.mode,
            "source": cls.source,
            "exists": exists,
            "kinds": list(cls.kinds),
            "subdir": cls.subdir,
            "field_sources": dict(cls.field_sources),
            "file_count": file_count,
            "newest": newest,
            "legacy_hits": _legacy_hits(path, matrix.legacy),
            "violations": _class_violations(name, cls),
        }
        if path:
            entry["path"] = path
        else:
            entry["files"] = dict(cls.files)
        if cls.naming:  # D3: naming is additive, absent for file-set/ephemeral/state
            entry["naming"] = cls.naming
        classes[name] = entry

    return {
        "schema_version": SCHEMA_VERSION,
        "preset": matrix.preset or "default",
        "enabled": matrix.enabled,
        "strict": matrix.strict,
        "classes": classes,
        "legacy": list(matrix.legacy),
        "unmanaged": list(matrix.unmanaged),
    }


def _legacy_hits(path: str, legacy: tuple[str, ...]) -> list[str]:
    """Legacy patterns that currently shadow this class path (read-only)."""
    return [pattern for pattern in legacy if path and _pattern_matches(path, pattern)]


def render_table(report: dict) -> str:
    """Render one row per class (23) as a stable human-readable table."""
    classes: dict[str, dict] = report.get("classes", {})
    lines = [
        f"Artifact locations (schema_version={report.get('schema_version')}, "
        f"preset={report.get('preset') or 'default'})",
        "",
        "  CLASS                MODE      TARGET                          SOURCE                   EXISTS FILES",
        "  " + "-" * 100,
    ]
    for name in sorted(classes):
        entry = classes[name]
        target = entry.get("path") or (
            "files: " + ", ".join(sorted(entry.get("files", {}).values()))
        )
        if len(target) > 30:
            target = target[:27] + "..."
        marker = "!" if entry.get("violations") else " "
        lines.append(
            f"{marker} {name:<20} {entry.get('mode', ''):<8} {target:<30} "
            f"{entry.get('source', ''):<24} {str(entry.get('exists', False)):<6} "
            f"{entry.get('file_count', 0):>5}"
        )
    lines.append("")
    lines.append(
        f"  {len(classes)} class(es); {len(report.get('unmanaged', []))} unmanaged "
        "path(s) (not classes)."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Resolved data-file payload (Stage 14c)
# ---------------------------------------------------------------------------
def _legacy_inventory(project_root: Path, matrix: Any) -> list[str]:
    """Inventory artifact files currently under a legacy[] pattern.

    Directory markers, backup siblings and unmanaged targets are excluded, so
    a clean scaffold produces an empty baseline (no false legacy-write finding).
    """
    root = Path(project_root)
    files: list[str] = []
    for path in _iter_project_files(root):
        if path.name in _MARKER_FILENAMES or _BACKUP_MARKER in path.name:
            continue
        relpath = path.relative_to(root).as_posix()
        if _matches_any(relpath, matrix.unmanaged):
            continue
        if _matches_any(relpath, matrix.legacy):
            files.append(relpath)
    return files


def build_resolved_payload(config: dict, agent_meta_root: Path, project_root: Path) -> dict:
    """Build the payload for ``.meta-config/artifact-locations.resolved.json``.

    ``classes`` is a *list* so hooks can filter by ``classes[].name`` (T16/T24);
    ``unmanaged`` and ``legacy`` stay top-level. The baseline carries the
    generated-at timestamp and the legacy artifact inventory used by T14.
    """
    matrix = resolve_artifact_locations(config, agent_meta_root, project_root)
    classes: list[dict] = []
    for name, cls in matrix.classes.items():
        patterns = list(cls.kinds)
        if cls.naming:
            patterns.append(cls.naming)
        if not patterns:
            patterns = sorted(cls.files.values())
        classes.append({
            "name": name,
            "path": cls.path or None,
            "mode": cls.mode,
            "naming": cls.naming,
            "patterns": patterns,
            "source": cls.source,
            "field_sources": dict(cls.field_sources),
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "enabled": matrix.enabled,
        "strict": matrix.strict,
        "root": str(project_root),
        "preset": matrix.preset or "default",
        "classes": classes,
        "legacy": list(matrix.legacy),
        "unmanaged": list(matrix.unmanaged),
        "baseline": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "legacy_files": _legacy_inventory(project_root, matrix),
        },
    }


__all__ = [
    "RESOLVED_RELPATH",
    "SCHEMA_VERSION",
    "build_report",
    "build_resolved_payload",
    "render_table",
]
