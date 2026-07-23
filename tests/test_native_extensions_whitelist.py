"""Tests for the orchestrator.native-extensions.whitelist config path."""
from pathlib import Path
import json

import pytest

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
