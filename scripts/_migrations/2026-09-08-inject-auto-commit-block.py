#!/usr/bin/env python3
"""One-off migration (issue #694): append the {{AUTO_COMMIT_BLOCK}}
reference + a minor version bump to every 1-generic template with
Edit/Write in tools:, except developer.md (already done, Task 4) and
_reference-agent.md (non-deployable, see tests/test_auto_commit_coverage.py).

Run once from the repo root: python3 scripts/_migrations/2026-09-08-inject-auto-commit-block.py
Safe to re-run: skips any file that already contains the block.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.auto_commit import is_role_eligible  # noqa: E402

_GENERIC_DIR = _REPO_ROOT / "agents" / "1-generic"
_EXCLUDED = {"_reference-agent", "developer"}

_APPEND_BLOCK = (
    "\n\n{{#if AUTO_COMMIT_ENABLED}}\n"
    "{{AUTO_COMMIT_BLOCK}}\n"
    "{{/if}}\n"
)

# Matches both quoted ("4.4.0") and unquoted (2.0.1) version: values.
_VERSION_RE = re.compile(r'^(version:\s*"?)(\d+)\.(\d+)\.(\d+)("?)\s*$', re.MULTILINE)


def _bump_minor(content: str) -> str:
    def _replace(match: re.Match) -> str:
        prefix, major, minor, _patch, suffix = match.groups()
        return f"{prefix}{major}.{int(minor) + 1}.0{suffix}"

    new_content, count = _VERSION_RE.subn(_replace, content, count=1)
    if count != 1:
        raise ValueError("could not find a version: line to bump")
    return new_content


def main() -> int:
    touched = []
    skipped_already_done = []
    for path in sorted(_GENERIC_DIR.glob("*.md")):
        role = path.stem
        if role in _EXCLUDED:
            continue
        if not is_role_eligible(role, _REPO_ROOT):
            continue
        content = path.read_text(encoding="utf-8")
        if "{{AUTO_COMMIT_BLOCK}}" in content:
            skipped_already_done.append(role)
            continue
        content = _bump_minor(content)
        content = content.rstrip("\n") + _APPEND_BLOCK
        path.write_text(content, encoding="utf-8")
        touched.append(role)

    print(f"Touched {len(touched)} templates: {', '.join(touched)}")
    if skipped_already_done:
        print(f"Already done, skipped: {', '.join(skipped_already_done)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
