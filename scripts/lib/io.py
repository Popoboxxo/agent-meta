"""I/O helpers for loading YAML/JSON config files."""

import json
import sys
from pathlib import Path

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


def _load_yaml_or_json(*paths: Path) -> tuple[dict, Path]:
    """Load the first existing file from paths (YAML or JSON). Returns (data, used_path).

    Accepts 1..N paths tried in order — first existing file wins.
    Preferred path (for "not found" return) is always paths[0].
    """
    preferred = paths[0]
    for path in paths:
        if not path.exists():
            continue
        if path.suffix.lower() in (".yaml", ".yml"):
            if not _YAML_AVAILABLE:
                print(f"ERROR: PyYAML not installed but {path.name} requires it. "
                      f"Run: pip install pyyaml", file=sys.stderr)
                sys.exit(1)
            with path.open(encoding="utf-8") as f:
                return _yaml.safe_load(f) or {}, path
        else:
            with path.open(encoding="utf-8") as f:
                return json.load(f), path
    return {}, preferred  # none found — return empty + preferred path


def _write_yaml(path: Path, data: dict) -> None:
    """Write data as YAML with consistent formatting."""
    with path.open("w", encoding="utf-8") as f:
        _yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                   sort_keys=False, indent=2)
