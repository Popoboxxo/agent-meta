"""Tests for scripts.lib.model_discovery (keyless OpenRouter + OpenCode Zen).

Network is mocked via unittest.mock — no real HTTP requests are made.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from scripts.lib.model_discovery import (
    discover_models,
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


# -- discover_models ----------------------------------------------------------


def test_discover_models_merges_openrouter_and_zen(tmp_path, monkeypatch):
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
    zen_fetched = [
        {
            "id": "opencode/qwen3.6-plus",
            "name": "Qwen3.6 Plus",
            "provider": "opencode-zen",
            "input_cost_api": 0.0,
            "output_cost_api": 0.0,
            "tier": "Standard",
        },
    ]

    with patch(
        "scripts.lib.model_discovery.fetch_openrouter_models",
        return_value=list(or_fetched),
    ), patch(
        "scripts.lib.model_discovery.fetch_opencode_zen_models",
        return_value=list(zen_fetched),
    ):
        registry = discover_models()

    assert isinstance(registry, dict)
    assert "models" in registry

    ids = [m["id"] for m in registry["models"]]
    for m in or_fetched + zen_fetched:
        assert m["id"] in ids


def test_discover_models_deduplicates_by_id():
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
        "scripts.lib.model_discovery.fetch_openrouter_models",
        return_value=list(duplicated),
    ), patch(
        "scripts.lib.model_discovery.fetch_opencode_zen_models",
        return_value=[],
    ):
        registry = discover_models()

    matching = [m for m in registry["models"] if m["id"] == "anthropic/claude-test"]
    assert len(matching) == 1
    assert matching[0]["name"] == "Claude Test A"
