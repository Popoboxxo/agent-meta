"""Sync execution pipeline for the default sync/--init mode (issue #481).

The ``_sync_stage_*`` helpers extracted from ``sync.py::_handle_sync`` live
here; ``_handle_sync`` (now in ``lib/cli_commands.py``, itself moved from
sync.py) keeps the thin orchestrator that calls the stages in the
original order. Extraction is purely mechanical (byte-identical behavior):

- ``log.*`` call order == output order (each stage owns exactly the block
  it was cut from),
- ``sys.exit(1)`` paths stay inside the stages,
- mutable accumulators (``mcp_gitignore_extras``, ``base_gitignore_entries``,
  ``env_gitignore``) cross stage boundaries by reference, exactly like the
  original local variables,
- ``provider_variables`` reference-sharing semantics (shallow copy only for
  ``orchestrator.provider-overrides.<Provider>.mode``; the shared
  ``variables`` dict is never mutated except ``PIPELINE_DETAILS_DIR``) are
  preserved verbatim.

Moved helpers found domain homes elsewhere: ``sync_knowledge_engine`` in
``lib/knowledge.py``, ``_probe_inactive_plugins`` in ``lib/plugins.py``,
``_collect_skill_gitignore_entries`` in ``lib/gitignore.py`` (this module
imports them back for the stage bodies).

Only stdlib + lib imports at top level (guard:
``tests/test_import_acyclicity.py``); the import direction is
``sync.py -> lib.sync_pipeline`` and must never be reversed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib.agent_sync import sync_agents_for_provider
from lib.commands import sync_commands_for_provider
from lib.config import (
    _orch_mode_flags,
    _resolve_orch_mode,
    fill_defaults,
    load_config,
)
from lib.config_audit import audit_config
from lib.context import (
    ensure_gitignore_entries,
    init_claude_personal,
    init_settings_json,
    init_settings_local_json,
    sync_claude_md_static,
    sync_context_for_provider,
    sync_prompts_for_continue,
    sync_snippets_for_provider,
)
from lib.deactivation import is_provider_active
from lib.dod import resolve_dod, resolve_release_gates
from lib.external_tools import (
    generate_external_tool_artifacts,
    render_injection_drift_artifacts,
    scan_injection_drift,
)
from lib.gitignore import (
    _collect_skill_gitignore_entries,
    collect_provider_roots,
    compute_base_gitignore_entries,
    filter_redundant_provider_entries,
)
from lib.hook_plugins import sync_hook_lib, sync_release_gates
from lib.hooks import sync_hooks
from lib.io import SyncError
from lib.isolation import sync_provider_isolation
from lib.knowledge import sync_knowledge_engine
from lib.log import SyncLog
from lib.mcp import generate_mcp_artifacts, sync_secrets_template
from lib.pipelines import (
    apply_overrides,
    load_quality_pipelines,
    resolve_pipeline_details_dir,
    sync_pipeline_detail_files,
)
from lib.platform import load_platform_config
from lib.plugins import _probe_inactive_plugins
from lib.providers import (
    load_providers_config,
    resolve_context_filename,
    resolve_providers,
)
from lib.rules import resolve_rules, sync_rules, sync_speech_mode
from lib.skills import (
    check_pinned_commits,
    load_external_skills_config,
    sync_external_skills_for_provider,
)
from lib.viz import (
    get_gitignore_entries as viz_gitignore_entries,
)


# ---------------------------------------------------------------------------
# Sync pipeline stages (execution order)
# ---------------------------------------------------------------------------


def _sync_stage_config_and_presets(
    agent_meta_root: Path, project_root: Path, config_path: Path,
    config: dict, platforms: list, args: argparse.Namespace, log: SyncLog,
) -> tuple[dict, dict, list, str, dict | None]:
    """Stages 1+2: config auto-fill + reload, provider/DoD/rules-preset
    resolution + logging, platform-config variables.

    Returns ``(config, provider_config, providers, mode, platform_vars)`` —
    the reloaded config must flow back to ``ctx.config`` via the
    orchestrator's final write-back (the original rebind of the local
    ``config`` variable, sync.py L1276).
    """
    # Auto-fill missing config fields with defaults (silent mode — only logs additions)
    fill_defaults(config_path, agent_meta_root, log, args.dry_run, silent=True)
    # Reload config after auto-fill to pick up newly written defaults
    config = load_config(config_path)

    provider_config = load_providers_config(agent_meta_root)
    providers = resolve_providers(config, provider_config)
    mode = "init" if args.init else "sync"
    log.note("providers", "active: " + ", ".join(providers))
    # Log resolved DoD
    preset_name = config.get("dod-preset", "full") or "full"
    dod_resolved = resolve_dod(config, agent_meta_root)
    dod_summary = ", ".join(f"{k}: {v}" for k, v in dod_resolved.items())
    log.note("DoD", f"preset '{preset_name}' -> {dod_summary}")
    # Log resolved rules-preset
    rules_preset_name = config.get("rules-preset", "default")
    rules_resolved = resolve_rules(config, agent_meta_root)
    if rules_resolved:
        rules_summary = ", ".join(
            f"{r}: {'+'.join(k for k, v in opts.items() if v is not False and v != 'skip') or 'alwaysApply=false'}"
            for r, opts in rules_resolved.items()
        )
        log.note("rules", f"preset '{rules_preset_name}' -> {rules_summary}")
    else:
        log.note("rules", f"preset '{rules_preset_name}' -> all alwaysApply (default)")
    # Load platform-config variables ({{platform.*}} placeholders)
    platform_vars = load_platform_config(agent_meta_root, project_root, platforms, log)
    if platform_vars is not None:
        log.note("platform-config", f"loaded {len(platform_vars)} platform variable(s) for: {', '.join(platforms)}")
    return config, provider_config, providers, mode, platform_vars


def _sync_stage_claude_base(
    agent_meta_root: Path, project_root: Path, config: dict,
    provider_config: dict, providers: list, variables: dict,
    args: argparse.Namespace, log: SyncLog,
) -> tuple[bool, dict, list, list]:
    """Stage 3: Claude-gated base syncs + gitignore/env baselines.

    Returns ``(is_claude, gitignore_cfg, base_gitignore_entries,
    env_gitignore)``; the two lists are later mutated by the gitignore
    stage (stage 11) through the same object references.
    """
    is_claude = "Claude" in providers
    gitignore_cfg = config.get("gitignore", {})
    # Base entries of the managed .gitignore block (local/generated/settings
    # categories, custom entries and — when gitignore.ignore-provider-dirs is
    # enabled — whole provider-root directories). Extracted to lib/gitignore.py
    # for unit-testability (issue #557); Claude-gated exactly as before: without
    # Claude only the additive per-provider path further below runs.
    base_gitignore_entries: list[str] = (
        compute_base_gitignore_entries(providers, provider_config, gitignore_cfg)
        if is_claude
        else []
    )
    if is_claude:
        sync_claude_md_static(agent_meta_root, project_root, config, variables, log, args.dry_run)
        init_claude_personal(agent_meta_root, project_root, log, args.dry_run)
    init_settings_json(agent_meta_root, project_root, log, args.dry_run,
                       providers=providers, provider_config=provider_config,
                       variables=variables)
    init_settings_local_json(agent_meta_root, project_root, log, args.dry_run,
                             providers=providers, provider_config=provider_config,
                             variables=variables)
    # Auto-generated env scripts — always gitignored (may contain defaults/secrets).
    env_gitignore = [".meta-config/env.ps1", ".meta-config/env.sh",
                     ".meta-config/env.unset.ps1", ".meta-config/env.unset.sh"]
    sync_secrets_template(agent_meta_root, project_root, config, log, args.dry_run)
    return is_claude, gitignore_cfg, base_gitignore_entries, env_gitignore


def _sync_stage_contexts(
    agent_meta_root: Path, project_root: Path, config: dict,
    provider_config: dict, providers: list, variables: dict,
    args: argparse.Namespace, log: SyncLog,
) -> tuple[bool, bool, list]:
    """Stage 4: per-provider context sync loop.

    Returns ``(debug_mode, allow_committed_secrets, mcp_gitignore_extras)`` —
    the flags feed stage 6, the accumulator list is appended to by stage 6
    (by reference) and read by stage 11.
    """
    # Per-provider sync
    debug_mode = config.get("debug-mode", False)
    if debug_mode:
        log.note("debug-mode", "active — injecting debug block into all agents")
    allow_committed_secrets = config.get("allow-committed-secrets", False)
    mcp_gitignore_extras: list[str] = []
    for provider in providers:
        pc = provider_config[provider]
        log.provider_header(provider)
        if not is_provider_active(config, provider):
            log.note("deactivation", f"provider '{provider}' is deactivated — skipping all output")
            continue
        # Per-provider orchestrator.mode override: orchestrator.provider-overrides.<Provider>.mode
        # takes precedence over the global orchestrator.mode for this provider's
        # generated agents/rules only. Build a shallow copy of `variables` with the
        # recomputed ORCH_MODE_* flags — the shared `variables` dict is never mutated.
        _orch_config = config.get("orchestrator", {})
        _provider_override = _orch_config.get("provider-overrides", {}).get(provider)
        if _provider_override and _provider_override.get("mode") is not None:
            provider_variables = dict(variables)
            provider_variables.update(
                _orch_mode_flags(_resolve_orch_mode(_orch_config, _provider_override))
            )
        else:
            provider_variables = variables
        sync_context_for_provider(agent_meta_root, project_root, config, provider_variables,
                                  log, args.dry_run, provider, provider_config)
    return debug_mode, allow_committed_secrets, mcp_gitignore_extras


def _sync_stage_legacy_cleanup(
    project_root: Path, config: dict, provider_config: dict,
    providers: list, args: argparse.Namespace, log: SyncLog,
) -> None:
    """Stage 5: cleanup legacy files for removed providers."""
    # Cleanup legacy files for removed providers
    all_known_providers = provider_config.keys()
    active_context_files = set()
    for prov in providers:
        if prov == "providers": continue
        if is_provider_active(config, prov):
            pc = provider_config.get(prov, {})
            c_file = resolve_context_filename(pc.get("context_file", f"{prov.upper()}.md"), prov, pc)
            active_context_files.add(c_file)

    for prov in all_known_providers:
        if prov == "providers": continue # Skip the top-level key if present
        if prov not in providers or not is_provider_active(config, prov):
            pc = provider_config.get(prov, {})

            # Default paths if missing from config
            a_dir = pc.get("agents_dir", f".{prov.lower()}/agents")
            c_file = resolve_context_filename(pc.get("context_file", f"{prov.upper()}.md"), prov, pc)

            agents_dir = project_root / a_dir
            context_file = project_root / c_file

            if agents_dir.exists():
                log.action("DELETE", str(agents_dir.relative_to(project_root)), f"provider {prov} removed")
                if not args.dry_run:
                    import shutil
                    shutil.rmtree(agents_dir)
            if context_file.exists() and c_file not in active_context_files:
                log.action("DELETE", str(context_file.relative_to(project_root)), f"provider {prov} removed")
                if not args.dry_run:
                    context_file.unlink()

            # Cleanup parent provider directory if empty. Resolved from this
            # provider's own isolation-dirs (config/ai-providers.yaml) instead
            # of a hardcoded per-provider string exception (issue #631) — e.g.
            # Copilot's ".github/copilot/" doesn't follow the ".<name>/"
            # convention every other provider uses.
            _isolation_dirs = pc.get("isolation-dirs") or [f".{prov.lower()}/"]
            prov_dir_name = _isolation_dirs[0].rstrip("/")
            prov_dir = project_root / prov_dir_name
            if prov_dir.exists() and not args.dry_run:
                import shutil
                try:
                    remaining_files = [f for f in prov_dir.rglob("*") if f.is_file()]
                    if not remaining_files:
                        shutil.rmtree(prov_dir)
                        log.action("DELETE", str(prov_dir.relative_to(project_root)), f"empty provider directory {prov} pruned")
                except OSError as e:
                    # Best-effort cleanup only — a permission error or a
                    # concurrent modification of prov_dir must not abort the
                    # rest of the sync. Safe to continue: leaving a non-empty
                    # or now-unreadable directory behind has no correctness
                    # impact (it's just a stale/leftover provider directory).
                    # Suppression rationale: SyncLog.debug(target, msg) isn't
                    # logging.debug(msg, *args) — same linter false positive
                    # class as pre-#574 SyncLog.info.
                    log.debug("provider-cleanup", f"could not prune '{prov_dir}': {type(e).__name__}: {e}")  # noqa: PLE1205


def _sync_stage_per_provider(
    agent_meta_root: Path, project_root: Path, config: dict,
    provider_config: dict, providers: list, variables: dict,
    platform_vars: dict | None, debug_mode: bool, allow_committed_secrets: bool,
    mcp_gitignore_extras: list, args: argparse.Namespace, log: SyncLog,
) -> None:
    """Stage 6: per-provider main loop (pipeline details, agents, Continue
    prompts, rules, MCP, external tools, hooks, commands, snippets,
    external skills).

    ``provider_variables`` reference-sharing semantics are preserved verbatim:
    a shallow copy of ``variables`` is made only for
    ``orchestrator.provider-overrides.<Provider>.mode``; otherwise the shared
    dict is used as-is, so the ``PIPELINE_DETAILS_DIR`` write below mutates
    the shared ``variables`` exactly as the original monolithic handler did.
    """
    for provider in providers:
        pc = provider_config[provider]
        if not is_provider_active(config, provider):
            continue

        _orch_config = config.get("orchestrator", {})
        _provider_override = _orch_config.get("provider-overrides", {}).get(provider)
        if _provider_override and _provider_override.get("mode") is not None:
            provider_variables = dict(variables)
            provider_variables.update(
                _orch_mode_flags(_resolve_orch_mode(_orch_config, _provider_override))
            )
        else:
            provider_variables = variables

        # PIPELINE_DETAILS_DIR + on-demand pipeline stage-detail files —
        # the lean, always-on-token-saving counterpart to
        # PIPELINE_DETAIL_BLOCKS (which inlines every pipeline's full
        # stage detail directly into orchestrator.md; fine for the
        # ORCH_MODE_STRICT/ADVISORY subagent, too expensive for
        # main-chat mode's always-loaded use-orchestrator.md / embedded
        # context file). One file per active pipeline; main_chat Read()s
        # the relevant one only once it actually routes there. Computed
        # centrally here (not inside sync_rules()) so it also reaches
        # providers without a native rules_dir (e.g. Opencode), whose
        # rules content is embedded into the context file instead
        # (sync_context_for_provider / _build_managed_block).
        pipeline_details_dir = resolve_pipeline_details_dir(pc, provider)
        provider_variables["PIPELINE_DETAILS_DIR"] = pipeline_details_dir
        pipelines_for_details = apply_overrides(
            load_quality_pipelines(str(agent_meta_root)), config.get("quality-pipelines", {})
        )
        if pipelines_for_details:
            sync_pipeline_detail_files(
                pipelines_for_details, provider, project_root / pipeline_details_dir,
                project_root, resolve_dod(config, agent_meta_root), log, args.dry_run,
            )

        sync_agents_for_provider(agent_meta_root, project_root, config, provider_variables,
                                 log, args.dry_run, provider, provider_config,
                                 platform_vars=platform_vars,
                                 debug_mode=debug_mode)
        if provider == "Continue":
            sync_prompts_for_continue(agent_meta_root, project_root, config,
                                      provider_variables, log, args.dry_run,
                                      provider_config=provider_config)
        if pc.get("has_rules", False):
            sync_rules(agent_meta_root, project_root, config, log, args.dry_run,
                       platform_vars=platform_vars, variables=provider_variables,
                       rules_dir=pc.get("rules_dir"), provider=provider,
                       provider_config=provider_config)
            sync_speech_mode(agent_meta_root, project_root, config, log, args.dry_run,
                             rules_dir=pc.get("rules_dir"))
        # MCP: generate rule files + provider configs + collect gitignore entries
        try:
            mcp_extras = generate_mcp_artifacts(
                agent_meta_root, project_root, config, provider_config,
                log, args.dry_run, provider, rules_dir=pc.get("rules_dir"),
                allow_committed_secrets=allow_committed_secrets,
            )
        except SyncError as exc:
            print(f"\n  !!  MCP sync aborted: {exc}", file=sys.stderr)
            sys.exit(1)
        for entry in mcp_extras:
            if entry not in mcp_gitignore_extras:
                mcp_gitignore_extras.append(entry)
        # External tools: generate rule files for active locally-installed CLI tools
        try:
            generate_external_tool_artifacts(
                agent_meta_root, project_root, config, provider_config,
                log, args.dry_run, provider, rules_dir=pc.get("rules_dir"),
            )
        except SyncError as exc:
            print(f"\n  !!  External-tools sync aborted: {exc}", file=sys.stderr)
            sys.exit(1)
        if pc.get("has_hooks", False):
            # sync_hooks()/sync_hook_lib()/sync_release_gates() each check
            # provider_hooks_supported(pc) internally (issue #630): with
            # has_hooks: true but no verified hook_protocol, they deploy
            # nothing new but still clean up any previously-deployed hooks.
            sync_hooks(agent_meta_root, project_root, config, log, args.dry_run,
                       provider=provider, provider_config=provider_config)
            sync_hook_lib(agent_meta_root, project_root, config, log, args.dry_run,
                          provider=provider, provider_config=provider_config)
            sync_release_gates(agent_meta_root, project_root, config, log, args.dry_run,
                                provider=provider, provider_config=provider_config,
                                release_gates_resolved=resolve_release_gates(config, agent_meta_root))
        else:
            log.note("hooks", f"skipped for {provider} — not supported")
        if pc.get("has_commands", False):
            sync_commands_for_provider(agent_meta_root, project_root, config, log,
                                       args.dry_run, provider,
                                       provider_config=provider_config,
                                       variables=variables)
        # Sync snippets and external skills per provider
        sync_snippets_for_provider(agent_meta_root, project_root, config, log, args.dry_run,
                                   provider, provider_config)
        sync_external_skills_for_provider(agent_meta_root, project_root, config, variables,
                                          log, args.dry_run, provider, provider_config)


def _sync_stage_drift_and_plugins(
    agent_meta_root: Path, project_root: Path, config: dict,
    provider_config: dict, args: argparse.Namespace, log: SyncLog,
) -> None:
    """Stage 7: injection-drift scan + plugin availability probe."""
    # External-tool injection governance: once per sync run (not per
    # provider) — diffs each active provider's managed dirs against
    # permitted-injections, warns on anything undeclared.
    try:
        drift = scan_injection_drift(agent_meta_root, project_root, config, provider_config)
        render_injection_drift_artifacts(drift, project_root, provider_config, log, args.dry_run)
    except SyncError as exc:
        print(f"\n  !!  External-tool injection drift scan aborted: {exc}", file=sys.stderr)
        sys.exit(1)
    # Sync-time plugin availability probe (Layer 3 hint): informational-only
    # nudge for catalog plugins that are locally available but not activated.
    # Skipped in --check (CI) mode to keep drift-check output stable. Read-only
    # (probe_plugin_availability only does shutil.which/HTTP HEAD) but wrapped
    # like the other optional summary blocks -- must never break a sync.
    if not args.check:
        try:
            for _hint in _probe_inactive_plugins(agent_meta_root, project_root, config):
                print(_hint)
        except Exception as exc:  # noqa: BLE001
            log.debug("plugin-probe", f"skipped: {type(exc).__name__}: {exc}")  # noqa: PLE1205


def _sync_stage_knowledge_and_isolation(
    agent_meta_root: Path, project_root: Path, config: dict,
    providers: list, provider_config: dict, args: argparse.Namespace, log: SyncLog,
) -> None:
    """Stages 8+9: knowledge-engine scaffolding + provider isolation."""
    # Knowledge Engine — Phase A scaffolding (no-op unless knowledge-engine.enabled)
    try:
        sync_knowledge_engine(agent_meta_root, project_root, config, log, args.dry_run)
    except SyncError as exc:
        print(f"\n  !!  Knowledge Engine sync aborted: {exc}", file=sys.stderr)
        sys.exit(1)
    # Provider isolation: hard-block cross-provider directory access
    isolation_mode = config.get("provider-isolation")
    if isolation_mode != "disabled":
        sync_provider_isolation(project_root, providers, provider_config, log, args.dry_run)
    else:
        log.skip("provider-isolation", "disabled in project.yaml")


def _sync_stage_external_skills_check(
    agent_meta_root: Path, config: dict, log: SyncLog,
) -> dict:
    """Stage 10: pinned-commit check + unknown/unapproved-skill warnings.

    Returns the loaded external-skills config; the gitignore stage reuses it
    for skill entries (same single load as the original monolithic handler).
    """
    # Check pinned commits + warn for unknown/unapproved skills in project config
    ext_config = load_external_skills_config(agent_meta_root)
    check_pinned_commits(ext_config, agent_meta_root, log)
    if "external-skills" in config:
        known_skills = set(ext_config.get("skills", {}).keys())
        known_repos = set(ext_config.get("repos", {}).keys())
        for skill_name in config["external-skills"]:
            if skill_name in known_repos:
                # It's a repo (e.g. awesome-claude-code) — implicit dependency, not a skill entry
                log.note("external-skills", f"'{skill_name}' is a framework repo (not a skill) — OK")
            elif skill_name not in known_skills:
                log.warning(f"external-skills: '{skill_name}' not found in skills-registry.yaml (neither skills nor repos) -- skipping")
            elif not ext_config["skills"][skill_name].get("approved", False):
                log.warning(f"external-skills: '{skill_name}' is not approved by meta-maintainer -- skipping")
    return ext_config


def _sync_stage_gitignore(
    project_root: Path, config: dict, provider_config: dict, providers: list,
    ext_config: dict, is_claude: bool, gitignore_cfg: dict,
    base_gitignore_entries: list, mcp_gitignore_extras: list,
    env_gitignore: list, args: argparse.Namespace, viz_cfg: dict, log: SyncLog,
) -> None:
    """Stage 11: .gitignore managed-block assembly.

    Receives the accumulators built by the earlier stages
    (``base_gitignore_entries`` from stage 2/3, ``mcp_gitignore_extras`` from
    stage 6, ``env_gitignore`` from stage 3) by reference — the viz-entry
    ``extend`` mutates the same list object the orchestrator passed in,
    exactly like the original local-variable flow.
    """
    # Update .gitignore managed block: base entries + per-provider entries + skill entries
    # Collect gitignore_entries from all active non-Claude providers
    extra_provider_entries: list[str] = []
    for _p in providers:
        if _p == "Claude":
            continue  # already in base_gitignore_entries
        _pc = provider_config.get(_p, {})
        if _pc.get("has_settings") and not _pc.get("gitignore_entries"):
            log.warning(f"provider '{_p}' has has_settings=true but no gitignore_entries — local settings may be accidentally committed")
        extra_provider_entries.extend(_pc.get("gitignore_entries", []))
    # Toggle mode (issue #557): provider-internal entries are redundant once the
    # whole provider root is ignored — drop them from the per-provider allowlist
    # too. Repo-root entries (e.g. AGENTS.personal.md) pass through unchanged.
    if gitignore_cfg.get("ignore-provider-dirs", False):
        extra_provider_entries = filter_redundant_provider_entries(
            extra_provider_entries,
            collect_provider_roots(providers, provider_config),
        )
    # Viz: add gitignore entries if viz mode is dynamic/full or viz is enabled
    viz_mode = args.viz_mode or viz_cfg.get("mode", "off")
    if viz_mode in ("dynamic", "full") or viz_cfg.get("enabled", False) or args.viz:
        viz_gitignore = viz_gitignore_entries()
        base_gitignore_entries.extend(viz_gitignore)

    if is_claude:
        skill_gitignore_entries = _collect_skill_gitignore_entries(config, ext_config, provider_config)
        all_gitignore_entries = (
            base_gitignore_entries + extra_provider_entries
            + skill_gitignore_entries + mcp_gitignore_extras
            + env_gitignore
        )
        ensure_gitignore_entries(project_root, log, args.dry_run,
                                 exact_entries=all_gitignore_entries)
    elif extra_provider_entries or mcp_gitignore_extras:
        # No Claude active but other providers have gitignore entries to manage
        ensure_gitignore_entries(project_root, log, args.dry_run,
                                 gitignore_entries=extra_provider_entries + mcp_gitignore_extras)


def _sync_stage_config_audit(agent_meta_root: Path, config_path: Path, log: SyncLog) -> None:
    """Stage 12: lightweight config-audit summary at the end of a sync."""
    # Lightweight config-audit summary at the end of a normal sync. Full
    # reporting stays opt-in via --audit-config; here we emit one log line
    # per non-empty category so projects do not silently keep stale or
    # broken config. Severity mapping mirrors --audit-config:
    #   roles_without_template    → ERROR
    #   templates_without_default → INFO
    #   deprecated_roles          → WARN (auto-fixable via --apply)
    #   orphaned_pipelines        → WARN
    # The audit itself must never break a sync — wrapped in try/except.
    try:
        _audit_report = audit_config(agent_meta_root, config_path)

        _missing = _audit_report.by_category("roles_without_template")
        if _missing:
            _names = ", ".join(sorted({i.role for i in _missing if i.role}))
            # SyncLog has no .error() level — emit as WARN with explicit
            # [ERROR] severity tag to keep parity with --audit-config output.
            log.warning(
                "config-audit [ERROR]: "
                f"{len(_missing)} role(s) without generic template: {_names}. "
                "Run: python scripts/sync.py --audit-config"
            )

        _templ_noref = _audit_report.by_category("templates_without_default")
        if _templ_noref:
            _names = ", ".join(sorted({i.role for i in _templ_noref if i.role}))
            log.note(
                "config-audit",
                f"{len(_templ_noref)} template(s) without role-defaults entry: {_names}."
            )

        _depr = _audit_report.deprecated_roles
        if _depr:
            log.warning(
                "config-audit: "
                f"{len(_depr)} deprecated role(s) still in project.yaml: "
                f"{', '.join(_depr)}. "
                "Run: python scripts/sync.py --audit-config --apply"
            )

        _orphans = _audit_report.by_category("orphaned_pipelines")
        if _orphans:
            _names = ", ".join(sorted({i.role for i in _orphans if i.role}))
            log.warning(
                "config-audit: "
                f"{len(_orphans)} orphaned pipeline reference(s): {_names}. "
                "Run: python scripts/sync.py --audit-config"
            )
    except Exception as exc:  # noqa: BLE001
        # Audit must never break a sync — degrade gracefully.
        log.note("config-audit", f"skipped (error: {exc})")
