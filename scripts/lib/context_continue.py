"""Continue provider context: prompts and config.yaml managed blocks."""

import re
from pathlib import Path

from .io import safe_path
from .log import SyncLog

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
                          _make_slim_body, AGENTS_DIR, _PROVIDER_PARALLEL_PATTERNS)
    from .config import substitute
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
        'PARALLEL_PATTERN': _PROVIDER_PARALLEL_PATTERNS.get("Continue", _PROVIDER_PARALLEL_PATTERNS["Claude"]),
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
