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
from .dispatch_depth import required_depth_int
from .frontmatter import (
    _parse_frontmatter_yaml,
    _quiet_field_set,
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
from .providers import (
    explicit_primary_role,
    resolve_frontmatter_strip_fields,
    resolve_provider_options,
)
from .repo_containment import TmpSinkError
from .tmp_paths import resolve_tmp_paths

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

_KNOWN_TIER_TOKENS = frozenset(
    {"nano", "fast", "balanced", "powerful", "max", "ultra"}
)


def _resolve_role_default_fallback(
    role: str,
    provider: str,
    agent_meta_root: Path,
    provider_config: dict | None,
) -> str:
    """Resolve a role's ``role-defaults`` model through the provider tier table.

    Inline counterpart of the ``model-inherit-fallback`` contract (D3): the
    ``role-defaults`` catalog stores abstract tiers (``balanced`` …). Such a
    token is looked up in the provider's ``ai-providers.yaml model-tiers`` and
    ``role``/``apply_model_format`` is applied **exactly once** via the public
    :func:`scripts.lib.roles.apply_model_format`. A still-unresolvable tier
    yields ``""`` so no raw tier token can ever be emitted; a concrete model ID
    passes through with the single ``model-format`` application.
    """
    from .roles import apply_model_format, load_roles_config

    roles_cfg = load_roles_config(agent_meta_root)
    raw = str((roles_cfg.get("roles", {}).get(role, {}) or {}).get("model", "") or "")
    if not raw:
        return ""
    if raw in _KNOWN_TIER_TOKENS:
        tiers = (provider_config or {}).get(provider, {}).get("model-tiers", {}) or {}
        resolved = str(tiers.get(raw, "") or "")
    else:
        resolved = raw
    if not resolved or resolved in _KNOWN_TIER_TOKENS:
        return ""
    return apply_model_format(resolved, provider_config, provider)


def _with_native_tools(tools: list, native: list | None) -> list:
    """Append a provider's declared native dispatch tools to a tool list.

    ``native`` is the ``native_agent_tools`` capability (e.g. Kimi
    ``[Agent, AgentSwarm]``). Order is preserved and duplicates are dropped; a
    non-list value is ignored. Used only for the dispatcher role (see the
    ``subagents-allowlist`` spec key in :func:`_apply_agent_transform`).
    """
    if not isinstance(native, list):
        return list(tools)
    out = list(tools)
    for t in native:
        if isinstance(t, str) and t not in out:
            out.append(t)
    return out


def _apply_tool_name_map(tools: list, tool_name_map: dict | None) -> list:
    """Translate Claude tool names to a provider vocabulary.

    The mapping is data (``agent-transform.tool-name-map``): a source name not
    present in the map passes through unchanged. Order and duplicates are
    preserved as declared in the template. A non-dict map is ignored.
    """
    if not isinstance(tool_name_map, dict):
        return list(tools)
    return [
        str(tool_name_map.get(t, t)) if isinstance(t, str) else t
        for t in tools
    ]

def _role_read_only(template_fm: dict) -> bool:
    """Whether a role declares no write capability in its template tools.

    Mirrors the doctor ``active_role_where: {tools_without: [Write, Edit]}``
    predicate (scripts/lib/doctor_predicates.py): a role is read-only when its
    template tool list contains neither ``Write`` nor ``Edit``; an empty or
    missing list also counts as read-only. A comma-separated tool string is
    accepted for parity with the doctor reader.
    """
    tools = (template_fm or {}).get('tools')
    if isinstance(tools, str):
        tools = [t.strip() for t in tools.split(',') if t.strip()]
    if tools is None:
        return True
    if not isinstance(tools, list):
        return False
    return not any(t in ('Write', 'Edit') for t in tools if isinstance(t, str))

def _effective_extra_fields(spec: dict, caps: dict, template_fm: dict) -> dict:
    """Resolve a transform's literal ``extra-fields`` for a role.

    A provider that enforces read-only access through a sandbox field declares
    the capability ``read_only_enforcement: sandbox`` (config/
    provider-capabilities.yaml) and the override map ``read-only-extra-fields``
    in its ``agent-transform`` spec. The override is merged over ``extra-fields``
    for a read-only role (see :func:`_role_read_only`); every other role keeps
    the default. Pure data — no provider-name branch.
    """
    fields = dict(spec.get('extra-fields') or {})
    read_only_fields = spec.get('read-only-extra-fields')
    if (
        caps.get('read_only_enforcement') == 'sandbox'
        and isinstance(read_only_fields, dict)
        and _role_read_only(template_fm)
    ):
        fields.update(read_only_fields)
    return fields

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

def _tmp_sink_edit_allow_paths(
    config: dict,
    project_root: Path | None,
    log: SyncLog,
) -> tuple[str, ...]:
    """Derive the primary edit-scope glob from the tmp-sink resolver (IC-10).

    The edit scope of a hook-less provider follows the configured sink instead
    of a shipped literal: ``TmpPaths.relative`` is the single source of truth
    (ADR-01), so a project with ``path: scratch/out`` gets
    ``scratch/out/**`` and never a stale ``.tmp/**``.

    A disabled sink contributes nothing; neither does an unresolvable sink
    configuration (the render must not crash mid-sync — fail-closed means the
    caller keeps only the static fallback or the scalar ``deny``).
    """
    if project_root is None or not isinstance(config, dict):
        return ()
    try:
        paths = resolve_tmp_paths(project_root, config)
    except TmpSinkError as exc:
        log.warning(
            f"opencode edit scope: tmp-sink not derivable ({exc}) - "
            "falling back to the static allow-list",
        )
        return ()
    if not paths.enabled:
        return ()
    relative = paths.relative.strip().strip("/")
    if not relative:
        return ()
    return (f"{relative}/**",)


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
    active_set=None,
    provider_capabilities: dict | None = None,
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
                                         resolved through the provider's
                                         model-tiers (never a raw tier token);
                                         skipped when model-inherit-main-chat
                                         is active
      inject-memory: bool
      inject-permission-mode: bool
      inject-subagent-depth: bool     — for the opencode-native mechanism, emit
                                        `subagent_depth: <required_depth>` (the
                                        capability value) so a spawned
                                        orchestrator keeps its dispatch tools
      extra-fields: {key: value}      — literal frontmatter updates
      tools-format: skip | keep | filter | remove | map
                                       — skip: leave untouched; keep: validate
                                         +warn only, the ORIGINAL list survives
                                         (out-of-whitelist tokens preserved)
                                         while tool-name-map still applies;
                                         filter: validate + replace with the
                                         whitelisted subset; remove: validate
                                         then drop the field; map: emit
                                         `{<name>: true}` object form (never a
                                         YAML list)
      tool-name-map: {claude: provider}
                                       — translate Claude tool names to the
                                         provider vocabulary; an unknown source
                                         name passes through unchanged
      rename-fields: {old: new}        — rename frontmatter keys (e.g. Kimi
                                         `hint` → `whenToUse`)
      subagents-allowlist: routable|roles
                                       — emit a `subagents:` allow-list of the
                                         active delegatable roles (from the shared
                                         ActiveSet) on the provider's primary
                                         role, and inject the provider's
                                         `native_agent_tools` capability; gated
                                         on the capability
                                         `subagent_allowlist_required`
      allowed-fields: [name, ...]      — frontmatter allow-list (validated by
                                         artifact_validate; Task-1)
      reject-fields: [name, ...]       — frontmatter deny-list (validated by
                                         artifact_validate; Task-1)
      tools: skip | keep | filter | remove
                                       — legacy alias; `tools-format` wins when
                                         both are present
      strip-fields: [name, ...]       — frontmatter keys to remove
      strip-claude-lines: bool        — strip Claude-only body lines + reassemble
      body-note: gemini-registration  — inject the Gemini registration note
      body-sanitize-hr: bool          — replace body `^---$` lines with `___`
      frontmatter-mechanism: opencode-native
                                       — build opencode-native frontmatter instead
                                         of the inject/strip steps above; the
                                         explicit `primary-role` is emitted as
                                         `mode: primary` (no `mode` otherwise)
      frontmatter-mechanism: opencode-native-v2
                                       — as opencode-native, except every role
                                         without the `primary-role` value is
                                         pinned to `mode: subagent`
      frontmatter-mechanism: codex-toml
                                       — build a Codex-native TOML agent document
                                         (name/description/model/extra-fields +
                                         the body as developer_instructions)
                                         instead of Markdown+YAML frontmatter

    Provider-level keys honoured here: `model-literal` (emit the literal
    verbatim, e.g. Antigravity `inherit`) and `primary-role` (the single
    `mode: primary` entry, on v1 and v2 alike; absent -> never primary, so a
    provider without the key, e.g. the Mammouth fork, stays byte-identical).
    """
    from .roles import (
        resolve_max_tokens,
        resolve_memory,
        resolve_model,
        resolve_permission_mode,
        resolve_steps,
        resolve_temperature,
    )
    rel = str(target_path.relative_to(project_root))
    # Capability entry for this provider (config/provider-capabilities.yaml),
    # read once here. The data-driven dispatch steps below consume it — never a
    # provider-name branch.
    _caps = (provider_capabilities or {}).get(provider) or {}

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
    mechanism = spec.get('frontmatter-mechanism')
    if mechanism in ('opencode-native', 'opencode-native-v2'):
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
        # Entry point (#1006, OQ-8 amendment A2): only an EXPLICIT `primary-role`
        # yields `mode: primary`, on v1 and v2 alike; there is no code default.
        mode = None
        primary_role = explicit_primary_role(provider_config, provider)
        if primary_role is not None and role == primary_role:
            mode = 'primary'
        elif mechanism == 'opencode-native-v2':
            mode = 'subagent'
        # Data-driven dispatch depth (spec key `inject-subagent-depth`): emit the
        # capability `required_depth` as the frontmatter `subagent_depth` so a
        # spawned orchestrator keeps its dispatch tools (study 3.4: no depth
        # emitted -> default 1). Gated on the spec key + a positive capability
        # value — never a provider-name branch; providers without the key (e.g.
        # Opencode) stay byte-identical.
        subagent_depth = None
        if spec.get('inject-subagent-depth'):
            subagent_depth = required_depth_int(_caps)
        # Write-scope lock (#1006, IC-3/ADR-5): the primary entry must not keep
        # a write-anywhere permission while the runtime gate is active — a
        # primary agent that can write anywhere defeats the Main-Chat gate.
        # The gate decision has one source of truth (`lib/isolation`), imported
        # lazily here to avoid a load-time cycle.
        # SPEC-OPENCODE-V2-SUPPORT Amendment B3 (AC-C14 applies to the agent
        # level too): the AGENT level must use the SAME predicate as the v2
        # config triples — `permission_deny_required`, i.e. tier `permission`
        # OR tier `plugin` while the baked plugin only observes. The frozen
        # `opencode_runtime_gate_wanted` (tier `permission` only) stays
        # untouched for the Spec-A writer; it would leave `edit: allow` in
        # place on tier `plugin` + `observe`, and that agent-level allow is
        # appended last, overruling the global deny (last match wins).
        # `capabilities` and `plugin_mode` are resolved HERE (Amendment
        # B3-Folge): the transform itself never loads them. Without an
        # effective strict gate no deny is emitted (AC-C16 b).
        # Known boundary: the lock keys off the DERIVED `mode` above. A project
        # override template that declares `mode: primary` for a role the
        # registry does not name as `primary-role` inherits the template value
        # further down (`mode or template_fm["mode"]`) but is NOT locked here.
        deny_edit = False
        edit_allow_paths: tuple[str, ...] = ()
        if mode == 'primary':
            from . import isolation
            from . import providers as providers_lib
            from . import runtime_gate
            from .consistency.orchestrator_strict import _resolve_effective_strict

            capabilities = provider_capabilities
            if capabilities is None:
                try:
                    capabilities = providers_lib.load_provider_capabilities(
                        agent_meta_root,
                    )
                except Exception:  # noqa: BLE001 - unreadable registry degrades
                    capabilities = {}
            orch = config.get('orchestrator', {}) if isinstance(config, dict) else {}
            # D2b: pass the framework root so the version-driven grace for the
            # IMPLICIT strict default applies here too — the agent-level deny
            # must never run ahead of the gate it mirrors.
            deny_edit = _resolve_effective_strict(orch, provider, agent_meta_root) and (
                isolation.permission_deny_required(
                    # One resolved provider entry (registry or single entry).
                    isolation._v2_provider_entry(provider_config, provider),
                    isolation._capabilities_for(capabilities, provider),
                    runtime_gate._baked_plugin_mode(),
                )
            )
            if deny_edit:
                allow_cfg = load_provider_tools_config(agent_meta_root).get(
                    'opencode_primary_edit_allow',
                )
                if isinstance(allow_cfg, list):
                    static_paths = tuple(
                        p for p in allow_cfg if isinstance(p, str) and p
                    )
                    # IC-10: the sink glob comes from the single resolver, the
                    # static list is only the context-free fallback. An
                    # explicitly empty list stays the documented opt-out
                    # (ADR-5 option A -> scalar `edit: deny`).
                    if static_paths:
                        edit_allow_paths = tuple(dict.fromkeys(
                            _tmp_sink_edit_allow_paths(config, project_root, log)
                            + static_paths
                        ))
        # Data-driven branch (SPEC 3.7): only the resolved v2 mechanism gets the
        # native v2 builder. `opencode-native` (v1 and providers without a
        # surface mechanism, e.g. the Mammouth fork) keeps the frozen v1 path.
        if mechanism == 'opencode-native-v2':
            return _transform_frontmatter_for_opencode_v2(
                content, name, description, model, steps, generated_from,
                agent_meta_root, temperature,
                strip_fields=strip_fields, mode=mode,
                variant=_resolve_v2_model_variant(config, provider, role),
                deny_edit=deny_edit, edit_allow_paths=edit_allow_paths,
            )
        return _transform_frontmatter_for_opencode(
            content, name, description, model, steps, generated_from, agent_meta_root, temperature,
            strip_fields=strip_fields, mode=mode, subagent_depth=subagent_depth,
            deny_edit=deny_edit, edit_allow_paths=edit_allow_paths,
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
        # IC-15 Nr. 21: a provider whose capability is
        # `read_only_enforcement: sandbox` maps read-only roles (template tools
        # without Write/Edit) to the read-only sandbox value declared under
        # `read-only-extra-fields` — a plain data lookup, never a provider name.
        extra_fields = _effective_extra_fields(spec, _caps, _fm)
        return build_agent_toml_document(
            name=name, description=description, model=model or "",
            extra_fields=extra_fields, body=body,
            version=str(_fm.get("version")) if _fm.get("version") is not None else None,
            generated_from=generated_from or None,
        )

    # --- 1. model ---
    model_mode = spec.get('model', 'skip')
    if model_mode == 'inject':
        model_literal = (provider_config.get(provider) or {}).get('model-literal')
        if model_literal:
            model = str(model_literal)
        else:
            model = resolve_model(role, config, agent_meta_root,
                                  provider=provider, provider_config=provider_config, log=log)
        if not model and spec.get('model-inherit-fallback'):
            inherit_active = bool((config.get('model-inherit-main-chat') or {}).get(provider))
            if not inherit_active:
                # Resolve the role-default through the provider's model-tiers and
                # apply model-format exactly once. An unresolvable tier yields ""
                # so a raw tier token is never written (AC-12/D3).
                model = _resolve_role_default_fallback(
                    role, provider, agent_meta_root, provider_config,
                )
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
    if spec.get('extra-fields') or spec.get('read-only-extra-fields'):
        # The read-only override (IC-15 Nr. 21) is resolved from the capability
        # `read_only_enforcement: sandbox` + the `read-only-extra-fields` map;
        # see _effective_extra_fields.
        extra_fields = _effective_extra_fields(
            spec, _caps, _parse_frontmatter_yaml(content),
        )
        if extra_fields:
            content = _update_frontmatter_dict(content, extra_fields)

    # --- 4b. frontmatter key renames (data: rename-fields) ---
    rename_fields = spec.get('rename-fields')
    if isinstance(rename_fields, dict) and rename_fields:
        _fm = _parse_frontmatter_yaml(content)
        _ren_updates: dict = {}
        _ren_removes: list = []
        for _old, _new in rename_fields.items():
            if _old in _fm:
                _ren_updates[str(_new)] = _fm[_old]
                _ren_removes.append(str(_old))
        if _ren_updates:
            content = _update_frontmatter_dict(content, _ren_updates, removes=_ren_removes)

    # --- 4c. subagent allowlist (data: subagents-allowlist) ---
    # A provider that requires an explicit `subagents:` allow-list on its
    # dispatcher (capability `subagent_allowlist_required`, e.g. Kimi) declares
    # the source (`routable` / `roles`) in its agent-transform spec. The roles
    # come from the shared ActiveSet (never re-resolved here); the native
    # dispatch tools come from the `native_agent_tools` capability. Both are
    # gated on the spec key + capability — no provider-name branch.
    _primary_role = (provider_config.get(provider) or {}).get('primary-role', 'orchestrator')
    _dispatch_source = spec.get('subagents-allowlist')
    _emit_dispatch = (
        bool(_dispatch_source)
        and role == _primary_role
        and active_set is not None
        and _caps.get('subagent_allowlist_required') is True
    )
    if _emit_dispatch:
        _pool = active_set.routable if str(_dispatch_source) == 'routable' else active_set.roles
        content = _update_frontmatter_dict(
            content, {'subagents': sorted(set(_pool) - {role})})

    # --- 5. tools ---
    tools_format = spec.get('tools-format')
    tools_mode = tools_format if tools_format is not None else spec.get('tools', 'skip')
    if tools_mode != 'skip':
        _fm = _parse_frontmatter_yaml(content)
        _tools = _fm.get('tools')
        if isinstance(_tools, list):
            _valid = _validate_tools_against_whitelist(
                _tools, provider, agent_meta_root, log, role,
            )
            if tools_mode == 'keep':
                # keep: preserve the ORIGINAL list (out-of-whitelist tokens
                # survive) — validation above only emits warnings — while the
                # tool-name-map is still applied to every declared token.
                _mapped = _apply_tool_name_map(_tools, spec.get('tool-name-map'))
                if _emit_dispatch:
                    _mapped = _with_native_tools(_mapped, _caps.get('native_agent_tools'))
                if _mapped != _tools:
                    content = _update_frontmatter_dict(content, {'tools': _mapped})
            elif tools_mode == 'filter':
                # filter: the ONLY mode that replaces the list with the
                # whitelisted subset (then translated to provider vocabulary).
                _mapped = _apply_tool_name_map(_valid, spec.get('tool-name-map'))
                if _emit_dispatch:
                    _mapped = _with_native_tools(_mapped, _caps.get('native_agent_tools'))
                if _mapped != _tools:
                    content = _update_frontmatter_dict(content, {'tools': _mapped})
            elif tools_mode == 'map':
                _mapped = _apply_tool_name_map(_valid, spec.get('tool-name-map'))
                content = _update_frontmatter_dict(
                    content, {'tools': {name: True for name in _mapped}},
                )
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
    active_set=None,
    provider_capabilities: dict | None = None,
) -> str:
    # Provider-agnostic frontmatter strip policy (SPEC-REFERENCE-STANDARDS-2026-09-15,
    # IC-03): the resolver unions the global defaults (`reference_standards`),
    # the project channel (`provider-options.<P>.frontmatter-strip-fields`) and
    # the ai-providers channel (`frontmatter_strip_fields`), then subtracts the
    # keep channels (`frontmatter-keep-fields` / `frontmatter_keep_fields`) —
    # keep wins. One code path for every provider, no provider-name branch.
    _strip_fields = resolve_frontmatter_strip_fields(provider, config, provider_config)
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
            active_set=active_set,
            provider_capabilities=provider_capabilities,
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

# v2 permission actions, in the order the emitted ``permissions[]`` list keeps
# (SPEC-OPENCODE-V2-SUPPORT-2026-10-22, 3.7 / AC-D1).
_V2_PERMISSION_ACTIONS = ("edit", "shell", "subagent")

# Claude tool -> v2 action. Tools without a v2 counterpart (Read, Glob, Grep,
# WebFetch, WebSearch, TodoWrite) carry no permission action in v2 and are
# dropped; the closed-world builder below still emits a ``deny`` for their
# action bucket.
_V2_CLAUDE_TOOL_ACTIONS = {
    "Write": "edit",
    "Edit": "edit",
    "Bash": "shell",
    "Agent": "subagent",
}

def map_tools_to_opencode_v2_permissions(
    tools: list,
    deny_list: list[str] | None = None,
) -> list[dict[str, str]]:
    """Map Claude Code tool names to a closed-world opencode v2 permission list.

    v2 replaces the v1 ``permission:`` map with an ordered ``permissions[]``
    list of ``{action, resource, effect}`` entries. Mapping:

      Write / Edit -> edit
      Bash         -> shell
      Agent        -> subagent

    Every other Claude tool has no v2 permission counterpart and is dropped.
    The result is CLOSED-WORLD: exactly one entry per action in the fixed order
    ``edit``, ``shell``, ``subagent`` — ``allow`` when the template tools map
    to that action, ``deny`` otherwise. A read-only role therefore gets
    ``edit: deny`` instead of silently inheriting write rights.

    ``deny_list`` (``opencode_deny_critical``) is accepted for signature parity
    with the v1 mapper and deliberately has no effect: the v2 surface is closed
    by construction, so there is nothing left for a deny list to close.
    """
    allowed = {
        _V2_CLAUDE_TOOL_ACTIONS[tool]
        for tool in tools
        if isinstance(tool, str) and tool in _V2_CLAUDE_TOOL_ACTIONS
    }
    return [
        {
            "action": action,
            "resource": "*",
            "effect": "allow" if action in allowed else "deny",
        }
        for action in _V2_PERMISSION_ACTIONS
    ]

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
    quiet_fields: frozenset[str] | None = None,
    mode: str | None = None,
    subagent_depth: int | None = None,
    deny_edit: bool = False,
    edit_allow_paths: tuple[str, ...] = (),
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

    quiet_fields: stripped keys that must NOT be named in that provenance
    comment (IC-04, mirrored from `build_frontmatter`). ``None`` applies the
    default quiet set; a non-set value falls back to the loud path.

    deny_edit: closes the primary agent's write scope while the runtime gate is
    active (#1006, IC-3/ADR-5). Only an existing ``permission.edit == "allow"``
    is replaced — a role without ``Write``/``Edit`` already carries ``"deny"``
    from ``opencode_deny_critical`` and stays untouched, so a lock never widens
    a privilege. The replacement is the scalar ``"deny"`` when
    ``edit_allow_paths`` is empty (closed by default) and otherwise the mapping
    ``{"*": "deny", <path>: "allow", …}`` with ``"*"`` first (last match wins
    in Opencode). Key order of the remaining permissions is preserved and the
    default ``deny_edit=False`` renders byte-identically to before.
    """
    body = _strip_frontmatter(content)
    body = _strip_claude_specific_lines(body)

    template_fm = _parse_frontmatter_yaml(content)
    strip_fields = strip_fields or []

    provenance_comment = None
    if strip_fields:
        quiet = _quiet_field_set(quiet_fields)
        preserved = {
            k: template_fm[k]
            for k in strip_fields
            if k in template_fm and k not in quiet
        }
        if (
            generated_from
            and "generated-from" in strip_fields
            and "generated-from" not in quiet
        ):
            preserved["generated-from"] = generated_from
        if preserved:
            pairs = " ".join(f"{k}={v}" for k, v in preserved.items())
            provenance_comment = f"<!-- agent-meta-provenance: {pairs} -->"

    # Preserve original fields and add/update opencode-specific ones
    updates: dict = {
        "name": name,
        "description": description,
        "mode": mode or template_fm.get("mode") or "subagent",
    }
    if isinstance(subagent_depth, int) and not isinstance(subagent_depth, bool) and subagent_depth >= 1:
        updates["subagent_depth"] = subagent_depth
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
            if deny_edit and perms.get("edit") == "allow":
                # Copy before the in-place replacement: never mutate the
                # mapping handed to us (shared state / caller expectations).
                perms = dict(perms)
                paths = tuple(
                    p for p in edit_allow_paths if isinstance(p, str) and p
                )
                if paths:
                    scoped: dict[str, str] = {"*": "deny"}
                    for path in paths:
                        scoped.setdefault(path, "allow")
                    perms["edit"] = scoped
                else:
                    perms["edit"] = "deny"
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

# Frontmatter keys a v2 artifact never carries (SPEC 3.7 b/d/e). `permission`
# is the v1 map, `tools`/`maxSteps`/`subagent_depth` have no v2 counterpart and
# the sampling fields (temperature/max_tokens/top_p/...) are v1 legacy. `system`
# is deliberately absent: the Markdown body IS the system prompt (Spike Q5).
_V2_OPENCODE_REMOVE_FIELDS = (
    "tools",
    "permission",
    "maxSteps",
    "subagent_depth",
    "temperature",
    "max_tokens",
    "top_p",
    "top_k",
    "stop_sequences",
    "max_output_tokens",
    "system",
    "generated_from",
    "permissionMode",
    "alwaysApply",
    "hint",
    "based-on",
    "based_on",
    "memory",
)


def _opencode_provenance_comment(
    template_fm: dict,
    strip_fields: list,
    quiet_fields: frozenset[str] | None,
    generated_from: str,
) -> str | None:
    """Build the `agent-meta-provenance` comment for stripped fields.

    Shared by the opencode-native builders (v1 keeps its inline copy byte-frozen
    for the v1 Freeze, the v2 builder calls this helper instead of duplicating
    the logic). Same contract as `build_frontmatter`: only fields that exist in
    the source are preserved, `quiet_fields` are never named, and the
    `generated_from` value is preserved only when that key is being stripped.
    """
    if not strip_fields:
        return None
    quiet = _quiet_field_set(quiet_fields)
    preserved = {
        key: template_fm[key]
        for key in strip_fields
        if key in template_fm and key not in quiet
    }
    if (
        generated_from
        and "generated-from" in strip_fields
        and "generated-from" not in quiet
    ):
        preserved["generated-from"] = generated_from
    if not preserved:
        return None
    pairs = " ".join(f"{key}={value}" for key, value in preserved.items())
    return f"<!-- agent-meta-provenance: {pairs} -->"

def _resolve_v2_model_variant(
    config: dict,
    provider: str,
    role: str,
) -> str | None:
    """Resolve the v2 `#variant` suffix source for one role.

    Reads the project channel `provider-options.<provider>.model-variants[role]`
    (SPEC 3.1/3.7 c). Fail-safe, never raises: a non-dict map, an absent role or
    a non-string/empty value means "no variant" (the model ID stays unchanged).
    """
    options = resolve_provider_options(config, provider)
    if not isinstance(options, dict):
        return None
    variants = options.get("model-variants")
    if not isinstance(variants, dict):
        return None
    variant = variants.get(role)
    if isinstance(variant, str) and variant:
        return variant
    return None

def _v2_permissions_with_edit_deny(
    permissions: list[dict[str, str]],
    edit_allow_paths: tuple[str, ...],
) -> list[dict[str, str]]:
    """Close the primary `edit` action, keeping the configured path allows.

    Spec A IC-3 on the v2 list surface: the `edit: allow` entry becomes
    ``{action: edit, resource: "*", effect: deny}`` followed by one ``allow``
    entry per ``edit_allow_paths`` path. The ``*`` deny MUST come FIRST: last
    matching rule wins (Amendment B1 / Spike Q3 VERIFIED), so only this order
    lets the specific allows win. A role without ``Write``/``Edit`` already
    carries ``edit: deny`` and is returned unchanged — a lock never widens a
    privilege. All other action entries keep their order and effect.
    """
    paths: list[str] = []
    for path in edit_allow_paths:
        if isinstance(path, str) and path and path not in paths:
            paths.append(path)
    scoped: list[dict[str, str]] = []
    for entry in permissions:
        if entry.get("action") != "edit" or entry.get("effect") != "allow":
            scoped.append(entry)
            continue
        scoped.append({"action": "edit", "resource": "*", "effect": "deny"})
        scoped.extend(
            {"action": "edit", "resource": path, "effect": "allow"} for path in paths
        )
    return scoped


def _transform_frontmatter_for_opencode_v2(
    content: str,
    name: str,
    description: str,
    model: str,
    steps: str,
    generated_from: str,
    agent_meta_root: Path,
    temperature: str = "",
    strip_fields: list[str] | None = None,
    quiet_fields: frozenset[str] | None = None,
    mode: str | None = None,
    variant: str | None = None,
    deny_edit: bool = False,
    edit_allow_paths: tuple[str, ...] = (),
) -> str:
    """Build the native opencode **v2** agent frontmatter.

    Only reached through the `opencode-native-v2` frontmatter mechanism. It
    differs from the v1 builder (SPEC 3.7) in exactly these points:

    (a) `permissions:` (list of `{action, resource, effect}`) instead of the
        `permission:` map; the list is CLOSED-WORLD (one entry per action in
        `edit`, `shell`, `subagent`, `deny` for unmapped tools);
    (b) `steps` only — no `maxSteps` alias and no `temperature`/`max_tokens`/
        `top_p` legacy fields (the parameter `temperature` is accepted for
        signature parity and intentionally never emitted);
    (c) `model` carries a `#variant` suffix when the project configures
        `provider-options.<provider>.model-variants[<role>]`;
    (d) `tools` is never emitted;
    (e) `subagent_depth` is never emitted;
    (f) no separate `system:` field — the Markdown body is the system prompt.

    Provenance comment, strip-fields and body cleanup reuse the shared helpers
    instead of duplicating the v1 logic. `agent_meta_root` is accepted for
    signature parity with the v1 builder: the closed-world permission list needs
    no tool config (unmapped actions are denied, so no deny list is read).
    `deny_edit=True` closes the primary role's `edit` scope (Spec A IC-3, §3.4
    "Agent-Ebene"): the `edit` allow becomes a `*` deny followed by the
    `edit_allow_paths` allows, so the gate survives on the agent level too.
    """
    body = _strip_frontmatter(content)
    body = _strip_claude_specific_lines(body)

    template_fm = _parse_frontmatter_yaml(content)
    strip_fields = strip_fields or []
    provenance_comment = _opencode_provenance_comment(
        template_fm, strip_fields, quiet_fields, generated_from,
    )

    updates: dict = {
        "name": name,
        "description": description,
        "mode": mode or template_fm.get("mode") or "subagent",
    }
    if template_fm.get("version") and "version" not in strip_fields:
        updates["version"] = template_fm.get("version")
    if generated_from and "generated-from" not in strip_fields:
        updates["generated-from"] = generated_from
    if model:
        # `variant` is appended only to a resolved model ID and never doubles
        # an existing `#` suffix (the model may already carry one).
        updates["model"] = (
            f"{model}#{variant}"
            if variant and "#" not in model
            else model
        )
    if steps:
        updates["steps"] = steps
    if "steps" in template_fm:
        updates["steps"] = template_fm["steps"]
    if "maxSteps" in template_fm:
        updates["steps"] = template_fm["maxSteps"]

    template_tools = template_fm.get("tools")
    permissions = map_tools_to_opencode_v2_permissions(
        template_tools if isinstance(template_tools, list) else [],
    )
    if deny_edit:
        permissions = _v2_permissions_with_edit_deny(permissions, edit_allow_paths)
    updates["permissions"] = permissions

    removes = list(_V2_OPENCODE_REMOVE_FIELDS)
    if strip_fields:
        removes.extend(strip_fields)

    content = _update_frontmatter_dict(content, updates, removes=removes)

    # Replace body with stripped version (shared splice helper).
    new_body = body.lstrip('\n')
    if provenance_comment:
        new_body = f"{provenance_comment}\n{new_body}"
    return _reassemble_body(content, new_body)

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
