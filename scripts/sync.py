#!/usr/bin/env python3
"""
agent-meta sync.py
==================
Generates .claude/agents/*.md for a project from agent-meta sources.
Manages .claude/3-project/<prefix>-<role>-ext.md extension files.
Syncs snippets, rules, hooks and external skill agents.

Usage:
  python .agent-meta/scripts/sync.py --config .meta-config/project.yaml
  python .agent-meta/scripts/sync.py --config .meta-config/project.yaml --init
  python .agent-meta/scripts/sync.py --config .meta-config/project.yaml --only-variables
  python .agent-meta/scripts/sync.py --config .meta-config/project.yaml --create-ext <role>
  python .agent-meta/scripts/sync.py --config .meta-config/project.yaml --update-ext
  python .agent-meta/scripts/sync.py --config .meta-config/project.yaml --create-rule <name>
  python .agent-meta/scripts/sync.py --config .meta-config/project.yaml --create-hook <name>
  python .agent-meta/scripts/sync.py --config .meta-config/project.yaml --dry-run
  python .agent-meta/scripts/sync.py --config .meta-config/project.yaml --validate
  python .agent-meta/scripts/sync.py --setup
  python .agent-meta/scripts/sync.py --add-skill <repo-url> --skill-name <name>
                                      --source <path> --role <role> [--entry <file>]

Config lookup order (when --config is omitted):
  1. .meta-config/project.yaml    (standard location — Zielprojekt + Meta-Repo self-hosting)
  2. agent-meta.config.yaml       (legacy flat-root)
  3. agent-meta.config.json       (legacy JSON fallback)

External skills (config/skills-registry.yaml in agent-meta):
  - Managed centrally in agent-meta (Modell A)
  - Each enabled skill generates a wrapper agent in .claude/agents/<role>.md
  - Skill files are copied to .claude/skills/<skill-name>/
  - Use --add-skill to register a new submodule + skill entry
  - Activate per-project via .meta-config/skills.yaml or project.yaml external-skills block
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Windows consoles often default to cp1252 — the sync report contains UTF-8
# characters (— → ✓), so force UTF-8 output to avoid UnicodeEncodeError.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add scripts/ directory to sys.path so lib/ is importable regardless of cwd
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.agents import (
    sync_agents_for_provider,
)
from lib.backup import (
    create_backup,
    delete_backup,
    list_backups,
    prune_backups,
    restore_backup,
)
from lib.commands import create_command, sync_commands_for_provider
from lib.config import (
    _orch_mode_flags,
    _resolve_orch_mode,
    build_variables,
    fill_defaults,
    find_agent_meta_root,
    load_config,
    read_git_version,
    read_version,
)
from lib.config_audit import apply_audit, audit_config, format_report
from lib.context import (
    ensure_gitignore_entries,
    init_claude_personal,
    init_settings_json,
    init_settings_local_json,
    only_variables,
    sync_claude_md_static,
    sync_context_for_provider,
    sync_prompts_for_continue,
    sync_snippets_for_provider,
)
from lib.deactivation import (
    activate_providers,
    deactivate_providers,
    get_deactivation_status,
    is_provider_active,
    resolve_deactivation_targets,
    update_deactivation_config,
)
from lib.dod import resolve_dod
from lib.extensions import create_extension, update_extensions
from lib.hooks import create_hook, sync_hooks
from lib.io import SyncError, safe_path, write_checked
from lib.isolation import sync_provider_isolation
from lib.knowledge import generate_initial_index, generate_initial_log, generate_schema
from lib.log import SyncLog
from lib.mcp import (
    generate_mcp_artifacts,
    init_secrets_template,
)
from lib.platform import load_platform_config
from lib.providers import (
    load_providers_config,
    resolve_providers,
)
from lib.roles import build_role_map
from lib.rules import create_rule, resolve_rules, sync_rules, sync_speech_mode
from lib.schema import update_roles_enum
from lib.skills import (
    add_skill,
    check_pinned_commits,
    load_external_skills_config,
    sync_external_skills_for_provider,
)
from lib.viz import (
    cleanup_old_sessions,
    generate_viz,
)
from lib.viz import (
    get_gitignore_entries as viz_gitignore_entries,
)

# ---------------------------------------------------------------------------
# Entrypoint-only constants
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
# Helpers
# ---------------------------------------------------------------------------

def _collect_skill_gitignore_entries(config: dict, ext_config: dict, provider_config: dict) -> list[str]:
    """Return .gitignore paths for skills with gitignore: true in project config.

    Only generates entries for skills that are approved + enabled (two-gate).
    Generates one entry per active provider so that skill files in all provider
    directories are properly gitignored when requested.
    """
    entries: list[str] = []
    project_skills = config.get("external-skills", {})
    providers = config.get("ai-providers", config.get("ai-provider", ["Claude"]))
    if isinstance(providers, str):
        providers = [providers]

    for skill_name, skill_project_cfg in project_skills.items():
        if not skill_project_cfg.get("gitignore", False):
            continue
        skill_meta = ext_config.get("skills", {}).get(skill_name, {})
        if not skill_meta.get("approved", False):
            continue
        if not skill_project_cfg.get("enabled", False):
            continue
        for provider in providers:
            pc = provider_config.get(provider, {})
            skills_dir = pc.get("skills_dir")
            if skills_dir:
                entries.append(f"{skills_dir}/{skill_name}/")
    return entries


# ---------------------------------------------------------------------------
# Knowledge Engine — Phase A scaffolding (sync Phase 2.5)
# ---------------------------------------------------------------------------

_KNOWLEDGE_GITKEEP_SUBDIRS = [
    Path("sources", "assets"),
    Path("wiki", "concepts"),
    Path("wiki", "entities"),
    Path("wiki", "topics"),
    Path("wiki", "sources"),
    Path("wiki", "queries"),
]


def sync_knowledge_engine(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Phase 2.5 — scaffold the knowledge/ bundle when knowledge-engine.enabled is true.

    No-op (zero-overhead) when disabled or absent. Idempotent: never
    overwrites existing schema.md/wiki/index.md/wiki/log.md, only fills in
    missing .gitkeep markers in empty subdirectories on subsequent runs.
    """
    ke_config = config.get("knowledge-engine") or {}
    if not ke_config.get("enabled", False):
        log.skip("knowledge-engine", "disabled in project.yaml")
        return

    domain = ke_config.get("domain", "research")
    bundle_rel = ke_config.get("bundle-path", "knowledge")
    bundle_dir = safe_path(project_root, bundle_rel)

    if bundle_dir.exists() and not bundle_dir.is_dir():
        raise SyncError(
            f"knowledge-engine.bundle-path '{bundle_rel}' points to an existing "
            f"file, not a directory: {bundle_dir}"
        )

    bundle_exists = bundle_dir.is_dir()

    if not bundle_exists:
        try:
            schema_content = generate_schema(domain, bundle_rel, agent_meta_root)
        except ValueError as exc:
            raise SyncError(f"knowledge-engine: {exc}") from exc

        if not dry_run:
            (bundle_dir / "wiki").mkdir(parents=True, exist_ok=True)

        schema_path = bundle_dir / "schema.md"
        rel_schema = f"{bundle_rel}/schema.md"
        if write_checked(schema_path, schema_content, log, rel_schema, dry_run=dry_run):
            log.action("CREATE", rel_schema, "knowledge-engine scaffolding")

        index_path = bundle_dir / "wiki" / "index.md"
        rel_index = f"{bundle_rel}/wiki/index.md"
        if write_checked(index_path, generate_initial_index(), log, rel_index, dry_run=dry_run):
            log.action("CREATE", rel_index, "knowledge-engine scaffolding")

        log_path = bundle_dir / "wiki" / "log.md"
        rel_log = f"{bundle_rel}/wiki/log.md"
        if write_checked(log_path, generate_initial_log(), log, rel_log, dry_run=dry_run):
            log.action("CREATE", rel_log, "knowledge-engine scaffolding")
    else:
        log.info(  # noqa: PLE1205
            "knowledge-engine",
            f"{bundle_rel}/ already exists — schema.md/index.md/log.md not "
            "regenerated. If domain changed, verify schema.md manually "
            "(not auto-migrated in Phase A)."
        )

    for rel_subdir in _KNOWLEDGE_GITKEEP_SUBDIRS:
        target_dir = bundle_dir / rel_subdir
        gitkeep_path = target_dir / ".gitkeep"
        rel_gitkeep = f"{bundle_rel}/{rel_subdir.as_posix()}/.gitkeep"
        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
        if write_checked(gitkeep_path, "", log, rel_gitkeep, dry_run=dry_run):
            log.action("CREATE", rel_gitkeep, "knowledge-engine scaffolding")


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
        log.info("test-repo", f"resolved from env var {env_var_name}: {resolved}")  # noqa: PLE1205
        return resolved

    # 2. Config path (relative or absolute)
    test_cfg = config.get("test-repo", {})
    if not test_cfg:
        log.info("test-repo", "not configured in project.yaml")  # noqa: PLE1205
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

    log.info("test-repo", f"resolved from config: {resolved}")  # noqa: PLE1205
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

    log.info("test-repo", f"validating against: {test_repo_path}")  # noqa: PLE1205

    # Perform a sync into the test repository
    from lib.agents import sync_agents_for_provider
    from lib.commands import sync_commands_for_provider
    from lib.config import build_variables
    from lib.context import sync_context_for_provider, sync_snippets_for_provider
    from lib.hooks import sync_hooks
    from lib.providers import load_providers_config, resolve_providers
    from lib.rules import sync_rules, sync_speech_mode
    from lib.skills import sync_external_skills_for_provider

    test_variables, _pre_warnings = build_variables(config, agent_meta_root)
    # Override AGENT_META_REPO to point to test repo for validation context
    test_variables["PROJECT_NAME"] = test_variables.get("PROJECT_NAME", "agent-meta-test")

    provider_config = load_providers_config(agent_meta_root)
    providers = resolve_providers(config, provider_config)

    validation_errors = 0
    for provider in providers:
        pc = provider_config[provider]
        log.info("test-repo", f"syncing agents for provider: {provider}")  # noqa: PLE1205
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
            log.info("test-repo", "sync.log contains no errors")  # noqa: PLE1205
    else:
        log.info("test-repo", "sync.log not found in test repository (first validation run)")  # noqa: PLE1205

    return validation_errors == 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Sync agent-meta agents into a project."
    )
    parser.add_argument("--config", required=False, default=None,
                        help="Path to project.yaml (default: auto-detect .meta-config/project.yaml "
                             "or legacy agent-meta.config.yaml). Not required for --add-skill.")
    parser.add_argument("--init", action="store_true",
                        help="Also generate CLAUDE.md from template (only if not present)")
    parser.add_argument("--only-variables", action="store_true",
                        help="Only substitute {{VARIABLE}} in existing CLAUDE.md")
    parser.add_argument("--create-ext", metavar="ROLE",
                        help="Create extension file for ROLE (or 'all'). "
                             "Does not overwrite existing files.")
    parser.add_argument("--update-ext", action="store_true",
                        help="Update managed block in all existing extension files")
    parser.add_argument("--create-rule", metavar="NAME",
                        help="Create .claude/rules/<NAME>.md template (never overwrites)")
    parser.add_argument("--create-hook", metavar="NAME",
                        help="Create .claude/hooks/<NAME>.sh template (never overwrites). "
                             "Enable via .meta-config/project.yaml: "
                             "hooks: <NAME>: enabled: true")
    parser.add_argument("--create-command", metavar="NAME",
                        help="Create .claude/commands/<NAME>.md template (never overwrites)")
    parser.add_argument("--fill-defaults", action="store_true",
                        help="Write missing config fields with their default values into "
                             ".meta-config/project.yaml (or .json). Structural fields (dod-preset, "
                             "max-parallel-agents, speech-mode, dod.*) are written when absent. "
                             "Missing variable keys are reported as warnings only.")
    parser.add_argument("--setup", action="store_true",
                        help="Interactive setup wizard: guided creation of .meta-config/project.yaml "
                             "followed by --init sync. Use before the first sync on a new project.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without writing files")
    parser.add_argument("--check", action="store_true",
                        help="CI mode (use with --dry-run): exit 1 if any file would be "
                             "written/changed, exit 0 if everything is up to date. "
                             "Use to fail CI when provider context files are out of sync.")
    parser.add_argument("--validate", action="store_true",
                        help="Validate sync output against the configured test repository. "
                             "Resolves test-repo.path from project.yaml (relative or absolute), "
                             "optionally overridden by AGENT_META_TEST_REPO env var. "
                             "Performs a full sync into the test repo and checks sync.log for errors.")
    parser.add_argument("--viz", action="store_true",
                        help="Generate static agent visualization (mindmap + interactive HTML)")
    parser.add_argument("--viz-mode", choices=["off", "static", "dynamic", "full"], default=None,
                        help="Visualization mode: off (default), static (mindmap only), "
                             "dynamic (agent event logging + reports), full (both)")
    parser.add_argument("--viz-only", action="store_true",
                        help="Only generate visualization, skip sync")
    parser.add_argument("--viz-cleanup", action="store_true",
                        help="Clean up old visualization sessions")
    parser.add_argument("--clear-cache", action="store_true",
                        help="Clear the outcome cache")

    # Provider deactivation
    parser.add_argument("--deactivate-providers", nargs="*", metavar="PROVIDER",
                        default=None,
                        help="Deactivate providers: zip and remove their directories. "
                             "Pass provider names or omit for all. "
                             "Use --activate-providers to restore.")
    parser.add_argument("--activate-providers", nargs="*", metavar="PROVIDER",
                        default=None,
                        help="Activate (restore) providers from backup zips. "
                             "Pass provider names or omit for all backed-up providers.")
    parser.add_argument("--deactivation-status", action="store_true",
                        help="Show provider deactivation status")

    # Backup & Restore
    parser.add_argument("--backup", nargs="*", metavar="PROVIDER",
                         default=None,
                         help="Create a timestamped backup of provider directories "
                              "and project config. Pass provider names or omit for all. "
                              "Use --label to add a description.")
    parser.add_argument("--label", metavar="TEXT", default=None,
                        help="Optional label/description for --backup")
    parser.add_argument("--restore", metavar="ARCHIVE",
                        help="Restore provider directories from a backup archive. "
                             "Use --restore-providers to select specific providers.")
    parser.add_argument("--restore-providers", nargs="*", metavar="PROVIDER",
                        default=None,
                        help="Which providers to restore from --restore (default: all)")
    parser.add_argument("--force", action="store_true",
                        help="Force overwrite when restoring (--restore)")
    parser.add_argument("--list-backups", action="store_true",
                        help="List all available backup archives with metadata")
    parser.add_argument("--delete-backup", metavar="ARCHIVE",
                        help="Delete a specific backup archive")
    parser.add_argument("--prune-backups", action="store_true",
                        help="Delete old backups according to retention policy")

    # Config audit
    parser.add_argument("--audit-config", action="store_true",
                        help="Audit project config against templates + role-defaults. "
                             "Reports roles_without_template (error), templates_without_default "
                             "(info), deprecated_roles (warning), orphaned_pipelines (warning). "
                             "Use --apply to additionally comment out deprecated roles in "
                             ".meta-config/project.yaml (idempotent, comment-preserving).")
    parser.add_argument("--apply", action="store_true",
                        help="When combined with --audit-config: rewrite project.yaml to comment "
                             "out deprecated roles. No-op without --audit-config.")

    # Admin UI server (zero-dependency stdlib HTTP server)
    parser.add_argument("--admin", action="store_true",
                        help="Start Admin UI server after running sync (port: --admin-port)")
    parser.add_argument("--admin-only", action="store_true",
                        help="Start Admin UI server without running sync first")
    parser.add_argument("--admin-port", type=int, default=7420,
                        help="Admin UI server port (default: 7420)")

    # Model discovery
    parser.add_argument("--update-models", action="store_true",
                        help="Update model registry from provider APIs")

    # External skill management
    parser.add_argument("--add-skill", metavar="REPO_URL",
                        help="Register a new external skill: git submodule add + config entry")
    parser.add_argument("--skill-name", metavar="NAME",
                        help="Skill identifier (used in config/skills-registry.yaml)")
    parser.add_argument("--source", metavar="PATH",
                        help="Path to skill directory within the submodule repo")
    parser.add_argument("--role", metavar="ROLE",
                        help="Agent role name for the generated wrapper agent")
    parser.add_argument("--entry", metavar="FILE", default="SKILL.md",
                        help="Entry file within the skill directory (default: SKILL.md)")

    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    agent_meta_root = find_agent_meta_root(script_path)

    log = SyncLog()

    if args.clear_cache:
        from lib.cache import CACHE_FILE, invalidate
        invalidate(CACHE_FILE)
        print("Outcome cache cleared.")
        return

    if args.update_models:
        from lib.model_discovery import discover_models
        print("  i  Updating model registry...")
        discover_models()
        return

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
        return

    if args.dry_run:
        print("DRY-RUN — no files will be written\n")

    # Regenerate derived schema fields (roles enum) from role-defaults.yaml.
    # Runs early so even short-circuit modes (--create-rule, --validate, …)
    # pick up the latest enum. Honors --dry-run.
    update_roles_enum(agent_meta_root, log, dry_run=args.dry_run)

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
        return

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
            return

    # All other modes require --config (or auto-detect)
    if not args.config:
        cwd = Path.cwd()
        for candidate in _CONFIG_CANDIDATES:
            if (cwd / candidate).exists():
                args.config = candidate
                print(f"  i  auto-detected config: {candidate}")
                break
        if not args.config:
            print("  !  No config found. Pass --config or create .meta-config/project.yaml",
                  file=sys.stderr)
            sys.exit(1)

    config_resolved = Path(args.config).resolve()
    config_parent_name = config_resolved.parent.name
    # .meta-config/project.yaml → project root is two levels up
    if config_parent_name in (".meta-config",):
        project_root = config_resolved.parent.parent
    else:
        project_root = config_resolved.parent
    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    variables, pre_warnings = build_variables(config, agent_meta_root)
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
        log.warning(w)

    if args.fill_defaults:
        mode = "fill-defaults"
        fill_defaults(config_path, agent_meta_root, log, args.dry_run)

    elif args.audit_config:
        mode = "audit-config"
        report = audit_config(agent_meta_root, config_path)
        print(format_report(report))
        if args.apply:
            if args.dry_run:
                log.info("audit-config",  # noqa: PLE1205
                         f"--apply skipped (dry-run): would disable "
                         f"{len(report.deprecated_roles)} deprecated role(s)")
            else:
                changed = apply_audit(report, config_path)
                if changed:
                    log.info("audit-config",  # noqa: PLE1205
                             f"commented out {changed} deprecated role line(s) in "
                             f"{config_path}")
                else:
                    log.info("audit-config",  # noqa: PLE1205
                             "no changes applied (nothing to disable)")

    elif args.only_variables:
        mode = "only-variables"
        provider_config = load_providers_config(agent_meta_root)
        providers = resolve_providers(config, provider_config)
        only_variables(project_root, variables, log, args.dry_run,
                       providers=providers, provider_config=provider_config)

    elif args.create_ext:
        mode = f"create-ext:{args.create_ext}"
        role_map = build_role_map(agent_meta_root)
        roles = list(role_map.keys()) if args.create_ext == "all" else [args.create_ext]
        for role in roles:
            create_extension(project_root, config, variables, role, log, args.dry_run,
                             agent_meta_root=agent_meta_root)

    elif args.update_ext:
        mode = "update-ext"
        update_extensions(project_root, variables, log, args.dry_run,
                          agent_meta_root=agent_meta_root)

    elif args.create_rule:
        mode = f"create-rule:{args.create_rule}"
        create_rule(project_root, args.create_rule, log, args.dry_run)

    elif args.create_hook:
        mode = f"create-hook:{args.create_hook}"
        create_hook(project_root, args.create_hook, log, args.dry_run)

    elif args.create_command:
        mode = f"create-command:{args.create_command}"
        create_command(project_root, args.create_command, log, args.dry_run)

    elif args.viz_only:
        mode = "viz-only"
        # Override viz config
        if "viz" not in config:
            config["viz"] = {}
        config["viz"]["enabled"] = True
        generate_viz(agent_meta_root, project_root, config, log, args.dry_run)

    elif args.viz_cleanup:
        mode = "viz-cleanup"
        viz_cfg = config.get("viz", {})
        retention = viz_cfg.get("report", {}).get("retention_days", 7)
        cleanup_old_sessions(project_root, retention_days=retention,
                             log=log, dry_run=args.dry_run)

    elif args.deactivation_status:
        mode = "deactivation-status"
        provider_config = load_providers_config(agent_meta_root)
        status = get_deactivation_status(project_root, config, provider_config)
        import json as _json
        print(_json.dumps(status, indent=2, ensure_ascii=False))

    elif args.deactivate_providers is not None:
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
            variables, _ = build_variables(config, agent_meta_root)
            for prov in resolve_providers(config, provider_config):
                sync_context_for_provider(agent_meta_root, project_root, config,
                                          variables, log, args.dry_run,
                                          prov, provider_config)
        import json as _json
        print(_json.dumps(results, indent=2, ensure_ascii=False))

    elif args.activate_providers is not None:
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
            variables, _ = build_variables(config, agent_meta_root)
            for prov in resolve_providers(config, provider_config):
                sync_context_for_provider(agent_meta_root, project_root, config,
                                          variables, log, args.dry_run,
                                          prov, provider_config)
        import json as _json
        print(_json.dumps(results, indent=2, ensure_ascii=False))

    elif args.backup is not None:
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

    elif args.restore:
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

    elif args.list_backups:
        mode = "list-backups"
        provider_config = load_providers_config(agent_meta_root)
        result = list_backups(project_root, config, provider_config)
        import json as _json
        print(_json.dumps(result, indent=2, ensure_ascii=False))

    elif args.delete_backup:
        mode = "delete-backup"
        result = delete_backup(project_root, args.delete_backup, config, log, args.dry_run)
        import json as _json
        print(_json.dumps(result, indent=2, ensure_ascii=False))

    elif args.prune_backups:
        mode = "prune-backups"
        result = prune_backups(project_root, config, log, args.dry_run)
        import json as _json
        print(_json.dumps(result, indent=2, ensure_ascii=False))

    elif args.validate:
        mode = "validate"
        if args.dry_run:
            print("DRY-RUN — validation will not write files\n")

        # Consistency checks always run (no test repo required). These validate
        # agent templates, cross-references, dual-tree parity and handoff
        # contracts against the agent-meta sources themselves.
        consistency_errors = _run_consistency_checks(agent_meta_root)

        test_repo_path = resolve_test_repo_path(config, project_root, log)
        if test_repo_path is None or not test_repo_path.exists():
            reason = (f"configured path {test_repo_path} does not exist"
                      if test_repo_path else
                      "not configured (set test-repo.path in .meta-config/project.yaml "
                      "or AGENT_META_TEST_REPO)")
            log.info("test-repo",  # noqa: PLE1205
                     f"Skipping test-repo sync validation — {reason}. "
                     "Consistency checks still ran.")
            sys.exit(1 if consistency_errors else 0)
        success = validate_test_repo(test_repo_path, agent_meta_root, config, log, args.dry_run)
        if not success or consistency_errors:
            sys.exit(1)

    else:
        provider_config = load_providers_config(agent_meta_root)
        providers = resolve_providers(config, provider_config)
        mode = "init" if args.init else "sync"
        log.info("providers", "active: " + ", ".join(providers))  # noqa: PLE1205
        # Log resolved DoD
        preset_name = config.get("dod-preset", "full")
        dod_resolved = resolve_dod(config, agent_meta_root)
        dod_summary = ", ".join(f"{k}: {v}" for k, v in dod_resolved.items())
        log.info("DoD", f"preset '{preset_name}' -> {dod_summary}")  # noqa: PLE1205
        # Log resolved rules-preset
        rules_preset_name = config.get("rules-preset", "default")
        rules_resolved = resolve_rules(config, agent_meta_root)
        if rules_resolved:
            rules_summary = ", ".join(
                f"{r}: {'+'.join(k for k, v in opts.items() if v is not False and v != 'skip') or 'alwaysApply=false'}"
                for r, opts in rules_resolved.items()
            )
            log.info("rules", f"preset '{rules_preset_name}' -> {rules_summary}")  # noqa: PLE1205
        else:
            log.info("rules", f"preset '{rules_preset_name}' -> all alwaysApply (default)")  # noqa: PLE1205
        # Load platform-config variables ({{platform.*}} placeholders)
        platform_vars = load_platform_config(agent_meta_root, project_root, platforms, log)
        if platform_vars is not None:
            log.info("platform-config", f"loaded {len(platform_vars)} platform variable(s) for: {', '.join(platforms)}")  # noqa: PLE1205
        is_claude = "Claude" in providers
        claude_pc = provider_config.get("Claude", {})
        gitignore_cfg = config.get("gitignore", {})
        base_gitignore_entries: list[str] = []
        if is_claude:
            if gitignore_cfg.get("local", True):
                base_gitignore_entries = list(claude_pc.get("gitignore_entries", [
                    ".claude/settings.local.json",
                    ".claude/agent-memory-local/",
                    "CLAUDE.personal.md",
                    "sync.log",
                ]))
            if gitignore_cfg.get("generated", False):
                for _prov in providers:
                    _pc = provider_config.get(_prov, {})
                    for _dir_key in ("agents_dir", "rules_dir", "hooks_dir"):
                        _d = _pc.get(_dir_key)
                        if _d:
                            base_gitignore_entries.append(_d + "/")
                    if _pc.get("has_commands") and _pc.get("commands_dir"):
                        base_gitignore_entries.append(_pc["commands_dir"] + "/")
            if gitignore_cfg.get("settings", False):
                for _prov in providers:
                    _pc = provider_config.get(_prov, {})
                    _sf = _pc.get("settings_file")
                    if _sf:
                        base_gitignore_entries.append(_sf)
                    _ctx = _pc.get("context_file")
                    if _ctx and _ctx != "CLAUDE.md":
                        base_gitignore_entries.append(_ctx)
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
        if args.init:
            init_secrets_template(agent_meta_root, project_root, config, log, args.dry_run)
        # Per-provider sync
        debug_mode = config.get("debug-mode", False)
        if debug_mode:
            log.info("debug-mode", "active — injecting debug block into all agents")  # noqa: PLE1205
        allow_committed_secrets = config.get("allow-committed-secrets", False)
        mcp_gitignore_extras: list[str] = []
        for provider in providers:
            pc = provider_config[provider]
            log.provider_header(provider)
            if not is_provider_active(config, provider):
                log.info("deactivation", f"provider '{provider}' is deactivated — skipping all output")  # noqa: PLE1205
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
        # Cleanup legacy files for removed providers
        all_known_providers = provider_config.keys()
        active_context_files = set()
        for prov in providers:
            if prov == "providers": continue
            if is_provider_active(config, prov):
                pc = provider_config.get(prov, {})
                c_file = pc.get("context_file", f"{prov.upper()}.md")
                if c_file == "CLAUDE.md" and prov != "Claude":
                    c_file = "AGENTS.md"
                active_context_files.add(c_file)

        for prov in all_known_providers:
            if prov == "providers": continue # Skip the top-level key if present
            if prov not in providers or not is_provider_active(config, prov):
                pc = provider_config.get(prov, {})
                
                # Default paths if missing from config
                a_dir = pc.get("agents_dir", f".{prov.lower()}/agents")
                c_file = pc.get("context_file", f"{prov.upper()}.md")
                if c_file == "CLAUDE.md" and prov != "Claude":
                    # E.g. Opencode uses AGENTS.md, fallback
                    c_file = "AGENTS.md"
                
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
            if pc.get("has_hooks", False):
                sync_hooks(agent_meta_root, project_root, config, log, args.dry_run,
                           provider=provider, provider_config=provider_config)
            else:
                log.info("hooks", f"skipped for {provider} — not supported")  # noqa: PLE1205
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
        # Check pinned commits + warn for unknown/unapproved skills in project config
        ext_config = load_external_skills_config(agent_meta_root)
        check_pinned_commits(ext_config, agent_meta_root, log)
        if "external-skills" in config:
            known_skills = set(ext_config.get("skills", {}).keys())
            for skill_name in config["external-skills"]:
                if skill_name not in known_skills:
                    log.warning(f"external-skills: '{skill_name}' not found in external-skills.config.json -- skipping")
                elif not ext_config["skills"][skill_name].get("approved", False):
                    log.warning(f"external-skills: '{skill_name}' is not approved by meta-maintainer -- skipping")
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
                log.info(  # noqa: PLE1205
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
            log.info("config-audit", f"skipped (error: {exc})")  # noqa: PLE1205

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
        except Exception:  # noqa: BLE001, S110
            pass

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


if __name__ == "__main__":
    main()
