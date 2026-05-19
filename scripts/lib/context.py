"""Context file management: provider context dispatch and public API re-exports."""

import re
from pathlib import Path

from .io import safe_path
from .log import SyncLog

from .context_claude import (
    _load_claude_md_managed_template,
    sync_claude_md_managed,
    init_claude_md,
    only_variables,
)
from .context_continue import _update_continue_config_managed_block, sync_prompts_for_continue
from .context_gitignore import ensure_gitignore_entries
from .context_personal import (
    init_claude_personal,
    init_opencode_personal,
    init_settings_json,
    init_settings_local_json,
)
from .context_rules import _build_opencode_managed_block
from .context_snippets import sync_snippets_for_provider


def sync_context_for_provider(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: dict,
):
    """Create or update the context file for a given provider.

    Claude:   CLAUDE.md - managed block updated on every sync
    Gemini:   .gemini/GEMINI.md - created once from template; managed block updated
    Continue: .continue/config.yaml - skeleton, created once (never overwritten)
    """
    from .config import substitute
    from .extensions import render_managed_block, update_managed_block

    pc = provider_config.get(provider)
    if not pc:
        return

    if provider == "Claude":
        sync_claude_md_managed(project_root, variables, log, dry_run, agent_meta_root)

    elif provider == "Gemini":
        context_file = pc["context_file"]
        if context_file is None:
            return
        target_path = safe_path(project_root, context_file)
        template_name = pc["context_template"]
        template_path = agent_meta_root / template_name if template_name else None

        if not target_path.exists():
            if template_path and template_path.exists():
                gcontent = template_path.read_text(encoding="utf-8")
                gcontent = substitute(gcontent, variables, template_name, log)
                log.action("INIT", str(target_path.relative_to(project_root)), template_name)
            else:
                project_name = config["project"]["name"]
                gcontent = (
                    f"# {project_name}\n\n"
                    "<!-- agent-meta:managed-begin -->\n"
                    "<!-- agent-meta:managed-end -->\n\n"
                    "## Agents\n\n"
                    f"Agent files are in .gemini/agents/ (use @agent-name).\n"
                )
                log.action("INIT", str(target_path.relative_to(project_root)),
                           "minimal fallback (GEMINI.project-template.md not found)")
            if not dry_run:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(gcontent, encoding="utf-8")
        else:
            existing = target_path.read_text(encoding="utf-8")
            managed_pattern = re.compile(
                r"<!--\s*agent-meta:managed-begin\s*-->"
                r".*?<!--\s*agent-meta:managed-end\s*-->",
                re.DOTALL,
            )
            if managed_pattern.search(existing):
                template = _load_claude_md_managed_template(agent_meta_root)
                new_managed = substitute(template, variables,
                                         str(target_path.relative_to(project_root)), log)
                new_content = managed_pattern.sub(new_managed, existing, count=1)
                if new_content != existing:
                    log.action("UPDATE", str(target_path.relative_to(project_root)),
                               "managed block")
                    if not dry_run:
                        target_path.write_text(new_content, encoding="utf-8")
                else:
                    log.skip(str(target_path.relative_to(project_root)), "managed block unchanged")

    elif provider == "Opencode":
        context_file = pc["context_file"]  # "AGENTS.md"
        target_path = safe_path(project_root, context_file)
        template_name = pc.get("context_template")
        template_path = agent_meta_root / template_name if template_name else None

        # Create AGENTS.md skeleton if it doesn't exist yet
        if not target_path.exists():
            if template_path and template_path.exists():
                ocontent = template_path.read_text(encoding="utf-8")
                ocontent = substitute(ocontent, variables, template_name, log)
            else:
                project_name = config["project"]["name"]
                ocontent = (
                    f"# {project_name}\n\n"
                    "<!-- agent-meta:managed-begin -->\n"
                    "<!-- agent-meta:managed-end -->\n"
                )
            log.action("INIT", context_file, template_name or "minimal fallback")
            if not dry_run:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(ocontent, encoding="utf-8")

        # Always update the managed block (agent hints + embedded rules)
        managed_pattern = re.compile(
            r"<!--\s*agent-meta:managed-begin\s*-->.*?<!--\s*agent-meta:managed-end\s*-->",
            re.DOTALL,
        )
        if dry_run and not target_path.exists():
            log.action("UPDATE", context_file, "managed block (agent hints + rules)")
        else:
            existing = target_path.read_text(encoding="utf-8")
            if managed_pattern.search(existing):
                new_managed = _build_opencode_managed_block(
                    agent_meta_root, config, variables, log,
                    provider=provider, provider_config=provider_config
                )
                new_content = managed_pattern.sub(new_managed, existing, count=1)
                if new_content != existing:
                    log.action("UPDATE", context_file, "managed block (agent hints + rules)")
                    if not dry_run:
                        target_path.write_text(new_content, encoding="utf-8")
                else:
                    log.skip(context_file, "managed block unchanged")

        # AGENTS.personal.md — personal local file, gitignored, created once
        init_opencode_personal(agent_meta_root, project_root, log, dry_run)

        # opencode.json — skeleton created once, never overwritten
        settings_file = pc.get("settings_file")
        if settings_file:
            settings_path = project_root / settings_file
            if settings_path.exists():
                log.skip(str(settings_path.relative_to(project_root)),
                         "already exists — not overwritten")
            else:
                settings_template_rel = pc.get("settings_template")
                settings_template_path = (
                    agent_meta_root / settings_template_rel if settings_template_rel else None
                )
                if settings_template_path and settings_template_path.exists():
                    json_content = settings_template_path.read_text(encoding="utf-8")
                    source_label = settings_template_rel
                else:
                    json_content = (
                        '{\n'
                        '  // opencode configuration — https://opencode.ai/docs/config\n'
                        '  // Agents  : .opencode/agents/  (managed by agent-meta)\n'
                        '  // Commands: .opencode/commands/ (managed by agent-meta)\n'
                        '  // Rules   : embedded in AGENTS.md (managed by agent-meta)\n'
                        '}\n'
                    )
                    source_label = "minimal fallback"
                    if settings_template_rel:
                        log.warn(
                            f"{settings_template_rel} not found "
                            f"— using minimal fallback for {settings_file}"
                        )
                log.action("INIT", str(settings_path.relative_to(project_root)), source_label)
                if not dry_run:
                    settings_path.parent.mkdir(parents=True, exist_ok=True)
                    settings_path.write_text(json_content, encoding="utf-8")

    elif provider == "Continue":
        # 1. .continue/rules/project-context.md — created once from template; managed block updated
        context_file = pc["context_file"]
        if context_file:
            ctx_path = project_root / context_file
            template_path = agent_meta_root / pc["context_template"]
            if not ctx_path.exists():
                if template_path.exists():
                    ccontent = substitute(
                        template_path.read_text(encoding="utf-8"),
                        variables, pc["context_template"], log,
                    )
                else:
                    ccontent = (
                        f"# {variables.get('PROJECT_NAME', 'Project Context')}\n\n"
                        f"{variables.get('PROJECT_CONTEXT', '')}\n\n"
                        "<!-- agent-meta:managed-begin -->\n"
                        "<!-- agent-meta:managed-end -->\n\n"
                        "## Agent Rules\n\n"
                        "Agent context files are in `.continue/rules/`.\n"
                        "Continue loads all Markdown files in this directory automatically as context.\n"
                    )
                    log.action("INIT", str(ctx_path.relative_to(project_root)),
                               "minimal fallback (CONTINUE.project-template.md not found)")
                log.action("INIT", str(ctx_path.relative_to(project_root)),
                           pc["context_template"])
                if not dry_run:
                    ctx_path.parent.mkdir(parents=True, exist_ok=True)
                    ctx_path.write_text(ccontent, encoding="utf-8")
            else:
                # Update managed block on every sync
                existing = ctx_path.read_text(encoding="utf-8")
                new_managed = render_managed_block(variables, context_file, log, agent_meta_root)
                updated = update_managed_block(existing, new_managed)
                if updated != existing:
                    log.action("UPDATE", str(ctx_path.relative_to(project_root)),
                               "managed block refreshed")
                    if not dry_run:
                        ctx_path.write_text(updated, encoding="utf-8")
                else:
                    log.skip(str(ctx_path.relative_to(project_root)), "managed block unchanged")

        # 2. .continue/config.yaml — skeleton created once; managed comment block updated
        settings_file = pc["settings_file"]
        settings_path = project_root / settings_file
        if settings_path.exists():
            _update_continue_config_managed_block(
                settings_path, variables, log, dry_run, project_root
            )
        else:
            settings_template_rel = pc.get("settings_template")
            if settings_template_rel:
                settings_template_path = agent_meta_root / settings_template_rel
            else:
                settings_template_path = None

            if settings_template_path and settings_template_path.exists():
                yaml_content = settings_template_path.read_text(encoding="utf-8")
                source_label = settings_template_rel
            else:
                yaml_content = (
                    "# Continue configuration\n"
                    "# See https://docs.continue.dev for full documentation\n"
                    "\n"
                    "# Agents are in .continue/agents/ - managed by agent-meta\n"
                    "# Project rules are in .continue/rules/ - managed by agent-meta\n"
                )
                source_label = "minimal fallback"
                if settings_template_rel:
                    log.warn(f"{settings_template_rel} not found — using minimal fallback for {settings_file}")
            log.action("INIT", str(settings_path.relative_to(project_root)),
                       source_label)
            if not dry_run:
                settings_path.parent.mkdir(parents=True, exist_ok=True)
                settings_path.write_text(yaml_content, encoding="utf-8")
