"""Agent-meta Backup & Restore System.

Creates timestamped, labelled zip archives of all generated provider directories
plus the project configuration. Supports listing, restoring, deleting and
pruning backups with configurable retention policies.

Config in project.yaml:

    backup:
      enabled: true
      dir: .backup/agent-meta
      retention:
        max_backups: 10
        max_age_days: 30
      auto-backup-before-sync: false

CLI:
    python scripts/sync.py --backup [--label "My label"] [Provider...]
    python scripts/sync.py --restore <archive.zip>
    python scripts/sync.py --list-backups
    python scripts/sync.py --delete-backup <archive.zip>
    python scripts/sync.py --prune-backups

The deactivation module delegates zip/restore to this module for consistency.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from .log import SyncLog
from .providers import load_providers_config

DEFAULT_BACKUP_DIR = ".backup/agent-meta"
DEFAULT_MAX_BACKUPS = 10
DEFAULT_MAX_AGE_DAYS = 30
MANIFEST_FILENAME = "manifest.json"


def _get_backup_config(config: dict) -> dict:
    """Return the backup config block with defaults applied."""
    bc = config.get("backup", {})
    if not isinstance(bc, dict):
        bc = {}
    bc.setdefault("enabled", True)
    bc.setdefault("dir", DEFAULT_BACKUP_DIR)
    retention = bc.get("retention")
    if not isinstance(retention, dict):
        retention = {}
        bc["retention"] = retention
    retention.setdefault("max_backups", DEFAULT_MAX_BACKUPS)
    retention.setdefault("max_age_days", DEFAULT_MAX_AGE_DAYS)
    return bc


def _get_provider_root_dir(provider: str, provider_config: dict) -> str | None:
    """Derive the provider's root directory from its agents_dir."""
    pc = provider_config.get(provider, {})
    agents_dir = pc.get("agents_dir", "")
    if not agents_dir:
        return None
    path = Path(agents_dir)
    parent = str(path.parent) if path.parent != Path(".") else str(path)
    if not parent or parent == ".":
        return None
    return parent.replace("\\", "/") + "/"


def _relative_path(path: Path, root: Path) -> str:
    """Return a forward-slash relative path string."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _build_manifest(
    backup_name: str,
    label: str | None,
    providers: list[str],
    project_root: Path,
    provider_config: dict,
    source_version: str,
    extra_files: dict[str, str],
) -> dict:
    """Build the metadata manifest for a backup archive."""
    manifest: dict = {
        "name": backup_name,
        "created": datetime.now(timezone.utc).isoformat(),
        "agent_meta_version": source_version,
        "label": label or "",
        "providers": {},
        "config_file": None,
        "extra_files": [],
    }

    for provider in providers:
        root_dir = _get_provider_root_dir(provider, provider_config)
        if root_dir:
            provider_dir = project_root / root_dir
            manifest["providers"][provider] = {
                "directory": root_dir,
                "exists": provider_dir.exists(),
            }

    for filename, _rel in extra_files.items():
        manifest["extra_files"].append({"file": filename, "relative": _rel})
        if filename == ".meta-config/project.yaml":
            manifest["config_file"] = ".meta-config/project.yaml"

    return manifest


def _archive_name(prefix: str = "agent-meta-backup") -> str:
    """Generate a timestamped archive name."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}"


def _parse_archive_metadata(name: str) -> dict:
    """Extract date/provider info from an archive filename."""
    result = {"name": name, "prefix": "", "timestamp": "", "provider": ""}
    stem = Path(name).stem
    parts = stem.rsplit("_", 2)
    if len(parts) >= 3:
        result["prefix"] = parts[0]
        result["timestamp"] = parts[1]
        result["provider"] = parts[2] if len(parts) > 2 else ""
    return result


def list_backups(
    project_root: Path,
    config: dict,
    provider_config: dict,
) -> dict:
    """Return all available backups with metadata.

    Returns a dict with:
        - backup_dir: relative path to backup directory
        - count: total number of backup archives
        - archives: list of archive metadata dicts
    """
    bc = _get_backup_config(config)
    backup_dir_name = bc["dir"]
    backup_dir = project_root / backup_dir_name

    result: dict = {
        "backup_dir": backup_dir_name,
        "exists": backup_dir.exists(),
        "count": 0,
        "archives": [],
        "retention": {
            "max_backups": bc["retention"]["max_backups"],
            "max_age_days": bc["retention"]["max_age_days"],
        },
    }

    if not backup_dir.exists():
        return result

    archives: list[dict] = []
    for f in sorted(backup_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            stat = f.stat()
            size_mb = stat.st_size / (1024 * 1024)
            info: dict = {
                "name": f.name,
                "path": _relative_path(f, project_root),
                "size_bytes": stat.st_size,
                "size_mb": round(size_mb, 2),
                "created": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }
            meta = _parse_archive_metadata(f.name)
            info.update(meta)

            # Try to read manifest from inside the zip for richer info
            try:
                import zipfile
                with zipfile.ZipFile(f, "r") as zf:
                    if MANIFEST_FILENAME in zf.namelist():
                        manifest_data = json.loads(zf.read(MANIFEST_FILENAME).decode("utf-8"))
                        info["label"] = manifest_data.get("label", "")
                        info["providers"] = list(manifest_data.get("providers", {}).keys())
                        info["agent_meta_version"] = manifest_data.get("agent_meta_version", "")
            except Exception:
                info["label"] = ""
                info["providers"] = []

            archives.append(info)
        except OSError:
            continue

    result["count"] = len(archives)
    result["archives"] = archives
    return result


def create_backup(
    project_root: Path,
    providers: list[str] | None,
    provider_config: dict,
    config: dict,
    log: SyncLog,
    label: str | None = None,
    dry_run: bool = False,
    source_version: str = "",
) -> dict:
    """Create a timestamped backup zip of provider directories and project config.

    The archive contains:
        - manifest.json (metadata)
        - .meta-config/project.yaml (project configuration)
        - Each provider's root directory (if it exists)

    Args:
        project_root: Root of the project being backed up.
        providers: Provider names to include, None or empty for all known.
        provider_config: Loaded provider configuration.
        config: Project configuration dict.
        log: Sync log instance.
        label: Optional human-readable label for the backup.
        dry_run: If True, only report what would happen.
        source_version: Agent-meta version string for the manifest.

    Returns:
        Dict with backup result including archive path and included providers.
    """
    bc = _get_backup_config(config)
    backup_dir_name = bc["dir"]
    backup_dir = project_root / backup_dir_name

    if providers is None or not providers:
        targets = list(provider_config.keys())
    else:
        targets = [p for p in providers if p in provider_config]

    archive_name = _archive_name()
    zip_path = backup_dir / (archive_name + ".zip")

    # Build manifest
    extra_files: dict[str, str] = {}
    project_yaml_path = project_root / ".meta-config" / "project.yaml"
    if project_yaml_path.exists():
        extra_files[".meta-config/project.yaml"] = _relative_path(project_yaml_path, project_root)

    manifest = _build_manifest(
        archive_name, label, targets, project_root, provider_config,
        source_version, extra_files,
    )

    if dry_run:
        log.info("backup", f"DRY-RUN: would create backup '{archive_name}.zip'")
        log.info("backup", f"  providers: {', '.join(targets)}")
        log.info("backup", f"  config: {'yes' if extra_files else 'no'}")
        if label:
            log.info("backup", f"  label: {label}")
        return {
            "success": True,
            "archive": _relative_path(zip_path, project_root),
            "providers": targets,
            "config_included": bool(extra_files),
            "label": label,
            "manifest": manifest,
            "dry_run": True,
        }

    backup_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # Write manifest
        manifest_path = tmp / MANIFEST_FILENAME
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Copy project.yaml
        for filename, rel_path in extra_files.items():
            src = project_root / rel_path
            if src.exists():
                dst = tmp / filename
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        # Copy provider directories
        included: list[str] = []
        for provider in targets:
            root_dir = _get_provider_root_dir(provider, provider_config)
            if not root_dir:
                log.warn(f"backup: cannot determine root directory for '{provider}'")
                continue
            src_dir = project_root / root_dir
            if not src_dir.exists():
                log.info("backup", f"provider directory not found, skipping: {root_dir}")
                manifest["providers"][provider]["backed_up"] = False
                continue

            dst_dir = tmp / root_dir
            dst_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src_dir, dst_dir, symlinks=False, dirs_exist_ok=True)
            manifest["providers"][provider]["backed_up"] = True
            included.append(provider)

        # Update manifest with final state and write again
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Create zip archive
        created = shutil.make_archive(
            str(zip_path.with_suffix("")),
            "zip",
            root_dir=str(tmp),
            base_dir=".",
        )

    zip_file = Path(created)
    size_mb = zip_file.stat().st_size / (1024 * 1024)
    log.info("backup", f"created '{_relative_path(zip_file, project_root)}' "
             f"({round(size_mb, 2)} MB, {len(included)} providers)")

    # Apply retention
    pruned = _prune_backups(backup_dir, bc["retention"]["max_backups"], log)

    return {
        "success": True,
        "archive": _relative_path(zip_file, project_root),
        "size_mb": round(size_mb, 2),
        "providers": included,
        "config_included": bool(extra_files),
        "label": label,
        "manifest": manifest,
        "pruned": pruned,
    }


def restore_backup(
    project_root: Path,
    archive_name: str,
    provider_config: dict,
    config: dict,
    log: SyncLog,
    providers: list[str] | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> dict:
    """Restore provider directories and optionally project config from a backup.

    Args:
        project_root: Root of the project.
        archive_name: Name of the zip file to restore (without path, or relative).
        provider_config: Loaded provider configuration.
        config: Project configuration dict.
        log: Sync log instance.
        providers: Which providers to restore (None = all in archive).
        force: If True, overwrite existing directories.
        dry_run: If True, only report what would happen.

    Returns:
        Dict with restore results per provider and config.
    """
    bc = _get_backup_config(config)
    backup_dir_name = bc["dir"]
    backup_dir = project_root / backup_dir_name

    # Resolve archive path
    archive_path = backup_dir / archive_name
    if not archive_path.exists():
        # Try as full path
        archive_path = Path(archive_name)
        if not archive_path.exists():
            return {"success": False, "error": f"archive not found: {archive_name}"}

    result: dict = {
        "success": True,
        "archive": _relative_path(archive_path, project_root),
        "provider_results": {},
        "config_restored": False,
    }

    # Read manifest
    manifest: dict = {}
    try:
        import zipfile
        with zipfile.ZipFile(archive_path, "r") as zf:
            names = zf.namelist()
            if MANIFEST_FILENAME in names:
                manifest = json.loads(zf.read(MANIFEST_FILENAME).decode("utf-8"))
    except Exception as exc:
        return {"success": False, "error": f"failed to read archive: {exc}"}

    archive_providers = list(manifest.get("providers", {}).keys()) if manifest else []
    if not archive_providers:
        # Fallback: infer from directory structure in zip
        try:
            import zipfile
            with zipfile.ZipFile(archive_path, "r") as zf:
                names = zf.namelist()
                archive_providers = []
                for n in names:
                    parts = n.split("/")
                    if parts[0].startswith(".") and len(parts) > 1:
                        candidate = parts[0] + "/"
                        if candidate not in archive_providers:
                            archive_providers.append(candidate)
                log.info("backup", f"inferred providers from archive: {archive_providers}")
        except Exception:
            pass

    restore_targets = providers if providers else archive_providers
    if isinstance(restore_targets, list):
        restore_targets = [p for p in restore_targets if isinstance(p, str)]
        # Normalize: strip trailing slash
        restore_targets = [p.rstrip("/") for p in restore_targets]

    for target in restore_targets:
        prov_result: dict = {"provider": target, "restored": False}

        # Find matching provider in archive
        matching = None
        for ap in archive_providers:
            if ap.rstrip("/") == target or ap == target + "/":
                matching = ap
                break
        if not matching:
            # Try by provider name from ai-providers config
            provider_root = _get_provider_root_dir(target, provider_config)
            if provider_root:
                archive_name_norm = provider_root.rstrip("/")
                for ap in archive_providers:
                    if ap.rstrip("/") == archive_name_norm:
                        matching = ap
                        break

        if not matching:
            prov_result["error"] = f"provider '{target}' not found in archive"
            result["provider_results"][target] = prov_result
            continue

        # Check if target already exists
        provider_root_dir = _get_provider_root_dir(target, provider_config)
        if not provider_root_dir:
            prov_result["error"] = f"cannot determine root directory for '{target}'"
            result["provider_results"][target] = prov_result
            continue

        target_dir = project_root / provider_root_dir
        if target_dir.exists() and not force:
            prov_result["error"] = f"target directory already exists: {provider_root_dir}"
            result["provider_results"][target] = prov_result
            continue

        if dry_run:
            log.info("backup", f"DRY-RUN: would restore '{matching}' from archive")
            prov_result["restored"] = True
            result["provider_results"][target] = prov_result
            continue

        # Extract from zip
        try:
            import zipfile
            with zipfile.ZipFile(archive_path, "r") as zf:
                # Extract only the matching provider directory
                for member in zf.namelist():
                    member_parts = Path(member).parts
                    if not member_parts:
                        continue
                    if member_parts[0].rstrip("/") == matching.rstrip("/"):
                        zf.extract(member, str(target_dir.parent))
                log.info("backup", f"restored '{matching}' for provider '{target}'")
                prov_result["restored"] = True
            result["provider_results"][target] = prov_result
        except Exception as exc:
            prov_result["error"] = str(exc)
            result["provider_results"][target] = prov_result

    # Restore project.yaml if requested
    project_yaml_in_archive = ".meta-config/project.yaml" if manifest else None
    if project_yaml_in_archive and not dry_run:
        try:
            import zipfile
            target_yaml = project_root / ".meta-config" / "project.yaml"
            with zipfile.ZipFile(archive_path, "r") as zf:
                if project_yaml_in_archive in zf.namelist():
                    if force or not target_yaml.exists():
                        target_yaml.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(project_yaml_in_archive) as src:
                            target_yaml.write_bytes(src.read())
                        result["config_restored"] = True
                        log.info("backup", "restored project.yaml from backup")
        except Exception:
            pass

    return result


def delete_backup(
    project_root: Path,
    archive_name: str,
    config: dict,
    log: SyncLog,
    dry_run: bool = False,
) -> dict:
    """Delete a specific backup archive.

    Args:
        project_root: Project root directory.
        archive_name: Name or relative path of the archive to delete.
        config: Project configuration dict.
        log: Sync log instance.
        dry_run: If True, only report what would happen.

    Returns:
        Dict with success status.
    """
    bc = _get_backup_config(config)
    backup_dir_name = bc["dir"]
    backup_dir = project_root / backup_dir_name

    archive_path = backup_dir / archive_name
    if not archive_path.exists():
        archive_path = Path(archive_name)
        if not archive_path.exists():
            return {"success": False, "error": f"archive not found: {archive_name}"}

    if dry_run:
        log.info("backup", f"DRY-RUN: would delete '{_relative_path(archive_path, project_root)}'")
        return {"success": True, "deleted": _relative_path(archive_path, project_root), "dry_run": True}

    try:
        size_mb = archive_path.stat().st_size / (1024 * 1024)
        archive_path.unlink()
        log.info("backup", f"deleted '{_relative_path(archive_path, project_root)}' "
                 f"({round(size_mb, 2)} MB)")
        return {"success": True, "deleted": _relative_path(archive_path, project_root),
                "size_mb": round(size_mb, 2)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def prune_backups(
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool = False,
) -> dict:
    """Delete old backups according to retention policy.

    Keeps at most max_backups archives (most recent) and deletes anything
    older than max_age_days.

    Returns:
        Dict with pruning results.
    """
    bc = _get_backup_config(config)
    backup_dir_name = bc["dir"]
    backup_dir = project_root / backup_dir_name
    max_backups = bc["retention"]["max_backups"]
    max_age_days = bc["retention"]["max_age_days"]

    if not backup_dir.exists():
        return {"success": True, "pruned": 0, "message": "no backup directory"}

    archives = sorted(
        backup_dir.glob("*.zip"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    to_delete: list[Path] = []
    cutoff = datetime.now() - timedelta(days=max_age_days)

    for i, archive in enumerate(archives):
        try:
            mtime = datetime.fromtimestamp(archive.stat().st_mtime)
        except OSError:
            continue
        if i >= max_backups or mtime < cutoff:
            to_delete.append(archive)

    if dry_run:
        log.info("backup", f"DRY-RUN: would prune {len(to_delete)} backup(s)")
        for a in to_delete:
            log.info("backup", f"  would delete: {a.name}")
        return {"success": True, "pruned": len(to_delete), "dry_run": True,
                "files": [a.name for a in to_delete]}

    pruned = _prune_backups(backup_dir, max_backups, log)
    # Also handle age-based pruning
    age_deleted = 0
    for archive in list(backup_dir.glob("*.zip")):
        try:
            mtime = datetime.fromtimestamp(archive.stat().st_mtime)
            if mtime < cutoff:
                archive.unlink()
                age_deleted += 1
                log.info("backup", f"pruned (age): {archive.name}")
        except OSError:
            continue

    return {"success": True, "pruned": pruned + age_deleted}


def _prune_backups(backup_dir: Path, max_backups: int, log: SyncLog) -> int:
    """Internal: delete excess backups beyond max_backups (most recent kept)."""
    archives = sorted(
        backup_dir.glob("*.zip"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    deleted = 0
    for old in archives[max_backups:]:
        try:
            old.unlink()
            deleted += 1
            log.info("backup", f"pruned (count): {old.name}")
        except OSError:
            continue
    return deleted


# ---------------------------------------------------------------------------
# Compatibility with deactivation module
# These delegate to the backup module so all zip/restore uses the same code.
# ---------------------------------------------------------------------------


def backup_provider_dir(
    project_root: Path,
    provider: str,
    provider_config: dict,
    config: dict,
    log: SyncLog,
    dry_run: bool = False,
    source_version: str = "",
) -> Path | None:
    """Backup a single provider directory (used by deactivation).

    Delegates to create_backup for a single provider. Returns the archive path.
    """
    result = create_backup(
        project_root, [provider], provider_config, config, log,
        label=f"deactivation:{provider}",
        dry_run=dry_run,
        source_version=source_version,
    )
    if result.get("success") and not dry_run:
        archive_path = project_root / result["archive"]
        return archive_path
    if dry_run:
        return project_root / result["archive"]
    return None


def restore_provider_dir(
    project_root: Path,
    provider: str,
    archive_name: str,
    provider_config: dict,
    config: dict,
    log: SyncLog,
    dry_run: bool = False,
) -> bool:
    """Restore a single provider from a backup archive (used by deactivation).

    Args:
        archive_name: The zip file name to restore from.

    Returns:
        True if restored successfully.
    """
    result = restore_backup(
        project_root, archive_name, provider_config, config, log,
        providers=[provider],
        dry_run=dry_run,
    )
    prov_result = result.get("provider_results", {}).get(provider, {})
    return prov_result.get("restored", False)
