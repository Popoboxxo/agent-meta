"""Schema shape tests for the release-checklist block (Task 1)."""

import json
from pathlib import Path

import pytest

SCHEMA = json.loads(
    (Path(__file__).resolve().parents[1] / "config" / "project-config.schema.json").read_text(
        encoding="utf-8"
    )
)
BLOCK = SCHEMA["properties"]["release-checklist"]
ITEM = BLOCK["properties"]["items"]["items"]


def test_block_shape():
    assert "default" not in BLOCK                                   # C9
    assert BLOCK["additionalProperties"] is False
    assert BLOCK["properties"]["mode"]["enum"] == ["strict", "advisory", "off"]


def test_item_shape():
    assert ITEM["required"] == ["id", "task", "verification"]
    assert ITEM["additionalProperties"] is False
    assert ITEM["properties"]["id"]["pattern"] == "^[a-z0-9][a-z0-9-]*$"
    assert ITEM["properties"]["check"]["enum"] == ["agent", "script"]
    assert ITEM["properties"]["phase"]["enum"] == ["precondition", "step"]
    assert ITEM["then"] == {"required": ["script"]}


def test_jsonschema_accepts_and_rejects():
    jsonschema = pytest.importorskip("jsonschema")
    ok = {"mode": "advisory", "items": [{"id": "a", "task": "t", "verification": "v"}]}
    jsonschema.validate(ok, BLOCK)
    for bad in ({"mode": "on"}, {"items": [{"id": "A", "task": "t", "verification": "v"}]},
                {"items": [{"id": "a", "task": "t", "verification": "v", "check": "script"}]},
                {"unknown": 1}):
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(bad, BLOCK)
