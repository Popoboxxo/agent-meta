"""Schema validation for the `readme` project.yaml block (issue #682 §3)."""

import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"


def _load_schema() -> dict:
    with _SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def test_schema_is_valid_json():
    _load_schema()  # raises json.JSONDecodeError on malformed schema


def test_readme_block_defined_with_expected_defaults():
    schema = _load_schema()
    readme = schema["properties"]["readme"]
    assert readme["type"] == "object"
    badges = readme["properties"]["badges"]
    assert badges["type"] == "array"
    assert badges["default"] == ["version", "stack", "license"]
    warnings = readme["properties"]["warnings"]
    assert warnings["type"] == "boolean"
    assert warnings["default"] is False
    sections = readme["properties"]["sections"]
    assert sections["type"] == "array"
    assert sections["default"] == ["description", "badges", "setup", "structure"]


def test_readme_block_rejects_unknown_keys():
    schema = _load_schema()
    assert schema["properties"]["readme"]["additionalProperties"] is False
