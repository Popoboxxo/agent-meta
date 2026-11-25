#!/usr/bin/env python3
"""Effective repo-containment config reader for the deployed shell hook.

Issue #1238b1: importable, fail-closed replacement for the inline Python
reader.  PyYAML remains the documented optional runtime exception; without it
the guard stays enabled and never honours an opt-out.
"""
import json
import os
import posixpath
import re
import sys


# Mirrors scripts/lib/repo_containment.py::tmp_sink_path_error (lexical rules).
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")
_RESERVED = frozenset(
    ["CON", "PRN", "AUX", "NUL"]
    + ["COM%d" % i for i in range(1, 10)]
    + ["LPT%d" % i for i in range(1, 10)]
)
_FORBIDDEN_CHARS = frozenset('<>"|?*')
# Lower-cased protected segment prefixes (framework dirs + provider_root_dirs).
_PROTECTED = (
    (".git",), (".claude",), (".meta-config",), (".agents",), (".codex",),
    (".continue",), (".gemini",), (".github", "copilot"), (".kimi-code",),
    (".mammouth",), (".opencode",), (".zcode",),
)


def canonical_path(path):
    """Backslash -> slash BEFORE normpath, always POSIX-style."""
    return posixpath.normpath(path.replace("\\", "/"))


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


def emit(enabled, sink_enabled, sink_path, rejected=False):
    # SINK_REJECTED is observed only by tests/test_tmp_sink_path_parity.py
    # (AC-97); the shell consumer deliberately ignores it (silent fallback).
    print("ENABLED=%d" % (1 if enabled else 0))
    print("SINK_ENABLED=%d" % (1 if sink_enabled else 0))
    print("SINK_PATH=%s" % sink_path)
    print("SINK_REJECTED=%d" % (1 if rejected else 0))


def main(argv: list[str], stdin: str) -> int:
    """Print ENABLED/SINK_ENABLED/SINK_PATH/SINK_REJECTED/SCRATCH_PATH."""
    del stdin
    if len(argv) != 2:
        return 1
    config_file, provider = argv

    try:
        import yaml

        with open(config_file, encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}

        raw = config.get("repo_containment")  # runtime-reader:repo_containment
        rc = raw if isinstance(raw, dict) else {}

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

        emit(enabled, sink_enabled, path, rejected)
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
        emit(True, True, ".tmp")
        # Fail-closed: an unreadable config must not let the env/matrix widen the jail.
        print("SCRATCH_PATH=.tmp")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], ""))
