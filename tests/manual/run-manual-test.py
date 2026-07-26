#!/usr/bin/env python3
"""
run-manual-test.py — Zentraler Einstiegspunkt für manuelle Tests.

Steuert die komplette Test-Pipeline: Vorbereitung → Validierung → Reporting.

Usage:
  python tests/manual/run-manual-test.py prepare --scenario SE-02
  python tests/manual/run-manual-test.py validate --scenario SE-02
  python tests/manual/run-manual-test.py validate --all --report
  python tests/manual/run-manual-test.py list
  python tests/manual/run-manual-test.py clean
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ENGINE_DIR = SCRIPT_DIR / "test-engine"
REPO_ROOT = SCRIPT_DIR.parent
SCENARIOS_SE_DIR = SCRIPT_DIR / "scenarios" / "se"
SCENARIOS_FW_DIR = SCRIPT_DIR / "scenarios" / "meta-agent"


def load_all_scenarios() -> dict:
    scenarios = {"SE": [], "FW": []}
    for f in sorted(SCENARIOS_SE_DIR.glob("*.json")):
        with open(f, "r", encoding="utf-8") as fh:
            scenarios["SE"].append(json.load(fh))
    for f in sorted(SCENARIOS_FW_DIR.glob("*.json")):
        with open(f, "r", encoding="utf-8") as fh:
            scenarios["FW"].append(json.load(fh))
    return {"scenarios": scenarios}


def run_prepare(args):
    """Run prepare-test-session.py"""
    cmd = [
        sys.executable, str(ENGINE_DIR / "prepare-test-session.py"),
        "--scenario", args.scenario
    ]
    if args.clear_log:
        cmd.append("--clear-log")
    if args.target_repo:
        cmd.extend(["--target-repo", args.target_repo])
    if args.dry_run:
        cmd.append("--dry-run")

    print(f"  [i] Starte Vorbereitung: {args.scenario}")
    result = subprocess.run(cmd, capture_output=False, text=True)  # noqa: PLW1510
    return result.returncode


def run_validate(args):
    """Run validate-delegation.py"""
    cmd = [
        sys.executable, str(ENGINE_DIR / "validate-delegation.py")
    ]
    if args.scenario:
        cmd.extend(["--scenario", args.scenario])
    elif args.all:
        cmd.append("--all")
    if args.report:
        cmd.append("--report")
    if args.auto_report_fail:
        cmd.append("--auto-report-fail")
    if args.target_repo:
        cmd.extend(["--target-repo", args.target_repo])
    if args.log:
        cmd.extend(["--log", args.log])

    print("  [i] Starte Validierung...")
    result = subprocess.run(cmd, capture_output=False, text=True)  # noqa: PLW1510
    return result.returncode


def run_list():
    """List all scenarios"""
    scenarios = load_all_scenarios()
    print("\n  Manuelle Test-Szenarien")
    print("  " + "=" * 60)
    for group_name, group_data in scenarios["scenarios"].items():
        print(f"\n  [{group_name}]")
        for s in group_data:
            print(f"    {s['id']}: {s['name']}")
    print()
    return 0


def run_clean():
    """Clean test artifacts"""

    # Clean bug reports
    bugs_dir = REPO_ROOT / "docs" / "bugs"
    if bugs_dir.exists():
        count = len(list(bugs_dir.glob("*.md")))
        for f in bugs_dir.glob("*.md"):
            f.unlink()
        print(f"  [OK] {count} Bug-Reports gelöscht: {bugs_dir}")

    # Clean results
    results_dir = SCRIPT_DIR / "results"
    if results_dir.exists():
        count = len(list(results_dir.glob("*")))
        for f in results_dir.glob("*"):
            if f.is_file():
                f.unlink()
        print(f"  [OK] {count} Ergebnis-Dateien gelöscht: {results_dir}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Zentraler Einstiegspunkt für manuelle Tests",
        usage="python tests/manual/run-manual-test.py <command> [options]"
    )
    subparsers = parser.add_subparsers(dest="command", help="Verfügbare Commands")

    # prepare
    prepare_parser = subparsers.add_parser("prepare", help="Test-Session vorbereiten")
    prepare_parser.add_argument("--scenario", required=True, help="Szenario-ID (z.B. SE-02)")
    prepare_parser.add_argument("--clear-log", action="store_true", help="Viz-Log leeren")
    prepare_parser.add_argument("--target-repo", default=None, help="Ziel-Repository")
    prepare_parser.add_argument("--dry-run", action="store_true",
                                  help="Dry-Run: Prompt enthält Hinweis auf keine echten Operationen")

    # validate
    validate_parser = subparsers.add_parser("validate", help="Test-Ergebnisse validieren")
    validate_parser.add_argument("--scenario", default=None, help="Ein Szenario validieren")
    validate_parser.add_argument("--all", action="store_true", help="Alle Szenarien validieren")
    validate_parser.add_argument("--report", action="store_true", help="Report generieren")
    validate_parser.add_argument("--auto-report-fail", action="store_true", help="Auto-Bug-Reports bei FAIL")
    validate_parser.add_argument("--target-repo", default=None, help="Ziel-Repository")
    validate_parser.add_argument("--log", default=None, help="Pfad zum Viz-Log")

    # list
    subparsers.add_parser("list", help="Alle Szenarien auflisten")

    # clean
    subparsers.add_parser("clean", help="Test-Artefakte löschen")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "prepare":
        return run_prepare(args)
    elif args.command == "validate":
        return run_validate(args)
    elif args.command == "list":
        return run_list()
    elif args.command == "clean":
        return run_clean()

    return 0


if __name__ == "__main__":
    sys.exit(main())
