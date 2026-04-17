"""I/O helpers for loading YAML/JSON config files."""

import json
import sys
from pathlib import Path

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


def _load_yaml_or_json(path_yaml: Path, path_json: Path) -> tuple[dict, Path]:
    """Load YAML file if it exists, else fall back to JSON. Returns (data, used_path)."""
    if path_yaml.exists():
        if not _YAML_AVAILABLE:
            print(f"ERROR: PyYAML not installed but {path_yaml.name} requires it. "
                  f"Run: pip install pyyaml", file=sys.stderr)
            sys.exit(1)
        with path_yaml.open(encoding="utf-8") as f:
            return _yaml.safe_load(f) or {}, path_yaml
    if path_json.exists():
        with path_json.open(encoding="utf-8") as f:
            return json.load(f), path_json
    return {}, path_yaml  # neither exists — return empty + preferred path


def _write_yaml(path: Path, data: dict) -> None:
    """Write data as YAML with consistent formatting."""
    with path.open("w", encoding="utf-8") as f:
        _yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                   sort_keys=False, indent=2)
