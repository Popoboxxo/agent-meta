"""Model discovery for the agent-meta registry.

Fetches models from external endpoints (OpenRouter, OpenCode Zen) and writes a
merged, deduplicated registry to ``config/generated/model-registry.json``.

Design notes:
    * Provider attribution uses the **exact prefix** of the model id
      (``provider/<name>``). No bucket heuristics are applied — the prefix is
      the provider.
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
HTTP_TIMEOUT = 20

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

    Args:
        _project_root: Optional override for project root path (used in testing).

    Returns:
        The registry dict written to ``config/generated/model-registry.json``.
    """
    logger.info("Discovering models from OpenRouter, OpenCode Zen and OpenCode Go...")
    if _project_root is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    else:
        project_root = _project_root

    blacklist = _load_blacklist(project_root)

    or_models = fetch_openrouter_models(blacklist)
    zen_models = fetch_opencode_zen_models(blacklist)
    go_models = fetch_opencode_go_models(blacklist)

    if not zen_models:
        logger.warning(
            "OpenCode Zen returned no models (network down or upstream error); "
            "continuing with OpenRouter-only registry."
        )

    all_models = or_models + zen_models + go_models

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
        f"(openrouter={len(or_models)}, opencode-zen={len(zen_models)}, "
        f"opencode-go={len(go_models)}, merged={len(deduped)})"
    )
    return registry


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    discover_models()
