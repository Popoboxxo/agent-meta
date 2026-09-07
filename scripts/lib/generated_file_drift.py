"""Generated-file drift detection: warn when a sync.py-owned file
(anything tracked via .agent-meta-managed) was manually edited since the
last sync. Warn-only for this phase -- write behavior is unaffected.

Split into two halves, mirroring context.py's context-hashes.json pattern:
- scan_generated_file_drift() (Task 2): pure, compares current file
  content hashes against the stored baseline, called BEFORE the
  per-provider write stage so it sees pre-overwrite state.
- capture_generated_file_hashes() (Task 3): writes a fresh baseline from
  the now-written files, called AFTER every writer has run.

Spec: docs/superpowers/specs/2026-09-05-generated-file-drift-detection-design.md
"""
from __future__ import annotations

import fnmatch
from pathlib import Path

from .io import load_json_file, load_yaml_file, write_atomic

GENERATED_FILE_HASHES_DIR = ".meta-config"
GENERATED_FILE_HASHES_FILE = "generated-file-hashes.json"
DRIFT_ALLOWLIST_FILE = "drift-allowlist.yaml"


def _hashes_path(project_root: Path) -> Path:
    return project_root / GENERATED_FILE_HASHES_DIR / GENERATED_FILE_HASHES_FILE


def _load_hashes(project_root: Path) -> dict[str, str]:
    """Read the hash-store sidecar; {} if absent or malformed (fail-soft,
    same contract as context.py's _load_context_hashes)."""
    data = load_json_file(_hashes_path(project_root), on_error="default", default={})
    hashes = data.get("hashes") if isinstance(data, dict) else None
    return hashes if isinstance(hashes, dict) else {}


def _save_hashes(project_root: Path, hashes: dict[str, str], dry_run: bool) -> None:
    """Write the hash-store sidecar (no-op in dry_run)."""
    if dry_run:
        return
    path = _hashes_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    import json
    payload = {"version": 1, "hashes": hashes}
    write_atomic(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _allowlist_path(project_root: Path) -> Path:
    return project_root / GENERATED_FILE_HASHES_DIR / DRIFT_ALLOWLIST_FILE


def _load_allowlist_patterns(project_root: Path) -> list[str]:
    """Read .meta-config/drift-allowlist.yaml's `allow-edits` list; []
    if absent or malformed (fail-soft, matching every other optional
    config file in this repo)."""
    data = load_yaml_file(_allowlist_path(project_root), on_error="default", default={})
    patterns = data.get("allow-edits") if isinstance(data, dict) else None
    return [p for p in patterns if isinstance(p, str)] if isinstance(patterns, list) else []


def is_allowlisted(rel_path: str, patterns: list[str]) -> bool:
    """True when rel_path matches any glob pattern in patterns (fnmatch semantics)."""
    return any(fnmatch.fnmatch(rel_path, pattern) for pattern in patterns)


def is_drift_detection_enabled(config: dict) -> bool:
    """True unless project.yaml explicitly sets drift-detection.enabled: false."""
    return bool(config.get("drift-detection", {}).get("enabled", True))
