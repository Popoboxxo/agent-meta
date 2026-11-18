"""Generalized artifact scaffolding for Issue #1186 (T8).

Creates one directory marker per managed ``files`` class plus the D-6 legacy
``docs/conclusions`` marker. The class set and the concrete paths come from the
single matrix resolver (``lib.artifact_locations``); this module never imports
the T14 consistency checker and never duplicates resolution logic.

The master switch ``artifact-locations.enabled`` guards the generalized path.
When it is off (or absent in the legacy sense), scaffolding falls back to the
three historical ``spec-plan-workflow.paths`` directories so that existing
projects keep today's behaviour.

``MARKER_FILENAMES`` is the single exemption source reused by the T14
consistency check and the T16 hook: a directory marker is not an artifact and
must never be reported as a write into a ``legacy[]`` tree.
"""
from __future__ import annotations

from pathlib import Path

from .artifact_locations import CLASS_REGISTRY, resolve_artifact_locations
from .dod import resolve_spec_plan_bundle
from .io import safe_path, write_checked
from .log import SyncLog

#: Marker filenames that are exempt from legacy-write detection (RVW2-1186-01).
MARKER_FILENAMES = frozenset({".gitkeep", ".gitignore", ".keep"})

#: D-6: the conclusions tree is a legacy target, not an artifact class. A single
#: marker scaffolds the directory without turning it into a managed class.
LEGACY_CONCLUSIONS_DIR = "docs/conclusions"

DEFAULT_SPECS_DIR = "docs/specs"
DEFAULT_PLANS_DIR = "docs/plans"
DEFAULT_SPIKES_DIR = "docs/spikes"

_SPEC_PLAN_CLASSES = frozenset({"specs", "plans", "spikes"})

_LEGACY_SOURCE = "spec-plan scaffolding"
_ARTIFACT_SOURCE = "artifact scaffolding"


def _scaffold_marker(
    project_root: Path,
    rel: str,
    log: SyncLog,
    dry_run: bool,
    source: str,
) -> None:
    """Create ``<rel>/.gitkeep`` idempotently and log the operation.

    A dry-run reports only markers that would actually be created: an existing
    marker is a no-op (recorded as unchanged) so ``sync.py --check`` stays clean
    on a synced checkout. Missing markers are still reported as CREATE in both
    dry-run and real runs; real runs stay incremental via ``write_checked``.
    """
    target = safe_path(project_root, rel)
    label = f"{rel}/.gitkeep"
    marker_path = target / ".gitkeep"
    if dry_run:
        if marker_path.exists():
            log.note_unchanged(label)
        else:
            log.action("CREATE", label, source)
        return
    target.mkdir(parents=True, exist_ok=True)
    if write_checked(marker_path, "", log, label):
        log.action("CREATE", label, source)
    else:
        log.note_unchanged(label)


def scaffold_legacy_spec_plan_dirs(
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Scaffold the three historical spec/plan/spike directories.

    Kept as a shared helper so ``spec_plan_scaffold.scaffold_spec_plan_dirs``
    can stay a thin, backward-compatible wrapper and the disabled-matrix
    fallback in :func:`scaffold_artifact_dirs` uses the exact same behaviour.
    """
    block = config.get("spec-plan-workflow") or {}
    paths = block.get("paths") or {}
    for key, default in (
        ("specs", DEFAULT_SPECS_DIR),
        ("plans", DEFAULT_PLANS_DIR),
        ("spikes", DEFAULT_SPIKES_DIR),
    ):
        rel = paths.get(key, default)
        target = safe_path(project_root, rel)
        if not dry_run:
            target.mkdir(parents=True, exist_ok=True)
        if write_checked(target / ".gitkeep", "", log, f"{rel}/.gitkeep",
                         dry_run=dry_run):
            log.action("CREATE", f"{rel}/.gitkeep", _LEGACY_SOURCE)


def scaffold_artifact_dirs(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Scaffold every ``files`` class directory plus the conclusions marker.

    Only classes with the directory form are scaffolded: SE cell roots are
    created by the SE workflow, ephemeral/state classes are gitignored and the
    file-set class has no own directory. ``mode: inline|off`` classes get no
    directory either. A disabled matrix falls back to the legacy three dirs.
    """
    matrix = resolve_artifact_locations(config, agent_meta_root, project_root)
    if not matrix.enabled:
        scaffold_legacy_spec_plan_dirs(project_root, config, log, dry_run)
        return

    # specs/plans/spikes stay governed by the spec-plan-workflow switch: a
    # disabled workflow must not scaffold them (scenarios 51/56).
    spec_plan_scaffold = resolve_spec_plan_bundle(config, agent_meta_root)["scaffold"]
    for name, spec in CLASS_REGISTRY.items():
        if spec.form != "directory":
            continue
        if name in _SPEC_PLAN_CLASSES and not spec_plan_scaffold:
            continue
        resolved = matrix.classes.get(name)
        if resolved is None or resolved.mode != "files" or not resolved.path:
            continue
        _scaffold_marker(project_root, resolved.path, log, dry_run,
                         _ARTIFACT_SOURCE)

    # D-6: scaffold the legacy conclusions tree as an empty, exempt marker.
    _scaffold_marker(project_root, LEGACY_CONCLUSIONS_DIR, log, dry_run,
                     _ARTIFACT_SOURCE)


__all__ = [
    "LEGACY_CONCLUSIONS_DIR",
    "MARKER_FILENAMES",
    "scaffold_artifact_dirs",
    "scaffold_legacy_spec_plan_dirs",
]
