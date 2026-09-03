"""Agent sync orchestration: compose, patch, path-rules and provider write-out.

Top I/O-orchestration layer of the agent pipeline (Issue #561 split of
agents.py). sync_agents_for_provider drives generation of every provider's
agent files; composition/patch helpers and MCP-tool resolution live here too.
Imports the neutral frontmatter layer and the provider_transform formatting
layer; heavier peers (mcp, rules, skills, viz, pipelines, roles, ...) are
imported lazily inside functions to avoid load-time import cycles.
"""
from __future__ import annotations

import re
from pathlib import Path

from .frontmatter import (
    AGENTS_DIR,
    _YAML_AVAILABLE,
    _is_role_enabled,
    _merge_frontmatter,
    _parse_frontmatter_yaml,
    _strip_frontmatter,
    append_frontmatter_tools,
    collect_sources,
    extract_frontmatter_field,
    target_filename,
)
from .io import safe_path, write_checked
from .log import SyncLog
from .provider_transform import (
    inject_debug_block,
    transform_agent_content_for_provider,
    wrap_sections_in_xml,
)
from .variables import strip_inactive_conditional_blocks, substitute

def _tools_can_spawn(tools) -> bool:
    """Return True if a frontmatter `tools` value grants sub-agent spawning.

    Spawning requires the `Agent` or `Task` tool (or a `*` wildcard granting all
    tools). Accepts the value in its raw frontmatter forms: a YAML list, a
    comma/space-separated string, or `*`. Anything else → cannot spawn.
    """
    if tools is None:
        return False
    if isinstance(tools, str):
        if tools.strip() == "*":
            return True
        items = re.split(r"[,\s]+", tools)
    elif isinstance(tools, (list, tuple)):
        if "*" in tools:
            return True
        items = tools
    else:
        return False
    names = {str(i).strip() for i in items if str(i).strip()}
    return "Agent" in names or "Task" in names

def resolve_mcp_tools_for_role(
    role: str,
    config: dict,
    agent_meta_root: Path,
    project_root: Path | None = None,
) -> list[str]:
    """Return the namespaced MCP tool names a role may use, e.g. ``mcp__playwright__browser_click``.

    A role opts in via ``mcp-servers:`` in ``config/role-defaults.yaml`` (or
    ``mcp-role-overrides.<role>`` in project.yaml, which wins). Only servers
    that are actually active for the project contribute tools, and only the
    server's ``tools.allowed`` entries — ``tools.blocked`` never leaks in.

    Without this the generated frontmatter lists just the base tools, so a role
    documented as MCP-capable (e2e-tester + playwright) starts a session with
    none of those tools bound (issue #467).
    """
    from .mcp import load_mcp_registry, resolve_active_mcp_servers
    from .roles import load_roles_config

    overrides = config.get("mcp-role-overrides", {}) or {}
    if role in overrides:
        wanted = overrides.get(role) or []
    else:
        role_cfg = load_roles_config(agent_meta_root)["roles"].get(role, {}) or {}
        wanted = role_cfg.get("mcp-servers", []) or []
    if isinstance(wanted, str):
        wanted = [wanted]
    if not wanted:
        return []

    registry = load_mcp_registry(agent_meta_root, config, project_root)
    active = set(resolve_active_mcp_servers(config, agent_meta_root, project_root, registry=registry))

    tools: list[str] = []
    for server in wanted:
        if server not in active:
            continue
        allowed = (registry.get(server, {}).get("tools", {}) or {}).get("allowed", []) or []
        for tool in allowed:
            name = f"mcp__{server}__{tool}"
            if name not in tools:
                tools.append(name)
    return tools

_CRITICAL_RULES = [
    "branch-guard",
    "commit-conventions",
    "dod-criteria",
]

def _extract_and_append_critical_footer(
    content: str,
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    provider: str = "Claude",
) -> str:
    """Append critical rules as a footer to generated agent content.

    Reads critical rule files, substitutes variables, strips frontmatter,
    and appends them as a '## Critical Rules' section at the end.

    Only rules that exist and are active (per rules-preset) are included.
    """
    from .rules import collect_rule_sources, resolve_rules

    rule_options = resolve_rules(config, agent_meta_root)
    platforms = config.get("platforms", [])
    sources = collect_rule_sources(agent_meta_root, platforms)

    # Build a lookup: rule_stem -> source_path
    source_map: dict[str, Path] = {}
    for source_path, output_name in sources:
        rule_stem = Path(output_name).stem
        if rule_stem in _CRITICAL_RULES:
            source_map[rule_stem] = source_path

    footer_sections: list[str] = []
    for rule_name in _CRITICAL_RULES:
        source_path = source_map.get(rule_name)
        if not source_path or not source_path.exists():
            continue

        opts = rule_options.get(rule_name, {})
        # Skip if rule is disabled via rules-preset
        if opts.get("alwaysApply") is False and opts.get("embed") is False:
            continue

        rule_content = source_path.read_text(encoding="utf-8")
        rel_source = f"rules/{source_path.parts[-2]}/{source_path.name}"
        rule_content = substitute(rule_content, variables, rel_source, log)

        # Strip frontmatter if present
        body = _strip_frontmatter(rule_content).strip()
        if body:
            footer_sections.append(body)

    if not footer_sections:
        return content

    footer = "\n\n---\n\n## Critical Rules\n\n" + "\n\n---\n\n".join(footer_sections)
    return content.rstrip() + footer

def apply_path_rules(
    content: str,
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    role: str,
) -> str:
    """Apply path-based contextual rules to agent content.

    Reads `pathRules` from config. Each rule has:
      - path: glob pattern (e.g. "*.py", "scripts/**", "agents/**/*.md")
      - rule: rule file name (stem) to include (e.g. "python-conventions")
      - agents: optional list of agent roles this rule applies to (default: all)

    Matching rules are read, variables substituted, and appended as
    "## Contextual Rules" section.
    """
    from .rules import collect_rule_sources, resolve_rules

    path_rules = config.get("pathRules", [])
    if not path_rules:
        return content

    # Build rule lookup: stem -> source_path
    platforms = config.get("platforms", [])
    sources = collect_rule_sources(agent_meta_root, platforms)
    rule_options = resolve_rules(config, agent_meta_root)
    source_map: dict[str, Path] = {}
    for source_path, output_name in sources:
        rule_stem = Path(output_name).stem
        source_map[rule_stem] = source_path

    matched_sections: list[str] = []
    for rule_def in path_rules:
        path_pattern = rule_def.get("path", "")
        rule_name = rule_def.get("rule", "")
        agents = rule_def.get("agents")  # None = all agents

        # Check if rule applies to this agent
        if agents is not None and role not in agents:
            continue

        source_path = source_map.get(rule_name)
        if not source_path or not source_path.exists():
            log.warning(f"pathRules: rule file '{rule_name}' not found (pattern: '{path_pattern}')")
            continue

        opts = rule_options.get(rule_name, {})
        if opts.get("alwaysApply") is False and opts.get("embed") is False:
            continue

        rule_content = source_path.read_text(encoding="utf-8")
        rel_source = f"rules/{source_path.parts[-2]}/{source_path.name}"
        rule_content = substitute(rule_content, variables, rel_source, log)
        body = _strip_frontmatter(rule_content).strip()

        if body:
            matched_sections.append(f"### Rule for `{path_pattern}`\n\n{body}")

    if not matched_sections:
        return content

    footer = "\n\n---\n\n## Contextual Rules\n\n" + "\n\n---\n\n".join(matched_sections)
    return content.rstrip() + footer

def _find_section_bounds(lines: list[str], anchor: str) -> tuple[int, int] | None:
    """Find (start, end) line indices for a section.

    Supports two anchor modes:
    - XML-tag anchor (e.g. '<workflow>'): start = line with opening tag,
      end = line after the matching closing '</tag>' (inclusive of close line).
    - Markdown heading anchor (e.g. '## Don\\'ts'): start = heading line,
      end = first line of next section at same or higher level (exclusive).
    """
    anchor_stripped = anchor.strip()

    # XML-anchor mode: anchor starts with '<' (e.g. '<workflow>')
    if anchor_stripped.startswith("<") and not anchor_stripped.startswith("</"):
        tag = anchor_stripped.strip("<>").strip()
        open_tag = f"<{tag}>"
        close_tag = f"</{tag}>"
        start_idx = None
        # Match only standalone tag lines (tag alone on its line), so inline
        # mentions like "(see `<context>`)" in prose never anchor a section.
        # Mirrors config_audit._STANDALONE_TAG_RE semantics.
        for i, line in enumerate(lines):
            stripped = line.strip()
            if start_idx is None and stripped == open_tag:
                start_idx = i
            elif start_idx is not None and stripped == close_tag:
                return (start_idx, i + 1)
        return None  # tag not found or unclosed

    anchor_level = len(anchor_stripped) - len(anchor_stripped.lstrip("#"))

    start_idx = None
    for i, line in enumerate(lines):
        if line.rstrip() == anchor_stripped:
            start_idx = i
            break

    if start_idx is None:
        return None

    in_fence = False
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if level <= anchor_level:
                return (start_idx, i)

    return (start_idx, len(lines))

def _dominant_newline(lines: list[str]) -> str:
    """Return the majority line-ending style ('\\r\\n' or '\\n') of a splitlines(keepends=True) list."""
    crlf_count = sum(1 for line in lines if line.endswith("\r\n"))
    lf_count = sum(1 for line in lines if line.endswith("\n") and not line.endswith("\r\n"))
    return "\r\n" if crlf_count > lf_count else "\n"

def _patch_append_after(content: str, anchor: str, patch_content: str,
                        log: SyncLog, source_label: str) -> str:
    """Insert patch_content after the section identified by anchor."""
    lines = content.splitlines(keepends=True)
    bounds = _find_section_bounds(lines, anchor)
    if bounds is None:
        log.warning(f"Composition patch 'append-after': anchor '{anchor}' not found in {source_label}")
        return content
    _, end_idx = bounds
    nl = _dominant_newline(lines)
    normalized_patch = patch_content.replace("\r\n", "\n").rstrip("\n").replace("\n", nl)
    patch_lines = (nl + nl + normalized_patch + nl + nl).splitlines(keepends=True)
    result_lines = lines[:end_idx] + patch_lines + lines[end_idx:]
    return "".join(result_lines)

def _patch_replace(content: str, anchor: str, patch_content: str,
                   log: SyncLog, source_label: str) -> str:
    """Replace the entire section identified by anchor with patch_content."""
    lines = content.splitlines(keepends=True)
    bounds = _find_section_bounds(lines, anchor)
    if bounds is None:
        log.warning(f"Composition patch 'replace': anchor '{anchor}' not found in {source_label}")
        return content
    start_idx, end_idx = bounds
    nl = _dominant_newline(lines)
    normalized_patch = patch_content.replace("\r\n", "\n").rstrip("\n").replace("\n", nl)
    patch_lines = (normalized_patch + nl).splitlines(keepends=True)
    result_lines = lines[:start_idx] + patch_lines + lines[end_idx:]
    return "".join(result_lines)

def _patch_delete(content: str, anchor: str, log: SyncLog, source_label: str) -> str:
    """Delete the entire section identified by anchor."""
    lines = content.splitlines(keepends=True)
    bounds = _find_section_bounds(lines, anchor)
    if bounds is None:
        log.warning(f"Composition patch 'delete': anchor '{anchor}' not found in {source_label}")
        return content
    start_idx, end_idx = bounds
    # Also remove leading blank line before section if present
    trim_start = start_idx
    if trim_start > 0 and lines[trim_start - 1].strip() == "":
        trim_start -= 1
    result_lines = lines[:trim_start] + lines[end_idx:]
    return "".join(result_lines)

def apply_patch(content: str, patch: dict, log: SyncLog, source_label: str) -> str:
    """Apply a single composition patch to content."""
    op = patch.get("op", "")
    anchor = patch.get("anchor", "")
    patch_content = patch.get("content", "")

    if op == "append":
        lines = content.splitlines(keepends=True)
        nl = _dominant_newline(lines)
        normalized_patch = patch_content.replace("\r\n", "\n").rstrip("\n").replace("\n", nl)
        return content.rstrip("\n").rstrip("\r") + nl + nl + normalized_patch + nl
    elif op == "append-after":
        return _patch_append_after(content, anchor, patch_content, log, source_label)
    elif op == "replace":
        return _patch_replace(content, anchor, patch_content, log, source_label)
    elif op == "delete":
        return _patch_delete(content, anchor, log, source_label)
    else:
        log.warning(f"Composition: unknown patch op '{op}' in {source_label}")
        return content

def compose_agent(
    base_path: Path,
    override_content: str,
    log: SyncLog,
) -> str:
    """Load base template, apply patches from override frontmatter, merge frontmatter.

    Returns the composed document ready for variable substitution.
    """
    if not _YAML_AVAILABLE:
        log.warning(
            "PyYAML not available — composition skipped. "
            "Install it with: pip install pyyaml"
        )
        return override_content

    if not base_path.exists():
        log.warning(f"Composition: base template not found: {base_path}")
        return override_content

    base_content = base_path.read_text(encoding="utf-8")
    override_fm = _parse_frontmatter_yaml(override_content)
    patches = override_fm.get("patches") or []

    # Start from base, apply each patch
    result = base_content
    source_label = base_path.name
    for patch in patches:
        result = apply_patch(result, patch, log, source_label)

    # Merge frontmatter: override fields win over base fields
    result = _merge_frontmatter(result, override_fm)

    return result

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
    from .pipelines import (
        apply_overrides,
        inject_pipeline_blocks,
        load_quality_pipelines,
    )
    from .platform import substitute_platform
    from .roles import (
        build_role_map,
        load_roles_config,
        resolve_max_tokens,
        resolve_memory,
        resolve_model,
        resolve_permission_mode,
        resolve_steps,
        resolve_temperature,
    )
    from .io import _normalize_enabled_config
    from .skills import _skill_is_active, load_external_skills_config

    pc = provider_config.get(provider)
    if not pc:
        log.warning(f"Unknown provider '{provider}' — skipping agent sync")
        return

    role_map = build_role_map(agent_meta_root)
    platforms = config.get('platforms', [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    target_dir = project_root / pc['agents_dir']

    allowed_roles = set(config['roles']) if 'roles' in config else None

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    expected_filenames: set = set()
    project_name = config.get('project', {}).get('name', 'unknown')

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

        if not _is_role_enabled(role, config):
            if provider == 'Claude':
                rel = (str(target_dir / filename)
                       .replace(str(project_root) + '/', '')
                       .replace(str(project_root) + chr(92), ""))
                if role.startswith("knowledge-"):
                    log.skip(rel, "knowledge-engine is disabled")
                else:
                    log.skip(rel, "systems-engineering is disabled")
            continue

        # Skip orchestrator agent file in main-chat mode — no orchestrator subagent
        # is spawned; the main chat acts as router + worker. Not added to
        # expected_filenames so any stale orchestrator.md gets pruned.
        if role == "orchestrator" and variables.get("ORCH_MODE_MAIN_CHAT") == "true":
            if provider == 'Claude':
                rel = (str(target_dir / filename)
                       .replace(str(project_root) + '/', '')
                       .replace(str(project_root) + chr(92), ""))
                log.skip(rel, "orchestrator skipped — ORCH_MODE_MAIN_CHAT active")
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
                log.note(
                    str(target_path.relative_to(project_root)),
                    f'composed from {extends_base} + {source_path.name}',
                )

        # Capture spawn capability from the (composed) source frontmatter before
        # any provider-specific tool transformation mangles the tools field.
        _can_spawn = _tools_can_spawn(_parse_frontmatter_yaml(content).get('tools'))

        rel_source = str(source_path.relative_to(agent_meta_root))
        source_version = extract_frontmatter_field(content, 'version')
        template_description = extract_frontmatter_field(content, 'description')
        description = (template_description or f'Agent for {project_name}.')
        description = description.replace('{{PROJECT_NAME}}', project_name)

        # Merge provider-specific variables (extension paths, snippets dir, parallel patterns, etc.)
        from .delegation_syntax import DelegationSyntaxEngine
        _ds_engine = DelegationSyntaxEngine(config_dir=agent_meta_root / "config")
        file_based = _ds_engine.has_file_based_agents(provider)
        provider_vars = {
            'EXTENSION_DIR': pc.get('extension_dir', f".{provider.lower()}/3-project"),
            'SNIPPETS_DIR': pc.get('snippets_dir', f".{provider.lower()}/snippets"),
            'PENDING_TASKS_FILE': pc.get('pending_tasks_file', f".{provider.lower()}/pending-tasks.md"),
            'SKILLS_DIR': pc.get('skills_dir', f".{provider.lower()}/skills"),
            'CONTEXT_FILE': pc.get('context_file', f"{provider.upper()}.md"),
            'FILE_BASED_AGENTS': 'true' if file_based else 'false',
        }
        merged_vars = {**variables, **provider_vars}

        # Inject provider-specific pipeline blocks before standard substitution
        pipelines = load_quality_pipelines(str(agent_meta_root))
        pipeline_overrides = config.get("quality-pipelines", {})
        effective = apply_overrides(pipelines, pipeline_overrides)
        if effective:
            from .dod import resolve_dod

            dod_resolved = resolve_dod(config, agent_meta_root)
            content = inject_pipeline_blocks(content, effective, provider, dod_resolved)

        content = substitute(content, merged_vars, rel_source, log)
        # Apply PAL delegation syntax per provider (Issue #277).
        # Must run BEFORE strip_inactive_conditional_blocks — its final cleanup
        # removes ALL {{#if}} markers, which would strip {{#if PAL_*}} blocks
        # before the engine can evaluate them per provider.
        from .delegation_syntax import DelegationSyntaxEngine
        pal_engine = DelegationSyntaxEngine(config_dir=agent_meta_root / "config")
        content = pal_engine.apply(content, provider, log=log)
        content = strip_inactive_conditional_blocks(content, variables)
        # Apply platform-config substitution ({{platform.*}} placeholders)
        if platform_vars is not None:
            content = substitute_platform(content, platform_vars, rel_source, log)

        name = Path(filename).stem
        layer = source_path.parts[-2]
        source_label = f'{layer}/{source_path.name}'
        generated_from = f'{source_label}@{source_version}' if source_version else source_label

        content = transform_agent_content_for_provider(
            content=content,
            provider=provider,
            role=role,
            name=name,
            description=description,
            generated_from=generated_from,
            config=config,
            agent_meta_root=agent_meta_root,
            project_root=project_root,
            target_path=target_path,
            provider_config=provider_config,
            log=log,
        )

        # MCP toolset: bind the servers this role opted into (issue #467).
        # Claude-only — `mcp__<server>__<tool>` is Claude Code's namespacing;
        # other providers surface MCP tools through their own config, not
        # through agent frontmatter.
        if provider == 'Claude':
            mcp_tools = resolve_mcp_tools_for_role(role, config, agent_meta_root, project_root)
            if mcp_tools:
                before = content
                content = append_frontmatter_tools(content, mcp_tools)
                if content != before:
                    servers = ', '.join(sorted({t.split('__')[1] for t in mcp_tools}))
                    log.note(str(target_path.relative_to(project_root)),
                             f'mcp tools: +{len(mcp_tools)} from {servers}')

        # Visualization: inject event-logging prompt block when dynamic/full mode is enabled
        # Applies to ALL providers — every generated agent gets the viz reporting block
        viz_cfg = config.get('viz', {})
        if viz_cfg.get('enabled', False) and viz_cfg.get('mode') in ('dynamic', 'full'):
            from .viz import inject_viz_prompt_block
            content = inject_viz_prompt_block(content, role, provider, viz_enabled=viz_cfg.get('enabled', False), agent_meta_root=agent_meta_root,
                                              viz_debug=viz_cfg.get("debug", False))

        if debug_mode:
            content = inject_debug_block(content, name)

        # Critical Rules Footer: append critical rules to end of agent files
        footer_cfg = config.get('critical-rules-footer', {})
        if footer_cfg.get('enabled', False):
            content = _extract_and_append_critical_footer(
                content, agent_meta_root, config, variables, log, provider
            )

        # Path-based Contextual Rules: inject rules based on path patterns
        path_rules_cfg = config.get('pathRules', [])
        if path_rules_cfg:
            content = apply_path_rules(
                content, agent_meta_root, config, variables, log, role
            )

        # XML Section Wrapping: wrap Markdown ## sections in XML tags
        xml_cfg = config.get('xml-section-wrapping', {})
        if xml_cfg.get('enabled', False):
            content = wrap_sections_in_xml(content)

        # Singleton-Constraint: inject guard block into all non-orchestrator agent files
        SINGLETON_CONSTRAINT_BLOCK = (
            "\n\n## Singleton-Regel: Orchestrator-Spawn (auto-generated)\n\n"
            "**NIEMALS** `task(subagent_type=\"orchestrator\", ...)` oder "
            "`Agent(subagent_type=\"orchestrator\", ...)` aufrufen.\n\n"
            "- Es existiert genau **EIN Orchestrator** pro Session — der vom `main_chat` gespawnte.\n"
            "- Mehrere Orchestrator-Instanzen verursachen Routing-Konflikte und Session-State-Korruption.\n"
            "- Bei unklarem Routing: Ergebnis an den Aufrufer zurückgeben, nicht weiter delegieren.\n\n"
            "> Durchgesetzt via `rules/1-generic/a2a-delegation-gates.md` Gate #5.\n"
        )
        # Only agents that can actually spawn sub-agents (Agent/Task tool) need
        # the singleton guard — injecting it into non-spawning agents is wasted context.
        if role != "orchestrator" and not role.endswith("-iteration") and _can_spawn:
            content = content.rstrip() + SINGLETON_CONSTRAINT_BLOCK

        rel_label = str(source_path.relative_to(agent_meta_root / AGENTS_DIR))
        rel_out = str(target_path.relative_to(project_root))
        allow_secrets = config.get("allow-committed-secrets", False) if config else False
        if write_checked(target_path, content, log, rel_label, config=config, dry_run=dry_run, allow_secrets=allow_secrets):
            log.action('WRITE', rel_out, rel_label)
        else:
            log.skip(rel_out, 'unchanged')

    # External skill filenames are always in .claude/agents/ (Claude only)
    if provider == 'Claude':
        ext_config = load_external_skills_config(agent_meta_root)
        project_skills = _normalize_enabled_config(config.get('external-skills', {}))
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
            if existing_file.name not in expected_filenames:  # noqa: SIM102
                if not managed_index.exists() or existing_file.name in previously_managed:
                    log.action('DELETE', str(existing_file.relative_to(project_root)),
                               'role removed from config')
                    if not dry_run:
                        existing_file.unlink()

        if not dry_run and expected_filenames:
            managed_index.write_text(
                '\n'.join(sorted(expected_filenames)) + '\n', encoding='utf-8'
            )

    # Provider Bootstrap: session-start agent registration for providers that
    # need it (Gemini: inject GEMINI.md instructions; Continue: update
    # .continue/config.yaml) — Issue #277, unified call site per #628: the
    # mechanism/action dispatch lives entirely in BootstrapEngine, no more
    # per-provider special-casing here.
    if provider in ("Gemini", "Continue"):
        from .bootstrap import BootstrapEngine
        bootstrap_engine = BootstrapEngine(config_dir=agent_meta_root / "config")
        result = bootstrap_engine.run_bootstrap(
            provider, target_dir, project_root,
            dry_run=dry_run, log=log,
            context_file=pc.get("context_file"),
            compact=variables.get("COMPACT_MODE") == "true",
            agents_label=pc.get("agents_dir", f".{provider.lower()}/agents"),
        )
        if provider == "Continue" and result.get("status") == "success":
            rel_target = str(target_dir.relative_to(project_root))
            log.note(rel_target, f"Continue config updated: {result.get('agent_count', 0)} agents")
