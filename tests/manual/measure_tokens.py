#!/usr/bin/env python3
"""Manual helper: compare bytes with real token counts for the context-report artifacts.

Not part of the automated suite. The optional tokenizer (``tiktoken``) is NOT a
framework dependency (Stdlib + PyYAML only in ``scripts/lib``); it is imported
here lazily. Without it the script prints a notice and exits 0 -- the byte
column of the measurement doc then stays "approximated (bytes // 4), UNVERIFIED".
With ``--strict`` a missing tokenizer is an error instead: exit code 3.

Usage (from the repo root)::

    python3 scripts/sync.py --context-report --json > report.json   # or reuse the sink file
    python3 tests/manual/measure_tokens.py report.json

Input is the JSON emitted by ``--context-report --json`` (provider -> artifact
-> {bytes, ...}). The tokenizer cannot see rendered text from the report alone,
so with ``--files`` real files are tokenized directly::

    python3 tests/manual/measure_tokens.py --files CLAUDE.md AGENTS.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load_encoder():
    """Return a ``str -> int`` token counter or ``None`` when no tokenizer exists."""
    try:
        import tiktoken  # type: ignore
    except ImportError:
        return None
    try:
        enc = tiktoken.get_encoding("cl100k_base")
    except Exception:  # vocabulary download blocked (offline / proxy): treat as unavailable
        return None
    return lambda text: len(enc.encode(text))


def _print_report(report: dict) -> None:
    print("provider | artifact | bytes | tokens_est (bytes//4)")
    for provider, artifacts in report.items():
        for name, stats in artifacts.items():
            print("%s | %s | %d | %d" % (provider, name, stats["bytes"], stats["bytes"] // 4))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("report", nargs="?", help="JSON from --context-report --json")
    parser.add_argument("--files", nargs="+", help="files to tokenize directly")
    parser.add_argument("--strict", action="store_true",
                        help="exit 3 instead of 0 when no tokenizer is available")
    args = parser.parse_args(argv)

    count = _load_encoder()
    missing_rc = 3 if args.strict else 0
    if args.report:
        _print_report(json.loads(Path(args.report).read_text(encoding="utf-8")))
    if not args.files:
        if count is None:
            print("NOTICE: no tokenizer available (pip install tiktoken to measure real "
                  "ratios); byte-based estimates above are UNVERIFIED.")
        return missing_rc if count is None else 0
    if count is None:
        print("NOTICE: no tokenizer available (pip install tiktoken); cannot tokenize "
              "files. Ratios stay UNVERIFIED.")
        return missing_rc
    print("file | bytes | tokens | bytes/token")
    for name in args.files:
        data = Path(name).read_bytes()
        tokens = count(data.decode("utf-8", errors="replace"))
        print("%s | %d | %d | %.2f" % (name, len(data), tokens, len(data) / max(tokens, 1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
