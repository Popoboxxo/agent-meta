#!/usr/bin/env python3
"""Path-containment verdict for the deployed repo-containment shell hook.

Issue #1238b1: importable replacement for the inline Python verdict.  Issue
#1275a adds protected submodule paths.  Any error produces no ALLOW verdict,
so the shell caller blocks (fail closed).  This is a convention boundary, not
a security boundary.
"""
import os
import posixpath
import re
import shlex
import sys


_DEFAULT_PROTECTED_PATHS = ("external", ".agent-meta")
_GITMODULES_PATH_RE = re.compile(r"^\s*path\s*=\s*(.*?)\s*$", re.IGNORECASE)
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")


def within(base, target):
    """Return whether *target* is *base* or one of its descendants."""
    try:
        normalized_base = os.path.normcase(base)
        return os.path.commonpath(
            [normalized_base, os.path.normcase(target)]
        ) == normalized_base
    except ValueError:
        return False


def gitmodules_paths(root):
    """Read every ``path =`` value from an existing root ``.gitmodules``.

    Git-config quoting and comments are decoded with the stdlib lexer.  Missing,
    unreadable or malformed values contribute no extra paths; the defaults
    remain active.  Unsafe paths are filtered by :func:`protected_roots`.
    """
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
        if len(values) == 1 and values[0].strip():
            paths.append(values[0].strip())
    return paths


def protected_roots(root):
    """Resolve defaults plus valid root-relative ``.gitmodules`` paths."""
    roots = []
    for raw in (*_DEFAULT_PROTECTED_PATHS, *gitmodules_paths(root)):
        canonical = raw.replace("\\", "/")
        if not canonical or _WINDOWS_DRIVE_RE.match(canonical):
            continue
        normalized = posixpath.normpath(canonical)
        if normalized in (".", "..") or normalized.startswith(("../", "/")):
            continue
        candidate = os.path.realpath(os.path.join(root, normalized))
        if candidate == root or not within(root, candidate):
            continue
        if candidate not in roots:
            roots.append(candidate)
    return roots


def path_verdict(root, workdir, sink_enabled, sink_path, raw):
    """Return ALLOW, BLOCK_SINK, BLOCK_PROTECTED or BLOCK for one target."""
    if not raw:
        return "BLOCK"

    target = os.path.realpath(raw if os.path.isabs(raw) else os.path.join(workdir, raw))
    sink_root = os.path.realpath(os.path.join(root, sink_path))

    # The override deliberately bypasses only this protected-path gate.  Root
    # containment and the tmp-sink rule below remain unchanged.
    if os.environ.get("AM_ALLOW_PROTECTED_WRITE") != "1":
        for protected_root in protected_roots(root):
            if within(protected_root, target):
                return "BLOCK_PROTECTED"

    if within(sink_root, target):
        return "ALLOW" if sink_enabled else "BLOCK_SINK"

    if within(root, target):
        return "ALLOW"

    return "BLOCK"


def main(argv: list[str], stdin: str) -> int:
    """Print ALLOW, BLOCK_SINK, BLOCK_PROTECTED or BLOCK for one write target."""
    del stdin
    if len(argv) != 5:
        return 1
    root = os.path.realpath(argv[0])
    workdir = os.path.realpath(argv[1])
    sink_enabled = argv[2] == "1"
    sink_path = argv[3]
    raw = argv[4]

    try:
        verdict = path_verdict(root, workdir, sink_enabled, sink_path, raw)
    except Exception:
        return 1
    print(verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], ""))
