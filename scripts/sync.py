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
import sys
from pathlib import Path

# Add scripts/ directory to sys.path so lib/ is importable regardless of cwd
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.log import SyncLog
from lib.io import _load_yaml_or_json, _write_yaml
from lib.config import (
    load_config, find_agent_meta_root, build_variables,
    fill_defaults, read_version, read_git_version, substitute,
)
from lib.roles import build_role_map
from lib.dod import resolve_dod
from lib.providers import load_providers_config, resolve_providers, resolve_provider_options
from lib.platform import load_platform_config
from lib.agents import (
    collect_sources, sync_agents_for_provider,
    build_agent_hints, build_agent_table,
    extract_frontmatter_field,
)
from lib.rules import sync_rules, sync_speech_mode, create_rule, resolve_rules
from lib.hooks import sync_hooks, create_hook
from lib.commands import sync_commands_for_provider, create_command
from lib.skills import (
    load_external_skills_config, check_pinned_commits, sync_external_skills_for_provider, add_skill,
)
from lib.extensions import create_extension, update_extensions
from lib.mcp import generate_mcp_artifacts, resolve_active_mcp_servers, init_secrets_template
from lib.isolation import sync_provider_isolation
from lib.io import SyncError
from lib.context import (
    sync_context_for_provider, init_claude_personal, init_opencode_personal,
    init_settings_json, init_settings_local_json, ensure_gitignore_entries,
    init_claude_md, only_variables, sync_prompts_for_continue, sync_snippets_for_provider,
)
from lib.viz import (
    generate_viz, get_gitignore_entries as viz_gitignore_entries,
    cleanup_old_sessions,
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
        log.info("test-repo", f"resolved from env var {env_var_name}: {resolved}")
        return resolved

    # 2. Config path (relative or absolute)
    test_cfg = config.get("test-repo", {})
    if not test_cfg:
        log.info("test-repo", "not configured in project.yaml")
        return None

    raw_path = test_cfg.get("path")
    if not raw_path:
        log.warn("test-repo.path is not set in project.yaml")
        return None

    path_obj = Path(raw_path)
    if path_obj.is_absolute():
        resolved = path_obj.resolve()
    else:
        # Relative to project_root (workspace)
        resolved = (project_root / path_obj).resolve()

    log.info("test-repo", f"resolved from config: {resolved}")
    return resolved


def validate_test_repo(test_repo_path: Path, agent_meta_root: Path, config: dict,
                       log: SyncLog, dry_run: bool) -> bool:
    """Validate by performing a sync into the test repository and checking results.

    Returns True if validation passed, False otherwise.
    """
    if not test_repo_path.exists():
        log.warn(
            f"Test repository not found at: {test_repo_path}\n"
            f"  Set AGENT_META_TEST_REPO environment variable or\n"
            f"  configure test-repo.path in .meta-config/project.yaml")
        return False

    if not test_repo_path.is_dir():
        log.warn(f"Path exists but is not a directory: {test_repo_path}")
        return False

    log.info("test-repo", f"validating against: {test_repo_path}")

    # Perform a sync into the test repository
    from lib.agents import collect_sources, sync_agents_for_provider
    from lib.config import build_variables, substitute
    from lib.providers import load_providers_config, resolve_providers
    from lib.dod import resolve_dod
    from lib.context import sync_context_for_provider, sync_snippets_for_provider
    from lib.rules import sync_rules, sync_speech_mode
    from lib.hooks import sync_hooks
    from lib.commands import sync_commands_for_provider
    from lib.skills import sync_external_skills_for_provider

    test_variables, pre_warnings = build_variables(config, agent_meta_root)
    # Override AGENT_META_REPO to point to test repo for validation context
    test_variables["PROJECT_NAME"] = test_variables.get("PROJECT_NAME", "agent-meta-test")

    provider_config = load_providers_config(agent_meta_root)
    providers = resolve_providers(config, provider_config)

    validation_errors = 0
    for provider in providers:
        pc = provider_config[provider]
        log.info("test-repo", f"syncing agents for provider: {provider}")
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
            log.warn(f"test-repo: Found {len(error_lines)} error(s) in sync.log:")
            for el in error_lines:
                log.warn(f"test-repo:   {el}")
            validation_errors += len(error_lines)
        else:
            log.info("test-repo", "sync.log contains no errors")
    else:
        log.info("test-repo", "sync.log not found in test repository (first validation run)")

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
        from lib.cache import invalidate, CACHE_FILE
        invalidate(CACHE_FILE)
        print("Outcome cache cleared.")
        return

    if args.dry_run:
        print("DRY-RUN — no files will be written\n")

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
    git_version = read_git_version(agent_meta_root)
    if git_version != "unknown" and git_version != source_version:
        log.warn(
            f"agent-meta version mismatch: config says v{source_version}, "
            f"but submodule git tag is v{git_version} — "
            f"run: git submodule update --init .agent-meta"
        )

    for w in pre_warnings:
        log.warn(w)

    if args.fill_defaults:
        mode = "fill-defaults"
        fill_defaults(config_path, agent_meta_root, log, args.dry_run)

    elif args.only_variables:
        mode = "only-variables"
        only_variables(project_root, variables, log, args.dry_run)

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

    elif args.validate:
        mode = "validate"
        if args.dry_run:
            print("DRY-RUN — validation will not write files\n")
        test_repo_path = resolve_test_repo_path(config, project_root, log)
        if test_repo_path is None:
            log.error("test-repo",
                      "No test repository configured.\n"
                      "  Add to .meta-config/project.yaml:\n"
                      "  test-repo:\n"
                      "    enabled: true\n"
                      "    path: \"../agent-meta-test\"\n"
                      "  Or set AGENT_META_TEST_REPO environment variable.")
            sys.exit(1)
        success = validate_test_repo(test_repo_path, agent_meta_root, config, log, args.dry_run)
        if not success:
            sys.exit(1)

    else:
        provider_config = load_providers_config(agent_meta_root)
        providers = resolve_providers(config, provider_config)
        mode = "init" if args.init else "sync"
        log.info("providers", "active: " + ", ".join(providers))
        # Log resolved DoD
        preset_name = config.get("dod-preset", "full")
        dod_resolved = resolve_dod(config, agent_meta_root)
        dod_summary = ", ".join(f"{k}: {v}" for k, v in dod_resolved.items())
        log.info("DoD", f"preset '{preset_name}' -> {dod_summary}")
        # Log resolved rules-preset
        rules_preset_name = config.get("rules-preset", "default")
        rules_resolved = resolve_rules(config, agent_meta_root)
        if rules_resolved:
            rules_summary = ", ".join(
                f"{r}: {'+'.join(k for k, v in opts.items() if v is not False and v != 'skip') or 'alwaysApply=false'}"
                for r, opts in rules_resolved.items()
            )
            log.info("rules", f"preset '{rules_preset_name}' -> {rules_summary}")
        else:
            log.info("rules", f"preset '{rules_preset_name}' -> all alwaysApply (default)")
        # Load platform-config variables ({{platform.*}} placeholders)
        platform_vars = load_platform_config(agent_meta_root, project_root, platforms, log)
        if platform_vars is not None:
            log.info("platform-config", f"loaded {len(platform_vars)} platform variable(s) for: {', '.join(platforms)}")
        is_claude = "Claude" in providers
        claude_pc = provider_config.get("Claude", {})
        gitignore_cfg = config.get("gitignore", {})
        base_gitignore_entries: list[str] = []

        # Claude-specific local entries (personal files, local settings)
        if is_claude and gitignore_cfg.get("local", True):
            base_gitignore_entries = list(claude_pc.get("gitignore_entries", [
                ".claude/settings.local.json",
                ".claude/agent-memory-local/",
                "CLAUDE.personal.md",
                "sync.log",
            ]))

        # Provider-generated directories (agents/, rules/, hooks/, commands/)
        # Not Claude-specific — applies to all active providers
        if gitignore_cfg.get("generated", False):
            for _prov in providers:
                _pc = provider_config.get(_prov, {})
                for _dir_key in ("agents_dir", "rules_dir", "hooks_dir"):
                    _d = _pc.get(_dir_key)
                    if _d:
                        base_gitignore_entries.append(_d + "/")
                if _pc.get("has_commands") and _pc.get("commands_dir"):
                    base_gitignore_entries.append(_pc["commands_dir"] + "/")

        # Provider settings files (settings.json, GEMINI.md, AGENTS.md etc.)
        # Not Claude-specific — applies to all active providers
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
            init_claude_md(agent_meta_root, project_root, config, variables, log, args.dry_run)
            init_claude_personal(agent_meta_root, project_root, log, args.dry_run)
            init_settings_json(project_root, log, args.dry_run)
            init_settings_local_json(project_root, log, args.dry_run)
        if args.init:
            init_secrets_template(agent_meta_root, project_root, config, log, args.dry_run)
        # Per-provider sync
        debug_mode = config.get("debug-mode", False)
        if debug_mode:
            log.info("debug-mode", "active — injecting debug block into all agents")
        allow_committed_secrets = config.get("allow-committed-secrets", False)
        mcp_gitignore_extras: list[str] = []
        for provider in providers:
            pc = provider_config[provider]
            log.provider_header(provider)
            sync_context_for_provider(agent_meta_root, project_root, config, variables,
                                      log, args.dry_run, provider, provider_config)
            sync_agents_for_provider(agent_meta_root, project_root, config, variables,
                                     log, args.dry_run, provider, provider_config,
                                     platform_vars=platform_vars,
                                     debug_mode=debug_mode)
            if provider == "Continue":
                sync_prompts_for_continue(agent_meta_root, project_root, config,
                                          variables, log, args.dry_run,
                                          provider_config=provider_config)
            if pc["has_rules"]:
                sync_rules(agent_meta_root, project_root, config, log, args.dry_run,
                           platform_vars=platform_vars, variables=variables,
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
            if pc["has_hooks"]:
                sync_hooks(agent_meta_root, project_root, config, log, args.dry_run,
                           provider=provider, provider_config=provider_config)
            else:
                log.info("hooks", f"skipped for {provider} — not supported")
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
                    log.warn(f"external-skills: '{skill_name}' not found in external-skills.config.json -- skipping")
                elif not ext_config["skills"][skill_name].get("approved", False):
                    log.warn(f"external-skills: '{skill_name}' is not approved by meta-maintainer -- skipping")
        # Update .gitignore managed block: base entries + per-provider entries + skill entries
        # Collect gitignore_entries from all active non-Claude providers
        extra_provider_entries: list[str] = []
        for _p in providers:
            if _p == "Claude":
                continue  # already in base_gitignore_entries
            _pc = provider_config.get(_p, {})
            if _pc.get("has_settings") and not _pc.get("gitignore_entries"):
                log.warn(f"provider '{_p}' has has_settings=true but no gitignore_entries — local settings may be accidentally committed")
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
            )
            ensure_gitignore_entries(project_root, log, args.dry_run,
                                     exact_entries=all_gitignore_entries)
        else:
            all_entries = base_gitignore_entries + extra_provider_entries + mcp_gitignore_extras
            if all_entries:
                ensure_gitignore_entries(project_root, log, args.dry_run,
                                         exact_entries=all_entries)

    # Visualization: generate static mindmap if requested (static or full mode)
    viz_mode = args.viz_mode or viz_cfg.get("mode", "off")
    if args.viz or viz_cfg.get("enabled", False) or viz_mode in ("static", "full"):
        generate_viz(agent_meta_root, project_root, config, log, args.dry_run)

    log_path = project_root / LOGFILE
    _providers = resolve_providers(config, load_providers_config(agent_meta_root)) if config else []
    _speech = config.get("speech-mode", "full") if config else "full"
    log.write(log_path, args.config, source_version, mode, platforms, args.dry_run,
              providers=_providers, speech_mode=_speech)


if __name__ == "__main__":
    main()
