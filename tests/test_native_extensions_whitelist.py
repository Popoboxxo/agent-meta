"""Tests for the orchestrator.native-extensions.whitelist config path."""
from pathlib import Path
import json

import pytest

from scripts.lib.config import build_variables

_AGENT_META_ROOT = Path(__file__).resolve().parent.parent


def test_schema_has_native_extensions_whitelist_property():
    schema_path = _AGENT_META_ROOT / "config" / "project-config.schema.json"
    with schema_path.open(encoding="utf-8") as f:
        schema = json.load(f)
    ne_schema = schema["properties"]["orchestrator"]["properties"]["native-extensions"]
    wl_schema = ne_schema["properties"]["whitelist"]
    assert wl_schema["type"] == "array"
    assert wl_schema["items"]["type"] == "string"
    assert wl_schema["default"] == []
    assert wl_schema["uniqueItems"] is True
    assert "Ist die Whitelist nicht leer" in wl_schema["description"]


def _minimal_config(**overrides) -> dict:
    config = {
        "project": {"name": "test-proj", "prefix": "tp", "short": "test-proj"},
        "ai-providers": ["Claude"],
    }
    config.update(overrides)
    return config


def test_build_variables_whitelist_inactive_when_absent():
    variables, _ = build_variables(_minimal_config(), _AGENT_META_ROOT)
    assert variables["NATIVE_EXTENSIONS_WHITELIST_ACTIVE"] == "false"
    assert variables["NATIVE_EXTENSIONS_WHITELIST_TABLE"] == ""


def test_build_variables_whitelist_inactive_when_empty_list():
    config = _minimal_config(orchestrator={"native-extensions": {"enabled": True, "whitelist": []}})
    variables, _ = build_variables(config, _AGENT_META_ROOT)
    assert variables["NATIVE_EXTENSIONS_WHITELIST_ACTIVE"] == "false"
    assert variables["NATIVE_EXTENSIONS_WHITELIST_TABLE"] == ""


def test_build_variables_whitelist_active_with_entries():
    config = _minimal_config(orchestrator={
        "native-extensions": {"enabled": True, "whitelist": ["superpowers", "code-simplifier"]},
    })
    variables, _ = build_variables(config, _AGENT_META_ROOT)
    assert variables["NATIVE_EXTENSIONS_WHITELIST_ACTIVE"] == "true"
    assert variables["NATIVE_EXTENSIONS_WHITELIST_TABLE"] == "- `superpowers`\n- `code-simplifier`"
