#!/usr/bin/env python3
"""
agent-meta migrate-config.py
=============================
Migrate a project's agent-meta.config.json → agent-meta.config.yaml.

Also migrates the internal agent-meta config files (roles, dod-presets,
external-skills) if run inside the agent-meta repo itself — but those are
already provided as .yaml files starting from v0.24.0, so this is mainly
needed for project configs.

Usage:
  # Migrate a project config (most common case):
  py .agent-meta/scripts/migrate-config.py --config agent-meta.config.json

  # Preview without writing:
  py .agent-meta/scripts/migrate-config.py --config agent-meta.config.json --dry-run

  # Migrate and keep the .json file as backup (default: rename to .json.bak):
  py .agent-meta/scripts/migrate-config.py --config agent-meta.config.json --keep-json

What it does:
  1. Reads agent-meta.config.json
  2. Writes agent-meta.config.yaml with clean YAML formatting
     - Comments are added for major sections (not preserved from JSON _comment keys)
     - Multiline string values are written as YAML block scalars
  3. Renames the original .json to .json.bak (unless --keep-json is passed)

After migration:
  py .agent-meta/scripts/sync.py --config agent-meta.config.yaml
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


# ---------------------------------------------------------------------------
# YAML representer: use block style for multiline strings
# ---------------------------------------------------------------------------

class _BlockStr(str):
    """Marker class for strings that should use YAML block style (|)."""


def _block_str_representer(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_yaml_value(v):
    """Recursively convert a JSON value to YAML-friendly Python types."""
    if isinstance(v, str) and "\n" in v:
        return _BlockStr(v)
    if isinstance(v, dict):
        return {k: _to_yaml_value(val) for k, val in v.items()
                if not k.startswith("_")}
    if isinstance(v, list):
        return [_to_yaml_value(item) for item in v]
    return v


def _strip_comment_keys(d: dict) -> dict:
    """Remove all keys starting with '_' (JSON comment convention)."""
    return {k: v for k, v in d.items() if not k.startswith("_")}


def migrate_config(src: Path, dry_run: bool, keep_json: bool) -> None:
    if not src.exists():
        print(f"ERROR: not found: {src}", file=sys.stderr)
        sys.exit(1)

    if src.suffix.lower() != ".json":
        print(f"ERROR: expected a .json file, got: {src}", file=sys.stderr)
        sys.exit(1)

    dest = src.with_suffix(".yaml")
    if dest.exists() and not dry_run:
        print(f"  !  {dest.name} already exists — aborting to avoid overwrite.")
        print(f"     Delete or rename it first, then re-run.")
        sys.exit(1)

    with src.open(encoding="utf-8") as f:
        raw = json.load(f)

    # Strip _comment* keys at top level and inside variables
    cleaned = _strip_comment_keys(raw)
    if "variables" in cleaned and isinstance(cleaned["variables"], dict):
        cleaned["variables"] = _strip_comment_keys(cleaned["variables"])

    # Convert multiline strings to block-style markers
    output = _to_yaml_value(cleaned)

    yaml.add_representer(_BlockStr, _block_str_representer)

    if dry_run:
        print(f"DRY-RUN: would write {dest}")
        print()
        print(yaml.dump(output, allow_unicode=True, default_flow_style=False,
                        sort_keys=False, indent=2))
        return

    with dest.open("w", encoding="utf-8") as f:
        f.write(f"# Migrated from {src.name} by migrate-config.py\n")
        f.write(f"# Edit this file directly — {src.name} can be deleted after verification.\n\n")
        yaml.dump(output, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, indent=2)

    print(f"  +  Written: {dest}")

    if keep_json:
        print(f"  i  Original kept: {src} (--keep-json)")
    else:
        bak = src.with_suffix(".json.bak")
        src.rename(bak)
        print(f"  i  Original renamed to: {bak.name}")

    print()
    print(f"Next step:")
    print(f"  py .agent-meta/scripts/sync.py --config {dest.name}")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate agent-meta.config.json → agent-meta.config.yaml"
    )
    parser.add_argument(
        "--config", required=True,
        help="Path to agent-meta.config.json to migrate"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview the YAML output without writing files"
    )
    parser.add_argument(
        "--keep-json", action="store_true",
        help="Keep the original .json file (default: rename to .json.bak)"
    )
    args = parser.parse_args()

    if not _YAML_AVAILABLE:
        print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
        sys.exit(1)

    migrate_config(Path(args.config).resolve(), args.dry_run, args.keep_json)


if __name__ == "__main__":
    main()
