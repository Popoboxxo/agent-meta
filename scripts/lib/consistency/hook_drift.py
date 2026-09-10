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

from ..hooks import (
    CLAUDE_HOOKS_DIR,
    collect_hook_sources,
    parse_hook_metadata,
    parse_hook_settings_command,
)
from ..io import read_json_lenient
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


def check_hook_enablement_consistency(
    project_root: Path, agent_meta_root: Path, config: dict, provider_config: dict
) -> list[Finding]:
    """Flag hooks that SHOULD guard tool calls but currently do not (#712, #714).

    "Should guard" is computed with the exact same enablement precedence
    ``sync_hooks()`` (lib/hooks.py) uses at deploy time: a hook's own
    ``# enabled_by_default:`` header, overridable per-project via
    ``project.yaml``'s ``hooks.<name>.enabled``. Two failure modes, both
    fail OPEN today (the tool call goes through unguarded, no error):

    - #712: the hook is enabled and listed in ``.agent-meta-managed``, but
      the deployed script file itself is gone (partial sync, manual
      deletion). ``bash <missing file>`` exits 127 before any guard logic
      runs -- a non-JSON, non-zero PreToolUse exit is non-blocking.
    - #714: the hook is enabled and the file is deployed, but no
      settings.json command entry actually invokes it -- the guard exists
      on disk but nothing ever runs it.

    Both share the same "what SHOULD be active" computation, so they are
    checked together in one function (see docs/superpowers/plans/
    2026-09-10-bug-batch-703-720.md Task 1 for why #712/#714 were merged).

    Deliberately excludes the viz-log auto-enable special case
    (``sync_hooks()``'s ``viz_active`` branch) -- a false negative there
    (viz-log silently un-registered while viz is on) is safer than the
    false-positive risk of duplicating that branch's logic here.
    # ponytail: viz-log auto-enable not modeled here -- upgrade path: pass
    # viz_cfg through if a real viz-log drift report is ever needed.
    """
    findings: list[Finding] = []
    platforms = config.get("platforms", [])
    sources = collect_hook_sources(agent_meta_root, platforms)
    if not sources:
        return findings
    project_hooks_cfg = config.get("hooks", {})
    # Parse each source's metadata once up front, not once per provider inside
    # the loop below (matching check_stale_deployed_hooks' source_versions).
    source_metas = {
        source_path: parse_hook_metadata(source_path.read_text(encoding="utf-8"))
        for source_path, _ in sources
    }

    seen_dirs: set[Path] = set()
    for pc in provider_config.values():
        hooks_dir_rel = pc.get("hooks_dir", CLAUDE_HOOKS_DIR)
        settings_file_rel = pc.get("settings_file", ".claude/settings.json")
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
        registered = _registered_hook_stems(project_root, pc, hooks_dir_rel)

        for source_path, output_name in sources:
            if output_name not in managed:
                continue  # not managed for this project -- not our call
            meta = source_metas[source_path]
            hook_stem = Path(output_name).stem
            should_be_active = project_hooks_cfg.get(hook_stem, {}).get(
                "enabled", meta.get("enabled_by_default", "false").lower() == "true"
            )
            if not should_be_active:
                continue

            deployed = target_dir / output_name
            rel_deployed = str(deployed.relative_to(project_root))
            if not deployed.is_file():
                findings.append(Finding(
                    Severity.ERROR,
                    "hooks.enabled-but-missing-file",
                    rel_deployed,
                    f"Hook '{output_name}' is enabled and listed in "
                    f"{managed_index.relative_to(project_root)}, but the deployed "
                    "file is missing -- any tool call this hook should guard now "
                    "goes through UNGUARDED (issue #712).",
                    "python scripts/sync.py",
                ))
            elif hook_stem not in registered:
                findings.append(Finding(
                    Severity.ERROR,
                    "hooks.enabled-but-not-registered",
                    rel_deployed,
                    f"Hook '{output_name}' is enabled and deployed, but its "
                    "registration artifact has no matching entry -- the "
                    "guard script exists but never runs (issue #714).",
                    "python scripts/sync.py",
                ))
    return findings


def _registered_hook_stems(
    project_root: Path, provider_cfg: dict, hooks_dir_rel: str
) -> set[str]:
    """Return the stems of hooks currently registered for a provider.

    The registration ARTIFACT and format are provider-agnostic: they follow
    the provider's ``hook_protocol`` capability flag, mirroring sync's own
    ``_HOOK_REGISTRATION_WRITERS`` dispatch (lib/hooks.py) rather than
    assuming Claude's settings.json shape for everyone. Two protocols exist
    today; an unknown/absent protocol falls back to the same default sync
    uses (``claude-code-json``), so a new provider speaking an already
    implemented protocol needs zero changes here.

    - ``antigravity-hooks-json``: hooks live in ``hooks_config_file`` as
      top-level keys (the hook-name stem itself).
    - ``claude-code-json`` (and the default): hooks are ``bash
      <hooks_dir>/<file>`` command strings inside ``settings_file``'s
      ``hooks`` block; the stem is derived from ``<file>``.
    """
    protocol = provider_cfg.get("hook_protocol")
    if protocol == "antigravity-hooks-json":
        config_rel = provider_cfg.get("hooks_config_file")
        if not config_rel:
            return set()
        data = read_json_lenient(project_root / config_rel)
        if not isinstance(data, dict):
            return set()
        return {str(k) for k in data}

    settings_rel = provider_cfg.get("settings_file", ".claude/settings.json")
    settings_path = project_root / settings_rel
    if not settings_path.is_file():
        return set()
    data = read_json_lenient(settings_path)
    if not isinstance(data, dict):
        return set()
    stems: set[str] = set()
    for event_entries in data.get("hooks", {}).values():
        if not isinstance(event_entries, list):
            continue
        for entry in event_entries:
            if not isinstance(entry, dict):
                continue
            for h in entry.get("hooks", []):
                if not isinstance(h, dict):
                    continue
                filename = parse_hook_settings_command(
                    str(h.get("command", "")), hooks_dir_rel
                )
                if filename:
                    stems.add(Path(filename).stem)
    return stems
