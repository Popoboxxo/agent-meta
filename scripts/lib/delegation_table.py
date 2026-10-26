from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from .roles import load_roles_config, resolve_active_roles

if TYPE_CHECKING:
    from .active_set import ActiveSet

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


def _active_role_names(
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    *,
    require_template: bool = False,
    template_roles: set[str] | None = None,
    warn_sink: list[str] | None = None,
    active_set: ActiveSet | None = None,
) -> list[str]:
    """Return the sorted role names that pass project activation filters.

    With ``active_set`` (IC-17, the per-sync object shared by all generators)
    the set is read from it instead of being resolved again; ``require_template``
    is then implied (``ActiveSet.roles`` is the Layer-2 set).

    Thin seam over ``roles.resolve_active_roles`` (SPEC
    dynamic-routing-template-slimming §3.5): ``variables`` is accepted for
    back-compatibility but is not a gate source — activation resolves from
    ``config`` alone. The default stays Layer 1 (``require_template=False``)
    so existing calls keep working; the internal callers request Layer 2.
    """
    if active_set is not None:
        return sorted(active_set.roles)
    return resolve_active_roles(
        agent_meta_root,
        config,
        require_template=require_template,
        template_roles=template_roles,
        warn_sink=warn_sink,
    )


def _has_routing_patterns(role_info: dict) -> bool:
    """Keyword-addressable per SPEC §3.4: non-empty keywords or examples."""
    patterns = role_info.get("routing_patterns")
    patterns = patterns if isinstance(patterns, dict) else {}
    return bool(patterns.get("keywords") or patterns.get("examples"))


def _derive_addressability(role_info: dict) -> tuple[str, bool]:
    """Return ``(addressability, derived)`` from the role's routing metadata.

    Single derivation shared by the routing ``name_index`` and the entry-file
    table filter (SPEC §3.4): an explicit ``routing.addressability`` wins;
    otherwise a role with routing patterns is ``keyword``, every other role is
    ``name_only`` (name dispatch only, no keyword surface). ``derived`` is True
    when the config carried no explicit value — only the routing builder turns
    that into a warning.
    """
    routing = role_info.get("routing")
    routing = routing if isinstance(routing, dict) else {}
    addressability = routing.get("addressability")
    if addressability in ("keyword", "name_only", "excluded"):
        return addressability, False
    return ("keyword" if _has_routing_patterns(role_info) else "name_only"), True


def exclude_name_only(agents: list[dict]) -> list[dict]:
    """Rows for the rendered agent table: keyword-addressable roles only.

    ``name_only`` roles are name-dispatchable but have no keyword surface, so a
    table row adds bytes to capped entry files without adding a routable
    keyword. They stay in ``target_agents``/``routing.name_index``. The filter
    reads the ``addressability`` field derived from ``config/role-defaults.yaml``
    — no role list is hardcoded here.
    """
    return [agent for agent in agents if agent.get("addressability") != "name_only"]


def _emit_warn_sink(messages: set[str], warn_sink: list[str] | None) -> None:
    """Emit sorted, deduplicated warnings to the sink or the SyncLog fallback."""
    if not messages:
        return
    ordered = sorted(messages)
    if warn_sink is not None:
        existing = set(warn_sink)
        warn_sink.extend(message for message in ordered if message not in existing)
        return
    from .log import SyncLog

    log = SyncLog()
    for message in ordered:
        log.warn(message)


def get_active_agents_data(
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    *,
    template_roles: set[str] | None = None,
    warn_sink: list[str] | None = None,
    active_set: ActiveSet | None = None,
    include_name_only: bool = True,
) -> list[dict]:
    """Return a list of dictionaries with agent data.

    Reads roles from config/role-defaults.yaml and resolves the shared Layer-2
    activation set (gates + whitelist intersected with generatable templates).
    Returns: list of dicts with 'name', 'short_desc', derived 'keywords' and the
    config-derived 'addressability' (keyword | name_only | excluded).

    ``include_name_only=False`` drops the ``name_only`` rows. That is the
    rendered-table view: such roles are reachable by explicit name dispatch
    (``routing.name_index``/``target_agents``) but contribute no keyword and no
    table row. The default stays the full catalog so the F15 contract below
    holds for audits.

    Contract (issue #811 / audit check F15): the returned catalog is exactly
    ``resolve_active_roles(..., require_template=True)``. ``config["roles"]`` is
    a *whitelist*, not the active set: an entry that is disabled by its
    ``activation_groups`` gate (e.g. ``se-component-requirements`` while
    ``systems-engineering.enabled: false``) is intentionally absent from the
    catalog. Audits must compare the catalog against the resolver output, never
    against the raw ``roles`` list. Regression lock:
    ``tests/test_context_catalog_active_roles.py``.
    """
    roles_cfg = load_roles_config(agent_meta_root)
    roles = roles_cfg.get("roles", {})

    active_agents_data = []

    for role_name in _active_role_names(
        agent_meta_root,
        config,
        variables,
        require_template=True,
        template_roles=template_roles,
        warn_sink=warn_sink,
        active_set=active_set,
    ):
        role_info = roles[role_name]
        addressability, _derived = _derive_addressability(role_info)
        if not include_name_only and addressability == "name_only":
            continue

        desc = role_info.get("short_desc", role_info.get("description", ""))
        active_agents_data.append({
            "name": role_name,
            "short_desc": desc,
            # Consumed by the compact branch of templates/context/partials/
            # agents-table.md ({{#if COMPACT_MODE}}); computed unconditionally
            # so the loop expansion never leaves a literal {{keywords}} behind.
            "keywords": derive_keywords(desc),
            "addressability": addressability,
        })

    return active_agents_data


_LANGUAGE_ALIASES = {"en": "english", "de": "deutsch"}


def _normalize_language(value: object) -> str:
    """Normalize a language label: strip, casefold, resolve the ``en``/``de`` aliases."""
    text = str(value).strip().casefold()
    return _LANGUAGE_ALIASES.get(text, text)


def _find_language_variant(examples: dict, language: str) -> list | None:
    """Return the example list for ``language`` (exact key first, then normalized match).

    Single lookup shared by the selection and the fallback-log decision
    (``_select_examples``) — no second matching logic.
    """
    exact = examples.get(language)
    if isinstance(exact, list):
        return exact
    wanted = _normalize_language(language)
    for key, value in examples.items():
        if isinstance(value, list) and _normalize_language(key) == wanted:
            return value
    return None


def _note_examples_fallback(role: str, language: str, info_sink: list[str] | None) -> None:
    """Record the INFO ``routing.examples-language-fallback`` (log only, no render effect)."""
    message = (
        f"routing.examples-language-fallback: role '{role}' has no examples for "
        f"language '{language}'; using first variant"
    )
    if info_sink is not None:
        if message not in info_sink:
            info_sink.append(message)
        return
    from .log import SyncLog

    SyncLog().note("routing.examples-language-fallback", message)


def _select_examples(
    examples: object,
    language: str,
    *,
    role: str = "",
    info_sink: list[str] | None = None,
) -> list[str]:
    """Select language-appropriate routing examples (issue #780, design C).

    Design C keeps ``keywords`` canonical/language-neutral; language nuance
    lives in the free-text ``examples`` layer, rendered per the project's
    ``COMMUNICATION_LANGUAGE``.

    Data shapes: a flat list is the language-neutral form and passes through
    unchanged; a language-tagged mapping (``{"Deutsch": [...], "English":
    [...]}``) is resolved by ``language`` — exact key first, then a
    case-insensitive match that also resolves the ``en``/``de`` aliases (same
    normalization as the fallback log). A miss falls back deterministically to
    the first available list variant.

    Fallback visibility (IC-29, log only): when a mapping lacks ``language``,
    one ``routing.examples-language-fallback`` INFO message per role is added to
    ``info_sink`` (or the ``SyncLog`` fallback). The selected result is unchanged.

    ponytail: passthrough-only until bilingual data exists. Authoring the
    per-language ``examples`` content for all roles is separate, larger work
    (#780 AC-3 / #779 IT-4); this function is just the generator plumbing.
    """
    if isinstance(examples, dict):
        variant = _find_language_variant(examples, language)
        if variant is None:
            # Log only a genuine miss: needs a role and no variant under the
            # language's alias either ("fr" vs mapping keys "Deutsch"/"English").
            if role:
                _note_examples_fallback(role, language, info_sink)
            # Deterministic fallback: first list variant in insertion order.
            variant = next(
                (v for v in examples.values() if isinstance(v, list)), []
            )
        return [str(e) for e in variant]
    if isinstance(examples, list):
        return [str(e) for e in examples]
    return []


def _produced_contracts(roles: dict, active_names: list[str]) -> set[str]:
    """Contracts produced as ``output_contract`` by at least one active role.

    Local equivalent of ``ActiveSet.producers`` for callers without a shared
    ActiveSet (same data: ``handoff.output_contract`` of the active roles).
    """
    produced: set[str] = set()
    for name in active_names:
        handoff = (roles.get(name) or {}).get("handoff")
        contract = handoff.get("output_contract") if isinstance(handoff, dict) else None
        if contract:
            produced.add(str(contract))
    return produced


def get_routing_rules(
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    pipelines: dict | None = None,
    *,
    template_roles: set[str] | None = None,
    warn_sink: list[str] | None = None,
    language: str = "en",
    info_sink: list[str] | None = None,
    active_set: ActiveSet | None = None,
) -> dict:
    """Build structured routing rules for the native intent-routing tool (issue #264).

    Data layer of the #264 generation pipeline: resolves each active role's
    ``routing_patterns`` (``config/role-defaults.yaml`` → ``roles.<role>.routing_patterns``
    with ``keywords``/``examples``) into provider-neutral rule dicts. The
    emission layer (``agents.build_routing_tool_definition``) turns these into
    a tool definition; this function is deliberately format-agnostic.

    Resolution rules:

    - Roles without any patterns produce no rule (they are not keyword-routable)
      but still appear in ``target_agents`` — the tool's enum covers name-based
      dispatch too, mirroring the current prose table.
    - ``orchestrator`` is excluded entirely (anti-recursion: self-dispatch is a
      HARD REJECT, see orchestrator.md Singleton-Regel).
    - ``orchestrator_only`` roles keep their rule + flag: the tool's consumer
      IS the orchestrator; the escalation gate lives in the prompt/data, not here.
    - ``language`` (design C, issue #780) selects language-tagged ``examples``
      when a role provides a mapping; matching is case-insensitive and resolves
      the ``en``/``de`` aliases (see ``_select_examples``). Flat-list examples
      are a no-op passthrough. ``keywords`` stay canonical/language-neutral
      regardless. Callers thread the project's ``COMMUNICATION_LANGUAGE`` here.

    Returns:
        ``{"target_agents": [...], "rules": [...], "pipelines": [...],
        "name_index": [...]}`` —
        ``target_agents`` is the sorted enum of active non-orchestrator roles;
        ``rules`` carries ``agent/tier/parallel/orchestrator_only/keywords/
        examples/output_contract/input_contracts`` per routed role
        (``input_contracts`` reduced to contracts with an active producer) (sorted by
        agent name for deterministic, idempotent output); ``pipelines`` maps
        quality pipelines with ``signal_keywords`` to ``{"route": "pipeline",
        "pipeline": <name>, "keywords": [...]}`` entries (sorted by name);
        ``name_index`` carries ``agent/short_desc/tier/orchestrator_only/
        addressability/name_only_reason`` for every target role (sorted by
        ``agent``, including ``name_only`` roles).
    """
    roles_cfg = load_roles_config(agent_meta_root)
    roles = roles_cfg.get("roles", {})
    active_names = _active_role_names(
        agent_meta_root,
        config,
        variables,
        require_template=True,
        template_roles=template_roles,
        warn_sink=warn_sink,
        active_set=active_set,
    )
    target_agents = [name for name in active_names if name != "orchestrator"]
    # IC-18 no. 4: an input contract stays only if an active role (the
    # orchestrator included) produces it as its output_contract.
    produced = (
        {contract for contract, who in active_set.producers.items() if who}
        if active_set is not None
        else _produced_contracts(roles, active_names)
    )

    rules = []
    for role_name in target_agents:
        role_info = roles.get(role_name) or {}
        patterns = role_info.get("routing_patterns")
        patterns = patterns if isinstance(patterns, dict) else {}
        routing = role_info.get("routing")
        routing = routing if isinstance(routing, dict) else {}
        keywords = patterns.get("keywords")
        keywords = [str(k) for k in keywords] if isinstance(keywords, list) else []
        examples = _select_examples(
            patterns.get("examples"), language, role=role_name, info_sink=info_sink
        )
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
                str(c) for c in (handoff.get("input_contracts") or [])
                if str(c).strip() and str(c) in produced
            ],
        })

    name_index = []
    derived_warnings: set[str] = set()
    for role_name in target_agents:
        role_info = roles.get(role_name) or {}
        routing = role_info.get("routing")
        routing = routing if isinstance(routing, dict) else {}
        addressability, derived = _derive_addressability(role_info)
        if derived:
            derived_warnings.add(
                f"missing addressability, derived: {role_name}={addressability}"
            )
        name_index.append({
            "agent": role_name,
            "short_desc": role_info.get("short_desc", role_info.get("description", "")),
            "tier": role_info.get("workflow_tier", "optional"),
            "orchestrator_only": bool(routing.get("orchestrator_only", False)),
            "addressability": addressability,
            "name_only_reason": str(routing.get("name_only_reason") or ""),
        })
    name_index.sort(key=lambda entry: entry["agent"])
    _emit_warn_sink(derived_warnings, warn_sink)

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

    return {
        "target_agents": target_agents,
        "rules": rules,
        "pipelines": pipeline_rules,
        "name_index": name_index,
    }


def get_intent_routing_table(
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    pipelines: dict | None = None,
    *,
    template_roles: set[str] | None = None,
    warn_sink: list[str] | None = None,
    active_set: ActiveSet | None = None,
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
    active_agents_data = get_active_agents_data(
        agent_meta_root,
        config,
        variables,
        template_roles=template_roles,
        warn_sink=warn_sink,
        active_set=active_set,
    )
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
