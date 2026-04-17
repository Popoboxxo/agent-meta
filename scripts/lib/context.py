"""Context file management: CLAUDE.md managed block, provider context, gitignore, settings."""

import json
import re
from pathlib import Path

from .log import SyncLog

CLAUDE_SNIPPETS_DIR = ".claude/snippets"
SNIPPETS_DIR = "snippets"
GITIGNORE_BLOCK_BEGIN = "# --- agent-meta managed (do not edit) ---"
GITIGNORE_BLOCK_END   = "# --- end agent-meta managed ---"

# Path to the CLAUDE.md managed block template (relative to agent-meta root)
_CLAUDE_MD_MANAGED_TEMPLATE_PATH = "templates/claude-md-managed.md"


def _load_claude_md_managed_template(agent_meta_root: Path) -> str:
    """Load CLAUDE.md managed block template from templates/claude-md-managed.md."""
    template_path = agent_meta_root / _CLAUDE_MD_MANAGED_TEMPLATE_PATH
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    # Inline fallback if template file is missing
    return (
        "<!-- agent-meta:managed-begin -->\n"
        "<!-- This block is automatically updated by sync.py on every sync. -->\n"
        "<!-- Manual changes here will be overwritten. -->\n"
        "\n"
        "Generiert von agent-meta v{{AGENT_META_VERSION}} — `{{AGENT_META_DATE}}`\n"
        "DoD-Preset: **{{DOD_PRESET}}** | REQ-Traceability: {{DOD_REQ_TRACEABILITY}} | "
        "Tests: {{DOD_TESTS_REQUIRED}} | Codebase-Overview: {{DOD_CODEBASE_OVERVIEW}} | "
        "Security-Audit: {{DOD_SECURITY_AUDIT}}\n"
        "\n"
        "{{AGENT_HINTS}}\n"
        "<!-- agent-meta:managed-end -->"
    )


def sync_claude_md_managed(
    project_root: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    agent_meta_root: Path | None = None,
):
    """Update the managed block in CLAUDE.md if it exists and contains the marker."""
    from .config import substitute

    if agent_meta_root is None:
        agent_meta_root = Path(__file__).resolve().parent.parent.parent

    target_path = project_root / "CLAUDE.md"
    if not target_path.exists():
        return

    existing = target_path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"<!--\s*agent-meta:managed-begin\s*-->.*?<!--\s*agent-meta:managed-end\s*-->",
        re.DOTALL,
    )
    if not pattern.search(existing):
        log.warn(
            "CLAUDE.md exists but has no managed block — "
            "AGENT_TABLE will not be updated. "
            "Add the following block at the desired location in CLAUDE.md:\n"
            "  <!-- agent-meta:managed-begin -->\n"
            "  <!-- agent-meta:managed-end -->"
        )
        return

    template = _load_claude_md_managed_template(agent_meta_root)
    new_managed = substitute(template, variables, "CLAUDE.md managed block", log)
    new_content = pattern.sub(new_managed, existing, count=1)

    if new_content == existing:
        log.skip("CLAUDE.md", "managed block unchanged")
    else:
        log.action("UPDATE", "CLAUDE.md", "managed block (AGENT_TABLE + version)")
        if not dry_run:
            target_path.write_text(new_content, encoding="utf-8")


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
        target_path = project_root / context_file
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

        # 2. .continue/config.yaml — skeleton, created once (never overwritten)
        settings_file = pc["settings_file"]
        settings_path = project_root / settings_file
        if settings_path.exists():
            log.skip(str(settings_path.relative_to(project_root)),
                     "already exists - not overwritten")
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


def init_claude_personal(
    agent_meta_root: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
):
    """Copy CLAUDE.personal-template.md to CLAUDE.personal.md if not present yet."""
    template_path = agent_meta_root / "howto" / "CLAUDE.personal-template.md"
    target_path = project_root / "CLAUDE.personal.md"

    if target_path.exists():
        log.skip("CLAUDE.personal.md", "already exists")
        return

    if not template_path.exists():
        log.warn("CLAUDE.personal-template.md not found — skipping CLAUDE.personal.md creation")
        return

    content = template_path.read_text(encoding="utf-8")
    log.action("INIT", "CLAUDE.personal.md", "howto/CLAUDE.personal-template.md")
    if not dry_run:
        target_path.write_text(content, encoding="utf-8")


def init_settings_json(
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
):
    """Create .claude/settings.json if it does not exist yet.

    The file is created once as a skeleton for team-shared settings.
    The hooks section is managed separately by sync_hooks() on every sync.
    """
    target_path = project_root / ".claude" / "settings.json"
    if target_path.exists():
        log.skip(".claude/settings.json", "already exists")
        return

    content = '{\n  "permissions": {\n    "allow": [],\n    "deny": []\n  }\n}\n'
    log.action("INIT", ".claude/settings.json", "team permissions skeleton")
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")


def init_settings_local_json(
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Create .claude/settings.local.json skeleton if it does not exist yet.

    This file is gitignored and intended for personal / machine-local overrides
    (e.g. allow-listing commands during development, local hook overrides).
    Created once on --init or first Claude sync — never overwritten afterwards.
    """
    target_path = project_root / ".claude" / "settings.local.json"
    if target_path.exists():
        log.skip(".claude/settings.local.json", "already exists")
        return

    content = (
        '{\n'
        '  "permissions": {\n'
        '    "allow": [],\n'
        '    "deny": []\n'
        '  }\n'
        '}\n'
    )
    log.action("INIT", ".claude/settings.local.json", "personal/local settings skeleton (gitignored)")
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")


def ensure_gitignore_entries(
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
    gitignore_entries: list[str] | None = None,
):
    """Ensure required entries exist in a managed block in .gitignore.

    Writes a clearly marked block so users know the entries are managed by
    agent-meta and should not be removed manually.
    If the block already exists, it is updated in-place (entries added, never removed).
    Entries that already exist outside the block are not duplicated.

    gitignore_entries: list of entries to add. If None, reads from providers.config.yaml (Claude).
    """
    if gitignore_entries is None:
        # Default: Claude entries (backward compat)
        gitignore_entries = [
            ".claude/settings.local.json",
            ".claude/agent-memory-local/",
            "CLAUDE.personal.md",
            "sync.log",
        ]

    gitignore_path = project_root / ".gitignore"
    existing = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""

    # Extract current block content if present
    block_pattern = re.compile(
        re.escape(GITIGNORE_BLOCK_BEGIN) + r"(.*?)" + re.escape(GITIGNORE_BLOCK_END),
        re.DOTALL,
    )
    block_match = block_pattern.search(existing)
    block_entries: set[str] = set()
    if block_match:
        block_entries = {
            line.strip() for line in block_match.group(1).splitlines() if line.strip()
        }

    missing = [e for e in gitignore_entries if e not in block_entries]
    if not missing:
        log.skip(".gitignore", "all required entries already present")
        return

    new_block_entries = sorted(block_entries | set(missing))
    new_block = (
        GITIGNORE_BLOCK_BEGIN + "\n"
        + "\n".join(new_block_entries) + "\n"
        + GITIGNORE_BLOCK_END
    )

    if block_match:
        new_content = block_pattern.sub(new_block, existing)
    else:
        new_content = existing.rstrip("\n") + "\n\n" + new_block + "\n"

    log.action("UPDATE", ".gitignore", f"added to managed block: {', '.join(missing)}")
    if not dry_run:
        gitignore_path.write_text(new_content, encoding="utf-8")


def init_claude_md(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Create CLAUDE.md from template if it does not exist."""
    from .config import substitute

    template_path = agent_meta_root / "howto" / "CLAUDE.project-template.md"
    target_path = project_root / "CLAUDE.md"

    if target_path.exists():
        print("  i  CLAUDE.md already exists — skipped (use --only-variables)")
        log.skip("CLAUDE.md", "already exists")
        return

    if not template_path.exists():
        log.warn(f"CLAUDE.project-template.md not found at {template_path}")
        return

    content = template_path.read_text(encoding="utf-8")
    content = substitute(content, variables, "CLAUDE.project-template.md", log)
    log.action("INIT", "CLAUDE.md", "howto/CLAUDE.project-template.md")
    if not dry_run:
        target_path.write_text(content, encoding="utf-8")


def only_variables(
    project_root: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Substitute {{VARIABLE}} placeholders in existing CLAUDE.md."""
    import sys
    from .config import substitute

    target_path = project_root / "CLAUDE.md"
    if not target_path.exists():
        print("  !  CLAUDE.md not found — use --init to create it")
        sys.exit(1)

    content = target_path.read_text(encoding="utf-8")
    new_content = substitute(content, variables, "CLAUDE.md", log)

    if new_content == content:
        log.action("SKIP", "CLAUDE.md", "no open placeholders")
    else:
        log.action("WRITE", "CLAUDE.md", "variables from config")
        if not dry_run:
            target_path.write_text(new_content, encoding="utf-8")


def sync_prompts_for_continue(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Generate .continue/prompts/<role>.md as invokable slash-commands.

    Controlled by provider-options.Continue:
        generate-prompts: true          # enable (default: false)
        prompt-mode: "full" | "slim"    # full = complete agent body (default)
                                        # slim = compact role + core rules only

    Works with any local LLM — no tool calling required.
    Slash-commands: /developer, /git, /orchestrator, ...
    """
    from .agents import (collect_sources, extract_frontmatter_field, compose_agent,
                          target_filename, _strip_frontmatter, _strip_claude_specific_lines,
                          _make_slim_body, AGENTS_DIR)
    from .config import substitute
    from .providers import resolve_provider_options
    from .roles import build_role_map

    opts = resolve_provider_options(config, "Continue")
    if not opts.get("generate-prompts", False):
        return

    role_map = build_role_map(agent_meta_root)
    prompt_mode = opts.get("prompt-mode", "full")
    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    allowed_roles: set | None = set(config["roles"]) if "roles" in config else None

    prompts_dir = project_root / ".continue" / "prompts"
    if not dry_run:
        prompts_dir.mkdir(parents=True, exist_ok=True)

    expected: set[str] = set()

    for role, source_path in overrides.items():
        filename = target_filename(role, role_map)
        if not filename:
            continue
        if allowed_roles is not None and role not in allowed_roles:
            continue

        expected.add(filename)
        target_path = prompts_dir / filename
        content = source_path.read_text(encoding="utf-8")

        # Composition
        extends_base = extract_frontmatter_field(content, "extends")
        if extends_base:
            base_path = agent_meta_root / AGENTS_DIR / extends_base
            content = compose_agent(base_path, content, log)

        rel_source = str(source_path.relative_to(agent_meta_root))
        content = substitute(content, variables, rel_source, log)

        template_description = extract_frontmatter_field(content, "description") or f"Agent for {role}."
        template_description = template_description.replace("{{PROJECT_NAME}}", config["project"]["name"])

        # Strip original frontmatter, optionally slim the body
        body = _strip_frontmatter(content)
        body = _strip_claude_specific_lines(body)
        if prompt_mode == "slim":
            body = _make_slim_body(body)

        # Build Continue prompt frontmatter
        fm = (
            f"---\n"
            f"name: {role}\n"
            f'description: "{template_description}"\n'
            f"invokable: true\n"
            f"---\n"
        )
        final = fm + body

        layer = source_path.parts[-2]
        log.action("WRITE", str(target_path.relative_to(project_root)),
                   f"{layer}/{source_path.name} [prompt/{prompt_mode}]")
        if not dry_run:
            target_path.write_text(final, encoding="utf-8")

    # Stale cleanup
    managed_index = prompts_dir / ".agent-meta-managed"
    previously_managed: set[str] = set()
    if managed_index.exists():
        for line in managed_index.read_text(encoding="utf-8").splitlines():
            if line.strip():
                previously_managed.add(line.strip())

    if prompts_dir.exists():
        for existing_file in sorted(prompts_dir.glob("*.md")):
            if existing_file.name not in expected:
                if not managed_index.exists() or existing_file.name in previously_managed:
                    log.action("DELETE", str(existing_file.relative_to(project_root)),
                               "role removed from config")
                    if not dry_run:
                        existing_file.unlink()

    if not dry_run and expected:
        managed_index.write_text("\n".join(sorted(expected)) + "\n", encoding="utf-8")


def sync_snippets(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Copy snippet files from agent-meta/snippets/ to .claude/snippets/ in the project.

    Only copies snippets referenced via TESTER_SNIPPETS_PATH (or similar *_SNIPPETS_PATH
    variables) in the project config. Unknown snippet files are skipped.
    All referenced paths are resolved relative to agent-meta/snippets/.
    """
    from .agents import extract_frontmatter_field

    variables = config.get("variables", {})
    snippets_root = agent_meta_root / SNIPPETS_DIR
    target_root = project_root / CLAUDE_SNIPPETS_DIR

    if not snippets_root.exists():
        return

    # Collect all *_SNIPPETS_PATH values from config variables
    snippet_paths: list[str] = [
        v for k, v in variables.items()
        if k.endswith("_SNIPPETS_PATH") and v
    ]

    if not snippet_paths:
        return

    for rel_path in snippet_paths:
        source_path = snippets_root / rel_path
        if not source_path.exists():
            log.warn(f"Snippet not found: snippets/{rel_path}")
            continue

        target_path = target_root / rel_path
        source_content = source_path.read_text(encoding="utf-8")
        snippet_version = extract_frontmatter_field(source_content, "version")
        version_label = f"@{snippet_version}" if snippet_version else ""

        log.action(
            "COPY",
            str(target_path.relative_to(project_root)),
            f"snippets/{rel_path}{version_label}",
        )
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(source_content, encoding="utf-8")
