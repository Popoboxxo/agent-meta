#!/usr/bin/env python3
"""Merge catalog.generated.yaml + catalog.manual.yaml and print one line per case.

Consumed by run_eval.sh, which can't parse YAML itself. Each line is
tab-unfriendly-safe: fields are joined with \\x1f (ASCII unit separator),
which cannot appear in normal task text, so run_eval.sh can split on it
without worrying about commas/pipes/colons inside the task string.

Output field order: id, pipeline, category, expected (comma-joined),
source_keyword, role, prompt (raw override), expected_any, expected_all,
forbidden (each comma-joined), task (task is last since it's the only field
that may itself contain arbitrary text, including trailing whitespace).

Usage:
    python3 list_cases.py [catalog.yaml ...]

With no arguments, reads catalog.generated.yaml and catalog.manual.yaml from
this script's own directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml  # type: ignore[import]
except ImportError:
    print("PyYAML is required (pip install pyyaml).", file=sys.stderr)
    sys.exit(1)

SEP = "\x1f"


def load_cases(path: Path) -> list[dict]:
    """Load the `cases` list from a single catalog YAML file."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("cases", [])


def main(argv: list[str]) -> int:
    """Print merged catalog cases as SEP-delimited lines. Returns exit code."""
    script_dir = Path(__file__).resolve().parent
    paths = (
        [Path(p) for p in argv]
        if argv
        else [script_dir / "catalog.generated.yaml", script_dir / "catalog.manual.yaml"]
    )

    seen_ids: dict[str, str] = {}
    for path in paths:
        for case in load_cases(path):
            case_id = str(case.get("id", ""))
            if not case_id:
                print(f"[list_cases] skipping case without 'id' in {path}", file=sys.stderr)
                continue
            if case_id in seen_ids:
                print(
                    f"[list_cases] duplicate case id '{case_id}' in {path} "
                    f"(already defined in {seen_ids[case_id]}) -- skipping",
                    file=sys.stderr,
                )
                continue
            seen_ids[case_id] = str(path)

            pipeline = case.get("pipeline") or ""
            category = case.get("category", "")
            expected = ",".join(str(e) for e in case.get("expected", []))
            source_keyword = case.get("source_keyword") or ""
            # Behavioral fields (issue #535): role under test, raw prompt
            # override, and extended assert criteria. Empty for legacy
            # routing cases, which keep the equals-grading path.
            role = case.get("role") or ""
            prompt = case.get("prompt") or ""
            expected_any = ",".join(str(e) for e in case.get("expected_any", []))
            expected_all = ",".join(str(e) for e in case.get("expected_all", []))
            forbidden = ",".join(str(e) for e in case.get("forbidden", []))

            # task stays LAST: it is the only field that may contain
            # arbitrary text including the separator-adjacent whitespace.
            print(SEP.join([
                case_id,
                pipeline,
                category,
                expected,
                source_keyword,
                role,
                prompt,
                expected_any,
                expected_all,
                forbidden,
                task,
            ]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
