#!/usr/bin/env python3
"""Effective repo-containment config reader for the deployed shell hook.

Issue #1238b1: importable, fail-closed replacement for the inline Python
reader.  PyYAML remains the documented optional runtime exception; without it
the guard stays enabled and never honours an opt-out. Issue #1275b adds the
structured effective protected-path list used by the deployed shell hook.
"""
import json
import os
import posixpath
import re
import shlex
import sys


# Mirrors scripts/lib/repo_containment.py::tmp_sink_path_error (lexical rules).
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")
_RESERVED = frozenset(
    ["CON", "PRN", "AUX", "NUL"]
    + ["COM%d" % i for i in range(1, 10)]
    + ["LPT%d" % i for i in range(1, 10)]
)
_FORBIDDEN_CHARS = frozenset('<>"|?*')
_DEFAULT_PROTECTED_PATHS = ("external/", ".agent-meta/")
_GITMODULES_PATH_RE = re.compile(r"^\s*path\s*=\s*(.*?)\s*$", re.IGNORECASE)
# Lower-cased protected segment prefixes (framework dirs + provider_root_dirs).
_PROTECTED = (
    (".git",), (".claude",), (".meta-config",), (".agents",), (".codex",),
    (".continue",), (".gemini",), (".github", "copilot"), (".kimi-code",),
    (".mammouth",), (".opencode",), (".zcode",),
)


def canonical_path(path):
    """Backslash -> slash BEFORE normpath, always POSIX-style."""
    return posixpath.normpath(path.replace("\\", "/"))


def normalize_protected_path(path):
    """Mirror scripts/lib/repo_containment.py::normalize_protected_path."""
    if not isinstance(path, str) or not path:
        return None
    if any(ord(ch) < 32 for ch in path):
        return None
    canonical = path.replace("\\", "/")
    if canonical.startswith("/") or _WINDOWS_DRIVE_RE.match(canonical):
        return None
    if ".." in canonical.split("/"):
        return None
    normalized = posixpath.normpath(canonical)
    if normalized in ("", ".", "..") or normalized.startswith("../"):
        return None
    return normalized


def _dedupe_protected_paths(paths):
    seen = set()
    result = []
    for path in paths:
        key = path.casefold()
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def _gitmodules_paths(root):
    try:
        with open(os.path.join(root, ".gitmodules"), encoding="utf-8") as handle:
            lines = handle.readlines()
    except (OSError, UnicodeError):
        return []
    paths = []
    for line in lines:
        match = _GITMODULES_PATH_RE.match(line)
        if match is None:
            continue
        lexer = shlex.shlex(match.group(1), posix=True)
        lexer.whitespace = "\t\r\n"
        lexer.whitespace_split = True
        lexer.commenters = "#;"
        try:
            values = list(lexer)
        except ValueError:
            continue
        if len(values) != 1:
            continue
        normalized = normalize_protected_path(values[0])
        if normalized is not None:
            paths.append(normalized)
    return _dedupe_protected_paths(paths)


def effective_protected_paths(config_file, config):
    """Resolve the same protected-path merge contract as the syncer.

    A present list replaces the defaults; existing ``.gitmodules`` paths are
    appended. Invalid configuration fails safe to defaults + ``.gitmodules``
    and is reported on stderr rather than silently widening the allow-list.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(config_file)))
    raw = config.get("repo_containment") if isinstance(config, dict) else None
    rc = raw if isinstance(raw, dict) else {}
    configured = rc.get("protected_paths", _UNSET)
    if configured is _UNSET:
        base = list(_DEFAULT_PROTECTED_PATHS)
    elif not isinstance(configured, list):
        print(
            "REPO_CONTAINMENT: warning: repo_containment.protected_paths must be "
            "a list of strings; using defaults (fail-closed).",
            file=sys.stderr,
        )
        base = list(_DEFAULT_PROTECTED_PATHS)
    else:
        normalized = [normalize_protected_path(value) for value in configured]
        if any(value is None for value in normalized):
            print(
                "REPO_CONTAINMENT: warning: repo_containment.protected_paths "
                "contains an invalid path; using defaults (fail-closed).",
                file=sys.stderr,
            )
            base = list(_DEFAULT_PROTECTED_PATHS)
        else:
            base = normalized
    paths = [normalize_protected_path(value) for value in base]
    paths = [value for value in paths if value is not None]
    paths.extend(_gitmodules_paths(root))
    return _dedupe_protected_paths(paths)


_UNSET = object()


def path_error(path):
    """Return an error string for an unsafe sink path, else None."""
    if not isinstance(path, str) or not path.strip():
        return "empty or not a string"
    if _WINDOWS_DRIVE_RE.match(path):
        return "drive-letter path"
    if path[:1] in ("/", "\\"):
        return "absolute or UNC path"
    if any(ord(ch) < 32 for ch in path):
        return "control character"
    if path in (".", ".."):
        return "root or parent"
    segments = path.replace("\\", "/").split("/")
    if any(segment == ".." for segment in segments):
        return "'..' segment"
    for segment in segments:
        if segment in ("", "."):
            continue
        if ":" in segment:
            return "':' in segment"
        if any(ch in _FORBIDDEN_CHARS for ch in segment):
            return "forbidden character"
        if segment[-1] in (".", " "):
            return "trailing dot or space"
        if segment.split(".", 1)[0].rstrip(" ").upper() in _RESERVED:
            return "reserved Windows name"
    normalized = canonical_path(path)
    if normalized in ("", ".", "..") or normalized.startswith("../"):
        return "escapes the root"
    lowered = tuple(seg.lower() for seg in normalized.split("/"))
    for prefix in _PROTECTED:
        if lowered[: len(prefix)] == prefix:
            return "protected directory"
    return None


def resolved_scratch_path(project_path, config_file):
    """Resolve the single scratch source without widening the jail.

    Precedence: ARTIFACT_SCRATCH_DIR env -> classes[scratch].path in the
    resolved matrix data file -> repo_containment.tmp-sink.path -> '.tmp'.
    Every candidate is checked with the SAME unchanged path_error() above; an
    unsafe value is ignored with a warning and the next source is tried. A
    missing or broken data file falls back to the legacy key (fail closed) --
    it never opens the prison. project_path is already validated/canonical.
    """
    sources = []
    env_path = os.environ.get("ARTIFACT_SCRATCH_DIR")
    if env_path:
        sources.append(("environment ARTIFACT_SCRATCH_DIR", env_path))

    data_file = os.path.join(
        os.path.dirname(config_file), "artifact-locations.resolved.json"
    )
    if os.path.isfile(data_file):
        try:
            with open(data_file, encoding="utf-8") as handle:
                data = json.load(handle)
            # T15 emits classes as a name-keyed mapping; the path-guard
            # contract also documents a name-tagged list. Accept both.
            classes = data.get("classes") if isinstance(data, dict) else None
            scratch = classes.get("scratch") if isinstance(classes, dict) else None
            if scratch is None and isinstance(classes, list):
                scratch = next(
                    (c for c in classes
                     if isinstance(c, dict) and c.get("name") == "scratch"),
                    None,
                )
            data_path = scratch.get("path") if isinstance(scratch, dict) else None
            if isinstance(data_path, str) and data_path.strip():
                sources.append(("artifact-locations.classes.scratch.path", data_path))
            else:
                print(
                    "REPO_CONTAINMENT: warning: " + data_file
                    + " has no artifact-locations.classes.scratch.path; falling back"
                    + " to repo_containment.tmp-sink.path (fail-closed).",
                    file=sys.stderr,
                )
        except Exception as exc:
            print(
                "REPO_CONTAINMENT: warning: could not read " + data_file
                + " (" + type(exc).__name__ + "); falling back to"
                + " repo_containment.tmp-sink.path (fail-closed).",
                file=sys.stderr,
            )
    else:
        print(
            "REPO_CONTAINMENT: warning: " + data_file
            + " not found; falling back to repo_containment.tmp-sink.path"
            + " for the scratch sink (fail-closed).",
            file=sys.stderr,
        )

    sources.append(("repo_containment.tmp-sink.path", project_path))
    for label, candidate in sources:
        if path_error(candidate) is None:
            return canonical_path(candidate)
        print(
            "REPO_CONTAINMENT: warning: unsafe scratch path from " + label
            + " (" + repr(candidate) + "); ignored (fail-closed).",
            file=sys.stderr,
        )
    return ".tmp"


def emit(enabled, sink_enabled, sink_path, rejected=False, protected_paths=None):
    # SINK_REJECTED is observed only by tests/test_tmp_sink_path_parity.py
    # (AC-97); the shell consumer deliberately ignores it (silent fallback).
    print("ENABLED=%d" % (1 if enabled else 0))
    print("SINK_ENABLED=%d" % (1 if sink_enabled else 0))
    print("SINK_PATH=%s" % sink_path)
    print("SINK_REJECTED=%d" % (1 if rejected else 0))
    if protected_paths is not None:
        print("PROTECTED_PATHS_JSON=%s" % json.dumps(
            protected_paths, ensure_ascii=True, separators=(",", ":")
        ))


def main(argv: list[str], stdin: str) -> int:
    """Print containment values and optionally structured protected paths.

    The two-argument form preserves the existing reader contract. The shell
    passes ``--include-protected-paths`` to receive one JSON-encoded line that
    can be forwarded as a single quoted argv value without eval or splitting.
    """
    del stdin
    if len(argv) not in (2, 3):
        return 1
    if len(argv) == 3 and argv[2] != "--include-protected-paths":
        return 1
    config_file, provider = argv[:2]
    include_protected = len(argv) == 3

    try:
        import yaml

        with open(config_file, encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
        if not isinstance(config, dict):
            raise ValueError("config root must be a mapping")

        raw = config.get("repo_containment")  # runtime-reader:repo_containment
        if raw is not None and not isinstance(raw, dict):
            print(
                "REPO_CONTAINMENT: warning: repo_containment must be a mapping; "
                "using framework defaults (fail-closed).",
                file=sys.stderr,
            )
        rc = raw if isinstance(raw, dict) else {}
        protected = (
            effective_protected_paths(config_file, config) if include_protected else None
        )

        # Master switch: provider-override > project value > default True.
        # A present-but-non-boolean value resolves safe-side to True (F4).
        enabled = True
        handled = False
        overrides = rc.get("provider-overrides")
        if isinstance(overrides, dict) and isinstance(provider, str) and provider:
            entry = overrides.get(provider)
            if isinstance(entry, dict) and "enabled" in entry:
                value = entry["enabled"]
                enabled = value if isinstance(value, bool) else True
                handled = True
        if not handled and "enabled" in rc:
            value = rc["enabled"]
            enabled = value if isinstance(value, bool) else True

        # tmp-sink settings (independent of the master switch; framework defaults).
        sink_raw = rc.get("tmp-sink")
        sink = sink_raw if isinstance(sink_raw, dict) else {}
        sink_enabled = sink.get("enabled", True)
        if not isinstance(sink_enabled, bool):
            sink_enabled = True

        path = sink.get("path", ".tmp")
        # Same decision and canonical form as Python; invalid => safe fallback.
        rejected = path_error(path) is not None
        path = ".tmp" if rejected else canonical_path(path)

        emit(enabled, sink_enabled, path, rejected, protected)
        # T24 (D1): SCRATCH_PATH is the effective path after precedence; SINK_PATH
        # above stays the raw project.yaml value so the parity suite keeps its pin.
        print("SCRATCH_PATH=%s" % resolved_scratch_path(path, config_file))
    except Exception as exc:
        # F4 safe-side: missing/unreadable/unparseable config never opens silently.
        # SR-B-20: honouring an opt-out here would need the shared stdlib YAML
        # subset reader; a misparse must never open the jail. The ignored opt-out
        # stays visible on stderr instead of being silently discarded.
        print(
            "REPO_CONTAINMENT: warning: could not read " + config_file
            + " with PyYAML (" + type(exc).__name__ + "); containment stays ENABLED."
            + " A configured repo_containment.enabled: false is NOT honoured in"
            + " this state (fail-closed). Install PyYAML for the hook interpreter"
            + " or run the project sync.",
            file=sys.stderr,
        )
        protected = (
            effective_protected_paths(config_file, None) if include_protected else None
        )
        emit(True, True, ".tmp", protected_paths=protected)
        # Fail-closed: an unreadable config must not let the env/matrix widen the jail.
        print("SCRATCH_PATH=.tmp")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], ""))
