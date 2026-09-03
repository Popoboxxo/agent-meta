"""Hook plugin-directory sync: release-gates/ and lib/ subdirectories.

Split out of hooks.py (issue #630/#631 wave pushed it past the 600-line
convention limit) — both functions here share the same "always-copy,
.agent-meta-managed-tracked, never-touch-project-owned-files" pattern for a
managed *subdirectory* of a provider's hooks_dir, as opposed to sync_hooks()
itself which manages the top-level hook scripts and their settings.json
registration.
"""
from __future__ import annotations

from pathlib import Path

from .hooks import CLAUDE_HOOKS_DIR, collect_hook_sources, parse_hook_metadata
from .io import safe_path, write_checked
from .log import SyncLog
from .providers import provider_hooks_supported

RELEASE_GATES_SUBDIR = "release-gates"
HOOK_LIB_SUBDIR = "lib"


def sync_release_gates(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str = "Claude",
    provider_config: dict | None = None,
    release_gates_resolved: dict | None = None,
) -> None:
    """Copy release-gate plugin scripts to <hooks_dir>/release-gates/.

    Plugin architecture (issue #558): hooks/1-generic/pre-release-check.sh is
    a pure dispatcher — at runtime it globs and runs every *.sh file
    alongside it in release-gates/, with no framework-side registry. This
    function only deploys the framework-shipped ("built-in") gate scripts
    from hooks/*/release-gates/ (same 0-external / 1-generic / 2-platform
    layering as collect_hook_sources() uses for regular hooks).

    Projects extend the pipeline by dropping their own *.sh files directly
    into <hooks_dir>/release-gates/ — those are NEVER touched here (not
    added to .agent-meta-managed), exactly like project-owned hooks created
    via create_hook(). The dispatcher picks them up automatically, no
    framework change required.

    Each shipped gate script may reference a single sync-time placeholder,
    ``{{RELEASE_GATE_ENABLED_DEFAULT}}``, baked to "true"/"false" from
    ``release_gates_resolved`` (output of dod.resolve_release_gates()):
    project.yaml `release-gates.<name>.enabled` > dod-preset default > that
    gate script's own `enabled_by_default` header (fallback when the name is
    in neither source).
    """
    pc = (provider_config or {}).get(provider, {})
    hooks_dir_rel = pc.get("hooks_dir", CLAUDE_HOOKS_DIR)

    platforms = config.get("platforms", [])
    sources = collect_hook_sources(agent_meta_root, platforms, subdir=RELEASE_GATES_SUBDIR)
    # See sync_hooks() (issue #630): has_hooks: true alone doesn't mean the
    # provider's hook_protocol is verified -- deploy nothing new, but still
    # fall through so previously-deployed gates get cleaned up below. Only
    # gated when a real provider_config was supplied -- callers that invoke
    # this directly without one (e.g. low-level unit tests) get the
    # pre-#630 always-deploy behavior, matching the provider="Claude" default.
    if provider_config is not None and not provider_hooks_supported(pc):
        sources = []

    target_dir = project_root / hooks_dir_rel / RELEASE_GATES_SUBDIR
    managed_index_path = target_dir / ".agent-meta-managed"

    previously_managed: set[str] = set()
    if managed_index_path.exists():
        for line in managed_index_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                previously_managed.add(line.strip())

    if not sources and not previously_managed:
        return  # nothing shipped, nothing to clean up — leave any project-owned gates alone

    now_managed: set[str] = set()
    resolved = release_gates_resolved or {}

    if not dry_run and sources:
        target_dir.mkdir(parents=True, exist_ok=True)

    for source_path, output_name in sources:
        target_path = safe_path(target_dir, output_name)
        source_content = source_path.read_text(encoding="utf-8")
        # Same sync-time-placeholder pattern as {{AGENT_META_PROVIDER}} in
        # sync_hooks() — no-op for scripts that don't reference it.
        source_content = source_content.replace("{{AGENT_META_PROVIDER}}", provider)
        meta = parse_hook_metadata(source_content)
        gate_stem = Path(output_name).stem

        enabled_default = resolved.get(gate_stem)
        if enabled_default is None:
            enabled_default = meta.get("enabled_by_default", "false").lower() == "true"
        source_content = source_content.replace(
            "{{RELEASE_GATE_ENABLED_DEFAULT}}",
            "true" if enabled_default else "false",
        )

        # Provider filter: skip gate script if it declares a specific provider that doesn't match
        gate_provider = meta.get("provider", "")
        if gate_provider and gate_provider != provider:
            log.skip(str(target_path.relative_to(project_root)),
                     f"provider-specific release gate ({gate_provider} only)")
            continue

        now_managed.add(output_name)
        rel_out = str(target_path.relative_to(project_root))
        rel_source = str(source_path.relative_to(agent_meta_root))
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if write_checked(target_path, source_content, log, rel_source, dry_run=dry_run):
                log.action("COPY", rel_out, rel_source)
            else:
                log.skip(rel_out, "unchanged")
        except Exception as exc:
            log.warning(f"Failed to deploy release gate {rel_out}: {exc}")
            continue

    # Remove stale shipped gate scripts — never touches project-owned custom
    # gates (not tracked in .agent-meta-managed in the first place).
    if target_dir.exists():
        for existing in sorted(target_dir.glob("*.sh")):
            if existing.name not in now_managed and existing.name in previously_managed:
                log.action("DELETE", str(existing.relative_to(project_root)),
                           "release gate removed from agent-meta sources")
                if not dry_run:
                    existing.unlink()

    if not dry_run and now_managed:
        managed_index_path.parent.mkdir(parents=True, exist_ok=True)
        managed_index_path.write_text(
            "\n".join(sorted(now_managed)) + "\n", encoding="utf-8"
        )


def sync_hook_lib(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str = "Claude",
    provider_config: dict | None = None,
) -> None:
    """Copy shared hook helper scripts to <hooks_dir>/lib/.

    Issue #601: several hook scripts duplicated the same JSON-parsing
    Python heredoc. hooks/1-generic/lib/hook_common.sh centralizes the
    common helpers (JSON field extraction, python3/python resolution,
    credential redaction, audit-log append+rotation) as functions the
    individual hook scripts `source`. This is plain library code, not a
    hook — never registered in settings.json, no `event`/`matcher`
    metadata expected on its files.

    Same 0-external / 1-generic / 2-platform layering as
    collect_hook_sources() (via the ``subdir`` parameter), same
    always-copied / .agent-meta-managed-tracked / never-touch-project-owned-
    files pattern as sync_release_gates(). Security-boundary hooks
    (orchestrator-guard.sh, dod-push-check.sh) fail CLOSED if this file is
    missing when they try to source it (issue #595) — so this function
    must run in the same sync pass as sync_hooks(), never independently.
    """
    pc = (provider_config or {}).get(provider, {})
    hooks_dir_rel = pc.get("hooks_dir", CLAUDE_HOOKS_DIR)

    platforms = config.get("platforms", [])
    sources = collect_hook_sources(agent_meta_root, platforms, subdir=HOOK_LIB_SUBDIR)
    # See sync_hooks() (issue #630): no verified hook_protocol -> nothing
    # sources this lib anymore, clean up any previously-deployed copy. Only
    # gated when a real provider_config was supplied -- see sync_release_gates()
    # for why (test/low-level callers without one keep pre-#630 behavior).
    if provider_config is not None and not provider_hooks_supported(pc):
        sources = []

    target_dir = project_root / hooks_dir_rel / HOOK_LIB_SUBDIR
    managed_index_path = target_dir / ".agent-meta-managed"

    previously_managed: set[str] = set()
    if managed_index_path.exists():
        for line in managed_index_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                previously_managed.add(line.strip())

    if not sources and not previously_managed:
        return  # nothing shipped, nothing to clean up

    now_managed: set[str] = set()

    if not dry_run and sources:
        target_dir.mkdir(parents=True, exist_ok=True)

    for source_path, output_name in sources:
        target_path = safe_path(target_dir, output_name)
        source_content = source_path.read_text(encoding="utf-8")

        now_managed.add(output_name)
        rel_out = str(target_path.relative_to(project_root))
        rel_source = str(source_path.relative_to(agent_meta_root))
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if write_checked(target_path, source_content, log, rel_source, dry_run=dry_run):
                log.action("COPY", rel_out, rel_source)
            else:
                log.skip(rel_out, "unchanged")
        except Exception as exc:
            log.warning(f"Failed to deploy hook lib file {rel_out}: {exc}")
            continue

    # Remove stale shipped lib files — never touches project-owned files
    # dropped directly into <hooks_dir>/lib/ (not tracked here).
    if target_dir.exists():
        for existing in sorted(target_dir.glob("*.sh")):
            if existing.name not in now_managed and existing.name in previously_managed:
                log.action("DELETE", str(existing.relative_to(project_root)),
                           "hook lib file removed from agent-meta sources")
                if not dry_run:
                    existing.unlink()

    if not dry_run and now_managed:
        managed_index_path.parent.mkdir(parents=True, exist_ok=True)
        managed_index_path.write_text(
            "\n".join(sorted(now_managed)) + "\n", encoding="utf-8"
        )
