"""Flat orchestrator topology flag tests (IC-4).

SPEC-orchestrator-topology-2026-11-03, P1 (issue #1077), Task 8.

``_topology_flags`` is the pure, provider-agnostic flag derivation consumed by
the global variables builder (P1) and the provider-scoped re-resolvers (P2):

* ``ORCH_TOPOLOGY``                  — ``"primary"|"subagent"|"hybrid"`` or ``""``
* ``ORCH_TOPOLOGY_EXPLICIT``         — project-scope declaration only
* ``ORCH_TOPOLOGY_PRIMARY``          — exactly one of the three is ``"true"``
* ``ORCH_TOPOLOGY_SUBAGENT``
* ``ORCH_TOPOLOGY_HYBRID``
* ``ORCH_TOPOLOGY_SOURCE``           — ``project|provider-override|derived``

A provider override counts for that provider's rendering, never for the
provider-less global ``ORCH_TOPOLOGY_EXPLICIT`` (``topology_explicit(config)``
with ``provider=None`` asks the project scope only).

Run: python3 -m pytest tests/test_orchestrator_topology_flags.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.config import build_variables  # noqa: E402
from scripts.lib.topology import topology_explicit  # noqa: E402
from scripts.lib.variables import _instance_flags, _topology_flags  # noqa: E402

_POSITION_FLAGS = (
    "ORCH_TOPOLOGY_PRIMARY",
    "ORCH_TOPOLOGY_SUBAGENT",
    "ORCH_TOPOLOGY_HYBRID",
)


@pytest.mark.parametrize("topology", ["primary", "subagent", "hybrid"])
def test_set_topology_yields_exactly_one_true_position_flag(topology):
    flags = _topology_flags(topology, explicit=True, source="project")
    assert flags["ORCH_TOPOLOGY"] == topology
    assert flags["ORCH_TOPOLOGY_EXPLICIT"] == "true"
    assert flags["ORCH_TOPOLOGY_SOURCE"] == "project"
    assert sum(flags[name] == "true" for name in _POSITION_FLAGS) == 1
    assert flags[f"ORCH_TOPOLOGY_{topology.upper()}"] == "true"


def test_unset_topology_is_empty_and_every_position_flag_is_false():
    flags = _topology_flags("", explicit=False, source="derived")
    assert flags["ORCH_TOPOLOGY"] == ""
    assert flags["ORCH_TOPOLOGY_EXPLICIT"] == "false"
    assert flags["ORCH_TOPOLOGY_SOURCE"] == "derived"
    assert all(flags[name] == "false" for name in _POSITION_FLAGS)


def test_explicit_is_project_scope_only_provider_override_does_not_count():
    config = {
        "orchestrator": {
            "provider-overrides": {"Claude": {"topology": "primary"}}
        }
    }
    # The provider override is explicit for Claude, but not project-scoped.
    assert topology_explicit(config, "Claude") is True
    flags = _topology_flags(
        "primary",
        explicit=topology_explicit(config),
        source="provider-override",
    )
    assert flags["ORCH_TOPOLOGY_EXPLICIT"] == "false"
    assert flags["ORCH_TOPOLOGY_SOURCE"] == "provider-override"


def test_explicit_project_key_sets_explicit_true():
    config = {"orchestrator": {"topology": "subagent"}}
    flags = _topology_flags(
        "subagent", explicit=topology_explicit(config), source="project"
    )
    assert flags["ORCH_TOPOLOGY_EXPLICIT"] == "true"


def test_all_flag_values_are_strings():
    flags = _topology_flags("hybrid", explicit=True, source="project")
    assert all(isinstance(value, str) for value in flags.values())


def test_unknown_topology_fails_closed_to_empty():
    flags = _topology_flags("hybrid2", explicit=True, source="project")
    assert flags["ORCH_TOPOLOGY"] == ""
    assert all(flags[name] == "false" for name in _POSITION_FLAGS)


# --- instance flags (P3, AC-8) ---------------------------------------------


def test_instance_flags_unset_is_the_single_instance_default():
    flags = _instance_flags(None, singleton_declared=False)
    assert flags == {
        "ORCH_MAX_INSTANCES": "1",
        "ORCH_SINGLETON_DECLARED": "false",
    }


@pytest.mark.parametrize(
    "count,singleton,expected_count,expected_flag",
    [
        (1, False, "1", "false"),
        (3, True, "3", "true"),
        (8, True, "8", "true"),
    ],
)
def test_instance_flags_carry_the_declared_values(
    count, singleton, expected_count, expected_flag
):
    flags = _instance_flags(count, singleton_declared=singleton)
    assert flags["ORCH_MAX_INSTANCES"] == expected_count
    assert flags["ORCH_SINGLETON_DECLARED"] == expected_flag


@pytest.mark.parametrize("value", [0, 9, -1, "3", True, 2.5, [3]])
def test_out_of_range_or_non_int_instance_count_fails_closed(value):
    flags = _instance_flags(value, singleton_declared=True)
    assert flags["ORCH_MAX_INSTANCES"] == "1"
    assert flags["ORCH_SINGLETON_DECLARED"] == "true"


def test_build_variables_emits_instance_flags_from_the_project_scope():
    unset, _warnings = build_variables({}, _REPO_ROOT)
    assert unset["ORCH_MAX_INSTANCES"] == "1"
    assert unset["ORCH_SINGLETON_DECLARED"] == "false"

    declared, _warnings = build_variables(
        {"orchestrator": {"max-instances": 3, "singleton": True}}, _REPO_ROOT
    )
    assert declared["ORCH_MAX_INSTANCES"] == "3"
    assert declared["ORCH_SINGLETON_DECLARED"] == "true"


def test_singleton_presence_not_truthiness_sets_the_declared_flag():
    # ``singleton: false`` is rejected by the schema/validator, but the flag
    # answers "was the key declared?" — never "is the value truthy?".
    variables, _warnings = build_variables(
        {"orchestrator": {"singleton": False}}, _REPO_ROOT
    )
    assert variables["ORCH_SINGLETON_DECLARED"] == "true"
