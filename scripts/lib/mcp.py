"""MCP framework: server registry, rule generation, gitignore management,
provider config generation and secrets template initialisation.

Public interface:
    load_mcp_registry(agent_meta_root)              → dict of server definitions
    resolve_active_mcp_servers(config, root)        → list of active server names
    generate_mcp_artifacts(...)                     → writes rule + provider config files,
                                                      returns gitignore entries
    sync_secrets_template(...)                       → creates/updates .meta-config/secrets.local.yaml
"""
from __future__ import annotations

from pathlib import Path

from .io import (
    _load_yaml_or_json,
    safe_path,
    write_checked,
)
from .log import SyncLog
from .mcp_registry import (  # noqa: F401 (re-exported for callers/tests, issue #613)
    SECRETS_LOCAL_FILE,
    build_mcp_guardrails_list,
    load_mcp_registry,
    resolve_active_mcp_servers,
)
from .rule_index import (
    bootstrap_previously_managed,
    cleanup_stale_managed_files,
    write_managed_index,
)

MCP_RULE_PREFIX = "mcp-"
# Fallback rules directory for providers without an explicit rules_dir (Claude).
# Mirrors rules.CLAUDE_RULES_DIR to keep MCP rule output aligned with sync_rules().
DEFAULT_RULES_DIR = ".claude/rules"
# Own managed-index filename for mcp-*.md rule files — deliberately separate
# from rules.py's ".agent-meta-managed" (which tracks the rules/ layer sources)
# so the two independent write loops never fight over the same index file.
MCP_MANAGED_INDEX_FILENAME = ".agent-meta-managed-mcp"


# ---------------------------------------------------------------------------
# Rule content generation
# ---------------------------------------------------------------------------

def _generate_rule_content(server_name: str, server_def: dict, compact: bool = False) -> str:
    """Build Markdown rule content for one MCP server from registry definition.

    compact=True renders the listen-only variant for embedded context files
    (issue #540 B3): title + one-line purpose + tool allow/block lists +
    connection type as a single pointer line. The Agent-Hinweise prose and the
    generator footer are dropped — both are OVERVIEW/METADATEN per
    docs/guides/context-block-inventory.md. The block lists themselves are
    INSTRUKTION and are NEVER dropped in either mode. Native rule artifacts
    (.claude/rules/mcp-*.md etc., the lazy channel) keep the full variant.
    """
    desc = server_def.get("description", server_name)
    lines: list[str] = [f"# MCP: {server_name}", "", f"> {desc}", "", "---", ""]

    tools = server_def.get("tools", {})
    allowed = tools.get("allowed", [])
    blocked = tools.get("blocked", [])

    if allowed:
        lines += ["## Erlaubte Tools", ""]
        lines += [f"- `{t}`" for t in allowed]
        lines.append("")

    if blocked:
        lines += ["## Verbotene Tools (ABSOLUT — keine Ausnahmen)", ""]
        lines += [f"- `{t}`" for t in blocked]
        lines.append("")

    hint = (server_def.get("agent-hint") or "").strip()
    if hint and not compact:
        lines += ["## Agent-Hinweise", "", hint, ""]

    conn = server_def.get("connection", {})
    if conn:
        conn_type = conn.get("type", "")
        if compact:
            # Single METADATA line instead of a URL/command block; details stay
            # discoverable in the registry.
            lines.append(f"**Verbindungstyp:** `{conn_type}` — Details: `config/mcp-registry.yaml`.")
            lines.append("")
        else:
            lines += ["## Verbindungstyp", ""]
            lines.append(f"- Typ: `{conn_type}`")
            if conn_type == "sse":
                lines.append(f"- URL: `{conn.get('url', '')}` — Wert aus `secrets.local.yaml`")
            elif conn_type == "stdio":
                cmd = conn.get("command", "")
                args = " ".join(str(a) for a in conn.get("args", []))
                lines.append(f"- Kommando: `{cmd} {args}`")
            lines.append("")

    if not compact:
        lines += [
            "---",
            "",
            "*Generiert von agent-meta aus `config/mcp-registry.yaml` — nicht manuell bearbeiten.*",
        ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Provider config generation — see scripts/lib/mcp_provider_config.py
# (split out to keep this module under the <=600-line convention). That
# module now imports load_mcp_registry/resolve_active_mcp_servers/
# SECRETS_LOCAL_FILE from mcp_registry.py directly, not from here, so this
# top-level import in the other direction cannot form a cycle (issue #613).
# ---------------------------------------------------------------------------

from .mcp_provider_config import (  # noqa: E402, F401 (re-exported for callers/tests)
    _update_json_config,
    generate_provider_configs,
)


# ---------------------------------------------------------------------------
# Secrets template sync (runs on every sync.py invocation)
# ---------------------------------------------------------------------------

def _required_secrets_by_server(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
) -> dict[str, list[str]]:
    """Map active MCP server → its declared `secrets:` list, skipping servers without any."""
    registry = load_mcp_registry(agent_meta_root, config, project_root)
    if not registry:
        return {}

    active_servers = resolve_active_mcp_servers(config, agent_meta_root, project_root, registry=registry)
    if not active_servers:
        return {}

    required: dict[str, list[str]] = {}
    for server_name in active_servers:
        server_def = registry.get(server_name)
        if not server_def:
            continue
        secrets = server_def.get("secrets", [])
        if secrets:
            required[server_name] = secrets
    return required


def _render_secrets_template(required: dict[str, list[str]]) -> str:
    """Build full secrets.local.yaml content (header + one block per server)."""
    lines: list[str] = [
        "# MCP Secrets — lokale Konfiguration",
        "# ====================================",
        "# NIEMALS committen. Diese Datei ist gitignored.",
        "# Nur Einträge befüllen die im Projekt aktiv genutzt werden.",
        "# Danach: python .agent-meta/scripts/sync.py",
        "",
    ]
    for server_name, secrets in required.items():
        lines.append(f"# ── {server_name} ──")
        for secret in secrets:
            lines.append(f'{secret}: ""')
        lines.append("")
    return "\n".join(lines)


def sync_secrets_template(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Keep .meta-config/secrets.local.yaml prepared for every active MCP server.

    Runs on every sync.py invocation (not just --init), so activating a new MCP
    server (e.g. via /add-mcp-server) immediately preps its required env vars as
    empty placeholders — the "Env Dialog" doesn't need to be filled out by hand
    from mcp-registry.yaml.

    - File missing: write the full template.
    - File exists: append only the secret keys of newly-active servers that
      aren't declared yet. Existing keys/values/comments are never touched or
      reordered, so filled-in secrets survive re-syncs untouched.
    """
    required = _required_secrets_by_server(agent_meta_root, project_root, config)
    if not required:
        return

    target_path = project_root / SECRETS_LOCAL_FILE

    if not target_path.exists():
        content = _render_secrets_template(required)
        log.action("INIT", SECRETS_LOCAL_FILE, "MCP secrets template (gitignored)")
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")
        return

    existing_data, _ = _load_yaml_or_json(target_path)
    existing_keys = set((existing_data or {}).keys())

    added_lines: list[str] = []
    added_count = 0
    for server_name, secrets in required.items():
        missing = [s for s in secrets if s not in existing_keys]
        if not missing:
            continue
        added_lines.append(f"# ── {server_name} (neu aktiviert) ──")
        for secret in missing:
            added_lines.append(f'{secret}: ""')
            added_count += 1
        added_lines.append("")

    if not added_lines:
        log.skip(SECRETS_LOCAL_FILE, "all required secrets already present")
        return

    log.action(
        "UPDATE", SECRETS_LOCAL_FILE,
        f"appended {added_count} new secret key(s) for newly active MCP server(s)",
    )
    if dry_run:
        return

    existing_text = target_path.read_text(encoding="utf-8")
    if not existing_text.endswith("\n"):
        existing_text += "\n"
    target_path.write_text(
        existing_text + "\n" + "\n".join(added_lines).rstrip() + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Artifact generation — main entrypoint called by sync.py
# ---------------------------------------------------------------------------

def generate_mcp_artifacts(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    provider_config: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    rules_dir: str | None = None,
    allow_committed_secrets: bool = False,
) -> list[str]:
    """Generate MCP rule files + provider configs for all active servers.

    For each active server (from project.yaml + platform bundles):
      - Writes mcp-<server>.md into the provider's rules_dir (if has_rules),
        or <skills_dir>/mcp-<server>/SKILL.md instead when rules-presets.yaml
        flags rule stem 'mcp-<server>' with channel: skill for a provider
        that supports it (see scripts/lib/skill_channel.py).
      - Writes/updates committed provider config with ${ENV_VAR} references
      - Writes/updates local provider config with actual values (if secrets.local.yaml exists)

    Returns a list of paths to add to the .gitignore managed block:
      - Provider-specific secrets-file (from ai-providers.yaml mcp-config)
      - .meta-config/secrets.local.yaml (central secret store)
    """
    from .rules import resolve_rules
    from .skill_channel import (
        cleanup_stale_skill_channel_rules,
        provider_supports_skill_channel,
        write_skill_channel_managed_index,
        write_skill_channel_rule,
    )

    registry = load_mcp_registry(agent_meta_root, config, project_root)
    if not registry:
        return []

    # No early return on an empty active_servers list here (unlike
    # load_mcp_registry's empty-registry check above): the loops below still
    # need to run with zero entries so cleanup_stale_managed_files() sees an
    # empty now_managed set and removes every previously-generated mcp-*.md
    # rule file — deactivating the last server must not orphan its rule file.
    active_servers = resolve_active_mcp_servers(config, agent_meta_root, project_root, registry=registry)

    pc = provider_config.get(provider, {})
    rule_options = resolve_rules(config, agent_meta_root)
    supports_skill_channel = provider_supports_skill_channel(provider, pc)
    skills_dir_rel = pc.get("skills_dir")
    skills_target_dir = (
        (project_root / skills_dir_rel) if (skills_dir_rel and supports_skill_channel) else None
    )
    all_mcp_rule_stems = {f"{MCP_RULE_PREFIX}{s}" for s in registry}
    now_managed_skill_rules: set[str] = set()

    # --- Rule file generation ---
    # Providers without an explicit rules_dir (e.g. Claude) fall back to the
    # default .claude/rules directory — mirrors sync_rules() in rules.py.
    effective_rules_dir = rules_dir or DEFAULT_RULES_DIR
    if pc.get("has_rules"):
        target_dir = project_root / effective_rules_dir
        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)

        managed_index_path = target_dir / MCP_MANAGED_INDEX_FILENAME
        previously_managed = bootstrap_previously_managed(
            target_dir, managed_index_path, f"{MCP_RULE_PREFIX}*.md",
            # "mcp-*.md" isn't an exclusive namespace — a manually-authored
            # rule like "mcp-guardrails.md" also matches it. Only files
            # actually generated by _generate_rule_content() carry this
            # footer; without the marker check, bootstrap would wrongly
            # sweep unrelated same-prefixed rules on their very first sync.
            content_marker="config/mcp-registry.yaml` — nicht manuell bearbeiten",
        )
        now_managed: set[str] = set()

        for server_name in active_servers:
            server_def = registry.get(server_name)
            if not server_def:
                log.warning(f"mcp: server '{server_name}' not in registry — skipping rule generation")
                continue

            rule_stem = f"{MCP_RULE_PREFIX}{server_name}"
            opts = rule_options.get(rule_stem, {})
            content = _generate_rule_content(server_name, server_def)
            src_label = f"mcp-registry/{server_name}"

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

        # Remove stale mcp-*.md rule files no longer covered by the current
        # active-server list (server deactivated in project.yaml or removed
        # from mcp-registry.yaml).
        cleanup_stale_managed_files(
            target_dir, project_root, previously_managed, now_managed, log, dry_run,
            "mcp server no longer active/registered",
        )
        write_managed_index(managed_index_path, now_managed, dry_run)

    if skills_target_dir is not None:
        cleanup_stale_skill_channel_rules(
            skills_target_dir, project_root, all_mcp_rule_stems, now_managed_skill_rules,
            log, dry_run, "mcp server rule no longer routed to channel: skill",
        )
        write_skill_channel_managed_index(
            skills_target_dir, now_managed_skill_rules, dry_run, universe=all_mcp_rule_stems
        )

    # --- Provider config generation ---
    generate_provider_configs(
        agent_meta_root=agent_meta_root,
        project_root=project_root,
        config=config,
        provider_config=provider_config,
        log=log,
        dry_run=dry_run,
        provider=provider,
        allow_committed_secrets=allow_committed_secrets,
    )

    # --- Gitignore entries ---
    gitignore_extras: list[str] = []
    secrets_file = pc.get("mcp-config", {}).get("secrets-file")
    if secrets_file:
        gitignore_extras.append(secrets_file)

    gitignore_extras.append(SECRETS_LOCAL_FILE)

    return gitignore_extras
