#!/usr/bin/env python3
"""Rebaseline helper entrypoint (issue #1237).

Thin CLI around :mod:`lib.rebaseline_pipeline`: parse flags, print the report
and return the exit code. All repository logic lives in ``scripts/lib``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, List

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib import rebaseline as base  # noqa: E402
from lib import rebaseline_pipeline as pipeline  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser from spec section C2."""
    parser = argparse.ArgumentParser(
        prog="rebaseline.py",
        description="Run the rebaseline steps in fixed order with a diff gate.",
    )
    parser.add_argument("--reason", default="", help="mandatory reason in write mode")
    parser.add_argument(
        "--expect", action="append", default=[], help="additional allowed path glob"
    )
    parser.add_argument(
        "--expect-key", action="append", default=[], help="additional allowed key glob"
    )
    parser.add_argument(
        "--base", default="origin/main", help="diff base (default: origin/main)"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check-only", action="store_true", help="measure only, write nothing"
    )
    mode.add_argument("--dry-run", action="store_true", help="alias for --check-only")
    parser.add_argument("--root", type=Path, default=None, help="repository root")
    parser.add_argument(
        "--steps", default="", help="comma-separated subset of the step order"
    )
    parser.add_argument(
        "--skip-verify", action="store_true", help="skip targeted pin tests"
    )
    parser.add_argument("--json", action="store_true", help="add a JSON report line")
    return parser


def _field(item: Any, name: str, default: Any = "") -> Any:
    """Read a field from a NamedTuple or a JSON dict."""
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _report_lines(result: Any, options: Any, root: Path) -> List[str]:
    """Render the human-readable ASCII report of spec section C4."""
    mode = "check-only" if options.get("check_only") else "write"
    lines = [
        "REBASELINE  root={}  base={}  mode={}".format(
            root, options.get("base", ""), mode
        )
    ]
    for warning in result.warnings or []:
        lines.append("WARNING  {}".format(warning))
    for status in result.pre or []:
        lines.append(
            "PRE  {}  {}  {}".format(
                _field(status, "klass"), _field(status, "artifact"),
                _field(status, "status"),
            )
        )
    for index, step in enumerate(result.steps or [], start=1):
        lines.append(
            "STEP  {} {}  wrote {}  gate={}".format(
                index, _field(step, "name"), _field(step, "wrote"),
                _field(step, "gate", "ok"),
            )
        )
    for status in result.post or []:
        post_status = _field(status, "status")
        lines.append(
            "POST  {}  {}  {}".format(
                _field(status, "klass"), _field(status, "artifact"),
                "OFFEN" if post_status == "betroffen" else post_status,
            )
        )
    for residual in result.residual or []:
        lines.append("RESIDUAL  {}".format(residual))
    lines.append(
        "RESULT  changed={} files  gate={}  verify={}  idempotent={}  log={}".format(
            len(result.changed_files or []), result.gate, result.verify,
            result.idempotency, result.log or "none",
        )
    )
    return lines


def main(argv: Any = None) -> int:
    """Run the helper and return one of the exit codes from spec section C3."""
    args = build_parser().parse_args(argv)
    check_only = bool(args.check_only or args.dry_run)
    root = base.resolve_root(Path(__file__), args.root)

    if not check_only and len((args.reason or "").strip()) < 10:
        print("ERROR: --reason (min. 10 chars) is required in write mode", file=sys.stderr)
        return base.EXIT_USAGE

    names = [part.strip() for part in args.steps.split(",") if part.strip()]
    steps = names or list(base.STEP_ORDER)
    unknown = [name for name in steps if name not in base.STEP_FUNCS]
    if unknown:
        print("ERROR: unknown step: {}".format(", ".join(unknown)), file=sys.stderr)
        return base.EXIT_USAGE

    options = {
        "reason": args.reason,
        "expect": list(args.expect),
        "expect_key": list(args.expect_key),
        "base": args.base,
        "check_only": check_only,
        "steps": steps,
        "skip_verify": bool(args.skip_verify),
    }
    result = pipeline.run_pipeline(root, options)
    for line in _report_lines(result, options, root):
        print(line)
    if args.json:
        print(
            json.dumps(
                pipeline.build_json_report(
                    result.pre,
                    result.steps,
                    result.post,
                    {
                        "exit_code": result.exit_code,
                        "changed": len(result.changed_files or []),
                        "gate": result.gate,
                        "verify": result.verify,
                        "idempotent": result.idempotency,
                        "residual": list(result.residual or []),
                        "log": result.log,
                    },
                ),
                sort_keys=True,
            )
        )
    return int(result.exit_code)


if __name__ == "__main__":
    sys.exit(main())
