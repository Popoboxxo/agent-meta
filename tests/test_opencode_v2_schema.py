"""Schema tests for the Opencode v2 project options (Task 4 / B.1).

Spec: ``docs/specs/2026-10-22-opencode-v2-support-spec.md`` §3.1
(``SPEC-OPENCODE-V2-SUPPORT-2026-10-22``), Amendment B1 (2026-10-23).
Plan: ``docs/plans/2026-10-22-opencode-v2-support-plan.md``, Task 4.

Covers the schema part of AC-D3: the new keys
``experimental-subagent-depth``, ``experimental-todo``, ``providers``,
``model-variants`` and ``cli`` are accepted under
``provider-options.Opencode`` and keep the block closed.

Amendment B1 removes ``small-model`` (``agents.title.model`` is UNVERIFIED),
therefore the block must reject it as an unknown key. Per the plan there is no
dedicated small-model test any more, so that guard lives in
``test_unknown_key_rejected``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"


def _schema() -> dict:
    with _SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _config(**provider_options) -> dict:
    """Minimal valid project config with the given Opencode provider options."""
    return {
        "project": {"name": "t", "prefix": "t", "short": "t"},
        "ai-providers": ["Opencode"],
        "provider-options": {"Opencode": dict(provider_options)},
    }


def _validate(**provider_options) -> None:
    jsonschema.validate(_config(**provider_options), _schema())


def _opencode_properties() -> dict:
    props = _schema()["properties"]["provider-options"]["properties"]["Opencode"]
    return props


def test_valid_v2_configuration_accepted():
    """All five new keys, in their documented shape, validate."""
    _validate(
        **{
            "surface-version": "v2",
            "experimental-subagent-depth": 2,
            "experimental-todo": True,
            "providers": {
                "opencode-go": {
                    "name": "opencode-go",
                    "env": ["OC_API_KEY"],
                    "settings": {"baseURL": "https://example.invalid/v1"},
                }
            },
            "model-variants": {"developer": "high"},
            "cli": {"plugins": ["example-plugin"]},
        }
    )


def test_model_variant_with_space_rejected():
    """AC-D3: a variant is appended as ``#variant`` — blanks are not allowed."""
    with pytest.raises(jsonschema.ValidationError):
        _validate(**{"model-variants": {"developer": "hi gh"}})


def test_subagent_depth_zero_rejected():
    with pytest.raises(jsonschema.ValidationError):
        _validate(**{"experimental-subagent-depth": 0})


def test_provider_id_with_dot_rejected():
    """``providers`` is keyed by provider id; a dot is not a valid id."""
    with pytest.raises(jsonschema.ValidationError):
        _validate(**{"providers": {"a.b": {}}})


def test_unknown_key_rejected():
    """``additionalProperties: false`` stays — ``foo`` and the removed
    ``small-model`` (Amendment B1) are both unknown keys."""
    assert "small-model" not in _opencode_properties()["properties"]
    for key, value in (("foo", True), ("small-model", "deepseek")):
        with pytest.raises(jsonschema.ValidationError):
            _validate(**{key: value})
