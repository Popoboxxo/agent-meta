"""Standalone spec/plan-workflow validation CLI mode (``sync.py --validate-spec-plan``).

Design spec §7.3 (F12, B1/RVW-S3). Unlike
``--validate`` this mode runs no sync and no consistency suite: it is a
read-only gate over the consumer project's spec/plan/spike artifacts (design
§7.3, F12) implementing the checks from ``lib/consistency/spec_plan.py``.

Exit codes:
- 0: clean run, no spec/plan artifacts present ("nothing to check"), or the
     spec/plan workflow is disabled (master switch) — the check is a no-op
     (``check_spec_plan_workflow`` returns ``[]`` early, §10.1)
- 1: findings exist (ERROR and WARNING both count — the flag is a CI gate)

The handler lives in its own module (not ``lib/cli_commands.py``) for the same
reason as ``lib/se_validate.py``: that module is already over the 600-line
module budget and this mode is fully self-contained.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from lib.log import SyncLog

if TYPE_CHECKING:
    from lib.consistency.report import Finding

MODE = "validate-spec-plan"


def _changed_files(project_root: Path) -> set[str] | None:
    """Return repo-relative changed paths for ``project_root``.

    Union of working tree vs ``HEAD``, staged changes and untracked files (all
    paths, no directory prefix restriction — the spec/plan backlog lives under
    ``docs/plans``). Returns ``None`` when ``project_root`` is not inside a git
    work tree, which the checker interprets as "no filter" (scan everything).

    Read-only: only ``git rev-parse``/``git diff``/``git ls-files`` are invoked.
    """
    try:
        probe = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(project_root), capture_output=True, text=True, timeout=10,
        )
        if probe.returncode != 0 or probe.stdout.strip() != "true":
            return None

        changed: set[str] = set()
        for args in (
            ["git", "diff", "--name-only", "HEAD"],
            ["git", "diff", "--name-only", "--cached"],
            ["git", "ls-files", "--others", "--exclude-standard"],
        ):
            result = subprocess.run(
                args, cwd=str(project_root), capture_output=True, text=True,
                timeout=10,
            )
            if result.returncode != 0:
                continue
            changed.update(
                line.strip()
                for line in result.stdout.splitlines()
                if line.strip()
            )
        return changed
    except (OSError, subprocess.SubprocessError):
        return None


def validate_spec_plan(project_root: Path, config: dict | None,
                       log: SyncLog) -> int:
    """Run the spec/plan-workflow checks and print the report.

    Returns the exit code: 0 when there is nothing to check (no artifacts or
    the workflow is disabled) or when the checks pass; 1 when any finding
    (error or warning) was reported.
    """
    from lib.consistency.report import Severity
    from lib.consistency.spec_plan import check_spec_plan_workflow
    from lib.providers import resolve_agent_meta_root

    findings = check_spec_plan_workflow(
        project_root,
        config,
        agent_meta_root=resolve_agent_meta_root(project_root),
        changed_files=_changed_files(project_root),
    )
    if not findings:
        message = ("no spec/plan-workflow findings — nothing to check"
                   " (exit 0)")
        log.note(MODE, message)
        print(f"\n  i  validate-spec-plan: {message}")
        return 0

    _print_spec_plan_report(findings, project_root)
    errors = sum(1 for f in findings if f.severity == Severity.ERROR)
    warnings = len(findings) - errors
    log.note(MODE, f"{errors} error(s), {warnings} warning(s)")
    return 1


def _print_spec_plan_report(findings: list[Finding], project_root: Path) -> None:
    """Print the human-readable spec/plan validation report."""
    by_file: dict[str, list] = {}
    for finding in findings:
        by_file.setdefault(finding.file, []).append(finding)

    print()
    print("=" * 64)
    print("  agent-meta spec/plan-workflow validation (--validate-spec-plan)")
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
        print("  [PASS]  All spec/plan-workflow checks passed.")
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


def _handle_validate_spec_plan(ctx) -> None:
    """Handle --validate-spec-plan: standalone, read-only artifact validation.

    Always exits directly (no fall-through to the common sync tail): the mode
    must never write files or trigger the provider-restart notice.
    """
    ctx.mode = MODE
    log = ctx.log
    log.note(MODE, "running spec/plan-workflow validation (read-only, no sync)")
    code = validate_spec_plan(ctx.project_root, ctx.config, log)
    sys.exit(code)
