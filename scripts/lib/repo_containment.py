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
import posixpath
import re
import shutil
import stat
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

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

# Windows-only path hazards, rejected on every host so a sink path means the
# same directory everywhere (IC-15 Nr. 27 a, F-45).
_WINDOWS_RESERVED_NAMES = frozenset(
    ["CON", "PRN", "AUX", "NUL"]
    + [f"COM{i}" for i in range(1, 10)]
    + [f"LPT{i}" for i in range(1, 10)]
)
_FORBIDDEN_SEGMENT_CHARS = frozenset('<>"|?*')

# Protected top-level names (compared case-insensitively) as sink or sink
# prefix. Provider directories come from ``provider_root_dirs`` in
# ``config/ai-providers.yaml`` (data-driven, no provider literals here); the
# static entries are the framework-owned directories plus a fallback.
_PROTECTED_STATIC = (".git", ".claude", ".meta-config")
_PROVIDERS_YAML = Path(__file__).resolve().parents[2] / "config" / "ai-providers.yaml"
_protected_cache: Optional[tuple] = None

# Test seam: called between resolving the sink dir and creating it
# (ensure_tmp_sink TOCTOU test, AC-93). Always ``None`` in production.
_TOCTOU_TEST_HOOK: Optional[Callable[[], None]] = None

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


def _protected_prefixes() -> tuple:
    """Lower-cased segment tuples that must not be a sink or sink prefix."""
    global _protected_cache
    if _protected_cache is not None:
        return _protected_cache
    entries = set(_PROTECTED_STATIC)
    try:
        import yaml  # PyYAML is a permitted dependency

        data = yaml.safe_load(_PROVIDERS_YAML.read_text(encoding="utf-8")) or {}
        providers = data.get("providers", data) if isinstance(data, dict) else {}
        for cfg in providers.values() if isinstance(providers, dict) else ():
            dirs = cfg.get("provider_root_dirs") if isinstance(cfg, dict) else None
            for entry in dirs or ():
                if isinstance(entry, str):
                    entries.add(entry)
    except Exception:  # noqa: BLE001 - registry unreadable => static list only
        pass
    prefixes = set()
    for entry in entries:
        segs = tuple(
            seg.lower() for seg in entry.replace("\\", "/").split("/") if seg not in ("", ".")
        )
        if segs:
            prefixes.add(segs)
    _protected_cache = tuple(sorted(prefixes))
    return _protected_cache


def canonical_tmp_sink_path(path: str) -> str:
    """Return the host-independent canonical form of a sink path.

    A backslash becomes ``/`` *before* ``normpath`` (IC-15 Nr. 27 b) and the
    normalization is always POSIX-style, so ``scratch\\out`` is the same
    directory on Linux and Windows.
    """
    return posixpath.normpath(path.replace("\\", "/"))


def _is_link_or_junction(path: str, pathmod: Any = os.path) -> bool:
    """True for a symlink, a junction or (Windows) any reparse point."""
    try:
        if pathmod.islink(path):
            return True
    except (OSError, ValueError):
        return True
    isjunction = getattr(pathmod, "isjunction", None)  # absent before Python 3.12
    if isjunction is not None:
        try:
            return bool(isjunction(path))
        except (OSError, ValueError):
            return True
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    try:
        attrs = getattr(os.stat(path, follow_symlinks=False), "st_file_attributes", None)
    except (OSError, ValueError):
        return False  # nonexistent component: nothing to follow
    return bool(attrs is not None and attrs & reparse)


def _lexical_error(path: str) -> Optional[str]:
    """Host-independent rules; returns an error string or None.

    Documented limits (no code fix): Windows 8.3 short names (e.g. ``GIT~1``
    for ``.git``) are not expanded lexically and therefore not matched against
    the protected prefixes.
    """
    if _WINDOWS_DRIVE_RE.match(path):
        return "must be relative to the project root (drive-letter paths are not allowed)"
    if path[:1] in ("/", "\\"):
        return "must be relative to the project root (absolute and UNC paths are not allowed)"
    if any(ord(ch) < 32 for ch in path):
        return "must not contain control characters"
    if path in (".", ".."):
        return f"must not be {path!r}"
    segments = path.replace("\\", "/").split("/")
    if any(segment == ".." for segment in segments):
        return "must not contain '..' segments"
    for segment in segments:
        if segment in ("", "."):
            continue
        if ":" in segment:
            return "must not contain ':' (NTFS data streams, drive prefixes)"
        if any(ch in _FORBIDDEN_SEGMENT_CHARS for ch in segment):
            return "must not contain any of the characters <>\"|?*"
        if segment[-1] in (".", " "):
            return "segments must not end with a dot or a space"
        if segment.split(".", 1)[0].rstrip(" ").upper() in _WINDOWS_RESERVED_NAMES:
            return "must not use a reserved Windows device name"
    normalized = canonical_tmp_sink_path(path)
    if normalized in ("", ".", "..") or normalized.startswith("../"):
        return "must not escape the project root"
    lowered = tuple(seg.lower() for seg in normalized.split("/"))
    for prefix in _protected_prefixes():
        if lowered[: len(prefix)] == prefix:
            return "must not be a protected directory (.git, .claude, .meta-config, provider directories)"
    return None


def _resolution_error(
    normalized: str, project_root: "str | os.PathLike[str]", pathmod: Any
) -> Optional[str]:
    """Realpath/link checks of *normalized* below *project_root*.

    Documented limits (no code fix): a link *inside* the project root that
    points at another in-root location such as ``.git`` is accepted, because
    the resolved target still lies within the root and this check does not
    re-apply the protected-prefix list to the resolved target.
    """
    root = pathmod.abspath(os.fspath(project_root))
    root_real = pathmod.realpath(root)
    key = pathmod.normcase

    def inside(candidate: str) -> bool:
        try:
            return key(pathmod.commonpath([root_real, candidate])) == key(root_real)
        except ValueError:  # e.g. different drives
            return False

    parts = normalized.split("/")
    current = root
    for index, part in enumerate(parts):
        current = pathmod.join(current, part)
        if not _is_link_or_junction(current, pathmod):
            continue
        if index == len(parts) - 1:
            return "must not be a symlink, junction or reparse point"
        if not inside(pathmod.realpath(current)):
            return "must not escape the project root (link in path)"

    target_real = pathmod.realpath(pathmod.join(root, *parts))
    if key(target_real) == key(root_real):
        return "must not resolve to the project root"
    if not inside(target_real):
        return "must not escape the project root"
    return None


def _resolve_sink_dir(
    project_root: "str | os.PathLike[str]",
    effective: ResolvedRepoContainment,
    *,
    pathmod: Any = os.path,
) -> Optional[Path]:
    """Resolve (and defensively re-validate) the sink directory, else None.

    Shared by :func:`ensure_tmp_sink`, :func:`cleanup_tmp_sink` and
    :func:`ensure_tmp_sink_gitignore`. Returns ``None`` when the sink is
    disabled, when the path breaks any :func:`tmp_sink_path_error` rule
    (lexical, link/junction on the way, realpath escape) and otherwise the
    **realpath-resolved** directory, so callers never act on a path that can be
    swapped for a link afterwards (spec §5.4, IC-15 Nr. 27 b/d).
    """
    if not isinstance(effective, ResolvedRepoContainment):
        return None
    if not effective.tmp_sink_enabled:
        return None
    if tmp_sink_path_error(effective.tmp_sink_path, project_root, pathmod=pathmod):
        return None
    root = pathmod.abspath(os.fspath(project_root))
    parts = canonical_tmp_sink_path(effective.tmp_sink_path).split("/")
    return Path(pathmod.realpath(pathmod.join(root, *parts)))


def tmp_sink_path_error(
    path: Any,
    project_root: "str | os.PathLike[str] | None" = None,
    *,
    pathmod: Any = os.path,
) -> Optional[str]:
    """Return an error string when *path* is not a safe scratch path, else None.

    Rules (spec §4.3, IC-34, IC-15 Nr. 27): non-empty string, relative (no
    ``/x``, backslash-leading, UNC, ``\\\\?\\``, drive letters), no ``..``
    segment, no reserved Windows device names, trailing dot/space, ``:``,
    ``<>"|?*`` or control characters, no protected directory (``.git``,
    ``.claude``, ``.meta-config``, provider directories; case-insensitive).
    When *project_root* is given the path is additionally resolved with
    ``pathmod.realpath``: no link/junction/reparse point on the way that
    escapes the root, no link as last component, no escape, not the root.
    ``pathmod`` (default ``os.path``) lets tests simulate ``ntpath``.
    """
    if not isinstance(path, str):
        return f"expected a string, got {type(path).__name__}"
    if not path.strip():
        return "must not be empty"
    error = _lexical_error(path)
    if error:
        return error
    if project_root is not None:
        return _resolution_error(canonical_tmp_sink_path(path), project_root, pathmod)
    return None


def tmp_sink_location_error(path: str, project_root: Path) -> Optional[str]:
    """Return an error when the sink resolves outside the repo or in system temp.

    Only place that consults :func:`tempfile.gettempdir` in the sink context.
    A sink under the system temp dir is reported only when the project root
    itself is *not* under it (otherwise every temp-based checkout would fail).
    """
    root_real = os.path.realpath(os.fspath(project_root))
    target_real = os.path.realpath(os.path.join(root_real, path))

    def under(base: str, candidate: str) -> bool:
        try:
            return os.path.commonpath([base, candidate]) == base
        except ValueError:
            return False

    temp_real = os.path.realpath(tempfile.gettempdir())
    if under(temp_real, target_real) and not under(temp_real, root_real):
        return "resolves into the system temp directory"
    if not under(root_real, target_real):
        return "resolves outside the project root"
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


class TmpSinkError(Exception):
    """Output-path resolution failure carrying a stable error code (IC-34).

    ``code`` is ``tmp-sink.disabled``, ``tmp-sink.invalid-path``,
    ``tmp-sink.invalid-segment`` or ``out-outside-tmp-sink``; when a *tool* is
    given every code is prefixed ``<tool>.<code>``. Callers map it to Exit 2.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _sink_error_code(code: str, tool: str) -> str:
    return f"{tool}.{code}" if tool else code


def _active_sink_dir(project_root: Path, config: Optional[dict], tool: str) -> Path:
    """Return the realpath-resolved sink dir or raise :class:`TmpSinkError`."""
    effective = resolve_effective_repo_containment(config)
    if not effective.tmp_sink_enabled:
        raise TmpSinkError(
            _sink_error_code("tmp-sink.disabled", tool),
            "tmp-sink is disabled; no output location available "
            "(opt in with repo_containment.tmp-sink.enabled: true)",
        )
    bad = [f for f in effective.findings if f.code == "repo-containment.tmp-sink-path"]
    if bad:  # resolver fell back to the default; never silently redirect output
        raise TmpSinkError(
            _sink_error_code("tmp-sink.invalid-path", tool), bad[0].message
        )
    error = tmp_sink_path_error(effective.tmp_sink_path, project_root)
    sink = _resolve_sink_dir(project_root, effective) if error is None else None
    if sink is None:
        raise TmpSinkError(
            _sink_error_code("tmp-sink.invalid-path", tool),
            f"repo_containment.tmp-sink.path {effective.tmp_sink_path!r}: "
            f"{error or 'not resolvable'}",
        )
    return sink


def _checked_segment(value: str, what: str, tool: str = "") -> str:
    """Validate a relative sub-path (*subdir*) or single segment (*run_id*)."""
    error = tmp_sink_path_error(value)
    if error is None and what == "run_id" and ("/" in value or "\\" in value):
        error = "must be a single path segment"
    if error is not None:
        raise TmpSinkError(
            _sink_error_code("tmp-sink.invalid-segment", tool),
            f"{what} {value!r}: {error}",
        )
    return canonical_tmp_sink_path(value)


def _ensure_inside_sink(sink: Path, joined: Path, what: str, tool: str) -> None:
    """Reject *joined* if its longest existing prefix resolves outside *sink*.

    Catches a symlink/junction planted inside the sink (a subdir that points
    to a location outside it) before the caller creates or writes anything
    below it. Non-existing tail segments cannot escape yet.
    """
    probe = joined
    while probe != sink and not os.path.lexists(probe) and probe != probe.parent:
        probe = probe.parent
    real = os.path.normcase(os.path.realpath(probe))
    base = os.path.normcase(os.fspath(sink))
    try:
        inside = os.path.commonpath([base, real]) == base
    except ValueError:  # different drives (Windows) or mixed absolute/relative
        inside = False
    if not inside:
        raise TmpSinkError(
            _sink_error_code("tmp-sink.invalid-segment", tool),
            f"{what} resolves outside the tmp-sink {os.fspath(sink)!r} "
            "(symlink or junction escape)",
        )


def resolve_output_dir(
    project_root: Path, config: Optional[dict], subdir: str, *, tool: str = ""
) -> Path:
    """Return ``<tmp-sink>/<subdir>`` (not created) for tool output (IC-34).

    Raises :class:`TmpSinkError` when the sink is disabled or unsafe; there is
    no fallback location (Q35). Never consults the system temp directory.
    """
    sink = _active_sink_dir(Path(project_root), config, tool)
    joined = sink.joinpath(*_checked_segment(subdir, "subdir", tool).split("/"))
    _ensure_inside_sink(sink, joined, "subdir", tool)
    return joined


def resolve_work_dir(
    project_root: Path,
    config: Optional[dict],
    subdir: str,
    run_id: str,
    *,
    tool: str = "",
) -> Path:
    """Return ``<tmp-sink>/<subdir>/<run_id>/work`` (not created), IC-34."""
    base = resolve_output_dir(project_root, config, subdir, tool=tool)
    work = base / _checked_segment(run_id, "run_id", tool) / "work"
    sink = _active_sink_dir(Path(project_root), config, tool)
    _ensure_inside_sink(sink, work, "run_id", tool)
    return work


def resolve_out_path(
    project_root: Path, config: Optional[dict], out: str, *, tool: str = ""
) -> Path:
    """Validate an explicit ``--out`` against the sink via ``realpath`` (IC-34).

    Relative paths are taken relative to *project_root*. Anything resolving
    outside the sink (``..``, symlinks, absolute paths) raises
    ``<tool>.out-outside-tmp-sink``.

    Caveats: the check is a point-in-time ``realpath`` test (TOCTOU) -- a
    symlink swapped in afterwards defeats it, so callers should open the file
    with ``O_NOFOLLOW``/``O_EXCL`` or re-check immediately before writing.
    Comparison uses ``os.path.normcase``, which only folds case on Windows;
    on case-insensitive filesystems elsewhere (macOS default) differently
    cased spellings of the sink are not folded. Windows junction/drive cases
    are only simulated in tests (UNVERIFIED).
    """
    sink = _active_sink_dir(Path(project_root), config, tool)
    root = os.path.abspath(os.fspath(project_root))
    target = os.path.realpath(os.path.join(root, os.fspath(out)))
    base = os.path.normcase(os.fspath(sink))
    try:
        inside = os.path.commonpath([base, os.path.normcase(target)]) == base
    except ValueError:
        inside = False
    if not inside or os.path.normcase(target) == base:
        raise TmpSinkError(
            _sink_error_code("out-outside-tmp-sink", tool),
            f"--out {os.fspath(out)!r} must lie inside the tmp-sink {os.fspath(sink)!r}",
        )
    return Path(target)


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

    The re-validation after ``makedirs`` is *detecting only*: the directory
    has already been created at that point and nothing is removed or rolled
    back; the caller merely receives ``None`` instead of the path.
    """
    sink_dir = _resolve_sink_dir(project_root, effective)
    if sink_dir is None:
        return None
    if _TOCTOU_TEST_HOOK is not None:
        _TOCTOU_TEST_HOOK()
    # Re-validate right before creating: the path may have turned into a link.
    if _resolve_sink_dir(project_root, effective) != sink_dir:
        return None
    if not dry_run:
        os.makedirs(sink_dir, exist_ok=True)
        # ... and once more afterwards (a swap during makedirs).
        if _resolve_sink_dir(project_root, effective) != sink_dir:
            return None
    return sink_dir


def work_dir_env(work_dir: Path, base: Optional[dict] = None) -> dict:
    """Return an environment whose temp-dir variables point at *work_dir*.

    Subprocesses started with it create temporary files below the tmp-sink
    work directory instead of the system temp directory (IC-34).
    """
    env = dict(os.environ if base is None else base)
    for key in ("TMPDIR", "TEMP", "TMP"):
        env[key] = str(work_dir)
    return env


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
