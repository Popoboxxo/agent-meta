"""PR 4.1 / P26 (E-23): deterministic intent-routing artifacts.

Single-source helpers for the compact-by-default routing model:

- ``resolve_routing_format`` — capability/config driven format gate (``auto``
  means compact unless a callable ``route_intent`` tool exists). Decoupled from
  the global ``context-profile`` (W1/E-29): no global compact activation here.
- ``render_routing_name_index_line`` — reduced name_index (E2): agent + reason
  only, and dropped entirely when the roster is already in the harness.
- ``build_direct_dispatch_section`` — generated from ``direct_dispatch`` role
  metadata (AC-R7), replacing the static config copy.
- ``render_routing_detail`` / ``routing_detail_pointer`` — the lazy detail file
  and its single provider-agnostic pointer line (E6/AC-R4).

All functions are stdlib-only, Python 3.9 compatible and free of provider
literals. The data comes from ``config/role-defaults.yaml`` via the shared
``roles`` loader — no second source of truth.
"""
from __future__ import annotations

from pathlib import Path

from .io import SyncError
from .roles import load_roles_config

_VALID_FORMATS = frozenset({"auto", "compact", "json", "off"})
_ROUTING_DETAILS_BASENAME = "routing-details.md"


# ---------------------------------------------------------------------------
# Format gate — compact by default, independent of the global context profile
# ---------------------------------------------------------------------------

def resolve_routing_format(
    config: dict, provider: str, *, route_intent_tool: bool = False
) -> str:
    """Return the effective routing format: ``compact``/``json``/``off``.

    ``routing-overrides.format`` (default ``auto``) is the single switch:

    - ``auto`` → compact for providers without a callable ``route_intent``
      tool, json for providers that have one (capability-gated, never a
      provider-name branch);
    - ``compact`` / ``json`` / ``off`` are explicit choices;
    - an unknown value fails closed (``SyncError routing-overrides.format``).

    Per-provider overrides under ``provider-overrides.<provider>`` may narrow
    the top-level value using the same key domain.
    """
    overrides = config.get("routing-overrides") or {}
    if not isinstance(overrides, dict):
        raise SyncError("routing-overrides: expected a mapping")
    fmt = overrides.get("format", "auto")

    provider_overrides = config.get("provider-overrides") or {}
    per_provider = (
        provider_overrides.get(provider) if isinstance(provider_overrides, dict) else None
    )
    if isinstance(per_provider, dict) and "routing-overrides" in per_provider:
        sub = per_provider["routing-overrides"]
        if isinstance(sub, dict) and "format" in sub:
            fmt = sub["format"]

    fmt = str(fmt)
    if fmt not in _VALID_FORMATS:
        raise SyncError(
            f"routing-overrides.format: invalid value {fmt!r}; "
            f"expected one of {', '.join(sorted(_VALID_FORMATS))}"
        )
    if fmt == "off":
        return "off"
    if fmt == "compact":
        return "compact"
    if fmt == "json":
        return "json"
    return "json" if route_intent_tool else "compact"


# ---------------------------------------------------------------------------
# Reduced name_index (E2 / AC-R3)
# ---------------------------------------------------------------------------

def render_routing_name_index_line(
    name_index: list[dict], *, roster_in_harness: bool = False
) -> str:
    """Render the reduced name-dispatch fallback as one line.

    ``roster_in_harness=True`` drops the index completely — the harness already
    carries the agent names. Otherwise a single sorted ``name-only:`` line with
    only ``agent (reason)`` pairs remains; the legacy ``short_desc``/``tier``
    dump is gone.
    """
    if roster_in_harness:
        return ""
    entries = sorted(
        (
            str(entry.get("agent", "")),
            str(entry.get("name_only_reason") or ""),
        )
        for entry in name_index
        if entry.get("addressability") == "name_only"
    )
    if not entries:
        return ""
    return "name-only: " + "; ".join(
        f"{agent} ({reason})" for agent, reason in entries
    )


# ---------------------------------------------------------------------------
# Direct dispatch generated from role metadata (AC-R7)
# ---------------------------------------------------------------------------

_DD_HEADER = (
    "## Direkter Dispatch (nur nach Regel 2)\n\n"
    "| Operation | Direkt an | Bedingung |\n"
    "|-----------|-----------|-----------|"
)
_DD_FOOTER = "> **Faustregel:** >1 Tool-Call → Orchestrator. Unsicher → Orchestrator."


def build_direct_dispatch_section(root: Path, active_roles: set[str]) -> str:
    """Build the direct-dispatch table from ``routing.direct_dispatch`` roles.

    Only active roles with ``direct_dispatch: true`` produce a row; the
    framework metadata carries operation text, target and condition. Sorting
    by the optional ``direct_dispatch_order`` keeps the golden byte-stable.
    """
    roles = load_roles_config(root).get("roles", {})
    rows = []
    for name, info in roles.items():
        routing = info.get("routing") or {}
        if not isinstance(routing, dict) or routing.get("direct_dispatch") is not True:
            continue
        if name not in active_roles:
            continue
        order = routing.get("direct_dispatch_order", 999)
        if not isinstance(order, int) or isinstance(order, bool):
            order = 999
        rows.append((
            order,
            str(routing.get("direct_dispatch_operation", "")),
            name,
            str(routing.get("direct_dispatch_condition", "")),
        ))
    lines = [_DD_HEADER]
    for _order, operation, name, condition in sorted(rows, key=lambda row: (row[0], row[2])):
        lines.append(f"| {operation} | `{name}` | {condition} |")
    lines.extend(["", _DD_FOOTER])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Lazy routing detail file (E6 / AC-R4)
# ---------------------------------------------------------------------------

def render_routing_detail(rules: list[dict], *, root: Path | None = None) -> str:
    """Render the full per-role routing data into the on-demand detail doc.

    Compact lines carry only the leading example + intent/size/priority flags;
    this document is the single lazy companion holding every deferred field
    (all examples, keywords, contracts, priority, intents, size class).

    With ``root`` given, intents/size_class are enriched from the framework
    defaults (``routing.*``) so the detail file stays the single full-field
    artifact even though the compact inline block omits them.
    """
    if root is not None:
        roles = load_roles_config(root).get("roles", {})
        enriched = []
        for rule in rules:
            item = dict(rule)
            routing = (roles.get(str(item.get("agent", ""))) or {}).get("routing") or {}
            if isinstance(routing, dict):
                item.setdefault("intents", routing.get("intents") or [])
                item.setdefault("size_class", routing.get("size_class") or "M")
            enriched.append(item)
        rules = enriched
    if not rules:
        return "# Routing-Details\n"
    lines = [
        "# Routing-Details",
        "",
        "Vollständige Routing-Regeln. Nur bei Bedarf lesen — der Always-on-Block "
        "im Orchestrator enthält die kompakte Zeilenform.",
        "",
    ]
    for rule in sorted(rules, key=lambda entry: str(entry.get("agent", ""))):
        agent = str(rule.get("agent", ""))
        intents = ", ".join(str(i) for i in (rule.get("intents") or [])) or "—"
        size_class = str(rule.get("size_class") or "M")
        priority = rule.get("priority")
        priority_text = f"p{priority}" if isinstance(priority, int) and not isinstance(priority, bool) else "—"
        keywords = ", ".join(str(k) for k in (rule.get("keywords") or [])) or "—"
        examples = "; ".join(str(e) for e in (rule.get("examples") or [])) or "—"
        output_contract = str(rule.get("output_contract") or "—")
        input_contracts = ", ".join(
            str(c) for c in (rule.get("input_contracts") or [])
        ) or "—"
        lines.extend([
            f"## {agent}",
            "",
            "| Feld | Wert |",
            "|------|------|",
            f"| intents | {intents} |",
            f"| size_class | {size_class} |",
            f"| priority | {priority_text} |",
            f"| keywords | {keywords} |",
            f"| examples | {examples} |",
            f"| output_contract | {output_contract} |",
            f"| input_contracts | {input_contracts} |",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def resolve_routing_detail_path(provider_config: dict, provider: str) -> str:
    """Return the provider-agnostic relative path of the lazy detail file.

    Mirrors ``resolve_pipeline_details_dir``: explicit ``routing_detail_file``
    wins, otherwise the file sits beside ``agents_dir`` as a sibling.
    """
    explicit = provider_config.get("routing_detail_file")
    if explicit:
        return str(explicit)
    agents_dir = provider_config.get("agents_dir", f".{provider.lower()}/agents")
    return str(Path(agents_dir).parent / _ROUTING_DETAILS_BASENAME)


def routing_detail_pointer(agents_dir: str) -> str:
    """Single provider-agnostic pointer line for the orchestrator prompt.

    ``agents_dir`` is provider *data* (never a hardcoded provider name); the
    pointer always resolves to ``<agents_dir>/../routing-details.md``.
    """
    path = str(Path(agents_dir).parent / _ROUTING_DETAILS_BASENAME)
    return (
        f"Volle Routing-Details (Intents, alle Beispiele, Priorität, Contracts) "
        f"bei Bedarf: `Read {path}`."
    )
