"""CLI command layer for sync.py (issue #481 extraction).

Holds the symbols sync.py dispatches to: the ``--validate`` helpers, the
early-return CLI modes and shared-context builder (:func:`_build_context`),
the mutable dispatch state (:class:`_SyncContext`), the ``_handle_*`` mode
handlers and the common post-dispatch tail. Every symbol is moved verbatim
from scripts/sync.py (byte-identical behavior):

- ``log.*`` call order == stdout/sync.log order,
- ``sys.exit`` paths stay inside the handlers/tail (no return-code
  refactorings),
- the ``_SyncContext`` contract is unchanged: each handler reads the fields
  it needs and writes back ``mode`` (always) and ``config`` (only when it
  reloads the config).

Import direction is ``sync.py -> lib.cli_commands`` and must never be
reversed (guard: ``tests/test_import_acyclicity.py``). Import style mirrors
``lib/sync_pipeline.py`` (absolute ``from lib.x import ...`` at top level,
lazy imports inside function bodies preserved as-is).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from lib.backup import (
    create_backup,
    delete_backup,
    list_backups,
    prune_backups,
    restore_backup,
)
from lib.commands import create_command
from lib.config import (
    build_variables,
    fill_defaults,
    load_config,
    read_git_version,
    read_version,
)
from lib.config_audit import apply_audit, audit_config, format_report
from lib.context import only_variables, sync_context_for_provider
from lib.deactivation import (
    activate_providers,
    deactivate_providers,
    get_deactivation_status,
    resolve_deactivation_targets,
    update_deactivation_config,
)
from lib.dod import resolve_dod
from lib.extensions import create_extension, update_extensions
from lib.hooks import create_hook
from lib.io import SyncError
from lib.log import SyncLog
from lib.pipelines import (
    apply_overrides,
    load_quality_pipelines,
    resolve_pipeline_details_dir,
    sync_pipeline_detail_files,
)
from lib.plugin_test import run_plugin_test
from lib.plugins import load_plugin_catalog
from lib.providers import load_providers_config, resolve_providers
from lib.roles import build_role_map
from lib.rules import create_rule
from lib.schema import update_roles_enum
from lib.skill_admin import add_skill
from lib.sync_pipeline import (
    _sync_stage_claude_base,
    _sync_stage_config_and_presets,
    _sync_stage_config_audit,
    _sync_stage_contexts,
    _sync_stage_drift_and_plugins,
    _sync_stage_external_skills_check,
    _sync_stage_gitignore,
    _sync_stage_knowledge_and_isolation,
    _sync_stage_legacy_cleanup,
    _sync_stage_per_provider,
)
from lib.viz import cleanup_old_sessions, generate_viz

# ---------------------------------------------------------------------------
# Entrypoint constants (moved from sync.py, #481)
# ---------------------------------------------------------------------------

EXT_SUFFIX = "-ext"
MANAGED_BEGIN = "<!-- agent-meta:managed-begin -->"
MANAGED_END   = "<!-- agent-meta:managed-end -->"
LOGFILE = "sync.log"
EXTERNAL_SKILLS_CONFIG = "config/skills-registry.yaml"

# Config auto-detect order when --config is omitted
_CONFIG_CANDIDATES = [
    ".meta-config/project.yaml",   # standard: Zielprojekt + Meta-Repo self-hosting
    "agent-meta.config.yaml",      # legacy flat-root
    "agent-meta.config.json",      # legacy JSON
]


# ---------------------------------------------------------------------------
# Test-Repository Validation
# ---------------------------------------------------------------------------

def resolve_test_repo_path(config: dict, project_root: Path, log: SyncLog) -> Path | None:
    """Resolve the test repository path with precedence:
    1. AGENT_META_TEST_REPO environment variable
    2. test-repo.path from project.yaml (relative or absolute)
    3. None if not configured

    Returns the resolved absolute path, or None if not available.
    """
    # 1. Environment variable override
    env_var_name = config.get("test-repo", {}).get("env-var", "AGENT_META_TEST_REPO")
    env_path = os.environ.get(env_var_name)
    if env_path:
        resolved = Path(env_path).resolve()
        log.note("test-repo", f"resolved from env var {env_var_name}: {resolved}")
        return resolved

    # 2. Config path (relative or absolute)
    test_cfg = config.get("test-repo", {})
    if not test_cfg:
        log.note("test-repo", "not configured in project.yaml")
        return None

    raw_path = test_cfg.get("path")
    if not raw_path:
        log.warning("test-repo.path is not set in project.yaml")
        return None

    path_obj = Path(raw_path)
    if path_obj.is_absolute():
        resolved = path_obj.resolve()
    else:
        # Relative to project_root (workspace)
        resolved = (project_root / path_obj).resolve()

    log.note("test-repo", f"resolved from config: {resolved}")
    return resolved


def _run_consistency_checks(agent_meta_root: Path) -> int:
    """Run the full agent-meta consistency-check suite over the sources.

    Reuses the runner in scripts/consistency-check.py (loaded via importlib
    because the filename contains a hyphen). Prints the human-readable report
    and returns the number of ERROR-severity findings (0 = no errors).
    """
    import importlib.util

    runner_path = agent_meta_root / "scripts" / "consistency-check.py"
    if not runner_path.exists():
        return 0
    spec = importlib.util.spec_from_file_location("_consistency_check_runner",
                                                  runner_path)
    if spec is None or spec.loader is None:
        return 0
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    from lib.consistency.report import Severity, print_report

    findings = module.run_checks(agent_meta_root, changed_only=False,
                                 specific_file=None)
    print_report(findings, agent_meta_root, changed_only=False)
    return sum(1 for f in findings if f.severity == Severity.ERROR)


def validate_test_repo(test_repo_path: Path, agent_meta_root: Path, config: dict,
                       log: SyncLog, dry_run: bool) -> bool:
    """Validate by performing a sync into the test repository and checking results.

    Returns True if validation passed, False otherwise.
    """
    if not test_repo_path.exists():
        log.warning(
            f"Test repository not found at: {test_repo_path}\n"
            f"  Set AGENT_META_TEST_REPO environment variable or\n"
            f"  configure test-repo.path in .meta-config/project.yaml")
        return False

    if not test_repo_path.is_dir():
        log.warning(f"Path exists but is not a directory: {test_repo_path}")
        return False

    log.note("test-repo", f"validating against: {test_repo_path}")

    # Perform a sync into the test repository
    from lib.agent_sync import sync_agents_for_provider
    from lib.commands import sync_commands_for_provider
    from lib.config import build_variables
    from lib.context import sync_context_for_provider, sync_snippets_for_provider
    from lib.dod import resolve_release_gates
    from lib.hook_plugins import sync_hook_lib, sync_release_gates
    from lib.hooks import sync_hooks
    from lib.providers import load_providers_config, resolve_providers
    from lib.rules import sync_rules, sync_speech_mode
    from lib.skills import sync_external_skills_for_provider

    test_variables, _pre_warnings = build_variables(config, agent_meta_root, test_repo_path)
    # Override AGENT_META_REPO to point to test repo for validation context
    test_variables["PROJECT_NAME"] = test_variables.get("PROJECT_NAME", "agent-meta-test")

    provider_config = load_providers_config(agent_meta_root)
    providers = resolve_providers(config, provider_config)

    validation_errors = 0
    for provider in providers:
        pc = provider_config[provider]
        log.note("test-repo", f"syncing agents for provider: {provider}")

        pipeline_details_dir = resolve_pipeline_details_dir(pc, provider)
        test_variables["PIPELINE_DETAILS_DIR"] = pipeline_details_dir
        pipelines_for_details = apply_overrides(
            load_quality_pipelines(str(agent_meta_root)), config.get("quality-pipelines", {})
        )
        if pipelines_for_details:
            sync_pipeline_detail_files(
                pipelines_for_details, provider, test_repo_path / pipeline_details_dir,
                test_repo_path, resolve_dod(config, agent_meta_root), log, dry_run,
            )

        sync_agents_for_provider(agent_meta_root, test_repo_path, config, test_variables,
                                 log, dry_run, provider, provider_config)
        sync_context_for_provider(agent_meta_root, test_repo_path, config, test_variables,
                                  log, dry_run, provider, provider_config)
        if pc["has_rules"]:
            sync_rules(agent_meta_root, test_repo_path, config, log, dry_run,
                       variables=test_variables, rules_dir=pc.get("rules_dir"),
                       provider=provider, provider_config=provider_config)
            sync_speech_mode(agent_meta_root, test_repo_path, config, log, dry_run,
                             rules_dir=pc.get("rules_dir"))
        if pc["has_hooks"]:
            sync_hooks(agent_meta_root, test_repo_path, config, log, dry_run,
                       provider=provider, provider_config=provider_config)
            sync_hook_lib(agent_meta_root, test_repo_path, config, log, dry_run,
                          provider=provider, provider_config=provider_config)
            sync_release_gates(agent_meta_root, test_repo_path, config, log, dry_run,
                                provider=provider, provider_config=provider_config,
                                release_gates_resolved=resolve_release_gates(config, agent_meta_root))
        if pc.get("has_commands", False):
            sync_commands_for_provider(agent_meta_root, test_repo_path, config, log,
                                       dry_run, provider, provider_config=provider_config,
                                       variables=test_variables)
        sync_snippets_for_provider(agent_meta_root, test_repo_path, config, log, dry_run,
                                   provider, provider_config)
        sync_external_skills_for_provider(agent_meta_root, test_repo_path, config, test_variables,
                                          log, dry_run, provider, provider_config)

    # Check sync.log for errors
    sync_log_path = test_repo_path / "sync.log"
    if sync_log_path.exists():
        content = sync_log_path.read_text(encoding="utf-8")
        error_lines = [line.strip() for line in content.splitlines()
                       if "[ERROR]" in line or "[FAIL]" in line]
        if error_lines:
            log.warning(f"test-repo: Found {len(error_lines)} error(s) in sync.log:")
            for el in error_lines:
                log.warning(f"test-repo:   {el}")
            validation_errors += len(error_lines)
        else:
            log.note("test-repo", "sync.log contains no errors")
    else:
        log.note("test-repo", "sync.log not found in test repository (first validation run)")

    return validation_errors == 0


class _SyncContext:
    """Mutable state shared across the CLI dispatch chain.

    Built once by :func:`_build_context` after the config is loaded. Each mode
    handler reads the fields it needs and writes back the two fields the common
    tail depends on: ``mode`` (always) and ``config`` (only handlers that reload
    it). Threading state through one object -- instead of a long local-variable
    tail -- is what makes the individual handlers independently unit-testable.
    """

    def __init__(self, *, args, log, agent_meta_root: Path, project_root: Path,
                 config: dict, config_path: Path, variables: dict,
                 platforms: list, source_version: str, viz_cfg: dict) -> None:
        self.args = args
        self.log = log
        self.agent_meta_root = agent_meta_root
        self.project_root = project_root
        self.config = config
        self.config_path = config_path
        self.variables = variables
        self.platforms = platforms
        self.source_version = source_version
        self.viz_cfg = viz_cfg
        self.mode: str | None = None



def _run_test_plugin(agent_meta_root: Path, project_root: Path, plugin_id: str) -> int:
    """Run the health check for one plugin from the catalog. Returns an exit code."""
    from lib.io import _load_yaml_or_json
    try:
        catalog = load_plugin_catalog(agent_meta_root=agent_meta_root, project_root=project_root)
        plugin_def = catalog.get(plugin_id)
        if not plugin_def:
            print(f"  !  '{plugin_id}' not in catalog ({', '.join(sorted(catalog)) or 'empty'})")
            return 1
        secrets, _ = _load_yaml_or_json(project_root / ".meta-config" / "secrets.local.yaml")
    except SyncError as exc:
        print(f"  FAIL  {plugin_id}: {exc}")
        return 1
    res = run_plugin_test(plugin_id, plugin_def, secrets=secrets or {})
    print(f"  {res['status']}  {plugin_id}: {res['message']} ({res['latency_ms']}ms)")
    return 0 if res["status"] == "PASS" else 1


def _build_context(args, agent_meta_root: Path, log: "SyncLog"):
    """Run the pre-config CLI modes and build the shared sync context.

    Returns ``None`` when an early-return mode handled the invocation (the
    caller should then simply return), otherwise a populated
    :class:`_SyncContext`. Preserves the original linear order of the
    early-return modes, --setup fall-through and config auto-detection.
    """
    if args.clear_cache:
        from lib.cache import CACHE_FILE, invalidate
        invalidate(CACHE_FILE)
        print("Outcome cache cleared.")
        return None

    if args.test_plugin:
        sys.exit(_run_test_plugin(agent_meta_root, Path.cwd(), args.test_plugin))

    if args.update_models:
        from lib.model_discovery import discover_models
        print("  i  Updating model registry...")
        discover_models()
        return None

    if args.render_standalone:
        from lib.standalone import write_standalone_files

        result = write_standalone_files(agent_meta_root, dry_run=args.dry_run)
        if args.check:
            drift = result["written"] + result["removed"]
            if drift:
                print("STANDALONE DRIFT — the following files are out of date:")
                for path in drift:
                    print(f"  {path}")
                sys.exit(1)
            print(f"  OK  standalone/ is up to date ({len(result['unchanged'])} file(s))")
            return None
        verb = "would write" if args.dry_run else "wrote"
        remove_verb = "would remove" if args.dry_run else "removed"
        for path in result["written"]:
            print(f"  {verb}: {path}")
        for path in result["removed"]:
            print(f"  {remove_verb}: {path}")
        for path in result["unchanged"]:
            print(f"  unchanged: {path}")
        print(f"\nSUMMARY\n-------\n{len(result['written'])} written  |  "
              f"{len(result['removed'])} removed  |  "
              f"{len(result['unchanged'])} unchanged  |  {len(result['roles'])} role(s)")
        return None

    if args.admin_only:
        admin_script = agent_meta_root / "scripts" / "admin-server.py"
        if not admin_script.exists():
            print(f"  !  admin-server.py not found at {admin_script}", file=sys.stderr)
            sys.exit(1)
        print(f"  i  Starting Admin UI server (admin-only mode) on port {args.admin_port}…")
        subprocess.run(
            [sys.executable, str(admin_script),
             "--port", str(args.admin_port),
             "--root", str(agent_meta_root)],
            check=False,
        )
        return None

    if args.dry_run:
        print("DRY-RUN — no files will be written\n")

    # Regenerate derived schema fields (roles enum) from role-defaults.yaml.
    # Runs early so even short-circuit modes (--create-rule, --validate, …)
    # pick up the latest enum. Honors --dry-run.
    if agent_meta_root.resolve() == Path.cwd().resolve():
        update_roles_enum(agent_meta_root, log, dry_run=args.dry_run)
    else:
        log.skip("schema", "skipped enum update (running as submodule)")

    if args.add_skill:
        mode = "add-skill"
        for required, flag in [(args.skill_name, "--skill-name"),
                               (args.source, "--source"),
                               (args.role, "--role")]:
            if not required:
                print(f"  !  --add-skill requires {flag}", file=sys.stderr)
                sys.exit(1)
        add_skill(agent_meta_root, args.add_skill, args.skill_name,
                  args.source, args.role, args.entry, log, args.dry_run)
        log.write(agent_meta_root / LOGFILE, EXTERNAL_SKILLS_CONFIG,
                  read_version(agent_meta_root), mode, [], args.dry_run)
        return None

    if args.setup:
        from lib.setup import run_setup_wizard
        cwd = Path.cwd()
        target_config = Path(args.config).resolve() if args.config else (
            cwd / ".meta-config" / "project.yaml"
        )
        run_setup_wizard(agent_meta_root, cwd, target_config, args.dry_run)
        if not args.dry_run:
            # Run --init sync with the freshly created config
            args.config = str(target_config)
            args.init = True
            print("\n  Starte --init Sync mit der neuen Konfiguration...\n")
        else:
            return None

    # All other modes require --config (or auto-detect)
    if not args.config:
        cwd = Path.cwd()
        for candidate in _CONFIG_CANDIDATES:
            if (cwd / candidate).exists():
                args.config = candidate
                print(f"  i  auto-detected config: {candidate}")
                break
        if not args.config:
            print("  i  Keine Konfiguration gefunden. Starte Setup-Wizard...\n")
            from lib.setup import run_setup_wizard
            target_config = cwd / ".meta-config" / "project.yaml"
            run_setup_wizard(agent_meta_root, cwd, target_config, args.dry_run)
            if not args.dry_run:
                args.config = str(target_config)
                args.init = True
            else:
                return None

    config_resolved = Path(args.config).resolve()
    config_parent_name = config_resolved.parent.name
    # .meta-config/project.yaml → project root is two levels up
    if config_parent_name in (".meta-config",):
        project_root = config_resolved.parent.parent
    else:
        project_root = config_resolved.parent
    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    variables, pre_warnings = build_variables(config, agent_meta_root, project_root)
    platforms = config.get("platforms", [])
    source_version = config.get("agent-meta-version", read_version(agent_meta_root))

    # Merge CLI viz-mode into config
    if args.viz_mode is not None:
        if "viz" not in config:
            config["viz"] = {}
        config["viz"]["mode"] = args.viz_mode
    viz_cfg = config.get("viz", {})

    # Warn if actual git tag of agent-meta submodule doesn't match configured version
    read_git_version(agent_meta_root)

    for w in pre_warnings:
        log.warn(w)

    return _SyncContext(
        args=args, log=log, agent_meta_root=agent_meta_root,
        project_root=project_root, config=config, config_path=config_path,
        variables=variables, platforms=platforms,
        source_version=source_version, viz_cfg=viz_cfg,
    )


# ---------------------------------------------------------------------------
# Mode handlers (#481 move from sync.py)
# ---------------------------------------------------------------------------

def _handle_fill_defaults(ctx: _SyncContext) -> None:
    """Handle --fill-defaults."""
    args = ctx.args
    log = ctx.log
    agent_meta_root = ctx.agent_meta_root
    config_path = ctx.config_path

    mode = "fill-defaults"
    fill_defaults(config_path, agent_meta_root, log, args.dry_run)

    ctx.mode = mode


def _handle_audit_config(ctx: _SyncContext) -> None:
    """Handle --audit-config (with optional --apply)."""
    args = ctx.args
    log = ctx.log
    agent_meta_root = ctx.agent_meta_root
    config = ctx.config
    config_path = ctx.config_path

    mode = "audit-config"
    report = audit_config(agent_meta_root, config_path)
    print(format_report(report))
    if args.apply:
        if args.dry_run:
            log.note("audit-config",
                     f"--apply skipped (dry-run): would disable "
                     f"{len(report.deprecated_roles)} deprecated role(s)")
        else:
            changed = apply_audit(report, config_path)
            if changed:
                log.note("audit-config",
                         f"commented out {changed} deprecated role line(s) in "
                         f"{config_path}")
            else:
                log.note("audit-config",
                         "no changes applied (nothing to disable)")

    ctx.config = config
    ctx.mode = mode


def _handle_only_variables(ctx: _SyncContext) -> None:
    """Handle --only-variables."""
    args = ctx.args
    log = ctx.log
    agent_meta_root = ctx.agent_meta_root
    project_root = ctx.project_root
    config = ctx.config
    variables = ctx.variables

    mode = "only-variables"
    provider_config = load_providers_config(agent_meta_root)
    providers = resolve_providers(config, provider_config)
    only_variables(project_root, variables, log, args.dry_run,
                   providers=providers, provider_config=provider_config)

    ctx.config = config
    ctx.mode = mode


def _handle_create_ext(ctx: _SyncContext) -> None:
    """Handle --create-ext ROLE."""
    args = ctx.args
    log = ctx.log
    agent_meta_root = ctx.agent_meta_root
    project_root = ctx.project_root
    config = ctx.config
    variables = ctx.variables

    mode = f"create-ext:{args.create_ext}"
    role_map = build_role_map(agent_meta_root)
    roles = list(role_map.keys()) if args.create_ext == "all" else [args.create_ext]
    for role in roles:
        create_extension(project_root, config, variables, role, log, args.dry_run,
                         agent_meta_root=agent_meta_root)

    ctx.config = config
    ctx.mode = mode


def _handle_update_ext(ctx: _SyncContext) -> None:
    """Handle --update-ext."""
    args = ctx.args
    log = ctx.log
    agent_meta_root = ctx.agent_meta_root
    project_root = ctx.project_root
    variables = ctx.variables

    mode = "update-ext"
    update_extensions(project_root, variables, log, args.dry_run,
                      agent_meta_root=agent_meta_root)

    ctx.mode = mode


def _handle_create_rule(ctx: _SyncContext) -> None:
    """Handle --create-rule NAME."""
    args = ctx.args
    log = ctx.log
    project_root = ctx.project_root

    mode = f"create-rule:{args.create_rule}"
    create_rule(project_root, args.create_rule, log, args.dry_run)

    ctx.mode = mode


def _handle_create_hook(ctx: _SyncContext) -> None:
    """Handle --create-hook NAME."""
    args = ctx.args
    log = ctx.log
    project_root = ctx.project_root

    mode = f"create-hook:{args.create_hook}"
    create_hook(project_root, args.create_hook, log, args.dry_run)

    ctx.mode = mode


def _handle_create_command(ctx: _SyncContext) -> None:
    """Handle --create-command NAME."""
    args = ctx.args
    log = ctx.log
    project_root = ctx.project_root

    mode = f"create-command:{args.create_command}"
    create_command(project_root, args.create_command, log, args.dry_run)

    ctx.mode = mode


def _handle_viz_only(ctx: _SyncContext) -> None:
    """Handle --viz-only."""
    args = ctx.args
    log = ctx.log
    agent_meta_root = ctx.agent_meta_root
    project_root = ctx.project_root
    config = ctx.config

    mode = "viz-only"
    # Override viz config
    if "viz" not in config:
        config["viz"] = {}
    config["viz"]["enabled"] = True
    generate_viz(agent_meta_root, project_root, config, log, args.dry_run)

    ctx.config = config
    ctx.mode = mode


def _handle_viz_cleanup(ctx: _SyncContext) -> None:
    """Handle --viz-cleanup."""
    args = ctx.args
    log = ctx.log
    project_root = ctx.project_root
    config = ctx.config
    viz_cfg = ctx.viz_cfg

    mode = "viz-cleanup"
    viz_cfg = config.get("viz", {})
    retention = viz_cfg.get("report", {}).get("retention_days", 7)
    cleanup_old_sessions(project_root, retention_days=retention,
                         log=log, dry_run=args.dry_run)

    ctx.config = config
    ctx.mode = mode


def _handle_deactivation_status(ctx: _SyncContext) -> None:
    """Handle --deactivation-status."""
    agent_meta_root = ctx.agent_meta_root
    project_root = ctx.project_root
    config = ctx.config

    mode = "deactivation-status"
    provider_config = load_providers_config(agent_meta_root)
    status = get_deactivation_status(project_root, config, provider_config)
    import json as _json
    print(_json.dumps(status, indent=2, ensure_ascii=False))

    ctx.config = config
    ctx.mode = mode


def _handle_deactivate_providers(ctx: _SyncContext) -> None:
    """Handle --deactivate-providers."""
    args = ctx.args
    log = ctx.log
    agent_meta_root = ctx.agent_meta_root
    project_root = ctx.project_root
    config = ctx.config
    config_path = ctx.config_path
    variables = ctx.variables

    mode = "deactivate-providers"
    provider_config = load_providers_config(agent_meta_root)
    targets = args.deactivate_providers if args.deactivate_providers else ["all"]
    results = deactivate_providers(
        project_root, targets, provider_config, config, log, args.dry_run
    )
    # Update project.yaml so resolve_providers() reflects the change.
    deactivated_list = resolve_deactivation_targets(targets, provider_config)
    update_deactivation_config(config_path, provider_config, deactivated_list,
                                config, log, args.dry_run)
    # Re-sync context files so AGENTS.md reflects the updated provider list.
    if not args.dry_run:
        config = load_config(config_path)
        variables, _ = build_variables(config, agent_meta_root, project_root)
        for prov in resolve_providers(config, provider_config):
            sync_context_for_provider(agent_meta_root, project_root, config,
                                      variables, log, args.dry_run,
                                      prov, provider_config)
    import json as _json
    print(_json.dumps(results, indent=2, ensure_ascii=False))

    ctx.config = config
    ctx.mode = mode


def _handle_activate_providers(ctx: _SyncContext) -> None:
    """Handle --activate-providers."""
    args = ctx.args
    log = ctx.log
    agent_meta_root = ctx.agent_meta_root
    project_root = ctx.project_root
    config = ctx.config
    config_path = ctx.config_path
    variables = ctx.variables

    mode = "activate-providers"
    provider_config = load_providers_config(agent_meta_root)
    targets = args.activate_providers if args.activate_providers else []
    results = activate_providers(
        project_root, targets, provider_config, config, log, args.dry_run
    )
    # Update project.yaml: remove activated providers from deactivation list.
    dc = config.get("provider-deactivation", {})
    current = set(dc.get("providers", []) if isinstance(dc.get("providers"), list) else [])
    if not targets:
        remaining = []  # activate all → clear deactivation
    else:
        remaining = sorted(current - set(resolve_deactivation_targets(targets, provider_config)))
    update_deactivation_config(config_path, provider_config, remaining,
                                config, log, args.dry_run)
    if not args.dry_run:
        config = load_config(config_path)
        variables, _ = build_variables(config, agent_meta_root, project_root)
        for prov in resolve_providers(config, provider_config):
            sync_context_for_provider(agent_meta_root, project_root, config,
                                      variables, log, args.dry_run,
                                      prov, provider_config)
    import json as _json
    print(_json.dumps(results, indent=2, ensure_ascii=False))

    ctx.config = config
    ctx.mode = mode


def _handle_backup(ctx: _SyncContext) -> None:
    """Handle --backup."""
    args = ctx.args
    log = ctx.log
    agent_meta_root = ctx.agent_meta_root
    project_root = ctx.project_root
    config = ctx.config
    source_version = ctx.source_version

    mode = "backup"
    provider_config = load_providers_config(agent_meta_root)
    targets = args.backup if args.backup else None
    result = create_backup(
        project_root, targets, provider_config, config, log,
        label=args.label,
        dry_run=args.dry_run,
        source_version=source_version,
    )
    import json as _json
    print(_json.dumps(result, indent=2, ensure_ascii=False))

    ctx.config = config
    ctx.mode = mode


def _handle_restore(ctx: _SyncContext) -> None:
    """Handle --restore."""
    args = ctx.args
    log = ctx.log
    agent_meta_root = ctx.agent_meta_root
    project_root = ctx.project_root
    config = ctx.config

    mode = "restore"
    provider_config = load_providers_config(agent_meta_root)
    result = restore_backup(
        project_root, args.restore, provider_config, config, log,
        providers=args.restore_providers,
        force=args.force,
        dry_run=args.dry_run,
    )
    import json as _json
    print(_json.dumps(result, indent=2, ensure_ascii=False))

    ctx.config = config
    ctx.mode = mode


def _handle_list_backups(ctx: _SyncContext) -> None:
    """Handle --list-backups."""
    agent_meta_root = ctx.agent_meta_root
    project_root = ctx.project_root
    config = ctx.config

    mode = "list-backups"
    provider_config = load_providers_config(agent_meta_root)
    result = list_backups(project_root, config, provider_config)
    import json as _json
    print(_json.dumps(result, indent=2, ensure_ascii=False))

    ctx.config = config
    ctx.mode = mode


def _handle_delete_backup(ctx: _SyncContext) -> None:
    """Handle --delete-backup."""
    args = ctx.args
    log = ctx.log
    project_root = ctx.project_root
    config = ctx.config

    mode = "delete-backup"
    result = delete_backup(project_root, args.delete_backup, config, log, args.dry_run)
    import json as _json
    print(_json.dumps(result, indent=2, ensure_ascii=False))

    ctx.config = config
    ctx.mode = mode


def _handle_prune_backups(ctx: _SyncContext) -> None:
    """Handle --prune-backups."""
    args = ctx.args
    log = ctx.log
    project_root = ctx.project_root
    config = ctx.config

    mode = "prune-backups"
    result = prune_backups(project_root, config, log, args.dry_run)
    import json as _json
    print(_json.dumps(result, indent=2, ensure_ascii=False))

    ctx.config = config
    ctx.mode = mode


def _handle_validate(ctx: _SyncContext) -> None:
    """Handle --validate (may sys.exit; falls through on full success)."""
    args = ctx.args
    log = ctx.log
    agent_meta_root = ctx.agent_meta_root
    project_root = ctx.project_root
    config = ctx.config
    config_path = ctx.config_path

    mode = "validate"
    if args.dry_run:
        print("DRY-RUN — validation will not write files\n")

    # Consistency checks always run (no test repo required). These validate
    # agent templates, cross-references, dual-tree parity and handoff
    # contracts against the agent-meta sources themselves.
    consistency_errors = _run_consistency_checks(agent_meta_root)

    # Config-audit staleness check (issue #560): full-replacement
    # 2-platform overrides pin their generic base via `based-on:
    # "1-generic/<role>.md@<version>"` but do not automatically inherit
    # later changes to that base -- including security-relevant workflow
    # steps. Warn loudly when the pin has fallen 1+ major versions behind
    # the current generic template so drift can't silently accumulate.
    _validate_audit_report = audit_config(agent_meta_root, config_path)
    _stale_overrides = _validate_audit_report.by_category("stale_platform_overrides")
    for _stale in _stale_overrides:
        log.warning(f"config-audit [P1] stale-override: {_stale.message}")

    # Unpaired closing tags (issue #567): a copy-paste artifact like a
    # trailing `</output>` with no `<output>` anywhere in the file ships
    # broken structural markup into every synced project. Treated as a hard
    # validation error, same as the other consistency checks.
    _unpaired_tags = _validate_audit_report.by_category("unpaired_closing_tags")
    for _unpaired in _unpaired_tags:
        log.warning(f"config-audit [ERROR] unpaired-closing-tag: {_unpaired.message}")
    if _unpaired_tags:
        consistency_errors += len(_unpaired_tags)

    # Tool-privilege / role-name mismatch (issue #575): warns only, does not
    # block validation -- a role claiming "read-only" in its persona but
    # carrying Write/Edit is a smell worth a human look, not a hard failure.
    _tool_mismatches = _validate_audit_report.by_category("tool_privilege_mismatch")
    for _mismatch in _tool_mismatches:
        log.warning(f"config-audit [WARN] tool-privilege-mismatch: {_mismatch.message}")

    # Provider-registry completeness (issue #625): warns only when a
    # registered provider is missing from a known provider-keyed Python
    # enumeration in scripts/ -- a provider can legitimately be excluded from
    # a given touchpoint, so this never blocks validation.
    _provider_gaps = _validate_audit_report.by_category("provider_registry_completeness")
    for _gap in _provider_gaps:
        log.warning(f"config-audit [WARN] provider-registry-gap: {_gap.message}")

    from lib.consistency.hook_drift import check_stale_deployed_hooks
    from lib.consistency.orchestrator_strict import check_orchestrator_strict_hook_support
    from lib.consistency.report import print_report
    from lib.providers import load_providers_config as _load_pc

    _provider_config = _load_pc(agent_meta_root)
    _strict_findings = check_orchestrator_strict_hook_support(project_root, config, _provider_config)
    # Deployed-hook version drift (issue #630): warns when a project's
    # .claude/hooks/*.sh (or another provider's hooks_dir) has fallen behind
    # the current hooks/1-generic/ source -- sibling check to
    # stale_platform_overrides above, for hooks instead of agent templates.
    _strict_findings += check_stale_deployed_hooks(project_root, agent_meta_root, config, _provider_config)
    if _strict_findings:
        print_report(_strict_findings, project_root, changed_only=False)

    test_repo_path = resolve_test_repo_path(config, project_root, log)
    if test_repo_path is None or not test_repo_path.exists():
        reason = (f"configured path {test_repo_path} does not exist"
                  if test_repo_path else
                  "not configured (set test-repo.path in .meta-config/project.yaml "
                  "or AGENT_META_TEST_REPO)")
        log.note("test-repo",
                 f"Skipping test-repo sync validation — {reason}. "
                 "Consistency checks still ran.")
        sys.exit(1 if consistency_errors else 0)
    success = validate_test_repo(test_repo_path, agent_meta_root, config, log, args.dry_run)
    if not success or consistency_errors:
        sys.exit(1)

    ctx.config = config
    ctx.mode = mode


def _handle_sync(ctx: _SyncContext) -> None:
    """Default handler: full sync / --init.

    Thin orchestrator over the ``_sync_stage_*`` helpers in
    ``lib/sync_pipeline.py`` (issue #481). The call order matches the
    original monolithic implementation 1:1, so the ``log.*`` call sequence
    (and therefore stdout) is unchanged. ``ctx.config``/``ctx.mode`` are
    written back at the end, exactly like before the split.
    """
    # Stages 1+2: config auto-fill + reload, provider/DoD/rules-preset
    # resolution + platform vars. The reloaded config flows back to
    # ctx.config via the final write-back below (same as the original
    # local rebind after auto-fill).
    config, provider_config, providers, mode, platform_vars = \
        _sync_stage_config_and_presets(
            ctx.agent_meta_root, ctx.project_root, ctx.config_path, ctx.config,
            ctx.platforms, ctx.args, ctx.log)
    # Stage 3: Claude-gated base syncs + gitignore/env baselines.
    is_claude, gitignore_cfg, base_gitignore_entries, env_gitignore = \
        _sync_stage_claude_base(ctx.agent_meta_root, ctx.project_root, config,
                                provider_config, providers, ctx.variables,
                                ctx.args, ctx.log)
    # Stage 4: per-provider context sync; also seeds the accumulators
    # consumed by stages 6 and 11.
    debug_mode, allow_committed_secrets, mcp_gitignore_extras = \
        _sync_stage_contexts(ctx.agent_meta_root, ctx.project_root, config,
                             provider_config, providers, ctx.variables,
                             ctx.args, ctx.log)
    # Stage 5: legacy-provider cleanup.
    _sync_stage_legacy_cleanup(ctx.project_root, config, provider_config,
                               providers, ctx.args, ctx.log)
    # Stage 6: per-provider main loop; mcp_gitignore_extras crosses the
    # stage boundary by reference.
    _sync_stage_per_provider(ctx.agent_meta_root, ctx.project_root, config,
                             provider_config, providers, ctx.variables,
                             platform_vars, debug_mode, allow_committed_secrets,
                             mcp_gitignore_extras, ctx.args, ctx.log)
    # Stage 7: injection-drift governance + plugin probe.
    _sync_stage_drift_and_plugins(ctx.agent_meta_root, ctx.project_root, config,
                                  provider_config, ctx.args, ctx.log)
    # Stages 8+9: knowledge engine + provider isolation.
    _sync_stage_knowledge_and_isolation(ctx.agent_meta_root, ctx.project_root,
                                        config, providers, provider_config,
                                        ctx.args, ctx.log)
    # Stage 10: pinned-commit check + unknown/unapproved-skill warnings;
    # ext_config feeds the gitignore stage.
    ext_config = _sync_stage_external_skills_check(ctx.agent_meta_root, config, ctx.log)
    # Stage 11: .gitignore managed-block assembly; the accumulators built
    # above cross the stage boundary by reference.
    _sync_stage_gitignore(ctx.project_root, config, provider_config, providers,
                          ext_config, is_claude, gitignore_cfg,
                          base_gitignore_entries, mcp_gitignore_extras,
                          env_gitignore, ctx.args, ctx.viz_cfg, ctx.log)
    # Stage 12: lightweight config-audit summary.
    _sync_stage_config_audit(ctx.agent_meta_root, ctx.config_path, ctx.log)

    ctx.config = config
    ctx.mode = mode




# ---------------------------------------------------------------------------
# Common tail (#481 move from sync.py)
# ---------------------------------------------------------------------------

def _run_common_tail(ctx: _SyncContext) -> None:
    """Shared post-dispatch tail: env scripts, viz, AST, log write,
    --check exit code, --admin server and the restart notice.

    Every dispatch branch that does not exit early falls through here.
    """
    args = ctx.args
    log = ctx.log
    agent_meta_root = ctx.agent_meta_root
    project_root = ctx.project_root
    config = ctx.config
    viz_cfg = ctx.viz_cfg
    platforms = ctx.platforms
    source_version = ctx.source_version
    mode = ctx.mode

    # Environment script generation: produce platform-specific setup scripts
    # (.ps1 / .sh) from the environments: section in project.yaml.
    from lib.env import generate_env_scripts
    env_results = generate_env_scripts(config, project_root, dry_run=args.dry_run)
    for rel, status in sorted(env_results.items()):
        if status == "skipped":
            log.skip(rel, "unchanged")
        elif status != "dry-run":
            log.action("WRITE", rel, f"env script ({status})")

    # Visualization: generate static mindmap if requested (static or full mode)
    viz_mode = args.viz_mode or viz_cfg.get("mode", "off")
    if args.viz or viz_cfg.get("enabled", False) or viz_mode in ("static", "full"):
        generate_viz(agent_meta_root, project_root, config, log, args.dry_run)

    # AST dependency analysis summary (analysis.ast: true)
    _analysis_cfg = config.get("analysis", {}) if config else {}
    if isinstance(_analysis_cfg, dict) and _analysis_cfg.get("ast", False):
        try:
            from lib.analysis import analyze_file_dependencies, is_available
            if is_available():
                _deps = analyze_file_dependencies(agent_meta_root)
                _dep_count = sum(len(v) for v in _deps.values())
                _files_with_deps = sum(1 for v in _deps.values() if v)
                print(
                    f"\n  i  AST analysis: {len(_deps)} files scanned, "
                    f"{_files_with_deps} with dependencies, "
                    f"{_dep_count} total import edges in scripts/lib/"
                )
        except (ImportError, OSError) as e:
            # Cosmetic summary print only — analyze_file_dependencies() already
            # catches per-file SyntaxError/OSError/UnicodeDecodeError internally
            # (lib/analysis.py). This guards the module import itself and any
            # directory-traversal failure; neither should abort the sync for an
            # optional, informational-only print statement.
            log.debug("ast-analysis", f"skipped: {type(e).__name__}: {e}")  # noqa: PLE1205

    log_path = project_root / LOGFILE
    _providers = resolve_providers(config, load_providers_config(agent_meta_root)) if config else []
    _speech = config.get("speech-mode", "full") if config else "full"
    log.write(log_path, args.config, source_version, mode, platforms, args.dry_run,
              providers=_providers, speech_mode=_speech)

    # CI check mode: signal pending changes via exit code.
    if getattr(args, "check", False):
        pending = len(log.actions)
        if pending > 0:
            print(
                f"  X  {pending} file(s) out of sync — run "
                f"`python scripts/sync.py` to regenerate.",
                file=sys.stderr,
            )
            sys.exit(1)
        print("  i  Provider context files are up to date.")
        sys.exit(0)

    if getattr(args, "admin", False):
        admin_script = agent_meta_root / "scripts" / "admin-server.py"
        if not admin_script.exists():
            print(f"  !  admin-server.py not found at {admin_script}", file=sys.stderr)
        else:
            print(f"  i  Starting Admin UI server on port {args.admin_port}…")
            subprocess.run(
                [sys.executable, str(admin_script),
                 "--port", str(args.admin_port),
                 "--root", str(agent_meta_root)],
                check=False,
            )

    if not getattr(args, "check", False) and not getattr(args, "admin", False) and not args.dry_run:
        print("\n" + "=" * 80)
        print("[WICHTIG] KI-PROVIDER / IDE RESTART ERFORDERLICH")
        print("Bitte starte deine KI-Session (IDE / CLI) JETZT neu, damit die neu generierten")
        print("Default-Agenten in die Laufzeitumgebung geladen werden!")
        print("Danach kann der agent-meta-manager unterstützen.")
        print("=" * 80 + "\n")


