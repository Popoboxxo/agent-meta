"""Generated-file drift detection: warn when a sync.py-owned file
(anything tracked via .agent-meta-managed) was manually edited since the
last sync, and write a timestamped `.sync-backup-<...>` sibling of every
drifted file before the writers overwrite it (issue #734). The edit is
still overwritten in place -- the backup is a safety net, not preservation.

Split into three parts, mirroring context.py's context-hashes.json pattern:
- scan_generated_file_drift(): pure, compares current file content hashes
  against the stored baseline, called BEFORE the per-provider write stage
  so it sees pre-overwrite state.
- backup_drifted_files(): writes one timestamped backup per finding from
  the pre-overwrite content, called right after the scan and before the
  warnings and the writers.
- capture_generated_file_hashes(): writes a fresh baseline from the
  now-written files, called AFTER every writer has run.

Spec: docs/superpowers/specs/2026-09-07-generated-file-drift-detection-design.md
(see its "Post-implementation update (2026-09-11, #734)" note).
"""
from __future__ import annotations

import fnmatch
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .deactivation import get_active_providers
from .io import content_hash, load_json_file, load_yaml_file, safe_path, write_atomic
from .log import SyncLog
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
    .agent-meta-managed, -mcp, -tools -- one per writer, issue
    extra_index_names lists the sidecar suffixes beyond the base
    .agent-meta-managed.
    """
    names = read_managed_index(dir_path / ".agent-meta-managed")
    for suffix in extra_index_names:
        names |= read_managed_index(dir_path / f".agent-meta-managed-{suffix}")
    return names


# `<file>.sync-backup-<YYYYmmdd-HHMMSS>` siblings written by
# backup_drifted_files(). They are ephemeral safety copies, never generated
# artifacts, so they must never enter the tracked hash baseline -- doing so
# would pin them forever (and scan_generated_file_drift would then flag their
# removal as drift).
_SYNC_BACKUP_PATTERN = "*.sync-backup-*"


def _is_sync_backup_name(name: str) -> bool:
    """True when *name* is a ``.sync-backup-<ts>`` sibling (never managed)."""
    return fnmatch.fnmatch(name, _SYNC_BACKUP_PATTERN)


# The trailing ``.sync-backup-<YYYYmmdd-HHMMSS>`` suffix written by
# backup_drifted_files() above (and its rule-index sibling). Anchored at the
# end of the name so a nested backup-of-a-backup still strips exactly one.
_SYNC_BACKUP_SUFFIX_RE = re.compile(r"\.sync-backup-(\d{8}-\d{6})$")


def _sync_backup_timestamp(name: str) -> Optional[datetime]:
    """Parse the ``YYYYmmdd-HHMMSS`` suffix of a backup *name*; None if absent
    or unparsable (such a name is never a prune candidate -- fail-safe)."""
    match = _SYNC_BACKUP_SUFFIX_RE.search(name)
    if match is None:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y%m%d-%H%M%S")
    except ValueError:
        return None


def _sync_backup_source(name: str) -> str:
    """Source identity of a backup *name* (the name with its backup suffix removed)."""
    return _SYNC_BACKUP_SUFFIX_RE.sub("", name)


def prune_sync_backups(
    target_dir: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
    max_age_days: int,
    max_per_source: int,
) -> list[str]:
    """Delete ``*.sync-backup-*`` siblings in *target_dir* per retention policy.

    Only direct children of *target_dir* are considered, and only names that
    match ``_is_sync_backup_name`` with a parsable ``YYYYmmdd-HHMMSS`` suffix
    (per the ``backup_drifted_files`` convention). A backup is pruned only when
    **both** thresholds are exceeded: its age is strictly greater than
    *max_age_days* AND strictly more than *max_per_source* newer backups exist
    for the same source. The most recent backup of a source therefore survives
    unconditionally, as do non-backup names and unparsable-timestamp names.

    Recommended default policy (OQ-2): ``max_per_source=3``,
    ``max_age_days=30``; callers pass the values explicitly.

    No-op in ``dry_run`` (returns ``[]``, no filesystem mutation). Fail-soft: a
    per-file ``OSError`` is logged at debug level and iteration continues.
    Returns the pruned project-relative posix paths.
    """
    if dry_run or not target_dir.is_dir():
        return []

    try:
        entries = sorted(target_dir.iterdir())
    except OSError as exc:
        log.debug(
            "sync-backup-prune",
            f"could not list '{target_dir}': {type(exc).__name__}: {exc}",
        )
        return []

    backups: list[tuple[Path, str, datetime]] = []
    for path in entries:
        if not path.is_file() or not _is_sync_backup_name(path.name):
            continue
        stamp = _sync_backup_timestamp(path.name)
        if stamp is None:
            continue
        backups.append((path, _sync_backup_source(path.name), stamp))

    now = datetime.now()
    pruned: list[str] = []
    for path, source, stamp in backups:
        if (now - stamp).days <= max_age_days:
            continue
        newer = sum(
            1 for _other, other_source, other_stamp in backups
            if other_source == source and other_stamp > stamp
        )
        if newer <= max_per_source:
            continue
        try:
            path.unlink()
        except OSError as exc:
            log.debug(
                "sync-backup-prune",
                f"could not delete '{path.name}': {type(exc).__name__}: {exc}",
            )
            continue
        try:
            pruned.append(path.relative_to(project_root).as_posix())
        except ValueError:
            pruned.append(str(path))
    return pruned


def _adapter_file_for_provider(
    config: dict, provider: str, pc: dict
) -> Optional[str]:
    """Project-relative adapter path when ``per-provider`` topology is active.

    An adapter file is a provider's native context file (e.g. Claude's
    ``CLAUDE.md`` at the project root) — outside the per-provider
    managed-index dirs walked below — so it is opted into the drift baseline
    explicitly. Only ``per-provider`` mode opts in, keeping the default
    ``unified`` baseline byte-identical. Purely key-driven (no provider name).
    """
    if not isinstance(config, dict):
        return None
    adapter_file = pc.get("context_adapter_file")
    if not (isinstance(adapter_file, str) and adapter_file.strip()):
        return None
    from .providers import context_topology

    if context_topology(config, provider) != "per-provider":
        return None
    return adapter_file


def _iter_managed_files(
    agent_meta_root: Path, project_root: Path, provider: str, pc: dict,
    config: Optional[dict] = None,
) -> list[Path]:
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
    if pc.get("has_plugins", False) and pc.get("plugin_dir"):
        # Runtime-gate plugin artifact (SPEC-OPENCODE-RUNTIME-GATE-2026-09-13,
        # IC-14): tracked only when the provider declares the plugin capability.
        dir_specs.append((pc["plugin_dir"], []))
    dir_specs.append((resolve_pipeline_details_dir(pc, provider), []))

    for dir_rel, extra_index_names in dir_specs:
        dir_path = project_root / dir_rel
        if not dir_path.is_dir():
            continue
        for name in sorted(_managed_names(dir_path, *extra_index_names)):
            if _is_sync_backup_name(name):
                continue
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
                files.extend(sorted(
                    p for p in candidate.rglob("*")
                    if p.is_file() and not _is_sync_backup_name(p.name)
                ))
        # Nested self-managed subdirectories (hooks/lib/, hooks/release-gates/,
        # issue #558) carry their OWN .agent-meta-managed index -- recurse
        # one level to pick those up too (mirrors scan_injection_drift's
        # "child.is_dir() and (child / '.agent-meta-managed').exists()" check).
        for child in sorted(dir_path.iterdir()):
            if child.is_dir() and (child / ".agent-meta-managed").exists():
                for name in sorted(_managed_names(child)):
                    if _is_sync_backup_name(name):
                        continue
                    nested_candidate = safe_path(child, name)
                    if nested_candidate.is_file():
                        files.append(nested_candidate)

    adapter_file = _adapter_file_for_provider(config, provider, pc)
    if adapter_file:
        adapter_path = project_root / adapter_file
        if adapter_path.is_file():
            files.append(adapter_path)

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
        for abs_path in _iter_managed_files(agent_meta_root, project_root, provider, pc, config):
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


def backup_drifted_files(
    findings: list[dict], project_root: Path, log: SyncLog, dry_run: bool = False,
) -> list[str]:
    """Write a `<file>.sync-backup-<YYYYmmdd-HHMMSS>` sibling for every
    finding, containing exactly the current (pre-overwrite) drifted
    content. One timestamp per invocation, so every backup written by the
    same sync shares the same suffix (mirrors context.py's
    _backup_context_file).

    Fail-soft: a file that cannot be read, or whose backup cannot be
    written, is logged at debug level and skipped -- matching this
    module's optional-config/optional-sidecar style. In dry_run nothing is
    written, but the would-be backup paths are still returned so the
    caller can surface them in its warnings. Returns the project-relative
    posix paths of the backups.
    """
    if not findings:
        return []

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backups: list[str] = []
    for finding in findings:
        rel_path = finding.get("path")
        if not rel_path:
            continue
        target = project_root / rel_path
        try:
            existing_content = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            log.debug(
                "generated-file-drift",
                f"could not read '{rel_path}' for backup: {type(exc).__name__}: {exc}",
            )
            continue
        backup = target.with_name(f"{target.name}.sync-backup-{ts}")
        if not dry_run:
            try:
                backup.write_text(existing_content, encoding="utf-8")
            except OSError as exc:
                log.debug(
                    "generated-file-drift",
                    f"could not write backup for '{rel_path}': {type(exc).__name__}: {exc}",
                )
                continue
        try:
            backups.append(backup.relative_to(project_root).as_posix())
        except ValueError:
            backups.append(str(backup))
    return backups


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
        for abs_path in _iter_managed_files(agent_meta_root, project_root, provider, pc, config):
            rel_path = abs_path.relative_to(project_root).as_posix()
            hashes[rel_path] = content_hash(abs_path.read_text(encoding="utf-8"))
    resolved_path = project_root / PLATFORM_DEFAULTS_RESOLVED_REL
    if resolved_path.is_file():
        hashes[PLATFORM_DEFAULTS_RESOLVED_REL] = content_hash(resolved_path.read_text(encoding="utf-8"))
    _save_hashes(project_root, hashes, dry_run)


# ---------------------------------------------------------------------------
# Path migration (SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30, Task 11; H-2,
# ADR-9). Backup-first managed delete + ordered
# write-new -> verify -> backup-old -> remove-old, plus the net-zero-aware
# final-content diff. Every helper is provider-agnostic: it reads managed
# markers / index entries and config path values, never a provider name.
# ---------------------------------------------------------------------------

_MANAGED_MARKERS = (
    "agent-meta:managed-begin",
    "agent-meta:bootstrap-begin",
    # Canonical simple-annotation sentinel emitted by writers that don't use the
    # block markers: isolation.py's Gemini TOML policy / Continue soft rule
    # (`# agent-meta managed — do not edit manually` / HTML-comment variant),
    # isolation state files and hooks.py's `_agent-meta` provenance key.
    # Deliberately the FULL sentence, not the bare prefix "agent-meta managed":
    # is_managed_artifact() also gates the destructive backup+delete / migrate
    # path (remove_managed_artifact / migrate_managed_artifact), so a loose
    # substring would let any user file merely *mentioning* the phrase be
    # deleted. A narrow marker keeps the destructive guard narrow (issue #802).
    "agent-meta managed — do not edit manually",
)


def is_managed_artifact(path: Path) -> bool:
    """True when *path* is an agent-meta-managed artifact.

    Two signals, either sufficient:

    A. the file content carries an agent-meta managed marker (the HTML comment
       form or the ``# agent-meta:managed-begin`` YAML-comment form);
    B. the file's basename is listed in a sibling ``.agent-meta-managed``
       (or ``-mcp``/``-tools``) index.

    A missing, foreign or unreadable file returns ``False`` — user content is
    never assumed managed.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    if any(marker in content for marker in _MANAGED_MARKERS):
        return True
    if not path.parent.is_dir():
        return False
    return path.name in _managed_names(path.parent, "mcp", "tools")


def write_sync_backup(target: Path, ts: Optional[str] = None) -> Optional[Path]:
    """Write a byte-exact ``<name>.sync-backup-<ts>`` sibling of *target*.

    One timestamp per call (pass *ts* to share it across a whole migration
    batch). Returns the backup path, or ``None`` when the target cannot be
    read or the backup cannot be written (fail-soft, mirrors
    ``backup_drifted_files``).
    """
    stamp = ts or datetime.now().strftime("%Y%m%d-%H%M%S")
    try:
        payload = target.read_bytes()
    except OSError:
        return None
    backup = target.with_name(f"{target.name}.sync-backup-{stamp}")
    try:
        backup.write_bytes(payload)
    except OSError:
        return None
    return backup


def _project_rel(path: Path, project_root: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return str(path)


def remove_managed_artifact(
    target: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool = False,
    ts: Optional[str] = None,
    verify=None,
) -> dict:
    """Backup-first managed delete (H-2 / ADR-9).

    A user-authored file (no managed marker / index entry) is NEVER deleted —
    it is left in place and a WARNING is logged. A managed file is backed up
    byte-exactly *before* it is removed, so the backup restores the exact
    pre-delete bytes. In ``dry_run`` nothing is written: ``removed`` stays
    ``False`` while ``would_remove`` records the intent.

    ``verify`` is an optional predicate ``verify(target) -> bool``: the delete
    is deferred when it does not return exactly ``True`` (design §6.2 step 2,
    "verify new before removing old"). The default ``None`` keeps the historical
    managed-marker guard as the only gate.
    """
    rel = _project_rel(target, project_root)
    result = {
        "path": rel,
        "removed": False,
        "would_remove": False,
        "backup": None,
        "reason": "absent",
    }
    if not target.is_file():
        return result
    if not is_managed_artifact(target):
        log.warning(f"{rel}: not agent-meta managed — user-authored file left in place")
        result["reason"] = "user-authored"
        return result
    if verify is not None:
        try:
            verdict = verify(target)
        except Exception as exc:
            verdict = f"{type(exc).__name__}: {exc}"
        if verdict is not True:
            log.warning(f"{rel}: verify deferred removal ({verdict!r}) — file left in place")
            result["reason"] = "verify-deferred"
            return result
    result["would_remove"] = True
    if dry_run:
        result["reason"] = "managed"
        return result
    backup = write_sync_backup(target, ts=ts)
    if backup is None:
        log.warning(f"{rel}: could not write .sync-backup sibling — file left in place")
        result["would_remove"] = False
        result["reason"] = "backup-failed"
        return result
    try:
        target.unlink()
    except OSError as exc:
        log.warning(f"{rel}: could not remove managed artifact: {type(exc).__name__}: {exc}")
        result["reason"] = "remove-failed"
        return result
    result["removed"] = True
    result["backup"] = _project_rel(backup, project_root)
    result["reason"] = "managed"
    return result


def migrate_managed_artifact(
    old_path: Path,
    new_path: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool = False,
    verify=None,
    ts: Optional[str] = None,
) -> dict:
    """Ordered path migration: write-new -> verify -> backup-old -> remove-old.

    Config-independent primitive used by the discovery migration driver. The
    new artifact is written first (bytes copied from the managed old artifact
    when the new path is still empty), then verified — ``verify(new_path)`` is
    an optional predicate whose verdict must be exactly ``True`` to continue.
    Only after verification succeeds is the old artifact backed up
    byte-exactly and removed. A user-authored old artifact is left untouched
    (data-loss guard).

    Returns a result dict; ``status`` is one of ``no-old``,
    ``user-authored``, ``read-failed``, ``write-failed``, ``verify-failed``,
    ``backup-failed``, ``remove-failed``, ``migrated`` or ``would-migrate``.
    """
    old_rel = _project_rel(old_path, project_root)
    new_rel = _project_rel(new_path, project_root)
    result = {"old": old_rel, "new": new_rel, "status": "no-old", "backup": None}
    if not old_path.is_file():
        return result
    if not is_managed_artifact(old_path):
        log.warning(
            f"{old_rel}: not agent-meta managed — user-authored file left in place "
            f"(no migration to {new_rel})"
        )
        result["status"] = "user-authored"
        return result

    # 1. write new.
    if not new_path.exists():
        try:
            payload = old_path.read_bytes()
        except OSError as exc:
            log.warning(f"{old_rel}: could not read for migration: {type(exc).__name__}: {exc}")
            result["status"] = "read-failed"
            return result
        if not dry_run:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                new_path.write_bytes(payload)
            except OSError as exc:
                log.warning(f"{new_rel}: could not write migrated artifact: {type(exc).__name__}: {exc}")
                result["status"] = "write-failed"
                return result

    # 2. verify new before anything is removed.
    if verify is not None:
        try:
            verdict = verify(new_path)
        except Exception as exc:  # noqa: BLE001 - any verifier error aborts the removal
            verdict = f"{type(exc).__name__}: {exc}"
        if verdict is not True:
            log.warning(f"{new_rel}: verification failed ({verdict!r}) — old artifact kept")
            result["status"] = "verify-failed"
            return result

    # 3. backup old + 4. remove old (backup-first).
    if dry_run:
        result["status"] = "would-migrate"
        return result
    backup = write_sync_backup(old_path, ts=ts)
    if backup is None:
        log.warning(f"{old_rel}: could not write .sync-backup sibling — old artifact left in place")
        result["status"] = "backup-failed"
        return result
    try:
        old_path.unlink()
    except OSError as exc:
        log.warning(f"{old_rel}: could not remove migrated artifact: {type(exc).__name__}: {exc}")
        result["status"] = "remove-failed"
        result["backup"] = _project_rel(backup, project_root)
        return result
    result["backup"] = _project_rel(backup, project_root)
    result["status"] = "migrated"
    return result


def final_content_diff(project_root: Path, final_contents: dict) -> list[str]:
    """Project-relative paths whose FINAL content differs from the on-disk bytes.

    "Final-content diff" (design §6.3): a pending-write computation must
    reflect the end state of a sync, not its intermediate writes. A file whose
    final content equals its current content is clean even when an intermediate
    step would have changed it (net-zero == clean). *final_contents* maps
    project-relative posix paths to ``str`` (utf-8) or ``bytes``.
    """
    changed: list[str] = []
    for rel_path, content in final_contents.items():
        desired = content.encode("utf-8") if isinstance(content, str) else bytes(content)
        try:
            current = (project_root / rel_path).read_bytes()
        except OSError:
            current = None
        if current != desired:
            changed.append(rel_path)
    return changed


# Optional `kind` values a migration entry may carry; anything else degrades to
# the conservative single-file behaviour.
_MIGRATION_KINDS = ("dir", "file")


def _normalize_migration_entry(raw) -> Optional[dict]:
    """One normalized ``{"remove": <rel>, "kind": <dir|file>}`` entry or None."""
    if not isinstance(raw, dict):
        return None
    remove = raw.get("remove")
    if not (isinstance(remove, str) and remove.strip()):
        return None
    kind = raw.get("kind", "file")
    if kind not in _MIGRATION_KINDS:
        kind = "file"
    return {"remove": remove.strip(), "kind": kind}


def _normalize_migration_spec(raw) -> Optional[dict]:
    """Normalize one provider's map value to ``{"requires-flag", "removals"}``.

    Accepts both documented shapes (data contract, config/provider-migrations.yaml):
    a bare sequence of entries (default-on, no flag) and a mapping with an
    optional ``requires-flag`` string plus a ``removals`` sequence. Anything
    malformed degrades to ``None`` (fail-soft, like every optional sidecar here).
    """
    if isinstance(raw, list):
        entries = [_normalize_migration_entry(item) for item in raw]
        removals = [entry for entry in entries if entry is not None]
        return {"requires-flag": None, "removals": removals} if removals else None
    if not isinstance(raw, dict):
        return None
    flag = raw.get("requires-flag")
    flag = flag.strip() if isinstance(flag, str) and flag.strip() else None
    raw_removals = raw.get("removals")
    if not isinstance(raw_removals, list):
        return None
    entries = [_normalize_migration_entry(item) for item in raw_removals]
    removals = [entry for entry in entries if entry is not None]
    if not removals:
        return None
    return {"requires-flag": flag, "removals": removals}


def load_provider_migrations(config_dir: Path) -> dict[str, dict]:
    """Read ``config/provider-migrations.yaml`` into a normalized dict.

    Returns ``{provider: {"requires-flag": str|None, "removals": [...]}}``; ``{}``
    when the file is absent or malformed (fail-soft — a project without the map
    simply migrates nothing). Purely data-driven: the provider key is a lookup
    key, never a branch condition.
    """
    data = load_yaml_file(config_dir / "provider-migrations.yaml", on_error="default", default={})
    migrations = data.get("migrations") if isinstance(data, dict) else None
    if not isinstance(migrations, dict):
        return {}
    normalized: dict[str, dict] = {}
    for provider, raw in migrations.items():
        if not isinstance(provider, str):
            continue
        spec = _normalize_migration_spec(raw)
        if spec is not None:
            normalized[provider] = spec
    return normalized

