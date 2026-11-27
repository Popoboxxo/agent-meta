#!/usr/bin/env python3
"""Artifact-location routing classifier for the deployed shell hook.

Issue #1238b2: importable replacement for the former inline Python heredoc.
The routing convention remains fail-open on missing or corrupt matrix data.
"""
from __future__ import annotations

import fnmatch
import json
import os
import sys


def main(argv: list[str], stdin: str) -> int:
    """Print ALLOW, WARN, BLOCK or FAIL for one artifact target."""
    del stdin
    if len(argv) != 4:
        return 1
    data_path, file_path, root, markers_raw = argv
    markers = set(markers_raw.split())

    try:
        with open(data_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        print(
            "FAIL:artifact-path-guard: WARN: unreadable data file "
            "(corrupt JSON); allowing (fail-open)"
        )
        return 0

    def matches(relpath, pattern):
        """Mirror lib.artifact_status._pattern_matches (framework preset shapes)."""
        pattern = pattern.replace("\\", "/")
        if not pattern:
            return False
        if pattern.endswith("/**"):
            return relpath.startswith(pattern[:-2])
        if pattern.endswith("/"):
            return relpath.startswith(pattern)
        if "**" in pattern:
            return relpath.startswith(pattern.split("**", 1)[0])
        if any(c in pattern for c in "*?["):
            return fnmatch.fnmatchcase(relpath, pattern)
        return relpath == pattern or relpath.startswith(pattern + "/")


    def matches_any(relpath, patterns):
        return any(matches(relpath, p) for p in (patterns or []))


    # Normalize the target to a project-relative POSIX path.
    target = file_path.replace("\\", "/")
    if os.path.isabs(target):
        root_norm = os.path.realpath(root)
        target_norm = os.path.realpath(target)
        try:
            rel = os.path.relpath(target_norm, root_norm).replace("\\", "/")
        except ValueError:
            rel = target_norm.replace("\\", "/")
        if rel == ".." or rel.startswith("../") or os.path.isabs(rel):
            print("ALLOW")  # outside the project root: repo-containment's job
            return 0
    else:
        rel = target
        while rel.startswith("./"):
            rel = rel[2:]
        if not rel or rel == "." or rel.startswith("../"):
            print("ALLOW")
            return 0

    # 1. Directory markers are never blocked (scaffold exception, §3.5).
    if os.path.basename(rel) in markers:
        print("ALLOW")
        return 0

    classes = data.get("classes") or []
    legacy = data.get("legacy") or []
    unmanaged = data.get("unmanaged") or []
    strict = bool(data.get("strict", False))

    # 2. unmanaged[] -> allow in both modes (D-8).
    if matches_any(rel, unmanaged):
        print("ALLOW")
        return 0

    # 3. legacy[] -> block in both modes.  Legacy is BEFORE class-path release,
    #    otherwise the flat ADR legacy glob inside docs/adr would be ineffective.
    if matches_any(rel, legacy):
        print(
            "BLOCK:artifact-path-guard: '%s' targets a legacy[] path; "
            "place new artifacts under an artifact-locations class path "
            "or add a legacy entry." % rel
        )
        return 0

    # 4. Class path (or a declared file-set file) -> allow.
    for cls in classes:
        path = cls.get("path")
        if path:
            path = path.replace("\\", "/").rstrip("/")
            if rel == path or rel.startswith(path + "/"):
                print("ALLOW")
                return 0
        else:
            for pat in (cls.get("patterns") or []):
                pat = pat.replace("\\", "/")
                if not any(c in pat for c in "*?{}[]") and rel == pat:
                    print("ALLOW")
                    return 0

    # Guess the intended class from a path segment, for the repair hint.
    expected = None
    expected_cls = None
    for cls in classes:
        name = cls.get("name") or ""
        path = cls.get("path")
        if path and name and name in rel.split("/"):
            expected = path.replace("\\", "/").rstrip("/")
            expected_cls = name
            break

    # 5. Managed tree (top-level segment of a declared class path) -> misroute.
    managed_roots = set()
    for cls in classes:
        path = cls.get("path")
        if path:
            first = path.replace("\\", "/").strip("/").split("/", 1)[0]
            if first:
                managed_roots.add(first)

    if rel.split("/", 1)[0] in managed_roots:
        hint = ("expected '%s' (classes.%s.path)" % (expected, expected_cls)
                if expected else "expected a declared artifact-locations class path")
        message = ("artifact-path-guard: '%s' is a misroute in a managed tree; %s; "
                   "add to artifact-locations.classes.<x>.path or a legacy entry." % (rel, hint))
        print(("BLOCK:" if strict else "WARN:") + message)
        return 0

    # 6. Root: outside all managed trees -> allow.
    print("ALLOW")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], ""))
