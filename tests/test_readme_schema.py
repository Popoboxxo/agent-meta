"""Schema validation for the `readme` project.yaml block (issue #682 §3)."""

import json
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"

_MINIMAL_PROJECT = {"name": "demo", "prefix": "dm", "short": "demo"}


def _load_schema() -> dict:
    with _SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _readme_badges_schema() -> dict:
    return _load_schema()["properties"]["readme"]["properties"]["badges"]


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


def test_readme_badges_enum_contains_agent_meta_and_existing_types():
    """The schema enum lists the new opt-in type `agent-meta` next to the
    pre-existing types version/stack/license/ci
    (docs/concepts/agent-meta-version-badge.md §3.1/§3.2)."""
    enum = _readme_badges_schema()["items"]["enum"]
    for badge_type in ("version", "stack", "license", "ci", "agent-meta"):
        assert badge_type in enum


def test_readme_badges_default_keeps_agent_meta_off():
    """`agent-meta` stays opt-in: the default badge set is unchanged and does
    not contain `agent-meta` (docs/concepts/agent-meta-version-badge.md §3.2)."""
    badges = _readme_badges_schema()
    assert badges["default"] == ["version", "stack", "license"]
    assert "agent-meta" not in badges["default"]


def test_draft7_accepts_agent_meta_badge():
    """Draft7 validation (as used by scripts/lib/config.py) accepts an explicit
    `["agent-meta"]` opt-in; skipped cleanly when jsonschema is not installed."""
    jsonschema = pytest.importorskip("jsonschema")
    validator = jsonschema.Draft7Validator(_load_schema())
    validator.validate({"project": _MINIMAL_PROJECT, "readme": {"badges": ["agent-meta"]}})


def test_draft7_rejects_unknown_badge_type():
    """A typo like `agentmeta` is rejected by the enum; skipped cleanly when
    jsonschema is not installed (docs/concepts/agent-meta-version-badge.md §3.3)."""
    jsonschema = pytest.importorskip("jsonschema")
    validator = jsonschema.Draft7Validator(_load_schema())
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(
            {"project": _MINIMAL_PROJECT, "readme": {"badges": ["agentmeta"]}}
        )
