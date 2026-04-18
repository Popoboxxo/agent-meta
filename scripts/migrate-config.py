#!/usr/bin/env python3
"""
agent-meta migrate-config.py
=============================
Two migration modes:

  1. JSON -> YAML  (legacy, still supported):
     Migrate a project's agent-meta.config.json -> agent-meta.config.yaml.

  2. flat-root -> .meta-config/  (new, v0.26+):
     Move agent-meta.config.yaml from the project root into .meta-config/project.yaml.
     This is the standard layout introduced in v0.26.0.

Usage:
  # JSON -> YAML (legacy):
  py .agent-meta/scripts/migrate-config.py --config agent-meta.config.json

  # flat-root -> .meta-config/ (recommended for all existing projects):
  py .agent-meta/scripts/migrate-config.py --to-meta-config
  py .agent-meta/scripts/migrate-config.py --to-meta-config --dry-run

  # Preview JSON migration without writing:
  py .agent-meta/scripts/migrate-config.py --config agent-meta.config.json --dry-run

  # JSON migration, keep .json file as backup:
  py .agent-meta/scripts/migrate-config.py --config agent-meta.config.json --keep-json

What --to-meta-config does:
  1. Creates .meta-config/ directory
  2. Moves agent-meta.config.yaml -> .meta-config/project.yaml
  3. Adds .meta-config/ to .gitignore (only the local-config entries, not the dir itself)
  4. Prints next-step instructions

After migration:
  py .agent-meta/scripts/sync.py --config .meta-config/project.yaml
  # or simply (auto-detect):
  py .agent-meta/scripts/sync.py
"""

import argparse
import json
import shutil
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


# ---------------------------------------------------------------------------
# Mode 1: JSON -> YAML
# ---------------------------------------------------------------------------

def migrate_json_to_yaml(src: Path, dry_run: bool, keep_json: bool) -> None:
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

    cleaned = _strip_comment_keys(raw)
    if "variables" in cleaned and isinstance(cleaned["variables"], dict):
        cleaned["variables"] = _strip_comment_keys(cleaned["variables"])

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
    print(f"Next step — move to standard layout:")
    print(f"  py .agent-meta/scripts/migrate-config.py --to-meta-config")


# ---------------------------------------------------------------------------
# Mode 2: flat-root -> .meta-config/
# ---------------------------------------------------------------------------

# Legacy source candidates (tried in order)
_LEGACY_CONFIG_CANDIDATES = [
    "agent-meta.config.yaml",
    "agent-meta.config.yml",
]


def migrate_to_meta_config(project_root: Path, dry_run: bool) -> None:
    """Move agent-meta.config.yaml -> .meta-config/project.yaml."""

    # Find legacy source
    src: Path | None = None
    for candidate in _LEGACY_CONFIG_CANDIDATES:
        p = project_root / candidate
        if p.exists():
            src = p
            break

    if src is None:
        # Already migrated?
        already = project_root / ".meta-config" / "project.yaml"
        if already.exists():
            print(f"  i  Already migrated: .meta-config/project.yaml exists.")
            print(f"     Nothing to do.")
            return
        print(f"  !  No legacy config found in {project_root}", file=sys.stderr)
        print(f"     Expected one of: {', '.join(_LEGACY_CONFIG_CANDIDATES)}", file=sys.stderr)
        sys.exit(1)

    dest_dir = project_root / ".meta-config"
    dest = dest_dir / "project.yaml"

    print(f"  >  Migrate: {src.name} -> .meta-config/project.yaml")

    if dest.exists():
        print(f"  !  .meta-config/project.yaml already exists — aborting.")
        print(f"     Delete it first if you want to re-run the migration.")
        sys.exit(1)

    if dry_run:
        print(f"DRY-RUN: would create {dest_dir}/")
        print(f"DRY-RUN: would move   {src} -> {dest}")
        print()
        print("Next steps would be:")
        _print_next_steps()
        return

    dest_dir.mkdir(exist_ok=True)
    shutil.move(str(src), str(dest))
    print(f"  +  Created: .meta-config/")
    print(f"  +  Moved:   {src.name} -> .meta-config/project.yaml")

    # Create placeholder .meta-config/skills.yaml if project had external-skills block
    _maybe_create_skills_placeholder(dest, dest_dir)

    print()
    _print_next_steps()


def _maybe_create_skills_placeholder(project_yaml: Path, dest_dir: Path) -> None:
    """If project.yaml contains an external-skills block, hint about skills.yaml."""
    try:
        if not _YAML_AVAILABLE:
            return
        with project_yaml.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if "external-skills" in data:
            print(f"  i  external-skills block found in project.yaml.")
            print(f"     You can optionally move it to .meta-config/skills.yaml")
            print(f"     (not required — keeping it in project.yaml works fine)")
    except Exception:
        pass


def _print_next_steps() -> None:
    print("Next steps:")
    print("  1. Run sync with new config location:")
    print("       py .agent-meta/scripts/sync.py --config .meta-config/project.yaml")
    print("     or simply (auto-detect):")
    print("       py .agent-meta/scripts/sync.py")
    print()
    print("  2. Commit the change:")
    print("       git add .meta-config/ agent-meta.config.yaml")
    print("       git commit -m \"chore: migrate config to .meta-config/project.yaml\"")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Migrate agent-meta config: JSON->YAML or flat-root->.meta-config/"
    )
    parser.add_argument(
        "--config",
        help="Path to agent-meta.config.json to migrate to YAML (legacy mode)"
    )
    parser.add_argument(
        "--to-meta-config", action="store_true",
        help="Move agent-meta.config.yaml -> .meta-config/project.yaml (v0.26+ standard layout)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would be done without writing files"
    )
    parser.add_argument(
        "--keep-json", action="store_true",
        help="(JSON->YAML only) Keep the original .json file instead of renaming to .json.bak"
    )
    args = parser.parse_args()

    if not args.config and not args.to_meta_config:
        parser.print_help()
        sys.exit(1)

    if not _YAML_AVAILABLE:
        print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
        sys.exit(1)

    if args.to_meta_config:
        migrate_to_meta_config(Path.cwd(), args.dry_run)
    else:
        migrate_json_to_yaml(Path(args.config).resolve(), args.dry_run, args.keep_json)


if __name__ == "__main__":
    main()
