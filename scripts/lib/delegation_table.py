from __future__ import annotations

import re
from pathlib import Path

from .roles import load_roles_config

# List separators used by role descriptions. Most short_desc values already
# enumerate capabilities as comma-separated noun phrases, so splitting on
# separators and keeping the leading segments yields the highest-signal nouns
# without any hardcoded per-agent keyword table (issue #540 B1).
_KEYWORD_SPLIT_RE = re.compile(r",|;| und | bzw\. | oder ")
_EGG_MARKER_RE = re.compile(r"\[[^\]]*\]\s*")


def derive_keywords(description: str, max_keywords: int = 3, max_length: int = 100) -> str:
    """Derive up to ``max_keywords`` noun phrases from an agent description.

    Compact agent-directory rows show ``name | max 3 keywords`` instead of the
    full description sentence (issue #540 B1). Keywords are derived from the
    description at generation time — first sentence only, split on list
    separators, first segments kept. No per-agent hardcoded list.
    """
    text = _EGG_MARKER_RE.sub("", description or "").strip()
    if not text:
        return ""
    # First sentence only — trailing prose ("...", "…") must not leak in.
    text = re.split(r"(?:\.\s|\.\.\.|…)", text)[0].strip()
    segments = (s.strip(" .…—-\u2014") for s in _KEYWORD_SPLIT_RE.split(text))
    keys = [s for s in segments if s]
    return ", ".join(keys[:max_keywords])[:max_length].rstrip()


def _active_role_names(agent_meta_root: Path, config: dict, variables: dict) -> list[str]:
    """Return the sorted role names that pass project activation filters.

    Shared activation logic (issue #264): feature-flag gates (SE, validator,
    knowledge engine, developer tiers) and the optional project ``roles``
    whitelist — exactly the filter chain ``get_active_agents_data()`` applies,
    extracted so the structured routing-rule builder sees the identical set
    of agents as the tables.
    """
    roles_cfg = load_roles_config(agent_meta_root)
    roles = roles_cfg.get("roles", {})

    roles_list = config.get("roles")
    active_roles = set(roles_list) if roles_list is not None else None

    se_enabled = variables.get("SE_ENABLED", "false") == "true"
    validator_enabled = variables.get("VALIDATOR_ENABLED", "false") == "true"
    knowledge_enabled = variables.get("KNOWLEDGE_ENGINE_ENABLED", "false") == "true"
    developer_tiers = variables.get("DEVELOPER_TIERS_ENABLED", "false") == "true"

    active = []
    for role_name in sorted(roles.keys()):
        if role_name.startswith("se-") and not se_enabled:
            continue
        if role_name == "validator" and not validator_enabled:
            continue
        if role_name.startswith("knowledge-") and not knowledge_enabled:
            continue
        if role_name in ("junior-developer", "senior-developer", "principal-developer") and not developer_tiers:
            continue
        if active_roles is not None and role_name not in active_roles:
            continue
        active.append(role_name)
    return active


def get_active_agents_data(agent_meta_root: Path, config: dict, variables: dict) -> list[dict]:
    """Return a list of dictionaries with agent data.

    Reads roles from config/role-defaults.yaml and respects workflow_tier and feature flags.
    Returns: list of dicts with 'name', 'short_desc' and derived 'keywords'.
    """
    roles_cfg = load_roles_config(agent_meta_root)
    roles = roles_cfg.get("roles", {})

    active_agents_data = []

    for role_name in _active_role_names(agent_meta_root, config, variables):
        role_info = roles[role_name]

        desc = role_info.get("short_desc", role_info.get("description", ""))
        active_agents_data.append({
            "name": role_name,
            "short_desc": desc,
            # Consumed by the compact branch of templates/context/partials/
            # agents-table.md ({{#if COMPACT_MODE}}); computed unconditionally
            # so the loop expansion never leaves a literal {{keywords}} behind.
            "keywords": derive_keywords(desc),
        })

    return active_agents_data


def get_routing_rules(
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    pipelines: dict | None = None,
) -> dict:
    """Build structured routing rules for the native intent-routing tool (issue #264).

    Data layer of the #264 generation pipeline: resolves each active role's
    ``routing_patterns`` (``config/role-defaults.yaml`` → ``roles.<role>.routing_patterns``
    with ``keywords``/``examples``) into provider-neutral rule dicts. The
    emission layer (``agents.build_routing_tool_definition``) turns these into
    a tool definition; this function is deliberately format-agnostic.

    Resolution rules:

    - ``keywords`` falls back to the legacy ``routing.intent_keywords`` list
      when ``routing_patterns.keywords`` is absent — keeps hand-written
      fixtures and not-yet-migrated roles routable without duplication.
    - Roles without any patterns produce no rule (they are not keyword-routable)
      but still appear in ``target_agents`` — the tool's enum covers name-based
      dispatch too, mirroring the current prose table.
    - ``orchestrator`` is excluded entirely (anti-recursion: self-dispatch is a
      HARD REJECT, see orchestrator.md Singleton-Regel).
    - ``orchestrator_only`` roles keep their rule + flag: the tool's consumer
      IS the orchestrator; the escalation gate lives in the prompt/data, not here.

    Returns:
        ``{"target_agents": [...], "rules": [...], "pipelines": [...]}`` —
        ``target_agents`` is the sorted enum of active non-orchestrator roles;
        ``rules`` carries ``agent/tier/parallel/orchestrator_only/keywords/
        examples/output_contract/input_contracts`` per routed role (sorted by
        agent name for deterministic, idempotent output); ``pipelines`` maps
        quality pipelines with ``signal_keywords`` to ``{"route": "pipeline",
        "pipeline": <name>, "keywords": [...]}`` entries (sorted by name).
    """
    roles_cfg = load_roles_config(agent_meta_root)
    roles = roles_cfg.get("roles", {})
    target_agents = [
        name for name in _active_role_names(agent_meta_root, config, variables)
        if name != "orchestrator"
    ]

    rules = []
    for role_name in target_agents:
        role_info = roles.get(role_name) or {}
        patterns = role_info.get("routing_patterns")
        patterns = patterns if isinstance(patterns, dict) else {}
        routing = role_info.get("routing")
        routing = routing if isinstance(routing, dict) else {}
        keywords = patterns.get("keywords")
        if not isinstance(keywords, list):
            # Documented fallback: legacy routing.intent_keywords (no other
            # Python consumer) keeps unmigrated roles keyword-routable.
            keywords = routing.get("intent_keywords")
        keywords = [str(k) for k in keywords] if isinstance(keywords, list) else []
        examples = patterns.get("examples")
        examples = [str(e) for e in examples] if isinstance(examples, list) else []
        if not keywords and not examples:
            continue
        handoff = role_info.get("handoff")
        handoff = handoff if isinstance(handoff, dict) else {}
        rules.append({
            "agent": role_name,
            "tier": role_info.get("workflow_tier", "optional"),
            "parallel": bool(routing.get("parallel", False)),
            "orchestrator_only": bool(routing.get("orchestrator_only", False)),
            "keywords": keywords,
            "examples": examples,
            "output_contract": str(handoff.get("output_contract") or ""),
            "input_contracts": [
                str(c) for c in (handoff.get("input_contracts") or []) if str(c).strip()
            ],
        })

    pipeline_rules = []
    for pipeline_name in sorted((pipelines or {}).keys()):
        pipeline_info = pipelines[pipeline_name]  # type: ignore[index]
        if not isinstance(pipeline_info, dict):
            continue
        signal_keywords = pipeline_info.get("signal_keywords")
        if not isinstance(signal_keywords, list) or not signal_keywords:
            continue
        pipeline_rules.append({
            "route": "pipeline",
            "pipeline": pipeline_name,
            "keywords": [str(k) for k in signal_keywords],
        })

    return {"target_agents": target_agents, "rules": rules, "pipelines": pipeline_rules}


def get_intent_routing_table(
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    pipelines: dict | None = None,
) -> str:
    """Generate the INTENT_ROUTING_TABLE: pipeline routing rows + a Tiers summary.

    Per-agent routing rows were dropped (token-efficiency review, 2026-08-14):
    each active agent's name + description already appears in the system
    prompt (Claude/Opencode), so a keyword->agent row in this table was pure
    duplication. Pipelines are NOT represented in the system prompt, so those
    rows stay. A compact 'Tiers' line replaces the removed per-agent rows so
    required/recommended coverage is still visible at a glance.
    """
    roles_cfg = load_roles_config(agent_meta_root)
    roles = roles_cfg.get("roles", {})
    active_agents_data = get_active_agents_data(agent_meta_root, config, variables)
    active_agent_names = {agent["name"] for agent in active_agents_data}

    required = sorted(
        name for name in active_agent_names
        if roles.get(name, {}).get("workflow_tier", "optional") == "required"
    )
    recommended = sorted(
        name for name in active_agent_names
        if roles.get(name, {}).get("workflow_tier", "optional") == "recommended"
    )

    table_lines = [
        "> Parallel ist rein informativ — kein Runtime-Enforcement, nur CI-Konsistenzcheck bei required/recommended-Tier-Abdeckung.",
        "",
    ]
    if required or recommended:
        rec_str = ", ".join(f"`{n}`" for n in recommended) or "—"
        req_str = ", ".join(f"`{n}`" for n in required) or "—"
        table_lines.append(f"**Tiers** (nicht gelistet = optional): recommended: {rec_str} | required: {req_str}")
        table_lines.append("")

    table_lines += [
        "| Intent / Keywords | Agent | Tier | Parallel |",
        "|-------------------|-------|------|----------|"
    ]

    has_entries = False
    for pipeline_name in sorted((pipelines or {}).keys()):
        pipeline_info = pipelines[pipeline_name]
        signal_keywords = pipeline_info.get("signal_keywords", [])
        if not signal_keywords:
            continue
        keywords_str = ", ".join(signal_keywords)
        table_lines.append(f"| {keywords_str} | → Pipeline: `{pipeline_name}` | pipeline | no |")
        has_entries = True

    if not has_entries and not (required or recommended):
        return ""

    return "\n".join(table_lines) + "\n"
