"""test-environments config schema (issue #1089): per-project test targets.

The JSON schema is additive only (C8); hard validation lives in the Python
validator. The block must not carry a top-level ``default`` (C9) because
``--fill-defaults`` would otherwise write it into every ``project.yaml``.
"""

import json
from pathlib import Path

import jsonschema
import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"


def _schema() -> dict:
    with _SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _cfg(envs: dict) -> dict:
    return {
        "project": {"name": "t", "prefix": "t", "short": "t"},
        "ai-providers": ["Claude"],
        "roles": ["orchestrator", "developer", "git"],
        "test-environments": envs,
    }


def test_schema_has_block_without_toplevel_default():
    prop = _schema()["properties"]["test-environments"]
    assert "default" not in prop
    assert prop["propertyNames"] == {"pattern": "^[a-z0-9][a-z0-9-]*$"}
    item = prop["additionalProperties"]
    assert item["additionalProperties"] is False
    assert item["properties"]["kind"]["enum"] == ["local", "remote", "both"]
    assert item["properties"]["access"]["enum"] == ["read", "deploy"]
    assert item["properties"]["remote-access"]["enum"] == ["deny", "ask", "allow"]
    assert item["properties"]["token-env"]["pattern"] == "^[A-Z][A-Z0-9_]*$"
    assert item["properties"]["url"]["minLength"] == 1
    assert "environments" in prop["description"] and "secret: true" in prop["description"]   # AC-ENV-17


def test_spec_example_validates():
    jsonschema.validate(_cfg({"ha-dev": {"kind": "both", "url": "http://ha-dev.lan:8123", "token-env": "HA_DEV_TOKEN",
                                        "access": "deploy", "remote-access": "ask", "notes": "x"},
                              "sharkord-local": {"kind": "local", "notes": "y"}}), _schema())


@pytest.mark.parametrize("bad", [{"kind": "remoteish"}, {"access": "write"}, {"remote-access": "maybe"},
                                 {"remote-access": False}, {"token-env": "lowercase"}, {"colour": "red"}, {"url": ""}])
def test_invalid_entry_rejected(bad):
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_cfg({"a": bad}), _schema())


def test_invalid_name_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_cfg({"Bad_Name": {}}), _schema())
