"""Agent file generation: frontmatter, composition, sync logic."""

from pathlib import Path

from .log import SyncLog
from .io import safe_path, write_checked
from .agents_frontmatter import (
    extract_frontmatter_field,
    build_frontmatter,
    inject_model_field,
    inject_memory_field,
    inject_permission_mode_field,
    inject_temperature_field,
    inject_max_tokens_field,
    inject_agent_fields,
    _strip_frontmatter,
    _remove_frontmatter_fields,
    _transform_frontmatter_for_opencode,
    _strip_claude_specific_lines,
)
from .agents_template import (
    target_filename,
    ext_target_filename,
    role_from_platform_file,
    apply_patch,
    compose_agent,
    collect_sources,
    AGENTS_DIR,
    EXTERNAL_DIR,
    SKILL_WRAPPER,
)

# Re-export public API so external callers (tests, sync.py) don't break
__all__ = [
    "extract_frontmatter_field",
    "build_frontmatter",
    "inject_model_field",
    "inject_memory_field",
    "inject_permission_mode_field",
    "inject_temperature_field",
    "inject_max_tokens_field",
    "inject_agent_fields",
    "target_filename",
    "ext_target_filename",
    "role_from_platform_file",
    "apply_patch",
    "compose_agent",
    "collect_sources",
    "sync_agents",
    "sync_agents_for_provider",
    "build_agent_hints",
    "build_agent_table",
    "inject_debug_block",
]

# Provider-specific parallel execution patterns (injected as {{PARALLEL_PATTERN}})
_PROVIDER_PARALLEL_PATTERNS: dict[str, str] = {
    "Claude": (
        "**Parallel-Pattern (konkret):**\n"
        "```\n"
        '# Vordergrund:\n'
        'Agent(subagent_type="validator", prompt="DoD-Check für ...")\n'
        "# Gleichzeitig im Hintergrund:\n"
        'Agent(subagent_type="documenter", prompt="Update CODEBASE_OVERVIEW ...", run_in_background=True)\n'
        "# Dann warten bis Hintergrund fertig, dann:\n"
        'Agent(subagent_type="git", prompt="Commit und PR erstellen ...")\n'
        "```\n"
    ),
    "Opencode": (
        "**Parallel-Pattern (konkret):**\n"
        "Opencode unterstützt parallele Subagent-Ausführung via mehrfacher `Agent`-Tool-Aufrufe.\n"
        "Starte unabhängige Agenten nacheinander im selben Kontext — sie laufen implizit parallel.\n"
    ),
    "Gemini": (
        "**Parallel-Pattern (konkret):**\n"
        "Gemini Code Assist führt unabhängige Tool-Aufrufe parallel aus.\n"
        "Delegiere an mehrere Agenten in einem einzigen Prompt — die Ausführung erfolgt automatisch parallelisiert.\n"
    ),
    "Continue": (
        "**Parallel-Pattern:**\n"
        "Continue unterstützt keine native parallele Subagent-Ausführung.\n"
        "Führe parallele Schritte sequentiell aus oder verwende separate Continue-Sessions.\n"
    ),
}


def sync_agents(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Generate all .claude/agents/*.md files (legacy Claude-only path)."""
    from .config import substitute, strip_inactive_dod_blocks
    from .roles import build_role_map
    from .skills import load_external_skills_config, _skill_is_active

    CLAUDE_AGENTS_DIR = ".claude/agents"
    role_map = build_role_map(agent_meta_root)
    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    target_dir = project_root / CLAUDE_AGENTS_DIR

    # Optional role whitelist — if "roles" key is absent, all roles are generated
    allowed_roles: set[str] | None = None
    if "roles" in config:
        allowed_roles = set(config["roles"])

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    # Track which filenames will be written in this sync
    expected_filenames: set[str] = set()

    project_name = config["project"]["name"]
    for role, source_path in overrides.items():
        filename = target_filename(role, role_map)
        if not filename:
            log.skip(str(source_path.name), "role not in ROLE_MAP")
            continue

        if allowed_roles is not None and role not in allowed_roles:
            log.skip(str(target_dir / filename).replace(str(project_root) + "/", "").replace(str(project_root) + "\\", ""),
                     f"role '{role}' not in config['roles']")
            continue

        expected_filenames.add(filename)
        target_path = safe_path(target_dir, filename)
        content = source_path.read_text(encoding="utf-8")

        # Composition mode: if 'extends:' present in frontmatter, compose from base
        extends_base = extract_frontmatter_field(content, "extends")
        if extends_base:
            base_path = agent_meta_root / AGENTS_DIR / extends_base
            content = compose_agent(base_path, content, log)
            log.info(
                str(target_path.relative_to(project_root)),
                f"composed from {extends_base} + {source_path.name}",
            )

        rel_source = str(source_path.relative_to(agent_meta_root))
        source_version = extract_frontmatter_field(content, "version")
        template_description = extract_frontmatter_field(content, "description")
        description = (template_description or f"Agent for {project_name}.")
        description = description.replace("{{PROJECT_NAME}}", project_name)
        content = substitute(content, variables, rel_source, log)
        content = strip_inactive_dod_blocks(content, variables, extra_vars=["CI_POLL_ENABLED"])
        name = Path(filename).stem
        layer = source_path.parts[-2]
        source_label = f"{layer}/{source_path.name}"
        generated_from = f"{source_label}@{source_version}" if source_version else source_label
        content = build_frontmatter(content, name, description,
                                    generated_from=generated_from)

        content = inject_agent_fields(
            content, role, config, agent_meta_root,
            log=log, project_root=target_path.parent,
        )

        # Visualization: inject event-logging prompt block when dynamic/full mode is enabled
        viz_cfg = config.get("viz", {})
        if viz_cfg.get("mode") in ("dynamic", "full"):
            from .viz import inject_viz_prompt_block
            content = inject_viz_prompt_block(content, role, "Claude", viz_enabled=True)

        rel_label = str(source_path.relative_to(agent_meta_root / AGENTS_DIR))
        rel_out = str(target_path.relative_to(project_root))
        if not dry_run:
            if write_checked(target_path, content, log, rel_label):
                log.action("WRITE", rel_out, rel_label)
            else:
                log.skip(rel_out, "unchanged")
        else:
            log.action("WRITE", rel_out, rel_label)

    # Also track external skill agent filenames (they are not in overrides)
    ext_config = load_external_skills_config(agent_meta_root)
    project_skills = config.get("external-skills", {})
    for skill_name, skill_cfg in ext_config.get("skills", {}).items():
        if _skill_is_active(skill_name, skill_cfg, project_skills):
            role = skill_cfg.get("role", skill_name)
            expected_filenames.add(f"{role}.md")

    # Remove stale agent files that are no longer in the active role set
    if target_dir.exists():
        for existing_file in sorted(target_dir.glob("*.md")):
            if existing_file.name not in expected_filenames:
                log.action("DELETE", str(existing_file.relative_to(project_root)),
                           "role removed from config")
                if not dry_run:
                    existing_file.unlink()


def sync_agents_for_provider(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: dict,
    platform_vars: dict | None = None,
    debug_mode: bool = False,
):
    """Generate agent files for a specific provider.

    Claude:    .claude/agents/<role>.md   — full frontmatter, all fields
    Gemini:    .gemini/agents/<role>.md   — frontmatter without permissionMode/memory
    Continue:  .continue/agents/<role>.md — minimal frontmatter (name, description, alwaysApply: false)
    """
    from .config import substitute, strip_inactive_dod_blocks
    from .platform import substitute_platform
    from .roles import build_role_map, resolve_model
    from .skills import load_external_skills_config, _skill_is_active

    pc = provider_config.get(provider)
    if not pc:
        log.warn(f"Unknown provider '{provider}' — skipping agent sync")
        return

    role_map = build_role_map(agent_meta_root)
    platforms = config.get('platforms', [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    target_dir = project_root / pc['agents_dir']

    allowed_roles = set(config['roles']) if 'roles' in config else None

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    expected_filenames: set = set()
    project_name = config['project']['name']

    for role, source_path in overrides.items():
        filename = target_filename(role, role_map)
        if not filename:
            if provider == 'Claude':
                log.skip(str(source_path.name), 'role not in ROLE_MAP')
            continue

        if allowed_roles is not None and role not in allowed_roles:
            if provider == 'Claude':
                rel = (str(target_dir / filename)
                       .replace(str(project_root) + '/', '')
                       .replace(str(project_root) + chr(92), ""))
                log.skip(rel, f"role '{role}' not in config['roles']")
            continue

        expected_filenames.add(filename)
        target_path = safe_path(target_dir, filename)
        content = source_path.read_text(encoding='utf-8')

        # Composition mode
        extends_base = extract_frontmatter_field(content, 'extends')
        if extends_base:
            base_path = agent_meta_root / AGENTS_DIR / extends_base
            content = compose_agent(base_path, content, log)
            if provider == 'Claude':
                log.info(
                    str(target_path.relative_to(project_root)),
                    f'composed from {extends_base} + {source_path.name}',
                )

        rel_source = str(source_path.relative_to(agent_meta_root))
        source_version = extract_frontmatter_field(content, 'version')
        template_description = extract_frontmatter_field(content, 'description')
        description = (template_description or f'Agent for {project_name}.')
        description = description.replace('{{PROJECT_NAME}}', project_name)

        # Merge provider-specific variables (extension paths, snippets dir, parallel patterns, etc.)
        provider_vars = {
            'EXTENSION_DIR': pc.get('extension_dir', '.claude/3-project'),
            'SNIPPETS_DIR': pc.get('snippets_dir', '.claude/snippets'),
            'PENDING_TASKS_FILE': pc.get('pending_tasks_file', '.claude/pending-tasks.md'),
            'SKILLS_DIR': pc.get('skills_dir', '.claude/skills'),
            'PARALLEL_PATTERN': _PROVIDER_PARALLEL_PATTERNS.get(provider, _PROVIDER_PARALLEL_PATTERNS['Claude']),
        }
        merged_vars = {**variables, **provider_vars}
        content = substitute(content, merged_vars, rel_source, log)
        content = strip_inactive_dod_blocks(content, variables, extra_vars=["CI_POLL_ENABLED"])
        # Apply platform-config substitution ({{platform.*}} placeholders)
        if platform_vars is not None:
            content = substitute_platform(content, platform_vars, rel_source, log)
        name = Path(filename).stem
        layer = source_path.parts[-2]
        source_label = f'{layer}/{source_path.name}'
        generated_from = f'{source_label}@{source_version}' if source_version else source_label

        if provider == 'Continue':
            # Continue agents: minimal frontmatter (name + description only)
            # alwaysApply: false — agent is invoked by name, not auto-loaded
            fm = f"---\nname: {name}\ndescription: \"{description}\"\nalwaysApply: false\n---\n"
            body = _strip_frontmatter(content)
            body = _strip_claude_specific_lines(body)
            content = fm + body
        else:
            content = build_frontmatter(content, name, description, generated_from=generated_from)

            if provider == 'Claude':
                content = inject_agent_fields(
                    content, role, config, agent_meta_root,
                    provider=provider, provider_config=provider_config,
                    log=log, project_root=target_path.parent,
                )

            elif provider == 'Gemini':
                # Gemini: provider-mapped model only; strip memory, permissionMode, Claude-specific lines
                model = resolve_model(role, config, agent_meta_root,
                                      provider=provider, provider_config=provider_config)
                content = inject_model_field(content, model)
                if model:
                    po = config.get('model-overrides', {})
                    is_override = role in po.get('Gemini', {})
                    src = 'project override' if is_override else 'meta default'
                    log.info(str(target_path.relative_to(project_root)), f'model: {model} (from {src})')
                content = _remove_frontmatter_fields(content, ['memory', 'permissionMode'])
                body = _strip_frontmatter(content)
                body = _strip_claude_specific_lines(body)
                fm_end = content.find('\n---', 3)
                if fm_end != -1:
                    content = content[:fm_end + 4] + '\n' + body.lstrip('\n')

            elif provider == 'Opencode':
                # Opencode: native frontmatter (description + mode: subagent + model)
                # Model IDs use "provider/model-id" format (e.g. anthropic/claude-sonnet-4-6)
                model = resolve_model(role, config, agent_meta_root,
                                      provider=provider, provider_config=provider_config)
                if model:
                    po = config.get('model-overrides', {})
                    is_override = role in po.get('Opencode', {})
                    src = 'project override' if is_override else 'meta default'
                    log.info(str(target_path.relative_to(project_root)), f'model: {model} (from {src})')
                content = _transform_frontmatter_for_opencode(
                    content, name, description, model, generated_from
                )

        # Visualization: inject event-logging prompt block when dynamic/full mode is enabled
        # Applies to ALL providers — every generated agent gets the viz reporting block
        viz_cfg = config.get('viz', {})
        if viz_cfg.get('mode') in ('dynamic', 'full'):
            from .viz import inject_viz_prompt_block
            content = inject_viz_prompt_block(content, role, provider, viz_enabled=True)

        if debug_mode:
            content = inject_debug_block(content, name)

        rel_label = str(source_path.relative_to(agent_meta_root / AGENTS_DIR))
        rel_out = str(target_path.relative_to(project_root))
        if not dry_run:
            if write_checked(target_path, content, log, rel_label):
                log.action('WRITE', rel_out, rel_label)
            else:
                log.skip(rel_out, 'unchanged')
        else:
            log.action('WRITE', rel_out, rel_label)

    # External skill filenames are always in .claude/agents/ (Claude only)
    if provider == 'Claude':
        ext_config = load_external_skills_config(agent_meta_root)
        project_skills = config.get('external-skills', {})
        for skill_name, skill_cfg in ext_config.get('skills', {}).items():
            if _skill_is_active(skill_name, skill_cfg, project_skills):
                ext_role = skill_cfg.get('role', skill_name)
                expected_filenames.add(f'{ext_role}.md')

    # Remove stale agent files
    if target_dir.exists():
        managed_index = target_dir / '.agent-meta-managed'
        previously_managed: set = set()
        if managed_index.exists():
            for line in managed_index.read_text(encoding='utf-8').splitlines():
                if line.strip():
                    previously_managed.add(line.strip())

        for existing_file in sorted(target_dir.glob('*.md')):
            if existing_file.name not in expected_filenames:
                if not managed_index.exists() or existing_file.name in previously_managed:
                    log.action('DELETE', str(existing_file.relative_to(project_root)),
                               'role removed from config')
                    if not dry_run:
                        existing_file.unlink()

        if not dry_run and expected_filenames:
            managed_index.write_text(
                '\n'.join(sorted(expected_filenames)) + '\n', encoding='utf-8'
            )


_DEBUG_BLOCK_MARKER = "<!-- agent-meta:debug-mode -->"

_DEBUG_BLOCK_TEMPLATE = """\

---

{marker}
## Debug-Modus

**Aktiv.** Starte jede Antwort mit: `[Agent: {agent_name}]`

Bei jeder Delegation an einen Sub-Agenten:
```
→ Delegiere an: <agent-name> — <kurze Aufgabenbeschreibung>
```

Am Ende jeder Antwort:
```
✓ [Agent: {agent_name}] fertig
```
"""


def inject_debug_block(content: str, agent_name: str) -> str:
    """Append a debug-mode instructions block to agent content.

    Only called when debug-mode: true is set in project.yaml.
    When not called (debug-mode: false, the default), content is unchanged.
    """
    if _DEBUG_BLOCK_MARKER in content:
        return content
    return content.rstrip("\n") + _DEBUG_BLOCK_TEMPLATE.format(
        marker=_DEBUG_BLOCK_MARKER,
        agent_name=agent_name,
    )


def _make_slim_body(content: str) -> str:
    """Reduce agent body to a compact prompt-friendly version.

    Keeps: role description, active DoD table, core workflow steps, Don'ts.
    Strips: extension hooks, verbose sub-sections, examples.
    """
    lines = content.splitlines()
    out = []
    skip_section = False
    slim_stop_anchors = {
        "## Workflow",
        "## Workflows",
        "## Schritt-für-Schritt",
        "## Beispiele",
        "## Beispiel",
        "## Anhang",
    }

    for line in lines:
        stripped = line.strip()
        # Skip extension-hook lines (Claude-specific)
        if stripped.startswith("> **Extension:**"):
            continue
        # Detect section changes
        if stripped.startswith("## "):
            skip_section = stripped in slim_stop_anchors
        if not skip_section:
            out.append(line)

    # Cap at ~80 lines for slim mode
    if len(out) > 80:
        out = out[:80]
        out.append("\n\n*[Prompt truncated — use agent mode for full context]*")

    return "\n".join(out)


def build_agent_hints(config: dict, agent_meta_root: Path) -> str:
    """Generate agent usage hints for {{AGENT_HINTS}}.

    Reads hint (preferred) or description from each active agent's template frontmatter.
    If orchestrator is active, adds a prominent start hint.
    """
    from .roles import build_role_map

    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    role_map = build_role_map(agent_meta_root)
    allowed_roles: set[str] | None = None
    if "roles" in config:
        allowed_roles = set(config["roles"])

    lines = []
    has_orchestrator = (
        "orchestrator" in overrides
        and (allowed_roles is None or "orchestrator" in allowed_roles)
    )
    if has_orchestrator:
        lines.append(
            "> **Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben."
        )
        lines.append("")

    lines.append("| Agent | Zuständigkeit |")
    lines.append("|-------|--------------|")
    for role, source_path in sorted(overrides.items()):
        if allowed_roles is not None and role not in allowed_roles:
            continue
        if not target_filename(role, role_map):
            continue
        content = source_path.read_text(encoding="utf-8")
        hint = extract_frontmatter_field(content, "hint") \
            or extract_frontmatter_field(content, "description") \
            or ""
        lines.append(f"| `{role}` | {hint} |")

    return "\n".join(lines)


def build_agent_table(config: dict, agent_meta_root: Path) -> tuple[str, list[str]]:
    """Generate markdown table for {{AGENT_TABLE}}. Returns (table, unmapped_warnings).

    Only includes roles present in config['roles'] whitelist (if set).
    """
    from .roles import build_role_map

    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    role_map = build_role_map(agent_meta_root)
    allowed_roles: set[str] | None = None
    if "roles" in config:
        allowed_roles = set(config["roles"])

    rows = []
    unmapped = []
    for role, source_path in sorted(overrides.items()):
        if allowed_roles is not None and role not in allowed_roles:
            continue
        filename = target_filename(role, role_map)
        if not filename:
            unmapped.append(
                f"Role '{role}' ({source_path.name}) not in ROLE_MAP — skipped in AGENT_TABLE"
            )
            continue
        agent_name = Path(filename).stem
        layer = source_path.parts[-2]
        rows.append(f"| `{agent_name}` | `{source_path.name}` | {layer} |")

    header = "| Agent | Quelle | Layer |\n|-------|--------|-------|"
    return header + "\n" + "\n".join(rows), unmapped
