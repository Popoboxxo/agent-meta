"""Generated-file drift detection: warn when a sync.py-owned file
(anything tracked via .agent-meta-managed) was manually edited since the
last sync. Warn-only for this phase -- write behavior is unaffected.

Split into two halves, mirroring context.py's context-hashes.json pattern:
- scan_generated_file_drift() (Task 2): pure, compares current file
  content hashes against the stored baseline, called BEFORE the
  per-provider write stage so it sees pre-overwrite state.
- capture_generated_file_hashes() (Task 3): writes a fresh baseline from
  the now-written files, called AFTER every writer has run.

Spec: docs/superpowers/specs/2026-09-07-generated-file-drift-detection-design.md
"""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path

from .deactivation import get_active_providers
from .io import content_hash, load_json_file, load_yaml_file, safe_path, write_atomic
from .pipelines import resolve_pipeline_details_dir
from .rule_index import read_managed_index

GENERATED_FILE_HASHES_DIR = ".meta-config"
GENERATED_FILE_HASHES_FILE = "generated-file-hashes.json"
DRIFT_ALLOWLIST_FILE = "drift-allowlist.yaml"
# Task 6 (platform-project-defaults feature): the resolved platform-preset
# snapshot is a generated file too but lives outside every provider's
# managed-index tree (_iter_managed_files only walks agents_dir/rules_dir/
# hooks_dir/commands_dir/skills_dir/pipeline_details_dir) -- registered
# explicitly here rather than teaching _iter_managed_files a project-root-
# level, non-per-provider file shape for a single caller.
PLATFORM_DEFAULTS_RESOLVED_REL = ".meta-config/platform-defaults.resolved.yaml"


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


def _managed_names(dir_path: Path, *extra_index_names: str) -> set[str]:
    """Union of every managed-index file's entries for dir_path.

    A directory can carry more than one index (rules/ has
    .agent-meta-managed, -mcp, -tools -- one per writer, issue #478/#613);
    extra_index_names lists the sidecar suffixes beyond the base
    .agent-meta-managed.
    """
    names = read_managed_index(dir_path / ".agent-meta-managed")
    for suffix in extra_index_names:
        names |= read_managed_index(dir_path / f".agent-meta-managed-{suffix}")
    return names


def _iter_managed_files(agent_meta_root: Path, project_root: Path, provider: str, pc: dict) -> list[Path]:
    """Absolute paths of every file this provider's writers track via a
    .agent-meta-managed index (or its -mcp/-tools sidecars), across
    agents/rules/hooks(+lib+release-gates)/commands/skills/pipeline-details.

    Default literal fallbacks (".claude/hooks" etc.) mirror the same
    established pattern in scan_injection_drift()
    (scripts/lib/external_tools_drift.py) -- correct today because only
    Claude omits these keys from ai-providers.yaml while having the
    capability; any provider without the capability flag never reaches
    the fallback at all.
    """
    files: list[Path] = []

    dir_specs: list[tuple[str, list[str]]] = [
        (pc.get("skills_dir", ".claude/skills"), []),
        (pc.get("agents_dir", ".claude/agents"), []),
    ]
    if pc.get("has_hooks", False):
        dir_specs.append((pc.get("hooks_dir", ".claude/hooks"), []))
    if pc.get("has_rules", False):
        dir_specs.append((pc.get("rules_dir", ".claude/rules"), ["mcp", "tools"]))
    if pc.get("has_commands", False):
        dir_specs.append((pc.get("commands_dir", ".claude/commands"), []))
    dir_specs.append((resolve_pipeline_details_dir(pc, provider), []))

    for dir_rel, extra_index_names in dir_specs:
        dir_path = project_root / dir_rel
        if not dir_path.is_dir():
            continue
        for name in sorted(_managed_names(dir_path, *extra_index_names)):
            candidate = safe_path(dir_path, name)
            if candidate.is_file():
                files.append(candidate)
            elif candidate.is_dir():
                # Skill-style index entries name a whole subdirectory (e.g.
                # .claude/skills/.agent-meta-managed lists "a2a-delegation-gates",
                # a directory containing SKILL.md and possibly further
                # reference files) rather than a single file -- collect
                # everything inside recursively so drift is caught for all
                # of it, today and as skills grow extra files.
                files.extend(sorted(p for p in candidate.rglob("*") if p.is_file()))
        # Nested self-managed subdirectories (hooks/lib/, hooks/release-gates/,
        # issue #558) carry their OWN .agent-meta-managed index -- recurse
        # one level to pick those up too (mirrors scan_injection_drift's
        # "child.is_dir() and (child / '.agent-meta-managed').exists()" check).
        for child in sorted(dir_path.iterdir()):
            if child.is_dir() and (child / ".agent-meta-managed").exists():
                for name in sorted(_managed_names(child)):
                    nested_candidate = safe_path(child, name)
                    if nested_candidate.is_file():
                        files.append(nested_candidate)

    return files


def scan_generated_file_drift(
    agent_meta_root: Path, project_root: Path, config: dict, provider_config: dict,
) -> list[dict]:
    """Compare every active provider's managed files against the stored
    hash baseline. Pure -- no writes, no warnings emitted (the caller,
    the sync_pipeline stage, turns findings into log.warning() calls).

    A file with no stored hash yet (first sync, or newly added to a
    managed index) is never a finding -- there is nothing to compare
    against yet.
    """
    stored_hashes = _load_hashes(project_root)
    allowlist = _load_allowlist_patterns(project_root)
    active_providers = set(get_active_providers(config, provider_config))

    findings: list[dict] = []
    for provider, pc in provider_config.items():
        if provider not in active_providers:
            continue
        for abs_path in _iter_managed_files(agent_meta_root, project_root, provider, pc):
            rel_path = abs_path.relative_to(project_root).as_posix()
            stored = stored_hashes.get(rel_path)
            if stored is None:
                continue
            current = content_hash(abs_path.read_text(encoding="utf-8"))
            if current == stored:
                continue
            if is_allowlisted(rel_path, allowlist):
                continue
            findings.append({"path": rel_path, "provider": provider})

    resolved_path = project_root / PLATFORM_DEFAULTS_RESOLVED_REL
    stored_resolved = stored_hashes.get(PLATFORM_DEFAULTS_RESOLVED_REL)
    if stored_resolved is not None and resolved_path.is_file():
        current_resolved = content_hash(resolved_path.read_text(encoding="utf-8"))
        if current_resolved != stored_resolved and not is_allowlisted(PLATFORM_DEFAULTS_RESOLVED_REL, allowlist):
            findings.append({"path": PLATFORM_DEFAULTS_RESOLVED_REL, "provider": "platform-defaults"})

    return findings


def capture_generated_file_hashes(
    agent_meta_root: Path, project_root: Path, config: dict, provider_config: dict, dry_run: bool,
) -> None:
    """Recompute and persist the complete hash baseline from the CURRENT
    on-disk state of every active provider's managed files. Called once,
    at the very end of the sync pipeline, after every writer has run --
    the on-disk content at this point is exactly what the next sync's
    scan_generated_file_drift() call should compare against.
    """
    active_providers = set(get_active_providers(config, provider_config))
    hashes: dict[str, str] = {}
    for provider, pc in provider_config.items():
        if provider not in active_providers:
            continue
        for abs_path in _iter_managed_files(agent_meta_root, project_root, provider, pc):
            rel_path = abs_path.relative_to(project_root).as_posix()
            hashes[rel_path] = content_hash(abs_path.read_text(encoding="utf-8"))
    resolved_path = project_root / PLATFORM_DEFAULTS_RESOLVED_REL
    if resolved_path.is_file():
        hashes[PLATFORM_DEFAULTS_RESOLVED_REL] = content_hash(resolved_path.read_text(encoding="utf-8"))
    _save_hashes(project_root, hashes, dry_run)
