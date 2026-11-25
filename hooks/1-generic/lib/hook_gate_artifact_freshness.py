#!/usr/bin/env python3
"""Artifact-freshness gate logic for the deployed release-gate hook.

Issue #1238c2: importable replacement for the former inline Python heredoc.
The documented YAML subset, git-first timestamp resolution, messages and exit
codes are unchanged.
"""
from __future__ import annotations

import glob as globmod
import os
import subprocess
import sys


def main(argv: list[str], stdin: str) -> int:
    """Check configured artifact pairs and return 0=pass or 1=fail."""
    del stdin
    if len(argv) != 2:
        return 1
    config_path, gate_name = argv

    # --- minimal stdlib-only parser for the documented subset ---
    pairs = []
    with open(config_path, encoding="utf-8") as f:
        lines = f.readlines()

    in_artifacts = False
    current = {}
    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "artifacts:":
            in_artifacts = True
            continue
        if not in_artifacts:
            continue
        if stripped.startswith("- source:"):
            if current.get("source") and current.get("generated"):
                pairs.append(current)
            current = {"source": stripped[len("- source:"):].strip().strip('"\'')}
        elif stripped.startswith("source:"):
            current["source"] = stripped[len("source:"):].strip().strip('"\'')
        elif stripped.startswith("generated:"):
            current["generated"] = stripped[len("generated:"):].strip().strip('"\'')
    if current.get("source") and current.get("generated"):
        pairs.append(current)

    def newest_mtime(pattern):
        matches = globmod.glob(pattern, recursive=True)
        if not matches:
            return None
        return max(os.path.getmtime(m) for m in matches if os.path.isfile(m))

    def git_mtime(pattern):
        try:
            out = subprocess.run(
                ["git", "log", "-1", "--format=%ct", "--", pattern],
                capture_output=True, text=True, timeout=10,
            )
            if out.returncode == 0 and out.stdout.strip():
                return float(out.stdout.strip())
        except Exception:
            pass
        return None

    def resolve_mtime(pattern):
        # issue #600: prefer git-log-derived commit timestamps over filesystem
        # mtime for BOTH source and generated artifacts. A fresh `git clone` (or
        # several CI checkout actions) commonly sets a uniform mtime on every
        # checked-out file, which makes a plain filesystem-mtime comparison an
        # unreliable freshness signal — it can produce both false passes (all
        # mtimes identical, "not older than") and false fails depending on
        # checkout order. git_mtime() is unaffected by checkout mtime behavior
        # since it reads the commit timestamp git itself recorded. Falls back
        # to filesystem mtime only for paths git has no history for at all
        # (e.g. a gitignored/never-committed build artifact) — otherwise every
        # such artifact would incorrectly resolve to "missing".
        return git_mtime(pattern) or newest_mtime(pattern)

    errors = []
    checked = 0
    for pair in pairs:
        source, generated = pair["source"], pair["generated"]
        src_mtime = resolve_mtime(source)
        gen_mtime = resolve_mtime(generated)
        if src_mtime is None:
            print(f"[SKIP] {gate_name}: source not found: {source}")
            continue
        checked += 1
        if gen_mtime is None:
            errors.append(f"{generated} (from {source}) — generated artifact missing")
            continue
        if src_mtime > gen_mtime:
            errors.append(f"{generated} is older than its source {source} — rebuild required")

    for error in errors:
        print(f"[FAIL] {gate_name}: {error}")
    if not errors:
        print(f"[INFO] {gate_name}: checked {checked} artifact pair(s), all fresh")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], ""))
