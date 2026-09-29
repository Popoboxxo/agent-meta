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
import contextlib
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
    handle_scan_staged,
)
from lib.config import find_agent_meta_root
from lib.io import clear_gitignore_cache
from lib.log import SyncLog
from lib.se_validate import _handle_validate_se
from lib.spec_plan_validate import _handle_validate_spec_plan
from lib.checkpoint_record import _handle_checkpoint
from lib.plan_ledger import handle_update_plan_ledger
from lib.rehydrate import _handle_rehydrate
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
    parser.add_argument("--cleanup-preview", action="store_true",
                        help="Planning-only, side-effect-free JSON preview of the stale "
                             "agent files a sync would remove. Emits exactly "
                             "one JSON object on stdout; writes nothing (no index write, "
                             "no unlink, no backup, no clone/submodule). Exit code 0 even "
                             "for a non-empty stale set, 1 only on internal failure.")
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
    parser.add_argument("--validate-se", action="store_true",
                        help="Standalone SE-cascade validation (issue #338): read-only "
                             "checks over the project's docs/se artifacts against the "
                             "#339 conventions (B1-B5): REQ frontmatter enums, taxonomy "
                             "naming incl. version-suffix ban, ADR lifecycle + open_adrs "
                             "integrity, L2 separation, review IDs. Exit 0 when clean or "
                             "when no SE artifacts exist; exit 1 with a findings list "
                             "otherwise.")
    parser.add_argument("--validate-spec-plan", action="store_true",
                        help="Standalone spec/plan-workflow validation (F12): checks the "
                             "project's docs/specs and docs/plans artifacts for required "
                             "sections, placeholders, traceability, approval markers, ledger "
                             "format and the plan task graph. Exit 0 when clean, when no "
                             "artifacts exist, or when the workflow is disabled; exit 1 with "
                             "a findings list otherwise.")
    parser.add_argument("--rehydrate", action="store_true",
                        help="Read-only resume path: print the resume context of the "
                             "newest unfinished session (plan/task/checkpoint identity, "
                             "next open task, drift). Writes nothing, runs no sync, and "
                             "exits 0 even when there is nothing to resume.")
    parser.add_argument("--checkpoint", action="store_true",
                        help="Write mode: append one checkpoint to the session "
                             "store (.meta-viz/checkpoints/ and its progress "
                             "write-through). Requires --session-id, --task, "
                             "--agent and --status "
                             "(completed|failed|timeout|in_progress). Plan "
                             "identity is explicit only: --plan-id, or --plan "
                             "<path> to derive it. Exit 1 on missing arguments "
                             "or a store error, 0 after a successful write.")
    parser.add_argument("--session-id", metavar="ID", default=None,
                        help="Session id for --checkpoint (one file per session "
                             "under .meta-viz/checkpoints/).")
    parser.add_argument("--agent", metavar="NAME", default=None,
                        help="Agent name for --checkpoint.")
    parser.add_argument("--plan", metavar="PATH", default=None,
                        help="Plan path for --checkpoint; its plan id is derived "
                             "from the document (or its file-stem slug). Never "
                             "random. Ignored when --plan-id is given.")
    parser.add_argument("--plan-id", metavar="ID", default=None,
                        help="Explicit plan id for --checkpoint. Takes precedence "
                             "over --plan.")
    parser.add_argument("--description", metavar="TEXT", default=None,
                        help="Task description for --checkpoint.")
    parser.add_argument("--summary", metavar="TEXT", default=None,
                        help="Status summary for --checkpoint.")
    parser.add_argument("--next-step", metavar="TEXT", default=None,
                        help="Next step for --checkpoint.")
    parser.add_argument("--update-plan-ledger", metavar="PLAN", nargs="?",
                        default=None, const="",
                        help="Write mode: rewrite the leading task checkboxes and/or the "
                             "first 'Status:' header of PLAN (path inside the project root). "
                             "Mark tasks done with --task <id>..., reset them with --open, "
                             "set the status via --status <s>. Combine with --dry-run for a "
                             "preview; exit 1 on missing arguments, a missing plan or an "
                             "unmatched task id.")
    parser.add_argument("--task", nargs="*", default=None, metavar="ID",
                        help="Task id(s) for --update-plan-ledger (normalized, "
                             "e.g. '1' or 'task-1'); for --checkpoint the first "
                             "id is normalized and recorded.")
    parser.add_argument("--open", action="store_true",
                        help="With --update-plan-ledger --task: reset the task checkboxes "
                             "to '- [ ]' instead of marking them done.")
    parser.add_argument("--status", metavar="STATUS", default=None,
                        help="With --update-plan-ledger: value for the first 'Status:' "
                             "header line of the plan. With --checkpoint: one of "
                             "completed|failed|timeout|in_progress.")
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

    # Secret scanning for auto-commits (issue #694)
    parser.add_argument("--scan-staged", action="store_true",
                        help="Scan git-staged file contents for secrets (issue #694 pre-commit gate) and exit.")

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


# ---------------------------------------------------------------------------
# --cleanup-preview (IC-06): planning-only, side-effect-free JSON preview
# ---------------------------------------------------------------------------

_PREVIEW_VERSION = 1
# Mirrors the OQ-2 default policy wired into the sync pipeline (IC-05).
_PREVIEW_PRUNE_MAX_AGE_DAYS = 30
_PREVIEW_PRUNE_MAX_PER_SOURCE = 3


class CleanupPreviewLog(SyncLog):
    """Collecting ``SyncLog`` variant for ``--cleanup-preview`` (IC-06).

    Records exactly like :class:`SyncLog` but never writes to stderr: the
    preview's stdout is a machine-consumed JSON contract, so diagnostic noise
    must not bleed into the process output. The retained lists keep the
    planning traversal inspectable in tests.
    """

    def warn(self, message: str) -> None:
        if message in self._seen_warnings:
            return
        self._seen_warnings.add(message)
        self.warnings.append(f"[WARN]   {message}")

    def error(self, target: str, message: str) -> None:
        self.errors.append(f"[ERROR]  {target:<50}  {message}")


def _preview_expected_filenames(
    config: dict,
    variables: dict,
    provider: str,
    pc: dict,
    role_map: dict,
    overrides: dict,
    target_dir: Path,
    project_root: Path,
    agent_meta_root: Path,
    log: SyncLog,
) -> set:
    """Filenames the provider's agent sync would (re)write this run.

    Mirrors the planning half of ``sync_agents_for_provider`` without composing
    or writing any content: the skip-gates decide membership, the IC-03
    collector adds the active external-skill wrappers (unconditional, no
    capability gate).
    """
    from lib.agent_sync import (
        _collect_active_skill_wrapper_filenames,
        _should_skip_role,
    )
    from lib.roles import resolve_activation_gates

    gates = resolve_activation_gates(agent_meta_root, config)
    allowed_roles = set(config["roles"]) if "roles" in config else None
    expected: set = set()
    for role, source_path in overrides.items():
        skip, filename = _should_skip_role(
            role, source_path, provider, pc, role_map, allowed_roles,
            config, variables, project_root, target_dir, log, gates=gates)
        if skip:
            continue
        expected.add(filename)
    expected |= _collect_active_skill_wrapper_filenames(agent_meta_root, config)
    return expected


def _preview_foreign_entries(
    target_dir: Path,
    pc: dict,
    expected: set,
    stale_names: set,
    project_root: Path,
) -> list:
    """Enumerate the candidate files that would survive (IC-06 ``foreign``).

    ``plan_agent_cleanup`` returns only the removable set, so the foreign set is
    derived here as the complement over the provider's candidate globs:
    candidates that are neither expected (managed) nor stale (removable).
    ``legacy_unmarked`` is the OQ-3 flag: True when the file carries no
    recognised primary agent-meta provenance marker (marker-less legacy file
    awaiting user-approved manual removal).
    """
    from lib.agent_sync import (
        _agent_has_provenance,
        _iter_agent_candidates,
        _read_text_or_none,
    )
    from lib.rule_index import _relative_posix

    foreign: list = []
    for candidate in _iter_agent_candidates(target_dir, pc):
        if candidate.name in expected or candidate.name in stale_names:
            continue
        text = _read_text_or_none(candidate)
        foreign.append({
            "path": _relative_posix(candidate, project_root),
            "legacy_unmarked": text is None or not _agent_has_provenance(candidate, text),
        })
    return foreign


def _preview_backups_to_prune(
    target_dir: Path,
    project_root: Path,
    max_age_days: int = _PREVIEW_PRUNE_MAX_AGE_DAYS,
    max_per_source: int = _PREVIEW_PRUNE_MAX_PER_SOURCE,
) -> list:
    """Pure would-be-prune list for ``target_dir`` (IC-06 ``backups_to_prune``).

    ``generated_file_drift.prune_sync_backups`` is a no-op in dry-run (IC-05),
    so the preview recomputes the very same dual-threshold candidate set without
    deleting anything: age strictly greater than *max_age_days* AND strictly
    more than *max_per_source* newer backups for the same source. The naming /
    timestamp helpers are imported from the pruner module so only the threshold
    decision is mirrored here.
    """
    from datetime import datetime

    from lib.generated_file_drift import (
        _is_sync_backup_name,
        _sync_backup_source,
        _sync_backup_timestamp,
    )
    from lib.rule_index import _relative_posix

    if not target_dir.is_dir():
        return []
    try:
        entries = sorted(target_dir.iterdir())
    except OSError:
        return []

    backups: list = []
    for path in entries:
        if not path.is_file() or not _is_sync_backup_name(path.name):
            continue
        stamp = _sync_backup_timestamp(path.name)
        if stamp is None:
            continue
        backups.append((path, _sync_backup_source(path.name), stamp))

    now = datetime.now()
    prunable: list = []
    for path, source, stamp in backups:
        if (now - stamp).days <= max_age_days:
            continue
        newer = sum(
            1 for _other, other_source, other_stamp in backups
            if other_source == source and other_stamp > stamp
        )
        if newer <= max_per_source:
            continue
        prunable.append(_relative_posix(path, project_root))
    return sorted(prunable)


def _cleanup_fingerprint(stale_entries: list) -> str:
    """Stable ``sha256:…`` hash over the canonicalized stale set (IC-06).

    Canonicalization sorts by ``(provider, path, reason, tracked, adopted)`` so
    the fingerprint is order-independent and changes whenever the apply handler
    would see a different stale set (TOCTOU detection, IC-07).
    """
    import hashlib
    import json

    canonical = sorted(
        (
            {
                "provider": entry.provider,
                "path": entry.path,
                "reason": entry.reason,
                "tracked": entry.tracked,
                "adopted": entry.adopted,
            }
            for entry in stale_entries
        ),
        key=lambda item: (
            item["provider"], item["path"], item["reason"],
            item["tracked"], item["adopted"],
        ),
    )
    blob = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def _handle_cleanup_preview(ctx: _SyncContext) -> None:
    """Handle ``--cleanup-preview`` (IC-06).

    Runs a planning-only traversal over every active provider, reusing the pure
    computation (``_resolve_sync_targets``, ``_should_skip_role``, IC-03
    collectors, ``plan_agent_cleanup``) and calling no writer stage. Emits
    exactly one JSON object on stdout; rc 0 even for a non-empty stale set, rc 1
    only on internal failure.
    """
    import json
    from datetime import datetime, timezone

    from lib.agent_sync import (
        _collect_all_registry_wrapper_filenames,
        _resolve_sync_targets,
        plan_agent_cleanup,
    )
    from lib.providers import load_providers_config, resolve_providers

    log = CleanupPreviewLog()
    agent_meta_root = ctx.agent_meta_root
    project_root = ctx.project_root
    config = ctx.config
    variables = ctx.variables

    try:
        provider_config = load_providers_config(agent_meta_root)
        providers = resolve_providers(config, provider_config)
        wrapper_filenames = _collect_all_registry_wrapper_filenames(agent_meta_root)

        provider_payload: list = []
        stale_entries: list = []
        for provider in providers:
            pc, role_map, overrides, target_dir = _resolve_sync_targets(
                provider, provider_config, agent_meta_root, project_root,
                config, True, log)
            if pc is None:
                continue
            expected = _preview_expected_filenames(
                config, variables, provider, pc, role_map, overrides,
                target_dir, project_root, agent_meta_root, log)
            stale = plan_agent_cleanup(
                target_dir, expected, provider, wrapper_filenames, pc, project_root)
            stale_entries.extend(stale)
            stale_names = {Path(entry.path).name for entry in stale}
            provider_payload.append({
                "provider": provider,
                "stale": [
                    {
                        "path": entry.path,
                        "reason": entry.reason,
                        "tracked": entry.tracked,
                        "adopted": entry.adopted,
                    }
                    for entry in stale
                ],
                "foreign": _preview_foreign_entries(
                    target_dir, pc, expected, stale_names, project_root),
                "backups_to_prune": _preview_backups_to_prune(target_dir, project_root),
            })

        payload = {
            "version": _PREVIEW_VERSION,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "providers": provider_payload,
            "fingerprint": _cleanup_fingerprint(stale_entries),
        }
    except Exception as exc:  # noqa: BLE001 — any internal failure → rc 1
        print(json.dumps(
            {"version": _PREVIEW_VERSION, "error": f"{type(exc).__name__}: {exc}"},
            ensure_ascii=False))
        sys.exit(1)

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    ctx.read_only = True
    ctx.mode = "cleanup-preview"


# Ordered (predicate, handler) table. Order mirrors the original if/elif
# chain exactly -- the first matching predicate wins, so flag precedence is
# preserved. The default (no predicate matches) is _handle_sync.
_MODE_HANDLERS = [
    (lambda a: a.fill_defaults, _handle_fill_defaults),
    (lambda a: a.audit_config, _handle_audit_config),
    (lambda a: a.only_variables, _handle_only_variables),
    (lambda a: a.cleanup_preview, _handle_cleanup_preview),
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
    (lambda a: a.validate_se, _handle_validate_se),
    (lambda a: a.validate_spec_plan, _handle_validate_spec_plan),
    (lambda a: a.rehydrate, _handle_rehydrate),
    (lambda a: a.checkpoint, _handle_checkpoint),
    (lambda a: a.update_plan_ledger is not None, handle_update_plan_ledger),
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
    # Start every run with a fresh gitignore probe cache (#752): a long-lived
    # process must not reuse an ignore decision from a previous run.
    clear_gitignore_cache()

    # Early-exit mode: scan staged files for secrets (issue #694)
    if args.scan_staged:
        sys.exit(handle_scan_staged())

    script_path = Path(__file__).resolve()
    agent_meta_root = find_agent_meta_root(script_path)
    log = SyncLog()

    if getattr(args, "cleanup_preview", False):
        # IC-06: the preview must emit exactly one JSON object on stdout and
        # write nothing. Context building is shared CLI plumbing that can print
        # (auto-detect banner) and, when self-hosting, touch the schema enum —
        # so run it with dry_run forced on and stdout redirected to stderr.
        saved_dry_run = args.dry_run
        args.dry_run = True
        with contextlib.redirect_stdout(sys.stderr):
            ctx = _build_context(args, agent_meta_root, log)
        args.dry_run = saved_dry_run
    else:
        ctx = _build_context(args, agent_meta_root, log)
    if ctx is None:
        return

    _dispatch(ctx)
    if not getattr(ctx, "read_only", False):
        _run_common_tail(ctx)


if __name__ == "__main__":
    main()
