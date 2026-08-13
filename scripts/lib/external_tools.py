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
DRIFT_FILENAME = "external-tools-drift.md"
_DRIFT_CAP = 10


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


# ---------------------------------------------------------------------------
# Drift artifact rendering
# ---------------------------------------------------------------------------

def _generate_drift_content(findings: list[dict]) -> str:
    """Generate Markdown content for external-tools-drift.md from findings."""
    lines = [
        "# External-Tool Injection Drift", "",
        "> Automatisch erkannt von `check_injection_drift` — Fremd-Artefakte, die keinem "
        "aktiven Tool in `config/external-tools-registry.yaml` als `permitted-injections` "
        "deklariert sind. Nur Warnung, kein automatisches Eingreifen.",
        "", "---", "",
    ]
    shown = findings[:_DRIFT_CAP]
    for f in shown:
        tool_label = f["tool"] or "keinem registrierten Tool zugeordnet"
        lines.append(f"- `{f['path']}` ({f['kind']}) — {tool_label}")
    remaining = len(findings) - len(shown)
    if remaining > 0:
        lines.append(f"- … {remaining} weitere, siehe sync.log")
    lines.append("")
    return "\n".join(lines) + "\n"


def render_injection_drift_artifacts(
    findings_by_provider: dict[str, list[dict]],
    project_root: Path,
    provider_config: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Render sparse external-tools-drift.md files when drift is detected.

    For each provider with has_rules: True, if findings exist, write
    .claude/rules/external-tools-drift.md (capped at 10 items). If no
    findings exist, delete the file if present. Warnings are logged for all
    findings regardless of has_rules setting. Uses write_checked for
    idempotence.
    """
    for provider, findings in findings_by_provider.items():
        pc = provider_config.get(provider, {})

        # Log warnings for all findings unconditionally.
        for f in findings:
            log.warning(
                f"external-tools: undeclared artifact '{f['path']}' ({f['kind']}) for provider "
                f"'{provider}' — not covered by any active tool's permitted-injections"
            )

        # Skip file rendering for providers without has_rules capability.
        if not pc.get("has_rules"):
            continue

        rules_dir = project_root / pc.get("rules_dir", DEFAULT_RULES_DIR)
        target_path = rules_dir / DRIFT_FILENAME

        if not findings:
            if target_path.exists():
                log.action("DELETE", str(target_path.relative_to(project_root)), "no drift found")
                if not dry_run:
                    target_path.unlink()
            continue

        content = _generate_drift_content(findings)
        rel_out = str(target_path.relative_to(project_root))

        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)

        if write_checked(target_path, content, log, "external-tools-drift", dry_run=dry_run):
            log.action("WRITE", rel_out, "external-tools-drift")
        else:
            log.skip(rel_out, "unchanged")


# ---------------------------------------------------------------------------
# Injection drift scanning
# ---------------------------------------------------------------------------

def _read_managed_index(dir_path: Path) -> set[str]:
    index_path = dir_path / ".agent-meta-managed"
    if not index_path.exists():
        return set()
    return {
        line.strip() for line in index_path.read_text(encoding="utf-8").splitlines() if line.strip()
    }


# Top-level entries under a provider's infra root that agent-meta itself may
# place there, independent of the four managed subdirs. Keyed by the
# provider_config field that names each one; a field absent from `pc` is
# skipped (not every provider has every capability).
_INFRA_ROOT_KNOWN_KEYS = [
    "agents_dir", "hooks_dir", "rules_dir", "commands_dir", "skills_dir",
    "snippets_dir", "extension_dir", "artifact_dir", "checkpoint_dir",
    "settings_file", "pending_tasks_file",
]
# Per-provider hardcoded fallback dirs for capability-gated keys that some
# providers (Claude, Continue) never store in ai-providers.yaml, relying
# instead on a literal default in the sync code itself (dir_specs above /
# lib.commands.sync_commands_for_provider). Without this, the fallback
# directory is agent-meta's own managed dir, but scan_injection_drift has no
# key to read its name from and misreports it as a top-level foreign "other"
# finding.
_INFRA_ROOT_FALLBACK_DIRS = {
    "hooks_dir": {"Claude": ".claude/hooks"},
    "rules_dir": {"Claude": DEFAULT_RULES_DIR},
    "commands_dir": {"Claude": ".claude/commands", "Continue": ".continue/prompts"},
}


def scan_injection_drift(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    provider_config: dict,
) -> dict[str, list[dict]]:
    """Find files/dirs under each active provider's infra root that neither
    agent-meta itself manages (per-directory .agent-meta-managed indexes) nor
    any active external tool's permitted-injections declares. Pure — no writes.
    """
    from .deactivation import is_provider_active
    from .mcp import resolve_active_mcp_servers

    registry = load_external_tools_registry(agent_meta_root, config, project_root)
    active_tools = resolve_active_external_tools(config, agent_meta_root, project_root)
    active_mcp = set(resolve_active_mcp_servers(config, agent_meta_root, project_root))

    findings_by_provider: dict[str, list[dict]] = {}

    for provider, pc in provider_config.items():
        if not is_provider_active(config, provider):
            continue

        # Permitted set, resolved to absolute paths, keyed by dir-kind.
        permitted_by_kind: dict[str, set[Path]] = {"skill": set(), "hook": set(), "rule": set()}
        permitted_root_extra: set[Path] = set()  # kind: config/other
        for tool_name in active_tools:
            for entry in registry.get(tool_name, {}).get("permitted-injections", []):
                resolved = resolve_injection_path(entry, pc, project_root)
                if entry["kind"] in permitted_by_kind:
                    permitted_by_kind[entry["kind"]].add(resolved)
                else:
                    permitted_root_extra.add(resolved)

        provider_findings: list[dict] = []

        # --- managed subdirs: skill / hook / rule (declarable kinds) ---
        # "skill" is unconditional (no has_skills flag exists in
        # ai-providers.yaml). "hook"/"rule" are gated on the provider's own
        # has_hooks/has_rules capability flags — without the gate, a provider
        # lacking the key (e.g. Opencode: no hooks_dir/rules_dir at all) would
        # silently fall through to Claude's ".claude/hooks"/".claude/rules"
        # defaults and misattribute Claude's own dir content to it.
        dir_specs = [("skill", pc.get("skills_dir", ".claude/skills"))]
        if pc.get("has_hooks", False):
            dir_specs.append(("hook", pc.get("hooks_dir", ".claude/hooks")))
        if pc.get("has_rules", False):
            dir_specs.append(("rule", pc.get("rules_dir", ".claude/rules")))
        for kind, dir_rel in dir_specs:
            dir_path = project_root / dir_rel
            if not dir_path.is_dir():
                continue
            managed = _read_managed_index(dir_path)
            if kind == "rule":
                managed |= {f"{TOOL_RULE_PREFIX}{t}.md" for t in active_tools}
                managed |= {f"mcp-{s}.md" for s in active_mcp}
            for child in sorted(dir_path.iterdir()):
                if child.name == ".agent-meta-managed":
                    continue
                if child.name in managed:
                    continue
                if child.resolve() in permitted_by_kind[kind]:
                    continue
                provider_findings.append({
                    "path": str(child.relative_to(project_root)),
                    "kind": kind,
                    "tool": None,
                })

        # --- agents_dir: no declarable permitted-injections kind exists for
        # it (per spec — agent files are never legitimately tool-installed).
        # Only an explicit kind: config/other entry (permitted_root_extra)
        # can excuse a finding here; the existing .agent-meta-managed index
        # (agents.py:1498) still excuses agent-meta's own generated roles.
        agents_dir_path = project_root / pc.get("agents_dir", ".claude/agents")
        if agents_dir_path.is_dir():
            managed = _read_managed_index(agents_dir_path)
            for child in sorted(agents_dir_path.iterdir()):
                if child.name == ".agent-meta-managed":
                    continue
                if child.name in managed:
                    continue
                if child.resolve() in permitted_root_extra:
                    continue
                provider_findings.append({
                    "path": str(child.relative_to(project_root)),
                    "kind": "other",
                    "tool": None,
                })

        # --- infra root: loose files/dirs beside the four managed subdirs ---
        # Determined from the provider's own infra root (parent of skills_dir,
        # e.g. ".claude" for Claude) rather than a hardcoded ".claude" literal,
        # so Gemini/.gemini, Opencode/.opencode etc. are covered the same way.
        skills_dir_rel = pc.get("skills_dir")
        if skills_dir_rel:
            infra_root = (project_root / skills_dir_rel).parent
            if infra_root.is_dir() and infra_root != project_root:
                known_names = set()
                for key in _INFRA_ROOT_KNOWN_KEYS:
                    val = pc.get(key)
                    if val:
                        known_names.add(Path(val).name)
                # Capability-gated fallback: the key may be absent from
                # ai-providers.yaml (Claude's hooks_dir/rules_dir/
                # commands_dir, Continue's commands_dir) with sync code
                # falling back to a hardcoded literal instead — only excuse
                # it when the provider actually has the capability, so e.g.
                # Opencode (has_rules: False) doesn't get a same-named
                # directory excused for the wrong reason.
                capability_by_key = {
                    "hooks_dir": "has_hooks", "rules_dir": "has_rules", "commands_dir": "has_commands",
                }
                for key, fallbacks in _INFRA_ROOT_FALLBACK_DIRS.items():
                    if pc.get(capability_by_key[key], False) and provider in fallbacks:
                        known_names.add(Path(fallbacks[provider]).name)
                # settings_local_file's basename varies per provider (e.g.
                # Continue: config.local.yaml, not settings.local.json).
                settings_local_val = pc.get("settings_local_file")
                if settings_local_val:
                    known_names.add(Path(settings_local_val).name)
                known_names.add("settings.local.json")
                # agent-memory/agent-memory-local are a documented agent-meta
                # feature (docs/guides/features/agent-memory.md), not external-
                # tool injections — no dedicated provider_config key exists for
                # them (agent-memory-local only appears buried in Claude's
                # gitignore_entries), so they're excused as literals.
                known_names.add("agent-memory")
                known_names.add("agent-memory-local")
                # Claude Code harness's own session task-scheduler lock —
                # local-machine runtime state (excluded via .git/info/exclude,
                # not a shared gitignore entry), not an external-tool
                # injection or an agent-meta artifact.
                known_names.add("scheduled_tasks.lock")
                for child in sorted(infra_root.iterdir()):
                    if child.name in known_names:
                        continue
                    if child.resolve() in permitted_root_extra:
                        continue
                    provider_findings.append({
                        "path": str(child.relative_to(project_root)),
                        "kind": "other",
                        "tool": None,
                    })

        findings_by_provider[provider] = provider_findings

    return findings_by_provider
