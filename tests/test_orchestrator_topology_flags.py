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

from scripts.lib.topology import topology_explicit  # noqa: E402
from scripts.lib.variables import _topology_flags  # noqa: E402

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
