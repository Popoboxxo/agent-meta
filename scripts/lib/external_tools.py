"""External dev-tool framework: registry loading, activation resolution and
rule generation for locally installed CLI tools (e.g. ``graphify``).

Structurally parallel to ``scripts/lib/mcp.py``, but deliberately simpler:
external CLI tools are machine-local, not platform-bound, so activation follows
the richer ``external-skills`` dict-with-enabled model (see
``scripts/lib/skills.py::_skill_is_active``) rather than the MCP platform-bundle
model. No connection blocks, no secrets, no provider-config injection — a tool
contributes only rule-content and a declarative list of hook wrappers that live
in ``hooks/0-external/``.

The registry loading and activation resolution live in the neutral
:mod:`lib.registry_query` core since Issue #478 (dependency inversion —
this module used to import the catalog core from :mod:`lib.plugins` while
``plugins`` lazily imported ``resolve_active_external_tools`` back, forming
a 3-cycle). This module keeps the *generation* machinery (rule content,
injection resolution, artifact writing) and re-exports the registry/
activation names for backward compatibility (sync.py, tests,
external_tools_drift).

Public interface:
    load_external_tools_registry(agent_meta_root, config, project_root)
        → dict of tool definitions (cli-tool slice of the plugin catalog)
          [re-exported from lib.registry_query]
    resolve_active_external_tools(config, agent_meta_root, project_root)
        → list of active tool names [re-exported from lib.registry_query]
    generate_external_tool_artifacts(...)
        → writes .claude/rules/tool-<name>.md for providers with has_rules
    scan_injection_drift(...) / render_injection_drift_artifacts(...)
        → thin re-exports of scripts/lib/external_tools_drift.py (split out
          to keep this module under the <=600-line convention; see that
          module's docstring)
"""
from __future__ import annotations

from pathlib import Path

from .io import safe_path, write_checked
from .log import SyncLog
from .registry_query import (  # noqa: F401 -- re-exported for API compat (Issue #478)
    _validate_permitted_injections,
    load_external_tools_registry,
    resolve_active_external_tools,
)
from .rule_index import bootstrap_previously_managed, cleanup_stale_managed_files, write_managed_index
from .rules import resolve_rules
from .skill_channel import (
    cleanup_stale_skill_channel_rules,
    provider_supports_skill_channel,
    write_skill_channel_managed_index,
    write_skill_channel_rule,
)

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
# Injection path resolution
# ---------------------------------------------------------------------------

_INJECTION_DIR_KEYS = {
    "skill": ("skills_dir", ".claude/skills"),
    "hook": ("hooks_dir", ".claude/hooks"),
    "rule": ("rules_dir", ".claude/rules"),
}


def resolve_injection_path(entry: dict, pc: dict, project_root: Path) -> Path:
    """Resolve one permitted-injections entry to an absolute path.

    kind in {skill, hook, rule}: <pc[<kind>s_dir]>/<name>
    kind in {config, other}: <project_root>/<path>, verbatim.
    """
    kind = entry["kind"]
    if kind in _INJECTION_DIR_KEYS:
        dir_key, default_dir = _INJECTION_DIR_KEYS[kind]
        # Null-valued dir keys (skills_dir: null in ai-providers.yaml) fall
        # back to the same default an absent key gets — project_root / None
        # would raise TypeError (found via the #192 weak-sharer test).
        base = project_root / (pc.get(dir_key) or default_dir)
        return (base / entry["name"]).resolve()
    return (project_root / entry["path"]).resolve()


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

    Three channels, selected purely by provider config keys (no provider-name
    branches):
      - has_rules providers: writes <rules_dir>/tool-<name>.md — or
        <skills_dir>/tool-<name>/SKILL.md when rules-presets.yaml flags rule
        stem 'tool-<name>' with channel: skill for a provider with native
        Skill support (scripts/lib/skill_channel.py PROVIDERS).
      - has_rules:false providers WITH skills_dir (#192 Phase 2
        embedded-rules channel): writes <skills_dir>/tool-<name>/SKILL.md for
        every tool the shared managed block no longer embeds (opts embed:
        false / channel: skill). No-op (block embeds as fallback) when no
        tools carry those flags.
      - has_rules:false providers WITHOUT skills_dir: no-op entirely — the
        managed block embeds the sections (content-loss protection).
    Warns when a tool declares a hook stem that has no matching
    hooks/0-external/<stem>.sh file. The hook wrapper .sh files themselves
    are deployed independently by sync_hooks() (all 0-external hooks are
    always copied; registration in settings.json stays opt-in per project).

    resolve_rules and the skill-channel helpers are imported at module top
    level (Issue #478): rules depends on registry_query, not on this module,
    so the former deferred import is no longer needed.
    """
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
    rule_options = resolve_rules(config, agent_meta_root)
    supports_skill_channel = provider_supports_skill_channel(provider, pc)
    skills_dir_rel = pc.get("skills_dir")
    skills_target_dir = (
        (project_root / skills_dir_rel) if (skills_dir_rel and supports_skill_channel) else None
    )
    all_tool_rule_stems = {f"{TOOL_RULE_PREFIX}{t}" for t in registry}
    now_managed_skill_rules: set[str] = set()

    # Issue #192 Phase 2 (selective rule embedding): providers WITHOUT a
    # native rules_dir but with a skills_dir receive the tool sections the
    # shared managed block no longer embeds (embed: false / channel: skill in
    # rules-presets.yaml) as separate SKILL.md files — same channel as mcp.py
    # and rules.py::sync_embedded_rule_files(). Config-key gating only.
    embedded_rules_channel_dir: Path | None = None
    if not pc.get("has_rules"):
        if not skills_dir_rel:
            # No rules_dir and no skills_dir: nothing can be rendered — the
            # managed block embeds these sections as fallback (content-loss
            # protection), so there is no file work here at all.
            return
        embedded_rules_channel_dir = project_root / skills_dir_rel
        if not dry_run:
            embedded_rules_channel_dir.mkdir(parents=True, exist_ok=True)

    effective_rules_dir = rules_dir or DEFAULT_RULES_DIR
    now_managed: set[str] = set()

    # --- Native rules_dir channel (has_rules providers, e.g. Claude) ---
    if pc.get("has_rules"):
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

    # --- #192 embedded-rules channel (has_rules:false + skills_dir) ---
    # Writes the tool sections the shared managed block no longer embeds as
    # <skills_dir>/tool-<name>/SKILL.md (FULL variant — lazy-loaded files are
    # not subject to embed-side compaction).
    if embedded_rules_channel_dir is not None:
        for tool_name in active_tools:
            tool_def = registry.get(tool_name)
            if not tool_def:
                continue
            if provider in tool_def.get("provider-skip", []):
                continue

            rule_stem = f"{TOOL_RULE_PREFIX}{tool_name}"
            opts = rule_options.get(rule_stem, {})
            if not (opts.get("embed") is False or opts.get("channel") == "skill"):
                # Preset says embed: the managed block renders the section —
                # nothing to write into the file channel.
                continue
            now_managed_skill_rules.add(rule_stem)
            write_skill_channel_rule(
                rule_stem,
                _generate_tool_rule_content(tool_name, tool_def, pc, project_root),
                opts, embedded_rules_channel_dir, project_root,
                log, dry_run, f"external-tools-registry/{tool_name}",
            )

    # Skill-channel stale-cleanup + managed-index merge — covers BOTH the
    # native skill channel (has_rules + PROVIDERS, e.g. Claude) and the #192
    # embedded-rules channel (has_rules:false + skills_dir, e.g. Opencode).
    # Universe-scoped to the tool-* stems so entries owned by other writers
    # of the same shared skills_dir index are never touched.
    effective_skill_dir = skills_target_dir or embedded_rules_channel_dir
    if effective_skill_dir is not None:
        cleanup_stale_skill_channel_rules(
            effective_skill_dir, project_root, all_tool_rule_stems, now_managed_skill_rules,
            log, dry_run, "external tool rule no longer routed to channel: skill",
        )
        write_skill_channel_managed_index(
            effective_skill_dir, now_managed_skill_rules, dry_run, universe=all_tool_rule_stems
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
