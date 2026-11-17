"""Consistency checks for the artifact-locations matrix (Issue #1186, T14).

Normative source: Spec §4.6 and Plan T14. Five checks with a fixed severity
mapping::

    artifact-locations.literal-path             ERROR
    artifact-locations.legacy-write             WARNING
    artifact-locations.inline-with-path-promise  ERROR
    artifact-locations.missing-dir              INFO
    artifact-locations.alias-divergence         WARNING

Design constraints (Spec §4.6 / RVW2-1186-02 / RVW-1186-01):

* ``legacy-write`` is **baseline-based**, never mtime-based. The baseline is
  the ``baseline.legacy_files`` inventory in
  ``.meta-config/artifact-locations.resolved.json`` (written by T15 / Stage
  14c). A missing/corrupt baseline fails open: no findings, one stderr notice.
* ``unmanaged[]`` targets (D-8) and directory markers (``MARKER_FILENAMES``
  from T8) trigger none of the five checks.
* The read-ok marker ``<!-- artifact-read-ok -->`` exempts a scan/read line
  from ``literal-path``; the marker set is a shrinking ratchet that starts at
  exactly two lines (``knowledge-migrator.md:39,50``).
* Disjoint from ``temp-literal.system-temp`` (system temp paths) and
  ``context.dangling-pointer`` (doc links): this module only inspects managed
  project artifact paths.
* ``enabled: false`` silences all five checks. Read-only: never raises, never
  writes to disk, no provider branching.

No second resolver: active class paths, ``legacy[]``, ``unmanaged[]`` and the
master switch all come from :func:`lib.artifact_locations.resolve_artifact_locations`.
"""
from __future__ import annotations

import fnmatch
import json
import re
import sys
from pathlib import Path
from typing import Iterable, Optional

from ..artifact_locations import CLASS_REGISTRY, resolve_artifact_locations
from ..artifact_scaffold import MARKER_FILENAMES
from .report import Finding, Severity

#: Public check IDs (the five from Spec §4.6).
CHECK_LITERAL_PATH = "artifact-locations.literal-path"
CHECK_LEGACY_WRITE = "artifact-locations.legacy-write"
CHECK_INLINE_PROMISE = "artifact-locations.inline-with-path-promise"
CHECK_MISSING_DIR = "artifact-locations.missing-dir"
CHECK_ALIAS_DIVERGENCE = "artifact-locations.alias-divergence"

#: Relative path of the resolved data file that carries the baseline inventory.
_RESOLVED_RELPATH = Path(".meta-config") / "artifact-locations.resolved.json"

#: Marker that declares a literal as an intentional read/scan position.
_READ_OK_MARKER = "<!-- artifact-read-ok -->"
_READ_OK_RATCHET = 2

#: Strong write cues. An *adjacent* cue (see `_CUE_WINDOW`) turns a literal into
#: a write position. The window keeps prose like "create you ... (see
#: `docs/concepts/...`)" from being misread as an output instruction.
_WRITE_CUES = (
    "**output file:**",
    "output file:",
    "persisted to:",
    "artifacts:",
    "output:",
    "write to",
    "write:",
    "schreibe",
    "schreib ",
    "speichere",
    "erstelle",
    "zielpfad:",
    "ziel:",
    "erstell ",
)
_CUE_WINDOW = 80
_ARROW_CUE = "→"

#: Roles live under ``agents/``; underscore files (notably
#: ``_reference-agent.md``) are included-by-reference escapes and are exempt.
_AGENTS_DIR = "agents"
_SKIP_DIRS = frozenset(
    {".git", "__pycache__", ".venv", "node_modules", ".tmp", ".pytest_cache"}
)

#: The managed class-path literals the framework historically hard-coded
#: (Spec §4.6). They are scanned in addition to the active paths from the
#: resolved matrix so a custom ``path`` is caught as well.
_FRAMEWORK_PATH_LITERALS = (
    "docs/specs", "docs/plans", "docs/spikes", "docs/concepts",
    "docs/reviews", "docs/audits", "docs/analysis", "docs/reports",
    "docs/adr", "docs/traceability", "docs/runbooks",
)
_FILENAME_LITERAL_RES = (
    r"\bplan-[A-Za-z0-9_.-]+\.md\b",
    r"\bconcept-[A-Za-z0-9_.-]+\.md\b",
)

#: Promises that a path will be persisted (inline-with-path-promise).
_PATH_PROMISES = ("**output file:**", "persisted to:", "artifacts:")


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------
def _read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _iter_files(root: Path, *, suffix: str | None = None) -> Iterable[Path]:
    """Yield files below *root*, skipping VCS/cache/sink directories."""
    if not root.is_dir():
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        # Check *relative* parts: a test fixture root may itself live under a
        # directory named like a skip dir (e.g. `.tmp/pytest-…`).
        if any(part in _SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if suffix is not None and path.suffix.lower() != suffix:
            continue
        yield path


def _load_baseline(project_root: Path) -> Optional[set[str]]:
    """Return the baseline inventory, or ``None`` when it is unavailable."""
    path = Path(project_root) / _RESOLVED_RELPATH
    text = _read_text(path)
    if text is None:
        return None
    try:
        payload = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None
    baseline = payload.get("baseline")
    if not isinstance(baseline, dict):
        return None
    files = baseline.get("legacy_files")
    if not isinstance(files, list):
        return None
    return {entry for entry in files if isinstance(entry, str)}


def _notice_baseline_missing() -> None:
    """One fail-open notice on stderr — never a new finding/check code.

    Spec §4.6/§6.3.4 mandates a single stderr line when the baseline is
    unavailable. This is the deliberate exception to the "no direct print in
    lib/" convention: a Finding would violate "0 findings / no new check
    code", and SyncLog writes the report's stdout, not the fail-open channel.
    """
    print(  # noqa: T201 - spec-mandated stderr notice, see docstring
        "  !  artifact-locations.legacy-write skipped: baseline unavailable "
        "(run sync.py to write .meta-config/artifact-locations.resolved.json)",
        file=sys.stderr,
    )


def _pattern_matches(relpath: str, pattern: str) -> bool:
    """Match a project-relative path against a legacy[]/unmanaged[] pattern.

    Supports the three shapes used by the presets: recursive ``dir/**``,
    directory prefixes (``docs/conclusions/`` or a wildcard-free directory),
    and fnmatch file patterns (``docs/plans/audit-*.md``, ADR forms).
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


def _active_path_literals(matrix) -> tuple[str, ...]:
    """Class paths that count as managed literals (framework defaults + live)."""
    paths: set[str] = set(_FRAMEWORK_PATH_LITERALS)
    for name, resolved in matrix.classes.items():
        path = getattr(resolved, "path", "")
        if (
            getattr(resolved, "mode", "") == "files"
            and isinstance(path, str)
            and "/" in path  # SE cell roots ("SE") are not literal dir targets
            and not path.startswith((".", "/"))
        ):
            paths.add(path)
    return tuple(sorted(paths))


def _literal_regex(paths: tuple[str, ...]):
    alternatives = [re.escape(path) + r"(?![A-Za-z0-9_.-])" for path in paths]
    alternatives.extend(_FILENAME_LITERAL_RES)
    return re.compile("|".join(alternatives))


# ---------------------------------------------------------------------------
# literal-path (ERROR)
# ---------------------------------------------------------------------------
def _has_write_cue(prefix: str) -> bool:
    tail = prefix[-_CUE_WINDOW:].lower()
    return any(cue in tail for cue in _WRITE_CUES) or _ARROW_CUE in tail


def _is_write_position(line: str, match_start: int, in_file_table: bool) -> bool:
    if in_file_table and line.lstrip().startswith("|"):
        return True
    return _has_write_cue(line[:match_start])


def _literal_path_findings(
    agent_meta_root: Path, matrix, unmanaged: tuple[str, ...]
) -> list[Finding]:
    agents_dir = Path(agent_meta_root) / _AGENTS_DIR
    paths = _active_path_literals(matrix)
    literal_re = _literal_regex(paths)
    findings: list[Finding] = []
    marker_lines = 0

    for path in _iter_files(agents_dir, suffix=".md"):
        if path.name.startswith("_"):
            continue  # _reference-agent.md and other include-only escapes
        relpath = _relpath(path, Path(agent_meta_root))
        if _matches_any(relpath, unmanaged):
            continue
        content = _read_text(path)
        if content is None:
            continue
        in_file_table = False
        for lineno, line in enumerate(content.splitlines(), start=1):
            lowered = line.lower()
            if line.lstrip().startswith("#"):
                in_file_table = any(
                    token in lowered for token in ("file", "ziel", "output")
                )
            if _READ_OK_MARKER in line:
                marker_lines += 1
                continue  # intentional read/scan position
            for match in literal_re.finditer(line):
                if _is_write_position(line, match.start(), in_file_table):
                    findings.append(Finding(
                        Severity.ERROR,
                        CHECK_LITERAL_PATH,
                        relpath,
                        f"managed class-path literal '{match.group(0)}' in write "
                        f"position on line {lineno}; use {{{{ARTIFACT_*_DIR}}}}",
                        "Replace the literal with the generated "
                        "{{ARTIFACT_*_DIR}} variable, or mark an intentional "
                        "read/scan line with <!-- artifact-read-ok -->.",
                    ))
                    break  # one finding per line

    # Shrinking ratchet: at most two read-ok markers across the framework.
    excess = marker_lines - _READ_OK_RATCHET
    if excess > 0:
        findings.append(Finding(
            Severity.ERROR,
            CHECK_LITERAL_PATH,
            f"{_AGENTS_DIR}/",
            f"read-ok marker ratchet exceeded: {marker_lines} marked line(s), "
            f"maximum {_READ_OK_RATCHET}",
            "Convert surplus read literals to {{ARTIFACT_*_DIR}} variables; "
            "the marker set may only shrink.",
        ))
    return findings


# ---------------------------------------------------------------------------
# inline-with-path-promise (ERROR)
# ---------------------------------------------------------------------------
def _inline_promise_findings(
    agent_meta_root: Path, matrix, unmanaged: tuple[str, ...]
) -> list[Finding]:
    agents_dir = Path(agent_meta_root) / _AGENTS_DIR
    inline_paths = {
        name: getattr(resolved, "path", "")
        for name, resolved in matrix.classes.items()
        if getattr(resolved, "mode", "") in {"inline", "off"}
        and getattr(resolved, "path", "")
    }
    if not inline_paths:
        return []

    findings: list[Finding] = []
    for path in _iter_files(agents_dir, suffix=".md"):
        if path.name.startswith("_"):
            continue
        relpath = _relpath(path, Path(agent_meta_root))
        if _matches_any(relpath, unmanaged):
            continue
        content = _read_text(path)
        if content is None:
            continue
        for lineno, line in enumerate(content.splitlines(), start=1):
            lowered = line.lower()
            if not any(promise in lowered for promise in _PATH_PROMISES):
                continue
            for name, class_path in inline_paths.items():
                if class_path not in line:
                    continue  # the promise must name this class's output path
                findings.append(Finding(
                    Severity.ERROR,
                    CHECK_INLINE_PROMISE,
                    relpath,
                    f"class '{name}' has mode inline/off but line {lineno} "
                    f"promises an output file at '{class_path}'",
                    "Remove the path promise for inline/off classes or switch "
                    "the class back to mode: files.",
                ))
    return findings


# ---------------------------------------------------------------------------
# missing-dir (INFO)
# ---------------------------------------------------------------------------
def _missing_dir_findings(project_root: Path, matrix, unmanaged: tuple[str, ...]) -> list[Finding]:
    findings: list[Finding] = []
    for name, spec in CLASS_REGISTRY.items():
        if spec.form != "directory":
            continue  # SE cells, ephemeral/state and file-sets have no own dir
        resolved = matrix.classes.get(name)
        if resolved is None or resolved.mode != "files" or not resolved.path:
            continue
        if _matches_any(resolved.path, unmanaged):
            continue
        if (Path(project_root) / resolved.path).is_dir():
            continue
        findings.append(Finding(
            Severity.INFO,
            CHECK_MISSING_DIR,
            ".meta-config/project.yaml",
            f"class '{name}' has mode: files but directory '{resolved.path}' "
            "does not exist in the project",
            "Run sync.py to scaffold the artifact directories.",
        ))
    return findings


# ---------------------------------------------------------------------------
# legacy-write (WARNING, baseline-based)
# ---------------------------------------------------------------------------
def _legacy_write_findings(
    project_root: Path, matrix, baseline: set[str]
) -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_files(Path(project_root)):
        if path.name in MARKER_FILENAMES:
            continue  # scaffold marker, never artifact content
        relpath = _relpath(path, Path(project_root))
        if _matches_any(relpath, matrix.unmanaged):
            continue
        if relpath in baseline or not _matches_any(relpath, matrix.legacy):
            continue
        findings.append(Finding(
            Severity.WARNING,
            CHECK_LEGACY_WRITE,
            relpath,
            f"artifact content in legacy[] target '{relpath}' is not in the "
            "sync baseline (new write)",
            "Move the artifact into its managed class path or re-run sync.py "
            "to refresh the baseline — nothing was deleted automatically.",
        ))
    return findings


# ---------------------------------------------------------------------------
# alias-divergence (WARNING)
# ---------------------------------------------------------------------------
def _alias_divergence_findings(config: dict) -> list[Finding]:
    section = config.get("artifact-locations") or {}
    classes = section.get("classes") or {} if isinstance(section, dict) else {}
    state = classes.get("state") or {} if isinstance(classes, dict) else {}
    subdirs = state.get("subdirs") or {} if isinstance(state, dict) else {}
    progress = config.get("progress") or {}
    viz = config.get("viz") or {}

    pairs = (
        ("progress.dir", progress.get("dir"), subdirs.get("progress")),
        ("progress.checkpoint-dir", progress.get("checkpoint-dir"),
         subdirs.get("checkpoints")),
        ("progress.handoffs-dir", progress.get("handoffs-dir"),
         subdirs.get("handoffs")),
        ("viz.event_log", viz.get("event_log"),
         state.get("event-log", state.get("event_log"))),
    )
    findings: list[Finding] = []
    for alias_key, alias_value, declared in pairs:
        if (
            isinstance(alias_value, str) and isinstance(declared, str)
            and alias_value and declared and alias_value != declared
        ):
            findings.append(Finding(
                Severity.WARNING,
                CHECK_ALIAS_DIVERGENCE,
                ".meta-config/project.yaml",
                f"alias '{alias_key}' diverges from state: "
                f"'{alias_value}' != '{declared}'",
                "Keep one source per state path; the project alias should "
                "match artifact-locations.classes.state (D1).",
            ))
    return findings


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def check_artifact_locations(
    agent_meta_root: Path,
    project_root: Path,
    config: Optional[dict],
) -> list[Finding]:
    """Return every ``artifact-locations.*`` finding (Spec §4.6, T14).

    *agent_meta_root* is the framework checkout (role templates live there);
    *project_root* is the synced project (baseline + class directories). The
    master ``enabled`` switch and all paths come from the single resolver;
    config-level hard errors are left to ``sync.py --validate`` and make this
    read-only check silent. Never raises.
    """
    try:
        matrix = resolve_artifact_locations(config or {}, agent_meta_root, project_root)
    except Exception:  # noqa: BLE001 - a read-only check must not crash
        return []
    if not matrix.enabled:
        return []

    unmanaged = tuple(matrix.unmanaged)
    findings: list[Finding] = []
    findings.extend(_literal_path_findings(agent_meta_root, matrix, unmanaged))
    findings.extend(_inline_promise_findings(agent_meta_root, matrix, unmanaged))
    findings.extend(_missing_dir_findings(project_root, matrix, unmanaged))
    findings.extend(_alias_divergence_findings(config or {}))

    baseline = _load_baseline(project_root)
    if baseline is None:
        _notice_baseline_missing()
    else:
        findings.extend(_legacy_write_findings(project_root, matrix, baseline))
    return findings


__all__ = [
    "CHECK_ALIAS_DIVERGENCE",
    "CHECK_INLINE_PROMISE",
    "CHECK_LEGACY_WRITE",
    "CHECK_LITERAL_PATH",
    "CHECK_MISSING_DIR",
    "check_artifact_locations",
]
