"""I/O helpers for loading YAML/JSON config files."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .log import SyncLog


class SyncError(Exception):
    """Fatal sync error — sync cannot continue safely."""
    pass

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _yaml = None  # type: ignore[assignment]
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
    log: SyncLog,
    rel_label: str,
    force: bool = False,
    allow_secrets: bool = False,
) -> bool:
    """Write content to path unless it is already identical (incremental sync).

    Scans for potential secrets before writing.
    - allow_secrets=False (default): raises SyncError when a secret is detected.
      Use this for committed files — secrets must never land in version control.
    - allow_secrets=True: emits a warning only (use for gitignored local files).

    Set allow-committed-secrets: true in project.yaml to override for a project
    (not recommended — prefer ${ENV_VAR} references in committed configs).

    Returns True when the file was written, False when skipped as unchanged.
    """
    if not force and is_unchanged(path, content):
        return False
    from .secrets import scan_for_secrets
    findings = scan_for_secrets(content)
    if findings:
        if not allow_secrets:
            raise SyncError(
                f"Secret detected in committed file '{rel_label}': "
                + ", ".join(findings)
                + "\n  Use allow-committed-secrets: true in project.yaml to bypass (not recommended)."
            )
        for finding in findings:
            log.warn(f"potential secret in {rel_label}: {finding} — verify before committing")
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


def clean_generated_files(
    project_root: Path,
    provider_config: dict,
    providers: list[str],
    log,
    dry_run: bool = False,
) -> dict:
    """Remove all generated output files from provider directories, then run a full sync.

    Protected paths (NEVER deleted):
      - Settings files: settings.json, opencode.json, config.yaml (per provider)
      - Local settings: settings.local.* files
      - Project extension files: 3-project/*-ext.md
      - .meta-config/ directory (everything inside it)
      - CLAUDE.md / AGENTS.md (semi-managed files)

    Returns dict with 'deleted' and 'protected' lists of relative path strings.
    """
    deleted: list[str] = []
    protected: list[str] = []

    # Build protected file set (relative to project_root)
    protected_files: set[str] = set()
    protected_dirs: set[str] = {".meta-config"}

    for provider in providers:
        pc = provider_config.get(provider, {})
        # Settings file (committed)
        sf = pc.get("settings_file")
        if sf:
            protected_files.add(sf)
        # Context file (CLAUDE.md, AGENTS.md, etc. — semi-managed)
        ctx = pc.get("context_file")
        if ctx:
            protected_files.add(ctx)
        # Extension directory contents (*-ext.md)
        ext_dir = pc.get("extension_dir")
        if ext_dir:
            protected_dirs.add(ext_dir)
        # MCP secrets file (local, should not be deleted as it may contain user secrets)
        mcp = pc.get("mcp-config", {})
        secrets_file = mcp.get("secrets-file")
        if secrets_file:
            protected_files.add(secrets_file)
        # Pending tasks file
        pending = pc.get("pending_tasks_file")
        if pending:
            protected_files.add(pending)

    def _is_protected(rel: str) -> bool:
        """Check if a relative path is protected."""
        if rel in protected_files:
            return True
        for pd in protected_dirs:
            if rel == pd or rel.startswith(pd + "/") or rel.startswith(pd + "\\"):
                return True
        # Local settings pattern: settings.local.* or *.local.*
        basename = Path(rel).name
        if ".local." in basename:
            return True
        return False

    items_to_delete: list[tuple[str, bool]] = []  # (rel_path, is_dir)

    # Map dir_key -> has_* flag for implicit directory resolution
    DIR_HAS_MAP = {
        "rules_dir": "has_rules",
        "hooks_dir": "has_hooks",
        "commands_dir": "has_commands",
        "skills_dir": "has_skills",
        "snippets_dir": "has_snippets",
    }

    def _resolve_dir(provider: str, pc: dict, dir_key: str) -> str | None:
        """Resolve a provider directory path, with fallback for implicit dirs."""
        # Explicit key takes precedence
        explicit = pc.get(dir_key)
        if explicit:
            return explicit
        # agents_dir is always explicit (all providers have it)
        if dir_key == "agents_dir":
            return None
        # Infer from has_* flag + provider naming convention
        has_key = DIR_HAS_MAP.get(dir_key)
        if has_key and pc.get(has_key, False):
            dir_name = dir_key.replace("_dir", "")
            return f".{provider.lower()}/{dir_name}"
        return None

    # Phase 1: Scan provider directories
    for provider in providers:
        pc = provider_config.get(provider, {})
        for dir_key in ("agents_dir", "rules_dir", "hooks_dir", "commands_dir",
                        "skills_dir", "snippets_dir"):
            dir_path = _resolve_dir(provider, pc, dir_key)
            if not dir_path:
                continue
            full_dir = project_root / dir_path
            if not full_dir.exists():
                continue
            for item in sorted(full_dir.iterdir()):
                rel = item.relative_to(project_root).as_posix()
                if _is_protected(rel):
                    protected.append(rel)
                    continue
                if item.is_dir():
                    items_to_delete.append((rel, True))
                else:
                    items_to_delete.append((rel, False))

    # Phase 2: Scan top-level generated files
    top_level_generated = ["sync.log"]
    for item_name in top_level_generated:
        full_path = project_root / item_name
        if full_path.exists():
            rel = item_name
            if not _is_protected(rel):
                items_to_delete.append((rel, False))

    # Phase 3: Execute deletions (files first, then directories)
    files_to_del = [(r, d) for r, d in items_to_delete if not d]
    dirs_to_del = [(r, d) for r, d in items_to_delete if d]

    for rel, _ in files_to_del:
        full_path = project_root / rel
        if dry_run:
            log.info("clean", f"would delete: {rel}")
        else:
            full_path.unlink()
            log.info("clean", f"deleted: {rel}")
        deleted.append(rel)

    for rel, _ in dirs_to_del:
        full_path = project_root / rel
        if dry_run:
            log.info("clean", f"would delete: {rel}/")
        else:
            import shutil
            shutil.rmtree(full_path)
            log.info("clean", f"deleted: {rel}/")
        deleted.append(rel)

    return {"deleted": deleted, "protected": protected}
