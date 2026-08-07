"""I/O helpers for loading YAML/JSON config files."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


class SyncError(Exception):
    """Fatal sync error — sync cannot continue safely."""

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
                print(f"WARNING: PyYAML not installed, skipping {path.name}.", file=sys.stderr)
                continue
            with path.open(encoding="utf-8") as f:
                return _yaml.safe_load(f) or {}, path
        else:
            with path.open(encoding="utf-8") as f:
                return json.load(f), path
    return {}, preferred  # none found — return empty + preferred path


def read_json_lenient(path: Path) -> dict | None:
    """Read a JSON file, tolerating JSONC-style // comments, trailing commas and a BOM.

    Settings files like opencode.json(c) are JSONC: full-line and inline
    // comments plus trailing commas left behind after commenting out entries.
    Returns None when the file cannot be parsed even after cleanup.
    """
    text = path.read_text(encoding="utf-8-sig")
    stripped = re.sub(r'(?m)^\s*//.*$', '', text)
    # Inline comments: require whitespace before // so URLs ("https://...") survive
    stripped = re.sub(r'(?m)\s+//[^"\n]*$', '', stripped)
    stripped = re.sub(r',\s*([}\]])', r'\1', stripped)
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        return None


def _write_yaml(path: Path, data: dict) -> None:
    """Write data as YAML with consistent formatting."""
    with path.open("w", encoding="utf-8") as f:
        _yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                   sort_keys=False, indent=2)


def content_hash(text: str) -> str:
    """Return a short SHA-256 hex digest of text (first 16 chars)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def is_unchanged(path: Path, new_content: str) -> bool:
    """Return True when path exists and already contains new_content."""
    if not path.exists():
        return False
    return path.read_text(encoding="utf-8") == new_content


def write_checked(
    path: Path,
    content: str,
    log: "SyncLog",  # noqa: F821
    rel_label: str,
    force: bool = False,
    allow_secrets: bool = False,
    config: dict | None = None,
    dry_run: bool = False,
) -> bool:
    """Write content to path unless it is already identical (incremental sync).

    Scans for potential secrets before writing.
    - allow_secrets=False (default): raises SyncError when a secret is detected.
      Use this for committed files — secrets must never land in version control.
    - allow_secrets=True: emits a warning only (use for gitignored local files).

    Set allow-committed-secrets: true in project.yaml to override for a project
    (not recommended — prefer ${ENV_VAR} references in committed configs).

    config: optional project config dict — extends secret detection with
            security.secret-patterns from project.yaml.

    dry_run: when True, perform only the change detection — skip the secret
             scan and the actual write. Returns True when the file *would* be
             written (content differs / missing), False when unchanged. This
             lets callers report accurate action/skip counts in dry-run mode
             (used by ``sync.py --dry-run --check`` for CI).

    Returns True when the file was written, False when skipped as unchanged.
    """
    if not force and is_unchanged(path, content):
        return False
    if dry_run:
        # Change detected but do not touch the filesystem (or scan secrets —
        # dry-run must never fail on secrets it would not write).
        return True
    from .secrets import scan_for_secrets
    findings = scan_for_secrets(content, config=config)
    if findings:
        if not allow_secrets:
            raise SyncError(
                f"Secret detected in committed file '{rel_label}': "
                + ", ".join(findings)
                + "\n  Use allow-committed-secrets: true in project.yaml to bypass (not recommended)."
            )
        for finding in findings:
            log.warning(f"potential secret in {rel_label}: {finding} — verify before committing")
    path.write_text(content, encoding="utf-8")
    return True


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
