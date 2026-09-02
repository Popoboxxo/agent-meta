"""Provider-specific agent transformations (Claude -> Gemini/Opencode/Continue).

Formatting layer of the agent pipeline (Issue #561 split of agents.py): tool
whitelisting/mapping, XML section wrapping, frontmatter rewriting per provider,
debug/bootstrap block injection and body slimming. Imports the neutral
frontmatter layer; the viz prompt-block injector is imported lazily inside
transform_agent_content_for_provider to avoid a load-time cycle with viz.py.
"""
from __future__ import annotations

import re
from pathlib import Path

from .frontmatter import (
    _parse_frontmatter_yaml,
    _remove_frontmatter_fields,
    _strip_frontmatter,
    _update_frontmatter_dict,
    build_frontmatter,
    inject_memory_field,
    inject_model_field,
    inject_permission_mode_field,
    load_provider_tools_config,
)
from .log import SyncLog

def _validate_tools_against_whitelist(
    tools: list, provider: str, agent_meta_root: Path, log: SyncLog, role: str,
) -> list:
    """Validate tool names against provider whitelist.

    Returns filtered list of valid tools.
    Logs WARNING for unknown tools (does NOT abort). Tools listed under
    '<provider>-silent' are known-unsupported by design and dropped as INFO.
    """
    config = load_provider_tools_config(agent_meta_root)
    whitelist = config.get(provider.lower(), [])
    if not whitelist:
        # No whitelist configured — allow all tools (backward compat)
        return tools
    silent = config.get(f"{provider.lower()}-silent", []) or []

    def matches(t: str, patterns: list) -> bool:
        return any(
            w.endswith("*") and t.startswith(w[:-1]) or w == t
            for w in patterns
        )

    valid: list = []
    for t in tools:
        if not isinstance(t, str):
            continue
        if matches(t, whitelist):
            valid.append(t)
        elif matches(t, silent):
            log.note(
                f"{provider}/{role}",
                f"tool '{t}' not supported by {provider} — dropped by design",
            )
        else:
            log.warning(
                f"{provider}/{role}: tool '{t}' not supported by {provider} — skipping (see config/provider-tools.yaml)",
            )
    return valid

def wrap_sections_in_xml(content: str) -> str:
    """Wrap Markdown heading sections in XML tags.

    Transforms:
        ## Section Name
        content...
        ## Next Section

    Into:
        <section name="section-name">
        ## Section Name
        content...
        </section>
        <section name="next-section">
        ## Next Section
        ...
        </section>

    Only processes ## level headings (not # title or ### sub-sections).
    The XML tag name is derived from the heading: lowercase, spaces->hyphens,
    special chars removed.
    """
    lines = content.splitlines(keepends=True)
    if not lines:
        return content

    result = []
    current_section = None
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip('\n').rstrip('\r')

        # Detect ## level heading (exactly ##, not ### or higher)
        if stripped.startswith('## ') and not stripped.startswith('###'):
            # Close previous section if open
            if current_section is not None:
                result.append('</section>\n')

            # Derive XML-safe tag name from heading
            heading_text = stripped[3:].strip()  # Remove '## '
            tag_name = _make_xml_tag_name(heading_text)
            current_section = tag_name

            # Open new section
            result.append(f'<section name="{tag_name}">\n')
            result.append(line)
        else:
            result.append(line)

        i += 1

    # Close last section
    if current_section is not None:
        result.append('</section>\n')

    return ''.join(result)

def _make_xml_tag_name(heading: str) -> str:
    """Convert a Markdown heading to an XML-safe tag name.

    Rules: lowercase, spaces->hyphens, remove special chars,
    collapse multiple hyphens, strip leading/trailing hyphens.
    """
    name = heading.lower()
    name = name.replace(' ', '-')
    name = re.sub(r'[^a-z0-9-]', '', name)
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    return name

def transform_agent_content_for_provider(
    content: str,
    provider: str,
    role: str,
    name: str,
    description: str,
    generated_from: str,
    config: dict,
    agent_meta_root: Path,
    project_root: Path,
    target_path: Path,
    provider_config: dict,
    log: SyncLog,
) -> str:
    from .roles import (        load_roles_config,        resolve_max_tokens,        resolve_memory,        resolve_model,        resolve_permission_mode,        resolve_steps,        resolve_temperature,    )
    # Opt-in per-provider frontmatter field stripping (issue #505): a
    # provider/validation layer with a strict agent-definition schema can
    # reject agent-meta's own bookkeeping fields (version/prompt_mode/
    # generated-from) as unknown extra inputs. Empty by default for every
    # shipped provider — fully backward compatible. A project opts in via
    # the existing project-level `provider-options` block (same mechanism
    # Continue's generate-prompts/prompt-mode already use, see
    # providers.py::resolve_provider_options()) — no core agent-meta change
    # needed per consumer provider quirk. `ai-providers.yaml` itself can
    # also set `frontmatter_strip_fields` as a provider-wide default.
    _strip_fields = (
        config.get('provider-options', {}).get(provider, {}).get('frontmatter-strip-fields')
        or provider_config.get(provider, {}).get('frontmatter_strip_fields', [])
    )
    if provider == 'Continue':
        # Continue agents: preserve original frontmatter, inject model/memory, add alwaysApply
        content = build_frontmatter(content, name, description, generated_from=generated_from,
                                    strip_fields=_strip_fields)
        model = resolve_model(role, config, agent_meta_root,
                              provider=provider, provider_config=provider_config, log=log)
        # model-inherit-main-chat: resolve_model() deliberately returns "" so the
        # agent inherits the main-chat model. That intentional "" must NOT trigger
        # the role-defaults fallback below (Continue would then never inherit).
        # Normal empty cases (provider without tiers) still fall back unchanged.
        inherit_active = bool((config.get('model-inherit-main-chat') or {}).get(provider))
        if not model and not inherit_active:
            roles_cfg = load_roles_config(agent_meta_root)
            raw = roles_cfg["roles"].get(role, {}).get("model", "")
            if raw:
                model = raw
        content = inject_model_field(content, model)
        if model:
            po = config.get('model-overrides', {})
            is_override = (role in po.get('Continue', {})) or (
                role in po and not isinstance(po.get(role), dict)
            )
            src = 'project override' if is_override else 'meta default'
            log.note(str(target_path.relative_to(project_root)), f'model: {model} (from {src})')
        memory = resolve_memory(role, config, agent_meta_root)
        content = inject_memory_field(content, memory)
        if memory:
            src = 'project override' if role in config.get('memory-overrides', {}) else 'meta default'
            log.note(str(target_path.relative_to(project_root)), f'memory: {memory} (from {src})')
        permission_mode = resolve_permission_mode(role, config, agent_meta_root)
        content = inject_permission_mode_field(content, permission_mode)
        if permission_mode:
            src = 'project override' if role in config.get('permission-mode-overrides', {}) else 'meta default'
            log.note(str(target_path.relative_to(project_root)), f'permissionMode: {permission_mode} (from {src})')
        content = _update_frontmatter_dict(content, {"alwaysApply": False})
        # Continue has no frontmatter tools model — validate and remove template tools
        _continue_fm = _parse_frontmatter_yaml(content)
        _continue_tools = _continue_fm.get('tools')
        if isinstance(_continue_tools, list):
            _validate_tools_against_whitelist(
                _continue_tools, provider, agent_meta_root, log, role,
            )
        content = _remove_frontmatter_fields(content, ['tools'])
        body = _strip_frontmatter(content)
        body = _strip_claude_specific_lines(body)
        
        # Sanitize standalone --- in the body to avoid breaking Continue's YAML parsing
        import re as _re
        body = _re.sub(r'(?m)^---$', '___', body)
        
        fm_end = content.find('\n---', 3)
        if fm_end != -1:
            content = content[:fm_end + 4] + '\n' + body.lstrip('\n')
    else:
        content = build_frontmatter(content, name, description, generated_from=generated_from,
                                    strip_fields=_strip_fields)

        if provider == 'Claude':
            model = resolve_model(role, config, agent_meta_root,
                                  provider=provider, provider_config=provider_config, log=log)
            content = inject_model_field(content, model)
            if model:
                po = config.get('model-overrides', {})
                is_override = (role in po.get('Claude', {})) or (
                    role in po and not isinstance(po.get(role), dict)
                )
                src = 'project override' if is_override else 'meta default'
                log.note(str(target_path.relative_to(project_root)), f'model: {model} (from {src})')

            memory = resolve_memory(role, config, agent_meta_root)
            content = inject_memory_field(content, memory)
            if memory:
                src = 'project override' if role in config.get('memory-overrides', {}) else 'meta default'
                log.note(str(target_path.relative_to(project_root)), f'memory: {memory} (from {src})')

            permission_mode = resolve_permission_mode(role, config, agent_meta_root)
            content = inject_permission_mode_field(content, permission_mode)
            if permission_mode:
                src = 'project override' if role in config.get('permission-mode-overrides', {}) else 'meta default'
                log.note(str(target_path.relative_to(project_root)), f'permissionMode: {permission_mode} (from {src})')

            # Validate tools against whitelist — log warnings but keep tools (Claude supports them natively)
            _claude_fm = _parse_frontmatter_yaml(content)
            _claude_tools = _claude_fm.get('tools')
            if isinstance(_claude_tools, list):
                _validate_tools_against_whitelist(
                    _claude_tools, provider, agent_meta_root, log, role,
                )

        elif provider == 'Gemini':
            # Gemini: provider-mapped model only; strip unsupported sampling
            # parameters (temperature, top_p, top_k, stop_sequences,
            # max_output_tokens) plus memory and permissionMode, then
            # strip Claude-specific lines.
            model = resolve_model(role, config, agent_meta_root,
                                  provider=provider, provider_config=provider_config, log=log)
            content = inject_model_field(content, model)
            if model:
                po = config.get('model-overrides', {})
                is_override = role in po.get('Gemini', {})
                src = 'project override' if is_override else 'meta default'
                log.note(str(target_path.relative_to(project_root)), f'model: {model} (from {src})')
            # Map generic tool names to Gemini-native tools
            _gemini_fm = _parse_frontmatter_yaml(content)
            _gemini_tools = _gemini_fm.get('tools')
            if isinstance(_gemini_tools, list):
                # Validate against provider whitelist first
                _gemini_valid_tools = _validate_tools_against_whitelist(
                    _gemini_tools, provider, agent_meta_root, log, role,
                )
                content = _update_frontmatter_dict(content, {'tools': _gemini_valid_tools})
            content = _remove_frontmatter_fields(
                content,
                [
                    'memory',
                    'permissionMode',
                    'temperature',
                    'top_p',
                    'top_k',
                    'stop_sequences',
                    'max_output_tokens',
                ]
            )
            body = _strip_frontmatter(content)
            body = _strip_claude_specific_lines(body)
            fm_end = content.find('\n---', 3)
            if fm_end != -1:
                # Gemini agents are API-registered, not file-discovered —
                # without the session bootstrap this file has no effect.
                registration_note = (
                    "> **Registrierung erforderlich:** Dieser Agent wird zur Laufzeit "
                    "via `define_subagent` registriert — er ist NICHT automatisch aktiv. "
                    f"Bootstrap-Instruktionen: `{provider_config.get(provider, {}).get('context_file', '.gemini/GEMINI.md')}` "
                    "(Block `agent-meta:bootstrap`).\n"
                )
                content = (content[:fm_end + 4] + '\n' + registration_note
                           + '\n' + body.lstrip('\n'))

        elif provider == 'Opencode':
            # Opencode: native frontmatter (description + mode: subagent + model)
            # Model IDs use "provider/model-id" format (e.g. anthropic/claude-sonnet-4-6)
            model = resolve_model(role, config, agent_meta_root,
                                  provider=provider, provider_config=provider_config, log=log)
            if model:
                po = config.get('model-overrides', {})
                is_override = role in po.get('Opencode', {})
                src = 'project override' if is_override else 'meta default'
                log.note(str(target_path.relative_to(project_root)), f'model: {model} (from {src})')
            temperature = resolve_temperature(role, config, agent_meta_root)
            if temperature:
                src = 'project override' if role in config.get('temperature-overrides', {}) else 'meta default'
                log.note(str(target_path.relative_to(project_root)), f'temperature: {temperature} (from {src})')
            max_tokens = resolve_max_tokens(role, config, agent_meta_root)
            if max_tokens:
                mt_src = 'project override' if role in config.get('max-tokens-overrides', {}) else 'meta default'
                log.note(str(target_path.relative_to(project_root)), f'max_tokens: {max_tokens} (from {mt_src})')
            steps = resolve_steps(role, config, agent_meta_root)
            if steps:
                src = 'project override' if role in config.get('steps-overrides', {}) else 'meta default'
                log.note(str(target_path.relative_to(project_root)), f'steps: {steps} (from {src})')
            # Validate tools against provider whitelist before transformation
            _opencode_fm = _parse_frontmatter_yaml(content)
            _opencode_raw_tools = _opencode_fm.get('tools')
            if isinstance(_opencode_raw_tools, list):
                _opencode_valid_tools = _validate_tools_against_whitelist(
                    _opencode_raw_tools, provider, agent_meta_root, log, role,
                )
                # Replace tools with validated subset before transformation
                content = _update_frontmatter_dict(content, {'tools': _opencode_valid_tools})
            content = _transform_frontmatter_for_opencode(
                content, name, description, model, steps, generated_from, agent_meta_root, temperature,
                strip_fields=_strip_fields,
            )

        elif provider == 'Copilot':
            # Copilot: frontmatter without model/memory/permissionMode/tools
            # Uses IDE-configured models — no per-agent model field
            content = build_frontmatter(content, name, description, generated_from=generated_from,
                                        strip_fields=_strip_fields)
            content = _remove_frontmatter_fields(content, [
                'memory', 'permissionMode', 'temperature', 'top_p', 'top_k',
                'stop_sequences', 'max_output_tokens', 'tools',
            ])
            body = _strip_frontmatter(content)
            body = _strip_claude_specific_lines(body)
            fm_end = content.find('\n---', 3)
            if fm_end != -1:
                content = content[:fm_end + 4] + '\n' + body.lstrip('\n')
            else:
                content = body.lstrip('\n')

        elif provider == 'Mammouth':
            # Mammouth Code agent: supports model, permissionMode, and tools fields.
            content = build_frontmatter(content, name, description, generated_from=generated_from,
                                        strip_fields=_strip_fields)
            model = resolve_model(role, config, agent_meta_root,
                                  provider=provider, provider_config=provider_config, log=log)
            content = inject_model_field(content, model)
            if model:
                po = config.get('model-overrides', {})
                is_override = (role in po.get('Mammouth', {})) or (
                    role in po and not isinstance(po.get(role), dict)
                )
                src = 'project override' if is_override else 'meta default'
                log.note(str(target_path.relative_to(project_root)), f'model: {model} (from {src})')

            permission_mode = resolve_permission_mode(role, config, agent_meta_root)
            content = inject_permission_mode_field(content, permission_mode)
            if permission_mode:
                src = 'project override' if role in config.get('permission-mode-overrides', {}) else 'meta default'
                log.note(str(target_path.relative_to(project_root)), f'permissionMode: {permission_mode} (from {src})')

            _mammouth_fm = _parse_frontmatter_yaml(content)
            _mammouth_tools = _mammouth_fm.get('tools')
            if isinstance(_mammouth_tools, list):
                _validate_tools_against_whitelist(
                    _mammouth_tools, provider, agent_meta_root, log, role,
                )

            content = _remove_frontmatter_fields(content, [
                'memory', 'temperature', 'top_p', 'top_k',
                'stop_sequences', 'max_output_tokens',
            ])
            body = _strip_frontmatter(content)
            body = _strip_claude_specific_lines(body)
            fm_end = content.find('\n---', 3)
            if fm_end != -1:
                content = content[:fm_end + 4] + '\n' + body.lstrip('\n')
            else:
                content = body.lstrip('\n')

    # Visualization: inject event-logging prompt block when dynamic/full mode is enabled
    # Applies to ALL providers — every generated agent gets the viz reporting block
    viz_cfg = config.get('viz', {})
    if viz_cfg.get('enabled', False) and viz_cfg.get('mode') in ('dynamic', 'full'):
        from .viz import inject_viz_prompt_block
    return content

def _inject_gemini_bootstrap(
    provider: str,
    target_dir: Path,
    agent_meta_root: Path,
    project_root: Path,
    pc: dict[str, str],
    log: SyncLog,
    dry_run: bool,
    compact: bool = False,
    agents_label: str = ".gemini/agents",
) -> None:
    from .bootstrap import BootstrapEngine

    bootstrap_engine = BootstrapEngine(config_dir=agent_meta_root / "config")
    bootstrap_config = bootstrap_engine.get_bootstrap_config(provider)

    if bootstrap_config.get("action") != "inject-bootstrap-instructions":
        return

    bootstrap_instructions = bootstrap_engine.generate_gemini_bootstrap_instructions(
        target_dir, compact=compact, agents_label=agents_label
    )
    if not bootstrap_instructions:
        return

    context_file = pc.get("context_file", ".gemini/GEMINI.md")
    # Validate context_file does not escape project_root (path traversal guard)
    resolved = (project_root / context_file).resolve()
    if project_root.resolve() not in resolved.parents and resolved != project_root.resolve():
        log.warning(f"{context_file} path escapes project root — skipping bootstrap injection")
        return

    gemini_md_path = project_root / context_file
    if not gemini_md_path.exists():
        log.warning(f"{gemini_md_path.relative_to(project_root)!s} does not exist — cannot inject bootstrap instructions")
        return

    existing = gemini_md_path.read_text(encoding="utf-8")
    bootstrap_marker_begin = "<!-- agent-meta:bootstrap-begin -->"
    bootstrap_marker_end = "<!-- agent-meta:bootstrap-end -->"
    bootstrap_block = f"{bootstrap_marker_begin}\n{bootstrap_instructions}\n{bootstrap_marker_end}"

    if bootstrap_marker_begin in existing:
        pattern = re.compile(
            re.escape(bootstrap_marker_begin) + ".*?" + re.escape(bootstrap_marker_end),
            re.DOTALL,
        )
        new_content = pattern.sub(bootstrap_block, existing, count=1)
    else:
        new_content = existing.rstrip("\n") + "\n\n" + bootstrap_block + "\n"

    if new_content != existing:
        log.action("UPDATE", str(gemini_md_path.relative_to(project_root)), "bootstrap instructions")
        if not dry_run:
            gemini_md_path.write_text(new_content, encoding="utf-8")
    else:
        log.skip(str(gemini_md_path.relative_to(project_root)), "bootstrap instructions unchanged")

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

def _map_claude_tools_to_gemini_tools(tools: list) -> list[str]:
    """Map Claude Code tool names to Gemini native tool names.

    Gemini available tools: code_execution, google_search, url_context.
    File system tools (Read, Write, Edit, Glob, Grep) are automatically
    active in the Gemini sandbox and don't need explicit mapping.
    """
    mapping = {
        "Bash": "code_execution",
        "WebSearch": "google_search",
        "WebFetch": "url_context",
    }
    mapped: set[str] = set()
    for t in tools:
        if isinstance(t, str) and t in mapping:
            mapped.add(mapping[t])
    return sorted(mapped)

def _map_claude_tools_to_opencode_permissions(
    tools: list,
    deny_list: list[str] | None = None,
) -> dict[str, str]:
    """Map Claude Code tool names to opencode permission keys.

    opencode uses a permission-based model (tools frontmatter is deprecated).
    Each mapped key is set to 'allow'. Unknown tools are ignored.

    If deny_list is provided, those permissions are set to 'deny'
    when not explicitly allowed by the template tools.

    Known mappings:
      Bash -> bash
      Read -> read
      Write / Edit -> edit  (write/edit/apply_patch gated by edit permission)
      Glob -> glob
      Grep -> grep
      WebFetch -> webfetch
      WebSearch -> websearch
      Agent -> task          (subagent invocation via task tool)
      TodoWrite -> todowrite
    """
    mapping = {
        "Agent": "task",
        "TodoWrite": "todowrite",
        "Bash": "bash",
        "Read": "read",
        "Write": "edit",
        "Edit": "edit",
        "Glob": "glob",
        "Grep": "grep",
        "WebFetch": "webfetch",
        "WebSearch": "websearch",
    }
    perms: dict[str, str] = {}

    # Allow-mapping
    for t in tools:
        if isinstance(t, str) and t in mapping:
            perms[mapping[t]] = "allow"

    # Deny-mapping
    if deny_list:
        for tool_name in deny_list:
            if tool_name in mapping and mapping[tool_name] not in perms:
                perms[mapping[tool_name]] = "deny"

    return perms

def _transform_frontmatter_for_opencode(
    content: str,
    name: str,
    description: str,
    model: str,
    steps: str,
    generated_from: str,
    agent_meta_root: Path,
    temperature: str = "",
    strip_fields: list[str] | None = None,
) -> str:
    """Build opencode-native agent frontmatter.

    opencode frontmatter schema:
      name: <role>
      description: "..."
      mode: subagent
      model: provider/model-id (optional)
      steps: <int> (optional)
      permission:             (mapped from template frontmatter tools)
        <key>: allow

    strip_fields: frontmatter keys to omit for providers/validation layers
    with a strict schema that rejects agent-meta's own bookkeeping fields
    (issue #505 — a Console Go validator in front of this exact schema
    rejected `version`/`prompt_mode`/`generated-from` as unknown extra
    inputs; `prompt_mode` was previously never stripped at all, just
    implicitly inherited from the source template's frontmatter). Their
    pre-strip values are preserved in an `agent-meta-provenance` HTML
    comment so traceability/version-bump enforcement survives the strip.
    """
    body = _strip_frontmatter(content)
    body = _strip_claude_specific_lines(body)

    template_fm = _parse_frontmatter_yaml(content)
    strip_fields = strip_fields or []

    provenance_comment = None
    if strip_fields:
        preserved = {k: template_fm[k] for k in strip_fields if k in template_fm}
        if generated_from and "generated-from" in strip_fields:
            preserved["generated-from"] = generated_from
        if preserved:
            pairs = " ".join(f"{k}={v}" for k, v in preserved.items())
            provenance_comment = f"<!-- agent-meta-provenance: {pairs} -->"

    # Preserve original fields and add/update opencode-specific ones
    updates: dict = {
        "name": name,
        "description": description,
        "mode": template_fm.get("mode") or "subagent",
    }
    if template_fm.get("version") and "version" not in strip_fields:
        updates["version"] = template_fm.get("version")
    if generated_from and "generated-from" not in strip_fields:
        updates["generated-from"] = generated_from
    if model:
        updates["model"] = model
    if steps:
        updates["steps"] = steps
    if "steps" in template_fm:
        updates["steps"] = template_fm["steps"]
    if "maxSteps" in template_fm:
        updates["steps"] = template_fm["maxSteps"]

    # Map template tools to opencode permission block
    template_tools = template_fm.get("tools")
    if isinstance(template_tools, list) and template_tools:
        provider_tools_cfg = load_provider_tools_config(agent_meta_root)
        deny_list = provider_tools_cfg.get("opencode_deny_critical", [])
        perms = _map_claude_tools_to_opencode_permissions(
            template_tools, deny_list=deny_list
        )
        if perms:
            updates["permission"] = perms

    # Preserve temperature: template frontmatter takes precedence over role defaults
    if "temperature" in template_fm:
        updates["temperature"] = template_fm["temperature"]
    elif temperature:
        updates["temperature"] = float(temperature)

    # Preserve max_tokens: template frontmatter takes precedence over role defaults
    if "max_tokens" in template_fm:
        updates["max_tokens"] = template_fm["max_tokens"]

    removes = [
        "tools",
        "generated_from",
        "permissionMode",
        "alwaysApply",
        "top_p",
        "top_k",
        "stop_sequences",
        "max_output_tokens",
        "hint",
        "based-on",
        "based_on",
        "maxSteps",
        "memory",
    ]
    if strip_fields:
        removes.extend(strip_fields)

    content = _update_frontmatter_dict(content, updates, removes=removes)

    # Replace body with stripped version
    fm_end = content.find('\n---', 3)
    if fm_end != -1:
        new_body = body.lstrip('\n')
        if provenance_comment:
            new_body = f"{provenance_comment}\n{new_body}"
        content = content[:fm_end + 4] + '\n' + new_body

    return content

def _strip_claude_specific_lines(content: str) -> str:
    """Remove Claude Code-specific lines that are meaningless in other providers.

    Currently strips:
    - Extension-Hook lines: > **Extension:** Falls `.claude/3-project/...` existiert → ...
    - Read-Tool instructions referencing .claude/ paths
    """
    lines = content.splitlines(keepends=True)
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("> **Extension:**") and ".claude/3-project/" in stripped:
            continue
        out.append(line)
    return "".join(out)

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
