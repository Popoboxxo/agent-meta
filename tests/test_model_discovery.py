"""Tests for scripts.lib.model_discovery (keyless OpenRouter + OpenCode Zen/Go).

Network is mocked via unittest.mock — no real HTTP requests are made.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from scripts.lib.model_discovery import (
    ANTHROPIC_FALLBACK_MODELS,
    _parse_anthropic_markdown,
    discover_models,
    fetch_anthropic_models,
    fetch_opencode_go_models,
    fetch_opencode_zen_models,
    fetch_openrouter_models,
)


# -- Helpers ------------------------------------------------------------------


def _make_urlopen_mock(payload):
    """Return a MagicMock that mimics urllib.request.urlopen() as a context manager."""
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    cm = MagicMock()
    cm.__enter__.return_value = response
    cm.__exit__.return_value = False
    return cm


def _sample_openrouter_payload():
    return {
        "data": [
            {
                "id": "anthropic/claude-3.5-sonnet",
                "name": "Claude 3.5 Sonnet",
                "pricing": {"prompt": "0.000003", "completion": "0.000015"},
            },
            {
                "id": "google/gemini-2.0-flash",
                "name": "Gemini 2.0 Flash",
                "pricing": {"prompt": "0.0000001", "completion": "0.0000004"},
            },
            {
                "id": "openai/gpt-4o",
                "name": "GPT-4o",
                "pricing": {"prompt": "0.0000025", "completion": "0.00001"},
            },
            {
                "id": "mistralai/mistral-large",
                "name": "Mistral Large",
                "pricing": {"prompt": "0.000002", "completion": "0.000006"},
            },
            {
                "id": "deprecated/model-x",
                "name": "Deprecated Model X",
                "pricing": {"prompt": "0", "completion": "0"},
            },
        ]
    }


def _sample_opencode_zen_payload():
    return {
        "data": [
            {"id": "deepseek-v4-flash-free", "context_length": 128000},
            {"id": "qwen3.6-plus", "context_length": 128000},
            {"id": "kimi-k2.6", "context_length": 200000},
        ]
    }


def _sample_opencode_go_payload():
    return {
        "data": [
            {"id": "deepseek-v4-flash", "context_length": 128000},
            {"id": "kimi-k2.6", "context_length": 200000},
            {"id": "qwen3.6-plus", "context_length": 128000},
        ]
    }


# -- fetch_openrouter_models: provider mapping (literal prefix) ---------------


def test_fetch_openrouter_models_provider_mapping_is_literal_prefix():
    payload = _sample_openrouter_payload()
    with patch("urllib.request.urlopen", return_value=_make_urlopen_mock(payload)):
        models = fetch_openrouter_models()

    by_id = {m["id"]: m for m in models}
    # Provider is the literal prefix before the first slash — no bucket heuristic.
    assert by_id["anthropic/claude-3.5-sonnet"]["provider"] == "anthropic"
    assert by_id["google/gemini-2.0-flash"]["provider"] == "google"
    assert by_id["openai/gpt-4o"]["provider"] == "openai"
    assert by_id["mistralai/mistral-large"]["provider"] == "mistralai"


# -- fetch_openrouter_models: blacklist ---------------------------------------


def test_fetch_openrouter_models_respects_blacklist():
    payload = _sample_openrouter_payload()
    blacklist = ["deprecated/model-x", "openai/gpt-4o"]
    with patch("urllib.request.urlopen", return_value=_make_urlopen_mock(payload)):
        models = fetch_openrouter_models(blacklist=blacklist)

    ids = {m["id"] for m in models}
    assert "deprecated/model-x" not in ids
    assert "openai/gpt-4o" not in ids
    assert "anthropic/claude-3.5-sonnet" in ids


# -- fetch_openrouter_models: cost scaling ------------------------------------


def test_fetch_openrouter_models_cost_scaling():
    payload = _sample_openrouter_payload()
    with patch("urllib.request.urlopen", return_value=_make_urlopen_mock(payload)):
        models = fetch_openrouter_models()

    by_id = {m["id"]: m for m in models}
    # 0.000003 $/token * 1_000_000 = 3.0 $/1M
    assert by_id["anthropic/claude-3.5-sonnet"]["input_cost_api"] == pytest.approx(3.0)
    assert by_id["anthropic/claude-3.5-sonnet"]["output_cost_api"] == pytest.approx(15.0)
    # 0.0000025 $/token * 1_000_000 = 2.5 $/1M
    assert by_id["openai/gpt-4o"]["input_cost_api"] == pytest.approx(2.5)
    assert by_id["openai/gpt-4o"]["output_cost_api"] == pytest.approx(10.0)


# -- fetch_openrouter_models: network error returns [] ------------------------


def test_fetch_openrouter_models_network_error_returns_empty():
    with patch("urllib.request.urlopen", side_effect=OSError("network down")):
        models = fetch_openrouter_models()
    assert models == []


# -- fetch_opencode_zen_models: namespacing and provider tag ------------------


def test_fetch_opencode_zen_models_namespaces_ids():
    payload = _sample_opencode_zen_payload()
    with patch("urllib.request.urlopen", return_value=_make_urlopen_mock(payload)):
        models = fetch_opencode_zen_models()

    ids = {m["id"] for m in models}
    assert "opencode/deepseek-v4-flash-free" in ids
    assert "opencode/qwen3.6-plus" in ids
    assert "opencode/kimi-k2.6" in ids

    for m in models:
        assert m["provider"] == "opencode-zen"
        assert m["id"].startswith("opencode/")


def test_fetch_opencode_zen_models_blacklist_matches_both_forms():
    payload = _sample_opencode_zen_payload()
    # Blacklist by both raw id and namespaced id forms.
    blacklist = ["kimi-k2.6", "opencode/qwen3.6-plus"]
    with patch("urllib.request.urlopen", return_value=_make_urlopen_mock(payload)):
        models = fetch_opencode_zen_models(blacklist=blacklist)

    ids = {m["id"] for m in models}
    assert "opencode/kimi-k2.6" not in ids
    assert "opencode/qwen3.6-plus" not in ids
    assert "opencode/deepseek-v4-flash-free" in ids


def test_fetch_opencode_zen_models_network_error_returns_empty():
    with patch("urllib.request.urlopen", side_effect=OSError("network down")):
        models = fetch_opencode_zen_models()
    assert models == []


# -- fetch_opencode_go_models: namespacing and provider tag -------------------


def test_fetch_opencode_go_models_namespaces_ids():
    payload = _sample_opencode_go_payload()
    with patch("urllib.request.urlopen", return_value=_make_urlopen_mock(payload)):
        models = fetch_opencode_go_models()

    ids = {m["id"] for m in models}
    assert "opencode-go/deepseek-v4-flash" in ids
    assert "opencode-go/kimi-k2.6" in ids
    assert "opencode-go/qwen3.6-plus" in ids

    for m in models:
        assert m["provider"] == "opencode-go"
        assert m["id"].startswith("opencode-go/")
        assert m["input_cost_api"] == 0.0
        assert m["output_cost_api"] == 0.0


def test_fetch_opencode_go_models_blacklist_matches_both_forms():
    payload = _sample_opencode_go_payload()
    # Blacklist by both raw id and namespaced id forms.
    blacklist = ["kimi-k2.6", "opencode-go/qwen3.6-plus"]
    with patch("urllib.request.urlopen", return_value=_make_urlopen_mock(payload)):
        models = fetch_opencode_go_models(blacklist=blacklist)

    ids = {m["id"] for m in models}
    assert "opencode-go/kimi-k2.6" not in ids
    assert "opencode-go/qwen3.6-plus" not in ids
    assert "opencode-go/deepseek-v4-flash" in ids


def test_fetch_opencode_go_models_network_error_returns_empty():
    with patch("urllib.request.urlopen", side_effect=OSError("network down")):
        models = fetch_opencode_go_models()
    assert models == []


# -- discover_models ----------------------------------------------------------


def test_discover_models_merges_openrouter_anthropic_and_go(tmp_path, monkeypatch):
    """Only OpenRouter models with an allowed provider prefix are merged.

    OpenCode Zen is intentionally not queried any more — see the
    ALLOWED_OPENROUTER_PROVIDER_PREFIXES constant in model_discovery.py.
    The platform.claude.com catalog (``fetch_anthropic_models``) is patched
    out here so the test exercises the OpenRouter path in isolation.
    """
    or_fetched = [
        {
            "id": "anthropic/claude-test",
            "name": "Claude Test",
            "provider": "anthropic",
            "input_cost_api": 1.0,
            "output_cost_api": 2.0,
            "tier": "Standard",
        },
        {
            "id": "openai/gpt-test",
            "name": "GPT Test",
            "provider": "openai",
            "input_cost_api": 0.5,
            "output_cost_api": 1.5,
            "tier": "Standard",
        },
    ]
    go_fetched = [
        {
            "id": "opencode-go/deepseek-v4-flash",
            "name": "Deepseek V4 Flash",
            "provider": "opencode-go",
            "input_cost_api": 0.0,
            "output_cost_api": 0.0,
            "tier": "Standard",
        },
    ]

    with patch(
        "scripts.lib.model_discovery.fetch_anthropic_models",
        return_value=[],
    ), patch(
        "scripts.lib.model_discovery.fetch_openrouter_models",
        return_value=list(or_fetched),
    ), patch(
        "scripts.lib.model_discovery.fetch_opencode_go_models",
        return_value=list(go_fetched),
    ):
        registry = discover_models(_project_root=str(tmp_path))

    assert isinstance(registry, dict)
    assert "models" in registry

    ids = [m["id"] for m in registry["models"]]
    providers = {m["provider"] for m in registry["models"]}

    # Allowed OpenRouter prefix is admitted.
    assert "anthropic/claude-test" in ids
    # Non-allowed OpenRouter prefix is dropped.
    assert "openai/gpt-test" not in ids
    assert "openai" not in providers
    # Go catalog is still merged.
    assert "opencode-go/deepseek-v4-flash" in ids
    assert "opencode-go" in providers
    # Only the allowed provider + opencode-go survive.
    assert providers <= {"anthropic", "opencode-go"}


def test_discover_models_deduplicates_by_id(tmp_path):
    duplicated = [
        {
            "id": "anthropic/claude-test",
            "name": "Claude Test A",
            "provider": "anthropic",
            "input_cost_api": 1.0,
            "output_cost_api": 2.0,
            "tier": "Standard",
        },
        {
            "id": "anthropic/claude-test",
            "name": "Claude Test B",  # second occurrence should be dropped
            "provider": "anthropic",
            "input_cost_api": 9.0,
            "output_cost_api": 9.0,
            "tier": "Standard",
        },
    ]

    with patch(
        "scripts.lib.model_discovery.fetch_anthropic_models",
        return_value=[],
    ), patch(
        "scripts.lib.model_discovery.fetch_openrouter_models",
        return_value=list(duplicated),
    ), patch(
        "scripts.lib.model_discovery.fetch_opencode_zen_models",
        return_value=[],
    ), patch(
        "scripts.lib.model_discovery.fetch_opencode_go_models",
        return_value=[],
    ):
        registry = discover_models(_project_root=str(tmp_path))

    matching = [m for m in registry["models"] if m["id"] == "anthropic/claude-test"]
    assert len(matching) == 1
    assert matching[0]["name"] == "Claude Test A"


def test_discover_models_platform_claude_preferred_over_openrouter(tmp_path, monkeypatch):
    """When the platform.claude.com catalog returns >=1 model, OpenRouter
    entries whose unprefixed id matches a platform id are dropped (the
    platform source is canonical for ids and pricing)."""
    platform = [
        {
            "id": "claude-haiku-4-5-20251001",
            "name": "Claude Haiku 4.5",
            "provider": "anthropic",
            "input_cost_api": 1.0,
            "output_cost_api": 5.0,
            "tier": "Standard",
        },
        {
            "id": "claude-opus-4-8",
            "name": "Claude Opus 4.8",
            "provider": "anthropic",
            "input_cost_api": 5.0,
            "output_cost_api": 25.0,
            "tier": "Standard",
        },
    ]
    or_fetched = [
        # Same id (unprefixed) — must be dropped in favor of platform entry.
        {
            "id": "anthropic/claude-opus-4-8",
            "name": "OR Claude Opus 4.8 (stale)",
            "provider": "anthropic",
            "input_cost_api": 9.0,
            "output_cost_api": 9.0,
            "tier": "Standard",
        },
        # Brand-new model not yet in the platform catalog — must survive.
        {
            "id": "anthropic/claude-future-9",
            "name": "Claude Future 9",
            "provider": "anthropic",
            "input_cost_api": 7.0,
            "output_cost_api": 35.0,
            "tier": "Standard",
        },
    ]

    with patch(
        "scripts.lib.model_discovery.fetch_anthropic_models",
        return_value=list(platform),
    ), patch(
        "scripts.lib.model_discovery.fetch_openrouter_models",
        return_value=list(or_fetched),
    ), patch(
        "scripts.lib.model_discovery.fetch_opencode_go_models",
        return_value=[],
    ):
        registry = discover_models(_project_root=str(tmp_path))

    ids = [m["id"] for m in registry["models"]]
    # Platform ids present
    assert "claude-haiku-4-5-20251001" in ids
    assert "claude-opus-4-8" in ids
    # OpenRouter duplicate of a platform id is dropped.
    assert "anthropic/claude-opus-4-8" not in ids
    # OpenRouter-only model is kept.
    assert "anthropic/claude-future-9" in ids

    # The platform entry wins for id and pricing.
    opus = next(m for m in registry["models"] if m["id"] == "claude-opus-4-8")
    assert opus["input_cost_api"] == 5.0
    assert opus["output_cost_api"] == 25.0
    assert opus["name"] == "Claude Opus 4.8"


def test_discover_models_drops_dot_notation_openrouter_duplicates(tmp_path):
    """OpenRouter spells versions with dots (anthropic/claude-opus-4.8);
    Claude Code ids use dashes (claude-opus-4-8). The dedup must normalize
    dots to dashes before comparing, otherwise dot-notation duplicates
    pollute the registry with ids Claude Code does not accept."""
    platform = [
        {
            "id": "claude-opus-4-8",
            "name": "Claude Opus 4.8",
            "provider": "anthropic",
            "input_cost_api": 5.0,
            "output_cost_api": 25.0,
            "tier": "Standard",
        },
    ]
    or_fetched = [
        # Dot-notation duplicate of a platform id — must be dropped.
        {
            "id": "anthropic/claude-opus-4.8",
            "name": "Anthropic: Claude Opus 4.8",
            "provider": "anthropic",
            "input_cost_api": 9.0,
            "output_cost_api": 9.0,
            "tier": "Standard",
        },
        # Dot-notation model without a platform counterpart — must survive.
        {
            "id": "anthropic/claude-opus-4.8-fast",
            "name": "Anthropic: Claude Opus 4.8 (Fast)",
            "provider": "anthropic",
            "input_cost_api": 9.0,
            "output_cost_api": 9.0,
            "tier": "Standard",
        },
    ]

    with patch(
        "scripts.lib.model_discovery.fetch_anthropic_models",
        return_value=list(platform),
    ), patch(
        "scripts.lib.model_discovery.fetch_openrouter_models",
        return_value=list(or_fetched),
    ), patch(
        "scripts.lib.model_discovery.fetch_opencode_go_models",
        return_value=[],
    ):
        registry = discover_models(_project_root=str(tmp_path))

    ids = [m["id"] for m in registry["models"]]
    assert "claude-opus-4-8" in ids
    assert "anthropic/claude-opus-4.8" not in ids
    assert "anthropic/claude-opus-4.8-fast" in ids


def test_discover_models_falls_back_to_openrouter_when_platform_empty(tmp_path, monkeypatch):
    """If the platform.claude.com fetcher returns 0 models (network failure),
    OpenRouter anthropic/* results are used as-is (legacy behavior)."""
    or_fetched = [
        {
            "id": "anthropic/claude-fallback",
            "name": "Claude Fallback",
            "provider": "anthropic",
            "input_cost_api": 1.0,
            "output_cost_api": 2.0,
            "tier": "Standard",
        },
    ]

    with patch(
        "scripts.lib.model_discovery.fetch_anthropic_models",
        return_value=[],
    ), patch(
        "scripts.lib.model_discovery.fetch_openrouter_models",
        return_value=list(or_fetched),
    ), patch(
        "scripts.lib.model_discovery.fetch_opencode_go_models",
        return_value=[],
    ):
        registry = discover_models(_project_root=str(tmp_path))

    ids = [m["id"] for m in registry["models"]]
    assert "anthropic/claude-fallback" in ids


def test_discover_models_does_not_overwrite_on_empty_result(tmp_path, monkeypatch):
    """If all fetchers return [] but a populated registry exists, it must be preserved."""
    import os
    from scripts.lib import model_discovery as md

    # Create a pre-existing registry with enough models
    registry_dir = tmp_path / "config" / "generated"
    registry_dir.mkdir(parents=True)
    existing_models = [{"id": f"x/model-{i}", "provider": "x", "name": f"Model {i}"} for i in range(20)]
    existing = {"models": existing_models}
    registry_file = registry_dir / "model-registry.json"
    registry_file.write_text(json.dumps(existing))

    # Patch fetchers to return empty
    monkeypatch.setattr(md, "fetch_anthropic_models", lambda blacklist=None: [])
    monkeypatch.setattr(md, "fetch_openrouter_models", lambda blacklist=None: [])
    monkeypatch.setattr(md, "fetch_opencode_zen_models", lambda blacklist=None: [])
    monkeypatch.setattr(md, "fetch_opencode_go_models", lambda blacklist=None: [])
    monkeypatch.setattr(md, "_load_blacklist", lambda project_root: [])

    # Capture the real os.path.join before patching
    real_join = os.path.join

    def mock_join(*args):
        """Route registry path to temp location, pass through others."""
        result = real_join(*args)
        if "model-registry.json" in result:
            return str(registry_file)
        return result

    monkeypatch.setattr(md.os.path, "join", mock_join)

    result = discover_models()

    # Should return existing registry unchanged
    assert len(result.get("models", [])) == 20
    # Registry file should still have 20 models
    on_disk = json.loads(registry_file.read_text())
    assert len(on_disk.get("models", [])) == 20


# -- fetch_anthropic_models ---------------------------------------------------


def test_fetch_anthropic_models_uses_curated_fallback():
    """The docs page is SPA-rendered; urllib gets the shell, not the table.
    The fetcher falls back to ANTHROPIC_FALLBACK_MODELS regardless."""
    from scripts.lib.model_discovery import ANTHROPIC_DOCS_URL

    # Pretend urllib returns the SPA shell (no model ids in the body).
    spa_shell = "<html><body><div id='__next'></div></body></html>"
    response = MagicMock()
    response.read.return_value = spa_shell.encode("utf-8")
    cm = MagicMock()
    cm.__enter__.return_value = response
    cm.__exit__.return_value = False
    with patch("urllib.request.urlopen", return_value=cm):
        models = fetch_anthropic_models()

    assert len(models) > 0
    assert all(m["provider"] == "anthropic" for m in models)
    # Latest model must be present
    ids = {m["id"] for m in models}
    assert "claude-opus-4-8" in ids
    assert "claude-fable-5" in ids
    assert "claude-haiku-4-5-20251001" in ids
    # Sanity: URL constant points at the platform (NOT docs.anthropic.com).
    assert ANTHROPIC_DOCS_URL.startswith("https://platform.claude.com/")


def test_fetch_anthropic_models_respects_blacklist():
    blacklist = ["claude-fable-5", "claude-opus-4-1-20250805"]
    models = fetch_anthropic_models(blacklist=blacklist)
    ids = {m["id"] for m in models}
    assert "claude-fable-5" not in ids
    assert "claude-opus-4-1-20250805" not in ids
    assert "claude-haiku-4-5-20251001" in ids
    assert "claude-opus-4-8" in ids


def test_fetch_anthropic_models_pricing_shape():
    """Each model has both input_cost_api and output_cost_api as positive floats."""
    models = fetch_anthropic_models()
    for m in models:
        assert isinstance(m["input_cost_api"], (int, float))
        assert isinstance(m["output_cost_api"], (int, float))
        assert m["input_cost_api"] > 0
        assert m["output_cost_api"] > 0
        # Output tokens cost more than input tokens (industry convention).
        assert m["output_cost_api"] >= m["input_cost_api"]


def test_fetch_anthropic_models_fallback_in_sync_with_docs():
    """The curated fallback must reflect the verified pricing from
    platform.claude.com/docs/en/about-claude/models/overview (2026-06-24)."""
    by_id = {m["id"]: m for m in ANTHROPIC_FALLBACK_MODELS}
    # Current generation
    assert by_id["claude-haiku-4-5-20251001"]["input_cost_api"] == pytest.approx(1.0)
    assert by_id["claude-haiku-4-5-20251001"]["output_cost_api"] == pytest.approx(5.0)
    assert by_id["claude-sonnet-4-6"]["input_cost_api"] == pytest.approx(3.0)
    assert by_id["claude-sonnet-4-6"]["output_cost_api"] == pytest.approx(15.0)
    assert by_id["claude-opus-4-8"]["input_cost_api"] == pytest.approx(5.0)
    assert by_id["claude-opus-4-8"]["output_cost_api"] == pytest.approx(25.0)
    assert by_id["claude-fable-5"]["input_cost_api"] == pytest.approx(10.0)
    assert by_id["claude-fable-5"]["output_cost_api"] == pytest.approx(50.0)
    # Deprecated
    assert by_id["claude-opus-4-1-20250805"]["input_cost_api"] == pytest.approx(15.0)
    assert by_id["claude-opus-4-1-20250805"]["output_cost_api"] == pytest.approx(75.0)
    # Mythos 5 (added 2026-06-09, not in older snapshots of the fallback)
    assert by_id["claude-mythos-5"]["input_cost_api"] == pytest.approx(10.0)
    assert by_id["claude-mythos-5"]["output_cost_api"] == pytest.approx(50.0)


# -- _parse_anthropic_markdown / live .md endpoint ----------------------------


# Minimal but representative slice of platform.claude.com/docs/.../overview.md
# (2026-06-24). Contains all three table formats the parser must handle:
#   1. Fable 5 / Mythos 5:  pricing="$X / $Y per MTok (input / output)"
#   2. Latest:              pricing="\$X / input MTok<br/>\$Y / output MTok"
#   3. Legacy:              pricing="\$X / input MTok<br/>\$Y / output MTok"
_SAMPLE_OVERVIEW_MD = """# Models overview

### Claude Fable 5 and Claude Mythos 5

| Feature | Claude Fable 5 | Claude Mythos 5 |
|:--------|:-------------|:-------------|
| **Claude API ID** | `claude-fable-5` | `claude-mythos-5` |
| **Pricing** | $10 / $50 per MTok (input / output) | $10 / $50 per MTok (input / output) |
| **Context window** | <Tooltip>1M tokens</Tooltip> | <Tooltip>1M tokens</Tooltip> |

### Latest models comparison

| Feature | Claude Opus 4.8 | Claude Sonnet 4.6 | Claude Haiku 4.5 |
|:--------|:-------------|:------------------|:-----------------|
| **Claude API ID** | claude-opus-4-8 | claude-sonnet-4-6 | claude-haiku-4-5-20251001 |
| **Claude API alias** | claude-opus-4-8 | claude-sonnet-4-6 | claude-haiku-4-5 |
| **Pricing** | \\$5 / input MTok<br/>\\$25 / output MTok | \\$3 / input MTok<br/>\\$15 / output MTok | \\$1 / input MTok<br/>\\$5 / output MTok |
| **Context window** | <Tooltip>1M tokens</Tooltip> | <Tooltip>1M tokens</Tooltip> | <Tooltip>200k tokens</Tooltip> |

<section title="Legacy models">

| Feature | Claude Opus 4.7 | Claude Opus 4.6 | Claude Sonnet 4.5 | Claude Opus 4.5 | Claude Opus 4.1 (deprecated) |
|:--------|:----------------|:----------------|:------------------|:----------------|:----------------|
| **Claude API ID** | claude-opus-4-7 | claude-opus-4-6 | claude-sonnet-4-5-20250929 | claude-opus-4-5-20251101 | claude-opus-4-1-20250805 |
| **Claude API alias** | claude-opus-4-7 | claude-opus-4-6 | claude-sonnet-4-5 | claude-opus-4-5 | claude-opus-4-1 |
| **Pricing** | \\$5 / input MTok<br/>\\$25 / output MTok | \\$5 / input MTok<br/>\\$25 / output MTok | \\$3 / input MTok<br/>\\$15 / output MTok | \\$5 / input MTok<br/>\\$25 / output MTok | \\$15 / input MTok<br/>\\$75 / output MTok |
| **Context window** | <Tooltip>1M tokens</Tooltip> | <Tooltip>1M tokens</Tooltip> | <Tooltip>200k tokens</Tooltip> | <Tooltip>200k tokens</Tooltip> | <Tooltip>200k tokens</Tooltip> |

<Warning>
Claude Opus 4.1 (`claude-opus-4-1-20250805`) is deprecated and will be retired on August 5, 2026.
</Warning>

</section>
"""


def test_parse_anthropic_markdown_extracts_all_three_tables():
    models = _parse_anthropic_markdown(_SAMPLE_OVERVIEW_MD)
    ids = {m["id"] for m in models}
    # Fable/Mythos table (format B pricing)
    assert "claude-fable-5" in ids
    assert "claude-mythos-5" in ids
    # Latest table (format A pricing)
    assert "claude-opus-4-8" in ids
    assert "claude-sonnet-4-6" in ids
    assert "claude-haiku-4-5-20251001" in ids
    # Legacy table (format A pricing)
    assert "claude-opus-4-7" in ids
    assert "claude-opus-4-6" in ids
    assert "claude-sonnet-4-5-20250929" in ids
    assert "claude-opus-4-5-20251101" in ids
    assert "claude-opus-4-1-20250805" in ids


def test_parse_anthropic_markdown_format_a_pricing():
    """Format A: \\$X / input MTok<br/>\\$Y / output MTok (Latest + Legacy)."""
    models = _parse_anthropic_markdown(_SAMPLE_OVERVIEW_MD)
    by_id = {m["id"]: m for m in models}

    assert by_id["claude-opus-4-8"]["input_cost_api"] == pytest.approx(5.0)
    assert by_id["claude-opus-4-8"]["output_cost_api"] == pytest.approx(25.0)
    assert by_id["claude-sonnet-4-6"]["input_cost_api"] == pytest.approx(3.0)
    assert by_id["claude-sonnet-4-6"]["output_cost_api"] == pytest.approx(15.0)
    assert by_id["claude-haiku-4-5-20251001"]["input_cost_api"] == pytest.approx(1.0)
    assert by_id["claude-haiku-4-5-20251001"]["output_cost_api"] == pytest.approx(5.0)
    assert by_id["claude-opus-4-1-20250805"]["input_cost_api"] == pytest.approx(15.0)
    assert by_id["claude-opus-4-1-20250805"]["output_cost_api"] == pytest.approx(75.0)


def test_parse_anthropic_markdown_format_b_pricing():
    """Format B: $X / $Y per MTok (input / output) (Fable/Mythos table)."""
    models = _parse_anthropic_markdown(_SAMPLE_OVERVIEW_MD)
    by_id = {m["id"]: m for m in models}

    assert by_id["claude-fable-5"]["input_cost_api"] == pytest.approx(10.0)
    assert by_id["claude-fable-5"]["output_cost_api"] == pytest.approx(50.0)
    assert by_id["claude-mythos-5"]["input_cost_api"] == pytest.approx(10.0)
    assert by_id["claude-mythos-5"]["output_cost_api"] == pytest.approx(50.0)


def test_parse_anthropic_markdown_context_window_units():
    """Context window is parsed with k/M unit multipliers."""
    models = _parse_anthropic_markdown(_SAMPLE_OVERVIEW_MD)
    by_id = {m["id"]: m for m in models}

    # 1M tokens → 1_000_000
    assert by_id["claude-opus-4-8"]["context_length"] == 1_000_000
    assert by_id["claude-sonnet-4-6"]["context_length"] == 1_000_000
    assert by_id["claude-fable-5"]["context_length"] == 1_000_000
    # 200k tokens → 200_000
    assert by_id["claude-haiku-4-5-20251001"]["context_length"] == 200_000
    assert by_id["claude-opus-4-1-20250805"]["context_length"] == 200_000


def test_parse_anthropic_markdown_creates_alias_entries():
    """Each model with a non-empty alias gets an additional '(alias)' entry."""
    models = _parse_anthropic_markdown(_SAMPLE_OVERVIEW_MD)
    by_id = {m["id"]: m for m in models}

    # Aliases that differ from the canonical id
    assert "claude-haiku-4-5" in by_id
    assert "claude-sonnet-4-5" in by_id
    assert "claude-opus-4-5" in by_id
    assert "claude-opus-4-1" in by_id
    # Aliases identical to canonical id are NOT emitted a second time
    assert sum(1 for m in models if m["id"] == "claude-opus-4-8") == 1
    # Aliases share the canonical entry's pricing
    assert by_id["claude-haiku-4-5"]["input_cost_api"] == pytest.approx(1.0)
    assert by_id["claude-haiku-4-5"]["output_cost_api"] == pytest.approx(5.0)
    # Alias names are prefixed '(alias) '
    assert by_id["claude-haiku-4-5"]["name"].startswith("(alias) ")


def test_parse_anthropic_markdown_marks_deprecated_models():
    models = _parse_anthropic_markdown(_SAMPLE_OVERVIEW_MD)
    by_id = {m["id"]: m for m in models}

    # Date suffix on canonical id is used as the retirement date
    assert "deprecated, retires 2026-08-05" in by_id["claude-opus-4-1-20250805"]["name"]
    # Alias for a deprecated model carries the same suffix
    assert "deprecated, retires 2026-08-05" in by_id["claude-opus-4-1"]["name"]


def test_parse_anthropic_markdown_returns_empty_for_spa_shell():
    """The HTML overview page (SPA shell) has no pipe tables — empty result."""
    spa_shell = (
        "<!doctype html><html><body>"
        "<div id='__next'></div>"
        "<p>Loading Claude platform…</p>"
        "</body></html>"
    )
    assert _parse_anthropic_markdown(spa_shell) == []


def test_parse_anthropic_markdown_ignores_non_claude_columns():
    """A table without a 'Claude API ID' row is skipped (e.g. unrelated GFM table)."""
    unrelated = (
        "| Feature | A | B |\n"
        "|:--------|:-|:-|\n"
        "| **Note** | x | y |\n"
    )
    assert _parse_anthropic_markdown(unrelated) == []


def test_fetch_anthropic_models_uses_live_markdown_endpoint():
    """fetch_anthropic_models hits the .md endpoint and parses the response."""
    response = MagicMock()
    response.read.return_value = _SAMPLE_OVERVIEW_MD.encode("utf-8")
    response.headers.get.return_value = "text/markdown; charset=utf-8"
    cm = MagicMock()
    cm.__enter__.return_value = response
    cm.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=cm) as mocked:
        models = fetch_anthropic_models()

    # Endpoint is the .md variant
    from scripts.lib.model_discovery import ANTHROPIC_DOCS_URL
    assert ANTHROPIC_DOCS_URL.endswith("/overview.md")
    assert mocked.called
    args, _ = mocked.call_args
    assert args[0].full_url == ANTHROPIC_DOCS_URL
    # All tables represented in the sample are surfaced
    ids = {m["id"] for m in models}
    assert "claude-fable-5" in ids
    assert "claude-mythos-5" in ids
    assert "claude-opus-4-8" in ids
    assert "claude-haiku-4-5" in ids
    assert "claude-opus-4-1-20250805" in ids


def test_fetch_anthropic_models_falls_back_on_network_error():
    """When the live fetch raises (e.g. offline), the curated list is served."""
    with patch("urllib.request.urlopen", side_effect=OSError("network down")):
        models = fetch_anthropic_models()
    assert len(models) > 0
    assert all(m["provider"] == "anthropic" for m in models)
    # Must contain canonical entries from the fallback
    ids = {m["id"] for m in models}
    assert "claude-opus-4-8" in ids
    assert "claude-fable-5" in ids


def test_fetch_anthropic_models_falls_back_on_non_markdown_response():
    """If the live response is HTML (SPA shell slipped through), fall back."""
    spa_shell = b"<html><body><div id='__next'></div></body></html>"
    response = MagicMock()
    response.read.return_value = spa_shell
    response.headers.get.return_value = "text/html; charset=utf-8"
    cm = MagicMock()
    cm.__enter__.return_value = response
    cm.__exit__.return_value = False
    with patch("urllib.request.urlopen", return_value=cm):
        models = fetch_anthropic_models()
    # Parser yields nothing for SPA shell; fallback kicks in
    assert len(models) > 0
    assert "claude-opus-4-8" in {m["id"] for m in models}
