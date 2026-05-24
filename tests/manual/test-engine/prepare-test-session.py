#!/usr/bin/env python3
"""
prepare-test-session.py — Bereitet eine manuelle Test-Session vor.

Zeigt den User-Prompt und die erwartete Delegationskette an,
sodass der Tester den Prompt in den Chat kopieren kann.
Optional: Leert das Viz-Log und startet den Viz-Server.

Usage:
  python tests/manual/test-engine/prepare-test-session.py --scenario SE-01
  python tests/manual/test-engine/prepare-test-session.py --scenario FW-01 --clear-log
  python tests/manual/test-engine/prepare-test-session.py --scenario SE-01 --start-server
  python tests/manual/test-engine/prepare-test-session.py --list
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent  # tests/manual/test-engine/ → tests/manual/ → tests/ → repo-root
SCENARIOS_FILE = SCRIPT_DIR / "manual-scenarios.json"

# Default viz log path (can be overridden by --target-repo)
DEFAULT_VIZ_LOG = REPO_ROOT / ".meta-viz" / "events.jsonl"


SCENARIOS_SE_DIR = SCRIPT_DIR.parent / "scenarios" / "se"
SCENARIOS_FW_DIR = SCRIPT_DIR.parent / "scenarios" / "meta-agent"


def load_all_scenarios() -> dict:
    scenarios = {"SE": [], "FW": []}
    for f in sorted(SCENARIOS_SE_DIR.glob("*.json")):
        with open(f, "r", encoding="utf-8") as fh:
            scenarios["SE"].append(json.load(fh))
    for f in sorted(SCENARIOS_FW_DIR.glob("*.json")):
        with open(f, "r", encoding="utf-8") as fh:
            scenarios["FW"].append(json.load(fh))
    return {"scenarios": scenarios}


def find_scenario(scenario_id: str) -> dict | None:
    all_scenarios = load_all_scenarios()
    for group_data in all_scenarios["scenarios"].values():
        for s in group_data:
            if s["id"] == scenario_id:
                return s
    return None


def list_all_scenarios(scenarios_data: dict):
    print("\n  Verfügbare Test-Szenarien:")
    print("  " + "=" * 60)
    for group_name, group_data in scenarios_data.get("scenarios", {}).items():
        print(f"\n  [{group_name}]")
        for s in group_data:
            print(f"    {s['id']}: {s['name']}")
    print()


def clear_viz_log(viz_log_path: Path):
    if viz_log_path.exists():
        viz_log_path.write_text("", encoding="utf-8")
        print(f"  [OK] Viz-Log geleert: {viz_log_path}")
    else:
        print(f"  [!] Viz-Log nicht gefunden: {viz_log_path}")
        print(f"      Erstelle Verzeichnis...")
        viz_log_path.parent.mkdir(parents=True, exist_ok=True)
        viz_log_path.write_text("", encoding="utf-8")
        print(f"  [OK] Viz-Log erstellt: {viz_log_path}")


def display_scenario(scenario: dict, target_repo: str | None = None, dry_run: bool = False):
    sid = scenario["id"]
    name = scenario["name"]
    prompt = scenario["user_input"]
    routing = scenario.get("expected_routing", {})
    chain = scenario.get("delegation_chain", [])
    agents = scenario.get("required_agents", [])
    critical = scenario.get("critical_checks", [])
    dry_notes = scenario.get("dry_run_notes", [])

    repo_info = f"Ziel-Repo: {target_repo}" if target_repo else "Repo: agent-meta (aktuell)"
    dry_label = " [DRY-RUN]" if dry_run else ""

    print("\n" + "=" * 70)
    print(f"  TEST-SESSION: {sid}{dry_label}")
    print(f"  {repo_info}")
    print("=" * 70)
    print(f"\n  Szenario: {name}")
    print(f"\n  {'='*60}")
    print("  >>> KOPIERE DIESEN PROMPT IN DEN CHAT <<<")
    print(f"  {'='*60}")

    # Append dry-run suffix to prompt if requested
    if dry_run:
        dry_suffix = " (dry-run: keine echten Git-Ops, kein Push, kein Release)"
        display_prompt = prompt + dry_suffix
    else:
        display_prompt = prompt

    print(f"\n  \"{display_prompt}\"")
    print(f"\n  {'='*60}")
    print("  >>> ENDE PROMPT <<<")
    print(f"  {'='*60}")

    print("\n  Erwartete Routing-Regel:")
    if routing:
        print(f"    orchestrator -> {routing.get('to', '?')} (Intent: {routing.get('intent', '?')})")

    print("\n  Erwartete Delegationskette:")
    if chain:
        for i, link in enumerate(chain, 1):
            note = f" [{link.get('note', '')}]" if link.get('note') else ""
            print(f"    {i}. {link['from']} -> {link['to']}{note}")
    else:
        print("    (keine Delegationen — Agent arbeitet selbstständig)")

    print("\n  Erwartete Agenten:")
    for agent in agents:
        print(f"    - {agent}")

    if critical:
        print("\n  Kritische Prüfpunkte:")
        for check in critical:
            print(f"    * {check}")

    if dry_run and dry_notes:
        print("\n  DRY-RUN Regeln (keine echten Operationen):")
        for note in dry_notes:
            print(f"    ⚠ {note}")
    elif dry_run:
        print("\n  DRY-RUN: Keine echten Git-/Release-/Push-Operationen!")

    print("\n  Provider-Dokumentation:")
    print("    WICHTIG: Notiere nach dem Test den verwendeten Provider!")
    print("    Mögliche Werte: Opencode, Gemini, Claude, Continue")
    print("    Der Provider steht im Viz-Log unter agent_start.provider")

    print("\n" + "=" * 70)
    print("  ANLEITUNG:")
    if dry_run:
        print("  DRY-RUN MODUS: Alle Operationen sind simulations-only.")
    print("  1. Kopiere den PROMPT in den Hauptchat")
    print("  2. Drücke ENTER")
    print("  3. WARTE bis alle Agenten beendet sind")
    print("  4. Führe aus: python tests/manual/run-manual-test.py validate")
    dry_flag = " --dry-run" if dry_run else ""
    if target_repo:
        print(f"     --scenario {sid} --target-repo {target_repo}{dry_flag}")
    else:
        print(f"     --scenario {sid}{dry_flag}")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Prepare a manual test session")
    parser.add_argument("--scenario", default=None, help="Scenario ID (e.g. SE-01)")
    parser.add_argument("--clear-log", action="store_true", help="Clear viz log before test")
    parser.add_argument("--start-server", action="store_true", help="Start viz server")
    parser.add_argument("--list", action="store_true", help="List all scenarios")
    parser.add_argument("--target-repo", default=None,
                        help="Target repository path (for projects using agent-meta as submodule). "
                             "Viz log will be cleared at <repo>/.meta-viz/events.jsonl")
    parser.add_argument("--dry-run", action="store_true",
                        help="Dry-Run Modus: zeigt '(dry-run: keine echten Git-Ops)' im Prompt an")

    args = parser.parse_args()

    if args.list:
        list_all_scenarios(load_all_scenarios())
        return

    if not args.scenario:
        print("  [!] Bitte --scenario angeben oder --list für Übersicht")
        sys.exit(1)

    scenario = find_scenario(args.scenario)
    if not scenario:
        print(f"  [!] Szenario '{args.scenario}' nicht gefunden")
        print(f"      Nutze --list für verfügbare Szenarien")
        sys.exit(1)

    # Determine viz log path
    if args.target_repo:
        viz_log_path = Path(args.target_repo) / ".meta-viz" / "events.jsonl"
        print(f"\n  [i] Ziel-Repository: {args.target_repo}")
        print(f"  [i] Viz-Log: {viz_log_path}")
    else:
        viz_log_path = DEFAULT_VIZ_LOG

    if args.clear_log:
        clear_viz_log(viz_log_path)

    display_scenario(scenario, target_repo=args.target_repo, dry_run=args.dry_run)

    if args.start_server:
        print("  [i] Starte Viz-Server auf Port 8765...")
        print(f"      Führe aus: python scripts/viz-server.py start")
        print(f"      Dashboard: http://localhost:8765/")


if __name__ == "__main__":
    main()
