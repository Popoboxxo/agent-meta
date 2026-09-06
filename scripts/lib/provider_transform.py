"""Provider-specific agent transformations (Claude -> Gemini/Opencode/Continue).

Formatting layer of the agent pipeline (Issue #561 split of agents.py): tool
whitelisting/mapping, XML section wrapping, frontmatter rewriting per provider,
debug/bootstrap block injection and body slimming. Imports the neutral
frontmatter layer. Dispatch is data-driven since #629: per-provider behavior
comes from the ``agent-transform:`` block in config/ai-providers.yaml, applied
by ``_apply_agent_transform`` — there is no Python if/elif dispatch chain.
The viz prompt-block injector is not imported here at all: the lazy
``from .viz import inject_viz_prompt_block`` lives in
``agent_sync._finalize_agent_content`` (avoids a load-time cycle with viz.py).
"""
from __future__ import annotations

import re
from pathlib import Path

from .agent_toml import build_agent_toml_document
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

def _reassemble_body(content: str, body: str) -> str:
    """Replace the post-frontmatter body of `content` with `body`.

    Mirrors the `fm_end = content.find('\\n---', 3)` splice repeated across the
    legacy per-provider branches: if a frontmatter terminator exists, keep the
    frontmatter and swap the body; otherwise the whole document becomes the body.
    """
    fm_end = content.find('\n---', 3)
    if fm_end != -1:
        return content[:fm_end + 4] + '\n' + body.lstrip('\n')
    return body.lstrip('\n')

def _apply_agent_transform(
    content: str,
    spec: dict,
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
    strip_fields: list,
) -> str:
    """Apply a data-driven per-provider agent transform (issue #629).

    `spec` is the provider's `agent-transform:` block from
    config/ai-providers.yaml. It replaces the hand-written per-provider elif
    branch with declarative steps. `content` must already have had
    build_frontmatter() applied by the caller. Recognised spec keys:

      model: inject | native | skip   — inject a `model:` field, resolve for the
                                         native-frontmatter builder, or skip
      model-note-flat: bool           — model-source note also honours the
                                         flat model-overrides map (not just the
                                         per-provider sub-map)
      model-inherit-fallback: bool    — empty model falls back to role-defaults
                                         unless model-inherit-main-chat is active
      inject-memory: bool
      inject-permission-mode: bool
      extra-fields: {key: value}      — literal frontmatter updates
      tools: skip | keep | filter | remove
                                       — skip: leave untouched (stripped via
                                         strip-fields); keep: validate+warn only;
                                         filter: validate + replace with subset;
                                         remove: validate then drop the field
      strip-fields: [name, ...]       — frontmatter keys to remove
      strip-claude-lines: bool        — strip Claude-only body lines + reassemble
      body-note: gemini-registration  — inject the Gemini registration note
      body-sanitize-hr: bool          — replace body `^---$` lines with `___`
      frontmatter-mechanism: opencode-native
                                       — build opencode-native frontmatter instead
                                         of the inject/strip steps above
      frontmatter-mechanism: codex-toml
                                       — build a Codex-native TOML agent document
                                         (name/description/model/extra-fields +
                                         the body as developer_instructions)
                                         instead of Markdown+YAML frontmatter
    """
    from .roles import (
        load_roles_config,
        resolve_max_tokens,
        resolve_memory,
        resolve_model,
        resolve_permission_mode,
        resolve_steps,
        resolve_temperature,
    )
    rel = str(target_path.relative_to(project_root))

    def _model_note(model: str) -> None:
        po = config.get('model-overrides', {})
        is_override = role in po.get(provider, {})
        if spec.get('model-note-flat'):
            is_override = is_override or (
                role in po and not isinstance(po.get(role), dict)
            )
        src = 'project override' if is_override else 'meta default'
        log.note(rel, f'model: {model} (from {src})')

    # --- opencode-native frontmatter: distinct format, handled wholesale ---
    if spec.get('frontmatter-mechanism') == 'opencode-native':
        model = resolve_model(role, config, agent_meta_root,
                              provider=provider, provider_config=provider_config, log=log)
        if model:
            _model_note(model)
        temperature = resolve_temperature(role, config, agent_meta_root)
        if temperature:
            src = 'project override' if role in config.get('temperature-overrides', {}) else 'meta default'
            log.note(rel, f'temperature: {temperature} (from {src})')
        max_tokens = resolve_max_tokens(role, config, agent_meta_root)
        if max_tokens:
            mt_src = 'project override' if role in config.get('max-tokens-overrides', {}) else 'meta default'
            log.note(rel, f'max_tokens: {max_tokens} (from {mt_src})')
        steps = resolve_steps(role, config, agent_meta_root)
        if steps:
            src = 'project override' if role in config.get('steps-overrides', {}) else 'meta default'
            log.note(rel, f'steps: {steps} (from {src})')
        _fm = _parse_frontmatter_yaml(content)
        _raw_tools = _fm.get('tools')
        if isinstance(_raw_tools, list):
            _valid_tools = _validate_tools_against_whitelist(
                _raw_tools, provider, agent_meta_root, log, role,
            )
            content = _update_frontmatter_dict(content, {'tools': _valid_tools})
        return _transform_frontmatter_for_opencode(
            content, name, description, model, steps, generated_from, agent_meta_root, temperature,
            strip_fields=strip_fields,
        )

    # --- codex-toml document: native TOML agent file, handled wholesale ---
    # Codex agents are TOML files (.codex/agents/*.toml, auto-loaded by the
    # harness): the document is built from name/description/model plus the
    # extra-fields and the Markdown body as developer_instructions (the
    # required body field per the verified Codex agent schema). Sampling
    # fields (temperature/max_tokens/steps) are deliberately NOT resolved —
    # the Codex agent TOML has no such verified fields — and tools are not
    # validated either (the mechanism spec declares `tools: skip`: the
    # document format has no tools field).
    if spec.get('frontmatter-mechanism') == 'codex-toml':
        model = resolve_model(role, config, agent_meta_root,
                              provider=provider, provider_config=provider_config, log=log)
        if model:
            _model_note(model)
        _fm = _parse_frontmatter_yaml(content)
        body = _strip_frontmatter(content)
        if spec.get('strip-claude-lines'):
            body = _strip_claude_specific_lines(body)
        extra_fields = dict(spec.get('extra-fields') or {})
        return build_agent_toml_document(
            name=name, description=description, model=model or "",
            extra_fields=extra_fields, body=body,
            version=str(_fm.get("version")) if _fm.get("version") is not None else None,
            generated_from=generated_from or None,
        )

    # --- 1. model ---
    model_mode = spec.get('model', 'skip')
    if model_mode == 'inject':
        model = resolve_model(role, config, agent_meta_root,
                              provider=provider, provider_config=provider_config, log=log)
        if spec.get('model-inherit-fallback'):
            inherit_active = bool((config.get('model-inherit-main-chat') or {}).get(provider))
            if not model and not inherit_active:
                roles_cfg = load_roles_config(agent_meta_root)
                raw = roles_cfg["roles"].get(role, {}).get("model", "")
                if raw:
                    model = raw
        content = inject_model_field(content, model)
        if model:
            _model_note(model)

    # --- 2. memory ---
    if spec.get('inject-memory'):
        memory = resolve_memory(role, config, agent_meta_root)
        content = inject_memory_field(content, memory)
        if memory:
            src = 'project override' if role in config.get('memory-overrides', {}) else 'meta default'
            log.note(rel, f'memory: {memory} (from {src})')

    # --- 3. permissionMode ---
    if spec.get('inject-permission-mode'):
        permission_mode = resolve_permission_mode(role, config, agent_meta_root)
        content = inject_permission_mode_field(content, permission_mode)
        if permission_mode:
            src = 'project override' if role in config.get('permission-mode-overrides', {}) else 'meta default'
            log.note(rel, f'permissionMode: {permission_mode} (from {src})')

    # --- 4. literal frontmatter updates ---
    extra_fields = spec.get('extra-fields')
    if extra_fields:
        content = _update_frontmatter_dict(content, dict(extra_fields))

    # --- 5. tools ---
    tools_mode = spec.get('tools', 'skip')
    if tools_mode != 'skip':
        _fm = _parse_frontmatter_yaml(content)
        _tools = _fm.get('tools')
        if isinstance(_tools, list):
            _valid = _validate_tools_against_whitelist(
                _tools, provider, agent_meta_root, log, role,
            )
            if tools_mode == 'filter':
                content = _update_frontmatter_dict(content, {'tools': _valid})
        if tools_mode == 'remove':
            content = _remove_frontmatter_fields(content, ['tools'])

    # --- 6. strip frontmatter fields ---
    fields_to_strip = spec.get('strip-fields')
    if fields_to_strip:
        content = _remove_frontmatter_fields(content, list(fields_to_strip))

    # --- 7. body rewrite ---
    if spec.get('strip-claude-lines'):
        body = _strip_frontmatter(content)
        body = _strip_claude_specific_lines(body)
        if spec.get('body-sanitize-hr'):
            body = re.sub(r'(?m)^---$', '___', body)
        if spec.get('body-note') == 'gemini-registration':
            registration_note = (
                "> **Registrierung erforderlich:** Dieser Agent wird zur Laufzeit "
                "via `define_subagent` registriert — er ist NICHT automatisch aktiv. "
                f"Bootstrap-Instruktionen: `{provider_config.get(provider, {}).get('context_file', '.gemini/GEMINI.md')}` "
                "(Block `agent-meta:bootstrap`).\n"
            )
            fm_end = content.find('\n---', 3)
            if fm_end != -1:
                content = (content[:fm_end + 4] + '\n' + registration_note
                           + '\n' + body.lstrip('\n'))
        else:
            content = _reassemble_body(content, body)

    return content

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
    # Provider transform is fully data-driven (issue #629): the per-provider
    # `agent-transform:` block in config/ai-providers.yaml describes the
    # frontmatter/tool/body steps, applied by _apply_agent_transform(). This
    # replaced a 6-way `if provider == ...` elif chain — a new provider is
    # enabled by adding a YAML block, no Python change.
    _transform_spec = provider_config.get(provider, {}).get('agent-transform')
    content = build_frontmatter(content, name, description, generated_from=generated_from,
                                strip_fields=_strip_fields)
    if _transform_spec is None:
        # No spec for this provider. The pre-#629 elif chain silently did
        # nothing for an unlisted provider; warn instead so a newly-added
        # provider missing its agent-transform: block is visible in sync.log.
        log.warning(
            f"{provider}/{role}: no agent-transform block in config/ai-providers.yaml "
            f"— agent frontmatter left as generated (add an agent-transform: spec for {provider})",
        )
    else:
        content = _apply_agent_transform(
            content, _transform_spec, provider, role, name, description, generated_from,
            config, agent_meta_root, project_root, target_path, provider_config, log,
            _strip_fields,
        )

    return content

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
