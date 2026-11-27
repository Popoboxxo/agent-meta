#!/usr/bin/env python3
"""Git-push argument walking for shared hook classifiers.

Issue #1238a: importable logic plus a byte-identical source emitter.
This module is stdlib-only.
"""
import sys
from pathlib import Path

# agent-meta:emit-start
def walk_push_args(args, opts_with_value):
    pos, opts = [], []
    i = 0
    while i < len(args):
        a = args[i]
        i += 1
        if a == "--":
            pos += args[i:]
            break
        if not a.startswith("-") or a == "-":
            pos.append(a)
            continue
        if a.startswith("--"):
            name, eq, val = a.partition("=")
            if eq:
                opts.append((name, val, a))
            elif name in opts_with_value:
                opts.append((name, args[i] if i < len(args) else "", a))
                i += 1
            else:
                opts.append((name, None, a))
            continue
        # short cluster: one option per character; 'o' takes the rest of
        # the cluster ('-o<val>') or the next token ('-o <val>') as value
        rest = a[1:]
        for k, ch in enumerate(rest):
            if ch == "o":
                if k + 1 < len(rest):
                    opts.append(("-o", rest[k + 1:], a))
                else:
                    opts.append(("-o", args[i] if i < len(args) else "", a))
                    i += 1
                break
            opts.append(("-" + ch, None, a))
    return pos, opts
# agent-meta:emit-end


_EMIT_START = "# agent-meta:emit-start\n"
_EMIT_END = "# agent-meta:emit-end\n"


def _emitted_source() -> str:
    source = Path(__file__).read_text(encoding="utf-8")
    start = source.index(_EMIT_START) + len(_EMIT_START)
    end = source.index(_EMIT_END, start)
    return source[start:end]


def main(argv: list[str], stdin: str) -> int:
    """Emit the source fragment consumed by composite hook calls."""
    del argv, stdin
    sys.stdout.write(_emitted_source())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], ""))
