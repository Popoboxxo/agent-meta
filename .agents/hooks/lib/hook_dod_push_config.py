#!/usr/bin/env python3
"""Read one agent-meta project variable for dod-push-check.

Issue #1238c1: importable replacement for the former inline config-reader
heredoc.  PyYAML is preferred when available; the stdlib fallback scans the
top-level ``variables:`` block.
"""
from __future__ import annotations

import sys


def main(argv: list[str], stdin: str) -> int:
    """Print ``variables.<key>``; unreadable or missing values stay empty."""
    del stdin
    if len(argv) != 2:
        return 1
    path, key = argv
    value = ""
    try:
        if path.endswith(".json"):
            import json

            with open(path, encoding="utf-8") as handle:
                data = json.load(handle) or {}
            value = str(data.get("variables", {}).get(key, ""))
        else:
            try:
                import yaml

                with open(path, encoding="utf-8") as handle:
                    data = yaml.safe_load(handle) or {}
                value = str(data.get("variables", {}).get(key, ""))
            except Exception:
                in_variables = False
                with open(path, encoding="utf-8") as handle:
                    for line in handle:
                        line = line.rstrip("\n")
                        if line.startswith("variables:"):
                            in_variables = True
                            continue
                        if in_variables:
                            if line and not line[0].isspace():
                                break
                            stripped = line.strip()
                            if stripped.startswith(key + ":"):
                                candidate = stripped[len(key) + 1:].strip()
                                if (
                                    len(candidate) >= 2
                                    and candidate[0] in "\"'"
                                    and candidate[-1] == candidate[0]
                                ):
                                    candidate = candidate[1:-1]
                                value = candidate
                                break
    except Exception:
        value = ""
    print(value)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], ""))
