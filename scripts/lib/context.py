"""Context file management: CLAUDE.md managed block, provider context, gitignore, settings."""

import json
import re
from pathlib import Path

from .io import safe_path, content_hash
from .log import SyncLog

SNIPPETS_DIR = "snippets"

# Sidecar store recording the hash of each generated static header, so a later
# sync can tell its own staleness apart from manual user edits.
_CONTEXT_HASHES_FILE = "context-hashes.json"
_CONTEXT_HASHES_DIR = ".meta-config"

# Marker that separates the static header from the managed block in context files.
_MANAGED_BLOCK_RE = re.compile(
    r"<!--\s*agent-meta:managed-begin\s*-->.*?<!--\s*agent-meta:managed-end\s*-->",
    re.DOTALL,
)


def _context_hashes_path(project_root: Path) -> Path:
    return project_root / _CONTEXT_HASHES_DIR / _CONTEXT_HASHES_FILE


def _load_context_hashes(project_root: Path) -> dict:
    """Read .meta-config/context-hashes.json; return {} if absent or invalid."""
    path = _context_hashes_path(project_root)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError, OSError):
        return {}
    hashes = data.get("hashes") if isinstance(data, dict) else None
    return hashes if isinstance(hashes, dict) else {}


def _save_context_hashes(project_root: Path, hashes: dict, dry_run: bool) -> None:
    """Write the sidecar hash store (no-op in dry_run)."""
    if dry_run:
        return
    path = _context_hashes_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "hashes": hashes}
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _record_static_hash(
    project_root: Path, rel_label: str, header_text: str, dry_run: bool
) -> None:
    """Store hash(header_text) for rel_label in the sidecar store."""
    hashes = _load_context_hashes(project_root)
    hashes[rel_label] = content_hash(header_text)
    _save_context_hashes(project_root, hashes, dry_run)


def _split_context_file(text: str) -> tuple[str, str | None, str]:
    """Split a context file into (header, managed_block, footer).

    - header: everything above the managed-begin marker.
    - managed_block: the full begin..end block (None if the file has none).
    - footer: everything after the managed-end marker.

    Concatenating header + managed_block + footer reproduces the original text
    exactly, so it is safe to regenerate only the header and keep the rest.
    """
    match = _MANAGED_BLOCK_RE.search(text)
    if not match:
        return text, None, ""
    return text[:match.start()], match.group(0), text[match.end():]


def _split_injected_footer_tail(footer: str) -> tuple[str, str]:
    """Split a footer into (template_part, injected_tail).

    The injected tail is any trailing block appended below the template footer by
    a separate step or external tool — e.g. agent-meta's own bootstrap block
    (``<!-- agent-meta:bootstrap-begin -->``) or a third-party wrapper block. All
    of these are delimited by HTML comments, and the context template footers are
    plain markdown with no HTML comments below the managed block, so the first
    ``<!--`` in the footer reliably marks the boundary. Returning the tail
    separately lets us regenerate the template part of the footer while preserving
    every injected trailing block byte-for-byte, exactly like the managed block.
    """
    idx = footer.find("<!--")
    if idx == -1:
        return footer, ""
    return footer[:idx], footer[idx:]


def _backup_context_file(
    target_path: Path, existing_content: str, rel_label: str, log: SyncLog, dry_run: bool
) -> None:
    """Write a timestamped backup before overwriting a user-modified static part."""
    from datetime import datetime

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = target_path.with_name(f"{target_path.name}.sync-backup-{ts}")
    log.warn(
        f"{rel_label}: static part differs from the last generated version "
        f"(manual edit or first-time migration). Backup written to {backup.name} — "
        f"review and merge any wanted changes."
    )
    print(f"  !  {rel_label}: static part changed -> backup {backup.name}")
    if not dry_run:
        backup.write_text(existing_content, encoding="utf-8")


def _regenerate_static_context(
    project_root: Path,
    target_path: Path,
    template_path: Path | None,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    rel_label: str,
    source_label: str,
    rebuild_footer: bool = False,
) -> None:
    """Regenerate the static part of an existing managed context file.

    Distinguishes agent-meta's own staleness (hash matches the last generated
    static part → silent overwrite) from manual user edits (hash mismatch or no
    record → timestamped backup, then overwrite; drift is worse than a
    recoverable overwrite). The managed block is always preserved verbatim.

    The footer (everything below the managed block) is preserved verbatim by
    default (CLAUDE.md behaviour). When ``rebuild_footer`` is set — the AGENTS.md
    family, whose footer holds the dynamic ``## Agents`` provider list — the
    footer template part is regenerated from the template too, while any
    agent-injected trailing block (e.g. the bootstrap block) is preserved
    verbatim, exactly like the managed block. The static signature used for
    drift detection then covers header + template footer instead of header only.
    """
    from .config import substitute

    if not target_path.exists():
        return
    if not template_path or not template_path.exists():
        log.info(rel_label, "no static template — skipping static regeneration")
        return

    rendered = substitute(
        template_path.read_text(encoding="utf-8"), variables, source_label, log
    )
    new_header, _tmpl_managed, new_footer = _split_context_file(rendered)

    existing = target_path.read_text(encoding="utf-8")
    existing_header, existing_managed, existing_footer = _split_context_file(existing)
    if existing_managed is None:
        # File has no managed block — not structured for a static/managed split.
        # Leave it untouched to avoid corrupting user content.
        log.info(rel_label, "no managed block — skipping static regeneration")
        return

    if rebuild_footer:
        existing_footer_tmpl, injected_tail = _split_injected_footer_tail(existing_footer)
        if injected_tail:
            # Re-attach the agent-injected tail below the fresh template footer,
            # reproducing the exact spacing the agents step uses when appending.
            target_footer = new_footer.rstrip("\n") + "\n\n" + injected_tail
        else:
            target_footer = new_footer
        # Signature covers header + template footer (ignoring the injected tail,
        # which is owned by the agents step and changes independently).
        new_sig = new_header + "\x00" + new_footer.rstrip("\n")
        existing_sig = existing_header + "\x00" + existing_footer_tmpl.rstrip("\n")
    else:
        target_footer = existing_footer
        new_sig = new_header
        existing_sig = existing_header

    if existing_sig == new_sig:
        log.skip(rel_label, "static part unchanged")
        _record_static_hash(project_root, rel_label, new_sig, dry_run)
        return

    stored = _load_context_hashes(project_root).get(rel_label)
    user_modified = stored is None or content_hash(existing_sig) != stored
    if user_modified:
        _backup_context_file(target_path, existing, rel_label, log, dry_run)

    new_content = new_header + existing_managed + target_footer
    log.action("UPDATE", rel_label, "static part regenerated from template")
    if not dry_run:
        target_path.write_text(new_content, encoding="utf-8")
    _record_static_hash(project_root, rel_label, new_sig, dry_run)
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
        "{{PROVIDER_ROUTING}}\n"
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
    # CLAUDE.md is Claude-specific: drop the per-agent table (native injection).
    render_vars = variables
    if "AGENT_HINTS_CLAUDE" in variables:
        render_vars = {**variables, "AGENT_HINTS": variables["AGENT_HINTS_CLAUDE"]}
    new_managed = substitute(template, render_vars, "CLAUDE.md managed block", log)
    new_content = pattern.sub(new_managed, existing, count=1)

    if new_content == existing:
        log.skip("CLAUDE.md", "managed block unchanged")
    else:
        log.action("UPDATE", "CLAUDE.md", "managed block (AGENT_TABLE + version)")
        if not dry_run:
            target_path.write_text(new_content, encoding="utf-8")


def _has_capability(pc: dict, capability: str) -> bool:
    """Return True if provider config lists the given capability."""
    return capability in pc.get("capabilities", [])


def _ensure_context_file(
    project_root: Path,
    agent_meta_root: Path,
    target_path: Path,
    template_path: Path | None,
    variables: dict,
    config: dict,
    log: SyncLog,
    dry_run: bool,
    fallback_agent_dir: str,
) -> None:
    """Create a provider context file from template or minimal fallback."""
    from .config import substitute

    if target_path.exists():
        return

    if template_path and template_path.exists():
        content = template_path.read_text(encoding="utf-8")
        source_label = str(template_path.relative_to(agent_meta_root))
        content = substitute(content, variables, source_label, log)
    else:
        project_name = config["project"]["name"]
        content = (
            f"# {project_name}\n\n"
            "<!-- agent-meta:managed-begin -->\n"
            "<!-- agent-meta:managed-end -->\n\n"
            f"## Agents\n\n"
            f"Agent files are in {fallback_agent_dir} (invoke by name).\n"
        )
        source_label = f"minimal fallback ({template_path.name if template_path else 'no template'})"
    log.action("INIT", str(target_path.relative_to(project_root)), source_label)
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")


def _update_managed_html_block(
    target_path: Path,
    project_root: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    agent_meta_root: Path,
    provider: str = "Claude",
) -> None:
    """Update the HTML-style managed block in a context file.

    For Claude, the per-agent table is dropped from the managed block:
    Claude Code injects agent descriptions natively, so the table would be a
    duplication. Other providers keep the full table via {{AGENT_HINTS}}.
    """
    from .config import substitute

    existing = target_path.read_text(encoding="utf-8")
    managed_pattern = re.compile(
        r"<!--\s*agent-meta:managed-begin\s*-->"
        r".*?<!--\s*agent-meta:managed-end\s*-->",
        re.DOTALL,
    )
    if not managed_pattern.search(existing):
        return
    template = _load_claude_md_managed_template(agent_meta_root)
    rel = str(target_path.relative_to(project_root))
    render_vars = variables
    if provider == "Claude" and "AGENT_HINTS_CLAUDE" in variables:
        render_vars = {**variables, "AGENT_HINTS": variables["AGENT_HINTS_CLAUDE"]}
    new_managed = substitute(template, render_vars, rel, log)
    new_content = managed_pattern.sub(new_managed, existing, count=1)
    if new_content != existing:
        log.action("UPDATE", rel, "managed block")
        if not dry_run:
            target_path.write_text(new_content, encoding="utf-8")
    else:
        log.skip(rel, "managed block unchanged")


def _sync_managed_block_context(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: dict,
) -> None:
    """Strategy for providers with a context file using HTML managed blocks."""
    from .config import substitute

    pc = provider_config[provider]
    context_file = pc.get("context_file")
    if not context_file:
        return
    target_path = safe_path(project_root, context_file)
    template_name = pc.get("context_template")
    template_path = agent_meta_root / template_name if template_name else None

    # Claude's CLAUDE.md static part is handled by sync_claude_md_static() in the
    # main sync loop; this strategy only refreshes the managed block for Claude.
    # For every other managed-block provider we also regenerate the static header
    # here (same hash-drift detection), when a static template is configured.
    if provider != "Claude":
        _ensure_context_file(
            project_root, agent_meta_root, target_path, template_path, variables, config,
            log, dry_run,
            fallback_agent_dir=pc.get("agents_dir", f".{provider.lower()}/agents"),
        )
        if target_path.exists():
            _regenerate_static_context(
                project_root, target_path, template_path, variables, log, dry_run,
                rel_label=context_file, source_label=template_name or context_file,
                rebuild_footer=True,
            )
    if target_path.exists():
        _update_managed_html_block(target_path, project_root, variables, log, dry_run, agent_meta_root, provider)

    # Claude settings files are initialized by the dedicated helpers in sync.py.
    if provider != "Claude":
        _init_provider_settings_json(project_root, pc, agent_meta_root, variables, log, dry_run)


def _sync_opencode_context(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: dict,
) -> None:
    """Strategy for Opencode: rules embedded into AGENTS.md managed block."""
    from .config import substitute

    pc = provider_config[provider]
    context_file = pc["context_file"]  # AGENTS.md
    target_path = safe_path(project_root, context_file)
    template_name = pc.get("context_template")
    template_path = agent_meta_root / template_name if template_name else None

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

    # Refresh the static header AND footer from the template on every sync so the
    # dynamic `## Agents` provider list never freezes at INIT (same header+footer
    # regeneration the managed-block providers get). The managed block and any
    # agent-injected trailing block are preserved verbatim.
    if target_path.exists():
        _regenerate_static_context(
            project_root, target_path, template_path, variables, log, dry_run,
            rel_label=context_file, source_label=template_name or context_file,
            rebuild_footer=True,
        )

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

    init_opencode_personal(agent_meta_root, project_root, log, dry_run)
    _init_provider_settings_json(project_root, pc, agent_meta_root, variables, log, dry_run)


def _sync_continue_context(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: dict,
) -> None:
    """Strategy for Continue: project-context.md + config.yaml comment block."""
    from .config import substitute
    from .extensions import render_managed_block, update_managed_block

    pc = provider_config[provider]
    context_file = pc.get("context_file")
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

    settings_file = pc.get("settings_file")
    if settings_file:
        settings_path = project_root / settings_file
        if settings_path.exists():
            _update_continue_config_managed_block(
                settings_path, variables, log, dry_run, project_root
            )
        else:
            settings_template_rel = pc.get("settings_template")
            settings_template_path = (
                agent_meta_root / settings_template_rel if settings_template_rel else None
            )
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
            log.action("INIT", str(settings_path.relative_to(project_root)), source_label)
            if not dry_run:
                settings_path.parent.mkdir(parents=True, exist_ok=True)
                settings_path.write_text(yaml_content, encoding="utf-8")


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

    Dispatch is capability-driven:
      - context-embedded-rules → Opencode strategy
      - provider == Continue   → Continue strategy (managed block + config.yaml comment)
      - context-managed-block  → generic HTML managed-block strategy
    """
    pc = provider_config.get(provider)
    if not pc:
        return

    if _has_capability(pc, "context-embedded-rules"):
        _sync_opencode_context(
            agent_meta_root, project_root, config, variables, log, dry_run,
            provider, provider_config,
        )
    elif provider == "Continue":
        _sync_continue_context(
            agent_meta_root, project_root, config, variables, log, dry_run,
            provider, provider_config,
        )
    elif _has_capability(pc, "context-managed-block"):
        _sync_managed_block_context(
            agent_meta_root, project_root, config, variables, log, dry_run,
            provider, provider_config,
        )


def _init_provider_settings_json(
    project_root: Path,
    pc: dict,
    agent_meta_root: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Create provider settings skeleton once if it does not exist yet."""
    from .config import substitute

    settings_file = pc.get("settings_file")
    if not settings_file:
        return
    settings_path = safe_path(project_root, settings_file)
    if settings_path.exists():
        log.skip(str(settings_path.relative_to(project_root)),
                 "already exists — not overwritten")
        return

    settings_template_rel = pc.get("settings_template")
    settings_template_path = (
        agent_meta_root / settings_template_rel if settings_template_rel else None
    )
    if settings_template_path and settings_template_path.exists():
        content = substitute(
            settings_template_path.read_text(encoding="utf-8"),
            variables, settings_template_rel, log,
        )
        source_label = settings_template_rel
    else:
        # Minimal provider-agnostic JSON skeleton
        content = '{\n  "//": "Provider settings managed by agent-meta"\n}\n'
        source_label = "minimal fallback"
        if settings_template_rel:
            log.warn(f"{settings_template_rel} not found — using minimal fallback for {settings_file}")
    log.action("INIT", str(settings_path.relative_to(project_root)), source_label)
    if not dry_run:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(content, encoding="utf-8")


_CONTINUE_MANAGED_BEGIN = "# agent-meta:managed-begin"
_CONTINUE_MANAGED_END   = "# agent-meta:managed-end"


def _update_continue_config_managed_block(
    settings_path: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    project_root: Path,
) -> None:
    """Insert or update the agent-meta metadata comment block in config.yaml.

    The block is YAML comments so it never affects parsing. User model config
    and any other customisations are left completely untouched.
    """
    from datetime import date
    version = variables.get("AGENT_META_VERSION", "?")
    today = date.today().isoformat()
    new_block = (
        f"{_CONTINUE_MANAGED_BEGIN}\n"
        f"# Managed by agent-meta v{version} — {today}\n"
        f"# Agents : .continue/agents/  (auto-discovered by Continue)\n"
        f"# Rules  : .continue/rules/   (auto-discovered by Continue)\n"
        f"{_CONTINUE_MANAGED_END}"
    )

    existing = settings_path.read_text(encoding="utf-8")
    rel = str(settings_path.relative_to(project_root))

    managed_re = re.compile(
        rf"^{re.escape(_CONTINUE_MANAGED_BEGIN)}.*?^{re.escape(_CONTINUE_MANAGED_END)}",
        re.MULTILINE | re.DOTALL,
    )
    if managed_re.search(existing):
        updated = managed_re.sub(new_block, existing, count=1)
        if updated != existing:
            log.action("UPDATE", rel, "managed comment block")
            if not dry_run:
                settings_path.write_text(updated, encoding="utf-8")
        else:
            log.skip(rel, "managed comment block unchanged")
    else:
        # Prepend block before first non-comment line
        updated = new_block + "\n" + existing
        log.action("UPDATE", rel, "inject managed comment block")
        if not dry_run:
            settings_path.write_text(updated, encoding="utf-8")


def _strip_rule_frontmatter(content: str) -> str:
    """Remove YAML frontmatter block from a rule file."""
    if not content.startswith('---'):
        return content
    end = content.find('\n---', 3)
    if end == -1:
        return content
    return content[end + 4:].lstrip('\n')


def _extract_rule_compact_from_content(content: str, output_name: str, rel_source: str,
                                        provider: str = "Claude", has_native_rules: bool = True) -> str:
    """Extract title + 1-sentence summary from already-substituted rule content.

    Reduces a 50-100 line rule to a single 3-line block:
      - Title
      - First non-empty paragraph (≤200 chars)
      - Pointer to full rule (provider-aware)
    """
    body = _strip_rule_frontmatter(content).strip()
    if not body:
        return f"- **{output_name}** — siehe `{rel_source}`"

    lines = body.splitlines()
    title = output_name.replace('-', ' ').replace('.md', '').title()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# '):
            title = stripped[2:].strip()
            break

    summary = ""
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or stripped.startswith('```'):
            continue
        summary = stripped
        if len(summary) > 200:
            summary = summary[:197] + "..."
        break

    rule_stem = Path(output_name).stem
    if has_native_rules:
        details = f"Details: `rules/.../{rule_stem}.md`"
    else:
        details = f"Details: embedded in `{provider}` context (Regeln-Abschnitt)"
    return f"### {title}\n{summary}\n{details}"


def _collect_embedded_rules_md(
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    provider: str = "Claude",
    provider_config: dict | None = None,
    compact: bool = False,
) -> str:
    """Collect all active rules and return them as concatenated markdown.

    Used to embed rules into AGENTS.md for providers without a native rules directory
    (e.g. opencode). Respects `opencode: skip` rule option and speech-mode config.

    When compact=True (default for Opencode), each rule is reduced to a 3-line
    summary block (title + 1-sentence summary + path) — full content stays in
    rules/<layer>/*.md. This shrinks AGENTS.md managed-block from ~660 to ~80 lines.
    """
    from .config import substitute, strip_inactive_conditional_blocks
    from .rules import collect_rule_sources, resolve_rules, SPEECH_DIR

    pc = (provider_config or {}).get(provider, {})
    provider_vars = {
        'EXTENSION_DIR': pc.get('extension_dir', '.claude/3-project'),
        'SNIPPETS_DIR': pc.get('snippets_dir', '.claude/snippets'),
        'PENDING_TASKS_FILE': pc.get('pending_tasks_file', '.claude/pending-tasks.md'),
        'SKILLS_DIR': pc.get('skills_dir', '.claude/skills'),
        'ORCHESTRATOR_INVOCATION_HINT': pc.get('orchestrator_hint', '- Bitte wählt den Orchestrator-Agenten aus.'),
        'AGENTS_DIR': pc.get('agents_dir', '.claude/agents'),
    }
    merged_vars = {**variables, **provider_vars}

    platforms = config.get('platforms', [])
    sources = collect_rule_sources(agent_meta_root, platforms)
    rule_options = resolve_rules(config, agent_meta_root)

    sections: list[str] = []

    embedded_count = 0
    skipped_count = 0

    provider_has_native_rules = pc.get('has_rules', False)
    for source_path, output_name in sources:
        rule_stem = Path(output_name).stem
        opts = rule_options.get(rule_stem, {})
        if opts.get('opencode') == 'skip':
            continue
        # Selective Rule Embedding:
        # embed: false → Rule wird nicht in den Managed Block eingebettet
        # (nur als separate Datei verfügbar, z.B. .claude/rules/)
        # Fallback B: Provider ohne native rules dir (has_rules: false) müssen
        # die Rule trotzdem embedden, sonst geht sie verloren.
        if opts.get('embed') == False and provider_has_native_rules:
            skipped_count += 1
            continue
        rel_source = f'rules/{source_path.parts[-2]}/{source_path.name}'
        content = source_path.read_text(encoding='utf-8')
        content = substitute(content, merged_vars, rel_source, log)
        content = strip_inactive_conditional_blocks(content, merged_vars)
        if compact:
            body = _extract_rule_compact_from_content(
                content, output_name, rel_source,
                provider=provider, has_native_rules=provider_has_native_rules,
            )
        else:
            body = _strip_rule_frontmatter(content).strip()
        if body:
            sections.append(body)
            embedded_count += 1

    if skipped_count > 0:
        log.info(f"Selective Embedding: {skipped_count} rules with embed:false skipped, {embedded_count} rules embedded", "embed filter")

    # Include speech-mode rule if configured (not handled by collect_rule_sources)
    mode = config.get('speech-mode', 'full')
    if mode != 'full':
        speech_path = agent_meta_root / SPEECH_DIR / f'{mode}.md'
        if speech_path.exists():
            speech_content = speech_path.read_text(encoding='utf-8')
            speech_content = substitute(speech_content, merged_vars, f"speech/{mode}.md", log)
            speech_content = strip_inactive_conditional_blocks(speech_content, merged_vars)
            if compact:
                body = _extract_rule_compact_from_content(
                    speech_content, f"{mode}.md", f"speech/{mode}.md",
                    provider=provider, has_native_rules=provider_has_native_rules,
                )
            else:
                body = _strip_rule_frontmatter(speech_content).strip()
            if body:
                sections.append(body)

    return '\n\n---\n\n'.join(sections)


def _build_opencode_managed_block(
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    provider: str = "Claude",
    provider_config: dict | None = None,
) -> str:
    """Build the managed block for AGENTS.md: agent hints + all embedded rules."""
    from .config import substitute

    provider_dirs = {
        "Claude": ".claude/agents",
        "Opencode": ".opencode/agents",
        "Gemini": ".gemini/agents",
        "Continue": ".continue/agents",
        "Copilot": ".github/copilot/agents",
        "Mammouth": ".mammouth/agents",
    }
    local_vars = dict(variables)
    if provider in provider_dirs:
        local_vars["AGENTS_DIR"] = provider_dirs[provider]

    template = _load_claude_md_managed_template(agent_meta_root)
    managed = substitute(template, local_vars, 'AGENTS.md managed block', log)

    # Phase 2: Opencode loads rules natively via the provider rules mechanism.
    # The managed block only keeps a compact pointer; full rules live in
    # rules/<layer>/*.md and are surfaced to the runtime via .opencode/rules/.
    managed = managed.replace(
        '<!-- agent-meta:managed-end -->',
        '\n## Regeln\n\n> **Regeln:** Alle Regeln werden nativ über den Provider-Rules-Mechanismus geladen. Siehe `.opencode/rules/`.\n\n<!-- agent-meta:managed-end -->',
    )

    return managed


def init_claude_personal(
    agent_meta_root: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
):
    """Copy CLAUDE.personal-template.md to CLAUDE.personal.md if not present yet."""
    template_path = agent_meta_root / "howto" / "configs" / "CLAUDE.personal-template.md"
    target_path = project_root / "CLAUDE.personal.md"

    if target_path.exists():
        log.skip("CLAUDE.personal.md", "already exists")
        return

    if not template_path.exists():
        log.warn("CLAUDE.personal-template.md not found — skipping CLAUDE.personal.md creation")
        return

    content = template_path.read_text(encoding="utf-8")
    log.action("INIT", "CLAUDE.personal.md", "templates/configs/CLAUDE.personal-template.md")
    if not dry_run:
        target_path.write_text(content, encoding="utf-8")


def init_opencode_personal(
    agent_meta_root: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
):
    """Copy AGENTS.personal-template.md to AGENTS.personal.md if not present yet.

    Analogous to CLAUDE.personal.md — gitignored, never committed, loaded via
    the `instructions` field in opencode.json.
    """
    template_path = agent_meta_root / "howto" / "configs" / "AGENTS.personal-template.md"
    target_path = project_root / "AGENTS.personal.md"

    if target_path.exists():
        log.skip("AGENTS.personal.md", "already exists")
        return

    if not template_path.exists():
        log.warn("AGENTS.personal-template.md not found — skipping AGENTS.personal.md creation")
        return

    content = template_path.read_text(encoding="utf-8")
    log.action("INIT", "AGENTS.personal.md", "templates/configs/AGENTS.personal-template.md")
    if not dry_run:
        target_path.write_text(content, encoding="utf-8")


def init_settings_json(
    agent_meta_root: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
    providers: list[str] | None = None,
    provider_config: dict | None = None,
    variables: dict | None = None,
):
    """Create provider settings files if they do not exist yet.

    Iterates over all active providers (or every configured provider if no
    explicit list is given) and initializes the committed settings file once.
    The hooks section for Claude is managed separately by sync_hooks().
    """
    pc = provider_config or {}
    active = providers if providers is not None else list(pc.keys())
    for provider in active:
        _init_provider_settings_json(
            project_root,
            pc[provider],
            agent_meta_root,
            variables or {},
            log,
            dry_run,
        )


def init_settings_local_json(
    agent_meta_root: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
    providers: list[str] | None = None,
    provider_config: dict | None = None,
    variables: dict | None = None,
) -> None:
    """Create provider-local settings files if they do not exist yet.

    These files are gitignored and intended for personal / machine-local
    overrides. Created once on --init or first sync — never overwritten.
    """
    from .config import substitute

    pc = provider_config or {}
    active = providers if providers is not None else list(pc.keys())
    for provider in active:
        prov_cfg = pc[provider]
        local_file = prov_cfg.get("settings_local_file")
        if not local_file:
            continue
        target_path = safe_path(project_root, local_file)
        if target_path.exists():
            log.skip(str(target_path.relative_to(project_root)), "already exists")
            continue

        template_rel = prov_cfg.get("settings_local_template")
        template_path = agent_meta_root / template_rel if template_rel else None
        if template_path and template_path.exists():
            content = substitute(
                template_path.read_text(encoding="utf-8"),
                variables or {}, template_rel, log,
            )
            source_label = template_rel
        else:
            content = _settings_local_fallback(local_file)
            source_label = "personal/local skeleton (gitignored)"

        log.action("INIT", str(target_path.relative_to(project_root)), source_label)
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")


def _settings_local_fallback(local_file: str) -> str:
    """Return a minimal, extension-aware skeleton for a local settings file."""
    lower = local_file.lower()
    if lower.endswith((".yaml", ".yml")):
        return "# Local overrides — managed by agent-meta, never committed\n"
    return '{\n  "//": "Local overrides — managed by agent-meta, never committed"\n}\n'


def ensure_gitignore_entries(
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
    gitignore_entries: list[str] | None = None,
    exact_entries: list[str] | None = None,
):
    """Ensure required entries exist in a managed block in .gitignore.

    Writes a clearly marked block so users know the entries are managed by
    agent-meta and should not be removed manually.

    gitignore_entries: entries to add (additive — never removes existing block entries).
    exact_entries: if provided, the managed block is set to exactly these entries
                   (entries no longer needed are removed from the block).
    """
    if exact_entries is not None:
        required = list(exact_entries)
    elif gitignore_entries is not None:
        required = list(gitignore_entries)
    else:
        required = []

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

    required_set = set(required)
    if exact_entries is not None:
        # Exact mode: block must contain exactly required_set
        new_block_entries = sorted(required_set)
        changed = block_entries != required_set
        added = sorted(required_set - block_entries)
        removed = sorted(block_entries - required_set)
    else:
        # Additive mode: add missing entries, never remove
        missing = [e for e in required if e not in block_entries]
        if not missing:
            log.skip(".gitignore", "all required entries already present")
            return
        new_block_entries = sorted(block_entries | required_set)
        changed = True
        added = missing
        removed = []

    if not changed:
        log.skip(".gitignore", "all required entries already present")
        return

    new_block = (
        GITIGNORE_BLOCK_BEGIN + "\n"
        + "\n".join(new_block_entries) + "\n"
        + GITIGNORE_BLOCK_END
    )

    if block_match:
        new_content = block_pattern.sub(new_block, existing)
    else:
        new_content = existing.rstrip("\n") + "\n\n" + new_block + "\n"

    parts = []
    if added:
        parts.append(f"added: {', '.join(added)}")
    if removed:
        parts.append(f"removed: {', '.join(removed)}")
    log.action("UPDATE", ".gitignore", f"managed block — {'; '.join(parts)}")
    if not dry_run:
        gitignore_path.write_text(new_content, encoding="utf-8")


def sync_claude_md_static(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Create or regenerate the STATIC part of CLAUDE.md (above the managed block).

    Supersedes the old write-once init_claude_md(): the static header (project
    name, tech stack, architecture — all derived from project.yaml) is now
    refreshed on every sync so it never drifts. The managed block itself stays
    owned by sync_claude_md_managed()/_update_managed_html_block() and is
    preserved verbatim here. User edits to the static part are detected via the
    sidecar hash store and backed up before overwrite.
    """
    from .config import substitute

    template_path = agent_meta_root / "templates" / "configs" / "CLAUDE.project-template.md"
    target_path = project_root / "CLAUDE.md"
    rel = "CLAUDE.md"

    if not template_path.exists():
        log.warn(f"CLAUDE.project-template.md not found at {template_path}")
        return

    if not target_path.exists():
        rendered = substitute(
            template_path.read_text(encoding="utf-8"), variables,
            "CLAUDE.project-template.md", log,
        )
        new_header, _managed, _footer = _split_context_file(rendered)
        log.action("INIT", rel, "templates/configs/CLAUDE.project-template.md")
        if not dry_run:
            target_path.write_text(rendered, encoding="utf-8")
        _record_static_hash(project_root, rel, new_header, dry_run)
        return

    _regenerate_static_context(
        project_root, target_path, template_path, variables, log, dry_run,
        rel_label=rel, source_label="CLAUDE.project-template.md",
    )


def only_variables(
    project_root: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    providers: list[str] | None = None,
    provider_config: dict | None = None,
):
    """Substitute {{VARIABLE}} placeholders in existing provider context files."""
    from .config import substitute

    pc = provider_config or {}
    active = providers if providers is not None else list(pc.keys())
    found_any = False
    for provider in active:
        context_file = pc[provider].get("context_file")
        if not context_file:
            continue
        target_path = safe_path(project_root, context_file)
        if not target_path.exists():
            continue
        found_any = True
        content = target_path.read_text(encoding="utf-8")
        new_content = substitute(content, variables, context_file, log)

        if new_content == content:
            log.skip(context_file, "no open placeholders")
        else:
            log.action("WRITE", context_file, "variables from config")
            if not dry_run:
                target_path.write_text(new_content, encoding="utf-8")

    if not found_any:
        print("  !  No provider context file found — use --init to create one")
        import sys
        sys.exit(1)


def sync_prompts_for_continue(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    provider_config: dict | None = None,
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
    from .config import substitute, strip_inactive_conditional_blocks
    from .providers import resolve_provider_options
    from .roles import build_role_map

    opts = resolve_provider_options(config, "Continue")
    if not opts.get("generate-prompts", False):
        return

    pc = (provider_config or {}).get("Continue", {})
    provider_vars = {
        'EXTENSION_DIR': pc.get('extension_dir', '.continue/3-project'),
        'SNIPPETS_DIR': pc.get('snippets_dir', '.continue/snippets'),
        'PENDING_TASKS_FILE': pc.get('pending_tasks_file', '.continue/pending-tasks.md'),
        'SKILLS_DIR': pc.get('skills_dir', '.continue/skills'),
    }
    merged_vars = {**variables, **provider_vars}

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
        target_path = safe_path(prompts_dir, filename)
        content = source_path.read_text(encoding="utf-8")

        # Composition
        extends_base = extract_frontmatter_field(content, "extends")
        if extends_base:
            base_path = agent_meta_root / AGENTS_DIR / extends_base
            content = compose_agent(base_path, content, log)

        rel_source = str(source_path.relative_to(agent_meta_root))
        content = substitute(content, merged_vars, rel_source, log)
        content = strip_inactive_conditional_blocks(content, merged_vars)

        # Apply PAL delegation syntax for Continue prompts
        from .delegation_syntax import DelegationSyntaxEngine
        pal_engine = DelegationSyntaxEngine(config_dir=agent_meta_root / "config")
        content = pal_engine.apply(content, "Continue")

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


def sync_snippets_for_provider(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: dict,
):
    """Copy snippet files from agent-meta/snippets/ to the provider-specific snippets dir.

    Only copies snippets referenced via TESTER_SNIPPETS_PATH (or similar *_SNIPPETS_PATH
    variables) in the project config. Unknown snippet files are skipped.
    All referenced paths are resolved relative to agent-meta/snippets/.
    """
    from .agents import extract_frontmatter_field

    pc = provider_config.get(provider, {})
    snippets_dir_rel = pc.get('snippets_dir')
    if not snippets_dir_rel:
        log.info("snippets", f"skipped for {provider} — no snippets_dir configured")
        return

    variables = config.get("variables", {})
    snippets_root = agent_meta_root / SNIPPETS_DIR
    target_root = project_root / snippets_dir_rel

    if not snippets_root.exists():
        return

    # Collect all *_SNIPPETS_PATH values from config variables
    snippet_paths: list[str] = [
        v for k, v in variables.items()
        if k.endswith("_SNIPPETS_PATH") and v
    ]

    # Remove stale snippet files no longer referenced in config
    expected_rel_paths: set[str] = set(snippet_paths)
    if target_root.exists():
        for existing in target_root.rglob("*.md"):
            rel = existing.relative_to(target_root).as_posix()
            if rel not in expected_rel_paths:
                log.action("DELETE", str(existing.relative_to(project_root)), "stale snippet")
                if not dry_run:
                    existing.unlink()

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
