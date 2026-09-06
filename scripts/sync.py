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
from __future__ import annotations

import argparse
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

# Moved symbols (#481): validate helpers, pre-config CLI modes, the shared
# _SyncContext, the _handle_* mode handlers and the common tail live in
# lib/cli_commands.py; sync.py keeps only the CLI shell (parser, dispatch
# registry, main) and imports the handlers back for _MODE_HANDLERS.
from lib.cli_commands import (
    _SyncContext,
    _build_context,
    _handle_activate_providers,
    _handle_audit_config,
    _handle_backup,
    _handle_create_command,
    _handle_create_ext,
    _handle_create_hook,
    _handle_create_rule,
    _handle_deactivate_providers,
    _handle_deactivation_status,
    _handle_delete_backup,
    _handle_fill_defaults,
    _handle_list_backups,
    _handle_only_variables,
    _handle_prune_backups,
    _handle_restore,
    _handle_sync,
    _handle_update_ext,
    _handle_validate,
    _handle_viz_cleanup,
    _handle_viz_only,
    _run_common_tail,
)
from lib.config import find_agent_meta_root
from lib.log import SyncLog
# Re-exported for tests: tests/test_knowledge_sync_integration.py reads
# sync_module.sync_knowledge_engine (kept stable during the #481 split).
from lib.knowledge import sync_knowledge_engine  # noqa: F401  (deliberate re-export)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _normalize_check_dry_run(args) -> None:
    """--check is a read-only CI gate: it must never allow real writes.

    If the caller forgot --dry-run, force it rather than silently writing files.
    """
    if getattr(args, "check", False) and not getattr(args, "dry_run", False):
        args.dry_run = True


def _build_arg_parser() -> argparse.ArgumentParser:
    """Construct the sync.py CLI argument parser (flag-based interface)."""
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
    parser.add_argument("--test-plugin", metavar="ID", default=None,
                        help="Run the health check for one plugin from the catalog and exit.")
    parser.add_argument("--render-standalone", action="store_true",
                        help="Render fully self-contained, English-only copies of every "
                             "1-generic agent template into standalone/agents/ — no Python/"
                             "project.yaml required to use them, no {{PLACEHOLDER}} left over. "
                             "Combine with --check for a read-only CI drift check.")
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

    # Cross-harness dev isolation (issue #547)
    parser.add_argument("--harness", metavar="NAME", default=None,
                        help="Activate a harness from config/harnesses/<NAME>.yaml and "
                             "enforce its write isolation: sync refuses to run when the "
                             "project root lies outside the harness's declared checkout-"
                             "root. Overrides the AGENT_META_HARNESS environment variable. "
                             "No harness active by default (fully backwards compatible).")

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
    return parser


# Ordered (predicate, handler) table. Order mirrors the original if/elif
# chain exactly -- the first matching predicate wins, so flag precedence is
# preserved. The default (no predicate matches) is _handle_sync.
_MODE_HANDLERS = [
    (lambda a: a.fill_defaults, _handle_fill_defaults),
    (lambda a: a.audit_config, _handle_audit_config),
    (lambda a: a.only_variables, _handle_only_variables),
    (lambda a: a.create_ext, _handle_create_ext),
    (lambda a: a.update_ext, _handle_update_ext),
    (lambda a: a.create_rule, _handle_create_rule),
    (lambda a: a.create_hook, _handle_create_hook),
    (lambda a: a.create_command, _handle_create_command),
    (lambda a: a.viz_only, _handle_viz_only),
    (lambda a: a.viz_cleanup, _handle_viz_cleanup),
    (lambda a: a.deactivation_status, _handle_deactivation_status),
    (lambda a: a.deactivate_providers is not None, _handle_deactivate_providers),
    (lambda a: a.activate_providers is not None, _handle_activate_providers),
    (lambda a: a.backup is not None, _handle_backup),
    (lambda a: a.restore, _handle_restore),
    (lambda a: a.list_backups, _handle_list_backups),
    (lambda a: a.delete_backup, _handle_delete_backup),
    (lambda a: a.prune_backups, _handle_prune_backups),
    (lambda a: a.validate, _handle_validate),
]


def _dispatch(ctx: _SyncContext) -> None:
    """Select and run the mode handler matching the parsed CLI flags."""
    for predicate, handler in _MODE_HANDLERS:
        if predicate(ctx.args):
            handler(ctx)
            return
    _handle_sync(ctx)


def main() -> None:
    """Parse CLI args and drive the sync: early modes, dispatch, common tail."""
    parser = _build_arg_parser()
    args = parser.parse_args()
    _normalize_check_dry_run(args)

    script_path = Path(__file__).resolve()
    agent_meta_root = find_agent_meta_root(script_path)
    log = SyncLog()

    ctx = _build_context(args, agent_meta_root, log)
    if ctx is None:
        return

    _dispatch(ctx)
    _run_common_tail(ctx)


if __name__ == "__main__":
    main()
