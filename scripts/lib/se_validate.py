"""Standalone SE-cascade validation CLI mode (``sync.py --validate-se``).

Issue #338, Phase 3 "Sync-Integration" of the #339 concept. Unlike
``--validate`` this mode runs no sync and no consistency suite: it is a
read-only gate over the project's SE cascade artifacts (``docs/se`` by
default) implementing the B1-B5 checks from
``lib/consistency/se_cascade.py``.

Exit codes:
- 0: clean run, or no SE artifacts present ("nothing to check")
- 1: findings exist (ERROR and WARNING both count — the flag is a CI gate)

The handler lives in its own module (not ``lib/cli_commands.py``) because
that module is already over the 600-line module budget and this mode is
fully self-contained.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from lib.log import SyncLog

if TYPE_CHECKING:  # annotations only — keeps runtime imports lazy
    from lib.consistency.report import Finding

MODE = "validate-se"


def validate_se_cascade(project_root: Path, config: dict | None,
                        log: SyncLog) -> int:
    """Run the SE-cascade checks and print the report. Returns the exit code.

    Exit 0 when the project has no SE artifacts (graceful skip) or when the
    checks pass; 1 when any finding (error or warning) was reported.
    """
    # Late imports keep `import lib.se_validate` cheap for non-SE CLI modes.
    from lib.consistency.report import Severity
    from lib.consistency.se_cascade import (
        has_se_artifacts,
        resolve_se_roots,
        run_se_cascade_checks,
    )

    if not has_se_artifacts(project_root, config):
        roots = ", ".join(resolve_se_roots(config))
        message = f"no SE cascade artifacts under {roots} — nothing to check"
        log.note(MODE, message)
        print(f"\n  i  validate-se: {message} (exit 0)")
        return 0

    findings = run_se_cascade_checks(project_root, config)
    _print_se_report(findings, project_root)
    if not findings:
        log.note(MODE, "all SE-cascade checks passed")
        return 0
    errors = sum(1 for f in findings if f.severity == Severity.ERROR)
    warnings = len(findings) - errors
    log.note(MODE, f"{errors} error(s), {warnings} warning(s)")
    return 1


def _print_se_report(findings: list[Finding], project_root: Path) -> None:
    """Print the human-readable SE validation report (print_report style)."""
    by_file: dict[str, list] = {}
    for finding in findings:
        by_file.setdefault(finding.file, []).append(finding)

    print()
    print("=" * 64)
    print("  agent-meta SE-cascade validation (--validate-se)")
    print(f"  Project: {project_root}")
    print("=" * 64)
    for filepath in sorted(by_file):
        print()
        print(f"  >>>  {filepath}")
        for finding in sorted(by_file[filepath], key=lambda x: x.severity.value):
            print(str(finding))
    print()
    errors = sum(1 for f in findings if f.severity.value == "ERROR")
    warnings = sum(1 for f in findings if f.severity.value == "WARNING")
    print("-" * 64)
    if not findings:
        print("  [PASS]  All SE-cascade checks passed.")
    else:
        parts = []
        if errors:
            parts.append(f"{errors} error(s)")
        if warnings:
            parts.append(f"{warnings} warning(s)")
        status = "FAIL" if errors else "WARN"
        print(f"  [{status}]  {', '.join(parts)} found  "
              f"({len(findings)} total findings)")
    print()


def _handle_validate_se(ctx) -> None:  # noqa: ANN001 — duck-typed _SyncContext
    """Handle --validate-se: standalone, read-only SE-cascade validation.

    Always exits directly (no fall-through to the common sync tail): the
    mode must never write files or trigger the provider-restart notice.
    """
    ctx.mode = MODE
    log = ctx.log
    log.note(MODE, "running SE-cascade validation (read-only, no sync)")
    code = validate_se_cascade(ctx.project_root, ctx.config, log)
    sys.exit(code)
