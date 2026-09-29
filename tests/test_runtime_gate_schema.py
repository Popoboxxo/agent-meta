"""Schema tests for the runtime-gate configuration keys.

SPEC-OPENCODE-RUNTIME-GATE-2026-09-13:

- AC-14: ``orchestrator.require-runtime-gate`` (IC-12) is a typed boolean
  sibling key of ``orchestrator.strict`` (which is itself a boolean, D-C2);
  a non-boolean is rejected; absence resolves to ``false``.
- AC-24: ``runtime-gate.plugin-mode`` (IC-16) is a typed enum
  (``observe``/``enforce``) under a closed ``runtime-gate`` root block;
  a missing key resolves to ``observe``.

Run: python -m pytest tests/test_runtime_gate_schema.py -v
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


def _config(**extra) -> dict:
    base = {
        "project": {"name": "t", "prefix": "t", "short": "t"},
        "ai-providers": ["Claude"],
    }
    base.update(extra)
    return base


def _orchestrator_props() -> dict:
    return _schema()["properties"]["orchestrator"]["properties"]


def _runtime_gate_schema() -> dict:
    return _schema()["properties"]["runtime-gate"]


# --- AC-14: orchestrator.require-runtime-gate --------------------------------


@pytest.mark.parametrize("value", [True, False])
def test_require_runtime_gate_boolean_accepted(value):
    jsonschema.validate(
        _config(orchestrator={"require-runtime-gate": value}), _schema()
    )


def test_require_runtime_gate_non_boolean_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(orchestrator={"require-runtime-gate": "yes"}), _schema()
        )


def test_require_runtime_gate_absent_defaults_false():
    jsonschema.validate(_config(orchestrator={"mode": "strict"}), _schema())
    require_schema = _orchestrator_props()["require-runtime-gate"]
    assert require_schema["type"] == "boolean"
    assert require_schema["default"] is False


def test_require_runtime_gate_is_sibling_not_nested_under_strict():
    """D-C2: ``orchestrator.strict`` is a boolean, so the opt-in is a sibling key."""
    assert _orchestrator_props()["strict"]["type"] == "boolean"
    assert "require-runtime-gate" in _orchestrator_props()


# --- AC-24: runtime-gate.plugin-mode -----------------------------------------


@pytest.mark.parametrize("mode", ["observe", "enforce"])
def test_plugin_mode_valid(mode):
    jsonschema.validate(
        _config(**{"runtime-gate": {"plugin-mode": mode}}), _schema()
    )


def test_plugin_mode_out_of_enum_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(**{"runtime-gate": {"plugin-mode": "audit"}}), _schema()
        )


def test_plugin_mode_non_string_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(**{"runtime-gate": {"plugin-mode": 1}}), _schema()
        )


def test_plugin_mode_missing_defaults_to_observe():
    jsonschema.validate(_config(**{"runtime-gate": {}}), _schema())
    plugin_mode = _runtime_gate_schema()["properties"]["plugin-mode"]
    assert plugin_mode["default"] == "observe"
    assert plugin_mode["enum"] == ["observe", "enforce"]


def test_runtime_gate_unknown_sibling_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(**{"runtime-gate": {"plugin-mode": "observe", "extra": 1}}),
            _schema(),
        )
