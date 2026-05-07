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


def write_checked(path: Path, content: str, log: "SyncLog", rel_label: str) -> None:
    """Write content to path, warning if potential secrets are detected."""
    from .secrets import scan_for_secrets
    findings = scan_for_secrets(content)
    for finding in findings:
        log.warn(f"potential secret in {rel_label}: {finding} — verify before committing")
    path.write_text(content, encoding="utf-8")


def safe_path(base: Path, *parts: str) -> Path:
    """Join base with parts and validate the result stays within base.

    Raises ValueError if the resolved path escapes the base directory.
    This prevents path traversal via malicious config values (e.g. prefix='../../evil').
    """
    path = base.joinpath(*parts).resolve()
    base_resolved = base.resolve()
    try:
        path.relative_to(base_resolved)
    except ValueError:
        raise ValueError(
            f"Path traversal detected: attempted to write outside project root. "
            f"Resolved path: {path}, base: {base_resolved}"
        )
    return path
