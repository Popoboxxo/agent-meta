#!/usr/bin/env python3
"""lifecycle_check.py — called by the lifecycle-check.sh hook.

Usage:
  python3 .agent-meta/scripts/lifecycle_check.py <event> [--project-root <path>]

Events: on-commit, on-merge, on-version-bump-patch, on-version-bump-minor,
        on-version-bump-major, on-release

Reads lifecycle-triggers from .meta-config/project.yaml and appends pending
tasks to .claude/pending-tasks.md.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


# ---------------------------------------------------------------------------
# Config loading (minimal, no lib/ dependency)
# ---------------------------------------------------------------------------

def _find_config(project_root: Path) -> Path | None:
    candidates = [
        project_root / ".meta-config" / "project.yaml",
        project_root / "agent-meta.config.yaml",
        project_root / "agent-meta.config.json",
    ]
    return next((c for c in candidates if c.exists()), None)


def _load_config(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        if _HAS_YAML:
            return yaml.safe_load(text) or {}
        # Minimal YAML fallback: only top-level keys matter for lifecycle-triggers
        # If PyYAML is not available, return empty (no triggers will fire)
        return {}
    return json.loads(text)


# ---------------------------------------------------------------------------
# Pending tasks file
# ---------------------------------------------------------------------------

PENDING_HEADER = "# Ausstehende Lifecycle-Tasks\n\n"
PENDING_FOOTER = (
    "\n---\n"
    "_Generiert von lifecycle-check.py — lösche diese Datei wenn alle Tasks erledigt sind._\n"
)

# Provider-specific pending-tasks paths (kept in sync with config/ai-providers.yaml)
_PROVIDER_PENDING_FILES: dict[str, str] = {
    "Claude":   ".claude/pending-tasks.md",
    "Opencode": ".opencode/pending-tasks.md",
    "Gemini":   ".gemini/pending-tasks.md",
    "Continue": ".continue/pending-tasks.md",
}

TRIGGER_LABELS = {
    "on-commit":              "Commit",
    "on-merge":               "Branch-Merge",
    "on-version-bump-patch":  "Patch-Version-Bump",
    "on-version-bump-minor":  "Minor-Version-Bump",
    "on-version-bump-major":  "Major-Version-Bump",
    "on-release":             "Release / Git-Tag",
    "on-config-change":       "Config-Änderung",
}

# Default tasks for events that should fire even without explicit configuration.
# Used only when no lifecycle-triggers.<event> is set in project.yaml.
DEFAULT_TASKS: dict[str, list[dict]] = {
    "on-config-change": [
        {
            "agent": "agent-meta-manager",
            "task": (
                ".meta-config/project.yaml was modified. Run "
                "`python scripts/sync.py` to regenerate provider context files."
            ),
        }
    ],
}


def _read_existing_tasks(path: Path) -> list[str]:
    """Return existing pending task lines (markdown list items)."""
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [l for l in lines if l.startswith("- [ ]")]


def write_pending_tasks(project_root: Path, event: str, tasks: list[dict], pending_file: str) -> None:
    """Append new pending tasks to the given pending-tasks file."""
    pending_path = project_root / pending_file
    pending_path.parent.mkdir(parents=True, exist_ok=True)

    existing = _read_existing_tasks(pending_path)
    label = TRIGGER_LABELS.get(event, event)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")  # noqa: DTZ005

    new_items = []
    for t in tasks:
        agent = t.get("agent", "orchestrator")
        task = t.get("task", "")
        item = f"- [ ] **[{agent}]** {task}"
        if item not in existing:
            new_items.append(item)

    if not new_items:
        return  # all tasks already pending

    section = f"## {label} — {timestamp}\n\n" + "\n".join(new_items)

    if pending_path.exists():
        current = pending_path.read_text(encoding="utf-8")
        # Append new section before footer
        if PENDING_FOOTER.strip() in current:
            current = current.replace(PENDING_FOOTER, f"\n{section}\n{PENDING_FOOTER}")
        else:
            current = current.rstrip("\n") + f"\n\n{section}\n"
        pending_path.write_text(current, encoding="utf-8")
    else:
        pending_path.write_text(
            PENDING_HEADER + section + PENDING_FOOTER, encoding="utf-8"
        )

    print(f"lifecycle-check: {len(new_items)} task(s) added to {pending_file} (trigger: {event})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage: lifecycle_check.py <event> [--project-root <path>]", file=sys.stderr)
        sys.exit(1)

    event = args[0]
    project_root = Path.cwd()
    if "--project-root" in args:
        idx = args.index("--project-root")
        if idx + 1 >= len(args):
            print("lifecycle-check: --project-root requires a path argument",
                  file=sys.stderr)
            sys.exit(1)
        project_root = Path(args[idx + 1]).resolve()

    config_path = _find_config(project_root)
    if not config_path:
        # No config found — silently exit (project may not use agent-meta)
        sys.exit(0)

    try:
        config = _load_config(config_path)
    except Exception as e:  # noqa: BLE001
        print(f"lifecycle-check: could not load config: {e}", file=sys.stderr)
        sys.exit(0)

    triggers = config.get("lifecycle-triggers", {})
    tasks = triggers.get(event, [])

    # Fall back to a built-in default task when the event is not explicitly
    # configured (e.g. on-config-change always suggests a re-sync).
    if not tasks:
        tasks = DEFAULT_TASKS.get(event, [])

    if not tasks:
        sys.exit(0)

    # Write to all active provider pending-files (multi-provider support)
    providers = config.get("ai-providers", config.get("ai-provider", ["Claude"]))
    if isinstance(providers, str):
        providers = [providers]
    elif isinstance(providers, dict):
        # Mapping form (provider -> settings): the keys are the provider names.
        providers = list(providers)
    elif not isinstance(providers, list):
        print(f"lifecycle-check: 'ai-providers' must be a list or mapping, "
              f"got {type(providers).__name__} — skipping", file=sys.stderr)
        sys.exit(0)

    for provider in providers:
        if not isinstance(provider, str):
            # A nested mapping/list entry is unhashable — .get() would raise.
            print(f"lifecycle-check: ignoring non-string provider entry "
                  f"({type(provider).__name__})", file=sys.stderr)
            continue
        pending_file = _PROVIDER_PENDING_FILES.get(provider, ".claude/pending-tasks.md")
        write_pending_tasks(project_root, event, tasks, pending_file)


if __name__ == "__main__":
    main()
