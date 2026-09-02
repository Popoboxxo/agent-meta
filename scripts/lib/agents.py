"""Agent hint/table builders for context files + backward-compat re-exports.

The bulk of the former agents.py was split (Issue #561) into the neutral
frontmatter layer, the provider_transform formatting layer and the agent_sync
orchestration layer. This module keeps the config/context-facing hint builders
(build_agent_hints/build_agent_table/build_knowledge_engine_hints) and
re-exports every moved symbol so existing `from .agents import X` call sites
(tests, sync.py, context.py, standalone.py, ...) keep working unchanged.
"""
from __future__ import annotations

from pathlib import Path  # noqa: F401

from .frontmatter import (  # noqa: F401 (re-exported for callers/tests, Issue #561)
    _YAML_AVAILABLE,
    AGENTS_DIR,
    EXTERNAL_DIR,
    EXT_SUFFIX,
    GENERIC_DIR,
    PLATFORM_DIR,
    PROJECT_DIR,
    PROVIDER_TOOLS_CONFIG,
    SKILL_WRAPPER,
    _insert_after_frontmatter,
    _is_role_enabled,
    _merge_frontmatter,
    _parse_frontmatter_yaml,
    _provider_tools_cache,
    _remove_frontmatter_fields,
    _split_frontmatter,
    _strip_frontmatter,
    _update_frontmatter_dict,
    append_frontmatter_tools,
    build_frontmatter,
    collect_sources,
    ext_target_filename,
    extract_frontmatter_field,
    inject_memory_field,
    inject_model_field,
    inject_permission_mode_field,
    is_deprecated_template,
    load_provider_tools_config,
    parse_frontmatter_file,
    role_from_platform_file,
    target_filename,
)
from .provider_transform import (  # noqa: F401 (re-exported for callers/tests, Issue #561)
    _DEBUG_BLOCK_MARKER,
    _DEBUG_BLOCK_TEMPLATE,
    _inject_gemini_bootstrap,
    _make_slim_body,
    _make_xml_tag_name,
    _map_claude_tools_to_gemini_tools,
    _map_claude_tools_to_opencode_permissions,
    _strip_claude_specific_lines,
    _transform_frontmatter_for_opencode,
    _validate_tools_against_whitelist,
    inject_debug_block,
    transform_agent_content_for_provider,
    wrap_sections_in_xml,
)
from .agent_sync import (  # noqa: F401 (re-exported for callers/tests, Issue #561)
    _CRITICAL_RULES,
    _dominant_newline,
    _extract_and_append_critical_footer,
    _find_section_bounds,
    _patch_append_after,
    _patch_delete,
    _patch_replace,
    _tools_can_spawn,
    apply_patch,
    apply_path_rules,
    compose_agent,
    resolve_mcp_tools_for_role,
    sync_agents_for_provider,
)


def build_knowledge_engine_hints(config: dict, compact: bool = False) -> str:
    """Generate the Knowledge Engine instructions block if enabled in config.

    compact=True reduces the block to a pointer (bundle path + wiki index +
    schema) per the target rule "discoverable via ls/Read → out of the context
    file" (issue #540 B8). The path table and the agent/workflow prose are
    OVERVIEW and discoverable inside the bundle itself.
    """
    lines = []
    ke_config = config.get("knowledge-engine", {})
    if ke_config.get("enabled", False):
        bundle = ke_config.get("bundle-path", "knowledge")
        domain = ke_config.get("domain", "research")
        wiki = f"{bundle}/wiki"
        sources = f"{bundle}/sources"

        if compact:
            lines.append("## Knowledge Engine")
            lines.append("")
            lines.append(
                f"Aktiviert (Domäne: **{domain}**). Bundle: `{bundle}/` — "
                f"Index: `{wiki}/index.md`, Schema/Workflows: `{bundle}/schema.md`, "
                f"immutable Sources: `{sources}/` (LLM liest, modifiziert NIEMALS)."
            )
            return "\n".join(lines)

        lines.append("## Knowledge Engine")
        lines.append("")
        lines.append(f"Die Knowledge Engine ist aktiviert. Domäne: **{domain}**.")
        lines.append("")
        lines.append(f"**Bundle-Pfad:** `{bundle}/`")
        lines.append("| Pfad | Zweck |")
        lines.append("|------|-------|")
        lines.append(f"| `{bundle}/schema.md` | Steuerungsdokument — Konventionen, Concept Types, Workflows |")
        lines.append(f"| `{sources}/` | Immutable Raw Sources — LLM liest, modifiziert NIEMALS |")
        lines.append(f"| `{wiki}/` | OKF Knowledge Bundle — LLM-owned, strukturiertes Wiki |")
        lines.append(f"| `{wiki}/index.md` | Content-Katalog aller Wiki-Seiten (OKF §6) |")
        lines.append(f"| `{wiki}/log.md` | Chronologisches Event-Log (OKF §7) |")
        lines.append("")
        lines.append("### Knowledge-Agenten")
        lines.append(f"- **Schema-Owner:** `knowledge-curator` verwaltet `{bundle}/schema.md` und Concept-Type-Konventionen")
        lines.append("")
        lines.append("### Knowledge-Workflows")
        lines.append(f"- **Ingest:** Source in `{sources}/` ablegen → `knowledge-ingestor` verarbeitet → Wiki aktualisiert")
        lines.append("- **Query:** Frage stellen → `knowledge-querier` durchsucht Index → synthetisiert Antwort")
        lines.append("- **Lint:** `knowledge-linter` prüft Wiki-Gesundheit (Widersprüche, Orphans, OKF-Compliance)")
        lines.append("- **Migration:** `knowledge-migrator` räumt vorhandene Inhalte auf und migriert ins OKF-Format")
        lines.append("- **Gardening:** `knowledge-gardener` pflegt Links, Tags, Typos, Timestamps")
        
    return "\n".join(lines)

def build_agent_hints(config: dict, agent_meta_root: Path, include_table: bool = True) -> str:
    """Generate agent usage hints for {{AGENT_HINTS}}.

    Reads hint (preferred) or description from each active agent's template frontmatter.
    If orchestrator is active, adds a prominent start hint.

    include_table:
      True  → full output: entry-point hint + per-agent role/description table.
      False → entry-point hint only. Used for providers (e.g. Claude) that inject
              agent descriptions natively — the table would be a ~1.5 KB duplication.
    """
    from .roles import build_role_map

    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    role_map = build_role_map(agent_meta_root)
    allowed_roles: set[str] | None = None
    if "roles" in config:
        allowed_roles = set(config["roles"])

    lines = []
    # Determine if main-chat mode is active (no orchestrator subagent in this mode)
    _orch_cfg = config.get("orchestrator", {})
    _orch_mode_explicit = _orch_cfg.get("mode")
    if _orch_mode_explicit is not None:
        _is_main_chat_mode = str(_orch_mode_explicit).strip().lower() == "main-chat"
    else:
        # Legacy fallback: enabled=false was the old way to disable orchestrator
        _is_main_chat_mode = not _orch_cfg.get("enabled", True)

    has_orchestrator = (
        "orchestrator" in overrides
        and (allowed_roles is None or "orchestrator" in allowed_roles)
        and not _is_main_chat_mode
    )
    if has_orchestrator:
        lines.append(
            "> **Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben — Ausnahmen siehe Abschnitt »Orchestrator — Universal Router«."
        )
    elif _is_main_chat_mode:
        lines.append(
            "> **Einstiegspunkt:** Du bist im `main-chat` Modus. Du agierst direkt als Router und Worker (siehe `use-orchestrator.md`)."
        )

    if include_table:
        if has_orchestrator:
            lines.append("")
        lines.append("| Agent | Zuständigkeit |")
        lines.append("|-------|--------------|")
        for role, source_path in sorted(overrides.items()):
            if allowed_roles is not None and role not in allowed_roles:
                continue
            if not _is_role_enabled(role, config):
                continue
            if not target_filename(role, role_map):
                continue
            content = source_path.read_text(encoding="utf-8")
            hint = extract_frontmatter_field(content, "hint") \
                or extract_frontmatter_field(content, "description") \
                or ""
            lines.append(f"| `{role}` | {hint} |")

    # Knowledge Engine hints (only when enabled). Emitted regardless of
    # include_table — this section is not a per-agent table duplication, it's
    # entry-point orientation that every provider (including Claude, which
    # gets AGENT_HINTS_CLAUDE with include_table=False) needs to see.
    ke_hints = build_knowledge_engine_hints(config)
    if ke_hints:
        lines.append("")
        lines.append(ke_hints)

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
        if not _is_role_enabled(role, config):
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
