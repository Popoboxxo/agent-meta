"""Configurable progress / checkpoint storage paths (leaf resolver).

Framework defaults keep the historical ``.meta-viz`` layout. A project may
relocate the two directories through the top-level ``progress`` block of
``.meta-config/project.yaml``::

    progress:
      dir: .run/progress
      checkpoint-dir: .run/checkpoints

Resolution mirrors ``scripts/lib/repo_containment.py`` (default plus project
override, findings instead of exceptions, traversal-validated paths): every
invalid value falls back to the framework default and emits at most one
``warning`` finding -- the resolver never raises and never exits.

This is a *leaf* module: it imports only the standard library, the repo-local
config loader (:mod:`lib.io`) and the shared path rules of
:mod:`lib.repo_containment` (which itself imports nothing from ``lib``). It must never import
``lib.checkpoint`` (the store imports this module), so no import cycle exists.
Provider-scoped behaviour does not exist here: the vestigial provider key
``checkpoint_dir`` is never consulted, and the code contains no provider
literal and no ``if provider == ...`` branch.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Tuple

from .io import SyncError, _load_yaml_or_json
from .repo_containment import canonical_tmp_sink_path, tmp_sink_path_error

DEFAULT_PROGRESS_DIR = ".meta-viz/progress"
DEFAULT_CHECKPOINT_DIR = ".meta-viz/checkpoints"

SOURCE_PROJECT = "project"
SOURCE_DEFAULT = "default"
SOURCE_SAFE_FALLBACK = "safe-fallback"

_PROGRESS_BLOCK = "progress"
_DIR_KEY = "dir"
_CHECKPOINT_DIR_KEY = "checkpoint-dir"

_UNSET = object()


@dataclass
class ProgressPathFinding:
    """One non-fatal resolution finding (never raises, never exits)."""

    level: str
    code: str
    message: str


@dataclass
class ResolvedProgressPaths:
    """Effective progress / checkpoint paths for one project root.

    Attributes:
        progress_dir: absolute progress-file directory, confined under
            ``project_root``.
        checkpoint_dir: absolute checkpoint directory, confined under
            ``project_root``.
        progress_rel: normalized, posix-form progress path relative to
            ``project_root``.
        checkpoint_rel: normalized, posix-form checkpoint path relative to
            ``project_root``.
        progress_source: one of :data:`SOURCE_PROJECT`,
            :data:`SOURCE_DEFAULT`, :data:`SOURCE_SAFE_FALLBACK`.
        checkpoint_source: source of the checkpoint directory.
        findings: non-fatal problems collected while resolving.
    """

    progress_dir: Path
    checkpoint_dir: Path
    progress_rel: str
    checkpoint_rel: str
    progress_source: str
    checkpoint_source: str
    findings: Tuple[ProgressPathFinding, ...]


def progress_path_error(
    path: object,
    project_root: Optional[Path] = None,
    *,
    pathmod: Any = os.path,
) -> Optional[str]:
    """Return an error string when *path* is not a safe relative path, else None.

    Delegates to ``repo_containment.tmp_sink_path_error`` so the validator, the
    resolver, the tmp-sink and the hook mirror share exactly one rule set
    (IC-15 Nr. 27 f, AC-97): relative only (no absolute, UNC, drive-letter),
    no ``..`` segment, no reserved Windows names, no trailing dot/space, ``:``
    or ``<>"|?*``/control characters, no protected directory (case-insensitive),
    and -- when *project_root* is given -- no link/junction escape. ``None``
    means valid; any other return value is the violation message.
    """
    return tmp_sink_path_error(path, project_root, pathmod=pathmod)


def _load_config_best_effort(root: Path) -> dict:
    """Best-effort read of ``<root>/.meta-config/project.{yaml,json}``.

    Identical contract to ``recovery._load_project_config``: an unreadable,
    malformed or non-mapping config yields ``{}`` and never raises.
    """
    try:
        data, _ = _load_yaml_or_json(
            root / ".meta-config" / "project.yaml",
            root / ".meta-config" / "project.json",
        )
    except (SyncError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _finding_suffix(raw: str) -> str:
    """Classify a rejected value as ``traversal`` or ``invalid``.

    A ``..`` segment is an active upward escape attempt (``traversal``); any
    other rejection (absolute path, drive-letter path, ``.``/``..``) keeps the
    stable ``invalid`` code.
    """
    segments = raw.replace("\\", "/").split("/")
    return "traversal" if ".." in segments else "invalid"


def _resolve_value(
    raw: object,
    default: str,
    key: str,
    root: Path,
    findings: list,
    *,
    force_fallback: bool,
) -> Tuple[str, str]:
    """Resolve one ``progress.<key>`` value to ``(relative_value, source)``.

    Precedence: explicit project value > framework default. A non-string value
    and a rejected path fall back to *default* with ``safe-fallback``; an
    empty/whitespace-only string is treated as absent (``default``, no
    finding). Never raises.
    """
    if force_fallback:
        return default, SOURCE_SAFE_FALLBACK
    if raw is _UNSET:
        return default, SOURCE_DEFAULT
    if not isinstance(raw, str):
        findings.append(ProgressPathFinding(
            "warning",
            "progress.{0}-type".format(key),
            "'progress.{0}' must be a string, got {1}; using framework default "
            "{2!r}.".format(key, type(raw).__name__, default),
        ))
        return default, SOURCE_SAFE_FALLBACK
    if not raw.strip():
        return default, SOURCE_DEFAULT
    error = progress_path_error(raw, root)
    if error is not None:
        findings.append(ProgressPathFinding(
            "warning",
            "progress.{0}-{1}".format(key, _finding_suffix(raw)),
            "'progress.{0}' is not a safe project-relative path ({1}); using "
            "framework default {2!r}.".format(key, error, default),
        ))
        return default, SOURCE_SAFE_FALLBACK
    return raw, SOURCE_PROJECT


def _absolute_and_rel(root: Path, rel: str) -> Tuple[Path, str]:
    """Return ``(absolute_path, posix_relative_path)`` for a project-relative value."""
    normalized = canonical_tmp_sink_path(rel)
    absolute = Path(os.path.abspath(os.path.join(str(root), *normalized.split("/"))))
    return absolute, normalized


def resolve_progress_paths(
    project_root: Path,
    config: Optional[dict] = None,
) -> ResolvedProgressPaths:
    """Resolve the progress / checkpoint directories for *project_root*.

    Reads exactly one configuration source -- the top-level ``progress`` block
    of *config* (or of ``.meta-config/project.yaml`` when *config* is ``None``)
    -- over exactly one framework default set. Never raises, never exits.
    """
    root = Path(project_root)
    findings: list = []

    if config is None:
        config = _load_config_best_effort(root)
    elif not isinstance(config, dict):
        config = {}

    raw_block = config.get(_PROGRESS_BLOCK)
    if raw_block is None:
        block: dict = {}
        force_fallback = False
    elif isinstance(raw_block, dict):
        block = raw_block
        force_fallback = False
    else:
        findings.append(ProgressPathFinding(
            "warning",
            "progress.not-mapping",
            "'progress' should be a mapping, got {0}; using framework "
            "defaults.".format(type(raw_block).__name__),
        ))
        block = {}
        force_fallback = True

    progress_raw, progress_source = _resolve_value(
        _UNSET if force_fallback else block.get(_DIR_KEY, _UNSET),
        DEFAULT_PROGRESS_DIR, _DIR_KEY, root, findings,
        force_fallback=force_fallback,
    )
    checkpoint_raw, checkpoint_source = _resolve_value(
        _UNSET if force_fallback else block.get(_CHECKPOINT_DIR_KEY, _UNSET),
        DEFAULT_CHECKPOINT_DIR, _CHECKPOINT_DIR_KEY, root, findings,
        force_fallback=force_fallback,
    )

    progress_dir, progress_rel = _absolute_and_rel(root, progress_raw)
    checkpoint_dir, checkpoint_rel = _absolute_and_rel(root, checkpoint_raw)

    return ResolvedProgressPaths(
        progress_dir=progress_dir,
        checkpoint_dir=checkpoint_dir,
        progress_rel=progress_rel,
        checkpoint_rel=checkpoint_rel,
        progress_source=progress_source,
        checkpoint_source=checkpoint_source,
        findings=tuple(findings),
    )
