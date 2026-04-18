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
from lib.rules import sync_rules, sync_speech_mode, create_rule
from lib.hooks import sync_hooks, create_hook
from lib.commands import sync_commands_for_provider, create_command
from lib.skills import (
    load_external_skills_config, check_pinned_commits, sync_external_skills, add_skill,
)
from lib.extensions import create_extension, update_extensions
from lib.context import (
    sync_context_for_provider, init_claude_personal, init_settings_json,
    init_settings_local_json, ensure_gitignore_entries, init_claude_md,
    only_variables, sync_prompts_for_continue, sync_snippets,
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

def _collect_skill_gitignore_entries(config: dict, ext_config: dict) -> list[str]:
    """Return .gitignore paths for skills with gitignore: true in project config.

    Only generates entries for skills that are approved + enabled (two-gate).
    """
    entries: list[str] = []
    project_skills = config.get("external-skills", {})
    for skill_name, skill_project_cfg in project_skills.items():
        if not skill_project_cfg.get("gitignore", False):
            continue
        skill_meta = ext_config.get("skills", {}).get(skill_name, {})
        if not skill_meta.get("approved", False):
            continue
        if not skill_project_cfg.get("enabled", False):
            continue
        entries.append(f".claude/skills/{skill_name}/")
    return entries


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
        # Load platform-config variables ({{platform.*}} placeholders)
        platform_vars = load_platform_config(agent_meta_root, project_root, platforms, log)
        if platform_vars is not None:
            log.info("platform-config", f"loaded {len(platform_vars)} platform variable(s) for: {', '.join(platforms)}")
        is_claude = "Claude" in providers
        if args.init or is_claude:
            init_claude_md(agent_meta_root, project_root, config, variables, log, args.dry_run)
            init_claude_personal(agent_meta_root, project_root, log, args.dry_run)
            init_settings_json(project_root, log, args.dry_run)
            init_settings_local_json(project_root, log, args.dry_run)
            claude_pc = provider_config.get("Claude", {})
            base_gitignore_entries = claude_pc.get("gitignore_entries", [
                ".claude/settings.local.json",
                ".claude/agent-memory-local/",
                "CLAUDE.personal.md",
                "sync.log",
            ])
            # Skill gitignore entries are collected after skills are processed (below)
            # and merged via exact_entries so stale entries are removed automatically.
        # Per-provider sync
        for provider in providers:
            pc = provider_config[provider]
            log.provider_header(provider)
            sync_agents_for_provider(agent_meta_root, project_root, config, variables,
                                     log, args.dry_run, provider, provider_config,
                                     platform_vars=platform_vars)
            sync_context_for_provider(agent_meta_root, project_root, config, variables,
                                      log, args.dry_run, provider, provider_config)
            if provider == "Continue":
                sync_prompts_for_continue(agent_meta_root, project_root, config,
                                          variables, log, args.dry_run)
            if pc["has_rules"]:
                sync_rules(agent_meta_root, project_root, config, log, args.dry_run,
                           platform_vars=platform_vars, variables=variables,
                           rules_dir=pc.get("rules_dir"))
                sync_speech_mode(agent_meta_root, project_root, config, log, args.dry_run,
                                 rules_dir=pc.get("rules_dir"))
            if pc["has_hooks"]:
                sync_hooks(agent_meta_root, project_root, config, log, args.dry_run)
            if pc.get("has_commands", False):
                sync_commands_for_provider(agent_meta_root, project_root, config, log,
                                           args.dry_run, provider, variables=variables)
        sync_snippets(agent_meta_root, project_root, config, log, args.dry_run)
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
        sync_external_skills(agent_meta_root, project_root, config, variables, log, args.dry_run)
        # Update .gitignore managed block: base entries + gitignore:true skill entries
        if is_claude:
            skill_gitignore_entries = _collect_skill_gitignore_entries(config, ext_config)
            all_gitignore_entries = base_gitignore_entries + skill_gitignore_entries
            ensure_gitignore_entries(project_root, log, args.dry_run,
                                     exact_entries=all_gitignore_entries)

    log_path = project_root / LOGFILE
    _providers = resolve_providers(config, load_providers_config(agent_meta_root)) if config else []
    _speech = config.get("speech-mode", "full") if config else "full"
    log.write(log_path, args.config, source_version, mode, platforms, args.dry_run,
              providers=_providers, speech_mode=_speech)


if __name__ == "__main__":
    main()
