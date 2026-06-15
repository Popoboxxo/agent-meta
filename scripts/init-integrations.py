#!/usr/bin/env python3
"""
agent-meta init-integrations.py
================================
Idempotent installer/initializer for project-enabled integrations.

Lifecycle per integration:

    1. healthcheck    -> already installed? -> skip install
    2. install        -> via configured installer (uv|pip) from registry
    3. init           -> one-shot, gated by state file
    4. index          -> options resolved via maps_to_arg
    5. mcp-healthcheck-> verify the tool is callable
    6. clear pending  -> remove .claude/pending-integrations.json marker

Flags
-----
(no flag)   Show what will be installed and ask once for confirmation.
--yes       Skip confirmation (CI / automation).
--reindex   Re-index only. Do NOT re-install or re-init.
--check     Read-only healthcheck. No side effects. Exits 0 if all OK, else 1.

Install policy
--------------
- Default installer per integration: registry.installer (uv|pip).
- uv mode runs: `uv pip install <package>` (project env, NOT `uv tool install`).
- If uv is selected but not available -> warn on stderr + fallback to
  `python -m pip install <package>`. Never abort because of a missing uv.

Paths (multi-repo / submodule friendly)
---------------------------------------
- Registry  : <script_dir>/../config/integrations-registry.yaml
- Project   : <cwd>/.meta-config/project.yaml
- State     : <cwd>/.meta-config/.integrations-state.json
- Pending   : <cwd>/.claude/pending-integrations.json

Stdlib only. Uses PyYAML when available with a graceful fallback.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Make lib importable when script lives in <repo>/scripts/
sys.path.insert(0, str(Path(__file__).parent))

from lib.integrations import (  # noqa: E402
    load_integrations_registry,
    resolve_enabled_integrations,
    write_pending_marker,
)

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

PREFIX = "[init-integrations]"


def info(msg: str) -> None:
    print(f"{PREFIX} {msg}")


def warn(msg: str) -> None:
    print(f"{PREFIX} WARNING: {msg}", file=sys.stderr)


def error(msg: str) -> None:
    print(f"{PREFIX} ERROR: {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def repo_root() -> Path:
    """Return current working directory — the target project root."""
    return Path.cwd()


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def registry_path() -> Path:
    return script_dir().parent / "config" / "integrations-registry.yaml"


def project_yaml_path() -> Path:
    return repo_root() / ".meta-config" / "project.yaml"


def state_path() -> Path:
    return repo_root() / ".meta-config" / ".integrations-state.json"


def pending_marker_path() -> Path:
    return repo_root() / ".claude" / "pending-integrations.json"


# ---------------------------------------------------------------------------
# project.yaml loading (PyYAML + minimal fallback)
# ---------------------------------------------------------------------------

def load_project_config(path: Path) -> dict:
    """Load .meta-config/project.yaml. Returns {} when missing."""
    if not path.exists():
        return {}
    if _YAML_AVAILABLE:
        try:
            with path.open(encoding="utf-8") as f:
                data = _yaml.safe_load(f) or {}
        except _yaml.YAMLError as e:
            warn(f"failed to parse {path}: {e}")
            return {}
        if isinstance(data, dict):
            return data
        return {}
    # Minimal fallback: only extract integrations.<name>.enabled and
    # integrations.<name>.<key>: <value>.
    return _parse_project_minimal(path)


def _parse_project_minimal(path: Path) -> dict:
    """Tiny fallback parser. Best-effort, sufficient for integrations block."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    integrations: dict = {}
    in_block = False
    current_name: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if indent == 0:
            in_block = stripped.startswith("integrations:")
            current_name = None
            continue
        if not in_block:
            continue
        if indent == 2 and stripped.endswith(":"):
            current_name = stripped[:-1].strip()
            integrations.setdefault(current_name, {})
            continue
        if current_name and indent >= 4 and ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if value.lower() in ("true", "false"):
                integrations[current_name][key] = (value.lower() == "true")
            elif value:
                integrations[current_name][key] = value.strip('"').strip("'")
    return {"integrations": integrations}


# ---------------------------------------------------------------------------
# State file
# ---------------------------------------------------------------------------

STATE_VERSION = 1


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"version": STATE_VERSION, "integrations": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        warn(f"state file unreadable, starting fresh: {e}")
        return {"version": STATE_VERSION, "integrations": {}}
    if not isinstance(data, dict):
        return {"version": STATE_VERSION, "integrations": {}}
    data.setdefault("version", STATE_VERSION)
    if not isinstance(data.get("integrations"), dict):
        data["integrations"] = {}
    return data


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Subprocess helper
# ---------------------------------------------------------------------------

def run_cmd(cmd: list[str], cwd: Path | None = None, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a subprocess. Returns CompletedProcess; never raises on non-zero."""
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=capture,
        text=True,
        check=False,
    )


def which(binary: str) -> str | None:
    return shutil.which(binary)


# ---------------------------------------------------------------------------
# Installer selection (uv -> pip fallback)
# ---------------------------------------------------------------------------

def build_install_cmd(installer: str, package: str) -> tuple[list[str], str]:
    """Return (command, chosen_installer).

    chosen_installer is the effective installer after fallback logic
    so that callers can log accurately.
    """
    if installer == "uv":
        if which("uv"):
            # Project env install, not `uv tool install`.
            return (["uv", "pip", "install", package], "uv")
        warn("uv requested but not on PATH — falling back to pip")
        return ([sys.executable, "-m", "pip", "install", package], "pip (fallback)")
    if installer == "pip":
        return ([sys.executable, "-m", "pip", "install", package], "pip")
    # Unknown installer -> pip default with warning
    warn(f"unknown installer '{installer}', defaulting to pip")
    return ([sys.executable, "-m", "pip", "install", package], "pip")


# ---------------------------------------------------------------------------
# Lifecycle command helpers
# ---------------------------------------------------------------------------

def _placeholder_substitute(value: str, target_root: Path) -> str:
    """Substitute {{TARGET_ROOT}} (and similar) placeholders in lifecycle args."""
    return value.replace("{{TARGET_ROOT}}", str(target_root))


def resolve_lifecycle_cmd(cmd_template: list, target_root: Path) -> list[str]:
    """Resolve placeholders in a lifecycle command template into a flat list."""
    resolved: list[str] = []
    for token in cmd_template or []:
        token_str = str(token)
        resolved.append(_placeholder_substitute(token_str, target_root))
    return resolved


def append_indexing_options(base_cmd: list[str], entry: dict) -> list[str]:
    """Append CLI args derived from maps_to_arg for the index command.

    Reads option schema from registry entry (entry["options"]) and looks up
    the merged user value (which is also on entry, since resolve_enabled_
    integrations did a shallow merge).
    """
    out = list(base_cmd)
    options_schema = entry.get("options")
    if not isinstance(options_schema, dict):
        return out
    for opt_name, spec in options_schema.items():
        if not isinstance(spec, dict):
            continue
        arg_name = spec.get("maps_to_arg")
        if not arg_name:
            continue
        # Prefer the user-supplied value (merged into entry), fall back to default.
        value = entry.get(opt_name, spec.get("default"))
        if value is None:
            continue
        # Skip when user explicitly set value equal to default? No — be explicit.
        if isinstance(value, list):
            if not value:
                continue
            out.append(str(arg_name))
            out.extend(str(v) for v in value)
        elif isinstance(value, bool):
            if value:
                out.append(str(arg_name))
        else:
            out.append(str(arg_name))
            out.append(str(value))
    return out


# ---------------------------------------------------------------------------
# Single integration lifecycle steps
# ---------------------------------------------------------------------------

def healthcheck(name: str, entry: dict) -> bool:
    """Run the registry-defined healthcheck command.

    Returns True iff the command exits with 0.
    """
    lifecycle = entry.get("lifecycle") or {}
    cmd_template = lifecycle.get("healthcheck")
    if not isinstance(cmd_template, list) or not cmd_template:
        # No healthcheck declared — be conservative and treat as "unknown",
        # which the caller interprets as "not installed".
        return False
    cmd = resolve_lifecycle_cmd(cmd_template, repo_root())
    if not which(cmd[0]):
        return False
    result = run_cmd(cmd, capture=True)
    return result.returncode == 0


def do_install(name: str, entry: dict) -> bool:
    package = entry.get("package")
    if not package:
        error(f"{name}: registry entry has no 'package' — cannot install")
        return False
    installer = str(entry.get("installer", "pip"))
    cmd, effective = build_install_cmd(installer, str(package))
    info(f"{name}: not installed — installing {package} via {effective}...")
    info(f"running: {' '.join(str(a) for a in cmd)}")
    result = run_cmd(cmd, capture=True)
    if result.returncode != 0:
        error(f"{name}: install failed (exit {result.returncode})")
        if result.stderr:
            error(f"stderr: {result.stderr}")
        return False
    info(f"{name}: installed OK")
    return True


def do_init(name: str, entry: dict) -> bool:
    lifecycle = entry.get("lifecycle") or {}
    cmd_template = lifecycle.get("init")
    if not isinstance(cmd_template, list) or not cmd_template:
        info(f"{name}: no init step declared — skipping")
        return True
    cmd = resolve_lifecycle_cmd(cmd_template, repo_root())
    info(f"{name}: running init...")
    info(f"running: {' '.join(str(a) for a in cmd)}")
    result = run_cmd(cmd, capture=True)
    if result.returncode != 0:
        error(f"{name}: init failed (exit {result.returncode})")
        if result.stderr:
            error(f"stderr: {result.stderr}")
        return False
    return True


def do_index(name: str, entry: dict) -> bool:
    lifecycle = entry.get("lifecycle") or {}
    cmd_template = lifecycle.get("index")
    if not isinstance(cmd_template, list) or not cmd_template:
        info(f"{name}: no index step declared — skipping")
        return True
    base_cmd = resolve_lifecycle_cmd(cmd_template, repo_root())
    cmd = append_indexing_options(base_cmd, entry)
    info(f"{name}: indexing...")
    info(f"running: {' '.join(str(a) for a in cmd)}")
    result = run_cmd(cmd, capture=True)
    if result.returncode != 0:
        error(f"{name}: index failed (exit {result.returncode})")
        if result.stderr:
            error(f"stderr: {result.stderr}")
        return False
    return True


def mcp_healthcheck(name: str, entry: dict) -> bool:
    """Verify the MCP command binary is callable.

    We do not actually speak the MCP protocol here — we only verify that
    the configured command's first token resolves on PATH. The registry's
    lifecycle.healthcheck command serves as the deeper sanity check and
    has already been validated.
    """
    mcp = entry.get("mcp")
    if not isinstance(mcp, dict):
        return True
    command = mcp.get("command")
    if not command:
        return True
    first = command[0] if isinstance(command, list) else str(command)
    if not which(str(first)):
        error(f"{name}: MCP command binary '{first}' not found on PATH")
        return False
    info(f"{name}: healthcheck OK")
    return True


# ---------------------------------------------------------------------------
# Confirmation
# ---------------------------------------------------------------------------

def ask_confirm(plan_lines: list[str]) -> bool:
    if not plan_lines:
        return True
    info("Planned actions:")
    for line in plan_lines:
        print(f"  - {line}")
    try:
        answer = input(f"{PREFIX} Proceed? [y/N]: ").strip().lower()
    except EOFError:
        return False
    return answer in ("y", "yes")


# ---------------------------------------------------------------------------
# Per-integration orchestration
# ---------------------------------------------------------------------------

def process_integration(
    name: str,
    entry: dict,
    state: dict,
    mode_reindex: bool,
    mode_check: bool,
) -> bool:
    """Drive a single integration through its lifecycle.

    Returns True on success (or no-op in --check when healthcheck passes).
    """
    info(f"Checking {name}...")
    integ_state = state["integrations"].setdefault(name, {})

    installed = healthcheck(name, entry)

    if mode_check:
        if installed:
            info(f"{name}: healthcheck OK")
            return True
        error(f"{name}: not installed / not healthy")
        return False

    if mode_reindex:
        if not installed:
            error(f"{name}: cannot reindex — not installed")
            return False
        ok = do_index(name, entry)
        if ok:
            integ_state["indexed"] = True
            integ_state["indexed_at"] = now_iso()
        return ok

    # Full lifecycle
    if not installed:
        if not do_install(name, entry):
            integ_state["installed"] = False
            return False
        integ_state["installed"] = True
        integ_state["package"] = entry.get("package", "")
        integ_state["installed_at"] = now_iso()
    else:
        integ_state["installed"] = True
        integ_state.setdefault("package", entry.get("package", ""))
        integ_state.setdefault("installed_at", now_iso())
        info(f"{name}: already installed — skipping install")

    if not integ_state.get("initialized"):
        if not do_init(name, entry):
            return False
        integ_state["initialized"] = True
        integ_state["initialized_at"] = now_iso()
    else:
        info(f"{name}: already initialized — skipping init")

    if not do_index(name, entry):
        return False
    integ_state["indexed"] = True
    integ_state["indexed_at"] = now_iso()

    if not mcp_healthcheck(name, entry):
        return False

    return True


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------

def build_plan(enabled: dict, state: dict, mode_reindex: bool) -> list[str]:
    """Build a list of human-readable plan lines for the confirmation prompt."""
    lines: list[str] = []
    for name, entry in enabled.items():
        integ_state = state["integrations"].get(name, {})
        installed = healthcheck(name, entry)
        if mode_reindex:
            lines.append(f"{name}: reindex")
            continue
        steps: list[str] = []
        if not installed:
            steps.append(f"install {entry.get('package', '?')} via {entry.get('installer', 'pip')}")
        if not integ_state.get("initialized"):
            steps.append("init")
        steps.append("index")
        steps.append("mcp-healthcheck")
        lines.append(f"{name}: " + " -> ".join(steps))
    return lines


# ---------------------------------------------------------------------------
# Argparse
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="init-integrations.py",
        description="Install, initialize and index project-enabled integrations.",
    )
    p.add_argument("--yes", action="store_true", help="Skip confirmation prompt.")
    p.add_argument("--reindex", action="store_true", help="Only re-index, do not (re)install or (re)init.")
    p.add_argument("--check", action="store_true", help="Read-only healthcheck. No side effects.")
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.reindex and args.check:
        error("--reindex and --check are mutually exclusive")
        return 2

    reg = load_integrations_registry(registry_path())
    proj = load_project_config(project_yaml_path())
    enabled = resolve_enabled_integrations(reg, proj)

    if not enabled:
        info("No enabled integrations. Nothing to do.")
        # Clear any stale pending marker
        write_pending_marker(pending_marker_path(), [])
        return 0

    state = load_state(state_path())

    plan = build_plan(enabled, state, args.reindex)

    # Confirmation gate — only for non-check, non-yes mode
    if not args.check and not args.yes:
        if not ask_confirm(plan):
            info("Aborted by user.")
            return 1

    successes: list[str] = []
    failures: list[str] = []
    pending: list[str] = []

    for name, entry in enabled.items():
        try:
            ok = process_integration(
                name, entry, state,
                mode_reindex=args.reindex,
                mode_check=args.check,
            )
        except Exception as e:  # noqa: BLE001 — top-level guard
            error(f"{name}: unexpected error: {e}")
            ok = False
        if ok:
            successes.append(name)
        else:
            failures.append(name)
            if not args.check:
                pending.append(name)

    # Persist state (skip in --check to keep it strictly read-only)
    if not args.check:
        save_state(state_path(), state)
        write_pending_marker(pending_marker_path(), pending)

    # Final summary
    if args.check:
        if failures:
            info(f"{len(failures)} integration(s) NOT healthy: {', '.join(failures)}")
            return 1
        info(f"All {len(successes)} integration(s) healthy.")
        return 0

    if failures:
        info(f"Done with errors. OK: {len(successes)}, failed: {len(failures)} ({', '.join(failures)})")
        return 1
    info(f"Done. {len(successes)} integration(s) ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
