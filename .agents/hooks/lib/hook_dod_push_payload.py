#!/usr/bin/env python3
"""Classify an unreadable/empty Bash payload for dod-push-check.

Issue #1238c1: importable replacement for the former inline ``python3 -c``
reader.  This module is stdlib-only.
"""
from __future__ import annotations

import json
import sys


def main(argv: list[str], stdin: str) -> int:
    """Print ``empty`` or ``unreadable`` for the hook payload."""
    if argv:
        return 1
    try:
        data = json.loads(stdin)
    except Exception:
        data = None
    tool_input = data.get("tool_input") if isinstance(data, dict) else None
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    tool = data.get("tool_name") if isinstance(data, dict) else None
    if not isinstance(data, dict) or (
        command not in (None, "") and tool in (None, "", "Bash")
    ):
        print("unreadable")
    else:
        print("empty")
    return 0


if __name__ == "__main__":
    sys.exit(main(
        sys.argv[1:],
        sys.stdin.buffer.read().decode("utf-8", "surrogateescape"),
    ))
