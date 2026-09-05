"""External dev-tool framework: registry loading, activation resolution and
rule generation for locally installed CLI tools (e.g. ``graphify``).

Structurally parallel to ``scripts/lib/mcp.py``, but deliberately simpler:
external CLI tools are machine-local, not platform-bound, so activation follows
the richer ``external-skills`` dict-with-enabled model (see
``scripts/lib/skills.py::_skill_is_active``) rather than the MCP platform-bundle
model. No connection blocks, no secrets, no provider-config injection — a tool
contributes only rule-content and a declarative list of hook wrappers that live
in ``hooks/0-external/``.

The tool definitions themselves are no longer read from a standalone
``config/external-tools-registry.yaml``; they are the ``cli-tool`` slice of the
unified plugin catalog (``config/plugin-catalog.yaml`` via :mod:`lib.plugins`),
filtered by kind here.

Public interface:
    load_external_tools_registry(agent_meta_root, config, project_root)
        → dict of tool definitions (cli-tool slice of the plugin catalog)
    resolve_active_external_tools(config, agent_meta_root, project_root)
        → list of active tool names
    generate_external_tool_artifacts(...)
        → writes .claude/rules/tool-<name>.md for providers with has_rules
    scan_injection_drift(...) / render_injection_drift_artifacts(...)
        → thin re-exports of scripts/lib/external_tools_drift.py (split out
          to keep this module under the <=600-line convention; see that
          module's docstring)
"""
from __future__ import annotations

from pathlib import Path

from .io import SyncError, _normalize_enabled_config, safe_path, write_checked
from .log import SyncLog
from .plugins import _activation_from_config, load_plugin_catalog, plugins_of_kind
from .rule_index import bootstrap_previously_managed, cleanup_stale_managed_files, write_managed_index

TOOL_RULE_PREFIX = "tool-"
EXTERNAL_HOOKS_DIR = "hooks/0-external"
# Fallback rules directory for providers without an explicit rules_dir (Claude).
# Mirrors mcp.DEFAULT_RULES_DIR to keep tool rule output aligned with sync_rules().
DEFAULT_RULES_DIR = ".claude/rules"
# Own managed-index filename for tool-*.md rule files — deliberately separate
# from rules.py's ".agent-meta-managed" and mcp.py's ".agent-meta-managed-mcp"
# so the three independent write loops never fight over the same index file.
TOOLS_MANAGED_INDEX_FILENAME = ".agent-meta-managed-tools"


# ---------------------------------------------------------------------------
# Registry loading
# ---------------------------------------------------------------------------

_INJECTION_KINDS_NAME = {"skill", "hook", "rule"}
_INJECTION_KINDS_PATH = {"config", "other"}


_INJECTION_DIR_KEYS = {
    "skill": ("skills_dir", ".claude/skills"),
    "hook": ("hooks_dir", ".claude/hooks"),
    "rule": ("rules_dir", ".claude/rules"),
}


def _validate_permitted_injections(tool_name: str, entries: list[dict]) -> None:
    """Validate a tool's ``permitted-injections`` list.

    kind in {skill, hook, rule} requires 'name' (provider-relative);
    kind in {config, other} requires an explicit 'path'. Mixing either
    field with the wrong kind group is a SyncError.
    """
    if not isinstance(entries, list):
        raise SyncError(
            f"external-tools-registry: '{tool_name}'.permitted-injections must be a list"
        )
    for entry in entries:
        if not isinstance(entry, dict):
            raise SyncError(
                f"external-tools-registry: '{tool_name}'.permitted-injections entries must be objects"
            )
        kind = entry.get("kind")
        if kind not in _INJECTION_KINDS_NAME | _INJECTION_KINDS_PATH:
            raise SyncError(
                f"external-tools-registry: '{tool_name}'.permitted-injections has invalid "
                f"kind '{kind}' (expected one of skill, hook, rule, config, other)"
            )
        if kind in _INJECTION_KINDS_NAME:
            if not entry.get("name"):
                raise SyncError(
                    f"external-tools-registry: '{tool_name}'.permitted-injections entry "
                    f"with kind '{kind}' requires 'name'"
                )
            if entry.get("path"):
                raise SyncError(
                    f"external-tools-registry: '{tool_name}'.permitted-injections entry "
                    f"with kind '{kind}' must not set 'path' (use 'name')"
                )
        else:
            if not entry.get("path"):
                raise SyncError(
                    f"external-tools-registry: '{tool_name}'.permitted-injections entry "
                    f"with kind '{kind}' requires 'path'"
                )
            if entry.get("name"):
                raise SyncError(
                    f"external-tools-registry: '{tool_name}'.permitted-injections entry "
                    f"with kind '{kind}' must not set 'name' (use 'path')"
                )


def resolve_injection_path(entry: dict, pc: dict, project_root: Path) -> Path:
    """Resolve one permitted-injections entry to an absolute path.

    kind in {skill, hook, rule}: <pc[<kind>s_dir]>/<name>
    kind in {config, other}: <project_root>/<path>, verbatim.
    """
    kind = entry["kind"]
    if kind in _INJECTION_DIR_KEYS:
        dir_key, default_dir = _INJECTION_DIR_KEYS[kind]
        base = project_root / pc.get(dir_key, default_dir)
        return (base / entry["name"]).resolve()
    return (project_root / entry["path"]).resolve()


def load_external_tools_registry(
    agent_meta_root: Path,
    config: dict | None = None,
    project_root: Path | None = None,
) -> dict:
    """Return the cli-tool slice of the unified plugin catalog.

    Loads config/plugin-catalog.yaml (with its own framework/project/inline
    deep-merge, see lib.plugins.load_plugin_catalog) and filters to the
    ``cli-tool`` kind, giving the same flat {tool_name: tool_def} shape the
    old config/external-tools-registry.yaml `external-tools` map had. Each
    returned tool's permitted-injections list is validated eagerly.
    """
    catalog = load_plugin_catalog(agent_meta_root=agent_meta_root, config=config, project_root=project_root)
    registry = plugins_of_kind(catalog, "cli-tool")

    for tool_name, tool_def in registry.items():
        if isinstance(tool_def, dict) and "permitted-injections" in tool_def:
            _validate_permitted_injections(tool_name, tool_def["permitted-injections"])

    return registry


# ---------------------------------------------------------------------------
# Activation resolution
# ---------------------------------------------------------------------------


def _tool_is_active(name: str, merged_def: dict, project_tools: dict) -> bool:
    """Return True if an external tool should be rendered for this project.

    Precedence (mirrors skills._skill_is_active):
      1. Explicit project setting: project_tools[name]['enabled'] (true OR
         false) always wins, independent of the registry default.
      2. Otherwise: merged_def['enabled-by-default'] (framework value, possibly
         replaced via an external-tools-registry project override).
      3. Fallback: False — external CLI tools are opt-in.
    """
    if name in project_tools and "enabled" in project_tools[name]:
        return bool(project_tools[name]["enabled"])
    if "enabled-by-default" in merged_def:
        return bool(merged_def["enabled-by-default"])
    return False


def resolve_active_external_tools(
    config: dict,
    agent_meta_root: Path,
    project_root: Path | None = None,
    registry: dict | None = None,
) -> list[str]:
    """Determine which external tools are active for this project.

    Returns tool names (registry order) for which _tool_is_active is True.
    Tools named in the project config but absent from the registry are skipped
    — without a registry definition there is no rule-content to render.

    registry: pass an already-loaded load_external_tools_registry() result to
    skip re-reading/re-parsing the plugin catalog when the caller has one on
    hand.
    """
    if registry is None:
        registry = load_external_tools_registry(agent_meta_root, config, project_root)
    if (config or {}).get("plugins") is not None:
        project_tools = _activation_from_config(config)
    else:
        project_tools = _normalize_enabled_config((config or {}).get("external-tools", {}))

    active: list[str] = []
    for name, tool_def in registry.items():
        if not isinstance(tool_def, dict):
            continue
        if _tool_is_active(name, tool_def, project_tools):
            active.append(name)
    return active


# ---------------------------------------------------------------------------
# Rule content generation
# ---------------------------------------------------------------------------

def _resolve_injection_rel(entry: dict, pcs: list[dict], project_root: Path) -> str:
    """Resolve one permitted-injections entry to a display path, or several.

    ``pcs`` normally holds a single provider config. When the target rule
    content is embedded once into a context_file shared by several providers
    (e.g. AGENTS.md for Opencode+Gemini, issue #638), it holds one config per
    shared provider instead, and every distinct resolved path is joined with
    " bzw. " -- so the rendered content is identical no matter which shared
    provider's sync run happens to build it (order-independent, no more
    infinite --check oscillation from a single-provider path).
    """
    rels: list[str] = []
    for pc in pcs:
        resolved = resolve_injection_path(entry, pc, project_root)
        rel = (
            str(resolved.relative_to(project_root.resolve()))
            if resolved.is_relative_to(project_root.resolve())
            else str(resolved)
        )
        if rel not in rels:
            rels.append(rel)
    return " bzw. ".join(rels)


def _generate_tool_rule_content(
    name: str, tool_def: dict, pc: dict, project_root: Path, compact: bool = False,
    shared_pcs: list[dict] | None = None,
) -> str:
    """Build Markdown rule content for one external tool from its registry def.

    compact=True reduces the section to title + purpose line + a single pointer
    naming the hook wrappers and permitted injections (issue #540 B8). The
    full rule-content body is reference prose that stays discoverable via the
    registry/skill artifacts; native artifacts keep the full variant.

    shared_pcs: pass the provider configs of every provider sharing the target
    context_file (see _resolve_injection_rel) instead of relying on ``pc``
    alone when this content is embedded into a shared file.
    """
    pcs = shared_pcs or [pc]
    desc = (tool_def.get("description") or name).strip()
    lines: list[str] = [f"# External Tool: {name}", "", f"> {desc}", "", "---", ""]

    if compact:
        hooks = tool_def.get("hooks", [])
        injections = tool_def.get("permitted-injections", [])
        pointers: list[str] = []
        if isinstance(hooks, list) and hooks:
            wrapped = ", ".join(f"`{EXTERNAL_HOOKS_DIR}/{stem}.sh`" for stem in hooks)
            pointers.append(f"Hook-Wrapper: {wrapped}")
        if isinstance(injections, list) and injections:
            inj_parts = [
                f"`{_resolve_injection_rel(entry, pcs, project_root)}` ({entry['kind']})"
                for entry in injections
            ]
            if inj_parts:
                pointers.append(f"Injektionen: {', '.join(inj_parts)}")
        lines.append("Details/Registrierung: `config/external-tools-registry.yaml`.")
        if pointers:
            lines.append(" · ".join(pointers))
        return "\n".join(lines) + "\n"

    body = (tool_def.get("rule-content") or "").strip()
    if body:
        lines += [body, ""]

    hooks = tool_def.get("hooks", [])
    if isinstance(hooks, list) and hooks:
        lines += ["## Hook-Wrapper", ""]
        lines += [f"- `{EXTERNAL_HOOKS_DIR}/{stem}.sh`" for stem in hooks]
        lines.append("")

    injections = tool_def.get("permitted-injections", [])
    if isinstance(injections, list) and injections:
        lines += ["## Erlaubte Injektionen", ""]
        for entry in injections:
            rel = _resolve_injection_rel(entry, pcs, project_root)
            desc_suffix = f" — {entry['description']}" if entry.get("description") else ""
            lines.append(f"- `{rel}` ({entry['kind']}){desc_suffix}")
        lines.append("")

    lines += [
        "---",
        "",
        "*Generiert von agent-meta aus `config/external-tools-registry.yaml` — "
        "nicht manuell bearbeiten.*",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Artifact generation — main entrypoint called by sync.py
# ---------------------------------------------------------------------------

def generate_external_tool_artifacts(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    provider_config: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    rules_dir: str | None = None,
) -> None:
    """Generate external-tool rule files for all active tools.

    For providers with has_rules: writes .claude/rules/tool-<name>.md for every
    active tool not skipped for this provider — or <skills_dir>/tool-<name>/
    SKILL.md instead when rules-presets.yaml flags rule stem 'tool-<name>'
    with channel: skill for a provider that supports it (see
    scripts/lib/skill_channel.py). Warns when a tool declares a hook stem
    that has no matching hooks/0-external/<stem>.sh file. The hook wrapper
    .sh files themselves are deployed independently by sync_hooks() (all
    0-external hooks are always copied; registration in settings.json stays
    opt-in per project).
    """
    from .rules import resolve_rules
    from .skill_channel import (
        cleanup_stale_skill_channel_rules,
        provider_supports_skill_channel,
        write_skill_channel_managed_index,
        write_skill_channel_rule,
    )

    registry = load_external_tools_registry(agent_meta_root, config, project_root)
    if not registry:
        return

    # No early return on an empty active_tools list here (unlike
    # load_external_tools_registry's empty-registry check above): the loops
    # below still need to run with zero entries so cleanup_stale_managed_files()
    # sees an empty now_managed set and removes every previously-generated
    # tool-*.md rule file — deactivating the last tool must not orphan its
    # rule file.
    active_tools = resolve_active_external_tools(config, agent_meta_root, project_root, registry=registry)

    # --- Missing-hook warnings (provider-independent) ---
    for tool_name in active_tools:
        tool_def = registry.get(tool_name, {})
        for stem in tool_def.get("hooks", []) or []:
            hook_src = agent_meta_root / EXTERNAL_HOOKS_DIR / f"{stem}.sh"
            if not hook_src.exists():
                log.warning(
                    f"external-tools: '{tool_name}' declares hook '{stem}' but "
                    f"{EXTERNAL_HOOKS_DIR}/{stem}.sh not found — the hook will "
                    "not be deployed. Add the wrapper script or remove the "
                    "declaration from config/external-tools-registry.yaml."
                )

    # --- Rule file generation (only for providers that use rule files) ---
    pc = provider_config.get(provider, {})
    if not pc.get("has_rules"):
        return

    rule_options = resolve_rules(config, agent_meta_root)
    supports_skill_channel = provider_supports_skill_channel(provider, pc)
    skills_dir_rel = pc.get("skills_dir")
    skills_target_dir = (
        (project_root / skills_dir_rel) if (skills_dir_rel and supports_skill_channel) else None
    )
    all_tool_rule_stems = {f"{TOOL_RULE_PREFIX}{t}" for t in registry}
    now_managed_skill_rules: set[str] = set()

    effective_rules_dir = rules_dir or DEFAULT_RULES_DIR
    target_dir = project_root / effective_rules_dir
    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    managed_index_path = target_dir / TOOLS_MANAGED_INDEX_FILENAME
    previously_managed = bootstrap_previously_managed(
        target_dir, managed_index_path, f"{TOOL_RULE_PREFIX}*.md",
        # "tool-*.md" isn't an exclusive namespace — see mcp.py's identical
        # comment on its own bootstrap call for why an unmarked glob match
        # is not safe to treat as previously managed.
        content_marker="config/external-tools-registry.yaml` — "
                        "nicht manuell bearbeiten",
    )
    now_managed: set[str] = set()

    for tool_name in active_tools:
        tool_def = registry.get(tool_name)
        if not tool_def:
            continue
        if provider in tool_def.get("provider-skip", []):
            continue

        rule_stem = f"{TOOL_RULE_PREFIX}{tool_name}"
        opts = rule_options.get(rule_stem, {})
        content = _generate_tool_rule_content(tool_name, tool_def, pc, project_root)
        src_label = f"external-tools-registry/{tool_name}"

        if opts.get("channel") == "skill" and skills_target_dir is not None:
            now_managed_skill_rules.add(rule_stem)
            write_skill_channel_rule(
                rule_stem, content, opts, skills_target_dir, project_root,
                log, dry_run, src_label,
            )
            continue

        filename = f"{rule_stem}.md"
        target_path = safe_path(target_dir, filename)
        rel_out = str(target_path.relative_to(project_root))
        now_managed.add(filename)

        if write_checked(target_path, content, log, src_label, config=config, dry_run=dry_run):
            log.action("WRITE", rel_out, src_label)
        else:
            log.skip(rel_out, "unchanged")

    # Remove stale tool-*.md rule files no longer covered by the current
    # active-tool list (tool deactivated in project.yaml or removed from
    # external-tools-registry.yaml).
    cleanup_stale_managed_files(
        target_dir, project_root, previously_managed, now_managed, log, dry_run,
        "external tool no longer active/registered",
    )
    write_managed_index(managed_index_path, now_managed, dry_run)

    if skills_target_dir is not None:
        cleanup_stale_skill_channel_rules(
            skills_target_dir, project_root, all_tool_rule_stems, now_managed_skill_rules,
            log, dry_run, "external tool rule no longer routed to channel: skill",
        )
        write_skill_channel_managed_index(
            skills_target_dir, now_managed_skill_rules, dry_run, universe=all_tool_rule_stems
        )


# ---------------------------------------------------------------------------
# Injection drift — thin re-exports (see external_tools_drift.py)
# ---------------------------------------------------------------------------
# Deferred imports (inside the function body, not at module top-level):
# external_tools_drift.py imports concrete registry/activation helpers from
# *this* module at its own top level, so a top-level import in the other
# direction here would be a circular import. Deferring until call-time avoids
# that while keeping both names importable from scripts.lib.external_tools
# for existing callers (sync.py, admin-server.py, tests).

def scan_injection_drift(*args, **kwargs):
    """Re-export of external_tools_drift.scan_injection_drift()."""
    from .external_tools_drift import scan_injection_drift as _impl
    return _impl(*args, **kwargs)


def render_injection_drift_artifacts(*args, **kwargs):
    """Re-export of external_tools_drift.render_injection_drift_artifacts()."""
    from .external_tools_drift import render_injection_drift_artifacts as _impl
    return _impl(*args, **kwargs)
