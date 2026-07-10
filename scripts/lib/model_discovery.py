"""Model discovery for the agent-meta registry.

Fetches models from external endpoints (OpenRouter, OpenCode Go) and writes a
merged, deduplicated registry to ``config/generated/model-registry.json``.

Design notes:
    * Provider attribution uses the **exact prefix** of the model id
      (``provider/<name>``). No bucket heuristics are applied — the prefix is
      the provider.
    * OpenRouter models are filtered to ``ALLOWED_OPENROUTER_PROVIDER_PREFIXES``
      (currently ``anthropic`` only). Only Claude Code, Opencode Go, GitHub
      Copilot, and Continue are wired up in ``config/ai-providers.yaml``; all
      other upstream providers would be noise in the picker UI.
    * OpenCode Zen was removed — superseded by the OpenCode Go catalog.
      ``fetch_opencode_zen_models`` and ``OPENCODE_ZEN_URL`` remain for
      backward compatibility (tests, ad-hoc scripts) but are no longer called
      from :func:`discover_models`.
    * Anthropic models are sourced from
      ``https://platform.claude.com/docs/en/about-claude/models/overview.md``
      (the Claude Code platform docs, Markdown variant).  docs.anthropic.com
      is intentionally NOT used — it lists API-only models that Claude Code
      does not accept.  The HTML overview page is a SPA and uncrawlable from
      Python; the site serves a ``.md`` sibling at the same path which is
      fetched and parsed (see ``_parse_anthropic_markdown``).  On network
      failure the curated ``ANTHROPIC_FALLBACK_MODELS`` list is used.
    * Hard exclusion (blacklist) is sourced from ``config/model-curation.yaml``
      (see :mod:`scripts.lib.curation`), not from ``pricing-overlay.yaml``.
    * Network failures are non-fatal: each fetcher returns ``[]`` on error so
      sync runs degrade gracefully in offline environments.
"""

import json
import logging
import os
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/models"
OPENCODE_ZEN_URL = "https://opencode.ai/zen/v1/models"
OPENCODE_GO_URL = "https://opencode.ai/zen/go/v1/models"
ANTHROPIC_DOCS_URL = (
    "https://platform.claude.com/docs/en/about-claude/models/overview.md"
)
HTTP_TIMEOUT = 20

# Curated fallback for Anthropic model catalog.
# Source: https://platform.claude.com/docs/en/about-claude/models/overview.md
# Last verified: 2026-06-24
# Used when the live fetch fails (network error or non-markdown response).
# The format mirrors the registry dict produced by the other fetchers
# so ``discover_models`` can use the result transparently.
#
# ID conventions (per platform.claude.com/docs/en/about-claude/models/model-ids-and-versions):
#   * 4.6 generation and later: dateless pinned snapshot IDs (claude-{name}-{major}-{minor}).
#   * pre-4.6: dated IDs (claude-{name}-{major}-{minor}-{YYYYMMDD}), optionally aliased
#     to the dateless form on the Claude API.
# We use the canonical (dated for pre-4.6, dateless for 4.6+) IDs as primary
# and expose the pre-4.6 aliases as additional entries with ``name`` prefixed
# ``(alias)`` so they surface in the UI but are visually distinct.
ANTHROPIC_FALLBACK_MODELS: List[Dict[str, Any]] = [
    {
        "id": "claude-haiku-4-5-20251001",
        "name": "Claude Haiku 4.5",
        "provider": "anthropic",
        "input_cost_api": 1.00,
        "output_cost_api": 5.00,
        "context_length": 200000,
        "tier": "Standard",
    },
    {
        "id": "claude-haiku-4-5",
        "name": "(alias) Claude Haiku 4.5",
        "provider": "anthropic",
        "input_cost_api": 1.00,
        "output_cost_api": 5.00,
        "context_length": 200000,
        "tier": "Standard",
    },
    {
        "id": "claude-sonnet-4-6",
        "name": "Claude Sonnet 4.6",
        "provider": "anthropic",
        "input_cost_api": 3.00,
        "output_cost_api": 15.00,
        "context_length": 1000000,
        "tier": "Standard",
    },
    {
        "id": "claude-opus-4-8",
        "name": "Claude Opus 4.8",
        "provider": "anthropic",
        "input_cost_api": 5.00,
        "output_cost_api": 25.00,
        "context_length": 1000000,
        "tier": "Standard",
    },
    {
        "id": "claude-opus-4-7",
        "name": "Claude Opus 4.7",
        "provider": "anthropic",
        "input_cost_api": 5.00,
        "output_cost_api": 25.00,
        "context_length": 1000000,
        "tier": "Standard",
    },
    {
        "id": "claude-opus-4-6",
        "name": "Claude Opus 4.6",
        "provider": "anthropic",
        "input_cost_api": 5.00,
        "output_cost_api": 25.00,
        "context_length": 1000000,
        "tier": "Standard",
    },
    {
        "id": "claude-sonnet-4-5-20250929",
        "name": "Claude Sonnet 4.5",
        "provider": "anthropic",
        "input_cost_api": 3.00,
        "output_cost_api": 15.00,
        "context_length": 200000,
        "tier": "Standard",
    },
    {
        "id": "claude-sonnet-4-5",
        "name": "(alias) Claude Sonnet 4.5",
        "provider": "anthropic",
        "input_cost_api": 3.00,
        "output_cost_api": 15.00,
        "context_length": 200000,
        "tier": "Standard",
    },
    {
        "id": "claude-opus-4-5-20251101",
        "name": "Claude Opus 4.5",
        "provider": "anthropic",
        "input_cost_api": 5.00,
        "output_cost_api": 25.00,
        "context_length": 200000,
        "tier": "Standard",
    },
    {
        "id": "claude-opus-4-5",
        "name": "(alias) Claude Opus 4.5",
        "provider": "anthropic",
        "input_cost_api": 5.00,
        "output_cost_api": 25.00,
        "context_length": 200000,
        "tier": "Standard",
    },
    {
        "id": "claude-opus-4-1-20250805",
        "name": "Claude Opus 4.1 (deprecated, retires 2026-08-05)",
        "provider": "anthropic",
        "input_cost_api": 15.00,
        "output_cost_api": 75.00,
        "context_length": 200000,
        "tier": "Standard",
    },
    {
        "id": "claude-fable-5",
        "name": "Claude Fable 5",
        "provider": "anthropic",
        "input_cost_api": 10.00,
        "output_cost_api": 50.00,
        "context_length": 1000000,
        "tier": "Standard",
    },
    {
        "id": "claude-mythos-5",
        "name": "Claude Mythos 5",
        "provider": "anthropic",
        "input_cost_api": 10.00,
        "output_cost_api": 50.00,
        "context_length": 1000000,
        "tier": "Standard",
    },
    {
        "id": "claude-opus-4-1",
        "name": "(alias) Claude Opus 4.1 (deprecated, retires 2026-08-05)",
        "provider": "anthropic",
        "input_cost_api": 15.00,
        "output_cost_api": 75.00,
        "context_length": 200000,
        "tier": "Standard",
    },
]

# Only these OpenRouter provider prefixes are admitted to the registry. Adding
# a new provider here requires wiring it into ``config/ai-providers.yaml`` first.
ALLOWED_OPENROUTER_PROVIDER_PREFIXES: tuple = ("anthropic",)

# A browser-like User-Agent is required: opencode.ai returns HTTP 403 for the
# default urllib agent. OpenRouter works without it but is sent the same header
# for consistency and robustness.
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (agent-meta model-discovery)"}


def fetch_openrouter_models(
    blacklist: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Fetch models from the keyless OpenRouter API.

    The provider attribution is the exact prefix before the first ``/`` in the
    model id (e.g. ``qwen/qwen3-coder`` → provider ``qwen``). No bucket
    heuristics are applied; the prefix is authoritative.

    Args:
        blacklist: Optional list of model ids to exclude from the result.

    Returns:
        List of model dicts. Empty list on any network or parse error.
    """
    if blacklist is None:
        blacklist = []
    blacklist_set = set(blacklist)
    models: List[Dict[str, Any]] = []
    try:
        req = urllib.request.Request(OPENROUTER_URL, headers=HTTP_HEADERS)
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))

        for m in data.get("data", []):
            model_id = m.get("id", "")
            if not model_id or "/" not in model_id:
                continue
            if model_id in blacklist_set:
                continue

            provider = model_id.split("/", 1)[0]
            model_name = m.get("name") or model_id

            pricing = m.get("pricing", {}) or {}
            try:
                input_cost = float(pricing.get("prompt", 0)) * 1_000_000
            except (ValueError, TypeError):
                input_cost = 0.0
            try:
                output_cost = float(pricing.get("completion", 0)) * 1_000_000
            except (ValueError, TypeError):
                output_cost = 0.0

            context_length = m.get("context_length")

            models.append({
                "id": model_id,
                "name": model_name,
                "provider": provider,
                "input_cost_api": input_cost,
                "output_cost_api": output_cost,
                "context_length": context_length,
                "tier": "Standard",  # Fallback if needed by UI
            })
    except Exception as e:
        logger.error(f"fetch_openrouter_models failed: {e}")
        return []
    return models


def fetch_opencode_zen_models(
    blacklist: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Fetch models from the OpenCode Zen endpoint.

    The endpoint is keyless and returns a ``data[]`` array of model objects.
    Registry ids are namespaced as ``opencode/<raw_id>`` to keep them
    distinguishable from OpenRouter ids.

    Args:
        blacklist: Optional list of model ids (post-namespacing) to exclude.

    Returns:
        List of model dicts. Empty list on any network or parse error.
    """
    if blacklist is None:
        blacklist = []
    blacklist_set = set(blacklist)
    models: List[Dict[str, Any]] = []
    try:
        req = urllib.request.Request(OPENCODE_ZEN_URL, headers=HTTP_HEADERS)
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))

        for m in data.get("data", []):
            raw_id = m.get("id", "")
            if not raw_id:
                continue
            namespaced_id = f"opencode/{raw_id}"
            if namespaced_id in blacklist_set or raw_id in blacklist_set:
                continue

            display_name = raw_id.replace("-", " ").title()
            context_length = m.get("context_length")

            models.append({
                "id": namespaced_id,
                "name": display_name,
                "provider": "opencode-zen",
                "input_cost_api": 0.0,
                "output_cost_api": 0.0,
                "context_length": context_length,
                "tier": "Standard",
            })
    except Exception as e:
        logger.error(f"fetch_opencode_zen_models failed: {e}")
        return []
    return models


def fetch_opencode_go_models(
    blacklist: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Fetch models from the OpenCode Go endpoint.

    The endpoint is keyless and returns a ``data[]`` array of model objects.
    Registry ids are namespaced as ``opencode-go/<raw_id>`` to keep them
    distinguishable from OpenRouter and OpenCode Zen ids.

    Args:
        blacklist: Optional list of model ids (post-namespacing) to exclude.

    Returns:
        List of model dicts. Empty list on any network or parse error.
    """
    if blacklist is None:
        blacklist = []
    blacklist_set = set(blacklist)
    models: List[Dict[str, Any]] = []
    try:
        req = urllib.request.Request(OPENCODE_GO_URL, headers=HTTP_HEADERS)
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))

        for m in data.get("data", []):
            raw_id = m.get("id", "")
            if not raw_id:
                continue
            namespaced_id = f"opencode-go/{raw_id}"
            if namespaced_id in blacklist_set or raw_id in blacklist_set:
                continue

            display_name = raw_id.replace("-", " ").title()
            context_length = m.get("context_length")

            models.append({
                "id": namespaced_id,
                "name": display_name,
                "provider": "opencode-go",
                "input_cost_api": 0.0,
                "output_cost_api": 0.0,
                "context_length": context_length,
                "tier": "Standard",
            })
    except Exception as e:
        logger.error(f"fetch_opencode_go_models failed: {e}")
        return []
    return models


def _parse_anthropic_markdown(md_text: str) -> List[Dict[str, Any]]:
    """Parse the platform.claude.com ``overview.md`` table set.

    The page contains up to three GFM-style tables that list Claude models:
      1. **Fable 5 / Mythos 5** — 2 columns, pricing formatted as
         ``$X / $Y per MTok (input / output)``.
      2. **Latest models comparison** — 3 columns, pricing formatted as
         ``\\$X / input MTok<br/>\\$Y / output MTok``.
      3. **Legacy models** — 5 columns, same pricing format as #2.

    Each model column provides (a) a ``Claude API ID`` row, (b) an optional
    ``Claude API alias`` row, (c) a ``Pricing`` row, and (d) a
    ``Context window`` row.  The display name is taken from the column
    header (e.g. ``Claude Opus 4.8``).  Aliases are emitted as additional
    entries prefixed ``(alias)`` in the display name.

    Args:
        md_text: Raw markdown body of ``overview.md``.

    Returns:
        List of model dicts in the registry shape. Empty if the input
        contains no parseable model tables (e.g. SPA shell HTML).
    """
    import re

    models: List[Dict[str, Any]] = []
    if not md_text or "claude-" not in md_text:
        return models

    # Pre-pass: extract retirement dates for deprecated models from
    # <Warning> blocks. The model id's trailing YYYYMMDD is the *release*
    # date, not the retirement date, so the warning text is authoritative.
    retirement_dates: Dict[str, str] = {}
    for warn_match in re.finditer(
        r"<Warning[^>]*>(.*?)</Warning>", md_text, re.DOTALL
    ):
        block = warn_match.group(1)
        id_match = re.search(r"`(claude-[\w-]+)`", block)
        date_match = re.search(
            r"retired\s+on\s+(\w+\s+\d{1,2},\s*\d{4})", block
        )
        if not (id_match and date_match):
            continue
        try:
            from datetime import datetime
            dt = datetime.strptime(date_match.group(1), "%B %d, %Y")
            retirement_dates[id_match.group(1)] = dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Group consecutive "|..." lines into tables. Each table is a list of
    # raw pipe-delimited lines (header, separator, body rows).
    tables: List[List[str]] = []
    current: List[str] = []
    for line in md_text.splitlines():
        if line.lstrip().startswith("|"):
            current.append(line)
        else:
            if current:
                tables.append(current)
                current = []
    if current:
        tables.append(current)

    for table in tables:
        if len(table) < 3:
            continue
        header_cells = [c.strip() for c in table[0].split("|")[1:-1]]
        if len(header_cells) < 2 or header_cells[0].lower() != "feature":
            continue
        rows_by_label: Dict[str, List[str]] = {}
        for row in table[2:]:
            cells = [c.strip() for c in row.split("|")[1:-1]]
            if not cells:
                continue
            # Strip HTML tags (Tooltip, sup, etc.) and markdown link wrappers
            label = re.sub(r"<[^>]+>", "", cells[0])
            label = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", label)
            label = label.replace("**", "")
            # Strip trailing footnote markers ("1", "1, 2", "3,4")
            label = re.sub(r"[\d,\s]+$", "", label)
            label = label.strip().rstrip(":").lower()
            rows_by_label.setdefault(label, cells)

        if "claude api id" not in rows_by_label:
            continue

        id_cells = rows_by_label["claude api id"]
        alias_cells = rows_by_label.get("claude api alias", [])
        pricing_cells = rows_by_label.get("pricing", [])
        context_cells = rows_by_label.get("context window", [])

        for i in range(1, len(header_cells)):
            if i >= len(id_cells):
                break
            raw_id = id_cells[i].strip().strip("`").strip()
            if not raw_id.startswith("claude-"):
                continue

            header = re.sub(r"<[^>]+>", "", header_cells[i]).strip()
            display_name = header
            is_deprecated = "(deprecated)" in display_name
            display_name = display_name.replace("(deprecated)", "").strip()

            input_cost = 0.0
            output_cost = 0.0
            if i < len(pricing_cells):
                pcell = pricing_cells[i]
                # Format A: \$X / input MTok<br/>\$Y / output MTok
                m_in = re.search(
                    r"\$([0-9]+(?:\.[0-9]+)?)\s*/\s*input\s*MTok", pcell
                )
                m_out = re.search(
                    r"\$([0-9]+(?:\.[0-9]+)?)\s*/\s*output\s*MTok", pcell
                )
                if m_in and m_out:
                    input_cost = float(m_in.group(1))
                    output_cost = float(m_out.group(1))
                else:
                    # Format B: $X / $Y per MTok (input / output)
                    prices = re.findall(r"\$([0-9]+(?:\.[0-9]+)?)", pcell)
                    if len(prices) >= 2:
                        input_cost = float(prices[0])
                        output_cost = float(prices[1])

            if input_cost <= 0 or output_cost <= 0:
                continue

            context_length: Optional[int] = None
            if i < len(context_cells):
                ccell = context_cells[i]
                m = re.search(r"(\d+)([kKmM]?)\s*tokens", ccell)
                if m:
                    n = int(m.group(1))
                    unit = m.group(2).lower()
                    if unit == "k":
                        context_length = n * 1_000
                    elif unit == "m":
                        context_length = n * 1_000_000
                    else:
                        context_length = n

            if is_deprecated:
                retirement = retirement_dates.get(raw_id)
                if retirement:
                    display_name = f"{display_name} (deprecated, retires {retirement})"
                else:
                    display_name = f"{display_name} (deprecated)"

            models.append({
                "id": raw_id,
                "name": display_name,
                "provider": "anthropic",
                "input_cost_api": input_cost,
                "output_cost_api": output_cost,
                "context_length": context_length,
                "tier": "Standard",
            })

            if i < len(alias_cells):
                alias = alias_cells[i].strip().strip("`").strip()
                if alias and alias != raw_id and alias.startswith("claude-"):
                    models.append({
                        "id": alias,
                        "name": f"(alias) {display_name}",
                        "provider": "anthropic",
                        "input_cost_api": input_cost,
                        "output_cost_api": output_cost,
                        "context_length": context_length,
                        "tier": "Standard",
                    })

    return models


def fetch_anthropic_models(
    blacklist: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Fetch the canonical Anthropic model catalog from the Claude Code platform docs.

    The source is
    ``https://platform.claude.com/docs/en/about-claude/models/overview.md``
    (the Claude Code platform documentation, Markdown variant).  The HTML
    page ``overview`` is a JS-rendered SPA which ``urllib`` cannot parse;
    the site serves a ``.md`` sibling at the same path which contains the
    same content in plain Markdown — discovered 2026-06-24.

    We attempt a live fetch first and parse the markdown with
    :func:`_parse_anthropic_markdown`.  On any failure (network error,
    HTTP non-2xx, response body is HTML, or the parser returns 0 models)
    we fall back to the curated ``ANTHROPIC_FALLBACK_MODELS`` list, which
    is kept in lockstep with the docs.

    docs.anthropic.com is intentionally NOT used — it lists API-only
    models that Claude Code does not accept as ``model:`` values.

    The returned models use ``provider == "anthropic"`` (unprefixed).  The
    registry consumer (``_collect_models``-style code) is responsible for
    namespace-prefixing the id if needed.

    Args:
        blacklist: Optional list of model ids to exclude from the result.

    Returns:
        List of model dicts.  Never empty on a working install — the
        curated fallback always provides the canonical catalog.  Returns
        ``[]`` only if both the live fetch and the curated fallback are
        unavailable (e.g. ``ANTHROPIC_FALLBACK_MODELS`` was patched out in
        a test).
    """
    if blacklist is None:
        blacklist = []
    blacklist_set = set(blacklist)

    live_models: List[Dict[str, Any]] = []
    try:
        req = urllib.request.Request(ANTHROPIC_DOCS_URL, headers=HTTP_HEADERS)
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as response:
            ct = response.headers.get("Content-Type", "")
            body = response.read().decode("utf-8", errors="replace")
        if "markdown" not in ct.lower() and not body.lstrip().startswith("#"):
            logger.info(
                f"fetch_anthropic_models: live response Content-Type={ct!r} "
                "is not markdown — using curated fallback"
            )
        else:
            live_models = _parse_anthropic_markdown(body)
            if not live_models:
                logger.info(
                    "fetch_anthropic_models: markdown parser yielded 0 models "
                    "— using curated fallback"
                )
    except Exception as e:
        logger.info(
            f"fetch_anthropic_models: live fetch failed ({e}) — using curated fallback"
        )

    source_models = live_models if live_models else list(ANTHROPIC_FALLBACK_MODELS)
    models: List[Dict[str, Any]] = []
    for m in source_models:
        if m["id"] in blacklist_set:
            continue
        models.append(dict(m))

    if not live_models and models:
        logger.info(
            f"fetch_anthropic_models: serving {len(models)} models from "
            f"curated fallback (source: {ANTHROPIC_DOCS_URL})"
        )
    elif live_models:
        logger.info(
            f"fetch_anthropic_models: serving {len(models)} models from "
            f"live markdown fetch ({ANTHROPIC_DOCS_URL})"
        )
    return models


def _load_blacklist(project_root: str) -> List[str]:
    """Load the model blacklist from ``config/model-curation.yaml``.

    Falls back to an empty list if the file is missing or unreadable. The
    curation file is the single source of truth for hard exclusions; the legacy
    ``excluded_models`` key in ``pricing-overlay.yaml`` is no longer consulted.
    """
    try:
        from scripts.lib.curation import load_curation  # local import to avoid cycles
    except ImportError:
        try:
            from lib.curation import load_curation  # type: ignore[no-redef]
        except ImportError:
            logger.warning("curation module not importable — blacklist disabled")
            return []
    try:
        data = load_curation(project_root)
        blacklist = data.get("blacklist", []) or []
        if not isinstance(blacklist, list):
            logger.warning("model-curation.yaml: 'blacklist' is not a list — ignoring")
            return []
        return [str(x) for x in blacklist]
    except Exception as e:
        logger.error(f"Failed to load model-curation.yaml: {e}")
        return []


def discover_models(_project_root: Optional[str] = None) -> Dict[str, Any]:
    """Fetch all upstream models, merge, deduplicate and persist the registry.

    OpenRouter results are filtered to ``ALLOWED_OPENROUTER_PROVIDER_PREFIXES``
    (currently ``anthropic`` only). OpenCode Zen is intentionally not queried
    — the Go catalog supersedes it.

    Args:
        _project_root: Optional override for project root path (used in testing).

    Returns:
        The registry dict written to ``config/generated/model-registry.json``.
    """
    logger.info(
        "Discovering models from platform.claude.com (anthropic), "
        "OpenRouter (anthropic only) and OpenCode Go..."
    )
    if _project_root is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    else:
        project_root = _project_root

    blacklist = _load_blacklist(project_root)

    anthropic_models = fetch_anthropic_models(blacklist)
    or_models = fetch_openrouter_models(blacklist)
    # Restrict OpenRouter to providers we actually wire up in
    # ``config/ai-providers.yaml``. Today that's just ``anthropic``; if a new
    # provider is added there, extend ``ALLOWED_OPENROUTER_PROVIDER_PREFIXES``.
    or_models = [
        m for m in or_models
        if m.get("provider") in ALLOWED_OPENROUTER_PROVIDER_PREFIXES
    ]
    go_models = fetch_opencode_go_models(blacklist)

    # Prefer platform.claude.com for canonical anthropic/* ids and pricing.
    # OpenRouter is fallback for models not yet in the platform catalog
    # (e.g. freshly released, not yet scraped).  If the Anthropic fetcher
    # returns 0 models (network failure) the OpenRouter anthropic/* results
    # are used as-is (the historical behavior).
    if anthropic_models:
        platform_ids = {m["id"] for m in anthropic_models}
        # Drop OpenRouter entries that duplicate a platform.claude.com id.
        # OpenRouter spells versions with dots (anthropic/claude-opus-4.8)
        # while Claude Code ids use dashes (claude-opus-4-8) — normalize the
        # unprefixed OpenRouter id before comparing, otherwise every
        # duplicate would slip through and pollute the model picker with
        # ids Claude Code does not accept.
        or_models_filtered = [
            m for m in or_models
            if m.get("id", "").split("/", 1)[-1].replace(".", "-")
            not in platform_ids
        ]
    else:
        or_models_filtered = or_models

    all_models = anthropic_models + or_models_filtered + go_models

    # Deduplicate by id, keep first occurrence.
    seen: set = set()
    deduped: List[Dict[str, Any]] = []
    for m in all_models:
        mid = m.get("id")
        if not mid or mid in seen:
            continue
        seen.add(mid)
        deduped.append(m)

    registry_path = os.path.join(
        project_root, "config", "generated", "model-registry.json"
    )

    # Safety guard: don't overwrite a populated registry with an empty/tiny result
    # that is almost certainly caused by a network outage rather than real data.
    MIN_MODELS_TO_WRITE = 10
    if len(deduped) < MIN_MODELS_TO_WRITE:
        # Try to preserve the existing registry
        if os.path.exists(registry_path):
            with open(registry_path, encoding="utf-8") as _f:
                _existing = json.loads(_f.read())
            existing_count = len(_existing.get("models", []))
            if existing_count >= MIN_MODELS_TO_WRITE:
                logger.warning(
                    f"Discovery returned only {len(deduped)} models "
                    f"(existing registry has {existing_count}). "
                    "Possible network outage — registry NOT overwritten."
                )
                return _existing
        logger.warning(f"Discovery returned only {len(deduped)} models — writing anyway (no existing registry).")

    registry = {"models": deduped}
    os.makedirs(os.path.dirname(registry_path), exist_ok=True)
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)

    logger.info(
        f"Model registry updated at {registry_path} "
        f"(anthropic={len(anthropic_models)}, "
        f"openrouter-anthropic={len(or_models_filtered)}, "
        f"opencode-go={len(go_models)}, merged={len(deduped)})"
    )
    return registry


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    discover_models()
