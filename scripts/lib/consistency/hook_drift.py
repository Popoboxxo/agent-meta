"""Consistency check: deployed hook copies vs. current hooks/1-generic/ source.

Platform-overrides (2-platform/) have had a staleness warning since issue #560
(``stale_platform_overrides`` in config_audit.py): a ``based-on:
"1-generic/<role>.md@<version>"`` pin that has fallen behind the current
generic template is flagged. Hooks deployed into a project (``.claude/hooks/``
or another provider's ``hooks_dir``) had no equivalent -- only a managed-index
based stale-*file* cleanup (deletes hooks no longer part of the managed set),
not a version-*drift* comparison against the still-current hooks/1-generic/
source (issue #630). A project that does not re-run sync.py after a hook
source bump keeps running the old script version indefinitely, unnoticed.
"""

from __future__ import annotations

from pathlib import Path

from ..hooks import CLAUDE_HOOKS_DIR, collect_hook_sources, parse_hook_metadata
from .report import Finding, Severity


def check_stale_deployed_hooks(
    project_root: Path, agent_meta_root: Path, config: dict, provider_config: dict
) -> list[Finding]:
    """Warn when a deployed hook's ``# version:`` header is behind its source.

    Compares every provider's deployed ``<hooks_dir>/*.sh`` against the
    current ``hooks/1-generic/`` (+ 0-external/2-platform layering) source
    with the same output filename. Only hooks tracked in the target's
    ``.agent-meta-managed`` index are compared -- project-owned hook scripts
    are never touched or judged by this check.
    """
    findings: list[Finding] = []
    platforms = config.get("platforms", [])
    sources = collect_hook_sources(agent_meta_root, platforms)
    if not sources:
        return findings
    source_versions = {
        name: parse_hook_metadata(src.read_text(encoding="utf-8")).get("version")
        for src, name in sources
    }

    seen_dirs: set[Path] = set()
    for pc in provider_config.values():
        hooks_dir_rel = pc.get("hooks_dir", CLAUDE_HOOKS_DIR)
        target_dir = project_root / hooks_dir_rel
        if target_dir in seen_dirs or not target_dir.is_dir():
            continue
        seen_dirs.add(target_dir)

        managed_index = target_dir / ".agent-meta-managed"
        if not managed_index.is_file():
            continue
        managed = {
            line.strip() for line in managed_index.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }

        for name, source_version in source_versions.items():
            if not source_version or name not in managed:
                continue
            deployed = target_dir / name
            if not deployed.is_file():
                continue
            deployed_version = parse_hook_metadata(
                deployed.read_text(encoding="utf-8")
            ).get("version")
            if deployed_version and deployed_version != source_version:
                findings.append(Finding(
                    Severity.WARNING,
                    "hooks.stale-deployed-version",
                    str(deployed.relative_to(project_root)),
                    f"Deployed hook '{name}' is at version {deployed_version}, but "
                    f"the current source (hooks/1-generic/{name}) is at "
                    f"{source_version} -- run sync.py to pick up the update.",
                    "python scripts/sync.py",
                ))
    return findings
