"""Schema tests for the orchestrator position axis (``orchestrator.topology``).

SPEC-orchestrator-topology-2026-11-03, P1 (issue #1077), Task 5.

IC-1 contract:

* ``orchestrator.topology`` is an optional string enum
  ``primary | subagent | hybrid``. It describes **where** the orchestrator
  lives; ``orchestrator.mode`` describes **how strictly** its gate is
  enforced. Omission preserves today's derivation, therefore the key carries
  **no** schema ``default``.
* ``orchestrator.provider-overrides.<P>.topology`` shares the enum and is the
  second property of an otherwise closed per-provider object
  (``additionalProperties: false`` stays).
* ``context_file.topology`` is a different axis (file layout) and its
  description says so.

Run: python3 -m pytest tests/test_orchestrator_topology_schema.py -q
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"

_TOPOLOGIES = ["primary", "subagent", "hybrid"]
_MODES = ["strict", "advisory", "main-chat"]


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


def _orchestrator_schema() -> dict:
    return _schema()["properties"]["orchestrator"]


def _orchestrator_props() -> dict:
    return _orchestrator_schema()["properties"]


def _override_schema() -> dict:
    return _orchestrator_props()["provider-overrides"]


# --- orchestrator.topology ---------------------------------------------------


def test_topology_enum_declares_exactly_the_three_positions():
    topology = _orchestrator_props()["topology"]
    assert topology["type"] == "string"
    assert topology["enum"] == _TOPOLOGIES


@pytest.mark.parametrize("value", _TOPOLOGIES)
def test_topology_each_valid_value_accepted(value):
    jsonschema.validate(_config(orchestrator={"topology": value}), _schema())


def test_topology_out_of_enum_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(orchestrator={"topology": "hybrid2"}), _schema()
        )


def test_topology_has_no_schema_default():
    """IC-1: the default is the existing derivation, never a schema literal."""
    assert "default" not in _orchestrator_props()["topology"]


def test_topology_description_names_position_axis_and_mode_values():
    description = _orchestrator_props()["topology"]["description"]
    lowered = description.lower()
    # "where" vs "how strictly" — the two orthogonal axes.
    assert "where" in lowered
    assert "strict" in lowered and "advisory" in lowered and "main-chat" in lowered
    for value in _TOPOLOGIES:
        assert value in description
    # Omission preserves today's derivation (no behaviour change, D9).
    assert "derived" in lowered or "derivation" in lowered
    # Distinguishes the sibling mode axis explicitly.
    assert "orchestrator.mode" in description


def test_context_file_topology_description_distinguishes_agent_topology():
    description = _schema()["properties"]["context_file"]["properties"][
        "topology"
    ]["description"]
    lowered = description.lower()
    assert "not" in lowered and "agent" in lowered
    assert "orchestrator.topology" in description


# --- orchestrator.provider-overrides.<P>.topology ---------------------------


def test_provider_override_topology_shares_enum():
    override = _override_schema()["additionalProperties"]
    assert "topology" in override["properties"]
    assert override["properties"]["topology"]["enum"] == _TOPOLOGIES
    assert override["properties"]["mode"]["enum"] == _MODES


def test_provider_override_accepts_topology_next_to_mode():
    jsonschema.validate(
        _config(
            orchestrator={
                "provider-overrides": {
                    "Opencode": {"mode": "strict", "topology": "primary"}
                }
            }
        ),
        _schema(),
    )


def test_provider_override_out_of_enum_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(
                orchestrator={
                    "provider-overrides": {"Opencode": {"topology": "hybrid2"}}
                }
            ),
            _schema(),
        )


def test_provider_override_object_stays_closed():
    override = _override_schema()["additionalProperties"]
    assert override["additionalProperties"] is False


# --- orchestrator.max-instances / orchestrator.singleton (P3, AC-8/AC-12) ----


def test_max_instances_declares_integer_one_to_eight_default_one():
    max_instances = _orchestrator_props()["max-instances"]
    assert max_instances["type"] == "integer"
    assert max_instances["minimum"] == 1
    assert max_instances["maximum"] == 8
    assert max_instances["default"] == 1


@pytest.mark.parametrize("value", [1, 2, 8])
def test_max_instances_accepts_in_range_values(value):
    jsonschema.validate(
        _config(orchestrator={"max-instances": value}), _schema()
    )


@pytest.mark.parametrize("value", [0, 9, -1])
def test_max_instances_rejects_out_of_range_values(value):
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(orchestrator={"max-instances": value}), _schema()
        )


def test_singleton_is_a_presence_only_alias_without_schema_default():
    """IC-1/D5: enum [true] and deliberately NO ``default`` key.

    Presence distinguishes "explicitly set" from "defaulted"; a schema default
    would make the key look declared on every project.
    """
    singleton = _orchestrator_props()["singleton"]
    assert singleton["enum"] == [True]
    assert "default" not in singleton


def test_singleton_true_is_accepted():
    jsonschema.validate(
        _config(orchestrator={"singleton": True}), _schema()
    )


def test_singleton_false_is_rejected_by_the_enum():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(orchestrator={"singleton": False}), _schema()
        )


def test_consistent_multi_instance_config_validates():
    jsonschema.validate(
        _config(orchestrator={"max-instances": 8, "singleton": True}),
        _schema(),
    )


def test_max_instances_description_distinguishes_max_parallel_agents():
    """AC-12: number of orchestrators vs parallelism inside one orchestrator."""
    description = _orchestrator_props()["max-instances"]["description"]
    lowered = description.lower()
    assert "max-parallel-agents" in description
    assert "orchestrator" in lowered
    assert "parallel" in lowered


def test_singleton_description_distinguishes_max_parallel_agents():
    description = _orchestrator_props()["singleton"]["description"]
    lowered = description.lower()
    assert "max-parallel-agents" in description
    assert "orchestrator" in lowered


def test_max_parallel_agents_description_mentions_max_instances():
    description = _schema()["properties"]["max-parallel-agents"]["description"]
    assert "max-instances" in description
    # The legacy key keeps its semantics: parallelism within one orchestrator.
    assert "within" in description.lower()


# --- compatibility -----------------------------------------------------------


def test_orchestrator_root_keeps_additional_properties_true():
    """Task 5 constraint: do not change ``additionalProperties`` on the root."""
    assert _orchestrator_schema()["additionalProperties"] is True
