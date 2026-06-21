import pytest
import os
import json
from scripts.lib.model_discovery import (
    fetch_anthropic_models,
    fetch_gemini_models,
    fetch_opencode_models,
    discover_models
)

def test_fetch_anthropic_models():
    models = fetch_anthropic_models()
    assert isinstance(models, list)
    assert len(models) == 3
    for m in models:
        assert m["provider"] == "anthropic"
        assert "id" in m
        assert "tier" in m

def test_fetch_gemini_models():
    models = fetch_gemini_models()
    assert isinstance(models, list)
    assert len(models) == 2
    for m in models:
        assert m["provider"] == "gemini"
        assert "id" in m
        assert "tier" in m

def test_fetch_opencode_models():
    models = fetch_opencode_models()
    assert isinstance(models, list)
    assert len(models) == 2
    for m in models:
        assert m["provider"] == "opencode"
        assert "id" in m
        assert "tier" in m

def test_discover_models():
    registry = discover_models()
    assert isinstance(registry, dict)
    assert "models" in registry
    assert len(registry["models"]) == 7
