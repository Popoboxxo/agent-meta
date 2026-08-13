"""External dev-tool framework: registry loading, activation resolution and
rule generation for locally installed CLI tools (e.g. ``graphify``).

Structurally parallel to ``scripts/lib/mcp.py``, but deliberately simpler:
external CLI tools are machine-local, not platform-bound, so activation follows
the richer ``external-skills`` dict-with-enabled model (see
``scripts/lib/skills.py::_skill_is_active``) rather than the MCP platform-bundle
model. No connection blocks, no secrets, no provider-config injection — a tool
contributes only rule-content and a declarative list of hook wrappers that live
in ``hooks/0-external/``.

Public interface:
    load_external_tools_registry(agent_meta_root, config, project_root)
        → dict of tool definitions (3-source merge)
    resolve_active_external_tools(config, agent_meta_root, project_root)
        → list of active tool names
    generate_external_tool_artifacts(...)
        → writes .claude/rules/tool-<name>.md for providers with has_rules
"""
from __future__ import annotations

from pathlib import Path

from .io import SyncError, _load_yaml_or_json, safe_path, write_checked
from .log import SyncLog

EXTERNAL_TOOLS_REGISTRY_YAML = "config/external-tools-registry.yaml"
TOOL_RULE_PREFIX = "tool-"
EXTERNAL_HOOKS_DIR = "hooks/0-external"
# Fallback rules directory for providers without an explicit rules_dir (Claude).
# Mirrors mcp.DEFAULT_RULES_DIR to keep tool rule output aligned with sync_rules().
DEFAULT_RULES_DIR = ".claude/rules"


# ---------------------------------------------------------------------------
# Registry loading
# ---------------------------------------------------------------------------

def _deep_merge(dict1: dict, dict2: dict) -> dict:
    """Recursively merge dict2 into dict1 (mirrors mcp._deep_merge)."""
    for k, v in dict2.items():
        if isinstance(v, dict) and k in dict1 and isinstance(dict1[k], dict):
            _deep_merge(dict1[k], v)
        else:
            dict1[k] = v
    return dict1


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
    """Load config/external-tools-registry.yaml and deep-merge project overrides.

    Sources (later wins, deep-merged):
      1. Framework:  <agent_meta_root>/config/external-tools-registry.yaml
      2. Project:    <project_root>/.meta-config/external-tools-registry.yaml
      3. Inline:     config["external-tools-registry"] from project.yaml

    Returns a flat {tool_name: tool_def} dict.
    """
    data, _ = _load_yaml_or_json(agent_meta_root / EXTERNAL_TOOLS_REGISTRY_YAML)
    registry: dict = {}
    if data and isinstance(data, dict):
        registry = data.get("external-tools", {})
        if not isinstance(registry, dict):
            registry = {}

    if project_root:
        proj_data, _ = _load_yaml_or_json(
            project_root / ".meta-config" / "external-tools-registry.yaml"
        )
        if proj_data and isinstance(proj_data, dict):
            proj_tools = proj_data.get("external-tools", proj_data)
            if isinstance(proj_tools, dict):
                _deep_merge(registry, proj_tools)

    if config:
        inline_registry = config.get("external-tools-registry", {})
        if isinstance(inline_registry, dict):
            _deep_merge(registry, inline_registry)

    for tool_name, tool_def in registry.items():
        if isinstance(tool_def, dict) and "permitted-injections" in tool_def:
            _validate_permitted_injections(tool_name, tool_def["permitted-injections"])

    return registry


# ---------------------------------------------------------------------------
# Activation resolution
# ---------------------------------------------------------------------------

def _normalize_project_tools(raw) -> dict:
    """Normalize project external-tools config to dict format.

    Accepts both the flat list shorthand ['graphify'] (alias for
    {'graphify': {'enabled': True}}) and the canonical dict form
    {'graphify': {'enabled': True}}. Mirrors skills._normalize_project_skills.
    """
    if isinstance(raw, list):
        return {name: {"enabled": True} for name in raw}
    if isinstance(raw, dict):
        return raw
    return {}


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
) -> list[str]:
    """Determine which external tools are active for this project.

    Returns tool names (registry order) for which _tool_is_active is True.
    Tools named in the project config but absent from the registry are skipped
    — without a registry definition there is no rule-content to render.
    """
    registry = load_external_tools_registry(agent_meta_root, config, project_root)
    project_tools = _normalize_project_tools((config or {}).get("external-tools", {}))

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

def _generate_tool_rule_content(name: str, tool_def: dict, pc: dict, project_root: Path) -> str:
    """Build Markdown rule content for one external tool from its registry def."""
    lines: list[str] = []

    desc = (tool_def.get("description") or name).strip()
    lines += [f"# External Tool: {name}", "", f"> {desc}", "", "---", ""]

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
            resolved = resolve_injection_path(entry, pc, project_root)
            rel = resolved.relative_to(project_root.resolve()) if resolved.is_relative_to(project_root.resolve()) else resolved
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
    active tool not skipped for this provider. Warns when a tool declares a hook
    stem that has no matching hooks/0-external/<stem>.sh file. The hook wrapper
    .sh files themselves are deployed independently by sync_hooks() (all
    0-external hooks are always copied; registration in settings.json stays
    opt-in per project).
    """
    registry = load_external_tools_registry(agent_meta_root, config, project_root)
    if not registry:
        return

    active_tools = resolve_active_external_tools(config, agent_meta_root, project_root)
    if not active_tools:
        return

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

    effective_rules_dir = rules_dir or DEFAULT_RULES_DIR
    target_dir = project_root / effective_rules_dir
    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    for tool_name in active_tools:
        tool_def = registry.get(tool_name)
        if not tool_def:
            continue
        if provider in tool_def.get("provider-skip", []):
            continue

        filename = f"{TOOL_RULE_PREFIX}{tool_name}.md"
        target_path = safe_path(target_dir, filename)
        content = _generate_tool_rule_content(tool_name, tool_def, pc, project_root)
        rel_out = str(target_path.relative_to(project_root))
        src_label = f"external-tools-registry/{tool_name}"

        if write_checked(target_path, content, log, src_label, config=config, dry_run=dry_run):
            log.action("WRITE", rel_out, src_label)
        else:
            log.skip(rel_out, "unchanged")
