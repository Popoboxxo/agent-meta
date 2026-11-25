#!/usr/bin/env python3
"""Path-containment verdict for the deployed repo-containment shell hook.

Issue #1238b1: importable replacement for the inline Python verdict.  Any
error produces no ALLOW verdict, so the shell caller blocks (fail closed).
"""
import os
import sys


def main(argv: list[str], stdin: str) -> int:
    """Print ALLOW, BLOCK_SINK or BLOCK for one write target."""
    del stdin
    if len(argv) != 5:
        return 1
    root = os.path.realpath(argv[0])
    workdir = os.path.realpath(argv[1])
    sink_enabled = argv[2] == "1"
    sink_path = argv[3]
    raw = argv[4]

    if not raw:
        print("BLOCK")
        return 0

    target = os.path.realpath(raw if os.path.isabs(raw) else os.path.join(workdir, raw))
    sink_root = os.path.realpath(os.path.join(root, sink_path))

    def within(base):
        try:
            return os.path.commonpath([base, target]) == base
        except ValueError:
            return False

    if within(sink_root):
        print("ALLOW" if sink_enabled else "BLOCK_SINK")
        return 0

    if within(root):
        print("ALLOW")
        return 0

    print("BLOCK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], ""))
