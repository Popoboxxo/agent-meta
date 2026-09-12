"""Repo-containment ("prison mode") resolution and tmp-sink provisioning.

This module is a *library*: it never calls ``sys.exit`` and never writes to a
hard error channel (stderr). Structural problems that the sync-time validator
(``scripts/lib/config.py::_validate_repo_containment``) hard-rejects are
reported here as non-fatal :class:`ContainmentFinding` entries, so runtime
consumers (hook-support check, variable building, gitignore logic) can degrade
safe-side instead of aborting.

Resolution precedence (spec
``docs/concepts/repo-containment-prison-mode.md`` §2.3)::

    provider-override > project repo_containment.enabled > framework default true

Provider selection is data-driven through
``config["repo_containment"]["provider-overrides"]`` keyed by the registered
provider name. There is intentionally no ``if provider == "Name"`` branch
anywhere in this module (provider-agnostic policy).
"""
from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Framework defaults (spec §2.1) — single source of truth shared by the
# non-exiting resolver and the Q1 materialization block.
# ---------------------------------------------------------------------------
DEFAULT_REPO_CONTAINMENT_ENABLED = True
DEFAULT_TMP_SINK_ENABLED = True
DEFAULT_TMP_SINK_PATH = ".tmp"
DEFAULT_TMP_SINK_GITIGNORE = True
DEFAULT_TMP_SINK_CLEANUP = "manual"
TMP_SINK_CLEANUP_MODES = ("manual", "on-sync")

# Self-ignoring fallback written as ``<sink>/.gitignore`` (spec §5.3). Works
# provider-agnostically, independent of the Claude-gated managed block.
TMP_SINK_GITIGNORE_FILENAME = ".gitignore"
TMP_SINK_GITIGNORE_CONTENT = "*\n!.gitignore\n"

# A leading ``<letter>:`` marks an absolute path on Windows. ``os.path.isabs``
# does not catch it on POSIX, so reject it explicitly here to keep the rule
# identical across platforms (mirrors the Admin-UI client-side validation).
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")

#: Which precedence level produced the effective master switch.
SOURCE_PROVIDER_OVERRIDE = "provider-override"
SOURCE_PROJECT = "project"
SOURCE_DEFAULT = "default"
SOURCE_SAFE_FALLBACK = "safe-fallback"

_UNSET = object()


@dataclass
class ContainmentFinding:
    """One non-fatal resolution finding (never raises, never exits)."""

    level: str  # "warning" (reserved for future severity levels)
    code: str  # stable machine-readable id, e.g. "repo-containment.enabled-type"
    message: str


@dataclass
class ResolvedRepoContainment:
    """Effective repo-containment state for one config/provider pair.

    Attributes:
        enabled: effective master switch (provider override > project >
            framework default) with safe-side fallback to ``True`` for a
            non-boolean/unresolvable value.
        source: which precedence level produced ``enabled`` — one of
            :data:`SOURCE_PROVIDER_OVERRIDE`, :data:`SOURCE_PROJECT`,
            :data:`SOURCE_DEFAULT`, :data:`SOURCE_SAFE_FALLBACK`.
        provider: provider name the resolution was requested for (or ``None``).
        tmp_sink_enabled: whether the scratch sink is sanctioned/provisioned.
        tmp_sink_path: validated project-relative scratch path.
        tmp_sink_gitignore: whether the framework should gitignore the sink.
        cleanup: ``"manual"`` or ``"on-sync"``.
        findings: non-fatal problems seen while resolving (safe-side
            fallbacks, wrong types, invalid tmp-sink path).
    """

    enabled: bool
    source: str
    provider: str | None = None
    tmp_sink_enabled: bool = DEFAULT_TMP_SINK_ENABLED
    tmp_sink_path: str = DEFAULT_TMP_SINK_PATH
    tmp_sink_gitignore: bool = DEFAULT_TMP_SINK_GITIGNORE
    cleanup: str = DEFAULT_TMP_SINK_CLEANUP
    findings: list[ContainmentFinding] = field(default_factory=list)

    @property
    def has_findings(self) -> bool:
        """True when at least one non-fatal finding was collected."""
        return bool(self.findings)


@dataclass
class TmpSinkCleanupOutcome:
    """Result of applying the resolved tmp-sink cleanup policy (spec §5.4).

    Attributes:
        sink_path: resolved scratch directory the policy applied to.
        cleanup: the effective cleanup mode (always ``"on-sync"`` when this
            outcome is returned — ``"manual"`` never yields an outcome).
        removed: top-level entry names that were deleted (or, in dry-run,
            would be deleted).
        performed: True only when deletions actually happened; always False
            in dry-run.
        dry_run: whether this was a report-only pass.
    """

    sink_path: Path
    cleanup: str
    removed: list[str] = field(default_factory=list)
    performed: bool = False
    dry_run: bool = False


@dataclass
class TmpSinkGitignoreOutcome:
    """Result of ensuring the self-ignoring ``<sink>/.gitignore`` fallback.

    Attributes:
        path: target file, or ``None`` when the fallback does not apply (sink
            or ``tmp-sink.gitignore`` disabled, invalid input, ...).
        changed: True when the file was (or, in dry-run, would be) written;
            False when it already had the expected content (idempotent).
        dry_run: whether this was a report-only pass.
    """

    path: Path | None = None
    changed: bool = False
    dry_run: bool = False


def _resolve_sink_dir(
    project_root: str | os.PathLike[str],
    effective: ResolvedRepoContainment,
) -> Path | None:
    """Resolve (and defensively re-validate) the sink directory, else None.

    Shared by :func:`ensure_tmp_sink`, :func:`cleanup_tmp_sink` and
    :func:`ensure_tmp_sink_gitignore`. Returns ``None`` when the sink is
    disabled, when the configured path would escape ``project_root`` (after
    symlink resolution) or when the sink directory **is itself a symlink**.

    Security note (spec §5.4): the naive ``normpath``/``commonpath`` check does
    not resolve symlinks. A ``.tmp`` symlink pointing outside the root would
    make ``ensure_tmp_sink_gitignore`` write and -- far worse -- make
    ``cleanup_tmp_sink`` with ``cleanup: on-sync`` DELETE outside the project.
    Both sides are therefore resolved with :func:`os.path.realpath`, containment
    is re-checked on the real paths, and a symlinked sink is refused outright.
    """
    if not isinstance(effective, ResolvedRepoContainment):
        return None
    if not effective.tmp_sink_enabled:
        return None

    root = os.fspath(project_root)
    root_real = os.path.realpath(root)
    target = os.path.normpath(os.path.join(root, effective.tmp_sink_path))

    # A sink that is itself a symlink is never trustworthy: the link target can
    # change at any time between the containment check and the write/delete.
    if os.path.islink(target):
        return None

    target_real = os.path.realpath(target)
    # A sink path that canonicalizes to the project root itself (``.``,
    # ``./.``, ``""``, ...) is refused: ``commonpath`` would otherwise accept
    # it, and a manually constructed ResolvedRepoContainment would let
    # cleanup_tmp_sink("on-sync") delete top-level project entries (spec §5.4).
    if target_real == root_real:
        return None
    try:
        if os.path.commonpath([root_real, target_real]) != root_real:
            return None
    except ValueError:
        return None
    return Path(target)


def tmp_sink_path_error(
    path: Any,
    project_root: str | os.PathLike[str] | None = None,
) -> str | None:
    """Return an error string when *path* is not a safe scratch path, else None.

    Rules (spec §4.3): non-empty string, relative, not ``.``/``..`` and
    without a ``..`` segment; after ``os.path.normpath`` it must not escape
    ``project_root`` (checked when *project_root* is provided). Shared by the
    non-exiting resolver and the hard sync-time validator so both enforce the
    exact same rule set.
    """
    if not isinstance(path, str):
        return f"expected a string, got {type(path).__name__}"
    if not path.strip():
        return "must not be empty"
    if os.path.isabs(path):
        return "must be relative to the project root (absolute paths are not allowed)"
    if _WINDOWS_DRIVE_RE.match(path):
        return "must be relative to the project root (drive-letter paths are not allowed)"
    if path in (".", ".."):
        return f"must not be {path!r}"
    segments = path.replace("\\", "/").split("/")
    if any(segment == ".." for segment in segments):
        return "must not contain '..' segments"
    normalized = os.path.normpath(path)
    if normalized in ("", ".", "..") or normalized.startswith(".." + os.sep):
        return "must not escape the project root"
    if project_root is not None:
        # ``project_root`` itself may be relative (e.g. ``"."`` when validating
        # a config that lives right here). ``os.path.commonpath`` returns ``""``
        # for two relative paths and would falsely report an escape, so resolve
        # BOTH sides against the current working directory first.
        root = os.path.abspath(os.fspath(project_root))
        target = os.path.abspath(os.path.join(root, normalized))
        try:
            if os.path.commonpath([root, target]) != root:
                return "must not escape the project root"
        except ValueError:
            return "must not escape the project root"
    return None


def default_repo_containment_block() -> dict:
    """Return a fresh default ``repo_containment`` block for Q1 materialization.

    A new dict per call so callers can mutate it without aliasing the module
    constants (spec §2.1 defaults: ``enabled: true`` plus tmp-sink defaults).
    """
    return {
        "enabled": DEFAULT_REPO_CONTAINMENT_ENABLED,
        "tmp-sink": {
            "enabled": DEFAULT_TMP_SINK_ENABLED,
            "path": DEFAULT_TMP_SINK_PATH,
            "gitignore": DEFAULT_TMP_SINK_GITIGNORE,
            "cleanup": DEFAULT_TMP_SINK_CLEANUP,
        },
    }


def _resolve_enabled(
    rc: dict,
    provider: str | None,
    findings: list[ContainmentFinding],
) -> tuple[bool, str]:
    """Resolve the master switch with precedence and safe-side fallback."""
    overrides = rc.get("provider-overrides")
    if overrides is not None and not isinstance(overrides, dict):
        findings.append(ContainmentFinding(
            "warning",
            "repo-containment.provider-overrides-type",
            "'repo_containment.provider-overrides' should be a mapping, got "
            f"{type(overrides).__name__}; provider overrides ignored.",
        ))
        overrides = None

    if isinstance(overrides, dict) and isinstance(provider, str):
        entry = overrides.get(provider)
        if entry is not None and not isinstance(entry, dict):
            findings.append(ContainmentFinding(
                "warning",
                "repo-containment.provider-override-entry-type",
                f"'repo_containment.provider-overrides.{provider}' should be a "
                f"mapping, got {type(entry).__name__}; falling back to the project value.",
            ))
        elif isinstance(entry, dict) and "enabled" in entry:
            value = entry["enabled"]
            if isinstance(value, bool):
                return value, SOURCE_PROVIDER_OVERRIDE
            findings.append(ContainmentFinding(
                "warning",
                "repo-containment.enabled-type",
                f"'repo_containment.provider-overrides.{provider}.enabled' must be "
                f"a boolean, got {type(value).__name__}; defaulting safe-side to enabled.",
            ))
            return True, SOURCE_SAFE_FALLBACK

    if "enabled" in rc:
        value = rc["enabled"]
        if isinstance(value, bool):
            return value, SOURCE_PROJECT
        findings.append(ContainmentFinding(
            "warning",
            "repo-containment.enabled-type",
            "'repo_containment.enabled' must be a boolean, got "
            f"{type(value).__name__}; defaulting safe-side to enabled.",
        ))
        return True, SOURCE_SAFE_FALLBACK

    return DEFAULT_REPO_CONTAINMENT_ENABLED, SOURCE_DEFAULT


def _resolve_bool(
    value: Any,
    default: bool,
    label: str,
    findings: list[ContainmentFinding],
) -> bool:
    """Return *value* when it is a bool, else *default* plus a WARNING finding."""
    if value is _UNSET:
        return default
    if isinstance(value, bool):
        return value
    findings.append(ContainmentFinding(
        "warning",
        "repo-containment.tmp-sink-type",
        f"'repo_containment.{label}' must be a boolean, got "
        f"{type(value).__name__}; using default {default!r}.",
    ))
    return default


def resolve_effective_repo_containment(
    config: dict | None,
    provider: str | None = None,
) -> ResolvedRepoContainment:
    """Resolve the effective repo-containment state — never exits, never raises.

    Precedence per spec §2.3: provider override > project value > framework
    default ``True``. Every nesting access is defended with
    ``isinstance(..., dict)`` guards. A present-but-non-boolean ``enabled``
    falls back safe-side to ``True`` and emits a WARNING finding (F4).

    The tmp-sink settings are resolved independently of the master switch,
    each falling back to its framework default.
    """
    findings: list[ContainmentFinding] = []

    raw = config.get("repo_containment") if isinstance(config, dict) else None
    if raw is not None and not isinstance(raw, dict):
        findings.append(ContainmentFinding(
            "warning",
            "repo-containment.not-mapping",
            "'repo_containment' should be a mapping, got "
            f"{type(raw).__name__}; using framework defaults.",
        ))
        raw = None
    rc: dict = raw if isinstance(raw, dict) else {}

    enabled, source = _resolve_enabled(rc, provider, findings)

    sink_raw = rc.get("tmp-sink")
    if sink_raw is not None and not isinstance(sink_raw, dict):
        findings.append(ContainmentFinding(
            "warning",
            "repo-containment.tmp-sink-not-mapping",
            "'repo_containment.tmp-sink' should be a mapping, got "
            f"{type(sink_raw).__name__}; using framework defaults.",
        ))
        sink_raw = None
    sink: dict = sink_raw if isinstance(sink_raw, dict) else {}

    sink_enabled = _resolve_bool(
        sink.get("enabled", _UNSET), DEFAULT_TMP_SINK_ENABLED,
        "tmp-sink.enabled", findings,
    )
    sink_gitignore = _resolve_bool(
        sink.get("gitignore", _UNSET), DEFAULT_TMP_SINK_GITIGNORE,
        "tmp-sink.gitignore", findings,
    )

    cleanup = sink.get("cleanup", _UNSET)
    if cleanup is _UNSET or cleanup is None:
        cleanup = DEFAULT_TMP_SINK_CLEANUP
    elif cleanup not in TMP_SINK_CLEANUP_MODES:
        findings.append(ContainmentFinding(
            "warning",
            "repo-containment.tmp-sink-cleanup",
            "'repo_containment.tmp-sink.cleanup' must be one of "
            f"{', '.join(TMP_SINK_CLEANUP_MODES)}, got {cleanup!r}; "
            f"using {DEFAULT_TMP_SINK_CLEANUP!r}.",
        ))
        cleanup = DEFAULT_TMP_SINK_CLEANUP

    path = sink.get("path", _UNSET)
    if path is _UNSET or path is None:
        path = DEFAULT_TMP_SINK_PATH
    else:
        error = tmp_sink_path_error(path)
        if error:
            findings.append(ContainmentFinding(
                "warning",
                "repo-containment.tmp-sink-path",
                f"'repo_containment.tmp-sink.path' is invalid ({error}); "
                f"using {DEFAULT_TMP_SINK_PATH!r}.",
            ))
            path = DEFAULT_TMP_SINK_PATH

    return ResolvedRepoContainment(
        enabled=enabled,
        source=source,
        provider=provider,
        tmp_sink_enabled=sink_enabled,
        tmp_sink_path=path,
        tmp_sink_gitignore=sink_gitignore,
        cleanup=cleanup,
        findings=findings,
    )


def ensure_tmp_sink(
    project_root: str | os.PathLike[str],
    effective: ResolvedRepoContainment,
    dry_run: bool = False,
) -> Path | None:
    """Provision ``<project_root>/<tmp-sink.path>`` when the sink is enabled.

    Idempotent (``os.makedirs(..., exist_ok=True)``) and **never deletes**
    anything. In ``dry_run`` the target path is only computed, never created.
    Returns the resolved sink :class:`Path` when the sink is enabled (also in
    dry-run, so callers can log it), else ``None``.

    The path is re-validated defensively: a manually constructed
    :class:`ResolvedRepoContainment` with an escaping path provisions nothing.
    """
    sink_dir = _resolve_sink_dir(project_root, effective)
    if sink_dir is None:
        return None
    if not dry_run:
        os.makedirs(sink_dir, exist_ok=True)
    return sink_dir


def _remove_entry(path: Path) -> None:
    """Delete one filesystem entry (file, symlink or directory tree)."""
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def cleanup_tmp_sink(
    project_root: str | os.PathLike[str],
    effective: ResolvedRepoContainment,
    dry_run: bool = False,
) -> TmpSinkCleanupOutcome | None:
    """Apply the resolved tmp-sink cleanup policy (spec §5.4).

    Returns ``None`` when nothing applies: the sink is disabled/invalid, or the
    policy is the safe default ``"manual"``. ``"manual"`` NEVER touches the
    filesystem — the directory may hold scratch artifacts whose loss would
    destroy a run, so the default is non-destructive.

    Only the explicit opt-in ``"on-sync"`` produces an outcome and empties the
    directory **contents**; the directory itself is never removed. ``dry_run``
    reports the entries that would be deleted without deleting them.
    """
    sink_dir = _resolve_sink_dir(project_root, effective)
    if sink_dir is None or effective.cleanup != "on-sync":
        return None

    removed: list[str] = []
    if sink_dir.is_dir():
        for child in sorted(sink_dir.iterdir(), key=lambda p: p.name):
            removed.append(child.name)
            if not dry_run:
                _remove_entry(child)

    return TmpSinkCleanupOutcome(
        sink_path=sink_dir,
        cleanup=effective.cleanup,
        removed=removed,
        performed=bool(removed) and not dry_run,
        dry_run=dry_run,
    )


def ensure_tmp_sink_gitignore(
    project_root: str | os.PathLike[str],
    effective: ResolvedRepoContainment,
    dry_run: bool = False,
) -> TmpSinkGitignoreOutcome:
    """Ensure the self-ignoring ``<sink>/.gitignore`` fallback (spec §5.3).

    Applies only when the sink is enabled **and** ``tmp-sink.gitignore`` is
    true. The file contains ``*`` plus a negation for itself, so the scratch
    directory stays untracked even on providers where the agent-meta managed
    block is Claude-gated. Idempotent: identical existing content is left
    untouched (``changed=False``); ``dry_run`` never writes.
    """
    if not isinstance(effective, ResolvedRepoContainment):
        return TmpSinkGitignoreOutcome()
    if not (effective.tmp_sink_enabled and effective.tmp_sink_gitignore):
        return TmpSinkGitignoreOutcome()

    sink_dir = _resolve_sink_dir(project_root, effective)
    if sink_dir is None:
        return TmpSinkGitignoreOutcome()

    path = sink_dir / TMP_SINK_GITIGNORE_FILENAME
    existing: str | None = None
    if path.is_file():
        try:
            existing = path.read_text(encoding="utf-8")
        except OSError:
            existing = None
    if existing == TMP_SINK_GITIGNORE_CONTENT:
        return TmpSinkGitignoreOutcome(path=path, changed=False, dry_run=dry_run)

    if not dry_run:
        os.makedirs(sink_dir, exist_ok=True)
        path.write_text(TMP_SINK_GITIGNORE_CONTENT, encoding="utf-8")
    return TmpSinkGitignoreOutcome(path=path, changed=True, dry_run=dry_run)
