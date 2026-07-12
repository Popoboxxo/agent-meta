"""Provider deactivation: backup provider directories as zip and remove them.

Supports per-provider or all-provider deactivation controlled via project.yaml:

    provider-deactivation:
      enabled: true
      mode: selective          # "all" | "selective"
      providers: [Gemini]      # which providers to deactivate (ignored when mode=all)
      backup-dir: .backup/provider-deactivation

Zip/restore operations delegate to backup.py for unified backup handling.
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from .log import SyncLog
from .backup import backup_provider_dir as _backup_single, restore_provider_dir as _restore_single


DEFAULT_BACKUP_DIR = ".backup/provider-deactivation"


def _get_provider_root_dir(provider: str, provider_config: dict) -> str | None:
    """Derive the provider's root directory from its agents_dir.

    Claude:    .claude/agents          -> .claude/
    Gemini:    .gemini/agents          -> .gemini/
    Opencode:  .opencode/agents        -> .opencode/
    Continue:  .continue/agents        -> .continue/
    Copilot:   .github/copilot/agents  -> .github/copilot/
    """
    pc = provider_config.get(provider, {})
    agents_dir = pc.get("agents_dir", "")
    if not agents_dir:
        return None
    path = Path(agents_dir)
    parent = str(path.parent) if path.parent != Path(".") else str(path)
    if not parent or parent == ".":
        return None
    return parent.replace("\\", "/") + "/"


def _get_deactivation_config(config: dict) -> dict:
    """Return the deactivation config block with defaults."""
    return config.get("provider-deactivation", {})


def _is_provider_deactivated(config: dict, provider: str) -> bool:
    """Check if a specific provider is deactivated."""
    dc = _get_deactivation_config(config)
    if not dc.get("enabled", False):
        return False
    mode = dc.get("mode", "all")
    if mode == "all":
        return True
    deactivated = dc.get("providers", [])
    if isinstance(deactivated, list):
        return provider in deactivated
    return False


def is_provider_active(config: dict, provider: str) -> bool:
    """Return True if the provider is not deactivated."""
    return not _is_provider_deactivated(config, provider)


def get_deactivated_providers(config: dict, provider_config: dict) -> list[str]:
    """Return list of currently deactivated provider names."""
    dc = _get_deactivation_config(config)
    if not dc.get("enabled", False):
        return []
    mode = dc.get("mode", "all")
    if mode == "all":
        return list(provider_config.keys())
    deactivated = dc.get("providers", [])
    if isinstance(deactivated, list):
        return [p for p in deactivated if p in provider_config]
    return []


def get_active_providers(config: dict, provider_config: dict) -> list[str]:
    """Return list of providers that are NOT deactivated."""
    from .providers import resolve_providers
    configured = resolve_providers(config, provider_config)
    dc = _get_deactivation_config(config)
    if not dc.get("enabled", False):
        return configured
    mode = dc.get("mode", "all")
    if mode == "all":
        return []
    deactivated = set(dc.get("providers", []) if isinstance(dc.get("providers"), list) else [])
    return [p for p in configured if p not in deactivated]


def get_deactivation_status(
    project_root: Path,
    config: dict,
    provider_config: dict,
) -> dict:
    """Return deactivation status for all providers.

    Returns a dict with per-provider status indicating whether the provider
    is deactivated, whether a backup exists, and file counts.
    """
    dc = _get_deactivation_config(config)
    backup_dir_name = dc.get("backup-dir", DEFAULT_BACKUP_DIR)
    backup_dir = project_root / backup_dir_name

    result: dict = {
        "enabled": dc.get("enabled", False),
        "mode": dc.get("mode", "all"),
        "deactivated_providers": dc.get("providers", []) if dc.get("mode") == "selective" else [],
        "backup_dir": backup_dir_name,
        "providers": {},
    }

    all_providers = list(provider_config.keys())
    for provider in all_providers:
        provider_root = _get_provider_root_dir(provider, provider_config)
        provider_dir = project_root / provider_root if provider_root else None
        dir_exists = provider_dir.exists() if provider_dir else False

        deactivated = _is_provider_deactivated(config, provider)

        backup_files = []
        backup_timestamps = []
        if backup_dir.exists():
            for f in sorted(backup_dir.glob(f"{provider}_*.zip")):
                backup_files.append(str(f.relative_to(project_root)))
                try:
                    backup_timestamps.append(
                        datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat()
                    )
                except OSError:
                    backup_timestamps.append("unknown")

        result["providers"][provider] = {
            "deactivated": deactivated,
            "directory": str(provider_dir.relative_to(project_root)) if provider_dir and dir_exists else (provider_root or ""),
            "directory_exists": dir_exists,
            "backups": backup_files,
            "backup_timestamps": backup_timestamps,
        }

    return result


def zip_provider_dir(
    project_root: Path,
    provider: str,
    provider_config: dict,
    config: dict,
    log: SyncLog,
    dry_run: bool = False,
) -> Path | None:
    """Zip a provider's root directory into a timestamped backup archive.

    Delegates to backup.backup_provider_dir for unified archive creation.
    """
    return _backup_single(project_root, provider, provider_config, config, log, dry_run)


def remove_provider_dir(
    project_root: Path,
    provider: str,
    provider_config: dict,
    log: SyncLog,
    dry_run: bool = False,
) -> bool:
    """Remove a provider's root directory.

    Returns True on success, False if the directory didn't exist.
    """
    provider_root = _get_provider_root_dir(provider, provider_config)
    if not provider_root:
        log.warn(f"deactivation: cannot determine root directory for provider '{provider}'")
        return False

    target_dir = project_root / provider_root
    if not target_dir.exists():
        log.info("deactivation", f"provider directory already removed: {provider_root}")
        return False

    if dry_run:
        log.info("deactivation", f"DRY-RUN: would remove '{provider_root}'")
        return True

    try:
        shutil.rmtree(target_dir)
        log.info("deactivation", f"removed provider directory: {provider_root}")
        return True
    except Exception as exc:
        log.error(f"deactivation: failed to remove '{provider_root}': {exc}")
        return False


def deactivate_providers(
    project_root: Path,
    providers: list[str],
    provider_config: dict,
    config: dict,
    log: SyncLog,
    dry_run: bool = False,
) -> dict:
    """Deactivate one or more providers: zip their directories and remove them.

    Args:
        project_root: Project root directory.
        providers: List of provider names to deactivate, or empty/["all"] for all.
        provider_config: Loaded provider configuration.
        config: Project configuration dict.
        log: Sync log instance.
        dry_run: If True, only report what would be done.

    Returns:
        A dict with status per provider.
    """
    if not providers or "all" in [p.lower() for p in providers]:
        targets = list(provider_config.keys())
    else:
        targets = [p for p in providers if p in provider_config]

    results: dict = {}
    for provider in targets:
        provider_result: dict = {"provider": provider, "backed_up": False, "removed": False}

        zip_path = zip_provider_dir(project_root, provider, provider_config, config, log, dry_run)
        if zip_path:
            provider_result["backed_up"] = True
            provider_result["backup_file"] = str(zip_path.relative_to(project_root))

        removed = remove_provider_dir(project_root, provider, provider_config, log, dry_run)
        provider_result["removed"] = removed

        results[provider] = provider_result

    return results


def activate_providers(
    project_root: Path,
    providers: list[str],
    provider_config: dict,
    config: dict,
    log: SyncLog,
    dry_run: bool = False,
) -> dict:
    """Activate (restore) one or more providers from backup zips.

    Delegates to backup.restore_backup for each provider, using the most
    recent backup archive found in the deactivation backup directory.

    Args:
        project_root: Project root directory.
        providers: List of provider names to activate, or empty for all.
        provider_config: Loaded provider configuration.
        config: Project configuration dict.
        log: Sync log instance.
        dry_run: If True, only report what would be done.

    Returns:
        A dict with status per provider.
    """
    if not providers:
        targets = list(provider_config.keys())
    else:
        targets = [p for p in providers if p in provider_config]

    dc = _get_deactivation_config(config)
    backup_dir_name = dc.get("backup-dir", DEFAULT_BACKUP_DIR)
    backup_dir = project_root / backup_dir_name

    results: dict = {}
    for provider in targets:
        provider_result: dict = {"provider": provider, "restored": False, "backup_used": None}

        if not backup_dir.exists():
            provider_result["error"] = f"backup directory not found: {backup_dir_name}"
            results[provider] = provider_result
            continue

        backups = sorted(
            backup_dir.glob(f"{provider}_*.zip"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if not backups:
            provider_result["error"] = f"no backup found for provider '{provider}'"
            results[provider] = provider_result
            continue

        latest_backup = backups[0]
        provider_result["backup_used"] = str(latest_backup.relative_to(project_root))
        provider_result["restored"] = _restore_single(
            project_root, provider, str(latest_backup.relative_to(project_root)),
            provider_config, config, log, dry_run,
        )

        results[provider] = provider_result

    return results
