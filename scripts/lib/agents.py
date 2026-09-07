"""Agent hint/table builders for config/context files.

The bulk of the former agents.py was split (Issue #561) into the neutral
frontmatter layer, the provider_transform formatting layer and the agent_sync
orchestration layer. This module keeps only the config/context-facing hint
builders (build_agent_hints/build_agent_table/build_knowledge_engine_hints)
plus the structured intent-routing tool-definition generators (issue #264).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from .frontmatter import (
    _is_role_enabled,
    collect_sources,
    extract_frontmatter_field,
    target_filename,
)

if TYPE_CHECKING:
    from .delegation_syntax import DelegationSyntaxEngine

try:
    import yaml as _yaml  # only used by the yaml_text_block serializer
except ImportError:  # pragma: no cover — mirrors io.py/frontmatter.py loader guards
    _yaml = None

# Native function-calling tool name for intent routing (issue #264). The
# orchestrator dispatches through the harness's own subagent tool; this
# definition is the structured routing contract consumed per provider format
# (handoff_format mechanism key from config/provider-capabilities.yaml).
ROUTING_TOOL_NAME = "route_intent"

# Static, deterministic tool description (English — code artifact convention).
# Provider-agnostic by design: it names no harness tool and no provider.
_ROUTING_TOOL_DESCRIPTION = (
    "Resolve a user request to a dispatch target before delegating. Prefer a "
    "pipeline route when the intent matches a pipeline's signal_keywords. "
    "Otherwise match the intent against the routing rules (keywords, example "
    "phrases) and return the best-fitting target_agent. Never dispatch to "
    "yourself; orchestrator_only targets require the escalation gate."
)

# Known serialization formats, keyed exactly like the existing
# handoff_format mechanism key in config/provider-capabilities.yaml
# ("json" | "yaml_text_block"). Adding a format = one key here + a branch in
# render_routing_tool_definition() + config change — never a provider-name
# branch (provider-agnostic policy).
_TOOL_FORMAT_KEYS = frozenset({"json", "yaml_text_block"})


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


# ---------------------------------------------------------------------------
# Structured intent-routing tool definitions (issue #264)
# ---------------------------------------------------------------------------
#
# Generation-side replacement for the orchestrator prompt's prose routing
# tables. Data layer: delegation_table.get_routing_rules() (same activation
# filters as the existing tables). Emission layer (below): provider-neutral
# tool definition → per-format serialization via a mechanism-key dispatch
# table ("json" | "yaml_text_block" — the same keys the existing
# handoff_format capability uses). No provider names appear anywhere in code.

def build_routing_tool_definition(
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    pipelines: dict | None = None,
) -> dict:
    """Build the provider-neutral intent-routing tool definition (issue #264).

    Args:
        agent_meta_root: agent-meta source root (for config/role-defaults.yaml).
        config: loaded project.yaml dict (``roles`` whitelist, read-only).
        variables: build-time variables (SE_ENABLED/VALIDATOR_ENABLED/
            KNOWLEDGE_ENGINE_ENABLED/DEVELOPER_TIERS_ENABLED gates).
        pipelines: effective quality-pipelines dict (same object the
            INTENT_ROUTING_TABLE builder receives) — pipelines with
            signal_keywords become structured pipeline routes.

    Returns:
        A JSON-serializable dict with two members:

        - ``tool``: the native function-calling definition —
          ``{"name", "description", "input_schema"}`` where
          ``input_schema.properties.target_agent.enum`` lists every active
          non-orchestrator role (the structured replacement for the prose
          routing table's role column).
        - ``routing``: the embedded routing knowledge —
          ``{"rules": [<per-role rule dicts>], "pipelines": [<signal-keyword
          route dicts>]}`` (see :func:`delegation_table.get_routing_rules`).

        Deterministic: sorted roles/pipelines, no timestamps — two calls over
        unchanged config produce equal dicts (idempotent output guarantee).
    """
    # Lazy import — keeps agents.py import-light.
    from .delegation_table import get_routing_rules

    rules_data = get_routing_rules(agent_meta_root, config, variables, pipelines=pipelines)
    return {
        "tool": {
            "name": ROUTING_TOOL_NAME,
            "description": _ROUTING_TOOL_DESCRIPTION,
            "input_schema": {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "description": "Verbatim user request or task line.",
                    },
                    "target_agent": {
                        "type": "string",
                        "enum": rules_data["target_agents"],
                        "description": (
                            "Active agent role to dispatch to (orchestrator "
                            "excluded: self-dispatch is forbidden)."
                        ),
                    },
                    "matched_rule": {
                        "type": "string",
                        "description": (
                            "Optional provenance: the matched keyword, example "
                            "phrase, or pipeline route."
                        ),
                    },
                },
                "required": ["intent", "target_agent"],
            },
        },
        "routing": {
            "rules": rules_data["rules"],
            "pipelines": rules_data["pipelines"],
        },
    }


def render_routing_tool_definition(definition: dict, tool_format: str) -> str:
    """Serialize a routing tool definition in a provider's native format.

    Format dispatch is mechanism-keyed: ``tool_format`` uses the same value
    domain as the existing ``handoff_format`` capability key in
    ``config/provider-capabilities.yaml`` — ``"json"`` for providers with
    native tool-call envelopes, ``"yaml_text_block"`` for text-mention
    providers. Known-key validation is fail-closed (mechanism-key precedent,
    see docs/spikes/2026-09-06-issue-265-async-fanout-spike.md §5.1).

    Args:
        definition: dict from :func:`build_routing_tool_definition`.
        tool_format: mechanism key — ``"json"`` or ``"yaml_text_block"``.

    Returns:
        The serialized artifact as text (trailing newline for ``json``).

    Raises:
        ValueError: on an unknown format key (never silently falsifies a
            provider's format); the message lists known keys only.
    """
    if tool_format == "json":
        return json.dumps(definition, indent=2, ensure_ascii=False) + "\n"
    if tool_format == "yaml_text_block":
        if _yaml is None:
            raise ValueError(
                "tool_format 'yaml_text_block' requires PyYAML "
                "(pip install pyyaml)"
            )
        return _yaml.safe_dump(
            definition,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=100,
        )
    raise ValueError(
        f"Unknown routing tool format '{tool_format}' — known formats: "
        f"{', '.join(sorted(_TOOL_FORMAT_KEYS))}"
    )


def build_routing_tool_definitions_for_providers(
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    providers: list[str],
    pipelines: dict | None = None,
    syntax_engine: DelegationSyntaxEngine | None = None,
) -> dict[str, str]:
    """Render the routing tool definition once per provider, in its format.

    The format is read from each provider's existing ``handoff_format``
    capability key (config/provider-capabilities.yaml) via
    :class:`delegation_syntax.DelegationSyntaxEngine` — config-driven, no
    provider-name branch. Providers with an empty/absent ``handoff_format``
    get an empty string (same fail-soft semantics as the PAL engine's
    missing-definition placeholders; drift detection is the later
    consistency-check step's job).

    Args:
        agent_meta_root, config, variables, pipelines: as in
            :func:`build_routing_tool_definition` (built exactly once).
        providers: provider registry keys to render for.
        syntax_engine: optional pre-built engine (reused to avoid re-parsing
            the capability registry per caller).

    Returns:
        ``{provider: rendered artifact or ""}``.
    """
    from .delegation_syntax import DelegationSyntaxEngine  # lazy import

    engine = syntax_engine or DelegationSyntaxEngine()
    definition = build_routing_tool_definition(
        agent_meta_root, config, variables, pipelines=pipelines
    )
    rendered: dict[str, str] = {}
    for provider in providers:
        caps = engine.get_capabilities(provider)
        tool_format = str(caps.get("handoff_format") or "")
        rendered[provider] = (
            render_routing_tool_definition(definition, tool_format) if tool_format else ""
        )
    return rendered
