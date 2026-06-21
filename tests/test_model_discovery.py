"""Tests for scripts.lib.model_discovery (keyless OpenRouter API).

Network is mocked via unittest.mock — no real HTTP requests are made.
"""

import json
import numbers
from unittest.mock import MagicMock, patch

import pytest

from scripts.lib.model_discovery import (
    OPENCODE_GO_MODELS,
    discover_models,
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


# -- OPENCODE_GO_MODELS structure --------------------------------------------


def test_opencode_go_models_structure():
    assert isinstance(OPENCODE_GO_MODELS, list)
    assert len(OPENCODE_GO_MODELS) >= 1
    for m in OPENCODE_GO_MODELS:
        assert isinstance(m, dict)
        assert isinstance(m["id"], str) and m["id"]
        assert isinstance(m["name"], str) and m["name"]
        assert m["provider"] == "opencode-go"
        assert isinstance(m["input_cost_api"], numbers.Real)
        assert isinstance(m["output_cost_api"], numbers.Real)
        assert m["input_cost_api"] >= 0
        assert m["output_cost_api"] >= 0


# -- fetch_openrouter_models: provider mapping --------------------------------


def test_fetch_openrouter_models_provider_mapping():
    payload = _sample_openrouter_payload()
    with patch("urllib.request.urlopen", return_value=_make_urlopen_mock(payload)):
        models = fetch_openrouter_models()

    by_id = {m["id"]: m for m in models}
    assert by_id["anthropic/claude-3.5-sonnet"]["provider"] == "anthropic"
    assert by_id["google/gemini-2.0-flash"]["provider"] == "gemini"
    assert by_id["openai/gpt-4o"]["provider"] == "openai"
    assert by_id["mistralai/mistral-large"]["provider"] == "opencode-go"


# -- fetch_openrouter_models: excluded_models ---------------------------------


def test_fetch_openrouter_models_excludes_models():
    payload = _sample_openrouter_payload()
    excluded = ["deprecated/model-x", "openai/gpt-4o"]
    with patch("urllib.request.urlopen", return_value=_make_urlopen_mock(payload)):
        models = fetch_openrouter_models(excluded_models=excluded)

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


# -- discover_models ----------------------------------------------------------


def test_discover_models_contains_all_opencode_and_fetched(tmp_path, monkeypatch):
    fetched = [
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

    # Patch the network-hitting function at the module level so discover_models
    # uses the stub instead of doing a real fetch.
    with patch(
        "scripts.lib.model_discovery.fetch_openrouter_models",
        return_value=list(fetched),
    ):
        registry = discover_models()

    assert isinstance(registry, dict)
    assert "models" in registry

    ids = [m["id"] for m in registry["models"]]
    # Every OPENCODE_GO_MODELS entry must be present
    for m in OPENCODE_GO_MODELS:
        assert m["id"] in ids
    # Fetched models must also be present
    for m in fetched:
        assert m["id"] in ids
