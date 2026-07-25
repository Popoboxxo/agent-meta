#!/usr/bin/env python3
"""
agent-meta consistency-check.py
================================
Validates agent templates, commands and cross-references for consistency.

Usage:
  # Check all agents + commands in agent-meta:
  py scripts/consistency-check.py

  # Check only git-changed files (fast, for pre-commit / CI):
  py scripts/consistency-check.py --changed

  # Check a specific file:
  py scripts/consistency-check.py --file agents/1-generic/my-agent.md

  # JSON output (for CI pipelines):
  py scripts/consistency-check.py --json

  # Strict mode: warnings also fail (exit 1):
  py scripts/consistency-check.py --strict

Exit codes:
  0 = no errors (warnings allowed unless --strict)
  1 = one or more errors found
  2 = script error (file not found, git unavailable, etc.)
"""

import argparse
import subprocess
import sys
from pathlib import Path

# ── path setup ────────────────────────────────────────────────────────────────
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

_AGENT_META_ROOT = _SCRIPTS_DIR.parent

from lib.consistency.report import Finding, Severity, print_report, print_json_report
from lib.consistency.frontmatter import check_agent_frontmatter
from lib.consistency.crossrefs import (
    check_role_defaults_coverage,
    check_role_defaults_has_generic_source,
    check_orchestrator_table,
    check_changelog_mentions_new_files,
    check_schema_refs,
)
from lib.consistency.placeholders import check_placeholders, load_project_vars
from lib.consistency.commands import check_command_frontmatter, check_duplicate_commands
from lib.consistency.handoff_contracts import check_handoff_contracts
from lib.consistency.docs import (
    check_sync_cli_docs,
    check_ui_help_mappings,
    check_readme_docs_index,
)


# ── git helpers ───────────────────────────────────────────────────────────────

def get_changed_files(root: Path) -> set[str]:
    """Return set of files changed vs HEAD (staged + unstaged + untracked agents/commands)."""
    changed: set[str] = set()
    try:
        # Tracked changes vs HEAD
        for flag in [["git", "diff", "--name-only", "HEAD"],
                     ["git", "diff", "--name-only", "--cached"]]:
            r = subprocess.run(flag, cwd=str(root), capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                changed.update(l.strip() for l in r.stdout.splitlines() if l.strip())
        # Untracked new files (agents + commands only)
        r = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", "agents/", "commands/"],
            cwd=str(root), capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            changed.update(l.strip() for l in r.stdout.splitlines() if l.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return changed


def get_new_files_vs_main(root: Path) -> list[str]:
    """Return files added in this branch vs main/master (for changelog check)."""
    for base in ("main", "master"):
        try:
            r = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=A", f"{base}...HEAD"],
                cwd=str(root), capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0:
                return [l.strip() for l in r.stdout.splitlines() if l.strip()]
        except (OSError, subprocess.SubprocessError):
            pass
    return []


# ── file collection ───────────────────────────────────────────────────────────

def collect_agent_files(root: Path, only: set[str] | None = None) -> list[Path]:
    """Collect agent .md files from agents/ (1-generic and 2-platform)."""
    files: list[Path] = []
    for layer in ("1-generic", "2-platform"):
        d = root / "agents" / layer
        if not d.exists():
            continue
        for md in sorted(d.glob("*.md")):
            if md.name.startswith("_"):
                continue
            rel = str(md.relative_to(root)).replace("\\", "/")
            if only is None or rel in only:
                files.append(md)
    return files


def collect_command_files(root: Path, only: set[str] | None = None) -> list[Path]:
    """Collect command .md files from commands/."""
    files: list[Path] = []
    for layer in ("1-generic", "2-platform", "0-external"):
        d = root / "commands" / layer
        if not d.exists():
            continue
        for md in sorted(d.glob("*.md")):
            rel = str(md.relative_to(root)).replace("\\", "/")
            if only is None or rel in only:
                files.append(md)
    return files


# ── main check runner ─────────────────────────────────────────────────────────

def run_checks(
    root: Path,
    changed_only: bool = False,
    specific_file: Path | None = None,
) -> list[Finding]:
    findings: list[Finding] = []

    changed_files: set[str] | None = None
    if changed_only or specific_file:
        changed_files = get_changed_files(root) if changed_only else None

    project_vars = load_project_vars(root)

    # Determine which files to check
    if specific_file:
        rel = str(specific_file.relative_to(root)).replace("\\", "/")
        if "commands/" in str(specific_file):
            cmd_files = [specific_file]
            agent_files = []
        else:
            agent_files = [specific_file]
            cmd_files = []
        only_set = {rel}
    else:
        only_set = changed_files if changed_only else None
        agent_files = collect_agent_files(root, only_set)
        cmd_files = collect_command_files(root, only_set)

    # ── per-file: agent frontmatter + placeholders ────────────────────────────
    for path in agent_files:
        content = _read(path)
        if content is None:
            continue
        findings += check_agent_frontmatter(path, content, root, changed_files)
        findings += check_placeholders(path, content, root, project_vars)

    # ── per-file: command checks ──────────────────────────────────────────────
    for path in cmd_files:
        content = _read(path)
        if content is None:
            continue
        findings += check_command_frontmatter(path, content, root)

    # ── global cross-reference checks (skip in single-file mode) ─────────────
    if not specific_file:
        findings += check_role_defaults_coverage(root)
        findings += check_role_defaults_has_generic_source(root)
        findings += check_orchestrator_table(root)
        findings += check_duplicate_commands(root)
        findings += check_schema_refs(root)
        findings += check_handoff_contracts(root)

        # Phase 5: Documentation & UI Consistency
        findings.extend(check_sync_cli_docs(_AGENT_META_ROOT))
        findings.extend(check_ui_help_mappings(_AGENT_META_ROOT))
        findings.extend(check_readme_docs_index(_AGENT_META_ROOT))

        # Changelog check: only meaningful when checking changed/new files
        new_files = get_new_files_vs_main(root)
        if new_files:
            findings += check_changelog_mentions_new_files(root, new_files)

    return findings


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"  ⚠️  Cannot read {path}: {e}", file=sys.stderr)
        return None


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate agent-meta agents, commands and cross-references.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--changed", action="store_true",
        help="Only check files changed vs HEAD (staged, unstaged, untracked in agents/ + commands/).",
    )
    parser.add_argument(
        "--file", metavar="PATH",
        help="Check a single file only.",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output findings as JSON (machine-readable, for CI pipelines).",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Exit 1 on warnings too (not just errors).",
    )
    parser.add_argument(
        "--root", metavar="DIR", default=None,
        help="agent-meta root directory (default: parent of scripts/).",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else _AGENT_META_ROOT

    specific_file: Path | None = None
    if args.file:
        specific_file = Path(args.file).resolve()
        if not specific_file.exists():
            print(f"ERROR: File not found: {specific_file}", file=sys.stderr)
            return 2

    findings = run_checks(root, changed_only=args.changed, specific_file=specific_file)

    if args.json:
        exit_code = print_json_report(findings)
    else:
        exit_code = print_report(findings, root, args.changed)

    if args.strict and any(f.severity == Severity.WARNING for f in findings):
        exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
